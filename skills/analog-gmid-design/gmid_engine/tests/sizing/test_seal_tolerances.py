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

from .conftest import (A, B, C, TOY_VGS, W_M, Oracle, hand_dc_gm, ja_state, mos_table, rel_close, run_blocks, run_of,
                       theta_a, theta_c, toy_npz)


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


# ---------------------------------------------------------------------------
# [LM-1e §5 J-a] 셀 결합: 결합 셀 하나가 None 이면 dc_tol_v 가 None -> 봉인 1·2·3 의 그 행이 undefined -> 보고 undefined
# 입력 = toy R(pmos 의 VDS index 0 열이 꺼져 tol 셀 0 = None) + `_scc_s_doc`(M1 nmos (vin, nb1, gnd), M2 nmos (vout, nb2, vin),
# M3 pmos (vout, pb, vdd)) + 손 θ. 스냅샷에서 `dc_op["M3"]` 의 `vds` 만 0.1 로 바꾼다(`dataclasses.replace` + conftest `tamper`;
# `dc_tol_v` 는 주입하지 않는다 -- None 은 `dc_tolerances` 가 `table_at` 으로 낸다): VDS 0.1 은 칸 [0, 0.25) = 셀 0(None)·셀 1(값) 결합.
# oracle: (a) 구성(꺼진 열의 셀은 정의상 None) + (d) 결합 규칙('하나라도 None 이면 None', 계획 표 10행·A-139 집계: 항에 None 이 하나라도 있으면 None).
# ---------------------------------------------------------------------------

SEAL_WRITERS_PASS = {6: "dc_seal_bulk_reverse", 7: "dc_seal_region", 8: "dc_seal_kvl_branch", 9: "dc_seal_region"}


def _ja_items(ctx, snap):
    """봉인 1·2·3 블록을 차례로 돌린다(블록 함수 그대로). 반환 (스냅샷, {번호: SealItem})."""
    from gmid_engine.sizing import dc_seal_kcl, dc_seal_node_conflict, dc_seal_vgs_match
    from .conftest import seal_item
    s = dc_seal_node_conflict(snap, **run_of(ctx))
    s = dc_seal_vgs_match(s, **run_of(ctx))
    s = dc_seal_kcl(s, (), **run_of(ctx))
    return s, {n: seal_item(s, n) for n in (1, 2, 3)}


def _nets_with_m3_on_path(snap):
    """N3 = M3 가 스냅샷 `node.dc_path_values` 경로 소자(PathValue.relation = (관계 종류, 원소))인 넷. 봉인 1·3 행의 tol 은 이 경로 소자의
    tol 에서 온다(interface §5 J-a, 위임 A-159 (3)(c)). 넷 이름을 test 가 박지 않고 스냅샷 열에서 유도한다(oracle (a): 구성으로 정해진 집합).
    N3 가 비면 전제 실패(멈추고 보고)."""
    pv = dict(snap.column("node", "dc_path_values"))
    n3 = sorted(net for net, vals in pv.items() if any(len(p.relation) > 1 and p.relation[1] == "M3" for p in vals))
    if not n3:
        pytest.fail("전제 실패(멈추고 보고): M3 가 dc_path_values 경로 소자인 넷이 없다 -- N3 비어 있음")
    return n3


def _m3_kcl_row_nets(snap):
    """K3 = 봉인 3 이 보는 넷 중 M3 가 닿는 것 = M3 채널 끝 넷(스냅샷 `dc_current_basis.ends` 의 M3 항목 드레인·소스) ∖ 봉인 3 제외 넷.
    제외 넷 = 레일(`node.is_rail`) ∪ 입력 포트(`node.port_direction == "input"`) ∪ `bias_inputs`(gate 전용이라 채널 끝에 들지 않음) -- 이상 전압원 넷이라
    KCL 잔차 미정의(계획 봉인 3 정의). 넷 이름을 박지 않고 toy 연결에서 유도(A-163). K3 가 비면 전제 실패."""
    from gmid_engine.sizing import DC_KEY
    basis = snap.value("graph", DC_KEY, "dc_current_basis")
    excluded = ({n for n, r in snap.column("node", "is_rail") if r} | {n for n, d in snap.column("node", "port_direction") if d == "input"})
    k3 = sorted({net for name, f, t in basis.ends if name == "M3" for net in (f, t)} - excluded)
    if not k3:
        pytest.fail("전제 실패(멈추고 보고): M3 채널 끝 넷 ∖ 제외 넷(K3)이 비어 있다")
    return k3


