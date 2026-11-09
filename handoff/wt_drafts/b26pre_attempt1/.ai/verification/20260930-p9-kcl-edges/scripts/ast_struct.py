"""구조 AST 측정 (auditor 독립 작성, 2026-09-30 P9 순서 3) -- spec card 20260930-p9-kcl-edges 계약 1·3(a)·5(a)(b)·6·7.
사용:
  python -P ast_struct.py selftest
  python -P ast_struct.py measure <root> <out.json>
측정 항목(모두 <root> 트리의 파일을 읽기만 한다, import 없음):
  c1: SD kcl_series_union 본문(docstring 제외)의 (a) _kcl_and_matching_edges 호출 수 (b) Name _RAIL_NETS 수
      (c) Attribute .source/.drain 수 (d) 중첩 find의 while 루프 안에서 parent[...] 대입(Subscript 대상) 수, 루프 본문 문장 dump
  c3a: _kcl_and_matching_edges 시그니처(args dump·returns dump)와 docstring 포함 ast.dump sha256
  c5a: A/*.py·workspaces/run_harness.py 문자열 상수(docstring 제외, f-string 조각 포함) 다중집합 -- 파일별 Counter
  c5b: SD의 ast.Name id=_RAIL_NETS 수(대입 대상 포함)
  c6: A/*.py에서 kcl_series_union·_kcl_and_matching_edges 호출 위치(파일, 감싸는 최상위 def[.메서드], 줄)
  c7: SD 최상위 정의별 ast.dump sha256(docstring 포함/제외 둘 다), SR·run_harness·library 파일 sha256, A/*.py 파일 sha256"""
import ast, collections, glob, hashlib, json, os, sys

SD_REL = "skills/analog-gmid-design/assets/stick_diagram.py"


def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode("utf-8")).hexdigest()


def is_doc(stmt):
    return isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str)


def strip_doc(body):
    return body[1:] if body and is_doc(body[0]) else body


def find_top_def(tree, name):
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def c1_measure(fn):
    """kcl_series_union FunctionDef -> 계약 1 수치."""
    body = strip_doc(fn.body)
    calls = rail = attrs = 0
    for st in body:
        for n in ast.walk(st):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_kcl_and_matching_edges":
                calls += 1
            if isinstance(n, ast.Name) and n.id == "_RAIL_NETS":
                rail += 1
            if isinstance(n, ast.Attribute) and n.attr in ("source", "drain"):
                attrs += 1
    finds = [n for st in body for n in ast.walk(st) if isinstance(n, ast.FunctionDef) and n.name == "find"]
    comp = 0
    loop_bodies = []
    for f in finds:
        for n in ast.walk(f):
            if isinstance(n, (ast.While, ast.For)):
                loop_bodies.append([ast.dump(s) for s in n.body])
                for s in n.body:
                    for m in ast.walk(s):
                        tg = []
                        if isinstance(m, ast.Assign):
                            tg = m.targets
                        elif isinstance(m, (ast.AugAssign, ast.AnnAssign)):
                            tg = [m.target]
                        for t in tg:
                            for tt in ast.walk(t):
                                if isinstance(tt, ast.Subscript) and isinstance(tt.value, ast.Name) and tt.value.id == "parent":
                                    comp += 1
    return {"calls_canonical": calls, "rail_nets_refs": rail, "source_drain_attrs": attrs,
            "n_nested_find": len(finds), "path_compression_assigns_in_find_loops": comp,
            "find_loop_bodies": loop_bodies,
            "verdict": {"a_calls_canonical": calls >= 1, "b_no_rail_nets": rail == 0, "c_no_source_drain": attrs == 0,
                        "d_no_path_compression": len(finds) >= 1 and comp == 0 and all(len(b) == 1 for b in loop_bodies)}}


def rail_name_count(tree):
    return sum(1 for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == "_RAIL_NETS")


def doc_nodes(tree):
    ids = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.body and is_doc(n.body[0]):
            ids.add(id(n.body[0].value))
    return ids


def str_consts(tree):
    d = doc_nodes(tree)
    return collections.Counter(n.value for n in ast.walk(tree)
                               if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in d)


def call_sites(tree, names):
    out = []
    def visit(node, owner):
        for ch in ast.iter_child_nodes(node):
            o = owner
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                o = ch.name if owner is None else (owner + "." + ch.name if isinstance(node, ast.ClassDef) else owner)
            if isinstance(ch, ast.Call) and isinstance(ch.func, ast.Name) and ch.func.id in names:
                out.append([ch.func.id, owner if owner else "<module>", ch.lineno])
            visit(ch, o)
    visit(tree, None)
    return out


def defs_dump(tree):
    res = {}
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            key = n.name
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            tg = n.targets if isinstance(n, ast.Assign) else [n.target]
            key = "=" + ",".join(ast.unparse(t) for t in tg)
        else:
            key = "@%s:%d" % (type(n).__name__, n.lineno)
        full = ast.dump(n)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            c = ast.parse(ast.unparse(n)).body[0]
            c.body = strip_doc(c.body) or [ast.Pass()]
            nodoc = ast.dump(c)
        else:
            nodoc = full
        if key in res:
            key = key + "#%d" % n.lineno
        res[key] = {"line": n.lineno, "dump": sha(full), "dump_nodoc": sha(nodoc)}
    return res


