"""P4-R CM 감지 저항 R 비교 bench (current_reuse 대표 동작점 = 손 설계 파일럿 r1, wt/_pilot_current_reuse/cr_r1_*.cir).

측정(R1 = R2 = R마다):
  lg : 차동 루프 이득 T_dm(f) = beta*A (파일럿과 같은 gate 절단), 개루프 A_dm(f)
  cm : CMFB 루프 이득 T_cm(f) -- Voc(R 중점) -> M37a gate 사이 Middlebrook 이중 주입(전압·전류), T = (TvTi-1)/(Tv+Ti+2)
  op : r_out(Vom) = 1/(gds15+gds16), C_voc = cgg(M37a)
변형: ideal(이상 R -- 엔진 MNA 꼴), par(sky130 res_high_po_0p35 모델식의 기생 C를 양 끝에 반씩, PDK 셀 subckt 와 같은 π 묶음).
결과는 케이스마다 results.jsonl 에 append.
"""
import json, math, os, re, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
BASE = os.path.join(HERE, "base_pilot_r1_lg.cir")
RUN = os.path.join(HERE, "runs")
OUT = os.path.join(HERE, "results.jsonl")
os.makedirs(RUN, exist_ok=True)

# sky130_fd_pr__res_high_po_0p35 (cells/res_high_po/*.model.spice): rbody = l*rsheet, rend = rcon (양 끝 각각),
# c = ((l+2*2.08)*w*crpf*1e-12 + 2*(l+2*2.08+w)*crpfsw*1e-6)/2 (양 끝 각각), typical crpf/crpfsw (montecarlo.spice 식의 ic_res = 0 항)
HP = dict(w=0.35, rsheet=1112.41, rcon=589.99, crpf=1.06e-4, crpfsw=5.04e-11)


def par_cap_half(R):
    l = max((R - 2 * HP["rcon"]) / HP["rsheet"], 0.0)
    return ((l + 2 * 2.08) * HP["w"] * HP["crpf"] * 1e-12 + 2 * (l + 2 * 2.08 + HP["w"]) * HP["crpfsw"] * 1e-6) / 2, l


def circuit_lines():
    txt = open(BASE, encoding="utf-8").read().split("\n")
    i_ctl = next(i for i, l in enumerate(txt) if l.strip().lower() == ".control")
    return txt[:i_ctl]


def build(R, mode, variant):
    lines = circuit_lines()
    out = []
    cpar, _ = par_cap_half(R)
    for l in lines:
        low = l.lower()
        if low.startswith("r1 ") or low.startswith("r2 "):
            continue
        if mode == "cm":
            if low.startswith("vtp ") or low.startswith("vtm "):
                continue
            if low.startswith("lbp ") or low.startswith("lbm "):
                # spec cm_loop 뷰: 입력 교류접지(sizing_spec pm_cm_ss_deg _view_comment) -- 입력을 ncm(DC 소스)에 직접
                l = "v" + l[1:].replace(" 1e15", " dc 0")
            l = l.replace("Vip_g", "Vip").replace("Vim_g", "Vim")
            if low.startswith("xm37a "):
                l = l.replace(" Voc ", " Voc_g ")
        out.append(l)
    mid = "Voc_Rn" if mode == "cm" else "Voc"
    out.append(f"r1 Vom {mid} {R:.6e}")
    out.append(f"r2 {mid} Vop {R:.6e}")
    if variant == "par":
        out.append(f"cpr1a Vom 0 {cpar:.6e}")
        out.append(f"cpr1b {mid} 0 {cpar:.6e}")
        out.append(f"cpr2a {mid} 0 {cpar:.6e}")
        out.append(f"cpr2b Vop 0 {cpar:.6e}")
    if mode == "cm":
        out.append("vinj Voc_g Voc_R dc 0 ac 1")
        out.append("vsy Voc_R Voc_Rn dc 0")
        out.append("iinj 0 Voc_R dc 0 ac 0")
    tag = f"{mode}_{variant}_R{R:.0e}".replace("+", "")
    f_ac = os.path.join(RUN, tag + "_ac.txt").replace("\\", "/")
    f_ac2 = os.path.join(RUN, tag + "_ac2.txt").replace("\\", "/")
    ctl = [".control", "op",
           "print @m.xm15.msky130_fd_pr__pfet_01v8[gds] @m.xm16.msky130_fd_pr__nfet_01v8[gds] @m.xm15.msky130_fd_pr__pfet_01v8[gm] @m.xm16.msky130_fd_pr__nfet_01v8[gm]",
           "print @m.xm37a.msky130_fd_pr__nfet_01v8[cgg] @m.xm37a.msky130_fd_pr__nfet_01v8[cgs] @m.xm37a.msky130_fd_pr__nfet_01v8[cgd] @m.xm37a.msky130_fd_pr__nfet_01v8[gm]",
           "print v(Vom) v(Vop) v(Vcmfb)",
           ]
    if mode == "lg":
        ctl += ["ac dec 40 1 10e9",
                "let T = -(v(Vip)-v(Vim))/(v(Vip_g)-v(Vim_g))",
                "let A = (v(Vop)-v(Vom))/(v(Vip_g)-v(Vim_g))",
                f"wrdata {f_ac} real(T) imag(T) real(A) imag(A)"]
    else:
        ctl += ["print v(Voc_R)",
                "ac dec 40 1 10e9",
                "let Tv = -v(Voc_R)/v(Voc_g)",
                f"wrdata {f_ac} real(Tv) imag(Tv)",
                "alter vinj ac = 0", "alter iinj ac = 1",
                "ac dec 40 1 10e9",
                "let Ti = i(vsy)/(-i(vinj))",
                f"wrdata {f_ac2} real(Ti) imag(Ti)"]
    ctl += ["quit", ".endc", ".end"]
    path = os.path.join(RUN, tag + ".cir")
    open(path, "w", encoding="utf-8").write("\n".join(out + ctl) + "\n")
    return path, tag, f_ac, f_ac2, cpar


