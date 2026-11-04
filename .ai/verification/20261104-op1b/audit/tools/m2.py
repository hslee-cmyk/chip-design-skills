"""§12.5 근거 (a)(b)를 r2에 대해 잰다(판정자 측정). 결과 = roles_evidence.json, roles.json."""
import hashlib, json, os, re, subprocess, sys
ISO, OUT = sys.argv[1:3]
GEN = "skills/analog-gmid-design/assets/sky130_lut_sweep.py"
PDK = "C:/pdk/sky130_fd_pr"
meta = json.load(open(os.path.join(OUT, "r2_meta.json"), encoding="utf-8"))
want = meta["generator_sha256"]


def git(*a, binary=True):
    return subprocess.run(["git", "-C", ISO, *a], capture_output=True, check=True).stdout


revs = git("log", "--all", "--format=%H", "--", GEN).decode().split()
hits = []
for r in revs:
    blob = git("show", f"{r}:{GEN}")
    lf = hashlib.sha256(blob.replace(b"\r\n", b"\n")).hexdigest()
    raw = hashlib.sha256(git("cat-file", "--filters", f"{r}:{GEN}")).hexdigest()
    crlf = hashlib.sha256(blob.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()
    if want in (lf, raw, crlf):
        hits.append({"rev": r, "lf": lf == want, "raw_filters": raw == want, "crlf_conv": crlf == want})
print("hits", hits)
rev = hits[0]["rev"] if hits else None
ev = {"generator_sha256": want, "revs_checked": len(revs), "hits": hits, "autocrlf": git("config", "--get", "core.autocrlf").decode().strip() if subprocess.run(["git", "-C", ISO, "config", "--get", "core.autocrlf"], capture_output=True).returncode == 0 else None}
if rev:
    src = git("show", f"{rev}:{GEN}").decode("utf-8", "replace").replace("\r\n", "\n")
    open(os.path.join(OUT, "generator_at_rev.py.txt"), "w", encoding="utf-8", newline="\n").write(src)
    lines = src.split("\n")
    pat = re.compile(r"bins\.csv|_included_files|model_includes|model_files_sha256|bins_csv|_bins_path|bins_path", re.I)
    ev["grep"] = [f"{i+1}: {ln}" for i, ln in enumerate(lines) if pat.search(ln)]
    print("\n".join(ev["grep"]))
json.dump(ev, open(os.path.join(OUT, "roles_a_grep.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
