# -*- coding: utf-8 -*-
"""`_solve_vgs()`의 **단조 전제**가 실제 LUT에서 성립하는지 재고, 수정 후에는
그 수정이 유지되는지 지키는 도구(2026-09-09, B19 설계공간 스윕 중 발견 -> 당일 해소).

## 상태: B20은 **해소됐다**(2026-09-09). 이 스크립트는 이제 회귀 감시가 본체다.

`_solve_vgs()`는 **rightmost root**(목표를 품는 가장 오른쪽 구간에서만 보간)로 다시
쓰였다. §4가 LUT 정의역을 훑으며 엔진과 독립 참조 구현을 대조한다 -- 마지막 실행에서
nmos 16,186건 / pmos 16,181건 **전부 일치**(실패 조건까지 동일)했다. §1/§1b는 왜 그
수정이 필요했는지를 남기는 측정이라 그대로 둔다.

## 무엇이 문제였나

`SemiEmpiricalGmIdLUT._solve_vgs()`는 docstring에 **"gm/ID는 VGS에 단조감소"**라고
전제를 적어놓고 이렇게 역보간했다:

    order = np.argsort(gm_id_vals)                       # 비단조면 두 branch가 뒤섞인다
    result = np.interp(gm_id, gm_id_sorted, vgs_sorted)

gm/ID가 VGS에 단조감소이면 `argsort`는 단순히 배열을 뒤집는 것이라 올바르다. 그러나
**비단조이면 서로 다른 branch의 VGS가 정렬 과정에서 섞여**, `np.interp`가 VGS 축에서
인접하지도 않은 두 점 사이를 보간한다 -- 물리적으로 아무 의미가 없는 VGS가 나온다.

이 함수는 `gm_id_to_id_density()`(=`W = L*ID/IDu`의 분모)와 `gm_gds_ratio()`/`fT()`/
`cgg_absolute()`가 전부 첫 줄에서 호출한다. 즉 **모든 W 계산의 뿌리**다.

## 실측으로 확인된 비단조 (raw LUT, 보간 없음)

    PMOS  L=0.15um  VDS=0.9000  VS=0
        VGS 0.4125 -> gm/ID 14.192
        VGS 0.4500 -> gm/ID 14.237   (오름)
        ...
        VGS 0.6375 -> gm/ID 15.338   (정점)
        VGS 0.6750 -> gm/ID 15.079   (꺾임)
        VGS 0.9750 -> gm/ID  6.354

ID 자체는 단조증가라(6.5e-8 -> 7.7e-5) 데이터가 깨진 게 아니다. 저전압 쪽에서 gm/ID가
낮은 것은 누설이 섞여 gm이 상대적으로 작기 때문으로 보이며, 어느 쪽이든 **LUT가 실제로
비단조라는 사실**은 남는다.

## 측정 결과 (2026-09-09)

**NMOS는 전 구간 단조라 무사하다. PMOS만 걸린다.**

`VDS>=0.15`인 격자점 2700개 중 비단조 2032개(75.3%). 다만 그 숫자만 보면 과장된다 --
상승 대부분은 누설이 지배하는 약반전 꼬리(gm/ID 26~31)라 엔진이 실제로 고르는
`gm_id_grid`(4~24) 밖이다. **탐색범위와 겹치는 것만** 세면 1446개(53.6%)이고, 겹칠 때는
중앙값 폭이 **20.0** -- 즉 겹치면 탐색범위가 통째로 이중값이 된다.

위험은 두 축에 몰려 있다:

    vsb=0.000  43.3%      L=0.15~0.25um  비단조지만 대역이 gm_id 26~29라 탐색범위 밖(무해)
    vsb=0.200  63.9%      L=0.30~1.00um  **완전히 단조**  <- 파일럿 theta bounds가 여기다
    vsb=0.400  83.3%      L=1.50um       [15.87, 31.13]  ★탐색범위와 겹침
    vsb=0.600  90.0%      L=2.50um       [ 7.51, 31.37]  ★
    vsb=0.800  95.7%      L=4.00um       [ 6.12, 30.90]  ★

즉 **바디효과가 걸린 소자**와 **긴 L(>=1.5um)**이 위험지대다. 파일럿의 theta bounds가
`[0.15, 1.0]um`이고 대부분의 소자가 vsb=0이라 지금은 거의 안 물리지만, 실제로 **2소자가
물렸다**: `M18a`/`M9a`(vsb=0.8003, vds=0.0587)에서 W가 1.0177um으로 나오는데 강반전
branch의 올바른 해는 0.4306um -- **2.36배 틀렸다**. 오류 없이 조용히.

주의: B9(vsb 오산출)이 아직 안 고쳐져 있으므로 현재 vsb 값 자체가 신뢰할 수 없다.
B9를 고치면 vsb가 커지는 소자가 늘어 이 결함에 **더 많이** 노출될 수 있다.

이 스크립트가 재는 것:

  1 / 1b  LUT 정의역 전체에서 비단조인 (L,VDS,VS) 동작점이 몇 %인가, 그중 탐색범위와
          겹치는 건 몇 %인가, 위험이 vsb/L 어디에 몰려 있는가 (수정의 근거 -- 보존)
  2 / 3   파일럿 소자가 그 대역에 걸리는가, 걸리면 W가 얼마나 틀리는가.
          `probe_mirror_design_space.py`가 만든 사이징 캐시가 있어야 돈다(없으면 건너뛴다).
          **수정 후에는 정의상 0건**이라, 남겨둔 것은 이력과 재현용이다.
  4       ★ **회귀 감시(본체)** -- 엔진의 `_solve_vgs()`가 독립 계산한 rightmost root와
          일치하는가. 사이징 캐시가 필요 없고, 하나라도 어긋나면 회귀다.

실행: assets 디렉터리에서 `python tests/probe_gm_id_monotonicity.py`
"""
import sys
import os
import json
import math

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
import numpy as np
import sizing_recipe as sr

