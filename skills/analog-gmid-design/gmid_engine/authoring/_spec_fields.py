"""authoring 공용 helper -- spec 로더 파일들이 같이 쓰는 필드 판정 (설계 design_spec_format 1.5·1.8).

* `at(where, key)`: 문서 위치 문자열 잇기(`human.constraints[2].view`).
* `is_pending(raw)` / `pending_decision(raw)`: 결정 대기 표지 `{"pending": <ID>}`(주석 `_` 키 밖에 `pending` 하나뿐인
  객체)인가 / 그 ID. ID 형식 검사는 `spec_schema` 한 곳.
* `finite_number(value)`: bool 이 아닌 유한 int·float 인가.
* `key_hits(obj, allowed, where, elements)`: 객체 키를 닫힌 어휘 `allowed` 로 검사해 위반 hit 를 낸다. `_` 접두 키는
  주석(읽지 않음). 어휘 밖 키는 옛 이름 표(1.8 (a))면 `legacy_name`, 회로 전용 키 표(1.8 (b))면
  `circuit_specific_key`, 그 밖이면 `unknown_key` -- 키 하나에 hit 하나.
* `value_slot(raw, where, is_reference, hits) -> (value, ref)`: 값 자리 `value` / `value_from_constraint` /
  `value_from_file` 중 정확히 하나(`value_and_ref`), 값은 유한 수(`type`), 참조는 비어 있지 않은 문자열(`type`)·옛 이름
  아님(`legacy_name`), 참조와 출처 kind reference 는 함께만(`ref_kind_mismatch`; `is_reference` 가 None 이면 출처가
  거부돼 보지 않음). `ref` = (참조 키, 문자열). 제약·보상 목표가 같이 쓴다.

옛 이름 표에서 library 원소·넷 이름과 글자가 같은 것(`CL`·`vdd`·`Voc_des`)은 뺐다(구조 규칙 E: 엔진 소스에 회로·
넷·소자 이름 문자열 금지). 그 키는 닫힌 어휘 밖이라 `unknown_key` 로 거부된다(거부 자체는 같고 규칙 이름만 다르다).
"""
import math
from types import MappingProxyType

from .topology_model import SchemaHit

COMMENT_PREFIX = "_"
PENDING_KEY = "pending"
REF_KEYS = ("value_from_constraint", "value_from_file")

# 설계 1.8 (a): N3.16 '흡수되는 옛 이름' + 이 형식이 대체한 계획 N3.15 이름(F9 `ports`, F2 `pending_7a`).
# [U5 2026-10-08] `input_dc_net`·`topology_hash`·`derived` 는 정본 이름(40 §3.1 개정)이라 표에서 뺐다 -- 거부하지 않는다.
# [U5] 정합 metric 옛 이름 `mismatch_sigma_mv`(소문자 mv)·`mirror_ratio_error_mv`·`mismatch_sigma_v` 를 더했다(40 §3.8-8, Q3):
# 새 이름은 `LEGACY_REPLACEMENT` 가 안내한다.
LEGACY_NAMES = frozenset((
    "supplies", "value_amp", "PM_target_deg", "PM", "GBW", "GBW_hz", "CL_farad", "IBias_amp", "same_as_device",
    "node_voltage_targets", "input_dc_v", "input_common_mode", "pm_deg", "gain_db", "dc_gain_db",
    "rout_ohm", "parasitic_pm_deg", "mismatch_sigma_mV", "mirror_ratio_error_mV", "power_uA",
    "ports", "pending_7a", "value_from_spec",
    "mismatch_sigma_mv", "mirror_ratio_error_mv", "mismatch_sigma_v", "mismatch_sigma_V",
))

# 옛 정합 metric 이름 -> 새 이름 안내(설계 40 §3.8-8). 거부 메시지에만 쓴다(판정은 `LEGACY_NAMES` 원소 여부).
LEGACY_REPLACEMENT = MappingProxyType({
    "mismatch_sigma_mv": "offset_in_sigma_mv (제약) 또는 구조 가드 offset_excess <= 값",
    "mirror_ratio_error_mv": "offset_sys_mv (value_from_constraint: offset_in_sigma_mv)",
    "mismatch_sigma_v": "offset_in_sigma_mv 와 mirror_ratio_sigma_pct (보고)",
    "mismatch_sigma_V": "offset_in_sigma_mv 와 mirror_ratio_sigma_pct (보고)",
    "mismatch_sigma_mV": "offset_in_sigma_mv (제약) 또는 구조 가드 offset_excess <= 값",
    "mirror_ratio_error_mV": "offset_sys_mv (value_from_constraint: offset_in_sigma_mv)",
})

