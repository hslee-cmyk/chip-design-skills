# Q-KV1 (다) B 안 순위 마지막 '이름'의 역할 실측 (2026-10-30).
# 고리 = current_reuse class-AB translinear 고리(topology.json netlist 판독):
#   P: VSG11a + VSG11b = VSG15 + VSG9a   (M11a 소스 vdd = 레일 다이오드, M11b 소스 N11a11b = 쌓인 다이오드)
#   N: VGS14a + VGS14b = VGS16 + VGS9b   (M14b 소스 gnd = 레일, M14a 소스 N14a_14b = 쌓인)
#   대칭 고리 {M18a,M20a,M20b,M25}·{M18b,M23a,M24b,M26} 는 같은 연결 복제(M20a 레일·M20b 쌓임, M24b 레일·M23a 쌓임).
# 이름순 선택: P -> M11a(레일), N -> M14a(쌓임), 대칭 P -> M20a(레일), 대칭 N -> M23a(쌓임).
# 두 선택: dep=rail / dep=stacked. θ = (I_Q, I9a, I9b, I11, I14, gm/ID 15·16·9a·9b, 독립 다이오드 gm/ID, L).
# 손계산 = LUT r2(assets/lut_v2_location.json 의 cap_npz) 만. oracle = ngspice sky130 tt 27C 반쪽 2단(이상 바이어스 전류원).
# 결과: 케이스마다 results.jsonl 에 append.
import json, math, pathlib, subprocess, sys, re
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import brentq

