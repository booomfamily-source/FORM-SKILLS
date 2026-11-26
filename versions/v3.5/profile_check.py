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
import textwrap

N = 400  # проби на сегмент


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_points(pts, max_step=None):
    if not isinstance(pts, (list, tuple)) or len(pts) < 2:
        raise ValueError("profile: нужни са поне две точки")
    for point in pts:
        if not isinstance(point, (list, tuple)) or len(point) != 2 or not all(number(x) for x in point) or point[0] < 0:
            raise ValueError("profile: точките са [r,z], крайни числа, r >= 0")
    if pts[-1][1] <= pts[0][1] or max(p[0] for p in pts) <= 0:
        raise ValueError("profile: височината и диаметърът трябва да са положителни")
    for a, b in zip(pts, pts[1:]):
        if b[1] < a[1] - 1e-8:
            raise ValueError("profile: z се връща назад; този checker изисква монотонен профил")
        distance = math.dist(a, b)
        if distance < 1e-12:
            raise ValueError("profile: съседни съвпадащи точки")
        if max_step is not None and distance > max_step + 1e-8:
            raise ValueError("points: стъпката надвишава 0.1 mm")


def evaluate(spec):
    """Validate a complete input and check unrounded dimensions and clearances.

    `wall` remains a radial allowance; it is not a normal shell-thickness or
    axial-cap check. All geometric results concern the sampled polyline.
    """
    if not isinstance(spec, dict) or ("nodes" in spec) == ("points" in spec):
        raise ValueError("spec: задайте точно едно от nodes и points")
    declared = spec.get("declared")
    if not isinstance(declared, dict) or not all(number(declared.get(k)) and declared[k] > 0 for k in ("height_mm", "diameter_mm")):
        raise ValueError("declared: нужни са положителни крайни height_mm и diameter_mm")
    if not number(spec.get("wall")) or spec["wall"] < 0 or not isinstance(spec.get("keepouts"), list):
        raise ValueError("wall и списъкът keepouts са задължителни; wall >= 0")
    if "points" in spec:
        pts = spec["points"]
        validate_points(pts, 0.1)
    else:
        nodes = spec["nodes"]
        if not isinstance(nodes, list) or len(nodes) < 2:
            raise ValueError("nodes: нужни са поне два възела")
        if any(not isinstance(n, (list, tuple)) or len(n) != 3 or not all(number(x) for x in n) or n[0] < 0 for n in nodes):
            raise ValueError("nodes: нужни са крайни [r,z,angle], r >= 0")
        tension = spec.get("tension", 1.25)
        if not number(tension) or tension <= 0:
            raise ValueError("tension: нужно е положително крайно число")
        pts = build(nodes, tension)
        validate_points(pts)
    m = measure(pts, spec["keepouts"], spec["wall"])
    raw = {"height_mm": pts[-1][1] - pts[0][1], "diameter_mm": 2 * max(p[0] for p in pts)}
    errors = []
    for key, actual in raw.items():
        if abs(actual - declared[key]) > 0.5:
            errors.append("%s: обявено %.6g, построено %.6g mm (числен праг 0.5 mm)" % (key, declared[key], actual))
    for fit in m["fits"]:
        if not fit["ok"]:
            errors.append("keepout %s: %s" % (fit["name"], "извън z-границите" if not fit["z_covered"] else "недостатъчен радиален запас"))
    m["raw_dimensions"] = raw
    m["limits"] = "Семплиран профил; wall е радиален резерв; не проверява крайни стени, 3D сглобка или G2 на повърхнина."
    return pts, m, errors


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
    validate_points(pts)
    if not number(wall) or wall < 0:
        raise ValueError("wall: нужен е неотрицателен краен радиален резерв")
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
        if not isinstance(k, dict) or not all(number(k.get(key)) for key in ("z0", "z1", "r")):
            raise ValueError("keepout: нужни са крайни z0, z1 и r")
        if k["z1"] <= k["z0"] or k["r"] < 0 or not isinstance(k.get("name"), str):
            raise ValueError("keepout: невалиден интервал, радиус или име")
        covered = k["z0"] >= pts[0][1] and k["z1"] <= pts[-1][1]
        # For this piecewise-linear profile, a minimum occurs at a knot or
        # a clipped interval endpoint. No fixed set of 21 stations can prove fit.
        zs = [k["z0"], k["z1"]]
        radii = [p[0] for p in pts if k["z0"] <= p[1] <= k["z1"]]
        radii.extend(r for r in (r_at(z) for z in zs) if r is not None)
        clear = min(radii) - wall - k["r"] if covered and radii else None
        fits.append({"name": k["name"], "clearance_mm": clear,
                     "z_covered": covered, "ok": covered and clear is not None and clear >= 0})

    return {
        "height_mm": round(H, 1),
        "diameter_mm": round(2 * rmax, 1),
        "H_over_D": round(H / (2 * rmax), 3),
        "widest_at_pct_from_top": round(100 * (z_eq - pts[0][1]) / H, 1),
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
        s.append(f"Горе допирателната е под {m['top_corner_deg']:.0f}° спрямо хоризонталата; това само не доказва гърло или отделен капак.")
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
        s.append("Не е открита инфлексия при използваното семплиране и праг; това не е доказателство за изпъкналост на 3D тялото.")
    else:
        s.append(f"{m['inflections']} инфлексии (z = {', '.join(str(z) for z in m['inflections_at_z_mm'])} mm): контурът сменя посоката на завиване и се чете като рамо или шия.")
    for k in m["kinks"]:
        s.append(f"Ръб или стъпало на z = {k['z_mm']} mm (скок {k['turn_deg']}°).")
    for k in m["necks"]:
        s.append(f"Гърло на z = {k['z_mm']} mm, Ø{k['d_mm']} mm.")
    w = m["widest_at_pct_from_top"]
    s.append(f"Най-широкото място е на {w:.0f}% от височината; това не определя центъра на тежестта.")
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
        span = max(abs(value) for value in r) * 1.15
        ax.set_xlim(-span, span)
        ax.set_ylim(max(z) + 12, min(z) - 12)
        ax.axhline(max(z), color="#B9B2A6", lw=0.8, zorder=0)
        ax.axis("off")
        ax.set_title(title, fontsize=11, loc="left", color="#1B1A18")
        txt = (f"Ø{m['diameter_mm']:.0f} × {m['height_mm']:.0f} mm · В/Д {m['H_over_D']}\n"
               f"права стена {m['straight_wall_pct']:.0f}% · инфлексии {m['inflections']} · "
               f"ъгъл горе {m['top_corner_deg']:.0f}°, долу {m['bottom_corner_deg']:.0f}°\n\n"
               + "\n".join("– " + l for l in lines))
        txt = "\n".join(textwrap.fill(line, width=76) for line in txt.split("\n"))
        ax.text(0.0, -0.02, txt, transform=ax.transAxes, fontsize=7.2, va="top", color="#3A3833")
    fig.subplots_adjust(left=0.04, right=0.98, top=0.94, bottom=0.27, wspace=0.08)
    fig.savefig(path, facecolor="#F4F1EB", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit("Употреба: python3 profile_check.py spec.json [out.png]")
    try:
        with open(sys.argv[1], encoding="utf-8") as handle:
            spec = json.load(handle)
        pts, m, errors = evaluate(spec)
        lines = read(m)
        print(json.dumps(m, ensure_ascii=False, indent=1, allow_nan=False))
        print("\n".join(lines))
        for error in errors:
            print("ОТХВЪРЛЕНО: " + error)
        if len(sys.argv) > 2:
            draw([(spec.get("name", ""), pts, spec["keepouts"], m, lines)], sys.argv[2])
        sys.exit(2 if errors else 0)
    except (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        print("REJECTED: " + str(exc))
        sys.exit(2)
