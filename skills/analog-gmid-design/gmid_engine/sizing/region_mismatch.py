"""영역 판정 거부 -- 선언과 실제 영역이 어긋나는가 (EO-1 범위 4, 설계 41 §4.8-1 표 'mismatch' 칸, 구조 규칙 A: 판정 함수 파일 분할).

진입점: `region_mismatch(judgment) -> bool`. 거부 판정은 이 함수 하나다(봉인 7·9 와 ss 층 관문이 같은 함수를 부른다).
declared·actual 만의 함수다: 선언 없음·triode 가 꺼짐·out_of_domain 이면 거부, 선언 없음이 triode 이면 거부, triode 선언이 saturation 이면 거부.
`unresolved`(VDSAT 열 없음)와 `not_judged`(off 선언)는 거부가 아니다.
"""
from .region_judge import (
    ACTUAL_CUTOFF,
    ACTUAL_OUT_OF_DOMAIN,
    ACTUAL_SATURATION,
    ACTUAL_TRIODE,
    DECLARED_TRIODE,
)


def region_mismatch(judgment):
    actual, declared = judgment.actual, judgment.declared
    if actual in (ACTUAL_CUTOFF, ACTUAL_OUT_OF_DOMAIN):
        return True
    if actual == ACTUAL_TRIODE:
        return declared != DECLARED_TRIODE
    if actual == ACTUAL_SATURATION:
        return declared == DECLARED_TRIODE
    return False
