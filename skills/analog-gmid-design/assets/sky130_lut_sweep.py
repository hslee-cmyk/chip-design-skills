#!/usr/bin/env python
"""sky130_lut_sweep.py -- real 4D gm/ID LUT generator using ngspice + the SkyWater sky130
open-source PDK (nfet_01v8 / pfet_01v8). Produces data directly loadable by
SemiEmpiricalGmIdLUT in sizing_recipe.py.

이 스크립트는 lut-generation-checklist.md §7.4(foundry 특성화 절차)의 실제 구현체이자, §7.3의
"Cgd/Cdd는 op-info로 뽑지 말고 AC/Y-parameter로 뽑아라"는 함정 항목을 실제로 겪고 고친 결과다.
`sky130_nfet_pfet_lut_sample.npz`가 이 스크립트로 생성한 (검증된) 샘플 결과물이다.

## 사전 준비 (한 번만) — CLAUDE.md·sky130-worked-example.md §1 참조

1. ngspice-46(Windows 네이티브, SourceForge, BSD 라이선스).
2. sky130 PDK 모델(SkyWater, Apache-2.0) — sparse-checkout으로 `models`+`cells/nfet_01v8`+
   `cells/pfet_01v8`만 받는다(전체 110MB 중 28MB).
3. 아래 NGSPICE_EXE / PDK_ROOT 상수를 자신의 경로로 수정.

## 왜 AC/Y-parameter로 뽑는가 (실제로 겪은 문제 — sky130-worked-example.md §7 참조)

ngspice BSIM4의 `@device[cgd]`/`@device[cdd]` **op-info 파라미터는 신뢰할 수 없다** — 실측 결과
Cgd는 op-info 대비 AC 추출값이 **36배**, Cdd는 부호까지 틀리고 **~300배** 차이가 났다(직접
`.op` 재확인으로 검증). Cgg는 상대적으로 양호(27% 차이)하지만 이 스크립트는 일관성을 위해
Cgg/Cgd 둘 다 AC/Y-parameter로 통일해 뽑는다. ID/GM/GDS는 op-info가 신뢰할 만하다(BSIM이
직접 계산하는 해석적 도함수이자 정의가 모호하지 않은 스칼라 DC 값이므로 — 다의적인 트랜스-커패시턴스
행렬과 다르다).

**추출 원리** (2-포트 Y-parameter, 게이트=포트1, 드레인=포트2, 소스/바디 접지):
```
Y11 = i_gate/v_gate |v_drain=0(AC접지)   = jw*Cgg   -> Cgg = |Y11|/(2*pi*f)
Y12 = i_gate/v_drain |v_gate=0(AC접지)   = -jw*Cgd  -> Cgd = |Y12|/(2*pi*f)
```
gm은 게이트 여기 시 드레인 전류(Y21)에 실려나오므로, **게이트 전류(i_gate)를 보는 한** gm 오염이
전혀 없다 — 이게 Y11/Y12로 뽑아야 하는 핵심 이유다. f=100MHz(fT 대비 충분히 낮아 순수 용량성
구간)에서 단일 주파수로 계산하며, 10~1000MHz 대에서 크기가 주파수에 선형 비례하는 것으로 순수
용량성임을 확인했다.

## 구현 메모 — ngspice 컨트롤 스크립트 내부 루프

각 (L, VS, 소자타입) 조합마다 ngspice 프로세스 하나를 띄우고, 그 안에서 VGS×VDS 49×49=2401개
바이어스점을 `.control` 블록의 `while` 루프로 순회한다(점마다 새 프로세스를 띄우면 너무 느림).
각 점에서: `alter`로 DC 바이어스 변경 → `op`으로 id/gm/gds 추출 → `alter ... ac=1/0` 전환 후
`ac lin 1 100meg 100meg` 두 번(Y11 설정, Y12 설정)으로 Cgg/Cgd 추출. 결과는 `echo`/`print`로
표준출력에 쌓아 Python에서 라인 단위로 파싱한다(ngspice 벡터를 루프 안에서 누적하는 방식은 각
분석마다 새 plot 컨텍스트가 생겨 실패했다 — 대신 표준출력 파싱이 안정적이었다).

## 체크포인트 (재실행 안전성)

전체 스윕(NMOS+PMOS, L4×VS5×49×49)은 약 55분 걸린다. 조합(devcell,L,VS)마다 즉시
`ac_sweep_checkpoints/*.npz`로 저장하므로, 중간에 프로세스가 죽어도(이 스크립트 개발 중 실제로
한 번 background timeout으로 죽었다) 재실행 시 이미 끝난 조합은 건너뛰고 이어서 한다.

## 검증된 사실

- gm/ID 최대값 NMOS 29.93 S/A, PMOS 32.20 S/A(이론치 1/(nUT), n≈1.3 가정 시 ≈29.6과 근접),
  두 소자 모두 VGS에 대해 단조감소.
- Walker CS/차동쌍 pole-zero 예제(gm-id-methodology.md §6.5)를 이 LUT로 완전히 재현 —
  fp1=739.85MHz, fp2=5.779GHz, W=3.32um. 별도로 손으로 한 단일점 AC 계산과 소수점까지 일치.
- PMOS gm/ID=20(L=0.5um,VDS=0.9V)에서 W가 커지는 현상은 버그가 아니라 실제 물성(직접 `.op`
  재확인으로 검증됨) — sky130-worked-example.md §5 참조.
"""
import subprocess
import sys
import os
import re
import math
import time
import numpy as np

