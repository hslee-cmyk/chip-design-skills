"""추출 도구 -- 인라인 self-test 블록(`if __name__ == "__main__":`)을 옮기고 섹션을 분석한다.

변경 20260922-ts1-extract-tool (Phase 1 C1, code-author). 정본 명세: design
`gain-budget-gmid-sizing.10-test-separation` v1.2 §5.1(섹션 경계·범주 규칙)·§5.2(명령·출력·exit code).
표준 라이브러리만 쓴다(Python 3.14).

명령:
    extract  --source <모듈.py> --module <import 이름> --out <파일>
    sections --source <.py> --out <json 경로>
    scan     --root <디렉터리> [--out <json 경로>]

exit code: 0 성공 / 1 scan이 인라인 self-test 발견 / 2 입력 오류(파일 없음·블록 0개 또는 2개 이상·파싱 실패) /
3 미해결 이름 / 4 지원하지 않는 구성.
"""
from __future__ import annotations

import argparse
import ast
import builtins
import hashlib
import json
import re
import sys
from pathlib import Path

# design §5.2-5 머리글 고정 텍스트.
_ASSETS_DIR_LINE = (
    '_ASSETS_DIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else '
    'os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))'
)

_BUILTIN_NAMES = set(dir(builtins))
# 모든 모듈에 파이썬이 자동으로 설정하는 이름(원본 모듈 최상위에서 명시적으로 묶이지 않는다).
_IMPLICIT_DUNDERS = {
    "__name__", "__file__", "__doc__", "__package__", "__loader__",
    "__spec__", "__builtins__", "__cached__",
}
_DISALLOWED_CALLS = {"globals", "locals", "eval", "exec", "__import__"}

# design §7 판정식 T의 토큰 정규식(단어 경계 -- 앞뒤에 알파벳이 없어야 한다).
_TOKEN_RE = re.compile(r"(?<![A-Za-z])(PASS|FAIL)(?![A-Za-z])")
# design §5.1 소 표지 제외 규칙.
_MARKER_EXCLUDE_RE = re.compile(r"^  \[\s*(PASS|FAIL|OK|SKIP|불가)")

_LOG_NAMES = {"logging", "logger", "log", "LOGGER", "LOG"}
_LOG_ATTRS = {"debug", "info", "warning", "warn", "error", "critical", "exception", "log"}

_TRY_TYPES = (ast.Try,) + ((ast.TryStar,) if hasattr(ast, "TryStar") else ())


# ---------------------------------------------------------------------------
# 읽기 유틸리티
# ---------------------------------------------------------------------------

def _read_source(path: Path) -> tuple[bytes, str]:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return raw, text


def _git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


# ---------------------------------------------------------------------------
# 블록 찾기(design §5.1)
# ---------------------------------------------------------------------------

def find_main_blocks(tree: ast.Module) -> list[ast.If]:
    blocks = []
    for node in tree.body:
        if isinstance(node, ast.If):
            try:
                cond = ast.unparse(node.test).replace("'", '"')
            except Exception:
                continue
            if cond == '__name__ == "__main__"':
                blocks.append(node)
    return blocks


# ---------------------------------------------------------------------------
# extract: __file__ 꼴·금지 호출 검사(design §5.2-2·5)
# ---------------------------------------------------------------------------

def _match_file_pattern(node: ast.AST):
    """`<X>.path.dirname(<X>.path.abspath(__file__))` 꼴이면 Call 노드를 돌려준다."""
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if not (isinstance(func, ast.Attribute) and func.attr == "dirname"):
        return None
    if len(node.args) != 1:
        return None
    outer_owner = func.value
    if not (isinstance(outer_owner, ast.Attribute) and outer_owner.attr == "path"
            and isinstance(outer_owner.value, ast.Name)):
        return None
    x1 = outer_owner.value.id
    inner = node.args[0]
    if not isinstance(inner, ast.Call):
        return None
    ifunc = inner.func
    if not (isinstance(ifunc, ast.Attribute) and ifunc.attr == "abspath"):
        return None
    if len(inner.args) != 1:
        return None
    inner_owner = ifunc.value
    if not (isinstance(inner_owner, ast.Attribute) and inner_owner.attr == "path"
            and isinstance(inner_owner.value, ast.Name)):
        return None
    x2 = inner_owner.value.id
    if x1 != x2:
        return None
    arg = inner.args[0]
    if not (isinstance(arg, ast.Name) and arg.id == "__file__"):
        return None
    return node


