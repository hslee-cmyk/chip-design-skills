"""F1/F2 작성 전 실측(측정 전용 -- 역할 산출물 아님, 작성자 != 검증자: test-author·code-author·auditor에게 건네지 않는다).

D0a `plan` 시제품(_drafts/p3kit_d0a/move_plan_proto.py d2f3da97…)의 배정부를 D0a spec card 계약 2 v8.4/v8.5 문언
(design 30 D-31)만 보고 다시 얹은 사본: 모듈 docstring 제외, A-0, A-1, A-2, A-3, A-4(칸 먼저 앉히기 + 승격, MOD7 상한),
A-K(--keep 잔여), A-5(승격·상한), A-6(R(u) 최댓값), A-7(고립 -> N3.10 파일 MOD), 단조 고정점. R(u) 최댓값은 N3.10 번호만.
`mod_imports`·`import_conflicts`는 내지 않는다(F1/F2 측정에 쓰지 않음). 단위마다 node 줄 번호(`line`)를 더 낸다(모의 생성기 짝짓기용).
G1 시제품(install_proto.py)이 설치된 복제본의 tools/gates에서 import한다.

    python -B plan_d31.py --root R [--rev REV] --plan P --registry G --split F… [--keep F…] [--aliases JSON]
"""
import argparse
import ast
import builtins
import fnmatch
import json
import os
import re
import subprocess
import sys

A = "skills/analog-gmid-design/assets/"
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
PYNAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\.py$")
KEEPNUM = 100
# F12_STMTKEY=hash: 레지스트리 행 짝짓기에서 문장 단위 키를 G1 시제품 `<stmt:해시>`로(D0b 키트·G1 키트 측정과 같은 판 -- 상수 행 7개 비대상)
STMTKEY_HASH = os.environ.get("F12_STMTKEY") == "hash"


def emit(obj, code):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.exit(code)


