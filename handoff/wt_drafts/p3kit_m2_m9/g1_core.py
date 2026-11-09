
# ===================================================================================================================
# G1 시제품(측정 전용 -- 역할 산출물 아님, test-author·code-author 열람 금지). spec card 20260930-p3-gate-move-aware
# 계약 0~3 문장을 reachability.py 이름 공간에 덧붙이는 코드다(install_proto.py가 이 파일 본문을 reachability.py 끝에 붙인다).
# 참조 구현 _drafts/p3v4_g1_measure.py(v4 모드)의 판정을 SourceIndex 모양으로 옮겼다.
# 잘못된 구현 변형: 환경 변수 G1_VARIANT(쉼표 목록) -- 규칙 하나씩 끈다(판별력 측정용).
# ===================================================================================================================
import builtins as _g1_builtins
import collections as _g1_collections
import copy as _g1_copy
import hashlib as _g1_hashlib
import re as _g1_re
import symtable as _g1_symtable

_G1_MODULE_IDENTITY = {"__name__", "__spec__", "__loader__", "__package__", "__path__", "__cached__", "__builtins__",
                       "__dict__", "__doc__", "__annotations__"}
_G1_INTROSPECT = {"globals", "eval", "exec"}
_G1_BUILTINS = set(dir(_g1_builtins))
_G1_COMPS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
G1_STATS = _g1_collections.Counter()      # 계약 10 확인용(파싱·symtable 횟수)


def _g1_var(flag):
    return flag in os.environ.get("G1_VARIANT", "").split(",")


def _strip_doc(fn):
    import copy as _c
    f = _c.deepcopy(fn)
    for n in ast.walk(f):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)) and n.body \
                and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant) \
                and isinstance(n.body[0].value.value, str):
            n.body = n.body[1:] or [ast.Pass()]
    return f


def def_hash(fn):
    return _g1_hashlib.sha256(ast.dump(_strip_doc(fn), include_attributes=False).encode("utf-8")).hexdigest()


class _G1Skel(ast.NodeTransformer):
    def visit_FunctionDef(self, n):
        return ast.Expr(ast.Name(id="<method %s>" % n.name, ctx=ast.Load()))

    visit_AsyncFunctionDef = visit_FunctionDef


def _g1_skel_hash(cls):
    if _g1_var("class_name_only"):          # 잘못된 구현: 클래스 단위를 머리·필드 없이 이름으로만
        return "class:" + cls.name
    return def_hash(_G1Skel().visit(_g1_copy.deepcopy(cls)))


def _g1_bound_names(stmt):
    out = set()

    def visit(n, in_comp=False):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
            for d in n.decorator_list:
                visit(d)
            return
        if isinstance(n, ast.Lambda):
            for d in n.args.defaults + [x for x in n.args.kw_defaults if x is not None]:
                visit(d)
            return
        if isinstance(n, _G1_COMPS):
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
        if isinstance(n, getattr(ast, "TypeAlias", ())) and isinstance(n.name, ast.Name):
            out.add(n.name.id)
        for ch in ast.iter_child_nodes(n):
            visit(ch, in_comp)

    visit(stmt)
    return out


def _g1_names_in(exprs):
    out = set()
    for e in exprs:
        if e is None:
            continue
        for n in ast.walk(e):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                out.add(n.id)
    return out


def _g1_free_loads(node):
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
            args = {x.arg for x in a.posonlyargs + a.args + a.kwonlyargs} | ({a.vararg.arg} if a.vararg else set()) \
                | ({a.kwarg.arg} if a.kwarg else set())
            visit(n.body, loc | args)
            return
        if isinstance(n, _G1_COMPS):
            gens = n.generators
            visit(gens[0].iter, loc)
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
            args = {x.arg for x in a.posonlyargs + a.args + a.kwonlyargs} | ({a.vararg.arg} if a.vararg else set()) \
                | ({a.kwarg.arg} if a.kwarg else set())
            stored = {x.id for x in ast.walk(n) if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del))}
            loc2 = frozenset((set(loc) | args | stored) - glob)
            for s in n.body:
                visit(s, loc2)
            return
        for ch in ast.iter_child_nodes(n):
            visit(ch, loc)

    visit(node, frozenset())
    return out


def _g1_annotation_names(node):
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
        out |= _g1_names_in([a])
        for c in ast.walk(a):
            if isinstance(c, ast.Constant) and isinstance(c.value, str):
                try:
                    out |= _g1_names_in([ast.parse(c.value, mode="eval")])
                except SyntaxError:
                    out |= set(_g1_re.findall(r"[A-Za-z_][A-Za-z0-9_]*", c.value))
    return out


