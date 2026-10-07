"""margin 정규화 -- 실패 크기를 그 클래스의 허용오차로 나눈 무차원 값 (계획 N3.14 'margin 정규화식', IC9, 설계 00-common §7.2).

진입점: `normalized_margin(magnitude, tol) -> float | None`. margin 을 계산하는 곳은 이 함수 하나다.
분모(tol_V·tol_I·분해능)의 선택은 부르는 쪽이 N3.14 정규화식대로 한다.
"""


def normalized_margin(magnitude, tol):
    """`tol` 이 None 이거나 0 이면 None(비교·정렬에 쓰지 않는 값), 아니면 `magnitude / tol`(float)."""
    if tol is None or tol == 0:
        return None
    return float(magnitude) / float(tol)
