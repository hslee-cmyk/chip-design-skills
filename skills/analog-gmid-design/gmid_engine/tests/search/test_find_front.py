"""CONTRACT 3.16 [r2·r4] `find_front(sctx, given_starts) -> SearchFront` + I-1·I-2·I-6·I-8 + S-18(W ≥ W_min).

기대값은 계약 문장(키 이름·notes 사유·계수 등식)과 독립 subprocess(PYTHONHASHSEED 1·2) 비교.
"""
import dataclasses
import importlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from gmid_engine.search import STATUS_PENDING_SEAL7, STATUS_SEALED, SearchFront, find_front

from .conftest import PENDING, SKILL_DIR, TESTS_DIR, build_case, circuit_c, circuit_p, front_signature, theta_p, theta_r4c, write_pdk

SS = (("gain_ss_db", ">=", 10.0, None),)
# [WB-1 v6.38.21, dispute 7.5] 면적 예산·게이트 진입 예산 test 의 회로 입력 = 회로 P (conftest: M1 pmos (out, in, vdd) + R1 (out, gnd), 출력 DC = I·R 을 저항이 정한다).
# 회로 C(nmos 싱크 + 고정 게이트 pmos 전류원 CS 단)는 출력이 고임피던스라 W' 반올림 뒤 입력 고정 KCL 근이 레일 밖이거나 M2 triode 가 되어 front 가 `lost`(fail-closed)로 빈다 --
# 그 판정은 물리적으로 맞으므로 단언·예산 수(8·12·24·40, 면적 예산)는 그대로 두고 W' 실현이 정의되는 회로로 입력만 바꿨다.
P_ELEMENTS = (("R1", "resistor", None),)
P_RBOUNDS = (1e3, 1e6)                       # θ 저항 상자 (손 선택 R = 9e4 를 품는 탐색 정의역 입력)
PERF_KEYS = ("requests", "kernel_calls", "hits", "fail_hits", "outside_domain", "recompute_same_key",
             "unique_keys", "eval_time_median_s", "wall_s", "lut_memo_evictions", "lut_memo_bound", "n_starts", "n_solves",
             "eval_budget", "eval_budget_source", "frozen_columns", "stops_eval_budget", "stops_wall_budget")
# [xrun] interface card C7: find_front perf(그리고 runs.jsonl 줄 perf) 키 집합 = 이 목록 정확히(as-built 에서 디스크 실패 적중 계수 하나만 빠짐,
# 설계 40 v1.10 §2.4.3 '결과 JSON perf' 삭제 행 -- 결과 JSON 형식 변경). 위 PERF_KEYS + 블록 계수 4개.
# [XRUN-F1 card A] interface card xrunf1a C6: 키 `lut_memo_bound` 추가 -> 22개(값 "fixed" | "unfixed_no_kernel_eval"). NFR-4 의
# test_lb_stop_notes_line_exactly_once 도 이 상수를 따라온다.
# [XRUN-F1 card B] interface card xrunf1b C8: 옛 네 칸(block_calls·block_reuses·block_computes·block_recomputes_same_input)을 지우고
# blocks·block_totals·block_index_entries·block_index_bound -> 22개 그대로.
PERF_BLOCK_KEYS = ("blocks", "block_totals", "block_index_entries", "block_index_bound")
OLD_BLOCK_KEYS = ("block_calls", "block_reuses", "block_computes", "block_recomputes_same_input")
PERF_SOLVER_KEYS = ("solver_stops",)      # [WB-1 범위 3a-0, interface 커밋 2] 계측 `perf.solver_stops`(출력 전용): 풀이 종류 {eps, layer0} 별 정지 사유 집계 -> 23개
PERF_WF_KEYS = ("wf_neighbor_evals", "wf_neighbor_wall_s")     # [FS-1 §5 N-5] 이웃 시험 출력 전용 칸 두 개 -> 25개
PERF_KEYS_C7 = PERF_KEYS + PERF_BLOCK_KEYS + PERF_SOLVER_KEYS + PERF_WF_KEYS
BLOCK_ROW_FIELDS = ("calls", "reuses", "grafts", "replays", "computes", "recomputes_same_input")


def _run(tmp, lut, **kw):
    given = kw.pop("given", None)
    case = build_case(tmp, kw.pop("topo", None) or circuit_c(), lut, **kw)
    return case, find_front(case.sctx, [theta_r4c()] if given is None else given)


def _notes(fr):
    return [dict(n) for n in fr.notes]


def test_sealed_run_perf_and_invariants(tmp_path, lut_sealed, short_root):
    case, fr = _run(tmp_path, lut_sealed, constraints=SS, eval_budget=40, archive_root=short_root)
    assert isinstance(fr, SearchFront)
    perf = dict(fr.perf)
    for k in PERF_KEYS:
        assert k in perf, k
    assert any(k.startswith("block_") for k in perf)
    assert perf["kernel_calls"] == perf["unique_keys"]                       # I-1
    assert perf["recompute_same_key"] == 0
    # [r5] 3.16 find_front 는 layer0_start 를 먼저 부르고 그 start 를 start_points 의 첫 후보로 넘긴다(3.12) -> 층 0 + given = 2
    assert perf["eval_budget"] == 40 and perf["n_starts"] == 2
    assert perf["kernel_calls"] <= 40 + len(case.sctx.domain.variables) + 1   # S-17
    lines = (Path(short_root) / case.sctx.context_fp / "evals.jsonl").read_text(encoding="utf-8").splitlines()
    assert len([x for x in lines if x.strip()]) == perf["kernel_calls"]       # I-2
    assert len(fr.front) >= 1
    for p in fr.front:
        assert p.result.status == STATUS_SEALED and tuple(p.result.unmeasured) == ()
    assert re.fullmatch(r"[0-9a-f]{64}", fr.run_id)


def test_perf_key_set_exact_in_result_and_runs_line(tmp_path, lut_sealed, short_root):
    """[xrun XR-7] interface card C7(양성 형식): find_front perf 키 집합과 runs.jsonl 줄 perf 키 집합이 정확히 목록과 같다.
    [XRUN-F1 card A] xrunf1a C6: 22개(lut_memo_bound 추가)."""
    assert len(PERF_KEYS_C7) == len(set(PERF_KEYS_C7)) == 25
    case, fr = _run(tmp_path, lut_sealed, eval_budget=30, archive_root=short_root)
    assert set(dict(fr.perf)) == set(PERF_KEYS_C7)
    (run,) = [json.loads(x) for x in (Path(short_root) / case.sctx.context_fp / "runs.jsonl").read_text(encoding="utf-8")
              .splitlines() if x.strip()]
    assert set(dict(run["perf"])) == set(PERF_KEYS_C7)


