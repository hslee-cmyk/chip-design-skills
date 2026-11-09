"""F1/F2 작성 전 실측(측정 전용 -- 역할 산출물 아님, 판정 도구 아님. 작성자 != 검증자).

모의 M9 병합본(rev)에서 추적 .py가 엔진 split 모듈(SR·TL·DR·SD)에서 읽는 이름을 AST로 모으고, F1이 바꿔야 할 곳을 계산한다.

    python -B f12_callers.py <복제본 루트> <rev> <out.json>

* 엔진 모듈 식(E3b `file_reads`를 모듈 넷으로 일반화): `import X [as a]`의 이름, `import_module`·`_import`·`__import__("X")` 호출,
  그것을 대입받은 이름, 그것을 돌려주는 함수의 호출. 읽는 곳: `from X import N`(form=from), 모듈 식 `.N`(attr),
  `getattr/hasattr/setattr/delattr(모듈 식, "N")`(getattr), `monkeypatch.setattr(모듈 식, "N", …)`(getattr).
  모듈 식만 쓰고 이름을 읽지 않는 곳은 form=bare(예: `import sizing_recipe` 존재 확인).
* F2 삭제 집합(design 30 §2.2): SR·TL·DR 파일 전체 + SD 최상위 재수출 줄(`from <N3.10 줄기> import …`)의 이름 중 SD 단위가
  어느 유효 범위에서도 읽지 않는 것(G1 시제품 `SourceIndex.global_names` 합).
* 목적지: 이름 N을 모듈 X에서 읽으면 `binding_origin(X, N)`(G1 시제품)의 정의 파일. SD에 남는 이름은 `stick_diagram`.
* D-17: 엔진 모듈 식 속성에 대입(`Assign`·`AugAssign`·`AnnAssign` 대상) 또는 `setattr`류로 쓰는 곳 -- 이름마다 정의 파일과
  '호출자 모듈'(그 정의를 자기 모듈 전역으로 읽는 소스 파일, F2 뒤 기준: SR·TL·DR shim 제외).
"""
import ast
import json
import os
import re
import subprocess
import sys

ROOT, REV, OUT = sys.argv[1:4]
A = "skills/analog-gmid-design/assets/"
ENG = {"sizing_recipe", "topology_library", "design_report", "stick_diagram"}
SHIMS = {"sizing_recipe", "topology_library", "design_report"}
IMPF = ("import_module", "_import", "__import__")
ATTRF = ("getattr", "hasattr", "setattr", "delattr")
sys.path.insert(0, os.path.join(ROOT, "tools", "gates"))
import reachability as rch  # noqa: E402  (G1 시제품 설치본)
import import_layering as il  # noqa: E402


def git(*a):
    r = subprocess.run(["git", "-c", "core.quotepath=off", "-C", ROOT] + list(a), capture_output=True)
    if r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr.decode("utf-8", "replace")))
    return r.stdout


files = rch.read_tree(ROOT, REV, rch.SOURCE_GLOBS)
idx = rch.SourceIndex(files)
plan = git("show", REV + ":docs/01-plan/features/gain-budget-gmid-sizing.plan.md").decode("utf-8")
MODT = il.mod_table(plan)
SD = A + "stick_diagram.py"

# ---- F2 삭제 집합(SD 재수출 중 SD가 읽지 않는 이름)
sd_tree = idx.tree(SD)
sd_rex = {}
for n in sd_tree.body:
    if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module in MODT and n.module != "stick_diagram":
        for a in n.names:
            sd_rex[a.asname or a.name] = n.module
sd_read = set()
for key, gn in idx.global_names(SD).items():
    sd_read |= set(gn)
sd_drop = sorted(nm for nm in sd_rex if nm not in sd_read)
sd_keepimp = sorted(nm for nm in sd_rex if nm in sd_read)


def dest(mod, name):
    p = A + mod + ".py"
    if mod == "stick_diagram" and name not in sd_drop:
        o = idx.binding_origin(p, name)
        return "stick_diagram", o
    o = idx.binding_origin(p, name)
    if o and o[0] == "def":
        return o[1][len(A):-3] if o[1].startswith(A) else o[1], o
    return None, o


