"""B2 측정 보조: <root> 사본에서 하네스 회로(P4_CIRCUIT, 기본 folded_cascode)의 θ 한 점을 평가한 뒤
propagate_node_voltages(spec vdd)의 conflicts·unresolved, 소자별 source 노드 전압과 vsb, LUT VS 축 밖 소자를 JSON으로.
사용: python -B b2_nodes.py <root> <theta json> <out json>
"""
import json
import os
import sys

root, theta, out = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3]
sys.path.insert(0, os.path.join(root, "workspaces"))
os.chdir(os.path.join(root, "workspaces"))
import run_harness as rh  # noqa: E402
import sizing_recipe as sr  # noqa: E402

CIRCUIT = os.environ.get("P4_CIRCUIT", "folded_cascode")
cfg = rh.SPECS[CIRCUIT]
topo = os.path.join(rh.LIBRARY_DIR, cfg["topology_file"])
spec = cfg["spec_fn"]()
ev = sr._build_theta_evaluator(topo, spec)
ctx, _m = ev["evaluate"](theta)
by_name = ev["by_name"]
rep = sr.propagate_node_voltages(by_name, ctx.sized, spec["vdd"])
vs_grid = list(spec["lut_by_kind"]["nmos"].VS_grid) if hasattr(spec["lut_by_kind"]["nmos"], "VS_grid") else None
devs = {}
for n, tr in sorted(by_name.items()):
    e = ctx.sized.get(n) or {}
    vsb = e.get("vsb")
    devs[n] = {"kind": tr.kind, "source": tr.source, "drain": tr.drain, "gate": tr.gate,
               "V_source": rep.nodes.get(tr.source), "vsb": vsb, "vds": e.get("vds"),
               "axis_out": (vsb is not None and vs_grid is not None and (vsb < vs_grid[0] - 1e-12 or vsb > vs_grid[-1] + 1e-12))}
res = {"circuit": CIRCUIT, "theta": theta, "vs_grid": vs_grid, "conflicts": [list(map(lambda x: x if not isinstance(x, float) else round(x, 6), c)) for c in rep.conflicts],
       "unresolved": rep.unresolved, "nodes": {k: round(v, 6) for k, v in sorted(rep.nodes.items())}, "devices": devs,
       "axis_out_devices": sorted(n for n, d in devs.items() if d["axis_out"])}
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("conflicts", len(rep.conflicts), "unresolved", rep.unresolved, "axis_out", res["axis_out_devices"])
for c in rep.conflicts:
    print("  conflict", c)
