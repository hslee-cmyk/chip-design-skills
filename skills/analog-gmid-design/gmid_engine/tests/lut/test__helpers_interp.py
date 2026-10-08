"""`_helpers_interp` [r5] -- CONTRACT 4.2 축별 보간(VGS·VDS cubic-Hermite, VS·L 선형, ln GDS·VTH 선형)과 6절 [r5].

- 6절: 옛 다선형 복사본(`multilinear_interp`·`multilinear_interp_point_multi`)은 패키지에서 빠졌다 -- 옛 파일 원본의 해시가
  계약 표와 같고, 패키지 어디에도 그 본문(같은 해시)·이름이 없다. 옛 원본은 격자점 동치 기대값의 참조로 실행한다.
- 4.2: 공개 조회(op_point·gm_id_curve)를 conftest 의 독립 Hermite 구현(`RefSlice`, 기저 함수 형태 -- 엔진의 de Casteljau 와
  다른 계산 경로)과 r5 toy 닫힌 식(CONTRACT 7.1)으로 대조한다. gm/ID = ln ID 의 VGS 미분(유한차분으로도 확인).
"""
import math

import numpy as np
import pytest

from gmid_engine.lut import gm_id_curve, op_point

from .conftest import (LEGACY_REF_HASHES, LEGACY_SR, LUT_SRC, R5_A, R5_B, TOY_L, TOY_VDS, TOY_VGS, TOY_VS, RefSlice,
                       anchor_w, ast_sha, function_body, interp4, l_weights, legacy_reference_functions, log_floor,
                       lut_package_function_names, lut_package_window_hashes, r4_toy_slice_arrays, r5_toy_lnid,
                       rel_close, toy_slice_arrays)

OP_FIELDS = ("IDu", "gm_over_id", "gm_gds", "gds_per_w", "vth")


# ---------------------------------------------------------------------------
# 6절 [r5]: 복사본 제거 + 옛 원본 참조
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("old_name,sha,n_stmts", LEGACY_REF_HASHES)
def test_legacy_reference_hash_and_copy_removed(old_name, sha, n_stmts):
    old = function_body(LEGACY_SR, old_name)
    assert len(old) == n_stmts
    assert ast_sha(old) == sha, "옛 원본 본문 해시가 계약 6절 표와 다르다(참조가 바뀜)"
    hits = lut_package_window_hashes(n_stmts).get(sha, [])
    assert hits == [], "옛 다선형 본문 복사가 패키지에 남아 있다: %r" % (hits,)
    names = lut_package_function_names()
    assert not ({"multilinear_interp", "multilinear_interp_point_multi", "_multilinear_interp",
                 "_multilinear_interp_point_multi"} & names)


def test_window_hash_scan_detects_a_copy():
    """음성 대조: 창 해시 검사가 실제로 잡는다 -- 패키지 함수 하나의 본문 해시는 검사 결과에 있다."""
    body = function_body(LUT_SRC / "_helpers_fail.py", "schema_rejected")
    hits = lut_package_window_hashes(len(body)).get(ast_sha(body), [])
    assert any(f == "_helpers_fail.py" for f, _ in hits)


# ---------------------------------------------------------------------------
# 4.2 r5 toy: 격자 밖 기대값 = 닫힌 식 (cubic-Hermite 가 2차식·1차식을 정확히 재현)
# ---------------------------------------------------------------------------

TOY_PTS = [
    (2e-6, 0.25, 0.75, 0.25),
    (3e-6, 0.9, 0.6, 0.1),
    (1e-6, 0.1, 1.0, 0.5),
    (3e-6, 1.0, 0.5, 0.0),
    (2e-6, 0.7, 0.8, 0.3),                   # CONTRACT 7.1 행
    (1e-6, 0.37, 0.93, 0.41),
]


