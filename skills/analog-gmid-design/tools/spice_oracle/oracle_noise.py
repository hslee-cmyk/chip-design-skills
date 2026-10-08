# -*- coding: utf-8 -*-
"""oracle_noise.py -- ngspice `.noise` 대조 측정 (설계 40 §4·§11 U6, 41 §7.6, 사용자 결정 2026-10-08 Q11 "노이즈 spec 을 추가").

진입점(단독 실행):
    python oracle_noise.py <oracle_input.json> <netlist.cir> <out_noise.json> --ngspice <ngspice_con.exe>
                           [--timeout-s S] [--cache-dir D]

  <netlist.cir> = oracle_netlist.py 가 쓴 free 본 넷리스트(+ .meta.json, 루프 넷리스트). 입력 JSON 의 `noise` 블록이 있을 때만 의미가 있다.
  엔진을 import 하지 않는다(P N3.8). 결과 JSON = noise_measure() 의 반환.

입력 `noise` 블록(선택, 스키마 oracle_input.schema.json):
  f_lo_hz               필수. 열잡음 평탄값·적분의 하한(엔진 LUT 가 실측한 가장 낮은 잡음 점 -- 외삽하지 않는다)
  points_per_decade     주파수 격자 밀도(기본 testbench.ac.points_per_decade)
  input_cell_devices    noise_excess_th 의 분모 소자(입력 셀) 이름 목록
  closed_loop           true 면 feedback_passives 로 닫은 루프 넷리스트(`.loop.cir`)에서 폐루프 적분 잡음 noise_out_int_vrms 를 잰다
  rel_resolution        적분 꼬리 판정의 상대 분해능 r(기본 = ngspice reltol)

측정(전부 `.noise`, 입력 환산은 같은 주파수의 `.ac` 차동 이득으로)
  * 개루프(noise_th_in_v2hz, noise_fc_in_hz, noise_excess_th, noise_contrib): 주파수 f 마다 `noise v(out) <Vac> lin 2 f f(1+δ) 1` 로
    소스별 적분값(ngspice 는 sqrt(∫S df) 를 낸다)을 얻고 S_k(f) = v_k²/Δf 로 밀도를 구한다(δ = reltol: 평균과 점값 차 <= δ/2).
    열 성분 = 1overf 가 아닌 모든 소스(MOS .id·.rd·.rs·.rg·.rb*·게이트 누설 shot, 저항 thermal), flicker = `1overf` 소스.
    입력 환산 S_in(f) = Σ_k S_k(f) / |H(f)|²(H = 같은 넷리스트의 차동/단일 AC 이득, 1 점 `.ac`).
      noise_th_in_v2hz = Σ(열 성분) 의 f_lo 값(저주파 평탄 영역; 엔진 정의 Σ|Z_k/H|² gm_k² B_k 와 같다)
      noise_fc_in_hz   = 입력 환산 flicker 합이 noise_th_in_v2hz 와 같아지는 주파수(f_lo 부터 격자를 올려 첫 교차를 로그-로그 보간;
                         f_lo 에서 이미 아래면 None + below_f_lo, 격자 끝까지 못 만나면 None + above_cap)
      noise_excess_th  = noise_th_in_v2hz / (input_cell_devices 만의 열 성분 합)
      noise_contrib    = 소자·저항별 [{element, thermal_in_v2hz, flicker_in_v2hz, share_thermal}] (f_lo)
  * 폐루프(noise_out_int_vrms): 루프 넷리스트를 닫은 채(Vlb DC 0) `noise v(out) Vlb_<넷> dec ppd f_lo f_top` 의 onoise_spectrum 을
    로그 격자 사다리꼴로 적분(밀도를 절반으로 줄여 같은 적분이 reltol 안에 일치하는지 보고 아니면 밀도 두 배, 상한 K 번).
    f_top = 테스트벤치 `.ac` fstop 에서 시작해 꼬리 상계 S(f)·f(>= 1 극 감쇠에서 성립) 가 (r·v_rms)² 이하가 될 때까지 10 배씩
    올린다(상한 NOISE_TOP_K_MAX). 못 맞추면 converged = False + 꼬리 상계를 같이 보고.
    스위치 kT/C 항은 이 모듈이 재지 않는다(`ktc_sampling` = not_measured: 샘플링 위상 과도 평균이 필요 -- README).
"""
import argparse
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle_simulate import reltol_of, run_ngspice  # noqa: E402

