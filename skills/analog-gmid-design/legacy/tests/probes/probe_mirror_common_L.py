# -*- coding: utf-8 -*-
"""미러 동치류의 **공통 L**을 정하려면 무엇이 먼저 무는가(2026-09-10).

## 배경 -- 왜 knee 하나로 못 정하나

사용자 지적으로 확인된 구조: 미러 안에서 L이 다르면 전류비가 PVT에 흔들려 실리콘에서
안 맞는다. 그리고 이 회로에서는 세 미러 그룹이 **하나의 동치류**로 묶인다:

    M5 --(같은 미러 Vbias4)-- M38 --> CMFB 차동쌍 --> M36a --(같은 미러 Vcmfb)-- M7
                                                                                 |
    M6 --(same_as_device)------------------------------------------------------- +

즉 **L의 자유도가 그룹당 하나가 아니라 회로 전체에 하나**다. 그런데 §7.10의 role별 편향은
서로 반대 방향을 요구한다:

    mirror/matching  : knee 이상 (면적이 매칭에 직접 기여)
    tail/load        : CMRR/PSRR을 만족하는 **최소** L
    속도 임계 입력단  : fT 상한이 지배 -> knee보다 작을 수도 있음

하나뿐인 L에 세 편향을 동시에 줄 수는 없다. **누가 먼저 무는지를 재서 정해야 한다.**

## 무엇을 재는가

동치류 전체를 후보 L마다 미러로 강제했을 때(공통 VGS는 diode 레퍼런스의 자기일관점에서
나온다), `diode_vds_window(..., mirror_members=...)`가 창을 돌려주는지 -- 즉 **전원이 W 한계
안에 들어오는 L 구간**이 어디인지 본다. 창이 비면 그 L은 애초에 불가능하다.

전류가 큰 소자(M38 23.6µA, M5 12.9µA)가 W 천장에 먼저 닿으므로, **tail이 상한을 쥔다**는
사용자 직관이 실제로 성립하는지가 여기서 드러난다.

**아무것도 고치지 않는다 -- 표만 만든다.**

실행: assets 디렉터리에서 `python tests/probe_mirror_common_L.py`
"""
import sys
import os
import json
import math
import collections

ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # probes -> tests -> assets
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


