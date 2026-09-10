# -*- coding: utf-8 -*-
"""L5c 픽스처에서 `L_stage2out_p/n`을 어디에 고정해야 하는가(2026-09-10).

## 왜 필요한가

class-AB 배터리 KVL(`stack_kvl_vgs_limit()`)을 gm_id 탐색에 배선하자, L5c 픽스처가 쓰던
중점 `L_stage2out_p/n = 0.575um`이 **물리적으로 도달 불가능한 점**이 됐다 -- 그 L에서는
`V_bat = vdd - VGS(M15) - VGS(M16)`가 음수다. 이건 v4.29/v4.30에서 `r_cmfb_vocdes`의
중점(0.11)이 도달 불가능해진 것과 **정확히 같은 상황**이고, 그때의 해법도 같았다:
픽스처 본연의 목적(헤드룸 singleton KVL 검증)은 두고 고정점만 실제로 도달 가능한 값으로
옮긴다.

문제는 **어디로 옮기느냐**다. 값을 지어내지 않으려면 재야 한다 -- 이 스크립트는 L5c
픽스처를 그대로 재현해(같은 spec, 같은 theta 고정, 같은 constraint 필터) L을 훑고
**선언된 제약 전부를 만족하는 L이 있는지** 본다.

**아무것도 고치지 않는다 -- 표만 만든다.**

실행: assets 디렉터리에서 `python tests/probe_l5c_stage2out_L.py`
"""
import sys
import os
import json
import tempfile

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
import numpy as np
import sizing_recipe as sr

_RESULT = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first = [True]


def emit(*p):
    line = " ".join(str(x) for x in p)
    print(line, flush=True)
    mode = "w" if _first[0] else "a"
    _first[0] = False
    with open(_RESULT, mode, encoding="utf-8") as f:
        f.write(line + "\n")


LIB = os.path.join(ASSETS, "library")
with open(os.path.join(LIB, "current_reuse_telescopic_ota.topology.json"),
          "r", encoding="utf-8") as f:
    TOPO = json.load(f)

# ── L5c 픽스처와 동일한 theta 고정(L_stage2out_p/n만 이 스크립트가 훑는다) ────────
SWEPT = ("L_stage2out_p", "L_stage2out_n")
for th in TOPO["sizing_roles"]["theta"]:
    if th["name"] == "K_replica":
        th["bounds"] = [0.05, 0.05]
    elif th["name"] == "r_classab_battery":
        th["bounds"] = [0.3, 0.3]
    elif th["name"] == "r_cmfb_vocdes":
        th["bounds"] = [0.02, 0.02]
    elif th["name"] in SWEPT or th["name"] == "L_cascode":
        pass                                   # L_cascode는 원 픽스처에서도 자유
    else:
        lo, hi = th["bounds"]
        mid = (lo + hi) / 2.0
        th["bounds"] = [mid, mid]

# 원 픽스처와 동일: classab_centering_dev_v는 이 검증 범위 밖이라 제외
TOPO["sizing_roles"]["constraints"] = [
    c for c in TOPO["sizing_roles"]["constraints"]
    if c["metric"] != "classab_centering_dev_v"]
CONS = TOPO["sizing_roles"]["constraints"]

d = np.load(os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                       d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                       W_ref=5e-6, SID_1F=d["SID_1F_" + k])
NM, PM = mk("n"), mk("p")
SPEC = {
    "lut_by_kind": {"nmos": NM, "pmos": PM}, "lut": NM, "vdd": 1.8,
    "L_candidates": [float(v) for v in NM.L_grid],
    "VDS_candidates": [float(v) for v in NM.VDS_grid[::4]],
    "gm_id_grid": [4.0, 8.0, 12.0, 16.0, 20.0, 24.0],
    "L_min": 0.15e-6, "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
    "W_bounds": (1e-6, 200e-6), "min_vds_by_role": {"cascode": 0.2, "tail": 0.3, "mirror": 0.3},
    "stage_objective": "power", "stage_w_max": 200e-6,
    "min_finger_w": 1e-6, "max_finger_w": 40e-6,
    "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
    "t_lln": 30e-9, "PM_target_deg": 70.0,
    "Cc": 500e-15, "Cf": 500e-15, "Cs": 500e-15, "C_Ltot": 1e-12,
    "t_settle_total": 40e-9, "omega_c": 6.9 / 30e-9,
    "_spec_source": "L5c self-test 픽스처 재현 -- 그 픽스처의 고정점을 고르려면 같은 "
                    "해상도로 재야 한다(정본보다 성긴 것이 이 조사의 대상 자체다)",
}

