"""이동 무변경 증명(PROCEDURE 남기는 것 3) -- move.py·mp_core와 코드를 공유하지 않는 독립 판정.

    python -B ast_check.py <base_rev> <head_rev> [--root R] [--out result.json]

base..head에서 바뀐 파일 전체를 대상으로(바뀐 파일이 .py가 아니면 FAIL):
  D1 정의 해시: 함수·클래스(중첩·메서드 포함, qualname)마다 ast.dump(docstring 제외, 위치 속성 제외) sha256.
     base 다중집합 = head 다중집합(파일은 무관 -- 옮겨도 같아야 한다). 사라진 정의 0, 새 정의 0, 바뀐 정의 0.
  D2 중복 정의: head의 한 파일 안에서 최상위 이름을 두 번 이상 정의(def·class·대입)한 것이 base보다 늘지 않음,
     그리고 최상위 def·class 이름이 head 대상 파일 둘 이상에 정의된 경우가 base보다 늘지 않음(옮기고 원본에 남긴 것).
  D3 import 아닌 최상위 문장: (모듈 docstring 제외) ast.dump 다중집합 base = head(docstring 포함 비교 -- 바이트 이동이면 같다).
  D4 차이는 import 줄뿐: D1·D3이 같으면 남는 차이는 Import/ImportFrom과 모듈 docstring뿐이다. 더해진·빠진 import 문장을 나열하고,
     더해진 것 중 `import *`가 있으면 FAIL. 새 파일의 모듈 docstring은 FAIL(이동 card = 이동만, W-3).
  D5 정적 이름 해석: head 대상 파일마다 symtable로 전역 참조인데 모듈에서 묶이지 않고 builtin도 아닌 이름(NameError 후보)이
     base(같은 파일, 새 파일이면 빈 집합)보다 늘지 않음 -- 옮긴 정의가 새 모듈에서 import를 빠뜨린 경우를 잡는다.
  D6 재수출 완전성: base 파일에서 최상위로 묶이던 이름이 head 그 파일에서 정의되지 않으면, 그 이름이 지금 정의된 파일에서
     `from <모듈> import 이름`으로 묶여야 한다(명시 재수출 -- 원 파일 경유로 읽는 쪽이 깨지지 않게).
exit 0 = PASS, 1 = FAIL, 2 = 오류.
"""
import argparse
import ast
import builtins
import collections
import copy
import hashlib
import json
import subprocess
import symtable
import sys


def git(root, *a):
    r = subprocess.run(["git", "-C", root] + list(a), capture_output=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr.decode("utf-8", "replace"))
        sys.exit(2)
    return r.stdout.decode("utf-8")


def show(root, rev, path):
    r = subprocess.run(["git", "-C", root, "show", "%s:%s" % (rev, path)], capture_output=True)
    return r.stdout.decode("utf-8").replace("\r\n", "\n") if r.returncode == 0 else None


def strip_doc(node):
    n = copy.deepcopy(node)
    for x in ast.walk(n):
        if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)) and x.body \
                and isinstance(x.body[0], ast.Expr) and isinstance(x.body[0].value, ast.Constant) \
                and isinstance(x.body[0].value.value, str):
            x.body = x.body[1:] or [ast.Pass()]
    return n


def h(node):
    return hashlib.sha256(ast.dump(strip_doc(node), include_attributes=False).encode("utf-8")).hexdigest()


def defs(tree):
    out = []

    def rec(body, pre):
        for n in body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                q = pre + n.name
                out.append((q, h(n)))
                rec(n.body, q + ".")
            else:
                for c in ast.iter_child_nodes(n):          # if/try 안의 정의도
                    if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        rec([c], pre)
                    elif hasattr(c, "body") and isinstance(getattr(c, "body"), list):
                        rec(c.body, pre)
    rec(tree.body, "")
    return out


def is_doc(tree, n):
    return (tree.body and n is tree.body[0] and isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
            and isinstance(n.value.value, str))


def top_names(tree):
    c = collections.Counter()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            c[n.name] += 1
        elif isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            ts = n.targets if isinstance(n, ast.Assign) else [n.target]
            for t in ts:
                for x in ast.walk(t):
                    if isinstance(x, ast.Name):
                        c[x.id] += 1
    return c


