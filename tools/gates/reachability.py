"""V7 배선 검사 (05-role-separation design §10, 계획 N4.2 V7).

    $PY reachability.py --root <격리 복제본 루트> --base <커밋> --head <커밋> [--config <gate_config.json>]

새 `def`(base에 없던 (파일, qualname))가 `gate_config.json`의 `reachability_roots`에서 **정적 호출 그래프**
(문자열 레지스트리 포함)로 도달하는지. 도달 못 한 def는 FAIL -- 면제는 레지스트리 등급 D 기록 + 승인 기록
(`target_kind: decision`, `target`에 `<파일>::<qualname>`)이 head 트리에 있을 때. V3(mutate_changed.py)의 인벤토리가
같은 그래프(`build_graph`)를 쓴다. exit 0 PASS / 1 FAIL / 2 실행 오류.

그래프(과대 근사 -- 도달 판정이 거짓 FAIL을 내지 않는 쪽): 노드 = 함수(`<파일>::<qualname>`), 모듈 최상위 코드
(`<파일>::<module>`), `if __name__ == "__main__":` 블록(`<파일>::__main__`). 간선 = 이름 호출·이름 참조(같은 모듈 def,
`from M import f`, 없으면 같은 이름의 모든 def), 속성 호출 `x.f`(모듈 별칭이면 그 모듈, 아니면 같은 이름의 모든 def),
def 이름과 같은 문자열 상수(문자열 레지스트리).
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys


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


def _refs(nodes, imports, mod_alias):
    """노드 목록(중첩 def 몸체 제외)이 참조하는 (종류, 값) 집합."""
    refs = set()
    stack = list(nodes)
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            # 중첩 def는 자기 노드가 있다. 이름 자체(정의)가 참조는 아니다. 기본값·데코레이터는 여기서 본다.
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                stack.extend(n.decorator_list)
                stack.extend(n.args.defaults + [d for d in n.args.kw_defaults if d is not None])
                refs.add(("nested", n.name))
            else:
                stack.append(n.body)
            continue
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            refs.add(("name", n.id))
        elif isinstance(n, ast.Attribute):
            if isinstance(n.value, ast.Name) and n.value.id in mod_alias:
                refs.add(("modattr", (mod_alias[n.value.id], n.attr)))
            else:
                refs.add(("attr", n.attr))
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.isidentifier():
            refs.add(("str", n.value))
        stack.extend(ast.iter_child_nodes(n))
    return refs


def build_graph(files: dict):
    """(노드 집합, 간선 {노드: 집합}, 이름 색인)."""
    parsed = {}
    for p, src in files.items():
        try:
            parsed[p] = ast.parse(src)
        except SyntaxError:
            continue
    by_name, by_mod = {}, {}
    nodes = set()
    for p, tree in parsed.items():
        m = module_name(p)
        for q, _ in iter_defs(tree):
            nid = "%s::%s" % (p, q)
            nodes.add(nid)
            by_name.setdefault(q.split(".")[-1], set()).add(nid)
            by_mod.setdefault((m, q.split(".")[-1]), set()).add(nid)
        nodes.add("%s::<module>" % p)
        nodes.add("%s::__main__" % p)
    edges = {}
    for p, tree in parsed.items():
        m = module_name(p)
        imports, mod_alias = {}, {}
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module:
                for a in n.names:
                    imports[a.asname or a.name] = (n.module.split(".")[-1], a.name)
            elif isinstance(n, ast.Import):
                for a in n.names:
                    mod_alias[a.asname or a.name.split(".")[0]] = a.name.split(".")[-1]
        defs = iter_defs(tree)
        local = {}
        for q, _ in defs:
            local.setdefault(q.split(".")[-1], set()).add("%s::%s" % (p, q))

        def resolve(refs, own_q=None):
            out = set()
            for kind, v in refs:
                if kind in ("name", "str", "nested"):
                    if own_q and kind == "nested":
                        out |= {"%s::%s.%s" % (p, own_q, v)} & nodes
                    if v in local:
                        out |= local[v]
                    elif v in imports:
                        out |= by_mod.get(imports[v], set()) or by_name.get(imports[v][1], set())
                    elif kind != "nested":
                        out |= by_name.get(v, set())
                elif kind == "modattr":
                    out |= by_mod.get(v, set()) or by_name.get(v[1], set())
                elif kind == "attr":
                    out |= by_name.get(v, set())
            return out
        for q, fn in defs:
            nid = "%s::%s" % (p, q)
            edges[nid] = resolve(_refs(fn.body, imports, mod_alias), q) - {nid}
        top = [n for n in tree.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
               and not _is_main_block(n)]
        edges["%s::<module>" % p] = resolve(_refs(top, imports, mod_alias))
        main = [n for n in tree.body if _is_main_block(n)]
        edges["%s::__main__" % p] = resolve(_refs(main, imports, mod_alias)) | {"%s::<module>" % p}
    return nodes, edges


def reach(edges, roots):
    seen, stack = set(), list(roots)
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x)
        stack.extend(edges.get(x, ()))
    return seen


GRAPH_PREFIXES = ("skills/analog-gmid-design/assets/", "workspaces/")
SOURCE_GLOBS = ("skills/analog-gmid-design/assets/", "workspaces/run_harness.py")


def _is_source(p):
    return (p.startswith("skills/analog-gmid-design/assets/") and p.count("/") == 3 and p.endswith(".py")) \
        or p == "workspaces/run_harness.py"


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
        # DESIGN-GAP: 계획 N4.2 V7 "Phase 3 전·후 두 벌" -- 어느 벌을 쓸지의 판정식이 없다. 두 벌의 합집합 중 head에
        # 파일이 있는 루트만 쓴다(Phase 3 전에는 MOD10 파일이 없어 전 벌만 남는다).
        roots = sorted({r for v in roots_cfg.values() for r in v if r.split("::")[0] in head})
        missing_roots = sorted({r for v in roots_cfg.values() for r in v} - set(roots))
        seen = reach(edges, roots)
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
    try:   # 로캘·PYTHONIOENCODING과 무관하게 출력을 UTF-8로(spec card 20260921-gate-output-utf8)
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
