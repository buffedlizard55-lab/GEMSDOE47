# Portal checklist — no upload or slot use in this review

The standing instruction for this work is **do not upload or spend a competition slot**. No portal login, upload, score request, or final selection was performed. H60 passed the repository's local preregistered scientific gate; organizer acceptance remains untested. H47-C1 remains **RESEARCH ONLY / NOT PROMOTED** and its gate remains closed.

See the [current status and exact-byte encoding audit](current-status.html), [submission guide](HOW_TO_SUBMIT.html), and [H60 evidence page](h60.html).

## H60 exact-file distinction

- **For local format review only:** [`gems47-h60-lidarscarp-s2p0-20261007-nanoutside.tif`](downloads/gems47-h60-lidarscarp-s2p0-20261007-nanoutside.tif), SHA-256 `d75ab9e282422d9592bc835c5cf719b22e6c564730de1f5fc42b57fc5bac2c01`. It has NaN NoData and NaNs outside the TIFF valid-data mask; finite valid values are in [0,1]. This matches the published outside-null/NaN wording locally; it is not organizer-accepted.
- **Diagnostic only:** [`gems47-h60-lidarscarp-s2p0-20261007-allfinite.tif`](downloads/gems47-h60-lidarscarp-s2p0-20261007-allfinite.tif). Every cell is finite and in [0,1], but outside cells are zeros with no NoData tag, so it does not literally meet the published null/NaN-outside requirement. The existing ZIP contains this diagnostic version and must not be described as an upload bundle.
- The earlier portal error `Predicted values must be in range [0, 1]` cannot be diagnosed: the exact rejected bytes and parser receipt are unavailable. Neither encoding has been tested by the portal.

The H60 name and short note are `GEMSDOE47-H60-lidarscarp-s2p0-20261007` and `h60 lidar-scarp d2p0 conformal90`. They are identifiers for a future, separately authorized attempt—not permission to use a slot.

## Official submission allowance vs. account state

The [DOE/NLR official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) states up to **three scoring/feedback submissions per week** and one final selected file for the competition's rounds. This published rules cap does not show this entrant's eligibility, prior submissions, remaining weekly feedback opportunities, or final-selection state; check those account-specific facts in the authenticated portal. Historical leaderboard scores are not upload receipts.

The official public leaderboard's saved observation from 7 October 2026 had rank 1 at 0.3774 and 0.3195 at rank 7. The participant board is dynamic and does not map scores to TIFFs. The H33-2-B2 / 0.2778 association remains owner-reported and unverified. See the [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).

## Future authorized attempt only

If the user separately authorizes a portal attempt, verify current eligibility and account state, read the [official GeoTIFF format instructions](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), hash-check the exact TIFF, and retain the organizer receipt. Submit one TIFF unless the authenticated form explicitly requests an archive. Disclose AI assistance under the official rules. Local mask compatibility, a passing range check, or a local promotion gate does not establish organizer acceptance or a leaderboard score.
