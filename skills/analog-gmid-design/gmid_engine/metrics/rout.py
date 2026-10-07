"""출력 저항 -- 같은 ω = 0 해의 전류 주입 열 (설계 design_mod1_lut_mod5_mna 3.4 `rout_ss_ohm`, DEC-66).

진입점: `output_resistance`.

여기원 전부 교류접지(그 열의 구동 진폭 0), 출력 포트에 전류 I 를 주입한 열의 DC 관측값 / I. 추가 분해 없음 --
`solve_responses` 의 DC 풀이(모든 열 한 번)를 읽는다. 열 조건: 전압 구동 진폭이 전부 0, 전류 주입은 관측 노드에만
(단일 관측: pos 에 I / 차동 관측: pos 에 +I, neg 에 −I). 부호는 그대로 낸다(음수면 그대로 보고).
"""
from .mna_types import OutputResistance, SystemResponse


def _injection_amp(excitation, sense):
    if any(amp for _, amp in excitation.voltages):
        return None
    currents = dict(excitation.currents)
    if sense.neg is None:
        if set(currents) != {sense.pos}:
            return None
        return currents[sense.pos]
    if set(currents) != {sense.pos, sense.neg} or currents[sense.pos] != -currents[sense.neg]:
        return None
    return currents[sense.pos]


def output_resistance(response, column):
    """`SystemResponse`, 전류 주입 열 번호 -> `OutputResistance`. 열 조건을 어기면 ValueError(뷰 정의 결함)."""
    if not isinstance(response, SystemResponse):
        raise TypeError("output_resistance 는 SystemResponse 를 받는다")
    system = response.system
    if not 0 <= column < len(system.excitations):
        raise ValueError("output_resistance: 열 %r 이 범위 밖이다" % (column,))
    amp = _injection_amp(system.excitations[column], system.sense)
    if not amp:
        raise ValueError(
            "output_resistance: 열 %r 은 관측 노드 전류 주입 열이 아니다(구동 진폭 0, 관측 노드에만 주입)"
            % (system.excitations[column].name,)
        )
    return OutputResistance(column=column, rout_ss_ohm=float(response.dc[column]) / amp)
