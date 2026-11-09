"""Phase 3 design v4 -- G1 이동 규칙(v4: M-0·M-0h·M-1~M-4 + 클래스 골격 + 문장 + def 중복 제외 + 해시 대조)의 참조 구현과
반례 재실행(읽기 전용). p3v3_g1_measure.py를 확장했다(2차 검토 review2_phase3_v3.md의 새 반례 전부 + D0a check 발견 모의).

이 파일은 **design 문장이 판정 가능한지 확인하는 초안 측정 스크립트**다. 게이트 코드가 아니고, G1 구현(code-author)이나
test 기대값(test-author)의 근거로 쓰지 않는다(작성자≠검증자). 결과는 이 파일 옆 p3v4_g1_results.json에 쓴다(WP-11).
케이스마다 결과를 누적 기록하므로 중간에 죽어도 앞 결과는 남는다(p3v4_g1_results.partial.jsonl).

    C:/Python314/python.exe -B p3v4_g1_measure.py

저장소는 읽기만 한다(`git ls-tree`/`show`, 게이트 모듈 import는 -B). 합성 git 저장소는 C:/g51 아래에 만들고 단계마다 지운다.

규칙 모드 두 가지(같은 입력에서 나란히 잰다):
* "v3" -- 초안 v3 규칙 그대로(p3v3_g1_measure.py와 같은 결과여야 한다 -- 회귀 확인).
* "v4" -- 2차 검토 반영: B1 (1) M-0h(목적 파일에서도 유일 바인딩) (2) p_b·p_h에 qualname이 둘 이상인 def는 defs에서 제외
  (3) V3·V7 제외는 (경로, qualname, def_hash)로; S1 (a) `global` 선언 이름 = ("global-dynamic", 경로, 이름)
  (b) ext·ext-module에 가져오는 파일의 디렉터리 (c) star import가 있는 모듈의 모든 이름 = star; S2 바인딩 = 모듈 공간 Store/Del 전부
  (+ except as·match 포획), 문장 단위 전역 읽기 = 유효 범위 규칙(lambda·컴프리헨션 지역 제외); S3 `__future__` 집합이 다르면 M-4 거부.
D0a `check` 발견 모의(v4 문언): changed·lost·move-rejected·changed-def(S6)·stmt-order(m2)·future(S3)·rebind(S5).
"""
import ast
import builtins
import collections
import copy
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import symtable
import time

R = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills"
G = os.path.join(R, "tools", "gates")
PY = sys.executable
SCR = "C:/g51"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "p3v4_g1_results.json")
PARTIAL = os.path.join(HERE, "p3v4_g1_results.partial.jsonl")
V3RES = os.path.join(HERE, "p3v3_g1_results.json")
sys.path.insert(0, G)
import mutate_changed as mc   # noqa: E402
import reachability as rch    # noqa: E402
import source_lint as sl      # noqa: E402

