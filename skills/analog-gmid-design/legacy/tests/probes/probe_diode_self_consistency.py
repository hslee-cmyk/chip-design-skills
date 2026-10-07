# -*- coding: utf-8 -*-
"""diode-connected 소자의 Vgs=Vds 자기일관해를 전수로 풀어 현재 배정과 대조하는 조사 도구.

계획 §7.3(B1 해소)의 근거다. `gate == drain`이면 Vgs=Vds가 물리적으로 강제되므로 그 소자의
vds는 배정 대상이 아니라 gm_id/L/vsb가 정하는 **종속값**이다.

측정 결과(2026-09-08, current_reuse_telescopic_ota, instance.json 사이징 기준):

  is_diode_connected()로 잡힌 소자: **16개**
  (참고: 이들의 headroom_role은 cascode 10 / mirror 3 / voltage_divider 2 /
   diode_reference 1로 흩어져 있다 -- role로 판정했다면 15개를 놓친다)

  자기일관해를 16/16 전부 찾았고 검산 g(v*) ~1e-7로 수렴했다.
  현재 배정 vds와의 **|오차| 평균 0.548V, 최대 1.061V**(M36a/M36b: 0.300 -> 1.361V).

  소자      현재vds   자기일관해    오차
  M36a/b    0.3000    1.3614     +1.0614
  M57       0.2000    1.0512     +0.8512
  M18_bg    0.2000    0.9849     +0.7849
  M11a/b, M20a/b  0.2000  0.8728  +0.6728
  M64       0.2000    0.6796     +0.4796
  M66       0.3000    0.6195     +0.3195
  M14a/b, M23a, M24b  0.2000  0.5517  +0.3517
  M39/M40   0.9000    0.9526     +0.0526

해법은 대입 반복이 아니라 **bisection**이다(계획 §10.2 A7). 브래킷을 지어내지 않고 LUT의
VDS 격자점 위에서 g(v) = vgs_for_gm_id(...) - v 의 부호가 갈리는 인접 구간을 찾는다.
VDS=0 같은 점은 소자가 꺼져 있어 gm_id 조회가 범위 밖이므로 건너뛴다(그 점을 브래킷 끝으로
쓰면 16개 전부 실패한다 -- 실측으로 확인했다).
해가 격자 안에 없으면 마지막 값을 반환하지 않고 DiodeSelfConsistencyError로 명시 실패한다.

실행: assets 디렉터리에서 `python tests/probe_diode_self_consistency.py`
(자동 테스트가 아니라 조사용. instance.json이 아직 옛 이름 `vs`를 쓰므로 읽을 때 vsb로 바꿔준다.)
"""
import os, sys, json
ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # probes -> tests -> assets
sys.path.insert(0, ASSETS)
import numpy as np
import sizing_recipe as sr

TOPO = os.path.join(ASSETS, "..", "assets", "library", "current_reuse_telescopic_ota.topology.json")
INST = os.path.join(ASSETS, "workspaces", "current-reuse-telescopic-ota-report", "current_reuse_telescopic_ota.instance.json")

trs, meta = sr.load_topology(TOPO)
sized = json.load(open(INST, encoding="utf-8"))["sizing"]
for v in sized.values():
    if "vs" in v and "vsb" not in v:
        v["vsb"] = v.pop("vs")
npz = np.load(os.path.join(ASSETS, "..", "assets", "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(npz["L"], npz["VGS"], npz["VDS"], npz["VS"],
                                       npz["ID_" + k], npz["GM_" + k], npz["GDS_" + k],
                                       npz["CGG_" + k], W_ref=5e-6)
lut = {"nmos": mk("n"), "pmos": mk("p")}
by = {t.name: t for t in trs}
roles = meta.get("device_roles", {})

diode = sorted(n for n, t in by.items() if sr.is_diode_connected(t))
print("is_diode_connected: %d개" % len(diode))
from collections import Counter
print("  headroom_role 분포:", dict(Counter(roles.get(n, {}).get("headroom_role") for n in diode)))
print()
print("%-8s %-5s %7s %9s %11s %11s %10s" %
      ("소자", "kind", "gm_id", "현재vds", "자기일관해", "검산 g(v*)", "오차(V)"))
print("-" * 76)
errs = []
for n in diode:
    e = sized[n]
    try:
        v = sr.solve_diode_connected_vds(lut[e["kind"]], e["gm_id"], e["L"], e.get("vsb", 0.0))
        g = lut[e["kind"]].vgs_for_gm_id(e["gm_id"], e["L"], v, e.get("vsb", 0.0)) - v
        errs.append(v - e["vds"])
        print("%-8s %-5s %7.2f %9.4f %11.4f %11.2e %+10.4f"
              % (n, e["kind"], e["gm_id"], e["vds"], v, g, v - e["vds"]))
    except sr.DiodeSelfConsistencyError as ex:
        print("%-8s %-5s %7.2f %9.4f  실패: %s" % (n, e["kind"], e["gm_id"], e["vds"], str(ex)[:70]))
if errs:
    print()
    print("해 찾음 %d/%d,  |오차| 최대 %.4f V, 평균 %.4f V"
          % (len(errs), len(diode), max(abs(x) for x in errs), sum(abs(x) for x in errs) / len(errs)))
