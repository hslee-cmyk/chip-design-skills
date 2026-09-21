"""interface card 생성 (05-role-separation design §11.1, 계획 N3.12.5, DEC-38).

    $PY interface_card.py <spec card> [--root <저장소 루트>] [--out <파일>]

출력 `docs/02-design/specs/<id>.interface.md`: spec card '관찰 가능한 계약'에 나온 기존 함수의 AST 시그니처 +
docstring 첫 단락, '신규 시그니처' 절(spec card 표 그대로 -- 신규 심볼은 (모듈, 심볼) 쌍 표). 본문 코드는 넣지 않는다.
test-author의 유일한 입력이다(§6.4 소스 열람 거부). red 수집 플러그인이 '신규 시그니처' 표를 읽는다(00-common §8.1).
기존 함수 찾기: '관찰 가능한 계약' 절의 백틱 토큰(`name`, `module.name`, `name(…)`)을 엔진 모듈
(`skills/analog-gmid-design/assets/*.py`, `workspaces/run_harness.py`)의 최상위 def·클래스 메서드와 대조한다.
exit 0 생성 / 1 실패(절 없음·찾은 함수 0개) / 2 입력 오류.
"""
from __future__ import annotations

import ast
import copy
import glob
import os
import re
import sys

import role_paths as rp

ENGINE_GLOBS = ("skills/analog-gmid-design/assets/*.py", "workspaces/run_harness.py")


def _signature(fn):
    f = copy.deepcopy(fn)
    f.body = [ast.Expr(value=ast.Constant(value=Ellipsis))]
    f.decorator_list = []
    text = ast.unparse(f)
    return text.split("\n")[0].rstrip(":").rstrip() if text else fn.name


def _doc_first_para(fn):
    d = ast.get_docstring(fn) or ""
    return d.strip().split("\n\n")[0].strip()


def engine_defs(root):
    """{심볼: [(모듈, 노드, qualname)]} -- 최상위 def와 클래스 메서드."""
    out = {}
    for g in ENGINE_GLOBS:
        for p in sorted(glob.glob(os.path.join(root, *g.split("/")))):
            mod = os.path.splitext(os.path.basename(p))[0]
            with open(p, "rb") as fh:
                tree = ast.parse(fh.read().decode("utf-8"))
            for n in tree.body:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.setdefault(n.name, []).append((mod, n, n.name))
                elif isinstance(n, ast.ClassDef):
                    for m in n.body:
                        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            out.setdefault(m.name, []).append((mod, m, "%s.%s" % (n.name, m.name)))
    return out


def _esc(s):
    return s.replace("|", "\\|")


def build(card_text, root):
    card = rp.parse_spec_card(card_text)
    secs = card["sections"]
    if "관찰 가능한 계약" not in secs or "신규 시그니처" not in secs:
        raise rp.GateError("spec card에 '관찰 가능한 계약'·'신규 시그니처' 절이 없다")
    tokens = re.findall(r"`([A-Za-z_][A-Za-z0-9_.]*)\s*(?:\([^`]*\))?`", secs["관찰 가능한 계약"])
    defs = engine_defs(root)
    rows, blocks, seen = [], [], set()
    for t in tokens:
        parts = t.split(".")
        sym = parts[-1]
        mod_hint = parts[-2] if len(parts) >= 2 else None
        for mod, fn, q in defs.get(sym, []):
            if mod_hint and mod_hint not in (mod, q.split(".")[0]):
                continue
            key = (mod, q)
            if key in seen:
                continue
            seen.add(key)
            sig = _signature(fn)
            rows.append("| `%s` | `%s` | `%s` |" % (mod, q, _esc(sig)))
            doc = _doc_first_para(fn)
            blocks.append("### `%s.%s`\n\n%s\n" % (mod, q, "\n".join("> " + l for l in doc.split("\n")) if doc else "(docstring 없음)"))
    out = ["# interface card: %s" % card["id"], "",
           "생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).", "",
           "## 관찰 가능한 계약", "", "| 모듈 | 심볼 | 시그니처 |", "|---|---|---|"] + rows + [""] + blocks + \
          ["## 신규 시그니처", "", secs["신규 시그니처"].strip(), ""]
    return card["id"], "\n".join(out), len(rows)


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="interface_card.py")
    ap.add_argument("spec_card")
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=None)
    try:
        ns = ap.parse_args(argv)
    except SystemExit:
        return 2
    try:
        root = ns.root or rp.main_worktree_of(os.getcwd())[0]
        with open(ns.spec_card, "rb") as fh:
            cid, text, n = build(fh.read().decode("utf-8"), root)
        out = ns.out or os.path.join(root, "docs", "02-design", "specs", "%s.interface.md" % cid)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    except (rp.GateError, OSError, SyntaxError, UnicodeDecodeError) as e:
        print("[interface_card] 실패: %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return 2
    print("interface card: %s (기존 함수 %d개)" % (out, n))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
