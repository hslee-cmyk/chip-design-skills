"""판정자 합성 회로 + 독립 손 유도 대조(엔진 풀이를 기대값으로 쓰지 않는다). 결과 run3/out/probe_phys.jsonl 케이스마다 append."""
import json
import math
import pathlib
import sys

import numpy as np

skill = sys.argv[1]
sys.path.insert(0, skill)
from gmid_engine.metrics import Capacitor, MosSmallSignal, Resistor, SmallSignalCircuit, SsCircuit, block_local_gain, sensitivity_gate
from gmid_engine.metrics._helpers_nodal import capacitance_matrix, nodal_adjoint, nodal_factor, nodal_solve
from gmid_engine.metrics.aux_types import BlockStruct

out = pathlib.Path(sys.argv[2])
out.write_text("", encoding="utf-8")


def rec(name, **kw):
    kw["case"] = name
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(kw, ensure_ascii=False, default=repr) + "\n")
    print(name, kw)


def block(key, inputs, outputs, nodes, members=(), kind="gain"):
    return BlockStruct(tuple(key), kind, 1, tuple(inputs), tuple(outputs), tuple(nodes), (), tuple(sorted(members)))


def ss_of(nets, mos, res, caps, ground, inputs, missing=()):
    return SsCircuit(tuple(nets), SmallSignalCircuit(mos=tuple(mos), resistors=tuple(res), capacitors=tuple(caps)),
                     tuple(r.label for r in res), tuple(c.label for c in caps), tuple(sorted(ground)), tuple(sorted(inputs)), tuple(missing))


# ---- 1. 전하 섬 두 넷(n1-n2), 5 용량 전부. 손 KCL: 미지수 n1, n2, out
nets = ("gnd", "vdd", "in", "n1", "n2", "out")
i = {n: k for k, n in enumerate(nets)}
c1, cc, cp, c2, cgs, cgd, cgb, cdb, csb = 2e-12, 1.3e-12, 0.7e-12, 3e-12, 5e-13, 2e-13, 1e-13, 4e-13, 6e-13
gm, gds, rl = 1e-3, 2e-5, 3e4
m1 = MosSmallSignal(i["out"], i["n2"], i["gnd"], i["gnd"], gm, 0.0, gds, cgs=cgs, cgd=cgd, cgb=cgb, cdb=cdb, csb=csb, label="M1")
ss = ss_of(nets, [m1], [Resistor(i["vdd"], i["out"], rl, label="RL")],
           [Capacitor(i["in"], i["n1"], c1, label="C1"), Capacitor(i["n1"], i["n2"], cc, label="Cc"), Capacitor(i["n1"], i["gnd"], cp, label="Cp"), Capacitor(i["n2"], i["gnd"], c2, label="C2")],
           ("gnd", "vdd"), ("in",))
got = block_local_gain(ss, block(("out",), ("in",), ("out",), ("in", "out"), ("M1", "RL")))
# 손: n1 행 (c1+cc+cp)n1 - cc n2 = c1; n2 행 -cc n1 + (cc+c2+cgs+cgd+cgb) n2 - cgd out = 0; out 행 gm n2 + (gds+1/rl) out = 0
A = np.array([[c1 + cc + cp, -cc, 0.0], [-cc, cc + c2 + cgs + cgd + cgb, -cgd], [0.0, gm, gds + 1 / rl]])
x = np.linalg.solve(A, np.array([c1, 0.0, 0.0]))
rec("1_charge_island_two_nets", engine_gain=got.gain, hand_gain=float(x[2]), rel=abs(got.gain / x[2] - 1), engine_n1=dict(got.node_v).get("n1"), hand_n1=float(x[0]),
    engine_n2=dict(got.node_v).get("n2"), hand_n2=float(x[1]), members=got.members, undefined=[u.code for u in got.undefined])

