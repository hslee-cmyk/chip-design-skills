"""Sandbox only. Build synthetic repo for the D0a 'determinism' stage and judge variant implementations.
usage: python det_run.py <gates dir> <mp.py> <work dir> <out jsonl>
Judging is independent of the implementation: expectations come from the construction below.
"""
import json
import os
import shutil
import subprocess
import sys

GATES, MP, WORK, OUT = (sys.argv[1:5] + [None]*4)[:4]
PY = sys.executable
A = "skills/analog-gmid-design/assets/"
NAMES = ["d", "c", "b", "a", "h", "g", "f", "e"]          # written in reverse-ish order on purpose


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("git %s: %s" % (args, r.stderr))
    return r.stdout.strip()


def write(repo, rel, text):
    p = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def build(repo, n, ncyc):
    """n = elements per order-asserted list, ncyc = MOD cycles. Returns (commits, expected)."""
    if os.path.exists(repo):
        shutil.rmtree(repo)
    os.makedirs(repo)
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "s@x")
    git(repo, "config", "user.name", "s")
    git(repo, "config", "core.autocrlf", "false")
    shutil.copytree(GATES, os.path.join(repo, "tools", "gates"), ignore=shutil.ignore_patterns("__pycache__"))
    nm = NAMES[:n]
    # ---- N3.10: MOD1..MOD7, m7 = layout row
    rep = {k: [] for k in range(1, 8)}
    for x in nm:                                   # conflicts n: token in MOD2 and MOD3 rows (reverse order in table)
        rep[2].append("cf_" + x)
        rep[3].append("cf_" + x)
    rep[7].append("l7t")                           # lift-cap target (MOD7)
    rep[2].append("la_tgt")                        # lift-a4 target (MOD2)
    cyc_pairs = [(3, 4), (5, 6)][:ncyc]
    for i, (j, k) in enumerate(cyc_pairs):
        rep[j].append("cy%d_lo" % i)
        rep[k].append("cy%d_hi" % i)
    plan = ["# plan", "", "### N3.10 모듈", "", "| ID | 파일 | 책임 | 대표 대상 |", "|---|---|---|---|"]
    for k in range(1, 8):
        resp = "레이아웃만" if k == 7 else "책임 %d" % k
        plan.append("| MOD%d | `m%d.py` | %s | %s |" % (k, k, resp, ", ".join("`%s`" % t for t in rep[k]) or "산문"))
    plan.append("")
    # ---- registry
    reg = ["# registry", "", "## 함수 표", "", "| 함수 | 이관 목적지 |", "|---|---|"]
    regrows = []
    for x in nm:
        regrows.append(("lc_" + x, "m2"))           # lift-cap-mod7 first branch: cell m2, calls MOD7 -> stays m2, upward
        regrows.append(("la_" + x, "m1"))           # lift-a4 first branch: cell m1, calls MOD2 -> m2, reg_mismatch
    F = 16
    for i in range(F):
        regrows.append(("f4_%02d" % i, "m1"))       # A-4 fillers
        regrows.append(("g4_%02d" % i, "m2"))
    regrows.sort(reverse=True)                      # table rows in reverse name order
    reg += ["| `%s` | %s |" % r for r in regrows]
    reg.append("")
    # ---- sources
    src = ['"""synthetic src."""', ""]
    for x in nm:
        src += ["def cf_%s():" % x, "    return 0", ""]
    src += ["def l7t():", "    return 7", "", "def la_tgt():", "    return 2", ""]
    for x in nm:
        src += ["def lc_%s():" % x, "    return l7t()", ""]
        src += ["def la_%s():" % x, "    return la_tgt()", ""]
    for i, (j, k) in enumerate(cyc_pairs):
        src += ["def cy%d_lo():" % i, "    return cy%d_hi()" % i, "", "def cy%d_hi():" % i, "    return cy%d_lo" % i, ""]
    for i in range(F):
        src += ["C5_%02d = %d" % (i, i), "SH_%02d = %d" % (i, i), ""]
        src += ["def f4_%02d():" % i, "    return C5_%02d + SH_%02d" % (i, i), ""]
        src += ["def g4_%02d():" % i, "    return SH_%02d" % i, ""]
    write(repo, A + "src.py", "\n".join(src) + "\n")
    iso = ['"""isolated."""', ""]
    for a, b in zip(nm[0::2], nm[1::2]):           # a7-isolated second branch: pairs calling only each other
        iso += ["def ua_%s():" % a, "    return ua_%s()" % b, "", "def ua_%s():" % b, "    return ua_%s()" % a, ""]
    write(repo, A + "iso.py", "\n".join(iso) + "\n")
    tool = ['"""tool."""', ""]
    for i in range(F):
        tool += ["def tk_%02d():" % i, "    return %d" % i, ""]
    write(repo, A + "tool.py", "\n".join(tool) + "\n")
    write(repo, "docs/plan.md", "\n".join(plan))
    write(repo, "docs/reg.md", "\n".join(reg))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "C0 determinism")
    c0 = git(repo, "rev-parse", "HEAD")
    exp = {
        "upward": sorted(["src.py::lc_%s -> src.py::l7t" % x for x in nm]
                         + ["src.py::cy%d_lo -> src.py::cy%d_hi" % (i, i) for i in range(ncyc)]),
        "cycles": [["m%d.py" % j, "m%d.py" % k] for j, k in cyc_pairs],
        "unassigned": sorted("iso.py::ua_%s" % x for x in nm),
        "conflicts": sorted(["src.py::cf_%s" % x for x in nm]),
        "reg_mismatch_units": sorted("src.py::la_%s" % x for x in nm),
        "units": ["src.py::%s" % u for u in
                  ["l7t", "la_tgt"] + ["lc_" + x for x in nm] + ["la_" + x for x in nm] + ["cf_" + x for x in nm]],
    }
    # ---- (iv) separate commits (children of C0): q rows
    commits = {"C0": c0}

    def child(tag, rows, a1=False):
        git(repo, "checkout", "-q", c0)
        s = open(os.path.join(repo, A + "src.py"), encoding="utf-8").read() + "\ndef q():\n    return 0\n"
        write(repo, A + "src.py", s)
        r = open(os.path.join(repo, "docs/reg.md"), encoding="utf-8").read().rstrip("\n") + "\n" + \
            "\n".join("| `q` | %s |" % c for c in rows) + "\n"
        write(repo, "docs/reg.md", r)
        if a1:
            p = open(os.path.join(repo, "docs/plan.md"), encoding="utf-8").read().replace("| MOD3 | `m3.py` | 책임 3 | ",
                                                                                     "| MOD3 | `m3.py` | 책임 3 | `q`, ")
            write(repo, "docs/plan.md", p)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", tag)
        commits[tag] = git(repo, "rev-parse", "HEAD")
    child("D5a", ["m2", "m5"])                 # (e5) -> exit 2
    child("D5b", ["m2", "m2"])                 # same -> q = m2.py A-4
    child("D5c", ["m2", "m5", "m3, m6"])       # (e5) with an A-3 row -> still exit 2 ((e5) precedes A-3)
    child("D5d", ["m2", "m5"], a1=True)        # q decided by A-1 (MOD3) -> (e5) out of scope -> q = m3.py A-1
    git(repo, "checkout", "-q", c0)
    return commits, exp


