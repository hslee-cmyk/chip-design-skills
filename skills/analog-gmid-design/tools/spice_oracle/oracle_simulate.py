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
          [신규 C10] nyquist_count(freq, L), nyquist_adaptive(freq, L, sample_fn), gain_crossings(freq, L), thermal_voltage(temp_c),
          solver_floor(options, v_ops), reltol_of(options), n_pp_of(reltol), band_f_crit(freq, L), stability_config(),
          tran_plan(crossings, temp_c, floor, file, f_crit_hz, reltol, wall_s_per_window), transient_decision(path, plan),
          early_unstable(M, floor2, reltol), limit_cycle_early(M, floor2, reltol), early_window(M, floor2, reltol),
          pz_poles(log), pz_rhp_count(poles, reltol, f_stop_hz), pz_check(...), stability_judgement(nyq, status, pm_raw, pz),
          stability_check(cir, meta, op, Ldata, exe, ...), apply_stability(res, cir, meta, Ldata, exe, ...)
[신규 C10] PM 안정성 근거: PM 원값이 있으면 Nyquist 감은 수 N(측정 L, 위상 펼침 + 적응 세분화) + 독립 `.pz` 로 잰 개루프 RHP 극 수 P 로
  Z = N + P 를 직접 구하고(P 를 못 믿을 때만 옛 추론표), 폐루프 .tran(<stem>.stab.cir, 창 단위 조기 종결)을 별도 증거로 같이 본다. 폐루프 과도 unstable
  (한계 사이클 포함) 또는 Z >= 1 이면 ac.stability.verdict = unstable(FAIL), P = 0 이 증명되지 않으면 ac.pm_deg = None + ac.pm_undefined(이유),
  원값 ac.pm_deg_raw. README C10.
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
import time

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
    가는 전류 = i(Vlb)), T = (Tv*Ti - 1)/(Tv + Ti + 2). 반환 (주파수, T 실수부, T 허수부) 또는 None.
    [신규 2026-10-08] 분모(sum(w*vy), sum(w*(w - ix)), Tv + Ti + 2) 중 하나가 데이터 파일 값으로 정확히 0 인 표본이 하나라도
    있으면 None(ZeroDivisionError 로 죽지 않는다) -- 그 표본의 Tv 또는 Ti 가 정의되지 않아 T 가 정의되지 않는다.
    어느 표본인지는 loop_probe_singular() 가 준다."""
    if loop_probe_singular(v_file, i_file, weights):
        return None
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


LOOP_PROBE_SINGULAR = "loop_probe_singular"


def loop_probe_singular(v_file, i_file, weights):
    """Middlebrook 분모가 정확히 0 인 표본 목록 [{f_hz, which}] (which = 'vy'(전압 주입: 증폭기 쪽 전압 0 -> Tv 정의 불가),
    'iy'(전류 주입: 주입 전류가 전부 되먹임 쪽으로 가 증폭기 쪽 전류 0 -> Ti 정의 불가), 'tv+ti+2'(합성식 분모 0)).
    iy = 0 은 그 주파수에서 증폭기 쪽(절단 넷의 증폭기 쪽 원소 + 테스트벤치 choke)의 어드미턴스가 데이터 파일 분해능에서 0 이라
    주입 전류의 귀로가 되먹임 쪽밖에 없다는 뜻이다(예: 입력 넷에 접지 C 가 없고 되먹임 Cf 만 있는 단일 입력 회로). 파일이 없으면 []."""
    v, i = _cols(v_file), _cols(i_file)
    if v is None or i is None or len(v[0]) != len(i[0]):
        return []
    out = []
    for f, row_v, row_i in zip(v[0], v[1], i[1]):
        vx = sum(w * row_v[2 * k] for k, w in enumerate(weights))
        vy = sum(w * row_v[2 * k + 1] for k, w in enumerate(weights))
        ix = sum(w * row_i[k] for k, w in enumerate(weights))
        iy = sum(w * (w - row_i[k]) for k, w in enumerate(weights))
        if vy == 0:
            out.append({"f_hz": f, "which": "vy"})
        elif iy == 0:
            out.append({"f_hz": f, "which": "iy"})
        elif (-vx / vy) + (ix / iy) + 2 == 0:
            out.append({"f_hz": f, "which": "tv+ti+2"})
    return out


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
    # 편각 변화가 π/2 이상인 양의 주파수 구간(적응 세분화 대상, nyquist_adaptive). 켤레 반쪽은 같은 구간의 거울상이라 양의 쪽만 센다.
    # 두 닫는 직선(저주파 conj L(f_first) -> L(f_first), 고주파 L(f_last) -> conj L(f_last))은 표본을 더할 수 없어 따로 기록한다.
    n = len(f)
    out["bad_intervals_hz"] = [[float(fz[n + i]), float(fz[n + i + 1])] for i in range(n - 1)
                               if abs(d[n + i]) >= np.pi / 2]
    out["closing_step_deg"] = [float(np.degrees(abs(d[n - 1]))), float(np.degrees(abs(d[2 * n - 1])))]
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


def reltol_of(options):
    """ngspice 가 쓰는 reltol = 입력 testbench.options 의 값, 없으면 ngspice 기본값(_NGSPICE_DEFAULT_TOL)."""
    o = {k.lower(): v for k, v in (options or {}).items()}
    return float(o.get("reltol", _NGSPICE_DEFAULT_TOL["reltol"]))


def n_pp_of(reltol):
    """한 주기당 표본 수 n_pp = ceil(π / arccos(1 − reltol)). 유도(계약 1(a)): 표본 간격 Δ = 주기/n 일 때 정현파 봉우리를 놓치는
    최대 상대 오차가 1 − cos(π/n) 이므로 이 값이 reltol 이하인 최소 n(reltol 1e-3 -> 71, 1e-4 -> 223)."""
    return int(math.ceil(math.pi / math.acos(1.0 - reltol)))


def band_f_crit(freq, L):
    """f_crit = 불안정 관련 대역 안에서 |1+L| 이 최소인 표본의 주파수(계약 1(a) d56ba66). 대역 = 스윕 첫 표본부터 **가장 높은
    |L|=1 교차를 지난 첫 표본**까지(닫기 부호 반영 L). |L| < 1 인 꼬리는 −1 을 감지 못하고(Nyquist) 거기서는 |1+L| -> 1 이라
    argmin 이 스윕 끝에 붙어 의미가 없다. 교차가 없으면 None."""
    import numpy as np
    f = np.asarray(freq, float)
    a = np.abs(np.asarray(L, complex))
    above = a >= 1
    cr = [i for i in range(len(a) - 1) if above[i] != above[i + 1]]
    if not cr:
        return None
    last = cr[-1] + 1
    band = np.abs(1.0 + np.asarray(L, complex)[:last + 1])
    return float(f[int(np.argmin(band))])


_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oracle_config.json")


def stability_config(path=None):
    """oracle_config.json 의 stability_transient 블록(창당 상한 wall_s_per_window 와 그 근거). 없거나 값이 없으면 예외
    (조용한 기본값을 두지 않는다 -- 계약 1(c): 상한이 선언돼 있어야 한다)."""
    with open(path or _CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    st = cfg["stability_transient"]
    w = st["wall_s_per_window"]
    if not isinstance(w, (int, float)) or isinstance(w, bool) or w <= 0:
        raise ValueError(f"oracle_config.json stability_transient.wall_s_per_window 는 양수여야 한다: {w!r}")
    return st


def tran_plan(crossings_hz, temp_c, floor_v, file_name, f_crit_hz=None, reltol=None, wall_s_per_window=None):
    """폐루프 과도 계획(전부 측정 L 과 입력에서 유도, 조정 상수 없음):
      kick_V = V_T(.temp)  -- 소신호 선형화의 물리 척도(exp(v/V_T) 1차), 해 분해능 floor 보다 커야 한다.
      시간 척도 = f_lo = 가장 낮은 |L|=1 교차 = PM 을 정의한 교차(UGF; L(fstart) >= 1 이고 첫 교차가 하강이라 늘 같다).
      td = tr = tf = pw = 1/(2π f_lo), 창 W = 1/f_lo, 창 수 K = ceil(ln(kick_V/floor)) -- 창마다 1 e-fold 감쇠하면
      킥 크기가 해 분해능에 닿는 창 수. K < 2 면 비교할 수 없어 계획 없음(None).
      [변경 2026-10-08, 조기 종결 계약 1(a)] 걸음 상한 tmax = min(1/(2π f_lo), 1/(f_crit·n_pp)): f_crit = 불안정 관련 대역 안 |1+L| 최소
      표본 주파수(band_f_crit), n_pp = 한 주기당 표본 수(n_pp_of(reltol)). f_crit 이 f_lo 근처면 옛 tmax 와 같고(min 이 f_lo 항),
      GHz 로 진동하는 회로는 걸음을 f_crit 주기에 맞춰 잡는다(ngspice LTE 걸음 제어가 GHz 주기를 따라가 끝나지 않던 문제의 한도).
      f_hi 는 기록만(걸음 수 한도로 쓰지 않는다 -- tmax 의 하한이 아니다).
      wall_cap_s = wall_s_per_window × K(첫 실행 상한; 계약 1(c))."""
    f_lo, f_hi = min(crossings_hz), max(crossings_hz)
    kick = thermal_voltage(temp_c)
    if not floor_v or floor_v <= 0 or kick <= floor_v:
        return None
    K = math.ceil(math.log(kick / floor_v))
    if K < 2:
        return None
    reltol = _NGSPICE_DEFAULT_TOL["reltol"] if reltol is None else reltol
    n_pp = n_pp_of(reltol)
    t_lo = 1 / (2 * math.pi * f_lo)
    tmax = t_lo if not f_crit_hz else min(t_lo, 1 / (f_crit_hz * n_pp))
    pw = t_lo
    W = 1 / f_lo
    t_end = t_lo + t_lo + pw + t_lo
    plan = {"kick_V": kick, "td": t_lo, "tr": t_lo, "pw": pw, "tmax": tmax, "window_s": W, "windows": K,
            "windows_planned": K, "t_kick_end": t_end, "tstop": t_end + K * W, "f_lo_hz": f_lo, "f_hi_hz": f_hi,
            "f_crit_hz": f_crit_hz, "n_pp": n_pp, "reltol": reltol, "floor_V": floor_v, "file": file_name}
    plan["wall_cap_s"] = None if wall_s_per_window is None else wall_s_per_window * K
    return plan


# ---------------------------------------------------------------- 창 판정 (분해능 인식형, 계약 1(b) d56ba66 + 사용자 결정 4)
def g_up(a, b, fl, reltol):
    """b 가 a 보다 측정 분해능을 넘게 큼: b(1 − reltol) > a(1 + reltol) + floor'. (M_j 는 표본 봉우리라 상대 오차 <= reltol(n_pp 유도),
    절대 분해능 floor' -- 두 창의 측정 불확실 구간이 겹치지 않을 때만 '커졌다')."""
    return b * (1 - reltol) > a * (1 + reltol) + fl