NOISE_TOP_K_MAX = 8     # 폐루프 적분 상한 확장 횟수(10 배씩 -> fstop 의 1e8 배까지)
INTEGRAL_K_MAX = 4      # 적분 격자 밀도를 두 배씩 올리는 횟수 상한

_VEC = re.compile(r"^\s*([io]noise_total[^\s=]*)\s*=\s*([-+0-9.eE]+)\s*$", re.M)
_MOS = re.compile(r"^[io]noise_total\.m\.x?(?P<inst>[^.]+)\.m[^.]*?(?:\.(?P<src>[a-z0-9]+))?$")
_RES = re.compile(r"^[io]noise_total_(?P<el>.+?)(?:_(?P<src>thermal|1overf))?$")


def oracle_element_names(name):
    """입력 JSON 소자 이름 -> 오라클 넷리스트의 .noise 요소 이름 후보(소문자). MOS(X<이름>)는 이름 자체, 수동·이상원 소자는 CIRCUIT_PREFIXES 의
    접두(Rp_·Cp_·Isrc_·Vsrc_) 붙은 이름. 이미 접두가 붙은 이름은 그대로도 후보다."""
    from oracle_netlist import CIRCUIT_PREFIXES
    n = str(name).lower()
    return [n] + [pre.lower() + n for pre in CIRCUIT_PREFIXES if pre != "X"]


def _out_spec(output_nodes):
    a, b = output_nodes[0], output_nodes[1]
    return f"v({a})" if b == "0" else f"v({a},{b})"


def _hexpr(text):
    """본 넷리스트 .control 의 `let hout = <식>`(AC 이득 식). 없으면 None."""
    for ln in text.splitlines():
        m = re.match(r"\s*let\s+hout\s*=\s*(.*)$", ln, re.I)
        if m:
            return m.group(1).strip()
    return None


def _first_vac(text):
    for ln in text.splitlines():
        tok = ln.split()
        if tok and tok[0].startswith("Vac_"):
            return tok[0]
    return None


def _body(text):
    out = []
    for raw in text.splitlines():
        if raw.strip().lower().startswith(".control"):
            break
        out.append(raw)
    return out


def parse_noise_totals(log):
    """`print all` 로 찍힌 noise 합계 벡터 -> {소스 키: {'onoise': V, 'inoise': V}} 가 아니라 요소별 dict.
    반환 list[(kind, element, source, value)]: kind 'o'|'i', element = 소자 인스턴스(소문자; MOS 는 'm1' 처럼 X 접두 뗀 이름) 또는
    저항 요소 이름, source = 'id'|'1overf'|'rd'|... | 'thermal'|'1overf'(저항), 소자 합계 줄(source 없음)은 제외."""
    out = []
    for name, val in _VEC.findall(log):
        v = float(val)
        m = _MOS.match(name)
        if m:
            if m.group("src") is None:
                continue                     # 소자 합계 줄(소스별 줄의 합)
            out.append((name[0], m.group("inst"), m.group("src"), v))
            continue
        m = _RES.match(name)
        if m and m.group("src") is not None:
            out.append((name[0], m.group("el"), m.group("src"), v))
    return out


def _is_flicker(src):
    return src == "1overf"


