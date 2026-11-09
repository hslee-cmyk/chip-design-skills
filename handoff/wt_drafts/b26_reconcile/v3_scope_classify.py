"""V3 범위 정책 card(20260930-v3-changed-stmt-scope) 대상 정의 재측정 -- 검토 review_v3_cards B2·S6 반영본.

게이트 도구 함수(mutate_changed.changed_defs·mutants·_path_nodes, reachability.iter_defs·build_graph)만 읽기 전용 import,
도구 main은 돌리지 않는다. 대상 card(head):
  * P9 실제(base 7535799 -> head b7765b0, git show로 읽음)
  * P9 시뮬레이션(sim_head.build_p9 -- b26_v3_measure.py의 것 그대로)
  * B26-1 시뮬레이션(sim_head.build_b26 -- 초안 시뮬레이션, b26_v3_measure.py의 것 그대로)
  * B34 좁힌 초안(draft_b34.spec.md v2 2차: 사이트 1·2·3·11·11b, def 4개/변이 55) -- 이 스크립트의 build_b34
정의(card 계약 1 개정본, 이름은 DEFS 사전):
  old_N1 / old_N2 / old_D1 = 검토 전 card 정의(교정용 -- 이전 측정 139/176 재현, D1 506은 재현 안 됨)
  공통 _C = T1(새 문장)·T2(머리 변경 복합문)·T5(early_return 무조건, 검토 B2)·T6(삭제 지점 바로 뒤 문장, 검토 S6)
  N2b = card 기본 N2 = _C + T3(b: def 자기 필드 + 바뀐 매개변수 이름을 읽는 문장) + T4(조상, 삭제 지점 포함)
  N2a = 선택지 2a = _C + T3(a: def 머리 변경이면 본문 전체) + T4
  D1b = 선택지 3 = _C + T3(b) + 이름 한 단계 의존(T7). N1b = _C + T3(b). N2b_noS6 = S6 몫을 뺀 N2b(효과 분리용)
  변이마다 'base 미실행 줄' 여부: head 줄을 같은(equal) base 줄로 대응, executed_lines.json(covplug)과 대조, 새 줄은 판정 불가.
시간: 하한 = 변이 x 5 s, 상한 = 변이 x 그 def 인벤토리 test 시간 합(junit, C:/g103/out/junit_base.xml).
결과: C:/g103/out/v3_scope_classify.txt(사람용), .json(행 단위). 케이스마다 append.
"""
import ast, copy, difflib, json, os, re, subprocess, sys

sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_reconcile")
import sim_head as S           # noqa: E402  (b26_v3_measure.py 사본, 경로만 C:/g60)
mc, rch = S.mc, S.rch

