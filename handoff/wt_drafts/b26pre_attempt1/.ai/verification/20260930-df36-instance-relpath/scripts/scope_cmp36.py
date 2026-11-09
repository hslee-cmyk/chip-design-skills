"""순수 변경 범위(auditor 작성, DF-36): base·병합본 stick_diagram.py 모듈 AST 비교.
(1) 병합본 최상위에서 새 def _topology_ref_relpath를 빼면 최상위 문장 수가 base와 같고, save_instance_json 외 모든 최상위 문장 ast.dump가 같다
(2) save_instance_json: 병합본 함수에서 data dict의 "topology_ref" 값 식을 base의 식(Name topology_json_path)으로 되돌리면 base 함수 ast.dump와 같다
(3) 새 헬퍼의 문자열 상수 목록(docstring 제외) -- 회로·파일 이름 리터럴 없음 확인용, 그리고 library 회로 이름·'.topology.json'·'library' 포함 여부
(4) git diff 변경 경로·numstat
사용: python -P scope_cmp36.py <복제본> <base> <M> <out.json>"""
import ast, glob, json, os, subprocess, sys
root, base, m, out = sys.argv[1:5]
P = "skills/analog-gmid-design/assets/stick_diagram.py"
def src(rev):
    return subprocess.run(["git", "-C", root, "show", f"{rev}:{P}"], capture_output=True, check=True).stdout.decode("utf-8")
tb, tm = ast.parse(src(base)), ast.parse(src(m))
res = {}
body_m = [n for n in tm.body if not (isinstance(n, ast.FunctionDef) and n.name == "_topology_ref_relpath")]
res["n_top_base"], res["n_top_merged"], res["n_top_merged_minus_helper"] = len(tb.body), len(tm.body), len(body_m)
diff_idx = [i for i, (a, b) in enumerate(zip(tb.body, body_m)) if ast.dump(a) != ast.dump(b)]
res["differing_top_level"] = [(i, getattr(tb.body[i], "name", type(tb.body[i]).__name__)) for i in diff_idx]
helper_idx = next(i for i, n in enumerate(tm.body) if isinstance(n, ast.FunctionDef) and n.name == "_topology_ref_relpath")
res["helper_position"] = {"index": helper_idx, "next": getattr(tm.body[helper_idx + 1], "name", None), "prev": getattr(tm.body[helper_idx - 1], "name", None)}
fb = next(n for n in tb.body if isinstance(n, ast.FunctionDef) and n.name == "save_instance_json")
fm = next(n for n in tm.body if isinstance(n, ast.FunctionDef) and n.name == "save_instance_json")
changed_values = []
class Revert(ast.NodeTransformer):
    def visit_Dict(self, node):
        self.generic_visit(node)
        for i, k in enumerate(node.keys):
            if isinstance(k, ast.Constant) and k.value == "topology_ref":
                changed_values.append(ast.unparse(node.values[i]))
                node.values[i] = ast.Name(id="topology_json_path", ctx=ast.Load())
        return node
import copy
fm_rev = Revert().visit(copy.deepcopy(fm))
res["save_instance_json_topology_ref_expr_merged"] = changed_values
res["save_instance_json_equal_after_revert"] = ast.dump(fm_rev) == ast.dump(fb)
h = tm.body[helper_idx]
doc = ast.get_docstring(h)
consts = []
for n in ast.walk(h):
    if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value != doc:
        consts.append(n.value)
res["helper_string_constants"] = consts
names = [os.path.basename(p)[:-len(".topology.json")] for p in glob.glob(os.path.join(root, "skills/analog-gmid-design/assets/library/*.topology.json"))]
res["helper_mentions_library_names"] = [x for x in names if any(x in c for c in consts)]
res["helper_mentions_topology_suffix_or_library"] = [c for c in consts if ".topology.json" in c or "library" in c or "folded" in c]
res["helper_names_used"] = sorted({n.id for n in ast.walk(h) if isinstance(n, ast.Name)} | {ast.unparse(n) for n in ast.walk(h) if isinstance(n, ast.Attribute)})
res["changed_paths_base_to_M"] = subprocess.run(["git", "-C", root, "diff", "--name-only", base, m], capture_output=True, check=True).stdout.decode().split()
res["numstat"] = subprocess.run(["git", "-C", root, "diff", "--numstat", base, m, "--", P], capture_output=True, check=True).stdout.decode().strip()
callers = []
for n in ast.walk(tm):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_topology_ref_relpath":
        callers.append(n.lineno)
res["helper_call_lines"] = callers
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
