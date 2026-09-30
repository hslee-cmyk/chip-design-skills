"""순수 변경 범위(auditor 작성): base·병합본 run_harness.py 모듈 AST에서 경로 문장(base: 35행 sys.path.insert·ASSETS_DIR·WORKSPACES_DIR 대입,
병합본: WORKSPACES_DIR·_REPO_ROOT·ASSETS_DIR 대입·sys.path.insert)을 뺀 나머지 최상위 문장 ast.dump 목록이 같은지, 그리고 git diff 줄 수.
또 메인 체크아웃 표기에서 병합본 유도식이 내는 문자열(순수 문자열 계산, 메인 파일은 읽지 않는다).
사용: python -P scope_cmp.py <복제본> <base> <M> <out.json>"""
import ast, hashlib, json, ntpath, subprocess, sys
root, base, m, out = sys.argv[1:5]
def src(rev):
    return subprocess.run(["git", "-C", root, "show", f"{rev}:workspaces/run_harness.py"], capture_output=True, check=True).stdout.decode("utf-8")
def is_path_stmt(n):
    if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("ASSETS_DIR", "WORKSPACES_DIR", "_REPO_ROOT"):
        return True
    if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and ast.unparse(n.value.func) == "sys.path.insert":
        return True
    return False
res = {}
bodies = {}
for tag, rev in (("base", base), ("merged", m)):
    t = ast.parse(src(rev))
    kept = [ast.dump(n) for n in t.body if not is_path_stmt(n)]
    removed = [(n.lineno, ast.unparse(n)) for n in t.body if is_path_stmt(n)]
    bodies[tag] = kept
    res[tag] = {"n_top": len(t.body), "n_kept": len(kept), "path_stmts": removed,
                "kept_sha256": hashlib.sha256("\n".join(kept).encode()).hexdigest()}
res["kept_equal"] = bodies["base"] == bodies["merged"]
# 경로 문장 앞뒤 순서: 병합본에서 경로 문장이 엔진 import보다 앞인지
t = ast.parse(src(m))
order = [(n.lineno, type(n).__name__, ast.unparse(n)[:60]) for n in t.body[:12]]
res["merged_head_order"] = order
ns = subprocess.run(["git", "-C", root, "diff", "--numstat", base, m, "--", "workspaces/run_harness.py"], capture_output=True, check=True).stdout.decode().strip()
res["numstat"] = ns
names = subprocess.run(["git", "-C", root, "diff", "--name-only", base, m], capture_output=True, check=True).stdout.decode().split()
res["changed_paths_base_to_M"] = names
# 메인 체크아웃 표기 관찰: 병합본 식 그대로(os.path == ntpath)
MAIN = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills"
LIT_A = MAIN + r"\skills\analog-gmid-design\assets"
LIT_W = MAIN + r"\workspaces"
obs = {}
for label, f in (("backslash", MAIN + r"\workspaces\run_harness.py"),
                 ("forward_slash", MAIN.replace("\\", "/") + "/workspaces/run_harness.py"),
                 ("lowercase_drive_and_dirs", MAIN.lower() + r"\workspaces\run_harness.py")):
    w = ntpath.dirname(ntpath.abspath(f)); a = ntpath.join(ntpath.dirname(w), "skills", "analog-gmid-design", "assets")
    obs[label] = {"__file__": f, "WORKSPACES_DIR": w, "ASSETS_DIR": a, "equals_literals": [w == LIT_W, a == LIT_A]}
res["main_checkout_string_observation"] = obs
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("kept_equal", "numstat", "changed_paths_base_to_M")}, ensure_ascii=False))
print(json.dumps(res["base"]["path_stmts"], ensure_ascii=False)); print(json.dumps(res["merged"]["path_stmts"], ensure_ascii=False))
print(json.dumps(obs, ensure_ascii=False, indent=0))
