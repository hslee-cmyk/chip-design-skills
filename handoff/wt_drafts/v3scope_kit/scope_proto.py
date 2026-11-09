"""V3 범위 정책 card 20260930-v3-changed-stmt-scope 계약 1(T1~T6, 넓힌 T6) 독립 프로토타입.

spec card '관찰 가능한 계약' 용어·계약 1 문장만 보고 새로 썼다(_drafts/v3_scripts·b26_scripts의 분류기 v3_scope_classify/v3_scope_widen을
import하지도 복사하지도 않는다 -- 결과를 그 분류기와 대조하려고). 도구 mutate_changed의 `mutants`(변이 경로 생성)만 쓴다.

select(base_fn, head_fn, muts, variant) -> [bool]  (muts = mutate_changed.mutants(head_fn, src)의 (op, path, _) 순서 그대로)
  variant "N2w" = 이 card 규칙(T1·T2·T3(b)·T4·T5·T6 가·나)
  variant "N2b" = 승인 당시 정의(T6 가만) -- 비교용
설정 가능한 해석(card 문장이 정하지 않은 자리 -- 착수 키트 §모호점):
  NEW_COMPOUND_NAMES: 새·지운 '복합문' R이 바꾸는 이름을 어디서 모으나 -- "subtree"(부분 트리 전체, 기본) | "own"(자기 필드만)
  PARAM_POS: 바뀐 매개변수의 '위치' -- "kind_index"(기본: 위치 전용·일반은 둘을 이은 위치 인자 순번, 키워드 전용은 그 목록 안 순번,
             *args·**kw는 0 -- review3 S1로 고침) | "flat_index"(시그니처 전체 순번)
"""
from __future__ import annotations

import ast
import difflib
import re

BLOCK = ("body", "orelse", "finalbody", "handlers", "cases")
LOOPS = (ast.For, ast.AsyncFor, ast.While)
NEW_COMPOUND_NAMES = "subtree"
PARAM_POS = "kind_index"


def fp(n):
    return ast.dump(n, include_attributes=False)


def head_fp(n):
    """블록 필드를 빈 목록으로 바꾼 노드의 지문(얕은 복사 -- 원본 불변)."""
    kw = {}
    for f, v in ast.iter_fields(n):
        kw[f] = [] if (f in BLOCK and isinstance(v, list)) else v
    return ast.dump(type(n)(**kw), include_attributes=False)


def is_compound(n):
    if isinstance(n, (ast.ExceptHandler, ast.match_case)):
        return True
    for f in BLOCK:
        v = getattr(n, f, None)
        if isinstance(v, list) and any(isinstance(x, (ast.stmt, ast.ExceptHandler, ast.match_case)) for x in v):
            return True
    return False


def own_roots(n):
    """복합문의 자기 필드(블록 필드 밖) 하위 노드들."""
    out = []
    for f, v in ast.iter_fields(n):
        if f in BLOCK:
            continue
        if isinstance(v, list):
            out += [x for x in v if isinstance(x, ast.AST)]
        elif isinstance(v, ast.AST):
            out.append(v)
    return out


def _walk_roots(roots):
    for r in roots:
        yield from ast.walk(r)


def scope_roots(n):
    """'읽는다'·몫의 범위: 단순문은 자기 자신 전체, 복합문은 자기 필드."""
    return own_roots(n) if is_compound(n) else [n]


def reads(n, names):
    if not names:
        return False
    return any(isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load) and x.id in names for x in _walk_roots(scope_roots(n)))


def _leftmost(x):
    while isinstance(x, (ast.Attribute, ast.Subscript, ast.Call, ast.Starred)):
        x = x.func if isinstance(x, ast.Call) else x.value
    return x.id if isinstance(x, ast.Name) else None


def modified_names(roots, handler=None):
    out = set()
    for x in _walk_roots(roots):
        if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del)):
            out.add(x.id)                                                       # ⓐ
        elif isinstance(x, (ast.Attribute, ast.Subscript)) and isinstance(x.ctx, (ast.Store, ast.Del)):
            r = _leftmost(x.value)                                              # ⓑ
            if r:
                out.add(r)
        elif isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute):
            r = _leftmost(x.func.value)                                         # ⓒ
            if r:
                out.add(r)
    for x in _walk_roots(roots):
        if isinstance(x, ast.ExceptHandler) and x.name:
            out.add(x.name)                                                     # ⓓ (부분 트리 안의 except 절)
    if handler is not None and isinstance(handler, ast.ExceptHandler) and handler.name:
        out.add(handler.name)                                                   # ⓓ (R 자신)
    return out


