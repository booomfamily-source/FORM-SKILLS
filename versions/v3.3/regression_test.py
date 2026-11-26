#!/usr/bin/env python3
"""Negative regression cases for FORM SKILLS v3.3 candidate.

Exit 1 until all expected rejection cases are correctly rejected.
Runs the candidate audit() directly; no CAD or manufacturing validation.
"""
import copy
import json
from pathlib import Path
from evidence_check import audit

base = json.loads((Path(__file__).parent / "concept-example.json").read_text(encoding="utf-8"))
tests = []
def case(name, mutate, should_reject):
    d = copy.deepcopy(base)
    mutate(d)
    tests.append((name, d, should_reject))

case("baseline_valid", lambda d: None, False)
case("duplicate_ids", lambda d: d["events"][1].update(id="V01"), True)
case("wrong_reduction", lambda d: d["claims"].update(visual=dict(before=2, after=1, percent=31)), True)
case("correct_reduction", lambda d: d["claims"].update(visual=dict(before=2, after=1, percent=50)), False)
case("g2_claim_without_evidence", lambda d: d["continuity"].update(status="PASS"), True)
case("g2_claim_fake_string", lambda d: d["continuity"].update(status="PASS", evidence="trust me"), True)
case("dimension_conflict_unmodeled", lambda d: d.update(render_dimensions=dict(length_mm=4620,width_mm=1980,height_mm=1180)), True)
case("negative_dimension", lambda d: d["dimensions"].update(height_mm=-5), True)
case("nan_dimension", lambda d: d["dimensions"].update(height_mm=float("nan")), True)
case("missing_event_ledger", lambda d: d.update(events=[]), True)
case("unknown_views", lambda d: d["views"].update(profile="UNKNOWN"), True)
case("missing_units", lambda d: d.pop("dimension_provenance"), True)
case("wrong_assembly_gap", lambda d: d.update(assembly=dict(nominal_mm=3.5,tolerance_mm=4.0)), True)
case("view_marked_pass_without_model", lambda d: d["views"].update(profile="PASS"), True)
case("nonphysical_axis", lambda d: d["axes"].update(x="front to back"), True)
case("wrong_percent_under_rounding", lambda d: d["claims"].update(visual=dict(before=2,after=1,percent=50.2)), True)
case("zero_events_with_false_100_percent", lambda d: (d.update(events=[]), d["claims"].update(visual=dict(before=0,after=0,percent=100))), True)
case("bad_event_type", lambda d: d["events"][0].update(type="manufacture"), True)
case("missing_axes", lambda d: d["axes"].pop("z"), True)
case("physical_count_not_documented", lambda d: d["claims"].update(physical=dict(before=0,after=0,percent=0)), True)
case("zero_axis_physical_semantics", lambda d: d["axes"].update(x="foo",y="bar",z="baz"), True)
case("no_design_constraints", lambda d: d.update(constraints=[]), True)
case("invalid_view_status", lambda d: d["views"].update(detail="DONE"), True)
case("unverified_cad_claim", lambda d: d.update(validation="CAD VERIFIED"), True)

bad=0
for name, doc, expect_reject in tests:
    try:
        findings=audit(doc)
        rejected=any(x["status"]=="FAIL" for x in findings)
    except Exception:
        rejected=True
    passed=(rejected==expect_reject)
    bad+=not passed
    print(("%s" % ("PASS" if passed else "FAIL")).ljust(5), name,
          "expect:", "reject" if expect_reject else "accept",
          "got:", "reject" if rejected else "accept")
print("TOTAL:", len(tests), "PASSED:", len(tests)-bad, "FAILED:", bad)
raise SystemExit(bool(bad))
