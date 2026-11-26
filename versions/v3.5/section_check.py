#!/usr/bin/env python3
"""section_check.py - проверка на сечение на ръб за плоски тела (телефон,
дистанционно, таблет). Допълва profile_check.py, който е за ротационни тела.

Употреба:
    python3 section_check.py spec.json [out.png]

spec.json:
{
  "name": "...",
  "thickness": 7.15,                         # обща дебелина, mm
  "stack": [["стъкло", 0.70], ...],          # слоевете в средата, от лицето към гърба
  "bezel": {"lip": 0.90, "gap": 0.15, "seat": 0.50, "clear": 0.10,
            "border": 0.80, "declared": 2.45},   # от външния ръб до активния екран
  "wall": 1.5,                               # най-тънка странична стена
  "edge": {"nodes": [[u, z, angle], ...]}    # външният контур на ръба
       или {"arc_radius": 0.6}               # прав ръб с две еднакви дъги
}
u = разстояние навътре от най-външната точка, z = дълбочина от лицето.
Ъгъл на допирателната по хода от лицето към гърба: 0 = по лицето навън,
90 = надолу по стената, 180 = по гърба навътре.

"min_blend_mm" (по подразбиране 2.0): под този размер преходът не се оценява
по този числен критерий; това не доказва зрителна неразличимост.

Какво проверява: сбор на стека, сбор на рамката и има ли легло за стъклото,
дебелина на стената, ръбове по контура, плавно ли расте кривината или скача
(обикновена дъга), равни фасети (там ляга широкият отблясък).
Праговете са наши. Програмата не казва дали ръбът е хубав.
"""
import json
import math
import sys

from profile_check import build, number

R0 = 100.0


def arc_edge(T, R, n=400):
    pts = [(1.5 * R + 1.0, 0.0), (R, 0.0)]
    for i in range(1, n + 1):
        a = math.pi / 2 * i / n
        pts.append((R - R * math.sin(a), R - R * math.cos(a)))
    pts.append((0.0, T - R))
    for i in range(1, n + 1):
        a = math.pi / 2 * i / n
        pts.append((R - R * math.cos(a), T - R + R * math.sin(a)))
    pts.append((1.5 * R + 1.0, T))
    return pts


