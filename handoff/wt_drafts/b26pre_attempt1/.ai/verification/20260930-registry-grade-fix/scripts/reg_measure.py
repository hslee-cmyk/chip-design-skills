"""base 레지스트리 독립 측정(순서 3, 순서 7 대조용). 사용: python -P reg_measure.py <복제본 루트> <out.json>
- §1 표 D 열, §7 소절 제목 괄호 수·표 행 수·첫 칸 백틱 이름·표 머리
- 엔진 정의 이름: A/*.py 최상위 def·class와 Class.method, workspaces/run_harness.py 최상위 def·class (AST)
- §7 이름 중 엔진에 없는 것
- §7 각 이름의 참조 위치(A/*.py, workspaces/**/*.py, tools/**/*.py, 그 밖 .py 전부; A/tests/** 는 따로) -- 파일:둘러싼 최상위 함수(클래스.메서드)
- R-4 네 이름: 위 참조 + 둘러싼 함수의 참조(한 단계 위)
- §2 표에서 W·union-find·레일 넷 집합·CMRR 행 원문
"""
import ast, json, os, re, sys

root, out = sys.argv[1], sys.argv[2]
A = "skills/analog-gmid-design/assets"
REG = "docs/03-analysis/gain-budget-gmid-sizing.function-registry.md"
text = open(os.path.join(root, REG), encoding="utf-8").read()
lines = text.split("\n")

def section(prefix):
    s = next(i for i, l in enumerate(lines) if l.startswith(prefix))
    e = next((j for j in range(s + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
    return s, e

def table_rows(block):
    rows = [l for l in block if l.startswith("|")]
    if not rows:
        return None, []
    head = [c.strip() for c in rows[0].strip("|").split("|")]
    body = [r for r in rows[1:] if not re.match(r"^\|\s*-", r)]
    return head, body

# §1
s1, e1 = section("## 1.")
h1, b1 = table_rows(lines[s1:e1])
sec1 = {}
di = h1.index("D")
for r in b1:
    c = [x.strip() for x in r.strip().strip("|").split("|")]
    sec1[c[0]] = int(c[di])

# §7
s7, e7 = section("## 7.")
subs = []
cur = None
for i in range(s7, e7):
    l = lines[i]
    m = re.match(r"^### (.+?) \((\d+)\)\s*$", l)
    if m:
        cur = {"title": m.group(1), "title_count": int(m.group(2)), "line": i + 1, "block": []}
        subs.append(cur)
    elif cur is not None:
        cur["block"].append(l)
sec7 = []
for sb in subs:
    head, body = table_rows(sb["block"])
    names = []
    for r in body:
        first = r.strip().strip("|").split("|")[0]
        bt = re.findall(r"`([^`]+)`", first)
        names.append(bt[0] if bt else None)
    sec7.append({"title": sb["title"], "title_count": sb["title_count"], "heading_line": sb["line"],
                 "table_head": head, "has_disposition_col": ("처리" in (head or [])),
                 "n_rows": len(body), "names": names})

# 엔진 정의 이름
eng = {}
def collect(path, with_methods):
    tree = ast.parse(open(path, encoding="utf-8").read())
    rel = os.path.relpath(path, root).replace("\\", "/")
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            eng.setdefault(n.name, []).append(f"{rel}:{n.lineno}")
            if with_methods and isinstance(n, ast.ClassDef):
                for m in n.body:
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        eng.setdefault(f"{n.name}.{m.name}", []).append(f"{rel}:{m.lineno}")
engine_files = sorted(f for f in os.listdir(os.path.join(root, A)) if f.endswith(".py"))
for f in engine_files:
    collect(os.path.join(root, A, f), True)
collect(os.path.join(root, "workspaces", "run_harness.py"), False)

all7 = [n for s in sec7 for n in s["names"] if n]
missing = [n for n in all7 if n not in eng]

# 참조 위치
def py_files():
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in (".git", "__pycache__")]
        for f in fn:
            if f.endswith(".py"):
                yield os.path.join(dp, f)

def refs_in(path, targets):
    try:
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src)
    except Exception as ex:
        return {"__parse_error__": [type(ex).__name__]}
    res = {}
    def walk(node, ctx):
        for ch in ast.iter_child_nodes(node):
            c2 = ctx
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                c2 = ch.name if ctx == "<module>" else f"{ctx}.{ch.name}"
                if ch.name in targets:
                    pass  # 정의 자체는 참조가 아니다
            nm = None
            if isinstance(ch, ast.Name) and ch.id in targets:
                nm = ch.id
            elif isinstance(ch, ast.Attribute) and ch.attr in targets:
                nm = ch.attr
            elif isinstance(ch, ast.alias) and ch.name in targets:
                nm = ch.name
            if nm:
                kind = "import" if isinstance(ch, ast.alias) else "ref"
                res.setdefault(nm, []).append(f"{ch.lineno if hasattr(ch,'lineno') else '?'}:{ctx}:{kind}")
            walk(ch, c2)
    walk(tree, "<module>")
    return res

targets = set(all7)
R4 = ["render_report", "gm_from_fT", "_optimize_theta_slsqp_block_coordinate", "SharedFingerWCandidate"]
refs = {}
files = sorted(py_files())
for p in files:
    rel = os.path.relpath(p, root).replace("\\", "/")
    r = refs_in(p, targets)
    for nm, locs in r.items():
        refs.setdefault(nm, {})[rel] = locs

def classify(rel):
    if rel.startswith(A + "/tests/"):
        return "tests"
    if rel.startswith(A + "/") and rel.count("/") == A.count("/") + 1:
        return "engine"
    if rel == "workspaces/run_harness.py":
        return "harness"
    return "other"

ref_summary = {}
for nm in all7:
    d = refs.get(nm, {})
    ref_summary[nm] = {k: {rel: locs for rel, locs in d.items() if classify(rel) == k} for k in ("engine", "harness", "other", "tests")}

# R-4 한 단계 위: 둘러싼 최상위 함수 이름의 참조
up = {}
for nm in R4:
    encl = set()
    for rel, locs in refs.get(nm, {}).items():
        if classify(rel) in ("engine", "harness", "other"):
            for l in locs:
                ctx = l.split(":")[1]
                if ctx != "<module>":
                    encl.add(ctx.split(".")[0])
    ups = {}
    for e in sorted(encl):
        for p in files:
            rel = os.path.relpath(p, root).replace("\\", "/")
            r = refs_in(p, {e})
            if e in r:
                ups.setdefault(e, {})[rel] = r[e]
    up[nm] = ups

# §2 원문 행
s2, e2 = section("## 2.")
want = {"W": r"^\| W 계산", "union-find": r"^\| union-find", "rail": r"^\| 레일 넷 집합", "CMRR": r"^\| CMRR"}
sec2 = {k: [l for l in lines[s2:e2] if re.match(p, l)] for k, p in want.items()}

res = {"registry_path": REG, "sec1_D": sec1, "sec7": sec7,
       "engine_files": [f"{A}/{f}" for f in engine_files] + ["workspaces/run_harness.py"],
       "n_engine_names": len(eng),
       "sec7_missing_from_engine": missing,
       "sec7_names_engine_defs": {n: eng.get(n) for n in all7},
       "refs": ref_summary, "r4_one_level_up": up, "sec2_rows": sec2}
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({"sec1_D": sec1, "sec7": [(s["title"], s["title_count"], s["n_rows"], s["table_head"]) for s in sec7],
                  "missing": missing, "n_engine_names": len(eng)}, ensure_ascii=False))
