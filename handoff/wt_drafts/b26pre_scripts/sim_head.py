"""B26-1 / P9 시뮬레이션 head 생성 + V3 비용 측정 (mutate_changed.py 함수만 import, main 미실행).
결과는 C:/g87/out/v3_measure.json 과 C:/g87/out/v3_measure.txt 에 쓴다."""
import ast, copy, difflib, io, json, os, re, sys, tokenize

BASE = "C:/g87/b1"
sys.path.insert(0, BASE + "/tools/gates")
import mutate_changed as mc   # noqa: E402
import reachability as rch     # noqa: E402

A = "skills/analog-gmid-design/assets/"
SD, SR = A + "stick_diagram.py", A + "sizing_recipe.py"
OUT = open("C:/g87/out/v3_measure.txt", "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n"); OUT.flush()


def read_files():
    files = {}
    for pre in rch.GRAPH_PREFIXES:
        for dp, _dn, fns in os.walk(os.path.join(BASE, pre)):
            for fn in fns:
                if fn.endswith(".py"):
                    full = os.path.join(dp, fn)
                    rel = os.path.relpath(full, BASE).replace("\\", "/")
                    with open(full, encoding="utf-8", errors="replace") as fh:
                        files[rel] = fh.read()
    return files


BASEF = read_files()

TARGET_SD = ["find_matching_candidates", "find_differential_pair_candidates", "_diff_pair_layer1_groups",
             "_propose_gm_id_roles", "_propose_L_roles", "kcl_series_union", "_kcl_and_matching_edges",
             "audit_vertical_stack_id_vs_kcl", "propose_device_roles_gap_fill", "check_symmetry_dispositions",
             "run_full_circuit_audit", "refine_differential_and_mirror_relations",
             "propose_vertical_stack_id_gap_fill", "_kcl_branch_map", "_branch_composite_pair",
             "_composite_collapse_for_crossover", "find_min_crossover_layout_with_branch_composite",
             "repair_matching_safety"]
TARGET_SR = ["true_current_mirror_groups", "resolve_stack_layout"]
TARGETS = set(TARGET_SD) | set(TARGET_SR)
SITE_SD = [1014, 1575, 1617, 2096, 2172, 3042, 3148, 3253, 3992, 4171, 4307, 4323, 4370, 4392]


def byte_to_char(line, col):
    return len(line.encode("utf-8")[:col].decode("utf-8", "replace"))


class Editor:
    def __init__(self, src):
        self.lines = src.split("\n")
        self.ins = []      # (line_idx0, char_col, text)
        self.repl = {}     # line_idx0 -> new text (whole line, may contain \n)
        self.after = []    # (line_idx0, text) insert whole lines after line

    def insert(self, lineno, bcol, text):
        li = lineno - 1
        self.ins.append((li, byte_to_char(self.lines[li], bcol), text))

    def insert_char(self, li, ccol, text):
        self.ins.append((li, ccol, text))

    def render(self):
        lines = list(self.lines)
        for li, cc, text in sorted(self.ins, key=lambda x: (x[0], x[1]), reverse=True):
            lines[li] = lines[li][:cc] + text + lines[li][cc:]
        for li, t in self.repl.items():
            lines[li] = t(lines[li]) if callable(t) else t
        for li, text in sorted(self.after, key=lambda x: x[0], reverse=True):
            lines[li] = lines[li] + "\n" + text
        return "\n".join(lines)


def sig_close_paren(lines, fn):
    """def 줄부터 토큰으로 첫 '(' 짝 ')' 위치(0-based line, char col)."""
    start = fn.lineno - 1
    text = "\n".join(lines[start:fn.body[0].lineno])
    depth = 0
    for tok in tokenize.generate_tokens(io.StringIO(text + "\n").readline):
        if tok.type == tokenize.OP and tok.string == "(":
            depth += 1
        elif tok.type == tokenize.OP and tok.string == ")":
            depth -= 1
            if depth == 0:
                return start + tok.start[0] - 1, tok.start[1]
    raise RuntimeError(fn.name)


def prev_nonspace(lines, li, cc):
    while True:
        s = lines[li][:cc].rstrip()
        if s:
            return s[-1]
        li -= 1
        cc = len(lines[li])


def add_kwonly(ed, fn):
    li, cc = sig_close_paren(ed.lines, fn)
    a = fn.args
    has_star = a.vararg is not None or a.kwonlyargs
    nparams = len(a.posonlyargs) + len(a.args) + len(a.kwonlyargs) + (a.vararg is not None)
    pc = prev_nonspace(ed.lines, li, cc)
    if nparams == 0:
        txt = "*, rails"
    else:
        sep = " " if pc == "," else ", "
        txt = sep + ("rails" if has_star else "*, rails")
    ed.insert_char(li, cc, txt)


