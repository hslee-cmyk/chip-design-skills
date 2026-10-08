"""출력 구동 선언 `human.driving_spec` (설계 40 §3.1, §3.8-3 `ls`, 계획 DEC-58).

진입점: `driving_declaration(raw) -> (DrivingDecl | None, tuple[SchemaHit])`.

모양: `{"slew_rate_v_per_s"?: 수, "load_peak_amp"?: 수, "load_dc_amp"?: 수, "source": {...}}`. 키가 없으면(None) `None`.
* 값 칸 3개는 선택이지만 **하나 이상** 있어야 한다(`driving_spec_empty` -- 값 없는 선언은 제약 행을 만들 수 없다). 있는 칸은 양의
  유한 수(`type`). 부하 용량은 부하 요소 참조(N3.15)라 여기 두지 않는다.
* `source` 필수, kind `user_spec` 만. 그 밖 키는 `key_hits` 가 거부한다.
"""
from ._spec_fields import at, finite_number, key_hits
from .spec_model import DrivingDecl
from .spec_sources import source_declaration_checks
from .topology_model import SchemaHit

WHERE = "human.driving_spec"
SECTION = "driving_spec"
VALUE_KEYS = ("slew_rate_v_per_s", "load_peak_amp", "load_dc_amp")


def driving_declaration(raw):
    if raw is None:
        return None, ()
    if not isinstance(raw, dict):
        return None, (SchemaHit("type", WHERE, "driving_spec 은 객체여야 한다: " + type(raw).__name__),)
    hits = key_hits(raw, VALUE_KEYS + ("source",), WHERE)
    values = {}
    for key in VALUE_KEYS:
        if key not in raw:
            continue
        value = raw[key]
        if not finite_number(value) or value <= 0:
            hits.append(SchemaHit("type", at(WHERE, key), key + " 는 양의 유한 수여야 한다: " + repr(value)))
        else:
            values[key] = float(value)
    if not values and not hits:
        hits.append(SchemaHit("driving_spec_empty", WHERE, "값 칸 " + repr(VALUE_KEYS) + " 중 하나 이상을 선언해야 한다"))
    source, source_hits = source_declaration_checks(raw.get("source"), WHERE, SECTION)
    hits.extend(source_hits)
    if hits:
        return None, tuple(hits)
    return DrivingDecl(values.get(VALUE_KEYS[0]), values.get(VALUE_KEYS[1]), values.get(VALUE_KEYS[2]), source), ()
