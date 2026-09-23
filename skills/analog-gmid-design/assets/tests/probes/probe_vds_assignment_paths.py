# -*- coding: utf-8 -*-
"""파일럿 51소자의 vds가 **실제로 어느 경로에서** 정해지는지 monkeypatch로 계측하는 조사 도구.

계획 문서 §7.3 "B1 해소 -- 티어의 자리를 실측으로 재지정"(v4.3)의 근거를 만든 스크립트다.

배경: v3.0은 diode 티어(gate==drain -> 고정점 solver)를 `resolve_feed_vds()` 안에 넣기로 했다.
그런데 그 함수의 호출자는 2곳뿐이고, 헤드룸을 실제로 배정하는 경로는 그것을 호출하지 않는다.
코드 읽기만으로 단정하지 않으려고 실주행(SLSQP)에 계측을 붙여 직접 셌다.

측정 결과(2026-09-07, current_reuse_telescopic_ota):
    allocate_stack_headroom()             28개 (diode 12)   <- 최대 경로
    (그 밖)                                14개 (diode  4)   <- M18_bg/M66/M36a/M36b
    _metric_stage_budget_vds_by_device()   5개 (diode  0)
    resolve_feed_vds()                     4개 (diode  0)   <- v3.0이 티어를 넣으려던 자리

즉 v3.0안대로면 diode 소자를 **하나도** 덮지 못한다. 사고19가 기록한 실패의 재현이다.

실행: assets 디렉터리에서 `python tests/probe_vds_assignment_paths.py`
(자동 테스트가 아니라 조사용. SLSQP 1 start라 수 분 걸린다.)
"""
import sys, json, copy, tempfile, os, collections
ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # probes -> tests -> assets
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ASSETS, "..", "..", "..", "workspaces"))
import numpy as np
import sizing_recipe as sr
import run_harness as H

LUTFILE = os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz")
TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")

# ── 계측 ───────────────────────────────────────────────────────────────────
ORIGIN = collections.defaultdict(list)      # device -> [(경로, 값)]
CALLS = collections.Counter()

_orig_feed = sr.resolve_feed_vds
def traced_resolve_feed_vds(name, declared_vds, ctx):
    CALLS["resolve_feed_vds"] += 1
    entry = ctx.sized.get(name)
    pre = entry.get("vds") if entry else None
    v = _orig_feed(name, declared_vds, ctx)
    tag = "resolve_feed_vds/tier1(ctx.sized 선점)" if pre is not None else (
          "resolve_feed_vds/tier2(declared)" if declared_vds is not None else
          "resolve_feed_vds/tier3(role 폴백)")
    ORIGIN[name].append((tag, v))
    return v
sr.resolve_feed_vds = traced_resolve_feed_vds

_orig_fb = sr._feed_vds_fallback
def traced_fb(declared_vds, role, mvbr):
    CALLS["_feed_vds_fallback"] += 1
    return _orig_fb(declared_vds, role, mvbr)
sr._feed_vds_fallback = traced_fb

_orig_alloc = sr.allocate_stack_headroom
def traced_alloc(vdd, stack, policy=sr.DEFAULT_POLICY):
    CALLS["allocate_stack_headroom"] += 1
    out = _orig_alloc(vdd, stack, policy)
    for nm, v in out.items():
        ORIGIN[nm].append(("allocate_stack_headroom", v))
    return out
sr.allocate_stack_headroom = traced_alloc

_orig_sbv = getattr(sr, "_metric_stage_budget_vds_by_device", None)
if _orig_sbv:
    def traced_sbv(*a, **k):
        CALLS["_metric_stage_budget_vds_by_device"] += 1
        out = _orig_sbv(*a, **k)
        if isinstance(out, dict):
            for nm, v in out.items():
                ORIGIN[nm].append(("_metric_stage_budget_vds_by_device", v))
        return out
    sr._metric_stage_budget_vds_by_device = traced_sbv

_orig_rvg = sr._hr_resolve_vertical_group
def traced_rvg(env, *a, **k):
    CALLS["_hr_resolve_vertical_group"] += 1
    return _orig_rvg(env, *a, **k)
sr._hr_resolve_vertical_group = traced_rvg

# ── 스모크 러너와 동일 설정(theta 중간값으로 접어 단일 평가) ───────────────
topo = json.load(open(TOPO, encoding="utf-8"))
tmp = TOPO      # 실제 bounds 그대로 -- 진짜 설계점에서 경로를 재야 의미가 있다

d = np.load(LUTFILE)
W_REF = 5e-6
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                       d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                       W_ref=W_REF, SID_1F=d["SID_1F_" + k])
nmos, pmos = mk("n"), mk("p")
# 2026-09-10 -- 손으로 복붙한 spec 블록을 폐기하고 **정본**을 쓴다. 복제본은 정본과
# 갈려 있었다(gm_id_grid 21점 vs 57점, L_candidates 12점 vs 41점, VDS_candidates 9점 vs
# 13점, stage_power_tolerance 누락). 같은 블록이 여러 파일에 그대로 퍼져 있었으므로
# 파일마다 다른 판단을 한 게 아니라 복제본 하나가 번진 것이다. 이제
# `sizing_recipe.require_declared_spec_source()`가 라이브러리 회로에 출처 선언을 강제하고,
# 일부러 다르게 쓸 때는 `H.derived_spec(key, why, **overrides)`로 무엇을 왜 바꿨는지 남긴다.
spec = H.canonical_spec("current_reuse_telescopic_ota")
nmos = spec["lut_by_kind"]["nmos"]
pmos = spec["lut_by_kind"]["pmos"]

print("파일럿 단일 평가 실행 중...")
try:
    res = sr.optimize_full_circuit_budget(tmp, spec, search_method="slsqp",
                                          slsqp_kwargs={"n_starts": 1, "maxiter": 40})
    sized = res.get("sized") or res.get("devices") or {}
    print("완료. sized 소자 %d개" % len(sized))
except Exception as e:
    import traceback; traceback.print_exc()
    sized = {}

print()
print("=== 경로별 호출 횟수 ===")
for k, v in sorted(CALLS.items()):
    print("  %-42s %d" % (k, v))

print()
print("=== 소자별 vds 최종값과 출처 ===")
trs, meta = sr.load_topology(TOPO)
roles = meta.get("device_roles", {})
by_origin = collections.Counter()
rows = []
for t in trs:
    nm = t.name
    e = sized.get(nm) or {}
    vds = e.get("vds")
    org = ORIGIN.get(nm)
    tag = org[-1][0] if org else "(계측 경로 밖)"
    by_origin[tag] += 1
    diode = "diode" if (t.gate == t.drain) else ""
    rows.append((nm, vds, tag, roles.get(nm, {}).get("headroom_role"), diode))
for nm, vds, tag, role, diode in rows:
    print("  %-8s vds=%-7s role=%-22s %-42s %s"
          % (nm, ("%.4f" % vds) if vds is not None else "None", str(role), tag, diode))

print()
print("=== 출처 집계 ===")
for k, v in by_origin.most_common():
    print("  %-42s %d개" % (k, v))
print()
print("=== vds=0.2 로 떨어진 소자 ===")
low = [(nm, role, dio) for nm, vds, tag, role, dio in rows if vds is not None and abs(vds - 0.2) < 1e-9]
print("  %d개: %s" % (len(low), [n for n, _, _ in low]))
print("  그중 diode-connected: %s" % [n for n, _, dio in low if dio])
