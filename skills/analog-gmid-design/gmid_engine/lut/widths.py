"""finger_w 후보 폭 집합 -- PDK 특성화 폭 슬라이스 중 최소 finger 폭 이상 (설계 MOD1 2.2, 확정 사항 6 E5).

진입점: `widths`.

폭 사이 보간·근접 폭 대체는 없다(bin 불연속, LCS 4절). 최대 폭 상수도 없다(슬라이스 최대 폭이 곧 상한).
"""


def widths(lut, kind):
    """`kind` 슬라이스의 폭 키(정수, 단위 = 제조 격자) 중 `w_key * grid >= 최소 finger 폭` 인 것의 오름차순 tuple.

    `kind` 의 최소 finger 폭이 `lut.spec.min_finger_w_m` 에 없으면 `KeyError`(선언 누락).
    """
    w_min = dict(lut.spec.min_finger_w_m)[kind]
    grid = lut.spec.manufacturing_grid_m
    return tuple(sorted(w_key for (k, w_key) in lut.slice_map if k == kind and w_key * grid >= w_min))
