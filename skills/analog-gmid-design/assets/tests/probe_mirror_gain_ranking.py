# -*- coding: utf-8 -*-
"""미러 3그룹의 공유 VGS를 **gain 기준**으로 고르는 조사 도구(2026-09-09).

## 사용자가 확정한 설계 의도 (2026-09-09)

> "tail M5/M6는 bias 미러에 묶는 것이 설계 의도야. vgs는 gain이야. 첫번째
>  differential input 단의 tail이기 때문에 gain에 직접적으로 영향을 미치는
>  id전류를 만들고 있어."

즉 B19'의 두 미결 판단이 모두 답을 받았다:

  (가) 18소자 전부를 미러로 강제하는가        -> **그렇다. tail 포함이 의도다.**
  (나) 공유 VGS를 어느 기준으로 고르는가       -> **gain.** 면적이 아니다.

`probe_mirror_design_space.py`가 성립 조합을 면적 오름차순으로 줄 세웠던 것은 **기준이
틀린 랭킹**이다. 이 스크립트가 같은 조합을 gain으로 다시 줄 세운다.

## 방법

세 그룹은 각각 tail을 하나씩 갖는다(PMOS Vbias1 -> M6, NMOS Vbias4 -> M5,
PMOS Vcmfb -> M7). 그래서 세 그룹의 (L, VGS)를 **교차로** 훑는다.

각 조합에서 18소자를 미러 강제값으로 덮어쓴 뒤 **엔진의 실제 metric**을 부른다
(`compute_metric`, 폐형식 근사가 아니라 선언된 그 metric). 덮어쓰는 값은:

    gm_id_i = gm_id_for_vgs(VGS, L, vds_i, vsb_i)     공유 VGS에서 직접
    W_i     = L * ID_i / IDu(VGS, L, vds_i, vsb_i)    ★ VGS에서 직접 조회
    gm_i    = gm_id_i * ID_i                          정의상 정확
    gds_i   = gm_i / (gm/gds)(VGS, ...)               ★ VGS에서 직접

★ 표시한 두 곳은 `gm_id_to_id_density()`/`gm_gds_ratio()`를 쓰면 안 된다 -- 두 함수 모두
첫 줄에서 `_solve_vgs(gm_id,...)`로 gm_id를 VGS로 되돌리는데 PMOS는 그 역변환이 깨져
있다(B20, `probe_gm_id_monotonicity.py`). VGS가 애초에 스윕 변수라 왕복할 이유가 없다.

**아무것도 고치지 않는다** -- ctx를 복사해 재고, 원본 topology/엔진은 안 건드린다.

## 측정 결과 (2026-09-09, 6480조합 = 20 x 9 x 36)

### ① 선언된 제약 `gain_db`는 미러를 **구조적으로 못 본다**

6480조합 전부에서 `gain_db` = 65.5547dB로 **완전히 불변**(Δ=0.0000)이다. 선언을 보면
이유가 명확하다:

    "gain_db": {"type": "gain_stages_sum",
                "stages": [["M1a","M4a","M2a","M3a"], ["M15","M16"]]}

소자 **6개**만 더한다. 미러 18소자는 하나도 없다. 그런데 `M19`의 drain은 `Vom1`,
`M10`의 drain은 `Vop1` -- **stage1의 출력노드 그 자체**다. 그 gds가 이득을 직접 깎는데
제약은 그것을 못 본다. 같은 6480조합에서 전체회로 MNA `gain_full_circuit_db`는
**63.67 ~ 89.82dB로 26.15dB 벌어진다.** 즉 **선언된 `gain_db >= 54` 제약은 26dB짜리
효과에 눈이 멀어 있다.**

(위생검사: 같은 스윕에서 `area_um2`는 6480개 전부 서로 다른 값이 나왔다 -- ctx 패치가
metric에 실제로 반영된다는 뜻이라, 위 Δ=0은 패치 누락이 아니라 진짜 무감도다.)

### ② 사용자의 gain 기준으로 고르면 답이 뒤집힌다

    랭킹 기준            선택                                   gain_full   미러면적
    면적 최소(틀린 기준)  0.20/0.75 + 0.15/0.55 + 0.15/0.80      63.72dB     73.95um^2
    gain 최대(옳은 기준)  4.00/1.10 + 4.00/0.60 + (무관)         89.82dB   1775.29um^2

**면적 최소 조합은 gain 순위 6423/6480** -- 사실상 최악이다. 사용자의 정정이 없었으면
정확히 반대로 골랐을 것이다. 대가는 미러면적 24배(73.95 -> 1775µm², 전체 922 -> 2535µm²).

### ③ 어느 그룹이 지렛대인가

    pmos:Vbias1 (M6 M8 M13 M22 M17 M18_bg M60 M61)   69.04 ~ 89.82dB   폭 20.8dB
    nmos:Vbias4 (M5 M12 M10 M21 M19 M66 M68 M38)     69.81 ~ 89.82dB   폭 20.0dB
    pmos:Vcmfb  (M7 M36a)                            89.82 ~ 89.82dB   폭  0.0dB

앞의 둘은 신호경로를 직접 로드해 20dB씩 좌우하고, **Vcmfb 그룹은 gain에 전혀 무관**하다
(CMFB 경로라 당연하다) -- 그 그룹만은 gain이 기준이 될 수 없고 다른 기준(면적 등)이 맞다.

둘 다 **L을 최대(4.0µm)로** 밀 때 최적이다(ro 최대화). 그런데 **L=1.5/2.5/4.0µm는
B20이 가장 심하게 무는 구간**이다(탐색범위와 겹치는 이중값 대역). 이 스크립트는 IDu와
gm/gds를 VGS에서 직접 읽어 그 경로를 피했지만, **엔진을 지금 배선하면 바로 그 깨진
경로로 계산한다.** B20이 먼저여야 하는 이유가 순서 위생이 아니라 실질이 됐다.

실행: assets 디렉터리에서 `python tests/probe_mirror_gain_ranking.py`
(theta_star 캐시가 없으면 SLSQP를 한 번 돌리므로 수 분 걸린다.)
"""
import sys
import os
import json
import math
import copy

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ASSETS, "..", "..", "..", "workspaces"))
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


TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
THETA_CACHE = os.path.splitext(os.path.abspath(__file__))[0] + ".theta_star.json"

d = np.load(os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                       d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                       W_ref=5e-6, SID_1F=d["SID_1F_" + k])
nmos, pmos = mk("n"), mk("p")
LUT = {"nmos": nmos, "pmos": pmos}

# 2026-09-10 -- 손으로 복붙한 spec 블록을 폐기하고 **정본**을 쓴다. 복제본은 정본과
# 갈려 있었다(gm_id_grid 21점 vs 57점, L_candidates 12점 vs 41점, VDS_candidates 9점 vs
# 13점, stage_power_tolerance 누락). 같은 블록이 여러 파일에 그대로 퍼져 있었으므로
# 파일마다 다른 판단을 한 게 아니라 복제본 하나가 번진 것이다. 이제
# `sizing_recipe.require_declared_spec_source()`가 라이브러리 회로에 출처 선언을 강제하고,
# 일부러 다르게 쓸 때는 `H.derived_spec(key, why, **overrides)`로 무엇을 왜 바꿨는지 남긴다.
SPEC = H.canonical_spec("current_reuse_telescopic_ota")
nmos = SPEC["lut_by_kind"]["nmos"]
pmos = SPEC["lut_by_kind"]["pmos"]

# ── theta_star 확보 (비싸므로 캐시) ───────────────────────────────────────────
if os.path.exists(THETA_CACHE):
    theta_star = json.load(open(THETA_CACHE, encoding="utf-8"))
    emit("[캐시] theta_star 재사용:", os.path.basename(THETA_CACHE))
else:
    _res = sr.optimize_full_circuit_budget(TOPO, SPEC, search_method="slsqp",
                                           slsqp_kwargs={"n_starts": 1, "maxiter": 40})
    theta_star = {k: float(v) for k, v in (_res["theta_star"] or {}).items()}
    json.dump(theta_star, open(THETA_CACHE, "w", encoding="utf-8"), indent=1)
    emit("[신규] SLSQP를 돌려 theta_star를 캐시했다.")

env = sr._build_theta_evaluator(TOPO, SPEC)
evaluate = env["evaluate"]
metrics_specs = env["metrics_specs"]
kind_of = env["kind_of"]

base_ctx, base_metrics = evaluate(theta_star)
emit("")
emit("기준점(미러 강제 없음)의 metric:")
for k in sorted(base_metrics):
    emit(f"    {k:<28}{base_metrics[k]:>16.6g}")

# ── 미러 그룹 (넷리스트에서 유도) ─────────────────────────────────────────────
_topo = json.load(open(TOPO, encoding="utf-8"))


