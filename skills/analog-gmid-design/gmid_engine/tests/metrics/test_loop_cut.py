"""CONTRACT 3.16: cut_circuit -- LoopCut 마다 원소 단자를 원래 노드 n 에서 새 노드 x 로 옮긴다. 같은 원래 노드 -> 같은 x,
x = 원래 최대 노드 인덱스 뒤에 n 오름차순(재번호 불변), 교류접지 그대로. 결과 pairs·excitations(4k 열: I(n..), I(x..),
Q(n..), Q(x..))·senses(2k: V(n..), V(x..)), ValueError(범위 밖·같은 원소 두 번·교류접지 절단), 빈 cuts.
기대값은 계약 문장과 test 쪽 원소 목록에서 직접 만든다."""
import pytest

from gmid_engine.metrics import (
    Capacitor,
    CutCircuit,
    LoopCut,
    MosSmallSignal,
    Resistor,
    Sense,
    SmallSignalCircuit,
    build_mna,
    cut_circuit,
)

from .conftest import EX7, STAMP_FUNCS, circuit_of, count_calls, ex7_parts, ex7b_parts


def _ex7():
    return circuit_of(*ex7_parts())


def _flat(pairs_list):
    return {n: a for n, a in pairs_list}


def test_ex7_single_cut_moves_cf_terminal_b():
    cut = cut_circuit(_ex7(), (LoopCut("capacitor", 1, "b"),))
    assert isinstance(cut, CutCircuit)
    assert tuple(cut.pairs) == ((3, 4),)                   # 예 7: 최대 노드 3 -> x = 4
    caps = cut.circuit.capacitors
    assert (caps[1].a, caps[1].b) == (2, 4)                 # Cf 의 b 단자만 옮김
    assert (caps[0].a, caps[0].b) == (2, 0) and (caps[2].a, caps[2].b) == (3, 0)   # 나머지 그대로
    m = cut.circuit.mos[0]
    assert (m.d, m.g, m.s, m.b) == (2, 3, 0, 0)
    assert tuple(cut.circuit.ac_ground) == (0,)
    assert tuple(cut.cuts) == (LoopCut("capacitor", 1, "b"),)


def test_ex7_excitations_and_senses_structure():
    """4k 열(k=1): 단위 전류 I(n), I(x), 단위 전하 Q(n), Q(x) 순서, 관측 V(n), V(x) 순서."""
    cut = cut_circuit(_ex7(), (LoopCut("capacitor", 1, "b"),))
    ex = cut.excitations
    assert len(ex) == 4
    assert [tuple(e.voltages) for e in ex] == [()] * 4
    assert [tuple(e.currents) for e in ex] == [((3, 1.0),), ((4, 1.0),), (), ()]
    assert [tuple(e.charges) for e in ex] == [(), (), ((3, 1.0),), ((4, 1.0),)]
    assert len({e.name for e in ex}) == 4                     # 계 안에서 이름 유일(1절)
    assert tuple(cut.senses) == (Sense(3), Sense(4))


def test_ex7b_two_cuts_pairs_ascending_after_max_node():
    c = circuit_of(*ex7b_parts())
    cut = cut_circuit(c, (LoopCut("capacitor", 4, "b"), LoopCut("capacitor", 1, "b")))   # 입력 순서와 무관
    assert tuple(cut.pairs) == ((3, 14), (13, 15))
    ex = cut.excitations
    assert len(ex) == 8 and len(cut.senses) == 4
    assert [tuple(e.currents) for e in ex[:4]] == [((3, 1.0),), ((13, 1.0),), ((14, 1.0),), ((15, 1.0),)]
    assert [tuple(e.charges) for e in ex[4:]] == [((3, 1.0),), ((13, 1.0),), ((14, 1.0),), ((15, 1.0),)]
    assert tuple(cut.senses) == (Sense(3), Sense(13), Sense(14), Sense(15))
    caps = cut.circuit.capacitors
    assert (caps[1].a, caps[1].b) == (2, 14) and (caps[4].a, caps[4].b) == (12, 15)


def test_same_original_node_shares_one_x():
    """같은 원래 노드에서 옮긴 단자 두 개 -> 같은 x(오라클 lbx_<넷> 하나), pairs 1개, 열 4개."""
    c = SmallSignalCircuit(
        mos=(MosSmallSignal(2, 3, 0, 0, 1e-3, 0.0, 1e-5),),
        resistors=(Resistor(3, 2, 1e5),),
        capacitors=(Capacitor(2, 3, 1e-12), Capacitor(3, 0, 3e-12)),
        ac_ground=(0,),
    )
    cut = cut_circuit(c, (LoopCut("capacitor", 0, "b"), LoopCut("resistor", 0, "a")))
    assert tuple(cut.pairs) == ((3, 4),)
    assert (cut.circuit.capacitors[0].a, cut.circuit.capacitors[0].b) == (2, 4)
    assert (cut.circuit.resistors[0].a, cut.circuit.resistors[0].b) == (4, 2)
    assert len(cut.excitations) == 4 and len(cut.senses) == 2


