"""`verified_by` -- 설계 40 §3.8-6('레지스트리 항목에 verified_by·model_error_ref, 오라클 대조 결과를 derived.model_error_<metric> 에'),
DEC-72·DEC-90 (3), 체크리스트 D-GB8c, 계약 10.0.

oracle:
* (d) 레지스트리 전수: 모든 metric 이 출처 종류 셋 중 하나와 `model_error_<metric>` 참조를 갖는다(표를 빠뜨리지 않는다).
* (d) 설계 40 §3.8-8·§10.2: offset_in_sigma_mv 는 오라클 Monte-Carlo, 스윙·ICMR 은 오라클 `.dc` 스윕 -> spice_oracle.
  offset_excess 는 구조 가드(엔진 전용). measure 이름은 오라클 측 실제 키(`oracle_offset_mc`·`oracle_swing` 의 출력)와 같아야 한다 --
  이 test 는 오라클 파일을 import 하지 않고 소스 텍스트에서 키 문자열이 있는지만 본다.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from gmid_engine.metrics import VerifiedBy, metric_registry, verified_by

KINDS = {"spice_oracle", "spice_unverifiable", "engine_only"}
ORACLE = Path(__file__).resolve().parents[3] / "tools" / "spice_oracle"


@pytest.mark.parametrize("name", sorted(metric_registry()))
def test_every_registry_metric_has_source(name):
    got = verified_by(name)
    assert isinstance(got, VerifiedBy) and got.metric == name
    assert got.kind in KINDS
    assert got.model_error_ref == "model_error_" + name
    assert (got.measure is None) == (got.kind != "spice_oracle")


def test_unknown_metric_key_error():
    with pytest.raises(KeyError):
        verified_by("gain_db")
    with pytest.raises(KeyError):
        verified_by("noise_th_in_v2hz")              # 계산 대기(레지스트리 밖) 이름


@pytest.mark.parametrize("name,kind", [("offset_in_sigma_mv", "spice_oracle"), ("swing_out_v", "spice_oracle"),
                                       ("icmr_v", "spice_oracle"), ("icm_margin_v", "spice_oracle"),
                                       ("offset_excess", "engine_only"), ("gain_ss_db", "spice_oracle")])
def test_design_sources(name, kind):
    assert verified_by(name).kind == kind


@pytest.mark.parametrize("name", ["offset_in_sigma_mv", "swing_out_v", "icmr_v", "icm_margin_v"])
def test_oracle_measure_key_exists_in_oracle_sources(name):
    measure = verified_by(name).measure
    text = "".join(p.read_text(encoding="utf-8") for p in ORACLE.glob("oracle_*.py"))
    assert '"%s"' % measure in text or "'%s'" % measure in text, (name, measure)
