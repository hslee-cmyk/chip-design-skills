"""IT-1 감사 S0 탐침: test_s0_layer_9circuits._chain 과 같은 사슬(단계 A -> B diagnostic -> 둘 다 ok 면 탐색 컨텍스트)과
test_current_basis._measured_domain 과 같은 search_domain 경로로, 회로마다 쓰기 계획·θ 스키마·search_domain ties/variables·
achievability dof·start 필드 값을 JSON 으로 남긴다(엔진 소스를 고치지 않는다, 관찰만).
usage: python -I probe_s0.py <repo_root> <out_json>
"""
import json
import sys
from pathlib import Path

repo = Path(sys.argv[1])
skill = repo / "skills" / "analog-gmid-design"
sys.path.insert(0, str(skill))
sys.path.append("C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_it1 import J  # noqa: E402  (같은 직렬화 함수)

import os  # noqa: E402
import tempfile  # noqa: E402
from types import SimpleNamespace  # noqa: E402

from gmid_engine.core import BoundedLRU, read_pdk_decl  # noqa: E402
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location  # noqa: E402
from gmid_engine.pipeline import run_stage_a, run_stage_b  # noqa: E402
from gmid_engine.search import SearchSettings, build_search_context, open_run, search_domain, S0_WRITERS  # noqa: E402
from gmid_engine.sizing import KERNEL_KEY, DC_KEY, build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access  # noqa: E402
from gmid_engine.authoring import THETA_BOUNDS, UNTIE_ORBITS  # noqa: E402

LIB = ["common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
       "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf"]
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))

loc = resolve_lut_location(str(skill / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(DEVICE_KINDS)
mins = {}
for e in man["slices"]:
    mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
dm = BoundedLRU(16)
pdk = read_pdk_decl(str(skill / "assets" / "sky130_pdk_decl.json"), dm)
q = dict(pdk.quantities)
spec_l = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                 noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec_l, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
rule = read_pdk_decl(str(skill / "assets" / "sky130_lut_rule_decl.json"), dm)
settings = SearchSettings(7200.0, 40, (1e2, 1e5), (("front_budget_s", "u13"),), (1e-13, 1e-10))
lib = skill / "assets" / "library"
res = {}
tmp = Path(tempfile.mkdtemp(prefix="it1probe_"))
for c in LIB:
    row = {}
    try:
        donors, counters = open_run()
        a = run_stage_a(lib / (c + ".topology.json"), lib / (c + ".sizing_spec.json"), lut, output_dir=tmp / c,
                        donors=donors, counters=counters)
        memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
        b = run_stage_b(a, memo, pdk, output_dir=tmp / c, diagnostic=True, settings=settings)
        row["status"] = [a.status, b.status]
        rb = json.loads(Path(b.report_paths[0]).read_text(encoding="utf-8"))
        row["ach_dof"] = (rb.get("achievability") or {}).get("dof")
        k = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
        base = k.base
        row["writers"] = J(dict(base.column("node", "dc_writer")))
        row["coords"] = J(dict(base.column("device", "dc_coord")))
        row["tie_breaks"] = J(base.value("graph", DC_KEY, "dc_tie_breaks"))
        search = a.spec.search if isinstance(a.spec.search, tuple) else ()
        sb = next((s.value for s in search if s.field == THETA_BOUNDS and s.value), ())
        un = tuple(n for n, _s in next((s.value for s in search if s.field == UNTIE_ORBITS and s.value), ()))
        bud = [float(d.value) for d in a.spec.judged_constraints if d.metric == "area_search_m2" and d.op == "<=" and d.value is not None]
        snap = search_domain(k.base.widen(S0_WRITERS), k.lut, None, None, pdk, sb, min(bud) if bud else None, un,
                             donors=k.donors, counters=k.counters)
        dom = snap.value("graph", KERNEL_KEY, "search_domain")
        row["domain_ties"] = J(dom.ties)
        row["domain_variables"] = [J(v)[0] if isinstance(J(v), list) else J(v) for v in dom.variables]
        row["domain_variables_raw"] = J(dom.variables)
        if (a.status, b.status) == ("ok", "ok"):
            sctx = build_search_context(k, a.spec, settings, None, pdk, rule, code_fp=a.code_fp)
            sb0 = sctx.dc.base
            row["theta_schema"] = J(sb0.value("graph", KERNEL_KEY, "theta_schema"))
            for f in ("rungs", "uncovered"):
                fv = sb0.field("graph", "start", f)
                row["start_" + f] = None if fv is None else J(fv.value)
    except Exception as exc:  # 관찰 하네스: 실패를 그대로 기록
        row["error"] = repr(exc)[:2000]
        d = getattr(exc, "detail", None)
        if d is not None:
            row["error_detail"] = J(d)
    res[c] = row
    Path(sys.argv[2]).write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(c, row.get("status"), row.get("error", "")[:200], flush=True)