def test_perf_blocks_rows_totals_and_index_bound(tmp_path, lut_sealed, short_root):
    """B-T21(XRUN-F1 card B C8): perf 키 22개(옛 블록 계수 네 칸 없음). blocks = 행 목록 {block, part, 여섯 칸}, (block, part) 정렬, 불린 것만,
    행마다 calls = reuses + grafts + replays + computes, 실행 전체(단계 A 의 S1 블록부터) = 그 실행 sctx.dc.counters 의 snapshot. block_totals = test 가
    더한 행 합. block_index_entries = 그 실행 색인 entry_count(). 선언 예산 실행의 block_index_bound = len(blocks) × (E_total + 1),
    E_total = eval_budget + 2 × 정의역 변수 수(test 가 계산). 같은 입력 재계산 0."""
    case, fr = _run(tmp_path, lut_sealed, constraints=SS, eval_budget=40, archive_root=short_root)
    perf = dict(fr.perf)
    assert set(perf) == set(PERF_KEYS_C7) and len(perf) == 25
    assert not set(OLD_BLOCK_KEYS) & set(perf)
    rows = [dict(r) for r in perf["blocks"]]                 # 행 = 칸 이름 -> 값(매핑 또는 (이름, 값) 쌍)
    assert rows, "전제: 블록 행이 있다"
    keys = [(r["block"], r["part"]) for r in rows]
    assert keys == sorted(keys) and len(set(keys)) == len(keys)
    for r in rows:
        assert set(r) == {"block", "part"} | set(BLOCK_ROW_FIELDS)
        assert r["calls"] == r["reuses"] + r["grafts"] + r["replays"] + r["computes"]
        assert r["calls"] >= 1                                                   # 불린 것만
        assert r["recomputes_same_input"] == 0                                   # 같은 입력 재계산 0
    totals = dict(perf["block_totals"])
    assert set(totals) == set(BLOCK_ROW_FIELDS)
    for f in BLOCK_ROW_FIELDS:
        assert totals[f] == sum(r[f] for r in rows), f
    # 실행 전체 = 그 실행 계수(card B C1)의 snapshot -- 단계 A(S1) 블록 행도 들어 있다
    snap = case.sctx.dc.counters.snapshot()
    assert [(b.block, b.part) + tuple(getattr(b, f) for f in BLOCK_ROW_FIELDS) for b in snap.blocks] == [
        (r["block"], r["part"]) + tuple(r[f] for f in BLOCK_ROW_FIELDS) for r in rows]
    assert "s1_structure" in {r["block"] for r in rows}
    assert isinstance(perf["block_index_entries"], int) and not isinstance(perf["block_index_entries"], bool)
    assert perf["block_index_entries"] == case.sctx.dc.donors.entry_count()
    assert perf["eval_budget_source"] == "declared" and perf["eval_budget"] == 40          # 전제: 선언 예산
    e_total = perf["eval_budget"] + 2 * len(case.sctx.domain.variables)
    assert perf["block_index_bound"] == len(rows) * (e_total + 1)
    assert perf["recompute_same_key"] == 0


def test_notes_record_open_items(tmp_path, lut_sealed):
    _, fr = _run(tmp_path, lut_sealed, eval_budget=30)
    notes = _notes(fr)
    reasons = {n.get("reason") for n in notes}
    # [r5] 3.16: 옛 {blocked, layer0_inputs_missing} 대신 층 0 결과 기록
    assert "layer0_inputs_missing" not in reasons
    (l0,) = [n for n in notes if n.get("reason") == "seal_margin_maxmin_centre"]
    assert l0["verdict"] == "layer0_minimal" and l0["rule"] == "DEC-71"
    for k in ("stop", "t", "hard_ok", "start_status", "centre_u", "kernel_calls", "probes", "origin_point"):
        assert k in l0, k
    assert l0["meaning"] == "feasibility_only" and l0["meaning_reason"] == "w_area_upper_bound_undeclared_S-3b"
    assert len(l0["refinements_out_of_scope"]) >= 1
    # 층 0 기록 값 = 같은 입력 새 컨텍스트의 layer0_start 결과(I-15 결정론)
    from gmid_engine.search import layer0_start
    case2 = build_case(tmp_path / "l0", circuit_c(), lut_sealed, eval_budget=30)
    r = layer0_start(case2.sctx)
    assert (l0["stop"], l0["t"], l0["hard_ok"], l0["origin_point"], l0["probes"]) == \
        (r.stop, r.t, r.hard_ok, r.origin_point, r.probes)
    assert "supply_current_dc_needs_counted_rails_declaration" in reasons
    assert any(n.get("rule") == "DEC-79" for n in notes)
    assert any(n.get("rule") == "DEC-72" for n in notes)


def test_pending_points_only_in_pending_front(tmp_path, lut_pending):
    """I-6."""
    _, fr = _run(tmp_path, lut_pending, constraints=SS, eval_budget=30)
    assert tuple(fr.front) == ()
    assert len(fr.pending_front) >= 1
    assert all(p.result.status == STATUS_PENDING_SEAL7 for p in fr.pending_front)
    notes = repr(_notes(fr))
    assert "pending" in notes or "seal" in notes                               # 봉인 7 대기 사유 기록


# [FS-1 A-193 MR-1 삭제] test_unmeasured_points_never_in_final_front (회로 C + 미선언 CL) -- 정본 경로에서 층 0 이 W = 0.5 µm(toy MINW)로 가 실현 m = 1 이 되고 out 손 근이 레일 밖(−1.19 V)이라
# 그 점을 잃는다 (판정 측정). 저항 부하 회로(P)에 미선언 CL 을 달아 시도했으나(rbounds·θ 4 변형) 단일 sealed 점이 실현에서 item 3 실패로 잃어 unmeasured front 가 비었다 -- 실현 조건이 맞는 toy 를 찾지
# 못해 RETIRED 에 기록 (tests/RETIRED_TESTS_fs1.md). 덮이지 않는 것: '미측정 점은 최종 front 에 없다' 의 find_front 수준 단언.


UB1_GATE_FIELDS = ("verdict", "reason", "errors", "checks", "unchecked", "unmeasured", "epsilon_db")


def _ub1_gate_rows(fr):
    return [n for n in _notes(fr) if n.get("rule") == "sensitivity_gate"]


def test_ub1_gate_note_exactly_one_row_with_fields(tmp_path, lut_sealed):
    """[UB-1 E-01, interface C-12] notes 에 rule == "sensitivity_gate" 행이 언제나 정확히 하나, 칸 verdict·reason·errors·checks·unchecked·
    unmeasured·epsilon_db. 사유 규칙(C-10): reason 이 없는 판정은 ok·error 뿐. (판정 값 자체는 회로 의존 -- 손으로 못 정하므로 규칙만.)"""
    _, fr = _run(tmp_path, lut_sealed, eval_budget=30)
    rows = _ub1_gate_rows(fr)
    assert len(rows) == 1
    g = rows[0]
    for k in UB1_GATE_FIELDS:
        assert k in g, k
    assert g["verdict"] in ("ok", "error", "undeterminable", "gate_empty")
    assert (g["reason"] is None) == (g["verdict"] in ("ok", "error"))


def test_ub1_gate_note_front_empty(tmp_path, lut_sealed, short_root):
    """[interface C-12] front 가 비면 게이트 행은 gate_empty / front_empty (C 값 없는 용량으로 front 가 빈 입력 -- 위 test 와 같은 구성)."""
    _, fr = _run(tmp_path, lut_sealed, constraints=SS, eval_budget=30, archive_root=short_root,
                 topo=circuit_c(with_cap=True), elements=(("CL", "capacitor", PENDING),))
    assert tuple(fr.front) == ()
    rows = _ub1_gate_rows(fr)
    assert len(rows) == 1
    assert rows[0]["verdict"] == "gate_empty" and rows[0]["reason"] == "front_empty"
    for k in UB1_GATE_FIELDS:
        assert k in rows[0], k


def test_front_points_respect_w_min(tmp_path, lut_sealed):
    """S-18: W_min 을 시작점 W 보다 크게 선언(시작점은 w_min 행 음수) -> front 점은 모두 W ≥ W_min(w_min 행 c ≥ 0)."""
    from .conftest import evaluate      # [FS-1 서명 맞춤] 손 wf 를 끼운 evaluate 래퍼
    pdk = write_pdk(tmp_path / "bigw", minw_um="100")
    case, fr = _run(tmp_path, lut_sealed, eval_budget=40, pdk=pdk)
    w_min = case.sctx.domain.w_min_m
    r0 = evaluate(case.sctx, tuple(sorted(theta_r4c().items())), (0, 1))
    assert any(c.name.startswith("w_min:") and c.c < 0 for c in r0.constraints)        # 시작점은 위반
    assert len(fr.front) >= 1                                                            # 탐색이 W 를 키워 들어온다
    for p in tuple(fr.front) + tuple(fr.pending_front) + tuple(fr.unmeasured_front):
        ops = dict(p.result.evaluation.snapshot.column("device", "dc_op"))
        assert all(op.W >= w_min for op in ops.values()), p.point_id
        assert all(c.c >= 0 for c in p.result.constraints if c.name.startswith("w_min:"))


