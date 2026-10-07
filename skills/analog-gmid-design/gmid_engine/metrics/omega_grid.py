"""ω 격자 -- 상수 없이 계에서 유도 (설계 design_mod1_lut_mod5_mna 3.3 'ω 격자(`omega_grid.py`)').

진입점: `omega_grid`.

꺾임점 = 주어진 모든 `Roots` 의 유한 극점·영점 크기 |s| 중 양수인 것(정렬·중복 제거 -- 서로 1 ulp 안(다음 부동소수 이하)이면
같은 꺾임점, 작은 쪽을 남긴다). 격자 = 0(DC, 위상 언랩 시작점이라
'충분히 낮은 시작 주파수' 상수가 필요 없다) + 꺾임점 + 인접 꺾임점 사이 기하 중점. 꺾임점이 없으면 (0,) 뿐이다.
여러 계(루프 인수들)가 같은 격자를 공유하도록 Roots 를 여러 개 받는다. 위상 차 세분과 상단 괄호는 소비자
(`phase_lag`·`crossing`)가 실제 풀이로 한다.
"""
import math

from .mna_types import Roots


def omega_grid(roots_seq):
    """`Roots` tuple -> 오름차순 ω tuple(rad/s), 첫 원소 0.0."""
    if not isinstance(roots_seq, tuple) or not roots_seq:
        raise TypeError("omega_grid 는 비어 있지 않은 Roots tuple 을 받는다")
    breaks = set()
    for roots in roots_seq:
        if not isinstance(roots, Roots):
            raise TypeError("omega_grid: 원소는 Roots 여야 한다: %r" % (roots,))
        for z in roots.poles + tuple(z for row in roots.zeros for col in row for z in col):
            mag = abs(z)
            if mag > 0 and math.isfinite(mag):
                breaks.add(mag)
    # 1 ulp 안의 꺾임점은 하나로(작은 쪽): 같은 근이 노드 번호에 따라 1 ulp 다르게 계산돼 격자 점 수가 갈리지 않게 한다.
    ordered = []
    for mag in sorted(breaks):
        if not ordered or mag > math.nextafter(ordered[-1], math.inf):
            ordered.append(mag)
    grid = [0.0]
    for lo, hi in zip(ordered, ordered[1:]):
        grid.append(lo)
        grid.append(math.sqrt(lo * hi))
    if ordered:
        grid.append(ordered[-1])
    return tuple(sorted(set(grid)))
