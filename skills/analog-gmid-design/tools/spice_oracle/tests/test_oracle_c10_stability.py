"""C10 PM 안정성 근거(README "[신규] C10 PM 안정성 근거") + C8(정의 불가 -> PASS 불가) + C20(교차 측정 무효) + C21(stability_cache).

근거: README C10·C8·C20·C21 과 "[신규] C10 PM 안정성 근거" 절, oracle_input.schema.json 만(오라클 소스는 열지 않는다).

기대값(피검 코드 출력으로 만들지 않음):
  * 손으로 쓴 독립 ngspice 넷리스트(finger 마다 인스턴스, m/nf 없음, 이상 전압원 입력):
    - 개루프 RHP 극 회로(trhp_posfb): nin -> M1(CS, R1) -> n1 -> M2(CS, R2) -> n2(출력), n2 -Cc- n3(Rb 로 0.7 V 레일)
      -> M3(드레인 n1) = DC 를 막은 양되먹임. 손 모형(.op gm·gds): A = A0(1+sτ)/(1+sτ(1-K)),
      K = gm2·gm3/(G1·G2), G1 = 1/R1 + gds1 + gds3, G2 = 1/R2 + gds2, τ = Rb·Cc -> RHP 극 p = 1/(τ(K-1)).
      독립 개루프 .tran(입력 고정, n3 에 작은 전류 킥)의 지수 증가율로 RHP 극을 확인하고, 독립 폐루프 .tran
      (이상 VCVS 단위 음되먹임)으로 폐루프가 불안정(지속 진동·포화)임을 확인한다.
    - 고전적 불안정(P = 0) 3단 CS(t3stage): 손 모형 L0/((1+s/p1)(1+s/p2)(1+s/p3)), 독립 .ac 로 PM(음수)과 N = 2.
    - 안정 루프: 같은 3단(지배극 분리, PM ~16 deg), conftest CS(β=1), conftest 되먹임(β 루프, 해석식 T).
  * N(시계 방향 감은 수)은 이 파일의 `nyquist()` 가 README 절차 2 의 정의대로(켤레 반쪽 + 측정 반쪽 + 두 닫는 직선,
    1+L 편각 변화 합, 표본 사이 ±π 접기, 유효 조건 (a)(b)(c)) **오라클이 쓴 AC 데이터 파일**과 독립 .ac 데이터에서 센다.
  * 과도 계획·판정(절차 4·5)은 이 파일의 `plan()`·`decide()` 가 입력값·독립 .op·L 데이터·`.stab.txt` 에서 다시 계산한다.
  * 조기 종결 계약 개정(사용자 결정 B 2026-10-08, docs/03-analysis/oracle-c10-early-termination.contract.md 절 1(a)~(d)):
    - (a) f_crit = 측정 L 에서 |1+L| 최소 표본의 주파수(오라클 AC 데이터에서 이 파일이 다시 찾음),
      n_pp = 정현파 봉우리 표본 오차 1 − cos(π/n) <= reltol 인 최소 n(이 파일은 폐형식 대신 n = 1, 2, ... 전수 탐색,
      oracle (b)), tmax = min(1/(2π f_lo), 1/(f_crit·n_pp)), td = tr = tf = pw = 1/(2π f_lo) 불변.
    - (b) 조기 unstable: g(j) = M_j(1 − reltol) > M_{j−1}(1 + reltol) + floor', j >= 3 인 첫 창에서 g(j−1)·g(j)·M_j >= M_1.
      순수 함수 `oracle_simulate.early_unstable(M, floor', reltol)` 은 합성 입력 리터럴(oracle (a))로, 파일 판정은
      이 파일의 `decide_run` 이 계약 문안대로 다시 계산한다.
    - (c) 기본 시간 상한 = oracle_config.json stability_transient.wall_s_per_window × 창 수, `--timeout-s` 우선.
    - (d) `.stab.cir`/`.stab2.cir` 의 save = H 식 피연산자 + time.
  * U6 개정(설계 40 §4 C10 2~7, 사용자 결정 4·Q10 2026-10-08, _drafts/user_decisions.md):
    - 결정 4 '폐루프 지속 진동은 불안정(한계 사이클)': 이 파일의 `limit_window` 가 설계 40 §4 2·8 의 조건
      (M_j(1−r) > floor', g↓(M_{j−1}, M_j) 아님; j >= 3 에서 창 j−1, j 연속 -- 8 이 2 의 '분해능 안 일정'을 대체)을 그대로
      구현해 `decide_run` 의 조기 판정에 넣는다(계약 d56ba66 L42-54 '일정 진폭 = undetermined' 를 설계 40 §4 3 이 대체).
    - Q10 '최종 판정 = Nyquist Z = N + P(.pz 독립 측정)·폐루프 과도, 둘 다 불가일 때만 INCOMPLETE' + 설계 40 §4 4
      '폐루프 과도 unstable 이면 FAIL'(pm 제약 유무와 무관): 이 파일의 `expected_judgement` 가 README 절차 8 의 표를
      독립 구현한다(P 는 오라클 기록 `pz_P`·`pz_validated` 를 입력으로 받고, 독립 .pz 가 있는 fixture 는 `independent_pz` 로
      그 P 자체를 따로 대조한다).
    - 설계 40 §4 6 'N 은 π/2 를 넘는 구간을 이분해 다시 .ac(상한 K_max)': 희박 스윕 fixture 의 N 은 이제 세어진다(밀한 독립
      스윕의 N 과 같아야 한다).
    - 설계 40 §4 C10 8(사용자 결정 2026-10-09, master a1775e1): 한계 사이클 = '감쇠하지 않음'(최근 두 창이 앞 창보다 분해능 이상
      줄지 않음, 출렁이는 rb1e6형 포함 -- `flat` 이 이 정의), `.pz` 신뢰 규칙 채택(`expected_p_eff`), 자극·관측 = 루프 끊는 점
      (test_stab_kick_and_observation_at_loop_break).
"""
import importlib
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pytest

import conftest
from conftest import (CS, FB, NFET, NGSPICE, _includes, ac_grid, by_name, cs_input, fb_input, fb_loop_gain,
                      independent_cs, independent_fb, make_lut, measure, preds_from_independent, probe, rc_input,
                      run_oracle, run_spice, stem_of, zero_diffusion)

SAT = 0.05
KB_OVER_Q = 1.380649e-23 / 1.602176634e-19        # 정의값(SI 2019)
TEMP_K = 27.0 + 273.15                             # make_lut 기본 temp_c
RELTOL, VNTOL = 1e-4, 1e-7                         # conftest.testbench_block 의 options
VOCAB = {"open_loop_rhp_poles", "closed_loop_unstable", "stability_evidence_inconsistent", "nyquist_count_unavailable",
         "stability_unverified"}


# ====================================================================== 독립 계산(README 절차의 독립 구현)
def nyquist(L):
    """README 절차 2: 닫힌 곡선 = conj(L[n-1..0]) + 직선 + L[0..n-1] + 직선(-> conj(L[n-1])).
    N = -(1+L 편각 변화 합)/2π, 표본 사이 변화는 (-π, π] 로 접음. 유효 조건 (a)|L(f_last)| < 1, (b) 모든 간격 < 90 deg,
    (c) L = -1 표본 없음. -> {N(유효하지 않으면 None), N_raw, max_step_deg, step_index, valid_a, valid_b, valid_c}."""
    L = np.asarray(L, dtype=complex)
    z = 1 + np.concatenate([np.conj(L[::-1]), L, [np.conj(L[-1])]])
    d = np.angle(z[1:] / z[:-1])
    n_raw = -d.sum() / (2 * math.pi)
    steps = np.degrees(np.abs(d))
    va = abs(L[-1]) < 1
    vb = bool(steps.max() < 90.0)
    vc = not np.any(L == -1)
    return {"N": int(round(n_raw)) if (va and vb and vc) else None, "N_raw": n_raw, "max_step_deg": float(steps.max()),
            "valid_a": va, "valid_b": vb, "valid_c": vc}


def gain_crossings(f, L):
    """|L| = 1 교차 전부(위·아래), log f 대 dB 선형 보간."""
    db = 20 * np.log10(np.abs(L))
    out = []
    for i in range(len(f) - 1):
        if (db[i] >= 0) != (db[i + 1] >= 0):
            t = db[i] / (db[i] - db[i + 1])
            out.append(10 ** (math.log10(f[i]) + t * (math.log10(f[i + 1]) - math.log10(f[i]))))
    return out


def n_pp_by_scan(reltol):
    """계약 1(a) n_pp 의 정의(정현파를 주기당 n 표본으로 볼 때 봉우리를 놓치는 최대 상대 오차 1 − cos(π/n) 가 reltol
    이하인 최소 n)를 폐형식 ceil(π/arccos(1 − reltol)) 대신 n = 1, 2, ... 전수 탐색으로 찾는다(oracle (b))."""
    n = 1
    while 1.0 - math.cos(math.pi / n) > reltol:
        n += 1
    return n


def band_f_crit(f, L):
    """계약 1(a) d56ba66: f_crit = 불안정 관련 대역 안 |1+L| 최소 표본의 주파수. 대역 = 스윕 첫 표본부터 가장 높은 |L|=1
    교차(f_hi)를 지난 첫 표본까지(교차는 |L| 이 표본 사이에서 1 을 지나는 곳 -- 그 위쪽 표본이 대역 끝)."""
    a = np.abs(np.asarray(L))
    above = a >= 1
    last = max(i for i in range(len(a) - 1) if above[i] != above[i + 1]) + 1     # 가장 높은 교차 위쪽 표본
    band = np.abs(1 + np.asarray(L[:last + 1]))
    return float(f[int(np.argmin(band))])


def plan(f, L, vop_outputs, reltol=RELTOL):
    """README 절차 4(조정 상수 없음, 4ab6d85 개정) + 조기 종결 계약 1(a)(사용자 결정 B 2026-10-08):
    펄스 시간 척도는 f_lo(가장 낮은 |L|=1 교차 = PM 교차) 하나: td = tr = tf = pw = 1/(2π f_lo), t_end = td + tr + pw + tf,
    W = 1/f_lo. 걸음 상한 tmax = min(1/(2π f_lo), 1/(f_crit·n_pp)), f_crit = |1+L| 최소 표본 주파수.
    f_hi 는 기록만(계획에 쓰지 않음). reltol = 입력 testbench.options(없으면 ngspice 기본 1e-3)."""
    cr = gain_crossings(f, L)
    f_lo, f_hi = min(cr), max(cr)
    kick = KB_OVER_Q * TEMP_K
    td = 1 / (2 * math.pi * f_lo)
    f_crit = band_f_crit(f, L)
    n_pp = n_pp_by_scan(reltol)
    tmax = min(td, 1 / (f_crit * n_pp))
    pw = td
    t_end = 4 * td
    w = 1 / f_lo
    floor = sum(reltol * abs(v) + VNTOL for v in vop_outputs)
    k = math.ceil(math.log(kick / floor))
    return {"f_lo": f_lo, "f_hi": f_hi, "kick": kick, "td": td, "tmax": tmax, "pw": pw, "t_end": t_end, "W": w,
            "floor": floor, "K": k, "tstop": t_end + k * w, "crossings": cr, "f_crit": f_crit, "n_pp": n_pp,
            "reltol": reltol}


ORACLE_CONFIG = conftest.ORACLE_DIR / "oracle_config.json"


def wall_s_per_window():
    """계약 1(c): 설정 파일이 선언한 창 하나의 ngspice 실행 시간 상한(s)."""
    cfg = json.loads(ORACLE_CONFIG.read_text(encoding="utf-8"))
    return cfg["stability_transient"]["wall_s_per_window"]


def check_plan_record(rec, pl, sign):
    """ac.stability.transient.plan 이 독립 계획과 같은지(필드 전부). floor 는 V_op 출처(독립 .op 대 동작점 패스)만 달라
    상대 1e-4, 나머지는 같은 식이라 1e-9. 계약 1(a)(c) 새 필드: f_crit_hz·n_pp·reltol·windows_planned·wall_cap_s."""
    exact = {"kick_V": pl["kick"], "td": pl["td"], "tr": pl["td"], "pw": pl["pw"], "tmax": pl["tmax"],
             "window_s": pl["W"], "t_kick_end": pl["t_end"], "f_lo_hz": pl["f_lo"], "f_hi_hz": pl["f_hi"],
             "f_crit_hz": pl["f_crit"], "reltol": pl["reltol"]}
    for k, v in exact.items():
        assert rec[k] == pytest.approx(v, rel=1e-9), (k, rec[k], v)
    assert rec["windows"] == pl["K"], (rec["windows"], pl["K"])
    assert rec["windows_planned"] == pl["K"], (rec["windows_planned"], pl["K"])
    assert rec["n_pp"] == pl["n_pp"], (rec["n_pp"], pl["n_pp"])
    # oracle (d) 계약 1(c): 계획 상한 = 선언된 창당 상한 × 계획 창 수(첫 실행 계획이라 연장 창 수 0)
    assert rec["wall_cap_s"] == pytest.approx(wall_s_per_window() * pl["K"], rel=1e-9), rec["wall_cap_s"]
    assert rec["floor_V"] == pytest.approx(pl["floor"], rel=1e-4)
    assert rec["tstop"] == pytest.approx(pl["tstop"], rel=1e-6)
    assert rec["sign"] == sign


def check_early_consistent(tr, dec, pl):
    """계약 1(b): 오라클의 조기 종결 기록 = 데이터 파일에서 다시 센 조기 창(없으면 None), windows_run = 그 창 또는 K."""
    es = tr.get("early_stop")
    assert (es["window"] if es else None) == dec["early"], (es, dec["early"], dec["M"])
    kinds = dec["early_kind"] or frozenset()
    assert (es.get("kind") if es else None) in (kinds or {None}), (es, kinds, dec["M"])
    assert tr["windows_run"] == (dec["early"] or pl["K"]), (tr["windows_run"], dec["early"], pl["K"])
    # 설계 40 §4 C10 2: 한계 사이클 FAIL 에는 고Q 감쇠와 구별 못 함 표시(limit_cycle_vs_slow_decay_unresolved)가 붙는다
    if es:
        assert (tr.get("limit_cycle_vs_slow_decay_unresolved") is not None) == (es.get("kind") == "limit_cycle"), tr
    assert es or tr.get("limit_cycle_vs_slow_decay_unresolved") is None, tr


_STABWIN_RE = re.compile(r"^\s*STABWIN\s+(\d+)\s+([-+0-9.eE]+)\s*$", re.M)


def check_stabwin_log(log: Path, m):
    """계약 1(b): 창이 끝날 때마다 로그에 `STABWIN j M_j` 한 줄 -- j = 1..(실행한 창 수), M_j = 데이터 파일에서 다시 센 값."""
    rows = [(int(a), float(b)) for a, b in _STABWIN_RE.findall(log.read_text(encoding="utf-8", errors="replace"))]
    assert [j for j, _ in rows] == list(range(1, len(m) + 1)), rows
    assert [v for _, v in rows] == pytest.approx(m, rel=1e-2), (rows, m)


def check_full_run(tr, pl, dec):
    """계약 1(b): 조기 기준을 한 번도 충족하지 않은 실행(안정·감쇠·일정 진폭) -- early_stop 없음, K 창 끝까지,
    적용된 시간 상한 = 계획 상한(`--timeout-s` 없음). 독립 재계산(dec)도 조기 창이 없어야 한다(전제)."""
    assert dec["early"] is None, dec
    assert tr.get("early_stop") is None, tr.get("early_stop")
    assert tr["windows_run"] == pl["K"] == tr["plan"]["windows_planned"], (tr["windows_run"], pl["K"])
    assert tr["wall_cap_s"] == pytest.approx(tr["plan"]["wall_cap_s"], rel=1e-12), tr["wall_cap_s"]


_PROBE_RE = re.compile(r"[vi]\([^()]*\)")


def save_vectors(text: str):
    """넷리스트의 save 문(`.save` 카드 또는 .control 안 `save`)이 저장하는 벡터 이름(소문자, 공백 제거)."""
    out = []
    for ln in text.splitlines():
        t = ln.split(None, 1)
        if t and t[0].lower() in ("save", ".save") and len(t) > 1:
            out += [m.replace(" ", "") for m in _PROBE_RE.findall(t[1].lower())]
            out += [w for w in re.sub(r"[vi]\([^()]*\)", " ", t[1].lower()).split()]
    return out


