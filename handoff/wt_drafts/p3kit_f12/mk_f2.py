"""F1/F2 작성 전 실측(측정 전용): 격리 복제본 작업 트리에 F2 모양을 적용한다(커밋은 호출자가).

    python -B mk_f2.py <복제본 루트> [--acf]

* SR·TL·DR shim 파일 삭제.
* SD 최상위 재수출 줄(`from <N3.10 줄기> import …`, level 0)에서 SD 단위가 어느 유효 범위에서도 읽지 않는 이름을 뺀다(줄이 비면 줄 삭제).
  'SD가 읽는 이름' = G1 시제품 SourceIndex.global_names(SD)의 합(작업 트리 소스로 색인).
* --acf: audit_current_forced.py(--keep split)의 재수출 줄에도 같은 규칙.
SD가 읽는 이름의 재수출은 남긴다(design 30 §2.2 3차 검토 m3). 줄 위치는 그대로(D-22 (4) '머리로 올려도 된다'는 쓰지 않는다).
"""
import ast
import os
import sys

ROOT = sys.argv[1]
ACF = "--acf" in sys.argv[2:]
A = os.path.join(ROOT, "skills", "analog-gmid-design", "assets")
sys.path.insert(0, os.path.join(ROOT, "tools", "gates"))
import reachability as rch  # noqa: E402
import import_layering as il  # noqa: E402

MODT = il.mod_table(open(os.path.join(ROOT, "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"), encoding="utf-8").read())
for f in ("sizing_recipe.py", "topology_library.py", "design_report.py"):
    p = os.path.join(A, f)
    if os.path.exists(p):
        os.remove(p)
targets = ["stick_diagram.py"] + (["audit_current_forced.py"] if ACF else [])
report = {}
for f in targets:
    p = os.path.join(A, f)
    src = open(p, encoding="utf-8", newline="").read()
    rel = "skills/analog-gmid-design/assets/" + f
    idx = rch.SourceIndex({rel: src})
    read = set()
    for gn in idx.global_names(rel).values():
        read |= set(gn)
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)
    edits = []
    dropped = []
    for n in tree.body:
        if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module in MODT and n.module != f[:-3] \
                and not (f == "audit_current_forced.py" and n.module == "stick_diagram"):   # ACF의 base import(SD)는 임시 재수출이 아니다
            keep = [a for a in n.names if (a.asname or a.name) in read]
            drop = [a for a in n.names if (a.asname or a.name) not in read]
            if not drop:
                continue
            dropped += [a.asname or a.name for a in drop]
            ind = lines[n.lineno - 1][:len(lines[n.lineno - 1]) - len(lines[n.lineno - 1].lstrip())]
            new = "" if not keep else ind + "from %s import %s\n" % (n.module, ", ".join(
                a.name + (" as " + a.asname if a.asname else "") for a in keep))
            edits.append((n.lineno, n.end_lineno, new))
    for a, b, new in sorted(edits, reverse=True):
        lines[a - 1:b] = [new] if new else []
    open(p, "w", encoding="utf-8", newline="").write("".join(lines))
    report[f] = sorted(dropped)
    print(f, "dropped", len(dropped), sorted(dropped))
