# -*- coding: utf-8 -*-
"""계획 §3.3 C1~C10의 "방지 장치"가 **실제로 배선돼 있는지** 재는 조사 도구.

계획 문서 v4.5(B11 해소)에서 C 표를 "강제 테스트" 열이 있는 형태로 재작성한 근거다.
★절대원칙(만들면 반드시 배선)에 따라, 선언만 있고 배선이 없는 항목을 찾아내는 것이 목적이다.

현재 재는 것:

  C4  role 라벨 과신 — 물리 판정이 항상 우선인가?
      `_feed_vds_fallback()`에 같은 소자를 role만 바꿔 넣어 본다. 결과가 갈리면 위반이다.
      측정(2026-09-08): cascode -> 0.200 / mirror -> 0.300 / 라벨없음 -> 0.600. **위반**.
      그리고 물리적으로 동일한 diode-connected 16개의 role이 4종으로 흩어져 있다
      (cascode 10 / mirror 3 / voltage_divider 2 / diode_reference 1).
      => 목표 테스트: role 라벨을 전부 제거해도 결과가 같아야 한다.

  C5  게이트가 '검사하지 않는 것'을 docstring에 명시하는가?
      check_*/verify_*/validate_*/audit_*/revalidate_* 전수의 docstring을 정적 검사한다.
      측정(2026-09-08): 19개 중 **4개만** 명시. **위반**.
      => 이 검사 자체가 C5의 강제 테스트 원형이다(정적이라 파이프라인 실행 불필요).

  C2  순서 의존 — 단일 setter로 수렴돼 있는가?
      vds 원시 대입이 남아 있는지 센다. 남아 있으면 순서 셔플 불변 테스트가 성립하지 않는다.

실행: assets 디렉터리에서 `python tests/probe_prevention_wiring.py`
(자동 테스트가 아니라 조사용 -- 값을 단정하지 않고 지금 상태를 찍는다. 항목이 PASS로 바뀌면
 그때 `tests/test_*.py`의 정식 테스트로 승격한다.)
"""
import os, sys, re, io, json, inspect
ASSETS = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets"
sys.path.insert(0, ASSETS)
import numpy as np, sizing_recipe as sr

print("=" * 96)
print("C4 — role 라벨 과신: '물리 판정이 항상 우선'이 지켜지는가")
print("=" * 96)
mvbr = {"cascode": 0.2, "tail": 0.3, "mirror": 0.3}
cases = [("headroom_role='cascode'", "cascode"), ("headroom_role='mirror'", "mirror"),
         ("headroom_role 없음(라벨 제거)", None)]
for label, role in cases:
    v = sr._feed_vds_fallback(None, role, mvbr)
    print("  _feed_vds_fallback(declared=None, role=%-8s) -> vds=%.3f" % (repr(role), v))
print("  => 같은 소자라도 **role 문자열만 바뀌면 vds가 달라진다**. 물리(gate==drain)는 보지 않는다.")

trs, meta = sr.load_topology(os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json"))
roles = meta.get("device_roles", {})
diode = [t.name for t in trs if t.gate == t.drain]
by_role = {}
for n in diode:
    r = roles.get(n, {}).get("headroom_role")
    by_role.setdefault(str(r), []).append(n)
print()
print("  diode-connected %d개의 headroom_role 분포:" % len(diode))
for r, ns in sorted(by_role.items(), key=lambda kv: -len(kv[1])):
    print("    %-20s %2d개  %s" % (r, len(ns), ns))
print("  => 물리적으로 동일한 성질(gate==drain)인데 라벨이 4종으로 흩어져 있다.")
print("     라벨을 지우면 결과가 바뀐다 = C4('물리 판정 항상 우선')가 아직 안 지켜졌다는 뜻.")

print()
print("=" * 96)
print("C5 — 게이트가 '검사하지 않는 것'을 docstring에 명시하는가")
print("=" * 96)
src = io.open(os.path.join(ASSETS, "sizing_recipe.py"), encoding="utf-8").read()
gate_names = [n for n in dir(sr)
              if n.startswith(("check_", "verify_", "validate_", "audit_", "revalidate_"))
              and callable(getattr(sr, n, None))]
import stick_diagram as sd
gate_names += ["sd." + n for n in dir(sd)
               if n.startswith(("check_", "verify_", "validate_", "audit_", "revalidate_"))
               and callable(getattr(sd, n, None))]
pat = re.compile(r"검사하지\s*않|안\s*보는\s*것|커버하지\s*않|범위\s*밖|의도적으로\s*안")
have, lack = [], []
for g in gate_names:
    obj = getattr(sd, g[3:]) if g.startswith("sd.") else getattr(sr, g)
    doc = inspect.getdoc(obj) or ""
    (have if pat.search(doc) else lack).append(g)
print("  게이트류 함수 %d개 중" % len(gate_names))
print("    '검사하지 않는 것'을 명시: %d개" % len(have))
for g in have:
    print("        %s" % g)
print("    명시 없음                : %d개" % len(lack))
for g in lack[:14]:
    print("        %s" % g)
if len(lack) > 14:
    print("        ... 외 %d개" % (len(lack) - 14))
print("  => C5 규약은 코드에도, 계획 §7.5에도 강제 장치가 없다.")

print()
print("=" * 96)
print("C2 — 순서 의존: 같은 입력을 다른 순서로 처리하면 결과가 같은가(테스트 가능성 확인)")
print("=" * 96)
print("  vds 기입 지점 7곳(§7.3 v4.3 실측) 중 단일 setter를 거치는 곳: 0곳")
raw = len(re.findall(r'\["vds"\]\s*=', src))
print("  현재 원시 대입 `[\"vds\"] =` 패턴: %d곳 (self-test 포함)" % raw)
print("  => 순서 셔플 불변 테스트가 성립하려면 먼저 set_device_vds() 단일화(v4.3)가 필요하다.")
