#!/usr/bin/env python
"""sky130_pair_mc.py -- ngspice 소자 쌍 Monte Carlo: mismatch 블록 변수를 소자마다 독립 gauss 로 흔들어 같은 전류에서의 ΔVGS 산포를 잰다
(설계 41 §6.4-2 '단위 확인', 계획 DEC-96 (2); 오라클 쪽 도구 -- 엔진(gmid_engine)에 의존하지 않는다).

무엇을 확인하나 (결과 JSON 의 `checks`):
1. **단위**(`unit`): 모델 카드는 `p = p0 + p_slope_spectre·(p_slope/sqrt(l·w·mult))` 로 변수를 흔든다. vth0 만 흔든 쌍의 σ(ΔVGS)·√(W·L) 이
   √2·`vth0_slope` 와 같으면 'l·w 는 µm 수치, slope 는 V·µm' 이다. 같은 σ 가 (a) `.option scale=1.0u` + 숫자만 쓴 l·w(µm) + std 1.0 과
   (b) 단위 글자로 m 를 직접 쓴 l·w + std = scale(1e-6, 생성기 mismatch 모드 섭동 크기) 에서 같은지도 재서 두 표기가 같은 1σ 임을 보인다.
2. **감도 합성**(`rss`): 변수를 모두 흔든 쌍 σ 가 변수별 +1σ 단독 섭동 ΔVGS 의 RSS × √2 (독립 → 분산 합, 쌍 → ×√2)와 같다 -- LUT 감도 열 DVGS_k 가
   섭동 곡선에서 오는 것과 같은 방법의 선형 합성이 MC 와 일치하는지.
3. **기하·bin 환산**(`geometry`): A_eff = σ_쌍·√(W·L) 이 (W, L) 이 달라도 같은 bin 안에서 같고, pfet L < 0.5 µm bin(vth0_slope1)에서 slope 비만큼 바뀐다.
4. **A_β**(`A_beta_mc_pct_um`): toxe 만 흔든 쌍의 σ(ΔVGS at 같은 ID)가 σ = a + b/(gm/ID) 꼴(toxe → Vth 항 a + β 항 b/(gm/ID),
   b = σ(Δβ/β))이라 gm/ID 여러 점에서 재어 선형 회귀한 b·√(W·L) 이 √2·`toxe_slope`(%·µm)와 같은지.

방법: 소자 A·B 는 모델 카드 복사본(서브서킷·`.model` 이름과 `*_slope_spectre` 이름에 접미사 A/B)이라 변수·모델 값이 독립이다. 둘 다 다이오드 접속(게이트=드레인)에
같은 강제 전류 I 를 흘려 V(ga) − V(gb) = ΔVGS(같은 ID). 표본마다 `alterparam` + `reset` + `op`. 난수는 numpy 고정 시드.
I 는 공칭 소자의 gm/ID 가 목표(`--gm-id`)에 가장 가까운 VGS 에서의 ID.

실행: python sky130_pair_mc.py --work <임시 폴더> --out <json> [--n 1000] [--jobs 6] [--seed 20261008]
"""
import argparse
import concurrent.futures as cf
import datetime
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time

import numpy as np

NGSPICE_EXE = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
PDK_ROOT = r"C:\pdk\sky130_fd_pr"
DEVICES = {"nfet_01v8": 1, "pfet_01v8": -1}            # 극성(+1: nfet, −1: pfet)
# 사례: (소자, W[µm], L[µm]) -- W 5 µm 은 LUT 기준 폭. L 0.5 는 pfet 에서 [0.25, 0.5] bin(vth0_slope1), 1.0 은 (0.5, 1] bin(vth0_slope).
BETA_GM_ID = (5.0, 7.0, 10.0, 12.0)                    # A_β 회귀 gm/ID 점(강반전~중반전, 제안서 §0.3 과 같은 범위 5-12)
CASES = (("nfet_01v8", 5.0, 0.5), ("nfet_01v8", 5.0, 1.0), ("nfet_01v8", 5.0, 0.18), ("nfet_01v8", 2.0, 1.0),
         ("pfet_01v8", 5.0, 0.5), ("pfet_01v8", 5.0, 1.0), ("pfet_01v8", 5.0, 0.18), ("pfet_01v8", 2.0, 1.0))
_VAL = re.compile(r"^\s*(v\(\w+\))\s*=\s*([-+0-9.eE]+)\s*$", re.I)


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _card(dev, name):
    return os.path.join(PDK_ROOT, "cells", dev, f"sky130_fd_pr__{dev}__{name}")