# 설계 1.8 (b): 회로 전용 키(대원칙 2026-10-07 -- topology 종속 엔진 금지).
CIRCUIT_SPECIFIC_KEYS = frozenset((
    "compensation", "function", "parameters", "stage_devices", "shared_gm_id_groups", "vds_kvl_groups", "kg",
    "Z", "NDP", "f_slew", "t_lln", "t_settle_total", "omega_c", "stack_groups_override", "row_split", "stage_gain_min",
    "stage_objective", "stage_power_tolerance", "min_vds_by_role", "vth0_slope", "W_bounds", "L_min",
    "min_finger_w", "max_finger_w", "report_only", "minimize", "inherits", "spec_fn",
))


def _replacement_note(name):
    new = LEGACY_REPLACEMENT.get(name)
    return "" if new is None else " -> 새 이름: " + new


def at(where, key):
    """`where` 아래 `key`(문자열 키 또는 list 위치 int)의 문서 위치."""
    if isinstance(key, int):
        return where + "[" + str(key) + "]"
    return where + "." + key if where else key


def is_pending(raw):
    """결정 대기 표지인가: 객체이고 `_` 주석 밖 키가 정확히 `pending` 하나."""
    if not isinstance(raw, dict) or PENDING_KEY not in raw:
        return False
    return all(k == PENDING_KEY or k.startswith(COMMENT_PREFIX) for k in raw)


def pending_decision(raw):
    """결정 대기 표지의 결정 ID(형식 검사 전 원문)."""
    return raw[PENDING_KEY]


def finite_number(value):
    """bool 이 아닌 유한 int·float 인가."""
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def key_hits(obj, allowed, where, elements=()):
    """`obj` 의 `_` 밖 키 중 `allowed` 밖인 것마다 hit 하나(옛 이름 / 회로 전용 키 / 미지 키)."""
    hits = []
    for key in obj:
        if key.startswith(COMMENT_PREFIX) or key in allowed:
            continue
        place = at(where, key)
        if key in LEGACY_NAMES:
            hits.append(SchemaHit("legacy_name", place, "옛 이름 " + repr(key)
                                  + " -- 정본 이름만 받는다(N3.16·DEC-69, 설계 1.8 (a))" + _replacement_note(key), elements))
        elif key in CIRCUIT_SPECIFIC_KEYS:
            hits.append(SchemaHit("circuit_specific_key", place, "회로 전용 키 " + repr(key)
                                  + " -- 보상·제약은 일반 metric 과 구조 유도로만 표현한다(대원칙 2026-10-07, 설계 1.8 (b))",
                                  elements))
        else:
            hits.append(SchemaHit("unknown_key", place, "받지 않는 키 " + repr(key) + " (받는 키 "
                                  + repr(sorted(allowed)) + ", 주석이면 '_' 접두)", elements))
    return hits


def _legacy_value_hit(value, where):
    """참조 문자열 값 안의 옛 이름(N3.16 끝 문단 -- 값 안 이름도 검사). `value_from_file` 은 '<회로>#<이름>' 의 이름 부분도 본다."""
    if isinstance(value, str):
        for candidate in (value, value.partition("#")[2]):
            if candidate in LEGACY_NAMES:
                return SchemaHit("legacy_name", where, "참조 값 안의 옛 이름 " + repr(candidate) + " (N3.16)"
                                 + _replacement_note(candidate))
    return None


def value_slot(raw, where, is_reference, hits):
    """값 자리 하나를 읽는다. 위반은 `hits` 에 더하고 (value, ref) 를 돌려준다(위반이면 해당 칸 None)."""
    present = tuple(k for k in ("value",) + REF_KEYS if k in raw)
    value = ref = None
    if len(present) != 1:
        hits.append(SchemaHit("value_and_ref", where, "value / value_from_constraint / value_from_file 중 정확히 하나: "
                              + repr(present)))
    elif present[0] == "value":
        if not finite_number(raw["value"]):
            hits.append(SchemaHit("type", at(where, "value"), "value 는 유한 수여야 한다: " + repr(raw["value"])))
        else:
            value = float(raw["value"])
    else:
        ref = (present[0], raw[present[0]])
        if not isinstance(ref[1], str) or not ref[1]:
            hits.append(SchemaHit("type", at(where, present[0]), "참조는 비어 있지 않은 문자열이어야 한다: " + repr(ref[1])))
        else:
            legacy = _legacy_value_hit(ref[1], at(where, present[0]))
            if legacy is not None:
                hits.append(legacy)
    if is_reference is not None and len(present) == 1 and (ref is not None) != is_reference:
        hits.append(SchemaHit("ref_kind_mismatch", at(where, "source"),
                              "value_from_* 참조는 source.kind reference 와 함께만 쓴다(값이면 다른 kind)"))
    return value, ref
