"""평가 커널 호출 없이 레이아웃을 놓는다 -- 폭 키 좁히기와 완화 판정을 포함 (계획 N3.17 LY5·LY7, 설계 40 §3.9 U14).

진입점: `place_layout(memo, snapshot, pdk, passives, rejected, relaxed, first_seen, previous, kinds, current_keys) -> PlacedLayout`.

`snapshot` = 설계점(봉인 S2) 스냅샷 -- 레이아웃 필드는 그 위에 쓰인다(설계 40 v1.6 §2.4.7, 별도 lineage 없음). 레이아웃 결과는 `LayoutResult.snapshot` 의 `ly_*` 필드로 읽는다.

`run_layout` 을 부르고, 결과가 다음을 요구하는 동안 입력을 바꿔 다시 부른다(레이아웃 안 재시도는 기하 판정만 다시 한다 -- 평가 커널 0, WP-23 (3)):
1. **폭 키 좁히기** -- 한 kind 의 배치가 둘 이상의 폭 키를 쓰면(`kernel_keys.conflicts`) 평가 커널이 그 kind 에 슬라이스 하나만 쓰므로 그 kind 의 PDK 폭 키를 한 키로 좁힌다.
   어느 키로 좁힐지는 사용된 키마다 좁혀 다시 놓아 보고 `layout_score` 가 가장 작은 키를 고른다(동점은 작은 키). 좁힌 키 집합은 줄기만 한다.
2. **완화** -- `relaxation_decision` 이 정한 그룹을 완화 입력(`relaxed`)에 더한다. 더한 gid 는 한 번만 판정한다(`first_seen` 에 완화 전 `GroupLayout` 을 남긴다).
소자 하나라도 놓지 못하면(`unplaced`) 멈춘다. `previous` = **같은 설계점** 위 앞 호출의 `LayoutResult`(graph 필드 캐시 -- 레이아웃 재시도는 같은 설계점
lineage 의 새 스냅샷) 또는 None. 입력 인자는 바꾸지 않는다.
"""
import dataclasses

from gmid_engine.layout import F_GROUPS, LAYOUT_KEY, run_layout

from .convergence_values import PlacedLayout
from .effective_placement import effective_placement
from .kernel_keys import kernel_keys
from .layout_input import layout_input_of
from .layout_score import layout_score
from .relaxation import relaxation_decision


def _narrow(pdk, chosen):
    pick = dict(chosen)
    keys = tuple((kind, (pick[kind],) if kind in pick else tuple(ks)) for kind, ks in pdk.slice_width_keys)
    return dataclasses.replace(pdk, slice_width_keys=keys)


def place_layout(memo, snapshot, pdk, passives, rejected, relaxed, first_seen, previous, kinds, current_keys):
    relaxed = set(relaxed)
    first_seen = dict(first_seen)
    narrowed = {}
    calls = 0
    while True:
        layout_input, undelivered = layout_input_of(snapshot, pdk, passives, rejected, relaxed)
        layout = run_layout(layout_input, memo, snapshot, previous)
        calls += 1
        previous = layout
        placements, unplaced = effective_placement(layout.snapshot, pdk.manufacturing_grid_m)
        keys, conflicts = (), ()
        if not unplaced:
            keys, conflicts = kernel_keys(placements, kinds, current_keys)
        if conflicts:
            for kind, used in conflicts:
                scored = []
                for key in used:
                    trial_pdk = _narrow(pdk, ((kind, key),))
                    trial_input, _undelivered = layout_input_of(snapshot, trial_pdk, passives, rejected, relaxed)
                    trial = run_layout(trial_input, memo, snapshot, previous).snapshot
                    calls += 1
                    scored.append((layout_score(trial, effective_placement(trial, pdk.manufacturing_grid_m)[1]), key))
                chosen = min(scored)[1]
                narrowed[kind] = chosen
                pdk = _narrow(pdk, ((kind, chosen),))
            continue
        if not unplaced:
            relax, not_relaxable = relaxation_decision(layout.snapshot, relaxed)
            by_gid = {g.gid: g for g in layout.snapshot.value("graph", LAYOUT_KEY, F_GROUPS)}
            for gid in relax + not_relaxable:
                first_seen.setdefault(gid, by_gid[gid])
            if relax:
                relaxed.update(relax)
                continue
        return PlacedLayout(layout, undelivered, placements, unplaced, keys, pdk, frozenset(relaxed), first_seen,
                            calls, tuple(sorted(narrowed.items())))
