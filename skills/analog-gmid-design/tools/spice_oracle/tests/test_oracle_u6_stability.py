"""U6 C10 최종 안정성 판정: 한계 사이클(사용자 결정 4), Nyquist 적응 세분화(설계 40 §4 C10 6), `.pz` P 와 신뢰 규칙
(사용자 결정 Q10 + README 절차 7·8), 조건부 안정 fixture(설계 40 §10.2 C10 행), 보상 내부 루프 회로의 P = 0(설계 40 §11 J 추가 범위,
J-B: '안정도 = 전체 pm_ss_deg + 개루프 RHP 극점 없음(P = 0)').

근거: 설계 40 §4·§10.2·§11, 계약 docs/03-analysis/oracle-c10-early-termination.contract.md(d56ba66 + 구현 메모), README "C10 PM
안정성 근거" 절차 2·5·7·8, 사용자 결정 4·Q10(_drafts/user_decisions.md 2026-10-08). 오라클 소스는 열지 않는다(공개 함수는 이름·서명·
docstring 만 보고 import).

기대값 출처(피검 함수로 만들지 않음):
  * oracle (a) 구성으로 답이 정해진 합성 입력: 창 최댓값 열, 합성 .stab 데이터 파일(정현파·지수), 해석식 전달함수 L(s).
  * oracle (b) 다른 방법: 해석식 L(s) 의 폐루프 특성다항식 근(numpy.roots)으로 센 Z(= N, P = 0) -- 위상 펼침과 다른 방법.
  * oracle (c) 손으로 쓴 독립 ngspice 넷리스트: .op·.ac(독립 N)·.pz(독립 P)·폐루프 .tran(이상 VCVS 단위 음되먹임).
"""
import importlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

import conftest
from conftest import NFET, make_lut, measure, run_oracle, run_spice, stem_of, zero_diffusion
from test_oracle_c10_stability import (SAT, THREE, _head, _ngspice, ac_loop_from_files, gain_crossings, independent_pz,
                                       notch_input, notch_ref, nyquist, rhp_count_in_sweep)


def _sim_mod():
    d = str(conftest.ORACLE_DIR)
    if d not in sys.path:
        sys.path.insert(0, d)
    return importlib.import_module("oracle_simulate")


# ====================================================================== 한계 사이클 조기 기준(순수 함수, oracle (a))
# 설계 40 §4 C10 2·8(사용자 결정 2026-10-09 '한계 사이클 = 감쇠하지 않음'): nd(j) := M_j(1−r) > floor'(바닥 위, 2 의 첫 항)
# 이고 g↓(M_{j−1}, M_j) 아님(앞 창보다 분해능 이상 줄지 않음), j >= 3 에서 nd(j−1)·nd(j) -> 한계 사이클. 각 기대값은 이 정의를
# 손으로 대입한 결과다.
LIMIT_CASES = [
    # 일정 진폭: 모든 쌍 |ΔM| = 0 <= 2·1e-3, M(1−r) = 0.999 > 0 -> flat(2)·flat(3) -> True (계약 구현 메모: constant 는 여기서 True)
    pytest.param([1.0, 1.0, 1.0, 1.0, 1.0], 0.0, 1e-3, True, id="constant"),
    # 계약 d56ba66 L52 의 지속 진동 fixture 열(상대 변화 ~5e-6 << reltol 1e-4): 결정 4 로 undetermined -> 한계 사이클
    pytest.param([1.094850, 1.094848, 1.094847, 1.094854, 1.094852, 1.094845], 1e-6, 1e-4, True, id="contract_sustained"),
    # 창 2 개뿐: j >= 3 이 없음 -> False
    pytest.param([1.0, 1.0], 0.0, 1e-3, False, id="j2"),
    # 바닥 아래 일정: M(1−r) = 0.999e-6 < floor' 1e-5 -> flat 아님 -> False(감쇠해 바닥에 붙은 안정 회로)
    pytest.param([1e-6, 1e-6, 1e-6, 1e-6], 1e-5, 1e-3, False, id="below_floor"),
    # 고Q 느린 감쇠(창당 5e-4 감소 <= (합)·1e-3 ≈ 2e-3): 분해능 안이라 flat -> True(설계 40 §4 C10 2 '고Q 안정 회로의 표시':
    # K 창 안에서 한계 사이클과 구별 불가 -> 보수적으로 unstable)
    pytest.param([1.0, 0.9995, 0.999, 0.9985], 0.0, 1e-3, True, id="high_q_slow_decay"),
    # 맥놀이 [1, 0.5, 1.2]: (1->0.5) g↓, (0.5->1.2) g↑ -> flat 없음 -> False
    pytest.param([1.0, 0.5, 1.2], 1e-3, 1e-3, False, id="beating"),
    # 분해능 초과 성장 [1, 1.2, 1.5]: 줄지 않음(g↓ 아님) 두 쌍 -> True (§4 C10 8: 감쇠하지 않음은 성장도 포함)
    pytest.param([1.0, 1.2, 1.5], 1e-3, 1e-3, True, id="growth"),
    # rb1e6형 출렁이는 지속 진동(사용자 결정 2026-10-09 이 명시한 열): (1.31->1.10) g↓, (1.10->1.14)·(1.14->1.18) 줄지 않음 -> j = 4 True
    pytest.param([1.31, 1.10, 1.14, 1.18, 1.10, 1.10], 1e-5, 1e-4, True, id="rb1e6_relaxation"),
    # 감쇠 뒤 한 번 다시 커짐 [1, 0.5, 0.6]: j = 3 에서 (1->0.5) g↓ -> False(창이 더 없음)
    pytest.param([1.0, 0.5, 0.6], 1e-3, 1e-3, False, id="decay_then_one_rise"),
    # 느린 감쇠지만 창마다 분해능 넘게 줄어듦(창당 2 %, r 1e-3): 모든 쌍 g↓ -> False(§4 C10 8 'slow decay 는 판정을 이어 간다')
    pytest.param([1.0, 0.98, 0.9604, 0.941192, 0.922368], 1e-6, 1e-3, False, id="slow_decay_beyond_resolution"),
    # 마지막 쌍만 줄지 않음: (5->1) g↓, (1->1.0005) 줄지 않음 -> j = 3 에서 nd(2) 거짓 -> False
    pytest.param([5.0, 1.0, 1.0005], 0.0, 1e-3, False, id="one_flat_pair"),
    # 같은 열에 창 4 추가: (1.0005->1.0) 분해능 안 감소 -> j = 4 에서 nd(3)·nd(4) -> True
    pytest.param([5.0, 1.0, 1.0005, 1.0], 0.0, 1e-3, True, id="two_flat_pairs_j4"),
    # 감쇠가 분해능 밖(창당 1/e): 모든 쌍 g↓ -> False(안정 감쇠는 절대 한계 사이클이 아님 -- 안정 판정 불변 조건)
    pytest.param([1.0, 0.3679, 0.1353, 0.0498, 0.0183, 0.0067], 1e-4, 1e-4, False, id="e_fold_decay"),
]


@pytest.mark.parametrize("m,floor2,reltol,expected", LIMIT_CASES)
def test_limit_cycle_early_predicate(m, floor2, reltol, expected):
    assert bool(_sim_mod().limit_cycle_early(list(m), floor2, reltol)) is expected


# early_window(M, fl, reltol) -> (j, 종류) 또는 None. 기대값(손 대입): growth 는 계약 1(b), limit_cycle 은 설계 40 §4 C10 2·8.
# §4 C10 8 이후 성장도 '감쇠하지 않음'이라 같은 j 에서 둘이 함께 성립할 수 있다 -- 그때 종류 이름은 설계가 정하지 않아 둘 다 허용.
EARLY_WINDOW_CASES = [
    pytest.param([1.0, 1.2, 1.5], 1e-3, 1e-3, 3, {"growth", "limit_cycle"}, id="growth_j3"),
    pytest.param([1.0, 1.0, 1.0, 1.0], 1e-3, 1e-3, 3, {"limit_cycle"}, id="limit_j3"),
    pytest.param([5.0, 1.0, 1.0005, 1.0], 1e-3, 1e-3, 4, {"limit_cycle"}, id="limit_j4"),
    # j = 3: (1->1)·(1->1.5) 둘 다 줄지 않음 -> 한계 사이클(성장 기준은 g↑(1,1) 거짓이라 j = 3 에서 불충족)
    pytest.param([1.0, 1.0, 1.5, 2.25], 1e-3, 1e-3, 3, {"limit_cycle"}, id="not_decaying_before_growth"),
    pytest.param([1.0, 0.5, 1.2], 1e-3, 1e-3, None, set(), id="beating_none"),
    pytest.param([1.31, 1.10, 1.14, 1.18, 1.10, 1.10], 1e-5, 1e-4, 4, {"limit_cycle"}, id="rb1e6_relaxation_j4"),
]


