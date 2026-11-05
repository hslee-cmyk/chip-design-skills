"""`sat_threshold(memo, kind, w_key, L, vgs, vds, vsb) -> SatBound` -- interface card 20261104-hcs §1 (S1 S2 S3 S3b S8).

oracle:
* (식) card §1 표: 위에서 아래로 첫 맞는 행(1 역방향 VDS / 2 열 없음 / 3 정의역 밖 / 4 tol None / 5 값).
* (손) r4 합성 LUT 의 VDSAT 닫힌 식(sizing conftest `r4_vdsat_at`·`r4_tol_vdsat`, npz 열 직접).
* (a) S2: 두 bin LUT(lut conftest 중점 toy)의 tol 셀이 bin 마다 다르다는 구성 -- 앵커 bin 셀 값이 감싼 앵커 최댓값과 다르다.
  기대값 출처는 lut 공개 함수 `tol_vdsat_table(...).at` 과 `vdsat`(card §1 이 허용, 별도 test 대상).
* S8: 엔진 소스의 삭제 이름 0 / metrics·봉인 쪽 `vdsat`·`tol_vdsat_table` 직접 호출 0 (call_sites 도구).
"""
import dataclasses
import tokenize

import pytest

import gmid_engine.lut as lutmod
from gmid_engine.lut import tol_vdsat_table, vdsat

from sizing.call_sites import calls_of, engine_sources
from sizing.conftest import R4_L, W_KEY, r4_tol_vdsat, r4_vdsat_at, r4_vdsat_grid, write_r4_lut

from .conftest import BIN_L, MID_L_SOURCE, mid_point_arrays, new_memo
from .hcs_cases import lookups, memo_of

REVERSE = "reverse_vds"
UNAVAILABLE = "vdsat_column_unavailable"
DOMAIN = "lut_domain"


@pytest.fixture(scope="module")
def lut_col(tmp_path_factory):
    return write_r4_lut(tmp_path_factory.mktemp("st_col"))


@pytest.fixture(scope="module")
def lut_nocol(tmp_path_factory):
    return write_r4_lut(tmp_path_factory.mktemp("st_nocol"), vdsat=())