@pytest.mark.parametrize("pt", TOY_PTS)
def test_op_point_offgrid_matches_closed_form_r5_toy(toy_memo, pt):
    L, v, d, s = pt
    iL = TOY_L.index(L)
    op = op_point(toy_memo, "nmos", 100, *pt)
    lnid = r5_toy_lnid(v, d, s, L)
    assert rel_close(op.IDu, math.exp(lnid) * L / 1e-6, 1e-12)
    assert rel_close(op.gm_over_id, R5_A - 2 * R5_B * v, 1e-12)
    # ln GDS 는 모든 축 선형(VGS 방향도 선형 -- 닫힌 식 아님): 독립 다선형
    lD = log_floor(toy_slice_arrays(1e-6)["GDS"])[0]
    lnD = interp4((TOY_L, TOY_VGS, TOY_VDS, TOY_VS), lD, pt)
    assert rel_close(op.gds_per_w, math.exp(lnD) / 1e-6, 1e-12)
    assert rel_close(op.gm_gds, (R5_A - 2 * R5_B * v) * math.exp(lnid - lnD), 1e-12)
    assert op.vth == pytest.approx(0.4, abs=1e-15)
    # 같은 값을 독립 Hermite 구현도 낸다
    ref = RefSlice(toy_slice_arrays(1e-6)).op(anchor_w(iL), L, v, d, s)
    for f in OP_FIELDS:
        assert rel_close(getattr(op, f), ref[f], 1e-12), f


@pytest.mark.parametrize("pt", [p for p in TOY_PTS if p[1] not in TOY_VGS])
def test_offgrid_differs_from_legacy_multilinear(toy_memo, pt):
    """판별력: 같은 입력에서 옛 다선형(로그공간)은 다른 값을 낸다(CONTRACT 7절 머리)."""
    a = toy_slice_arrays(1e-6)
    lI, lG = log_floor(a["ID"])[0], log_floor(a["GM"])[0]
    old = legacy_reference_functions()["_multilinear_interp_point_multi"]
    li, lg = old([list(TOY_L), list(TOY_VGS), list(TOY_VDS), list(TOY_VS)], [lI, lG], list(pt))
    op = op_point(toy_memo, "nmos", 100, *pt)
    assert not rel_close(op.gm_over_id, math.exp(lg - li), 1e-6)
    assert not rel_close(op.IDu, math.exp(li) * pt[0] / 1e-6, 1e-6)


def test_gm_over_id_is_vgs_derivative_of_lnid(toy_memo):
    """4.2: gm/ID = ln ID 의 VGS 미분(같은 곡면) -- 중심 유한차분 대조(닫힌 식과 무관한 확인)."""
    n = 0
    for L, v, d, s in TOY_PTS:
        if v in TOY_VGS:
            continue
        dv = 1e-5
        up = op_point(toy_memo, "nmos", 100, L, v + dv, d, s)
        dn = op_point(toy_memo, "nmos", 100, L, v - dv, d, s)
        fd = (math.log(up.IDu) - math.log(dn.IDu)) / (2 * dv)
        assert rel_close(op_point(toy_memo, "nmos", 100, L, v, d, s).gm_over_id, fd, 1e-7)
        n += 1
    assert n == 5


def test_r4_toy_fc_violating_cells_fall_back_to_linear(r4toy_memo):
    """CONTRACT 7.2: VGS 칸 0·VDS 칸 위반 -> 그 축 선형, 실패하지 않는다(op_point 행).
    oracle (a) 손계산([r7] 1.4 단위 검사와 맞는 r4 toy -- conftest R4_*): VGS 0.25·VDS 0.75 는 두 축 모두 칸 중앙(t = ½) 선형 ->
    ln IDu = ½(ln1e-7 + ln1e-6) + ½(0 + 0.01), gm/ID = 그 직선의 미분 ln10/0.5, ln GDS 선형 -> GDS/ID = √(0.1·0.01),
    gm_gds = gm/ID ÷ √(1e-3), gds_per_w = IDu·√(1e-3)/1e-6 (w_m = L = 1e-6)."""
    op = op_point(r4toy_memo, "nmos", 100, 1e-6, 0.25, 0.75, 0.0)
    assert rel_close(op.IDu, math.sqrt(1e-7 * 1e-6) * math.exp(0.005), 1e-12)
    assert rel_close(op.IDu, 3.178129e-7, 1e-6)
    assert rel_close(op.gm_over_id, math.log(10.0) / 0.5, 1e-12)
    assert rel_close(op.gm_over_id, 4.605170, 1e-6)
    assert rel_close(op.gm_gds, math.log(10.0) / 0.5 / math.sqrt(1e-3), 1e-12)
    assert rel_close(op.gm_gds, 145.6283, 1e-6)
    assert rel_close(op.gds_per_w, math.sqrt(1e-7 * 1e-6) * math.exp(0.005) * math.sqrt(1e-3) / 1e-6, 1e-12)
    assert rel_close(op.gds_per_w, 0.01005013, 1e-6)
    assert op.vth == pytest.approx(0.4, abs=1e-15)
    ref = RefSlice(r4_toy_slice_arrays(1e-6)).op(anchor_w(0), 1e-6, 0.25, 0.75, 0.0)
    assert ref["vgs_hermite"] is False
    for f in OP_FIELDS:
        assert rel_close(getattr(op, f), ref[f], 1e-12), f