def _g1_table_globals(t):
    out = set()
    for s in t.get_symbols():
        if s.is_global() and (s.is_referenced() or s.is_assigned()):
            out.add(s.get_name())
    for c in t.get_children():
        out |= _g1_table_globals(c)
    return out


def _g1_dir(path):
    return path.rsplit("/", 1)[0] if "/" in path else ""


class _G1Mod:
    def __init__(self, path, src):
        self.path, self.src = path, src
        G1_STATS["ast.parse"] += 1
        self.tree = ast.parse(src)
        self.units = []                 # (kind, key, hash, node, bound frozenset)
        self.bindings = {}
        self._st = None
        self._gn = None
        self.futures = frozenset(a.name for n in self.tree.body if isinstance(n, ast.ImportFrom) and n.module == "__future__"
                                 for a in n.names)
        self.global_declared = frozenset(nm for n in ast.walk(self.tree) if isinstance(n, ast.Global) for nm in n.names)
        for n in self.tree.body:
            if _is_main_block(n):
                continue
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.units.append(("def", n.name, def_hash(n), n, frozenset({n.name})))
            elif isinstance(n, ast.ClassDef):
                self.units.append(("class", n.name, _g1_skel_hash(n), n, frozenset({n.name})))
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                pass
            else:
                self.units.append(("stmt", None, def_hash(n), n, frozenset(_g1_bound_names(n))))
        self._collect(self.tree.body)
        self.qcount = _g1_collections.Counter(q for q, _ in iter_defs(self.tree))

    def _add(self, nm, b):
        self.bindings.setdefault(nm, []).append(b)

    def _collect(self, body):
        for n in body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self._add(n.name, ("bind",))
            elif isinstance(n, ast.ImportFrom):
                for a in n.names:
                    if a.name == "*":
                        self._add("*", ("star", n.module, n.level))
                    else:
                        self._add(a.asname or a.name, ("from", n.module or "", n.level, a.name))
            elif isinstance(n, ast.Import):
                for a in n.names:
                    self._add(a.asname or a.name.split(".")[0], ("import", a.name if a.asname else a.name.split(".")[0]))
            elif isinstance(n, (ast.If, ast.Try, ast.With, ast.For, ast.While, getattr(ast, "TryStar", ast.Try),
                                getattr(ast, "Match", ast.If))) and not _is_main_block(n):
                sub = []
                for f in ("body", "orelse", "finalbody"):
                    sub += getattr(n, f, []) or []
                for h in getattr(n, "handlers", []) or []:
                    sub += h.body
                    if h.name:
                        self._add(h.name, ("bind",))
                for c in getattr(n, "cases", []) or []:
                    sub += c.body
                    for nm in _g1_bound_names(ast.Expr(ast.Constant(0))) | {x.name for x in ast.walk(c.pattern)
                                                                           if isinstance(x, (ast.MatchAs, ast.MatchStar)) and x.name} \
                            | {x.rest for x in ast.walk(c.pattern) if isinstance(x, ast.MatchMapping) and x.rest}:
                        self._add(nm, ("bind",))
                names = set()
                if isinstance(n, ast.For):
                    names |= {x.id for x in ast.walk(n.target) if isinstance(x, ast.Name)}
                if isinstance(n, ast.With):
                    for it in n.items:
                        if it.optional_vars is not None:
                            names |= {x.id for x in ast.walk(it.optional_vars) if isinstance(x, ast.Name)}
                for nm in names:
                    self._add(nm, ("bind",))
                for e in [getattr(n, "test", None), getattr(n, "iter", None), getattr(n, "subject", None)] + \
                        [it.context_expr for it in getattr(n, "items", []) or []]:
                    if e is not None:
                        for nm in _g1_bound_names(ast.Expr(e)):
                            self._add(nm, ("bind",))
                self._collect(sub)
            else:
                for nm in _g1_bound_names(n):
                    self._add(nm, ("bind",))

    def symtab(self):
        if self._st is None:
            G1_STATS["symtable"] += 1
            self._st = _g1_symtable.symtable(self.src, self.path, "exec")
        return self._st

    def unit_globals(self, kind, node):
        if kind == "stmt":
            if _g1_var("stmt_names_in"):        # 잘못된 구현: 문장 단위 전역 읽기를 유효 범위 없이 모든 Load 이름으로
                return _g1_names_in([node])
            return _g1_free_loads(node) | _g1_annotation_names(node)
        if _g1_var("names_in_all"):              # 잘못된 구현: 함수·클래스도 symtable 없이 모든 Load 이름(지역 포함)
            return _g1_names_in([node]) | _g1_annotation_names(node)
        out = set()
        tabs = [c for c in self.symtab().get_children() if c.get_name() == node.name]
        if len(tabs) != 1:
            tabs = [c for c in tabs if c.get_lineno() == node.lineno] or tabs
        for t in tabs:
            out |= _g1_table_globals(t)
        if kind == "def":
            a = node.args
            out |= _g1_names_in(node.decorator_list + a.defaults + [d for d in a.kw_defaults if d is not None]
                                + [x.annotation for x in a.posonlyargs + a.args + a.kwonlyargs if x.annotation is not None]
                                + [node.returns])
        else:
            out |= _g1_names_in(node.decorator_list + node.bases + [k.value for k in node.keywords])
        out |= _g1_annotation_names(node)
        return out


