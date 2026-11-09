# 검증 41 -- 감사 '미측정' 두 가지 실측 (m_j1b/measure_j1b.py 사본 변형, 원본 무수정).
# (a) P4 대 P2 S·F 출발점 t* 차:
#     P2 = D2 = 포화·속도·최소폭 (ID > 0 노드 전부, 봉인 9 그대로라 S_d 만 행 제외)
#     P4 = P2 ∩ (ID > I_off) -- I_off = 같은 (L,VDS,VSB) 곡선의 VGS = 0 마디 ID. ID(VGS) 엄격 단조라 VGS 0 마디만 빠짐(단조 위반 곡선 수도 잰다).
#     옛 D2+ (봉인 9 식 tol 3 경우) 도 같은 판에 두어 P4 와 비교.
# (b) LUT 정적 판정: 각 S·F 소자·설정의 출발점 t*(P4·P2 각각)에서 옛 봉인 9 식(I_off <= (gm/ID) tol_V ID)과 P4 정의(ID > I_off)의 판정이 갈리는 소자 수.
#     (다수 = 그 소자 비지 않은 설정의 >= 50 %, 1개 이상 = 설정 하나라도.)
# 입력은 measure_j1b.py 와 같다(M-J1 devices.jsonl, tolv_cells.json, PDK periphery.csv 의 W_min) -- 읽기만. LUT 는 resolve_lut_location.
import json, os, sys, csv, pathlib, time
import numpy as np
sys.dont_write_bytecode = True
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG))
from gmid_engine.lut.data_location import resolve_lut_location  # noqa: E402
LOC = resolve_lut_location(str(ENG / "assets/lut_v2_location.json"), os.environ)
HERE = pathlib.Path(__file__).parent
EV = HERE.parent
M1 = EV / "m_j1"
LIB = ENG / "assets/library"
Z = np.load(LOC.cap_npz_path, allow_pickle=True)
LG, VG, VD = Z["L"], Z["VGS"], Z["VDS"]
W_REF = float(Z["w_ref_m"]); NV = len(VG)
assert VG[0] == 0.0
W_MIN = None
for row in csv.reader(open(r"C:/pdk/skywater-pdk/docs/rules/periphery/periphery.csv", encoding="utf-8")):
    if row and row[0] == "2" and "Minimum channel width (Diff And Poly)" in row[1] and "2a" in row[1]:
        W_MIN = float(row[3]) * 1e-6
assert W_MIN is not None
TOLV = json.loads((EV / "m_j1b/tolv_cells.json").read_text(encoding="utf-8"))
TAB = {}
mono_bad = {}
for k, kind in (("n", "nmos"), ("p", "pmos")):
    ID, GM, VDSAT, CGG = Z["ID_" + k], Z["GM_" + k], Z["VDSAT_" + k], Z["CGG_" + k]
    mv = lambda a: np.moveaxis(a, 1, 3)
    with np.errstate(all="ignore"):
        g = np.where(ID > 0, GM / ID, np.nan)
        ft = np.where(CGG > 0, GM / (2 * np.pi * CGG), np.nan)
    tl = TOLV[kind]
    loo = np.array([[np.nan if v is None else v for v in r] for r in tl["id_equivalent_v"]], float)
    idm = mv(ID)
    di = VD >= 0.3 - 1e-12
    mono_bad[kind] = int((np.diff(idm[:, di], axis=-1) <= 0).any(-1).sum())
    TAB[k] = dict(id=idm, gm=mv(GM), g=mv(g), ft=mv(ft), vdsat=mv(VDSAT), valid=mv((ID > 0) & (GM > 0)), loo=loo)
IDS = [1e-7, 1e-6, 1e-5, 1e-4, 1e-3]
TOLS = [("t0p1mV", 1e-4), ("t1mV", 1e-3), ("tLOO", None)]


def spec_of(name):
    return json.loads((LIB / f"{name}.sizing_spec.json").read_text(encoding="utf-8"))["human"]


def constraint_value(name, metric, depth=0):
    for c in spec_of(name)["constraints"]:
        if c["metric"] == metric:
            if "value" in c:
                return c["value"]
            if "value_from_file" in c and depth < 3:
                other, m = c["value_from_file"].split("#")
                return constraint_value(other, m, depth + 1)
            if "value_from_constraint" in c:
                return constraint_value(name, c["value_from_constraint"], depth + 1)
    return None


def first_true(m):
    return np.where(m.any(-1), np.argmax(m, -1), -1)


def take(a, ix):
    return np.take_along_axis(a, np.maximum(ix, 0)[..., None], -1)[..., 0]


DEVS = [json.loads(l) for l in (M1 / "devices.jsonl").read_text(encoding="utf-8").splitlines()]
SF = [r for r in DEVS if r["cls"] != "B"]
NSF = {}
for r in SF:
    NSF[r["circuit"]] = NSF.get(r["circuit"], 0) + 1
