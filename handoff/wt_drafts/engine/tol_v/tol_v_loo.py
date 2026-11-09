# -*- coding: utf-8 -*-
"""tol_V 실측: (kind, L 앵커, VDS)별 LUT leave-one-out 보간 오차(VGS 기준)의 최댓값.

계획 N3.6 -- "tol_V = (kind, L 앵커, VDS)별 LUT leave-one-out 보간 오차(VGS 기준)의 최댓값.
계산 방법은 probe_interp_scheme_loo.py".

방법(옛 probe 재현 + VGS 기준으로 확장):
  * 옛 probe(legacy/tests/probes/probe_interp_scheme_loo.py)와 같은 leave-one-out:
    L 앵커 iL 하나(양끝 제외 -- 양끝은 보간이 아니라 외삽)를 뺀 LUT를 옛 엔진의
    `SemiEmpiricalGmIdLUT`로 만들고, 그 앵커의 실측 스윕값과 대조한다. ON_MIN_ID=1e-12 A
    (켜진 구간만)도 probe 값 그대로.
  * 옛 probe는 gm/ID 상대오차(%)를 쟀다. 계획은 VGS 기준이므로 대조 대상을
    `vgs_for_gm_id()`(= `_solve_vgs`, rightmost root) 출력으로 바꾼다:
        target g_j = 실측 gm/ID(VGS_j)  (held-out 앵커, ID_j > ON_MIN_ID)
        truth     = full_lut.vgs_for_gm_id(g_j, L_iL, vds, vs)  (앵커 위라 보간 가중 0 -- 실측 곡선의 rightmost root)
        estimate  = loo_lut.vgs_for_gm_id(g_j, L_iL, vds, vs)
        err_vgs   = |estimate - truth|   [V]
    역산 실패(ValueError: 목표가 LOO 곡선 범위 밖)는 오차값이 아니라 실패 개수로 센다.
  * 보조 지표 err_id_eq: 같은 VGS_j에서 ln ID 보간 오차를 VGS로 환산
        |ln ID_loo(VGS_j) - ln ID_true(VGS_j)| / (gm/ID)_true   [V]
    (KCL tol_I = tol_V x gm 쪽 해석용.)
  * 범위: VDS 격자 전체 x VS 격자 전체(probe는 VDS 3점 x VS 2점). 셀 (kind,L,VDS) 값 = VS와
    목표 전체에 대한 최댓값.

일반화: --npz 여러 개 / --slices-dir(그 안의 *.npz 전부). 키는 L,VGS,VDS,VS + ID_<k>,GM_<k>,
GDS_<k>,CGG_<k> (k = n|p, 있는 것만). W_ref는 VGS 역산에 영향이 없다(ID/W 스케일은 gm/ID 비와
ln ID 차에서 상쇄) -- npz에 'W_ref' 키가 있으면 쓰고 없으면 None.

실행: python tol_v_loo.py [--npz A.npz ...] [--slices-dir DIR] [--out DIR]
결과는 줄마다 append(중간에 죽어도 남는다).
"""
import argparse
import csv
import glob
import json
import os
import re
import sys
import time

sys.dont_write_bytecode = True  # 읽기 전용 저장소에 __pycache__를 만들지 않는다
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
LEGACY = os.path.join(REPO, "skills/analog-gmid-design/legacy")
DEFAULT_NPZ = os.path.join(REPO, "skills/analog-gmid-design/assets/sky130_nfet_pfet_lut_sample.npz")
DEFAULT_TLEF = r"C:/pdk/sky130_fd_sc_hd/tech/sky130_fd_sc_hd.tlef"
ON_MIN_ID = 1e-12  # 옛 probe와 같은 값(켜진 구간 판정)

sys.path.insert(0, LEGACY)
import sizing_recipe as sr  # noqa: E402  (옛 엔진, 읽기만)