def test_run_id_deterministic_in_process(tmp_path, lut_sealed):
    _, a = _run(tmp_path / "a", lut_sealed, eval_budget=30)
    _, b = _run(tmp_path / "b", lut_sealed, eval_budget=30)
    _, c = _run(tmp_path / "c", lut_sealed, eval_budget=31)
    assert a.run_id == b.run_id and front_signature(a) == front_signature(b)
    assert c.run_id != a.run_id


def test_g7_new_process_twice_bit_identical_wf_start_dc_finger_w_key():
    """[FS-1 G-7] 같은 입력을 새 프로세스에서 두 번(PYTHONHASHSEED 1·2) 돌리면 wf_start·front 점 dc_finger·DeviceOp.w_key 가 비트(float.hex)로 같다.
    공허 방지: front 점 >= 1, wf_start 칸 >= 1."""
    outs = []
    for seed in ("1", "2"):
        code = ("import sys; sys.path[:0] = [%r, %r]; from search.conftest import fs1_determinism_probe; "
                "print(fs1_determinism_probe())" % (str(SKILL_DIR), str(TESTS_DIR)))
        env = dict(os.environ, PYTHONHASHSEED=seed)
        p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=900)
        assert p.returncode == 0, p.stderr[-3000:]
        outs.append(json.loads(p.stdout.strip().splitlines()[-1]))
    assert outs[0]["wf_start"] and outs[0]["front"]
    assert outs[0] == outs[1]


def test_hashseed_independent_front(tmp_path):
    """I-8: 같은 입력·같은 선언 E_B, stops_wall_budget == 0 이면 PYTHONHASHSEED 무관 같은 front (별도 프로세스)."""
    outs = []
    for seed in ("1", "2"):
        d = tmp_path / ("p" + seed)
        d.mkdir()
        code = ("import sys; sys.path[:0] = [%r, %r]; from search.conftest import determinism_probe; "
                "print(determinism_probe(sys.argv[1]))" % (str(SKILL_DIR), str(TESTS_DIR)))
        env = dict(os.environ, PYTHONHASHSEED=seed)
        p = subprocess.run([sys.executable, "-c", code, str(d)], capture_output=True, text=True, env=env, timeout=600)
        assert p.returncode == 0, p.stderr[-3000:]
        outs.append(json.loads(p.stdout.strip().splitlines()[-1]))
    assert outs[0]["wall"] == 0 and outs[1]["wall"] == 0
    assert outs[0] == outs[1]
    assert outs[0]["front"]


def test_eval_budget_derived_and_recorded(tmp_path, lut_sealed):
    """1.1: eval_budget None -> evaluate 가 한 번 유도, perf 에 'derived_once:...@n_evals=<n+1>' 기록."""
    case, fr = _run(tmp_path, lut_sealed, eval_budget=None, budget_s=2.0)
    perf = dict(fr.perf)
    m = re.fullmatch(r"derived_once:floor\(B/median_t_eval\)@n_evals=(\d+)", str(perf["eval_budget_source"]))
    assert m, perf["eval_budget_source"]
    assert int(m.group(1)) == len(case.sctx.domain.variables) + 1
    assert isinstance(perf["eval_budget"], int) and perf["eval_budget"] > 0