def hst_operands(text: str):
    """`let hst = <H 식>` 의 피연산자(v(..)/i(..), 소문자, 공백 제거)."""
    for ln in text.splitlines():
        m = re.match(r"\s*let\s+hst\s*=\s*(.*)$", ln, re.I)
        if m:
            return {x.replace(" ", "") for x in _PROBE_RE.findall(m.group(1).lower())}
    return None


def check_save_probes_only(text: str):
    """계약 1(d): save 는 H 식 피연산자와 time 만(전체 저장 아님)."""
    ops = hst_operands(text)
    sv = save_vectors(text)
    assert ops, "let hst 식에서 피연산자를 찾지 못함 -- 조건 점검"
    assert sv, "save 문 없음"
    assert set(sv) - {"time"} == ops, (sv, ops)
    assert "all" not in sv, sv


def mantissa_digits(path: Path) -> int:
    """파일 실수들의 가수 유효숫자(찍힌 가수 자릿수, 전체 최솟값) -- README C20 data_rel_resolution 의 d."""
    d = None
    for tok in path.read_text(encoding="utf-8").split():
        m = re.fullmatch(r"[-+]?(\d+)\.?(\d*)[eE][-+]?\d+", tok)
        if m:
            n = len(m.group(1) + m.group(2))
            d = n if d is None else min(d, n)
    return d


def g_up(a, b, fl, reltol):
    """계약 1(b) d56ba66: b 가 a 보다 측정 분해능을 넘게 큼 -- b(1 − reltol) > a(1 + reltol) + floor'."""
    return b * (1 - reltol) > a * (1 + reltol) + fl


def g_down(a, b, fl, reltol):
    """계약 1(b) d56ba66: b 가 a 보다 측정 분해능을 넘게 작음 -- a(1 − reltol) > b(1 + reltol) + floor'."""
    return a * (1 - reltol) > b * (1 + reltol) + fl


def growth_window(m, fl, reltol):
    """계약 1(b) 조기 unstable 기준(계약 문안의 독립 구현): j >= 3 인 첫 창에서 g↑(M_{j−2}, M_{j−1}) 그리고
    g↑(M_{j−1}, M_j) 그리고 g↑(M_1, M_j) 이면 그 j(1 부터), 없으면 None."""
    for j in range(3, len(m) + 1):
        if g_up(m[j - 3], m[j - 2], fl, reltol) and g_up(m[j - 2], m[j - 1], fl, reltol) and g_up(m[0], m[j - 1], fl,
                                                                                                    reltol):
            return j
    return None


def flat(a, b, fl, reltol):
    """설계 40 §4 C10 8 '한계 사이클 = 감쇠하지 않음'(사용자 결정 2026-10-09, 2 의 '분해능 안에서 일정'을 대체): 창 b 가
    앞 창 a 보다 분해능 이상 줄지 않았다(g↓(a, b) 아님) -- 출렁이는 지속 진동(rb1e6형)·증가도 포함. 바닥 조건(2 의 첫 항,
    대체되지 않음): b(1 − r) > floor' -- 해 분해능 바닥에 붙은(감쇠를 끝낸) 안정 회로의 창은 진동이 아니다."""
    return b * (1 - reltol) > fl and not g_down(a, b, fl, reltol)


def limit_window(m, fl, reltol):
    """설계 40 §4 C10 2·8: j >= 3 인 첫 창에서 최근 두 창(j−1, j)이 둘 다 '감쇠하지 않음'(flat(M_{j−2}, M_{j−1}),
    flat(M_{j−1}, M_j))이면 그 j(1 부터), 없으면 None."""
    for j in range(3, len(m) + 1):
        if flat(m[j - 3], m[j - 2], fl, reltol) and flat(m[j - 2], m[j - 1], fl, reltol):
            return j
    return None


def early_window(m, fl, reltol):
    """조기 종결 창 (j, 종류 집합) -- 'growth'(계약 1(b)) | 'limit_cycle'(설계 40 §4 C10 2·8) 중 먼저 오는 창, 없으면 (None, None).
    §4 C10 8 이후 성장(g↑ 연속)도 '감쇠하지 않음'이라 같은 j 에서 둘이 함께 성립할 수 있다 -- 그때 종류 이름은 설계가 정하지
    않았으므로 둘 다 허용(집합)."""
    cands = [(j, k) for j, k in ((growth_window(m, fl, reltol), "growth"), (limit_window(m, fl, reltol), "limit_cycle"))
             if j is not None]
    if not cands:
        return None, None
    j0 = min(j for j, _ in cands)
    return j0, frozenset(k for j, k in cands if j == j0)


def decide_run(stab_txt: Path, p):
    """README 절차 5 의 한 실행 판정(3fdabd7 개정) + 조기 종결 계약 1(b): e = H - H(0), 창 j 의 M_j = max|e|(끝까지 닿은
    창만), floor' = floor + u·max|H|. 끝난 창들에서 조기 기준을 충족하는 첫 창 j 가 있으면 unstable(early = j, M = M_1..M_j).
    아니고 마지막 시각이 tstop·(1 − 2u) 보다 이르면 failed. 그 밖(분해능 인식형, d56ba66) M_K <= floor' -> stable;
    g↑(M_1, M_K) -> unstable; 모든 연속 창 g↓(M_{j−1}, M_j) -> decaying; 그 밖(분해능 안의 같음 포함) -> undetermined.
    연장 실행에도 같은 규칙."""
    a = np.loadtxt(stab_txt)
    t, h = a[:, 0], a[:, 1]
    u = 0.5 * 10.0 ** (1 - mantissa_digits(stab_txt))
    e = np.abs(h - h[0])
    m = []
    for j in range(p["K"]):
        lo, hi = p["t_end"] + j * p["W"], p["t_end"] + (j + 1) * p["W"]
        if t[-1] < hi * (1 - 2 * u):
            break                                    # 창 j+1 끝까지 가지 않음(잘린 파일)
        sel = (t >= lo) & (t <= hi)
        m.append(float(e[sel].max()) if sel.any() else float("nan"))
    fl = p["floor"] + u * float(np.abs(h).max())
    r = p.get("reltol", RELTOL)
    early, kind = early_window(m, fl, r)
    if early is not None:
        return {"status": "unstable", "M": m[:early], "floor2": fl, "early": early, "early_kind": kind,
                "t_last": float(t[-1])}
    if t[-1] < p["tstop"] * (1 - 2 * u):
        st = "failed"
    elif m[-1] <= fl:
        st = "stable"
    elif g_up(m[0], m[-1], fl, r):
        st = "unstable"
    elif all(g_down(m[j], m[j + 1], fl, r) for j in range(len(m) - 1)):
        st = "decaying"
    else:
        st = "undetermined"
    return {"status": st, "M": m, "floor2": fl, "early": None, "early_kind": None, "t_last": float(t[-1])}


def extension_plan(p, first):
    """README 절차 5: decaying 이면 r = M_K/M_{K-1}, n = ceil(ln(floor'/M_K)/ln r), 창 K + n, tstop = t_end + (K + n)·W."""
    m = first["M"]
    r = m[-1] / m[-2]
    n = math.ceil(math.log(first["floor2"] / m[-1]) / math.log(r))
    return n, dict(p, K=p["K"] + n, tstop=p["t_end"] + (p["K"] + n) * p["W"])


def decide(stab_txt: Path, p):
    """절차 5 전체: 첫 실행(.stab.txt) 판정, decaying 이면 연장 실행(.stab2.txt)을 같은 규칙으로 판정해 최종 상태.
    반환 status = 최종, first = 첫 실행 상태, M·floor2 = 첫 실행 값, ext = 연장 판정(+ n, plan) 또는 None."""
    first = decide_run(stab_txt, p)
    out = {"status": first["status"], "first": first["status"], "M": first["M"], "floor2": first["floor2"],
           "ext": None, "early": first["early"], "early_kind": first["early_kind"], "t_last": first["t_last"]}
    if first["status"] != "decaying":
        return out
    n, p2 = extension_plan(p, first)
    ext = decide_run(Path(str(stab_txt).replace(".stab.txt", ".stab2.txt")), p2)
    ext.update(n=n, plan=p2)
    out["ext"] = ext
    out["status"] = {"stable": "stable", "decaying": "stable", "unstable": "unstable"}.get(ext["status"],
                                                                                         "undetermined")
    return out


def expected_row(s, n, pm_raw):
    """README 절차 6 표 -> (closed_loop, open_loop_rhp_poles, bound 접두, pm_undefined)."""
    known = s if s in ("stable", "unstable") else None
    if known == "stable":
        if n == 0:
            return "stable", 0, "==", None
        if n is not None and n < 0:
            return "stable", -n, "==", "open_loop_rhp_poles"
        if n is not None and n > 0:
            return "stable", None, None, "stability_evidence_inconsistent"
        return "stable", None, None, "nyquist_count_unavailable"
    if known == "unstable":
        if n is not None and n <= 0:
            return "unstable", 1 - n, ">=", "open_loop_rhp_poles"
        if n is not None and n >= 1:
            return ("unstable", 0, "==", None) if pm_raw < 0 else ("unstable", None, None,
                                                                   "stability_evidence_inconsistent")
        return "unstable", None, None, "closed_loop_unstable"
    if n is not None and n >= 1:
        return ("unstable", 0, "==", None) if pm_raw < 0 else ("unstable", None, None, "stability_evidence_inconsistent")
    if n is not None and n < 0:
        return None, -n, ">=", "open_loop_rhp_poles"
    return None, None, None, "stability_unverified"


def expected_p_eff(status, n, pz_p, pz_validated):
    """README 절차 7·8 의 `.pz` 신뢰 규칙(독립 구현) -> PM 유효성에 쓰는 P(정수) 또는 None(모름 -> 옛 표 expected_row).
    (d) 폐루프 과도 stable 이면 Z = 0 이라 P = −N(Nyquist); 폐루프 과도 unstable 이면 `.pz` 의 P(이름 붙이기용);
    (e) 그 밖(undetermined·failed)이면 `.pz` 의 P >= 1 은 개루프 과도 확인(pz_validated is True)일 때만, P = 0 은 그대로."""
    if status == "stable":
        return None if n is None else -n
    if status == "unstable":
        return pz_p
    if pz_p is not None and (pz_p == 0 or pz_validated is True):
        return pz_p
    return None


def expected_judgement(status, n, pz_p, pz_validated, pm_raw):
    """최종 안정성 판정(설계 40 §4 C10 4·7, 사용자 결정 Q10·4, README 절차 8 표의 독립 구현) -> dict(verdict, P_eff, Z, pm_undefined).
    verdict: 과도 unstable 또는 N >= 1(P >= 0 이라 Z >= 1) 또는 Z = N + P_eff >= 1 -> unstable; 과도 stable -> stable; 그 밖 undetermined.
    PM: P_eff 를 모르면 옛 표(expected_row). P_eff = 0: stable -> 값, unstable -> N >= 1 & pm_raw < 0 만 값(그 밖 inconsistent),
    undetermined -> stability_unverified. P_eff >= 1: Z = 0 이고 stable -> 조건부 안정(값), 그 밖 open_loop_rhp_poles. Z < 0 -> inconsistent."""
    p_eff = expected_p_eff(status, n, pz_p, pz_validated)
    z = None if (p_eff is None or n is None) else n + p_eff
    if status == "unstable" or (n is not None and n >= 1) or (z is not None and z >= 1):
        verdict = "unstable"
    elif status == "stable":
        verdict = "stable"
    else:
        verdict = "undetermined"
    if p_eff is None or z is None:
        und = expected_row(status, n, pm_raw)[3]
    elif z < 0:
        und = "stability_evidence_inconsistent"
    elif p_eff == 0:
        und = {"stable": None, "undetermined": "stability_unverified"}.get(
            verdict, None if (n >= 1 and pm_raw < 0) else "stability_evidence_inconsistent")
    else:
        und = None if (z == 0 and verdict == "stable") else "open_loop_rhp_poles"
    return {"verdict": verdict, "P_eff": p_eff, "Z": z, "pm_undefined": und}


def independent_pz(body_lines, out_node, workdir: Path):
    """독립 `.pz`(oracle (c), 손으로 쓴 개루프 넷리스트: 입력 이상 전압원 고정, 출력 노드 전류 포트) -> 극점 목록(복소수)."""
    lines = _head() + list(body_lines) + [".control", "set noaskquit", "op", f"pz {out_node} 0 {out_node} 0 cur pol",
                                          "print all", "quit", ".endc", ".end"]
    p, _ = _ngspice(lines, workdir, name="pz.cir")
    poles = [complex(float(a), float(b)) for a, b in
             re.findall(r"pole\(\d+\)\s*=\s*([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)", p.stdout)]
    assert poles, (p.stdout + p.stderr)[-1500:]
    return poles


def rhp_count_in_sweep(poles, f_stop_hz):
    """실수부 > 0 이고 크기가 .ac 스윕 상한(2π f_stop) 안인 극의 수(독립 .pz 대조용, 설계 40 §4 C10 6 'P = 실수부 > 0 인 극점 수')."""
    return sum(1 for q in poles if q.real > 0 and abs(q) <= 2 * math.pi * f_stop_hz)


def ac_loop_from_files(odir: Path, stem: str, beta_loop: bool):
    """오라클이 쓴 AC 데이터 파일 -> (f, L, A 또는 T). β=1: L = sign·A (sign = Re A(fstart) 부호, 입력 가중 1).
    β 루프(끊은 넷 1개, 가중 1): Tv = -V(lbx)/V(n), Ti = I_x/(1 - I_x), T = (Tv·Ti - 1)/(Tv + Ti + 2)."""
    if not beta_loop:
        a = np.loadtxt(odir / f"{stem}.ac.txt")
        f, A = a[:, 0], a[:, 1] + 1j * a[:, 2]
        return f, np.sign(A[0].real) * A, A
    v = np.loadtxt(odir / f"{stem}.loop.v.txt")
    i = np.loadtxt(odir / f"{stem}.loop.i.txt")
    f = v[:, 0]
    vlbx, vn = v[:, 1] + 1j * v[:, 2], v[:, 3] + 1j * v[:, 4]
    ix = i[:, 1] + 1j * i[:, 2]
    tv = -vlbx / vn
    ti = ix / (1 - ix)
    T = (tv * ti - 1) / (tv + ti + 2)
    return f, T, T


def pulse_of(text: str, name: str):
    for ln in text.splitlines():
        if ln.split() and ln.split()[0].lower() == name.lower():
            m = re.search(r"PULSE\(([^)]*)\)", ln, re.I)
            return [float(x) for x in m.group(1).split()], ln.split()
    return None, None


def tran_line(text: str):
    for ln in text.splitlines():
        t = ln.split()
        if t and t[0].lower() == "tran":
            return [float(x) for x in t[1:]]
    return None


NGSPICE_TIMEOUT_S = 600                # 독립 ngspice 한 번의 기본 시간 한도


