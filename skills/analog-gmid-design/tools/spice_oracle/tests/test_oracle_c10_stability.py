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
"""
import json
import math
import re
import subprocess
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


def plan(f, L, vop_outputs):
    """README 절차 4(조정 상수 없음, 4ab6d85 개정): 시간 척도는 f_lo(가장 낮은 |L|=1 교차 = PM 교차) 하나.
    tmax = td = tr = tf = pw = 1/(2π f_lo), t_end = td + tr + pw + tf, W = 1/f_lo. f_hi 는 기록만(계획에 쓰지 않음)."""
    cr = gain_crossings(f, L)
    f_lo, f_hi = min(cr), max(cr)
    kick = KB_OVER_Q * TEMP_K
    tmax = 1 / (2 * math.pi * f_lo)
    pw = tmax
    t_end = 4 * tmax
    w = 1 / f_lo
    floor = sum(RELTOL * abs(v) + VNTOL for v in vop_outputs)
    k = math.ceil(math.log(kick / floor))
    return {"f_lo": f_lo, "f_hi": f_hi, "kick": kick, "tmax": tmax, "pw": pw, "t_end": t_end, "W": w, "floor": floor,
            "K": k, "tstop": t_end + k * w, "crossings": cr}


def check_plan_record(rec, pl, sign):
    """ac.stability.transient.plan 이 독립 계획과 같은지(필드 전부). floor 는 V_op 출처(독립 .op 대 동작점 패스)만 달라
    상대 1e-4, 나머지는 같은 식이라 1e-9."""
    exact = {"kick_V": pl["kick"], "td": pl["tmax"], "tr": pl["tmax"], "pw": pl["pw"], "tmax": pl["tmax"],
             "window_s": pl["W"], "t_kick_end": pl["t_end"], "f_lo_hz": pl["f_lo"], "f_hi_hz": pl["f_hi"]}
    for k, v in exact.items():
        assert rec[k] == pytest.approx(v, rel=1e-9), (k, rec[k], v)
    assert rec["windows"] == pl["K"], (rec["windows"], pl["K"])
    assert rec["floor_V"] == pytest.approx(pl["floor"], rel=1e-4)
    assert rec["tstop"] == pytest.approx(pl["tstop"], rel=1e-6)
    assert rec["sign"] == sign


def mantissa_digits(path: Path) -> int:
    """파일 실수들의 가수 유효숫자(찍힌 가수 자릿수, 전체 최솟값) -- README C20 data_rel_resolution 의 d."""
    d = None
    for tok in path.read_text(encoding="utf-8").split():
        m = re.fullmatch(r"[-+]?(\d+)\.?(\d*)[eE][-+]?\d+", tok)
        if m:
            n = len(m.group(1) + m.group(2))
            d = n if d is None else min(d, n)
    return d


def decide_run(stab_txt: Path, p):
    """README 절차 5 의 한 실행 판정(3fdabd7 개정): e = H - H(0), 창 j 의 M_j = max|e|, floor' = floor + u·max|H|.
    M_K <= floor' -> stable; M_K >= M_1 -> unstable; M_1 > M_2 > ... > M_K -> decaying; 그 밖 -> undetermined."""
    a = np.loadtxt(stab_txt)
    t, h = a[:, 0], a[:, 1]
    u = 0.5 * 10.0 ** (1 - mantissa_digits(stab_txt))
    e = np.abs(h - h[0])
    m = []
    for j in range(p["K"]):
        lo, hi = p["t_end"] + j * p["W"], p["t_end"] + (j + 1) * p["W"]
        sel = (t >= lo) & (t <= hi)
        m.append(float(e[sel].max()) if sel.any() else float("nan"))
    fl = p["floor"] + u * float(np.abs(h).max())
    if t[-1] < p["tstop"] * (1 - 2 * u):
        st = "failed"
    elif m[-1] <= fl:
        st = "stable"
    elif m[-1] >= m[0]:
        st = "unstable"
    elif all(m[j] > m[j + 1] for j in range(len(m) - 1)):
        st = "decaying"
    else:
        st = "undetermined"
    return {"status": st, "M": m, "floor2": fl}


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
           "ext": None}
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
    """summary.stability 가 (독립 N, 과도 상태, pm_raw) 에서 표가 정하는 행과 같은지."""
    cl, p, bound, und = expected_row(status, nyq_mine, pm_raw)
    assert st["closed_loop"] == cl, st
    assert st["open_loop_rhp_poles"] == p, st
    if bound is None:
        assert st["open_loop_rhp_poles_bound"] is None, st
    else:
        assert str(st["open_loop_rhp_poles_bound"]).startswith(bound), st
    assert st["pm_undefined"] == und, st
    assert st["pm_valid"] is (und is None), st


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
    assert pv[2:6] == pytest.approx([pl["tmax"], pl["tmax"], pl["tmax"], pl["pw"]], rel=1e-6), (pv, pl)
    tr = tran_line(text)
    assert tr[0] == pytest.approx(pl["tmax"], rel=1e-6) and tr[1] == pytest.approx(pl["tstop"], rel=1e-6), (tr, pl)
    dec = decide(o / f"{stem}.stab.txt", pl)
    t = _sim(o, inp)["ac"]["stability"]["transient"]
    assert t["status"] == dec["status"], (t["status"], dec)
    assert t["first_status"] == dec["first"] == "unstable", (t["first_status"], dec)
    assert t["M"] == pytest.approx(dec["M"], rel=1e-2)
    assert t["floor_V"] == pytest.approx(dec["floor2"], rel=1e-6)
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
    assert st["pm_undefined"] == "open_loop_rhp_poles" and st["open_loop_rhp_poles"] == 1
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
    assert c["summary"]["verdict"] == "INCOMPLETE", c["summary"]
    if bias == "free":
        a = c["summary"]["acceptance"]
        assert a["constraints_unmeasured"] == ["pmc"] and a["constraints_failed"] == [], a
    md = (d / "o" / f"{stem_of(inp, bias)}.compare.md").read_text(encoding="utf-8")
    assert "- C10 PM 안정성 근거:" in md
    assert p.returncode == 0


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
    """수치로는 어떤 limit 이든 '만족'할 값(원값 284 deg)이 있어도 정의 불가 -> INCOMPLETE(반환 0), 절대 PASS 아님."""
    d, inp, *_ = rhp_run
    inp2 = json.loads(json.dumps(inp))
    inp2["acceptance"] = {"constraints": [pm_con(op, limit)]}
    p, res = run_oracle(inp2, tmp_path / "o", sat_margin=SAT, extra=["--cache-dir", d / "cache"])
    c = res["free"]
    assert c is not None, (p.stdout + p.stderr)[-1500:]
    assert _cons(c, "pmc")["judge"] == "N/A(정의 불가: open_loop_rhp_poles)"
    assert c["summary"]["verdict"] == "INCOMPLETE" and p.returncode == 0, c["summary"]


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


