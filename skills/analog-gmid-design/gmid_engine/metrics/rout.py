"""출력 저항 -- 같은 ω = 0 해의 전류 주입 열 (설계 design_mod1_lut_mod5_mna 3.4 `rout_ss_ohm`, DEC-66, 7a design 3.2).

진입점: `output_resistance`.

계 = 포트 전달 뷰 계(입력 포트 고정 0 V, 레일·gate 전용 넷 교류접지 -- DEC-66 '모든 여기원을 교류접지', 개루프). 그 계에
출력 포트 감지 노드 전류 주입 열 하나를 두고, 그 열의 DC 관측값 / I 를 낸다. 추가 분해 없음 -- `solve_responses` 의 DC
풀이(모든 열 한 번)를 읽는다. 열 조건: 전압 구동 진폭이 전부 0, 전하 주입 없음, 전류 주입은 관측 행 `row` 의 노드에만
(단일 관측: pos 에 I / 차동 관측: pos 에 +I, neg 에 −I).
DC 극한이 정의되지 않으면(용량 전용 노드 주입 등) 예외 없이 `rout_ohm=None` + `undefined`. 값이 음수(양되먹임 -- 정상
해에서는 생기지 않지만 탐색 후보에서 생길 수 있다)면 그대로 내지 않고 None + `negative_output_resistance`(definitional,
오케스트레이터 결정 2026-10-07, 7a design Q3) -- `rout_ss_ohm <= 값` 제약이 음수로 통과하지 않는다.
"""
import math

from .mna_types import OutputResistance, SystemResponse, Undefined


def _injection_amp(excitation, sense):
    if any(amp for _, amp in excitation.voltages) or excitation.charges:
        return None
    currents = dict(excitation.currents)
    if sense.neg is None:
        if set(currents) != {sense.pos}:
            return None
        return currents[sense.pos]
    if set(currents) != {sense.pos, sense.neg} or currents[sense.pos] != -currents[sense.neg]:
        return None
    return currents[sense.pos]


def output_resistance(response, column, row=0):
    """`SystemResponse`, 전류 주입 열 번호, 관측 행 번호 -> `OutputResistance`. 열 조건을 어기면 ValueError(뷰 정의 결함)."""
    if not isinstance(response, SystemResponse):
        raise TypeError("output_resistance 는 SystemResponse 를 받는다")
    system = response.system
    if not 0 <= column < len(system.excitations):
        raise ValueError("output_resistance: 열 %r 이 범위 밖이다" % (column,))
    if not 0 <= row < len(system.senses):
        raise ValueError("output_resistance: 관측 행 %r 이 범위 밖이다" % (row,))
    amp = _injection_amp(system.excitations[column], system.senses[row])
    if not amp:
        raise ValueError(
            "output_resistance: 열 %r 은 관측 노드 전류 주입 열이 아니다(구동 진폭 0, 관측 노드에만 주입)"
            % (system.excitations[column].name,)
        )
    value = float(response.dc[row, column])
    if math.isnan(value):
        causes = tuple(u for u in response.undefined if dict(u.detail).get("column", column) == column)
        cause = causes[0] if causes else Undefined("response", "response_not_finite", "numeric")
        return OutputResistance(
            column=column, rout_ohm=None, row=row,
            undefined=(Undefined("rout_ohm", cause.code, cause.category, cause.detail),),
        )
    rout = value / amp
    if rout < 0:
        return OutputResistance(
            column=column, rout_ohm=None, row=row,
            undefined=(Undefined("rout_ohm", "negative_output_resistance", "definitional", (("value_ohm", rout),)),),
        )
    return OutputResistance(column=column, rout_ohm=rout, row=row)
