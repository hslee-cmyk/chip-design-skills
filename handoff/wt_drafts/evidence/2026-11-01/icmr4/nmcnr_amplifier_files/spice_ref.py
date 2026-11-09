# nmcnr_amplifier ICMR 기능 기준 실측(oracle 쪽, AI 손계산 + SPICE -- 엔진 아님).
# 목적: '입력 공통모드가 움직일 때 무엇이 먼저 무너지나'와 기능 기준 후보(기준점 대비 허용 저하 X dB, 절대 하한 = spec gain 하한)별 창 끝을
#       물리적으로 말이 되는 손계산 설계점(R-설계)에서 잰다. R-설계의 W·L·전류는 측정 매개변수(설계 권고·spec 값 아님).
# 연결 = library topology.json netlist·passive_elements 그대로(이름·단자 읽기만), bulk = DEC-61 기본(nmos 최저·pmos 최고 레일).
# 바이어스 VB1~VB5 = 외부 바이어스 입력(topology bias_inputs) -- 측정용 복제 diode + 이상 전류원으로 만든다(VB3 = 목표 V_F + VGS 복제).
# 측정 구성 = 계획 N3.8 'ICMR 측정 구성'(servo): 비반전 입력 = x, 반전 입력 = V(out) - Vofs + (x - x0) (E 소스 + 1e12 H choke + 1 F AC 결합)
#   -> 출력이 기준점 V_out 에 DC 로 묶인다. 점마다 .op(소자 vds·vdsat·id) + .ac 1점(f = 0.01 Hz, 차동 AC ±0.5) = 증분 DC 이득 근사.
# 모델 = LUT meta model_files_sha256 와 sha 대조한 파일. 결과는 점마다 Python 바이너리 append.
import json, pathlib, re, subprocess, sys, hashlib, math
import numpy as np
HERE = pathlib.Path(__file__).parent
TMP = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/icmr4_nmcnr_spice"); TMP.mkdir(parents=True, exist_ok=True)
NG = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
PDK = pathlib.Path(r"C:/pdk/sky130_fd_pr")
LIB = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library")
LUTNPZ = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz")
CELL = {"nmos": "sky130_fd_pr__nfet_01v8", "pmos": "sky130_fd_pr__pfet_01v8"}
OUT = HERE / "spice_ref.jsonl"
z = np.load(LUTNPZ, allow_pickle=True)
meta = json.loads(str(z["meta_json"]))
INC, shaok = [], {}
for dev, files in meta["model_files_sha256"].items():
    for rel, sha in files.items():
        if rel.endswith(".csv"):
            continue
        shaok[rel] = hashlib.sha256((PDK / rel).read_bytes()).hexdigest() == sha
        if rel not in INC:
            INC.append(rel)
assert all(shaok.values()), shaok
topo = json.loads((LIB / "nmcnr_amplifier.topology.json").read_text(encoding="utf-8"))
spec = json.loads((LIB / "nmcnr_amplifier.sizing_spec.json").read_text(encoding="utf-8"))["human"]
rails = spec["supplies_v"]["values"]                       # vdd 1.8, vss 0, agnd 0.9 (spec 선언)
VDD, VSS, AGND = rails["vdd"], rails["vss"], rails["agnd"]
WREF = float(z["w_ref_m"]); Lax = z["L"]; VGSax = z["VGS"]; VDSax = z["VDS"]


def app(rec):
    with open(OUT, "ab") as fh:
        fh.write((json.dumps(rec, default=float, ensure_ascii=False) + "\n").encode("utf-8"))


def w_for(kind, L, gmid, I, vds=0.5):
    """LUT(VS=0, VDS 격자점 = vds 근처) 에서 gm/ID = gmid 인 VGS 의 ID/W -> W = I / (ID/W). 측정 설계용 손계산."""
    s = "_n" if kind == "nmos" else "_p"
    li = int(np.argmin(abs(Lax - L))); di = int(np.argmin(abs(VDSax - vds)))
    idv = z["ID" + s][li, :, di, 0]; gmv = z["GM" + s][li, :, di, 0]
    ok = idv > 0
    g = np.where(ok, gmv / np.where(ok, idv, 1), 0)
    # 강반전 쪽에서 약반전 쪽으로 gm/ID 가 커진다 -- VGS 증가 방향으로 처음 gm/ID <= gmid 가 되는 구간에서 선형 보간
    k = next(i for i in range(1, len(VGSax)) if ok[i] and ok[i - 1] and g[i - 1] >= gmid >= g[i])
    t = (g[k - 1] - gmid) / (g[k - 1] - g[k])
    jd = (idv[k - 1] + t * (idv[k] - idv[k - 1])) / WREF
    return I / jd, float(VGSax[k - 1] + t * (VGSax[k] - VGSax[k - 1]))