AS = "skills/analog-gmid-design/assets/"
res = {"head": subprocess.run(["git", "-C", R, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()}
if os.path.exists(PARTIAL):
    os.remove(PARTIAL)


def _partial(rec):
    with open(PARTIAL, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


# =============================================================================================== 참조 규칙
MODULE_IDENTITY = {"__name__", "__spec__", "__loader__", "__package__", "__path__", "__cached__", "__builtins__",
                   "__dict__", "__doc__", "__annotations__"}
MODULE_INTROSPECTION_BUILTINS = {"globals", "eval", "exec"}
BUILTINS = set(dir(builtins))
MODE = "v4"
COMPS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


class _Skel(ast.NodeTransformer):
    """클래스 골격: 클래스 안의 def(메서드, 중첩 클래스의 메서드 포함)를 이름 표지로 바꾼다. 함수 안으로는 내려가지 않는다."""

    def visit_FunctionDef(self, n):
        return ast.Expr(ast.Name(id="<method %s>" % n.name, ctx=ast.Load()))

    visit_AsyncFunctionDef = visit_FunctionDef


def skel_hash(cls):
    return mc.def_hash(_Skel().visit(copy.deepcopy(cls)))


def stmt_hash(node):
    return mc.def_hash(node)  # _strip_doc는 Module/def/class 몸체만 건드린다 -- 문장은 ast.dump 그대로


def _bound_names_v3(stmt):
    out = set()
    for n in ast.walk(stmt):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            out.add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
    return out


def _bound_names_v4(stmt):
    """S2: 모듈 공간(def·class·lambda·컴프리헨션 몸체 밖)에서 Store/Del 문맥인 이름 + def·class 이름 + except as·match 포획
    + import(블록 안) + 컴프리헨션 안 walrus(바깥 유효 범위에 묶인다) + type 별칭."""
    out = set()

    def visit(n, in_comp=False):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
            # 데코레이터·기본값·기반은 모듈 공간에서 평가되지만 바인딩(walrus)은 드물다 -- 그래도 방문
            for d in n.decorator_list:
                visit(d)
            return
        if isinstance(n, ast.Lambda):
            for d in n.args.defaults + [x for x in n.args.kw_defaults if x is not None]:
                visit(d)
            return
        if isinstance(n, COMPS):
            for ch in ast.iter_child_nodes(n):
                visit(ch, True)
            return
        if isinstance(n, ast.NamedExpr):
            out.add(n.target.id)
            visit(n.value, in_comp)
            return
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)) and not in_comp:
            out.add(n.id)
        if isinstance(n, ast.ExceptHandler) and n.name:
            out.add(n.name)
        if isinstance(n, (ast.MatchAs, ast.MatchStar)) and n.name:
            out.add(n.name)
        if isinstance(n, ast.MatchMapping) and n.rest:
            out.add(n.rest)
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                if a.name != "*":
                    out.add(a.asname or a.name.split(".")[0])
        if isinstance(n, (ast.Global, ast.Nonlocal)):
            pass
        for ch in ast.iter_child_nodes(n):
            visit(ch, in_comp)

    visit(stmt)
    return out


def _bound_names(stmt):
    return _bound_names_v4(stmt) if MODE == "v4" else _bound_names_v3(stmt)


class ModInfo:
    """한 파일의 최상위 단위와 바인딩(파일당 한 번 파싱)."""

    def __init__(self, path, src):
        self.path, self.src = path, src
        self.tree = ast.parse(src)
        self.units = []           # (kind, key, hash, node, bound_names)
        self.bindings = {}        # name -> list of binding descriptors
        self._st = None
        self.futures = frozenset(a.name for n in self.tree.body if isinstance(n, ast.ImportFrom) and n.module == "__future__"
                                 for a in n.names)
        self.global_declared = frozenset(nm for n in ast.walk(self.tree) if isinstance(n, ast.Global) for nm in n.names)
        for n in self.tree.body:
            if rch._is_main_block(n):
                continue
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.units.append(("def", n.name, mc.def_hash(n), n, {n.name}))
            elif isinstance(n, ast.ClassDef):
                self.units.append(("class", n.name, skel_hash(n), n, {n.name}))
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                pass
            else:
                self.units.append(("stmt", None, stmt_hash(n), n, _bound_names(n)))
        self._collect(self.tree.body)
        self._qcount = None

    def qcount(self):
        if self._qcount is None:
            self._qcount = collections.Counter(q for q, _ in rch.iter_defs(self.tree))
        return self._qcount

    def _collect(self, body):
        for n in body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.bindings.setdefault(n.name, []).append(("bind",))
            elif isinstance(n, ast.ImportFrom):
                for a in n.names:
                    if a.name == "*":
                        self.bindings.setdefault("*", []).append(("star", n.module, n.level))
                    else:
                        self.bindings.setdefault(a.asname or a.name, []).append(("from", n.module or "", n.level, a.name))
            elif isinstance(n, ast.Import):
                for a in n.names:
                    if a.asname:
                        self.bindings.setdefault(a.asname, []).append(("import", a.name))
                    else:
                        self.bindings.setdefault(a.name.split(".")[0], []).append(("import", a.name.split(".")[0]))
            elif isinstance(n, (ast.If, ast.Try, ast.With, ast.For, ast.While)) and not rch._is_main_block(n):
                # 블록 안의 바인딩은 블록 몸체를 재귀로(조건부 바인딩 -- 여러 바인딩이면 'multi')
                sub = []
                for f in ("body", "orelse", "finalbody"):
                    sub += getattr(n, f, []) or []
                for h in getattr(n, "handlers", []) or []:
                    sub += h.body
                    if MODE == "v4" and h.name:
                        self.bindings.setdefault(h.name, []).append(("bind",))
                if isinstance(n, (ast.For, ast.With)):
                    tgt = n.target if isinstance(n, ast.For) else None
                    names = set()
                    if tgt is not None:
                        names |= {x.id for x in ast.walk(tgt) if isinstance(x, ast.Name)}
                    if isinstance(n, ast.With):
                        for it in n.items:
                            if it.optional_vars is not None:
                                names |= {x.id for x in ast.walk(it.optional_vars) if isinstance(x, ast.Name)}
                    for nm in names:
                        self.bindings.setdefault(nm, []).append(("bind",))
                if MODE == "v4":
                    # 조건식·반복 대상 식 안의 walrus
                    for e in [getattr(n, "test", None), getattr(n, "iter", None)] + [it.context_expr for it in getattr(n, "items", []) or []]:
                        if e is not None:
                            for nm in _bound_names(ast.Expr(e)):
                                self.bindings.setdefault(nm, []).append(("bind",))
                self._collect(sub)
            else:
                for nm in _bound_names(n):
                    self.bindings.setdefault(nm, []).append(("bind",))

    def symtab(self):
        if self._st is None:
            self._st = symtable.symtable(self.src, self.path, "exec")
        return self._st


def _dir(path):
    return path.rsplit("/", 1)[0] if "/" in path else ""


def _module_file(tree_infos, from_path, modname, level):
    """`from <modname> import` 가 가리키는 트리 안 파일(같은 디렉터리의 <modname>.py). 없으면 None."""
    if level or not modname:
        return None
    d = _dir(from_path)
    last = modname.split(".")[-1]
    cand = (d + "/" if d else "") + last + ".py"
    return cand if cand in tree_infos else None


def canon(infos, path, name, depth=0):
    """이름 name이 모듈 path 최상위에서 가리키는 정의의 정규 출처(= G1 binding_origin)."""
    if depth > 20:
        return ("cycle", path, name)
    if name == "__file__":
        return ("file-dir", _dir(path))
    if name in MODULE_IDENTITY:
        return ("module-identity", path)
    info = infos.get(path)
    if info is None:
        return ("unbound", name) if name not in BUILTINS else ("builtin", name)
    if MODE == "v4":
        if "*" in info.bindings:                  # S1 (c): star가 하나라도 있으면 모든 이름이 star
            return ("star", path, name)
        if name in info.global_declared:          # S1 (a): 어딘가에서 global로 쓰는 이름
            return ("global-dynamic", path, name)
    bs = info.bindings.get(name)
    if not bs:
        if MODE != "v4" and "*" in info.bindings:
            return ("star", path, name)
        if name in MODULE_INTROSPECTION_BUILTINS:
            return ("module-identity", path)
        return ("builtin", name) if name in BUILTINS else ("unbound", name)
    if len(bs) > 1:
        return ("multi", path, name)
    b = bs[0]
    if b[0] == "bind":
        return ("def", path, name)
    if b[0] == "from":
        tgt = _module_file(infos, path, b[1], b[2])
        if tgt is None:
            if MODE == "v4":                      # S1 (b): 디렉터리 포함
                return ("ext", _dir(path), "." * b[2] + b[1], b[3])
            return ("ext", "." * b[2] + b[1], b[3])
        return canon(infos, tgt, b[3], depth + 1)
    if b[0] == "import":
        tgt = _module_file(infos, path, b[1], 0)
        if tgt:
            return ("module", tgt)
        return ("ext-module", _dir(path), b[1]) if MODE == "v4" else ("ext-module", b[1])
    return ("other", path, name)


def _names_in(exprs):
    out = set()
    for e in exprs:
        if e is None:
            continue
        for n in ast.walk(e):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                out.add(n.id)
    return out


def _free_loads(node, local=frozenset()):
    """S2: 문장의 모듈 전역 읽기 -- lambda 인자·컴프리헨션 대상·중첩 def 지역을 뺀 Load 이름(유효 범위 규칙 근사)."""
    out = set()

    def visit(n, loc):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            if n.id not in loc:
                out.add(n.id)
            return
        if isinstance(n, ast.Lambda):
            for d in n.args.defaults + [x for x in n.args.kw_defaults if x is not None]:
                visit(d, loc)
            a = n.args
            args = {x.arg for x in a.posonlyargs + a.args + a.kwonlyargs} | ({a.vararg.arg} if a.vararg else set()) | ({a.kwarg.arg} if a.kwarg else set())
            visit(n.body, loc | args)
            return
        if isinstance(n, COMPS):
            gens = n.generators
            visit(gens[0].iter, loc)              # 첫 iter는 바깥 유효 범위
            inner = set(loc)
            for i, g in enumerate(gens):
                inner |= {x.id for x in ast.walk(g.target) if isinstance(x, ast.Name)}
                if i:
                    visit(g.iter, frozenset(inner))
                for c in g.ifs:
                    visit(c, frozenset(inner))
            for e in ([n.key, n.value] if isinstance(n, ast.DictComp) else [n.elt]):
                visit(e, frozenset(inner))
            return
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = n.args
            for d in n.decorator_list + a.defaults + [x for x in a.kw_defaults if x is not None]:
                visit(d, loc)
            glob = {nm for x in ast.walk(n) if isinstance(x, ast.Global) for nm in x.names}
            args = {x.arg for x in a.posonlyargs + a.args + a.kwonlyargs} | ({a.vararg.arg} if a.vararg else set()) | ({a.kwarg.arg} if a.kwarg else set())
            stored = {x.id for x in ast.walk(n) if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del))}
            loc2 = frozenset((set(loc) | args | stored) - glob)
            for s in n.body:
                visit(s, loc2)
            return
        for ch in ast.iter_child_nodes(n):
            visit(ch, loc)

    visit(node, frozenset(local))
    return out


def _table_globals(t):
    out = set()
    for s in t.get_symbols():
        if s.is_global() and (s.is_referenced() or s.is_assigned()):
            out.add(s.get_name())
    for c in t.get_children():
        out |= _table_globals(c)
    return out


def global_reads(info, kind, node):
    """G(u): 단위 u가 모듈 전역 공간에서 읽거나 쓰는 이름(Python 유효 범위 규칙 = symtable) + 모듈 공간에서 평가되는
    데코레이터·기본값·주석·기반 클래스·키워드의 이름."""
    if kind == "stmt":
        return (_free_loads(node) | _annotation_names(node)) if MODE == "v4" else _names_in([node])
    out = set()
    mod = info.symtab()
    tabs = [c for c in mod.get_children() if c.get_name() == node.name]
    if len(tabs) != 1:
        tabs = [c for c in tabs if c.get_lineno() == node.lineno] or tabs
    for t in tabs:
        out |= _table_globals(t)
    if kind == "def":
        a = node.args
        out |= _names_in(node.decorator_list + a.defaults + [d for d in a.kw_defaults if d is not None]
                         + [x.annotation for x in a.posonlyargs + a.args + a.kwonlyargs if x.annotation is not None]
                         + [node.returns])
    else:
        out |= _names_in(node.decorator_list + node.bases + [k.value for k in node.keywords])
    out |= _annotation_names(node)
    return out


def _annotation_names(node):
    """u 안의 모든 주석(평가형·문자열형)의 식별자 -- 문자열 주석도 도입. 파싱 못 하는 문자열은 식별자 토큰으로."""
    anns = []
    for n in ast.walk(node):
        if isinstance(n, ast.arg) and n.annotation is not None:
            anns.append(n.annotation)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.returns is not None:
            anns.append(n.returns)
        elif isinstance(n, ast.AnnAssign):
            anns.append(n.annotation)
    out = set()
    for a in anns:
        out |= _names_in([a])
        for c in ast.walk(a):
            if isinstance(c, ast.Constant) and isinstance(c.value, str):
                try:
                    out |= _names_in([ast.parse(c.value, mode="eval")])
                except SyntaxError:
                    out |= set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", c.value))
    return out