# 이름 공간 암묵 이름(예: Python 3.14 symtable의 __conditional_annotations__)은 dunder 전부를 해석된 것으로 본다
BUILTIN = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__spec__", "__loader__", "__package__",
                                "__builtins__", "__annotations__", "__dict__", "__path__", "__cached__"}


def _dunder(nm):
    return nm.startswith("__") and nm.endswith("__")


def unresolved(src, fname):
    top = symtable.symtable(src, fname, "exec")
    bound = {s.get_name() for s in top.get_symbols() if s.is_assigned() or s.is_imported()}
    for st in top.get_children():
        bound.add(st.get_name())
    bad = set()

    def walk(t):
        for s in t.get_symbols():
            nm = s.get_name()
            if t.get_type() == "module":
                if s.is_referenced() and not (s.is_assigned() or s.is_imported()) and nm not in BUILTIN and nm not in bound and not _dunder(nm):
                    bad.add(nm)
            elif s.is_global() and s.is_referenced() and nm not in bound and nm not in BUILTIN and not _dunder(nm):
                bad.add(nm)
        for c in t.get_children():
            walk(c)
    walk(top)
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("head")
    ap.add_argument("--root", default=".")
    ap.add_argument("--out")
    ns = ap.parse_args()
    root = ns.root
    changed = [l for l in git(root, "diff", "--name-only", ns.base, ns.head).splitlines() if l]
    res = {"base": git(root, "rev-parse", ns.base).strip(), "head": git(root, "rev-parse", ns.head).strip(),
           "files": changed, "fail": []}
    non_py = [f for f in changed if not f.endswith(".py")]
    if non_py:
        res["fail"].append({"check": "non-py file changed", "files": non_py})
    py = [f for f in changed if f.endswith(".py")]
    bt, ht, bs, hs = {}, {}, {}, {}
    for f in py:
        b, hh = show(root, ns.base, f), show(root, ns.head, f)
        try:
            if b is not None:
                bt[f], bs[f] = ast.parse(b), b
            if hh is not None:
                ht[f], hs[f] = ast.parse(hh), hh
        except SyntaxError as e:
            res["fail"].append({"check": "parse", "file": f, "error": str(e)})
    # D1
    bd = collections.Counter(x for f in bt for x in defs(bt[f]))
    hd = collections.Counter(x for f in ht for x in defs(ht[f]))
    lost, new = bd - hd, hd - bd
    bq = {q for q, _ in bd}
    hq = {q for q, _ in hd}
    changed_defs = sorted({q for q, _ in lost} & {q for q, _ in new})
    res["D1"] = {"defs_base": sum(bd.values()), "defs_head": sum(hd.values()),
                 "lost": sorted(q for q, _ in lost if q not in changed_defs),
                 "new": sorted(q for q, _ in new if q not in changed_defs), "changed": changed_defs}
    if lost or new:
        res["fail"].append({"check": "D1 def hash multiset differs"})
    # 이동 지도(정보): qualname -> (base 파일, head 파일)
    where_b = collections.defaultdict(list)
    where_h = collections.defaultdict(list)
    for f in bt:
        for n in bt[f].body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                where_b[n.name].append(f)
    for f in ht:
        for n in ht[f].body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                where_h[n.name].append(f)
    res["moved_top_defs"] = sorted("%s: %s -> %s" % (k, ",".join(where_b[k]), ",".join(where_h[k]))
                                   for k in where_h if where_b.get(k) and sorted(where_b[k]) != sorted(where_h[k]))
    # D2
    dup = []
    for f in ht:
        cb = top_names(bt[f]) if f in bt else collections.Counter()
        for nm, c in top_names(ht[f]).items():
            if c > 1 and c > cb.get(nm, 0):
                dup.append({"file": f, "name": nm, "count": c, "base": cb.get(nm, 0)})
    for nm, fs in where_h.items():
        if len(fs) > 1 and len(fs) > len(where_b.get(nm, [])):
            dup.append({"name": nm, "files": fs, "base_files": where_b.get(nm, [])})
    res["D2_duplicates"] = dup
    if dup:
        res["fail"].append({"check": "D2 duplicate definitions"})
    # D3 / D4
    def stmts(trees, imports):
        c = collections.Counter()
        for f, t in trees.items():
            for n in t.body:
                if is_doc(t, n):
                    continue
                if isinstance(n, (ast.Import, ast.ImportFrom)) == imports:
                    c[ast.dump(n, include_attributes=False) if not imports else ast.unparse(n)] += 1
        return c
    sb, sh = stmts(bt, False), stmts(ht, False)
    res["D3"] = {"stmts_base": sum(sb.values()), "stmts_head": sum(sh.values()),
                 "only_base": sum((sb - sh).values()), "only_head": sum((sh - sb).values())}
    if sb != sh:
        res["fail"].append({"check": "D3 non-import top-level statements differ"})
        res["D3"]["only_base_sample"] = [x[:200] for x in list((sb - sh))[:5]]
        res["D3"]["only_head_sample"] = [x[:200] for x in list((sh - sb))[:5]]
    ib, ih = stmts(bt, True), stmts(ht, True)
    res["D4_imports_added"] = sorted((ih - ib).elements())
    res["D4_imports_removed"] = sorted((ib - ih).elements())
    star = [x for x in res["D4_imports_added"] if x.endswith("import *")]
    if star:
        res["fail"].append({"check": "D4 import * added", "lines": star})
    docs = []
    for f in set(bt) | set(ht):
        db = ast.get_docstring(bt[f], clean=False) if f in bt else None
        dh = ast.get_docstring(ht[f], clean=False) if f in ht else None
        if f in bt and f in ht and db != dh:
            docs.append({"file": f, "why": "module docstring changed"})
        if f not in bt and dh is not None:
            docs.append({"file": f, "why": "new file has module docstring"})
    res["D4_docstrings"] = docs
    if docs:
        res["fail"].append({"check": "D4 module docstring"})
    # D5
    d5 = []
    for f in ht:
        try:
            ub = unresolved(bs[f], f) if f in bs else set()
            uh = unresolved(hs[f], f)
        except SyntaxError:
            continue
        if uh - ub:
            d5.append({"file": f, "names": sorted(uh - ub)})
    res["D5_new_unresolved"] = d5
    if d5:
        res["fail"].append({"check": "D5 new unresolved global names"})
    # D6 재수출 완전성: base 파일 f의 최상위 이름이 head f에서 정의되지 않으면 head f가 그 이름을 정의된 새 파일에서 import해야 한다
    def top_bound(t):
        out = set(top_names(t))
        return out
    def imported(t):
        m = {}
        for n in t.body:
            if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
                for a in n.names:
                    m[a.asname or a.name] = n.module
        return m
    defined_in = collections.defaultdict(set)
    for f, t in ht.items():
        for nm in top_bound(t):
            defined_in[nm].add(f.rsplit("/", 1)[-1][:-3])
    d6 = []
    for f in bt:
        if f not in ht:
            continue
        gone = top_bound(bt[f]) - top_bound(ht[f])
        imp = imported(ht[f])
        for nm in sorted(gone):
            if imp.get(nm) not in defined_in.get(nm, set()):
                d6.append({"file": f, "name": nm, "imported_from": imp.get(nm), "defined_in": sorted(defined_in.get(nm, ()))})
    res["D6_missing_reexport"] = d6
    if d6:
        res["fail"].append({"check": "D6 moved-out name not re-exported from its new module"})
    res["verdict"] = "FAIL" if res["fail"] else "PASS"
    if ns.out:
        json.dump(res, open(ns.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    show_keys = ("verdict", "files", "D1", "D2_duplicates", "D3", "D4_imports_added", "D4_imports_removed", "D4_docstrings",
                 "D5_new_unresolved", "D6_missing_reexport", "fail")
    print(json.dumps({k: res[k] for k in show_keys if k in res}, ensure_ascii=False, indent=1))
    sys.exit(1 if res["fail"] else 0)


if __name__ == "__main__":
    main()
