"""`midpoint_l_bin_checks` -- CONTRACT 5.1 [r6]: 앵커 2개 bin 의 외부 값(검증 중점 파일, 1.7).

- memo derived, 키 (kind, w_key). `MidpointChecks(kind, w_key, rows, skipped, midpoints_sha256)`; 중점 표 없는 kind -> (kind, w_key, (), (), None).
- 중점마다 순서대로: width_differs -> bins_unavailable -> is_anchor -> outside_model_bins -> single_point(앵커 < 2, model)·
  bin_has_interior_anchors(> 2) -> not_bracketed. 남은 중점: t = (L_m − a0)/(a1 − a0), 세 값은 **VDS 격자점 k 마다의 tuple**(결정 A):
  id_equivalent_v[k] = max |lnID(i0) + t·(lnID(i1) − lnID(i0)) − lnID_m| / gm_id_m (중점 on ∧ 슬라이스 on(i0) ∧ on(i1)),
  gm_id_inverse_v[k] = max |strong_inversion_root(L 선형 보간 곡선, g_j) − VGS_j| (5절 목표 규칙), vdsat_v[k] = max |선형 보간 − VDSAT_m|
  (출처 4.3, 축 같을 때). Richardson 환산 없음. 같은 bin 의 중점은 한 MidpointRow 로(k 마다 최댓값, 개수 합), rows = model 정렬.
- 기대값: conftest `midpoint_ref`(npz 직접 -- 5.1 식의 독립 구현), 중점 toy 의 닫힌 식(VDSAT 오차 = 0.05·(Lu_m − Lu0)(Lu1 − Lu_m)·(1 + d)).
"""
import hashlib
import json
import math
import os
import subprocess
import sys

import numpy as np
import pytest

from gmid_engine.lut import (MidpointChecks, MidpointRow, load_lut_set, midpoint_l_bin_checks, tol_v_table,
                             tol_vdsat_table)

from .conftest import (BIN_L, MID_L_SOURCE, REAL_DEVICE_KINDS, SKILL_DIR, TOY_SPEC, gamma_n, manufacturing_grid_m,
                       mid_point_arrays, mid_toy_arrays, midpoint_ref, new_memo, parse_model_bins, same_bounds, sha256_file, um)

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
    b = toy_build("plainmid", empty_bins=True)       # [WB-1 §4] bin 블록 없는 합성 모델 파일 = 빈 지도
    p = tmp_path / "plain_mid.npz"
    np.savez(p, **mid_point_arrays((1.5e-6, 2.5e-6), l_source=MID_L_SOURCE))
    lut = load_lut_set(str(b.manifest), str(b.cap), TOY_SPEC, verify_midpoints=str(p), bin_rule=b.bin_rule,
                        pdk_root=b.tb.pdk_root)
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
# 실데이터 (LUT v2 r2 + 중점 파일 r2): 계약 5.1·8절(2026-10-08 중점 변경)과 독립 numpy 재계산
# ---------------------------------------------------------------------------

def _showmod_expected(ngspice_bins, kind, z, mids_m):
    """oracle (a): ngspice showmod 가 실제로 고른 bin 으로 5.1 판정 3~6 을 독립으로 다시 한다(엔진 bin 지도 미사용).
    앵커·중점을 같은 폭(슬라이스 W)에서 showmod 로 재고, bin 이름은 PDK 모델 파일을 test 쪽 파서로 읽어 경계로 맞춘다.
    반환 (rows = [(model, (중점 index, ...), i0, i1)] model 정렬, skipped = [(L_m, 사유, model 또는 None)] 파일 순서)."""
    device = {k: d for d, k in REAL_DEVICE_KINDS}[kind]
    Lg = [float(x) for x in z["L"]]
    w = um(float(z["W"]))
    b_anchor = ngspice_bins.query(device, [(w, um(L)) for L in Lg])
    b_mid = ngspice_bins.query(device, [(w, um(L)) for L in mids_m])
    names = parse_model_bins(ngspice_bins.pm3(device))

    def name_of(bnd):
        hit = [n for n, v in names.items() if same_bounds(v, bnd)]
        assert len(hit) == 1, (bnd, hit)
        return hit[0]
    rows, skipped = {}, []
    for mi, Lm in enumerate(mids_m):
        if any(abs(Lm - a) <= math.ulp(a) for a in Lg):
            skipped.append((Lm, "is_anchor", None))
            continue
        bm = b_mid[mi]
        if bm is None:
            skipped.append((Lm, "outside_model_bins", None))
            continue
        idx = [i for i, ba in enumerate(b_anchor) if same_bounds(ba, bm)]
        if len(idx) < 2:
            skipped.append((Lm, "single_point", name_of(bm)))
        elif len(idx) > 2:
            skipped.append((Lm, "bin_has_interior_anchors", name_of(bm)))
        elif not Lg[idx[0]] < Lm < Lg[idx[1]]:
            skipped.append((Lm, "not_bracketed", name_of(bm)))
        else:
            rows.setdefault(name_of(bm), (idx[0], idx[1], []))[2].append(mi)
    return [(mo, tuple(v[2]), v[0], v[1]) for mo, v in sorted(rows.items())], skipped


