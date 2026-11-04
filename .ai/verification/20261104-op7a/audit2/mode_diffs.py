"""A-2b 기록 전용. 슬라이스 동률 칸마다 두 모드의 id·gm·gds + C 열 상대차 |기본-대조|/|기본|. 합격 조건·문턱 없음.
조건 = 그 슬라이스 meta(w_m, nf, m, geometry, temp_c_from_log, sign_convention), 바이어스 = VGS·VDS 축 절댓값 최대, VS 첫 index(0).
C 열 = 결합 세트 생성기 규약: 게이트·드레인·소스·바디 AC 여기, CGG=-Im(i(vgs))/w, C_gx=+Im(i(vgs))/w, CDD=-Im(i(vds))/w, CSS=-Im(i(vsrc))/w, w=2 pi F_TEST.
F_TEST·LCHOKE_AC는 생성기 상수와 r2 meta frequencies_hz. 자릿수 15. 칸마다 append."""
import json, math, os, re, subprocess, sys
import numpy
T = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit"
W2 = T + "/work2"
sys.path.insert(0, T + "/op7a-iso2/.ai/verification/20261104-op7a/scripts")
import bin_rule_lib as B
plan = json.load(open(W2 + "/plan2.json", encoding="utf-8"))
kinds = {k["name"]: k for k in plan["kinds"]}
g = plan["lut_grid_um"] * 1e-6
with numpy.load(plan["combined_sets"][0]["npz"]) as z:
    r2 = json.loads(str(z["meta_json"]))
F = r2["frequencies_hz"]["F_TEST"]
LCH = 1e-15  # 생성기 LCHOKE_AC
OM = 2 * math.pi * F
OUTF = W2 + "/mode_value_diffs.jsonl"
open(OUTF, "w").close()
d = W2 + "/md"
for m_, txt in (("default", None), ("hsa", "set ngbehavior=hsa\n")):
    os.makedirs(f"{d}/{m_}/cwd", exist_ok=True); os.makedirs(f"{d}/{m_}/home", exist_ok=True)
    if txt:
        open(f"{d}/{m_}/cwd/.spiceinit", "w", newline="").write(txt)
cells = {}
for ln in open(W2 + "/run1/source_modes.jsonl", encoding="utf-8"):
    r = json.loads(ln)
    if "set" in r:
        cells.setdefault(r["set"], []).append(r)
NUM = r"([-+0-9.eE]+)"
def sim(k, sl_meta, l, w, vg, vd, pol, mode):
    sub = k["subckt"]; inst = f"m.xp.m{sub}"
    gm = re.search(r"ad=as=([0-9.eE+-]+)p pd=ps=([0-9.eE+-]+)u", sl_meta["geometry"])
    ad, pd = gm.group(1), gm.group(2)
    ac = f"ac lin 1 {F:.0f} {F:.0f}"
    lines = ["* a2b", *k["includes"], f".temp {sl_meta['temp_c_from_log']}", f"vgs g 0 dc {pol*vg} ac 0", f"vds dd 0 dc {pol*vd} ac 0",
             f"lchoke dd d {LCH}", "vsrc s 0 dc 0 ac 0", "vb b 0 dc 0",
             f"xp d g s b {sub} l={l*1e6:g}u w={w*1e6:g}u ad={ad}p as={ad}p pd={pd}u ps={pd}u nf={sl_meta['nf']} m={sl_meta['m']}",
             ".control", "set numdgt=15", "op", f"print @{inst}[id]", f"print @{inst}[gm]", f"print @{inst}[gds]", f"print @{inst}[vth]"]
    for src, tag, pr in (("vgs", "G", ["imag(i(vgs))"]), ("vds", "D", ["imag(i(vgs))", "imag(i(vds))"]), ("vsrc", "S", ["imag(i(vgs))", "imag(i(vsrc))"]), ("vb", "B", ["imag(i(vgs))"])):
        lines += [f"alter {src} ac = 1", ac, f"echo AC{tag}"] + [f"print {x}" for x in pr] + [f"alter {src} ac = 0"]
    lines += ["echo SHOWMOD p0", f"showmod {inst} : lmin lmax wmin wmax", "quit", ".endc", ".end"]
    cwd = f"{d}/{mode}/cwd"
    open(cwd + "/s.cir", "w", newline="\n").write("\n".join(lines) + "\n")
    p = subprocess.run([plan["ngspice_exe"], "-b", "s.cir"], cwd=cwd, env=B.isolated_env(os.environ, f"{d}/{mode}/home"), capture_output=True)
    t = p.stdout.decode(errors="replace")
    out = {"rc": p.returncode}
    for nm in ("id", "gm", "gds", "vth"):
        mm = re.search(r"\[%s\]\s*=\s*%s" % (nm, NUM), t)
        out[nm] = abs(float(mm.group(1))) if mm else None
    def sect(tag, expr):
        mm = re.search(r"AC%s\b.*?%s\s*=\s*%s" % (tag, re.escape(expr), NUM), t, re.S)
        return float(mm.group(1)) if mm else None
    def cv(sg, tag, e):
        v = sect(tag, e)
        return None if v is None else sg * v / OM
    out["CGG"] = cv(-1, "G", "imag(i(vgs))"); out["CGD"] = cv(1, "D", "imag(i(vgs))"); out["CGS"] = cv(1, "S", "imag(i(vgs))")
    out["CGB"] = cv(1, "B", "imag(i(vgs))"); out["CDD"] = cv(-1, "D", "imag(i(vds))"); out["CSS"] = cv(-1, "S", "imag(i(vsrc))")
    try:
        out["bin"] = B.parse_probe_log(t, k["bins"], g)["p0"]
    except B.BinRuleStop as e:
        out["bin"] = None; out["bin_err"] = e.reason
    return out
for sl in plan["slices"]:
    with numpy.load(sl["npz"]) as z:
        m = json.loads(str(z["meta_json"]))
    k = kinds[sl["kind"]]; pol = -1 if m["sign_convention"] and sl["kind"].startswith("pfet") else 1
    assert "pfet driven negative" in m["sign_convention"]
    vg = max(m["axes"]["VGS_V"], key=abs); vd = max(m["axes"]["VDS_V"], key=abs)
    assert m["axes"]["VS_V"][0] == 0.0
    w = m["w_m"]
    with open(OUTF, "a", encoding="utf-8") as f:
        for c in cells[sl["set"]]:
            a = sim(k, m, c["l_m"], w, vg, vd, pol, "default"); b = sim(k, m, c["l_m"], w, vg, vd, pol, "hsa")
            rel, why = {}, {}
            for q in ("id", "gm", "gds", "vth", "CGG", "CGD", "CGS", "CGB", "CDD", "CSS"):
                if a[q] is None or b[q] is None:
                    rel[q] = None; why[q] = "못 잼"
                elif a[q] == 0:
                    rel[q] = None; why[q] = "기본 값 0"
                else:
                    rel[q] = abs(a[q] - b[q]) / abs(a[q])
            f.write(json.dumps({"set": sl["set"], "kind": sl["kind"], "l_m": c["l_m"], "w_m": w,
                                "axes": list(B.tie_axes(c["l_m"], w, k["bins"], g)), "bin_d": a["bin"], "bin_h": b["bin"],
                                "bins_as_measured": a["bin"] == c["default"] and b["bin"] == c["hsa"], "rel": rel, "why": why,
                                "default": a, "hsa": b}) + "\n")
print("done")
