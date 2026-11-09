"""F1 작성 전 실측(측정 전용 -- 판정 도구 시제품이 아니라 계약 문언이 판정 가능한지 보는 측정. auditor는 독립으로 쓴다).

F1 계약 2(호출부 동등)의 두 식을 base·head 커밋 쌍의 바뀐 추적 .py마다 잰다.

    python -B f12_equiv.py <복제본 루트> <base rev> <head rev> <out.json> [--d17 <f1sim.json>]

 (i) 정규화 AST 같음: 엔진·MOD 모듈 import 문(`import X`·`from X import`, X 첫 성분이 SR·TL·DR·SD 또는 그 트리의 N3.10 줄기)을 지우고,
     모듈 식(그 import가 묶은 모듈 별칭 Name, import 호출 `import_module/_import/__import__("X")`)을 `Name('<M>')`로,
     D-17 대입 문장(엔진 모듈 식 속성이 대상인 Assign)의 대상 목록을 `<D17>` 하나로 바꾼 뒤 `ast.dump`가 같다.
 (ii) 해석 같음: 읽는 곳마다 정의 출처 -- from-import 이름은 (묶는 이름 -> 정의), 모듈 식 속성·getattr 상수는 (등장 순서 -> 정의)
     -- 를 base 트리(SR·TL·DR shim 경유)와 head 트리에서 G1 시제품 binding_origin으로 푼 결과가 같다.
     정의 = ("def", 파일, 이름) 또는 외부 출처(ext/ext-module 모듈·이름). 풀리지 않는 이름은 ("unresolved", 이름) -- 양쪽 같으면 같음.
 (iii) D-17: head 대입 대상 모듈 집합 = f1sim.json `d17`의 호출자 집합(측정 입력).
"""
import ast
import json
import os
import re
import subprocess
import sys

ROOT, BASE, HEAD, OUT = sys.argv[1:5]
D17 = json.load(open(sys.argv[sys.argv.index("--d17") + 1], encoding="utf-8"))["d17"] if "--d17" in sys.argv else {}
A = "skills/analog-gmid-design/assets/"
IMPF = ("import_module", "_import", "__import__")
sys.path.insert(0, os.path.join(ROOT, "tools", "gates"))
import reachability as rch  # noqa: E402
import import_layering as il  # noqa: E402


def git(*a):
    r = subprocess.run(["git", "-c", "core.quotepath=off", "-C", ROOT] + list(a), capture_output=True)
    if r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr.decode("utf-8", "replace")))
    return r.stdout.decode("utf-8")


IB = rch.SourceIndex(rch.read_tree(ROOT, BASE, rch.SOURCE_GLOBS))
IH = rch.SourceIndex(rch.read_tree(ROOT, HEAD, rch.SOURCE_GLOBS))
MODT = il.mod_table(git("show", HEAD + ":docs/01-plan/features/gain-budget-gmid-sizing.plan.md"))
ENG = {"sizing_recipe", "topology_library", "design_report", "stick_diagram"} | set(MODT)


SD_READ = set()   # head SD가 스스로 읽는 이름(F2 뒤에도 SD에 바인딩이 남는다 -- design 30 §7.2: 그 이름의 SD import는 F1이 고치지 않는다)
for _gn in IH.global_names(A + "stick_diagram.py").values():
    SD_READ |= set(_gn)


def canon(o):
    if o[0] == "def":
        return ("def", o[1], o[2])
    if o[0] == "ext":
        return ("ext", o[-2], o[-1])
    if o[0] == "ext-module":
        return ("ext-module", o[-1])
    if o[0] == "module":
        return ("module", o[1])
    return (o[0],) + tuple(o[1:])


def resolve(idx, mod, name):
    p = A + mod + ".py"
    if p not in idx.paths():
        return ("unresolved", mod, name)
    return canon(idx.binding_origin(p, name))


