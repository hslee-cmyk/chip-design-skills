"""measure only (NOT a role artifact): T1 prototype -- unit/test_selftest_<old>.py x4 -> unit/test_mod<k>_<stem>.py by t1_map R2c
(fallback: the old file's engine module's MOD for tests with no engine reference -- TL s011 -> MOD4).

    python -B gen_t1.py <root (checked out at T1 base)> <t1_map.json> <out report.json>

* each test function / fixture / helper keeps its source bytes (decorators..end_lineno);
* fixture/helper whose users (transitive) land in one target -> that target file; users in >= 2 targets -> unit/_selftest_shared.py
  (imported by name into each target that needs it);
* fixture-name collision inside one target (different origins) -> the later origin's fixture is renamed <name>__<old> together with the
  parameter names of its users in that target (reported);
* module header of each target = header statements (non-def, non-docstring) of every origin present, verbatim, de-duplicated by exact
  text; a name bound by two different header statements is reported as a conflict;
* contracts/test_ts3_no_print_verdicts.py `_LEGACY_SCRIPTS` = the new test_mod files; old files deleted;
* docstring references `unit/test_selftest_<old>.py::<test>` in other tests' docstrings rewritten to the new id (reported)."""
import ast
import collections
import json
import os
import re
import sys

ROOT, MAP, REP = sys.argv[1:4]
A = os.path.join(ROOT, "skills", "analog-gmid-design", "assets")
U = os.path.join(A, "tests", "unit")
OLD = ["sizing_recipe", "stick_diagram", "design_report", "topology_library"]
FALLBACK = {"topology_library": 4}
m = json.load(open(MAP, encoding="utf-8"))
mods = m["mods"]
stem_of = {k: s for s, k in mods.items()}
tgt_of = {}
for key, v in m["tests"].items():
    old, name = key.split("::")
    tgt_of[(old, name)] = v["k"] if "k" in v else (v["R2c"] if v["R2c"] is not None else FALLBACK[old])

src, tree, lines, funcs, header = {}, {}, {}, {}, {}
for old in OLD:
    p = os.path.join(U, "test_selftest_%s.py" % old)
    s = open(p, encoding="utf-8", newline="").read()
    assert "\r\n" not in s
    src[old] = s
    lines[old] = s.split("\n")
    t = ast.parse(s)
    tree[old] = t
    funcs[old] = {n.name: n for n in t.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    hdr = []
    for i, n in enumerate(t.body):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if i == 0 and isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant):
            continue
        hdr.append(n)
    header[old] = hdr


def seg(old, n):
    start = (n.decorator_list[0].lineno if getattr(n, "decorator_list", None) else n.lineno)
    return "\n".join(lines[old][start - 1:n.end_lineno])


def deps(old, name):
    fn = funcs[old][name]
    params = [a.arg for a in fn.args.args + fn.args.kwonlyargs]
    names = {x.id for x in ast.walk(fn) if isinstance(x, ast.Name)}
    return [d for d in params if d in funcs[old]] + [d for d in names if d in funcs[old] and d != name and not d.startswith("test")]


users = collections.defaultdict(set)   # (old, fixture/helper) -> {targets}
for (old, name), k in tgt_of.items():
    seen, st = set(), list(deps(old, name))
    while st:
        d = st.pop()
        if d in seen:
            continue
        seen.add(d)
        st += deps(old, d)
    for d in seen:
        users[(old, d)].add(k)
place = {}
for (old, d), ks in users.items():
    place[(old, d)] = "shared" if len(ks) > 1 else next(iter(ks))
unused = [(o, n) for o in OLD for n in funcs[o] if not n.startswith("test") and (o, n) not in place]

files = collections.defaultdict(lambda: {"origins": [], "defs": [], "imports_shared": set()})
for old in OLD:
    for n in tree[old].body:
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if n.name.startswith("test"):
            k = tgt_of[(old, n.name)]
        elif (old, n.name) in place:
            k = place[(old, n.name)]
        else:
            continue
        f = files[k]
        if old not in f["origins"]:
            f["origins"].append(old)
        f["defs"].append((old, n.name))
for k, f in files.items():
    if k == "shared":
        continue
    for old, name in f["defs"]:
        for d in deps(old, name):
            if place.get((old, d)) == "shared":
                f["imports_shared"].add((old, d))
# transitive shared deps imported too
for k, f in files.items():
    if k == "shared":
        continue
    st = list(f["imports_shared"])
    while st:
        o, d = st.pop()
        for dd in deps(o, d):
            if place.get((o, dd)) == "shared" and (o, dd) not in f["imports_shared"]:
                f["imports_shared"].add((o, dd))
                st.append((o, dd))

