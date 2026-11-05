"""`run_sensitivity_gate` -- 설계 40 §3.8-2(감도 게이트: 분해 metric 이 **읽지 않는** 소자를 건드리는 θ 방향으로 섭동, 최종 해에서 돈다),
체크리스트 D-SG, metrics CONTRACT 10.7.

이 test 는 섭동 점 평가(fd_jacobian)를 손 결과로 바꿔 끼워 '어느 방향을 섭동하는가'와 '판정에 무엇을 넘기는가'만 본다.
oracle (a) 구성: 읽는 소자 {M1, M2}(블록 잔차 보고 read_devices). θ 변수와 그 영향 소자(손으로 정함):
  L:M1 -> {M1}(읽음, 건너뜀), current:I1 -> KCL 원뿔에서 원천 I1 을 항으로 갖는 MOS {M1, M3}(M1 읽음 -> 건너뜀),
  current:I2 -> {M3}(안 읽음 -> 섭동), ln_idu:M9 -> {M9}(섭동), y:vcm -> 모든 MOS(건너뜀).
  섭동 결과: current:I2 = 분해 그대로·MNA 0.4 dB 이동 -> 오류, ln_idu:M9 = 둘 다 그대로 -> 정상.
"""
from __future__ import annotations

import sys
import types

import pytest

from gmid_engine.metrics import REPORT_BLOCK_RESIDUAL, MetricBundle
from gmid_engine.sizing import METRICS_KEY, THETA_CURRENT, THETA_Y
from gmid_engine.search.gate_run import run_sensitivity_gate

GR = sys.modules["gmid_engine.search.gate_run"]


def _snapshot(dec, full, res=1e-13, read=("M1", "M2")):
    report = (("view", "t"), ("gain_residual_db", None if dec is None or full is None else full - dec), ("full_gain_db", full),
              ("decomposed_gain_db", dec),
              ("rout_residual_ohm", None), ("solve_residual", res), ("read_devices", read), ("block_gain", ()), ("ff_contrib", ()),
              ("undefined", ()))
    bundle = MetricBundle((), reports=((REPORT_BLOCK_RESIDUAL, report),))

    def value(kind, key, field):
        assert (kind, key, field) == ("graph", METRICS_KEY, "metrics_aux")
        return bundle

    return types.SimpleNamespace(value=value, column=lambda kind, field: tuple((m, None) for m in ("M1", "M2", "M3", "M9")))


def _result(dec, full):
    return types.SimpleNamespace(evaluation=types.SimpleNamespace(snapshot=_snapshot(dec, full)), theta=THETA,
                                 key=types.SimpleNamespace(cells=("c",)))


VARS = tuple(types.SimpleNamespace(component=c, log=lg, lo=0.0, hi=10.0) for c, lg in (
    (("L", "M1"), False), ((THETA_CURRENT, "I1"), True), ((THETA_CURRENT, "I2"), True), (("ln_idu", "M9"), False),
    ((THETA_Y, "vcm"), False)))
THETA = {("L", "M1"): 1e-6, (THETA_CURRENT, "I1"): 1e-5, (THETA_CURRENT, "I2"): 2e-5, ("ln_idu", "M9"): -3.0, (THETA_Y, "vcm"): 0.9}
TERM = lambda src: types.SimpleNamespace(source=src)  # noqa: E731
_SCHEMA = types.SimpleNamespace(current_cone=(("M1", (TERM("I1"),)), ("M3", (TERM("I1"), TERM("I2"))), ("M2", (TERM("I0"),))))
# [U17 ①-b] θ 스키마는 커널 컨텍스트 칸이 아니라 S0 수준 필드 `graph/kernel: theta_schema`(설계 40 v1.9.1 §2.4.7·§2.4.8 D8) -- 손 컨텍스트의 `dc.base` 가 그 필드를 돌려준다.
_BASE = types.SimpleNamespace(value=lambda kind, key, field: {("graph", "kernel", "theta_schema"): _SCHEMA}[(kind, key, field)])
SCTX = types.SimpleNamespace(domain=types.SimpleNamespace(variables=VARS), dc=types.SimpleNamespace(base=_BASE),
                             eval_budget=None, eval_budget_source=None)   # [XRUN-F1 card C] e_total 이 읽는 칸 -- None 이면 ceiling=None