REPO = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
OUTT = "C:/g103/out/v3_scope_classify.txt"
OUTJ = "C:/g103/out/v3_scope_classify.json"
BLOCK = ("body", "orelse", "finalbody", "handlers", "cases")
LOW_S = 5.0


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    with open(OUTT, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


def fp(n):
    return ast.dump(n, include_attributes=False)


def hfp(n):
    c = copy.copy(n)
    for f in BLOCK:
        if isinstance(getattr(c, f, None), list):
            setattr(c, f, [])
    return ast.dump(c, include_attributes=False)


def is_compound(n):
    return any(isinstance(getattr(n, f, None), list) and getattr(n, f) for f in BLOCK)


def jp(owner, field, j):
    return "%s.%s[%d]" % (owner, field, j) if owner else "%s[%d]" % (field, j)


class Match:
    def __init__(self):
        self.new = []        # head 경로(부분 트리 전체)
        self.hdr = []        # 머리 변경 복합문 head 경로
        self.dels = []       # (owner 경로, field, head 위치 j) -- 삭제 지점
        self.del_nodes = []  # 지운 base 노드

    def block(self, bl, hl, owner, field):
        sm = difflib.SequenceMatcher(None, [fp(x) for x in bl], [fp(x) for x in hl], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            if tag == "insert":
                self.new += [jp(owner, field, j) for j in range(j1, j2)]
                continue
            if tag == "delete":
                self.dels.append((owner, field, j1))
                self.del_nodes += bl[i1:i2]
                continue
            free = list(range(i1, i2))
            for j in range(j1, j2):
                h = hl[j]
                pick = None
                if is_compound(h):
                    for i in free:
                        if type(bl[i]) is type(h) and is_compound(bl[i]) and hfp(bl[i]) == hfp(h):
                            pick = i
                            break
                    if pick is None:
                        for i in free:
                            if type(bl[i]) is type(h) and is_compound(bl[i]):
                                pick = i
                                break
                if pick is None:
                    self.new.append(jp(owner, field, j))
                    continue
                free.remove(pick)
                b = bl[pick]
                hp = jp(owner, field, j)
                if hfp(b) != hfp(h):
                    self.hdr.append(hp)
                for f in BLOCK:
                    bv, hv = getattr(b, f, None), getattr(h, f, None)
                    if isinstance(hv, list) or isinstance(bv, list):
                        self.block(bv or [], hv or [], hp, f)
            if free:
                self.dels.append((owner, field, j2))
                self.del_nodes += [bl[i] for i in free]


def split_path(p):
    return re.findall(r"([A-Za-z_]+)(?:\[(\d+)\])?", p)


def stmt_prefixes(p):
    """p의 엄격한 접두 중 문장(블록 필드 원소) 경로들."""
    parts = split_path(p)
    out, cur = [], ""
    for k, (f, i) in enumerate(parts):
        cur = ("%s.%s" % (cur, f) if cur else f) + ("[%s]" % i if i != "" else "")
        if k < len(parts) - 1 and f in BLOCK and i != "":
            out.append(cur)
    return out


def under(np, q):
    return np == q or np.startswith(q + ".")


def own(np, q):
    if not np.startswith(q + "."):
        return False
    first = split_path(np[len(q) + 1:])[0][0]
    return first not in BLOCK


def node_path(op, mpath):
    return re.sub(r"\.ops\[\d+\]$", "", mpath) if op == "cmp_flip" else mpath


def names(node, own_only=False):
    """(대입 이름, 읽는 이름). own_only면 복합문의 블록 필드 밖만."""
    st, ld = set(), set()
    roots = []
    if own_only:
        for f, v in ast.iter_fields(node):
            if f in BLOCK:
                continue
            if isinstance(v, list):
                roots += [x for x in v if isinstance(x, ast.AST)]
            elif isinstance(v, ast.AST):
                roots.append(v)
    else:
        roots = [node]
    for r in roots:
        for x in ast.walk(r):
            if isinstance(x, ast.Name):
                (st if isinstance(x.ctx, (ast.Store, ast.Del)) else ld).add(x.id)
    return st, ld


def param_sig(fn):
    a = fn.args
    pos = a.posonlyargs + a.args
    d = {}
    defs = [None] * (len(pos) - len(a.defaults)) + list(a.defaults)
    for k, (x, dv) in enumerate(zip(pos, defs)):
        d[x.arg] = ("pos" if k < len(a.posonlyargs) else "arg", fp(dv) if dv else None, fp(x.annotation) if x.annotation else None, k)
    if a.vararg:
        d[a.vararg.arg] = ("vararg", None, fp(a.vararg.annotation) if a.vararg.annotation else None, -1)
    for x, dv in zip(a.kwonlyargs, a.kw_defaults):
        d[x.arg] = ("kwonly", fp(dv) if dv else None, fp(x.annotation) if x.annotation else None, -1)
    if a.kwarg:
        d[a.kwarg.arg] = ("kwarg", None, fp(a.kwarg.annotation) if a.kwarg.annotation else None, -1)
    return d


def changed_params(bfn, hfn):
    b, h = param_sig(bfn), param_sig(hfn)
    return {n for n in set(b) | set(h) if b.get(n) != h.get(n)}


EXEC = None


def node_lines(n):
    if isinstance(n, ast.ExceptHandler):
        return {n.lineno}
    if isinstance(n, ast.stmt) and is_compound(n):
        end = n.body[0].lineno - 1 if getattr(n, "body", None) else n.lineno
        return set(range(n.lineno, max(n.lineno, end) + 1))
    if hasattr(n, "lineno"):
        return set(range(n.lineno, (n.end_lineno or n.lineno) + 1))
    return set()


def mutant_lines(fn, op, mpath):
    if op == "early_return":
        k = int(re.search(r"\[(\d+)\]", mpath).group(1))
        b = fn.body[min(k, len(fn.body) - 1)]
        return {b.lineno}
    np_ = node_path(op, mpath)
    return node_lines(mc._get(fn, np_) if np_ else fn)


def classify(bfn, hfn, src, hmap=None, executed=None):
    """한 def의 변이 목록과 정의별 대상 여부. hmap: head 줄 -> base 줄(같은 줄만), executed: base 실행 줄 집합."""
    M = Match()
    M.block(bfn.body, hfn.body, "", "body")
    def_hdr = hfp(bfn) != hfp(hfn)
    pn = {p: n for n, p in mc._path_nodes(hfn)}
    # T6(S6): 삭제 지점 바로 뒤 문장
    t6_simple, t6_comp = [], []
    for owner, field, j in M.dels:
        lst = getattr(pn[owner] if owner else hfn, field, None) or []
        if j < len(lst):
            (t6_comp if is_compound(lst[j]) else t6_simple).append(jp(owner, field, j))
    # T4 조상
    anc_old = set()
    for q in M.new + M.hdr:
        anc_old |= set(stmt_prefixes(q))
    anc_new = set(anc_old)
    for owner, field, j in M.dels:
        if owner:
            anc_new.add(owner)
            anc_new |= set(stmt_prefixes(owner))
    for q in t6_simple + t6_comp:
        anc_new |= set(stmt_prefixes(q))
    # D1 이름
    a_old, r_old = set(), set()
    for q in M.new:
        s, l = names(pn[q]); a_old |= s; r_old |= l
    for q in M.hdr:
        s, l = names(pn[q], own_only=True); a_old |= s; r_old |= l
    a_new, r_new = set(a_old), set(r_old)
    for n in M.del_nodes:
        s, l = names(n); a_new |= s; r_new |= l
    stmt_paths = [p for n, p in mc._path_nodes(hfn) if p and isinstance(n, (ast.stmt, ast.ExceptHandler, ast.match_case))]

    def dep_set(A, R):
        simple, comp = [], []
        for p in stmt_paths:
            n = pn[p]
            c = is_compound(n)
            s, l = names(n, own_only=c)
            if (l & A) or (s & R):
                (comp if c else simple).append(p)
        return simple, comp
    d_old = dep_set(a_old, r_old)
    d_new = dep_set(a_new, r_new)
    any_change = bool(M.new or M.hdr or M.dels or def_hdr)
    cps = changed_params(bfn, hfn) if def_hdr else set()
    t3n_simple, t3n_comp = [], []
    for p in stmt_paths:
        n = pn[p]
        c = is_compound(n)
        _s, l = names(n, own_only=c)
        if l & cps:
            (t3n_comp if c else t3n_simple).append(p)
    rows = []
    for op, mpath, _m in mc.mutants(hfn, src):
        np_ = node_path(op, mpath)
        if op == "early_return":
            t = dict(T1=False, T2=False, T3o=False, T3n=def_hdr, T4o=False, T4n=False, T5o=any_change, T5n=True,
                     T6=False, Do=False, Dn=False, T3name=False)
        else:
            hd = op in ("stmt_delete", "except_body_delete")

            def comp_hit(qs):
                return any(own(np_, q) or (hd and np_ == q) for q in qs)
            t = dict(
                T1=any(under(np_, q) for q in M.new),
                T2=comp_hit(M.hdr),
                T3o=def_hdr and (np_ != "" and split_path(np_)[0][0] not in BLOCK),
                T3n=def_hdr,
                T4o=comp_hit(anc_old), T4n=comp_hit(anc_new),
                T5o=False, T5n=False,
                T6=any(under(np_, q) for q in t6_simple) or comp_hit(t6_comp),
                T3name=any(under(np_, q) for q in t3n_simple) or comp_hit(t3n_comp),
                Do=any(under(np_, q) for q in d_old[0]) or comp_hit(d_old[1]),
                Dn=any(under(np_, q) for q in d_new[0]) or comp_hit(d_new[1]),
            )
        t["op"], t["path"] = op, mpath
        t["deco"] = mpath.startswith("decorator_list")
        t["unexec"] = None
        if hmap is not None and executed is not None:
            hl = mutant_lines(hfn, op, mpath)
            bl = [hmap.get(x) for x in hl]
            t["unexec"] = (None if (not bl or any(x is None for x in bl)) else not any(x in executed for x in bl))
        rows.append(t)
    info = dict(cps=sorted(cps), def_hdr=def_hdr, new=len(M.new), hdr=len(M.hdr), dels=len(M.del_nodes), t6=len(t6_simple) + len(t6_comp))
    return rows, info


_C = lambda t: t["T1"] or t["T2"] or t["T5n"] or t["T6"]          # 개정 공통: T1·T2·T5(무조건)·T6(삭제 뒤 문장)
_A = lambda t: t["T3n"]                                             # T3 변형 a: def 머리 변경 -> 본문 전체(검토 B2 기본)
_B = lambda t: t["T3o"] or t["T3name"]                              # T3 변형 b: def 자기 필드 + 바뀐 매개변수 이름을 읽는 문장
DEFS = {
    "old_N1": lambda t: t["T1"] or t["T2"] or t["T3o"] or t["T5o"],
    "old_N2": lambda t: t["T1"] or t["T2"] or t["T3o"] or t["T5o"] or t["T4o"],
    "old_D1": lambda t: t["T1"] or t["T2"] or t["T3o"] or t["T5o"] or t["Do"],
    "N1a": lambda t: _C(t) or _A(t),
    "N2a": lambda t: _C(t) or _A(t) or t["T4n"],
    "D1a": lambda t: _C(t) or _A(t) or t["Dn"],
    "N1b": lambda t: _C(t) or _B(t),
    "N2b": lambda t: _C(t) or _B(t) or t["T4n"],
    "D1b": lambda t: _C(t) or _B(t) or t["Dn"],
    "N2b_noS6": lambda t: t["T1"] or t["T2"] or t["T5n"] or _B(t) or t["T4o"],
}


def durations():
    import xml.etree.ElementTree as ET
    d = {}
    root = ET.parse("C:/g103/out/junit_base.xml").getroot()
    for tc in root.iter("testcase"):
        parts = tc.get("classname", "").split(".")
        name = re.sub(r"\[.*$", "", tc.get("name", ""))
        for k in range(len(parts), 0, -1):
            cand = "/".join(parts[:k]) + ".py"
            if os.path.exists(os.path.join(S.BASE, cand)):
                key = "%s::%s" % (cand, ".".join(parts[k:] + [name]))
                d[key] = d.get(key, 0.0) + float(tc.get("time", 0) or 0)
                break
    return d


DUR = None


def measure(label, base_files, head_files):
    global DUR
    if DUR is None:
        DUR = durations()
    nodes, edges = rch.build_graph(head_files)
    tests = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
             and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
    out = []
    executed = EXEC
    tot = {k: 0 for k in ["all"] + list(DEFS)}
    unx = {k: 0 for k in tot}
    unk = {k: 0 for k in tot}
    conf_h = {k: 0.0 for k in tot}
    tl = {k: 0.0 for k in tot}
    th = {k: 0.0 for k in tot}
    for path in sorted(p for p in head_files if head_files[p] != base_files.get(p) and rch._is_source(p)):
        bsrc = base_files.get(path)
        bdefs = dict(rch.iter_defs(ast.parse(bsrc))) if bsrc else {}
        for q, hfn in mc.changed_defs(bsrc, head_files[path]):
            inv = mc.inventory(edges, "%s::%s" % (path, q), tests)
            invs = sum(DUR.get(x, 0.0) for x in inv)
            fname = path.split("/")[-1]
            ex = set(executed.get(fname, [])) if executed is not None else None
            hmap = line_map(bsrc, head_files[path]) if bsrc else None
            if q in bdefs:
                rows, info = classify(bdefs[q], hfn, head_files[path], hmap, ex)
            else:
                rows = [dict(op=o, path=p, unexec=None) for o, p, _ in mc.mutants(hfn, head_files[path])]
                info = dict(cps=[], def_hdr=None, new="newdef", hdr=0, dels=0, t6=0)
            cnt = {"all": len(rows)}
            sel = {"all": rows}
            for k, f in DEFS.items():
                sel[k] = rows if q not in bdefs else [t for t in rows if f(t)]
                cnt[k] = len(sel[k])
            for k in tot:
                u = sum(1 for t in sel[k] if t.get("unexec") is True)
                unx[k] += u
                unk[k] += sum(1 for t in sel[k] if t.get("unexec") is None)
                conf_h[k] += u * invs
            cnt.update({"unexec_" + k: sum(1 for t in sel[k] if t.get("unexec") is True) for k in ("all", "N2a", "N2b")})
            deco = sum(1 for t in rows if t.get("deco"))
            for k in tot:
                tot[k] += cnt[k]
                tl[k] += cnt[k] * LOW_S
                th[k] += cnt[k] * invs
            out.append(dict(path=path, def_=q, inv=len(inv), inv_s=round(invs, 1), deco_mutants=deco, **info, **cnt))
    out.sort(key=lambda r: -r["all"])
    log("== %s: changed defs %d" % (label, len(out)))
    log("   " + "  ".join("%s=%d" % (k, tot[k]) for k in tot))
    for k in tot:
        log("   time %-10s %6d mutants  low %7.1f min  high %7.2f h | base 미실행 줄 변이 %5d (판정불가 새 줄 %5d) -> 현실 하한 %6.2f h" % (
            k, tot[k], tl[k] / 60, th[k] / 3600, unx[k], unk[k], (tl[k] + conf_h[k]) / 3600))
    for r in out:
        log("   %-58s hdr=%-5s cps=%s new=%s chdr=%s del=%s t6=%s inv=%d inv_s=%s deco=%d | all=%d oN1=%d oN2=%d oD1=%d | N1a=%d N2a=%d D1a=%d | N1b=%d N2b=%d D1b=%d N2b_noS6=%d | unexec all/N2a/N2b=%d/%d/%d" % (
            r["path"].split("/")[-1] + "::" + r["def_"], r["def_hdr"], ",".join(r["cps"]) or "-", r["new"], r["hdr"], r["dels"], r["t6"], r["inv"],
            r["inv_s"], r["deco_mutants"], r["all"], r["old_N1"], r["old_N2"], r["old_D1"], r["N1a"], r["N2a"], r["D1a"],
            r["N1b"], r["N2b"], r["D1b"], r["N2b_noS6"], r["unexec_all"], r["unexec_N2a"], r["unexec_N2b"]))
    return dict(label=label, totals=tot, low_min={k: round(v / 60, 1) for k, v in tl.items()},
                high_h={k: round(v / 3600, 2) for k, v in th.items()}, unexec=unx, undeterminable=unk,
                realistic_low_h={k: round((tl[k] + conf_h[k]) / 3600, 2) for k in tot}, rows=out)


def line_map(bsrc, hsrc):
    """head 줄(1-based) -> base 줄. 같은(equal) 줄만."""
    sm = difflib.SequenceMatcher(None, bsrc.split("\n"), hsrc.split("\n"), autojunk=False)
    m = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                m[j1 + k + 1] = i1 + k + 1
    return m


def base_unexecuted(label, base_files, names_by_path):
    """base 본문 기준 '어떤 test도 실행하지 않은 줄'의 변이(검토 전 card '작성 전 실측' 3의 재현)."""
    tot = n_all = 0
    per = []
    for path, qs in names_by_path.items():
        d = dict(rch.iter_defs(ast.parse(base_files[path])))
        ex = set(EXEC.get(path.split("/")[-1], []))
        for q in qs:
            fn = d[q]
            ms = mc.mutants(fn, base_files[path])
            u = sum(1 for op, p, _ in ms if not (mutant_lines(fn, op, p) & ex))
            tot += u
            n_all += len(ms)
            if u:
                per.append((q, u, len(ms)))
    per.sort(key=lambda x: -x[1])
    log("== %s: base 본문 변이 %d 중 미실행 줄 %d" % (label, n_all, tot))
    log("   " + ", ".join("%s %d/%d" % x for x in per))
    return dict(label=label, mutants=n_all, unexecuted=tot, per=per)


def git_show(rev, path):
    return subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (rev, path)], capture_output=True, check=True).stdout.decode("utf-8")


