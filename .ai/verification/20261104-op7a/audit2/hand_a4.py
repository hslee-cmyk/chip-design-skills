"""A-4 재판정. bin_rule_lib·measure_bin_rule를 부르지 않는다. 입력: run1 산출물, PDK pm3, LUT meta_json·L(앞 판정 dump 재사용 안 함, 여기서 다시 읽음), PDK 바이트."""
import hashlib, json, re, collections
import numpy
T = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit"
W2 = T + "/work2"
plan = json.load(open(W2 + "/plan2.json", encoding="utf-8"))
tlef = open(plan["tlef"], encoding="utf-8", errors="replace").read()
G = float(re.search(r"MANUFACTURINGGRID\s+(\S+)", tlef).group(1)) * 1e-6
I = lambda x: int(round(x / G))
def table(path):
    t, name = {}, None
    for ln in open(path, encoding="utf-8", errors="replace"):
        s = ln.strip()
        if s.lower().startswith(".model"):
            name = s.split()[1]; t[name] = {}
        elif name and s.startswith("+") and "lmin" in s and not t[name]:
            t[name] = {k: I(float(v)) for k, v in re.findall(r"(lmin|lmax|wmin|wmax) = (\S+)", s)}
    return t
TB = {d: table(f"C:\\pdk\\sky130_fd_pr\\cells\\{d}\\sky130_fd_pr__{d}__tt.pm3.spice") for d in ("nfet_01v8", "pfet_01v8")}
def ties(T_, l, w):
    lt = any(b["lmax"] == l and b["wmin"] <= w <= b["wmax"] for b in T_.values()) and any(b["lmin"] == l and b["wmin"] <= w <= b["wmax"] for b in T_.values())
    wt = any(b["wmax"] == w and b["lmin"] <= l <= b["lmax"] for b in T_.values()) and any(b["wmin"] == w and b["lmin"] <= l <= b["lmax"] for b in T_.values())
    return lt, wt
pts = [json.loads(l) for l in open(W2 + "/run1/points.jsonl", encoding="utf-8")]
idx = {(p["kind"], I(p["L"]), I(p["W"])): p for p in pts}
out = {"points": len(pts)}
for mode in ("default", "cwd", "home", "empty"):
    c = collections.Counter()
    for p in pts:
        b = TB[p["kind"]][p[mode]]; l, w = I(p["L"]), I(p["W"])
        c["outside"] += not (b["lmin"] <= l <= b["lmax"] and b["wmin"] <= w <= b["wmax"])
        lt, wt = ties(TB[p["kind"]], l, w)
        c["tie"] += lt or wt
        if lt: c["L_lower" if b["lmax"] == l else "L_upper" if b["lmin"] == l else "L_interior"] += 1
        if wt: c["W_lower" if b["wmax"] == w else "W_upper" if b["wmin"] == w else "W_interior"] += 1
    out[mode] = dict(c)
# 출처 모드: 슬라이스마다 L·meta_json만
src = collections.Counter(); rec_lines = 0
files_hash = {}
srcfile_rows = {}
for ln in open(W2 + "/run1/source_modes.jsonl", encoding="utf-8"):
    r = json.loads(ln)
    if "set" in r:
        srcfile_rows[(r["set"], I(r["l_m"]))] = r
for sl in plan["slices"]:
    with numpy.load(sl["npz"]) as z:
        L = [float(x) for x in z["L"]]; m = json.loads(str(z["meta_json"]))
    per = {I(float(k) * 1e-6): v for k, v in m["model_bin_per_L"].items()}
    w = I(m["w_m"]); T_ = TB[sl["kind"]]
    for l in L:
        li = I(l); lt, wt = ties(T_, li, w)
        if not (lt or wt):
            continue
        p = idx[(sl["kind"], li, w)]; rec = per.get(li)
        src["cells"] += 1
        src["rec_default"] += rec == p["default"]; src["rec_hsa"] += rec == p["cwd"]
        src["modes_differ"] += p["default"] != p["cwd"]
        fr = srcfile_rows[(sl["set"], li)]
        src["file_row_same"] += fr["recorded"] == rec and fr["default"] == p["default"] and fr["hsa"] == p["cwd"]
    files_hash[sl["set"]] = m["model_files_sha256"]
out["source"] = dict(src)
# 결합·cap
loc = json.load(open(plan["location"], encoding="utf-8"))
comb = {}
for cs in plan["combined_sets"]:
    with numpy.load(cs["npz"]) as z:
        m = json.loads(str(z["meta_json"]))
    c = collections.Counter(); w = I(m["w_ref_m"])
    for dev, tab in m["model_bin_per_L_at_w_ref"].items():
        for k, b in tab.items():
            p = idx[(dev, I(float(k) * 1e-6), w)]
            c["cells"] += 1; c["same"] += b["model"] == p["default"]
    comb[cs["set"]] = dict(c)
out["combined"] = comb
cap = {}
for bs in plan["bound_sets"]:
    with numpy.load(bs["npz"]) as z:
        cap[bs["set"]] = json.loads(str(z["meta_json"]))["cap_npz_sha256"] == loc["files"]["cap_npz"]["sha256"]
out["cap_bind"] = cap
# model sha 다시 계산
lf, machine, mism = set(), set(), []
recs = {}
for s, mf in files_hash.items():
    for rel, sha in mf.items():
        recs[(rel, sha)] = 1
for f in loc["files"]:
    if f == "manifest":
        continue
    with numpy.load("C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/" + loc["files"][f]["path"]) as z:
        mf = json.loads(str(z["meta_json"]))["model_files_sha256"]
    for dv in mf.values():
        for rel, sha in dv.items():
            recs[(rel, sha)] = 1
for rel, sha in recs:
    b = open("C:/pdk/sky130_fd_pr/" + rel, "rb").read()
    a = hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest(); r = hashlib.sha256(b).hexdigest()
    lf.add(a)
    if sha == a: pass
    elif sha == r: machine.add(rel)
    else: mism.append(rel)
decl = json.load(open(W2 + "/run1_decl.json", encoding="utf-8"))
out["model_sha"] = {"records": len(recs), "same_as_decl": sorted(lf) == decl["model_files_sha256"], "machine_dep": len(machine), "mismatch": mism}
# 선언 evidence: lower 방향·동률 전부
pt_ok = 0
for e in decl["evidence"]["points"]:
    k = "nfet_01v8" if "nfet" in e["chosen_bin"] else "pfet_01v8"
    p = idx[(k, I(e["L"]), I(e["W"]))]
    pt_ok += p["default"] == e["chosen_bin"]
out["decl_points"] = {"n": len(decl["evidence"]["points"]), "same_as_points": pt_ok, "rule": decl["rule"], "source_basis": decl["evidence"]["source_basis"]}
json.dump(out, open(W2 + "/a4_result.json", "w"), indent=1)
print(json.dumps(out, indent=0))
