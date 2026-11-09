"""Sandbox only (det3 author kit, measure only). Build the synthetic repo for the D0a 'determinism' stage per the det3 card
sentences ((a) multi-MOD A-5 referrers, (b) one MOD with >=4 `from` lines + >=2 `import` lines, (c) mixed upper/_/lower names,
(d) import_conflicts child commit, (iv-a..g)) and judge variant implementations.
usage: python det_run3.py <gates dir> <mp.py> <work dir> <out jsonl> [variant,variant,...]   (env MP_STMT_KEY=names is set per run)
Expectations come from the construction below (never from tool output).
"""
import json
import os
import shutil
import subprocess
import sys

GATES, MP, WORK, OUT = (sys.argv[1:5] + [None]*4)[:4]
PY = sys.executable
A = "skills/analog-gmid-design/assets/"
ADIR = A.rstrip("/")
LET = ["d", "c", "b", "a"]          # written in reverse order on purpose


def mixed(prefix, x):
    """(c): b -> Capitalised, c -> _ prefix, a/d -> lower. codepoint order != case-insensitive order != punctuation-ignoring order."""
    if x == "b":
        return prefix.capitalize() + "_" + x
    if x == "c":
        return "_" + prefix + "_" + x
    return prefix + "_" + x


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


def read(repo, rel):
    return open(os.path.join(repo, rel), encoding="utf-8").read()


def ek(x):
    return x if isinstance(x, str) else json.dumps(x, sort_keys=True, ensure_ascii=False)


EXT_HEAD = ["from string import Template, ascii_letters", "import sys", "from os import sep, path as _osp",   # (b) not in module-name order
            "from re import Pattern, escape", "import math", "from json import JSONDecoder, dumps", ""]
EXP_M1 = ["from json import JSONDecoder, dumps", "from os import path as _osp, sep", "from re import Pattern, escape",
          "from string import Template, ascii_letters", "import math", "import sys"]
IC_NAMES = ["Mx", "_nx", "kx", "lx"]