def _ngspice(lines, workdir: Path, name="r.cir", timeout=NGSPICE_TIMEOUT_S):
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    timed_out = None
    try:
        p = subprocess.run([str(NGSPICE), "-b", name], capture_output=True, text=True, cwd=str(workdir),
                           encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as e:
        timed_out = e.stdout[-300:] if isinstance(e.stdout, str) else (e.stdout or b"")[-300:]
    if timed_out is not None:
        # 시간 초과는 독립 기준 실행의 실패다(판정 결과가 아님) -- 예외 추적 대신 원인을 밝혀 실패시킨다.
        pytest.fail(f"독립 ngspice 실행이 {timeout} s 안에 끝나지 않음: {workdir / name} (stdout 끝: {timed_out!r})")
    vals = {}
    for ln in p.stdout.splitlines():
        if " = " in ln:
            k, v = ln.split(" = ", 1)
            try:
                vals[k.strip().lower()] = float(v.split()[0])
            except ValueError:
                pass
    return p, vals


HEAD = ["* independent C10 reference", None, ".temp 27.0", ".option gmin=1e-15 reltol=1e-4 abstol=1e-14 vntol=1e-7"]


def _head():
    h = list(HEAD)
    h[1] = _includes("tt")
    return h


# ====================================================================== 회로 1: 개루프 RHP 극(DC 를 막은 양되먹임)
RHP = dict(vdd=1.8, vb=0.7, vin=0.7, r1=51764.70588, r2=129400.0, cc=1e-12, L=0.5e-6, fw=2e-6, n1f=1, n2f=2, n3f=4)
RB = {"rb1e5": 1e5, "rb1e6": 1e6, "rb1e7": 1e7}


def rhp_body(rb, vin_line=None):
    c = RHP
    b = [f"Vdd vdd 0 DC {c['vdd']}", f"Vb vb 0 DC {c['vb']}", vin_line or f"Vin nin 0 DC {c['vin']} AC 1",
         f"R1 vdd n1 {c['r1']}", f"R2 vdd n2 {c['r2']}", f"Rb vb n3 {rb}", f"Cc n2 n3 {c['cc']}"]
    for nm, d, g, n in (("M1", "n1", "nin", c["n1f"]), ("M2", "n2", "n1", c["n2f"]), ("M3", "n1", "n3", c["n3f"])):
        b += [f"X{nm}_{k} {d} {g} 0 0 {NFET} l={c['L']} w={c['fw']}" for k in range(n)]
    return b


def rhp_input(lut, rb, constraints=None, metrics=None, nodes=None):
    c = RHP

    def dev(name, d, g, n):
        return {"name": name, "kind": "nmos", "drain": d, "gate": g, "source": "gnd", "bulk": "gnd",
                "L": c["L"], "finger_w": c["fw"], "n_fingers": n, "W": c["fw"] * n}

    inp = {"schema": "spice_oracle_input/1", "circuit": "trhp_posfb",
           "process": conftest.process_block(lut),
           "rails": [{"net": "vdd", "voltage": c["vdd"]}, {"net": "vb", "voltage": c["vb"]},
                     {"net": "gnd", "voltage": 0.0, "reference": True}],
           "devices": [dev("M1", "n1", "nin", c["n1f"]), dev("M2", "n2", "n1", c["n2f"]),
                       dev("M3", "n1", "n3", c["n3f"])],
           "sources": [],
           "passives": [{"name": "R1", "kind": "resistor", "terminals": ["vdd", "n1"], "value": c["r1"]},
                        {"name": "R2", "kind": "resistor", "terminals": ["vdd", "n2"], "value": c["r2"]},
                        {"name": "Rb", "kind": "resistor", "terminals": ["vb", "n3"], "value": rb},
                        {"name": "Cc", "kind": "capacitor", "terminals": ["n2", "n3"], "value": c["cc"]}],
           "ports": {"input": "nin", "output": "n2"},
           "predictions": {"nodes": {"nin": c["vin"], **(nodes or {})},
                           "devices": {k: {"off_current_A": 0.0} for k in ("M1", "M2", "M3")},
                           "metrics": metrics or []},
           "testbench": conftest.testbench_block()}
    if constraints is not None:
        inp["acceptance"] = {"constraints": constraints}
    return zero_diffusion(inp)


_RHP_REF = {}


def rhp_ref(root: Path, rb):
    """독립 .op + .ac(입력 이상 전압원 AC 1) -> gm·gds, 손 모형 K·A0·p, 측정 정의 값, N."""
    if rb in _RHP_REF:
        return _RHP_REF[rb]
    pr = ["v(n1)", "v(n2)", "v(n3)"]
    for nm, n in (("xm1", RHP["n1f"]), ("xm2", RHP["n2f"]), ("xm3", RHP["n3f"])):
        pr += [probe("nmos", f"{nm}_{k}", q) for k in range(n) for q in ("gm", "gds", "vds", "vdsat")]
    r = run_spice("\n".join(rhp_body(rb)), root / f"rhp_{rb:g}", pr, ac_out="n2", ac=(0.01, 1e10, 40))
    op = r["op"]
    g = {nm: {q: sum(op[probe("nmos", f"{nm}_{k}", q).lower()] for k in range(n)) for q in ("gm", "gds")}
         for nm, n in (("xm1", RHP["n1f"]), ("xm2", RHP["n2f"]), ("xm3", RHP["n3f"]))}
    sat = min(op[probe("nmos", f"{nm}_0", "vds").lower()] - op[probe("nmos", f"{nm}_0", "vdsat").lower()]
              for nm in ("xm1", "xm2", "xm3"))
    g1 = 1 / RHP["r1"] + g["xm1"]["gds"] + g["xm3"]["gds"]
    g2 = 1 / RHP["r2"] + g["xm2"]["gds"]
    K = g["xm2"]["gm"] * g["xm3"]["gm"] / (g1 * g2)
    A0 = g["xm1"]["gm"] * g["xm2"]["gm"] / (g1 * g2)
    H = r["H"]
    out = {"op": op, "K": K, "A0": A0, "p_hand": 1 / (rb * RHP["cc"] * (K - 1)), "sat_min": sat, "f": r["f"], "H": H,
           "meas": measure(r["f"], H), "nyq": nyquist(np.sign(H[0].real) * H),
           "nodes": {"n1": op["v(n1)"], "n2": op["v(n2)"], "n3": op["v(n3)"]}}
    _RHP_REF[rb] = out
    return out


RHP_KICK = dict(dv=0.01, delay=1e-6, rise=1e-8, width=1e-6, fall=1e-8)   # 폐루프 킥(PULSE) -- 아래 창 계산과 공유
TMAX_PER_TAU = 20                     # τ 지수 회복을 τ 당 20 점 이상으로 따라간다(빠른 근 구간은 ngspice 오차 제어가 더 줄인다)
# 폐루프 .tran 비용 모형: 반복 횟수는 낮은 상태의 빠른 근 진동 길이(~τ = Rb·Cc)에 비례하고, 창(tstop)도 τ 의 배수라
# 같은 주기 수를 도는 실행의 비용은 Rb 에 비례한다. 기준 실측(2026-10-08, 다른 ngspice ~5개 동시 실행 부하):
# Rb 1e6, 이 창(tstop = 킥 끝 + 2T = 23.2 µs) -> 벽시계 298 s, 반복 317,345 회. 확인: Rb 1e7 한 주기(tstop 108 µs) ->
# 반복 1,056,754 회(Rb 1e6 의 두 주기 반복 x 10 / 2 = 1.59e6 이하로 비례 모형 안), 645 s.
CL_COST_REF = dict(rb=1e6, wall_s=298.0)
# 안전 계수 3: 같은 Rb 1e6 실행이 부하에 따라 114 s(pytest)~298 s(scratch) 로 2.6 배 흔들렸다 -> 그보다 큰 3.
CL_TIMEOUT_SAFETY = 3.0


def rhp_closed_loop_cost_s(rb):
    """비용 모형의 예측 벽시계(s) -- 기준 실측 x Rb 비."""
    return CL_COST_REF["wall_s"] * rb / CL_COST_REF["rb"]


def rhp_closed_loop_timeout_s(rb):
    """폐루프 .tran 한 번의 시간 한도: 예측 x 안전 계수, 기본 한도보다 작아지지 않는다."""
    return max(NGSPICE_TIMEOUT_S, CL_TIMEOUT_SAFETY * rhp_closed_loop_cost_s(rb))


def rhp_closed_loop_window(rb, K):
    """폐루프 .tran 의 (tstop, last, tmax) 를 이 회로 자신의 τ = Rb·Cc 와 손 모형 K(rhp_ref, 독립 .op)로 유도한다.

    폐루프 파형(독립 실행 2026-10-08)은 이완 발진이다: 높은 상태(M2 꺼짐, V(n2) ~ VDD)와 낮은 상태를 오가며, 전환
    때 Cc 로 n3 에 실린 n2 스윙이 Rb 를 거쳐 τ = Rb·Cc 로 vb(= .op 의 V(n3); Rb 에는 DC 전류가 없다) 쪽으로 회복하다가,
    남은 차이가 내부 양되먹임 루프가 선형(루프 이득 K)으로 동작하는 폭 ~ (n2 스윙)/K 안에 들어오면 빠른 RHP 근
    (~6e9 rad/s, test_rhp_fixture_has_open_loop_rhp_pole)으로 재생 전환한다. 그래서 반주기 ~ τ·ln(스윙 / (스윙/K))
    = τ·ln K, 주기 상한 T = 2τ·ln K (K ~ 197 -> 10.6τ; 실측 주기 Rb 1e5: 9.3τ, Rb 1e6: 6.6τ -- 상한 안).
      * tstop = 킥 끝(지연+상승+폭+하강) + 2T: 앞 T 는 킥 응답이 빠지는 구간(안정 계라면 가장 느린 시간상수 τ 의
        ln K 배 넘게 지나 감쇠한다), 뒤 T 가 판정 창 `last` -- 주기 상한이라 지속 이완 발진이면 창 안에 최대·최소가
        다 든다(창이 한 주기보다 짧으면 정지한 높은 상태만 볼 수 있다).
      * tmax = τ / TMAX_PER_TAU.
    계산 비용은 낮은 상태 앞부분의 빠른 근 진동 길이(~τ)에 비례해 Rb 에 비례한다(고정 tstop 300 µs 는 Rb 1e5·1e6 에서
    600 s 초과, Rb 1e7 에서 메모리 부족이었다)."""
    tau = rb * RHP["cc"]
    period = 2.0 * tau * math.log(K)
    k = RHP_KICK
    kick_end = k["delay"] + k["rise"] + k["width"] + k["fall"]
    return kick_end + 2.0 * period, period, tau / TMAX_PER_TAU


def rhp_closed_loop_pp(root: Path, rb, v2op, K):
    """독립 폐루프 .tran: nin = (0.7 + V2op + 킥) - V(n2) (이상 VCVS 단위 음되먹임, A(0) > 0).
    마지막 `last` 구간의 V(n2) 최대-최소. 창은 `rhp_closed_loop_window`."""
    tstop, last, tmax = rhp_closed_loop_window(rb, K)
    v0 = RHP["vin"] + v2op
    k = RHP_KICK
    body = rhp_body(rb, vin_line=f"Ecl nin cl n2 0 -1")
    body.append(f"Vcl cl 0 DC {v0} PULSE({v0} {v0 + k['dv']} {k['delay']} {k['rise']} {k['fall']} {k['width']})")
    body.append(".save v(n2)")                      # 판정에 쓰는 벡터만 저장(전체 저장은 긴 실행에서 메모리 부족)
    ctrl = [".control", "set noaskquit", f"tran {tmax} {tstop} 0 {tmax}",
            f"meas tran vmax MAX v(n2) from={tstop - last} to={tstop}",
            f"meas tran vmin MIN v(n2) from={tstop - last} to={tstop}", "quit", ".endc", ".end"]
    p, vals = _ngspice(_head() + body + ctrl, root / f"rhp_cl_{rb:g}", timeout=rhp_closed_loop_timeout_s(rb))
    assert "vmax" in vals and "vmin" in vals, (p.returncode, p.stdout[-600:], p.stderr[-2000:])
    return vals["vmax"] - vals["vmin"]


# ====================================================================== 회로 2: 3단 CS(고전적 불안정 / 안정 저 PM)
THREE = dict(vdd=1.8, vin=0.7, rl=129409.146, L=0.5e-6, fw=2e-6, n=2)
CAPS = {"classic_unstable": (1e-9, 1e-12, 1e-12), "stable_lowpm": (1e-8, 3e-12, 3e-12)}


def three_body(caps):
    c = THREE
    b = [f"Vdd vdd 0 DC {c['vdd']}", f"Vin nin 0 DC {c['vin']} AC 1"]
    prev = "nin"
    for i, cap in enumerate(caps, 1):
        b += [f"R{i} vdd n{i} {c['rl']}", f"C{i} n{i} 0 {cap}"]
        b += [f"XM{i}_{k} n{i} {prev} 0 0 {NFET} l={c['L']} w={c['fw']}" for k in range(c["n"])]
        prev = f"n{i}"
    return b


def three_input(lut, caps, ppd=40, constraints=None):
    c = THREE
    inp = {"schema": "spice_oracle_input/1", "circuit": "t3stage",
           "process": conftest.process_block(lut),
           "rails": [{"net": "vdd", "voltage": c["vdd"]}, {"net": "gnd", "voltage": 0.0, "reference": True}],
           "devices": [{"name": f"M{i}", "kind": "nmos", "drain": f"n{i}", "gate": g, "source": "gnd", "bulk": "gnd",
                        "L": c["L"], "finger_w": c["fw"], "n_fingers": c["n"], "W": c["fw"] * c["n"]}
                       for i, g in ((1, "nin"), (2, "n1"), (3, "n2"))],
           "sources": [],
           "passives": [{"name": f"R{i}", "kind": "resistor", "terminals": ["vdd", f"n{i}"], "value": c["rl"]}
                        for i in (1, 2, 3)]
           + [{"name": f"C{i}", "kind": "capacitor", "terminals": [f"n{i}", "gnd"], "value": cap}
              for i, cap in enumerate(caps, 1)],
           "ports": {"input": "nin", "output": "n3"},
           "predictions": {"nodes": {"nin": c["vin"]},
                           "devices": {k: {"off_current_A": 0.0} for k in ("M1", "M2", "M3")}, "metrics": []},
           "testbench": conftest.testbench_block()}
    inp["testbench"]["ac"]["points_per_decade"] = ppd
    if constraints is not None:
        inp["acceptance"] = {"constraints": constraints}
    return zero_diffusion(inp)


_THREE_REF = {}


def three_ref(root: Path, caps, ppd=40):
    key = (caps, ppd)
    if key not in _THREE_REF:
        r = run_spice("\n".join(three_body(caps)), root / f"three_{caps[0]:g}_{caps[1]:g}_{ppd}", ["v(n3)"],
                      ac_out="n3", ac=(0.01, 1e10, ppd))
        H = r["H"]
        _THREE_REF[key] = {"f": r["f"], "H": H, "meas": measure(r["f"], H), "nyq": nyquist(np.sign(H[0].real) * H),
                           "v3": r["op"]["v(n3)"]}
    return _THREE_REF[key]


# ====================================================================== 공용
def _sim(odir: Path, inp, bias="free"):
    return json.loads((odir / f"{stem_of(inp, bias)}.sim.json").read_text(encoding="utf-8"))


def _cons(c, name):
    return by_name(c["constraints"], "name", name)


def _perf(c, name):
    return by_name(c["performance"], "name", name)


def pm_con(op, limit, name="pmc"):
    return {"name": name, "measure": "pm_deg", "op": op, "limit": limit}


STAB_KEYS = {"pm_valid", "pm_undefined", "pm_deg_raw", "loop", "closed_loop", "open_loop_rhp_poles",
             "open_loop_rhp_poles_bound", "nyquist_encirclements_cw", "nyquist_reason", "transient_status",
             "transient_reason", "reason"}


def check_row(st, nyq_mine, status, pm_raw):
    """summary.stability 가 (독립 N, 과도 상태, pm_raw, 기록된 .pz P·개루프 과도 확인) 에서 판정 규칙이 정하는 값과 같은지.
    P_eff 를 모르면(README 절차 6) 옛 표 행 전체, 알면(절차 8) P_eff·Z·verdict·pm_undefined."""
    exp = expected_judgement(status, nyq_mine, st.get("pz_P"), st.get("pz_validated"), pm_raw)
    assert st["verdict"] == exp["verdict"], (st, exp)
    if exp["P_eff"] is None:
        cl, p, bound, und = expected_row(status, nyq_mine, pm_raw)
        assert st["closed_loop"] == cl, st
        assert st["open_loop_rhp_poles"] == p, st
        if bound is None:
            assert st["open_loop_rhp_poles_bound"] is None, st
        else:
            assert str(st["open_loop_rhp_poles_bound"]).startswith(bound), st
    else:
        assert st["Z"] == exp["Z"], (st, exp)
        assert st["open_loop_rhp_poles"] == exp["P_eff"], (st, exp)
        assert str(st["open_loop_rhp_poles_bound"]).startswith("=="), st
    assert st["pm_undefined"] == exp["pm_undefined"], (st, exp)
    assert st["pm_valid"] is (exp["pm_undefined"] is None), st


# ====================================================================== 독립 전제(피검 코드 없음)
@pytest.mark.parametrize("rb", list(RB))
def test_rhp_fixture_has_open_loop_rhp_pole(ref_root, rb):
    """전제 확인: 개루프(입력 이상 전압원 고정)를 .op 해에서 출발시키면 V(n2) 가 지수 증가 = 개루프 RHP 극(P >= 1).
    손 모형(MOS 용량 무시) K > 1 이면 내부 양되먹임 루프 K·sτ/(1+sτ)/(극들) = 1 의 양의 실근이 있다: 느린 근
    1/(τ(K-1)) 과, MOS 노드 용량이 만드는 빠른 근(Rb 무관). 실측 증가율은 빠른 근(~6e9 rad/s, 2026-10-08 독립 실행,
    Rb 1e5/1e6/1e7 에서 2 % 이내 같음) -- 그래서 손 모형 느린 근과의 일치는 보지 않고 '느린 근보다 크다'만 본다."""
    ref = rhp_ref(ref_root, RB[rb])
    assert ref["sat_min"] > SAT, "모든 MOS 포화 조건 점검"
    assert ref["K"] > ref["A0"] + 1 > 2, "K > 1 + A0(폐루프도 불안정), K > 1(개루프 RHP 극) 조건 점검"
    body = rhp_body(RB[rb], vin_line=f"Vin nin 0 DC {RHP['vin']}") + [
        "Ik 0 n3 DC 0 PULSE(0 1e-12 5e-10 1e-11 1e-11 1e-10)"]
    ctrl = [".control", "set noaskquit", "tran 1e-11 2e-8 0 1e-11", "let vo2 = v(n2)", "set wr_singlescale",
            "wrdata g.txt vo2", "quit", ".endc", ".end"]
    wd = ref_root / f"rhp_open_tran_{rb}"
    p, _ = _ngspice(_head() + body + ctrl, wd)
    a = np.loadtxt(wd / "g.txt")
    t, e = a[:, 0], np.abs(a[:, 1] - a[0, 1])
    assert a[0, 1] == pytest.approx(ref["nodes"]["n2"], abs=1e-5)       # .op 해에서 출발
    sel = (e > 1e-8) & (e < 1e-3)
    assert sel.sum() > 20 and math.log(e[sel].max() / e[sel].min()) > 4, (p.stdout + p.stderr)[-1500:]
    rate = np.polyfit(t[sel], np.log(e[sel]), 1)[0]
    assert rate > ref["p_hand"] > 0, (rate, ref["p_hand"])
    assert e[-1] > 1e-2                                                  # 끝내 큰 신호로 이탈(포화)


# 예측 비용이 기본 한도(600 s)를 넘는 경우(Rb 1e7: ~2980 s)만 `slow` -- 빠른 실행은 -m "not slow" 로 뺀다(conftest).
RB_CLOSED_LOOP = [pytest.param(k, marks=[pytest.mark.slow] if rhp_closed_loop_cost_s(v) > NGSPICE_TIMEOUT_S else [])
                  for k, v in RB.items()]


@pytest.mark.parametrize("rb", RB_CLOSED_LOOP)
def test_rhp_fixture_closed_loop_oscillates_and_n_is_zero(ref_root, rb):
    """전제 확인: 독립 폐루프 .tran 은 끝까지 큰 진폭(지속 진동/포화), 독립 .ac 의 N = 0 -> Z = N + P 에서 P >= 1."""
    ref = rhp_ref(ref_root, RB[rb])
    assert ref["nyq"]["N"] == 0, ref["nyq"]
    assert ref["meas"]["pm_deg"] is not None and ref["meas"]["pm_deg"] > 180, ref["meas"]   # Bode 식은 '여유 큼'
    pp = rhp_closed_loop_pp(ref_root, RB[rb], ref["nodes"]["n2"], ref["K"])
    # oracle (a) 물리 불변식: 킥 응답이 빠진 뒤 마지막 이완 주기 상한(2τ·ln K) 창에도 0.3 V 넘게 흔들림 = 감쇠하지 않음
    assert pp > 0.3, pp


# ====================================================================== 개루프 RHP 극 -> PM 정의 불가
@pytest.fixture(scope="module")
def rhp_run(tmp_path_factory, ref_root):
    rb = RB["rb1e5"]
    ref = rhp_ref(ref_root, rb)
    d = tmp_path_factory.mktemp("rhp")
    inp = rhp_input(make_lut(d / "lut.npz"), rb, constraints=[pm_con(">=", 60.0)],
                    metrics=[{"name": "pm", "measure": "pm_deg", "value": 60.0}], nodes=ref["nodes"])
    p, res = run_oracle(inp, d / "o", biases=("free", "forced"), sat_margin=SAT, extra=["--cache-dir", d / "cache"])
    assert res["free"] is not None and res["forced"] is not None, (p.stdout + p.stderr)[-2000:]
    return d, inp, res, ref, p


def test_rhp_nyquist_count_from_oracle_data(rhp_run):
    d, inp, res, ref, _ = rhp_run
    f, L, A = ac_loop_from_files(d / "o", stem_of(inp, "free"), beta_loop=False)
    mine = nyquist(L)
    ny = _sim(d / "o", inp)["ac"]["stability"]["nyquist"]
    assert mine["N"] == 0 == ny["encirclements_cw"], (mine, ny)
    assert ny["max_step_deg"] == pytest.approx(mine["max_step_deg"], rel=1e-6)
    assert ny["f_first_hz"] == pytest.approx(f[0]) and ny["f_last_hz"] == pytest.approx(f[-1])
    assert complex(*ny["L_first"]) == pytest.approx(L[0], rel=1e-9)
    assert complex(*ny["L_last"]) == pytest.approx(L[-1], rel=1e-9)
    st = _sim(d / "o", inp)["ac"]["stability"]
    assert st["loop"] == "beta_1" and st["closure_sign"] == np.sign(A[0].real) == 1.0


def test_rhp_transient_plan_and_decision(rhp_run):
    """절차 3·4·5: 폐루프 넷리스트 원소·과도 계획(입력·L·독립 .op 에서 유도)·판정(.stab.txt 재계산)."""
    d, inp, res, ref, _ = rhp_run
    o = d / "o"
    stem = stem_of(inp, "free")
    f, L, A = ac_loop_from_files(o, stem, beta_loop=False)
    pl = plan(f, L, [ref["nodes"]["n2"]])
    check_plan_record(_sim(o, inp)["ac"]["stability"]["transient"]["plan"], pl, 1.0)
    text = (o / f"{stem}.stab.cir").read_text(encoding="utf-8")
    low = text.lower()
    for nm in ("cac_nin", "vac_nin", "vdc_nin", "ldc_nin"):
        assert not re.search(rf"^{nm}\b", low, re.M), nm
    ecl = conftest.elem(text, "Ecl_nin")
    sign = 1.0                                       # Re A(fstart) > 0 (두 반전단)
    g = -sign * 1.0
    assert ecl[1:5] == ["nin", "ecl_nin", "n2", "0"] and float(ecl[5]) == pytest.approx(g), ecl
    pv, _ = pulse_of(text, "Vcl_nin")
    v0 = RHP["vin"] - g * ref["nodes"]["n2"]
    assert pv[0] == pytest.approx(v0, abs=1e-5) and pv[1] - pv[0] == pytest.approx(pl["kick"], rel=1e-6), pv
    assert pv[2:6] == pytest.approx([pl["td"], pl["td"], pl["td"], pl["pw"]], rel=1e-6), (pv, pl)
    tr = tran_line(text)
    assert tr[0] == pytest.approx(pl["tmax"], rel=1e-6) and tr[1] == pytest.approx(pl["tstop"], rel=1e-6), (tr, pl)
    dec = decide(o / f"{stem}.stab.txt", pl)
    t = _sim(o, inp)["ac"]["stability"]["transient"]
    assert t["status"] == dec["status"], (t["status"], dec)
    assert t["first_status"] == dec["first"] == "unstable", (t["first_status"], dec)
    assert t["M"] == pytest.approx(dec["M"], rel=1e-2)
    assert t["floor_V"] == pytest.approx(dec["floor2"], rel=1e-6)
    check_early_consistent(t, dec, pl)
    # 첫 실행이 decaying 이 아니면 연장 없음: extension 기록·.stab2.* 파일·캐시 extension 키 모두 없다
    assert "extension" not in t or t["extension"] is None, t.get("extension")
    assert not list(o.glob(f"{stem}.stab2*"))
    assert "extension" not in _sim(o, inp)["stability_cache"]


def test_rhp_pm_undefined_open_loop_rhp_poles(rhp_run):
    d, inp, res, ref, _ = rhp_run
    stem = stem_of(inp, "free")
    f, L, A = ac_loop_from_files(d / "o", stem, beta_loop=False)
    status = decide(d / "o" / f"{stem}.stab.txt", plan(f, L, [ref["nodes"]["n2"]]))["status"]
    assert status == "unstable"                     # 독립 폐루프 .tran 과 같은 결론(test_rhp_fixture_...)
    st = res["free"]["summary"]["stability"]
    assert STAB_KEYS <= set(st), set(st) ^ STAB_KEYS
    check_row(st, nyquist(L)["N"], status, ref["meas"]["pm_deg"])
    # 사용자 결정 Q10: P = 독립 .pz 의 RHP 극 수. oracle (c): 손으로 쓴 개루프(입력 이상 전압원 고정) .pz 와 같은 수
    p_mine = rhp_count_in_sweep(independent_pz(rhp_body(RB["rb1e5"], vin_line=f"Vin nin 0 DC {RHP['vin']}"), "n2",
                                               d / "ind_pz"), inp["testbench"]["ac"]["fstop_hz"])
    assert st["pz_P"] == p_mine >= 1, (st, p_mine)
    assert st["pm_undefined"] == "open_loop_rhp_poles" and st["open_loop_rhp_poles"] == p_mine
    assert st["verdict"] == "unstable" and st["Z"] == p_mine            # Z = N(0) + P
    assert st["pm_deg_raw"] == pytest.approx(ref["meas"]["pm_deg"], abs=0.05)
    assert st["loop"] == "beta_1" and st["transient_status"] == "unstable" and st["nyquist_encirclements_cw"] == 0
    ac = _sim(d / "o", inp)["ac"]
    assert ac["pm_deg"] is None and ac["pm_undefined"] == "open_loop_rhp_poles"
    assert ac["pm_deg_raw"] == st["pm_deg_raw"]
    assert ac["pm_open_loop_deg"] is None                         # β=1 이면 같은 양 -> None
    assert ac["ugf_hz"] == pytest.approx(ref["meas"]["ugf_hz"], rel=1e-4)    # 다른 측정은 그대로
    assert ac["dc_gain_db"] == pytest.approx(ref["meas"]["dc_gain_db"], abs=1e-3)


def test_rhp_crosscheck_invalidated(rhp_run):
    """C20 [변경]: pm_crosscheck_deg·gap = None, note = '정의 불가(<이유>) -- ...', |C| 측정값은 남는다."""
    d, inp, res, ref, _ = rhp_run
    ac = _sim(d / "o", inp)["ac"]
    assert ac["pm_crosscheck_deg"] is None and ac["pm_crosscheck_gap_deg"] is None
    assert str(ac["pm_crosscheck_note"]).startswith("정의 불가(open_loop_rhp_poles)"), ac["pm_crosscheck_note"]
    f, L, _ = ac_loop_from_files(d / "o", stem_of(inp, "free"), beta_loop=False)
    u = 0.5 * 10.0 ** (1 - mantissa_digits(d / "o" / f"{stem_of(inp, 'free')}.ac.txt"))
    assert ac["pm_crosscheck_mp_resolution"] == pytest.approx(2 * 2 * u, rel=1e-9)
    c = np.abs(L / (1 + L))
    i = int(np.argmax(c))
    mp = c[i] / c[0]
    if i == 0 or mp <= 1 + 4 * u:
        assert ac["closed_loop_peaking_db"] is None and ac["pm_crosscheck_deg_raw"] is None, ac
    else:
        assert ac["closed_loop_peaking_db"] == pytest.approx(20 * math.log10(mp), abs=1e-6)
        assert ac["pm_crosscheck_deg_raw"] is not None


@pytest.mark.parametrize("bias", ["free", "forced"])
def test_rhp_constraint_and_metric_na(rhp_run, bias):
    d, inp, res, ref, p = rhp_run
    c = res[bias]
    k = _cons(c, "pmc")
    und = c["summary"]["stability"]["pm_undefined"]
    assert und in VOCAB, c["summary"]["stability"]
    if bias == "free":
        assert und == "open_loop_rhp_poles"
    assert k["spice"] is None and k["judge"] == f"N/A(정의 불가: {und})" and k["undefined"] == und, k
    m = _perf(c, "pm")
    assert m["spice"] is None and m["judge"] == k["judge"], m
    # [U6 개정] free: 폐루프 과도 한계 사이클(사용자 결정 4) + Z = N + P >= 1(Q10) -> 폐루프 불안정 -> pm 제약은 N/A 로 남지만
    # free verdict 는 FAIL(설계 40 §4 C10 4, README 절차 9). forced 는 진단 전용이라 C8 대로 INCOMPLETE.
    assert c["summary"]["verdict"] == {"free": "FAIL", "forced": "INCOMPLETE"}[bias], c["summary"]
    if bias == "free":
        a = c["summary"]["acceptance"]
        assert a["constraints_unmeasured"] == ["pmc"] and a["constraints_failed"] == [], a
        assert a["closed_loop_unstable"], a
    md = (d / "o" / f"{stem_of(inp, bias)}.compare.md").read_text(encoding="utf-8")
    assert "- C10 PM 안정성 근거:" in md
    assert p.returncode == 1                          # C8: 여러 bias 중 최악(free FAIL) -> 1


def test_rhp_forced_stab_netlist_freezes_chokes(rhp_run):
    """forced: 고정 choke(Lhold_) 마다 Itb_<choke> DC I_op + .ic v(회로 노드) = V_op (동작점 패스 값)."""
    d, inp, res, ref, _ = rhp_run
    text = (d / "o" / f"{stem_of(inp, 'forced')}.stab.cir").read_text(encoding="utf-8")
    main = (d / "o" / f"{stem_of(inp, 'forced')}.cir").read_text(encoding="utf-8")
    chokes = [ln.split() for ln in main.splitlines() if ln.split() and ln.split()[0].lower().startswith("lhold_")]
    assert chokes, "forced 본 넷리스트에 Lhold_ 가 없다 -- 조건 점검"
    ics = dict(re.findall(r"v\((\w+)\)\s*=\s*([-+0-9.eE]+)", " ".join(
        ln for ln in text.splitlines() if ln.lower().startswith(".ic")), re.I))
    ics = {k.lower(): float(v) for k, v in ics.items()}
    for ch in chokes:
        itb = conftest.elem(text, f"Itb_{ch[0]}")
        assert itb is not None and itb[1:3] == ch[1:3], (ch, itb)
        assert abs(conftest.dc_value(itb)) < 1e-9, itb        # 예측 = 독립 해 -> 고정원 전류 ~ 0
        assert conftest.elem(text, ch[0]) is None             # choke 자체는 없다
        node = ch[2].lower()
        assert ics[node] == pytest.approx(ref["nodes"][node] if node in ref["nodes"] else RHP["vin"], abs=1e-4)


@pytest.mark.parametrize("op,limit", [(">=", -1e9), ("<=", 1e9), (">=", 0.0)])
def test_rhp_constraint_never_pass(tmp_path, rhp_run, op, limit):
    """수치로는 어떤 limit 이든 '만족'할 값(원값 284 deg)이 있어도 정의 불가, 절대 PASS 아님.
    [U6 개정] 이 회로(Rb 100 kΩ)는 폐루프 과도가 한계 사이클(사용자 결정 4)이고 Z = N + P >= 1(Q10)이라 free verdict 는
    INCOMPLETE 가 아니라 FAIL(반환 1) -- 설계 40 §4 C10 4·7."""
    d, inp, *_ = rhp_run
    inp2 = json.loads(json.dumps(inp))
    inp2["acceptance"] = {"constraints": [pm_con(op, limit)]}
    p, res = run_oracle(inp2, tmp_path / "o", sat_margin=SAT, extra=["--cache-dir", d / "cache"])
    c = res["free"]
    assert c is not None, (p.stdout + p.stderr)[-1500:]
    assert _cons(c, "pmc")["judge"] == "N/A(정의 불가: open_loop_rhp_poles)"
    assert c["summary"]["verdict"] == "FAIL" and p.returncode == 1, c["summary"]


def test_rhp_with_other_fail_is_fail(tmp_path, rhp_run):
    d, inp, res, ref, _ = rhp_run
    inp2 = json.loads(json.dumps(inp))
    inp2["acceptance"] = {"constraints": [pm_con(">=", 0.0),
                                          {"name": "g", "measure": "dc_gain_db", "op": ">=",
                                           "limit": ref["meas"]["dc_gain_db"] + 10}]}
    p, res2 = run_oracle(inp2, tmp_path / "o", sat_margin=SAT, extra=["--cache-dir", d / "cache"])
    c = res2["free"]
    assert c["summary"]["verdict"] == "FAIL" and p.returncode == 1, c["summary"]
    assert c["summary"]["acceptance"]["constraints_failed"] == ["g"]


def test_rhp_closed_loop_unstable_fails_without_pm_constraint(tmp_path, rhp_run):
    """[U6 개정, 옛 이름 test_rhp_control_pass_without_pm_constraint] 같은 회로, PM 이 아닌 제약만(만족) -> 옛 기대 PASS 는
    이제 FAIL: 폐루프 과도 unstable(한계 사이클, 사용자 결정 4)이면 pm 제약이 있든 없든 free verdict FAIL(설계 40 §4 C10 4,
    README 절차 9 [신규 U6]). 다른 제약(dc_gain)은 PASS 로 남고 FAIL 사유는 폐루프 불안정 하나다."""
    d, inp, res, ref, _ = rhp_run
    inp2 = json.loads(json.dumps(inp))
    inp2["acceptance"] = {"constraints": [{"name": "g", "measure": "dc_gain_db", "op": ">=",
                                           "limit": ref["meas"]["dc_gain_db"] - 1}]}
    inp2["predictions"]["metrics"] = []
    p, res2 = run_oracle(inp2, tmp_path / "o", sat_margin=SAT, extra=["--cache-dir", d / "cache"])
    c = res2["free"]
    assert _cons(c, "g")["judge"] == "PASS", _cons(c, "g")
    a = c["summary"]["acceptance"]
    assert a["closed_loop_unstable"] and a["constraints_failed"] == [], a
    assert c["summary"]["verdict"] == "FAIL" and p.returncode == 1, c["summary"]


def run_oracle_guarded(inp, out: Path, guard_s):
    """conftest.run_oracle 과 같은 호출(free, --sat-margin-v SAT)에 벽시계 한도를 건다. 한도를 넘으면 자기 PID 트리만
    끊고(taskkill /T /PID, 이미지 이름으로 죽이지 않음) 실패시킨다. -> (proc rc, 출력 끝, compare dict 또는 None, 경과 s)."""
    out.mkdir(parents=True, exist_ok=True)
    ip = conftest.write_json(out / "t.input.json", inp)
    args = [conftest.PY, "-P", str(conftest.ORACLE_DIR / "oracle_run.py"), str(ip), str(out), "--bias", "free",
            "--ngspice", str(NGSPICE), "--sat-margin-v", repr(SAT)]
    t0 = time.monotonic()
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
                            errors="replace", cwd=str(out))
    try:
        so, se = proc.communicate(timeout=guard_s)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        else:
            proc.kill()
        proc.communicate()
        pytest.fail(f"오라클이 벽시계 한도 {guard_s:.0f} s 안에 끝나지 않음(계약 1(c) 기본 상한 위반 의심): {out}")
    cj = out / f"{stem_of(inp, 'free')}.compare.json"
    return (proc.returncode, (so + se)[-1500:], json.loads(cj.read_text(encoding="utf-8")) if cj.exists() else None,
            time.monotonic() - t0)