def _find_file_pattern_nodes(block: ast.If) -> list[ast.Call]:
    matched = []
    for node in ast.walk(block):
        m = _match_file_pattern(node)
        if m is not None:
            matched.append(m)
    return matched


def has_unsupported_construct(block: ast.If) -> bool:
    matched = _find_file_pattern_nodes(block)
    consumed_ids = set()
    for m in matched:
        for sub in ast.walk(m):
            consumed_ids.add(id(sub))
    for node in ast.walk(block):
        if isinstance(node, ast.Name):
            if node.id == "__file__" and id(node) not in consumed_ids:
                return True
            if node.id == "_ASSETS_DIR":
                return True
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id in _DISALLOWED_CALLS:
                return True
    return False


# ---------------------------------------------------------------------------
# extract: 이름 해석(design §5.2-3)
# ---------------------------------------------------------------------------

def _collect_block_names(block: ast.If):
    """블록 안의 (Load 이름, 줄), 저장된 이름 집합, 이름별 최초 저장 줄을 돌려준다."""
    loads: list[tuple[str, int]] = []
    store_names: set[str] = set()
    first_store_line: dict[str, int] = {}

    def note_store(name: str, lineno: int) -> None:
        store_names.add(name)
        first_store_line[name] = min(first_store_line.get(name, lineno), lineno)

    def note_params(arguments: ast.arguments, fallback_lineno: int) -> None:
        # 함수·람다 인자는 `ast.Name`이 아니라 `ast.arg`다 -- design §5.1 의존 규칙의 "인자"와 같은 취급으로
        # 블록 안에서 저장되는 이름으로 센다(원본 모듈 최상위 이름과 무관한 지역 바인딩).
        for name, lineno in _arguments_names_with_lines(arguments, fallback_lineno):
            note_store(name, lineno)

    for node in ast.walk(block):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                loads.append((node.id, node.lineno))
            elif isinstance(node.ctx, ast.Store):
                note_store(node.id, node.lineno)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            note_store(node.name, node.lineno)
            note_params(node.args, node.lineno)
        elif isinstance(node, ast.ClassDef):
            note_store(node.name, node.lineno)
        elif isinstance(node, ast.Lambda):
            note_params(node.args, node.lineno)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                note_store(alias.asname or alias.name.split(".")[0], node.lineno)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    continue
                note_store(alias.asname or alias.name, node.lineno)
        elif isinstance(node, ast.ExceptHandler):
            if node.name:
                note_store(node.name, node.lineno)
    return loads, store_names, first_store_line


def _visit_bind_targets(target: ast.AST, bind) -> None:
    if isinstance(target, ast.Name):
        bind(target.id)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            _visit_bind_targets(elt, bind)
    elif isinstance(target, ast.Starred):
        _visit_bind_targets(target.value, bind)


