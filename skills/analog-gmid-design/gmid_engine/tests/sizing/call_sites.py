"""[EO-1 범위 4] 엔진 소스의 호출 자리·금지 이름 훑기 -- AST 로만 읽는다(엔진 import 없이, 이 test 파일들이 쓰는 도구).

`calls_of(name)`: 엔진 소스(`tests/` 밖 `*.py`) 중 이름 `name` 을 호출(`name(...)` 또는 `x.name(...)`)하는 자리를
{(엔진 상대 경로, 가장 바깥 def 이름)} 로 돌려준다. 정의(def) 자체는 호출이 아니다.
`words_in_engine(words)`: 엔진 소스(`tests/` 밖) 텍스트에 단어(식별자 경계)가 나오는 {(상대 경로, 단어)}.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[2]       # tests/sizing/x.py -> tests -> gmid_engine


def engine_sources():
    out = []
    for p in sorted(ENGINE_ROOT.rglob("*.py")):
        rel = p.relative_to(ENGINE_ROOT)
        if rel.parts[0] == "tests" or "__pycache__" in rel.parts or any(s.startswith(".") for s in rel.parts):
            continue
        out.append(p)
    return out


def _callee(node):
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def calls_of(name):
    found = set()
    for p in engine_sources():
        tree = ast.parse(p.read_text(encoding="utf-8"))
        rel = p.relative_to(ENGINE_ROOT).as_posix()
        for top in tree.body:
            holders = [top] if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef)) else []
            if isinstance(top, ast.ClassDef):
                holders = [m for m in top.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            for h in holders:
                for n in ast.walk(h):
                    if isinstance(n, ast.Call) and _callee(n) == name:
                        found.add((rel, h.name))
    return found


def words_in_engine(words):
    found = set()
    pats = {w: re.compile(r"(?<![A-Za-z0-9_])" + re.escape(w) + r"(?![A-Za-z0-9_])") for w in words}
    for p in engine_sources():
        text = p.read_text(encoding="utf-8")
        rel = p.relative_to(ENGINE_ROOT).as_posix()
        for w, pat in pats.items():
            if pat.search(text):
                found.add((rel, w))
    return found


def imported_modules(path):
    """파일이 import 하는 모듈 이름 집합(`import a.b` -> a.b, `from a.b import c` -> a.b)."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            mods.add(n.module)
    return mods
