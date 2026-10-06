#!/usr/bin/env python3
"""Compare a candidate with local prior rasters and the pinned sibling-site inventory.

Requires ``gh`` authenticated for GitHub Contents API access. It compares TIFFs
currently available in the repository/restored cache, then downloads each unique
public GitHub TIFF blob temporarily, verifies its recorded Git blob SHA-1, compares
masks on the exact grid, and deletes the temporary file. These are bounded
inventories, not a global uniqueness proof. It does not contact or monitor DrivenData.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "docs" / "h47b-uniqueness-audit-20261006.json"
DEFAULT_CANDIDATE = ROOT / "docs" / "downloads" / (
    "gems47-h47b-single-scale-tmi-up150-400m-d5-n18524-"
    "research-only-not-for-submission-20261006-nanoutside.tif"
)
ALLFINITE_DIAGNOSTIC = ROOT / "docs" / "downloads" / (
    "gems47-h47b-single-scale-tmi-up150-400m-d5-n18524-"
    "research-only-not-for-submission-20261006-allfinite.tif"
)
DEFAULT_OUTPUT = ROOT / "evidence" / "conformal_candidate_uniqueness_20261006.json"


def git_blob_sha1(path: Path) -> str:
    size = path.stat().st_size
    digest = hashlib.sha1()  # Git's object ID is SHA1(blob <size>\0<data>).
    digest.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _grid(ds: rasterio.io.DatasetReader) -> dict[str, Any]:
    return {
        "width": ds.width,
        "height": ds.height,
        "crs": ds.crs.to_string() if ds.crs else None,
        "transform_gdal": list(ds.transform.to_gdal()),
    }


def _top_equal_mass_mask(values: np.ndarray, footprint: np.ndarray, budget: int) -> np.ndarray:
    support = np.isfinite(values) & (values > 0.0) & footprint
    flat = np.flatnonzero(support.ravel())
    if flat.size > budget:
        order = np.lexsort((flat, -values.ravel()[flat]))
        flat = flat[order[:budget]]
    result = np.zeros(values.shape, dtype=bool)
    result.ravel()[flat] = True
    return result


def _fetch_blob(repo: str, branch: str, path: str, destination: Path) -> None:
    if shutil.which("gh") is None:
        raise RuntimeError("gh CLI is required to fetch pinned public GitHub artifacts")
    endpoint = f"repos/buffedlizard55-lab/{repo}/contents/{quote(path, safe='/')}?ref={quote(branch, safe='')}"
    # Write raw media directly to disk so a single potentially large TIFF is
    # never duplicated in Python memory.
    with destination.open("wb") as stream:
        completed = subprocess.run(
            ["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw"],
            stdout=stream,
            stderr=subprocess.PIPE,
            check=False,
        )
    if completed.returncode:
        destination.unlink(missing_ok=True)
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"GitHub fetch failed for {repo}/{path}: {message}")


def _jaccard(left: np.ndarray, right: np.ndarray) -> float:
    union = int(np.count_nonzero(left | right))
    if union == 0:
        return 1.0
    return float(np.count_nonzero(left & right) / union)


def _compare_local_prior_artifacts(
    candidate_path: Path,
    candidate_grid: dict[str, Any],
    candidate_mask: np.ndarray,
    footprint: np.ndarray,
    budget: int,
) -> dict[str, Any]:
    data_dir = ROOT / ".cache" / "gems_data"
    candidate_paths = {
        *((ROOT / "docs" / "downloads").glob("*.tif")),
        *((data_dir / "scored").glob("*.tif")),
        *((data_dir / "reference").glob("*.tif")),
    }
    candidate_realpath = candidate_path.resolve()
    excluded_related_variants: list[dict[str, str]] = []
    if candidate_realpath == DEFAULT_CANDIDATE.resolve() and ALLFINITE_DIAGNOSTIC.is_file():
        try:
            with rasterio.open(ALLFINITE_DIAGNOSTIC) as diagnostic_ds:
                diagnostic_values = diagnostic_ds.read(1)
                diagnostic_mask = (
                    np.isfinite(diagnostic_values) & (diagnostic_values > 0.0) & footprint
                )
                same_grid = diagnostic_ds.count == 1 and _grid(diagnostic_ds) == candidate_grid
        except rasterio.errors.RasterioError:
            same_grid = False
            diagnostic_mask = np.zeros_like(candidate_mask)
        if same_grid and np.array_equal(candidate_mask, diagnostic_mask):
            candidate_paths.discard(ALLFINITE_DIAGNOSTIC)
            excluded_related_variants.append({
                "path": str(ALLFINITE_DIAGNOSTIC.relative_to(ROOT)),
                "sha256": hashlib.sha256(ALLFINITE_DIAGNOSTIC.read_bytes()).hexdigest(),
                "positive_mask_verified": "true",
                "reason": (
                    "same generated positive mask as the candidate, verified on the candidate grid; "
                    "retained only as an alternate outside-footprint encoding for range-error diagnostics, "
                    "not an independent prior model"
                ),
            })
    rows: list[dict[str, Any]] = []
    for path in sorted(candidate_paths):
        if path.resolve() == candidate_realpath:
            continue
        row: dict[str, Any] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        try:
            with rasterio.open(path) as ds:
                if ds.count != 1 or _grid(ds) != candidate_grid:
                    row["grid_comparable"] = False
                    rows.append(row)
                    continue
                values = ds.read(1)
            support = np.isfinite(values) & (values > 0.0) & footprint
            top_equal = _top_equal_mass_mask(values, footprint, budget)
            row.update({
                "grid_comparable": True,
                "positive_pixels": int(support.sum()),
                "exact_positive_mask_match": bool(np.array_equal(candidate_mask, support)),
                "positive_support_jaccard": _jaccard(candidate_mask, support),
                "equal_mass_positive_pixels": int(top_equal.sum()),
                "equal_mass_jaccard": _jaccard(candidate_mask, top_equal),
            })
        except Exception as exc:  # retain per-artifact failures in the bounded audit
            row["grid_comparable"] = False
            row["error"] = str(exc)
        rows.append(row)

    comparable = [row for row in rows if row.get("grid_comparable") is True]
    closest_support = max(comparable, key=lambda row: row["positive_support_jaccard"], default=None)
    closest_equal = max(comparable, key=lambda row: row["equal_mass_jaccard"], default=None)
    return {
        "scope": (
            "prior TIFFs present in docs/downloads and the restored .cache/gems_data/scored and "
            "reference directories at audit time; the paired same-mask all-finite diagnostic encoding "
            "is excluded when auditing the NaN-outside primary; not a global or complete inventory"
        ),
        "excluded_related_variants": excluded_related_variants,
        "artifacts_attempted": len(rows),
        "exact_grid_comparisons": len(comparable),
        "grid_mismatches_or_failures": len(rows) - len(comparable),
        "exact_positive_mask_matches": sum(bool(row.get("exact_positive_mask_match")) for row in comparable),
        "maximum_positive_support_jaccard": (
            closest_support["positive_support_jaccard"] if closest_support else None
        ),
        "closest_positive_support": closest_support,
        "maximum_equal_mass_jaccard": (
            closest_equal["equal_mass_jaccard"] if closest_equal else None
        ),
        "closest_equal_mass": closest_equal,
        "comparisons": rows,
    }


def run(candidate_path: Path, output_path: Path) -> dict[str, Any]:
    if not candidate_path.is_file():
        raise FileNotFoundError(candidate_path)
    source = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    inventory = source["inventory"]
    comparable = {
        str(row["git_blob_sha"]): row
        for row in source["all_comparisons_sorted_by_equal_mass_jaccard_descending"]
    }
    excluded = {
        str(row["git_blob_sha1"])
        for row in source["comparison"]["non_comparable_artifacts"]
    }
    candidate_sha256 = hashlib.sha256(candidate_path.read_bytes()).hexdigest()

    with rasterio.open(candidate_path) as ds:
        if ds.count != 1 or ds.dtypes[0] != "float32":
            raise ValueError("candidate must be one-band float32")
        candidate_grid = _grid(ds)
        candidate_values = ds.read(1)
        candidate_positive = np.isfinite(candidate_values) & (candidate_values > 0)
        height, width = candidate_values.shape

    # The official mirror footprint is pinned in the H47-B screen; read it from
    # the ignored cache if present, otherwise use the candidate's data-valid
    # footprint. The candidate produced here is all-finite, so prefer the exact
    # labels mask from the restored mirror to avoid treating zeros outside its
    # irregular data area as valid for the comparison.
    data_dir = ROOT / ".cache" / "gems_data"
    labels_path = data_dir / "labels.tif"
    if labels_path.is_file():
        with rasterio.open(labels_path) as labels_ds:
            if labels_ds.shape != candidate_values.shape or _grid(labels_ds) != candidate_grid:
                raise ValueError("restored labels grid differs from candidate")
            footprint = labels_ds.read(1) != -1
        footprint_source = str(labels_path.relative_to(ROOT))
    else:
        footprint = np.isfinite(candidate_values)
        footprint_source = "candidate finite-data mask (labels mirror absent)"

    budget = int(candidate_positive.sum())
    candidate_mask = candidate_positive & footprint
    local_prior_artifact_comparison = _compare_local_prior_artifacts(
        candidate_path, candidate_grid, candidate_mask, footprint, budget
    )
    expected_grid = candidate_grid
    blob_records = [row for row in inventory["files"]
                    if str(row["git_blob_sha1"]) in comparable and
                    str(row["git_blob_sha1"]) not in excluded]
    if len(blob_records) != len(comparable):
        raise ValueError(
            f"inventory mismatch: {len(blob_records)} comparable blobs vs {len(comparable)} comparisons"
        )

    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    exact_matches = 0
    max_support_jaccard = -1.0
    max_equal_jaccard = -1.0
    closest_support: dict[str, Any] | None = None
    closest_equal: dict[str, Any] | None = None

    with tempfile.TemporaryDirectory(prefix="gems47-uniq-") as temp_dir:
        temp_root = Path(temp_dir)
        for index, record in enumerate(blob_records, 1):
            blob = str(record["git_blob_sha1"])
            location = record["paths"][0]
            repo = str(location["repository"])
            branch = str(location["branch"])
            path = str(location["path"])
            local = temp_root / f"{index:04d}.tif"
            try:
                _fetch_blob(repo, branch, path, local)
                actual_blob = git_blob_sha1(local)
                if actual_blob != blob:
                    raise RuntimeError(
                        f"Git blob changed since inventory: expected {blob}, got {actual_blob}"
                    )
                if local.stat().st_size != int(record["size_bytes"]):
                    raise RuntimeError("byte count differs from the saved inventory")
                with rasterio.open(local) as ds:
                    if ds.count != 1 or _grid(ds) != expected_grid:
                        raise RuntimeError("raster is no longer on the exact candidate grid")
                    values = ds.read(1)
                prior_support = np.isfinite(values) & (values > 0.0) & footprint
                prior_top = _top_equal_mass_mask(values, footprint, budget)
                support_j = _jaccard(candidate_mask, prior_support)
                equal_j = _jaccard(candidate_mask, prior_top)
                exact = bool(np.array_equal(candidate_mask, prior_support))
                exact_matches += int(exact)
                result = {
                    "git_blob_sha1": blob,
                    "repository": repo,
                    "path": path,
                    "size_bytes": int(record["size_bytes"]),
                    "exact_positive_mask_match": exact,
                    "positive_support_pixels": int(prior_support.sum()),
                    "positive_support_jaccard": support_j,
                    "equal_mass_positive_pixels": int(prior_top.sum()),
                    "equal_mass_jaccard": equal_j,
                }
                results.append(result)
                if support_j > max_support_jaccard:
                    max_support_jaccard = support_j
                    closest_support = result
                if equal_j > max_equal_jaccard:
                    max_equal_jaccard = equal_j
                    closest_equal = result
            except Exception as exc:  # record individual public-source failures; continue the audit
                failures.append({
                    "git_blob_sha1": blob,
                    "repository": repo,
                    "path": path,
                    "error": str(exc),
                })
            finally:
                local.unlink(missing_ok=True)
            if index % 25 == 0 or index == len(blob_records):
                print(f"[{index}/{len(blob_records)}] checked; failures={len(failures)}", flush=True)

    audit = {
        "schema_version": 1,
        "title": "H47-B single-scale d=5 local and visible-artifact uniqueness audit",
        "candidate": {
            "path": str(candidate_path.relative_to(ROOT)),
            "sha256": candidate_sha256,
            "positive_pixels": int(candidate_mask.sum()),
            "grid": candidate_grid,
            "footprint_source": footprint_source,
        },
        "inventory": {
            "source_audit": "docs/h47b-uniqueness-audit-20261006.json",
            "snapshot_date": inventory["snapshot_date"],
            "visible_repositories": inventory["repositories"],
            "unique_blobs_in_original_inventory": inventory["unique_git_blobs"],
            "exact_grid_blobs_attempted": len(blob_records),
            "verified_exact_grid_comparisons": len(results),
            "fetch_or_verification_failures": len(failures),
            "note": "Historical GitHub branch/path inventory; current blob SHA-1 is checked before every comparison.",
        },
        "comparison": {
            "method": "positive-support Jaccard plus top-equal-mass mask Jaccard; ties by ascending flat index",
            "budget": budget,
            "exact_positive_mask_matches": exact_matches,
            "maximum_positive_support_jaccard": max_support_jaccard,
            "closest_positive_support": closest_support,
            "maximum_equal_mass_jaccard": max_equal_jaccard,
            "closest_equal_mass": closest_equal,
        },
        "local_prior_artifact_comparison": local_prior_artifact_comparison,
        "scope_caveat": (
            "A bounded comparison to the local prior TIFFs and prior visible sibling-repository inventory "
            "available at audit time. It cannot establish uniqueness against private, deleted, unindexed, "
            "or later-published files, and says nothing about performance, score attribution, or portal acceptance."
        ),
        "failures": failures,
        "comparisons": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        run(args.candidate.resolve(), args.output.resolve())
    except (FileNotFoundError, ValueError, RuntimeError, rasterio.errors.RasterioError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
