"""Sandbox only (det3 author kit, measure only -- NOT a role artifact): copy move_plan_sim.py -> mp.py with env MPV variants.
MPV =
  proto          : prototype as is (no canonical output, no (e5)/(e6), first registry row)
  sorted         : canonical output per contract 2 'determinism' (det3: origin values kept as is) + (e5) (scope incl. A-2) + (e6)
  leak_unassigned: sorted, but `unassigned` emitted in set iteration order
  leak_upward    : sorted, but `upward` emitted as list(set)
  content        : sorted output, but A-5 base = first referencer in set iteration (content nondeterministic)
  first_row      : sorted output, no (e5)/(e6) -- A-4 reads the first single-MOD row, A-3 the first A-3 row
  leak_fromorder : sorted, but mod_imports `from` lines in set iteration order of modules
  key_lower      : sorted, but element sort key = str.lower (case-insensitive)
  key_locale     : sorted, but element sort key = lower + punctuation removed (locale/ICU-like)
  leak_impconf   : sorted, but import_conflicts in set iteration order
  e5_noA2        : sorted, but (e5) skips A-2 units (record class with referencers)
  a3_min         : sorted + (e5), no (e6) -- several A-3 rows -> min of the minima (prototype)
  a3_first       : sorted + (e5), no (e6) -- several A-3 rows -> first A-3 row
  sort_origin    : sorted, but origin tuples (JSON lists) are element-sorted too (det2 literal reading)
usage: python mk_mp3.py <src move_plan_sim.py> <dst mp.py>
"""
import sys

src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding="utf-8").read()


def sub(old, new):
    global t
    assert t.count(old) == 1, old[:60]
    t = t.replace(old, new)


sub('A = "skills/analog-gmid-design/assets/"', 'A = "skills/analog-gmid-design/assets/"\nMPV = os.environ.get("MPV", "proto")')

# (e5)/(e6) -- before A-2/A-3/A-4, only for units not decided by A-0/A-1 and not A-1 conflicts
sub("""        ms = regmods.get(U[uid]["key"])
        others = referencers[uid] - {uid}
""", """        ms = regmods.get(U[uid]["key"])
        others = referencers[uid] - {uid}
        if MPV not in ("proto", "first_row") and ms and not (MPV == "e5_noA2" and uid in rec and others):
            singles = sorted({next(iter(m)) for m in ms if len(m) == 1})
            if len(singles) > 1:
                err("(e5) %s::%s single-MOD cells differ: %s" % (U[uid]["file"], U[uid]["key"], [modfile[k] for k in singles]))
        if MPV not in ("proto", "first_row", "a3_min", "a3_first") and ms:
            a3lo = sorted({min(m) for m in ms if len(m) >= 2})
            if len(a3lo) > 1:
                err("(e6) %s::%s A-3 rows with different lowest MODs: %s" % (U[uid]["file"], U[uid]["key"], [modfile[k] for k in a3lo]))
""")

# A-3 row choice
sub("""            lo = min(min(m) for m in ms if len(m) >= 2)
""", """            lo = min([m for m in ms if len(m) >= 2][0]) if MPV in ("a3_first", "first_row", "proto_first") else min(min(m) for m in ms if len(m) >= 2)
""")

# content variant: A-5 picks first referencer in set iteration order
sub("""                base = min(cand)
""", """                base = cand[0] if (MPV == "content" and r_ == "A-5") else min(cand)
""")

# leak_upward
sub("""    upward = sorted({"%s -> %s" % (u_, v) for u_ in assign for v in R[u_] if v in assign and assign[u_] < assign[v]})
""", """    upward = sorted({"%s -> %s" % (u_, v) for u_ in assign for v in R[u_] if v in assign and assign[u_] < assign[v]})
    if MPV == "leak_upward":
        upward = list({"%s -> %s" % (u_, v) for u_ in assign for v in R[u_] if v in assign and assign[u_] < assign[v]})
""")

# leak_unassigned
sub("""    unassigned = sorted(uid for uid in targets if uid not in assign and uid not in conflict_units)
""", """    unassigned = sorted(uid for uid in targets if uid not in assign and uid not in conflict_units)
    if MPV == "leak_unassigned":
        unassigned = [uid for uid in targets if uid not in assign and uid not in conflict_units]
""")

# leak_fromorder
sub("""        for m in sorted(frm):
            lines.append""", """        for m in (list(set(frm)) if MPV == "leak_fromorder" else sorted(frm)):
            lines.append""")

# leak_impconf
sub("""    rule_counts = {}
    for uid in assign:""", """    if MPV == "leak_impconf":
        import_conflicts = [json.loads(s) for s in {json.dumps(x, sort_keys=True) for x in import_conflicts}]
    rule_counts = {}
    for uid in assign:""")

# canonical emit
sub('''def emit(obj, code):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\\n")
    sys.exit(code)
''', '''ORDERED_TOP = ("order",)            # contract-ordered lists (kept as generated)
ORDERED_UNDER = ("mod_imports", "reexports")
ORIGIN_KEYS = ("origin", "base", "head")   # binding_origin tuples: positional values, not lists (det3 m-c)


def _sk(s):
    if MPV == "key_lower":
        return (s.lower(), s)
    if MPV == "key_locale":
        import re as _re
        return (_re.sub(r"[^0-9a-z]", "", s.lower()), s)
    return (s,)


def _ek(x):
    if isinstance(x, str):
        return (0, _sk(x), 0)
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return (1, ("",), x)
    return (2, _sk(json.dumps(x, sort_keys=True, ensure_ascii=False)), 0)


def _canon(v, path):
    if isinstance(v, dict):
        return {k: _canon(v[k], path + (k,)) for k in sorted(v)}
    if isinstance(v, list):
        items = [_canon(x, path + ("[]",)) for x in v]
        keep = (path in ((p,) for p in ORDERED_TOP)) or (len(path) == 2 and path[0] in ORDERED_UNDER)
        if path and path[-1] in ORIGIN_KEYS and MPV != "sort_origin":
            keep = True
        if MPV == "leak_unassigned" and path == ("unassigned",):
            keep = True
        if MPV == "leak_upward" and path == ("upward",):
            keep = True
        if MPV == "leak_impconf" and path == ("import_conflicts",):
            keep = True
        return items if keep else sorted(items, key=_ek)
    return v


def emit(obj, code):
    if MPV != "proto" and obj.get("verdict") != "ERROR":
        obj = dict(obj)
        obj.pop("rule_counts_sim", None)
        out = {k: obj[k] for k in ("tool", "command", "verdict")}
        for k in sorted(k for k in obj if k not in out):
            out[k] = _canon(obj[k], (k,))
        obj = out
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\\n")
    sys.exit(code)
''')
open(dst, "w", encoding="utf-8", newline="\n").write(t)
print("ok", dst)