def noise_open_loop(cir_path, meta, inp, exe, timeout_s=None, cache_dir=None):
    """개루프 `.noise` 측정(모듈 머리말). 반환 dict {status, th_in_v2hz, fc_in_hz, excess_th, contrib, grid, ...}."""
    nz = inp.get("noise") or {}
    d = os.path.dirname(os.path.abspath(cir_path))
    stem = os.path.splitext(os.path.basename(cir_path))[0]
    with open(cir_path, encoding="utf-8") as fh:
        text = fh.read()
    out = {"status": "failed", "reason": None, "th_in_v2hz": None, "fc_in_hz": None, "excess_th": None, "contrib": [],
           "f_lo_hz": nz.get("f_lo_hz"), "method": "ngspice .noise (소스별 합계, 좁은 대역 lin 2) + .ac 이득"}
    hexpr, src = _hexpr(text), _first_vac(text)
    outs = meta.get("output_nodes")
    f_lo = nz.get("f_lo_hz")
    if not hexpr or not src or not outs or not f_lo:
        out["reason"] = "본 넷리스트에 AC 이득 식(let hout)·입력 Vac 원·출력 노드가 없거나 noise.f_lo_hz 가 없다"
        return out
    tb = inp["testbench"]
    reltol = reltol_of(tb.get("options"))
    ppd = int(nz.get("points_per_decade") or tb["ac"]["points_per_decade"])
    f_cap = float(tb["ac"]["fstop_hz"])
    n_dec = max(1, math.ceil(math.log10(f_cap / f_lo)))
    freqs = [f_lo * 10 ** (k / ppd) for k in range(n_dec * ppd + 1) if f_lo * 10 ** (k / ppd) <= f_cap]
    delta = reltol
    ctrl = [".control", "set noaskquit", "set wr_singlescale"]
    for f in freqs:
        f2 = f * (1 + delta)
        ctrl += [f"echo NZF {f:.12g}", f"ac lin 1 {f:.12g} {f:.12g}", f"let hout = {hexpr}", "print hout",
                 f"noise {_out_spec(outs)} {src} lin 2 {f:.12g} {f2:.12g} 1", "print all"]
    ctrl += ["quit", ".endc", ".end"]
    ncir = os.path.join(d, f"{stem}.noise.cir")
    with open(ncir, "w", encoding="utf-8") as fh:
        fh.write("\n".join(_body(text) + ctrl) + "\n")
    import subprocess
    try:
        rc, log, _ = run_ngspice(exe, ncir, os.path.splitext(ncir)[0] + ".log", timeout_s, cache_dir, [])
    except subprocess.TimeoutExpired:
        out["reason"] = f".noise 가 시간 상한 {timeout_s} s 에 끊겼다"
        return out
    out["ngspice_rc"] = rc
    blocks = re.split(r"^NZF\s+", log, flags=re.M)[1:]
    rows = []
    for blk in blocks:
        f = float(blk.split()[0])
        mh = re.search(r"^hout\s*=\s*([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)", blk, re.M)
        if not mh:
            continue
        h2 = float(mh.group(1)) ** 2 + float(mh.group(2)) ** 2
        df = f * delta
        srcs = {}
        for kind, el, s, v in parse_noise_totals(blk):
            if kind == "o":
                srcs[(el, s)] = v * v / df          # 출력 PSD [V²/Hz]
        if h2 > 0 and srcs:
            rows.append((f, h2, srcs))
    if not rows:
        out["reason"] = "ngspice 로그에서 noise 합계를 읽지 못했다: " + " | ".join(
            ln.strip() for ln in log.splitlines() if re.search(r"error|fatal|singular", ln, re.I))[:400]
        return out

    def split(srcs, h2, only=None):
        th = sum(v for (el, s), v in srcs.items() if not _is_flicker(s) and (only is None or el in only)) / h2
        fl = sum(v for (el, s), v in srcs.items() if _is_flicker(s) and (only is None or el in only)) / h2
        return th, fl

    f0, h20, s0 = rows[0]
    th_in, fl0 = split(s0, h20)
    out.update(status="ok", f_eval_hz=f0, th_in_v2hz=th_in, flicker_in_at_f_lo_v2hz=fl0)
    # 소자·저항별 기여 (f_lo)
    els = sorted({el for (el, _) in s0})
    contrib = []
    for el in els:
        t, fl = split(s0, h20, {el})
        contrib.append({"element": el, "thermal_in_v2hz": t, "flicker_in_v2hz": fl,
                        "share_thermal": (t / th_in) if th_in else None})
    out["contrib"] = sorted(contrib, key=lambda c: -(c["thermal_in_v2hz"] or 0))
    # excess
    if nz.get("input_cell_devices"):
        # 입력 셀 소자 이름 -> 오라클 넷리스트 이름(설계 40 §4 C10 8 후속 (v)): MOS 는 X<이름> 인스턴스의 벡터 이름 '<이름>'(소문자), 수동소자는
        # 접두 붙은 요소(Rp_<이름> 저항 등 -- oracle_netlist.CIRCUIT_PREFIXES 표) 의 '<접두><이름>'(소문자). 선언 이름마다 후보를 모두 찾는다.
        cand = {n: oracle_element_names(n) for n in nz["input_cell_devices"]}
        low = {el.lower(): el for el in els}
        cell_el = {low[c] for cs in cand.values() for c in cs if c in low}
        want = {n for n, cs in cand.items() if not any(c in low for c in cs)}
        t_cell, _ = split(s0, h20, cell_el)
        out["input_cell_matched"] = sorted(cell_el)
        out["input_cell_missing"] = sorted(want)
        # fail-closed: 선언된 입력 셀 소자 중 하나라도 오라클 넷리스트 요소로 못 찾으면 부분집합으로 계산하지 않는다(분모가 작아져 과대 평가).
        if want:
            out["excess_th"] = None
            out["excess_reason"] = "입력 셀 소자를 오라클 넷리스트에서 못 찾음(input_cell_missing): " + ", ".join(sorted(want))
        else:
            out["excess_th"] = (th_in / t_cell) if t_cell else None
        if not want and not t_cell:
            out["excess_reason"] = "입력 셀 소자의 열 성분이 0 이다(이름이 안 맞거나 꺼진 소자)"
    else:
        out["excess_reason"] = "noise.input_cell_devices 가 없다"
    # 코너 주파수
    grid = []
    for f, h2, srcs in rows:
        t, fl = split(srcs, h2)
        grid.append({"f_hz": f, "thermal_in_v2hz": t, "flicker_in_v2hz": fl, "gain_abs2": h2})
    out["grid"] = grid
    prev = None
    fc, why = None, "above_cap"
    if grid[0]["flicker_in_v2hz"] <= th_in:
        fc, why = None, "below_f_lo"
    else:
        for g in grid[1:]:
            if g["flicker_in_v2hz"] <= th_in:
                a = prev if prev else grid[0]
                la, lb = math.log10(a["flicker_in_v2hz"]), math.log10(g["flicker_in_v2hz"])
                lt = math.log10(th_in)
                lf = math.log10(a["f_hz"]) + (la - lt) / (la - lb) * (math.log10(g["f_hz"]) - math.log10(a["f_hz"]))
                fc, why = 10 ** lf, None
                break
            prev = g
    out["fc_in_hz"], out["fc_reason"] = fc, why
    return out


