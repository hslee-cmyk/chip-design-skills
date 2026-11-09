# O-200 Q5 측정 1a -- K10 하네스(o200_v41/v41_p4_vs_p2.py 와 같은 115 S·F 소자·입력·설정: M-J1 devices.jsonl, LUT cap_npz 격자 원값 = w_key 1000(5 µm),
# W_min = PDK 최소 finger 폭 선언 값의 원 파일 행, ID 경우 5칸, 면적 예산 3경우, 규칙 (가)/(나)) 에서 포화 행만 두 꼴로 바꿔 S_d 절단과 출발점 t* 이동을 잰다.
#   noTol: VDSAT(노드) <= VDS       Tol: VDSAT(노드) + tol_VDsat(셀) <= VDS
#   tol_VDsat(셀) = (L 앵커, VDS 칸) 조회 규칙(같은 L 앵커 행, VDS 칸 [k, k+1] 두 셀 최댓값) -- 셀 값은 q5_tolvdsat_indep.py 로 독립 재계산과 비트 동일 확인된 엔진 표.
#   S_d 변형: P2 = 포화·속도·최소폭 / D2P = P2 ∩ 전도 여유(LOO tol_V, 옛 봉인 9 식). 헤드룸 V_part 분할은 하네스 미구현(V_part = 소자 VDS 대표) -- 그래서
#   이 하네스의 '헤드룸 행'은 소자 하나의 VDS 행이고 Σ tol_VDsat = 그 소자 셀값 하나다(경로 합은 q5_engine.py 헤드룸 행 기록).
# 산출: q5_k10_lut.jsonl (소자마다 1줄, Python append), q5_k10_lut_meta.json.
import json, os, sys, csv, pathlib, time
import numpy as np
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
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
W_MIN = None
for row in csv.reader(open(r"C:/pdk/skywater-pdk/docs/rules/periphery/periphery.csv", encoding="utf-8")):
    if row and row[0] == "2" and "Minimum channel width (Diff And Poly)" in row[1] and "2a" in row[1]:
        W_MIN = float(row[3]) * 1e-6
assert W_MIN is not None
TOLV = json.loads((EV / "m_j1b/tolv_cells.json").read_text(encoding="utf-8"))
import importlib
R = importlib.import_module("gmid_engine.tests.search.u13_real")
from gmid_engine.lut import tol_vdsat_table
env = R.real_env()
GRID_W = float(json.loads(pathlib.Path(LOC.manifest_path).read_text(encoding="utf-8")).get("manufacturing_grid_m") or 5e-9)
WK = int(round(W_REF / GRID_W))
TAB = {}
for k, kind in (("n", "nmos"), ("p", "pmos")):
    ID, GM, VDSAT, CGG = Z["ID_" + k], Z["GM_" + k], Z["VDSAT_" + k], Z["CGG_" + k]
    mv = lambda a: np.moveaxis(a, 1, 3)
    with np.errstate(all="ignore"):
        g = np.where(ID > 0, GM / ID, np.nan)
        ft = np.where(CGG > 0, GM / (2 * np.pi * CGG), np.nan)
    loo = np.array([[np.nan if v is None else v for v in r] for r in TOLV[kind]["id_equivalent_v"]], float)
    tb = tol_vdsat_table(env.memo, kind, WK)
    assert np.allclose(np.asarray(tb.L_anchors, float), LG) and np.allclose(np.asarray(tb.vds_grid, float), VD)
    cell = np.array([[np.nan if c.vdsat_v is None else c.vdsat_v for c in r] for r in tb.cells], float)   # [L, VDS]
    kk = np.minimum(np.arange(len(VD)), len(VD) - 2)
    tq = np.fmax(cell[:, kk], cell[:, kk + 1])     # 격자점 VDS_k 조회의 칸 [k, k+1] 최댓값 (table_at)
    TAB[k] = dict(id=mv(ID), gm=mv(GM), g=mv(g), ft=mv(ft), vdsat=mv(VDSAT), valid=mv((ID > 0) & (GM > 0)), loo=loo, tq=tq)
IDS = [1e-7, 1e-6, 1e-5, 1e-4, 1e-3]


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


def q(a):
    a = np.asarray(a, float); a = a[np.isfinite(a)]
    return None if a.size == 0 else [float(np.min(a)), float(np.median(a)), float(np.quantile(a, 0.9)), float(np.max(a))]


DEVS = [json.loads(l) for l in (M1 / "devices.jsonl").read_text(encoding="utf-8").splitlines()]
SF = [r for r in DEVS if r["cls"] != "B"]
NSF = {}
for r in SF:
    NSF[r["circuit"]] = NSF.get(r["circuit"], 0) + 1
BUDGET = {c: constraint_value(c, "area_search_m2") for c in NSF}
OUT = HERE / "q5_k10_lut.jsonl"; OUT.write_text("", encoding="utf-8")


