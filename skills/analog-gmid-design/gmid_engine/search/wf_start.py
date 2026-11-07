"""출발 w_f 칸 -- 정합 묶음 폐포 칸과 칸 출발 슬라이스 선택 (FS-1, 계획 DEC-108 (2)(3), 설계 40 §3.7-B 2·3, 41 §6.1 5a, interface card §3.2).

진입점: `wf_start_value(groups, mos, position, kinds, start_w, candidates, defined, reference, l_defined, *, grid_m) -> (tuple[WfCell], tuple[(코드, 상세 dict)])`
-- 출발 블록(`start_intervals`)이 부르는 유일한 칸 계산이다(칸 폐포 구현 하나; 부르는 곳이 출발 블록 밖이면 둘째 계산 자리). 기록 상세는 dict(출발 블록이 graph 에 둘 때 쌍 tuple 로 바꾼다).

* `groups` = ((role, members, status), ...)(`graph.matching_groups` 의 `kind`·`members`·`status`), `mos` = MOS 이름, `position` = {이름: 정준 위치 int}(`device.dc_colour`), `kinds` = {이름: kind},
  `start_w` = {이름: 멤버 출발 W(float) 또는 why 문자열(`reference_slice_undefined`·`no_member_density`·`no_partner`)}, `candidates` = {kind: 후보 슬라이스 키 오름차순}(`widths`),
  `defined(name, key)` = 그 멤버의 출발점 조회가 그 슬라이스에서 정의되는가(전압 판정 포함), `reference` = {kind: LUT 선언 기준 폭 슬라이스 키}, `l_defined(name, key)` = 그 멤버의 출발 L 이 그 슬라이스의
  L 위치 판정(앵커이거나 같은 bin 안 두 앵커 사이)을 통과하는가(전압 인자 없음), `grid_m` = 제조 격자.
* **짝 없는 단일 멤버 칸**: 멤버가 하나(X)이고 `start_w[X]` 가 `no_partner` 이면 r = `reference[kind]`; r 가 후보 안이고 `l_defined(X, r)` 이면 칸 키 = r(W 기준 선택·`defined` 를 거치지 않는다) + 기록
  `wf_start_reference`; 아니면 None + why `reference_start_undefined`. 다멤버 칸의 `no_partner` 는 why `no_member_partner`(출발 불능, 기준 폭 대체 0). 전류 없음(`no_member_density`)은 기준 폭이 아니다.
* **칸**: role ∈ {mirror, diff_pair, branch_symmetric} 이고 status ∈ {derived, ratified} 인 묶음을 소자 공유로 합집합한 성분 하나 = 칸 하나, 묶음 밖 MOS 는 자기 칸.
  칸 멤버 = `position` 오름차순, 칸 목록 = 첫 멤버 `position` 오름차순(이름 무관). 한 칸에 kind 가 둘 이상이면 `StructureUnresolvedError`(`wf_cell_kind_mixed`).
* **선택**(칸마다): 멤버 `start_w` 에 why 문자열이 있으면 그 칸 `w_key` = None(첫 why). 아니면 W_c = 멤버 출발 W 최솟값, 후보 중 모든 멤버가 정의인 것에서
  (i) `키·grid_m <= W_c` 인 가장 큰 키 (ii) 없으면 가장 작은 키 (iii) 모든 후보가 정의 불능이면 None(`no_defined_candidate`). None 칸마다 기록 `("wf_start_undefined", {members, why})`.
"""
from gmid_engine.core import StructureUnresolvedError
from gmid_engine.graph import MATCH_BRANCH_SYMMETRIC, MATCH_DIFF_PAIR, MATCH_MIRROR, STATUS_DERIVED, STATUS_RATIFIED
from gmid_engine.sizing import WfCell

from .wf_member_w import WHY_NO_PARTNER

CELL_ROLES = (MATCH_MIRROR, MATCH_DIFF_PAIR, MATCH_BRANCH_SYMMETRIC)      # 칸을 만드는 묶음 kind·status -- 정의 하나(짝 판정 `start_partner` 도 이 status 상수를 읽는다)
CELL_STATUSES = (STATUS_DERIVED, STATUS_RATIFIED)
WHY_NO_DEFINED_CANDIDATE = "no_defined_candidate"
WHY_REFERENCE_START_UNDEFINED = "reference_start_undefined"
WHY_NO_MEMBER_PARTNER = "no_member_partner"
RECORD_START_UNDEFINED = "wf_start_undefined"
RECORD_START_REFERENCE = "wf_start_reference"       # 출력 전용 기록(소비자 = 계획 M-FS1·N6.43 완료 (8) (b))
REASON_CELL_KIND_MIXED = "wf_cell_kind_mixed"


def wf_start_value(groups, mos, position, kinds, start_w, candidates, defined, reference, l_defined, *, grid_m):
    parent = {m: m for m in mos}            # 소자 공유 합집합 폐포(union-find)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for role, members, status in groups:
        if role not in CELL_ROLES or status not in CELL_STATUSES:
            continue
        inside = [m for m in members if m in parent]
        for other in inside[1:]:
            parent[find(other)] = find(inside[0])
    by_root = {}
    for m in mos:
        by_root.setdefault(find(m), []).append(m)
    ordered = sorted((tuple(sorted(members, key=lambda m: position[m])) for members in by_root.values()), key=lambda members: position[members[0]])
    cells, records = [], []
    for members in ordered:
        if len({kinds[m] for m in members}) > 1:
            raise StructureUnresolvedError(detail={"reason": REASON_CELL_KIND_MIXED, "members": members, "field": "matching_groups"})
        whys = [start_w[m] for m in members if isinstance(start_w[m], str)]
        key, why = None, whys[0] if whys else None
        if len(members) == 1 and why == WHY_NO_PARTNER:
            ref = reference[kinds[members[0]]]
            if ref in candidates[kinds[members[0]]] and l_defined(members[0], ref):
                key, why = ref, None
                records.append((RECORD_START_REFERENCE, {"members": members, "w_key": ref}))
            else:
                why = WHY_REFERENCE_START_UNDEFINED
        elif why == WHY_NO_PARTNER:
            why = WHY_NO_MEMBER_PARTNER
        elif not whys:
            w_c = min(start_w[m] for m in members)
            usable = [k for k in candidates[kinds[members[0]]] if all(defined(m, k) for m in members)]
            below = [k for k in usable if k * grid_m <= w_c]
            key = max(below) if below else (min(usable) if usable else None)
            why = None if key is not None else WHY_NO_DEFINED_CANDIDATE
        cells.append(WfCell(members, key))
        if key is None:
            records.append((RECORD_START_UNDEFINED, {"members": members, "why": why}))
    return tuple(cells), tuple(records)
