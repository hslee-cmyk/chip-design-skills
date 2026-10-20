"""`dc_tolerances(snapshot, lut)` -- 소자별 tol_V 셀과 tol_I 의 gm 필드.

근거: 설계 40 v1.6 §3.7-3(tol_I), §2.4.8 소유표 `device: dc_gm` 행, §2.4.11.
- `device.dc_tol_v` = tol_v_table(kind, w_key).at(L, vds, "id_equivalent") (CONTRACT 6절 tol 행, 이번 개정에서 바뀌지 않음).
- `device.dc_gm` = 그 소자 ID × 그 동작점(L, VGS, VDS, VSB)의 LUT gm/ID. writer 는 `dc_tolerances` 하나(dc 단계). parent(S2p)를 읽지
  않는다. 옛 `dc_gm_bound`(S2p gm/ID 또는 곡선 격자 최대 gm 상계) 필드는 폐기(§3.7-3 '폐기').

기대값:
- tol_V: toy LUT npz 배열에 lut 계약 5절 id_equivalent LOO 정의(r5 Hermite·Richardson)를 직접 적용(conftest `Oracle.tol_v`).
- dc_gm: conftest `hand_dc_gm` -- 이 test 가 LUT 파일(npz)을 직접 열어 GM/ID 격자를 그 동작점에서 보간한 값 × dc_op.current.
  손 확인: toy 파일의 GM/ID = B − C·VGS(conftest 해석식)라 기대값은 닫힌 식 (B − C·vgs)·ID 와도 같아야 한다(두 독립 경로 대조).
피검 함수로 기대값을 만들지 않는다. dc_op(동작점 좌표·전류)는 피검 블록의 입력이다.
"""
import math

import pytest

from gmid_engine.sizing import S2_WRITERS, dc_tolerances

from .conftest import (A, B, C, TOY_VGS, W_M, Oracle, hand_dc_gm, mos_table, rel_close, run_blocks, run_of, theta_a,
                       theta_c, toy_npz)


def test_oracle_tol_hand_value():
    # 손계산(r5): VGS(2차)·VDS(1차) Hermite LOO 는 정확(0), VS 선형 LOO 오차 A·h² (h = 0.45), Richardson ÷ 2^2,
    # gm/ID 최소 = B − 1.8·C
    assert rel_close(Oracle.tol_v(), A * 0.45 ** 2 / 4 / (B - 1.8 * C), 1e-9)


def test_block_declaration_writes_dc_gm_not_bound():
    """§2.4.8 소유표: `device: dc_gm` 의 writer = `dc_tolerances`(writer 1개). 옛 `dc_gm_bound` 필드는 권한표에도 블록 writes 에도 없다."""
    assert set(dc_tolerances.writes) == {("device", "dc_tol_v"), ("device", "dc_gm")}
    assert S2_WRITERS.writer_of("device", "dc_gm") == dc_tolerances.name == "dc_tolerances"
    assert S2_WRITERS.writer_of("device", "dc_gm_bound") is None


@pytest.mark.parametrize("which", ["C", "A"])
def test_values(ctx_c, ctx_a, toy_lut_paths, which):
    """dc_tol_v = Oracle.tol_v(모든 셀 같음), dc_gm = ID × LUT 파일 gm/ID(그 동작점). 소자 집합 = S1 MOS 전부."""
    ctx, th = (ctx_c[2], theta_c()) if which == "C" else (ctx_a[2], theta_a())
    snap = run_blocks(ctx, th)
    out = dc_tolerances(snap, ctx.lut, **run_of(ctx))
    tol = dict(out.column("device", "dc_tol_v"))
    gm = dict(out.column("device", "dc_gm"))
    mt = mos_table(snap)
    assert set(tol) == set(mt) == set(gm)
    ops = dict(snap.column("device", "dc_op"))
    manifest = toy_lut_paths[0]
    for m in mt:
        assert rel_close(tol[m], Oracle.tol_v(), 1e-9), m
        op = ops[m]
        want = hand_dc_gm(lambda kind: toy_npz(manifest, kind), op)
        assert rel_close(want, (B - C * op.vgs) * op.current, 1e-12), m       # 두 독립 경로(파일 보간 / 해석식) 대조
        assert rel_close(gm[m], want, 1e-9), (m, gm[m], want)


def test_dc_gm_is_own_operating_point_not_curve_max(ctx_c, toy_lut_paths):
    """§3.7-3 '폐기하는 근거': 봉인 3 허용오차의 gm 은 곡선 전체 최대(상계)가 아니라 **이 후보 동작점**의 값이다. toy 의 곡선 최대 gm
    (VGS 격자 마디 위 ID·gm/ID 최댓값 × W/w_m, conftest 해석식)은 vgs 0.6·0.7 점의 gm 보다 훨씬 크므로 둘을 구별할 수 있다 -- 값이
    동작점 gm 과 같고 곡선 최대와 다름을 함께 단언한다."""
    ctx = ctx_c[2]
    snap = run_blocks(ctx, theta_c())
    gm = dict(dc_tolerances(snap, ctx.lut, **run_of(ctx)).column("device", "dc_gm"))
    for m, op in snap.column("device", "dc_op"):
        own = hand_dc_gm(lambda kind: toy_npz(toy_lut_paths[0], kind), op)
        curve_max = max(math.exp(math.log(W_M / op.L) + Oracle.ln_idu(op.kind, v, op.vds, op.vsb)) * Oracle.gm_id(v)
                        for v in TOY_VGS) * op.W / W_M
        assert curve_max > 10 * own, m                                          # 전제: 구별 가능
        assert rel_close(gm[m], own, 1e-9), m


def test_l_not_anchor_fails_before_tolerance(ctx_c):
    """L 이 앵커가 아니면 tol 셀에 닿기 전 좌표 역산에서 lut_query_failed(계속하지 않음)."""
    from gmid_engine.core import SealViolationError
    with pytest.raises(SealViolationError):
        run_blocks(ctx_c[2], theta_c(l1=1.7e-6))