@pytest.mark.lut_realdata
@pytest.mark.parametrize("kind,suf", [("nmos", "_n"), ("pmos", "_p")])
def test_real_rows_match_independent(real_lut, raw_slice, raw_mid, ngspice_bins, kind, suf):
    """[2026-10-08 중점 변경] 중점 0.165·0.85·1.75·3.25 µm 가 모두 앵커 2개 bin(.26·.23·.22·.21)의 행이 된다(skipped = ()).
    oracle: 행 구성 = (a) showmod 소속(`_showmod_expected`), 값 = (b) conftest `midpoint_ref`(npz 직접, 5.1 식 독립 구현) --
    허용 차는 그 구현의 유도 반올림 상한. skipped = () 은 (d) CONTRACT 8절 실측 문장('4 중점 모두 사용(skipped = ())')과도 대조."""
    m = new_memo(real_lut)
    mc = midpoint_l_bin_checks(m, kind, 1000)
    assert mc.midpoints_sha256 == real_lut.provenance.midpoints_sha256
    z = raw_slice(kind, 1000)
    mids_m = [float(x) for x in raw_mid["L"]]
    exp_rows, exp_skipped = _showmod_expected(ngspice_bins, kind, z, mids_m)
    assert [tuple(s) for s in mc.skipped] == exp_skipped
    assert tuple(mc.skipped) == ()                                   # (d) CONTRACT 8절
    assert [e[0].rsplit(".", 1)[1] for e in exp_rows] == ["21", "22", "23", "26"]   # (d) 8절 표의 bin 4개 = (a) showmod 결과
    assert [r.model for r in mc.rows] == [e[0] for e in exp_rows]
    on = (z["ID"] > 0) & (z["GM"] > 0)
    nV = len(z["VDS"])
    for row, (model, mis, i0, i1) in zip(mc.rows, exp_rows):
        refs = [midpoint_ref(z, raw_mid, suf, mi, i0, i1, z["VDSAT"], on) for mi in mis]

        def kmax(key):
            return [max((r[key][k] for r in refs if r[key][k] is not None), default=None) for k in range(nV)]
        assert tuple(row.L_points) == tuple(mids_m[mi] for mi in mis)
        assert (row.n_targets, row.n_inverse_failed) == (sum(r["n_t"] for r in refs), sum(r["n_f"] for r in refs)), model
        _assert_tuple_close(row.id_equivalent_v, kmax("eq"), kmax("eq_bound"), (model, "eq"))
        _assert_tuple_close(row.gm_id_inverse_v, kmax("inv"), kmax("inv_bound"), (model, "inv"))
        vd = kmax("vdsat")
        _assert_tuple_close(row.vdsat_v, vd, [0 if v is None else 8 * gamma_n() * 2.0 for v in vd], (model, "vdsat"))
        assert row.vdsat_v[0] is None                                # k = 0 은 ID = 0 (VDS = 0 열)


# CONTRACT 8절 표(2026-10-08 실측, w_key 1000): (kind, model 접미) -> ((n_targets, 실패), inv mV, eq mV, vdsat mV)
# oracle (d): 계약에 기록된 값(code author 측정 문장). 독립 재계산 대조는 위 test_real_rows_match_independent 가 한다.
CONTRACT_8_TABLE = {
    ("nmos", "26"): ((23520, 0), "518", "18.9", "2.49"), ("pmos", "26"): ((19671, 1569), "316", "22.7", "32.5"),
    ("nmos", "23"): ((23520, 3598), "289", "26.5", "2.87"), ("pmos", "23"): ((22992, 0), "635", "12.8", "1.33"),
    ("nmos", "22"): ((23520, 39), "364", "16.0", "3.28"), ("pmos", "22"): ((22207, 6341), "252", "8.43", "0.79"),
    ("nmos", "21"): ((23520, 3691), "155", "44.6", "6.39"), ("pmos", "21"): ((21850, 0), "648", "21.4", "0.77"),
}


