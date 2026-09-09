# -*- coding: utf-8 -*-
"""B19' 배선 **후** 왜 infeasible한가를 소자 단위로 짚는 조사 도구(2026-09-09).

## 배경

미러 15소자에 `gm_id_match_vgs_of`를 선언해 VGS를 강제했더니 SLSQP가 40회 전부
infeasible을 냈고, 이어서 레이아웃이 `cmfb_tail`(M37a/M37b/M38)에서 공통 finger 폭을
못 찾았다. **관계는 강제됐고 현재 동작점이 그 관계를 만족하지 못한다**는 뜻이다.

이 스크립트는 그 이유를 소자 단위로 계산한다 -- 각 미러 소자가 레퍼런스의 VGS에서
**자기 자신의 L**로 얼마의 W를 요구하는지 재고, W_bounds(1~200µm)를 넘는 소자를 짚는다.

## 왜 "자기 자신의 L"인가

`probe_mirror_design_space.py`는 그룹이 **하나의 L을 공유**한다고 가정하고 훑었다.
그런데 실제로는 갈린다 -- `device_roles.L_role`이 소자마다 다르기 때문이다:

    L_role="mirror"        L = L_min * 2.5 = 0.375um   (_L_ROLE_MULTIPLIERS, 하드코딩 상수)
    L_role="bias_replica"  L = L_min * 1.2 = 0.180um

미러 성립에 L이 같을 필요는 없다(VGS 동일은 KVL이 강제하고, 각 소자의 gm_id는 자기
(L,vds,vsb)에서 역산된다). 다만 **요구 W는 L에 비례**하므로 판정은 소자별로 해야 한다.

실행: assets 디렉터리에서 `python tests/probe_mirror_infeasibility.py`
(사이징을 돌리지 않는다 -- 배선 전 실측값을 상수로 받아 LUT만 조회하므로 즉시 끝난다.)
"""
import sys
import os
import json
import math
import collections

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

# 배선 **직전**의 실측 동작점(probe_mirror_wiring_readiness.result.txt, 2026-09-09).
# 사이징을 다시 돌리지 않고 이 상수를 쓰는 이유: 지금 돌리면 infeasible이라 값 자체가
# 안 나온다. 우리가 답하려는 질문은 "그 동작점에서 미러를 강제하면 무엇이 터지나"다.
REF_VGS = {"pmos:Vbias1": 0.6750, "nmos:Vbias4": 0.3750, "pmos:Vcmfb": 0.8625}
# 소자: (kind, ID(A), vds(V), vsb(V), L(m))
OP = {
    "M6":  ("pmos", 6.4661e-6, 0.2000, 0.0, 0.180e-6),
    "M8":  ("pmos", 3.8796e-6, 0.9411, 0.0, 0.375e-6),
    "M13": ("pmos", 0.2586e-6, 1.0500, 0.0, 0.375e-6),
    "M22": ("pmos", 0.2586e-6, 1.0500, 0.0, 0.375e-6),
    "M17": ("pmos", 3.8796e-6, 0.9411, 0.0, 0.375e-6),
    "M60": ("pmos", 0.2586e-6, 1.4250, 0.0, 0.375e-6),
    "M61": ("pmos", 0.2586e-6, 0.9500, 0.0, 0.375e-6),
    "M5":  ("nmos", 12.9321e-6, 0.2000, 0.0, 0.180e-6),
    "M12": ("nmos", 0.2586e-6, 0.4500, 0.0, 0.375e-6),
    "M10": ("nmos", 3.8796e-6, 0.8003, 0.0, 0.375e-6),
    "M21": ("nmos", 0.2586e-6, 0.4500, 0.0, 0.375e-6),
    "M19": ("nmos", 3.8796e-6, 0.8003, 0.0, 0.375e-6),
    "M68": ("nmos", 0.2586e-6, 0.6875, 0.0, 0.375e-6),
    "M38": ("nmos", 23.6003e-6, 0.7375, 0.0, 0.375e-6),
    "M7":  ("pmos", 1.2932e-6, 0.2000, 0.0, 0.180e-6),
}
GROUP_OF = {
    **{m: "pmos:Vbias1" for m in ("M6", "M8", "M13", "M22", "M17", "M60", "M61")},
    **{m: "nmos:Vbias4" for m in ("M5", "M12", "M10", "M21", "M19", "M68", "M38")},
    "M7": "pmos:Vcmfb",
}
W_LO, W_HI = 1e-6, 200e-6


def idu_at_vgs(lut, vgs, L, vds, vsb):
    raw = math.exp(lut._query(lut._log_ID, L, vgs, vds, vsb))
    return raw * L / lut._w_ref_effective(L)


