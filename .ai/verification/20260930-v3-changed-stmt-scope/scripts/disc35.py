"""순서 3 판별력 확인 (auditor, 20260930-v3-changed-stmt-scope).
사용: python -B disc35.py <v.json> <base 게이트 디렉터리> <작업 디렉터리> <출력 json>

단계마다
 (A) rt.py와 독립으로 git 합성 저장소(base 커밋 -> head 커밋)를 직접 만들고 base 도구(def 전체 변이)를 --out과 함께 돌려
     변이 id별 killed/survived를 얻는다(①: X가 base에서 생존인지, 나머지 대상 변이가 test로 죽는지의 근거).
 (B) spec card 계약 1을 auditor가 직접 구현한 분류기(classify)로 대상/대상 밖을 정한다(②). 피검 도구·키트 scope_proto는 쓰지 않는다.
 (C) 규칙 하나씩 뺀 정의(변형)로 다시 분류해, 변형마다 그 단계 기대(exit·조각·observed_equals)가 깨지는지(③ 판별력)를 예측한다.
     예측 = 대상 변이의 결과는 (A)의 base 실행 결과(변이 실행 방식은 계약 9 데코레이터 치환 말고는 같다),
     데코레이터 변이는 (D)의 계약 9 치환 실측.
 (D) decorator_list 안 변이: base _replace_def 결과 AST가 원본과 같은지(NOOP), 계약 9 판(첫 데코레이터 줄부터 치환)으로
     바꾼 소스로 그 단계 test를 직접 pytest 실행해 killed/survived.
"""
import ast
import copy
import difflib
import json
import os
import re
import shutil
import subprocess
import sys

vjson, gate, work, outp = sys.argv[1:5]
PY = sys.executable
ENGINE = "skills/analog-gmid-design/assets/rt_engine.py"
BLOCK = ("body", "orelse", "finalbody", "handlers", "cases")
LOOPS = (ast.For, ast.AsyncFor, ast.While)


# ---------------------------------------------------------------- 계약 1 (auditor 구현)
def fp(n):
    return ast.dump(n, include_attributes=False)


def header(n):
    c = copy.copy(n)
    for f in BLOCK:
        if isinstance(getattr(c, f, None), list):
            setattr(c, f, [])
    return fp(c)


def is_compound(n):
    if isinstance(n, (ast.ExceptHandler, ast.match_case)):
        return True
    return any(isinstance(getattr(n, f, None), list) and getattr(n, f) for f in BLOCK)


def self_field_values(n):
    for f, v in ast.iter_fields(n):
        if f in BLOCK:
            continue
        if isinstance(v, list):
            for x in v:
                if isinstance(x, ast.AST):
                    yield x
        elif isinstance(v, ast.AST):
            yield v


def walk_region(n, whole):
    """whole: 부분 트리 전체, 아니면 자기 필드 안만."""
    if whole:
        yield from ast.walk(n)
    else:
        for v in self_field_values(n):
            yield from ast.walk(v)


def lead_name(e):
    while isinstance(e, (ast.Attribute, ast.Subscript)):
        e = e.value
    while isinstance(e, ast.Call):   # a.b().c 꼴
        e = e.func
        while isinstance(e, (ast.Attribute, ast.Subscript)):
            e = e.value
    return e.id if isinstance(e, ast.Name) else None


def changed_names(nodes_whole):
    """nodes_whole: [(노드, whole)]"""
    out = set()
    for n, whole in nodes_whole:
        if isinstance(n, ast.ExceptHandler) and n.name:
            out.add(n.name)
        for x in walk_region(n, whole):
            if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del)):
                out.add(x.id)
            elif isinstance(x, (ast.Attribute, ast.Subscript)) and isinstance(x.ctx, (ast.Store, ast.Del)):
                ln = lead_name(x.value)
                if ln:
                    out.add(ln)
            elif isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute):
                ln = lead_name(x.func.value)
                if ln:
                    out.add(ln)
            elif isinstance(x, ast.ExceptHandler) and x.name:
                out.add(x.name)
    return out