# ---------------------------------------------------------------------------
# 자신의 환경에 맞게 수정
# ---------------------------------------------------------------------------
NGSPICE_EXE = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
PDK_ROOT = r"C:\pdk\sky130_fd_pr"          # sparse-checkout으로 받은 위치
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
LOD_SPICE = os.path.join(PDK_ROOT, "models", "parameters", "lod.spice")
CKPT_DIR = os.path.join(OUTPUT_DIR, "ac_sweep_checkpoints")

# ---------------------------------------------------------------------------
# 스윕 격자 (Jespers-style VGS/VDS 49점, L 4개, VS 5개 — 데모 규모, 필요시 조정)
# ---------------------------------------------------------------------------
# 2026-08-13(세션31 계속, BZ①/CA -- two_stage_ota gain_db>=60이 L=1.0um(기존 상한)까지의
# LUT로는 실제 sky130 LUT로도 물리적으로 불가능함을 실측 확인(.ai/context.md 세션31 CA)한 뒤
# 사용자 지시로 L 상한 확장. 기존 4개 앵커점([0.15,0.35,0.5,1.0])은 그대로 두고 **뒤에만
# 추가**한다(오름차순 유지 -- ac_sweep_checkpoints/*_L{0..3}_VS*.npz 40개가 그대로 재사용되고,
# sky130_regression_reference.json의 nmcnr_3stage 회귀 케이스는 L_candidates="lut.L"로 raw
# LUT.L 배열을 그대로 쓰는데 objective=power 동점 tie-break가 "먼저 나온 후보 유지"라 앞쪽
# 원소 순서/값이 안 바뀌면 골든값도 안 바뀐다 -- 새 앵커는 반드시 끝에만 추가할 것, 중간
# 삽입은 기존 인덱스를 밀어 체크포인트 캐시와 회귀 케이스를 둘 다 깬다).
L_GRID_UM = [0.15, 0.35, 0.5, 1.0, 1.5, 2.5, 4.0]
N_VGS, N_VDS = 49, 49
VGS_START, VGS_STOP = 0.0, 1.8   # sky130 nfet_01v8/pfet_01v8은 1.8V 소자
VDS_START, VDS_STOP = 0.0, 1.8
VS_GRID = [0.0, 0.2, 0.4, 0.6, 0.8]
F_TEST = 100e6                    # AC 추출 주파수 (fT 대비 충분히 낮은 순수 용량성 구간)

VGS_ARR = np.linspace(VGS_START, VGS_STOP, N_VGS)
VDS_ARR = np.linspace(VDS_START, VDS_STOP, N_VDS)
_NUM_RE = re.compile(r"=\s*([-+0-9.eE]+)\s*$")


