"""교대 재실행 후보 선별 -- 판정 축 순위가 뒤집힐 수 있는 점 (계획 DEC-79 '순위가 뒤집힌 점에서는 MOD8 수렴 루프를 다시 돈다', 설계 40 §3.9 MOD8 (4)).

진입점: `admit_candidates(survivors, candidates) -> tuple[FrontPoint]`.

`survivors` = 지금 판정 축 front 에 남은 수렴 점(`ConvergedPoint`), `candidates` = 아직 레이아웃하지 않은 봉인 후보 `search.FrontPoint`(탐색 축에서 지배당해 front 밖이었던 점).
탐색 축에서 지배한 점의 면적이 레이아웃 뒤 커지면 그 점이 지배하던 후보가 판정 축에서 살아날 수 있다. 후보의 레이아웃 면적은 레이아웃 전에는 모르므로 **그 탐색 축 면적을 판정 축
면적의 대리값**으로 둔다: 후보를 (전력, 탐색 축 면적)으로, 남은 점을 (전력, 레이아웃 면적)으로 놓고 같은 비지배 필터를 돌려 거기서 살아남는 후보만 뽑는다(대리값은 추정 --
뽑힌 점은 실제로 레이아웃·재검증한 뒤 진짜 판정 축 값으로 다시 거른다). 동률 폭: 전력 = 두 점 b_P 중 큰 값, 면적 = 남은 점 floorplan 의 `area_tie_m2`(후보 쪽은 비교 상대 점의
floorplan 으로 갈음, 후보끼리는 남은 점 floorplan 자기 쌍 폭 중 최솟값 -- 후보에는 floorplan 이 없다. 작은 폭이 더 많은 후보를 뽑는다). 반환은 후보 입력 순서.
"""
from gmid_engine.layout import area_tie_m2
from gmid_engine.search import nondominated


def admit_candidates(survivors, candidates):
    survivors, candidates = tuple(survivors), tuple(candidates)
    if not candidates or not survivors:
        return ()
    plan = {p.point_id: p.layout.floorplan for p in survivors}
    power_tie = {p.point_id: p.power_resolution_w for p in survivors}
    power_tie.update((c.point_id, c.result.objectives.power_resolution_w) for c in candidates)

    finest = min(area_tie_m2(f, f) for f in plan.values())

    def area_tie(a, b):
        pa, pb = plan.get(a), plan.get(b)
        if pa is None and pb is None:
            return finest
        return area_tie_m2(pa or pb, pb or pa)

    entries = tuple((p.point_id, (p.power_w, p.layout_area_m2), sum(r.c for r in p.result.constraints if r.active)) for p in survivors)
    entries += tuple((c.point_id, (c.result.objectives.power_w, c.result.objectives.area_m2),
                      sum(r.c for r in c.result.constraints if r.active)) for c in candidates)
    result = nondominated(entries, (lambda a, b: max(power_tie[a], power_tie[b]), area_tie))
    alive = {entries[i][0] for i in result.kept}
    return tuple(c for c in candidates if c.point_id in alive)
