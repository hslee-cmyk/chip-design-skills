"""B26-1 v4 V3 대상 분류 (review2_b26_1 B1 재현 + 사이트 10·14를 B35로 넘긴 v4 head).

정의(범위 정책 card 20260930-v3-changed-stmt-scope 계약 1):
  N2b = T1·T2·T3(b)·T4·T5·T6(가)  (v3_scope_classify.DEFS["N2b"])
  N2w = N2b + T6(나) -- 복합문은 '자기 필드'에서 읽을 때만, 몫 = 자기 필드 (card 규칙 = review2의 'own')  (v3_scope_widen)
  N2d = N2b + T6(나) deep 변형(복합문의 하위 블록에서 읽어도 그 복합문 몫 + 하위의 읽는 단순문) -- review2의 'deep', 비교용
출력: C:/g87/out/classify_<mode>.txt(사람용, append), targets_<mode>.json(대상 변이 행)
"""
import ast, json, re, subprocess, sys

sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26pre_scripts")
import v3_scope_widen as W      # noqa: E402
import b26v4_head as H          # noqa: E402
V, S, mc, rch = W.V, W.S, W.mc, W.rch

REPO = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
OUT = "C:/g87/out/"
TAG = ""


def log(path, *a):
    s = " ".join(str(x) for x in a)
    print(s)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


def t6deep(bfn, hfn):
    M = W.MatchW()
    M.block(bfn.body, hfn.body, "", "body")
    pn = {p: n for n, p in mc._path_nodes(hfn)}
    simple, comp = set(), set()

    def visit(node, p, names):
        c = V.is_compound(node)
        _s, ld_own = V.names(node, own_only=c)
        if not c:
            if ld_own & names:
                simple.add(p)
            return
        _s2, ld_all = V.names(node, own_only=False)
        if not (ld_all & names):
            return
        comp.add(p)
        for f in V.BLOCK:
            lst = getattr(node, f, None)
            if isinstance(lst, list):
                for k, s in enumerate(lst):
                    if isinstance(s, (ast.stmt, ast.ExceptHandler, ast.match_case)):
                        visit(s, V.jp(p, f, k), names)

    for owner, field, j, strict, names in M.sites:
        if not names:
            continue
        own_node = pn[owner] if owner else hfn
        lst = getattr(own_node, field, None) or []
        loop = field == "body" and isinstance(own_node, W.LOOPS)
        for k, s in enumerate(lst):
            if loop:
                if strict and k == j:
                    continue
            elif (k <= j) if strict else (k < j):
                continue
            if not isinstance(s, (ast.stmt, ast.ExceptHandler, ast.match_case)):
                continue
            visit(s, V.jp(owner, field, k), names)
    return sorted(simple), sorted(comp)


def classify_all(bfn, hfn, src, hmap, ex):
    rows, info = W.classify_w(bfn, hfn, src, hmap, ex)
    ds, dc = t6deep(bfn, hfn)
    for t in rows:
        if t["op"] == "early_return":
            t["T6d"] = False
            continue
        np_ = V.node_path(t["op"], t["path"])
        hd = t["op"] in ("stmt_delete", "except_body_delete")
        t["T6d"] = any(V.under(np_, q) for q in ds) or any(V.own(np_, q) or (hd and np_ == q) for q in dc)
        t["N2b"] = V.DEFS["N2b"](t)
        t["N2w"] = t["N2b"] or t["T6w"]
        t["N2d"] = t["N2w"] or t["T6d"]
    for t in rows:
        if t["op"] == "early_return":
            t["N2b"] = V.DEFS["N2b"](t)
            t["N2w"] = t["N2d"] = t["N2b"]
    return rows, info


def git_show(rev, path):
    return subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (rev, path)], capture_output=True, check=True).stdout.decode("utf-8")


def compose(m1, m2):
    return {k: m2.get(v) for k, v in m1.items() if m2.get(v) is not None}


def main(mode):
    txt = OUT + TAG + "classify_%s.txt" % mode
    open(txt, "w").close()
    head, _ = H.build_head(mode)
    base = S.BASEF
    with open(OUT + "executed_lines.json", encoding="utf-8") as fh:
        EXEC = json.load(fh)
    dur = V.durations()
    nodes, edges = rch.build_graph(head)
    tests = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
             and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
    allrows = []
    per = []
    for path in sorted(p for p in head if head[p] != base.get(p) and rch._is_source(p)):
        bsrc, hsrc = base.get(path), head[path]
        bdefs = dict(rch.iter_defs(ast.parse(bsrc))) if bsrc else {}
        # head 줄 -> b1 줄 -> 7535799 줄(실행 줄 기록이 7535799 사본 기준)
        old = git_show("7535799", path)
        hmap = compose(V.line_map(bsrc, hsrc), V.line_map(old, bsrc))
        ex = set(EXEC.get(path.split("/")[-1], []))
        for q, hfn in mc.changed_defs(bsrc, hsrc):
            inv = mc.inventory(edges, "%s::%s" % (path, q), tests)
            invs = sum(dur.get(x, 0.0) for x in inv)
            if q in bdefs:
                rows, info = classify_all(bdefs[q], hfn, hsrc, hmap, ex)
            else:
                rows = []
                for o, p, _ in mc.mutants(hfn, hsrc):
                    rows.append(dict(op=o, path=p, unexec=None, N2b=True, N2w=True, N2d=True, new_def=True))
            for t in rows:
                t.update(file=path, def_=q, inv=len(inv), inv_s=invs,
                         id="%s:%s:%s:%s" % (rch.module_name(path), q, t["op"], t["path"]))
            allrows += rows
            per.append((path.split("/")[-1] + "::" + q, len(rows), sum(t["N2b"] for t in rows), sum(t["N2w"] for t in rows),
                        sum(t["N2d"] for t in rows), len(inv), round(invs, 1)))
    per.sort(key=lambda r: -r[1])
    log(txt, "== mode %s: changed defs %d" % (mode, len(per)))
    for k in ("N2b", "N2w", "N2d"):
        sel = [t for t in allrows if t[k]]
        lo = len(sel) * V.LOW_S / 60
        hi = sum(t["inv_s"] for t in sel) / 3600
        unx = sum(1 for t in sel if t.get("unexec") is True)
        inv0 = sum(1 for t in sel if t["inv"] == 0)
        log(txt, "   %s targets %d | low %.1f min | high %.2f h | unexecuted-line %d | inventory-0 %d" % (k, len(sel), lo, hi, unx, inv0))
    log(txt, "   all mutants %d" % len(allrows))
    for r in per:
        log(txt, "   %-62s all=%4d N2b=%3d N2w=%3d N2d=%3d inv=%d inv_s=%s" % r)
    with open(OUT + TAG + "targets_%s.json" % mode, "w", encoding="utf-8") as fh:
        json.dump([{k: v for k, v in t.items() if k in ("id", "file", "def_", "op", "path", "N2b", "N2w", "N2d", "inv", "unexec", "new_def")}
                   for t in allrows if t["N2d"]], fh, ensure_ascii=False, indent=0)


if __name__ == "__main__":
    for m in sys.argv[1:] or ["review2", "v4"]:
        main(m)
