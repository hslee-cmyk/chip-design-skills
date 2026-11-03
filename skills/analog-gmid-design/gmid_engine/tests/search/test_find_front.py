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

from .conftest import PENDING, SKILL_DIR, TESTS_DIR, build_case, circuit_c, front_signature, theta_r4c, write_pdk

SS = (("gain_ss_db", ">=", 10.0, None),)
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
PERF_KEYS_C7 = PERF_KEYS + PERF_BLOCK_KEYS
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
    assert len(PERF_KEYS_C7) == len(set(PERF_KEYS_C7)) == 22
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
    assert set(perf) == set(PERF_KEYS_C7) and len(perf) == 22
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


def test_unmeasured_points_never_in_final_front(tmp_path, lut_sealed, short_root):
    case, fr = _run(tmp_path, lut_sealed, constraints=SS, eval_budget=30, archive_root=short_root,
                    topo=circuit_c(with_cap=True), elements=(("CL", "capacitor", PENDING),))
    assert tuple(fr.front) == ()
    assert len(fr.unmeasured_front) >= 1
    assert all(len(tuple(p.result.unmeasured)) >= 1 for p in fr.unmeasured_front)
    um = [n for n in _notes(fr) if "unmeasured" in json.dumps(n, default=str)]
    assert um and "gain_ss_db" in json.dumps(um, default=str)
    (run,) = [json.loads(x) for x in (Path(short_root) / case.sctx.context_fp / "runs.jsonl")
              .read_text(encoding="utf-8").splitlines() if x.strip()]
    assert run["front"] == [] and len(run["unmeasured_front"]) == len(fr.unmeasured_front)


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
    from gmid_engine.search import evaluate
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


def test_passive_theta_circuit_front_measured(tmp_path, lut_sealed):
    """r6 DEC-92: θ capacitance·ss_resistance 회로 -- 최종 front 점은 ss 제약이 측정되고(행 있음·unmeasured 0), I-1 유지."""
    from .conftest import Z_ELEMENTS, circuit_z, theta_z
    case = build_case(tmp_path, circuit_z(), lut_sealed, elements=Z_ELEMENTS, rbounds=(1e2, 1e6), cbounds=(1e-14, 1e-10),
                      constraints=SS, eval_budget=40)
    fr = find_front(case.sctx, [theta_z(case.dc)])
    perf = dict(fr.perf)
    assert perf["kernel_calls"] == perf["unique_keys"] and perf["recompute_same_key"] == 0
    assert len(fr.front) >= 1
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

CM_PORTS_D = {"ip": ("input", "differential_input_p"), "im": ("input", "differential_input_n"),
              "op": ("output", "differential_output_p"), "om": ("output", "differential_output_n")}
CM_GAIN_VIEW = {"ac_excite": {"ip": 0.5, "im": -0.5}, "sense_p": "op", "sense_n": "om", "sense_mode": "differential"}


def circuit_cmfb_diff():
    from .conftest import mos, topo, two
    return topo("hand_cmfb_diff", [mos("M1", "nmos", "op", "ip", "gnd"), mos("M2", "nmos", "om", "im", "gnd"),
                                   mos("M3", "pmos", "op", "c", "vdd"), mos("M4", "pmos", "om", "c", "vdd")],
                CM_PORTS_D, passives=[two("R1", "resistor", "op", "c"), two("R2", "resistor", "c", "om")])


def _cm_case(tmp, lut, archive_root=None):
    return build_case(tmp, circuit_cmfb_diff(), lut, constraints=(("gain_ss_db", ">=", 0.0, CM_GAIN_VIEW),),
                      elements=(("R1", "resistor", 1e6), ("R2", "resistor", 1e6)), eval_budget=20, archive_root=archive_root)


def test_cm_unconstrained_warning_reaches_run_notes_i22(tmp_path, lut_sealed, short_root):
    """I-22: CMFB 루프가 있고 선언이 없으면 run notes 에 {verdict: warning, code: cm_loop_unconstrained, points ≥ 1}(코드별 하나),
    points ≤ 봉인 점 수(경고는 봉인 점의 ss 평가에서만 나온다). 경고는 notes 외 판정에 영향 없음 -- 다른 notes 는 그대로 있다."""
    case = _cm_case(tmp_path, lut_sealed, short_root)
    fr = find_front(case.sctx, [])
    warn = [dict(n) for n in fr.notes if dict(n).get("verdict") == "warning"]
    assert len(warn) == 1, warn
    assert warn[0]["code"] == "cm_loop_unconstrained"
    lines = [json.loads(x) for x in (Path(short_root) / case.sctx.context_fp / "evals.jsonl").read_text(
        encoding="utf-8").splitlines() if x.strip()]
    n_sealed = sum(1 for x in lines if x["status"] == STATUS_SEALED)
    assert 1 <= warn[0]["points"] <= n_sealed


def test_cm_constrained_circuit_has_no_warning_note(tmp_path, lut_sealed):
    """S-27·I-22: 같은 회로에 pm_cm_ss_deg 를 선언하면 경고 note 가 없다(판정은 제약 행이 맡는다)."""
    case = build_case(tmp_path, circuit_cmfb_diff(), lut_sealed,
                      constraints=(("gain_ss_db", ">=", 0.0, CM_GAIN_VIEW), ("pm_cm_ss_deg", ">=", 60.0, None)),
                      elements=(("R1", "resistor", 1e6), ("R2", "resistor", 1e6)), eval_budget=20)
    fr = find_front(case.sctx, [])
    assert not [n for n in fr.notes if dict(n).get("verdict") == "warning"]


def test_eval_result_warnings_equal_ss_evaluate_i22(tmp_path, lut_sealed, short_root):
    """I-22: 봉인 점의 EvalResult.warnings == 같은 점을 ss_evaluate 로 직접 부른 SsEvaluation.warnings(== ss.warnings), 형식
    (("cm_loop_unconstrained", (("dc_db", 값 > 0),)),); 실패 점은 ()."""
    from gmid_engine.metrics import ss_evaluate
    from gmid_engine.search import STATUS_FAILED, evaluate
    case = _cm_case(tmp_path, lut_sealed, short_root)
    find_front(case.sctx, [])
    lines = [json.loads(x) for x in (Path(short_root) / case.sctx.context_fp / "evals.jsonl").read_text(
        encoding="utf-8").splitlines() if x.strip()]
    sealed = [x for x in lines if x["status"] == STATUS_SEALED]
    assert sealed
    th = {tuple(k): v for k, v in sealed[0]["theta"]}
    r = evaluate(case.sctx, th, tuple(sealed[0]["cells"]))
    assert r.status == STATUS_SEALED
    ssv = ss_evaluate(r.evaluation.sealed, case.sctx.dc, th, case.sctx.ss_constraints, junction=case.sctx.junction)
    assert ssv.warnings == ssv.ss.warnings == r.warnings
    assert len(r.warnings) == 1
    code, det = r.warnings[0]
    assert code == "cm_loop_unconstrained" and [k for k, _ in det] == ["dc_db"] and dict(det)["dc_db"] > 0.0
    failed = [x for x in lines if x["status"] == STATUS_FAILED]
    if failed:
        r2 = evaluate(case.sctx, {tuple(k): v for k, v in failed[0]["theta"]}, tuple(failed[0]["cells"]))
        assert tuple(r2.warnings) == ()


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
    case, fr = _run(tmp_path, lut_sealed, eval_budget=40, constraints=(("area_search_m2", "<=", A_BUDGET, None),))
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
