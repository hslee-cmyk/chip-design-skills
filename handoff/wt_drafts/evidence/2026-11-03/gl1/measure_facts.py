"""GL-1 spec card 사실 측정(읽기 전용, 엔진 import·실행 0). 구현물이 아니라 design 문언의 실현 가능성 측정용 시제품이다.

실행: PYTHONIOENCODING=utf-8 C:/Python314/python.exe measure_facts.py <engine dir> <label>
결과: 같은 폴더 facts_<label>.jsonl(케이스마다 바로 append), facts_<label>_summary.txt
"""
import ast
import collections
import json
import os
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
LABEL = sys.argv[2]
HERE = Path(__file__).resolve().parent
OUT = open(HERE / ("facts_%s.jsonl" % LABEL), "w", encoding="utf-8")

ALLOW = {
    "core/graph_snapshot.py", "core/compute_block.py", "core/projection.py", "core/graft.py", "core/donors.py",
    "core/field_value.py", "core/graph_record.py", "core/writer_table.py",
    "lut/lut_memo.py", "lut/table_cache.py", "core/bounded_lru.py",
    "search/archive.py", "search/s3_index.py", "core/run_counters.py",
}
MUT_CALL = {"dict", "list", "set", "defaultdict", "OrderedDict", "deque", "Counter", "WeakValueDictionary", "WeakKeyDictionary"}
CACHE_OBJ = {"BoundedLRU", "LutMemo", "OrderedDict", "WeakValueDictionary", "WeakKeyDictionary"}
CONT = {"tuple", "Tuple", "list", "List", "dict", "Dict", "set", "Set", "frozenset", "FrozenSet", "Sequence", "Mapping",
        "Optional", "Union", "Iterable", "defaultdict", "OrderedDict", "deque"}

rows = []


def emit(kind, path, line, detail):
    r = {"kind": kind, "path": path, "line": line, "detail": detail, "allowed": path in ALLOW}
    rows.append(r)
    OUT.write(json.dumps(r, ensure_ascii=False) + "\n")
    OUT.flush()


def files():
    for p in sorted(ROOT.rglob("*.py")):
        parts = p.relative_to(ROOT).parts
        if parts[0] == "tests" or "__pycache__" in parts or any(x.startswith(".") for x in parts):
            continue
        yield p, "/".join(parts)


def call_name(n):
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        return n.attr
    return ""


def is_mut(v):
    if isinstance(v, (ast.Dict, ast.List, ast.Set, ast.DictComp, ast.ListComp, ast.SetComp)):
        return True
    return isinstance(v, ast.Call) and call_name(v.func) in MUT_CALL


def is_frozen_dc(c):
    for d in c.decorator_list:
        if isinstance(d, ast.Call) and call_name(d.func) == "dataclass":
            for k in d.keywords:
                if k.arg == "frozen" and isinstance(k.value, ast.Constant) and k.value.value is True:
                    return True
    return False


def is_dc(c):
    return any(call_name(d.func if isinstance(d, ast.Call) else d) == "dataclass" for d in c.decorator_list)


trees = {r: ast.parse(p.read_text(encoding="utf-8")) for p, r in files()}

frozen = {}
for r, t in trees.items():
    for n in t.body:
        if isinstance(n, ast.ClassDef) and is_frozen_dc(n):
            frozen.setdefault(n.name, []).append(r)
dup = {k: v for k, v in frozen.items() if len(v) > 1}


def ann_names(a):
    """주석 표현의 이름들(컨테이너 안 포함)."""
    if a is None:
        return set()
    if isinstance(a, ast.Constant) and isinstance(a.value, str):
        try:
            a = ast.parse(a.value, mode="eval").body
        except SyntaxError:
            return set()
    return {call_name(x) for x in ast.walk(a) if isinstance(x, (ast.Name, ast.Attribute))}