HERE = pathlib.Path(__file__).parent
OUT = HERE / "results.jsonl"
RUNS = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/kv1/runs")
LOC = json.loads(pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/lut_v2_location.json").read_text(encoding="utf-8"))
LUTF = pathlib.Path(LOC["root"]["default"]) / LOC["files"]["cap_npz"]["path"]
NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
PDK = "C:/pdk/sky130_fd_pr"
VDD = 1.8

Z = np.load(LUTF, allow_pickle=True)
WREF = float(Z["w_ref_m"])
LG, VG, VD, VS = Z["L"], Z["VGS"], Z["VDS"], Z["VS"]
_I = {}


def interp(kind, L):
    key = (kind, L)
    if key not in _I:
        li = int(np.argmin(np.abs(LG - L)))
        assert abs(LG[li] - L) < 1e-12, f"L {L} not on LUT grid"
        s = "_" + kind
        idv = Z["ID" + s][li]
        gm = Z["GM" + s][li]
        vds = Z["VDSAT" + s][li]
        _I[key] = (RegularGridInterpolator((VG, VD, VS), np.log(np.maximum(idv, 1e-30)), method="cubic"),
                   RegularGridInterpolator((VG, VD, VS), gm / np.maximum(idv, 1e-30), method="cubic"),
                   RegularGridInterpolator((VG, VD, VS), vds, method="linear"))
    return _I[key]


FINE = np.linspace(VG[1], VG[-1], 3001)        # VGS 1차 축(조회 분해능 ~0.6 mV), 0 은 누설이라 제외


def curve(kind, L, vds, vsb, diode=False):
    lid, gmid, _ = interp(kind, L)
    vd = FINE if diode else np.full_like(FINE, vds)
    pts = np.column_stack([FINE, vd, np.full_like(FINE, vsb)])
    return gmid(pts), lid(pts)


def branch(kind, L, vds, vsb, diode=False):
    """강반전 분지(gm/ID 정점 오른쪽) -- 정의역 = [g(VGS_max), g_peak]."""
    g, lid = curve(kind, L, vds, vsb, diode)
    p = int(np.argmax(g))
    return FINE[p:], g[p:], lid[p:]


def g_of(kind, L, vgs, vds, vsb, diode=False):
    lid, gmid, _ = interp(kind, L)
    return float(gmid([[vgs, vgs if diode else vds, vsb]])[0])


def idu(kind, L, vgs, vds, vsb):
    lid, _, _ = interp(kind, L)
    return float(np.exp(lid([[vgs, vds, vsb]])[0])) / WREF


def vdsat(kind, L, vgs, vds, vsb):
    return float(interp(kind, L)[2]([[vgs, vds, vsb]])[0])


def vgs_from_idu(kind, L, iu, vds, vsb, diode=False):
    """θ 좌표 ln IDu(A/m) -> VGS. ln ID 는 VGS 에 단조 증가(실측 확인) -> 해 유일. 정의역 밖이면 None."""
    g, lid = curve(kind, L, vds, vsb, diode)
    t = math.log(iu * WREF)
    if not (lid[0] <= t <= lid[-1]):
        return None
    return float(np.interp(t, lid, FINE))


def margin(kind, L, vgs, vds, vsb, diode):
    """종속 소자 정의역 = LUT 축 안 + gm/ID 정점 오른쪽(엔진 vgs_root 분지 정의와 같은 꼴) -- VGS·ln IDu 여유."""
    v, gb, lid = branch(kind, L, vds, vsb, diode)
    lo, hi = float(v[0]), float(v[-1])
    t = float(np.interp(vgs, FINE, curve(kind, L, vds, vsb, diode)[1]))
    return dict(vgs_dom=[lo, hi], vgs_margin_lo=float(vgs - lo), vgs_margin_hi=float(hi - vgs),
                lnidu_margin_lo=float(t - lid[0]), lnidu_margin_hi=float(lid[-1] - t),
                g_dep=g_of(kind, L, vgs, vds, vsb, diode), idu_dep=float(math.exp(t) / WREF))


def outer(th):
    """고리 우변(독립 소자) -- 두 선택에 공통."""
    vsg15 = vgs_from_idu("p", th["L15"], th["u15"], VDD - 0.9, 0.0)
    vgs16 = vgs_from_idu("n", th["L16"], th["u16"], 0.9, 0.0)
    vg15, vop1 = VDD - vsg15, vgs16
    vbat = vg15 - vop1
    vsg9a = vgs_from_idu("p", th["L9a"], th["u9a"], vbat, vsg15)     # 소스 Vg15, 몸체 vdd -> VSB = VSG15
    vgs9b = vgs_from_idu("n", th["L9b"], th["u9b"], vbat, vop1)      # 소스 Vop1, 몸체 gnd -> VSB = Vop1
    return dict(vsg15=vsg15, vgs16=vgs16, vg15=vg15, vop1=vop1, vbat=vbat, vsg9a=vsg9a, vgs9b=vgs9b,
                Tp=vsg15 + vsg9a, Tn=vgs16 + vgs9b)


def close_loop(kind, L, T, u_ind, dep):
    """두 다이오드(같은 kind·L·전류) 사슬: v_rail + v_stk = T, v_stk 의 VSB = v_rail.
    dep='stacked': 레일 다이오드 ln IDu 독립 -> v_rail 명시 -> v_stk = T - v_rail -> 종속 IDu 순방향 조회(반복 0).
    dep='rail'   : 쌓인 다이오드 ln IDu 독립 -> v_rail 이 v_stk 의 VSB 로 들어가 결합 -> 1차 근 풀이(단조라 해 유일)."""
    rec = dict(dep=dep, u_ind=u_ind, T=T)
    if dep == "stacked":
        vr = vgs_from_idu(kind, L, u_ind, None, 0.0, diode=True)
        if vr is None:
            rec.update(ok=False, why="independent IDu outside rail-diode LUT range")
            return rec
        vs_ = T - vr
        rec.update(v_rail=vr, v_stk=vs_, solve="explicit (0 root iterations)", n_lut_inversions=1)
        if not (FINE[0] <= vs_ <= FINE[-1]):
            rec.update(ok=False, why="dependent VGS off LUT VGS axis")
            return rec
        m = margin(kind, L, vs_, None, vr, True)
    else:
        nit = [0]

        def f(vr):
            nit[0] += 1
            x = vgs_from_idu(kind, L, u_ind, None, vr, diode=True)
            return np.nan if x is None else vr + x - T
        grid = np.linspace(FINE[0], min(T, FINE[-1]), 60)
        vals = np.array([f(x) for x in grid])
        okm = np.isfinite(vals)
        sgn = np.where(okm[:-1] & okm[1:] & (np.sign(vals[:-1]) != np.sign(vals[1:])))[0]
        if len(sgn) == 0:
            rec.update(ok=False, why="no root (independent stacked IDu infeasible / dependent off axis)")
            return rec
        nit[0] = 0
        vr = brentq(f, grid[sgn[0]], grid[sgn[0] + 1], xtol=1e-8)
        vs_ = T - vr
        rec.update(v_rail=vr, v_stk=vs_, solve="implicit 1-D root", n_lut_inversions=nit[0], n_roots=int(len(sgn)))
        m = margin(kind, L, vr, None, 0.0, True)
    indom = m["vgs_margin_lo"] >= 0 and m["vgs_margin_hi"] >= 0
    rec.update(ok=bool(indom), why=None if indom else "dependent left of gm/ID peak (outside branch)", dep_margin=m)
    return rec


def append(obj):
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj) + "\n")


