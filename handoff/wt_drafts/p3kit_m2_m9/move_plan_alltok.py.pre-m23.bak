# p3fq_kit copy of p3kit_m1/move_plan_sim.py + MP_REG_ALLTOK variant (measure only)
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




# ============================================================================================
# scratch extension (C:/g200, M1 card drafting -- measure only, NOT a role artifact):
#   plan  = D0a contract 2 v8.4/v8.5 wording re-implemented on top of proto d2f3da97 (D-31 rules, mod_imports, import_conflicts)
#   check = D0a contract 4 wording (move-set, move-rejected, changed, rebind, future, import-dup, stmt-order, lost, order, shim, cache)
# ============================================================================================

def load_gates(root):
    sys.path.insert(0, os.path.join(root, "tools", "gates"))
    import import_layering as il
    import reachability as rch
    import role_paths as rp
    return il, rch, rp


def is_docstring_stmt(tree, node):
    return (bool(tree.body) and node is tree.body[0] and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str))


MOD7 = 7


def compute_plan(root, rev, ns, aliases, il, rch, rp, files=None, idx=None):
    plan_text = git_show(root, rev, ns.plan)
    reg_text = git_show(root, rev, ns.registry)
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
    if files is None:
        files = rch.read_tree(root, rev, rch.SOURCE_GLOBS)
    if idx is None:
        idx = rch.SourceIndex({k: v for k, v in files.items() if rch._is_source(k)})
    split = list(dict.fromkeys(ns.split))
    keep = list(dict.fromkeys(ns.keep))
    absent_split = [f for f in split if (A + f) not in files]
    present = [f for f in dict.fromkeys(split + sorted(n310)) if (A + f) in files]
    KEEPNUM = {}
    for i_, f_ in enumerate(keep):
        KEEPNUM[f_] = 1000 + i_
        modfile[1000 + i_] = f_

    U, by_bind, g1key = {}, {}, {}
    for f in present:
        mod = idx.mod(A + f)
        tree = idx.tree(A + f)
        for (kind, q, h, bound), raw in zip(idx.units(A + f), mod.units):
            node = raw[3]
            if kind == "stmt" and is_docstring_stmt(tree, node):
                continue                                   # v8.4: module docstring is not a unit to assign
            key = q if (kind != "stmt" or os.environ.get("MP_STMT_KEY", "hash") == "hash") else (",".join(sorted(bound)) if bound else q)
            uid = "%s::%s" % (f, key)
            if uid in U:
                uid = "%s#%s" % (uid, h[:8])
            U[uid] = {"file": f, "kind": kind, "key": key, "gn": q, "node": node, "bound": set(bound), "hash": h}
            g1key[uid] = q
            for nm in bound:
                by_bind[(f, nm)] = uid

    def unit_of(origin):
        if origin and origin[0] == "def" and origin[1].startswith(A):
            return by_bind.get((origin[1][len(A):], origin[2]))
        return None

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
    for uid in targets:                                      # A-0
        f = U[uid]["file"]
        if f in n310 and f not in split:
            assign[uid], rule[uid] = n310[f], "A-0"
    ci_id, ci_rep = hdr.index("ID"), hdr.index("대표 대상")   # A-1
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
    conflict_units = {c["unit"] for c in conflicts}

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
        # p3fq variant (measure only): every backtick identifier token of the function cell names a unit (`A`/`B` rows)
        _names = toks if os.environ.get("MP_REG_ALLTOK") == "1" else toks[:1]
        for _t in dict.fromkeys(x.strip().split(".")[0] for x in _names):
            if IDENT.fullmatch(_t):
                regmods.setdefault(_t, []).append(cell_mods(dcell))
    key_units = {}
    for uid in targets:
        key_units.setdefault(U[uid]["key"], []).append(uid)

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
        if uid in rule or uid in conflict_units:
            continue
        ms = regmods.get(U[uid]["key"])
        others = referencers[uid] - {uid}
        if uid in rec and others:
            cat[uid] = ("A-2", None)
        elif ms and any(len(m) >= 2 for m in ms):
            lo = min(min(m) for m in ms if len(m) >= 2)
            cat[uid] = ("A-3", lo)
            assign[uid], rule[uid] = lo, "A-3"                    # seat first (monotone)
        elif ms and any(len(m) == 1 for m in ms):
            c = next(iter([x for x in ms if len(x) == 1][0]))
            cat[uid] = ("A-4", c)
            assign[uid], rule[uid] = c, "A-4"                     # seat first (monotone)
        elif U[uid]["file"] in KEEPNUM:
            assign[uid], rule[uid] = KEEPNUM[U[uid]["file"]], "A-K"
        elif others:
            cat[uid] = ("A-5", None)
        else:
            cat[uid] = ("A-6", None)

    def maxR(uid):
        ks = [assign[v] for v in R[uid] if v in assign and v != uid and assign[v] < 1000]
        return max(ks) if ks else None

    def step():
        moved = False
        for uid in sorted(cat):
            r_, lo = cat[uid]
            mr = maxR(uid)
            if r_ in ("A-2", "A-5"):
                cand = [assign[v] for v in referencers[uid] if v in assign and v != uid]
                if not cand:
                    continue
                base = min(cand)
                k = base if mr is None else max(base, mr)
                if k == MOD7 and base != MOD7:
                    k = base
            elif r_ == "A-3":
                k = lo if mr is None else max(lo, mr)
            elif r_ == "A-4":
                k = lo if mr is None else max(lo, mr)
                if k == MOD7 and lo != MOD7:
                    k = lo
            else:                                   # A-6
                if mr is None:
                    continue
                k = mr
            cur = assign.get(uid)
            if cur is None or k > cur:
                assign[uid], rule[uid] = k, r_
                moved = True
        return moved

    for outer in range(100):
        for it in range(500):
            if not step():
                break
        newly = False
        for uid in sorted(targets):                    # A-7
            if uid in assign or uid in conflict_units:
                continue
            f = U[uid]["file"]
            if f in n310:
                assign[uid], rule[uid] = n310[f], "A-7"
                cat.pop(uid, None)
                newly = True
        if not newly:
            break
    unassigned = sorted(uid for uid in targets if uid not in assign and uid not in conflict_units)
    PLAN_STATE = {"U": U, "R": R, "assign": assign, "rule": rule, "modfile": modfile, "n310": n310, "g1key": g1key,
                  "idx": idx, "files": files, "split": split, "keep": keep, "present": present, "by_bind": by_bind,
                  "regmods": regmods, "key_units": key_units, "conflicts": conflicts, "unassigned": unassigned,
                  "absent_split": absent_split, "targets": targets}
    return finish_plan(PLAN_STATE)


