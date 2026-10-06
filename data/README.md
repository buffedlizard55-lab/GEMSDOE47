# Data

**No large input is committed.** Everything here is either a small receipt or a
pointer.

| Path | Status |
|---|---|
| `restore_receipt.json` | committed historical snapshot: 23 files verified against the manifest that existed at generation time (2026-10-06); it predates three H47-B metadata/audit entries added afterward |
| `*.tif`, `external/`, `scored/`, `prepared/`, `raw_parts/` | git-ignored, restored on demand |

Restore (requires the `gh` CLI and GitHub API access to the public pinned mirrors; no DrivenData login is used; current manifest is about 531 MB / 507 MiB):

```bash
python3 scripts/restore_data.py --group all
# groups: core | external | scored | reference | all
# flags : --target-dir PATH   --skip-large   --only ID[,ID...]
```

Every file is verified against `registry/data_manifest.json` by SHA-256 and byte
count before it is accepted. The script prints `ALL_VERIFIED=True` only if all
files match; anything else exits non-zero.

Where the bytes come from: the competition portal requires credentials this
environment does not have, so the three competition rasters, external feature and
diagnostic layers (including H47-B's metadata sidecar and figure-derived,
label-free acquisition-block audit), twelve scored prior submissions, and the
H33 reference are restored from hash-pinned owner mirrors in sibling repositories
through the GitHub Contents API. Pins establish mirror consistency, not organizer
authentication. Each source, ref, path, byte count, and SHA-256 is recorded in
the manifest rather than being passed off as a direct competition-portal
download.

The `h33-2-b2` reference raster comes from `buffedlizard55-lab/GEMSDOE32` and
is pinned by SHA-256 in the same manifest (`reference/h33-2-b2-zeros.tif`). It is
not an authenticated thirteenth score/raster pair: the participant-level 0.2778
row is not linked to this TIFF, and the owner page marks it unscored. Include it
only as an explicitly assumed sensitivity scenario.
