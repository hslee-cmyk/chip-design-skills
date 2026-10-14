"""S1 스냅샷을 S1+S2 권한표(`S2_WRITERS`) 스냅샷으로 옮긴다 -- S0~S2 가 한 graph 에 산다 (확정 사항 1·2, 계획 N3.3).

진입점: `lift_s1(s1graph) -> GraphSnapshot`.

core `GraphSnapshot.widen(S2_WRITERS)`(권한표 확장 API `extend_writers`, sizing O7 -- 2026-10-08 사용자 승인)로 S1 스냅샷을 그대로
더 넓은 권한표(지금 표 ∪ `S2_WRITERS`) 아래로 옮긴다. S0 수준 스냅샷(권한표가 이미 S1·S1v 등을 덮는 것, 설계 40 §2.4.1)도 받는다. 그래서
* 값·writer·입력 버전·쓰기 횟수·`block_version` 이 S1 과 같고 레코드 객체를 공유한다(구조 공유) -- S1 계산 블록을 이 스냅샷에
  다시 부르면 재사용(계산 0)이다.
* 그 뒤 dc 계산 블록이 같은 스냅샷에 S2 필드를 더한다(필드마다 writer 하나 -- 권한표가 강제).
S0 당 1회(커널 컨텍스트 생성) 부른다. S1 writer 중 돌지 않은 것이 있으면 `ValueError`(build_s1 결과만 받는다).
"""
from gmid_engine.graph import S1_WRITERS, S1Graph

from .s2_values import S2_WRITERS


def lift_s1(s1graph):
    if not isinstance(s1graph, S1Graph) or not s1graph.snapshot.writers.covers(S1_WRITERS):
        raise TypeError("lift_s1: 권한표가 S1_WRITERS 를 덮는 S1Graph 여야 한다")
    source = s1graph.snapshot
    for writer in sorted({writer for _kind_field, writer in S1_WRITERS.entries}):
        if source.block_version(writer) is None:
            raise ValueError("lift_s1: S1 writer " + repr(writer) + " 가 돌지 않은 S1Graph 다(build_s1 결과만 받는다)")
    return source.widen(S2_WRITERS)