def build(repo):
    if os.path.exists(repo):
        shutil.rmtree(repo)
    os.makedirs(repo)
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "s@x")
    git(repo, "config", "user.name", "s")
    git(repo, "config", "core.autocrlf", "false")
    shutil.copytree(GATES, os.path.join(repo, "tools", "gates"), ignore=shutil.ignore_patterns("__pycache__"))
    cf = [mixed("cf", x) for x in LET]
    lc = [mixed("lc", x) for x in LET]
    la = [mixed("la", x) for x in LET]
    ua = [mixed("ua", x) for x in LET]
    rep = {k: [] for k in range(1, 8)}
    for n in cf:                                    # conflicts 4: token in MOD2 and MOD3 rows
        rep[2].append(n)
        rep[3].append(n)
    rep[7].append("l7t")
    rep[2].append("la_tgt")
    cyc_pairs = [(3, 4), (5, 6)]
    for i, (j, k) in enumerate(cyc_pairs):
        rep[j].append("cy%d_lo" % i)
        rep[k].append("cy%d_hi" % i)
    for k in rep:
        rep[k].sort(reverse=True)                   # tokens in reverse name order
    plan = ["# plan", "", "### N3.10 모듈", "", "| ID | 파일 | 책임 | 대표 대상 |", "|---|---|---|---|"]
    for k in range(1, 8):
        resp = "레이아웃만" if k == 7 else "책임 %d" % k
        plan.append("| MOD%d | `m%d.py` | %s | %s |" % (k, k, resp, ", ".join("`%s`" % t for t in rep[k]) or "산문"))
    plan.append("")
    regrows = []
    for n in lc:
        regrows.append((n, "m2"))                   # lift-cap-mod7: cell m2, calls MOD7 -> stays m2, upward
    for n in la:
        regrows.append((n, "m1"))                   # lift-a4: cell m1, calls MOD2 -> m2, reg_mismatch
    F = 16
    for i in range(F):
        regrows.append(("f4_%02d" % i, "m1"))       # (a) referrer in MOD1
        regrows.append(("g4_%02d" % i, "m2"))       # (a) referrer in MOD2
    regrows += [("Ext_b", "m1"), ("_ext_c", "m1")]  # (b) MOD1 import head
    regrows.sort(reverse=True)
    reg = ["# registry", "", "## 함수 표", "", "| 함수 | 이관 목적지 |", "|---|---|"] + ["| `%s` | %s |" % r for r in regrows] + [""]
    src = ['"""synthetic src."""'] + EXT_HEAD
    for n in cf:
        src += ["def %s():" % n, "    return 0", ""]
    src += ["def l7t():", "    return 7", "", "def la_tgt():", "    return 2", ""]
    for n in lc:
        src += ["def %s():" % n, "    return l7t()", ""]
    for n in la:
        src += ["def %s():" % n, "    return la_tgt()", ""]
    for i in range(len(cyc_pairs)):
        src += ["def cy%d_lo():" % i, "    return cy%d_hi()" % i, "", "def cy%d_hi():" % i, "    return cy%d_lo" % i, ""]
    for i in range(F):
        src += ["C5_%02d = %d" % (i, i), "SH_%02d = %d" % (i, i), ""]
        src += ["def f4_%02d():" % i, "    return C5_%02d + SH_%02d" % (i, i), ""]
        src += ["def g4_%02d():" % i, "    return SH_%02d" % i, ""]
    src += ["def Ext_b():", "    return JSONDecoder, dumps, sep, _osp, math.pi", "",
            "def _ext_c():", "    return Pattern, escape, Template, ascii_letters, sys.argv", ""]
    write(repo, A + "src.py", "\n".join(src) + "\n")
    iso = ['"""isolated."""', ""]
    for a, b in zip(ua[0::2], ua[1::2]):            # a7-isolated second branch: pairs calling only each other
        iso += ["def %s():" % a, "    return %s()" % b, "", "def %s():" % b, "    return %s()" % a, ""]
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
        "upward": sorted(["src.py::%s -> src.py::l7t" % n for n in lc] + ["src.py::cy%d_lo -> src.py::cy%d_hi" % (i, i) for i in range(2)]),
        "cycles": [["m%d.py" % j, "m%d.py" % k] for j, k in cyc_pairs],
        "unassigned": sorted("iso.py::" + n for n in ua),
        "conflicts": sorted("src.py::" + n for n in cf),
        "reg_mismatch_units": sorted("src.py::" + n for n in la),
        "a5": {"src.py::SH_%02d" % i: {"mod": "m1.py", "rule": "A-5"} for i in range(F)},
        "m1_imports": EXP_M1,
        "units": ["src.py::" + u for u in ["l7t", "la_tgt"] + lc + la + cf] + ["iso.py::" + u for u in ua],
    }
    commits = {"C0": c0}

    def child(tag, src_add, rows, plan_sub=None, iso_add=None):
        git(repo, "checkout", "-q", c0)
        write(repo, A + "src.py", read(repo, A + "src.py") + src_add)
        if iso_add:
            write(repo, A + "iso.py", read(repo, A + "iso.py") + iso_add)
        write(repo, "docs/reg.md", read(repo, "docs/reg.md").rstrip("\n") + "\n" + "\n".join("| `%s` | %s |" % r for r in rows) + "\n")
        if plan_sub:
            write(repo, "docs/plan.md", read(repo, "docs/plan.md").replace(*plan_sub))
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", tag)
        commits[tag] = git(repo, "rev-parse", "HEAD")
    Q = "\ndef q():\n    return 0\n"
    child("iv-a", Q, [("q", "m2"), ("q", "m5")])
    child("iv-b", Q, [("q", "m2"), ("q", "m2")])
    child("iv-c", Q, [("q", "m2"), ("q", "m5"), ("q", "m3, m6")])
    child("iv-d", Q, [("q", "m2"), ("q", "m5")], plan_sub=("| MOD3 | `m3.py` | 책임 3 | ", "| MOD3 | `m3.py` | 책임 3 | `q`, "))
    child("iv-e", "\nfrom dataclasses import dataclass\n\n@dataclass\nclass Q:\n    x: int = 0\n\ndef q_user():\n    return Q()\n",
          [("Q", "m2"), ("Q", "m5"), ("q_user", "m3")])
    child("iv-f", Q, [("q", "m2, m5"), ("q", "m3, m6")])
    child("iv-g", Q, [("q", "m2, m5"), ("q", "m2, m6")])
    child("vi", "\nfrom pa import %s\n\ndef ic_src():\n    return %s\n" % (", ".join(IC_NAMES), ", ".join(IC_NAMES)),
          [("ic_src", "m4"), ("ic_iso", "m4")],
          iso_add="\nfrom pb import %s\n\ndef ic_iso():\n    return %s\n" % (", ".join(IC_NAMES), ", ".join(IC_NAMES)))
    ic = []
    for n in IC_NAMES:
        og = [{"unit": "src.py::ic_src", "origin": ["ext", ADIR, "pa", n]}, {"unit": "iso.py::ic_iso", "origin": ["ext", ADIR, "pb", n]}]
        ic.append({"mod": "m4.py", "name": n, "origins": sorted(og, key=ek)})
    exp["import_conflicts_vi"] = sorted(ic, key=ek)
    git(repo, "checkout", "-q", c0)
    return commits, exp