@pytest.mark.parametrize("m,fl,reltol,window,kinds", EARLY_WINDOW_CASES)
def test_early_window_kind(m, fl, reltol, window, kinds):
    got = _sim_mod().early_window(list(m), fl, reltol)
    assert (None if got is None else got[0]) == window, got
    assert (got is None) if window is None else (got[1] in kinds), got


# ====================================================================== 파일 판정(합성 .stab 데이터 파일, oracle (a))
W_S, K_WIN, T_END = 1e-6, 6, 1e-6           # 창 W, 창 수 K, 킥 끝 t_end(합성 계획 -- README 절차 4 의 필드 이름)


def _plan(floor_v, reltol=1e-3):
    tstop = T_END + K_WIN * W_S
    return {"kick_V": 0.0259, "td": T_END / 4, "tr": T_END / 4, "tf": T_END / 4, "pw": T_END / 4, "tmax": W_S / 400,
            "window_s": W_S, "windows": K_WIN, "windows_planned": K_WIN, "t_kick_end": T_END, "tstop": tstop,
            "f_lo_hz": 1 / W_S, "f_hi_hz": 1 / W_S, "f_crit_hz": 1 / W_S, "n_pp": 71, "reltol": reltol,
            "wall_cap_s": 1.0, "floor_V": floor_v, "sign": 1.0}


def _write_stab(path: Path, e_of_t, t_last=None, h_op=0.5):
    """wrdata(wr_singlescale, numdgt 8) 모양: 'time H' 두 열, 가수 9 자리. 첫 표본 = 동작점(킥 전), 킥 구간 안은 동작점."""
    t = np.linspace(0.0, T_END + K_WIN * W_S, 1 + 400 * (K_WIN + 1))   # 창당 400 표본, 창 경계가 표본에 놓임
    if t_last is not None:
        t = t[t <= t_last]
    h = np.where(t < T_END, h_op, h_op + e_of_t(t - T_END))
    path.write_text("\n".join(f"{a:.8e} {b:.8e}" for a, b in zip(t, h)) + "\n", encoding="utf-8")
    return path


# 정현파 주기 = W/10(창마다 봉우리 10 개, 표본 40 개/주기라 봉우리가 표본에 정확히 놓인다)
_SINE = lambda a: (lambda s: a * np.sin(2 * np.pi * s / (W_S / 10)))
FILE_CASES = [
    # 일정 진폭 지속 진동 -> 결정 4: unstable(limit_cycle), 창 3 조기 종결, 고Q 구별 불가 표시
    pytest.param(_SINE(0.1), None, 1e-4, ("unstable", 3, {"limit_cycle"}), id="sustained_sine"),
    # 창당 1/e 지수 증가 -> unstable 창 3(계약 1(b) growth 와 §4 C10 8 '감쇠하지 않음' 이 같은 창에서 성립 -- 종류 둘 다 허용)
    pytest.param(lambda s: 1e-3 * np.exp(s / W_S) * np.sin(2 * np.pi * s / (W_S / 10)), None, 1e-6,
                 ("unstable", 3, {"growth", "limit_cycle"}), id="growth"),
    # 진폭이 창마다 분해능 밖으로 출렁이는 지속 진동(rb1e6형, 사용자 결정 2026-10-09): 창 j 진폭 = 0.1·[1.31,1.10,1.14,1.18,1.10,1.10]
    pytest.param(lambda s: 0.1 * np.interp(np.minimum(np.floor(s / W_S), 5), np.arange(6), [1.31, 1.10, 1.14, 1.18, 1.10, 1.10])
                 * np.sin(2 * np.pi * s / (W_S / 10)), None, 1e-4, ("unstable", 4, {"limit_cycle"}), id="relaxation_rb1e6_shape"),
    # 창당 1/e 감쇠, 바닥 0.01 (M_K ~ e^-5·0.1 = 6.7e-4 <= 0.01) -> stable(조기 기준 불충족)
    pytest.param(lambda s: 0.1 * np.exp(-s / W_S) * np.cos(2 * np.pi * s / (W_S / 10)), None, 1e-2, ("stable", None, set()),
                 id="decay_to_floor"),
    # 같은 감쇠, 바닥 1e-6 -> 모든 연속 창 g↓, 바닥 못 닿음 -> decaying(연장 대상; §4 C10 8 'slow decay 는 판정을 이어 간다')
    pytest.param(lambda s: 0.1 * np.exp(-s / W_S) * np.cos(2 * np.pi * s / (W_S / 10)), None, 1e-6, ("decaying", None, set()),
                 id="decaying"),
    # 일정 진폭이지만 창 2 끝에서 파일이 끊김(ngspice 중간 사망) -> 조기 기준(j >= 3) 불가, tstop 미도달 -> failed
    pytest.param(_SINE(0.1), T_END + 2.5 * W_S, 1e-4, ("failed", None, set()), id="truncated"),
]


@pytest.mark.parametrize("e_of_t,t_last,floor_v,expected", FILE_CASES)
def test_transient_decision_synthetic_file(tmp_path, e_of_t, t_last, floor_v, expected):
    p = _write_stab(tmp_path / "x.stab.txt", e_of_t, t_last)
    dec = _sim_mod().transient_decision(str(p), _plan(floor_v))
    status, window, kinds = expected
    assert dec["status"] == status, dec
    es = dec.get("early_stop") or {}
    assert es.get("window") == window, es
    assert (es.get("kind") in kinds) if kinds else not es, es
    # 설계 40 §4 C10 2: 한계 사이클 판정에만 고Q 감쇠와 구별 못 함 표시가 붙는다
    assert (dec.get("limit_cycle_vs_slow_decay_unresolved") is not None) == (es.get("kind") == "limit_cycle"), dec


# ====================================================================== Nyquist 적응 세분화(해석식 L, oracle (a)·(b))
POLES_W = 2 * np.pi * np.array([1e3, 1e5, 1e6])


def _L3(f, k0, poles=POLES_W):
    s = 2j * np.pi * np.asarray(f, dtype=float)
    out = np.full(s.shape, k0, dtype=complex)
    for w in poles:
        out = out / (1 + s / w)
    return out


def _z_by_roots(k0, poles=POLES_W):
    """oracle (b): 폐루프 특성다항식 Π(1 + s/w_i) + k0 의 RHP 근 수(위상 펼침과 다른 방법). L 에 RHP 극이 없어(P = 0) N = Z."""
    poly = np.array([1.0])
    for w in poles:
        poly = np.polymul(poly, [1 / w, 1.0])
    poly = np.polyadd(poly, [k0])
    return int(sum(1 for r in np.roots(poly) if r.real > 0))


def _grid(f0, f1, ppd):
    n = int(round(math.log10(f1 / f0) * ppd))
    return f0 * 10.0 ** (np.arange(n + 1) / ppd)


def _sampler(k0, poles=POLES_W, calls=None):
    def fn(f_a, f_b, ppd, tag):
        f = np.unique(np.concatenate([[f_a], _grid(f_a, f_b, max(int(ppd), 1)), [f_b]]))
        f = f[(f >= f_a) & (f <= f_b)]
        if calls is not None:
            calls.append((f_a, f_b, ppd, tag))
        L = _L3(f, k0, poles)
        return f, L.real, L.imag
    return fn