def test_perturbs_only_unread_directions_and_flags_error(monkeypatch):
    seen = {}

    def fake(sctx, variables, x, base, cells, to_theta, origin, skip, **kw):  # [XRUN-F1 card C] 게이트가 ceiling 키워드를 넘긴다
        seen["skip"] = set(skip)
        seen["x"] = list(x)
        out = []
        for i, v in enumerate(variables):
            if i in skip:
                out.append((base, 0.0))
            elif v.component == (THETA_CURRENT, "I2"):
                out.append((_result(60.0, 60.4), 0.01))
            else:
                out.append((_result(60.0, 60.0), 0.01))
        return out

    monkeypatch.setattr(GR, "fd_jacobian", fake)
    got = run_sensitivity_gate(SCTX, _result(60.0, 60.0))
    assert seen["skip"] == {0, 1, 4}                        # L:M1·current:I1(M1 포함)·y 는 읽는 소자를 건드린다
    assert seen["x"][1] == pytest.approx(__import__("math").log(1e-5))   # log 변수는 ln 좌표
    assert got.ok is False and got.errors == ("current:I2",)
    assert [c[0] for c in got.checks] == ["current:I2", "ln_idu:M9"]


def test_no_report_no_gate():
    """[UB-1 E-01 뜻 교체, fail-open -> fail-closed] 보고가 없으면 None(= 통과로 읽힘)이 아니라 gate_empty/no_block_report 판정."""
    base = types.SimpleNamespace(evaluation=types.SimpleNamespace(snapshot=types.SimpleNamespace(
        value=lambda *a: (_ for _ in ()).throw(KeyError("metrics_aux")))))
    for b in (base, types.SimpleNamespace(evaluation=None)):
        got = run_sensitivity_gate(SCTX, b)
        assert got is not None
        assert got.ok is False and got.verdict == "gate_empty" and got.reason == "no_block_report"


def test_all_directions_read_no_gate(monkeypatch):
    """[UB-1 E-01 뜻 교체] 모든 변수가 읽는 소자를 건드려 건너뛰면 gate_empty/no_unread_direction(평가 0)."""
    monkeypatch.setattr(GR, "fd_jacobian", lambda *a, **k: pytest.fail("평가하면 안 된다"))
    base = _result(60.0, 60.0)
    base.evaluation.snapshot = _snapshot(60.0, 60.0, read=("M1", "M2", "M3", "M9"))
    got = run_sensitivity_gate(SCTX, base)
    assert got is not None
    assert got.ok is False and got.verdict == "gate_empty" and got.reason == "no_unread_direction"


def test_ub1_base_db_undefined_is_undeterminable_without_perturbation(monkeypatch):
    """T-6a (a): 분해 dB 또는 전회로 dB 가 None 이면 섭동 평가 0, undeterminable/base_undefined."""
    monkeypatch.setattr(GR, "fd_jacobian", lambda *a, **k: pytest.fail("섭동을 평가하면 안 된다"))
    for dec, full in ((None, 60.0), (60.0, None)):
        got = run_sensitivity_gate(SCTX, _result(dec, full))
        assert got is not None
        assert got.ok is False and got.verdict == "undeterminable" and got.reason == "base_undefined"


def test_ub1_unmeasured_perturbations_are_rows_not_skips(monkeypatch):
    """T-6a (a): skip 아닌 변수의 평가가 `res is base`·보고 없음·평가 없음이면 (이름, None, None, None) 행 -> unmeasured 에 든다.
    손 입력: 섭동 대상 current:I2 와 ln_idu:M9 (skip = {0, 1, 4})."""
    no_report = types.SimpleNamespace(evaluation=types.SimpleNamespace(snapshot=types.SimpleNamespace(
        value=lambda *a: (_ for _ in ()).throw(KeyError("metrics_aux")))), theta=THETA, key=types.SimpleNamespace(cells=("c",)))
    no_eval = types.SimpleNamespace(evaluation=None, theta=THETA, key=types.SimpleNamespace(cells=("c",)))

    def make(second):
        def fake(sctx, variables, x, base, cells, to_theta, origin, skip, ceiling=None):
            out = []
            for i, v in enumerate(variables):
                if i in skip:
                    out.append((base, 0.0))
                elif v.component == (THETA_CURRENT, "I2"):
                    out.append((base, 0.01))                      # res is base
                else:
                    out.append((second(base), 0.01))
            return out
        return fake

    for second, unmeasured in ((lambda b: _result(60.0, 60.0), ("current:I2",)),
                               (lambda b: no_report, ("current:I2", "ln_idu:M9")),
                               (lambda b: no_eval, ("current:I2", "ln_idu:M9")),
                               (lambda b: None, ("current:I2", "ln_idu:M9"))):                 # 평가 실패 res is None
        monkeypatch.setattr(GR, "fd_jacobian", make(second))
        got = run_sensitivity_gate(SCTX, _result(60.0, 60.0))
        assert got.ok is False and got.verdict == "undeterminable" and got.reason == "perturbation_unmeasured"
        assert got.unmeasured == unmeasured and got.errors == ()
        assert [c[0] for c in got.checks if c[4] is None] == list(unmeasured)