class SourceIndex:
    """계약 0: {저장소 상대 경로: 소스}(소스 파일만) 색인. 파일마다 ast.parse 1회, symtable 1회(처음 필요할 때)."""

    def __init__(self, files):
        self._mods = {}
        for p, s in files.items():
            if not _is_source(p):
                continue
            try:
                self._mods[p] = _G1Mod(p, s)
            except SyntaxError:
                continue
        self._origin = {}

    def paths(self):
        return list(self._mods)

    def mod(self, path):
        return self._mods.get(path)

    def tree(self, path):
        """계약 0(v9, D0a 요청): 색인이 만든 그 파일의 ast.parse 결과(같은 객체 -- 다시 파싱하지 않는다). 색인에 없으면 None."""
        m = self._mods.get(path)
        return None if m is None else m.tree

    def units(self, path):
        m = self._mods.get(path)
        return [] if m is None else [(k, q if q else "<stmt:%s>" % h[:12], h, b) for (k, q, h, n, b) in m.units]

    def global_names(self, path):
        m = self._mods.get(path)
        if m is None:
            return {}
        if m._gn is None:
            m._gn = {}
            for (k, q, h, n, b) in m.units:
                key = q if q else "<stmt:%s>" % h[:12]
                m._gn[key] = frozenset(m.unit_globals(k, n))
        return m._gn

    def _module_file(self, from_path, modname, level):
        if level or not modname:
            return None
        d = _g1_dir(from_path)
        cand = (d + "/" if d else "") + modname.split(".")[-1] + ".py"
        return cand if cand in self._mods else None

    def binding_origin(self, path, name, _depth=0):
        key = (path, name)
        if _depth == 0 and key in self._origin:
            return self._origin[key]
        r = self._origin_calc(path, name, _depth)
        if _depth == 0:
            self._origin[key] = r
        return r

    def _origin_calc(self, path, name, depth):
        if depth > 20:
            return ("cycle", path, name)
        if name == "__file__":
            return ("file-dir", _g1_dir(path)) if not _g1_var("file_nodir") else ("module-identity", "file")
        if name in _G1_MODULE_IDENTITY:
            return ("module-identity", path)
        m = self._mods.get(path)
        if m is None:
            return ("builtin", name) if name in _G1_BUILTINS else ("unbound", name)
        if "*" in m.bindings and not _g1_var("star_unbound_only"):
            return ("star", path, name)
        if name in m.global_declared and not _g1_var("no_global_dynamic"):
            return ("global-dynamic", path, name)
        bs = m.bindings.get(name)
        if not bs:
            if "*" in m.bindings:
                return ("star", path, name)
            if name in _G1_INTROSPECT:
                return ("module-identity", path)
            return ("builtin", name) if name in _G1_BUILTINS else ("unbound", name)
        if len(bs) > 1:
            return ("multi", path, name)
        b = bs[0]
        if b[0] == "bind":
            return ("def", path, name)
        if b[0] == "from":
            tgt = self._module_file(path, b[1], b[2])
            if tgt is None:
                if _g1_var("ext_nodir"):
                    return ("ext", "." * b[2] + b[1], b[3])
                return ("ext", _g1_dir(path), "." * b[2] + b[1], b[3])
            return self.binding_origin(tgt, b[3], depth + 1)
        if b[0] == "import":
            tgt = self._module_file(path, b[1], 0)
            if tgt:
                return ("module", tgt)
            return ("ext-module", b[1]) if _g1_var("ext_nodir") else ("ext-module", _g1_dir(path), b[1])
        return ("other", path, name)


