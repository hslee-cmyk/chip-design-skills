# M-J1b -- 실제 출발점(사다리 칸 0 t*)이 K10 행 선택(D1/D2+/D2)과 K3 규칙((가) 아래 끝/(나) 가장 왼쪽 argmax)에 따라 얼마나 바뀌는가.
# 정의 정본 = wt/_drafts/evidence/2026-10-31/plan_v6386_decision_candidates.md K3·K10 'M-J1b 측정 정의'.
# 입력: LUT v2 r2 (assets/lut_v2_location.json -> cap_npz, 보간 없음 격자 원값), library 13회로 topology/sizing_spec, M-J1 devices.jsonl(분류 S/F·VSB 마디·f_req),
#       tolv_cells.json(엔진 lut 모듈 tol_v_table 의 LOO 셀값, tolv.py).  저장소 쓰기 0, 엔진 파이프라인(run_stage_*/start_intervals) 호출 0.
#
# 구현한 S_d 행(design 41 §6 머리, 격자 노드 = LUT VGS 마디, ln ID 는 VGS 에 엄격 증가라 ln IDu 순서 = VGS 순서):
#   - 포화 행(M-J1 그대로): VDSAT(노드) <= VDS.
#   - 속도 행(M-J1 그대로, C 열 CGG 포함): f_T = GM/(2 pi CGG) >= f_req (gbw 선언 회로만).
#   - 최소 폭 행: W = ID_dev L/IDu >= W_min  <=>  ID_node(W_ref) <= ID_dev * W_ref / W_min.   W_min = PDK min_finger_w_m (difftap.2).
#   - [K10] 반전 수준 하한 행(DEC-88): 노드 >= 그 (L,VDS,VSB) 곡선의 gm/ID 가장 왼쪽 argmax(floor_m) -- 곡선 전체(포화 행 이전) 기준(M-J1 '정점' 정의).
#   - [K10] 전도 여유 행(DEC-88 봉인 9): I_off <= (gm/ID) tol_V ID  <=>  GM(노드) tol_V >= ID(VGS=0 노드).  tol_V 3 경우: 0.1 mV, 1 mV, LOO 셀값(L 앵커,VDS 칸, id_equivalent_v).
#   변형 D1 = 포화·속도·최소폭 + 반전 수준 하한 + 전도 여유 / D2+ = 포화·속도·최소폭 + 전도 여유 / D2 = 포화·속도·최소폭(ID>0 노드 전부).
#   미구현(표지): 면적 조건 행(§6.4-2, 절대 offset 제약 회로만 = current_reuse 1/13, 상한 행), 부하 가드·잡음 가드(상한 행), 헤드룸 V_part 분할(V_part = VDS 대표).
# 출발점: 사다리 칸 0 = 면적 <= 예산인 최대 t* = S_d 안 면적 실행 가능 노드 중 가장 낮은 ln IDu (면적 W L = ID_dev L W_ref / ID_node 은 ln IDu 에 감소 -> 실행 가능 집합은 위 끝 쪽 집합).
#   (가) 시도점 = S_d 아래 끝, t* = S_d ∩ 면적 실행 가능 가운데 가장 낮은 노드.
#   (나) 시도점 = S_d 안 gm/ID 가장 왼쪽 argmax, t* = 그 노드 이상(ln IDu 같거나 큰 쪽)에서 S_d ∩ 면적 실행 가능인 가장 낮은 노드.
#   매크로 근 조건은 엔진 없이 못 재므로 뺐다(표지).  면적 예산 경우: none(예산 무시) / full(소자 하나가 예산 전부, 필요조건) / share(예산/n_SF, 같은 몫 가정 -- 경우 나눔).
# ID_dev(엔진 없이 gm_req·KCL 전류를 못 재므로 경우 나눔): 1e-7 ... 1e-3 A (십진 5칸, 값 주장 아님).
import json, math, pathlib, sys, time, csv
import numpy as np

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).parent
M1 = HERE.parent / "m_j1"
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
LIB = ENG / "assets/library"
LOC = json.loads((ENG / "assets/lut_v2_location.json").read_text(encoding="utf-8"))
Z = np.load(pathlib.Path(LOC["root"]["default"]) / LOC["files"]["cap_npz"]["path"], allow_pickle=True)
LG, VG, VD, VS = Z["L"], Z["VGS"], Z["VDS"], Z["VS"]
W_REF = float(Z["w_ref_m"])
NV = len(VG)
assert VG[0] == 0.0

