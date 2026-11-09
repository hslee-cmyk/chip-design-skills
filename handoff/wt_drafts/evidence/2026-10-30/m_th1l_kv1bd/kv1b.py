# M-KV1b: current_reuse 다이오드 고리에서 두 종속 선택(dep=rail / dep=stacked)의 손계산 front 차이.
# 손계산 = LUT r2(kv1_tiebreak 와 같은 곡면, ln IDu θ). SPICE 없음.
# θ(고리마다 2차원): (u_out = 배터리 소자 IDu -- P: M9a, N: M9b, u_ind = 독립 다이오드 IDu). 나머지 θ 는 kv1 rep 고정(u15, u16, 다른 고리 소자).
# 목적: A = Σ W·L(배터리 소자 + 두 다이오드) 최소, H = 바이어스 소자 헤드룸 노드 최대(P: V(N11b) = vdd − T_p, N: vdd − V(N14a14b) = vdd − T_n).
# 가능: 모든 역산이 LUT 정의역 안, 배터리 소자 포화(VDS ≥ VDSAT), H > 0, 종속 다이오드가 분지 안(close_loop ok).
# 상자: full = 각 좌표 LUT ln IDu 정의역(배터리: rep 의 VDS·VSB 곡선, 다이오드: VSB = 0 다이오드 곡선) / narrow = rep 값 ×{1/4, 4}(측정 표본 상자 -- 규칙 아님, kv1 OUTERS 와 같은 배율)
#       sym = narrow + 종속 다이오드 IDu 도 같은 구간 안(고리 멤버 모두에 상자 -- (바) 안).  같은 예산: 좌표마다 로그 격자 N_GRID 점.
# 비교: 각 (고리, 상자) 에서 두 선택 front 의 hypervolume(공통 기준점) 차, 서로의 front 를 지배하는 점 수.
import json, math, pathlib, sys
import numpy as np
sys.path.insert(0, r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-30/m_kv1_name_tiebreak")
import kv1_tiebreak as K
import run_kv1 as R

HERE = pathlib.Path(__file__).parent
OUT = HERE / "kv1b.jsonl"
N_GRID = 30


def lnidu_domain(kind, L, vds, vsb, diode):
    v, g, lid = K.branch(kind, L, vds, vsb, diode)
    return float(math.exp(lid[0]) / K.WREF), float(math.exp(lid[-1]) / K.WREF)


def front(points):
    pts = sorted(points, key=lambda p: (p[0], -p[1]))
    f, best = [], -1e9
    for a, h in pts:
        if h > best:
            f.append((a, h)); best = h
    return f


def hv(f, ref):
    # 최소 A, 최대 H; ref = (A_ref, H_ref) -- A_ref 이상·H_ref 이하는 0
    s, prev_h = 0.0, ref[1]
    for a, h in sorted(f, key=lambda p: p[1]):
        if a < ref[0] and h > prev_h:
            pass
    # 직사각형 합: H 오름차순으로 계단
    pts = sorted([p for p in f if p[0] < ref[0] and p[1] > ref[1]], key=lambda p: p[0])
    s = 0.0
    for i, (a, h) in enumerate(pts):
        a_next = pts[i + 1][0] if i + 1 < len(pts) else ref[0]
        s += (a_next - a) * (h - ref[1])
    return s


def run_loop(loop):
    th = R.th_of(1.0)
    o_rep = K.outer(th)
    if loop == "P":
        kind, Ld, I_d, Lb, Ib, key = "p", th["Ld"], th["I11"], th["L9a"], th["I9a"], "u9a"
        bvds, bvsb = o_rep["vbat"], o_rep["vsg15"]
        Uind = R.U_ORIG["P"]
    else:
        kind, Ld, I_d, Lb, Ib, key = "n", th["Ld"], th["I14"], th["L9b"], th["I9b"], "u9b"
        bvds, bvsb = o_rep["vbat"], o_rep["vop1"]
        Uind = R.U_ORIG["N"]
    bkind = "p" if loop == "P" else "n"
    boxes = {
        "full": (lnidu_domain(bkind, Lb, bvds, bvsb, False), lnidu_domain(kind, Ld, None, 0.0, True)),
        "narrow": ((th[key] / 4, th[key] * 4), (Uind / 4, Uind * 4)),
    }
    boxes["sym"] = boxes["narrow"]
    res = {}
    for bname, (bx_out, bx_ind) in boxes.items():
        uo = np.exp(np.linspace(math.log(bx_out[0]), math.log(bx_out[1]), N_GRID))
        ui = np.exp(np.linspace(math.log(bx_ind[0]), math.log(bx_ind[1]), N_GRID))
        pts = {"rail": [], "stacked": []}
        for u_o in uo:
            t2 = dict(th); t2[key] = float(u_o)
            try:
                o = K.outer(t2)
            except Exception:
                continue
            if None in (o["vsg9a"], o["vgs9b"]):
                continue
            T = o["Tp"] if loop == "P" else o["Tn"]
            vb = o["vsg9a"] if loop == "P" else o["vgs9b"]
            vsb_b = o["vsg15"] if loop == "P" else o["vop1"]
            if o["vbat"] < K.vdsat(bkind, Lb, vb, o["vbat"], vsb_b):
                continue
            H = K.VDD - T
            if H <= 0:
                continue
            Wb = Ib / K.idu(bkind, Lb, vb, o["vbat"], vsb_b)
            for u_i in ui:
                for dep in ("rail", "stacked"):
                    r = K.close_loop(kind, Ld, T, float(u_i), dep)
                    if not r.get("ok"):
                        continue
                    u_dep = r["dep_margin"]["idu_dep"]
                    if bname == "sym" and not (bx_ind[0] <= u_dep <= bx_ind[1]):
                        continue
                    A = (Wb * Lb + I_d / float(u_i) * Ld + I_d / u_dep * Ld) * 1e12      # um^2
                    pts[dep].append((A, H))
        fr = {d: front(p) for d, p in pts.items()}
        allp = pts["rail"] + pts["stacked"]
        if not allp:
            res[bname] = dict(empty=True); continue
        ref = (max(p[0] for p in allp), min(p[1] for p in allp))
        hvs = {d: hv(fr[d], ref) for d in fr}
        # 교차 지배: rail front 점 중 stacked front 에 지배되는 수, 그 반대
        def dominated(p, F):
            return any(q[0] <= p[0] and q[1] >= p[1] and (q[0] < p[0] or q[1] > p[1]) for q in F)
        cross = dict(rail_dominated_by_stacked=sum(dominated(p, fr["stacked"]) for p in fr["rail"]),
                     stacked_dominated_by_rail=sum(dominated(p, fr["rail"]) for p in fr["stacked"]))
        res[bname] = dict(n_feas={d: len(p) for d, p in pts.items()}, n_front={d: len(f) for d, f in fr.items()},
                          hv=hvs, hv_rel_diff=(hvs["rail"] - hvs["stacked"]) / max(hvs.values()) if max(hvs.values()) > 0 else None,
                          minA={d: min(p[0] for p in pts[d]) if pts[d] else None for d in pts},
                          maxH={d: max(p[1] for p in pts[d]) if pts[d] else None for d in pts}, cross=cross,
                          bounds=dict(out=list(bx_out), ind=list(bx_ind)))
        with open(OUT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(dict(loop=loop, box=bname, **res[bname]), default=float) + "\n")
    return res


if __name__ == "__main__":
    if OUT.exists():
        OUT.unlink()
    for lp in ("P", "N"):
        run_loop(lp)
