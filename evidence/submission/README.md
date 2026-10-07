# Historical H49 builder receipts — superseded interpretation

`bundle_h49.json` and `checks-h49-*.json` are the original builder outputs preserved from main. Their hashes, byte counts, local checks, and raw calculations are retained for provenance; the `all_checks_passed` result did **not** verify that cells outside the footprint were null or NaN. The H49 TIFF read-back is all-finite with no NoData tag and fails the published outside-null/NaN requirement. See [`evidence/h49/format-contract-audit.json`](../h49/format-contract-audit.json).

The companion `bundle_h49.json` now carries a `review_interpretation` object that closes the promotion gate. The nominal 90% conformal number is an assumption-conditional calculation over public proxy blocks; exchangeability is unverified, the operating rule was amended after repeated-split review, and formal coverage of the post-hoc process is not established. The comparator key `REF_incumbent_0.2778` is a legacy label for an **owner-reported d2.8 reference**, not an authenticated leaderboard incumbent. Neither proxy results nor local novelty checks are slot authorization.

The old optional portal-note text is withdrawn. No H49 file is submission-eligible or slot-authorized. Do not upload.