@pytest.mark.parametrize("k0", [3e3, 1e3, 5.0])
def test_nyquist_count_dense_matches_roots(k0):
    """밀한 표본(100/decade)에서 nyquist_count 의 N = 특성다항식 근으로 센 Z(P = 0): k0 3e3 -> 2(불안정), 1e3·5 -> 0
    (세 극이 1e3·1e5·1e6 Hz 로 넓게 떨어져 임계 이득이 1e3 과 3e3 사이 -- 근 계산이 정한다)."""
    f = _grid(1.0, 1e9, 100)
    ny = _sim_mod().nyquist_count(f, _L3(f, k0))
    assert ny["encirclements_cw"] == _z_by_roots(k0), ny
    assert ny["max_step_deg"] < 90.0


@pytest.mark.parametrize("k0", [3e3, 1e3])
def test_nyquist_adaptive_refines_sparse_sweep(k0):
    """희박 표본(1/decade)만으로는 편각 간격 >= 90 deg 라 N = None(nyquist_count). 설계 40 §4 C10 6: 그 구간을 이분해 다시 잰
    표본(sample_fn = 같은 해석식)을 합치면 N = 근으로 센 Z. 합친 표본은 오름차순이고 원래 표본을 포함, 라운드 1..k_max."""
    sim = _sim_mod()
    f = _grid(1.0, 1e9, 1)
    L = _L3(f, k0)
    assert sim.nyquist_count(f, L)["encirclements_cw"] is None
    calls = []
    ny, f2, L2 = sim.nyquist_adaptive(f, L, sample_fn=_sampler(k0, calls=calls), k_max=10)
    assert ny["encirclements_cw"] == _z_by_roots(k0), ny
    ref = ny["refinement"]
    assert 1 <= ref["rounds"] <= ref["k_max"] == 10 and ref["samples_added"] > 0 and calls, ref
    f2 = np.asarray(f2)
    assert np.all(np.diff(f2) > 0) and set(np.round(np.log10(f), 9)) <= set(np.round(np.log10(f2), 9))
    assert np.asarray(L2) == pytest.approx(_L3(f2, k0), rel=1e-12)


def test_nyquist_adaptive_gives_up_after_k_max():
    """L 이 −1 을 극히 가까이 지나는 구조(세 같은 극, k0 = 8(1 + 1e-12): ω = √3·w 에서 L = −(1 + 1e-12)): 편각이 π 가까이
    도는 폭이 상대 1e-12 수준이라 k_max = 10 라운드(1024 분할)로는 π/2 아래로 못 줄인다 -> N 미정(None + 이유), 라운드 <= k_max."""
    poles = np.full(3, 2 * np.pi * 1e4)
    k0 = 8.0 * (1 + 1e-12)
    f = _grid(1.0, 1e9, 20)
    ny, _, _ = _sim_mod().nyquist_adaptive(f, _L3(f, k0, poles), sample_fn=_sampler(k0, poles), k_max=10)
    assert ny["encirclements_cw"] is None and ny["reason"], ny
    assert 1 <= ny["refinement"]["rounds"] <= 10, ny["refinement"]


def test_nyquist_adaptive_without_sampler_no_refinement():
    """sample_fn = None 이면 세분화 없음(docstring): 희박 표본 N = None, 라운드 0."""
    f = _grid(1.0, 1e9, 1)
    ny, f2, _ = _sim_mod().nyquist_adaptive(f, _L3(f, 1e3), sample_fn=None, k_max=10)
    assert ny["encirclements_cw"] is None and ny["refinement"]["rounds"] == 0 and len(f2) == len(f)


# ====================================================================== `.pz` RHP 계수(순수 함수, oracle (a))
def test_pz_rhp_count_resolution_and_sweep_limit():
    """README 절차 7 신뢰 규칙 (c): Re p > reltol·|p| 만 센다; (b) .ac 스윕 상한(2π f_stop) 밖 RHP 후보가 있으면 P = None +
    beyond_sweep. 손 대입(reltol 1e-4, f_stop 1e10 -> ω_stop 6.28e10): 5e4 ± j1e8 (Re/|p| = 5e-4) 둘, 1e5 실극 하나 -> 3;
    2e3 ± j1e8 (2e-5 < 1e-4) 은 0 근처라 안 셈; 음의 극 안 셈."""
    sim = _sim_mod()
    poles = [complex(-1e6, 0), complex(5e4, 1e8), complex(5e4, -1e8), complex(2e3, 1e8), complex(2e3, -1e8),
             complex(1e5, 0)]
    r = sim.pz_rhp_count(poles, 1e-4, 1e10)
    assert r["P"] == 3 and not r["beyond_sweep"] and r["n_poles"] == len(poles), r
    r2 = sim.pz_rhp_count(poles + [complex(5.9e13, 1e12)], 1e-4, 1e10)
    assert r2["P"] is None and len(r2["beyond_sweep"]) == 1, r2
    assert r2["omega_stop"] == pytest.approx(2 * math.pi * 1e10, rel=1e-12)


# ====================================================================== 최종 판정 분기(순수 함수, oracle (a)/(d))
def _nyq(n):
    return {"encirclements_cw": n, "reason": None if n is not None else "test"}


def _pz(p, validated=None, status="ok"):
    return {"status": status, "P": p, "rhp": [], "beyond_sweep": [], "n_poles": 5, "validated": validated}


JUDGE_CASES = [
    # (과도, N, pz, pm_raw) -> (verdict, pm_undefined, conditionally_stable)
    # 결정 4 + 설계 40 §4 C10 4: 폐루프 과도 unstable(한계 사이클 포함) -> FAIL. Z = 0 + 2 = 2.
    pytest.param("unstable", 0, _pz(2), 270.0, ("unstable", "open_loop_rhp_poles", False), id="transient_unstable"),
    # Q10: 과도가 결론 없음 + .pz P = 2 가 개루프 과도로 확인 -> Z = 2 >= 1 -> FAIL
    pytest.param("undetermined", 0, _pz(2, validated=True), 270.0, ("unstable", "open_loop_rhp_poles", False),
                 id="undetermined_pz_validated"),
    # Q10 + 설계 40 §4 C10 7: Z = 0 이라도 과도가 결론을 못 내면 안정이라 하지 않는다 -> INCOMPLETE(stability_unverified)
    pytest.param("undetermined", 0, _pz(0), 60.0, ("undetermined", "stability_unverified", False), id="undetermined_p0"),
    # 설계 40 §10.2 C10 행: 개루프 RHP(P = 2)이면서 Z = N + P = 0 이고 과도 안정 -> 합격(조건부 안정, PM 값 유지)
    pytest.param("stable", -2, _pz(2), 425.0, ("stable", None, True), id="conditionally_stable"),
    # N >= 1 이면 P >= 0 이라 Z >= 1 -> FAIL(과도가 결론을 못 내도)
    pytest.param("undetermined", 2, _pz(None, status="failed"), -20.0, ("unstable", None, False), id="n_positive"),
    # .pz 실패(P 모름) + 과도 stable + N = 0 -> 옛 표(절차 6): 안정, PM 값
    pytest.param("stable", 0, _pz(None, status="failed"), 60.0, ("stable", None, False), id="pz_failed_stable"),
    # .pz 신뢰 규칙(설계 40 §4 C10 8, 사용자 결정 2026-10-09 로 채택 -- README 절차 7 (d)):
    # 과도 stable 이면 P = −N(= 0), .pz 의 P = 2 는 pz_conflict 로 기록만 -> 안정
    pytest.param("stable", 0, _pz(2), 60.0, ("stable", None, False), id="trust_rule_d_transient_stable_ignores_pz"),
    # .pz 신뢰 규칙(설계 40 §4 C10 8 채택, README 절차 7 (e)): 과도 결론 없음 + N = 0 + .pz P = 2 미확인 -> P 를 쓰지 않음 -> INCOMPLETE
    pytest.param("failed", 0, _pz(2, validated=None), 270.0, ("undetermined", "stability_unverified", False),
                 id="trust_rule_e_unvalidated_pz_unused"),
]


