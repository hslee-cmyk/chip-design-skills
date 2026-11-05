"""sizing/symmetry_marks.py -- `symmetry_marks(inputs: DcInputs) -> graph.SymmetryMarks` (sizing CONTRACT 1절 표 [U17-1d]·3.0b 선언 표시 형식,
설계 40 v1.8 §6-8 '원소 처음 색(kind, is_diode, 선언 표시)·노드 색(레일, 포트 role, 선언 표시)', D-2 그래프 하나).

기대값은 DcInputs 손 입력에서 3.0b 형식대로 손으로 적는다:
- 원소 표시: 값 선언 `("value", 값)`(값이 None 이면 표시 없음), engine 원소 `("engine", 0.0)`, 선언 영역 [EO-1 범위 4, A-88] `triode` -> `("triode", 0.0)`, `off` -> `("off_l", l_m)`·`("off_w", w_m)` -- 원소 이름순, 원소 안 표시 이름순.
- 노드 표시: 노드 목표 ((넷, V), ...) 넷 이름순, 입력 DC `input_dc_v`(없으면 None). 레일 전위는 여기서 만들지 않는다(대칭 블록이 supplies 에서).
"""
import dataclasses

import pytest

from gmid_engine.authoring import RegionDecl
from gmid_engine.graph import NO_MARKS, SymmetryMarks
from gmid_engine.sizing import DcInputs, symmetry_marks


def test_empty_inputs_give_no_marks():
    m = symmetry_marks(DcInputs((("gnd", 0.0), ("vdd", 1.8))))
    assert m == SymmetryMarks(None, (), ()) == NO_MARKS


def test_full_marks_by_hand():
    inputs = DcInputs((("gnd", 0.0), ("vdd", 1.8)), input_dc_v=0.9,
                      node_targets=(("o2", 1), ("o1", 0.9)),
                      element_values=(("R2", 1e5), ("I1", 2e-5), ("Rx", None)),
                      regions=(RegionDecl("M9", "triode"), RegionDecl("M8", "off", None, ("gain_ss_db",), 2e-6, 1e-6)),
                      engine_elements=("Cc", "R2"))
    m = symmetry_marks(inputs)
    assert m.input_dc_v == 0.9 and isinstance(m.input_dc_v, float)
    assert m.targets == (("o1", 0.9), ("o2", 1.0))
    assert isinstance(m.targets[1][1], float)
    assert m.elements == (
        ("Cc", (("engine", 0.0),)),
        ("I1", (("value", 2e-5),)),
        ("M8", (("off_l", 1e-6), ("off_w", 2e-6))),
        ("M9", (("triode", 0.0),)),
        ("R2", (("engine", 0.0), ("value", 1e5))),
    )                                                                       # Rx(값 None) 은 표시 없음


def _off(name, w, l):
    return RegionDecl(name, "off", None, ("gain_ss_db",), w, l)


def test_off_marks_split_pair_unless_declaration_equal():
    """짝 두 소자 중 하나만 off 면 표시가 갈리고(-> graph.orbits 에서 갈린다: tests/sizing/test_region_decl.py), 폭·길이가 같은 둘 다 off 면 표시가 같다
    (같은 궤도), 폭이나 길이가 다르면 다시 갈린다."""
    def elems(*regions):
        return dict(symmetry_marks(DcInputs((("vdd", 1.8),), regions=tuple(regions))).elements)
    one = elems(_off("Mb", 1e-6, 1e-6))
    assert "Ma" not in one and one["Mb"] == (("off_l", 1e-6), ("off_w", 1e-6))
    both = elems(_off("Ma", 1e-6, 1e-6), _off("Mb", 1e-6, 1e-6))
    assert both["Ma"] == both["Mb"]
    assert elems(_off("Ma", 2e-6, 1e-6), _off("Mb", 1e-6, 1e-6))["Ma"] != both["Mb"]
    assert elems(_off("Ma", 1e-6, 2e-6), _off("Mb", 1e-6, 1e-6))["Ma"] != both["Mb"]


def test_order_independent():
    a = DcInputs((("vdd", 1.8),), element_values=(("A", 1.0), ("B", 2.0)), node_targets=(("x", 0.5), ("y", 0.6)))
    b = DcInputs((("vdd", 1.8),), element_values=(("B", 2.0), ("A", 1.0)), node_targets=(("y", 0.6), ("x", 0.5)))
    assert symmetry_marks(a) == symmetry_marks(b)


def test_supplies_not_in_marks():
    """레일 전위는 대칭 블록이 supplies 에서 만든다 -- supplies 만 다른 두 입력의 표시는 같다."""
    assert symmetry_marks(DcInputs((("vdd", 1.8),))) == symmetry_marks(DcInputs((("vdd", 3.3),)))


def test_result_is_frozen_graph_type():
    m = symmetry_marks(DcInputs((("vdd", 1.8),), input_dc_v=0.9))
    assert isinstance(m, SymmetryMarks)
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.input_dc_v = 1.0  # type: ignore[misc]


@pytest.mark.parametrize("bad", [None, {"supplies_v": ()}, (("vdd", 1.8),)])
def test_non_dcinputs_rejected(bad):
    with pytest.raises(TypeError):
        symmetry_marks(bad)
