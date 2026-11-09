"""sf_pushpull_output_opamp -- 손계산 설계점 + ICMR servo 훑기(.op) + 점별 증분 DC 이득(.tf) oracle 측정.

목적: ICMR 기능 기준 후보(기준점 대비 허용 저하 / 절대 하한 = gain_ss_db)를 적용한 창 끝을 SPICE로 재고 영역 행 창(VDS >= VDSAT)과 비교.
설계점: LUT gm/ID 선택(아래 DESIGN 주석) -> 자기 바이어스 R은 SPICE op의 VSG/VDSAT로 포화 창 중앙에 맞춤(반복),
출력단 배율 k는 출력 정지 전류 목표에 맞춤. 저장소·spec·topology 쓰기 0. 결과는 케이스마다 jsonl append.
연결은 topology.json netlist를 그대로 읽는다(소자 이름·넷 이름 하드코딩은 크기 표 키로만).
"""
import json, math, os, re, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "spice_icmr.jsonl"
TOPO = Path("C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library/sf_pushpull_output_opamp.topology.json")
NG = "C:/ngspice/Spice64/bin/ngspice_con.exe"
PDK = "C:\\pdk\\sky130_fd_pr"
TMP = Path(tempfile.mkdtemp(prefix="icmr4_sf_spice_"))
VDD, VSS, AGND = 1.8, 0.0, 0.9          # spec human.supplies_v
IBIAS = 5e-05                           # spec element_values.IBias
VCM0 = AGND                             # spec human.input_dc = agnd
VO0 = AGND                              # servo 출력 목표 = beta=1 사용(입력 DC = 출력 DC)
GAIN_SPEC_DB = 65.0                     # spec constraints gain_ss_db >= 65

# DESIGN (손계산 선택, 근거는 보고서 §3): 단위 W = 5 um(LUT w_ref), m = 병렬 배수
# 거울 pmos L 1u gm/ID~15, 거울 nmos L 1u gm/ID~20(M20 VDSAT 헤드룸), 입력쌍 L 0.5u gm/ID~20, 꼬리 L 1u gm/ID~15,
# follower M18/M19, 출력 M21/M22 = L 0.15u(sky130 pfet 최소 L; VSB 0.9에서 |VT| 롤오프로만 VSG21 <= vout - VDSAT20 안 전류 밀도 확보 -- LUT 실측 §2.3)(헤드룸 사슬 vdd >= VDSAT17+VSG18+VGS19+VDSAT20)
SIZE = {
    "M1": (0.5e-6, 6.2), "M2": (0.5e-6, 6.2),
    "M3": (1e-6, 4.35), "M4": (1e-6, 4.35),
    "M5": (1e-6, 12.0), "M6": (1e-6, 12.0), "M7": (1e-6, 12.0), "M8": (1e-6, 12.0),
    "M9": (1e-6, 12.0), "M10": (1e-6, 12.0), "M11": (1e-6, 12.0), "M12": (1e-6, 12.0), "M17": (1e-6, 12.0),
    "M13": (1e-6, 7.0), "M14": (1e-6, 7.0), "M15": (1e-6, 7.0), "M16": (1e-6, 7.0), "M20": (1e-6, 7.0),
    "M18": (0.15e-6, 4.0), "M19": (0.15e-6, 2.0),
    "M22": (0.15e-6, 1.0), "M21": (0.15e-6, 3.0),
}


def log(rec):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


TOP = json.loads(TOPO.read_text(encoding="utf-8"))
DEVS = TOP["netlist"]
PASS = TOP["passive_elements"]


def bulk(d):
    return "vss" if d["kind"] == "nmos" else "vdd"    # DEC-61/O-188 기본 레일(원문 그림 M18/M21 VDD, M19/M22 VSS와 같음)


def model(d):
    return "sky130_fd_pr__nfet_01v8" if d["kind"] == "nmos" else "sky130_fd_pr__pfet_01v8"


def header():
    return "\n".join([
        "* sf_pushpull icmr4",
        f'.include "{PDK}\\cells\\nfet_01v8\\sky130_fd_pr__nfet_01v8__tt.pm3.spice"',
        f'.include "{PDK}\\cells\\nfet_01v8\\sky130_fd_pr__nfet_01v8__mismatch.corner.spice"',
        f'.include "{PDK}\\models\\parameters\\lod.spice"',
        f'.include "{PDK}\\cells\\pfet_01v8\\sky130_fd_pr__pfet_01v8__tt.pm3.spice"',
        f'.include "{PDK}\\cells\\pfet_01v8\\sky130_fd_pr__pfet_01v8__mismatch.corner.spice"',
        ".temp 27",
        ".option gmin=1e-15 reltol=1e-6 abstol=1e-15 vntol=1e-9 itl1=1000 itl2=1000",
    ])


