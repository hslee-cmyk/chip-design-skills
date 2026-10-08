"""`cm_partition` -- CM 루프 구동자/소비자 구조 분류 (metrics CONTRACT 7.11 [6a6e4c7], SPEC_CONTRACT 3절 cm_loop, S-21·S-29·S-31).

공개 소비 경로 `default_views(topology, ()).cm_loop`(ViewDecl cm_output 의 cuts = 구동자)로 확인한다 -- `cm_partition` 자체의 인자 형식
(outputs·mos·two_terminals·rails·source_nets)은 계약에 적혀 있지 않아 직접 호출하지 않는다(보고 항목).
회로: tests/metrics/conftest.py 의 합성 CMFB 변형(cm_variant, test 작성자 설계), 기대 구동자 = 7.11 규칙을 test 작성자가 손으로 적용한
CM_DRIVERS(oracle (d)+(a), 각 변형 주석에 도달 경로). cuts 순서는 계약이 정하지 않아 집합으로 비교한다.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gmid_engine.authoring import ViewDecl, default_views, load_topology

from metrics.conftest import cm_topology

_LIB = Path(__file__).resolve().parents[3] / "assets" / "library"
_PILOT = "current_reuse_telescopic_ota"
_CM_W = (("om", 0.5), ("op", 0.5))


def _variant_td(tmp_path, variant):
    doc, v = cm_topology("cmp_" + variant, variant)
    p = tmp_path / ("cmp_%s.topology.json" % variant)
    p.write_text(json.dumps(doc), encoding="utf-8")
    return load_topology(str(p)), doc, v


def _want_cuts(v):
    out = set()
    for m in v["mos"]:
        if m[0] in v["drivers"]:
            (o,) = [n for n in (m[2], m[4]) if n in ("op", "om")]
            out.add((m[0], o))
    return out


@pytest.mark.parametrize("variant", ["direct", "ref_rc", "err_amp", "sf_buffer", "dda", "triode", "cascode_ideal", "degen",
                                     "pass_device"])
def test_cm_partition_drivers_by_hand_s29(tmp_path, variant):
    """S-29: 명확한 변형 -- cm_output 뷰, 가중 (om ½, op ½), cuts = 손 분류 구동자 (MOS, 출력 넷). triode 평균(Mt)은 소비자(레일 미도달),
    출력 캐스코드(이상원 단자 = 레일)·소스 축퇴(수동소자 경유 레일)는 구동자, 출력 사이 통과 소자(d·s 모두 출력)는 어느 쪽도 아님."""
    td, _, v = _variant_td(tmp_path, variant)
    got = default_views(td, ()).cm_loop
    assert isinstance(got, ViewDecl), got
    assert got.mode == "cm_output" and tuple(got.weights) == _CM_W
    assert set(got.cuts) == _want_cuts(v) and len(got.cuts) == len(v["drivers"])


@pytest.mark.parametrize("variant", ["ambiguous", "diode_load"])
def test_cm_partition_ambiguous_stops_s29(tmp_path, variant):
    """S-29: 모호(감지 넷이 이상원 단자 = 레일이면서 gate 가 걸림 / 후보 gate 가 출력 넷) -> 뷰 없음(사유 문자열)."""
    td, _, _ = _variant_td(tmp_path, variant)
    got = default_views(td, ()).cm_loop
    assert isinstance(got, str) and got


def test_pilot_cm_cuts_s21():
    """S-21: 파일럿 구동자 = M15·M16(Vom)·M25·M26(Vop) -- topology 를 손으로 읽음(M15 pmos Vom–vdd, M16 nmos Vom–gnd, M25·M26 대칭)."""
    v = default_views(load_topology(str(_LIB / (_PILOT + ".topology.json"))), ()).cm_loop
    assert v.mode == "cm_output" and tuple(v.weights) == (("Vom", 0.5), ("Vop", 0.5))
    assert set(v.cuts) == {("M15", "Vom"), ("M16", "Vom"), ("M25", "Vop"), ("M26", "Vop")}