# ---- 2. 막다른 저항 넷이 전하 넷의 용량 쪽 끝: out -Rz- mz -Cc- n -C2- gnd, M2(g n). 저항 전류 0 -> V(mz) = V(out). 전회로·블록 모두.
nets = ("gnd", "vdd", "in", "out", "mz", "n", "o2")
i = {n: k for k, n in enumerate(nets)}
gm1, gds1, r1, gm2, gds2, r2, ccz, c2z, rz = 1e-3, 2e-5, 3e4, 2e-3, 3e-5, 2e4, 1e-12, 3e-12, 1e3
mos = [MosSmallSignal(i["out"], i["in"], i["gnd"], i["gnd"], gm1, 0.0, gds1, label="M1"),
       MosSmallSignal(i["o2"], i["n"], i["gnd"], i["gnd"], gm2, 0.0, gds2, label="M2")]
res = [Resistor(i["vdd"], i["out"], r1, label="R1"), Resistor(i["vdd"], i["o2"], r2, label="R2"), Resistor(i["out"], i["mz"], rz, label="Rz")]
caps = [Capacitor(i["mz"], i["n"], ccz, label="Cc"), Capacitor(i["n"], i["gnd"], c2z, label="C2")]
ss = ss_of(nets, mos, res, caps, ("gnd", "vdd"), ("in",))
got = block_local_gain(ss, block(("o2",), ("in",), ("o2",), ("in", "out", "mz", "n", "o2"), ("M1", "M2", "R1", "R2", "Rz", "Cc", "C2")))
vout = -gm1 / (gds1 + 1 / r1)
vn = ccz / (ccz + c2z) * vout
vo2 = -gm2 / (gds2 + 1 / r2) * vn
rec("2_dead_end_read_by_capacitor", engine_gain=got.gain, hand_gain=vo2, engine_node_v=got.node_v, members=got.members, undefined=[u.code for u in got.undefined],
    hand_vn=vn, verdict="엔진 == 손?" + str(got.gain is not None and abs(got.gain / vo2 - 1) < 1e-9))
# 같은 회로 전회로 factor(비교: 전회로는 mz 를 안 뺀다)
from gmid_engine.metrics.ss_nodal import nodal_of
nod = nodal_of(ss)
v, _r = nodal_solve(nod.factor, len(nets), {i["in"]: 1.0})
rec("2b_same_circuit_full_nodal", v_o2=None if v is None else float(v[i["o2"]]), hand=vo2, charge=[nets[k] for k in nod.factor[5]])

# ---- 3. 출력 넷에 스탬프 소자가 없음(exclude 로 빠짐), C 도 없음: 0 V 조용한 처리가 남았는가
nets = ("gnd", "vdd", "in", "x", "out")
i = {n: k for k, n in enumerate(nets)}
mos = [MosSmallSignal(i["x"], i["in"], i["gnd"], i["gnd"], 1e-3, 0.0, 2e-5, label="M1"), MosSmallSignal(i["out"], i["x"], i["gnd"], i["gnd"], 1e-3, 0.0, 2e-5, label="Mf")]
res = [Resistor(i["vdd"], i["x"], 1e4, label="R1")]
ss = ss_of(nets, mos, res, [], ("gnd", "vdd"), ("in",))
got = block_local_gain(ss, block(("out",), ("in",), ("out",), ("in", "x", "out"), ("M1", "R1")), exclude=("Mf",))
rec("3_output_only_on_excluded_device", gain=got.gain, zout=got.zout_ohm, undefined=[u.code for u in got.undefined], node_v=got.node_v)

