# -*- coding: utf-8 -*-
"""gm_id 축에서 gain(gm/gds)/V_A/면적이 실제로 어떻게 움직이는지 LUT로 재는 조사 스크립트.

계획 문서 §10.2의 A10/A11 근거를 만든 도구다. 두 가지를 잰다:

  1. 분리형 `gain = gm_id x V_A` 가 얼마나 틀리는가
     -- V_A가 gm_id에 따라 감소하므로 분리형은 gain을 **과대평가**한다(L=0.35um/VDS=0.6에서
        gm_id 5->26 구간 5.50dB). §7.9가 gain 제약을 폐형식 대신 compute_metric()에 위임하는
        결정(v4.0)의 정량 근거.
  2. gm/gds 가 gm_id에 단조인가
     -- 아니다. VDS>=0.6에서 gm_id ~18~20.5에 내부 최댓값이 있고 그 위는 gain이 떨어지면서
        면적만 폭발한다(A11). "gm_id를 올리면 gain이 오른다"는 KKT 전제가 거기서 깨진다.

실행: 이 디렉터리 기준 `python tests/probe_gmid_gain_landscape.py`
(자동 테스트가 아니라 **조사용**이다 -- 값을 단정하지 않고 그때의 LUT가 말하는 것을 찍는다.
공정/LUT가 바뀌면 숫자도 바뀌는 것이 정상이고, 그 변화를 보는 것이 이 스크립트의 목적이다.)
"""
import os, sys, math
ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # probes -> tests -> assets
sys.path.insert(0, ASSETS)
import numpy as np
import sizing_recipe as sr

d = np.load(os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"],
                                       d["ID_" + k], d["GM_" + k], d["GDS_" + k],
                                       d["CGG_" + k], W_ref=5e-6)
lut = {"n": mk("n"), "p": mk("p")}

L, VS, VDS = 0.35e-6, 0.0, 0.6

print("### 1. 분리형 gain = gm_id x V_A 가 얼마나 틀리는가 (nmos, L=0.35um, VDS=0.6)")
print("%7s %10s %9s %11s %13s" % ("gm_id", "gm/gds", "V_A(V)", "gain(dB)", "분리형가정(dB)"))
base = None
for g in (5, 10, 15, 20, 22, 26):
    r = lut["n"].gm_gds_ratio(g, L, VDS, VS)
    va = r / g
    if base is None:
        base = (g, r, va)
    # V_A가 상수라면 gain은 gm_id 비율만큼만 올라야 한다
    naive = 20 * math.log10(base[1] * (g / base[0]))
    print("%7.1f %10.2f %9.2f %11.2f %13.2f" % (g, r, va, 20 * math.log10(r), naive))
g0, r0, va0 = base
r1 = lut["n"].gm_gds_ratio(26, L, VDS, VS)
print("  -> gm_id %.0f→26 (%.2fx) 에서 실제 gain %.2f배, 분리형 예측 %.2f배"
      % (g0, 26 / g0, r1 / r0, 26 / g0))
print("  -> V_A가 %.2f→%.2f V로 %.2fx **감소**했기 때문. 분리형이 놓치는 dB = %.2f"
      % (va0, r1 / 26, va0 / (r1 / 26), 20 * math.log10(26 / g0) - 20 * math.log10(r1 / r0)))

print()
print("### 2. gm/gds 가 gm_id에 단조인가 (0.5 간격 정밀 스윕)")
prev = None
flips = []
xs = [5 + 0.5 * i for i in range(44)]
vals = []
for g in xs:
    try:
        v = lut["n"].gm_gds_ratio(g, L, VDS, VS)
    except Exception:
        break
    vals.append((g, v))
    if prev is not None and (v - prev[1]) * (prev[1] - (vals[-3][1] if len(vals) >= 3 else prev[1])) < 0:
        flips.append(g)
    prev = (g, v)
print("  스윕 범위 gm_id %.1f ~ %.1f (%d점)" % (vals[0][0], vals[-1][0], len(vals)))
peak = max(vals, key=lambda kv: kv[1])
print("  최대 gm/gds = %.2f @ gm_id=%.1f  (끝점 gm_id=%.1f 에서는 %.2f)"
      % (peak[1], peak[0], vals[-1][0], vals[-1][1]))
decreasing = [(a[0], a[1], b[1]) for a, b in zip(vals, vals[1:]) if b[1] < a[1]]
print("  gm_id를 올렸는데 gm/gds가 **떨어지는** 구간 %d개" % len(decreasing))
for a in decreasing[:8]:
    print("     gm_id %.1f→%.1f : %.2f → %.2f" % (a[0], a[0] + 0.5, a[1], a[2]))

print()
print("### 3. LUT 상한 근처인가 (gm_id 격자 도달 범위)")
for LL in (0.15e-6, 0.35e-6, 1.0e-6):
    hi = None
    for g in [40 - 0.2 * i for i in range(180)]:
        try:
            lut["n"].gm_gds_ratio(g, LL, VDS, VS)
            hi = g
            break
        except Exception:
            continue
    print("  L=%.2fum : 도달 가능한 최대 gm_id ~ %.1f" % (LL * 1e6, hi if hi else float("nan")))

print()
print("### 4. 면적 폭발이 실제인가 (weak inversion 전류밀도 확인, gm=75uS)")
for g in (18, 22, 24, 26):
    r = sr.size_transistor(75e-6, g, L, lut["n"], VDS, VS)
    idu = (75e-6 / g) / r.W          # A/m
    print("  gm_id=%2d : ID=%.3fuA  W=%9.2fum  전류밀도 IDu=%.4g A/um  면적=%.2fum2"
          % (g, 75e-6 / g * 1e6, r.W * 1e6, idu * 1e-6, r.W * L * 1e12))
