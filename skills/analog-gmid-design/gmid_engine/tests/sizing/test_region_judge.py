"""공용 영역 판정 `judge_region(device, declared, current, vds, vdsat) -> RegionJudgment` -- interface card 20261104-eo1r4-sf1l §1 표.

oracle (식): card §1 표 10행을 이 파일에서 행마다 손으로 옮겼다(표 첫 맞는 행 순서). 값은 2진 분수(0.125·0.25 V)라 비교가 정확하다.
피검 함수로 기대값을 만들지 않는다. 수치 문턱 없음 -- current = 0 정확히, VDS = vdsat 정확히를 경계 양쪽(nextafter)으로 건다.
"""
import dataclasses
import inspect
import math

import pytest

from gmid_engine.sizing import OUT_OF_DOMAIN, RegionJudgment, judge_region

VDSAT = 0.25
BELOW = 0.125          # VDS < vdsat
ABOVE = 0.5            # VDS > vdsat
POS = 1e-6             # current > 0

# (행, declared, current, vds, vdsat, actual, mismatch)  -- card §1 표
ROWS = [
    # 1: off -> not_judged (무관)
    (1, "off", POS, ABOVE, VDSAT, "not_judged", False),
    (1, "off", 0.0, BELOW, VDSAT, "not_judged", False),
    (1, "off", -POS, -BELOW, OUT_OF_DOMAIN, "not_judged", False),
    (1, "off", POS, ABOVE, None, "not_judged", False),
    # 2: None/triode, current <= 0 -> cutoff (VDS·vdsat 무관)
    (2, None, 0.0, ABOVE, VDSAT, "cutoff", True),
    (2, None, -POS, BELOW, VDSAT, "cutoff", True),
    (2, "triode", 0.0, ABOVE, VDSAT, "cutoff", True),
    (2, "triode", -POS, -BELOW, OUT_OF_DOMAIN, "cutoff", True),
    (2, None, 0.0, ABOVE, None, "cutoff", True),
    # 3: None, current > 0, VDS < 0 -> triode, mismatch (vdsat 값 안 봄)
    (3, None, POS, -BELOW, VDSAT, "triode", True),
    (3, None, POS, -BELOW, OUT_OF_DOMAIN, "triode", True),
    (3, None, POS, -BELOW, None, "triode", True),
    (3, None, POS, -BELOW, -ABOVE, "triode", True),
    # 4: triode, current > 0, VDS < 0 -> triode, 일치
    (4, "triode", POS, -BELOW, VDSAT, "triode", False),
    (4, "triode", POS, -BELOW, OUT_OF_DOMAIN, "triode", False),
    (4, "triode", POS, -BELOW, None, "triode", False),
    # 5: None/triode, current > 0, vdsat OUT_OF_DOMAIN (VDS >= 0) -> out_of_domain, mismatch
    (5, None, POS, ABOVE, OUT_OF_DOMAIN, "out_of_domain", True),
    (5, "triode", POS, BELOW, OUT_OF_DOMAIN, "out_of_domain", True),
    (5, None, POS, 0.0, OUT_OF_DOMAIN, "out_of_domain", True),
    # 6: None/triode, current > 0, vdsat None (VDS >= 0) -> unresolved, 불일치 아님
    (6, None, POS, ABOVE, None, "unresolved", False),
    (6, "triode", POS, BELOW, None, "unresolved", False),
    (6, None, POS, 0.0, None, "unresolved", False),
    # 7: None, VDS >= vdsat -> saturation, 일치 (등호 포함)
    (7, None, POS, ABOVE, VDSAT, "saturation", False),
    (7, None, POS, VDSAT, VDSAT, "saturation", False),
    (7, None, POS, 0.0, 0.0, "saturation", False),
    # 8: None, VDS < vdsat -> triode, mismatch
    (8, None, POS, BELOW, VDSAT, "triode", True),
    (8, None, POS, 0.0, VDSAT, "triode", True),
    # 9: triode, VDS < vdsat -> triode, 일치
    (9, "triode", POS, BELOW, VDSAT, "triode", False),
    (9, "triode", POS, 0.0, VDSAT, "triode", False),
    # 10: triode, VDS >= vdsat -> saturation, mismatch (등호 포함)
    (10, "triode", POS, ABOVE, VDSAT, "saturation", True),
    (10, "triode", POS, VDSAT, VDSAT, "saturation", True),
    (10, "triode", POS, 0.0, 0.0, "saturation", True),
]


def _ids(rows):
    return ["row%d-%s-i%s-v%s-s%s" % (r[0], r[1], r[2], r[3], "OOD" if r[4] is OUT_OF_DOMAIN else r[4]) for r in rows]


