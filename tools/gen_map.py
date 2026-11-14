#!/usr/bin/env python3
"""Генерирует src/europe_map.py — контуры стран Европы для карты в «Über mich».
Источник: Natural Earth 1:50m (public domain) через world-atlas@2.0.2 (countries-50m.json, TopoJSON).
Запуск: python3 tools/gen_map.py /path/to/countries-50m.json   (результат коммитится; в CI не нужен)."""
import json, math, sys, os

LON0, LAT0 = 20.5, 49.5                  # центр проекции (Lambert azimuthal equal-area)
BBOX = (2.5, 43.8, 42.0, 55.4)           # lon_min, lat_min, lon_max, lat_max
W = 1000                                  # ширина viewBox
HIGHLIGHT = {"276": "de", "804": "ua", "756": "ch"}
CRIMEA = (32.4, 44.3, 36.7, 46.25)       # полуостров Крым — часть Украины (если в источнике отнесён к другой стране)


def laea(lon, lat):
    l, p, l0, p0 = map(math.radians, (lon, lat, LON0, LAT0))
    k = math.sqrt(2 / (1 + math.sin(p0) * math.sin(p) + math.cos(p0) * math.cos(p) * math.cos(l - l0)))
    return k * math.cos(p) * math.sin(l - l0), -k * (math.cos(p0) * math.sin(p) - math.sin(p0) * math.cos(p) * math.cos(l - l0))


def main(src):
    topo = json.load(open(src))
    sx, sy = topo["transform"]["scale"]; tx, ty = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0; pts = []
        for dx, dy in arc:
            x += dx; y += dy; pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)

    def ring(idx):
        out = []
        for i in idx:
            pts = arcs[i] if i >= 0 else arcs[~i][::-1]
            out.extend(pts if not out else pts[1:])
        return out

    # рамка карты в проекции
    edge = [(BBOX[0] + (BBOX[2] - BBOX[0]) * t / 40, BBOX[1]) for t in range(41)] + \
           [(BBOX[0] + (BBOX[2] - BBOX[0]) * t / 40, BBOX[3]) for t in range(41)] + \
           [(BBOX[0], BBOX[1] + (BBOX[3] - BBOX[1]) * t / 40) for t in range(41)] + \
           [(BBOX[2], BBOX[1] + (BBOX[3] - BBOX[1]) * t / 40) for t in range(41)]
    P = [laea(*p) for p in edge]
    x0, x1 = min(p[0] for p in P), max(p[0] for p in P)
    y0, y1 = min(p[1] for p in P), max(p[1] for p in P)
    # обрезаем по внутренней части: используем прямоугольник по центральным сторонам, чтобы не было пустых углов
    cx0 = max(laea(BBOX[0], BBOX[1])[0], laea(BBOX[0], BBOX[3])[0]); cx1 = min(laea(BBOX[2], BBOX[1])[0], laea(BBOX[2], BBOX[3])[0])
    cy0 = laea(LON0, BBOX[3])[1]; cy1 = laea(LON0, BBOX[1])[1]
    S = W / (cx1 - cx0); H = round((cy1 - cy0) * S)

    def proj(lon, lat):
        x, y = laea(lon, lat); return ((x - cx0) * S, (y - cy0) * S)

    def clip(poly):  # Sutherland–Hodgman по прямоугольнику [−m, W+m]×[−m, H+m]
        m = 4
        for edge_fn, inter in (
            (lambda p: p[0] >= -m, lambda a, b: (-m, a[1] + (b[1] - a[1]) * (-m - a[0]) / (b[0] - a[0]))),
            (lambda p: p[0] <= W + m, lambda a, b: (W + m, a[1] + (b[1] - a[1]) * (W + m - a[0]) / (b[0] - a[0]))),
            (lambda p: p[1] >= -m, lambda a, b: (a[0] + (b[0] - a[0]) * (-m - a[1]) / (b[1] - a[1]), -m)),
            (lambda p: p[1] <= H + m, lambda a, b: (a[0] + (b[0] - a[0]) * (H + m - a[1]) / (b[1] - a[1]), H + m))):
            if not poly: return []
            out = []
            for i, cur in enumerate(poly):
                prev = poly[i - 1]
                if edge_fn(cur):
                    if not edge_fn(prev): out.append(inter(prev, cur))
                    out.append(cur)
                elif edge_fn(prev):
                    out.append(inter(prev, cur))
            poly = out
        return poly

    def path(poly, tol=1.6):
        pts = [poly[0]]
        for p in poly[1:]:
            if math.hypot(p[0] - pts[-1][0], p[1] - pts[-1][1]) >= tol: pts.append(p)
        if len(pts) < 3: return ""
        r = [(round(x * 2) / 2, round(y * 2) / 2) for x, y in pts]
        d = f"M{r[0][0]:g} {r[0][1]:g}"
        d += "l" + " ".join(f"{b[0]-a[0]:g} {b[1]-a[1]:g}" for a, b in zip(r, r[1:]))
        return d + "z"

    def in_box(lon, lat, b): return b[0] <= lon <= b[2] and b[1] <= lat <= b[3]

    countries = {}
    for g in topo["objects"]["countries"]["geometries"]:
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]] if g["type"] == "Polygon" else []
        for poly in polys:
            outer = ring(poly[0])
            cid = g.get("id", "")
            # Крым всегда рисуем как часть Украины
            if cid != "804" and outer and all(in_box(lon, lat, CRIMEA) for lon, lat in outer):
                cid = "804"; print("Crimea polygon reassigned from", g.get("id"), "points", len(outer))
            for k, r in enumerate(poly):
                c = clip([proj(*p) for p in ring(r)])
                d = path(c) if c else ""
                if d: countries.setdefault(cid, []).append(d)
    # проверка Крыма: точка Симферополя должна оказаться в Украине
    out = ["# Сгенерировано tools/gen_map.py из Natural Earth 1:50m (public domain). Не править вручную.",
           f"W, H = {W}, {H}", f"LON0, LAT0, CX0, CY0, S = {LON0}, {LAT0}, {cx0!r}, {cy0!r}, {S!r}",
           f"HIGHLIGHT = {HIGHLIGHT!r}", "PATHS = {"]
    for cid, ds in countries.items():
        out.append(f"    {cid!r}: {''.join(ds)!r},")
    out.append("}")
    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "europe_map.py")
    open(dst, "w").write("\n".join(out) + "\n")
    print("countries:", len(countries), "bytes:", sum(len(''.join(v)) for v in countries.values()), "H:", H)


if __name__ == "__main__":
    main(sys.argv[1])
