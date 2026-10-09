"""search/start_values.py -- 출발 구간 값 형식·어휘 (설계 41 §6.6 보고 표, search CONTRACT U13).

oracle:
- (a) PM_FLOOR_DEG: 2극점 근사 PM = atan(f_np/GBW) 에서 비주극점이 UGF 에 놓이는 f_np = GBW 의 값 = atan(1) = 45° (CONTRACT 주장의 수치 확인;
  설계 41 §6.3 은 PM 목표가 없으면 비활성이라 쓴다 -- 이견은 test_iv_speed·보고).
- (d) 41 §6.6 보고 표 열: device, gm_id_lo/hi/chosen, L_lo/hi/chosen, bin, I_start, sources, inactive_reasons, conflicts.
- 경계 식 이름·비활성 사유는 서로 다른 문자열이어야 보고에서 구별된다. 값 형식은 불변(frozen).
"""
import dataclasses
import math

import pytest

from gmid_engine.search import start_values as sv


def test_pm_floor_is_atan_one():
    assert sv.PM_FLOOR_DEG == pytest.approx(math.degrees(math.atan(1.0)), abs=0.0)
    assert sv.PM_FLOOR_DEG == pytest.approx(45.0, abs=1e-12)


def test_report_row_has_design_columns():
    fields = [f.name for f in dataclasses.fields(sv.StartRow)]
    for name in ("device", "gm_id_lo", "gm_id_hi", "gm_id_chosen", "l_lo", "l_hi", "l_chosen", "bin", "i_start", "sources",
                 "inactive_reasons", "conflicts"):
        assert name in fields


def test_vocabulary_strings_distinct():
    src = [v for k, v in vars(sv).items() if k.startswith("SRC_")]
    why = [v for k, v in vars(sv).items() if k.startswith("WHY_")]
    assert len(src) == len(set(src)) and len(src) >= 15
    assert len(why) == len(set(why))


def test_value_types_are_frozen():
    b = sv.Bound("gm_id", "lo", sv.SRC_LUT_RANGE, 5.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        b.value = 6.0
    r = sv.StartRung(1.0, (), (), ())
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.t = 0.5
