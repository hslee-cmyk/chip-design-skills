# class-AB 부유 배터리(Monticelli) 반쪽 2단 sky130 ngspice 벤치 -- 정지 전류·최소 전류·루프 감도·PVT·배터리 극점.
# 회로 = current_reuse_telescopic_ota 의 M8·M9a·M9b·M10·M11a·M11b·M12·M13·M14a·M14b·M15·M16 연결 그대로
# (topology.json netlist 판독, 2026-10-29). 바이어스 전류원 M8·M10·M12·M13 은 이상 전류원(원문 Fig.7 정지 전류값),
# 1단 출력 = Vop1 에 들어가는 VCCS 서보(1 F 저역 -- DC 만 Vom = 0.9 V 로 고정, AC 에서는 개방).
# 치수 = 원문 Fig.7(a) (Xie & Chen, p.7) W/L 그대로 sky130 에 옮김(공정이 달라 동작 영역은 비슷한 꼴만 -- 절대값 비교용 아님).
# 결과는 케이스마다 results.jsonl 에 append.
import json, subprocess, sys, pathlib, math, re

HERE = pathlib.Path(__file__).parent
NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
PDK = "C:/pdk/sky130_fd_pr"
OUT = HERE / "results.jsonl"

# 원문 Fig.7(a)(b): W/L(um), 정지 전류(uA)
SIZES = dict(M15=("p", 65, 0.36), M16=("n", 25, 0.36), M9a=("p", 3, 0.54), M9b=("n", 1, 0.36),
             M11a=("p", 15, 0.18), M11b=("p", 15, 0.18), M14a=("n", 2, 0.18), M14b=("n", 2, 0.18))
I8, I10, I12, I13 = 1.196e-6, 1.196e-6, 2.199e-6, 2.502e-6   # I10 = I8 (1단 DC 불균형 0 으로 둠)


def models(corner):
    s = ""
    for k in ("nfet_01v8", "pfet_01v8"):
        s += f'.include "{PDK}/cells/{k}/sky130_fd_pr__{k}__{corner}.pm3.spice"\n'
        s += f'.include "{PDK}/cells/{k}/sky130_fd_pr__{k}__mismatch.corner.spice"\n'
    s += f'.include "{PDK}/models/parameters/lod.spice"\n'
    return s


def mos(name, d, g, s, b, scale=None):
    k, w, l = SIZES[name]
    if scale and name in scale:
        w = w * scale[name]
    sub = "sky130_fd_pr__nfet_01v8" if k == "n" else "sky130_fd_pr__pfet_01v8"
    return f"X{name} {d} {g} {s} {b} {sub} {geom(w, l)}\n"


def geom(w, l):
    """W 가 크면 손가락 폭 <= 10 um 의 병렬 m 개(같은 총 W) -- sky130 W bin 정의역 안."""
    m = max(1, math.ceil(w / 10.0 - 1e-9))
    wf = w / m
    return f"l={l}u w={wf:.4f}u ad={wf*0.29:.4f}p as={wf*0.29:.4f}p pd={2*wf+0.58:.4f}u ps={2*wf+0.58:.4f}u m={m}"


