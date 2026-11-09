"""Phase 3 design v7 -- D-22 전제(4차 검토 S5) 실측. 읽기 전용(초안 측정 -- D0b 계약 test 기대값의 근거가 아니다).

전제: MOD8·MOD9 파일이 **import 시점에** 읽는 이름 중 출처가 번호 7 이상인 다른 모듈(SD·MOD8)인 것 = 0.
import 시점 읽기 = 모듈 수준 문장(def·class 몸체 밖)의 Load 이름 ∪ def·class의 데코레이터·기본값·기반·키워드 ∪ 클래스 몸체(메서드 몸체 제외) ∪
(`from __future__ import annotations`가 없으면) def 인자·반환 주석과 모듈·클래스 수준 주석.
입력 1) 실제 저장소 커밋의 원본 파일(SR·DR·TL·ACF) -- 출처가 SD인 이름의 import 시점 읽기.
입력 2) 모의 M9 트리(p3v6_order_shim_sim `bottom7 pull`)의 MOD8·MOD9 파일 -- 출처가 SD·MOD8인 이름.
사용: python p3v7_import_time_reads.py <repo> <rev> <모의 state_M9 dir> <out.json>
"""
import ast
import json
import subprocess
import sys

REPO, REV, SIMD, OUT = sys.argv[1:5]


def import_time_loads(tree):
    fut = any(isinstance(n, ast.ImportFrom) and n.module == "__future__" and any(a.name == "annotations" for a in n.names)
              for n in tree.body)
    out = []

    def loads(node):
        for x in ast.walk(node):
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
                out.append((x.id, x.lineno))

    def head(fn):
        for d in fn.decorator_list:
            loads(d)
        a = fn.args
        for d in a.defaults + [x for x in a.kw_defaults if x is not None]:
            loads(d)
        if not fut:
            for arg in a.posonlyargs + a.args + a.kwonlyargs + [x for x in (a.vararg, a.kwarg) if x]:
                if arg.annotation is not None:
                    loads(arg.annotation)
            if fn.returns is not None:
                loads(fn.returns)

    def block(stmts, in_class):
        for s in stmts:
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
                head(s)
            elif isinstance(s, ast.ClassDef):
                for d in s.decorator_list + s.bases + [k.value for k in s.keywords]:
                    loads(d)
                block(s.body, True)
            elif isinstance(s, (ast.Import, ast.ImportFrom)):
                continue
            elif isinstance(s, ast.AnnAssign):
                if s.value is not None:
                    loads(s.value)
                if not fut:
                    loads(s.annotation)
            else:
                # 복합문(if/try/for/with)의 머리와 몸체 모두 import 시점 -- 안의 def·class는 다시 머리만
                sub = []
                for f in ("body", "orelse", "finalbody", "handlers"):
                    v = getattr(s, f, None)
                    if isinstance(v, list):
                        sub += v
                if sub:
                    for fname, val in ast.iter_fields(s):
                        if fname in ("body", "orelse", "finalbody", "handlers"):
                            continue
                        if isinstance(val, ast.AST):
                            loads(val)
                        elif isinstance(val, list):
                            for v in val:
                                if isinstance(v, ast.AST):
                                    loads(v)
                    hb = []
                    for h in getattr(s, "handlers", []) or []:
                        if h.type is not None:
                            loads(h.type)
                        hb += h.body
                    block([x for x in sub if not isinstance(x, ast.ExceptHandler)] + hb, in_class)
                else:
                    loads(s)
    block(tree.body, False)
    return out


def imported_from(tree, mods):
    m = {}
    for n in tree.body:
        if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module in mods:
            for a in n.names:
                m[a.asname or a.name] = n.module
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name in mods:
                    m[a.asname or a.name] = a.name
    return m


res = {"rev": REV, "repo_files": {}, "sim_files": {}}
A = "skills/analog-gmid-design/assets/"
for f in ("sizing_recipe.py", "design_report.py", "topology_library.py", "audit_current_forced.py"):
    src = subprocess.run(["git", "-C", REPO, "show", REV + ":" + A + f], capture_output=True, check=True).stdout
    t = ast.parse(src)
    frm = imported_from(t, {"stick_diagram"})
    hits = [(n, ln) for n, ln in import_time_loads(t) if n in frm]
    res["repo_files"][f] = {"names_from_sd": len(frm), "import_time_reads_of_sd_names": hits}
for f, hi in (("sizing_layout_convergence.py", {"stick_diagram"}),
              ("instance_report_builder.py", {"stick_diagram", "sizing_layout_convergence"})):
    t = ast.parse(open(SIMD + "/" + f, encoding="utf-8").read())
    frm = {}
    for n in ast.walk(t):   # 끝에 둔 import 줄 포함(모듈 최상위 어디든)
        if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module in hi:
            for a in n.names:
                frm[a.asname or a.name] = n.module
    hits = [(n, ln, frm[n]) for n, ln in import_time_loads(t) if n in frm]
    res["sim_files"][f] = {"names_from_mod_ge7": len(frm), "import_time_reads": hits}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({"repo": {k: len(v["import_time_reads_of_sd_names"]) for k, v in res["repo_files"].items()},
                  "repo_names_from_sd": {k: v["names_from_sd"] for k, v in res["repo_files"].items()},
                  "sim": {k: len(v["import_time_reads"]) for k, v in res["sim_files"].items()},
                  "sim_names": {k: v["names_from_mod_ge7"] for k, v in res["sim_files"].items()}}, ensure_ascii=False))