# ---------------- oracle ----------------
def models():
    s = ""
    for k in ("nfet_01v8", "pfet_01v8"):
        s += f'.include "{PDK}/cells/{k}/sky130_fd_pr__{k}__tt.pm3.spice"\n'
        s += f'.include "{PDK}/cells/{k}/sky130_fd_pr__{k}__mismatch.corner.spice"\n'
    s += f'.include "{PDK}/models/parameters/lod.spice"\n'
    return s


def geom(w, l):
    m = max(1, math.ceil(w / (WREF * 1e6) - 1e-9))   # 손가락 폭 <= LUT W_ref
    wf = w / m
    return f"l={l}u w={wf:.4f}u ad={wf*0.5:.4f}p as={wf*0.5:.4f}p pd={wf+2:.4f}u ps={wf+2:.4f}u m={m}"


DEVS = ["M15", "M16", "M9a", "M9b", "M11a", "M11b", "M14a", "M14b"]


def spice(tag, S, cur):
    wd = RUNS / tag
    wd.mkdir(parents=True, exist_ok=True)
    def mos(nm, d, g, s, b):
        k, w, l = S[nm]
        sub = "sky130_fd_pr__nfet_01v8" if k == "n" else "sky130_fd_pr__pfet_01v8"
        return f"X{nm} {d} {g} {s} {b} {sub} {geom(w, l)}\n"
    n = "* kv1\n" + models() + ".temp 27\nvdd vdd 0 1.8\n"
    I8 = cur["I9a"] + cur["I9b"]
    n += f"i8 vdd vg15 {I8}\ni10 vop1 0 {I8}\ni12 n11b 0 {cur['I11']}\ni13 vdd n14a14b {cur['I14']}\n"
    n += mos("M11a", "n11a11b", "n11a11b", "vdd", "vdd") + mos("M11b", "n11b", "n11b", "n11a11b", "vdd")
    n += mos("M9a", "vop1", "n11b", "vg15", "vdd") + mos("M9b", "vg15", "n14a14b", "vop1", "0")
    n += mos("M14a", "n14a14b", "n14a14b", "n14a_14b", "0") + mos("M14b", "n14a_14b", "n14a_14b", "0", "0")
    n += mos("M15", "vom", "vg15", "vdd", "vdd") + mos("M16", "vom", "vop1", "0", "0")
    n += "rf vom vf 1\ncf vf 0 1\ngsv vop1 0 vref vf 1e-3\nvref vref 0 0.9\n"
    n += ".options gmin=1e-15 reltol=1e-6 abstol=1e-15 vntol=1e-9\n.control\nset filetype=ascii\nop\nprint all > op_out.txt\n"
    q = []
    for d in DEVS:
        k = S[d][0]
        for p in ("id", "vds", "vgs", "vdsat", "gm"):
            q.append(f"@m.x{d.lower()}.msky130_fd_pr__{'n' if k == 'n' else 'p'}fet_01v8[{p}]")
    n += "print " + " ".join(q) + " > op_dev.txt\nquit\n.endc\n.end\n"
    (wd / "b.cir").write_text(n, encoding="utf-8")
    for f in ("op_out.txt", "op_dev.txt"):
        if (wd / f).exists():
            (wd / f).unlink()
    subprocess.run([NG, "-b", "b.cir"], cwd=wd, capture_output=True)
    def parse(p):
        vals = {}
        if p.exists():
            for line in p.read_text(errors="replace").splitlines():
                m = re.match(r"\s*(\S+)\s*=\s*([-+0-9.eE]+)", line)
                if m:
                    vals[m.group(1)] = float(m.group(2))
        return vals
    v = parse(wd / "op_out.txt")
    dv = {}
    for k, x in parse(wd / "op_dev.txt").items():
        mm = re.match(r"@m\.x(m\w+)\.msky130_fd_pr__[np]fet_01v8\[(\w+)\]", k)
        if mm:
            dv[f"{mm.group(1)}.{mm.group(2)}"] = x
    return v, dv


