"""card GC-1 M-G3·M-G9 기준선 측정(독립 스크립트 -- 규칙 L test 코드가 아니다, 계획 N3.1-6 (c)).

입력: 엔진 사본 경로(git archive, 저장소를 건드리지 않음)와 tables.json(dump_tables.py 결과, 교차 확인용).
출력: <out>/mg3_*.jsonl·summary.txt. 단계마다 파일에 쓴다.
정의 출처: graph-consumption 계획 N0.1·N3.1(규칙 L-1~L-5·부채), design §2·§3. LUT·엔진 평가 0.
"""
import ast
import json
import pathlib
import sys

ENGINE = pathlib.Path(sys.argv[1])
TABLES = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
OUT = pathlib.Path(sys.argv[3])
PKG = "gmid_engine"
ACCESSORS = {"value": 3, "field": 3, "column": 2, "column_fields": 2}
KINDS = {k for k, _f, _w in TABLES["writers"]}
ENTRY_DRAFT = [("pipeline.stage_a", "run_stage_a"), ("pipeline.stage_b", "run_stage_b"),
               ("search.find_front", "find_front"), ("search.front_query", "node_across_front")]
ENTRY_ADD = [("convergence.converge", "converge")]   # N0.1 '수렴 진입점' -- design 초기안에 없음(대조 실행)
ENTRY_REC = ENTRY_DRAFT + ENTRY_ADD + [("search.search_context", "build_search_context"), ("search.open_run", "open_run"), ("lut.lut_set", "load_lut_set"),
                                       ("lut.data_location", "resolve_lut_location"), ("core.pdk_decl", "read_pdk_decl"), ("search.front_entries", "read_front_entries")]
# 흐름 분석이 tuple 반환을 못 따라가는 자리를 손으로 확인: _coupling_stage 가 (s1, report, stop)을 돌려주고 run_stage_a 는 report 를 보고 dict "coupling" 칸에만 쓴다(stage_a.py:248,255).
HAND_OUTPUT = {"pipeline.stage_a:_coupling_report"}
BUILTIN_WRAP = {"sorted", "list", "tuple", "dict", "set", "frozenset", "len", "str", "repr", "float", "int", "bool", "sum", "min", "max", "any", "all",
                "enumerate", "zip", "map", "filter", "reversed", "round", "abs", "isinstance", "print"}


