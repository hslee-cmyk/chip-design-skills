"""#2 d4-delete-unwired V3 규모 시뮬레이션(scratch, 저장소 읽기 전용). 결과는 C:/g204/out_v3.txt에 append."""
import ast, os, re, subprocess, sys
CL = "C:/g204/sim"
KIT = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/v3scope_kit"
sys.path.insert(0, KIT); sys.path.insert(0, CL + "/tools/gates")
import mutate_changed as mc, reachability as rch, scope_proto as SP  # noqa: E401,E402
OUT = "C:/g204/out_v3.txt"


def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


def git(*a):
    r = subprocess.run(["git", "-C", CL] + list(a), capture_output=True)
    if r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr.decode("utf-8", "replace")))
    return r.stdout


A = "skills/analog-gmid-design/assets/"
SR, SD, TOOL = A + "sizing_recipe.py", A + "stick_diagram.py", A + "tests/tools/derive_achievable_bounds.py"
DEL = {SR: ["solve_diode_stack_current", "estimate_area_budget", "derived_bounds_path", "load_derived_bounds"],
       SD: ["MultiLeafHubParityVerdict", "check_multi_leaf_hub_parity"]}
NAMES = sum(DEL.values(), [])


def read(rev, p):
    return git("show", "%s:%s" % (rev, p)).decode("utf-8")


def delete_defs(src, names):
    t = ast.parse(src); lines = src.split("\n"); spans = []
    for n in t.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names:
            s = min([n.lineno] + [d.lineno for d in n.decorator_list]); spans.append((s, n.end_lineno))
    assert len(spans) == len(names), (names, spans)
    for s, e in sorted(spans, reverse=True):
        del lines[s - 1:e]
    return "\n".join(lines)


def edit_doc_mentions(src, names):
    """삭제 이름을 언급하는 docstring 줄만 바꾼다(주석 줄은 AST 밖)."""
    t = ast.parse(src); lines = src.split("\n"); touched = []; docs = []
    for q, n in rch.iter_defs(t):
        b0 = n.body[0] if n.body else None
        if isinstance(b0, ast.Expr) and isinstance(b0.value, ast.Constant) and isinstance(b0.value.value, str):
            docs.append((q, b0.lineno, b0.end_lineno))
    for i, L in enumerate(lines, 1):
        for nm in names:
            if re.search(r"\b%s\b" % nm, L):
                for q, s, e in docs:
                    if s <= i <= e and q.split(".")[-1] not in names:
                        lines[i - 1] = re.sub(r"\b%s\b" % nm, "<deleted:%s>" % nm, lines[i - 1]); touched.append((q, i, nm))
    return "\n".join(lines), touched


def commit(parent, files, msg, br):
    git("checkout", "--quiet", "-B", br, parent)
    for rel, txt in files.items():
        with open(os.path.join(CL, *rel.split("/")), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(txt)
        git("add", "--", rel)
    git("commit", "--quiet", "-m", msg)
    return git("rev-parse", "HEAD").decode().strip()


def measure(label, base, head):
    diff = git("diff", "--name-only", "--no-renames", "--diff-filter=AM", base, head).decode()
    targets = [p for p in diff.splitlines() if p.endswith(".py") and rch._is_source(p)]
    hf = rch.read_tree(CL, head, rch.GRAPH_PREFIXES); nodes, edges = rch.build_graph(hf)
    tests = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
             and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
    tot = {"all": 0, "N2w": 0, "N2b": 0}; rows = []
    for path in targets:
        hsrc = hf[path]; bsrc = read(base, path); bdefs = dict(rch.iter_defs(ast.parse(bsrc)))
        for q, hfn in mc.changed_defs(bsrc, hsrc):
            ms = mc.mutants(hfn, hsrc)
            w = SP.select(bdefs[q], hfn, ms, "N2w") if q in bdefs else [True] * len(ms)
            b = SP.select(bdefs[q], hfn, ms, "N2b") if q in bdefs else [True] * len(ms)
            inv = mc.inventory(edges, "%s::%s" % (path, q), tests)
            tot["all"] += len(ms); tot["N2w"] += sum(w); tot["N2b"] += sum(b)
            rows.append((path.split("/")[-1] + "::" + q, len(ms), sum(b), sum(w), len(inv), q not in bdefs))
    log("== %s base %s head %s | V3 source files %s" % (label, base[:8], head[:8], [p.split('/')[-1] for p in targets]))
    log("   changed defs %d | all(현 규칙 def 전체) %d | N2b %d | N2w(범위 정책 card 규칙) %d" % (len(rows), tot["all"], tot["N2b"], tot["N2w"]))
    for r in sorted(rows, key=lambda r: -r[1]):
        log("   %-60s all=%4d N2b=%3d N2w=%3d inv=%d%s" % (r[0], r[1], r[2], r[3], r[4], " NEW" if r[5] else ""))
    return tot


def gone(label, h):
    hf = rch.read_tree(CL, h, rch.GRAPH_PREFIXES); left = []
    for p, s in sorted(hf.items()):
        if not p.endswith(".py"):
            continue
        try:
            t = ast.parse(s)
        except SyntaxError:
            continue
        for n in ast.walk(t):
            nm = (n.id if isinstance(n, ast.Name) else n.attr if isinstance(n, ast.Attribute)
                  else n.name if isinstance(n, (ast.FunctionDef, ast.ClassDef)) else None)
            if nm in NAMES:
                left.append((p.replace(A, "A/"), n.lineno, nm))
            if isinstance(n, ast.ImportFrom):
                for a in n.names:
                    if a.name in NAMES:
                        left.append((p.replace(A, "A/"), n.lineno, "import " + a.name))
    log("GONE 잔여 AST 참조(%s, assets/** + workspaces/**, 코드 커밋만 적용한 모의 head): %d" % (label, len(left)))
    for x in left:
        log("   ", x)


if __name__ == "__main__":
    open(OUT, "w").close()
    P0 = git("rev-parse", "HEAD").decode().strip()
    log("P0 =", P0)
    sr0, sd0, tool0 = read(P0, SR), read(P0, SD), read(P0, TOOL)
    srA, sdA = delete_defs(sr0, DEL[SR]), delete_defs(sd0, DEL[SD])
    toolA = tool0.replace("book = sr.load_derived_bounds(topo)", "book = {}").replace("path = sr.derived_bounds_path(topo)", "path = None")
    assert toolA != tool0
    HA = commit(P0, {SR: srA, SD: sdA, TOOL: toolA}, "sim A: delete only", "simA")
    srB, tSR = edit_doc_mentions(srA, NAMES); sdB, tSD = edit_doc_mentions(sdA, NAMES)
    log("docstring 언급 수정 위치(B):", [(q, i, n) for q, i, n in tSR + tSD])
    HB = commit(HA, {SR: srB, SD: sdB}, "sim B: + docstring mentions", "simB")
    measure("A_delete_only", P0, HA)
    measure("B_delete_plus_docstrings", P0, HB)
    gone("A", HA)
    git("checkout", "--quiet", "sim")