@pytest.mark.lut_realdata
def test_real_contract_measured_summary(real_lut):
    """CONTRACT 8절 표(2026-10-08) 대조: bin 별 목표·실패 수 정확히, VDS 별 max(mV) 는 표기 마지막 자리 반 단위 안."""
    m = new_memo(real_lut)
    seen = set()
    for kind in ("nmos", "pmos"):
        for row in midpoint_l_bin_checks(m, kind, 1000).rows:
            key = (kind, row.model.rsplit(".", 1)[1])
            cnt, inv, eq, vd = CONTRACT_8_TABLE[key]
            seen.add(key)
            assert (row.n_targets, row.n_inverse_failed) == cnt, key
            for got, want in ((max(x for x in row.gm_id_inverse_v if x is not None), inv),
                              (max(x for x in row.id_equivalent_v if x is not None), eq),
                              (max(x for x in row.vdsat_v if x is not None), vd)):
                dec = len(want.split(".")[1]) if "." in want else 0
                assert abs(got / 1e-3 - float(want)) <= 0.5 * 10 ** (-dec), (key, got, want)   # mV 표기 마지막 자리 반 단위
    assert seen == set(CONTRACT_8_TABLE)


@pytest.mark.lut_realdata
def test_real_other_width_width_differs(real_lut, raw_mid):
    """5.1 판정 1: 중점 표 폭 키(1000) ≠ 조회 폭 -> 모든 중점 width_differs. 중점 수 = 중점 파일 L 축 길이(npz 직접, 4)."""
    mc = midpoint_l_bin_checks(new_memo(real_lut), "nmos", 84 if ("nmos", 84) in real_lut.slice_map else 72)
    assert tuple(mc.rows) == ()
    assert len(raw_mid["L"]) == 4
    assert [s[1] for s in mc.skipped] == ["width_differs"] * len(raw_mid["L"])


# ---------------------------------------------------------------------------
# [2026-10-08] 중점 유도 규칙 (CONTRACT 8절, user_decisions 2026-10-08 '7번'): 승인 L 격자의 앵커가 showmod 소속으로 정확히 2개인 bin 마다
# 두 앵커의 중점을 제조 격자로 반올림. 선언(`verification_midpoints_um`)은 이 규칙의 결과여야 한다.
# ---------------------------------------------------------------------------

L_GRID_FILE = SKILL_DIR / "assets" / "sky130_lut_L_grid.json"


def _declared_l_grid():
    return json.loads(L_GRID_FILE.read_text(encoding="utf-8"))


def _derive_midpoints_um(ngspice_bins, tlef, w_ref_m):
    """oracle (a)+(b): 소속 = ngspice showmod 가 (W = w_ref, L = 앵커)에서 고른 bin(시뮬레이터 자체), bin 경계·이름 = PDK 모델 파일을
    test 쪽 파서로 직접 읽은 lmin·lmax(엔진·생성기 코드 미사용). 앵커가 정확히 2개인 bin 의 중점을 tlef MANUFACTURINGGRID 로 반올림.
    반환 ({device: [(model, (a0, a1) µm, 중점 µm)]}, 정렬된 중점 µm 합집합)."""
    L_um = _declared_l_grid()["L_um"]
    grid_um = manufacturing_grid_m(tlef) * 1e6
    w = um(w_ref_m)
    per_dev, mids = {}, set()
    for device, _kind in REAL_DEVICE_KINDS:
        bins = ngspice_bins.query(device, [(w, round(x, 6)) for x in L_um])
        assert all(b is not None for b in bins), (device, bins)        # 18 앵커 모두 유효 모델이 있다
        names = parse_model_bins(ngspice_bins.pm3(device))
        groups = {}
        for x, b in zip(L_um, bins):
            hit = [n for n, v in names.items() if same_bounds(v, b)]
            assert len(hit) == 1, (device, x, b)
            # 4.0.1 규칙 교차 확인: showmod 가 고른 bin 은 lmin ≤ L ≤ lmax 를 만족한다(경계 L 은 아래 bin)
            assert b[0] * 1e6 - 1e-9 <= x <= b[1] * 1e6 + 1e-9, (device, x, b)
            groups.setdefault(hit[0], []).append(x)
        rows = []
        for model, xs in sorted(groups.items(), key=lambda kv: kv[1][0]):
            if len(xs) == 2:
                mid = round(round((xs[0] + xs[1]) / 2 / grid_um) * grid_um, 9)
                rows.append((model, tuple(xs), mid))
                mids.add(mid)
        per_dev[device] = rows
    return per_dev, sorted(mids)


