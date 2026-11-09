# O-200 Q5 측정 4 보강 -- find_front 평가 행 가운데 봉인 7 띠 안(0 <= VDS − VDsat < tol_VDsat)·위반(< 0) 행과, 대조로 띠 밖 근처 행 일부를
# ngspice-46 단일 소자(전압원 바이어스 = 엔진 점의 VGS·VDS·VSB, 소스 접지, 바디 −VSB(nfet)/+VSB(pfet); 기하 = LUT 생성기 DUT 줄과 같은 w=5u
# ad=2.5p as=2.5p pd=7u ps=7u, m=1 -- 엔진 w_key 1000 슬라이스 폭)로 돌려 @m[vdsat] 와 VDS − @m[vdsat] 부호를 잰다. 모델 include = LUT 생성기 메타
# model_files_sha256 와 같은 세 파일(pm3·mismatch.corner·lod) + 27 °C. 출력: TEMP 고유 경로(넷리스트·로그), 결과 q5_spice_band.jsonl(행마다 append).
import json, pathlib, re, subprocess, sys, hashlib
HERE = pathlib.Path(__file__).parent
TMP = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/q5_1bd9a6b5/spice"); TMP.mkdir(parents=True, exist_ok=True)
NG = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
PDK = pathlib.Path(r"C:/pdk/sky130_fd_pr")
INC = {"nmos": ["cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice", "cells/nfet_01v8/sky130_fd_pr__nfet_01v8__mismatch.corner.spice"],
       "pmos": ["models/parameters/lod.spice", "cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.pm3.spice", "cells/pfet_01v8/sky130_fd_pr__pfet_01v8__mismatch.corner.spice"]}
CELL = {"nmos": "sky130_fd_pr__nfet_01v8", "pmos": "sky130_fd_pr__pfet_01v8"}
rows = [json.loads(l) for l in (HERE / "q5_engine_rows.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
rows = [r for r in rows if "slack0" in r and r.get("tol") is not None]
sel, seen = [], set()
def key(r):
    return (r["circuit"], r["device"], round(r["L"] * 1e9, 3), round(r["vgs"], 7), round(r["vds"], 7), round(r["vsb"], 7))
band = [r for r in rows if r["band"] or r["sat_violate"]]
near = sorted([r for r in rows if not r["band"] and not r["sat_violate"]], key=lambda r: r["slack0"] - r["tol"])[:40]   # 띠 바로 위 대조
for grp, rs in (("band_or_violate", band), ("control_above_band", near)):
    for r in rs:
        k = key(r)
        if k in seen:
            continue
        seen.add(k); sel.append((grp, r))
print("points", len(sel), "band/viol", sum(g == "band_or_violate" for g, _ in sel), flush=True)
sha = {p: hashlib.sha256((PDK / p).read_bytes()).hexdigest() for k in INC for p in INC[k]}
OUT = HERE / "q5_spice_band.jsonl"; OUT.write_text("", encoding="utf-8")
CH = 60
for c0 in range(0, len(sel), CH):
    chunk = sel[c0:c0 + CH]
    L = ["* q5 band single-device", ".temp 27", ".option gmin=1e-15 reltol=1e-4 abstol=1e-14 vntol=1e-7"]
    for p in sorted({p for _, r in chunk for p in INC[r["kind"]]} | set(INC["pmos"]) | set(INC["nmos"])):
        L.append(f'.include "{(PDK / p).as_posix()}"')
    for i, (_, r) in enumerate(chunk):
        pol = 1 if r["kind"] == "nmos" else -1; bs = -1 if pol == 1 else 1
        L += [f"vg{i} g{i} 0 dc {pol * r['vgs']:.12g}", f"vd{i} d{i} 0 dc {pol * r['vds']:.12g}", f"vb{i} b{i} 0 dc {bs * r['vsb']:.12g}",
              f"xq{i} d{i} g{i} 0 b{i} {CELL[r['kind']]} l={r['L']:.10g} w=5u m=1 ad=2.5p as=2.5p pd=7u ps=7u"]
    L += [".control", "set noaskquit", "option numdgt=10", "op"]
    for i, (_, r) in enumerate(chunk):
        L.append(f"echo BEGIN {i}")
        for q in ("id", "vdsat", "vds", "vgs", "vbs", "vth"):
            L.append(f"print @m.xq{i}.m{CELL[r['kind']]}[{q}]")
        L.append("echo END")
    L += ["quit", ".endc", ".end"]
    cir = TMP / f"band_{c0:04d}.cir"; cir.write_bytes(("\n".join(L) + "\n").encode("utf-8"))
    pr = subprocess.run([NG, "-b", str(cir)], capture_output=True, text=True, cwd=str(TMP), timeout=600)
    (TMP / f"band_{c0:04d}.log").write_bytes((pr.stdout + "\n--stderr--\n" + pr.stderr).encode("utf-8"))
    res, cur = {}, None
    for ln in pr.stdout.splitlines():
        s = ln.strip()
        if s.startswith("BEGIN "):
            cur = res.setdefault(int(s.split()[1]), {}); continue
        if s == "END":
            cur = None; continue
        m = re.match(r"^@m\.\S+\[(\w+)\]\s*=\s*([-+0-9.eE]+)", s)
        if m and cur is not None:
            cur[m.group(1)] = float(m.group(2))
    for i, (grp, r) in enumerate(chunk):
        s = res.get(i, {})
        rec = dict(group=grp, circuit=r["circuit"], device=r["device"], kind=r["kind"], L=r["L"], vgs=r["vgs"], vds=r["vds"], vsb=r["vsb"],
                   vdsat_eng=r["vdsat"], tol=r["tol"], slack_eng=r["slack0"], band=r["band"], viol=r["sat_violate"],
                   spice=s, rc=pr.returncode)
        if "vdsat" in s and "vds" in s:
            rec.update(slack_spice=s["vds"] - s["vdsat"], dvdsat_mV=1e3 * (r["vdsat"] - s["vdsat"]), dvdsat_over_tol=abs(r["vdsat"] - s["vdsat"]) / r["tol"],
                       spice_sat=s["vds"] - s["vdsat"] >= 0, vds_check=abs(s["vds"] - r["vds"]))
        with open(OUT, "ab") as fh:
            fh.write((json.dumps(rec) + "\n").encode("utf-8"))
    print("chunk", c0, "rc", pr.returncode, "parsed", len(res), flush=True)
(HERE / "q5_spice_band_meta.json").write_bytes(json.dumps(dict(n=len(sel), model_sha256=sha)).encode("utf-8"))
print("done")
