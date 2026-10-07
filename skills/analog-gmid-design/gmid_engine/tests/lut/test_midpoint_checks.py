"""`midpoint_l_bin_checks` -- CONTRACT 5.1 [r6]: 앵커 2개 bin 의 외부 값(검증 중점 파일, 1.7).

- memo derived, 키 (kind, w_key). `MidpointChecks(kind, w_key, rows, skipped, midpoints_sha256)`; 중점 표 없는 kind -> (kind, w_key, (), (), None).
- 중점마다 순서대로: width_differs -> bins_unavailable -> is_anchor -> outside_model_bins -> single_point(앵커 < 2, model)·
  bin_has_interior_anchors(> 2) -> not_bracketed. 남은 중점: t = (L_m − a0)/(a1 − a0), 세 값은 **VDS 격자점 k 마다의 tuple**(결정 A):
  id_equivalent_v[k] = max |lnID(i0) + t·(lnID(i1) − lnID(i0)) − lnID_m| / gm_id_m (중점 on ∧ 슬라이스 on(i0) ∧ on(i1)),
  gm_id_inverse_v[k] = max |strong_inversion_root(L 선형 보간 곡선, g_j) − VGS_j| (5절 목표 규칙), vdsat_v[k] = max |선형 보간 − VDSAT_m|
  (출처 4.3, 축 같을 때). Richardson 환산 없음. 같은 bin 의 중점은 한 MidpointRow 로(k 마다 최댓값, 개수 합), rows = model 정렬.
- 기대값: conftest `midpoint_ref`(npz 직접 -- 5.1 식의 독립 구현), 중점 toy 의 닫힌 식(VDSAT 오차 = 0.05·(Lu_m − Lu0)(Lu1 − Lu_m)·(1 + d)).
"""
import math

import numpy as np
import pytest

from gmid_engine.lut import (MidpointChecks, MidpointRow, load_lut_set, midpoint_l_bin_checks, tol_v_table,
                             tol_vdsat_table)

from .conftest import (BIN_L, MID_L_SOURCE, TOY_SPEC, gamma_n, mid_point_arrays, mid_toy_arrays, midpoint_ref, new_memo,
                       sha256_file)

M = "toyn__model."
# 중점(오름차순 = 파일 순서)과 손으로 정한 판정(conftest 머리 bin 표: A [1,2] 앵커 1·1.5·2, B (2,4] 3·4, C (4,5] 없음,
# 빈틈 (5,6), D (6,8] 7·8, E (8,10] 9)
MID_L = (1.25e-6, 2.5e-6, 3e-6, 3.25e-6, 3.5e-6, 4.5e-6, 5.5e-6, 7.5e-6, 9.5e-6)
EXPECT_SKIPPED = ((1.25e-6, "bin_has_interior_anchors", M + "0"), (2.5e-6, "not_bracketed", M + "1"),
                  (3e-6, "is_anchor", None), (4.5e-6, "single_point", M + "2"), (5.5e-6, "outside_model_bins", None),
                  (9.5e-6, "single_point", M + "4"))
# 남은 중점 -> (model, 중점 index, 앵커 i0, i1)
EXPECT_ROWS = ((M + "1", (3, 4), 3, 4), (M + "3", (7,), 5, 6))


@pytest.fixture
def mid_toy(mid_toy_build):
    return mid_toy_build("mt", mid=mid_point_arrays(MID_L, l_source=MID_L_SOURCE))


def _vd_bound(t, V0, V1, Vm):
    return 2 * gamma_n() * ((1 + abs(t)) * abs(V0) + abs(t) * abs(V1) + abs(Vm))


def _expected_rows(slice_z, mid_z, vdsat_src, src_on):
    rows = []
    for model, mids, i0, i1 in EXPECT_ROWS:
        refs = [midpoint_ref(slice_z, mid_z, "_n", m, i0, i1, vdsat_src, src_on) for m in mids]
        nV = len(slice_z["VDS"])

        def kmax(key):
            out = []
            for k in range(nV):
                vals = [r[key][k] for r in refs if r[key][k] is not None]
                out.append(max(vals) if vals else None)
            return tuple(out)

        def kbound(key):
            out = []
            for k in range(nV):
                vals = [r[key][k] for r in refs if r[key][k] is not None]
                out.append(max(vals) if vals else None)
            return tuple(out)
        rows.append({"model": model, "L": tuple(float(mid_z["L"][m]) for m in mids), "inv": kmax("inv"), "eq": kmax("eq"),
                     "vdsat": kmax("vdsat"), "n_t": sum(r["n_t"] for r in refs), "n_f": sum(r["n_f"] for r in refs),
                     "inv_b": kbound("inv_bound"), "eq_b": kbound("eq_bound"), "mids": mids, "i0": i0, "i1": i1})
    return rows


