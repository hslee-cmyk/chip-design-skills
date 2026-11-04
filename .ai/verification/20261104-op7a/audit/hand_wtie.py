"""원인 규명: W 동률 점(L = bin 안쪽)에서는 두 모드 값이 갈리는가. 슬라이스 meta geometry 포함, @m[id] 15자리.
슬라이스마다 L 축의 bin 안쪽 앵커 하나(meta L 축에서 W 동률만 되는 첫 점). LUT ID는 슬라이스마다 놓는다."""
import json, os, re, subprocess, sys
sys.path.insert(0, "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/op7a-iso/.ai/verification/20261104-op7a/scripts")
import bin_rule_lib as B
import numpy
W = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/work"
R = "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2"
plan = json.load(open(W + "/plan.json", encoding="utf-8"))
kinds = {k["name"]: k for k in plan["kinds"]}
g = plan["lut_grid_um"] * 1e-6
man = json.load(open(R + "/manifest.json", encoding="utf-8"))
res = open(W + "/hand_wtie.jsonl", "w", encoding="utf-8")
def run(k, kname, l, w, geo, pol, vg, vd, mode):
    d = f"{W}/hand_w/{kname}_{w:.3e}_{mode}"
    os.makedirs(d + "/cwd", exist_ok=True); os.makedirs(d + "/home", exist_ok=True)
    if mode == "hsa":
        open(d + "/cwd/.spiceinit", "w", newline="").write("set ngbehavior=hsa\n")
    sub = k["subckt"]; inst = f"m.xp.m{sub}"
    lines = ["* w", *k["includes"], ".temp 27.0".replace("27.0", str(TEMP)), f"vgs g 0 dc {pol*vg}", f"vds d 0 dc {pol*vd}", "vsrc s 0 dc 0", "vb b 0 dc 0",
             f"xp d g s b {sub} l={l*1e6:g}u w={w*1e6:g}u {geo} m=1", ".control", "set numdgt=15", "op", f"print @{inst}[id]",
             "echo SHOWMOD p0", f"showmod {inst} : lmin lmax wmin wmax", "quit", ".endc", ".end"]
    open(d + "/cwd/s.cir", "w", newline="\n").write("\n".join(lines) + "\n")
    p = subprocess.run([plan["ngspice_exe"], "-b", "s.cir"], cwd=d + "/cwd", env=B.isolated_env(os.environ, d + "/home"), capture_output=True)
    t = p.stdout.decode(errors="replace")
    return float(re.search(r"\[id\]\s*=\s*([0-9.eE+-]+)", t).group(1)), B.parse_probe_log(t, k["bins"], g)["p0"]
for s in man["slices"]:
    with numpy.load(f"{R}/{s['file']}") as z:
        m = json.loads(str(z["meta_json"].item() if z["meta_json"].shape == () else z["meta_json"].tolist()))
        k = kinds[s["device"]]; w = m["w_m"]; TEMP = m["temp_c_from_log"]
        ax = m["axes"]["L_m"]
        ls = [i for i, l in enumerate(ax) if B.tie_axes(l, w, k["bins"], g) == ("W",)]
        if not ls:
            res.write(json.dumps({"file": s["file"], "skip": "no W-only tie"}) + "\n"); continue
        il = ls[0]; l = ax[il]
        ig = len(m["axes"]["VGS_V"]) - 1; idd = len(m["axes"]["VDS_V"]) - 1
        lut = float(z["ID"][il, ig, idd, 0])
    gm = re.search(r"ad=as=([0-9.eE+-]+)p pd=ps=([0-9.eE+-]+)u", m["geometry"])
    geo = f"ad={gm.group(1)}p as={gm.group(1)}p pd={gm.group(2)}u ps={gm.group(2)}u"
    pol = -1 if s["device"].startswith("pfet") else 1
    vg, vd = m["axes"]["VGS_V"][ig], m["axes"]["VDS_V"][idd]
    a, ba = run(k, s["device"], l, w, geo, pol, vg, vd, "default")
    b, bb = run(k, s["device"], l, w, geo, pol, vg, vd, "hsa")
    res.write(json.dumps({"file": s["file"], "l": l, "w": w, "lut": lut, "default": a, "hsa": b, "bin_d": ba, "bin_h": bb,
                          "rel_modes": abs(abs(a) - abs(b)) / abs(a), "lut_vs_d": abs(lut - abs(a)) / lut, "lut_vs_h": abs(lut - abs(b)) / lut,
                          "identify": B.identify_mode(lut, a, b)}) + "\n")
    res.flush()
res.close()
print("done")
