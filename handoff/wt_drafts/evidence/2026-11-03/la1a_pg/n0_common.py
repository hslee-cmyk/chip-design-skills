# 개정판 공용: 원시 값(bundle) 포착, 시제품 출발 θ 적재, D1 이득 입력. 측정 도구(엔진 무변경). 엔진 = integ-it12(시제품 base).
import os, sys, ast
os.environ.setdefault("PG_ENGINE_ROOT", "C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12/skills/analog-gmid-design")
from pg_common import *
ivc = sys.modules["gmid_engine.search.iv_context"]
km = sys.modules["gmid_engine.search.kernel"]
ff = sys.modules["gmid_engine.search.find_front"]
from gmid_engine.metrics import ACH_KEY, ParamTables, block_spec
from gmid_engine.search.start_values import GainInputs
from gmid_engine.search.kernel import evaluate
from gmid_engine.search import find_front, SearchSettings

CAP = {}
RAW_OF = {}   # 평가 키 -> 원시 값 (측정 도구 안, 엔진 밖)
_orig_ss = km.ss_constraint_rows


def _wrap(bundle, declared, model_error=()):
    CAP["b"] = bundle
    return _orig_ss(bundle, declared, model_error)


km.ss_constraint_rows = _wrap


def raw_now():
    b = CAP.get("b")
    return {} if b is None else {str(k.metric): v.value for k, v in b.entries}


def gain_inputs_d1(p, views, lut, constraints):
    if not any(m == "gain_ss_db" and op == ">=" for m, op, _v in constraints):
        return None, (("gain_l", "constraint_not_declared"),)
    gain = dict(p.column("graph", "gain_checks")).get(ACH_KEY)
    view = next((v for v in views if v.kind == "transfer"), None)
    found = [b.found_db for b in gain.blocks] if gain is not None else []
    goal = max(float(v) for m, op, v in constraints if m == "gain_ss_db" and op == ">=")
    if gain is None or view is None or not gain.blocks or len(view.blocks) != len(gain.blocks) or any(f is None for f in found):
        return None, (("gain_l", "found_db_missing"),)
    total = float(sum(found))
    local = p.value("graph", ACH_KEY, "local_inputs").view
    keep = [(block_spec(view, b, local), goal * f / total) for b, f in zip(view.blocks, found) if b.kind != "buffer"]
    return GainInputs(local, ParamTables(lut.memo, local.w_keys, local.grids), tuple(keep)), ()


def use_d1(run):
    if run.endswith("d1"):
        ivc._gain_inputs = gain_inputs_d1


def build_ctx(c, eval_budget=40, budget_s=200.0):
    """pg_common.build 와 같고 eval_budget 만 인자. None = 예산 해제(엔진이 유도)."""
    lut, pdk, rule = load_env()
    work = pathlib.Path(tempfile.mkdtemp(prefix="n_%s_" % c[:6], dir=str(TEMP_ROOT)))
    donors, counters = open_run()
    kw = {}
    if c == "ngcc_3stage_ff":
        topo = load_topology(str(LIB / (c + ".topology.json")))
        st = {"schema_version": "1", "topology_hash": topo.connectivity_fp, "rule_hash": structure_rule_fp(), "facts": [
            {"concept": "dc_role", "subject": m, "value": "signal", "status": "ratified",
             "evidence": {"rule": "TEMP O-216 content", "nets": ["V1", "gnd"]}, "approval_id": "TEMP-la1a-pg"} for m in ("M8", "M14")]}
        sp = work / (c + ".structure.json"); sp.write_text(json.dumps(st), encoding="utf-8")
        kw = {"structure_path": sp}
    a = run_stage_a(LIB / (c + ".topology.json"), LIB / (c + ".sizing_spec.json"), lut, output_dir=work / c, donors=donors, counters=counters, **kw)
    memo = LutMemo(lut, point=1 << 14, curve=1 << 12, root=1 << 14)
    settings = SearchSettings(budget_s, eval_budget, (1e2, 1e5), (("front_budget_s", "la1a pg rev"),), (1e-13, 1e-10))
    b = run_stage_b(a, memo, pdk, output_dir=work / c, diagnostic=True, settings=settings)
    kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
    s3 = work / c / "s3"; s3.mkdir(parents=True, exist_ok=True)
    return build_search_context(kctx, a.spec, settings, str(s3), pdk, rule, code_fp=a.code_fp)


def load_theta(c, run):
    fn = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/la1a_pg_a/proto/out") / ("v2start_%s_k1_v2m_spec_%s.json" % (c, run))
    return {ast.literal_eval(k): float(v) for k, v in json.loads(fn.read_text(encoding="utf-8"))["theta"].items()}


def targets(sctx):
    return {str(d.metric): (d.op, float(d.value)) for d in sctx.ss_constraints}


def judge(tg, raw):
    out = {}
    for m, v in raw.items():
        if m in tg and v is not None:
            op, t = tg[m]
            out[m] = [round(float(v), 5) if abs(float(v)) < 1e3 else float("%.4g" % v), t, bool(v >= t if op == ">=" else v <= t)]
    return out


def ev(sctx, th, cells, tag=("stage", "pgrev")):
    CAP.pop("b", None)
    r = evaluate(sctx, th, cells, origin=(tag,))
    # 캐시 적중이면 bundle 이 없으므로 키별로 기억해 둔 원시 값을 쓴다(측정 도구 안, 엔진 밖)
    now = raw_now() if r.status == "sealed" else {}
    if now:
        RAW_OF[r.key] = now
    return r, RAW_OF.get(r.key, {})
