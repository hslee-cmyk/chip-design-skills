"""CONTRACT 3.2: build_mna -- 소자마다 스탬프 1회, ω 무관 실수 G·C·BG·BC·sense_rows·sense_direct(쓰기 금지, 관측 1-tuple),
미지수 = 등장 노드 − 고정 노드 오름차순, defects(isolated_node)·charge_nodes, 2절 입력 계약 위반 ValueError."""
import numpy as np
import pytest

from gmid_engine.metrics import (
    Capacitor,
    Excitation,
    MnaSystem,
    MosSmallSignal,
    Resistor,
    Sense,
    SmallSignalCircuit,
    build_mna,
    mos_stamps,
    two_terminal_stamps,
)

from .conftest import EX2_CL, EX2_GDS, EX2_GM, codes, count_calls, ex1_rc, ex2_amp, ex2c_beta_cap, ex2d_sc_loop, ex3_miller


def _arr(x):
    return np.asarray(x)


# ---------- 예 1·2 손 조립과 비교 ----------

def test_rc_matrices_by_hand():
    s = ex1_rc()
    assert isinstance(s, MnaSystem)
    assert tuple(s.nodes) == (2,)
    assert set(s.fixed_nodes) == {0, 1}
    # KCL(2): (v2 − v1)/R + sC v2 = 0 -> (1/R + sC) v2 = v1/R
    assert np.allclose(_arr(s.G), [[1e-3]], rtol=1e-15, atol=0)
    assert np.allclose(_arr(s.C), [[1e-9]], rtol=1e-15, atol=0)
    assert np.allclose(_arr(s.BG), [[1e-3]], rtol=1e-15, atol=0)
    assert np.allclose(_arr(s.BC), [[0.0]], atol=0)
    assert np.array_equal(_arr(s.sense_rows), [[1.0]])
    assert np.array_equal(_arr(s.sense_direct), [[0.0]])
    assert s.defects == () and s.charge_nodes == ()


def test_cs_amp_matrices_by_hand():
    s = ex2_amp()
    # KCL(2): gm v1 + gds v2 + sCL v2 = I_in(2)  ->  BG = [−gm, +1], BC = [0, 0]
    assert tuple(s.nodes) == (2,)
    assert np.allclose(_arr(s.G), [[EX2_GDS]], rtol=1e-15, atol=0)
    assert np.allclose(_arr(s.C), [[EX2_CL]], rtol=1e-15, atol=0)
    assert np.allclose(_arr(s.BG), [[-EX2_GM, 1.0]], rtol=1e-15, atol=0)
    assert np.allclose(_arr(s.BC), [[0.0, 0.0]], atol=0)
    assert _arr(s.BG).shape == (1, 2)


def test_cap_divider_bc_carries_drive_coupling():
    s = ex2c_beta_cap()
    # 노드 3: s(Cf+Cs)v3 = s Cf v2  ->  G = 0, C = Cf+Cs, BG = 0, BC = Cf
    assert tuple(s.nodes) == (3,)
    assert np.allclose(_arr(s.G), [[0.0]], atol=0)
    assert np.allclose(_arr(s.C), [[4e-12]], rtol=1e-15, atol=0)
    assert np.allclose(_arr(s.BG), [[0.0]], atol=0)
    assert np.allclose(_arr(s.BC), [[1e-12]], rtol=1e-15, atol=0)
    assert tuple(s.charge_nodes) == (0,)
    assert s.defects == ()


def test_charge_nodes_index_in_unknowns():
    s = ex2d_sc_loop()
    assert tuple(s.nodes) == (2, 3)
    assert tuple(s.charge_nodes) == (1,)       # 노드 3 = 미지수 번호 1


def test_unknowns_ascending_and_fixed_excluded():
    s = ex3_miller(nm={0: 50, 1: 40, 2: 30, 3: 20})
    assert tuple(s.nodes) == (20, 30)
    assert set(s.fixed_nodes) == {40, 50}


def test_sense_direct_for_driven_neg_node():
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3),), capacitors=(Capacitor(2, 0, 1e-9),), ac_ground=(0,))
    s = build_mna(ck, (Excitation("a", voltages=((1, 1.0),)), Excitation("b", voltages=((1, 3.0),))), (Sense(2, 1),))
    assert np.array_equal(_arr(s.sense_rows), [[1.0]])
    assert np.allclose(_arr(s.sense_direct), [[-1.0, -3.0]], rtol=1e-15, atol=0)


def test_omitted_driven_node_is_zero_volt_in_other_column():
    s = ex2_amp()
    # iout 열에 vin 이 없다 -> 그 열의 BG 는 전류 주입만
    assert _arr(s.BG)[0, 1] == pytest.approx(1.0)


def test_arrays_read_only():
    s = ex3_miller()
    for name in ("G", "C", "BG", "BC", "sense_rows", "sense_direct"):
        a = getattr(s, name)
        with pytest.raises((ValueError, TypeError)):
            a[(0,) * np.ndim(a)] = 123.0
    assert np.isrealobj(_arr(s.G)) and np.isrealobj(_arr(s.C))