@pytest.mark.lut_realdata
def test_real_declared_midpoints_follow_derivation_rule(ngspice_bins, real_paths, raw_mid):
    """선언 `verification_midpoints_um` = 유도 규칙의 결과 [0.165, 0.85, 1.75, 3.25] (두 소자 모두 같은 bin 4개 .26·.23·.22·.21).
    판별: 옛 선언 (0.165, 6.0, 14.0) 의 6.0·14.0 은 showmod 로 앵커 1개 bin(.20 의 8 µm, .19 의 20 µm) 안이라 규칙이 내지 않는다
    -- 경계 L(4·8 µm)을 위 bin 으로 센 옛 규칙의 값(8절 원인 문장)."""
    per_dev, mids = _derive_midpoints_um(ngspice_bins, real_paths["tlef"], float(raw_mid["w_ref_m"]))
    declared = _declared_l_grid()["verification_midpoints_um"]
    assert mids == declared == [0.165, 0.85, 1.75, 3.25]               # (a) 유도 = (d) 사용자 결정 2026-10-08 '7번' 목록
    for device, rows in per_dev.items():
        assert [r[0].rsplit(".", 1)[1] for r in rows] == ["26", "23", "22", "21"], device
        assert [r[1] for r in rows] == [(0.15, 0.18), (0.7, 1.0), (1.5, 2.0), (2.5, 4.0)], device
    # 옛 중점 6.0·14.0 은 그 bin 의 앵커가 하나뿐(8 µm·20 µm) -- 규칙 밖
    for device, _ in REAL_DEVICE_KINDS:
        L_um = _declared_l_grid()["L_um"]
        w = um(float(raw_mid["w_ref_m"]))
        b_old = ngspice_bins.query(device, [(w, 6.0), (w, 14.0)])
        b_anc = ngspice_bins.query(device, [(w, round(x, 6)) for x in L_um])
        assert [sum(same_bounds(a, b) for a in b_anc) for b in b_old] == [1, 1], device


SWEEP_SCRIPT = SKILL_DIR / "assets" / "sky130_lut_sweep.py"


@pytest.mark.lut_realdata
def test_real_sweep_candidates_emits_derived_midpoints(ngspice_bins, real_paths, raw_mid, tmp_path):
    """생성기 공개 진입점 `sky130_lut_sweep.py candidates`(승인 L 파일 provenance 의 명령 그대로: --l-max-um 20 --discontinuous-um
    0.18,0.25)를 실제로 돌려, 산출 JSON 의 2점 bin 중점 = 위 독립 유도(showmod 소속 + 모델 파일 경계 + tlef 격자) = 선언 목록,
    후보 L = 승인 18점 격자, 소속 model = showmod 독립 조회와 같다.
    oracle: (a) `_derive_midpoints_um`(생성기 코드 미사용) + (d) 승인 L 파일. 실행 시간 실측 2026-10-08: CLI 단독 1092 s, 이 test 651 s --
    ngspice 경계 탐침 sweep 이 대부분이다(보고 대상)."""
    per_dev, mids = _derive_midpoints_um(ngspice_bins, real_paths["tlef"], float(raw_mid["w_ref_m"]))
    declared = _declared_l_grid()
    exe = os.environ.get("GMID_NGSPICE", r"C:\ngspice\Spice64\bin\ngspice_con.exe")
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(exe) + os.pathsep + env.get("PATH", "")
    out = tmp_path / "candidates.json"
    r = subprocess.run([sys.executable, str(SWEEP_SCRIPT), "candidates", "--l-max-um", "20", "--discontinuous-um", "0.18,0.25",
                        "--work", str(tmp_path / "work"), "--out", str(out)],
                       cwd=str(SKILL_DIR), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=3 * 3600)
    assert r.returncode == 0, (r.returncode, r.stdout[-2000:], r.stderr[-4000:])
    got = json.loads(out.read_text(encoding="utf-8"))
    assert got["verification_midpoints_um_two_point_bins"] == mids == declared["verification_midpoints_um"]
    assert got["candidates_um"] == declared["L_um"]
    assert got["compare"]["L_um_equal"] is True and got["compare"]["midpoints_equal"] is True
    assert got["compare"]["sha256"] == hashlib.sha256(L_GRID_FILE.read_bytes()).hexdigest()
    for device, rows in per_dev.items():
        for model, xs, _ in rows:
            for x in xs:
                assert got["bins_at_w_ref"][device]["%g" % x]["model"] == model, (device, x)
