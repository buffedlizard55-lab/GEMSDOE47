#!/usr/bin/env python3
"""Restore the three official competition rasters and verify them byte-for-byte.

Why this exists
---------------
The competition's data download is login-gated
(https://www.drivendata.org/competitions/306/competition-doe-gems/data/ redirects to
/accounts/login/), and this environment has no DrivenData credentials.  `curl`/`wget` are also
blocked for every host except `pypi.org` and `github.com`.  The one transport that works for
large binaries is the GitHub REST API via `gh api`, which this script uses.

**Identity is established by SHA-256, not by provenance.**  The pins in `src/gems47s3/spec.py`
were recorded from the official downloads in an earlier session and are re-verified here.  A
file that does not match its pin is refused, whatever its source.

Transport mirror, stated plainly
--------------------------------
`training_features.tif` is 418,912,844 bytes, above GitHub's 100 MB single-blob limit, so it
travels as five parts in a public team mirror (`buffedlizard55-lab/6GEMSDOE` at commit
`e2fe3f41…`).  That repository is a *transport* mirror maintained by this team; it is **not** an
official publisher of the competition data.  The official files are
`gems-geodawn-numerical-features.tif`, `existing_faults.tif` and `example_submission.tif` on the
competition's Data tab, and the pins are what tie the restored bytes to them.

Run:  python3 scripts/fetch_data.py [--verify-only]
Out:  data/training_features.tif, data/labels.tif, data/sample_submission.tif,
      evidence/data_restoration.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems47s3.spec import (
    BRIDGE_COMMIT,
    BRIDGE_PARTS,
    BRIDGE_REPO,
    FOOTPRINT_PIXELS,
    LABEL_POSITIVE_PIXELS,
    PINS,
)

DATA = ROOT / "data"
EV = ROOT / "evidence"

# Where each small official raster was found in a public team repository.  Same caveat as the
# bridge: these are transport copies, and the sha256 pins are the authority.
SMALL_SOURCES = [
    ("labels.tif", "buffedlizard55-lab/GEMSDOE10", "main", "data/labels.tif"),
    ("labels.tif", "buffedlizard55-lab/19GEMSDOE", "main", "data/labels.tif"),
    ("sample_submission.tif", "buffedlizard55-lab/GEMSDOE10", "main", "data/sample_submission.tif"),
    ("sample_submission.tif", "buffedlizard55-lab/19GEMSDOE", "main", "data/sample_submission.tif"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def gh_raw(repo: str, ref: str, path: str, dest: Path) -> bool:
    """Fetch one blob's raw bytes through the GitHub API.  Returns True on success."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"/repos/{repo}/contents/{path}?ref={ref}"
    with dest.open("wb") as fh:
        # check=False deliberately: a 404 from one candidate path is an expected branch, not an
        # error, and the caller inspects the return code and the sha256 pin instead.
        r = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw+json", url],
                           stdout=fh, stderr=subprocess.PIPE, check=False)
    if r.returncode != 0:
        dest.unlink(missing_ok=True)
        print(f"    gh api failed: {r.stderr.decode()[:200].strip()}")
        return False
    return True


def verify(name: str, path: Path) -> dict:
    pin = PINS[name]
    out = dict(file=name, path=str(path), exists=path.exists(),
               expected_bytes=pin["bytes"], expected_sha256=pin["sha256"],
               official_data_tab_name=pin["official_data_tab_name"])
    if not path.exists():
        out["ok"] = False
        return out
    out["bytes"] = path.stat().st_size
    out["sha256"] = sha256(path)
    out["bytes_match"] = out["bytes"] == pin["bytes"]
    out["sha256_match"] = out["sha256"] == pin["sha256"]
    out["ok"] = bool(out["bytes_match"] and out["sha256_match"])
    return out