def engine_reads(tree):
    al, fn_eng = {}, {}

    def mod_of(e):
        if isinstance(e, ast.Name):
            return al.get(e.id)
        if isinstance(e, ast.Call):
            f = e.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if nm in IMPF and e.args and isinstance(e.args[0], ast.Constant) and isinstance(e.args[0].value, str) \
                    and e.args[0].value.split(".")[0] in ENG:
                return e.args[0].value.split(".")[0]
            if isinstance(f, ast.Name) and f.id in fn_eng:
                return fn_eng[f.id]
        return None
    ch = True
    while ch:
        ch = False
        for n in ast.walk(tree):
            new = {}
            if isinstance(n, ast.Import):
                for a in n.names:
                    if a.name.split(".")[0] in ENG:
                        new[a.asname or a.name.split(".")[0]] = a.name.split(".")[0]
            elif isinstance(n, (ast.Assign, ast.AnnAssign, ast.NamedExpr)) and getattr(n, "value", None) is not None and mod_of(n.value):
                tg = n.targets if isinstance(n, ast.Assign) else [n.target]
                for t in tg:
                    if isinstance(t, ast.Name):
                        new[t.id] = mod_of(n.value)
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name not in fn_eng:
                for r in ast.walk(n):
                    if isinstance(r, ast.Return) and r.value is not None and mod_of(r.value):
                        fn_eng[n.name] = mod_of(r.value)
                        ch = True
                        break
            for k, v in new.items():
                if al.get(k) != v:
                    al[k] = v
                    ch = True
    reads, bare, writes = [], [], []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module and n.module.split(".")[0] in ENG:
            for a in n.names:
                reads.append({"line": n.lineno, "mod": n.module.split(".")[0], "name": a.name, "form": "from"})
        elif isinstance(n, ast.Attribute) and mod_of(n.value):
            reads.append({"line": n.lineno, "mod": mod_of(n.value), "name": n.attr, "form": "attr",
                          "via": n.value.id if isinstance(n.value, ast.Name) else type(n.value).__name__})
        elif isinstance(n, ast.Call) and n.args:
            f = n.func
            fnm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if fnm in ATTRF and mod_of(n.args[0]):
                a = n.args[1] if len(n.args) > 1 else None
                nm = a.value if isinstance(a, ast.Constant) and isinstance(a.value, str) else "<동적 이름>"
                reads.append({"line": n.lineno, "mod": mod_of(n.args[0]), "name": nm, "form": "getattr", "fn": fnm})
                if fnm in ("setattr", "delattr"):
                    writes.append({"line": n.lineno, "mod": mod_of(n.args[0]), "name": nm, "form": fnm})
        if isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            tg = n.targets if isinstance(n, ast.Assign) else [n.target]
            for t in tg:
                for x in ast.walk(t):
                    if isinstance(x, ast.Attribute) and isinstance(x.ctx, ast.Store) and mod_of(x.value):
                        writes.append({"line": n.lineno, "mod": mod_of(x.value), "name": x.attr, "form": type(n).__name__})
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.split(".")[0] in ENG:
                    bare.append({"line": n.lineno, "mod": a.name.split(".")[0], "alias": a.asname or a.name})
        if isinstance(n, ast.Call):
            f = n.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if nm in IMPF and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str) \
                    and n.args[0].value.split(".")[0] in ENG:
                bare.append({"line": n.lineno, "mod": n.args[0].value.split(".")[0], "call": nm})
    return reads, bare, writes, al, fn_eng


tracked = [p for p in git("ls-tree", "-r", "--name-only", "-z", REV).decode("utf-8").split("\0") if p.endswith(".py")]
res = {"rev": git("rev-parse", REV).decode().strip(), "sd_reexport_names": len(sd_rex), "sd_drop": sd_drop,
       "sd_keep_import": sd_keepimp, "files": {}}
for p in tracked:
    src = git("show", REV + ":" + p)
    if not re.search(rb"sizing_recipe|topology_library|design_report|stick_diagram", src):
        continue
    if p in (A + m + ".py" for m in ENG):
        continue
    try:
        tree = ast.parse(src)
    except SyntaxError:
        res["files"][p] = {"parse_error": True}
        continue
    reads, bare, writes, al, fn = engine_reads(tree)
    need, dests, per_alias = [], {}, {}
    for r in reads:
        d, o = dest(r["mod"], r["name"])
        r["dest"] = d
        if r["mod"] in SHIMS or (r["mod"] == "stick_diagram" and r["name"] in sd_drop):
            need.append(r)
        if r["form"] in ("attr", "getattr"):
            per_alias.setdefault(r.get("via", "call") + "@" + r["mod"], set()).add(d)
    shim_bare = [b for b in bare if b["mod"] in SHIMS]
    if not reads and not bare and not writes:
        continue
    res["files"][p] = {"reads": reads, "bare": bare, "writes": writes, "aliases": al, "fn_mod": fn,
                       "needs_change": bool(need or shim_bare),
                       "need": need, "alias_dests": {k: sorted(x or "?" for x in v) for k, v in per_alias.items()}}


# ---- D-17 호출자 모듈
def callers(defp, name):
    out = []
    for p in idx.paths():
        if p in (A + m + ".py" for m in SHIMS):
            continue
        for key, gn in idx.global_names(p).items():
            if name in gn and idx.binding_origin(p, name) == ("def", defp, name):
                out.append(p[len(A):] if p.startswith(A) else p)
                break
    return sorted(set(out))


d17 = []
for p, info in res["files"].items():
    for w in info.get("writes", []):
        d, o = dest(w["mod"], w["name"])
        defp = o[1] if o and o[0] == "def" else None
        d17.append({"file": p, "line": w["line"], "mod": w["mod"], "name": w["name"], "form": w["form"],
                    "def_file": defp[len(A):] if defp and defp.startswith(A) else defp,
                    "callers": callers(defp, w["name"]) if defp else []})
res["d17"] = d17
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1, default=sorted)
nf = [p for p, i in res["files"].items() if i.get("needs_change")]
print("files_with_engine_refs", len(res["files"]), "needs_change", len(nf), "sd_drop", len(sd_drop), "d17", len(d17))
