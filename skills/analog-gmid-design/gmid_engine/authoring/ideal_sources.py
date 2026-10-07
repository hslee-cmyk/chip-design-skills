"""이상원 선언 접근자 `ideal_sources` (설계 design_mod3_s1_graph 2.1 `ideal_sources.py`).

진입점: `source_declaration(doc) -> tuple[SourceDecl]` (이름순).

선택 키: 없으면 `()`. 있으면 원소 규칙은 `_two_terminal.two_terminal_elements`(`ideal_sources_type`·`element_type`·
`element_unknown_key`·`element_field`·`terminals`·`element_value`)이고, 걸린 곳을 모두 모아 `SchemaRejectedError` 한 번
(detail `gate="ideal_sources"`). 값 필드 = `VALUE_KEYS`. `IGNORED_KEYS`(`implementable`)는 허용하되 읽지 않는다.
kind 는 기록만 하고 판정은 graph 가 한다(전압원 등 지원 밖 kind 는 graph 의 unsupported 기록, DEC-76).
"""
from ._rejection import reject, require_object
from ._two_terminal import two_terminal_elements
from .topology_model import SourceDecl

SOURCE_KEY = "ideal_sources"
VALUE_KEYS = ("value_amp", "value_volt")
IGNORED_KEYS = ("implementable",)


def source_declaration(doc):
    require_object("ideal_sources", doc)
    if SOURCE_KEY not in doc:
        return ()
    elements, hits = two_terminal_elements(doc[SOURCE_KEY], SOURCE_KEY, VALUE_KEYS, IGNORED_KEYS, SourceDecl)
    if hits:
        reject("ideal_sources", SOURCE_KEY, hits)
    return elements
