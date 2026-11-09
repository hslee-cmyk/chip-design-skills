# current_reuse ICMR 기능 기준 SPICE 실측 (oracle 꼴 재현: .op servo 점마다 개방 .tf 증분 DC 이득)
# 대표 설계점 = wt/_scratch_b81/out/spice/cr_free_y0.85.cir (B81 분석의 '원문 노드 전압 보존 θ', sky130 1.8 V) -- 사본 ref_cr_free_y0.85.cir (sha 대조)
# servo: Vip = Vcm + Vh, Vim = Vcm - Vh, Vh = -0.5*(Vop - Vom) (E 소스, 개방 이득 A 만큼 루프 이득 -> Vod ~ 0 = 봉인점 차동 출력 0 에 묶음),
#        출력 공통모드는 회로 자체 CMFB. 그 점의 Vh* 로 Vh 를 고정한 개방 회로에서 .tf v(vop,vom) -> Adm = tf/2 (Vid = 2 Vh).
# 결과는 점마다 icmr_servo_sweep.jsonl 에 Python 바이너리 append.
import json, os, re, subprocess, sys, tempfile, pathlib, math

HERE = pathlib.Path(__file__).parent
REF = HERE / "ref_cr_free_y0.85.cir"
OUT = HERE / ("icmr_servo_sweep%s.jsonl" % (("_" + sys.argv[1]) if len(sys.argv) > 1 else ""))
NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
TMP = pathlib.Path(tempfile.mkdtemp(prefix="icmr4_crt_sp_", dir=os.environ.get("TEMP")))
DEVS = ["M1a", "M2a", "M3a", "M4a", "M5", "M6", "M7", "M58", "M57", "M63", "M64", "M61", "M68", "M26", "M19", "M38", "M37a"]
KIND = {}
body = []
for ln in REF.read_text(encoding="utf-8").splitlines():
    if ln.startswith("XM"):
        nm = ln.split()[0][1:]
        KIND[nm] = "nfet" if "nfet" in ln else "pfet"
    if ln.startswith(("Vip ", "Vim ", ".control")):
        if ln.startswith(".control"):
            break
        continue
    body.append(ln)
body = "\n".join(body)
if os.environ.get("ALLDEV") == "1":  # 전 MOS 영역 행(O-205 R0) 점검용
    DEVS = sorted(KIND)
NODES = ["vx", "vy", "n1a2a", "n3a4a", "vom1", "vop1", "vbias2", "vbias3", "vcmfb", "vop", "vom", "voc", "ncmfb_tail"]


def dprm(d, p):
    return "@m.x%s.msky130_fd_pr__%s_01v8[%s]" % (d.lower(), KIND[d], p)


def run(net):
    f = TMP / "t.cir"
    f.write_text(net, encoding="utf-8")
    r = subprocess.run([NG, "-b", str(f)], capture_output=True, text=True)
    vals = {}
    for m in re.finditer(r"^\s*([^\s=]+)\s*=\s*([-+0-9.eE]+)\s*$", r.stdout, re.M):
        vals[m.group(1).lower()] = float(m.group(2))
    return vals, r.stdout[-1500:] + r.stderr[-800:]


def app(rec):
    with open(OUT, "ab") as fh:
        fh.write((json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8"))


lo, hi, st = (float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0.30, 1.40, 0.01)
app({"case": "start", "ref": str(REF), "lo": lo, "hi": hi, "step": st})
n = int(round((hi - lo) / st))
for i in range(n + 1):
    x = round(lo + i * st, 6)
    prints = " ".join("v(%s)" % s for s in NODES) + " v(nh)"
    dp = " ".join(dprm(d, p) for d in DEVS for p in ("id", "vds", "vdsat", "gm", "gds"))
    servo = body + "\nVcm ncm 0 DC %r\nEh nh 0 vom vop 0.5\nEip Vip ncm nh 0 1\nEim Vim ncm nh 0 -1\n.control\nset noaskquit\nop\nprint %s\nprint %s\nquit\n.endc\n.end\n" % (x, prints, dp)
    v1, tail1 = run(servo)
    if "v(nh)" not in v1:
        app({"case": "point", "vcm": x, "servo_ok": False, "tail": tail1})
        continue
    vh = v1["v(nh)"]
    ol = body + "\nVcm ncm 0 DC %r\nVhs nh 0 DC %r\nEip Vip ncm nh 0 1\nEim Vim ncm nh 0 -1\n.control\nset noaskquit\ntf v(vop,vom) Vhs\nprint all\nquit\n.endc\n.end\n" % (x, vh)
    v2, tail2 = run(ol)
    tfv = None
    for k, val in v2.items():
        if k.startswith("transfer_function"):
            tfv = val
    adm = (tfv / 2.0) if tfv is not None else None
    rec = {"case": "point", "vcm": x, "servo_ok": True, "vh": vh, "vod": v1.get("v(vop)", 0) - v1.get("v(vom)", 0),
           "tf": tfv, "adm": adm, "adm_db": (20 * math.log10(abs(adm)) if adm else None),
           "nodes": {s: v1.get("v(%s)" % s) for s in NODES}}
    sat = {}
    for d in DEVS:
        idv, vds, vdsat = v1.get(dprm(d, "id").lower()), v1.get(dprm(d, "vds").lower()), v1.get(dprm(d, "vdsat").lower())
        if vds is not None and vdsat is not None:
            sat[d] = {"id": idv, "vds": vds, "vdsat": vdsat, "m": abs(vds) - abs(vdsat), "gm": v1.get(dprm(d, "gm").lower()), "gds": v1.get(dprm(d, "gds").lower())}
    rec["sat"] = sat
    if tfv is None:
        rec["tail"] = tail2
    app(rec)
app({"case": "done"})
