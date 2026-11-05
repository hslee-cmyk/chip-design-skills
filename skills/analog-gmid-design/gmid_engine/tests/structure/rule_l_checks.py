"""규칙 L-1~L-5 판정(card 20261104-gc1-rule-l, graph-consumption 계획 N3.1·design §2~§4).

AST만 쓴다(엔진 import·실행 0, 표준 라이브러리만). `structure_checks.py`를 쓰지 않는다(GD §1).
풀지 못하면 위반이다(fail-closed): 권한표 `writes=`/`reads=`/`WriterTable(...)`을 상수로 못 풀면 `writer_table_unresolved`,
READS 열을 따라가지 못하면 `reads_unverifiable`, 동작점 사본 추적이 끊기면 `op_copy`.

공개: `Violation`, `DebtReport`, `check_rule_l`, `check_debt`, `fingerprint`.
키·code 표기는 interface card '위반 키와 code'. 줄 번호는 키에 쓰지 않는다(같은 함수의 여러 자리는 항목 하나).
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Mapping, NamedTuple

PKG = "gmid_engine"
ACCESSORS = {"value": 3, "field": 3, "column": 2, "column_fields": 2}
BUILTIN_WRAP = frozenset({"sorted", "list", "tuple", "dict", "set", "frozenset", "len", "str", "repr", "float", "int", "bool", "sum", "min",
                          "max", "any", "all", "enumerate", "zip", "map", "filter", "reversed", "round", "abs", "isinstance", "print", "range"})
VOCABULARY = ("배선 대기", "정본 읽기로 교체", "출력 전용 선언 대기", "삭제 승인 대기", "공동분석 대기", "정적 해석 형태로 바꾸기")
GATE, DRAIN, SOURCE = ("g", "gate", "MOS_GATE"), ("d", "drain", "MOS_DRAIN"), ("s", "source", "MOS_SOURCE")
KEY_WRAPPERS = ("sorted", "tuple", "frozenset", "list")
KEY_METHODS = ("setdefault", "get", "pop", "__contains__")
CONTAINER_ADD = ("append", "extend", "add", "update", "setdefault", "insert")
VALUE_VIEWS = ("items", "values", "keys", "get", "copy")


class Violation(NamedTuple):
    key: tuple
    code: str
    detail: str


class DebtReport(NamedTuple):
    missing: tuple
    stale: tuple
    outside_baseline: tuple
    bad_items: tuple


class Unresolved(Exception):
    """상수로 풀지 못한 식(권한표). 잡아서 위반으로 바꾼다."""


class _WT(NamedTuple):
    entries: tuple          # ((kind, field), writer) 정렬


class _Mod(NamedTuple):
    name: str


class Scope:
    """함수 하나(중첩 def 제외, lambda·컴프리헨션 포함) 또는 모듈 최상위(클래스 본문 포함)."""

    def __init__(self, sid, module, node, cls, parent):
        self.sid, self.module, self.node, self.cls, self.parent = sid, module, node, cls, parent
        self.nested = {}
        self.locals = set()
        self.local_names = set()
        self.body_nodes = []
        self.edges = set()
        self.sites = []
        self.site_map = {}
        self.precise = set()
        self.reads = []
        self.dynamic = []
        self.getattr_dynamic = []


class _Engine:
    """엔진 소스 트리 한 벌의 AST 색인. check_rule_l 한 번에 한 번 만든다(호출 안 지역)."""

    def __init__(self, root: Path):
        self.root = root
        self.modules, self.symbols, self.classes, self.method_index = {}, {}, {}, {}
        self.imports, self.constants, self.tree_of = {}, {}, {}
        self.scopes, self.scopes_by_mod = {}, {}
        self._load()
        self._build_scopes()
        self._collect_imports()
        for scope in self.scopes.values():
            scope.local_names = set() if scope.sid.endswith(":<module>") else self._locals_of(scope)
        self._analyse_edges()
        self._const_memo = {}

    # ---- 적재 ----
    def _modname(self, path):
        parts = list(path.relative_to(self.root).with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts)

    def _load(self):
        for path in sorted(self.root.rglob("*.py")):
            rel = path.relative_to(self.root)
            if rel.parts[0] == "tests" or "__pycache__" in rel.parts:
                continue
            name = self._modname(path)
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                for child in ast.iter_child_nodes(node):
                    child.parent = node
            self.tree_of[name] = tree
            self.modules[name] = rel.as_posix()

    def _resolve_relative(self, mod, node):
        is_pkg = self.modules[mod].endswith("__init__.py")
        base = mod.split(".") if mod else []
        if node.level:
            cut = node.level - 1 if is_pkg else node.level
            base = base[:len(base) - cut] if cut else base
            return ".".join(base + ([node.module] if node.module else []))
        if node.module and (node.module == PKG or node.module.startswith(PKG + ".")):
            return node.module[len(PKG) + 1:]
        return None

    def _build_scopes(self):
        engine = self

        def add_scope(node, module, cls, parent, qual):
            sid = module + ":" + qual
            scope = Scope(sid, module, node, cls, parent)
            engine.scopes[sid] = scope
            if parent is not None:
                parent.nested[node.name] = scope
            engine.symbols[sid] = scope
            return scope

        def visit(node, scope, module, cls, prefix):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    scope.body_nodes.append(dec)
                for default in node.args.defaults + [d for d in node.args.kw_defaults if d]:
                    scope.body_nodes.append(default)
                qual = prefix + node.name
                is_top = scope.node is engine.tree_of[module] or isinstance(scope.node, ast.ClassDef)
                child = add_scope(node, module, cls, None if is_top else scope, qual)
                for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
                    child.locals.add(arg.arg)
                if node.args.vararg:
                    child.locals.add(node.args.vararg.arg)
                if node.args.kwarg:
                    child.locals.add(node.args.kwarg.arg)
                for stmt in node.body:
                    visit(stmt, child, module, None, qual + ".")
                if cls:
                    engine.method_index.setdefault(node.name, set()).add(child.sid)
                return
            if isinstance(node, ast.ClassDef):
                qual = prefix + node.name
                engine.classes[module + ":" + qual] = node
                for dec in node.decorator_list + node.bases + [k.value for k in node.keywords]:
                    scope.body_nodes.append(dec)
                for stmt in node.body:
                    visit(stmt, scope, module, qual, qual + ".")
                return
            scope.body_nodes.append(node)

        for mod, tree in self.tree_of.items():
            top = Scope(mod + ":<module>", mod, tree, None, None)
            self.scopes[top.sid] = top
            self.scopes_by_mod[mod] = top
            for stmt in tree.body:
                visit(stmt, top, mod, None, "")

    def _collect_imports(self):
        for mod, tree in self.tree_of.items():
            table = self.imports.setdefault(mod, {})
            const = self.constants.setdefault(mod, {})
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    base = self._resolve_relative(mod, node)
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
                elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.value is not None:
                    const[stmt.target.id] = stmt.value

    def resolve_symbol(self, mod, name, seen=None):
        """('fn',sid)|('cls',cid)|('mod',m)|('const',(m,expr))|('ext',..)|None. 재수출을 따라간다(패키지 재수출이 하위 모듈보다 앞선다)."""
        seen = seen if seen is not None else set()
        if (mod, name) in seen or mod not in self.modules:
            return None
        seen.add((mod, name))
        sid = mod + ":" + name
        if sid in self.symbols:
            return ("fn", sid)
        if sid in self.classes:
            return ("cls", sid)
        if name in self.constants.get(mod, {}):
            return ("const", (mod, self.constants[mod][name]))
        entry = self.imports.get(mod, {}).get(name)
        if entry:
            where, base, attr = entry
            if where == "ext":
                return ("ext", base)
            if attr is None:
                return ("mod", base)
            if attr == "*":
                return None
            first = self.resolve_symbol(base, attr, seen)
            if first is not None:
                return first
            sub = (base + "." + attr) if base else attr
            return ("mod", sub) if sub in self.modules else None
        return None

    def class_methods(self, cid):
        prefix = cid + "."
        return [sid for sid in self.symbols if sid.startswith(prefix)]

    @staticmethod
    def _locals_of(scope):
        names = set(scope.locals)
        for root in scope.body_nodes:
            for node in ast.walk(root):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    names.add(node.id)
        return names

    @staticmethod
    def _enclosing_nested(scope, name):
        cur = scope
        while cur is not None:
            if name in cur.nested:
                return cur.nested[name]
            cur = cur.parent
        return None

    @staticmethod
    def _targets_of(res):
        return {res[1]} if res is not None and res[0] in ("fn", "cls") else set()

    def _analyse_edges(self):
        for scope in self.scopes.values():
            loc = scope.local_names
            for root in scope.body_nodes:
                for node in ast.walk(root):
                    targets, precise = set(), True
                    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                        nested = self._enclosing_nested(scope, node.id)
                        if nested is not None:
                            targets = {nested.sid}
                        elif node.id not in loc:
                            targets = self._targets_of(self.resolve_symbol(scope.module, node.id))
                    elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                        targets, precise = self._attr_targets(scope, node.value, node.attr, loc)
                    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr" and len(node.args) >= 2:
                        if isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
                            targets, precise = self._attr_targets(scope, node.args[0], node.args[1].value, loc)
                        else:
                            scope.getattr_dynamic.append((node.lineno, "getattr_nonconst"))
                    if targets:
                        scope.edges |= targets
                        scope.sites.append((targets, node))
                        scope.site_map[id(node)] = targets
                        if precise:
                            scope.precise.add(id(node))

    def _attr_targets(self, scope, recv, attr, loc):
        """(대상 집합, 정확 여부). 정확 = 모듈·클래스·self 로 풀린 것, 부정확 = 같은 이름 메서드 전부(넓게, 도달·호출자 센서용)."""
        if isinstance(recv, ast.Name) and recv.id not in loc:
            res = self.resolve_symbol(scope.module, recv.id)
            if res is not None:
                if res[0] == "ext":
                    return set(), False
                if res[0] == "mod":
                    return self._targets_of(self.resolve_symbol(res[1], attr)), True
                if res[0] == "cls":
                    sid = res[1] + "." + attr
                    if sid in self.symbols:
                        return {sid}, True
        if isinstance(recv, ast.Name) and recv.id == "self":
            qual = scope.sid.split(":", 1)[1].rsplit(".", 1)[0]
            sid = scope.module + ":" + qual + "." + attr
            if sid in self.symbols:
                return {sid}, True
        return set(self.method_index.get(attr, ())), False

    # ---- 상수 해석(읽기 인자) ----
    def resolve_const(self, scope, expr, depth=0):
        """문자열 상수로 풀면 그 값, 아니면 None."""
        if depth > 8:
            return None
        if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
            return expr.value
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
            a, b = self.resolve_const(scope, expr.left, depth + 1), self.resolve_const(scope, expr.right, depth + 1)
            return None if a is None or b is None else a + b
        if isinstance(expr, ast.Name):
            if expr.id in scope.local_names:
                return None
            res = self.resolve_symbol(scope.module, expr.id)
            if res and res[0] == "const":
                mod, value = res[1]
                return self.resolve_const(self.scopes_by_mod[mod], value, depth + 1)
        if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
            res = self.resolve_symbol(scope.module, expr.value.id)
            if res and res[0] == "mod":
                sub = self.resolve_symbol(res[1], expr.attr)
                if sub and sub[0] == "const":
                    return self.resolve_const(self.scopes_by_mod[sub[1][0]], sub[1][1], depth + 1)
        return None

    def module_tuple(self, scope, expr, depth=0):
        """모듈 수준 tuple 이름을 값(문자열·중첩 tuple)으로 펼친다. 못 풀면 None."""
        if depth > 8:
            return None
        if isinstance(expr, ast.Name) and expr.id not in scope.local_names:
            res = self.resolve_symbol(scope.module, expr.id)
            if res and res[0] == "const":
                mod, value = res[1]
                return self._tuple_value(self.scopes_by_mod[mod], value, depth + 1)
        if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
            res = self.resolve_symbol(scope.module, expr.value.id)
            if res and res[0] == "mod":
                sub = self.resolve_symbol(res[1], expr.attr)
                if sub and sub[0] == "const":
                    return self._tuple_value(self.scopes_by_mod[sub[1][0]], sub[1][1], depth + 1)
        return None

    def _tuple_value(self, scope, expr, depth):
        if isinstance(expr, (ast.Tuple, ast.List)):
            out = []
            for elt in expr.elts:
                val = self._tuple_value(scope, elt, depth + 1)
                if val is None:
                    return None
                out.append(val)
            return tuple(out)
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
            a, b = self._tuple_value(scope, expr.left, depth + 1), self._tuple_value(scope, expr.right, depth + 1)
            return None if a is None or b is None else a + b
        text = self.resolve_const(scope, expr, depth + 1)
        if text is not None:
            return text
        return self.module_tuple(scope, expr, depth + 1)

    @staticmethod
    def _bind(target, value, env):
        if isinstance(target, ast.Name):
            env.setdefault(target.id, []).append(value)
            return True
        if isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, tuple) and len(value) == len(target.elts):
            return all(_Engine._bind(t, v, env) for t, v in zip(target.elts, value))
        return False

    def loop_env(self, scope, call):
        """call 을 감싼 for·컴프리헨션의 루프 변수를 모듈 수준 tuple 로 펼친 환경 {이름: [값...]}."""
        env = {}
        node = call
        while hasattr(node, "parent"):
            node = node.parent
            gens = []
            if isinstance(node, ast.For):
                gens = [(node.target, node.iter)]
            elif isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
                gens = [(g.target, g.iter) for g in node.generators]
            for target, it in gens:
                val = self.module_tuple(scope, it)
                if val is None:
                    continue
                for item in val:
                    self._bind(target, item, env)
            if node is scope.node:
                break
        return env

    def arg_values(self, scope, expr, env):
        if isinstance(expr, ast.Name) and expr.id in env:
            vals = [v for v in env[expr.id] if isinstance(v, str)]
            return sorted(set(vals)) or None
        val = self.resolve_const(scope, expr)
        return [val] if val is not None else None

    # ---- 권한표(AST만) ----
    def _eval(self, mod, expr, env, depth=0):
        """권한표 식을 값(str·tuple·_WT·_Mod)으로 푼다. 못 풀면 Unresolved."""
        if depth > 24:
            raise Unresolved("깊이")
        if isinstance(expr, ast.Constant):
            return expr.value
        if isinstance(expr, (ast.Tuple, ast.List)):
            out = []
            for elt in expr.elts:
                if isinstance(elt, ast.Starred):
                    inner = self._eval(mod, elt.value, env, depth + 1)
                    if not isinstance(inner, tuple):
                        raise Unresolved("starred")
                    out.extend(inner)
                else:
                    out.append(self._eval(mod, elt, env, depth + 1))
            return tuple(out)
        if isinstance(expr, ast.Name):
            if expr.id in env:
                return env[expr.id]
            res = self.resolve_symbol(mod, expr.id)
            if res is None:
                raise Unresolved(expr.id)
            if res[0] == "const":
                m, e = res[1]
                memo = (m, id(e))
                if memo not in self._const_memo:
                    self._const_memo[memo] = self._eval(m, e, {}, depth + 1)
                return self._const_memo[memo]
            if res[0] == "mod":
                return _Mod(res[1])
            raise Unresolved(expr.id)
        if isinstance(expr, ast.Attribute):
            base = self._eval(mod, expr.value, env, depth + 1)
            if isinstance(base, _Mod):
                res = self.resolve_symbol(base.name, expr.attr)
                if res and res[0] == "const":
                    m, e = res[1]
                    memo = (m, id(e))
                    if memo not in self._const_memo:
                        self._const_memo[memo] = self._eval(m, e, {}, depth + 1)
                    return self._const_memo[memo]
                raise Unresolved(expr.attr)
            if isinstance(base, _WT) and expr.attr == "entries":
                return base.entries
            raise Unresolved(expr.attr)
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
            a, b = self._eval(mod, expr.left, env, depth + 1), self._eval(mod, expr.right, env, depth + 1)
            if isinstance(a, (tuple, str)) and type(a) is type(b):
                return a + b
            raise Unresolved("add")
        if isinstance(expr, (ast.GeneratorExp, ast.ListComp)):
            return tuple(self._comp(mod, expr, 0, env, depth + 1))
        if isinstance(expr, ast.Subscript) and isinstance(expr.slice, ast.Constant) and isinstance(expr.slice.value, int):
            base = self._eval(mod, expr.value, env, depth + 1)
            if isinstance(base, tuple):
                try:
                    return base[expr.slice.value]
                except IndexError as exc:
                    raise Unresolved("index") from exc
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and len(expr.args) == 1 and not expr.keywords:
            name = expr.func.id
            if name in ("tuple", "list"):
                inner = self._eval(mod, expr.args[0], env, depth + 1)
                if isinstance(inner, tuple):
                    return inner
                raise Unresolved(name)
            res = self.resolve_symbol(mod, name)
            if res and res[0] == "cls" and res[1].endswith(":WriterTable"):
                return self._writer_table(self._eval(mod, expr.args[0], env, depth + 1))
        raise Unresolved(type(expr).__name__)

    def _comp(self, mod, comp, index, env, depth):
        if index == len(comp.generators):
            yield self._eval(mod, comp.elt, env, depth + 1)
            return
        gen = comp.generators[index]
        if gen.ifs or gen.is_async:
            raise Unresolved("comprehension if")
        items = self._eval(mod, gen.iter, env, depth + 1)
        if not isinstance(items, tuple):
            raise Unresolved("iter")
        for item in items:
            inner = dict(env)
            if not self._unpack(gen.target, item, inner):
                raise Unresolved("unpack")
            yield from self._comp(mod, comp, index + 1, inner, depth + 1)

    def _unpack(self, target, value, env):
        if isinstance(target, ast.Name):
            env[target.id] = value
            return True
        if isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, tuple) and len(value) == len(target.elts):
            return all(self._unpack(t, v, env) for t, v in zip(target.elts, value))
        return False

    @staticmethod
    def _writer_table(entries):
        if not isinstance(entries, tuple):
            raise Unresolved("WriterTable 인자")
        index = {}
        for entry in entries:
            if not (isinstance(entry, tuple) and len(entry) == 3 and all(isinstance(x, str) for x in entry)):
                raise Unresolved("WriterTable 항목")
            index.setdefault((entry[0], entry[1]), entry[2])
        return _WT(tuple(sorted(index.items())))

    def pairs(self, scope, expr):
        """(kind, field) 쌍 tuple. 못 풀면 Unresolved."""
        value = self._eval(scope.module, expr, {})
        if not isinstance(value, tuple):
            raise Unresolved("쌍 목록")
        out = []
        for item in value:
            if not (isinstance(item, tuple) and len(item) == 2 and all(isinstance(x, str) for x in item)):
                raise Unresolved("쌍")
            out.append(item)
        return tuple(out)


# ------------------------------------------------------------------ 도우미

def _fn_spec(spec):
    """'패키지/파일.py:함수' -> (모듈 점 표기, 함수 한정 이름)."""
    path, _, qual = spec.partition(":")
    mod = path[:-3] if path.endswith(".py") else path
    parts = mod.split("/")
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts), qual


def _spec_sid(spec):
    mod, qual = _fn_spec(spec)
    return mod + ":" + qual


def _descendants(scope):
    out = [scope]
    for child in scope.nested.values():
        out.extend(_descendants(child))
    return out


def _fn_key(sid):
    return sid.replace(":", ".")


def _qual(sid):
    return sid.split(":", 1)[1]


def _is_block_dec(dec):
    if not isinstance(dec, ast.Call):
        return False
    fn = dec.func
    return (isinstance(fn, ast.Name) and fn.id == "compute_block") or (isinstance(fn, ast.Attribute) and fn.attr == "compute_block")


class _Blocks:
    """블록 함수 표와 권한표. unresolved = [(키, code, 설명)]."""

    def __init__(self, eng):
        self.eng = eng
        self.block_sid = {}          # 블록 이름 -> 함수 sid
        self.reads = {}              # 블록 이름 -> (kind, field) tuple 또는 None
        self.table = {}              # (kind, field) -> writer 이름
        self.unresolved = []
        for sid in sorted(eng.scopes):
            scope = eng.scopes[sid]
            if not isinstance(scope.node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in scope.node.decorator_list:
                if not _is_block_dec(dec):
                    continue
                name_expr = dec.args[0] if dec.args else next((k.value for k in dec.keywords if k.arg == "name"), None)
                name = eng.resolve_const(scope, name_expr) if name_expr is not None else None
                label = name or _qual(sid)
                outer = eng.scopes_by_mod[scope.module]
                kw = {k.arg: k.value for k in dec.keywords}
                writes_expr = kw.get("writes", dec.args[2] if len(dec.args) > 2 else None)
                reads_expr = kw.get("reads", dec.args[1] if len(dec.args) > 1 else None)
                self.block_sid[label] = sid
                try:
                    if writes_expr is None:
                        raise Unresolved("writes 없음")
                    for kind, field in eng.pairs(outer, writes_expr):
                        self.table.setdefault((kind, field), label)
                except Unresolved as exc:
                    self.unresolved.append((("L-1", label, eng.modules[scope.module]), "writer_table_unresolved", "writes= 상수 해석 실패: %s" % exc))
                try:
                    self.reads[label] = eng.pairs(outer, reads_expr) if reads_expr is not None else ()
                except Unresolved:
                    self.reads[label] = None
        for mod in sorted(eng.tree_of):
            for stmt in eng.tree_of[mod].body:
                value, name = None, None
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                    value, name = stmt.value, stmt.targets[0].id
                elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.value is not None:
                    value, name = stmt.value, stmt.target.id
                if not (isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "WriterTable"):
                    continue
                try:
                    table = eng._eval(mod, value, {})
                    if not isinstance(table, _WT):
                        raise Unresolved("WriterTable")
                    for (kind, field), writer in table.entries:
                        self.table.setdefault((kind, field), writer)
                except Unresolved as exc:
                    self.unresolved.append((("L-1", name, eng.modules[mod]), "writer_table_unresolved", "WriterTable 상수 해석 실패: %s" % exc))


def _analyse_reads(eng, kinds):
    """scope.reads = (kind, field, line, accessor, Call), scope.dynamic = (line, 원문)."""
    for scope in eng.scopes.values():
        for root in scope.body_nodes:
            for node in ast.walk(root):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                    continue
                attr = node.func.attr
                if attr not in ACCESSORS or len(node.args) != ACCESSORS[attr] or node.keywords:
                    continue
                if isinstance(node.func.value, ast.Name):
                    res = None if node.func.value.id in scope.local_names else eng.resolve_symbol(scope.module, node.func.value.id)
                    if res and res[0] == "ext":
                        continue
                env = eng.loop_env(scope, node)
                kind_vals = eng.arg_values(scope, node.args[0], env)
                field_vals = eng.arg_values(scope, node.args[-1], env)
                if kind_vals is not None and not set(kind_vals) <= kinds:
                    continue            # 이름이 같은 다른 객체의 메서드
                if kind_vals is None or field_vals is None:
                    scope.dynamic.append((node.lineno, ast.unparse(node)[:120]))
                    continue
                for kind in kind_vals:
                    for field in field_vals:
                        scope.reads.append((kind, field, node.lineno, attr, node))


def _import_closure(eng, start):
    seen, stack = set(), list(start)
    while stack:
        mod = stack.pop()
        if mod in seen or mod not in eng.modules:
            continue
        seen.add(mod)
        parts = mod.split(".")
        for i in range(len(parts)):
            parent = ".".join(parts[:i])
            if parent in eng.modules:
                stack.append(parent)
        for where, base, attr in eng.imports.get(mod, {}).values():
            if where == "eng":
                stack.append(base)
                if attr and ((base + "." + attr) if base else attr) in eng.modules:
                    stack.append((base + "." + attr) if base else attr)
    return seen


def _reachable(eng, entry_sids):
    modules = [sid.split(":")[0] for sid in entry_sids if sid in eng.scopes]
    closure = _import_closure(eng, modules)
    stack = [sid for sid in entry_sids if sid in eng.scopes] + [m + ":<module>" for m in closure if m + ":<module>" in eng.scopes]
    seen = set()
    while stack:
        sid = stack.pop()
        if sid in seen:
            continue
        seen.add(sid)
        if sid in eng.classes:
            for meth in eng.class_methods(sid):
                if meth.rsplit(".", 1)[-1].startswith("__"):
                    stack.append(meth)
            continue
        scope = eng.scopes.get(sid)
        if scope is not None:
            stack.extend(scope.edges)
    return seen


def _under(sid, bases):
    """sid 가 bases 의 함수 자신이거나 그 안 중첩 함수인가."""
    return any(sid == b or sid.startswith(b + ".") for b in bases)


# ------------------------------------------------------------------ L-1, L-1d, L-2

def _rule_fields(eng, blocks, reach, params, out):
    writer_scopes = {}
    for label, sid in blocks.block_sid.items():
        writer_scopes.setdefault(label, set()).update(d.sid for d in _descendants(eng.scopes[sid]))
    output_sids = {_spec_sid(s) for s in params.output_functions}
    for spec in params.output_functions:
        if _spec_sid(spec) not in eng.scopes:
            out.append(Violation(("L-2", spec), "output_function_unreachable", "출력 함수 목록의 함수가 엔진에 없다"))
    declared = {}
    for field, func, _why in params.output_only_fields:
        declared.setdefault(field, []).append(func)
    reads_by = {}
    for sid, scope in eng.scopes.items():
        for kind, field, _line, _how, _node in scope.reads:
            reads_by.setdefault((kind, field), []).append(sid)
    for (kind, field), writer in sorted(blocks.table.items()):
        name = kind + "." + field
        own = writer_scopes.get(writer, set())
        outside = [sid for sid in reads_by.get((kind, field), ()) if sid not in own and sid in reach]
        if not outside:
            out.append(Violation(("L-1", name), "no_reader", "writer 블록 밖 도달 읽기 0"))
        elif all(_under(sid, output_sids) for sid in outside) and name not in declared:
            out.append(Violation(("L-2", name), "output_only_undeclared", "읽기가 모두 출력 함수에 있고 출력 전용 목록에 없다"))
    for name, funcs in sorted(declared.items()):
        for func in funcs:
            if _spec_sid(func) not in reach:
                out.append(Violation(("L-2", name), "output_function_unreachable", "출력 전용 목록의 출력 함수가 진입점에서 도달하지 않는다: " + func))
                break


def _rule_dynamic(eng, params, out):
    allowed = set(params.dynamic_allowed_files)
    for sid in sorted(eng.scopes):
        scope = eng.scopes[sid]
        if scope.dynamic and eng.modules[scope.module] not in allowed and not sid.endswith(":<module>"):
            out.append(Violation(("L-1d", _fn_key(sid)), "field_arg_dynamic", "필드 인자가 상수로 풀리지 않는다: " + scope.dynamic[0][1]))
        elif scope.dynamic and eng.modules[scope.module] not in allowed:
            out.append(Violation(("L-1d", scope.module + ".<module>"), "field_arg_dynamic", "필드 인자가 상수로 풀리지 않는다: " + scope.dynamic[0][1]))


# ------------------------------------------------------------------ L-3

def _rule_l3(eng, blocks, out):
    for label, sid in sorted(blocks.block_sid.items()):
        reads = blocks.reads.get(label)
        scope = eng.scopes[sid]
        if reads is None:
            out.append(Violation(("L-3", label + ".<reads>"), "reads_unverifiable", "reads= 를 상수로 풀지 못했다"))
            continue
        posargs = scope.node.args.posonlyargs + scope.node.args.args
        param = posargs[0].arg if posargs else None
        found = set()
        tainted = {param}
        helpers, passes_on = [], []
        for sc in _descendants(scope):
            for kind, field, _l, _h, _n in sc.reads:
                found.add((kind, field))
            for root in sc.body_nodes:
                for node in ast.walk(root):
                    if isinstance(node, ast.Call) and any(isinstance(a, ast.Name) and a.id in tainted for a in list(node.args) + [k.value for k in node.keywords]):
                        targets = sc.site_map.get(id(node.func))
                        if not targets:
                            passes_on.append((sc.sid, ast.unparse(node.func)[:60]))
                            continue
                        for t in sorted(targets):
                            same = t.split(":")[0].split(".")[0] == scope.module.split(".")[0]
                            if not same:
                                passes_on.append((sc.sid, t))
                            elif t in eng.classes:
                                helpers.extend(eng.scopes[m] for m in eng.class_methods(t))
                            elif t in eng.scopes:
                                helpers.append(eng.scopes[t])
        for helper in helpers:
            hparams = {a.arg for a in helper.node.args.args}
            for sc in _descendants(helper):
                for root in sc.body_nodes:
                    for node in ast.walk(root):
                        if (isinstance(node, ast.Call) and any(isinstance(a, ast.Name) and a.id in hparams for a in node.args)
                                and not isinstance(node.func, ast.Attribute)
                                and not (isinstance(node.func, ast.Name) and node.func.id in BUILTIN_WRAP)):
                            passes_on.append((sc.sid, "helper_passes:" + ast.unparse(node.func)[:40]))
            for sc in _descendants(helper):
                for kind, field, _l, _h, _n in sc.reads:
                    found.add((kind, field))
                if sc.dynamic or sc.getattr_dynamic:
                    passes_on.append((sc.sid, "dynamic"))
        for sc in _descendants(scope):
            if sc.dynamic or sc.getattr_dynamic:
                passes_on.append((sc.sid, "dynamic"))
        for kind, field in reads:
            if (kind, field) in found:
                continue
            code = "reads_unverifiable" if passes_on else "reads_not_read"
            out.append(Violation(("L-3", "%s.%s.%s" % (label, kind, field)), code, "READS 열의 실제 읽기를 확인하지 못했다"))


# ------------------------------------------------------------------ L-4

def _is_frozen_dc(node):
    for dec in node.decorator_list:
        if isinstance(dec, ast.Call) and "dataclass" in ast.unparse(dec.func):
            for kw in dec.keywords:
                if kw.arg == "frozen" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    return True
    return False


def _rule_l4(eng, params, out):
    loads, strings = set(), set()
    for tree in eng.tree_of.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                if not (isinstance(node.value, ast.Name) and node.value.id == "self"):
                    loads.add(node.attr)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr" and len(node.args) >= 2:
                if isinstance(node.args[1], ast.Constant):
                    loads.add(node.args[1].value)
        for stmt in tree.body:
            if isinstance(stmt, ast.Assign):
                for node in ast.walk(stmt.value):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        strings.add(node.value)
    exempt = set()
    for item in tuple(params.output_only_slots) + tuple(params.fingerprint_only_slots):
        exempt.add(item[0] if isinstance(item, (tuple, list)) else item)
    for mod in sorted(eng.tree_of):
        tree = eng.tree_of[mod]
        public = [s for s in tree.body if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not s.name.startswith("_")]
        if not (public and all(isinstance(s, ast.ClassDef) for s in public)):
            continue
        for stmt in tree.body:
            if not (isinstance(stmt, ast.ClassDef) and _is_frozen_dc(stmt)):
                continue
            for item in stmt.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    slot = item.target.id
                    key = "%s.%s.%s" % (mod, stmt.name, slot)
                    if slot in loads or slot in strings or key in exempt:
                        continue
                    out.append(Violation(("L-4", key), "slot_no_reader", "칸을 self 밖에서 읽는 곳·getattr·등록 문자열이 없다"))


# ------------------------------------------------------------------ L-5

def _pin_token(expr):
    if isinstance(expr, ast.Call) and expr.args and not expr.keywords:
        return _pin_token(expr.args[0])         # canon(gate, point) 처럼 핀을 한 번 감싼 꼴도 같은 핀이다
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


def _is_key_position(node):
    """node(필요하면 sorted·tuple 래퍼 안쪽)가 묶음 키 자리에 있는가."""
    cur = node
    while isinstance(cur.parent, ast.Call) and isinstance(cur.parent.func, ast.Name) and cur.parent.func.id in KEY_WRAPPERS and cur.parent.args and cur.parent.args[0] is cur:
        cur = cur.parent
    par = cur.parent
    if isinstance(par, ast.Subscript) and par.slice is cur:
        return True
    if isinstance(par, ast.Compare) and len(par.ops) == 1 and isinstance(par.ops[0], (ast.In, ast.NotIn)) and par.left is cur:
        return True
    if isinstance(par, ast.Call) and isinstance(par.func, ast.Attribute) and par.func.attr in KEY_METHODS and par.args and par.args[0] is cur:
        return True
    if isinstance(par, ast.DictComp) and par.key is cur:
        return True
    if isinstance(par, ast.Lambda) and par.body is cur:
        gp = par.parent
        if isinstance(gp, ast.keyword):
            gp = gp.parent
        return isinstance(gp, ast.Call)
    return False


def _predicate_sites(scope):
    """scope 안의 diode·same_vgs 재계산 자리: ({'diode'}, {'same_vgs'})."""
    diode = same = False
    for root in scope.body_nodes:
        for node in ast.walk(root):
            if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
                if {_pin_token(node.left), _pin_token(node.comparators[0])} == {"g", "d"}:
                    diode = True
            elif isinstance(node, ast.Tuple) and isinstance(node.ctx, ast.Load) and len(node.elts) in (2, 3):
                toks = [_pin_token(e) for e in node.elts]
                if toks[-2:] == ["g", "s"] and _is_key_position(node):
                    same = True
            elif isinstance(node, ast.DictComp) and isinstance(node.key, ast.Tuple) and len(node.key.elts) == 3:
                if "kind" in ast.unparse(node.key.elts[0]):
                    same = True
    return diode, same


class _OpCopy:
    """동작점 사본 추적(N3.1-5). 출처 = 정본 필드 읽기('S'). 흐름은 변수·루프·튜플 풀기·float/int·함수 인자·반환·객체 생성자.
    산술은 끊는다. 함수마다 '매개변수 라벨'(P:이름)로 값이 어느 매개변수에서 왔는지를 따라가, 호출 맥락 없이 반환·영속 자리를
    풀지 않고 호출 자리에서 맞춘다. 영속 자리(.write, 블록 출력, 비 self 속성 대입)나 추적 불능 호출에 'S'가 닿는 함수가 사본 자리이고,
    칸 값을 그대로 담아 반환해 그 자리에 닿게 하는 함수도 사본 자리다. 반환·인자 전달만 하는 운반 함수는 아니다."""

    def __init__(self, eng, reach, source, exempt_sids, writer_file):
        self.eng, self.source = eng, source
        self.cands = [sid for sid in sorted(reach) if sid in eng.scopes and not sid.endswith(":<module>")
                      and eng.modules[eng.scopes[sid].module] != writer_file and not _under(sid, exempt_sids)]
        self.cset = set(self.cands)
        self.src_ids = {sid: {id(r[4]) for r in eng.scopes[sid].reads if (r[0], r[1]) == source} for sid in self.cands}
        self.params = {sid: self._params_of(eng.scopes[sid]) for sid in self.cands}
        self.T = {sid: {p: {"P:" + p} for p in self.params[sid]} for sid in self.cands}      # 이름 -> 라벨
        self.D = self.T                                                                      # 한 표: 칸 값·객체를 변형 없이 담은 값만 라벨을 갖는다
        self.ret, self.retd, self.sink = {}, {}, {}
        self.recv = {sid: set() for sid in self.cands}                                       # 'S'가 닿는 매개변수
        self.block = {sid: self._in_block(eng.scopes[sid]) for sid in self.cands}
        self.sink_local = {sid: set() for sid in self.cands}
        for sid in self.cands:
            self.ret[sid], self.retd[sid], self.sink[sid] = set(), set(), set()

    # ---- 구조 ----
    @staticmethod
    def _params_of(scope):
        node = scope.node
        names = [a.arg for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs]
        return [n for n in names if n not in ("self", "cls")]

    @staticmethod
    def _in_block(scope):
        cur = scope
        while cur is not None:
            if isinstance(cur.node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(_is_block_dec(d) for d in cur.node.decorator_list):
                return True
            cur = cur.parent
        return False

    @staticmethod
    def _is_block(scope):
        return isinstance(scope.node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(_is_block_dec(d) for d in scope.node.decorator_list)

    @staticmethod
    def _precise(scope, fn):
        return scope.site_map.get(id(fn), set()) if id(fn) in scope.precise else set()

    @staticmethod
    def _store_names(target):
        """대입·루프 대상에서 값이 담기는 이름: 이름 자신, 튜플 풀기의 각 이름, 첨자·속성이면 그 바탕 이름(첨자 안의 키 이름은 아니다)."""
        if isinstance(target, ast.Name):
            return {target.id}
        if isinstance(target, (ast.Tuple, ast.List)):
            names = set()
            for elt in target.elts:
                names |= _OpCopy._store_names(elt)
            return names
        if isinstance(target, ast.Starred):
            return _OpCopy._store_names(target.value)
        while isinstance(target, (ast.Attribute, ast.Subscript)):
            target = target.value
        return {target.id} if isinstance(target, ast.Name) else set()

    @staticmethod
    def _iter_bind(target, iter_expr, got):
        """for 대상 이름에 어떤 라벨이 담기는가. (키, 값) 쌍을 풀면 값 쪽만, .keys() 는 없음, 이름 하나로 도는 'S' 는 키로 본다."""
        if not got:
            return {}
        view = iter_expr.func.attr if isinstance(iter_expr, ast.Call) and isinstance(iter_expr.func, ast.Attribute) else None
        if view == "keys":
            return {}
        names = _OpCopy._store_names
        if isinstance(target, (ast.Tuple, ast.List)) and len(target.elts) == 2:
            return {n: set(got) for n in names(target.elts[1])}
        if isinstance(target, ast.Name) and view != "values":
            kept = {lab for lab in got if lab != "S"}
            return {target.id: kept} if kept else {}
        return {n: set(got) for n in names(target)}

    def _actuals(self, callee, call):
        """호출의 실인자를 callee 매개변수 이름에 맞춘다: [(이름, 식)]."""
        params = [a.arg for a in self.eng.scopes[callee].node.args.posonlyargs + self.eng.scopes[callee].node.args.args]
        if params and params[0] in ("self", "cls") and isinstance(call.func, ast.Attribute):
            params = params[1:]
        return list(zip(params, call.args)) + [(k.arg, k.value) for k in call.keywords if k.arg]

    def _s_tainted(self, sid, labels):
        return "S" in labels or any(lab[:2] == "R:" or (lab[:2] in ("P:", "X:", "Y:", "Z:") and lab[2:] in self.recv[sid]) for lab in labels)

    def _extracted(self, sid, labels):
        """칸을 꺼냈거나 객체에 담은 값('S' 또는 X:)이 닿는가. 매개변수를 그대로 돌려주는 운반(P:)은 아니다."""
        return "S" in labels or any(lab.startswith("X:") and lab[2:] in self.recv[sid] for lab in labels)

    @staticmethod
    def _carried(labels, callee):
        """피호출이 칸을 꺼내 돌려준 값: 호출한 쪽에서는 운반(Y:)이고, 출처 자체는 피호출이 만든 사본 후보(R:)다."""
        return {"R:" + callee if lab == "S" else ("Y:" + lab[2:] if lab[:2] in ("P:", "X:", "Z:") else lab) for lab in labels}

    @staticmethod
    def _as_extracted(labels):
        """매개변수에서 칸을 꺼낸 값(X:)."""
        return {"X:" + lab[2:] if lab[:2] == "P:" else lab for lab in labels}

    @staticmethod
    def _as_contained(labels):
        """매개변수를 객체에 담은 값(Z:) -- 추적은 하지만 이 함수가 칸을 꺼낸 것은 아니다."""
        return {"Z:" + lab[2:] if lab[:2] == "P:" else lab for lab in labels}

    # ---- 라벨 ----
    def labels(self, sid, expr, direct, extra=None):
        env = (self.D if direct else self.T)[sid]
        extra = extra or {}
        lab = self.labels
        if isinstance(expr, ast.Name):
            return extra.get(expr.id) or env.get(expr.id, set())
        if isinstance(expr, ast.Attribute):
            return self._as_extracted(lab(sid, expr.value, direct, extra))
        if isinstance(expr, (ast.Subscript, ast.Starred)):
            return lab(sid, expr.value, direct, extra)
        if isinstance(expr, (ast.Tuple, ast.List, ast.Set)):
            return set().union(*(lab(sid, e, direct, extra) for e in expr.elts)) if expr.elts else set()
        if isinstance(expr, ast.Dict):
            return set().union(*(lab(sid, v, direct, extra) for v in expr.values if v is not None)) if expr.values else set()
        if isinstance(expr, ast.IfExp):
            return lab(sid, expr.body, direct, extra) | lab(sid, expr.orelse, direct, extra)
        if isinstance(expr, ast.BoolOp):
            return set().union(*(lab(sid, v, direct, extra) for v in expr.values))
        if isinstance(expr, (ast.ListComp, ast.GeneratorExp, ast.SetComp, ast.DictComp)):
            more = dict(extra)
            for gen in expr.generators:
                got = lab(sid, gen.iter, direct, more)
                for n, labs_ in self._iter_bind(gen.target, gen.iter, got).items():
                    more[n] = labs_
            return lab(sid, expr.value if isinstance(expr, ast.DictComp) else expr.elt, direct, more)
        if isinstance(expr, ast.Call):
            return self._call_labels(sid, expr, direct, extra)
        return set()

    def _call_labels(self, sid, expr, direct, extra):
        eng, scope, lab = self.eng, self.eng.scopes[sid], self.labels
        if id(expr) in self.src_ids[sid]:
            return {"S"}
        fn = expr.func
        args = list(expr.args) + [k.value for k in expr.keywords]
        if isinstance(fn, ast.Name) and fn.id in ("float", "int", "str", "bool", "dict", "tuple", "list", "set", "frozenset", "sorted", "reversed", "getattr") and expr.args:
            return lab(sid, expr.args[0], direct, extra)
        targets = self._precise(scope, fn)
        if isinstance(fn, ast.Attribute) and fn.attr in VALUE_VIEWS and not any(tg in eng.scopes for tg in targets):
            return lab(sid, fn.value, direct, extra)
        if any(tg in eng.classes for tg in targets):
            return self._as_contained(set().union(*(lab(sid, a, direct, extra) for a in args))) if args else set()
        out = set()
        for tg in targets:
            if tg not in self.cset or self._is_block(eng.scopes[tg]):
                continue
            retl = self.ret[tg]
            out |= {lab_ for lab_ in retl if lab_[:2] == "R:"}
            if self._extracted(tg, retl):
                out.add("R:" + tg)
            for pname, aexpr in self._actuals(tg, expr):
                if "P:" + pname in retl:
                    out |= lab(sid, aexpr, False, extra)
                if any(k + pname in retl for k in ("X:", "Y:", "Z:")):
                    out |= self._carried(lab(sid, aexpr, False, extra), tg)
        return out

    # ---- 고정점 ----
    def _step(self, sid):
        eng = self.eng
        scope = eng.scopes[sid]
        grew = False
        T, D = self.T[sid], self.D[sid]

        def put(table, names, labs):
            nonlocal grew
            if not labs:
                return
            for n in names:
                cur = table.setdefault(n, set())
                if not labs <= cur:
                    cur |= labs
                    grew = True

        def sink(labs, local=True):
            nonlocal grew
            if labs and not labs <= self.sink[sid]:
                self.sink[sid] |= labs
                grew = True
            if local and labs and not labs <= self.sink_local[sid]:
                self.sink_local[sid] |= labs
                grew = True

        for root in scope.body_nodes:
            for node in ast.walk(root):
                if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and getattr(node, "value", None) is not None:
                    t, d = self.labels(sid, node.value, False), self.labels(sid, node.value, True)
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        names = self._store_names(target)
                        put(T, names, set(t))
                        put(D, names, set(d))
                        if isinstance(node, ast.Assign) and isinstance(target, ast.Attribute) and t:
                            base = target
                            while isinstance(base, (ast.Attribute, ast.Subscript)):
                                base = base.value
                            if not (isinstance(base, ast.Name) and base.id == "self"):
                                sink(set(t))
                elif isinstance(node, (ast.For, ast.comprehension)):
                    got = self.labels(sid, node.iter, False)
                    for n, labs_ in self._iter_bind(node.target, node.iter, got).items():
                        put(T, {n}, labs_)
                elif isinstance(node, ast.Return) and node.value is not None:
                    t, d = self.labels(sid, node.value, False), self.labels(sid, node.value, True)
                    if self._is_block(scope):
                        sink(set(t))
                    else:
                        if not t <= self.ret[sid]:
                            self.ret[sid] |= t
                            grew = True
                        if not d <= self.retd[sid]:
                            self.retd[sid] |= d
                            grew = True
                elif isinstance(node, ast.Call):
                    fn = node.func
                    args = list(node.args) + [k.value for k in node.keywords]
                    if isinstance(fn, ast.Attribute) and fn.attr in CONTAINER_ADD:
                        t = set().union(*(self.labels(sid, a, False) for a in args)) if args else set()
                        d = set().union(*(self.labels(sid, a, True) for a in args)) if args else set()
                        base = fn.value
                        while isinstance(base, (ast.Attribute, ast.Subscript)):
                            base = base.value
                        if isinstance(base, ast.Name):
                            put(T, {base.id}, t)
                            put(D, {base.id}, d)
                    if isinstance(fn, ast.Attribute) and fn.attr == "write":
                        sink(set().union(*(self.labels(sid, a, False) for a in args)) if args else set())
                    elif isinstance(fn, (ast.Subscript, ast.Call)) or (
                            isinstance(fn, ast.Name) and fn.id in scope.local_names and fn.id not in scope.locals
                            and eng._enclosing_nested(scope, fn.id) is None):
                        got = set().union(*(self.labels(sid, a, False) for a in args)) if args else set()
                        sink({lab_ for lab_ in got if lab_ == "S" or lab_[:2] == "R:"})
                    for callee in self._precise(scope, fn):
                        if callee not in self.cset or callee in eng.classes:
                            continue
                        for pname, aexpr in self._actuals(callee, node):
                            lab_a = self.labels(sid, aexpr, False)
                            if not lab_a:
                                continue
                            if self._is_block(eng.scopes[callee]):
                                continue                    # 블록 함수의 인자는 스냅샷·투영이지 칸 값이 아니다
                            if self._s_tainted(sid, lab_a) and pname not in self.recv[callee]:
                                self.recv[callee].add(pname)
                                grew = True
                            if any(k + pname in self.sink[callee] for k in ("P:", "X:", "Y:", "Z:")):
                                sink(set(lab_a), local=False)
        return grew

    def run(self):
        for _ in range(24):
            grew = False
            for sid in self.cands:
                grew = self._step(sid) or grew
            if not grew:
                break

    def copies(self):
        self.run()
        flagged = {sid for sid in self.cands if self._s_tainted(sid, self.sink_local[sid])}
        for sid in self.cands:
            for lab in self.sink[sid]:
                if lab[:2] == "R:" and lab[2:] in self.cset:
                    flagged.add(lab[2:])
        return flagged


def _rule_l5(eng, reach, params, out):
    output_sids = {_spec_sid(s) for s in params.output_functions}
    for concept, (canon, writer_file) in sorted(params.l5_concepts.items()):
        if concept not in ("diode", "same_vgs", "op_copy"):
            raise ValueError("규칙 L-5: 등록 개념의 판정기가 없다: " + concept)
        if writer_file not in eng.modules.values():
            out.append(Violation(("L-5", concept, writer_file, "<writer_file>"), "writer_file_missing", "등록 writer 파일이 엔진에 없다"))
            continue
        if concept == "op_copy":
            kind, _, field = canon.partition(".")
            op = _OpCopy(eng, reach, (kind, field), output_sids, writer_file)
            for sid in sorted(op.copies()):
                scope = eng.scopes[sid]
                out.append(Violation(("L-5", "op_copy", eng.modules[scope.module], _qual(sid)), "op_copy", "정본 %s 의 칸 값을 영속 자리에 그대로 담거나 추적이 끊긴다" % canon))
            continue
        for sid in sorted(eng.scopes):
            scope = eng.scopes[sid]
            if eng.modules[scope.module] == writer_file:
                continue
            diode, same = _predicate_sites(scope)
            if (concept == "diode" and diode) or (concept == "same_vgs" and same):
                out.append(Violation(("L-5", concept, eng.modules[scope.module], _qual(sid)), "predicate_recomputed", "정본 %s 를 다시 계산한다" % canon))


# ------------------------------------------------------------------ L-1x

def _rule_l1x(eng, entry_sids, out):
    callers = {}
    for sid, scope in eng.scopes.items():
        for targets, _site in scope.sites:
            for t in targets:
                if t != sid and not sid.startswith(t + "."):
                    callers.setdefault(t, set()).add(sid)
    for sid in sorted(eng.scopes):
        if sid.endswith(":<module>") or sid in entry_sids:
            continue
        leaf = sid.rsplit(".", 1)[-1] if "." in _qual(sid) else _qual(sid)
        if leaf.startswith("__") and leaf.endswith("__"):
            continue
        if not callers.get(sid):
            out.append(Violation(("L-1x", _fn_key(sid)), "no_caller", "진입점 밖이고 엔진 안 호출자 0"))
    for cid in sorted(eng.classes):
        if not callers.get(cid):
            out.append(Violation(("L-1x", _fn_key(cid)), "no_caller", "클래스를 부르는 곳이 엔진 안에 없다"))


# ------------------------------------------------------------------ 공개

def check_rule_l(engine_root: Path, params) -> tuple:
    """엔진 소스 트리의 규칙 L 위반(키로 정렬). 엔진 import·실행 0."""
    eng = _Engine(Path(engine_root))
    blocks = _Blocks(eng)
    kinds = {k for k, _f in blocks.table}
    _analyse_reads(eng, kinds)
    entry_sids = {_spec_sid(s) for s in params.entry_points}
    out = []
    for spec in params.entry_points:
        if _spec_sid(spec) not in eng.scopes:
            out.append(Violation(("L-1", "<entry>", spec), "entry_point_missing", "진입점 함수가 엔진에 없다"))
    for key, code, detail in blocks.unresolved:
        out.append(Violation(key, code, detail))
    reach = _reachable(eng, entry_sids)
    _rule_fields(eng, blocks, reach, params, out)
    _rule_dynamic(eng, params, out)
    _rule_l3(eng, blocks, out)
    _rule_l4(eng, params, out)
    _rule_l5(eng, reach, params, out)
    _rule_l1x(eng, entry_sids, out)
    first = {}
    for v in out:
        first.setdefault((v.key, v.code), v)
    return tuple(sorted(first.values(), key=lambda v: (v.key, v.code)))


def check_debt(violations, debt: Mapping, baseline: tuple) -> DebtReport:
    """(a) 현재 위반 ⊆ 목록 (b) 목록 항목은 지금도 위반 (c) 목록 키 ⊆ 기준선, card id 빈 칸 0, 처리 어휘 6개."""
    current = {}
    for v in violations:
        current.setdefault(v.key, v)
    keys = set(current)
    base = set(baseline)
    missing = tuple(current[k] for k in sorted(keys - set(debt)))
    stale = tuple(sorted(set(debt) - keys))
    outside = tuple(sorted(set(debt) - base))
    bad = tuple(sorted(k for k, item in debt.items() if item.how not in VOCABULARY or not str(item.card).strip()))
    return DebtReport(missing, stale, outside, bad)


def _normalized(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def fingerprint(params, checks_path: Path, tables_path: Path) -> str:
    """판정을 바꿀 수 있는 입력의 지문: 정렬 JSON(UTF-8, 고정 구분자)의 sha256 16진.
    대상 = 규칙 매개변수 전부(진입점·출력 함수·동적 접근 허용 파일·L-5 등록표·출력 전용/지문 전용 목록)
    + rule_l_checks.py·rule_l_tables.py 바이트(줄바꿈 정규화)."""
    payload = {
        "params": dict(params._asdict()),
        "checks": _normalized(Path(checks_path)),
        "tables": _normalized(Path(tables_path)),
    }
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=list)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