def load_cplx(f, ncols):
    d = np.loadtxt(f)
    fr = d[:, 0]
    cols = []
    # wrdata: freq re1 freq im1 ... (each vector preceded by its scale)
    k = 1
    vals = []
    while k < d.shape[1]:
        vals.append(d[:, k]); k += 2
    for j in range(0, len(vals), 2):
        cols.append(vals[j] + 1j * vals[j + 1])
    return fr, cols


def loop_metrics(fr, T):
    mag = np.abs(T)
    ph = np.unwrap(np.angle(T)) * 180 / math.pi
    ph0 = ph[0]
    sign_flip = abs(((ph0 + 180) % 360) - 180) > 90  # DC 위상이 ±180 근처면 부호 반전 규약
    if sign_flip:
        ph = ph - 180 * round(ph0 / 180)
    else:
        ph = ph - 360 * round(ph0 / 360)
    t0_db = 20 * math.log10(mag[0])
    idx = np.where((mag[:-1] >= 1) & (mag[1:] < 1))[0]
    if len(idx) == 0:
        return dict(t0_db=t0_db, ugf_hz=None, pm_deg=None, sign_flip=bool(sign_flip))
    i = idx[0]
    x0, x1 = math.log10(fr[i]), math.log10(fr[i + 1])
    y0, y1 = 20 * math.log10(mag[i]), 20 * math.log10(mag[i + 1])
    xu = x0 + (0 - y0) * (x1 - x0) / (y1 - y0)
    pu = ph[i] + (ph[i + 1] - ph[i]) * (xu - x0) / (x1 - x0)
    return dict(t0_db=t0_db, ugf_hz=10 ** xu, pm_deg=180 + pu, sign_flip=bool(sign_flip))


def parse_op(log):
    vals = {}
    for m in re.finditer(r"^(@m\.[^\s=]+|v\([^)]+\))\s*=\s*([-+0-9.eE]+)", log, re.M):
        vals[m.group(1)] = float(m.group(2))
    return vals


def run_case(R, mode, variant):
    path, tag, f_ac, f_ac2, cpar = build(R, mode, variant)
    p = subprocess.run([NG, "-b", path], capture_output=True, text=True, cwd=RUN)
    log = p.stdout + p.stderr
    open(os.path.join(RUN, tag + ".log"), "w", encoding="utf-8").write(log)
    op = parse_op(log)
    rec = dict(R=R, mode=mode, variant=variant, cpar_half_f=cpar if variant == "par" else 0.0, op=op)
    try:
        if mode == "lg":
            fr, (T, A) = load_cplx(f_ac, 2)
            rec["T_dm"] = loop_metrics(fr, T)
            rec["A_dm_dc_db"] = 20 * math.log10(abs(A[0]))
        else:
            fr, (Tv,) = load_cplx(f_ac, 1)
            fr2, (Ti,) = load_cplx(f_ac2, 1)
            T = (Tv * Ti - 1) / (Tv + Ti + 2)
            rec["T_cm"] = loop_metrics(fr, T)
            rec["T_cm_vonly"] = loop_metrics(fr, Tv)
    except Exception as e:  # 기록하고 계속(조용한 생략 아님 -- 결과 칸에 오류)
        rec["error"] = repr(e)
    with open(OUT, "a", encoding="utf-8") as fo:
        fo.write(json.dumps(rec) + "\n")
    return rec


if __name__ == "__main__":
    Rs = [float(x) for x in sys.argv[1].split(",")]
    variants = sys.argv[2].split(",") if len(sys.argv) > 2 else ["ideal", "par"]
    for v in variants:
        for R in Rs:
            for mode in ("lg", "cm"):
                r = run_case(R, mode, v)
                key = "T_dm" if mode == "lg" else "T_cm"
                print(v, mode, f"{R:.3g}", r.get(key), r.get("A_dm_dc_db"), r.get("error", ""))