def finish_plan(S):
    U, R, assign, rule, modfile, n310 = S["U"], S["R"], S["assign"], S["rule"], S["modfile"], S["n310"]
    idx, files, split, present, by_bind = S["idx"], S["files"], S["split"], S["present"], S["by_bind"]
    targets = S["targets"]

    def unit_of(origin):
        if origin and origin[0] == "def" and origin[1].startswith(A):
            return by_bind.get((origin[1][len(A):], origin[2]))
        return None

    upward = sorted({"%s -> %s" % (u_, v) for u_ in assign for v in R[u_] if v in assign and assign[u_] < assign[v]})
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
    order = [modfile[k] for k in sorted(set(assign.values())) if k < 1000]
    reg_mismatch = []
    for name, ms in S["regmods"].items():
        for m in ms:
            if len(m) == 1:
                for uid in S["key_units"].get(name, []):
                    if uid in assign and assign[uid] != next(iter(m)):
                        reg_mismatch.append({"unit": uid, "registry": modfile[next(iter(m))], "assigned": modfile[assign[uid]],
                                             "rule": rule[uid]})

    futures = {f: idx.mod(A + f).futures for f in present}
    sp = [n310[f] for f in split if f in n310]
    ith = []
    if sp:
        s = min(sp)

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
            if k <= s or k >= 1000:
                continue
            u = U[uid]
            for v in sorted(set(it_names(u["node"], "annotations" in futures[u["file"]]))):
                o = idx.binding_origin(A + u["file"], v)
                w = unit_of(o)
                if w and w in assign and s <= assign[w] < k:
                    ith.append({"unit": uid, "name": v, "origin": list(o), "origin_mod": modfile[assign[w]]})

    # ---- mod_imports / import_conflicts (D-30)
    ADIR = A.rstrip("/")
    mod_imports, import_conflicts = {}, []
    for k in sorted({x for x in assign.values() if x < 1000}):
        kf = modfile[k]
        Uk = [uid for uid in sorted(assign) if assign[uid] == k and U[uid]["file"] != kf]
        if not Uk:
            continue
        need, bad = {}, []
        for uid in Uk:
            u = U[uid]
            for v in sorted(idx.global_names(A + u["file"]).get(u["gn"], frozenset())):
                o = idx.binding_origin(A + u["file"], v)
                if o[0] == "def":
                    f = o[1][len(A):] if o[1].startswith(A) else None
                    w = by_bind.get((f, o[2])) if f else None
                    if w is not None and w in assign:
                        if assign[w] == k:
                            continue
                        spec = ("from", modfile[assign[w]][:-3], o[2])
                    elif f is not None and "/" not in f:
                        spec = ("from", f[:-3], o[2])
                    else:
                        bad.append((v, uid, o))
                        continue
                elif o[0] == "ext":
                    if o[1] != ADIR:
                        bad.append((v, uid, o))
                        continue
                    spec = ("from", o[2], o[3])
                elif o[0] == "module":
                    spec = ("import", o[1][len(A):-3] if o[1].startswith(A) else o[1], None)
                elif o[0] == "ext-module":
                    if o[1] != ADIR:
                        bad.append((v, uid, o))
                        continue
                    spec = ("import", o[2], None)
                elif o[0] in ("builtin", "module-identity", "file-dir", "unbound"):
                    continue
                else:
                    bad.append((v, uid, o))
                    continue
                need.setdefault(v, {}).setdefault(spec, []).append((uid, [str(x) for x in o]))
        for v, specs in sorted(need.items()):
            if len(specs) > 1:
                import_conflicts.append({"mod": kf, "name": v, "origins": [{"unit": x[0][0], "origin": x[0][1]} for x in specs.values()]})
        for v, uid, o in bad:
            import_conflicts.append({"mod": kf, "name": v, "origins": [{"unit": uid, "origin": [str(x) for x in o]}]})
        fs = {}
        for uid in Uk:
            fs.setdefault(U[uid]["file"], sorted(futures[U[uid]["file"]]))
        if (A + kf) in files and idx.mod(A + kf) is not None:
            fs[kf] = sorted(idx.mod(A + kf).futures)
        if len({tuple(x) for x in fs.values()}) > 1:
            import_conflicts.append({"mod": kf, "name": "__future__", "origins": [{"file": f, "features": x} for f, x in sorted(fs.items())]})
        lines = []
        fut = sorted(set().union(*[set(futures[U[uid]["file"]]) for uid in Uk]))
        if fut:
            lines.append("from __future__ import %s" % ", ".join(fut))
        frm, imp = {}, []
        for v, specs in sorted(need.items()):
            if len(specs) != 1:
                continue
            (kind, m, n), = specs.keys()
            if kind == "from":
                frm.setdefault(m, []).append(n if n == v else "%s as %s" % (n, v))
            else:
                imp.append(("import %s" % m) if m == v else ("import %s as %s" % (m, v)))
        for m in sorted(frm):
            lines.append("from %s import %s" % (m, ", ".join(sorted(frm[m]))))
        lines += sorted(set(imp))
        mod_imports[kf] = lines

    rule_counts = {}
    for uid in assign:
        rule_counts[rule[uid]] = rule_counts.get(rule[uid], 0) + 1
    res = {"tool": "move_plan", "command": "plan", "verdict": None,
           "assignment": {uid: {"mod": modfile[assign[uid]], "rule": rule[uid]} for uid in sorted(assign)},
           "upward": upward, "cycles": cycles, "unassigned": S["unassigned"], "conflicts": S["conflicts"],
           "reexports": reexports, "order": order, "absent_split": S["absent_split"], "reg_mismatch": reg_mismatch,
           "import_time_high": ith, "mod_imports": mod_imports, "import_conflicts": import_conflicts,
           "rule_counts_sim": rule_counts}
    bad = any(res[k] for k in ("upward", "cycles", "unassigned", "conflicts", "reg_mismatch", "import_time_high", "import_conflicts"))
    res["verdict"] = "FAIL" if bad else "PASS"
    S["futures"] = futures
    return res, S