def circuit_pz():
    """저항 부하 P (M1 pmos (out, in, vdd) + R1 (out, gnd)) + 수동소자 θ 회로 Rz (out, x) + Cz (x, gnd)."""
    from .conftest import mos, topo, two
    return topo("hand_pz", [mos("M1", "pmos", "out", "in", "vdd")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                passives=[two("R1", "resistor", "out", "gnd"), two("Rz", "resistor", "out", "x"), two("Cz", "capacitor", "x", "gnd")])


def theta_pz(dc, cz=1e-12, rz=1e4, i=1e-5, r=9e4, vgs=0.6, l1=1e-6):
    """회로 PZ 의 θ = 회로 P 의 θ (conftest theta_p 와 같은 손 식) + 수동소자 θ. 성분 키는 스키마(입력)에서 읽는다."""
    from .conftest import r4_ln_idu, schema_of
    comps = set(schema_of(dc).components)
    th = {("L", "M1"): l1, ("ln_idu", "M1"): r4_ln_idu("pmos", vgs, 1.8 - i * r, 0.0), ("resistance", "R1"): r,
          ("capacitance", "Cz"): cz, ("ss_resistance", "Rz"): rz}
    for k in comps:
        if k[0] == "current":
            th[k] = i
    assert set(th) == comps, (sorted(th), sorted(comps))
    return th


def assert_realized_roots_inside_rails(fr):
    """전제 (손, 저항 부하 P): front 점마다 실현 잔차 r(= dc_finger.residual) 로 out KCL 손 근이 레일 안 -- `wb1_hand.source_load_kcl_at_vdd` > 0 (a = I·R)."""
    from sizing.conftest import LAM
    from wb1_hand import source_load_kcl_at_vdd
    assert len(fr.front) >= 1
    for p in fr.front:
        th = dict(p.result.theta)
        res = th[("resistance", "R1")]
        cur = next(v for k, v in th.items() if k[0] == "current")
        r = dict(p.result.evaluation.snapshot.column("device", "dc_finger"))["M1"].residual
        assert source_load_kcl_at_vdd(1.8, res, cur, cur * res, r, LAM) > 0.0, (res, cur, r)


def test_passive_theta_circuit_front_measured(tmp_path, lut_sealed):
    """r6 DEC-92: θ capacitance·ss_resistance 회로 -- 최종 front 점은 ss 제약이 측정되고(행 있음·unmeasured 0), I-1 유지."""
    # [FS-1 A-193 MR-1] 회로 = 저항 부하 P + 수동소자 θ (Rz, Cz): 정본 경로에서 실현 조건이 맞는 toy (회로 C 는 층 0 의 W = MINW 점이 실현에서 레일 밖 근으로 사라진다).
    case = build_case(tmp_path, circuit_pz(), lut_sealed, elements=P_ELEMENTS + (("Rz", "resistor", None), ("Cz", "capacitor", None)),
                      rbounds=P_RBOUNDS, cbounds=(1e-14, 1e-10), constraints=SS, eval_budget=40)
    fr = find_front(case.sctx, [theta_pz(case.dc)])
    perf = dict(fr.perf)
    assert perf["kernel_calls"] == perf["unique_keys"] and perf["recompute_same_key"] == 0
    assert len(fr.front) >= 1
    assert_realized_roots_inside_rails(fr)                                      # 전제 (손): 실현 점의 out 근이 레일 안
    for p in fr.front:
        assert tuple(p.result.unmeasured) == ()
        assert any(c.name.startswith("ss:") for c in p.result.constraints)
        th = dict(p.result.theta)
        assert 1e-14 <= th[("capacitance", "Cz")] <= 1e-10 and 1e2 <= th[("ss_resistance", "Rz")] <= 1e6


# =====================================================================================================================
# [CM 0e487b3] search CONTRACT I-22 경고 표면: SsEvaluation.warnings -> EvalResult.warnings -> find_front run notes
# {verdict: "warning", code, points}. 회로: 완전 차동 CS 쌍 + PMOS 부하, 부하 gate c = 출력 저항 평균(R1·R2) -- CMFB 루프가 있는데
# pm_cm_ss_deg 를 선언하지 않았다(metrics 7.11 '보고 전용' + 경고 조건 T_cm(0) > 1: CM 이득 ≈ gmp/(gds_n + gds_p) ≫ 1).
# 기대값은 계약 문장(키·코드 이름)과 같은 점의 ss_evaluate 직접 호출(등식 I-22).
# =====================================================================================================================

# [FS-1 A-190 M-2a 삭제] test_cm_unconstrained_warning_reaches_run_notes_i22·test_cm_constrained_circuit_has_no_warning_note·test_eval_result_warnings_equal_ss_evaluate_i22
# (+ circuit_cmfb_diff·_cm_case) -- CMFB 루프 toy 는 단계 A 가 `unsupported_rule_branch|loop_record_only|...|global_feedback_or_cross_coupled` 로 정지시킨다 (실측).
# 루프를 없애면 test 대상(cm_loop_unconstrained 경고)이 사라지므로 toy 를 고칠 수 없다. tests/RETIRED_TESTS_fs1.md.


# ---------------------------------------------------------------- [r11, 사용자 결정 11] 면적 예산 선언 spec (S-3b 닫힘, 3.22)
# oracle (d) 계약 S-3b 문장: 예산 선언 spec -> notes {"verdict": "closed", "rule": "S-3b"}, 층 0 meaning_reason = w_bounded_by_area_budget,
# 예산 없는 spec -> {"verdict": "provisional", "rule": "S-3b"}. oracle (a) 물리 불변식: front 점은 판정 제약 면적 행 c ≥ 0 ⇔ 면적 ≤ A,
# 면적 = Σ W·L(회로 C 는 수동소자 없음) ≥ 어느 소자 하나의 W·L. 행 c = (A − 면적)/b_A 는 원 값(SLSQP 척도 배 없음).

A_BUDGET = 1e-10        # 회로 C 시작점(theta_r4c) Σ W·L ≈ 6.7e-11 m² 보다 크게 고른 구성 입력 -- 시작점이 예산 안


def test_budget_closes_s3b_note_and_layer0_reason(tmp_path, lut_sealed):
    _, fr = _run(tmp_path, lut_sealed, eval_budget=30, constraints=(("area_search_m2", "<=", A_BUDGET, None),))
    notes = _notes(fr)
    s3b = [n for n in notes if n.get("rule") == "S-3b"]
    assert len(s3b) == 1 and s3b[0]["verdict"] == "closed"
    assert not any(n.get("rule") == "S-3b" and n.get("verdict") == "provisional" for n in notes)
    (l0,) = [n for n in notes if n.get("reason") == "seal_margin_maxmin_centre"]
    assert l0["meaning_reason"] == "w_bounded_by_area_budget"


def test_no_budget_keeps_s3b_provisional(tmp_path, lut_sealed):
    _, fr = _run(tmp_path, lut_sealed, eval_budget=30)
    s3b = [n for n in _notes(fr) if n.get("rule") == "S-3b"]
    assert len(s3b) == 1 and s3b[0]["verdict"] == "provisional"


def test_front_points_inside_area_budget(tmp_path, lut_sealed):
    # [dispute 7.5] 회로 입력만 회로 P(저항 부하, 면적 = 수동소자 제외 Σ W·L 이라 아래 단언 그대로)로 바꿨다. 예산 A_BUDGET 은 그대로이고, 회로 P 는 게이트 이득 제약
    # 없이는 front 가 비므로(수동소자 θ 가 있는 회로의 탐색 입력) 이득 제약 SS 를 함께 선언한다 -- 면적 행 단언과 무관한 구성 입력.
    case = build_case(tmp_path, circuit_p(), lut_sealed, eval_budget=40, elements=P_ELEMENTS, rbounds=P_RBOUNDS,
                      constraints=(("area_search_m2", "<=", A_BUDGET, None),) + SS)
    fr = find_front(case.sctx, [theta_p(case.dc)])
    b_a = case.sctx.domain.area_resolution_m2
    assert len(fr.front) >= 1
    for p in fr.front:
        area = p.result.objectives.area_m2
        ops = dict(p.result.evaluation.snapshot.column("device", "dc_op"))
        wl = [op.W * op.L for op in ops.values()]
        (row,) = [c for c in p.result.constraints if c.name == "spec:area_search_m2<="]
        assert row.c >= 0, p.point_id
        assert area <= A_BUDGET
        assert row.c == pytest.approx((A_BUDGET - area) / b_a, rel=1e-9)
        assert area == pytest.approx(sum(wl), rel=1e-12)
        assert area >= max(wl)


# =====================================================================================================================
# [NFR-4 card 2] interface card nfr4c2 C3(실행 환경 지문 기록 두 곳 중 S3 runs 줄)·C5(L-b 정지 사유 notes 한 줄).
# oracle: (식) 계약 문장(키 이름·notes 형식·키워드 전용 인자 목록), (비교) 같은 함수 두 출력(runs 줄 env_fp 대 test 의 fp_of(blas_environment())),
# (독립) S3 파일 읽기. 피검 함수로 기대값을 만들지 않는다.
# =====================================================================================================================

LB_STOP_KEYS = {"class", "l_from", "stop", "accepted"}
LB_STOPS = {"converged", "eval_budget", "wall_budget"}


def _lines(root, ctx_fp, name):
    return [json.loads(x) for x in (Path(root) / ctx_fp / name).read_text(encoding="utf-8").splitlines() if x.strip()]


def test_env_fp_in_runs_line_not_in_evals(tmp_path, lut_sealed, short_root):
    """N-T14: archive 있는 toy 실행 -- runs 줄 최상위 `env_fp` = 같은 프로세스 fp_of(blas_environment()), evals 줄에는 `env_fp` 가 없다,
    build_search_context 의 키워드 전용 인자 = (code_fp,)(서명 불변)."""
    import inspect
    from gmid_engine.search import build_search_context
    case, fr = _run(tmp_path, lut_sealed, eval_budget=30, archive_root=short_root)
    (run,) = _lines(short_root, case.sctx.context_fp, "runs.jsonl")
    assert "env_fp" in run, sorted(run)                                        # C3: runs 줄 최상위 키
    from gmid_engine.core import blas_environment, fp_of
    assert run["env_fp"] == fp_of(blas_environment())                          # (비교) 같은 프로세스의 같은 함수 출력
    evals = _lines(short_root, case.sctx.context_fp, "evals.jsonl")
    assert evals and all("env_fp" not in e for e in evals)
    kwonly = tuple(n for n, p in inspect.signature(build_search_context).parameters.items() if p.kind is p.KEYWORD_ONLY)
    assert kwonly == ("code_fp",)


def _l_search_notes(notes):
    return [dict(n) for n in notes if dict(n).get("verdict") == "l_search"]


def test_lb_stop_notes_line_exactly_once(tmp_path, lut_sealed, short_root):
    """N-T18 (find_front 쪽): L-b 가 도는 toy(회로 C, front 점 있음)에서 SearchFront.notes 와 runs 줄 notes 에 `l_search` 줄이 정확히
    하나 -- {"verdict": "l_search", "rule": "LR10", "stops": [...]}, stops 원소 키 = {class, l_from, stop, accepted}, stop ∈ 세 사유, accepted 는
    0 이상 정수. perf 키 집합은 그대로(PERF_KEYS_C7 -- 위 test_perf_key_set_exact_in_result_and_runs_line 와 같은 목록)."""
    case, fr = _run(tmp_path, lut_sealed, constraints=SS, eval_budget=40, archive_root=short_root)
    assert len(fr.front) >= 1                                                  # 전제: 풀이된 점이 있어 L-b 가 돈다
    (ls,) = _l_search_notes(fr.notes)
    assert set(ls) == {"verdict", "rule", "stops"} and ls["rule"] == "LR10"
    assert isinstance(ls["stops"], (list, tuple)) and len(ls["stops"]) >= 1
    for st in ls["stops"]:
        st = dict(st)
        assert set(st) == LB_STOP_KEYS, st
        assert st["stop"] in LB_STOPS and isinstance(st["accepted"], int) and st["accepted"] >= 0, st
    (run,) = _lines(short_root, case.sctx.context_fp, "runs.jsonl")
    (rls,) = _l_search_notes(run["notes"])
    assert rls == json.loads(json.dumps(ls))                                   # runs 줄 notes 와 SearchFront.notes 가 같은 줄
    assert set(dict(fr.perf)) == set(PERF_KEYS_C7)


def test_lb_stop_notes_empty_when_lb_never_runs(tmp_path, lut_sealed):
    """N-T18 (find_front 쪽): 모든 평가가 실패하는 빈 창 회로(풀이된 점 0 -> L-b 가 돌 출발점이 없다)에서도 `l_search` 줄이 정확히 하나이고
    stops = [](C5 'L-b 가 돌지 않았으면 stops 빈 목록'). 회로 = test_layer0_center 의 빈 창 회로와 같은 손 회로(MA nmos (x, vdd, vdd) -> x ≥ V(vdd),
    MB pmos (x, gnd, gnd) -> x ≤ V(gnd): 창이 비어 모든 평가가 empty_window 실패)."""
    from .conftest import mos, topo
    window = topo("hand_empty_window_lb",
                  [mos("MA", "nmos", "x", "vdd", "vdd"), mos("MB", "pmos", "x", "gnd", "gnd"), mos("MC", "nmos", "x", "inp", "gnd")],
                  {"inp": ("input", "single_ended_input"), "x": ("output", "single_ended_output")})
    _, fr = _run(tmp_path, lut_sealed, eval_budget=20, topo=window, given=[])
    assert tuple(fr.front) == tuple(fr.pending_front) == tuple(fr.unmeasured_front) == ()   # 전제: 풀이된 점 0
    (ls,) = _l_search_notes(fr.notes)
    assert json.loads(json.dumps(ls)) == {"verdict": "l_search", "rule": "LR10", "stops": []}


# =====================================================================================================================
# [XRUN-F1 card A] interface card xrunf1a C6: perf `lut_memo_bound` = 탐색 memo bound_state 가 "fixed" 면 "fixed", 첫 커널 평가 없이 끝났으면
# "unfixed_no_kernel_eval"(예외 아님). oracle (식) 계약 문장. 커널 평가 유무는 perf kernel_calls(전제)로 확인한다.
# =====================================================================================================================

def test_lut_memo_bound_fixed_after_kernel_eval(tmp_path, lut_sealed, short_root):
    """A-T13: 커널 평가가 있는 실행 -- perf·runs 줄 perf 의 lut_memo_bound == "fixed"."""
    case, fr = _run(tmp_path, lut_sealed, eval_budget=30, archive_root=short_root)
    perf = dict(fr.perf)
    assert perf["kernel_calls"] > 0                                            # 전제
    assert perf["lut_memo_bound"] == "fixed"
    (run,) = _lines(short_root, case.sctx.context_fp, "runs.jsonl")
    assert dict(run["perf"])["lut_memo_bound"] == "fixed"


def test_lut_memo_bound_unfixed_without_kernel_eval(tmp_path, lut_sealed, monkeypatch):
    """A-T14: 첫 커널 평가 없이 끝난 실행 -- lut_memo_bound == "unfixed_no_kernel_eval", 예외 없음.
    만드는 방법(구성): find_front 의 모듈 속성 `layer0_start`(NFR-4 관찰 지점, xrunf1a C2)를 '시작점 없음' 층 0 결과로 바꾸고(그 결과 =
    같은 입력의 **다른** 컨텍스트에서 진짜 layer0_start 를 부른 frozen dataclass 에서 start 만 None -- 이 실행의 탐색 memo 는 건드리지 않는다),
    주는 시작점은 원뿔 밖 θ(전류 −1e-5 -> outside_domain, 커널 0 -- test_kernel 의 원뿔 밖 입력과 같음) 하나."""
    ff_mod = importlib.import_module("gmid_engine.search.find_front")
    from gmid_engine.search import layer0_start
    other = build_case(tmp_path / "other", circuit_c(), lut_sealed, eval_budget=30)
    no_start = dataclasses.replace(layer0_start(other.sctx), start=None)
    monkeypatch.setattr(ff_mod, "layer0_start", lambda sctx, *a, **k: no_start)
    case = build_case(tmp_path / "run", circuit_c(), lut_sealed, eval_budget=30)
    fr = find_front(case.sctx, [theta_r4c(i2=-1e-5)])
    perf = dict(fr.perf)
    assert perf["kernel_calls"] == 0 and perf["outside_domain"] >= 1          # 전제: 커널 평가 0, 원뿔 밖 판정은 있었다
    assert perf["lut_memo_bound"] == "unfixed_no_kernel_eval"
    assert set(perf) == set(PERF_KEYS_C7)


# =====================================================================================================================
# [XRUN-F1 card C] interface card xrunf1c C8 (C-T11·C-T13) -- 감도 게이트 진입 때 kernel_calls <= 탐색 예산, 게이트 안 커널 평가 수 <= R,
# front 점이 있으면 탐색 예산을 다 써도 게이트가 돈다, 끝 확인(kernel_calls > E_total -> RuntimeError), perf.block_index_bound 식.
# 관찰 지점(J-3) = find_front 모듈의 전역 이름 run_sensitivity_gate. oracle: (손) 정의 -- 선언 E_B 에서 R = 2 n_θ, E_total = E_B + R.
# 구성: 회로 C(n_θ = 4, R = 8), 선언 E_B ∈ {8, 12, 24, 40} -- 탐색 묶음(층 0·끝점·ε·L-b)이 이 예산을 넘기는 합성 입력(옛 동작은 한 묶음을 끝까지
# 쓴 뒤 예산을 확인해 게이트 진입 때 kernel_calls 가 E_B 를 넘었다).
# =====================================================================================================================

def _gated_run(tmp_path, lut, monkeypatch, e_b, inject=None, resistive=False):
    """resistive=True (dispute 7.5): 회로 C 대신 회로 P(저항 부하) -- W' 실현이 정의되는 회로. 기본(False)은 회로 C 그대로(다른 test 불변)."""
    ff_mod = importlib.import_module("gmid_engine.search.find_front")
    if resistive:
        case = build_case(tmp_path, circuit_p(), lut, eval_budget=e_b, constraints=SS, elements=P_ELEMENTS, rbounds=P_RBOUNDS)
    else:
        case = build_case(tmp_path, circuit_c(), lut, eval_budget=e_b, constraints=SS)
    s = case.sctx
    seen = []
    real = ff_mod.run_sensitivity_gate

    def wrapped(sctx, *a, **k):
        entry = dict(sctx.counters)["kernel_calls"]
        out = real(sctx, *a, **k)
        seen.append((entry, dict(sctx.counters)["kernel_calls"]))
        if inject is not None:
            sctx.counters["kernel_calls"] += inject
        return out
    monkeypatch.setattr(ff_mod, "run_sensitivity_gate", wrapped)
    return case, s, seen


@pytest.mark.parametrize("e_b", [8, 12, 24, 40])
def test_gate_entry_budget_kernel_calls_within_search_budget(tmp_path, lut_sealed, monkeypatch, e_b):
    case, s, seen = _gated_run(tmp_path, lut_sealed, monkeypatch, e_b, resistive=True)      # [dispute 7.5] 회로 P (n_θ = 3, R = 6): 선언 E_B 별 R = 2 n_θ 는 s.domain 에서 읽는다
    fr = find_front(s, [theta_p(case.dc)])
    r = 2 * len(s.domain.variables)
    assert len(fr.front) >= 1                                                   # 전제: front 점이 있다
    assert len(seen) == 1, seen                                                 # 탐색 예산을 다 써도 게이트가 돈다
    assert not [n for n in fr.notes if dict(n).get("verdict") == "not_run" and "gate" in repr(n).lower()]   # 게이트 not_run 없음
    entry, after = seen[0]
    assert entry <= e_b, (entry, e_b)                                           # 진입 때 kernel_calls <= 탐색 예산
    assert after - entry <= r                                                   # 게이트 안 커널 평가 수 <= R
    assert dict(fr.perf)["kernel_calls"] <= e_b + r                             # <= E_total


def test_gate_entry_budget_end_check_violation_runtime_error(tmp_path, lut_sealed, monkeypatch):
    # 주입: 게이트가 끝난 직후 kernel_calls 를 E_total + 1 이상으로 올린다 -> 끝 확인(kernel_calls > E_total)이 RuntimeError.
    # [dispute 8.2, card 범위 7 (b)·R-18] 게이트 대상 = 실현 front 첫 점이므로 입력 회로는 실현 front 가 비지 않는 회로 P(resistive=True)다 (회로 C 의 탐색 front 점은
    # 실현 관문에서 lost 라 게이트 호출 0). 공허하지 않음 = 게이트가 실제로 불렸다(seen == 1, 끝 확인 전 단언).
    e_b = 24
    case, s, seen = _gated_run(tmp_path, lut_sealed, monkeypatch, e_b, inject=10 ** 6, resistive=True)
    with pytest.raises(RuntimeError):
        find_front(s, [theta_p(case.dc)])
    assert len(seen) == 1                                                       # 게이트가 불렸다 (불리지 않았다면 RuntimeError 는 다른 원인)


def test_gate_entry_budget_perf_declared_and_block_index_bound(tmp_path, lut_sealed, short_root):
    case, fr = _run(tmp_path, lut_sealed, constraints=SS, eval_budget=12, archive_root=short_root)
    perf = dict(fr.perf)
    assert set(perf) == set(PERF_KEYS_C7) and len(perf) == 25                   # perf 키 23개 그대로(WB-1 solver_stops 추가)
    assert perf["eval_budget_source"] == "declared" and perf["eval_budget"] == 12
    e_total = 12 + 2 * len(case.sctx.domain.variables)                          # 손: E_B + R
    assert perf["block_index_bound"] == len(perf["blocks"]) * (e_total + 1)


def test_gate_entry_budget_donors_bound_opened_and_closed(tmp_path, lut_sealed, monkeypatch):
    # oracle (손): C8 '진입에서 donors.open_bound(...), 끝 확인 뒤 donors.close_bound()' -- 같은 실행 색인의 두 메서드를 감싸 호출 수·순서를 본다.
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=12, constraints=SS)
    s = case.sctx
    cls = type(s.dc.donors)
    log = []
    real_open, real_close = cls.open_bound, cls.close_bound

    def op(self, total_of):
        log.append(("open", total_of()))
        return real_open(self, total_of)

    def cl(self):
        log.append(("close", None))
        return real_close(self)
    monkeypatch.setattr(cls, "open_bound", op)
    monkeypatch.setattr(cls, "close_bound", cl)
    find_front(s, [theta_r4c()])
    e_total = 12 + 2 * len(s.domain.variables)
    assert [k for k, _ in log] == ["open", "close"]
    assert log[0][1] == e_total                                                 # total_of() = E_total


