"""measure only (NOT a role artifact): T1 head vs base -- contracts 2/3/4 and the S-3 reading of R-4.
    python -B t1_verify.py <repo> <base> <head> <t1_map.json> <out.json>"""
import ast
import collections
import json
import re
import subprocess
import sys

R, B, H, MAP, OUT = sys.argv[1:6]
U = "skills/analog-gmid-design/assets/tests/unit/"
OLD = ["sizing_recipe", "stick_diagram", "design_report", "topology_library"]


def show(rev, p):
    r = subprocess.run(["git", "-C", R, "show", "%s:%s" % (rev, p)], capture_output=True)
    return r.stdout.decode("utf-8") if r.returncode == 0 else None


m = json.load(open(MAP, encoding="utf-8"))
stem_of = {k: s for s, k in m["mods"].items()}
base_defs = collections.defaultdict(dict)   # name -> {old: dump}
for o in OLD:
    for n in ast.parse(show(B, U + "test_selftest_%s.py" % o)).body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            base_defs[n.name][o] = ast.dump(n)
ls = subprocess.run(["git", "-C", R, "ls-tree", "--name-only", H, U], capture_output=True).stdout.decode().split()
new = [p for p in ls if re.search(r"/(test_mod\d+_[a-z_]+|_selftest_shared)\.py$", p)]
placed = collections.defaultdict(list)   # (old, name) -> [file]
in_file = collections.defaultdict(collections.Counter)
mismatch, unmatched, renamed_users = [], [], []
for p in new:
    f = p.rsplit("/", 1)[-1]
    for n in ast.parse(show(H, p)).body:
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        in_file[f][n.name] += 1
        name, d = n.name, ast.dump(n)
        mm = re.match(r"(.+)__(%s)$" % "|".join(OLD), name)
        if mm:  # contract 5 rename: undo the token and compare
            name = mm.group(1)
            src = ast.unparse(n)
            d = ast.dump(ast.parse(re.sub(r"\b%s\b" % re.escape(n.name), name, src)).body[0])
            # compare via unparse round-trip on both sides (rename path only)
            cands = {}
            for o in OLD:
                for bn in ast.parse(show(B, U + "test_selftest_%s.py" % o)).body:
                    if isinstance(bn, (ast.FunctionDef, ast.AsyncFunctionDef)) and bn.name == name:
                        cands[o] = ast.dump(ast.parse(ast.unparse(bn)).body[0])
        else:
            cands = base_defs.get(name, {})
        origin = [o for o, bd in cands.items() if bd == d]
        if not origin and re.search(r"\b\w+__(%s)\b" % "|".join(OLD), ast.unparse(n)):
            # contract 5: a user of a renamed fixture -- undo the token(s), compare by unparse round-trip
            src2 = re.sub(r"\b(\w+?)__(%s)\b" % "|".join(OLD), r"\1", ast.unparse(n))
            d2 = ast.dump(ast.parse(src2).body[0])
            for o in OLD:
                for bn in ast.parse(show(B, U + "test_selftest_%s.py" % o)).body:
                    if isinstance(bn, (ast.FunctionDef, ast.AsyncFunctionDef)) and bn.name == name and ast.dump(ast.parse(ast.unparse(bn)).body[0]) == d2:
                        origin.append(o)
                        renamed_users.append([f, name, o])
        if not origin:
            (mismatch if cands else unmatched).append([f, n.name])
            continue
        for o in origin:
            placed[(o, name)].append(f)
moved_tests = {k: v for k, v in placed.items() if k[1].startswith("test")}
dup_origin = {"%s:%s" % k: v for k, v in placed.items() if len(v) > 1}
wrong_k = []
for key, v in m["tests"].items():
    o, n = key.split("::")
    fs = placed.get((o, n), [])
    if fs != ["test_mod%d_%s.py" % (v["k"], stem_of[v["k"]])]:
        wrong_k.append([key, fs, v["k"]])
within = {f: sorted(x for x, c in cnt.items() if c > 1) for f, cnt in in_file.items() if any(c > 1 for c in cnt.values())}
across = collections.defaultdict(set)
for f, cnt in in_file.items():
    for x in cnt:
        across[x].add(f)
same_name_multi_file = {x: sorted(fs) for x, fs in across.items() if len(fs) > 1}
base_missing = [k for k in ((o, n) for n, d in base_defs.items() for o in d) if k not in placed]
res = {"new_files": sorted(p.rsplit("/", 1)[-1] for p in new), "defs_placed": len(placed), "tests_placed": len(moved_tests),
       "ast_mismatch": mismatch, "unmatched_new_defs": unmatched, "base_defs_not_placed": base_missing,
       "same_origin_in_2plus_files": dup_origin, "within_file_name_clash": within,
       "same_name_in_2plus_files_tests": sorted(x for x in same_name_multi_file if x.startswith("test")),
       "same_name_in_2plus_files_nontest": {x: v for x, v in same_name_multi_file.items() if not x.startswith("test")},
       "wrong_k": wrong_k, "renamed_token_users": renamed_users}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: (v if not isinstance(v, list) or len(v) < 15 else len(v)) for k, v in res.items()}, ensure_ascii=False))
