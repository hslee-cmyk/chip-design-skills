# -*- coding: utf-8 -*-
"""OP-2 구역 A2-2~A2-5 측정. 사용: a2.py <iso> <out.json>"""
import hashlib, json, os, re, subprocess, sys

ISO, OUT = sys.argv[1:3]
S = os.path.join(ISO, "skills/analog-gmid-design")
O = os.path.join(S, "tools/spice_oracle")
A = os.path.join(S, "assets")
sys.path.insert(0, O)
rawh = lambda b: hashlib.sha256(b).hexdigest()
lf = lambda b: rawh(b.replace(b"\r\n", b"\n"))
rd = lambda p: open(p, "rb").read()
res = {}
dp = os.path.join(O, "descriptors/sky130.oracle_descriptor.json")
doc = json.load(open(dp, encoding="utf-8"))
# A2-2 sha 따로 재기
ref = {"engine_decl": doc["engine_decl"], **{f"extra:{k}": v for k, v in doc["extra_engine_decls"].items()},
       "location": doc["lut_record_root"]["location_decl"]}
res["A2-2"] = {k: {"descriptor": v["sha256"], "file_lf": lf(rd(os.path.join(os.path.dirname(dp), v["path"]))),
                   "file_raw": rawh(rd(os.path.join(os.path.dirname(dp), v["path"]))),
                   "equal": v["sha256"] == lf(rd(os.path.join(os.path.dirname(dp), v["path"])))} for k, v in ref.items()}
decl = json.load(open(os.path.join(os.path.dirname(dp), doc["engine_decl"]["path"]), encoding="utf-8"))
pdk = decl["pdk_root"]
eng = {k: os.path.abspath(os.path.join(pdk, s["path"])) for k, s in decl["sources"].items()}
ext = {k: os.path.abspath(os.path.join(pdk, s["path"])) for k, s in doc["extra_sources"].items()}
res["A2-2"]["overlap"] = {"path": sorted(set(eng.values()) & set(ext.values())),
                          "sha": sorted({lf(rd(p)) for p in eng.values()} & {lf(rd(p)) for p in ext.values()})}
res["A2-2"]["n_sources"] = [len(eng), len(ext)]
# A2-3
from core.descriptor import load_descriptor  # noqa: E402
env = {k: v for k, v in os.environ.items() if k != "GMID_PDK_ROOT"}
D = load_descriptor(dp, env=env)
used = set()
for kd in doc["kinds"].values():
    for s in (kd["name"], kd["inner_device"]):
        if "expr" in s:
            used.add(s["expr"]["source"])
    used.add(kd["parallel_multiplier"]["source"]["expr"]["source"])
    for it in kd["includes"]:
        used.add(it["source"])
    used.add(decl["quantities"][kd["geometry_unit"]["source"]]["source"])
for t in doc["temperature"]["tnom"].values():
    used.add(decl["quantities"][t["source"]]["source"])
used &= set(decl["sources"])
raw_only = sorted(k for k in used if decl["sources"][k]["sha256"] != lf(rd(eng[k])) and decl["sources"][k]["sha256"] == rawh(rd(eng[k])))
bad = sorted(k for k in used if decl["sources"][k]["sha256"] not in (lf(rd(eng[k])), rawh(rd(eng[k]))))
got = sorted(r["ref"].split(":", 1)[1] for r in D.machine_dependent_refs)
res["A2-3"] = {"record_root": D.record_root, "source": D.record_root_source, "used_keys": sorted(used), "direct_raw_only": raw_only, "direct_bad": bad,
               "loader_machine_dep": got, "equal": raw_only == got, "fp": D.fp}