# ---------------------------------------------------------------- C-T13 무동작 (green 유지)

@pytest.mark.slow
def test_gate_entry_budget_same_input_same_trajectory_and_no_shortfall_escape(tmp_path, lut_sealed, monkeypatch):
    """C-T13 무동작(interface C-T13, green 유지): E_B 를 넉넉히 선언한 합성 실행 -- `eval_budget` 정지 사유 0, shortfall 0, 궤적(θ·seq) 동일 쌍 비교.
    oracle (c)꼴 구성: 이 toy 가 예산 없이 스스로 끝나는 kernel_calls(감사 실측 7892)보다 훨씬 큰 두 E_B(20000, 100000)는 둘 다 안 닿는다.
    예산이 안 닿는 실행은 E_B 값과 무관해야 하므로 두 실행의 궤적(front 서명 = θ·목적, 커널 수, 요청 수, notes)이 같아야 한다.
    각 실행: perf.stops_eval_budget 0(= 반복 중·첫 스텝 FdBudgetShortfall 어느 것도 정지 사유 eval_budget 으로 안 닿음), stops_wall_budget 0,
    kernel_calls < E_B(예산을 다 쓰지 않음), notes 에 eval_budget 사유 0, 게이트는 1회 돈다. (느림: 실행 하나 약 5분 -> --run-slow 표지.)"""
    ff_mod = importlib.import_module("gmid_engine.search.find_front")
    real, calls = ff_mod.run_sensitivity_gate, []
    monkeypatch.setattr(ff_mod, "run_sensitivity_gate", lambda *a, **k: (calls.append(1), real(*a, **k))[1])
    sigs = []
    for name, e_b in (("a", 20000), ("b", 100000)):
        del calls[:]
        _, fr = _run(tmp_path / name, lut_sealed, constraints=SS, eval_budget=e_b)
        perf = dict(fr.perf)
        assert len(calls) == 1
        assert len(fr.front) >= 1
        assert perf["stops_eval_budget"] == 0 and perf["stops_wall_budget"] == 0
        assert perf["kernel_calls"] < e_b                                       # 예산을 다 쓰지 않았다
        notes = json.dumps(_notes(fr), sort_keys=True, default=str)
        assert "eval_budget" not in notes
        sigs.append((front_signature(fr), perf["kernel_calls"], perf["requests"], notes))
    assert sigs[0] == sigs[1]


