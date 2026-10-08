"""구조 계수 예산 선언 `human.structure_count_budget` (설계 40 §3.1, 41 §0 'N_S').

진입점: `count_budget_declaration(raw) -> (CountBudgetDecl | None, tuple[SchemaHit])`.

모양: `{"value": 양의 정수, "source": {...}}`. 키가 없으면(None) `None` -- 소비자(41 §0)가 LUT 격자에서 유도한 기본값을 쓴다.
`value` 는 bool 이 아닌 양의 정수(`type`; 실수는 정수값이어도 거부 -- 계수는 세는 값이다). `source` 필수, kind `user_spec` 만.
선언된 값은 S0 지문(`count_budget_fp`)에 들어간다.
"""
from ._spec_fields import at, key_hits
from .spec_model import CountBudgetDecl
from .spec_sources import source_declaration_checks
from .topology_model import SchemaHit

WHERE = "human.structure_count_budget"
SECTION = "structure_count_budget"


def count_budget_declaration(raw):
    if raw is None:
        return None, ()
    if not isinstance(raw, dict):
        return None, (SchemaHit("type", WHERE, "structure_count_budget 은 {value, source} 객체여야 한다: " + type(raw).__name__),)
    hits = key_hits(raw, ("value", "source"), WHERE)
    value = raw.get("value")
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        hits.append(SchemaHit("type", at(WHERE, "value"), "value 는 양의 정수여야 한다: " + repr(value)))
    source, source_hits = source_declaration_checks(raw.get("source"), WHERE, SECTION)
    hits.extend(source_hits)
    if hits:
        return None, tuple(hits)
    return CountBudgetDecl(value, source), ()