def test_rhp_control_pass_without_pm_constraint(tmp_path, rhp_run):
    """대조: 같은 회로, PM 이 아닌 제약만 -> PASS. 위 INCOMPLETE 는 PM 정의 불가 때문."""
    d, inp, res, ref, _ = rhp_run
    inp2 = json.loads(json.dumps(inp))
    inp2["acceptance"] = {"constraints": [{"name": "g", "measure": "dc_gain_db", "op": ">=",
                                           "limit": ref["meas"]["dc_gain_db"] - 1}]}
    inp2["predictions"]["metrics"] = []
    p, res2 = run_oracle(inp2, tmp_path / "o", sat_margin=SAT, extra=["--cache-dir", d / "cache"])
    assert res2["free"]["summary"]["verdict"] == "PASS" and p.returncode == 0, res2["free"]["summary"]


@pytest.mark.parametrize("rb", list(RB))
def test_rhp_variants_never_pass(tmp_path, ref_root, rb):
    """음성 검사: 개루프 RHP 극(독립 증명: N = 0 + 독립 폐루프 지속 진동 -> P >= 1)이 있는 회로는 Rb 를 바꿔도
    PM 이 값이 되어서는 안 되고 pm_deg 제약 free verdict 는 PASS 가 될 수 없다(README C10·C8, 절 머리
    'P = 0 이 증명되거나 증거가 P = 0 과 맞을 때만 PM 이 값')."""
    ref = rhp_ref(ref_root, RB[rb])
    inp = rhp_input(make_lut(tmp_path / "lut.npz"), RB[rb], constraints=[pm_con(">=", 60.0)])
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    assert c is not None, (p.stdout + p.stderr)[-1500:]
    st = c["summary"]["stability"]
    tr = _sim(tmp_path / "o", inp)["ac"]["stability"]["transient"]
    assert st["pm_valid"] is False and st["pm_undefined"] in VOCAB, (st, tr.get("M"))
    assert c["summary"]["verdict"] != "PASS" and p.returncode == 0, (c["summary"]["verdict"], st, tr.get("M"))
    # 절차 5 독립 재계산(연장 포함) = 오라클 기록, 지속 진동은 절대 stable 이 아님
    stem = stem_of(inp, "free")
    f, L, _ = ac_loop_from_files(tmp_path / "o", stem, beta_loop=False)
    dec = decide(tmp_path / "o" / f"{stem}.stab.txt", plan(f, L, [ref["nodes"]["n2"]]))
    assert tr["first_status"] == dec["first"] and tr["status"] == dec["status"] != "stable", (tr, dec)
    check_row(st, nyquist(L)["N"], dec["status"], st["pm_deg_raw"])


