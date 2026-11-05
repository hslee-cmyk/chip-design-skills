# -*- coding: utf-8 -*-
"""A3-3: 옆 선언 둘을 판정자가 근거 (a)(b)로 직접 재서 만든다. 오라클·엔진 import 없음(표준 라이브러리 + numpy npz 읽기).
사용: a3_roles.py <repo> <lut_root> <pdk_root> <out_dir>
"""
import glob, hashlib, json, os, re, subprocess, sys
import numpy as np

REPO, LUT, PDK, OUT = sys.argv[1:5]
os.makedirs(OUT, exist_ok=True)
sha = lambda b: hashlib.sha256(b).hexdigest()
lf = lambda b: b.replace(b"\r\n", b"\n")


def meta(p):
    with np.load(p, allow_pickle=False) as z:
        return json.loads(str(z["meta_json"].item()))


INC = re.compile(r"""^\s*\.(?:include|inc|lib)\s+["']?([^"'\s]+)["']?""", re.I)


def graph(starts):
    seen, stack = [], list(starts)
    while stack:
        rel = stack.pop(0)
        if rel in seen:
            continue
        seen.append(rel)
        with open(os.path.join(PDK, rel), encoding="utf-8", errors="replace") as f:
            for ln in f:
                if ln.lstrip().startswith("*"):
                    continue
                m = INC.match(ln)
                if m:
                    q = m.group(1).replace("\\", "/")
                    stack.append(os.path.relpath(os.path.join(os.path.dirname(os.path.join(PDK, rel)), q), PDK).replace("\\", "/"))
    return seen


report = {}
# ---- 결합 파일
combined = os.path.join(LUT, "sky130_nfet_pfet_lut_v2_r2.npz")
mc = meta(combined)
gen_c = mc["generator_sha256"]
commit = "00085057d94e1f058be4c1a15808747d6aeec764"
gpath = "skills/analog-gmid-design/assets/sky130_lut_sweep.py"
blob = subprocess.run(["git", "-C", REPO, "cat-file", "blob", f"{commit}:{gpath}"], capture_output=True, check=True).stdout
blob_crlf = lf(blob).replace(b"\n", b"\r\n")
filt = subprocess.run(["git", "-C", REPO, "cat-file", "--filters", f"{commit}:{gpath}"], capture_output=True).stdout
src = lf(blob).decode("utf-8", errors="replace").split("\n")
report["combined"] = {"generator_sha256": gen_c, "blob_lf": sha(lf(blob)), "blob_crlf": sha(blob_crlf), "cat_file_filters": sha(filt),
                      "append_lines": [i + 1 for i, s in enumerate(src) if "bins.csv" in s or "bins_csv" in s],
                      "model_includes": src[219:228]}
matched_c = "lf" if sha(lf(blob)) == gen_c else ("raw" if gen_c in (sha(blob_crlf), sha(filt)) else None)
# ---- 슬라이스
slices = sorted(glob.glob(os.path.join(LUT, "*__tt__W*_dc.npz")))
sm = {p: meta(p) for p in slices}
gens = sorted({m["generator_sha256"] for m in sm.values()})
gen_path = os.path.join(LUT, "verification", "slices_vdsat", "sky130_dc_width_slices.py")
gb = open(gen_path, "rb").read()
gl = lf(gb).decode("utf-8", errors="replace").split("\n")
report["slices"] = {"n": len(slices), "generator_values": gens, "file_raw": sha(gb), "file_lf": sha(lf(gb)),
                    "lines_73_79": gl[72:79], "line_175": gl[174], "lines_177_178": gl[176:178], "lines_296_299": gl[295:299]}
matched_s = "lf" if sha(lf(gb)) == gens[0] else ("raw" if sha(gb) == gens[0] else None)

# ---- 역할 값(근거 (b): 시작점 include 재귀 그래프에 없고, 기록에는 있다)
rec_all = {}
for kind_tbl in mc["model_files_sha256"].values():
    rec_all.update(kind_tbl)
starts_c = [r for r in rec_all if not r.endswith(".csv")]
g_c = {k: graph([r for r in t if not r.endswith(".csv")]) for k, t in mc["model_files_sha256"].items()}
# 시작점을 이름으로 고르지 않음을 보이기 위해 include 목록은 생성기 코드에서 따로 읽어 report 에 둔다(model_includes, lines_73_79)


def build(gen, recs, matched, generator_ev, files_starts):
    roles = {}
    files = graph(files_starts)
    for rel, s in sorted(recs.items()):
        roles[rel] = {"sha256": s, "role": "model_file" if rel in files else "generation_aux_input"}
    return {"schema": "lut_file_roles/1", "generator_sha256": gen, "roles": roles,
            "evidence": {"generator": generator_ev, "include_graph": {"start": files_starts, "files": files},
                         "measured_by": "verifier(판정자, card 20261104-op23 A3-3)", "date": "2026-11-04"}}


doc_c = build(gen_c, rec_all, matched_c,
              {"commit": commit, "path": gpath, "file_sha256": gen_c, "matched": matched_c,
               "aux_append_lines": report["combined"]["append_lines"]}, sorted(starts_c))
rec_s = {}
conf = []
for p, m in sm.items():
    for rel, s in m["model_files_sha256"].items():
        if rec_s.get(rel, s) != s:
            conf.append((os.path.basename(p), rel))
        rec_s[rel] = s
report["slices"]["record_conflicts"] = conf
report["slices"]["record_paths"] = sorted(rec_s)
doc_s = build(gens[0], rec_s, matched_s,
              {"commit": None, "data_path": "verification/slices_vdsat/sky130_dc_width_slices.py", "path": "sky130_dc_width_slices.py",
               "file_sha256": gens[0], "matched": matched_s, "aux_append_lines": [298]},
              sorted(r for r in rec_s if not r.endswith(".csv")))
for d in (doc_c, doc_s):
    p = os.path.join(OUT, f"{d['generator_sha256'][:16]}.lut_file_roles.json")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    report.setdefault("files", {})[os.path.basename(p)] = {"lf": sha(lf(open(p, "rb").read())),
                                                           "aux": sorted(r for r, v in d["roles"].items() if v["role"] != "model_file"),
                                                           "model": sorted(r for r, v in d["roles"].items() if v["role"] == "model_file")}
# 보조 입력 디스크 대조
report["aux_disk"] = {}
for d in (doc_c, doc_s):
    for r, v in d["roles"].items():
        if v["role"] != "model_file":
            b = open(os.path.join(PDK, r), "rb").read()
            report["aux_disk"][r] = {"record": v["sha256"], "raw": sha(b), "lf": sha(lf(b))}
with open(os.path.join(OUT, "a3_3_report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print(json.dumps(report, ensure_ascii=False, indent=1))