def test_r4_toy_monotone_vgs_cell_uses_hermite(r4toy_memo):
    """r4 toy VGS 칸 1(기울기 4·1.5, 현 3)은 단조 -> Hermite. VDS 칸은 FC 위반이라 VDS 선형(RefSlice 독립 구현이 같은 규칙)."""
    rs = RefSlice(r4_toy_slice_arrays(1e-6))
    for pt in ((1e-6, 0.75, 0.5, 0.0), (2e-6, 0.6, 0.8, 0.3), (3e-6, 0.95, 0.7, 0.45)):
        ref = rs.op(anchor_w(TOY_L.index(pt[0])), *pt)
        assert ref["vgs_hermite"] is True
        op = op_point(r4toy_memo, "nmos", 100, *pt)
        for f in OP_FIELDS:
            assert rel_close(getattr(op, f), ref[f], 1e-12), (pt, f)
        assert not rel_close(op.gm_over_id, 1.5 / 0.5, 1e-3), "Hermite 칸이면 직선 기울기(칸 1 현 3)가 아니다"


def test_gm_id_curve_offgrid_matches_independent_hermite_toy(toy_memo):
    L, vds, vsb = 2e-6, 0.8, 0.3
    c = gm_id_curve(toy_memo, "nmos", 100, L, vds, vsb)
    V, S, ok = RefSlice(toy_slice_arrays(1e-6)).curve(anchor_w(1), vds, vsb)
    np.testing.assert_allclose(np.asarray(c.log_id_vals), V, rtol=1e-13)
    np.testing.assert_allclose(np.asarray(c.id_vals), np.exp(V), rtol=1e-12)
    np.testing.assert_allclose(np.asarray(c.gm_id_vals), S, rtol=1e-12)
    assert tuple(bool(x) for x in c.cell_ok) == ok == (True, True)
    for j, v in enumerate(TOY_VGS):
        assert rel_close(float(c.log_id_vals[j]), r5_toy_lnid(v, vds, vsb, L), 1e-13)
        assert rel_close(float(c.gm_id_vals[j]), R5_A - 2 * R5_B * v, 1e-12)


# ---------------------------------------------------------------------------
# 실데이터
# ---------------------------------------------------------------------------

def _anchor_bin(real_lut, kind, wk):
    return tuple(real_lut.slice_map[(kind, wk)].l_bins.anchor_bin)


@pytest.mark.lut_realdata
def test_op_point_offgrid_matches_independent_hermite_real(real_lut, real_memo, raw_slice):
    """격자 밖(VGS·VDS·VS, L 은 앵커 또는 같은 bin 안 보간) op_point = 독립 Hermite 구현."""
    rng = np.random.default_rng(474)
    n_l_interp = n_herm = 0
    for kind, wk in (("nmos", 72), ("pmos", 1000), ("nmos", 1000)):
        z = raw_slice(kind, wk)
        rs = RefSlice(z)
        ab = _anchor_bin(real_lut, kind, wk)
        Lg = [float(x) for x in z["L"]]
        done = 0
        while done < 30:
            if done % 3 == 2:
                k = int(rng.integers(1, len(Lg)))
                L = float(Lg[k - 1] + rng.uniform(0.1, 0.9) * (Lg[k] - Lg[k - 1]))
            else:
                L = Lg[int(rng.integers(0, len(Lg)))]
            pos = l_weights(Lg, ab, L)
            if pos is None:
                continue
            Lw, Lval = pos
            v, d, s = (float(rng.uniform(g[0], g[-1])) for g in rs.grids[1:])
            ref = rs.op(Lw, Lval, v, d, s)
            if not math.isfinite(ref["gm_over_id"]):
                continue
            op = op_point(real_memo, kind, wk, L, v, d, s)
            for f in OP_FIELDS:
                assert rel_close(getattr(op, f), ref[f], 1e-10), (kind, wk, L, v, d, s, f, getattr(op, f), ref[f])
            n_l_interp += len(Lw) == 2
            n_herm += bool(ref["vgs_hermite"])
            done += 1
    assert n_l_interp >= 10 and n_herm >= 30