def collect_module_top_level_bindings(tree: ast.Module, skip_node: ast.AST) -> set[str]:
    """모듈 최상위(`def`·`class`·대입·`import`, `try`/`if` 안 포함)에서 묶이는 이름."""
    bound: set[str] = set()

    def bind(name: str) -> None:
        if name:
            bound.add(name)

    def walk_stmts(stmts) -> None:
        for node in stmts:
            if node is skip_node:
                continue
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    _visit_bind_targets(t, bind)
            elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                _visit_bind_targets(node.target, bind)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    bind(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        bind(alias.asname or alias.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                bind(node.name)
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                _visit_bind_targets(node.target, bind)
                walk_stmts(node.body)
                walk_stmts(node.orelse)
            elif isinstance(node, ast.While):
                walk_stmts(node.body)
                walk_stmts(node.orelse)
            elif isinstance(node, ast.If):
                walk_stmts(node.body)
                walk_stmts(node.orelse)
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if item.optional_vars is not None:
                        _visit_bind_targets(item.optional_vars, bind)
                walk_stmts(node.body)
            elif isinstance(node, _TRY_TYPES):
                walk_stmts(node.body)
                for h in node.handlers:
                    if h.name:
                        bind(h.name)
                    walk_stmts(h.body)
                walk_stmts(node.orelse)
                walk_stmts(node.finalbody)
            else:
                for sub in ast.walk(node):
                    if isinstance(sub, ast.NamedExpr):
                        _visit_bind_targets(sub.target, bind)

    walk_stmts(tree.body)
    return bound


def resolve_import_names(block: ast.If, tree: ast.Module):
    """필요 이름과 추가 이름을 계산한다. 돌려주는 값: (import_names, unresolved)."""
    loads, store_names, first_store_line = _collect_block_names(block)
    top_level = collect_module_top_level_bindings(tree, skip_node=block)

    required = {n for n, _ in loads} - store_names - _BUILTIN_NAMES - _IMPLICIT_DUNDERS
    unresolved = sorted(n for n in required if n not in top_level)
    resolved = {n for n in required if n in top_level}

    additional = set()
    for name in store_names:
        if name in top_level:
            fline = first_store_line[name]
            if any(nm == name and ln < fline for nm, ln in loads):
                additional.add(name)

    import_names = sorted(resolved | additional)
    return import_names, unresolved


# ---------------------------------------------------------------------------
# extract: 본문·머리글 조립(design §5.2-4·5·6)
# ---------------------------------------------------------------------------

def build_extracted_text(source_path: Path, module_name: str, raw_bytes: bytes, text: str,
                          block: ast.If, import_names: list[str]) -> bytes:
    lines = text.split("\n")
    body_lines = lines[block.lineno - 1: block.end_lineno]
    body_text = "\n".join(body_lines)

    for m in _find_file_pattern_nodes(block):
        segment = ast.get_source_segment(text, m)
        if segment is not None and segment in body_text:
            body_text = body_text.replace(segment, "_ASSETS_DIR", 1)
    body_text = body_text.rstrip("\n") + "\n"

    blob_id = _git_blob_id(raw_bytes)
    header_lines = [
        "# extract_selftest: tools/migrate/extract_selftest.py 로 생성했다(사람이 고치지 마라).",
        f"# 원본 경로: {source_path}",
        f"# 원본 blob id: {blob_id}",
        "import os",
        "import sys",
        _ASSETS_DIR_LINE,
        "sys.path.insert(0, _ASSETS_DIR)",
    ]
    if import_names:
        header_lines.append(f"from {module_name} import ({', '.join(import_names)})")
    header_lines.append("")
    header_lines.append("")
    header_text = "\n".join(header_lines)

    return (header_text + body_text).encode("utf-8")


# ---------------------------------------------------------------------------
# sections: 표지·범주(design §5.1)
# ---------------------------------------------------------------------------

def _marker_prefix_text(node: ast.AST):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value for v in node.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
    return None


def classify_marker(stmt: ast.stmt):
    if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)):
        return None
    call = stmt.value
    if not (isinstance(call.func, ast.Name) and call.func.id == "print"):
        return None
    if not call.args:
        return None
    text = _marker_prefix_text(call.args[0])
    if text is None:
        return None
    if text.startswith("# ") or text.startswith("=== "):
        return "major"
    if text.startswith("  ["):
        if _MARKER_EXCLUDE_RE.match(text):
            return None
        return "sub"
    return None


def _is_verdict_call(call: ast.Call) -> bool:
    func = call.func
    if isinstance(func, ast.Name) and func.id == "print":
        return True
    if isinstance(func, ast.Attribute):
        base = func.value
        if isinstance(base, ast.Name) and base.id in _LOG_NAMES and func.attr in _LOG_ATTRS:
            return True
    return False


def _count_tokens_in_expr(node: ast.AST) -> int:
    total = 0
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            total += len(_TOKEN_RE.findall(n.value))
    return total


def _call_verdict_tokens(call: ast.Call) -> int:
    total = 0
    for arg in list(call.args) + [kw.value for kw in call.keywords]:
        total += _count_tokens_in_expr(arg)
    return total


def _section_verdict_tokens(stmts) -> int:
    total = 0
    for s in stmts:
        for n in ast.walk(s):
            if isinstance(n, ast.Call) and _is_verdict_call(n):
                total += _call_verdict_tokens(n)
    return total


def _is_fully_static_string(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return True
    if isinstance(node, ast.JoinedStr):
        return all(isinstance(v, ast.Constant) and isinstance(v.value, str) for v in node.values)
    return False


def _is_static_print_stmt(stmt: ast.stmt) -> bool:
    if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)):
        return False
    call = stmt.value
    if not (isinstance(call.func, ast.Name) and call.func.id == "print"):
        return False
    args = list(call.args) + [kw.value for kw in call.keywords]
    if not args:
        return True
    return all(_is_fully_static_string(a) for a in args)


