# -*- coding: utf-8 -*-
"""tol_v_loo.py 의 목표별 원자료(<tag>.targets.npz)를 분해한다 -- 최댓값이 어디서 나오나.

분류(상수 없이 곡선 자체로 정의):
  * 분지 점프: 목표 VGS_j는 실측 곡선의 rightmost 분지(정점 오른쪽)에 있는데, LOO 역산값이
    실측 곡선 정점 VGS보다 왼쪽(누설 지배 분지)에 떨어진 경우. 역산이 ValueError가 아니라
    다른 분지의 VGS를 조용히 돌려준 것.
  * 정점 근접도 r = g_j / g_peak (같은 곡선의 실측 gm/ID 최댓값 대비). r->1 이면 d(gm/ID)/dVGS -> 0
    이라 gm/ID -> VGS 역산의 조건수가 발산한다.
  * 예측 오차 = |g_loo(VGS_j) - g_j| / |dg/dVGS|_j (1차 근사) -- 조건수 설명력 확인용.

실행: python tol_v_breakdown.py [targets.npz] [lut.npz]
"""
import os
import sys

sys.dont_write_bytecode = True
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
TG = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "sky130_nfet_pfet_lut_sample.targets.npz")
LUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "skills/analog-gmid-design/assets/sky130_nfet_pfet_lut_sample.npz")
OUT = os.path.splitext(TG)[0].replace(".targets", "") + ".breakdown.txt"
open(OUT, "w", encoding="utf-8").close()


def emit(*p):
    s = " ".join(str(x) for x in p)
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")


sys.path.insert(0, HERE)
from tol_v_loo import load_arrays  # noqa: E402  (두 npz 형식 공통 로더)

z = np.load(TG)
t = z["targets"]
d = np.load(LUT)
arrs = load_arrays(LUT, d)
vgs = d["VGS"].astype(float)
L = d["L"].astype(float)
vds_g = d["VDS"].astype(float)
kind = t[:, 0].astype(int)
iL, iV, iS = t[:, 1].astype(int), t[:, 2].astype(int), t[:, 3].astype(int)
vj, g, es, eb, eid, br = t[:, 4], t[:, 5], t[:, 7], t[:, 11], t[:, 9], t[:, 10].astype(bool)

# 실측 곡선 정점(VGS, gm/ID)과 국소 기울기
vpeak = np.empty(len(t))
gpeak = np.empty(len(t))
slope = np.empty(len(t))
cache = {}
for n in range(len(t)):
    key = (kind[n], iL[n], iV[n], iS[n])
    if key not in cache:
        k = "n" if kind[n] == 0 else "p"
        idt = arrs[k]["ID"][iL[n], :, iV[n], iS[n]].astype(float)
        gmt = arrs[k]["GM"][iL[n], :, iV[n], iS[n]].astype(float)
        on = (idt > 1e-12) & (gmt > 0)
        gc = np.where(on, gmt / np.where(idt > 0, idt, 1), np.nan)
        ip = int(np.nanargmax(gc))
        cache[key] = (vgs[ip], gc[ip], np.gradient(np.nan_to_num(gc, nan=0.0), vgs))
    vp, gp, sl = cache[key]
    vpeak[n], gpeak[n] = vp, gp
    j = int(np.argmin(np.abs(vgs - vj[n])))
    slope[n] = sl[j]

valid = br & ~np.isnan(eb)
jump = valid & (es < vpeak)
emit("목표 %d, rightmost 분지 위 유효 %d, 그중 분지 점프 %d (%.3f%%)"
     % (len(t), valid.sum(), jump.sum(), 100 * jump.sum() / valid.sum()))
for kk in (0, 1):
    m = jump & (kind == kk)
    if m.any():
        emit("  %s 점프: n=%d, 오차 범위 %.0f~%.0f mV, VGS_j 범위 %.3f~%.3f, gm/ID %.2f~%.2f"
             % ("nmos" if kk == 0 else "pmos", m.sum(), eb[m].min() * 1e3, eb[m].max() * 1e3,
                vj[m].min(), vj[m].max(), g[m].min(), g[m].max()))
