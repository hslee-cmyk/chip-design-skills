# O-206 실측 (oracle 쪽) -- o206_seal_dump.jsonl 의 봉인점(W·L·바이어스·수동소자 값)으로 ngspice-46 넷리스트를 만들고, 측정 구성 T
# (oracle_netlist free 와 같은 꼴: 비반전 입력 = DC choke + AC 결합, 반전 입력 = 출력 단위 되먹임 Efb + 오프셋 Vofs + choke -- 출력이 봉인 V_out 에 묶임)
# 에서 입력 공통모드 Δ 를 훑는다(oracle_swing 의 'Vofs 에서 Δ 빼고 Vdc 에 Δ 더함'과 같은 이동: 여기서는 한 전원 Vsw 가 두 쪽을 함께 민다).
# 점마다 .op(소자 id·vds·vdsat·gm) + .ac 1점(f = fstart, 차동 AC ±0.5 = oracle legacy_testbench 값) -> 개루프 차동 이득.
# 기하 = 엔진 레이아웃 전 규칙(finger_w = 슬라이스 w_m, m = W/w_m, ad/as/pd/ps = LUT 규칙 -- JunctionSource.pre_layout_geometry 값 그대로).
# 모델 = LUT 메타 model_files_sha256 와 sha 대조한 파일. 테스트벤치 값 = tools/spice_oracle/legacy_testbench.json(choke·결합 C·options·fstart·AC 크기).
# 결과: o206_spice_sweep.jsonl(점마다 append), 넷리스트·로그 = TEMP 고유 경로.
import json, pathlib, re, subprocess, sys, hashlib, math
import numpy as np
HERE = pathlib.Path(__file__).parent
TMP = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/o206_7c3e91/spice"); TMP.mkdir(parents=True, exist_ok=True)
NG = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
PDK = pathlib.Path(r"C:/pdk/sky130_fd_pr")
TB = json.loads(pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/tools/spice_oracle/legacy_testbench.json").read_text(encoding="utf-8"))
LUTNPZ = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz")
CELL = {"nmos": "sky130_fd_pr__nfet_01v8", "pmos": "sky130_fd_pr__pfet_01v8"}
meta = json.loads(str(np.load(LUTNPZ, allow_pickle=True)["meta_json"]))
INC = []
shaok = {}
for dev, files in meta["model_files_sha256"].items():
    for rel, sha in files.items():
        if rel.endswith(".csv"):
            continue
        got = hashlib.sha256((PDK / rel).read_bytes()).hexdigest()
        shaok[rel] = (got == sha)
        if rel not in INC:
            INC.append(rel)
assert all(shaok.values()), shaok
name = sys.argv[1]
step = float(sys.argv[2])
dump = [json.loads(l) for l in (HERE / "o206_seal_dump.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
d = [r for r in dump if r.get("circuit") == name and "devices" in r][-1]
V0 = d["nodes"]; inp, inn, out = d["inp"], d["inn"], d["out"]
rails = d["rails"]
gnd = min(rails, key=lambda n: rails[n])
N = lambda n: "0" if n == gnd else n
L = [f"* o206 {name} T", f".temp {meta['temp_c_from_log']}"]
L.append(".option " + " ".join(f"{k}={v}" for k, v in TB["options"].items()))
for rel in INC:
    L.append(f'.include "{(PDK / rel).as_posix()}"')
for n, v in rails.items():
    if n != gnd:
        L.append(f"Vrail_{n} {n} 0 DC {v - rails[gnd]:.12g}")
gates = sorted({dv["pins"]["g"] for dv in d["devices"].values()})
for g in gates:
    if g in d["ss_ground"] and g not in rails:
        L.append(f"Vbias_{g} {g} 0 DC {V0[g] - rails[gnd]:.12g}")
mos = sorted(d["devices"])
for m in mos:
    dv = d["devices"][m]; geo = dv["geometry"]; p = dv["pins"]
    L.append(f"X{m} {N(p['d'])} {N(p['g'])} {N(p['s'])} {N(dv['bulk'])} {CELL[dv['kind']]} l={dv['L']:.10g} w={geo['finger_w_m']:.10g} m={geo['m']:.10g} "
             f"ad={geo['ad_m2']:.10g} as={geo['as_m2']:.10g} pd={geo['pd_m']:.10g} ps={geo['ps_m']:.10g}")
for pn, pv in d["passives"].items():
    a, b = list(pv["pins"].values())
    L.append(f"{'R' if pv['kind'] == 'resistor' else 'C'}{pn} {N(a)} {N(b)} {pv['value']:.12g}")
ch, cc = TB["dc_choke_H"], TB["ac_couple_F"]
vg = rails[gnd]
L += ["Vsw dn 0 DC 0", f"Vp0 cp 0 DC {V0[inp] - vg:.12g}", "Ep dcs_p cp dn 0 1", f"Ldc_p dcs_p {inp} {ch}", f"Cac_p {inp} acs_p {cc}",
      f"Vac_p acs_p 0 DC 0 AC {TB['ac']['input_p_ac']}",
      f"Efb fbs 0 {out} 0 1", f"Vofs fbs fbm DC {V0[out] - V0[inn]:.12g}", "En fbd fbm dn 0 1", f"Lfb fbd {inn} {ch}", f"Cac_n {inn} acs_n {cc}",
      f"Vac_n acs_n 0 DC 0 AC {TB['ac']['input_n_ac']}"]
ns = [f"v({n})={V0[n] - vg:.9g}" for n in V0 if n not in rails]
for i in range(0, len(ns), 8):
    L.append(".nodeset " + " ".join(ns[i:i + 8]))
lo, hi = min(rails.values()), max(rails.values())
k_lo = int(math.floor((V0[inp] - lo) / step + 1e-9)); k_hi = int(math.floor((hi - V0[inp]) / step + 1e-9))
grid = [-k * step for k in range(k_lo, 0, -1)] + [k * step for k in range(0, k_hi + 1)]
Q = ("id", "vds", "vgs", "vdsat", "gm", "gds")
f0 = TB["ac"]["fstart_hz"]
C = [".control", "set noaskquit", "option numdgt=10"]
for j, dx in enumerate(grid):
    C += [f"alter vsw dc = {dx:.9g}", "op", f"echo BEGIN {j}", f"print v({inp}) v({inn}) v({out})"]
    for m in mos:
        for q in Q:
            C.append(f"print @m.x{m.lower()}.m{CELL[d['devices'][m]['kind']]}[{q}]")
    C += [f"ac lin 1 {f0} {f0}", f"print vm({out}) vp({out})", "echo END", "destroy all"]
C += ["quit", ".endc", ".end"]
cir = TMP / f"{name}_T.cir"
cir.write_bytes(("\n".join(L + C) + "\n").encode("utf-8"))
pr = subprocess.run([NG, "-b", str(cir)], capture_output=True, text=True, cwd=str(TMP), timeout=3000)
(TMP / f"{name}_T.log").write_bytes((pr.stdout + "\n--stderr--\n" + pr.stderr).encode("utf-8"))
res, cur = {}, None
for ln in pr.stdout.splitlines():
    s = ln.strip()
    if s.startswith("BEGIN "):
        cur = res.setdefault(int(s.split()[1]), {}); continue
    if s == "END":
        cur = None; continue
    if cur is None:
        continue
    mm = re.match(r"^(@m\.x(\w+)\.\S+\[(\w+)\]|v\(([^)]+)\)|vm\(([^)]+)\)|vp\(([^)]+)\))\s*=\s*([-+0-9.eE]+)", s)
    if mm:
        val = float(mm.group(7))
        if mm.group(2):
            cur.setdefault("dev", {}).setdefault(mm.group(2).upper(), {})[mm.group(3)] = val
        elif mm.group(4):
            cur["v_" + mm.group(4)] = val
        elif mm.group(5):
            cur["vm"] = val
        elif mm.group(6):
            cur["vp"] = val
OUT = HERE / "o206_spice_sweep.jsonl"
for j, dx in enumerate(grid):
    s = res.get(j, {})
    rec = dict(circuit=name, dx=dx, x=V0[inp] + dx, rc=pr.returncode, **{k: v for k, v in s.items() if k != "dev"})
    if "vm" in s and s["vm"] > 0:
        rec["gain_db"] = 20 * math.log10(s["vm"])
    rec["dev"] = s.get("dev")
    with open(OUT, "ab") as fh:
        fh.write((json.dumps(rec) + "\n").encode("utf-8"))
(HERE / "o206_spice_meta.json").write_bytes(json.dumps(dict(circuit=name, model_sha_ok=shaok, includes=INC, temp=meta["temp_c_from_log"], tb=TB,
                                                             netlist=str(cir), rc=pr.returncode, n_points=len(grid), n_parsed=len(res))).encode("utf-8"))
print("rc", pr.returncode, "points", len(grid), "parsed", len(res), flush=True)
