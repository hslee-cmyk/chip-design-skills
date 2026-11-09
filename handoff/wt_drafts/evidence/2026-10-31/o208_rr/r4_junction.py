# R4 대안 (나′) 실측 -- 비채널 누설을 '접합 몫(PDK BSIM4 접합 파라미터 + 확산 기하에서 닫힌 식)'과 'GIDL 몫(모델 agidl 계열)'으로 나눌 수 있는가.
# 단일 소자(LUT DUT 기하 w=5u ad=as=2.5p pd=ps=7u), |VDS| = 1.8 V, VSB 0, VGS 0 / 끄는 방향 −0.2·−0.4·−0.6 V, gmin 1e-18, tt 27 C.
#  (1) ngspice 단자 i(vd) 와 채널 @m[id]: 원 모델 / altermod agidl = agisl = 0(GIDL·GISL 끔)  -> 접합 몫 = GIDL 끈 단자 − 채널
#  (2) showmod 로 그 인스턴스가 쓴 bin 의 접합 파라미터(jsd·jswd·jswgd·njd·permod 등)를 읽어 닫힌 식 Isbd 와 대조
# 모델 = LUT 메타 sha 대조 파일. 결과 = r4_junction.txt(덮어씀), 넷리스트·로그 TEMP 고유 경로.
import json, pathlib, hashlib, subprocess, re, math
import numpy as np
HERE = pathlib.Path(__file__).parent
TMP = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/o208rr_5b2d"); TMP.mkdir(parents=True, exist_ok=True)
NG = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
PDK = pathlib.Path(r"C:/pdk/sky130_fd_pr")
meta = json.loads(str(np.load(r"C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz", allow_pickle=True)["meta_json"]))
INC = []
for dev, files in meta["model_files_sha256"].items():
    for rel, sha in files.items():
        if rel.endswith(".csv"):
            continue
        assert hashlib.sha256((PDK / rel).read_bytes()).hexdigest() == sha, rel
        INC.append(rel) if rel not in INC else None
DEV = [("n015", "nfet_01v8", 0.15, 1), ("n1", "nfet_01v8", 1.0, 1), ("p015", "pfet_01v8", 0.15, -1), ("p1", "pfet_01v8", 1.0, -1)]
KEYS = ("agidl", "agisl", "jsd", "jss", "jswd", "jsws", "jswgd", "jswgs", "njd", "njs", "permod", "tnom", "xtid", "xtis", "bvd", "ijthdrev", "weff")
VGS = (0.0, -0.2, -0.4, -0.6)


def netlist(gidl_off):
    L = ["* o208 R4 junction split", f".temp {meta['temp_c_from_log']}", ".options gmin=1e-18"]
    L += [f'.include "{(PDK / r).as_posix()}"' for r in INC]
    for tag, cell, l, p in DEV:
        L += [f"vg{tag} g{tag} 0 dc 0", f"vd{tag} d{tag} 0 dc {p * 1.8}",
              f"x{tag} d{tag} g{tag} 0 0 sky130_fd_pr__{cell} l={l}u w=5u ad=2.5p as=2.5p pd=7u ps=7u"]
    L += [".control"]
    if gidl_off:
        for tag, cell, l, p in DEV:
            L += [f"altermod @m.x{tag}.msky130_fd_pr__{cell}[agidl] = 0", f"altermod @m.x{tag}.msky130_fd_pr__{cell}[agisl] = 0"]
    for v in VGS:
        for tag, cell, l, p in DEV:
            L.append(f"alter vg{tag} dc = {p * v}")
        L += ["op", f"echo VGS {v}"]
        for tag, cell, l, p in DEV:
            L += [f"echo DEV {tag}", f"print i(vd{tag})", f"print @m.x{tag}.msky130_fd_pr__{cell}[id]"]
    for tag, cell, l, p in DEV:
        L += [f"echo SHOW {tag}", f"showmod m.x{tag}.msky130_fd_pr__{cell} : " + " ".join(KEYS)]
    L += ["quit", ".endc", ".end"]
    return "\n".join(L) + "\n"