report = {"files": {}, "renames": [], "header_conflicts": {}, "unused_defs": unused, "docstring_refs": []}
rename = {}
for k, f in files.items():
    seen = {}
    for old, name in f["defs"] + sorted(f["imports_shared"]):
        if name.startswith("test"):
            continue
        if name in seen and seen[name] != old:
            rename[(k, old, name)] = "%s__%s" % (name, old)
            report["renames"].append([str(k), old, name, rename[(k, old, name)]])
        else:
            seen.setdefault(name, old)


def fname(k):
    return "_selftest_shared.py" if k == "shared" else "test_mod%d_%s.py" % (k, stem_of[k])


for k, f in sorted(files.items(), key=lambda kv: str(kv[0])):
    out = ['"""T1(design 30-module-split §8, card p3-test-relocate): unit/test_selftest_<모듈>.py 의 test를 N3.10 MOD%s로 재배치(본문 그대로).\n"""'
           % ("(공유 fixture)" if k == "shared" else k)]
    hdr_txt, bound = [], {}
    for old in f["origins"]:
        for n in header[old]:
            t = "\n".join(lines[old][n.lineno - 1:n.end_lineno])
            if t in hdr_txt:
                continue
            names = set()
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                names = {a.asname or a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.Assign):
                names = {x.id for tg in n.targets for x in ast.walk(tg) if isinstance(x, ast.Name)}
            for nm in names:
                if nm in bound and bound[nm] != t:
                    report["header_conflicts"].setdefault(fname(k), []).append(nm)
                bound[nm] = t
            hdr_txt.append(t)
    out += hdr_txt
    if f["imports_shared"]:
        out.append("from _selftest_shared import %s  # noqa: E402,F401" % ", ".join(sorted({d for _, d in f["imports_shared"]})))
    body = []
    for old, name in f["defs"]:
        s = seg(old, funcs[old][name])
        rn = {nm: nn for (kk, oo, nm), nn in rename.items() if kk == k and oo == old}
        for a, b in rn.items():
            s = re.sub(r"\b%s\b" % re.escape(a), b, s)
        body.append(s)
    text = "\n".join(out) + "\n\n\n" + "\n\n\n".join(body) + "\n"
    ast.parse(text)
    open(os.path.join(U, fname(k)), "w", encoding="utf-8", newline="\n").write(text)
    report["files"][fname(k)] = {"tests": sum(1 for _, n in f["defs"] if n.startswith("test")),
                                 "fixtures_helpers": sum(1 for _, n in f["defs"] if not n.startswith("test")),
                                 "origins": f["origins"], "imports_shared": sorted(d for _, d in f["imports_shared"])}
for old in OLD:
    os.remove(os.path.join(U, "test_selftest_%s.py" % old))
# C group
ts3 = os.path.join(A, "tests", "contracts", "test_ts3_no_print_verdicts.py")
t3 = open(ts3, encoding="utf-8", newline="").read()
newlist = sorted(fname(k) for k in files if k != "shared")
old_lit = re.search(r"_LEGACY_SCRIPTS = \((.|\n)*?\)\n", t3).group(0)
new_lit = "_LEGACY_SCRIPTS = (" + ",\n                   ".join('"unit/%s"' % x for x in newlist) + ")\n"
t3 = t3.replace(old_lit, new_lit)
open(ts3, "w", encoding="utf-8", newline="").write(t3)
# id map + docstring refs
idmap = {}
for (old, name), k in tgt_of.items():
    idmap["unit/test_selftest_%s.py::%s" % (old, name)] = "unit/%s::%s" % (fname(k), name)
for dp, _, fs in os.walk(os.path.join(A, "tests")):
    for fn_ in fs:
        if not fn_.endswith(".py"):
            continue
        p = os.path.join(dp, fn_)
        s = open(p, encoding="utf-8", newline="").read()
        s2 = s
        for o, n in idmap.items():
            if o in s2:
                s2 = s2.replace(o, n)
                report["docstring_refs"].append([os.path.relpath(p, A).replace("\\", "/"), o, n])
        if s2 != s:
            open(p, "w", encoding="utf-8", newline="").write(s2)
report["id_map"] = idmap
report["legacy_scripts"] = newlist
json.dump(report, open(REP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in report.items() if k not in ("id_map",)}, ensure_ascii=False)[:3000])
