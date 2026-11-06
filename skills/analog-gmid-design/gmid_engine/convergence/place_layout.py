"""평가 커널 호출 없이 레이아웃을 놓는다 -- 폭 키 좁히기와 완화 판정을 포함 (계획 N3.17 LY5·LY7, 설계 40 §3.9 U14).

진입점: `place_layout(memo, snapshot, pdk, passives, rejected, relaxed, first_seen, previous, kinds, excluded=(), *, donors, counters) -> PlacedLayout`
(`excluded` = ((행 그룹 rid, (뺀 폭 키, ...)), ...) -- `key_exclusion` 이 행 그룹 단위로 뺀 폭 후보, `layout_input_of` 로 그대로 넘긴다).
`donors`·`counters` = 필수 키워드(기본값 없음) -- `converge_point` 가 `sctx.dc` 에서 꺼내 넘기는 실행 하나의 블록 결과 색인·계수. `run_layout` 에 그대로 넘긴다.

`snapshot` = 설계점(봉인 S2) 스냅샷 -- 레이아웃 필드는 그 위에 쓰인다(설계 40 v1.6 §2.4.7, 별도 lineage 없음). 레이아웃 결과는 `LayoutResult.snapshot` 의 `ly_*` 필드로 읽는다.

`run_layout` 을 부르고, 결과가 다음을 요구하는 동안 입력을 바꿔 다시 부른다(레이아웃 안 재시도는 기하 판정만 다시 한다 -- 평가 커널 0, WP-23 (3)):
1. **완화** -- `relaxation_decision` 이 정한 그룹을 완화 입력(`relaxed`)에 더한다. 더한 gid 는 한 번만 판정한다(`first_seen` 에 완화 전 `GroupLayout` 을 남긴다).
소자 하나라도 놓지 못하면(`unplaced`) 멈춘다. `previous` = **같은 설계점** 위 앞 호출의 `LayoutResult`(graph 필드 캐시 -- 레이아웃 재시도는 같은 설계점
lineage 의 새 스냅샷) 또는 None. 입력 인자는 바꾸지 않는다.
"""
from gmid_engine.layout import F_GROUPS, LAYOUT_KEY, run_layout

from .convergence_values import PlacedLayout
from .effective_placement import effective_placement
from .layout_input import layout_input_of
from .relaxation import relaxation_decision


def place_layout(memo, snapshot, pdk, passives, rejected, relaxed, first_seen, previous, kinds, excluded=(), *, donors, counters):
    relaxed = set(relaxed)
    first_seen = dict(first_seen)
    calls = 0
    while True:
        layout_input, undelivered = layout_input_of(snapshot, pdk, passives, rejected, relaxed, excluded)
        layout = run_layout(layout_input, memo, snapshot, previous, donors=donors, counters=counters)
        calls += 1
        previous = layout
        placements, unplaced = effective_placement(layout.snapshot, pdk.manufacturing_grid_m)
        if not unplaced:
            relax, not_relaxable = relaxation_decision(layout.snapshot, relaxed)
            by_gid = {g.gid: g for g in layout.snapshot.value("graph", LAYOUT_KEY, F_GROUPS)}
            for gid in relax + not_relaxable:
                first_seen.setdefault(gid, by_gid[gid])
            if relax:
                relaxed.update(relax)
                continue
        return PlacedLayout(layout, undelivered, placements, unplaced, pdk, frozenset(relaxed), first_seen, calls)