def test_gate_entry_derives_budget_when_evaluations_at_most_n_theta(tmp_path, lut_sealed, monkeypatch):
    # [XRUN-F1 card C 판정 Major-2] interface C-T11 '평가 n_θ 이하 실행의 게이트 전 유도' (C8: sweep_front 뒤 게이트 전에 search_ceiling(final=True)).
    # oracle (구성): eval_budget None 실행에서 sweep_front 가 끝난 직후 평가 시간 기록을 평가 1개(= 0.5^12 s, 이진 정확값, n_θ + 1 미만)로
    # 되돌리고 eval_budget 을 None 으로 되돌린다. 손: D = ⌊B / 중앙값⌋ = ⌊2.0 / 2^-12⌋ = 8192. 게이트 진입 때 sctx.eval_budget == 8192 이고
    # 출처가 유도 표지여야 한다(final=True 호출이 없으면 None 으로 남는다).
    ff_mod = importlib.import_module("gmid_engine.search.find_front")
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=None, budget_s=2.0, constraints=SS)
    s = case.sctx
    n = len(s.domain.variables)
    src0 = s.eval_budget_source
    real_sweep, real_gate, seen = ff_mod.sweep_front, ff_mod.run_sensitivity_gate, []

    def sweep(*a, **k):
        out = real_sweep(*a, **k)
        s.eval_budget = None                                                    # 구성: 아직 유도 전 상태
        s.eval_budget_source = src0
        del s.eval_times[:]
        s.eval_times.append(2.0 ** -12)                                         # 평가 1개 <= n_θ
        return out

    def gate(sctx, *a, **k):
        seen.append((sctx.eval_budget, sctx.eval_budget_source))
        return real_gate(sctx, *a, **k)
    monkeypatch.setattr(ff_mod, "sweep_front", sweep)
    monkeypatch.setattr(ff_mod, "run_sensitivity_gate", gate)
    assert 1 <= n                                                               # 전제: 평가 1개 <= n_θ
    fr = find_front(s, [theta_r4c()])
    assert len(seen) == 1, seen
    assert seen[0][0] == 8192, seen
    assert re.fullmatch(r"derived_once:floor\(B/median_t_eval\)@n_evals=\d+", str(seen[0][1])), seen
    assert dict(fr.perf)["eval_budget"] == 8192


# =====================================================================================================================
# [WB-1 개정 셋째·넷째·다섯째] R-17 (unmeasured_front 도 실현 관문 + 실현 뒤 재분류) · R-18 (감도 게이트 대상 ∈ 실현 front). oracle (손) interface §6 '관문'·§10 R-17·R-18.
# 입력 = R-2 회로 + 출력 용량 CL(`wb1_flow.circuit_r2_cl`): CL 미선언 -> gain_ss_db 행 미측정(unmeasured), 선언 -> 측정. 점 둘 = 층 L 1e-6 / 2e-6 의 θ (R-5 가 둘 다
# 실현 가능함을 보인 입력). 관찰 지점(§9) = find_front 모듈 전역 `sweep_front`·`realize_front`·`run_sensitivity_gate`, realize_front 모듈 전역 `evaluate`.
# =====================================================================================================================

