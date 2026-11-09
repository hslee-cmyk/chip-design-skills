# q8 SPICE 확인 -- ngcc_3stage_ff: 출발점 L 칸 후보(안별 L 지도)에서 다단 DC 이득이 spec gain_ss_db >= 111 dB 에 닿는가.
# 회로 = icmr4 ngcc 분석의 손 사이징 시험점(wt/_drafts/evidence/2026-11-01/icmr4/ngcc_3stage_ff_files/icmr_servo_spice.py 의 SIZES·VBP·VBN 을 그대로 읽어 씀 --
#        L 을 바꿀 때 W/L 유지 배율(같은 전류밀도 근사)도 그 스크립트와 같은 규칙). 시험점은 spec 값·엔진 점이 아니다(측정 매개변수).
# 측정 = servo(출력 Vref 고정) 동작점 .op + .tf v(e) vref -> A = 1/(de/dVref) - 1 (DC 소신호, 원칙 3). 결과 = 케이스마다 jsonl append.
import importlib.util, json, math, re, subprocess, sys, pathlib, hashlib

HERE = pathlib.Path(__file__).parent
OUT = HERE / "q8_spice_ngcc.jsonl"
SRC = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-01/icmr4/ngcc_3stage_ff_files/icmr_servo_spice.py")
spec_ = importlib.util.spec_from_file_location("ngcc_src", SRC)
src = importlib.util.module_from_spec(spec_)
spec_.loader.exec_module(src)
NG = src.NG
WORK = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/q8_spice_ngcc")
WORK.mkdir(exist_ok=True)
# W 하한 = LUT manifest 의 kind 별 가장 좁은 슬라이스 폭(그 아래는 PDK 모델 bin 없음 -- ngspice 'could not find a valid modelname' 실측). 값은 manifest 에서 읽음.
_MAN = json.loads(pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/manifest.json").read_text(encoding="utf-8"))
WMIN_UM = {"n": min(e["w_um"] for e in _MAN["slices"] if e["device"] == "nfet_01v8"), "p": min(e["w_um"] for e in _MAN["slices"] if e["device"] == "pfet_01v8")}
CLAMPED = []


def app(rec):
    with open(OUT, "ab") as fh:
        fh.write((json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8"))


def netlist(vcm, vref, Lmap):
    lines = ["* q8 ngcc servo point", src.INC, ".temp 27", ".option gmin=1e-15 reltol=1e-6 abstol=1e-15 vntol=1e-9 itl1=1000",
             "Vdd vdd 0 DC 1.8", "Vbp VBP 0 DC %g" % src.VBP, "Vbn VBN 0 DC %g" % src.VBN,
             "Vref vref 0 DC %g" % vref, "Vcm vcm 0 DC %g" % vcm, "Ee e 0 vref Vout 1", "Ep Vinp vcm e 0 0.5", "En Vinn vcm e 0 -0.5"]
    for n, (k, d, g, s, w) in src.SIZES.items():
        b = "vdd" if k == "p" else "0"
        L = Lmap[n]
        w = w * L / 5e-7
        if w < WMIN_UM[k]:
            CLAMPED.append((n, round(w, 4), WMIN_UM[k]))
            w = WMIN_UM[k]
        m = max(1, math.ceil(w / 10.0))
        lines.append("X%s %s %s %s %s sky130_fd_pr__%sfet_01v8 l=%g w=%g m=%d" % (n, d, g, s, b, k, L, w / m * 1e-6, m))
    lines += ["CL Vout 0 10p", "Cm1 V1 Vout 1.68p", "Cm2 V2 Vout 1.32p"]
    sv = " ".join("%s[%s]" % (src.dev(n), p) for n in src.SIZES for p in ("vds", "vdsat", "id"))
    lines += [".control", "set noaskquit", "option numdgt=12", "save all " + sv, "op", "print v(Vout) v(e) v(TAIL) v(V1) v(V2)"]
    for n in src.SIZES:
        lines.append("print %s[vds] %s[vdsat] %s[id]" % ((src.dev(n),) * 3))
    lines += ["tf v(e) vref", "print all", "quit", ".endc", ".end"]
    return "\n".join(lines) + "\n"


def run(case, Lmap, vcm=0.5, vref=0.9):
    del CLAMPED[:]
    p = WORK / (case + ".cir")
    p.write_text(netlist(vcm, vref, Lmap), encoding="utf-8")
    r = subprocess.run([NG, "-b", str(p)], capture_output=True, text=True, cwd=str(WORK))
    v = src.parse(r.stdout)
    tfk = [k for k in v if "transfer" in k]
    rec = {"case": case, "vcm": vcm, "vref": vref, "L_um": {k: round(x * 1e6, 4) for k, x in Lmap.items()}, "ok": bool(tfk and "v(vout)" in v), "w_clamped_to_wmin": list(CLAMPED)}
    if rec["ok"]:
        de = v[tfk[0]]
        A = 1.0 / de - 1.0
        rec["A_db"] = 20 * math.log10(abs(A))
        rec["vout"] = v["v(vout)"]
        sat = {}
        for nm in src.SIZES:
            d = src.dev(nm).lower()
            sat[nm] = abs(v.get(d + "[vds]", float("nan"))) - abs(v.get(d + "[vdsat]", float("nan")))
        rec["min_sat_margin_v"] = min(sat.values())
        rec["min_sat_dev"] = min(sat, key=sat.get)
    else:
        rec["stdout_tail"] = r.stdout[-800:]
    app(rec)
    print(json.dumps(rec)[:400])


names = list(src.SIZES)
app({"case": "src", "path": str(SRC), "sha256": hashlib.sha256(SRC.read_bytes()).hexdigest(), "pm3_include": src.INC.strip().splitlines()[0]})
app({"case": "rerun_note", "note": "앞 케이스 uniform_L0.15·ga_startL 은 W < 모델 최소 폭으로 ngspice 실패 -- W 하한 clamp 추가 뒤 재실행"})
for Lu in (() if "--bintop" in sys.argv else (0.15, 0.5, 1.0)):
    run("uniform_L%g" % Lu, {n: Lu * 1e-6 for n in names})
# (가) 실측 L 지도: q8_engine_gainL.jsonl ngcc ga rung0 -- 동치류 주인 L 을 멤버에 펼침(주인 표 = 같은 실행의 rung0_L; 멤버 소속은 아래 표, 근거 = 연결: 같은 gate·source 묶음)
ga_owner = {"M0": 0.4948, "M1": 0.4948, "M2": 0.4948, "M3": 0.4948, "M6A": 0.15, "M8": 0.9415, "M9": 0.9415, "M11": 0.9415, "M13": 0.4092}
member_of = {"M0": "M0", "M5": "M0", "M12": "M0", "M1": "M1", "M2": "M2", "M3": "M3", "M4": "M3", "M6B": "M3", "M6A": "M6A", "M7": "M6A",
             "M8": "M8", "M14": "M8", "M9": "M9", "M10": "M9", "M11": "M11", "M13": "M13"}
app({"case": "ga_member_map", "member_of": member_of, "note": "동치류 소속은 연결(같은 gate·source 넷) 판독 -- 엔진 l_ties 출력은 rung0 주인만 기록됨"})
if "--bintop" not in sys.argv:
    run("ga_startL", {n: ga_owner[member_of[n]] * 1e-6 for n in names})
# (가) 칸 안 위 끝(외층 SLSQP 가 bin 고정·bin 안 연속으로 L 을 올릴 수 있는 한계, LR10 L-a): 칸 2 = bin [0.25, 0.5] um, 칸 3 = [0.5, 1.0] um, 칸 0 = [0.15, 0.18] um (LUT meta model_bin_per_L_at_w_ref)
if "--bintop" in sys.argv:
    top = {"M0": 0.5, "M1": 0.5, "M2": 0.5, "M3": 0.5, "M6A": 0.18, "M8": 1.0, "M9": 1.0, "M11": 1.0, "M13": 0.5}
    run("ga_cell_top", {n: top[member_of[n]] * 1e-6 for n in names})