def _read_spectrum(path):
    f, s = [], []
    with open(path) as fh:
        for ln in fh:
            try:
                v = [float(x) for x in ln.split()]
            except ValueError:
                continue
            if len(v) >= 2:
                f.append(v[0])
                s.append(v[1])
    return f, s


def _trapz_log(f, s):
    """로그 주파수 격자 위 사다리꼴 ∫ S df."""
    return sum(0.5 * (s[i] + s[i + 1]) * (f[i + 1] - f[i]) for i in range(len(f) - 1))


def noise_closed_loop(cir_path, meta, inp, exe, timeout_s=None, cache_dir=None):
    """폐루프 적분 출력 잡음 noise_out_int_vrms(모듈 머리말). 루프 넷리스트(feedback_passives 로 닫음)가 없으면 status = unavailable."""
    nz = inp.get("noise") or {}
    lm = meta.get("loop")
    out = {"status": "unavailable", "reason": None, "out_int_vrms": None, "converged": None,
           "ktc_sampling": {"status": "not_measured",
                            "reason": "샘플링 kT/C 는 샘플링 위상 과도(trnoise 평균)가 필요하다 -- 이 모듈은 주파수 영역 .noise 만 쓴다(README)"}}
    if not lm:
        out["reason"] = "feedback_passives 가 없어 루프 넷리스트가 없다(폐루프 되먹임 요소 미선언)"
        return out
    d = os.path.dirname(os.path.abspath(cir_path))
    with open(os.path.join(d, lm["netlist"]), encoding="utf-8") as fh:
        text = fh.read()
    outs = meta.get("output_nodes")
    src = next((ln.split()[0] for ln in text.splitlines() if ln.startswith("Vlb_")), None)
    f_lo = nz.get("f_lo_hz")
    if not outs or not src or not f_lo:
        out["reason"] = "루프 넷리스트에 Vlb 원·출력 노드가 없거나 noise.f_lo_hz 가 없다"
        return out
    tb = inp["testbench"]
    reltol = reltol_of(tb.get("options"))
    r = float(nz.get("rel_resolution") or reltol)
    ppd = int(nz.get("points_per_decade") or tb["ac"]["points_per_decade"])
    f_top = float(tb["ac"]["fstop_hz"])
    import subprocess
    stem = os.path.splitext(lm["netlist"])[0]
    body = _body(text)
    k_top = 0
    while True:
        # 격자 밀도를 올려 가며(적분 수렴) 같은 구간을 잰다
        p, prev_int, spec = ppd, None, None
        for kk in range(INTEGRAL_K_MAX + 1):
            sfile = f"{stem}.noise{k_top}_{kk}.txt"
            ctrl = [".control", "set noaskquit", "set wr_singlescale",
                    f"noise {_out_spec(outs)} {src} dec {p} {f_lo:.12g} {f_top:.12g} 1", "setplot noise1",
                    f"wrdata {sfile} onoise_spectrum", "quit", ".endc", ".end"]
            ncir = os.path.join(d, f"{stem}.noise{k_top}_{kk}.cir")
            with open(ncir, "w", encoding="utf-8") as fh:
                fh.write("\n".join(body + ctrl) + "\n")
            if os.path.exists(os.path.join(d, sfile)):
                os.remove(os.path.join(d, sfile))
            try:
                run_ngspice(exe, ncir, os.path.splitext(ncir)[0] + ".log", timeout_s, cache_dir, [sfile])
            except subprocess.TimeoutExpired:
                out.update(status="failed", reason=f".noise 가 시간 상한 {timeout_s} s 에 끊겼다")
                return out
            if not os.path.exists(os.path.join(d, sfile)):
                out.update(status="failed", reason="onoise_spectrum 데이터 파일이 없다(ngspice .noise 실패)")
                return out
            f, s = _read_spectrum(os.path.join(d, sfile))
            s2 = [x * x for x in s]            # onoise_spectrum 은 V/sqrt(Hz)
            integ = _trapz_log(f, s2)
            spec = (f, s2)
            if prev_int is not None and abs(integ - prev_int) <= reltol * integ:
                break
            prev_int, p = integ, p * 2
        f, s2 = spec
        cum = integ
        tail = s2[-1] * f[-1]
        out.update(status="ok", out_int_v2=integ, out_int_vrms=math.sqrt(integ), f_lo_hz=f_lo, f_hi_hz=f[-1],
                   points_per_decade=p, tail_bound_v2=tail, rel_resolution=r, integral_converged=(kk <= INTEGRAL_K_MAX
                   and prev_int is not None and abs(integ - prev_int) <= reltol * integ),
                   top_extensions=k_top)
        if tail <= (r ** 2) * cum:
            out["converged"] = True
            return out
        if k_top >= NOISE_TOP_K_MAX:
            out["converged"] = False
            out["reason"] = (f"꼬리 상계 S(f)·f = {tail:.3g} V² 가 (r·v_rms)² = {(r ** 2) * cum:.3g} V² 보다 크다 -- "
                             f"상한 확장 {NOISE_TOP_K_MAX} 회로도 못 맞춤(보고 값은 f_hi 까지의 적분)")
            return out
        k_top += 1
        f_top *= 10


