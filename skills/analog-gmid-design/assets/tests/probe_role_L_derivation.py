# -*- coding: utf-8 -*-
"""`L_role` 배수 상수를 **유도**로 대체한 결과를 4개 회로 전수로 잰다 (2026-09-10).

사용자 지시: *"bias_replica 상수도 없애"* -> (전 회로 적용).

무엇을 재는가 (회로 이름을 코드에 박지 않는다 -- `run_harness.SPECS`를 순회한다):

  1. `L_role`이 선언된 소자마다 새 규칙이 실제로 **유도**됐는가(`_L_source ==
     "L_role_derived"`), 아니면 상수 폴백(`"L_role"`)으로 떨어졌는가.
  2. 유도된 L이 옛 상수(`L_min x _L_ROLE_MULTIPLIERS[role]`)와 얼마나 다른가.
  3. clamp가 실제로 물렸는가 -- knee, 실현가능 창 `(lo,hi)`, 최종 L을 나란히 본다.

**아무것도 고치지 않는다 -- 표만 만든다.**

실행: assets 디렉터리에서 `python tests/probe_role_L_derivation.py`
"""
import sys
import os
import json

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ASSETS, "..", "..", "..", "workspaces"))
import sizing_recipe as sr
import run_harness as H

_RESULT = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first = [True]


def emit(*p):
    line = " ".join(str(x) for x in p)
    print(line, flush=True)
    with open(_RESULT, "w" if _first[0] else "a", encoding="utf-8") as f:
        f.write(line + "\n")
    _first[0] = False


emit("=" * 108)
emit("L_role 상수 -> 유도 전환 결과 (4개 회로 전수)")
emit("=" * 108)
emit("  옛 규칙(실효): mirror = knee(§7.10 C1/C9로 이미 대체됨), bias_replica = L_min x 1.2 (상수)")
emit("  새 규칙: L = clamp(knee_L_for_kind(LUT 실측), feasible_L_window(선언 W_bounds + 실제 ID))")

# 2026-09-10 이전의 _L_ROLE_MULTIPLIERS(삭제됨) -- 비교 기준으로만 남긴다.
_OLD_MULT = {"mirror": 2.5, "bias_replica": 1.2}

THETA_STAR = os.path.join(ASSETS, "tests", "canonical_theta_star.json")
TOT = {"derived": 0, "fallback": 0, "clamped": 0, "changed": 0}

for key, cfg in H.SPECS.items():
    topo = os.path.join(ASSETS, "library", cfg["topology_file"])
    spec = H.canonical_spec(key)
    emit("")
    emit("-" * 108)
    emit(f"[{key}]")
    trs, meta = sr.load_topology(topo)
    roles = meta.get("device_roles") or {}
    targets = {n: r["L_role"] for n, r in roles.items()
               if isinstance(r, dict) and r.get("L_role")}
    if not targets:
        emit("  L_role 선언이 없다 -- 이 변경은 이 회로에서 무동작이다")
        continue
    emit(f"  L_role 선언 소자 {len(targets)}개")
    try:
        ev = sr._build_theta_evaluator(topo, spec)
        if key == "current_reuse_telescopic_ota" and os.path.exists(THETA_STAR):
            theta = json.load(open(THETA_STAR, encoding="utf-8"))
            theta = {t["name"]: theta.get(t["name"],
                     (float(t["bounds"][0]) + float(t["bounds"][1])) / 2.0)
                     for t in ev["thetas"]}
        else:
            theta = {t["name"]: (float(t["bounds"][0]) + float(t["bounds"][1])) / 2.0
                     if t.get("bounds") else 0.0 for t in ev["thetas"]}
        ctx, _m = ev["evaluate"](theta)
    except Exception as e:
        emit(f"  ★ 사이징 실패: {type(e).__name__}: {str(e)[:200]}")
        continue

    emit("")
    emit(f"    {'소자':<8} {'role':<13} {'출처':<17} {'knee':>8} {'창 lo':>8} {'창 hi':>8}"
         f" {'최종 L':>8} {'옛 상수':>8}  {'목표점':<13} 비고")
    hdr_done = True
    for name in sorted(targets):
        e = ctx.sized.get(name) or {}
        src = e.get("_L_source", "-")
        if src not in ("L_role", "L_role_derived"):
            continue          # theta/compensation 등 더 권위 있는 출처가 이겼다
        role = targets[name]
        kind = ctx.kind_of.get(name)
        lut = (spec.get("lut_by_kind") or {}).get(kind)
        knee = lo = hi = None
        if lut is not None:
            try:
                knee = sr.knee_L_for_kind(lut, spec)
            except (KeyError, ValueError):
                knee = None
            ID = e.get("ID")
            if knee and ID and ID > 0:
                vl = sorted(float(v) for v in (spec.get("VDS_candidates") or ()) if v > 0)
                # 엔진과 **같은 호출**을 해야 표가 사실이다 -- diode는 gm_id가 자유롭지
                # 않아 판정이 다르다(feasible_L_window의 diode_kind/vds_is_fixed).
                _dk = kind if name in sr._diode_set_cached(topo) else ""
                lo, hi = sr.feasible_L_window(
                    lut, ID, e.get("vds") or vl[len(vl) // 2], e.get("vsb", 0.0),
                    spec["L_candidates"], spec["gm_id_grid"],
                    spec.get("W_bounds", (1e-6, 200e-6)),
                    diode_kind=_dk, vds_is_fixed=bool(e.get("vds")))
        L_min = spec.get("L_min_by_kind", {}).get(kind, spec.get("L_min"))
        # 옛 **실효** 동작: mirror는 이미 §7.10 C1/C9가 knee로 대체했고(고정배수 2.5는
        # knee를 못 잴 때만 나왔다), 상수가 실제로 값을 정하던 건 bias_replica뿐이다.
        old = knee if (role == "mirror" and knee) else L_min * _OLD_MULT[role]
        tgt = sr._L_ROLE_TARGETS.get(role, "?")
        L = e.get("L")
        note = []
        if src == "L_role_derived":
            TOT["derived"] += 1
            if knee and L and abs(L - knee) > 1e-15:
                note.append("clamp됨"); TOT["clamped"] += 1
        else:
            TOT["fallback"] += 1
            note.append("★상수 폴백")
        if L and abs(L - old) > 1e-15:
            TOT["changed"] += 1
        u = lambda v: f"{v * 1e6:.3f}" if v else "  -  "
        emit(f"    {name:<8} {role:<13} {src:<17} {u(knee):>8} {u(lo):>8} {u(hi):>8}"
             f" {u(L):>8} {u(old):>8}  {tgt:<13} {' '.join(note)}")

emit("")
emit("=" * 108)
emit(f"  유도 성공 {TOT['derived']}개 / 상수 폴백 {TOT['fallback']}개 "
     f"(그중 clamp가 물린 것 {TOT['clamped']}개, 옛 상수와 값이 달라진 것 {TOT['changed']}개)")
emit("=" * 108)
