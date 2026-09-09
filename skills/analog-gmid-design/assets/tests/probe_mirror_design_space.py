# -*- coding: utf-8 -*-
"""B19(깨진 미러 3그룹)을 **고칠 수 있는 동작점이 존재하는가**를 실측하는 조사 도구(2026-09-09).

## 배경

`probe_ratio_pair_analysis.py`가 확인한 사실: 세 그룹은 게이트·소스를 공유하는 진짜
전류미러라 VGS가 KVL로 강제 동일해야 하는데, 사이징은 최대 464mV를 벌려놓았다. 미러를
강제하면 M8/M17이 W≈1545µm(상한 200µm의 7.7배)를 요구해 회로가 성립하지 않는다.

그 결론은 **현재 동작점 한 점에서만** 확인한 것이다. 이 스크립트는 그 한 점 대신
설계 공간 전체를 훑어 "성립하는 (L, VGS, Iref)가 있는가, 있다면 그 대가가 무엇인가"를
표로 만든다 -- **아무것도 고치지 않고 재기만 한다.**

## 먼저 정정: 미러 그룹은 11소자가 아니라 18소자다 (2026-09-09)

앞선 조사는 `symmetry.matching_pairs`에 **선언된** 그룹만 봤다. 그런데 VGS 동일 강제는
선언이 아니라 게이트·소스 공유라는 connectivity에서 나온다. 넷리스트를 전수로 다시 세면:

    PMOS gate=Vbias1 source=vdd  8개  M6 M8 M13 M22 M17 M18_bg M60 M61   (diode: M18_bg)
    NMOS gate=Vbias4 source=gnd  8개  M5 M12 M10 M21 M19 M66 M68 M38     (diode: M66)
    PMOS gate=Vcmfb  source=vdd  2개  M7 M36a                            (diode: M36a)

빠져 있던 것이 **7소자**다. 특히 (1) **M6/M5는 diffpair tail**이라 회로의 주 전류를
나르고, (2) **M66은 NMOS 그룹의 diode 레퍼런스인데 그룹에서 빠져 있었다**(즉 그 그룹은
레퍼런스 없이 분석됐다), (3) **M7/M36a 그룹은 통째로 누락**돼 있었다 -- M36a는 이
계획서 Executive Summary가 지목한 원래 버그의 대표 소자다.

## 방법

미러가 성립하면 그룹 안에서 VGS가 하나로 통일되므로, 자유도는 정확히 셋이다:

    L        (그룹 공유 채널길이)
    VGS      (= 레퍼런스 diode의 VDS이기도 하다 -- gate=drain이므로)
    k_Iref   (bias generator 전류 배율 -- 그룹의 모든 ID를 함께 스케일)

각 (L, VGS)에서 소자마다 `gm_id_i = gm_id_for_vgs(VGS, L, vds_i, vsb_i)`로 gm_id를 얻고
`W_i = L * ID_i / IDu`로 폭을 구한다. 레퍼런스는 diode이므로 `vds_ref = VGS`를 쓴다.

★ IDu는 `gm_id_to_id_density(gm_id,...)`가 **아니라** VGS에서 직접 읽는다(`_idu_at_vgs()`).
그 함수는 내부에서 gm_id를 VGS로 되돌리는데 PMOS는 그 역변환이 깨져 있다
(`probe_gm_id_monotonicity.py`). 처음엔 그걸 썼다가 W_max가 VGS에 대해 18배씩
출렁이는 비물리 표가 나왔고, 그게 이 결함을 찾은 계기였다.

성립 판정은 **세 조건 전부**다: `1um <= W_i <= 200um`(W_bounds 양쪽)와
`vds_i >= 2/gm_id_i`(포화). 상한만 보면 강반전 구석에서 W가 0.3um까지 내려가는
가짜 해가 잡힌다.

`vsb`는 **두 가지로 계산해 나란히 적는다**: (a) 엔진이 지금 들고 있는 값, (b) 물리적으로
옳은 값(소스가 vdd/gnd 레일에 묶여 있으므로 0). B9가 (a)를 틀리게 만든다는 것은 이미
확인돼 있으므로, 판단은 (b)로 해야 한다.

## 측정 결과 (2026-09-09) -- ★ B19의 기존 결론은 틀렸다. 미러는 성립한다.

계획서 §10.3 B19는 "고치면 회로가 성립하지 않는다(M8/M17이 W≈1545µm 요구), bias
generator의 전류나 L을 다시 잡는 **회로 설계 판단**이 필요하다"고 적었다. 설계공간을
실제로 훑으니 **세 그룹 모두 성립하는 조합이 있다**:

    그룹                     성립조합   최소 그룹면적   그 조합
    PMOS Vbias1 (8소자)        20개       22.90 µm²    L=0.20µm VGS=0.75V  gm_id 15.42~15.70
    NMOS Vbias4 (8소자)         9개       50.28 µm²    L=0.15µm VGS=0.55V  gm_id 22.36~23.07
    PMOS Vcmfb  (2소자)        36개        0.77 µm²    L=0.15µm VGS=0.80V  gm_id 11.83~14.01

세 그룹 합쳐 **73.95 µm²**인데, 지금은 M18_bg 혼자 W=103µm(38.6µm²), M66 혼자
W=164µm(61.6µm²)이라 **미러를 제대로 강제하면 면적이 오히려 줄어든다.**

기존 결론이 틀린 이유는 둘이고, 둘 다 실측으로 확인됐다:

  1. **VGS를 현재값 0.675V에 고정한 채 물었다.** 그런데 diode 레퍼런스의 VDS(=VGS)는
     설계 변수다 -- W가 그것을 따라 정해질 뿐이다. VGS=0.675V 근처에서만 W가 폭발하고,
     0.75~0.90V로 옮기면 전원이 상한 안에 들어온다.
  2. **W를 `gm_id_to_id_density()`로 구했다.** PMOS는 그 함수의 gm_id->VGS 역변환이
     깨져 있어(`probe_gm_id_monotonicity.py`) W가 VGS에 대해 18배씩 출렁였다.

부수 측정:

  - **k_Iref는 지렛대가 아니다.** W ∝ ID라 전류를 k배 하면 W도 정확히 k배지만, 성립
     조합 수는 0.25~15배 구간에서 거의 안 변한다(20 -> 13개). 즉 "Iref를 다시 잡는
     문제"가 아니다. 실제 지렛대는 **공유 VGS**다.
  - **B9(vsb 오산출)이 NMOS 그룹을 최대 8.07배 부풀린다**(M38의 vsb가 0이어야 하는데
     0.8625). PMOS Vbias1 그룹은 1.5% 이내라 거의 무영향.

즉 B19는 **막힌 설계 판단이 아니라 배선 과제**다. 기전도 이미 있다 --
nmcnr의 M203/M204에 쓴 `gm_id_match_vgs_of`(세션38)와 같은 클래스다. 다만 (가) 대상
소자 결정과 (나) 공유 VGS를 어떤 기준으로 고를지는 회로위상 해석이라 **공동분석 대상**이다.

실행: assets 디렉터리에서 `python tests/probe_mirror_design_space.py`
"""
import sys
import os
import json
import math

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
CACHE = os.path.splitext(os.path.abspath(__file__))[0] + ".sizing_cache.json"

