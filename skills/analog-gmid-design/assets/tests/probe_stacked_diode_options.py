# -*- coding: utf-8 -*-
"""적층 diode 스택(`biasgen_vom_battery_a` = M11a/M11b/M12)의 **선택지를 계산**한다
(2026-09-09, B24 후속).

## 왜 이 스택인가

B9(vsb를 노드전압에서 유도)를 고치자 `M11b`가 **W=6342µm**를 요구해 파일럿이 성립하지
않았다. 그 전까지는 `vsb=0.0`이라 문제가 안 보였을 뿐이다.

구조를 보면 이유가 분명하다 -- 이 스택은 **적층 diode**다:

    vdd --> M11a (PMOS diode, source=vdd)      --> N11a11b
        --> M11b (PMOS diode, source=N11a11b)  --> N11b
        --> M12  (NMOS,       source=gnd)      --> gnd

    KVL:  v_a + v_b + v_12 = vdd = 1.8V

둘 다 diode-connected라 `VDS = VGS`이고 W는 그 값이 정한다. 그리고 결정적으로:

    M11a의 vsb = vdd - V(vdd)     = 0          (소스가 레일)
    M11b의 vsb = vdd - V(N11a11b) = **v_a**    (소스가 M11a의 드레인)

즉 **M11a가 헤드룸을 많이 가질수록 M11b의 바디효과가 커진다**. Vth가 올라가 같은 VGS에서
전류밀도가 떨어지고, 그래서 M11b가 더 넓어져야 한다. 이 결합이 B9 이전에는 `vsb=0.0`으로
지워져 있었다.

## 계산하는 선택지

자유도 셋을 훑는다(각각이 실제로 바꿀 수 있는 것과 대응한다):

    v_a, v_b   스택 예산 배분      <- 헤드룸 배분기가 정하는 것(§7.9)
    L          채널길이            <- 지금은 `L_role="mirror"` = L_min*2.5 = 0.375um 하드코딩
    k_ID       전류 배율           <- theta `r_diode_M11a`(bounds 0.02~0.15, 현재 0.085)

각 조합에서 세 소자의 W를 구해 `W_bounds(1~200um)` 안인지, M12가 포화인지 본다.
**아무것도 고치지 않는다 -- 표만 만든다.**

실행: assets 디렉터리에서 `python tests/probe_stacked_diode_options.py`
"""
import sys
import os
import json
import math

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
import numpy as np
import sizing_recipe as sr

_RESULT = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first = [True]


def emit(*p):
    line = " ".join(str(x) for x in p)
    print(line, flush=True)
    mode = "w" if _first[0] else "a"
    _first[0] = False
    with open(_RESULT, mode, encoding="utf-8") as f:
        f.write(line + "\n")


VDD = 1.8
W_LO, W_HI = 1e-6, 200e-6
d = np.load(os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                       d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                       W_ref=5e-6, SID_1F=d["SID_1F_" + k])
NM, PM = mk("n"), mk("p")

# 현 동작점(2026-09-09 실측, tests/probe_node_voltage_audit.py와 같은 theta).
# ID는 theta `r_diode_M11a`가 정하고 세 소자가 같은 전류를 흘린다(직렬).
ID0 = 0.2598e-6          # A
L0 = 0.375e-6            # m  (L_role="mirror" = L_min*2.5)
VA0, VB0 = 0.6750, 0.6750
MIN_VDS_M12 = 0.3        # min_vds_by_role["mirror"]


def idu(lut, vgs, L, vds, vsb):
    return math.exp(lut._query(lut._log_ID, L, vgs, vds, vsb)) * L / lut._w_ref_effective(L)


def widths(v_a, v_b, L, ID):
    """(W_a, W_b, v_12) -- 실패하면 None. M11b의 vsb는 v_a다(적층 바디효과)."""
    v12 = VDD - v_a - v_b
    if v12 < MIN_VDS_M12:
        return None
    try:
        wa = L * ID / idu(PM, v_a, L, v_a, 0.0)
        wb = L * ID / idu(PM, v_b, L, v_b, v_a)
    except Exception:
        return None
    if not (wa > 0 and wb > 0):
        return None
    return wa, wb, v12