def size_all(th, o, P, N):
    S = {}
    def W(kind, L, I, vgs, vds, vsb):
        return I / idu(kind, L, vgs, vds, vsb) * 1e6
    S["M15"] = ("p", W("p", th["L15"], th["IQ"], o["vsg15"], VDD - 0.9, 0.0), th["L15"] * 1e6)
    S["M16"] = ("n", W("n", th["L16"], th["IQ"], o["vgs16"], 0.9, 0.0), th["L16"] * 1e6)
    S["M9a"] = ("p", W("p", th["L9a"], th["I9a"], o["vsg9a"], o["vbat"], o["vsg15"]), th["L9a"] * 1e6)
    S["M9b"] = ("n", W("n", th["L9b"], th["I9b"], o["vgs9b"], o["vbat"], o["vop1"]), th["L9b"] * 1e6)
    S["M11a"] = ("p", W("p", th["Ld"], th["I11"], P["v_rail"], P["v_rail"], 0.0), th["Ld"] * 1e6)
    S["M11b"] = ("p", W("p", th["Ld"], th["I11"], P["v_stk"], P["v_stk"], P["v_rail"]), th["Ld"] * 1e6)
    S["M14b"] = ("n", W("n", th["Ld"], th["I14"], N["v_rail"], N["v_rail"], 0.0), th["Ld"] * 1e6)
    S["M14a"] = ("n", W("n", th["Ld"], th["I14"], N["v_stk"], N["v_stk"], N["v_rail"]), th["Ld"] * 1e6)
    return S


def e0_hand(th, o, P, N):
    rows = {}
    def chk(nm, kind, L, vgs, vds, vsb):
        vs = vdsat(kind, L, vgs, vds, vsb)
        rows[nm] = dict(vds=vds, vdsat=vs, sat=bool(vds >= vs))
    chk("M15", "p", th["L15"], o["vsg15"], VDD - 0.9, 0.0)
    chk("M16", "n", th["L16"], o["vgs16"], 0.9, 0.0)
    chk("M9a", "p", th["L9a"], o["vsg9a"], o["vbat"], o["vsg15"])
    chk("M9b", "n", th["L9b"], o["vgs9b"], o["vbat"], o["vop1"])
    chk("M11a", "p", th["Ld"], P["v_rail"], P["v_rail"], 0.0)
    chk("M11b", "p", th["Ld"], P["v_stk"], P["v_stk"], P["v_rail"])
    chk("M14b", "n", th["Ld"], N["v_rail"], N["v_rail"], 0.0)
    chk("M14a", "n", th["Ld"], N["v_stk"], N["v_stk"], N["v_rail"])
    kvl = dict(P=P["v_rail"] + P["v_stk"] - o["Tp"], N=N["v_rail"] + N["v_stk"] - o["Tn"])
    return dict(sat=rows, all_sat=all(r["sat"] for r in rows.values()), kvl_residual_V=kvl,
                n11b=VDD - o["Tp"], n14a14b=o["Tn"])
