# -*- coding: utf-8 -*-
"""B19' 배선 **전** 점검: 미러 18소자에 `gm_id_match_vgs_of`를 걸면 실제로 강제되는가.

## 왜 먼저 재는가

`gm_id_match_vgs_of` 2차 pass에는 조용히 넘어가는 분기가 있다:

    entry = ctx.sized.get(name, {})
    if _gm_id_already_authoritative(entry):
        continue                      # <- 선언해도 **아무 일도 안 일어난다**

즉 이미 권위 있는 출처(compensation / replica / metric_stage_budget /
gm_target_convention / diode_self_consistency)로 gm_id가 정해진 소자에 이 필드를
걸면 **선언은 되는데 미러는 안 걸린다**. 그러면 "배선했다"고 믿는 채로 VGS가 계속
갈라진다 -- 정확히 B19가 처음 놓쳤던 종류의 실패다.

또 두 가지 계약이 더 있다(엔진 주석):

  - **2-pass 고정 순서**: `gm_id_role` 소자를 전부 확정한 뒤 `gm_id_match_vgs_of`를
    처리한다. 따라서 **레퍼런스는 반드시 그 이전에 확정되는 소자**여야 한다.
  - **체인 미지원**: 레퍼런스가 또 다른 `gm_id_match_vgs_of` 소자면 안 된다.

이 스크립트는 배선 전에 셋을 전부 확인한다 -- **아무것도 고치지 않는다.**

  1. 미러 18소자 각각의 gm_id가 지금 어느 출처에서 오는가 (`_gm_id_source`)
  2. 그중 **권위 있는 출처라 skip될 소자**가 누구인가 (걸어도 무효인 소자)
  3. 레퍼런스 3개(M18_bg / M66 / M36a)가 2-pass 순서에서 companion 자격이 되는가

실행: assets 디렉터리에서 `python tests/probe_mirror_wiring_readiness.py`
(SLSQP 없이 `_build_theta_evaluator` + 기본 theta 1회 평가라 빠르다.)
"""
import sys
import os
import json

ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # probes -> tests -> assets
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ASSETS, "workspaces"))
import numpy as np
import sizing_recipe as sr
import run_harness as H

_RESULT_PATH = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first_emit = [True]


def emit(*parts):
    line = " ".join(str(p) for p in parts)
    print(line, flush=True)
    mode = "w" if _first_emit[0] else "a"
    _first_emit[0] = False
    with open(_RESULT_PATH, mode, encoding="utf-8") as _f:
        _f.write(line + "\n")


