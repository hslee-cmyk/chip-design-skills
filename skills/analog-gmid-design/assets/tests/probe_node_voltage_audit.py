# -*- coding: utf-8 -*-
"""`propagate_node_voltages()` / `audit_vsb_consistency()`를 파일럿에 돌려 **B9(vsb 오산출)의
현재 상태**를 재는 조사 도구.

## 2026-09-09 개정 -- 낡은 산출물 대신 **지금 엔진으로 새로 사이징**해서 잰다

원래 이 스크립트는 workspaces의 `*.instance.json`을 읽었다. 그 파일은 세션18 산출물이라
옛 필드 이름(`vs`)을 쓰고 있어서 읽을 때 `vsb`로 바꿔주는 호환 코드까지 달려 있었다 --
즉 **지금 엔진이 내는 값이 아니라 옛날 값을 재고 있었다**. B20/B22가 들어간 지금은 그
괴리가 더 커져서, 여기서 나온 숫자로 B9를 고치면 엉뚱한 것을 고치게 된다.

이제 `_build_theta_evaluator()` + 실제 최적 theta로 **그 자리에서 사이징**해 잰다.

## 무엇을 보는가

  1. `propagate_node_voltages()` -- 노드전압 복원. **다중도달 불일치**(같은 노드에 두 경로가
     서로 다른 전압을 준다)를 그대로 돌려준다. §7.5가 완성돼야 할 지점.
  2. `audit_vsb_consistency()` -- 선언된 `vsb`가 복원된 노드전압과 맞는지 전수 대조.
     ⚠️ 이 함수는 **엔진 경로에 호출부가 없다**(2026-09-09 확인, 조사용 여기 하나뿐).
     ★절대원칙상 B9를 고치면서 파이프라인 게이트로 배선해야 한다.
  3. 불일치를 **원인별로 분류**한다 -- 어디를 고쳐야 하는지가 분류에서 바로 나온다:
       (가) 소스가 레일인데 vsb!=0     -> 전파가 레일을 안 본다
       (나) 소스가 비레일인데 vsb==0   -> 전파가 아예 안 닿았다
       (다) 그 외 값 불일치            -> kind 혼동 등

실행: assets 디렉터리에서 `python tests/probe_node_voltage_audit.py`
(최적 theta 캐시가 없으면 SLSQP를 한 번 돌리므로 수 분 걸린다.)
"""
import os
import sys
import json

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
import numpy as np
import sizing_recipe as sr
import run_harness as H

_RESULT_PATH = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first = [True]


def emit(*parts):
    line = " ".join(str(p) for p in parts)
    print(line, flush=True)
    mode = "w" if _first[0] else "a"
    _first[0] = False
    with open(_RESULT_PATH, mode, encoding="utf-8") as f:
        f.write(line + "\n")


TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
VDD = 1.8
d = np.load(os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                       d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                       W_ref=5e-6, SID_1F=d["SID_1F_" + k])
nmos, pmos = mk("n"), mk("p")
# 2026-09-10 -- 손으로 복붙한 spec 블록을 폐기하고 **정본**을 쓴다. 복제본은 정본과
# 갈려 있었다(gm_id_grid 21점 vs 57점, L_candidates 12점 vs 41점, VDS_candidates 9점 vs
# 13점, stage_power_tolerance 누락). 같은 블록이 여러 파일에 그대로 퍼져 있었으므로
# 파일마다 다른 판단을 한 게 아니라 복제본 하나가 번진 것이다. 이제
# `sizing_recipe.require_declared_spec_source()`가 라이브러리 회로에 출처 선언을 강제하고,
# 일부러 다르게 쓸 때는 `H.derived_spec(key, why, **overrides)`로 무엇을 왜 바꿨는지 남긴다.
SPEC = H.canonical_spec("current_reuse_telescopic_ota")
nmos = SPEC["lut_by_kind"]["nmos"]
pmos = SPEC["lut_by_kind"]["pmos"]