def build_infos(files):
    out = {}
    for p, s in files.items():
        if not rch._is_source(p):
            continue
        try:
            out[p] = ModInfo(p, s)
        except SyntaxError:
            pass
    return out


def moved_defs_idx(binfo, hinfo):
    """참조 규칙(design §3 MOVED): 반환 {"units": {to: from}, "defs": {to_def: from_def}, "def_hashes": {to_def: hash},
    "rejected": {...}, "_cand": 내부}."""
    bidx, hidx = {}, {}
    for p, inf in binfo.items():
        for (k, key, h, node, names) in inf.units:
            bidx.setdefault((k, key, h), []).append(p)
    for p, inf in hinfo.items():
        for (k, key, h, node, names) in inf.units:
            hidx.setdefault((k, key, h), []).append(p)
    cand, rejected = {}, {}
    for p_h, inf in hinfo.items():
        for (k, key, h, node, names) in inf.units:
            uid = "%s::%s" % (p_h, key if key else "<stmt:%s>" % h[:12])
            origins = bidx.get((k, key, h), [])
            if p_h in origins:
                continue  # 같은 자리 무변경 -- 이동 아님(원래 대상도 아님)
            if not origins:
                continue  # 해시가 같은 원본 없음 -- 이동 아님(옮기며 바뀜 또는 새 정의)
            reason = None
            if len(set(origins)) != 1 or len(origins) != 1:
                reason = ("M-1", sorted(origins))
            else:
                p_b = origins[0]
                # M-0: base p_h가 같은 이름을 다른 것으로 바인딩하지 않는다
                for nm in sorted(names):
                    c = canon(binfo, p_h, nm)
                    if c[0] not in ("unbound", "builtin") and c != ("def", p_b, nm):
                        reason = ("M-0", nm, c)
                        break
                # M-0h(v4, 검토 B1 (1) M-0'): head p_h에서도 u가 그 이름의 유일한 바인딩
                if reason is None and MODE == "v4":
                    for nm in sorted(names):
                        c = canon(hinfo, p_h, nm)
                        if c != ("def", p_h, nm):
                            reason = ("M-0h", nm, c)
                            break
                # M-2: head p_b에서 사라졌다(정의가 없고, 남은 바인딩은 p_h를 가리키는 재수출뿐)
                if reason is None:
                    hb = hinfo.get(p_b)
                    if hb is not None and any(u[0] == k and u[1] == key and (k != "stmt" or u[2] == h) for u in hb.units):
                        reason = ("M-2", "원본 자리에 정의가 남음")
                    else:
                        for nm in sorted(names):
                            c = canon(hinfo, p_b, nm)
                            if c[0] not in ("unbound", "builtin") and c != ("def", p_h, nm):
                                reason = ("M-2", nm, c)
                                break
                # M-3: head에서 한 곳에만
                if reason is None and len(hidx.get((k, key, h), [])) != 1:
                    reason = ("M-3", sorted(hidx[(k, key, h)]))
            if reason is None:
                cand[uid] = (p_h, origins[0], k, key, h, node, names)
            else:
                rejected[uid] = {"rule": reason[0], "detail": [str(x) for x in reason[1:]]}
    # M-4: 고정점(함께 옮긴 것은 함께 옮긴 동안만 인정)
    changed = True
    while changed:
        changed = False
        moved_names = {}
        for uid, (p_h, p_b, k, key, h, node, names) in cand.items():
            for nm in names:
                moved_names[("def", p_h, nm)] = ("def", p_b, nm)
        for uid in list(cand):
            p_h, p_b, k, key, h, node, names = cand[uid]
            bad = None
            if MODE == "v4" and binfo[p_b].futures != hinfo[p_h].futures:     # S3
                bad = ("__future__", sorted(binfo[p_b].futures), sorted(hinfo[p_h].futures))
            if bad is None:
                for v in sorted(global_reads(hinfo[p_h], k, node)):
                    cb = canon(binfo, p_b, v)
                    ch = canon(hinfo, p_h, v)
                    if cb == ch:
                        continue
                    if moved_names.get(ch) == cb:
                        continue
                    bad = (v, cb, ch)
                    break
            if bad:
                del cand[uid]
                rejected[uid] = {"rule": "M-4", "detail": [str(x) for x in bad]}
                changed = True
    # 단위 → def 항목(iter_defs 키): 함수 단위는 그 안의 모든 중첩 def, 클래스 단위는 base 원본과 def_hash가 같은 메서드
    units = {uid: "%s::%s" % (v[1], v[3] if v[3] else "<stmt:%s>" % v[4][:12]) for uid, v in cand.items()}
    defs, dhash, dup_excluded = {}, {}, []
    for uid, (p_h, p_b, k, key, h, node, names) in cand.items():
        if k == "stmt":
            continue
        bmap = {q: mc.def_hash(n) for q, n in rch.iter_defs(binfo[p_b].tree) if q == key or q.startswith(key + ".")}
        for q, n in rch.iter_defs(ast.Module(body=[node], type_ignores=[])):
            if MODE == "v4" and (binfo[p_b].qcount()[q] > 1 or hinfo[p_h].qcount()[q] > 1):   # B1 (2)
                dup_excluded.append("%s::%s" % (p_h, q))
                continue
            hh = mc.def_hash(n)
            if k == "def" or bmap.get(q) == hh:
                defs["%s::%s" % (p_h, q)] = "%s::%s" % (p_b, q)
                dhash["%s::%s" % (p_h, q)] = hh
    return {"units": units, "defs": defs, "def_hashes": dhash, "rejected": rejected,
            "dup_excluded": sorted(set(dup_excluded)), "_cand": cand}


def moved_defs(base_files, head_files):
    binfo, hinfo = build_infos(base_files), build_infos(head_files)
    return moved_defs_idx(binfo, hinfo), binfo, hinfo


def _excluded(moved, nid, fn):
    if nid not in moved["defs"]:
        return False
    if MODE == "v4":                       # B1 (3): (경로, qualname, def_hash)
        return moved["def_hashes"].get(nid) == mc.def_hash(fn)
    return True


# =============================================================================================== 도구 모의(새 규칙)
def sim_v3_targets(base_files, head_files, moved):
    out = []
    for p, s in head_files.items():
        if not rch._is_source(p):
            continue
        b = base_files.get(p)
        if b == s:
            continue
        for q, fn in mc.changed_defs(b, s):
            nid = "%s::%s" % (p, q)
            if not _excluded(moved, nid, fn):
                out.append(nid)
    return sorted(out)


def sim_v7_new(base_files, head_files, moved):
    bd = set()
    for p, s in base_files.items():
        try:
            bd |= {"%s::%s" % (p, q) for q, _ in rch.iter_defs(ast.parse(s))}
        except SyntaxError:
            pass
    out = []
    for p, s in head_files.items():
        if not rch._is_source(p):
            continue
        for q, fn in rch.iter_defs(ast.parse(s)):
            nid = "%s::%s" % (p, q)
            if nid not in bd and not _excluded(moved, nid, fn):
                out.append(nid)
    return sorted(set(out))


def _stmt_items(feats_module, node):
    lo, hi = node.lineno, getattr(node, "end_lineno", node.lineno)
    out = {}
    for k, items in feats_module.items():
        out[k] = [x for x in items if lo <= (x[0] if isinstance(x, tuple) else x) <= hi]
    return out


def sim_v6(base_files, head_files, moved):
    """V6 새 규칙 모의: 옮긴 def 단위의 이전 항목 수 = 원본 맥락, <module>의 이전 항목 수 += 옮긴 문장의 원본 맥락 항목 수."""
    findings = []
    binfo = {p: s for p, s in base_files.items()}
    for p, s in head_files.items():
        if not sl.is_source(p) or base_files.get(p) == s:
            continue
        hf = sl.unit_features(ast.parse(s), s, set())
        b = base_files.get(p)
        bf = sl.unit_features(ast.parse(b), b, set()) if b is not None else {}
        extra_module = {}
        for uid, frm in moved["units"].items():
            if not uid.startswith(p + "::"):
                continue
            p_b = frm.split("::")[0]
            bs = binfo[p_b]
            bft = sl.unit_features(ast.parse(bs), bs, set())
            if "<stmt:" in uid:
                h = uid.split("<stmt:")[1][:-1]
                for n in ast.parse(bs).body:
                    if stmt_hash(n)[:12] == h:
                        for k, items in _stmt_items(bft["<module>"], n).items():
                            extra_module[k] = extra_module.get(k, 0) + len(items)
        for unit, feats in hf.items():
            for k, items in feats.items():
                nid = "%s::%s" % (p, unit)
                if nid in moved["defs"]:
                    p_b, q = moved["defs"][nid].split("::", 1)
                    bs = binfo[p_b]
                    before = len(sl.unit_features(ast.parse(bs), bs, set()).get(q, {}).get(k, []))
                else:
                    before = len(bf.get(unit, {}).get(k, []))
                    if unit == "<module>":
                        before += extra_module.get(k, 0)
                if len(items) > before:
                    findings.append({"path": p, "unit": unit, "check": k, "base": before, "head": len(items)})
    return findings


