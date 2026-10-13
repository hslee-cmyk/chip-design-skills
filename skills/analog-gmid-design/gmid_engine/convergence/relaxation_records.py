"""완화 판정 기록 (계획 N3.17 LY5 '완화는 relaxed 와 시도 기록을 남긴다 -- 조용한 완화 금지', 설계 40 §3.9 U14).

진입점: `relaxation_records(first_seen, final_layout, relaxed) -> tuple[Relaxation]`.

* `first_seen` = {gid: 완화 판정 시점의 `GroupLayout`} -- 완화 전 role·사유(`reason`)·시도 기록(`attempts`).
* `final_layout` = 수렴(또는 마지막) `LayoutResult`(그룹은 그 스냅샷의 `ly_groups` 필드), `relaxed` = 실제로 완화 입력으로 바꾼 gid 집합.
gid 순 `Relaxation`: 완화한 그룹은 최종 레이아웃의 같은 gid 그룹(role 이 `mirror` 로 바뀐 것)이 패턴을 가졌으면 `RELAX_PLACED`(dx·dy·ok 기록), 못 놓았으면
`RELAX_NOT_PLACED`; 완화하지 못한 그룹은 `RELAX_NOT_AVAILABLE`(배치 없음).
"""
from gmid_engine.layout import F_GROUPS, LAYOUT_KEY

from .convergence_values import RELAX_NOT_AVAILABLE, RELAX_NOT_PLACED, RELAX_PLACED, Relaxation


def relaxation_records(first_seen, final_layout, relaxed):
    final = {g.gid: g for g in final_layout.snapshot.value("graph", LAYOUT_KEY, F_GROUPS)}
    out = []
    for gid in sorted(first_seen):
        before = first_seen[gid]
        if gid not in relaxed:
            out.append(Relaxation(gid, before.role, before.members, before.reason, before.attempts, RELAX_NOT_AVAILABLE,
                                  None, None, None, False))
            continue
        after = final.get(gid)
        placed = after is not None and after.pattern is not None
        out.append(Relaxation(gid, before.role, before.members, before.reason, before.attempts,
                              RELAX_PLACED if placed else RELAX_NOT_PLACED, after.pattern if placed else None,
                              after.dx if placed else None, after.dy if placed else None, bool(placed and after.ok)))
    return tuple(out)
