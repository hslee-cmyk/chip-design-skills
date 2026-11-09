"""measure only: compare plan outputs (hash vs names key; names + variants). Writes JSON to argv[2]."""
import json
import sys

O = sys.argv[1]
OUT = sys.argv[2]
LISTS = ["upward", "cycles", "unassigned", "conflicts", "reg_mismatch", "import_time_high", "import_conflicts"]


def load(n):
    d = json.load(open("%s/plan_%s.json" % (O, n), encoding="utf-8"))
    a = d["assignment"]
    # assignment: list or dict -> map unit key (file::key) -> mod
    m = {}
    if isinstance(a, dict):
        for k, v in a.items():
            m[k] = v["mod"] if isinstance(v, dict) else v
    else:
        for e in a:
            m[e["unit"]] = e["mod"]
    return d, m


def norm(m):
    # statement keys differ between hash/names; normalize by (file, mod) multiset and by names where possible
    return m


res = {}
base_d, base_m = load("hash")
for n in ["hash", "names", "qtok", "regfix"]:
    d, m = load(n)
    r = {"verdict": d["verdict"], "counts": {k: len(d.get(k, [])) for k in LISTS},
         "upward": d.get("upward"), "cycles": d.get("cycles"), "n_assigned": len(m)}
    per_mod = {}
    for u, mod in m.items():
        per_mod[mod] = per_mod.get(mod, 0) + 1
    r["per_mod"] = dict(sorted(per_mod.items()))
    r["mod1_units"] = sorted(u for u, mod in m.items() if mod == "gmid_lut.py")
    res[n] = r
# diffs among names-key runs (same key space)
_, mn = load("names")
for n in ["qtok", "regfix"]:
    _, mv = load(n)
    res[n]["diff_vs_names"] = sorted("%s: %s -> %s" % (u, mn.get(u), mv.get(u)) for u in set(mn) | set(mv) if mn.get(u) != mv.get(u))
# hash vs names: compare by statement units whose names-key contains identifiers; map via mod multiset per file
_, mh = load("hash")
hn = {}
for u, mod in mh.items():
    hn.setdefault(u, mod)
res["hash_vs_names_nonstmt_diff"] = sorted("%s: %s -> %s" % (u, mh.get(u), mn.get(u)) for u in set(mh) & set(mn) if mh[u] != mn[u])
res["hash_only_keys"] = len(set(mh) - set(mn))
res["names_only_keys"] = len(set(mn) - set(mh))
# per-mod count delta
pm_h, pm_n = res["hash"]["per_mod"], res["names"]["per_mod"]
res["per_mod_delta_hash_to_names"] = {k: pm_n.get(k, 0) - pm_h.get(k, 0) for k in sorted(set(pm_h) | set(pm_n)) if pm_n.get(k, 0) != pm_h.get(k, 0)}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: (v["counts"], v["n_assigned"], v["per_mod"]) if isinstance(v, dict) and "counts" in v else v for k, v in res.items()}, ensure_ascii=False, indent=1)[:6000])