# =====================================================================================================================
# [XRUN-F1 card A] interface card xrunf1a C2 감도 게이트 행: variables = sctx.domain.variables(조정 없음), 시작 θ = dict(base.theta),
# FD 에 들어가는 시작 좌표 = x0 그대로(자르지 않음, X-14), 좌표 -> θ = ThetaCoords.to_theta 그대로. 관찰 지점(J-3) = 모듈 속성
# `gate_run.fd_jacobian`(위 test 와 같은 교체 선례).
# 손 입력: 위 VARS 와 같은 성분·log 여부, bounds 만 바꿈 -- current:I2 는 ln 좌표가 bounds 안([-20, -5] ∋ ln 2e-5 ≈ −10.8),
# current:I1 은 bounds 밖([0, 10] ∌ ln 1e-5 ≈ −11.5). θ 는 위 THETA(1e-5·2e-5 는 math.exp(math.log(θ)) != θ -- test 가 먼저 단언).
# oracle: (Py) x 기대값 = math.log(θ)(log 변수)·θ(선형) -- 이 파일이 math 로 만든다. (비교) to_theta(x) 와 기준 θ 의 비트(float.hex) 비교.
# =====================================================================================================================

VARS_RT = tuple(types.SimpleNamespace(component=c, log=lg, lo=lo, hi=hi) for c, lg, lo, hi in (
    (("L", "M1"), False, 0.0, 10.0), ((THETA_CURRENT, "I1"), True, 0.0, 10.0), ((THETA_CURRENT, "I2"), True, -20.0, -5.0),
    (("ln_idu", "M9"), False, -10.0, 0.0), ((THETA_Y, "vcm"), False, 0.0, 1.0)))
SCTX_RT = types.SimpleNamespace(domain=types.SimpleNamespace(variables=VARS_RT), dc=types.SimpleNamespace(base=_BASE),
                                eval_budget=None, eval_budget_source=None)   # [XRUN-F1 card C] e_total 이 읽는 칸 -- None 이면 ceiling=None


def _record_gate_fd(monkeypatch, store):
    """gate_run.fd_jacobian 을 기록하는 손 결과 함수로 바꾼다(위 test 의 fake 와 같은 결과 모양)."""
    def fake(sctx, variables, x, base, cells, to_theta, origin, skip, **kw):  # [XRUN-F1 card C] 게이트가 ceiling 키워드를 넘긴다
        store.append((tuple(variables), list(x), to_theta))
        return [(base, 0.0) if i in skip else (_result(60.0, 60.0), 0.01) for i in range(len(variables))]
    monkeypatch.setattr(GR, "fd_jacobian", fake)


def test_gate_start_coordinates_unclipped_and_theta_bits_preserved(monkeypatch):
    """A-T6: x[i] == math.log(θᵢ)(log 변수, bounds 밖 성분 포함 -- 자르지 않음) 또는 θᵢ, to_theta(x) 가 θ 와 성분마다 비트 동일."""
    import math
    log_comps = [v.component for v in VARS_RT if v.log]
    assert all(math.exp(math.log(THETA[c])) != THETA[c] for c in log_comps)          # 전제: 왕복이 원값을 잃는 θ
    outside = [v.component for v in VARS_RT if v.log and not (v.lo <= math.log(THETA[v.component]) <= v.hi)]
    assert outside == [(THETA_CURRENT, "I1")]                                           # 전제: bounds 밖 log 성분 하나
    seen = []
    _record_gate_fd(monkeypatch, seen)
    run_sensitivity_gate(SCTX_RT, _result(60.0, 60.0))
    assert len(seen) == 1
    variables, x, to_theta = seen[0]
    assert [v.component for v in variables] == [v.component for v in VARS_RT]
    want_x = [math.log(THETA[v.component]) if v.log else THETA[v.component] for v in VARS_RT]   # (Py)
    assert [float(a).hex() for a in x] == [float(b).hex() for b in want_x]
    got = to_theta(x)
    assert {k: float(v).hex() for k, v in got.items()} == {k: float(v).hex() for k, v in THETA.items()}


