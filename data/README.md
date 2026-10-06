# Data

**No large input is committed.** Everything here is either a small receipt or a
pointer.

| Path | Status |
|---|---|
| `restore_receipt.json` | committed — 22/22 SHA-256 verifications with per-file source, ref and URL |
| `*.tif`, `external/`, `scored/`, `prepared/`, `raw_parts/` | git-ignored, restored on demand |

Restore (needs `gh` authenticated as the repository owner, ~30 s for 1.2 GB):

```bash
python3 scripts/restore_data.py --group all
# groups: core | external | scored | reference | all
# flags : --target-dir PATH   --skip-large   --force
```

Every file is verified against `registry/data_manifest.json` by SHA-256 and byte
count before it is accepted. The script prints `ALL_VERIFIED=True` only if all
files match; anything else exits non-zero.

Where the bytes come from: the competition portal requires credentials this
environment does not have, so the three official rasters
(`training_features.tif`, `labels.tif`, `sample_submission.tif`), the seven
external layers and the twelve scored prior submissions are restored from the
owner's hash-pinned mirrors in sibling repositories through the GitHub Contents
API. `raw.githubusercontent.com` and every USGS / GDR / DrivenData host are
network-unreachable from this sandbox; the Contents API is not. That is recorded
as the provenance in the manifest rather than being passed off as a direct
download.

The thirteenth observation — the reported-0.2778 `h33-2-b2` reference raster —
comes from `buffedlizard55-lab/GEMSDOE32` and is pinned by SHA-256 in the same
manifest (`reference/h33-2-b2-zeros.tif`).