def g_down(a, b, fl, reltol):
    """b 가 a 보다 측정 분해능을 넘게 작음: a(1 − reltol) > b(1 + reltol) + floor'."""
    return a * (1 - reltol) > b * (1 + reltol) + fl


def _flat(a, b, fl, reltol):
    """창 b(직전 창 a)가 일정 진폭 진동 창이다(사용자 결정 4): 바닥보다 분해능 넘게 크고(b(1−reltol) > floor') 직전 창과의 변화가
    분해능 안(|b − a| <= (a+b)·reltol + floor' <=> g↑ 도 g↓ 도 아님)."""
    return b * (1 - reltol) > fl and not g_up(a, b, fl, reltol) and not g_down(a, b, fl, reltol)


def growth_window(M, fl, reltol):
    """엄격 증가 조기 기준: j >= 3 인 첫 창에서 g↑(M_{j−2}, M_{j−1}) 그리고 g↑(M_{j−1}, M_j) 그리고 g↑(M_1, M_j). 창 번호(1 부터) 또는 None."""
    for j in range(3, len(M) + 1):
        if g_up(M[j - 3], M[j - 2], fl, reltol) and g_up(M[j - 2], M[j - 1], fl, reltol) and g_up(M[0], M[j - 1], fl, reltol):
            return j
    return None


def limit_cycle_window(M, fl, reltol):
    """한계 사이클 조기 기준(사용자 결정 4): j >= 3 인 첫 창에서 창 j−1 과 창 j 가 둘 다 일정 진폭(_flat). 창 번호 또는 None.
    일정 진폭 진동은 분해능 안에서 줄지도 늘지도 않는 지속 진동이다."""
    for j in range(3, len(M) + 1):
        if _flat(M[j - 3], M[j - 2], fl, reltol) and _flat(M[j - 2], M[j - 1], fl, reltol):
            return j
    return None


def early_window(M, fl, reltol):
    """조기 종결 창 (j, 종류) 또는 None. 종류 = 'growth'(엄격 증가) | 'limit_cycle'(일정 진폭 지속 진동). 둘은 같은 창 쌍에서 동시에 성립할 수 없다."""
    g, c = growth_window(M, fl, reltol), limit_cycle_window(M, fl, reltol)
    if g is not None and (c is None or g <= c):
        return g, "growth"
    if c is not None:
        return c, "limit_cycle"
    return None


def early_unstable(M, floor2, reltol):
    """조기 unstable(엄격 증가) 기준의 순수 함수(계약 1(b)): 창 최댓값 열 M, 해 분해능 floor', reltol 에서 j >= 3 인 어떤 창이
    g↑(M_{j−2},M_{j−1})·g↑(M_{j−1},M_j)·g↑(M_1,M_j) 를 충족하면 True. 일정 진폭 진동은 이 함수가 아니라 limit_cycle_early 가 본다."""
    return growth_window(list(M), floor2, reltol) is not None


def limit_cycle_early(M, floor2, reltol):
    """한계 사이클 조기 기준의 순수 함수: 연속 두 창이 일정 진폭이면 True(사용자 결정 4)."""
    return limit_cycle_window(list(M), floor2, reltol) is not None