# ---- R-설계(측정 매개변수): L 공통, 전류·gm/ID ----
LCOM = float(sys.argv[1]) if len(sys.argv) > 1 else 1e-6
VF = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3          # 접힘 노드 목표(VB3 복제 source) -- 측정 매개변수
TAG = sys.argv[3] if len(sys.argv) > 3 else "R1"
I = dict(M101=20e-6, M102=10e-6, M103=10e-6, M104=20e-6, M105=20e-6, M106=10e-6, M107=10e-6, M108=10e-6, M109=10e-6,
         M201=10e-6, M203=10e-6, M204=10e-6, M202=10e-6, M301=100e-6, M302=100e-6)
G = dict(M101=10, M102=15, M103=15, M104=10, M105=10, M106=12, M107=12, M108=10, M109=10, M201=12, M203=10, M204=10,
         M202=10, M301=12, M302=10)
if len(sys.argv) > 6:                                            # 측정 매개변수 덮어쓰기 {"G": {...}, "I": {...}}
    _ov = json.loads(sys.argv[6]); G.update(_ov.get("G", {})); I.update(_ov.get("I", {}))
kind ={d["name"]: d["kind"] for d in topo["netlist"]}
W = {}
for m in I:
    W[m], _ = w_for(kind[m], LCOM, G[m], I[m])
W["M204"] = W["M203"]; W["M109"] = W["M108"]; W["M103"] = W["M102"]; W["M105"] = W["M104"]; W["M107"] = W["M106"]
FW = 1e-6                                                        # finger 폭(측정 매개변수) -> m = W / FW
L = ["* icmr4 nmcnr R-design servo sweep", f".temp {meta['temp_c_from_log']}", ".option gmin=1e-15 reltol=1e-5 abstol=1e-14 vntol=1e-8 itl1=500 itl2=500"]
for rel in INC:
    L.append(f'.include "{(PDK / rel).as_posix()}"')
N = lambda n: "0" if n == "vss" else n
L += [f"Vvdd vdd 0 DC {VDD - VSS}", f"Vagnd agnd 0 DC {AGND - VSS}"]


PAIR_BULK_SRC = len(sys.argv) > 6 and bool(json.loads(sys.argv[6]).get("pair_bulk_src"))   # 정보용 측정: 입력쌍 bulk = 공통 source(topology 밖 선언)


def mos(name, d, g, s, k, w, l):
    b = "vdd" if k == "pmos" else "0"
    if PAIR_BULK_SRC and name in ("M102", "M103"):
        b = s
    mm = max(1, round(w / FW))
    return f"X{name} {N(d)} {N(g)} {N(s)} {b} {CELL[k]} l={l:.6g} w={FW:.6g} m={mm}"


for dv in topo["netlist"]:
    m = dv["name"]
    L.append(mos(m, dv["drain"], dv["gate"], dv["source"], kind[m], W[m], LCOM))
# 바이어스 복제(측정용 이상 바이어스 망 -- topology 밖, VB 넷만 구동)
L += [mos("RB1", "VB1", "VB1", "vdd", "pmos", W["M101"], LCOM), f"IRB1 VB1 0 DC {I['M101']}",
      mos("RB2", "VB2", "VB2", "vss", "nmos", W["M104"], LCOM), f"IRB2 vdd VB2 DC {I['M104']}",
      mos("RB3", "VB3", "VB3", "vf3", "nmos", W["M106"], LCOM), f"IRB3 vdd VB3 DC {I['M106']}", f"VF3 vf3 0 DC {VF}",
      mos("RB4", "VB4", "VB4", "vdd", "pmos", W["M202"], LCOM), f"IRB4 VB4 0 DC {I['M202']}",
      mos("RB5", "VB5", "VB5", "vdd", "pmos", W["M302"] / 10, LCOM), f"IRB5 VB5 0 DC {I['M302'] / 10}"]
# 수동소자(값: CL·RL = spec 선언, Cm1·Cm2·Rm = engine 값이라 DC 무관 -- 측정 매개변수 1 pF·1 pF·1/gm3 근사 10 kΩ)
pv = {"CL": spec["element_values"]["CL"]["value_farad"], "RL": spec["element_values"]["RL"]["value_ohm"], "Cm1": 1e-12, "Cm2": 1e-12, "Rm": 1e4}
for p in topo["passive_elements"]:
    a, b = p["terminals"]
    L.append(f"{'R' if p['name'].startswith('R') else 'C'}{p['name']} {N(a)} {N(b)} {pv[p['name']]:.6g}")