def mismatch_vars(dev):
    """모델 카드 머리 `.param <소자>__<변수>_slope_spectre = 0.0` 의 변수 이름(정렬)."""
    txt = open(_card(dev, "tt.pm3.spice"), encoding="utf-8", errors="replace").read()
    pre = f"sky130_fd_pr__{dev}__"
    return sorted(set(re.findall(rf"^\.param\s+{re.escape(pre)}(\w+?)_slope_spectre\s*=\s*0\.0\s*$", txt, re.M)))


def slopes(dev):
    """mismatch 계수 파일 `.param 이름=값` -> {이름: 값}."""
    txt = open(_card(dev, "mismatch.corner.spice"), encoding="utf-8", errors="replace").read()
    return {k: float(v) for k, v in re.findall(r"^\.param\s+(\S+)\s*=\s*([-+0-9.eE]+)\s*$", txt, re.M)}


def block_slope(dev, var, w_um, l_um):
    """ngspice 가 (w, l) 에서 고르는 bin 은 showmod 로 읽는 것이 정본이지만, 이 도구는 모델 카드를 직접 읽어 같은 규칙(양끝 닫힘, 아래 bin 우선)을
    적용한다 -- 독립 구현(엔진 코드 아님). 반환: (slope 이름, 값, 블록 이름)."""
    txt = open(_card(dev, "tt.pm3.spice"), encoding="utf-8", errors="replace").read()
    pre = f"sky130_fd_pr__{dev}__"
    hits = []
    for m in re.finditer(r"^\.model\s+(\S+)\s+[np]mos\b(.*?)(?=^\.model|\Z)", txt, re.S | re.I | re.M):
        b = {k: float(re.search(rf"\b{k}\s*=\s*([-+0-9.eE]+)", m.group(2), re.I).group(1)) for k in ("lmin", "lmax", "wmin", "wmax")}
        w, l = w_um * 1e-6, l_um * 1e-6
        if b["wmin"] - math.ulp(b["wmin"]) <= w <= b["wmax"] + math.ulp(b["wmax"]) and \
                b["lmin"] - math.ulp(b["lmin"]) <= l <= b["lmax"] + math.ulp(b["lmax"]):
            hits.append((b["wmin"], b["lmin"], m.group(1), m.group(2)))
    if not hits:
        raise RuntimeError(f"{dev}: W={w_um} L={l_um} 를 품는 .model 없음")
    _, _, name, body = sorted(hits)[0]                       # 경계 공유 시 아래(작은 lmin·wmin) bin
    ref = re.findall(rf"{re.escape(pre)}{var}_slope(\d*)(?![\w])", body)
    if not ref:
        return None, 0.0, name
    ident = f"{pre}{var}_slope{sorted(set(ref))[0]}"
    return ident, slopes(dev)[ident], name


def _renamed(dev, tag):
    """모델 카드 복사본 텍스트: 서브서킷·`.model` 이름과 `*_slope_spectre` 변수 이름에 접미사 `tag` -- 소자별 독립 모델·변수."""
    pre = f"sky130_fd_pr__{dev}"
    txt = open(_card(dev, "tt.pm3.spice"), encoding="utf-8", errors="replace").read()
    txt = re.sub(rf"({re.escape(pre)})(?=\s|$)", rf"\g<1>{tag}", txt, flags=re.M)             # .subckt 이름 · 소자 줄의 모델 이름 앞부분
    txt = re.sub(rf"({re.escape(pre)})(__model)", rf"\g<1>{tag}\g<2>", txt)                    # .model 이름(소자 줄의 bin 모델 이름 포함)
    txt = re.sub(rf"({re.escape(pre)}__\w+?_slope_spectre)", rf"\g<1>_{tag}", txt)             # mismatch 변수
    return txt