def _mirror_groups(topo):
    import collections
    g = collections.defaultdict(list)
    for dv in topo["netlist"]:
        g[(dv.get("gate"), dv.get("source"), dv.get("kind"))].append(dv)
    out = []
    for (gate, src, kind), ds in sorted(g.items(), key=lambda kv: (-len(kv[1]), str(kv[0]))):
        if len(ds) < 2:
            continue
        names = [dv["name"] for dv in ds]
        diodes = [dv["name"] for dv in ds if dv.get("gate") == dv.get("drain")]
        out.append({"tag": f"{kind}:{gate}", "kind": kind, "members": names,
                    "ref": diodes[0] if diodes else None})
    return out


GROUPS = _mirror_groups(_topo)
emit("")
emit("미러 그룹(넷리스트 유도):")
for g in GROUPS:
    emit(f"    {g['tag']:<16} n={len(g['members'])}  ref={g['ref']}  {', '.join(g['members'])}")


def _q(lut, arr, L, vgs, vds, vsb):
    return lut._query(arr, L, vgs, vds, vsb)


def forced(group, L, vgs, sized):
    """이 그룹을 (L, VGS)로 미러 강제했을 때의 소자별 사이징. 불가능하면 None."""
    lut = LUT[group["kind"]]
    out = {}
    for m in group["members"]:
        e = sized.get(m)
        if e is None:
            return None
        ID = float(e["ID"])
        vds = vgs if m == group["ref"] else float(e["vds"])
        vsb = 0.0                      # 소스가 레일이므로 물리적으로 0 (B9와 무관하게)
        try:
            gm_id = lut.gm_id_for_vgs(vgs, L, vds, vsb)
            idu = math.exp(_q(lut, lut._log_ID, L, vgs, vds, vsb)) * L / lut._w_ref_effective(L)
            ratio = math.exp(_q(lut, lut._log_GM, L, vgs, vds, vsb)
                             - _q(lut, lut._log_GDS, L, vgs, vds, vsb))
        except Exception:
            return None
        if not (gm_id > 0 and idu > 0 and ratio > 0):
            return None
        W = L * ID / idu
        if not (1e-6 <= W <= 200e-6):
            return None
        if vds < 2.0 / gm_id:                       # 포화 위반
            return None
        gm = gm_id * ID
        out[m] = {**e, "L": L, "vds": vds, "vsb": vsb, "gm_id": gm_id,
                  "W": W, "gm": gm, "gds": gm / ratio,
                  "_gm_id_source": "mirror_forced", "_L_source": "mirror_forced"}
    return out


L_GRID = [float(v) for v in nmos.L_grid]
VGS_LIST = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00, 1.10, 1.20]

# 그룹별 성립 후보 미리 계산
cands = []
for g in GROUPS:
    lst = []
    for L in L_GRID:
        for vgs in VGS_LIST:
            f = forced(g, L, vgs, base_ctx.sized)
            if f is not None:
                lst.append((L, vgs, f))
    cands.append(lst)
    emit(f"    -> {g['tag']:<16} 성립 조합 {len(lst)}개")

# ★ 랭킹 metric은 `gain_full_circuit_db`(전체회로 MNA)여야 한다.
# 선언된 제약 `gain_db`는 `gain_stages_sum`으로 소자 6개(M1a/M4a/M2a/M3a + M15/M16)만
# 더하므로 **미러 18소자를 구조적으로 하나도 안 본다** -- 실제로 6480조합 전부에서
# Δgain=0.0000이 나왔다(2026-09-09 실측). M10/M19는 drain이 stage1 출력노드
# (Vop1/Vom1)라 그 gds가 이득을 직접 깎는데도 그렇다.
GAIN = "gain_full_circuit_db"
WATCH = ["gain_full_circuit_db", "gain_db", "area_um2", "cmrr_estimate_db",
         "psrr_estimate_db", "supply_current_uA"]
WATCH = [m for m in WATCH if m in metrics_specs]
assert GAIN in metrics_specs, f"{GAIN} metric이 선언돼 있지 않다: {sorted(metrics_specs)}"

# ── 교차 스윕: 세 그룹을 동시에 강제하고 실제 gain을 잰다 ─────────────────────
emit("")
emit("=" * 96)
emit("미러 3그룹을 동시에 강제했을 때의 실제 gain  --  gain 내림차순")
emit("=" * 96)
emit("")
emit(f"  기준(미러 강제 없음) gain_db = {base_metrics[GAIN]:.4f}")
emit("")

rows = []
saved = {n: dict(e) for n, e in base_ctx.sized.items()}
n_eval = n_fail = 0
for L0, v0, f0 in cands[0]:
    for L1, v1, f1 in cands[1]:
        for L2, v2, f2 in cands[2]:
            for n, e in saved.items():
                base_ctx.sized[n] = dict(e)
            base_ctx.sized.update(f0)
            base_ctx.sized.update(f1)
            base_ctx.sized.update(f2)
            try:
                mv = {m: sr.compute_metric(metrics_specs[m], base_ctx) for m in WATCH}
            except Exception:
                n_fail += 1
                continue
            n_eval += 1
            area = sum(x["W"] * x["L"] for x in list(f0.values()) + list(f1.values())
                       + list(f2.values())) * 1e12
            rows.append((mv[GAIN], (L0, v0), (L1, v1), (L2, v2), area, mv))
