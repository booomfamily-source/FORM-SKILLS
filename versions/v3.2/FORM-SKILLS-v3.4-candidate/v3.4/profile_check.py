#!/usr/bin/env python3
"""profile_check.py - строи и проверява профил на ротационно тяло от числа.

Профилът е крива (r, z): r = радиус, z = разстояние от върха надолу, в mm.
Задава се с възли [r, z, ъгъл]. Ъгълът е посоката на допирателната при
движение от върха към основата:
    0   = хоризонтално навън (продължава плоскост на капак)
    90  = отвесно надолу (права стена)
    180 = хоризонтално навътре (продължава плоскост на дъно)
Между два възела се прекарва крива с нулева кривина в краищата, така че
преходът към права или плоскост е без скок в кривината.

Употреба:
    python3 profile_check.py spec.json [out.png]

spec.json:
{
  "name": "...",
  "nodes": [[r, z, angle], ...],          # от върха към основата
  "points": [[r, z], ...],                # вместо nodes: готов профил, гъсто
                                          # семплиран (стъпка <= 0.1 mm)
  "declared": {"height_mm": .., "diameter_mm": ..},   # обявените габарити
  "keepouts": [{"name": "...", "z0": .., "z1": .., "r": ..}],   # вътрешности
  "wall": 3.0                              # обвивка + стена, mm
}

Програмата не преценява дали формата е хубава. Тя дава мерките, по които
силуетът се описва с думи: ъгли в краищата, дял на правата стена, инфлексии,
къде е най-широкото място и дали вътрешностите се побират.
"""
import json
import math
import sys

N = 400  # проби на сегмент


def hermite5(p0, t0, p1, t1):
    """Квинтичен Ермит с нулева втора производна в двата края."""
    pts = []
    for i in range(N + 1):
        s = i / N
        h00 = 1 - 10 * s**3 + 15 * s**4 - 6 * s**5
        h10 = s - 6 * s**3 + 8 * s**4 - 3 * s**5
        h01 = 10 * s**3 - 15 * s**4 + 6 * s**5
        h11 = -4 * s**3 + 7 * s**4 - 3 * s**5
        pts.append((h00 * p0[0] + h10 * t0[0] + h01 * p1[0] + h11 * t1[0],
                    h00 * p0[1] + h10 * t0[1] + h01 * p1[1] + h11 * t1[1]))
    return pts


def build(nodes, tension=1.25):
    """Връща списък от точки (r, z) по целия профил."""
    out = []
    for a, b in zip(nodes, nodes[1:]):
        chord = math.hypot(b[0] - a[0], b[1] - a[1])
        m = chord * tension
        ta = (m * math.cos(math.radians(a[2])), m * math.sin(math.radians(a[2])))
        tb = (m * math.cos(math.radians(b[2])), m * math.sin(math.radians(b[2])))
        seg = hermite5(a[:2], ta, b[:2], tb)
        out.extend(seg if not out else seg[1:])
    return out


