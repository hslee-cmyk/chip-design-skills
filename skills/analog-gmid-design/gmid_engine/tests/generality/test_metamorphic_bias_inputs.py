"""metamorphic: `bias_inputs`(authoring CONTRACT 9절)가 넷 이름 치환·순서 섞기를 따라가는가.

- 이름 치환(random_renaming + rename, 치환표가 bias_inputs 원소도 옮긴다 -- topogen `_doc_walk.map_nets`):
  로드 결과 `bias_inputs` = 원래 결과의 각 넷을 같은 표로 옮겨 정렬한 tuple(9절 '정렬 tuple'). 로더는 이름을 불투명한
  값으로만 다룬다(README '이름 치환' 불변량과 같은 근거).
- 치환표를 넷 자리에만 적용하고 bias_inputs 는 옛 이름으로 두면(낡은 선언) -> 새 gate 전용 이름은 `gate_only_undeclared`,
  옛 이름은 `bias_input_not_gate_only`(gate 에도 없는 넷) -- 위반 elements 가 정확히 치환표의 상/원상이다.
- 순서 섞기(shuffle_order)·bias_inputs 원소 순서 뒤집기: 결과 동일.

oracle: (a) 기대값 = 원래 로드 결과(같은 함수의 다른 입력)에 치환표를 적용한 것 + 구성으로 정한 gate 전용 넷.
대상: 합성 회로 syn_cs_load 에 외부 바이어스 gate 를 하나 더한 것(구성) + library 7회로(bias_inputs 선언 회로).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from .topogen import random_renaming, rename, shuffle_order, synthetic_topologies

LIBRARY = Path(__file__).resolve().parents[3] / "assets" / "library"
# bias_inputs 를 선언한 library 회로(CONTRACT 9절 라이브러리 선언 목록 -- current_reuse·sf_pushpull 은 선언 없음)
LIB_WITH_BIAS = ("common_gate_amplifier", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
                 "pushpull_follower_buffer", "two_stage_ota", "two_stage_ota_sf")
SEEDS = range(3)


def _lib(name):
    return json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))


def _synthetic_with_bias():
    """syn_cs_load + PMOS(gate syn_vbx, drain cs_out, source qp_hi): gate 전용 넷 = {syn_vbx}(구성)."""
    doc = synthetic_topologies()["syn_cs_load"]
    doc["netlist"].append({"name": "Xbx", "kind": "pmos", "drain": "cs_out", "gate": "syn_vbx", "source": "qp_hi"})
    doc["bias_inputs"] = ["syn_vbx"]
    return doc


CASES = ["syn_cs_load+bias"] + list(LIB_WITH_BIAS)


def _doc(case):
    return _synthetic_with_bias() if case == "syn_cs_load+bias" else _lib(case)


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("seed", SEEDS)
def test_renaming_maps_bias_inputs(topo, case, seed):
    doc = _doc(case)
    base = topo.load(doc)
    assert base.bias_inputs                                       # 공허한 비교 아님
    m = random_renaming(doc, seed)
    td = topo.load(rename(doc, m))
    assert td.bias_inputs == tuple(sorted(m[n] for n in base.bias_inputs))
    assert td.bias_inputs != base.bias_inputs                     # 이름이 실제로 바뀌었다


@pytest.mark.parametrize("case", CASES)
def test_stale_bias_inputs_after_renaming_rejected(topo, case):
    """넷만 치환하고 bias_inputs 는 옛 이름 그대로 -> 새 이름 미선언 + 옛 이름 gate 전용 아님(넷마다)."""
    doc = _doc(case)
    old = sorted(doc["bias_inputs"])
    m = random_renaming(doc, 7)
    renamed = rename(doc, m)
    renamed["bias_inputs"] = list(doc["bias_inputs"])
    detail = topo.rejected(renamed)
    assert detail["rejected_gates"] == ("bias_inputs",)
    undeclared = sorted(e for h in detail["hits"] if h.rule == "gate_only_undeclared" for e in h.elements)
    not_gate_only = sorted(e for h in detail["hits"] if h.rule == "bias_input_not_gate_only" for e in h.elements)
    assert undeclared == sorted(m[n] for n in old)
    assert not_gate_only == old
    assert {h.rule for h in detail["hits"]} == {"gate_only_undeclared", "bias_input_not_gate_only"}


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("seed", SEEDS)
def test_shuffle_and_entry_order_keep_bias_inputs(topo, case, seed):
    doc = _doc(case)
    base = topo.load(doc)
    shuffled = shuffle_order(doc, seed)
    shuffled["bias_inputs"] = list(reversed(doc["bias_inputs"]))
    td = topo.load(shuffled)
    assert td.bias_inputs == base.bias_inputs
    assert td.connectivity_fp == base.connectivity_fp
