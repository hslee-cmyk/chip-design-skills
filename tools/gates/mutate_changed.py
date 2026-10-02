"""V3 뮤테이션 (05-role-separation design §10, 계획 N4.2 V3, DEC-39 자체 AST 변이기).

    $PY mutate_changed.py --root <격리 복제본 루트> --base <커밋> --head <커밋> --pytest-ini <캐시>/pytest_gate.ini
                          [--python <인터프리터>] [--timeout <초>] [--out <결과 jsonl>]

① 대상 = diff가 닿은 `def` 중 `ast.dump`(docstring 제외) 해시가 base와 다른 것. 새 def는 본문 전체, 기존 def는
   바뀐 문장·감싸는 제어문·바꾸거나 지운 문장 자리 바로 뒤 문장·같은 블록 뒤쪽(반복문 본문이면 그 본문 전체)에서
   바뀐 이름을 읽는 문장·def 머리 변경 몫·`early_return`(정의: spec card 20260930-v3-changed-stmt-scope 계약 1).
   대상 밖 변이는 실행하지 않고 수와 id만 출력한다(`not_targeted`, 판정 제외)
② 연산자: 비교 뒤집기, 산술 교체(`+↔-`, `*↔/`), 상수 변경(정수 ±1, 실수는 표기된 마지막 자릿수 한 단위 ±),
   문장 삭제, 조기 `return`, `except` 본문 삭제
③ 인벤토리 = 정적 호출 그래프(V7 `reachability.build_graph`)에서 그 함수에 도달하는 test 함수
④ 변이마다 `--head` 커밋의 격리 복제본(이력 포함, origin 없음)에서 그 test만(worktree는 바꾸지 않는다).
   인벤토리 기준 실행 실패 = ERROR(exit 2, 변이를 생존으로 세지 않는다)
⑤ 살아남은 변이가 있으면 FAIL. 변이 id = `<모듈>:<함수 qualname>:<연산자>:<AST 노드 경로>`.
   등가 변이 면제는 `target_kind: decision`, `target` 원소 = `<변이 id>@<묶기 해시>`인 승인 기록(head 트리) --
   head의 그 def 묶기 해시(`bind_hash`: docstring·데코레이터 포함 def 노드 원본의 `ast.dump` sha256)가 같을 때만
   적용한다. 해시가 없거나 다르거나 형식이 틀린 원소는 적용하지 않고 출력 `exempt_ignored`에 싣는다.
판정 JSON 한 줄, exit 0 PASS / 1 FAIL / 2 실행 오류. 변이마다 결과를 --out에 append(WP-11).
"""
from __future__ import annotations

import ast
import copy
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import merge_gate as mg
import reachability as rch

TESTS_PREFIX = "skills/analog-gmid-design/assets/tests/"
TESTS_TOOLS = "skills/analog-gmid-design/assets/tests/tools/"
CONFTEST_REL = TESTS_PREFIX + "conftest.py"


class BaselineFailed(RuntimeError):
    """변이 전 기준 실행에서 인벤토리 test가 통과하지 않았다(B28: 생존이 아니라 ERROR)."""

    def __init__(self, tests, code):
        RuntimeError.__init__(self, "기준 실행 실패(exit %s): %s" % (code, ", ".join(tests)))
        self.tests = list(tests)
        self.code = code


