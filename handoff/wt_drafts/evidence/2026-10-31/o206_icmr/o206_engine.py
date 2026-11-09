# O-206 실측 (엔진 쪽) -- library 회로 하나의 layer0 출발 봉인점(master 엔진, library 경로 그대로)을 잡고, 측정 구성 T(출력 = 봉인 V_out 고정,
# 비반전 입력 = x 이동, 반전 입력 = servo)에서 입력 공통모드 Δx 를 훑으며 세 가지 엔진 쪽 추정을 낸다.
#  (a) O-206 엔진 안: 봉인점 graph.ss_nodal 과 같은 컨덕턴스 계(_ss_of -> conductance_matrix -> nodal_factor)로 KCL 1차 감도 s 를 한 번 풀고,
#      V(Δx) = V0 + s·Δx 로 예측한 소자 바이어스에서 LUT 순방향 조회(op_point, gmb) -> gm·gds·gmb 를 바꾼 같은 ss 회로의 DC 노달 풀이 1회 -> 차동 이득.
#  (c) 대안: 점마다 W·바이어스 고정 비선형 KCL(LUT 전류) Newton -- 수렴한 바이어스에서 (a)와 같은 이득 풀이. 반복 수·LUT 조회 수 기록.
# 엔진 소스 수정 0(공개·내부 함수 import·호출만), 저장소 쓰기 0(단계 A/B output_dir = TEMP 고유 경로). 결과는 케이스마다 Python 바이너리 append.
import os, sys, json, time, math, pathlib, tempfile, traceback, dataclasses
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG))
HERE = pathlib.Path(__file__).parent
TMP = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/o206_7c3e91")
import importlib
import numpy as np
R = importlib.import_module("gmid_engine.tests.search.u13_real")
from gmid_engine.search import SearchSettings, open_run
from gmid_engine.search.layer0_center import layer0_start
from gmid_engine.search.kernel import evaluate
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.metrics.metrics_aux import _ss_of
from gmid_engine.metrics.ss_circuit import ss_circuit
from gmid_engine.metrics._helpers_nodal import conductance_matrix, nodal_factor, nodal_solve
from gmid_engine.lut import op_point, gmb
from gmid_engine.lut.vdsat_query import vdsat
from gmid_engine.sizing._helpers_lut import terminal_voltages
from gmid_engine.core import SealViolationError

F_DUMP = HERE / "o206_seal_dump.jsonl"; F_SWEEP = HERE / "o206_engine_sweep.jsonl"


def app(path, rec):
    with open(path, "ab") as fh:
        fh.write((json.dumps(rec, default=float, ensure_ascii=False) + "\n").encode("utf-8"))