def err(msg):
    emit({"tool": "move_plan", "verdict": "ERROR", "error": msg}, 2)


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
    lines = text.replace("\r\n", "\n").split("\n")
    rows, i = [], 0
    while i < len(lines):
        if lines[i].startswith("|") and i + 1 < len(lines) and re.match(r"^\|\s*:?-{3,}", lines[i + 1]):
            hdr = split_cells(lines[i])
            j = i + 2
            if "함수" in hdr and "이관 목적지" in hdr:
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
    return rows


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--rev", default="HEAD")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--split", nargs="+", required=True)
    ap.add_argument("--keep", nargs="*", default=[])
    ap.add_argument("--aliases", default="{}")
    ns = ap.parse_args(argv)
    aliases = json.loads(ns.aliases)
    sys.path.insert(0, os.path.join(ns.root, "tools", "gates"))
    import import_layering as il
    import reachability as rch
    import role_paths as rp
    plan_text = git_show(ns.root, ns.rev, ns.plan)
    reg_text = git_show(ns.root, ns.rev, ns.registry)
    modtab = il.mod_table(plan_text)
    hdr, n310rows = rp.read_section_table(plan_text, "### N3.10 ")
    n310 = {s + ".py": k for s, k in modtab.items()}
    modfile = {k: f for f, k in n310.items()}
    keep = list(dict.fromkeys(ns.keep))
    for f in keep:
        modfile.setdefault(KEEPNUM + keep.index(f), f)
    alias_mod = {a_: n310[f] for a_, f in aliases.items()}
    reg = registry_rows(reg_text)
    files = rch.read_tree(ns.root, ns.rev, rch.SOURCE_GLOBS)
    idx = rch.SourceIndex(files)
    split = list(dict.fromkeys(ns.split))
    absent_split = [f for f in split if (A + f) not in files]
    present = [f for f in dict.fromkeys(split + sorted(n310)) if (A + f) in files]

    U, by_bind, docs = {}, {}, []
    for f in present:
        mod = idx.mod(A + f)
        tree = idx.tree(A + f)
        doc_node = None
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) \
                and isinstance(tree.body[0].value.value, str):
            doc_node = tree.body[0]
        for (kind, q, h, bound), raw in zip(idx.units(A + f), mod.units):
            node = raw[3]
            key = q if not q.startswith("<stmt:") else (",".join(sorted(bound)) if bound else q)
            uid = "%s::%s" % (f, key)
            if uid in U:
                uid = "%s#%s" % (uid, h[:8])
            if node is doc_node:
                docs.append(uid)
                continue
            U[uid] = {"file": f, "kind": kind, "key": key, "gn": q, "node": node, "bound": set(bound),
                      "line": node.lineno}
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
    for uid in targets:
        f = U[uid]["file"]
        if f in n310 and f not in split:
            assign[uid], rule[uid] = n310[f], "A-0"
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
    conf_units = {c["unit"] for c in conflicts}

    def cell_mods(cell):
        out = set()
        for t in IDENT.findall(cell):
            if t + ".py" in n310:
                out.add(n310[t + ".py"])
            elif t in n310:
                out.add(n310[t])
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
        key_units.setdefault(U[uid]["key"] if not (STMTKEY_HASH and U[uid]["kind"] == "stmt") else U[uid]["gn"], []).append(uid)

    def is_dataclass_deco(d):
        d = d.func if isinstance(d, ast.Call) else d
        return (isinstance(d, ast.Name) and d.id == "dataclass") or (isinstance(d, ast.Attribute) and d.attr == "dataclass")
    rec = set()
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
                    if unit_of(o) in rec:
                        ok = True
            if ok:
                rec.add(uid)
                changed = True

    # 범주(A-2·A-3·A-4·A-K·A-5/A-6) -- A-3·A-4는 칸 MOD에 먼저 앉힌다(단조)
    cat = {}
    for uid in targets:
        if uid in rule or uid in conf_units:
            continue
        ms = regmods.get(U[uid]["key"] if not (STMTKEY_HASH and U[uid]["kind"] == "stmt") else U[uid]["gn"])
        if uid in rec and (referencers[uid] - {uid}):
            cat[uid] = ("A-2", None)
        elif ms and any(len(m) >= 2 for m in ms):
            lo = min(min(m) for m in ms if len(m) >= 2)
            cat[uid] = ("A-3", lo)
            assign[uid], rule[uid] = lo, "A-3"
        elif ms and any(len(m) == 1 for m in ms):
            lo = next(iter([x for x in ms if len(x) == 1][0]))
            cat[uid] = ("A-4", lo)
            assign[uid], rule[uid] = lo, "A-4"
        elif U[uid]["file"] in keep:
            assign[uid], rule[uid] = KEEPNUM + keep.index(U[uid]["file"]), "A-K"
        else:
            cat[uid] = ("A-5", None)
    MOD7 = n310.get("stick_diagram.py")   # 상한 비교용 번호(N3.10 '레이아웃만' 행) -- 이름은 계획 표에서 읽은 값
    for row in n310rows:
        if "레이아웃만" in row[hdr.index("책임")] if "책임" in hdr else False:
            MOD7 = int(row[ci_id].strip()[3:])

    def rmax(uid):
        vals = [assign[v] for v in R[uid] if v in assign and assign[v] < KEEPNUM]
        return max(vals) if vals else None

    def lifted(base, uid, cap=True):
        m = rmax(uid)
        k = base if m is None else max(base, m)
        if cap and k == MOD7 and base != MOD7:
            return base
        return k

    def fixpoint():
        for it in range(500):
            moved = False
            for uid, (r_, lo) in sorted(cat.items()):
                if r_ in ("A-2", "A-5"):
                    cand = [assign[v] for v in referencers[uid] if v in assign and v != uid and assign[v] < KEEPNUM]
                    if cand:
                        k, rr = lifted(min(cand), uid), r_
                    elif r_ == "A-5" and not (referencers[uid] - {uid}):
                        m = rmax(uid)
                        if m is None:
                            continue
                        k, rr = m, "A-6"
                    else:
                        continue
                elif r_ == "A-3":
                    k, rr = lifted(lo, uid, cap=False), "A-3"
                else:
                    k, rr = lifted(lo, uid), "A-4"
                if uid not in assign or k > assign[uid]:
                    assign[uid], rule[uid] = k, rr
                    moved = True
            if not moved:
                return it
        return -1
    fixpoint()
    a7 = [uid for uid in targets if uid not in assign and uid not in conf_units and U[uid]["file"] in n310]
    for uid in a7:
        assign[uid], rule[uid] = n310[U[uid]["file"]], "A-7"
        cat.pop(uid, None)
    if a7:
        fixpoint()
    unassigned = sorted(uid for uid in targets if uid not in assign and uid not in conf_units)

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
    reg_mismatch = []
    for name, ms in regmods.items():
        for m in ms:
            if len(m) == 1:
                for uid in key_units.get(name, []):
                    if uid in assign and assign[uid] != next(iter(m)):
                        reg_mismatch.append({"unit": uid, "registry": modfile[next(iter(m))], "assigned": modfile[assign[uid]],
                                             "rule": rule[uid]})
    mod7_outside = sorted(uid for uid in assign if assign[uid] == MOD7 and U[uid]["file"] != modfile[MOD7])
    rc = {}
    for uid in assign:
        rc[rule[uid]] = rc.get(rule[uid], 0) + 1
    per_mod = {}
    for uid in assign:
        per_mod[modfile[assign[uid]]] = per_mod.get(modfile[assign[uid]], 0) + 1
    res = {"tool": "move_plan(d31-sim)", "command": "plan",
           "assignment": {uid: {"mod": modfile[assign[uid]], "rule": rule[uid], "line": U[uid]["line"],
                                "kind": U[uid]["kind"], "bound": sorted(U[uid]["bound"])} for uid in sorted(assign)},
           "upward": upward, "cycles": cycles, "unassigned": unassigned, "conflicts": conflicts,
           "reexports": reexports, "absent_split": absent_split, "reg_mismatch_n": len(reg_mismatch),
           "mod7_outside": mod7_outside, "docstrings": docs, "rule_counts": rc, "per_mod": per_mod, "n": len(assign)}
    emit(res, 0)


if __name__ == "__main__":
    main(sys.argv[1:])