TOPO = os.path.join(ASSETS, "..", "assets", "library", "current_reuse_telescopic_ota.topology.json")
VDD, W_LO, W_HI = 1.8, 1e-6, 200e-6
d = np.load(os.path.join(ASSETS, "..", "assets", "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                       d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                       W_ref=5e-6, SID_1F=d["SID_1F_" + k])
LUT = {"nmos": mk("n"), "pmos": mk("p")}

# 현 동작점(2026-09-09 실측). ID/vds는 L을 바꿔도 KCL/헤드룸이 정하므로 그대로 쓰고,
# vsb는 소스가 레일이라 0이다(B9로 확인).
#   (소자, kind, ID(A), vds(V), 역할)
OP = [
    ("M5",     "nmos", 12.9321e-6, 0.2000, "tail"),
    ("M38",    "nmos", 23.6003e-6, 0.7375, "tail"),
    ("M10",    "nmos",  3.8796e-6, 0.8003, "mirror"),
    ("M19",    "nmos",  3.8796e-6, 0.8003, "mirror"),
    ("M12",    "nmos",  0.2586e-6, 0.4500, "mirror"),
    ("M21",    "nmos",  0.2586e-6, 0.4500, "mirror"),
    ("M68",    "nmos",  0.2586e-6, 0.6875, "mirror"),
    ("M66",    "nmos",  0.2586e-6, 0.3750, "diode ref"),
    ("M6",     "pmos",  6.4661e-6, 0.2000, "tail"),
    ("M8",     "pmos",  3.8796e-6, 0.9411, "mirror"),
    ("M17",    "pmos",  3.8796e-6, 0.9411, "mirror"),
    ("M13",    "pmos",  0.2586e-6, 1.0500, "mirror"),
    ("M22",    "pmos",  0.2586e-6, 1.0500, "mirror"),
    ("M60",    "pmos",  0.2586e-6, 1.4250, "mirror"),
    ("M61",    "pmos",  0.2586e-6, 0.9500, "mirror"),
    ("M18_bg", "pmos",  0.2586e-6, 0.6750, "diode ref"),
    ("M7",     "pmos",  1.2932e-6, 0.2000, "tail"),
    ("M36a",   "pmos", 11.8002e-6, 0.8625, "diode ref"),
]
GROUP = {**{n: "nmos:Vbias4" for n in ("M5", "M38", "M10", "M19", "M12", "M21", "M68", "M66")},
         **{n: "pmos:Vbias1" for n in ("M6", "M8", "M17", "M13", "M22", "M60", "M61", "M18_bg")},
         **{n: "pmos:Vcmfb" for n in ("M7", "M36a")}}
REF = {"nmos:Vbias4": "M66", "pmos:Vbias1": "M18_bg", "pmos:Vcmfb": "M36a"}
BY = {n: (k, i, v, r) for n, k, i, v, r in OP}


def idu(kind, vgs, L, vds, vsb=0.0):
    # IDu(W/L=1 기준 전류)는 VGS에서 직접 읽는 엔진 정본 `id_density_at_vgs()`로 얻는다.
    return LUT[kind].id_density_at_vgs(vgs, L, vds, vsb)


emit("=" * 104)
emit("미러 동치류의 공통 L -- 후보 L마다 전원이 W 한계 안에 들어오는가")
emit("=" * 104)
emit("")
emit("  공통 VGS는 각 그룹 diode 레퍼런스의 자기일관점(Vgs=Vds)에서 나온다. 그 VGS로")
emit("  같은 그룹 전원의 W를 구해 1~200um 안인지 본다. 창이 비면 그 L은 불가능하다.")
emit("")
emit(f"  knee = 2.5 x L_min = 0.375um  (§7.10)")

L_GRID = [float(v) for v in LUT["nmos"].L_grid]
rows = []
for L in L_GRID:
    per_group = {}
    for g, refname in REF.items():
        kind_r, ID_r, _vds_r, _ = BY[refname]
        lut_r = LUT[kind_r]
        # diode 레퍼런스의 자기일관 vds 후보 = VDS 격자. 그 중 그룹 전원이 성립하는 것.
        best = None
        for v in lut_r.VDS_grid:
            v = float(v)
            if v <= 0:
                continue
            try:
                w_r = L * ID_r / idu(kind_r, v, L, v)
            except Exception:
                continue
            if not (W_LO <= w_r <= W_HI):
                continue
            worst_w, worst_n, ok = w_r, refname, True
            for n2 in [x for x in GROUP if GROUP[x] == g and x != refname]:
                k2, I2, v2, _ = BY[n2]
                try:
                    w2 = L * I2 / idu(k2, v, L, v2)
                except Exception:
                    ok = False
                    break
                if not (W_LO <= w2 <= W_HI):
                    ok = False
                    worst_w, worst_n = w2, n2
                    break
                if w2 > worst_w:
                    worst_w, worst_n = w2, n2
            if ok and (best is None or worst_w < best[1]):
                best = (v, worst_w, worst_n)
        per_group[g] = best
    rows.append((L, per_group))

emit("")
emit(f"  {'L(um)':>8}" + "".join(f"{g:>26}" for g in REF))
emit("  " + "-" * (8 + 26 * len(REF)))
for L, pg in rows:
    cells = []
    for g in REF:
        b = pg[g]
        cells.append(f"{'★불가':>26}" if b is None
                     else f"{('VGS%.3f W%.1f(%s)' % (b[0], b[1] * 1e6, b[2])):>26}")
    mark = "  <- knee" if abs(L - 0.375e-6) < 1e-12 else ""
    emit(f"  {L*1e6:>8.4f}" + "".join(cells) + mark)

emit("")
emit("  (칸: 그룹이 성립하는 공통 VGS와 그때 **가장 넓은 소자**의 W)")

emit("")
emit("=" * 104)
emit("어느 소자가 상한을 쥐는가 -- L별 최대 W 소자")
emit("=" * 104)
emit("")
holder = collections.Counter()
for L, pg in rows:
    for g, b in pg.items():
        if b:
            holder[b[2]] += 1
emit("  L 후보 전체에서 '가장 넓은 소자'로 뽑힌 횟수:")
for n, c in holder.most_common():
    emit(f"    {n:<8}{BY[n][3]:<12}ID={BY[n][1]*1e6:>8.4f}uA   {c}회")

emit("")
emit("  -> 전류가 큰 tail이 W 천장을 먼저 친다면, 공통 L의 **상한은 tail이 쥔다**.")

emit("")
emit("완료. 결과 파일:", _RESULT)