def run_device(rec):
    kind = rec["kind"]; T = TAB[kind]
    li = list(range(len(LG))); di = [i for i in range(len(VD)) if VD[i] >= 0.3 - 1e-12]; si = rec["vsb_idx"]
    sel = np.ix_(li, di, si)
    idn, gm, g, ft, vdsat, valid = (T[x][sel] for x in ("id", "gm", "g", "ft", "vdsat", "valid"))
    loo = T["loo"][np.ix_(li, di)][:, :, None, None]
    tq = T["tq"][np.ix_(li, di)][:, :, None, None]
    Lb = LG[:, None, None, None]
    vdsv = VD[np.asarray(di)][None, :, None, None]
    lnidu = np.where(valid, np.log(np.where(idn > 0, idn, 1.0) * Lb / W_REF), np.nan)
    ioff = np.maximum(idn[..., 0], 0.0)[..., None]
    idx = np.arange(NV)[None, None, None, :]
    sat0 = valid & (vdsat <= vdsv)
    sat1 = valid & (vdsat + tq <= vdsv)
    spd = np.ones_like(sat0) if rec["f_req"] is None else (ft >= rec["f_req"])
    cond = gm * loo >= ioff
    budget = BUDGET[rec["circuit"]]
    buds = [("none", None)] + ([("full", budget), ("share", budget / NSF[rec["circuit"]])] if budget else [])
    ratio = (np.broadcast_to(tq, sat0.shape[:3] + (1,))[..., 0] / np.broadcast_to(vdsv, sat0.shape[:3] + (1,))[..., 0])
    res = dict(circuit=rec["circuit"], dev=rec["dev"], kind=kind, cls=rec["cls"], f_req=rec["f_req"],
               tol_cell_mV=q(1e3 * np.broadcast_to(tq, sat0.shape[:3] + (1,))[..., 0]), tol_over_vds=q(ratio), combos={})
    for idc in IDS:
        minw = idn <= idc * W_REF / W_MIN
        for var in ("P2", "D2P"):
            extra = cond if var == "D2P" else np.ones_like(sat0)
            s0 = sat0 & spd & minw & extra; s1 = sat1 & spd & minw & extra
            removed = s0 & ~s1                                  # 띠 0 <= VDS - VDSAT < tol 안 노드
            n_set_removed = int(removed.any(-1).sum())
            ne0, ne1 = s0.any(-1), s1.any(-1)
            for rule in ("ga", "na"):
                att0 = first_true(s0) if rule == "ga" else np.where(ne0, np.argmax(np.where(s0, g, -np.inf), -1), -1)
                att1 = first_true(s1) if rule == "ga" else np.where(ne1, np.argmax(np.where(s1, g, -np.inf), -1), -1)
                for bname, B in buds:
                    def tstar(s, att, ne):
                        ok = s if B is None else s & (idn >= idc * Lb * W_REF / B)
                        if rule == "na":
                            ok = ok & (idx >= att[..., None])
                        return np.where(ne, first_true(ok), -1)
                    t0, t1 = tstar(s0, att0, ne0), tstar(s1, att1, ne1)
                    both = (t0 >= 0) & (t1 >= 0)
                    dl = (take(lnidu, t1) - take(lnidu, t0))[both]
                    dv = (VG[np.maximum(t1, 0)] - VG[np.maximum(t0, 0)])[both]
                    res["combos"][f"{var}|{rule}|ID{idc:g}|{bname}"] = dict(
                        n_cfg=int(ne0.size), sd_nonempty_noTol=int(ne0.sum()), sd_nonempty_Tol=int(ne1.sum()), sd_emptied=int((ne0 & ~ne1).sum()),
                        n_set_band_nodes=n_set_removed, n_band_nodes=int(removed.sum()),
                        ts_both=int(both.sum()), ts_differ=int((dl != 0).sum()), ts_lost=int(((t0 >= 0) & (t1 < 0)).sum()),
                        dlnidu=q(np.abs(dl[dl != 0])) if (dl != 0).any() else None, dvgs=q(np.abs(dv[dv != 0])) if (dv != 0).any() else None,
                        att_differ=int(((att0 >= 0) & (att1 >= 0) & (att0 != att1)).sum()))
    with open(OUT, "ab") as fh:
        fh.write((json.dumps(res) + "\n").encode("utf-8"))


t0 = time.time()
for n, rec in enumerate(SF):
    run_device(rec)
    print(n + 1, len(SF), rec["circuit"], rec["dev"], round(time.time() - t0, 1), flush=True)
(HERE / "q5_k10_lut_meta.json").write_bytes(json.dumps(dict(n_sf=len(SF), w_min_m=W_MIN, w_key=WK, budgets=BUDGET)).encode("utf-8"))
print("done", round(time.time() - t0, 1))
