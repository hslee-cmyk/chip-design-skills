"""규칙 L-1~L-5 판정(card 20261104-gc1-rule-l, graph-consumption 계획 N3.1·design §2~§4).

AST만 쓴다(엔진 import·실행 0, 표준 라이브러리만). `structure_checks.py`를 쓰지 않는다(GD §1).
풀지 못하면 위반이다(fail-closed): 권한표 `writes=`/`reads=`/`WriterTable(...)`을 상수로 못 풀면 `writer_table_unresolved`,
READS 열을 따라가지 못하면 `reads_unverifiable`, 동작점 사본 추적이 끊기면 `op_copy`.

공개: `Violation`, `DebtReport`, `check_rule_l`, `check_debt`, `fingerprint`.
키·code 표기는 interface card '위반 키와 code'. 줄 번호는 키에 쓰지 않는다(같은 함수의 여러 자리는 항목 하나).
"""
from __future__ import annotations

import ast
import builtins
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
VALUE_VIEWS = ("items", "values", "keys", "get", "copy", "pop", "popitem", "setdefault")      # 칸 값을 돌려주는 수신자 흐름(라벨만 따라간다, 면제 아님)
OP_COPY_ROUNDS = 24                  # 동작점 사본 고정점 상한. 다 돌고도 더 자라면 추적 실패(op_copy)로 낸다
# 동작점 사본의 예외 -- 값을 보관하지 않음이 언어 정의로 확정된 내장의 닫힌 목록 하나(N3.1-5, 지문 대상). 이름 허용 목록은 이것뿐이다.
#  * 내장 함수: 이름이 지역·엔진·import 어디에도 가려지지 않은 경우에 한한다(새 값·불리언·개수를 돌려주며 인자를 쥐지 않음).
#  * 내장 형 메서드: 수신자가 그 형으로 확정된 경우에 한한다(수신자 형을 못 정하면 예외 아님).
#  * 값을 보관하거나 문자열로 옮기는 내장(type·repr·format·ascii 등)은 보관하지 않음이 확정되지 않으니 이 목록에 없다(풀리지 않는 호출 = sink).
BUILTIN_PURE_FUNCS = frozenset({"abs", "all", "any", "bin", "callable", "chr", "divmod", "hasattr", "hash", "hex", "id",
                                "isinstance", "issubclass", "len", "oct", "ord", "pow", "range", "round", "sum"})
BUILTIN_FLOW_FUNCS = frozenset({"float", "int", "str", "bool", "dict", "tuple", "list", "set", "frozenset", "sorted", "reversed", "getattr",
                                "min", "max", "zip", "enumerate", "iter", "next", "filter", "map"})   # 전 인자(키워드 포함)의 라벨을 합쳐 돌려준다(라벨 흐름). 콜백 인자는 따라갈 수 없으면 sink
_STR_METHODS = frozenset({"capitalize", "casefold", "center", "count", "encode", "endswith", "expandtabs", "find", "format", "format_map", "index",
                          "isalnum", "isalpha", "isascii", "isdecimal", "isdigit", "isidentifier", "islower", "isnumeric", "isprintable",
                          "isspace", "istitle", "isupper", "join", "ljust", "lower", "lstrip", "partition", "removeprefix", "removesuffix",
                          "replace", "rfind", "rindex", "rjust", "rpartition", "rsplit", "rstrip", "split", "splitlines", "startswith", "strip",
                          "swapcase", "title", "translate", "upper", "zfill"})
BUILTIN_TYPE_METHODS = {
    "str": _STR_METHODS,
    "list": frozenset({"clear", "copy", "count", "index", "pop", "remove", "reverse", "sort"}),
    "dict": frozenset({"clear", "copy", "get", "items", "keys", "pop", "popitem", "values"}),
    "set": frozenset({"clear", "copy", "difference", "discard", "intersection", "isdisjoint", "issubset", "issuperset", "pop", "remove",
                      "symmetric_difference", "union"}),
    "tuple": frozenset({"count", "index"}),
}
_NONFLOW_METHODS = frozenset({"count", "endswith", "find", "index", "isalnum", "isalpha", "isascii", "isdecimal", "isdigit", "isidentifier",
                              "islower", "isnumeric", "isprintable", "isspace", "istitle", "isupper", "isdisjoint", "issubset", "issuperset",
                              "rfind", "rindex", "startswith"})       # 불리언·개수·위치만 돌려주는 내장 형 메서드: 라벨을 끊는다(나머지 내장 형 메서드는 수신자·인자 라벨을 합쳐 돌려준다)
BUILTIN_TYPE_ADD = {                 # 수신자(지역에서 새로 만든 내장 컨테이너) 자신에 값을 담는 메서드 -- 수신자 변수에 라벨이 옮겨 붙는다
    "list": frozenset({"append", "extend", "insert"}),
    "dict": frozenset({"setdefault", "update"}),
    "set": frozenset({"add", "update"}),
}
SRC_BASES = frozenset({"S", "SP", "SD"})        # 출처 라벨 꼴: S 값(들), SP (이름, 값) 쌍 열(column), SD 이름 -> 값 사전
_COLUMN_ACCESSORS = frozenset({"column", "column_fields"})
_ITER_WRAPS = frozenset({"list", "tuple", "sorted", "reversed", "iter", "set", "frozenset"})
_SAFE_DECORATORS = frozenset({"staticmethod", "classmethod", "property", "abstractmethod", "setter", "getter", "deleter"})
_DATACLASS_DECORATORS = frozenset({"dataclass"})
# 라벨 계산이 흐름을 구현한 식·문 꼴. 여기에 없는 꼴에 출처 라벨이 닿으면 추적 실패(sink)다.
_MODELED_EXPR = (ast.Constant, ast.Name, ast.Attribute, ast.Subscript, ast.Starred, ast.Tuple, ast.List, ast.Set, ast.Dict, ast.IfExp, ast.BoolOp,
                 ast.ListComp, ast.GeneratorExp, ast.SetComp, ast.DictComp, ast.Call, ast.Lambda, ast.BinOp, ast.UnaryOp, ast.Compare,
                 ast.Yield, ast.YieldFrom, ast.Slice)
_MODELED_STMT = (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.For, ast.Return, ast.Expr, ast.If, ast.While, ast.Break, ast.Continue, ast.Pass,
                 ast.Try, ast.Global, ast.Nonlocal, ast.Import, ast.ImportFrom, ast.Delete, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef,
                 ast.Assert)
_FRESH_TYPES = {ast.List: "list", ast.ListComp: "list", ast.Dict: "dict", ast.DictComp: "dict", ast.Set: "set", ast.SetComp: "set",
                ast.Tuple: "tuple", ast.JoinedStr: "str"}
_FRESH_CALLS = {"list": "list", "dict": "dict", "set": "set", "tuple": "tuple", "str": "str", "frozenset": "frozenset", "sorted": "list"}


