"""T0 계약 6·7 합성 트리 만들기(측정 전용, 격리 복제본 작업 트리를 제자리에서 고친다).

    C:/Python314/python.exe -B make_synth.py <복제본 루트> <move|copy|rebind>

move  : sizing_recipe.py에서 check_quasi_static·size_transistor·_build_theta_evaluator의 def 텍스트(데코레이터 포함)를 잘라
        새 파일 A/zz_loc_free_probe.py에 붙이고, 원래 파일 끝에 `from zz_loc_free_probe import <이름>`을 더한다(계약 6).
copy  : size_transistor def 텍스트를 새 파일에 복사(원래 것도 남김, 계약 7 -- 정의 파일 2개).
rebind: move 트리 + 다른 엔진 파일(topology_library.py) 끝에 `_L_ROLE_MULTIPLIERS = {}`(거부해야 할 입력 -- 엔진 어느 파일이든).
새 파일 머리 = `from __future__ import annotations`(원본과 같은 기능 집합 -- import 시점 주석 평가로 깨지지 않게).
"""
import ast
import os
import sys

ROOT, MODE = sys.argv[1], sys.argv[2]
A = os.path.join(ROOT, "skills", "analog-gmid-design", "assets")
SR = os.path.join(A, "sizing_recipe.py")
NEW = os.path.join(A, "zz_loc_free_probe.py")


def rd(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return fh.read().replace("\r\n", "\n")


def wr(p, t):
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(t)


src = rd(SR)
lines = src.split("\n")
tree = ast.parse(src)
names = ["size_transistor"] if MODE == "copy" else ["check_quasi_static", "size_transistor", "_build_theta_evaluator"]
spans = []
for n in tree.body:
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names:
        start = min([n.lineno] + [d.lineno for d in n.decorator_list])
        spans.append((start, n.end_lineno, n.name))
assert sorted(s[2] for s in spans) == sorted(names), spans
chunks = ["\n".join(lines[s - 1:e]) for s, e, _ in sorted(spans)]
wr(NEW, "from __future__ import annotations\n\n\n" + "\n\n\n".join(chunks) + "\n")
if MODE in ("move", "rebind"):
    keep = [True] * len(lines)
    for s, e, _ in spans:
        for i in range(s - 1, e):
            keep[i] = False
    body = "\n".join(l for l, k in zip(lines, keep) if k).rstrip("\n")
    body += "\n\n" + "".join("from zz_loc_free_probe import %s  # noqa: E402\n" % nm for nm in names)
    wr(SR, body)
if MODE == "rebind":
    tl = os.path.join(A, "topology_library.py")
    wr(tl, rd(tl).rstrip("\n") + "\n\n_L_ROLE_MULTIPLIERS = {}\n")
print(MODE, "ok", [(s, e, nm) for s, e, nm in sorted(spans)])