def window_ratios(M):
    """창당 변화비 M_j / M_{j−1} (j = 2..). 0 이면 None."""
    return [None if not a else b / a for a, b in zip(M, M[1:])]


def transient_decision(path, plan):
    """폐루프 과도 판정(계약 1(b), 사용자 결정 4). e(t) = H(t) - H(0)(H(0) = 동작점), 킥이 끝난 뒤 창 j = 1..K 의 M_j = max|e| (창 끝까지
    표본이 닿은 창만 센다 -- 조기 종결·중간 사망 파일은 앞쪽 창만 있다). floor' = plan.floor_V + (데이터 파일 반올림 u*max|H|).
    분해능 인식형 g↑/g↓(reltol = plan.reltol):
      조기(끝난 창들에서 첫 j): growth(엄격 증가 연속) 또는 limit_cycle(연속 두 창이 일정 진폭)   -> unstable + early_stop
      마지막 시각이 tstop 에 못 닿음(조기 아님)                                                -> failed
      M_K <= floor'                                  -> stable(해 분해능 아래로 감쇠)
      g↑(M_1, M_K)                                   -> unstable(분해능 넘는 증가)
      모든 연속 창 g↓(M_{j−1}, M_j)                  -> decaying(연장 실행 대상)
      그 밖(분해능 안의 같음 포함)                    -> undetermined(완화 진동·맥놀이·늦게 자라는 모드 -- stable 아님)
    limit_cycle 은 고Q로 천천히 감쇠하는 안정 회로와 K 창 안에서 구별할 수 없다 -> 보수적으로 unstable, 같이
    limit_cycle_vs_slow_decay_unresolved{M, window_ratios, reason} 를 낸다(사용자가 FAIL 이 판정 한계에서 나온 것을 알아보도록).
    반환 {status, M, floor_V, reason, windows_run, early_stop(조기일 때), limit_cycle_vs_slow_decay_unresolved(limit_cycle 일 때)}."""
    out = {"status": "failed", "M": None, "floor_V": None, "reason": None, "windows_run": 0}
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
    if len(t) < 2:
        out["reason"] = f"과도가 tstop 까지 가지 않았다(마지막 t = {t[-1] if t else None})"
        return out
    floor = plan["floor_V"] + u * max(abs(x) for x in v)
    reltol = plan.get("reltol", _NGSPICE_DEFAULT_TOL["reltol"])
    ref = plan["h_ref"] if plan.get("h_ref") is not None else v[0]     # 개루프 과도 확인은 기준 = 동작점 H 값(초기 변위 이전)
    M = []
    for j in range(plan["windows"]):
        a = plan["t_kick_end"] + j * plan["window_s"]
        b = a + plan["window_s"]
        # 창 끝까지 표본이 닿은 창만(넷리스트 시각 10 자리·파일 시각 자릿수의 반올림 차는 파일 분해능 u 의 두 배 안)
        if t[-1] < b * (1 - 2 * u):
            break
        seg = [abs(x - ref) for tt, x in zip(t, v) if a <= tt <= b]
        if not seg:
            out["reason"] = f"창 {j + 1} 에 표본이 없다"
            return out
        M.append(max(seg))
    out.update(M=M, floor_V=floor, windows_run=len(M))
    ew = early_window(M, floor, reltol)
    if ew is not None:
        j, kind = ew
        out.update(M=M[:j], windows_run=j, status="unstable")
        if kind == "growth":
            why = (f"창 {j} 에서 분해능을 넘는 연속 증가(g↑(M_{j - 2},M_{j - 1})·g↑(M_{j - 1},M_{j})·g↑(M_1,M_{j}), "
                   f"reltol {reltol:g}, floor' {floor:.3g})")
        else:
            why = (f"limit_cycle: 창 {j - 1}·{j} 가 일정 진폭 지속 진동(바닥 {floor:.3g} 보다 분해능 넘게 크고 직전 창과의 변화가 "
                   f"reltol {reltol:g} 안)")
            out["limit_cycle_vs_slow_decay_unresolved"] = {
                "M": M[:j], "window_ratios": window_ratios(M[:j]), "floor_V": floor, "reltol": reltol,
                "reason": ("분해능 안에서 일정한 창 진폭 -- 지속 진동(한계 사이클)이거나 창당 감쇠가 분해능보다 작은 고Q 안정 회로다. "
                           "K 창 안에서는 둘을 구별할 수 없어 보수적으로 unstable(limit_cycle) -> FAIL 로 판정했다.")}
        out["early_stop"] = {"window": j, "M": M[:j], "reason": why, "kind": kind}
        out["reason"] = why
        return out
    if t[-1] < plan["tstop"] * (1 - 2 * u):
        out.update(status="failed", reason=f"과도가 tstop 까지 가지 않았다(마지막 t = {t[-1]})")
        return out
    if not M:
        out.update(status="failed", reason="끝난 창이 없다")
        return out
    if M[-1] <= floor:
        out.update(status="stable", reason="끝 창 응답이 해 분해능 아래로 감쇠")
    elif g_up(M[0], M[-1], floor, reltol):
        out.update(status="unstable", reason="K 창 동안 응답이 분해능을 넘게 증가")
    elif all(g_down(a, b, floor, reltol) for a, b in zip(M, M[1:])):
        out.update(status="decaying", reason="모든 창에서 분해능을 넘게 감소하지만 아직 해 분해능 위")
    else:
        out.update(status="undetermined",
                   reason="창 사이 응답이 분해능 안에서 같거나 다시 커짐(완화 진동·맥놀이·늦게 자라는 모드)")
    return out


def extension_plan(plan, dec, file_name, wall_s_per_window=None):
    """decaying 이면 마지막 창 감쇠비 r = M_K/M_{K-1} 의 기하 감쇠로 floor' 에 닿는 창 수 n = ceil(ln(floor'/M_K)/ln r)
    만큼 늘린 계획(같은 킥·같은 창, 창 수 K + n). 측정한 감쇠율에서 유도(상수 없음). 아니면 None.
    wall_cap_s = wall_s_per_window × (K + n)(연장 실행은 K+n 창을 처음부터 다시 돌린다; 계약 1(c))."""
    M, fl = dec.get("M") or [], dec.get("floor_V")
    if dec.get("status") != "decaying" or len(M) < 2 or not fl or M[-1] <= fl:
        return None
    r = M[-1] / M[-2]
    n = math.ceil(math.log(fl / M[-1]) / math.log(r))
    p = dict(plan)
    p.update(windows=plan["windows"] + n, tstop=plan["t_kick_end"] + (plan["windows"] + n) * plan["window_s"],
             file=file_name, extension_windows=n)
    p["windows_planned"] = p["windows"]
    p["wall_cap_s"] = None if wall_s_per_window is None else wall_s_per_window * (plan["windows"] + n)
    return p


def final_transient_status(dec1, dec2):
    """첫 실행과 연장 실행으로 최종 상태. 첫 실행이 decaying 이 아니면 그 상태(stable·unstable·undetermined·failed).
    decaying 이면 연장 실행이: stable(floor' 도달) 또는 decaying(투영 시간 전체에서 창마다 감소 = 감쇠 입증) -> stable,
    unstable -> unstable, 그 밖(failed·undetermined) -> undetermined. 'stable' 은 floor' 도달 또는 입증된 감쇠뿐이다."""
    s1 = dec1.get("status")
    if s1 != "decaying":
        return s1
    s2 = (dec2 or {}).get("status")
    if s2 in ("stable", "decaying"):
        return "stable"
    if s2 == "unstable":
        return "unstable"
    return "undetermined"


