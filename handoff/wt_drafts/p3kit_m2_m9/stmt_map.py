"""measure only: map statement units between hash keys (<stmt:...>) and names keys on clone R at rev, then report
statement units whose MOD differs between plan_hash.json and plan_names.json (and the registry rows they match).
    python -B stmt_map.py <clone root> <rev> <out dir> <out json>"""
import json
import os
import sys

R, REV, O, OUT = sys.argv[1:5]
sys.path.insert(0, os.path.join(R, "tools", "gates"))
import reachability as rch  # noqa: E402

A = "skills/analog-gmid-design/assets/"
files = rch.read_tree(R, REV, rch.SOURCE_GLOBS)
idx = rch.SourceIndex({k: v for k, v in files.items() if rch._is_source(k)})
ph = json.load(open(O + "/plan_hash.json", encoding="utf-8"))["assignment"]
pn = json.load(open(O + "/plan_names.json", encoding="utf-8"))["assignment"]
rows = []
for f in ["sizing_recipe.py", "stick_diagram.py", "topology_library.py", "design_report.py", "audit_current_forced.py"]:
    if (A + f) not in files:
        continue
    mod = idx.mod(A + f)
    for (kind, q, h, bound), raw in zip(idx.units(A + f), mod.units):
        if kind != "stmt" or not bound:
            continue
        hk = "%s::%s" % (f, q)
        nk = "%s::%s" % (f, ",".join(sorted(bound)))
        a, b = ph.get(hk), pn.get(nk)
        if a is None or b is None:
            continue
        if a["mod"] != b["mod"]:
            rows.append({"file": f, "line": raw[3].lineno, "names": nk, "hash_key": hk,
                         "hash": a, "names_key_assign": b})
json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for r in rows:
    print(r["file"], r["line"], r["names"], r["hash"], "->", r["names_key_assign"])
print("changed", len(rows))
