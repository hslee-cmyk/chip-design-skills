# K3 / J1 측정 -- S·F 소자 출발값 = 출발 구간 S_d 아래 끝(ln IDu 최소) 대 S_d 안 gm/ID 최대점.
# 입력: LUT r2 (assets/lut_v2_location.json 의 cap_npz 만), library 13회로 topology+sizing_spec, S1v 구조 분류(s1v_roles.jsonl, s1v_probe.py).
# 쓰기: 이 폴더 안만 (devices.jsonl 소자마다 append, sweep.jsonl, curves_summary.json).
#
# S_d 구현(design 41 §6.1-6/7 머리 '좌표와 구간 꼴'): S_d = (순방향 제약 행 해 집합의 교집합) ∩ LUT 정의역 ∩ 최소 폭 하한.
#   - LUT 정의역: 두 해석을 나눠 잰다.
#       D2 = (L, VDS, VSB) 곡선의 ID>0 인 VGS 마디 전부(약반전 포함)       [문언 'LUT 정의역' 문자 그대로]
#       D1 = D2 중 gm/ID 정점(가장 왼쪽 argmax) 이상 + ln ID 엄격 증가 첫 구간 [lut/CONTRACT 3.1 순방향 조회 정의역: 강반전 분지]
#   - 포화 행(헤드룸 행의 대표): VDSAT(마디) <= VDS.   (V_part = VDS 로 둔 대표; 기둥 분할은 엔진 DC 풀이 필요 -> 미구현, 상단 끝에만 영향)
#   - 속도 행(§6.3): f_T(마디) >= f_np_min = GBW / tan(90deg - PM)   (필요조건 -- f_T = GM / (2 pi CGG), LUT C 열 CGG 포함 -- 원칙 1;
#       PM 미선언 + GBW 선언이면 PM_FLOOR 45 deg 경로 -> f_np_min = GBW).  gbw 선언이 없는 회로는 속도 행 비활성(§6.3 전제).
#   - 최소 폭 하한: ln IDu <= ln(ID L / W_min) -- ID 를 모르면(엔진 DC 풀이 필요) 상단 끝만 자르므로 미구현(아래 끝 불변, 차 크기는 상한).
#   - 면적 조건 행·부하 가드·잡음 가드: 상단 끝 행(ln IDu 상한) 또는 ID 필요 -> 미구현 (아래 끝 불변).
# 변형: A = D2 ∩ 포화 ;  B = D2 ∩ 포화 ∩ 속도 ;  C = D1 ∩ 포화 ∩ 속도.
import json, math, pathlib, sys
import numpy as np

HERE = pathlib.Path(__file__).parent
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
LIB = ENG / "assets/library"
LOC = json.loads((ENG / "assets/lut_v2_location.json").read_text(encoding="utf-8"))
Z = np.load(pathlib.Path(LOC["root"]["default"]) / LOC["files"]["cap_npz"]["path"], allow_pickle=True)
LG, VG, VD, VS = Z["L"], Z["VGS"], Z["VDS"], Z["VS"]
NV = len(VG)
OUT_DEV = HERE / "devices.jsonl"
OUT_SW = HERE / "sweep.jsonl"

TAB = {}
for k in ("n", "p"):
    ID, GM, VDSAT, CGG = Z["ID_" + k], Z["GM_" + k], Z["VDSAT_" + k], Z["CGG_" + k]
    with np.errstate(all="ignore"):
        g = np.where(ID > 0, GM / ID, np.nan)
        ft = np.where(CGG > 0, GM / (2 * np.pi * CGG), np.nan)
        lnid = np.where(ID > 0, np.log(ID), np.nan)
    # 축 (L, VGS, VDS, VS) -> (L, VDS, VS, VGS)
    TAB[k] = dict(g=np.moveaxis(g, 1, 3), ft=np.moveaxis(ft, 1, 3), vdsat=np.moveaxis(VDSAT, 1, 3),
                  lnid=np.moveaxis(lnid, 1, 3), valid=np.moveaxis((ID > 0) & (GM > 0), 1, 3))


def first_true(m):
    any_ = m.any(axis=-1)
    return np.where(any_, np.argmax(m, axis=-1), -1)