# ---------------------------------------------------------------- [신규 U6] 독립 P (.pz) 와 N 적응 세분화, 최종 판정 (사용자 결정 Q10)
# Nyquist: Z = N + P. N 은 .ac 표본에서(위상 펼침, 인접 표본 편각 변화 >= π/2 이면 그 구간을 이분해 다시 .ac), P(개루프 RHP 극 수)는
# 같은 루프 절단의 개루프 넷리스트에 ngspice `.pz` 를 돌려 독립으로 잰다. 폐루프 .tran 은 별도 증거다.
NYQUIST_K_MAX = 10      # 세분화 라운드 상한: 한 라운드가 편각 π/2 이상인 구간을 이분 -> 10 라운드 = 1024 분할. 그래도 넘으면 L 이 -1 을 극히 가까이 지나는 특이 구조라 N 미정.

_PZ_POLE = re.compile(r"^\s*pole\(\d+\)\s*=\s*([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)\s*$", re.M)


def pz_poles(log):
    """ngspice `pz ... pol` + `print all` 로그에서 극점(복소수 목록). 실패 표지(반복 한도 도달 등)는 (극점, 문제 문자열 목록)으로 같이 돌려준다."""
    poles = [complex(float(a), float(b)) for a, b in _PZ_POLE.findall(log)]
    problems = [ln.strip() for ln in log.splitlines()
                if re.search(r"giving up|iteration limit|singular matrix|rror", ln, re.I)]
    return poles, problems


def pz_rhp_count(poles, reltol, f_stop_hz):
    """실수부가 분해능 밖으로 양수인 극 수 P. 분해능 = 극 자신의 크기에 대한 상대 reltol(Re p > reltol·|p|; 0 근처 극은 실수부가 양수라도
    크기에 비해 reltol 이하면 세지 않는다). .ac 스윕 상한(2π·f_stop)을 넘는 RHP 후보는 `.pz` 근 찾기의 수치 허수일 수 있어(README:
    BSIM4 큰 회로에서 +5.9e13 rad/s 가짜 극) 세지 않고 beyond_sweep 에 따로 기록하며 이 경우 P 는 신뢰하지 않는다(P = None).
    반환 {P, rhp, beyond_sweep, n_poles, omega_stop}."""
    w_stop = 2 * math.pi * f_stop_hz
    rhp, beyond = [], []
    for p in poles:
        if p.real > reltol * abs(p):
            (beyond if abs(p) > w_stop else rhp).append([p.real, p.imag])
    return {"P": None if beyond else len(rhp), "rhp": rhp, "beyond_sweep": beyond, "n_poles": len(poles),
            "omega_stop": w_stop}


def pz_check(pz_cir, text, meta, node_V, choke_I, timeout_s, cache_dir, exe, reltol, f_stop_hz, loop_kind=None):
    """개루프 넷리스트 <pz_cir> 를 쓰고 ngspice `.pz` 를 돌려 P 를 낸다(oracle_netlist.pz_netlist: 큰 L·C 없이 동작점 값으로 만든 개루프).
    loop_kind = None(β=1 본 넷리스트) | 'dm'(β 루프 넷리스트) | 'cm'(CM 루프 넷리스트). 반환 dict {status ok|failed|unavailable, P, rhp,
    beyond_sweep, n_poles, reason, netlist, ngspice_rc, poles(실수부 큰 순 상위 40)}. 실패(반복 한도·극 0 개·시간 초과)는 P = None
    (알 수 없음 -- 0 으로 두지 않는다)."""
    from oracle_netlist import pz_netlist
    out = {"status": "unavailable", "P": None, "rhp": [], "beyond_sweep": [], "n_poles": 0, "reason": None,
           "netlist": os.path.basename(pz_cir), "ngspice_rc": None,
           "method": "ngspice .pz (cur, pol) on the open-loop testbench (bias from the operating-point pass)",
           "open_loop": {"dm": "both cut ends (n and lbx) AC-grounded at the bias point", "cm": "forward input (lbx) driven, driver output free",
                         None: "main netlist, inputs driven (beta=1)"}[loop_kind]}
    sn = meta.get("spice_node") or {}
    nets = [n for n in meta.get("inputs") or [] if n in sn]
    outs = meta.get("output_nodes") or []
    if not nets or not outs:
        out["reason"] = "넷리스트 meta 에 입력·출력 노드가 없다"
        return out
    lm = meta.get("loop") or {}
    try:
        ptext = pz_netlist(text, nets, [sn[n] for n in nets], outs[0], node_V or {}, choke_I or {}, loop_kind,
                           lm.get("break_nets") or [])
    except ValueError as e:
        out["reason"] = str(e)
        return out
    with open(pz_cir, "w", encoding="utf-8") as fh:
        fh.write(ptext)
    try:
        rc, log, _ = run_ngspice(exe, pz_cir, os.path.splitext(pz_cir)[0] + ".log", timeout_s, cache_dir, [])
    except subprocess.TimeoutExpired:
        out.update(status="failed", reason=f".pz 가 시간 상한 {timeout_s} s 에 끊겼다")
        return out
    out["ngspice_rc"] = rc
    poles, problems = pz_poles(log)
    out["n_poles"] = len(poles)
    if problems:
        out.update(status="failed", reason="; ".join(problems[:3]))
        return out
    if not poles:
        out.update(status="failed", reason="ngspice .pz 가 극점을 내지 않았다")
        return out
    cnt = pz_rhp_count(poles, reltol, f_stop_hz)
    out.update(status="ok", P=cnt["P"], rhp=cnt["rhp"], beyond_sweep=cnt["beyond_sweep"], omega_stop=cnt["omega_stop"],
               poles=[[p.real, p.imag] for p in sorted(poles, key=lambda q: -q.real)[:40]])
    if cnt["P"] is None:
        out["reason"] = (f"RHP 후보 극 {len(cnt['beyond_sweep'])} 개가 .ac 스윕 상한 {cnt['omega_stop']:.3g} rad/s 밖 -- "
                         f"수치 허수와 구별할 수 없어 P 를 쓰지 않는다")
    return out


def _refine_text(text, f_a, f_b, ppd, tag):
    """원 넷리스트 텍스트에서 `ac dec ...` 줄의 구간·밀도를 바꾸고 `wrdata <파일>` 의 파일 이름 앞에 tag 를 붙인다(나머지 줄은 그대로)."""
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if re.match(r"ac\s+dec\s+", s, re.I):
            out.append(f"ac dec {int(ppd)} {f_a:.10g} {f_b:.10g}")
        elif s.lower().startswith("wrdata "):
            t = s.split(None, 2)
            out.append(f"wrdata {tag}{t[1]} {t[2] if len(t) > 2 else ''}")
        else:
            out.append(ln)
    return "\n".join(out) + "\n"


