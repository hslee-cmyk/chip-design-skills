"""V7 배선 검사 (05-role-separation design §10, 계획 N4.2 V7).  -- B33 측정용 시제품(draft, 저장소 반영본 아님)

    $PY reachability.py --root <격리 복제본 루트> --base <커밋> --head <커밋> [--config <gate_config.json>]

새 `def`(base에 없던 (파일, qualname))가 `gate_config.json`의 `reachability_roots`에서 **정적 호출 그래프**
(문자열 레지스트리 포함)로 도달하는지. 도달 못 한 def는 FAIL -- 면제는 레지스트리 등급 D 기록 + 승인 기록
(`target_kind: decision`, `target`에 `<파일>::<qualname>`)이 head 트리에 있을 때. V3(mutate_changed.py)의 인벤토리가
같은 그래프(`build_graph`)를 쓴다. exit 0 PASS / 1 FAIL / 2 실행 오류.

그래프: 노드 = 함수(`<파일>::<qualname>`), 모듈 최상위 코드(`<파일>::<module>`), `if __name__ == "__main__":` 블록
(`<파일>::__main__`). 간선 = 이름 호출·이름 참조(같은 모듈 def, `from M import f`, 없으면 같은 이름의 모든 def),
속성 호출 `x.f`(모듈 별칭이면 그 모듈, 아니면 같은 이름의 모든 def -- dunder 속성 `x.__y__`는 폴백 없음),
def 이름과 같은 문자열 상수. 여기에 (B33)
  R1 모듈 최상위 단순 이름 바인딩 `NAME = <식>`은 바인딩 노드 `<파일>::=NAME`(노드 집합에는 넣지 않는다). 바인딩 노드
     -> 값 식의 이름·속성·생성자 참조(문자열 상수 제외). 바인딩 노드로 가는 간선은 네 형식뿐: 같은 파일 맨 이름(함수
     지역 이름 제외), `from M import NAME`, 모듈 별칭 `M.NAME`, 그 둘에서 M에 바인딩이 없으면 M 파일의
     `from X import NAME`을 따라감(재수출). M은 그래프 안 모듈일 때만.
  R2 호출 `Cls(...)`·`raise Cls`(같은 파일 클래스, `from M import Cls`, `M.Cls`) -> 그 클래스의 `__init__`·`__new__`·
     `__post_init__`(없으면 기반 클래스의 것). `super().__d__` -> 둘러싼 클래스의 기반 클래스의 `__d__`.
  R3(main만) 도달 계산은 소스 분류 파일(`_is_source`) 노드만 따라간다.
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys

# 측정용 변형 스위치(시제품 전용): draft = 초안 v1 문장, fixed = 개정안
VARIANT = os.environ.get("RCH_VARIANT", "fixed")
_V = {
    "fixed": dict(str_in_binding=False, dunder_fallback=False, reexport="chase", local_shadow=True, super_=True,
                  bindings=True, ctors=True, r3=True),
    "draft": dict(str_in_binding=True, dunder_fallback=True, reexport="byname", local_shadow=False, super_=False,
                  bindings=True, ctors=True, r3=True),
    "nosuper": dict(str_in_binding=False, dunder_fallback=False, reexport="chase", local_shadow=True, super_=False,
                    bindings=True, ctors=True, r3=True),
    "loose": dict(str_in_binding=True, dunder_fallback=True, reexport="byname", local_shadow=False, super_=False,
                  bindings=True, ctors=True, r3=True, loose=True),
    "base": dict(str_in_binding=True, dunder_fallback=True, reexport="byname", local_shadow=False, super_=False,
                 bindings=False, ctors=False, r3=False),
}[VARIANT]
CTOR_DUNDERS = ("__init__", "__new__", "__post_init__")


def _is_dunder(s):
    return len(s) > 4 and s.startswith("__") and s.endswith("__")


def _git(root, args):
    p = subprocess.run(["git", "-C", root] + args, capture_output=True, env=dict(os.environ, GIT_NO_REPLACE_OBJECTS="1"))
    if p.returncode != 0:
        raise RuntimeError("git %s 실패: %s" % (" ".join(args[:3]), p.stderr.decode("utf-8", "replace")[:300]))
    return p.stdout


def read_tree(root, rev, prefixes):
    """{상대 경로: 소스} -- rev의 .py 파일 중 prefixes 아래."""
    out = _git(root, ["ls-tree", "-r", "-z", "--name-only", "--full-tree", rev, "--"] + list(prefixes)).decode("utf-8")
    res = {}
    for p in out.split("\0"):
        if p.endswith(".py"):
            res[p] = _git(root, ["show", "%s:%s" % (rev, p)]).decode("utf-8", "replace")
    return res


def _is_main_block(n):
    return isinstance(n, ast.If) and isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Name) \
        and n.test.left.id == "__name__" and any(isinstance(c, ast.Constant) and c.value == "__main__"
                                                  for c in n.test.comparators)


def module_name(path):
    return os.path.splitext(os.path.basename(path))[0]


def iter_defs(tree):
    """(qualname, 노드) -- 중첩 포함."""
    out = []

    def rec(nodes, prefix):
        for n in nodes:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = prefix + n.name
                out.append((q, n))
                rec(n.body, q + ".")
            elif isinstance(n, ast.ClassDef):
                rec(n.body, prefix + n.name + ".")
            elif isinstance(n, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                rec(getattr(n, "body", []) + getattr(n, "orelse", []) + getattr(n, "finalbody", []), prefix)
    rec(tree.body, "")
    return out


def iter_classes(tree):
    """(qualname, ClassDef) -- iter_defs와 같은 순회(중첩 포함)."""
    out = []

    def rec(nodes, prefix):
        for n in nodes:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                rec(n.body, prefix + n.name + ".")
            elif isinstance(n, ast.ClassDef):
                out.append((prefix + n.name, n))
                rec(n.body, prefix + n.name + ".")
            elif isinstance(n, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                rec(getattr(n, "body", []) + getattr(n, "orelse", []) + getattr(n, "finalbody", []), prefix)
    rec(tree.body, "")
    return out


def _refs(nodes, imports, mod_alias):
    """노드 목록(중첩 def 몸체 제외)이 참조하는 (종류, 값) 집합.
    B33 추가 종류: ("call", Cls) 맨 이름 호출·raise, ("callmod", (M, Cls)) 모듈 별칭 호출·raise, ("super", 속성)."""
    refs = set()
    stack = list(nodes)
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                stack.extend(n.decorator_list)
                stack.extend(n.args.defaults + [d for d in n.args.kw_defaults if d is not None])
                refs.add(("nested", n.name))
            else:
                stack.append(n.body)
            continue
        if isinstance(n, (ast.Call, ast.Raise)):
            f = n.func if isinstance(n, ast.Call) else n.exc
            if isinstance(f, ast.Name):
                refs.add(("call", f.id))
            elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in mod_alias:
                refs.add(("callmod", (mod_alias[f.value.id], f.attr)))
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            refs.add(("name", n.id))
        elif isinstance(n, ast.Attribute):
            if isinstance(n.value, ast.Name) and n.value.id in mod_alias:
                refs.add(("modattr", (mod_alias[n.value.id], n.attr)))
            else:
                refs.add(("attr", n.attr))
                if isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id == "super":
                    refs.add(("super", n.attr))
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.isidentifier():
            refs.add(("str", n.value))
        stack.extend(ast.iter_child_nodes(n))
    return refs


def _local_names(fn):
    """함수 fn의 지역 이름(인자·대입 대상·중첩 def/class 이름·except 이름) - global/nonlocal 선언. 중첩 def 몸체는 보지 않는다."""
    a = fn.args
    names = {x.arg for x in a.posonlyargs + a.args + a.kwonlyargs}
    names |= {x.arg for x in (a.vararg, a.kwarg) if x is not None}
    declared = set()
    stack = list(fn.body)
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
            continue
        if isinstance(n, ast.Lambda):
            continue
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            names.add(n.id)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            declared |= set(n.names)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            names.add(n.name)
        stack.extend(ast.iter_child_nodes(n))
    return names - declared


def _bindings(tree):
    """모듈 최상위 단순 이름 바인딩 {NAME: 값 식 목록}."""
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and n.targets and all(isinstance(t, ast.Name) for t in n.targets):
            for t in n.targets:
                out.setdefault(t.id, []).append(n.value)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value is not None:
            out.setdefault(n.target.id, []).append(n.value)
    return out


def build_graph(files: dict):
    """(노드 집합, 간선 {노드: 집합}). 바인딩 노드(`<파일>::=NAME`)는 간선 사전의 키·값에만 있고 노드 집합에는 없다."""
    parsed = {}
    for p, src in files.items():
        try:
            parsed[p] = ast.parse(src)
        except SyntaxError:
            continue
    by_name, by_mod = {}, {}
    nodes = set()
    info = {}
    mods = {}
    for p, tree in parsed.items():
        m = module_name(p)
        mods.setdefault(m, []).append(p)
        defs = iter_defs(tree)
        for q, _ in defs:
            nid = "%s::%s" % (p, q)
            nodes.add(nid)
            by_name.setdefault(q.split(".")[-1], set()).add(nid)
            by_mod.setdefault((m, q.split(".")[-1]), set()).add(nid)
        nodes.add("%s::<module>" % p)
        nodes.add("%s::__main__" % p)
        imports, mod_alias = {}, {}
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module:
                for a in n.names:
                    imports[a.asname or a.name] = (n.module.split(".")[-1], a.name)
            elif isinstance(n, ast.Import):
                for a in n.names:
                    mod_alias[a.asname or a.name.split(".")[0]] = a.name.split(".")[-1]
        classes = iter_classes(tree)
        cls_by_name = {}
        for q, c in classes:
            cls_by_name.setdefault(q.split(".")[-1], set()).add((p, q))
        info[p] = dict(m=m, defs=defs, imports=imports, mod_alias=mod_alias,
                       binds=_bindings(tree) if _V["bindings"] else {},
                       cls_by_name=cls_by_name, cls_nodes={q: c for q, c in classes})

    bind_tab = {p: {k: {"%s::=%s" % (p, k)} for k in info[p]["binds"]} for p in info}
    cls_tab = {p: info[p]["cls_by_name"] for p in info}

    memo_mod = {}

    def lookup_mod(stem, name, table, kind, seen=frozenset()):
        """(모듈 stem, 이름) -> 바인딩 노드/클래스 집합. 그래프 밖 모듈이면 빈 집합(B2). 없으면 M 파일의
        `from X import NAME`을 따라간다(재수출). 순환은 방문 집합으로 끊는다(깊이 상수 없음)."""
        key = (stem, name, kind)
        if not seen and key in memo_mod:
            return memo_mod[key]
        out = set()
        if stem in mods and key not in seen:
            for f in mods[stem]:
                out |= table[f].get(name, set())
            if not out and _V["reexport"] == "chase":
                for f in mods[stem]:
                    imp = info[f]["imports"].get(name)
                    if imp:
                        out |= lookup_mod(imp[0], imp[1], table, kind, seen | {key})
        if not out and _V["reexport"] == "byname" and not seen:
            for f in table:
                out |= table[f].get(name, set())
        if not seen:
            memo_mod[key] = frozenset(out)
        return frozenset(out)

    memo_dunder = {}

    def resolve_class_expr(p, expr):
        if isinstance(expr, ast.Name):
            return cls_tab[p].get(expr.id) or (lookup_mod(*info[p]["imports"][expr.id], cls_tab, "c")
                                               if expr.id in info[p]["imports"] else set())
        if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name) and expr.value.id in info[p]["mod_alias"]:
            return lookup_mod(info[p]["mod_alias"][expr.value.id], expr.attr, cls_tab, "c")
        return set()

    def dunder_impl(c, d, guard=frozenset()):
        """클래스 c=(파일, qualname)의 dunder d 구현 def 노드 집합(자기 것, 없으면 기반 클래스 재귀). 클래스당 1회 계산."""
        key = (c, d)
        if key in memo_dunder:
            return memo_dunder[key]
        if c in guard:
            return set()
        p, q = c
        nid = "%s::%s.%s" % (p, q, d)
        if nid in nodes:
            res = {nid}
        else:
            res = set()
            for b in info[p]["cls_nodes"][q].bases:
                for bc in resolve_class_expr(p, b):
                    res |= dunder_impl(bc, d, guard | {c})
        memo_dunder[key] = frozenset(res)
        return memo_dunder[key]

    def ctor_targets(classes):
        out = set()
        for c in classes:
            for d in CTOR_DUNDERS:
                out |= dunder_impl(c, d)
        return out

    edges = {}
    for p, tree in parsed.items():
        I = info[p]
        imports, mod_alias, defs = I["imports"], I["mod_alias"], I["defs"]
        local = {}
        for q, _ in defs:
            local.setdefault(q.split(".")[-1], set()).add("%s::%s" % (p, q))

        def resolve(refs, own_q=None, locals_=frozenset(), drop_str=False):
            out = set()
            for kind, v in refs:
                if kind in ("name", "str", "nested"):
                    if drop_str and kind == "str":
                        continue
                    if own_q and kind == "nested":
                        out |= {"%s::%s.%s" % (p, own_q, v)} & nodes
                    if v in local:
                        out |= local[v]
                    elif v in imports:
                        out |= by_mod.get(imports[v], set()) or by_name.get(imports[v][1], set())
                    elif kind != "nested":
                        out |= by_name.get(v, set())
                elif kind == "modattr":
                    out |= by_mod.get(v, set()) or (by_name.get(v[1], set())
                                                    if _V["dunder_fallback"] or not _is_dunder(v[1]) else set())
                elif kind == "attr":
                    if _V["dunder_fallback"] or not _is_dunder(v):
                        out |= by_name.get(v, set())
            # R1: 바인딩 노드로 가는 네 형식
            shadow = locals_ if _V["local_shadow"] else frozenset()
            for kind, v in refs:
                if kind == "name" and v not in shadow:
                    if v in bind_tab[p]:
                        out |= bind_tab[p][v]
                    elif v in imports:
                        out |= lookup_mod(imports[v][0], imports[v][1], bind_tab, "b")
                elif kind == "modattr":
                    out |= lookup_mod(v[0], v[1], bind_tab, "b")
                if _V.get("loose") and (kind in ("attr", "str") or (kind == "name" and v not in bind_tab[p]
                                                                   and v not in imports)):
                    for f in bind_tab:
                        out |= bind_tab[f].get(v, set())
            # R2: 생성자
            if _V["ctors"]:
                for kind, v in refs:
                    if kind == "call" and v not in shadow:
                        cl = cls_tab[p].get(v) or (lookup_mod(imports[v][0], imports[v][1], cls_tab, "c")
                                                   if v in imports else set())
                        out |= ctor_targets(cl)
                    elif kind == "callmod":
                        out |= ctor_targets(lookup_mod(v[0], v[1], cls_tab, "c"))
                    elif kind == "super" and _V["super_"] and _is_dunder(v) and own_q and "." in own_q:
                        cq = own_q.rsplit(".", 1)[0]
                        if cq in I["cls_nodes"]:
                            for b in I["cls_nodes"][cq].bases:
                                for bc in resolve_class_expr(p, b):
                                    out |= dunder_impl(bc, v)
            return out
        for q, fn in defs:
            nid = "%s::%s" % (p, q)
            edges[nid] = resolve(_refs(fn.body, imports, mod_alias), q,
                                 _local_names(fn) if _V["local_shadow"] else frozenset()) - {nid}
        top = [n for n in tree.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
               and not _is_main_block(n)]
        edges["%s::<module>" % p] = resolve(_refs(top, imports, mod_alias))
        main = [n for n in tree.body if _is_main_block(n)]
        edges["%s::__main__" % p] = resolve(_refs(main, imports, mod_alias)) | {"%s::<module>" % p}
        for k, vals in I["binds"].items():
            bid = "%s::=%s" % (p, k)
            edges[bid] = resolve(_refs(vals, imports, mod_alias), drop_str=not _V["str_in_binding"]) - {bid}
    return nodes, edges


def reach(edges, roots, keep=None):
    seen, stack = set(), list(roots)
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        if keep is not None and not keep(x):
            continue
        seen.add(x)
        stack.extend(edges.get(x, ()))
    return seen


GRAPH_PREFIXES = ("skills/analog-gmid-design/assets/", "workspaces/")
SOURCE_GLOBS = ("skills/analog-gmid-design/assets/", "workspaces/run_harness.py")


def _is_source(p):
    return (p.startswith("skills/analog-gmid-design/assets/") and p.count("/") == 3 and p.endswith(".py")) \
        or p == "workspaces/run_harness.py"


def _source_node(nid):
    return _is_source(nid.split("::")[0])


def _approved_ids(root, rev):
    ids = set()
    out = _git(root, ["ls-tree", "-r", "-z", "--name-only", "--full-tree", rev, "--", ".ai/approvals/"]).decode("utf-8")
    for p in out.split("\0"):
        b = os.path.basename(p)
        if not p.endswith(".md") or b.startswith("_"):
            continue
        text = _git(root, ["show", "%s:%s" % (rev, p)]).decode("utf-8", "replace").replace("\r\n", "\n")
        if not text.startswith("---\n") or "\ntarget_kind: decision\n" not in text:
            continue
        for line in text.split("\n"):
            if line.startswith("target: "):
                ids |= {x.strip() for x in line[len("target: "):].split(",")}
    return ids


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="reachability.py")
    ap.add_argument("--root", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--config", default=None, help="gate_config.json(기본: head 트리의 tools/gates/gate_config.json)")
    try:
        ns = ap.parse_args(argv)
    except SystemExit:
        return 2
    try:
        if ns.config:
            with open(ns.config, "rb") as fh:
                cfg = json.loads(fh.read().decode("utf-8"))
        else:
            cfg = json.loads(_git(ns.root, ["show", "%s:tools/gates/gate_config.json" % ns.head]).decode("utf-8"))
        roots_cfg = cfg.get("reachability_roots")
        if not isinstance(roots_cfg, dict) or not roots_cfg:
            raise ValueError("gate_config.json reachability_roots가 없다")
        head = read_tree(ns.root, ns.head, GRAPH_PREFIXES)
        base = read_tree(ns.root, ns.base, GRAPH_PREFIXES)
        nodes, edges = build_graph(head)
        roots = sorted({r for v in roots_cfg.values() for r in v if r.split("::")[0] in head})
        missing_roots = sorted({r for v in roots_cfg.values() for r in v} - set(roots))
        seen = reach(edges, roots, _source_node if _V["r3"] else None)
        base_defs = set()
        for p, src in base.items():
            try:
                base_defs |= {"%s::%s" % (p, q) for q, _ in iter_defs(ast.parse(src))}
            except SyntaxError:
                continue
        new_defs = sorted(n for n in nodes if _is_source(n.split("::")[0]) and not n.endswith(("::<module>", "::__main__"))
                          and n not in base_defs)
        unreached = [n for n in new_defs if n not in seen]
        approved = _approved_ids(ns.root, ns.head)
        unexempt = [n for n in unreached if n not in approved]
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, UnicodeDecodeError) as e:
        print(json.dumps({"tool": "V7", "verdict": "ERROR", "error": "%s: %s" % (type(e).__name__, e)}, ensure_ascii=False))
        return 2
    print(json.dumps({"tool": "V7", "verdict": "FAIL" if unexempt else "PASS", "roots": roots,
                      "roots_without_file": missing_roots, "new_defs": new_defs, "unreached": unreached,
                      "unreached_without_approval": unexempt}, ensure_ascii=False))
    return 1 if unexempt else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
