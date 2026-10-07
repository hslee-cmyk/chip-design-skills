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
          simulate(cir_path, meta, exe, timeout_s, cache_dir)
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


def simulate(cir_path, meta, exe, timeout_s=None, cache_dir=None):
    base = os.path.splitext(cir_path)[0]
    log_path = base + ".log"
    ac_path = os.path.join(os.path.dirname(os.path.abspath(cir_path)), meta["ac_file"]) if meta.get("ac_file") else None
    if ac_path and os.path.exists(ac_path):
        os.remove(ac_path)
    if meta.get("blockers"):
        # 막힌 넷리스트는 돌리지 않는다(지어낸 값으로 채운 회로를 재지 않는다 -- README C2/C8)
        return {"skipped": "넷리스트 막힘: " + " | ".join(meta["blockers"]), "devices": {}, "nodes": {},
                "rail_current_A": {}, "hold_current_A": {}, "ngspice_rc": None, "log": None, "log_errors": [],
                "op_ok": False, "ac": None, "ac_file": None, "loop": None}
    rc, log, cst = run_ngspice(exe, cir_path, log_path, timeout_s, cache_dir,
                               [meta["ac_file"]] if meta.get("ac_file") else [])
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
    res["loop"] = None
    lm = meta.get("loop")
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
        res["loop"] = {"ngspice_rc": lrc, "break_nets": lm["break_nets"],
                       "log_errors": [ln.strip() for ln in llog.splitlines()
                                      if re.search(r"error|fatal|singular|abort", ln, re.I)][:40],
                       "measures": ac_measures(*t) if t else None,
                       "pm_crosscheck": pm_crosscheck(*t, mp_res=lres) if t else None}
    if res["ac"] is not None:
        res["ac"]["pm_open_loop_deg"] = res["ac"]["pm_deg"]
        if lm:
            lt = (res["loop"] or {}).get("measures") or {}
            res["ac"]["pm_deg"] = lt.get("pm_deg")
            res["ac"]["pm_definition"] = "beta_loop"
            res["ac"]["loop_ugf_hz"] = lt.get("ugf_hz")
            res["ac"]["loop_gain_dc_db"] = lt.get("dc_gain_db")
            xc = (res["loop"] or {}).get("pm_crosscheck") or {}
        else:
            res["ac"]["pm_definition"] = "beta_1"
            # A 한 표본 = 데이터 파일 실수 2개(출력/입력 복소)
            xc = pm_crosscheck(*raw, mp_res=mp_resolution(data_rel_resolution(ac_path), 2))
        res["ac"].update({k: xc.get(k) for k in ("pm_crosscheck_deg", "pm_crosscheck_note", "pm_crosscheck_method",
                                                 "pm_crosscheck_mp_resolution",
                                                 "closed_loop_peaking_db", "closed_loop_peak_hz")})
        pc, pm = res["ac"].get("pm_crosscheck_deg"), res["ac"].get("pm_deg")
        res["ac"]["pm_crosscheck_gap_deg"] = None if pc is None or pm is None else pc - pm
    return res


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
