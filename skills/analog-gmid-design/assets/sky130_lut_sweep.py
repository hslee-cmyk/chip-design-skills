#!/usr/bin/env python
"""sky130_lut_sweep.py -- 기준 폭(W_ref) 4D gm/ID LUT 생성기 (ngspice + SkyWater sky130 nfet_01v8 / pfet_01v8).

이 스크립트는 lut-generation-checklist.md §7.4(foundry 특성화 절차)의 구현체이고, §7.3의 "Cgd/Cdd는 op-info로
뽑지 말고 AC/Y-parameter로 뽑아라"를 따른다. 새 엔진(gmid_engine/lut, `load_lut_set`)은 이 산출물을 '기준 LUT'
(용량·잡음 열, W_ref)으로 읽고, DC 정본은 폭 슬라이스(별도 생성기)다.

2026-10-07 개정(U-27 재생성, 사용자 승인 Q1 (a')~(g), 근거 wt/_drafts/engine/lut_regen_plan.md):
* L 축은 **입력**에서 받는다(`sweep --l-json [--l-json-key K]` 또는 `--l-um`). 이 파일에 L 목록을 적지 않는다. 각 L은 제조 격자
  (tlef MANUFACTURINGGRID) 위, 모델 bin L 범위 안이어야 한다. 각 L이 쓰는 bin은 Python 규칙으로 추정하지 않고
  ngspice `showmod`로 읽어 메타에 적는다(ngspice-46은 경계값 L = lmax에서 **아래 bin**을 쓴다, 계획 1.2a).
* `candidates` 부명령: 사용자 결정(L 선형 보간은 한 PDK 모델 bin 안에서만) 아래 L 후보
  = 기존 앵커(기존 LUT npz의 L 축) ∪ 모델 bin `lmin` 집합 ∪ (불연속 경계 b마다 b가 들지 않은 bin의 끝점 = 실제 전환
  칸의 다른 점, ngspice-46에서 b + 격자 한 칸)을 [lmin 최솟값, --l-max-um] 안에서 낸다. bin 경계는 모델 파일
  `lmin`/`lmax`를 파싱해 얻고(`bins.csv` L 집합과 교차 확인), 각 경계의 전환 칸 점프(VGS 환산)를 ngspice로 재서 함께
  낸다. '불연속' 판정은 입력이다(`--discontinuous-um` 결정 또는 `--tol-v` 해상도) -- 이 파일은 임계값을 갖지 않는다.
* VS 축 0 ~ VGS 축 상한(소자 정격, `--vs-max`로 바꿀 수 있음), 간격은 옛 VS 축 간격 그대로.
* 열 추가: GMBS·VTH·VDSAT(op), CGS·CGB(소스·바디 AC 여기), CDD·CSS(드레인·소스 자기 용량, 접합 포함 = PDK 모델
  카드), 잡음 SVG2_1HZ·SVG2_HF(게이트 환산 V²/Hz -- 옛 `SID_1F`는 inoise_spectrum(V/√Hz) 그대로였고 이름도
  드레인 전류잡음처럼 보여서 바꿨다. SVG2_1HZ = SID_1F²).
* 용량 열은 **부호 보존**(옛 `mag()`/`abs` 아님). 규약: CGG = −Im(i(vgs))/ω (게이트 여기), C_gx = +Im(i(vgs))/ω
  (x 여기, x = d·s·b), CDD = −Im(i(vds))/ω (드레인 여기), CSS = −Im(i(vsrc))/ω (소스 여기). 게이트 행합
  CGG = CGD + CGS + CGB 잔차와 게이트 실수부 최댓값을 메타 `checks`에 남긴다.
* 생성기 결함 수정(D7): 점마다 `destroy all`(plot 누적 -- 2401점 조합 291 s → 3.5 s, 값 동일 실측),
  stdout/stderr 분리(경고가 값 줄에 끼어 파싱이 죽던 결함), ngspice error/fatal 줄 검사, 체크포인트 이름을
  VS **값** 기반으로, 조합 단위 병렬(ThreadPool), 메타(w_ref_m·sha256·단위·bin).

## 사전 준비 -- CLAUDE.md·sky130-worked-example.md §1
ngspice-46(Windows 네이티브), sky130 PDK 모델(`models` + `cells/nfet_01v8` + `cells/pfet_01v8`). 아래 NGSPICE_EXE /
PDK_ROOT / TLEF_PATH를 자기 경로로.

## 왜 AC/Y-parameter인가 (sky130-worked-example.md §7)
ngspice BSIM4 `@device[cgd]`/`@device[cdd]` op-info는 믿을 수 없다(Cgd 36배, Cdd 부호까지 틀림 실측). 그래서 용량은
전부 단일 주파수 F_TEST(fT 대비 충분히 낮은 순수 용량 구간)의 AC 전류 허수부로 뽑는다. ID/GM/GDS/GMBS/VTH/VDSAT는
BSIM이 직접 내는 op 값이다(VDSAT은 SPICE 오라클 tools/spice_oracle의 `@m[vdsat]`과 같은 정의).

## 잡음 측정 구조
드레인을 이상적 전압원이 바로 잡으면 `.noise v(d)`가 0이다. 그래서 `vds`가 중간 노드 `dd`를 구동하고 인덕터
`lchoke`(DC 저항 0)로 `d`와 잇는다. AC 측정 중엔 LCHOKE_AC(사실상 wire), 잡음 측정 중엔 LCHOKE_NOISE(사실상 open).

## 실행
    python sky130_lut_sweep.py candidates --l-max-um 20 --work <임시> --out cand.json
    python sky130_lut_sweep.py sweep --l-json <L 목록 json> --work <임시> --out <npz> [--jobs 8] [--devices ...]
(소자, L, VS) 조합마다 ngspice 프로세스 1개, 그 안에서 VGS×VDS 격자를 `.control` 루프로 돈다. 조합마다 체크포인트
(생성기 sha256이 같을 때만 재사용)와 진행 로그(append)를 `--work`에 남긴다.
"""
import argparse
import concurrent.futures as cf
import csv
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

# ---------------------------------------------------------------------------
# 자신의 환경에 맞게 수정
# ---------------------------------------------------------------------------
NGSPICE_EXE = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
PDK_ROOT = r"C:\pdk\sky130_fd_pr"          # sparse-checkout으로 받은 위치
TLEF_PATH = r"C:\pdk\sky130_fd_sc_hd\tech\sky130_fd_sc_hd.tlef"   # MANUFACTURINGGRID 출처
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
LOD_SPICE = os.path.join(PDK_ROOT, "models", "parameters", "lod.spice")
EXISTING_LUT = os.path.join(OUTPUT_DIR, "sky130_nfet_pfet_lut_sample.npz")   # candidates의 '기존 앵커' 출처
L_GRID_JSON = os.path.join(OUTPUT_DIR, "sky130_lut_L_grid.json")   # 기본 L 입력(사용자 승인 목록, 출처는 파일 안)