@pytest.mark.lut_realdata
def test_real_gm_over_id_is_vgs_derivative(real_memo, raw_slice):
    """같은 곡면: gm/ID 와 ln IDu 의 VGS 중심차분이 맞는다(강반전, 칸 안 점)."""
    z = raw_slice("nmos", 1000)
    rng = np.random.default_rng(9)
    VGS = z["VGS"]
    for _ in range(20):
        iL, j, k, s = int(rng.integers(0, 12)), int(rng.integers(20, 47)), int(rng.integers(5, 48)), int(rng.integers(0, 9))
        v = float(VGS[j] + 0.43 * (VGS[j + 1] - VGS[j]))
        L, d, vs = float(z["L"][iL]), float(z["VDS"][k]), float(z["VS"][s])
        dv = 1e-6
        up = op_point(real_memo, "nmos", 1000, L, v + dv, d, vs)
        dn = op_point(real_memo, "nmos", 1000, L, v - dv, d, vs)
        fd = (math.log(up.IDu) - math.log(dn.IDu)) / (2 * dv)
        assert rel_close(op_point(real_memo, "nmos", 1000, L, v, d, vs).gm_over_id, fd, 1e-6)


@pytest.mark.lut_realdata
def test_grid_points_bit_equal_to_legacy_multilinear(real_memo, raw_slice):
    """CONTRACT 6절 [r5]: 격자점(L 앵커·VGS·VDS·VS 모두 격자)에서 op_point 의 IDu·gm_over_id·gds_per_w·vth 는 옛 원본
    `_multilinear_interp_point_multi`(로그공간, 1.4 바닥 규칙)와 비트 단위로 같고 gm_gds 는 상대 ≤ 1e-14.
    마지막 격자점을 포함한다."""
    old = legacy_reference_functions()["_multilinear_interp_point_multi"]
    rng = np.random.default_rng(606)
    n = 0
    for kind, wk in (("nmos", 72), ("nmos", 1000), ("pmos", 1000)):
        z = raw_slice(kind, wk)
        grids = [[float(x) for x in z[a]] for a in ("L", "VGS", "VDS", "VS")]
        lI, lG, lD = log_floor(z["ID"])[0], log_floor(z["GM"])[0], log_floor(z["GDS"])[0]
        W = float(z["W"])
        shape = z["ID"].shape
        pts = [tuple(d - 1 for d in shape)]
        while len(pts) < 121:
            idx = tuple(int(rng.integers(0, d)) for d in shape)
            if z["ID"][idx] > 0 and z["GM"][idx] > 0:
                pts.append(idx)
        for idx in pts:
            pt = [grids[a][idx[a]] for a in range(4)]
            li, lg, ld, vth = old(grids, [lI, lG, lD, z["VTH"]], pt)
            op = op_point(real_memo, kind, wk, *pt)
            assert op.IDu == math.exp(li) * pt[0] / W, (kind, wk, idx)
            assert op.gm_over_id == math.exp(lg - li), (kind, wk, idx)
            assert op.gds_per_w == math.exp(ld) / W, (kind, wk, idx)
            assert op.vth == vth, (kind, wk, idx)
            assert rel_close(op.gm_gds, math.exp(lg - ld), 1e-14), (kind, wk, idx)
            n += 1
    assert n == 3 * 121


