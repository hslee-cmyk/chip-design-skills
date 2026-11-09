# ⚑ 별건 정량: LUT r2(위치 선언 파일 cap_npz 만)에서 gm/ID(VGS) 분지(정점 오른쪽)의 비단조 -- 해 둘 이상인 구간.
# 격자 원값(VGS 49점, 보간 없음)으로 잰다(보간 인공물 배제).
# shadowed(x): 분지 위 VGS 격자점 x 에서 g(x) <= max_{x'>x} g(x') -> 같은 gm/ID 의 더 큰 VGS 해가 있다
#   -> '가장 큰 VGS 해' 규칙(엔진 lut/vgs_root.py 머리 문언과 같은 꼴)으로는 x 에 도달할 수 없다.
# 진폭 = max_x (max_{x'>x} g(x') - g(x)) [S/A] 와 그 상대값(/g(x)).
# 결과: multiroot.jsonl (곡선마다 1줄 -- kind, L, VSB, VDS), multiroot_summary.json
import json, math, pathlib
import numpy as np

HERE = pathlib.Path(__file__).parent
LOC = json.loads(pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/lut_v2_location.json").read_text(encoding="utf-8"))
Z = np.load(pathlib.Path(LOC["root"]["default"]) / LOC["files"]["cap_npz"]["path"], allow_pickle=True)
LG, VG, VD, VS = Z["L"], Z["VGS"], Z["VDS"], Z["VS"]
OUT = HERE / "multiroot.jsonl"


def analyse_curve(g, vg):
    ok = np.isfinite(g) & (vg > 0)
    g, vg = g[ok], vg[ok]
    if len(g) < 3:
        return None
    p = int(np.argmax(g))
    gb, vb = g[p:], vg[p:]
    if len(gb) < 3:
        return None
    suffmax = np.maximum.accumulate(gb[::-1])[::-1]       # max_{x'>=x}
    nxt = np.append(suffmax[1:], -np.inf)                  # max_{x'>x}
    sh = nxt >= gb
    amp = nxt - gb
    i = int(np.argmax(amp))
    band = None
    if sh.any():
        js = np.where(sh)[0]
        band = dict(vgs=[float(vb[js[0]]), float(vb[js[-1]])], g=[float(gb[js].min()), float(nxt[js].max())])
    return dict(n_branch=int(len(gb)), n_shadowed=int(sh.sum()), amp=float(max(amp.max(), 0.0)),
                amp_rel=float(max(amp[i], 0.0) / gb[i]) if gb[i] > 0 else None, band=band,
                g_dom=[float(gb.min()), float(gb.max())], vgs_peak=float(vb[0]))


def main():
    if OUT.exists():
        OUT.unlink()
    summ = {}
    with open(OUT, "a", encoding="utf-8") as fh:
        for kind in ("n", "p"):
            ID, GM = Z["ID_" + kind], Z["GM_" + kind]
            g4 = GM / np.where(ID > 0, ID, np.nan)
            for li, L in enumerate(LG):
                for si, vs in enumerate(VS):
                    for di, vd in enumerate(VD):
                        r = analyse_curve(g4[li, :, di, si], VG)
                        if r is None:
                            continue
                        r.update(kind=kind, L=float(L), VSB=float(vs), VDS=float(vd), diode=False)
                        fh.write(json.dumps(r) + "\n")
                    # 다이오드 대각(VDS = VGS)
                    gd = np.array([g4[li, k, k, si] for k in range(len(VG))])
                    r = analyse_curve(gd, VG)
                    if r is not None:
                        r.update(kind=kind, L=float(L), VSB=float(vs), VDS=None, diode=True)
                        fh.write(json.dumps(r) + "\n")
    rows = [json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines()]
    for kind in ("n", "p"):
        for diode in (False, True):
            for sat_only in (False, True):
                rs = [r for r in rows if r["kind"] == kind and r["diode"] == diode and (diode or not sat_only or r["VDS"] >= 0.3)]
                if not rs:
                    continue
                nb = sum(r["n_branch"] for r in rs); ns = sum(r["n_shadowed"] for r in rs)
                nc = sum(r["n_shadowed"] > 0 for r in rs)
                amps = sorted(r["amp_rel"] or 0 for r in rs if r["n_shadowed"] > 0)
                perL = {}
                for r in rs:
                    k = f"{r['L']*1e6:.3g}"
                    a = perL.setdefault(k, [0, 0, 1e9, -1e9])
                    a[0] += r["n_branch"]; a[1] += r["n_shadowed"]
                    if r["band"]:
                        a[2] = min(a[2], r["band"]["g"][0]); a[3] = max(a[3], r["band"]["g"][1])
                key = f"{kind}{'_diode' if diode else ''}{'_vds>=0.3' if sat_only and not diode else ''}"
                summ[key] = dict(curves=len(rs), curves_nonmono=nc, branch_pts=nb, shadowed_pts=ns,
                                 shadowed_frac=ns / nb if nb else None,
                                 amp_rel_median=amps[len(amps) // 2] if amps else None, amp_rel_max=amps[-1] if amps else None,
                                 perL={k: dict(frac=v[1] / v[0], g_band=None if v[2] > 1e8 else [round(v[2], 2), round(v[3], 2)]) for k, v in perL.items()})
    (HERE / "multiroot_summary.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
