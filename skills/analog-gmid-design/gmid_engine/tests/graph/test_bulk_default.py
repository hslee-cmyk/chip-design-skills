"""graph/bulk_default.py -- `s1_bulk` 블록: device.bulk 와 정지 검사(계약 4.2, 7.1, 7.3).

기대 bulk 는 JsonAgg.expected_bulk(계약 4.2 우선순위 표를 test 쪽에서 JSON 에 직접 적용)와 계약 7.1 표 숫자.
'이름이 아니라 전위로' 는 레일 이름 바꾸기·이름과 전위 뒤집기·원점 이동 변형으로 확인한다.
정지 변형은 계약 7.3 의 메모리 변형을 그대로 재현한다.
"""
from __future__ import annotations

import collections

import pytest

from gmid_engine.core import ComputeBlock, StructureUnresolvedError, exit_code_for
from gmid_engine.graph import (
    BRANCH_MULTI_DOMAIN,
    BRANCH_POTENTIAL_TIE,
    S1_BULK_WRITER,
    UNSUPPORTED_RULE_BRANCH,
    BulkResult,
    build_s1,
    s1_bulk,
)

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)

# 9회로 전부(2026-10-07 topology 정정 b9c7042 뒤 모두 load 통과) -- JSON 직접 집계 대조용
NINE = tuple(sorted(SIX + ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")))
# 계약 7.1 표 bulk 열: (origin, reason) -> {net: 개수}
TABLE_BULK = {
    "common_gate_amplifier": {("gnd", "default_rule"): 2, ("vdd", "default_rule"): 1},
    "current_reuse_telescopic_ota": {("gnd", "default_rule"): 24, ("vdd", "default_rule"): 27},
    "ngcc_3stage_ff": {("gnd", "default_rule"): 9, ("vdd", "default_rule"): 7},
    "pushpull_follower_buffer": {("vss", "default_rule"): 3, ("vdd", "default_rule"): 3},
    "sf_pushpull_output_opamp": {("vss", "default_rule"): 11, ("vdd", "default_rule"): 11},
    "two_stage_ota_sf": {("gnd", "default_rule"): 6, ("vdd", "default_rule"): 3},   # 7.1 갱신: 사용자 확정 supplies_v
}


def _bulk(s1):
    return {k: (v.net, v.origin, v.reason) for k, v in s1.column("device", "bulk")}


def _dist(bulk):
    return dict(collections.Counter((v[0], v[1]) for v in bulk.values()))


def _stop(fn):
    with pytest.raises(StructureUnresolvedError) as ei:
        fn()
    exc = ei.value
    assert exit_code_for(exc) == 2
    assert exc.record.failure_class == "STRUCTURE_UNRESOLVED"
    d = dict(exc.record.detail)
    assert d["reason"] == UNSUPPORTED_RULE_BRANCH
    return d, exc.record.devices


# ------------------------------------------------------------------ 6회로 기대 분포


@pytest.mark.parametrize("name", SIX)
def test_library_bulk_matches_json_rule(gh, name):
    raw = gh.raw(name)
    agg = gh.agg(raw)
    sv = gh.supplies_for(name, raw)
    exp = agg.expected_bulk(sv)
    assert _dist(exp) == TABLE_BULK[name]                     # 집계를 계약 표와 교차 확인
    s1 = build_s1(gh.load_lib(name), sv)
    got = _bulk(s1)
    assert got == exp
    assert tuple(got) == tuple(sorted(agg.mos))               # MOS 레코드에만, key 정렬
    for k, _ in s1.column("device", "bulk"):
        assert isinstance(s1.value("device", k, "bulk"), BulkResult)
        assert s1.snapshot.field("device", k, "bulk").writer == S1_BULK_WRITER


def test_two_stage_ota_sf_needs_supplies(gh):
    s1 = build_s1(gh.load_lib("two_stage_ota_sf"), None)
    assert set(_bulk(s1).values()) == {(None, "undetermined", "needs_supplies_v")}
    assert len(_bulk(s1)) == 9


@pytest.mark.parametrize("name", NINE)
def test_without_supplies_every_default_device_needs_supplies(gh, name):
    agg = gh.agg(gh.raw(name))
    got = _bulk(build_s1(gh.load_lib(name), None))
    assert got == {n: (None, "undetermined", "needs_supplies_v") for n in agg.mos}


# ------------------------------------------------------------------ 이름이 아니라 전위로


def test_rail_names_renamed_same_result(gh, tmp_path):
    raw = gh.raw("pushpull_follower_buffer")
    sv = gh.supplies_for("pushpull_follower_buffer", raw)       # vdd 1.8, vss 0, agnd 0.9
    # 이름 정렬·글자가 전위와 반대 방향이 되게: 최고 전위를 'aaa', 최저를 'zzz'
    mapping = {"vdd": "aaa", "vss": "zzz", "agnd": "mmm"}
    raw2 = gh.rename_nets(raw, mapping)
    sv2 = {mapping[k]: v for k, v in sv.items()}
    base = _bulk(build_s1(gh.load_raw(tmp_path, raw), sv))
    ren = _bulk(build_s1(gh.load_raw(tmp_path, raw2, "renamed"), sv2))
    assert ren == {k: (mapping.get(v[0], v[0]),) + v[1:] for k, v in base.items()}
    assert ren == gh.agg(raw2).expected_bulk(sv2)


def test_name_says_vdd_but_potential_is_lowest(gh, tmp_path):
    # 레일 이름은 그대로, 전위만 뒤집는다: 'gnd' = 1.8, 'vdd' = 0 -> nmos 는 vdd, pmos 는 gnd.
    # 채널 레일은 여전히 {최저, 최고} 안이라 정지하지 않는다.
    raw = gh.raw("common_gate_amplifier")
    agg = gh.agg(raw)
    sv = {"vdd": 0.0, "gnd": 1.8}
    got = _bulk(build_s1(gh.load_lib("common_gate_amplifier"), sv))
    assert got == agg.expected_bulk(sv)
    assert {v[0] for n, v in got.items() if agg.mos[n]["kind"] == "nmos"} == {"vdd"}
    assert {v[0] for n, v in got.items() if agg.mos[n]["kind"] == "pmos"} == {"gnd"}


@pytest.mark.parametrize("name", ["pushpull_follower_buffer", "sf_pushpull_output_opamp",
                                  "current_reuse_telescopic_ota", "ngcc_3stage_ff"])
@pytest.mark.parametrize("offset", [-0.9, 5.0, -100.0, 0.25])
def test_origin_shift_invariant(gh, name, offset):
    doc = gh.load_lib(name)
    sv = gh.supplies_for(name)
    shifted = {k: v + offset for k, v in sv.items()}
    a = build_s1(doc, sv)
    b = build_s1(doc, shifted)
    assert a.key.supplies_v_fp != b.key.supplies_v_fp          # 다른 supplies 로 실제 다시 계산했다
    assert _bulk(a) == _bulk(b)


def test_origin_shift_pm09_vs_0_18(gh):
    # 계약 4.2: ±0.9 와 0/1.8 이 같은 넷을 고른다
    doc = gh.load_lib("ngcc_3stage_ff")
    assert _bulk(build_s1(doc, {"vdd": 0.9, "gnd": -0.9})) == _bulk(build_s1(doc, {"vdd": 1.8, "gnd": 0.0}))


# ------------------------------------------------------------------ 우선순위 1·2


def test_declared_bulk_wins_and_skips_stop_check(gh, tmp_path):
    # 모든 MOS 에 bulk 선언 -> 4번 규칙을 쓰는 소자가 없으니 전위 동률이어도 정지하지 않는다
    raw = gh.raw("pushpull_follower_buffer")
    for e in raw["netlist"]:
        e["bulk"] = "vss" if e["kind"] == "nmos" else "vdd"
    raw["netlist"][0]["bulk"] = "agnd"                            # 선언이면 레일 아무거나 그대로
    doc = gh.load_raw(tmp_path, raw)
    sv = {"vdd": 1.8, "vss": 0.0, "agnd": 0.0}                    # 동률(정지 조건) 이지만 대상 없음
    got = _bulk(build_s1(doc, sv))
    assert got == {e["name"]: (e["bulk"], "declared", None) for e in raw["netlist"]}
    assert _bulk(build_s1(doc, None)) == got                      # supplies 없어도 declared


def test_partial_declared_mixed(gh, tmp_path):
    raw = gh.raw("common_gate_amplifier")
    raw["netlist"][0]["bulk"] = "vdd"                             # nmos 에 일부러 vdd 선언
    doc = gh.load_raw(tmp_path, raw)
    agg = gh.agg(raw)
    got = _bulk(build_s1(doc, {"vdd": 1.8, "gnd": 0.0}))
    assert got == agg.expected_bulk({"vdd": 1.8, "gnd": 0.0})
    assert got[raw["netlist"][0]["name"]] == ("vdd", "declared", None)
    got_none = _bulk(build_s1(doc, None))
    assert got_none[raw["netlist"][0]["name"]] == ("vdd", "declared", None)
    assert {v for k, v in got_none.items() if k != raw["netlist"][0]["name"]} == {
        (None, "undetermined", "needs_supplies_v")}


def test_unsupported_kind_bulk_undetermined(gh, tmp_path):
    raw = gh.raw("common_gate_amplifier")
    raw["netlist"][1]["kind"] = "njfet"
    name = raw["netlist"][1]["name"]
    doc = gh.load_raw(tmp_path, raw)
    for sv in (None, {"vdd": 1.8, "gnd": 0.0}):
        got = _bulk(build_s1(doc, sv))
        assert got[name] == (None, "undetermined", "unsupported_kind")
        assert got == gh.agg(raw).expected_bulk(sv)


# ------------------------------------------------------------------ 정지: 다중 도메인 / 전위 동률 (계약 7.3)


def test_multi_domain_pushpull_nmos_source_to_agnd(gh, tmp_path):
    raw = gh.raw("pushpull_follower_buffer")
    m6 = next(e for e in raw["netlist"] if e["name"] == "M6")
    assert m6["kind"] == "nmos" and m6["source"] == "vss"
    m6["source"] = "agnd"
    agg = gh.agg(raw)
    doc = gh.load_raw(tmp_path, raw)
    d, devices = _stop(lambda: build_s1(doc, {"vdd": 1.8, "vss": 0.0, "agnd": 0.9}))
    assert d["rule_branch"] == BRANCH_MULTI_DOMAIN
    assert d["channel_rails"] == tuple(sorted(agg.channel_rails)) == ("agnd", "vdd", "vss")
    assert d["bulk_rails"] == ("vss", "vdd")
    assert d["outside_rails"] == ("agnd",)
    assert devices == ("M6",)
    # supplies 없으면 검사 미적용 -> 정지하지 않는다
    assert set(_bulk(build_s1(doc, None)).values()) == {(None, "undetermined", "needs_supplies_v")}


def _sf_with_vddx(gh, potential):
    raw = gh.raw("sf_pushpull_output_opamp")
    raw["supply_nets"] = list(raw["supply_nets"]) + ["vddx"]
    pm = next(e for e in raw["netlist"] if e["kind"] == "pmos" and e["source"] == "vdd")
    pm["source"] = "vddx"
    sv = dict(gh.supplies_for("sf_pushpull_output_opamp", gh.raw("sf_pushpull_output_opamp")))
    sv["vddx"] = potential
    return raw, pm["name"], sv


def test_multi_domain_sf_extra_mid_rail(gh, tmp_path):
    raw, moved, sv = _sf_with_vddx(gh, 1.5)
    doc = gh.load_raw(tmp_path, raw)
    d, devices = _stop(lambda: build_s1(doc, sv))
    assert d["rule_branch"] == BRANCH_MULTI_DOMAIN
    assert d["bulk_rails"] == ("vss", "vdd")
    assert d["outside_rails"] == ("vddx",)
    assert devices == (moved,)


def test_multi_domain_sf_extra_rail_becomes_highest(gh, tmp_path):
    raw, moved, sv = _sf_with_vddx(gh, 3.3)
    agg = gh.agg(raw)
    on_vdd = tuple(sorted(n for n, e in agg.mos.items()
                          if e["kind"] in ("nmos", "pmos") and "vdd" in (e["drain"], e["source"])))
    assert len(on_vdd) == 6                                         # 계약 7.3 '소자 6개' 를 JSON 으로 교차 확인
    doc = gh.load_raw(tmp_path, raw)
    d, devices = _stop(lambda: build_s1(doc, sv))
    assert d["rule_branch"] == BRANCH_MULTI_DOMAIN
    assert d["bulk_rails"] == ("vss", "vddx")
    assert d["outside_rails"] == ("vdd",)
    assert devices == on_vdd


def test_capacitor_only_rail_is_not_channel_rail(gh):
    # pushpull·sf 의 agnd 는 CL(·Cc) 단자만 -- 중간 전위여도 통과(계약 7.3)
    for name in ("pushpull_follower_buffer", "sf_pushpull_output_opamp"):
        agg = gh.agg(gh.raw(name))
        assert "agnd" in agg.rails and "agnd" not in agg.channel_rails
        build_s1(gh.load_lib(name), gh.supplies_for(name))


@pytest.mark.parametrize("agnd,rails,pot", [(0.0, ("agnd", "vss"), 0.0), (1.8, ("agnd", "vdd"), 1.8)])
def test_potential_tie_pushpull(gh, agnd, rails, pot):
    doc = gh.load_lib("pushpull_follower_buffer")
    d, _ = _stop(lambda: build_s1(doc, {"vdd": 1.8, "vss": 0.0, "agnd": agnd}))
    assert d["rule_branch"] == BRANCH_POTENTIAL_TIE
    assert d["rails"] == rails
    assert d["potential"] == pot


def test_potential_tie_two_rails_equal(gh):
    doc = gh.load_lib("common_gate_amplifier")
    d, _ = _stop(lambda: build_s1(doc, {"vdd": 1.0, "gnd": 1.0}))
    assert d["rule_branch"] == BRANCH_POTENTIAL_TIE
    assert d["rails"] == ("gnd", "vdd")


def test_tie_needs_default_rule_user(gh, tmp_path):
    # 동률이어도 4번 규칙을 쓰는 MOS 가 하나도 없으면(전부 미지원 kind) 정지하지 않는다
    raw = gh.raw("common_gate_amplifier")
    for e in raw["netlist"]:
        e["kind"] = "njfet"
    doc = gh.load_raw(tmp_path, raw)
    got = _bulk(build_s1(doc, {"vdd": 1.0, "gnd": 1.0}))
    assert set(got.values()) == {(None, "undetermined", "unsupported_kind")}


@pytest.mark.parametrize("name", NINE)
def test_nine_originals_never_falsely_stop(gh, name):
    """9회로 원본 연결은 정지하지 않는다(7.3). 9회로 모두 library 원본 그대로 load 한다."""
    raw = gh.raw(name)
    sv = gh.supplies_for(name, raw)
    agg = gh.agg(raw)
    if sv is not None:                                             # JSON 으로 '정지 조건 없음' 을 먼저 확인
        lo, vmin, hi, vmax = agg.extreme_rails(sv)
        assert len(lo) == 1 and len(hi) == 1
        assert agg.channel_rails <= {lo[0], hi[0]}
    doc = gh.load_lib(name)
    got = _bulk(build_s1(doc, sv))
    assert got == agg.expected_bulk(sv)
    assert all(v[1] == "default_rule" for v in got.values())   # 9회로 모두 supplies 있음


# ------------------------------------------------------------------ 블록 형식


def test_block_declaration():
    assert isinstance(s1_bulk, ComputeBlock)
    assert s1_bulk.name == S1_BULK_WRITER
    assert set(s1_bulk.reads) == {("device", "bulk_declared"), ("device", "element_class"), ("device", "kind"),
                                  ("device", "pins"), ("node", "is_rail")}
    assert tuple(s1_bulk.writes) == (("device", "bulk"),)


def test_block_rejects_mutable_supplies(gh):
    s1 = build_s1(gh.load_lib("common_gate_amplifier"), None)
    before = s1_bulk.stats()
    with pytest.raises(TypeError):
        s1_bulk(s1.snapshot, {"vdd": 1.8, "gnd": 0.0})
    assert s1_bulk.stats().calls == before.calls
