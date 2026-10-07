"""반환 경로 구조 확인(AST) -- run_matching_safety_with_finger_growth.
usage: python return_paths.py <sizing_recipe.py> <out.json>
중첩 def 안은 제외하고 바깥 함수의 모든 return을 찾아, 같은 블록에서 바로 앞 문장이
`... = _finalize(...)` 대입인지 본다. _finalize 안 _backfill_interdig_ok 호출, 바깥(중첩 def 밖)
_backfill_interdig_ok 호출, relaxed_pairs.append 자리와 그 조건 사슬도 적는다."""
import ast, json, sys

src_path, out_path = sys.argv[1], sys.argv[2]
src = open(src_path, encoding="utf-8").read()
tree = ast.parse(src)
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
          and n.name == "run_matching_safety_with_finger_growth")
lines = src.splitlines()


def walk_outer(node, parents):
    """중첩 def/lambda/class 안은 내려가지 않는다. (node, parents) 생성."""
    for field, value in ast.iter_fields(node):
        kids = value if isinstance(value, list) else [value]
        for k in kids:
            if isinstance(k, ast.AST):
                if isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                    continue
                yield k, parents + [(node, field)]
                yield from walk_outer(k, parents + [(node, field)])


def is_call_to(node, name):
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name


returns = []
backfill_outer = []
appends = []
for node, parents in walk_outer(fn, []):
    if isinstance(node, ast.Return):
        par, field = parents[-1]
        block = getattr(par, field)
        idx = block.index(node)
        prev = block[idx - 1] if idx > 0 else None
        via = bool(prev is not None and isinstance(prev, ast.Assign) and is_call_to(prev.value, "_finalize"))
        reason_kw = None
        if isinstance(node.value, ast.Dict):
            for k, v in zip(node.value.keys, node.value.values):
                if isinstance(k, ast.Constant) and k.value == "unresolved_reason":
                    reason_kw = ast.unparse(v)
        conds = [ast.unparse(p.test)[:90] for p, f in parents if isinstance(p, (ast.If, ast.While)) and f == "body"]
        conds += ["for " + ast.unparse(p.target) for p, f in parents if isinstance(p, ast.For)]
        returns.append({"line": node.lineno, "end_line": node.end_lineno,
                        "prev_line": prev.lineno if prev is not None else None,
                        "prev_text": lines[prev.lineno - 1].strip() if prev is not None else None,
                        "via_finalize": via, "unresolved_reason_expr": reason_kw,
                        "enclosing": conds})
    if is_call_to(node, "_backfill_interdig_ok"):
        backfill_outer.append({"line": node.lineno, "text": lines[node.lineno - 1].strip()})
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "append" and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "relaxed_pairs"):
        conds = [ast.unparse(p.test) for p, f in parents if isinstance(p, ast.If) and f == "body"]
        appends.append({"line": node.lineno, "enclosing_if_body": conds})

nested = {n.name: n for n in fn.body if isinstance(n, ast.FunctionDef)}
fin = nested.get("_finalize")
fin_calls = []
if fin is not None:
    for n in ast.walk(fin):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            fin_calls.append({"line": n.lineno, "func": n.func.id, "args": [ast.unparse(a) for a in n.args]})
# relaxed_pairs 이름을 쓰는 모든 자리(바깥, 중첩 def 밖) -- 재대입·변경 여부
rp_uses = []
for node, parents in walk_outer(fn, []):
    if isinstance(node, ast.Name) and node.id == "relaxed_pairs":
        rp_uses.append({"line": node.lineno, "ctx": type(node.ctx).__name__, "text": lines[node.lineno - 1].strip()[:110]})

out = {"file": src_path, "def_line": fn.lineno, "def_end": fn.end_lineno,
       "nested_defs": sorted(nested), "returns": returns,
       "all_returns_via_finalize": all(r["via_finalize"] for r in returns),
       "backfill_calls_outside_nested": backfill_outer,
       "finalize_calls": fin_calls,
       "relaxed_pairs_append": appends, "relaxed_pairs_name_uses": rp_uses}
json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ("all_returns_via_finalize", "backfill_calls_outside_nested")}, ensure_ascii=False))
for r in returns:
    print(r["line"], r["via_finalize"], r["unresolved_reason_expr"], r["prev_text"], r["enclosing"])
print("finalize:", fin_calls)
print("append:", appends)