# ---------------------------------------------------------------------------
# 격자 (L은 입력에서 받는다 -- 위 docstring)
# ---------------------------------------------------------------------------
N_VGS, N_VDS = 49, 49
VGS_START, VGS_STOP = 0.0, 1.8   # sky130 nfet_01v8/pfet_01v8은 1.8V 소자
VDS_START, VDS_STOP = 0.0, 1.8
VS_STEP = 0.2                     # 옛 VS 축 [0, 0.2, 0.4, 0.6, 0.8]의 간격 그대로(U-27: 상한만 늘림)
F_TEST = 100e6                    # AC 추출 주파수 (fT 대비 충분히 낮은 순수 용량성 구간), SVG2_HF 주파수
NOISE_F_PROBE = 1.0               # SVG2_1HZ 주파수
LCHOKE_AC = 1e-15                 # AC 측정 중엔 사실상 wire
LCHOKE_NOISE = 1e9                # noise 측정 중엔 사실상 open
VGS_ARR = np.linspace(VGS_START, VGS_STOP, N_VGS)
VDS_ARR = np.linspace(VDS_START, VDS_STOP, N_VDS)

# DUT 한 줄(기준 폭 W_ref와 확산 기하의 유일한 출처 -- W_REF_M은 이 줄에서 읽는다). 오라클 어댑터
# (tools/spice_oracle/legacy_adapter.py)가 이 줄·`.include` 줄·_gen_netlist의 id 출력 줄·`run_device(...)` 호출을
# 소스 정규식으로 읽는다(첫 일치를 쓴다 -- 주석에 그 형태를 그대로 적으면 주석이 먼저 잡힌다). 형태를 바꾸면 그쪽도 본다.
DUT_LINE = "xdut d g s b sky130_fd_pr__{devcell} l={L_um}u w=5u ad=2.5p as=2.5p pd=7u ps=7u"
COL_SUFFIX = {"nfet_01v8": "_n", "pfet_01v8": "_p"}   # 저장 열 접미사(옛 npz와 같음, 엔진 LutSpec.cap_column_suffix)
OP_PARAMS = ("id", "gm", "gds", "gmbs", "vth", "vdsat")

_SI_EXP = {"f": "e-15", "p": "e-12", "n": "e-9", "u": "e-6", "m": "e-3", "": ""}
_VAL_RE = re.compile(r"^\s*(\S.*?)\s*=\s*([-+0-9.eE]+)\s*$")
_BAD_RE = re.compile(r"\b(error|fatal)\b", re.I)


def _w_ref_m():
    m = re.search(r"\bw=([0-9.]+)(\w?)\s", DUT_LINE)
    return float(m.group(1) + _SI_EXP[m.group(2)])   # 문자열로 지수를 붙여 5u -> 5e-06 그대로(곱셈 반올림 없음)


W_REF_M = _w_ref_m()


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


# --------------------------------------------------------------------------- PDK 읽기
def manufacturing_grid_um(tlef=TLEF_PATH):
    txt = open(tlef, encoding="utf-8", errors="replace").read()
    m = re.search(r"^\s*MANUFACTURINGGRID\s+([0-9.eE+-]+)\s*;", txt, re.M)
    if m is None:
        raise RuntimeError(f"{tlef}: MANUFACTURINGGRID 없음")
    return float(m.group(1))


def grid_key(l_um, grid_um):
    """L(um)의 제조 격자 정수 키. 격자 위가 아니면 거부(부동소수 반올림 몇 번만 허용)."""
    q = l_um / grid_um
    k = round(q)
    if abs(q - k) > 4 * math.ulp(q):
        raise RuntimeError(f"L={l_um} um 이 제조 격자 {grid_um} um 위에 있지 않다")
    return k


def model_file(devcell, corner="tt"):
    return os.path.join(PDK_ROOT, "cells", devcell, f"sky130_fd_pr__{devcell}__{corner}.pm3.spice")


def parse_bins(pm3_path):
    """모델 파일의 `.model ... nmos|pmos` 블록마다 {model, lmin, lmax, wmin, wmax}[m]."""
    txt = open(pm3_path, encoding="utf-8", errors="replace").read()
    bins = []
    for m in re.finditer(r"^\.model\s+(\S+)\s+[np]mos\b(.*?)(?=^\.model|\Z)", txt, re.S | re.I | re.M):
        rec = {"model": m.group(1)}
        for k in ("lmin", "lmax", "wmin", "wmax"):
            mm = re.search(rf"\b{k}\s*=\s*([-+0-9.eE]+)", m.group(2), re.I)
            if mm is None:
                raise RuntimeError(f"{pm3_path}: {m.group(1)}에 {k} 없음")
            rec[k] = float(mm.group(1))
        bins.append(rec)
    if not bins:
        raise RuntimeError(f"{pm3_path}: .model bin을 하나도 못 읽음")
    return bins


def bin_lmins_um(devcell, bins):
    """bin lmin 집합(um) -- PDK bins.csv L 집합과 같아야 한다(교차 확인, 다르면 거부)."""
    lm = sorted({round(b["lmin"] * 1e6, 6) for b in bins})
    csv_path = os.path.join(PDK_ROOT, "cells", devcell, f"sky130_fd_pr__{devcell}.bins.csv")
    with open(csv_path, newline="") as f:
        lc = sorted({round(float(r["L"]), 6) for r in csv.DictReader(f)})
    if lm != lc:
        raise RuntimeError(f"{devcell}: 모델 bin lmin 집합 {lm} != bins.csv L 집합 {lc}")
    return lm, csv_path


SHOWMOD_KEYS = ("lmin", "lmax", "wmin", "wmax")


def showmod_cmd(inst):
    """ngspice가 인스턴스에 실제로 고른 bin의 경계를 출력하는 명령. bin 소속은 Python 규칙으로 추정하지 않는다:
    ngspice-46은 경계값(L = lmax = 이웃 lmin)에서 **아래 bin**을 고른다(lut_regen_plan.md 1.2a 실측)."""
    return f"showmod m.{inst}.msky130_fd_pr__{{devcell}} : " + " ".join(SHOWMOD_KEYS)