def measure(root):
    rd = lambda rel: open(os.path.join(root, rel), "rb").read()
    sd_src = rd(SD_REL)
    sd_tree = ast.parse(sd_src)
    ksu = find_top_def(sd_tree, "kcl_series_union")
    kme = find_top_def(sd_tree, "_kcl_and_matching_edges")
    A = os.path.join(root, "skills", "analog-gmid-design", "assets")
    py = sorted(glob.glob(os.path.join(A, "*.py")))
    strs, sites, fsha = {}, [], {}
    for p in py + [os.path.join(root, "workspaces", "run_harness.py")]:
        rel = os.path.relpath(p, root).replace("\\", "/")
        b = open(p, "rb").read()
        fsha[rel] = sha(b)
        t = ast.parse(b)
        strs[rel] = dict(sorted(str_consts(t).items()))
        if p in py:
            for s in call_sites(t, {"kcl_series_union", "_kcl_and_matching_edges"}):
                sites.append([rel] + s)
    lib = {os.path.relpath(p, root).replace("\\", "/"): sha(open(p, "rb").read())
           for p in sorted(glob.glob(os.path.join(A, "library", "*")))}
    return {
        "c1_kcl_series_union": c1_measure(ksu),
        "c3a_canonical": {"line": kme.lineno, "args_dump": ast.dump(kme.args), "returns_dump": ast.dump(kme.returns) if kme.returns else None,
                          "dump_with_doc_sha256": sha(ast.dump(kme))},
        "c5b_rail_nets_name_refs": rail_name_count(sd_tree),
        "c5b_rail_nets_line_grep": sum(1 for l in sd_src.decode("utf-8").splitlines() if "_RAIL_NETS" in l),
        "c5a_str_consts_total": sum(sum(v.values()) for v in strs.values()),
        "c5a_str_consts_by_file": strs,
        "c6_call_sites": sites,
        "c7_sd_top_defs": defs_dump(sd_tree),
        "c7_file_sha256": fsha,
        "c7_library_sha256": lib,
        "sd_sha256": sha(sd_src),
    }


SELF = {
    "reject_rail_source": '''
def kcl_series_union(netlist, matching_pairs):
    """doc"""
    net_uses = {}
    for t in netlist:
        net_uses.setdefault(t.source, []).append(t.name)
    parent = {t.name: t.name for t in netlist}
    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for net, uses in net_uses.items():
        if net in _RAIL_NETS:
            continue
    for a, b, _k, _d in _kcl_and_matching_edges(netlist, matching_pairs):
        pass
    return {}
''',
    "reject_path_compression": '''
def kcl_series_union(netlist, matching_pairs):
    """doc mentions _RAIL_NETS and t.source only in text"""
    parent = {t.name: t.name for t in netlist}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b, _k, _d in _kcl_and_matching_edges(netlist, matching_pairs):
        pass
    return {}
''',
    "accept_canonical_only": '''
def kcl_series_union(netlist, matching_pairs):
    """doc mentions _RAIL_NETS, .source, .drain, parent[x] = parent[parent[x]]"""
    parent = {t.name: t.name for t in netlist}
    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    for a, b, _kind, _detail in _kcl_and_matching_edges(netlist, matching_pairs):
        union(a, b)
    return {}
''',
    "reject_no_call": '''
def kcl_series_union(netlist, matching_pairs):
    parent = {t.name: t.name for t in netlist}
    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    return {}
''',
}


def selftest():
    out = {}
    for k, s in SELF.items():
        v = c1_measure(ast.parse(s).body[0])["verdict"]
        out[k] = all(v.values())
        print(k, v, "PASS" if out[k] else "REJECT")
    assert out == {"reject_rail_source": False, "reject_path_compression": False, "accept_canonical_only": True, "reject_no_call": False}, out
    # 5(b): docstring에만 _RAIL_NETS 글자 -> 참조 수 0
    t = ast.parse('_RAIL_NETS = frozenset()\ndef f():\n    """_RAIL_NETS in doc"""\n    return _RAIL_NETS\n# _RAIL_NETS comment\n')
    assert rail_name_count(t) == 2, rail_name_count(t)
    t2 = ast.parse('def f():\n    """_RAIL_NETS only in doc"""\n    return 1\n')
    assert rail_name_count(t2) == 0
    # 5(a): 합성 병합본에 새 문자열 상수 -> 발견, docstring 변경은 제외, f-string 조각 포함
    b = str_consts(ast.parse('def f():\n    """old doc"""\n    return "a" + f"x{1}y"\n'))
    m = str_consts(ast.parse('def f():\n    """new doc changed"""\n    return "a" + f"x{1}y" + "vss"\n'))
    new = m - b
    assert dict(new) == {"vss": 1}, new
    assert b == collections.Counter({"a": 1, "x": 1, "y": 1}), b
    print("selftest OK: 1(a)(b)(c)(d) reject/accept 4/4, 5(b) doc-only 0, 5(a) new const found {'vss': 1}, doc change ignored")


if __name__ == "__main__":
    if sys.argv[1] == "selftest":
        selftest()
    else:
        r = measure(os.path.abspath(sys.argv[2]))
        json.dump(r, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        c1 = r["c1_kcl_series_union"]
        print("c1", {k: c1[k] for k in ("calls_canonical", "rail_nets_refs", "source_drain_attrs", "n_nested_find", "path_compression_assigns_in_find_loops")}, c1["verdict"])
        print("c3a", r["c3a_canonical"]["line"], r["c3a_canonical"]["dump_with_doc_sha256"])
        print("c5b", r["c5b_rail_nets_name_refs"], "line grep", r["c5b_rail_nets_line_grep"])
        print("c5a total", r["c5a_str_consts_total"], "files", len(r["c5a_str_consts_by_file"]))
        print("c6", r["c6_call_sites"])
        print("c7 sd defs", len(r["c7_sd_top_defs"]), "ksu", r["c7_sd_top_defs"]["kcl_series_union"])
