"""봉인 4 버전 일치 (계획 N3.6 항목 4, SC-b, 설계 3.6 F7).

진입점: `seal_versions(snapshot, calls, base) -> SealItem`.

`calls` = 이번 평가에서 부른 dc 계산 블록과 그 추가 인자 ((ComputeBlock, extras tuple), ...). 블록마다
(1) 현재 스냅샷에서 다시 잰 입력 버전 `block.input_version(snapshot, *extras)`(입력 버전 정본 -- core `ComputeBlock`, 식 사본 없음) == `snapshot.block_version(이름)`(그 블록이 읽은
입력이 그 뒤 바뀌지 않았다 -- 낡은 입력으로 만든 하류 필드 없음), (2) 그 블록이 쓴 모든 필드의 `FieldValue.input_version`
== `block_version`(다른 경로로 섞인 필드 없음). 정확 일치. 위반 블록 이름을 `devices` 대신 detail `blocks` 에 남긴다.
스냅샷 파생 규칙(계획 N3.3, O-61 P1)의 단언 둘: (3) coverage -- 스냅샷 모든 필드의 writer ∈ base writer(`base.block_versions` 키) ∪ calls 블록 이름
(위반 detail `foreign_writers`), (4) 서로소 -- base writer ∩ calls 블록 이름 = ∅(위반 detail `base_call_overlap`). 항상 검사한다(`base` 필수, None 이면 `TypeError`).
메타데이터(입력 버전)를 읽어야 해서 계산 블록(투영은 값만 담는다)이 아니라 함수다.
"""
from .s2_values import SEAL_FAIL, SEAL_PASS, SEAL_VERSIONS, SealItem


def seal_versions(snapshot, calls, base):
    if base is None:
        raise TypeError("seal_versions: base 는 필수다(ctx.base)")
    stale = []
    for block, extras in calls:
        recorded = snapshot.block_version(block.name)
        if block.input_version(snapshot, *extras) != recorded:
            stale.append(block.name)
            continue
        for kind, field in block.writes:
            for key in snapshot.keys(kind):
                value = snapshot.field(kind, key, field)
                if value is not None and value.input_version != recorded:
                    stale.append(block.name)
                    break
    stale = tuple(sorted(set(stale)))
    base_writers = set(base.block_versions)
    called = {block.name for block, _extras in calls}
    overlap = tuple(sorted(base_writers & called))
    used = {fv.writer for records in snapshot.tables.values() for record in records.values() for _name, fv in record.fields}
    foreign = tuple(sorted(used - base_writers - called))
    status = SEAL_FAIL if stale or foreign or overlap else SEAL_PASS
    return SealItem(SEAL_VERSIONS, status, len(stale) + len(foreign) + len(overlap), 0, None, (), (),
                    (("blocks", stale), ("n_checked", len(calls)))
                    + (("foreign_writers", foreign),) * bool(foreign)           # 위반 이름은 위반일 때만 detail 에 더한다(설계 41 4.7-3c)
                    + (("base_call_overlap", overlap),) * bool(overlap))
