"""import 계층 검사 (05-role-separation design §10, 계획 N3.10).

    $PY import_layering.py --root <저장소 루트> [--plan <계획서>]

MOD 번호(계획 N3.10 표를 직접 읽는다: `ID`=MODn, `파일`)의 그래프에서 **큰 번호로의 import**와 **순환**을 FAIL.
규칙 원문: "import는 번호가 작은 모듈 쪽으로만, 순환 0". 표에 있는 파일 중 저장소에 있는 것만 본다(Phase 3 전에는
없는 파일이 많다). exit 0 PASS / 1 FAIL / 2 실행 오류.
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys

import role_paths as rp

ASSETS = "skills/analog-gmid-design/assets"


def mod_table(plan_text):
    header, rows = rp.read_section_table(plan_text, "### N3.10 ")
    ci = [i for i, h in enumerate(header) if h.strip() == "ID"]
    cf = [i for i, h in enumerate(header) if h.strip() == "파일"]
    if len(ci) != 1 or len(cf) != 1:
        raise rp.GateError("N3.10 표 머리에서 ID·파일 열을 찾지 못함")
    out = {}
    for r in rows:
        m = re.fullmatch(r"MOD([0-9]+)", r[ci[0]].strip())
        f = re.search(r"`([A-Za-z0-9_]+)\.py`", r[cf[0]])
        if not m or not f:
            raise rp.GateError("N3.10 행 형식 위반: %r" % r[:2])
        out[f.group(1)] = int(m.group(1))
    return out


def imports_of(src):
    names = set()
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Import):
            names |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            names.add(n.module.split(".")[0])
        elif isinstance(n, ast.ImportFrom) and n.level > 0 and n.module:
            names.add(n.module.split(".")[0])
    return names


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="import_layering.py")
    ap.add_argument("--root", required=True)
    ap.add_argument("--plan", default=None)
    try:
        ns = ap.parse_args(argv)
    except SystemExit:
        return 2
    try:
        plan = ns.plan or os.path.join(ns.root, *rp.PLAN_PATH.split("/"))
        with open(plan, "rb") as fh:
            table = mod_table(fh.read().decode("utf-8"))
        present = {m: n for m, n in table.items() if os.path.isfile(os.path.join(ns.root, *ASSETS.split("/"), m + ".py"))}
        graph, fails = {}, []
        for m, n in present.items():
            with open(os.path.join(ns.root, *ASSETS.split("/"), m + ".py"), "rb") as fh:
                deps = imports_of(fh.read().decode("utf-8")) & set(present)
            graph[m] = sorted(deps - {m})
            for d in graph[m]:
                if present[d] > n:
                    fails.append({"check": "큰 번호로의 import", "from": "MOD%d %s" % (n, m), "to": "MOD%d %s" % (present[d], d)})
        # 순환
        state = {}

        def dfs(u, path):
            state[u] = 1
            for v in graph.get(u, []):
                if state.get(v) == 1:
                    fails.append({"check": "순환", "cycle": path[path.index(v):] + [v] if v in path else [u, v]})
                elif state.get(v) is None:
                    dfs(v, path + [v])
            state[u] = 2
        for m in sorted(graph):
            if state.get(m) is None:
                dfs(m, [m])
    except (rp.GateError, OSError, SyntaxError, UnicodeDecodeError) as e:
        print(json.dumps({"tool": "import_layering", "verdict": "ERROR", "error": "%s: %s" % (type(e).__name__, e)},
                         ensure_ascii=False))
        return 2
    print(json.dumps({"tool": "import_layering", "verdict": "FAIL" if fails else "PASS", "present": present,
                      "graph": graph, "findings": fails}, ensure_ascii=False))
    return 1 if fails else 0


if __name__ == "__main__":
    try:   # 로캘·PYTHONIOENCODING과 무관하게 출력을 UTF-8로(spec card 20260921-gate-output-utf8)
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