def measure(pts, keepouts=(), wall=0.0, straight_tol=2.0, kink_deg=8.0):
    """Мерки на профил, зададен като точки (r, z)."""
    H = pts[-1][1] - pts[0][1]
    rmax = max(p[0] for p in pts)
    z_at_max = [p[1] for p in pts if p[0] >= rmax - 1e-6]
    z_eq = (z_at_max[0] + z_at_max[-1]) / 2

    ang, straight, length = [], 0.0, 0.0
    for a, b in zip(pts, pts[1:]):
        dr, dz = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dr, dz)
        if d < 1e-9:
            continue
        th = math.degrees(math.atan2(dz, dr))
        ang.append((th, d))
        length += d
        if abs(th - 90.0) <= straight_tol:
            straight += abs(dz)

    # инфлексии: смяна на знака на завиване, с праг срещу шум
    mids = [((p[1] + q[1]) / 2) for p, q in zip(pts, pts[1:])
            if math.hypot(q[0] - p[0], q[1] - p[1]) >= 1e-9]
    turns, acc = [], 0.0
    kinks, min_rc = [], float("inf")
    for i, ((t0, d0), (t1, d1)) in enumerate(zip(ang, ang[1:])):
        dth = (t1 - t0 + 180.0) % 360.0 - 180.0   # без скок при преминаване през 180°
        if abs(dth) >= kink_deg:            # скок в посоката = ръб или стъпало
            kinks.append({"z_mm": round(mids[i + 1], 1), "turn_deg": round(dth, 1)})
        acc += dth
        if abs(acc) >= 1.0:
            turns.append((1 if acc > 0 else -1, mids[i + 1]))
            acc = 0.0
    infl_z = [round(b[1], 1) for a, b in zip(turns, turns[1:]) if a[0] != b[0]]
    inflections = len(infl_z)
    # най-малък радиус на кривина: описана окръжност през точки на ~1 mm по дъгата
    rs, acc_len = [pts[0]], 0.0
    for p, q in zip(pts, pts[1:]):
        acc_len += math.hypot(q[0] - p[0], q[1] - p[1])
        if acc_len >= 1.0:
            rs.append(q)
            acc_len = 0.0
    for p, q, r3 in zip(rs, rs[1:], rs[2:]):
        a_, b_, c_ = math.dist(p, q), math.dist(q, r3), math.dist(p, r3)
        area2 = abs((q[0] - p[0]) * (r3[1] - p[1]) - (r3[0] - p[0]) * (q[1] - p[1]))
        if area2 > 1e-6:
            min_rc = min(min_rc, a_ * b_ * c_ / (2 * area2))
    # гърло: вътрешен локален минимум на радиуса
    necks = []
    for i in range(1, len(pts) - 1):
        lo = pts[i][0]
        if lo < max(p[0] for p in pts[:i]) - 0.5 and lo < max(p[0] for p in pts[i + 1:]) - 0.5 \
                and lo <= pts[i - 1][0] and lo < pts[i + 1][0]:
            necks.append({"z_mm": round(pts[i][1], 1), "d_mm": round(2 * lo, 1)})

    top_angle, bottom_angle = ang[0][0], ang[-1][0]
    # ъгъл между капака (хоризонтал, 0 градуса) и началото на стената
    top_corner = abs(top_angle - 0.0)
    bottom_corner = abs(180.0 - bottom_angle)

    def r_at(z):
        best = None
        for a, b in zip(pts, pts[1:]):
            lo, hi = sorted((a[1], b[1]))
            if lo - 1e-9 <= z <= hi + 1e-9 and abs(b[1] - a[1]) > 1e-9:
                r = a[0] + (b[0] - a[0]) * (z - a[1]) / (b[1] - a[1])
                best = r if best is None else min(best, r)
        return best

    fits = []
    for k in keepouts:
        zs = [k["z0"] + (k["z1"] - k["z0"]) * i / 20 for i in range(21)]
        rs = [r_at(z) for z in zs]
        rs = [r for r in rs if r is not None]
        clear = (min(rs) - wall - k["r"]) if rs else float("nan")
        fits.append({"name": k["name"], "clearance_mm": round(clear, 1), "ok": clear >= 0})

    return {
        "height_mm": round(H, 1),
        "diameter_mm": round(2 * rmax, 1),
        "H_over_D": round(H / (2 * rmax), 3),
        "widest_at_pct_from_top": round(100 * z_eq / H, 1),
        "straight_wall_pct": round(100 * straight / H, 1),
        "inflections": inflections,
        "inflections_at_z_mm": infl_z,
        "kinks": kinks,
        "necks": necks,
        "min_radius_of_curvature_mm": None if min_rc == float("inf") else round(min_rc, 1),
        "top_tangent_deg": round(top_angle, 1),
        "bottom_tangent_deg": round(bottom_angle, 1),
        "top_corner_deg": round(top_corner, 1),
        "bottom_corner_deg": round(bottom_corner, 1),
        "top_d_mm": round(2 * pts[0][0], 1),
        "base_d_mm": round(2 * pts[-1][0], 1),
        "fits": fits,
    }


