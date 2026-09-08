# -*- coding: utf-8 -*-
"""`vs`의 정의를 LUT 정본에 맞춰 검산한다(B9 후속, 사용자 확인 요청).

LUT 생성 넷리스트(sky130_lut_sweep.py)가 정본:
    vb  b 0 dc {vb_dc}        vb_dc = vb_sign * VS * (-1)
    xdut d g 0 b ...          <- source는 항상 노드 0
즉 VS 축은 **소스-벌크 역바이어스 |V_SB|**다(소스의 절대 전압이 아니다).

그런데 벌크가 레일에 묶이는 통상 배치에서는
    NMOS (bulk=gnd) : |V_SB| = V_source - 0      = V_source
    PMOS (bulk=vdd) : |V_BS| = vdd - V_source
가 되어, NMOS에서는 "소스 전압"과 값이 같아진다.

이 스크립트는 노드전압을 복원한 뒤 소자별 **기대 vs**를 위 식으로 계산해 선언값과 대조한다.
"""
import os, sys, json
ASSETS = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets"
sys.path.insert(0, ASSETS)
import sizing_recipe as sr

TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
INST = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\current-reuse-telescopic-ota-report\current_reuse_telescopic_ota.instance.json"
VDD = 1.8
RAIL_HI, RAIL_LO = {"vdd", "VDD"}, {"gnd", "GND", "vss", "VSS"}

trs, meta = sr.load_topology(TOPO)
sized = json.load(open(INST, encoding="utf-8"))["sizing"]
by = {t.name: t for t in trs}

# 결정론적 노드전압 복원(이름 정렬 순회)
nodes = {"vdd": VDD, "gnd": 0.0}
unresolved = set(by)
for _ in range(30):
    progressed = False
    for name in sorted(unresolved):
        t = by[name]
        if t.source in nodes and t.drain not in nodes:
            nodes[t.drain] = (nodes[t.source] - sized[name]["vds"] if t.kind == "pmos"
                              else nodes[t.source] + sized[name]["vds"])
            unresolved.discard(name); progressed = True
        elif t.source in nodes and t.drain in nodes:
            unresolved.discard(name)
    if not progressed:
        break
print("노드전압 복원: %d개 (미해소 소자 %d개)" % (len(nodes), len(unresolved)))
print()

print("%-8s %-5s %-13s %9s %11s %11s %10s" %
      ("소자", "kind", "source net", "V(src)", "선언 vs", "기대 vs", "차이"))
print("-" * 82)
bad, ok, unknown = [], [], []
for name in sorted(by):
    t = by[name]; e = sized.get(name)
    if not e or "vs" not in e:
        continue
    vsrc = nodes.get(t.source)
    if vsrc is None:
        unknown.append(name); continue
    exp = vsrc if t.kind == "nmos" else (VDD - vsrc)     # 벌크가 레일에 묶였다는 전제
    d = e["vs"] - exp
    row = (name, t.kind, t.source, vsrc, e["vs"], exp, d)
    (ok if abs(d) < 1e-6 else bad).append(row)
for r in sorted(bad, key=lambda x: -abs(x[6])):
    print("%-8s %-5s %-13s %9.4f %11.4f %11.4f %+10.4f" % r)
print()
print("일치 %d개 / **불일치 %d개** / 노드전압 미복원 %d개" % (len(ok), len(bad), len(unknown)))
print()
print("=== 일치하는 소자(참고, 앞 8개) ===")
for r in ok[:8]:
    print("%-8s %-5s %-13s %9.4f %11.4f %11.4f %+10.4f" % r)

print()
print("=== 눈에 띄는 쌍 ===")
for a, b in (("M9a", "M9b"), ("M18a", "M18b")):
    ea, eb = sized.get(a), sized.get(b)
    ta, tb = by.get(a), by.get(b)
    if not (ea and eb):
        continue
    va, vb2 = nodes.get(ta.source), nodes.get(tb.source)
    print("  %s(%s, src=%s V=%.4f) vs=%.4f  |  %s(%s, src=%s V=%.4f) vs=%.4f"
          % (a, ta.kind, ta.source, va if va is not None else float('nan'), ea["vs"],
             b, tb.kind, tb.source, vb2 if vb2 is not None else float('nan'), eb["vs"]))
    if va is not None and vb2 is not None:
        exp_a = va if ta.kind == "nmos" else VDD - va
        exp_b = vb2 if tb.kind == "nmos" else VDD - vb2
        print("      기대: %s=%.4f, %s=%.4f  -> 선언값이 서로 바뀐 것처럼 보이는가: %s"
              % (a, exp_a, b, exp_b,
                 "예" if (abs(ea["vs"] - exp_b) < 1e-3 and abs(eb["vs"] - exp_a) < 1e-3) else "아니오"))
