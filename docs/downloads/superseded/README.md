# Superseded artifacts (do not submit)

Kept for auditability as local research bytes only. None is promoted or slot-eligible. Historical local format checks did not all test the published null/NaN-outside requirement. The H33-2-B2 / participant-DTI 0.2778 association is unverified; all score-dependent comparisons are conditional, and no owner-reported reference is an authenticated leaderboard incumbent.

| file | why it is here |
|---|---|
| `gems47-h48-mscl-repack-r1p5-44838px-…-allfinite.tif` | H48 **repack** arm, 2026-10-06 20:32Z. It passed 21/21 historical local checks but stores unmasked zeros outside and fails the published null/NaN-outside check. Its local proxy values were 0.0404/0.1081 versus 0.0067/0.0989 against owner-reported d2.8 reference geometry; these are not leaderboard comparisons. It **re-issues prior geometry**: 59.2 % of its pixels are the owner-reported 0.2600 field's and 66.9 % overlap the owner-supplied H33-2-B2 raster (participant-score association unverified) (max equal-mass Jaccard **0.4400** vs the 0.0457 project record). Rejected under the standing brief's uniqueness rule. |
| `gems47-h48-mscl-conf-r1p5-44838px-…-allfinite.tif` | First emission of the same run, before the novelty audit; superseded by the repack file above. |
| `gems47-h48-mscl-conf-r2p5-8176px-…-allfinite.tif` | **Buggy build, kept as a cautionary record.** The snap step collapsed 44,090 base dots onto consensus maxima (kept 2,689) and drove the model DTI 0.196 → 0.056; its sweep numbers (0.0562–0.0649) are artifacts of that collapse and must not be quoted. Fixed in `emit_repack` (one-to-one assignment). |
| `gems47-h47b-tmiup150-xscale-persist-n18524-…-research-not-submittable-20261006.tif` | H47-B research artifact, falsified (fixed-seed random control). |
| `gems47-dcat20-annulus-flankprune-n18524-20261006.tif` | H47-SAF flank-pruning arm; its sensitivity is bracketed only between tested assumptions 0.2200 and 0.2400. The 13th observation is participant-level, not mapped to a TIFF. |
