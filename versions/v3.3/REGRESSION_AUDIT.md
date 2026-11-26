# FORM SKILLS v3.3 — critical regression audit
Date: 2026-11-26. Target: candidate branch upgrade/v3.3-design-evidence, PR #1.
Status: **BLOCKED — NOT RELEASE READY**. v3.2 is still published. This is a software/schema test only.

## Reproduction
The tested script was byte-identical to the GitHub blob b5fdbd9fc761904c80687857b0c8863602137508 (verified with git hash-object on local executable copy). Used the repository's concept-example.json as the baseline and 23 systematically mutated inputs. Each case executed as an external Python process with JSON and return-code inspection. No CAD geometry, physical product or render image was produced or validated.

Exit convention: 0 = checker accepts, 1 = checker rejects. Expectations below are acceptance expectations under the v3.3 documented requirements; when a requirement is merely a semantic or release-level concern, the current checker returning 0 is a release-gate gap, not a Python runtime error.

Result: **13/24 expected outcomes met; 11/24 unmet**.

| Case | Expected | Actual | Verdict |
|---|---:|---:|---|
| baseline_valid | 0 | 0 | PASS (schema only) |
| duplicate_ids | 1 | 1 | PASS |
| wrong_reduction | 1 | 1 | PASS |
| correct_reduction | 0 | 0 | PASS |
| g2_claim_without_evidence | 1 | 1 | PASS |
| g2_claim_fake_string | 1 | 0 | FAIL |
| dimension_conflict_unmodeled | 1 | 0 | FAIL |
| negative_dimension | 1 | 1 | PASS |
| nan_dimension | 1 | 1 | PASS |
| missing_event_ledger | 1 | 0 | FAIL |
| unknown_views | 1 | 0 | FAIL as release gate |
| missing_units | 1 | 0 | FAIL |
| wrong_assembly_gap | 1 | 0 | FAIL |
| view_marked_pass_without_model | 1 | 0 | FAIL |
| nonphysical_axis | 1 | 0 | FAIL |
| wrong_percent_under_rounding | 1 | 1 | PASS |
| zero_events_with_false_100_percent | 1 | 1 | PASS |
| bad_event_type | 1 | 1 | PASS |
| missing_axes | 1 | 1 | PASS |
| physical_count_not_documented | 1 | 1 | PASS |
| zero_axis_physical_semantics | 1 | 0 | FAIL |
| no_design_constraints | 1 | 0 | FAIL |
| invalid_view_status | 1 | 1 | PASS |
| unverified_cad_claim | 1 | 0 | FAIL |

## Release blocking findings

P0 / G-01. The machine-readable source of truth does not check image annotations, alternative declared dimensional values, cross-file consistency, or locked-constraint changes. A manifest may pass while a render contradicts it.

P0 / G-02. Evidence is checked by nonempty-string truthiness: arbitrary prose satisfies a G2 PASS claim. Mathematical continuity (G0/G1/G2), 3D CAD, tolerance and model-provenance validation are absent.

P0 / G-03. A manifest containing zero physical and zero visual events is accepted, and missing constraints/provenance metadata are accepted. No complete geometry-to-inventory trace exists.

P0 / G-04. Unknown or unsupported viewpoints pass the structural checker. Distinguish schema-valid, design-incomplete, and releasable project verdicts. UNKNOWN is permitted documentation but not evidence of completed design verification.

P1 / G-05. Manufacturing gap stack and tolerance limits are ignored. Invalid assumptions (tolerance > nominal gap) can pass without warning.

P1 / G-06. Axis labels are only tested for distinct strings and not orientation or consistent physical meaning.

P1 / G-07. No independent blind human comparison, CAD continuity proof, process capability, assembly study, ergonomic, safety, structural or aerodynamic validation. These require external evidence and are not solved by Python alone.

## Relative assessment: v3.2 versus v3.3
v3.2 already mandates source-derived CAD/SVG, ten acceptance conditions, layout evaluation, rotational profile verification, and rejecting inconsistent renders. v3.3 adds explicit manifest, counts and audit language, but the new checker presently verifies only a subset of these promises. Thus no demonstrated design-quality improvement or independent validation exists yet. Retaining byte-identical profile_check.py protects rotational checker behavior but does not establish its correctness or safety.

## Required next fixes
1. Add strict schema and explicit versioned datum/unit/constraint definitions, reject unknown keys or audit them.
2. Separate schema outcome from project release-readiness; UNKNOWN and missing proof are blockers to release, not parser failures.
3. Validate typed evidence records with actual numeric curve/patch continuity data, not filenames or prose.
4. Introduce cross-artifact dimensional reconciliation between manifest, CAD, drawings and generated captions.
5. Require full event inventory with stable IDs, physical/visual split and view-to-feature linkage.
6. Validate tolerance stack / tool-access and assembly paths with domain-specific checkers.
7. Implement automated test suite using these negative cases and CI; archive stdout, fixtures, expected/actual.
8. Execute a blinded v3.2 vs v3.3 design task comparison with independent reviewer, fixed prompts and identical tools.

## Limits of this audit
These tests exercise a locally materialized copy of the **exact GitHub checker** plus intentionally constructed JSON variants; they do not claim live GitHub Actions execution. Any wording that implies independent validation, CAD verification or proven manufacturability is unsupported. User approval is required before changing LATEST or merging the PR.
