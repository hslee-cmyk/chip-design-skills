"""metamorphic: connectivity_fp 가 변형에 대해 계약대로 움직인다(authoring CONTRACT 2절).

계약 정의: `connectivity_fp` = fp_of(소자 (name, kind, d, g, s, bulk), 수동·이상원 (name, kind, terminals, value_key, value),
정렬 레일, 포트 (net, direction, role)). 불변식 -- `_` 주석 키를 바꾸거나 더해도 같다, 태그 키 4개를 통째로 지워도 같다,
원소 순서를 섞어도 같다 / 넷 이름 하나, kind 하나, 포트 role 하나, 레일 집합, 수동소자 값 하나라도 바뀌면 다르다 /
file_sha256 은 지문에 들어가지 않는다.
그래서 이름 치환은 fp 를 **바꾼다**(넷·원소 이름이 투영에 있다). 이름에 무관한 것은 'fp 값'이 아니라 '치환표가 같으면 같은 fp,
되돌리면 원래 fp' 라는 함수성이다 -- 이 test 들이 그것을 본다. topology_name 은 투영 목록에 없으므로 fp 에 들어가지 않는다.
"""
from __future__ import annotations

import pytest

from .topogen import (
    add_tag_noise,
    duplicate_stage,
    flip_polarity,
    random_renaming,
    rename,
    shuffle_order,
    synthetic_topologies,
)

CIRCUITS = sorted(synthetic_topologies())
SEEDS = range(3)


def _fp(topo, doc):
    return topo.load(doc).connectivity_fp


@pytest.mark.parametrize("name", CIRCUITS)
@pytest.mark.parametrize("seed", SEEDS)
def test_order_shuffle_keeps_fp_but_not_file_hash(topo, name, seed):
    doc = synthetic_topologies()[name]
    a, b = topo.load(doc), topo.load(shuffle_order(doc, seed))
    assert a.connectivity_fp == b.connectivity_fp
    assert a.file_sha256 != b.file_sha256            # 파일 바이트는 달라졌다 -- 지문이 파일 해시가 아니다


@pytest.mark.parametrize("name", CIRCUITS)
@pytest.mark.parametrize("seed", SEEDS)
def test_tag_and_comment_noise_keeps_fp(topo, name, seed):
    doc = synthetic_topologies()[name]
    assert _fp(topo, add_tag_noise(doc, seed)) == _fp(topo, doc)


@pytest.mark.parametrize("name", CIRCUITS)
def test_topology_name_not_in_fp(topo, name):
    doc = synthetic_topologies()[name]
    other = dict(doc, topology_name="zz_other_name")
    a, b = topo.load(doc), topo.load(other)
    assert a.name != b.name and a.connectivity_fp == b.connectivity_fp


@pytest.mark.parametrize("name", CIRCUITS)
@pytest.mark.parametrize("seed", SEEDS)
def test_rename_changes_fp_and_inverse_restores(topo, name, seed):
    doc = synthetic_topologies()[name]
    m = random_renaming(doc, seed)
    renamed = rename(doc, m)
    assert _fp(topo, renamed) != _fp(topo, doc)
    back = rename(renamed, {v: k for k, v in m.items()})
    assert _fp(topo, back) == _fp(topo, doc)


@pytest.mark.parametrize("name", CIRCUITS)
@pytest.mark.parametrize("seed", SEEDS)
def test_same_mapping_same_fp_regardless_of_order(topo, name, seed):
    """fp 는 (구조, 치환표)의 함수다: 순서를 다르게 섞은 두 입력에 같은 치환표를 걸면 fp 가 같다."""
    doc = synthetic_topologies()[name]
    m = random_renaming(doc, seed)
    a = rename(shuffle_order(doc, seed), m)
    b = rename(shuffle_order(doc, seed + 100), m)
    assert _fp(topo, a) == _fp(topo, b)


@pytest.mark.parametrize("name", CIRCUITS)
def test_single_internal_net_rename_changes_fp(topo, name):
    """넷 이름 하나만 바꿔도 fp 가 다르다(CONTRACT 2절). 레일·포트가 아닌 내부 넷 하나를 고른다."""
    doc = synthetic_topologies()[name]
    nets = topo.json_names(doc) - {doc["topology_name"]} - {e["name"] for k in ("netlist", "passive_elements",
                                                                               "ideal_sources") for e in doc[k]}
    internal = sorted(nets - set(doc["supply_nets"]) - set(doc["ports"]))
    assert internal
    assert _fp(topo, rename(doc, {internal[0]: internal[0] + "_x"})) != _fp(topo, doc)


@pytest.mark.parametrize("name", CIRCUITS)
def test_single_element_rename_changes_fp(topo, name):
    """원소 이름 하나만 바꿔도 fp 가 다르다(투영에 소자 name 이 있다, CONTRACT 2절)."""
    doc = synthetic_topologies()[name]
    first = doc["netlist"][0]["name"]
    assert _fp(topo, rename(doc, {first: first + "_x"})) != _fp(topo, doc)


@pytest.mark.parametrize("name", CIRCUITS)
def test_polarity_flip_changes_fp_and_twice_restores(topo, name):
    doc = synthetic_topologies()[name]
    once, _ = flip_polarity(doc)
    twice, _ = flip_polarity(once)
    assert _fp(topo, once) != _fp(topo, doc)
    assert _fp(topo, twice) == _fp(topo, doc)


@pytest.mark.parametrize("name", CIRCUITS)
@pytest.mark.parametrize("seed", SEEDS)
def test_duplicate_commutes_with_flip_and_shuffle(topo, name, seed):
    """단 복제는 극성 뒤집기·순서 섞기와 교환된다(이어지는 입력은 이름순 첫째라 순서·극성에 무관)."""
    doc = synthetic_topologies()[name]
    dup, _ = duplicate_stage(doc, "_s2")
    flip_dup, _ = flip_polarity(dup)
    dup_flip, _ = duplicate_stage(flip_polarity(doc)[0], "_s2")
    assert _fp(topo, flip_dup) == _fp(topo, dup_flip)
    assert _fp(topo, duplicate_stage(shuffle_order(doc, seed), "_s2")[0]) == _fp(topo, dup)
    assert _fp(topo, dup) != _fp(topo, doc)
