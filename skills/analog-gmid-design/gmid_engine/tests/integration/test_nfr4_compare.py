"""[NFR-4 card 2] 비교기 `nfr4_compare.py` 단위 test N-T24~N-T28 (interface card nfr4c2 C7, 설계 40 §2.4.13 (2)~(5)). 엔진을 돌리지 않는다.

oracle (손): 실행 기록을 손으로 만든다(칸 부류·값·구역·분해능 인자·context·전제 칸). 기대 판정은 계약 문장 그대로다 -- 1차 검사 = 비트 동일 집합(T 만 뺌),
다르면 FAIL(필드별로 넘어가지 않음), 필드별 = D 정확히 같음·C |Δ| ≤ 분해능(같은 구역 D 가 같을 때만)·K·T 보고만, 전제 위반·분해능 자료 없음 = 판정 불능.
분해능 기대값(N-T26)은 설계 40 §2.4.13 (4) 표의 식을 손 숫자에 적용한 값이다(비교기 출력을 기대값으로 쓰지 않는다).
"""
from __future__ import annotations

import copy
import json
import math
import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nfr4_compare as N  # noqa: E402

GRID, WMIN = 5e-9, 4.2e-7                                   # 손: PDK 격자·최소 폭
RAILS = {"vdd": 1.8, "vss": -0.9, "gnd": 0.0}              # 손: 레일 전위
TOL_I = {"vdd": 2e-9, "vss": 3e-9, "gnd": 5e-9}            # 손: 레일 전류 허용오차


def h(x):
    return float(x).hex()


def flip_lsb(x):
    """float 의 가수 마지막 비트를 뒤집은 값(1 ulp 차)."""
    (n,) = struct.unpack("<q", struct.pack("<d", x))
    return struct.unpack("<d", struct.pack("<q", n ^ 1))[0]


def F(cls, value, zone, kind=None, fp=False, **res):
    f = {"cls": cls, "value": value, "zone": zone}
    if fp:
        f["fp"] = True
    if kind is not None:
        f["res"] = dict(kind=kind, **res)
    return f


def record():
    """손으로 만든 실행 기록 하나(탐색 있는 실행, 전제 성립)."""
    return {
        "format": N.FORMAT, "circuit": "hand", "code_fp": "K1", "searched": True,
        "env_fp": [["stage_a", "E1"], ["runs", "E1"]],
        "eval_budget_source": "declared", "stops_wall_budget": 0,
        "stop_values": [["layer0/stop", "converged"], ["sweep/solves/EP:s1/stop", "slsqp_8"], ["notes/l_search/stops[0]/stop", "converged"]],
        "context": {"grid_m": GRID, "w_min_m": WMIN, "rails": dict(RAILS), "node_mos": {"n1": ["M1", "M2"], "n2": []},
                    "mos_tol_v": {"M1": 2e-3, "M2": 1e-3}},
        "fields": {
            "stage_a/status": F("D", "ok", "stage_a"),
            "eval/1/status": F("D", "sealed", "eval:1"),
            "eval/1/constraints/w_min:M1/c": F("C", h(2.5), "eval:1", "c"),
            "eval/1/objectives/power_w": F("C", h(1e-6), "eval:1", "power", tol_i=dict(TOL_I)),
            "eval/1/objectives/area_m2": F("C", h(3e-12), "eval:1", "area"),
            "eval/2/status": F("D", "failed", "eval:2"),
            "eval/2/failure/margin": F("C", h(0.25), "eval:2", "margin"),
            "layer0/t": F("C", h(0.75), "layer0", "t"),
            "layer0/iterations": F("K", 5, "layer0"),
            "perf/kernel_calls": F("K", 40, "perf"),
            "perf/wall_s": F("T", h(1.23), "perf"),
            "s0/graph/kernel/theta_schema": F("D", "fp-schema-1", "s0"),
        },
    }


def mutate(rec, path, value):
    out = copy.deepcopy(rec)
    out["fields"][path]["value"] = value
    return out


