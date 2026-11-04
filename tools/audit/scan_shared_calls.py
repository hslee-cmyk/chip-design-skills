"""gmid_engine 공유 호출 감사 도구 (읽기 전용, GL-1, design 40 §2.4.10 'GL-1 design' 감사 도구).

사용: python scan_shared_calls.py --engine <gmid_engine 폴더> --out <산출물 폴더> [--touching <상대 경로> ...]

대상 엔진을 import·실행하지 않는다(AST 로만 읽는다, 표준 라이브러리만). 호출을 정의 모듈로 해석하고(패키지 재수출 포함),
인자를 잎(필드 F[종류.필드], 매개변수 P[이름], 리터럴, 전역 G[이름])으로 치환해 호출 모듈이 다른 두 자리의 쌍을
B / not_B / D 로 가른다. 확정 판정자가 아니다: D 와 B 는 판정자가 자리마다 G0~G7 근거로 손 분류한다(N6.3 (i)).
산출물: calls.json, shared.tsv, b_candidates.tsv, limits.json (UTF-8, LF, 정렬, 절대 경로 없음).
종료 코드: 0 성공, 2 입력 오류(산출물 b_candidates.tsv 를 남기지 않는다).
정적 한계: 메서드 호출 `obj.f(x)` 는 해석하지 않고 limits.json 에 수만 센다. 별칭을 거친 호출·동적 호출·람다 매개변수는 못 푼다.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

PKG = "gmid_engine"
DEF_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
FUNC_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)
SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
OUTPUTS = ("calls.json", "shared.tsv", "b_candidates.tsv", "limits.json")
SHARED_HEADER = "callee_mod\tcallee\tn_caller_mods\tn_sites\tcaller_mods"
B_HEADER = "callee_mod\tcallee\tclass\tn_sites\tpairs_b\tpairs_not_b\tpairs_d"
TEXT_MAX = 300


class InputError(Exception):
    pass


class Fn:
    """함수 하나의 지역 환경: 매개변수, 지역 대입(이름 -> [(줄, 식)]), 바깥 함수."""

    def __init__(self, node, parent):
        self.node = node
        self.parent = parent
        a = node.args
        self.pos = [x.arg for x in list(a.posonlyargs) + list(a.args)]
        self.params = set(self.pos) | {x.arg for x in a.kwonlyargs}
        self.params |= {x.arg for x in (a.vararg, a.kwarg) if x is not None}
        self.assigns: dict[str, list] = {}
        self.top_level = False


def _target_names(t) -> list[str]:
    if isinstance(t, ast.Name):
        return [t.id]
    if isinstance(t, (ast.Tuple, ast.List)):
        return [n for e in t.elts for n in _target_names(e)]
    if isinstance(t, ast.Starred):
        return _target_names(t.value)
    return []


def _own_nodes(body):
    """중첩 def·class·lambda 의 본문을 뺀 노드(그 노드 자신은 포함)."""
    stack = list(reversed(body))
    while stack:
        n = stack.pop()
        yield n
        if isinstance(n, SCOPE_NODES):
            continue
        stack.extend(reversed(list(ast.iter_child_nodes(n))))


def _collect_assigns(fn: Fn) -> None:
    def add(names, expr):
        for nm in names:
            fn.assigns.setdefault(nm, []).append((expr.lineno, expr))

    for n in _own_nodes(fn.node.body):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                add(_target_names(t), n.value)
        elif isinstance(n, ast.AnnAssign) and n.value is not None:
            add(_target_names(n.target), n.value)
        elif isinstance(n, (ast.For, ast.AsyncFor, ast.comprehension)):
            add(_target_names(n.target), n.iter)
        elif isinstance(n, ast.withitem) and n.optional_vars is not None:
            add(_target_names(n.optional_vars), n.context_expr)
        elif isinstance(n, ast.NamedExpr):
            add(_target_names(n.target), n.value)


class Module:
    def __init__(self, name: str, rel: str, is_pkg: bool, tree: ast.Module):
        self.name = name
        self.rel = rel
        self.is_pkg = is_pkg
        self.tree = tree
        self.defs = {n.name for n in tree.body if isinstance(n, DEF_NODES)}
        self.funcs = {n.name: n for n in tree.body if isinstance(n, FUNC_NODES)}
        self.globals = set(self.defs)
        for n in tree.body:
            for t in (n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, ast.AnnAssign) else []):
                self.globals.update(_target_names(t))
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                self.globals.update((a.asname or a.name).split(".")[0] for a in n.names)
        self.calls: list = []        # (Call, Fn|None, caller_fn 이름) -- 모듈 안 모든 호출
        self.fn_of: dict[int, Fn] = {}
        self._scan()

    def _scan(self) -> None:
        stack = [(self.tree, None, "<module>", True)]
        while stack:
            node, fn, qual, top = stack.pop()
            kids = []
            if isinstance(node, FUNC_NODES):
                f = Fn(node, fn)
                f.top_level = top and node.name in self.funcs and self.funcs[node.name] is node
                _collect_assigns(f)
                self.fn_of[id(node)] = f
                q = node.name if qual == "<module>" else qual + "." + node.name
                kids = [(c, fn, qual, False) for c in node.decorator_list]
                kids += [(c, fn, qual, False) for c in list(node.args.defaults) + [d for d in node.args.kw_defaults if d]]
                kids += [(c, f, q, False) for c in node.body]
            elif isinstance(node, ast.ClassDef):
                q = node.name if qual == "<module>" else qual + "." + node.name
                kids = [(c, fn, qual, False) for c in list(node.decorator_list) + list(node.bases)]
                kids += [(c, fn, q, False) for c in node.body]
            else:
                if isinstance(node, ast.Call):
                    self.calls.append((node, fn, qual))
                kids = [(c, fn, qual, top and isinstance(node, ast.Module)) for c in ast.iter_child_nodes(node)]
            stack.extend(reversed(kids))


class Engine:
    def __init__(self, root: Path):
        self.mods: dict[str, Module] = {}
        for p in sorted(root.rglob("*.py")):
            parts = p.relative_to(root).parts
            if parts[0] == "tests" or any(x == "__pycache__" or x.startswith(".") for x in parts):
                continue
            rel = "/".join(parts)
            try:
                tree = ast.parse(p.read_text(encoding="utf-8"), filename=rel)
            except (SyntaxError, UnicodeDecodeError, ValueError) as e:
                raise InputError("구문 오류·읽기 실패: %s (%s)" % (rel, e))
            stem = rel[:-3]
            is_pkg = stem.endswith("__init__") and (stem == "__init__" or stem.endswith("/__init__"))
            if is_pkg:
                stem = stem[: -len("__init__")].rstrip("/")
            dotted = ".".join([PKG] + ([x for x in stem.split("/") if x] if stem else []))
            self.mods[dotted] = Module(dotted, rel, is_pkg, tree)
        if not self.mods:
            raise InputError(".py 파일이 없다")

    # -------------------------------------------------------- 이름 해석
    def _from_module(self, m: Module, node: ast.ImportFrom) -> str | None:
        if node.level == 0:
            return node.module
        parts = m.name.split(".")
        base = parts if m.is_pkg else parts[:-1]
        up = node.level - 1
        if up > len(base):
            return None
        base = base[: len(base) - up]
        if node.module:
            base = base + node.module.split(".")
        return ".".join(base)

    def follow(self, mod: str, name: str, seen=frozenset()):
        """재수출을 따라 정의 모듈로: (정의 모듈, 이름) 또는 None."""
        if mod not in self.mods or (mod, name) in seen:
            return None
        m = self.mods[mod]
        if name in m.defs:
            return (mod, name)
        seen = seen | {(mod, name)}
        for node in ast.walk(m.tree):
            if isinstance(node, ast.ImportFrom):
                src = self._from_module(m, node)
                if src is None:
                    continue
                for a in node.names:
                    if (a.asname or a.name) == name:
                        r = self.follow(src, a.name, seen)
                        if r:
                            return r
        return None

    def imports(self, m: Module):
        """(이름 -> (모듈, 함수), 별칭 -> 모듈 전체 이름)."""
        names: dict[str, tuple] = {}
        aliases: dict[str, str] = {}
        for node in ast.walk(m.tree):
            if isinstance(node, ast.ImportFrom):
                src = self._from_module(m, node)
                if src is None:
                    continue
                for a in node.names:
                    local = a.asname or a.name
                    if (src + "." + a.name) in self.mods:
                        aliases[local] = src + "." + a.name
                        continue
                    r = self.follow(src, a.name)
                    if r:
                        names[local] = r
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.asname:
                        if a.name in self.mods:
                            aliases[a.asname] = a.name
                    elif a.name.split(".")[0] == PKG:
                        aliases[PKG] = PKG
        return names, aliases

    def resolve(self, m: Module, call: ast.Call, names, aliases):
        f = call.func
        if isinstance(f, ast.Name):
            if f.id in names:
                return names[f.id]
            if f.id in m.defs:
                return (m.name, f.id)
            return None
        if isinstance(f, ast.Attribute):
            parts = []
            e = f
            while isinstance(e, ast.Attribute):
                parts.append(e.attr)
                e = e.value
            if not isinstance(e, ast.Name) or e.id not in aliases:
                return None
            parts.reverse()
            full = ".".join([aliases[e.id]] + parts[:-1])
            return self.follow(full, parts[-1])
        return None


# -------------------------------------------------------- 인자 잎 치환

def _str_const(n) -> str | None:
    return n.value if isinstance(n, ast.Constant) and isinstance(n.value, str) else None


class Tracer:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.sites: dict[tuple, list] = {}      # (모듈, 함수) -> [(Call, 호출한 Fn)] -- 같은 모듈 호출 자리
        for m in engine.mods.values():
            names, aliases = engine.imports(m)
            for call, fn, _ in m.calls:
                if isinstance(call.func, ast.Name) and call.func.id in m.funcs and call.func.id not in names:
                    self.sites.setdefault((m.name, call.func.id), []).append((call, fn))

    def key(self, e, fn, line, seen, leaves, mod: Module) -> str:
        if isinstance(e, ast.Constant):
            s = repr(e.value)
            leaves.append(s)
            return s
        if isinstance(e, ast.Name):
            return self.name(e.id, fn, line, seen, leaves, mod)
        if isinstance(e, ast.Call):
            f = e.func
            if isinstance(f, ast.Attribute):
                if f.attr == "column" and len(e.args) >= 2 and _str_const(e.args[0]) and _str_const(e.args[1]):
                    leaf = "F[%s.%s]" % (_str_const(e.args[0]), _str_const(e.args[1]))
                    leaves.append(leaf)
                    return leaf
                if f.attr == "value" and len(e.args) >= 3 and _str_const(e.args[0]) and _str_const(e.args[2]):
                    leaf = "F[%s.%s]" % (_str_const(e.args[0]), _str_const(e.args[2]))
                    leaves.append(leaf)
                    return leaf
            args = [self.key(a, fn, line, seen, leaves, mod) for a in e.args]
            args += ["%s=%s" % (k.arg, self.key(k.value, fn, line, seen, leaves, mod)) for k in e.keywords]
            return "%s(%s)" % (self.key(f, fn, line, seen, leaves, mod), ",".join(args))
        if isinstance(e, ast.Attribute):
            return "%s.%s" % (self.key(e.value, fn, line, seen, leaves, mod), e.attr)
        if isinstance(e, ast.Starred):
            return "*" + self.key(e.value, fn, line, seen, leaves, mod)
        kids = [self.key(c, fn, line, seen, leaves, mod) for c in ast.iter_child_nodes(e)
                if isinstance(c, ast.expr)]
        return "%s(%s)" % (type(e).__name__, ",".join(kids))

    def name(self, nm, fn, line, seen, leaves, mod: Module) -> str:
        f = fn
        while f is not None:
            marker = (id(f), nm)
            before = [x for x in f.assigns.get(nm, []) if x[0] < line]
            use = before[-1] if before else (None if nm in f.params else (f.assigns[nm][-1] if nm in f.assigns else None))
            if use is not None:
                if marker in seen:
                    leaf = "P[%s]" % nm
                    leaves.append(leaf)
                    return leaf
                return self.key(use[1], f, use[0], seen | {marker}, leaves, mod)
            if nm in f.params:
                return self.param(f, nm, seen, leaves, mod)
            f = f.parent
        leaf = "G[%s]" % nm
        leaves.append(leaf)
        return leaf

    def param(self, f: Fn, nm, seen, leaves, mod: Module) -> str:
        marker = (id(f), nm)
        leaf = "P[%s]" % nm
        if f.top_level and nm in f.pos and marker not in seen:
            callers = [(c, cf) for c, cf in self.sites.get((mod.name, f.node.name), []) if cf is not f]
            if len(callers) == 1:
                call, cfn = callers[0]
                i = f.pos.index(nm)
                arg = call.args[i] if i < len(call.args) and not isinstance(call.args[i], ast.Starred) else None
                if arg is None:
                    arg = next((k.value for k in call.keywords if k.arg == nm), None)
                if arg is not None:
                    return self.key(arg, cfn, call.lineno, seen | {marker}, leaves, mod)
        leaves.append(leaf)
        return leaf

    def site_keys(self, call: ast.Call, fn, mod: Module):
        leaves: list[str] = []
        keys = [self.key(a, fn, call.lineno, frozenset(), leaves, mod) for a in call.args]
        keys += ["%s=%s" % (k.arg, self.key(k.value, fn, call.lineno, frozenset(), leaves, mod)) for k in call.keywords]
        return keys, sorted(set(leaves))


# -------------------------------------------------------- 분류와 산출

def _field_leaves(s) -> int:
    return sum(1 for x in s["leaves"] if x.startswith("F["))


def _param_leaves(s) -> int:
    return sum(1 for x in s["leaves"] if x.startswith("P["))


def classify_pair(a, b) -> str:
    if a["arg_keys"] == b["arg_keys"] and _field_leaves(a) >= 1 and _field_leaves(b) >= 1:
        return "B"
    if (a["arg_keys"] != b["arg_keys"] and _field_leaves(a) >= 1 and _field_leaves(b) >= 1
            and _param_leaves(a) == 0 and _param_leaves(b) == 0):
        return "not_B"
    return "D"


def normalize_touching(t: str, rels: set[str]) -> str:
    p = t.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    if p in rels:
        return p
    marker = PKG + "/"
    if marker in p:
        tail = p.split(marker, 1)[1]
        if tail in rels:
            return tail
    raise InputError("--touching 경로가 대상 파일에 없다: %s" % t)


def scan(engine_dir: Path, touching: list[str]):
    if not engine_dir.is_dir():
        raise InputError("--engine 폴더가 없다: %s" % engine_dir.name)
    if engine_dir.name != PKG:
        raise InputError("--engine 폴더 이름은 %s 여야 한다" % PKG)
    eng = Engine(engine_dir)
    rels = {m.rel for m in eng.mods.values()}
    touched = {normalize_touching(t, rels) for t in touching}
    tracer = Tracer(eng)
    calls, method_unresolved = [], 0
    for mname in sorted(eng.mods):
        m = eng.mods[mname]
        names, aliases = eng.imports(m)
        for call, fn, qual in m.calls:
            tgt = eng.resolve(m, call, names, aliases)
            if tgt is None:
                if isinstance(call.func, ast.Attribute):
                    method_unresolved += 1
                continue
            if tgt[0] == mname:
                continue
            keys, leaves = tracer.site_keys(call, fn, m)
            calls.append({
                "callee_mod": tgt[0], "callee": tgt[1], "caller_mod": mname, "caller_fn": qual,
                "line": call.lineno, "text": ast.unparse(call)[:TEXT_MAX], "arg_keys": keys, "leaves": leaves,
                "_col": call.col_offset, "_rel": m.rel,
            })
    calls.sort(key=lambda c: (c["callee_mod"], c["callee"], c["caller_mod"], c["line"], c["_col"], c["caller_fn"], c["text"]))
    by: dict[tuple, list] = {}
    for c in calls:
        by.setdefault((c["callee_mod"], c["callee"]), []).append(c)
    shared, cand = [], []
    for (cm, fn_name), cs in sorted(by.items()):
        mods = sorted({c["caller_mod"] for c in cs})
        if len(mods) < 2:
            continue
        shared.append("\t".join([cm, fn_name, str(len(mods)), str(len(cs)), ",".join(mods)]))
        if touched and not any(c["_rel"] in touched for c in cs):
            continue
        counts = {"B": 0, "not_B": 0, "D": 0}
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                if cs[i]["caller_mod"] != cs[j]["caller_mod"]:
                    counts[classify_pair(cs[i], cs[j])] += 1
        cls = "B" if counts["B"] else ("D" if counts["D"] else "not_B")
        cand.append("\t".join([cm, fn_name, cls, str(len(cs)), str(counts["B"]), str(counts["not_B"]), str(counts["D"])]))
    limits = {"method_calls_unresolved": method_unresolved,
              "sites_with_param_leaf": sum(1 for c in calls if _param_leaves(c) >= 1)}
    for c in calls:
        del c["_col"], c["_rel"]
    return calls, shared, cand, limits


def _write(path: Path, text: str) -> None:
    path.write_bytes(text.encode("utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--engine", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--touching", nargs="*", default=[])
    ns = ap.parse_args(argv)
    out = Path(ns.out)
    try:
        calls, shared, cand, limits = scan(Path(ns.engine), list(ns.touching))
    except InputError as e:
        stale = out / "b_candidates.tsv"
        if stale.is_file():
            stale.unlink()
        print("입력 오류: %s" % e, file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    _write(out / "calls.json", json.dumps(calls, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    _write(out / "shared.tsv", "".join(x + "\n" for x in [SHARED_HEADER] + shared))
    _write(out / "b_candidates.tsv", "".join(x + "\n" for x in [B_HEADER] + cand))
    _write(out / "limits.json", json.dumps(limits, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("modules-calls %d shared %d" % (len(calls), len(shared)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
