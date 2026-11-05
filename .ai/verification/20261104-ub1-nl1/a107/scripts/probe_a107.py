"""A-107 재판정 probe: M-1 과잉 제외·부족 제외 합성 회로를 전회로 풀이(nodal_of)와 손 값으로 대조, 행 모드 둘째 정의. 결과 jsonl append."""
import importlib
import json
import pathlib
import sys

skill = sys.argv[1]
sys.path.insert(0, skill)
sys.path.insert(0, str(pathlib.Path(skill) / "gmid_engine" / "tests"))
out = pathlib.Path(sys.argv[2])
out.write_text("", encoding="utf-8")
from gmid_engine.metrics import Capacitor, MosSmallSignal, Resistor, SmallSignalCircuit, SsCircuit, block_local_gain
from gmid_engine.metrics._helpers_nodal import nodal_solve
from gmid_engine.metrics.aux_types import BlockStruct

SN = importlib.import_module("gmid_engine.metrics.ss_nodal")
GM1, GDS1, R1, GM2, GDS2, R2, CC, C2, RZ = 1e-3, 2e-5, 3e4, 2e-3, 3e-5, 2e4, 1e-12, 3e-12, 1e3


def rec(name, **kw):
    kw["case"] = name
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(kw, ensure_ascii=False, default=repr) + "\n")
    print(name, kw)


def blk(key, inputs, outputs, nodes, members):
    return BlockStruct(tuple(key), "gain", 1, tuple(inputs), tuple(outputs), tuple(nodes), (), tuple(sorted(members)))


def build(extra_nets, extra_mos, extra_res, caps_of):
    nets = ("gnd", "vdd", "in", "out", "mz", "n", "o2") + tuple(extra_nets)
    i = {n: k for k, n in enumerate(nets)}
    mos = [MosSmallSignal(i["out"], i["in"], i["gnd"], i["gnd"], GM1, 0.0, GDS1, label="M1"),
           MosSmallSignal(i["o2"], i["n"], i["gnd"], i["gnd"], GM2, 0.0, GDS2, label="M2")] + list(extra_mos(i))
    res = [Resistor(i["vdd"], i["out"], R1, label="R1"), Resistor(i["vdd"], i["o2"], R2, label="R2"), Resistor(i["out"], i["mz"], RZ, label="Rz")] + list(extra_res(i))
    caps = list(caps_of(i))
    ss = SsCircuit(nets, SmallSignalCircuit(mos=tuple(mos), resistors=tuple(res), capacitors=tuple(caps)), tuple(r.label for r in res), tuple(c.label for c in caps), ("gnd", "vdd"), ("in",))
    return ss, i


def compare(name, ss, i, members, nodes=("in", "out", "o2")):
    got = block_local_gain(ss, blk(("o2",), ("in",), ("o2",), nodes, members))
    nod = SN.nodal_of(ss)
    v, _r = nodal_solve(nod.factor, len(ss.nodes), {i["in"]: 1.0})
    rec(name, block_gain=got.gain, full_gain=None if v is None else float(v[i["o2"]]), node_v=got.node_v, members=got.members, undefined=[u.code for u in got.undefined])


