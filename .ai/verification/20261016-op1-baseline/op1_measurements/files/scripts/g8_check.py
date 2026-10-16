"""T1-0 dry run: every draft token must hit the baseline netlists or old-code literals; none may hit core vocabulary words alone.
Also records per-file hit counts on old literals (what T1-1 would flag if the code were moved to core unchanged)."""
import json, re, glob, os, collections
B = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1"
TOK = json.load(open(B + "/g8_dialect_tokens.draft.json", encoding="utf-8"))
LIT = json.load(open(B + "/results/g8_old_literals.json", encoding="utf-8"))
OUT = B + "/results/g8_check.json"
regs = {t["id"]: re.compile(t["regex"]) for t in TOK["tokens"]}

nets = [p for p in glob.glob(B + "/baseline/**/*.cir", recursive=True)]
net_hits = collections.Counter()
for p in nets:
    txt = open(p, encoding="utf-8", errors="replace").read()
    for k, r in regs.items():
        if r.search(txt):
            net_hits[k] += 1
lit_hits = {k: collections.Counter() for k in regs}
examples = {k: [] for k in regs}
for f, L in LIT.items():
    for ln, s in L:
        for k, r in regs.items():
            if r.search(s):
                lit_hits[k][f] += 1
                if len(examples[k]) < 4:
                    examples[k].append(f"{f}:{ln}: {s[:70]!r}")
vocab_hits = {w: [k for k, r in regs.items() if r.search(w)] for w in TOK["not_tokens_core_vocabulary"]}
res = {"n_netlists": len(nets), "netlist_files_hit": dict(net_hits),
       "literal_hits_per_file": {k: dict(v) for k, v in lit_hits.items()}, "examples": examples,
       "core_vocab_false_hits": vocab_hits,
       "tokens_with_no_hit_anywhere": [k for k in regs if net_hits[k] == 0 and not lit_hits[k]]}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("n_netlists", "netlist_files_hit", "core_vocab_false_hits", "tokens_with_no_hit_anywhere")}, ensure_ascii=False))
for k in regs:
    print(k, dict(lit_hits[k]), examples[k][:2])
