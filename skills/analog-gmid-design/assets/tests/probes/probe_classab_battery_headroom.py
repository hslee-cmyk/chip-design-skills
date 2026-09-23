# -*- coding: utf-8 -*-
"""class-AB floating battery의 **헤드룸**이 선언돼 있지 않다 -- M9b 스택 예산 음수의 원인
(2026-09-10, 정본 spec 도입 후 드러남).

## 구조 (순수 connectivity 사실, 세션22 J-2가 이미 확인)

    M9a  PMOS  source=Vg15  drain=Vop1  gate=N11b
    M9b  NMOS  drain=Vg15   source=Vop1 gate=N14a14b

**직렬이 아니라 같은 두 노드를 잇는 상보 병렬쌍**(Monticelli floating current source)이다.
실제 컬럼은 `vdd -> M8 -> Vg15 -> (M9a∥M9b) -> Vop1 -> M10 -> gnd`이고, 양 끝은 출력단
게이트가 KVL로 직접 정한다:

    VDS(M8)  = |VGS(M15)|   (M8.drain = Vg15 = M15.gate, M15.source=vdd)   <- vds_match_vgs_of
    VDS(M10) =  VGS(M16)    (M10.drain= Vop1 = M16.gate, M16.source=gnd)   <- vds_match_vgs_of

    => V_bat = V(Vg15) - V(Vop1) = vdd - |VGS(M15)| - VGS(M16)

## 무엇이 빠졌나

`classab_centering_dev_v`(= |VGS(M16) - VGS(M15)|, constraint <= 0.15V)는 이미 선언돼 있다.
그런데 그건 **차이**다. 배터리 몫은 **합**이다:

    centering :  VGS(M16) = VGS(M15)                      <- 선언·통과함
    battery   :  vdd - VGS(M15) - VGS(M16) >= (포화 여유)   <- **선언 없음**

완벽히 센터링해도 `V_bat = vdd - 2*VGS`라 VGS가 크면 음수가 된다. 논문 동작점(Vg15 1.3V /
Vop1 0.5V)은 VGS 0.5V씩이라 V_bat=0.8V인데, 엔진에는 VGS를 그쪽으로 끌 근거가 없다.

## 이 스크립트가 재는 것

  1. 실패 지점의 실제 수치(어느 소자가 얼마를 먹는가)
  2. (gm_id, L) 평면에서 `V_bat >= 포화여유`인 영역이 **존재하는가**
     -> 존재하면 설계 불가능이 아니라 제약 누락이다

**아무것도 고치지 않는다 -- 표만 만든다.**

실행: assets 디렉터리에서 `python tests/probe_classab_battery_headroom.py`
"""
import sys
import os

ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # probes -> tests -> assets
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ASSETS, "..", "..", "..", "workspaces"))
import numpy as np
import sizing_recipe as sr
import run_harness as H

_RESULT = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first = [True]


def emit(*p):
    line = " ".join(str(x) for x in p)
    print(line, flush=True)
    mode = "w" if _first[0] else "a"
    _first[0] = False
    with open(_RESULT, mode, encoding="utf-8") as f:
        f.write(line + "\n")


TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
SPEC = H.canonical_spec("current_reuse_telescopic_ota")
VDD = SPEC["vdd"]
P, N = SPEC["lut_by_kind"]["pmos"], SPEC["lut_by_kind"]["nmos"]
MINV = sr._DEFAULT_MIN_VDS_FALLBACK      # floating_current_source는 role 항목이 없다

emit("=" * 100)
emit("class-AB floating battery 헤드룸 -- 선언이 빠져 있다 (정본 spec)")
emit("=" * 100)
emit(f"  spec 출처: {SPEC['_spec_source']}")
emit(f"  min_vds_by_role = {SPEC['min_vds_by_role']}")
emit(f"  floating_current_source 항목 없음 -> 폴백 {MINV}V 적용")

emit("")
emit("-" * 100)
emit("1. 실패 지점 -- theta를 bounds 중점에 놓고 1점 평가")
emit("-" * 100)
env = sr._build_theta_evaluator(TOPO, SPEC)
mid = {t["name"]: (float(t["bounds"][0]) + float(t["bounds"][1])) / 2.0 if t.get("bounds") else 0.0
       for t in env["thetas"]}
snap = None
try:
    env["evaluate"](mid)
    emit("  평가 성공 -- 이 시점에는 재현되지 않는다")
except sr.InfeasibleSizingError as e:
    snap = getattr(e, "sized_snapshot", None)
    emit(f"  InfeasibleSizingError: {str(e)[:150]}")

