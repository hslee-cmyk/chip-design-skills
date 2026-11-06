"""WB-1 M-5 (interface card 20261104-wb1 §8 M 표): `inversion_floor:<m>` 행의 정점은 그 소자의 슬라이스 키(`DeviceOp.w_key`)를 읽는다.

oracle (a): r4 닫힌 식. 슬라이스 키 100·200 에서 키 200 의 ID·GM·GDS 를 폭 비의 두 배로 둔다(IDu_200 = 2·IDu_100 -- 비례 슬라이스면 두 키의
값이 같아 공허하다). 그러면 키 200 슬라이스의 곡선 정점 r_peak = ln(2·I0[kind]) + LAM·vds + (VS 항, bulk = source 면 0) 이다.
c = (op.ln_idu − r_peak)·op.gm_id/tol (op·tol 은 그 스냅샷 값, search CONTRACT 3.8). 기준 키(100)로 읽으면 ln 2 만큼 달라 red.
쓰기 소자 W ≈ 2e-6 이면 키 100 m = 2, 키 200 m = 1 이 곱 동률이라 큰 키 200 이 된다(interface §2 `finger_slice`).
"""
import math

import pytest

from gmid_engine.search import constraint_rows
from gmid_engine.sizing import size_and_seal

from .conftest import GRID, I0, LAM, W_MIN, circuit_c, col, r4_ln_idu, r4_vs_term, theta_r4c
from .wb1_flow import bins_case

FACTOR = {100: 1.0, 200: 2.0}          # 키 → IDu 배율 (LUT 구성: widths 1e-6·2e-6, 2e-6 슬라이스만 배율 2)


@pytest.fixture(scope="module")
def sealed(tmp_path_factory):
    case = bins_case(tmp_path_factory.mktemp("wb1_m5"), circuit_c(), widths=(1e-6, 2e-6), idu_factor={2e-6: 2.0})
    y, v1, v2, l1 = 0.55, 0.65, 0.75, 1e-6
    idu1 = math.exp(r4_ln_idu("nmos", v1, y * 1.8, 0.0))
    i2 = 2e-6 * idu1 / l1                                           # W_M1 = I·L/IDu = 2e-6 (닫힌 식)
    ev = size_and_seal(case.dc, theta_r4c(y=y, v1=v1, v2=v2, l1=l1, i2=i2))
    return case, ev.snapshot


def test_constraints_inversion_floor_peak_reads_device_slice_key(sealed):
    case, snap = sealed
    ops, tol, coord = (col(snap, "device", f) for f in ("dc_op", "dc_tol_v", "dc_coord"))
    assert ops["M1"].W == pytest.approx(2e-6, rel=1e-3)                          # 전제 (손 유도)
    assert ops["M1"].w_key == 200 and abs(ops["M1"].vsb) < 1e-12                 # 곱 동률 -> 큰 키, bulk = source
    rows, undefined = constraint_rows(snap, case.acc, W_MIN, GRID)
    inv = {r.name: r for r in rows if r.name.startswith("inversion_floor:")}
    writers = [m for m in ops if coord[m].role == "writer" and tol.get(m) is not None and tol[m] > 0]
    assert "M1" in writers and set(inv) == {"inversion_floor:%s" % m for m in writers}
    for m in writers:
        op = ops[m]
        r_peak = math.log(FACTOR[op.w_key] * I0[op.kind]) + LAM * op.vds + r4_vs_term(op.vsb)
        want = (op.ln_idu - r_peak) * op.gm_id / tol[m]
        assert inv["inversion_floor:%s" % m].c == pytest.approx(want, rel=1e-9, abs=1e-12), m
    assert inv["inversion_floor:M1"].c >= 0.0


def test_constraints_inversion_floor_differs_from_reference_key_peak_by_ln2(sealed):
    # 판별력: 기준 키 정점(ln I0 + ...)으로 읽었다면 c 가 ln 2·gm_id/tol 만큼 달라진다 -- 그 차가 실제로 0 이 아님을 본다
    case, snap = sealed
    ops, tol = col(snap, "device", "dc_op"), col(snap, "device", "dc_tol_v")
    op = ops["M1"]
    rows, _ = constraint_rows(snap, case.acc, W_MIN, GRID)
    c = {r.name: r for r in rows}["inversion_floor:M1"].c
    ref_key_c = (op.ln_idu - (math.log(I0[op.kind]) + LAM * op.vds + r4_vs_term(op.vsb))) * op.gm_id / tol["M1"]
    assert abs(ref_key_c - c) == pytest.approx(math.log(2.0) * op.gm_id / tol["M1"], rel=1e-9)
    assert abs(ref_key_c - c) > 1e-9
