"""XRUN-F1 card C interface card C3 -- `gate_reserve(sctx) -> R`, `e_total(sctx) -> int | None` (C-T4). 규칙 H 꼴 파일 이름.

oracle: (손) 정의(interface 1절): R = 2 × n_θ, 선언 E_total = E_B + R, 유도(전이 뒤) E_total = D, eval_budget None 이면 None.
n_θ 는 sctx.domain.variables 길이를 test 가 센다(피검 함수 호출이 아니라 입력 칸). 피검 식을 다시 쓰지 않는다 -- 숫자는 합성 입력에서 손으로 낸다.
"""
import importlib

from .conftest import build_case, circuit_c

H = importlib.import_module("gmid_engine.search._helpers_ceiling")


def test_gate_reserve_is_twice_the_variable_count(tmp_path, lut_sealed):
    s = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=40).sctx
    n = len(s.domain.variables)
    assert n >= 1
    assert H.gate_reserve(s) == 2 * n


def test_e_total_declared_is_e_b_plus_reserve(tmp_path, lut_sealed):
    s = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=40).sctx
    n = len(s.domain.variables)
    assert s.eval_budget_source == "declared"
    assert H.e_total(s) == 40 + 2 * n
    s.eval_budget = 7
    assert H.e_total(s) == 7 + 2 * n


def test_e_total_derived_is_d(tmp_path, lut_sealed):
    s = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=40).sctx
    n = len(s.domain.variables)
    s.eval_budget = 123                                                         # 유도 뒤 sctx.eval_budget = D
    s.eval_budget_source = "derived_once:floor(B/median_t_eval)@n_evals=%d" % (n + 1)
    assert H.e_total(s) == 123


def test_e_total_none_before_derivation(tmp_path, lut_sealed):
    s = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=None, budget_s=100.0).sctx
    assert s.eval_budget is None
    assert H.e_total(s) is None
    assert s.eval_budget is None                                                # 읽기만 한다
