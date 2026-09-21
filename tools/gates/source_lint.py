"""V6 소스 lint (05-role-separation design §10, 계획 N4.2 V6).

    $PY source_lint.py --root <격리 복제본 루트> --base <커밋> --head <커밋>

소스 분류의 바뀐 `.py`에서 '새' 항목(= base 대비 AST 차이: 같은 단위(함수 qualname, 모듈 최상위)의 항목 수가 늘었다):
* 새 광범위 except(`except:`, `except Exception`, `except BaseException`, 이들을 담은 튜플)
* 새 skip/continue 분기(`continue`) -- 예외: `optional_stages` 화이트리스트를 가르는 선언 분기 1곳, 사유 주석 필수(DEC-75)
* 허용 집합 {0, 1, −1, 산술식의 2, 인덱스} 밖 숫자 리터럴 중 `# derive: <함수명>` 태그(그 함수 존재 검사)가 없는 것
* 읽는 코드 없는 경고 리스트(이름에 warn이 든 리스트가 append·extend·insert로만 쓰인다)
* `id(...)` 캐시 키(`id` 호출)
* 상한 없는 캐시(`functools.cache`·`lru_cache(maxsize=None)`, 이름에 cache가 든 dict에 `len(` 검사가 없다)
exit 0 PASS / 1 FAIL / 2 실행 오류.
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys


def _git(root, args, check=True):
    p = subprocess.run(["git", "-C", root] + args, capture_output=True, env=dict(os.environ, GIT_NO_REPLACE_OBJECTS="1"))
    if check and p.returncode != 0:
        raise RuntimeError("git %s 실패: %s" % (" ".join(args[:3]), p.stderr.decode("utf-8", "replace")[:300]))
    return p


def _src(root, rev, path):
    p = _git(root, ["show", "%s:%s" % (rev, path)], check=False)
    return p.stdout.decode("utf-8", "replace") if p.returncode == 0 else None


def is_source(p):
    return (p.startswith("skills/analog-gmid-design/assets/") and p.count("/") == 3 and p.endswith(".py")) \
        or p == "workspaces/run_harness.py"


BROAD = ("Exception", "BaseException")


def _is_broad(h):
    t = h.type
    if t is None:
        return True
    names = [t] if not isinstance(t, ast.Tuple) else list(t.elts)
    return any((isinstance(x, ast.Name) and x.id in BROAD) or (isinstance(x, ast.Attribute) and x.attr in BROAD) for x in names)


def _units(tree):
    """(단위 이름, 노드 목록, 부모 사슬 사전)."""
    units = []

    def rec(nodes, prefix):
        for n in nodes:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                units.append((prefix + n.name, n))
                rec(n.body, prefix + n.name + ".")
            elif isinstance(n, ast.ClassDef):
                rec(n.body, prefix + n.name + ".")
    rec(tree.body, "")
    return units


def _own_nodes(root_nodes):
    """중첩 def·class 안으로 들어가지 않는 (노드, 부모) 목록."""
    out = []
    stack = [(n, None) for n in root_nodes]
    while stack:
        n, par = stack.pop()
        out.append((n, par))
        for c in ast.iter_child_nodes(n):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                if isinstance(c, ast.Lambda):
                    stack.append((c.body, n))
                continue
            stack.append((c, n))
    return out


def _docstring_nodes(tree):
    ids = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body \
                and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            ids.add(id(n.body[0].value))
    return ids


_DERIVE = re.compile(r"#\s*derive:\s*([A-Za-z_][A-Za-z0-9_]*)")


def unit_features(tree, src, known_defs):
    lines = src.split("\n")
    docs = _docstring_nodes(tree)
    units = [("<module>", [n for n in tree.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))])]
    for name, fn in _units(tree):
        units.append((name, fn.body + fn.args.defaults + [d for d in fn.args.kw_defaults if d is not None] + fn.decorator_list))
    res = {}
    module_text = src
    for name, nodes in units:
        own = _own_nodes(nodes)
        parent = {id(n): p for n, p in own}
        f = {"broad_except": [], "continue": [], "magic_number": [], "warn_list": [], "id_call": [], "unbounded_cache": []}
        for n, par in own:
            if isinstance(n, ast.ExceptHandler) and _is_broad(n):
                f["broad_except"].append(n.lineno)
            if isinstance(n, ast.Continue):
                f["continue"].append(n.lineno)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "id":
                f["id_call"].append(n.lineno)
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool) \
                    and id(n) not in docs:
                if _allowed_number(n, par, parent):
                    continue
                m = _DERIVE.search(lines[n.lineno - 1]) if n.lineno - 1 < len(lines) else None
                if m and m.group(1) in known_defs:
                    continue
                f["magic_number"].append((n.lineno, repr(-n.value if isinstance(par, ast.UnaryOp) and isinstance(par.op, ast.USub) else n.value)))
        # 데코레이터·dict 캐시
        for n, par in own:
            if isinstance(n, ast.Call) and _cache_decorator_unbounded(n):
                f["unbounded_cache"].append(n.lineno)
            if isinstance(n, ast.Assign) and _is_empty_dict(n.value):
                for t in n.targets:
                    nm = t.id if isinstance(t, ast.Name) else (t.attr if isinstance(t, ast.Attribute) else None)
                    if nm and "cache" in nm.lower() and not re.search(r"len\(\s*(self\.)?%s\s*\)" % re.escape(nm), module_text):
                        f["unbounded_cache"].append(n.lineno)
            if isinstance(n, ast.Assign) and _is_empty_list(n.value):
                for t in n.targets:
                    if isinstance(t, ast.Name) and "warn" in t.id.lower() and _write_only(t.id, own):
                        f["warn_list"].append(n.lineno)
        res[name] = f
    return res


def _allowed_number(n, par, parent):
    v = n.value
    if v in (0, 1):
        return True
    if isinstance(par, ast.UnaryOp) and isinstance(par.op, ast.USub) and v == 1:
        return True
    if v == 2 and isinstance(par, ast.BinOp):
        return True
    # 인덱스: 첨자·슬라이스 경계
    if isinstance(par, ast.Subscript) and par.slice is n:
        return True
    if isinstance(par, ast.Slice):
        return True
    if isinstance(par, ast.UnaryOp) and isinstance(parent.get(id(par)), (ast.Subscript, ast.Slice)):
        return True
    return False


def _cache_decorator_unbounded(call):
    f = call.func
    name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
    if name != "lru_cache":
        return False
    for k in call.keywords:
        if k.arg == "maxsize" and isinstance(k.value, ast.Constant) and k.value.value is None:
            return True
    return bool(call.args) and isinstance(call.args[0], ast.Constant) and call.args[0].value is None


def _is_empty_dict(v):
    return (isinstance(v, ast.Dict) and not v.keys) or (isinstance(v, ast.Call) and isinstance(v.func, ast.Name)
                                                        and v.func.id == "dict" and not v.args and not v.keywords)


def _is_empty_list(v):
    return (isinstance(v, ast.List) and not v.elts) or (isinstance(v, ast.Call) and isinstance(v.func, ast.Name)
                                                        and v.func.id == "list" and not v.args)


def _write_only(name, own):
    for n, par in own:
        if isinstance(n, ast.Name) and n.id == name and isinstance(n.ctx, ast.Load):
            if isinstance(par, ast.Attribute) and par.attr in ("append", "extend", "insert"):
                continue
            return False
    return True


def decorator_caches(tree):
    """함수 데코레이터 `@cache`·`@functools.cache` -- 단위(qualname)별 줄."""
    out = {}
    for name, fn in _units(tree):
        for d in fn.decorator_list:
            dn = d.attr if isinstance(d, ast.Attribute) else (d.id if isinstance(d, ast.Name) else "")
            if dn == "cache":
                out.setdefault(name, []).append(d.lineno)
    return out


def known_defs(root, rev):
    out = _git(root, ["ls-tree", "-r", "-z", "--name-only", "--full-tree", rev, "--",
                      "skills/analog-gmid-design/assets/", "workspaces/"]).stdout.decode("utf-8")
    names = set()
    for p in out.split("\0"):
        if p.endswith(".py"):
            s = _src(root, rev, p)
            try:
                names |= {n.name for n in ast.walk(ast.parse(s)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            except (SyntaxError, ValueError):
                continue
    return names


def compare(path, base_src, head_src, kd):
    # DESIGN-GAP: §10 V6 "'새' = base 대비 AST 차이" -- 단위(함수 qualname, 모듈 최상위)마다 항목 수가 base보다 늘면 '새'로
    # 읽는다(같은 단위 안의 위치 이동은 새 항목이 아니다). 새 함수는 모든 항목이 새것이다.
    out = []
    ht = ast.parse(head_src)
    hf = unit_features(ht, head_src, kd)
    for u, lines in decorator_caches(ht).items():
        hf.setdefault(u, {}).setdefault("unbounded_cache", []).extend(lines)
    bf = {}
    if base_src is not None:
        bt = ast.parse(base_src)
        bf = unit_features(bt, base_src, kd)
        for u, lines in decorator_caches(bt).items():
            bf.setdefault(u, {}).setdefault("unbounded_cache", []).extend(lines)
    for unit, feats in hf.items():
        for k, items in feats.items():
            before = bf.get(unit, {}).get(k, [])
            if k == "continue" and len(items) > len(before):
                items = _drop_optional_stages_exempt(head_src, ht, unit, items, before)
            if len(items) > len(before):
                out.append({"path": path, "unit": unit, "check": k, "base": len(before), "head": len(items),
                            "where": items[:10]})
    return out


def _drop_optional_stages_exempt(src, tree, unit, items, before):
    """DEC-75 예외: `optional_stages`를 가르는 선언 분기 안 continue 1곳, 그 if 줄이나 continue 줄에 사유 주석."""
    lines = src.split("\n")
    exempt = None
    for n in ast.walk(tree):
        if isinstance(n, ast.If) and "optional_stages" in ast.unparse(n.test):
            for c in ast.walk(n):
                if isinstance(c, ast.Continue) and c.lineno in items and ("#" in lines[n.lineno - 1] or "#" in lines[c.lineno - 1]):
                    exempt = c.lineno
                    break
        if exempt:
            break
    return [x for x in items if x != exempt]


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="source_lint.py")
    ap.add_argument("--root", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    try:
        ns = ap.parse_args(argv)
    except SystemExit:
        return 2
    try:
        names = _git(ns.root, ["diff", "--name-only", "--no-renames", "--diff-filter=AM", ns.base, ns.head]).stdout.decode("utf-8").splitlines()
        targets = [p for p in names if is_source(p)]
        kd = known_defs(ns.root, ns.head)
        findings = []
        for p in targets:
            findings += compare(p, _src(ns.root, ns.base, p), _src(ns.root, ns.head, p), kd)
    except (OSError, RuntimeError, SyntaxError, UnicodeDecodeError) as e:
        print(json.dumps({"tool": "V6", "verdict": "ERROR", "error": "%s: %s" % (type(e).__name__, e)}, ensure_ascii=False))
        return 2
    print(json.dumps({"tool": "V6", "verdict": "FAIL" if findings else "PASS", "targets": targets, "findings": findings},
                     ensure_ascii=False))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