# 과도 최종 상태로 허용되는 값(계약 2 표 'test_rhp_variants_never_pass[rb1e7]: unstable 이거나 failed' -- 첫 창 안 GHz
# 버스트는 기본 상한이 끊는다). [U6 개정] rb1e5·rb1e6 은 독립 폐루프 .tran 이 지속 진동(전제 test)이고 설계 40 §4 C10 8
# (사용자 결정 2026-10-09 '한계 사이클 = 감쇠하지 않음', 출렁이는 rb1e6형 포함)에 따라 과도 자체가 unstable 이어야 한다.
RB_VARIANT_ALLOWED = {"rb1e5": {"unstable"}, "rb1e6": {"unstable"}, "rb1e7": {"unstable", "failed"}}


@pytest.mark.parametrize("rb", list(RB))
def test_rhp_variants_never_pass(tmp_path, ref_root, rb):
    """음성 검사: 개루프 RHP 극(독립 증명: N = 0 + 독립 폐루프 지속 진동 -> P >= 1)이 있는 회로는 Rb 를 바꿔도
    PM 이 값이 되어서는 안 되고 pm_deg 제약 free verdict 는 PASS 가 될 수 없다(README C10·C8, 절 머리
    'P = 0 이 증명되거나 증거가 P = 0 과 맞을 때만 PM 이 값').
    조기 종결 계약 1(c)(사용자 결정 B): `--timeout-s` 없이도 기본 상한(창당 선언 상한 × 창 수) 안에 끝나야 한다 --
    벽시계 한도 = 이 파일의 기본 독립 실행 한도(본 .op/.ac·동작점 패스, 상한 미적용) + 독립 계획 K 로 셈한 과도 상한.
    연장은 decaying 일 때만이라 넣지 않는다(지속 진동 회로는 전제 test 가 감쇠하지 않음을 보였다)."""
    ref = rhp_ref(ref_root, RB[rb])
    pl_ind = plan(ref["f"], np.sign(ref["H"][0].real) * ref["H"], [ref["nodes"]["n2"]])
    guard = NGSPICE_TIMEOUT_S + wall_s_per_window() * pl_ind["K"]
    inp = rhp_input(make_lut(tmp_path / "lut.npz"), RB[rb], constraints=[pm_con(">=", 60.0)])
    rc, tail, c, elapsed = run_oracle_guarded(inp, tmp_path / "o", guard)
    assert c is not None, tail
    st = c["summary"]["stability"]
    tr = _sim(tmp_path / "o", inp)["ac"]["stability"]["transient"]
    assert st["pm_valid"] is False and st["pm_undefined"] in VOCAB, (st, tr.get("M"))
    # [U6 개정] Q10: Z = N + P(.pz) 로 결론이 나므로 INCOMPLETE 가 아니라 FAIL(반환 1). 근거: rb1e5 폐루프 한계 사이클(결정 4),
    # rb1e6·rb1e7 은 과도가 결론을 못 내도 .pz P >= 1(독립 개루프 .tran 이 증가를 보인 전제 test) 이라 Z >= 1.
    assert c["summary"]["verdict"] == "FAIL" and rc == 1, (c["summary"]["verdict"], st, tr.get("M"))
    assert st["verdict"] == "unstable", st
    assert tr["status"] in RB_VARIANT_ALLOWED[rb], (tr["status"], tr.get("reason"), tr.get("M"))
    # 계약 1(c): 적용 상한 = 계획 상한 = 선언 창당 상한 × 계획 창 수(--timeout-s 없음)
    assert tr["plan"]["wall_cap_s"] == pytest.approx(wall_s_per_window() * tr["plan"]["windows"], rel=1e-9)
    assert tr["wall_cap_s"] == pytest.approx(tr["plan"]["wall_cap_s"], rel=1e-12), tr["wall_cap_s"]
    assert elapsed <= guard, elapsed
    stem = stem_of(inp, "free")
    f, L, _ = ac_loop_from_files(tmp_path / "o", stem, beta_loop=False)
    if tr.get("timeout") is not None:
        # 끊긴 과도는 부분 데이터로 판정하지 않는다 -> failed(진동 확인이 아니므로 unstable 아님)
        assert tr["status"] == "failed" == tr["first_status"], tr
    else:
        # 절차 5 독립 재계산(연장·조기 종결 포함) = 오라클 기록, 지속 진동은 절대 stable 이 아님
        pl = plan(f, L, [ref["nodes"]["n2"]])
        dec = decide(tmp_path / "o" / f"{stem}.stab.txt", pl)
        assert tr["first_status"] == dec["first"] and tr["status"] == dec["status"] != "stable", (tr, dec)
        check_early_consistent(tr, dec, pl)
    check_row(st, nyquist(L)["N"], tr["status"], st["pm_deg_raw"])


