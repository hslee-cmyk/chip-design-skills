"""재필터와 MOD8 재실행 교대 횟수 상한 K_alt (계획 DEC-79·LR9 '교대 반복 상한은 N3.6 K_max 규칙을 그대로 쓴다', 설계 40 §3.9 (4)).

진입점: `alternation_bound(points) -> int`.

K_alt = sizing `k_max(구간폭, tol)`: 구간폭 = 수렴 점들의 판정 축 외곽 면적 범위 `max − min`(m²), tol = 두 점 사이 동률 폭 `area_tie_m2` 의 최솟값(레이아웃 해상도 -- 이보다 작은
면적 차는 순위를 가르지 못한다). 범위가 tol 이하이거나 점이 하나뿐이면 1(재실행 한 번 허용). 새 상수 없음.
"""
from gmid_engine.layout import F_FLOORPLAN, LAYOUT_KEY, area_tie_m2
from gmid_engine.sizing import k_max


def alternation_bound(points):
    points = tuple(points)
    if len(points) <= 1:
        return 1
    areas = [p.layout_area_m2 for p in points]
    width = max(areas) - min(areas)
    plan = [p.layout.snapshot.value("graph", LAYOUT_KEY, F_FLOORPLAN) for p in points]
    tol = min(area_tie_m2(a, b) for i, a in enumerate(plan) for b in plan[i + 1:])
    return 1 if width <= tol else k_max(width, tol)
