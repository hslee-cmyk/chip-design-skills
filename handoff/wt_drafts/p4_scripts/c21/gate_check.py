"""#21 시제품 게이트·유도 함수 직접 점검(값은 파일로).
사용: python -B -P gate_check.py <root> <out.json>
기록: (1) SPECS 4회로 canonical_spec -> reject_legacy_names(harness_spec) 통과/거부, rail_voltages(spec, meta["rails"]) 값
      (2) 합성 거부 입력: spec에 스칼라 vdd / supplies 키, topology metric 선언에 supply_nets, supplies_v 레일 누락
      (3) library 9회로 load_topology meta 키 목록과 meta["rails"]"""
import copy, glob, importlib.util, json, os, sys, traceback
root, out = os.path.abspath(sys.argv[1]), sys.argv[2]
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
sys.path.insert(0, A)
import stick_diagram as sd
import sizing_recipe as sr
res = {"root": root, "has": {n: hasattr(m, n) for m, n in ((sd, "reject_legacy_names"), (sr, "rail_voltages"), (sd, "rail_declaration"))}}
def tryit(fn):
    try:
        return {"ok": True, "value": fn()}
    except Exception as e:
        return {"ok": False, "exc": type(e).__name__, "msg": str(e)[:300]}
spec_ = importlib.util.spec_from_file_location("run_harness_c21", os.path.join(root, "workspaces", "run_harness.py"))
H = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(H)
res["specs"] = {}
for k, cfg in H.SPECS.items():
    topo = os.path.join(A, "library", cfg["topology_file"])
    ent = {"canonical_spec": tryit(lambda: sorted(kk for kk in H.canonical_spec(k) if kk in ("vdd", "supplies_v", "supplies")))}
    if ent["canonical_spec"]["ok"]:
        s = H.canonical_spec(k)
        ent["supplies_v"] = s.get("supplies_v"); ent["vdd"] = s.get("vdd")
        if res["has"]["rail_voltages"]:
            def rv():
                v = sr.rail_voltages(s, sd.load_topology(topo)[1]["rails"])
                return {"by_net": v.by_net, "hi": v.hi, "lo": v.lo, "span": v.span, "hi_plus_lo": v.hi + v.lo}
            ent["rail_voltages"] = tryit(rv)
            bad = copy.copy(s); bad["supplies_v"] = {kk: vv for kk, vv in s["supplies_v"].items() if kk != "vdd"}
            ent["reject_missing_rail"] = tryit(lambda: sr.rail_voltages(bad, sd.load_topology(topo)[1]["rails"]) and "NOT REJECTED")
        if res["has"]["reject_legacy_names"]:
            ent["reject_scalar_vdd"] = tryit(lambda: sd.reject_legacy_names({**s, "vdd": 1.8}, "harness_spec") or "NOT REJECTED")
            ent["reject_supplies"] = tryit(lambda: sd.reject_legacy_names({**s, "supplies": {"vdd": 1.8}}, "harness_spec") or "NOT REJECTED")
            ent["accept_canonical"] = tryit(lambda: sd.reject_legacy_names(s, "harness_spec") or "accepted")
    res["specs"][k] = ent
if res["has"]["reject_legacy_names"]:
    synth = {"supply_nets": ["vdd", "gnd"], "sizing_roles": {"metrics": {"i_sup": {"type": "supply_current", "supply_nets": ["vdd"]}}}}
    res["reject_metric_supply_nets"] = tryit(lambda: sd.reject_legacy_names(synth, "topology") or "NOT REJECTED")
    synth_ok = {"supply_nets": ["vdd", "gnd"], "sizing_roles": {"metrics": {"i_sup": {"type": "supply_current"}, "g": {"excite": {"vdd": 0.0}}}}}
    res["accept_top_supply_nets_and_excite_vdd"] = tryit(lambda: sd.reject_legacy_names(synth_ok, "topology") or "accepted")
res["library"] = {}
for p in sorted(glob.glob(os.path.join(A, "library", "*.topology.json"))):
    n = os.path.basename(p)[:-len(".topology.json")]
    if n.startswith("_"):
        continue
    def lm():
        _, m = sd.load_topology(p)
        r = m.get("rails")
        return {"meta_keys": sorted(m), "rails": None if r is None else {"type": type(r).__name__, "fields": sorted(getattr(r, "__dataclass_fields__", {})), "nets": sorted(r.nets)}}
    res["library"][n] = tryit(lm)
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=repr)
print("wrote", out)