def test_sustained_oscillation_rb1e6_limit_cycle_fail(tmp_path, ref_root):
    """[U6 개정, 옛 이름 test_sustained_oscillation_undetermined_incomplete] 손 RHP 회로 Rb 1 MΩ(독립 폐루프 .tran 은 지속
    진동 -- test_rhp_fixture_closed_loop_oscillates_and_n_is_zero[rb1e6]; 독립 개루프 .tran 은 지수 증가 -- 개루프 RHP 극 P >= 1).
    이 회로의 창 최댓값은 이완 진동이라 분해능 밖으로 출렁인다(예 [1.31, 1.10, 1.14, 1.18, 1.10, 1.10]). 사용자 결정 2026-10-09
    (설계 40 §4 C10 8 '한계 사이클 = 감쇠하지 않음 -- 출렁이는 rb1e6형 포함')로 과도 자체가 unstable(limit_cycle)이고,
    따라서 FAIL(반환 1), pm 제약은 N/A(정의 불가)."""
    rb = RB["rb1e6"]
    ref = rhp_ref(ref_root, rb)
    inp = rhp_input(make_lut(tmp_path / "lut.npz"), rb, constraints=[pm_con(">=", 60.0)])
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    assert c is not None, (p.stdout + p.stderr)[-1500:]
    # [사용자 결정 2026-10-09, 설계 40 §4 C10 8] 보류 해제: 출렁이는 지속 진동도 '감쇠하지 않음' -> 과도 자체가 unstable(limit_cycle).
    # 독립 재계산(decide, 같은 규칙)과 조기 창·종류가 같아야 한다.
    o, stem = tmp_path / "o", stem_of(inp, "free")
    f, L, _ = ac_loop_from_files(o, stem, beta_loop=False)
    pl = plan(f, L, [ref["nodes"]["n2"]])
    dec = decide(o / f"{stem}.stab.txt", pl)
    tr = _sim(o, inp)["ac"]["stability"]["transient"]
    assert dec["status"] == "unstable" and "limit_cycle" in (dec["early_kind"] or ()), dec
    assert tr["status"] == tr["first_status"] == "unstable", (tr["status"], tr.get("M"), tr.get("reason"))
    assert (tr.get("early_stop") or {}).get("kind") == "limit_cycle", tr.get("early_stop")
    check_early_consistent(tr, dec, pl)
    st = c["summary"]["stability"]
    assert st["verdict"] == "unstable" and st["pm_valid"] is False, st
    k = _cons(c, "pmc")
    assert k["spice"] is None and k["judge"] == f"N/A(정의 불가: {st['pm_undefined']})", k
    assert c["summary"]["verdict"] == "FAIL" and p.returncode == 1, c["summary"]


# ====================================================================== 고전적 불안정(P = 0, PM < 0) -> 값 유지, FAIL
@pytest.fixture(scope="module")
def classic_run(tmp_path_factory, ref_root):
    caps = CAPS["classic_unstable"]
    ref = three_ref(ref_root, caps)
    d = tmp_path_factory.mktemp("classic")
    inp = three_input(make_lut(d / "lut.npz"), caps, constraints=[pm_con(">=", 45.0)])
    p, res = run_oracle(inp, d / "o", sat_margin=SAT)
    assert res["free"] is not None, (p.stdout + p.stderr)[-2000:]
    return d, inp, res, ref, p


def test_classic_fixture_premise(ref_root):
    caps = CAPS["classic_unstable"]
    ref = three_ref(ref_root, caps)
    assert ref["nyq"]["N"] == 2 and ref["meas"]["pm_deg"] < 0, (ref["nyq"], ref["meas"])
    # 손 모형(3 실극, MOS 용량 무시): PM 부호와 대략 크기
    ro = 1 / (1 / THREE["rl"] + 1.04e-6)
    f = ac_grid(0.01, 1e10, 40)
    s = 2j * np.pi * f
    Lh = (137.8e-6 * ro) ** 3 / np.prod([1 + s * ro * c for c in caps], axis=0)
    assert nyquist(Lh)["N"] == 2 and measure(f, Lh)["pm_deg"] == pytest.approx(ref["meas"]["pm_deg"], abs=3.0)


def test_classic_negative_pm_kept_and_fail(classic_run):
    d, inp, res, ref, p = classic_run
    stem = stem_of(inp, "free")
    f, L, A = ac_loop_from_files(d / "o", stem, beta_loop=False)
    mine = nyquist(L)
    assert mine["N"] == 2 and np.sign(A[0].real) == -1.0
    v3 = ref["v3"]
    status = decide(d / "o" / f"{stem}.stab.txt", plan(f, L, [v3]))["status"]
    c = res["free"]
    st = c["summary"]["stability"]
    check_row(st, mine["N"], status, ref["meas"]["pm_deg"])
    assert st["closed_loop"] == "unstable" and st["pm_valid"] is True and st["open_loop_rhp_poles"] == 0
    ac = _sim(d / "o", inp)["ac"]
    assert ac["pm_deg"] == pytest.approx(ref["meas"]["pm_deg"], abs=0.01) and ac["pm_deg"] < 0
    assert ac["pm_deg_raw"] == ac["pm_deg"] and ac["pm_undefined"] is None
    assert ac["pm_open_loop_deg"] == ac["pm_deg"]                 # β=1: 같은 양, 유효
    k = _cons(c, "pmc")
    assert k["judge"] == "FAIL" and k["spice"] == ac["pm_deg"], k
    assert c["summary"]["verdict"] == "FAIL" and p.returncode == 1, c["summary"]


def test_classic_sparse_sweep_refined_count(tmp_path, ref_root):
    """[U6 개정, 옛 이름 test_classic_sparse_sweep_count_unavailable] 스윕 밀도 부족(points_per_decade 2): 순진한 감은 수는
    틀린 0 이 나온다(독립 확인). 설계 40 §4 C10 6(사용자 결정 Q10): π/2 를 넘는 구간은 이분해 다시 .ac(상한 K_max) -> 오라클은
    N 을 세고 그 값은 밀한 독립 스윕(40/decade)의 N(= 2, test_classic_fixture_premise)과 같아야 한다(oracle (c)). 폐루프 과도
    unstable(성장)이고 N >= 1 이라 verdict FAIL(반환 1)."""
    caps = CAPS["classic_unstable"]
    ref = three_ref(ref_root, caps, ppd=2)
    dense = three_ref(ref_root, caps)                     # 40/decade 독립 .ac
    assert ref["nyq"]["N_raw"] == pytest.approx(0, abs=1e-9) and not ref["nyq"]["valid_b"], ref["nyq"]
    assert dense["nyq"]["N"] == 2, dense["nyq"]
    inp = three_input(make_lut(tmp_path / "lut.npz"), caps, ppd=2, constraints=[pm_con("<=", 1e9)])
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    st = c["summary"]["stability"]
    f, L, _ = ac_loop_from_files(tmp_path / "o", stem_of(inp, "free"), beta_loop=False)
    mine = nyquist(L)
    assert mine["N"] is None and mine["max_step_deg"] > 120              # 원래 스윕만으로는 셀 수 없음(전제)
    ny = _sim(tmp_path / "o", inp)["ac"]["stability"]["nyquist"]
    assert ny["encirclements_cw"] == dense["nyq"]["N"], ny
    assert 1 <= ny["refinement"]["rounds"] <= ny["refinement"]["k_max"] == 10, ny["refinement"]
    assert ny["refinement"]["samples_added"] > 0 and ny["max_step_deg"] < 90.0, ny
    status = decide(tmp_path / "o" / f"{stem_of(inp, 'free')}.stab.txt", plan(f, L, [ref["v3"]]))["status"]
    assert status == "unstable"
    check_row(st, dense["nyq"]["N"], status, st["pm_deg_raw"])
    assert st["verdict"] == "unstable" and st["nyquist_encirclements_cw"] == 2
    assert c["summary"]["verdict"] == "FAIL" and p.returncode == 1, c["summary"]


