# -*- coding: utf-8 -*-
"""oracle_offset_mc.py -- 입력 환산 랜덤 offset 1σ 의 ngspice Monte-Carlo (설계 40 §10.2·41 §6.4-2, 사용자 결정 2026-10-08 Q3).

진입점(단독 실행):
    python oracle_offset_mc.py <oracle_input.json> <netlist.cir> <out_mc.json> --ngspice <ngspice_con.exe>
                               [--timeout-s S] [--cache-dir D]

  <netlist.cir> = oracle_netlist.py 가 쓴 free 본 넷리스트(+ .meta.json). 입력 JSON 의 `offset_mc` 블록이 있을 때만 의미가 있다.
  엔진을 import 하지 않는다. 결과 JSON = offset_mc_measure() 의 반환.

입력 `offset_mc` 블록(선택):
  rel_resolution   필수. MC σ 추정의 목표 상대 표준오차 r(엔진의 offset resolution). 표본 수 N = ceil(1 + 1/(2 r²)) --
                   정규 표본의 표본 표준편차 상대 표준오차가 1/sqrt(2(N-1)) 이므로 이것을 r 로 둔 것(유도, 상수 없음).
  seed             난수 시드(기본 0, 결과에 기록)
  max_samples      표본 수 상한(넘으면 상한으로 줄이고 n_capped = True + 실제 상대 표준오차를 보고)

방법
  * 모델 카드의 mismatch 변수 `<subckt>__{toxe,vth0,voff,...}_slope_spectre`(PDK 가 `.param ... = 0.0` 으로 선언, 표준정규를 기대하는
    변수 -- 카드 안 `vth0 = vth0_0 + slope_spectre*(vth0_slope/sqrt(l*w*mult))`)를 **소자마다 독립으로** 흔든다: 소자 k 마다 래퍼
    subckt `mmv_<이름>` 안에서 그 변수들을 지역 `.param` 으로 덮어(ngspice 가 모델 `{식}` 을 래퍼 인스턴스 범위에서 평가함 -- 실측) 인스턴스
    줄을 래퍼 호출로 바꾼다. 표본마다 `alterparam` 으로 전역 `.param pv_<이름>_<j>` 를 바꾸고 `reset` + `op` (한 번의 ngspice 실행).
  * 단위: 카드는 l·w 가 µm 숫자라고 가정(`.option scale=1u`)하지만 오라클 넷리스트는 SI 숫자를 주므로 sqrt(l*w*mult) 가 1e-6 배다.
    또 인스턴스 m(병렬)은 카드의 mult 가 아니라서 면적에 안 들어간다. 그래서 변수값 = z·1e-6/sqrt(m) (z ~ N(0,1))로 두어
    σ(ΔP) = slope/sqrt(L_um·W_um·m) (엔진 41 §6.4-2 A_eff 모델과 같은 면적 의존)을 얻는다.
  * 입력 환산 offset(차동 입력 쌍 + DC 되먹임 servo 가 있는 free 넷리스트): 표본마다 DC 해에서
        V_os,k = (V_out,k - V_out,0)/A - (V_id,k - V_id,0)       (A = 같은 넷리스트의 DC 차동 이득 부호 포함, 0 = 흔들림 없는 기준 해)
    V_id = V(input_p) - V(input_n) (servo 가 출력을 묶으려고 건 입력), V_out = 출력 차동 또는 단일 전압. 계통 offset 은 기준 해와의 차에서 이미
    빠진다(σ 와 평균은 흔들림만의 것). 입력이 차동 쌍이 아니거나 servo 가 없으면 status = unavailable + 이유.
"""
import argparse
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle_simulate import parse_ac_file, run_ngspice  # noqa: E402

_NODE_RE = re.compile(r"^\s*(v)\(([^)]+)\)\s*=\s*([-+0-9.eE]+)\s*$", re.I | re.M)


def sample_count(rel_resolution, max_samples=None):
    """N = ceil(1 + 1/(2 r²)). 반환 (N, 상한에 걸렸는가, 실제 상대 표준오차 1/sqrt(2(N-1)))."""
    n = math.ceil(1 + 1 / (2 * rel_resolution ** 2))
    capped = False
    if max_samples is not None and n > max_samples:
        n, capped = int(max_samples), True
    return n, capped, 1 / math.sqrt(2 * (n - 1))


