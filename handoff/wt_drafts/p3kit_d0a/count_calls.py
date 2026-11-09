"""D0a 계약 6 관찰(측정 전용): 시제품 plan 한 번 실행의 ast.parse·read_tree·SourceIndex·symtable 호출 수와 읽은 소스 파일 수.
    python -B count_calls.py <root> <move_plan 시제품> <출력 JSON> -- <plan 인자…>
"""
import ast, json, runpy, sys
root, tool, out = sys.argv[1:4]
args = sys.argv[sys.argv.index("--") + 1:]
sys.path.insert(0, root + "/tools/gates")
import reachability as rch
cnt = {"ast.parse": 0, "read_tree": 0, "SourceIndex": 0, "files_read": 0}
_p, _rt, _si = ast.parse, rch.read_tree, rch.SourceIndex.__init__
def p(*a, **k):
    cnt["ast.parse"] += 1; m = k.get("mode", a[2] if len(a) > 2 else "exec"); cnt["mode_" + m] = cnt.get("mode_" + m, 0) + 1; return _p(*a, **k)
def rt(*a, **k):
    cnt["read_tree"] += 1; r = _rt(*a, **k); cnt["files_read"] += len(r); return r
def si(self, *a, **k):
    cnt["SourceIndex"] += 1; return _si(self, *a, **k)
ast.parse, rch.read_tree, rch.SourceIndex.__init__ = p, rt, si
sys.argv = [tool] + args
try:
    runpy.run_path(tool, run_name="__main__")
except SystemExit as e:
    cnt["exit"] = e.code
cnt["G1_STATS"] = dict(getattr(rch, "G1_STATS", {}))
open(out, "w", encoding="utf-8").write(json.dumps(cnt))