def stats(a):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return None
    q = np.quantile(a, [0, .25, .5, .75, .9, 1])
    return dict(n=int(a.size), min=float(q[0]), q25=float(q[1]), med=float(q[2]), q75=float(q[3]), q90=float(q[4]), max=float(q[5]))


def evaluate(kind, li, di, si, f_req, want_arrays=False):
    """선택 (L 인덱스들, VDS 인덱스들, VSB 인덱스들) 곡선 전체에서 세 변형의 아래 끝·최대점을 잰다. 반환: dict 변형 -> 배열 묶음."""
    T = TAB[kind]
    sel = np.ix_(li, di, si)
    g, ft, vds_sat, lnid, valid = (T[x][sel] for x in ("g", "ft", "vdsat", "lnid", "valid"))
    vdsv = VD[np.asarray(di)][None, :, None, None]
    gm_ = np.where(valid, g, -np.inf)
    peak = np.argmax(gm_, axis=-1)                           # 가장 왼쪽 argmax (전체 곡선, 포화 행 이전)
    idx = np.arange(NV)[None, None, None, :]
    # D1: 정점 이상 + ln ID 엄격 증가 첫 구간 [p, end] (monotone_end: q[p]<q[p+1]<...<q[end])
    d_up = np.concatenate([np.diff(lnid, axis=-1) > 0, np.zeros(valid.shape[:-1] + (1,), bool)], axis=-1)   # 마디 j 에서 j+1 로 증가?
    stop = ~d_up & (idx >= peak[..., None])
    end = np.argmax(stop, axis=-1)                           # 정점 이상에서 처음으로 증가가 끊기는 마디 (마지막 마디는 항상 stop)
    ok = (idx >= peak[..., None]) & (idx <= end[..., None])
    d1 = ok & valid
    sat = valid & (vds_sat <= vdsv)
    out = {}
    for name, dom, spd in (("A", valid, False), ("B", valid, True), ("C", d1, True)):
        m = dom & sat
        if spd and f_req is not None:
            m = m & (ft >= f_req)
        lo = first_true(m)
        gg = np.where(m, g, -np.inf)
        am = np.argmax(gg, axis=-1)
        nonempty = lo >= 0
        lo_c = np.where(nonempty, lo, 0)
        take = lambda a, ix: np.take_along_axis(a, ix[..., None], -1)[..., 0]
        vg_lo, vg_am = VG[lo_c], VG[am]
        g_lo, g_am = take(g, lo_c), take(g, am)
        y_lo, y_am = take(lnid, lo_c), take(lnid, am)
        res = dict(nonempty=nonempty, left=nonempty & (lo_c < peak), differ=nonempty & (am != lo_c),
                   dvgs=np.where(nonempty, vg_am - vg_lo, np.nan), dg=np.where(nonempty, g_am - g_lo, np.nan),
                   drel=np.where(nonempty, (g_am - g_lo) / g_lo, np.nan), dlnidu=np.where(nonempty, y_am - y_lo, np.nan),
                   vg_lo=np.where(nonempty, vg_lo, np.nan), vg_peak=VG[peak], g_peak=take(g, peak),
                   dvgs_peak=np.where(nonempty, VG[peak] - vg_lo, np.nan), dg_peak=np.where(nonempty, take(g, peak) - g_lo, np.nan),
                   drel_peak=np.where(nonempty, (take(g, peak) - g_lo) / g_lo, np.nan))
        out[name] = res
    return out


def per_l(res):
    out = {}
    for name, r in res.items():
        ne = r["nonempty"]
        rows = []
        for l in range(ne.shape[0]):
            d = r["differ"][l]; n = ne[l]
            def mx(a):
                v = np.where(d, a[l], np.nan)
                return float(np.nanmax(v)) if d.any() else None
            def md(a):
                v = np.where(d, a[l], np.nan)
                return float(np.nanmedian(v)) if d.any() else None
            rows.append(dict(L_um=float(LG[l] * 1e6), n_nonempty=int(n.sum()), n_left=int(r["left"][l].sum()), n_differ=int(d.sum()),
                             n_gt1pct=int(((r["drel"][l] > 0.01) & n).sum()), n_gt5pct=int(((r["drel"][l] > 0.05) & n).sum()),
                             dvgs_med=md(r["dvgs"]), dvgs_max=mx(r["dvgs"]), drel_med=md(r["drel"]), drel_max=mx(r["drel"]),
                             dlnidu_med=md(r["dlnidu"]), dlnidu_max=mx(r["dlnidu"]), dg_max=mx(r["dg"])))
        out[name] = rows
    return out


