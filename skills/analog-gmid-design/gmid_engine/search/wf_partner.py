"""출발 W 의 짝 -- 비쓰기 멤버의 출발 W 에 밀도를 주는 쓰기 소자 판정 (FS-1, 계획 v6.39.5 DEC-108 (3), 설계 40 §3.7-B 3, interface card §3.3).

진입점: `start_partner(name, mos, position, gate, source, bulk, kind, length, writers, groups) -> str | None`.

짝 = KVL 짝 ∪ 대칭 짝, 둘 다 있으면 KVL 짝. 순수 함수, 저장 0.
* `mos` = 회로 MOS 이름 전부(칸·VGS 묶음으로 거르지 않는다), `position` = {이름: 정준 위치 int}(`device.dc_colour`), `gate`·`source`·`bulk`·`kind` = {이름: 넷/kind}(bulk = DEC-61 kind별 기본이 적용된
  실효 bulk 넷), `length` = {이름: 출발 L 값(5의 L)}, `writers` = 출발 단계가 ln IDu 좌표를 두는 쓰기 소자 집합, `groups` = ((role, members, status), ...).
* KVL 후보 = `name` 이 아니고 `writers` 에 들며 gate·source·bulk·kind 가 `name` 과 모두 같고 `length` 값이 `==` 로 같은 소자(같은 VGS·VSB·L 이면 단위 폭 전류 밀도가 같다).
* 대칭 후보(KVL 후보가 없을 때만) = role ∈ {diff_pair, branch_symmetric}, status ∈ {derived, ratified} 이고 `name` 이 든 묶음의 다른 쓰기 멤버(mirror 묶음은 대칭 짝을 주지 않는다).
* 후보가 여럿이면 `position` 최소. 고른 짝의 밀도가 정의되지 않아도 다른 짝으로 바꾸지 않는다(호출자가 why 를 그대로 낸다). 없으면 None.
"""
from gmid_engine.graph import MATCH_BRANCH_SYMMETRIC, MATCH_DIFF_PAIR

from .wf_start import CELL_STATUSES

SYMMETRIC_ROLES = (MATCH_DIFF_PAIR, MATCH_BRANCH_SYMMETRIC)


def start_partner(name, mos, position, gate, source, bulk, kind, length, writers, groups):
    kvl = [o for o in mos if o != name and o in writers and length[o] == length[name] and all(table[o] == table[name] for table in (gate, source, bulk, kind))]
    if kvl:
        return min(kvl, key=lambda o: position[o])
    symmetric = [o for role, members, status in groups if role in SYMMETRIC_ROLES and status in CELL_STATUSES and name in members
                 for o in members if o != name and o in writers]
    return min(symmetric, key=lambda o: position[o]) if symmetric else None
