"""두 여기 열의 응답비 (설계 design_mod1_lut_mod5_mna 3.4 `ratio_ss_db` -- 옛 `smallsignal_ratio_db`, CMRR·PSRR 일반형,
DF-29·DF-30 회로 전용 metric 대체).

진입점: `response_ratio`.

같은 MnaSystem(같은 고정 노드 집합·같은 관측)의 두 열 num·den 의 ω = 0 극한 응답 크기비 20·log10|H_num(0)/H_den(0)|.
G·C 는 같고 우변 열만 다르므로 추가 분해가 없다(`solve_responses` 의 DC 해를 읽는다). 예외를 던지지 않는다:
분모 0 = `den_zero`, 분자 0 = `num_zero`(definitional), 열 극한 미정의는 그 사유.
"""
import math

from gmid_engine.core import AMPLITUDE_DB_PER_DECADE

from .mna_types import ResponseRatio, SystemResponse, Undefined


def _column_value(response, column):
    value = float(response.dc[column])
    if math.isnan(value):
        causes = tuple(u for u in response.undefined if dict(u.detail).get("column", column) == column)
        return None, causes[0] if causes else Undefined("response", "response_not_finite", "numeric")
    return value, None


def response_ratio(response, num_column, den_column):
    """`SystemResponse`, 분자 열, 분모 열 -> `ResponseRatio`."""
    if not isinstance(response, SystemResponse):
        raise TypeError("response_ratio 는 SystemResponse 를 받는다")
    m = len(response.system.excitations)
    if not (0 <= num_column < m and 0 <= den_column < m) or num_column == den_column:
        raise ValueError("response_ratio: 열 (%r, %r) 이 범위 밖이거나 같다" % (num_column, den_column))
    num, why_num = _column_value(response, num_column)
    den, why_den = _column_value(response, den_column)
    why = why_num or why_den
    if why is None and den == 0:
        why = Undefined("ratio_db", "den_zero", "definitional", (("column", den_column),))
    if why is None and num == 0:
        why = Undefined("ratio_db", "num_zero", "definitional", (("column", num_column),))
    if why is not None:
        return ResponseRatio(
            num_column=num_column, den_column=den_column, ratio_db=None,
            undefined=(Undefined("ratio_db", why.code, why.category, why.detail),),
        )
    return ResponseRatio(
        num_column=num_column, den_column=den_column,
        ratio_db=AMPLITUDE_DB_PER_DECADE * math.log10(abs(num / den)),
    )
