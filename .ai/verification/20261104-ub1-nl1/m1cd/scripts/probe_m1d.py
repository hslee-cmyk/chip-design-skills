"""M-1c·M-1d 재판정: C 조립 호출 수(자리별), charge_seeded 치환 비트 동일, 고립 섬. 결과 jsonl append."""
import importlib
import json
import pathlib
import sys

import numpy as np

skill = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(skill))
sys.path.insert(0, str(skill / "gmid_engine" / "tests"))
out = pathlib.Path(sys.argv[2])
out.write_text("", encoding="utf-8")
from gmid_engine.authoring import ExciteSense, ViewDecl
from gmid_engine.metrics import Capacitor, MosSmallSignal, Resistor, SmallSignalCircuit, SsCircuit, block_local_gain
from gmid_engine.metrics._helpers_nodal import capacitance_matrix as real_c, charge_seeded, nodal_factor, nodal_solve
from gmid_engine.metrics.aux_types import BlockStruct, ViewStruct

m = lambda n: importlib.import_module("gmid_engine.metrics." + n)
SN, HV, BM, BR, OA, HN = m("ss_nodal"), m("_helpers_view"), m("block_model"), m("block_residual"), m("offset_analysis"), m("_helpers_nodal")


def rec(name, **kw):
    kw["case"] = name
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(kw, ensure_ascii=False, default=repr) + "\n")
    print(name, kw)


sites = {}


def counted(circuit, size):
    s = sys._getframe(1).f_code.co_name
    sites[s] = sites.get(s, 0) + 1
    return real_c(circuit, size)


for mod in (SN, HV, BM):
    mod.capacitance_matrix = counted


def blk(key, inputs, outputs, nodes, members):
    return BlockStruct(tuple(key), "gain", 1, tuple(inputs), tuple(outputs), tuple(nodes), (), tuple(sorted(members)))


GM, GDS, RL = 1e-3, 2e-5, 3e4

# 1. 전하 넷 0: 자리별 조립 0, view_factor 다른 고정 집합 포함
nets = ("gnd", "vdd", "in", "x", "out")
i = {n: k for k, n in enumerate(nets)}
mos = (MosSmallSignal(i["out"], i["x"], i["gnd"], i["gnd"], GM, 0.0, GDS, cgs=1e-13, cgd=1e-13, label="M1"), MosSmallSignal(i["x"], i["in"], i["gnd"], i["gnd"], GM, 0.0, GDS, cgs=1e-13, label="M0"))
res = (Resistor(i["vdd"], i["out"], RL, label="RL"), Resistor(i["vdd"], i["x"], 1e4, label="Rx"))
ss = SsCircuit(nets, SmallSignalCircuit(mos=mos, resistors=res, capacitors=(Capacitor(i["out"], i["gnd"], 1e-12, label="CL"),)), ("RL", "Rx"), ("CL",), ("gnd", "vdd"), ("in",))
nod = SN.nodal_of(ss)
rec("1a_nodal_of_no_charge", sites=dict(sites)); sites.clear()
HV.view_factor(ss, nod, {i["gnd"], i["vdd"], i["in"]})
HV.view_factor(ss, nod, {i["gnd"], i["vdd"], i["x"]})
HV.view_factor(ss, None, {i["gnd"], i["vdd"], i["x"]})
rec("1b_view_factor_base_other_none_no_charge", sites=dict(sites)); sites.clear()
block_local_gain(ss, blk(("out",), ("in",), ("out",), ("in", "x", "out"), ("M0", "M1", "RL", "Rx")))
rec("1c_block_local_gain_no_charge", sites=dict(sites)); sites.clear()
view = ViewDecl("transfer", transfer=ExciteSense((("in", 1.0),), "out", None, "single"))
vs = ViewStruct("t", (("in", 1.0),), ("out",), (blk(("out",), ("in",), ("out",), ("in", "x", "out"), ("M0", "M1", "RL", "Rx")),), ())
BR.block_residual(ss, view, vs)
rec("1d_block_residual_no_charge", sites=dict(sites)); sites.clear()