@pytest.mark.lut_realdata
def test_grid_curve_nodes_bit_equal_to_legacy(real_memo, raw_slice):
    """CONTRACT 6절 [r5]: VDS·VS 격자점의 gm_id_curve 마디 값(id_vals·gm_id_vals)은 옛 곡선(`_gm_id_curve` 의 식 --
    옛 원본 `_multilinear_interp` 로 VGS 격자 전체)과 비트 단위로 같다(gm/ID 가 정의된 마디)."""
    old = legacy_reference_functions()["_multilinear_interp"]
    rng = np.random.default_rng(77)
    for kind, wk in (("nmos", 1000), ("pmos", 84)):
        z = raw_slice(kind, wk)
        grids = [[float(x) for x in z[a]] for a in ("L", "VGS", "VDS", "VS")]
        lI, lG = log_floor(z["ID"])[0], log_floor(z["GM"])[0]
        VGS = grids[1]
        for _ in range(10):
            iL, k, s = int(rng.integers(0, 12)), int(rng.integers(1, 49)), int(rng.integers(0, 10))
            L, d, vs = grids[0][iL], grids[2][k], grids[3][s]
            pts = np.column_stack([np.full(len(VGS), L), VGS, np.full(len(VGS), d), np.full(len(VGS), vs)])
            log_id = np.asarray(old(grids, lI, pts))
            log_gm = np.asarray(old(grids, lG, pts))
            c = gm_id_curve(real_memo, kind, wk, L, d, vs)
            on = (z["ID"][iL, :, k, s] > 0) & (z["GM"][iL, :, k, s] > 0)
            assert np.array_equal(np.asarray(c.id_vals), np.exp(log_id))
            assert np.array_equal(np.asarray(c.gm_id_vals)[on], np.exp(log_gm - log_id)[on])
            assert np.all(np.isnan(np.asarray(c.gm_id_vals)[~on])), "on_mask 거짓 마디의 gm/ID 는 NaN(4.1 표·4.2)"


# ---------------------------------------------------------------------------
# [r7] VS 축 Hermite (계획 DEC-87 'VS 축 = 선형(GMBS 열이 생기면 기울기 −GMBS/ID 의 Hermite)', CONTRACT 4.2 [r7])
#   oracle (a): conftest `vs_toy_*` -- ln ID 가 VS 의 2차식이고 GMBS = 정확한 기울기 -> Hermite 는 2차식을 정확히 재현(닫힌 식),
#   선형은 칸 중앙에서 ln 으로 (0.5)²/4 = 0.0625 낮다. 폴백 사유는 CONTRACT 4.1 `OpPoint.fallbacks`.
# ---------------------------------------------------------------------------

from .conftest import vs_toy_lnid, vs_toy_slices  # noqa: E402


@pytest.fixture
def vs_memo(toy_build):
    from .conftest import new_memo
    return new_memo(toy_build("vs", slices=vs_toy_slices()).load())


@pytest.mark.parametrize("v,d,s", [(0.5, 0.5, 0.25), (0.25, 0.75, 0.1), (0.9, 1.0, 0.4), (0.0, 0.6, 0.33)])
def test_vs_hermite_reproduces_quadratic_in_vs(vs_memo, v, d, s):
    op = op_point(vs_memo, "nmos", 100, 1e-6, v, d, s)
    assert abs(math.log(op.IDu) - vs_toy_lnid(v, d, s)) <= 1e-12
    assert op.fallbacks == ()
    assert abs(op.gm_over_id - (R5_A - 2 * R5_B * v)) <= 1e-12          # gm/ID 의 VS 방향은 마디 기울기 선형(정확: VS 무관)


def test_vs_hermite_differs_from_linear(vs_memo):
    """판별: 같은 점의 VS 선형 값(두 VS 마디 ln ID 의 평균)과 0.0625 차이(2차식 −s² 의 칸 중앙 오차)."""
    op = op_point(vs_memo, "nmos", 100, 1e-6, 0.5, 0.5, 0.25)
    lin = 0.5 * (vs_toy_lnid(0.5, 0.5, 0.0) + vs_toy_lnid(0.5, 0.5, 0.5))
    assert abs(math.log(op.IDu) - lin - 0.0625) <= 1e-12


def test_vs_on_grid_has_no_vs_fallback(toy_build):
    """VS 가 격자점이면 VS 보간이 없다 -> 폴백 기록도 없다(기울기가 정의 안 된 자료여도)."""
    from .conftest import new_memo
    m = new_memo(toy_build("vsneg0", slices=vs_toy_slices(gmbs_mutate=lambda g: -g)).load())
    assert op_point(m, "nmos", 100, 1e-6, 0.5, 0.5, 0.5).fallbacks == ()


def test_vs_slope_undefined_falls_back_to_linear(toy_build):
    """GMBS ≤ 0(기울기 정의 안 됨) -> VS 선형, `fallbacks` = (("VS", "slope_undefined"),)."""
    from .conftest import new_memo
    m = new_memo(toy_build("vsneg", slices=vs_toy_slices(gmbs_mutate=lambda g: -g)).load())
    op = op_point(m, "nmos", 100, 1e-6, 0.5, 0.5, 0.25)
    assert op.fallbacks == (("VS", "slope_undefined"),)
    lin = 0.5 * (vs_toy_lnid(0.5, 0.5, 0.0) + vs_toy_lnid(0.5, 0.5, 0.5))
    assert abs(math.log(op.IDu) - lin) <= 1e-12


