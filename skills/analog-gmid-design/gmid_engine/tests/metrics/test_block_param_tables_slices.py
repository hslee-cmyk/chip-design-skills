"""WB-1 E-1·E-4(GB4 쪽)·E-6·E-7 + s4 (interface card 20261104-wb1 §5 '블록 값'·'W가 없는 단계').

`ParamTables(memo, grids, side, z_side)` 네 표(upper/lower × z min/max)와 `block_gain_bound` 네 번 호출의 합침 규칙을 본다.
oracle (a): 합성 슬라이스 LUT(`wb1_gb4.write_slice_lut`)는 격자 마디에서 x = f'(VGS), y = lam, z = 2A·zs·VS 가 닫힌 식이다.
upper = x 슬라이스 최댓값·y 최솟값, lower = x 최솟값·y 최댓값, z = `z_side`(min/max) 쪽. 기대값은 이 닫힌 식과 독립 numpy 전수 최댓값(wb1_gb4.follower_amax)이다.
블록 값(card): A_max·status·b_db = upper 두 표(둘 다 certified 일 때만 인증, 값 = a_max_db 큰 쪽), found_db = lower 두 표 found_db 의 작은 쪽
(한쪽이 None 이면 None), pi 는 표마다 같다.
**애매한 계약(보고)**: s3(슬라이스 VGS 격자 일치 거부)는 예외 종류가 card 에 없고 로더가 슬라이스 축 불일치를 이미 거부해 쓰지 않았다.
E-2·E-3·E-4 출발 쪽은 호출 이름이 card 에 없어 쓰지 않았다(보고). s4 는 'lut_column_unavailable 이 조용히 삼켜지지 않는다' 읽기를 쓴다.
"""
from __future__ import annotations

import dataclasses
import sys

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.metrics import ParamTables, block_gain_bound

from . import gb4_hand as G
from .gb4_hand import (GRIDS, LAM, cs_model, db, follower_model, memo_of, mos_e, stage_ab, toy_pdk, topology, two_e, write_case)
from .wb1_gb4 import all_index, follower_amax, write_slice_lut

SIDES = (("upper", "min"), ("upper", "max"), ("lower", "min"), ("lower", "max"))
VS = np.asarray(G.VS_GRID)
VGS = np.asarray(G.VGS_GRID)
PI_FOL = 19 * 2 * 7 * 6


def detail(exc):
    return dict(exc.record.detail)


@pytest.fixture(scope="module")
def lut_lam(tmp_path_factory):                     # E-1: 같은 ID·GM 비, LAM 0.1 / 0.2
    return write_slice_lut(tmp_path_factory.mktemp("wb1_lam"), ((1e-6, 0.1, 1.0), (2e-6, 0.2, 1.0)))


@pytest.fixture(scope="module")
def lut_gmbs(tmp_path_factory):                    # E-6: 같은 ID·GM·GDS 비, GMBS 배율 1.0 / 1.5 (z = 4·VS / 6·VS)
    return write_slice_lut(tmp_path_factory.mktemp("wb1_gmbs"), ((1e-6, 0.1, 1.0), (2e-6, 0.1, 1.5)))


@pytest.fixture(scope="module")
def lut_both(tmp_path_factory):                    # E-7: y 와 z 가 모두 다름 -> 표 넷이 서로 구별된다
    return write_slice_lut(tmp_path_factory.mktemp("wb1_both"), ((1e-6, 0.1, 1.0), (2e-6, 0.2, 1.5)))


def tables_of(lut):
    memo = memo_of(lut)
    return {s: ParamTables(memo, GRIDS, side=s[0], z_side=s[1]) for s in SIDES}