def run(tag, off):
    cir = TMP / f"r4j_{tag}.cir"; cir.write_bytes(netlist(off).encode("utf-8"))
    pr = subprocess.run([NG, "-b", str(cir)], capture_output=True, text=True, cwd=str(TMP))
    (TMP / f"r4j_{tag}.log").write_bytes((pr.stdout + "\n--stderr--\n" + pr.stderr).encode("utf-8"))
    res, show, v, d, sd = {}, {}, None, None, None
    for ln in pr.stdout.splitlines():
        s = ln.strip().split()
        if not s:
            continue
        if s[0] == "VGS":
            v = float(s[1]); sd = None; continue
        if s[0] == "DEV":
            d = s[1]; continue
        if s[0] == "SHOW":
            sd = s[1]; show[sd] = {}; continue
        if sd and len(s) == 2 and s[0] in KEYS:
            try:
                show[sd][s[0]] = float(s[1])
            except ValueError:
                show[sd][s[0]] = s[1]
            continue
        m = re.match(r"^(i\(vd\w+\)|@m\.\S+\[id\])\s*=\s*([-+0-9.eE]+)", ln.strip())
        if m and d:
            res.setdefault((v, d), {})["term" if m.group(1).startswith("i(") else "chan"] = float(m.group(2))
    return pr.returncode, res, show


rc0, base, show = run("base", False)
rc1, off, _ = run("gidl_off", True)
T = [f"# R4 접합·GIDL 분리 (rc {rc0}/{rc1}, gmin 1e-18, tt {meta['temp_c_from_log']} C, w 5 um, |VDS| 1.8 V, VSB 0)",
     "소자 | VGS(끄는 방향) | 채널 @m[id] | 단자(원 모델) | 단자(agidl=agisl=0) | 접합 몫 = (GIDL 끔 단자 − 채널) | GIDL 몫 = 원 − 끔 | 닫힌 식 Isbd(접합 파라미터)"]
Vt = 1.380649e-23 * (273.15 + meta["temp_c_from_log"]) / 1.602176634e-19
for tag, cell, l, p in DEV:
    sp = show.get(tag, {})
    try:
        weff = sp.get("weff") if isinstance(sp.get("weff"), float) else 5e-6
        perim = 7e-6 - (weff if sp.get("permod", 1) == 1 else 0.0)
        isbd = 2.5e-12 * sp["jsd"] + perim * sp["jswd"] + weff * sp["jswgd"]
        ij = isbd * (1 - math.exp(-1.8 / (sp["njd"] * Vt)))
    except Exception as e:  # noqa: BLE001 -- 측정 기록
        ij = None
    for v in VGS:
        b, o = base.get((v, tag), {}), off.get((v, tag), {})
        if "term" not in b or "term" not in o:
            T.append(f"{tag} | {v} | 파싱 실패 {b} {o}"); continue
        ti, to, ch = -b["term"] * p, -o["term"] * p, b["chan"]
        T.append(f"{tag} ({cell}, L {l} um) | {v} | {ch:.3e} | {ti:.3e} | {to:.3e} | {to - ch:.3e} | {ti - to:.3e} | {ij if ij is None else f'{ij:.3e}'}")
T.append("")
T.append("showmod 접합 파라미터: " + json.dumps(show, ensure_ascii=False))
T.append("닫힌 식 = BSIM4 역바이어스 접합 Isbd = AD·JSD + PD′·JSWD + Weff·JSWGD (permod = 1이면 PD′ = PD − Weff), × (1 − exp(−|V|/(NJD·Vt))); 온도 보정(XTID, TNOM ≠ TEMP) 미적용 -- 차이가 나면 그 몫")
(HERE / "r4_junction.txt").write_bytes(("\n".join(T) + "\n").encode("utf-8"))
print("\n".join(T))
