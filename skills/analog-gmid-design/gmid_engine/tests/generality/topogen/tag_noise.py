"""태그·주석 잡음: 로더가 읽지 않는 키에 무작위 값을 넣는다(authoring CONTRACT 머리 '태그 키는 읽지 않는다', 2절 불변식
"`_` 주석 키를 바꾸거나 더해도 같다. 태그 키 4개를 통째로 지워도 같다", 계획 IC4·U-50).

- 최상위 태그 키 4개(device_roles·symmetry·sizing_roles·compensation, CONTRACT 3.2 IGNORED_TAG_KEYS)를 무작위 내용으로
  채운다. device_roles 의 소자별 값에는 계획 U-50·IC4 의 역할 키(fold_group·headroom_role·gm_id_role·L_role·
  vertical_stack_id)를 무작위 값으로 넣는다 -- 역할 라벨이 엉터리여도 결과가 같아야 한다.
- `_` 주석 키를 최상위·원소·포트 선언에 더한다.
"""
from __future__ import annotations

import random

from ._doc_walk import ELEMENT_LISTS

ROLE_KEYS = ("fold_group", "headroom_role", "gm_id_role", "L_role", "vertical_stack_id")
ROLE_WORDS = ("tail", "input", "load", "cascode", "mirror", "bias", "none")


def add_tag_noise(doc, seed):
    """잡음을 더한 새 doc."""
    rng = random.Random(seed)
    out = dict(doc)
    names = [e["name"] for e in doc["netlist"]]
    out["device_roles"] = {n: {k: rng.choice(ROLE_WORDS) + str(rng.randint(0, 9)) for k in ROLE_KEYS if rng.random() < 0.8}
                           for n in names}
    pairs = [sorted(rng.sample(names, 2))] if len(names) >= 2 else []
    out["symmetry"] = {"matching_pairs": pairs, "_comment": "noise %d" % rng.randint(0, 999)}
    out["sizing_roles"] = [rng.random(), "noise", None]
    out["compensation"] = {"stage_devices": rng.sample(names, len(names)), "anything": rng.randint(0, 99)}
    out["_note"] = "noise %d" % rng.randint(0, 9999)
    for key in ELEMENT_LISTS:
        if key in doc:
            out[key] = [dict(e, _comment="noise %d" % rng.randint(0, 99)) for e in doc[key]]
    out["ports"] = {k: (dict(v, _comment="noise") if isinstance(v, dict) else v) for k, v in doc["ports"].items()}
    out["ports"]["_comment"] = "noise port comment"
    return out
