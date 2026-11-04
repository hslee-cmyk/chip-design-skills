"""Independent re-count of the real tree (no import of structure_checks). usage: python -I indep_count.py <engine dir> <out json>
Grep-level regex plus own AST walk, compared to the tool output by hand."""
import ast, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

E, out = Path(sys.argv[1]), Path(sys.argv[2])
ALLOW = {"core/graph_snapshot.py", "core/compute_block.py", "core/projection.py", "core/graft.py", "core/donors.py",
         "core/field_value.py", "core/graph_record.py", "core/writer_table.py", "lut/lut_memo.py", "lut/table_cache.py",
         "core/bounded_lru.py", "search/archive.py", "search/s3_index.py", "core/run_counters.py"}
MUT = {"dict", "list", "set", "bytearray", "defaultdict", "OrderedDict", "Counter", "deque", "ChainMap",
       "WeakValueDictionary", "WeakKeyDictionary", "WeakSet"}
files = [p for p in sorted(E.rglob("*.py")) if p.relative_to(E).parts[0] != "tests"
         and "__pycache__" not in p.parts and not any(x.startswith(".") for x in p.relative_to(E).parts)]
rx = {"id_call": r"(?<![\w.])id\(", "cached_property": r"cached_property", "default_factory": r"default_factory\s*=\s*(dict|list|set)\b",
      "any_default_factory": r"default_factory\s*=", "lru_cache": r"\blru_cache\b", "functools_cache": r"\bfunctools\.cache\b|(?<![\w.])cache\(",
      "memo_call": r"memo\.call\(", "memo_lookup": r"memo\.(lookup|lookup_persistent)\(", "any_lookup": r"\.(lookup|lookup_persistent)\(",
      "module_cache_ctor": r"^\s*\w[\w, ]*=\s*[\w.]*(BoundedLRU|LutMemo|OrderedDict|WeakValueDictionary)\("}
grep = defaultdict(list)
near = Counter()


def mut(v):
    if isinstance(v, (ast.Dict, ast.List, ast.Set, ast.DictComp, ast.ListComp, ast.SetComp)):
        return True
    if isinstance(v, ast.Tuple):
        return any(mut(x) for x in v.elts)
    if isinstance(v, ast.Call):
        f = v.func
        return (f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")) in MUT
    return False


ast_counts = Counter()
near_rows = defaultdict(list)
frozen, non_frozen_annot = set(), []
trees = {}
for p in files:
    r = p.relative_to(E).as_posix()
    src = p.read_text(encoding="utf-8")
    trees[r] = ast.parse(src)
    if r in ALLOW:
        continue
    for i, line in enumerate(src.splitlines(), 1):
        code = line.split("#", 1)[0]
        for k, pat in rx.items():
            if re.search(pat, code):
                grep[k].append("%s:%d:%s" % (r, i, line.strip()[:110]))
for r, t in trees.items():
    for n in ast.walk(t):
        if isinstance(n, ast.ClassDef):
            for d in n.decorator_list:
                if isinstance(d, ast.Call) and getattr(d.func, "id", getattr(d.func, "attr", "")) == "dataclass":
                    if any(k.arg == "frozen" and getattr(k.value, "value", None) is True for k in d.keywords):
                        frozen.add(n.name)
for r, t in trees.items():
    if r in ALLOW:
        continue
    for c in [n for n in ast.walk(t) if isinstance(n, ast.ClassDef)]:
        is_fro = any(isinstance(d, ast.Call) and any(k.arg == "frozen" and getattr(k.value, "value", None) is True for k in d.keywords) for d in c.decorator_list)
        for s in c.body:
            tg = s.targets if isinstance(s, ast.Assign) else [s.target] if isinstance(s, ast.AnnAssign) else []
            val = getattr(s, "value", None) if isinstance(s, (ast.Assign, ast.AnnAssign)) else None
            if tg and val is not None and mut(val) and any(isinstance(x, ast.Name) for x in tg):
                ast_counts["class_container"] += 1
                near_rows["class_container"].append("%s:%d:%s" % (r, s.lineno, c.name))
            if isinstance(s, ast.AnnAssign) and not is_fro:
                names = {m.id for m in ast.walk(s.annotation) if isinstance(m, ast.Name)} | {m.attr for m in ast.walk(s.annotation) if isinstance(m, ast.Attribute)}
                strs = " ".join(m.value for m in ast.walk(s.annotation) if isinstance(m, ast.Constant) and isinstance(m.value, str))
                hit = (names & frozen) | {f for f in frozen if re.search(r"\b%s\b" % re.escape(f), strs)}
                if hit:
                    non_frozen_annot.append("%s:%d:%s.%s:%s" % (r, s.lineno, c.name, getattr(s.target, "id", "?"), sorted(hit)))
        for f in [x for x in c.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            params = list(f.args.posonlyargs) + list(f.args.args)
            if not params:
                continue
            me = params[0].arg
            for n in ast.walk(f):
                tg = n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, ast.AnnAssign) else []
                val = getattr(n, "value", None) if isinstance(n, (ast.Assign, ast.AnnAssign)) else None
                if val is None:
                    continue
                for x in tg:
                    if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id == me:
                        if mut(val):
                            ast_counts["attr_container_%s" % ("frozen" if is_fro else "plain")] += 1
                            near_rows["attr_container"].append("%s:%d:%s.%s" % (r, n.lineno, c.name, x.attr))
                        elif isinstance(val, (ast.IfExp, ast.BoolOp)) and any(mut(m) for m in ast.iter_child_nodes(val)):
                            near["attr_ifexp_or_boolop_mutable"] += 1
                            near_rows["attr_ifexp_or_boolop_mutable"].append("%s:%d:%s.%s" % (r, n.lineno, c.name, x.attr))
                        elif isinstance(val, ast.Call) and getattr(val.func, "id", "") in frozen and not is_fro:
                            near_rows["attr_vt_ctor"].append("%s:%d:%s.%s" % (r, n.lineno, c.name, x.attr))
                    if isinstance(x, (ast.Tuple, ast.List)) and isinstance(val, (ast.Tuple, ast.List)):
                        for a, b in zip(x.elts, val.elts):
                            if isinstance(a, ast.Attribute) and isinstance(a.value, ast.Name) and a.value.id == me and mut(b):
                                near["attr_tuple_unpack_mutable"] += 1
                                near_rows["attr_tuple_unpack_mutable"].append("%s:%d:%s.%s" % (r, n.lineno, c.name, a.attr))
                if isinstance(n, ast.Call):
                    pass
            for n in ast.walk(f):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "__setattr__" and len(n.args) >= 3 and mut(n.args[2]):
                    near["object_setattr_mutable"] += 1
                    near_rows["object_setattr_mutable"].append("%s:%d:%s" % (r, n.lineno, c.name))
out.write_text(json.dumps({"n_files": len(files), "n_frozen_types": len(frozen),
    "grep_counts": {k: len(v) for k, v in grep.items()}, "ast_counts": dict(ast_counts), "near_counts": dict(near),
    "non_frozen_annot": non_frozen_annot, "grep": grep, "near_rows": near_rows}, ensure_ascii=False, indent=1), encoding="utf-8")
