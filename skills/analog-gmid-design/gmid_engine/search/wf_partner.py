"""종속 멤버의 KVL 짝 -- 출발 w_f 칸 멤버 출발 W 에 쓰는 같은 VGS 짝 쓰기 멤버 판정 (FS-1, 계획 DEC-108 (3), 설계 40 §3.7-B 3, interface card §3.3).

진입점: `kvl_partner(name, cell, gate, source, bulk, kind, writers) -> str | None`.

`cell` = 칸 멤버 tuple(정준 순), `gate`·`source`·`bulk`·`kind` = {이름: 넷/kind}(bulk = DEC-61 kind별 기본이 적용된 실효 bulk 넷), `writers` = 출발 단계가 ln IDu 좌표를 두는 멤버 집합.
답 = `cell` 안에서 `name` 이 아니고 `writers` 에 들고 gate·source·bulk·kind 가 `name` 과 모두 같은 멤버 가운데 칸 순서 첫 것, 없으면 None(gate 만 공유하고 source 가 다른 멤버,
선언 bulk 가 다른 멤버 -- 같은 VGS·VSB 라는 물리 등식이 서지 않아 짝이 아니다). 차동쌍·가지 대칭의 대칭 짝은 이 함수가 아니라 출발 블록이 묶음 상대를 직접 준다.
"""


def kvl_partner(name, cell, gate, source, bulk, kind, writers):
    for other in cell:
        if other != name and other in writers and all(table[other] == table[name] for table in (gate, source, bulk, kind)):
            return other
    return None