X0 = float(sys.argv[4]) if len(sys.argv) > 4 else AGND                # 기준점 입력 공통모드(기본 = agnd, SP-2 권고안)
VOUT0 = float(sys.argv[5]) if len(sys.argv) > 5 else AGND             # 기준점 출력(servo 묶음, 기본 = agnd)
ch, cc = 1e12, 1.0
L += ["Vsw dn 0 DC 0", f"Vp0 cp 0 DC {X0}", "Ep dcs_p cp dn 0 1", f"Ldc_p dcs_p Vin_p {ch}", f"Cac_p Vin_p acs_p {cc}", "Vac_p acs_p 0 DC 0 AC 0.5",
      "Efb fbs 0 Vout 0 1", f"Vofs fbs fbm DC {VOUT0 - X0}", "En fbd fbm dn 0 1", f"Lfb fbd Vin_n {ch}", f"Cac_n Vin_n acs_n {cc}", "Vac_n acs_n 0 DC 0 AC -0.5"]
lo, hi, step = VSS, VDD, 0.01
grid = [round(-X0 + k * step, 6) for k in range(0, int(round((hi - lo) / step)) + 1)]
mosn = [d["name"] for d in topo["netlist"]]
C = [".control", "set noaskquit", "option numdgt=10"]
for j, dx in enumerate(grid):
    C += [f"alter vsw dc = {dx:.9g}", "op", f"echo BEGIN {j}", "print v(Vin_p) v(Vin_n) v(Vout) v(NodeTail) v(NodeF1) v(NodeF2) v(NodeM2) v(NodeS2)"]
    for m in mosn:
        for q in ("id", "vds", "vdsat", "gm"):
            C.append(f"print @m.x{m.lower()}.m{CELL[kind[m]]}[{q}]")
    C += ["ac lin 1 0.01 0.01", "print vm(Vout)", "echo END", "destroy all"]
C += ["quit", ".endc", ".end"]
cir = TMP / f"nmcnr_{TAG}.cir"
cir.write_bytes(("\n".join(L + C) + "\n").encode("utf-8"))
pr = subprocess.run([NG, "-b", str(cir)], capture_output=True, text=True, cwd=str(TMP))
(TMP / f"nmcnr_{TAG}.log").write_bytes((pr.stdout + "\n--stderr--\n" + pr.stderr).encode("utf-8"))
res, cur = {}, None
for ln in pr.stdout.splitlines():
    s = ln.strip()
    if s.startswith("BEGIN "):
        cur = res.setdefault(int(s.split()[1]), {}); continue
    if s == "END":
        cur = None; continue
    if cur is None:
        continue
    mm = re.match(r"^(@m\.x(\w+)\.\S+\[(\w+)\]|v\(([^)]+)\)|vm\(([^)]+)\))\s*=\s*([-+0-9.eE]+)", s)
    if mm:
        val = float(mm.group(6))
        if mm.group(2):
            cur.setdefault("dev", {}).setdefault(mm.group(2).upper(), {})[mm.group(3)] = val
        elif mm.group(4):
            cur["v_" + mm.group(4).lower()] = val
        elif mm.group(5):
            cur["vm"] = val
app({"case": "design", "tag": TAG, "L": LCOM, "VF": VF, "X0": X0, "VOUT0": VOUT0, "I": I, "gmid": G, "W": W, "fw": FW, "netlist": str(cir),
     "rc": pr.returncode, "model_sha_ok": shaok, "passives": pv, "n_points": len(grid), "n_parsed": len(res)})
for j, dx in enumerate(grid):
    s = res.get(j, {})
    rec = {"case": "point", "tag": TAG, "x": X0 + dx, **{k: v for k, v in s.items() if k != "dev"}}
    if s.get("vm", 0) > 0:
        rec["gain_db"] = 20 * math.log10(s["vm"])
    dev = s.get("dev") or {}
    sl = {m: abs(d.get("vds", 0)) - abs(d.get("vdsat", 0)) for m, d in dev.items()}
    if sl:
        mn = min(sl, key=sl.get)
        rec["min_slack"] = [mn, sl[mn]]
        rec["sat_fail"] = sorted(m for m, v in sl.items() if v < 0)
        rec["id"] = {m: d.get("id") for m, d in dev.items()}
    app(rec)
print("rc", pr.returncode, "parsed", len(res), "of", len(grid))
