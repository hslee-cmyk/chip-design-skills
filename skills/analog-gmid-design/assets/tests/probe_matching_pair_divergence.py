# -*- coding: utf-8 -*-
"""**매칭 쌍의 사이징이 실제로 같은지** 전수로 재는 조사 도구(2026-09-08).

## 왜

면적 제약이 조용히 깨지는 것을 추적하다 발견했다. `area_um2 <= 900`을 걸었을 때
SLSQP는 **867.95um^2의 실현가능한 해**를 찾는데, 최종 반환값은 **1050.40um^2**로 제약을
위반한다. 차이 182.45um^2는 전부 **M2a/M2b 두 소자**에서 나온다:

    M2b  W 1.107um  -> 104.036um   (+102.9um^2)
    M2a  W 24.515um -> 104.036um   (+79.5um^2)

M2a/M2b는 `symmetry.matching_pairs`에 `current_forced=true`로 선언된 매칭 쌍이고
M2b는 `same_as_device="M2a"`로 VDS까지 강제된다. 그런데 **사이징이 두 소자에 22배 다른
W를 준다**. 레이아웃의 matching-safety 복구가 그걸 같게 맞추면서 면적이 21% 늘고, 그
시점에는 아무도 제약을 다시 확인하지 않는다.

## 무엇을 재나

`W = L * ID / IDu(gm_id, L, vds, vsb)`이므로 W가 갈리려면 L/ID/gm_id/vds/vsb 중 하나가
갈려야 한다. 선언된 **모든 매칭 쌍**에 대해 그 다섯 값을 나란히 찍어 **어느 축이
갈리는지** 본다. M2a/M2b만의 문제인지, 매칭 강제가 사이징 단계에 아예 없는 것인지를
구분하는 게 목적이다.

⚠️ 이 스크립트는 원인을 **지목만** 한다 -- 고치지 않는다. `matching_sensitivity`가
`ratio`인 쌍은 W가 달라도 되는 경우가 있으므로(의도된 비율), 판정은 사람이 한다.

## 측정 결과 (2026-09-08, 12앵커 LUT)

선언된 매칭 쌍 21개 중 **6개가 갈린다**. 두 부류로 뚜렷하게 나뉜다.

**(가) 명백한 결함 3쌍 -- L/ID/vds/vsb가 전부 같은데 gm_id만 다르다.**
같은 동작점이면 gm_id도 같아야 하므로 변명의 여지가 없다.

    쌍            L(um)   ID(uA)   vds     gm_id            W(um)
    M2a/M2b       1.000   6.1701   0.200   15.0  / 2.5      24.5151 / 1.1070
    M3a/M3b       1.000   6.1701   0.200   15.0  / 7.5       4.3279 / 1.0214
    M37a/M37b     0.350  11.1242   0.200   17.23 / 9.5       5.0000 / 1.0115

**(나) 판단 보류 3쌍** -- ID/vds 자체가 다른 `ratio` 매칭이라 W가 달라도 될 수 있다
(`M18_bg`+6소자 / `M18_bg`+M60/M61 / M10·M12·M19·M21). 미러비가 의도된 것인지
사람이 판정해야 한다.

## 기전 -- 두 소자가 서로 다른 경로로 gm_id를 받는다

    M2a   _L_source = "metric_stage_budget"                -> 권위 있는 출처
    M2b   _L_source = "metric_stage_budget_vds_deferred"   -> 권위 목록에 **없음**

`_AUTHORITATIVE_GM_ID_SOURCES = {compensation, metric_stage_budget, gm_target_convention}`
이라 M2a는 `gm_id_role` 루프가 건너뛰고 feed가 준 15.0을 유지하는데, M2b는 `deferred`
태그라 그 루프가 처리해 `search_gm_id_for_role("matching")`이 독립적으로 2.5를 준다.
M37a/M37b도 같다(`gm_target_convention` vs `L_role`).

## 근본 원인 -- 엔진이 매칭 쌍에 L만 전파하고 gm_id는 전파하지 않는다

`optimize_full_circuit_budget()`의 `for _p in pairs_meta:` 루프는 **L만** 다룬다 --
한쪽만 있으면 복사하고, 둘 다 있는데 다르면 `_AUTHORITATIVE_L_SOURCES`로 우선순위를
가리고, 그것도 안 되면 **명시적으로 실패**한다. 잘 만들어진 로직이다.

**그런데 gm_id에는 그 대응물이 아예 없다.** VDS는 `same_as_device`/vertical stack이
따로 강제하고 W는 gm_id에서 유도되므로, 결국 **gm_id 하나만 무방비**다.

## 파급 -- 면적 제약이 조용히 깨진다

레이아웃의 matching-safety 복구가 M2a/M2b를 나중에 같게 맞추는데(둘 다 104.036um,
원래 값 둘 다보다 크다) 그 시점에는 아무도 제약을 다시 확인하지 않는다. 그래서
`area_um2 <= 900`을 걸면 SLSQP는 867.95um^2의 실현가능한 해를 내는데 최종 반환은
1050.40um^2가 되고 **위반이 보고되지 않는다**(+182.45um^2 전부가 M2a/M2b에서 나온다).

실행: assets 디렉터리에서 `python tests/probe_matching_pair_divergence.py`
"""
import sys
import os
import json

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
import numpy as np
import sizing_recipe as sr


