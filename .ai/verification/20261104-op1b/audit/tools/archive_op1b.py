# -*- coding: utf-8 -*-
"""C-7 보관(판정자 실행, OP-1a 분류 규칙 그대로). npz는 없음(LUT는 참조만).
사용: archive_op1b.py <raw work 폴더> <run 폴더> <DST = audit worktree/.ai/verification/20261104-op1b/baseline>
"""
import glob, hashlib, json, os, re, shutil, sys

RAW, RUN, DST = sys.argv[1:4]
PDK = "C:/pdk/sky130_fd_pr"


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


files = sorted(os.path.relpath(p, RAW).replace("\\", "/") for p in glob.glob(RAW + "/**/*", recursive=True) if os.path.isfile(p))
MC_AC = {f[:-len(".mc.log")] + ".ac.txt" for f in files if f.endswith(".mc.log")}
rows = []
groups = {}
for rel in files:
    p = os.path.join(RAW, rel)
    s, n = sha(p), os.path.getsize(p)
    base = os.path.basename(rel)
    ext = base.rsplit(".", 1)[1].lower() if "." in base else ""
    if ext in ("json", "md", "cir", "xml"):
        cls, keep = ext, True
    elif base.endswith(".mc.log"):
        cls, keep = "mc_log", True
    elif rel in MC_AC:
        cls, keep = "mc_ac", True
    elif ext == "txt":
        cls, keep = "sim_data_txt", False
    elif ext == "log":
        cls, keep = "sim_log", False
    else:
        cls, keep = "other_" + ext, False
    rows.append((rel, n, s, cls, keep))
    if keep:
        q = os.path.join(DST, "files", rel)
        os.makedirs(os.path.dirname(q), exist_ok=True)
        shutil.copyfile(p, q)
    else:
        g = groups.setdefault(cls, {"n": 0, "bytes": 0})
        g["n"] += 1
        g["bytes"] += n
os.makedirs(DST, exist_ok=True)
with open(os.path.join(DST, "_sha256_all.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("rel\tsize\tsha256\tclass\tcommitted\n")
    for rel, n, s, cls, keep in rows:
        f.write(f"{rel}\t{n}\t{s}\t{cls}\t{1 if keep else 0}\n")
OLD = re.compile(r"error|fatal|singular|abort", re.I)
PZ = re.compile(r"giving up|iteration limit|singular matrix", re.I)
MORE = re.compile(r"timestep too small|no convergence|not converge|gmin step|source step|could not find|unable to find|unknown|cannot|can't|failed|warning", re.I)
CTX = re.compile(r"stepping|^\s*note:", re.I)
nx = 0
with open(os.path.join(DST, "_log_excerpt.jsonl"), "w", encoding="utf-8", newline="\n") as f:
    for rel, n, s, cls, keep in rows:
        if not rel.endswith(".log"):
            continue
        with open(os.path.join(RAW, rel), encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
        hit = [(i + 1, ln) for i, ln in enumerate(lines) if OLD.search(ln) or PZ.search(ln) or MORE.search(ln) or CTX.search(ln)]
        if hit:
            f.write(json.dumps({"rel": rel, "sha256": s, "n_lines": len(lines),
                                "lines": [[i, ln, bool(OLD.search(ln)), bool(PZ.search(ln))] for i, ln in hit]}, ensure_ascii=False) + "\n")
            nx += len(hit)
with open(os.path.join(DST, "_external.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump({"raw_root": RAW.replace("\\", "/"), "groups": groups}, f, ensure_ascii=False, indent=1)
for name in sorted(os.listdir(os.path.join(RUN, "baseline"))):
    shutil.copyfile(os.path.join(RUN, "baseline", name), os.path.join(DST, name))
total = sum(os.path.getsize(os.path.join(r, x)) for r, _, xs in os.walk(os.path.join(DST, "files")) for x in xs)
print(json.dumps({"raw_files": len(rows), "committed": sum(1 for r in rows if r[4]), "committed_bytes": total, "excerpt_lines": nx, "groups": groups}))