def test_sat_threshold_reason_constants_and_value_type():
    assert (lutmod.REASON_REVERSE_VDS, lutmod.REASON_VDSAT_COLUMN_UNAVAILABLE, lutmod.REASON_LUT_DOMAIN,
            lutmod.REASON_OFF_DECLARED) == (REVERSE, UNAVAILABLE, DOMAIN, "off_declared")
    sb = lutmod.SatBound(0.25, 0.5, None)
    assert dataclasses.is_dataclass(sb) and type(sb).__dataclass_params__.frozen
    assert [f.name for f in dataclasses.fields(sb)] == ["vdsat_v", "tol_v", "reason"]
    assert sb == lutmod.SatBound(0.25, 0.5, None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        sb.vdsat_v = 0.0


# ---- S1 행 1: vds < 0 -> reverse_vds, LUT 조회 0 ----------------------------------------------------------------------------

@pytest.mark.parametrize("kind", ["nmos", "pmos"])
@pytest.mark.parametrize("vds", [-0.25, -1e-12])
def test_sat_threshold_reverse_vds_is_a_reason_and_costs_no_lookup(lut_col, kind, vds):
    """oracle (식) 행 1. VDS 격자 간격 0.25 만큼 음수·0 바로 아래. 새 memo 의 모든 영역 계수가 전후 같다(조회 0)."""
    m = memo_of(lut_col)
    before = lookups(m)
    sb = lutmod.sat_threshold(m, kind, W_KEY, 1e-6, 0.5, vds, 0.0)
    assert (sb.vdsat_v, sb.tol_v, sb.reason) == (None, None, REVERSE)
    assert lookups(m) == before


def test_sat_threshold_reverse_vds_outranks_missing_column_and_domain(lut_nocol, lut_col):
    """행 1 이 행 2·3 보다 먼저: 열 없는 LUT 도, 축 밖 vgs 도 vds < 0 이면 reverse_vds."""
    assert lutmod.sat_threshold(memo_of(lut_nocol), "nmos", W_KEY, 1e-6, 0.5, -0.25, 0.0).reason == REVERSE
    assert lutmod.sat_threshold(memo_of(lut_col), "nmos", W_KEY, 1e-6, 2.25, -0.25, 0.0).reason == REVERSE


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_sat_threshold_vds_zero_is_not_reverse(lut_col, kind):
    """경계: vds = 0 은 역방향이 아니다(행 4·5)."""
    sb = lutmod.sat_threshold(memo_of(lut_col), kind, W_KEY, 1e-6, 0.5, 0.0, 0.0)
    assert sb.reason is None
    assert sb.vdsat_v == pytest.approx(r4_vdsat_at(kind, 1e-6, 0.5, 0.0), rel=1e-12)


# ---- 행 5 / 행 4 ---------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("kind", ["nmos", "pmos"])
@pytest.mark.parametrize("L", R4_L)
@pytest.mark.parametrize("vgs,vsb", [(0.5, 0.0), (0.3125, 0.125), (1.0, 0.5)])
def test_sat_threshold_value_row_matches_closed_form(lut_col, kind, L, vgs, vsb):
    """oracle (손) conftest 닫힌 식: vdsat = r4_vdsat_at, tol = r4_tol_vdsat(모든 셀 같음)."""
    sb = lutmod.sat_threshold(memo_of(lut_col), kind, W_KEY, L, vgs, 1.5, vsb)
    assert sb.reason is None
    assert sb.vdsat_v == pytest.approx(r4_vdsat_at(kind, L, vgs, vsb), rel=1e-12)
    assert sb.tol_v == pytest.approx(r4_tol_vdsat(kind), rel=1e-9)


def test_sat_threshold_tol_cell_none_keeps_value(tmp_path):
    """행 4: VGS·VDS·VS 축이 2점이면 tol 셀이 None(내부 격자점 없음) -> 값은 있고 tol_v None, 사유 None."""
    lut = write_r4_lut(tmp_path, grids=(R4_L, (0.0, 2.0), (0.0, 2.0), (0.0, 2.0)))
    sb = lutmod.sat_threshold(memo_of(lut), "nmos", W_KEY, 1e-6, 0.0, 0.5, 0.0)
    assert (sb.reason, sb.tol_v) == (None, None)
    assert sb.vdsat_v == pytest.approx(r4_vdsat_grid("nmos", 0, 0.0, 0.0), rel=1e-12)   # 격자점: 0.0625 (손)


# ---- S3 행 2: VDSAT 열 없음 (0 이 아니다) --------------------------------------------------------------------------------

@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_sat_threshold_column_unavailable_is_a_reason_not_zero(lut_nocol, kind):
    sb = lutmod.sat_threshold(memo_of(lut_nocol), kind, W_KEY, 1e-6, 0.5, 1.5, 0.0)
    assert (sb.vdsat_v, sb.tol_v, sb.reason) == (None, None, UNAVAILABLE)
    assert sb.vdsat_v != 0.0


# ---- S3b 행 3: 정의역 밖 ----------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("args", [(1e-6, 2.25, 1.5, 0.0), (1e-6, 0.5, 2.25, 0.0), (1e-6, 0.5, 1.5, 2.5), (5e-6, 0.5, 1.5, 0.0)],
                         ids=["vgs_out", "vds_out", "vsb_out", "L_out"])
def test_sat_threshold_axis_outside_is_lut_domain(lut_col, args):
    sb = lutmod.sat_threshold(memo_of(lut_col), "nmos", W_KEY, *args)
    assert (sb.vdsat_v, sb.tol_v, sb.reason) == (None, None, DOMAIN)