def _assert_tuple_close(got, exp, bnd, what):
    assert len(got) == len(exp), what
    for k, (g, e, b) in enumerate(zip(got, exp, bnd)):
        if e is None:
            assert g is None, (what, k)
        else:
            assert g is not None and abs(g - e) <= b, (what, k, g, e, b)


def test_rows_and_skipped_match_independent(mid_toy):
    lut = mid_toy.load()
    m = new_memo(lut)
    mc = midpoint_l_bin_checks(m, "nmos", 100)
    assert isinstance(mc, MidpointChecks)
    assert (mc.kind, mc.w_key) == ("nmos", 100)
    assert mc.midpoints_sha256 == sha256_file(mid_toy.mid_path)
    assert tuple(tuple(s) for s in mc.skipped) == EXPECT_SKIPPED
    z = mid_toy_arrays(1e-6, 1.0, {})
    mid = mid_point_arrays(MID_L, l_source=MID_L_SOURCE)
    on = (z["ID"] > 0) & (z["GM"] > 0)
    exp = _expected_rows(z, mid, z["VDSAT"], on)
    assert [r.model for r in mc.rows] == [e["model"] for e in exp]
    for r, e in zip(mc.rows, exp):
        assert isinstance(r, MidpointRow)
        assert tuple(r.L_points) == e["L"]
        assert (r.n_targets, r.n_inverse_failed) == (e["n_t"], e["n_f"])
        _assert_tuple_close(r.id_equivalent_v, e["eq"], e["eq_b"], (e["model"], "eq"))
        _assert_tuple_close(r.gm_id_inverse_v, e["inv"], e["inv_b"], (e["model"], "inv"))
        # vdsat: 선형 보간·뺄셈 두 경로 반올림 -- 값 크기 상한 Vmax = 그 VDS 의 중점 toy VDSAT 최댓값(앵커 i1 쪽)
        Lu1 = BIN_L[e["i1"]] / 1e-6
        vmax = [0.1 + 0.2 + 0.05 * Lu1 ** 2 * (1 + d) for d in z["VDS"]]
        vb = [_vd_bound(1.0, v, v, v) for v in vmax]
        _assert_tuple_close(r.vdsat_v, e["vdsat"], vb, (e["model"], "vdsat"))


def test_hand_values_vdsat_and_targets(mid_toy):
    """닫힌 식: bin B 의 중점 3.25·3.5 µm -> VDSAT 오차 0.05·(Lu_m − 3)(4 − Lu_m)·(1 + d) 의 max = 3.5 µm 의 0.0125·(1 + d)
    -> (0.01875, 0.025). 판별: id_equivalent·gm_id_inverse 도 0 이 아니다(c(L) 이 L 에 2차). 목표 수 = 중점 2 × VS 2 × 목표 3."""
    mc = midpoint_l_bin_checks(new_memo(mid_toy.load()), "nmos", 100)
    row = {r.model: r for r in mc.rows}[M + "1"]
    for k, hand in enumerate((0.0125 * 1.5, 0.0125 * 2.0)):
        assert abs(row.vdsat_v[k] - hand) <= 8 * gamma_n() * 1.0, (k, row.vdsat_v[k], hand)
    assert all(v is not None and v > 0 for v in row.id_equivalent_v)
    assert any(v is not None and v > 0 for v in row.gm_id_inverse_v)
    # 중점 곡선 g = c(L_m)·(20 − 12v) 는 감소 -> VGS 3 점 모두 목표(5절 규칙): 중점 2 × VDS 2 × VS 2 × 목표 3 = 24
    assert row.n_targets == 24
    # 행은 L_points 두 개(3.25·3.5 µm)를 합쳤다
    assert tuple(row.L_points) == (3.25e-6, 3.5e-6)


def test_per_vds_tuples_have_grid_length(mid_toy):
    lut = mid_toy.load()
    mc = midpoint_l_bin_checks(new_memo(lut), "nmos", 100)
    n = len(lut.slice_map[("nmos", 100)].grids[2])
    for r in mc.rows:
        for f in ("gm_id_inverse_v", "id_equivalent_v", "vdsat_v"):
            assert isinstance(getattr(r, f), tuple) and len(getattr(r, f)) == n


def test_width_differs_for_other_width(mid_toy):
    """중점 표 폭 키 100 ≠ 조회 w_key 200 -> 모든 중점 "width_differs"(다른 폭으로 옮기지 않는다), rows ()."""
    mc = midpoint_l_bin_checks(new_memo(mid_toy.load()), "nmos", 200)
    assert mc.rows == () or tuple(mc.rows) == ()
    assert [s[1] for s in mc.skipped] == ["width_differs"] * len(MID_L)
    assert [s[0] for s in mc.skipped] == list(MID_L)
    assert all(s[2] is None for s in mc.skipped)