emit("=" * 104)
emit("L5c 픽스처: L_stage2out_p/n을 어디에 고정할 것인가 (2026-09-10)")
emit("=" * 104)
emit(f"  제약 {len(CONS)}개: " + ", ".join(f"{c['metric']}{c['op']}{c['value']}" for c in CONS))
emit(f"  gm_id_grid(픽스처) = {SPEC['gm_id_grid']}")

with tempfile.TemporaryDirectory() as tmp:
    path = os.path.join(tmp, "l5c_scan.topology.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(TOPO, f)
    env = sr._build_theta_evaluator(path, SPEC)
    base = {}
    for t in env["thetas"]:
        b = t.get("bounds")
        base[t["name"]] = (float(b[0]) + float(b[1])) / 2.0 if b else 0.0

    emit("")
    emit(f"  {'L(um)':>8}{'평가':>8}{'cmrr':>9}{'psrr':>9}{'gain_db':>9}"
         f"{'gain_full':>11}{'area':>9}{'V_bat':>9}{'centering':>11}   판정")
    emit("  " + "-" * 100)
    rows = []
    for L in [float(v) for v in NM.L_grid if 1.5e-7 <= v <= 1.0e-6]:
        th = dict(base)
        th["L_stage2out_p"] = L
        th["L_stage2out_n"] = L
        try:
            ctx, m = env["evaluate"](th)
        except Exception as e:
            emit(f"  {L*1e6:>8.4f}{'실패':>8}   {type(e).__name__}: {str(e)[:60]}")
            rows.append((L, None, None))
            continue
        bad = [c["metric"] for c in CONS
               if not (m[c["metric"]] >= c["value"] if c["op"] == ">=" else m[c["metric"]] <= c["value"])]
        s = ctx.sized

        def vgs(n):
            e = s[n]
            return SPEC["lut_by_kind"][e["kind"]].vgs_for_gm_id(
                e["gm_id"], e["L"], e["vds"], e.get("vsb", 0.0))
        vb = 1.8 - vgs("M15") - vgs("M16")
        emit(f"  {L*1e6:>8.4f}{'OK':>8}{m['cmrr_estimate_db']:>9.2f}{m['psrr_estimate_db']:>9.2f}"
             f"{m['gain_db']:>9.2f}{m['gain_full_circuit_db']:>11.2f}{m['area_um2']:>9.1f}"
             f"{vb:>9.4f}{m['classab_centering_dev_v']:>11.4f}   "
             + ("전부 만족 ***" if not bad else "위반 " + ",".join(bad)))
        rows.append((L, m, bad))

emit("")
ok = [(L, m) for L, m, bad in rows if m is not None and not bad]
emit(f"  선언된 제약을 전부 만족하는 L: {len(ok)}개")
if ok:
    emit("")
    emit(f"    {'L(um)':>9}{'power_uA':>11}{'area_um2':>11}{'gain_full':>11}")
    emit("    " + "-" * 42)
    for L, m in sorted(ok, key=lambda x: x[1]["power_uA"]):
        emit(f"    {L*1e6:>9.4f}{m['power_uA']:>11.2f}{m['area_um2']:>11.1f}"
             f"{m['gain_full_circuit_db']:>11.2f}")
    emit("")
    emit("    -> objective가 power 최소화이므로 첫 줄이 이 픽스처에서 설계가 고를 값이다.")
else:
    emit("")
    emit("    ★ 전부 만족하는 L이 없다 -- 고정점을 옮기는 것만으로는 이 픽스처를 살릴 수")
    emit("       없다는 뜻이다. 제약을 지우지 말고 사용자와 함께 볼 것.")

emit("")
emit("완료. 결과 파일:", _RESULT)
