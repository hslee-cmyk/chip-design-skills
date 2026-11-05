"""`source_manifest` -- 출처 개수 대조 (authoring CONTRACT 10절, 2026-10-08 Q7).

근거(계약만, authoring 소스 미열람):
- 선택 최상위 키 `source_manifest{figure, device_count, passive_count}`. 키 없으면 검사 안 함. `connectivity_fp` 불변.
- device_count == netlist MOS 수, passive_count == `passive_elements` 수(이상원 제외).
- 위반 gate `source_manifest`: `source_manifest_mismatch`(선언·실제 개수 둘 다 메시지에), `source_manifest_type`·`_key`·
  `_figure`·`_count`(형식). 소자·수동 선언이 거부된 문서에서는 건너뛴다(`not_evaluated` 이름은 늘리지 않는다).

oracle: (a) 구성 -- base_valid 픽스처의 개수를 JSON 에서 직접 센다(MOS 4, passive 3, 이상원 1: 손으로 확인).
개수 불일치 값은 실제와 겹치지 않는 37·29 로 골라 메시지에서 두 수를 찾는다(10절 '둘 다 메시지에').
"""
from __future__ import annotations

import re

import pytest

import gmid_engine.authoring as authoring
from gmid_engine.authoring import load_topology

GATE = "source_manifest"
NOT_EVALUATED_NAMES = {
    "all_declarations", "name_uniqueness", "ports.port_net_unknown", "ports.port_on_rail", "hidden_rails"}
FIGURE = "hand-made fixture, no figure"


def counts(doc):
    """test 쪽 oracle (a): JSON 직접 집계 (MOS 수, passive_elements 수)."""
    return len(doc["netlist"]), len(doc["passive_elements"])


def with_manifest(ah, **over):
    doc = ah.base()
    n_dev, n_pas = counts(doc)
    m = {"figure": FIGURE, "device_count": n_dev, "passive_count": n_pas}
    m.update(over)
    doc["source_manifest"] = m
    return doc


def load_rejected(ah, tmp_path, doc):
    exc, detail = ah.rejected(load_topology, ah.write(tmp_path, doc))
    assert detail["gate"] == "topology_load"
    return detail


def has_number(text, n):
    return re.search(r"(?<![0-9.])%d(?![0-9.])" % n, text) is not None


def test_fixture_counts(ah):
    """구성 확인: base 는 MOS 4, passive 3, 이상원 1(이상원이 있어야 '이상원 제외' 대조가 의미 있다)."""
    doc = ah.base()
    assert counts(doc) == (4, 3)
    assert len(doc["ideal_sources"]) == 1


# ---------------------------------------------------------------------------------------------------- 통과
def test_matching_manifest_loads(ah, tmp_path):
    load_topology(ah.write(tmp_path, with_manifest(ah)))


def test_zero_passive_count_ok(ah, tmp_path):
    """passive 0 개 회로에서 passive_count 0 은 통과(common_gate 3/0 과 같은 형태)."""
    doc = ah.base()
    doc["passive_elements"] = []
    doc["supply_nets"].remove("rail_ac")       # rail_ac 는 Cload 에만 있었다 -> 지우지 않으면 rail_not_connected
    doc["source_manifest"] = {"figure": FIGURE, "device_count": 4, "passive_count": 0}
    load_topology(ah.write(tmp_path, doc))


def test_absent_key_not_checked(ah, tmp_path):
    load_topology(ah.write(tmp_path, ah.base()))


# ---------------------------------------------------------------------------------------------------- 불일치
def test_device_count_mismatch(ah, tmp_path):
    detail = load_rejected(ah, tmp_path, with_manifest(ah, device_count=37))
    assert ah.rules(detail["hits"]) == ["source_manifest_mismatch"]
    assert detail["hits"][0].where == "source_manifest.device_count"       # 10절(78ebbbd 보강)
    assert detail["rejected_gates"] == (GATE,)
    msg = detail["hits"][0].message
    assert has_number(msg, 37) and has_number(msg, 4), msg


def test_passive_count_mismatch(ah, tmp_path):
    detail = load_rejected(ah, tmp_path, with_manifest(ah, passive_count=29))
    assert ah.rules(detail["hits"]) == ["source_manifest_mismatch"]
    assert detail["hits"][0].where == "source_manifest.passive_count"      # 10절(78ebbbd 보강)
    msg = detail["hits"][0].message
    assert has_number(msg, 29) and has_number(msg, 3), msg


def test_passive_count_excludes_ideal_sources(ah, tmp_path):
    """passive_count 에 이상원(Ib)을 더해 4 로 선언 -> 불일치(10절 '이상원 제외')."""
    detail = load_rejected(ah, tmp_path, with_manifest(ah, passive_count=4))
    assert ah.rules(detail["hits"]) == ["source_manifest_mismatch"]


def test_device_count_counts_mos_only_not_sources(ah, tmp_path):
    """device_count 에 이상원을 더해 5 로 선언 -> 불일치(netlist MOS 수만)."""
    detail = load_rejected(ah, tmp_path, with_manifest(ah, device_count=5))
    assert ah.rules(detail["hits"]) == ["source_manifest_mismatch"]


def test_both_counts_mismatch_all_reported(ah, tmp_path):
    """두 개수 모두 틀림 -> 위반은 전부 모은다(0절). 모든 hit 가 mismatch 이고 네 수가 메시지 어딘가에 있다."""
    detail = load_rejected(ah, tmp_path, with_manifest(ah, device_count=37, passive_count=29))
    rules = ah.rules(detail["hits"])
    assert rules == ["source_manifest_mismatch"] * 2
    assert sorted(h.where for h in detail["hits"]) == ["source_manifest.device_count", "source_manifest.passive_count"]
    text = " ".join(h.message for h in detail["hits"])
    for n in (37, 4, 29, 3):
        assert has_number(text, n), (n, text)