def def_replace(src, qual, old, new, count=1):
    tree = ast.parse(src)
    fn = dict(rch.iter_defs(tree))[qual]
    lines = src.split("\n")
    seg = "\n".join(lines[fn.lineno - 1:fn.end_lineno])
    assert seg.count(old) == count, (qual, seg.count(old), old)
    seg2 = seg.replace(old, new)
    return "\n".join(lines[:fn.lineno - 1] + seg2.split("\n") + lines[fn.end_lineno:])


def build_b34(files):
    """draft_b34.spec.md v2(2차) '코드를 바꾸는 것' 표의 사이트 1·2·3·11·11b만. docstring은 해시 불변이라 적용하지 않음."""
    head = dict(files)
    src = files[S.SD]
    src = def_replace(src, "_import_analog_grammar", "    except ImportError:\n        return tuple(None for _ in module_names)",
                      "    except ImportError as e:\n        raise ImportError(\"analog-grammar skill을 import할 수 없다(탐색 경로 %s)\" % _ag_path) from e")
    src = def_replace(src, "find_idiom_matches", "    if netclass is None:\n        return None\n", "")
    src = def_replace(src, "find_stack_edges", "    if netclass is None:\n        return None\n", "")
    src = def_replace(src, "audit_theta_root_direction", "    if netclass_mod is None or idioms_mod is None:\n        return []\n", "")
    src = def_replace(src, "audit_theta_root_direction", "    if matches is None:\n        return []\n", "")
    ast.parse(src)
    head[S.SD] = src
    return head


