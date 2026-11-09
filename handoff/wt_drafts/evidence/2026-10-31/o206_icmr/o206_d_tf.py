# O-206 대안 (d) oracle 쪽 -- 점별 증분 DC 이득(DC 해석 양): servo 훑기(o206_spice_sweep.jsonl)가 찾은 각 점의 두 입력 DC 전압을 그대로
# 이상 전압원으로 고정한 개루프 넷리스트(같은 소자·기하·모델·options, 테스트벤치 servo 제거)에서 `.tf v(out) Vd`(차동 원 Vd, 공통 Vcm)로
# dV_out/dV_id 를 잰다(.tf = DC 해의 선형화 = '.dc 기울기'의 정확한 극한, O-43 D1 (d) 선례). 출력 DC 가 servo 점과 같은지(v(out) 차)도 기록.
# 결과: o206_d_tf.jsonl(점마다 append). 넷리스트·로그 = TEMP 고유 경로.
import json, pathlib, re, subprocess, math
HERE = pathlib.Path(__file__).parent
TMP = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/o206_7c3e91/spice")
NG = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
name = "nmcnr_amplifier"
src = (TMP / f"{name}_T.cir").read_text(encoding="utf-8").splitlines()
d = [json.loads(l) for l in (HERE / "o206_seal_dump.jsonl").read_text(encoding="utf-8").splitlines() if l.strip() and '"devices"' in l][-1]
inp, inn, out = d["inp"], d["inn"], d["out"]
body = []
for ln in src:
    if ln.startswith(".control"):
        break
    tok = ln.split()
    if tok and tok[0] in ("Vsw", "Vp0", "Ep", "Ldc_p", "Cac_p", "Vac_p", "Efb", "Vofs", "En", "Lfb", "Cac_n", "Vac_n"):
        continue
    if ln.startswith(".nodeset"):
        continue
    body.append(ln)
body += ["Vcm cm 0 DC 0", "Vd vd 0 DC 0", f"Edp {inp} cm vd 0 0.5", f"Edn cm {inn} vd 0 0.5"]
pts = [json.loads(l) for l in (HERE / "o206_spice_sweep.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
pts = [p for p in pts if p["circuit"] == name and ("v_" + inp.lower()) in p]
C = [".control", "set noaskquit", "option numdgt=12"]
for j, p in enumerate(pts):
    vp, vn = p["v_" + inp.lower()], p["v_" + inn.lower()]
    C += [f"alter vcm dc = {0.5 * (vp + vn):.12g}", f"alter vd dc = {vp - vn:.12g}", f"nodeset v({out})={p['v_' + out.lower()]:.10g}",
          "op", f"echo BEGIN {j}", f"print v({out})", f"tf v({out}) vd", "print all", "echo END", "destroy all"]
C += ["quit", ".endc", ".end"]
cir = TMP / f"{name}_d_tf.cir"
cir.write_bytes(("\n".join(body + C) + "\n").encode("utf-8"))
pr = subprocess.run([NG, "-b", str(cir)], capture_output=True, text=True, cwd=str(TMP), timeout=3000)
(TMP / f"{name}_d_tf.log").write_bytes((pr.stdout + "\n--stderr--\n" + pr.stderr).encode("utf-8"))
res, cur = {}, None
for ln in pr.stdout.splitlines():
    s = ln.strip()
    if s.startswith("BEGIN "):
        cur = res.setdefault(int(s.split()[1]), {}); continue
    if s == "END":
        cur = None; continue
    if cur is None:
        continue
    m = re.match(r"^(v\([^)]+\)|transfer_function)\s*=\s*([-+0-9.eE]+)", s)
    if m:
        cur[m.group(1)] = float(m.group(2))
OUT = HERE / "o206_d_tf.jsonl"
for j, p in enumerate(pts):
    r = res.get(j, {})
    tf = r.get("transfer_function")
    rec = dict(circuit=name, dx=p["dx"], x=p["x"], tf=tf, tf_db=None if not tf else 20 * math.log10(abs(tf)), ac_db=p.get("gain_db"),
               vout_ol=r.get(f"v({out.lower()})"), vout_servo=p.get("v_" + out.lower()), rc=pr.returncode)
    with open(OUT, "ab") as fh:
        fh.write((json.dumps(rec) + "\n").encode("utf-8"))
print("rc", pr.returncode, "points", len(pts), "parsed", len(res))