# ---------------------------------------------------------------- 표 값 (E-1 y, E-6 z)
@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_slice_param_tables_y_upper_is_min_lower_is_max(lut_lam, kind):
    il, idd, iss, iv = all_index()
    for (side, zside), t in tables_of(lut_lam).items():
        x, y, z = t.lookup(kind, il, idd, iss, iv)
        want_y = 0.1 if side == "upper" else 0.2                    # upper: y 최솟값, lower: y 최댓값
        assert np.allclose(y, want_y, rtol=1e-9, atol=0), (side, zside)
        assert np.allclose(x, G.fp_default(VGS[iv]), rtol=1e-9, atol=0)          # x 는 슬라이스에 무관
        assert np.allclose(z, 4.0 * VS[iss], rtol=1e-9, atol=1e-12)


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_slice_param_tables_z_follows_z_side(lut_gmbs, kind):
    il, idd, iss, iv = all_index()
    za, zb = 4.0 * VS[iss], 6.0 * VS[iss]                           # 슬라이스별 z 닫힌 식
    for (side, zside), t in tables_of(lut_gmbs).items():
        x, y, z = t.lookup(kind, il, idd, iss, iv)
        want = np.minimum(za, zb) if zside == "min" else np.maximum(za, zb)
        assert np.allclose(z, want, rtol=1e-9, atol=1e-12), (side, zside)
        assert np.allclose(y, 0.1, rtol=1e-9, atol=0)
    # 판별력: VS < 0 에서 min 과 max 가 실제로 다르다
    neg = VS[iss] < 0
    assert neg.any() and not np.allclose(np.minimum(za, zb)[neg], np.maximum(za, zb)[neg])


def test_slice_param_tables_signature_has_no_w_keys():
    import inspect
    from gmid_engine.metrics import LocalInputs
    assert list(inspect.signature(ParamTables).parameters) == ["memo", "grids", "side", "z_side"]
    assert "w_keys" not in {f.name for f in dataclasses.fields(LocalInputs)}


# ---------------------------------------------------------------- E-1 직접: 단순 공통 소스에서 6.02 dB
def test_slice_gain_bound_upper_exceeds_lower_by_6_02_db_for_doubled_y(lut_lam):
    m = cs_model()
    ts = tables_of(lut_lam)
    up = [block_gain_bound(m, ts[s], m.pi, ("M1", "M2")) for s in SIDES[:2]]
    lo = [block_gain_bound(m, ts[s], m.pi, ("M1", "M2")) for s in SIDES[2:]]
    assert all(b.status == "certified" and b.pi == m.pi for b in up + lo)
    a_max = max(b.a_max_db for b in up)
    found = min(b.found_db for b in lo)
    assert a_max == pytest.approx(db(20.0 / (0.1 + 0.1)), abs=1e-9)           # x1 최대 20, y1 = y2 = 0.1
    assert found == pytest.approx(db(20.0 / (0.2 + 0.2)), abs=1e-9)           # y 두 배 -> gain 절반
    assert a_max - found == pytest.approx(db(2.0), abs=1e-9)                  # 6.02 dB


# ---------------------------------------------------------------- 파이프라인 (네 표를 합친 블록 값)
def run_follower(root, lut, count_budget=None):
    pdk = toy_pdk(root / "pdk")
    topo = topology("wb1fol", [mos_e("M1", "nmos", "vdd", "in", "out")], sources=[two_e("I1", "current_source", "out", "gnd")])
    tp, sp = write_case(root / "case", topo, elements=(("I1", "current_source", None),),
                        constraints=(("gain_ss_db", ">=", 10.0),), count_budget=count_budget)
    return stage_ab(root / "case", lut, tp, sp, pdk)[1]


def block_of(b):
    g = b.s1.value("graph", "ach", "gain_checks")
    (blk,) = g.blocks
    return blk


def test_slice_block_value_e1_amax_from_min_y_found_from_max_y(tmp_path, lut_lam):
    blk = block_of(run_follower(tmp_path, lut_lam))
    assert blk.status == "certified" and blk.pi == PI_FOL
    z = lambda s: 4.0 * s
    assert blk.a_max_db == pytest.approx(db(follower_amax(0.1, z)), abs=1e-9)          # = db(5.6/3.9)
    assert blk.found_db == pytest.approx(db(follower_amax(0.2, z)), abs=1e-9)          # = db(5.6/4.0)
    assert blk.a_max_db > blk.found_db


def test_slice_block_value_e6_amax_is_larger_of_two_z_side_tables(tmp_path, lut_gmbs):
    blk = block_of(run_follower(tmp_path, lut_gmbs))
    za = lambda s: 4.0 * s
    zb = lambda s: 6.0 * s
    zmin = lambda s: min(za(s), zb(s))
    zmax = lambda s: max(za(s), zb(s))
    cands = [db(follower_amax(0.1, zmin)), db(follower_amax(0.1, zmax))]
    assert blk.status == "certified" and blk.pi == PI_FOL            # Π 는 슬라이스 수로 바뀌지 않는다
    assert blk.a_max_db == pytest.approx(max(cands), abs=1e-9)
    assert abs(cands[0] - cands[1]) > 1e-3                           # 판별력: 두 표의 상한이 실제로 다르다