def _netlist(dev, w_txt, l_txt, current, pol, vars_, samples, native_scale):
    """쌍 넷리스트: 표본마다 alterparam(소자 A·B 의 변수 값) -> reset -> op -> print."""
    pre = f"sky130_fd_pr__{dev}"
    lines = [f"* pair MC {dev}", ".option scale=1.0u" if native_scale else "* (no scale option)"]
    if dev.startswith("pfet"):
        lines.append(f'.include "{os.path.join(PDK_ROOT, "models", "parameters", "lod.spice")}"')
    lines += ['.include "cardA.spice"', '.include "cardB.spice"', f'.include "{_card(dev, "mismatch.corner.spice")}"',
              f"ia {'0 ga' if pol > 0 else 'ga 0'} dc {current:.12g}", f"ib {'0 gb' if pol > 0 else 'gb 0'} dc {current:.12g}",
              f"xa ga ga 0 0 {pre}A l={l_txt} w={w_txt}", f"xb gb gb 0 0 {pre}B l={l_txt} w={w_txt}", "", ".control"]
    for z in samples:
        for tag, row in (("A", z[0]), ("B", z[1])):
            for var, value in zip(vars_, row):
                lines.append(f"alterparam {pre}__{var}_slope_spectre_{tag} = {value:.12g}")
        lines += ["reset", "op", "print v(ga) v(gb)"]
    lines += ["quit", ".endc", ".end"]
    return "\n".join(lines) + "\n"


def _run(work, stem, dev, w_txt, l_txt, current, pol, vars_, samples, native_scale):
    for tag in ("A", "B"):
        with open(os.path.join(work, f"card{tag}.spice"), "w", encoding="utf-8", newline="\n") as f:
            f.write(_renamed(dev, tag))
    net = os.path.join(work, stem + ".cir")
    out = os.path.join(work, stem + ".out")
    with open(net, "w") as f:
        f.write(_netlist(dev, w_txt, l_txt, current, pol, vars_, samples, native_scale))
    with open(out, "w") as fo, open(os.path.join(work, stem + ".err"), "w") as fe:
        subprocess.run([NGSPICE_EXE, "-b", net], cwd=work, stdout=fo, stderr=fe, timeout=3600, check=False)
    text = open(out, encoding="utf-8", errors="replace").read()
    if re.search(r"\b(error|fatal)\b", text + open(os.path.join(work, stem + ".err"), encoding="utf-8", errors="replace").read(), re.I):
        raise RuntimeError(f"{stem}: ngspice 오류")
    vals = [float(m.group(2)) for ln in text.splitlines() if (m := _VAL.match(ln))]
    if len(vals) != 2 * len(samples):
        raise RuntimeError(f"{stem}: 값 {len(vals)}개 (기대 {2 * len(samples)})")
    arr = np.array(vals).reshape(-1, 2)
    return arr[:, 0] - arr[:, 1]                            # V(ga) − V(gb) = ΔVGS


def bias_current(work, dev, w_um, l_um, pol, gm_id_target):
    """공칭 소자의 gm/ID 가 목표에 가장 가까운 VGS 의 ID(A) -- VGS 격자 op 로 찾는다."""
    pre = f"sky130_fd_pr__{dev}"
    inst = f"@m.xdut.msky130_fd_pr__{dev}"
    v = np.round(np.linspace(0.05, 1.8, 176), 6)
    lines = [f"* bias {dev}"]
    if dev.startswith("pfet"):
        lines.append(f'.include "{os.path.join(PDK_ROOT, "models", "parameters", "lod.spice")}"')
    lines += [f'.include "{_card(dev, "tt.pm3.spice")}"', f'.include "{_card(dev, "mismatch.corner.spice")}"',
              "vgs g 0 dc 0", "vds d 0 dc 0", f"xdut d g 0 0 {pre} l={l_um}u w={w_um}u", ".control"]
    for x in v:
        lines += [f"alter vgs = {pol * x}", f"alter vds = {pol * 0.9}", "op", "echo P", f"print {inst}[id]", f"print {inst}[gm]", "destroy all"]
    lines += ["quit", ".endc", ".end"]
    net, out = os.path.join(work, f"bias_{dev}_{w_um}_{l_um}.cir"), os.path.join(work, f"bias_{dev}_{w_um}_{l_um}.out")
    open(net, "w").write("\n".join(lines) + "\n")
    with open(out, "w") as fo:
        subprocess.run([NGSPICE_EXE, "-b", net], cwd=work, stdout=fo, stderr=subprocess.DEVNULL, timeout=600, check=False)
    vals = [float(m.group(1)) for ln in open(out, encoding="utf-8", errors="replace").read().splitlines()
            if (m := re.match(rf"^\s*{re.escape(inst)}\[(?:id|gm)\]\s*=\s*([-+0-9.eE]+)\s*$", ln, re.I))]
    a = np.abs(np.array(vals).reshape(-1, 2))
    gmid = np.where(a[:, 0] > 0, a[:, 1] / np.where(a[:, 0] > 0, a[:, 0], 1.0), 0.0)
    peak = int(np.argmax(gmid))
    j = peak + int(np.argmin(np.abs(gmid[peak:] - gm_id_target)))      # 강반전 쪽(정점 오른쪽)에서 목표에 가장 가까운 점
    return float(a[j, 0]), float(gmid[j]), float(v[j])


