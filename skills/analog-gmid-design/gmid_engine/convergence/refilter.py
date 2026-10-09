"""판정 축 재필터 -- (전력, 레이아웃 외곽 면적) 비지배 필터 (계획 DEC-79 '비지배 판정의 정본은 판정 축이다', DEC-95 (2), 설계 40 §3.9 MOD8 (4), U12 인계).

진입점: `refilter(points) -> (kept, dominated, folded)`.

`points` = 수렴한(`STATUS_CONVERGED`) `ConvergedPoint` 들. 탐색 축 필터와 같은 함수 `search.nondominated` 를 쓴다:
* 축 = (재검증 점의 `power_w`, 수렴 레이아웃의 `floorplan.outline_area_m2`), 둘 다 최소화. slack = 재검증 점의 활성 제약 여유 합.
* 동률 폭 = (전력: 두 점 전력 분해능 b_P 중 큰 값 -- 탐색 축 필터와 같다, 면적: `layout.area_tie_m2`(두 점 `FloorplanSummary`) = 제조 격자 x max(두 점 bbox 변 4개), DEC-79).
반환: `kept` = 남은 점 id(남기는 순서), `dominated` = ((id, 지배한 id), ...) id 순, `folded` = ((id, 대표 id), ...) id 순 -- 모든 축이 동률 폭 안이라 먼저 남은 점으로 접힌 점.
"""
from gmid_engine.layout import area_tie_m2
from gmid_engine.search import nondominated


def refilter(points):
    points = tuple(points)
    ids = tuple(p.point_id for p in points)
    plan = {p.point_id: p.layout.floorplan for p in points}
    power_tie = {p.point_id: p.power_resolution_w for p in points}
    entries = tuple((p.point_id, (p.power_w, p.layout_area_m2), sum(row.c for row in p.result.constraints if row.active))
                    for p in points)
    result = nondominated(entries, (lambda a, b: max(power_tie[a], power_tie[b]), lambda a, b: area_tie_m2(plan[a], plan[b])))
    kept = tuple(ids[i] for i in result.kept)
    dominated = tuple(sorted((ids[i], ids[k]) for i, k in result.dominated))
    folded = tuple(sorted((ids[i], ids[k]) for i, k in result.folded))
    return kept, dominated, folded