def _count_asserts(stmts) -> int:
    return sum(1 for s in stmts for n in ast.walk(s) if isinstance(n, ast.Assert))


def _is_assertion_error_exc(exc) -> bool:
    if exc is None:
        return False
    if isinstance(exc, ast.Call):
        f = exc.func
        return (isinstance(f, ast.Name) and f.id == "AssertionError") or \
               (isinstance(f, ast.Attribute) and f.attr == "AssertionError")
    if isinstance(exc, ast.Name):
        return exc.id == "AssertionError"
    return False


def _has_raise_assertion(stmts) -> bool:
    for s in stmts:
        for n in ast.walk(s):
            if isinstance(n, ast.Raise) and _is_assertion_error_exc(n.exc):
                return True
    return False


def _count_reject_try(stmts) -> int:
    count = 0
    for s in stmts:
        for n in ast.walk(s):
            if isinstance(n, ast.ExceptHandler):
                if not any(isinstance(x, ast.Raise) for x in ast.walk(n)):
                    count += 1
    return count


def _arguments_names_with_lines(arguments: ast.arguments, fallback_lineno: int) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for arg in (list(arguments.posonlyargs) + list(arguments.args) + list(arguments.kwonlyargs)):
        out.append((arg.arg, getattr(arg, "lineno", fallback_lineno)))
    if arguments.vararg is not None:
        out.append((arguments.vararg.arg, getattr(arguments.vararg, "lineno", fallback_lineno)))
    if arguments.kwarg is not None:
        out.append((arguments.kwarg.arg, getattr(arguments.kwarg, "lineno", fallback_lineno)))
    return out


def _collect_names_with_lines(stmts, ctx_type):
    out: list[tuple[str, int]] = []
    for root in stmts:
        for node in ast.walk(root):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ctx_type):
                out.append((node.id, node.lineno))
            if ctx_type is ast.Store:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.append((node.name, node.lineno))
                    out.extend(_arguments_names_with_lines(node.args, node.lineno))
                elif isinstance(node, ast.ClassDef):
                    out.append((node.name, node.lineno))
                elif isinstance(node, ast.Lambda):
                    out.extend(_arguments_names_with_lines(node.args, node.lineno))
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        out.append((alias.asname or alias.name.split(".")[0], node.lineno))
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name != "*":
                            out.append((alias.asname or alias.name, node.lineno))
                elif isinstance(node, ast.ExceptHandler):
                    if node.name:
                        out.append((node.name, node.lineno))
    return out


def _group_block_sections(block: ast.If):
    groups = []
    prelude_stmts = []
    cur = None
    for stmt in block.body:
        mk = classify_marker(stmt)
        if mk is None:
            if cur is None:
                prelude_stmts.append(stmt)
            else:
                cur["stmts"].append(stmt)
        else:
            if cur is not None and cur["kind"] == "major" and mk == "major":
                cur["stmts"].append(stmt)
            else:
                if cur is not None:
                    groups.append(cur)
                cur = {"kind": mk, "stmts": [stmt]}
    if cur is not None:
        groups.append(cur)
    return [{"kind": "prelude", "stmts": prelude_stmts}] + groups