def jp(owner, field, k):
    return "%s.%s[%d]" % (owner, field, k) if owner else "%s[%d]" % (field, k)


class Matcher:
    """base·head def의 블록 필드를 지문으로 맞춘다(계약 1 규범 알고리즘)."""

    def __init__(self):
        self.new = []          # head 경로(새 문장)
        self.hdr = []          # (head 경로, base 노드, head 노드) 머리 변경 복합문
        self.dels = []         # (owner 경로, field, j, base 노드) 지운 문장, j = 삭제 지점
        self.sites = []        # (owner 경로, field, kind, j, R names) -- T6 나

    def block(self, bl, hl, owner, field):
        a = [fp(x) for x in bl]
        b = [fp(x) for x in hl]
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if tag == "equal":
                continue
            if tag == "insert":
                for j in range(j1, j2):
                    self._new(owner, field, j, hl[j])
                continue
            if tag == "delete":
                for i in range(i1, i2):
                    self._del(owner, field, j1, bl[i])
                continue
            free = list(range(i1, i2))
            for j in range(j1, j2):
                h = hl[j]
                pick = None
                if is_compound(h):
                    hh = head_fp(h)
                    for i in free:
                        if type(bl[i]) is type(h) and is_compound(bl[i]) and head_fp(bl[i]) == hh:
                            pick = i
                            break
                    if pick is None:
                        for i in free:
                            if type(bl[i]) is type(h) and is_compound(bl[i]):
                                pick = i
                                break
                if pick is None:
                    self._new(owner, field, j, h)
                    continue
                free.remove(pick)
                bn = bl[pick]
                p = jp(owner, field, j)
                if head_fp(bn) != head_fp(h):
                    self.hdr.append((p, bn, h))
                    self.sites.append((owner, field, "hdr", j,
                                       modified_names(own_roots(bn), bn) | modified_names(own_roots(h), h)))
                for f in BLOCK:
                    bv, hv = getattr(bn, f, None), getattr(h, f, None)
                    if isinstance(bv, list) or isinstance(hv, list):
                        self.block(bv or [], hv or [], p, f)
            for i in free:
                self._del(owner, field, j2, bl[i])

    def _roots_for_names(self, n):
        if is_compound(n) and NEW_COMPOUND_NAMES == "own":
            return own_roots(n)
        return [n]

    def _new(self, owner, field, j, n):
        self.new.append(jp(owner, field, j))
        self.sites.append((owner, field, "new", j, modified_names(self._roots_for_names(n), n)))

    def _del(self, owner, field, j, n):
        self.dels.append((owner, field, j, n))
        self.sites.append((owner, field, "del", j, modified_names(self._roots_for_names(n), n)))


def def_header_fp(fn):
    return head_fp(fn)


def param_table(fn):
    a = fn.args
    out = {}
    pos = list(a.posonlyargs) + list(a.args)
    nd = len(a.defaults)
    flat = 0
    for k, x in enumerate(pos):
        kind = "posonly" if k < len(a.posonlyargs) else "pos"
        d = a.defaults[k - (len(pos) - nd)] if k >= len(pos) - nd else None
        ki = k      # 위치 전용·일반 매개변수는 둘을 이은 위치 인자 순번(review3 S1 -- 옛: 같은 종류 목록 안 순번)
        out[x.arg] = [kind, ki if PARAM_POS == "kind_index" else flat, fp(d) if d else None, fp(x.annotation) if x.annotation else None]
        flat += 1
    if a.vararg:
        out[a.vararg.arg] = ["vararg", 0 if PARAM_POS == "kind_index" else flat, None,
                             fp(a.vararg.annotation) if a.vararg.annotation else None]
        flat += 1
    for k, x in enumerate(a.kwonlyargs):
        d = a.kw_defaults[k]
        out[x.arg] = ["kwonly", k if PARAM_POS == "kind_index" else flat, fp(d) if d else None,
                      fp(x.annotation) if x.annotation else None]
        flat += 1
    if a.kwarg:
        out[a.kwarg.arg] = ["kwarg", 0 if PARAM_POS == "kind_index" else flat, None,
                            fp(a.kwarg.annotation) if a.kwarg.annotation else None]
    return out