_RESULT_PATH = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first_emit = [True]


def emit(*parts):
    line = " ".join(str(p) for p in parts)
    print(line, flush=True)
    mode = "w" if _first_emit[0] else "a"
    _first_emit[0] = False
    with open(_RESULT_PATH, mode, encoding="utf-8") as _f:
        _f.write(line + "\n")


d = np.load(os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                       d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                       W_ref=5e-6, SID_1F=d["SID_1F_" + k])
LUT = {"nmos": mk("n"), "pmos": mk("p")}


def curve_stats(lut, L, vds, vsb):
    """(L,vds,vsb)의 gm/ID 곡선이 VGS에 단조감소인지, 아니면 이중값 대역이 어디인지."""
    _, g = lut._gm_id_curve(L, vds, vsb)
    g = np.asarray(g, dtype=float)
    if not np.all(np.isfinite(g)):
        return None
    dg = np.diff(g)
    n_up = int(np.sum(dg > 0))
    if n_up == 0:
        return {"mono": True, "n_up": 0, "band": None, "peak": float(g.max())}
    # 이중값 대역: 상승 구간의 정점과, 그 정점 이전 최솟값 사이
    i_peak = int(np.argmax(g))
    lo = float(np.min(g[:i_peak + 1]))
    hi = float(g[i_peak])
    return {"mono": False, "n_up": n_up, "band": (lo, hi), "peak": hi,
            "vgs_peak": float(lut.VGS_grid[i_peak])}


# ── 1. LUT 정의역 전체 ────────────────────────────────────────────────────────
emit("=" * 96)
emit("1. LUT 정의역 전체에서 gm/ID 곡선이 VGS에 단조감소인가")
emit("=" * 96)
emit("")
emit("  격자점 (L x VDS x VS) 전수. VDS=0 근처는 물리적으로 사이징 대상이 아니므로")
emit("  VDS >= 0.15V만 센다.")
emit("")
emit("  ★ '비단조'만 세면 과장된다 -- 대부분의 상승은 누설이 지배하는 약반전 꼬리에 있고,")
emit("     엔진이 실제로 고르는 gm_id는 `gm_id_grid`(4~24) 안이다. 그래서 **탐색범위와")
emit("     겹치는 이중값 대역**을 따로 센다. 이게 실제로 무는 비율이다.")
emit("")
SEARCH_LO, SEARCH_HI = 4.0, 24.0
emit(f"  {'kind':<7}{'동작점':>9}{'비단조':>9}{'비율':>8}"
     f"{'탐색범위와겹침':>15}{'비율':>8}{'대역폭 중앙':>12}{'최대대역':>22}")