def analyze(src, idx):
    t = ast.parse(src)
    al = {}
    for n in ast.walk(t):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.split(".")[0] in ENG:
                    al[a.asname or a.name.split(".")[0]] = a.name.split(".")[0]

    def call_mod(e):
        if isinstance(e, ast.Call):
            f = e.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if nm in IMPF and e.args and isinstance(e.args[0], ast.Constant) and isinstance(e.args[0].value, str) \
                    and e.args[0].value.split(".")[0] in ENG:
                return e.args[0].value.split(".")[0]
        return None
    for n in ast.walk(t):   # 별칭 = import 호출 결과를 대입받은 이름
        if isinstance(n, ast.Assign) and call_mod(n.value):
            for tg in n.targets:
                if isinstance(tg, ast.Name):
                    al[tg.id] = call_mod(n.value)

    def mod_of(e):
        if isinstance(e, ast.Name) and e.id in al:
            return al[e.id]
        return call_mod(e)
    froms, attrs, notdef, d17t = [], [], [], []
    for n in ast.walk(t):
        if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module and n.module.split(".")[0] in ENG:
            for a in n.names:
                r = resolve(idx, n.module.split(".")[0], a.name)
                froms.append((a.asname or a.name, r))
                if r[0] == "def" and r[1] != A + n.module.split(".")[0] + ".py" and not (n.module == "stick_diagram" and a.name in SD_READ):
                    notdef.append((n.lineno, n.module, a.name, r[1]))
        elif isinstance(n, ast.Attribute) and mod_of(n.value) and not isinstance(n.ctx, ast.Store):
            r = resolve(idx, mod_of(n.value), n.attr)
            attrs.append(r)
            if r[0] == "def" and r[1] != A + mod_of(n.value) + ".py" and not (mod_of(n.value) == "stick_diagram" and n.attr in SD_READ):
                notdef.append((n.lineno, mod_of(n.value), n.attr, r[1]))
        elif isinstance(n, ast.Assign):
            tg = [x for x in n.targets if isinstance(x, ast.Attribute) and mod_of(x.value)]
            if tg:
                d17t.append((tg[0].attr, sorted({mod_of(x.value) for x in tg})))
        elif isinstance(n, ast.Call) and n.args and mod_of(n.args[0]) and \
                (n.func.id if isinstance(n.func, ast.Name) else getattr(n.func, "attr", "")) in ("getattr", "hasattr"):
            a1 = n.args[1] if len(n.args) > 1 else None
            attrs.append(resolve(idx, mod_of(n.args[0]), a1.value) if isinstance(a1, ast.Constant) else ("dynamic",))

    class Norm(ast.NodeTransformer):
        def visit_Import(self, n):
            n.names = [a for a in n.names if a.name.split(".")[0] not in ENG]
            return n if n.names else None

        def visit_ImportFrom(self, n):
            return None if (n.level == 0 and n.module and n.module.split(".")[0] in ENG) else n

        def visit_Assign(self, n):
            if any(isinstance(x, ast.Attribute) and mod_of(x.value) for x in n.targets):
                n.targets = [ast.Name("<D17>", ast.Store())]
            self.generic_visit(n)
            return n

        def visit_Name(self, n):
            return ast.Name("<M>", n.ctx) if n.id in al and isinstance(n.ctx, ast.Load) else n

        def visit_Call(self, n):
            if call_mod(n):
                return ast.Name("<M>", ast.Load())
            self.generic_visit(n)
            return n
    t2 = Norm().visit(ast.parse(src))
    # 지운 import로 비게 된 블록은 pass로 맞춘다
    for n in ast.walk(t2):
        for fld in ("body", "orelse", "finalbody"):
            if isinstance(getattr(n, fld, None), list) and not getattr(n, fld) and fld == "body":
                setattr(n, fld, [ast.Pass()])
    return ast.dump(t2, include_attributes=False), sorted(froms), attrs, notdef, d17t


changed = [p for p in git("diff", "--name-only", "-z", BASE, HEAD).split("\0")
           if p.endswith(".py") and not (p.startswith(A) and "/" not in p[len(A):])]
res = {"files": {}, "summary": {}}
for p in changed:
    try:
        sb, sh = git("show", BASE + ":" + p), git("show", HEAD + ":" + p)
    except SystemExit:
        res["files"][p] = {"verdict": "absent"}
        continue
    nb, fb, ab, _nd, d17b = analyze(sb, IB)
    nh, fh, ah, ndh, d17h = analyze(sh, IH)
    fbd, fhd = dict(fb), dict(fh)
    want = {(x["name"], tuple(sorted(x["callers"]))) for x in D17.get(p, [])}
    got = {(nm, tuple(ms)) for nm, ms in d17h}
    v = {"ast_same": nb == nh, "from_same": all(fhd.get(k) == fbd[k] for k in fbd) and set(fbd) <= set(fhd),
         "attr_same": ab == ah, "def_module": not ndh, "d17_same": (want == got) if (want or got) else True}
    if ndh:
        v["not_def_module"] = ndh[:5]
    if not v["d17_same"]:
        v["d17_diff"] = [sorted(want - got)[:3], sorted(got - want)[:3]]
    if not v["from_same"]:
        v["from_diff"] = [(k, fbd[k], fhd.get(k)) for k in fbd if fhd.get(k) != fbd[k]][:5]
    if not v["attr_same"]:
        v["attr_diff"] = [(i, x, y) for i, (x, y) in enumerate(zip(ab, ah)) if x != y][:5] + ([("len", len(ab), len(ah))] if len(ab) != len(ah) else [])
    v["verdict"] = "PASS" if all((v["ast_same"], v["from_same"], v["attr_same"], v["def_module"], v["d17_same"])) else "FAIL"
    res["files"][p] = v
res["summary"] = {"files": len(changed), "pass": sum(1 for x in res["files"].values() if x.get("verdict") == "PASS"),
                  "fail": sorted(p for p, x in res["files"].items() if x.get("verdict") == "FAIL")}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1, default=list)
print(json.dumps(res["summary"], ensure_ascii=False))
