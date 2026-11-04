"""OP-3 회로 IR 생성(core.build_circuit.circuit_ir, core.build_benches.main_requests) + IR 이름 충돌 -- interface §5, T3-11, design §4.

oracle (a)(d): 입력 I(손으로 정한 회로: NMOS 하나 + 부하 저항 하나)에서 IR 이 입력 값을 SI 그대로 담고, 본 회로/테스트벤치 역할이
구성으로 갈리며 Z1 omit 이 그 소자를 뺀다는 규칙 문장(D §4.1·§4.2). 텍스트(넷리스트)를 보지 않는다. 시뮬레이터 호출 0.
해석: `circuit_ir(inp, bias, omit=(), short=()) -> (Circuit, blockers)`; 접지 넷 이름은 입력의 `gnd` 또는 상수 `0`.
"""
import pytest

from core import ir
from core.build_benches import main_requests
from core.build_circuit import circuit_ir
from core import requests as rq

from op23_support import World, deep, read_reject
from stub_adapter import StubAdapter

GROUND = ("gnd", "0")


@pytest.fixture
def w(tmp_path):
    return World(tmp_path)


def by_name(circuit):
    return {e.name: e for e in circuit.elements}


def test_free_ir_values_are_si_input_values(w):
    circuit, blockers = circuit_ir(w.inp, "free")
    assert blockers == []                                                # 양성 대조: 예시 I 는 막힘 없음
    els = by_name(circuit)
    m, rl = els["M1"], els["RL"]
    assert (m.kind, m.d, m.g) == ("nmos", "out", "in") and m.s in GROUND and m.b in GROUND
    assert (m.L, m.finger_w, m.n_fingers) == (5e-7, 1e-6, 2)             # 입력 값 그대로(SI, 단위 환산은 어댑터 몫)
    assert (m.diffusion.ad, m.diffusion.as_, m.diffusion.pd, m.diffusion.ps) == (0.0, 0.0, 0.0, 0.0)
    assert rl.value == 20000.0 and {rl.a, rl.b} == {"vdd", "out"}
    assert len(els) == len(circuit.elements)                             # 이름 중복 없음


def test_role_table_splits_circuit_and_testbench(w):
    circuit, _ = circuit_ir(w.inp, "free")
    circ = {n for n, r in circuit.role.items() if r == "circuit"}
    assert circ == {"M1", "RL"}                                          # 입력에 있는 소자만 본 회로
    tb = {n for n, r in circuit.role.items() if r == "testbench"}
    assert tb and tb.isdisjoint(circ) and tb | circ == set(circuit.role) == set(by_name(circuit))
    rails = [e for e in circuit.elements if type(e).__name__ == "VSource" and circuit.role[e.name] == "testbench"
             and e.dc == 1.8]
    assert len(rails) == 1                                               # 레일 vdd = 1.8 V 전압원은 테스트벤치 원소


def test_testbench_names_use_tb_prefix(w):
    circuit, _ = circuit_ir(w.inp, "free")
    assert all(n.startswith("tb:") for n, r in circuit.role.items() if r == "testbench")      # D §4.1 `tb:<용도>:<대상>`


def test_z1_omit_removes_element(w):
    circuit, _ = circuit_ir(w.inp, "free", omit=("RL",))
    assert "RL" not in by_name(circuit) and "M1" in by_name(circuit)


def test_forced_ir_fixes_predicted_node_voltage(w):
    circuit, _ = circuit_ir(w.inp, "forced")
    fixed = [e for e in circuit.elements if type(e).__name__ == "VSource" and e.p == "out" and e.dc == 0.9]
    assert len(fixed) == 1 and circuit.role[fixed[0].name] == "testbench"      # 예측 0.9 V 를 이상 전압원으로


def test_free_ir_has_no_predicted_voltage_source_on_output(w):
    circuit, _ = circuit_ir(w.inp, "free")
    assert [e for e in circuit.elements if type(e).__name__ == "VSource" and e.p == "out" and e.dc == 0.9] == []


def test_two_reference_rails_is_a_blocker_not_an_error(w):
    inp = deep(w.inp); inp["rails"][0]["reference"] = True
    circuit, blockers = circuit_ir(inp, "free")
    assert isinstance(blockers, list) and len(blockers) >= 1 and all(isinstance(b, str) and b for b in blockers)


def test_main_requests_op_and_ac_from_testbench(w):
    circuit, _ = circuit_ir(w.inp, "free")
    reqs = main_requests(w.inp, "free", circuit)
    ops = [r for r in reqs if isinstance(r, rq.Op)]
    acs = [r for r in reqs if isinstance(r, rq.Ac)]
    assert len(ops) == 1 and len(acs) == 1
    ac = acs[0]
    assert (ac.f_start, ac.f_stop, ac.points_per_decade) == (0.01, 1e10, 20)      # 입력 testbench.ac 값 그대로
    assert ops[0].id != ac.id


# ------------------------------------------------------------------ T3-11 대소문자 접기 충돌
def collide_input(w):
    inp = deep(w.inp)
    inp["passives"] += [{"name": "R3", "kind": "resistor", "terminals": ["out", "Aa"], "value": 1e3},
                        {"name": "R2", "kind": "resistor", "terminals": ["Aa", "aA"], "value": 1e3},
                        {"name": "R4", "kind": "resistor", "terminals": ["aA", "gnd"], "value": 1e3}]
    return inp


def test_t3_11_case_fold_collision_refused_when_adapter_is_case_insensitive(w):
    stub = StubAdapter({"M1": {"gm": 6e-4, "gds": 1 / 60000.0}}, case_insensitive=True)
    rc, out = w.run(stub, inp=collide_input(w))
    rec = read_reject(out)
    assert rec["code"] == "ir_name_collision" and stub.calls == []


def test_t3_11_same_input_passes_when_adapter_is_case_sensitive(w):
    stub = StubAdapter({"M1": {"gm": 6e-4, "gds": 1 / 60000.0}}, case_insensitive=False)
    rc, out = w.run(stub, inp=collide_input(w))
    assert not (out / "cs_toy.reject.json").exists() and len(stub.calls) >= 1
