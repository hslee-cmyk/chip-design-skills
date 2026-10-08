"""사이징 spec JSON(dict) 이름 치환: topology 이름 치환표를 spec 의 이름 자리에 같은 표로 적용한다.

이름 자리의 근거는 authoring SPEC_CONTRACT 1~3절(엔진 소스 아님):
- `meta.circuit`(= topology_name, `circuit_name_mismatch`), `meta.topology_fp`(= 치환한 topology 의 connectivity_fp,
  `topology_fp_mismatch` -- 지문은 엔진 공개 API 로 재는 값이라 호출자가 인자로 준다; 이 파일은 엔진을 import 하지 않는다).
- `human.supplies_v.values` 키(레일 넷), `human.input_dc.net`(mode net), `human.element_values` 키(수동소자·이상원 이름),
  `human.feedback.elements`(수동소자 이름).
- [2026-10-08 r10·r12, U5] `human.search.theta_bounds`·`human.search.untie_orbits` 키(원소 이름, SPEC_CONTRACT 1절 search 칸),
  `human.gain_budget_db_override[].block`(넷 이름 -- 사전순 엄격 증가가 계약이라 치환 뒤 다시 정렬한다),
  `human.noise_testbench.sampling_caps[].element`(커패시터 이름), 제약 `view` 의 `cm_sense_elements`(MOS 이름 list,
  SPEC_CONTRACT 3절 cm_loop -- 그 키 하나뿐인 닫힌 어휘).
- 이 helper 가 옮기지 못하는 이름 자리(`cm_sense_elements` 밖의 선언된 제약 view 의 넷, 선언된 `node_voltage_targets_v`·`intended_region` -- 형식이 이 계약
  요약에 다 적혀 있지 않다)가 있으면 조용히 두지 않고 `ValueError` 로 멈춘다. 결정 대기 표지(`{"pending": ID}`)와 `_` 주석 키는 이름이
  없으므로 그대로 둔다. `value_from_file` 참조는 다른 회로 파일 이름이라 이 회로의 치환표 밖이다(그대로).
"""
from __future__ import annotations

import copy

PENDING_KEY = "pending"
COMMENT_PREFIX = "_"
UNMAPPED_SECTIONS = ("node_voltage_targets_v", "intended_region")
SEARCH_ELEMENT_KEYED = ("theta_bounds", "untie_orbits")     # SPEC_CONTRACT 1절: 원소 이름이 키인 search 칸
CM_SENSE_KEY = "cm_sense_elements"                          # SPEC_CONTRACT 3절 cm_loop 선언 view(닫힌 어휘 키 하나)


def _declared_keys(section):
    return [k for k in section if not k.startswith(COMMENT_PREFIX) and k != PENDING_KEY]


def rename_spec(spec, mapping, topology_fp):
    """mapping 으로 이름을 바꾸고 meta.topology_fp 를 topology_fp 로 둔 새 spec dict(입력은 바꾸지 않는다)."""
    def fn(name):
        return mapping.get(name, name)

    out = copy.deepcopy(spec)
    out["meta"]["circuit"] = fn(spec["meta"]["circuit"])
    out["meta"]["topology_fp"] = topology_fp
    human = out["human"]
    supplies = human["supplies_v"]
    if "values" in supplies:
        supplies["values"] = {fn(k): v for k, v in supplies["values"].items()}
    if "net" in human["input_dc"]:
        human["input_dc"]["net"] = fn(human["input_dc"]["net"])
    human["element_values"] = {(k if k.startswith(COMMENT_PREFIX) else fn(k)): v
                               for k, v in human["element_values"].items()}
    if "elements" in human["feedback"]:
        human["feedback"]["elements"] = [fn(e) for e in human["feedback"]["elements"]]
    search = human.get("search", {})
    for key in SEARCH_ELEMENT_KEYED:
        if isinstance(search.get(key), dict):
            search[key] = {(k if k.startswith(COMMENT_PREFIX) else fn(k)): v for k, v in search[key].items()}
    for item in human.get("gain_budget_db_override", ()):
        item["block"] = sorted(fn(n) for n in item["block"])
    noise = human.get("noise_testbench")
    if isinstance(noise, dict):
        for cap in noise.get("sampling_caps", ()):
            cap["element"] = fn(cap["element"])
    for i, c in enumerate(human["constraints"]):
        view = c.get("view")
        if isinstance(view, dict) and _declared_keys(view) == [CM_SENSE_KEY]:
            view[CM_SENSE_KEY] = [fn(e) for e in view[CM_SENSE_KEY]]
        elif isinstance(view, dict) and _declared_keys(view):
            raise ValueError("rename_spec: constraints[%d] 에 선언 view 가 있다(넷 자리 치환 미지원)" % i)
    for key in UNMAPPED_SECTIONS:
        if _declared_keys(human[key]):
            raise ValueError("rename_spec: %s 에 선언 값이 있다(이름 자리 치환 미지원)" % key)
    return out
