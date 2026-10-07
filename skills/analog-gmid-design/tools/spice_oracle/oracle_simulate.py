# -*- coding: utf-8 -*-
"""oracle_simulate.py -- ngspice 배치 실행 + .op/.ac 결과 추출.

진입점(단독 실행):
    python oracle_simulate.py <netlist.cir> <out_sim.json> --ngspice <ngspice_con.exe> [--timeout-s S] [--cache-dir D]

  <netlist.cir>.meta.json(oracle_netlist.py 가 씀)을 읽어 probe 이름을 알고, ngspice -b 를 돌려
  .op(소자별 id/gm/gds/vth/vdsat/vgs/vds/vbs, 넷 전압, 레일 공급전류, forced 고정원 전류)와
  .ac(wrdata 파일 -> dc gain, f-3dB, UGF, PM)를 sim JSON 으로 쓴다.

공개 함수: run_ngspice(exe, cir, log, timeout_s, cache_dir, outputs), parse_op(log_text, meta), parse_ac_file(path),
          ac_measures(freq, re, im), pm_crosscheck(freq, re, im, mp_res), data_rel_resolution(path),
          mp_resolution(rel_resolution, values_per_sample), run_cache_key(exe, cir_path),
          ratio_measure(run, folder), rout_measure(run, folder), loop_choke_ratio(i_file, nets, weights, choke_H),
          simulate(cir_path, meta, exe, timeout_s, cache_dir),
          [신규 C10] nyquist_count(freq, L), gain_crossings(freq, L), thermal_voltage(temp_c), solver_floor(options, v_ops),
          tran_plan(crossings, temp_c, floor, file), transient_decision(path, plan), stability_judgement(nyq, status),
          stability_check(cir, meta, op, Ldata, exe, ...), apply_stability(res, cir, meta, Ldata, exe, ...)
[신규 C10] PM 안정성 근거: PM 원값이 있으면 Nyquist 감은 수 N(측정 L) + 폐루프 .tran(<stem>.stab.cir)로 개루프 RHP 극 수
  P = Z - N 을 추론하고, P = 0 이 증명되지 않으면 ac.pm_deg = None + ac.pm_undefined(이유), 원값 ac.pm_deg_raw. README C10.
[신규] C26 rout_ohm: meta.rout_runs 의 데이터 파일(.ac 한 점, 감지 노드 단위 AC 전류)에서 sim.rout 를 만든다
  (rout_ohm = Re(V/I), 음수면 None + undefined, C21 캐시에 함께 저장·복원).
[신규] C27 기록: ac.dc_path_isolation(넷리스트 meta), ac.loop_choke_ratio(β 루프 2회 실행 첫 점), ac.loop_break_nets·loop_weights.
[신규] C24 ratio_db(CMRR·PSRR): 넷리스트 meta.ratio_runs 의 num/den 데이터 파일(.ac 한 점)에서 sim.ratio 를 만든다
  (데이터 파일은 C21 캐시에 함께 저장·복원).
[신규] PM 교차 측정(C20, 기록만): PM 을 정한 루프 이득 L 로 폐루프 L/(1+L) 의 peaking Mp 를 재고 2차계 관계로 PM 을 역산해
  ac.pm_crosscheck_deg 로 남긴다(ac.pm_deg 와 다른 측정 방법 -- 교차점·위상 언랩 오류 검출용, 판정 무관).
[신규] 실행 캐시(C21, 선택): cache_dir 가 있으면 (넷리스트 바이트, 넷리스트가 .include/.lib 로 읽는 모델 파일 전부의 바이트
  (재귀), ngspice 실행 파일 경로, 명령 '-b') sha256 을 키로 로그·출력 데이터 파일을 저장하고 같은 키면 ngspice 를 다시
  돌리지 않는다. 모델 파일을 하나라도 못 찾으면 캐시를 쓰지 않는다.

부호 규칙(출력)
  * 소자 값은 ngspice 원값. BSIM4 @ 값은 극성 정규화돼 있다(PMOS 도 id/vgs/vds 양수, vbs=type*(Vb-Vs)).
  * rail_current_A[net] = 그 레일 전압원이 회로에 공급하는 전류 = -i(Vrail).
  * hold_current_A[net] = forced 고정원으로 그 넷에서 빠져나가는 전류 = i(Vhold) (KCL 잔차).
  * 개루프 A(H = 출력/입력 AC): gain_dc = |H(f_first)|, f-3dB = |H| < |H(f_first)|/sqrt(2) 인 첫 주파수 점(보간 없음),
    UGF = |H|=1 첫 하강 교차(log-log 보간).
  * PM(위상여유, README "PM 정의"): 루프 이득 L 에 대해 PM = 180 - (DC 위상 - |L|=1 교차 위상) [deg].
    feedback_passives 선언이 있으면 L = β 루프 이득 T(루프 넷리스트, Middlebrook 이중 주입 loop_gain()),
    없으면 L = A(β=1). ac.pm_deg 가 그 값, ac.pm_open_loop_deg 는 늘 A 기준 값, ac.pm_definition = beta_loop|beta_1.
  * 넷리스트 meta 에 막힘이 있으면 ngspice 를 돌리지 않는다(skipped).
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # [신규 C10] oracle_netlist 공개 함수(python -P 실행 대비)

_NUM = r"([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)"


_INC = re.compile(r"""^\s*\.(?:include|inc|lib)\s+["']?([^"'\s]+)["']?""", re.I)


def _model_files(path, seen):
    """path 가 .include/.lib 로 읽는 파일을 재귀로 모은다(상대 경로는 그 파일 폴더 기준). 못 찾으면 False."""
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    for ln in lines:
        m = _INC.match(ln)
        if not m:
            continue
        q = m.group(1)
        q = q if os.path.isabs(q) else os.path.join(os.path.dirname(os.path.abspath(path)), q)
        q = os.path.normcase(os.path.abspath(q))
        if q in seen:
            continue
        if not os.path.exists(q):
            return False
        seen.add(q)
        if not _model_files(q, seen):
            return False
    return True


def run_cache_key(exe, cir_path):
    """실행 캐시 키 sha256(넷리스트 바이트 + 모델 파일(재귀) 경로·바이트 + ngspice 경로 + '-b'). 모델 파일을 못 찾으면 None."""
    import hashlib
    seen = set()
    if not _model_files(cir_path, seen):
        return None
    h = hashlib.sha256()
    with open(cir_path, "rb") as f:
        h.update(f.read())
    for q in sorted(seen):
        h.update(q.encode("utf-8"))
        with open(q, "rb") as f:
            h.update(hashlib.sha256(f.read()).digest())
    h.update(os.path.abspath(exe).encode("utf-8"))
    h.update(b"-b")
    return h.hexdigest()


def run_ngspice(exe, cir_path, log_path, timeout_s=None, cache_dir=None, outputs=()):
    """ngspice -b 실행. 반환 (rc, 로그 텍스트, 캐시 상태 None|'hit'|'miss'|'off(모델 파일 못 찾음)').
    outputs = 넷리스트가 cir 폴더에 쓰는 데이터 파일 이름(캐시에 함께 저장·복원)."""
    import shutil
    d = os.path.dirname(os.path.abspath(cir_path))
    key = run_cache_key(exe, cir_path) if cache_dir else None
    state = None if not cache_dir else ("off(모델 파일 못 찾음)" if key is None else "miss")
    slot = os.path.join(cache_dir, key) if key else None
    if slot and os.path.exists(os.path.join(slot, "done")):
        for o in outputs:
            src = os.path.join(slot, os.path.basename(o))
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(d, o))
        shutil.copyfile(os.path.join(slot, "ngspice.log"), log_path)
        with open(os.path.join(slot, "rc"), encoding="utf-8") as f:
            rc = int(f.read().strip())
        with open(log_path, encoding="utf-8", errors="replace") as f:
            return rc, f.read(), "hit"
    with open(log_path, "w", encoding="utf-8", errors="replace") as fo:
        r = subprocess.run([exe, "-b", os.path.basename(cir_path)], cwd=d,
                           stdout=fo, stderr=subprocess.STDOUT, timeout=timeout_s)
    if slot:
        os.makedirs(slot, exist_ok=True)
        for o in outputs:
            if os.path.exists(os.path.join(d, o)):
                shutil.copyfile(os.path.join(d, o), os.path.join(slot, os.path.basename(o)))
        shutil.copyfile(log_path, os.path.join(slot, "ngspice.log"))
        with open(os.path.join(slot, "rc"), "w", encoding="utf-8") as f:
            f.write(str(r.returncode))
        with open(os.path.join(slot, "done"), "w", encoding="utf-8") as f:
            f.write(os.path.abspath(cir_path))
    with open(log_path, encoding="utf-8", errors="replace") as f:
        return r.returncode, f.read(), state


def _grab(text, expr):
    m = re.search(r"^\s*" + re.escape(expr) + r"\s*=\s*" + _NUM, text, re.I | re.M)
    return float(m.group(1)) if m else None


def parse_op(log, meta):
    devices = {}
    for name, pr in meta["probes"].items():
        devices[name] = {p: _grab(log, expr) for p, expr in pr.items()}
    nodes = {}
    for net in meta["nets"]:
        nodes[net] = _grab(log, f"v({meta['spice_node'][net].lower()})")
    rails = {}
    for net, src in meta["rail_sources"].items():
        v = _grab(log, f"i({src.lower()})")
        rails[net] = None if v is None else -v
    hold = {}
    for net in meta["held"]:
        hold[net] = _grab(log, f"i(vhold_{net.lower()})")
    return {"devices": devices, "nodes": nodes, "rail_current_A": rails, "hold_current_A": hold}


def parse_ac_file(path):
    if not path or not os.path.exists(path):
        return None
    fr, re_, im = [], [], []
    with open(path) as f:
        for line in f:
            parts = line.split()
            try:
                vals = [float(x) for x in parts]
            except ValueError:
                continue
            if len(vals) >= 3:
                fr.append(vals[0]); re_.append(vals[1]); im.append(vals[2])
    return (fr, re_, im) if fr else None


def ac_measures(freq, re_, im, ref="first"):
    """기준점(DC 대용) = 첫 주파수 점. ref='peak' 이면 |H| 최대 점(진단용, 오라클 판정 경로에서는 쓰지 않음)."""
    import numpy as np
    f = np.asarray(freq)
    H = np.asarray(re_) + 1j * np.asarray(im)
    mag = np.abs(H)
    ph = np.unwrap(np.angle(H))
    k0 = int(np.argmax(mag)) if ref == "peak" else 0
    out = {"f_first_hz": float(f[k0]), "gain_dc": float(mag[k0]), "dc_gain_db": float(20 * np.log10(mag[k0])),
           "phase_dc_deg": float(np.degrees(ph[k0])), "reference_point": ref}
    i3 = np.where(mag[k0:] < mag[k0] / math.sqrt(2))[0]
    out["f3db_hz"] = float(f[k0 + i3[0]]) if len(i3) else None
    iu = np.where(mag[k0:] < 1.0)[0]
    if len(iu) and iu[0] > 0:
        k = k0 + iu[0]
        lf = np.interp(0.0, [np.log10(mag[k]), np.log10(mag[k - 1])], [np.log10(f[k]), np.log10(f[k - 1])])
        phu = np.interp(lf, [np.log10(f[k - 1]), np.log10(f[k])], [ph[k - 1], ph[k]])
        lag = math.degrees(ph[k0] - phu)
        out["ugf_hz"] = float(10 ** lf)
        out["phase_lag_at_ugf_deg"] = float(lag)
        out["pm_deg"] = float(180.0 - lag)
    else:
        out["ugf_hz"] = None
        out["phase_lag_at_ugf_deg"] = None
        out["pm_deg"] = None
    out["a0_f3db_hz"] = out["gain_dc"] * out["f3db_hz"] if out["f3db_hz"] else None
    return out


def data_rel_resolution(path):
    """wrdata 데이터 파일의 상대 분해능 u = 0.5 * 10^(1-d) (d = 파일에 찍힌 가수 유효숫자 수의 최솟값, 반올림 반 단위).
    ngspice 가 실제로 쓴 출력 자릿수에서 읽는다(상수 없음). 숫자가 없거나 파일이 없으면 None."""
    if not path or not os.path.exists(path):
        return None
    d_min = None
    with open(path) as f:
        for line in f:
            for tok in line.split():
                mant = re.split(r"[eE]", tok.lstrip("+-"), maxsplit=1)[0]
                if not re.fullmatch(r"[0-9]+\.?[0-9]*|\.[0-9]+", mant):
                    continue
                digits = mant.replace(".", "").lstrip("0")
                if digits and (d_min is None or len(digits) < d_min):
                    d_min = len(digits)
    return None if d_min is None else 0.5 * 10.0 ** (1 - d_min)


def mp_resolution(rel_resolution, values_per_sample):
    """Mp = |C(f_k)|/|C(f_0)| 의 분해능. 두 표본 각각이 데이터 파일의 실수 values_per_sample 개로 만들어지고 각 값의
    상대 반올림 오차가 rel_resolution 이하이므로 1차 오차 한계 = (모은 값 개수 2*values_per_sample) * rel_resolution.
    엔진 metrics/pencil_roots 의 원점 고유값 판정 |alpha| <= 차원*eps*||A||_F 와 같은 꼴(개수 * 단위 반올림 * 크기,
    Mp ~ 1 이라 크기 1). 오라클은 엔진을 import 하지 않으므로(C1) 식만 같게 쓴다."""
    return None if rel_resolution is None else 2 * values_per_sample * rel_resolution


def pm_crosscheck(freq, re_, im, mp_res=None):
    """PM 교차 측정(기록만): 루프 이득 L 에서 폐루프 C = L/(1+L), peaking Mp = max|C| / |C(f_first)|.
    2차계 관계 Mp = 1/(2 z sqrt(1-z^2)) 로 z 를 풀고 PM = atan(2z / sqrt(sqrt(1+4z^4) - 2z^2)) [deg].
    Mp <= 1 + mp_res(첫 점 뒤로 데이터 분해능보다 크게 솟지 않음, mp_res = mp_resolution())이면 z >= 1/sqrt(2) 라
    PM 은 그 z 의 PM 이상이라는 것만 알 수 있다 -> 값 None + 하한. mp_res 가 None 이면 분해능 0(정확한 입력)."""
    import numpy as np
    L = np.asarray(re_) + 1j * np.asarray(im)
    C = np.abs(L / (1.0 + L))
    k = int(np.argmax(C))
    mp = float(C[k] / C[0]) if C[0] > 0 else None
    tol = mp_res or 0.0

    def pm_of(z):
        return math.degrees(math.atan2(2 * z, math.sqrt(math.sqrt(1 + 4 * z ** 4) - 2 * z ** 2)))
    out = {"closed_loop_peaking_db": None if not mp else 20 * math.log10(mp),
           "closed_loop_peak_hz": float(freq[k]), "pm_crosscheck_deg": None,
           "pm_crosscheck_method": "closed_loop_peaking_2nd_order", "pm_crosscheck_mp_resolution": mp_res}
    if mp is None:
        out["pm_crosscheck_note"] = "폐루프 첫 점 크기 0 -- 계산 불가"
    elif k == 0 or mp <= 1.0 + tol:
        out["closed_loop_peaking_db"] = None
        out["closed_loop_peak_hz"] = None
        out["pm_crosscheck_note"] = (f"peaking 없음(Mp-1 = {mp - 1:.3g}, 데이터 분해능 {tol:.3g} 이하) -- "
                                     f"2차 근사로 PM >= {pm_of(1 / math.sqrt(2)):.4g} deg")
    else:
        z = math.sqrt((1 - math.sqrt(1 - 1 / mp ** 2)) / 2)
        out["pm_crosscheck_deg"] = pm_of(z)
        out["pm_crosscheck_note"] = None
    return out


def _cols(path):
    """wrdata(wr_singlescale) 파일 -> (주파수 목록, [복소 열 목록])."""
    if not path or not os.path.exists(path):
        return None
    fr, cols = [], []
    with open(path) as f:
        for line in f:
            try:
                vals = [float(x) for x in line.split()]
            except ValueError:
                continue
            if len(vals) < 3:
                continue
            fr.append(vals[0])
            cols.append([complex(vals[i], vals[i + 1]) for i in range(1, len(vals) - 1, 2)])
    return (fr, cols) if fr else None


def loop_gain(v_file, i_file, weights):
    """Middlebrook 이중 주입 루프 이득. 끊은 넷 k 마다 x=되먹임 쪽(lbx), y=증폭기 쪽.
    Tv = -sum(w*vx)/sum(w*vy) (직렬 전압 주입), Ti = sum(w*ix)/sum(w*(w - ix)) (전류 w 주입, ix = 되먹임 쪽으로
    가는 전류 = i(Vlb)), T = (Tv*Ti - 1)/(Tv + Ti + 2). 반환 (주파수, T 실수부, T 허수부) 또는 None."""
    v, i = _cols(v_file), _cols(i_file)
    if v is None or i is None or len(v[0]) != len(i[0]):
        return None
    re_, im = [], []
    for row_v, row_i in zip(v[1], i[1]):
        vx = sum(w * row_v[2 * k] for k, w in enumerate(weights))
        vy = sum(w * row_v[2 * k + 1] for k, w in enumerate(weights))
        ix = sum(w * row_i[k] for k, w in enumerate(weights))
        iy = sum(w * (w - row_i[k]) for k, w in enumerate(weights))
        tv, ti = -vx / vy, ix / iy
        t = (tv * ti - 1) / (tv + ti + 2)
        re_.append(t.real)
        im.append(t.imag)
    return v[0], re_, im


def ratio_measure(run, folder):
    """C24: ratio_db 뷰 한 개의 두 .ac 결과(wrdata 한 점) -> {view, f_hz, num{re, im, mag}, den{...}, ratio_db}.
    ratio_db = 20*log10(|H_num|/|H_den|). 파일이 없거나 |H_den| = 0 이면 ratio_db None."""
    out = {"view": run["view"], "f_hz": run["f_hz"], "num": None, "den": None, "ratio_db": None}
    for side in ("num", "den"):
        raw = parse_ac_file(os.path.join(folder, run[f"{side}_file"]))
        if raw:
            re_, im = raw[1][0], raw[2][0]
            out[side] = {"re": re_, "im": im, "mag": math.hypot(re_, im), "f_hz": raw[0][0]}
    if out["num"] and out["den"] and out["den"]["mag"] > 0 and out["num"]["mag"] > 0:
        out["ratio_db"] = 20 * math.log10(out["num"]["mag"] / out["den"]["mag"])
    return out


ROUT_NEGATIVE = "negative_real_part"


def rout_measure(run, folder):
    """C26: rout_ohm 뷰 한 개의 .ac 한 점(감지 노드 단위 AC 전류) -> {view, f_hz, re, im, mag, rout_ohm, undefined}.
    H = V(sense_p) [- V(sense_n)] 를 주입 전류 1 A 로 나눈 값이 임피던스이고 rout_ohm = Re(H)(엔진 rout_ss_ohm 의 ω -> 0
    실수 값과 같은 쪽). Re(H) < 0 이면 rout_ohm None + undefined = 'negative_real_part'(정의 불가 -- 엔진 결정: 음의 출력
    저항은 통과하지 않는다), 파일이 없으면 None + 'no_data'."""
    out = {"view": run["view"], "f_hz": run["f_hz"], "re": None, "im": None, "mag": None, "rout_ohm": None,
           "undefined": None}
    raw = parse_ac_file(os.path.join(folder, run["file"]))
    if not raw:
        out["undefined"] = "no_data"
        return out
    re_, im = raw[1][0], raw[2][0]
    out.update(re=re_, im=im, mag=math.hypot(re_, im), f_hz=raw[0][0])
    if re_ < 0:
        out["undefined"] = ROUT_NEGATIVE
    else:
        out["rout_ohm"] = re_
    return out


def loop_choke_ratio(i_file, break_nets, weights, choke_H):
    """C27 기록(판정 아님): β 루프 2회(전류 주입) 실행의 첫 점(fstart)에서 끊은 넷 k 마다
    |jω·L_choke| / |V(n_k)/w_k| (w_k = 그 넷 주입 전류 진폭). >> 1 이면 choke 가 측정 대역에서 열린 것으로 본다.
    반환 [{net, f_hz, choke_H, node_impedance_ohm, ratio}] 또는 None(파일·choke 없음). w_k = 0 이면 그 넷 ratio None."""
    c = _cols(i_file)
    nb = len(break_nets)
    if c is None or choke_H is None or not c[1] or len(c[1][0]) < 2 * nb:
        return None
    f0, row = c[0][0], c[1][0]
    out = []
    for k, net in enumerate(break_nets):
        w = weights[k]
        z = None if not w else abs(row[nb + k] / w)
        zl = 2 * math.pi * f0 * float(choke_H)
        out.append({"net": net, "f_hz": f0, "choke_H": float(choke_H), "node_impedance_ohm": z,
                    "ratio": None if not z else zl / z})
    return out


# ---------------------------------------------------------------- [신규 C10 안정성] PM 이 안정 여유인가
# PM = 180 - (기준점 위상 - |L|=1 위상) 은 개루프 L 에 RHP 극이 없을 때(P = 0)만 안정 여유다(Nyquist: Z = N + P,
# Z = 폐루프 RHP 극 수, N = 1+L 이 원점을 시계 방향으로 감는 수). 오라클은 N 을 측정 L(jω) 에서 세고(SPICE .ac),
# Z > 0 여부를 폐루프 .tran 으로 본다(SPICE). 둘로 P 를 추론하고, P = 0 이 증명될 때만 PM 을 값으로 둔다.
PM_UNDEFINED_RHP = "open_loop_rhp_poles"
PM_UNDEFINED_CL_UNSTABLE = "closed_loop_unstable"
PM_UNDEFINED_INCONSISTENT = "stability_evidence_inconsistent"
PM_UNDEFINED_NO_NYQUIST = "nyquist_count_unavailable"
PM_UNDEFINED_UNVERIFIED = "stability_unverified"
# 물리 상수(SI 2019 정의값) -- 킥 진폭 V_T = k_B*T/q 용
_K_B = 1.380649e-23
_Q_E = 1.602176634e-19
_T0_K = 273.15
# ngspice 의 기본 수렴 허용오차(입력 .option 에 없을 때 ngspice 가 실제로 쓰는 값; ngspice 매뉴얼 .options)
_NGSPICE_DEFAULT_TOL = {"reltol": 1e-3, "vntol": 1e-6}


def nyquist_count(freq, L):
    """측정 L(jω)(ω = 2π·freq, freq 오름차순)로 1+L 이 원점(= L 이 -1)을 **시계 방향**으로 감는 수 N(Z - P).
    닫힌 곡선 = 켤레 반쪽(ω: -f_last -> -f_first) + 측정 반쪽(f_first -> f_last), 두 끝은 직선(저주파: conj L(f_first)
    -> L(f_first), 고주파: L(f_last) -> conj L(f_last))으로 잇는다. 감은 수 = 표본 사이 1+L 편각 변화(±π 로 접음)의 합/2π.
    유효 조건(데이터에서 판정, 아니면 N = None + 이유):
      * |L(f_last)| < 1 -- 스윕 위 꼬리(f > f_last)가 단위원 안이라 -1 을 감을 수 없다(측정 정의의 UGF 와 같은 가정).
      * 모든 표본 간격(두 닫는 직선 포함)에서 1+L 편각 변화 < π/2 -- 접기 모호성(π)의 절반 여유. 넘으면 그 근처에서
        스윕 밀도가 부족해 곡선이 -1 의 어느 쪽을 지났는지 모른다.
    반환 {encirclements_cw, reason, max_step_deg, max_step_hz, f_first_hz, f_last_hz, L_first, L_last}."""
    import numpy as np
    f = np.asarray(freq, float)
    L = np.asarray(L, complex)
    out = {"encirclements_cw": None, "reason": None, "max_step_deg": None, "max_step_hz": None,
           "f_first_hz": float(f[0]), "f_last_hz": float(f[-1]),
           "L_first": [float(L[0].real), float(L[0].imag)], "L_last": [float(L[-1].real), float(L[-1].imag)]}
    if abs(L[-1]) >= 1:
        out["reason"] = (f"|L(f_last={f[-1]:.4g} Hz)| = {abs(L[-1]):.4g} >= 1 -- 스윕 위 꼬리가 -1 을 감을 수 있어 "
                         f"감은 수를 셀 수 없다(fstop_hz 부족)")
        return out
    z = np.concatenate([np.conj(L[::-1]), L]) + 1.0
    fz = np.concatenate([-f[::-1], f])
    if np.any(z == 0):
        out["reason"] = "L = -1 인 표본이 있다(감은 수 정의 불가)"
        return out
    ang = np.angle(z)
    d = np.diff(np.append(ang, ang[0]))
    d = (d + np.pi) % (2 * np.pi) - np.pi
    k = int(np.argmax(np.abs(d)))
    out["max_step_deg"] = float(np.degrees(abs(d[k])))
    out["max_step_hz"] = float(abs(fz[k]))
    if abs(d[k]) >= np.pi / 2:
        out["reason"] = (f"{abs(fz[k]):.4g} Hz 근처 표본 간격에서 1+L 편각이 {np.degrees(abs(d[k])):.1f} deg 바뀐다(>= 90) -- "
                         f"스윕 밀도 부족으로 -1 의 어느 쪽을 지났는지 모른다(points_per_decade 부족)")
        return out
    out["encirclements_cw"] = -int(round(float(d.sum()) / (2 * np.pi)))
    return out


def gain_crossings(freq, L):
    """|L| = 1 교차 주파수 전부(위·아래 방향, log f 대 log|L| 선형 보간). 오름차순."""
    import numpy as np
    f = np.asarray(freq, float)
    m = np.abs(np.asarray(L, complex))
    out = []
    for k in range(len(f) - 1):
        if (m[k] - 1) * (m[k + 1] - 1) < 0:
            a, b = math.log10(m[k]), math.log10(m[k + 1])
            out.append(10 ** (math.log10(f[k]) + a / (a - b) * (math.log10(f[k + 1]) - math.log10(f[k]))))
    return out


def thermal_voltage(temp_c):
    """V_T = k_B*T/q [V] (T = temp_c + 273.15 K)."""
    return _K_B * (float(temp_c) + _T0_K) / _Q_E


def solver_floor(options, v_ops):
    """ngspice 가 이 넷리스트에서 구분하는 전압 크기(해 분해능) = 관측 노드마다 reltol*|V_op| + vntol 의 합.
    reltol·vntol 은 입력 testbench.options 값, 없으면 ngspice 기본값(_NGSPICE_DEFAULT_TOL -- 실제로 쓰이는 값)."""
    o = {k.lower(): v for k, v in (options or {}).items()}
    rel = float(o.get("reltol", _NGSPICE_DEFAULT_TOL["reltol"]))
    vn = float(o.get("vntol", _NGSPICE_DEFAULT_TOL["vntol"]))
    return sum(rel * abs(v) + vn for v in v_ops)


def tran_plan(crossings_hz, temp_c, floor_v, file_name):
    """폐루프 과도 계획(전부 측정 L 과 입력에서 유도, 조정 상수 없음):
      kick_V = V_T(.temp)  -- 소신호 선형화의 물리 척도(exp(v/V_T) 1차), 해 분해능 floor 보다 커야 한다.
      tmax = 1/(2π f_hi)   -- f_hi = 가장 높은 |L|=1 교차(폐루프 진동은 |L| >= 1 인 주파수에서만 생긴다)의 1 rad 시간.
      킥 = PULSE(td = tr = tf = tmax, pw = 1/(2π f_lo)) -- f_lo = 가장 낮은 |L|=1 교차, 지배 루프 동특성을 1 rad 동안 민다.
      창 W = 1/f_lo(가장 느린 교차의 한 주기), 창 수 K = ceil(ln(kick_V/floor)) -- 창마다 1 e-fold 감쇠하면 킥 크기가
      해 분해능에 닿는 창 수. K < 2 면 비교할 수 없어 계획 없음(None)."""
    f_lo, f_hi = min(crossings_hz), max(crossings_hz)
    kick = thermal_voltage(temp_c)
    if not floor_v or floor_v <= 0 or kick <= floor_v:
        return None
    K = math.ceil(math.log(kick / floor_v))
    if K < 2:
        return None
    tmax = 1 / (2 * math.pi * f_hi)
    pw = 1 / (2 * math.pi * f_lo)
    W = 1 / f_lo
    t_end = tmax + tmax + pw + tmax
    return {"kick_V": kick, "td": tmax, "tr": tmax, "pw": pw, "tmax": tmax, "window_s": W, "windows": K,
            "t_kick_end": t_end, "tstop": t_end + K * W, "f_lo_hz": f_lo, "f_hi_hz": f_hi, "floor_V": floor_v,
            "file": file_name}


def transient_decision(path, plan):
    """폐루프 과도 판정. e(t) = H(t) - H(0)(H(0) = 동작점), 킥이 끝난 뒤 창 j = 1..K 의 M_j = max|e|.
    floor = plan.floor_V + (데이터 파일 반올림 u*max|H|).
      M_K <= floor           -> stable(해 분해능 아래로 감쇠)
      M_K >= M_1             -> unstable(K 창 동안 줄지 않음 = 증가 또는 지속 진동)
      M_K <  M_{K-1}         -> stable(끝 창까지 감쇠 중)
      그 밖(줄었다 다시 커짐) -> undetermined.
    반환 {status, M, floor_V, reason}."""
    out = {"status": "failed", "M": None, "floor_V": None, "reason": None}
    if not path or not os.path.exists(path):
        out["reason"] = "과도 데이터 파일 없음"
        return out
    t, v = [], []
    with open(path) as f:
        for line in f:
            try:
                vals = [float(x) for x in line.split()]
            except ValueError:
                continue
            if len(vals) >= 2:
                t.append(vals[0])
                v.append(vals[1])
    u = data_rel_resolution(path) or 0.0
    # 넷리스트 tstop(10 자리)과 파일 시각(wrdata 자릿수)의 반올림 차는 파일 분해능 u 의 두 배 안
    if len(t) < 2 or t[-1] < plan["tstop"] * (1 - 2 * u):
        out["reason"] = f"과도가 tstop 까지 가지 않았다(마지막 t = {t[-1] if t else None})"
        return out
    floor = plan["floor_V"] + u * max(abs(x) for x in v)
    M = []
    for j in range(plan["windows"]):
        a = plan["t_kick_end"] + j * plan["window_s"]
        b = a + plan["window_s"]
        seg = [abs(x - v[0]) for tt, x in zip(t, v) if a <= tt <= b]
        if not seg:
            out["reason"] = f"창 {j + 1} 에 표본이 없다"
            return out
        M.append(max(seg))
    out.update(M=M, floor_V=floor)
    if M[-1] <= floor:
        out.update(status="stable", reason="끝 창 응답이 해 분해능 아래로 감쇠")
    elif M[-1] >= M[0]:
        out.update(status="unstable", reason="K 창 동안 응답이 줄지 않음(증가 또는 지속 진동)")
    elif M[-1] < M[-2]:
        out.update(status="stable", reason="끝 창까지 감쇠 중")
    else:
        out.update(status="undetermined", reason="응답이 줄었다가 끝 창에서 다시 커짐(맥놀이 또는 늦게 자라는 모드)")
    return out


def stability_judgement(nyq, tran_status):
    """Nyquist N(Z - P)과 폐루프 과도 상태로 PM 이 안정 여유인지 정한다(P = 0 이 증명될 때만 유효).
    반환 {closed_loop, open_loop_rhp_poles, open_loop_rhp_poles_bound, pm_valid, pm_undefined}."""
    N = nyq.get("encirclements_cw") if nyq else None
    S = tran_status if tran_status in ("stable", "unstable") else None
    r = {"closed_loop": S, "open_loop_rhp_poles": None, "open_loop_rhp_poles_bound": None, "pm_valid": False,
         "pm_undefined": None}
    if S == "stable":
        if N is None:
            r["pm_undefined"] = PM_UNDEFINED_NO_NYQUIST
        elif N == 0:
            r.update(open_loop_rhp_poles=0, open_loop_rhp_poles_bound="==", pm_valid=True)
        elif N < 0:
            r.update(open_loop_rhp_poles=-N, open_loop_rhp_poles_bound="==", pm_undefined=PM_UNDEFINED_RHP)
        else:
            r["pm_undefined"] = PM_UNDEFINED_INCONSISTENT
    elif S == "unstable":
        if N is not None and N <= 0:
            r.update(open_loop_rhp_poles=1 - N, open_loop_rhp_poles_bound=">=", pm_undefined=PM_UNDEFINED_RHP)
        else:
            r["pm_undefined"] = PM_UNDEFINED_CL_UNSTABLE
    else:
        if N is not None and N >= 1:
            r.update(closed_loop="unstable", pm_undefined=PM_UNDEFINED_CL_UNSTABLE)
        elif N is not None and N < 0:
            r.update(open_loop_rhp_poles=-N, open_loop_rhp_poles_bound=">=", pm_undefined=PM_UNDEFINED_RHP)
        else:
            r["pm_undefined"] = PM_UNDEFINED_UNVERIFIED
    return r


def stability_check(cir_path, meta, op, Ldata, exe, timeout_s=None, cache_dir=None):
    """PM 을 정한 루프 L 의 안정성 근거(C10). β 루프면 L = T(실제 루프), β=1 이면 L = sign*A(sign = 기준점 Re A 의 부호,
    PM 정의가 가정하는 음되먹임 닫기). Nyquist N(nyquist_count) + 폐루프 .tran(stability_netlist, transient_decision)
    -> stability_judgement. 동작점 패스 <stem>.stabop.cir(choke 전류·노드 전압), 과도 넷리스트 <stem>.stab.cir,
    데이터 <stem>.stab.txt(C21 캐시에 함께 저장·복원). op = 본 시뮬 결과(노드 전압, floor 용)."""
    import numpy as np
    from oracle_netlist import stability_netlist, stability_op_netlist
    f, re_, im = Ldata
    L = np.asarray(re_) + 1j * np.asarray(im)
    lm = meta.get("loop")
    mode = "beta_loop" if lm else "beta_1"
    sign = 1.0
    out = {"method": "nyquist_count + closed_loop_transient", "loop": mode, "closure_sign": None}
    if mode == "beta_1":
        sign = 1.0 if L[0].real > 0 else (-1.0 if L[0].real < 0 else 0.0)
    out["closure_sign"] = sign
    nyq = nyquist_count(f, sign * L) if sign else {"encirclements_cw": None,
                                                   "reason": "기준점 Re A = 0 -- 음되먹임 닫기 부호를 정할 수 없다"}
    out["nyquist"] = nyq
    d = os.path.dirname(os.path.abspath(cir_path))
    stem = os.path.splitext(os.path.basename(cir_path))[0]
    tr = {"status": "not_run", "reason": None}
    outs = meta.get("outputs") or []
    cr = gain_crossings(f, L)
    temp = (meta.get("lut_meta") or {}).get("temp_c")
    nodes = (op or {}).get("nodes") or {}
    v_ops = [nodes.get(n) for n in outs]
    if not sign:
        tr["reason"] = "닫기 부호 없음"
    elif not outs or not meta.get("output_nodes"):
        tr["reason"] = "넷리스트 meta 에 출력 노드 없음"
    elif not cr or temp is None or any(v is None for v in v_ops):
        tr["reason"] = "|L|=1 교차·.temp·출력 동작점 중 없는 것이 있다"
    else:
        plan = tran_plan(cr, temp, solver_floor(meta.get("tb_options"), v_ops), f"{stem}.stab.txt")
        if plan is None:
            tr["reason"] = "킥 V_T 가 해 분해능에 비해 작아 비교 창을 만들 수 없다"
        else:
            plan["sign"] = sign
            sn = meta.get("spice_node") or {}
            plan["input_nodes"] = {n: sn[n] for n in meta.get("inputs") or [] if n in sn}
            src = os.path.join(d, lm["netlist"]) if lm else cir_path
            with open(src, encoding="utf-8") as fh:
                text = fh.read()
            # 동작점 패스: 같은 본문의 .op 로 choke 전류와 (입력·출력·choke 회로 쪽) 노드 전압
            otext, chokes, onodes = stability_op_netlist(
                text, list(plan["input_nodes"].values()) + list(meta["output_nodes"]))
            ocir = os.path.join(d, f"{stem}.stabop.cir")
            with open(ocir, "w", encoding="utf-8") as fh:
                fh.write(otext)
            orc, olog, ocst = run_ngspice(exe, ocir, os.path.splitext(ocir)[0] + ".log", timeout_s, cache_dir, [])
            plan["choke_I"] = {c.lower(): _grab(olog, f"i({c.lower()})") for c in chokes}
            plan["node_V"] = {n.lower(): _grab(olog, f"v({n.lower()})") for n in onodes}
            tr["op_pass"] = {"netlist": os.path.basename(ocir), "ngspice_rc": orc, "cache": ocst,
                             "choke_current_A": plan["choke_I"], "node_V": plan["node_V"]}
            w = dict(zip(lm["break_nets"], lm["weights"])) if lm else dict(meta.get("input_ac_weights") or {})
            stext, missing = stability_netlist(text, mode, w, meta["output_nodes"], plan)
            tr["plan"] = {k: v for k, v in plan.items() if k not in ("file", "choke_I", "node_V", "input_nodes")}
            if missing or not w:
                tr.update(status="failed", reason=f"과도 넷리스트를 만들 수 없다(킥 넷·동작점 값 없음): {missing or '(가중 없음)'}")
            else:
                scir = os.path.join(d, f"{stem}.stab.cir")
                with open(scir, "w", encoding="utf-8") as fh:
                    fh.write(stext)
                sfile = os.path.join(d, plan["file"])
                if os.path.exists(sfile):
                    os.remove(sfile)
                rc, slog, cst = run_ngspice(exe, scir, os.path.splitext(scir)[0] + ".log", timeout_s, cache_dir,
                                            [plan["file"]])
                dec = transient_decision(sfile, plan)
                tr.update(dec)
                tr.update(netlist=os.path.basename(scir), file=plan["file"], ngspice_rc=rc, cache=cst)
    out["transient"] = tr
    out.update(stability_judgement(nyq, tr.get("status")))
    out["gain_crossings_hz"] = cr
    return out


def simulate(cir_path, meta, exe, timeout_s=None, cache_dir=None):
    base = os.path.splitext(cir_path)[0]
    log_path = base + ".log"
    ac_path = os.path.join(os.path.dirname(os.path.abspath(cir_path)), meta["ac_file"]) if meta.get("ac_file") else None
    if ac_path and os.path.exists(ac_path):
        os.remove(ac_path)
    runs = meta.get("ratio_runs") or []
    rruns = meta.get("rout_runs") or []
    d0 = os.path.dirname(os.path.abspath(cir_path))
    rfiles = [r[f"{s}_file"] for r in runs for s in ("num", "den")] + [r["file"] for r in rruns]
    for x in rfiles:
        if os.path.exists(os.path.join(d0, x)):
            os.remove(os.path.join(d0, x))
    if meta.get("blockers"):
        # 막힌 넷리스트는 돌리지 않는다(지어낸 값으로 채운 회로를 재지 않는다 -- README C2/C8)
        return {"skipped": "넷리스트 막힘: " + " | ".join(meta["blockers"]), "devices": {}, "nodes": {},
                "rail_current_A": {}, "hold_current_A": {}, "ngspice_rc": None, "log": None, "log_errors": [],
                "op_ok": False, "ac": None, "ac_file": None, "loop": None, "ratio": [], "rout": []}
    rc, log, cst = run_ngspice(exe, cir_path, log_path, timeout_s, cache_dir,
                               ([meta["ac_file"]] if meta.get("ac_file") else []) + rfiles)
    res = parse_op(log, meta)
    res["ngspice_rc"] = rc
    res["cache"] = {"main": cst, "loop": None}
    res["log"] = log_path
    errs = [ln.strip() for ln in log.splitlines() if re.search(r"error|fatal|singular|abort", ln, re.I)]
    res["log_errors"] = errs[:40]
    res["op_ok"] = any(v.get("id") is not None for v in res["devices"].values())
    raw = parse_ac_file(ac_path)
    res["ac"] = ac_measures(*raw) if raw else None
    res["ac_file"] = ac_path
    res["ratio"] = [ratio_measure(r, d0) for r in runs]
    res["rout"] = [rout_measure(r, d0) for r in rruns]
    res["loop"] = None
    lm = meta.get("loop")
    Ldata = None if lm else raw
    if lm:
        d = os.path.dirname(os.path.abspath(cir_path))
        lcir = os.path.join(d, lm["netlist"])
        vf, inf = os.path.join(d, lm["v_file"]), os.path.join(d, lm["i_file"])
        for x in (vf, inf):
            if os.path.exists(x):
                os.remove(x)
        lrc, llog, lcst = run_ngspice(exe, lcir, os.path.splitext(lcir)[0] + ".log", timeout_s, cache_dir,
                                      [lm["v_file"], lm["i_file"]])
        res["cache"]["loop"] = lcst
        t = loop_gain(vf, inf, lm["weights"])
        # T 한 표본 = 끊은 넷마다 v 파일 실수 4개(vx, vy 복소) + i 파일 실수 2개(ix 복소); 분해능은 두 파일 중 거친 쪽
        uv, ui = data_rel_resolution(vf), data_rel_resolution(inf)
        lres = mp_resolution(None if uv is None or ui is None else max(uv, ui), 6 * len(lm["weights"]))
        Ldata = t
        res["loop"] = {"ngspice_rc": lrc, "break_nets": lm["break_nets"],
                       "log_errors": [ln.strip() for ln in llog.splitlines()
                                      if re.search(r"error|fatal|singular|abort", ln, re.I)][:40],
                       "measures": ac_measures(*t) if t else None,
                       "pm_crosscheck": pm_crosscheck(*t, mp_res=lres) if t else None,
                       "choke_ratio": loop_choke_ratio(inf, lm["break_nets"], lm["weights"], lm.get("choke_H"))}
    if res["ac"] is not None:
        res["ac"]["pm_open_loop_deg"] = res["ac"]["pm_deg"]
        res["ac"]["dc_path_isolation"] = meta.get("dc_path_isolation")  # C27 기록(판정 아님)
        if lm:
            lt = (res["loop"] or {}).get("measures") or {}
            res["ac"]["pm_deg"] = lt.get("pm_deg")
            res["ac"]["pm_definition"] = "beta_loop"
            res["ac"]["loop_ugf_hz"] = lt.get("ugf_hz")
            res["ac"]["loop_gain_dc_db"] = lt.get("dc_gain_db")
            res["ac"]["loop_break_nets"] = list(lm["break_nets"])
            res["ac"]["loop_weights"] = dict(zip(lm["break_nets"], lm["weights"]))
            res["ac"]["loop_choke_ratio"] = (res["loop"] or {}).get("choke_ratio")
            xc = (res["loop"] or {}).get("pm_crosscheck") or {}
        else:
            res["ac"]["pm_definition"] = "beta_1"
            res["ac"]["loop_break_nets"] = []
            res["ac"]["loop_weights"] = dict(meta.get("input_ac_weights") or {})  # β=1: A 의 입력 여기 가중
            res["ac"]["loop_choke_ratio"] = None
            # A 한 표본 = 데이터 파일 실수 2개(출력/입력 복소)
            xc = pm_crosscheck(*raw, mp_res=mp_resolution(data_rel_resolution(ac_path), 2))
        res["ac"].update({k: xc.get(k) for k in ("pm_crosscheck_deg", "pm_crosscheck_note", "pm_crosscheck_method",
                                                 "pm_crosscheck_mp_resolution",
                                                 "closed_loop_peaking_db", "closed_loop_peak_hz")})
        pc, pm = res["ac"].get("pm_crosscheck_deg"), res["ac"].get("pm_deg")
        res["ac"]["pm_crosscheck_gap_deg"] = None if pc is None or pm is None else pc - pm
        apply_stability(res, cir_path, meta, Ldata, exe, timeout_s, cache_dir)
    return res


def apply_stability(res, cir_path, meta, Ldata, exe, timeout_s=None, cache_dir=None):
    """C10 [신규]: PM 값이 있으면 stability_check 를 돌려 ac.stability 에 남기고, P = 0 이 증명되지 않으면 PM 을 정의 불가로
    바꾼다 -- ac.pm_deg = None, ac.pm_undefined = 이유, ac.pm_deg_raw = Bode 식 원값. β=1 이면 pm_open_loop_deg 도 같은 양이라
    None. C20 교차 측정도 PM 이 아니므로 pm_crosscheck_deg·gap = None(원값 pm_crosscheck_deg_raw, note 에 이유)."""
    ac = res["ac"]
    ac["pm_undefined"] = None
    ac["pm_deg_raw"] = ac.get("pm_deg")
    if ac.get("pm_deg") is None or Ldata is None:
        ac["stability"] = {"method": "nyquist_count + closed_loop_transient", "pm_valid": None, "pm_undefined": None,
                           "reason": "PM 값 없음(|L|=1 하강 교차 없음 또는 루프 측정 없음) -- 검사 대상 아님"}
        return
    st = stability_check(cir_path, meta, res, Ldata, exe, timeout_s, cache_dir)
    # 캐시 상태는 결과가 아니다(C21: hit 이든 miss 든 ac 는 같아야 한다) -- sim.stability_cache 로 뺀다
    tr = st.get("transient") or {}
    res["stability_cache"] = {"op_pass": (tr.get("op_pass") or {}).pop("cache", None), "transient": tr.pop("cache", None)}
    ac["stability"] = st
    why = st.get("pm_undefined")
    if not why:
        return
    ac["pm_undefined"] = why
    ac["pm_deg"] = None
    if st["loop"] == "beta_1":
        ac["pm_open_loop_deg"] = None
    ac["pm_crosscheck_deg_raw"] = ac.get("pm_crosscheck_deg")
    ac["pm_crosscheck_deg"] = None
    ac["pm_crosscheck_gap_deg"] = None
    ac["pm_crosscheck_note"] = (f"정의 불가({why}) -- 개루프 RHP 극·불안정 폐루프에서는 peaking 역산이 위상여유가 아니다"
                                f"(원값 {ac['pm_crosscheck_deg_raw']})")


def main(argv=None):
    ap = argparse.ArgumentParser(description="ngspice 실행 + .op/.ac 추출")
    ap.add_argument("netlist")
    ap.add_argument("out_json")
    ap.add_argument("--ngspice", required=True, help="ngspice 콘솔 실행 파일 경로")
    ap.add_argument("--timeout-s", type=float, default=None)
    ap.add_argument("--cache-dir", default=None, help="[신규] 실행 캐시 폴더(C21)")
    a = ap.parse_args(argv)
    with open(a.netlist + ".meta.json", encoding="utf-8") as f:
        meta = json.load(f)
    res = simulate(a.netlist, meta, a.ngspice, a.timeout_s, a.cache_dir)
    with open(a.out_json, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("wrote", a.out_json, "op_ok=", res["op_ok"], "ac=", None if res["ac"] is None else
          {k: res["ac"][k] for k in ("dc_gain_db", "ugf_hz", "pm_deg")})
    return 0 if res["op_ok"] else 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