for n, e in saved.items():
    base_ctx.sized[n] = dict(e)

emit(f"  평가 {n_eval}조합 (실패 {n_fail})")
emit("")
rows.sort(key=lambda r: -r[0])
emit(f"  {'gain_full':>11}{'gain_db':>10}{'전체면적':>11}{'PMOS:Vbias1':>18}"
     f"{'NMOS:Vbias4':>16}{'PMOS:Vcmfb':>16}{'미러면적':>11}")
emit("  " + "-" * 93)
for gv, a, b, c, area, mv in rows[:20]:
    emit(f"  {gv:>11.4f}{mv.get('gain_db',float('nan')):>10.4f}"
         f"{mv.get('area_um2',float('nan')):>11.2f}"
         f"{a[0]*1e6:>9.4f}/{a[1]:<8.2f}{b[0]*1e6:>7.4f}/{b[1]:<8.2f}"
         f"{c[0]*1e6:>7.4f}/{c[1]:<8.2f}{area:>11.2f}")
emit("")
emit(f"  최저 gain_full = {rows[-1][0]:.4f}dB  (최고와 {rows[0][0]-rows[-1][0]:.4f}dB 차이)")
_areas = {round(r[5].get('area_um2', 0.0), 6) for r in rows}
emit(f"  위생검사: area_um2가 조합마다 실제로 달라지는가 -> 서로 다른 값 {len(_areas)}개 "
     f"(1이면 패치가 metric에 반영되지 않은 것이다)")

emit("")
emit("  (참고) 면적 최소 조합이 gain에서 몇 등인가:")
by_area = sorted(rows, key=lambda r: r[4])
if by_area:
    best_a = by_area[0]
    rank = 1 + sum(1 for r in rows if r[0] > best_a[0])
    emit(f"    면적최소 {best_a[4]:.2f}um^2 -> gain {best_a[0]:.4f}dB, gain 순위 {rank}/{len(rows)}")
    emit(f"    gain최고 {rows[0][0]:.4f}dB -> 면적 {rows[0][4]:.2f}um^2")

# ── 각 그룹이 gain에 얼마나 기여하는가(나머지는 gain 최적으로 고정) ───────────
emit("")
emit("=" * 96)
emit("그룹별 민감도  --  나머지 두 그룹을 gain 최적점에 고정하고 한 그룹만 훑는다")
emit("=" * 96)
if rows:
    best = rows[0]
    picks = [best[1], best[2], best[3]]
    for gi, g in enumerate(GROUPS):
        emit("")
        emit(f"  [{g['tag']}]  tail 포함 소자: {', '.join(g['members'])}")
        emit(f"    {'L(um)':>9}{'VGS':>7}{'gain_full':>11}{'Δgain':>10}{'그룹면적(um^2)':>16}")
        emit("    " + "-" * 53)
        sub = []
        for (Lx, vx, fx) in cands[gi]:
            for n, e in saved.items():
                base_ctx.sized[n] = dict(e)
            for gj in range(3):
                if gj == gi:
                    base_ctx.sized.update(fx)
                else:
                    Lp, vp = picks[gj]
                    ff = forced(GROUPS[gj], Lp, vp, saved)
                    if ff:
                        base_ctx.sized.update(ff)
            try:
                gv = sr.compute_metric(metrics_specs[GAIN], base_ctx)
            except Exception:
                continue
            ar = sum(x["W"] * x["L"] for x in fx.values()) * 1e12
            sub.append((gv, Lx, vx, ar))
        sub.sort(key=lambda r: -r[0])
        for gv, Lx, vx, ar in sub[:8]:
            emit(f"    {Lx*1e6:>9.4f}{vx:>7.2f}{gv:>11.4f}{gv-best[0]:>10.4f}{ar:>16.2f}")
        if len(sub) > 8:
            emit(f"    ... (총 {len(sub)}개, 최저 gain {sub[-1][0]:.4f}dB "
                 f"@ L={sub[-1][1]*1e6:.4f}um VGS={sub[-1][2]:.2f})")
    for n, e in saved.items():
        base_ctx.sized[n] = dict(e)

emit("")
emit("완료. 결과 파일:", _RESULT_PATH)