def value_vt(v):
    if isinstance(v, ast.Call) and call_name(v.func) in frozen:
        return call_name(v.func)
    if isinstance(v, (ast.Tuple, ast.List, ast.Set)):
        for e in v.elts:
            x = value_vt(e)
            if x:
                return x
    if isinstance(v, ast.Dict):
        for e in v.values:
            x = value_vt(e)
            if x:
                return x
    if isinstance(v, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
        return value_vt(v.elt)
    if isinstance(v, ast.DictComp):
        return value_vt(v.value)
    return None


for r, t in trees.items():
    for n in t.body:  # 모듈 수준
        tgt = None
        if isinstance(n, ast.Assign):
            tgt, val, ann = n.targets[0], n.value, None
        elif isinstance(n, ast.AnnAssign):
            tgt, val, ann = n.target, n.value, n.annotation
        if tgt is not None:
            name = getattr(tgt, "id", "?")
            if val is not None and call_name(val.func if isinstance(val, ast.Call) else ast.Name("")) in CACHE_OBJ:
                emit("g_module_cache_object", r, n.lineno, name)
            hit = (ann_names(ann) & set(frozen)) or ({value_vt(val)} if val is not None and value_vt(val) else set())
            if hit:
                emit("vt_module", r, n.lineno, "%s:%s" % (name, sorted(hit)[0]))
    for n in ast.walk(t):
        if isinstance(n, ast.ClassDef):
            frozen_cls = is_frozen_dc(n)
            for s in n.body:
                if isinstance(s, ast.Assign) and is_mut(s.value):
                    emit("g_class_container", r, s.lineno, "%s.%s" % (n.name, call_name(s.targets[0])))
                if isinstance(s, ast.AnnAssign) and s.value is not None and is_mut(s.value):
                    emit("g_class_container", r, s.lineno, "%s.%s" % (n.name, call_name(s.target)))
                if not frozen_cls:
                    if isinstance(s, ast.AnnAssign):
                        hit = ann_names(s.annotation) & set(frozen)
                        if hit:
                            emit("vt_class_field", r, s.lineno, "%s.%s:%s" % (n.name, call_name(s.target), sorted(hit)[0]))
                    if isinstance(s, ast.Assign) and value_vt(s.value):
                        emit("vt_class_attr", r, s.lineno, "%s.%s:%s" % (n.name, call_name(s.targets[0]), value_vt(s.value)))
                if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for x in ast.walk(s):
                        tg, val, ann = None, None, None
                        if isinstance(x, ast.Assign) and len(x.targets) == 1:
                            tg, val = x.targets[0], x.value
                        elif isinstance(x, ast.AnnAssign):
                            tg, val, ann = x.target, x.value, x.annotation
                        if isinstance(tg, ast.Attribute) and isinstance(tg.value, ast.Name) and tg.value.id == "self":
                            if val is not None and is_mut(val):
                                emit("g_attr_container", r, x.lineno, "%s.%s" % (n.name, tg.attr))
                            hit = (ann_names(ann) & set(frozen)) or ({value_vt(val)} if val is not None and value_vt(val) else set())
                            if hit:
                                emit("vt_self_attr", r, x.lineno, "%s.%s:%s" % (n.name, tg.attr, sorted(hit)[0]))
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for d in n.decorator_list:
                if call_name(d) == "cached_property":
                    emit("g_cached_property", r, d.lineno, n.name)
        if isinstance(n, ast.Call):
            nm = call_name(n.func)
            if nm == "field" or (isinstance(n.func, ast.Attribute) and n.func.attr == "field"):
                for k in n.keywords:
                    if k.arg == "default_factory" and call_name(k.value) in ("dict", "list", "set"):
                        emit("g_default_factory", r, n.lineno, call_name(k.value))
            if isinstance(n.func, ast.Name) and n.func.id == "id":
                emit("g_id_call", r, n.lineno, ast.unparse(n)[:60])
            if isinstance(n.func, ast.Call) and call_name(n.func.func) in ("lru_cache", "cache"):
                emit("g_lru_call", r, n.lineno, ast.unparse(n)[:60])
            if isinstance(n.func, (ast.Name, ast.Attribute)) and nm == "cache":
                emit("g_lru_call", r, n.lineno, ast.unparse(n)[:60])
            if nm == "call" and isinstance(n.func, ast.Attribute) and call_name(n.func.value) == "memo":
                first = n.args[0] if n.args else None
                emit("memo_call_seen", r, n.lineno, ast.unparse(first)[:60] if first else "")

cnt = collections.Counter((x["kind"], x["allowed"]) for x in rows)
files_by_kind = collections.defaultdict(set)
for x in rows:
    if not x["allowed"]:
        files_by_kind[x["kind"]].add(x["path"])
with open(HERE / ("facts_%s_summary.txt" % LABEL), "w", encoding="utf-8") as fh:
    def w(*a):
        s = " ".join(str(i) for i in a)
        print(s)
        fh.write(s + "\n")
    w("label", LABEL, "engine files", len(trees), "frozen dataclasses", len(frozen), "dup names", json.dumps(dup, ensure_ascii=False))
    for k in sorted(cnt):
        w(k, cnt[k])
    for k in sorted(files_by_kind):
        w(k, "files", len(files_by_kind[k]), sorted(files_by_kind[k])[:40])
    vt_mod = collections.Counter(x["detail"].split(":")[-1] for x in rows if x["kind"] == "vt_module" and not x["allowed"])
    w("vt_module top types", vt_mod.most_common(25))
    vt_other = [x for x in rows if x["kind"] in ("vt_class_field", "vt_class_attr", "vt_self_attr") and not x["allowed"]]
    for x in vt_other[:60]:
        w(" ", x["kind"], x["path"], x["line"], x["detail"])
    w("EvalResult frozen:", "EvalResult" in frozen, "SearchContext frozen:", "SearchContext" in frozen,
      "KernelContext frozen:", "KernelContext" in frozen)
