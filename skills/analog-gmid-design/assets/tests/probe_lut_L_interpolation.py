# -*- coding: utf-8 -*-
"""LUT의 **L 보간**이 gm/ID를 비물리적 값으로 만드는지 재는 조사 도구(2026-09-08).

B1 5단계(배선) 착수 전 계측 중에 발견했다. 계기: step 2("헤드룸 pre-pass에서
`solve_diode_connected_vds()` 호출")가 성립하는지 보려고 diode 곡선의 두 방향
(`gm_id -> vds` / `vds -> gm_id`)을 왕복 검산했더니 PMOS에서만 깨졌다.

## 무엇을 쟀나

1. `_gm_id_curve(L, vds, vsb)`가 주는 gm/ID 곡선의 최대값을 L을 바꿔가며 잰다.
   물리 상한은 1/(nV_T) ≈ 30~38(스윕 스크립트 docstring의 실측: NMOS 29.93 / PMOS 32.20).
2. 그 값이 LUT의 **L 앵커** 위에서와 앵커 **사이**에서 어떻게 다른지 나눠 본다.
3. 실제 사이징(VGS/전류밀도/W)이 얼마나 달라지는지 환산한다.

## 측정 결과 (2026-09-08, sky130_nfet_pfet_lut_sample.npz)

L 앵커: [0.15, 0.35, 0.5, 1.0, 1.5, 2.5, 4.0] um  -- 0.15와 0.35 사이가 비어 있다.

gm/ID 최대값 (vds=0.5, vsb=0):

    L(um)   앵커?   nmos     pmos
    0.150   앵커    24.8     26.2
    0.200   보간    27.0    403.0   <- 비물리
    0.250   보간    28.4   5516.8   <- 비물리
    0.300   보간    28.6  56646.3   <- 비물리
    0.350   앵커    26.8     29.9
    0.400   보간    26.9     40.2   <- 비물리
    0.450   보간    26.9     45.7   <- 비물리
    0.500   앵커    27.0     30.5
    0.830   보간    27.3     45.9   <- 비물리
    1.000   앵커    27.4     30.1

**앵커 위에서는 전부 정상이고, 앵커 사이에서만 PMOS가 터진다.** NMOS는 무사하다.

## 기전

`_gm_id_curve()`는 **ID를 로그공간에서**(`self._log_ID`, 세션29에 성능 목적으로 도입)
보간하고 **GM은 선형공간에서** 보간한 뒤 그 둘을 나눈다. 두 보간이 일관되지 않다.

PMOS는 L=0.15um과 L=0.35um 사이에서 같은 VGS의 ID가 **약 6자릿수** 차이 난다
(VGS=0에서 1.12e-11 A vs 6.50e-17 A -- 짧은 채널의 DIBL/서브스레숄드 누설이라 물성 자체는
정상이다). 그래서 중간점에서

    ID  <- 기하평균 2.70e-14   (로그보간)
    GM  <- 산술평균 1.46e-10   (선형보간)
    gm/ID = 5423   (일관되게 계산하면 26.15 -- **207배** 부풀려진다)

NMOS는 같은 구간의 ID 차이가 훨씬 완만해서 이 괴리가 드러나지 않는다.

## 실사이징 영향 (ID=10uA, vds=0.6, vsb=0)

    kind   L(um)  gm_id  VGS 현행   VGS 일관보간   W 현행     W 일관보간
    pmos   0.20   15.0   0.9280    0.7536       2.83um    25.5um
    pmos   0.25   15.0   1.0037    0.7873       2.84um    45.9um
    pmos   0.83   15.0   1.0832    1.0416       17.1um    30.9um
    nmos   0.83   15.0   0.6958    0.6926       5.11um    5.36um   (NMOS는 2~9%)

## 이게 실제 파이프라인에 닿는가 -- 닿는다

`L_stage2out_p` theta가 **M15/M25(PMOS)**를 `L in [0.15, 1.0] um`에서 **5nm 격자**로
탐색한다(`_theta_grid_points()`의 `L_grid_step` 경로). 격자점 대부분이 앵커 밖이다.
`L_cascode`(M2a/M2b PMOS 포함)도 같다.

다만 **현재 저장된 파일럿 산출물은 오염돼 있지 않다** -- PMOS가 전부 앵커에 안착했다
(M2a/M2b=1.0um, M15/M25=0.15um). 탐색이 오염된 후보와 정상 후보를 나란히 비교한 뒤
앵커를 골랐다는 뜻이고, 그 선택 자체가 아티팩트일 가능성은 남는다.

## 왜 지금 중요한가

계획 §0.3은 재탐색 해가 `L = 0.15~0.45um`에 있으리라 본다 -- **정확히 오염 대역**이다.
이 상태로 B1 5단계의 재탐색을 돌리면 그럴듯해 보이는 틀린 답이 나온다.

## 한계 -- "GM도 로그보간"이 완전한 해결책은 아니다

일관보간으로 바꾸면 비물리적 폭발은 사라지고 앵커값도 보존된다(상대변화 <1.5e-3, 그
잔차는 VDS축 보간에서 온다). 그러나 위 표의 `pmos L=0.20, gm_id=20`에서는 일관보간 쪽이
W=339mm라는 역시 쓸 수 없는 값을 낸다. **0.15~0.35um 구간은 PMOS 물성이 너무 빨리 변해서
어떤 보간식으로도 복원되지 않는다** -- 앵커를 더 넣는 것 말고는 답이 없다.

실행: assets 디렉터리에서 `python tests/probe_lut_L_interpolation.py`
"""
import sys, os
ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
import numpy as np
import sizing_recipe as sr