# ---------------------------------------------------------------- N-T24 1차 검사 (같은 환경)

def test_nfr4_cmp_first_pass_identical_records_pass():
    rep = N.first_pass(record(), record())
    assert (rep["verdict"], rep["undecidable"], rep["diffs"], rep["fieldwise"]) == ("PASS", 0, [], False)


@pytest.mark.parametrize("path, cls", [("stage_a/status", "D"), ("eval/1/constraints/w_min:M1/c", "C"), ("perf/kernel_calls", "K")])
def test_nfr4_cmp_first_pass_last_bit_change_fails(path, cls):
    """비트 동일 집합 칸 하나(D·C·K 각각)의 마지막 비트를 바꾼 기록 -> FAIL. 필드별로 넘어가지 않는다: C 칸은 1 ulp(분해능 1 안)라 필드별 비교면
    PASS 인데 1차 검사는 FAIL 이고, 보고에 필드별 판정(PASS·판정 불능·분해능)이 없다."""
    base = record()
    v = base["fields"][path]["value"]
    if cls == "D":
        new = v[:-1] + chr(ord(v[-1]) ^ 1)
    elif cls == "C":
        new = h(flip_lsb(float.fromhex(v)))
    else:
        new = v ^ 1
    other = mutate(base, path, new)
    assert base["fields"][path]["cls"] == cls and new != v                     # 전제
    rep = N.first_pass(base, other)
    assert rep["verdict"] == "FAIL" and rep["diffs"] == [path] and rep["undecidable"] == 0
    assert rep["fieldwise"] is False
    assert {e["verdict"] for e in rep["fields"]} <= {"FAIL", "REPORT"}         # 필드별 판정으로 넘어가지 않음
    assert all(e["resolution"] is None and e["delta"] is None for e in rep["fields"])
    if cls == "C":
        assert N.fieldwise(base, other)["verdict"] == "PASS"                   # 대조: 같은 쌍을 필드별로 보면 분해능 안


def test_nfr4_cmp_first_pass_time_fields_only_pass():
    other = mutate(record(), "perf/wall_s", h(99.0))
    rep = N.first_pass(record(), other)
    assert (rep["verdict"], rep["undecidable"], rep["diffs"]) == ("PASS", 0, [])
    (t,) = [e for e in rep["fields"] if e["path"] == "perf/wall_s"]
    assert t["verdict"] == "REPORT"


def test_nfr4_cmp_first_pass_missing_field_fails():
    other = copy.deepcopy(record())
    del other["fields"]["eval/2/failure/margin"]
    rep = N.first_pass(record(), other)
    assert rep["verdict"] == "FAIL" and rep["diffs"] == ["eval/2/failure/margin"]


@pytest.mark.parametrize("what", ["env_fp", "code_fp"])
def test_nfr4_cmp_first_pass_rejects_different_env_or_code(what):
    """거부: 1차 검사는 같은 환경(env_fp)·같은 코드(code_fp) 두 실행만 -- 다르면 ValueError."""
    other = copy.deepcopy(record())
    if what == "env_fp":
        other["env_fp"] = [["stage_a", "E2"], ["runs", "E2"]]
    else:
        other["code_fp"] = "K2"
    with pytest.raises(ValueError):
        N.first_pass(record(), other)


# ---------------------------------------------------------------- N-T25 필드별

def _verdict(rep, path):
    (e,) = [x for x in rep["fields"] if x["path"] == path]
    return e


def test_nfr4_cmp_fieldwise_discrete_mismatch_fails():
    rep = N.fieldwise(record(), mutate(record(), "stage_a/status", "stopped"))
    assert rep["verdict"] == "FAIL" and _verdict(rep, "stage_a/status")["verdict"] == "FAIL"