class Emitter:
    def __init__(self, path):
        self.path = path
        open(path, "w", encoding="utf-8").close()

    def __call__(self, *parts):
        line = " ".join(str(p) for p in parts)
        print(line, flush=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def parse_mfg_grid(tlef):
    """tlef의 MANUFACTURINGGRID(um)를 읽는다."""
    with open(tlef, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.match(r"\s*MANUFACTURINGGRID\s+([0-9.eE+-]+)\s*;", line)
            if m:
                return float(m.group(1))
    raise ValueError("MANUFACTURINGGRID not found in " + tlef)


def load_arrays(npz_path, d):
    """kind -> {ID,GM,GDS,CGG} 배열. 두 형식을 받는다.
    (a) 기준 LUT: ID_n/GM_n/.../ID_p/... (한 파일에 두 kind)
    (b) 폭별 슬라이스(lut_slices/sky130_dc_width_slices.py): ID/GM/GDS(접미사 없음, 한 파일 한 소자),
        소자는 meta_json의 device 또는 파일명(nfet/pfet)으로 판정. CGG가 없으면 0 배열
        (CGG는 VGS 역산에 쓰이지 않는다 -- 생성자 인자 자리만 채움)."""
    out = {}
    for k in ("n", "p"):
        if all((a + "_" + k) in d.files for a in ("ID", "GM", "GDS")):
            out[k] = {a: d[a + "_" + k] for a in ("ID", "GM", "GDS")}
            out[k]["CGG"] = d["CGG_" + k] if ("CGG_" + k) in d.files else np.zeros_like(d["ID_" + k])
    if not out and all(a in d.files for a in ("ID", "GM", "GDS")):
        dev = ""
        if "meta_json" in d.files:
            dev = json.loads(str(d["meta_json"])).get("device", "")
        dev = (dev or os.path.basename(npz_path)).lower()
        k = "p" if "pfet" in dev else ("n" if "nfet" in dev else None)
        if k is None:
            raise ValueError("소자 종류(nfet/pfet)를 판정할 수 없음: " + npz_path)
        out[k] = {a: d[a] for a in ("ID", "GM", "GDS")}
        out[k]["CGG"] = d["CGG"] if "CGG" in d.files else np.zeros_like(d["ID"])
    return out


def w_ref_of(d):
    for key in ("W_ref", "W"):
        if key in d.files:
            return float(d[key])
    return None


def build(d, arrs, k, keep):
    sel = np.array(sorted(keep))
    a = arrs[k]
    return sr.SemiEmpiricalGmIdLUT(
        d["L"][sel], d["VGS"], d["VDS"], d["VS"],
        a["ID"][sel], a["GM"][sel], a["GDS"][sel], a["CGG"][sel],
        W_ref=w_ref_of(d))


def measure(npz_path, emit, out_dir):
    d = np.load(npz_path)
    tag = os.path.splitext(os.path.basename(npz_path))[0]
    L_all = [float(x) for x in d["L"]]
    vgs = d["VGS"].astype(float)
    vds_g = d["VDS"].astype(float)
    vs_g = d["VS"].astype(float)
    emit("== LUT:", npz_path)
    emit("L(um):", [round(x * 1e6, 4) for x in L_all], " VGS n=%d VDS n=%d VS=%s"
         % (len(vgs), len(vds_g), vs_g.tolist()))
    if len(L_all) < 3:
        emit("  L 앵커 < 3 -- 내부 앵커가 없어 leave-one-out 불가. 건너뜀.")
        return None
    rows_full = []      # (kind,L,VDS,VS) 셀
    targets = []        # 목표별 원자료
    t0 = time.time()
    arrs = load_arrays(npz_path, d)
    emit("kind:", sorted(arrs), " W_ref:", w_ref_of(d))
    for k in sorted(arrs):
        kind = "nmos" if k == "n" else "pmos"
        full = build(d, arrs, k, range(len(L_all)))
        for iL in range(1, len(L_all) - 1):
            loo = build(d, arrs, k, [i for i in range(len(L_all)) if i != iL])
            L = L_all[iL]
            for iV, vds in enumerate(vds_g):
                vds = float(vds)
                for iS, vs in enumerate(vs_g):
                    vs = float(vs)
                    idt = arrs[k]["ID"][iL, :, iV, iS].astype(float)
                    gmt = arrs[k]["GM"][iL, :, iV, iS].astype(float)
                    on = (idt > ON_MIN_ID) & (gmt > 0)
                    n_on = int(on.sum())
                    if n_on == 0:
                        continue
                    id_loo, _ = loo._gm_id_curve(L, vds, vs)
                    ev, ei, nf = [], [], 0
                    with np.errstate(divide="ignore", invalid="ignore"):
                        gall = np.where(on, gmt / np.where(idt > 0, idt, 1.0), -np.inf)
                    for j in np.flatnonzero(on):
                        g = gmt[j] / idt[j]
                        # 실측 곡선에서 VGS_j가 rightmost root인가(오른쪽 모든 점의 gm/ID < g_j).
                        # 이 조건이면 truth = VGS_j(정확), 엔진이 고르는 분지 위의 목표다.
                        branch = 1.0 if (j == len(gall) - 1 or g > gall[j + 1:].max()) else 0.0
                        e_id = abs(np.log(max(id_loo[j], 1e-300)) - np.log(idt[j])) / g
                        ei.append(e_id)
                        try:
                            tr = full.vgs_for_gm_id(g, L, vds, vs)
                        except ValueError:
                            tr = float("nan")
                        try:
                            es = loo.vgs_for_gm_id(g, L, vds, vs)
                        except ValueError:
                            es = float("nan")
                        if np.isnan(es) or np.isnan(tr):
                            nf += 1
                            e = float("nan")
                        else:
                            e = abs(es - tr)
                            ev.append(e)
                        eb = abs(es - float(vgs[j])) if (branch and not np.isnan(es)) else float("nan")
                        targets.append((k, iL, iV, iS, float(vgs[j]), g, tr, es, e, e_id, branch, eb))
                    rows_full.append(dict(
                        kind=kind, L_um=L * 1e6, VDS=vds, VS=vs, n_on=n_on, n_fail=nf,
                        max_err_vgs=(max(ev) if ev else float("nan")),
                        med_err_vgs=(float(np.median(ev)) if ev else float("nan")),
                        max_err_id_eq=max(ei)))
            emit("  %s L=%.4fum done (%.1fs)" % (kind, L * 1e6, time.time() - t0))
    # 저장
    with open(os.path.join(out_dir, tag + ".cells_kind_L_VDS_VS.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_full[0].keys()))
        w.writeheader()
        w.writerows(rows_full)
    tg = np.array([(0 if t[0] == "n" else 1,) + t[1:] for t in targets], dtype=float)
    np.savez_compressed(os.path.join(out_dir, tag + ".targets.npz"), targets=tg,
                        columns=np.array(["kind(0n,1p)", "iL", "iVDS", "iVS", "VGS_j", "gm_id_target",
                                          "vgs_truth", "vgs_loo", "err_vgs", "err_id_eq",
                                          "on_rightmost_branch", "err_vgs_branch"]),
                        L=d["L"], VDS=vds_g, VS=vs_g)
    return dict(tag=tag, rows=rows_full, tg=tg, L=L_all, VDS=vds_g, VS=vs_g)


def summarize(res, emit, out_dir, mfg_um, col=8, label="raw"):
    tag = res["tag"]
    tg = res["tg"]
    L_all, vds_g = res["L"], res["VDS"]
    err = tg[:, col]
    ok = ~np.isnan(err)
    tg = tg.copy()
    tg[:, 8] = err  # 이하 코드는 8열을 측정 지표로 읽는다
    tag = tag + "." + label
    emit()
    emit("##### 지표 = %s #####" % label)
    emit("=== [%s] 목표 수 %d, 지표 유효 %d, 무효(역산 실패/분지 밖) %d (%.2f%%) ==="
         % (tag, len(tg), ok.sum(), (~ok).sum(), 100 * (~ok).mean()))
    # (kind,L,VDS) 셀 = VS와 목표 전체 최댓값
    cells = {}
    for t in tg[ok]:
        key = (int(t[0]), int(t[1]), int(t[2]))
        if t[8] > cells.get(key, (-1,))[0]:
            cells[key] = (t[8], t[3], t[5], t[4])
    with open(os.path.join(out_dir, tag + ".tolV_kind_L_VDS.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kind", "L_um", "VDS", "tol_V_mV", "argmax_VS", "argmax_gm_id", "argmax_VGS_j"])
        for (kk, iL, iV), (e, iS, g, vj) in sorted(cells.items()):
            w.writerow(["nmos" if kk == 0 else "pmos", round(L_all[iL] * 1e6, 4), round(float(vds_g[iV]), 4),
                        round(e * 1e3, 4), float(res["VS"][int(iS)]), round(g, 3), vj])
    cv = np.array([v[0] for v in cells.values()])
    gmax = float(np.nanmax(err))
    imax = int(np.nanargmax(err))
    tmax = tg[imax]
    emit("tol_V 전체 최댓값 = %.2f mV  (kind=%s, L=%.4fum, VDS=%.4f, VS=%.2f, gm/ID=%.2f, VGS_j=%.4f, truth=%.4f, loo=%.4f)"
         % (gmax * 1e3, "nmos" if tmax[0] == 0 else "pmos", L_all[int(tmax[1])] * 1e6, vds_g[int(tmax[2])],
            res["VS"][int(tmax[3])], tmax[5], tmax[4], tmax[6], tmax[7]))
    emit("err_id_eq(보조) 전체 최댓값 = %.2f mV" % (np.nanmax(tg[:, 9]) * 1e3))
    emit()
    emit("-- 셀 (kind,L,VDS) 최댓값 분포 [mV] (셀 수 %d) --" % len(cv))
    q = [0, 10, 25, 50, 75, 90, 95, 99, 100]
    emit("백분위 " + "  ".join("p%d=%.2f" % (p, np.percentile(cv, p) * 1e3) for p in q))
    emit()
    emit("-- kind x L 앵커: VDS 셀 최댓값의 [최소 / 중앙 / 최대] mV, 그리고 최대인 VDS --")
    emit("%-5s %-7s | %-8s %-8s %-8s | %-8s" % ("kind", "L(um)", "min", "median", "max", "VDS@max"))
    per_kl = {}
    for (kk, iL, iV), v in cells.items():
        per_kl.setdefault((kk, iL), []).append((v[0], float(vds_g[iV])))
    for (kk, iL) in sorted(per_kl):
        a = np.array([x[0] for x in per_kl[(kk, iL)]])
        vm = max(per_kl[(kk, iL)])[1]
        emit("%-5s %-7.4f | %-8.2f %-8.2f %-8.2f | %-8.4f" % ("nmos" if kk == 0 else "pmos", L_all[iL] * 1e6,
             a.min() * 1e3, np.median(a) * 1e3, a.max() * 1e3, vm))
    emit()
    emit("-- kind x VDS 구간: L 셀 최댓값 [mV] --")
    vbins = [(0.0, 0.15), (0.15, 0.3), (0.3, 0.6), (0.6, 1.2), (1.2, 1.81)]
    emit("%-5s " % "kind" + " ".join("%-14s" % ("VDS[%.2f,%.2f)" % b) for b in vbins))
    for kk in sorted(set(int(x) for x in tg[:, 0])):
        line = "%-5s " % ("nmos" if kk == 0 else "pmos")
        for lo, hi in vbins:
            a = [v[0] for (k2, iL, iV), v in cells.items() if k2 == kk and lo <= vds_g[iV] < hi]
            line += "%-14s " % ("%.2f" % (max(a) * 1e3) if a else "-")
        emit(line)
    emit()
    emit("-- gm/ID 구간별 err_vgs [mV]: 중앙 / p99 / 최대 (목표 단위) --")
    gb = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, 1e9)]
    for kk in sorted(set(int(x) for x in tg[:, 0])):
        for lo, hi in gb:
            m = ok & (tg[:, 0] == kk) & (tg[:, 5] >= lo) & (tg[:, 5] < hi)
            if m.sum() == 0:
                continue
            a = tg[m, 8]
            emit("%-5s gm/ID[%g,%s) n=%-6d med=%.3f p99=%.2f max=%.2f   (err_id_eq max=%.2f)"
                 % ("nmos" if kk == 0 else "pmos", lo, ("inf" if hi > 1e8 else "%g" % hi), m.sum(),
                    np.median(a) * 1e3, np.percentile(a, 99) * 1e3, a.max() * 1e3, tg[m, 9].max() * 1e3))
    # W 허용오차
    emit()
    emit("=== W 허용오차: 상한 tol_V x gm/ID  vs  하한 MANUFACTURINGGRID/(2 finger_w), MFG=%.4g um ===" % mfg_um)
    def kmax(kk):
        a = tg[(tg[:, 0] == kk) & ~np.isnan(tg[:, 8]), 8]
        return float(a.max()) if a.size else float("nan")
    tolsets = [("전체 최댓값", gmax)]
    tolsets += [(nm + " 최댓값", kmax(kk)) for kk, nm in ((0, "nmos"), (1, "pmos")) if not np.isnan(kmax(kk))]
    tolsets += [("셀 중앙값", float(np.median(cv))), ("셀 최솟값", float(cv.min()))]
    gm_ids = [2, 4, 6, 8, 10, 12, 15, 18, 20, 22, 25, 28]
    emit("finger_w_crit = MFG/(2 * tol_V * gm/ID): finger_w < crit 이면 하한 > 상한(격자 반올림만으로 위반)")
    emit("%-12s %-9s | " % ("tol_V 출처", "tol_V(mV)") + " ".join("%-12s" % ("gm/ID=%g" % g) for g in gm_ids))
    wrows = []
    for name, tv in tolsets:
        cells_s = []
        for g in gm_ids:
            up = tv * g
            crit = mfg_um / (2 * up)
            cells_s.append("%5.1f%%/%-.4g" % (up * 100, crit))
            wrows.append(dict(tol_src=name, tol_V_mV=tv * 1e3, gm_id=g, W_rel_upper=up, finger_w_crit_um=crit))
        emit("%-12s %-9.3f | " % (name, tv * 1e3) + " ".join("%-12s" % c for c in cells_s))
    emit("(칸 = 상한 상대오차% / finger_w_crit[um])")
    with open(os.path.join(out_dir, tag + ".W_tolerance.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(wrows[0].keys()))
        w.writeheader()
        w.writerows(wrows)
    summ = dict(metric=label, tag=tag, n_targets=int(len(tg)), n_fail=int((~ok).sum()), tol_V_max_mV=gmax * 1e3,
                tol_V_max_n_mV=kmax(0) * 1e3, tol_V_max_p_mV=kmax(1) * 1e3,
                cell_percentiles_mV={("p%d" % p): float(np.percentile(cv, p) * 1e3) for p in q},
                err_id_eq_max_mV=float(np.nanmax(tg[:, 9]) * 1e3), mfg_grid_um=mfg_um)
    with open(os.path.join(out_dir, tag + ".summary.json"), "w", encoding="utf-8") as f:
        json.dump(summ, f, ensure_ascii=False, indent=1)
    return summ


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", nargs="*", default=None)
    ap.add_argument("--slices-dir", default=None)
    ap.add_argument("--tlef", default=DEFAULT_TLEF)
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    a = ap.parse_args()
    paths = list(a.npz or [])
    if a.slices_dir:
        paths += sorted(glob.glob(os.path.join(a.slices_dir, "*.npz")))
    if not paths:
        paths = [DEFAULT_NPZ]
    os.makedirs(a.out, exist_ok=True)
    emit = Emitter(os.path.join(a.out, "tol_v_loo.result.txt"))
    mfg = parse_mfg_grid(a.tlef)
    emit("MANUFACTURINGGRID(%s) = %g um" % (a.tlef, mfg))
    allsum = []
    for p in paths:
        res = measure(p, emit, a.out)
        if res is not None:
            for col, label in ((8, "raw_vgs_for_gm_id"), (11, "branch_vgs_for_gm_id"), (9, "id_equiv")):
                allsum.append(summarize(res, emit, a.out, mfg, col, label))
    with open(os.path.join(a.out, "all_summaries.json"), "w", encoding="utf-8") as f:
        json.dump(allsum, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
