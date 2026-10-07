# -*- coding: utf-8 -*-
"""`min sum_current`가 진짜 회로 전력인가를 재는 조사 도구(계획 §10.2 A3의 근거).

검토자 지적은 "병렬 branch 수 / 직렬 공유 전류 중복 / bias_devices 전류가 빠졌다"였다.
실측해 보니 셋 중 하나만 맞았다.

측정 결과(2026-09-08, current_reuse_telescopic_ota 51소자):

  (1) bias 누락?  -- **아니다.** sum_current는 devices 미선언 시 ctx.sized 전체를 더한다.
      gain-stage 밖 39소자 107.50uA가 이미 포함돼 있다.

  (2) 직렬 중복?  -- **맞다, 그리고 크다.**
        전 소자 ID 합      243.32 uA
        VDD 레일 유입      86.27 uA     <- 진짜 공급전류
        비율               2.82배

  (3) 더 나쁜 것: 배수가 branch마다 다르다(diffpair_branch_a 8소자 vs battery 3소자).
      즉 `min sum_current`는 **"그 branch에 소자가 몇 개냐"는 설계와 무관한 가중치**가
      붙은 전력을 최소화하게 되어, 소자 수가 많은 branch의 전류를 부당하게 무겁게 본다.

  (4) 부수 관찰: vdd 유입 86.27uA vs gnd 유출 88.93uA로 **3.1% 어긋난다**.
      §7.5가 전압만 검사하고 KCL 잔차를 안 본다는 B8 지적의 실물 증거다.

이 실측이 `_metric_supply_current()`(A3, 2026-09-08 신설)를 만든 근거다. 다만 objective를
supply_current로 바꾸는 것은 탐색 결과를 바꾸는 **설계 결정**이라 아직 하지 않았다 --
두 값을 나란히 보고하는 단계다.

실행: assets 디렉터리에서 `python tests/probe_supply_current.py`
(자동 테스트가 아니라 조사용.)
"""
import os, sys, json
from collections import defaultdict
ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # probes -> tests -> assets
sys.path.insert(0, ASSETS)
import sizing_recipe as sr

TOPO = os.path.join(ASSETS, "..", "assets", "library", "current_reuse_telescopic_ota.topology.json")
INST = os.path.join(ASSETS, "workspaces", "current-reuse-telescopic-ota-report", "current_reuse_telescopic_ota.instance.json")
trs, meta = sr.load_topology(TOPO)
sized = json.load(open(INST, encoding="utf-8"))["sizing"]
by = {t.name: t for t in trs}

# 레일 넷 집합은 엔진 정본 상수를 쓴다(재선언하지 않는다).
RAILS_HI = sr._DEFAULT_RAIL_HI
RAILS_LO = sr._DEFAULT_RAIL_LO

total_all = sum(sized[n]["ID"] for n in sized if "ID" in sized[n])
print("(1) sum_current(devices 미선언) = ctx.sized 전 소자 합")
print("    소자 %d개, 합 = %.4f uA" % (len(sized), total_all * 1e6))
bias_like = [n for n in sized if n not in
             ("M1a", "M1b", "M4a", "M4b", "M2a", "M2b", "M3a", "M3b", "M15", "M16", "M25", "M26")]
print("    그중 gain-stage 밖 소자 %d개 합 = %.4f uA -> **bias 전류는 이미 포함돼 있다**"
      % (len(bias_like), sum(sized[n]["ID"] for n in bias_like) * 1e6))

print()
print("(2)(3) vdd 노드에서 실제로 빠져나가는 전류")
# PMOS는 source가 vdd면 그 소자가 vdd에서 전류를 끌어온다.
# NMOS가 drain=vdd인 경우도(드묾) 포함.
from_vdd = []
for n, t in by.items():
    e = sized.get(n)
    if not e or "ID" not in e:
        continue
    if t.kind == "pmos" and t.source in RAILS_HI:
        from_vdd.append((n, e["ID"], "pmos.source=vdd"))
    elif t.kind == "nmos" and t.drain in RAILS_HI:
        from_vdd.append((n, e["ID"], "nmos.drain=vdd"))
# 공급전류 값은 엔진 정본 `sr._metric_supply_current()`로 구한다(위 목록은 표시용 내역).
supply = sr._metric_supply_current({}, sr.SizingContext(sized=sized, topology_path=TOPO))
print("    vdd에 직접 물린 소자 %d개:" % len(from_vdd))
for n, i, why in sorted(from_vdd, key=lambda x: -x[1]):
    print("      %-8s %8.4f uA   (%s)" % (n, i * 1e6, why))
print("    ** 실제 공급전류 = %.4f uA **" % (supply * 1e6))
print()
print("    전 소자 ID 합 = %.4f uA" % (total_all * 1e6))
print("    비율 = %.2f배  -> 직렬 스택의 공유 전류를 그만큼 중복해서 센다" % (total_all / supply))

print()
print("(2b) 중복이 어디서 오는가 -- 소자별 '몇 겹으로 세어졌나'")
# vertical_stack_id(전기적 직렬 컬럼) 별 소자 수 = 그 컬럼 전류가 몇 번 더해졌는지
roles = meta.get("device_roles", {})
col = defaultdict(list)
for n in sized:
    vs = roles.get(n, {}).get("vertical_stack_id")
    col[vs].append(n)
print("    vertical_stack_id 그룹 %d개" % len(col))
for vs, members in sorted(col.items(), key=lambda kv: -len(kv[1]))[:8]:
    ids = [sized[m]["ID"] for m in members if "ID" in sized[m]]
    same = len(set(round(i, 12) for i in ids)) == 1
    print("      %-22s 소자 %2d개  ID합 %8.4f uA  전부 같은 전류=%s"
          % (str(vs), len(members), sum(ids) * 1e6, same))

print()
print("(4) gnd 쪽으로도 확인(합이 맞아야 KCL 정합)")
to_gnd = sum(e["ID"] for n, e in sized.items()
             if "ID" in e and by.get(n) and
             ((by[n].kind == "nmos" and by[n].source in RAILS_LO) or
              (by[n].kind == "pmos" and by[n].drain in RAILS_LO)))
print("    gnd에 직접 물린 소자 전류 합 = %.4f uA" % (to_gnd * 1e6))
print("    vdd 유입 %.4f uA vs gnd 유출 %.4f uA -> 차이 %.4f uA (%.1f%%)"
      % (supply * 1e6, to_gnd * 1e6, (supply - to_gnd) * 1e6,
         abs(supply - to_gnd) / supply * 100))