def changed_params(bfn, hfn):
    b, h = param_table(bfn), param_table(hfn)
    return (set(b) ^ set(h)) | {n for n in set(b) & set(h) if b[n] != h[n]}


_PART = re.compile(r"([A-Za-z_]+)(?:\[(\d+)\])?")


def parts(p):
    return [(m.group(1), m.group(2)) for m in _PART.finditer(p)] if p else []


def under(np_, p):
    return np_ == p or np_.startswith(p + ".")


def in_own(np_, p):
    """np_가 복합문 p의 자기 필드 안인가."""
    if not np_.startswith(p + "."):
        return False
    first = parts(np_[len(p) + 1:])[0][0]
    return first not in BLOCK


def mut_node_path(op, path):
    return re.sub(r"\.ops\[\d+\]$", "", path) if op == "cmp_flip" else path


def stmt_index(fn):
    """def 안 모든 문장(블록 필드 원소)의 경로 -> 노드, 경로 -> 부모 경로 목록(조상 복합문)."""
    nodes, anc = {}, {}

    def rec(n, p, chain):
        for f in BLOCK:
            v = getattr(n, f, None)
            if not isinstance(v, list):
                continue
            for k, s in enumerate(v):
                if isinstance(s, (ast.stmt, ast.ExceptHandler, ast.match_case)):
                    q = jp(p, f, k)
                    nodes[q] = s
                    anc[q] = list(chain)
                    rec(s, q, chain + [q])
    rec(fn, "", [])
    return nodes, anc


def select(bfn, hfn, muts, variant="N2w"):
    M = Matcher()
    M.block(bfn.body, hfn.body, "", "body")
    nodes, anc = stmt_index(hfn)
    def_hdr = def_header_fp(bfn) != def_header_fp(hfn)
    cps = changed_params(bfn, hfn) if def_hdr else set()

    whole = set(M.new)                         # T1: 부분 트리 전체
    share = set(p for p, _b, _h in M.hdr)      # T2: 몫
    # T3
    if def_hdr and cps:
        for q, s in nodes.items():
            if reads(s, cps):
                (share if is_compound(s) else whole).add(q)
    # T6
    t6 = set()
    for owner, field, kind, j, names in M.sites:
        own_node = hfn if owner == "" else nodes[owner]
        lst = getattr(own_node, field, None) or []
        if kind == "del" and j < len(lst):
            t6.add(jp(owner, field, j))                                  # 가
        if variant == "N2w" and names:
            loop = field == "body" and isinstance(own_node, LOOPS)
            for k, s in enumerate(lst):
                if loop:
                    if kind != "del" and k == j:
                        continue
                elif (k <= j) if kind != "del" else (k < j):
                    continue
                if reads(s, names):
                    t6.add(jp(owner, field, k))                          # 나
    for q in t6:
        (share if is_compound(nodes[q]) else whole).add(q)
    # T4: T1·T2·T6 영역과 삭제 지점의 조상
    ancs = set()
    for q in set(M.new) | set(p for p, _b, _h in M.hdr) | t6:
        ancs.update(anc[q])
    for owner, field, j, _n in M.dels:
        if owner:
            ancs.add(owner)
            ancs.update(anc[owner])
    share |= ancs

    out = []
    for op, path, _ in muts:
        if op == "early_return":
            out.append(True)                                                  # T5
            continue
        np_ = mut_node_path(op, path)
        hit = False
        if not np_.startswith(BLOCK) and not np_.startswith("body"):
            hit = def_hdr                                                     # T3: def 자기 필드
        else:
            hit = any(under(np_, q) for q in whole)
            if not hit:
                for q in share:
                    s = nodes[q]
                    if in_own(np_, q) or (np_ == q and op == "stmt_delete") or \
                            (np_ == q and op == "except_body_delete" and isinstance(s, ast.ExceptHandler)):
                        hit = True
                        break
        out.append(hit)
    return out