def js(v, d=0):
    if d > 5:
        return repr(v)[:200]
    if v is None or isinstance(v, (str, bool, int)):
        return v
    if isinstance(v, (float, np.floating)):
        return float(v)
    if isinstance(v, dict):
        return {str(k): js(x, d + 1) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [js(x, d + 1) for x in v]
    if dataclasses.is_dataclass(v):
        return {f.name: js(getattr(v, f.name), d + 1) for f in dataclasses.fields(v)}
    if hasattr(v, "_asdict"):
        return {k: js(x, d + 1) for k, x in v._asdict().items()}
    return repr(v)[:300]


def col(snap, kind, fld):
    try:
        return dict(snap.column(kind, fld))
    except Exception as e:  # noqa: BLE001 -- 측정: 없는 열은 기록만
        return {"__err__": repr(e)[:200]}


class Probe:
    """봉인점 회로 사실 + LUT 조회 계수."""

    def __init__(self, sctx, snap):
        self.memo = sctx.dc.lut.memo
        self.snap = snap
        self.ops = dict(snap.column("device", "dc_op"))
        self.pins = {m: dict(p) for m, p in snap.column("device", "pins")}
        self.bulk = {m: b.net for m, b in snap.column("device", "bulk")}
        self.ssv = dict(snap.column("device", "ss_dev"))
        self.dcv = {n: v for n, v in snap.column("node", "dc_v") if v is not None}
        self.rails = {n: v for n, v in snap.column("node", "dc_rail_v") if v is not None}
        self.ss, _sv, _orb = _ss_of(snap)
        self.index = {n: i for i, n in enumerate(self.ss.nodes)}
        self.size = len(self.ss.nodes)
        self.fixed = {self.index[n] for n in tuple(self.ss.ground_nets) + tuple(self.ss.input_nets)}
        self.lut_calls = 0
        self.passive = dict(snap.column("device", "passive_value"))
        self.classes = dict(snap.column("device", "element_class"))
        self.kinds = dict(snap.column("device", "kind"))

    def values0(self):
        v = dict(self.rails); v.update(self.dcv)
        return v

    def device_point(self, m, V):
        op = self.ops[m]
        p = self.pins[m]
        return terminal_voltages(op.kind, V[p["d"]], V[p["g"]], V[p["s"]], V[self.bulk[m]])

    def lut_dev(self, m, vgs, vds, vsb):
        op = self.ops[m]
        sl = self.memo.lut.slice_map[(op.kind, op.w_key)]
        self.lut_calls += 2
        pt = op_point(self.memo, op.kind, op.w_key, op.L, vgs, vds, vsb)
        gb = gmb(self.memo, op.kind, op.w_key, op.L, vgs, vds, vsb)
        idd = pt.IDu * op.W / op.L
        gm_id = pt.gm_over_id
        gdsw = pt.gds_per_w
        return dict(ID=idd, gm=gm_id * idd, gds=gdsw * op.W, gmb=gb * op.W / sl.w_m, gm_id=gm_id)

    def circuit_with(self, repl):
        devs = []
        for name in self.classes:
            ss = self.ssv.get(name)
            if name in repl and ss is not None:
                r = repl[name]
                ss = dataclasses.replace(ss, gm=r["gm"], gds=r["gds"], gmb=r["gmb"])
            devs.append((name, self.classes[name], self.kinds[name], tuple(sorted(self.pins[name].items())) if name in self.pins else
                         dict(self.snap.column("device", "pins"))[name], self.bulk.get(name), ss))
        return ss_circuit(self.ss.nodes, self.ss.ground_nets, self.ss.input_nets, devs, self.snap.column("device", "passive_value"))

    def factor(self, circ):
        g = conductance_matrix(circ.circuit, self.size)
        return nodal_factor(g, self.fixed), g


def diff_gain(pr, fac, inp, inn, out):
    v, rel = nodal_solve(fac, pr.size, {pr.index[inp]: 0.5, pr.index[inn]: -0.5})
    return None if v is None else float(v[pr.index[out]]), rel


def run(name, dmax, step):
    t0 = time.time()
    env = R.real_env()
    out_dir = pathlib.Path(tempfile.mkdtemp(prefix="o206_" + name[:10] + "_", dir=str(TMP)))
    donors, counters = open_run()
    a = run_stage_a(R.LIBRARY / (name + ".topology.json"), R.LIBRARY / (name + ".sizing_spec.json"), env.lut, output_dir=out_dir,
                    donors=donors, counters=counters)
    if a.status != "ok":
        app(F_DUMP, dict(circuit=name, stageA=a.status, stop=js(a.report.get("stop_reasons")) if hasattr(a, "report") and isinstance(a.report, dict) else None))
        return
    settings = SearchSettings(600.0, R.EVAL_BUDGET, R.RBOX, (("front_budget_s", "u13 test fixture"),), R.CBOX)
    b = run_stage_b(a, env.memo, env.pdk, output_dir=out_dir, settings=settings)
    if b.status != "ok":
        app(F_DUMP, dict(circuit=name, stageB=b.status)); return
    topo = json.loads((R.LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))
    recipe = R._recipe(a, b, topo, settings)
    case = R._contexts(recipe, dict(donors=a.donors, counters=a.counters))
    sctx = case.sctx
    l0 = layer0_start(sctx)
    if l0.start is None:
        app(F_DUMP, dict(circuit=name, layer0=repr(l0)[:800])); return
    res = evaluate(sctx, dict(l0.start.theta), l0.start.cells)
    snap = res.evaluation.snapshot
    bundle = None
    from gmid_engine.sizing import METRICS_KEY
    metrics = {}
    try:
        mk = METRICS_KEY or "metrics"
        bundle = snap.value("graph", mk, "metrics_ss")
        metrics = js(bundle)
    except Exception as e:  # noqa: BLE001
        metrics = {"__err__": repr(e)[:300]}
    pr = Probe(sctx, snap)
    ports = topo["ports"]
    ins = [n for n, p in ports.items() if not n.startswith("_") and p.get("direction") == "input"]
    outs = [n for n, p in ports.items() if not n.startswith("_") and p.get("direction") == "output"]
    pol = {n: ports[n].get("polarity") for n in ins + outs}
    # 반전 입력 판정: 봉인점 노달 계 전달 부호(구조 사실, 엔진 계)
    fac0, g0 = pr.factor(pr.circuit_with({}))
    out = outs[0]
    T = {}
    for p in ins:
        v, _ = nodal_solve(fac0, pr.size, {pr.index[p]: 1.0})
        T[p] = float(v[pr.index[out]])
    inn = min(ins, key=lambda p: T[p]); inp = max(ins, key=lambda p: T[p])
    V0 = pr.values0()
    dev_rec = {}
    jg = sctx.junction
    for m, op in pr.ops.items():
        sl = pr.memo.lut.slice_map[(op.kind, op.w_key)]
        geo = jg.pre_layout_geometry(sl.w_m, op.W / sl.w_m)
        dev_rec[m] = dict(kind=op.kind, w_key=op.w_key, L=op.L, W=op.W, w_m=sl.w_m, pins=pr.pins[m], bulk=pr.bulk[m], vgs=op.vgs, vds=op.vds,
                          vsb=op.vsb, ID=getattr(op, "current", None), gm_id=getattr(op, "gm_id", None), ss=js(pr.ssv.get(m)), geometry=js(geo),
                          op=js(op))
    passives = {n: dict(kind=pr.kinds[n], pins=dict(dict(snap.column("device", "pins"))[n]), value=pr.passive.get(n))
                for n in pr.classes if pr.classes[n] != "mos"}
    g_nom, rel0 = diff_gain(pr, fac0, inp, inn, out)
    # KCL 1차 감도 -- 측정 구성 T 두 꼴: hold = 이상 servo(Δout = 0), tb = oracle 테스트벤치 되먹임 그대로(V(inn) = V(out) − V_out0 + V(inp), 1차)
    vx, _ = nodal_solve(fac0, pr.size, {pr.index[inp]: 1.0})
    vu, _ = nodal_solve(fac0, pr.size, {pr.index[inn]: 1.0})
    Tp, Tn = vx[pr.index[out]], vu[pr.index[out]]
    u = -Tp / Tn
    s = {n: float(vx[i] + u * vu[i]) for n, i in pr.index.items()}
    dout = (Tp + Tn) / (1.0 - Tn)
    u_tb = 1.0 + dout
    s_tb = {n: float(vx[i] + u_tb * vu[i]) for n, i in pr.index.items()}
    app(F_DUMP, dict(circuit=name, theta=js(l0.start.theta), layer0_source=getattr(l0, "source", None), status=res.status, nodes=V0, rails=pr.rails,
                     devices=dev_rec, passives=passives, ss_nodes=list(pr.ss.nodes), ss_ground=list(pr.ss.ground_nets), ss_inputs=list(pr.ss.input_nets),
                     inp=inp, inn=inn, out=out, T=T, polarity=pol, metrics=metrics, gain_nodal_nominal=g_nom,
                     gain_db_nominal=None if g_nom is None else 20 * math.log10(abs(g_nom)), s_T=s, u_T=float(u), s_tb=s_tb, u_tb=float(u_tb),
                     spec_constraints=js([(c.metric, c.op, c.value) for c in sctx.spec.judged_constraints]),
                     seconds=round(time.time() - t0, 1)))
    mos = [m for m in pr.classes if pr.classes[m] == "mos"]
    free = [i for i in range(pr.size) if i not in pr.fixed]
    # ---- 훑기
    for direction in (+1, -1):
        Vc = None    # (c) Newton 연속 출발점
        k = 0
        while True:
            dx = direction * k * step
            if abs(dx) > dmax + 1e-12:
                break
            rec = dict(circuit=name, dx=dx, x=V0[inp] + dx)
            # (a) 1차 예측 (두 측정 구성 꼴)
            for tag, sens in (("a_tb", s_tb), ("a_hold", s)):
                Va = {n: V0[n] + sens.get(n, 0.0) * dx for n in V0}
                c0 = pr.lut_calls
                repl, region, bad = {}, {}, None
                for m in mos:
                    vgs, vds, vsb = pr.device_point(m, Va)
                    try:
                        r = pr.lut_dev(m, vgs, vds, vsb)
                        op = pr.ops[m]
                        sat = vdsat(pr.memo, op.kind, op.w_key, op.L, vgs, vds, vsb)
                        pr.lut_calls += 1
                        repl[m] = r
                        region[m] = dict(vgs=vgs, vds=vds, vsb=vsb, ID=r["ID"], gm=r["gm"], slack=vds - sat)
                    except (SealViolationError, Exception) as e:  # noqa: BLE001 -- LUT 정의역 밖 = E-0 정의 불능 기록
                        bad = (m, vgs, vds, vsb, repr(e)[:160]); break
                if bad is None:
                    fa, _ = pr.factor(pr.circuit_with(repl))
                    ga, _r = diff_gain(pr, fa, inp, inn, out)
                    rec[tag] = dict(gain=ga, gain_db=None if ga is None else 20 * math.log10(abs(ga)), lut_calls=pr.lut_calls - c0, lin_solves=1,
                                    Vinn=Va[inn], Vout=Va[out], dev=region)
                else:
                    rec[tag] = dict(lut_out=bad, lut_calls=pr.lut_calls - c0)
                if tag == "a_tb":
                    bad_tb, Va_tb = bad, Va
            # (c) W·바이어스 고정 비선형 KCL Newton (미지수 = 고정 아닌 노드 중 out 제외 + inn, 식 = 고정 아닌 노드 KCL)
            c1 = pr.lut_calls
            V = dict(Va_tb) if Vc is None else {n: Vc[n] for n in Vc}
            V[inp] = V0[inp] + dx
            V[inn] = V[out] - V0[out] + V[inp]
            unk_nodes = [pr.ss.nodes[i] for i in free]
            eq_nodes = [pr.ss.nodes[i] for i in free]
            it, conv, err = 0, False, None
            try:
                for it in range(1, 61):
                    I = {n: 0.0 for n in pr.ss.nodes}
                    repl = {}
                    for m in mos:
                        p = pr.pins[m]; op = pr.ops[m]
                        vgs, vds, vsb = pr.device_point(m, V)
                        r = pr.lut_dev(m, vgs, vds, vsb)
                        repl[m] = r
                        sgn = 1.0 if op.kind == "nmos" else -1.0
                        I[p["d"]] -= sgn * r["ID"]; I[p["s"]] += sgn * r["ID"]     # 드레인에서 나가는 전류(nmos 드레인 유입 = 노드 유출)
                    for n_, pv in passives.items():
                        if pv["kind"] == "resistor" and pv["value"]:
                            a_, b_ = list(pv["pins"].values())
                            ii = (V[a_] - V[b_]) / pv["value"]
                            I[a_] -= ii; I[b_] += ii
                    F = np.array([I[n] for n in eq_nodes])
                    circ = pr.circuit_with(repl)
                    G = conductance_matrix(circ.circuit, pr.size)
                    J = np.zeros((len(eq_nodes), len(unk_nodes)))
                    for a_i, n in enumerate(eq_nodes):
                        for b_i, q in enumerate(unk_nodes):
                            J[a_i, b_i] = -G[pr.index[n], pr.index[q]]
                        J[a_i, unk_nodes.index(out)] += -G[pr.index[n], pr.index[inn]]     # V(inn) = V(out) − V_out0 + V(inp)
                    scale = max(1e-9, max(abs(r_["ID"]) for r_ in repl.values()))
                    if np.max(np.abs(F)) < 1e-9 * scale + 1e-15:
                        conv = True; break
                    dv = np.linalg.solve(J, -F)
                    lim = np.max(np.abs(dv))
                    if lim > 0.05:
                        dv *= 0.05 / lim
                    for b_i, q in enumerate(unk_nodes):
                        V[q] += float(dv[b_i])
                    V[inn] = V[out] - V0[out] + V[inp]
            except Exception as e:  # noqa: BLE001
                err = repr(e)[:200]
            cr = dict(conv=conv, iters=it, lut_calls=pr.lut_calls - c1, err=err)
            if conv:
                fc, _ = pr.factor(pr.circuit_with(repl))
                gc, _r = diff_gain(pr, fc, inp, inn, out)
                cr.update(gain=gc, gain_db=None if gc is None else 20 * math.log10(abs(gc)), Vinn=V[inn], Vout=V[out],
                          dev={m: dict(ID=repl[m]["ID"], gm=repl[m]["gm"], vds=pr.device_point(m, V)[1], vgs=pr.device_point(m, V)[0],
                                       slack=pr.device_point(m, V)[1] - vdsat(pr.memo, pr.ops[m].kind, pr.ops[m].w_key, pr.ops[m].L, *pr.device_point(m, V))) for m in mos})
                Vc = dict(V)
            rec["c"] = cr
            app(F_SWEEP, rec)
            if bad_tb is not None and not conv:
                break
            k += 1
    print(name, "done", round(time.time() - t0, 1), flush=True)


if __name__ == "__main__":
    nm = sys.argv[1]
    dmax = float(sys.argv[2]); step = float(sys.argv[3])
    try:
        run(nm, dmax, step)
    except BaseException:  # noqa: BLE001
        app(F_DUMP, dict(circuit=nm, error=traceback.format_exc()[-3000:]))
        raise