def refine_samples(cir_path, meta, f_a, f_b, ppd, tag, exe, timeout_s=None, cache_dir=None):
    """L(jω) 를 [f_a, f_b] 에서 더 촘촘히(ppd 점/decade) 다시 잰다 -- 원래 L 을 만든 넷리스트(β=1: 본 넷리스트의 `ac`, β 루프: 루프
    넷리스트의 Middlebrook 두 `ac`)를 구간·밀도만 바꿔 다시 돌린다. 반환 (f, re, im)(양끝 포함) 또는 None."""
    d = os.path.dirname(os.path.abspath(cir_path))
    lm = meta.get("loop")
    src = os.path.join(d, lm["netlist"]) if lm else cir_path
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    new = os.path.join(d, f"{tag}{os.path.basename(src)}")
    with open(new, "w", encoding="utf-8") as fh:
        fh.write(_refine_text(text, f_a, f_b, ppd, tag))
    files = [lm["v_file"], lm["i_file"]] if lm else [meta["ac_file"]]
    for x in files:
        if os.path.exists(os.path.join(d, tag + x)):
            os.remove(os.path.join(d, tag + x))
    try:
        run_ngspice(exe, new, os.path.splitext(new)[0] + ".log", timeout_s, cache_dir, [tag + x for x in files])
    except subprocess.TimeoutExpired:
        return None
    if lm:
        return loop_gain(os.path.join(d, tag + lm["v_file"]), os.path.join(d, tag + lm["i_file"]), lm["weights"])
    return parse_ac_file(os.path.join(d, tag + meta["ac_file"]))


def nyquist_adaptive(freq, L, sample_fn=None, k_max=NYQUIST_K_MAX):
    """nyquist_count 에 적응 세분화를 더한다(사용자 결정 Q10): N 이 인접 표본 편각 변화 >= π/2 로 정해지지 않으면 그런 양의 주파수 구간마다
    구간을 (로그) 이분하는 점을 sample_fn(f_a, f_b, ppd, tag) 으로 다시 재서 합치고 다시 센다(최대 k_max 라운드). sample_fn 이 None 이면
    세분화 없음. 반환 (nyq, freq, L) -- 합친 표본. nyq.refinement = {rounds, samples_added, k_max, history}."""
    import numpy as np
    f = np.asarray(freq, float)
    Lc = np.asarray(L, complex)
    nyq = nyquist_count(f, Lc)
    rounds, added, hist = 0, 0, []
    while (sample_fn is not None and nyq["encirclements_cw"] is None and nyq.get("bad_intervals_hz")
           and rounds < k_max):
        new_f, new_L = [], []
        for fa, fb in nyq["bad_intervals_hz"]:
            ppd = max(1, math.ceil(2.0 / math.log10(fb / fa)))        # 표본 간격이 원래의 절반 이하가 되는 밀도
            got = sample_fn(fa, fb, ppd, f"nyq{rounds + 1}_")
            if not got:
                continue
            gf, gr, gi = np.asarray(got[0], float), np.asarray(got[1], float), np.asarray(got[2], float)
            keep = (gf > fa * (1 + 1e-9)) & (gf < fb * (1 - 1e-9))
            new_f += list(gf[keep])
            new_L += list((gr + 1j * gi)[keep])
        hist.append({"round": rounds + 1, "intervals": nyq["bad_intervals_hz"], "samples": len(new_f)})
        if not new_f:
            break
        order = np.argsort(np.concatenate([f, new_f]))
        f = np.concatenate([f, new_f])[order]
        Lc = np.concatenate([Lc, new_L])[order]
        added += len(new_f)
        rounds += 1
        nyq = nyquist_count(f, Lc)
    nyq["refinement"] = {"rounds": rounds, "samples_added": added, "k_max": k_max, "history": hist}
    return nyq, f, Lc


def _judgement_legacy(nyq, tran_status, pm_raw=None):
    """Nyquist N(Z - P)과 폐루프 과도 상태로 PM 이 안정 여유인지 정한다 -- P 를 모를 때(.pz 가 없거나 못 믿을 때)의 추론표
    (P = 0 일 때 유효 -- 음수 PM 도 유효한 여유, 엔진 metrics §3.10 과 같은 정의). 폐루프 불안정이고 N >= 1 이면 P = 0(Z = N)과
    맞는 증거는 Bode PM < 0 뿐이다: pm_raw < 0 이면 PM 값 유지(제약은 이전처럼 FAIL), pm_raw >= 0 이면 증거 충돌(P > 0 또는 놓친
    모드) -> stability_evidence_inconsistent. 반환 {closed_loop, open_loop_rhp_poles, open_loop_rhp_poles_bound, pm_valid,
    pm_undefined}."""
    N = nyq.get("encirclements_cw") if nyq else None
    neg = pm_raw is not None and pm_raw < 0
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
        elif N is not None and neg:
            r.update(open_loop_rhp_poles=0, open_loop_rhp_poles_bound="== (Z = N 과 일치)", pm_valid=True)
        elif N is not None:
            r["pm_undefined"] = PM_UNDEFINED_INCONSISTENT
        else:
            r["pm_undefined"] = PM_UNDEFINED_CL_UNSTABLE
    else:
        if N is not None and N >= 1 and neg:
            r.update(closed_loop="unstable", open_loop_rhp_poles=0, open_loop_rhp_poles_bound="== (Z = N 과 일치)",
                     pm_valid=True)
        elif N is not None and N >= 1:
            r.update(closed_loop="unstable", pm_undefined=PM_UNDEFINED_INCONSISTENT)
        elif N is not None and N < 0:
            r.update(open_loop_rhp_poles=-N, open_loop_rhp_poles_bound=">=", pm_undefined=PM_UNDEFINED_RHP)
        else:
            r["pm_undefined"] = PM_UNDEFINED_UNVERIFIED
    return r