def reads(S, names):
    whole = not is_compound(S)
    return any(isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load) and x.id in names for x in walk_region(S, whole))


def params(fn):
    a = fn.args
    pos = list(a.posonlyargs) + list(a.args)
    nd = len(a.defaults)
    res = {}
    for i, p in enumerate(pos):
        kind = "posonly" if i < len(a.posonlyargs) else "normal"
        d = a.defaults[i - (len(pos) - nd)] if i >= len(pos) - nd else None
        res[p.arg] = (kind, i, fp(d) if d is not None else None, fp(p.annotation) if p.annotation else None)
    if a.vararg:
        res[a.vararg.arg] = ("vararg", 0, None, fp(a.vararg.annotation) if a.vararg.annotation else None)
    for i, p in enumerate(a.kwonlyargs):
        d = a.kw_defaults[i]
        res[p.arg] = ("kwonly", i, fp(d) if d is not None else None, fp(p.annotation) if p.annotation else None)
    if a.kwarg:
        res[a.kwarg.arg] = ("kwarg", 0, None, fp(a.kwarg.annotation) if a.kwarg.annotation else None)
    return res


class Match:
    def __init__(self, bfn, hfn):
        self.new = []          # head 노드(맞춤에서 직접 기록된 새 문장)
        self.hdr = {}          # id(head 복합문) -> (base 노드, head 노드)
        self.deleted = []      # (head 부모, 필드, 삭제 지점 j, base 노드)
        self.pos = {}          # id(head 문장) -> (head 부모, 필드, j)
        self.def_hdr_changed = header(bfn) != header(hfn)
        bp, hp = params(bfn), params(hfn)
        self.changed_params = set(bp) ^ set(hp)
        self.changed_params |= {k for k in set(bp) & set(hp) if bp[k] != hp[k]}
        self._index(hfn)
        self.match(bfn.body, hfn.body, hfn, "body")

    def _index(self, node):
        for f in BLOCK:
            lst = getattr(node, f, None)
            if isinstance(lst, list):
                for j, s in enumerate(lst):
                    if isinstance(s, ast.AST):
                        self.pos[id(s)] = (node, f, j)
                        self._index(s)

    def match(self, a, b, hparent, field):
        sm = difflib.SequenceMatcher(None, [fp(x) for x in a], [fp(x) for x in b], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            if tag == "insert":
                self.new += b[j1:j2]
                continue
            if tag == "delete":
                for i in range(i1, i2):
                    self.deleted.append((hparent, field, j1, a[i]))
                continue
            unpaired = list(range(i1, i2))
            for j in range(j1, j2):
                h = b[j]
                pick = None
                if is_compound(h):
                    cands = [i for i in unpaired if is_compound(a[i]) and type(a[i]) is type(h)]
                    same = [i for i in cands if header(a[i]) == header(h)]
                    pick = (same or cands or [None])[0]
                if pick is None:
                    self.new.append(h)
                    continue
                unpaired.remove(pick)
                bn = a[pick]
                if header(bn) != header(h):
                    self.hdr[id(h)] = (bn, h)
                for f in BLOCK:
                    la, lb = getattr(bn, f, None), getattr(h, f, None)
                    if isinstance(lb, list) or isinstance(la, list):
                        self.match(la or [], lb or [], h, f)
            for i in unpaired:
                self.deleted.append((hparent, field, j2, a[i]))


def chain_of(fn, path):
    """변이 경로 -> 소유 문장 사슬 [(문장 노드)], 그리고 소유 문장(마지막)."""
    cur = fn
    chain = []
    parts = re.findall(r"([A-Za-z_]+)(?:\[(\d+)\])?", path)
    for name, idx in parts:
        val = getattr(cur, name)
        if idx != "":
            val = val[int(idx)]
            if name in BLOCK and (isinstance(cur, (ast.stmt, ast.ExceptHandler, ast.match_case)) or cur is fn):
                chain.append(val)
        cur = val
    return chain


def ancestors(fn, node, m):
    """node(head 문장)를 감싸는 복합문(대상 def 제외)."""
    out = []
    p = m.pos.get(id(node))
    while p is not None:
        parent = p[0]
        if parent is fn:
            break
        out.append(parent)
        p = m.pos.get(id(parent))
    return out


def classify(bfn, hfn, mids, variant=frozenset()):
    """mids: [(id, op, path)]. variant: 뺄 규칙 이름 집합.
    규칙 이름: T1 T2 T3 T4 T5 T6a T6b T6b_far(같은 블록 뒤쪽 중 바로 뒤가 아닌 것) LOOP INDENT(들여쓰기만 바뀐 문장=새 문장)
    + WIDEN(다른 블록까지 넓힘) + ALL(def 전체)"""
    if "ALL" in variant:
        return {mid for mid, _, _ in mids}
    m = Match(bfn, hfn)
    new_nodes = list(m.new)
    if "INDENT" in variant:
        base_fps = {fp(x) for x in ast.walk(bfn) if isinstance(x, ast.stmt) and x is not bfn}
        new_nodes = [n for n in new_nodes if fp(n) not in base_fps]
    new_ids = {id(n) for n in new_nodes}
    share = set()      # id(문장) -- 몫
    regions = []       # (노드, 부모, 필드, j, kind)
    for n in new_nodes:
        par, f, j = m.pos[id(n)]
        regions.append((n, par, f, j, "new"))
    for bn, hn in m.hdr.values():
        par, f, j = m.pos[id(hn)]
        regions.append((hn, par, f, j, "hdr"))
    for par, f, j, bn in m.deleted:
        regions.append((bn, par, f, j, "del"))
    t6 = set()
    for par, f, j, bn in m.deleted:
        lst = getattr(par, f)
        if "T6a" not in variant and j < len(lst):
            t6.add(id(lst[j]))
    if "T6b" not in variant:
        for n, par, f, j, kind in regions:
            if kind == "hdr":
                bn = m.hdr[id(n)][0]
                names = changed_names([(bn, False), (n, False)])
            else:
                names = changed_names([(n, True)])
            lst = getattr(par, f)
            loop = isinstance(par, LOOPS) and f == "body" and "LOOP" not in variant
            for k, s in enumerate(lst):
                if kind != "del" and s is n:
                    continue
                later = (k > j) if kind != "del" else (k >= j)
                if not (loop or later):
                    continue
                if "T6b_far" in variant and not loop:
                    adj = (k == j + 1) if kind != "del" else (k == j)
                    if not adj:
                        continue
                if reads(s, names):
                    t6.add(id(s))
            if "WIDEN" in variant:   # 다른 블록(바깥 블록 뒤쪽)까지
                cur = par
                while cur is not hfn and id(cur) in m.pos:
                    gp, gf, gj = m.pos[id(cur)]
                    for k, s in enumerate(getattr(gp, gf)):
                        if k > gj and reads(s, names):
                            t6.add(id(s))
                    cur = gp
    t3 = set()
    if m.def_hdr_changed and "T3" not in variant:
        for sid, (par, f, j) in m.pos.items():
            s = getattr(par, f)[j]
            if reads(s, m.changed_params):
                t3.add(sid)
    anc = set()
    if "T4" not in variant:
        roots = [n for n in new_nodes] if "T1" not in variant else []
        if "T2" not in variant:
            roots += [hn for _, hn in m.hdr.values()]
        id2node = {}
        for sid, (par, f, j) in m.pos.items():
            id2node[sid] = getattr(par, f)[j]
        roots += [id2node[s] for s in t6]
        for r in roots:
            anc |= {id(x) for x in ancestors(hfn, r, m)}
        for par, f, j, bn in m.deleted:
            if par is not hfn:
                anc.add(id(par))
                anc |= {id(x) for x in ancestors(hfn, par, m)}
    targets = set()
    for mid, op, path in mids:
        if op == "early_return":
            if "T5" not in variant:
                targets.add(mid)
            continue
        ch = chain_of(hfn, path)
        owner = ch[-1] if ch else None
        if owner is None:   # def 자기 필드
            if m.def_hdr_changed and "T3" not in variant:
                targets.add(mid)
            continue
        if "T1" not in variant and any(id(x) in new_ids for x in ch):
            targets.add(mid)
        elif "T2" not in variant and id(owner) in m.hdr:
            targets.add(mid)
        elif id(owner) in t3 or id(owner) in t6 or id(owner) in anc:
            targets.add(mid)
    return targets


# ---------------------------------------------------------------- 합성 저장소·base 도구
def git(cwd, *a):
    r = subprocess.run(["git", "-C", cwd, *a], capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode("utf-8", "replace"))
    return r.stdout.decode("utf-8").strip()


def mkrepo(path, base, head):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    git(path, "init", "-q", "-b", "master")
    for k, v in (("user.name", "audit"), ("user.email", "audit@example.invalid"), ("core.autocrlf", "false"),
                 ("commit.gpgsign", "false"), ("core.hooksPath", path + "/.nohooks")):
        git(path, "config", k, v)

    def put(files):
        for p, data in files.items():
            fp_ = os.path.join(path, p)
            os.makedirs(os.path.dirname(fp_), exist_ok=True)
            with open(fp_, "wb") as f:
                f.write(data.encode("utf-8"))
    put(base)
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "base")
    b = git(path, "rev-parse", "HEAD")
    put(head)
    git(path, "add", "-A")
    git(path, "commit", "-q", "--allow-empty", "-m", "head")
    return b, git(path, "rev-parse", "HEAD")


