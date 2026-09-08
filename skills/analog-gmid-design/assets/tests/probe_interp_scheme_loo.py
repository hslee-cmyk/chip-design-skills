# -*- coding: utf-8 -*-
"""보간 방식을 **leave-one-out**으로 고르는 조사 도구(2026-09-08, B15 ①).

`_gm_id_curve()`가 ID는 로그공간·GM은 선형공간에서 보간해 두 보간이 불일치한다는 것까지는
`probe_lut_L_interpolation.py`가 보였다. 그럼 무엇으로 통일해야 하나? 논증으로 고르지 않고
**실측으로 고른다**: L 앵커 하나를 빼고 양옆 앵커에서 보간한 뒤, 그 앵커의 **실제 SPICE
스윕값**과 얼마나 다른지 잰다. LUT 자신이 정답표를 갖고 있으므로 이 검사는 공짜다.

## 1) gm/ID 곡선 -- 비교 대상 3가지

    현행   gm/ID = interp_lin(GM) / exp(interp_lin(log ID))     <- 두 보간이 불일치
    선형   gm/ID = interp_lin(GM) / interp_lin(ID)
    로그   gm/ID = exp(interp_lin(log GM) - interp_lin(log ID))

## 2) 배열별 -- 어느 배열을 로그공간에서 보간해야 하나

gm/ID만 보고 GM을 바꾸면 `gm_gds_ratio()`/`fT()`가 쓰는 `_query()`는 그대로 선형이라 같은
소자에 대해 두 값이 어긋난다. ID/GM/GDS/CGG를 각각 따로 재서 배열마다 결정한다.

## 측정 결과 (2026-09-08, 7앵커판 sky130_nfet_pfet_lut_sample.npz)

gm/ID 곡선 -- **로그가 모든 held-out 앵커에서, 두 kind 모두, 중앙값·최악 전부 이긴다**:

    kind   현행 중앙  선형 중앙  로그 중앙 | 현행 최악   선형 최악  로그 최악
    nmos   6.37       1.86      1.27      | 74.5        11.6      6.6
    pmos   13.70      4.99      2.63      | 17884.9     64.4      33.6

현행 방식의 PMOS 최악 오차가 **17,885%**다. 로그로 바꾸면 33.6%로 떨어진다.
다만 로그로 바꿔도 held-out L=0.35um에서 PMOS 중앙값이 19%다 -- **앵커 추가(③)가 함께
필요한 이유**이고, 두 조치가 같은 측정으로 정당화된다.

배열별 결과는 아래 실행 출력을 볼 것.

실행: assets 디렉터리에서 `python tests/probe_interp_scheme_loo.py [다른_npz_경로]`
"""
import sys
import os

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
import numpy as np
import sizing_recipe as sr

# 스윕이 이 파일을 갱신 중일 수 있으므로 인자로 다른 경로를 받을 수 있게 한다.
NPZ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    ASSETS, "sky130_nfet_pfet_lut_sample.npz")
d = np.load(NPZ)
L_ALL = [float(x) for x in d["L"]]
print("LUT:", os.path.basename(NPZ))
print("L 앵커(um):", [round(x * 1e6, 4) for x in L_ALL])
print()

# VGS 격자 중 소자가 실제로 켜져 있는(=사이징이 쓰는) 구간만 본다. 완전 off 영역의
# gm/ID 비는 수치적으로 의미가 없고, 어느 방식도 거기서는 정확할 수 없다.
ON_MIN_ID = 1e-12
VDS_LIST = [0.487, 0.900, 1.200]
VS_LIST = [0.0, 0.4]
METHODS = ("현행", "선형", "로그")


def build(kind, keep_idx):
    """keep_idx의 L 앵커만 남긴 LUT을 만든다(held-out 앵커는 빠진다)."""
    k = kind[0]
    sel = np.array(sorted(keep_idx))
    return sr.SemiEmpiricalGmIdLUT(
        d["L"][sel], d["VGS"], d["VDS"], d["VS"],
        d["ID_" + k][sel], d["GM_" + k][sel], d["GDS_" + k][sel], d["CGG_" + k][sel],
        W_ref=5e-6)


def curves(lut, L, vds, vsb):
    """세 가지 방식의 gm/ID 곡선을 한 번에 낸다."""
    n = len(lut.VGS_grid)
    pts = np.column_stack([np.full(n, L), lut.VGS_grid, np.full(n, vds), np.full(n, vsb)])
    lin_id = np.asarray(sr._multilinear_interp(lut._grids_list, lut.ID, pts))
    lin_gm = np.asarray(sr._multilinear_interp(lut._grids_list, lut.GM, pts))
    log_id = np.asarray(sr._multilinear_interp(lut._grids_list, lut._log_ID, pts))
    log_gm = np.asarray(sr._multilinear_interp(
        lut._grids_list, np.log(np.clip(lut.GM, 1e-30, None)), pts))
    return {
        "현행": lin_gm / np.clip(np.exp(log_id), 1e-30, None),
        "선형": lin_gm / np.clip(lin_id, 1e-30, None),
        "로그": np.exp(log_gm - log_id),
    }


def truth(kind, iL, iVDS, iVS):
    k = kind[0]
    return (d["GM_" + k][iL, :, iVDS, iVS]
            / np.clip(d["ID_" + k][iL, :, iVDS, iVS], 1e-30, None))


