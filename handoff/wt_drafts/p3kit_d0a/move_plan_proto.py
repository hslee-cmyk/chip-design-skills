"""D0a `plan` 시제품(측정 전용 -- 역할 산출물 아님, test-author·code-author·auditor 열람 금지(작성자 != 검증자)).

spec card 20260930-p3-move-plan-tool 계약 1·2·3(plan 쪽)만 옮겼다. `check`(계약 4)는 없다.
G1의 reachability.SourceIndex를 --root/tools/gates에서 import한다(G1 시제품 _drafts/g1_kit/install_proto.py가 설치된 복제본).
단위 AST는 G1 시제품의 내부 속성 `SourceIndex.mod(path).units[i][3]`에서 꺼낸다 -- G1 spec card 계약 0의 공개 표면
(`units`·`global_names`·`binding_origin`)에는 노드가 없다(키트 보고 '인터페이스 틈' 참조).

    python -B move_plan_proto.py plan --root R [--rev REV] --plan P --registry G --split F… [--keep F…] [--aliases JSON]
"""
import argparse
import ast
import fnmatch
import json
import os
import re
import subprocess
import sys

A = "skills/analog-gmid-design/assets/"
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
PYNAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\.py$")


def emit(obj, code):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.exit(code)


def err(msg):
    emit({"tool": "move_plan", "verdict": "ERROR", "error": msg}, 2)


class P(argparse.ArgumentParser):
    def error(self, message):
        err("인자 오류: " + message)


def git_show(root, rev, path):
    r = subprocess.run(["git", "-C", root, "show", "%s:%s" % (rev, path)], capture_output=True)
    if r.returncode != 0:
        err("git show %s:%s 실패" % (rev, path))
    return r.stdout.decode("utf-8")