def _ukey(k, q, h):
    return q if q else "<stmt:%s>" % h[:12]


def _is_main(n):
    return (isinstance(n, ast.If) and isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Name)
            and n.test.left.id == "__name__")


def compute_check(root, ns, aliases, il, rch, rp):
    bfiles = rch.read_tree(root, ns.base, rch.SOURCE_GLOBS)
    hfiles = rch.read_tree(root, ns.head, rch.SOURCE_GLOBS)
    B = rch.SourceIndex({k: v for k, v in bfiles.items() if rch._is_source(k)})
    H = rch.SourceIndex({k: v for k, v in hfiles.items() if rch._is_source(k)})
    pres, S = compute_plan(root, ns.base, ns, aliases, il, rch, rp, files=bfiles, idx=B)
    U, n310, g1key = S["U"], S["n310"], S["g1key"]
    mv = rch.moved_defs(B, H)
    card = ns.card
    if card != "ALL" and card not in n310:
        err("--card가 N3.10 파일이 아님: %r" % card)
    assigned, assigned_dest = set(), {}
    for uid, a in pres["assignment"].items():
        f = U[uid]["file"]
        gid = "%s%s::%s" % (A, f, g1key[uid])
        assigned_dest[gid] = A + a["mod"]
        if a["mod"] == f:
            continue
        if card == "ALL" or a["mod"] == card:
            assigned.add(gid)
    allow = set(ns.allow_changed or [])
    F = {k: [] for k in ("move-set", "move-rejected", "changed", "lost", "rebind", "future", "import-dup", "stmt-order",
                         "order", "shim", "cache")}
    moved_src = {}
    for huid, buid in mv["units"].items():
        moved_src[buid] = huid
        dest = huid.split("::")[0]
        want = (A + card) if card != "ALL" else assigned_dest.get(buid)
        if dest != want:
            F["move-set"].append({"unit": buid, "to": huid, "why": "destination differs from assignment"})
    for x in sorted(set(moved_src) - assigned):
        F["move-set"].append({"unit": x, "why": "moved but not assigned to this card"})
    for x in sorted(assigned - set(moved_src)):
        F["move-set"].append({"unit": x, "why": "assigned but not moved"})
    for k_, v in sorted(mv["rejected"].items()):
        F["move-rejected"].append(dict(unit=k_, **v))
    bunits = {p: {(k, q, h) for (k, q, h, b) in B.units(p)} for p in B.paths()}
    hunits = {p: {(k, q, h) for (k, q, h, b) in H.units(p)} for p in H.paths()}
    changed_ids = set()
    for p in H.paths():
        for (k, q, h, b) in H.units(p):
            huid = "%s::%s" % (p, q)
            if huid in mv["units"] or (k, q, h) in bunits.get(p, set()) or huid in allow:
                continue
            F["changed"].append({"unit": huid, "kind": k})
            changed_ids.add((p, k, q))
    for huid, buid in mv["units"].items():
        p_h, q = huid.split("::", 1)
        p_b = buid.split("::", 1)[0]
        hn = [n for (k, qq, h, n, b) in H.mod(p_h).units if qq == q and k == "class"]
        if not hn:
            continue
        bn = [n for (k, qq, h, n, b) in B.mod(p_b).units if qq == q and k == "class"]
        hd, bd = {}, {}
        for qq, fn in rch.iter_defs(ast.Module(body=hn, type_ignores=[])):
            hd.setdefault(qq, []).append(rch.def_hash(fn))
        for qq, fn in rch.iter_defs(ast.Module(body=bn, type_ignores=[])):
            bd.setdefault(qq, []).append(rch.def_hash(fn))
        for qq in sorted(set(hd) | set(bd)):
            if hd.get(qq) != bd.get(qq):
                F["changed"].append({"unit": "%s::%s" % (p_h, qq), "kind": "method-in-moved-class"})
    for p in B.paths():
        for (k, q, h, b) in B.units(p):
            buid = "%s::%s" % (p, q)
            if buid in moved_src or (k, q, h) in hunits.get(p, set()) or (p, k, q) in changed_ids:
                continue
            F["lost"].append({"unit": buid, "kind": k})
    moved_names = {}
    for huid, buid in mv["units"].items():
        p_h, p_b = huid.split("::")[0], buid.split("::")[0]
        for (k, q, h, n, b) in H.mod(p_h).units:
            if "%s::%s" % (p_h, _ukey(k, q, h)) == huid:
                for nm in b:
                    moved_names[("def", p_h, nm)] = ("def", p_b, nm)
    for p in H.paths():
        gn = H.global_names(p)
        for (k, q, h, b) in H.units(p):
            if (p, k, q) in changed_ids:
                continue
            huid = "%s::%s" % (p, q)
            pb = mv["units"][huid].split("::")[0] if huid in mv["units"] else p
            if B.mod(pb) is None:
                continue
            for v in sorted(gn.get(q, ())):
                ch, cb = H.binding_origin(p, v), B.binding_origin(pb, v)
                if ch == cb or moved_names.get(ch) == cb:
                    continue
                F["rebind"].append({"unit": huid, "name": v, "base": [str(x) for x in cb], "head": [str(x) for x in ch]})
    dests = {}
    for huid, buid in mv["units"].items():
        dests.setdefault(huid.split("::")[0], set()).add(buid.split("::")[0])
    for d, srcs in sorted(dests.items()):
        need = set().union(*[set(B.mod(s_).futures) for s_ in srcs])
        if not need <= set(H.mod(d).futures):
            F["future"].append({"file": d, "need": sorted(need), "have": sorted(H.mod(d).futures)})
    cards = [card] if card != "ALL" else sorted(f for f in n310 if (A + f) in hfiles)
    for cf in cards:
        p = A + cf
        m = H.mod(p)
        if m is None:
            continue
        for nm, bs in sorted(m.bindings.items()):
            if len(bs) > 1 and all(b[0] in ("from", "import") for b in bs):
                F["import-dup"].append({"file": p, "name": nm, "n": len(bs)})
        k = n310[cf]
        for n in ast.walk(m.tree):
            mods_ = []
            if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
                mods_ = [n.module.split(".")[0]]
            elif isinstance(n, ast.Import):
                mods_ = [a.name.split(".")[0] for a in n.names]
            for mm in mods_:
                f = mm + ".py"
                if (A + f) not in hfiles:
                    continue
                if f in n310:
                    if n310[f] >= k and f != cf:
                        F["order"].append({"file": p, "imports": f, "line": n.lineno})
                elif f in S["split"]:
                    F["order"].append({"file": p, "imports": f, "line": n.lineno})
    groups = {}
    for huid, buid in mv["units"].items():
        if "<stmt:" not in huid:
            continue
        p_h, p_b = huid.split("::")[0], buid.split("::")[0]
        hpos = [i for i, (k, q, h, n, b) in enumerate(H.mod(p_h).units) if "%s::%s" % (p_h, _ukey(k, q, h)) == huid]
        bpos = [i for i, (k, q, h, n, b) in enumerate(B.mod(p_b).units) if "%s::%s" % (p_b, _ukey(k, q, h)) == buid]
        groups.setdefault((p_b, p_h), []).append((bpos[0] if bpos else -1, hpos[0] if hpos else -1, huid))
    for key, lst in groups.items():
        lst.sort()
        hs = [x[1] for x in lst]
        if hs != sorted(hs):
            F["stmt-order"].append({"from": key[0], "to": key[1]})
    for f in S["split"]:
        p = A + f
        if p not in hfiles:
            continue
        bt = ast.parse(bfiles[p]) if p in bfiles else ast.Module(body=[], type_ignores=[])
        ht = ast.parse(hfiles[p])
        cnt = {}
        for n in bt.body:
            cnt[ast.dump(n)] = cnt.get(ast.dump(n), 0) + 1
        reex = set()
        for n in ht.body:
            d = ast.dump(n)
            if cnt.get(d, 0) > 0:
                cnt[d] -= 1
                continue
            if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module and (n.module + ".py") in n310:
                reex |= {(a.asname or a.name) for a in n.names}
            else:
                F["shim"].append({"file": p, "why": "(a) new top-level stmt is not a MOD re-export", "line": n.lineno})
        nonmod = f not in S["keep"] and f not in n310
        body_left = [n for i, n in enumerate(ht.body) if not (i == 0 and isinstance(n, ast.Expr)) and not isinstance(n, (ast.Import, ast.ImportFrom))]
        if nonmod and not body_left:
            for i, n in enumerate(ht.body):
                if i == 0 and isinstance(n, ast.Expr):
                    continue
                if isinstance(n, ast.ImportFrom) and (n.module == "__future__" or (n.level == 0 and n.module and (n.module + ".py") in n310)):
                    continue
                F["shim"].append({"file": p, "why": "(b) complete shim has a non re-export statement", "line": n.lineno})
        if card != "ALL":
            moved_here = set()
            for huid, buid in mv["units"].items():
                if buid.split("::")[0] == p:
                    ph = huid.split("::")[0]
                    for (k, q, h, n, b) in H.mod(ph).units:
                        if "%s::%s" % (ph, _ukey(k, q, h)) == huid:
                            moved_here |= set(b)
            if reex != moved_here:
                F["shim"].append({"file": p, "why": "(c) re-export names != names moved out", "extra": sorted(reex - moved_here),
                                  "missing": sorted(moved_here - reex)})
        for nm in sorted(reex):
            o_s = H.binding_origin(p, nm)
            if o_s[0] != "def" or not o_s[1].startswith(A) or (o_s[1][len(A):] not in n310):
                F["shim"].append({"file": p, "why": "(c) re-export origin is not a MOD def", "name": nm, "origin": [str(x) for x in o_s]})
        if [ast.dump(n) for n in bt.body if _is_main(n)] != [ast.dump(n) for n in ht.body if _is_main(n)]:
            F["shim"].append({"file": p, "why": "main block changed"})
    for p in H.paths():
        if not p.startswith(A):
            continue
        for (k, q, h, n, b) in H.mod(p).units:
            if k != "stmt":
                continue
            tgt, val = None, None
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                tgt, val = n.targets[0].id, n.value
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
                tgt, val = n.target.id, n.value
            if not tgt or "cache" not in tgt.lower():
                continue
            empty = (isinstance(val, ast.Dict) and not val.keys) or (isinstance(val, ast.Call) and isinstance(val.func, ast.Name)
                                                                      and val.func.id == "dict" and not val.args and not val.keywords)
            if not empty:
                continue
            for p2 in H.paths():
                if not p2.startswith(A) or p2 == p:
                    continue
                gn = H.global_names(p2)
                for (k2, q2, h2, b2) in H.units(p2):
                    if tgt in gn.get(q2, ()) and H.binding_origin(p2, tgt) == ("def", p, tgt):
                        F["cache"].append({"cache": "%s::%s" % (p, tgt), "user": "%s::%s" % (p2, q2)})
    res = {"tool": "move_plan", "command": "check", "verdict": None, "assigned": sorted(assigned),
           "moved_units": mv["units"], "moved_defs": mv["defs"], "findings": F}
    res["verdict"] = "FAIL" if any(F.values()) else "PASS"
    return res