def test_vs_fc_violation_falls_back_to_linear(toy_build):
    """[r7 2026-10-09] VS FC 위반 판 vs toy(conftest vs_fc=True -- ln ID 의 VS 몫 −(μ/λ)(e^(λs) − 1), GMBS/ID = μe^(λs), 기울기 자료가
    ln ID 와 맞아 1.4 단위 검사 통과): 끝 기울기 −(0.1, 14.84), Δln ID = −1.474 -> b0 = −0.05, b2 = −7.421, b1 = 3.049 > 0,
    b1² = 9.30 > b0·b2 = 0.371 -> FC 위반(CONTRACT 1.4 식, 손계산) -> VS 선형, 사유 'fc_violation'.
    (옛 입력 = GMBS 1000 배는 기울기가 ln ID 와 모순이라 이제 로드 거부 -- test_lut_set `test_unit_mismatch_rejected_gmbs`.)"""
    from .conftest import new_memo
    m = new_memo(toy_build("vsfc", slices=vs_toy_slices(vs_fc=True)).load())
    op = op_point(m, "nmos", 100, 1e-6, 0.5, 0.5, 0.25)
    assert op.fallbacks == (("VS", "fc_violation"),)
    lin = 0.5 * (vs_toy_lnid(0.5, 0.5, 0.0, vs_fc=True) + vs_toy_lnid(0.5, 0.5, 0.5, vs_fc=True))
    assert abs(math.log(op.IDu) - lin) <= 1e-12


def test_vgs_linear_cell_fallback_recorded(r4toy_memo):
    """CONTRACT 4.1 [r7]: Hermite 가 가능한 칸인데 선형으로 간 축은 조용하지 않다 -- r4 toy VGS 칸 0(FC 위반)·VDS 칸(위반)."""
    op = op_point(r4toy_memo, "nmos", 100, 1e-6, 0.25, 0.75, 0.0)
    assert dict(op.fallbacks) == {"VDS": "fc_violation", "VGS": "fc_violation"}
    assert list(op.fallbacks) == sorted(op.fallbacks)


@pytest.mark.lut_realdata
def test_real_vs_offgrid_matches_independent_hermite(real_memo, raw_slice):
    """(b) 실데이터(GMBS 열 있음): VS 칸 중앙 조회의 IDu·gm/ID 가 conftest 독립 Hermite(VS 축 Hermite 포함, 기저 함수 경로)와 상대 1e-11,
    폴백 사유도 독립 판정과 같다. nmos w_key 72 L 0.15 µm 는 VS FC 위반 칸(243개)이 있는 슬라이스 -- 그 칸은 선형·'fc_violation'."""
    rng = np.random.default_rng(20261008)
    for kind, w_key in (("nmos", 1000), ("pmos", 1000), ("nmos", 72), ("pmos", 400)):
        z = raw_slice(kind, w_key)
        rs = RefSlice(z)
        n_fb = 0
        for _ in range(60):
            i = int(rng.integers(0, 2)) if w_key in (72, 400) else int(rng.integers(len(z["L"])))
            g, k, s = int(rng.integers(1, len(z["VGS"]) - 1)), int(rng.integers(2, len(z["VDS"]) - 1)), int(rng.integers(len(z["VS"]) - 1))
            vgs = float(z["VGS"][g])
            vds = float(z["VDS"][k])
            vsb = 0.5 * float(z["VS"][s] + z["VS"][s + 1])
            L = float(z["L"][i])
            op = op_point(real_memo, kind, w_key, L, vgs, vds, vsb)
            exp = rs.op(anchor_w(i), L, vgs, vds, vsb)
            assert rel_close(op.IDu, exp["IDu"], 1e-11), (kind, w_key, i, g, k, s)
            assert rel_close(op.gm_over_id, exp["gm_over_id"], 1e-11)
            fb = rs.vs_fallback(anchor_w(i), vgs, vds, vsb)
            assert dict(op.fallbacks).get("VS") == fb
            n_fb += fb is not None