TOPO = os.path.join(ASSETS, "..", "assets", "library", "current_reuse_telescopic_ota.topology.json")
d = np.load(os.path.join(ASSETS, "..", "assets", "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                       d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                       W_ref=5e-6, SID_1F=d["SID_1F_" + k])
nmos, pmos = mk("n"), mk("p")
# 2026-09-10 -- 손으로 복붙한 spec 블록을 폐기하고 **정본**을 쓴다. 복제본은 정본과
# 갈려 있었다(gm_id_grid 21점 vs 57점, L_candidates 12점 vs 41점, VDS_candidates 9점 vs
# 13점, stage_power_tolerance 누락). 같은 블록이 여러 파일에 그대로 퍼져 있었으므로
# 파일마다 다른 판단을 한 게 아니라 복제본 하나가 번진 것이다. 이제
# `sizing_recipe.require_declared_spec_source()`가 라이브러리 회로에 출처 선언을 강제한다.
SPEC = H.canonical_spec("current_reuse_telescopic_ota")
nmos = SPEC["lut_by_kind"]["nmos"]
pmos = SPEC["lut_by_kind"]["pmos"]

# theta는 아무 값이나 되지 않는다 -- 빈 dict면 A엔진이 전류를 못 정하고, bounds 중점은
# 헤드룸이 infeasible이었다(둘 다 실측). 그래서 **실제 최적점**을 한 번 구해 캐시한다.
THETA_CACHE = os.path.splitext(os.path.abspath(__file__))[0] + ".theta_star.json"
if os.path.exists(THETA_CACHE):
    _theta0 = json.load(open(THETA_CACHE, encoding="utf-8"))
    emit("[캐시] theta_star 재사용:", os.path.basename(THETA_CACHE))
else:
    _r = sr.optimize_full_circuit_budget(TOPO, SPEC, search_method="slsqp",
                                         slsqp_kwargs={"n_starts": 1, "maxiter": 40})
    _theta0 = {k: float(v) for k, v in (_r["theta_star"] or {}).items()}
    json.dump(_theta0, open(THETA_CACHE, "w", encoding="utf-8"), indent=1)
    emit("[신규] SLSQP로 theta_star를 구해 캐시했다.")

env = sr._build_theta_evaluator(TOPO, SPEC)
ctx, _metrics = env["evaluate"](_theta0)
sized = ctx.sized
topo = json.load(open(TOPO, encoding="utf-8"))
roles = topo.get("device_roles") or {}


def mirror_groups(topo_path):
    """미러군은 엔진 정본 `sr.true_current_mirror_groups()`, diode는 `sr.is_diode_connected()`로 정한다.

    표시 순서: 그룹은 (소자 수 내림차순, gate 넷, source 넷), 그룹 안 소자는 넷리스트 순서.
    """
    trs, _meta = sr.load_topology(topo_path)
    by = {t.name: t for t in trs}
    order = {t.name: i for i, t in enumerate(trs)}
    groups = [sorted(ms, key=order.get) for ms in sr.true_current_mirror_groups(by)]
    groups.sort(key=lambda ms: by[ms[0]].source)
    groups.sort(key=lambda ms: (-len(ms), by[ms[0]].gate))
    out = []
    for names in groups:
        t0 = by[names[0]]
        diodes = [n for n in names if sr.is_diode_connected(by[n])]
        out.append({"tag": f"{t0.kind}:{t0.gate}", "kind": t0.kind, "members": names,
                    "ref": diodes[0] if diodes else None})
    return out


GROUPS = mirror_groups(TOPO)

emit("=" * 100)
emit("1. 미러 18소자의 gm_id가 지금 어디서 오는가  --  걸어도 무효인 소자를 찾는다")
emit("=" * 100)

blocked = []
for g in GROUPS:
    emit("")
    emit(f"  [{g['tag']}]  레퍼런스={g['ref']}")
    emit(f"  {'소자':<9}{'역할':<12}{'_gm_id_source':<26}{'권위?':<8}{'gm_id':>9}{'VGS(V)':>9}")
    emit("  " + "-" * 75)
    for m in g["members"]:
        e = sized.get(m, {})
        src = e.get("_gm_id_source", "(없음)")
        auth = sr._gm_id_already_authoritative(e)
        dr = roles.get(m) or {}
        role = dr.get("gm_id_role") or ("diode" if m == g["ref"] else "-")
        try:
            lut = SPEC["lut_by_kind"][e["kind"]]
            vgs = lut.vgs_for_gm_id(e["gm_id"], e["L"], e["vds"], e.get("vsb", 0.0))
        except Exception:
            vgs = float("nan")
        mark = "★권위" if auth else ""
        if auth and m != g["ref"]:
            blocked.append((g["tag"], m, src))
        emit(f"  {m:<9}{str(role):<12}{src:<26}{mark:<8}"
             f"{e.get('gm_id', float('nan')):>9.3f}{vgs:>9.4f}")
    vs = []
    for m in g["members"]:
        e = sized.get(m, {})
        try:
            lut = SPEC["lut_by_kind"][e["kind"]]
            vs.append(lut.vgs_for_gm_id(e["gm_id"], e["L"], e["vds"], e.get("vsb", 0.0)))
        except Exception:
            pass
    if vs:
        emit(f"  -> 지금 VGS 퍼짐: {max(vs)-min(vs)*1:.4f} V  (min {min(vs):.4f} / max {max(vs):.4f})")

emit("")
emit("=" * 100)
emit("2. 판정")
emit("=" * 100)
emit("")
if blocked:
    emit(f"  ★ 걸어도 무효인 소자 {len(blocked)}개 -- 이 소자들은 `gm_id_match_vgs_of`를")
    emit("     선언해도 `_gm_id_already_authoritative()`에서 조용히 건너뛴다:")
    for tag, m, src in blocked:
        emit(f"       {m:<9} ({tag})  출처={src}")
    emit("")
    emit("     => 배선 전에 이 소자들을 어떻게 할지 정해야 한다(권위 출처를 떼거나,")
    emit("        미러 강제를 그 출처보다 우선시키거나, 예외로 남기거나).")
else:
    emit("  걸어도 무효인 소자 없음 -- 15개 전부 실제로 강제된다.")

emit("")
emit("  레퍼런스 companion 자격 (2-pass 순서상 먼저 확정되는가):")
for g in GROUPS:
    ref = g["ref"]
    e = sized.get(ref, {})
    dr = roles.get(ref) or {}
    has_role = bool(dr.get("gm_id_role"))
    src = e.get("_gm_id_source", "(없음)")
    is_chain = bool(dr.get("gm_id_match_vgs_of"))
    ok = ("gm_id" in e) and not is_chain
    emit(f"    {str(ref):<9} gm_id_role={str(has_role):<6} 출처={src:<26} "
         f"체인여부={is_chain}  -> {'OK' if ok else '★불가'}")

emit("")
emit("완료. 결과 파일:", _RESULT_PATH)
