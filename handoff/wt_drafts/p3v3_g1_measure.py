"""Phase 3 design v3 -- G1 이동 규칙(M-0~M-4 + 클래스 골격 단위 + 문장 단위)의 참조 구현과 반례 재실행(읽기 전용).

이 파일은 **design 문장이 판정 가능한지 확인하는 초안 측정 스크립트**다. 게이트 코드가 아니고, G1 구현(code-author)이나
test 기대값(test-author)의 근거로 쓰지 않는다(작성자≠검증자). 결과는 이 파일 옆 p3v3_g1_results.json에 쓴다(WP-11).

    C:/Python314/python.exe -B p3v3_g1_measure.py

저장소는 읽기만 한다(`git ls-tree`/`show`, 게이트 모듈 import는 -B). 합성 git 저장소는 C:/g29 아래에 만들고 끝나면 지운다.
"""
import ast
import builtins
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
SCR = "C:/g29"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "p3v3_g1_results.json")
sys.path.insert(0, G)
import mutate_changed as mc   # noqa: E402
import reachability as rch    # noqa: E402
import source_lint as sl      # noqa: E402

AS = "skills/analog-gmid-design/assets/"
res = {"head": subprocess.run(["git", "-C", R, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()}

# =============================================================================================== 참조 규칙
MODULE_IDENTITY = {"__name__", "__spec__", "__loader__", "__package__", "__path__", "__cached__", "__builtins__",
                   "__dict__", "__doc__", "__annotations__"}
MODULE_INTROSPECTION_BUILTINS = {"globals", "eval", "exec"}
BUILTINS = set(dir(builtins))


class _Skel(ast.NodeTransformer):
    """클래스 골격: 클래스 안의 def(메서드, 중첩 클래스의 메서드 포함)를 이름 표지로 바꾼다. 함수 안으로는 내려가지 않는다."""

    def visit_FunctionDef(self, n):
        return ast.Expr(ast.Name(id="<method %s>" % n.name, ctx=ast.Load()))

    visit_AsyncFunctionDef = visit_FunctionDef


def skel_hash(cls):
    return mc.def_hash(_Skel().visit(copy.deepcopy(cls)))


def stmt_hash(node):
    return mc.def_hash(node)  # _strip_doc는 Module/def/class 몸체만 건드린다 -- 문장은 ast.dump 그대로


def _bound_names(stmt):
    out = set()
    for n in ast.walk(stmt):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            out.add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
    return out


class ModInfo:
    """한 파일의 최상위 단위와 바인딩(파일당 한 번 파싱)."""

    def __init__(self, path, src):
        self.path, self.src = path, src
        self.tree = ast.parse(src)
        self.units = []           # (kind, key, hash, node, bound_names)
        self.bindings = {}        # name -> list of binding descriptors
        self._st = None
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
                self._collect(sub)
            else:
                for nm in _bound_names(n):
                    self.bindings.setdefault(nm, []).append(("bind",))

    def symtab(self):
        if self._st is None:
            self._st = symtable.symtable(self.src, self.path, "exec")
        return self._st


def _module_file(tree_infos, from_path, modname, level):
    """`from <modname> import` 가 가리키는 트리 안 파일(같은 디렉터리의 <modname>.py). 없으면 None."""
    if level or not modname:
        return None
    d = from_path.rsplit("/", 1)[0] if "/" in from_path else ""
    last = modname.split(".")[-1]
    cand = (d + "/" if d else "") + last + ".py"
    return cand if cand in tree_infos else None


def canon(infos, path, name, depth=0):
    """이름 name이 모듈 path 최상위에서 가리키는 정의의 정규 출처."""
    if depth > 20:
        return ("cycle", path, name)
    if name == "__file__":
        return ("file-dir", path.rsplit("/", 1)[0])
    if name in MODULE_IDENTITY:
        return ("module-identity", path)
    info = infos.get(path)
    if info is None:
        return ("unbound", name) if name not in BUILTINS else ("builtin", name)
    bs = info.bindings.get(name)
    if not bs:
        if "*" in info.bindings:
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
            return ("ext", "." * b[2] + b[1], b[3])
        return canon(infos, tgt, b[3], depth + 1)
    if b[0] == "import":
        tgt = _module_file(infos, path, b[1], 0)
        return ("module", tgt) if tgt else ("ext-module", b[1])
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
        return _names_in([node])
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
    """u 안의 모든 주석(평가형·문자열형)의 식별자 -- 문자열 주석도 도입(`typing.get_type_hints`·dataclasses가
    모듈 전역에서 해석한다). 파싱 못 하는 문자열은 식별자 토큰으로."""
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


def moved_defs(base_files, head_files):
    """참조 규칙(design v3 §3 MOVED): 반환 {"units": {to: from}, "defs": {to_def: from_def}, "rejected": {...}}."""
    bsrc = {p: s for p, s in base_files.items() if rch._is_source(p)}
    hsrc = {p: s for p, s in head_files.items() if rch._is_source(p)}
    binfo, hinfo = {}, {}
    for p, s in bsrc.items():
        try:
            binfo[p] = ModInfo(p, s)
        except SyntaxError:
            pass
    for p, s in hsrc.items():
        try:
            hinfo[p] = ModInfo(p, s)
        except SyntaxError:
            pass
    # canon는 GRAPH 전체가 아니라 소스 분류 파일만으로 해석(엔진 import는 전부 소스 분류 파일 사이)
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
                bnames = names
                # M-0: base p_h가 같은 이름을 다른 것으로 바인딩하지 않는다
                for nm in bnames:
                    c = canon(binfo, p_h, nm)
                    if c[0] not in ("unbound", "builtin") and c != ("def", p_b, nm):
                        reason = ("M-0", nm, c)
                        break
                # M-2: head p_b에서 사라졌다(정의가 없고, 남은 바인딩은 p_h를 가리키는 재수출뿐)
                if reason is None:
                    hb = hinfo.get(p_b)
                    if hb is not None and any(u[0] == k and u[1] == key and (k != "stmt" or u[2] == h) for u in hb.units):
                        reason = ("M-2", "원본 자리에 정의가 남음")
                    else:
                        for nm in bnames:
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
    defs = {}
    for uid, (p_h, p_b, k, key, h, node, names) in cand.items():
        if k == "stmt":
            continue
        bmap = {q: mc.def_hash(n) for q, n in rch.iter_defs(binfo[p_b].tree) if q == key or q.startswith(key + ".")}
        for q, n in rch.iter_defs(ast.Module(body=[node], type_ignores=[])):
            if k == "def" or bmap.get(q) == mc.def_hash(n):
                defs["%s::%s" % (p_h, q)] = "%s::%s" % (p_b, q)
    return {"units": units, "defs": defs, "rejected": rejected}


# =============================================================================================== 도구 모의(새 규칙)
def sim_v3_targets(base_files, head_files, moved):
    out = []
    for p, s in head_files.items():
        if not rch._is_source(p):
            continue
        b = base_files.get(p)
        if b == s:
            continue
        for q, _fn in mc.changed_defs(b, s):
            nid = "%s::%s" % (p, q)
            if nid not in moved["defs"]:
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
        for q, _ in rch.iter_defs(ast.parse(s)):
            nid = "%s::%s" % (p, q)
            if nid not in bd and nid not in moved["defs"]:
                out.append(nid)
    return sorted(out)


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
        # 트리를 files 그대로 맞춘다
        for dp, dn, fn in os.walk(rt):
            if ".git" in dp.split(os.sep):
                continue
            for f in fn:
                full = os.path.join(dp, f)
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
    # V3 exit: 대상 def의 변이가 하나라도 있으면(인벤토리 없음) 1
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


CASES = {}
# 1 정확한 이동(인정)
CASES["move-exact"] = ({A("a.py"): "def run():\n    return 1\n\n" + F1, "workspaces/run_harness.py": HARN},
                       {A("a.py"): "from b import f  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): F1,
                        "workspaces/run_harness.py": HARN})
CASES["move-edited"] = (CASES["move-exact"][0],
                        {A("a.py"): "from b import f  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): F1E,
                         "workspaces/run_harness.py": HARN})
CASES["copy"] = (CASES["move-exact"][0],
                 {A("a.py"): "def run():\n    return 1\n\n" + F1, A("b.py"): F1, "workspaces/run_harness.py": HARN})
CASES["wrapper"] = (CASES["move-exact"][0],
                    {A("a.py"): "from b import f as _bf\n\ndef run():\n    return 1\n\ndef f(x):\n    return _bf(x)\n",
                     A("b.py"): F1, "workspaces/run_harness.py": HARN})
CASES["ambiguous"] = ({A("a.py"): "def run():\n    return 1\n\n" + F1, A("c.py"): F1, "workspaces/run_harness.py": HARN},
                      {A("a.py"): "from b import f  # noqa: F401\n\ndef run():\n    return 1\n", A("c.py"): F1, A("b.py"): F1,
                       "workspaces/run_harness.py": HARN})
CASES["two-targets"] = (CASES["move-exact"][0],
                        {A("a.py"): "from b import f  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): F1, A("d.py"): F1,
                         "workspaces/run_harness.py": HARN})
# B1 덮어쓰기
CASES["overwrite"] = ({A("a.py"): "def run():\n    return 1\n\n" + F1, A("b.py"): F2, "workspaces/run_harness.py": HARN},
                      {A("a.py"): "from b import f  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): F1,
                       "workspaces/run_harness.py": HARN})
# B1 변형: base b.py가 f를 다른 모듈에서 import(바인딩이 H2를 가리킴)
CASES["overwrite-import"] = ({A("a.py"): "def run():\n    return 1\n\n" + F1, A("c.py"): F2, A("b.py"): "from c import f  # noqa\n",
                              "workspaces/run_harness.py": HARN},
                             {A("a.py"): "from b import f  # noqa: F401\n\ndef run():\n    return 1\n", A("c.py"): F2, A("b.py"): F1,
                              "workspaces/run_harness.py": HARN})
# B1 무해 변형: base b.py가 f를 a에서 import(같은 정의) -- 이동 인정
CASES["absorb-own-import"] = ({A("a.py"): "def run():\n    return 1\n\n" + F1, A("b.py"): "from a import f  # noqa\n",
                               "workspaces/run_harness.py": HARN},
                              {A("a.py"): "from b import f  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): F1,
                               "workspaces/run_harness.py": HARN})
CASES["swap"] = ({A("a.py"): "def run():\n    return 1\n\n" + F1, A("b.py"): F2, "workspaces/run_harness.py": HARN},
                 {A("a.py"): "def run():\n    return 1\n\n" + F2, A("b.py"): F1, "workspaces/run_harness.py": HARN})
# B2 재바인딩
G_BASE = "def run():\n    return 1\n\ndef helper():\n    return 2\n\ndef g(x):\n    try:\n        return helper() / 3.7\n    except Exception:\n        return x\n"
CASES["rebind"] = ({A("a.py"): G_BASE, A("c.py"): "def helper():\n    return 5\n", "workspaces/run_harness.py": HARN},
                   {A("a.py"): "from b import g  # noqa: F401\n\ndef run():\n    return 1\n\ndef helper():\n    return 2\n",
                    A("b.py"): "from c import helper\n\n\ndef g(x):\n    try:\n        return helper() / 3.7\n    except Exception:\n        return x\n",
                    A("c.py"): "def helper():\n    return 5\n", "workspaces/run_harness.py": HARN})
CASES["move-with-helper-import"] = ({A("a.py"): G_BASE, "workspaces/run_harness.py": HARN},
                                    {A("a.py"): "from b import g  # noqa: F401\n\ndef run():\n    return 1\n\ndef helper():\n    return 2\n",
                                     A("b.py"): "from a import helper\n\n\ndef g(x):\n    try:\n        return helper() / 3.7\n    except Exception:\n        return x\n",
                                     "workspaces/run_harness.py": HARN})
CASES["move-together"] = ({A("a.py"): G_BASE, "workspaces/run_harness.py": HARN},
                          {A("a.py"): "from b import g, helper  # noqa: F401\n\ndef run():\n    return 1\n",
                           A("b.py"): "def helper():\n    return 2\n\ndef g(x):\n    try:\n        return helper() / 3.7\n    except Exception:\n        return x\n",
                           "workspaces/run_harness.py": HARN})
# 앞 card에서 helper가 이미 m1.py로 옮겨지고 a.py는 재수출만 -- 이번 card에서 g를 m2.py로(ORDER대로 m1 import)
CASES["move-chain"] = ({A("a.py"): "from m1 import helper  # noqa\n\ndef run():\n    return 1\n\ndef g(x):\n    try:\n        return helper() / 3.7\n    except Exception:\n        return x\n",
                        A("m1.py"): "def helper():\n    return 2\n", "workspaces/run_harness.py": HARN},
                       {A("a.py"): "from m1 import helper  # noqa\nfrom m2 import g  # noqa\n\ndef run():\n    return 1\n",
                        A("m1.py"): "def helper():\n    return 2\n",
                        A("m2.py"): "from m1 import helper\n\n\ndef g(x):\n    try:\n        return helper() / 3.7\n    except Exception:\n        return x\n",
                        "workspaces/run_harness.py": HARN})
# 지역 이름이 원본 모듈 최상위 이름과 같아도(유효 범위 규칙) 이동 인정
CASES["local-shadow"] = ({A("a.py"): "helper = 7\n\ndef run():\n    return 1\n\ndef g(x):\n    helper = x\n    try:\n        return helper / 3.7\n    except Exception:\n        return x\n",
                          "workspaces/run_harness.py": HARN},
                         {A("a.py"): "from b import g  # noqa: F401\n\nhelper = 7\n\ndef run():\n    return 1\n",
                          A("b.py"): "def g(x):\n    helper = x\n    try:\n        return helper / 3.7\n    except Exception:\n        return x\n",
                          "workspaces/run_harness.py": HARN})
# __file__ 의존: 같은 디렉터리는 인정, 다른 디렉터리(workspaces/run_harness.py)는 아님
FF = "import os\n\n\ndef ff():\n    try:\n        return os.path.dirname(__file__) + '/x' * 3\n    except Exception:\n        return None\n"
CASES["file-same-dir"] = ({A("a.py"): "import os\n\ndef run():\n    return 1\n\n\ndef ff():\n    try:\n        return os.path.dirname(__file__) + '/x' * 3\n    except Exception:\n        return None\n",
                           "workspaces/run_harness.py": HARN},
                          {A("a.py"): "from b import ff  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): FF,
                           "workspaces/run_harness.py": HARN})
CASES["file-dir-change"] = (CASES["file-same-dir"][0],
                            {A("a.py"): "from run_harness import ff  # noqa: F401\n\ndef run():\n    return 1\n",
                             "workspaces/run_harness.py": HARN + "\n" + FF})
# 원본 자리에 재수출 없이 다른 디렉터리의 소스 파일로(M-2 통과) -- __file__ 출처가 달라 M-4
CASES["file-dir-change-noshim"] = (CASES["file-same-dir"][0],
                                   {A("a.py"): "def run():\n    return 1\n",
                                    "workspaces/run_harness.py": HARN + "\n" + FF})
# B3 클래스
C_BASE = "class Base:\n    pass\n\nclass Other:\n    pass\n\nclass C(Base):\n    k = 3.5\n\n    def m(self, x):\n        try:\n            return x / 3.7\n        except Exception:\n            return None\n"
CASES["class-exact"] = ({A("a.py"): "def run():\n    return 1\n\n" + C_BASE, "workspaces/run_harness.py": HARN},
                        {A("a.py"): "from b import C, Base, Other  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): C_BASE,
                         "workspaces/run_harness.py": HARN})
CASES["class-header-changed"] = (CASES["class-exact"][0],
                                 {A("a.py"): "from b import C, Base, Other  # noqa: F401\n\ndef run():\n    return 1\n",
                                  A("b.py"): C_BASE.replace("class C(Base):", "class C(Other):"),
                                  "workspaces/run_harness.py": HARN})
CASES["class-field-changed"] = (CASES["class-exact"][0],
                                {A("a.py"): "from b import C, Base, Other  # noqa: F401\n\ndef run():\n    return 1\n",
                                 A("b.py"): C_BASE.replace("k = 3.5", "k = 4.5"), "workspaces/run_harness.py": HARN})
REC = "import dataclasses\n\n\n@dataclasses.dataclass\nclass Rec:\n    a: float = 2.5\n    b: int = 3\n"
CASES["record-class-exact"] = ({A("a.py"): "import dataclasses\n\ndef run():\n    return 1\n\n\n@dataclasses.dataclass\nclass Rec:\n    a: float = 2.5\n    b: int = 3\n",
                                "workspaces/run_harness.py": HARN},
                               {A("a.py"): "from b import Rec  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): REC,
                                "workspaces/run_harness.py": HARN})
CASES["record-class-default-changed"] = (CASES["record-class-exact"][0],
                                         {A("a.py"): "from b import Rec  # noqa: F401\n\ndef run():\n    return 1\n",
                                          A("b.py"): REC.replace("2.5", "3.5"), "workspaces/run_harness.py": HARN})
# 캐시
CG = "_X_CACHE = {}\n\n\ndef g(k):\n    if len(_X_CACHE) > 3.5:\n        _X_CACHE.clear()\n    return _X_CACHE.setdefault(k, k)\n"
CASES["cache-together"] = ({A("a.py"): "def run():\n    return 1\n\n" + CG, "workspaces/run_harness.py": HARN},
                           {A("a.py"): "from b import g, _X_CACHE  # noqa: F401\n\ndef run():\n    return 1\n", A("b.py"): CG,
                            "workspaces/run_harness.py": HARN})
CASES["cache-split"] = (CASES["cache-together"][0],
                        {A("a.py"): "from b import _X_CACHE\n\ndef run():\n    return 1\n\n\ndef g(k):\n    if len(_X_CACHE) > 3.5:\n        _X_CACHE.clear()\n    return _X_CACHE.setdefault(k, k)\n",
                         A("b.py"): "_X_CACHE = {}\n", "workspaces/run_harness.py": HARN})
# 같은 경로 import 재바인딩(지금 게이트의 기존 한계 관찰 -- 이동 없음)
CASES["same-path-rebind(observation)"] = ({A("a.py"): "from c import helper\n\ndef run():\n    return helper()\n", A("c.py"): "def helper():\n    return 5\n",
                                           A("d.py"): "def helper():\n    return 6\n", "workspaces/run_harness.py": HARN},
                                          {A("a.py"): "from d import helper\n\ndef run():\n    return helper()\n", A("c.py"): "def helper():\n    return 5\n",
                                           A("d.py"): "def helper():\n    return 6\n", "workspaces/run_harness.py": HARN})

os.makedirs(SCR, exist_ok=True)
ce = {}
for name, (bf, hf) in CASES.items():
    mv = moved_defs(bf, hf)
    rt, b, h = make_repo("ce_" + "".join(ch if ch.isalnum() else "_" for ch in name), bf, hf)
    bt = base_tools(rt, b, h)
    nt = new_tools(bf, hf, mv)
    ce[name] = {"moved_units": mv["units"], "moved_defs": mv["defs"], "rejected": mv["rejected"],
                "base_exit": bt, "new_exit": {k: nt[k] for k in ("V3", "V6", "V7")},
                "new_detail": {k: nt[k] for k in ("v3_targets", "v6", "v7_new_defs")}}
    shutil.rmtree(rt, onexc=_onerr)
res["counterexamples"] = ce


# =============================================================================================== 실제 트리
def tree_at(rev, prefixes=rch.GRAPH_PREFIXES):
    return rch.read_tree(R, rev, prefixes)


# 무동작: 최근 판정 기록 2건
noop = {}
for rid, (b, h) in {"df36": ("070cf6937e2841bdd3b4781eb9b8ba5bba9cc606", "ed98d35b22b9d3dfac5b26e7794709e1e39b1673"),
                    "dup-w-calc": ("b7d179817245a99cccea45cd5f7642f9815dcec0", "a9de49c031edf544a3af1ce383426c1fa01e6bab")}.items():
    mv = moved_defs(tree_at(b, rch.SOURCE_GLOBS), tree_at(h, rch.SOURCE_GLOBS))
    noop[rid] = {"units": mv["units"], "defs": mv["defs"], "rejected": mv["rejected"]}
res["noop"] = noop

# 실제 엔진 파일 통째 이름 바꾸기(같은 디렉터리): 원본은 명시 재수출만 남긴다 -- M-0~M-4가 정당한 이동을 거부하는지(거짓 거부) 측정
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
    mv = moved_defs(head, hf)
    dt = time.perf_counter() - t0
    all_defs = ["%s::%s" % (AS + m + "_mv.py", q) for q, _ in rch.iter_defs(ast.parse(src))]
    rej = mv["rejected"]
    real[m] = {"units_total": len(info.units), "units_moved": len(mv["units"]),
               "defs_total": len(all_defs), "defs_moved": len([d for d in all_defs if d in mv["defs"]]),
               "rejected_by_rule": {r: sum(1 for v in rej.values() if v["rule"] == r) for r in sorted({v["rule"] for v in rej.values()})},
               "rejected_sample": dict(list(rej.items())[:8]),
               "moved_defs_seconds": round(dt, 2)}
res["real_rename_same_dir"] = real

# 클래스 사실(B3): 파일별 클래스 수, 메서드 없는 클래스, 클래스 수준 문장이 있는 클래스
cls = {}
for m in ("sizing_recipe", "stick_diagram", "topology_library", "design_report"):
    t = ast.parse(head[AS + m + ".py"])
    cs = [n for n in t.body if isinstance(n, ast.ClassDef)]
    cls[m] = {"classes": len(cs),
              "no_methods": sum(1 for c in cs if not any(isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) for x in ast.walk(c))),
              "dataclass": sum(1 for c in cs if any((isinstance(d, ast.Name) and d.id == "dataclass") or (isinstance(d, ast.Attribute) and d.attr == "dataclass")
                                                    or (isinstance(d, ast.Call) and ((isinstance(d.func, ast.Name) and d.func.id == "dataclass") or (isinstance(d.func, ast.Attribute) and d.func.attr == "dataclass")))
                                                    for d in c.decorator_list)),
              "exception_base": sum(1 for c in cs if any((isinstance(b_, ast.Name) and (b_.id.endswith("Error") or b_.id.endswith("Exception"))) for b_ in c.bases)),
              "with_class_level_stmts": sum(1 for c in cs if any(not isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and not (isinstance(x, ast.Expr) and isinstance(getattr(x, "value", None), ast.Constant)) for x in c.body))}
res["classes"] = cls

# 이름이 모듈 최상위에서 두 번 이상 바인딩되는 것(canon 'multi' -- 보수적으로 이동 거부 원인이 될 수 있다)
multi = {}
for m in ("sizing_recipe", "stick_diagram", "topology_library", "design_report"):
    info = ModInfo(AS + m + ".py", head[AS + m + ".py"])
    multi[m] = sorted(n for n, bs in info.bindings.items() if len(bs) > 1)
res["multi_bound_names"] = multi

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print("wrote", OUT)