if __name__ == "__main__":
    open(OUTT, "w").close()
    with open("C:/g103/out/executed_lines.json", encoding="utf-8") as fh:
        EXEC = json.load(fh)
    res = {}
    # P9 실제: base 7535799, head b7765b0 -- 두 쪽 모두 git blob(LF)
    p9b = dict(S.BASEF); p9b[S.SD] = git_show("7535799", S.SD)
    p9h = dict(p9b); p9h[S.SD] = git_show("b7765b0", S.SD)
    res["p9_real"] = measure("P9 실제(7535799 -> b7765b0)", p9b, p9h)
    res["p9_sim"] = measure("P9 시뮬레이션(build_p9)", S.BASEF, S.build_p9(S.BASEF))
    b26, _ = S.build_b26(S.BASEF)
    res["b26_1_sim"] = measure("B26-1 시뮬레이션(build_b26)", S.BASEF, b26)
    res["b34_v2"] = measure("B34 좁힌 초안(사이트 1·2·3·11·11b)", S.BASEF, build_b34(S.BASEF))
    # 검토 전 card의 확정 생존 298(B26-1)·75(넓은 B34) 재현: base 본문 기준
    b26_names = {}
    for path in (S.SD, S.SR):
        bd = dict(rch.iter_defs(ast.parse(S.BASEF[path])))
        b26_names[path] = [q for q, _ in mc.changed_defs(S.BASEF[path], b26[path]) if q in bd]
    res["unexec_b26"] = base_unexecuted("B26-1 대상 def(base 본문)", S.BASEF, b26_names)
    b34_wide = ["_import_analog_grammar", "find_idiom_matches", "find_stack_edges", "find_differential_and_mirror_forks",
                "suggest_vertical_stack_composites", "find_verified_differential_and_mirror_relations",
                "_propose_vertical_stack_ids", "_propose_headroom_roles", "refine_differential_and_mirror_relations",
                "audit_theta_root_direction", "propose_theta_kcl_gap_fill", "propose_device_roles_gap_fill",
                "find_differential_pair_candidates", "_propose_gm_id_roles", "_propose_L_roles",
                "propose_vertical_stack_id_gap_fill", "geometry_colocation_union", "load_topology"]
    res["unexec_b34_wide"] = base_unexecuted("넓은 B34(v1, 18 def) base 본문", S.BASEF, {S.SD: b34_wide})
    res["unexec_b34_v2"] = base_unexecuted("좁힌 B34(4 def) base 본문", S.BASEF,
                                           {S.SD: ["_import_analog_grammar", "find_idiom_matches", "find_stack_edges", "audit_theta_root_direction"]})
    with open(OUTJ, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