NOISE_F_PROBE = 1.0    # SID_1F는 1Hz 기준(§ SemiEmpiricalGmIdLUT.noise_1f_density 참고)
LCHOKE_AC = 1e-15      # Y11/Y12(100MHz) 측정 중엔 사실상 wire(임피던스 6e-7옴 무시 가능)
LCHOKE_NOISE = 1e9     # noise(1Hz) 측정 중엔 사실상 open(임피던스 6e9옴, ro보다 훨씬 큼)


def _gen_netlist(devcell, L_um, VS, vb_dc, polarity, lod_include):
    """polarity: +1(NMOS, 양의 VGS/VDS) 또는 -1(PMOS, 음의 VGS/VDS 인가).

    배치 7-5b(2026-07-31) -- SID_1F(1/f 노이즈, 배치 7-3g가 요구하지만 이 스크립트엔 없던 필드)
    추가. 드레인을 이상적 DC 전압원(`vds`)이 그대로 클램프하면 `.noise v(d) ...`가 항상
    정확히 0을 반환한다(이상적 전압원 노드는 정의상 잡음전압이 0) -- 실측으로 확인한 뒤(아래
    참고), `vds`가 중간노드 `dd`를 구동하고 큰 인덕터(`lchoke`, DC저항 0 -> 동작점 완전
    보존)로 실제 드레인 `d`와 분리하는 구조로 바꿨다. 인덕턴스 값은 `alter`로 두 상태를
    오간다: Y11/Y12(100MHz) 측정 중엔 `LCHOKE_AC`(사실상 wire, 기존 측정과 동일한 결과를
    내도록)로, noise(1Hz) 측정 직전엔 `LCHOKE_NOISE`(사실상 open, 잡음이 드레인 자체
    출력임피던스로만 나타나도록)로 전환 -- 단일 인덕터로 두 마리 토끼를 잡을 수 없어서
    (임피던스는 주파수에 비례 증가만 하므로) 값 자체를 전환하는 방식을 택했다. 단일
    bias점 스탠드얼론 테스트로 세 가지 다 확인: (1) 초기 클램프 구조는 노이즈가 항상
    0(이상적 전압원 노드는 잡음전압이 정의상 0), (2) choke-decouple 단독 구조는 비영값,
    (3) choke 토글(AC 측정 땐 작게, noise 측정 땐 크게)이 기존 Y11/Y12/id/gm/gds 값을
    전혀 바꾸지 않으면서 (2)와 정확히 같은 noise 값을 낸다."""
    vgs_vals = [round(polarity * v, 6) for v in VGS_ARR]
    vds_vals = [round(polarity * v, 6) for v in VDS_ARR]
    L = []
    L.append(f"* AC-based sweep {devcell} L={L_um}um VS={VS}")
    if lod_include:
        L.append(f'.include "{lod_include}"')
    L.append(f'.include "{PDK_ROOT}\\cells\\{devcell}\\sky130_fd_pr__{devcell}__tt.pm3.spice"')
    L.append(f'.include "{PDK_ROOT}\\cells\\{devcell}\\sky130_fd_pr__{devcell}__mismatch.corner.spice"')
    L.append("")
    L.append("vgs g 0 dc 0 ac 1")
    L.append("vds dd 0 dc 0 ac 0")
    L.append(f"lchoke dd d {LCHOKE_AC}")
    L.append(f"vb  b 0 dc {vb_dc}")
    L.append(f"xdut d g 0 b sky130_fd_pr__{devcell} l={L_um}u w=5u ad=2.5p as=2.5p pd=7u ps=7u")
    L.append("")
    L.append(".control")
    L.append(f"let vgs_grid = vector({N_VGS})")
    for i, v in enumerate(vgs_vals):
        L.append(f"let vgs_grid[{i}] = {v}")
    L.append(f"let vds_grid = vector({N_VDS})")
    for i, v in enumerate(vds_vals):
        L.append(f"let vds_grid[{i}] = {v}")
    L.append("let ig = 0")
    L.append(f"while ig < {N_VGS}")
    L.append("  let vgv = vgs_grid[ig]")
    L.append("  let ivd = 0")
    L.append(f"  while ivd < {N_VDS}")
    L.append("    let vdv = vds_grid[ivd]")
    L.append("    alter vgs = $&vgv")
    L.append("    alter vds = $&vdv")
    L.append("    op")
    L.append("    echo P")
    L.append(f"    print @m.xdut.msky130_fd_pr__{devcell}[id]")
    L.append(f"    print @m.xdut.msky130_fd_pr__{devcell}[gm]")
    L.append(f"    print @m.xdut.msky130_fd_pr__{devcell}[gds]")
    L.append("    alter vgs ac = 1")
    L.append("    alter vds ac = 0")
    L.append(f"    ac lin 1 {F_TEST:.0f} {F_TEST:.0f}")
    L.append("    print mag(i(vgs))")            # Y11 -> Cgg
    L.append("    alter vgs ac = 0")
    L.append("    alter vds ac = 1")
    L.append(f"    ac lin 1 {F_TEST:.0f} {F_TEST:.0f}")
    L.append("    print mag(i(vgs))")            # Y12 -> Cgd
    L.append(f"    alter lchoke = {LCHOKE_NOISE}")
    L.append("    alter vgs ac = 1")
    L.append("    alter vds ac = 0")
    L.append(f"    noise v(d) vgs dec 1 {NOISE_F_PROBE:.0f} {NOISE_F_PROBE:.0f}")
    L.append("    print inoise_spectrum")        # 게이트환산 1/f+열 잡음밀도(1Hz) -> SID_1F
    L.append(f"    alter lchoke = {LCHOKE_AC}")
    L.append("    let ivd = ivd + 1")
    L.append("  end")
    L.append("  let ig = ig + 1")
    L.append("end")
    L.append("quit")
    L.append(".endc")
    L.append(".end")
    return "\n".join(L) + "\n"


