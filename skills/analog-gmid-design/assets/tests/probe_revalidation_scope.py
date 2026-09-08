# -*- coding: utf-8 -*-
"""레이아웃 재검증이 **어느 metric을 건너뛰는지** 재는 조사 도구(2026-09-08).

## 배경 -- W가 왜 커지는가, 왜 아무도 못 잡는가

면적 제약이 조용히 깨지는 것을 추적한 두 번째 결함. 매칭 gm_id 전파를 고친 뒤에도
`area_um2 <= 800`을 걸면 SLSQP는 792.87um^2를 내는데 최종은 943.42um^2로 위반한다.

**W가 커지는 기전**: `_sync_finger_fixup()`이 `w = n_fingers * finger_w`로 W를 다시
쓴다. euler/common-centroid 배치를 위해 `n_fingers`를 늘리면 **핑거 폭은 그대로 두고
개수만 늘리므로 W가 비례해 커진다**(M2a/M2b: 24.515 -> 99.785um, n_fingers=6).
이건 레이아웃이 실제로 요구하는 것이라 그 자체는 정당하다.

**왜 아무도 못 잡는가**: 재검증(`revalidate_finger_override()`)은 이미 있는데,
"영향받는 metric만 다시 계산한다"는 최적화가 이렇게 돼 있다:

    affected_metrics = {m for m, spec in metrics_specs.items()
                        if _collect_device_refs(spec, known_names) & set(overrides)}

`_collect_device_refs()`는 **spec 안에 이름이 적힌 소자**만 모은다. 그런데
`area_um2`의 선언은 `{"type":"sum_area","unit":"um^2"}`로 `devices` 키가 없고,
계산기는 `spec.get("devices") or list(ctx.sized.keys())`로 **전 소자**를 쓴다.
참조 수집기가 빈 집합을 돌려주니 교집합이 비고, **"무관"으로 분류돼 건너뛴다**.

## 측정 결과 (2026-09-08, 파일럿 17개 metric)

**전 소자를 쓰는데 재검증에서 건너뛰는 metric 6개**:

    power_uA (목적함수!), area_um2, mirror_ratio_error_pct,
    supply_current_uA, kcl_residual_uA, stack_headroom_slack_v

**소자를 하나도 명시하지 않아 역시 건너뛰는 전체회로 metric 3개**:

    cmrr_estimate_db (제약!), psrr_estimate_db (제약!), gain_full_circuit_db

즉 선언된 제약 5개 중 `gain_db` 하나만 재검증되고, 전체회로 MNA 제약인 cmrr/psrr는
**W가 바뀌어도 다시 계산되지 않는다**. 목적함수 `power_uA`조차 그렇다.

`_collect_device_refs()`의 docstring은 "_METRICS_REGISTRY 9종 확인"이라고 적혀 있는데
그 뒤로 레지스트리가 커졌고, 새로 추가된 metric들은 전부 전 소자를 읽는다.

## 판단

"참조가 안 보이면 무관"은 **안전한 방향이 반대다**. 독립임을 적극적으로 확인했을 때만
건너뛰어야 하고, 모르면 다시 계산해야 한다(§3.2 P1 -- 조용한 실패 금지). 즉 `devices`를
명시하지 않은 spec은 **전 소자 의존**으로 보는 게 맞다. 미수정 -- 공유 엔진 변경이라
승인 대상.

실행: assets 디렉터리에서 `python tests/probe_revalidation_scope.py`
"""
import sys, os, json
ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
import sizing_recipe as sr
OUT = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
def emit(*p):
    line=" ".join(str(x) for x in p); print(line, flush=True)
    with open(OUT,"a",encoding="utf-8") as f: f.write(line+"\n")
open(OUT,"w").close()

TOPO = os.path.join(ASSETS,"library","current_reuse_telescopic_ota.topology.json")
topo = json.load(open(TOPO,encoding="utf-8"))
specs = topo["sizing_roles"]["metrics"]
cons = {c["metric"] for c in topo["sizing_roles"]["constraints"]}
trs,_ = sr.load_topology(TOPO)
known = {t.name for t in trs}
# 레이아웃이 실제로 건드리는 소자(실측에서 M2a/M2b)
overrides = {"M2a","M2b"}

emit("파일럿 metric %d개 -- 재검증이 '영향 있음'으로 볼까?" % len(specs))
emit("(레이아웃이 바꾼 소자: %s)" % sorted(overrides))
emit()
emit("%-26s %-9s %-10s %-30s %s" % ("metric","제약?","판정","spec이 참조하는 소자","실제 계산 대상"))
emit("-"*104)
ALL_DEVICE_METRICS = {"sum_area","sum_current","supply_current","kcl_residual",
                      "mirror_ratio_error","stack_headroom_slack","pelgrom_mismatch"}
for name, spec in sorted(specs.items()):
    refs = sr._collect_device_refs(spec, known)
    affected = bool(refs & overrides)
    t = spec.get("type") if isinstance(spec, dict) else spec
    implicit_all = (isinstance(spec,dict) and not spec.get("devices")
                    and t in ALL_DEVICE_METRICS)
    scope = "전 소자(암묵)" if implicit_all else ("%d개 명시" % len(refs) if refs else "(참조 없음)")
    verdict = "재검증함" if affected else "★건너뜀"
    flag = "  <-- 전 소자를 쓰는데 건너뛴다" if (implicit_all and not affected) else ""
    emit("%-26s %-9s %-10s %-30s %s%s"
         % (name, "예" if name in cons else "", verdict,
            (", ".join(sorted(refs))[:28] if refs else "-"), scope, flag))
emit()
skipped_global = [n for n,s in specs.items()
                  if isinstance(s,dict) and not s.get("devices")
                  and s.get("type") in ALL_DEVICE_METRICS
                  and not (sr._collect_device_refs(s,known) & overrides)]
emit("전 소자를 쓰는데 재검증에서 건너뛰는 metric %d개: %s" % (len(skipped_global), skipped_global))
emit("그중 제약으로 걸려 있는 것: %s" % sorted(set(skipped_global) & cons))