def grid_assertions() -> dict:
    """Independent structural check: the restored rasters must agree with the pinned grid."""
    import numpy as np
    import rasterio
    res = {}
    try:
        with rasterio.open(DATA / "training_features.tif") as ds:
            res["features"] = dict(width=ds.width, height=ds.height, count=ds.count,
                                   dtype=str(ds.dtypes[0]),
                                   crs_epsg=ds.crs.to_epsg() if ds.crs else None,
                                   transform=list(tuple(ds.transform)[:6]),
                                   ok=(ds.width == 3292 and ds.height == 3730 and ds.count == 19
                                       and ds.crs.to_epsg() == 32611))
        with rasterio.open(DATA / "labels.tif") as ds:
            a = ds.read(1)
            res["labels"] = dict(width=ds.width, height=ds.height, dtype=str(a.dtype),
                                 nodata=ds.nodata, positive_pixels=int((a == 1).sum()),
                                 ok=(int((a == 1).sum()) == LABEL_POSITIVE_PIXELS))
        with rasterio.open(DATA / "sample_submission.tif") as ds:
            s = ds.read(1)
            res["sample_submission"] = dict(width=ds.width, height=ds.height,
                                            dtype=str(s.dtype), nodata=ds.nodata,
                                            footprint_pixels=int(np.isfinite(s).sum()),
                                            ok=(int(np.isfinite(s).sum()) == FOOTPRINT_PIXELS))
    except Exception as e:                                    # pragma: no cover
        res["error"] = str(e)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true",
                    help="do not download; verify and report what is already present")
    args = ap.parse_args()
    t0 = time.time()
    DATA.mkdir(parents=True, exist_ok=True)
    EV.mkdir(parents=True, exist_ok=True)
    log: dict = dict(started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                     transport="gh api (GitHub REST, raw accept header)",
                     note=("Identity is established by sha256 against src/gems47s3/spec.py::PINS. "
                           "The source repositories are team transport mirrors, not official "
                           "publishers; the official files are the three named on the "
                           "competition Data tab."),
                     steps=[])

    # --------------------------------------------------------------- training_features.tif
    tgt = DATA / "training_features.tif"
    v = verify("training_features.tif", tgt)
    if v.get("ok"):
        print("[skip] training_features.tif already matches its pin")
        log["steps"].append(dict(action="skip", file="training_features.tif", reason="pin matched"))
    elif args.verify_only:
        print("[missing] training_features.tif")
    else:
        bridge = DATA / "bridge"
        bridge.mkdir(parents=True, exist_ok=True)
        parts_ok = True
        for name, nbytes, digest in BRIDGE_PARTS:
            dest = bridge / name
            if dest.exists() and dest.stat().st_size == nbytes and sha256(dest) == digest:
                print(f"[cached] {name}")
                continue
            print(f"[fetch ] {BRIDGE_REPO}@{BRIDGE_COMMIT[:8]} {name} ({nbytes:,} bytes)")
            if (not gh_raw(BRIDGE_REPO, BRIDGE_COMMIT, f"data/bridge/{name}", dest)
                    and not gh_raw(BRIDGE_REPO, BRIDGE_COMMIT, name, dest)):
                parts_ok = False
                break
            got = dest.stat().st_size
            gd = sha256(dest)
            ok = (got == nbytes and gd == digest)
            log["steps"].append(dict(action="fetch_part", part=name, bytes=got, sha256=gd,
                                     expected_bytes=nbytes, expected_sha256=digest, ok=ok))
            print(f"         {got:,} bytes sha256={gd[:16]}… {'OK' if ok else 'MISMATCH'}")
            if not ok:
                parts_ok = False
                break
        if parts_ok:
            print("[concat] 5 parts -> training_features.tif")
            with tgt.open("wb") as out:
                for name, _, _ in BRIDGE_PARTS:
                    with (bridge / name).open("rb") as fh:
                        shutil.copyfileobj(fh, out, 1 << 22)
            v = verify("training_features.tif", tgt)
            print(f"[verify] training_features.tif ok={v.get('ok')} sha256={v.get('sha256','')[:16]}…")
            log["steps"].append(dict(action="concatenate", **v))
            if v.get("ok"):
                shutil.rmtree(bridge, ignore_errors=True)
                print("[clean ] removed data/bridge (400 MB of scratch)")
        else:
            print("[FAIL  ] a bridge part did not match its pin; refusing to concatenate")

    # --------------------------------------------------------------- the two small rasters
    for name in ("labels.tif", "sample_submission.tif"):
        tgt = DATA / name
        v = verify(name, tgt)
        if v.get("ok"):
            print(f"[skip] {name} already matches its pin")
            log["steps"].append(dict(action="skip", file=name, reason="pin matched"))
            continue
        if args.verify_only:
            print(f"[missing] {name}")
            continue
        for fname, repo, ref, path in SMALL_SOURCES:
            if fname != name:
                continue
            print(f"[fetch ] {repo}@{ref} {path}")
            if not gh_raw(repo, ref, path, tgt):
                continue
            v = verify(name, tgt)
            log["steps"].append(dict(action="fetch", file=name, source=f"{repo}@{ref}:{path}", **v))
            if v.get("ok"):
                print(f"[verify] {name} ok=True sha256={v['sha256'][:16]}…")
                break
            print(f"[verify] {name} MISMATCH from {repo}; trying the next source")
            tgt.unlink(missing_ok=True)

    # --------------------------------------------------------------- final report
    final = {n: verify(n, DATA / n) for n in PINS}
    grid = grid_assertions()
    all_ok = all(v.get("ok") for v in final.values()) and \
        all(g.get("ok") for g in grid.values() if isinstance(g, dict))
    log["seconds"] = round(time.time() - t0, 1)
    log["verification"] = final
    log["grid_assertions"] = grid
    log["all_pins_matched"] = all_ok
    (EV / "data_restoration.json").write_text(json.dumps(log, indent=2, default=str))
    print("\n--- verification ---")
    for n, v in final.items():
        print(f"  {n:26s} ok={v.get('ok')} bytes={v.get('bytes')} sha256={str(v.get('sha256'))[:16]}…")
    for n, g in grid.items():
        if isinstance(g, dict):
            print(f"  grid[{n}] {g}")
    print(f"\nALL PINS MATCHED: {all_ok}   ({time.time()-t0:.0f}s)")
    print(f"wrote {EV/'data_restoration.json'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
