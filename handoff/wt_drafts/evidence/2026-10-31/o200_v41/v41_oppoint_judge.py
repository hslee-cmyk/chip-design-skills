# 검증 41 (b) 보조 -- 기존 동작점 기록(evidence/2026-10-22/b74_oppoint_gap/out: 3회로 36소자, 엔진 dc_op 점 + SPICE op 점)에서
# 옛 봉인 9 식(I_off <= (gm/ID) tol_V ID) 대 P4(ID > I_off) 판정이 갈리는 소자 수. 읽기만.
# ln(ID/I_off) = ln ID(VGS) - ln ID(0) 를 같은 (L, VDS, VSB) LUT 곡선에서 잰다(W 상쇄). L = 가장 가까운 LUT L 점, VDS·VSB·VGS 는 ln ID 다중선형 보간.
# tol_V = 기록의 dc_tol_v(그 점 엔진 셀값) 그대로, gm/ID = 기록값(엔진 점) / SPICE 점은 엔진 gm/ID 를 씀(SPICE gm 기록 없음 -- 표지).
import json, os, sys, pathlib
import numpy as np
sys.dont_write_bytecode = True
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG))
from gmid_engine.lut.data_location import resolve_lut_location  # noqa: E402
LOC = resolve_lut_location(str(ENG / "assets/lut_v2_location.json"), os.environ)
Z = np.load(LOC.cap_npz_path, allow_pickle=True)
LG, VG, VD, VS = Z["L"], Z["VGS"], Z["VDS"], Z["VS"]
B74 = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-22/b74_oppoint_gap/out")
rows = json.loads((B74 / "summary_rows.json").read_text(encoding="utf-8"))
engq = json.loads((B74 / "engq.json").read_text(encoding="utf-8"))
OUT = pathlib.Path(__file__).parent / "v41_oppoint_judge.txt"
OUT.write_text("", encoding="utf-8")


def P(s):
    print(s)
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


def kind_of(circ, dev):
    topo = json.loads((ENG / f"assets/library/{circ}.topology.json").read_text(encoding="utf-8"))
    for d in topo["netlist"]:
        if d.get("name") == dev:
            return {"nmos": "n", "pmos": "p"}.get(d.get("kind"))
    return None


def lnid(k, li, vgs, vds, vsb):
    A = np.log(np.maximum(Z["ID_" + k][li], 1e-300))   # (VGS, VDS, VS)
    def ip(ax, x):
        i = int(np.clip(np.searchsorted(ax, x) - 1, 0, len(ax) - 2)); t = (x - ax[i]) / (ax[i + 1] - ax[i]); return i, float(np.clip(t, 0, 1))
    (i, a), (j, b), (m, c) = ip(VG, vgs), ip(VD, vds), ip(VS, vsb)
    v = 0.0
    for di_, wa in ((0, 1 - a), (1, a)):
        for dj, wb in ((0, 1 - b), (1, b)):
            for dm, wc in ((0, 1 - c), (1, c)):
                v += wa * wb * wc * A[i + di_, j + dj, m + dm]
    return v


n_dev = n_diff_e = n_diff_s = 0
P("circuit dev kind L_um | 엔진점 VGS ln(ID/Ioff) eps=(gm/ID)tol ln(1/eps) 옛 P4 | SPICE점 VGS ln(ID/Ioff) 옛 P4")
for circ, rs in rows.items():
    for r in rs:
        e = engq[circ][r["device"]]
        L = e["idu_fwd_engine_query"] * e["w_m"] / e["ID_slice_A"]
        li = int(np.argmin(np.abs(LG - L)))
        k = kind_of(circ, r["device"]) or "?"
        if k == "?":
            P(f"{circ} {r['device']} kind 미상 -- 건너뜀 아님: 표지"); continue
        g, tol = r["gm_id_eng"], r["dc_tol_v"]
        eps = g * tol
        out = []
        for vgs, vds in ((r["vgs"], r["vds"]), (r.get("circ.vgs"), r.get("circ.vds"))):
            if vgs is None:
                out.append(None); continue
            lr = lnid(k, li, abs(vgs), abs(vds), max(r["vsb"], 0.0)) - lnid(k, li, 0.0, abs(vds), max(r["vsb"], 0.0))
            old = np.exp(-lr) <= eps
            p4 = lr > 0
            out.append((abs(vgs), lr, old, p4))
        n_dev += 1
        n_diff_e += int(out[0][2] != out[0][3])
        if out[1]:
            n_diff_s += int(out[1][2] != out[1][3])
        s = out[1]
        P(f"{circ} {r['device']} {k} {L*1e6:.3f} | {out[0][0]:.3f} {out[0][1]:.2f} {eps:.3f} {-np.log(eps):.2f} {out[0][2]} {out[0][3]} | "
          + (f"{s[0]:.3f} {s[1]:.2f} {s[2]} {s[3]}" if s else "없음"))
P(f"소자 {n_dev}: 엔진점 판정 갈림 {n_diff_e}, SPICE점 판정 갈림 {n_diff_s}")
