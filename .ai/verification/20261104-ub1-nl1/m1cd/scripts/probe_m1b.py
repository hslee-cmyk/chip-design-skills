"""M-1b 재판정: (2) 전하 넷 확장 루프가 MOS 단자 용량을 놓치는 회로를 전회로 풀이·손 값과 대조. (1) library 합성 값 block_local_gain C 조립 횟수. 결과 jsonl append."""
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
from gmid_engine.metrics import Capacitor, MosSmallSignal, Resistor, SmallSignalCircuit, SsCircuit, block_local_gain
from gmid_engine.metrics._helpers_nodal import nodal_solve
from gmid_engine.metrics.aux_types import BlockStruct

SN = importlib.import_module("gmid_engine.metrics.ss_nodal")
BM = importlib.import_module("gmid_engine.metrics.block_model")


def rec(name, **kw):
    kw["case"] = name
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(kw, ensure_ascii=False, default=repr) + "\n")
    print(name, kw)


def blk(key, inputs, outputs, nodes, members):
    return BlockStruct(tuple(key), "gain", 1, tuple(inputs), tuple(outputs), tuple(nodes), (), tuple(sorted(members)))


GM, GDS, RL, C1, C2, CB, C3 = 1e-3, 2e-5, 3e4, 2e-12, 3e-12, 1e-12, 4e-12


def case(name, c3, swap=False):
    """in -C1- n1 -C2- gnd, M1(d out, g n1, s gnd), RL(vdd-out). M3(d vdd, s gnd): g n1·b n2(또는 swap: g n2·b n1), cgb CB 로만 n1-n2 를 잇는다. n2 -C3- gnd(c3 > 0 일 때).
    M3 는 d·s 가 F 라 스탬프 안 됨. n2 는 용량 전용 넷이고 스탬프 MOS 가 안 읽는다."""
    nets = ("gnd", "vdd", "in", "n1", "n2", "out")
    i = {n: k for k, n in enumerate(nets)}
    g3, b3 = (i["n2"], i["n1"]) if swap else (i["n1"], i["n2"])
    mos = (MosSmallSignal(i["out"], i["n1"], i["gnd"], i["gnd"], GM, 0.0, GDS, label="M1"),
           MosSmallSignal(i["vdd"], g3, i["gnd"], b3, 1e-4, 0.0, 1e-5, cgb=CB, label="M3"))
    res = (Resistor(i["vdd"], i["out"], RL, label="RL"),)
    caps = [Capacitor(i["in"], i["n1"], C1, label="C1"), Capacitor(i["n1"], i["gnd"], C2, label="C2")]
    if c3:
        caps.append(Capacitor(i["n2"], i["gnd"], c3, label="C3"))
    ss = SsCircuit(nets, SmallSignalCircuit(mos=mos, resistors=res, capacitors=tuple(caps)), ("RL",), tuple(c.label for c in caps), ("gnd", "vdd"), ("in",))
    got = block_local_gain(ss, blk(("out",), ("in",), ("out",), ("in", "out"), ("M1", "RL")))
    nod = SN.nodal_of(ss)
    v, _r = nodal_solve(nod.factor, len(nets), {i["in"]: 1.0})
    # 손: n1 행 (C1+C2+CB) v1 - CB v2 = C1, n2 행 -CB v1 + (CB+c3) v2 = 0
    A = np.array([[C1 + C2 + CB, -CB], [-CB, CB + c3]])
    v1, v2 = np.linalg.solve(A, np.array([C1, 0.0]))
    hand = -GM / (GDS + 1 / RL) * v1
    rec(name, block_gain=got.gain, full_gain=None if v is None else float(v[i["out"]]), hand_gain=float(hand), hand_v1=float(v1), hand_v2=float(v2), node_v=got.node_v,
        rel_err=None if got.gain is None else abs(got.gain / hand - 1), undefined=[u.code for u in got.undefined])


case("a_cgb_island_with_c3", C3)
case("b_cgb_island_only_cgb", 0.0)
case("c_cgb_island_swapped_g_b", C3, swap=True)

# 앞 재현 case 2·6 은 probe_a107.py 가 잰다.
# A-4: 전하 넷 없는 회로의 C 조립 횟수(모듈 속성 교체로 호출 자리별 계수)
from gmid_engine.tests.metrics import u7_ngcc as N
orig = BM.capacitance_matrix
sites = {}


def counted(circuit, size):
    s = sys._getframe(1).f_code.co_name
    sites[s] = sites.get(s, 0) + 1
    return orig(circuit, size)


BM.capacitance_matrix = counted
BR = importlib.import_module("gmid_engine.metrics.block_residual")
for name in ("folded_cascode", "ngcc_3stage_ff", "two_stage_ota"):
    sites.clear()
    ss, structs, decls = N.library_case(name)
    blocks = 0
    charge_n = 0
    for v in structs:
        every = {n for b in v.blocks for n in b.nodes}
        excl = tuple(sorted({m for f in v.ff for m in f.members}))
        for b in v.blocks:
            blocks += 1
            _f, _u, ch, _m, _r, _c = BM._structure(ss, b, BM._unit_drive(b.inputs), every - set(b.nodes), excl, (), v.ac_ground)
            charge_n += len(ch)
    structure_only = dict(sites)
    sites.clear()
    for view, vstruct in zip(decls, structs):
        BR.block_residual(ss, view, vstruct, nodal=None)
    rec("c_matrix_calls_" + name, blocks=blocks, charge_nets=charge_n, per_structure_loop=structure_only, one_block_residual=dict(sites))

# 같은 입력 이중 조립: 전하 넷 있는 호출 하나의 조립 횟수
sites.clear()
nets = ("gnd", "vdd", "in", "n", "out")
i = {n: k for k, n in enumerate(nets)}
ss = SsCircuit(nets, SmallSignalCircuit(mos=(MosSmallSignal(i["out"], i["n"], i["gnd"], i["gnd"], GM, 0.0, GDS, label="M1"),), resistors=(Resistor(i["vdd"], i["out"], RL, label="RL"),),
                                        capacitors=(Capacitor(i["in"], i["n"], C1, label="C1"), Capacitor(i["n"], i["gnd"], C2, label="C2"))), ("RL",), ("C1", "C2"), ("gnd", "vdd"), ("in",))
block_local_gain(ss, blk(("out",), ("in",), ("out",), ("in", "out"), ("M1", "RL")))
rec("c_matrix_calls_one_charge_block", sites=dict(sites))