# 2. 전하 넷 있음: 호출마다 횟수
nets = ("gnd", "vdd", "in", "n", "x", "out")
i = {n: k for k, n in enumerate(nets)}
mos = (MosSmallSignal(i["out"], i["n"], i["gnd"], i["gnd"], GM, 0.0, GDS, label="M1"), MosSmallSignal(i["x"], i["vdd"], i["gnd"], i["gnd"], 1e-4, 0.0, 1e-5, label="Mx"))
res = (Resistor(i["vdd"], i["out"], RL, label="RL"), Resistor(i["vdd"], i["x"], 1e4, label="Rx"))
caps = (Capacitor(i["in"], i["n"], 2e-12, label="C1"), Capacitor(i["n"], i["gnd"], 3e-12, label="C2"))
ss2 = SsCircuit(nets, SmallSignalCircuit(mos=mos, resistors=res, capacitors=caps), ("RL", "Rx"), ("C1", "C2"), ("gnd", "vdd"), ("in",))
b2 = blk(("out",), ("in",), ("out",), ("in", "out"), ("M1", "RL"))
got = block_local_gain(ss2, b2)
rec("2a_block_local_gain_charge", sites=dict(sites), gain=got.gain, hand=-GM / (GDS + 1 / RL) * 0.4); sites.clear()
nod2 = SN.nodal_of(ss2)
rec("2b_nodal_of_charge", sites=dict(sites), charge=[nets[k] for k in nod2.factor[5]]); sites.clear()
HV.view_factor(ss2, nod2, {i["gnd"], i["vdd"], i["in"]})
rec("2c_view_factor_base_hit_charge", sites=dict(sites)); sites.clear()
HV.view_factor(ss2, nod2, {i["gnd"], i["vdd"], i["in"], i["x"]})
rec("2d_view_factor_other_fixed_charge", sites=dict(sites)); sites.clear()
vs2 = ViewStruct("t", (("in", 1.0),), ("out",), (b2,), ())
BR.block_residual(ss2, view, vs2, nodal=nod2)
rec("2e_block_residual_with_field_charge", sites=dict(sites)); sites.clear()

# 3. 씨앗 판정 치환 비트 동일: nodal_factor(c=진짜 C) 대 엔진(charge_seeded 분기) -- 씨앗 없는 무작위 회로, 있는 회로, 뷰 고정 집합 다름
rng = np.random.default_rng(7)
stats = dict(n=0, seeded=0, same=0, seeded_false_but_row_zero=0)
for t in range(400):
    n = int(rng.integers(4, 9))
    mos = []
    for k in range(int(rng.integers(1, 6))):
        d, g, s, b = (int(x) for x in rng.integers(0, n, 4))
        mos.append(MosSmallSignal(d, g, s, b, *(float(x) for x in rng.random(3) * 1e-3), *(float(x) for x in (rng.random(5) - 0.3) * 1e-13), label="m%d" % k))
    res = [Resistor(int(a), int((a + 1 + rng.integers(0, n - 1)) % n), float(1e3 + rng.random() * 1e4), label="r%d" % k) for k, a in enumerate(rng.integers(0, n, int(rng.integers(0, 4))))]
    cap = [Capacitor(int(a), int((a + 1 + rng.integers(0, n - 1)) % n), float(1e-13 + rng.random() * 1e-12), label="c%d" % k) for k, a in enumerate(rng.integers(0, n, int(rng.integers(0, 4))))]
    ck = SmallSignalCircuit(mos=tuple(mos), resistors=tuple(res), capacitors=tuple(cap))
    names = tuple("n%d" % k for k in range(n))
    ss_t = SsCircuit(names, ck, tuple(r.label for r in res), tuple(c.label for c in cap), names[:2], names[2:3])
    nod = SN.nodal_of(ss_t)
    fixed = frozenset(int(x) for x in rng.choice(n, size=int(rng.integers(1, n)), replace=False))
    for fx, fac in ((nod.fixed, nod.factor), (fixed, HV.view_factor(ss_t, nod, fixed))):
        ref = nodal_factor(nod.g, fx, c=real_c(ck, n))
        same = all((a is None and b is None) or (not isinstance(a, np.ndarray) and a == b) or (isinstance(a, np.ndarray) and isinstance(b, np.ndarray) and a.tobytes() == b.tobytes()) for a, b in zip(fac, ref))
        stats["n"] += 1
        stats["same"] += bool(same)
        stats["seeded"] += bool(charge_seeded(nod.g, fx))
        free = [k for k in range(n) if k not in fx]
        stats["seeded_false_but_row_zero"] += (not charge_seeded(nod.g, fx)) and any(not nod.g[k].any() for k in free)
sites.clear()
rec("3_seed_substitution_bit_same", **stats)

# 4. 고립 섬(기준 없는 용량 전용 섬): 정의 불가
nets = ("gnd", "vdd", "in", "n1", "n2", "out")
i = {n: k for k, n in enumerate(nets)}
mos = (MosSmallSignal(i["out"], i["n1"], i["gnd"], i["gnd"], GM, 0.0, GDS, label="M1"),)
ss4 = SsCircuit(nets, SmallSignalCircuit(mos=mos, resistors=(Resistor(i["vdd"], i["out"], RL, label="RL"),), capacitors=(Capacitor(i["n1"], i["n2"], 1e-12, label="C1"),)), ("RL",), ("C1",), ("gnd", "vdd"), ("in",))
got = block_local_gain(ss4, blk(("out",), ("in",), ("out",), ("in", "out"), ("M1", "RL")))
rec("4_isolated_island", gain=got.gain, undefined=[u.code for u in got.undefined])