@pytest.mark.parametrize("tran,n,pz,pm_raw,expected", JUDGE_CASES)
def test_stability_judgement_branches(tran, n, pz, pm_raw, expected):
    j = _sim_mod().stability_judgement(_nyq(n), tran, pm_raw=pm_raw, pz=pz)
    verdict, und, cond = expected
    assert j["verdict"] == verdict, j
    assert j["pm_undefined"] == und and j["pm_valid"] is (und is None), j
    assert bool(j["conditionally_stable"]) is cond, j


def test_stability_judgement_records_pz_conflict():
    """설계 40 §4 C10 8(사용자 결정 2026-10-09) '과도 stable 이면 .pz 를 쓰지 않는다(Z = 0, P = −N) ... .pz 가 −N 과 다르면
    pz_conflict 를 기록': 과도 stable, N = 0, .pz P = 2 -> pz_conflict, P_eff = −N = 0, Z = 0."""
    j = _sim_mod().stability_judgement(_nyq(0), "stable", pm_raw=60.0, pz=_pz(2))
    assert j["pz_conflict"] and j["P_eff"] == 0 and j["Z"] == 0 and j["P_pz"] == 2, j


PZ_CONFLICT_CASES = [
    # (N, .pz P) -> 과도 stable 이므로 Z = 0, P_eff = −N(Nyquist, 설계 40 §4 C10 8 '.pz 신뢰 규칙'), .pz 는 −N 과 다를 때만 pz_conflict.
    # 각 기대값은 정의를 손으로 대입(oracle (a)/(d)):
    # N = 0, .pz 가 가짜 RHP 2 개(파일럿 23 개형) -> 충돌, P_eff = 0, 조건부 안정 아님(P_eff = 0)
    pytest.param(0, 2, True, 0, False, id="spurious_rhp"),
    # N = −1(반시계 1 회), .pz 가 RHP 극을 놓침(P = 0) -> 충돌, P_eff = 1 이 정확(Z = N + P = 0), P_eff >= 1 & Z = 0 & 안정 -> 조건부 안정
    pytest.param(-1, 0, True, 1, True, id="missed_rhp"),
    # N = −2, .pz P = 2 -> 일치(충돌 없음), P_eff = 2, 조건부 안정
    pytest.param(-2, 2, False, 2, True, id="agree_p2"),
    # N = 0, .pz P = 0 -> 일치, P_eff = 0
    pytest.param(0, 0, False, 0, False, id="agree_p0"),
]


@pytest.mark.parametrize("n,pz_p,conflict,p_eff,cond", PZ_CONFLICT_CASES)
def test_pz_conflict_keeps_z_and_p_eff(n, pz_p, conflict, p_eff, cond):
    """설계 40 §4 C10 8 + README 절차 7 (d)·8(3fc2f20 계약 문장 'pz_conflict 에만 적는다(Z·P_eff 를 비우지 않는다)'):
    과도 stable 이면 Z = 0, P_eff = −N 이 .pz 와 무관하게 정해지고, .pz 가 −N 과 다르면 pz_conflict 만 참이다. verdict stable,
    pm_valid 유지(P_eff >= 1 이면 조건부 안정 -- PM 원값을 값으로)."""
    j = _sim_mod().stability_judgement(_nyq(n), "stable", pm_raw=60.0, pz=_pz(pz_p))
    assert j["Z"] == 0 and j["P_eff"] == p_eff and j["P_pz"] == pz_p, j
    assert bool(j["pz_conflict"]) is conflict, j
    assert j["verdict"] == "stable" and j["pm_undefined"] is None and j["pm_valid"] is True, j
    assert bool(j["conditionally_stable"]) is cond, j


# ====================================================================== 하측 이득 여유 순수 함수(설계 40 §4 C10 8 (iv))
def _lsgm():
    """피검 순수 함수 `oracle_simulate.low_side_gain_margin(freq, L)`(README 절차 8 이름) -- 소스는 열지 않고 import 만.
    반환 {low_side_gain_margin_db, low_side_crossings(x, 주파수 오름차순), low_side_crossing_hz, conditional_band}(docstring)."""
    return _sim_mod().low_side_gain_margin


# oracle (a) 구성으로 답이 정해진 합성 곡선: 음의 실축을 지나는 표본 쌍은 실수부가 같고 허수부가 ±1e-3 로 대칭이라
# 교차점 x 는 표본 사이 보간 방식(직교·극좌표)과 무관하게 그 실수부(|x| 오차 <= 1.3e-7)다.
#   표본: 20 −1e-3j (저주파, 양의 실축 근처) -> 5 −5j -> [−4 −1e-3j, −4 +1e-3j](x = −4, |L| > 1 에서 −180° 를 넘음)
#         -> [−2.5 +1e-3j, −2.5 −1e-3j](x = −2.5, 위상이 −180° 위로 돌아옴) -> 0.3 −0.3j(|L| = 1 교차, 위상 > −180°) -> 0.01 −1e-3j.
#   하측 교차(x < −1) = [−4, −2.5], min|x| = 2.5 -> 20·log10(2.5) = 7.9588 dB, 그 교차는 f[4] = 5 Hz 와 f[5] = 6 Hz 사이.
POLY_F = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
POLY_L = [20 - 1e-3j, 5 - 5j, -4 - 1e-3j, -4 + 1e-3j, -2.5 + 1e-3j, -2.5 - 1e-3j, 0.3 - 0.3j, 0.01 - 1e-3j]


def _hz_list(v):
    return [float(x) for x in (v if isinstance(v, (list, tuple)) else [v])]


def test_low_side_gain_margin_synthetic_polygon():
    """설계 40 §4 C10 8 (iv) `low_side_gain_margin_db` = 20·log10(min|x|), x = 음의 실축을 −1 바깥(x < −1)에서 지나는 점."""
    r = _lsgm()(np.array(POLY_F), np.array(POLY_L))
    assert r["low_side_gain_margin_db"] == pytest.approx(20 * math.log10(2.5), abs=1e-5), r
    assert [float(x) for x in r["low_side_crossings"]] == pytest.approx([-4.0, -2.5], abs=1e-5), r
    assert bool(r["conditional_band"]) is True, r
    hz = _hz_list(r["low_side_crossing_hz"])
    # min|x| 교차(x = −2.5)의 주파수는 그 표본 쌍 사이(5 ~ 6 Hz) -- 목록이면 두 교차 각각 [3, 4]·[5, 6] 사이
    if len(hz) == 1:
        assert 5.0 <= hz[0] <= 6.0, r
    else:
        assert len(hz) == 2 and 3.0 <= hz[0] <= 4.0 and 5.0 <= hz[1] <= 6.0, r


@pytest.mark.parametrize("curve", ["inside_minus_one", "no_axis_crossing"])
def test_low_side_gain_margin_none_without_outer_crossing(curve):
    """하측 교차가 없으면 None(docstring '없으면 None'), 조건부 대역 아님(oracle (a)):
      * inside_minus_one: 음의 실축을 x = −0.5(−1 안쪽, 보통의 이득 여유 자리)에서만 지남 -> 하측 교차 아님;
      * no_axis_crossing: 단일 극 L = 10/(1 + jf) -- 위상 > −90° 라 음의 실축을 지나지 않음."""
    if curve == "inside_minus_one":
        f = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        L = np.array([5 - 1e-3j, 0.5 - 2j, -0.5 - 1e-3j, -0.5 + 1e-3j, -0.01 + 1e-3j])
    else:
        f = np.logspace(-2, 4, 121)
        L = 10 / (1 + 1j * f)
    r = _lsgm()(f, L)
    assert r["low_side_gain_margin_db"] is None, r
    assert not r["low_side_crossings"] and not r["conditional_band"], r


def _cond_L(f):
    """해석식 조건부 안정 루프(oracle (b) 다른 방법의 기준): L(s) = K(1 + s/z)³/((1 + s/p)⁴(1 + s/p2)), s = j·f,
    K = 1e8, z = 30, p = 1, p2 = 1e5. 위상이 p 근처에서 −180° 아래로 갔다가(|L| ~ 2e7) z 근처에서 돌아오고(|L| ~ 120),
    |L| = 1 교차(~3.7e3)에서는 위상 ~ −92°(PM > 0). 음의 실축 교차 둘 다 x < −1."""
    s = 1j * np.asarray(f, dtype=float)
    return 1e8 * (1 + s / 30.0) ** 3 / ((1 + s / 1.0) ** 4 * (1 + s / 1e5))