# =============================================================================================== D0a check 발견 모의(v4 문언)
def sim_check(binfo, hinfo, mv):
    """D0a 계약 4의 발견 중 G1 밖의 것을 문언대로 모의: changed·lost·move-rejected·changed-def(S6)·stmt-order(m2)·future(S3)·rebind(S5).
    move-set·order·shim·cache는 이관표·MOD 표가 필요해 여기서 재지 않는다."""
    f = {k: [] for k in ("move-rejected", "changed", "lost", "changed-def", "stmt-order", "future", "rebind")}
    f["move-rejected"] = sorted(mv["rejected"])
    cand = mv["_cand"]
    origins = {}   # (p_b, k, key, h) -> uid
    for uid, (p_h, p_b, k, key, h, node, names) in cand.items():
        origins[(p_b, k, key, h)] = uid
    bset = {p: {(k, key, h) for (k, key, h, n, nm) in inf.units} for p, inf in binfo.items()}
    hset = {p: {(k, key, h) for (k, key, h, n, nm) in inf.units} for p, inf in hinfo.items()}
    hkeys = {p: {(k, key) for (k, key, h, n, nm) in inf.units if key} for p, inf in hinfo.items()}
    changed_keys = set()
    for p, inf in hinfo.items():
        for (k, key, h, node, names) in inf.units:
            uid = "%s::%s" % (p, key if key else "<stmt:%s>" % h[:12])
            if uid in cand:
                continue
            if (k, key, h) not in bset.get(p, set()):
                f["changed"].append(uid)
                if key:
                    changed_keys.add((p, k, key))
    for p, inf in binfo.items():
        for (k, key, h, node, names) in inf.units:
            if (k, key, h) in hset.get(p, set()) or (p, k, key, h) in origins:
                continue
            if key and (p, k, key) in changed_keys:
                continue
            f["lost"].append("%s::%s" % (p, key if key else "<stmt:%s>" % h[:12]))
    # S6: 옮긴 클래스 안 def 단위 대조(qualname별 해시 목록)
    for uid, (p_h, p_b, k, key, h, node, names) in cand.items():
        if k != "class":
            continue
        bnode = [n for (kk, kq, hh, n, nm) in binfo[p_b].units if kk == "class" and kq == key and hh == h][0]
        bl, hl = collections.defaultdict(list), collections.defaultdict(list)
        for q, n in rch.iter_defs(ast.Module(body=[bnode], type_ignores=[])):
            bl[q].append(mc.def_hash(n))
        for q, n in rch.iter_defs(ast.Module(body=[node], type_ignores=[])):
            hl[q].append(mc.def_hash(n))
        for q in sorted(set(bl) | set(hl)):
            if bl.get(q) != hl.get(q):
                f["changed-def"].append("%s::%s" % (p_h, q))
    # m2: 옮긴 문장 단위의 원본 상대 순서
    by_dest = collections.defaultdict(list)
    for uid, (p_h, p_b, k, key, h, node, names) in cand.items():
        if k != "stmt":
            continue
        bpos = [i for i, (kk, kq, hh, n, nm) in enumerate(binfo[p_b].units) if kk == "stmt" and hh == h][0]
        hpos = [i for i, (kk, kq, hh, n, nm) in enumerate(hinfo[p_h].units) if kk == "stmt" and hh == h][0]
        by_dest[(p_h, p_b)].append((hpos, bpos, uid))
    for (p_h, p_b), lst in by_dest.items():
        lst.sort()
        bp = [x[1] for x in lst]
        if bp != sorted(bp):
            f["stmt-order"].append("%s <- %s" % (p_h, p_b))
    # S3: 목적 파일 __future__ ⊇ 원본
    for uid, (p_h, p_b, k, key, h, node, names) in cand.items():
        if not binfo[p_b].futures <= hinfo[p_h].futures:
            f["future"].append(uid)
    # 옮긴 단위(M-4 거부 포함)가 아니어도: M-4로 거부된 후보의 future 차이도 보고(문언: MOD 파일 ⊇ 원본들)
    for uid, r in mv["rejected"].items():
        if r["rule"] == "M-4" and r["detail"] and r["detail"][0] == "__future__":
            f["future"].append(uid)
    # S5: 모든 head 단위의 전역 읽기 출처 = base 출처(옮긴 단위 사상 적용)
    moved_names = {}
    for uid, (p_h, p_b, k, key, h, node, names) in cand.items():
        for nm in names:
            moved_names[("def", p_h, nm)] = ("def", p_b, nm)
    for p, inf in hinfo.items():
        for (k, key, h, node, names) in inf.units:
            uid = "%s::%s" % (p, key if key else "<stmt:%s>" % h[:12])
            if uid in cand:
                p_src = cand[uid][1]
            elif (k, key, h) in bset.get(p, set()):
                p_src = p
            else:
                continue  # changed/새 단위는 changed가 이미 보고
            for v in sorted(global_reads(inf, k, node)):
                ch, cb = canon(hinfo, p, v), canon(binfo, p_src, v)
                if ch != cb and moved_names.get(ch) != cb:
                    f["rebind"].append("%s:%s" % (uid, v))
                    break
    return {k: sorted(set(v)) for k, v in f.items()}


