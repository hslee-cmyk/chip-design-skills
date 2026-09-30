"""P8 W 식 인라인 사이트 독립 측정(auditor 작성, 2026-09-30 순서 3). test 코드를 가져오지 않는다.

규칙 = spec card 20260930-dup-w-calc 계약 2 문장:
  `(a * b) / c` -- BinOp(Div)의 left가 BinOp(Mult). c의 이름(Name.id / Attribute.attr / 문자열 상수 첨자 키)이 대소문자 무시 'idu' 포함.
  a·b 중 하나가 L 계열, 다른 하나가 ID 계열.
  L 계열: 앞의 밑줄(전부)과 그 뒤 소문자 m 하나를 뗀 stem이 'L' | 'L_'로 시작 | 'L'+숫자 | 'Lc'.
          (변형 LTAIL_WIDE: 'L' 뒤 [0-9c]+ -- 문장 해석 차이가 결과를 바꾸는지 확인용)
  ID 계열: 이름에 'ID' 포함 또는 이름 == 'I'.
  범위: A/*.py(최상위) + workspaces/run_harness.py. width_from_id_density 정의 본문 안은 제외.

모드
  base    <root> <rev> <out.json>             : git blob 기준으로 사이트 목록 + 사이트별 문장/함수 AST(자리표시자 치환) 기록
  compare <root> <rev> <base.json> <out.json> : (순서 7) 병합본에서 width_from_id_density 호출을 같은 자리표시자로 치환해
                                                문장·함수 AST가 base와 같은지, 호출 인자 = (L, ID, IDu) 피연산자인지 대조
보조: 넓은 탐지(broad) -- 모든 Div에서 분자 부분트리에 L 계열·ID 계열 이름, 분모 부분트리에 idu 이름이 있는 것(규칙 밖 모양 참고).
"""
import ast, copy, hashlib, json, re, subprocess, sys

A = "skills/analog-gmid-design/assets/"
NEW = "width_from_id_density"
PH = "__W_SITE__"
LTAIL = re.compile(r"L(?:[0-9]+|c)")
LTAIL_WIDE = re.compile(r"L[0-9c]+")


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def git(root, *a):
    return subprocess.run(["git", "-C", root, *a], capture_output=True, check=True).stdout


def scope_files(root, rev):
    names = git(root, "ls-tree", "--name-only", rev, A).decode("utf-8").split("\n")
    fs = sorted(n for n in names if n.endswith(".py") and n.count("/") == A.count("/"))
    return fs + ["workspaces/run_harness.py"]


def oname(n):
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        return n.attr
    if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str):
        return n.slice.value
    return None


def is_l(name, wide=False):
    if not name:
        return False
    s = name.lstrip("_")
    if s[:1] == "m":
        s = s[1:]
    return s == "L" or s.startswith("L_") or (LTAIL_WIDE if wide else LTAIL).fullmatch(s) is not None


def is_id(name):
    return bool(name) and ("ID" in name or name == "I")


def match(node, wide=False):
    """규칙에 맞으면 (L 피연산자, ID 피연산자, IDu 피연산자), 아니면 None."""
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)):
        return None
    m = node.left
    if not (isinstance(m, ast.BinOp) and isinstance(m.op, ast.Mult)):
        return None
    c = oname(node.right)
    if c is None or "idu" not in c.lower():
        return None
    a, b = oname(m.left), oname(m.right)
    if is_l(a, wide) and is_id(b):
        return (m.left, m.right, node.right)
    if is_id(a) and is_l(b, wide):
        return (m.right, m.left, node.right)
    return None


def names_in(n):
    out = []
    for x in ast.walk(n):
        v = oname(x)
        if v:
            out.append(v)
    return out


def broad(node):
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)):
        return False
    num, den = names_in(node.left), names_in(node.right)
    return any("idu" in d.lower() for d in den) and any(is_l(x) or is_l(x, True) for x in num) and any(is_id(x) for x in num)