def parse_showmod(text, bins):
    """`echo SHOWMOD <tag>` 뒤의 showmod 출력 블록마다 {tag: {lmin, lmax, wmin, wmax, model}}.
    model 이름은 showmod가 잘라 찍으므로, 경계 4값이 모델 파일 bin과 정확히(상대 1e-12) 같은 것 하나로 정한다."""
    out, tag, cur = {}, None, {}
    for ln in text.splitlines():
        s = ln.split()
        if len(s) >= 2 and s[0] == "SHOWMOD":
            tag, cur = s[1], {}
            continue
        if tag is not None and len(s) == 2 and s[0] in SHOWMOD_KEYS:
            cur[s[0]] = float(s[1])
            if len(cur) == len(SHOWMOD_KEYS):
                hit = [b["model"] for b in bins
                       if all(abs(b[k] - cur[k]) <= 1e-12 * abs(cur[k]) for k in SHOWMOD_KEYS)]
                if len(hit) != 1:
                    raise RuntimeError(f"showmod {cur} 와 같은 모델 bin {len(hit)}개 (1개여야 함)")
                out[tag] = dict(cur, model=hit[0])
                tag = None
    return out


def ngspice_bins(work, devcell, l_list):
    """W_ref 인스턴스를 L마다 하나씩 두고 op 뒤 showmod로 ngspice가 실제로 쓴 bin을 읽는다 -> {L문자열: bin}."""
    stem = f"bins_{devcell}_{len(l_list)}"
    L = [f"* showmod bins {devcell}"] + model_includes(devcell)
    L += ["vgs g 0 dc 0", "vds d 0 dc 0", "vsrc s 0 dc 0", "vb b 0 dc 0"]
    for i, l_um in enumerate(l_list):
        L.append(DUT_LINE.replace("xdut", f"xd{i}").format(devcell=devcell, L_um=l_um))
    L += [".control", "op"]
    for i, l_um in enumerate(l_list):
        L += [f"echo SHOWMOD {l_um:g}", showmod_cmd(f"xd{i}").format(devcell=devcell)]
    L += ["quit", ".endc", ".end"]
    cir, log, err = (os.path.join(work, stem + s) for s in (".cir", ".log", ".err"))
    open(cir, "w").write("\n".join(L) + "\n")
    with open(log, "w") as fo, open(err, "w") as fe:
        subprocess.run([NGSPICE_EXE, "-b", cir], cwd=work, stdout=fo, stderr=fe, timeout=300, check=False)
    _check_log(stem, log, err)
    res = parse_showmod(open(log, encoding="utf-8", errors="replace").read(), parse_bins(model_file(devcell)))
    missing = [f"{x:g}" for x in l_list if f"{x:g}" not in res]
    if missing:
        raise RuntimeError(f"{devcell}: showmod 결과 없음 L={missing}")
    for p in (cir, log, err):
        _cleanup_temp(p)
    return res


def model_includes(devcell):
    """DUT 넷리스트의 include 줄(오라클 어댑터가 이 함수 안의 f-string을 정규식으로 읽는다)."""
    lod_include = LOD_SPICE if devcell.startswith("pfet") else ""
    L = []
    if lod_include:
        L.append(f'.include "{lod_include}"')
    L.append(f'.include "{PDK_ROOT}\\cells\\{devcell}\\sky130_fd_pr__{devcell}__tt.pm3.spice"')
    L.append(f'.include "{PDK_ROOT}\\cells\\{devcell}\\sky130_fd_pr__{devcell}__mismatch.corner.spice"')
    return L


def _included_files(devcell):
    return [re.search(r'"(.*)"', ln).group(1).replace("\\\\", "\\") for ln in model_includes(devcell)]


# --------------------------------------------------------------------------- sweep 넷리스트·파싱
def _fields(devcell):
    """점마다 출력하는 (열 이름, print 식) 순서. 파싱은 이 순서와 식 이름을 그대로 대조한다."""
    inst = f"@m.xdut.msky130_fd_pr__{devcell}"
    f = [(p.upper(), f"{inst}[{p}]") for p in OP_PARAMS]
    f += [("IG_G", "imag(i(vgs))"), ("RG_G", "real(i(vgs))"),
          ("IG_D", "imag(i(vgs))"), ("ID_D", "imag(i(vds))"),
          ("IG_S", "imag(i(vgs))"), ("IS_S", "imag(i(vsrc))"),
          ("IG_B", "imag(i(vgs))"),
          ("N_1HZ", "inoise_spectrum"), ("N_HF", "inoise_spectrum")]
    return f


def _gen_netlist(devcell, L_um, VS, vb_dc, polarity):
    """polarity: +1(NMOS) 또는 -1(PMOS, 음의 VGS/VDS 인가). 소스는 `vsrc`(DC 0)로 분리해 AC 여기한다."""
    vgs_vals = [round(polarity * v, 6) for v in VGS_ARR]
    vds_vals = [round(polarity * v, 6) for v in VDS_ARR]
    fl = _fields(devcell)
    pr = {k: e for k, e in fl}
    ac = f"ac lin 1 {F_TEST:.0f} {F_TEST:.0f}"
    L = [f"* AC-based sweep {devcell} L={L_um}um VS={VS}"]
    L += model_includes(devcell)
    L += ["", "vgs g 0 dc 0 ac 0", "vds dd 0 dc 0 ac 0", f"lchoke dd d {LCHOKE_AC}", "vsrc s 0 dc 0 ac 0",
          f"vb  b 0 dc {vb_dc}", DUT_LINE.format(devcell=devcell, L_um=L_um), "", ".control"]
    L.append(f"let vgs_grid = vector({N_VGS})")
    L += [f"let vgs_grid[{i}] = {v}" for i, v in enumerate(vgs_vals)]
    L.append(f"let vds_grid = vector({N_VDS})")
    L += [f"let vds_grid[{i}] = {v}" for i, v in enumerate(vds_vals)]
    L += ["let ig = 0", f"while ig < {N_VGS}", "  let vgv = vgs_grid[ig]", "  let ivd = 0",
          f"  while ivd < {N_VDS}", "    let vdv = vds_grid[ivd]",
          "    alter vgs = $&vgv", "    alter vds = $&vdv", "    op", "    echo P"]
    L.append(f"    print @m.xdut.msky130_fd_pr__{devcell}[id]")   # 오라클 어댑터가 이 줄에서 op 프로브 형식을 읽는다
    L += [f"    print {pr[p.upper()]}" for p in OP_PARAMS[1:]]
    for src, prints in (("vgs", ("IG_G", "RG_G")), ("vds", ("IG_D", "ID_D")), ("vsrc", ("IG_S", "IS_S")),
                        ("vb", ("IG_B",))):
        L += [f"    alter {src} ac = 1", f"    {ac}"] + [f"    print {pr[k]}" for k in prints] + [f"    alter {src} ac = 0"]
    L += [f"    alter lchoke = {LCHOKE_NOISE}", "    alter vgs ac = 1",
          f"    noise v(d) vgs dec 1 {NOISE_F_PROBE:.0f} {NOISE_F_PROBE:.0f}", f"    print {pr['N_1HZ']}",
          f"    noise v(d) vgs dec 1 {F_TEST:.0f} {F_TEST:.0f}", f"    print {pr['N_HF']}",
          "    alter vgs ac = 0", f"    alter lchoke = {LCHOKE_AC}",
          "    destroy all",
          "    let ivd = ivd + 1", "  end", "  let ig = ig + 1", "end",
          f"echo SHOWMOD {L_um:g}", showmod_cmd("xdut").format(devcell=devcell),   # 실제로 쓴 bin(메타)
          "quit", ".endc", ".end"]
    return "\n".join(L) + "\n"