def body(sz, R, Cc):
    lines = []
    for d in DEVS:
        L, m = sz[d["name"]]
        lines.append(f"X{d['name']} {d['drain']} {d['gate']} {d['source']} {bulk(d)} {model(d)} l={L} w=5e-06 m={m}")
    for p in PASS:
        t0, t1 = p["terminals"] if "terminals" in p else (p["t0"], p["t1"])
        if p["kind"] == "resistor":
            lines.append(f"R{p['name']} {t0} {t1} {R[p['name']]}")
        else:
            lines.append(f"C{p['name']} {t0} {t1} {Cc if p['name'] == 'Cc' else 1e-12}")
    lines += [f"IBias vdd NB DC {IBIAS}", f"Vvdd vdd 0 DC {VDD}", f"Vvss vss 0 DC {VSS}", f"Vagnd agnd 0 DC {AGND}"]
    return "\n".join(lines)


def dev_vec(d, q):
    return f"@m.x{d['name'].lower()}.m{model(d)}[{q}]"


def run(deck, tag):
    p = TMP / f"{tag}.cir"
    p.write_text(deck, encoding="utf-8")
    r = subprocess.run([NG, "-b", str(p)], capture_output=True, text=True)
    return r.stdout + r.stderr


def parse(out):
    vals = {}
    for line in out.splitlines():
        m = re.match(r"^\s*(\S+)\s*=\s*([-+0-9.eE]+)\s*$", line)
        if m:
            try:
                vals[m.group(1).lower()] = float(m.group(2))
            except ValueError:
                pass
    return vals


NODES = sorted({d[t] for d in DEVS for t in ("drain", "gate", "source")} | {"vout", "y"})


def probe_lines():
    ls = ["set numdgt=12"]
    for n in NODES:
        ls.append(f"print v({n.lower()})")
    for d in DEVS:
        for q in ("id", "vds", "vdsat", "vgs", "gm", "gmbs", "vth"):
            ls.append(f"print {dev_vec(d, q)}")
    return ls


def servo_deck(sz, R, Cc, x, vo):
    # 입력 공통모드 x: vin_p = x, vin_n = vout + (x - vo) -> DC 해에서 vout ~ vo(+offset/A), servo = 연결 소스(되먹임 소자 아님)
    return "\n".join([header(), body(sz, R, Cc), f"Vinp vin_p 0 DC {x}", f"Vfb vin_n vout DC {x - vo}",
                      ".control", "op", *probe_lines(), "quit", ".endc", ".end"])


def open_deck(sz, R, Cc, x, vd):
    # 개루프: vin_p = x + vd/2, vin_n = x - vd/2 (Vdif 독립원 -> .tf 차동 DC 이득)
    return "\n".join([header(), body(sz, R, Cc), f"Vcm cm 0 DC {x}", f"Vdif dif 0 DC {vd}",
                      "Bp vin_p 0 V = v(cm) + v(dif)/2", "Bn vin_n 0 V = v(cm) - v(dif)/2",
                      ".control", "op", *probe_lines(), "tf v(vout) Vdif", "print all", "quit", ".endc", ".end"])


def devstate(v):
    rows = {}
    for d in DEVS:
        vds = v.get(dev_vec(d, "vds").lower()); vdsat = v.get(dev_vec(d, "vdsat").lower()); idv = v.get(dev_vec(d, "id").lower())
        if vds is None or vdsat is None:
            rows[d["name"]] = None
            continue
        rows[d["name"]] = {"vds": vds, "vdsat": vdsat, "sat_margin": abs(vds) - abs(vdsat), "id": idv,
                           "gm": v.get(dev_vec(d, "gm").lower()), "vgs": v.get(dev_vec(d, "vgs").lower())}
    return rows


DOWN = {"R1a": "M1", "R1b": "M2", "R1c": "M12"}     # R 아래쪽 끝 넷의 채널 소자(연결: R1a.t1=N1=M1.drain, R1b.t1=N2=M2.drain, R1c.t0=N12=M12.drain)