def test_bins_unavailable(toy_build, tmp_path):
    """bin 지도 없는 슬라이스(r5 toy) -> 모든 중점 "bins_unavailable". (중점 파일 축 = toy 축)"""
    b = toy_build("plainmid")
    p = tmp_path / "plain_mid.npz"
    np.savez(p, **mid_point_arrays((1.5e-6, 2.5e-6), l_source=MID_L_SOURCE))
    lut = load_lut_set(str(b.manifest), str(b.cap), TOY_SPEC, verify_midpoints=str(p))
    mc = midpoint_l_bin_checks(new_memo(lut), "nmos", 100)
    assert tuple(mc.rows) == ()
    assert [s[1] for s in mc.skipped] == ["bins_unavailable", "bins_unavailable"]


def test_no_midpoints_contract_toy(toy_memo):
    """7.1 r6 표: 중점 표 없음 -> MidpointChecks("nmos", 100, (), (), None)."""
    assert midpoint_l_bin_checks(toy_memo, "nmos", 100) == MidpointChecks("nmos", 100, (), (), None)


def test_vdsat_none_without_midpoint_column(mid_toy_build):
    """중점 VDSAT 열 없음 -> vdsat_v 모두 None(다른 두 값은 그대로)."""
    mt = mid_toy_build("novd", mid=mid_point_arrays(MID_L, l_source=MID_L_SOURCE, vdsat=False))
    mc = midpoint_l_bin_checks(new_memo(mt.load()), "nmos", 100)
    for r in mc.rows:
        assert all(v is None for v in r.vdsat_v)
        assert any(v is not None for v in r.id_equivalent_v)


def test_vdsat_none_without_source_column(mid_toy_build):
    """출처 열 없음(슬라이스·기준 LUT 모두 VDSAT 없음 -- column_source required=False 가 None) -> vdsat_v 모두 None."""
    mt = mid_toy_build("nosrc", slice_cols=(), mid=mid_point_arrays(MID_L, l_source=MID_L_SOURCE))
    mc = midpoint_l_bin_checks(new_memo(mt.load()), "nmos", 100)
    assert mc.rows and all(all(v is None for v in r.vdsat_v) for r in mc.rows)


def test_vdsat_from_cap_table_source(mid_toy_build):
    """슬라이스에 VDSAT 없고 기준 LUT(폭 키 100)에 있으면 출처 "cap_table" 의 값으로 vdsat_v(4.3 규칙). 기준 LUT VDSAT = 슬라이스 식의
    2 배로 두어 출처를 값으로 가린다."""
    cap_v = 2.0 * mid_toy_arrays(1e-6, 1.0, {})["VDSAT"]
    mt = mid_toy_build("capsrc", slice_cols=("GMBS",), cap_extra={"VDSAT_n": cap_v},
                       mid=mid_point_arrays(MID_L, l_source=MID_L_SOURCE))
    mc = midpoint_l_bin_checks(new_memo(mt.load()), "nmos", 100)
    z = mid_toy_arrays(1e-6, 1.0, {})
    mid = mid_point_arrays(MID_L, l_source=MID_L_SOURCE)
    ref = midpoint_ref(z, mid, "_n", 4, 3, 4, cap_v, None)            # 기준 LUT on_mask 없음(ID·GM 열 없음) -> 생략
    row = {r.model: r for r in mc.rows}[M + "1"]
    for k in range(2):
        assert abs(row.vdsat_v[k] - ref["vdsat"][k]) <= 8 * gamma_n() * 2.0


def test_memo_derived_and_tol_default(mid_toy):
    """memo derived 키 (kind, w_key): 두 번째 호출은 같은 객체. tol_v_table(None) 은 중점 조회를 먼저 부르고(derived misses +1),
    tol_vdsat_table(None) 은 그 결과를 재사용(hits). 기본 표 = rows 를 명시한 표(같은 객체)."""
    m = new_memo(mid_toy.load())
    t = tol_v_table(m, "nmos", 100)
    st = dict(m.stats())["derived"]
    assert st.misses == 2
    mc = midpoint_l_bin_checks(m, "nmos", 100)
    assert midpoint_l_bin_checks(m, "nmos", 100) is mc
    explicit = tuple((r.model, r.gm_id_inverse_v, r.id_equivalent_v) for r in mc.rows)
    assert tol_v_table(m, "nmos", 100, explicit) is t
    st2 = dict(m.stats())["derived"]
    assert st2.misses == 2 and st2.hits >= 2
    tv = tol_vdsat_table(m, "nmos", 100)
    st3 = dict(m.stats())["derived"]
    assert st3.misses == 3
    assert tol_vdsat_table(m, "nmos", 100, tuple((r.model, r.vdsat_v) for r in mc.rows)) is tv
    assert tuple(s for _, _, s in t.l_loo_bins) == ("computed", "external", "external", "single_point")