# ====================================================================== 안정 루프: PM 값 불변, N = 0
@pytest.fixture(scope="module")
def lowpm_run(tmp_path_factory, ref_root):
    caps = CAPS["stable_lowpm"]
    ref = three_ref(ref_root, caps)
    d = tmp_path_factory.mktemp("lowpm")
    inp = three_input(make_lut(d / "lut.npz"), caps, constraints=[pm_con(">=", 10.0)])
    p, res = run_oracle(inp, d / "o", sat_margin=SAT)
    assert res["free"] is not None, (p.stdout + p.stderr)[-2000:]
    return d, inp, res, ref, p


def test_stable_lowpm_value_unchanged_and_pass(lowpm_run):
    d, inp, res, ref, p = lowpm_run
    stem = stem_of(inp, "free")
    f, L, A = ac_loop_from_files(d / "o", stem, beta_loop=False)
    mine = nyquist(L)
    assert mine["N"] == 0 == ref["nyq"]["N"]
    pl = plan(f, L, [ref["v3"]])
    check_plan_record(_sim(d / "o", inp)["ac"]["stability"]["transient"]["plan"], pl, -1.0)
    dec = decide(d / "o" / f"{stem}.stab.txt", pl)
    assert dec["status"] == "stable", dec
    st = res["free"]["summary"]["stability"]
    check_row(st, 0, "stable", ref["meas"]["pm_deg"])
    ac = _sim(d / "o", inp)["ac"]
    assert ac["pm_deg"] == pytest.approx(ref["meas"]["pm_deg"], abs=0.01), (ac["pm_deg"], ref["meas"])
    assert ac["pm_deg_raw"] == ac["pm_deg"] and ac["pm_open_loop_deg"] == ac["pm_deg"]
    assert ac["stability"]["transient"]["status"] == "stable"
    assert ac["stability"]["transient"]["M"] == pytest.approx(dec["M"], rel=1e-2)
    check_full_run(ac["stability"]["transient"], pl, dec)       # 계약 1(b): 안정(감쇠) 회로는 조기 종결 없음
    check_stabwin_log(d / "o" / f"{stem}.stab.log", dec["M"])
    pv, _ = pulse_of((d / "o" / f"{stem}.stab.cir").read_text(encoding="utf-8"), "Vcl_nin")
    g = -(-1.0) * 1.0                            # sign = -1 (세 반전단) -> g = -sign·w = +1
    assert pv[0] == pytest.approx(THREE["vin"] - g * ref["v3"], abs=1e-5)
    assert pv[2:6] == pytest.approx([pl["td"]] * 3 + [pl["pw"]], rel=1e-6)
    assert res["free"]["summary"]["verdict"] == "PASS" and p.returncode == 0, res["free"]["summary"]


def test_stable_sparse_sweep_refined_count_pass(tmp_path, ref_root, lowpm_run):
    """[U6 개정, 옛 이름 test_stable_sparse_sweep_nyquist_count_unavailable] 스윕 밀도 부족(points_per_decade 3): 원래 표본만으로는
    1+L 편각 한 간격 >= 90 deg 라 N 을 셀 수 없다(독립 확인). 설계 40 §4 C10 6: 그 구간을 이분해 다시 .ac -> N = 밀한 독립 스윕의
    N(= 0). 폐루프 과도 stable 이고 Z = 0 이라 안정(설계 40 §4 C10 7) -> PM 은 원값 그대로 값, 제약 >= 10 deg PASS(같은 회로 40/decade
    대조와 같은 결론)."""
    caps = CAPS["stable_lowpm"]
    ref = three_ref(ref_root, caps, ppd=3)
    dense = three_ref(ref_root, caps)
    assert dense["nyq"]["N"] == 0, dense["nyq"]
    inp = three_input(make_lut(tmp_path / "lut.npz"), caps, ppd=3, constraints=[pm_con(">=", 10.0)])
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    stem = stem_of(inp, "free")
    f, L, _ = ac_loop_from_files(tmp_path / "o", stem, beta_loop=False)
    mine = nyquist(L)
    assert mine["N"] is None and mine["valid_a"] and not mine["valid_b"] and mine["max_step_deg"] > 100, mine
    ny = _sim(tmp_path / "o", inp)["ac"]["stability"]["nyquist"]
    assert ny["encirclements_cw"] == dense["nyq"]["N"] == 0, ny
    assert 1 <= ny["refinement"]["rounds"] <= 10 and ny["refinement"]["samples_added"] > 0, ny["refinement"]
    dec = decide(tmp_path / "o" / f"{stem}.stab.txt", plan(f, L, [ref["v3"]]))
    assert dec["status"] == "stable", dec
    st = c["summary"]["stability"]
    check_row(st, 0, "stable", st["pm_deg_raw"])
    assert st["pm_undefined"] is None and st["verdict"] == "stable" and st["nyquist_encirclements_cw"] == 0, st
    assert st["pm_deg_raw"] == pytest.approx(ref["meas"]["pm_deg"], abs=0.01)    # 원값은 같은 격자의 Bode 값
    ac = _sim(tmp_path / "o", inp)["ac"]
    assert ac["pm_deg"] == ac["pm_deg_raw"] and ac["pm_deg"] >= 10.0, ac["pm_deg"]
    k = _cons(c, "pmc")
    assert k["judge"] == "PASS" and k["spice"] == ac["pm_deg"], k
    assert c["summary"]["verdict"] == "PASS" and p.returncode == 0, c["summary"]


@pytest.fixture(scope="module")
def ind_cs(ref_root):
    return independent_cs(ref_root)


def test_stable_cs_beta1_value_unchanged(tmp_path, ind_cs):
    """conftest CS(β=1, 단일 극): PM = 독립 .ac 측정 정의 값 그대로, N = 0, 과도 stable, P = 0(==)."""
    pr = preds_from_independent(ind_cs)
    inp = cs_input(make_lut(tmp_path / "lut.npz"), diffusion="zero", preds_nodes=pr["nodes"],
                   preds_devices=pr["devices"], constraints=[pm_con(">=", 45.0)])
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    ref_pm = measure(ind_cs["f"], ind_cs["H"])["pm_deg"]
    f, L, A = ac_loop_from_files(tmp_path / "o", stem_of(inp, "free"), beta_loop=False)
    assert np.sign(A[0].real) == -1.0 and nyquist(L)["N"] == 0
    pl = plan(f, L, [ind_cs["V"]["nout"]])
    # 계약 1(a) d56ba66 기대 f_crit(독립 .ac, 대역 = 첫 표본 ~ 단일 교차 2.23e7 Hz 위 첫 표본): 그 위쪽 표본 10^7.35 Hz
    # (단일 극 루프는 |1+L| 이 주파수에 따라 줄어 대역 끝에서 최소; 대역 없이 고르면 스윕 끝 1e10 Hz 였다)
    ind_L = np.sign(ind_cs["H"][0].real) * ind_cs["H"]
    assert band_f_crit(ind_cs["f"], ind_L) == pytest.approx(10 ** 7.35, rel=1e-6)
    dec = decide(tmp_path / "o" / f"{stem_of(inp, 'free')}.stab.txt", pl)
    assert dec["status"] == "stable", dec
    ac = _sim(tmp_path / "o", inp)["ac"]
    check_plan_record(ac["stability"]["transient"]["plan"], pl, -1.0)
    check_full_run(ac["stability"]["transient"], pl, dec)       # 계약 1(b): 안정 회로는 조기 종결 없음
    assert ac["pm_deg"] == pytest.approx(ref_pm, abs=1e-3) and ac["pm_deg_raw"] == ac["pm_deg"]
    check_row(c["summary"]["stability"], 0, "stable", ref_pm)
    assert c["summary"]["verdict"] == "PASS" and p.returncode == 0, c["summary"]


@pytest.fixture(scope="module")
def fb_ref(ref_root):
    return independent_fb(ref_root)


def _fb_inp(lut):
    inp = fb_input(lut, cin=1e-12)
    inp["predictions"]["devices"] = {"M1": {"off_current_A": 0.0}}
    inp["acceptance"] = {"constraints": [pm_con(">=", 20.0)]}
    return inp


def test_stable_beta_loop_value_unchanged(tmp_path, fb_ref):
    """β 루프(Middlebrook T, 해석식 conftest.fb_loop_gain): PM 그대로, N = 0(오라클 루프 데이터에서 다시 셈), 루프
    폐루프 과도 넷리스트 = 루프 넷리스트 + Vlb PULSE(0 w·kick ...), Ldc 는 Itb(DC I_op) + .ic."""
    inp = _fb_inp(make_lut(tmp_path / "lut.npz"))
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    o, stem = tmp_path / "o", stem_of(inp, "free")
    f, T, _ = ac_loop_from_files(o, stem, beta_loop=True)
    ac = _sim(o, inp)["ac"]
    assert ac["pm_definition"] == "beta_loop"
    assert measure(f, T)["pm_deg"] == pytest.approx(ac["pm_deg_raw"], abs=1e-6)    # 데이터 재구성 확인
    Th = fb_loop_gain(f, fb_ref["gm"], fb_ref["gds"], cin=1e-12)
    assert ac["pm_deg"] == pytest.approx(measure(f, Th)["pm_deg"], abs=1.0)     # 해석식(MOS 용량 무시)
    mine = nyquist(T)
    assert mine["N"] == 0 == nyquist(Th)["N"] and ac["stability"]["nyquist"]["encirclements_cw"] == 0
    assert ac["stability"]["nyquist"]["max_step_deg"] == pytest.approx(mine["max_step_deg"], rel=1e-6)
    assert ac["stability"]["loop"] == "beta_loop"
    text = (o / f"{stem}.stab.cir").read_text(encoding="utf-8")
    pl = plan(f, T, [fb_ref["vout"]])
    rec = ac["stability"]["transient"]["plan"]
    check_plan_record(rec, pl, rec["sign"])          # β 루프: 닫기 부호는 회전 없음(절차 1) -- 값은 기록 그대로 대조 제외
    pv, tok = pulse_of(text, "Vlb_nin")
    assert tok[1:3] == ["nin", "lbx_nin"] and pv[0] == 0.0 and pv[1] == pytest.approx(pl["kick"], rel=1e-6), tok
    assert pv[2:6] == pytest.approx([pl["td"]] * 3 + [pl["pw"]], rel=1e-6)
    assert tran_line(text)[1] == pytest.approx(pl["tstop"], rel=1e-6)
    itb = conftest.elem(text, "Itb_Ldc_nin")
    i_op = (FB["vin"] - fb_ref["vout"]) / FB["rf"]        # choke 가 nin 으로 보내는 전류 = Rf 로 나가는 전류
    assert itb[1:3] == ["dcs_nin", "nin"] and conftest.dc_value(itb) == pytest.approx(i_op, rel=1e-3), itb
    assert conftest.elem(text, "Ldc_nin") is None
    assert re.search(r"^\.ic\s+v\(nin\)\s*=\s*0\.7\b", text, re.M | re.I), text[-800:]
    dec = decide(o / f"{stem}.stab.txt", pl)
    assert dec["status"] == "stable" == ac["stability"]["transient"]["status"]
    check_full_run(ac["stability"]["transient"], pl, dec)       # 계약 1(b): 안정 회로는 조기 종결 없음
    check_save_probes_only(text)                                 # 계약 1(d): β 루프 H 식도 피연산자만
    check_row(c["summary"]["stability"], 0, "stable", ac["pm_deg_raw"])
    assert ac["pm_deg"] == ac["pm_deg_raw"] and ac["pm_open_loop_deg"] is not None
    assert ac["pm_crosscheck_deg"] is not None                                   # C20 그대로(z ~0.29 peaking)
    assert c["summary"]["verdict"] == "PASS" and p.returncode == 0, c["summary"]


# ====================================================================== 검사 대상 아님 / 캐시(C21)
def test_no_pm_raw_not_checked(tmp_path):
    """|L| 이 첫 점부터 1 미만(RC 분압, 이득 0.5) -> PM 원값 없음 -> 검사 대상 아님: pm_valid None + reason, .stab 없음."""
    inp = rc_input(make_lut(tmp_path / "lut.npz"))
    zero_diffusion(inp)
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    assert c is not None, (p.stdout + p.stderr)[-1500:]
    st = c["summary"]["stability"]
    assert st["pm_valid"] is None and st["reason"], st
    ac = _sim(tmp_path / "o", inp)["ac"]
    assert ac["pm_deg"] is None and ac["stability"]["reason"], ac["stability"]
    assert not list((tmp_path / "o").glob("*.stab*"))


@pytest.mark.parametrize("circ", ["fb_beta_loop", "three_lowpm"])
def test_cache_stability_outside_ac(tmp_path, circ):
    """C21: 폐루프 과도 캐시 상태는 sim.stability_cache = {op_pass, transient}(+ 연장 실행을 했을 때만 extension)(ac 밖).
    첫 실행 miss, 재실행 hit, hit·miss 에서 ac 동일, .stab.txt(·.stab2.txt) 복원. 캐시 미사용이면 전부 None."""
    lut = make_lut(tmp_path / "lut.npz")
    inp = _fb_inp(lut) if circ == "fb_beta_loop" else three_input(lut, CAPS["stable_lowpm"],
                                                                    constraints=[pm_con(">=", 10.0)])
    cache = tmp_path / "cache"
    run_oracle(inp, tmp_path / "o1", sat_margin=SAT, extra=["--cache-dir", cache])
    run_oracle(inp, tmp_path / "o2", sat_margin=SAT, extra=["--cache-dir", cache])
    run_oracle(inp, tmp_path / "o3", sat_margin=SAT)
    s1, s2, s3 = (_sim(tmp_path / k, inp) for k in ("o1", "o2", "o3"))
    extended = s1["ac"]["stability"]["transient"].get("extension") is not None
    if circ == "three_lowpm":
        assert extended                          # 아래 test_extension_decaying_to_stable 의 전제와 같음
    keys = ["op_pass", "transient"] + (["extension"] if extended else [])
    assert s1["stability_cache"] == dict.fromkeys(keys, "miss"), s1["stability_cache"]
    assert s2["stability_cache"] == dict.fromkeys(keys, "hit"), s2["stability_cache"]
    assert s3["stability_cache"] == dict.fromkeys(keys, None), s3["stability_cache"]
    for s in (s1, s2, s3):
        assert "stability_cache" not in s["ac"] and "stability_cache" not in s["ac"]["stability"]
    assert s1["ac"] == s2["ac"]
    stem = stem_of(inp, "free")
    assert (tmp_path / "o2" / f"{stem}.stab.txt").exists()
    assert (tmp_path / "o2" / f"{stem}.stab2.txt").exists() is extended
    assert s2["ac"]["stability"]["transient"]["status"] == "stable"