def _run_git(args):
    r = subprocess.run(["git"] + args, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError("git %s 실패(exit %d): %s" % (args[0] if args[0] != "-C" else args[2], r.returncode,
                                                         r.stderr.decode("utf-8", "replace").strip()))


def make_clone(root, work, head):
    """`--head` 커밋의 격리 복제본(이력 포함, origin 없음). 하드링크 없음."""
    _run_git(["clone", "--quiet", "--no-checkout", "--no-hardlinks", "--no-local", "-c", "core.longpaths=true",
              root, work])
    _run_git(["-C", work, "remote", "remove", "origin"])
    _run_git(["-C", work, "checkout", "--quiet", "--detach", head])


def _rmtree_force(path):
    """읽기 전용 파일(git pack)까지 지운다: 실패하면 쓰기 권한을 풀고 재시도."""
    import stat

    def onexc(func, p, exc):
        try:
            os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
            func(p)
        except OSError:
            pass
    shutil.rmtree(path, onexc=onexc)


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


def bind_hash(fn):
    """면제 묶기 해시: 변이 경로를 정하는 바로 그 노드(docstring·데코레이터·중첩 def 포함)의 ast.dump sha256.
    `def_hash`(① 대상 선택, docstring 제외)와 다르다. 인자는 판마다 기본값이 바뀌어도 같도록 모두 명시한다."""
    return hashlib.sha256(ast.dump(fn, annotate_fields=True, include_attributes=False, indent=None,
                                   show_empty=False).encode("utf-8")).hexdigest()


_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def approved_index(approved):
    """승인 원소 집합 -> {id: [(원소 문자열, 종류, 해시)...]} (원소 문자열 오름차순). 종류 = bound|unbound|malformed."""
    idx = {}
    for el in sorted(set(e.strip() for e in approved)):
        if "@" not in el:
            mid, kind, h = el, "unbound", None
        else:
            parts = el.split("@")
            mid = parts[0]
            if len(parts) == 2 and _HASH_RE.match(parts[1]):
                kind, h = "bound", parts[1]
            else:
                kind, h = "malformed", None
        idx.setdefault(mid, []).append((el, kind, h))
    return idx


def exempt_decision(mid, head_hash, index):
    """변이 하나의 면제 판정 -> (exempt 레코드 | None, exempt_ignored 항목 목록)."""
    elems = index.get(mid)
    if not elems:
        return None, []
    for _el, kind, h in elems:
        if kind == "bound" and h == head_hash:
            return {"id": mid, "result": "exempt", "bind_hash": head_hash}, []
    ignored = []
    for el, kind, h in elems:
        if kind == "bound":
            ignored.append({"id": mid, "reason": "hash_mismatch", "approved_hash": h, "head_hash": head_hash})
        elif kind == "unbound":
            ignored.append({"id": mid, "reason": "unbound"})
        else:
            ignored.append({"id": mid, "reason": "malformed", "element": el})
    return None, ignored


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
    """소스에서 fn의 줄 범위(첫 데코레이터 줄부터 end_lineno)를 new_fn(데코레이터 포함)의 unparse로 바꾼다."""
    lines = src.split("\n")
    start = min([fn.lineno] + [d.lineno for d in fn.decorator_list]) - 1
    end = fn.end_lineno
    ind = len(lines[start]) - len(lines[start].lstrip())
    nf = copy.deepcopy(new_fn)
    text = ast.unparse(ast.fix_missing_locations(nf))
    new = [(" " * ind + l) if l.strip() else l for l in text.split("\n")]
    return "\n".join(lines[:start] + new + lines[end:])


# ---------------------------------------------------------------- 대상 분류(spec card 20260930-v3-changed-stmt-scope 계약 1)
_BLOCKS = ("body", "orelse", "finalbody", "handlers", "cases")
_LOOPS = (ast.For, ast.AsyncFor, ast.While)


def _blk(n, f):
    v = getattr(n, f, None)
    return v if isinstance(v, list) else []


def _is_compound(n):
    return any(_blk(n, f) for f in _BLOCKS)


def _field(comp):
    return comp.split("[", 1)[0]


def _elem_path(owner_path, field, i):
    return "%s.%s[%d]" % (owner_path, field, i) if owner_path else "%s[%d]" % (field, i)


def _prefixes(path):
    """경로의 비지 않은 누적 접두(`body[2].orelse[0]` -> `body[2]`, `body[2].orelse[0]`)."""
    comps = path.split(".") if path else []
    return [".".join(comps[:k]) for k in range(1, len(comps) + 1)]


def _lead_name(n):
    """`self.x`·`d[k]`·`out.append`의 맨 앞 Name id(없으면 None)."""
    while isinstance(n, (ast.Attribute, ast.Subscript)):
        n = n.value
    return n.id if isinstance(n, ast.Name) else None


def _scan_roots(n):
    """복합문은 자기 필드(블록 필드 밖), 단순문은 부분 트리 전체."""
    if not _is_compound(n):
        return [n]
    roots = []
    for f, v in ast.iter_fields(n):
        if f in _BLOCKS:
            continue
        if isinstance(v, list):
            roots.extend(x for x in v if isinstance(x, ast.AST))
        elif isinstance(v, ast.AST):
            roots.append(v)
    return roots


def _reads(n):
    """문장 n이 읽는 이름(단순문은 부분 트리, 복합문은 자기 필드의 `Name(Load)`)."""
    out = set()
    for r in _scan_roots(n):
        for x in ast.walk(r):
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
                out.add(x.id)
    return out


def _writes(roots, extra_handler=None):
    """바꾸는 이름 ⓐ~ⓓ(계약 1 용어). `roots` = 훑을 노드들, `extra_handler` = 자기 필드만 훑는 except 절."""
    out = set()
    if isinstance(extra_handler, ast.ExceptHandler) and extra_handler.name:
        out.add(extra_handler.name)
    for r in roots:
        for x in ast.walk(r):
            if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del)):
                out.add(x.id)
            elif isinstance(x, (ast.Attribute, ast.Subscript)) and isinstance(x.ctx, (ast.Store, ast.Del)):
                nm = _lead_name(x.value)
                if nm:
                    out.add(nm)
            elif isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute):
                nm = _lead_name(x.func.value)
                if nm:
                    out.add(nm)
            elif isinstance(x, ast.ExceptHandler) and x.name:
                out.add(x.name)
    return out


