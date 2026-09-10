# -*- coding: utf-8 -*-
"""미러 동치류의 **L이 실제로 갈려 있는가**, 그리고 무엇이 각 L을 정하는가(2026-09-10).

## 배경 -- 사용자가 확정한 설계 원칙

> "tail이 bias generation하는 mirror와 L이 다르면 전류비가 실제 실리콘에서는 PVT때문에
>  정확하지 않을 수 있잖아. ... L값이 중요한 stage의 tail의 공통 L을 탐색하고 그 L값으로
>  mirror단의 L은 모두 같이 사용해야 하는 것이지."
> "M5가 주인이야."

물리적 근거는 미러비 식 자체다. 전류미러의 비는

    ID2/ID1 = (W2/L2) / (W1/L1)

인데, **L1 == L2일 때만** 이것이 순수한 W 비(=레이아웃 비, PVT에 강함)로 축약된다. L이
다르면 비가 이동도/Vth/채널길이변조의 L 의존성을 타고 공정·전압·온도에 따라 흔들린다.

## 지금 엔진은 어떻게 하고 있나

`select_L_by_role()`이 `_L_ROLE_MULTIPLIERS = {"mirror": 2.5, "bias_replica": 1.2}`로
**role별 고정배수**를 준다(knee = 2.5 x L_min). 미러 상대가 tail이든 무엇이든 상관없이
자기 role의 배수를 쓴다 -- 즉 **미러비를 PVT에 취약하게 만드는 바로 그 상태**다.

## 무엇을 재는가 (회로 이름을 박지 않는다 -- 선언에서 유도한다)

  1. `gm_id_match_vgs_of`(+`same_as_device`)로 **동치류**를 만든다. 이 필드는 "게이트·소스를
     물리적으로 공유하는 진짜 전류미러"라는 뜻이므로(B19', 사용자 확정), 같은 류의 소자는
     VGS가 KVL로 이미 강제 동일하다. 미러비가 PVT에 강하려면 **L도 같아야** 한다.
  2. 실제 사이징 결과에서 각 류의 L이 몇 종으로 갈리는지, 그리고 각 L을 **무엇이** 정했는지
     (theta / compensation / L_role 배수) 센다.
  3. L이 갈린 류마다 미러비 오차가 얼마인지 본다(`mirror_ratio_error_pct`의 근원).

**아무것도 고치지 않는다 -- 표만 만든다.**

실행: assets 디렉터리에서 `python tests/probe_mirror_common_L_wiring.py`
"""
import sys
import os
import json
import collections

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


emit("=" * 104)
emit("미러 동치류의 L이 갈려 있는가 -- 4개 회로 전수 (2026-09-10)")
emit("=" * 104)
emit("")
emit(f"  현재 규칙: _L_ROLE_MULTIPLIERS = {sr._L_ROLE_MULTIPLIERS}  (role별 고정배수)")
emit("  미러비가 PVT에 강하려면 ID2/ID1 = (W2/L2)/(W1/L1)이 순수 W비로 축약돼야 하고,")
emit("  그건 L1==L2일 때만 성립한다.")

THETA_STAR = os.path.join(ASSETS, "tests", "canonical_theta_star.json")

for key, cfg in H.SPECS.items():
    topo = os.path.join(ASSETS, "library", cfg["topology_file"])
    spec = cfg["spec_fn"]()
    emit("")
    emit("-" * 104)
    emit(f"[{key}]")
    emit("-" * 104)
    trs, meta = sr.load_topology(topo)
    roles = meta.get("device_roles") or {}

    # ── 동치류: gm_id_match_vgs_of(+same_as_device)를 union-find로 ──────────────
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    alias = sr.vgs_alias_map(meta)
    for a, b in alias.items():
        union(a, b)
    for n, r in roles.items():
        if isinstance(r, dict) and r.get("same_as_device"):
            union(n, r["same_as_device"])
    classes = collections.defaultdict(list)
    for n in list(parent):
        classes[find(n)].append(n)
    classes = {k: sorted(v) for k, v in classes.items() if len(v) > 1}
    if not classes:
        emit("  gm_id_match_vgs_of/same_as_device 선언이 없다 -- 이 회로엔 동치류가 없다")
        continue
    emit(f"  선언에서 유도된 동치류 {len(classes)}개")

    # ── 실제 사이징 ─────────────────────────────────────────────────────────
    try:
        ev = sr._build_theta_evaluator(topo, spec)
        theta = {}
        if key == "current_reuse_telescopic_ota" and os.path.exists(THETA_STAR):
            theta = json.load(open(THETA_STAR, encoding="utf-8"))
            emit("  (theta_star 재사용 -- tests/canonical_theta_star.json)")
        else:
            theta = {t["name"]: (float(t["bounds"][0]) + float(t["bounds"][1])) / 2.0
                     if t.get("bounds") else 0.0 for t in ev["thetas"]}
            emit("  (theta = bounds 중점)")
        ctx, _m = ev["evaluate"](theta)
        sized = ctx.sized
    except Exception as e:
        emit(f"  ★ 사이징 실패: {type(e).__name__}: {str(e)[:160]}")
        continue

    # ── L이 어디서 왔나 ─────────────────────────────────────────────────────
    theta_devices = {}
    for th in ev["thetas"]:
        f = th.get("feeds")
        if isinstance(f, dict) and f.get("type") == "metric_stage_budget":
            for d in (f.get("devices") or []):
                theta_devices[d] = th["name"]

    def l_source(n):
        if n in theta_devices:
            return f"theta:{theta_devices[n]}"
        r = (roles.get(n) or {}).get("L_role")
        if r:
            return f"L_role:{r}(x{sr._L_ROLE_MULTIPLIERS.get(r, '?')})"
        return "compensation/기타"

    emit("")
    emit(f"    {'동치류(레퍼런스)':<14}{'소자수':>6}{'L 종수':>7}   L(um)별 소자 / 출처")
    emit("    " + "-" * 92)
    n_split = 0
    for root, members in sorted(classes.items()):
        by_L = collections.defaultdict(list)
        for m in members:
            e = sized.get(m)
            if not e or e.get("L") is None:
                by_L["(미사이징)"].append(m)
                continue
            by_L[round(e["L"] * 1e6, 4)].append(m)
        n_kinds = len([k for k in by_L if k != "(미사이징)"])
        if n_kinds > 1:
            n_split += 1
        emit(f"    {root:<14}{len(members):>6}{n_kinds:>7}   " +
             ("★갈림" if n_kinds > 1 else "OK"))
        for L, ms in sorted(by_L.items(), key=lambda kv: str(kv[0])):
            srcs = sorted({l_source(m) for m in ms})
            emit(f"        L={str(L):<9} {len(ms):>2}개  {', '.join(ms[:8])}"
                 + (" ..." if len(ms) > 8 else ""))
            emit(f"          출처: {', '.join(srcs)}")
    emit("")
    emit(f"    -> L이 갈린 동치류: {n_split} / {len(classes)}")

emit("")
emit("=" * 104)
emit("해석")
emit("=" * 104)
emit("")
emit("  같은 동치류인데 L이 갈렸다는 것은, 그 미러비가 W비만으로 정해지지 않고")
emit("  L 의존 항(이동도/Vth/채널길이변조)을 타고 PVT에 흔들린다는 뜻이다.")
emit("  선언(gm_id_match_vgs_of)은 이미 '이들은 진짜 전류미러'라고 말하고 있는데,")
emit("  L 배정만 그 선언을 안 보고 role 고정배수를 쓰고 있다.")
emit("")
emit("완료. 결과 파일:", _RESULT)