@pytest.mark.parametrize("new, want", [(2.5 + 0.9, "PASS"), (2.5 + 1.0, "PASS"), (2.5 + 1.5, "FAIL")])
def test_nfr4_cmp_fieldwise_continuous_within_resolution(new, want):
    """C: ConstraintRow.c 분해능 1 -- |Δ| 0.9·1.0 PASS, 1.5 FAIL(손)."""
    path = "eval/1/constraints/w_min:M1/c"
    rep = N.fieldwise(record(), mutate(record(), path, h(new)))
    e = _verdict(rep, path)
    assert e["verdict"] == want and e["resolution"] == 1.0 and math.isclose(e["delta"], new - 2.5, rel_tol=1e-15)
    assert rep["verdict"] == want


def test_nfr4_cmp_fieldwise_same_zone_discrete_change_skips_continuous():
    """같은 구역(eval:1)의 D 가 다르면 그 구역 C 는 비교하지 않는다(NOT_COMPARED) -- D 불일치로 이미 FAIL. 다른 구역 C 는 그대로 비교."""
    other = mutate(record(), "eval/1/status", "failed")
    other["fields"]["eval/1/constraints/w_min:M1/c"]["value"] = h(9.0)          # 분해능 밖 차
    other["fields"]["layer0/t"]["value"] = h(0.75 + 0.5)                         # 다른 구역, 분해능 안
    rep = N.fieldwise(record(), other)
    assert rep["verdict"] == "FAIL"
    assert _verdict(rep, "eval/1/status")["verdict"] == "FAIL"
    assert _verdict(rep, "eval/1/constraints/w_min:M1/c")["verdict"] == "NOT_COMPARED"
    assert _verdict(rep, "eval/1/objectives/power_w")["verdict"] == "NOT_COMPARED"
    assert _verdict(rep, "layer0/t")["verdict"] == "PASS"


def test_nfr4_cmp_fieldwise_path_counts_report_only():
    """K(경로 계수)·T(시간)는 판정 없이 보고만 -- 둘만 달라도 PASS."""
    other = mutate(record(), "layer0/iterations", 9)
    other["fields"]["perf/kernel_calls"]["value"] = 77
    other["fields"]["perf/wall_s"]["value"] = h(5.0)
    rep = N.fieldwise(record(), other)
    assert rep["verdict"] == "PASS" and rep["undecidable"] == 0
    for p in ("layer0/iterations", "perf/kernel_calls", "perf/wall_s"):
        assert _verdict(rep, p)["verdict"] == "REPORT"


def test_nfr4_cmp_compare_dispatch():
    assert N.compare(record(), record(), "same_env")["kind"] == "same_env"
    assert N.compare(record(), record(), "other_env")["kind"] == "other_env"
    assert N.compare(record(), record(), "refactor")["kind"] == "refactor"
    with pytest.raises(ValueError):
        N.compare(record(), record(), "bitwise")


# ---------------------------------------------------------------- N-T26 분해능 식 (40 §2.4.13 (4), 손 숫자)

CTX = record()["context"]


@pytest.mark.parametrize("kind, args, want", [
    ("c", {}, 1.0),
    ("t", {}, 1.0),
    ("margin", {}, 1.0),
    ("W", {}, 5e-9),                                             # grid_m
    ("area", {}, 5e-9 * 4.2e-7),                                 # grid_m·w_min_m = 2.1e-15
    ("power", {"tol_i": TOL_I}, 1.8 * 2e-9 + 0.9 * 3e-9),        # Σ|V_k|·tol_I,k = 6.3e-9 (gnd 0 V)
    ("kcl", {"tol_i": TOL_I}, 2e-9 + 3e-9 + 5e-9),               # Σ tol_I,k = 1e-8
    ("node_v", {"node": "n1"}, 1e-3),                            # 노드 n1 에 닿는 MOS(M1 2 mV, M2 1 mV) dc_tol_v 최솟값
    ("metric", {"resolution": 0.01}, 0.01),
    ("theta", {"h": -0.002}, 0.002),
    ("max_decl_prop", {"declared": "W", "propagated": 3e-9}, 5e-9),
    ("max_decl_prop", {"declared": "area", "propagated": 7e-15}, 7e-15),
])
def test_nfr4_cmp_resolution_formulas(kind, args, want):
    got, src = N.resolution({"res": dict(kind=kind, **args)}, CTX)
    assert math.isclose(got, want, rel_tol=1e-12), (kind, got, want)
    assert src