def noise_measure(inp, cir_path, meta, exe, timeout_s=None, cache_dir=None):
    """sim.noise = {open_loop, closed_loop} (입력 `noise` 블록이 있을 때)."""
    nz = inp.get("noise")
    if not nz:
        return None
    res = {"open_loop": noise_open_loop(cir_path, meta, inp, exe, timeout_s, cache_dir)}
    res["closed_loop"] = noise_closed_loop(cir_path, meta, inp, exe, timeout_s, cache_dir) if nz.get("closed_loop") else None
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description="ngspice .noise 대조 측정")
    ap.add_argument("oracle_input")
    ap.add_argument("netlist")
    ap.add_argument("out_json")
    ap.add_argument("--ngspice", required=True)
    ap.add_argument("--timeout-s", type=float, default=None)
    ap.add_argument("--cache-dir", default=None)
    a = ap.parse_args(argv)
    with open(a.oracle_input, encoding="utf-8") as f:
        inp = json.load(f)
    with open(a.netlist + ".meta.json", encoding="utf-8") as f:
        meta = json.load(f)
    res = noise_measure(inp, a.netlist, meta, a.ngspice, a.timeout_s, a.cache_dir)
    with open(a.out_json, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    ol = (res or {}).get("open_loop") or {}
    print("wrote", a.out_json, "th_in_v2hz=", ol.get("th_in_v2hz"), "fc_in_hz=", ol.get("fc_in_hz"))
    return 0 if ol.get("status") == "ok" else 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