emit("=" * 100)
emit("0. 현 동작점에서 무엇이 터지나  (B9 적용 = vsb를 물리대로)")
emit("=" * 100)
emit("")
r = widths(VA0, VB0, L0, ID0)
emit(f"  L={L0*1e6:.4f}um  ID={ID0*1e6:.4f}uA  v_a={VA0:.4f}  v_b={VB0:.4f}")
if r:
    wa, wb, v12 = r
    emit(f"    M11a  vsb=0.0000  W={wa*1e6:>10.2f}um   {'OK' if wa <= W_HI else '★상한 초과'}")
    emit(f"    M11b  vsb={VA0:.4f}  W={wb*1e6:>10.2f}um   {'OK' if wb <= W_HI else '★상한 초과'}")
    emit(f"    M12   vds={v12:.4f}V")
    emit("")
    emit(f"  -> M11b가 M11a보다 {wb/wa:.1f}배 넓어야 한다. 둘은 같은 전류·같은 L·같은 VGS인데,")
    emit(f"     차이는 오직 **바디효과**(vsb 0 vs {VA0:.4f}V)다.")

# ── 1. 배분(v_a, v_b) 축 ─────────────────────────────────────────────────────
emit("")
emit("=" * 100)
emit("1. 스택 예산 배분만 바꾼다  (L, ID는 현재값 고정)")
emit("=" * 100)
emit("")
emit("  가로 v_b / 세로 v_a. 칸은 max(W_a, W_b) in um. * = 셋 다 성립(W 1~200um, M12 포화여유)")
grid = [float(v) for v in PM.VDS_grid if 0.15 <= v <= 1.2]
emit("")
emit("  " + f"{'v_a\\v_b':>9}" + "".join(f"{v:>9.3f}" for v in grid[::2]))
emit("  " + "-" * (9 + 9 * len(grid[::2])))
feas_split = []
for va in grid[::2]:
    cells = []
    for vb in grid[::2]:
        rr = widths(va, vb, L0, ID0)
        if rr is None:
            cells.append(f"{'--':>9}")
            continue
        wa, wb, v12 = rr
        wmax = max(wa, wb)
        ok = (W_LO <= wa <= W_HI) and (W_LO <= wb <= W_HI)
        if ok:
            feas_split.append((va, vb, wa, wb, v12))
        txt = f"{wmax*1e6:.1f}" if wmax * 1e6 < 1e5 else f"{wmax*1e6:.0e}"
        cells.append(f"{(txt + ('*' if ok else '')):>9}")
    emit(f"  {va:>9.3f}" + "".join(cells))
emit("")
emit(f"  -> 배분만으로 성립하는 조합 {len(feas_split)}개")
if feas_split:
    feas_split.sort(key=lambda x: max(x[2], x[3]))
    emit(f"     {'v_a':>7}{'v_b':>8}{'v_12':>8}{'W_a(um)':>11}{'W_b(um)':>11}")
    emit("     " + "-" * 45)
    for va, vb, wa, wb, v12 in feas_split[:10]:
        emit(f"     {va:>7.3f}{vb:>8.3f}{v12:>8.3f}{wa*1e6:>11.3f}{wb*1e6:>11.3f}")

# ── 2. L 축 ──────────────────────────────────────────────────────────────────
emit("")
emit("=" * 100)
emit("2. L을 바꾸면  (배분은 현재값 v_a=v_b=0.675 고정, ID 현재값)")
emit("=" * 100)
emit("")
emit(f"  {'L(um)':>9}{'W_a(um)':>12}{'W_b(um)':>12}{'판정':>10}   (L_role: mirror=2.5x, bias_replica=1.2x)")
emit("  " + "-" * 55)
for L in [float(v) for v in PM.L_grid]:
    rr = widths(VA0, VB0, L, ID0)
    if rr is None:
        emit(f"  {L*1e6:>9.4f}{'--':>12}{'--':>12}{'실패':>10}")
        continue
    wa, wb, _ = rr
    ok = (W_LO <= wa <= W_HI) and (W_LO <= wb <= W_HI)
    emit(f"  {L*1e6:>9.4f}{wa*1e6:>12.3f}{wb*1e6:>12.3f}{('OK' if ok else '★초과'):>10}")

