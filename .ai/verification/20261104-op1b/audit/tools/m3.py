"""§12.5 근거 (a)(b) 측정 결과를 판정 기록용 파일로 쓴다. 입력 = r2 meta, 생성기 판 텍스트(00085057)."""
import json, os, re, sys, hashlib
OUT = sys.argv[1]
m = json.load(open(os.path.join(OUT, "r2_meta.json"), encoding="utf-8"))
src = open(os.path.join(OUT, "generator_at_rev.py.txt"), encoding="utf-8").read().split("\n")
pm = re.search(r'PDK_ROOT = r"(.*)"', "\n".join(src)).group(1).replace("\\", "/")
pdk = m["pdk_root"].replace("\\", "/")
assert pm == pdk, (pm, pdk)
lod = re.search(r'LOD_SPICE\s*=\s*(.*)', "\n".join(src)).group(1)
inc_re = re.compile(r"^\s*\.(include|lib)\b", re.I)
lines_mi = src[219:228]  # 220-228행 model_includes, 줄 번호는 evidence에 적는다
assert src[219].startswith("def model_includes")
assert "_included_files(dev) + [os.path.join(PDK_ROOT, \"cells\", dev, f\"sky130_fd_pr__{dev}.bins.csv\")]" in src[676]
ev = {"generator": {"commit": "00085057d94e1f058be4c1a15808747d6aeec764", "path": "skills/analog-gmid-design/assets/sky130_lut_sweep.py",
                    "file_sha256": m["generator_sha256"], "matched": "raw",
                    "aux_append_lines": [677], "model_includes_lines": [220, 228], "lod_spice_decl": lod},
      "include_graph": {}, "measured_by": "verifier(판정자)", "date": "2026-11-04"}
roles = {}
for dev, rec in m["model_files_sha256"].items():
    start = []
    if dev.startswith("pfet"):
        start.append("models/parameters/lod.spice")
    start += [f"cells/{dev}/sky130_fd_pr__{dev}__tt.pm3.spice", f"cells/{dev}/sky130_fd_pr__{dev}__mismatch.corner.spice"]
    seen, stack = [], list(start)
    while stack:
        r = stack.pop(0)
        if r in seen:
            continue
        seen.append(r)
        data = open(os.path.join(pdk, r), "rb").read().decode("utf-8", "replace")
        hits = [ln for ln in data.splitlines() if inc_re.match(ln)]
        if hits:
            raise SystemExit(f"재귀 include 있음: {r} {hits[:3]} -- 측정 다시")
    ev["include_graph"][dev] = {"start": start, "files": seen}
    for rel, sha in rec.items():
        if rel in seen:
            role = "model_file"
        else:
            role = "generation_aux_input"
            raw = hashlib.sha256(open(os.path.join(pdk, rel), "rb").read()).hexdigest()
            ev.setdefault("aux_sha", {})[rel] = {"record": sha, "disk_raw": raw, "equal": raw == sha}
        roles[rel] = role
json.dump(roles, open(os.path.join(OUT, "roles.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1, sort_keys=True)
json.dump(ev, open(os.path.join(OUT, "roles_evidence.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print(json.dumps(roles, indent=0)); print(json.dumps(ev, ensure_ascii=False)[:1500])