def _parse_output(path, devcell):
    """`echo P` 마커 뒤의 값 줄을 `_fields` 순서·식 이름과 대조해 읽는다 -> {열: [VGS, VDS] 배열}."""
    fl = _fields(devcell)
    n_f = len(fl)
    rows, cur = [], None
    for line in open(path, encoding="utf-8", errors="replace").read().splitlines():
        if line.strip() == "P":
            if cur is not None:
                raise RuntimeError(f"{path}: 점 {len(rows)} 값 {len(cur)}개 (기대 {n_f})")
            cur = []
            continue
        if cur is None:
            continue
        m = _VAL_RE.match(line)
        if m is None or line.lstrip().startswith("Doing analysis"):   # 분석마다 찍는 'TEMP = .. TNOM = ..' 줄
            continue
        name, expr = fl[len(cur)]
        if m.group(1).lower() != expr.lower():
            raise RuntimeError(f"{path}: 점 {len(rows)} 필드 {name}: '{m.group(1)}' != '{expr}'")
        cur.append(float(m.group(2)))
        if len(cur) == n_f:
            rows.append(cur)
            cur = None
    if cur is not None or len(rows) != N_VGS * N_VDS:
        raise RuntimeError(f"expected {N_VGS * N_VDS} points, parsed {len(rows)} from {path}")
    a = np.array(rows).reshape(N_VGS, N_VDS, n_f)
    raw = {name: a[:, :, k] for k, (name, _) in enumerate(fl)}
    w = 2 * math.pi * F_TEST
    out = {p.upper(): np.abs(raw[p.upper()]) for p in OP_PARAMS}
    out.update({"CGG": -raw["IG_G"] / w, "CGD": raw["IG_D"] / w, "CGS": raw["IG_S"] / w, "CGB": raw["IG_B"] / w,
                "CDD": -raw["ID_D"] / w, "CSS": -raw["IS_S"] / w,
                "SVG2_1HZ": raw["N_1HZ"] ** 2, "SVG2_HF": raw["N_HF"] ** 2})
    chk = {"gate_real_max_S": float(np.abs(raw["RG_G"]).max()),
           "vth_raw_min": float(raw["VTH"].min()), "vdsat_raw_min": float(raw["VDSAT"].min())}
    return out, chk


COLUMNS = ("ID", "GM", "GDS", "GMBS", "VTH", "VDSAT", "CGG", "CGD", "CGS", "CGB", "CDD", "CSS", "SVG2_1HZ", "SVG2_HF")


def _ltag(L_um: float) -> str:
    """체크포인트 이름에 쓰는 **값 기반** 태그(인덱스 기반이면 격자 중간 삽입 때 다른 L 결과가 조용히 재사용된다)."""
    return ("L%.4f" % L_um).replace(".", "p")


def _vstag(VS: float) -> str:
    return ("VS%.4f" % VS).replace(".", "p")


def _cleanup_temp(path, attempts=5, delay=0.4):
    """임시 파일 삭제 -- Windows 잠금 경합은 짧게 재시도, 그래도 안 되면 경고하고 계속(체크포인트는 이미 저장됨)."""
    for i in range(attempts):
        try:
            os.remove(path)
            return True
        except FileNotFoundError:
            return True
        except OSError as e:
            if i == attempts - 1:
                print(f"  [경고] 임시 파일 삭제 실패(계속 진행, 데이터 영향 없음): {os.path.basename(path)} -- {e}",
                      flush=True)
                return False
            time.sleep(delay)
    return False


def _check_log(stem, *paths):
    bad = []
    for p in paths:
        bad += [ln for ln in open(p, encoding="utf-8", errors="replace").read().splitlines() if _BAD_RE.search(ln)]
    if bad:
        raise RuntimeError(f"{stem}: ngspice 오류 {bad[:3]}")


def _log_conditions(path):
    txt = open(path, encoding="utf-8", errors="replace").read()
    temps = sorted(set(re.findall(r"TEMP\s*=\s*([-0-9.]+)", txt)))
    vers = sorted(set(re.findall(r"(ngspice-\d+\S*)", txt)))
    return ";".join(temps), ";".join(vers)


def _run_combo(cfg, devcell, L_um, VS, polarity, vb_sign):
    stem = f"{devcell}_{_ltag(L_um)}_{_vstag(VS)}"
    ckpt = os.path.join(cfg["ckpt"], stem + ".npz")
    if os.path.exists(ckpt):
        d = np.load(ckpt)
        if str(d["gen_sha256"]) == cfg["gen_sha"] and all(c in d.files for c in COLUMNS):
            return ({c: d[c] for c in COLUMNS}, json.loads(str(d["checks"])), str(d["temp_log"]),
                    str(d["ngspice_ver"]), 0.0, True)
    vb_dc = vb_sign * VS * -1
    netfile = os.path.join(cfg["work"], stem + ".cir")
    outfile = os.path.join(cfg["work"], stem + "_out.txt")
    errfile = os.path.join(cfg["work"], stem + "_err.txt")
    with open(netfile, "w") as f:
        f.write(_gen_netlist(devcell, L_um, VS, vb_dc, polarity))
    t0 = time.time()
    with open(outfile, "w") as fo, open(errfile, "w") as fe:
        subprocess.run([NGSPICE_EXE, "-b", netfile], cwd=cfg["work"], stdout=fo, stderr=fe, timeout=600,
                       check=False)
    dt = time.time() - t0
    _check_log(stem, outfile, errfile)
    out, chk = _parse_output(outfile, devcell)
    sm = parse_showmod(open(outfile, encoding="utf-8", errors="replace").read(), parse_bins(model_file(devcell)))
    if list(sm) != [f"{L_um:g}"]:
        raise RuntimeError(f"{stem}: showmod bin을 못 읽음 {sm}")
    chk["bin"] = sm[f"{L_um:g}"]
    temps, vers = _log_conditions(outfile)
    if not vers:
        temps2, vers = _log_conditions(errfile)
        temps = temps or temps2
    np.savez(ckpt, gen_sha256=cfg["gen_sha"], checks=json.dumps(chk), temp_log=temps, ngspice_ver=vers, **out)
    for p in (netfile, outfile, errfile):
        _cleanup_temp(p)
    return out, chk, temps, vers, dt, False