def mismatch_vars(text, subckt):
    """넷리스트가 .include/.lib 로 읽는 모델 파일 머리(앞 300 줄)에서 `<subckt>__*_slope_spectre` 변수 이름 목록(선언 순서)."""
    names = []
    for m in re.finditer(r"""^\s*\.(?:include|inc|lib)\s+["']?([^"'\s]+)["']?""", text, re.I | re.M):
        p = m.group(1)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            for i, ln in enumerate(fh):
                if i > 300:
                    break
                mm = re.match(r"\s*\.param\s+(" + re.escape(subckt) + r"__\w+_slope_spectre)\s*=", ln, re.I)
                if mm and mm.group(1) not in names:
                    names.append(mm.group(1))
    return names


def build_mc_netlist(text, inp, meta, samples, a_signed):
    """본 넷리스트 본문의 소자 인스턴스 줄을 소자별 래퍼 subckt 호출로 바꾸고, 표본마다 alterparam/reset/op 를 펼친 .control 을 붙인다.
    반환 (넷리스트 텍스트, 소자별 변수 목록)."""
    models = inp["process"]["models"]
    kind_of = {d["name"]: d["kind"] for d in inp["devices"]}
    body, wrappers, params, devvars = [], [], [], {}
    for raw in text.splitlines():
        if raw.strip().lower().startswith(".control"):
            break
        tok = raw.split()
        if tok and tok[0].startswith("X") and tok[0][1:] in kind_of and len(tok) >= 6:
            name = tok[0][1:]
            sub = models[kind_of[name]]["subckt"]
            vs = mismatch_vars(text, sub)
            devvars[name] = vs
            kv = " ".join(tok[6:])
            wrappers += [f".subckt mmv_{name} d g s b params: " + " ".join(f"v{j}=0" for j in range(len(vs))),
                         *[f".param {v}={{v{j}}}" for j, v in enumerate(vs)],
                         f"X1 d g s b {tok[5]} {kv}", ".ends"]
            params += [f".param pv_{name}_{j}=0" for j in range(len(vs))]
            body.append(f"{tok[0]} {tok[1]} {tok[2]} {tok[3]} {tok[4]} mmv_{name} "
                        + " ".join(f"v{j}={{pv_{name}_{j}}}" for j in range(len(vs))))
            continue
        body.append(raw)
    outs = meta["output_nodes"]
    sn = meta["spice_node"]
    ports = inp["ports"]
    ip = sn[ports["input_p"]]
    im = sn[ports["input_n"]]
    probe = {ip, im, outs[0]} | ({outs[1]} if outs[1] != "0" else set())
    c = [".control", "set noaskquit"]
    for k, z in enumerate(samples):
        for name, vs in devvars.items():
            for j in range(len(vs)):
                c.append(f"alterparam pv_{name}_{j} = {z[name][j]:.12e}")
        c += ["reset", "op", f"echo MCS {k}"] + [f"print v({n.lower()})" for n in sorted(probe)]
    c += ["quit", ".endc", ".end"]
    return "\n".join(body[:1] + wrappers + params + body[1:] + c) + "\n", devvars


