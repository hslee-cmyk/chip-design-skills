# -*- coding: utf-8 -*-
"""CM 루프·β 루프 데이터·nodeset: R1~R5 에 없는 벤치의 옛/새 넷리스트 대조. OP-1 기준선의 CM 입력을 결합 LUT 로 옮겨 새 오라클로 돌려 넷리스트를 N4-3 과 같은 변환으로 대조하고 측정값 비교.
사용: a3_cm.py <iso_v> <work> <exe> <out.json>"""
import glob, hashlib, json, os, re, shutil, subprocess, sys

ISO, WORK, EXE, OUT = sys.argv[1:5]
O = os.path.join(ISO, "skills/analog-gmid-design/tools/spice_oracle")
FILES = os.path.join(ISO, ".ai/verification/20261016-op1-baseline/baseline/files")
sys.path.insert(0, os.path.join(ISO, ".ai/verification/20261104-op1b/scripts"))
import op1b_lib as L  # noqa: E402

DESC = os.path.join(O, "descriptors/sky130.oracle_descriptor.json")
dsha = hashlib.sha256(open(DESC, "rb").read().replace(b"\r\n", b"\n")).hexdigest()
R2 = "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz"
rsha = hashlib.sha256(open(R2, "rb").read()).hexdigest()
os.makedirs(WORK, exist_ok=True)
home = os.path.join(WORK, "home")
os.makedirs(home, exist_ok=True)
env = dict(os.environ)
env["HOME"] = env["USERPROFILE"] = home
for k in ("HOMEDRIVE", "HOMEPATH", "SPICE_USERINIT_DIR"):
    env.pop(k, None)
cands = []
for c in sorted(glob.glob(FILES + "/pytest/tmp/**/*.cmloop.cir", recursive=True)):
    d = os.path.dirname(c)
    ip = os.path.join(d, "t.input.json")
    if not os.path.exists(ip):
        continue
    cands.append((c, ip))
res = {"n_cm_baseline_cirs": len(cands), "cases": []}
seen = 0
for c, ip in cands:
    old = json.load(open(ip, encoding="utf-8"))
    kinds = {}
    for dv in old["devices"]:
        kinds[dv["kind"]] = "nfet_01v8" if dv["kind"] == "nmos" else "pfet_01v8"
    old2 = L.rewrite_lut_ref(old, R2)
    new, _ = L.convert_input(old2, lut_files=[{"path": R2, "sha256": rsha, "kinds": kinds}], descriptor={"path": DESC.replace("\\", "/"), "sha256": dsha}, adapter="ngspice", exe=EXE)
    name = f"c{seen}"
    d = os.path.join(WORK, name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    p = os.path.join(d, "t.input.json")
    json.dump(new, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    bias = "forced" if ".forced." in c else "free"
    r = subprocess.run([sys.executable, "-P", os.path.join(O, "oracle_run.py"), p, os.path.join(d, "o"), "--bias", bias], cwd=d, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    stem = os.path.basename(c)[:-len(".cmloop.cir")]
    rec = {"baseline": os.path.relpath(c, FILES).replace("\\", "/"), "rc": r.returncode}
    rej = glob.glob(os.path.join(d, "o", "*.reject.json"))
    if rej:
        j = json.load(open(rej[0], encoding="utf-8"))
        rec.update(reject=j["code"], detail=str(j["detail"])[:200])
    else:
        nc = os.path.join(d, "o", stem + ".cmloop", "bench.cir")
        if os.path.exists(nc):
            elems = lambda t: [ln for ln in t.splitlines() if ln and ln[0] not in "*." and not ln.startswith(("set ", "print", "let", "alter", "ac ", "op", "echo", "wrdata", "quit", "run"))]  # noqa: E731

            def conv(ln):
                toks = ln.split()
                if toks[0][0] in "Xx" and len(toks) > 6:
                    kv = dict(t.split("=", 1) for t in toks[6:])
                    return " ".join(toks[:6]) + " " + " ".join(sorted(f"{k}={float(v) / (1e-6 ** (2 if k in ('ad', 'as') else 1)) if k not in ('m', 'mult') else float(v):.10g}" for k, v in kv.items()) + [f"mult={float(kv['m']):.10g}"])
                return " ".join(format(float(t), ".10g") if re.fullmatch(r"[-+]?[0-9.]+(e[-+]?[0-9]+)?", t, re.I) else t for t in toks)

            def conv_new(ln):
                toks = ln.split()
                if toks[0][0] in "Xx" and len(toks) > 6:
                    kv = dict(t.split("=", 1) for t in toks[6:])
                    return " ".join(toks[:6]) + " " + " ".join(sorted(f"{k}={float(v):.10g}" for k, v in kv.items()))
                return " ".join(format(float(t), ".10g") if re.fullmatch(r"[-+]?[0-9.]+(e[-+]?[0-9]+)?", t, re.I) else t for t in toks)
            so = {conv(x) for x in elems(open(c, encoding="utf-8", errors="replace").read())}
            sn = {conv_new(x) for x in elems(open(nc, encoding="utf-8", errors="replace").read())}
            rec.update(only_old=sorted(so - sn)[:30], only_new=sorted(sn - so)[:30])
            base_sim = c[:-len(".cmloop.cir")] + ".sim.json"
            nsim = os.path.join(d, "o", stem + ".sim.json")
            if os.path.exists(base_sim) and os.path.exists(nsim):
                bs, ns = json.load(open(base_sim, encoding="utf-8")), json.load(open(nsim, encoding="utf-8"))
                bm, nm = (bs.get("cm_loop") or {}).get("measures") or {}, (ns.get("cm_loop") or {}).get("measures") or {}
                rec["cm_measures_diff"] = {k: (bm.get(k), nm.get(k)) for k in ("gain_dc", "ugf_hz", "pm_deg", "f3db_hz") if bm.get(k) != nm.get(k)}
                rec["cm_pm"] = {"raw": (ns.get("cm_loop") or {}).get("pm_deg_raw"), "pm_deg": (ns.get("cm_loop") or {}).get("pm_deg"), "pm_undefined": (ns.get("cm_loop") or {}).get("pm_undefined"), "weights": (ns.get("cm_loop") or {}).get("weights")}
                rec["cm_status_old_new"] = [bs.get("cm_loop", {}).get("ngspice_rc"), (ns.get("cm_loop") or {}).get("status", {}).get("rc")]
        else:
            rec["no_cm_bench"] = True
    res["cases"].append(rec)
    print(json.dumps(rec, ensure_ascii=False)[:1400])
    seen += 1
    if seen >= 3:
        break
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print("n_cm_baseline", len(cands))
