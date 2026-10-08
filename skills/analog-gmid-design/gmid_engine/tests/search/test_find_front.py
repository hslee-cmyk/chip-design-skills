"""CONTRACT 3.16 [r2·r4] `find_front(sctx, given_starts) -> SearchFront` + I-1·I-2·I-6·I-8 + S-18(W ≥ W_min).

기대값은 계약 문장(키 이름·notes 사유·계수 등식)과 독립 subprocess(PYTHONHASHSEED 1·2) 비교.
"""
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
PERF_KEYS = ("requests", "kernel_calls", "hits", "fail_hits", "disk_hits", "outside_domain", "recompute_same_key",
             "unique_keys", "eval_time_median_s", "wall_s", "lut_memo_evictions", "n_starts", "n_solves", "eval_budget",
             "eval_budget_source", "frozen_columns", "stops_eval_budget", "stops_wall_budget")


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
