"""measure only (NOT a role artifact): contract 3 (a)(b)(c) of the M-card drafts as an ast.dump sequence comparison.
    python -B c3.py <root> <base> <head> <card stem> <plan_base.json> <gates dir>
(a) two readings of the MOD file statement list:
    corrected = [mod_imports lines that are NOT D-22 (2) targets] + moved units (TL->SD->SR->DR->ACF, file order) + [D-22 (2) target lines]
    literal   = [all mod_imports lines]                             + moved units                                + [D-22 (2) target lines]
(b) every split file that lost units: base body - moved units + one re-export ImportFrom after the last import of the head bundle
    -- the head bundle is taken in the BASE file (before the units are removed; review r1 N-1): a mid-file import that becomes
    adjacent to the head only after the removal is not part of the bundle
    (SD = MOD7 with card number > 7: at the file end); complete shim = docstring + __future__ + base N3.10 re-export lines + the new one.
(c) first statement of the MOD file is `from __future__ import annotations`.
Prints one JSON line."""
import ast
import json
import subprocess
import sys

ROOT, BASE, HEAD, CARD, PLAN, GC = sys.argv[1:7]
sys.path.insert(0, GC)
import import_layering as il  # noqa: E402
import reachability as rch    # noqa: E402

A = "skills/analog-gmid-design/assets/"
CF = CARD + ".py"
KEEP = ["audit_current_forced.py"]
INIT_ORDER = ["topology_library.py", "stick_diagram.py", "sizing_recipe.py", "design_report.py", "audit_current_forced.py"]
plan = json.load(open(PLAN, encoding="utf-8"))


def show(rev, rel):
    r = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (rev, rel)], capture_output=True)
    return None if r.returncode else r.stdout.decode("utf-8").replace("\r\n", "\n")


modtab = il.mod_table(show(BASE, "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"))
n310 = {s + ".py": k for s, k in modtab.items()}
k_card = n310[CF]
files = rch.read_tree(ROOT, BASE, rch.SOURCE_GLOBS)
idx = rch.SourceIndex({k: v for k, v in files.items() if rch._is_source(k)})
units = []
for uid, a in plan["assignment"].items():
    if a["mod"] != CF:
        continue
    f, key = uid.split("::", 1)
    key = key.split("#")[0]
    if f == CF:
        continue
    m = idx.mod(A + f)
    hit = [(n, b) for (k, q, h, n, b) in m.units if (q if q else "<stmt:%s>" % h[:12]) == key
           or (k == "stmt" and ",".join(sorted(b)) == key)]
    assert len(hit) == 1, uid
    units.append((f, hit[0][0], hit[0][1]))
units.sort(key=lambda u: (INIT_ORDER.index(u[0]) if u[0] in INIT_ORDER else 99, u[1].lineno))


def d(n):
    return ast.dump(n)


def parse1(line):
    return ast.parse(line).body[0]


def is_d22(line):
    if line.startswith("from __future__"):
        return False
    mod = line.split()[1].split(".")[0] + ".py"
    return k_card >= 8 and mod in n310 and n310[mod] >= 7


mi = plan["mod_imports"].get(CF, [])
tail = [parse1(l) for l in mi if is_d22(l)]
unit_dumps = [d(u[1]) for u in units]
exp_corr = [d(parse1(l)) for l in mi if not is_d22(l)] + unit_dumps + [d(n) for n in tail]
exp_lit = [d(parse1(l)) for l in mi] + unit_dumps + [d(n) for n in tail]
head_mod = show(HEAD, A + CF)
got = [d(n) for n in ast.parse(head_mod).body] if head_mod is not None else []


def first_diff(x, y):
    for i, (p, q) in enumerate(zip(x, y)):
        if p != q:
            return i
    return None if len(x) == len(y) else min(len(x), len(y))


out = {"card": CARD, "head": HEAD, "n_units": len(units), "n_tail": len(tail),
       "a_corrected": got == exp_corr, "a_corrected_first_diff": first_diff(got, exp_corr),
       "a_literal": got == exp_lit, "a_literal_first_diff": first_diff(got, exp_lit),
       "c_future_first": bool(got) and got[0] == d(parse1("from __future__ import annotations"))}
b = {}
per = {}
for f, n, bn in units:
    per.setdefault(f, []).append((n, bn))
for f, lst in per.items():
    t = show(BASE, A + f)
    tree = ast.parse(t)
    gone = {n.lineno for n, _ in lst}
    names = sorted(set().union(*[set(bn) for _, bn in lst]))
    rex = ast.ImportFrom(module=CARD, names=[ast.alias(name=x) for x in names], level=0)
    body = tree.body
    has_doc = bool(body) and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str)
    remaining = [n for n in body if n.lineno not in gone and not isinstance(n, (ast.Import, ast.ImportFrom)) and not (has_doc and n is body[0])]
    if f not in n310 and f not in KEEP and not remaining:
        exp = ([body[0]] if has_doc else []) + [n for n in body if isinstance(n, ast.ImportFrom) and n.module == "__future__"] + \
              [n for n in body if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module and (n.module + ".py") in n310] + [rex]
        kind = "complete-shim"
    else:
        keep = [n for n in body if n.lineno not in gone]
        if f in n310 and n310[f] == 7 and k_card > 7:
            exp = keep + [rex]
            kind = "tail"
        else:
            # head bundle in the BASE body (units not yet removed -- review r1 N-1)
            last_node = None
            for i, n in enumerate(body):
                if i == 0 and has_doc:
                    continue
                if isinstance(n, (ast.Import, ast.ImportFrom)):
                    last_node = n
                    continue
                if (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute)
                        and ast.unparse(n.value.func).startswith("sys.path.")):
                    continue
                break
            assert last_node is None or last_node.lineno not in gone, (f, "head-bundle import is a moved unit")
            last = -1 if last_node is None else next(i for i, n in enumerate(keep) if n is last_node)
            exp = keep[:last + 1] + [rex] + keep[last + 1:]
            kind = "head"
    h = show(HEAD, A + f)
    g = [d(n) for n in ast.parse(h).body]
    e = [d(n) for n in exp]
    b[f] = {"kind": kind, "match": g == e, "first_diff": first_diff(g, e), "n_got": len(g), "n_exp": len(e)}
out["b"] = b
out["b_all"] = all(v["match"] for v in b.values())
print(json.dumps(out, ensure_ascii=False))