def stability_judgement(nyq, tran_status, pm_raw=None, pz=None):
    """최종 안정성 판정(사용자 결정 Q10): Nyquist Z = N + P(P = 독립 `.pz`, N = 위상 펼침 .ac 표본) 와 폐루프 과도를 함께 본다.
    **`.pz` 신뢰 규칙** (ngspice `.pz` 는 큰 BSIM4 회로에서 근을 놓치거나 가짜 RHP 근을 낸다 -- smoke 파일럿 forced 에서 RHP 극 23 개를 냈지만 개루프 과도는
    증가가 없다):
      * 폐루프 과도가 stable 로 정해졌으면 Z = 0 이므로 P = -N 이 **정확**하다(Nyquist) -- `.pz` 는 참고(어긋나면 `pz_conflict` 에 기록하고 무시);
      * 폐루프 과도가 unstable 이면 FAIL 은 이미 정해졌고 P 는 이름 붙이기용으로만 쓴다;
      * 폐루프 과도가 정해지지 않았으면(undetermined·failed·not_run) `.pz` 의 P >= 1 은 **개루프 과도가 증가를 보일 때만**(`pz.validated` is True) 쓴다.
    verdict = 'unstable'    폐루프 과도 unstable(limit_cycle 포함) / N >= 1 (P >= 0 이라 Z >= N >= 1) / Z >= 1 이고 P 가 검증됨
              'stable'      폐루프 과도 stable (basis: transient[+nyquist])
              'undetermined' 그 밖 -- 둘 다 결론을 못 낸 경우(INCOMPLETE; Z = 0 이라도 과도가 안 정해졌으면 Nyquist 만으로는 안정이라 하지 않는다: P = 0 은 `.pz` 가
                             근을 놓치지 않았다는 가정에 기댄다)
    P_eff(PM 유효성에 쓰는 P)가 정수면 PM:
      P_eff == 0 : verdict stable -> PM 값 / unstable 이면 N >= 1 & pm_raw < 0 만 값(Z = N 과 일치), 그 밖 stability_evidence_inconsistent /
                   undetermined -> stability_unverified
      P_eff >= 1 : Z == 0 이고 안정 -> 조건부 안정(conditionally_stable): PM 원값을 값으로 둔다. 그 밖 -> open_loop_rhp_poles(정의 불가)
      Z < 0      : 불가능한 값 -> stability_evidence_inconsistent
    P_eff 를 모르면 _judgement_legacy 표(N + 과도로 P 추론)로 PM 을 정한다.
    반환 {closed_loop, open_loop_rhp_poles(_bound), pm_valid, pm_undefined, verdict, verdict_basis, Z, P_pz, P_eff, pz_conflict, conditionally_stable}."""
    N = nyq.get("encirclements_cw") if nyq else None
    P = pz.get("P") if pz else None
    S = tran_status if tran_status in ("stable", "unstable") else None
    Z = None if N is None or P is None else N + P
    r = _judgement_legacy(nyq, tran_status, pm_raw)
    P_eff, conflict = None, None
    if P is not None:
        if S == "stable":
            if Z == 0:
                P_eff = P
            else:
                conflict = (f".pz P = {P} 인데 폐루프 과도는 stable(Nyquist 로는 P = -N = {None if N is None else -N}) -- "
                            f".pz 근 찾기가 믿을 수 없는 회로로 보고 무시한다")
        elif S == "unstable":
            P_eff = P
        elif pz.get("validated") is True:
            P_eff = P
        elif P >= 1:
            conflict = ".pz 의 RHP 극을 개루프 과도가 확인하지 못했다(검증 없음 -- 판정에 쓰지 않는다)"
    Zeff = None if N is None or P_eff is None else N + P_eff
    r.update(Z=Zeff, P_pz=P, P_eff=P_eff, pz_conflict=conflict, conditionally_stable=False)
    if S == "unstable":
        verdict, basis = "unstable", "transient" + ("+nyquist" if (Zeff is not None and Zeff >= 1) or (N is not None and N >= 1) else "")
    elif N is not None and N >= 1:
        verdict, basis = "unstable", "nyquist(N >= 1)"
    elif Zeff is not None and Zeff >= 1:
        verdict, basis = "unstable", "nyquist+pz(검증됨)"
    elif S == "stable":
        verdict, basis = "stable", "transient" + ("+nyquist" if Zeff == 0 else "")
    else:
        verdict, basis = "undetermined", "none"
    r.update(verdict=verdict, verdict_basis=basis)
    if verdict == "unstable" and r["closed_loop"] is None:
        r["closed_loop"] = "unstable"
    if verdict == "stable" and r["closed_loop"] is None:
        r["closed_loop"] = "stable"
    if P_eff is None:
        return r
    # ---- P_eff 를 안다: 독립 .pz 로 개루프 RHP 극 수가 정해졌다 (legacy 추론 대신)
    neg = pm_raw is not None and pm_raw < 0
    r.update(open_loop_rhp_poles=P_eff, open_loop_rhp_poles_bound="== (.pz)", pm_valid=False, pm_undefined=None)
    if Zeff is not None and Zeff < 0:
        r["pm_undefined"] = PM_UNDEFINED_INCONSISTENT
    elif P_eff == 0:
        if verdict == "stable":
            r["pm_valid"] = True
        elif verdict == "unstable":
            if N is None:
                r["pm_undefined"] = PM_UNDEFINED_CL_UNSTABLE
            elif N >= 1 and neg:
                r["pm_valid"] = True
            else:
                r["pm_undefined"] = PM_UNDEFINED_INCONSISTENT
        else:
            r["pm_undefined"] = PM_UNDEFINED_UNVERIFIED
    else:
        if verdict == "stable" and Zeff == 0:
            r.update(pm_valid=True, conditionally_stable=True)
        else:
            r["pm_undefined"] = PM_UNDEFINED_RHP
    return r


def pz_validate(d, stem, text, meta, input_nodes, node_V, choke_I, plan, kind, exe, cap, cache_dir):
    """`.pz` 가 낸 RHP 극(P >= 1)을 개루프 과도로 확인한다(oracle_netlist.openloop_tran_netlist): 출력 노드에 초기 변위 V_T 를 주고 같은 창 계획(K 창, t_kick_end = 0,
    기준 = 동작점 H)에서 transient_decision 으로 판정한다. 반환 {validated: True(unstable -- 변위가 자라거나 일정 진폭 지속) | False(stable·decaying) | None(그 밖:
    undetermined·failed·시간 초과), status, M, ...}. 폐루프 과도가 정해지지 않은 회로에서 `.pz` 의 P 를 판정에 쓰는 조건이다(stability_judgement)."""
    from oracle_netlist import openloop_tran_netlist
    outs = meta["output_nodes"]
    vo = [0.0 if n == "0" else node_V.get(n.lower()) for n in outs]
    if None in vo:
        return {"validated": None, "status": "not_run", "reason": "출력 동작점 전압이 없다"}
    pl = dict(plan)
    pl.update(t_kick_end=0.0, tstop=plan["windows"] * plan["window_s"], file=f"{stem}.pzv.txt", h_ref=vo[0] - vo[1])
    lm = meta.get("loop") or {}
    try:
        t = openloop_tran_netlist(text, list(input_nodes.keys()), list(input_nodes.values()), outs, node_V, choke_I, kind,
                                  lm.get("break_nets") or [], pl, plan["kick_V"])
    except ValueError as e:
        return {"validated": None, "status": "not_run", "reason": str(e)}
    cir = os.path.join(d, f"{stem}.pzv.cir")
    with open(cir, "w", encoding="utf-8") as fh:
        fh.write(t)
    f = os.path.join(d, pl["file"])
    if os.path.exists(f):
        os.remove(f)
    rc, _, cst, to = _run_stab(exe, cir, cap, cache_dir, [pl["file"]])
    dec = transient_decision(f, pl)
    if to:
        dec.update(status="failed", reason=f"개루프 과도 시간 초과: {to}", timeout=to)
    v = True if dec["status"] == "unstable" else (False if dec["status"] in ("stable", "decaying") else None)
    return {**dec, "validated": v, "netlist": os.path.basename(cir), "ngspice_rc": rc, "wall_cap_s": cap,
            "kick_V": plan["kick_V"], "h_ref": pl["h_ref"], "cache": cst}