def run_device(devcell: str, polarity: int, vb_sign: int, cfg: dict):
    """한 소자의 (L, VS) 조합 전부를 cfg['jobs'] 병렬로 돌려 [L, VGS, VDS, VS] 배열 dict와 조합 기록을 낸다."""
    Ls, VSs = cfg["L_um"], cfg["VS"]
    arr = {c: np.zeros((len(Ls), N_VGS, N_VDS, len(VSs))) for c in COLUMNS}
    recs = []
    with cf.ThreadPoolExecutor(max_workers=cfg["jobs"]) as ex:
        futs = {ex.submit(_run_combo, cfg, devcell, L, VS, polarity, vb_sign): (iL, iV)
                for iL, L in enumerate(Ls) for iV, VS in enumerate(VSs)}
        for fu in cf.as_completed(futs):
            iL, iV = futs[fu]
            out, chk, temps, vers, dt, cached = fu.result()
            for c in COLUMNS:
                arr[c][iL, :, :, iV] = out[c]
            recs.append({"L_um": Ls[iL], "VS": float(VSs[iV]), "checks": chk, "temp": temps, "ngspice": vers,
                         "seconds": round(dt, 3), "cached": cached})
            with open(cfg["progress"], "a", encoding="utf-8") as pf:
                pf.write(f"{devcell} L={Ls[iL]} VS={VSs[iV]:.4f} {'cached' if cached else f'{dt:.2f}s'} "
                         f"elapsed={time.time() - cfg['t0']:.0f}s\n")
    return arr, recs


# --------------------------------------------------------------------------- L 입력
def read_l_list(l_json=None, l_um=None, l_json_key="L_um"):
    """L 목록(um)과 출처. `--l-json`: 리스트 또는 {key: [...]} json(key = `--l-json-key`, 기본 "L_um";
    예: 승인 파일의 "verification_midpoints_um"). `--l-um`: 쉼표 목록. json 출처는 path·sha256·key를 남긴다."""
    if l_json is not None and l_um is not None:
        raise SystemExit("--l-json 과 --l-um 중 하나만 준다")
    if l_json is None and l_um is None:
        l_json = L_GRID_JSON   # 기본: 승인된 L 목록 파일
    if l_json is not None:
        d = json.load(open(l_json, encoding="utf-8"))
        if isinstance(d, dict):
            if l_json_key not in d:
                raise SystemExit(f"{l_json} 에 키 {l_json_key!r} 가 없다(있는 키: {sorted(d)})")
            vals = d[l_json_key]
        else:
            if l_json_key != "L_um":
                raise SystemExit(f"{l_json} 은 리스트 json이라 --l-json-key {l_json_key!r} 를 쓸 수 없다")
            vals = d
        src = {"kind": "json", "path": os.path.abspath(l_json), "sha256": _sha256(l_json),
               "key": l_json_key if isinstance(d, dict) else None}
    else:
        if l_json_key != "L_um":
            raise SystemExit("--l-json-key 는 --l-json(또는 기본 승인 파일)과만 쓴다")
        vals = [x for x in l_um.split(",") if x.strip()]
        src = {"kind": "cli", "value": l_um}
    vals = [float(v) for v in vals]
    if vals != sorted(set(vals)):
        raise SystemExit(f"L 목록은 중복 없이 오름차순이어야 한다: {vals}")
    return vals, src


def check_l_list(l_list, devices, grid_um, work):
    """각 L: 제조 격자 위, 모델 bin L 범위([lmin 최솟값, lmax 최댓값]) 안. bin은 ngspice showmod로 읽는다
    -> {devcell: {L문자열: {lmin, lmax, wmin, wmax, model}}}."""
    out = {}
    for dev in devices:
        bins = parse_bins(model_file(dev))
        lo, hi = min(b["lmin"] for b in bins) * 1e6, max(b["lmax"] for b in bins) * 1e6
        for L in l_list:
            grid_key(L, grid_um)
            if not lo - 1e-9 <= L <= hi + 1e-9:
                raise SystemExit(f"{dev}: L={L} um 이 모델 bin 범위 [{lo}, {hi}] 밖")
        out[dev] = ngspice_bins(work, dev, l_list)
    return out


# --------------------------------------------------------------------------- candidates (bin 경계 불연속 측정)
def _read_raw(path):
    """ngspice binary rawfile(실수) -> {변수 이름 또는 [param]: ndarray}."""
    b = open(path, "rb").read()
    i = b.index(b"Binary:\n")
    nv = npt = None
    names, invars = [], False
    for ln in b[:i].decode("latin1").splitlines():
        if ln.startswith("No. Variables:"):
            nv = int(ln.split(":")[1])
        elif ln.startswith("No. Points:"):
            npt = int(ln.split(":")[1])
        elif ln.startswith("Flags:") and "real" not in ln:
            raise RuntimeError(f"{path}: 복소 raw는 지원 안 함")
        elif ln.startswith("Variables:"):
            invars = True
        elif invars and ln.strip():
            names.append(ln.split()[1])
    a = np.frombuffer(b[i + 8:], dtype="<f8", count=nv * npt).reshape(npt, nv)
    out = {}
    for k, n in enumerate(names):
        mm = re.search(r"\[(\w+)\]", n)
        out[mm.group(1) if mm else n] = a[:, k]
    return out