def _exact_axis_roots(f):
    """Im L(f) = 0 의 근을 표본 쌍마다 이분법(로그 중점, 200 회)으로 정확히 구한 (f*, Re L(f*)) -- 음의 실축(Re < 0)만."""
    L = _cond_L(f)
    out = []
    for i in range(len(f) - 1):
        if (L[i].imag > 0) != (L[i + 1].imag > 0):
            lo, hi = float(f[i]), float(f[i + 1])
            for _ in range(200):
                m = math.sqrt(lo * hi)
                if (_cond_L(lo).imag > 0) == (_cond_L(m).imag > 0):
                    lo = m
                else:
                    hi = m
            x = float(_cond_L(lo).real)
            if x < 0:
                out.append((lo, x, float(f[i]), float(f[i + 1])))
    return out


def test_low_side_gain_margin_analytic_matches_exact_roots():
    """oracle (b): 해석식 L 의 음의 실축 교차를 이분법으로 정확히 구해(표본 보간과 다른 방법) 하측 교차 x < −1 둘의 실수값과
    min|x| 의 dB 를 대조. 허용오차 = 표본 사이 선형 보간 오차의 상계: 200/decade 격자에서 이 곡선의 보간 x 와 정확한 x 의 차는
    상대 1.7e-4(바깥 교차)·5.1e-5(안쪽)(scratch 2026-10-09 측정) -> x 는 상대 1e-3, dB 는 0.01 dB 로 둔다."""
    f = np.logspace(-3, 8, 11 * 200 + 1)
    roots = _exact_axis_roots(f)
    outer = [r for r in roots if r[1] < -1]
    assert len(outer) == 2, roots                                             # 전제: 하측 교차 둘
    r = _lsgm()(f, _cond_L(f))
    xs = [float(x) for x in r["low_side_crossings"]]
    assert xs == pytest.approx([x for _, x, _, _ in outer], rel=1e-3), (xs, outer)
    want_db = 20 * math.log10(min(abs(x) for _, x, _, _ in outer))
    assert r["low_side_gain_margin_db"] == pytest.approx(want_db, abs=0.01), (r, want_db)
    assert bool(r["conditional_band"]) is True
    hz = _hz_list(r["low_side_crossing_hz"])
    k = min(range(2), key=lambda i: abs(outer[i][1]))                         # min|x| 교차
    if len(hz) == 1:
        assert outer[k][2] <= hz[0] <= outer[k][3], (hz, outer[k])
    else:
        assert len(hz) == 2 and all(o[2] <= h <= o[3] for h, o in zip(hz, outer)), (hz, outer)


# ====================================================================== 조건부 안정 fixture(설계 40 §10.2 C10 행, oracle (c))
# 회로: test_oracle_c10_stability 의 손 RHP 회로(nin -> M1 -> n1 -> M2 -> n2, n2 -Cc- n3(Rb 로 0.7 V) -> M3(드레인 n1) = DC 를 막은
#   내부 양되먹임)에서 M1 을 16 finger, M3 를 1 finger 로 하고 n2 에 부하 C 2 pF 를 단다. 손 모형 A = A0(1+sτ)/(1 − sτ(K−1)) 에서
#   A0 > K − 1 이면 단위 음되먹임 폐루프 특성근 s = −(1 + A0)/(τ(1 + A0 − K)) < 0 -- 개루프 RHP 극이 있어도 폐루프 안정(조건부 안정).
#   R1 은 V(n1) = V(nin) = 0.7 V 가 되도록 독립 .op(n1 고정, M1·M3 전류)에서 유도한다.
COND = dict(vdd=1.8, vb=0.7, vin=0.7, r2=129400.0, rb=1e5, cc=1e-12, cl=2e-12, L=0.5e-6, fw=2e-6, n1f=16, n2f=2, n3f=1)


def cond_body(r1, vin_line=None):
    c = COND
    b = [f"Vdd vdd 0 DC {c['vdd']}", f"Vb vb 0 DC {c['vb']}", vin_line or f"Vin nin 0 DC {c['vin']} AC 1",
         f"R1 vdd n1 {r1}", f"R2 vdd n2 {c['r2']}", f"Rb vb n3 {c['rb']}", f"Cc n2 n3 {c['cc']}", f"CL n2 0 {c['cl']}"]
    for nm, d, g, n in (("M1", "n1", "nin", c["n1f"]), ("M2", "n2", "n1", c["n2f"]), ("M3", "n1", "n3", c["n3f"])):
        b += [f"X{nm}_{k} {d} {g} 0 0 {NFET} l={c['L']} w={c['fw']}" for k in range(n)]
    return b


@pytest.fixture(scope="module")
def cond_ref(ref_root):
    c = COND
    # R1: n1 을 0.7 V 로 묶은 독립 .op 에서 M1(게이트 0.7)·M3(게이트 vb 0.7) 전류 합 I -> R1 = (VDD − 0.7)/I
    body = [f"Vn1 n1 0 DC {c['vin']}", f"Vg g 0 DC {c['vin']}"]
    body += [f"XM1_{k} n1 g 0 0 {NFET} l={c['L']} w={c['fw']}" for k in range(c["n1f"])]
    body += [f"XM3_{k} n1 g 0 0 {NFET} l={c['L']} w={c['fw']}" for k in range(c["n3f"])]
    i = abs(run_spice("\n".join(body), ref_root / "cond_r1", ["i(vn1)"])["op"]["i(vn1)"])
    r1 = (c["vdd"] - c["vin"]) / i
    r = run_spice("\n".join(cond_body(r1)), ref_root / "cond_ac", ["v(n1)", "v(n2)"], ac_out="n2", ac=(0.01, 1e10, 40))
    H = r["H"]
    poles = independent_pz(cond_body(r1, vin_line=f"Vin nin 0 DC {c['vin']}"), "n2", ref_root / "cond_pz")
    # 독립 폐루프 .tran: nin = (0.7 + V2op + 킥) − V(n2) (이상 VCVS 단위 음되먹임, A(0) > 0), 킥 = V_T 급 0.0259 V, 1 ns
    v2 = r["op"]["v(n2)"]
    v0 = c["vin"] + v2
    tb = cond_body(r1, vin_line="Ecl nin cl n2 0 -1") + [
        f"Vcl cl 0 DC {v0} PULSE({v0} {v0 + 0.0259} 1e-9 1e-10 1e-10 1e-9 1)", ".save v(n2)"]
    ctrl = [".control", "set noaskquit", "tran 1e-10 2e-6 0 1e-10", "let h = v(n2)", "set wr_singlescale",
            "wrdata g.txt h", "quit", ".endc", ".end"]
    wd = ref_root / "cond_cl"
    _ngspice(_head() + tb + ctrl, wd)
    a = np.loadtxt(wd / "g.txt")
    t, e = a[:, 0], np.abs(a[:, 1] - v2)
    return {"r1": r1, "f": r["f"], "H": H, "L": np.sign(H[0].real) * H, "op": r["op"], "poles": poles,
            "e_early": float(e[(t > 1e-9) & (t < 2e-7)].max()), "e_late": float(e[t > 1.8e-6].max())}