def _wb1_points(tmp_path, cl, ids=("u0", "u1"), archive_root=None):
    from gmid_engine.search import FrontPoint
    from .conftest import evaluate      # [FS-1 서명 맞춤] 손 wf 를 끼운 evaluate 래퍼
    from .wb1_flow import R2_CELLS, R2_ELEMENTS, bins_case, circuit_r2_cl, r2_theta, sorted_theta
    case = bins_case(tmp_path, circuit_r2_cl(), elements=R2_ELEMENTS + (("CL", "capacitor", cl),), eval_budget=60, archive_root=archive_root)
    ths = (sorted_theta(r2_theta(case.dc)), sorted_theta(r2_theta(case.dc, l=2e-6)))
    cells = (R2_CELLS, (1, 1, 1, 1))
    evs = [evaluate(case.sctx, th, c) for th, c in zip(ths, cells)]
    return case, [FrontPoint(i, e, ()) for i, e in zip(ids, evs)], ths


def _stubbed_find_front(case, monkeypatch, front, unmeasured, wrap_evaluate=None, gate_log=None):
    """sweep_front 를 front / unmeasured_front 가 정해진 stub 로, realize_front·(선택) realize_front.evaluate·run_sensitivity_gate 를 감싸 find_front 를 돈다."""
    from .wb1_flow import r2_theta
    ff = sys.modules["gmid_engine.search.find_front"]
    rf_mod = sys.modules["gmid_engine.search.realize_front"]
    real_sweep, real_rf, real_gate = ff.sweep_front, ff.realize_front, ff.run_sensitivity_gate
    rec = []

    def sweep(*a, **k):
        out = dict(real_sweep(*a, **k))
        out["front"], out["unmeasured_front"] = tuple(front), tuple(unmeasured)
        return out

    def rf(sctx, points):
        o = real_rf(sctx, points)
        rec.append((tuple(points), o))
        return o

    def gate(sctx, base, *a, **k):
        if gate_log is not None:
            gate_log.append(base)
        return real_gate(sctx, base, *a, **k)
    monkeypatch.setattr(ff, "sweep_front", sweep)
    monkeypatch.setattr(ff, "realize_front", rf)
    monkeypatch.setattr(ff, "run_sensitivity_gate", gate)
    if wrap_evaluate is not None:
        real_eval = rf_mod.evaluate
        monkeypatch.setattr(rf_mod, "evaluate", lambda *a, **k: wrap_evaluate(real_eval, *a, **k))
    return find_front(case.sctx, [r2_theta(case.dc)]), rec