class Violation(NamedTuple):
    key: tuple
    code: str
    detail: str
    paths: tuple = ()            # op_copy: 잡힌 칸 경로(튜플의 튜플). 판정용 정보이고 위반 키에는 들어가지 않는다
    sinks: tuple = ()            # op_copy: 잡힌 (칸 경로, sink 꼴) 쌍. 표 행 op_copy_cleared 가 가리는 단위


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
        grew = True
        while grew:                                  # 별칭(p = projection)도 투영이다
            grew = False
            for sc in _descendants(scope):
                for root in sc.body_nodes:
                    for node in ast.walk(root):
                        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Name) and node.value.id in tainted:
                            for target in node.targets:
                                if isinstance(target, ast.Name) and target.id not in tainted:
                                    tainted.add(target.id)
                                    grew = True
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
                    if slot in loads or slot in strings or any(key == e or key.endswith("." + e) for e in exempt):
                        continue
                    out.append(Violation(("L-4", key), "slot_no_reader", "칸을 self 밖에서 읽는 곳·getattr·등록 문자열이 없다"))


# ------------------------------------------------------------------ L-5

def _pin_token(expr, unwrap=False):
    if (unwrap and isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id not in BUILTIN_WRAP
            and expr.args and not expr.keywords):
        return _pin_token(expr.args[0])         # canon(gate, point) 처럼 사용자 함수로 핀을 감싼 묶음 키 성분(len(g) 같은 내장 호출은 아니다)
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
    while isinstance(cur.parent, ast.Call) and isinstance(cur.parent.func, ast.Name) and cur.parent.args and cur.parent.args[0] is cur and len(cur.parent.args) == 1:
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
                toks = [_pin_token(e, True) for e in node.elts]
                if toks[-2:] == ["g", "s"] and _is_key_position(node):
                    same = True
            elif isinstance(node, ast.DictComp) and isinstance(node.key, ast.Tuple) and len(node.key.elts) == 3:
                if "kind" in ast.unparse(node.key.elts[0]):
                    same = True
    return diode, same


def _split_lab(lab):
    """라벨 = [@칸|]* 기본라벨. (접두, 기본)."""
    pre, sep, base = lab.rpartition("|")
    return pre + sep, base


def _lab_map(labels, fn):
    """기본라벨마다 fn(기본) -> 새 기본(None이면 버림). 칸 접두는 그대로 둔다."""
    out = set()
    for lab in labels:
        pre, base = _split_lab(lab)
        new = fn(base)
        if new is not None:
            out.add(pre + new)
    return out


def _elems(labels):
    """컨테이너를 돌 때 나오는 원소의 라벨: 쌍 열(SP)의 원소는 쌍(값을 담음), 사전(SD)은 이름(키)이라 없음."""
    return _lab_map(labels, lambda b: None if b == "SD" else ("S" if b in SRC_BASES else b))


def _as_value(labels):
    """컨테이너가 아니라 값 하나로 본 것(첨자·get·표시식 원소): 출처 꼴은 모두 S."""
    return _lab_map(labels, lambda b: "S" if b in SRC_BASES else b)


def _as_dict(labels):
    """값을 담은 사전(키는 이름): 출처 꼴은 SD."""
    return _lab_map(labels, lambda b: "SD" if b in SRC_BASES else b)


def _container(labels):
    """list·sorted 등으로 원소를 모은 컨테이너: 사전은 키만 남아 없음, 쌍 열은 쌍 열."""
    return _lab_map(labels, lambda b: None if b == "SD" else b)


def _pair_split(labels):
    """두 칸으로 푸는 원소의 (앞, 뒤) 라벨: 쌍 열은 뒤만(앞은 이름), 사전은 없음, 나머지는 둘 다."""
    first, second = set(), set()
    for lab in labels:
        pre, base = _split_lab(lab)
        if base == "SP":
            second.add(pre + "S")
        elif base != "SD":
            first.add(lab)
            second.add(lab)
    return first, second


def _norm(text):
    return " ".join(text.split())