def test_sustained_oscillation_undetermined_incomplete(tmp_path, ref_root):
    """절차 5 개정의 계기(40158dd 의 rb1e6, M = [1.43, 1.21, 0.68, 1.13, 1.45, 1.30]): 창 사이 다시 커짐(M_K < M_1,
    단조 감소 아님) -> 첫 실행 `undetermined`, 연장 없음 -> 최종 '모름', N = 0 -> `stability_unverified`,
    pm 제약 N/A -> INCOMPLETE(반환 0). 독립 폐루프 .tran 은 지속 진동(test_rhp_fixture_...)."""
    rb = RB["rb1e6"]
    ref = rhp_ref(ref_root, rb)
    inp = rhp_input(make_lut(tmp_path / "lut.npz"), rb, constraints=[pm_con(">=", 60.0)])
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    o, stem = tmp_path / "o", stem_of(inp, "free")
    f, L, _ = ac_loop_from_files(o, stem, beta_loop=False)
    dec = decide(o / f"{stem}.stab.txt", plan(f, L, [ref["nodes"]["n2"]]))
    m = dec["M"]
    assert m[-1] < m[0] and not all(m[j] > m[j + 1] for j in range(len(m) - 1)), m     # 다시 커짐(전제)
    assert dec["first"] == dec["status"] == "undetermined", dec
    tr = _sim(o, inp)["ac"]["stability"]["transient"]
    assert tr["first_status"] == "undetermined" == tr["status"], tr
    assert tr["M"] == pytest.approx(m, rel=1e-2)
    assert tr.get("extension") is None and not list(o.glob(f"{stem}.stab2*"))
    st = c["summary"]["stability"]
    assert st["closed_loop"] is None and st["pm_undefined"] == "stability_unverified" and st["pm_valid"] is False, st
    k = _cons(c, "pmc")
    assert k["judge"] == "N/A(정의 불가: stability_unverified)" and k["spice"] is None, k
    assert c["summary"]["verdict"] == "INCOMPLETE" and p.returncode == 0, c["summary"]


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


def test_classic_sparse_sweep_count_unavailable(tmp_path, ref_root):
    """스윕 밀도 부족(points_per_decade 2): 순진한 감은 수는 틀린 0 이 나온다(독립 확인) -> 오라클은 N 을 세지
    않아야 한다(None + reason). 폐루프 불안정이면 `closed_loop_unstable`, PM 정의 불가 -> PASS 불가."""
    caps = CAPS["classic_unstable"]
    ref = three_ref(ref_root, caps, ppd=2)
    assert ref["nyq"]["N_raw"] == pytest.approx(0, abs=1e-9) and not ref["nyq"]["valid_b"], ref["nyq"]
    inp = three_input(make_lut(tmp_path / "lut.npz"), caps, ppd=2, constraints=[pm_con("<=", 1e9)])
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    st = c["summary"]["stability"]
    f, L, _ = ac_loop_from_files(tmp_path / "o", stem_of(inp, "free"), beta_loop=False)
    mine = nyquist(L)
    assert mine["N"] is None and mine["max_step_deg"] > 120
    ny = _sim(tmp_path / "o", inp)["ac"]["stability"]["nyquist"]
    assert ny["encirclements_cw"] is None and ny["reason"], ny
    assert ny["max_step_deg"] == pytest.approx(mine["max_step_deg"], rel=1e-6)
    status = decide(tmp_path / "o" / f"{stem_of(inp, 'free')}.stab.txt", plan(f, L, [ref["v3"]]))["status"]
    check_row(st, None, status, st["pm_deg_raw"])
    assert st["pm_undefined"] in ("closed_loop_unstable", "stability_unverified"), st
    assert _cons(c, "pmc")["judge"] == f"N/A(정의 불가: {st['pm_undefined']})"
    assert c["summary"]["verdict"] == "INCOMPLETE" and p.returncode == 0, c["summary"]


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
    pv, _ = pulse_of((d / "o" / f"{stem}.stab.cir").read_text(encoding="utf-8"), "Vcl_nin")
    g = -(-1.0) * 1.0                            # sign = -1 (세 반전단) -> g = -sign·w = +1
    assert pv[0] == pytest.approx(THREE["vin"] - g * ref["v3"], abs=1e-5)
    assert pv[2:6] == pytest.approx([pl["tmax"]] * 3 + [pl["pw"]], rel=1e-6)
    assert res["free"]["summary"]["verdict"] == "PASS" and p.returncode == 0, res["free"]["summary"]


