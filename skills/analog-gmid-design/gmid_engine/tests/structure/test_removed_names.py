"""[U17 ①] 폐기 이름 부재 -- 설계 40 v1.6 §3.7-3 '폐기', §11 U17 ① '같은 변경에서 지우는 것'.

대상 이름과 근거:
- `dc_gm_bound`(필드), `previous_gm_id`·`inherited_gm_id`·`canonical_gm_id`(as-built U4 S2p 경로), `gm_grid_max`(곡선 격자 최대 gm 상계)
  -- §3.7-3 "폐기: 옛 문언 'S2p ss gm, 첫 평가만 격자 최대 gm'과 as-built U4 경로(previous_gm_id·inherited_gm_id·canonical_gm_id,
  gm_grid_max, dc_gm_bound 필드)", §11 U17 ① 지우는 것 목록.
- `_power_resolution`(search 의 b_P 재계산) -- §2.4.7 Objectives 행 "search의 재계산(`_power_resolution`)을 지운다", §11 U17 ①.
- `spec_passive_values`(SearchContext 의 수동소자 값 사본) -- §2.4.7 '수동소자 값' 행·SearchContext 칸 배정, §11 U17 ① `sctx.spec_passive_values`.

판정(AST, 엔진 소스 = tests/ 밖 `*.py` 전부, structure_checks.engine_files): 이름이 **코드로** 남아 있으면 위반 --
식별자(Name), 속성 이름(Attribute), def·class 이름, 인자 이름, import 이름·별칭, 키워드 인자 이름, 그리고 이름과 정확히 같은 문자열
상수(필드 이름 `("device", "dc_gm_bound")` 같은 선언). 주석·docstring 안의 언급(경위 설명)은 코드가 아니라 보지 않는다(문자열 상수가
이름과 '정확히 같을' 때만 센다).
검사기가 공허하지 않다는 증거: `test_scanner_rejects_each_form` 이 형식마다 위반 소스 조각을 실제로 잡는지 본다.
"""
from __future__ import annotations

import ast

import pytest

REMOVED = ("dc_gm_bound", "previous_gm_id", "inherited_gm_id", "canonical_gm_id", "gm_grid_max",
           "_power_resolution", "spec_passive_values")


def removed_name_hits(tree, names=REMOVED):
    """-> [(줄, 이름, 형식)] 정렬."""
    names = frozenset(names)
    out = []
    for n in ast.walk(tree):
        found = []
        if isinstance(n, ast.Name):
            found.append((n.id, "name"))
        elif isinstance(n, ast.Attribute):
            found.append((n.attr, "attribute"))
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found.append((n.name, "definition"))
        elif isinstance(n, ast.arg):
            found.append((n.arg, "argument"))
        elif isinstance(n, ast.alias):
            found.append((n.name.rsplit(".", 1)[-1], "import"))
            if n.asname:
                found.append((n.asname, "import_alias"))
        elif isinstance(n, ast.keyword) and n.arg is not None:
            found.append((n.arg, "keyword"))
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            found.append((n.value, "string"))
        for name, form in found:
            if name in names:
                out.append((getattr(n, "lineno", 0), name, form))
    return sorted(out)


def test_removed_names_absent_from_engine(checks, engine_root, report):
    files = checks.engine_files(engine_root)
    hits = []
    for p in files:
        for line, name, form in removed_name_hits(checks.parse(p)):
            hits.append("%s:%d %s (%s)" % (checks.rel(engine_root, p), line, name, form))
    report(len(files), len(hits))
    assert len(files) > 0
    assert not hits, "폐기 이름이 엔진 코드에 남아 있다 %d건:\n%s" % (len(hits), "\n".join(hits))


@pytest.mark.parametrize("src, form", [
    ("x = dc_gm_bound\n", "name"),
    ("y = snap.previous_gm_id\n", "attribute"),
    ("def inherited_gm_id(p):\n    return p\n", "definition"),
    ("def f(canonical_gm_id):\n    return 0\n", "argument"),
    ("from gmid_engine.sizing import gm_grid_max\n", "import"),
    ("import os as _power_resolution\n", "import_alias"),
    ("f(spec_passive_values=0)\n", "keyword"),
    ("W = ((\"device\", \"dc_gm_bound\"),)\n", "string"),
])
def test_scanner_rejects_each_form(src, form):
    hits = removed_name_hits(ast.parse(src))
    assert hits and all(h[2] == form for h in hits), hits


def test_scanner_ignores_docstring_and_comment_mentions():
    src = '"""옛 `dc_gm_bound` 와 previous_gm_id 는 폐기됐다."""\n# gm_grid_max 는 지웠다\nx = "dc_gm"\n'
    assert removed_name_hits(ast.parse(src)) == []
