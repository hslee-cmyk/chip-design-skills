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

# 이름 -> 설계가 삭제를 적은 범위(엔진 상대 경로 접두사; None = 엔진 전체). `_power_resolution` 은 설계 §2.4.7·§11 U17 ① 이
# 'search/objectives.py 의 _power_resolution' 으로 범위를 적었으므로 search/ 안에서만 폐기 이름이다(b_P 의 정본은 metrics_dc 로
# 옮겨졌고, 그 파일 안의 `_` helper 이름은 설계가 정하지 않는다 -- 파일 분할 규칙 (B)).
REMOVED_SCOPES = (("dc_gm_bound", None), ("previous_gm_id", None), ("inherited_gm_id", None), ("canonical_gm_id", None),
                  ("gm_grid_max", None), ("_power_resolution", "search/"), ("spec_passive_values", None),
                  # [U17 ①-b] 설계 40 v1.9 §2.4.2 '묶음 객체(S1v, Achievability, StartIntervals)는 필드 묶음으로 풀고 사본을 두지 않는다',
                  # §2.4.7 StartContext·CurveBook '없앤다', §11 U17 ① 지우는 것(StartContext, CurveBook, S1v·Achievability·StartIntervals 묶음 전달).
                  ("S1v", None), ("Achievability", None), ("StartIntervals", None), ("StartContext", None), ("CurveBook", None),
                  # [U17 ①-b] §2.4.6 끝·§2.4.7 SearchContext 칸 배정 `cell_floors`: 1변수 writer 집합(`cell_floor.py` 의 `_ONE_VAR_KEY` 칸)은
                  # S0 수준 필드 `device: dc_self_referential`(§2.4.8) -- search 쪽 사본 키를 지운다.
                  ("_ONE_VAR_KEY", "search/"),
                  # [v1.11.2 O-39 (1)] 설계 40 §2.4.14 (4) 행 '`F_DEVICE`, `ly_device`' 범위 = 엔진 전체(소스·CONTRACT·tests), 같은 행
                  # '`(DEVICE, F_DEVICE)` READS·`projection.column(DEVICE, F_DEVICE)`'도 함께 0. 이 검사는 그중 엔진 소스 코드 범위다.
                  ("F_DEVICE", None), ("ly_device", None))
REMOVED = tuple(n for n, _s in REMOVED_SCOPES)


def removed_names_for(rel_path):
    """엔진 상대 경로(`/` 구분)에 적용되는 폐기 이름 집합."""
    rel_path = rel_path.replace("\\", "/")
    return frozenset(n for n, scope in REMOVED_SCOPES if scope is None or rel_path.startswith(scope))


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
        rel = checks.rel(engine_root, p)
        for line, name, form in removed_name_hits(checks.parse(p), removed_names_for(rel)):
            hits.append("%s:%d %s (%s)" % (rel, line, name, form))
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


def test_scope_of_power_resolution_is_search_only():
    """§2.4.7·§11 U17 ①: `_power_resolution` 삭제 범위는 search/objectives.py -- search/ 밖(metrics 의 b_P 정본 파일)에는 적용하지
    않고, 범위 없는 이름(dc_gm_bound 등)은 모든 파일에 적용한다."""
    assert "_power_resolution" in removed_names_for("search/objectives.py")
    assert "_power_resolution" in removed_names_for("search\\kernel.py")
    assert "_power_resolution" not in removed_names_for("metrics/dc_metrics.py")
    assert removed_names_for("metrics/dc_metrics.py") == frozenset(n for n, scope in REMOVED_SCOPES if scope is None)
    assert "_ONE_VAR_KEY" in removed_names_for("search/cell_floor.py") and "_ONE_VAR_KEY" not in removed_names_for("sizing/writer_plan.py")


def test_scanner_ignores_docstring_and_comment_mentions():
    src = '"""옛 `dc_gm_bound` 와 previous_gm_id 는 폐기됐다."""\n# gm_grid_max 는 지웠다\nx = "dc_gm"\n'
    assert removed_name_hits(ast.parse(src)) == []


def local_inputs_rebuild_hits(tree):
    """-> [(줄, 형식)]: `local_inputs` 를 **부르거나 import** 하는 곳(필드 이름 문자열 `"local_inputs"` 읽기는 해당 없음)."""
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
            if name == "local_inputs":
                out.append((n.lineno, "call"))
        elif isinstance(n, ast.alias) and (n.asname or n.name).rsplit(".", 1)[-1] == "local_inputs":
            out.append((getattr(n, "lineno", 0), "import"))
    return sorted(out)


def test_local_inputs_not_rebuilt_in_search(checks, engine_root, report):
    """[U17 ①-b] 설계 40 v1.9 §2.4.8 '블록 국소 모델 입력 LocalInputs(achievability.py:77-113, iv_context.py:63-69 에서 두 번)' 행:
    `graph/ach: local_inputs` 의 writer 는 achievability(GB4) 하나이고 '출발 구간이 같은 필드를 읽는다'. 그래서 search 패키지(출발 구간·층 0)는
    `local_inputs` 를 다시 만들지(호출·import) 않는다 -- 필드를 읽는다."""
    files = [p for p in checks.engine_files(engine_root) if checks.rel(engine_root, p).replace("\\", "/").startswith("search/")]
    hits = ["%s:%d (%s)" % (checks.rel(engine_root, p), line, form)
            for p in files for line, form in local_inputs_rebuild_hits(checks.parse(p))]
    report(len(files), len(hits))
    assert files
    assert not hits, "search 가 LocalInputs 를 다시 만든다 %d건:\n%s" % (len(hits), "\n".join(hits))


@pytest.mark.parametrize("src, n", [("x = local_inputs(a, b)\n", 1), ("x = metrics.local_inputs(a)\n", 1),
                                    ("from gmid_engine.metrics import local_inputs\n", 1),
                                    ("x = s.value('graph', 'ach', 'local_inputs')\n", 0)])
def test_local_inputs_scanner(src, n):
    assert len(local_inputs_rebuild_hits(ast.parse(src))) == n


# ---------------------------------------------------------------- [IT-1 T-G] 옛 정지 사유 이름 잔재 0 (DEC-106·O-210 RR-6)
# oracle (독립): 비test 엔진 소스(`*.py`)와 CONTRACT 문서 글자 그대로 0 -- 이름이 지워졌는지 문자열로 본다(주석·docstring 포함: A4 잔재 grep 과 같은 뜻).
IT1_REMOVED_TEXT = ("input_port_multiple_roots", "BRANCH_INPUT_MULTIPLE_ROOTS", "gvgs_self_edge", "BRANCH_GVGS_SELF_EDGE",
                    "off_device_on_signal_path")


def test_it1_removed_stop_names_absent_from_engine_and_contracts(checks, engine_root, report):
    files = list(checks.engine_files(engine_root))
    docs = sorted(p for p in engine_root.rglob("CONTRACT*.md") if "tests" not in p.relative_to(engine_root).parts)
    assert docs                                                                                  # 전제: 계약 문서가 있다(공허한 검사 아님)
    hits = []
    for p in list(files) + docs:
        text = p.read_text(encoding="utf-8")
        for name in IT1_REMOVED_TEXT:
            if name in text:
                hits.append("%s %s" % (p.relative_to(engine_root).as_posix(), name))
    report(len(files) + len(docs), len(hits))
    assert hits == []
