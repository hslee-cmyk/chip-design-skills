# -*- coding: utf-8 -*-
"""B1 5단계 착수 전 계측 -- **헤드룸 해석 시점에 diode의 gm_id/L이 이미 있는가**.

step 2(헤드룸 pre-pass에 diode 자기참조 추가)는 그 시점에 `solve_diode_connected_vds()`를
부를 수 있어야 성립한다. 그런데 현재 파이프라인은 `L -> VDS -> gm_id` 순서라, 그 시점에
gm_id가 아직 없을 수 있다 -- 그러면 pre-pass 자체가 성립하지 않고 설계를 바꿔야 한다.
코드 읽기로 단정하지 않고 실주행에 계측을 붙여 직접 센다.

실행: assets 디렉터리에서 `python tests/probe_diode_gmid_readiness.py`
"""
import sys, os, json, collections
ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ASSETS, "..", "..", "..", "workspaces"))
import numpy as np
import sizing_recipe as sr
import run_harness as H


# ---------------------------------------------------------------------------
# 결과는 **파일에도 남긴다**(사용자 지시, 2026-09-08). stdout에만 쓰면
# `| grep | tail` 파이프가 백그라운드 전환 때 버퍼째 날아가, 계산은 성공했는데
# 결과만 잃는다(이 세션에서 실제로 두 번). 한 줄 쓸 때마다 append하므로 중간에
# 죽어도 거기까지는 건진다. 파일은 이 스크립트 옆에 `<이름>.result.txt`로 남는다.
# ---------------------------------------------------------------------------
_RESULT_PATH = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first_emit = [True]


def emit(*parts):
    """print와 같은 시그니처로 쓰되 파일에도 남긴다."""
    line = " ".join(str(p) for p in parts)
    print(line, flush=True)
    mode = "w" if _first_emit[0] else "a"
    _first_emit[0] = False
    with open(_RESULT_PATH, mode, encoding="utf-8") as _f:
        _f.write(line + "\n")



LUTFILE = os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz")
TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")

trs, meta = sr.load_topology(TOPO)
BY = {t.name: t for t in trs}
DIODE = {n for n, t in BY.items() if sr.is_diode_connected(t)}
emit("diode-connected 소자 %d개: %s" % (len(DIODE), sorted(DIODE)))

# ── 계측: _hr_resolve_vertical_group 진입 시점의 diode 상태 ────────────────
OBS = []            # (vsid, name, has_gm_id, has_L, has_vds)
GROUP_SEEN = []
_orig = sr._hr_resolve_vertical_group
def traced(env, vsid):
    members = env.vertical_groups.get(vsid, [])
    ds = [m for m in members if m in DIODE]
    if ds:
        GROUP_SEEN.append(vsid)
        for m in ds:
            e = env.ctx.sized.get(m, {})
            OBS.append((vsid, m, e.get("gm_id") is not None,
                        e.get("L") is not None, e.get("vds") is not None))
    return _orig(env, vsid)
sr._hr_resolve_vertical_group = traced

d = np.load(LUTFILE)
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
spec = H.canonical_spec("current_reuse_telescopic_ota")
nmos = spec["lut_by_kind"]["nmos"]
pmos = spec["lut_by_kind"]["pmos"]

emit("\n파일럿 단일 평가 실행 중(SLSQP 1 start)...")
try:
    res = sr.optimize_full_circuit_budget(TOPO, spec, search_method="slsqp",
                                          slsqp_kwargs={"n_starts": 1, "maxiter": 5})
    sized = res.get("sized") or res.get("devices") or {}
    emit("완료. sized %d개" % len(sized))
except Exception as e:
    import traceback; traceback.print_exc()
    sized = {}

emit("\n=== 헤드룸 그룹 해석 진입 시점의 diode 상태(첫 관측만) ===")
first = {}
for vsid, m, g, L, v in OBS:
    first.setdefault(m, (vsid, g, L, v))
emit("  %-8s %-28s %-8s %-6s %-6s" % ("소자", "vertical_stack_id", "gm_id?", "L?", "vds?"))
emit("  " + "-" * 62)
ready = 0
for m in sorted(first):
    vsid, g, L, v = first[m]
    if g and L:
        ready += 1
    emit("  %-8s %-28s %-8s %-6s %-6s" % (m, vsid, "O" if g else "X",
                                             "O" if L else "X", "O" if v else "X"))
covered = set(first)
emit("\n  헤드룸 그룹에서 관측된 diode: %d/%d개" % (len(covered), len(DIODE)))
emit("  그중 gm_id+L이 이미 있는(=pre-pass 가능) diode: %d개" % ready)
missing = sorted(DIODE - covered)
if missing:
    emit("  ⚠️ 헤드룸 그룹 경로에 안 나타난 diode %d개: %s" % (len(missing), missing))