def test_cell_combine_j_a0_premise_no_failing_rows(tmp_path):
    """전제 J-a0(안 서면 J-a 의 기대가 이 입력으로 성립하지 않는다 -- `judge` 는 실패를 먼저 본다): M3 가 닿는 봉인 행(봉인 2 의 M3 행,
    N3 = M3 가 `dc_path_values` 경로 소자인 넷의 봉인 1·3 행)에 실패 행이 없다. 결합 규칙과 무관하게 서는 전제다(실패 판정은 정의된 행만 본다)."""
    from gmid_engine.sizing import SEAL_FAIL
    ctx, _th, _changed, snap = ja_state(tmp_path)
    _nets_with_m3_on_path(snap)                                         # N3 비어 있지 않음 (봉인 1 행)
    _m3_kcl_row_nets(snap)                                              # K3 비어 있지 않음 (봉인 3 행)
    _s, items = _ja_items(ctx, snap)
    for n, it in items.items():
        assert it.status != SEAL_FAIL, (n, it.status, it.devices, it.nodes)


def test_cell_combine_j_a_none_cell_cascades_to_seals_and_report(tmp_path):
    from gmid_engine.sizing import (DC_KEY, REPORT_UNDEFINED, SEAL_PASS, SEAL_UNDEFINED, DcEvaluation, SealItem, dc_seal_report)
    from gmid_engine.search import STATUS_UNDEFINED, seal_status
    ctx, _th, changed, snap = ja_state(tmp_path)
    tolv = dict(snap.column("device", "dc_tol_v"))
    assert dict(changed.column("device", "dc_op"))["M3"].vds == 0.1
    assert tolv["M3"] is None                                           # table_at 경유: 칸 [0, 0.25) 의 셀 0 이 None
    assert tolv["M1"] is not None and tolv["M2"] is not None            # 다른 소자(nmos)의 셀은 정의
    s, items = _ja_items(ctx, snap)
    assert all(it.status != "fail" for it in items.values())            # J-a0 전제
    assert items[2].status == SEAL_UNDEFINED and "M3" in items[2].devices
    n3 = _nets_with_m3_on_path(snap)                                    # N3: 유도(넷 이름을 박지 않음)
    k3 = _m3_kcl_row_nets(snap)                                         # K3: 봉인 3 이 보는 M3 채널 끝 넷(유도)
    want = {1: n3, 3: k3}                                               # 봉인 1 = N3 각 넷, 봉인 3 = K3 각 넷 [A-163]
    for n in (1, 3):
        assert items[n].status == SEAL_UNDEFINED, n
        for net in want[n]:                                             # 그 넷의 행 tol = None -> 그 item undefined
            assert net in items[n].nodes, (n, net, items[n].nodes)
    # 나머지 항목(4~9)은 이 test 의 대상이 아니다 -- pass 로 두고 보고서 상태 규칙만 본다(fail 있으면 violated, undefined 있으면 undefined).
    for n, w in SEAL_WRITERS_PASS.items():
        s = s.write(w, "t-%d-pass" % n, {("graph", "dc_seal_%d" % n): {DC_KEY: SealItem(n, SEAL_PASS)}})
    rep = dc_seal_report(s, SealItem(4, SEAL_PASS), SealItem(5, SEAL_PASS), **run_of(ctx)).value("graph", DC_KEY, "dc_seal_report")
    assert rep.status == REPORT_UNDEFINED
    assert seal_status(DcEvaluation(None, rep, None)) == STATUS_UNDEFINED == "seal_undefined"


def test_cell_combine_j_a_control_defined_cells_stay_values(tmp_path):
    """대조(판별): M3 의 vds 만 0.5 (칸 [0.5, 0.75) -- 켜진 칸)로 바꾸면 tol 이 모두 정의라 봉인 1·2·3 이 pass(undefined 아님)."""
    from gmid_engine.sizing import SEAL_PASS
    ctx, _th, _changed, snap = ja_state(tmp_path, vds=0.5)
    assert all(v is not None for v in dict(snap.column("device", "dc_tol_v")).values())
    _s, items = _ja_items(ctx, snap)
    assert {n: it.status for n, it in items.items()} == {1: SEAL_PASS, 2: SEAL_PASS, 3: SEAL_PASS}
