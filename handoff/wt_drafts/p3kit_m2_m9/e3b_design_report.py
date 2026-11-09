import ast, re, subprocess, symtable, sys
sys.stdout.reconfigure(encoding="utf-8")
iso, b0, head, excl = sys.argv[1:5]
SD = "skills/analog-gmid-design/assets/design_report.py"
IMPL = {"__file__", "__name__", "__doc__", "__dict__", "__spec__", "__loader__", "__package__", "__builtins__", "__cached__"}
IMPF = ("import_module", "_import", "__import__")
ATTRF = ("getattr", "hasattr", "setattr", "delattr")
G = ["git", "-c", "core.quotepath=off", "-C", iso]
errs = []

def show(rev, p):
    s = subprocess.run(G + ["show", rev + ":" + p], capture_output=True)
    if s.returncode != 0:
        errs.append("ERROR show %s:%s" % (rev, p))
        return None
    return s.stdout

def sd_names(rev):   # SD 최상위 바인딩: (정의 = def·class·대입, 가져옴 = import)
    src = show(rev, SD)
    if src is None:
        return set(), set()
    defs, imps = set(), set()
    for s in symtable.symtable(src.decode("utf-8"), SD, "exec").get_symbols():
        if s.is_imported():
            imps.add(s.get_name())
        elif s.is_assigned() or s.is_namespace():
            defs.add(s.get_name())
    if "__getattr__" in defs | imps:
        errs.append("ERROR SD에 모듈 __getattr__ (%s) -- 이름 해석을 정적으로 판정할 수 없다" % rev)
    return defs, imps

def file_reads(tree):   # SD 모듈 식(별칭·import_module 결과·그것을 돌려주는 함수 호출)에서 읽는 이름
    al, fn_sd = set(), set()
    def is_sd(e):
        if isinstance(e, ast.Name):
            return e.id in al
        if isinstance(e, ast.Call):
            f = e.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if nm in IMPF and e.args and isinstance(e.args[0], ast.Constant) and e.args[0].value == "design_report":
                return True
            return isinstance(f, ast.Name) and f.id in fn_sd
        return False
    ch = True
    while ch:
        ch = False
        for n in ast.walk(tree):
            new = set()
            if isinstance(n, ast.Import):
                new = {a.asname or a.name for a in n.names if a.name == "design_report"}
            elif isinstance(n, (ast.Assign, ast.AnnAssign, ast.NamedExpr)) and n.value is not None and is_sd(n.value):
                tg = n.targets if isinstance(n, ast.Assign) else [n.target]
                new = {t.id for t in tg if isinstance(t, ast.Name)}
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name not in fn_sd and any(
                    isinstance(r, ast.Return) and r.value is not None and is_sd(r.value) for r in ast.walk(n)):
                fn_sd.add(n.name); ch = True
            if new - al:
                al |= new; ch = True
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module == "design_report":
            out |= {(n.lineno, a.name) for a in n.names}          # "*"는 해석 불가 이름으로 FAIL
        elif isinstance(n, ast.Attribute) and is_sd(n.value):
            out.add((n.lineno, n.attr))
        elif isinstance(n, ast.Call) and n.args and is_sd(n.args[0]) and (
                (n.func.id if isinstance(n.func, ast.Name) else getattr(n.func, "attr", "")) in ATTRF):
            a = n.args[1] if len(n.args) > 1 else None
            out.add((n.lineno, a.value if isinstance(a, ast.Constant) and isinstance(a.value, str) else "<동적 이름>"))
    return out

def reads(rev):   # {경로: {(줄, 이름)}} -- 제외 집합(D-9)과 SD 자신 밖의 추적 .py
    r = subprocess.run(G + ["grep", "-z", "-l", "-F", "design_report", rev, "--", "*.py"], capture_output=True)
    if r.returncode not in (0, 1):
        errs.append("ERROR git grep %s rc=%d" % (rev, r.returncode))
        return {}
    res = {}
    for ent in r.stdout.decode("utf-8").split("\0"):
        if not ent:
            continue
        if not ent.startswith(rev + ":"):
            errs.append("ERROR git grep 항목 " + ent)
            continue
        p = ent[len(rev) + 1:]
        if p == SD or re.search(excl, p):
            continue
        src = show(rev, p)
        if src is None:
            continue
        try:
            res[p] = file_reads(ast.parse(src))
        except SyntaxError:
            res[p] = {(0, "<PARSE-ERROR>")}
    return res

hd, hi = sd_names(head)
bd, bi = sd_names(b0)
hr, br = reads(head), reads(b0)
MARK = lambda n: n == "*" or n.startswith("<")   # 표지 이름: star import·"<동적 이름>"·"<PARSE-ERROR>"(v8 -- 5차 검토 B2)
pre = {(p, n) for p, s in br.items() for _, n in s
       if not MARK(n) and n not in bd | bi | IMPL}  # base에서 이미 안 풀리던 실제 이름만. 표지는 base에 있어도 면제하지 않는다(head에서 FAIL)
moved_out = bd - hd                                                                    # base SD 정의 중 head SD에 정의가 없는 이름
live = sorted(p for p, s in br.items() if any(n in moved_out for _, n in s))
print("E3b LIVE moved_out=%d base_files_reading_moved_out=%d pre_existing=%d" % (len(moved_out), len(live), len(pre)))
fails = sorted("%s:%d %s" % (p, ln, n) for p, s in hr.items() for ln, n in s
               if n not in hd | hi | IMPL and (p, n) not in pre)
for e in errs:
    print(e)
for f in fails:
    print("E3b FAIL " + f)
if not moved_out or not live:
    print("E3b INVALID: base에서 SD 밖으로 나간 이름을 읽는 추적 파일 0(명령 고장 또는 base 오지정)")
elif not errs and not fails:
    print("E3b PASS")
sys.exit(3 if errs else 0)
