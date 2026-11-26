#!/usr/bin/env python3
"""FORM SKILLS v3.4 candidate - project_check.py

Замества evidence_check.py от v3.3. Разликата: декларация не е доказателство.
Където манифестът твърди нещо за геометрията, проверката го преизчислява със
section_check.py или profile_check.py от посочения файл с числа.

Употреба:  python3 project_check.py manifest.json

Три изхода, които не се смесват:
  REJECTED            (код 2)  манифестът е невалиден или твърдение е опровергано
  PROJECT_INCOMPLETE  (код 1)  манифестът е валиден, но нещо още не е доказано
  CHECKS_PASS         (код 0)  всичко заявено е преизчислено и съвпада

CHECKS_PASS не е приемане за производство и не е независима оценка на дизайна.
Проверката не вижда CAD, хват, здравина, топлина, акустика или безопасност.
"""
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

VIEWS = ("profile", "front", "rear", "three_quarter", "detail")
AXIS_WORD = {"x": "length", "y": "width", "z": "height"}
EVENT_TYPES = ("physical", "visual")


def audit(doc, base_dir="."):
    base = Path(base_dir)
    rejected, incomplete, info = [], [], []

    def num(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)

    # --- размери, единици, произход
    dims = doc.get("dimensions", {})
    keys = ("length_mm", "width_mm", "height_mm")
    vals = [dims.get(k) for k in keys]
    if not all(num(v) and v > 0 for v in vals):
        rejected.append("dimensions: нужни са три положителни крайни размера в mm")
    prov = doc.get("dimension_provenance")
    if not (isinstance(prov, str) and prov.strip()):
        rejected.append("dimension_provenance: липсва произход на размерите (дадени, изведени или допускане)")

    # --- оси: една и съща координатна система за всички проекти
    axes = doc.get("axes", {})
    for a, word in AXIS_WORD.items():
        v = axes.get(a)
        if not (isinstance(v, str) and v.strip().lower().startswith(word)):
            rejected.append("axes.%s: трябва да започва с '%s' (x=length, y=width, z=height)" % (a, word))

    # --- заключени изисквания
    if "constraints" not in doc:
        incomplete.append("constraints: няма списък на заключените изисквания")
    elif not (isinstance(doc["constraints"], list) and doc["constraints"]):
        rejected.append("constraints: списъкът е празен")

    # --- регистър на събитията
    events = doc.get("events")
    if not (isinstance(events, list) and events):
        rejected.append("events: регистърът е празен или липсва")
        events = []
    ids = [e.get("id") for e in events]
    if len(ids) != len(set(ids)) or not all(isinstance(i, str) and i for i in ids):
        rejected.append("events: идентификаторите трябва да са уникални и непразни")
    for e in events:
        if e.get("type") not in EVENT_TYPES or not isinstance(e.get("before"), bool) or not isinstance(e.get("after"), bool):
            rejected.append("events.%s: нужни са type (physical|visual), before и after" % e.get("id"))
    for kind in EVENT_TYPES:
        claim = doc.get("claims", {}).get(kind)
        if not claim:
            continue
        b = sum(e.get("before") is True for e in events if e.get("type") == kind)
        a = sum(e.get("after") is True for e in events if e.get("type") == kind)
        if b == 0:
            rejected.append("claims.%s: няма нито едно събитие от този вид в регистъра" % kind)
            continue
        exp = round(100 * (b - a) / b, 1)
        if claim.get("before") != b or claim.get("after") != a or not num(claim.get("percent")) or abs(claim["percent"] - exp) > 0.05:
            rejected.append("claims.%s: по регистъра е %d -> %d = %.1f%%, заявено %s -> %s = %s%%"
                            % (kind, b, a, exp, claim.get("before"), claim.get("after"), claim.get("percent")))
        else:
            info.append("редукция %s: %d -> %d = %.1f%%" % (kind, b, a, exp))

    # --- сглобки
    joints = doc.get("joints", [])
    if "assembly" in doc:
        joints = joints + [dict(doc["assembly"], name="assembly")]
    for j in joints:
        g, t = j.get("nominal_mm"), j.get("tolerance_mm")
        if not (num(g) and num(t) and g > 0 and t > 0):
            rejected.append("joint %s: процепът и допускът трябва да са положителни числа" % j.get("name"))
        elif t >= g:
            rejected.append("joint %s: допуск ±%.2f при процеп %.2f позволява частите да се застъпят" % (j.get("name"), t, g))
        else:
            info.append("сглобка %s: %.2f ±%.2f mm = %.0f%% от процепа" % (j.get("name"), g, t, 100 * t / g))
    if not joints:
        incomplete.append("joints: няма нито една описана сглобка")

    # --- изображения с различни размери
    for r in ([{"name": "render", "dimensions": doc["render_dimensions"], "status": doc.get("render_status")}]
              if "render_dimensions" in doc else []) + doc.get("visuals", []):
        d = r.get("dimensions", {})
        if any(k in d and d[k] != dims.get(k) for k in keys) and r.get("status") != "REJECTED_VISUAL":
            rejected.append("visual %s: размерите му се различават от манифеста и не е отбелязан като REJECTED_VISUAL" % r.get("name"))

    # --- изгледи: PASS само ако изгледът е построен от файла с числата
    views = doc.get("views", {})
    src = doc.get("view_sources", {})
    for v in VIEWS:
        st = views.get(v)
        if st not in ("PASS", "FAIL", "UNKNOWN"):
            rejected.append("views.%s: статусът трябва да е PASS, FAIL или UNKNOWN" % v)
        elif st == "PASS":
            f = src.get(v)
            if not (f and (base / f).is_file()):
                rejected.append("views.%s: PASS без съществуващ файл, построен от числата (view_sources)" % v)
        else:
            incomplete.append("views.%s: %s" % (v, st))

    # --- непрекъснатост: преизчислява се, текст не се приема
    cont = doc.get("continuity", {})
    st = cont.get("status")
    chk = cont.get("check")
    if st == "PASS":
        if not (isinstance(chk, dict) and chk.get("tool") in ("section_check", "profile_check") and chk.get("spec")):
            rejected.append("continuity: PASS без check {tool, spec}; текстово доказателство не се приема")
        else:
            p = base / chk["spec"]
            if not p.is_file():
                rejected.append("continuity: файлът %s липсва" % chk["spec"])
            else:
                spec = json.load(open(p, encoding="utf-8"))
                if chk["tool"] == "section_check":
                    import section_check
                    text, ok = section_check.run(spec)
                    if not ok:
                        rejected.append("continuity: section_check отхвърля %s" % chk["spec"])
                    info.append("section_check:\n" + text)
                else:
                    import profile_check
                    pts = [tuple(q) for q in spec["points"]] if "points" in spec else profile_check.build(spec["nodes"], spec.get("tension", 1.25))
                    m = profile_check.measure(pts, spec.get("keepouts", ()), spec.get("wall", 0.0))
                    bad = [f["name"] for f in m["fits"] if not f["ok"]]
                    if m["kinks"] or m["necks"] or bad:
                        rejected.append("continuity: profile_check намира ръбове %d, гърла %d, непобиращи се %s"
                                        % (len(m["kinks"]), len(m["necks"]), bad))
                    info.append("profile_check: ръбове %d, гърла %d, инфлексии %d" % (len(m["kinks"]), len(m["necks"]), m["inflections"]))
    elif st in (None, "UNKNOWN"):
        incomplete.append("continuity: не е проверена")
    elif st != "FAIL":
        rejected.append("continuity.status: PASS, FAIL или UNKNOWN")

    # --- твърдения за CAD и физическа проверка
    blob = " ".join(str(doc.get(k, "")) for k in ("validation", "notes"))
    if re.search(r"(cad|physical|физич)\w*\W+(\w+\W+){0,3}(verified|validated|проверен|валидиран)", blob, re.I) or doc.get("cad_verified") is True:
        f = doc.get("cad_file")
        if not (f and (base / f).is_file()):
            rejected.append("validation: твърди се CAD или физическа проверка без приложен файл")

    status = "REJECTED" if rejected else "PROJECT_INCOMPLETE" if incomplete else "CHECKS_PASS"
    return {"status": status, "rejected": rejected, "incomplete": incomplete, "info": info}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Употреба: python3 project_check.py manifest.json")
    path = Path(sys.argv[1])
    res = audit(json.load(open(path, encoding="utf-8")), path.parent)
    print(res["status"])
    for k, label in (("rejected", "ОТХВЪРЛЕНО"), ("incomplete", "НЕДОКАЗАНО"), ("info", "ПРЕИЗЧИСЛЕНО")):
        for line in res[k]:
            print("  %s: %s" % (label, line))
    print("CHECKS_PASS не е приемане за производство и не е независима оценка на дизайна.")
    sys.exit({"REJECTED": 2, "PROJECT_INCOMPLETE": 1, "CHECKS_PASS": 0}[res["status"]])