def test_slice_grid_product_does_not_depend_on_slice_count(tmp_path, lut_gmbs):
    m = follower_model()
    for s, t in tables_of(lut_gmbs).items():
        bb = block_gain_bound(m, t, m.pi, ("M1",))
        assert bb.pi == m.pi == PI_FOL and bb.status == "certified", s       # 예산 = Π 면 전수(인증)
        assert block_gain_bound(m, t, m.pi - 1, ("M1",)).reason == "grid_product_over_budget", s


# ---------------------------------------------------------------- E-7
def wrap_bound(monkeypatch, mode):
    """achievability 모듈 전역 block_gain_bound 를 감싼다(card §9 s2). 표 구분은 lookup 한 점으로 한다(내부 속성 이름에 의존하지 않음):
    y 가 큰 쪽 = lower, z 가 작은 쪽 = z_side min (lut_both: 격자 점 VS = −0.45 에서 z = −2.7 / −1.8)."""
    ach = sys.modules["gmid_engine.metrics.achievability"]
    real = ach.block_gain_bound
    seen = []

    def wrapped(model, tables, budget, members):
        bb = real(model, tables, budget, members)
        z0 = np.zeros(1, dtype=int)
        _, y, z = tables.lookup("nmos", z0, z0, z0, z0)
        lower, zmin = bool(y[0] > 0.15), bool(z[0] < -2.0)
        seen.append((lower, zmin))
        if mode == "lower_found_none" and lower:
            bb = dataclasses.replace(bb, found_db=None)
        if mode == "upper_unknown" and not lower and zmin:
            bb = dataclasses.replace(bb, status="unknown", reason="grid_product_over_budget", a_max_db=None, b_db=None)
        return bb
    monkeypatch.setattr(ach, "block_gain_bound", wrapped)
    return seen


def test_slice_block_value_e7_lower_found_none_gives_none_found(tmp_path, lut_both, monkeypatch):
    seen = wrap_bound(monkeypatch, "lower_found_none")
    blk = block_of(run_follower(tmp_path, lut_both))
    assert len(set(seen)) == 4                                       # 네 표가 모두 불렸다(공허 통과 방지)
    assert blk.found_db is None
    assert blk.status == "certified"                                 # upper 쪽은 그대로
    zmin = lambda s: min(4.0 * s, 6.0 * s)
    zmax = lambda s: max(4.0 * s, 6.0 * s)
    want = max(db(follower_amax(0.1, zmin)), db(follower_amax(0.1, zmax)))
    assert blk.a_max_db == pytest.approx(want, abs=1e-9)


def test_slice_block_value_e7_one_upper_unknown_gives_unknown_block(tmp_path, lut_both, monkeypatch):
    seen = wrap_bound(monkeypatch, "upper_unknown")
    blk = block_of(run_follower(tmp_path, lut_both))
    assert len(set(seen)) == 4
    assert blk.status == "unknown"
    assert blk.a_max_db is None and blk.b_db is None


# ---------------------------------------------------------------- E-4 (GB4 쪽): 빈 bin 지도 -> w_hi 실패 -> 그 행 A_max 미정
def test_slice_block_value_e4_empty_bin_map_leaves_amax_undetermined(tmp_path_factory):
    lut = write_slice_lut(tmp_path_factory.mktemp("wb1_nobins"), ((1e-6, 0.1, 1.0), (2e-6, 0.1, 1.0)), no_bins=True)
    from gmid_engine.lut import widths
    assert tuple(widths(lut, "nmos")) != ()                          # [FS-1 A-196] 후보 = widths(lut, kind) (`reachable_slices` 삭제) -- 전제: 후보는 있고(L 무관 정적 집합) bin 지도만 비었다
    blk = block_of(run_follower(tmp_path_factory.mktemp("wb1_nobins_run"), lut))
    assert blk.a_max_db is None and blk.status != "certified"