def parents(tree):
    p = {}
    for n in ast.walk(tree):
        for ch in ast.iter_child_nodes(n):
            p[ch] = n
    return p


def excluded(tree):
    return [(n.lineno, n.end_lineno) for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == NEW]


def chain(node, par):
    """(가장 안쪽 문장, 가장 안쪽 함수, 함수 qualname)."""
    stmt = None
    fn = None
    qual = []
    x = node
    while x in par:
        x = par[x]
        if stmt is None and isinstance(x, ast.stmt):
            stmt = x
        if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if fn is None and not isinstance(x, ast.ClassDef):
                fn = x
            qual.append(x.name)
    return stmt, fn, ".".join(reversed(qual)) or "<module>"


class Sub(ast.NodeTransformer):
    """대상 노드(id 집합)를 자리표시자 Name으로 바꾼다."""
    def __init__(self, targets):
        self.t = targets

    def visit(self, node):
        if id(node) in self.t:
            return ast.Name(id=PH, ctx=ast.Load())
        return super().visit(node)


def dump_sub(node, targets):
    """node 사본에서 targets(원본 노드)를 치환한 ast.dump. copy.deepcopy는 노드 id를 바꾸므로 경로로 대응."""
    memo = {}
    c = copy.deepcopy(node, memo)
    t = {id(memo[id(x)]) for x in targets if id(x) in memo}
    return ast.dump(Sub(t).visit(c), include_attributes=False)


def is_new_call(n):
    if not isinstance(n, ast.Call):
        return False
    f = n.func
    return (isinstance(f, ast.Name) and f.id == NEW) or (isinstance(f, ast.Attribute) and f.attr == NEW)


def scan(root, rev, mode):
    res = {"rev": rev, "files": {}, "sites": [], "broad_extra": [], "wide_rule_diff": []}
    for f in scope_files(root, rev):
        data = git(root, "cat-file", "blob", f"{rev}:{f}")
        src = data.decode("utf-8")
        tree = ast.parse(src)
        par = parents(tree)
        ex = excluded(tree)
        res["files"][f] = {"blob_sha256": hashlib.sha256(data).hexdigest(), "excluded_spans": ex}
        found = []   # (node, triple)
        for n in ast.walk(tree):
            if any(lo <= getattr(n, "lineno", -1) <= hi for lo, hi in ex):
                continue
            if mode == "base":
                t = match(n)
                if t:
                    found.append((n, t))
                elif match(n, wide=True):
                    res["wide_rule_diff"].append({"file": f, "line": n.lineno, "src": ast.get_source_segment(src, n)})
                if broad(n) and not t:
                    res["broad_extra"].append({"file": f, "line": n.lineno, "src": ast.get_source_segment(src, n)})
            else:
                t = match(n)
                if t:
                    found.append((n, "INLINE"))
                elif is_new_call(n):
                    found.append((n, tuple(n.args) + tuple(k.value for k in n.keywords)))
        # 같은 문장·함수 안 다른 사이트도 함께 치환해야 비교가 사이트별로 독립이다
        by_fn = {}
        for n, t in found:
            stmt, fn, qual = chain(n, par)
            by_fn.setdefault(id(fn) if fn else 0, []).append(n)
        for n, t in sorted(found, key=lambda x: (x[0].lineno, x[0].col_offset)):
            stmt, fn, qual = chain(n, par)
            site = {"file": f, "line": n.lineno, "col": n.col_offset, "end_line": n.end_lineno, "function": qual,
                    "expr_src": ast.get_source_segment(src, n)}
            if t == "INLINE":
                site["kind"] = "inline"
            else:
                site["operands_dump"] = [ast.dump(x, include_attributes=False) for x in t]
                site["operands_src"] = [ast.get_source_segment(src, x) for x in t]
                if mode != "base":
                    site["kind"] = "call"
                    site["n_args"] = len(n.args)
                    site["keywords"] = [k.arg for k in n.keywords]
            same_stmt = [m for m in by_fn.get(id(fn) if fn else 0, []) if chain(m, par)[0] is stmt]
            site["stmt_type"] = type(stmt).__name__
            site["stmt_lines"] = [stmt.lineno, stmt.end_lineno]
            if isinstance(stmt, (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.FunctionDef, ast.AsyncFunctionDef)):
                site["stmt_note"] = "compound -- 문장 dump는 본문 포함"
            site["stmt_src"] = "\n".join(src.splitlines()[stmt.lineno - 1:stmt.end_lineno])
            sd = dump_sub(stmt, same_stmt)
            site["stmt_dump_sub"] = sd
            site["stmt_dump_sub_sha256"] = sha(sd)
            if fn is not None:
                fd = dump_sub(fn, by_fn[id(fn)])
                site["function_dump_sub_sha256"] = sha(fd)
                site["function_lines"] = [fn.lineno, fn.end_lineno]
                site["function_n_sites"] = len(by_fn[id(fn)])
            res["sites"].append(site)
    return res