def test_theta_coords_used_by_gate(monkeypatch):
    """A-T8(감도 게이트 경로): ThetaCoords.start 를 클래스 수준에서 감싸(원래 것을 부름) 한 번 이상 불리고, FD 에 들어간 변환의 출력이
    감싼 객체의 to_theta 출력과 같다(시작 좌표·좌표 하나를 옮긴 x 둘 다). oracle (비교)."""
    from gmid_engine.search import ThetaCoords
    made = []
    orig = ThetaCoords.start

    def start(cls, variables, theta):
        c = orig(variables, theta)
        made.append(c)
        return c
    monkeypatch.setattr(ThetaCoords, "start", classmethod(start))
    seen = []
    _record_gate_fd(monkeypatch, seen)
    run_sensitivity_gate(SCTX_RT, _result(60.0, 60.0))
    assert len(made) >= 1 and len(seen) == 1
    _, x, to_theta = seen[0]
    coords = made[-1]
    moved = list(x)
    moved[2] = moved[2] + 0.25
    for xx in (x, moved):
        a, b = to_theta(xx), coords.to_theta(xx)
        assert {k: float(v).hex() for k, v in a.items()} == {k: float(v).hex() for k, v in b.items()}


# =====================================================================================================================
# [XRUN-F1 card C] interface card xrunf1c C7 (C-T10) -- 묶음 `ceiling` = e_total(sctx), FdBudgetShortfall 을 잡지 않음,
# 게이트 시작 뒤 search_ceiling·search_stop 호출 0. 관찰 지점 = 모듈 속성 `gate_run.fd_jacobian`(위 test 와 같은 교체 선례).
# oracle: (손) 가짜 sctx = interface 1절의 칸만(domain.variables 5개 -> R = 10, 선언 E_B = 40 -> E_total = 40 + 10 = 50, 손 계산).
# =====================================================================================================================

import importlib  # noqa: E402

_FD_MOD = importlib.import_module("gmid_engine.search.fd_jacobian")
E_B_GATE = 40
E_TOTAL_GATE = E_B_GATE + 2 * len(VARS)          # 40 + 2 × 5 = 50 (손)
SCTX_C = types.SimpleNamespace(domain=types.SimpleNamespace(variables=VARS), dc=types.SimpleNamespace(base=_BASE),
                               eval_budget=E_B_GATE, eval_budget_source="declared", eval_times=[],
                               counters={"kernel_calls": 7}, deadline=None)


def _count_calls(monkeypatch, names):
    """gmid_engine.search 의 이름(패키지 속성, 같은 이름의 모듈 속성, gate_run 속성)을 호출 수를 세는 감싸개로 바꾼다. -> 호출 기록 list."""
    import gmid_engine.search as pkg
    calls = []
    for name in names:
        targets = [pkg, GR]
        sub = sys.modules.get("gmid_engine.search." + name)
        if sub is not None:
            targets.append(sub)
        for mod in targets:
            orig = getattr(mod, name, None)
            if not callable(orig):
                continue

            def wrapper(*a, _orig=orig, _name=name, **k):
                calls.append(_name)
                return _orig(*a, **k)
            monkeypatch.setattr(mod, name, wrapper)
    return calls


def test_gate_entry_budget_ceiling_is_e_total(monkeypatch):
    seen = []

    def fake(sctx, variables, x, base, cells, to_theta, origin, skip, **kw):
        seen.append(dict(kw))
        return [(base, 0.0) if i in skip else (_result(60.0, 60.0), 0.01) for i in range(len(variables))]

    monkeypatch.setattr(GR, "fd_jacobian", fake)
    run_sensitivity_gate(SCTX_C, _result(60.0, 60.0))
    assert len(seen) == 1 and seen[0] == {"ceiling": E_TOTAL_GATE}               # 인자 관찰: ceiling = E_B + 2 n_θ = 50


def test_gate_entry_budget_shortfall_propagates(monkeypatch):
    def fake(sctx, variables, x, base, cells, to_theta, origin, skip, **kw):
        raise _FD_MOD.FdBudgetShortfall(10, 9)                                 # 주입 -- 게이트는 잡지 않는다(C7)

    monkeypatch.setattr(GR, "fd_jacobian", fake)
    with pytest.raises(_FD_MOD.FdBudgetShortfall):
        run_sensitivity_gate(SCTX_C, _result(60.0, 60.0))


def test_gate_entry_budget_no_search_ceiling_or_stop_calls(monkeypatch):
    def fake(sctx, variables, x, base, cells, to_theta, origin, skip, **kw):
        return [(base, 0.0) if i in skip else (_result(60.0, 60.0), 0.01) for i in range(len(variables))]

    monkeypatch.setattr(GR, "fd_jacobian", fake)
    calls = _count_calls(monkeypatch, ("search_ceiling", "search_stop"))
    got = run_sensitivity_gate(SCTX_C, _result(60.0, 60.0))
    assert got is not None                                                       # 게이트가 실제로 돌았다 (공허 방지)
    assert calls == []
