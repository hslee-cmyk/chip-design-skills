"""판정자 독립 C-10 확인. 슬라이스 meta geometry 포함, @m[id]와 i(vds)를 함께 읽고 showmod로 고른 bin을 적는다.
source_modes(측정 스크립트)와 달리 geometry를 넣은 넷리스트와 뺀 넷리스트를 모두 돈다."""
import json, os, re, subprocess, sys
sys.path.insert(0, "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/op7a-iso/.ai/verification/20261104-op7a/scripts")
import bin_rule_lib as B
import numpy
W = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/work"
OUTDIR = W + "/hand"
plan = json.load(open(W + "/plan.json", encoding="utf-8"))
kinds = {k["name"]: k for k in plan["kinds"]}
g = plan["lut_grid_um"] * 1e-6
HSA = "set ngbehavior=hsa\n"
res_path = W + "/hand_c10.jsonl"
open(res_path, "w").close()
os.makedirs(OUTDIR, exist_ok=True)

def geom(text):
    m = re.search(r"ad=as=([0-9.eE+-]+)p pd=ps=([0-9.eE+-]+)u", text)
    if not m:
        raise SystemExit("geometry parse " + text)
    return float(m.group(1)), float(m.group(2))

def run(k, pr, w, mode, use_geom):
    name = f"{pr['kind']}_{pr['l_m']:.3e}_{mode}_{int(use_geom)}"
    d = f"{OUTDIR}/{name}"
    os.makedirs(d + "/cwd", exist_ok=True); os.makedirs(d + "/home", exist_ok=True)
    if mode == "hsa":
        open(d + "/cwd/.spiceinit", "w", newline="").write(HSA)
    sim = pr["sim"]; sub = k["subckt"]
    ad, pd = geom(pr["_geometry"])
    g_txt = f" ad={ad:g}p as={ad:g}p pd={pd:g}u ps={pd:g}u" if use_geom else ""
    inst = f"m.xp.m{sub}"
    lines = [f"* hand", *k["includes"], f".temp {sim['temp_c']}", f"vgs g 0 dc {sim['vgs']}", f"vds d 0 dc {sim['vds']}",
             f"vsrc s 0 dc {sim['vs']}", f"vb b 0 dc {sim['vb']}",
             f"xp d g s b {sub} l={pr['l_m']*1e6:g}u w={w*1e6:g}u{g_txt} m={sim['mult']:g}",
             ".control", "op", "print i(vds)", f"print @{inst}[id]", "echo SHOWMOD p0", f"showmod {inst} : lmin lmax wmin wmax", "quit", ".endc", ".end"]
    open(d + "/cwd/s.cir", "w", newline="\n").write("\n".join(lines) + "\n")
    env = B.isolated_env(os.environ, d + "/home")
    p = subprocess.run([plan["ngspice_exe"], "-b", "s.cir"], cwd=d + "/cwd", env=env, capture_output=True)
    t = p.stdout.decode(errors="replace")
    iv = re.search(r"i\(vds\)\s*=\s*([0-9.eE+-]+)", t)
    idv = re.search(r"\[id\]\s*=\s*([0-9.eE+-]+)", t)
    b = B.parse_probe_log(t, k["bins"], g)["p0"]
    return {"rc": p.returncode, "i_vds": float(iv.group(1)) if iv else None, "id": float(idv.group(1)) if idv else None, "bin": b}

for pr in plan["source"]["probes"]:
    k = kinds[pr["kind"]]
    w = pr["_w_m"]
    lut = pr["lut"]
    with numpy.load(lut["npz"]) as z:
        lut_id = float(z["ID"][tuple(lut["index"])])
    row = {"kind": pr["kind"], "l_m": pr["l_m"], "w_m": w, "slice": pr["_slice"], "lut_id": lut_id}
    for mode in ("default", "hsa"):
        for ug in (1, 0):
            row[f"{mode}_{'geom' if ug else 'nogeom'}"] = run(k, pr, w, mode, bool(ug))
    with open(res_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
print("done")