# ---- 4. 출력 넷 자체가 전하 넷(용량 분압 출력): zout 정의 불가
nets = ("gnd", "vdd", "in", "x", "out")
i = {n: k for k, n in enumerate(nets)}
mos = [MosSmallSignal(i["x"], i["in"], i["gnd"], i["gnd"], 1e-3, 0.0, 2e-5, label="M1")]
res = [Resistor(i["vdd"], i["x"], 1e4, label="R1")]
caps = [Capacitor(i["x"], i["out"], 1e-12, label="C1"), Capacitor(i["out"], i["gnd"], 3e-12, label="C2")]
ss = ss_of(nets, mos, res, caps, ("gnd", "vdd"), ("in",))
got = block_local_gain(ss, block(("out",), ("in",), ("out",), ("in", "x", "out"), ("M1", "R1", "C1", "C2")))
rp = 1 / (2e-5 + 1e-4)
rec("4_output_is_charge_net", gain=got.gain, hand_gain=-1e-3 * rp * 0.25, zout=got.zout_ohm, zout_isnan=(got.zout_ohm is not None and math.isnan(got.zout_ohm)), undefined=[u.code for u in got.undefined])

# ---- 5. 감도 게이트 NaN·inf 입력(칸이 None 이 아니고 NaN): ok 로 새는가
g = sensitivity_gate((40.0, 40.0, 1e-12), (("a", float("nan"), 41.0, 1e-12),))
rec("5a_gate_nan_dec", ok=g.ok, verdict=g.verdict, reason=g.reason, checks=g.checks)
g = sensitivity_gate((40.0, 40.0, 1e-12), (("a", 40.0, float("nan"), 1e-12),))
rec("5b_gate_nan_full", ok=g.ok, verdict=g.verdict, reason=g.reason, checks=g.checks)
g = sensitivity_gate((float("nan"), 40.0, 1e-12), (("a", 40.0, 41.0, 1e-12),))
rec("5c_gate_nan_base", ok=g.ok, verdict=g.verdict, reason=g.reason, checks=g.checks)
g = sensitivity_gate((float("-inf"), 40.0, 1e-12), (("a", float("-inf"), 41.0, 1e-12),))
rec("5d_gate_minf_both", ok=g.ok, verdict=g.verdict, reason=g.reason, checks=g.checks)

# ---- 6. 전회로 gate 전용 넷 C 없음: 옛 floating 0 V -> lu None
nets = ("gnd", "vdd", "in", "n", "out")
i = {n: k for k, n in enumerate(nets)}
mos = [MosSmallSignal(i["out"], i["n"], i["gnd"], i["gnd"], 1e-3, 0.0, 2e-5, label="M1")]
res = [Resistor(i["vdd"], i["out"], 1e4, label="R1")]
ss = ss_of(nets, mos, res, [], ("gnd", "vdd"), ("in",))
nod = nodal_of(ss)
rec("6_full_gate_only_no_c", lu_none=nod.factor[1] is None, floating=nod.factor[4], charge=nod.factor[5], unknown=list(map(int, nod.factor[0])), solve=str(nodal_solve(nod.factor, 5, {i["in"]: 1.0})))

# ---- 7. offset_analysis: MOS d·s 가 전하 넷(값 전부 0 인 off 소자): 수반 NaN 이 sigma 로 새는가
from gmid_engine.authoring import ExciteSense, ViewDecl
from gmid_engine.metrics import offset_analysis
nets = ("gnd", "vdd", "in", "n", "out")
i = {n: k for k, n in enumerate(nets)}
mos = [MosSmallSignal(i["out"], i["in"], i["gnd"], i["gnd"], 1e-3, 0.0, 2e-5, label="M1"),
       MosSmallSignal(i["n"], i["out"], i["gnd"], i["gnd"], 0.0, 0.0, 0.0, cdb=1e-15, label="Moff")]
res = [Resistor(i["vdd"], i["out"], 1e4, label="R1")]
ss = ss_of(nets, mos, res, [], ("gnd", "vdd"), ("in",))
view = ViewDecl("transfer", transfer=ExciteSense((("in", 1.0),), "out", None, "single"))
try:
    an = offset_analysis(ss, view, (("M1", 1e-3, "t"), ("Moff", 1e-3, "t")), ("M1",))
    rec("7_offset_nan_leak", sigma=an.sigma_in_mv if hasattr(an, "sigma_in_mv") else repr(an)[:300], full=repr(an)[:400])
except Exception as exc:
    rec("7_offset_nan_leak", exc=repr(exc)[:400])
