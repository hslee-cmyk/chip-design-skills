"""[U17 ①-b] 커널 구조 파생 계산 블록 `kernel_fields` -- 규칙 H 1:1 test(원본 `sizing/kernel_fields.py`).

근거: 설계 40 v1.9.1 §2.4.7 `KernelContext` 행('설계 값은 S0 수준 필드: graph/kernel: theta_schema, fixed_values, resistor_values, l_ties'),
§2.4.8 '커널 컨텍스트 구조 파생 -> graph/kernel: theta_schema, fixed_values, resistor_values, l_ties, writer = build_kernel_context 를 블록으로(sizing)',
§2.4.2 'S0 수준 값은 계산 블록으로 만들고 … 입력 버전이 같으면 다시 계산하지 않는다'. 옛 KernelContext 칸의 의미(CONTRACT 1.3·13절·14.1)는 그대로:
- fixed_values = W3 노드 목표 ∪ (입력 DC 선언 시) 목표 없는 입력 포트의 입력 DC, W3 우선, 넷 이름순.
- resistor_values = spec 에 값이 선언된 DC 경로 저항(S1 dc_pruned 잎 저항 제외), 이름순.
- l_ties = derived·ratified L 동치류의 (비주인 멤버, 주인), 정렬. S1v 필드가 없으면 ().
기대값은 손 회로 구성과 위 문장에서 손으로 적는다(피검 함수로 만들지 않는다). L 동치류 입력은 `inject_l_classes`(graph/s1v: l_classes 필드 주입).
"""
import pytest

from gmid_engine.graph import S1V_KEY, LClass, build_s1
from gmid_engine.sizing import KERNEL_CONTEXT_WRITER, KERNEL_KEY, kernel_fields, lift_s1

from .conftest import SUPPLIES, inject_l_classes, load_doc, mos, topo, two

FIELDS = ("fixed_values", "resistor_values", "l_ties")


def _two_in():
    # test_kernel_context.test_fixed_values_w3_and_input_dc 와 같은 손 회로(입력 포트 inp·inn, 꼬리 t)
    return topo("hand_two_in",
                [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "out", "inn", "t"),
                 mos("M3", "pmos", "o1", "o1", "vdd"), mos("M4", "pmos", "out", "o1", "vdd"),
                 mos("M5", "nmos", "t", "vb", "gnd")],
                {"inp": ("input", "a"), "inn": ("input", "b"), "out": ("output", "c")},
                bias=["vb"])


def _base(tmp_path, doc, l_classes=()):
    return lift_s1(inject_l_classes(build_s1(load_doc(tmp_path, doc), dict(SUPPLIES)), tuple(l_classes)))


def _read(snap):
    return {f: snap.value("graph", KERNEL_KEY, f) for f in FIELDS}


def test_writer_and_fields(tmp_path):
    """§2.4.8: 세 필드가 graph/kernel 레코드에 있고 writer 는 한 블록(kernel_fields 의 이름)이다."""
    snap = kernel_fields(_base(tmp_path, _two_in()), (), None, ())
    for f in FIELDS:
        assert snap.field("graph", KERNEL_KEY, f).writer == KERNEL_CONTEXT_WRITER
    assert kernel_fields.name == KERNEL_CONTEXT_WRITER
    assert _read(snap) == {"fixed_values": (), "resistor_values": (), "l_ties": ()}


def test_fixed_values_w3_wins_over_input_dc(tmp_path):
    snap = kernel_fields(_base(tmp_path, _two_in()), (("inp", 1.0), ("t", 0.3)), 0.9, ())
    assert _read(snap)["fixed_values"] == (("inn", 0.9), ("inp", 1.0), ("t", 0.3))
    snap = kernel_fields(_base(tmp_path, _two_in()), (), 0.9, ())
    assert _read(snap)["fixed_values"] == (("inn", 0.9), ("inp", 0.9))


def test_resistor_values_exclude_pruned_and_undeclared(tmp_path):
    # R2(out–leaf) 는 잎 가지치기 저항(dc_pruned), R3 값 미선언, C1 은 저항 아님 -> R1 만
    doc = topo("hand_rvals", [mos("M1", "nmos", "out", "in", "sdeg")],
               {"in": ("input", "x"), "out": ("output", "y")},
               passives=[two("R1", "resistor", "vdd", "out"), two("R2", "resistor", "out", "leaf"),
                         two("R3", "resistor", "sdeg", "gnd"), two("C1", "capacitor", "out", "gnd")])
    snap = kernel_fields(_base(tmp_path, doc), (), None, (("C1", 1e-12), ("R1", 1e4), ("R2", 5e3), ("R3", None)))
    assert _read(snap)["resistor_values"] == (("R1", 1e4),)


def test_l_ties_from_s1v_field_only_derived_and_ratified(tmp_path):
    classes = (LClass(("M3", "M4"), "M3", "hand", "derived"), LClass(("M1", "M2"), "M2", "hand", "ratified"),
               LClass(("M5",), "M5", "hand", "derived"))
    snap = kernel_fields(_base(tmp_path, _two_in(), classes), (), None, ())
    assert _read(snap)["l_ties"] == (("M1", "M2"), ("M4", "M3"))
    review = (LClass(("M3", "M4"), "M3", "hand", "review_needed"),)
    snap = kernel_fields(_base(tmp_path, _two_in(), review), (), None, ())
    assert _read(snap)["l_ties"] == ()


def test_no_s1v_field_means_no_ties(tmp_path):
    base = _base(tmp_path, _two_in())
    assert base.record("graph", S1V_KEY) is None
    assert _read(kernel_fields(base, (), None, ()))["l_ties"] == ()


@pytest.mark.parametrize("classes", [
    (LClass(("M1", "Mzz"), "M1", "hand", "derived"),),                                          # S1 원소 아님
    (LClass(("M1", "M2"), "M1", "hand", "derived"), LClass(("M2", "M3"), "M2", "hand", "derived")),  # 주인 M2 가 다른 동치류 멤버
    (LClass(("M1", "M3"), "M1", "hand", "derived"), LClass(("M2", "M3"), "M2", "hand", "derived")),  # M3 가 두 동치류 멤버
], ids=["unknown", "owner_is_member", "two_classes"])
def test_l_class_contract_violation(tmp_path, classes):
    with pytest.raises(ValueError):
        kernel_fields(_base(tmp_path, _two_in(), classes), (), None, ())


def test_reuse_same_inputs(tmp_path):
    """§2.4.2: 입력 버전이 같으면 다시 계산하지 않는다(계산 0, 같은 스냅샷)."""
    snap = kernel_fields(_base(tmp_path, _two_in()), (("t", 0.3),), 0.9, ())
    kernel_fields.reset_stats()
    assert kernel_fields(snap, (("t", 0.3),), 0.9, ()) is snap
    st = kernel_fields.stats()
    assert (st.calls, st.reuses, st.computes) == (1, 1, 0)