d = np.load(os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                       d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                       W_ref=5e-6, SID_1F=d["SID_1F_" + k])
nmos, pmos = mk("n"), mk("p")
LUT = {"nmos": nmos, "pmos": pmos}

SPEC = {
    "lut_by_kind": LUT, "lut": nmos, "vdd": 1.8,
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

# ── 사이징 결과(현 동작점). 비싸므로 캐시한다. ────────────────────────────────
if os.path.exists(CACHE):
    sized = json.load(open(CACHE, encoding="utf-8"))
    emit("[캐시] 기존 사이징 결과를 재사용한다:", os.path.basename(CACHE))
else:
    res = sr.optimize_full_circuit_budget(TOPO, SPEC, search_method="slsqp",
                                          slsqp_kwargs={"n_starts": 1, "maxiter": 40})
    sized = {k: {kk: vv for kk, vv in v.items() if isinstance(vv, (int, float, str, bool)) or vv is None}
             for k, v in res["sizing"].items()}
    json.dump(sized, open(CACHE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    emit("[신규] 사이징을 새로 돌려 캐시했다:", os.path.basename(CACHE))

trs, meta = sr.load_topology(TOPO)
by = {t.name: t for t in trs}

# ── 미러 그룹은 **넷리스트에서 직접 유도한다**(선언된 matching_pairs가 아니라). ──────
#
# 2026-09-09 발견: `probe_ratio_pair_analysis.py`는 `symmetry.matching_pairs`에 선언된
# 그룹만 봤기 때문에 11소자로 셌는데, 게이트+소스+kind를 실제로 공유하는 소자를 넷리스트에서
# 전수로 세면 **18소자 3그룹**이다. 빠져 있던 것:
#
#   PMOS Vbias1 : M6              <- diffpair tail. 미러인데 안 세고 있었다
#   NMOS Vbias4 : M5, M66, M68, M38   <- M66이 이 그룹의 diode 레퍼런스인데 빠져 있었다
#   PMOS Vcmfb  : M7, M36a        <- 그룹 자체가 통째로 빠져 있었다(M36a가 diode 레퍼런스)
#
# VGS 동일 강제는 게이트·소스 공유라는 **순수 connectivity 사실**에서 나오므로,
# 선언 여부와 무관하게 이 18소자 전부에 적용된다.
def _mirror_groups_from_netlist(topo):
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
        out.append((f"{kind.upper():<4}  gate={gate} source={src}", kind,
                    names, diodes[0] if diodes else None))
    return out


_topo_json = json.load(open(TOPO, encoding="utf-8"))
GROUPS = _mirror_groups_from_netlist(_topo_json)

W_MAX_UM = 200.0


def dev_info(name):
    e = sized[name]
    return {
        "ID": float(e["id_bias"]) if "id_bias" in e else float(e.get("ID", 0.0)),
        "vds": float(e["vds"]),
        "vsb_engine": float(e.get("vsb", 0.0)),
        "gm_id": float(e.get("gm_id", 0.0)),
        "L": float(e.get("L", 0.0)),
        "W": float(e.get("W", 0.0)),
    }


emit("")
emit("=" * 100)
emit("0. 현 동작점 -- 각 소자의 ID/vds/vsb가 어디서 왔는가")
emit("=" * 100)
for title, kind, members, ref in GROUPS:
    emit("")
    emit(f"  [{title}]")
    emit(f"  {'소자':<9}{'ID(uA)':>10}{'vds':>9}{'vsb(엔진)':>11}{'gm_id':>9}{'L(um)':>9}{'W(um)':>11}")
    emit("  " + "-" * 76)
    for m in members:
        i = dev_info(m)
        emit(f"  {m:<9}{i['ID']*1e6:>10.4f}{i['vds']:>9.4f}{i['vsb_engine']:>11.4f}"
             f"{i['gm_id']:>9.3f}{i['L']*1e6:>9.4f}{i['W']*1e6:>11.4f}")

# ── 1. 설계공간 스윕 ──────────────────────────────────────────────────────────
emit("")
emit("=" * 100)
emit("1. 미러를 강제했을 때 성립하는 (L, VGS)가 있는가  --  vsb는 물리값(레일 소스이므로 0)")
emit("=" * 100)
emit("")
emit("  판정: 그룹 전원의 W가 상한 200um 이하이면 성립. W_max를 적는다(단위 um).")

L_GRID = [float(v) for v in nmos.L_grid]
VGS_LIST = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00, 1.10, 1.20]


def _idu_at_vgs(lut, vgs, L, vds, vsb):
    """VGS에서 전류밀도(IDu)를 **직접** 읽는다.

    ★ `gm_id_to_id_density(gm_id, ...)`를 쓰면 안 된다 -- 그 함수는 내부에서
    `_solve_vgs(gm_id,...)`로 gm_id를 다시 VGS로 되돌리는데, PMOS는 gm/ID가 VGS에
    비단조라 그 역변환이 다른 branch로 튄다(`probe_gm_id_monotonicity.py`가 실측:
    탐색범위와 겹치는 동작점 53.6%, 파일럿 2소자에서 W가 2.36배 틀림). 여기서는
    VGS가 애초에 스윕 변수라 왕복할 이유가 없다 -- 곧바로 조회한다.
    """
    raw = math.exp(lut._query(lut._log_ID, L, vgs, vds, vsb))
    return raw * L / lut._w_ref_effective(L)


W_MIN_UM = 1.0            # W_bounds 하한 -- 이것도 제약이다


def widths_at(kind, members, ref, L, vgs, vsb_mode, id_scale=1.0):
    """(L, VGS)에서 그룹 전원의 (W(um), gm_id, vds, 포화여유)를 돌려준다. 실패하면 None."""
    lut = LUT[kind]
    out = {}
    for m in members:
        i = dev_info(m)
        vds = vgs if m == ref else i["vds"]          # 레퍼런스는 diode -> vds = vgs
        vsb = 0.0 if vsb_mode == "phys" else i["vsb_engine"]
        try:
            gm_id = lut.gm_id_for_vgs(vgs, L, vds, vsb)
            idu = _idu_at_vgs(lut, vgs, L, vds, vsb)
        except Exception:
            return None
        if not (gm_id > 0) or not (idu > 0):
            return None
        # 포화 여유: Jespers 근사 Vdsat ~ 2/gm_id. 음수면 triode라 사이징이 무효다.
        sat_margin = vds - 2.0 / gm_id
        out[m] = (L * i["ID"] * id_scale / idu * 1e6, gm_id, vds, sat_margin)
    return out


def verdict(w):
    """그룹이 실제로 성립하는가 -- W 상·하한과 포화조건을 **전부** 본다."""
    if w is None:
        return None
    wmax = max(v[0] for v in w.values())
    wmin = min(v[0] for v in w.values())
    sat = min(v[3] for v in w.values())
    ok = (wmax <= W_MAX_UM) and (wmin >= W_MIN_UM) and (sat >= 0.0)
    return {"ok": ok, "wmax": wmax, "wmin": wmin, "sat": sat}


for title, kind, members, ref in GROUPS:
    emit("")
    emit(f"  [{title}]   레퍼런스={ref or '(diode 없음 -- 외부에서 VGS가 정해짐)'}")
    hdr = f"  {'L(um)':>8}" + "".join(f"{v:>9.2f}" for v in VGS_LIST)
    emit(hdr)
    emit("  " + "-" * (8 + 9 * len(VGS_LIST)))
    for L in L_GRID:
        cells = []
        for vgs in VGS_LIST:
            v = verdict(widths_at(kind, members, ref, L, vgs, "phys"))
            if v is None:
                cells.append(f"{'--':>9}")
            else:
                txt = f"{v['wmax']:.1f}" if v["wmax"] < 1e5 else f"{v['wmax']:.1e}"
                cells.append(f"{(txt + ('*' if v['ok'] else '')):>9}")
        emit(f"  {L*1e6:>8.4f}" + "".join(cells))
emit("")
emit("  * = W 상·하한(1~200um)과 포화조건(vds >= 2/gm_id)을 전부 만족하는 조합")

# ── 2. 성립하는 조합의 상세 ───────────────────────────────────────────────────
emit("")
emit("=" * 100)
emit("2. W_max <= 200um인 조합의 상세  --  대가가 무엇인가")
emit("=" * 100)

for title, kind, members, ref in GROUPS:
    emit("")
    emit(f"  [{title}]")
    feasible = []
    reject = {"W상한": 0, "W하한": 0, "포화": 0}
    for L in L_GRID:
        for vgs in VGS_LIST:
            w = widths_at(kind, members, ref, L, vgs, "phys")
            v = verdict(w)
            if v is None:
                continue
            if not v["ok"]:
                if v["wmax"] > W_MAX_UM:
                    reject["W상한"] += 1
                elif v["wmin"] < W_MIN_UM:
                    reject["W하한"] += 1
                else:
                    reject["포화"] += 1
                continue
            gm_ids = [x[1] for x in w.values()]
            area = sum(x[0] for x in w.values()) * L * 1e6   # sum(W*L), um^2
            feasible.append((v["wmax"], L, vgs, min(gm_ids), max(gm_ids), area, w, v))
    emit(f"    기각 사유: W상한초과 {reject['W상한']}  /  W하한미달 {reject['W하한']}"
         f"  /  포화위반 {reject['포화']}")
    if not feasible:
        emit("    ★ 세 조건을 모두 만족하는 조합이 하나도 없다.")
        continue
    feasible.sort(key=lambda r: r[5])          # 면적 오름차순
    emit(f"    성립 조합 {len(feasible)}개 (면적 오름차순 상위 15개)")
    emit(f"    {'L(um)':>8}{'VGS(V)':>9}{'W범위(um)':>20}{'gm_id범위':>18}"
         f"{'포화여유(V)':>13}{'그룹면적(um^2)':>16}")
    emit("    " + "-" * 88)
    for wmax, L, vgs, gmin, gmax, area, w, v in feasible[:15]:
        emit(f"    {L*1e6:>8.4f}{vgs:>9.2f}{v['wmin']:>10.2f}~{wmax:<9.2f}"
             f"{gmin:>9.2f}~{gmax:<8.2f}{v['sat']:>13.3f}{area:>16.2f}")

    best = feasible[0]
    emit("")
    emit(f"    가장 면적이 작은 조합의 소자별 내역  (L={best[1]*1e6:.4f}um, VGS={best[2]:.2f}V)")
    emit(f"    {'소자':<9}{'ID(uA)':>10}{'vds':>9}{'gm_id':>9}{'W(um)':>11}{'gm(uS)':>10}{'V_A(V)':>9}")
    emit("    " + "-" * 67)
    lut = LUT[kind]
    for m in members:
        wum, gm_id, vds, _satm = best[6][m]
        i = dev_info(m)
        gm = gm_id * i["ID"]
        try:
            va = lut.gm_gds_ratio(gm_id, best[1], vds, 0.0) / gm_id
        except Exception:
            va = float("nan")
        emit(f"    {m:<9}{i['ID']*1e6:>10.4f}{vds:>9.4f}{gm_id:>9.3f}{wum:>11.3f}"
             f"{gm*1e6:>10.4f}{va:>9.3f}")

# ── 3. bias generator 전류를 다시 잡으면 어떻게 달라지는가 ────────────────────
emit("")
emit("=" * 100)
emit("3. bias generator 전류 배율 k_Iref가 성립 여부를 바꾸는가")
emit("=" * 100)
emit("")
emit("  W는 ID에 비례하므로(W = L*ID/IDu, IDu는 ID와 무관) k배를 곱하면 W_max도 정확히 k배다.")
emit("  즉 전류를 낮추면 성립 영역이 넓어지고 높이면 좁아진다 -- 아래는 각 배율에서")
emit("  성립하는 (L,VGS) 조합의 개수와 최소 그룹면적이다.")

for title, kind, members, ref in GROUPS:
    emit("")
    emit(f"  [{title}]")
    emit(f"    {'k_Iref':>8}{'성립조합수':>12}{'최소W_max(um)':>16}{'최소그룹면적(um^2)':>20}")
    emit("    " + "-" * 56)
    for k in [0.25, 0.5, 1.0, 2.0, 4.0, 15.0]:
        n_ok, best_w, best_a = 0, float("inf"), float("inf")
        for L in L_GRID:
            for vgs in VGS_LIST:
                w = widths_at(kind, members, ref, L, vgs, "phys", id_scale=k)
                v = verdict(w)
                if v is None:
                    continue
                best_w = min(best_w, v["wmax"])
                if v["ok"]:
                    n_ok += 1
                    best_a = min(best_a, sum(x[0] for x in w.values()) * L * 1e6)
        emit(f"    {k:>8.2f}{n_ok:>12d}{best_w:>16.2f}"
             + (f"{best_a:>20.2f}" if best_a < float('inf') else f"{'--':>20}"))

# ── 4. vsb 오차(B9)가 판정을 바꾸는가 ─────────────────────────────────────────
emit("")
emit("=" * 100)
emit("4. B9(vsb 오산출)이 이 판정을 바꾸는가  --  엔진 vsb vs 물리 vsb=0")
emit("=" * 100)
for title, kind, members, ref in GROUPS:
    emit("")
    emit(f"  [{title}]")
    emit(f"    {'L(um)':>8}{'VGS':>7}{'W합(물리)':>14}{'W합(엔진vsb)':>17}{'비율':>9}")
    emit("    " + "-" * 55)
    shown = 0
    for L in L_GRID:
        for vgs in VGS_LIST:
            a = widths_at(kind, members, ref, L, vgs, "phys")
            b = widths_at(kind, members, ref, L, vgs, "engine")
            if a is None or b is None:
                continue
            # ★ 최댓값으로 비교하면 안 된다 -- W_max를 쥔 소자가 vsb=0이면
            # 다른 소자의 vsb가 틀려도 차이가 안 드러난다. 그룹 W 합으로 본다.
            wa = sum(x[0] for x in a.values())
            wb = sum(x[0] for x in b.values())
            if abs(wa - wb) / max(wa, 1e-30) < 1e-9:
                continue
            emit(f"    {L*1e6:>8.4f}{vgs:>7.2f}{wa:>14.2f}{wb:>17.2f}{wb/wa:>9.3f}")
            shown += 1
            if shown >= 12:
                break
        if shown >= 12:
            break
    if shown == 0:
        emit("    (차이 없음 -- 이 그룹은 엔진 vsb도 전부 0이다)")

emit("")
emit("완료. 결과 파일:", _RESULT_PATH)
