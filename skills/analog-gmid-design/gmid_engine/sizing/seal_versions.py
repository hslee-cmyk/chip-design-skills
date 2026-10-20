"""봉인 4 버전 일치 (계획 N3.6 항목 4, SC-b, 설계 3.6 F7).

진입점: `seal_versions(snapshot, calls) -> SealItem`.

`calls` = 이번 평가에서 부른 dc 계산 블록과 그 추가 인자 ((ComputeBlock, extras tuple), ...). 블록마다
(1) 현재 스냅샷에서 다시 잰 입력 버전 `block.input_version(snapshot, *extras)`(입력 버전 정본 -- core `ComputeBlock`, 식 사본 없음) == `snapshot.block_version(이름)`(그 블록이 읽은
입력이 그 뒤 바뀌지 않았다 -- 낡은 입력으로 만든 하류 필드 없음), (2) 그 블록이 쓴 모든 필드의 `FieldValue.input_version`
== `block_version`(다른 경로로 섞인 필드 없음). 정확 일치. 위반 블록 이름을 `devices` 대신 detail `blocks` 에 남긴다.
메타데이터(입력 버전)를 읽어야 해서 계산 블록(투영은 값만 담는다)이 아니라 함수다.
"""
from .s2_values import SEAL_FAIL, SEAL_PASS, SEAL_VERSIONS, SealItem


def seal_versions(snapshot, calls):
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
    status = SEAL_FAIL if stale else SEAL_PASS
    return SealItem(SEAL_VERSIONS, status, len(stale), 0, None, (), (),
                    (("blocks", stale), ("n_checked", len(calls))))
