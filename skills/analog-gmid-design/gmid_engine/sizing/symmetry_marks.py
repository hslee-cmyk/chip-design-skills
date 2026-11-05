"""대칭 블록의 선언 표시 -- spec 선언(`DcInputs`)을 graph `SymmetryMarks` 로 옮긴다 (설계 40 §6-8 '원소 처음 색·노드 색의 선언 표시', sizing CONTRACT 3.0b).

진입점: `symmetry_marks(inputs) -> SymmetryMarks`.

* 원소 표시: 값 선언(`("value", 값)`, 저항 Ω·이상 전류원 A), engine 값 원소(`("engine", 0.0)`), `triode` 선언 소자(`("triode", 0.0)`), `off` 선언 소자(`("off_w", w_m)`,
  `("off_l", l_m)` -- 짝 두 소자 중 하나만 `off` 거나 폭·길이가 다르면 `graph.orbits` 에서 갈려 θ 가 묶이지 않는다. 같은 선언이면 같은 궤도).
* 노드 표시: 노드 목표 W3(`targets`), 입력 포트 공통 DC(`input_dc_v`). 레일 전위 표시는 graph 대칭 블록이 supplies 에서 직접 만든다.
* 단계 A(`build_s1(marks=)`)와 커널 컨텍스트(`s1_symmetry` 재호출 -- 같은 표시면 재사용)가 같은 함수로 만든다 -- 두 곳이 같은 그래프 하나를 본다(D-2).
"""
from gmid_engine.authoring import REGION_OFF
from gmid_engine.graph import SymmetryMarks

from .s2_values import DcInputs


def symmetry_marks(inputs):
    if not isinstance(inputs, DcInputs):
        raise TypeError("symmetry_marks: inputs 는 DcInputs 여야 한다")
    elements = {}
    for name, value in inputs.element_values:
        if value is not None:
            elements.setdefault(name, []).append(("value", float(value)))
    for name in inputs.engine_elements:
        elements.setdefault(name, []).append(("engine", 0.0))
    for r in inputs.regions:
        if r.region == REGION_OFF:
            elements.setdefault(r.device, []).extend((("off_l", float(r.l_m)), ("off_w", float(r.w_m))))
        else:
            elements.setdefault(r.device, []).append((r.region, 0.0))
    packed = tuple((n, tuple(sorted(marks))) for n, marks in sorted(elements.items()))
    targets = tuple(sorted((net, float(volts)) for net, volts in inputs.node_targets))
    return SymmetryMarks(None if inputs.input_dc_v is None else float(inputs.input_dc_v), packed, targets)