def _dc_run(work, devcell, L_um, VS_arr, polarity, vb_sign):
    """W_ref·L에서 VS마다 .dc(VDS 안쪽, VGS 바깥) -> id, gm, vth, vdsat [VGS, VDS, VS] (절댓값)."""
    stem = f"dc_{devcell}_{_ltag(L_um)}"
    inst = f"@m.xdut.msky130_fd_pr__{devcell}"
    sg, sd = (VGS_STOP - VGS_START) / (N_VGS - 1), (VDS_STOP - VDS_START) / (N_VDS - 1)
    L = [f"* bin boundary probe {devcell} L={L_um}"] + model_includes(devcell)
    L += ["vgs g 0 dc 0", "vds d 0 dc 0", "vsrc s 0 dc 0", "vb b 0 dc 0", DUT_LINE.format(devcell=devcell, L_um=L_um),
          ".save v(g) v(d) " + " ".join(f"{inst}[{q}]" for q in ("id", "gm", "vth", "vdsat")), ".control",
          "set filetype=binary"]
    for k, vs in enumerate(VS_arr):
        L.append(f"alter vb dc = {vb_sign * vs * -1:.9g}")
        L.append(f"dc vds {polarity * VDS_START:.9g} {polarity * VDS_STOP:.9g} {polarity * sd:.9g} "
                 f"vgs {polarity * VGS_START:.9g} {polarity * VGS_STOP:.9g} {polarity * sg:.9g}")
        L.append(f"write {os.path.join(work, f'{stem}_vs{k}.raw').replace(os.sep, '/')}")
    L += ["quit", ".endc", ".end"]
    cir, log, err = (os.path.join(work, stem + s) for s in (".cir", ".log", ".err"))
    open(cir, "w").write("\n".join(L) + "\n")
    with open(log, "w") as fo, open(err, "w") as fe:
        subprocess.run([NGSPICE_EXE, "-b", cir], cwd=work, stdout=fo, stderr=fe, timeout=300, check=False)
    _check_log(stem, log, err)
    res = {q: np.empty((N_VGS, N_VDS, len(VS_arr))) for q in ("id", "gm", "vth", "vdsat")}
    for k in range(len(VS_arr)):
        rp = os.path.join(work, f"{stem}_vs{k}.raw")
        r = _read_raw(rp)
        for q in res:
            res[q][:, :, k] = np.abs(r[q]).reshape(N_VGS, N_VDS)
        _cleanup_temp(rp)
    for p in (cir, log, err):
        _cleanup_temp(p)
    return res


def boundary_probe(work, devcell, polarity, vb_sign, b_um, grid_um, VS_arr):
    """모델 경계값 b 근처 격자점 b−2g … b+2g의 실제 bin(showmod)에서 전환 칸(t → t+1)을 찾고, 전환 칸의 Δln ID에서
    양쪽 bin 안 칸(t−1→t, t+1→t+2)의 평균을 뺀 점프(매끄러운 L 의존 제거)를 VGS 환산(÷ gm/ID)으로 잰다.
    점 = 네 L 모두 켜짐·포화(ID>0, VGS>=VTH, VDS>=VDSAT -- 문턱·포화 기준은 모델 op 값), W_ref, 전 VGS·VDS·VS 격자.
    불연속 판정은 하지 않는다(계획 K1b: '점프 > 그 셀 tol_V' -- tol_V는 입력). `end_point_um` = 전환 칸 두 점 가운데
    b가 아닌 점(b가 들지 않은 bin의 끝점; ngspice-46은 b를 아래 bin에 넣으므로 b+g)."""
    k = grid_key(b_um, grid_um)
    L5 = [round((k + d) * grid_um, 9) for d in (-2, -1, 0, 1, 2)]
    sm = ngspice_bins(work, devcell, L5)
    names = [sm[f"{L:g}"]["model"] for L in L5]
    trans = [i for i in range(4) if names[i] != names[i + 1]]
    if len(trans) != 1 or trans[0] not in (1, 2):
        return {"boundary_um": b_um, "L_um": L5, "bins": names, "skipped": "W_ref에서 전환이 한 번이 아님"}
    t = trans[0]
    Ls = L5[t - 1:t + 3]
    end_point = Ls[2] if Ls[1] == round(k * grid_um, 9) else Ls[1]
    r = [_dc_run(work, devcell, L, VS_arr, polarity, vb_sign) for L in Ls]
    names = names[t - 1:t + 3]
    vg = VGS_ARR[:, None, None]
    vd = VDS_ARR[None, :, None]
    mask = np.ones(r[0]["id"].shape, bool)
    for x in r:
        mask &= (x["id"] > 0) & (x["gm"] > 0) & (vg >= x["vth"]) & (vd >= x["vdsat"])
    lid = [np.log(np.where(mask, x["id"], 1.0)) for x in r]
    d = [lid[i + 1] - lid[i] for i in range(3)]          # 부호 있는 한 칸 Δln ID: 아래 bin 칸, 전환 칸, 위 bin 칸
    excess = d[1] - (d[0] + d[2]) / 2                     # 매끄러운 L 의존(1·2차)을 뺀 전환 칸 점프
    gmid = r[1]["gm"] / np.where(mask, r[1]["id"], 1.0)
    jump_v = np.abs(excess)[mask] / gmid[mask]            # VGS 환산 점프 |Δln ID|/(gm/ID) [V]
    dvth = np.abs((r[2]["vth"] - r[1]["vth"]) - ((r[1]["vth"] - r[0]["vth"]) + (r[3]["vth"] - r[2]["vth"])) / 2)[mask]

    def q(a):
        return {"median": float(np.median(a)), "p90": float(np.percentile(a, 90)), "max": float(a.max())}

    return {"boundary_um": b_um, "L_um": Ls, "bins": names, "end_point_um": end_point, "n_points": int(mask.sum()),
            "median_step_dlnID": {"lower_bin": float(np.median(d[0][mask])), "switch": float(np.median(d[1][mask])),
                                  "upper_bin": float(np.median(d[2][mask]))},
            "switch_excess_dlnID": q(np.abs(excess)[mask]), "switch_jump_vgs_equiv_V": q(jump_v),
            "switch_excess_dVTH_V": q(dvth)}