emit("  " + "-" * 82)

DOMAIN = {}
for kind, lut in LUT.items():
    tot = bad = overlap = 0
    widths = []
    worst = None
    rows = []
    for L in lut.L_grid:
        for vds in lut.VDS_grid:
            if vds < 0.15:
                continue
            for vsb in lut.VS_grid:
                st = curve_stats(lut, float(L), float(vds), float(vsb))
                if st is None:
                    continue
                tot += 1
                if st["mono"]:
                    continue
                bad += 1
                lo, hi = st["band"]
                rows.append((float(L), float(vds), float(vsb), st))
                # 탐색범위와 실제로 겹치는가
                ov_lo, ov_hi = max(lo, SEARCH_LO), min(hi, SEARCH_HI)
                if ov_hi > ov_lo:
                    overlap += 1
                    widths.append(ov_hi - ov_lo)
                    if worst is None or (ov_hi - ov_lo) > worst[0]:
                        worst = (ov_hi - ov_lo, float(L), float(vds), float(vsb), lo, hi)
    DOMAIN[kind] = rows
    med = f"{float(np.median(widths)):.3f}" if widths else "--"
    wtxt = (f"[{worst[4]:.2f},{worst[5]:.2f}] @L={worst[1]*1e6:.2f}um,VDS={worst[2]:.2f}"
            if worst else "(없음)")
    emit(f"  {kind:<7}{tot:>9d}{bad:>9d}{bad/max(tot,1)*100:>7.1f}%"
         f"{overlap:>15d}{overlap/max(tot,1)*100:>7.1f}%{med:>12}{wtxt:>22}")

# ── 1b. 어디가 위험한가 -- vsb와 L로 쪼갠다 ───────────────────────────────────
emit("")
emit("-" * 96)
emit("1b. 위험이 어디에 몰려 있나  (pmos만 -- nmos는 전 구간 단조)")
emit("-" * 96)
lut = LUT["pmos"]

emit("")
emit("  (가) vsb(바디효과)별  --  VDS>=0.15의 모든 (L,VDS)")
emit(f"      {'vsb(V)':>8}{'비단조':>10}{'전체':>8}{'비율':>9}")
emit("      " + "-" * 35)
for vsb in lut.VS_grid:
    tot = bad = 0
    for L in lut.L_grid:
        for vds in lut.VDS_grid:
            if vds < 0.15:
                continue
            st = curve_stats(lut, float(L), float(vds), float(vsb))
            if st is None:
                continue
            tot += 1
            bad += 0 if st["mono"] else 1
    emit(f"      {float(vsb):>8.3f}{bad:>10d}{tot:>8d}{bad/max(tot,1)*100:>8.1f}%")

emit("")
emit("  (나) L 앵커별 (vsb=0)  --  '겹침'은 이중값 대역이 탐색범위 [4,24]와 겹치는 VDS 수")
emit(f"      {'L(um)':>9}{'비단조VDS':>11}{'겹침':>7}{'대표 대역':>22}")
emit("      " + "-" * 49)
for L in lut.L_grid:
    bad = ov = 0
    rep = None
    for vds in lut.VDS_grid:
        if vds < 0.15:
            continue
        st = curve_stats(lut, float(L), float(vds), 0.0)
        if st is None or st["mono"]:
            continue
        bad += 1
        lo, hi = st["band"]
        if min(hi, SEARCH_HI) > max(lo, SEARCH_LO):
            ov += 1
        if rep is None:
            rep = (lo, hi)
    tag = f"[{rep[0]:.2f}, {rep[1]:.2f}]" if rep else "(단조)"
    mark = "  ★위험" if ov else ""
    emit(f"      {float(L)*1e6:>9.4f}{bad:>11d}{ov:>7d}{tag:>22}{mark}")