def test_mismatch_follows_netlist_edit(ah, tmp_path):
    """MOS 하나를 더 넣고 manifest 는 그대로 -> 불일치(대조가 실제 개수를 본다, 고정값이 아님)."""
    doc = with_manifest(ah)
    doc["netlist"].append({"name": "Mfx5", "kind": "nmos", "drain": "n_outp", "gate": "n_mid", "source": "rail_lo"})
    detail = load_rejected(ah, tmp_path, doc)
    assert ah.rules(detail["hits"]) == ["source_manifest_mismatch"]
    assert has_number(detail["hits"][0].message, 5)


# ---------------------------------------------------------------------------------------------------- 형식
@pytest.mark.parametrize("value", [[], "x", 3, None], ids=["list", "str", "int", "null"])
def test_source_manifest_type(ah, tmp_path, value):
    doc = ah.base()
    doc["source_manifest"] = value
    detail = load_rejected(ah, tmp_path, doc)
    assert ah.rules(detail["hits"]) == ["source_manifest_type"], detail["hits"]
    assert detail["rejected_gates"] == (GATE,)


@pytest.mark.parametrize("missing", ["figure", "device_count", "passive_count"])
def test_source_manifest_key_missing(ah, tmp_path, missing):
    doc = with_manifest(ah)
    del doc["source_manifest"][missing]
    detail = load_rejected(ah, tmp_path, doc)
    assert "source_manifest_key" in ah.rules(detail["hits"]), detail["hits"]
    assert set(ah.rules(detail["hits"])) <= {"source_manifest_key"}


@pytest.mark.parametrize("figure", ["", 12, None, ["p.3"]], ids=["empty", "int", "null", "list"])
def test_source_manifest_figure(ah, tmp_path, figure):
    detail = load_rejected(ah, tmp_path, with_manifest(ah, figure=figure))
    assert ah.rules(detail["hits"]) == ["source_manifest_figure"], detail["hits"]


@pytest.mark.parametrize("field", ["device_count", "passive_count"])
@pytest.mark.parametrize("value", [True, False, -1, "4", 2.5, None], ids=["true", "false", "neg", "str", "frac", "null"])
def test_source_manifest_count(ah, tmp_path, field, value):
    detail = load_rejected(ah, tmp_path, with_manifest(ah, **{field: value}))
    assert ah.rules(detail["hits"]) == ["source_manifest_count"], detail["hits"]


# ---------------------------------------------------------------------------------------------------- 건너뛰기
def test_skipped_when_devices_rejected(ah, tmp_path):
    doc = with_manifest(ah, device_count=37)
    doc["netlist"][0]["n_fingers"] = 4                 # devices element_unknown_key (3.4)
    detail = load_rejected(ah, tmp_path, doc)
    assert GATE not in detail["rejected_gates"]
    assert not [h for h in detail["hits"] if h.rule.startswith("source_manifest")]
    assert set(detail["not_evaluated"]) <= NOT_EVALUATED_NAMES


def test_skipped_when_passives_rejected(ah, tmp_path):
    doc = with_manifest(ah, passive_count=29)
    doc["passive_elements"][0]["terminals"] = ["n_outp"]  # passives terminals (3.6)
    detail = load_rejected(ah, tmp_path, doc)
    assert GATE not in detail["rejected_gates"]
    assert not [h for h in detail["hits"] if h.rule.startswith("source_manifest")]
    assert set(detail["not_evaluated"]) <= NOT_EVALUATED_NAMES


# ---------------------------------------------------------------------------------------------------- 지문
def test_manifest_not_in_connectivity_fp(ah, tmp_path):
    a = load_topology(ah.write(tmp_path, ah.base(), "a"))
    b = load_topology(ah.write(tmp_path, with_manifest(ah), "b"))
    c = load_topology(ah.write(tmp_path, with_manifest(ah, figure="another figure, p.9"), "c"))
    assert a.connectivity_fp == b.connectivity_fp == c.connectivity_fp
    assert len({a.file_sha256, b.file_sha256, c.file_sha256}) == 3


# ---------------------------------------------------------------------------------------------------- 닫힌 어휘·공개 이름 (10절, 78ebbbd 보강)
def test_unknown_key_rejected(ah, tmp_path):
    """`_` 접두 아닌 알 수 없는 키는 거부(닫힌 어휘). rule 이름은 계약이 정하지 않아 gate·형식 규칙 집합으로 판정."""
    doc = with_manifest(ah)
    doc["source_manifest"]["page"] = 3
    detail = load_rejected(ah, tmp_path, doc)
    assert detail["rejected_gates"] == (GATE,)
    assert len(detail["hits"]) == 1
    assert detail["hits"][0].rule in {"source_manifest_key", "source_manifest_type"}, detail["hits"]


def test_underscore_key_accepted(ah, tmp_path):
    doc = with_manifest(ah)
    doc["source_manifest"]["_comment"] = "comment keys are outside the vocabulary but accepted"
    load_topology(ah.write(tmp_path, doc))


def test_public_export():
    """10절: 공개 이름 check_source_manifest 가 __all__ 에 있고 호출 가능하다."""
    assert "check_source_manifest" in authoring.__all__
    assert callable(authoring.check_source_manifest)