def run_tool(path, b, h, tag):
    out = os.path.join(work, tag + ".jsonl")
    if os.path.exists(out):
        os.remove(out)
    cmd = [PY, os.path.join(gate, "mutate_changed.py"), "--root", path, "--base", b, "--head", h,
           "--pytest-ini", os.path.join(gate, "pytest_gate.ini"), "--out", out]
    r = subprocess.run(cmd, capture_output=True)
    stdout = r.stdout.decode("utf-8", "replace")
    first = next((ln for ln in stdout.splitlines() if ln.strip().startswith("{")), None)
    obj = json.loads(first) if first else None
    recs = [json.loads(l) for l in open(out, encoding="utf-8")] if os.path.exists(out) else []
    return {"exit": r.returncode, "stdout": stdout.strip(), "stderr_tail": r.stderr.decode("utf-8", "replace")[-400:],
            "summary": obj, "out_records": [(x.get("id"), x.get("result")) for x in recs]}


# ---------------------------------------------------------------- 계약 9 치환(데코레이터 변이) 실측
sys.path.insert(0, gate)
import mutate_changed as mc  # noqa: E402  base 판 -- mutants()(변이 생성 그대로)와 _replace_def(NOOP 확인)만


def replace_def_c9(src, fn, new_fn):
    lines = src.split("\n")
    start = (fn.decorator_list[0].lineno if fn.decorator_list else fn.lineno) - 1
    end = fn.end_lineno
    ind = len(lines[start]) - len(lines[start].lstrip())
    text = ast.unparse(ast.fix_missing_locations(copy.deepcopy(new_fn)))
    new = [(" " * ind + l) if l.strip() else l for l in text.split("\n")]
    return "\n".join(lines[:start] + new + lines[end:])


