"""단계 A 계수 예산 N_S (설계 41 §0, 40 §10.1 `count_budget`).

진입점: `structure_count_budget(lut, kinds) -> int`.

N_S = 이 회로에 쓰이는 kind 들의 LUT 격자점 수 합 = Σ_kind Σ_(그 kind 의 폭 슬라이스) |L|·|VGS|·|VDS|·|VS|. 근거는 "상한 계산 한 번이 LUT 전체를 한 번
훑는 양을 넘지 않는다"이고 LUT 파일에서 정해지는 값이라 새 상수가 아니다. 시간과 무관해 같은 LUT·kind 면 늘 같다. spec `structure_count_budget` 선언은 U5 가
로더에 넣은 뒤 이 값을 대체한다. U9 `search/count_budget.py` 가 생기면 그쪽으로 옮긴다.
"""
import math


def structure_count_budget(lut, kinds):
    total = sum(math.prod(len(axis) for axis in s.grids) for (kind, _w_key), s in lut.slice_map.items() if kind in kinds)
    if total < 1:
        raise ValueError("structure_count_budget: 쓰는 kind " + repr(sorted(kinds)) + " 의 LUT 슬라이스가 없다")
    return total
