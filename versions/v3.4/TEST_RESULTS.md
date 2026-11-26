# FORM SKILLS v3.4 — regression and release limits

Tested on 2026-11-26: local `python test_regression.py` with 24 positive and negative cases. Observed **24/24 outcomes matched expectations**; unlike v3.3 (13/24), malformed documents, missing inventories, contradictory render metadata and unsupported PASS states are explicitly rejected or classified as incomplete.

The suite exercises schema and metadata validation only, not real curve/patch geometry. The baseline case is intentionally `INCOMPLETE_EVIDENCE` because no CAD, view models, or physical evidence are supplied. A successful 24/24 result is **not** proof of a ready physical design.

The legacy rotational checker is copied unchanged from v3.2; no additional correctness claim is made for it.

Known limitations:
1. Geometry references, geometry SHA-256 fields and numerical G2 residuals are not independently verified against actual CAD files. They can be asserted dishonestly.
2. `render_dimensions` checks structured metadata only, not words inside a raster image.
3. The axes schema is a vehicle-specific example and rejects other categories until extended.
4. Gap checks do not evaluate true manufacturing capability or full tolerance stack.
5. Independent blind human comparison, physical tests, aerodynamics and safety remain pending.
6. Adversarial and fuzz tests beyond the included 24 cases are pending.

Previous audit: `versions/v3.3/REGRESSION_AUDIT.md`. Preserve all older versions; the new checker is not a substitute for engineering review.
