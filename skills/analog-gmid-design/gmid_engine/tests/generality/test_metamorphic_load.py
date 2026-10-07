"""metamorphic: 변형한 합성 topology 도 로드를 통과하고, 로드 결과가 변형의 '기대 상'과 같다.

기대 상 = 원래 doc 의 로드 투영에 같은 변형(이름 치환표·레일 치환·kind 치환)을 적용한 것. 즉 로더는 이름을
불투명한 값으로만 다룬다(이름이 바뀌면 결과의 이름만 바뀐다). 근거: authoring CONTRACT 2절(TopologyDoc 필드),
3.5 "넷 이름으로 레일을 정하지 않는다", 머리 "태그 키는 읽지 않는다".
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
KIND_SWAP = {"nmos": "pmos", "pmos": "nmos"}


@pytest.mark.parametrize("name", CIRCUITS)
@pytest.mark.parametrize("seed", SEEDS)
def test_renamed_loads_with_mapped_projection(topo, name, seed):
    doc = synthetic_topologies()[name]
    base = topo.projection(topo.load(doc))
    m = random_renaming(doc, seed)
    td = topo.load(rename(doc, m))
    assert td.name == m[name]
    assert topo.projection(td) == topo.map_projection(base, m)


@pytest.mark.parametrize("name", CIRCUITS)
@pytest.mark.parametrize("seed", SEEDS)
def test_shuffled_loads_with_same_projection(topo, name, seed):
    doc = synthetic_topologies()[name]
    base = topo.load(doc)
    td = topo.load(shuffle_order(doc, seed))
    assert topo.projection(td) == topo.projection(base)
    # 결과 tuple 은 정렬된다(CONTRACT 2절: 원소 이름순, 포트 넷순) -- 입력 순서가 결과 순서에 새지 않는다
    assert td.devices == base.devices and td.passives == base.passives and td.sources == base.sources
    assert td.ports == base.ports


@pytest.mark.parametrize("name", CIRCUITS)
def test_flipped_loads_with_swapped_kinds_and_rails(topo, name):
    doc = synthetic_topologies()[name]
    base = topo.projection(topo.load(doc))
    flipped, swap = flip_polarity(doc)
    td = topo.load(flipped)
    assert topo.projection(td) == topo.map_projection(base, swap, KIND_SWAP)
    assert td.rails == base["rails"]                  # 레일 집합 자체는 같다(두 넷을 맞바꿈)


@pytest.mark.parametrize("name", CIRCUITS)
def test_duplicated_stage_loads(topo, name):
    doc = synthetic_topologies()[name]
    base = topo.projection(topo.load(doc))
    dup, link = duplicate_stage(doc, "_s2")
    td = topo.load(dup)
    proj = topo.projection(td)
    assert proj == topo.json_projection(dup)
    for key in ("devices", "passives", "sources"):
        assert len(proj[key]) == 2 * len(base[key])
        assert base[key] <= proj[key]                 # 앞 단은 그대로 들어 있다
    assert proj["rails"] == base["rails"]
    assert [p.net for p in td.ports if p.direction == "output"] == [link + "_s2"]


@pytest.mark.parametrize("name", CIRCUITS)
@pytest.mark.parametrize("seed", SEEDS)
def test_tag_noise_loads_with_same_projection(topo, name, seed):
    doc = synthetic_topologies()[name]
    base = topo.projection(topo.load(doc))
    assert topo.projection(topo.load(add_tag_noise(doc, seed))) == base


@pytest.mark.parametrize("name", CIRCUITS)
@pytest.mark.parametrize("seed", SEEDS)
def test_composed_transforms_load(topo, name, seed):
    """변형을 겹쳐도(태그 잡음 -> 이름 치환 -> 극성 -> 단 복제 -> 순서 섞기) 로드가 통과하고 투영이 JSON 집계와 같다."""
    doc = synthetic_topologies()[name]
    x = add_tag_noise(doc, seed)
    x = rename(x, random_renaming(x, seed))
    x, _ = flip_polarity(x)
    x, _ = duplicate_stage(x, "q")
    x = shuffle_order(x, seed)
    td = topo.load(x)
    assert topo.projection(td) == topo.json_projection(x)
    assert len(td.devices) == 2 * len(doc["netlist"])
