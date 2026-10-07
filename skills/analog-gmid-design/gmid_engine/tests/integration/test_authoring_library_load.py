"""9회로 교차 -- `load_topology` 를 assets/library 원본에 실제로 건다 (authoring CONTRACT 4절).

기대값은 topology JSON 직접 집계(test 쪽 json)와 계약 4절 표 숫자에서 만든다. 피검 함수로 기대값을 만들지 않는다.
folded_cascode·nmcnr_amplifier·two_stage_ota 는 2026-10-07 topology 정정(b9c7042)으로 passive_elements 를 선언해
이제 9회로 모두 로드를 통과한다(CI-12 기본안 '키 없으면 거부' 는 authoring 단위 test 가 픽스처로 확인).
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from gmid_engine.authoring import load_topology
from gmid_engine.core import SchemaRejectedError, exit_code_for

LIBRARY = Path(__file__).resolve().parents[3] / "assets" / "library"

# 계약 4절 표: (소자, 수동, 이상원, 레일, in 포트, out 포트) -- 표에 없는 칸은 None(JSON 집계만으로 확인)
PASS_TABLE = {
    "common_gate_amplifier": (3, 0, None, 2, 1, 1),
    "current_reuse_telescopic_ota": (51, 12, 1, None, 2, 2),
    "ngcc_3stage_ff": (16, 3, None, None, None, None),
    "pushpull_follower_buffer": (6, 1, None, 3, None, None),
    "sf_pushpull_output_opamp": (22, 5, 1, 3, None, None),
    "two_stage_ota_sf": (9, 2, None, None, None, None),
    # 예전 CI-12 3회로: 숫자 칸은 JSON 집계로만 확인(None)
    "folded_cascode": (None, None, None, None, None, None),
    "nmcnr_amplifier": (None, None, None, None, None, None),
    "two_stage_ota": (None, None, None, None, None, None),
}
FORMER_CI12 = ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")
TAGS = ("device_roles", "symmetry", "sizing_roles", "compensation")


def _path(name):
    return LIBRARY / (name + ".topology.json")


def _raw(name):
    return json.loads(_path(name).read_text(encoding="utf-8"))


def _write(tmp_path, doc, name):
    p = tmp_path / (name + ".topology.json")
    p.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(p)


def _rejected(path):
    with pytest.raises(SchemaRejectedError) as ei:
        load_topology(path)
    assert exit_code_for(ei.value) == 7
    return dict(ei.value.record.detail)


def _value(e, fields):
    vk = next((k for k in fields if k in e), None)
    return vk, (e[vk] if vk else None)


def test_library_has_exactly_nine_circuits():
    names = sorted(p.name[: -len(".topology.json")] for p in LIBRARY.glob("*.topology.json") if not p.name.startswith("_"))
    assert names == sorted(PASS_TABLE)


@pytest.mark.parametrize("name", sorted(PASS_TABLE))
def test_passing_circuit_matches_json_aggregate(name):
    raw = _raw(name)
    doc = load_topology(str(_path(name)))
    assert doc.name == raw["topology_name"]
    assert doc.file_sha256 == hashlib.sha256(_path(name).read_bytes()).hexdigest()

    exp_dev = sorted((e["name"], e["kind"], e["drain"], e["gate"], e["source"], e.get("bulk")) for e in raw["netlist"])
    assert [(d.name, d.kind, d.d, d.g, d.s, d.bulk) for d in doc.devices] == exp_dev

    exp_pas = sorted((e["name"], e["kind"], tuple(e["terminals"])) + _value(e, ("value_ohm", "value_farad"))
                     for e in raw["passive_elements"])
    assert [(p.name, p.kind, p.terminals, p.value_key, p.value) for p in doc.passives] == exp_pas

    exp_src = sorted((e["name"], e["kind"], tuple(e["terminals"])) + _value(e, ("value_amp", "value_volt"))
                     for e in raw.get("ideal_sources", []))
    assert [(s.name, s.kind, s.terminals, s.value_key, s.value) for s in doc.sources] == exp_src

    assert doc.rails == frozenset(raw["supply_nets"])
    exp_ports = sorted((k, v["direction"], v["role"]) for k, v in raw["ports"].items() if not k.startswith("_"))
    assert [(p.net, p.direction, p.role) for p in doc.ports] == exp_ports

    # 넷 수: JSON 단자 넷 집합 == 결과 선언에서 모은 단자 넷 집합
    json_nets = {e[k] for e in raw["netlist"] for k in ("drain", "gate", "source", "bulk") if k in e}
    json_nets |= {t for e in raw["passive_elements"] + raw.get("ideal_sources", []) for t in e["terminals"]}
    doc_nets = {n for d in doc.devices for n in (d.d, d.g, d.s, d.bulk) if n is not None}
    doc_nets |= {t for x in doc.passives + doc.sources for t in x.terminals}
    assert doc_nets == json_nets

    # 계약 4절 표 숫자와도 대조
    n_dev, n_pas, n_src, n_rail, n_in, n_out = PASS_TABLE[name]
    counts = (len(doc.devices), len(doc.passives), len(doc.sources), len(doc.rails),
              sum(p.direction == "input" for p in doc.ports), sum(p.direction == "output" for p in doc.ports))
    for want, got in zip((n_dev, n_pas, n_src, n_rail, n_in, n_out), counts):
        if want is not None:
            assert got == want, (name, counts)


@pytest.mark.parametrize("name", FORMER_CI12)
def test_former_ci12_circuits_load_with_declared_passives(name):
    """예전 CI-12 3회로는 이제 passive_elements 를 선언해 통과하고, 선언 수동소자가 JSON 집계와 같다."""
    raw = _raw(name)
    assert isinstance(raw.get("passive_elements"), list) and raw["passive_elements"]   # JSON 직접 확인: 선언 있음
    doc = load_topology(str(_path(name)))
    exp = sorted((e["name"], e["kind"], tuple(e["terminals"])) + _value(e, ("value_ohm", "value_farad"))
                 for e in raw["passive_elements"])
    assert [(p.name, p.kind, p.terminals, p.value_key, p.value) for p in doc.passives] == exp
    assert len(doc.devices) == len(raw["netlist"])


def test_current_reuse_resistor_connected_nets_not_rejected():
    """N_cc_rz1/2 는 MOS 단자에 없고 2단자 원소에만 있다(JSON 집계) -- Rz 로 DC 연결돼 숨은 레일 아님(오거부 0)."""
    raw = _raw("current_reuse_telescopic_ota")
    mos_nets = {e[k] for e in raw["netlist"] for k in ("drain", "gate", "source")}
    two_nets = {t for e in raw["passive_elements"] + raw["ideal_sources"] for t in e["terminals"]}
    only_two = two_nets - mos_nets - set(raw["supply_nets"])
    assert {"N_cc_rz1", "N_cc_rz2"} <= only_two
    doc = load_topology(str(_path("current_reuse_telescopic_ota")))
    assert {"N_cc_rz1", "N_cc_rz2"} <= {t for p in doc.passives for t in p.terminals}


@pytest.mark.parametrize("name", ["pushpull_follower_buffer", "sf_pushpull_output_opamp"])
def test_attack_14b_hidden_rail_when_agnd_dropped(tmp_path, name):
    raw = _raw(name)
    assert "agnd" in raw["supply_nets"]
    users = sorted(e["name"] for e in raw["passive_elements"] + raw.get("ideal_sources", []) if "agnd" in e["terminals"])
    assert "agnd" not in {e[k] for e in raw["netlist"] for k in ("drain", "gate", "source")}
    raw["supply_nets"] = [n for n in raw["supply_nets"] if n != "agnd"]
    detail = _rejected(_write(tmp_path, raw, name))
    assert [(h.rule, h.elements) for h in detail["hits"]] == [("hidden_rail", tuple(sorted(users + ["agnd"])))]
    assert detail["not_evaluated"] == ()


def test_attack_14b_expected_elements_match_contract_text():
    """계약 4절 문장(pushpull (CL, agnd), sf (CL, Cc, agnd))이 JSON 집계와 같은지 -- 위 test 기대값의 교차 확인."""
    for name, want in (("pushpull_follower_buffer", {"CL"}), ("sf_pushpull_output_opamp", {"CL", "Cc"})):
        raw = _raw(name)
        assert {e["name"] for e in raw["passive_elements"] + raw.get("ideal_sources", []) if "agnd" in e["terminals"]} == want


def test_two_stage_ota_sf_fp_invariant(tmp_path):
    """계약 4절 지문 확인: 태그 키 4개 삭제 + `_note` 변경 + netlist 섞기 -> connectivity_fp 같음. 연결 하나 바꾸면 다름."""
    name = "two_stage_ota_sf"
    base = load_topology(str(_path(name)))
    raw = _raw(name)
    for t in TAGS:
        raw.pop(t, None)
    raw["_note"] = "changed for the fingerprint test"
    random.Random(5).shuffle(raw["netlist"])
    random.Random(6).shuffle(raw["passive_elements"])
    got = load_topology(_write(tmp_path, raw, name))
    assert got.connectivity_fp == base.connectivity_fp
    assert got.file_sha256 != base.file_sha256

    changed = copy.deepcopy(raw)
    changed["netlist"][0]["kind"] = "pmos" if changed["netlist"][0]["kind"] == "nmos" else "nmos"
    assert load_topology(_write(tmp_path, changed, name + "_k")).connectivity_fp != base.connectivity_fp