def test_x_after_max_node_including_ac_ground():
    """x 는 원래 회로 최대 노드 인덱스 뒤: 교류접지 노드가 가장 큰 번호여도 그 뒤."""
    c = circuit_of(*ex7_parts(), ac_ground=(0,), nm={0: 50, 2: 7, 3: 9})
    cut = cut_circuit(c, (LoopCut("capacitor", 1, "b"),))
    assert tuple(cut.pairs) == ((9, 51),)


def test_cut_circuit_builds_once_with_4k_columns_2k_senses():
    """I-14 앞부분: build_mna(cut.circuit, cut.excitations, cut.senses) 한 번 -- (n, 4k) 열, (2k, n) 관측."""
    c = circuit_of(*ex7b_parts())
    with count_calls(*STAMP_FUNCS) as n0:
        cut = cut_circuit(c, (LoopCut("capacitor", 1, "b"), LoopCut("capacitor", 4, "b")))
    assert n0 == {"mos_stamps": 0, "two_terminal_stamps": 0}        # 절단은 스탬프하지 않는다
    with count_calls(*STAMP_FUNCS) as n1:
        s = build_mna(cut.circuit, cut.excitations, cut.senses)
    assert n1 == {"mos_stamps": 2, "two_terminal_stamps": 7}          # 소자마다 1회
    import numpy as np
    assert np.shape(s.BG)[1] == 8 and np.shape(s.BC)[1] == 8
    assert np.shape(s.sense_rows)[0] == 4


def test_pure_function_input_unchanged():
    c = _ex7()
    before = (c.capacitors, c.resistors, c.mos, c.ac_ground)
    cut_circuit(c, (LoopCut("capacitor", 1, "b"),))
    assert (c.capacitors, c.resistors, c.mos, c.ac_ground) == before


def test_deterministic():
    a = cut_circuit(circuit_of(*ex7b_parts()), (LoopCut("capacitor", 1, "b"), LoopCut("capacitor", 4, "b")))
    b = cut_circuit(circuit_of(*ex7b_parts()), (LoopCut("capacitor", 1, "b"), LoopCut("capacitor", 4, "b")))
    assert a == b


# ---------- 입력 계약 위반 ----------

def test_empty_cuts_rejected():
    """계약 3.16 은 '빈 tuple(TypeError)', 2절은 '빈 cuts' 를 ValueError 목록에 적는다 -- 둘 중 하나면 통과(모호, 보고)."""
    with pytest.raises((TypeError, ValueError)):
        cut_circuit(_ex7(), ())


@pytest.mark.parametrize("cut", [LoopCut("capacitor", 3, "b"), LoopCut("resistor", 0, "a")],
                         ids=["cap_index_out_of_range", "no_resistors"])
def test_index_out_of_range(cut):
    with pytest.raises(ValueError):
        cut_circuit(_ex7(), (cut,))


@pytest.mark.parametrize("cuts", [
    (LoopCut("capacitor", 1, "b"), LoopCut("capacitor", 1, "a")),     # 두 단자 모두(로더 feedback_cut_ambiguous 조건)
    (LoopCut("capacitor", 1, "b"), LoopCut("capacitor", 1, "b")),
], ids=["both_terminals", "same_terminal_twice"])
def test_same_element_twice(cuts):
    with pytest.raises(ValueError):
        cut_circuit(_ex7(), cuts)


def test_cut_node_on_ac_ground():
    """CL(2,0) 의 b 단자 = 노드 0(교류접지) -> ValueError."""
    with pytest.raises(ValueError):
        cut_circuit(_ex7(), (LoopCut("capacitor", 0, "b"),))


@pytest.mark.parametrize("kw", [dict(kind="mos", index=0, terminal="a"), dict(kind="capacitor", index=0, terminal="c")])
def test_loopcut_vocabulary(kw):
    """1절: kind ∈ {resistor, capacitor}, terminal ∈ {a, b}."""
    with pytest.raises(ValueError):
        LoopCut(**kw)


def test_ex7_values_constant_untouched():
    """예 7 원소 값은 절단 뒤에도 같다(값을 바꾸지 않고 단자만 옮긴다)."""
    cut = cut_circuit(_ex7(), (LoopCut("capacitor", 1, "b"),))
    assert [c.farad for c in cut.circuit.capacitors] == [EX7["cl"], EX7["cf"], EX7["cs"]]
