#!/usr/bin/env python3
"""Регресия за FORM SKILLS v3.4 candidate.

Съдържа 24-те случая от v3.3 със същите промени върху същия манифест и
пет нови. Очакването вече е един от три статуса, не „приема/отхвърля“.
"""
import copy
import json
import shutil
import tempfile
from pathlib import Path

from project_check import audit

HERE = Path(__file__).resolve().parent
EX = HERE / "examples"
base = json.loads((EX / "concept-example-v3.3.json").read_text(encoding="utf-8"))
R, I, P = "REJECTED", "PROJECT_INCOMPLETE", "CHECKS_PASS"
tests = []
def case(name, mutate, expect):
    d = copy.deepcopy(base)
    mutate(d)
    tests.append((name, d, expect))

# --- 24-те случая от v3.3
case("baseline_valid", lambda d: None, I)
case("duplicate_ids", lambda d: d["events"][1].update(id="V01"), R)
case("wrong_reduction", lambda d: d["claims"].update(visual=dict(before=2, after=1, percent=31)), R)
case("correct_reduction", lambda d: d["claims"].update(visual=dict(before=2, after=1, percent=50)), I)
case("g2_claim_without_evidence", lambda d: d["continuity"].update(status="PASS"), R)
case("g2_claim_fake_string", lambda d: d["continuity"].update(status="PASS", evidence="trust me"), R)
case("dimension_conflict_unmodeled", lambda d: d.update(render_dimensions=dict(length_mm=4620, width_mm=1980, height_mm=1180)), R)
case("negative_dimension", lambda d: d["dimensions"].update(height_mm=-5), R)
case("nan_dimension", lambda d: d["dimensions"].update(height_mm=float("nan")), R)
case("missing_event_ledger", lambda d: d.update(events=[]), R)
case("unknown_views", lambda d: d["views"].update(profile="UNKNOWN"), I)   # същият документ като baseline_valid
case("missing_units", lambda d: d.pop("dimension_provenance"), R)
case("wrong_assembly_gap", lambda d: d.update(assembly=dict(nominal_mm=3.5, tolerance_mm=4.0)), R)
case("view_marked_pass_without_model", lambda d: d["views"].update(profile="PASS"), R)
case("nonphysical_axis", lambda d: d["axes"].update(x="front to back"), R)
case("wrong_percent_under_rounding", lambda d: d["claims"].update(visual=dict(before=2, after=1, percent=50.2)), R)
case("zero_events_with_false_100_percent", lambda d: (d.update(events=[]), d["claims"].update(visual=dict(before=0, after=0, percent=100))), R)
case("bad_event_type", lambda d: d["events"][0].update(type="manufacture"), R)
case("missing_axes", lambda d: d["axes"].pop("z"), R)
case("physical_count_not_documented", lambda d: d["claims"].update(physical=dict(before=0, after=0, percent=0)), R)
case("zero_axis_physical_semantics", lambda d: d["axes"].update(x="foo", y="bar", z="baz"), R)
case("no_design_constraints", lambda d: d.update(constraints=[]), R)
case("invalid_view_status", lambda d: d["views"].update(detail="DONE"), R)
case("unverified_cad_claim", lambda d: d.update(validation="CAD VERIFIED"), R)

# --- нови: доказателството се преизчислява
case("g2_recomputed_plain_arc", lambda d: d["continuity"].update(status="PASS", check=dict(tool="section_check", spec="arc-r3-edge.json")), R)
case("g2_recomputed_smooth_blend", lambda d: d["continuity"].update(status="PASS", check=dict(tool="section_check", spec="form04-edge.json")), I)
case("g2_spec_file_missing", lambda d: d["continuity"].update(status="PASS", check=dict(tool="section_check", spec="nope.json")), R)
case("conflicting_render_labelled_rejected", lambda d: d.update(render_dimensions=dict(length_mm=4620, width_mm=1980, height_mm=1180), render_status="REJECTED_VISUAL"), I)
def complete(d):
    d.update(constraints=["test"], joints=[dict(name="j", nominal_mm=3.5, tolerance_mm=0.5)],
             view_sources={v: "form04.svg" for v in d["views"]})
    d["views"].update({v: "PASS" for v in d["views"]})
    d["continuity"].update(status="PASS", check=dict(tool="section_check", spec="form04-edge.json"))
case("complete_synthetic", complete, P)

bad = 0
for name, doc, expect in tests:
    try:
        got = audit(doc, EX)["status"]
    except Exception as e:           # A crash is not a rejection diagnostic.
        got = "CRASH: " + type(e).__name__
    ok = got == expect
    bad += not ok
    print(("PASS" if ok else "FAIL").ljust(5), name.ljust(40), "очаквано", expect.ljust(19), "получено", got)
print("ОБЩО:", len(tests), "СЪВПАДАТ:", len(tests) - bad, "НЕ СЪВПАДАТ:", bad)
raise SystemExit(bool(bad))