def test_out_of_domain_constant_is_the_string():
    assert OUT_OF_DOMAIN == "out_of_domain"


@pytest.mark.parametrize("row", ROWS, ids=_ids(ROWS))
def test_region_judge_table_three_fields(row):
    """표 10행 전부, RegionJudgment 3칸(device·declared·actual) 정확 일치 -- bool 만 내면 red."""
    _, declared, current, vds, vdsat, actual, _mm = row
    j = judge_region("Mx", declared, current, vds, vdsat)
    assert isinstance(j, RegionJudgment)
    assert (j.device, j.declared, j.actual) == ("Mx", declared, actual)


def test_region_judge_mixed_devices_do_not_interact():
    """소자 셋(선언 없음 꺼짐·triode 꺼짐·off)을 한 평가에 섞어도 소자별로 독립(상태 없음)."""
    js = [judge_region("Mu", None, 0.0, ABOVE, VDSAT),
          judge_region("Mt", "triode", 0.0, ABOVE, VDSAT),
          judge_region("Mo", "off", 0.0, ABOVE, VDSAT),
          judge_region("Mu", None, POS, ABOVE, VDSAT)]
    assert [(j.device, j.declared, j.actual) for j in js] == [
        ("Mu", None, "cutoff"), ("Mt", "triode", "cutoff"), ("Mo", "off", "not_judged"), ("Mu", None, "saturation")]


# ---- T-R2: 경계(수치 문턱 없음), LUT 없이 호출, 서명


def test_region_judge_current_zero_exactly_is_cutoff_and_smallest_positive_is_not():
    tiny = math.ulp(0.0)                                   # 0 바로 위 양수
    assert judge_region("M", None, 0.0, ABOVE, VDSAT).actual == "cutoff"
    assert judge_region("M", None, -tiny, ABOVE, VDSAT).actual == "cutoff"
    assert judge_region("M", None, tiny, ABOVE, VDSAT).actual == "saturation"
    assert judge_region("M", "triode", 0.0, BELOW, VDSAT).actual == "cutoff"
    assert judge_region("M", "triode", tiny, BELOW, VDSAT).actual == "triode"


@pytest.mark.parametrize("declared,below_actual,at_actual,above_actual", [
    (None, "triode", "saturation", "saturation"),
    ("triode", "triode", "saturation", "saturation"),
])
def test_region_judge_vds_equals_vdsat_both_sides(declared, below_actual, at_actual, above_actual):
    """VDS = vdsat 정확히 = saturation 쪽, 1 ulp 아래 = triode (경계 양쪽)."""
    below = math.nextafter(VDSAT, 0.0)
    above = math.nextafter(VDSAT, 1.0)
    assert judge_region("M", declared, POS, below, VDSAT).actual == below_actual
    assert judge_region("M", declared, POS, VDSAT, VDSAT).actual == at_actual
    assert judge_region("M", declared, POS, above, VDSAT).actual == above_actual


def test_region_judge_vds_zero_exactly_is_not_reverse():
    """VDS = 0 정확히는 VDS < 0 이 아니다(행 3·4 아님) -> vdsat 비교로 넘어간다. 바로 아래 음수는 행 3·4."""
    neg = -math.ulp(0.0)
    assert judge_region("M", None, POS, 0.0, VDSAT).actual == "triode"          # 행 8 (0 < vdsat)
    assert judge_region("M", None, POS, neg, OUT_OF_DOMAIN).actual == "triode"   # 행 3 (OOD 무시)
    assert judge_region("M", None, POS, 0.0, OUT_OF_DOMAIN).actual == "out_of_domain"   # 행 5
    assert judge_region("M", "triode", POS, neg, None).actual == "triode"        # 행 4 (None 무시)
    assert judge_region("M", "triode", POS, 0.0, None).actual == "unresolved"   # 행 6


def test_region_judge_needs_no_lut_object_and_signature_has_no_threshold():
    """함수는 LUT 를 부르지 않는다: 서명 칸 5개뿐(I_off·tol·lut 칸 없음)."""
    params = list(inspect.signature(judge_region).parameters)
    assert params == ["device", "declared", "current", "vds", "vdsat"]
    for banned in ("lut", "i_off", "tol", "memo", "access"):
        assert not any(banned in p for p in params)


def test_region_judge_result_is_frozen():
    j = judge_region("M", None, POS, ABOVE, VDSAT)
    with pytest.raises(dataclasses.FrozenInstanceError):
        j.actual = "triode"