def deco_probe(step, head_files, qual):
    src = head_files[ENGINE]
    tree = ast.parse(src)
    fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == qual][0]
    res = {}
    tests = [p for p in head_files if p.startswith("skills/analog-gmid-design/assets/tests/")]
    for op, path, mfn in mc.mutants(fn, src):
        if not path.startswith("decorator_list"):
            continue
        mid = "rt_engine:%s:%s:%s" % (qual, op, path)
        base_src = mc._replace_def(src, fn, mfn)
        noop = fp(ast.parse(base_src)) == fp(ast.parse(src))
        c9 = replace_def_c9(src, fn, mfn)
        c9_differs = fp(ast.parse(c9)) != fp(ast.parse(src))
        d = os.path.join(work, step + "-c9", re.sub(r"[^A-Za-z0-9]+", "_", mid))
        if os.path.exists(d):
            shutil.rmtree(d)
        for p, t in head_files.items():
            fp_ = os.path.join(d, p)
            os.makedirs(os.path.dirname(fp_), exist_ok=True)
            with open(fp_, "w", encoding="utf-8", newline="\n") as f:
                f.write(c9 if p == ENGINE else t)
        r = subprocess.run([PY, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *[os.path.join(d, t) for t in tests]],
                           capture_output=True, cwd=d)
        res[mid] = {"base_replace_noop": noop, "c9_ast_differs": c9_differs,
                    "c9_pytest_exit": r.returncode, "c9_result": "killed" if r.returncode != 0 else "survived",
                    "c9_tail": r.stdout.decode("utf-8", "replace")[-300:]}
    return res


