"""생성기·변형기 자체 확인 -- 엔진 결과를 보기 전에 입력이 의도대로 만들어졌는지(공허한 metamorphic test 방지).

- 합성 회로 4종이 library 이름과 겹치지 않고, 로드를 통과하며, 로드 결과가 JSON 직접 집계와 같다.
- 변형기의 dict 수준 성질: 이름 치환은 전단사이고 역치환으로 되돌아온다, 극성 뒤집기 두 번 = 원래, 순서 섞기는 내용을
  바꾸지 않는다, 단 복제는 원소 수를 두 배로 만든다.
- helper 모듈이 구조 규칙 A·B 를 지킨다(tests/ 는 구조 test 대상 밖이지만 이 패키지는 스스로 검사기를 건다).
"""
from __future__ import annotations

import json
from pathlib import Path

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
TOPOGEN = Path(__file__).resolve().parent / "topogen"


def _canon(doc):
    """순서 무관 비교용 정규형(원소 목록·supply_nets·포트를 정렬, 키 순서 무시)."""
    def norm(x):
        if isinstance(x, dict):
            return tuple(sorted((k, norm(v)) for k, v in x.items()))
        if isinstance(x, list):
            return tuple(norm(v) for v in x)
        return x
    out = {}
    for k, v in doc.items():
        if k in ("netlist", "passive_elements", "ideal_sources", "supply_nets"):
            out[k] = tuple(sorted((norm(e) for e in v), key=repr))
        else:
            out[k] = norm(v)
    return tuple(sorted(out.items()))


def test_four_synthetic_circuits_with_two_rails_and_both_polarities():
    docs = synthetic_topologies()
    assert CIRCUITS == ["syn_cascode", "syn_cs_load", "syn_diffpair5", "syn_follower"]
    kinds = set()
    for name, doc in docs.items():
        assert doc["topology_name"] == name
        assert len(doc["supply_nets"]) == len(set(doc["supply_nets"])) == 2
        kinds |= {e["kind"] for e in doc["netlist"]}
    assert kinds == {"nmos", "pmos"}


def test_synthetic_names_disjoint_from_library(topo, structure_checks, library_dir):
    """library 밖 회로다: 이름 집합(규칙 E 와 같은 수집 -- 회로·파일·소자·넷·포트·레일)과 겹치는 이름 0."""
    circuits, lib_names = structure_checks.library_names(library_dir)
    assert len(circuits) >= 9 and "two_stage_ota" in lib_names
    for doc in synthetic_topologies().values():
        assert not topo.json_names(doc) & set(lib_names), sorted(topo.json_names(doc) & set(lib_names))


def test_generator_returns_fresh_objects():
    a = synthetic_topologies()
    a["syn_cs_load"]["netlist"][0]["name"] = "changed"
    assert synthetic_topologies()["syn_cs_load"]["netlist"][0]["name"] != "changed"


@pytest.mark.parametrize("name", CIRCUITS)
def test_synthetic_loads_and_matches_json(topo, name):
    doc = synthetic_topologies()[name]
    td = topo.load(doc)
    assert td.name == name
    assert topo.projection(td) == topo.json_projection(doc)
    assert len(td.devices) == len(doc["netlist"])


@pytest.mark.parametrize("name", CIRCUITS)
@pytest.mark.parametrize("seed", range(3))
def test_random_renaming_is_total_bijection_and_invertible(topo, name, seed):
    doc = synthetic_topologies()[name]
    m = random_renaming(doc, seed)
    names = topo.json_names(doc)
    assert set(m) == names                                         # 모든 이름을 바꾼다
    assert len(set(m.values())) == len(m)                          # 전단사
    assert not set(m.values()) & names                             # 옛 이름과 겹치지 않음
    assert len({v.casefold() for v in m.values()}) == len(m)       # casefold 충돌 없음
    assert all(v[0].isalpha() for v in m.values())                 # 포트 키가 주석(`_`)이 되지 않음
    assert m == random_renaming(doc, seed)                         # 결정론
    renamed = rename(doc, m)
    assert topo.json_names(renamed) == set(m.values())
    assert rename(renamed, {v: k for k, v in m.items()}) == doc


@pytest.mark.parametrize("name", CIRCUITS)
def test_flip_polarity_twice_is_identity(name):
    doc = synthetic_topologies()[name]
    once, swap = flip_polarity(doc)
    assert sorted(swap) == sorted(doc["supply_nets"]) and swap[doc["supply_nets"][0]] == doc["supply_nets"][1]
    assert [e["kind"] for e in once["netlist"]] == [{"nmos": "pmos", "pmos": "nmos"}[e["kind"]] for e in doc["netlist"]]
    twice, _ = flip_polarity(once)
    assert twice == doc


@pytest.mark.parametrize("name", CIRCUITS)
@pytest.mark.parametrize("seed", range(3))
def test_shuffle_keeps_content(name, seed):
    doc = synthetic_topologies()[name]
    s = shuffle_order(doc, seed)
    assert _canon(s) == _canon(doc)
    assert json.dumps(s) != json.dumps(doc)       # 실제로 섞였다(공허하지 않음)


@pytest.mark.parametrize("name", CIRCUITS)
def test_duplicate_stage_doubles_elements(topo, name):
    doc = synthetic_topologies()[name]
    dup, link = duplicate_stage(doc, "_s2")
    for key in ("netlist", "passive_elements", "ideal_sources"):
        assert len(dup[key]) == 2 * len(doc[key])
    assert dup["supply_nets"] == doc["supply_nets"]
    ins = [k for k, v in doc["ports"].items() if v["direction"] == "input"]
    outs = [k for k, v in doc["ports"].items() if v["direction"] == "output"]
    assert outs == [link]
    dins = [k for k, v in dup["ports"].items() if v["direction"] == "input"]
    douts = [k for k, v in dup["ports"].items() if v["direction"] == "output"]
    assert len(dins) == 2 * len(ins) - 1 and douts == [link + "_s2"]
    assert link not in dup["ports"]                                 # 이어진 넷은 내부 넷이 됐다
    assert len(topo.json_names(dup)) > len(topo.json_names(doc))


@pytest.mark.parametrize("name", CIRCUITS)
def test_tag_noise_adds_only_ignored_and_comment_keys(name):
    doc = synthetic_topologies()[name]
    noisy = add_tag_noise(doc, 0)
    added = set(noisy) - set(doc)
    assert added == {"device_roles", "symmetry", "sizing_roles", "compensation", "_note"}   # CONTRACT 3.2 IGNORED_TAG_KEYS + `_`
    assert any(r for r in noisy["device_roles"].values())


def test_topogen_helpers_obey_structure_rules_a_b(structure_checks):
    """생성기 helper(topogen/)도 파일당 진입점 1개(A)·다른 파일 `_` 이름 import 금지(B)를 지킨다.
    구조 test 는 tests/ 를 대상에서 빼므로(structure README '검사 대상') 여기서 같은 검사기를 직접 건다."""
    n, v = structure_checks.check_a(TOPOGEN)
    assert n > 0 and v == [], "\n".join(map(str, v))
    n, v = structure_checks.check_b(TOPOGEN)
    assert n > 0 and v == [], "\n".join(map(str, v))
