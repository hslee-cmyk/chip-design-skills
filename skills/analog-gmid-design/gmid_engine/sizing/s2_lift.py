"""S1 스냅샷을 S1+S2 권한표(`S2_WRITERS`) 스냅샷으로 옮긴다 -- S0~S2 가 한 graph 에 산다 (확정 사항 1·2, 계획 N3.3).

진입점: `lift_s1(s1graph) -> GraphSnapshot`.

S1 의 모든 필드를 core setter(`GraphSnapshot.write`)로만 같은 writer·같은 입력 버전으로 다시 쓴다. 그래서
* 값·writer·입력 버전(`block_version`)이 S1 과 같다 -- S1 계산 블록을 이 스냅샷에 다시 부르면 재사용(계산 0)이다.
* 그 뒤 dc 계산 블록이 같은 스냅샷에 S2 필드를 더한다(필드마다 writer 하나 -- 권한표가 강제).
S0 당 1회(커널 컨텍스트 생성) 부른다. 원시 생성(`GraphSnapshot(...)`) 은 core 계약상 쓰지 않는다 -- 그래서 레코드 객체는
S1Graph 쪽과 공유되지 않는다(열린 질문: core 에 권한표 확장 API 가 생기면 구조 공유로 바꾼다).
"""
from gmid_engine.core import GraphSnapshot
from gmid_engine.graph import S1_WRITERS, S1Graph

from .s2_values import S2_WRITERS


def lift_s1(s1graph):
    if not isinstance(s1graph, S1Graph) or s1graph.snapshot.writers != S1_WRITERS:
        raise TypeError("lift_s1: S1_WRITERS 권한표의 S1Graph 여야 한다")
    source = s1graph.snapshot
    snapshot = GraphSnapshot.empty(S2_WRITERS)
    writers = sorted({writer for _kind_field, writer in S1_WRITERS.entries})
    for writer in writers:
        version = source.block_version(writer)
        if version is None:
            raise ValueError("lift_s1: S1 writer " + repr(writer) + " 가 돌지 않은 S1Graph 다(build_s1 결과만 받는다)")
        columns = {(kind, field): dict(source.column(kind, field)) for kind, field in S1_WRITERS.fields_of(writer)}
        snapshot = snapshot.write(writer, version, columns)
    return snapshot