# A2-4 값 대조
vals = {}
for kn, kd in doc["kinds"].items():
    model = rd(eng[kd["name"]["expr"]["source"]]).decode("utf-8", errors="replace").replace("\r\n", "\n")
    m = re.search(r"^\.subckt\s+(\S+)\s+(.*)$", model, re.M | re.I)
    inner = re.search(r"^(m\S*)\s", model[m.end():], re.M | re.I)
    pol = re.search(r"^\.model\s+\S+\s+(\w+)", model, re.M | re.I)
    lv = re.search(r"level\s*=\s*(\S+)", model, re.I)
    ver = re.search(r"version\s*=\s*(\S+)", model, re.I)
    expr = len(re.findall(r"sqrt\(l\*w\*mult\)", model, re.I))
    vals[kn] = {"direct_name": m.group(1), "loader_name": D.text(kd["name"]), "subckt_params": m.group(2)[:120],
                "direct_inner": inner.group(1) if inner else None, "loader_inner": D.text(kd["inner_device"]),
                "polarity_card": pol.group(1) if pol else None, "polarity_desc": kd["polarity"], "level": lv.group(1) if lv else None, "version": ver.group(1) if ver else None,
                "unit": D.quantity(kd["geometry_unit"]["source"]), "tnom_card": sorted(set(re.findall(r"tnom\s*=\s*(\S+)", model, re.I)))[:3], "tnom_quantity_key_in_decl": doc["temperature"]["tnom"][kn]["source"] in decl["quantities"],
                "sqrt_lwmult_hits": expr, "includes": [D.source_path(i["source"]) for i in kd["includes"]]}
vals["scale_line"] = re.search(r"^\.option\s+scale\s*=\s*\S+", rd(eng["scale_option"]).decode("utf-8", "replace"), re.M | re.I).group(0)
vals["model_family"] = doc["model_family"]
vals["diffusion"] = {k: D.quantity(doc["diffusion"][k]) for k in ("ad_per_w", "as_per_w", "pd_extra", "ps_extra")}
gen = open(os.path.join(os.path.dirname(dp), json.load(open(os.path.join(A, "sky130_lut_rule_decl.json"), encoding="utf-8"))["sources"]["lut_generator"].get("path", "x")), "rb").read() if False else None
rule = json.load(open(os.path.join(A, "sky130_lut_rule_decl.json"), encoding="utf-8"))
vals["lut_rule_sources"] = {k: {kk: vv for kk, vv in v.items() if kk in ("path", "format")} for k, v in rule["sources"].items()}
vals["numeric_values_in_descriptor"] = sorted({str(x) for x in re.findall(r":\s*(-?[0-9][0-9.eE+-]*)\s*[,\n}]", rd(dp).decode("utf-8"))})
vals["extra_source"] = {k: {"path": v["path"], "desc_sha": v["sha256"], "file_lf": lf(rd(ext[k])), "provenance": v["provenance"][:300]} for k, v in doc["extra_sources"].items()}
pdk_head = subprocess.run(["git", "-C", pdk, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
vals["pdk_repo_head"] = pdk_head
res["A2-4"] = vals
# 옛 process.diffusion 대조(변환 기록)
bl = os.path.join(ISO, ".ai/verification/20261104-op1b/baseline")
res["old_process_diffusion"] = {r: json.load(open(os.path.join(bl, f"{r}.converted.json"), encoding="utf-8"))["record"]["diffusion"] for r in ("R1", "R2", "R3", "R4", "R5")}
# A2-5
pdf_repo = os.path.join(A, "simulator_sources/ngspice_46_manual/source.pdf")
pdf_ext = "C:/ngspice/Spice64/docs/ngspice-46-manual.pdf"
res["A2-5"] = {"repo_pdf_exists": os.path.exists(pdf_repo), "ext_pdf_sha": rawh(rd(pdf_ext)), "ext_pdf_size": os.path.getsize(pdf_ext), "pages": {}}
for pg in (317, 318, 320):
    t = subprocess.run(["pdftotext", "-layout", "-f", str(pg), "-l", str(pg), pdf_ext, "-"], capture_output=True).stdout.decode("utf-8", "replace")
    keep = [ln.strip() for ln in t.splitlines() if re.search(r"ABSTOL|RELTOL|VNTOL|SCALE|scale|default", ln)]
    res["A2-5"]["pages"][pg] = keep[:30]
cal = json.load(open(os.path.join(O, "adapters/ngspice/calibration.json"), encoding="utf-8"))
res["A2-5"]["cal_tolerances"] = {k: v["value"] for k, v in cal["default_tolerances"].items()}
res["A2-5"]["cal_affects"] = cal["global_geometry_directive"]["affects"]
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1, default=str)
print(json.dumps(res, ensure_ascii=False, indent=0, default=str))