def read(m):
    """Превежда мерките в изречения за силуета. Правилата са наши."""
    s = []
    if m["top_corner_deg"] >= 45:
        s.append(f"Горе стената среща капака под {m['top_corner_deg']:.0f}°: капакът се чете като отделен диск върху гърло.")
    elif m["top_corner_deg"] <= 10:
        s.append("Горе повърхността продължава плоскостта на върха без ръб.")
    else:
        s.append(f"Горе има мек ръб от {m['top_corner_deg']:.0f}°.")
    if m["bottom_corner_deg"] >= 45:
        s.append(f"Долу стената стъпва под {m['bottom_corner_deg']:.0f}°: тялото стои върху цокъл.")
    else:
        s.append("Долу тялото се прибира под себе си и сянката го отделя от плота.")
    if m["straight_wall_pct"] >= 40:
        s.append(f"{m['straight_wall_pct']:.0f}% от височината е права стена: водещият жест е цилиндър с обработени краища.")
    elif m["straight_wall_pct"] <= 10:
        s.append("Почти няма права стена: контурът е една крива.")
    else:
        s.append(f"{m['straight_wall_pct']:.0f}% от височината е права стена.")
    if m["inflections"] == 0:
        s.append("Няма инфлексия: контурът е изпъкнал навсякъде.")
    else:
        s.append(f"{m['inflections']} инфлексии (z = {', '.join(str(z) for z in m['inflections_at_z_mm'])} mm): контурът сменя посоката на завиване и се чете като рамо или шия.")
    for k in m["kinks"]:
        s.append(f"Ръб или стъпало на z = {k['z_mm']} mm (скок {k['turn_deg']}°).")
    for k in m["necks"]:
        s.append(f"Гърло на z = {k['z_mm']} mm, Ø{k['d_mm']} mm.")
    w = m["widest_at_pct_from_top"]
    s.append(f"Най-широкото място е на {w:.0f}% от върха: масата е " +
             ("високо." if w < 42 else "ниско." if w > 58 else "в средата."))
    bad = [f for f in m["fits"] if not f["ok"]]
    if bad:
        s.append("Не се побира: " + ", ".join(f"{f['name']} ({f['clearance_mm']} mm)" for f in bad) + ".")
    elif m["fits"]:
        s.append("Вътрешностите се побират; най-малък запас " +
                 f"{min(f['clearance_mm'] for f in m['fits'])} mm.")
    return s


def draw(items, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, len(items), figsize=(5.2 * len(items), 5.7), dpi=150)
    if len(items) == 1:
        axes = [axes]
    for ax, (title, pts, keepouts, m, lines) in zip(axes, items):
        r = [p[0] for p in pts]
        z = [p[1] for p in pts]
        ax.fill(r + [-x for x in reversed(r)], z + list(reversed(z)), color="#2B2A28", zorder=1)
        for k in keepouts:
            ax.add_patch(plt.Rectangle((-k["r"], k["z0"]), 2 * k["r"], k["z1"] - k["z0"],
                                       fill=False, ec="#E9A15F", lw=0.9, zorder=2))
            ax.text(0, (k["z0"] + k["z1"]) / 2, k["name"], color="#E9A15F", fontsize=6.5,
                    ha="center", va="center", zorder=3)
        ax.set_aspect("equal")
        ax.set_xlim(-105, 105)
        ax.set_ylim(max(z) + 12, min(z) - 12)
        ax.axhline(max(z), color="#B9B2A6", lw=0.8, zorder=0)
        ax.axis("off")
        ax.set_title(title, fontsize=11, loc="left", color="#1B1A18")
        txt = (f"Ø{m['diameter_mm']:.0f} × {m['height_mm']:.0f} mm · В/Д {m['H_over_D']}\n"
               f"права стена {m['straight_wall_pct']:.0f}% · инфлексии {m['inflections']} · "
               f"ъгъл горе {m['top_corner_deg']:.0f}°, долу {m['bottom_corner_deg']:.0f}°\n\n"
               + "\n".join("– " + l for l in lines))
        ax.text(0.0, -0.02, txt, transform=ax.transAxes, fontsize=7.2, va="top", color="#3A3833",
                wrap=True)
    fig.subplots_adjust(left=0.04, right=0.98, top=0.94, bottom=0.27, wspace=0.08)
    fig.savefig(path, facecolor="#F4F1EB")


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    if "points" in spec:                      # готов профил от собствена формула
        pts = [tuple(p) for p in spec["points"]]
    else:
        pts = build(spec["nodes"], spec.get("tension", 1.25))
    m = measure(pts, spec.get("keepouts", ()), spec.get("wall", 0.0))
    lines = read(m)
    print(json.dumps(m, ensure_ascii=False, indent=1))
    print("\n".join(lines))
    for key, label in (("height_mm", "височина"), ("diameter_mm", "диаметър")):
        want = spec.get("declared", {}).get(key)
        if want is not None:
            diff = m[key] - want
            print(f"Обявен {label} {want} mm, построен {m[key]} mm: " +
                  ("съвпада." if abs(diff) <= 0.5 else f"РАЗМИНАВАНЕ {diff:+.1f} mm."))
    if len(sys.argv) > 2:
        draw([(spec.get("name", ""), pts, spec.get("keepouts", ()), m, lines)], sys.argv[2])