def _run_stab(exe, cir, timeout_s, cache_dir, outputs):
    """안정성 근거 실행(동작점 패스·과도·연장)용 run_ngspice. --timeout-s 로 끊기면(subprocess.TimeoutExpired) 죽지 않고
    (None, '', None, 사유) 를 돌려준다 -- 데이터 파일이 tstop 에 못 미쳐 절차 5 의 failed -> '모름'(README C10 절차 4).
    반환 (rc, 로그, 캐시 상태, timeout 사유 또는 None)."""
    try:
        rc, log, cst = run_ngspice(exe, cir, os.path.splitext(cir)[0] + ".log", timeout_s, cache_dir, outputs)
        return rc, log, cst, None
    except subprocess.TimeoutExpired:
        return None, "", None, f"ngspice 가 --timeout-s {timeout_s} s 에 끊겼다({os.path.basename(cir)})"


def stability_check(cir_path, meta, op, Ldata, exe, timeout_s=None, cache_dir=None, pm_raw=None):
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
    if sign:
        def _sample(fa, fb, ppd, tag):
            got = refine_samples(cir_path, meta, fa, fb, ppd, tag, exe, timeout_s, cache_dir)
            return None if not got else (got[0], [sign * x for x in got[1]], [sign * x for x in got[2]])
        nyq, _, _ = nyquist_adaptive(f, sign * L, _sample)
    else:
        nyq = {"encirclements_cw": None, "reason": "기준점 Re A = 0 -- 음되먹임 닫기 부호를 정할 수 없다"}
    out["nyquist"] = nyq
    d = os.path.dirname(os.path.abspath(cir_path))
    stem = os.path.splitext(os.path.basename(cir_path))[0]
    tr = {"status": "not_run", "reason": None}
    outs = meta.get("outputs") or []
    sn = meta.get("spice_node") or {}
    src = os.path.join(d, lm["netlist"]) if lm else cir_path
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    # 동작점 패스(개루프 .pz 와 폐루프 .tran 이 같이 쓴다): 같은 본문의 .op 로 choke 전류와 (입력·출력·choke 회로 쪽·절단 양쪽) 노드 전압
    input_nodes = {n: sn[n] for n in meta.get("inputs") or [] if n in sn}
    choke_I, node_V, op_rec, op_to = {}, {}, None, None
    if meta.get("output_nodes"):
        otext, chokes, onodes = stability_op_netlist(text, list(input_nodes.values()) + list(meta["output_nodes"]))
        ocir = os.path.join(d, f"{stem}.stabop.cir")
        with open(ocir, "w", encoding="utf-8") as fh:
            fh.write(otext)
        orc, olog, ocst, op_to = _run_stab(exe, ocir, timeout_s, cache_dir, [])
        choke_I = {c.lower(): _grab(olog, f"i({c.lower()})") for c in chokes}
        node_V = {n.lower(): _grab(olog, f"v({n.lower()})") for n in onodes}
        op_rec = {"netlist": os.path.basename(ocir), "ngspice_rc": orc, "cache": ocst, "choke_current_A": choke_I,
                  "node_V": node_V}
        if op_to:
            op_rec["timeout"] = op_to
    # 독립 P: 같은 루프 절단의 개루프 넷리스트에 `.pz`(사용자 결정 Q10). 시간 상한 = --timeout-s, 없으면 창당 상한 1 회분.
    if op_to:
        pz = {"status": "unavailable", "P": None, "reason": f"동작점 패스 시간 초과: {op_to}"}
    else:
        kind = None if not lm else ("cm" if meta.get("loop_kind") == "cm" else "dm")
        pz = pz_check(os.path.join(d, f"{stem}.pz.cir"), text, meta, node_V, choke_I,
                      timeout_s if timeout_s is not None else stability_config()["wall_s_per_window"],
                      cache_dir, exe, reltol_of(meta.get("tb_options")), float(f[-1]), kind)
    out["pz"] = pz
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
        wps = stability_config()["wall_s_per_window"]
        plan = tran_plan(cr, temp, solver_floor(meta.get("tb_options"), v_ops), f"{stem}.stab.txt",
                         f_crit_hz=band_f_crit(f, sign * L), reltol=reltol_of(meta.get("tb_options")),
                         wall_s_per_window=wps)
        if plan is None:
            tr["reason"] = "킥 V_T 가 해 분해능에 비해 작아 비교 창을 만들 수 없다"
        else:
            plan["sign"] = sign
            plan["input_nodes"] = input_nodes
            plan["choke_I"], plan["node_V"] = choke_I, node_V
            tr["op_pass"] = op_rec
            oto = op_to
            w = dict(zip(lm["break_nets"], lm["weights"])) if lm else dict(meta.get("input_ac_weights") or {})
            stext, missing = stability_netlist(text, mode, w, meta["output_nodes"], plan)
            tr["plan"] = {k: v for k, v in plan.items() if k not in ("file", "choke_I", "node_V", "input_nodes")}
            if oto:
                tr.update(status="failed", reason=f"동작점 패스 시간 초과: {oto}", timeout=oto)
            elif missing or not w:
                tr.update(status="failed", reason=f"과도 넷리스트를 만들 수 없다(킥 넷·동작점 값 없음): {missing or '(가중 없음)'}")
            else:
                scir = os.path.join(d, f"{stem}.stab.cir")
                with open(scir, "w", encoding="utf-8") as fh:
                    fh.write(stext)
                sfile = os.path.join(d, plan["file"])
                if os.path.exists(sfile):
                    os.remove(sfile)
                # 실행 시간 상한(계약 1(c)): --timeout-s 가 있으면 그것(사용자 지정 우선), 없으면 계획 상한 wall_s_per_window × K
                cap = timeout_s if timeout_s is not None else plan["wall_cap_s"]
                t_run0 = time.monotonic()
                rc, slog, cst, sto = _run_stab(exe, scir, cap, cache_dir, [plan["file"]])
                t_first = time.monotonic() - t_run0
                dec = transient_decision(sfile, plan)
                if sto:  # 끊긴 과도는 tstop 에 못 미친다 -> failed(부분 파일로 판정하지 않는다)
                    dec.update(status="failed", reason=f"과도 시간 초과: {sto}")
                tr.update(dec)
                tr.update(netlist=os.path.basename(scir), file=plan["file"], ngspice_rc=rc, cache=cst, wall_cap_s=cap)
                if sto:
                    tr["timeout"] = sto
                tr["first_status"] = dec["status"]
                p2 = extension_plan(plan, dec, f"{stem}.stab2.txt", wps)
                dec2 = None
                if p2 is not None:  # 감쇠가 일관되지만 floor' 위 -> 투영한 길이만큼 늘려 감쇠를 입증
                    s2text, _ = stability_netlist(text, mode, w, meta["output_nodes"], p2)
                    s2cir = os.path.join(d, f"{stem}.stab2.cir")
                    with open(s2cir, "w", encoding="utf-8") as fh:
                        fh.write(s2text)
                    s2file = os.path.join(d, p2["file"])
                    if os.path.exists(s2file):
                        os.remove(s2file)
                    cap2 = timeout_s if timeout_s is not None else p2["wall_cap_s"]
                    rc2, _, cst2, s2to = _run_stab(exe, s2cir, cap2, cache_dir, [p2["file"]])
                    dec2 = transient_decision(s2file, p2)
                    if s2to:
                        dec2.update(status="failed", reason=f"연장 실행 시간 초과: {s2to}", timeout=s2to)
                    tr["extension"] = {**dec2, "netlist": os.path.basename(s2cir), "file": p2["file"],
                                       "ngspice_rc": rc2, "cache": cst2, "extension_windows": p2["extension_windows"],
                                       "tstop": p2["tstop"], "wall_cap_s": cap2}
                tr["status"] = final_transient_status(dec, dec2)
                if tr["status"] != dec["status"]:
                    tr["reason"] = (f"첫 실행 {dec['status']}({dec['reason']}) -> 연장 실행 "
                                    f"{(dec2 or {}).get('status')}({(dec2 or {}).get('reason')})")
                # `.pz` 의 RHP 극(P >= 1)은 폐루프 과도가 정해지지 않은 회로에서만 개루프 과도로 확인해 쓴다(pz_validate)
                if tr["status"] not in ("stable", "unstable") and pz.get("status") == "ok" and (pz.get("P") or 0) >= 1:
                    # 시간 예산: 과도가 쓰고 남은 계획 상한(plan.wall_cap_s - 과도 시간)을 주되 최소 창 하나 몫(wall_s_per_window)은 보장한다 --
                    # 증가하는 회로는 창 3 안에 확인되어 짧고, 상한은 느린 확인이 무한정 길어지지 않게 하는 것이다(--timeout-s 가 있으면 그것).
                    cap_v = timeout_s if timeout_s is not None else max(plan["wall_cap_s"] - t_first, wps)
                    pz["validation"] = pz_validate(d, stem, text, meta, input_nodes, node_V, choke_I, plan,
                                                   None if not lm else ("cm" if meta.get("loop_kind") == "cm" else "dm"),
                                                   exe, cap_v, cache_dir)
                    pz["validated"] = pz["validation"]["validated"]
    out["transient"] = tr
    lc = tr.get("limit_cycle_vs_slow_decay_unresolved") or (tr.get("extension") or {}).get("limit_cycle_vs_slow_decay_unresolved")
    if lc:
        out["limit_cycle_vs_slow_decay_unresolved"] = lc
    out.update(stability_judgement(nyq, tr.get("status"), pm_raw, pz))
    out["gain_crossings_hz"] = cr
    return out


