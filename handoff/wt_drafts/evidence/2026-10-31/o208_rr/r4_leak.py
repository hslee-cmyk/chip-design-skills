# R4 실측 -- 엔진 평가 점(q5_engine_rows.jsonl, library 6회로 봉인 평가 2413 소자점)의 바이어스에서
# 단일 소자 ngspice .op 로 채널 전류 @m[id](LUT 열과 같은 양) 와 단자 드레인 전류 i(vd)(채널 + 접합 + GIDL) 를 같이 재고
# 비채널 몫 = 단자 − 채널 의 채널 대비 비를 낸다. 기하 = LUT DUT 규칙(w=5u, ad=as=2.5p, pd=ps=7u) m=1 --
# 엔진 레이아웃 전 규칙(finger_w = 5 um, m = W/w_m, 같은 ad/as/pd/ps)에서 채널·접합이 모두 m 배라 비는 W와 무관.
# 모델 = LUT 메타 model_files_sha256 와 sha 대조 파일. 두 판: (A) oracle options(legacy_testbench.json), (B) 같은 options + gmin=1e-18.
# 저장소 쓰기 0, 넷리스트·로그 = TEMP 고유 경로, 결과 = r4_leak.jsonl(케이스마다 append) + r4_leak.txt.
import json, pathlib, hashlib, subprocess, re, collections, math
import numpy as np
HERE = pathlib.Path(__file__).parent
TMP = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/o208rr_5b2d"); TMP.mkdir(parents=True, exist_ok=True)
NG = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
PDK = pathlib.Path(r"C:/pdk/sky130_fd_pr")
TB = json.loads(pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/tools/spice_oracle/legacy_testbench.json").read_text(encoding="utf-8"))
LUTNPZ = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz")
ROWS = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-31/o200_q5/q5_engine_rows.jsonl")
CELL = {"nmos": "nfet_01v8", "pmos": "pfet_01v8"}
meta = json.loads(str(np.load(LUTNPZ, allow_pickle=True)["meta_json"]))
INC, shaok = [], {}
for dev, files in meta["model_files_sha256"].items():
    for rel, sha in files.items():
        if rel.endswith(".csv"):
            continue
        shaok[rel] = hashlib.sha256((PDK / rel).read_bytes()).hexdigest() == sha
        if rel not in INC:
            INC.append(rel)
assert all(shaok.values()), shaok
rows = [json.loads(l) for l in ROWS.read_text(encoding="utf-8").splitlines() if l.strip()]
rows = [r for r in rows if r.get("current") and r["current"] > 0]
OUT = HERE / "r4_leak.jsonl"
if OUT.exists():
    OUT.unlink()


def run(tag, extra_opt):
    L = [f"* o208 R4 leak {tag}", f".temp {meta['temp_c_from_log']}"]
    opts = dict(TB["options"]); opts.update(extra_opt)
    L.append(".option " + " ".join(f"{k}={v}" for k, v in opts.items()))
    L += [f'.include "{(PDK / rel).as_posix()}"' for rel in INC]
    for k, r in enumerate(rows):
        p = 1 if r["kind"] == "nmos" else -1
        vs = p * r["vsb"]; vg = vs + p * r["vgs"]; vd = vs + p * r["vds"]
        L += [f"vs{k} s{k} 0 dc {vs:.12g}", f"vg{k} g{k} 0 dc {vg:.12g}", f"vd{k} d{k} 0 dc {vd:.12g}",
              f"x{k} d{k} g{k} s{k} 0 sky130_fd_pr__{CELL[r['kind']]} l={r['L'] * 1e6:.6g}u w=5u ad=2.5p as=2.5p pd=7u ps=7u"]
    L += [".control", "op"]
    for k, r in enumerate(rows):
        L += [f"echo R {k}", f"print i(vd{k})", f"print @m.x{k}.msky130_fd_pr__{CELL[r['kind']]}[id]"]
    L += ["quit", ".endc", ".end"]
    cir = TMP / f"r4_{tag}.cir"
    cir.write_bytes(("\n".join(L) + "\n").encode("utf-8"))
    pr = subprocess.run([NG, "-b", str(cir)], capture_output=True, text=True, cwd=str(TMP))
    (TMP / f"r4_{tag}.log").write_bytes((pr.stdout + "\n--stderr--\n" + pr.stderr).encode("utf-8"))
    res, cur = {}, None
    for ln in pr.stdout.splitlines():
        s = ln.strip()
        if s.startswith("R ") and s[2:].isdigit():
            cur = int(s[2:]); res[cur] = {}; continue
        m = re.match(r"^(i\(vd\d+\)|@m\.x\d+\.\S+\[id\])\s*=\s*([-+0-9.eE]+)", s)
        if m and cur is not None:
            res[cur]["term" if m.group(1).startswith("i(") else "chan"] = float(m.group(2))
    return pr.returncode, res


summary = {}
for tag, extra in (("A_oracle_opts", {}), ("B_gmin1e-18", {"gmin": "1e-18"})):
    rc, res = run(tag, extra)
    per = collections.defaultdict(list)
    for k, r in enumerate(rows):
        v = res.get(k, {})
        if "term" not in v or "chan" not in v:
            continue
        p = 1 if r["kind"] == "nmos" else -1
        term_in = -v["term"] * p          # 드레인으로 들어가는 전류(선언 방향, nmos +, pmos 는 부호 뒤집어 + 방향)
        chan = v["chan"]                  # BSIM @m[id]: nfet·pfet 모두 선언 방향 전도가 + (첫 실행에서 pfet 부호 뒤집기로 비 2.0 -- 정정)
        non = term_in - chan
        ratio = abs(non) / abs(chan) if chan else float("inf")
        rec = dict(tag=tag, circuit=r["circuit"], ev=r["ev"], device=r["device"], kind=r["kind"], L=r["L"], vgs=r["vgs"], vds=r["vds"], vsb=r["vsb"],
                   engine_current=r["current"], term_in_ref=term_in, chan_ref=chan, nonchan_ref=non, ratio=ratio)
        with open(OUT, "ab") as fh:
            fh.write((json.dumps(rec) + "\n").encode("utf-8"))
        per[r["circuit"]].append(rec)
    summary[tag] = (rc, per)

lut_rel_tol = None
try:
    lut_rel_tol = meta.get("lut_rel_tol")
except Exception:
    pass
T = [f"# R4 비채널 전류 / 채널 전류 (엔진 평가 점 바이어스, 단일 소자 sky130 tt {meta['temp_c_from_log']} C, 모델 sha 일치 {all(shaok.values())})",
     f"표본: {ROWS} 의 current > 0 소자점 {len(rows)}개, 회로 {sorted(set(r['circuit'] for r in rows))}",
     "판 A = oracle options " + json.dumps(TB['options']) + " / 판 B = 같은 options + gmin=1e-18", ""]
for tag, (rc, per) in summary.items():
    T.append(f"## {tag} (rc {rc})")
    T.append("회로 | 점 수 | 최소 채널 전류 A(기준폭 5 um) | 비 중앙 | 비 최대 (소자, kind, L um, VGS, VDS, VSB) | 비>1e-3 점 | 비>1e-2 점 | 비>1 점")
    for c, lst in sorted(per.items()):
        rs = sorted(x["ratio"] for x in lst)
        mx = max(lst, key=lambda x: x["ratio"])
        T.append(f"{c} | {len(lst)} | {min(abs(x['chan_ref']) for x in lst):.3e} | {rs[len(rs)//2]:.3e} | {mx['ratio']:.3e} ({mx['device']}, {mx['kind']}, {mx['L']*1e6:.3g}, {mx['vgs']:.3f}, {mx['vds']:.3f}, {mx['vsb']:.3f}) | "
                 f"{sum(r > 1e-3 for r in rs)} | {sum(r > 1e-2 for r in rs)} | {sum(r > 1 for r in rs)}")
    T.append("")
(HERE / "r4_leak.txt").write_bytes(("\n".join(T) + "\n").encode("utf-8"))
print("\n".join(T))