# ---------------------------------------------------------------------------
# 결과는 **파일에도 남긴다**(사용자 지시, 2026-09-08). stdout에만 쓰면
# `| grep | tail` 파이프가 백그라운드 전환 때 버퍼째 날아가, 계산은 성공했는데
# 결과만 잃는다(이 세션에서 실제로 두 번). 한 줄 쓸 때마다 append하므로 중간에
# 죽어도 거기까지는 건진다. 파일은 이 스크립트 옆에 `<이름>.result.txt`로 남는다.
# ---------------------------------------------------------------------------
_RESULT_PATH = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first_emit = [True]


def emit(*parts):
    """print와 같은 시그니처로 쓰되 파일에도 남긴다."""
    line = " ".join(str(p) for p in parts)
    print(line, flush=True)
    mode = "w" if _first_emit[0] else "a"
    _first_emit[0] = False
    with open(_RESULT_PATH, mode, encoding="utf-8") as _f:
        _f.write(line + "\n")



d = np.load(os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz"))
L_ANCH = [float(x) for x in d["L"]]


def mk(k):
    return sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                    d["GM_" + k], d["GDS_" + k], d["CGG_" + k], W_ref=5e-6)


def curve_consistent(lut, L, vds, vsb):
    """GM도 로그보간하는 대안 -- gm/ID = exp(interp(log GM) - interp(log ID))."""
    n = len(lut.VGS_grid)
    pts = np.column_stack([np.full(n, L), lut.VGS_grid, np.full(n, vds), np.full(n, vsb)])
    log_id = np.asarray(sr._multilinear_interp(lut._grids_list, lut._log_ID, pts))
    log_gm = np.asarray(sr._multilinear_interp(
        lut._grids_list, np.log(np.clip(lut.GM, 1e-24, None)), pts))
    return np.exp(log_gm - log_id)


PHYS_MAX = 40.0        # 1/(nV_T) 이론 상한(n<=1.5, 300K)에 여유를 준 판정선

emit("L 앵커(um):", [round(x * 1e6, 3) for x in L_ANCH])
emit()
emit("=== gm/ID 최대값: 앵커 위 vs 앵커 사이 (vds=0.5, vsb=0) ===")
emit("%-6s %-9s %-7s | %-14s %-14s | %s"
      % ("kind", "L(um)", "앵커?", "현행", "일관보간", "판정"))
emit("-" * 74)
n_bad = 0
for kind in ("nmos", "pmos"):
    lut = mk(kind[0])
    for Lum in (0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.83, 1.00):
        L = Lum * 1e-6
        _, gi = lut._gm_id_curve(L, 0.5, 0.0)
        gc = curve_consistent(lut, L, 0.5, 0.0)
        anch = any(abs(L - a) < 1e-12 for a in L_ANCH)
        bad = max(gi) > PHYS_MAX
        n_bad += bool(bad)
        emit("%-6s %-9.3f %-7s | %-14.1f %-14.1f | %s"
              % (kind, Lum, "앵커" if anch else "보간", max(gi), max(gc),
                 "★비물리(>%g)" % PHYS_MAX if bad else ""))
emit("\n비물리 판정 %d개 -- 전부 앵커 사이의 PMOS여야 한다." % n_bad)

emit()
emit("=== 기전: ID는 로그보간(기하평균), GM은 선형보간(산술평균) ===")
iVDS = int(np.argmin(np.abs(d["VDS"] - 0.5)))
emit("PMOS L=0.15um vs 0.35um, VDS=%.3f, VS=0" % d["VDS"][iVDS])
emit("%-8s | %-12s %-12s %-10s | %-12s %-12s"
      % ("VGS", "ID@0.15", "ID@0.35", "ID비", "gm/ID 현행", "gm/ID 일관"))
emit("-" * 76)
for i in (0, 4, 8, 16, 24):
    i0, i1 = d["ID_p"][0, i, iVDS, 0], d["ID_p"][1, i, iVDS, 0]
    g0, g1 = d["GM_p"][0, i, iVDS, 0], d["GM_p"][1, i, iVDS, 0]
    geo = np.exp(0.5 * (np.log(max(i0, 1e-18)) + np.log(max(i1, 1e-18))))
    ari, gl = 0.5 * (i0 + i1), 0.5 * (g0 + g1)
    emit("%-8.3f | %-12.3e %-12.3e %-10.3g | %-12.2f %-12.2f"
          % (d["VGS"][i], i0, i1, (i1 / i0 if i0 else float("nan")), gl / geo, gl / ari))

emit()
emit("=== 이 오염 대역을 실제로 탐색하는가 ===")
import json
topo = json.load(open(os.path.join(ASSETS, "library",
                                    "current_reuse_telescopic_ota.topology.json"),
                      encoding="utf-8"))
for th in (topo.get("sizing_roles") or {}).get("theta", []):
    f = th.get("feeds")
    if isinstance(f, dict) and f.get("type") == "metric_stage_budget":
        lo, hi = th["bounds"]
        emit("  theta %-16s L in [%.3f, %.3f]um  devices=%s"
              % (th["name"], lo * 1e6, hi * 1e6, f.get("devices")))
emit("  -> 5nm 격자(spec['L_grid_step'])로 훑으므로 격자점 대부분이 앵커 밖이다.")