# ── 2. 파일럿 소자가 그 대역에 걸리는가 ───────────────────────────────────────
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "probe_mirror_design_space.sizing_cache.json")
emit("")
emit("=" * 96)
emit("2. 파일럿 51소자 중 자기 gm_id가 이중값 대역 안에 있는 소자")
emit("=" * 96)

if not os.path.exists(CACHE):
    emit("  (사이징 캐시가 없다 -- tests/probe_mirror_design_space.py를 먼저 실행할 것)")
    sized = {}
else:
    sized = json.load(open(CACHE, encoding="utf-8"))

TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
trs, _meta = sr.load_topology(TOPO)
kind_of = {t.name: t.kind for t in trs}


def strong_branch_vgs(lut, gm_id, L, vds, vsb):
    """강반전 쪽(정점 오른쪽, 단조감소 구간)에서 gm_id를 만족하는 VGS -- 물리적으로 옳은 해."""
    _, g = lut._gm_id_curve(L, vds, vsb)
    g = np.asarray(g, dtype=float)
    i_peak = int(np.argmax(g))
    gg, vv = g[i_peak:], np.asarray(lut.VGS_grid, dtype=float)[i_peak:]
    if gm_id > gg[0] or gm_id < gg[-1]:
        return None
    return float(np.interp(gm_id, gg[::-1], vv[::-1]))


def idu_at_vgs(lut, vgs, L, vds, vsb):
    raw = math.exp(lut._query(lut._log_ID, L, vgs, vds, vsb))
    return raw * L / lut._w_ref_effective(L)


emit("")
emit(f"  {'소자':<9}{'kind':<6}{'gm_id':>8}{'L(um)':>8}{'vds':>7}{'vsb':>7}"
     f"{'대역':>18}{'걸림':>7}")
emit("  " + "-" * 72)
hits = []
for name in sorted(sized.keys()):
    e = sized[name]
    kind = kind_of.get(name)
    if kind not in LUT:
        continue
    try:
        L, vds, vsb = float(e["L"]), float(e["vds"]), float(e.get("vsb", 0.0))
        gm_id = float(e["gm_id"])
    except (KeyError, TypeError, ValueError):
        continue
    st = curve_stats(LUT[kind], L, vds, vsb)
    if st is None:
        continue
    if st["mono"]:
        continue
    lo, hi = st["band"]
    inside = lo <= gm_id <= hi
    if inside:
        hits.append((name, kind, gm_id, L, vds, vsb, lo, hi))
    emit(f"  {name:<9}{kind:<6}{gm_id:>8.3f}{L*1e6:>8.4f}{vds:>7.4f}{vsb:>7.4f}"
         f"   [{lo:>6.3f},{hi:>6.3f}]{'★예' if inside else '아니오':>7}")

emit("")
emit(f"  -> 비단조 동작점에 놓인 소자 {len(hits)}개가 실제로 이중값 대역 안에 있다.")

# ── 3. W가 얼마나 틀리는가 ────────────────────────────────────────────────────
emit("")
emit("=" * 96)
emit("3. 걸린 소자의 W가 얼마나 틀리는가  --  엔진 argsort 해 vs 강반전 branch 해")
emit("=" * 96)
if not hits:
    emit("")
    emit("  걸린 소자가 없다 -- 현 동작점에서는 이 결함이 W를 틀리게 만들지 않는다.")
    emit("  (다만 탐색이 이 대역을 지나가면 언제든 발동한다. §1의 비율 참고.)")
else:
    emit("")
    emit(f"  {'소자':<9}{'gm_id':>8}{'VGS(엔진)':>11}{'VGS(강반전)':>13}"
         f"{'W(엔진)um':>12}{'W(올바름)um':>13}{'배수':>10}")
    emit("  " + "-" * 78)
    for name, kind, gm_id, L, vds, vsb, lo, hi in hits:
        lut = LUT[kind]
        ID = float(sized[name].get("ID", 0.0))
        v_eng = lut._solve_vgs(gm_id, L, vds, vsb)
        v_str = strong_branch_vgs(lut, gm_id, L, vds, vsb)
        idu_eng = lut.gm_id_to_id_density(gm_id, L, vds, vsb)
        w_eng = L * ID / idu_eng * 1e6 if idu_eng > 0 else float("nan")
        if v_str is None:
            emit(f"  {name:<9}{gm_id:>8.3f}{v_eng:>11.4f}{'(해없음)':>13}"
                 f"{w_eng:>12.4f}{'--':>13}{'--':>10}")
            continue
        idu_str = idu_at_vgs(lut, v_str, L, vds, vsb)
        w_str = L * ID / idu_str * 1e6 if idu_str > 0 else float("nan")
        emit(f"  {name:<9}{gm_id:>8.3f}{v_eng:>11.4f}{v_str:>13.4f}"
             f"{w_eng:>12.4f}{w_str:>13.4f}{w_eng/max(w_str,1e-30):>10.2f}x")