def moved_defs(base, head):
    """계약 3. base·head = read_tree 모양 사전 또는 SourceIndex."""
    G1_STATS["moved_defs"] += 1
    B = base if isinstance(base, SourceIndex) else SourceIndex(base)
    H = head if isinstance(head, SourceIndex) else SourceIndex(head)
    bidx, hidx = {}, {}
    for p in B.paths():
        for (k, q, h, n, b) in B.mod(p).units:
            bidx.setdefault((k, q, h), []).append(p)
    for p in H.paths():
        for (k, q, h, n, b) in H.mod(p).units:
            hidx.setdefault((k, q, h), []).append(p)
    cand, rejected = {}, {}
    for p_h in H.paths():
        for (k, q, h, node, names) in H.mod(p_h).units:
            uid = "%s::%s" % (p_h, q if q else "<stmt:%s>" % h[:12])
            origins = bidx.get((k, q, h), [])
            if p_h in origins or not origins:
                continue
            reason = None
            if len(origins) != 1 and not _g1_var("no_m1"):
                reason = ("M-1", sorted(origins))
            else:
                p_b = origins[0]
                if not _g1_var("no_m0"):
                    for nm in sorted(names):
                        c = B.binding_origin(p_h, nm)
                        ok = c[0] in ("unbound", "builtin") or c == ("def", p_b, nm)
                        if _g1_var("m0_strict"):     # 잘못된 구현: base 목적 파일에 그 이름이 있으면 무조건 거부(원본 재수출도)
                            ok = c[0] in ("unbound", "builtin")
                        if not ok:
                            reason = ("M-0", nm, c)
                            break
                if reason is None and not _g1_var("no_m0h"):
                    for nm in sorted(names):
                        c = H.binding_origin(p_h, nm)
                        if c != ("def", p_h, nm):
                            reason = ("M-0h", nm, c)
                            break
                if reason is None and not _g1_var("no_m2"):
                    hb = H.mod(p_b)
                    if hb is not None and any(u[0] == k and u[1] == q and (k != "stmt" or u[2] == h) for u in hb.units):
                        reason = ("M-2", "원본 자리에 정의가 남음")
                    else:
                        for nm in sorted(names):
                            c = H.binding_origin(p_b, nm)
                            if c[0] not in ("unbound", "builtin") and c != ("def", p_h, nm):
                                reason = ("M-2", nm, c)
                                break
                if reason is None and not _g1_var("no_m3") and len(hidx.get((k, q, h), [])) != 1:
                    reason = ("M-3", sorted(hidx[(k, q, h)]))
            if reason is None:
                cand[uid] = (p_h, origins[0], k, q, h, node, names)
            else:
                rejected[uid] = {"rule": reason[0], "detail": [str(x) for x in reason[1:]]}
    changed = True
    while changed and not _g1_var("no_m4"):
        changed = False
        moved_names = {}
        if not _g1_var("no_moved_map"):
            for uid, (p_h, p_b, k, q, h, node, names) in cand.items():
                for nm in names:
                    moved_names[("def", p_h, nm)] = ("def", p_b, nm)
        for uid in list(cand):
            p_h, p_b, k, q, h, node, names = cand[uid]
            bad = None
            if B.mod(p_b).futures != H.mod(p_h).futures and not _g1_var("no_future"):
                bad = ("__future__", sorted(B.mod(p_b).futures), sorted(H.mod(p_h).futures))
            if bad is None:
                key = q if q else "<stmt:%s>" % h[:12]
                for v in sorted(H.global_names(p_h)[key]):
                    cb, ch = B.binding_origin(p_b, v), H.binding_origin(p_h, v)
                    if cb == ch or moved_names.get(ch) == cb:
                        continue
                    bad = (v, cb, ch)
                    break
            if bad:
                del cand[uid]
                rejected[uid] = {"rule": "M-4", "detail": [str(x) for x in bad]}
                changed = True
    units = {uid: "%s::%s" % (v[1], v[3] if v[3] else "<stmt:%s>" % v[4][:12]) for uid, v in cand.items()}
    defs, dhash = {}, {}
    for uid, (p_h, p_b, k, q, h, node, names) in cand.items():
        if k == "stmt":
            continue
        bm, hm = B.mod(p_b), H.mod(p_h)
        bmap = {qq: def_hash(n) for qq, n in iter_defs(bm.tree) if qq == q or qq.startswith(q + ".")}
        for qq, n in iter_defs(ast.Module(body=[node], type_ignores=[])):
            if (bm.qcount[qq] > 1 or hm.qcount[qq] > 1) and not _g1_var("no_dup_excl"):
                continue
            hh = def_hash(n)
            if k == "def" or bmap.get(qq) == hh or _g1_var("class_methods_all"):
                defs["%s::%s" % (p_h, qq)] = "%s::%s" % (p_b, qq)
                dhash["%s::%s" % (p_h, qq)] = hh
    return {"units": units, "defs": defs, "def_hashes": dhash, "rejected": rejected}


def g1_excluded(moved, path, qualname, fn):
    """계약 4·6: (경로, qualname, def_hash)가 모두 맞을 때만 뺀다."""
    nid = "%s::%s" % (path, qualname)
    if nid not in moved["defs"]:
        return False
    if _g1_var("key_only"):                    # 잘못된 구현: 키만 대조(2차 검토 B1 (3))
        return True
    return moved["def_hashes"].get(nid) == def_hash(fn)


def g1_moved_list(moved):
    return [{"from": v, "to": k} for k, v in moved["defs"].items()]