def add_call_kw(ed, call):
    li = call.end_lineno - 1
    cc = byte_to_char(ed.lines[li], call.end_col_offset) - 1   # ')' 위치
    assert ed.lines[li][cc] == ")", (call.lineno, ed.lines[li])
    pc = prev_nonspace(ed.lines, li, cc)
    if not call.args and not call.keywords:
        txt = "rails=rails"
    else:
        txt = (" " if pc == "," else ", ") + "rails=rails"
    ed.insert_char(li, cc, txt)


def body_insert(ed, fn, stmts):
    """docstring 뒤(없으면 첫 문장 앞)에 문장 줄 삽입."""
    b0 = fn.body[0]
    is_doc = isinstance(b0, ast.Expr) and isinstance(b0.value, ast.Constant) and isinstance(b0.value.value, str)
    ind = " " * byte_to_char(ed.lines[b0.lineno - 1], b0.col_offset)
    text = "\n".join(ind + s for s in stmts)
    if is_doc:
        ed.after.append((b0.end_lineno - 1, text))
    else:
        li = b0.lineno - 1
        old = ed.repl.get(li)
        ed.repl[li] = (lambda l, t=text, o=old: t + "\n" + (o(l) if callable(o) else (o if o is not None else l)))


def top_defs(tree):
    return {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def enclosing_top(tree):
    """노드 id -> 최상위 def 이름."""
    m = {}
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for x in ast.walk(n):
                m[id(x)] = n.name
    return m


def callee(c):
    f = c.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


ROOT_ACQ = {
    "load_topology": ["rails = rail_declaration(topology)", "for _lf in _linked_topologies:",
                      "    if 'supply_nets' in _lf and rail_declaration(_lf).nets != rails.nets:",
                      "        raise ValueError('supply_nets conflict (DEC-60)')", "meta['rails'] = rails"],
    "l_sharing_classes": ["if 'rails' not in meta:", "    raise ValueError('meta rails (DEC-60)')",
                          "rails = meta['rails']"],
    "_metric_kcl_residual": ["if 'rail_nets' in spec:", "    raise ValueError('rail_nets (DEC-60)')"],
}
DEFAULT_ACQ = ["rails = meta['rails']"]


def build_b26(files):
    head = dict(files)
    callers_outside = {}
    for path in (SD, SR) + tuple(p for p in files if p.startswith(A) and p.count("/") == 3 and p not in (SD, SR)) \
            + ("workspaces/run_harness.py",):
        src = files[path]
        tree = ast.parse(src)
        ed = Editor(src)
        tops = top_defs(tree)
        enc = enclosing_top(tree)
        # 1. 시그니처
        mine = TARGET_SD if path == SD else TARGET_SR if path == SR else []
        for name in mine:
            add_kwonly(ed, tops[name])
        # 2. 호출부
        need = set()
        for c in ast.walk(tree):
            if isinstance(c, ast.Call) and callee(c) in TARGETS:
                owner = enc.get(id(c))
                if owner is None:
                    continue
                add_call_kw(ed, c)
                if owner not in TARGETS:
                    need.add(owner)
        for owner in sorted(need):
            callers_outside.setdefault(path, []).append(owner)
            body_insert(ed, tops[owner], ROOT_ACQ.get(owner, DEFAULT_ACQ))
        for owner in ("load_topology", "l_sharing_classes", "_metric_kcl_residual"):
            if owner in tops and owner not in need and ((path == SD and owner == "load_topology") or
                                                         (path == SR and owner != "load_topology")):
                body_insert(ed, tops[owner], ROOT_ACQ[owner])
                callers_outside.setdefault(path, []).append(owner + "(직접)")
        # 3. 판정 사이트
        if path == SD:
            for n in SITE_SD:
                li = n - 1
                old = ed.repl.get(li)
                def f(l, o=old):
                    l = o(l) if callable(o) else l
                    l = l.replace('{"vdd": "vdd", "gnd": "gnd"}', "{n: n for n in rails.nets}")
                    return l.replace("_RAIL_NETS", "rails.nets")
                ed.repl[li] = f
            new_defs = ("\n\n@dataclass(frozen=True)\nclass RailDeclaration:\n    nets: frozenset\n\n\n"
                        "def rail_declaration(topology: dict) -> RailDeclaration:\n"
                        "    \"\"\"doc\"\"\"\n"
                        "    if 'supply_nets' not in topology:\n"
                        "        raise ValueError('supply_nets missing (DEC-60)')\n"
                        "    v = topology['supply_nets']\n"
                        "    if not isinstance(v, list):\n"
                        "        raise ValueError('supply_nets not list (DEC-60)')\n"
                        "    for x in v:\n"
                        "        if not isinstance(x, str) or not x:\n"
                        "            raise ValueError('supply_nets element (DEC-60)')\n"
                        "    if len(set(v)) != len(v):\n"
                        "        raise ValueError('supply_nets duplicate (DEC-60)')\n"
                        "    return RailDeclaration(nets=frozenset(v))\n")
        if path == SR:
            ed.repl[2207 - 1] = lambda l: l.replace("set(_DEFAULT_RAIL_HI) | set(_DEFAULT_RAIL_LO)", "set(rails.nets)")
            ed.repl[4293 - 1] = lambda l: l.replace(
                'set(spec.get("rail_nets") or ("vdd", "VDD", "gnd", "GND", "vss", "VSS"))',
                'set(_topology_meta_cached(ctx.topology_path)["rails"].nets)')
        out = ed.render()
        if path == SD:
            out = out.rstrip("\n") + "\n" + new_defs
        ast.parse(out)
        head[path] = out
    return head, callers_outside


def build_p9(files):
    head = dict(files)
    src = files[SD]
    tree = ast.parse(src)
    fn = top_defs(tree)["kcl_series_union"]
    lines = src.split("\n")
    body = "\n".join(lines[fn.lineno - 1:fn.end_lineno])
    new = body
    new = new.replace("""    net_uses: dict = defaultdict(list)
    for t in netlist:
        net_uses[t.source].append(t.name)
        net_uses[t.drain].append(t.name)

""", "")
    new = new.replace("""    for net, uses in net_uses.items():
        if net in _RAIL_NETS:
            continue
        if len(uses) == 2 and uses[0] != uses[1]:
            union(uses[0], uses[1])
    for names in matching_pairs:
        for a, b in zip(names, names[1:]):
            union(a, b)
""", """    for a, b, _kind, _detail in _kcl_and_matching_edges(netlist, matching_pairs):
        union(a, b)
""")
    assert new != body
    head[SD] = "\n".join(lines[:fn.lineno - 1]) + "\n" + new + "\n" + "\n".join(lines[fn.end_lineno:])
    ast.parse(head[SD])
    return head


def changed_line_set(base_src, head_src):
    """head 쪽에서 바뀌거나 새로 생긴 줄(1-based)."""
    sm = difflib.SequenceMatcher(None, base_src.split("\n"), head_src.split("\n"), autojunk=False)
    ch = set()
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            ch |= set(range(j1 + 1, j2 + 1))
    return ch


def own_lines(node):
    if isinstance(node, ast.stmt) and any(isinstance(getattr(node, f, None), list) and getattr(node, f)
                                          and isinstance(getattr(node, f)[0], ast.stmt)
                                          for f in ("body", "orelse", "finalbody", "handlers")):
        end = node.body[0].lineno - 1 if getattr(node, "body", None) else node.lineno
        return set(range(node.lineno, max(node.lineno, end) + 1))
    if isinstance(node, ast.ExceptHandler):
        return {node.lineno}
    if hasattr(node, "lineno"):
        return set(range(node.lineno, (node.end_lineno or node.lineno) + 1))
    return set()


def touched_count(fn, src, chlines, is_new):
    """diff가 닿은 문장·식에 걸린 변이 수(좁은 정의: 복합문은 머리 줄만, early_return은 새 def만)."""
    if is_new:
        return len(mc.mutants(fn, src))
    n = 0
    for op, path, _m in mc.mutants(fn, src):
        if op == "early_return":
            continue
        p = path
        if op == "cmp_flip":
            p = re.sub(r"\.ops\[\d+\]$", "", path)
        node = mc._get(fn, p) if p else fn
        if own_lines(node) & chlines:
            n += 1
    return n


def durations():
    """junit xml -> {test 함수 node id(파라미터 제외): 초 합}."""
    import xml.etree.ElementTree as ET
    d = {}
    try:
        root = ET.parse("C:/g87/out/junit_base.xml").getroot()
    except Exception:
        return None
    for tc in root.iter("testcase"):
        cls = tc.get("classname", "")
        name = re.sub(r"\[.*$", "", tc.get("name", ""))
        parts = cls.split(".")
        # classname = skills.analog-gmid-design.assets.tests.x.test_mod[.TestCls]
        path, qual = None, None
        for k in range(len(parts), 0, -1):
            cand = "/".join(parts[:k]) + ".py"
            if os.path.exists(os.path.join(BASE, cand)):
                path = cand
                qual = ".".join(parts[k:] + [name])
                break
        if path is None:
            continue
        key = "%s::%s" % (path, qual)
        d[key] = d.get(key, 0.0) + float(tc.get("time", 0) or 0)
    return d


def measure(label, head, extra_test=None):
    files = dict(head)
    if extra_test:
        files.update(extra_test)
    nodes, edges = rch.build_graph(files)
    tests = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
             and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
    dur = durations()
    rows = []
    for path in sorted(p for p in head if head[p] != BASEF.get(p) and rch._is_source(p)):
        chl = changed_line_set(BASEF.get(path, ""), head[path])
        bmap = {q: n for q, n in rch.iter_defs(ast.parse(BASEF[path]))} if path in BASEF else {}
        for q, fn in mc.changed_defs(BASEF.get(path), head[path]):
            ms = mc.mutants(fn, head[path])
            inv = mc.inventory(edges, "%s::%s" % (path, q), tests)
            t = None
            if dur is not None:
                t = sum(dur.get(x, 0.0) for x in inv)
            rows.append({"path": path, "def": q, "new": q not in bmap, "mutants": len(ms),
                         "touched": touched_count(fn, head[path], chl, q not in bmap),
                         "inventory": len(inv), "inv_seconds": t, "lines": fn.end_lineno - fn.lineno + 1})
    rows.sort(key=lambda r: -r["mutants"])
    log("== %s: changed defs %d, mutants %d, touched %d, no-inventory mutants %d" % (
        label, len(rows), sum(r["mutants"] for r in rows), sum(r["touched"] for r in rows),
        sum(r["mutants"] for r in rows if r["inventory"] == 0)))
    for r in rows:
        log("  %-60s new=%-5s mut=%4d touched=%3d inv=%4d inv_s=%s lines=%d" % (
            r["path"].split("/")[-1] + "::" + r["def"], r["new"], r["mutants"], r["touched"], r["inventory"],
            "%.1f" % r["inv_seconds"] if r["inv_seconds"] is not None else "-", r["lines"]))
    return rows


def base_defs_measure(label, names_by_path):
    nodes, edges = rch.build_graph(BASEF)
    tests = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
             and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
    dur = durations()
    rows = []
    for path, names in names_by_path.items():
        dm = dict(rch.iter_defs(ast.parse(BASEF[path])))
        for q in names:
            fn = dm[q]
            inv = mc.inventory(edges, "%s::%s" % (path, q), tests)
            rows.append({"path": path, "def": q, "mutants": len(mc.mutants(fn, BASEF[path])), "inventory": len(inv),
                         "inv_seconds": sum(dur.get(x, 0.0) for x in inv) if dur else None,
                         "lines": fn.end_lineno - fn.lineno + 1})
    log("== %s (base 본문 기준): defs %d, mutants %d" % (label, len(rows), sum(r["mutants"] for r in rows)))
    for r in rows:
        log("  %-60s mut=%4d inv=%4d inv_s=%s lines=%d" % (r["path"].split("/")[-1] + "::" + r["def"], r["mutants"],
                                                          r["inventory"], "%.1f" % r["inv_seconds"] if r["inv_seconds"] is not None else "-", r["lines"]))
    return rows


if __name__ == "__main__":
    res = {}
    head, outside = build_b26(BASEF)
    log("B26-1 roots (callers outside 20):", json.dumps(outside, ensure_ascii=False))
    res["b26"] = measure("B26-1 sim head", head)
    newtest = {A + "tests/contracts/test_b26_kcl_residual_direct.py":
               "import sizing_recipe as sr\n\ndef test_kcl_residual_direct():\n    sr._metric_kcl_residual({}, None)\n"}
    res["b26_with_direct_test"] = measure("B26-1 sim head + 이름 직접 참조 test", head, newtest)
    res["p9"] = measure("P9 sim head", build_p9(BASEF))
    b34_direct = ["_import_analog_grammar", "find_idiom_matches", "find_stack_edges", "find_differential_and_mirror_forks",
                  "suggest_vertical_stack_composites", "find_verified_differential_and_mirror_relations",
                  "_propose_vertical_stack_ids", "_propose_headroom_roles", "refine_differential_and_mirror_relations",
                  "audit_theta_root_direction", "propose_theta_kcl_gap_fill", "propose_device_roles_gap_fill"]
    b34_prop = ["find_differential_pair_candidates", "_propose_gm_id_roles", "_propose_L_roles",
                "propose_vertical_stack_id_gap_fill", "geometry_colocation_union", "load_topology"]
    res["b34_direct"] = base_defs_measure("B34 직접 폴백 def", {SD: b34_direct})
    res["b34_prop"] = base_defs_measure("B34 전파 폴백 def", {SD: b34_prop})
    with open("C:/g87/out/v3_measure.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
