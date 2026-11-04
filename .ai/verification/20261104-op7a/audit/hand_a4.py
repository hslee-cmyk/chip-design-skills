"""A-4 독립 재확인. bin_rule_lib를 부르지 않는다(마지막 비교 한 줄만). 정수 비교는 nm 단위 자체 구현.
입력: run1/points.jsonl, run1/source_modes.jsonl, PDK pm3, LUT meta(meta_json 멤버만 읽은 dump), PDK 파일 바이트."""
import hashlib, json, re, sys, collections
W = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/work"
plan = json.load(open(W + "/plan.json", encoding="utf-8"))
GRID_UM = plan["lut_grid_um"]
tlef = open(plan["tlef"], encoding="utf-8", errors="replace").read()
assert float(re.search(r"MANUFACTURINGGRID\s+(\S+)", tlef).group(1)) == GRID_UM
G = GRID_UM * 1e-6
I = lambda x: int(round(x / G))
def table(path):
    t = {}; name = None
    for ln in open(path, encoding="utf-8", errors="replace"):
        s = ln.strip()
        if s.lower().startswith(".model"):
            name = s.split()[1]; t[name] = {}
        elif name and s.startswith("+") and "lmin" in s and not t[name]:
            kv = re.findall(r"(lmin|lmax|wmin|wmax) = (\S+)", s)
            t[name] = {k: I(float(v)) for k, v in kv}
    return t
out = {}
for mode in ("default", "cwd", "home", "empty"):
    dirs = collections.Counter(); per_axis = collections.Counter()
    tie_pts = 0; n = 0; bad = 0
    for ln in open(W + "/run1/points.jsonl", encoding="utf-8"):
        p = json.loads(ln); n += 1
        dev = p["kind"]
        t = TABLES.setdefault(dev, table(f"C:\\pdk\\sky130_fd_pr\\cells\\{dev}\\sky130_fd_pr__{dev}__tt.pm3.spice")) if False else None
        break
TABLES = {d: table(f"C:\\pdk\\sky130_fd_pr\\cells\\{d}\\sky130_fd_pr__{d}__tt.pm3.spice") for d in ("nfet_01v8", "pfet_01v8")}
for mode in ("default", "cwd", "home", "empty"):
    per_axis = collections.Counter(); tie_pts = 0; n = 0; outside = 0
    per_kind = collections.Counter()
    for ln in open(W + "/run1/points.jsonl", encoding="utf-8"):
        p = json.loads(ln); n += 1
        T = TABLES[p["kind"]]; l, w = I(p["L"]), I(p["W"])
        c = T[p[mode]]
        if not (c["lmin"] <= l <= c["lmax"] and c["wmin"] <= w <= c["wmax"]):
            outside += 1
        lt = any(b["lmax"] == l and b["wmin"] <= w <= b["wmax"] for b in T.values()) and any(b["lmin"] == l and b["wmin"] <= w <= b["wmax"] for b in T.values())
        wt = any(b["wmax"] == w and b["lmin"] <= l <= b["lmax"] for b in T.values()) and any(b["wmin"] == w and b["lmin"] <= l <= b["lmax"] for b in T.values())
        if lt or wt: tie_pts += 1
        if lt:
            d = "lower" if c["lmax"] == l else "upper" if c["lmin"] == l else "interior"
            per_axis["L:" + d] += 1; per_kind[p["kind"] + ":L:" + d] += 1
        if wt:
            d = "lower" if c["wmax"] == w else "upper" if c["wmin"] == w else "interior"
            per_axis["W:" + d] += 1; per_kind[p["kind"] + ":W:" + d] += 1
    vals = {k.split(":")[1] for k in per_axis}
    out[mode] = {"points": n, "tie_points": tie_pts, "outside": outside, "per_axis": dict(per_axis), "per_kind": dict(per_kind),
                 "rule": next(iter(vals)) if len(vals) == 1 else None}
srcrows = [json.loads(l) for l in open(W + "/run1/source_modes.jsonl", encoding="utf-8")]
def mode_of(r):
    a = abs(abs(r["lut_id"]) - abs(r["default_id"])); b = abs(abs(r["lut_id"]) - abs(r["hsa_id"]))
    return "default" if a < b else "hsa" if b < a else None
out["source"] = {"n": len(srcrows), "rederived": collections.Counter(str(mode_of(r)) for r in srcrows),
                 "recorded": collections.Counter(str(r["mode"]) for r in srcrows), "identical_pair": sum(r["default_id"] == r["hsa_id"] for r in srcrows)}
# model_files_sha256
lf_vals = set(); machine = set(); mism = []
for path, rec in plan["model_records"]:
    b = open(path, "rb").read()
    lf = hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest(); raw = hashlib.sha256(b).hexdigest()
    lf_vals.add(lf)
    if rec == lf: pass
    elif rec == raw: machine.add(path)
    else: mism.append(path)
sys.path.insert(0, "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/op7a-iso/.ai/verification/20261104-op7a/scripts")
import bin_rule_lib as B
lib_lf, lib_md = B.union_model_sha([tuple(r) for r in plan["model_records"]], lambda p: open(p, "rb").read())
out["model_sha"] = {"n_records": len(plan["model_records"]), "lf": sorted(lf_vals), "machine_dep": sorted(machine), "mismatch": mism,
                    "same_as_lib": lib_lf == sorted(lf_vals) and lib_md == sorted(machine)}
json.dump(out, open(W + "/a4_result.json", "w"), indent=1, default=dict)
print(json.dumps(out, indent=1, default=dict))
