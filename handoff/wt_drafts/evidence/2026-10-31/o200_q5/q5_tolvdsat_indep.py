# O-200 Q5 측정 6·2 -- tol_VDsat 셀값을 계획 정의(P:635 '허용오차 식' + N3.6 표 7행: VDSAT 열 leave-one-out, 운영 보간과 같은 방법 = 선형,
# Richardson 2^p 나눔(선형 p = 2), 셀 = (kind, w_key, L 점, VDS), 셀 값 = 셀 안 최댓값, L 은 같은 PDK 모델 bin 안 내부 점만,
# 앵커 2개 bin 은 검증 중점 파일 오차(환산 없음)를 그 bin 의 L 방향 값으로)대로 LUT 원자료에서 직접 다시 계산하고, 엔진 함수 값과 대조한다.
# 엔진 함수는 비교 대상일 뿐 근거가 아니다(원칙 8). LUT = resolve_lut_location(sha256 대조). 읽기·실행만.
# 산출(케이스마다 Python append): q5_tolvdsat_indep.jsonl (슬라이스마다 1줄), q5_tolvdsat_top_pmos1000.jsonl (pmos 1000 상위 셀 원인).
import os, sys, json, pathlib, math
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
import numpy as np
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG))
HERE = pathlib.Path(__file__).parent
from gmid_engine.lut import resolve_lut_location
LOC = resolve_lut_location(str(ENG / "assets/lut_v2_location.json"), os.environ)   # sha256 대조(실패면 예외)
ROOT = pathlib.Path(LOC.manifest_path).parent
MAN = json.loads(pathlib.Path(LOC.manifest_path).read_text(encoding="utf-8"))
GRID = float(MAN.get("manufacturing_grid_m") or 5e-9)   # manifest 에 없으면 엔진 LutSpec 과 같은 기본(u13_real.real_env 와 같은 출처)
MID = np.load(LOC.midpoints_path, allow_pickle=True)
KIND = {"nfet_01v8": ("nmos", "_n"), "pfet_01v8": ("pmos", "_p")}
OUT = HERE / "q5_tolvdsat_indep.jsonl"; OUT.write_text("", encoding="utf-8")
TOP = HERE / "q5_tolvdsat_top_pmos1000.jsonl"; TOP.write_text("", encoding="utf-8")


def app(path, rec):
    with open(path, "ab") as fh:
        fh.write((json.dumps(rec, default=float) + "\n").encode("utf-8"))


def loo(values, on, grids, interior):
    """점별 [L,VGS,VDS,VS] (환산 값, 그 값을 낸 축 번호, 환산 전 값)."""
    best = np.full(values.shape, np.nan); src = np.full(values.shape, -1); raw_best = np.full(values.shape, np.nan)
    for ax in range(4):
        x = np.asarray(grids[ax], float)
        v = np.moveaxis(values, ax, 0); o = np.moveaxis(on, ax, 0)
        sh = (-1,) + (1,) * 3
        t = ((x[1:-1] - x[:-2]) / (x[2:] - x[:-2])).reshape(sh)
        est = v[:-2] + t * (v[2:] - v[:-2])
        ok = o[:-2] & o[1:-1] & o[2:]
        if ax == 0:
            ok = ok & np.asarray(interior[1:-1], bool).reshape(sh)
        raw = np.where(ok, np.abs(est - v[1:-1]), np.nan)
        sc = raw / 2.0 ** 2
        bv = np.moveaxis(best, ax, 0); sv = np.moveaxis(src, ax, 0); rv = np.moveaxis(raw_best, ax, 0)
        better = np.nan_to_num(sc, nan=-1) > np.nan_to_num(bv[1:-1], nan=-1)
        sv[1:-1] = np.where(better, ax, sv[1:-1])
        bv[1:-1] = np.fmax(bv[1:-1], sc)
        rv[1:-1] = np.fmax(rv[1:-1], raw)
    return best, src, raw_best


def cellmax(p):
    q = np.moveaxis(p, 2, 1).reshape(p.shape[0], p.shape[2], -1)   # [L, VDS, VGS*VS]
    has = ~np.isnan(q).all(-1)
    out = np.full(q.shape[:2], np.nan); out[has] = np.nanmax(q[has], -1)
    return out


import importlib
R = importlib.import_module("gmid_engine.tests.search.u13_real")
from gmid_engine.lut import tol_vdsat_table
env = R.real_env()

