"""design §7 (OP-1 측정 대기): ngspice log lines in the baseline that match the old regexes (error|fatal|singular|abort and
.pz 'giving up|iteration limit|singular matrix') plus other failure-looking lines; grouped into distinct normalised messages
with a draft code (§7 table) and example files."""
import glob, json, os, re, collections
B = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/baseline"
EXTRA = [r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/runs"]
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/results/m8_errlog.json"
OLD = re.compile(r"error|fatal|singular|abort", re.I)
PZ = re.compile(r"giving up|iteration limit|singular matrix", re.I)
MORE = re.compile(r"timestep too small|no convergence|not converge|gmin step|source step|could not find|unable to find|unknown|"
                  r"cannot|can't|failed|warning", re.I)
DRAFT = [(re.compile(r"singular", re.I), "sim_singular_matrix"),
         (re.compile(r"timestep too small", re.I), "sim_timestep_too_small"),
         (re.compile(r"no convergence|not converge|gmin step.*fail|source step.*fail|iteration limit|giving up", re.I), "sim_convergence_failed"),
         (re.compile(r"unable to find definition of model|could not find|unknown (?:sub)?circuit|model .* not found", re.I), "sim_model_not_found")]


def norm(s):
    s = re.sub(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", "#", s.strip())
    s = re.sub(r"\b[\w.:]*(?:x|m)[\w.]*\.[\w.]+\b", "<path>", s)
    return s[:160]


groups = collections.OrderedDict()
logs = [p for root in [B] + EXTRA for p in glob.glob(root + "/**/*.log", recursive=True)]
for p in logs:
    for ln in open(p, encoding="utf-8", errors="replace"):
        if not (OLD.search(ln) or PZ.search(ln) or MORE.search(ln)):
            continue
        k = norm(ln)
        g = groups.setdefault(k, {"n": 0, "files": [], "old_regex": bool(OLD.search(ln)), "pz_regex": bool(PZ.search(ln)),
                                  "draft_code": next((c for r, c in DRAFT if r.search(ln)), "sim_failed_other" if OLD.search(ln) or PZ.search(ln) else "(warning/info)"),
                                  "example": ln.strip()[:200]})
        g["n"] += 1
        if len(g["files"]) < 3:
            g["files"].append(os.path.relpath(p, os.path.dirname(B)))
res = {"n_logs": len(logs), "n_groups": len(groups), "groups": groups}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(res["n_logs"], res["n_groups"])
for k, g in groups.items():
    print(g["n"], g["draft_code"], "|", g["old_regex"], g["pz_regex"], "|", g["example"][:120])