# ---- 다시 던지는 것 -------------------------------------------------------------------------------------------------------

def test_sat_threshold_missing_slice_is_keyerror_not_a_reason(lut_col):
    with pytest.raises(KeyError):
        lutmod.sat_threshold(memo_of(lut_col), "nmos", 777, 1e-6, 0.5, 1.5, 0.0)


# ---- S2 두 bin: tol 은 앵커 bin 셀 (감싼 앵커 최댓값 아님) -------------------------------------------------------------------

@pytest.mark.parametrize("k", [0, 1])
def test_sat_threshold_tol_is_the_anchor_bin_cell_not_wrapped_maximum(mid_toy_build, k):
    """중점 toy: L 앵커 BIN_L[1](1.5 µm, bin A 내부) 의 셀은 L 방향 LOO 가 크고, 앵커 BIN_L[2](2 µm, bin A 끝) 의 셀은 0 수준
    (lut conftest·test_vdsat_tolerance 의 손계산: 0.0125·(1 + d)/4 대 ~0). 2 µm 에서 tol_v 는 그 앵커 셀 값이다 --
    감싼 두 앵커(1.5, 2 µm) 최댓값이면 앞 셀 값이 된다(옛 tol_vdsat_max 꼴)."""
    mt = mid_toy_build("hcs_s2", mid=mid_point_arrays((3.5e-6, 7.5e-6), l_source=MID_L_SOURCE))
    m = new_memo(mt.load())
    z = mt.slice_arrays[0]
    t = tol_vdsat_table(m, "nmos", 100)
    L = BIN_L[2]
    vgs, vsb, vds = float(z["VGS"][1]), float(z["VS"][1]), float(z["VDS"][k])
    cell_anchor, cell_wrapped = t.cells[2][k].vdsat_v, t.cells[1][k].vdsat_v
    assert cell_wrapped > cell_anchor                                  # 입력 검사: 두 bin 셀이 다르다
    sb = lutmod.sat_threshold(m, "nmos", 100, L, vgs, vds, vsb)
    assert sb.reason is None
    assert sb.tol_v == cell_anchor and sb.tol_v == t.at(L, vds)
    assert sb.tol_v != max(cell_anchor, cell_wrapped)
    assert sb.vdsat_v == vdsat(m, "nmos", 100, L, vgs, vds, vsb)


# ---- S8 소스 훑기 -----------------------------------------------------------------------------------------------------------

REMOVED_NAMES = ("_tol_vdsat_max", "_tol_vdsat_grid", "tol_vdsat_max", "_vds_floor", "tol_vdsat")


def _names_in(path):
    """토큰으로 읽는다: 식별자(NAME)와 '이름만 든 문자열'(derived 이름 키). 주석·긴 문장 문자열(docstring)은 보지 않는다."""
    found = set()
    with open(path, "rb") as f:
        for tok in tokenize.tokenize(f.readline):
            if tok.type == tokenize.NAME and tok.string in REMOVED_NAMES:
                found.add(tok.string)
            elif tok.type == tokenize.STRING and tok.string.strip("'\"") in REMOVED_NAMES:
                found.add(tok.string.strip("'\""))
    return found


def test_sat_threshold_removed_names_absent_from_engine_sources():
    hits = {(p.name, n) for p in engine_sources() for n in _names_in(p)}
    assert hits == set()


def test_sat_threshold_no_direct_vdsat_lookup_in_metrics_or_seal_region():
    """metrics/ (ss_off_gate 포함)와 봉인 지역(dc_seal_region 이 있는 파일·함수)에서 lut `vdsat`·`tol_vdsat_table` 직접 호출 0."""
    bad = set()
    for name in ("vdsat", "tol_vdsat_table"):
        for rel, fn in calls_of(name):
            if rel.startswith("metrics/") or "seal_region" in rel or "seal_region" in fn:
                bad.add((name, rel, fn))
    assert bad == set()

