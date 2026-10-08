# Next-session handoff — 8 October 2026 after H65

**Read the standing brief in `README.md` first.** H60 remains the one primary artifact that is
**OK TO DOWNLOAD AND SUBMIT**; H50 is the labelled fallback. H65 failed one frozen gate condition,
so no H65 TIFF was built and no slot was spent.

## What happened

1. Four geological hypotheses H65–H68 were ranked and preregistered before scoring at commit `b73bb64`.
2. H65 tested H60's six-channel lidar scarp field at 1.4, 1.6, 1.8, 2.0, 2.2 and 2.4 px on the exact
   frozen H50/H60 41-block split.
3. The selection half chose 2.2 px. Proxy scores improved over H60: primary pooled 0.291533 vs 0.287891,
   mean block 0.285494 vs 0.284379, independent SGMC 0.205420 vs 0.193813, and simultaneous conformal
   floor 0.099207 at ≥90.91% conditional coverage.
4. The preregistration required a selected point strictly below 2.0 px. That condition failed. The gate
   was not rewritten post-hoc; no TIFF was built. Full history: `evidence/h65/` and `docs/h65.html`.
5. Landing, executive-summary and submission pages were replaced to remove contradictory old H47-C1/H50
   instructions. All now lead with the exact H60 bytes and label H65 research-only.

## Next priority

1. If a slot is used, submit exact H60 bytes only after live portal eligibility/quota review and save the receipt.
2. Do not retest a 2.2 px H65 candidate on these same blocks; all block scores are now inspected.
3. H66 (ordered positive-crest/negative-toe lidar curvature pair with step support) is the next scientific
   hypothesis. Preregister it against a genuinely independent or untouched target before implementation.
4. H67 needs official raw 1 m DEM windows/tile-list coverage; do not call it viable with only the quantized stack.
5. Resolve the organizer's null/NaN-outside wording versus the observed NaN-intolerant range rejection only through
   an authenticated portal receipt. Keep exact failed bytes/errors.

## Verification at handoff

- Restored 28/28 hash-pinned inputs; `ALL_VERIFIED=True` (mirror identity is not organizer authentication).
- `pytest tests -q`: 320 passed, 2 skipped, 7 subtests passed.
- `unittest discover`: 91 passed.
- Ruff 0.16.10: clean.
- H60 SHA-256 remains `4ee074230a305fce6768012fc33380bf196c89170e70050a77cf4a44d74ef14c`.