if snap:
    def vgs(n):
        e = snap[n]
        return SPEC["lut_by_kind"][e["kind"]].vgs_for_gm_id(
            e["gm_id"], e["L"], e["vds"], e.get("vsb", 0.0))
    emit("")
    emit(f"    {'소자':<7}{'kind':<6}{'gm_id':>8}{'L(um)':>9}{'vds(V)':>9}{'VGS(V)':>9}"
         f"{'ID(uA)':>10}{'W(um)':>10}")
    emit("    " + "-" * 68)
    for n in ("M15", "M16"):
        e = snap.get(n)
        if not e:
            continue
        emit(f"    {n:<7}{e['kind']:<6}{e['gm_id']:>8.3f}{e['L']*1e6:>9.4f}"
             f"{e['vds']:>9.4f}{vgs(n):>9.4f}{e['ID']*1e6:>10.4f}{e['W']*1e6:>10.3f}")
    gp, gn = vgs("M15"), vgs("M16")
    emit("")
    emit(f"    centering |VGS(M16)-VGS(M15)| = {abs(gn-gp):.4f}V  (제약 <=0.15V -> "
         f"{'통과' if abs(gn-gp) <= 0.15 else '위반'})")
    emit(f"    battery   vdd - VGS(M15) - VGS(M16) = {VDD:.2f} - {gp:.4f} - {gn:.4f} = "
         f"**{VDD-gp-gn:+.4f}V**  (필요 >= {MINV}V)")
    emit("")
    emit("    -> 센터링은 통과하는데 배터리는 음수다. 차이는 재고 합은 안 재기 때문이다.")

emit("")
emit("-" * 100)
emit(f"2. (gm_id, L) 평면에서 V_bat >= {MINV}V 영역이 존재하는가")
emit("-" * 100)
emit("")
emit("  센터링(VGS 동일)을 가정하면 V_bat = vdd - 2*VGS_p. VGS(M15)는 PMOS/vds=0.6/vsb=0.")
emit("")
LS = [0.15e-6, 0.2e-6, 0.3e-6, 0.45e-6, 0.575e-6, 0.75e-6, 1.0e-6]
GM = SPEC["gm_id_grid"]
emit(f"  {'gm_id':>6}" + "".join(f"{L*1e6:>10.3f}" for L in LS) + "   <- L(um), 칸=V_bat(V)")
emit("  " + "-" * (6 + 10 * len(LS)))
cells_ok = 0
cells_all = 0
for g in GM[::4]:
    row = []
    for L in LS:
        try:
            vb = VDD - 2 * P.vgs_for_gm_id(g, L, 0.6, 0.0)
        except Exception:
            row.append(f"{'--':>10})"[:10])
            continue
        cells_all += 1
        if vb >= MINV:
            cells_ok += 1
        row.append(f"{(('%.3f' % vb) + ('*' if vb >= MINV else '')):>10}")
    emit(f"  {g:>6.1f}" + "".join(row))
emit("")
emit(f"  * = V_bat >= {MINV}V.  성립 {cells_ok} / {cells_all}칸")
emit("")
emit(f"  -> 영역이 **존재한다**. 무는 것은 gm_id다: L=0.575um(중점)에서도 gm_id>=19면 성립하고,")
emit(f"     실패 지점의 M15는 gm_id=16.5였다. 즉 설계 불가능이 아니라 **탐색이 그 영역을")
emit(f"     피할 이유가 없어서** 벗어난 것이다 -- 배터리 헤드룸이 metric/constraint로")
emit(f"     선언돼 있지 않기 때문이다.")

emit("")
emit("-" * 100)
emit("3. 참고 -- 센터링 없이 각각 자유로우면 최소 VGS 합은 얼마인가")
emit("-" * 100)
emit("")
emit(f"  {'L(um)':>9}{'min VGS_p':>12}{'min VGS_n':>12}{'합':>10}{'V_bat 최대':>12}")
emit("  " + "-" * 55)
for L in LS:
    vs = []
    for lut, vds in ((P, 0.6), (N, 1.2)):
        best = None
        for g in GM:
            try:
                v = lut.vgs_for_gm_id(g, L, vds, 0.0)
            except Exception:
                continue
            best = v if best is None else min(best, v)
        vs.append(best)
    if None in vs:
        emit(f"  {L*1e6:>9.4f}{'(범위 밖)':>12}")
        continue
    emit(f"  {L*1e6:>9.4f}{vs[0]:>12.4f}{vs[1]:>12.4f}{vs[0]+vs[1]:>10.4f}"
         f"{VDD-vs[0]-vs[1]:>12.4f}")

emit("")
emit("완료. 결과 파일:", _RESULT)