def main2(argv):
    ap = P(prog="move_plan")
    sub = ap.add_subparsers(dest="cmd")
    for c in ("plan", "check"):
        p = sub.add_parser(c)
        p.error = ap.error
        p.add_argument("--root", required=True)
        if c == "plan":
            p.add_argument("--rev", default="HEAD")
        else:
            p.add_argument("--base", required=True)
            p.add_argument("--head", required=True)
            p.add_argument("--card", required=True)
            p.add_argument("--allow-changed", nargs="*", default=[])
        p.add_argument("--plan", required=True)
        p.add_argument("--registry", required=True)
        p.add_argument("--split", nargs="+", required=True)
        p.add_argument("--keep", nargs="*", default=[])
        p.add_argument("--aliases", default="{}")
    ns = ap.parse_args(argv)
    if ns.cmd not in ("plan", "check"):
        err("no command")
    for f in ns.split + ns.keep:
        if not PYNAME.match(f):
            err("file arg shape: %r" % f)
    try:
        aliases = json.loads(ns.aliases)
        assert isinstance(aliases, dict)
    except Exception:
        err("--aliases JSON broken")
    il, rch, rp = load_gates(ns.root)
    if ns.cmd == "plan":
        res, _ = compute_plan(ns.root, ns.rev, ns, aliases, il, rch, rp)
    else:
        res = compute_check(ns.root, ns, aliases, il, rch, rp)
    emit(res, 1 if res["verdict"] == "FAIL" else 0)


if __name__ == "__main__":
    main2(sys.argv[1:])