def tune_R(sz, Cc, R):
    """자기 바이어스 R: 포화 창 [VSGc - VSGm + VDSATm, VSGc - VDSATc] 중앙(max-min 여유) -- 창은 SPICE op로 읽음."""
    pairs = {"R1a": ("M5", "M6"), "R1b": ("M7", "M8"), "R1c": ("M13", "M14")}   # (캐스코드, 거울) -- 연결: R 양끝 = 캐스코드 게이트/거울 게이트
    hist = []
    for it in range(6):
        v = parse(run(servo_deck(sz, R, Cc, VCM0, VO0), f"tuneR{it}"))
        st = devstate(v)
        newR = {}
        for r, (c, mm) in pairs.items():
            vc, vm = st[c], st[mm]
            lo = abs(vc["vgs"]) - abs(vm["vgs"]) + abs(vm["vdsat"])
            hi = abs(vc["vgs"]) - abs(vc["vdsat"])
            I = abs(vc["id"])
            # max-min: IR 강하는 거울 소자 여유(IR - lo)를 늘리고 R 아래 소자(입력쌍 M1/M2 또는 M12) 여유를 같은 양 줄인다(KVL)
            down = st[DOWN[r]]["sat_margin"]
            ir = R[r] * I
            m_c = ir - lo
            ir_new = min(max(ir + (down - m_c) / 2, lo), hi)
            newR[r] = ir_new / I
            hist.append({"it": it, "R": r, "lo_V": lo, "hi_V": hi, "I": I, "down_margin": down, "R_new": newR[r]})
        R = newR
    return R, hist


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else "base"
    sz = dict(SIZE)
    R = {"R1a": 6000.0, "R1b": 6000.0, "R1c": 6000.0}
    Cc = 1e-12
    # 1) 출력단 배율 k: 출력 정지 전류 목표 = Rout <= 1 kOhm(spec) 만족하는 최소(gm21+gm22+gmb >= 1 mS) -- 2분 탐색
    R, hist = tune_R(sz, Cc, R)
    log({"case": case, "step": "tune_R", "hist": hist, "R": R})
    k_lo, k_hi = 0.05, 50.0
    base22, base21 = sz["M22"][1], sz["M21"][1]
    for it in range(14):
        k = math.sqrt(k_lo * k_hi)
        sz["M22"] = (sz["M22"][0], base22 * k); sz["M21"] = (sz["M21"][0], base21 * k)
        v = parse(run(servo_deck(sz, R, Cc, VCM0, VO0), f"k{it}"))
        st = devstate(v)
        g = sum(abs(st[n]["gm"]) + abs(v.get(dev_vec(next(d for d in DEVS if d['name'] == n), 'gmbs').lower(), 0.0)) for n in ("M21", "M22"))
        if g >= 1e-3:
            k_hi = k
        else:
            k_lo = k
    k = k_hi
    sz["M22"] = (sz["M22"][0], base22 * k); sz["M21"] = (sz["M21"][0], base21 * k)
    # 2) Cc: GB = gm1/Cc(원문 정의 Allen p.26-6 'GB' -- 손계산 식) = spec gbw_ss_hz
    v = parse(run(servo_deck(sz, R, Cc, VCM0, VO0), "ref"))
    st = devstate(v)
    gm1 = abs(st["M1"]["gm"])
    Cc = gm1 / (2 * math.pi * 60e6)
    v = parse(run(servo_deck(sz, R, Cc, VCM0, VO0), "ref2"))
    st = devstate(v)
    nodes = {n: v.get(f"v({n.lower()})") for n in NODES}
    log({"case": case, "step": "design", "k_out": k, "size": sz, "R": R, "Cc": Cc, "gm1": gm1, "nodes": nodes, "dev": st,
         "gm_out_sum_incl_gmb": None})
    # 3) ICMR servo 훑기
    xs = [round(0.30 + 0.01 * i, 3) for i in range(0, 151)]
    rows = []
    for x in xs:
        vs = parse(run(servo_deck(sz, R, Cc, x, VO0), f"s{int(x*1000)}"))
        vinn = vs.get("v(vin_n)")
        vout_s = vs.get("v(vout)")
        if vinn is None:
            rec = {"case": case, "step": "icmr", "x": x, "status": "servo_fail"}
            log(rec); rows.append(rec); continue
        vd = x - vinn
        vo = parse(run(open_deck(sz, R, Cc, x, vd), f"o{int(x*1000)}"))
        A = None
        for key in ("transfer_function", "v(vout)/vdif#transfer_function"):
            pass
        for kk, val in vo.items():
            if "transfer_function" in kk:
                A = val
        st = devstate(vo)
        worst = min(((n, r["sat_margin"]) for n, r in st.items() if r), key=lambda t: t[1])
        rec = {"case": case, "step": "icmr", "x": x, "vd_servo": vd, "vout_servo": vout_s, "vout_open": vo.get("v(vout)"),
               "A": A, "A_db": (20 * math.log10(abs(A)) if A else None),
               "worst_sat": worst, "neg_sat": [(n, round(r["sat_margin"], 4)) for n, r in st.items() if r and r["sat_margin"] < 0],
               "i_tail": st["M3"]["id"], "i_m18": st["M18"]["id"], "i_m21": st["M21"]["id"], "i_m22": st["M22"]["id"],
               "tail_v": vo.get("v(tail)"), "n1": vo.get("v(n1)"), "y": vo.get("v(y)")}
        log(rec); rows.append(rec)
    print("done", TMP)


if __name__ == "__main__":
    main()
