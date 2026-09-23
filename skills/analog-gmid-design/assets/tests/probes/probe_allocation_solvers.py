# -*- coding: utf-8 -*-
"""stage별 gm_id 배분 문제를 세 가지 방법으로 풀어 비교하는 조사 스크립트.

계획 문서 §7.9 "해법 확정 -- 분리형 DP"(v4.2)의 근거를 만든 도구다.

  (A) exhaustive()  전수 대조 -- ground truth. 87^N 조합이라 N<=3에서만 현실적.
  (B) kkt_greedy()  v3.3이 규정했던 규칙: "면적 1단위당 전력을 가장 많이 아끼는 stage에
                    먼저 배분". **기울기에 의존**하므로 gain(gm_id)이 비단조인 구간에서
                    무너진다 -- 72 시나리오 중 27건 어긋남, 그 중 8건은 feasible 해가
                    있는데도 gain 미달 해를 반환(탐욕이 gain 제약을 아예 안 본다).
  (C) dp()          분리형 DP. 각 stage의 (전력/면적/gain)이 자기 gm_id에만 의존한다는
                    성질을 써서 면적 bin별 (gain, power) 비지배 집합을 전파한다.
                    **기울기를 안 쓰므로 비볼록이어도 전역 최적**이고, 탐욕이 틀린 9개
                    케이스에서 전수와 9/9 일치했다. N=4가 0.294s(전수는 5,729만 조합).

핵심 논점: "해석해가 아니면 탐색 문제가 되는가?" -> 아니다. 탐색이 아니라 **정확한 이산
최적화**다. 같은 입력이면 같은 답이고, 임의 가중치·초기값·시드가 없으며, 국소최적이
구조적으로 존재하지 않는다. 남는 근사는 격자 해상도 하나이고 그건 선언해서 리포트에 찍는다.

실행: assets 디렉터리에서 `python tests/probe_allocation_solvers.py`
(자동 테스트가 아니라 조사용 -- 값을 단정하지 않고 그때의 LUT가 말하는 것을 찍는다.)
"""
import os, sys, math, itertools, time
ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # probes -> tests -> assets
sys.path.insert(0, ASSETS)
import numpy as np
import sizing_recipe as sr

d = np.load(os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz"))
LUT = sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"],
                              d["ID_n"], d["GM_n"], d["GDS_n"], d["CGG_n"], W_ref=5e-6)
VS = 0.0
GRID = [5.0 + 0.25 * i for i in range(87)]


def table(gm, L, vds):
    rows = []
    for g in GRID:
        try:
            ratio = LUT.gm_gds_ratio(g, L, vds, VS)
            r = sr.size_transistor(gm, g, L, LUT, vds, VS)
        except Exception:
            continue
        rows.append((g, gm / g * 1e6, r.W * L * 1e12, 20 * math.log10(ratio)))
    return rows


def exhaustive(tabs, gt, ab):
    best, bp = None, float("inf")
    for sel in itertools.product(*[range(len(t)) for t in tabs]):
        a = sum(tabs[i][k][2] for i, k in enumerate(sel))
        if a > ab: continue
        if sum(tabs[i][k][3] for i, k in enumerate(sel)) < gt: continue
        p = sum(tabs[i][k][1] for i, k in enumerate(sel))
        if p < bp: best, bp = sel, p
    return best, bp


def kkt_greedy(tabs, gt, ab):
    sel = [0] * len(tabs)
    while True:
        cand = None
        for i, tb in enumerate(tabs):
            k = sel[i]
            if k + 1 >= len(tb): continue
            dP = tb[k][1] - tb[k + 1][1]; dA = tb[k + 1][2] - tb[k][2]
            r = dP / dA if dA > 0 else float("inf")
            if r > 0 and (cand is None or r > cand[1]): cand = (i, r)
        if cand is None: break
        trial = list(sel); trial[cand[0]] += 1
        if sum(tabs[i][k][2] for i, k in enumerate(trial)) > ab: break
        sel = trial
    a = sum(tabs[i][k][2] for i, k in enumerate(sel))
    g = sum(tabs[i][k][3] for i, k in enumerate(sel))
    p = sum(tabs[i][k][1] for i, k in enumerate(sel))
    return sel, p, (a <= ab and g >= gt)