def cond_input(lut, r1, constraints):
    c = COND

    def dev(name, d, g, n):
        return {"name": name, "kind": "nmos", "drain": d, "gate": g, "source": "gnd", "bulk": "gnd", "L": c["L"],
                "finger_w": c["fw"], "n_fingers": n, "W": c["fw"] * n}

    inp = {"schema": "spice_oracle_input/1", "circuit": "tcondstab", "process": conftest.process_block(lut),
           "rails": [{"net": "vdd", "voltage": c["vdd"]}, {"net": "vb", "voltage": c["vb"]},
                     {"net": "gnd", "voltage": 0.0, "reference": True}],
           "devices": [dev("M1", "n1", "nin", c["n1f"]), dev("M2", "n2", "n1", c["n2f"]), dev("M3", "n1", "n3", c["n3f"])],
           "sources": [],
           "passives": [{"name": "R1", "kind": "resistor", "terminals": ["vdd", "n1"], "value": r1},
                        {"name": "R2", "kind": "resistor", "terminals": ["vdd", "n2"], "value": c["r2"]},
                        {"name": "Rb", "kind": "resistor", "terminals": ["vb", "n3"], "value": c["rb"]},
                        {"name": "Cc", "kind": "capacitor", "terminals": ["n2", "n3"], "value": c["cc"]},
                        {"name": "CL", "kind": "capacitor", "terminals": ["n2", "gnd"], "value": c["cl"]}],
           "ports": {"input": "nin", "output": "n2"},
           "predictions": {"nodes": {"nin": c["vin"]}, "devices": {k: {"off_current_A": 0.0} for k in ("M1", "M2", "M3")},
                           "metrics": []},
           "testbench": conftest.testbench_block(), "acceptance": {"constraints": constraints}}
    return zero_diffusion(inp)


def test_conditionally_stable_fixture_premise(cond_ref):
    """전제(oracle (c), 피검 코드 없음): 독립 .pz 의 개루프 RHP 극 P >= 1, 독립 .ac 의 N = −P(반시계), 독립 폐루프 .tran 감쇠."""
    p = rhp_count_in_sweep(cond_ref["poles"], 1e10)
    ny = nyquist(cond_ref["L"])
    assert p >= 1 and ny["N"] == -p, (p, ny, [q for q in cond_ref["poles"] if q.real > 0])
    assert cond_ref["e_early"] > 1e-3 and cond_ref["e_late"] < 1e-6, (cond_ref["e_early"], cond_ref["e_late"])


def test_conditionally_stable_passes(tmp_path, cond_ref):
    """설계 40 §10.2 C10 행 '개루프 RHP이면서 Z = 0이고 과도 안정 -> 합격'(+ §4 C10 5 '개루프 RHP 극점만으로 FAIL 을 내지 않는다').
    오라클의 N = 독립 .ac 의 N(오라클 AC 데이터에서도 다시 셈), Z = N + P = 0, 폐루프 과도 stable, 조건부 안정, PM = Bode 원값,
    pm 제약(독립 PM − 5 deg 하한) PASS."""
    pm_mine = measure(cond_ref["f"], cond_ref["H"])["pm_deg"]
    inp = cond_input(make_lut(tmp_path / "lut.npz"), cond_ref["r1"],
                     [{"name": "pmc", "measure": "pm_deg", "op": ">=", "limit": pm_mine - 5.0}])
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    assert c is not None, (p.stdout + p.stderr)[-1500:]
    f, L, _ = ac_loop_from_files(tmp_path / "o", stem_of(inp, "free"), beta_loop=False)
    n_mine = nyquist(L)["N"]
    p_mine = rhp_count_in_sweep(cond_ref["poles"], inp["testbench"]["ac"]["fstop_hz"])
    assert n_mine == nyquist(cond_ref["L"])["N"] == -p_mine, (n_mine, p_mine)
    st = c["summary"]["stability"]
    assert st["nyquist_encirclements_cw"] == n_mine and st["transient_status"] == "stable", st
    assert st["verdict"] == "stable" and st["Z"] == 0 and st["conditionally_stable"] is True, st
    assert st["open_loop_rhp_poles"] == p_mine and st["pm_valid"] is True and st["pm_undefined"] is None, st
    ac = json.loads((tmp_path / "o" / f"{stem_of(inp, 'free')}.sim.json").read_text(encoding="utf-8"))["ac"]
    assert ac["pm_deg"] == ac["pm_deg_raw"] == pytest.approx(pm_mine, abs=0.05), (ac["pm_deg"], pm_mine)
    assert c["summary"]["verdict"] == "PASS" and p.returncode == 0, c["summary"]


# ====================================================================== 보상 내부 루프(Miller) 회로의 P = 0(설계 40 §11 J 추가 범위, oracle (c))
# 회로: 2단 CS(M1 2 finger -> n1 -> M2 4 finger -> n2 출력), Miller Cc(n1–n2) = 2단 둘레 국소 음되먹임(보상 내부 루프, J-B 의
#   '중첩 Miller 내부 루프 = 보상 루프'의 최소형), 부하 CL. 단마다 저항 R_i 는 V(n_i) = 0.7 V 가 되도록 독립 .op 에서 유도한다.
#   ngcc·nmcnr 같은 3단 중첩 Miller 는 2단이 비반전이어야 하는데 이 test 의 NMOS CS 사슬은 모두 반전이라 만들지 않았다(보고).
MILLER = dict(vdd=1.8, vin=0.7, L=0.5e-6, fw=2e-6, nf=(2, 4), cc=3e-12, cl=2e-12)


def miller_body(rs, vin_line=None):
    c = MILLER
    b = [f"Vdd vdd 0 DC {c['vdd']}", vin_line or f"Vin nin 0 DC {c['vin']} AC 1"]
    prev = "nin"
    for i, (r, n) in enumerate(zip(rs, c["nf"]), 1):
        b += [f"R{i} vdd n{i} {r}"] + [f"XM{i}_{k} n{i} {prev} 0 0 {NFET} l={c['L']} w={c['fw']}" for k in range(n)]
        prev = f"n{i}"
    b += [f"Cc n1 n2 {c['cc']}", f"CL n2 0 {c['cl']}"]
    return b


@pytest.fixture(scope="module")
def miller_ref(ref_root):
    c = MILLER
    rs = []
    for n in c["nf"]:
        body = [f"Vn n 0 DC {c['vin']}", f"Vg g 0 DC {c['vin']}"] + [
            f"XM_{k} n g 0 0 {NFET} l={c['L']} w={c['fw']}" for k in range(n)]
        i = abs(run_spice("\n".join(body), ref_root / f"miller_r{n}", ["i(vn)"])["op"]["i(vn)"])
        rs.append((c["vdd"] - c["vin"]) / i)
    r = run_spice("\n".join(miller_body(rs)), ref_root / "miller_ac", ["v(n1)", "v(n2)"], ac_out="n2",
                  ac=(0.01, 1e10, 40))
    poles = independent_pz(miller_body(rs, vin_line=f"Vin nin 0 DC {c['vin']}"), "n2", ref_root / "miller_pz")
    return {"rs": rs, "f": r["f"], "H": r["H"], "L": np.sign(r["H"][0].real) * r["H"], "poles": poles, "op": r["op"]}


def miller_input(lut, rs, constraints):
    c = MILLER
    devs = [{"name": f"M{i}", "kind": "nmos", "drain": f"n{i}", "gate": g, "source": "gnd", "bulk": "gnd", "L": c["L"],
             "finger_w": c["fw"], "n_fingers": n, "W": c["fw"] * n} for i, (g, n) in enumerate(zip(("nin", "n1"), c["nf"]), 1)]
    inp = {"schema": "spice_oracle_input/1", "circuit": "tmiller2", "process": conftest.process_block(lut),
           "rails": [{"net": "vdd", "voltage": c["vdd"]}, {"net": "gnd", "voltage": 0.0, "reference": True}],
           "devices": devs, "sources": [],
           "passives": [{"name": f"R{i}", "kind": "resistor", "terminals": ["vdd", f"n{i}"], "value": r}
                        for i, r in enumerate(rs, 1)]
           + [{"name": "Cc", "kind": "capacitor", "terminals": ["n1", "n2"], "value": c["cc"]},
              {"name": "CL", "kind": "capacitor", "terminals": ["n2", "gnd"], "value": c["cl"]}],
           "ports": {"input": "nin", "output": "n2"},
           "predictions": {"nodes": {"nin": c["vin"]}, "devices": {k["name"]: {"off_current_A": 0.0} for k in devs},
                           "metrics": []},
           "testbench": conftest.testbench_block(), "acceptance": {"constraints": constraints}}
    return zero_diffusion(inp)