def candidates(a):
    grid = manufacturing_grid_um(a.tlef)
    devices = a.devices.split(",")
    vs_arr = vs_axis(a.vs_max)
    old = np.load(a.existing_npz)
    existing = sorted({round(grid_key(float(x) * 1e6, grid) * grid, 9) for x in old["L"]})
    lmins, per_dev = set(), {}
    for dev in devices:
        lm, _ = bin_lmins_um(dev, parse_bins(model_file(dev)))
        per_dev[dev] = lm
        lmins.update(lm)
    lo = min(lmins)
    in_range = lambda x: lo - 1e-12 <= x <= a.l_max_um + 1e-12   # noqa: E731
    lmins = sorted(x for x in lmins if in_range(x))
    os.makedirs(a.work, exist_ok=True)
    probes = {dev: [] for dev in devices}
    disc, ends = set(), set()
    for b in (x for x in lmins if x > lo):
        for dev in devices:
            if b not in per_dev[dev]:
                continue
            pol, vbs = (+1, +1) if COL_SUFFIX[dev] == "_n" else (-1, -1)
            p = boundary_probe(a.work, dev, pol, vbs, b, grid, vs_arr)
            if "skipped" not in p:   # 판정: 입력(--discontinuous-um 결정 또는 --tol-v 해상도). 이 파일은 임계값을 갖지 않는다
                if a.discontinuous_um is not None:
                    p["discontinuous"] = any(abs(b - x) < grid / 2 for x in a.discontinuous_um)
                    p["decided_by"] = "--discontinuous-um"
                else:
                    p["discontinuous"] = p["switch_jump_vgs_equiv_V"]["max"] > a.tol_v
                    p["decided_by"] = f"--tol-v {a.tol_v} vs max VGS-equivalent jump"
                if p["discontinuous"]:
                    disc.add(b)
                    ends.add(p["end_point_um"])
            probes[dev].append(p)
    ends = sorted(ends)
    cand = sorted({x for x in existing + lmins + ends if in_range(x)})
    origin = {f"{x:g}": [t for t, s in (("existing_anchor", existing), ("bin_lmin", lmins),
                                        ("other_side_end_of_discontinuous_boundary", ends)) if x in s] for x in cand}
    bins_c = check_l_list(cand, devices, grid, a.work)
    # 점이 2개(양끝)뿐인 bin 구간의 검증 전용 중점(LUT 축 아님, 계획 K2'). bin 구간 = W_ref가 쓰는 W bin(showmod
    # wmin/wmax)의 L 구간 [lmin, lmax]. 연속 경계 b는 양쪽 구간의 공통 끝점, 불연속 경계 b는 showmod가 고른 bin에만 든다.
    groups = {}
    for dev in devices:
        used = bins_c[dev]
        wset = {(u["wmin"], u["wmax"]) for u in used.values()}
        if len(wset) != 1:
            raise RuntimeError(f"{dev}: 후보 L마다 W bin이 다름 {wset}")
        wmin, wmax = next(iter(wset))
        for bn in parse_bins(model_file(dev)):
            if bn["wmin"] != wmin or bn["wmax"] != wmax:
                continue
            l0, l1 = bn["lmin"] * 1e6, bn["lmax"] * 1e6
            # 소속 = showmod 가 고른 model(경계 L 은 아래 bin -- 엔진 4.0.1 규칙과 같다). 구간 끝점이라도 다른 bin 에 속하면 뺀다.
            mem = [x for x in cand if l0 - 1e-9 <= x <= l1 + 1e-9 and used[f"{x:g}"]["model"] == bn["model"]]
            if mem:
                groups[(dev, bn["model"])] = mem
    mids = sorted({round(round((g[0] + g[1]) / 2 / grid) * grid, 9) for g in groups.values() if len(g) == 2})
    res = {"generated": datetime.datetime.now().isoformat(timespec="seconds"),
           "generator": os.path.basename(__file__), "generator_sha256": _sha256(os.path.abspath(__file__)),
           "manufacturing_grid_um": grid, "tlef": a.tlef, "l_max_um": a.l_max_um, "w_ref_m": W_REF_M,
           "existing_npz": os.path.abspath(a.existing_npz), "existing_anchors_um": existing,
           "bin_lmins_um": lmins, "discontinuous_boundaries_um": sorted(disc), "other_side_end_points_um": ends,
           "rule": "bin membership = ngspice showmod (not a Python rule). At each model boundary b, find the grid step "
                   "where the actual bin switches (t->t+1); jump = dlnID(switch) - mean(dlnID of the two in-bin "
                   "neighbour steps), VGS-equivalent = |jump|/(gm/ID); points on & saturated at all 4 L (ID>0, VGS>=VTH, "
                   "VDS>=VDSAT), W=W_ref, full VGS/VDS/VS axes. Discontinuity is an input decision "
                   "(--discontinuous-um, or --tol-v vs max jump). For a discontinuous b, add the switch-step point that "
                   "is not b (end point of the bin b does not belong to).",
           "decision_input": {"discontinuous_um": a.discontinuous_um, "tol_v": a.tol_v},
           "VS_axis": vs_arr.tolist(), "probes": probes, "candidates_um": cand, "origin": origin,
           "verification_midpoints_um_two_point_bins": mids, "bins_at_w_ref": bins_c}
    if os.path.exists(a.compare_json):   # 승인 목록 파일과 대조(모델 파일에서 같은 목록이 다시 나오는지)
        ref = json.load(open(a.compare_json, encoding="utf-8"))
        res["compare"] = {"file": os.path.abspath(a.compare_json), "sha256": _sha256(a.compare_json),
                          "L_um_equal": [round(x, 9) for x in ref["L_um"]] == cand,
                          "midpoints_equal": [round(x, 9) for x in ref.get("verification_midpoints_um", [])] == mids}
        print(f"compare {a.compare_json}: {res['compare']}")
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(f"candidates ({len(cand)}): {cand}")
    print(f"discontinuous boundaries: {sorted(disc)}")
    return res


# --------------------------------------------------------------------------- sweep
def vs_axis(vs_max=None):
    top = VGS_STOP if vs_max is None else vs_max
    n = int(round(top / VS_STEP)) + 1
    v = np.round(VS_STEP * np.arange(n), 9)
    if abs(v[-1] - top) > 1e-9:
        raise SystemExit(f"VS 상한 {top} 이 간격 {VS_STEP}의 배수가 아니다")
    return v


