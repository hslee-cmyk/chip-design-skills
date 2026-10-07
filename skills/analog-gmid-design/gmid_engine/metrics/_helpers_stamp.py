"""2단자 어드미턴스 스탬프 공용 helper (MOS 용량 스탬프와 수동소자 스탬프가 같은 식을 쓴다 -- 개념 하나 정의 하나).

공개 함수: `admittance_pair`(사용처: `stamp_mos.py`, `stamp_two_terminal.py`).
"""


def admittance_pair(a, b, value):
    """노드 a–b 사이 어드미턴스 `value` 의 (행, 열, 값) 4 항목."""
    return ((a, a, value), (a, b, -value), (b, a, -value), (b, b, value))