ARGS = ["--plan", "docs/plan.md", "--registry", "docs/reg.md", "--split", "src.py", "iso.py", "tool.py", "--keep", "tool.py"]


def run(variant, seed, argv):
    env = dict(os.environ, MPV=variant, PYTHONHASHSEED=str(seed), PYTHONDONTWRITEBYTECODE="1", MP_STMT_KEY="names")  # contract-2 stmt key
    r = subprocess.run([PY, "-B", MP] + argv, capture_output=True, env=env)
    return r.returncode, r.stdout.decode("utf-8"), r.stderr.decode("utf-8")[-400:]


def keys_sorted_deep(v):
    if isinstance(v, dict):
        ks = list(v)
        return ks == sorted(ks) and all(keys_sorted_deep(x) for x in v.values())
    if isinstance(v, list):
        return all(keys_sorted_deep(x) for x in v)
    return True


def judge(repo, commits, exp, variant, seeds):
    res = {"variant": variant, "seeds": [seeds[0], seeds[-1]], "fail": []}
    outs = [run(variant, s, ["plan", "--root", repo, "--rev", commits["C0"]] + ARGS) for s in seeds]
    res["plan_distinct"] = len({o[1] for o in outs})
    if res["plan_distinct"] != 1:
        res["fail"].append("(i)")
    rc, so, se = outs[0]
    try:
        obj = json.loads(so)
    except Exception:
        res["fail"].append("plan not JSON rc=%d %s" % (rc, se))
        res["verdict"] = "FAIL"
        return res
    if rc != 1 or obj.get("verdict") != "FAIL":
        res["fail"].append("(i) exit/verdict %s %s" % (rc, obj.get("verdict")))
    ii = []
    top = list(obj)
    if top[:3] != ["tool", "command", "verdict"] or top[3:] != sorted(top[3:]):
        ii.append("top key order")
    if not all(keys_sorted_deep(obj[k]) for k in top):
        ii.append("nested key order")
    for k in ("upward", "cycles", "unassigned", "conflicts", "reg_mismatch"):
        L = obj.get(k, [])
        if [ek(x) for x in L] != sorted(ek(x) for x in L):
            ii.append("%s order" % k)
    if sorted(obj.get("upward", [])) != exp["upward"]:
        ii.append("upward set")
    if sorted(obj.get("cycles", [])) != exp["cycles"]:
        ii.append("cycles set")
    if sorted(obj.get("unassigned", [])) != exp["unassigned"]:
        ii.append("unassigned set")
    if sorted(c["unit"] for c in obj.get("conflicts", [])) != exp["conflicts"]:
        ii.append("conflicts set")
    if sorted(r["unit"] for r in obj.get("reg_mismatch", [])) != exp["reg_mismatch_units"]:
        ii.append("reg_mismatch set(%d)" % len(obj.get("reg_mismatch", [])))
    asg = obj.get("assignment", {})
    bad5 = [u for u, e in exp["a5"].items() if asg.get(u) != e]
    if bad5:
        ii.append("(a) A-5 %d wrong" % len(bad5))
    if obj.get("mod_imports", {}).get("m1.py") != exp["m1_imports"]:
        ii.append("(b) mod_imports m1.py")
    if ii:
        res["fail"].append("(ii) " + "; ".join(ii))
    res["sizes"] = {k: len(obj.get(k, [])) for k in ("upward", "cycles", "unassigned", "conflicts", "reg_mismatch", "import_conflicts")}
    res["assigned"] = len(asg)
    chk = ["check", "--root", repo, "--base", commits["C0"], "--head", commits["C0"], "--card", "ALL"] + ARGS
    res["check_distinct"] = len({run(variant, s, chk)[1] for s in seeds})
    if res["check_distinct"] != 1:
        res["fail"].append("(iii)")
    iv = {}
    for tag in ("iv-a", "iv-b", "iv-c", "iv-d", "iv-e", "iv-f", "iv-g"):
        rc, so, se = run(variant, 0, ["plan", "--root", repo, "--rev", commits[tag]] + ARGS)
        o = json.loads(so)
        unit = "src.py::Q" if tag == "iv-e" else "src.py::q"
        iv[tag] = [rc, o.get("verdict"), o.get("assignment", {}).get(unit), (o.get("error") or "")[:90]]
    res["iv"] = iv
    def ex2(tag, name):
        return iv[tag][0] == 2 and iv[tag][1] == "ERROR" and name in iv[tag][3]
    ivf = []
    if not ex2("iv-a", "q"): ivf.append("a")
    if iv["iv-b"][2] != {"mod": "m2.py", "rule": "A-4"}: ivf.append("b")
    if not ex2("iv-c", "q"): ivf.append("c")
    if iv["iv-d"][2] != {"mod": "m3.py", "rule": "A-1"}: ivf.append("d")
    if not ex2("iv-e", "Q"): ivf.append("e")
    if not ex2("iv-f", "q"): ivf.append("f")
    if iv["iv-g"][2] != {"mod": "m2.py", "rule": "A-3"}: ivf.append("g")
    if ivf:
        res["fail"].append("(iv-%s)" % ",".join(ivf))
    vouts = [run(variant, s, ["plan", "--root", repo, "--rev", commits["vi"]] + ARGS) for s in seeds]
    res["vi_distinct"] = len({o[1] for o in vouts})
    vo = json.loads(vouts[0][1])
    vif = []
    if res["vi_distinct"] != 1:
        vif.append("bytes")
    if vo.get("import_conflicts") != exp["import_conflicts_vi"]:
        vif.append("import_conflicts")
    if vif:
        res["fail"].append("(vi) " + ",".join(vif))
    res["verdict"] = "FAIL" if res["fail"] else "PASS"
    return res


