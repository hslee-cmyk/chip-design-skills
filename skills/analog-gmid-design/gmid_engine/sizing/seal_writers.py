"""봉인 5 writer 유일 (계획 N3.6 항목 5, N3.4 '노드 하나에 writer 하나', SC-a, 설계 3.6).

진입점: `seal_writers(snapshot) -> SealItem`.

* 모든 필드의 `FieldValue.writer` == 권한표(`snapshot.writers`)가 그 (kind, field) 에 배정한 writer.
* 노드마다 쓰기 계획 writer(`dc_writer`)가 정확히 하나 있고, 레일 노드(S1 `is_rail`) <=> 티어 W0.
* 노드전압 값의 writer 가 하나: 레일은 `dc_rail_v` 만, 레일이 아닌 노드는 `dc_v` 만(둘 다 있거나 둘 다 없으면 위반).
런타임에는 계획과 실제 필드 writer 의 대조만 한다(계획 컴파일에서 이미 참이어야 하는 성질 -- 구현 결함 탐지용).
메타데이터를 읽어야 해서 함수다.
"""
from .s2_values import SEAL_FAIL, SEAL_PASS, SEAL_WRITER_UNIQUE, TIER_W0, SealItem


def seal_writers(snapshot):
    bad_fields = set()
    for kind in snapshot.kinds():
        for key in snapshot.keys(kind):
            record = snapshot.record(kind, key)
            for field in record.field_names():
                if record.get(field).writer != snapshot.writers.writer_of(kind, field):
                    bad_fields.add((kind, field))
    bad_nodes = []
    for net in snapshot.keys("node"):
        is_rail = snapshot.value("node", net, "is_rail")
        writer = snapshot.field("node", net, "dc_writer")
        has_rail = snapshot.field("node", net, "dc_rail_v") is not None
        has_v = snapshot.field("node", net, "dc_v") is not None
        if writer is None or (writer.value.tier == TIER_W0) != is_rail or has_rail == has_v or has_rail != is_rail:
            bad_nodes.append(net)
    status = SEAL_FAIL if bad_fields or bad_nodes else SEAL_PASS
    return SealItem(SEAL_WRITER_UNIQUE, status, len(bad_fields) + len(bad_nodes), 0, None, (), tuple(bad_nodes),
                    (("fields", tuple(sorted(bad_fields))), ("n_nodes", len(snapshot.keys("node")))))
