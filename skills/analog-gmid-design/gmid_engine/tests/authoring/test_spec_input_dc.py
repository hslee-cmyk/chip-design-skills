"""입력 DC `human.input_dc` (gate `input_dc`) -- SPEC_CONTRACT 2절 input_dc_* 행, 3절 InputDc mode."""
from __future__ import annotations

import pytest

SRC = {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}


def test_value_mode(sc):
    doc = sc.load()
    assert (doc.input_dc.mode, doc.input_dc.value_v) == ("value", sc.human["input_dc"]["value_v"])


@pytest.mark.parametrize("rail", ["rail_hi", "rail_lo"])
def test_net_mode_on_rail(sc, rail):
    sc.human["input_dc"] = {"net": rail, "source": SRC}
    doc = sc.load()
    assert (doc.input_dc.mode, doc.input_dc.net) == ("net", rail)


def test_engine_mode(sc):
    sc.human["input_dc"] = {"engine": True, "source": SRC}
    assert sc.load().input_dc.mode == "engine"


def test_pending_mode(sc):
    sc.human["input_dc"] = {"pending": "SP-2"}
    doc = sc.load()
    assert doc.input_dc.mode == "pending" and doc.input_dc.decision == "SP-2"


@pytest.mark.parametrize("net", ["n_mid", "n_inp", "n_ghost"])
def test_net_not_rail(sc, net):
    sc.human["input_dc"] = {"net": net, "source": SRC}
    sc.reject_only("input_dc_net_not_rail", "input_dc")


@pytest.mark.parametrize("v", [1.3, -0.1, 5.0])
def test_out_of_rails(sc, v):
    sc.human["input_dc"]["value_v"] = v
    sc.reject_only("input_dc_out_of_rails", "input_dc")


@pytest.mark.parametrize("v", [0.0, 1.2, 0.6])
def test_within_rails_inclusive(sc, v):
    sc.human["input_dc"]["value_v"] = v
    sc.load()


@pytest.mark.parametrize("raw", [
    {"value_v": 0.6, "net": "rail_hi", "source": SRC},       # 모드 키 2개
    {"source": SRC},                                           # 모드 키 0개
    {"value_v": "0.6", "source": SRC},
    {"net": 3, "source": SRC},
    {"engine": False, "source": SRC},
    {"engine": 1, "source": SRC},
    [0.6],
])
def test_type(sc, raw):
    sc.human["input_dc"] = raw
    d = sc.reject()
    assert sc.rules(d) == ["type"], sc.rules(d)
    assert d["rejected_gates"] == ("input_dc",)


def test_out_of_rails_not_checked_when_supplies_rejected(sc):
    """docstring: 전원 선언이 거부되면 레일 범위 검사는 하지 않는다."""
    sc.human["supplies_v"]["values"]["rail_hi"] = "bad"
    sc.human["input_dc"]["value_v"] = 9.0
    d = sc.reject()
    assert "input_dc_out_of_rails" not in sc.rules(d)
    assert d["rejected_gates"] == ("supplies",)


def test_unknown_key(sc):
    sc.human["input_dc"]["icmr_v"] = [0.2, 1.0]
    d = sc.reject()
    assert sc.rules(d) in (["unknown_key"], ["legacy_name"])
    assert d["rejected_gates"] == ("input_dc",)


def test_plan_rule_not_allowed(sc):
    sc.human["input_dc"]["source"] = {"kind": "plan_rule", "plan_id": "DEC-1"}
    sc.reject_only("source_kind_not_allowed_here", "input_dc")