class _OpCopy:
    """동작점 사본 추적(N3.1-5). 출처 = 정본 필드 읽기. 출처 라벨 꼴: S(값), SP((이름, 값) 쌍 열), SD(이름 -> 값 사전).
    흐름은 변수·루프·튜플 풀기·내장 흐름 함수·함수 인자·반환·객체 생성자·클로저(바깥 함수 변수 조회). 끊는 것은 산술(이항·단항·비교)뿐이다.
    라벨 계산이 모르는 식·문 꼴에 출처 라벨이 닿으면 추적 실패로 sink를 낸다(기본값이 위반이다).
    함수마다 '매개변수 라벨'(P:이름)로 값이 어느 매개변수에서 왔는지를 따라가, 호출 맥락 없이 반환·영속 자리를 풀지 않고 호출 자리에서 맞춘다.
    영속 자리(.write, 블록 출력, 비 self 속성 대입, 새로 만들지 않은 컨테이너의 첨자·키, 전역, 풀리지 않는 호출, 모델 밖 구문)에 출처가 닿는 함수가
    사본 자리이고, 칸 값을 그대로 담아 반환해 그 자리에 닿게 하는 함수도 사본 자리다. 반환·인자 전달만 하는 운반 함수는 아니다.
    위반은 (칸 경로, sink 꼴) 쌍으로 낸다. sink 꼴 = 영속 자리 종류 + 대상 식 문자열(줄 번호 아님, 공백 정규화)."""

    def __init__(self, eng, reach, source, output_sids, exempt_sids):
        self.eng, self.source = eng, source
        self.output_sids = output_sids
        self.cands = [sid for sid in sorted(eng.scopes) if not sid.endswith(":<module>") and sid in reach          # 도달 조건(N3.1-5)
                      and not _under(sid, exempt_sids)]                                                           # 정본 쓰기 블록 자신만 대상 밖
        self.cset = set(self.cands)
        self.types = {}
        self.nonconverged = False
        self._txt = {}
        scopes = [eng.scopes[sid] for sid in self.cands]
        self.nodes = {sc.sid: [n for root in sc.body_nodes for n in ast.walk(root)] for sc in scopes}
        self.read_ids = {sc.sid: {id(r[4]) for r in sc.reads} for sc in scopes}                                  # 정본 읽기 호출(인자는 키 문자열)
        self.src_ids = {sc.sid: {id(r[4]): r[3] for r in sc.reads if (r[0], r[1]) == source} for sc in scopes}
        self.extra_src = {}
        for sc in scopes:
            self.extra_src[sc.sid] = self._scan_sources(sc)
        self.params = {sc.sid: self._params_of(sc) for sc in scopes}
        self.T = {sid: {p: {"P:" + p} for p in self.params[sid]} for sid in self.cands}      # 이름 -> 라벨 (한 표)
        self.ret, self.sink, self.sink_rec = {}, {}, {}
        self.recv = {sid: set() for sid in self.cands}                                       # 'S'가 닿는 매개변수
        self.block = {sid: self._in_block(eng.scopes[sid]) for sid in self.cands}
        self.globals_ = {sc.sid: {n for g in self.nodes[sc.sid] if isinstance(g, (ast.Global, ast.Nonlocal)) for n in g.names} for sc in scopes}
        for sid in self.cands:
            self.ret[sid], self.sink[sid], self.sink_rec[sid] = set(), set(), set()

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

    def _text(self, node):
        txt = self._txt.get(id(node))
        if txt is None:
            txt = self._txt[id(node)] = _norm(ast.unparse(node))
        return txt

    def _scan_sources(self, scope):
        """정본 읽기를 상수 인자 꼴(`value(kind, key, field)` 등)로 못 알아본 접근도 출처로 본다(fail-closed): 정본 필드 이름 문자열을 인자(키워드 포함)로 받는
        호출은 무엇을 부르든(접근자 키워드 호출·메서드 별칭·getattr·partial·kind 가 상수가 아닌 읽기) 그 필드를 읽는 것으로 본다."""
        eng, field = self.eng, self.source[1]
        extra = {}
        read_ids = {id(r[4]) for r in scope.reads}
        for root in scope.body_nodes:
            for node in ast.walk(root):
                if not isinstance(node, ast.Call) or id(node) in read_ids:
                    continue
                vals = [eng.resolve_const(scope, a) for a in node.args if not isinstance(a, ast.Starred)] + \
                       [eng.resolve_const(scope, k.value) for k in node.keywords]
                if field in vals:
                    fn = node.func
                    extra[id(node)] = "SP" if isinstance(fn, ast.Attribute) and fn.attr in _COLUMN_ACCESSORS else "S"
        return extra

    # ---- 내장 형 확정(예외 목록의 조건) ----
    def _shadowed(self, scope, name):
        """name 이 내장 이름이 아니게 가려졌는가(이 함수·바깥 함수의 지역 이름, 엔진 정의, import)."""
        cur = scope
        while cur is not None:
            if name in cur.local_names or name in cur.locals:
                return True
            cur = cur.parent
        return self.eng.resolve_symbol(scope.module, name) is not None or self.eng._enclosing_nested(scope, name) is not None

    def _expr_type(self, scope, expr):
        """식이 내장 형(str·list·dict·set·tuple·frozenset)의 새 값이면 그 형, 아니면 None."""
        if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
            return "str"
        kind = _FRESH_TYPES.get(type(expr))
        if kind:
            return kind
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id in _FRESH_CALLS and not self._shadowed(scope, expr.func.id):
            return _FRESH_CALLS[expr.func.id]
        return None

    def _name_types(self, sid):
        """이름 -> 내장 형. 한 함수 안에서 그 이름의 모든 묶임이 같은 형의 새 값 대입뿐일 때만 확정한다(매개변수·루프·with·전역 선언은 확정 아님)."""
        if sid in self.types:
            return self.types[sid]
        scope = self.eng.scopes[sid]
        seen, bad = {}, set(scope.locals)
        direct = set()
        for node in self.nodes[sid]:
            if isinstance(node, (ast.Global, ast.Nonlocal)):
                bad |= set(node.names)
            elif isinstance(node, ast.Assign):
                for tgt in node.targets:
                    for leaf, val, exact in self._unpack(tgt, node.value):
                        if isinstance(leaf, ast.Name) and exact:      # 풀기에서 왼쪽 이름과 오른쪽 식이 하나씩 짝이 맞는 이름만 형을 정한다(나머지는 확정 아님)
                            direct.add(id(leaf))
                            seen.setdefault(leaf.id, set()).add(self._expr_type(scope, val))
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
                direct.add(id(node.target))
                seen.setdefault(node.target.id, set()).add(self._expr_type(scope, node.value))
        for node in self.nodes[sid]:
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)) and id(node) not in direct:
                bad.add(node.id)
        out = {}
        for name, kinds in seen.items():
            if name not in bad and len(kinds) == 1 and None not in kinds:
                out[name] = next(iter(kinds))
        self.types[sid] = out
        return out

    def _btype(self, sid, expr):
        """수신자 식의 내장 형(확정된 것만)."""
        scope = self.eng.scopes[sid]
        if isinstance(expr, ast.Name):
            return self._name_types(sid).get(expr.id)
        return self._expr_type(scope, expr)

    def _local_container(self, sid, expr):
        """첨자 대상이 이 함수 안에서 새로 만든 list·dict·set 이름 하나(첨자만 겹침)인가 -- 호출보다 오래 살 수 없는 자리."""
        while isinstance(expr, ast.Subscript):
            expr = expr.value
        return isinstance(expr, ast.Name) and self._name_types(sid).get(expr.id) in ("list", "dict", "set")

    def _builtin(self, sid, fn, names):
        """호출 대상이 가려지지 않은 내장 이름이고 names 에 있는가."""
        return isinstance(fn, ast.Name) and fn.id in names and not self._shadowed(self.eng.scopes[sid], fn.id)

    def _resolved_call(self, sid, node):
        """호출이 풀리는가: 엔진 안 정확한 대상, 이름이 안 가려진 내장 함수, 내장 형으로 확정된 수신자의 그 형 메서드. 나머지는 추적 불능."""
        scope, fn = self.eng.scopes[sid], node.func
        if self._precise(scope, fn):
            return True
        if isinstance(fn, ast.Name):
            return (fn.id in BUILTIN_PURE_FUNCS or fn.id in BUILTIN_FLOW_FUNCS) and not self._shadowed(scope, fn.id)
        if isinstance(fn, ast.Attribute):
            kind = self._btype(sid, fn.value)
            return kind is not None and (fn.attr in BUILTIN_TYPE_METHODS.get(kind, ()) or fn.attr in BUILTIN_TYPE_ADD.get(kind, ()))
        return False

    @staticmethod
    def _is_block(scope):
        return isinstance(scope.node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(_is_block_dec(d) for d in scope.node.decorator_list)

    @staticmethod
    def _precise(scope, fn):
        return scope.site_map.get(id(fn), set()) if id(fn) in scope.precise else set()

    def _is_output(self, sid):
        return _under(sid, self.output_sids)

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
    def _unpack(target, value):
        """대입 대상을 오른쪽 식과 짝짓는다: [(잎 대상, 그 잎에 담기는 식, 짝이 맞는가)]. 왼쪽 튜플·리스트와 오른쪽 튜플·리스트의 칸 수가 같고
        어느 쪽에도 `*`가 없으면 칸마다 재귀해 한 칸씩 짝짓는다(짝이 맞음). 그 밖의 풀기(오른쪽이 이름·호출·다른 길이·`*` 포함)는 잎 모두에
        그 층의 오른쪽 식 전체를 준다(짝이 안 맞음 -- 라벨은 합쳐 주고 형은 확정하지 않는다)."""
        if isinstance(target, (ast.Tuple, ast.List)):
            if (isinstance(value, (ast.Tuple, ast.List)) and len(target.elts) == len(value.elts)
                    and not any(isinstance(x, ast.Starred) for x in list(target.elts) + list(value.elts))):
                return [item for t, v in zip(target.elts, value.elts) for item in _OpCopy._unpack(t, v)]
            return [(leaf, value, False) for leaf in _OpCopy._leaf_targets(target)]
        return [(target, value, True)]

    @staticmethod
    def _top_exprs(node):
        """node 바로 아래(문·식을 넘지 않고 withitem·match_case 같은 껍데기는 지나) 식들. 저장 자리 이름은 뺀다."""
        out, stack = [], list(ast.iter_child_nodes(node))
        while stack:
            child = stack.pop()
            if isinstance(child, ast.expr):
                if not (isinstance(child, (ast.Name, ast.Attribute, ast.Subscript, ast.Tuple, ast.List, ast.Starred))
                        and isinstance(getattr(child, "ctx", None), ast.Store)):
                    out.append(child)
            elif not isinstance(child, ast.stmt):
                stack.extend(ast.iter_child_nodes(child))
        return out

    def _bind_iter(self, sid, target, iter_expr, extra):
        """for·컴프리헨션 대상 이름에 담기는 라벨 {이름: 라벨}. 쌍 열을 두 칸으로 풀면 뒤만, 사전을 돌면 키(없음), zip·enumerate 는 칸별로,
        그 밖의 두 칸 풀기와 이름 하나는 원소 라벨 모두(왼쪽도 값일 수 있다)."""
        scope = self.eng.scopes[sid]
        got = self.labels(sid, iter_expr, extra)
        out = {}

        def add(names, labs):
            if labs:
                for n in names:
                    out.setdefault(n, set()).update(labs)

        leaves = list(target.elts) if isinstance(target, (ast.Tuple, ast.List)) else None
        core = iter_expr
        while (isinstance(core, ast.Call) and isinstance(core.func, ast.Name) and core.func.id in _ITER_WRAPS and core.args
               and not self._shadowed(scope, core.func.id)):
            core = core.args[0]
        plain = leaves is not None and not any(isinstance(x, ast.Starred) for x in leaves)
        if plain and isinstance(core, ast.Call) and self._builtin(sid, core.func, ("zip", "enumerate")):
            args = list(core.args)
            if core.func.id == "zip" and len(args) == len(leaves) and not any(isinstance(a, ast.Starred) for a in args):
                for leaf, a in zip(leaves, args):
                    add(self._store_names(leaf), _elems(self.labels(sid, a, extra)))
                return out
            if core.func.id == "enumerate" and len(leaves) == 2 and args and not isinstance(args[0], ast.Starred):
                add(self._store_names(leaves[1]), _elems(self.labels(sid, args[0], extra)))
                return out
        if leaves is None:
            add(self._store_names(target), _elems(got))
        elif plain and len(leaves) == 2:
            first, second = _pair_split(got)
            add(self._store_names(leaves[0]), first)
            add(self._store_names(leaves[1]), second)
        else:
            first, second = _pair_split(got)
            add(self._store_names(target), first | second)
        return out

    def _actuals(self, callee, call, ctor=False, mod=None):
        """호출의 실인자를 callee 매개변수 이름에 맞춘다: ([(이름, 식)], [맞출 수 없는 실인자 식]). 위치 초과·모르는 키워드·`*`·`**` 실인자는 맞출 수 없다."""
        a = self.eng.scopes[callee].node.args
        pos = [x.arg for x in a.posonlyargs + a.args]
        kwonly = {x.arg for x in a.kwonlyargs}
        if pos and pos[0] in ("self", "cls") and (ctor or self._binds_first(callee, call, mod)):
            pos = pos[1:]
        mapped, unmapped, starred = [], [], False
        for i, arg in enumerate(call.args):
            if isinstance(arg, ast.Starred):
                unmapped.append(arg.value)
                starred = True
            elif starred or i >= len(pos):
                unmapped.append(arg)
            else:
                mapped.append((pos[i], arg))
        for kw in call.keywords:
            if kw.arg is not None and (kw.arg in pos or kw.arg in kwonly):
                mapped.append((kw.arg, kw.value))
            else:
                unmapped.append(kw.value)
        return mapped, unmapped

    def _binds_first(self, callee, call, mod=None):
        """속성 호출이 callee 의 첫 매개변수(self·cls)를 묶는가: 클래스 이름으로 부른 메서드는 classmethod 만, 그 밖은 staticmethod 가 아니면 묶는다."""
        fn = call.func
        if not isinstance(fn, ast.Attribute):
            return False
        decs = {self._dec_name(d) for d in self.eng.scopes[callee].node.decorator_list}
        if "staticmethod" in decs:
            return False
        res = self.eng.resolve_symbol(mod or self.eng.scopes[callee].module, fn.value.id) if isinstance(fn.value, ast.Name) else None
        return "classmethod" in decs if res is not None and res[0] == "cls" else True

    @staticmethod
    def _dec_name(dec):
        node = dec.func if isinstance(dec, ast.Call) else dec
        return node.attr if isinstance(node, ast.Attribute) else node.id if isinstance(node, ast.Name) else ast.dump(node)

    def _plain_function(self, scope):
        """장식이 언어 정의로 인자를 보관하지 않는 것(staticmethod·classmethod·property·abstractmethod·setter 류)뿐인 함수인가."""
        return all(self._dec_name(d) in _SAFE_DECORATORS for d in scope.node.decorator_list)

    def _class_init(self, cid, depth=0):
        """(__init__ 함수 sid 또는 None, 불투명 여부). 불투명 = __post_init__·__new__ 가 있거나, dataclass 아닌 장식·메타클래스·풀리지 않는
        바탕 클래스가 있어 생성이 인자를 어디에 두는지 정적으로 풀리지 않는 클래스."""
        node = self.eng.classes.get(cid)
        if node is None or depth > 6:
            return None, True
        mod = cid.split(":")[0]
        if cid + ".__post_init__" in self.eng.scopes or cid + ".__new__" in self.eng.scopes:
            return None, True
        if node.keywords or any(self._dec_name(d) not in _DATACLASS_DECORATORS for d in node.decorator_list):
            return None, True
        if cid + ".__init__" in self.eng.scopes:
            return cid + ".__init__", False
        init, opaque = None, False
        for base in node.bases:
            res = self.eng.resolve_symbol(mod, base.id) if isinstance(base, ast.Name) else None
            if res is not None and res[0] == "cls":
                sub, op = self._class_init(res[1], depth + 1)
                init, opaque = init or sub, opaque or op
            elif not (isinstance(base, ast.Name) and hasattr(builtins, base.id) and res is None):
                opaque = True
        return init, opaque

    @staticmethod
    def _attr_labels(labels, attr):
        """속성 읽기: 칸 접두가 있으면 그 칸만 풀리고(다른 칸은 오염 아님), 접두가 없으면 객체 전체를 꺼낸 것(P: -> X:)이다."""
        out = set()
        for lab in labels:
            if lab.startswith("@"):
                head, _, rest = lab.partition("|")
                if head[1:] in (attr, "?"):
                    out |= _lab_map({rest}, lambda b: "X:" + b[2:] if b[:2] == "P:" else b)
            else:
                out |= _lab_map({lab}, lambda b: "X:" + b[2:] if b[:2] == "P:" else b)
        return out

    @staticmethod
    def _cap(lab):
        """칸 접두는 두 겹까지만 구분한다(고정점이 끝나도록). 더 깊으면 '어느 칸이든'(@?)으로 합친다."""
        if lab.count("@") <= 2:
            return lab
        return "@?|" + lab.rpartition("|")[2]

    def _s_tainted(self, sid, labels):
        scope = self.eng.scopes[sid]
        for lab in labels:
            b = _split_lab(lab)[1]
            if b in SRC_BASES or b[:2] == "R:":
                return True
            if b[:2] in ("P:", "X:", "Y:", "Z:"):
                cur = scope
                while cur is not None:                      # 바깥 함수의 매개변수에서 온 값도 같다(클로저)
                    if cur.sid in self.recv and b[2:] in self.recv[cur.sid]:
                        return True
                    cur = cur.parent
        return False

    def _extracted(self, sid, labels):
        """칸을 꺼냈거나 객체에 담은 값(출처 꼴 또는 X:)이 닿는가. 매개변수를 그대로 돌려주는 운반(P:)은 아니다."""
        for lab in labels:
            b = _split_lab(lab)[1]
            if b in SRC_BASES or (b.startswith("X:") and b[2:] in self.recv[sid]):
                return True
        return False

    @staticmethod
    def _carried(labels, callee):
        """피호출이 칸을 꺼내 돌려준 값: 호출한 쪽에서는 운반(Y:)이고, 출처 자체는 피호출이 만든 사본 후보(R:)다."""
        return _lab_map(labels, lambda b: "R:" + callee if b in SRC_BASES else ("Y:" + b[2:] if b[:2] in ("P:", "X:", "Z:") else b))

    def _init_attrs(self, init, param):
        """__init__ 안에서 param 이 담기는 인스턴스 속성 이름들. param 을 다른 데 쓰면(속성 대입 밖) '?'(어느 속성이든)을 더한다."""
        attrs, covered = set(), set()
        for root in init.body_nodes:
            for node in ast.walk(root):
                if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) or getattr(node, "value", None) is None:
                    continue
                names = {n for n in ast.walk(node.value) if isinstance(n, ast.Name) and n.id == param}
                if not names:
                    continue
                for tgt in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                    cur = tgt
                    while isinstance(cur, (ast.Attribute, ast.Subscript)):
                        if isinstance(cur, ast.Attribute) and isinstance(cur.value, ast.Name) and cur.value.id == "self":
                            attrs.add(cur.attr)
                            covered |= {id(n) for n in names}
                            break
                        cur = cur.value
        for root in init.body_nodes:
            for node in ast.walk(root):
                if isinstance(node, ast.Name) and node.id == param and isinstance(node.ctx, ast.Load) and id(node) not in covered:
                    attrs.add("?")
        return sorted(attrs)

    def _ctor_info(self, cid, depth=0):
        """(위치 매개변수 이름들, {매개변수: [속성...]}) 또는 None(풀지 못함 -- 인자는 '어느 속성이든'으로 본다).
        __init__ 이 있으면 매개변수 -> 대입되는 속성, 없으면 칸 선언(상속 칸이 앞)이고 칸 이름 = 속성 이름이다."""
        if depth > 6:
            return None
        init = self.eng.scopes.get(cid + ".__init__")
        if init is not None:
            a = init.node.args
            pos = [x.arg for x in a.posonlyargs + a.args][1:]
            kwonly = [x.arg for x in a.kwonlyargs]
            return pos, {n: self._init_attrs(init, n) for n in pos + kwonly}
        node = self.eng.classes.get(cid)
        if node is None:
            return None
        fields, amap = [], {}
        for base in node.bases:
            res = self.eng.resolve_symbol(cid.split(":")[0], base.id) if isinstance(base, ast.Name) else None
            if res is None or res[0] != "cls":
                return None
            info = self._ctor_info(res[1], depth + 1)
            if info is None:
                return None
            fields += info[0]
            amap.update(info[1])
        own = [i.target.id for i in node.body if isinstance(i, ast.AnnAssign) and isinstance(i.target, ast.Name)]
        for name in own:
            amap[name] = [name]
        return fields + own, amap

    def _ctor_labels(self, sid, expr, cid, extra):
        info = self._ctor_info(cid)
        out = set()
        contain = lambda b: "Z:" + b[2:] if b[:2] == "P:" else ("S" if b in SRC_BASES else b)       # noqa: E731
        for i, a in enumerate(expr.args):
            wild = info is None or isinstance(a, ast.Starred) or i >= len(info[0])
            heads = ["?"] if wild else info[1].get(info[0][i], [])
            labs = _lab_map(self.labels(sid, a, extra), contain)
            out |= {self._cap("@" + f + "|" + lab) for f in heads for lab in labs}
        for k in expr.keywords:
            heads = ["?"] if (info is None or k.arg is None or k.arg not in info[1]) else info[1][k.arg]
            labs = _lab_map(self.labels(sid, k.value, extra), contain)
            out |= {self._cap("@" + f + "|" + lab) for f in heads for lab in labs}
        return out

    # ---- 라벨 ----
    def _lookup(self, sid, name):
        """이름의 라벨: 이 함수 표, 이 함수의 지역이 아니면 바깥 함수 표(클로저)."""
        scope = self.eng.scopes[sid]
        while scope is not None:
            env = self.T.get(scope.sid)
            if env is not None and name in env:
                return env[name]
            if name in scope.local_names or name in scope.locals:
                return set()
            scope = scope.parent
        return set()

    def labels(self, sid, expr, extra=None):
        """식이 담을 수 있는 출처 라벨. 전파를 끊는 것은 산술(BinOp·UnaryOp·Compare)뿐이고, 구현하지 않은 꼴은 자식 식의 라벨을 합쳐 낸다
        (그 자리의 sink 는 `_step` 이 낸다) -- 기본값이 빈 집합이 아니다."""
        extra = extra or {}
        lab = self.labels
        if isinstance(expr, (ast.Constant, ast.BinOp, ast.UnaryOp, ast.Compare, ast.Slice)):
            return set()
        if isinstance(expr, ast.Name):
            return extra.get(expr.id) or self._lookup(sid, expr.id)
        if isinstance(expr, ast.Attribute):
            return self._attr_labels(lab(sid, expr.value, extra), expr.attr)
        if isinstance(expr, ast.Subscript):
            base = lab(sid, expr.value, extra)
            return set(base) if isinstance(expr.slice, ast.Slice) else _as_value(base)
        if isinstance(expr, ast.Starred):
            return _elems(lab(sid, expr.value, extra))
        if isinstance(expr, (ast.Tuple, ast.List, ast.Set)):
            return _as_value(set().union(*(lab(sid, e, extra) for e in expr.elts))) if expr.elts else set()
        if isinstance(expr, ast.Dict):
            out = set()
            for k, v in zip(expr.keys, expr.values):
                if k is None:
                    out |= lab(sid, v, extra)
                else:
                    out |= _as_value(lab(sid, k, extra)) | _as_dict(lab(sid, v, extra))
            return out
        if isinstance(expr, ast.IfExp):
            return lab(sid, expr.body, extra) | lab(sid, expr.orelse, extra)
        if isinstance(expr, ast.BoolOp):
            return set().union(*(lab(sid, v, extra) for v in expr.values))
        if isinstance(expr, (ast.ListComp, ast.GeneratorExp, ast.SetComp, ast.DictComp)):
            more = dict(extra)
            for gen in expr.generators:
                for n, labs_ in self._bind_iter(sid, gen.target, gen.iter, more).items():
                    more[n] = labs_
            if isinstance(expr, ast.DictComp):
                return _as_value(lab(sid, expr.key, more)) | _as_dict(lab(sid, expr.value, more))
            return _as_value(lab(sid, expr.elt, more))
        if isinstance(expr, ast.Call):
            return self._call_labels(sid, expr, extra)
        if isinstance(expr, ast.Lambda):
            return lab(sid, expr.body, extra)
        if isinstance(expr, ast.NamedExpr):
            return lab(sid, expr.value, extra)
        if isinstance(expr, (ast.Yield, ast.YieldFrom)):
            return lab(sid, expr.value, extra) if expr.value is not None else set()
        out = set()                                   # 모델 밖 꼴(f-string·await 등): 자식 식의 라벨을 합친다
        for child in self._top_exprs(expr):
            out |= lab(sid, child, extra)
        return out

    def _view_labels(self, sid, expr, recv, attr, extra):
        """수신자가 칸 값을 돌려주는 메서드(items·values·keys·get·copy·pop·popitem·setdefault)의 라벨."""
        if attr == "keys":
            return set()
        if attr == "copy":
            return set(recv)
        if attr == "items":
            return _lab_map(recv, lambda b: "SP" if b in SRC_BASES else b)
        out = _as_value(recv)                         # values·get·pop·popitem·setdefault
        if attr != "values":
            for a in list(expr.args[1:]) + [k.value for k in expr.keywords]:
                out |= self.labels(sid, a, extra)
        return out

    def _flow_labels(self, sid, expr, extra):
        """닫힌 목록 BUILTIN_FLOW_FUNCS 호출의 라벨: 전 인자(키워드 포함)의 라벨을 합쳐 호출 의미대로 넘긴다."""
        name = expr.func.id
        lab = self.labels
        args = [a.value if isinstance(a, ast.Starred) else a for a in expr.args]
        pos = [lab(sid, a, extra) for a in expr.args]
        kws = [(k.arg, lab(sid, k.value, extra)) for k in expr.keywords]
        kwall = set().union(*(v for _a, v in kws)) if kws else set()
        if name in ("float", "int", "bool", "str"):
            return _as_value(set().union(*pos, kwall) if pos or kws else set())
        if name == "dict":
            out = set()
            for p in pos:
                out |= _as_dict(p)
            return out | _as_dict(kwall)
        if name in _ITER_WRAPS:
            return _container(pos[0]) if pos else set()
        if name == "getattr":
            if len(args) >= 2 and isinstance(args[1], ast.Constant) and isinstance(args[1].value, str):
                base = self._attr_labels(pos[0], args[1].value)
            else:
                base = set(pos[0]) if pos else set()
            return base | (pos[2] if len(pos) > 2 else set()) | kwall
        if name in ("min", "max"):
            cb = {a for a, _v in kws if a == "key"}
            rest = set().union(*(v for a, v in kws if a not in cb)) if kws else set()
            if len(pos) == 1:
                return _elems(pos[0]) | rest
            return _as_value(set().union(*pos)) | rest if pos else rest
        if name == "next":
            return (_elems(pos[0]) if pos else set()) | (set().union(*pos[1:]) if len(pos) > 1 else set())
        if name == "zip":
            return _as_value(set().union(*(_elems(p) for p in pos))) if pos else set()
        if name == "enumerate":
            return _as_value(_elems(pos[0])) if pos else set()
        if name == "filter":
            return _container(pos[1]) if len(pos) > 1 else set()
        if name == "map":
            cb = args[0] if args else None
            if isinstance(cb, ast.Lambda):
                return lab(sid, cb.body, extra)
            if self._builtin(sid, cb, BUILTIN_PURE_FUNCS):
                return set()
            return _as_value(set().union(*(_elems(p) for p in pos[1:]))) if len(pos) > 1 else set()
        return set()

    def _call_labels(self, sid, expr, extra):
        eng, scope, lab = self.eng, self.eng.scopes[sid], self.labels
        if id(expr) in self.src_ids[sid]:
            return {"SP"} if self.src_ids[sid][id(expr)] in _COLUMN_ACCESSORS else {"S"}
        if id(expr) in self.extra_src[sid]:
            return {self.extra_src[sid][id(expr)]}
        fn = expr.func
        if self._builtin(sid, fn, BUILTIN_FLOW_FUNCS):
            return self._flow_labels(sid, expr, extra)
        if self._builtin(sid, fn, BUILTIN_PURE_FUNCS):
            if fn.id == "sum" and (len(expr.args) > 1 or expr.keywords):      # sum(열, 시작값): 컨테이너를 이어 붙이는 꼴은 값을 보관한다
                return _as_value(set().union(*(lab(sid, a, extra) for a in list(expr.args) + [k.value for k in expr.keywords])))
            return set()
        targets = self._precise(scope, fn)
        clss = [tg for tg in targets if tg in eng.classes]
        if clss:
            return self._ctor_labels(sid, expr, clss[0], extra) if (expr.args or expr.keywords) else set()
        out = set()
        if isinstance(fn, ast.Attribute) and not any(tg in eng.scopes for tg in targets):
            recv = lab(sid, fn.value, extra)
            if fn.attr in VALUE_VIEWS:
                return self._view_labels(sid, expr, recv, fn.attr, extra)
            kind = self._btype(sid, fn.value)
            if kind is not None and (fn.attr in BUILTIN_TYPE_METHODS.get(kind, ()) or fn.attr in BUILTIN_TYPE_ADD.get(kind, ())):
                if fn.attr in _NONFLOW_METHODS:
                    return set()
                return recv | set().union(*(lab(sid, a, extra) for a in list(expr.args) + [k.value for k in expr.keywords]))
        elif isinstance(fn, (ast.Name, ast.Lambda)) and not targets:
            out |= lab(sid, fn, extra)                # 지역 변수·람다가 담은 호출 대상: 그 안의 값이 결과로 나올 수 있다
        for tg in targets:
            if tg not in self.cset or self._is_block(eng.scopes[tg]) or self._is_output(tg):         # 출력 함수의 반환은 보고 객체(iii)라 사본을 옮기지 않는다
                continue
            retl = self.ret[tg]
            out |= {lab_ for lab_ in retl if _split_lab(lab_)[1][:2] == "R:"}
            if self._extracted(tg, retl):
                out.add("R:" + tg)
            for pname, aexpr in self._actuals(tg, expr, False, scope.module)[0]:
                al = None
                for lab_ in retl:
                    pre, b = _split_lab(lab_)
                    if b == "P:" + pname:
                        al = lab(sid, aexpr, extra) if al is None else al
                        out |= {self._cap(pre + a) for a in al}
                    elif b in ("X:" + pname, "Y:" + pname, "Z:" + pname):
                        al = lab(sid, aexpr, extra) if al is None else al
                        out |= {self._cap(pre + c) for c in self._carried(al, tg)}
        return out

    # ---- 고정점 ----
    @staticmethod
    def _leaf_targets(target):
        if isinstance(target, (ast.Tuple, ast.List)):
            return [leaf for elt in target.elts for leaf in _OpCopy._leaf_targets(elt)]
        if isinstance(target, ast.Starred):
            return _OpCopy._leaf_targets(target.value)
        return [target]

    def _step(self, sid):
        eng = self.eng
        scope = eng.scopes[sid]
        T, globals_ = self.T[sid], self.globals_[sid]
        flag = [False]
        lab = lambda e: self.labels(sid, e)             # noqa: E731

        def put(names, labs):
            if not labs:
                return
            for n in names:
                cur = T.setdefault(n, set())
                if not labs <= cur:
                    cur |= labs
                    flag[0] = True

        def sink(labs, kind, node, local=True):
            if not labs:
                return
            form = kind + ":" + (node if isinstance(node, str) else self._text(node))
            rec = self.sink_rec[sid]
            for item in labs:
                key = (item, form, local)
                if key not in rec:
                    rec.add(key)
                    flag[0] = True
            self.sink[sid] |= labs

        in_init = scope.node.name in ("__init__", "__post_init__") if isinstance(scope.node, (ast.FunctionDef, ast.AsyncFunctionDef)) else False
        for node in self.nodes[sid]:
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                if getattr(node, "value", None) is None:
                    continue
                for target in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                    for leaf, val, _exact in self._unpack(target, node.value):       # 짝이 맞는 풀기는 왼쪽 이름별로 자기 오른쪽 식의 라벨만 받는다
                        t = lab(val)
                        put(self._store_names(leaf), t)
                        if isinstance(leaf, ast.Name):
                            if leaf.id in globals_:
                                sink(t, "global", leaf)                   # 전역·바깥 함수 변수에 담는다
                        elif isinstance(leaf, ast.Attribute):
                            if not (in_init and isinstance(leaf.value, ast.Name) and leaf.value.id == "self"):   # 생성 중인 객체(흐름은 생성자 라벨이 따른다)
                                sink(t, "attr", leaf)                     # 속성: 객체가 호출보다 오래 사는지 풀리지 않는다
                        elif isinstance(leaf, ast.Subscript):
                            klabs = set() if isinstance(leaf.slice, ast.Slice) else lab(leaf.slice)
                            if self._local_container(sid, leaf):
                                put(self._store_names(leaf), _as_value(klabs))             # 지역 컨테이너의 키도 담긴 값이다
                            else:
                                sink(t, "subscript", leaf)                # 첨자: 이 함수에서 새로 만든 컨테이너가 아니면 오래 사는지 풀리지 않는다
                                sink(klabs, "key", leaf)                  # 사전 키로 담기
            elif isinstance(node, ast.For):
                for n, labs_ in self._bind_iter(sid, node.target, node.iter, None).items():
                    put({n}, labs_)
            elif isinstance(node, ast.comprehension):
                for n, labs_ in self._bind_iter(sid, node.target, node.iter, None).items():
                    put({n}, labs_)
            elif isinstance(node, (ast.Return, ast.Yield, ast.YieldFrom)) and node.value is not None:
                t = lab(node.value)
                if self._is_block(scope) and isinstance(node, ast.Return):
                    sink(t, "block-return", node.value)
                elif not self._is_output(sid) and not t <= self.ret[sid]:                  # 출력 함수의 반환은 보고 객체(iii)
                    self.ret[sid] |= t
                    flag[0] = True
            elif isinstance(node, ast.Assert):
                if node.msg is not None:
                    sink(lab(node.msg), "assert-msg", node.msg)
            elif isinstance(node, ast.Call):
                self._step_call(sid, node, put, sink, flag)
            if isinstance(node, ast.expr) and not isinstance(node, _MODELED_EXPR):
                if not (isinstance(getattr(node, "parent", None), ast.expr) and not isinstance(node.parent, _MODELED_EXPR)):
                    if isinstance(node, ast.NamedExpr):
                        put({node.target.id}, lab(node.value))
                    sink(self._union(sid, self._top_exprs(node)), "untraced:" + type(node).__name__, node)
            elif isinstance(node, ast.stmt) and not isinstance(node, _MODELED_STMT):
                if isinstance(node, (ast.With, ast.AsyncWith)):
                    for item in node.items:
                        if item.optional_vars is not None:
                            put(self._store_names(item.optional_vars), lab(item.context_expr))
                head = "; ".join(self._text(e) for e in sorted(self._top_exprs(node), key=lambda e: (e.lineno, e.col_offset)))
                sink(self._union(sid, self._top_exprs(node)), "untraced:" + type(node).__name__, head)
        return flag[0]

    def _union(self, sid, exprs):
        out = set()
        for e in exprs:
            out |= self.labels(sid, e)
        return out

    def _step_call(self, sid, node, put, sink, flag):
        eng = self.eng
        scope = eng.scopes[sid]
        fn = node.func
        if id(node) in self.read_ids[sid]:
            return
        lab = lambda e: self.labels(sid, e)             # noqa: E731
        exprs = [a.value if isinstance(a, ast.Starred) else a for a in node.args] + [k.value for k in node.keywords]
        arg_labs = self._union(sid, exprs)
        if isinstance(fn, ast.Attribute) and fn.attr in CONTAINER_ADD:
            base = fn.value
            while isinstance(base, (ast.Attribute, ast.Subscript)):
                base = base.value
            if isinstance(base, ast.Name):
                put({base.id}, arg_labs)                      # 흐름 추적(수신자 변수에 라벨이 옮겨 붙는다)
        if isinstance(fn, ast.Attribute) and fn.attr == "write":
            sink(arg_labs, "write", node)                     # 정본 쓰기·파일 쓰기: 정의된 영속 자리
        elif not self._resolved_call(sid, node):
            sink(arg_labs | lab(fn.value if isinstance(fn, ast.Attribute) else fn), "call", node)   # 추적 불능 호출: 넘긴 값 모두 영속으로 본다
        self._step_callbacks(sid, node, put, sink)
        for callee in self._precise(scope, fn):
            self._link(sid, node, callee, arg_labs, sink, flag)

    def _step_callbacks(self, sid, node, put, sink):
        """map·filter 의 함수 인자, sorted·min·max·list.sort 의 key= 콜백. 람다는 매개변수에 원소 라벨을 묶어 본문을 따라가고(본문은 이 함수 안),
        내장 함수 이름은 그대로 두고, 나머지는 따라갈 수 없으니 원소를 sink 로 본다."""
        fn = node.func
        jobs = []                                                # (콜백 식, 원소를 내는 식들)
        if self._builtin(sid, fn, ("map", "filter")) and node.args:
            jobs.append((node.args[0], list(node.args[1:])))
        elif self._builtin(sid, fn, ("sorted", "min", "max")):
            data = list(node.args[:1]) if len(node.args) == 1 or fn.id == "sorted" else list(node.args)
            jobs += [(k.value, data) for k in node.keywords if k.arg == "key"]
        elif isinstance(fn, ast.Attribute) and fn.attr == "sort" and self._btype(sid, fn.value) == "list":
            jobs += [(k.value, [fn.value]) for k in node.keywords if k.arg == "key"]
        for cb, data in jobs:
            per = [_elems(self.labels(sid, d)) if len(data) == 1 or self._builtin(sid, fn, ("map", "filter", "sorted")) else _as_value(self.labels(sid, d))
                   for d in data]
            allv = set().union(*per) if per else set()
            if isinstance(cb, ast.Lambda):
                a = cb.args
                names = [x.arg for x in a.posonlyargs + a.args + a.kwonlyargs] + [x.arg for x in (a.vararg, a.kwarg) if x]
                for i, n in enumerate(names):
                    put({n}, per[i] if len(per) == len(names) and len(per) > 1 else allv)
            elif not (isinstance(cb, ast.Constant) and cb.value is None) and not self._builtin(sid, cb, BUILTIN_PURE_FUNCS | BUILTIN_FLOW_FUNCS):
                sink(allv, "callback", cb)

    def _link(self, sid, node, callee, arg_labs, sink, flag):
        """호출 자리의 실인자 라벨을 피호출(생성자면 __init__)의 매개변수와 맞춘다. 맞출 수 없는 실인자·풀리지 않는 피호출은 sink."""
        eng = self.eng
        ctor = callee in eng.classes
        if ctor:
            target, opaque = self._class_init(callee)
            if opaque:
                sink(arg_labs, "ctor-opaque", node)
                return
            if target is None:
                return                                           # 칸 선언만 있는 값 형식: 흐름은 생성자 라벨이 따른다
        else:
            target = callee
        tscope = eng.scopes[target]
        if self._is_block(tscope) or not self._plain_function(tscope) or target not in self.cset:
            sink(arg_labs, "call", node)                    # 블록 extras·장식된 함수(인자를 보관할 수 있다)·분석하지 못한 피호출
            return
        mapped, unmapped = self._actuals(target, node, ctor, eng.scopes[sid].module)
        for expr in unmapped:
            sink(self.labels(sid, expr), "call", node)      # *args·**kwargs·위치 초과: 매개변수에 맞출 수 없다
        for pname, aexpr in mapped:
            lab_a = self.labels(sid, aexpr)
            if not lab_a:
                continue
            if pname in ("self", "cls"):
                sink(lab_a, "call", node)
                continue
            if self._s_tainted(sid, lab_a) and pname not in self.recv[target]:
                self.recv[target].add(pname)
                flag[0] = True
            if any(_split_lab(l)[1] in (k + pname for k in ("P:", "X:", "Y:", "Z:")) for l in self.sink[target]):
                sink(set(lab_a), "arg", "%s(%s)" % (self._text(node.func), pname), local=False)

    def run(self):
        for _ in range(OP_COPY_ROUNDS):
            grew = False
            for sid in self.cands:
                grew = self._step(sid) or grew
            if not grew:
                return
        self.nonconverged = True            # 상한까지 돌고도 더 자란다: 추적이 끊겼으니 조용히 멈추지 않고 위반으로 낸다

    @staticmethod
    def _path(lab):
        """라벨의 칸 경로: 바깥 칸부터 안쪽 칸 순서의 이름 tuple (칸 접두가 없으면 빈 tuple)."""
        pre = _split_lab(lab)[0]
        return tuple(h[1:] for h in pre.split("|") if h.startswith("@"))

    def copies(self):
        """{사본 자리 함수 sid: {(칸 경로, sink 꼴), ...}}."""
        self.run()
        found = {}
        for sid in self.cands:
            for lab, form, local in sorted(self.sink_rec[sid]):
                base = _split_lab(lab)[1]
                if local and self._s_tainted(sid, [lab]):
                    found.setdefault(sid, set()).add((self._path(lab), form))
                if base[:2] == "R:" and base[2:] in self.cset:
                    callee = base[2:]       # 사본을 만든 피호출: 칸 경로 = 받은 쪽에서 담은 칸 + 피호출이 돌려준 칸, sink 꼴 = 받은 쪽(호출자)의 것
                    inner = {self._path(r) for r in self.ret[callee] if _split_lab(r)[1] in SRC_BASES} or {()}
                    found.setdefault(callee, set()).update((self._path(lab) + path, form) for path in inner)
        return found