def _params(fn):
    """매개변수 이름 -> (종류, 위치, 기본값 지문, 주석 지문). 위치 전용·일반은 이은 위치 인자 순번, 키워드 전용은 그 목록 안 순번."""
    a = fn.args
    d = lambda x: ast.dump(x, include_attributes=False) if x is not None else None
    out = {}
    pos = list(a.posonlyargs) + list(a.args)
    defaults = [None] * (len(pos) - len(a.defaults)) + list(a.defaults)
    npo = len(a.posonlyargs)
    for i, (p, df) in enumerate(zip(pos, defaults)):
        out[p.arg] = ("posonly" if i < npo else "arg", i, d(df), d(p.annotation))
    if a.vararg:
        out[a.vararg.arg] = ("vararg", 0, None, d(a.vararg.annotation))
    for i, (p, df) in enumerate(zip(a.kwonlyargs, a.kw_defaults)):
        out[p.arg] = ("kwonly", i, d(df), d(p.annotation))
    if a.kwarg:
        out[a.kwarg.arg] = ("kwarg", 0, None, d(a.kwarg.annotation))
    return out


class _Scope:
    """해시가 바뀐 기존 def 하나의 대상 변이 판정(def마다 한 번 만든다 -- 변이 루프 안에서 다시 맞추지 않는다)."""

    def __init__(self, base_fn, head_fn):
        self.full = set()      # 부분 트리 전체가 대상인 문장 경로(새 문장, 대상 단순문)
        self.shared = set()    # 몫만 대상인 복합문 경로(자기 필드·자기 stmt_delete·except_body_delete)
        self.deleted = 0
        self._fp_cache = {}
        self._events = []
        self.header_changed = self._head_fp(base_fn) != self._head_fp(head_fn)
        self.root_self = self.header_changed
        self._match(base_fn.body, head_fn.body, "", "body", head_fn)
        self._select(head_fn, base_fn)

    # -- 지문
    def _fp(self, n):
        k = id(n)
        if k not in self._fp_cache:
            self._fp_cache[k] = ast.dump(n, include_attributes=False)
        return self._fp_cache[k]

    @staticmethod
    def _head_fp(n):
        c = copy.copy(n)
        for f in _BLOCKS:
            if isinstance(getattr(c, f, None), list):
                setattr(c, f, [])
        return ast.dump(c, include_attributes=False)

    # -- 맞춤
    def _match(self, base_list, head_list, owner_path, field, owner):
        if not base_list and not head_list:
            return
        sm = difflib.SequenceMatcher(None, [self._fp(x) for x in base_list], [self._fp(x) for x in head_list],
                                     autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            if tag == "insert":
                for j in range(j1, j2):
                    self._events.append(("new", owner_path, field, head_list, j, head_list[j], None, owner))
            elif tag == "delete":
                for i in range(i1, i2):
                    self._del(owner_path, field, head_list, j1, base_list[i], owner)
            else:
                free = list(range(i1, i2))
                for j in range(j1, j2):
                    h = head_list[j]
                    pair = None
                    if _is_compound(h):
                        cands = [i for i in free if type(base_list[i]) is type(h) and _is_compound(base_list[i])]
                        hh = self._head_fp(h)
                        same = [i for i in cands if self._head_fp(base_list[i]) == hh]
                        pair = same[0] if same else (cands[0] if cands else None)
                    if pair is None:
                        self._events.append(("new", owner_path, field, head_list, j, h, None, owner))
                        continue
                    free.remove(pair)
                    b = base_list[pair]
                    hp = _elem_path(owner_path, field, j)
                    if self._head_fp(b) != self._head_fp(h):
                        self._events.append(("hdr", owner_path, field, head_list, j, h, b, owner))
                    for f in _BLOCKS:
                        self._match(_blk(b, f), _blk(h, f), hp, f, h)
                for i in free:
                    self._del(owner_path, field, head_list, j2, base_list[i], owner)

    def _del(self, owner_path, field, head_list, j, base_node, owner):
        self.deleted += 1
        self._events.append(("del", owner_path, field, head_list, j, None, base_node, owner))

    # -- 대상 집합 만들기(T1~T4, T6)
    def _add_share(self, path, node):
        (self.shared if _is_compound(node) else self.full).add(path)

    def _select(self, head_fn, base_fn):
        reads_cache = {}

        def reads(n):
            k = id(n)
            if k not in reads_cache:
                reads_cache[k] = _reads(n)
            return reads_cache[k]

        for kind, owner_path, field, lst, j, h, b, owner in self._events:
            # T4: 영역(또는 삭제 지점)을 감싸는 모든 복합문 -- 대상 def 자신은 뺀다
            for p in _prefixes(owner_path):
                self.shared.add(p)
            loop_body = isinstance(owner, _LOOPS) and field == "body"
            if kind == "new":
                self.full.add(_elem_path(owner_path, field, j))               # T1
                names = _writes([h])
                after = j + 1
            elif kind == "hdr":
                self.shared.add(_elem_path(owner_path, field, j))             # T2
                names = _writes(_scan_roots(h) + _scan_roots(b), extra_handler=None)
                for x in (h, b):
                    if isinstance(x, ast.ExceptHandler) and x.name:
                        names.add(x.name)
                after = j + 1
            else:
                if j < len(lst):                                              # T6 (가)
                    self._add_share(_elem_path(owner_path, field, j), lst[j])
                names = _writes([b])
                after = j
            if not names:
                continue
            for k, s in enumerate(lst):                                       # T6 (나)
                if kind != "del" and k == j:
                    continue
                if not loop_body and k < after:
                    continue
                if reads(s) & names:
                    self._add_share(_elem_path(owner_path, field, k), s)
        if self.header_changed:                                               # T3
            changed = set()
            bp, hp = _params(base_fn), _params(head_fn)
            for nm in set(bp) | set(hp):
                if bp.get(nm) != hp.get(nm):
                    changed.add(nm)
            if changed:
                def walk(node, path):
                    for f in _BLOCKS:
                        for i, e in enumerate(_blk(node, f)):
                            ep = _elem_path(path, f, i)
                            if reads(e) & changed:
                                self._add_share(ep, e)
                            walk(e, ep)
                walk(head_fn, "")

    def targets(self, opname, npath):
        """변이 (연산자, 경로)가 대상인가."""
        if opname == "early_return":                                          # T5
            return True
        node_path = re.sub(r"\.ops\[\d+\]$", "", npath) if opname == "cmp_flip" else npath
        comps = node_path.split(".") if node_path else []
        if self.root_self and comps and _field(comps[0]) not in _BLOCKS:     # T3 def 자기 필드
            return True
        for k in range(1, len(comps) + 1):
            pre = ".".join(comps[:k])
            if pre in self.full:
                return True
            if pre in self.shared:
                rest = comps[k:]
                if not rest:
                    if opname in ("stmt_delete", "except_body_delete"):
                        return True
                elif _field(rest[0]) not in _BLOCKS:
                    return True
        return False


def test_nodeid(nid):
    p, q = nid.split("::", 1)
    return p + "::" + q.replace(".", "::")


def inventory(graph_edges, target, test_nodes):
    return sorted(t for t in test_nodes if target in rch.reach(graph_edges, [t]))


def _approved(root, rev):
    return rch._approved_ids(root, rev)


def _dotted(node):
    """`pytest.mark.gmid_ic` 같은 점 이어진 이름(`test_ic_markers_match_plan.py`와 같은 읽기 방식)."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _gmid_ic_calls(func_def):
    """함수 데코레이터 식 안의 모든 `pytest.mark.gmid_ic(...)` 호출(parametrize의 pytest.param marks 포함)."""
    out = []
    for deco in func_def.decorator_list:
        for node in ast.walk(deco):
            if isinstance(node, ast.Call) and _dotted(node.func) == "pytest.mark.gmid_ic":
                out.append(node)
    return out


def _marker_ic_case(call, phase):
    """(ic, case) -- 표식 phase가 주어진 phase와 같을 때만(문자열 상수가 아니면 None)."""
    ic = call.args[0].value if (len(call.args) == 1 and isinstance(call.args[0], ast.Constant)
                                and isinstance(call.args[0].value, str)) else None
    mphase = case = None
    for kw in call.keywords:
        if kw.arg == "phase" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            mphase = kw.value.value
        if kw.arg == "case" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            case = kw.value.value
    if ic is None or case is None or mphase != phase:
        return None
    return ic, case


def _strict_keys(raw):
    """`00-common` §8.1: 값 없는 `--gmid-strict=`는 키가 없는 것이다."""
    if not raw:
        return set()
    return set(raw.split(","))


def inventory_gmid_keys(work, inv, phase):
    """인벤토리 test 함수의 `gmid_ic` 표식(데코레이터·`pytest.param(..., marks=...)`) 중 표식 phase가
    이번 Phase와 같은 것의 `<IC>:<case>` 키 집합(design `10-test-separation` §6.10, C6 대조 test와 같은 AST 읽기)."""
    by_file = {}
    for t in inv:
        path, qual = t.split("::", 1)
        by_file.setdefault(path, set()).add(qual)
    keys = set()
    for path, quals in by_file.items():
        fpath = os.path.join(work, *path.split("/"))
        try:
            with open(fpath, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        defmap = dict(rch.iter_defs(tree))
        for q in quals:
            fn = defmap.get(q)
            if fn is None:
                continue
            for call in _gmid_ic_calls(fn):
                pair = _marker_ic_case(call, phase)
                if pair is not None:
                    keys.add("%s:%s" % pair)
    return keys


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
    ap.add_argument("--gmid-phase", default=None, dest="gmid_phase",
                    help="V1과 같은 값(`00-common` §9.3). conftest가 옵션을 모르면 전달하지 않는다.")
    ap.add_argument("--gmid-strict", default=None, dest="gmid_strict",
                    help="V1 엄격 집합(`<IC>:<case>,...`). 인벤토리 test에 표식이 있는 키만 pytest에 넘긴다.")
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
        approved_idx = approved_index(_approved(root, ns.head))
        tmp = tempfile.mkdtemp(prefix="gmid-v3-")
        work = os.path.join(tmp, "copy")
        make_clone(root, work, ns.head)
        pyc = os.path.join(tmp, "pycache")
        os.makedirs(pyc)
        survivors, killed, results = [], 0, []
        survivor_bindings, exempt_ignored = [], []
        not_targeted_n, targets_by_def = 0, {}
        baseline_ok = {}
        strict_for_inv = {}
        # C11(design §6.10): conftest가 --gmid-phase를 모르면(C6 전 모양) 옵션을 넘기지 않는다 -- merge gate
        # 'CC-3 병합 전 판정식'과 같은 판정(conftest_has_gmid_phase, §9.2-7).
        try:
            with open(os.path.join(work, *CONFTEST_REL.split("/")), "rb") as fh:
                conftest_bytes = fh.read()
        except OSError:
            conftest_bytes = None
        gmid_supported = ns.gmid_phase is not None and mg.conftest_has_gmid_phase(conftest_bytes)
        gmid_strict_v1 = _strict_keys(ns.gmid_strict)

        def gmid_extra_args(inv):
            if not gmid_supported:
                return []
            key = tuple(inv)
            if key not in strict_for_inv:
                strict_for_inv[key] = sorted(gmid_strict_v1 & inventory_gmid_keys(work, inv, ns.gmid_phase))
            return ["--gmid-phase=%s" % ns.gmid_phase, "--gmid-strict=%s" % ",".join(strict_for_inv[key])]

        def run_tests(inv):
            env = dict(os.environ, PYTHONPYCACHEPREFIX=pyc, PYTHONDONTWRITEBYTECODE="1")
            cmd = [ns.python, "-P", "-m", "pytest", "-c", ns.pytest_ini, "--rootdir=" + work,
                   "--confcutdir=" + work, "-x", "-q", "-p", "no:cacheprovider"] + gmid_extra_args(inv) + \
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
            base_defs = {}
            if base_src is not None:
                try:
                    base_defs = dict(rch.iter_defs(ast.parse(base_src)))
                except SyntaxError:
                    base_defs = {}
            modname = rch.module_name(path)
            fpath = os.path.join(work, *path.split("/"))
            for q, fn in changed_defs(base_src, head_src):
                inv = inventory(edges, "%s::%s" % (path, q), test_nodes)
                if inv and tuple(inv) not in baseline_ok:
                    # 변이 전 기준 실행: 인벤토리 test가 변이 없는 코드에서 통과해야 '죽인 변이'가 뜻이 있다
                    # (기준에서 이미 실패하면 모든 변이가 죽은 것으로 보여 거짓 PASS가 된다 -- WP-02)
                    base_code = run_tests(inv)
                    if base_code != 0:
                        raise BaselineFailed(inv, base_code)
                    baseline_ok[tuple(inv)] = True
                fn_bind = bind_hash(fn)   # def마다 한 번
                # 대상 분류도 def마다 한 번(새 def = 본문 전체). 맞추는 트리는 head·base def 노드 원본(docstring 포함)
                scope = _Scope(base_defs[q], fn) if q in base_defs else None
                stat = {"targeted": 0, "not_targeted": 0, "deleted_statements": scope.deleted if scope else 0,
                        "def_header_changed": scope.header_changed if scope else False}
                targets_by_def["%s::%s" % (path, q)] = stat
                for opname, npath, mfn in mutants(fn, head_src):
                    mid = "%s:%s:%s:%s" % (modname, q, opname, npath)
                    if scope is not None and not scope.targets(opname, npath):
                        # 대상 밖: 실행·면제 판정·인벤토리 생존 판정 없이 수와 id만 남긴다
                        not_targeted_n += 1
                        stat["not_targeted"] += 1
                        if ns.out:
                            with open(ns.out, "a", encoding="utf-8") as fh:
                                fh.write(json.dumps({"id": mid, "result": "not_targeted"}, ensure_ascii=False) + "\n")
                        continue
                    stat["targeted"] += 1
                    ex_rec, ignored = exempt_decision(mid, fn_bind, approved_idx)
                    exempt_ignored.extend(ignored)
                    if ex_rec is not None:
                        results.append(ex_rec)
                        if ns.out:
                            with open(ns.out, "a", encoding="utf-8") as fh:
                                fh.write(json.dumps(ex_rec, ensure_ascii=False) + "\n")
                        continue
                    if not inv:
                        survivors.append(mid)
                        survivor_bindings.append("%s@%s" % (mid, fn_bind))
                        rec = {"id": mid, "result": "survived", "reason": "인벤토리 없음(도달하는 test 없음)"}
                    else:
                        with open(fpath, "w", encoding="utf-8", newline="\n") as fh:
                            fh.write(_replace_def(head_src, fn, mfn))
                        code = run_tests(inv)
                        with open(fpath, "w", encoding="utf-8", newline="\n") as fh:
                            fh.write(head_src)
                        if code == 0:
                            survivors.append(mid)
                            survivor_bindings.append("%s@%s" % (mid, fn_bind))
                            rec = {"id": mid, "result": "survived", "tests": inv}
                        else:
                            killed += 1
                            rec = {"id": mid, "result": "killed", "exit": code}
                    results.append(rec)
                    if ns.out:
                        with open(ns.out, "a", encoding="utf-8") as fh:
                            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except BaselineFailed as e:
        print(json.dumps({"tool": "V3", "verdict": "ERROR", "error": "%s: %s" % (type(e).__name__, e),
                          "baseline_failed": e.tests}, ensure_ascii=False))
        return 2
    except (OSError, RuntimeError, SyntaxError, ValueError, UnicodeDecodeError) as e:
        print(json.dumps({"tool": "V3", "verdict": "ERROR", "error": "%s: %s" % (type(e).__name__, e)}, ensure_ascii=False))
        return 2
    finally:
        if tmp:
            _rmtree_force(tmp)
    print(json.dumps({"tool": "V3", "verdict": "FAIL" if survivors else "PASS", "targets": targets,
                      "mutants": len(results), "killed": killed, "survivors": survivors,
                      "survivor_bindings": survivor_bindings, "exempt_ignored": exempt_ignored,
                      "not_targeted": not_targeted_n, "targets_by_def": targets_by_def},
                     ensure_ascii=False))
    return 1 if survivors else 0


if __name__ == "__main__":
    # 로캘·PYTHONIOENCODING과 무관하게 출력을 UTF-8로(spec card 20260921-gate-output-utf8).
    # Python 3.14는 항상 reconfigure를 제공한다(V6, spec card 20260921-gate-flow-liveness 계약 6).
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