# ---------- 조립 1회 ----------

def test_each_stamp_called_exactly_once_per_element():
    ck = SmallSignalCircuit(
        mos=(MosSmallSignal(2, 1, 0, 0, 1e-4, 0.0, 1e-6), MosSmallSignal(3, 2, 0, 0, 1e-3, 0.0, 1e-5)),
        resistors=(Resistor(3, 4, 1e3),),
        capacitors=(Capacitor(2, 0, 1e-13), Capacitor(3, 0, 1e-12), Capacitor(2, 3, 5e-13), Capacitor(4, 0, 1e-12)),
        ac_ground=(0,),
    )
    with count_calls(mos_stamps, two_terminal_stamps) as n:
        build_mna(ck, (Excitation("v", voltages=((1, 1.0),)),), (Sense(4),))
    assert n == {"mos_stamps": 2, "two_terminal_stamps": 5}


# ---------- defects ----------

def test_isolated_node_defect():
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3), Resistor(2, 0, 1e3)), ac_ground=(0,))
    s = build_mna(ck, (Excitation("v", voltages=((1, 1.0),)),), (Sense(5),))   # 노드 5: 어떤 소자에도 없다
    assert "isolated_node" in codes(s.defects)
    assert all(u.category == "structural" for u in s.defects)


def test_no_defect_on_good_circuit():
    for s in (ex1_rc(), ex2_amp(), ex2c_beta_cap(), ex2d_sc_loop(), ex3_miller()):
        assert s.defects == ()


# ---------- 입력 계약 위반 ----------

def _rc():
    return SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3),), capacitors=(Capacitor(2, 0, 1e-9),), ac_ground=(0,))


def test_duplicate_excitation_name_value_error():
    with pytest.raises(ValueError):
        build_mna(_rc(), (Excitation("v", voltages=((1, 1.0),)), Excitation("v", voltages=((1, 2.0),))), (Sense(2),))


def test_driven_node_overlapping_ac_ground_value_error():
    with pytest.raises(ValueError):
        build_mna(_rc(), (Excitation("v", voltages=((0, 1.0),)),), (Sense(2),))


def test_current_into_fixed_node_value_error():
    with pytest.raises(ValueError):
        build_mna(_rc(), (Excitation("v", voltages=((1, 1.0),)), Excitation("i", currents=((1, 1.0),))), (Sense(2),))
    with pytest.raises(ValueError):
        build_mna(_rc(), (Excitation("v", voltages=((1, 1.0),)), Excitation("i", currents=((0, 1.0),))), (Sense(2),))


def test_sense_only_undriven_fixed_node_value_error():
    with pytest.raises(ValueError):
        build_mna(_rc(), (Excitation("v", voltages=((1, 1.0),)),), (Sense(0),))


def test_string_node_in_circuit_type_error():
    with pytest.raises(TypeError):
        build_mna(_rc(), (Excitation("v", voltages=((1, 1.0),)),), "out")


# ---------- 7a: 전하 열(BC 전용)·다중 관측 (1절·3.2) ----------

def test_charge_column_goes_to_bc_only():
    """전하 주입 q 는 전류 s·q -> 열의 BC 에만(+q, 노드로 들어가는 방향), BG 는 0. 예 2c 계 + 노드 3 전하 열."""
    ck = SmallSignalCircuit(capacitors=(Capacitor(2, 3, 1e-12), Capacitor(3, 0, 3e-12)), ac_ground=(0,))
    s = build_mna(ck, (Excitation("v", voltages=((2, 1.0),)), Excitation("q", charges=((3, 2.5),))), (Sense(3),))
    assert tuple(s.nodes) == (3,)
    assert np.array_equal(_arr(s.BG)[:, 1], [0.0])
    assert np.array_equal(_arr(s.BC)[:, 1], [2.5])


def test_multiple_senses_rows_in_order():
    """senses = Sense tuple(관측 여러 개): sense_rows (r, n), sense_direct (r, m), senses 그대로."""
    s = build_mna(_rc(), (Excitation("v", voltages=((1, 1.0),)),), (Sense(2), Sense(2, 1), Sense(1)))
    assert tuple(s.senses) == (Sense(2), Sense(2, 1), Sense(1))
    assert _arr(s.sense_rows).shape == (3, 1)
    assert np.array_equal(_arr(s.sense_rows), [[1.0], [1.0], [0.0]])
    assert np.array_equal(_arr(s.sense_direct), [[0.0], [-1.0], [1.0]])


def test_charge_into_fixed_node_value_error():
    with pytest.raises(ValueError):
        build_mna(_rc(), (Excitation("v", voltages=((1, 1.0),)), Excitation("q", charges=((1, 1.0),))), (Sense(2),))
    with pytest.raises(ValueError):
        build_mna(_rc(), (Excitation("q", charges=((0, 1.0),)),), (Sense(2),))


def test_empty_senses_rejected():
    """관측 1개 이상(1절)."""
    with pytest.raises((TypeError, ValueError)):
        build_mna(_rc(), (Excitation("v", voltages=((1, 1.0),)),), ())
