# Superseded artifacts (do not submit)

Kept only so that every number on the site can be checked against real bytes. None of these
is the current candidate; the current candidate is one directory up.

| file | why it is here |
|---|---|
| `gems47-h48-mscl-repack-r1p5-44838px-…-allfinite.tif` | H48 **repack** arm, 2026-10-06 20:32Z. Format-valid (21/21) and it wins both blocked holdout frames vs the incumbent (0.0404/0.1081 vs 0.0067/0.0989), but it **re-issues a prior submission**: 59.2 % of its pixels are the 0.2600 field's and 66.9 % of them are the reported-0.2778 field's (max equal-mass Jaccard **0.4400** vs the 0.0457 project record). Rejected under the standing brief's uniqueness rule. |
| `gems47-h48-mscl-conf-r1p5-44838px-…-allfinite.tif` | First emission of the same run, before the novelty audit; superseded by the repack file above. |
| `gems47-h48-mscl-conf-r2p5-8176px-…-allfinite.tif` | **Buggy build, kept as a cautionary record.** The snap step collapsed 44,090 base dots onto consensus maxima (kept 2,689) and drove the model DTI 0.196 → 0.056; its sweep numbers (0.0562–0.0649) are artifacts of that collapse and must not be quoted. Fixed in `emit_repack` (one-to-one assignment). |
| `gems47-h47b-tmiup150-xscale-persist-n18524-…-research-not-submittable-20261006.tif` | H47-B research artifact, falsified (fixed-seed random control). |
| `gems47-dcat20-annulus-flankprune-n18524-20261006.tif` | H47-SAF flank-pruning arm, falsified against the 13th return. |