def test_nfr4_cmp_resolution_unknown_kind_rejected():
    with pytest.raises(ValueError):
        N.resolution({"res": {"kind": "made_up"}}, CTX)


# ---------------------------------------------------------------- N-T27 판정 불능 분류

UNDEC_FIELDS = {
    "eval/1/metrics/gain_ss_db": ("metric", {"resolution": None}),          # MetricResult.resolution None
    "eval/1/theta/current:M2": ("theta", {"h": None}),                       # θ 칸 스냅샷 없음(FD 스텝 없음)
    "eval/1/node_v/n2": ("node_v", {"node": "n2"}),                          # MOS 없는 노드
    "layer0/centre_u": ("unsourced", {}),                                    # 출처 없는 칸
    "s0/device/M1/start.row/w_m": ("max_decl_prop", {"declared": "W", "propagated": None}),   # max(선언, 전파)의 전파 없음
}


def test_nfr4_cmp_undecidable_classification():
    base, other = record(), record()
    for p, (kind, args) in UNDEC_FIELDS.items():
        base["fields"][p] = F("C", h(1.0), "u:" + p, kind, **args)
        other["fields"][p] = F("C", h(1.0 + 1e-6), "u:" + p, kind, **args)
    base["fields"]["eval/1/theta/current:M1"] = F("C", h(1.0), "u:ok", "theta", h=0.01)      # 대조: 자료 있으면 판정
    other["fields"]["eval/1/theta/current:M1"] = F("C", h(1.0 + 1e-6), "u:ok", "theta", h=0.01)
    rep = N.fieldwise(base, other)
    for p in UNDEC_FIELDS:
        assert _verdict(rep, p)["verdict"] == "UNDECIDABLE", p
    assert _verdict(rep, "eval/1/theta/current:M1")["verdict"] == "PASS"
    assert rep["undecidable"] == 5                                           # 손으로 센 수
    assert rep["verdict"] == "UNDECIDABLE"
    assert list(rep)[0] == "undecidable"                                     # 보고 맨 위


def test_nfr4_cmp_fingerprint_continuous_field():
    """지문 칸(연속값을 담은 값의 fp): 같으면 PASS, 다르면 |Δ| 를 잴 수 없어 판정 불능(분해능 자료가 있어도)."""
    base, other = record(), record()
    base["fields"]["s0/graph/start/area_est_m2"] = F("C", "fpA", "s0c", "area", fp=True)
    other["fields"]["s0/graph/start/area_est_m2"] = F("C", "fpA", "s0c", "area", fp=True)
    assert _verdict(N.fieldwise(base, other), "s0/graph/start/area_est_m2")["verdict"] == "PASS"
    other["fields"]["s0/graph/start/area_est_m2"]["value"] = "fpB"
    assert _verdict(N.fieldwise(base, other), "s0/graph/start/area_est_m2")["verdict"] == "UNDECIDABLE"


# ---------------------------------------------------------------- cross_env: 다른 환경의 타당성 (설계 40 §2.4.13 (2) 개정)

def with_front(rec, env, n_points=1, status="sealed", item_status="pass", c=2.5, oracle=None):
    """record() 에 front 점 n_points 개와 다른 환경 지문 env 를 붙인 기록(손). 점마다 평가 보고서 status·항목 status·제약값 c."""
    out = copy.deepcopy(rec)
    out["env_fp"] = [["stage_a", env], ["runs", env]]
    for i in range(n_points):
        b = "result/front[%d]/result/" % i
        out["fields"][b + "evaluation/report/status"] = F("D", status, "front")
        out["fields"][b + "evaluation/report/items[0]/status"] = F("D", item_status, "front")
        out["fields"][b + "constraints/w_min:M1/c"] = F("C", h(c), "front", "c")
    if oracle is not None:
        out["oracle"] = oracle
    return out