for e in MAN["slices"]:
    kind, suf = KIND[e["device"]]
    z = np.load(ROOT / e["file"], allow_pickle=True)
    meta = json.loads(str(z["meta_json"]))
    W = float(z["W"]); wk = int(round(W / GRID))
    L, VG, VD, VS = (np.asarray(z[k], float) for k in ("L", "VGS", "VDS", "VS"))
    V = np.asarray(z["VDSAT"], float); on = (np.asarray(z["ID"]) > 0) & (np.asarray(z["GM"]) > 0)
    bins = [meta["model_bin_per_L"][("%g" % (l * 1e6))] for l in L]          # PDK 모델 bin(ngspice showmod, 생성기 메타)
    n = len(L)
    interior = [0 < i < n - 1 and bins[i - 1] == bins[i] == bins[i + 1] for i in range(n)]
    best, src, raw = loo(V, on, (L, VG, VD, VS), interior)
    cell = cellmax(best); cell_raw = cellmax(raw)
    # 앵커 2개 bin: 검증 중점(같은 폭일 때만) -- L 방향 값, 환산 없음
    ext = {}            # anchor index -> per-VDS array
    ext_info = []
    w_mid = float(MID["w_ref_m"])
    groups = {}
    for i, b in enumerate(bins):
        groups.setdefault(b, []).append(i)
    if abs(w_mid - W) <= GRID / 2:
        Lm = np.asarray(MID["L"], float)
        Vm = np.asarray(MID["VDSAT" + suf], float); onm = (np.asarray(MID["ID" + suf]) > 0) & (np.asarray(MID["GM" + suf]) > 0)
        assert np.allclose(MID["VGS"], VG) and np.allclose(MID["VDS"], VD) and np.allclose(MID["VS"], VS)
        for m, lm in enumerate(Lm):
            for b, idx in groups.items():
                if len(idx) == 2 and L[idx[0]] < lm < L[idx[1]]:
                    i0, i1 = idx
                    t = (lm - L[i0]) / (L[i1] - L[i0])
                    err = np.abs(V[i0] + t * (V[i1] - V[i0]) - Vm[m])
                    ok = onm[m] & on[i0] & on[i1]
                    er = np.where(ok, err, np.nan)                       # [VGS,VDS,VS]
                    pv = np.array([np.nanmax(er[:, k, :]) if np.isfinite(er[:, k, :]).any() else np.nan for k in range(len(VD))])
                    for i in idx:
                        ext[i] = np.fmax(ext.get(i, np.full(len(VD), np.nan)), pv)
                    a = np.nanargmax(np.where(np.isfinite(er), er, -1))
                    gi, ki, si = np.unravel_index(a, er.shape)
                    ext_info.append(dict(L_mid_um=lm * 1e6, bin=b, anchors_um=[L[i0] * 1e6, L[i1] * 1e6], max_mV=float(er[gi, ki, si]) * 1e3,
                                         at_VGS=float(VG[gi]), at_VDS=float(VD[ki]), at_VS=float(VS[si]),
                                         vdsat_a0=float(V[i0, gi, ki, si]), vdsat_a1=float(V[i1, gi, ki, si]), vdsat_mid=float(Vm[m, gi, ki, si])))
    cell_I = cell.copy()                      # 변형 I: 외부 값을 그 bin 두 앵커 셀에 max 로 넣음
    for i, pv in ext.items():
        cell_I[i] = np.where(np.isnan(cell[i]), np.nan, np.fmax(cell[i], pv))
    # 엔진 표
    tb = tol_vdsat_table(env.memo, kind, wk)
    eng = np.array([[np.nan if c.vdsat_v is None else c.vdsat_v for c in row] for row in tb.cells], float)
    eng_raw = np.array([[np.nan if c.vdsat_loo_v is None else c.vdsat_loo_v for c in row] for row in tb.cells], float)
    def cmp(a, b):
        both = np.isfinite(a) & np.isfinite(b)
        return dict(n_both=int(both.sum()), n_only_indep=int((np.isfinite(a) & ~np.isfinite(b)).sum()), n_only_eng=int((~np.isfinite(a) & np.isfinite(b)).sum()),
                    max_abs_diff_V=float(np.abs(a - b)[both].max()) if both.any() else None, n_diff_gt_1e12=int((np.abs(a - b)[both] > 1e-12).sum()))
    rec = dict(kind=kind, w_key=wk, W_um=W * 1e6, bins=bins, interior=interior, ext_anchor_idx=sorted(ext),
               cmp_noext=cmp(cell, eng), cmp_extI=cmp(cell_I, eng), cmp_raw=cmp(cell_raw, eng_raw), ext_info=ext_info,
               q_mV_extI=[float(np.nanquantile(cell_I, p)) * 1e3 for p in (0, .1, .5, .9, 1)],
               argmax_extI=[float(L[np.unravel_index(np.nanargmax(cell_I), cell_I.shape)[0]]), float(VD[np.unravel_index(np.nanargmax(cell_I), cell_I.shape)[1]])],
               q_mV_noext=[float(np.nanquantile(cell, p)) * 1e3 for p in (0, .1, .5, .9, 1)])
    app(OUT, rec)
    print(kind, wk, rec["cmp_noext"], rec["cmp_extI"], rec["q_mV_extI"][-1], flush=True)
    if kind == "pmos" and wk == 1000:
        order = np.argsort(np.nan_to_num(cell_I, nan=-1).ravel())[::-1][:25]
        for f in order:
            i, k = np.unravel_index(f, cell_I.shape)
            c_in = cell[i, k]; c_ex = ext.get(i, np.full(len(VD), np.nan))[k] if i in ext else None
            # 내부 LOO 최댓값 점
            sl = best[i, :, k, :]
            if np.isfinite(sl).any():
                g, s = np.unravel_index(np.nanargmax(np.where(np.isfinite(sl), sl, -1)), sl.shape)
                ax = int(src[i, g, k, s])
                inner = dict(val_mV=float(sl[g, s]) * 1e3, axis=["L", "VGS", "VDS", "VS"][ax], VGS=float(VG[g]), VS=float(VS[s]),
                             vdsat_here=float(V[i, g, k, s]), ID_here=float(z["ID"][i, g, k, s]))
            else:
                inner = None
            app(TOP, dict(rank=int(len(open(TOP, encoding="utf-8").read().splitlines())), L_um=float(L[i] * 1e6), VDS=float(VD[k]), cell_mV=float(cell_I[i, k]) * 1e3,
                          eng_mV=float(eng[i, k]) * 1e3, inner_loo=inner, ext_mV=None if c_ex is None or not np.isfinite(c_ex) else float(c_ex) * 1e3, bin=bins[i]))
print("done")
