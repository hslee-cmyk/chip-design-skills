"""`linked_topology_files` 게이트 (설계 design_mod3_s1_graph 2.1 `linked_files.py`, DEC-76).

진입점: `check_linked_files(doc) -> tuple[SchemaHit]`.

키가 없거나 빈 list 면 통과한다. list 가 아니면 `linked_files_type`, 원소가 하나라도 있으면 `linked_files_unsupported`
로 거부한다: library 9회로의 발동이 0(빈 list 6·키 없음 3)이라 옛 여러 파일 합치기는 이식하지 않았고, 그 입력이 오면
조용히 진입 파일만 읽는 대신 거부한다(`unsupported_rule_branch` 와 같은 뜻의 안전망).
"""
from .topology_model import SchemaHit

LINKED_KEY = "linked_topology_files"


def check_linked_files(doc):
    if not isinstance(doc, dict) or LINKED_KEY not in doc:
        return ()
    linked = doc[LINKED_KEY]
    if not isinstance(linked, list):
        return (SchemaHit("linked_files_type", LINKED_KEY, LINKED_KEY + " 는 list 여야 한다: " + type(linked).__name__),)
    if linked:
        return (SchemaHit("linked_files_unsupported", LINKED_KEY,
                          "여러 파일 topology(" + LINKED_KEY + " 원소 " + str(len(linked))
                          + "개)는 아직 지원하지 않는다(DEC-76 -- 합치기 로직 미이식, 진입 파일만 읽지 않고 거부)",
                          tuple(x for x in linked if isinstance(x, str))),)
    return ()