def fit_beta(gm_ids, sigmas):
    """σ_i = a + b/g_i 최소제곱 -> (a, b). 점 2개 이상."""
    x = 1.0 / np.asarray(gm_ids, dtype=float)
    b, a = np.polyfit(x, np.asarray(sigmas, dtype=float), 1)
    return float(a), float(b)


def _chunks(n, parts):
    k = max(1, math.ceil(n / parts))
    return [(i, min(n, i + k)) for i in range(0, n, k)]


def pair_sigma(work, jobs, tag, dev, w_txt, l_txt, current, pol, vars_, z, native_scale, scale):
    """표본 행렬 z[N, 2, len(vars_)] (단위 gauss) × scale 로 쌍 ΔVGS 표본 배열."""
    parts = _chunks(len(z), jobs)
    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        futs = []
        for p, (a, b) in enumerate(parts):
            wd = os.path.join(work, f"{tag}_{p}")
            os.makedirs(wd, exist_ok=True)
            futs.append(ex.submit(_run, wd, f"{tag}_{p}", dev, w_txt, l_txt, current, pol, vars_, z[a:b] * scale, native_scale))
        return np.concatenate([f.result() for f in futs])


def one_sided(work, tag, dev, w_txt, l_txt, current, pol, vars_, scale):
    """변수 k 를 A 소자만 +1σ(scale) 로 한 ΔVGS (단독 섭동 감도, B 는 공칭) -- 변수별."""
    out = {}
    os.makedirs(os.path.join(work, tag), exist_ok=True)
    for k, var in enumerate(vars_):
        z = np.zeros((1, 2, len(vars_)))
        z[0, 0, k] = 1.0
        out[var] = float(_run(os.path.join(work, tag), f"{tag}_{var}", dev, w_txt, l_txt, current, pol, vars_, z * scale, False)[0])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="ngspice 소자 쌍 Monte Carlo (mismatch 단위·합성·기하 확인)")
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--seed", type=int, default=20261008)
    ap.add_argument("--gm-id", type=float, default=10.0, help="공칭 소자 gm/ID 목표(1/V) -- 강반전 쪽에서 가장 가까운 VGS")
    ap.add_argument("--limit-cases", type=int, default=len(CASES), help="앞에서 몇 사례만(시험용)")
    ap.add_argument("--n-beta", type=int, default=400, help="A_β 회귀의 gm/ID 점마다 표본 수")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    os.makedirs(a.work, exist_ok=True)
    t0 = time.time()
    scale_txt = open(os.path.join(PDK_ROOT, "models", "all.spice"), encoding="utf-8", errors="replace").read()
    scale = float(re.search(r"^\.option\s+scale\s*=\s*([-+0-9.eE]+)u\s*$", scale_txt, re.M | re.I).group(1)) * 1e-6
    rng = np.random.default_rng(a.seed)
    cases = []
    for dev, w_um, l_um in CASES[:a.limit_cases]:
        pol = DEVICES[dev]
        vars_ = mismatch_vars(dev)
        tag = f"{dev}_W{w_um}_L{l_um}"
        cur, gmid, vgs = bias_current(a.work, dev, w_um, l_um, pol, a.gm_id)
        # 소자 전류는 W 비례가 아니라 같은 gm/ID 의 전류밀도로: 위 bias 는 이 (W, L) 인스턴스에서 직접 잰 값이다.
        z = rng.standard_normal((a.n, 2, len(vars_)))
        meter = (f"{w_um}u", f"{l_um}u")
        d_all = pair_sigma(a.work, a.jobs, tag + "_all", dev, *meter, cur, pol, vars_, z, False, scale)
        vth = vars_.index("vth0")
        z_vth = np.zeros_like(z)
        z_vth[:, :, vth] = z[:, :, vth]
        d_vth = pair_sigma(a.work, a.jobs, tag + "_vth", dev, *meter, cur, pol, vars_, z_vth, False, scale)
        native = pair_sigma(a.work, a.jobs, tag + "_nat", dev, str(w_um), str(l_um), cur, pol, vars_, z_vth, True, 1.0)
        single = one_sided(a.work, tag + "_one", dev, *meter, cur, pol, vars_, scale)
        toxe = vars_.index("toxe")
        beta_g, beta_s = [], []
        z_t = np.zeros((a.n_beta, 2, len(vars_)))
        z_t[:, :, toxe] = rng.standard_normal((a.n_beta, 2))       # 모든 gm/ID 점에서 같은 표본(회귀 잡음을 줄인다)
        for g_target in BETA_GM_ID:
            cur_g, gmid_g, _ = bias_current(a.work, dev, w_um, l_um, pol, g_target)
            d_t = pair_sigma(a.work, a.jobs, f"{tag}_beta{g_target}", dev, *meter, cur_g, pol, vars_, z_t, False, scale)
            beta_g.append(gmid_g)
            beta_s.append(float(np.std(d_t, ddof=1)))
        _, b_fit = fit_beta(beta_g, beta_s)
        t_ident, t_slope, _ = block_slope(dev, "toxe", w_um, l_um)
        ident, slope, blk = block_slope(dev, "vth0", w_um, l_um)
        area = w_um * l_um
        sig_all, sig_vth, sig_nat = (float(np.std(x, ddof=1)) for x in (d_all, d_vth, native))
        rss = math.sqrt(2.0) * math.sqrt(sum(v * v for v in single.values()))
        n = a.n
        cases.append({
            "device": dev, "W_um": w_um, "L_um": l_um, "model": blk, "I_a": cur, "gm_id_at_bias": gmid, "vgs_at_bias": vgs, "n": n,
            "variables": vars_,
            "sigma_pair_all_mv": 1e3 * sig_all, "sigma_pair_vth0_only_mv": 1e3 * sig_vth,
            "sigma_pair_vth0_only_native_scale_mv": 1e3 * sig_nat,
            "A_eff_mc_mv_um": 1e3 * sig_all * math.sqrt(area),
            "A_VT_mc_mv_um": 1e3 * sig_vth * math.sqrt(area),
            "A_VT_expected_mv_um": 1e3 * math.sqrt(2.0) * slope, "vth0_slope_name": ident, "vth0_slope": slope,
            "A_VT_native_mv_um": 1e3 * sig_nat * math.sqrt(area),
            "one_sided_dvgs_mv": {k: 1e3 * v for k, v in single.items()},
            "sigma_pair_rss_pred_mv": 1e3 * rss,
            "rel_err_stat_1sigma": 1.0 / math.sqrt(2.0 * (n - 1)),
            "ratio_vth0_mc_to_expected": (sig_vth * math.sqrt(area)) / (math.sqrt(2.0) * slope),
            "ratio_native_to_meter": sig_nat / sig_vth,
            "ratio_all_mc_to_rss": sig_all / rss,
            "beta_fit_gm_id": beta_g, "beta_fit_sigma_pair_mv": [1e3 * s for s in beta_s], "toxe_slope_name": t_ident,
            "toxe_slope": t_slope, "A_beta_mc_pct_um": 100.0 * b_fit * math.sqrt(area),
            "A_beta_expected_pct_um": 100.0 * math.sqrt(2.0) * t_slope,
            "ratio_A_beta_mc_to_expected": (b_fit * math.sqrt(area)) / (math.sqrt(2.0) * t_slope),
        })
        print(f"{tag}: A_VT mc {cases[-1]['A_VT_mc_mv_um']:.3f} exp {cases[-1]['A_VT_expected_mv_um']:.3f} native "
              f"{cases[-1]['A_VT_native_mv_um']:.3f}  A_eff {cases[-1]['A_eff_mc_mv_um']:.3f}  all/rss {cases[-1]['ratio_all_mc_to_rss']:.3f}",
              flush=True)
    rec = {
        "tool": os.path.basename(__file__), "tool_sha256": _sha(os.path.abspath(__file__)), "ngspice": NGSPICE_EXE,
        "pdk_root": PDK_ROOT, "seed": a.seed, "n": a.n, "gm_id_target": a.gm_id, "scale_from_all_spice_m": scale,
        "files_sha256": {os.path.relpath(p, PDK_ROOT).replace(os.sep, "/"): _sha(p) for p in
                         [os.path.join(PDK_ROOT, "models", "all.spice")] + [_card(d, n) for d in DEVICES for n in ("tt.pm3.spice", "mismatch.corner.spice")]},
        "cases": cases, "date": datetime.date.today().isoformat(), "seconds": round(time.time() - t0, 1),
    }
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(f"saved {a.out} ({rec['seconds']} s)")


if __name__ == "__main__":
    main()