def offset_mc_measure(inp, cir_path, meta, exe, timeout_s=None, cache_dir=None):
    """sim.offset_mc (입력 `offset_mc` 블록이 있을 때, 모듈 머리말). status ok|unavailable|failed."""
    cfg = inp.get("offset_mc")
    if not cfg:
        return None
    out = {"status": "unavailable", "reason": None, "sigma_in_mV": None, "mean_in_mV": None, "n_samples": 0,
           "method": "ngspice Monte-Carlo (소자별 독립 mismatch 변수, alterparam+reset+op)"}
    ports = inp["ports"]
    if not (ports.get("input_p") and ports.get("input_n")):
        out["reason"] = "차동 입력 쌍(ports.input_p/input_n)이 없다 -- DC servo 로 입력 환산 offset 을 잴 수 없다"
        return out
    if meta.get("blockers"):
        out["reason"] = "넷리스트 막힘: " + " | ".join(meta["blockers"])
        return out
    d = os.path.dirname(os.path.abspath(cir_path))
    stem = os.path.splitext(os.path.basename(cir_path))[0]
    with open(cir_path, encoding="utf-8") as fh:
        text = fh.read()
    if "Lfb_" not in text:
        out["reason"] = "free 넷리스트에 DC 되먹임(servo)이 없다 -- 입력 환산 offset 을 DC 로 잴 수 없다"
        return out
    h0 = None
    raw = parse_ac_file(os.path.join(d, meta["ac_file"])) if meta.get("ac_file") else None
    if raw:
        h0 = complex(raw[1][0], raw[2][0])
    if h0 is None or abs(h0) == 0:
        out["reason"] = "DC 차동 이득(.ac 첫 점)을 읽지 못했다"
        return out
    a_signed = h0.real if abs(h0.imag) <= 1e-3 * abs(h0) else None
    if a_signed is None:
        out["reason"] = f"기준점 이득 H0 = {h0} 의 허수부가 커서 DC 이득 부호를 정할 수 없다"
        return out
    n, capped, se = sample_count(float(cfg["rel_resolution"]), cfg.get("max_samples"))
    import numpy as np
    rng = np.random.default_rng(int(cfg.get("seed") or 0))
    devs = {x["name"]: x for x in inp["devices"]}
    # 표본 0 = 흔들림 없는 기준 해(변수 0), 1..n = 소자·변수마다 z·1e-6/sqrt(m)
    zero, samples = None, []
    # 변수 개수는 build 에서 정해지므로 먼저 한 번 훑는다
    models = inp["process"]["models"]
    nv = {nm: len(mismatch_vars(text, models[devs[nm]["kind"]]["subckt"])) for nm in devs}
    zero = {nm: [0.0] * nv[nm] for nm in devs}
    samples.append(zero)
    for _ in range(n):
        samples.append({nm: [float(rng.standard_normal()) * 1e-6 / math.sqrt(devs[nm]["n_fingers"]) for _ in range(nv[nm])]
                        for nm in devs})
    mtext, devvars = build_mc_netlist(text, inp, meta, samples, a_signed)
    mcir = os.path.join(d, f"{stem}.mc.cir")
    with open(mcir, "w", encoding="utf-8") as fh:
        fh.write(mtext)
    import subprocess
    try:
        rc, log, _ = run_ngspice(exe, mcir, os.path.splitext(mcir)[0] + ".log", timeout_s, cache_dir, [])
    except subprocess.TimeoutExpired:
        out.update(status="failed", reason=f"MC 가 시간 상한 {timeout_s} s 에 끊겼다")
        return out
    out["ngspice_rc"] = rc
    sn, outs = meta["spice_node"], meta["output_nodes"]
    ip, im = sn[ports["input_p"]].lower(), sn[ports["input_n"]].lower()
    o1 = outs[0].lower()
    o2 = None if outs[1] == "0" else outs[1].lower()
    rows, fails = [], 0
    for blk in re.split(r"^MCS\s+", log, flags=re.M)[1:]:
        vals = {m.group(2).lower(): float(m.group(3)) for m in _NODE_RE.finditer(blk)}
        if ip in vals and im in vals and o1 in vals and (o2 is None or o2 in vals):
            rows.append((vals[ip] - vals[im], vals[o1] - (vals[o2] if o2 else 0.0)))
        else:
            rows.append(None)
            fails += 1
    if len(rows) != n + 1 or rows[0] is None:
        out.update(status="failed", reason=f"기준 해 또는 표본 {n + 1 - len(rows)}개를 읽지 못했다(ngspice 로그 {len(rows)}/{n + 1} 블록, 기준 해 "
                                           f"{'없음' if not rows or rows[0] is None else '있음'}): "
                   + " | ".join(ln.strip() for ln in log.splitlines() if re.search(r"error|fatal|singular", ln, re.I))[:300])
        return out
    vid0, vout0 = rows[0]
    vos = [(vo - vout0) / a_signed - (vi - vid0) for r in rows[1:] if r is not None for vi, vo in [r]]
    arr = np.asarray(vos, float)
    ok = len(arr)
    out.update(status="ok" if ok > 1 else "failed", n_samples=ok, n_requested=n, n_failed=fails, n_capped=capped,
               rel_se_achieved=1 / math.sqrt(2 * (ok - 1)) if ok > 1 else None, rel_resolution=float(cfg["rel_resolution"]),
               seed=int(cfg.get("seed") or 0), a_dc_signed=a_signed,
               sigma_in_mV=float(arr.std(ddof=1) * 1e3) if ok > 1 else None, mean_in_mV=float(arr.mean() * 1e3) if ok else None,
               mismatch_vars={k: v for k, v in devvars.items()}, unit_note="변수값 = z·1e-6/sqrt(m) (모듈 머리말)")
    if ok <= 1:
        out["reason"] = "유효 표본이 2 개 미만이다"
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="ngspice Monte-Carlo 입력 환산 offset")
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
    res = offset_mc_measure(inp, a.netlist, meta, a.ngspice, a.timeout_s, a.cache_dir)
    with open(a.out_json, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("wrote", a.out_json, "status=", (res or {}).get("status"), "sigma_in_mV=", (res or {}).get("sigma_in_mV"))
    return 0 if (res or {}).get("status") == "ok" else 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