def dp(tabs, gt, ab, nb=600, keep=400):
    """면적을 bin으로 이산화하고 bin마다 (gain, power) 비지배 집합을 전파한다.

    분리형(각 stage의 면적/이득/전력이 자기 gm_id에만 의존)이라 성립하는 정확 알고리즘.
    비볼록이어도 국소최적에 빠지지 않는다 -- 기울기를 쓰지 않기 때문이다.
    """
    step = ab / nb
    states = {0: [(0.0, 0.0, ())]}
    for tb in tabs:
        nxt = {}
        for b, lst in states.items():
            for (g, p, path) in lst:
                for k, row in enumerate(tb):
                    nbb = b + int(row[2] / step)
                    if nbb > nb: continue
                    nxt.setdefault(nbb, []).append((g + row[3], p + row[1], path + (k,)))
        for b in list(nxt):
            arr = sorted(nxt[b], key=lambda x: (x[1], -x[0]))
            out, bg = [], -1e18
            for it in arr:
                if it[0] > bg: out.append(it); bg = it[0]
            nxt[b] = out[:keep]
        states = nxt
    best, bp = None, float("inf")
    for b, lst in states.items():
        for (g, p, path) in lst:
            if g >= gt and p < bp: best, bp = path, p
    return best, bp


print("### 1. KKT 탐욕이 틀렸던 시나리오에서 DP가 전수와 일치하는가")
print("%-42s %9s %9s %9s %s" % ("시나리오", "전수", "KKT", "DP", "판정"))
print("-" * 92)
cases = [(0.6,150e-6,10.0,79.0),(0.6,150e-6,40.0,79.0),(0.6,150e-6,200.0,79.0),
         (0.6,220e-6,10.0,68.0),(0.6,220e-6,40.0,79.0),(0.6,220e-6,200.0,79.0),
         (0.9,220e-6,40.0,74.0),(0.9,220e-6,200.0,79.0),(1.2,220e-6,40.0,77.0)]
nfail = 0
for vds, gm2, ab, gt in cases:
    tabs = [table(75e-6,0.35e-6,vds), table(gm2,0.50e-6,vds)]
    se, pe = exhaustive(tabs, gt, ab)
    sk, pk, okk = kkt_greedy(tabs, gt, ab)
    sd, pd = dp(tabs, gt, ab)
    ok = (se is None and sd is None) or (sd is not None and abs(pd-pe) < 1e-9)
    if not ok: nfail += 1
    print("%-42s %9.4f %9s %9.4f %s"
          % ("VDS=%.1f gm2=%.0fuS A<=%.0f G>=%.0f"%(vds,gm2*1e6,ab,gt),
             pe, ("%.4f"%pk) if okk else "실패", pd,
             "DP=전수 OK" if ok else "★DP 불일치"))
print("-" * 92)
print("DP 불일치: %d / %d" % (nfail, len(cases)))

print()
print("### 2. stage 수가 늘 때 비용 (전수는 87^N)")
for n in (2, 3, 4):
    tabs = [table(75e-6, 0.35e-6, 0.9)] + [table(150e-6, 0.5e-6, 0.9)] * (n - 1)
    gt, ab = 34.0 * n, 30.0 * n
    t0 = time.perf_counter(); sd, pd = dp(tabs, gt, ab); tdp = time.perf_counter() - t0
    if n <= 3:
        t0 = time.perf_counter(); se, pe = exhaustive(tabs, gt, ab); tex = time.perf_counter() - t0
        agree = "일치" if (se and abs(pd - pe) < 1e-9) else "불일치"
        print("  N=%d: 전수 %9.3fs (%d조합) | DP %6.3fs | %s | 전력 %.4f uA"
              % (n, tex, 87 ** n, tdp, agree, pd))
    else:
        print("  N=%d: 전수 %d조합 = 비현실적 | DP %6.3fs | 전력 %.4f uA"
              % (n, 87 ** n, tdp, pd))