def cm_loop_measure(cir_path, meta, op, exe, timeout_s=None, cache_dir=None):
    """공통 모드(CMFB) 루프 PM (meta.cm_loop 가 있을 때). 평균 감지 넷을 끊은 넷리스트 <stem>.cmloop.cir 에서 DM β 루프와 같은
    Middlebrook 이중 주입(loop_gain)으로 T_cm 을 재고, ac_measures 로 PM 을 낸 뒤 DM 과 같은 C10 안정성 근거(Nyquist +
    폐루프 .tran, apply_stability)를 건다 -- P = 0 이 증명되지 않으면 PM 은 정의 불가(pm_undefined). 안정성 파일은
    <stem>.cmloop.stab*.cir/txt 로 DM 것과 겹치지 않는다. op = 본 시뮬 결과(출력 동작점, floor 용). 반환 dict:
    ngspice_rc, break_nets, measures(ac_measures), singular, pm_deg, pm_undefined, pm_deg_raw, stability, stability_cache."""
    cm = meta["cm_loop"]
    d = os.path.dirname(os.path.abspath(cir_path))
    ccir = os.path.join(d, cm["netlist"])
    vf, inf = os.path.join(d, cm["v_file"]), os.path.join(d, cm["i_file"])
    for x in (vf, inf):
        if os.path.exists(x):
            os.remove(x)
    rc, log, cst = run_ngspice(exe, ccir, os.path.splitext(ccir)[0] + ".log", timeout_s, cache_dir,
                               [cm["v_file"], cm["i_file"]])
    sing = loop_probe_singular(vf, inf, cm["weights"])
    t = None if sing else loop_gain(vf, inf, cm["weights"])
    out = {"ngspice_rc": rc, "cache": cst, "break_nets": cm["break_nets"], "weights": cm["weights"],
           "log_errors": [ln.strip() for ln in log.splitlines() if re.search(r"error|fatal|singular|abort", ln, re.I)][:40],
           "measures": ac_measures(*t) if t else None, "singular": None}
    if sing:
        out["singular"] = {"count": len(sing), "first": sing[0], "points": sing[:20]}
    shadow = {"ac": dict(out["measures"]) if out["measures"] else {"pm_deg": None}, "nodes": (op or {}).get("nodes")}
    apply_stability(shadow, ccir, dict(meta, loop=cm, loop_kind="cm"), t, exe, timeout_s, cache_dir)
    ac = shadow["ac"]
    out.update(pm_deg=ac.get("pm_deg"), pm_deg_raw=ac.get("pm_deg_raw"), pm_undefined=ac.get("pm_undefined"),
               stability=ac.get("stability"), stability_cache=shadow.get("stability_cache"))
    if sing:
        out["pm_undefined"] = LOOP_PROBE_SINGULAR
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
                "op_ok": False, "ac": None, "ac_file": None, "loop": None, "cm_loop": None, "ratio": [], "rout": []}
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
        sing = loop_probe_singular(vf, inf, lm["weights"])
        t = None if sing else loop_gain(vf, inf, lm["weights"])
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
        if sing:  # T 가 정의되지 않는 표본 -> 루프 측정 전체가 정의 불가(측정 실패 아님, 막힘 아님)
            res["loop"]["singular"] = {"count": len(sing), "first": sing[0], "points": sing[:20]}
    res["cm_loop"] = cm_loop_measure(cir_path, meta, res, exe, timeout_s, cache_dir) if meta.get("cm_loop") else None
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
        sg = (res["loop"] or {}).get("singular")
        if sg:  # PM 은 측정 실패가 아니라 정의 불가(값에 따른 불가능 -> N/A(정의 불가) -> PASS 불가)
            res["ac"]["pm_undefined"] = LOOP_PROBE_SINGULAR
            res["ac"]["stability"]["reason"] = (f"β 루프 T 정의 불가: Middlebrook 분모 0 인 표본 {sg['count']}개(첫 표본 "
                                                f"{sg['first']['f_hz']:.4g} Hz, {sg['first']['which']})")
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
    st = stability_check(cir_path, meta, res, Ldata, exe, timeout_s, cache_dir, ac.get("pm_deg"))
    # 캐시 상태는 결과가 아니다(C21: hit 이든 miss 든 ac 는 같아야 한다) -- sim.stability_cache 로 뺀다
    tr = st.get("transient") or {}
    res["stability_cache"] = {"op_pass": (tr.get("op_pass") or {}).pop("cache", None), "transient": tr.pop("cache", None)}
    if tr.get("extension"):  # 연장 실행을 했을 때만 키가 생긴다
        res["stability_cache"]["extension"] = tr["extension"].pop("cache", None)
    if (st.get("pz") or {}).get("validation"):  # `.pz` 개루프 과도 확인을 했을 때만 키가 생긴다
        res["stability_cache"]["pz_validation"] = st["pz"]["validation"].pop("cache", None)
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
