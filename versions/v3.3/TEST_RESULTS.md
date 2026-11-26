# Design test review — v3.3 candidate (2026-11-26)

This is an evidence audit, **not** independent validation. The repository had no discoverable issue or PR test logs during review.

| Finding | Source | Weakness | Corrective gate |
|---|---|---|---|
| F01 | Recent car concept chat | Text envelope 4750 x 2020 x 1150 mm disagreed with first generated board 4620 x 1980 x 1180 mm | Manifest-led geometry and rejected-visual label |
| F02 | Generated car presentation | Claimed 16 to 11 events (-31%) without traceable individual entries | Stable-ID physical and visual ledgers |
| F03 | Side-surface sketches | Claimed smooth/G2 curvature with no measured derivatives or CAD patches | Position/tangent/curvature test; otherwise UNKNOWN |
| F04 | Car manufacturing narrative | Stamped aluminum, gaps and process claims lacked forming/tolerance stack data | Process and clearance acceptance gate |
| F05 | Multiple rendered viewpoints | 3/4, profile, front and rear are illustrative, not traced to one 3D geometry | Cross-view audit with explicit missing-evidence status |
| F06 | Existing reference's remote-control and speaker notes | Remote thickness 20 mm reported without derivation; speaker volumes stacked without alternatives | Derive bounding boxes from three layout options |

Positive observation: original low, sweeping car silhouette stayed recognizable in the visuals. That is not a manufacturing or independent design-success claim.

## Regression checks required before publication

- Inject false dimensions in a render and demand rejection.
- Duplicate an event ID and require checker FAIL.
- Give a wrong percentage and require FAIL.
- Supply no G2 evidence and require UNKNOWN, never PASS.
- Reconstruct front, profile, rear, three-quarter and detail from one CAD model.
- Verify the legacy rotational profile_check.py is byte-for-byte identical to v3.2.
- Run an independent blind comparison and document evaluator and sample size.

## Status

Source review: completed. New checker execution: not yet verified. Independent blinded comparison: pending. CAD continuity test: pending. Physical safety, aerodynamics, ergonomics and manufacturability: pending.