def main():
    mode = sys.argv[1]
    if mode == "base":
        root, rev, out = sys.argv[2:5]
        r = scan(root, rev, "base")
        r["n_sites"] = len(r["sites"])
        json.dump(r, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("n_sites", r["n_sites"], "wide_rule_diff", len(r["wide_rule_diff"]), "broad_extra", len(r["broad_extra"]))
        for s in r["sites"]:
            print(s["file"].split("/")[-1], s["line"], s["function"], s["stmt_type"], s["expr_src"], s["stmt_dump_sub_sha256"][:12])
        for x in r["broad_extra"]:
            print("broad_extra", x)
        for x in r["wide_rule_diff"]:
            print("wide_rule_diff", x)
    elif mode == "compare":
        root, rev, basef, out = sys.argv[2:6]
        b = json.load(open(basef, encoding="utf-8"))
        m = scan(root, rev, "merged")
        inline = [s for s in m["sites"] if s["kind"] == "inline"]
        bs = sorted(b["sites"], key=lambda s: (s["file"], s["line"], s["col"]))
        # 사이트 대응: 파일·함수 이름·함수 안 순서
        def key(s):
            return (s["file"], s["function"])
        from collections import defaultdict
        bm, mm = defaultdict(list), defaultdict(list)
        for s in bs:
            bm[key(s)].append(s)
        for s in sorted(m["sites"], key=lambda s: (s["file"], s["line"], s["col"])):
            if s["kind"] == "call":
                mm[key(s)].append(s)
        rows, bad = [], 0
        for k in sorted(set(bm) | set(mm)):
            bl, ml = bm.get(k, []), mm.get(k, [])
            for i in range(max(len(bl), len(ml))):
                x = bl[i] if i < len(bl) else None
                y = ml[i] if i < len(ml) else None
                row = {"file": k[0], "function": k[1], "base_line": x and x["line"], "merged_line": y and y["line"]}
                if x and y:
                    row["args_equal"] = (y["n_args"] == 3 and not y["keywords"] and y["operands_dump"] == x["operands_dump"])
                    row["stmt_equal"] = y["stmt_dump_sub_sha256"] == x["stmt_dump_sub_sha256"]
                    row["function_equal"] = y.get("function_dump_sub_sha256") == x.get("function_dump_sub_sha256")
                    ok = row["args_equal"] and row["stmt_equal"]
                else:
                    ok = False
                row["ok"] = ok
                bad += not ok
                rows.append(row)
        r = {"rev": rev, "n_base_sites": len(bs), "n_merged_calls": sum(len(v) for v in mm.values()),
             "n_merged_inline": len(inline), "inline": inline, "rows": rows, "n_bad": bad}
        json.dump(r, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(json.dumps({k: r[k] for k in ("n_base_sites", "n_merged_calls", "n_merged_inline", "n_bad")}))
        for row in rows:
            print(row)


main()
