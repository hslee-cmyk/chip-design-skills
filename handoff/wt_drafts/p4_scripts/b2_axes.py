"""B2 측정 보조: <root> 사본(수정 없는 HEAD)에서 하네스 회로 θ 한 점 평가 중 LUT 보간 조회의 축별(L·VGS·VDS·VS) 격자 밖 계수.
모듈 전역 _multilinear_interp·_multilinear_interp_point_multi를 계수 래퍼로 바꿔 끼운다(사본 파일은 바꾸지 않음).
사용: python -B b2_axes.py <root> <theta json> <out json>   (P4_CIRCUIT 환경변수로 회로 선택)
"""
import json
import os
import sys
from collections import Counter

root, theta, out = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3]
sys.path.insert(0, os.path.join(root, "workspaces"))
os.chdir(os.path.join(root, "workspaces"))
import run_harness as rh  # noqa: E402
import sizing_recipe as sr  # noqa: E402

AX = ("L", "VGS", "VDS", "VS")
cnt = Counter()
vals = {a: set() for a in AX}
n_calls = Counter()


def chk(grids, pt):
    n_calls["points"] += 1
    for i, a in enumerate(AX):
        g = grids[i]
        lo, hi = float(g[0]), float(g[-1])
        v = float(pt[i])
        if v < lo - 1e-12 or v > hi + 1e-12:
            cnt[a] += 1
            if len(vals[a]) < 40:
                vals[a].add(round(v, 6))


_orig1, _orig2 = sr._multilinear_interp, sr._multilinear_interp_point_multi


def w1(grids, values, points):
    ps = points.tolist() if hasattr(points, "tolist") else points
    if ps and not hasattr(ps[0], "__len__"):
        ps = [ps]
    for p in ps:
        chk(grids, p)
    return _orig1(grids, values, points)


def w2(grids, arrays, point):
    chk(grids, point)
    return _orig2(grids, arrays, point)


sr._multilinear_interp, sr._multilinear_interp_point_multi = w1, w2
CIRCUIT = os.environ.get("P4_CIRCUIT", "folded_cascode")
cfg = rh.SPECS[CIRCUIT]
spec = cfg["spec_fn"]()
ev = sr._build_theta_evaluator(os.path.join(rh.LIBRARY_DIR, cfg["topology_file"]), spec)
ctx, _m = ev["evaluate"](theta)
lut = spec["lut_by_kind"]["nmos"]
grids = {a: [float(x) for x in g] for a, g in zip(AX, (lut.L_grid, lut.VGS_grid, lut.VDS_grid, lut.VS_grid))} if hasattr(lut, "VS_grid") else None
res = {"circuit": CIRCUIT, "theta": theta, "points": n_calls["points"], "out_of_axis": dict(cnt),
       "values": {a: sorted(v) for a, v in vals.items()}, "grid_ranges": {a: [g[0], g[-1]] for a, g in grids.items()} if grids else None}
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False)[:1500])
