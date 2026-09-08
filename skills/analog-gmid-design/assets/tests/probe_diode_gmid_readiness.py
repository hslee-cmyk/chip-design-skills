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
import numpy as np
import sizing_recipe as sr

LUTFILE = os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz")
TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")

trs, meta = sr.load_topology(TOPO)
BY = {t.name: t for t in trs}
DIODE = {n for n, t in BY.items() if sr.is_diode_connected(t)}
print("diode-connected 소자 %d개: %s" % (len(DIODE), sorted(DIODE)))

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
spec = {
    "lut_by_kind": {"nmos": nmos, "pmos": pmos}, "lut": nmos, "vdd": 1.8,
    "L_candidates": [float(v) for v in nmos.L_grid],
    "VDS_candidates": [0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.2, 1.4],
    "gm_id_grid": [float(4 + i) for i in range(21)],
    "L_min": 0.15e-6, "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
    "W_bounds": (1e-6, 200e-6),
    "min_vds_by_role": {"cascode": 0.2, "tail": 0.3, "mirror": 0.3},
    "stage_objective": "power", "stage_w_max": 200e-6,
    "min_finger_w": 1e-6, "max_finger_w": 40e-6,
    "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
    "t_lln": 30e-9, "PM_target_deg": 70.0,
    "Cc": 500e-15, "Cf": 500e-15, "Cs": 500e-15, "C_Ltot": 1e-12,
    "t_settle_total": 40e-9, "omega_c": 6.9 / 30e-9,
    "L_grid_step": 5e-9,
}

print("\n파일럿 단일 평가 실행 중(SLSQP 1 start)...")
try:
    res = sr.optimize_full_circuit_budget(TOPO, spec, search_method="slsqp",
                                          slsqp_kwargs={"n_starts": 1, "maxiter": 5})
    sized = res.get("sized") or res.get("devices") or {}
    print("완료. sized %d개" % len(sized))
except Exception as e:
    import traceback; traceback.print_exc()
    sized = {}

print("\n=== 헤드룸 그룹 해석 진입 시점의 diode 상태(첫 관측만) ===")
first = {}
for vsid, m, g, L, v in OBS:
    first.setdefault(m, (vsid, g, L, v))
print("  %-8s %-28s %-8s %-6s %-6s" % ("소자", "vertical_stack_id", "gm_id?", "L?", "vds?"))
print("  " + "-" * 62)
ready = 0
for m in sorted(first):
    vsid, g, L, v = first[m]
    if g and L:
        ready += 1
    print("  %-8s %-28s %-8s %-6s %-6s" % (m, vsid, "O" if g else "X",
                                             "O" if L else "X", "O" if v else "X"))
covered = set(first)
print("\n  헤드룸 그룹에서 관측된 diode: %d/%d개" % (len(covered), len(DIODE)))
print("  그중 gm_id+L이 이미 있는(=pre-pass 가능) diode: %d개" % ready)
missing = sorted(DIODE - covered)
if missing:
    print("  ⚠️ 헤드룸 그룹 경로에 안 나타난 diode %d개: %s" % (len(missing), missing))
