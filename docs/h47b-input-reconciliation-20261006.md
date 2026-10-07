# H47-B input reconciliation — 2026-10-06

> **This is a provenance review, not a rerun. H47-B was not rescored.** Its negative result and `NOT PROMOTED` status remain unchanged.

## Frozen protocol and report integrity

The machine-readable H47-B report records protocol SHA-256 `4cb65d953e575d942f0b1db8d258a36fbc2c8caea32e3409da127d36eaa0c6c6`. That hash matches the byte-exact frozen [`preregistered-h2.md`](preregistered-h2.md) retained at this revision. Post-run storage-path and provenance clarification is recorded here rather than changing the frozen protocol.

The report records:

- feature TIFF: `a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b`
- feature metadata sidecar: `56556f24c051043fd7a85587786118f8064624f2ad0604aaa3e6614f1a9f6d2f`
- labels: `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093`
- sample-submission grid/template: `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc`
- descriptive acquisition-block raster: `2c0785c4b3ec46c734d1be7a7aedbb3e816201100ab358033a3af074418c894a`

Each hash matches its corresponding entry in the **current 26-entry** `registry/data_manifest.json`. The feature TIFF, labels, and template are present in the 23-entry `data/restore_receipt.json`; the acquisition-block raster, its derivation receipt, and the feature metadata sidecar are not listed in that receipt. The current receipt's `all_verified: true` certifies only the files actually listed there; it is not a 26-entry restore attestation.

The grid recorded by the report is 3292 × 3730, EPSG:32611, 100 m, transform `(243350, 100, 0, 4508550, 0, -100)`. The metadata identifies `TMI_up150` as a rank-encoded uint8 channel, not physical magnetic units. The acquisition-block raster is figure-derived and approximate; it was used only for descriptive subgroup checks, never to build the candidate or select spacing.

## Provenance and rerun gate

The ignored `.cache/gems_data/` payload was not present during this review. The comparisons above are record-to-record checks among the frozen report, current manifest, and saved receipt; no current local raster bytes were reread, no fresh full restore was attempted, and no experiment was rerun. These checks establish that the recorded hashes agree with the manifest where noted, not fresh local-byte validation.

All comparisons above establish byte/hash consistency with an owner-supplied public GitHub mirror, **not organizer authentication**. The feature and competition rasters were not obtained through an authenticated entrant download. The acquisition-block boundaries are approximate and non-official; they are not a model input, selection criterion, or eligibility gate.

Before any future H47-B rerun, first obtain/reconcile the complete current-manifest inputs and hashes, confirm an authorized data source and the intended restore scope, and verify the exact code/protocol version against the frozen record. A fresh full 26-entry restore has not been established by the 23-entry receipt. This review authorizes no rerun, portal upload, or submission-slot use.

Source records: [`h47b-screen-report-20261006.json`](h47b-screen-report-20261006.json), [`preregistered-h2.md`](preregistered-h2.md), [`registry/data_manifest.json`](../registry/data_manifest.json), and [`data/restore_receipt.json`](../data/restore_receipt.json).