def test_tol_default_without_midpoints_does_not_query(toy_build):
    """2절: 중점 표가 없으면 midpoint 조회를 하지 않는다(r5 와 같은 misses 수)."""
    m = new_memo(toy_build("nm").load())
    t = tol_v_table(m, "nmos", 100)
    assert dict(m.stats())["derived"].misses == 1
    assert tuple(t.l_bin_checks) == ()


# ---------------------------------------------------------------------------
# 실데이터 (LUT v2 + 중점 파일): 계약 5.1 실측과 독립 numpy 재계산
# ---------------------------------------------------------------------------

@pytest.mark.lut_realdata
@pytest.mark.parametrize("kind,suf", [("nmos", "_n"), ("pmos", "_p")])
def test_real_rows_match_independent(real_lut, raw_slice, raw_mid, kind, suf):
    m = new_memo(real_lut)
    mc = midpoint_l_bin_checks(m, kind, 1000)
    assert mc.midpoints_sha256 == real_lut.provenance.midpoints_sha256
    assert len(mc.rows) == 1
    row = mc.rows[0]
    assert row.model.endswith(".26") and tuple(row.L_points) == (1.65e-7,)
    z = raw_slice(kind, 1000)
    Lg = [float(x) for x in z["L"]]
    i0 = Lg.index(0.15e-6) if 0.15e-6 in Lg else 0
    ref = midpoint_ref(z, raw_mid, suf, 0, i0, i0 + 1, z["VDSAT"], (z["ID"] > 0) & (z["GM"] > 0))
    assert (row.n_targets, row.n_inverse_failed) == (ref["n_t"], ref["n_f"])
    _assert_tuple_close(row.id_equivalent_v, ref["eq"], ref["eq_bound"], "eq")
    _assert_tuple_close(row.gm_id_inverse_v, ref["inv"], ref["inv_bound"], "inv")
    vb = [None if v is None else 8 * gamma_n() * 2.0 for v in ref["vdsat"]]
    _assert_tuple_close(row.vdsat_v, ref["vdsat"], [b if b is not None else 0 for b in vb], "vdsat")
    assert row.vdsat_v[0] is None                                   # k = 0 은 ID = 0 (계약 실측)
    sk = [(s[0], s[1]) for s in mc.skipped]
    assert sk == [(6e-6, "single_point"), (1.4e-5, "single_point")]
    assert [s[2].rsplit(".", 1)[1] for s in mc.skipped] == ["20", "19"]
    v = [x for x in row.vdsat_v if x is not None]
    print("%s 중점 .26: n_targets %d (실패 %d), vdsat max %.4g V, eq max %.4g V, inv max %.4g V"
          % (kind, row.n_targets, row.n_inverse_failed, max(v), max(x for x in row.id_equivalent_v if x is not None),
             max(x for x in row.gm_id_inverse_v if x is not None)))


@pytest.mark.lut_realdata
def test_real_contract_measured_summary(real_lut):
    """계약 5.1 실측(2026-10-08) 대조: nmos 23,520 목표·실패 0, pmos 19,671·실패 1,569; VDS 별 max(mV) nmos inv 518·eq 18.9·
    vdsat 2.49, pmos inv 316·eq 22.7·vdsat 32.5 (계약 표기 자릿수 안)."""
    m = new_memo(real_lut)
    exp = {"nmos": ((23520, 0), "518", "18.9", "2.49"), "pmos": ((19671, 1569), "316", "22.7", "32.5")}
    for kind, (cnt, inv, eq, vd) in exp.items():
        row = midpoint_l_bin_checks(m, kind, 1000).rows[0]
        assert (row.n_targets, row.n_inverse_failed) == cnt
        for got, want in ((max(x for x in row.gm_id_inverse_v if x is not None), inv),
                          (max(x for x in row.id_equivalent_v if x is not None), eq),
                          (max(x for x in row.vdsat_v if x is not None), vd)):
            dec = len(want.split(".")[1]) if "." in want else 0
            assert abs(got / 1e-3 - float(want)) <= 0.5 * 10 ** (-dec), (kind, got, want)      # mV 표기 마지막 자리 반 단위


@pytest.mark.lut_realdata
def test_real_other_width_width_differs(real_lut):
    mc = midpoint_l_bin_checks(new_memo(real_lut), "nmos", 84 if ("nmos", 84) in real_lut.slice_map else 72)
    assert tuple(mc.rows) == ()
    assert [s[1] for s in mc.skipped] == ["width_differs"] * 3