THETA_CACHE = os.path.splitext(os.path.abspath(__file__))[0] + ".theta_star.json"
if os.path.exists(THETA_CACHE):
    THETA = json.load(open(THETA_CACHE, encoding="utf-8"))
    emit("[캐시] theta_star 재사용:", os.path.basename(THETA_CACHE))
else:
    emit("[신규] SLSQP로 theta_star를 구한다(수 분)...")
    _r = sr.optimize_full_circuit_budget(TOPO, SPEC, search_method="slsqp",
                                         slsqp_kwargs={"n_starts": 1, "maxiter": 40})
    THETA = {k: float(v) for k, v in (_r["theta_star"] or {}).items()}
    json.dump(THETA, open(THETA_CACHE, "w", encoding="utf-8"), indent=1)
    emit("[신규] 확보.")

env = sr._build_theta_evaluator(TOPO, SPEC)
ctx, metrics = env["evaluate"](dict(THETA))
sized = ctx.sized
trs, meta = sr.load_topology(TOPO)
by = {t.name: t for t in trs}
RAILS = {"vdd", "vss", "gnd", "0"}

emit("")
emit("=" * 100)
emit("1. propagate_node_voltages -- 노드전압 복원")
emit("=" * 100)
rep = sr.propagate_node_voltages(by, sized, VDD)
emit(f"  노드 {len(rep.nodes)}개 / 미해소 {len(rep.unresolved)}개 / pass {rep.passes}회")
emit(f"  다중도달 불일치 {len(rep.conflicts)}건:")
for nm, net, have, exp, diff in rep.conflicts:
    t = by[nm]
    emit(f"    {nm:<7}{t.kind:<6}{t.source:<12} -> {t.drain:<12} vds={sized[nm]['vds']:.4f} "
         f"| 기존 {have:.4f} vs {exp:.4f} = {diff*1e3:+.1f} mV")

emit("")
emit("=" * 100)
emit("2. audit_vsb_consistency -- 선언 vsb vs 노드전압에서 유도한 vsb")
emit("=" * 100)
bad = sr.audit_vsb_consistency(by, sized, VDD)
emit(f"  전체 {len(by)}소자 중 불일치 {len(bad)}개")
emit("")
emit(f"  {'소자':<8}{'kind':<6}{'source':<14}{'V(src)':>8}{'선언':>9}{'기대':>9}{'차이':>9}")
emit("  " + "-" * 65)
cat = {"가": [], "나": [], "다": []}
for name, kind, src, vsrc, declared, expected, diff in bad:
    emit(f"  {name:<8}{kind:<6}{src:<14}{vsrc:>8.4f}{declared:>9.4f}{expected:>9.4f}{diff:>+9.4f}")
    if src in RAILS and abs(declared) > 1e-9:
        cat["가"].append(name)
    elif src not in RAILS and abs(declared) <= 1e-9:
        cat["나"].append(name)
    else:
        cat["다"].append(name)

emit("")
emit("=" * 100)
emit("3. 원인별 분류 -- 어디를 고쳐야 하나")
emit("=" * 100)
emit("")
emit(f"  (가) 소스가 레일인데 vsb!=0  {len(cat['가']):>3}개 : {', '.join(cat['가']) or '-'}")
emit("       -> vsb 전파가 레일 소스를 특별취급하지 않는다(레일이면 벌크와 같은 전위라 0)")
emit(f"  (나) 소스가 비레일인데 vsb==0 {len(cat['나']):>3}개 : {', '.join(cat['나']) or '-'}")
emit("       -> 전파가 이 소자에 아예 안 닿았다(선언 0.0이 그대로 남음)")
emit(f"  (다) 그 외 값 불일치         {len(cat['다']):>3}개 : {', '.join(cat['다']) or '-'}")
emit("       -> kind 혼동 등(PMOS는 vdd-V(src)인데 NMOS 식을 썼거나 그 반대)")

emit("")
emit("완료. 결과 파일:", _RESULT_PATH)