def test_miller_compensation_loop_pz_p_zero(tmp_path, miller_ref):
    """설계 40 §11 J 추가 범위(J-B): 보상 내부 루프 회로의 전체 PM 판정에 개루프 P = 0(.pz)이 들어간다.
    독립 .pz(oracle (c)): RHP 극 0 개, 독립 .ac: N = 0. 오라클: .pz 성공(status ok)이고 P = 0 = 독립 값, Z = 0, P_eff = 0,
    과도 stable -> verdict stable, PM = 독립 .ac 측정값(값으로 유효), pm 제약(독립 PM − 5 deg) PASS."""
    p_mine = rhp_count_in_sweep(miller_ref["poles"], 1e10)
    n_mine = nyquist(miller_ref["L"])["N"]
    pm_mine = measure(miller_ref["f"], miller_ref["H"])["pm_deg"]
    assert p_mine == 0 and n_mine == 0 and pm_mine > 30.0, (p_mine, n_mine, pm_mine)        # 전제
    inp = miller_input(make_lut(tmp_path / "lut.npz"), miller_ref["rs"],
                       [{"name": "pmc", "measure": "pm_deg", "op": ">=", "limit": pm_mine - 5.0}])
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    assert c is not None, (p.stdout + p.stderr)[-1500:]
    st = c["summary"]["stability"]
    assert st["pz_status"] == "ok" and st["pz_P"] == p_mine, st
    assert st["nyquist_encirclements_cw"] == n_mine and st["Z"] == 0 and st["verdict"] == "stable", st
    ac = json.loads((tmp_path / "o" / f"{stem_of(inp, 'free')}.sim.json").read_text(encoding="utf-8"))["ac"]
    assert ac["stability"]["P_eff"] == 0 and ac["stability"]["pz"]["P"] == 0, ac["stability"]
    assert ac["pm_deg"] == pytest.approx(pm_mine, abs=0.05) and st["pm_valid"] is True, (ac["pm_deg"], pm_mine)
    assert c["summary"]["verdict"] == "PASS" and p.returncode == 0, c["summary"]


# ====================================================================== 조건부 안정(P = 0) 손 toy: PM·표시·하측 이득 여유
# 설계 40 §4 C10 8 '조건부 안정'(사용자 결정 2026-10-09): Z = 0 이고 과도 stable 이면 pm_valid 유지, PM = 모든 |T| = 1 교차의
# 최솟값, P >= 1 이거나 교차 아래 |T| > 1 구간에서 위상이 −180° 를 넘으면 conditionally_stable 표시 + 하측 이득 여유(루프 이득이
# 몇 dB 줄면 감김 수가 바뀌는지, 같은 .ac 에서) 보고(제약 아님).
# 손 toy(oracle (a)): 3단 NMOS CS(세 반전단, 단마다 V(n_i) = 0.7 V 인 부하 R = THREE.rl), 단마다 lag-lead 부하 Rz(= R/20)+Cz(1 nF)
#   -> 단 전달 ∝ (1 + s Rz Cz)/(1 + s (R + Rz) Cz): 극 1.17 kHz, 영점 24.6 kHz(비 21). 단당 최대 위상 지연 asin(20/22) = 65.4°,
#   세 단 196° > 180° 이고 그 주파수(극·영점의 기하평균)에서 |L| ~ (gm R)^3·21^(−3/2) >> 1 -> −180° 를 넘는 |L| > 1 구간(위상이
#   돌아와 교차 위에서는 안정: P = 0, N = 0). 음의 실축 교차 둘(|x| > 1)이 생기며 하측 이득 여유 = 20·log10(min |x|).
LEADLAG = dict(rz_ratio=20.0, cz=1e-9)


def leadlag_body(vin_line=None):
    c = THREE
    b = [f"Vdd vdd 0 DC {c['vdd']}", vin_line or f"Vin nin 0 DC {c['vin']} AC 1"]
    prev = "nin"
    for i in (1, 2, 3):
        b += [f"R{i} vdd n{i} {c['rl']}", f"Rz{i} n{i} z{i} {c['rl'] / LEADLAG['rz_ratio']}", f"Cz{i} z{i} 0 {LEADLAG['cz']}"]
        b += [f"XM{i}_{k} n{i} {prev} 0 0 {NFET} l={c['L']} w={c['fw']}" for k in range(c["n"])]
        prev = f"n{i}"
    return b


def leadlag_input(lut, constraints):
    c = THREE
    pas = []
    for i in (1, 2, 3):
        pas += [{"name": f"R{i}", "kind": "resistor", "terminals": ["vdd", f"n{i}"], "value": c["rl"]},
                {"name": f"Rz{i}", "kind": "resistor", "terminals": [f"n{i}", f"z{i}"], "value": c["rl"] / LEADLAG["rz_ratio"]},
                {"name": f"Cz{i}", "kind": "capacitor", "terminals": [f"z{i}", "gnd"], "value": LEADLAG["cz"]}]
    inp = {"schema": "spice_oracle_input/1", "circuit": "tleadlag3", "process": conftest.process_block(lut),
           "rails": [{"net": "vdd", "voltage": c["vdd"]}, {"net": "gnd", "voltage": 0.0, "reference": True}],
           "devices": [{"name": f"M{i}", "kind": "nmos", "drain": f"n{i}", "gate": g, "source": "gnd", "bulk": "gnd",
                        "L": c["L"], "finger_w": c["fw"], "n_fingers": c["n"], "W": c["fw"] * c["n"]}
                       for i, g in ((1, "nin"), (2, "n1"), (3, "n2"))],
           "sources": [], "passives": pas, "ports": {"input": "nin", "output": "n3"},
           "predictions": {"nodes": {"nin": c["vin"]}, "devices": {k: {"off_current_A": 0.0} for k in ("M1", "M2", "M3")},
                           "metrics": []},
           "testbench": conftest.testbench_block(), "acceptance": {"constraints": constraints}}
    return zero_diffusion(inp)


def neg_real_axis_crossings(L):
    """L 곡선(양의 주파수)이 음의 실축을 지나는 점의 실수값(표본 사이 선형 보간) -- 하측 이득 여유의 독립 계산(oracle (b))."""
    out = []
    for i in range(len(L) - 1):
        a, b = L[i], L[i + 1]
        if (a.imag > 0) != (b.imag > 0):
            t = a.imag / (a.imag - b.imag)
            x = a.real + t * (b.real - a.real)
            if x < 0:
                out.append(float(x))
    return out


def pm_at_crossings(f, L):
    """README 'PM 정의'(PM = 180 − (기준점 위상 − 교차 위상), 위상 펼침)를 모든 |L| = 1 교차에서 -- 설계 40 §4 C10 8 'PM 은 모든
    교차의 최솟값' 의 독립 계산(log f 선형 보간)."""
    ph = np.degrees(np.unwrap(np.angle(L)))
    lf = np.log10(f)
    out = []
    for fc in gain_crossings(f, L):
        out.append(180.0 - (ph[0] - float(np.interp(math.log10(fc), lf, ph))))
    return out


def _find_key(d, *words):
    """중첩 dict 에서 이름에 words 가 모두 든 키의 값 목록(필드 이름은 설계가 정하지 않음 -- '하측 이득 여유' 보고 필드 탐색)."""
    hits = []
    if isinstance(d, dict):
        for k, v in d.items():
            if all(w in k.lower() for w in words) and isinstance(v, (int, float)) and not isinstance(v, bool):
                hits.append(v)
            hits += _find_key(v, *words)
    return hits


@pytest.fixture(scope="module")
def leadlag_ref(ref_root):
    r = run_spice("\n".join(leadlag_body()), ref_root / "leadlag_ac", ["v(n3)"], ac_out="n3", ac=(0.01, 1e10, 40))
    H = r["H"]
    return {"f": r["f"], "H": H, "L": np.sign(H[0].real) * H,
            "poles": independent_pz(leadlag_body(vin_line=f"Vin nin 0 DC {THREE['vin']}"), "n3", ref_root / "leadlag_pz")}