def _parse_output(path):
    """echo 'P' 마커로 구분된 반복 출력에서 id/gm/gds/Y11-mag/Y12-mag/noise를 순서대로
    파싱한다(배치 7-5b: `inoise_spectrum` 6번째 값 추가 -- SID_1F)."""
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    id_v, gm_v, gds_v, y11_v, y12_v, noise_v = [], [], [], [], [], []
    cur = []
    for line in lines:
        if "[id]" in line:
            cur = [float(_NUM_RE.search(line).group(1))]
        elif "[gm]" in line and cur:
            cur.append(float(_NUM_RE.search(line).group(1)))
        elif "[gds]" in line and cur:
            cur.append(float(_NUM_RE.search(line).group(1)))
        elif line.strip().startswith("mag(") and len(cur) in (3, 4):
            cur.append(float(_NUM_RE.search(line).group(1)))
        elif line.strip().startswith("inoise_spectrum") and len(cur) == 5:
            cur.append(float(_NUM_RE.search(line).group(1)))
            id_v.append(cur[0]); gm_v.append(cur[1]); gds_v.append(cur[2])
            y11_v.append(cur[3]); y12_v.append(cur[4]); noise_v.append(cur[5])
            cur = []
    n = N_VGS * N_VDS
    if len(id_v) != n:
        raise RuntimeError(f"expected {n} points, parsed {len(id_v)} from {path}")
    ID = np.abs(np.array(id_v)).reshape(N_VGS, N_VDS)
    GM = np.abs(np.array(gm_v)).reshape(N_VGS, N_VDS)
    GDS = np.abs(np.array(gds_v)).reshape(N_VGS, N_VDS)
    CGG = np.abs(np.array(y11_v)).reshape(N_VGS, N_VDS) / (2 * math.pi * F_TEST)
    CGD = np.abs(np.array(y12_v)).reshape(N_VGS, N_VDS) / (2 * math.pi * F_TEST)
    SID_1F = np.abs(np.array(noise_v)).reshape(N_VGS, N_VDS)
    return ID, GM, GDS, CGG, CGD, SID_1F