def summarise(res, dev_has_speed):
    s = {}
    for name, r in res.items():
        ne = r["nonempty"]
        n_cfg = int(ne.size)
        n_ne = int(ne.sum())
        s[name] = dict(n_cfg=n_cfg, n_nonempty=n_ne, n_left=int(r["left"].sum()), n_differ=int(r["differ"].sum()),
                       dvgs=stats(r["dvgs"][ne]), dg=stats(r["dg"][ne]), drel=stats(r["drel"][ne]), dlnidu=stats(r["dlnidu"][ne]),
                       dvgs_peak=stats(r["dvgs_peak"][ne]), dg_peak=stats(r["dg_peak"][ne]),
                       n_differ_rel_gt_0p1pct=int(((r["drel"] > 0.001) & ne).sum()),
                       n_left_rel_gt_0p1pct=int((r["left"] & (r["drel_peak"] > 0.001)).sum()), n_left_rel_gt_1pct=int((r["left"] & (r["drel_peak"] > 0.01)).sum()),
                       drel_peak=stats(r["drel_peak"][r["left"]]),
                       n_differ_rel_gt_1pct=int(((r["drel"] > 0.01) & ne).sum()), n_differ_rel_gt_5pct=int(((r["drel"] > 0.05) & ne).sum()),
                       n_differ_dvgs_gt_50mV=int(((r["dvgs"] > 0.05) & ne).sum()))
    return s


# ---------------- 소자 분류 (R13) ----------------
S1V = {}
for l in (HERE / "s1v_roles.jsonl").read_text(encoding="utf-8").splitlines():
    r = json.loads(l)
    S1V[r["circuit"]] = r


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


def vsb_cfg(topo, supplies, d):
    """소자의 VSB 인덱스 집합과 표지. 소스 넷 전위가 선언(공급·agnd)이면 |V_b - V_s| 에 인접한 격자 마디, 아니면 0 이 아닌 격자 마디 전부(<= 공급 폭)."""
    kind = d["kind"]
    rails = {k: v for k, v in supplies.items()}
    lo_n = min(rails, key=lambda k: rails[k]); hi_n = max(rails, key=lambda k: rails[k])
    bulk = d.get("bulk") or (lo_n if kind == "nmos" else hi_n)
    vb = rails.get(bulk)
    src = d["source"]
    if vb is not None and src in rails:
        vsb = (rails[src] - vb) if kind == "nmos" else (vb - rails[src])
        vsb = max(vsb, 0.0)
        j = np.searchsorted(VS, vsb)
        if j < len(VS) and abs(VS[j] - vsb) < 1e-9:
            return [int(j)], f"fixed {vsb:.3g} V (source {src} = declared net)"
        return sorted({int(max(j - 1, 0)), int(min(j, len(VS) - 1))}), f"fixed {vsb:.3g} V -> bracket grid {VS[max(j-1,0)]:.2g},{VS[min(j,len(VS)-1)]:.2g}"
    span = max(rails.values()) - min(rails.values())
    idx = [int(i) for i in range(1, len(VS)) if VS[i] <= span + 1e-9]
    return idx, f"unknown (source {src} not a declared net) -> VSB grid {VS[idx[0]]:.2g}..{VS[idx[-1]]:.2g}"


def classify(circuit):
    s1v = S1V[circuit]
    view = s1v["views"][0]
    assert view["id"] == "transfer:0"
    roles = {}
    for b in view["blocks"]:
        for dev, role in b["roles"]:
            roles.setdefault(dev, (role, b["kind"]))
    return roles