# ---------------------------------------------------------------- s4: 열 없음은 조용히 빠지지 않는다
# card 뜻(interface §5 '블록 값', s4): 포락 항은 `is_slice_gap(exc)` 인 실패만 뺀다. 슬라이스 틈(`lut_axis_out_of_range` 등)이 아닌 실패 --
# 특히 `lut_column_unavailable` -- 는 광범위 except 에 삼켜지지 않고 올라간다.
# 근거(dispute 1): 합성 LUT 는 GMBS 열이 없어도 `lut.gmb` 가 VS 할선(lut CONTRACT 4.4 (4))으로 값을 내므로 이 LUT 로는 `lut_column_unavailable` 이 나지 않는다
# (실측). 그래서 단언을 '다른 열' 로 넓히지 않고, 같은 계약(분류 경로)을 슬라이스 하나의 `param_row` 조회가 던지는 사유로 직접 시험한다:
# LutMemo 공개 주입점 `lookup(region, fn_name, key, compute)` 를 감싸 폭 키 200 슬라이스의 `param_row` 조회만 사유를 던진다(관찰 지점은 §9 밖이라
# 공개 memo 서브클래스만 쓴다). oracle (d): `is_slice_gap` 어휘 = SLICE_GAP_REASONS 다섯(F-3), 그 밖 사유는 전파.
from gmid_engine.lut import LutMemo, SLICE_GAP_REASONS, is_slice_gap  # noqa: E402


class FailingSliceMemo(LutMemo):
    """폭 키 `fail_key` 슬라이스의 `param_row` 조회가 주어진 사유로 실패한다. `raised` = 던진 횟수(공허 통과 방지)."""

    def __init__(self, lut, reason, fail_key=200, n=8192):
        super().__init__(lut, point=n, curve=n, root=n)
        self.reason, self.fail_key, self.raised = reason, fail_key, 0

    def lookup(self, region, fn_name, key, compute):
        if fn_name == "param_row" and self.fail_key in tuple(key):
            self.raised += 1
            raise SealViolationError(devices=(), margin=None, detail={"reason": self.reason, "w_key": self.fail_key})
        return super().lookup(region, fn_name, key, compute)


@pytest.fixture(scope="module")
def lut_same_rows(tmp_path_factory):               # 두 슬라이스의 행이 같다(y 0.1·GMBS 배율 1.0) -> 한 슬라이스를 빼도 포락 값이 같다
    return write_slice_lut(tmp_path_factory.mktemp("wb1_s4"), ((1e-6, 0.1, 1.0), (2e-6, 0.1, 1.0)))


@pytest.mark.parametrize("side,zside", [("upper", "min"), ("lower", "max")])
def test_slice_param_tables_column_unavailable_propagates(lut_same_rows, side, zside):
    reason = "lut_column_unavailable"
    assert reason not in SLICE_GAP_REASONS                                  # 슬라이스 틈 어휘 밖
    memo = FailingSliceMemo(lut_same_rows, reason)
    t = ParamTables(memo, GRIDS, side=side, z_side=zside)
    il, idd, iss, iv = all_index()
    with pytest.raises(SealViolationError) as ei:
        t.lookup("nmos", il, idd, iss, iv)
    assert detail(ei.value)["reason"] == reason and not is_slice_gap(ei.value)
    assert memo.raised >= 1


@pytest.mark.parametrize("side,zside", [("upper", "min"), ("lower", "max")])
def test_slice_param_tables_slice_gap_is_dropped_from_envelope(lut_same_rows, side, zside):
    """대조(양성): 슬라이스 틈 사유(`lut_axis_out_of_range`)는 그 슬라이스 항만 포락에서 빠지고 남은 슬라이스 값이 나온다 -- 행이 같은 슬라이스라 값이 같다."""
    reason = "lut_axis_out_of_range"
    assert reason in SLICE_GAP_REASONS
    memo = FailingSliceMemo(lut_same_rows, reason)
    t = ParamTables(memo, GRIDS, side=side, z_side=zside)
    ref = ParamTables(memo_of(lut_same_rows), GRIDS, side=side, z_side=zside)
    il, idd, iss, iv = all_index()
    got, want = t.lookup("nmos", il, idd, iss, iv), ref.lookup("nmos", il, idd, iss, iv)
    assert memo.raised >= 1
    for a, b in zip(got, want):
        assert np.allclose(np.asarray(a), np.asarray(b), rtol=1e-9, atol=1e-12, equal_nan=True)
