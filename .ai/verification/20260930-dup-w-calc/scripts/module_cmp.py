"""순서 7: 엔진의 다른 변경 0 확인(auditor). base·병합본 git blob을 ast.parse해
  base: 계약 2 규칙의 W 식 사이트(w_sites.match) -> Name('__W_SITE__')
  병합본: width_from_id_density(...) 호출 -> Name('__W_SITE__'), 최상위 def width_from_id_density 제거
뒤 모듈 전체 ast.dump(include_attributes=False, docstring 포함)를 대조한다. 새 함수 정의 AST·시그니처·이름 가림도 본다.
그리고 범위 파일(A/*.py 최상위 + workspaces/run_harness.py) 중 sizing_recipe.py 밖 blob이 base와 같은지 본다.
사용: python -P module_cmp.py <복제본> <base> <병합본> <out.json>"""
import ast, hashlib, importlib.util, inspect, json, os, subprocess, sys
root, base, head, out = sys.argv[1:5]
sys.argv = [sys.argv[0], "base"]          # w_sites import 시 main()이 argv를 읽으므로 막는다
spec = importlib.util.spec_from_file_location("w_sites_mod", os.path.join(os.path.dirname(os.path.abspath(__file__)), "w_sites.py"))
src_ws = open(spec.origin, encoding="utf-8").read().replace("\nmain()\n", "\n")
ws = type(sys)("w_sites_mod"); exec(compile(src_ws, spec.origin, "exec"), ws.__dict__)
F = "skills/analog-gmid-design/assets/sizing_recipe.py"
NEW = "width_from_id_density"


def blob(rev, p):
    return subprocess.run(["git", "-C", root, "cat-file", "blob", f"{rev}:{p}"], capture_output=True, check=True).stdout


class Rep(ast.NodeTransformer):
    def __init__(self, pred):
        self.pred = pred
        self.n = 0

    def visit(self, node):
        if self.pred(node):
            self.n += 1
            return ast.Name(id="__W_SITE__", ctx=ast.Load())
        return super().visit(node)


res = {}
tb = ast.parse(blob(base, F).decode("utf-8"))
tm = ast.parse(blob(head, F).decode("utf-8"))
# 새 함수 정의
defs = [n for n in tm.body if isinstance(n, ast.FunctionDef) and n.name == NEW]
all_defs = [n for n in ast.walk(tm) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) and getattr(n, "name", None) == NEW]
res["new_def_count_top"] = len(defs)
res["new_def_count_any_depth"] = len(all_defs)
d = defs[0]
body = d.body[1:] if (d.body and isinstance(d.body[0], ast.Expr) and isinstance(d.body[0].value, ast.Constant) and isinstance(d.body[0].value.value, str)) else d.body
res["new_def_has_docstring"] = len(body) != len(d.body)
res["new_def_body_dump"] = [ast.dump(s, include_attributes=False) for s in body]
expect = ast.dump(ast.parse("return L * ID / IDu", mode="exec").body[0], include_attributes=False) if False else None
ref = ast.parse("def f(L, ID, IDu):\n    return L * ID / IDu\n").body[0].body[0]
res["new_def_body_is_exact_return_L_ID_div_IDu"] = len(body) == 1 and ast.dump(body[0], include_attributes=False) == ast.dump(ref, include_attributes=False)
res["new_def_signature_src"] = "def %s(%s) -> %s" % (NEW, ", ".join("%s: %s" % (a.arg, ast.unparse(a.annotation) if a.annotation else "") for a in d.args.args), ast.unparse(d.returns) if d.returns else None)
res["new_def_decorators"] = [ast.unparse(x) for x in d.decorator_list]
res["new_def_other_args"] = {"posonly": len(d.args.posonlyargs), "vararg": d.args.vararg is not None, "kwonly": len(d.args.kwonlyargs), "kwarg": d.args.kwarg is not None, "defaults": len(d.args.defaults)}
res["new_def_position"] = {"line": d.lineno, "index_in_body": tm.body.index(d), "next_top": getattr(tm.body[tm.body.index(d) + 1], "name", None), "prev_top": getattr(tm.body[tm.body.index(d) - 1], "name", None)}
# 이름 가림: 병합본 어디서든 NEW를 대입·인자·import 별칭으로 묶는가
binds = []
for n in ast.walk(tm):
    if isinstance(n, ast.Name) and n.id == NEW and not isinstance(n.ctx, ast.Load):
        binds.append(("Name-store", n.lineno))
    if isinstance(n, ast.arg) and n.arg == NEW:
        binds.append(("arg", n.lineno))
    if isinstance(n, (ast.Import, ast.ImportFrom)):
        for a in n.names:
            if (a.asname or a.name) == NEW:
                binds.append(("import", n.lineno))
    if isinstance(n, ast.Global) and NEW in n.names:
        binds.append(("global", n.lineno))
res["name_rebinds"] = binds
# 호출 형태
calls = [n for n in ast.walk(tm) if isinstance(n, ast.Call) and ((isinstance(n.func, ast.Name) and n.func.id == NEW) or (isinstance(n.func, ast.Attribute) and n.func.attr == NEW))]
res["calls_total"] = len(calls)
res["calls_by_form"] = {"Name": sum(isinstance(c.func, ast.Name) for c in calls), "Attribute": sum(isinstance(c.func, ast.Attribute) for c in calls)}
res["calls_all_3_positional_no_kw"] = all(len(c.args) == 3 and not c.keywords and not any(isinstance(a, ast.Starred) for a in c.args) for c in calls)
refs = [n.lineno for n in ast.walk(tm) if isinstance(n, ast.Name) and n.id == NEW and isinstance(n.ctx, ast.Load)]
res["name_load_refs"] = len(refs)
# 모듈 전체 대조
rb = Rep(lambda n: ws.match(n) is not None)
tb2 = rb.visit(tb)
tm.body = [n for n in tm.body if not (isinstance(n, ast.FunctionDef) and n.name == NEW)]
rm = Rep(lambda n: isinstance(n, ast.Call) and ((isinstance(n.func, ast.Name) and n.func.id == NEW) or (isinstance(n.func, ast.Attribute) and n.func.attr == NEW)))
tm2 = rm.visit(tm)
db, dm = ast.dump(tb2, include_attributes=False), ast.dump(tm2, include_attributes=False)
res["module_sites_replaced"] = {"base": rb.n, "merged": rm.n}
res["module_dump_equal_after_replacement"] = db == dm
res["module_dump_sha256"] = {"base": hashlib.sha256(db.encode()).hexdigest(), "merged": hashlib.sha256(dm.encode()).hexdigest()}
res["module_top_level_count"] = {"base": len(tb2.body), "merged_without_new_def": len(tm2.body)}
# 다른 범위 파일
others = {}
names = subprocess.run(["git", "-C", root, "diff", "--name-only", base, head], capture_output=True, check=True).stdout.decode().split()
res["changed_paths_base_to_head"] = names
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "new_def_body_dump"}, ensure_ascii=False, indent=1))