# ── 4. 수정 후 회귀 감시 -- 엔진이 rightmost root와 일치하는가 ────────────────
emit("")
emit("=" * 96)
emit("4. 회귀 감시: `_solve_vgs()`가 독립 계산한 rightmost root와 일치하는가 (B20 수정 후)")
emit("=" * 96)
emit("")
emit("  B20 수정(2026-09-09) 이후 이 절이 이 스크립트의 본체다. LUT 정의역을 훑으며")
emit("  엔진의 `_solve_vgs()`와, 여기서 순수 파이썬으로 다시 구현한 rightmost root를")
emit("  대조한다. 하나라도 어긋나면 회귀다.")


def rightmost_root(lut, gm_id, L, vds, vsb):
    """목표를 품는 가장 오른쪽 구간에서 선형 보간 -- 엔진과 독립인 참조 구현."""
    _, g = lut._gm_id_curve(L, vds, vsb)
    g = np.asarray(g, dtype=float)
    vg = np.asarray(lut.VGS_grid, dtype=float)
    hit = None
    for i in range(len(g) - 2, -1, -1):       # 오른쪽에서 왼쪽으로
        a, b = g[i] - gm_id, g[i + 1] - gm_id
        if a * b <= 0.0:
            hit = i
            break
    if hit is None:
        return None
    ga, gb, va, vb = g[hit], g[hit + 1], vg[hit], vg[hit + 1]
    if ga == gb:
        return float(vb)
    x0, x1, y0, y1 = (ga, gb, va, vb) if ga <= gb else (gb, ga, vb, va)
    return float((y1 - y0) / (x1 - x0) * (gm_id - x0) + y0)


emit("")
emit(f"  {'kind':<7}{'대조 건수':>10}{'일치':>9}{'불일치':>9}{'최대차(V)':>12}"
     f"{'엔진만 실패':>12}{'참조만 실패':>12}")
emit("  " + "-" * 71)
_guard_bad = 0
for kind, lut in LUT.items():
    n = ok = bad = only_eng = only_ref = 0
    worst = 0.0
    for L in lut.L_grid:
        for vds in lut.VDS_grid:
            if vds < 0.15:
                continue
            for vsb in lut.VS_grid:
                for gi in (4.0, 8.0, 12.0, 16.0, 20.0, 24.0):
                    lut._solve_vgs_cache.pop((gi, float(L), float(vds), float(vsb)), None)
                    try:
                        eng = lut._solve_vgs(gi, float(L), float(vds), float(vsb))
                    except ValueError:
                        eng = None
                    ref = rightmost_root(lut, gi, float(L), float(vds), float(vsb))
                    if eng is None and ref is None:
                        continue
                    if eng is None:
                        only_ref += 1
                        continue
                    if ref is None:
                        only_eng += 1
                        continue
                    n += 1
                    if eng == ref:
                        ok += 1
                    else:
                        bad += 1
                        worst = max(worst, abs(eng - ref))
    _guard_bad += bad + only_eng + only_ref
    emit(f"  {kind:<7}{n:>10d}{ok:>9d}{bad:>9d}{worst:>12.3g}{only_eng:>12d}{only_ref:>12d}")

emit("")
emit("  판정: " + ("★ 회귀 -- 위 불일치를 조사할 것" if _guard_bad
                   else "통과 (전 건 일치, 실패 조건도 동일)"))

emit("")
emit("완료. 결과 파일:", _RESULT_PATH)