nj = valid & ~jump
emit()
emit("점프 제외 최댓값: " + " / ".join("%s %.2f mV" % ("nmos" if kk == 0 else "pmos", eb[nj & (kind == kk)].max() * 1e3)
                                    for kk in (0, 1) if (nj & (kind == kk)).any()))

emit()
emit("-- 정점 근접도 r = g_j/g_peak 별 err_vgs(점프 제외) [mV]: n / 중앙 / p99 / 최대 --")
rb = [(0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 0.9), (0.9, 0.95), (0.95, 0.99), (0.99, 1.0001)]
r = g / gpeak
for kk in (0, 1):
    for lo, hi in rb:
        m = nj & (kind == kk) & (r >= lo) & (r < hi)
        if not m.any():
            continue
        a = eb[m]
        emit("%-5s r[%.2f,%.2f) n=%-6d med=%7.3f p99=%8.2f max=%8.2f | gm/ID %.1f~%.1f"
             % ("nmos" if kk == 0 else "pmos", lo, min(hi, 1), m.sum(), np.median(a) * 1e3,
                np.percentile(a, 99) * 1e3, a.max() * 1e3, g[m].min(), g[m].max()))

# (kind,L,VDS) 셀 최댓값 -- r 상한별(정점 근접 영역을 빼면 tol_V가 어떻게 되나)
emit()
emit("-- (kind,L,VDS) 셀 최댓값의 분포: 점프 제외 + r < r_max 로 자른 경우 [mV] --")
emit("%-7s | %-8s %-8s %-8s %-8s %-8s | %-9s %-9s" % ("r_max", "p50", "p90", "p99", "max_n", "max_p", "셀수", "목표비율"))
for rmax in (1.0001, 0.99, 0.95, 0.9, 0.75):
    m = nj & (r < rmax)
    cells = {}
    for n in np.flatnonzero(m):
        key = (kind[n], iL[n], iV[n])
        if eb[n] > cells.get(key, -1):
            cells[key] = eb[n]
    cv = np.array(list(cells.values()))
    mn = max([v for kk, v in cells.items() if kk[0] == 0] or [float("nan")])
    mp = max([v for kk, v in cells.items() if kk[0] == 1] or [float("nan")])
    emit("%-7s | %-8.2f %-8.2f %-8.2f %-8.2f %-8.2f | %-9d %.3f"
         % ("%.4g" % rmax, np.percentile(cv, 50) * 1e3, np.percentile(cv, 90) * 1e3,
            np.percentile(cv, 99) * 1e3, mn * 1e3, mp * 1e3, len(cv), m.sum() / nj.sum()))

# 1차 예측(조건수) 설명력
emit()
pred = np.full(len(t), np.nan)
with np.errstate(divide="ignore", invalid="ignore"):
    # g_loo(VGS_j)는 targets에 없으므로 err_id_eq 대신 err_vgs*|slope| = |Δg| 를 역으로 확인
    dg = eb * np.abs(slope)
emit("|Δ(gm/ID)| = err_vgs x |dg/dVGS| (점프 제외) 중앙 %.4f, p99 %.3f  -- 오차가 큰 곳이 기울기 0 근처인지 확인"
     % (np.nanmedian(dg[nj]), np.nanpercentile(dg[nj], 99)))
big = nj & (eb > np.percentile(eb[nj], 99))
emit("err_vgs 상위 1%%(> %.1f mV) 목표의 r 중앙 %.3f, |slope| 중앙 %.2f /V (전체 |slope| 중앙 %.2f /V)"
     % (np.percentile(eb[nj], 99) * 1e3, np.median(r[big]), np.median(np.abs(slope[big])),
        np.median(np.abs(slope[nj]))))

# 상위 20개
emit()
emit("-- 점프 제외 상위 15 --")
emit("kind L(um)  VDS    VS   VGS_j  gm/ID   g_peak  r      err(mV) slope(/V)")
for n in np.argsort(-np.where(nj, eb, -1))[:15]:
    emit("%-4s %-6.3f %-6.4f %-4.1f %-6.4f %-7.3f %-7.3f %-6.4f %-7.2f %-8.2f"
         % ("n" if kind[n] == 0 else "p", L[iL[n]] * 1e6, vds_g[iV[n]], float(d["VS"][iS[n]]), vj[n], g[n],
            gpeak[n], r[n], eb[n] * 1e3, slope[n]))