def test_stable_sparse_sweep_nyquist_count_unavailable(tmp_path, ref_root, lowpm_run):
    """스윕 밀도 부족(points_per_decade 3): 1+L 편각 한 간격 >= 90 deg -> N = None,
    폐루프 과도 stable -> `nyquist_count_unavailable`, 제약 N/A -> INCOMPLETE(대조: 같은 회로 40/decade 는 PASS)."""
    caps = CAPS["stable_lowpm"]
    ref = three_ref(ref_root, caps, ppd=3)
    inp = three_input(make_lut(tmp_path / "lut.npz"), caps, ppd=3, constraints=[pm_con(">=", 10.0)])
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    stem = stem_of(inp, "free")
    f, L, _ = ac_loop_from_files(tmp_path / "o", stem, beta_loop=False)
    mine = nyquist(L)
    assert mine["N"] is None and mine["valid_a"] and not mine["valid_b"] and mine["max_step_deg"] > 100, mine
    ny = _sim(tmp_path / "o", inp)["ac"]["stability"]["nyquist"]
    assert ny["encirclements_cw"] is None and isinstance(ny["reason"], str) and ny["reason"], ny
    assert ny["max_step_deg"] == pytest.approx(mine["max_step_deg"], rel=1e-6)
    dec = decide(tmp_path / "o" / f"{stem}.stab.txt", plan(f, L, [ref["v3"]]))
    assert dec["status"] == "stable", dec
    st = c["summary"]["stability"]
    check_row(st, None, "stable", st["pm_deg_raw"])
    assert st["pm_undefined"] == "nyquist_count_unavailable" and st["nyquist_encirclements_cw"] is None
    assert st["pm_deg_raw"] == pytest.approx(ref["meas"]["pm_deg"], abs=0.01)    # 원값은 같은 격자의 Bode 값
    ac = _sim(tmp_path / "o", inp)["ac"]
    assert ac["pm_deg"] is None and ac["pm_crosscheck_deg"] is None
    k = _cons(c, "pmc")
    assert k["judge"] == "N/A(정의 불가: nyquist_count_unavailable)" and k["undefined"] == "nyquist_count_unavailable"
    assert c["summary"]["verdict"] == "INCOMPLETE" and p.returncode == 0, c["summary"]


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
    dec = decide(tmp_path / "o" / f"{stem_of(inp, 'free')}.stab.txt", plan(f, L, [ind_cs["V"]["nout"]]))
    assert dec["status"] == "stable", dec
    ac = _sim(tmp_path / "o", inp)["ac"]
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
    assert pv[2:6] == pytest.approx([pl["tmax"]] * 3 + [pl["pw"]], rel=1e-6)
    assert tran_line(text)[1] == pytest.approx(pl["tstop"], rel=1e-6)
    itb = conftest.elem(text, "Itb_Ldc_nin")
    i_op = (FB["vin"] - fb_ref["vout"]) / FB["rf"]        # choke 가 nin 으로 보내는 전류 = Rf 로 나가는 전류
    assert itb[1:3] == ["dcs_nin", "nin"] and conftest.dc_value(itb) == pytest.approx(i_op, rel=1e-3), itb
    assert conftest.elem(text, "Ldc_nin") is None
    assert re.search(r"^\.ic\s+v\(nin\)\s*=\s*0\.7\b", text, re.M | re.I), text[-800:]
    dec = decide(o / f"{stem}.stab.txt", pl)
    assert dec["status"] == "stable" == ac["stability"]["transient"]["status"]
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
    assert rec["tmax"] == pytest.approx(1 / (2 * math.pi * rec["f_lo_hz"]), rel=1e-12)
    assert rec["tmax"] > 50 / (2 * math.pi * rec["f_hi_hz"])                  # 옛 1/(2π f_hi) 와 확실히 다름
    text = (o / f"{stem}.stab.cir").read_text(encoding="utf-8")
    pv, _ = pulse_of(text, "Vcl_nin")
    assert pv[2:6] == pytest.approx([pl["tmax"]] * 4, rel=1e-6), (pv, pl)
    tr = tran_line(text)
    assert tr[0] == pytest.approx(pl["tmax"], rel=1e-6) and tr[3] == pytest.approx(pl["tmax"], rel=1e-6)
    assert tr[1] == pytest.approx(pl["tstop"], rel=1e-6)
    dec = decide(o / f"{stem}.stab.txt", pl)
    assert st["transient"]["status"] == dec["status"] and st["transient"]["first_status"] == dec["first"], dec
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
    assert cmp["summary"]["verdict"] == "INCOMPLETE", cmp["summary"]