# =============================================================================================== 합성 저장소
def _onerr(func, path, _exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def make_repo(name, base, head):
    rt = os.path.join(SCR, name)
    if os.path.exists(rt):
        shutil.rmtree(rt, onexc=_onerr)
    os.makedirs(rt)

    def git(*a):
        return subprocess.run(["git", "-C", rt] + list(a), capture_output=True, text=True, check=True).stdout.strip()

    def put(files):
        for dp, dn, fn in os.walk(rt):
            if ".git" in dp.split(os.sep):
                continue
            for f_ in fn:
                full = os.path.join(dp, f_)
                rel = os.path.relpath(full, rt).replace("\\", "/")
                if rel not in files and not rel.startswith(".git"):
                    os.remove(full)
        for rel, text in files.items():
            pth = os.path.join(rt, *rel.split("/"))
            os.makedirs(os.path.dirname(pth), exist_ok=True)
            with open(pth, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
    git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t")
    put(base); git("add", "-A"); git("commit", "-q", "-m", "base"); b = git("rev-parse", "HEAD")
    put(head); git("add", "-A"); git("commit", "-q", "-m", "head"); h = git("rev-parse", "HEAD")
    return rt, b, h


CFG = json.dumps({"reachability_roots": {"before_phase3": ["workspaces/run_harness.py::run2"]}})
HARN = "from a import run\n\ndef run2():\n    return run()\n"
F1 = "def f(x):\n    try:\n        return x / 3.7\n    except Exception:\n        return None\n"
F1E = "def f(x):\n    try:\n        return x / 3.8\n    except Exception:\n        return None\n"
F2 = "def f(x):\n    return x\n"


def base_tools(rt, b, h):
    out = {}
    cfgp = os.path.join(rt, "..", os.path.basename(rt) + "_cfg.json")
    with open(cfgp, "w", encoding="utf-8") as fh:
        fh.write(CFG)
    for tool, extra in (("mutate_changed.py", ["--pytest-ini", os.path.join(G, "pytest_gate.ini")]),
                        ("source_lint.py", []), ("reachability.py", ["--config", cfgp])):
        p = subprocess.run([PY, "-B", os.path.join(G, tool), "--root", rt, "--base", b, "--head", h] + extra,
                           capture_output=True, text=True, encoding="utf-8", timeout=600)
        out[{"mutate_changed.py": "V3", "source_lint.py": "V6", "reachability.py": "V7"}[tool]] = p.returncode
    os.remove(cfgp)
    return out


def new_tools(bf, hf, moved):
    v3 = sim_v3_targets(bf, hf, moved)
    v3_mut = 0
    for nid in v3:
        p, q = nid.split("::", 1)
        src = hf[p]
        for qq, fn in rch.iter_defs(ast.parse(src)):
            if qq == q:
                v3_mut += sum(1 for _ in mc.mutants(fn, src))
    v6 = sim_v6(bf, hf, moved)
    v7 = sim_v7_new(bf, hf, moved)
    return {"V3": 1 if v3_mut else 0, "V6": 1 if v6 else 0, "V7": 1 if v7 else 0,
            "v3_targets": v3, "v3_mutants": v3_mut, "v6": v6, "v7_new_defs": v7}


def A(p):
    return AS + p


CASES = {}   # name -> (base, head, kind, subjects)   kind: accept | reject | observe | adversarial
# ---------------------------------------------------------------- v3 27단계(그대로)
CASES["move-exact"] = ({A("a.py"): "def run():\n    return 1\n\n" + F1, "workspaces/run_harness.py": HARN},
                       {A("a.py"): "from b import f  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): F1,
                        "workspaces/run_harness.py": HARN}, "accept")
CASES["move-edited"] = (CASES["move-exact"][0],
                        {A("a.py"): "from b import f  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): F1E,
                         "workspaces/run_harness.py": HARN}, "reject")
CASES["copy"] = (CASES["move-exact"][0],
                 {A("a.py"): "def run():\n    return 1\n\n" + F1, A("b.py"): F1, "workspaces/run_harness.py": HARN}, "reject")
CASES["wrapper"] = (CASES["move-exact"][0],
                    {A("a.py"): "from b import f as _bf\n\ndef run():\n    return 1\n\ndef f(x):\n    return _bf(x)\n",
                     A("b.py"): F1, "workspaces/run_harness.py": HARN}, "reject")
CASES["ambiguous"] = ({A("a.py"): "def run():\n    return 1\n\n" + F1, A("c.py"): F1, "workspaces/run_harness.py": HARN},
                      {A("a.py"): "from b import f  # noqa: F401\n\ndef run():\n    return 1\n", A("c.py"): F1, A("b.py"): F1,
                       "workspaces/run_harness.py": HARN}, "reject")
CASES["two-targets"] = (CASES["move-exact"][0],
                        {A("a.py"): "from b import f  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): F1, A("d.py"): F1,
                         "workspaces/run_harness.py": HARN}, "reject")
CASES["overwrite"] = ({A("a.py"): "def run():\n    return 1\n\n" + F1, A("b.py"): F2, "workspaces/run_harness.py": HARN},
                      {A("a.py"): "from b import f  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): F1,
                       "workspaces/run_harness.py": HARN}, "reject")
CASES["overwrite-import"] = ({A("a.py"): "def run():\n    return 1\n\n" + F1, A("c.py"): F2, A("b.py"): "from c import f  # noqa\n",
                              "workspaces/run_harness.py": HARN},
                             {A("a.py"): "from b import f  # noqa: F401\n\ndef run():\n    return 1\n", A("c.py"): F2, A("b.py"): F1,
                              "workspaces/run_harness.py": HARN}, "reject")
CASES["absorb-own-import"] = ({A("a.py"): "def run():\n    return 1\n\n" + F1, A("b.py"): "from a import f  # noqa\n",
                               "workspaces/run_harness.py": HARN},
                              {A("a.py"): "from b import f  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): F1,
                               "workspaces/run_harness.py": HARN}, "accept")
CASES["swap"] = ({A("a.py"): "def run():\n    return 1\n\n" + F1, A("b.py"): F2, "workspaces/run_harness.py": HARN},
                 {A("a.py"): "def run():\n    return 1\n\n" + F2, A("b.py"): F1, "workspaces/run_harness.py": HARN}, "reject")
G_BASE = "def run():\n    return 1\n\ndef helper():\n    return 2\n\ndef g(x):\n    try:\n        return helper() / 3.7\n    except Exception:\n        return x\n"
CASES["rebind"] = ({A("a.py"): G_BASE, A("c.py"): "def helper():\n    return 5\n", "workspaces/run_harness.py": HARN},
                   {A("a.py"): "from b import g  # noqa: F401\n\ndef run():\n    return 1\n\ndef helper():\n    return 2\n",
                    A("b.py"): "from c import helper\n\n\ndef g(x):\n    try:\n        return helper() / 3.7\n    except Exception:\n        return x\n",
                    A("c.py"): "def helper():\n    return 5\n", "workspaces/run_harness.py": HARN}, "reject")
CASES["move-with-helper-import"] = ({A("a.py"): G_BASE, "workspaces/run_harness.py": HARN},
                                    {A("a.py"): "from b import g  # noqa: F401\n\ndef run():\n    return 1\n\ndef helper():\n    return 2\n",
                                     A("b.py"): "from a import helper\n\n\ndef g(x):\n    try:\n        return helper() / 3.7\n    except Exception:\n        return x\n",
                                     "workspaces/run_harness.py": HARN}, "accept")
CASES["move-together"] = ({A("a.py"): G_BASE, "workspaces/run_harness.py": HARN},
                          {A("a.py"): "from b import g, helper  # noqa: F401\n\ndef run():\n    return 1\n",
                           A("b.py"): "def helper():\n    return 2\n\ndef g(x):\n    try:\n        return helper() / 3.7\n    except Exception:\n        return x\n",
                           "workspaces/run_harness.py": HARN}, "accept")
CASES["move-chain"] = ({A("a.py"): "from m1 import helper  # noqa\n\ndef run():\n    return 1\n\ndef g(x):\n    try:\n        return helper() / 3.7\n    except Exception:\n        return x\n",
                        A("m1.py"): "def helper():\n    return 2\n", "workspaces/run_harness.py": HARN},
                       {A("a.py"): "from m1 import helper  # noqa\nfrom m2 import g  # noqa\n\ndef run():\n    return 1\n",
                        A("m1.py"): "def helper():\n    return 2\n",
                        A("m2.py"): "from m1 import helper\n\n\ndef g(x):\n    try:\n        return helper() / 3.7\n    except Exception:\n        return x\n",
                        "workspaces/run_harness.py": HARN}, "accept")
CASES["local-shadow"] = ({A("a.py"): "helper = 7\n\ndef run():\n    return 1\n\ndef g(x):\n    helper = x\n    try:\n        return helper / 3.7\n    except Exception:\n        return x\n",
                          "workspaces/run_harness.py": HARN},
                         {A("a.py"): "from b import g  # noqa: F401\n\nhelper = 7\n\ndef run():\n    return 1\n",
                          A("b.py"): "def g(x):\n    helper = x\n    try:\n        return helper / 3.7\n    except Exception:\n        return x\n",
                          "workspaces/run_harness.py": HARN}, "accept")
FF = "import os\n\n\ndef ff():\n    try:\n        return os.path.dirname(__file__) + '/x' * 3\n    except Exception:\n        return None\n"
CASES["file-same-dir"] = ({A("a.py"): "import os\n\ndef run():\n    return 1\n\n\ndef ff():\n    try:\n        return os.path.dirname(__file__) + '/x' * 3\n    except Exception:\n        return None\n",
                           "workspaces/run_harness.py": HARN},
                          {A("a.py"): "from b import ff  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): FF,
                           "workspaces/run_harness.py": HARN}, "accept")
CASES["file-dir-change"] = (CASES["file-same-dir"][0],
                            {A("a.py"): "from run_harness import ff  # noqa: F401\n\ndef run():\n    return 1\n",
                             "workspaces/run_harness.py": HARN + "\n" + FF}, "reject")
CASES["file-dir-change-noshim"] = (CASES["file-same-dir"][0],
                                   {A("a.py"): "def run():\n    return 1\n",
                                    "workspaces/run_harness.py": HARN + "\n" + FF}, "reject")
C_BASE = "class Base:\n    pass\n\nclass Other:\n    pass\n\nclass C(Base):\n    k = 3.5\n\n    def m(self, x):\n        try:\n            return x / 3.7\n        except Exception:\n            return None\n"
CASES["class-exact"] = ({A("a.py"): "def run():\n    return 1\n\n" + C_BASE, "workspaces/run_harness.py": HARN},
                        {A("a.py"): "from b import C, Base, Other  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): C_BASE,
                         "workspaces/run_harness.py": HARN}, "accept")
CASES["class-header-changed"] = (CASES["class-exact"][0],
                                 {A("a.py"): "from b import C, Base, Other  # noqa: F401\n\ndef run():\n    return 1\n",
                                  A("b.py"): C_BASE.replace("class C(Base):", "class C(Other):"),
                                  "workspaces/run_harness.py": HARN}, "reject")
CASES["class-field-changed"] = (CASES["class-exact"][0],
                                {A("a.py"): "from b import C, Base, Other  # noqa: F401\n\ndef run():\n    return 1\n",
                                 A("b.py"): C_BASE.replace("k = 3.5", "k = 4.5"), "workspaces/run_harness.py": HARN}, "reject")
REC = "import dataclasses\n\n\n@dataclasses.dataclass\nclass Rec:\n    a: float = 2.5\n    b: int = 3\n"
CASES["record-class-exact"] = ({A("a.py"): "import dataclasses\n\ndef run():\n    return 1\n\n\n@dataclasses.dataclass\nclass Rec:\n    a: float = 2.5\n    b: int = 3\n",
                                "workspaces/run_harness.py": HARN},
                               {A("a.py"): "from b import Rec  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): REC,
                                "workspaces/run_harness.py": HARN}, "observe")
CASES["record-class-default-changed"] = (CASES["record-class-exact"][0],
                                         {A("a.py"): "from b import Rec  # noqa: F401\n\ndef run():\n    return 1\n",
                                          A("b.py"): REC.replace("2.5", "3.5"), "workspaces/run_harness.py": HARN}, "observe")
CG = "_X_CACHE = {}\n\n\ndef g(k):\n    if len(_X_CACHE) > 3.5:\n        _X_CACHE.clear()\n    return _X_CACHE.setdefault(k, k)\n"
CASES["cache-together"] = ({A("a.py"): "def run():\n    return 1\n\n" + CG, "workspaces/run_harness.py": HARN},
                           {A("a.py"): "from b import g, _X_CACHE  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): CG,
                            "workspaces/run_harness.py": HARN}, "accept")
CASES["cache-split"] = (CASES["cache-together"][0],
                        {A("a.py"): "from b import _X_CACHE\n\ndef run():\n    return 1\n\n\ndef g(k):\n    if len(_X_CACHE) > 3.5:\n        _X_CACHE.clear()\n    return _X_CACHE.setdefault(k, k)\n",
                         A("b.py"): "_X_CACHE = {}\n", "workspaces/run_harness.py": HARN}, "reject")
CASES["same-path-rebind(observation)"] = ({A("a.py"): "from c import helper\n\ndef run():\n    return helper()\n", A("c.py"): "def helper():\n    return 5\n",
                                           A("d.py"): "def helper():\n    return 6\n", "workspaces/run_harness.py": HARN},
                                          {A("a.py"): "from d import helper\n\ndef run():\n    return helper()\n", A("c.py"): "def helper():\n    return 5\n",
                                           A("d.py"): "def helper():\n    return 6\n", "workspaces/run_harness.py": HARN}, "adversarial")

# ---------------------------------------------------------------- 2차 검토 새 반례(부록 B·§3 표) -- 모두 adversarial
RUN = "def run():\n    return 1\n"
CR = "FLAG = True\nif FLAG:\n    def f(x):\n        return -x\n"
CASES["N1-dest-conditional-redef-noshim"] = ({A("a.py"): RUN + "\n" + F1, "workspaces/run_harness.py": HARN},
                                             {A("a.py"): RUN, A("b.py"): F1 + "\n" + CR, "workspaces/run_harness.py": HARN}, "adversarial")
CASES["N1b-dest-conditional-redef-shim"] = (CASES["N1-dest-conditional-redef-noshim"][0],
                                            {A("a.py"): "from b import f  # noqa: F401\n\n" + RUN, A("b.py"): F1 + "\n" + CR,
                                             "workspaces/run_harness.py": HARN}, "adversarial")
CASES["N1c-same-path-conditional-redef"] = (CASES["N1-dest-conditional-redef-noshim"][0],
                                            {A("a.py"): RUN + "\n" + F1 + "\n" + CR, "workspaces/run_harness.py": HARN}, "observe")
PCLS = "class P:\n    @property\n    def x(self):\n        return self._x * 3.7\n\n    @x.setter\n    def x(self, v):\n        self._x = v\n"
CASES["P-property-getter-changed"] = ({A("a.py"): RUN + "\n" + PCLS, "workspaces/run_harness.py": HARN},
                                      {A("a.py"): "from b import P  # noqa: F401\n\n" + RUN, A("b.py"): PCLS.replace("3.7", "4.7"),
                                       "workspaces/run_harness.py": HARN}, "adversarial")
CASES["P-property-exact"] = (CASES["P-property-getter-changed"][0],
                             {A("a.py"): "from b import P  # noqa: F401\n\n" + RUN, A("b.py"): PCLS,
                              "workspaces/run_harness.py": HARN}, "accept-or-conservative")
CASES["N2-dest-lambda-rebind"] = (CASES["N1-dest-conditional-redef-noshim"][0],
                                  {A("a.py"): RUN, A("b.py"): F1 + "\nf = (lambda g: (lambda x: -g(x)))(f)\n",
                                   "workspaces/run_harness.py": HARN}, "adversarial")
G_EXC = "def g(x):\n    try:\n        return helper() / 3.7\n    except Exception:\n        return x\n"
CASES["N3-star-shadow-builtin"] = ({A("a.py"): RUN + "\ndef helper():\n    return 2\n\n" + G_EXC, A("c.py"): "def helper():\n    return 5\n",
                                    "workspaces/run_harness.py": HARN},
                                   {A("a.py"): "from b import g, helper  # noqa: F401\n\n" + RUN,
                                    A("b.py"): "def helper():\n    return 2\n\n" + G_EXC + "\nfrom c import *  # noqa\n",
                                    A("c.py"): "def helper():\n    return 5\n", "workspaces/run_harness.py": HARN}, "adversarial")
G_NB = "def g(x):\n    return helper() * x\n"
CASES["N3b-star-shadow"] = ({A("a.py"): RUN + "\ndef helper():\n    return 2\n\n" + G_NB, A("c.py"): "def helper():\n    return 5\n",
                             "workspaces/run_harness.py": HARN},
                            {A("a.py"): "from b import g, helper  # noqa: F401\n\n" + RUN,
                             A("b.py"): "def helper():\n    return 2\n\n" + G_NB + "\nfrom c import *  # noqa\n",
                             A("c.py"): "def helper():\n    return 5\n", "workspaces/run_harness.py": HARN}, "adversarial")
SETX = "def setx(v):\n    global X\n    X = v\n"
G_X = "def g(y):\n    try:\n        return X / 3.7\n    except Exception:\n        return y\n"
CASES["N4-unbound-global-reader-moved"] = ({A("a.py"): RUN + "\n" + SETX + "\n" + G_X, "workspaces/run_harness.py": HARN},
                                           {A("a.py"): "from b import g  # noqa: F401\n\n" + RUN + "\n" + SETX, A("b.py"): G_X,
                                            "workspaces/run_harness.py": HARN}, "adversarial")
FUT = "from __future__ import annotations\n"
RECB = "@dataclasses.dataclass\nclass Rec:\n    a: float = 2.5\n"
CASES["N5-future-annotations-dropped"] = ({A("a.py"): FUT + "import dataclasses\n\n" + RUN + "\n\n" + RECB, "workspaces/run_harness.py": HARN},
                                          {A("a.py"): FUT + "from b import Rec  # noqa: F401\n\n" + RUN,
                                           A("b.py"): "import dataclasses\n\n\n" + RECB, "workspaces/run_harness.py": HARN}, "adversarial")
CASES["N5ok-future-annotations-kept"] = (CASES["N5-future-annotations-dropped"][0],
                                         {A("a.py"): FUT + "from b import Rec  # noqa: F401\n\n" + RUN,
                                          A("b.py"): FUT + "import dataclasses\n\n\n" + RECB, "workspaces/run_harness.py": HARN}, "accept")
CASES["N6-moved-stmt-order-swapped"] = ({A("a.py"): RUN + "\nX = {}\nX.update(a=1)\nX.update(a=2)\n", "workspaces/run_harness.py": HARN},
                                        {A("a.py"): "from b import X  # noqa: F401\n\n" + RUN,
                                         A("b.py"): "X = {}\nX.update(a=2)\nX.update(a=1)\n", "workspaces/run_harness.py": HARN}, "adversarial")
CASES["N6ok-moved-stmt-order-kept"] = (CASES["N6-moved-stmt-order-swapped"][0],
                                       {A("a.py"): "from b import X  # noqa: F401\n\n" + RUN,
                                        A("b.py"): "X = {}\nX.update(a=1)\nX.update(a=2)\n", "workspaces/run_harness.py": HARN}, "accept")
CASES["N7-method-body-changed-in-moved-class"] = (CASES["class-exact"][0],
                                                  {A("a.py"): "from b import C, Base, Other  # noqa: F401\n\ndef run():\n    return 1\n",
                                                   A("b.py"): C_BASE.replace("x / 3.7", "x / 3.8"), "workspaces/run_harness.py": HARN}, "adversarial")
CASES["N8a-decorator-added"] = (CASES["move-exact"][0],
                                {A("a.py"): "from b import f  # noqa: F401\n\n" + RUN,
                                 A("b.py"): "import functools\n\n\n@functools.lru_cache(maxsize=8)\n" + F1, "workspaces/run_harness.py": HARN}, "adversarial")
DECO_C = "def deco(fn):\n    return fn\n"
DECO_D = "def deco(fn):\n    return lambda x: -fn(x)\n"
CASES["N8b-decorator-name-rebound"] = ({A("a.py"): "from c import deco\n\n" + RUN + "\n\n@deco\n" + F1, A("c.py"): DECO_C, A("d.py"): DECO_D,
                                        "workspaces/run_harness.py": HARN},
                                       {A("a.py"): "from b import f  # noqa: F401\n\n" + RUN, A("b.py"): "from d import deco\n\n\n@deco\n" + F1,
                                        A("c.py"): DECO_C, A("d.py"): DECO_D, "workspaces/run_harness.py": HARN}, "adversarial")
FK = "def f(x, k=K):\n    try:\n        return x / k\n    except Exception:\n        return None\n"
CASES["N9a-default-const-rebound"] = ({A("a.py"): "K = 3.7\n\n" + RUN + "\n\n" + FK, "workspaces/run_harness.py": HARN},
                                      {A("a.py"): "from b import f  # noqa: F401\n\nK = 3.7\n\n" + RUN, A("b.py"): "K = 4.7\n\n\n" + FK,
                                       "workspaces/run_harness.py": HARN}, "adversarial")
FD = "def f(x, k=3.7):\n    try:\n        return x / k\n    except Exception:\n        return None\n"
CASES["N9b-default-expr-changed"] = ({A("a.py"): RUN + "\n\n" + FD, "workspaces/run_harness.py": HARN},
                                     {A("a.py"): "from b import f  # noqa: F401\n\n" + RUN, A("b.py"): FD.replace("k=3.7", "k=4.7"),
                                      "workspaces/run_harness.py": HARN}, "adversarial")
G_H = "def g(x):\n    try:\n        return h() / 3.7\n    except Exception:\n        return x\n"
CASES["N10-import-as-rebound"] = ({A("a.py"): "from c import helper as h\n\n" + RUN + "\n\n" + G_H, A("c.py"): "def helper():\n    return 5\n",
                                   A("d.py"): "def helper():\n    return 6\n", "workspaces/run_harness.py": HARN},
                                  {A("a.py"): "from b import g  # noqa: F401\n\n" + RUN, A("b.py"): "from d import helper as h\n\n\n" + G_H,
                                   A("c.py"): "def helper():\n    return 5\n", A("d.py"): "def helper():\n    return 6\n",
                                   "workspaces/run_harness.py": HARN}, "adversarial")
CASES["N11-method-to-toplevel"] = (CASES["class-exact"][0],
                                   {A("a.py"): "from b import m  # noqa: F401\n\n" + RUN + "\nclass Base:\n    pass\n\nclass Other:\n    pass\n\nclass C(Base):\n    k = 3.5\n",
                                    A("b.py"): "def m(self, x):\n    try:\n        return x / 3.7\n    except Exception:\n        return None\n",
                                    "workspaces/run_harness.py": HARN}, "adversarial")
CASES["N12-try-import-fallback"] = ({A("a.py"): G_BASE, "workspaces/run_harness.py": HARN},
                                    {A("a.py"): "from b import g, helper  # noqa: F401\n\n" + RUN,
                                     A("b.py"): "def helper():\n    return 2\n\ntry:\n    from fastlib import helper  # noqa\nexcept ImportError:\n    pass\n\n" + G_EXC,
                                     "workspaces/run_harness.py": HARN}, "adversarial")
CASES["N13-ext-dir-change"] = ({A("a.py"): "from wsutil import h\n\n" + RUN + "\n\n" + G_H, "workspaces/wsutil.py": "def h():\n    return 1\n",
                                "workspaces/run_harness.py": HARN},
                               {A("a.py"): RUN, "workspaces/wsutil.py": "def h():\n    return 1\n",
                                "workspaces/run_harness.py": HARN + "\nfrom wsutil import h\n\n\n" + G_H}, "adversarial")
# S2: 증강 대입·del로 목적 파일이 이름을 다시 묶음(계약 문언이 def·class·대입·for/with만이면 뚫린다)
CASES["S2-augassign-rebind"] = (CASES["move-exact"][0],
                                {A("a.py"): "from b import f  # noqa: F401\n\n" + RUN, A("b.py"): F1 + "\nf += 0\n",
                                 "workspaces/run_harness.py": HARN}, "adversarial")
CASES["S2-except-as-rebind"] = (CASES["move-exact"][0],
                                {A("a.py"): "from b import f  # noqa: F401\n\n" + RUN,
                                 A("b.py"): F1 + "\ntry:\n    pass\nexcept Exception as f:\n    pass\n",
                                 "workspaces/run_harness.py": HARN}, "adversarial")
# S5: 제자리 단위가 읽는 이름을 import 줄로 다른 정의에 묶음(이동 card 안) -- 옮긴 단위와 함께
CASES["S5-inplace-rebind-in-move-card"] = ({A("a.py"): "from c import helper\n\n" + RUN + "\n\ndef user():\n    return helper()\n\n" + F1,
                                            A("c.py"): "def helper():\n    return 5\n", A("d.py"): "def helper():\n    return 6\n",
                                            "workspaces/run_harness.py": HARN},
                                           {A("a.py"): "from d import helper\nfrom b import f  # noqa: F401\n\n" + RUN + "\n\ndef user():\n    return helper()\n",
                                            A("b.py"): F1, A("c.py"): "def helper():\n    return 5\n", A("d.py"): "def helper():\n    return 6\n",
                                            "workspaces/run_harness.py": HARN}, "adversarial")

# 반례마다 '잡혔다'고 볼 대상(주체 단위·def) -- G1이 그 주체를 V3·V7 대상으로 남기거나 rejected에 넣으면 G1이 잡은 것
SUBJECT = {
    "same-path-rebind(observation)": [A("a.py") + "::run"],
    "N1-dest-conditional-redef-noshim": [A("b.py") + "::f"],
    "N1b-dest-conditional-redef-shim": [A("b.py") + "::f"],
    "P-property-getter-changed": [A("b.py") + "::P.x"],
    "N2-dest-lambda-rebind": [A("b.py") + "::f"],
    "N3-star-shadow-builtin": [A("b.py") + "::g"],
    "N3b-star-shadow": [A("b.py") + "::g"],
    "N4-unbound-global-reader-moved": [A("b.py") + "::g"],
    "N5-future-annotations-dropped": [A("b.py") + "::Rec"],
    "N6-moved-stmt-order-swapped": [],
    "N7-method-body-changed-in-moved-class": [A("b.py") + "::C.m"],
    "N8a-decorator-added": [A("b.py") + "::f"],
    "N8b-decorator-name-rebound": [A("b.py") + "::f"],
    "N9a-default-const-rebound": [A("b.py") + "::f"],
    "N9b-default-expr-changed": [A("b.py") + "::f"],
    "N10-import-as-rebound": [A("b.py") + "::g"],
    "N11-method-to-toplevel": [A("b.py") + "::m"],
    "N12-try-import-fallback": [A("b.py") + "::g", A("b.py") + "::helper"],
    "N13-ext-dir-change": ["workspaces/run_harness.py::g"],
    "S2-augassign-rebind": [A("b.py") + "::f"],
    "S2-except-as-rebind": [A("b.py") + "::f"],
    "S5-inplace-rebind-in-move-card": [A("a.py") + "::user"],
}


def run_mode(mode, bf, hf):
    global MODE
    MODE = mode
    mv, binfo, hinfo = moved_defs(bf, hf)
    nt = new_tools(bf, hf, mv)
    chk = sim_check(binfo, hinfo, mv) if mode == "v4" else None
    MODE = "v4"
    return mv, nt, chk


os.makedirs(SCR, exist_ok=True)
v3prev = {}
if os.path.exists(V3RES):
    with open(V3RES, encoding="utf-8") as fh:
        v3prev = json.load(fh).get("counterexamples", {})
ce = {}
for name, (bf, hf, kind) in CASES.items():
    mv3, nt3, _ = run_mode("v3", bf, hf)
    mv4, nt4, chk = run_mode("v4", bf, hf)
    rt, b, h = make_repo("ce_" + "".join(ch if ch.isalnum() else "_" for ch in name), bf, hf)
    bt = base_tools(rt, b, h)
    shutil.rmtree(rt, onexc=_onerr)
    subj = SUBJECT.get(name, [])
    g1_caught = [s for s in subj if s in nt4["v3_targets"] or s in mv4["rejected"] or s in nt4["v7_new_defs"]]
    # 클래스 단위 주체(Rec)는 V3·V7이 보지 않는다 -- rejected만
    d0a_kinds = sorted(k for k, v in chk.items() if v and k != "move-rejected")
    rec = {"kind": kind, "base_exit": bt,
           "v3_exit": {k: nt3[k] for k in ("V3", "V6", "V7")}, "v3_rejected": {u: r["rule"] for u, r in mv3["rejected"].items()},
           "v3_units": mv3["units"],
           "v4_exit": {k: nt4[k] for k in ("V3", "V6", "V7")}, "v4_rejected": mv4["rejected"], "v4_units": mv4["units"],
           "v4_defs": mv4["defs"], "v4_dup_excluded": mv4["dup_excluded"],
           "v4_detail": {k: nt4[k] for k in ("v3_targets", "v6", "v7_new_defs")},
           "d0a_check_sim": chk, "subjects": subj, "g1_caught": g1_caught, "d0a_caught": d0a_kinds}
    if kind == "adversarial":
        rec["rejected_overall"] = bool(g1_caught or d0a_kinds)
    if name in v3prev:
        p = v3prev[name]
        rec["v3_matches_previous_run"] = (p["base_exit"] == bt and p["new_exit"] == rec["v3_exit"]
                                          and {u: r["rule"] for u, r in p["rejected"].items()} == rec["v3_rejected"])
        rec["v4_equals_v3_exit"] = rec["v4_exit"] == rec["v3_exit"]
    ce[name] = rec
    _partial({"case": name, **{k: rec[k] for k in ("kind", "base_exit", "v3_exit", "v4_exit", "g1_caught", "d0a_caught")}})
res["counterexamples"] = ce
res["adversarial_summary"] = {n: {"g1": r["g1_caught"], "d0a": r["d0a_caught"], "rejected": r["rejected_overall"],
                                  "v3_exit": r["v3_exit"], "v4_exit": r["v4_exit"], "base_exit": r["base_exit"]}
                              for n, r in ce.items() if r["kind"] == "adversarial"}
res["v3_regression"] = {n: r.get("v3_matches_previous_run") for n, r in ce.items() if "v3_matches_previous_run" in r}
res["v3_steps_v4_changed"] = {n: {"v3": r["v3_exit"], "v4": r["v4_exit"]} for n, r in ce.items()
                              if n in v3prev and not r.get("v4_equals_v3_exit")}


# =============================================================================================== 실제 트리
def tree_at(rev, prefixes=rch.GRAPH_PREFIXES):
    return rch.read_tree(R, rev, prefixes)


noop = {}
for rid, (b, h) in {"df36": ("070cf6937e2841bdd3b4781eb9b8ba5bba9cc606", "ed98d35b22b9d3dfac5b26e7794709e1e39b1673"),
                    "dup-w-calc": ("b7d179817245a99cccea45cd5f7642f9815dcec0", "a9de49c031edf544a3af1ce383426c1fa01e6bab")}.items():
    mv, _, _ = moved_defs(tree_at(b, rch.SOURCE_GLOBS), tree_at(h, rch.SOURCE_GLOBS))
    noop[rid] = {"units": mv["units"], "defs": mv["defs"], "rejected": mv["rejected"]}
res["noop"] = noop
_partial({"noop": noop})

# 실제 엔진 파일 통째 이름 바꾸기(같은 디렉터리): 원본은 명시 재수출만 -- 거짓 거부 측정(v4) + D0a check 모의 발견
head = tree_at("HEAD", rch.SOURCE_GLOBS)
real = {}
for m in ("sizing_recipe", "stick_diagram", "topology_library", "design_report"):
    p = AS + m + ".py"
    src = head[p]
    info = ModInfo(p, src)
    tops = sorted({nm for (k, key, h_, node, names) in info.units for nm in names if not nm.startswith("__")})
    hf = dict(head)
    hf[AS + m + "_mv.py"] = src
    hf[p] = "from %s_mv import (%s)  # noqa\n" % (m, ", ".join(tops))
    t0 = time.perf_counter()
    mv, binfo, hinfo = moved_defs(head, hf)
    dt = time.perf_counter() - t0
    t1 = time.perf_counter()
    chk = sim_check(binfo, hinfo, mv)
    dt2 = time.perf_counter() - t1
    all_defs = ["%s::%s" % (AS + m + "_mv.py", q) for q, _ in rch.iter_defs(ast.parse(src))]
    rej = mv["rejected"]
    real[m] = {"units_total": len(info.units), "units_moved": len(mv["units"]),
               "defs_total": len(all_defs), "defs_moved": len([d for d in all_defs if d in mv["defs"]]),
               "dup_excluded": mv["dup_excluded"],
               "rejected_by_rule": {r: sum(1 for v in rej.values() if v["rule"] == r) for r in sorted({v["rule"] for v in rej.values()})},
               "rejected_sample": dict(list(rej.items())[:8]),
               "m0h_violations": sum(1 for v in rej.values() if v["rule"] == "M-0h"),
               "d0a_check_findings": {k: len(v) for k, v in chk.items()},
               "d0a_check_sample": {k: v[:5] for k, v in chk.items() if v},
               "moved_defs_seconds": round(dt, 2), "check_seconds": round(dt2, 2)}
    _partial({"real": m, **{k: real[m][k] for k in ("units_total", "units_moved", "defs_total", "defs_moved", "rejected_by_rule", "d0a_check_findings")}})
res["real_rename_same_dir"] = real

# 엔진 사실(2차 검토 부록 A 재측정): star·global·future·qualname 중복
facts = {}
for m in ("sizing_recipe", "stick_diagram", "topology_library", "design_report"):
    info = ModInfo(AS + m + ".py", head[AS + m + ".py"])
    facts[m] = {"star": "*" in info.bindings, "global_declared": sorted(info.global_declared), "futures": sorted(info.futures),
                "future_line": [n.lineno for n in info.tree.body if isinstance(n, ast.ImportFrom) and n.module == "__future__"],
                "qualname_dups": sorted(q for q, c in info.qcount().items() if c > 1),
                "multi_bound": sorted(n for n, bs in info.bindings.items() if len(bs) > 1)}
res["engine_facts"] = facts

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print("wrote", OUT)