print("=== 1) gm/ID 곡선: 앵커 하나를 빼고 보간해 그 앵커의 실측값과 대조 ===")
print("(상대오차 %%, 켜진 구간만: ID > %.0e A)" % ON_MIN_ID)
print()
print("%-6s %-9s | %-26s | %-26s" % ("kind", "held-out", "중앙값 오차(%)", "최악 오차(%)"))
print("%-6s %-9s | %-8s %-8s %-8s | %-8s %-8s %-8s"
      % ("", "L(um)", "현행", "선형", "로그", "현행", "선형", "로그"))
print("-" * 80)
agg = {kd: {m: [] for m in METHODS} for kd in ("nmos", "pmos")}
for kind in ("nmos", "pmos"):
    for iL in range(1, len(L_ALL) - 1):        # 양끝은 보간이 아니라 외삽이라 제외
        lut = build(kind, [i for i in range(len(L_ALL)) if i != iL])
        errs = {m: [] for m in METHODS}
        for vds in VDS_LIST:
            iVDS = int(np.argmin(np.abs(d["VDS"] - vds)))
            for vs in VS_LIST:
                iVS = int(np.argmin(np.abs(d["VS"] - vs)))
                ref = truth(kind, iL, iVDS, iVS)
                on = d["ID_" + kind[0]][iL, :, iVDS, iVS] > ON_MIN_ID
                if not on.any():
                    continue
                got = curves(lut, L_ALL[iL], float(d["VDS"][iVDS]), float(d["VS"][iVS]))
                for m, v in got.items():
                    e = np.abs(v[on] - ref[on]) / np.abs(ref[on]) * 100.0
                    errs[m].extend(e.tolist())
                    agg[kind][m].extend(e.tolist())
        print("%-6s %-9.4f | %-8.2f %-8.2f %-8.2f | %-8.1f %-8.1f %-8.1f"
              % (kind, L_ALL[iL] * 1e6,
                 np.median(errs["현행"]), np.median(errs["선형"]), np.median(errs["로그"]),
                 np.max(errs["현행"]), np.max(errs["선형"]), np.max(errs["로그"])))

print()
print("--- 전체 집계 ---")
print("%-6s | %-10s %-10s %-10s | %-10s %-10s %-10s"
      % ("kind", "현행 중앙", "선형 중앙", "로그 중앙", "현행 최악", "선형 최악", "로그 최악"))
print("-" * 74)
for kind in ("nmos", "pmos"):
    a = agg[kind]
    print("%-6s | %-10.2f %-10.2f %-10.2f | %-10.1f %-10.1f %-10.1f"
          % (kind, np.median(a["현행"]), np.median(a["선형"]), np.median(a["로그"]),
             np.max(a["현행"]), np.max(a["선형"]), np.max(a["로그"])))
print()
print("중앙값 기준 승자: " + " / ".join(
    "%s=%s" % (kd, min(agg[kd], key=lambda m: np.median(agg[kd][m])))
    for kd in ("nmos", "pmos")))

print()
print("=== 2) 배열별 leave-one-out (선형 vs 로그, 상대오차 %) ===")
print("%-6s %-7s | %-20s | %-20s" % ("kind", "배열", "중앙값 오차(%)", "최악 오차(%)"))
print("%-6s %-7s | %-9s %-9s | %-9s %-9s" % ("", "", "선형", "로그", "선형", "로그"))
print("-" * 62)
for kind in ("nmos", "pmos"):
    k = kind[0]
    for arr_name in ("ID", "GM", "GDS", "CGG"):
        full = d[arr_name + "_" + k]
        lin_e, log_e = [], []
        for iL in range(1, len(L_ALL) - 1):
            keep = np.array([i for i in range(len(L_ALL)) if i != iL])
            sub = full[keep]
            grids = [d["L"][keep].tolist(), d["VGS"].tolist(),
                     d["VDS"].tolist(), d["VS"].tolist()]
            logsub = np.log(np.clip(sub, 1e-30, None))
            for vds in VDS_LIST:
                iVDS = int(np.argmin(np.abs(d["VDS"] - vds)))
                for vs in VS_LIST:
                    iVS = int(np.argmin(np.abs(d["VS"] - vs)))
                    on = d["ID_" + k][iL, :, iVDS, iVS] > ON_MIN_ID
                    if not on.any():
                        continue
                    n = len(d["VGS"])
                    pts = np.column_stack([np.full(n, L_ALL[iL]), d["VGS"],
                                            np.full(n, float(d["VDS"][iVDS])),
                                            np.full(n, float(d["VS"][iVS]))])
                    ref = full[iL, :, iVDS, iVS]
                    lin = np.asarray(sr._multilinear_interp(grids, sub, pts))
                    log = np.exp(np.asarray(sr._multilinear_interp(grids, logsub, pts)))
                    denom = np.abs(ref[on])
                    lin_e.extend((np.abs(lin[on] - ref[on]) / denom * 100).tolist())
                    log_e.extend((np.abs(log[on] - ref[on]) / denom * 100).tolist())
        print("%-6s %-7s | %-9.2f %-9.2f | %-9.1f %-9.1f"
              % (kind, arr_name, np.median(lin_e), np.median(log_e),
                 np.max(lin_e), np.max(log_e)))
