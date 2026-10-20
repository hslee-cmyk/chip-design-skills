"""metamorphic: 레이아웃 matching 분류(graph `s1_matching_groups`, graph CONTRACT 4.5a)가 이름·순서·극성 변형을 따라가는가.

oracle 종류 (a) -- 구성으로 정답이 정해진 변형 관계(피검 함수 출력을 기대값으로 쓰지 않는다. 비교는 '원래 결과에 변형 표를
적용한 것' 대 '변형 입력의 결과'):
- graph CONTRACT 머리 '대원칙': 규칙은 connectivity·선언만으로 판정하고 이름은 결정론적 순서 tie-break 로만 쓴다.
  4.5a '구조 정의'도 "소자·넷 이름은 결정론적 순서에만 쓴다". 그래서 이름 치환 뒤 matching_groups·matching_dispositions 를
  이름 무관 정준형(다중집합)으로 풀면 원래 것에 치환표를 적용한 것과 같다.
- 정준형의 순서 규칙(4.5a 표·4.5 표): mirror·bias_distribution·feedback_shared 의 nets = (gate, source) -- 순서가 뜻이라 tuple;
  diff_pair 의 nets = (source,) + 남은 멤버 gate 넷 **정렬**(4.5 rel_matching_offset), branch_symmetric 의 nets = (gate,) + source 넷
  **정렬** -- 첫 칸만 뜻이고 나머지는 이름 정렬이라 (첫 칸, 집합); bias_sibling = (source, 그 소자 gate) tuple. members·group 은 집합.
  [2026-10-08 J14 이후 4.5a 표] `mirror_consumer_symmetric` 의 nets = (gate, source, a, b) "a < b" -- 대응 넷 짝 {a ↔ b} 는 무향이고
  a·b 순서는 이름 정렬이라 ((gate, source), {a, b}).
  그룹 목록 순서는 gs 묶음 순서(이름 정렬)라 다중집합으로 비교한다.
- 순서 섞기·태그 잡음(authoring CONTRACT 2절: 연결 투영이 같으면 같은 S1 키): 결과 tuple 이 그대로(순서까지).
- 극성 뒤집기(nmos<->pmos + 두 레일 맞바꿈): 4.5a 정의는 kind 를 '같은 kind' 비교로만 쓰고 레일·G·B·L 은 kind 와 무관하므로
  분류가 레일 치환표를 따라간다(MatchingGroup.kind 는 mirror/diff_pair/… 라 극성과 무관).
- 단 복제(duplicate_stage): 4.5a '일반성' 문단 -- 모든 분류 kind 수가 정확히 2배.

회로: 합성 3종(syn_cascode 는 S1 에서 이상 전압원 정지 -- test_metamorphic_s1 이 다룬다) + library 9회로 전부.
변형: 이름 치환 seed 0~2, 섞기+태그 잡음 seed 0~2, 극성(레일 2개인 회로). 그래프 에이전트가 손으로 돌린 이름·섞기·극성
점검(4.5a '이름 치환 3벌·순서 섞기 3벌·극성 뒤집기' 42/42)을 library 로 넓힌 고정 test 다.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

import pytest

from gmid_engine.graph import GRAPH_KEY, build_s1

from .topogen import add_tag_noise, duplicate_stage, flip_polarity, random_renaming, rename, shuffle_order, synthetic_topologies

LIBRARY = Path(__file__).resolve().parents[3] / "assets" / "library"
SYNTH = ("syn_cs_load", "syn_diffpair5", "syn_follower")
LIB = ("common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
       "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf")
CIRCUITS = SYNTH + LIB
SEEDS = range(3)
SORTED_TAIL_RULES = ("diff_pair", "branch_symmetric")      # nets = (첫 칸,) + 이름 정렬 나머지 (4.5 / 4.5a 표)
SORTED_PAIR_RULES = ("mirror_consumer_symmetric",)         # nets = (gate, source, a, b), a < b 무향 짝 (4.5a 표)


def _doc(name):
    if name in SYNTH:
        return synthetic_topologies()[name]
    return json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))


def _build(topo, doc):
    from gmid_engine.search import open_run
    donors, counters = open_run()          # [XRUN-F1 card B C0·C6] 변형마다 새 실행 하나
    return build_s1(topo.load(doc), None, donors=donors, counters=counters)


def _field(s1, f):
    return s1.value("graph", GRAPH_KEY, f)


def canon(s1, nm=lambda x: x):
    """(matching_groups 다중집합, matching_dispositions 다중집합) -- 이름은 nm 으로 옮긴다."""
    def nets(ev):
        ns = tuple(nm(n) for n in ev.nets)
        if ev.rule in SORTED_TAIL_RULES:
            return (ns[:1], frozenset(ns[1:]))
        if ev.rule in SORTED_PAIR_RULES:
            return (ns[:2], frozenset(ns[2:]))
        return ns

    def row(x):
        return (x.kind, frozenset(nm(m) for m in x.members), x.status, x.evidence.rule, nets(x.evidence),
                frozenset(nm(g) for g in x.evidence.group), x.evidence.basis)

    return (collections.Counter(row(x) for x in _field(s1, "matching_groups")),
            collections.Counter(row(x) for x in _field(s1, "matching_dispositions")))


def kind_counts(s1):
    return collections.Counter(x.evidence.rule for x in _field(s1, "matching_groups") + _field(s1, "matching_dispositions"))


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", CIRCUITS)
def test_renaming_maps_matching_classification(topo, name, seed):
    doc = _doc(name)
    m = random_renaming(doc, seed)
    a = _build(topo, doc)
    b = _build(topo, rename(doc, m))
    assert canon(b) == canon(a, lambda x: m.get(x, x))
    if any(canon(a)):
        assert canon(b) != canon(a)          # 정준형이 이름을 실제로 담는다(공허한 비교 아님)


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", CIRCUITS)
def test_shuffle_and_tag_noise_keep_matching_exactly(topo, name, seed):
    doc = _doc(name)
    a = _build(topo, doc)
    b = _build(topo, add_tag_noise(shuffle_order(doc, seed), seed))
    for f in ("matching_groups", "matching_dispositions", "rel_matching_offset"):
        assert _field(b, f) == _field(a, f)


@pytest.mark.parametrize("name", [n for n in CIRCUITS if len(_doc(n)["supply_nets"]) == 2])
def test_polarity_flip_maps_matching_classification(topo, name):
    doc = _doc(name)
    flipped, swap = flip_polarity(doc)
    a = _build(topo, doc)
    b = _build(topo, flipped)
    assert canon(b) == canon(a, lambda x: swap.get(x, x))


@pytest.mark.parametrize("name", SYNTH)
def test_duplicate_stage_doubles_every_matching_kind(topo, name):
    doc = _doc(name)
    a = _build(topo, doc)
    b = _build(topo, duplicate_stage(doc, "_s2")[0])
    ka, kb = kind_counts(a), kind_counts(b)
    assert kb == collections.Counter({k: 2 * v for k, v in ka.items()})


def test_inputs_are_nontrivial(topo):
    """공허한 통과 방지(oracle (d) 회로 해석): two_stage_ota 는 차동쌍(M1/M2) + diode 미러 부하(M3/M4) OTA 이고(library topology
    `_netlist_sections_structured` 의 사람 선언), folded_cascode 는 캐스코드 쌍을 가진다 -- 그래서 변형 비교 대상에 diff_pair·mirror
    계열·branch_symmetric 분류가 실제로 있다."""
    seen = collections.Counter()
    for name in CIRCUITS:
        seen.update(kind_counts(_build(topo, _doc(name))))
    assert seen["diff_pair"] > 0 and seen["branch_symmetric"] > 0, seen
    assert sum(v for k, v in seen.items() if k.startswith("mirror_")) > 0, seen