def netlist(corner="tt", temp=27, il=0.0, delta=0.0, ac=False, sweep=None, scale=None, cl=1e-12, extra=""):
    n = f"* classab half {corner} {temp}\n" + models(corner) + f".temp {temp}\n"
    n += "vdd vdd 0 1.8\n"
    n += f"i8 vdd vg15 {I8}\n"                      # M8 (pmos 전류원, vdd -> Vg15)
    n += f"i10 vop1 0 {I10}\n"                      # M10 (nmos 싱크, Vop1 -> gnd)
    n += f"i12 n11b 0 {I12}\n"                      # M12
    n += f"i13 vdd n14a14b {I13}\n"                 # M13
    n += mos("M11a", "n11a11b", "n11a11b", "vdd", "vdd", scale)
    n += mos("M11b", "n11b", "n11b", "n11a11b", "vdd", scale)
    n += f"vdel n11b g9a {delta}\n"                 # 루프 전압 섭동 δ (M9a gate = N11b − δ)
    n += mos("M9a", "vop1", "g9a", "vg15", "vdd", scale)
    n += mos("M9b", "vg15", "n14a14b", "vop1", "0", scale)
    n += mos("M14a", "n14a14b", "n14a14b", "n14a_14b", "0", scale)
    n += mos("M14b", "n14a_14b", "n14a_14b", "0", "0", scale)
    n += mos("M15", "vom", "vg15", "vdd", "vdd", scale)
    n += mos("M16", "vom", "vop1", "0", "0", scale)
    # 서보(1단 대역): Vom -> 1 F 저역 -> VCCS 를 Vop1 에 주입. DC 에서 Vom = 0.9 고정, AC 에서는 끊김.
    n += "rf vom vf 1\ncf vf 0 1\n"
    n += "gsv vop1 0 vref vf 1e-3\nvref vref 0 0.9\n"   # Vop1 에서 빼는 전류 = 1 mS·(0.9 − Vf)
    n += f"il vom 0 dc {il}\n"                      # 출력 부하 전류(+ = Vom 에서 끌어냄 -> M15 공급)
    n += f"cl vom 0 {cl}\n"
    n += extra
    n += ".options gmin=1e-15 reltol=1e-5 abstol=1e-15 vntol=1e-8\n"
    n += ".control\nset filetype=ascii\n"
    if sweep is None:
        n += "op\n"
        n += ("print all > op_out.txt\n"
              "print @m.xm15.msky130_fd_pr__pfet_01v8[id] @m.xm16.msky130_fd_pr__nfet_01v8[id] "
              "@m.xm9a.msky130_fd_pr__pfet_01v8[id] @m.xm9b.msky130_fd_pr__nfet_01v8[id] "
              "@m.xm15.msky130_fd_pr__pfet_01v8[gm] @m.xm16.msky130_fd_pr__nfet_01v8[gm] "
              "@m.xm9a.msky130_fd_pr__pfet_01v8[gm] @m.xm9a.msky130_fd_pr__pfet_01v8[gmbs] "
              "@m.xm9b.msky130_fd_pr__nfet_01v8[gm] @m.xm9b.msky130_fd_pr__nfet_01v8[gmbs] "
              "@m.xm9a.msky130_fd_pr__pfet_01v8[gds] @m.xm9b.msky130_fd_pr__nfet_01v8[gds] "
              "@m.xm15.msky130_fd_pr__pfet_01v8[cgg] @m.xm15.msky130_fd_pr__pfet_01v8[cgd] "
              "@m.xm9a.msky130_fd_pr__pfet_01v8[cdd] @m.xm9b.msky130_fd_pr__nfet_01v8[cdd] @m.xm9a.msky130_fd_pr__pfet_01v8[css] "
              "@m.xm9b.msky130_fd_pr__nfet_01v8[css] "
              "@m.xm15.msky130_fd_pr__pfet_01v8[vdsat] @m.xm16.msky130_fd_pr__nfet_01v8[vdsat] "
              "@m.xm9a.msky130_fd_pr__pfet_01v8[vdsat] @m.xm9b.msky130_fd_pr__nfet_01v8[vdsat] > op_dev.txt\n")
    elif sweep == "il":
        n += ("save @m.xm15.msky130_fd_pr__pfet_01v8[id] @m.xm16.msky130_fd_pr__nfet_01v8[id] "
              "@m.xm9a.msky130_fd_pr__pfet_01v8[id] @m.xm9b.msky130_fd_pr__nfet_01v8[id] vop1 vg15 vom\n")
        n += "dc il -300u 300u 2u\n"
        n += ("wrdata sweep_out.txt @m.xm15.msky130_fd_pr__pfet_01v8[id] @m.xm16.msky130_fd_pr__nfet_01v8[id] "
              "@m.xm9a.msky130_fd_pr__pfet_01v8[id] @m.xm9b.msky130_fd_pr__nfet_01v8[id] v(vop1) v(vg15) v(vom)\n")
    if ac:
        n += "ac dec 40 1e3 1e10\n"
        n += "wrdata ac_out.txt v(vg15) v(vop1) v(vom)\n"
    n += "quit\n.endc\n.end\n"
    return n


def run(tag, net, workdir):
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "bench.cir").write_text(net, encoding="utf-8")
    p = subprocess.run([NG, "-b", "bench.cir"], cwd=workdir, capture_output=True, text=True)
    (workdir / "bench.log").write_text(p.stdout + p.stderr, encoding="utf-8")
    return p.returncode


def parse_print(path):
    vals = {}
    for line in pathlib.Path(path).read_text(errors="replace").splitlines():
        m = re.match(r"\s*(\S+)\s*=\s*([-+0-9.eE]+)", line)
        if m:
            vals[m.group(1)] = float(m.group(2))
    return vals


def op(tag, **kw):
    wd = HERE / "runs" / tag
    rc = run(tag, netlist(**kw), wd)
    v = parse_print(wd / "op_out.txt") if (wd / "op_out.txt").exists() else {}
    d = parse_print(wd / "op_dev.txt") if (wd / "op_dev.txt").exists() else {}
    short = {}
    for k, x in d.items():
        mm = re.match(r"@m\.x(m\w+)\.msky130_fd_pr__[np]fet_01v8\[(\w+)\]", k)
        if mm:
            short[f"{mm.group(1)}.{mm.group(2)}"] = x
    rec = dict(tag=tag, rc=rc, kw={k: v_ for k, v_ in kw.items() if k != "extra"}, nodes={k: v[k] for k in v if k in
               ("vg15", "vop1", "vom", "n11b", "n11a11b", "n14a14b", "n14a_14b", "g9a")}, dev=short)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "q"
    if what == "q":
        r = op("q_tt27")
        print(json.dumps(r, indent=1))