def sweep(a):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    grid = manufacturing_grid_um(a.tlef)
    l_list, l_src = read_l_list(a.l_json, a.l_um, a.l_json_key)
    devices = a.devices.split(",")
    VS = vs_axis(a.vs_max)
    os.makedirs(a.work, exist_ok=True)
    bins_per_L = check_l_list(l_list, devices, grid, a.work)
    ckpt = os.path.join(a.work, "ckpt")
    os.makedirs(ckpt, exist_ok=True)
    gen_sha = _sha256(os.path.abspath(__file__))
    cfg = dict(work=a.work, ckpt=ckpt, gen_sha=gen_sha, L_um=l_list, VS=VS, jobs=a.jobs, t0=time.time(),
               progress=os.path.join(a.work, "generation_progress.log"))
    with open(cfg["progress"], "a", encoding="utf-8") as pf:
        pf.write(f"# start {datetime.datetime.now().isoformat(timespec='seconds')} gen_sha256={gen_sha} "
                 f"L={l_list} VS={VS.tolist()} devices={devices} jobs={a.jobs}\n")
    runners = {"nfet_01v8": lambda: run_device("nfet_01v8", polarity=+1, vb_sign=+1, cfg=cfg),
               "pfet_01v8": lambda: run_device("pfet_01v8", polarity=-1, vb_sign=-1, cfg=cfg)}
    save, combos, model_sha = {}, {}, {}
    temps, vers = set(), set()
    checks = {}
    for dev in devices:
        arr, recs = runners[dev]()
        sfx = COL_SUFFIX[dev]
        save.update({c + sfx: arr[c] for c in COLUMNS})
        combos[dev] = sorted(recs, key=lambda r: (r["L_um"], r["VS"]))
        bad = [(r["L_um"], r["VS"]) for r in recs if r["checks"]["bin"] != bins_per_L[dev][f"{r['L_um']:g}"]]
        if bad:   # 스윕 프로세스 안 showmod와 사전 showmod가 다르면 거부
            raise RuntimeError(f"{dev}: 조합 showmod bin이 사전 확인과 다름 {bad[:5]}")
        temps |= {r["temp"] for r in recs}
        vers |= {r["ngspice"] for r in recs}
        files = _included_files(dev) + [os.path.join(PDK_ROOT, "cells", dev, f"sky130_fd_pr__{dev}.bins.csv")]
        model_sha[dev] = {os.path.relpath(f, PDK_ROOT).replace(os.sep, "/"): _sha256(f) for f in files}
        cgg = arr["CGG"]
        nz = np.abs(cgg) > 0
        rowsum = np.abs(cgg - (arr["CGD"] + arr["CGS"] + arr["CGB"]))[nz] / np.abs(cgg)[nz]
        checks[dev] = {"gate_rowsum_rel_max": float(rowsum.max()),
                       "gate_real_max_S": max(r["checks"]["gate_real_max_S"] for r in recs),
                       "vth_raw_min": min(r["checks"]["vth_raw_min"] for r in recs),
                       "vdsat_raw_min": min(r["checks"]["vdsat_raw_min"] for r in recs),
                       "cgg_min_F": float(cgg.min()), "cgb_min_F": float(arr["CGB"].min())}
    if len(temps) != 1 or len(vers) != 1 or not next(iter(temps)):
        raise RuntimeError(f"온도/버전이 조합마다 같지 않거나 못 읽음: {temps} {vers}")
    temp_c = float(next(iter(temps)))
    meta = {
        "generator": os.path.basename(__file__), "generator_sha256": gen_sha, "ngspice": next(iter(vers)),
        "ngspice_exe": NGSPICE_EXE, "pdk_root": PDK_ROOT, "corner": "tt", "temp_c_from_log": temp_c,
        "model_files_sha256": model_sha, "w_ref_m": W_REF_M, "dut_line": DUT_LINE,
        "L_source": l_src, "model_bin_per_L_at_w_ref": bins_per_L,
        "manufacturing_grid_um": grid, "tlef": a.tlef,
        "axes": {"L_m": [x * 1e-6 for x in l_list], "VGS_V": VGS_ARR.tolist(), "VDS_V": VDS_ARR.tolist(),
                 "VS_V": VS.tolist()},
        "array_layout": "[L, VGS, VDS, VS]", "column_suffix": COL_SUFFIX,
        "units": {"ID": "A at W_ref", "GM": "S", "GDS": "S", "GMBS": "S", "VTH": "V", "VDSAT": "V",
                  "CGG": "F", "CGD": "F", "CGS": "F", "CGB": "F", "CDD": "F", "CSS": "F",
                  "SVG2_1HZ": "V^2/Hz (gate-referred, f=NOISE_F_PROBE)", "SVG2_HF": "V^2/Hz (gate-referred, f=F_TEST)"},
        "sign_convention": "ID/GM/GDS/GMBS/VTH/VDSAT absolute values of BSIM op params (VDSAT = ngspice @m[vdsat], "
                           "same as tools/spice_oracle). Capacitances keep sign: CGG=-Im(i(vgs))/w gate-excited, "
                           "C_gx=+Im(i(vgs))/w x-excited (x=d,s,b), CDD=-Im(i(vds))/w, CSS=-Im(i(vsrc))/w, w=2*pi*F_TEST. "
                           "Source node at 0 V via vsrc; body = -VS (nfet) / +VS (pfet); pfet driven with negative VGS/VDS.",
        "frequencies_hz": {"F_TEST": F_TEST, "NOISE_F_PROBE": NOISE_F_PROBE},
        "checks": checks, "combos": combos,
        "date": datetime.date.today().isoformat(),
    }
    np.savez(a.out, corner="tt", temp_c=temp_c, w_ref_m=W_REF_M,
             L=np.array(l_list) * 1e-6, VGS=VGS_ARR, VDS=VDS_ARR, VS=VS,
             meta_json=json.dumps(meta, ensure_ascii=False), **save)
    with open(cfg["progress"], "a", encoding="utf-8") as pf:
        pf.write(f"# saved {a.out} total {time.time() - cfg['t0']:.1f}s\n")
    print(f"Saved to {a.out} (total {time.time() - cfg['t0']:.0f}s)")
    for k in sorted(save):
        print(f"{k}: min={save[k].min():.3e} max={save[k].max():.3e}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="sky130 기준 폭 gm/ID LUT 생성기")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sweep", help="LUT 생성")
    s.add_argument("--l-json", default=None,
                   help='L 목록 json(리스트 또는 {"L_um": [...]}); --l-um도 없으면 기본 sky130_lut_L_grid.json')
    s.add_argument("--l-json-key", default="L_um",
                   help='--l-json(기본 승인 파일 포함)에서 읽을 키. 검증 중점 실행 = verification_midpoints_um')
    s.add_argument("--l-um", default=None, help="L 목록(um, 쉼표)")
    s.add_argument("--out", required=True, help="산출 npz 경로")
    s.add_argument("--work", required=True, help="임시 넷리스트·체크포인트·진행 로그 경로")
    s.add_argument("--jobs", type=int, default=8)
    s.add_argument("--devices", default="nfet_01v8,pfet_01v8")
    s.add_argument("--vs-max", type=float, default=None, help="기본 = VGS 축 상한(소자 정격)")
    s.add_argument("--tlef", default=TLEF_PATH)
    c = sub.add_parser("candidates", help="L 후보 = 기존 앵커 ∪ bin lmin ∪ 불연속 경계 바로 아래 점")
    c.add_argument("--l-max-um", type=float, required=True, help="L 상한(사용자 결정 값을 넘긴다)")
    dg = c.add_mutually_exclusive_group(required=True)
    dg.add_argument("--discontinuous-um", type=lambda s: [float(x) for x in s.split(",") if x.strip()],
                    help="불연속으로 둘 경계 b(um, 쉼표) -- 결정 입력(예: 계획 K1b 기본안)")
    dg.add_argument("--tol-v", type=float, help="VGS 환산 점프 최댓값이 이 값(V, tol_V)을 넘는 경계를 불연속으로")
    c.add_argument("--work", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--existing-npz", default=EXISTING_LUT)
    c.add_argument("--compare-json", default=L_GRID_JSON, help="후보·중점을 대조할 L 목록 파일(기본 승인 목록)")
    c.add_argument("--devices", default="nfet_01v8,pfet_01v8")
    c.add_argument("--vs-max", type=float, default=None)
    c.add_argument("--tlef", default=TLEF_PATH)
    a = ap.parse_args(argv)
    if a.cmd == "sweep":
        sweep(a)
    else:
        candidates(a)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