def test_nfr4_cross_env_valid_fronts_pass_even_if_fronts_differ():
    """각 환경의 front 점이 타당하면 PASS -- 두 환경의 front 개수·내용이 달라도 요구하지 않는다(보고만)."""
    a, b = with_front(record(), "E1", 2), with_front(record(), "E2", 1, c=7.0)
    rep = N.compare(a, b, "cross_env")
    assert rep["verdict"] == "PASS" and rep["kind"] == "cross_env", rep
    assert rep["summary"] == {"base": {"front_points": 2, "oracle_checked": False}, "other": {"front_points": 1, "oracle_checked": False}}
    assert rep["front_presence_differs"] is False and rep["vacuous"] is False
    assert rep["oracle_not_run"] == ["base", "other"]


def test_nfr4_cross_env_front_presence_difference_is_reported_not_failed():
    """한 환경만 front 를 찾은 경우(실측 common_gate_amplifier): FAIL 이 아니라 front_presence_differs 보고."""
    rep = N.compare(with_front(record(), "E1", 1), with_front(record(), "E2", 0), "cross_env")
    assert rep["verdict"] == "PASS" and rep["front_presence_differs"] is True and rep["vacuous"] is False


@pytest.mark.parametrize("kw, note", [
    (dict(status="failed"), "report_status:failed"),
    (dict(item_status="fail"), "item_not_pass:"),
    (dict(c=-1e-3), "constraint_negative:"),
])
def test_nfr4_cross_env_invalid_front_point_fails(kw, note):
    """front 점이 엔진 타당성(sealed·항목 pass·제약 c>=0)을 어기면 어느 환경의 것이든 FAIL (손: 어긴 곳을 note 로)."""
    for bad_side in ("base", "other"):
        good, bad = with_front(record(), "E1", 1), with_front(record(), "E2", 1, **kw)
        a, b = (bad, good) if bad_side == "base" else (good, bad)
        rep = N.compare(a, b, "cross_env")
        assert rep["verdict"] == "FAIL", (bad_side, kw)
        fails = [e for e in rep["fields"] if e["verdict"] == "FAIL"]
        assert len(fails) == 1 and fails[0]["path"].startswith(bad_side + ":") and fails[0]["note"].startswith(note), fails


def test_nfr4_cross_env_both_empty_is_vacuous_pass():
    """두 환경 모두 front 가 없으면 아무것도 검증하지 못했다: PASS 이되 vacuous."""
    rep = N.compare(with_front(record(), "E1", 0), with_front(record(), "E2", 0), "cross_env")
    assert rep["verdict"] == "PASS" and rep["vacuous"] is True and rep["oracle_not_run"] == []


def test_nfr4_cross_env_oracle_verdicts():
    """기록에 oracle 판정이 있으면 모두 pass 여야 한다. 하나라도 아니면 FAIL, 없으면 oracle_not_run 보고."""
    ok = [{"point": 0, "status": "pass"}]
    rep = N.compare(with_front(record(), "E1", 1, oracle=ok), with_front(record(), "E2", 1, oracle=ok), "cross_env")
    assert rep["verdict"] == "PASS" and rep["oracle_not_run"] == []
    bad = [{"point": 0, "status": "fail"}]
    rep = N.compare(with_front(record(), "E1", 1, oracle=ok), with_front(record(), "E2", 1, oracle=bad), "cross_env")
    assert rep["verdict"] == "FAIL"
    assert [e["path"] for e in rep["fields"] if e["verdict"] == "FAIL"] == ["other:oracle[point 0]"]