def _run_line(short_root, case):
    (run,) = [json.loads(x) for x in (Path(short_root) / case.sctx.context_fp / "runs.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    return run


def _result_of(x):
    return getattr(x, "result", x)


def test_r17_unmeasured_front_points_pass_the_realize_gate_and_failed_one_is_lost(tmp_path, monkeypatch, short_root):
    """R-17: front 0점·unmeasured_front 2점(둘 다 봉인, 미측정 행 있음; 하나는 실현 봉인 실패로 강제). `realize_front` 호출에 두 점이 전달되고(호출 >= 1),
    결과 unmeasured_front = 남은 1점의 **실현 값**, 미측정 사유로 빠지지 않으며 실패 점은 `realize.lost`(사유 있음). base = 실현 없이 반환 (red)."""
    from gmid_engine.core import SealViolationError
    from gmid_engine.search import STATUS_SEALED
    case, (u0, u1), ths = _wb1_points(tmp_path / "pts", PENDING, archive_root=short_root)
    assert u0.result.status == u1.result.status == STATUS_SEALED
    assert len(tuple(u0.result.unmeasured)) >= 1 and len(tuple(u1.result.unmeasured)) >= 1        # 전제: 미측정 행 있음
    bad = tuple(u1.result.theta)

    def forced(real, sctx, theta, *a, **k):
        if tuple(theta) == bad:
            raise SealViolationError(devices=("M1",), margin=0.5, detail={"item": 7, "reason": "wb1_test_forced_failure"})
        return real(sctx, theta, *a, **k)
    fr, rec = _stubbed_find_front(case, monkeypatch, (), (u0, u1), wrap_evaluate=forced)
    assert len(rec) >= 1                                                                          # 양성 대조: 관문이 불렸다 (호출 0 이면 red)
    assert {p.point_id for pts, _ in rec for p in pts} == {"u0", "u1"}                          # unmeasured_front 점이 realize_front 로 전달
    out = rec[0][1]
    assert tuple(fr.front) == () and [p.point_id for p in fr.unmeasured_front] == ["u0"]
    assert fr.unmeasured_front[0].result is out.points[0].result and fr.unmeasured_front[0].result is not u0.result      # 실현 값
    lost = {pid: (reason, detail) for pid, reason, detail in out.lost}
    assert set(lost) == {"u1"} and lost["u1"][0] and lost["u1"][0] != "realized_spec_unmeasured"  # 미측정 사유로 빠지지 않음
    run = _run_line(short_root, case)                                                            # 결과 JSON: 집합 둘 = 실현 값, 실패 점은 realize.lost
    real = dict(run["realize"])
    assert run["front"] == [] and len(run["unmeasured_front"]) == 1
    assert real["n_lost"] == 1 and "u1" in json.dumps(real["lost"], default=str) and "realized_spec_unmeasured" not in json.dumps(real, default=str)


def test_r17_unmeasured_point_whose_realized_row_is_measured_moves_to_front(tmp_path, monkeypatch, short_root):
    """R-17 (i) [넷째 R-M2]: 탐색 unmeasured_front 점의 실현 평가에서 미측정 행이 0 (실현 평가 결과의 미측정 칸을 비운 꼴) -> 결과 front 에 들어가고 `realize.moved` =
    (점, unmeasured_front, front), `realized_spec_unmeasured` 사유 0."""
    case, pts, _ = _wb1_points(tmp_path / "pts", PENDING, archive_root=short_root)
    seen = {"n": 0}

    def cleared(real, *a, **k):
        res = real(*a, **k)
        seen["n"] += 1
        return dataclasses.replace(res, unmeasured=())
    fr, rec = _stubbed_find_front(case, monkeypatch, (), tuple(pts), wrap_evaluate=cleared)
    assert seen["n"] >= 1 and len(rec) >= 1                                                       # 양성 대조: 감쌈이 실제 realize 평가에 닿았다
    ids = {p.point_id for p in fr.front}
    assert ids and ids <= {"u0", "u1"} and tuple(fr.unmeasured_front) == ()                      # front 로 이동 (front 지배 재필터를 거친 부분집합)
    run = _run_line(short_root, case)
    real = dict(run["realize"])
    moved = [list(m) for m in real["moved"]]
    for pid in ids:
        assert [pid, "unmeasured_front", "front"] in moved, (pid, moved)
    assert "realized_spec_unmeasured" not in json.dumps(real, default=str) and rec[0][1].lost == ()


def test_r17_front_point_whose_realized_row_is_unmeasured_moves_to_unmeasured_front(tmp_path, monkeypatch, short_root):
    """R-17 (ii) [넷째 R-M2]: 탐색 front 점의 실현 평가에 미측정 행이 생김(같은 감쌈으로 미측정 하나를 더함) -> 결과 unmeasured_front (lost 아님), `realize.moved` =
    (점, front, unmeasured_front), `realized_spec_unmeasured` 사유 0. 미측정 행의 모양 = 실제 미측정 결과에서 가져온 한 항목."""
    case, pts, _t = _wb1_points(tmp_path / "meas", 1e-12, archive_root=short_root)               # CL 선언 -> 측정 점
    assert all(len(tuple(p.result.unmeasured)) == 0 for p in pts)                               # 전제: 측정
    _c2, (s0, _s1), _t2 = _wb1_points(tmp_path / "unm", PENDING)
    row = tuple(s0.result.unmeasured)[0]                                                         # 실제 미측정 항목 하나 (모양 출처)
    seen = {"n": 0}

    def added(real, *a, **k):
        res = real(*a, **k)
        seen["n"] += 1
        return dataclasses.replace(res, unmeasured=tuple(res.unmeasured) + (row,))
    fr, rec = _stubbed_find_front(case, monkeypatch, tuple(pts), (), wrap_evaluate=added)
    assert seen["n"] >= 1 and len(rec) >= 1
    ids = {p.point_id for p in fr.unmeasured_front}
    assert ids and ids <= {"u0", "u1"} and tuple(fr.front) == () and rec[0][1].lost == ()
    moved = [list(m) for m in dict(_run_line(short_root, case)["realize"])["moved"]]
    for pid in ids:
        assert [pid, "front", "unmeasured_front"] in moved, (pid, moved)
    assert "realized_spec_unmeasured" not in json.dumps(dict(_run_line(short_root, case)["realize"]), default=str)


def test_r18_sensitivity_gate_target_is_a_realized_front_point(tmp_path, monkeypatch, short_root):
    """R-18: front 2점, realize_front 가 첫 탐색 점을 lost 로(봉인 실패 꼴) -> 게이트가 본 점 ∈ 실현 front (남은 점의 실현 값 결과, 탐색 첫 점 아님), 게이트 호출 >= 1.
    base = 탐색 front 첫 점 (red)."""
    from gmid_engine.core import SealViolationError
    case, (p0, p1), _t = _wb1_points(tmp_path / "pts", 1e-12, ids=("p0", "p1"))
    bad = tuple(p0.result.theta)

    def forced(real, sctx, theta, *a, **k):
        if tuple(theta) == bad:
            raise SealViolationError(devices=("M1",), margin=0.5, detail={"item": 7, "reason": "wb1_test_forced_failure"})
        return real(sctx, theta, *a, **k)
    gate_log = []
    fr, rec = _stubbed_find_front(case, monkeypatch, (p0, p1), (), wrap_evaluate=forced, gate_log=gate_log)
    out = rec[0][1]
    assert [p.point_id for p in out.points] == ["p1"] and [pid for pid, _r, _d in out.lost] == ["p0"]   # 전제: 첫 탐색 점만 lost
    assert [p.point_id for p in fr.front] == ["p1"]
    assert len(gate_log) >= 1                                                                    # 양성 대조: 게이트가 돌았다
    seen = [_result_of(b) for b in gate_log]
    assert all(s is out.points[0].result for s in seen)                                          # 게이트가 본 점 = 실현 front 의 점 (실현 값 결과)
    assert all(s is not p0.result and s is not p1.result for s in seen)                          # 탐색 첫 점도, 탐색 값도 아니다


def test_r18_empty_realized_front_skips_the_gate_and_records_no_target(tmp_path, monkeypatch, short_root):
    """R-18 둘째 꼴: 두 점 모두 lost -> 실현 front 가 비어 게이트 호출 0, 게이트 행 = gate_empty / front_empty('대상 없음' 기록; interface C-12)."""
    from gmid_engine.core import SealViolationError
    case, (p0, p1), _t = _wb1_points(tmp_path / "pts", 1e-12, ids=("p0", "p1"))
    bad = {tuple(p0.result.theta), tuple(p1.result.theta)}
    calls = {"n": 0}

    def forced(real, sctx, theta, *a, **k):
        calls["n"] += 1
        if tuple(theta) in bad:
            raise SealViolationError(devices=("M1",), margin=0.5, detail={"item": 7, "reason": "wb1_test_forced_failure"})
        return real(sctx, theta, *a, **k)
    gate_log = []
    fr, rec = _stubbed_find_front(case, monkeypatch, (p0, p1), (), wrap_evaluate=forced, gate_log=gate_log)
    assert calls["n"] >= 2 and len(rec) >= 1                                                     # 양성 대조: 두 점 모두 realize 평가를 거쳐 lost
    assert len(rec[0][1].lost) == 2 and tuple(fr.front) == ()
    assert gate_log == []                                                                        # 실현 front 가 비면 게이트 호출 0
    rows = _ub1_gate_rows(fr)
    assert len(rows) == 1 and rows[0]["verdict"] == "gate_empty" and rows[0]["reason"] == "front_empty"


# =====================================================================================================================
# [FS-1 O-2·N-5] 출발 불능 진입(초기 wf None) 과 이웃 시험 perf 칸. 회로 = u13 toy (출발 블록을 거친 sctx -- wf_start 가 있다).
# oracle (식) interface card 20261107-fs1 §6: initial_wf(base) None -> 평가 0회, notes {"verdict": "start_undefined", "rule": "DEC-108 (3)", "records": [...]},
# front·pending·unmeasured_front 빈 tuple. §5 perf: wf_neighbor_evals = 이웃 시험 중 w_f 이동 평가 수 (spy 로 센 값), wf_neighbor_wall_s >= 0.
# =====================================================================================================================
def _u13_toy():
    from .u13_hand import cs_chain, toy_case
    return toy_case(cs_chain(2), elements=(("C1", "capacitor", 1e-12), ("C2", "capacitor", 2e-12)),
                    constraints=(("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0)))


def test_o2_start_undefined_means_no_evaluation_and_empty_front():
    """O-2 (A-190 M-3): 동작 대체 stub 없음 -- `graph/start: wf_start` 의 한 칸 w_key 를 None 으로 쓴 손 스냅샷 입력(S-6 꼴 결과 값)으로 만든 sctx."""
    import dataclasses
    from gmid_engine.search import initial_wf
    from sizing.conftest import tamper
    case = _u13_toy()
    base = case.sctx.dc.base
    assert initial_wf(base) is not None                                               # 양성 대조: 출발이 정의된 toy
    cells = base.value("graph", "start", "wf_start")
    broken = (dataclasses.replace(cells[0], w_key=None),) + tuple(cells[1:])
    case.sctx.dc = dataclasses.replace(case.sctx.dc, base=tamper(base, "start_intervals", "graph", "wf_start", {"start": broken}))
    assert initial_wf(case.sctx.dc.base) is None
    k0 = dict(case.sctx.counters)["kernel_calls"]
    fr = find_front(case.sctx, [])
    assert dict(case.sctx.counters)["kernel_calls"] == k0 == 0
    notes = [dict(n) for n in fr.notes]
    hit = [n for n in notes if n.get("verdict") == "start_undefined"]
    assert len(hit) == 1 and hit[0]["rule"] == "DEC-108 (3)" and "records" in hit[0]
    assert fr.front == () and fr.pending_front == () and fr.unmeasured_front == ()


def test_n5_perf_has_wf_neighbor_columns_equal_to_spied_count(monkeypatch):
    lb = sys.modules["gmid_engine.search.l_bin_search"]
    orig, seen = lb.evaluate, []

    def spy(sctx, theta, cells, wf, *a, **k):
        seen.append(tuple(wf.keys))
        return orig(sctx, theta, cells, wf, *a, **k)
    monkeypatch.setattr(lb, "evaluate", spy)
    case = _u13_toy()
    base = tuple(case.sctx.dc.base.value("graph", "start", "wf_start")[i].w_key for i in range(len(case.sctx.dc.base.value("graph", "start", "wf_start"))))
    fr = find_front(case.sctx, [])
    perf = dict(fr.perf)
    assert "wf_neighbor_evals" in perf and "wf_neighbor_wall_s" in perf
    # 이 toy LUT 는 kind 당 슬라이스 하나라 w_f 이동 후보가 없다 -> spy 로 센 w_f 이동(= 출발 키와 다른 wf.keys) 평가 0 = perf 값
    assert perf["wf_neighbor_evals"] == sum(1 for k in seen if k != base)
    assert isinstance(perf["wf_neighbor_wall_s"], float) and perf["wf_neighbor_wall_s"] >= 0.0