def resample(pts, step):
    out, acc = [pts[0]], 0.0
    for p, q in zip(pts, pts[1:]):
        d = math.dist(p, q)
        while acc + d >= step:
            t = (step - acc) / d
            p = (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
            out.append(p)
            d = math.dist(p, q)
            acc = 0.0
        acc += d
    return out


def analyse(pts, step=0.02):
    """pts в (u, z). Връща мерки на контура."""
    rs = resample(pts, step)
    ang = [math.degrees(math.atan2(q[1] - p[1], p[0] - q[0])) for p, q in zip(rs, rs[1:])]
    dth = [((b - a + 180) % 360) - 180 for a, b in zip(ang, ang[1:])]
    kinks = [(round(rs[i + 1][0], 2), round(rs[i + 1][1], 2), round(d, 1)) for i, d in enumerate(dth) if abs(d) >= 8.0]
    # кривина, изгладена върху 0,1 mm
    w = max(1, int(0.1 / step))
    kap = []
    for i in range(len(ang) - w):
        d = ((ang[i + w] - ang[i] + 180) % 360) - 180
        kap.append(math.radians(d) / (w * step))
    kmax = max((abs(k) for k in kap), default=0.0)
    jump = max((abs(b - a) for a, b in zip(kap, kap[w:])), default=0.0)
    # равни фасети и извитите участъци между тях
    facets, runs, i, last_end = [], [], 0, 0
    def close_run(i0, i1):
        if i1 - i0 < 3:
            return
        seg = rs[i0:i1 + 2]
        size = max(abs(seg[-1][0] - seg[0][0]), abs(seg[-1][1] - seg[0][1]))
        kk = kap[i0:max(i0 + 1, i1 - w)]
        km = max((abs(k) for k in kk), default=0.0)
        jp = max((abs(q - p) for p, q in zip(kk, kk[w:])), default=0.0)
        # входът и изходът също са скок: от равно (0) към първата/последната стойност
        edge_jump = max(abs(kk[0]), abs(kk[-1])) if kk else 0.0
        runs.append({"size": round(size, 2), "min_radius": (1 / km if km else float("inf")),
                     "jump_ratio": (max(jp, edge_jump) / km if km else 0.0),
                     "at": (round(seg[0][0], 2), round(seg[0][1], 2))})
    while i < len(ang):
        j = i
        while j + 1 < len(ang) and abs(((ang[j + 1] - ang[i] + 180) % 360) - 180) <= 0.5:
            j += 1
        length = (j - i + 1) * step
        if length >= 0.3:
            close_run(last_end, i - 1)
            facets.append((round(ang[i]) % 360, round(length, 2)))
            last_end = j + 1
        i = j + 1
    close_run(last_end, len(ang) - 1)
    return {"kinks": kinks, "runs": runs, "facets": facets,
            "start_deg": round(ang[0], 1), "end_deg": round(ang[-1] % 360, 1)}



def validate_spec(spec):
    if not isinstance(spec, dict) or not number(spec.get("thickness")) or spec["thickness"] <= 0:
        raise ValueError("thickness: нужно е положително крайно число")
    stack = spec.get("stack", [])
    if not isinstance(stack, list) or any(not isinstance(x, list) or len(x) != 2 or not isinstance(x[0], str) or not number(x[1]) or x[1] <= 0 for x in stack):
        raise ValueError("stack: нужни са [име, положителна крайна дебелина]")
    bezel = spec.get("bezel", {})
    if not isinstance(bezel, dict) or any(not number(value) or value < 0 for value in bezel.values()):
        raise ValueError("bezel: размерите трябва да са крайни и неотрицателни")
    if "wall" in spec and (not number(spec["wall"]) or spec["wall"] < 0):
        raise ValueError("wall: невалидна дебелина")
    if not number(spec.get("min_blend_mm", 2.0)) or spec.get("min_blend_mm", 2.0) <= 0:
        raise ValueError("min_blend_mm: нужно е положително крайно число")
    edge = spec.get("edge")
    if not isinstance(edge, dict) or ("nodes" in edge) == ("arc_radius" in edge):
        raise ValueError("edge: точно едно от nodes и arc_radius")
    if "arc_radius" in edge:
        radius = edge["arc_radius"]
        if not number(radius) or radius <= 0 or 2 * radius > spec["thickness"]:
            raise ValueError("arc_radius: 0 < 2R <= thickness")
    else:
        nodes = edge["nodes"]
        if not isinstance(nodes, list) or len(nodes) < 2 or any(not isinstance(n, list) or len(n) != 3 or not all(number(x) for x in n) or n[0] < 0 for n in nodes):
            raise ValueError("edge.nodes: нужни са крайни [u,z,angle], u >= 0")
        if abs(nodes[0][1]) > .005 or abs(nodes[-1][1] - spec["thickness"]) > .005:
            raise ValueError("edge.nodes: началото трябва да е z=0, краят z=thickness")
        if any(b[1] < a[1] for a,b in zip(nodes,nodes[1:])):
            raise ValueError("edge.nodes: z не трябва да се връща назад")
        if not number(edge.get("tension", 1.0)) or edge.get("tension", 1.0) <= 0:
            raise ValueError("edge.tension: нужно е положително крайно число")


def run(spec, png=None):
    try:
        validate_spec(spec)
        return _run(spec, png)
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        return "СЕЧЕНИЕТО НЕ МИНАВА: невалиден вход: " + str(exc), False


def _run(spec, png=None):
    L, ok = [], True
    def line(good, text):
        nonlocal ok
        if good is False:
            ok = False
        L.append(("  OK  " if good else "  НЕ  " if good is False else "      ") + text)

    T = spec["thickness"]
    L.append("%s — дебелина %.2f mm" % (spec.get("name", ""), T))
    st = spec.get("stack", [])
    s = sum(v for _, v in st)
    line(abs(s - T) <= 0.005 if st else False,
         "стек: " + " + ".join("%.2f" % v for _, v in st) + " = %.2f (обявено %.2f)" % (s, T) if st else "няма стек")
    b = spec.get("bezel")
    if b and all(k in b for k in ("lip", "gap", "seat", "clear", "border")):
        sb = b["lip"] + b["gap"] + b["seat"] + b["clear"] + b["border"]
        line(abs(sb - b.get("declared", sb)) <= 0.005,
             "рамка: устна %.2f + процеп %.2f + легло %.2f + луфт %.2f + неактивна ивица %.2f = %.2f (обявено %.2f)"
             % (b["lip"], b["gap"], b["seat"], b["clear"], b["border"], sb, b.get("declared", sb)))
        line(b["seat"] >= 0.4, "легло за стъклото %.2f mm (праг 0,40)" % b["seat"])
    else:
        line(False, "рамката не е разложена: няма устна, процеп и легло за стъклото"
             + (" (обявена само %.2f mm)" % b["declared"] if b and "declared" in b else ""))
    if "wall" in spec:
        line(spec["wall"] >= 1.0, "странична стена %.2f mm (праг 1,00)" % spec["wall"])
    else:
        line(False, "няма странична стена в сечението")

    e = spec["edge"]
    if "arc_radius" in e:
        pts = arc_edge(T, e["arc_radius"])
        L.append("      ръб: зададен като дъга R%.2f" % e["arc_radius"])
    else:
        pts = [(R0 - r, z) for r, z in build([[R0 - u, z, a] for u, z, a in e["nodes"]], e.get("tension", 1.0))]
    if any(b[1] < a[1] - 1e-8 for a, b in zip(pts, pts[1:])):
        raise ValueError("построеният ръб се връща назад по z")
    m = analyse(pts)
    line(len(m["kinks"]) == 0, "ръбове по контура: %d %s" % (len(m["kinks"]), m["kinks"][:3] if m["kinks"] else ""))
    BIG = spec.get("min_blend_mm", 2.0)
    for r in m["runs"]:
        big = r["size"] >= BIG
        smooth_k = r["jump_ratio"] < 0.5
        verdict = ("кривината расте плавно" if smooth_k else "кривината скача: обикновена дъга")
        if not big:
            line(None, "малък преход %.2f mm при (u %.2f, z %.2f): най-малък радиус %.2f mm; под %.1f mm преходът не се оценява по този числен критерий"
                 % (r["size"], r["at"][0], r["at"][1], r["min_radius"], BIG))
        else:
            line(smooth_k, "преход %.2f mm при (u %.2f, z %.2f): най-малък радиус %.2f mm; скок %.0f%% — %s"
                 % (r["size"], r["at"][0], r["at"][1], r["min_radius"], 100 * r["jump_ratio"], verdict))
    if not any(r["size"] >= BIG for r in m["runs"]):
        line(None, "няма преход над %.1f mm: ръбът е плоча с прави стени и малки заобляния" % BIG)
    line(None, "допирателна в началото %.0f°, в края %.0f°" % (m["start_deg"], m["end_deg"]))
    names = {0: "лице", 90: "стена (лента)", 180: "гръб"}
    for a, ln in m["facets"]:
        line(None, "равна фасета %s, %.2f mm%s" % (names.get(a, "под %d°" % a), ln,
                                                     " — тук ляга широкият отблясък отстрани" if a == 90 else ""))
    if not any(a == 90 for a, _ in m["facets"]):
        line(None, "няма равна стена: отблясъкът отстрани е тънка линия")
    L.append("СЕЧЕНИЕТО МИНАВА ГЕОМЕТРИЧНИТЕ ПРОВЕРКИ (това не е приемане на проекта)" if ok else "СЕЧЕНИЕТО НЕ МИНАВА: има неизпълнена проверка")
    if png:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 4.2), dpi=150)
        xs = [-p[0] for p in pts]
        zs = [p[1] for p in pts]
        ax.fill(xs + [xs[-1] - 6, xs[0] - 6], zs + [zs[-1], zs[0]], color="#C4C7C9", ec="#333", lw=0.6)
        ax.set_aspect("equal")
        ax.invert_yaxis()
        ax.axis("off")
        ax.set_title(spec.get("name", ""), fontsize=9, loc="left")
        fig.savefig(png, facecolor="#FBFAF7", bbox_inches="tight")
        plt.close(fig)
    return "\n".join(L), ok


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit("Употреба: python3 section_check.py spec.json [out.png]")
    try:
        with open(sys.argv[1], encoding="utf-8") as handle:
            spec = json.load(handle)
        text, ok = run(spec, sys.argv[2] if len(sys.argv) > 2 else None)
        print(text)
        sys.exit(0 if ok else 2)
    except (OSError, ValueError) as exc:
        print("REJECTED: " + str(exc))
        sys.exit(2)
