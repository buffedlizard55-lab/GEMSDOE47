#!/usr/bin/env python3
"""Bounded, commit/blob-pinned uniqueness and historical-site inventory.

Read-only GitHub operations via configured gh. No branch creation, no token
handling, no private-repository publishing. Large input datasets stay ignored.
Visible public GEMSDOE repositories are evidence for prior art, not official
score receipts. This audit never infers a filename-to-leaderboard mapping.
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures
import hashlib
import json
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.io import MemoryFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems47 import contract as C
from gems47 import grid as G

OWNER = "buffedlizard55-lab"
CACHE = ROOT / ".cache" / "prior_artifacts"
INVENTORY = ROOT / "evidence" / "prior-inventory-20261006.json"
MAX_BYTES = 40_000_000


def gh_json(endpoint: str) -> dict:
    result = subprocess.run(["gh", "api", endpoint], capture_output=True, check=True, text=True, timeout=90)
    return json.loads(result.stdout)


def blob_bytes(repo: str, sha: str, *, suffix: str = "") -> bytes:
    path = CACHE / "blobs" / f"{sha}{suffix}"
    if path.exists():
        content = path.read_bytes()
    else:
        body = gh_json(f"repos/{OWNER}/{repo}/git/blobs/{sha}")
        if body.get("encoding") != "base64":
            raise ValueError("unexpected Git blob encoding")
        content = base64.b64decode(body["content"].replace("\n", ""), validate=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".partial")
        temporary.write_bytes(content)
        temporary.replace(path)
    actual = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content,
                          usedforsecurity=False).hexdigest()
    if actual != sha:
        path.unlink(missing_ok=True)
        raise ValueError("Git blob SHA-1 integrity mismatch")
    return content


def inventory() -> dict:
    result = subprocess.run(["gh", "repo", "list", OWNER, "--limit", "200", "--json", "name,isPrivate"],
                            capture_output=True, check=True, text=True, timeout=90)
    repositories = [r["name"] for r in json.loads(result.stdout)
                    if not r["isPrivate"] and re.fullmatch(r"(?:\d+)?GEMSDOE\d*", r["name"], re.IGNORECASE)]
    files: dict[str, dict] = {}
    sources = []
    def inspect(repo: str):
        try:
            commit = gh_json(f"repos/{OWNER}/{repo}/git/ref/heads/main")["object"]["sha"]
            tree = gh_json(f"repos/{OWNER}/{repo}/git/trees/{commit}?recursive=1")
            if tree.get("truncated"):
                raise ValueError("recursive tree truncated; inventory incomplete")
            entries = tree["tree"]
            artifact_entries = [e for e in entries if e["type"] == "blob"
                                and e["path"].lower().endswith((".tif", ".tiff", ".zip"))
                                and (e["path"].startswith(("docs/", "submissions/", "artifacts/", "outputs/"))
                                     or re.search(r"submission.*\.tif$", e["path"], re.IGNORECASE))]
            # Preserve a commit-pinned owner narrative for learning, with a hash,
            # not a scraped numerical "official score" assertion.
            narratives = []
            for path in ("docs/index.html", "index.html", "README.md"):
                e = next((e for e in entries if e["path"] == path and e["type"] == "blob"), None)
                if e and e.get("size", 0) <= 500_000:
                    content = blob_bytes(repo, e["sha"], suffix=".txt")
                    narratives.append({"path": path, "sha256": hashlib.sha256(content).hexdigest(),
                                       "git_blob_sha1": e["sha"], "bytes": len(content),
                                       "url": f"https://github.com/{OWNER}/{repo}/blob/{commit}/{path}"})
            return {"repository": repo, "commit": commit, "tree_sha1": tree["sha"],
                    "status": "verified_inventory", "narratives": narratives}, artifact_entries
        except (subprocess.CalledProcessError, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
            return {"repository": repo, "status": "inventory_failed", "error": str(error)[:250]}, []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        for source, entries in executor.map(inspect, sorted(repositories)):
            sources.append(source)
            for entry in entries:
                sha = entry["sha"]
                rec = files.setdefault(sha, {"git_blob_sha1": sha, "size_bytes": entry.get("size", 0), "paths": []})
                rec["paths"].append({"repository": source["repository"], "commit": source["commit"], "path": entry["path"]})
            print(f"[inventory] {source['repository']}: {len(entries)} paths, {source['status']}", flush=True)
    out = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "scope": "public owner repositories visible through gh, main commits pinned before comparison",
           "repositories": sources, "files": list(files.values()), "unique_git_blobs": len(files),
           "complete_repository_inventories": sum(r["status"] == "verified_inventory" for r in sources),
           "failed_repository_inventories": sum(r["status"] != "verified_inventory" for r in sources),
           "limitations": ["Not global uniqueness; inaccessible/unpublished artifacts are excluded.",
                           "Source narratives and scores are owner reports, never organizer receipts.",
                           "Files larger than 40 MB will be recorded as unexamined, not assumed different."]}
    INVENTORY.write_text(json.dumps(out, indent=2) + "\n")
    return out


def compare(candidate: Path, current_inventory: dict) -> dict:
    template = G.load_template()
    validation = C.validate(candidate, template)
    if not validation["format_valid"]:
        raise ValueError("candidate contract must pass before uniqueness audit")
    with rasterio.open(candidate) as source:
        current = source.read(1)[template.footprint]
    mask = current > 0
    n_current = int(mask.sum())
    target_relative = candidate.resolve().relative_to(ROOT).as_posix()
    def one(entry: dict):
        source = next((p for p in entry["paths"]
                       if not (p["repository"] == "GEMSDOE47" and p["path"] == target_relative)), None)
        row = {"git_blob_sha1": entry["git_blob_sha1"], "size_bytes": entry["size_bytes"], "paths": entry["paths"]}
        if source is None:
            return {**row, "status": "current_artifact_self_reference_excluded"}
        if entry["size_bytes"] > MAX_BYTES:
            return {**row, "status": "unexamined_size_limit"}
        try:
            raw = blob_bytes(source["repository"], entry["git_blob_sha1"], suffix=".bin")
            if len(raw) != entry["size_bytes"]:
                raise ValueError("tree byte size differs from downloaded blob")
            if source["path"].lower().endswith(".zip"):
                import io
                with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                    members = [m for m in archive.infolist() if not m.is_dir()]
                    if len(members) != 1 or not members[0].filename.lower().endswith((".tif", ".tiff")):
                        return {**row, "status": "not_single_tiff_zip"}
                    if members[0].file_size > 70_000_000:
                        return {**row, "status": "unexamined_zip_expansion_limit"}
                    raw = archive.read(members[0])
            with MemoryFile(raw) as memory, memory.open() as source_ds:
                if source_ds.count != 1 or source_ds.shape != template.shape or source_ds.crs != rasterio.crs.CRS.from_string(template.crs) \
                   or not np.allclose(tuple(source_ds.transform), tuple(template.transform), rtol=0, atol=1e-9):
                    return {**row, "status": "not_single_band_exact_grid"}
                values = source_ds.read(1)[template.footprint]
            bad = ~np.isfinite(values) | (values < 0) | (values > 1)
            prior = np.where(np.isfinite(values), values, 0)
            pm = prior > 0
            inter = int(np.count_nonzero(mask & pm))
            union = n_current + int(pm.sum()) - inter
            return {**row, "status": "compared", "prior_file_sha256": hashlib.sha256(raw).hexdigest(),
                    "positive_pixels": int(pm.sum()), "invalid_interior_pixels": int(bad.sum()),
                    "intersection": inter, "jaccard": inter / union if union else 0,
                    "exact_positive_mask_match": bool(np.array_equal(mask, pm)),
                    "exact_in_footprint_prediction_match": bool(np.array_equal(current, prior))}
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError, ValueError,
                rasterio.errors.RasterioError, zipfile.BadZipFile, KeyError) as error:
            return {**row, "status": "comparison_failed", "error": str(error)[:250]}
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        for i, row in enumerate(executor.map(one, current_inventory["files"]), start=1):
            rows.append(row)
            if i % 40 == 0:
                print(f"[compare] {i}/{len(current_inventory['files'])}", flush=True)
    # Current branch's historical research downloads aren't necessarily on main.
    for path in sorted((ROOT / "docs" / "downloads").glob("*.tif")):
        if path.resolve() == candidate.resolve():
            continue
        with rasterio.open(path) as source:
            if source.shape != template.shape or source.count != 1 or source.transform != template.transform:
                continue
            values = np.nan_to_num(source.read(1)[template.footprint], nan=0.0)
        pm = values > 0
        inter = int((mask & pm).sum()); union = n_current + int(pm.sum()) - inter
        rows.append({"status": "compared_local_history", "path": path.relative_to(ROOT).as_posix(),
                     "prior_file_sha256": C.sha256(path), "positive_pixels": int(pm.sum()),
                     "intersection": inter, "jaccard": inter / union if union else 0,
                     "exact_positive_mask_match": bool(np.array_equal(mask, pm)),
                     "exact_in_footprint_prediction_match": bool(np.array_equal(current, values))})
    compared = [r for r in rows if r["status"].startswith("compared")]
    matches = [r for r in compared if r["exact_positive_mask_match"] or r["exact_in_footprint_prediction_match"]]
    out = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "candidate_filename": candidate.name, "candidate_sha256": validation["sha256"],
           "candidate_positive_pixels": n_current, "inventory_sha256": C.sha256(INVENTORY),
           "public_repositories_in_inventory": len(current_inventory["repositories"]),
           "comparisons": len(compared), "exact_matches": len(matches),
           "bounded_unique": bool(compared and n_current and not matches),
           "global_unique_proven": False,
           "max_jaccard": max((r["jaccard"] for r in compared), default=None),
           "unexamined_or_failed": sum(not r["status"].startswith("compared") for r in rows),
           "failed_repository_inventories": current_inventory["failed_repository_inventories"],
           "rows": sorted(rows, key=lambda r: r.get("jaccard", -1), reverse=True),
           "limits": current_inventory["limitations"]}
    (ROOT / "evidence" / "profile-uniqueness.json").write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument("--refresh-inventory", action="store_true")
    parser.add_argument("--candidate", type=Path)
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    current_inventory = inventory() if args.refresh_inventory or not INVENTORY.exists() else json.loads(INVENTORY.read_text())
    if not args.inventory_only:
        if not args.candidate:
            parser.error("--candidate is required for comparison")
        result = compare(args.candidate, current_inventory)
        return 0 if result["bounded_unique"] else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