def build_sections(block: ast.If, source_text: str) -> list[dict]:
    all_groups = _group_block_sections(block)

    store_events = []
    for idx, g in enumerate(all_groups):
        for name, lineno in _collect_names_with_lines(g["stmts"], ast.Store):
            store_events.append((name, lineno, idx))

    sections = []
    for idx, g in enumerate(all_groups):
        stmts = g["stmts"]
        kind = g["kind"]
        if stmts:
            start = stmts[0].lineno
            end = max(s.end_lineno for s in stmts)
        else:
            start = end = block.lineno

        asserts = _count_asserts(stmts)
        raise_assertion = _has_raise_assertion(stmts)
        vtokens = _section_verdict_tokens(stmts)

        if kind == "prelude":
            category = "P"
        elif stmts and all(_is_static_print_stmt(s) for s in stmts):
            category = "D"
        elif asserts > 0 or raise_assertion:
            category = "A"
        elif vtokens > 0:
            category = "B"
        else:
            category = "C"

        loads = _collect_names_with_lines(stmts, ast.Load)
        deps = set()
        for name, lineno in loads:
            candidates = [(nm, ln, si) for (nm, ln, si) in store_events if nm == name and ln < lineno]
            if candidates:
                _, _, si = max(candidates, key=lambda t: t[1])
                if si != idx:
                    deps.add((name, si))

        defs = sorted({n for n, _ in _collect_names_with_lines(stmts, ast.Store)})
        title = None
        if kind != "prelude" and stmts:
            seg = ast.get_source_segment(source_text, stmts[0])
            title = seg.strip() if seg else None

        sections.append({
            "index": idx,
            "kind": kind,
            "category": category,
            "start": start,
            "end": end,
            "title": title,
            "asserts": asserts,
            "raise_assertion": raise_assertion,
            "reject_try": _count_reject_try(stmts),
            "verdict_tokens": vtokens,
            "deps": [{"name": n, "section": s} for n, s in sorted(deps)],
            "provides_to": [],
            "defs": defs,
        })

    provides = {i: set() for i in range(len(sections))}
    for sec in sections:
        for d in sec["deps"]:
            provides[d["section"]].add(sec["index"])
    for sec in sections:
        sec["provides_to"] = sorted(provides[sec["index"]])
    return sections


def has_inline_selftest(block: ast.If, source_text: str) -> bool:
    return any(s["category"] in ("A", "B") for s in build_sections(block, source_text))


# ---------------------------------------------------------------------------
# 명령 구현
# ---------------------------------------------------------------------------

def cmd_extract(args: argparse.Namespace) -> int:
    source_path = Path(args.source)
    if not source_path.is_file():
        return 2
    try:
        raw, text = _read_source(source_path)
        tree = ast.parse(text, filename=str(source_path))
    except (SyntaxError, UnicodeDecodeError):
        return 2

    blocks = find_main_blocks(tree)
    if len(blocks) != 1:
        return 2
    block = blocks[0]

    if has_unsupported_construct(block):
        return 4

    import_names, unresolved = resolve_import_names(block, tree)
    if unresolved:
        print("미해결 이름:", ", ".join(unresolved), file=sys.stderr)
        return 3

    out_bytes = build_extracted_text(source_path.resolve(), args.module, raw, text, block, import_names)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(out_bytes)
    return 0


def cmd_sections(args: argparse.Namespace) -> int:
    source_path = Path(args.source)
    if not source_path.is_file():
        return 2
    try:
        _, text = _read_source(source_path)
        tree = ast.parse(text, filename=str(source_path))
    except (SyntaxError, UnicodeDecodeError):
        return 2

    blocks = find_main_blocks(tree)
    if len(blocks) != 1:
        return 2
    block = blocks[0]

    sections = build_sections(block, text)
    payload = {"source": str(source_path), "sections": sections}
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    root = Path(args.root)
    if not root.is_dir():
        return 2

    files_info: dict[str, dict] = {}
    any_selftest = False
    for py_file in sorted(root.glob("*.py")):
        entry = {"has_inline_selftest": False, "block_count": 0}
        try:
            _, text = _read_source(py_file)
            tree = ast.parse(text, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            files_info[py_file.name] = entry
            continue
        blocks = find_main_blocks(tree)
        entry["block_count"] = len(blocks)
        flagged = any(has_inline_selftest(b, text) for b in blocks)
        entry["has_inline_selftest"] = flagged
        if flagged:
            any_selftest = True
        files_info[py_file.name] = entry

    if args.out:
        payload = {"root": str(root), "files": files_info}
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return 1 if any_selftest else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="extract_selftest")
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser("extract")
    p_extract.add_argument("--source", required=True)
    p_extract.add_argument("--module", required=True)
    p_extract.add_argument("--out", required=True)
    p_extract.set_defaults(func=cmd_extract)

    p_sections = sub.add_parser("sections")
    p_sections.add_argument("--source", required=True)
    p_sections.add_argument("--out", required=True)
    p_sections.set_defaults(func=cmd_sections)

    p_scan = sub.add_parser("scan")
    p_scan.add_argument("--root", required=True)
    p_scan.add_argument("--out", required=False, default=None)
    p_scan.set_defaults(func=cmd_scan)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