# W_min = PDK min_finger_w_m (sky130_pdk_decl.json: source periphery_rules, expression difftap.2)
W_MIN = None
for row in csv.reader(open(r"C:/pdk/skywater-pdk/docs/rules/periphery/periphery.csv", encoding="utf-8")):
    if row and row[0] == "2" and "Minimum channel width (Diff And Poly)" in row[1] and "2a" in row[1]:
        W_MIN = float(row[3]) * 1e-6
assert W_MIN is not None
TOLV = json.loads((HERE / "tolv_cells.json").read_text(encoding="utf-8"))

TAB = {}
for k, kind in (("n", "nmos"), ("p", "pmos")):
    ID, GM, VDSAT, CGG = Z["ID_" + k], Z["GM_" + k], Z["VDSAT_" + k], Z["CGG_" + k]
    mv = lambda a: np.moveaxis(a, 1, 3)          # (L,VGS,VDS,VS) -> (L,VDS,VS,VGS)
    with np.errstate(all="ignore"):
        g = np.where(ID > 0, GM / ID, np.nan)
        ft = np.where(CGG > 0, GM / (2 * np.pi * CGG), np.nan)
    tl = TOLV[kind]
    assert np.allclose(np.array(tl["L_m"]), LG) and np.allclose(np.array(tl["VDS"]), VD)
    loo = np.array([[np.nan if v is None else v for v in r] for r in tl["id_equivalent_v"]], float)       # (L, VDS)
    TAB[k] = dict(id=mv(ID), gm=mv(GM), g=mv(g), ft=mv(ft), vdsat=mv(VDSAT), valid=mv((ID > 0) & (GM > 0)), loo=loo)

IDS = [1e-7, 1e-6, 1e-5, 1e-4, 1e-3]
TOLS = [("t0p1mV", 1e-4), ("t1mV", 1e-3), ("tLOO", None)]
VARS = ["D1", "D2P", "D2"]
RULES = ["ga", "na"]                  # (가) 아래 끝 / (나) 가장 왼쪽 argmax
VT = [("D1", t[0]) for t in TOLS] + [("D2P", t[0]) for t in TOLS] + [("D2", "-")]


def vt_name(v, t):
    return v if t == "-" else f"{v}@{t}"


def first_true(m):
    return np.where(m.any(axis=-1), np.argmax(m, axis=-1), -1)


def take(a, ix):
    return np.take_along_axis(a, np.maximum(ix, 0)[..., None], -1)[..., 0]


def q3(a):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return None
    return [float(a.min()), float(np.median(a)), float(a.max())]


def spec_of(name):
    return json.loads((LIB / f"{name}.sizing_spec.json").read_text(encoding="utf-8"))["human"]


def constraint_value(name, metric, depth=0):
    sp = spec_of(name)
    for c in sp["constraints"]:
        if c["metric"] == metric:
            if "value" in c:
                return c["value"]
            if "value_from_file" in c and depth < 3:
                other, m = c["value_from_file"].split("#")
                return constraint_value(other, m, depth + 1)
            if "value_from_constraint" in c:
                return constraint_value(name, c["value_from_constraint"], depth + 1)
    return None


DEVS = [json.loads(l) for l in (M1 / "devices.jsonl").read_text(encoding="utf-8").splitlines()]
SF = [r for r in DEVS if r["cls"] != "B"]
import os
if os.environ.get("J1B_LIMIT"): SF = SF[:int(os.environ["J1B_LIMIT"])]
NSF = {}
for r in SF:
    NSF[r["circuit"]] = NSF.get(r["circuit"], 0) + 1
BUDGET = {c: constraint_value(c, "area_search_m2") for c in NSF}

POOL = {}          # (kind_of_comparison, ...) -> {(cls, kind): dict(n=, nd=, nd1=, nd5=, gdiff1=, samp=[(dlnidu, dvgs, dg)])}
STRIDE_KEEP = 300