def test_extension_decaying_to_stable(lowpm_run, ref_root):
    """절차 5 연장: 저 PM(~16 deg) 3단은 첫 실행 K 창에서 창마다 줄지만 floor' 에 못 닿음 -> `decaying` -> 연장 실행
    `.stab2.*`(같은 킥·같은 창, n = ceil(ln(floor'/M_K)/ln(M_K/M_{K-1})), tstop = t_end + (K + n)·W) -> 같은 규칙으로
    stable/decaying -> 최종 stable. 기록 모양: transient{status, first_status, ..., extension{status, M, floor_V, reason,
    netlist, file, ngspice_rc, extension_windows, tstop}}."""
    d, inp, res, ref, p = lowpm_run
    o, stem = d / "o", stem_of(inp, "free")
    f, L, _ = ac_loop_from_files(o, stem, beta_loop=False)
    pl = plan(f, L, [ref["v3"]])
    dec = decide(o / f"{stem}.stab.txt", pl)
    assert dec["first"] == "decaying" and dec["ext"] is not None, dec                 # 전제(독립 재계산)
    assert dec["ext"]["status"] in ("stable", "decaying") and dec["status"] == "stable", dec["ext"]
    tr = _sim(o, inp)["ac"]["stability"]["transient"]
    assert tr["first_status"] == "decaying" and tr["status"] == "stable", tr
    assert tr["M"] == pytest.approx(dec["M"], rel=1e-2) and tr["floor_V"] == pytest.approx(dec["floor2"], rel=1e-6)
    assert tr["plan"]["windows"] == pl["K"]                                           # plan 은 첫 실행 것
    ex = tr["extension"]
    assert {"status", "M", "floor_V", "reason", "netlist", "file", "ngspice_rc", "extension_windows",
            "tstop"} <= set(ex), set(ex)
    assert ex["extension_windows"] == dec["ext"]["n"] > 0, (ex["extension_windows"], dec["ext"]["n"])
    assert ex["tstop"] == pytest.approx(dec["ext"]["plan"]["tstop"], rel=1e-9)
    # 계약 1(c) d56ba66: 연장 실행 상한 = 창당 상한 × (K + n), 첫 실행 상한(transient.wall_cap_s)은 plan 것 그대로
    assert ex["wall_cap_s"] == pytest.approx(wall_s_per_window() * (pl["K"] + ex["extension_windows"]), rel=1e-9)
    assert tr["wall_cap_s"] == pytest.approx(tr["plan"]["wall_cap_s"], rel=1e-12)
    assert ex["status"] == dec["ext"]["status"] and ex["ngspice_rc"] == 0, ex
    assert len(ex["M"]) == pl["K"] + ex["extension_windows"]
    assert ex["M"] == pytest.approx(dec["ext"]["M"], rel=1e-2)
    assert ex["floor_V"] == pytest.approx(dec["ext"]["floor2"], rel=1e-6)
    assert ex["netlist"] == f"{stem}.stab2.cir" and ex["file"] == f"{stem}.stab2.txt", ex
    t1 = (o / f"{stem}.stab.cir").read_text(encoding="utf-8")
    t2 = (o / f"{stem}.stab2.cir").read_text(encoding="utf-8")
    # 같은 킥·같은 동작점·같은 시간 척도(V1 V2 TD TR TF PW; PER 은 펄스 반복 방지용이라 tstop 에 따라 다를 수 있음)
    assert pulse_of(t2, "Vcl_nin")[0][:6] == pulse_of(t1, "Vcl_nin")[0][:6]
    tr2 = tran_line(t2)
    assert tr2[0] == pytest.approx(pl["tmax"], rel=1e-6) and tr2[1] == pytest.approx(ex["tstop"], rel=1e-6), tr2
    assert (o / f"{stem}.stab2.log").exists()
    assert res["free"]["summary"]["stability"]["transient_status"] == "stable"


def test_extension_record_absent_when_not_decaying(classic_run):
    """첫 실행이 decaying 이 아니면(고전적 불안정 -> unstable) 그 상태가 최종: extension 없음, .stab2.* 없음."""
    d, inp, res, ref, _ = classic_run
    o, stem = d / "o", stem_of(inp, "free")
    tr = _sim(o, inp)["ac"]["stability"]["transient"]
    assert tr["first_status"] == tr["status"] != "decaying", tr
    assert tr.get("extension") is None and not list(o.glob(f"{stem}.stab2*"))


# ====================================================================== 조기 종결 계약(사용자 결정 B 2026-10-08)
def _early_unstable():
    """피검 순수 함수 `oracle_simulate.early_unstable(M, floor', reltol)`(계약 1(b) 이름) -- 소스는 열지 않고 import 만."""
    d = str(conftest.ORACLE_DIR)
    if d not in sys.path:
        sys.path.insert(0, d)
    return importlib.import_module("oracle_simulate").early_unstable


# oracle (a): 구성으로 답이 정해진 합성 창 최댓값 열. 각 기대값의 근거(계약 1(b) 정의를 손으로 대입):
EARLY_CASES = [
    # 일정 진폭: 모든 g(j) 에서 M_j(1-r) < M_{j-1}(1+r) -> 증가 없음 -> 절대 False(계약 '일정 진폭은 조기 종결하지 않는다')
    pytest.param([1.0, 1.0, 1.0, 1.0, 1.0], 0.0, 1e-3, False, id="constant"),
    # 분해능 이내 증가: g(2) = 1.0015*0.999 = 1.0005 < 1*1.001 + 1e-3 = 1.002 -> False
    pytest.param([1.0, 1.0015, 1.003, 1.0045], 1e-3, 1e-3, False, id="within_resolution"),
    # 상대 증가는 reltol 을 넘지만 floor' 이내: g(2) = 1.05*0.999 = 1.049 < 1*1.001 + 0.1 = 1.101 -> False
    pytest.param([1.0, 1.05, 1.1, 1.15], 0.1, 1e-3, False, id="within_floor"),
    # 분해능 초과 연속 증가: g(2) 1.1988 > 1.002, g(3) 1.4985 > 1.2022, M_3 = 1.5 >= M_1 -> True(j = 3)
    pytest.param([1.0, 1.2, 1.5], 1e-3, 1e-3, True, id="growth_j3"),
    # 맥놀이: g(2) 0.4995 < 1.002 -> j = 3 에서 g(j-1) 거짓, 더 볼 창 없음 -> False
    pytest.param([1.0, 0.5, 1.2], 1e-3, 1e-3, False, id="beating"),
    # 창 2 개(j = 2): 기준은 j >= 3 부터 -> 증가가 커도 False
    pytest.param([1.0, 1.5], 1e-3, 1e-3, False, id="j2"),
    pytest.param([1.0, 2.0], 0.0, 1e-3, False, id="j2_large"),
    # M_j >= M_1 조건: j = 4 에서 g(3)*g(4) 참이지만 M_4 = 1.5 < M_1 = 5 -> False
    pytest.param([5.0, 1.0, 1.2, 1.5], 1e-3, 1e-3, False, id="below_first"),
    # 같은 열에 창 5 추가: g(4) 1.4985 > 1.2022, g(5) 5.994 > 1.5025, M_5 = 6 >= 5 -> True(j = 5)
    pytest.param([5.0, 1.0, 1.2, 1.5, 6.0], 1e-3, 1e-3, True, id="above_first_j5"),
    # g↑(M_1, M_j) 는 분해능 인식형(d56ba66): j = 4 에서 g↑(0.5, 0.6) 0.5994 > 0.5015, g↑(0.6, 1.0005) 0.9995 > 0.6016 참이지만
    # M_4 = 1.0005 는 M_1 = 1 보다 분해능 안(0.9995 < 1·1.001 + 1e-3 = 1.002) -> False (옛 'M_j >= M_1' 이면 True)
    pytest.param([1.0, 0.5, 0.6, 1.0005], 1e-3, 1e-3, False, id="equal_first_within_resolution"),
    # reltol 경계(floor' 0): 1.0021*0.999 = 1.0010979 > 1.001, 1.0043*0.999 = 1.0032957 > 1.0021*1.001 = 1.0031021 -> True
    pytest.param([1.0, 1.0021, 1.0043], 0.0, 1e-3, True, id="just_above_reltol"),
    # reltol 경계 아래: 1.0019*0.999 = 1.0008981 < 1.001 -> g(2) 거짓, j = 3 뒤 창 없음 -> False
    pytest.param([1.0, 1.0019, 1.0039], 0.0, 1e-3, False, id="just_below_reltol"),
    # 일정 진폭 + reltol 이내 흔들림(긴 열): 어떤 이웃 쌍도 M_j(1-r) > M_{j-1}(1+r) 를 만족하지 않음 -> False
    pytest.param([1.0, 1.0009, 0.9995, 1.001, 1.0008, 1.0], 0.0, 1e-3, False, id="jitter_within_reltol"),
]


@pytest.mark.parametrize("m,floor2,reltol,expected", EARLY_CASES)
def test_early_unstable_predicate(m, floor2, reltol, expected):
    """계약 1(b) 조기 unstable 기준의 순수 입출력(경계: j = 2, 맥놀이, 일정 진폭, 분해능 이내, M_j >= M_1, reltol 경계).
    반환은 참/거짓 값으로 본다(조기 창 번호를 돌려도 참 값이면 통과)."""
    assert bool(_early_unstable()(list(m), floor2, reltol)) is expected


def test_n_pp_contract_literal():
    """계약 1(a) 예시 'reltol 1e-3 이면 n_pp 71'(oracle (d))과 이 파일의 전수 탐색(oracle (b))이 같은지 -- 계획 대조의 전제.
    이 파일 testbench reltol 1e-4: 1 - cos(pi/222) = 1.0014e-4 > 1e-4, 1 - cos(pi/223) = 9.92e-5 <= 1e-4 -> 223."""
    assert n_pp_by_scan(1e-3) == 71
    assert n_pp_by_scan(1e-4) == 223


def test_config_declares_wall_cap():
    """계약 1(c): oracle_config.json stability_transient 에 창당 상한(양수, s)과 근거 문장(justification)."""
    cfg = json.loads(ORACLE_CONFIG.read_text(encoding="utf-8"))
    stc = cfg["stability_transient"]
    w = stc["wall_s_per_window"]
    assert isinstance(w, (int, float)) and not isinstance(w, bool) and w > 0, w
    assert isinstance(stc["justification"], str) and stc["justification"].strip(), stc
    # d56ba66: wall_s_per_window = safety_factor × 창당 비용 최댓값, safety_factor = 반복 실행 max/median(1 미만이면 1),
    # 측정치는 config 의 measured_* 키에 같이 남긴다
    sf = stc["safety_factor"]
    assert isinstance(sf, (int, float)) and not isinstance(sf, bool) and sf >= 1, sf
    assert any(k.startswith("measured_") for k in stc), sorted(stc)


def test_plan_default_reltol(tmp_path, ind_cs):
    """계약 1(a): testbench.options 에 reltol 이 없으면 ngspice 기본 1e-3 -> plan.reltol 1e-3, n_pp 71(계약 예시 리터럴),
    floor 도 같은 reltol. 안정 CS 라 조기 종결 없음."""
    pr = preds_from_independent(ind_cs)
    inp = cs_input(make_lut(tmp_path / "lut.npz"), diffusion="zero", preds_nodes=pr["nodes"],
                   preds_devices=pr["devices"], constraints=[pm_con(">=", 45.0)])
    del inp["testbench"]["options"]["reltol"]
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    assert res["free"] is not None, (p.stdout + p.stderr)[-1500:]
    o, stem = tmp_path / "o", stem_of(inp, "free")
    f, L, _ = ac_loop_from_files(o, stem, beta_loop=False)
    pl = plan(f, L, [ind_cs["V"]["nout"]], reltol=1e-3)
    tr = _sim(o, inp)["ac"]["stability"]["transient"]
    assert tr["plan"]["reltol"] == 1e-3 and tr["plan"]["n_pp"] == 71, tr["plan"]
    check_plan_record(tr["plan"], pl, -1.0)
    dec = decide(o / f"{stem}.stab.txt", pl)
    assert dec["status"] == "stable" == tr["status"], (dec, tr["status"])
    check_full_run(tr, pl, dec)


def test_growing_fixture_premise_independent(ref_root):
    """전제(oracle (a), 피검 코드 없음): 고전적 불안정 3단(PM < 0, N = 2)을 손으로 쓴 폐루프 .tran(이상 VCVS 단위
    음되먹임, 같은 킥·창·tmax 를 독립 .ac 에서 계획)으로 돌리면 창 최댓값이 분해능을 넘어 연속 증가 -> 계약 1(b) 조기
    창이 계획 창 수 K 보다 앞이다(scratch 2026-10-08, 옛 tmax: M ~ [0.049, 0.093, 0.186, 0.293, 0.219, 0.359] -> j = 3)."""
    caps = CAPS["classic_unstable"]
    ref = three_ref(ref_root, caps)
    sign = float(np.sign(ref["H"][0].real))
    assert sign == -1.0                                   # 세 반전단
    pl = plan(ref["f"], sign * ref["H"], [ref["v3"]])
    g = -sign * 1.0
    v0 = THREE["vin"] - g * ref["v3"]
    body = [b for b in three_body(caps) if not b.startswith("Vin ")]
    body += [f"Ecl nin ecl n3 0 {g}",
             f"Vcl ecl 0 DC {v0} PULSE({v0} {v0 + pl['kick']} {pl['td']} {pl['td']} {pl['td']} {pl['pw']} 1)",
             ".save v(n3)"]
    ctrl = [".control", "set noaskquit", f"tran {pl['tmax']} {pl['tstop']} 0 {pl['tmax']}", "let h = v(n3)",
            "set wr_singlescale", "wrdata g.txt h", "quit", ".endc", ".end"]
    wd = ref_root / "classic_closed_loop"
    p, _ = _ngspice(_head() + body + ctrl, wd)
    dec = decide_run(wd / "g.txt", pl)
    assert dec["early"] is not None and 3 <= dec["early"] < pl["K"], (dec, pl["K"], (p.stdout + p.stderr)[-800:])
    assert dec["status"] == "unstable"


def test_growing_fixture_early_stop(classic_run):
    """계약 1(b): 증가하는 불안정 회로(classic_run) -> 창 j 에서 즉시 중단, status = unstable, early_stop{window, M, reason},
    windows_run = j < 계획 창 수, 데이터 파일 마지막 시각 = 창 j 끝(< tstop 이어도 failed 아님), 연장 없음, STABWIN 로그,
    pm 제약은 이전처럼 FAIL(불안정은 계속 FAIL)."""
    d, inp, res, ref, p = classic_run
    o, stem = d / "o", stem_of(inp, "free")
    f, L, _ = ac_loop_from_files(o, stem, beta_loop=False)
    pl = plan(f, L, [ref["v3"]])
    dec = decide(o / f"{stem}.stab.txt", pl)
    assert dec["early"] is not None and dec["early"] < pl["K"], (dec, pl["K"])        # 파일이 증명하는 조기 창
    tr = _sim(o, inp)["ac"]["stability"]["transient"]
    check_plan_record(tr["plan"], pl, -1.0)
    assert tr["status"] == tr["first_status"] == "unstable" == dec["status"], (tr["status"], dec)
    es = tr["early_stop"]
    assert es["window"] == dec["early"] == tr["windows_run"] < tr["plan"]["windows_planned"], (es, tr["windows_run"])
    assert len(es["M"]) == es["window"] and es["M"] == pytest.approx(dec["M"], rel=1e-2), (es, dec["M"])
    assert isinstance(es["reason"], str) and es["reason"], es
    assert tr["M"] == pytest.approx(dec["M"], rel=1e-2)
    # 데이터 파일은 창 j 끝에 닿았고(decide_run 이 창 j 를 끝난 창으로 셌다) 창 j+1 끝 전에 멈췄다
    assert dec["t_last"] < pl["t_end"] + (dec["early"] + 1) * pl["W"], (dec["t_last"], pl)
    assert dec["t_last"] < pl["tstop"]
    assert tr["wall_cap_s"] == pytest.approx(tr["plan"]["wall_cap_s"], rel=1e-12)
    assert tr.get("extension") is None and not list(o.glob(f"{stem}.stab2*"))
    check_stabwin_log(o / f"{stem}.stab.log", dec["M"])
    c = res["free"]
    assert _cons(c, "pmc")["judge"] == "FAIL" and c["summary"]["verdict"] == "FAIL" and p.returncode == 1, c["summary"]