def witness(keys, seeds):
    code = "import json,sys; print(json.dumps(list(set(json.loads(sys.argv[1])))))"
    outs = set()
    for s in seeds:
        env = dict(os.environ, PYTHONHASHSEED=str(s))
        outs.add(subprocess.run([PY, "-c", code, json.dumps(keys)], capture_output=True, text=True, env=env).stdout)
    return len(outs)


VARIANTS = ("sorted", "proto", "leak_unassigned", "leak_upward", "content", "first_row", "leak_fromorder", "key_lower",
            "key_locale", "leak_impconf", "e5_noA2", "a3_min", "a3_first", "sort_origin")

if __name__ == '__main__':
    os.makedirs(WORK, exist_ok=True)
    seeds = list(range(8))
    with open(OUT, "w", encoding="utf-8") as fh:
        repo = os.path.join(WORK, "syn_det3")
        commits, exp = build(repo)
        fh.write(json.dumps({"stage": "det3", "witness_distinct_set_orders": witness(exp["units"], seeds), "nseeds": 8}) + "\n")
        fh.flush()
        for v in (sys.argv[5].split(",") if len(sys.argv) > 5 else VARIANTS):
            r = judge(repo, commits, exp, v, seeds)
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            print(v, r["verdict"], r["fail"])
    print("done", OUT)