BUDGET = {c: constraint_value(c, "area_search_m2") for c in NSF}
OUT = HERE / "v41_p4_vs_p2.jsonl"
OUT.write_text("", encoding="utf-8")


def run_device(rec):
    kind = rec["kind"]; T = TAB[kind]
    li = list(range(len(LG))); di = [i for i in range(len(VD)) if VD[i] >= 0.3 - 1e-12]; si = rec["vsb_idx"]
    sel = np.ix_(li, di, si)
    idn, gm, g, ft, vdsat, valid = (T[x][sel] for x in ("id", "gm", "g", "ft", "vdsat", "valid"))
    loo = T["loo"][np.ix_(li, di)][:, :, None, None]
    Lb = LG[:, None, None, None]
    vdsv = VD[np.asarray(di)][None, :, None, None]
    lnidu = np.where(valid, np.log(np.where(idn > 0, idn, 1.0) * Lb / W_REF), np.nan)
    ioff = np.maximum(idn[..., 0], 0.0)[..., None]
    idx = np.arange(NV)[None, None, None, :]
    base = valid & (vdsat <= vdsv)
    if rec["f_req"] is not None:
        base = base & (ft >= rec["f_req"])
    p4row = idn > ioff                     # ID > I_off (선언 방향 ID > 0 은 valid)
    tolarr = {"t0p1mV": 1e-4, "t1mV": 1e-3, "tLOO": loo}
    old = {t: (gm * tolarr[t] >= ioff) for t in tolarr}   # 옛 봉인 9 전도
    budget = BUDGET[rec["circuit"]]
    buds = [("none", None)] + ([("full", budget), ("share", budget / NSF[rec["circuit"]])] if budget else [])
    res = dict(circuit=rec["circuit"], dev=rec["dev"], kind=kind, cls=rec["cls"], f_req=rec["f_req"], combos={})
    for idc in IDS:
        minw = idn <= idc * W_REF / W_MIN
        sd = {"P2": base & minw, "P4": base & minw & p4row}
        for t in tolarr:
            sd["D2P@" + t] = base & minw & old[t]
        for rule in ("ga", "na"):
            att = {}
            for v, s in sd.items():
                att[v] = first_true(s) if rule == "ga" else np.where(s.any(-1), np.argmax(np.where(s, g, -np.inf), -1), -1)
            for bname, B in buds:
                ts = {}
                for v, s in sd.items():
                    ok = s if B is None else s & (idn >= idc * Lb * W_REF / B)
                    if rule == "na":
                        ok = ok & (idx >= att[v][..., None])
                    t_ = first_true(ok)
                    ts[v] = np.where(s.any(-1), t_, -1)
                c = {}
                a, b = ts["P4"], ts["P2"]
                both = (a >= 0) & (b >= 0)
                dl = (take(lnidu, a) - take(lnidu, b))[both]
                dg = ((take(g, a) - take(g, b)) / take(g, b))[both]
                c["P4-P2"] = dict(n=int(both.sum()), n_differ=int((dl != 0).sum()), only_P2=int(((b >= 0) & (a < 0)).sum()),
                                  dln_max=float(np.abs(dl).max()) if dl.size else 0.0, dg_rel_max=float(np.abs(dg).max()) if dg.size else 0.0,
                                  p2_at_node0=int((both & (b == 0)).sum()))
                for t in tolarr:
                    a2 = ts["D2P@" + t]
                    both2 = (a >= 0) & (a2 >= 0)
                    dl2 = (take(lnidu, a2) - take(lnidu, a))[both2]
                    c["D2P-P4@" + t] = dict(n=int(both2.sum()), n_differ=int((dl2 != 0).sum()), dln_max=float(np.abs(dl2).max()) if dl2.size else 0.0)
                # (b) 정적 판정: P4·P2 t* 에서 옛 봉인 9 가 꺼짐(거부)인데 P4 는 전도인 설정 수
                for v in ("P4", "P2"):
                    tt = ts[v]; okp = tt >= 0
                    p4c = okp & take(p4row, tt).astype(bool)
                    for t in tolarr:
                        oc = okp & take(old[t], tt).astype(bool)
                        c[f"judge@{v}@{t}"] = dict(n=int(okp.sum()), old_off_p4_on=int((p4c & ~oc).sum()), old_on_p4_off=int((oc & ~p4c).sum()))
                res["combos"][f"{rule}|ID{idc:g}|{bname}"] = c
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(res) + "\n")


t0 = time.time()
for n, rec in enumerate(SF):
    run_device(rec)
    print(n + 1, len(SF), rec["circuit"], rec["dev"], round(time.time() - t0, 1), flush=True)
with open(HERE / "v41_p4_vs_p2_meta.json", "w", encoding="utf-8") as fh:
    json.dump(dict(n_sf=len(SF), mono_violation_curves=mono_bad, w_min_m=W_MIN, budgets=BUDGET), fh)
print("done", round(time.time() - t0, 1))