def split_cells(line):
    s = line.strip()[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    out, cur, i = [], "", 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur += "|"
            i += 2
            continue
        if s[i] == "|":
            out.append(cur.strip())
            cur = ""
        else:
            cur += s[i]
        i += 1
    out.append(cur.strip())
    return out


def registry_rows(text):
    """`함수`와 `이관 목적지` 열을 모두 가진 표의 행 [(함수 셀, 목적지 셀)] -- `〃`는 위 행의 셀."""
    lines = text.replace("\r\n", "\n").split("\n")
    rows, i, found = [], 0, 0
    while i < len(lines):
        if lines[i].startswith("|") and i + 1 < len(lines) and re.match(r"^\|\s*:?-{3,}", lines[i + 1]):
            hdr = split_cells(lines[i])
            j = i + 2
            if "함수" in hdr and "이관 목적지" in hdr:
                found += 1
                cf, cd = hdr.index("함수"), hdr.index("이관 목적지")
                prev = ""
                while j < len(lines) and lines[j].startswith("|"):
                    c = split_cells(lines[j])
                    d = c[cd] if cd < len(c) else ""
                    if d.strip() == "〃":
                        d = prev
                    prev = d
                    rows.append((c[cf] if cf < len(c) else "", d))
                    j += 1
            else:
                while j < len(lines) and lines[j].startswith("|"):
                    j += 1
            i = j
            continue
        i += 1
    if not found:
        err("레지스트리 함수 표 없음")
    return rows


def main(argv):
    ap = P(prog="move_plan")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("plan")
    p.error = ap.error
    p.add_argument("--root", required=True)
    p.add_argument("--rev", default="HEAD")
    p.add_argument("--plan", required=True)
    p.add_argument("--registry", required=True)
    p.add_argument("--split", nargs="+", required=True)
    p.add_argument("--keep", nargs="*", default=[])
    p.add_argument("--aliases", default="{}")
    ns = ap.parse_args(argv)
    if ns.cmd != "plan":
        err("명령 없음(시제품은 plan만)")
    for f in ns.split + ns.keep:
        if not PYNAME.match(f):
            err("파일 인자 모양 아님: %r" % f)
    try:
        aliases = json.loads(ns.aliases)
        assert isinstance(aliases, dict)
    except Exception:
        err("--aliases JSON 파손")
    sys.path.insert(0, os.path.join(ns.root, "tools", "gates"))
    import import_layering as il
    import reachability as rch
    import role_paths as rp
    plan_text = git_show(ns.root, ns.rev, ns.plan)
    reg_text = git_show(ns.root, ns.rev, ns.registry)
    try:
        modtab = il.mod_table(plan_text)
        hdr, n310rows = rp.read_section_table(plan_text, "### N3.10 ")
    except rp.GateError as e:
        err("N3.10 표 파손: %s" % e)
    n310 = {s + ".py": k for s, k in modtab.items()}
    modfile = {k: f for f, k in n310.items()}
    alias_mod = {}
    for a_, f in aliases.items():
        if f not in n310:
            err("--aliases 값이 N3.10 파일이 아님: %r" % f)
        alias_mod[a_] = n310[f]
    reg = registry_rows(reg_text)
    files = rch.read_tree(ns.root, ns.rev, rch.SOURCE_GLOBS)
    idx = rch.SourceIndex(files)
    split = list(dict.fromkeys(ns.split))
    absent_split = [f for f in split if (A + f) not in files]
    present = [f for f in dict.fromkeys(split + sorted(n310)) if (A + f) in files]

    # ---- 단위
    U = {}            # uid -> dict
    by_bind = {}      # (file, name) -> uid
    for f in present:
        mod = idx.mod(A + f)
        for (kind, q, h, bound), raw in zip(idx.units(A + f), mod.units):
            node = raw[3]
            key = q if q else (",".join(sorted(bound)) if bound else "<stmt:%s>" % h[:12])
            uid = "%s::%s" % (f, key)
            if uid in U:
                uid = "%s#%s" % (uid, h[:8])
            U[uid] = {"file": f, "kind": kind, "key": key, "gn": q if q else "<stmt:%s>" % h[:12], "node": node,
                      "bound": set(bound)}
            for nm in bound:
                by_bind[(f, nm)] = uid

    def unit_of(origin):
        if origin and origin[0] == "def" and origin[1].startswith(A):
            return by_bind.get((origin[1][len(A):], origin[2]))
        return None

    # ---- 참조 R(u)
    R = {}
    for uid, u in U.items():
        refs = set()
        gn = idx.global_names(A + u["file"]).get(u["gn"], frozenset())
        for v in gn:
            w = unit_of(idx.binding_origin(A + u["file"], v))
            if w and w != uid:
                refs.add(w)
        for n in ast.walk(u["node"]):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
                o = idx.binding_origin(A + u["file"], n.value.id)
                if o[0] == "module" and o[1].startswith(A):
                    w = by_bind.get((o[1][len(A):], n.attr))
                    if w and w != uid:
                        refs.add(w)
        R[uid] = refs
    referencers = {uid: set() for uid in U}
    for uid, refs in R.items():
        for w in refs:
            referencers[w].add(uid)

    targets = {uid for uid, u in U.items() if u["file"] in split or u["file"] in n310}
    assign, rule = {}, {}
    # A-0
    for uid in targets:
        f = U[uid]["file"]
        if f in n310 and f not in split:
            assign[uid], rule[uid] = n310[f], "A-0"
    # A-1
    ci_id, ci_rep = hdr.index("ID"), hdr.index("대표 대상")
    a1 = {}
    for row in n310rows:
        k = int(re.fullmatch(r"MOD([0-9]+)", row[ci_id].strip()).group(1))
        for tok in re.findall(r"`([^`]*)`", row[ci_rep]):
            tok = tok.strip()
            if PYNAME.match(tok):
                if tok in split:
                    for uid in targets:
                        if U[uid]["file"] == tok and uid not in rule:
                            a1.setdefault(uid, set()).add(k)
                continue
            m = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)", tok)
            if m:
                tok = m.group(2)
            elif not (re.fullmatch(r"[A-Za-z_*][A-Za-z0-9_*]*", tok) and tok.count("*") <= 1 and tok != "*"):
                continue
            for uid in targets:
                if uid in rule:
                    continue
                if any(fnmatch.fnmatchcase(b, tok) for b in U[uid]["bound"]):
                    a1.setdefault(uid, set()).add(k)
    conflicts = []
    for uid, ks in a1.items():
        if len(ks) == 1:
            assign[uid], rule[uid] = next(iter(ks)), "A-1"
        else:
            conflicts.append({"unit": uid, "mods": sorted(modfile[k] for k in ks)})

    # ---- 레지스트리 열
    def cell_mods(cell):
        out = set()
        for t in IDENT.findall(cell):
            if t + ".py" in n310:
                out.add(n310[t + ".py"])
            elif t in alias_mod:
                out.add(alias_mod[t])
        return out
    regmods = {}
    for fcell, dcell in reg:
        toks = re.findall(r"`([^`]*)`", fcell)
        if not toks:
            continue
        name = toks[0].strip().split(".")[0]
        if not IDENT.fullmatch(name):
            continue
        regmods.setdefault(name, []).append(cell_mods(dcell))
    key_units = {}
    for uid in targets:
        key_units.setdefault(U[uid]["key"], []).append(uid)

    # ---- 레코드 클래스
    def is_dataclass_deco(d):
        d = d.func if isinstance(d, ast.Call) else d
        return (isinstance(d, ast.Name) and d.id == "dataclass") or (isinstance(d, ast.Attribute) and d.attr == "dataclass")
    rec = set()
    import builtins
    exc_names = {n for n in dir(builtins) if isinstance(getattr(builtins, n), type) and issubclass(getattr(builtins, n), BaseException)}
    changed = True
    while changed:
        changed = False
        for uid in targets:
            u = U[uid]
            if u["kind"] != "class" or uid in rec:
                continue
            n = u["node"]
            ok = any(is_dataclass_deco(d) for d in n.decorator_list)
            ok = ok or not any(isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)) for b in n.body)
            for b in n.bases:
                if isinstance(b, ast.Name):
                    o = idx.binding_origin(A + u["file"], b.id)
                    if o[0] == "builtin" and o[1] in exc_names:
                        ok = True
                    w = unit_of(o)
                    if w in rec:
                        ok = True
            if ok:
                rec.add(uid)
                changed = True

    cat = {}
    for uid in targets:
        if uid in rule:
            continue
        ms = regmods.get(U[uid]["key"])
        if uid in rec and (referencers[uid] - {uid}):
            cat[uid] = ("A-2", None)
        elif ms and any(len(m) >= 2 for m in ms):
            cat[uid] = ("A-3", min(min(m) for m in ms if len(m) >= 2))
        elif ms and any(len(m) == 1 for m in ms):
            m = [x for x in ms if len(x) == 1][0]
            assign[uid], rule[uid] = next(iter(m)), "A-4"
        else:
            cat[uid] = ("A-5", None)
    for it in range(200):
        moved = False
        for uid, (r_, lo) in cat.items():
            if r_ in ("A-2", "A-5"):
                cand = [assign[v] for v in referencers[uid] if v in assign and v != uid]
                if not cand:
                    continue
                k = min(cand)
            else:
                k = max([lo] + [assign[v] for v in R[uid] if v in assign])
            if assign.get(uid) != k:
                assign[uid], rule[uid] = k, r_
                moved = True
        if not moved:
            break
    unassigned = sorted(uid for uid in targets if uid not in assign and uid not in {c["unit"] for c in conflicts})

    upward = sorted({"%s -> %s" % (u_, v) for u_ in assign for v in R[u_] if v in assign and assign[u_] < assign[v]})
    # MOD 순환(SCC)
    g = {}
    for u_ in assign:
        for v in R[u_]:
            if v in assign and assign[u_] != assign[v]:
                g.setdefault(assign[u_], set()).add(assign[v])
    cycles = []
    sys.setrecursionlimit(10000)
    index, low, st, on, cnt = {}, {}, [], set(), [0]

    def sc(v):
        index[v] = low[v] = cnt[0]
        cnt[0] += 1
        st.append(v)
        on.add(v)
        for w in g.get(v, ()):
            if w not in index:
                sc(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = st.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                cycles.append(sorted(modfile[x] for x in comp))
    for v in list(g):
        if v not in index:
            sc(v)

    reexports = {}
    for f in split:
        if f not in present:
            continue
        per = {}
        for uid in targets:
            if U[uid]["file"] == f and uid in assign and modfile[assign[uid]] != f:
                per.setdefault(assign[uid], set()).update(U[uid]["bound"])
        if per:
            reexports[f] = ["from %s import %s" % (modfile[k][:-3], ", ".join(sorted(v))) for k, v in sorted(per.items())]
    order = [modfile[k] for k in sorted(set(assign.values()))]
    reg_mismatch = []
    for name, ms in regmods.items():
        for m in ms:
            if len(m) == 1:
                for uid in key_units.get(name, []):
                    if uid in assign and assign[uid] != next(iter(m)):
                        reg_mismatch.append({"unit": uid, "registry": modfile[next(iter(m))], "assigned": modfile[assign[uid]],
                                             "rule": rule[uid]})

    # ---- import_time_high
    sp = [n310[f] for f in split if f in n310]
    ith = []
    if sp:
        s = min(sp)
        futures = {f: "annotations" in idx.mod(A + f).futures for f in present}

        def it_names(node, fut):
            out = []

            def ann(e):
                if e is not None and not fut:
                    walk(e)

            def fn_head(n):
                for d in n.decorator_list:
                    walk(d)
                a = n.args
                for d in a.defaults + [x for x in a.kw_defaults if x is not None]:
                    walk(d)
                for x in a.posonlyargs + a.args + a.kwonlyargs + ([a.vararg] if a.vararg else []) + ([a.kwarg] if a.kwarg else []):
                    ann(x.annotation)
                ann(n.returns)

            def walk(n):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    fn_head(n)
                    return
                if isinstance(n, ast.Lambda):
                    for d in n.args.defaults + [x for x in n.args.kw_defaults if x is not None]:
                        walk(d)
                    return
                if isinstance(n, ast.ClassDef):
                    for d in n.decorator_list + n.bases + [k.value for k in n.keywords]:
                        walk(d)
                    for b in n.body:
                        walk(b)
                    return
                if isinstance(n, ast.AnnAssign):
                    if n.value is not None:
                        walk(n.value)
                    ann(n.annotation)
                    walk(n.target)
                    return
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                    out.append(n.id)
                for c in ast.iter_child_nodes(n):
                    walk(c)
            walk(node)
            return out

        for uid in sorted(assign):
            k = assign[uid]
            if k <= s:
                continue
            u = U[uid]
            for v in sorted(set(it_names(u["node"], futures[u["file"]]))):
                o = idx.binding_origin(A + u["file"], v)
                w = unit_of(o)
                if w and w in assign and s <= assign[w] < k:
                    ith.append({"unit": uid, "name": v, "origin": list(o), "origin_mod": modfile[assign[w]]})

    res = {"tool": "move_plan", "command": "plan", "verdict": None,
           "assignment": {uid: {"mod": modfile[assign[uid]], "rule": rule[uid]} for uid in sorted(assign)},
           "upward": upward, "cycles": cycles, "unassigned": unassigned, "conflicts": conflicts,
           "reexports": reexports, "order": order, "absent_split": absent_split, "reg_mismatch": reg_mismatch,
           "import_time_high": ith}
    bad = any(res[k] for k in ("upward", "cycles", "unassigned", "conflicts", "reg_mismatch", "import_time_high"))
    res["verdict"] = "FAIL" if bad else "PASS"
    emit(res, 1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