ARGS = ["--plan", "docs/plan.md", "--registry", "docs/reg.md", "--split", "src.py", "iso.py", "tool.py", "--keep", "tool.py"]


def run(variant, seed, argv):
    env = dict(os.environ, MPV=variant, PYTHONHASHSEED=str(seed), PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([PY, "-B", MP] + argv, capture_output=True, env=env)
    return r.returncode, r.stdout.decode("utf-8"), r.stderr.decode("utf-8")[-400:]


def keys_sorted_deep(v):
    if isinstance(v, dict):
        ks = list(v)
        return ks == sorted(ks) and all(keys_sorted_deep(x) for x in v.values())
    if isinstance(v, list):
        return all(keys_sorted_deep(x) for x in v)
    return True


def ek(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False) if not isinstance(x, str) else x


def judge(repo, commits, exp, variant, seeds, n, ncyc):
    res = {"variant": variant, "n": n, "ncyc": ncyc, "seeds": list(seeds), "fail": []}
    plan_argv = ["plan", "--root", repo, "--rev", commits["C0"]] + ARGS
    outs = [run(variant, s, plan_argv) for s in seeds]
    res["plan_distinct"] = len({o[1] for o in outs})
    # (i)
    if res["plan_distinct"] != 1:
        res["fail"].append("(i) plan stdout differs across seeds")
    rc, so, se = outs[0]
    try:
        obj = json.loads(so, object_pairs_hook=lambda kv: dict(kv))
    except Exception:
        res["fail"].append("plan not JSON rc=%d %s" % (rc, se))
        return res
    if rc != 1 or obj.get("verdict") != "FAIL":
        res["fail"].append("(i) exit/verdict %s %s" % (rc, obj.get("verdict")))
    # (ii)
    top = list(obj)
    if top[:3] != ["tool", "command", "verdict"] or top[3:] != sorted(top[3:]):
        res["fail"].append("(ii) top key order")
    if not all(keys_sorted_deep(obj[k]) for k in top):
        res["fail"].append("(ii) nested key order")
    for k in ("upward", "cycles", "unassigned", "conflicts", "reg_mismatch"):
        L = obj.get(k, [])
        if [ek(x) for x in L] != sorted(ek(x) for x in L):
            res["fail"].append("(ii) %s not element-sorted" % k)
    # construction expectations (precondition: lists really have >= n / ncyc elements)
    if sorted(obj.get("upward", [])) != exp["upward"]:
        res["fail"].append("(ii) upward set != construction")
    if sorted(obj.get("cycles", [])) != exp["cycles"]:
        res["fail"].append("(ii) cycles != construction")
    if sorted(obj.get("unassigned", [])) != exp["unassigned"]:
        res["fail"].append("(ii) unassigned != construction")
    if sorted(c["unit"] for c in obj.get("conflicts", [])) != exp["conflicts"]:
        res["fail"].append("(ii) conflicts != construction")
    if sorted(r["unit"] for r in obj.get("reg_mismatch", [])) != exp["reg_mismatch_units"]:
        res["fail"].append("(ii) reg_mismatch != construction")
    res["sizes"] = {k: len(obj.get(k, [])) for k in ("upward", "cycles", "unassigned", "conflicts", "reg_mismatch")}
    res["assigned"] = len(obj.get("assignment", {}))
    # (iii)
    chk = ["check", "--root", repo, "--base", commits["C0"], "--head", commits["C0"], "--card", "ALL"] + ARGS
    couts = [run(variant, s, chk) for s in seeds]
    res["check_distinct"] = len({o[1] for o in couts})
    if res["check_distinct"] != 1:
        res["fail"].append("(iii) check stdout differs across seeds")
    # (iv)
    iv = {}
    for tag in ("D5a", "D5b", "D5c", "D5d"):
        rc, so, se = run(variant, 0, ["plan", "--root", repo, "--rev", commits[tag]] + ARGS)
        o = json.loads(so)
        iv[tag] = (rc, o.get("verdict"), o.get("assignment", {}).get("src.py::q"), (o.get("error") or "")[:80])
    res["iv"] = iv
    if not (iv["D5a"][0] == 2 and iv["D5a"][1] == "ERROR" and "q" in iv["D5a"][3]):
        res["fail"].append("(iv) D5a not exit 2")
    if iv["D5b"][2] != {"mod": "m2.py", "rule": "A-4"}:
        res["fail"].append("(iv) D5b q != m2.py A-4")
    if not (iv["D5c"][0] == 2 and "q" in iv["D5c"][3]):
        res["fail"].append("(iv) D5c not exit 2")
    if iv["D5d"][2] != {"mod": "m3.py", "rule": "A-1"}:
        res["fail"].append("(iv) D5d q != m3.py A-1")
    res["verdict"] = "FAIL" if res["fail"] else "PASS"
    return res


def witness(keys, seeds):
    code = "import json,sys; print(json.dumps(list(set(json.loads(sys.argv[1])))))"
    outs = set()
    for s in seeds:
        env = dict(os.environ, PYTHONHASHSEED=str(s))
        outs.add(subprocess.run([PY, "-c", code, json.dumps(keys)], capture_output=True, text=True, env=env).stdout)
    return len(outs)


if __name__ == '__main__':
    os.makedirs(WORK, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        for label, n, ncyc, seeds in (("old-card(n=2,cyc=1,seeds 0-1)", 2, 1, range(2)),
                                      ("new-card(n=4,cyc=2,seeds 0-7)", 4, 2, range(8))):
            repo = os.path.join(WORK, "syn_n%d" % n)
            commits, exp = build(repo, n, ncyc)
            w = witness(exp["units"], seeds)
            fh.write(json.dumps({"stage": label, "witness_distinct_set_orders": w, "nseeds": len(list(seeds))}) + "\n")
            fh.flush()
            for v in ("sorted", "leak_unassigned", "leak_upward", "content", "first_row", "proto"):
                r = judge(repo, commits, exp, v, seeds, n, ncyc)
                r["stage"] = label
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                fh.flush()
    print("done", OUT)