def pool_add(key, cls, kind, dl, dv, dg, rel):
    P = POOL.setdefault(key, {}).setdefault((cls, kind), dict(n=0, nd=0, nd1=0, nd5=0, g1=0, dev=0, devh=0, samp=[]))
    P["n"] += int(dl.size)
    P["nd"] += int((dl != 0).sum()); P["nd1"] += int((np.abs(dl) > 1).sum()); P["nd5"] += int((np.abs(dl) > 5).sum())
    P["g1"] += int((np.abs(rel) > 0.01).sum())
    if dl.size:
        P["dev"] += 1
        P["devh"] += int((dl != 0).mean() >= 0.5)
        step = max(1, dl.size // STRIDE_KEEP)
        P["samp"].append(np.stack([dl[::step], dv[::step], dg[::step]], 1).astype(np.float32))


def run_device(rec, out_fh):
    kind = rec["kind"]; T = TAB[kind]
    li = list(range(len(LG))); di = [i for i in range(len(VD)) if VD[i] >= 0.3 - 1e-12]; si = rec["vsb_idx"]
    sel = np.ix_(li, di, si)
    idn, gm, g, ft, vdsat, valid = (T[x][sel] for x in ("id", "gm", "g", "ft", "vdsat", "valid"))
    loo = T["loo"][np.ix_(li, di)][:, :, None, None]           # (nL, nD, 1, 1)
    Lb = LG[:, None, None, None]
    vdsv = VD[np.asarray(di)][None, :, None, None]
    shape = idn.shape[:3]
    ncfg = int(np.prod(shape))
    lnidu = np.where(valid, np.log(np.where(idn > 0, idn, 1.0) * Lb / W_REF), np.nan)
    ioff = np.maximum(idn[..., 0], 0.0)[..., None]
    gg = np.where(valid, g, -np.inf)
    peak = np.argmax(gg, axis=-1)
    idx = np.arange(NV)[None, None, None, :]
    floor_ok = idx >= peak[..., None]
    base = valid & (vdsat <= vdsv)
    f_req = rec["f_req"]
    if f_req is not None:
        base = base & (ft >= f_req)
    tolarr = {"t0p1mV": 1e-4, "t1mV": 1e-3, "tLOO": loo}
    cond = {t: (gm * tolarr[t] >= ioff) for t in tolarr}
    budget = BUDGET[rec["circuit"]]
    buds = [("none", None)] + ([("full", budget), ("share", budget / NSF[rec["circuit"]])] if budget else [])
    T_ = {}         # (vt, rule, idc, bud) -> (att_idx, ts_idx)
    combos = {}
    for idc in IDS:
        minw = idn <= idc * W_REF / W_MIN
        for v, t in VT:
            sd = base & minw
            if v == "D1":
                sd = sd & cond[t] & floor_ok
            elif v == "D2P":
                sd = sd & cond[t]
            vt = vt_name(v, t)
            lo = first_true(sd)
            am = np.where(sd.any(axis=-1), np.argmax(np.where(sd, g, -np.inf), axis=-1), -1)
            nonempty = lo >= 0
            for rule, att in (("ga", lo), ("na", am)):
                for bname, B in buds:
                    if B is None:
                        ok = sd
                    else:
                        area_ok = idn >= idc * Lb * W_REF / B
                        ok = sd & area_ok
                    if rule == "na":
                        ok = ok & (idx >= att[..., None])
                    ts = first_true(ok)
                    ts = np.where(nonempty, ts, -1)
                    T_[(vt, rule, idc, bname)] = (att, ts, nonempty)
    # ---- 기록 -----
    dev_rec = dict(circuit=rec["circuit"], dev=rec["dev"], kind=kind, cls=rec["cls"], role=rec["role"], f_req=f_req, budget_m2=budget,
                   n_sf_circuit=NSF[rec["circuit"]], n_cfg=ncfg, vsb_note=rec["vsb_note"], w_min_m=W_MIN, combos={})
    for (vt, rule, idc, bname), (att, ts, nonempty) in T_.items():
        def pt(ix):
            ok = ix >= 0
            vgs = np.where(ok, VG[np.maximum(ix, 0)], np.nan)
            gv = np.where(ok, take(g, ix), np.nan)
            ln = np.where(ok, take(lnidu, ix), np.nan)
            idnv = np.where(ok, take(idn, ix), np.nan)
            w = idc * W_REF / idnv
            return dict(lnidu=q3(ln), vgs=q3(vgs), gm_id=q3(gv), w_m=q3(w), n=int(ok.sum()))
        # 누설 영역 = 전도 여유 위반(I_off > (gm/ID) tol_V ID) -- tol 경우별
        def leak(ix):
            ok = ix >= 0
            return {t: int((ok & ~take(cond[t], ix).astype(bool)).sum()) for t in tolarr}
        moved = int(((ts >= 0) & (att >= 0) & (ts != att)).sum())
        miss = int((nonempty & (ts < 0)).sum())
        c = dict(sd_nonempty=int(nonempty.sum()), att=pt(att), ts=pt(ts), moved=moved, ts_missing=miss, leak_att=leak(att), leak_ts=leak(ts))
        dev_rec["combos"]["|".join([vt, rule, f"ID{idc:g}", bname])] = c
    out_fh.write(json.dumps(dev_rec) + "\n"); out_fh.flush()
    # ---- 풀링: 변형 사이·규칙 사이 t* 차 -----
    cls, k = rec["cls"], kind
    lnflat = lnidu
    for idc in IDS:
        for bname, B in buds:
            for rule in RULES:
                for t, _ in TOLS:
                    pairs = [(("D1", t), ("D2P", t)), (("D1", t), ("D2", "-")), (("D2P", t), ("D2", "-"))]
                    for a, b in pairs:
                        ia = T_[(vt_name(*a), rule, idc, bname)][1]; ib = T_[(vt_name(*b), rule, idc, bname)][1]
                        both = (ia >= 0) & (ib >= 0)
                        dl = (take(lnidu, ia) - take(lnidu, ib))[both]
                        dv = (VG[np.maximum(ia, 0)] - VG[np.maximum(ib, 0)])[both]
                        ga, gb = take(g, ia)[both], take(g, ib)[both]
                        pool_add(("K10", rule, f"{a[0]}-{b[0]}", t, idc, bname), cls, k, dl, dv, ga - gb, (ga - gb) / gb)
            for v, t in VT:
                vt = vt_name(v, t)
                ia = T_[(vt, "na", idc, bname)][1]; ib = T_[(vt, "ga", idc, bname)][1]
                both = (ia >= 0) & (ib >= 0)
                dl = (take(lnidu, ia) - take(lnidu, ib))[both]
                dv = (VG[np.maximum(ia, 0)] - VG[np.maximum(ib, 0)])[both]
                ga, gb = take(g, ia)[both], take(g, ib)[both]
                pool_add(("K3", "na-ga", vt, "-", idc, bname), cls, k, dl, dv, ga - gb, (ga - gb) / gb)


def main():
    t0 = time.time()
    out = HERE / "devices_j1b.jsonl"
    if out.exists():
        out.unlink()
    with open(out, "a", encoding="utf-8") as fh:
        for n, rec in enumerate(SF):
            run_device(rec, fh)
            print(n + 1, len(SF), rec["circuit"], rec["dev"], round(time.time() - t0, 1), flush=True)
    # 풀링 요약 (quantile)
    res = {}
    for key, d in POOL.items():
        for (cls, kind), P in d.items():
            s = np.concatenate(P["samp"], 0) if P["samp"] else np.zeros((0, 3), np.float32)
            def qs(col):
                if s.shape[0] == 0:
                    return None
                a = np.abs(s[:, col])
                return [float(np.quantile(a, x)) for x in (0.5, 0.9, 1.0)]
            res["|".join(map(str, key)) + f"|{cls}|{kind}"] = dict(
                n=P["n"], n_differ=P["nd"], n_dln_gt1=P["nd1"], n_dln_gt5=P["nd5"], n_dg_rel_gt1pct=P["g1"], n_dev=P["dev"], n_dev_majority_differ=P["devh"],
                abs_dlnidu_p50_p90_max=qs(0), abs_dvgs_p50_p90_max=qs(1), abs_dgm_id_p50_p90_max=qs(2), n_samp=int(s.shape[0]))
    (HERE / "pooled_j1b.json").write_text(json.dumps(res), encoding="utf-8")
    print("done", round(time.time() - t0, 1), "s", len(res), "pool keys")


if __name__ == "__main__":
    main()