M = ("M1", "M2", "R1", "R2", "Rz")
# 1 M-1 재현
ss, i = build((), lambda i: (), lambda i: (), lambda i: (Capacitor(i["mz"], i["n"], CC, label="Cc"), Capacitor(i["n"], i["gnd"], C2, label="C2")))
compare("1_m1_case2", ss, i, M, ("in", "out", "mz", "n", "o2"))
# 2 두 단 저항 사슬 끝이 C 독자
ss, i = build(("mz2",), lambda i: (), lambda i: (Resistor(i["mz"], i["mz2"], RZ, label="Rz2"),), lambda i: (Capacitor(i["mz2"], i["n"], CC, label="Cc"), Capacitor(i["n"], i["gnd"], C2, label="C2")))
compare("2_two_resistor_chain_read", ss, i, M + ("Rz2",), ("in", "out", "mz", "mz2", "n", "o2"))
# 3 옛 막다른 경우: Rz-Cc 가 전도 넷(o2)으로 -- 전하 넷 없음, 빼야 함. M2 g 는 out
nets = ("gnd", "vdd", "in", "out", "mz", "o2")
i = {n: k for k, n in enumerate(nets)}
mos = (MosSmallSignal(i["out"], i["in"], i["gnd"], i["gnd"], GM1, 0.0, GDS1, label="M1"), MosSmallSignal(i["o2"], i["out"], i["gnd"], i["gnd"], GM2, 0.0, GDS2, label="M2"))
res = (Resistor(i["vdd"], i["out"], R1, label="R1"), Resistor(i["vdd"], i["o2"], R2, label="R2"), Resistor(i["out"], i["mz"], RZ, label="Rz"))
ss = SsCircuit(nets, SmallSignalCircuit(mos=mos, resistors=res, capacitors=(Capacitor(i["mz"], i["o2"], CC, label="Cc"),)), tuple(r.label for r in res), ("Cc",), ("gnd", "vdd"), ("in",))
got = block_local_gain(ss, blk(("o2",), ("in",), ("o2",), ("in", "out", "o2"), M))
rec("3_old_dead_end_rz_cc_to_conducting", gain=got.gain, hand=GM1 / (GDS1 + 1 / R1) * GM2 / (GDS2 + 1 / R2), members=got.members, node_v=got.node_v, rz_dropped="Rz" not in got.members)
# 4 다른 막다른 저항이 따로 있고 전하 넷도 있음: 전하와 안 이어진 쪽만 빠져야 함
ss, i = build(("md",), lambda i: (), lambda i: (Resistor(i["o2"], i["md"], RZ, label="Rd"),), lambda i: (Capacitor(i["mz"], i["n"], CC, label="Cc"), Capacitor(i["n"], i["gnd"], C2, label="C2"), Capacitor(i["md"], i["gnd"], CC, label="Cd")))
got = block_local_gain(ss, blk(("o2",), ("in",), ("o2",), ("in", "out", "o2"), M + ("Rd",)))
rec("4_unrelated_dead_end_with_charge_present", gain=got.gain, members=got.members, rd_dropped="Rd" not in got.members, rz_kept="Rz" in got.members)
# 5 막다른 넷의 C 가 읽지 않는 용량 전용 넷으로만 이어짐: 전하 넷 아님 -> 빠져야 함
nets = ("gnd", "vdd", "in", "out", "mz", "k")
i = {n: k for k, n in enumerate(nets)}
mos = (MosSmallSignal(i["out"], i["in"], i["gnd"], i["gnd"], GM1, 0.0, GDS1, label="M1"),)
res = (Resistor(i["vdd"], i["out"], R1, label="R1"), Resistor(i["out"], i["mz"], RZ, label="Rz"))
ss = SsCircuit(nets, SmallSignalCircuit(mos=mos, resistors=res, capacitors=(Capacitor(i["mz"], i["k"], CC, label="Cc"), Capacitor(i["k"], i["gnd"], C2, label="C2"))), tuple(r.label for r in res), ("Cc", "C2"), ("gnd", "vdd"), ("in",))
got = block_local_gain(ss, blk(("out",), ("in",), ("out",), ("in", "out"), ("M1", "R1", "Rz")))
rec("5_dead_end_to_unread_cap_island", gain=got.gain, hand=-GM1 / (GDS1 + 1 / R1), members=got.members, node_v=got.node_v)
# 6 부족 제외: 용량이 MOS 단자 용량(cgb)인 경우. M3 g=n, b=mz, d·s 는 F -- 스탬프 안 됨, 커패시터 소자 아님
ss, i = build((), lambda i: (MosSmallSignal(i["vdd"], i["n"], i["gnd"], i["mz"], 1e-4, 0.0, 1e-5, cgb=CC, label="M3"),), lambda i: (), lambda i: (Capacitor(i["n"], i["gnd"], C2, label="C2"),))
compare("6_mos_cap_reader_on_dead_end", ss, i, M, ("in", "out", "mz", "n", "o2"))
# 7 행 모드: case 2 (n 이 블록 노드 밖 / 안)
gb = importlib.import_module("gmid_engine.tests.metrics.gb4_hand")
from gmid_engine.metrics import block_gain_model_of
pins = {"M1": ("out", "in", "gnd", "gnd"), "M2": ("o2", "n", "gnd", "gnd"), "R1": ("vdd", "out"), "R2": ("vdd", "o2"), "Rz": ("out", "mz"), "Cc": ("mz", "n"), "C2": ("n", "gnd")}
rec("7_helper_signature", local_inputs=str(__import__("inspect").signature(gb.local_inputs)), block_spec=str(__import__("inspect").signature(gb.block_spec)))