def _fmt_path(path):
    return ".".join(path) if path else "<칸 전체>"


def _cleared_rows(rows):
    """op_copy_cleared 행 = (위반 키, 칸 경로 tuple, sink 꼴 문자열, 근거) -> {(키, 칸 경로, 공백 정규화한 sink 꼴)}. 모양이 다르면 거부(fail-closed)."""
    out = set()
    for row in rows:
        if len(row) != 4:
            raise ValueError("op_copy_cleared 행은 (위반 키, 칸 경로, sink 꼴, 근거) 넷이다: %r" % (row,))
        out.add((tuple(row[0]), tuple(row[1]), _norm(str(row[2]))))
    return out


def _rule_l5(eng, reach, params, out, blocks):
    output_sids = {_spec_sid(s) for s in params.output_functions}
    cleared = tuple(getattr(params, "op_copy_cleared", ()))
    cleared_set = _cleared_rows(cleared)
    op_found = {}
    for concept, (canon, writer_file) in sorted(params.l5_concepts.items()):
        if concept not in ("diode", "same_vgs", "op_copy"):
            raise ValueError("규칙 L-5: 등록 개념의 판정기가 없다: " + concept)
        if writer_file not in eng.modules.values():
            out.append(Violation(("L-5", concept, writer_file, "<writer_file>"), "writer_file_missing", "등록 writer 파일이 엔진에 없다"))
            continue
        if concept == "op_copy":
            kind, _, field = canon.partition(".")
            label = blocks.table.get((kind, field))                      # 정본 쓰기 면제 = 그 필드를 쓰는 블록 자신(N3.1-5), 파일 전체가 아니다
            exempt = {blocks.block_sid[label]} if label in blocks.block_sid else set()
            op = _OpCopy(eng, reach, (kind, field), output_sids, exempt)
            found = op.copies()
            if op.nonconverged:
                out.append(Violation(("L-5", "op_copy", writer_file, "<fixed_point>"), "op_copy",
                                     "추적이 %d회 안에 끝나지 않았다(추적 실패)" % OP_COPY_ROUNDS))
            for sid in sorted(found):
                scope = eng.scopes[sid]
                key = ("L-5", "op_copy", eng.modules[scope.module], _qual(sid))
                op_found[key] = found[sid]
                left = tuple(sorted(pair for pair in found[sid] if (key, pair[0], pair[1]) not in cleared_set))
                if left:
                    paths = tuple(sorted({pa for pa, _form in left}))
                    out.append(Violation(key, "op_copy", "정본 %s 의 칸 값을 영속 자리에 그대로 담거나 추적이 끊긴다; 칸 경로·sink 꼴: %s"
                                         % (canon, "; ".join("%s @ %s" % (_fmt_path(pa), form) for pa, form in left)), paths, left))
            continue
        for sid in sorted(eng.scopes):
            scope = eng.scopes[sid]
            if eng.modules[scope.module] == writer_file:
                continue
            diode, same = _predicate_sites(scope)
            if (concept == "diode" and diode) or (concept == "same_vgs" and same):
                out.append(Violation(("L-5", concept, eng.modules[scope.module], _qual(sid)), "predicate_recomputed", "정본 %s 를 다시 계산한다" % canon))
    stale = {}
    for key, path, form in sorted(cleared_set):
        if (path, form) not in op_found.get(key, ()):
            where = key[2:4] if len(key) >= 4 else ("<행>", str(key))
            stale.setdefault(("L-5", "op_copy_cleared") + tuple(where), []).append((path, form))
    for key, pairs in sorted(stale.items()):
        out.append(Violation(key, "op_copy_cleared_stale",
                             "표 행이 지금 잡히지 않는다(낡은 항목): " + "; ".join("%s @ %s" % (_fmt_path(pa), form) for pa, form in sorted(pairs)),
                             tuple(sorted({pa for pa, _f in pairs})), tuple(sorted(pairs))))


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
    _rule_l5(eng, reach, params, out, blocks)
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