def main():
    for p in (OUT_DEV, OUT_SW):
        if p.exists():
            p.unlink()
    tot = {}
    for p in sorted(LIB.glob("*.topology.json")):
        if p.name.startswith("_"):
            continue
        circuit = p.name.replace(".topology.json", "")
        topo = json.loads(p.read_text(encoding="utf-8"))
        sp = spec_of(circuit)
        supplies = {k: v for k, v in sp["supplies_v"]["values"].items()}
        gbw = constraint_value(circuit, "gbw_ss_hz")
        pm = constraint_value(circuit, "pm_ss_deg")
        macro = gbw is not None
        pm_eff = pm if pm is not None else 45.0
        f_req = (gbw / math.tan(math.radians(90.0 - pm_eff))) if macro else None
        roles = classify(circuit)
        mos = [d for d in topo["netlist"] if d["kind"] in ("nmos", "pmos")]
        missing = [d["name"] for d in mos if d["name"] not in roles]
        for d in mos:
            role, bk = roles.get(d["name"], (None, None))
            if role == "input":
                cls = "S" if macro else "F"
            elif role in ("cascode", "pass", "follower"):
                cls = "F"
            else:
                cls = "B"
            kind = "n" if d["kind"] == "nmos" else "p"
            rec = dict(circuit=circuit, dev=d["name"], kind=kind, role=role, block_kind=bk, cls=cls, macro=macro,
                       gbw=gbw, pm=pm, f_req=f_req, no_block=(role is None))
            if cls != "B":
                vi, vnote = vsb_cfg(topo, supplies, d)
                li = list(range(len(LG)))
                di = [i for i in range(len(VD)) if VD[i] >= 0.3 - 1e-12]
                res = evaluate(kind, li, di, vi, f_req)
                rec.update(vsb_idx=vi, vsb_note=vnote, summary=summarise(res, macro), perL=per_l(res))
            with open(OUT_DEV, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(circuit, "S/F:", sum(1 for d in mos if (roles.get(d["name"], (None,))[0] in ("input", "cascode", "pass", "follower"))),
              "of", len(mos), "macro", macro, "f_req", f_req, "missing", missing[:3])


def sweep():
    """f_req 소거 지도: kind x VSB 부류(0 / >0) 에서 f_req 를 로그 격자로 훑어 '아래 끝 != 최대점' 곡선 비율.  변형 C, B 모두."""
    freqs = [10 ** (e / 2) for e in range(10, 22)]        # 1e5 ... 3e10 (반 decade)
    for kind in ("n", "p"):
        for vname, vi in (("VSB0", [0]), ("VSB>0", list(range(1, len(VS))))):
            for f in freqs:
                li = list(range(len(LG))); di = [i for i in range(len(VD)) if VD[i] >= 0.3 - 1e-12]
                res = evaluate(kind, li, di, vi, f)
                row = dict(kind=kind, vsb=vname, f_req=f)
                for name in ("B", "C"):
                    r = res[name]; ne = r["nonempty"]
                    row[name] = dict(n_nonempty=int(ne.sum()), n_left=int(r["left"].sum()), n_differ=int(r["differ"].sum()),
                                     n_differ_rel_gt_0p1pct=int(((r["drel"] > 0.001) & ne).sum()),
                       n_left_rel_gt_0p1pct=int((r["left"] & (r["drel_peak"] > 0.001)).sum()), n_left_rel_gt_1pct=int((r["left"] & (r["drel_peak"] > 0.01)).sum()),
                       drel_peak=stats(r["drel_peak"][r["left"]]),
                       n_differ_rel_gt_1pct=int(((r["drel"] > 0.01) & ne).sum()),
                                     dvgs_med=stats(r["dvgs"][r["differ"]])["med"] if r["differ"].any() else None,
                                     dvgs_max=stats(r["dvgs"][r["differ"]])["max"] if r["differ"].any() else None,
                                     drel_med=stats(r["drel"][r["differ"]])["med"] if r["differ"].any() else None,
                                     drel_max=stats(r["drel"][r["differ"]])["max"] if r["differ"].any() else None)
                with open(OUT_SW, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
    if len(sys.argv) > 1 and sys.argv[1] == "sweep":
        sweep()