def emit(name, rows):
    with open(OUT / name, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


class Scope:
    """함수 하나(중첩 def 제외, lambda·컴프리헨션 포함) 또는 모듈 최상위(클래스 본문 포함)."""

    def __init__(self, sid, module, node, cls, parent):
        self.sid, self.module, self.node, self.cls, self.parent = sid, module, node, cls, parent
        self.nested = {}
        self.locals = set()
        self.body_nodes = []
        self.edges = set()
        self.sites = []        # (callee sid 집합, Call 또는 Load 노드)
        self.reads = []        # (kind, field, line, how)
        self.dynamic = []      # (line, 호출 원문)
        self.get_reads = []


modules, symbols, classes, method_index, imports, constants, tree_of = {}, {}, {}, {}, {}, {}, {}


def modname(path):
    rel = path.relative_to(ENGINE).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def load():
    for path in sorted(ENGINE.rglob("*.py")):
        rel = path.relative_to(ENGINE)
        if rel.parts[0] == "tests" or "__pycache__" in rel.parts:
            continue
        name = modname(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
        tree_of[name] = tree
        modules[name] = str(rel).replace("\\", "/")


def resolve_relative(mod, node):
    is_pkg = modules[mod].endswith("__init__.py")
    base = mod.split(".") if mod else []
    if node.level:
        cut = node.level - 1 if is_pkg else node.level
        base = base[:len(base) - cut] if cut else base
        return ".".join(base + ([node.module] if node.module else []))
    if node.module and (node.module == PKG or node.module.startswith(PKG + ".")):
        return node.module[len(PKG) + 1:]
    return None


def scope_build():
    scopes = {}

    def add_scope(node, module, cls, parent, qual):
        sid = module + ":" + qual
        s = Scope(sid, module, node, cls, parent)
        scopes[sid] = s
        if parent is not None:
            parent.nested[node.name] = s
        symbols[sid] = s
        return s

    def walk_body(body, scope, module, cls, prefix):
        for stmt in body:
            visit(stmt, scope, module, cls, prefix)

    def visit(node, scope, module, cls, prefix):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                scope.body_nodes.append(dec)
            for default in node.args.defaults + [d for d in node.args.kw_defaults if d]:
                scope.body_nodes.append(default)
            qual = prefix + node.name
            child = add_scope(node, module, cls, scope if scope.node is not tree_of[module] and not isinstance(scope.node, ast.ClassDef) else None, qual)
            if child.parent is None and cls is None:
                pass
            for arg in node.args.args + node.args.kwonlyargs + node.args.posonlyargs:
                child.locals.add(arg.arg)
            if node.args.vararg:
                child.locals.add(node.args.vararg.arg)
            if node.args.kwarg:
                child.locals.add(node.args.kwarg.arg)
            walk_body(node.body, child, module, None, qual + ".")
            if cls:
                method_index.setdefault(node.name, set()).add(child.sid)
            return
        if isinstance(node, ast.ClassDef):
            qual = prefix + node.name
            classes[module + ":" + qual] = node
            for dec in node.decorator_list + node.bases + [k.value for k in node.keywords]:
                scope.body_nodes.append(dec)
            for stmt in node.body:
                visit(stmt, scope, module, qual, qual + ".")
            return
        scope.body_nodes.append(node)

    for mod, tree in tree_of.items():
        top = Scope(mod + ":<module>", mod, tree, None, None)
        scopes[top.sid] = top
        walk_body(tree.body, top, mod, None, "")
    return scopes


def collect_imports():
    for mod, tree in tree_of.items():
        table = imports.setdefault(mod, {})
        const = constants.setdefault(mod, {})
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                base = resolve_relative(mod, node)
                for alias in node.names:
                    table[alias.asname or alias.name] = ("eng" if base is not None else "ext", base if base is not None else node.module, alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == PKG or alias.name.startswith(PKG + "."):
                        table[alias.asname or alias.name.split(".")[0]] = ("eng", alias.name[len(PKG) + 1:], None)
                    else:
                        table[alias.asname or alias.name.split(".")[0]] = ("ext", alias.name, None)
        for stmt in tree.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                const[stmt.targets[0].id] = stmt.value


def resolve_symbol(mod, name, seen=None):
    """모듈 mod 의 이름 name -> ('fn',sid)|('cls',cid)|('mod',m)|('const',(m,expr))|('ext',..)|None. 재수출을 따라간다."""
    seen = seen or set()
    if (mod, name) in seen or mod not in modules:
        return None
    seen.add((mod, name))
    sid = mod + ":" + name
    if sid in symbols:
        return ("fn", sid)
    if sid in classes:
        return ("cls", sid)
    if name in constants.get(mod, {}):
        return ("const", (mod, constants[mod][name]))
    entry = imports.get(mod, {}).get(name)
    if entry:
        where, base, attr = entry
        if where == "ext":
            return ("ext", base)
        if attr is None:
            return ("mod", base)
        if attr == "*":
            return None
        first = resolve_symbol(base, attr, seen)
        if first is not None:
            return first
        sub = (base + "." + attr) if base else attr
        return ("mod", sub) if sub in modules else None
    return None


def class_methods(cid):
    prefix = cid + "."
    return [sid for sid in symbols if sid.startswith(prefix)]


def locals_of(scope):
    names = set(scope.locals)
    for root in scope.body_nodes:
        for node in ast.walk(root):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                names.add(node.id)
    return names


def enclosing_nested(scope, name):
    cur = scope
    while cur is not None:
        if name in cur.nested:
            return cur.nested[name]
        cur = cur.parent
    return None


def targets_of_symbol(res):
    if res is None:
        return set()
    if res[0] == "fn":
        return {res[1]}
    if res[0] == "cls":
        return {res[1]}
    return set()


def analyse_edges(scopes):
    for scope in scopes.values():
        loc = locals_of(scope) if not scope.sid.endswith(":<module>") else set()
        scope.local_names = loc
        for root in scope.body_nodes:
            for node in ast.walk(root):
                targets = set()
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    nested = enclosing_nested(scope, node.id)
                    if nested is not None:
                        targets = {nested.sid}
                    elif node.id not in loc:
                        targets = targets_of_symbol(resolve_symbol(scope.module, node.id))
                elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                    targets = attr_targets(scope, node.value, node.attr, loc)
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr" and len(node.args) >= 2:
                    if isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
                        targets = attr_targets(scope, node.args[0], node.args[1].value, loc)
                    else:
                        scope.dynamic.append((node.lineno, "getattr_nonconst"))
                if targets:
                    scope.edges |= targets
                    scope.sites.append((targets, node))


def attr_targets(scope, recv, attr, loc):
    if isinstance(recv, ast.Name) and recv.id not in loc:
        res = resolve_symbol(scope.module, recv.id)
        if res is not None:
            if res[0] == "ext":
                return set()
            if res[0] == "mod":
                return targets_of_symbol(resolve_symbol(res[1], attr))
            if res[0] == "cls":
                sid = res[1] + "." + attr
                if sid in symbols:
                    return {sid}
    if isinstance(recv, ast.Name) and recv.id == "self":
        qual = scope.sid.split(":", 1)[1].rsplit(".", 1)[0]
        sid = scope.module + ":" + qual + "." + attr
        if sid in symbols:
            return {sid}
    return set(method_index.get(attr, ()))


def resolve_const(scope, expr, depth=0):
    """문자열 상수로 풀면 그 값, 아니면 None. 지역 단일 대입·모듈 상수·import 상수·모듈.상수."""
    if depth > 8:
        return None
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
        a, b = resolve_const(scope, expr.left, depth + 1), resolve_const(scope, expr.right, depth + 1)
        return None if a is None or b is None else a + b
    if isinstance(expr, ast.Name):
        if scope is not None and expr.id in getattr(scope, "local_names", ()):
            return None
        res = resolve_symbol(scope.module, expr.id)
        if res and res[0] == "const":
            mod, value = res[1]
            return resolve_const(scopes_by_mod[mod], value, depth + 1)
    if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
        res = resolve_symbol(scope.module, expr.value.id)
        if res and res[0] == "mod":
            sub = resolve_symbol(res[1], expr.attr)
            if sub and sub[0] == "const":
                return resolve_const(scopes_by_mod[sub[1][0]], sub[1][1], depth + 1)
    return None


def module_tuple(scope, expr, depth=0):
    """모듈 수준 tuple 이름을 파이썬 값(문자열·중첩 tuple)으로 펼친다. 못 풀면 None."""
    if depth > 8:
        return None
    if isinstance(expr, ast.Name) and expr.id not in getattr(scope, "local_names", ()):
        res = resolve_symbol(scope.module, expr.id)
        if res and res[0] == "const":
            mod, value = res[1]
            return tuple_value(scopes_by_mod[mod], value, depth + 1)
    if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
        res = resolve_symbol(scope.module, expr.value.id)
        if res and res[0] == "mod":
            sub = resolve_symbol(res[1], expr.attr)
            if sub and sub[0] == "const":
                return tuple_value(scopes_by_mod[sub[1][0]], sub[1][1], depth + 1)
    return None


def tuple_value(scope, expr, depth):
    if isinstance(expr, (ast.Tuple, ast.List)):
        out = []
        for elt in expr.elts:
            val = tuple_value(scope, elt, depth + 1)
            if val is None:
                return None
            out.append(val)
        return tuple(out)
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
        a, b = tuple_value(scope, expr.left, depth + 1), tuple_value(scope, expr.right, depth + 1)
        return None if a is None or b is None else a + b
    text = resolve_const(scope, expr, depth + 1)
    if text is not None:
        return text
    return module_tuple(scope, expr, depth + 1)


def bind_target(target, value, env):
    if isinstance(target, ast.Name):
        env.setdefault(target.id, []).append(value)
        return True
    if isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, tuple) and len(value) == len(target.elts):
        return all(bind_target(t, v, env) for t, v in zip(target.elts, value))
    return False


def loop_env(scope, call):
    """call 을 감싼 for·컴프리헨션의 루프 변수를 모듈 수준 tuple 로 펼친 환경 {이름: [값...]}."""
    env = {}
    node = call
    while hasattr(node, "parent"):
        node = node.parent
        gens = []
        if isinstance(node, (ast.For,)):
            gens = [(node.target, node.iter)]
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            gens = [(g.target, g.iter) for g in node.generators]
        for target, it in gens:
            val = module_tuple(scope, it)
            if val is None:
                continue
            for item in val:
                bind_target(target, item, env)
        if node is scope.node:
            break
    return env


def arg_values(scope, expr, env):
    if isinstance(expr, ast.Name) and expr.id in env:
        vals = [v for v in env[expr.id] if isinstance(v, str)]
        return sorted(set(vals)) or None
    val = resolve_const(scope, expr)
    return [val] if val is not None else None


def analyse_reads(scopes):
    for scope in scopes.values():
        for root in scope.body_nodes:
            for node in ast.walk(root):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                    continue
                attr = node.func.attr
                if attr == "get" and len(node.args) == 1:
                    recv = node.func.value
                    if isinstance(recv, ast.Call) and isinstance(recv.func, ast.Attribute) and recv.func.attr == "record":
                        val = resolve_const(scope, node.args[0])
                        scope.get_reads.append((node.lineno, val))
                if attr not in ACCESSORS or len(node.args) != ACCESSORS[attr] or node.keywords:
                    continue
                if isinstance(node.func.value, ast.Name):
                    res = None if node.func.value.id in scope.local_names else resolve_symbol(scope.module, node.func.value.id)
                    if res and res[0] == "ext":
                        continue
                env = loop_env(scope, node)
                kinds = arg_values(scope, node.args[0], env)
                fields = arg_values(scope, node.args[-1], env)
                if kinds is not None and not set(kinds) <= KINDS:
                    continue       # 이름이 같은 다른 객체의 메서드
                if kinds is None or fields is None:
                    scope.dynamic.append((node.lineno, ast.unparse(node)[:120]))
                    continue
                for kind in kinds:
                    for field in fields:
                        scope.reads.append((kind, field, node.lineno, attr))


def import_closure(start):
    seen, stack = set(), list(start)
    while stack:
        mod = stack.pop()
        if mod in seen or mod not in modules:
            continue
        seen.add(mod)
        parts = mod.split(".")
        for i in range(len(parts)):
            parent = ".".join(parts[:i])
            if parent in modules:
                stack.append(parent)
        for where, base, attr in imports.get(mod, {}).values():
            if where == "eng":
                stack.append(base)
                if attr and ((base + "." + attr) if base else attr) in modules:
                    stack.append((base + "." + attr) if base else attr)
    return seen


def reachable(scopes, entries):
    roots = [m + ":" + f for m, f in entries]
    closure = import_closure([m for m, _f in entries])
    stack = roots + [m + ":<module>" for m in closure]
    seen = set()
    while stack:
        sid = stack.pop()
        if sid in seen:
            continue
        seen.add(sid)
        if sid in classes:
            for meth in class_methods(sid):
                if meth.rsplit(".", 1)[-1].startswith("__"):
                    stack.append(meth)
            continue
        scope = scopes.get(sid)
        if scope is not None:
            stack.extend(scope.edges)
    return seen


def block_table(scopes):
    """@compute_block 함수 -> 블록 이름(AST). 교차 확인은 tables.json."""
    blocks = {}
    for sid, scope in scopes.items():
        node = scope.node
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == "compute_block":
                name = resolve_const(scope, dec.args[0]) if dec.args else None
                blocks[sid] = name
    return blocks


def descendants(scope):
    out = [scope]
    for child in scope.nested.values():
        out.extend(descendants(child))
    return out


# ---- 출력 함수 판정(N3.1-2): 최대 고정점 ----
def writes_file(scopes):
    direct = set()
    for sid, scope in scopes.items():
        for root in scope.body_nodes:
            for node in ast.walk(root):
                if isinstance(node, ast.Call):
                    fn = node.func
                    name = fn.attr if isinstance(fn, ast.Attribute) else fn.id if isinstance(fn, ast.Name) else ""
                    if name in ("write_text", "print", "dump", "writelines", "write_bytes") or (name == "write" and isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id in ("fh", "f", "stream", "sys")):
                        direct.add(sid)
    changed = True
    out = set(direct)
    while changed:
        changed = False
        for sid, scope in scopes.items():
            if sid in out:
                continue
            precise = set()
            for tgts, site in scope.sites:
                if isinstance(site, ast.Name):
                    precise |= tgts
            if precise & out:
                out.add(sid)
                changed = True
    return out


def stmt_of(node):
    cur = node
    while hasattr(cur, "parent") and not isinstance(cur, ast.stmt):
        cur = cur.parent
    return cur


def enclosing_call_arg(node, stop):
    """node 를 인자로 받는 가장 가까운 Call(리터럴·컴프리헨션은 투명). 없으면 None."""
    cur = node
    while hasattr(cur, "parent") and cur is not stop:
        par = cur.parent
        if isinstance(par, ast.Call) and cur is not par.func:
            return par
        if isinstance(par, ast.keyword) and isinstance(par.parent, ast.Call):
            return par.parent
        cur = par
    return None


def use_is_output(node, scope, scopes, output, entries_sid, write_set, visited):
    stmt = stmt_of(node)
    call = enclosing_call_arg(node, stmt)
    if isinstance(stmt, (ast.If, ast.While, ast.Assert)) and not _in_body_value(node, stmt):
        return False
    if isinstance(stmt, ast.For) and node_in(stmt.iter, node) is False:
        return False
    if call is not None:
        fn = call.func
        if isinstance(fn, ast.Name) and fn.id in BUILTIN_WRAP and fn.id not in scope.local_names and enclosing_nested(scope, fn.id) is None and not resolve_symbol(scope.module, fn.id):
            return use_is_output(call, scope, scopes, output, entries_sid, write_set, visited)
        targets = None
        for tgts, site in scope.sites:
            if site is fn:
                targets = tgts
                break
        if targets:
            if any(t in classes for t in targets):
                return isinstance(stmt, ast.Return) and (scope.sid in entries_sid or scope.sid in output)
            if all(t in output for t in targets):
                return use_is_output(call, scope, scopes, output, entries_sid, write_set, visited)
            return False
        if isinstance(fn, ast.Attribute):
            if fn.attr in ("append", "extend", "add", "update", "setdefault"):
                base = fn.value
                while isinstance(base, (ast.Attribute, ast.Subscript, ast.Call)):
                    base = base.func if isinstance(base, ast.Call) else base.value
                if isinstance(base, ast.Name):
                    return name_is_output(base.id, scope, scopes, output, entries_sid, write_set, visited)
                return False
            if fn.attr in ("dumps", "join", "items", "values", "keys", "format", "get", "sort", "as_posix"):
                return use_is_output(call, scope, scopes, output, entries_sid, write_set, visited)
            return False
        return False
    if isinstance(stmt, ast.Return):
        return scope.sid in output or scope.sid in entries_sid
    if isinstance(stmt, ast.Expr):
        return True
    if isinstance(stmt, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
        targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
        ok = True
        for target in targets:
            base = target
            while isinstance(base, (ast.Subscript, ast.Attribute)):
                base = base.value
            if isinstance(target, (ast.Tuple, ast.List)):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        ok = ok and name_is_output(elt.id, scope, scopes, output, entries_sid, write_set, visited)
                continue
            if isinstance(base, ast.Name) and not (isinstance(target, ast.Attribute)):
                ok = ok and name_is_output(base.id, scope, scopes, output, entries_sid, write_set, visited)
            else:
                ok = False
        return ok
    return False


def node_in(root, node):
    return any(n is node for n in ast.walk(root))


def _in_body_value(node, stmt):
    return not node_in(stmt.test, node)


def name_is_output(name, scope, scopes, output, entries_sid, write_set, visited):
    key = (scope.sid, name)
    if key in visited:
        return True
    visited.add(key)
    for root in scope.body_nodes:
        for node in ast.walk(root):
            if isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, ast.Load):
                if not use_is_output(node, scope, scopes, output, entries_sid, write_set, visited):
                    return False
    return True


def output_functions(scopes, reach, entries):
    entries_sid = {m + ":" + f for m, f in entries}
    write_set = writes_file(scopes)
    callers = {}
    for sid, scope in scopes.items():
        if sid in reach:
            for tgts, site in scope.sites:
                for t in tgts:
                    callers.setdefault(t, []).append((scope, site))
    output = {sid for sid in reach if sid in scopes and sid not in entries_sid and not sid.endswith(":<module>") and not sid.rsplit(".", 1)[-1].startswith("__")}
    changed = True
    while changed:
        changed = False
        for sid in sorted(output):
            uses = callers.get(sid, [])
            good = bool(uses)
            for scope, site in uses:
                if scope.sid.endswith(":<module>"):
                    good = False
                    break
                call = site.parent if isinstance(site.parent, ast.Call) and site.parent.func is site else None
                if call is None:
                    good = False
                    break
                if isinstance(stmt_of(call), ast.Expr) and stmt_of(call).value is call:
                    if sid not in write_set:
                        good = False
                        break
                    continue
                if not use_is_output(call, scope, scopes, output, entries_sid, write_set, set()):
                    good = False
                    break
            if not good:
                output.discard(sid)
                changed = True
    return output


# ---- 규칙 ----
def rule_l1_l2(scopes, reach, output, blocks):
    writer_scopes = {}
    for sid, name in blocks.items():
        writer_scopes.setdefault(name, set()).update(d.sid for d in descendants(scopes[sid]))
    table = {(k, f): w for k, f, w in TABLES["writers"]}
    rows = {}
    for key in table:
        rows[key] = {"reads_reach": [], "reads_unreach": [], "reads_writer": []}
    for sid, scope in scopes.items():
        for kind, field, line, how in scope.reads:
            if (kind, field) not in rows:
                continue
            row = rows[(kind, field)]
            where = modules[scope.module] + ":" + str(line) + " " + sid.split(":", 1)[1]
            if sid in writer_scopes.get(table[(kind, field)], ()):
                row["reads_writer"].append(where)
            elif sid in reach:
                row["reads_reach"].append((where, sid in output))
            else:
                row["reads_unreach"].append(where)
    out = []
    for (kind, field), row in sorted(rows.items()):
        reads = row["reads_reach"]
        cls = "ok"
        if not reads:
            cls = "L-1"
        elif all(flag for _w, flag in reads):
            cls = "L-2"
        out.append({"kind": kind, "field": field, "writer": table[(kind, field)], "class": cls,
                    "reads": [w for w, _f in reads], "output_flags": [f for _w, f in reads],
                    "reads_unreachable": row["reads_unreach"], "reads_in_writer": row["reads_writer"]})
    return out


def rule_l3(scopes, blocks):
    block_by_name = {name: sid for sid, name in blocks.items()}
    rows = []
    for name, reads, _writes in TABLES["blocks"]:
        sid = block_by_name.get(name)
        if sid is None:
            rows.append({"block": name, "column": None, "status": "block_function_not_found"})
            continue
        scope = scopes[sid]
        param = scope.node.args.args[0].arg if scope.node.args.args else None
        found = set()
        tainted = {param}
        helper_scopes, deep = [], []
        for sc in descendants(scope):
            for kind, field, _l, _h in sc.reads:
                found.add((kind, field))
            for root in sc.body_nodes:
                for node in ast.walk(root):
                    if isinstance(node, ast.Call) and any(isinstance(a, ast.Name) and a.id in tainted for a in list(node.args) + [k.value for k in node.keywords]):
                        tg = None
                        for tgts, site in sc.sites:
                            if site is node.func:
                                tg = tgts
                                break
                        if not tg:
                            deep.append((sc.sid, ast.unparse(node.func)[:60]))
                            continue
                        for t in tg:
                            pkg = t.split(":")[0].split(".")[0]
                            same = pkg == scope.module.split(".")[0]
                            if not same:
                                deep.append((sc.sid, t))
                            elif t in classes:
                                helper_scopes.extend(scopes[m] for m in class_methods(t))
                            elif t in scopes:
                                helper_scopes.append(scopes[t])
        passes_on = list(deep)
        for hs in helper_scopes:
            hparams = {a.arg for a in hs.node.args.args}
            for sc in descendants(hs):
                for root in sc.body_nodes:
                    for node in ast.walk(root):
                        if isinstance(node, ast.Call) and any(isinstance(a, ast.Name) and a.id in hparams for a in node.args) and not isinstance(node.func, ast.Attribute) and not (isinstance(node.func, ast.Name) and node.func.id in BUILTIN_WRAP):
                            passes_on.append((sc.sid, "helper_passes:" + ast.unparse(node.func)[:40]))
            for sc in descendants(hs):
                for kind, field, _l, _h in sc.reads:
                    found.add((kind, field))
                if sc.dynamic:
                    passes_on.append((sc.sid, "dynamic"))
        for sc in descendants(scope):
            if sc.dynamic:
                passes_on.append((sc.sid, "dynamic"))
        for kind, field in reads:
            if (kind, field) in found:
                continue
            rows.append({"block": name, "column": kind + "." + field,
                         "status": "reads_unverifiable" if passes_on else "reads_not_read",
                         "passes_on": sorted(set(str(p) for p in passes_on))[:5]})
    return rows


def is_frozen_dc(node):
    for dec in node.decorator_list:
        if isinstance(dec, ast.Call) and "dataclass" in ast.unparse(dec.func):
            for kw in dec.keywords:
                if kw.arg == "frozen" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    return True
    return False


def rule_l4(scopes):
    loads = set()
    strings = set()
    for mod, tree in tree_of.items():
        class_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                recv_self = isinstance(node.value, ast.Name) and node.value.id == "self"
                if not recv_self:
                    loads.add(node.attr)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr" and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                loads.add(node.args[1].value)
        for stmt in tree.body:
            if isinstance(stmt, ast.Assign):
                for node in ast.walk(stmt.value):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        strings.add(node.value)
        del class_nodes
    rows = []
    for mod, tree in tree_of.items():
        public = [s for s in tree.body if isinstance(s, (ast.FunctionDef, ast.ClassDef)) and not s.name.startswith("_")]
        decl_module = bool(public) and all(isinstance(s, ast.ClassDef) for s in public)
        for stmt in tree.body:
            if not (isinstance(stmt, ast.ClassDef) and is_frozen_dc(stmt)):
                continue
            for item in stmt.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    slot = item.target.id
                    rows.append({"module": mod, "cls": stmt.name, "slot": slot, "decl_module": decl_module,
                                 "read": slot in loads, "registry": slot in strings})
    return rows


GATE, DRAIN, SOURCE = ("g", "gate", "MOS_GATE"), ("d", "drain", "MOS_DRAIN"), ("s", "source", "MOS_SOURCE")


def pin_token(scope, expr):
    """핀 표현식 -> 'g'·'d'·'s' 또는 None: 속성 .g, 첨자 ["g"], 첨자 상수 이름, 지역 이름(g·gate 등)."""
    if isinstance(expr, ast.Attribute):
        name = expr.attr
    elif isinstance(expr, ast.Subscript):
        key = expr.slice
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            name = key.value
        elif isinstance(key, ast.Name):
            name = key.id
        else:
            return None
    elif isinstance(expr, ast.Name):
        name = expr.id
    else:
        return None
    for token, group in (("g", GATE), ("d", DRAIN), ("s", SOURCE)):
        if name in group:
            return token
    return None


def rule_l5(scopes, reach):
    diode, gs = [], []
    for sid, scope in scopes.items():
        for root in scope.body_nodes:
            for node in ast.walk(root):
                if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
                    pair = {pin_token(scope, node.left), pin_token(scope, node.comparators[0])}
                    if pair == {"g", "d"}:
                        diode.append({"file": modules[scope.module], "line": node.lineno, "fn": sid.split(":", 1)[1], "reach": sid in reach, "src": ast.unparse(node)[:70]})
                if isinstance(node, ast.Tuple):
                    toks = [pin_token(scope, e) for e in node.elts]
                    if len(node.elts) in (2, 3) and toks[-2:] == ["g", "s"]:
                        par = node.parent
                        role = type(par).__name__
                        if isinstance(par, ast.keyword):
                            role = "keyword"
                        gs.append({"file": modules[scope.module], "line": node.lineno, "fn": sid.split(":", 1)[1], "reach": sid in reach, "arity": len(node.elts),
                                   "ctx": role, "store": isinstance(node.ctx, ast.Store), "src": ast.unparse(node.parent)[:90]})
    return diode, gs


DEVICE_OP_SLOTS = None


def rule_l5_op(scopes, reach):
    """출처 = dc_op 읽기. 지역 전파 + 함수 인자(한 고정점). 산술이면 끊는다. 후보만 내고 분류는 수작업 표(문서)."""
    tainted = {}   # sid -> 이름 집합
    for sid, scope in scopes.items():
        if any(field == "dc_op" for _k, field, _l, _h in scope.reads):
            tainted[sid] = set()
    def is_source(scope, expr, names):
        if isinstance(expr, ast.Name):
            return expr.id in names
        if isinstance(expr, ast.Attribute):
            return is_source(scope, expr.value, names)
        if isinstance(expr, ast.Subscript):
            return is_source(scope, expr.value, names)
        if isinstance(expr, ast.Call):
            fn = expr.func
            if isinstance(fn, ast.Name) and fn.id in ("float", "int", "dict", "tuple", "list") and expr.args:
                return is_source(scope, expr.args[0], names)
            if isinstance(fn, ast.Attribute) and fn.attr in ACCESSORS and len(expr.args) == ACCESSORS[fn.attr]:
                return resolve_const(scope, expr.args[-1]) == "dc_op"
            if isinstance(fn, ast.Attribute) and fn.attr in ("items", "values"):
                return is_source(scope, fn.value, names)
        if isinstance(expr, (ast.GeneratorExp, ast.ListComp)):
            return False
        return False
    sinks = []
    for _ in range(6):
        grew = False
        for sid in sorted(tainted):
            scope = scopes[sid]
            names = tainted[sid]
            for _inner in range(4):
                before = len(names)
                for root in scope.body_nodes:
                    for node in ast.walk(root):
                        if isinstance(node, ast.Assign) and is_source(scope, node.value, names):
                            for target in node.targets:
                                for n in ast.walk(target):
                                    if isinstance(n, ast.Name):
                                        names.add(n.id)
                        if isinstance(node, (ast.For, ast.comprehension)) and is_source(scope, node.iter, names):
                            for n in ast.walk(node.target):
                                if isinstance(n, ast.Name):
                                    names.add(n.id)
                grew = grew or len(names) != before
            for root in scope.body_nodes:
                for node in ast.walk(root):
                    if isinstance(node, ast.Call):
                        tgts = None
                        for t, site in scope.sites:
                            if site is node.func:
                                tgts = t
                                break
                        if not tgts:
                            continue
                        for t in tgts:
                            if t in scopes and isinstance(scopes[t].node, (ast.FunctionDef,)) and not t.startswith("core.") and isinstance(node.func, ast.Name):
                                params = [a.arg for a in scopes[t].node.args.args]
                                for i, arg in enumerate(node.args):
                                    if i < len(params) and is_source(scope, arg, names):
                                        if t not in tainted:
                                            tainted[t] = set()
                                            grew = True
                                        if params[i] not in tainted[t]:
                                            tainted[t].add(params[i])
                                            grew = True
        if not grew:
            break
    seen = set()
    for sid, names in tainted.items():
        scope = scopes[sid]
        for root in scope.body_nodes:
            for node in ast.walk(root):
                kind, src = None, None
                if isinstance(node, ast.Call):
                    tgts = None
                    for t, site in scope.sites:
                        if site is node.func:
                            tgts = t
                            break
                    clss = [t for t in (tgts or ()) if t in classes]
                    args = list(node.args) + [k.value for k in node.keywords]
                    if clss and any(is_source(scope, a, names) for a in args):
                        kind, src = "ctor:" + clss[0].split(":", 1)[1], ast.unparse(node)[:110]
                    fn = node.func
                    if isinstance(fn, ast.Attribute) and fn.attr == "write" and any(is_source(scope, a, names) for a in args):
                        kind, src = "snapshot.write", ast.unparse(node)[:110]
                elif isinstance(node, ast.Return) and node.value is not None and is_source(scope, node.value, names):
                    kind, src = "return", ast.unparse(node)[:110]
                elif isinstance(node, ast.Dict) and any(v is not None and is_source(scope, v, names) for v in node.values):
                    kind, src = "dict_value", ast.unparse(node)[:110]
                elif isinstance(node, ast.Assign) and is_source(scope, node.value, names) and any(isinstance(t, ast.Attribute) for t in node.targets):
                    kind, src = "attr_assign", ast.unparse(node)[:110]
                if kind and (sid, node.lineno, kind) not in seen:
                    seen.add((sid, node.lineno, kind))
                    sinks.append({"file": modules[scope.module], "line": node.lineno, "fn": sid.split(":", 1)[1], "reach": sid in reach, "sink": kind, "src": src})
    return sorted(sinks, key=lambda r: (r["file"], r["line"]))


def zero_callers(scopes, entries, blocks):
    entry_ids = {m + ":" + f for m, f in entries}
    callers = {}
    for sid, scope in scopes.items():
        for tgts, _site in scope.sites:
            for t in tgts:
                if t != sid and not sid.startswith(t + "."):
                    callers.setdefault(t, set()).add(sid)
    fn_rows, cls_rows = [], []
    for sid, scope in scopes.items():
        if sid.endswith(":<module>") or sid in entry_ids:
            continue
        leaf = sid.rsplit(":", 1)[1].rsplit(".", 1)[-1]
        if leaf.startswith("__") and leaf.endswith("__"):
            continue
        if not callers.get(sid):
            fn_rows.append({"fn": sid, "file": modules[scope.module], "line": scope.node.lineno, "is_block": sid in blocks,
                            "is_method": scope.sid.split(":", 1)[1].count(".") > 0})
    for cid, node in classes.items():
        if not callers.get(cid):
            cls_rows.append({"cls": cid, "file": modules[cid.split(":")[0]], "line": node.lineno})
    return fn_rows, cls_rows


def main():
    global scopes_by_mod
    load()
    scopes = scope_build()
    scopes_by_mod = {sid.split(":")[0]: scope for sid, scope in scopes.items() if sid.endswith(":<module>")}
    collect_imports()
    for scope in scopes.values():
        scope.local_names = locals_of(scope) if not scope.sid.endswith(":<module>") else set()
    analyse_edges(scopes)
    analyse_reads(scopes)
    blocks = block_table(scopes)
    lines = []
    ast_names = sorted(n for n in blocks.values() if n)
    dyn_names = sorted(n for n, _r, _w in TABLES["blocks"])
    lines.append("modules=%d scopes=%d classes=%d blocks(AST)=%d blocks(import)=%d diff=%s" % (len(modules), len(scopes), len(classes), len(ast_names), len(dyn_names), sorted(set(ast_names) ^ set(dyn_names))))
    lines.append("fields(table)=%d" % len(TABLES["writers"]))
    for label, entries in (("draft", ENTRY_DRAFT), ("draft+converge", ENTRY_DRAFT + ENTRY_ADD), ("recommended", ENTRY_REC)):
        missing = [e for e in entries if e[0] + ":" + e[1] not in scopes]
        reach = reachable(scopes, entries)
        output = output_functions(scopes, reach, entries) | (HAND_OUTPUT & reach)
        rows = rule_l1_l2(scopes, reach, output, blocks)
        emit("mg3_fields_%s.jsonl" % label.replace("+", "_"), rows)
        fn_scopes = [s for s in scopes if not s.endswith(":<module>")]
        lines.append("[%s] missing_entries=%s reach=%d/%d output_fns=%d L-1=%d L-2=%d ok=%d" % (label, missing, len([s for s in fn_scopes if s in reach]), len(fn_scopes), len(output),
                     sum(r["class"] == "L-1" for r in rows), sum(r["class"] == "L-2" for r in rows), sum(r["class"] == "ok" for r in rows)))
        emit("mg9_output_functions_%s.jsonl" % label.replace("+", "_"), [{"fn": s, "file": modules[s.split(":")[0]], "reads": sorted({k + "." + f for k, f, _l, _h in scopes[s].reads})} for s in sorted(output)])
        emit("mg9_unreached_%s.jsonl" % label.replace("+", "_"), [{"fn": s, "file": modules[s.split(":")[0]]} for s in sorted(fn_scopes) if s not in reach])
        if label == "recommended":
            reach_draft, output_draft = reach, output
            entry_sids = {m + ":" + f for m, f in entries}
            only_entry = []
            for row in rows:
                if row["class"] == "ok" and row["reads"] and all(r.split(" ", 1)[1] in {e.split(":", 1)[1] for e in entry_sids} and any(r.startswith(modules[e.split(":")[0]]) for e in entry_sids) for r in row["reads"]):
                    only_entry.append({"field": row["kind"] + "." + row["field"], "reads": row["reads"]})
            emit("mg9_fields_read_only_in_entry_body.jsonl", only_entry)
            lines.append("fields read only in entry bodies=%d" % len(only_entry))
    dyn = []
    gets = []
    for sid, scope in sorted(scopes.items()):
        for line, src in scope.dynamic:
            dyn.append({"file": modules[scope.module], "line": line, "fn": sid.split(":", 1)[1], "reach": sid in reach_draft, "src": src})
        for line, val in scope.get_reads:
            gets.append({"file": modules[scope.module], "line": line, "fn": sid.split(":", 1)[1], "field": val})
    emit("mg3_dynamic.jsonl", dyn)
    emit("mg3_record_get_reads.jsonl", gets)
    lines.append("dynamic_sites=%d (reach=%d) record.get_reads=%d" % (len(dyn), sum(d["reach"] for d in dyn), len(gets)))
    l3 = rule_l3(scopes, blocks)
    emit("mg3_l3.jsonl", l3)
    lines.append("L-3 items=%d not_read=%d unverifiable=%d no_fn=%d" % (len(l3), sum(r["status"] == "reads_not_read" for r in l3), sum(r["status"] == "reads_unverifiable" for r in l3), sum(r["status"] == "block_function_not_found" for r in l3)))
    l4 = rule_l4(scopes)
    emit("mg3_l4.jsonl", l4)
    zero = [r for r in l4 if not r["read"] and not r["registry"]]
    lines.append("L-4 slots=%d zero=%d | decl_module slots=%d zero=%d" % (len(l4), len(zero), sum(r["decl_module"] for r in l4), sum(r["decl_module"] for r in zero)))
    diode, gs = rule_l5(scopes, reach_draft)
    emit("mg3_l5_diode.jsonl", diode)
    emit("mg3_l5_gs.jsonl", gs)
    lines.append("L-5 diode_sites=%d gs_tuple_sites=%d" % (len(diode), len(gs)))
    sinks = rule_l5_op(scopes, reach_draft)
    emit("mg3_l5_op.jsonl", sinks)
    lines.append("L-5 op sink candidates=%d (reach=%d)" % (len(sinks), sum(s["reach"] for s in sinks)))
    kind_keys = []
    for sid, scope in scopes.items():
        for root in scope.body_nodes:
            for node in ast.walk(root):
                if isinstance(node, ast.DictComp) and isinstance(node.key, ast.Tuple) and len(node.key.elts) == 3:
                    first = ast.unparse(node.key.elts[0])
                    if "kind" in first:
                        kind_keys.append({"file": modules[scope.module], "line": node.lineno, "fn": sid.split(":", 1)[1], "src": ast.unparse(node.key)[:80]})
    emit("mg3_l5_gs_kind_key.jsonl", kind_keys)
    lines.append("L-5 gs kind-first dictcomp key sites=%d" % len(kind_keys))
    fn_rows, cls_rows = zero_callers(scopes, ENTRY_REC, blocks)
    emit("mg9_zero_callers_fn.jsonl", fn_rows)
    emit("mg9_zero_callers_cls.jsonl", cls_rows)
    lines.append("L-1x zero_callers fn=%d (method=%d block=%d) cls=%d" % (len(fn_rows), sum(r["is_method"] for r in fn_rows), sum(r["is_block"] for r in fn_rows), len(cls_rows)))
    (OUT / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


main()