CLEARED_FILE = "rule_l_op_copy_cleared.json"      # rule_l_tables.CLEARED_FILE 과 같은 이름(이 파일은 tables 를 import 하지 않는다)


def fingerprint(params, checks_path: Path, tables_path: Path, cleared_path: Path | None = None) -> str:
    """판정을 바꿀 수 있는 입력의 지문: 정렬 JSON(UTF-8, 고정 구분자)의 sha256 16진.
    대상 = 규칙 매개변수 전부(진입점·출력 함수·동적 접근 허용 파일·L-5 등록표·출력 전용/지문 전용 목록·손 분류 표 행)
    + rule_l_checks.py·rule_l_tables.py·손 분류 표 데이터 파일(`rule_l_op_copy_cleared.json`) 바이트(줄바꿈 정규화).
    표 파일은 cleared_path 를 주지 않으면 tables_path 와 같은 폴더의 같은 이름 파일이다. 파일이 없으면 FileNotFoundError(조용히 건너뛰지 않는다)."""
    cleared = Path(cleared_path) if cleared_path is not None else Path(tables_path).with_name(CLEARED_FILE)
    payload = {
        "params": dict(params._asdict()),
        "checks": _normalized(Path(checks_path)),
        "tables": _normalized(Path(tables_path)),
        "op_copy_cleared_file": _normalized(cleared),
    }
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=list)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