# ---------------------------------------------------------------- 단계별 기대 대조
def predict(targets, mids_order, results, n_all):
    tg = [mid for mid in mids_order if mid in targets]
    surv = [mid for mid in tg if results[mid] == "survived"]
    nt = [mid for mid in mids_order if mid not in targets]
    return {"exit": 1 if surv else 0, "verdict": "FAIL" if surv else "PASS", "survivors": surv,
            "mutants": len(tg), "killed": len(tg) - len(surv), "not_targeted": len(nt),
            "observed": {"lines": n_all, "by_result": ({"not_targeted": sorted(nt)} if nt else {})}}


def expect_holds(exp, pr):
    """기대 조각을 예측 출력에서 재구성해 대조(부분 문자열 대조의 의미 그대로: 조각이 출력 JSON 문자열에 들어 있는가)."""
    out = json.dumps({"tool": "V3", "verdict": pr["verdict"], "mutants": pr["mutants"], "killed": pr["killed"],
                      "survivors": pr["survivors"], "survivor_bindings": {}, "exempt_ignored": [],
                      "not_targeted": pr["not_targeted"], "targets_by_def": {}}, ensure_ascii=False)
    # 계약 5 키 순서: tool, verdict, targets, mutants, killed, survivors, survivor_bindings, exempt_ignored, not_targeted, targets_by_def
    out = out.replace('"verdict": "%s", ' % pr["verdict"], '"verdict": "%s", "targets": [], ' % pr["verdict"])
    miss = [frag for frag in exp.get("message_contains", []) if frag not in out]
    ok = (exp["exit"] == pr["exit"]) and not miss
    obs_ok = None
    if "observed_equals" in exp:
        obs_ok = exp["observed_equals"] == pr["observed"]
        ok = ok and obs_ok
    return {"holds": ok, "exit_ok": exp["exit"] == pr["exit"], "missing_fragments": miss, "observed_ok": obs_ok}


AIMED = {
    "unchanged-stmt-survivor": [["ALL"]],
    "changed-stmt-survivor": [["T1"]],
    "enclosing-guard-survivor": [["T4"]],
    "unwrapped-stmt": [["INDENT"]],
    "header-only-change": [["T2"]],
    "header-default-bool": [["T3", "T5"], ["T3"], ["T5"]],
    "delete-then-use": [["T6a"], ["T6a", "T6b"]],
    "decorator-mutant-applied": [["DECO_NOOP"]],
    "same-block-later-use": [["T6b_far"]],
    "loop-carried-use": [["LOOP"]],
    "cross-block-not-targeted": [["WIDEN"], ["ALL"]],
}
ALL_VARIANTS = [["ALL"], ["T1"], ["T2"], ["T3"], ["T4"], ["T5"], ["T3", "T5"], ["T6a"], ["T6b"], ["T6a", "T6b"],
                ["T6b_far"], ["LOOP"], ["INDENT"], ["WIDEN"], ["DECO_NOOP"]]

