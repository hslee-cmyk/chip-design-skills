# -*- coding: utf-8 -*-
"""`apply_diode_self_consistent_gm_id()`의 **skip 분기가 정당한지** 실측으로 검토하는 도구.

사용자 지시(2026-09-08): "타당성을 따지지 않고 skip 로직을 만들지 말 것." 그 pass에는
`continue`가 3개 있는데, 각각이 실제로 몇 개를 건너뛰고 그게 정당한지 세어 본다.

  (S1) entry is None                      -- ctx.sized에 아예 없는 diode
  (S2) _L_source가 권위 있는 출처         -- compensation/metric_stage_budget/
                                             gm_target_convention이 이미 gm_id를 정함
  (S3) L/vds/ID 중 하나라도 없거나 ID<=0  -- 유도할 근거가 없음

정당성 판정 기준:
  - S1이 0개면 "있을 수 없는 경우"라 방어적 분기이고, 0이 아니면 **왜 없는지** 설명이 필요하다.
  - S2는 그 경로가 vds를 `set_device_vds()`로 기입해 **거기서 이미 검사받는가**에 달렸다.
    검사받지 않는다면 이 skip은 물리 검사를 통째로 비켜가게 하는 구멍이다.
  - S3은 "아직 안 채워진 것"인지 "영영 안 채워지는 것"인지 구분해야 한다. 후자면 조용히
    넘어가면 안 된다.

주의: 격자탐색(grid_points_per_theta)은 못 쓴다 -- theta가 22개라 2점씩만 잡아도
2^22 조합이고, 1점으로 줄이면 `_theta_grid_points()`의 `i/(n-1)`이 ZeroDivisionError를
낸다(비-L theta가 있을 때 걸리는 **기존 결함**, 이 배선과 무관). 그래서 SLSQP 1 start.

실행: assets 디렉터리에서 `python tests/probe_diode_pass_skips.py`
"""
import sys
import os
import json
import collections

ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # probes -> tests -> assets
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



TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
LUTFILE = os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz")

trs, meta = sr.load_topology(TOPO)
DIODE = sorted(n for n, t in {t.name: t for t in trs}.items() if sr.is_diode_connected(t))
emit("diode-connected %d개: %s" % (len(DIODE), DIODE))
emit()

STATS = collections.Counter()
DETAIL = {}
_orig = sr.apply_diode_self_consistent_gm_id


def traced(ctx, spec, kind_of, gm_id_tol=1e-3):
    for name in DIODE:
        e = ctx.sized.get(name)
        if e is None:
            STATS["S1_entry_없음"] += 1
            DETAIL.setdefault(name, "S1 entry 없음")
        elif e.get("_L_source") in sr._AUTHORITATIVE_GM_ID_SOURCES:
            STATS["S2_권위출처"] += 1
            DETAIL.setdefault(name, "S2 _L_source=%r / _vds_source=%r"
                               % (e.get("_L_source"), e.get("_vds_source")))
        elif (e.get("L") is None or e.get("vds") is None
              or e.get("ID") is None or e.get("ID", 0) <= 0):
            STATS["S3_근거부족"] += 1
            DETAIL.setdefault(name, "S3 L=%s vds=%s ID=%s"
                               % (e.get("L"), e.get("vds"), e.get("ID")))
        else:
            STATS["처리됨"] += 1
            DETAIL.setdefault(name, "처리 (vds=%.4f, _vds_source=%r)"
                               % (e["vds"], e.get("_vds_source")))
    return _orig(ctx, spec, kind_of, gm_id_tol)


sr.apply_diode_self_consistent_gm_id = traced

d = np.load(LUTFILE)
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                        d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                        W_ref=5e-6, SID_1F=d["SID_1F_" + k])
nmos, pmos = mk("n"), mk("p")
# 2026-09-10 -- 손으로 복붙한 spec 블록을 폐기하고 **정본**을 쓴다. 복제본은 정본과
# 갈려 있었다(gm_id_grid 21점 vs 57점, L_candidates 12점 vs 41점, VDS_candidates 9점 vs
# 13점, stage_power_tolerance 누락). 같은 블록이 여러 파일에 그대로 퍼져 있었으므로
# 파일마다 다른 판단을 한 게 아니라 복제본 하나가 번진 것이다. 이제
# `sizing_recipe.require_declared_spec_source()`가 라이브러리 회로에 출처 선언을 강제한다.
spec = H.canonical_spec("current_reuse_telescopic_ota")
nmos = spec["lut_by_kind"]["nmos"]
pmos = spec["lut_by_kind"]["pmos"]

emit("파일럿 평가 1점 실행 중...")
err = None
try:
    sr.optimize_full_circuit_budget(TOPO, spec, search_method="slsqp",
                                    slsqp_kwargs={"n_starts": 1, "maxiter": 3})
except Exception as e:                       # 실패해도 계측값은 남는다
    err = "%s: %s" % (type(e).__name__, str(e)[:220])

emit()
emit("=== skip 분기별 집계(첫 관측 기준) ===")
for k in ("처리됨", "S1_entry_없음", "S2_권위출처", "S3_근거부족"):
    emit("  %-16s %d개" % (k, STATS[k]))
emit()
emit("=== 소자별 ===")
for n in DIODE:
    emit("  %-8s %s" % (n, DETAIL.get(n, "(pass가 호출되지 않음)")))
if err:
    emit()
    emit("평가 결과: %s" % err)
