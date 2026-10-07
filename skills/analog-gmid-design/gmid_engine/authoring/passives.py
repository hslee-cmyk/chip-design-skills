"""수동소자 선언 접근자 `passive_elements` (설계 design_mod3_s1_graph 2.1 `passives.py`, J9·CI-12 기본안).

진입점: `passive_declaration(doc) -> tuple[PassiveDecl]` (이름순).

거부(모두 모아 `SchemaRejectedError` 한 번, detail `gate="passives"`):
* `missing_key` -- 최상위 `passive_elements` 키가 없다. **CI-12 기본안(사용자 결정 대기)**: 키가 없는 것을 `[]` 로 읽으면
  '수동소자 없음'이라는 회로 사실을 엔진이 지어내는 셈이라 거부한다. `[]` 는 '없음'을 명시한 선언으로 받는다.
* 원소 규칙은 `_two_terminal.two_terminal_elements`(`passive_elements_type`·`element_type`·`element_unknown_key`·
  `element_field`·`terminals`·`element_value`).
값 필드 = `VALUE_KEYS`(null 이면 미선언). `IGNORED_KEYS`(`value_from_spec` = spec 값 연결, `nulling_reference_device` =
역할 태그)는 허용하되 읽지 않는다. kind 는 제한하지 않는다(resistor·capacitor 밖 kind 는 graph 가 기록만, DEC-59).
"""
from ._rejection import reject, require_object
from ._two_terminal import two_terminal_elements
from .topology_model import PassiveDecl, SchemaHit

PASSIVE_KEY = "passive_elements"
VALUE_KEYS = ("value_ohm", "value_farad")
IGNORED_KEYS = ("value_from_spec", "nulling_reference_device")


def passive_declaration(doc):
    require_object("passives", doc)
    if PASSIVE_KEY not in doc:
        reject("passives", PASSIVE_KEY, (SchemaHit(
            "missing_key", PASSIVE_KEY,
            "최상위 passive_elements 가 없다 -- 수동소자가 없으면 [] 로 명시한다(키 없음을 '없음'으로 읽지 않는다, CI-12)"),))
    elements, hits = two_terminal_elements(doc[PASSIVE_KEY], PASSIVE_KEY, VALUE_KEYS, IGNORED_KEYS, PassiveDecl)
    if hits:
        reject("passives", PASSIVE_KEY, hits)
    return elements
