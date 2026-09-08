# -*- coding: utf-8 -*-
"""propagate_node_voltages() / audit_vsb_consistency() 를 파일럿에 돌려 보는 조사 도구.

계획 §7.5의 코어(노드전압 복원)와 §10.3 B7/B9의 근거다. 두 신규 함수가 실제로 무엇을
잡아내는지 눈으로 보려고 만들었다.

측정 결과(2026-09-08, current_reuse_telescopic_ota, instance.json의 사이징 기준):

  propagate_node_voltages()
    노드 36개 복원 / 미해소 소자 0개 / pass 3회
    **다중도달 불일치 4건, 전부 정확히 243.5 mV**
      M5 (nmos, gnd->Vy)  M64 (nmos, N64_63->Vbias3)
      M1a/M1b (pmos, Vx->N1a2a/N1b2b)
    -> 네 건이 같은 크기라는 것은 단일 원인이 전파된 것이다. M5/M1a/M1b는 전부
       vertical_stack_id='diffpair_branch_a'로 같은 컬럼이다.
    결정론: 소자 사전을 뒤집어 넣어도 노드값·conflict 건수가 동일하다.

  audit_vsb_consistency()
    선언 vsb와 복원된 노드전압이 어긋나는 소자 **26개**. 최대 -1.3000V(M37a/M37b).

⚠️ 중요한 함의: 다중도달 불일치가 남아 있는 동안에는 **노드전압이 유일하게 정해지지
않는다**. 어느 경로가 먼저 도달하느냐에 따라 값이 갈리므로, 그 위에서 유도한 "기대 vsb"도
잠정값이다. 따라서 vsb를 고치기 전에 243.5mV 불일치(= 선언된 vds들이 서로 모순)를 먼저
해소해야 한다.

실행: assets 디렉터리에서 `python tests/probe_node_voltage_audit.py`
(자동 테스트가 아니라 조사용. instance.json이 아직 옛 이름 `vs`를 쓰므로 읽을 때 vsb로 바꿔준다.)
"""
import os, sys, json
ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
import sizing_recipe as sr

TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
INST = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\current-reuse-telescopic-ota-report\current_reuse_telescopic_ota.instance.json"
VDD = 1.8

trs, meta = sr.load_topology(TOPO)
sized = json.load(open(INST, encoding="utf-8"))["sizing"]
for v in sized.values():                      # 옛 이름 호환(조사용에 한함)
    if "vs" in v and "vsb" not in v:
        v["vsb"] = v.pop("vs")
by = {t.name: t for t in trs}

rep = sr.propagate_node_voltages(by, sized, VDD)
print("=== propagate_node_voltages ===")
print("  노드 %d개 / 미해소 %d개 / pass %d회" % (len(rep.nodes), len(rep.unresolved), rep.passes))
print("  다중도달 불일치 %d건:" % len(rep.conflicts))
for nm, net, have, exp, d in rep.conflicts:
    t = by[nm]
    print("    %-6s %-5s %-11s -> %-11s vds=%.4f | 기존 %.4f vs %.4f = %.1f mV"
          % (nm, t.kind, t.source, t.drain, sized[nm]["vds"], have, exp, d * 1e3))

print()
print("=== audit_vsb_consistency ===")
bad = sr.audit_vsb_consistency(by, sized, VDD)
print("  불일치 %d개:" % len(bad))
for r in bad:
    print("    %-8s %-5s src=%-13s V=%7.4f  선언 %7.4f  기대 %7.4f  차이 %+7.4f" % r)
