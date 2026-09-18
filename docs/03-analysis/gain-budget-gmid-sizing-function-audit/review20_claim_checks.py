import json, os, itertools, collections
import engine as E, analysis as A
fn = os.path.join(E.SP, "results6_claims.jsonl"); open(fn, "w").close()
def w(row):
    open(fn, "a", encoding="utf-8").write(json.dumps(row, ensure_ascii=False) + "\n"); print(row)
# (c) rule1(4) without condition (0): candidates among all non-acg nets (not only signal nets)
for c in E.circuits():
    acg0, _ = E.base_acg(c)
    net_sym, _ = E.symmetry_map(c)
    excite = c["ins"]
    R0 = E.reach(c, acg0, excite)
    nets = E.all_nets(c) - acg0 - set(excite)
    orig = E.reach
    # emulate: treat every net as 'signal' for condition (0) by temporarily evaluating predicate on all nets
    cnt = 0; hits = []
    for b in sorted(nets):
        if any(m["s"] == b for m in c["devs"]): continue
        if any(b in (p["a"], p["b"]) for p in c["pas"]): continue
        drivers = [m for m in c["devs"] if m["d"] == b or m["s"] == b]
        selfc = [m for m in drivers if m["g"] == b]
        bad = [m for m in drivers if m["g"] != b and m["g"] in R0]
        if bad or not selfc: continue
        Rb = E.reach(c, acg0 | {b}, excite)
        ok = False
        for m in selfc:
            fr = [m["s"] if m["d"] == b else m["d"]]; seen = set()
            while fr and not ok:
                n = fr.pop(0)
                if n in seen or n == b or n in acg0: continue
                seen.add(n)
                if n in Rb: ok = True; break
                for u in c["devs"]:
                    if u["d"] == n: fr.append(u["s"])
        hits.append((b, ok))
    w(dict(check="rule1_4_without_cond0", circuit=c["name"], cand_i_ii=[h[0] for h in hits], with_iii=[h[0] for h in hits if h[1]]))
# (a) merge-order claim: count circuits with any merge node when (a) judged first
for c in E.circuits():
    r1, ctx = E.run(c, {"pcost": 0})
    merges = r1["merges"]
    w(dict(check="merge_nodes", circuit=c["name"], merges=[(m["node"], m["kind"]) for m in merges]))
# no mirror-merge branch: how many circuits get residual (multi-input) merges
for c in E.circuits():
    r1, ctx = E.run(c, {"pcost": 0, "mirror_merge": "none"})
    w(dict(check="no_mirror_merge", circuit=c["name"], residual=[m["node"] for m in r1["merges"] if m["kind"] == "residual"]))
