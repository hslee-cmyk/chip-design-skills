"""metamorphic: 위반 검출이 이름·순서·극성·회로 크기와 무관하다.

각 합성 회로를 변형(그대로, 무작위 이름 치환 2벌, 순서 섞기, 극성 뒤집기, 단 복제, 태그 잡음)한 뒤 위반 하나를 주입하면
로드는 그 위반 **하나만** 낸다(rule 목록 == [기대 rule]). 기대 hit 은 주입기가 계약(authoring CONTRACT 3.4·3.8·3.9·3.11)에서
정한 것 -- 피검 함수 출력이 아니다. elements 는 계약이 정확히 정한 종류(hidden_rail·name_case_collision)는 같음, 그 밖은 포함.
또 주입 뒤 이름을 치환하면 hit 의 elements 가 같은 치환표로 옮겨진다(위반이 '이름'이 아니라 '구조'에 붙어 있다).
"""
from __future__ import annotations

import pytest

from .topogen import (
    VIOLATION_KINDS,
    add_tag_noise,
    duplicate_stage,
    flip_polarity,
    inject_violation,
    random_renaming,
    rename,
    shuffle_order,
    synthetic_topologies,
)

CIRCUITS = sorted(synthetic_topologies())


def _variant(doc, how):
    if how == "identity":
        return doc
    if how.startswith("rename"):
        seed = int(how[len("rename"):])
        return rename(doc, random_renaming(doc, seed))
    if how == "shuffle":
        return shuffle_order(doc, 7)
    if how == "flip":
        return flip_polarity(doc)[0]
    if how == "duplicate":
        return duplicate_stage(doc, "_s2")[0]
    if how == "tag_noise":
        return add_tag_noise(doc, 3)
    raise ValueError(how)


VARIANTS = ("identity", "rename0", "rename1", "shuffle", "flip", "duplicate", "tag_noise")


def _check(detail, expected):
    rule, elements, exact = expected
    hits = detail["hits"]
    assert [h.rule for h in hits] == [rule], [(h.rule, h.elements) for h in hits]
    got = set(hits[0].elements)
    if exact:
        assert got == set(elements), (got, elements)
    else:
        assert set(elements) <= got, (got, elements)


def test_violation_kinds_cover_contract_tables():
    assert set(VIOLATION_KINDS) == {"hidden_rail", "rail_not_connected", "name_duplicate", "name_case_collision",
                                    "port_net_unknown", "port_on_rail", "element_unknown_key"}


@pytest.mark.parametrize("name", CIRCUITS)
@pytest.mark.parametrize("kind", VIOLATION_KINDS)
@pytest.mark.parametrize("how", VARIANTS)
def test_injected_violation_detected_in_every_variant(topo, name, kind, how):
    doc = _variant(synthetic_topologies()[name], how)
    topo.load(doc)                                    # 변형만으로는 통과(주입 전 깨끗함)
    bad, expected = inject_violation(doc, kind)
    _check(topo.rejected(bad), expected)


# 주입 -> 이름 치환: 대소문자 충돌은 무작위 치환이 두 이름을 서로 무관한 소문자 이름으로 보내 충돌이 사라지므로 뺀다
# (치환이 대소문자 관계를 보존하지 않는 것은 변형기의 정의다 -- random_renaming 머리).
RENAME_AFTER_KINDS = tuple(k for k in VIOLATION_KINDS if k != "name_case_collision")


@pytest.mark.parametrize("name", CIRCUITS)
@pytest.mark.parametrize("kind", RENAME_AFTER_KINDS)
@pytest.mark.parametrize("seed", range(2))
def test_violation_elements_follow_renaming(topo, name, kind, seed):
    doc = synthetic_topologies()[name]
    bad, (rule, elements, exact) = inject_violation(doc, kind)
    m = random_renaming(bad, seed)
    detail = topo.rejected(rename(bad, m))
    _check(detail, (rule, frozenset(m.get(x, x) for x in elements), exact))
    # 같은 위반을 이름만 바꾼 두 문서가 같은 위반 종류 목록·같은 not_evaluated 를 낸다
    plain = topo.rejected(bad)
    assert detail["rejected_gates"] == plain["rejected_gates"]
    assert detail["not_evaluated"] == plain["not_evaluated"]
    assert {frozenset(m.get(x, x) for x in h.elements) for h in plain["hits"]} == \
        {frozenset(h.elements) for h in detail["hits"]}