spec = json.load(open(vjson, encoding="utf-8"))
res = {"steps": {}}
for case in spec["cases"]:
    step = case["step"]
    qual = case["subjects"][0].split(".")[-1]
    base = {p: v["text"] for p, v in case["base"].items()}
    head = dict(base)
    head.update({p: v["text"] for p, v in case["head"].items()})
    repo = os.path.join(work, "repo", step)
    b, h = mkrepo(repo, base, {p: v["text"] for p, v in case["head"].items()})
    tool = run_tool(repo, b, h, step)
    results = dict(tool["out_records"])
    bsrc, hsrc = base[ENGINE], head[ENGINE]
    bfn = [n for n in ast.parse(bsrc).body if isinstance(n, ast.FunctionDef) and n.name == qual][0]
    hfn = [n for n in ast.parse(hsrc).body if isinstance(n, ast.FunctionDef) and n.name == qual][0]
    mids = [("rt_engine:%s:%s:%s" % (qual, op, path), op, path) for op, path, _ in mc.mutants(hfn, hsrc)]
    order = [mid for mid, _, _ in mids]
    st = {"kind": case["kind"], "base_tool": {"exit": tool["exit"], "summary": tool["summary"],
                                             "stderr_tail": tool["stderr_tail"] if tool["exit"] == 2 else ""},
          "base_out": tool["out_records"], "all_mutants": order,
          "base_out_ids_equal_mutants": [x for x, _ in tool["out_records"]] == order}
    deco = deco_probe(step, head, qual) if any(p.startswith("decorator_list") for _, _, p in mids) else {}
    st["decorator_probe"] = deco
    res_c9 = dict(results)
    for mid, d in deco.items():
        res_c9[mid] = d["c9_result"]
    exp = case["expect"]
    full = classify(bfn, hfn, mids)
    st["targets_auditor"] = [x for x in order if x in full]
    st["not_targeted_auditor"] = [x for x in order if x not in full]
    pr = predict(full, order, res_c9, len(order))
    st["predicted_full"] = pr
    st["expect_holds_full"] = expect_holds(exp, pr)
    # 판별력: 변형마다
    var = {}
    for v in ALL_VARIANTS:
        key = "-".join(v)
        if v == ["DECO_NOOP"]:
            tv, rv = full, results    # 계약 9 없음 = base 치환(NOOP) 결과
        else:
            tv, rv = classify(bfn, hfn, mids, frozenset(v)), res_c9
        pv = predict(tv, order, rv, len(order))
        var[key] = {"targets_n": len([x for x in order if x in tv]), "pred_exit": pv["exit"], "pred_survivors": pv["survivors"],
                    "step_fails": not expect_holds(exp, pv)["holds"]}
    st["variants"] = var
    st["aimed"] = {"-".join(v): var["-".join(v)]["step_fails"] for v in AIMED[step]}
    res["steps"][step] = st
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

# 변형별: 어느 단계가 잡는가
cover = {}
for v in ALL_VARIANTS:
    key = "-".join(v)
    cover[key] = [s for s, st in res["steps"].items() if st["variants"][key]["step_fails"]]
res["variant_caught_by"] = cover
with open(outp, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
summ = {s: {"base_exit": st["base_tool"]["exit"], "n_all": len(st["all_mutants"]), "n_target": len(st["targets_auditor"]),
            "full_holds": st["expect_holds_full"], "aimed_caught": st["aimed"]} for s, st in res["steps"].items()}
print(json.dumps({"steps": summ, "variant_caught_by": cover}, ensure_ascii=False, indent=1))
