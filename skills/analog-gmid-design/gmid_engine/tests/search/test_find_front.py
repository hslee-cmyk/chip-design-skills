"""CONTRACT 3.16 [r2·r4] `find_front(sctx, given_starts) -> SearchFront` + I-1·I-2·I-6·I-8 + S-18(W ≥ W_min).

기대값은 계약 문장(키 이름·notes 사유·계수 등식)과 독립 subprocess(PYTHONHASHSEED 1·2) 비교.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path


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
    assert perf["eval_budget"] == 40 and perf["n_starts"] == 1
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
    assert "layer0_inputs_missing" in reasons
    l0 = [n for n in notes if n.get("reason") == "layer0_inputs_missing"][0]
    assert l0.get("verdict") == "blocked" and len(l0.get("missing", ())) >= 1
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
