# -*- coding: utf-8 -*-
"""파일럿의 **6개 계기판 metric을 한 번에** 찍는 도구(계획 §0.4 검증 절차).

계획 §0.1이 만든 대시보드를 재현 가능한 스크립트로 굳힌 것이다. 엔진을 고칠 때마다
"이 수정이 물리적으로 옳은 방향인가"를 이 6개 숫자로 판정한다.

  power_uA               직렬 중복 포함(A3) -- 진짜 전력이 아니다
  supply_current_uA      진짜 공급전류(A3)
  kcl_residual_uA        전류 정합성 위반(B8)
  mirror_ratio_error_pct 미러비 계통 오차(A4)
  stack_headroom_slack_v 스택 KVL 여유, 음수면 그 스택이 성립 안 함(A8)
  gain_db

## 이력

    시점                              power  supply  kcl    mirror  slack   gain
    2026-09-08 세션45(기준)           243.32  86.27  3.96   63.61   -1.35   56.98
    (아래 실행 결과가 현재 값)

실행: assets 디렉터리에서 `python tests/probe_metric_dashboard.py`
(SLSQP 1 start라 수 분 걸린다.)
"""
import sys
import os

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
import numpy as np
import sizing_recipe as sr


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



TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
LUTFILE = os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz")

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

emit("LUT L 앵커(um):", [round(float(x) * 1e6, 4) for x in d["L"]])
emit("파일럿 SLSQP 1 start 실행 중...")
res = sr.optimize_full_circuit_budget(TOPO, spec, search_method="slsqp",
                                       slsqp_kwargs={"n_starts": 1, "maxiter": 40})
m = res.get("metrics") or {}
sized = res.get("sizing") or {}

BASE = {"power_uA": 243.32, "supply_current_uA": 86.27, "kcl_residual_uA": 3.96,
        "mirror_ratio_error_pct": 63.61, "stack_headroom_slack_v": -1.35,
        "gain_db": 56.98}

emit()
emit("=== 계기판 ===")
emit("%-24s %-14s %-14s %s" % ("metric", "세션45 기준", "현재", "변화"))
emit("-" * 64)
for k in ("power_uA", "supply_current_uA", "kcl_residual_uA",
          "mirror_ratio_error_pct", "stack_headroom_slack_v", "gain_db"):
    cur = m.get(k)
    b = BASE[k]
    if cur is None:
        emit("%-24s %-14.4f %-14s (metric 미선언/미계산)" % (k, b, "-"))
        continue
    emit("%-24s %-14.4f %-14.4f %+.4f" % (k, b, cur, cur - b))

emit()
emit("=== 면적 ===")
# v3.3의 핵심 제약이 면적인데 계기판에 없었다(2026-09-08 추가). `area_um2` metric은
# 파일럿 topology.json에 선언돼 있지 않으므로 sized에서 직접 합산한다.
trs, _meta = sr.load_topology(TOPO)
_diode = {tr.name for tr in trs if sr.is_diode_connected(tr)}
_ar = lambda names=None: sum(
    v["W"] * v["L"] for k, v in sized.items()
    if v.get("W") and v.get("L") and (names is None or k in names))
emit("  총 면적        %10.2f um^2" % (_ar() * 1e12))
emit("  diode 16개     %10.2f um^2 (%.1f%%)" % (_ar(_diode) * 1e12,
                                                 _ar(_diode) / _ar() * 100))
emit("  그 외 35개     %10.2f um^2" % ((_ar() - _ar(_diode)) * 1e12))
emit("  v3.3 예시 예산 200um^2 대비: %.1f배" % (_ar() * 1e12 / 200))

emit()
emit("=== diode 소자의 vds/gm_id 출처 ===")
diode = sorted(n for n, tr in {tr.name: tr for tr in trs}.items()
               if sr.is_diode_connected(tr))
emit("%-8s %-9s %-9s %-11s %s" % ("소자", "vds(V)", "gm_id", "W(um)", "_vds_source"))
emit("-" * 76)
for n in diode:
    e = sized.get(n) or {}
    emit("%-8s %-9s %-9s %-11s %s"
          % (n,
             ("%.4f" % e["vds"]) if e.get("vds") is not None else "-",
             ("%.3f" % e["gm_id"]) if e.get("gm_id") is not None else "-",
             ("%.3f" % (e["W"] * 1e6)) if e.get("W") is not None else "-",
             e.get("_vds_source", "-")))
