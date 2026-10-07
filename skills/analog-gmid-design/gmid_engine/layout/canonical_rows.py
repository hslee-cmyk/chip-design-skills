"""MOD7 행 결과 정규화 `canonical_row` -- 복사 패턴 함수의 결정론 결함 보정(design_mod7_layout.md 7절 끝, NR 1.5).

복사본 `_hubleaf_sequence_node_path`(SD 265~290)는 시작 노드 후보를 `set` 으로 모아 순회하므로, 시작 노드를 두 개
이상 허용하는 finger 순서(예: 1 finger 단독, [A, A])에서는 node_sequence 가 PYTHONHASHSEED 에 따라 달라진다.
복사 본문을 고치면 AST 해시가 깨지므로(L10) 여기서 transistor_sequence 와 소자 연결(source·drain)만으로
node_sequence 를 다시 유도한다: 시작 노드 후보를 넷 이름 정렬 순서로 시도해 처음으로 끝까지 이어지는 walk 를 쓴다.

결과는 transistor_sequence·소자 연결의 함수다(입력 node_sequence·해시 시드·set 순회 순서와 무관). 시작 노드가 하나만
가능한 행에서는 원래 node_sequence 와 같다. crossover 로 나뉜 행은 segment 마다 따로 유도하고 행 node_sequence 는
segment node_sequence 를 이어 붙인다(복사본의 평탄화 규칙과 같다).
"""
from __future__ import annotations


def _walk(start, transistor_sequence, ends):
    """`start` 에서 출발해 finger 마다 그 소자의 다른 끝으로 건너가는 node 열. 막히면 None."""
    node = start
    path = [start]
    for name in transistor_sequence:
        source, drain = ends[name]
        if node == source:
            node = drain
        elif node == drain:
            node = source
        else:
            return None
        path.append(node)
    return path


def _canonical_nodes(transistor_sequence, ends):
    if not transistor_sequence:
        return []
    starts = sorted({net for name in transistor_sequence for net in ends[name]})
    for start in starts:
        path = _walk(start, transistor_sequence, ends)
        if path is not None:
            return path
    raise ValueError("finger 순서 %r 는 어떤 시작 노드로도 이어지는 walk 가 아니다(행 결과와 소자 연결 불일치)"
                     % (list(transistor_sequence),))


def canonical_row(seq_result, members):
    """행 결과 하나(`transistor_sequence`, 선택 `node_sequence`·`segments`·`crossover_after`)의 node_sequence 를
    정렬 규칙으로 다시 유도한 새 dict 를 돌려준다(입력은 바꾸지 않는다).

    `members`: 행에 나오는 소자들(`name`·`source`·`drain` 속성, 예: `Transistor`). 행에 나오는 이름이 `members` 에
    없으면 KeyError, 어떤 시작 노드로도 walk 가 안 되면 ValueError.
    `segments` 가 있으면 segment 마다 유도하고 행 `node_sequence` = segment node_sequence 이어 붙이기,
    없으면 `transistor_sequence` 전체를 한 walk 로 유도한다. 그 밖의 키는 그대로 옮긴다.
    """
    ends = {m.name: (m.source, m.drain) for m in members}
    out = dict(seq_result)
    segments = seq_result.get("segments")
    if segments:
        new_segments = []
        for seg in segments:
            new_seg = dict(seg)
            new_seg["transistor_sequence"] = list(seg["transistor_sequence"])
            new_seg["node_sequence"] = _canonical_nodes(seg["transistor_sequence"], ends)
            new_segments.append(new_seg)
        out["segments"] = new_segments
        out["node_sequence"] = [node for seg in new_segments for node in seg["node_sequence"]]
    else:
        out["node_sequence"] = _canonical_nodes(seq_result["transistor_sequence"], ends)
    out["transistor_sequence"] = list(seq_result["transistor_sequence"])
    return out
