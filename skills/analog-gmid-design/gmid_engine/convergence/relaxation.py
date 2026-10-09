"""LY5 완화 판정 -- W 조정이 불가능해 common-centroid 로 배치되지 못한 그룹 (계획 N3.17 LY5, 설계 40 §3.9 U14, U12 인계).

진입점: `relaxation_decision(layout, layout_input, relaxed) -> (relax, not_relaxable)`.

레이아웃은 즉시 완화하지 않는다(U12 -- `GroupLayout.pattern is None`). 시도 순서 (i) 같은 (ID, gm/ID, L) 에서 nf 조정 (ii) W_request 로 sizing 재평가를 거친 W 조정이
**둘 다** 불가능해야만 완화한다: 그룹이 common-centroid 를 요구하는 role(`CC_REQUIRED_ROLES` -- 차동쌍·branch_symmetric)이고, 배치가 없고(`pattern is None`), W_request 응답 대기가
아니다(`pending` 이면 아직 (ii) 중이다 -- 요청이 성립하거나 거부된 뒤에 다시 본다). 이 조건이 지금까지의 모든 시도(레이아웃 `attempts`)가 소진된 사유(조정 불가·요청 거부·사용
가능한 공통 폭 없음)를 한꺼번에 가리키므로 사유 문자열을 따로 읽지 않는다.

* `relax` = 완화할 gid 튜플(gid 순): hub 넷이 있는 그룹 -- 입력 role 을 일반 hub-leaf 쌍(`mirror`)으로, 허용 패턴을 interdigitation 만으로 바꿔 다시 놓는다(`layout_input_of`).
* `not_relaxable` = (gid 순) hub 가 없어 interdigitation 경로가 없는 그룹(branch_symmetric 은 hub 없는 쌍 -- 행 swap common-centroid 만): 배치 없이 `review_needed` 로 남긴다.
`relaxed` = 이미 완화한 gid 집합(다시 판정하지 않는다).
"""
from gmid_engine.layout import CC_REQUIRED_ROLES


def relaxation_decision(layout, layout_input, relaxed):
    hub = {g.gid: g.hub_net for g in layout_input.matching_groups}
    relax, not_relaxable = [], []
    for g in sorted(layout.groups, key=lambda x: x.gid):
        if g.role not in CC_REQUIRED_ROLES or g.pattern is not None or g.pending or g.gid in relaxed:
            continue
        (relax if hub.get(g.gid) is not None else not_relaxable).append(g.gid)
    return tuple(relax), tuple(not_relaxable)