emit("=" * 96)
emit("1. 레퍼런스 VGS를 그대로 강제하면 각 소자가 요구하는 W")
emit("=" * 96)
emit("")
emit("  W_bounds = 1 ~ 200 um. 넘으면 그 소자 때문에 이 동작점이 성립하지 않는다.")

by_group = collections.defaultdict(list)
for m, g in GROUP_OF.items():
    by_group[g].append(m)

violators = []
for g in ("pmos:Vbias1", "nmos:Vbias4", "pmos:Vcmfb"):
    vgs = REF_VGS[g]
    emit("")
    emit(f"  [{g}]  강제 VGS = {vgs:.4f} V")
    emit(f"  {'소자':<7}{'L(um)':>8}{'ID(uA)':>10}{'vds':>8}{'gm_id':>9}"
         f"{'요구W(um)':>13}{'판정':>10}")
    emit("  " + "-" * 66)
    for m in by_group[g]:
        kind, ID, vds, vsb, L = OP[m]
        lut = LUT[kind]
        try:
            gm_id = lut.gm_id_for_vgs(vgs, L, vds, vsb)
            idu = idu_at_vgs(lut, vgs, L, vds, vsb)
            W = L * ID / idu
        except Exception as e:
            emit(f"  {m:<7}{L*1e6:>8.4f}{ID*1e6:>10.4f}{vds:>8.4f}"
                 f"{'--':>9}{'(LUT 범위 밖)':>13}{'★실패':>10}")
            violators.append((g, m, None))
            continue
        over = W > W_HI or W < W_LO
        verdict = ("★상한 초과" if W > W_HI else ("★하한 미달" if W < W_LO else "OK"))
        if over:
            violators.append((g, m, W))
        emit(f"  {m:<7}{L*1e6:>8.4f}{ID*1e6:>10.4f}{vds:>8.4f}{gm_id:>9.3f}"
             f"{W*1e6:>13.3f}{verdict:>10}")

emit("")
emit("=" * 96)
emit("2. 판정")
emit("=" * 96)
emit("")
if violators:
    emit(f"  W_bounds를 벗어나는 소자 {len(violators)}개:")
    for g, m, W in violators:
        txt = "LUT 범위 밖" if W is None else f"{W*1e6:.1f}um (상한의 {W/W_HI:.1f}배)"
        emit(f"    {m:<7}({g})  {txt}")
else:
    emit("  전원 W_bounds 안 -- 이 동작점에서도 성립한다.")

# ── 3. 어디까지 VGS를 올리면 성립하나 ────────────────────────────────────────
emit("")
emit("=" * 96)
emit("3. 그룹별로 VGS를 얼마나 옮기면 전원이 W_bounds 안에 들어오나")
emit("=" * 96)
emit("")
emit("  각 소자의 L은 지금 값 그대로 두고 공유 VGS만 훑는다(= diode 레퍼런스의 vds를")
emit("  어디로 보내야 하는가). L을 바꾸는 것은 별개 선택지다.")

for g in ("pmos:Vbias1", "nmos:Vbias4", "pmos:Vcmfb"):
    emit("")
    emit(f"  [{g}]  현재 {REF_VGS[g]:.4f} V")
    emit(f"    {'VGS(V)':>8}{'최대 요구W(um)':>16}{'그 소자':>9}{'판정':>8}")
    emit("    " + "-" * 43)
    ok_lo = None
    for vgs in [0.40 + 0.05 * i for i in range(21)]:
        worst_w, worst_m, bad = 0.0, None, False
        for m in by_group[g]:
            kind, ID, vds, vsb, L = OP[m]
            lut = LUT[kind]
            try:
                idu = idu_at_vgs(lut, vgs, L, vds, vsb)
                W = L * ID / idu
            except Exception:
                bad = True
                break
            if W > worst_w:
                worst_w, worst_m = W, m
            if W < W_LO:
                bad = True
        if bad:
            continue
        ok = worst_w <= W_HI
        if ok and ok_lo is None:
            ok_lo = vgs
        if 0.55 <= vgs <= 1.15:
            emit(f"    {vgs:>8.2f}{worst_w*1e6:>16.2f}{str(worst_m):>9}"
                 f"{'OK' if ok else '초과':>8}")
    emit(f"    -> 성립 시작 VGS ≈ {ok_lo if ok_lo else '(없음)'}"
         f"   (현재 {REF_VGS[g]:.4f}V 대비 {'+%.3fV' % (ok_lo - REF_VGS[g]) if ok_lo else '--'})")

emit("")
emit("완료. 결과 파일:", _RESULT_PATH)
