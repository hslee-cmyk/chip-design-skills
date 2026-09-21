"""V3 뮤테이션 (05-role-separation design §10, 계획 N4.2 V3, DEC-39 자체 AST 변이기).

    $PY mutate_changed.py --root <격리 복제본 루트> --base <커밋> --head <커밋> --pytest-ini <캐시>/pytest_gate.ini
                          [--python <인터프리터>] [--timeout <초>] [--out <결과 jsonl>]

① diff가 닿은 `def` 중 `ast.dump`(docstring 제외) 해시가 base와 다른 것(새 def 포함)
② 연산자: 비교 뒤집기, 산술 교체(`+↔-`, `*↔/`), 상수 변경(정수 ±1, 실수는 표기된 마지막 자릿수 한 단위 ±),
   문장 삭제, 조기 `return`, `except` 본문 삭제
③ 인벤토리 = 정적 호출 그래프(V7 `reachability.build_graph`)에서 그 함수에 도달하는 test 함수
④ 변이마다 worktree 밖 임시 복사본에서 그 test만(worktree는 바꾸지 않는다)
⑤ 살아남은 변이가 있으면 FAIL. 변이 id = `<모듈>:<함수 qualname>:<연산자>:<AST 노드 경로>`.
   등가 변이 면제는 `target_kind: decision`, `target` = 변이 id 목록인 승인 기록(head 트리).
판정 JSON 한 줄, exit 0 PASS / 1 FAIL / 2 실행 오류. 변이마다 결과를 --out에 append(WP-11).
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import reachability as rch

TESTS_PREFIX = "skills/analog-gmid-design/assets/tests/"
TESTS_TOOLS = "skills/analog-gmid-design/assets/tests/tools/"


def _strip_doc(fn):
    f = copy.deepcopy(fn)
    for n in ast.walk(f):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)) and n.body \
                and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant) \
                and isinstance(n.body[0].value.value, str):
            n.body = n.body[1:] or [ast.Pass()]
    return f


def def_hash(fn):
    return hashlib.sha256(ast.dump(_strip_doc(fn), include_attributes=False).encode("utf-8")).hexdigest()


def changed_defs(base_src, head_src):
    """head의 (qualname, 노드) 중 base와 해시가 다르거나 새 것."""
    bmap = {}
    if base_src is not None:
        try:
            bmap = {q: def_hash(n) for q, n in rch.iter_defs(ast.parse(base_src))}
        except SyntaxError:
            bmap = {}
    out = []
    for q, n in rch.iter_defs(ast.parse(head_src)):
        if bmap.get(q) != def_hash(n):
            out.append((q, n))
    return out


# ---------------------------------------------------------------- 변이 연산자
CMP_FLIP = {ast.Lt: ast.GtE, ast.GtE: ast.Lt, ast.Gt: ast.LtE, ast.LtE: ast.Gt, ast.Eq: ast.NotEq,
            ast.NotEq: ast.Eq, ast.Is: ast.IsNot, ast.IsNot: ast.Is, ast.In: ast.NotIn, ast.NotIn: ast.In}
ARITH = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult}
_NUM_RE = re.compile(r"^([0-9_]*)(?:\.([0-9_]*))?(?:[eE]([+-]?[0-9_]+))?$")


def _float_unit(text):
    """표기된 마지막 자릿수 한 단위(`0.65` → 0.01, `1e-9` → 1e-9, `2.5e3` → 100)."""
    m = _NUM_RE.match(text.replace("_", ""))
    if not m:
        return None
    dec = len(m.group(2) or "")
    exp = int(m.group(3) or 0)
    return 10.0 ** (exp - dec)


def _path_nodes(root):
    """(노드, 경로 문자열) -- 함수 노드 기준 필드 경로. 중첩 def 안으로도 들어간다(그 def의 문장도 변이 대상)."""
    out = []

    def rec(n, path):
        out.append((n, path))
        for fname, val in ast.iter_fields(n):
            if isinstance(val, list):
                for i, x in enumerate(val):
                    if isinstance(x, ast.AST):
                        rec(x, "%s.%s[%d]" % (path, fname, i) if path else "%s[%d]" % (fname, i))
            elif isinstance(val, ast.AST):
                rec(val, "%s.%s" % (path, fname) if path else fname)
    rec(root, "")
    return out


def _get(root, path):
    cur = root
    for part in re.findall(r"([A-Za-z_]+)(?:\[(\d+)\])?", path):
        cur = getattr(cur, part[0])
        if part[1] != "":
            cur = cur[int(part[1])]
    return cur


def mutants(fn, src_text):
    """(연산자, 경로, 변이된 함수 노드) 목록."""
    res = []
    for node, path in _path_nodes(fn):
        if isinstance(node, ast.Compare):
            for k, op in enumerate(node.ops):
                if type(op) in CMP_FLIP:
                    f = copy.deepcopy(fn)
                    _get(f, path).ops[k] = CMP_FLIP[type(op)]()
                    res.append(("cmp_flip", "%s.ops[%d]" % (path, k), f))
        if isinstance(node, (ast.BinOp, ast.AugAssign)) and type(node.op) in ARITH:
            f = copy.deepcopy(fn)
            _get(f, path).op = ARITH[type(node.op)]()
            res.append(("arith", path, f))
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            if isinstance(node.value, int):
                deltas = (1, -1)
            else:
                seg = ast.get_source_segment(src_text, node) if src_text else None
                unit = _float_unit(seg) if seg else None
                deltas = (unit, -unit) if unit else ()
            for d, tag in zip(deltas, ("+", "-")):
                f = copy.deepcopy(fn)
                _get(f, path).value = node.value + d
                res.append(("const" + tag, path, f))
        for fname in ("body", "orelse", "finalbody"):
            stmts = getattr(node, fname, None)
            if isinstance(stmts, list) and stmts and isinstance(stmts[0], ast.stmt) \
                    and not isinstance(node, ast.ExceptHandler):
                for i, s in enumerate(stmts):
                    if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        continue
                    if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str) and i == 0:
                        continue   # docstring
                    f = copy.deepcopy(fn)
                    lst = getattr(_get(f, path), fname)
                    lst[i] = ast.Pass()
                    res.append(("stmt_delete", "%s.%s[%d]" % (path, fname, i) if path else "%s[%d]" % (fname, i), f))
        if isinstance(node, ast.ExceptHandler) and not (len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
            f = copy.deepcopy(fn)
            _get(f, path).body = [ast.Pass()]
            res.append(("except_body_delete", path, f))
    f = copy.deepcopy(fn)
    k = 1 if (fn.body and isinstance(fn.body[0], ast.Expr) and isinstance(fn.body[0].value, ast.Constant)
              and isinstance(fn.body[0].value.value, str)) else 0
    f.body.insert(k, ast.Return(value=None))
    res.append(("early_return", "body[%d]" % k, f))
    return res


def _replace_def(src, fn, new_fn):
    """소스에서 fn의 줄 범위를 new_fn의 unparse로 바꾼다(데코레이터 줄은 유지)."""
    lines = src.split("\n")
    start = fn.lineno - 1
    end = fn.end_lineno
    ind = len(lines[start]) - len(lines[start].lstrip())
    nf = copy.deepcopy(new_fn)
    nf.decorator_list = []
    text = ast.unparse(ast.fix_missing_locations(nf))
    new = [(" " * ind + l) if l.strip() else l for l in text.split("\n")]
    return "\n".join(lines[:start] + new + lines[end:])


def test_nodeid(nid):
    p, q = nid.split("::", 1)
    return p + "::" + q.replace(".", "::")


def inventory(graph_edges, target, test_nodes):
    return sorted(t for t in test_nodes if target in rch.reach(graph_edges, [t]))


def _approved(root, rev):
    return rch._approved_ids(root, rev)


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="mutate_changed.py")
    ap.add_argument("--root", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--pytest-ini", required=True)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--timeout", type=float, default=600.0, help="변이 하나의 test 실행 상한(초) -- 넘으면 죽인 변이")
    ap.add_argument("--out", default=None)
    try:
        ns = ap.parse_args(argv)
    except SystemExit:
        return 2
    tmp = None
    try:
        root = os.path.abspath(ns.root)
        diff = rch._git(root, ["diff", "--name-only", "--no-renames", "--diff-filter=AM", ns.base, ns.head]).decode("utf-8")
        targets = [p for p in diff.splitlines() if p.endswith(".py") and rch._is_source(p)]
        head_files = rch.read_tree(root, ns.head, rch.GRAPH_PREFIXES)
        nodes, edges = rch.build_graph(head_files)
        test_nodes = [n for n in nodes if n.startswith(TESTS_PREFIX) and not n.startswith(TESTS_TOOLS)
                      and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
        approved = _approved(root, ns.head)
        tmp = tempfile.mkdtemp(prefix="gmid-v3-")
        work = os.path.join(tmp, "copy")
        shutil.copytree(root, work, ignore=shutil.ignore_patterns(".git"))
        pyc = os.path.join(tmp, "pycache")
        os.makedirs(pyc)
        survivors, killed, results = [], 0, []
        baseline_ok = {}

        def run_tests(inv):
            env = dict(os.environ, PYTHONPYCACHEPREFIX=pyc, PYTHONDONTWRITEBYTECODE="1")
            cmd = [ns.python, "-P", "-m", "pytest", "-c", ns.pytest_ini, "--rootdir=" + work,
                   "--confcutdir=" + work, "-x", "-q", "-p", "no:cacheprovider"] + \
                  [os.path.join(work, *test_nodeid(t).split("::")[0].split("/")) + "::" +
                   test_nodeid(t).split("::", 1)[1] for t in inv]
            try:
                return subprocess.run(cmd, cwd=work, capture_output=True, env=env, timeout=ns.timeout).returncode
            except subprocess.TimeoutExpired:
                return "timeout"
        for path in targets:
            head_src = head_files[path]
            rc = subprocess.run(["git", "-C", root, "cat-file", "-e", "%s:%s" % (ns.base, path)], capture_output=True,
                                env=dict(os.environ, GIT_NO_REPLACE_OBJECTS="1")).returncode
            base_src = rch._git(root, ["show", "%s:%s" % (ns.base, path)]).decode("utf-8") if rc == 0 else None
            modname = rch.module_name(path)
            fpath = os.path.join(work, *path.split("/"))
            for q, fn in changed_defs(base_src, head_src):
                inv = inventory(edges, "%s::%s" % (path, q), test_nodes)
                if inv and tuple(inv) not in baseline_ok:
                    # 변이 전 기준 실행: 인벤토리 test가 변이 없는 코드에서 통과해야 '죽인 변이'가 뜻이 있다
                    # (기준에서 이미 실패하면 모든 변이가 죽은 것으로 보여 거짓 PASS가 된다 -- WP-02)
                    baseline_ok[tuple(inv)] = run_tests(inv) == 0
                for opname, npath, mfn in mutants(fn, head_src):
                    mid = "%s:%s:%s:%s" % (modname, q, opname, npath)
                    if mid in approved:
                        results.append({"id": mid, "result": "exempt"})
                        continue
                    if not inv:
                        survivors.append(mid)
                        rec = {"id": mid, "result": "survived", "reason": "인벤토리 없음(도달하는 test 없음)"}
                    elif not baseline_ok[tuple(inv)]:
                        survivors.append(mid)
                        rec = {"id": mid, "result": "survived", "reason": "변이 없는 기준 실행에서 인벤토리 test가 통과하지 않음"}
                    else:
                        with open(fpath, "w", encoding="utf-8", newline="\n") as fh:
                            fh.write(_replace_def(head_src, fn, mfn))
                        code = run_tests(inv)
                        with open(fpath, "w", encoding="utf-8", newline="\n") as fh:
                            fh.write(head_src)
                        if code == 0:
                            survivors.append(mid)
                            rec = {"id": mid, "result": "survived", "tests": inv}
                        else:
                            killed += 1
                            rec = {"id": mid, "result": "killed", "exit": code}
                    results.append(rec)
                    if ns.out:
                        with open(ns.out, "a", encoding="utf-8") as fh:
                            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except (OSError, RuntimeError, SyntaxError, ValueError, UnicodeDecodeError) as e:
        print(json.dumps({"tool": "V3", "verdict": "ERROR", "error": "%s: %s" % (type(e).__name__, e)}, ensure_ascii=False))
        return 2
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({"tool": "V3", "verdict": "FAIL" if survivors else "PASS", "targets": targets,
                      "mutants": len(results), "killed": killed, "survivors": survivors}, ensure_ascii=False))
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