# ── 3. 전류 축 ───────────────────────────────────────────────────────────────
emit("")
emit("=" * 100)
emit("3. 전류를 바꾸면  (theta r_diode_M11a, bounds 0.02~0.15 / 현재 0.085)")
emit("=" * 100)
emit("")
emit("  W는 ID에 비례하므로 배율이 그대로 W 배율이다. 현재 조합에서:")
emit(f"  {'k_ID':>8}{'r_diode':>10}{'ID(uA)':>10}{'W_a(um)':>12}{'W_b(um)':>12}{'판정':>10}")
emit("  " + "-" * 62)
for k in (0.235, 0.35, 0.5, 0.75, 1.0, 1.5, 1.765):
    rr = widths(VA0, VB0, L0, ID0 * k)
    if rr is None:
        continue
    wa, wb, _ = rr
    ok = (W_LO <= wa <= W_HI) and (W_LO <= wb <= W_HI)
    emit(f"  {k:>8.3f}{0.085*k:>10.4f}{ID0*k*1e6:>10.4f}"
         f"{wa*1e6:>12.3f}{wb*1e6:>12.3f}{('OK' if ok else '★초과'):>10}")

# ── 4. 세 축 교차 -- 성립하는 최소 변경 ──────────────────────────────────────
emit("")
emit("=" * 100)
emit("4. 세 축 교차 -- 현재값에서 **가장 적게 바꿔** 성립하는 조합")
emit("=" * 100)
emit("")
cands = []
for L in [float(v) for v in PM.L_grid]:
    for k in (0.235, 0.35, 0.5, 0.75, 1.0, 1.5, 1.765):
        for va in grid:
            for vb in grid:
                rr = widths(va, vb, L, ID0 * k)
                if rr is None:
                    continue
                wa, wb, v12 = rr
                if not (W_LO <= wa <= W_HI and W_LO <= wb <= W_HI):
                    continue
                # "변경량" -- 각 축을 현재값 대비 상대변화로 재고 합친다
                cost = (abs(va - VA0) + abs(vb - VB0)) / 0.0375 + \
                       abs(math.log(L / L0)) / math.log(2.5) + abs(math.log(k)) / math.log(2)
                cands.append((cost, L, k, va, vb, wa, wb, v12))
cands.sort(key=lambda x: x[0])
emit(f"  성립 조합 {len(cands)}개. 변경량이 작은 순 12개:")
emit(f"  {'변경량':>7}{'L(um)':>9}{'k_ID':>8}{'v_a':>7}{'v_b':>7}{'v_12':>7}"
     f"{'W_a(um)':>10}{'W_b(um)':>10}   바꿔야 하는 것")
emit("  " + "-" * 96)
for cost, L, k, va, vb, wa, wb, v12 in cands[:12]:
    ch = []
    if abs(L - L0) > 1e-12:
        ch.append(f"L {L0*1e6:.3f}->{L*1e6:.3f}um")
    if abs(k - 1.0) > 1e-9:
        ch.append(f"전류 x{k:.2f}")
    if abs(va - VA0) > 1e-9 or abs(vb - VB0) > 1e-9:
        ch.append(f"배분 {VA0:.3f}/{VB0:.3f}->{va:.3f}/{vb:.3f}")
    emit(f"  {cost:>7.2f}{L*1e6:>9.4f}{k:>8.3f}{va:>7.3f}{vb:>7.3f}{v12:>7.3f}"
         f"{wa*1e6:>10.3f}{wb*1e6:>10.3f}   {', '.join(ch) or '(변경 없음)'}")

emit("")
emit("완료. 결과 파일:", _RESULT)
