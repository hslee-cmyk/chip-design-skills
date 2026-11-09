"""post-35 재측정 -- 정적 항목(줄 번호·출력 키·install_proto 앵커). 쓰기는 --out 파일 하나뿐.

    python -B p35_static.py lines   <tools/gates 디렉터리> --out <json>
    python -B p35_static.py anchors <install_proto.py> <tools/gates 디렉터리> --out <json>

lines: 키트가 인용한 줄을 같은 grep 식으로 다시 찾는다(줄 번호 목록).
  G1(g1_briefs.md §0.7 ③, draft_p3_g1.spec.md '작성 전 실측' 1): mutate_changed `changed_defs(` 호출·`mutants(` 호출·`json.dumps`·`make_clone`·`_rmtree_force`·
     `def _strip_doc`·`def def_hash`·`def changed_defs`, reachability `base_defs`·`new_defs`·`def main`, source_lint `def compare`·`compare(`·`def main`, rt.py `observe`, run_all.py 98행 글.
  B33(draft_b33.final.spec.md '작성 전 실측' 1·2): mutate_changed `rch.reach`·`rch.build_graph(head_files)`·`_is_source`·`except subprocess.TimeoutExpired`·
     `return "timeout"`·`killed += 1`, reachability `def _refs`·`def build_graph`·`def reach`·`def _is_source`·`seen = reach`·`new_defs = `.
  V3 정상 출력 키 순서(main의 마지막 json.dumps dict, `"survivors"`가 든 것 -- `|` 합성도 따라감).
anchors: install_proto.py의 sub(t, OLD, NEW, LABEL) 호출을 AST로 뽑아(바로 앞 `p = os.path.join(G, …)`가 정한 파일) 그 파일(CRLF→LF)에 OLD가 몇 번 있는지.
  1이 아니면 그 앵커에서 install_proto가 멈춘다(설치 전 정적 판정 -- 실제 설치는 remeasure.sh가 따로 시도).
"""
import ast
import json
import os
import re
import sys

PAT = {
    "mutate_changed.py": [("G1", r"changed_defs\(base_src"), ("G1", r"in mutants\("), ("G1", r"json\.dumps\("), ("G1", r"make_clone\("),
                          ("G1", r"_rmtree_force\("), ("G1", r"^def _strip_doc"), ("G1", r"^def def_hash"), ("G1", r"^def changed_defs"),
                          ("B33", r"rch\.reach"), ("B33", r"rch\.build_graph\(head_files\)"), ("B33", r"_is_source"),
                          ("B33", r"except subprocess\.TimeoutExpired"), ("B33", r'return "timeout"'), ("B33", r"killed \+= 1"),
                          ("35", r"not_targeted"), ("35", r"targets_by_def")],
    "reachability.py": [("G1", r"base_defs"), ("G1", r"new_defs"), ("G1", r"^def main"),
                        ("B33", r"^def _refs"), ("B33", r"^def build_graph"), ("B33", r"^def reach"), ("B33", r"^def _is_source"),
                        ("B33", r"seen = reach"), ("B33", r"new_defs = ")],
    "source_lint.py": [("G1", r"^def compare"), ("G1", r"[^f] compare\(|=\s*compare\(|\+= compare\("), ("G1", r"^def main")],
    "redteam/lib/rt.py": [("G1", r"observe")],
}


def rd(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return fh.read().replace("\r\n", "\n")


def out_keys(src):
    tree = ast.parse(src)
    main = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main"]
    keys = None
    for n in ast.walk(main[0] if main else tree):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "dumps" and n.args:
            a = n.args[0]
            parts = []
            stack = [a]
            while stack:
                x = stack.pop(0)
                if isinstance(x, ast.BinOp):
                    stack = [x.left, x.right] + stack
                elif isinstance(x, ast.IfExp):
                    stack = [x.body] + stack
                elif isinstance(x, ast.Dict):
                    parts += [k.value for k in x.keys if isinstance(k, ast.Constant)]
            if "survivors" in parts and "tool" in parts:
                keys = parts
    return keys


def lines(gdir):
    res = {}
    for rel, pats in PAT.items():
        p = os.path.join(gdir, *rel.split("/"))
        if not os.path.exists(p):
            res[rel] = None
            continue
        L = rd(p).split("\n")
        for tag, pat in pats:
            res["%s|%s|%s" % (tag, rel, pat)] = [i + 1 for i, l in enumerate(L) if re.search(pat, l)]
    ra = os.path.join(gdir, "redteam", "run_all.py")
    if os.path.exists(ra):
        L = rd(ra).split("\n")
        res["G1|redteam/run_all.py|line98"] = L[97].strip()[:120] if len(L) >= 98 else None
    res["V3 output keys"] = out_keys(rd(os.path.join(gdir, "mutate_changed.py")))
    return res


def anchors(ip, gdir):
    tree = ast.parse(open(ip, encoding="utf-8").read())
    cur = None
    res = []
    for st in tree.body:
        for n in ast.walk(st):
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and getattr(n.targets[0], "id", None) == "p" \
                    and isinstance(n.value, ast.Call) and getattr(n.value.func, "attr", None) == "join":
                cur = "/".join(a.value for a in n.value.args[1:] if isinstance(a, ast.Constant))
            if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "sub" and len(n.args) == 4:
                old, label = n.args[1], n.args[3]
                if isinstance(old, ast.Constant) and isinstance(label, ast.Constant):
                    f = os.path.join(gdir, *cur.split("/"))
                    cnt = rd(f).count(old.value) if os.path.exists(f) else None
                    res.append({"label": label.value, "file": cur, "count": cnt})
    return res


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    o = a[a.index("--out") + 1]
    if a[0] == "lines":
        r = lines(a[1])
    else:
        r = anchors(a[1], a[2])
    with open(o, "w", encoding="utf-8") as fh:
        json.dump(r, fh, ensure_ascii=False, indent=1)
    print(json.dumps(r, ensure_ascii=False)[:3000])