def _run_combo(devcell, iL, L_um, iVS, VS, polarity, vb_sign):
    os.makedirs(CKPT_DIR, exist_ok=True)
    ckpt = os.path.join(CKPT_DIR, f"{devcell}_L{iL}_VS{iVS}.npz")
    if os.path.exists(ckpt):
        d = np.load(ckpt)
        if "SID_1F" in d:
            return d["ID"], d["GM"], d["GDS"], d["CGG"], d["CGD"], d["SID_1F"]
        # 배치 7-5b 이전(노이즈 없이) 생성된 체크포인트 -- 그대로 못 쓴다. 재실행해서 채운다.

    vb_dc = vb_sign * VS * -1
    netfile = os.path.join(OUTPUT_DIR, f"_ac_{devcell}_L{iL}_VS{iVS}.cir")
    outfile = os.path.join(OUTPUT_DIR, f"_ac_{devcell}_L{iL}_VS{iVS}_out.txt")
    net = _gen_netlist(devcell, L_um, VS, vb_dc, polarity,
                        LOD_SPICE if devcell.startswith("pfet") else "")
    with open(netfile, "w") as f:
        f.write(net)
    with open(outfile, "w") as fo:
        subprocess.run([NGSPICE_EXE, "-b", netfile], cwd=OUTPUT_DIR,
                        stdout=fo, stderr=subprocess.STDOUT, timeout=300)
    result = _parse_output(outfile)
    np.savez(ckpt, ID=result[0], GM=result[1], GDS=result[2], CGG=result[3], CGD=result[4],
             SID_1F=result[5])
    os.remove(netfile)
    os.remove(outfile)
    return result


def run_device(devcell: str, polarity: int, vb_sign: int, t0: float):
    nL, nVS = len(L_GRID_UM), len(VS_GRID)
    ID = np.zeros((nL, N_VGS, N_VDS, nVS))
    GM = np.zeros((nL, N_VGS, N_VDS, nVS))
    GDS = np.zeros((nL, N_VGS, N_VDS, nVS))
    CGG = np.zeros((nL, N_VGS, N_VDS, nVS))
    CGD = np.zeros((nL, N_VGS, N_VDS, nVS))
    SID_1F = np.zeros((nL, N_VGS, N_VDS, nVS))
    for iL, L_um in enumerate(L_GRID_UM):
        for iVS, VS in enumerate(VS_GRID):
            id_, gm_, gds_, cgg_, cgd_, sid1f_ = _run_combo(devcell, iL, L_um, iVS, VS, polarity, vb_sign)
            ID[iL, :, :, iVS] = id_
            GM[iL, :, :, iVS] = gm_
            GDS[iL, :, :, iVS] = gds_
            CGG[iL, :, :, iVS] = cgg_
            CGD[iL, :, :, iVS] = cgd_
            SID_1F[iL, :, :, iVS] = sid1f_
            print(f"  [{devcell}] L={L_um}um VS={VS} done ({time.time()-t0:.0f}s elapsed)", flush=True)
    return ID, GM, GDS, CGG, CGD, SID_1F


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    t0 = time.time()

    print("=== NMOS (nfet_01v8) ===")
    ID_n, GM_n, GDS_n, CGG_n, CGD_n, SID_1F_n = run_device("nfet_01v8", polarity=+1, vb_sign=+1, t0=t0)

    print("=== PMOS (pfet_01v8) ===")
    ID_p, GM_p, GDS_p, CGG_p, CGD_p, SID_1F_p = run_device("pfet_01v8", polarity=-1, vb_sign=-1, t0=t0)

    npz_path = os.path.join(OUTPUT_DIR, "sky130_nfet_pfet_lut_sample.npz")
    np.savez(npz_path,
             L=np.array(L_GRID_UM) * 1e-6, VGS=VGS_ARR, VDS=VDS_ARR, VS=np.array(VS_GRID),
             ID_n=ID_n, GM_n=GM_n, GDS_n=GDS_n, CGG_n=CGG_n, CGD_n=CGD_n, SID_1F_n=SID_1F_n,
             ID_p=ID_p, GM_p=GM_p, GDS_p=GDS_p, CGG_p=CGG_p, CGD_p=CGD_p, SID_1F_p=SID_1F_p)
    print(f"\nSaved to {npz_path} (total {time.time()-t0:.0f}s)")
    for name, arr in [("ID_n", ID_n), ("CGG_n", CGG_n), ("CGD_n", CGD_n), ("SID_1F_n", SID_1F_n),
                      ("ID_p", ID_p), ("CGG_p", CGG_p), ("CGD_p", CGD_p), ("SID_1F_p", SID_1F_p)]:
        print(f"{name}: min={arr.min():.3e} max={arr.max():.3e}")