def test_nfr4_cross_env_same_env_rejected_and_preconditions_undecidable():
    """같은 환경(env_fp 같음)은 same_env 로 비교한다(ValueError). 전제 위반(예: E_B 미선언)은 판정 불능."""
    with pytest.raises(ValueError):
        N.compare(with_front(record(), "E1", 1), with_front(record(), "E1", 1), "cross_env")
    a, b = with_front(record(), "E1", 1), with_front(record(), "E2", 1)
    b["eval_budget_source"] = "derived_once:floor(B/median_t_eval)@n_evals=7"
    assert N.compare(a, b, "cross_env")["verdict"] == "UNDECIDABLE"


# ---------------------------------------------------------------- N-T28 전제 (판정 불능)

def _pre_cases():
    out = {}
    r = record()
    r["eval_budget_source"] = "derived_once:floor(B/median_t_eval)@n_evals=7"
    out["eb_not_declared"] = r
    r = record()
    r["stops_wall_budget"] = 1
    out["stops_wall_budget"] = r
    for name, path, val in (("layer0_stop", "layer0/stop", "start_empty_window+probe_wall_budget"),
                            ("halton_reason", "layer0/probe_reason", "probe_wall_budget"),
                            ("eps_stop", "sweep/solves/EP:s1/stop", "wall_budget"),
                            ("eps_aborts", "sweep/solves/EP:s1/aborts[0]", "wall_budget"),
                            ("failed_eps", "sweep/failed_eps[0]/stop", "wall_budget"),
                            ("lb_stops", "notes/l_search/stops[0]/stop", "wall_budget")):
        r = record()
        r["stop_values"] = r["stop_values"] + [[path, val]]
        out["wall_" + name] = r
    r = record()
    r["env_fp"] = [["stage_a", "E1"], ["runs", "E9"]]
    out["env_fp_differs_within_run"] = r
    r = record()
    r["env_fp"] = [["stage_a", "E1"]]
    out["searched_without_runs_line"] = r
    return out


@pytest.mark.parametrize("name", sorted(_pre_cases()))
def test_first_pass_preconditions(name):
    """N-T28: 전제 위반 기록 -> 1차 검사·필드별 비교 모두 판정 불능(PASS·FAIL 아님), 판정 불능 수 ≥ 1, 위반 사유가 보고에 남는다.
    비교 상대(기준)는 전제를 지킨 같은 기록이라 칸 값은 같다 -- 판정 불능의 원인은 전제뿐이다."""
    bad = _pre_cases()[name]
    for rep in (N.first_pass(record(), bad), N.first_pass(bad, record()), N.fieldwise(record(), bad)):
        assert rep["verdict"] == "UNDECIDABLE", (name, rep["verdict"])
        assert rep["undecidable"] >= 1
        assert rep["preconditions"]["base"] or rep["preconditions"]["other"]


def test_first_pass_preconditions_unsearched_run_single_report_holds():
    """N-T28: 탐색 없는 실행(예: ngcc_3stage_ff -- 단계 A 보고서 하나)은 (다)가 그 하나로 성립하고, E_B·벽시계 칸이 없어도 전제 위반이 아니다."""
    r = record()
    r.update(searched=False, env_fp=[["stage_a", "E1"]], eval_budget_source=None, stops_wall_budget=None, stop_values=[])
    assert N.preconditions(r) == []
    rep = N.first_pass(r, copy.deepcopy(r))
    assert (rep["verdict"], rep["undecidable"]) == ("PASS", 0)


def test_nfr4_cmp_cli_writes_report(tmp_path):
    a, b, out = tmp_path / "a.json", tmp_path / "b.json", tmp_path / "rep.json"
    a.write_text(json.dumps(record()), encoding="utf-8")
    b.write_text(json.dumps(mutate(record(), "perf/wall_s", h(2.0))), encoding="utf-8")
    assert N.main([str(a), str(b), "same_env", str(out)]) == 0
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["verdict"] == "PASS" and rep["undecidable"] == 0