_RESULT_PATH = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first_emit = [True]


def emit(*parts):
    line = " ".join(str(p) for p in parts)
    print(line, flush=True)
    mode = "w" if _first_emit[0] else "a"
    _first_emit[0] = False
    with open(_RESULT_PATH, mode, encoding="utf-8") as _f:
        _f.write(line + "\n")


TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
d = np.load(os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                        d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                        W_ref=5e-6, SID_1F=d["SID_1F_" + k])
nmos, pmos = mk("n"), mk("p")
SPEC = {
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

# 사이징 직후(레이아웃 복구 **전**) 상태를 잡는다 -- 복구가 덮어쓰기 전의 진짜 사이징 결과.
PRE = {}
_orig = sr._optimize_theta_slsqp


def traced(*a, **k):
    th, sz, mt = _orig(*a, **k)
    PRE.clear()
    PRE.update({kk: dict(vv) for kk, vv in sz.items()})
    return th, sz, mt


sr._optimize_theta_slsqp = traced

res = sr.optimize_full_circuit_budget(TOPO, SPEC, search_method="slsqp",
                                       slsqp_kwargs={"n_starts": 1, "maxiter": 40})
post = res["sizing"]

topo = json.load(open(TOPO, encoding="utf-8"))
pairs = (topo.get("symmetry") or {}).get("matching_pairs") or []
roles = topo.get("device_roles") or {}

emit("선언된 matching_pairs: %d개" % len(pairs))
emit("사이징 직후(레이아웃 복구 전) 값으로 판정한다.")
emit()

FIELDS = ("L", "ID", "gm_id", "vds", "vsb", "W")
bad = []
for p in pairs:
    names = [n for n in (p.get("names") or []) if n in PRE]
    if len(names) < 2:
        continue
    vals = {f: [PRE[n].get(f) for n in names] for f in FIELDS}

    def diverges(f):
        v = [x for x in vals[f] if x is not None]
        if len(v) < 2:
            return False
        lo, hi = min(v), max(v)
        return (hi - lo) > 1e-12 * max(abs(hi), 1.0) and (
            abs(hi - lo) / max(abs(hi), 1e-30) > 1e-6)

    div = [f for f in FIELDS if diverges(f)]
    if not div:
        continue
    bad.append((p, names, vals, div))

emit("=== 값이 갈리는 매칭 쌍 %d개 ===" % len(bad))
for p, names, vals, div in bad:
    emit()
    emit("  %s  (matching_sensitivity=%s, current_forced=%s)"
         % (names, p.get("matching_sensitivity"), p.get("current_forced")))
    emit("     갈리는 축: %s" % div)
    for f in FIELDS:
        v = vals[f]
        scale = {"L": 1e6, "ID": 1e6, "W": 1e6}.get(f, 1.0)
        unit = {"L": "um", "ID": "uA", "W": "um"}.get(f, "")
        s = " / ".join("-" if x is None else "%.4f" % (x * scale) for x in v)
        mark = "  <-- 갈림" if f in div else ""
        emit("       %-6s %-34s %s%s" % (f, s, unit, mark))
    # 레이아웃 복구가 이 쌍을 어떻게 바꿨는지
    after = " / ".join("-" if not (post.get(n) or {}).get("W")
                        else "%.4f" % (post[n]["W"] * 1e6) for n in names)
    emit("       %-6s %-34s um  (레이아웃 복구 후)" % ("W'", after))

emit()
emit("=== 참고: 사이징 경로 태그 ===")
for p, names, vals, div in bad:
    for n in names:
        e = PRE.get(n) or {}
        emit("  %-6s _L_source=%-28s _gm_id_source=%-24s device_roles=%s"
             % (n, e.get("_L_source"), e.get("_gm_id_source"),
                {k: v for k, v in (roles.get(n) or {}).items()
                 if k in ("gm_id_role", "L_role", "same_as_device", "vertical_stack_id")}))