def test_leadlag_toy_premise(leadlag_ref):
    """전제(oracle (a)·(c)): 독립 .ac 에서 N = 0, |L| > 1 인 구간의 최소 위상 < −180°(교차 아래), 음의 실축 교차 중 |x| > 1 이 있음,
    독립 .pz RHP 극 0 개."""
    L, f = leadlag_ref["L"], leadlag_ref["f"]
    ph = np.degrees(np.unwrap(np.angle(L)))
    assert nyquist(L)["N"] == 0
    assert ph[np.abs(L) > 1].min() < -180.0, ph[np.abs(L) > 1].min()
    assert [x for x in neg_real_axis_crossings(L) if x < -1], neg_real_axis_crossings(L)
    assert rhp_count_in_sweep(leadlag_ref["poles"], 1e10) == 0


def test_conditionally_stable_p0_flag_pm_and_low_side_gain_margin(tmp_path, leadlag_ref):
    """설계 40 §4 C10 8: P = 0 이지만 교차 아래 |T| > 1 구간에서 위상이 −180° 를 넘는 루프 -> verdict stable, pm_valid 유지,
    PM = 모든 교차 PM 의 최솟값(오라클 AC 데이터로 독립 계산), conditionally_stable 표시, 하측 이득 여유(dB) =
    20·log10(min{|x| : 음의 실축 교차 x < −1})(독립 계산 (b): 루프 이득을 1/|x| 배로 줄이면 −1 이 그 교차에 놓여 감김 수가 바뀐다)를 보고.
    하측 이득 여유는 보고일 뿐 제약이 아니다(verdict PASS)."""
    pms = pm_at_crossings(leadlag_ref["f"], leadlag_ref["L"])
    inp = leadlag_input(make_lut(tmp_path / "lut.npz"),
                        [{"name": "pmc", "measure": "pm_deg", "op": ">=", "limit": min(pms) - 5.0}])
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    assert c is not None, (p.stdout + p.stderr)[-1500:]
    f, L, _ = ac_loop_from_files(tmp_path / "o", stem_of(inp, "free"), beta_loop=False)
    xs = [x for x in neg_real_axis_crossings(L) if x < -1]
    gm_low_db = 20 * math.log10(min(abs(x) for x in xs))
    st = c["summary"]["stability"]
    assert st["verdict"] == "stable" and st["pm_valid"] is True and st["Z"] == 0, st
    ac = json.loads((tmp_path / "o" / f"{stem_of(inp, 'free')}.sim.json").read_text(encoding="utf-8"))["ac"]
    assert ac["pm_deg"] == pytest.approx(min(pm_at_crossings(f, L)), abs=0.05), (ac["pm_deg"], pm_at_crossings(f, L))
    assert st["conditionally_stable"] is True, st
    gms = _find_key(c["summary"], "gain_margin") + _find_key(ac, "gain_margin")
    assert gms and any(g == pytest.approx(gm_low_db, abs=0.1) for g in gms), (gms, gm_low_db)
    assert c["summary"]["verdict"] == "PASS" and p.returncode == 0, c["summary"]


def test_pm_is_minimum_over_all_crossings(tmp_path, ref_root):
    """설계 40 §4 C10 8 'PM 은 모든 |T| = 1 교차의 최솟값': 교차 3 개인 쌍T 노치 회로(test_multi_crossing_plan_uses_f_lo 와 같은
    회로, 독립 .ac N = 0, 과도 stable) -> ac.pm_deg = 오라클 AC 데이터에서 독립 계산한 교차별 PM 의 최솟값."""
    cn1 = 20e-12
    ref = notch_ref(ref_root, cn1)
    assert len(ref["cross"]) == 3 and ref["nyq"]["N"] == 0
    inp = notch_input(make_lut(tmp_path / "lut.npz"), cn1)
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    assert res["free"] is not None, (p.stdout + p.stderr)[-1500:]
    f, L, _ = ac_loop_from_files(tmp_path / "o", stem_of(inp, "free"), beta_loop=False)
    pms = pm_at_crossings(f, L)
    assert len(pms) == 3
    st = res["free"]["summary"]["stability"]
    ac = json.loads((tmp_path / "o" / f"{stem_of(inp, 'free')}.sim.json").read_text(encoding="utf-8"))["ac"]
    assert st["verdict"] == "stable" and st["pm_valid"] is True, st
    assert ac["pm_deg"] == pytest.approx(min(pms), abs=0.05), (ac["pm_deg"], pms)


# ====================================================================== 차동 입력 β=1: 관측 = 가중 부호 합, floor 는 관측 노드들
@pytest.fixture(scope="module")
def t5_stab_run(tmp_path_factory):
    """u6_toy5t 5T OTA(차동 입력 inp/inn, 단일 출력 out) -- β=1 루프의 폐루프 과도 기록·넷리스트."""
    import u6_toy5t as toy
    conftest.require_spice()
    d = tmp_path_factory.mktemp("t5stab")
    nom = toy.nominal_op(d / "ind_op")
    inp = toy.toy_input(d, nom, judge={"sat_margin_V": SAT})
    p, res = run_oracle(inp, d / "o", sat_margin=SAT)
    assert res["free"] is not None, (p.stdout + p.stderr)[-1500:]
    return d, inp, nom


def test_differential_beta1_observe_weighted_sign_sum_and_floor(t5_stab_run):
    """설계 40 §4 C10 8 '자극 위치' + 'U6 test 후속 정의' (i)(a1e1d2c), README 절차 3·4:
      * 관측 H = 끊는 점(β=1: 루프를 닫는 입력 넷들) 노드 전압의 가중치 부호 합 -> plan.observe = [["inp", +1], ["inn", −1]]
        (oracle (a) 구성: testbench input_p_ac = +0.5, input_n_ac = −0.5 의 부호), `let hst` 피연산자 = {v(inp), v(inn)}.
      * floor = 관측 노드마다 reltol·|V_op| + vntol 의 합(출력 노드 아님). V_op 는 이 test 의 독립 servo 넷리스트 .op
        (u6_toy5t.nominal_op, oracle (c)) 의 v(inp)·v(inn). reltol·vntol = testbench options(1e-4, 1e-7). 허용 상대 1e-4:
        V_op 출처(독립 servo 대 오라클 동작점 패스)만 다르다(check_plan_record 와 같은 근거)."""
    from test_oracle_c10_stability import hst_operands
    d, inp, nom = t5_stab_run
    tb = inp["testbench"]
    assert tb["ac"]["input_p_ac"] > 0 > tb["ac"]["input_n_ac"]                     # 전제(가중 부호)
    st = json.loads((d / "o" / f"{stem_of(inp, 'free')}.sim.json").read_text(encoding="utf-8"))["ac"]["stability"]
    assert st["loop"] == "beta_1", st.get("loop")
    rec = st["transient"]["plan"]
    obs = sorted((str(n).lower(), float(s)) for n, s in rec["observe"])
    assert obs == sorted([("inp", 1.0), ("inn", -1.0)]), rec["observe"]
    text = (d / "o" / f"{stem_of(inp, 'free')}.stab.cir").read_text(encoding="utf-8")
    assert hst_operands(text) == {"v(inp)", "v(inn)"}, hst_operands(text)
    reltol, vntol = float(tb["options"]["reltol"]), float(tb["options"]["vntol"])
    floor = sum(reltol * abs(nom[k]) + vntol for k in ("inp", "inn"))
    assert rec["floor_V"] == pytest.approx(floor, rel=1e-4), (rec["floor_V"], floor)
    # 출력 노드 기준이었다면 reltol·|V(out)| + vntol 하나(노드 1 개) -- 관측 노드 2 개 합과 구별됨(전제: 두 값이 1e-4 보다 크게 다름)
    assert abs(floor - (reltol * abs(nom["out"]) + vntol)) > 1e-4 * floor


# ====================================================================== 거부(설정·스키마)
def test_stability_config_without_wall_cap_rejected(tmp_path):
    """계약 1(c): 창당 상한이 선언돼 있지 않으면 조용한 기본값 없이 예외(stability_config docstring)."""
    cfg = tmp_path / "oracle_config.json"
    cfg.write_text(json.dumps({"stability_transient": {"justification": "x"}}), encoding="utf-8")
    with pytest.raises((KeyError, ValueError, RuntimeError)):
        _sim_mod().stability_config(str(cfg))