@pytest.mark.parametrize("which", ["lowpm_stab", "lowpm_stab2", "classic_stab", "rhp_stab"])
def test_stab_netlist_saves_probes_only(request, which):
    """계약 1(d): `.stab.cir`·`.stab2.cir` 는 H 식 피연산자(v(..)/i(..))와 time 만 save."""
    fx, ext = {"lowpm_stab": ("lowpm_run", "stab"), "lowpm_stab2": ("lowpm_run", "stab2"),
               "classic_stab": ("classic_run", "stab"), "rhp_stab": ("rhp_run", "stab")}[which]
    d, inp, *_ = request.getfixturevalue(fx)
    check_save_probes_only((d / "o" / f"{stem_of(inp, 'free')}.{ext}.cir").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def fb_stab_run(tmp_path_factory, ref_root):
    d = tmp_path_factory.mktemp("fbstab")
    inp = _fb_inp(make_lut(d / "lut.npz"))
    p, res = run_oracle(inp, d / "o", sat_margin=SAT)
    assert res["free"] is not None, (p.stdout + p.stderr)[-1500:]
    return d, inp, res


@pytest.mark.parametrize("which", ["lowpm_run", "classic_run", "rhp_run", "fb_stab_run"])
def test_stab_kick_and_observation_at_loop_break(request, which):
    """설계 40 §4 C10 8 '자극 위치'(사용자 결정 2026-10-09): 폐루프 과도의 자극과 관측은 루프 끊는 점에 둔다. 끊는 점 =
    β=1 은 루프를 닫는 입력 넷(nin -- Ecl_nin 이 구동), β 루프는 절단 넷(nin / lbx_nin, Vlb_nin). 단언: 킥 원(PULSE)이 그 점의
    원(Vcl_nin 또는 Vlb_nin)이고, 판정 데이터 H(`let hst` 식)의 피연산자가 그 끊는 점의 노드 전압뿐이다(출력 노드 관측 아님)."""
    d, inp, *_ = request.getfixturevalue(which)
    text = (d / "o" / f"{stem_of(inp, 'free')}.stab.cir").read_text(encoding="utf-8")
    beta_loop = which == "fb_stab_run"
    kick_src = "Vlb_nin" if beta_loop else "Vcl_nin"
    pv, _ = pulse_of(text, kick_src)
    assert pv is not None and pv[1] != pv[0], (kick_src, pv)
    break_nodes = {"v(nin)", "v(lbx_nin)"} if beta_loop else {"v(nin)"}
    ops = hst_operands(text)
    assert ops and ops <= break_nodes, (ops, break_nodes)


def test_timeout_s_overrides_default_cap(tmp_path):
    """계약 1(c): `--timeout-s` 가 있으면 그것이 적용 상한(transient.wall_cap_s), 계획 상한(plan.wall_cap_s)은 선언값 x K
    그대로. 끊기면 failed(사유 과도 시간 초과, timeout 기록) -> PASS 불가. 회로는 test_truncated_... 와 같다(손 RHP
    회로 Rb 1 MOhm: scratch 2026-10-08 계약 tmax 로 같은 .stab.cir 단독 실행 107 s >> 4 s)."""
    from conftest import run_netlist, run_simulate
    rb = RB["rb1e6"]
    inp = rhp_input(make_lut(tmp_path / "lut.npz"), rb, constraints=[pm_con(">=", 60.0)])
    p, text, meta = run_netlist(inp, tmp_path)
    assert p.returncode == 0 and meta["blockers"] == [], (p.stdout + p.stderr)[-800:]
    cir, sim = tmp_path / "t.free.cir", tmp_path / "t.free.sim.json"
    q = run_simulate(cir, sim, tmp_path, ["--timeout-s", "4"])
    assert q.returncode == 0 and sim.exists(), (q.returncode, (q.stdout + q.stderr)[-1500:])
    tr = json.loads(sim.read_text(encoding="utf-8"))["ac"]["stability"]["transient"]
    assert tr["wall_cap_s"] == pytest.approx(4.0), tr.get("wall_cap_s")
    assert tr["plan"]["wall_cap_s"] == pytest.approx(wall_s_per_window() * tr["plan"]["windows"], rel=1e-9)
    assert tr["status"] == "failed" and tr["timeout"], tr
    assert tr.get("early_stop") is None, tr.get("early_stop")


# ====================================================================== 절차 4 개정(4ab6d85): 교차 여럿 -> 시간 척도 f_lo
# 회로 3: CS(M1, RL) 출력 n1 -> 쌍T 노치(Rt1·Rt2 = R, Ctm = 2C 접지 / Ct1·Ct2 = C, Rts = R/2 접지) -> no(출력).
#   손 모형: A = -gm·Ro(n1)·N(s), N = (1 + (s/ω0)²)/(1 + 4 s/ω0 + (s/ω0)²), ω0 = 1/(RC) -- |A| 가 노치(f0 = 9.95 kHz) 앞에서
#   1 아래로 내려갔다(PM 교차 f_lo) 노치 뒤에서 다시 1 위로, Cn1 이 있으면 n1 극 뒤에서 다시 1 아래로 -> 교차 3 개.
#   Cn1 이 없으면 고주파에서 N -> 1 이라 |L(fstop)| ~ gm·Ro > 1 -> 절차 2 유효 조건 (a) 실패.
NOTCH = dict(vdd=1.8, vin=0.7, rl=129409.146, R=1e7, C=1.6e-12, L=0.5e-6, fw=2e-6, n=2)


def notch_body(cn1):
    c = NOTCH
    b = [f"Vdd vdd 0 DC {c['vdd']}", f"Vin nin 0 DC {c['vin']} AC 1", f"RL vdd n1 {c['rl']}",
         f"Rt1 n1 nm {c['R']}", f"Rt2 nm no {c['R']}", f"Ctm nm 0 {2 * c['C']}", f"Ct1 n1 nc {c['C']}",
         f"Ct2 nc no {c['C']}", f"Rts nc 0 {c['R'] / 2}"]
    b += [f"XM1_{k} n1 nin 0 0 {NFET} l={c['L']} w={c['fw']}" for k in range(c["n"])]
    if cn1:
        b.append(f"Cn1 n1 0 {cn1}")
    return b


def notch_input(lut, cn1, constraints=None):
    c = NOTCH
    pas = [{"name": "RL", "kind": "resistor", "terminals": ["vdd", "n1"], "value": c["rl"]},
           {"name": "Rt1", "kind": "resistor", "terminals": ["n1", "nm"], "value": c["R"]},
           {"name": "Rt2", "kind": "resistor", "terminals": ["nm", "no"], "value": c["R"]},
           {"name": "Ctm", "kind": "capacitor", "terminals": ["nm", "gnd"], "value": 2 * c["C"]},
           {"name": "Ct1", "kind": "capacitor", "terminals": ["n1", "nc"], "value": c["C"]},
           {"name": "Ct2", "kind": "capacitor", "terminals": ["nc", "no"], "value": c["C"]},
           {"name": "Rts", "kind": "resistor", "terminals": ["nc", "gnd"], "value": c["R"] / 2}]
    if cn1:
        pas.append({"name": "Cn1", "kind": "capacitor", "terminals": ["n1", "gnd"], "value": cn1})
    inp = {"schema": "spice_oracle_input/1", "circuit": "tnotch",
           "process": conftest.process_block(lut),
           "rails": [{"net": "vdd", "voltage": c["vdd"]}, {"net": "gnd", "voltage": 0.0, "reference": True}],
           "devices": [{"name": "M1", "kind": "nmos", "drain": "n1", "gate": "nin", "source": "gnd", "bulk": "gnd",
                        "L": c["L"], "finger_w": c["fw"], "n_fingers": c["n"], "W": c["fw"] * c["n"]}],
           "sources": [], "passives": pas,
           "ports": {"input": "nin", "output": "no"},
           "predictions": {"nodes": {"nin": c["vin"]}, "devices": {"M1": {"off_current_A": 0.0}}, "metrics": []},
           "testbench": conftest.testbench_block()}
    if constraints is not None:
        inp["acceptance"] = {"constraints": constraints}
    return zero_diffusion(inp)


def notch_ref(root: Path, cn1):
    r = run_spice("\n".join(notch_body(cn1)), root / f"notch_{cn1:g}", ["v(no)"], ac_out="no", ac=(0.01, 1e10, 40))
    H = r["H"]
    L = np.sign(H[0].real) * H
    return {"f": r["f"], "H": H, "L": L, "meas": measure(r["f"], H), "nyq": nyquist(L), "vo": r["op"]["v(no)"],
            "cross": gain_crossings(r["f"], L)}


def test_multi_crossing_plan_uses_f_lo(tmp_path, ref_root):
    """|L| = 1 교차 3 개(f_hi/f_lo > 100): 계획의 tmax·td·tr·tf·pw·창 = f_lo 하나에서, f_hi 는 plan.f_hi_hz 기록만.
    폐루프 넷리스트의 PULSE·tran 도 f_lo 척도. PM 은 독립 .ac 값 그대로, N = 0, 과도 판정 = 독립 재계산."""
    cn1 = 20e-12
    ref = notch_ref(ref_root, cn1)
    assert len(ref["cross"]) == 3 and ref["cross"][-1] / ref["cross"][0] > 100, ref["cross"]     # 전제(독립 .ac)
    # 계약 1(a) d56ba66 기대 f_crit(독립 .ac, 대역 = 첫 표본 ~ f_hi 1.09 MHz 위 첫 표본): |1+L| 최소 = 노치 중심 격자점
    # 1e4 Hz(40/decade 격자, 노치 f0 = 1/(2π RC) = 9.95 kHz 에 가장 가까운 표본). 대역 없이 고르면 스윕 끝 1e10 Hz 였다.
    assert band_f_crit(ref["f"], ref["L"]) == pytest.approx(1e4, rel=1e-6)
    assert ref["nyq"]["N"] == 0
    inp = notch_input(make_lut(tmp_path / "lut.npz"), cn1, constraints=[pm_con(">=", 10.0)])
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    assert c is not None, (p.stdout + p.stderr)[-1500:]
    o, stem = tmp_path / "o", stem_of(inp, "free")
    f, L, A = ac_loop_from_files(o, stem, beta_loop=False)
    pl = plan(f, L, [ref["vo"]])
    assert len(pl["crossings"]) == 3 and pl["crossings"] == pytest.approx(ref["cross"], rel=1e-4)
    ac = _sim(o, inp)["ac"]
    st = ac["stability"]
    assert st["gain_crossings_hz"] == pytest.approx(pl["crossings"], rel=1e-9)
    rec = st["transient"]["plan"]
    check_plan_record(rec, pl, -1.0)
    # 계약 1(a): 펄스 척도 td 는 f_lo 하나(불변), 걸음 상한 tmax 만 min(td, 1/(f_crit·n_pp))
    assert rec["td"] == pytest.approx(1 / (2 * math.pi * rec["f_lo_hz"]), rel=1e-12)
    assert rec["td"] > 50 / (2 * math.pi * rec["f_hi_hz"])                    # 옛 1/(2π f_hi) 와 확실히 다름
    assert rec["tmax"] == pytest.approx(min(rec["td"], 1 / (rec["f_crit_hz"] * rec["n_pp"])), rel=1e-12)
    text = (o / f"{stem}.stab.cir").read_text(encoding="utf-8")
    pv, _ = pulse_of(text, "Vcl_nin")
    assert pv[2:6] == pytest.approx([pl["td"]] * 4, rel=1e-6), (pv, pl)
    tr = tran_line(text)
    assert tr[0] == pytest.approx(pl["tmax"], rel=1e-6) and tr[3] == pytest.approx(pl["tmax"], rel=1e-6)
    assert tr[1] == pytest.approx(pl["tstop"], rel=1e-6)
    dec = decide(o / f"{stem}.stab.txt", pl)
    assert st["transient"]["status"] == dec["status"] and st["transient"]["first_status"] == dec["first"], dec
    check_early_consistent(st["transient"], dec, pl)
    assert ac["pm_deg_raw"] == pytest.approx(ref["meas"]["pm_deg"], abs=0.01)
    assert st["nyquist"]["encirclements_cw"] == nyquist(L)["N"] == 0
    check_row(c["summary"]["stability"], 0, dec["status"], ac["pm_deg_raw"])


def test_tail_above_one_nyquist_unavailable(tmp_path, ref_root):
    """절차 2 유효 조건 (a): Cn1 없는 노치 회로는 |L(fstop)| >= 1(고주파에서 N -> 1, 독립 .ac 확인)인데 PM 원값(첫 하강
    교차)은 있다 -> N = None + reason. 과도 판정이 stable 이면 `nyquist_count_unavailable`, 아니면 표대로 -- 어느 경우든
    PM 정의 불가 -> pm 제약 N/A -> INCOMPLETE(PASS 불가)."""
    ref = notch_ref(ref_root, 0.0)
    assert abs(ref["L"][-1]) >= 1 and not ref["nyq"]["valid_a"] and ref["meas"]["pm_deg"] is not None, ref["nyq"]
    inp = notch_input(make_lut(tmp_path / "lut.npz"), 0.0, constraints=[pm_con(">=", 10.0)])
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    o, stem = tmp_path / "o", stem_of(inp, "free")
    f, L, _ = ac_loop_from_files(o, stem, beta_loop=False)
    mine = nyquist(L)
    assert mine["N"] is None and not mine["valid_a"]
    ny = _sim(o, inp)["ac"]["stability"]["nyquist"]
    assert ny["encirclements_cw"] is None and isinstance(ny["reason"], str) and ny["reason"], ny
    assert abs(complex(*ny["L_last"])) >= 1
    dec = decide(o / f"{stem}.stab.txt", plan(f, L, [ref["vo"]]))
    st = c["summary"]["stability"]
    check_row(st, None, dec["status"], st["pm_deg_raw"])
    assert st["pm_valid"] is False
    assert _cons(c, "pmc")["judge"] == f"N/A(정의 불가: {st['pm_undefined']})"
    assert c["summary"]["verdict"] == "INCOMPLETE" and p.returncode == 0, c["summary"]


def test_truncated_transient_failed_never_pass(tmp_path, ref_root):
    """README 절차 4: 실행 시간 상한은 진입점 `--timeout-s` 가 ngspice 를 끊는다 -> 데이터 파일이 tstop 에 못 미침 ->
    절차 5 `failed` -> '모름' -> PM 은 표대로(N = 0 이면 `stability_unverified`) 정의 불가 -> PASS 불가.
    회로: 손 RHP 회로 Rb 1 MΩ(폐루프 과도가 지속 완화 진동이라 .stab 실행이 본 .op/.ac 보다 훨씬 김).
    oracle_simulate.py 만 `--timeout-s` 를 받으므로(README 파일 표) netlist -> simulate -> compare 로 부른다."""
    from conftest import run_compare, run_netlist, run_simulate
    rb = RB["rb1e6"]
    inp = rhp_input(make_lut(tmp_path / "lut.npz"), rb, constraints=[pm_con(">=", 60.0)])
    p, text, meta = run_netlist(inp, tmp_path)
    assert p.returncode == 0 and meta["blockers"] == [], (p.stdout + p.stderr)[-800:]
    cir, sim = tmp_path / "t.free.cir", tmp_path / "t.free.sim.json"
    q = run_simulate(cir, sim, tmp_path, ["--timeout-s", "4"])
    assert q.returncode == 0 and sim.exists(), (q.returncode, (q.stdout + q.stderr)[-1500:])
    s = json.loads(sim.read_text(encoding="utf-8"))
    ac = s["ac"]
    assert ac["pm_deg_raw"] is not None, "본 .ac 는 상한 안에 끝나야 한다 -- 조건 점검"
    tr = ac["stability"]["transient"]
    assert tr["status"] == "failed" or tr["first_status"] == "failed", tr
    st_sim = ac["stability"]
    assert st_sim["pm_undefined"] in VOCAB and ac["pm_deg"] is None, st_sim
    r, cmp = run_compare(inp, cir, sim, tmp_path / "cmp", sat_margin=SAT)
    assert cmp is not None, (r.stdout + r.stderr)[-1500:]
    st = cmp["summary"]["stability"]
    check_row(st, st_sim["nyquist"]["encirclements_cw"], "failed", st["pm_deg_raw"])
    assert _cons(cmp, "pmc")["judge"].startswith("N/A(정의 불가: ")
    # [U6 개정] 과도가 결론을 못 내도(failed) Q10 의 Z = N + P 가 결론을 내면 그것이 판정이다: .pz P >= 1 이 개루프 과도로
    # 확인되었으면(README 절차 7 신뢰 규칙) unstable -> FAIL, 확인 못 했으면(4 s 상한은 부하에 따라 확인 실행도 끊음) 둘 다
    # 결론 없음 -> INCOMPLETE. 어느 쪽이든 PASS 는 아니다. 기대 verdict 는 기록된 .pz·확인 결과에서 판정 규칙(독립 구현)으로 셈.
    exp = expected_judgement("failed", st_sim["nyquist"]["encirclements_cw"], st.get("pz_P"), st.get("pz_validated"),
                             st["pm_deg_raw"])
    assert cmp["summary"]["verdict"] == {"unstable": "FAIL", "undetermined": "INCOMPLETE"}[exp["verdict"]], (
        cmp["summary"], exp)
