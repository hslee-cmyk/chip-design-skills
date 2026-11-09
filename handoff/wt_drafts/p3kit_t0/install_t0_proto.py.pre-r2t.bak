"""T0 시제품 설치(측정 전용 -- 역할 산출물 아님, test-author·auditor 열람 금지(작성자 != 검증자)).

    C:/Python314/python.exe -B install_t0_proto.py <복제본 루트>

spec card 20260930-p3-tests-location-free 계약 1~4를 격리 복제본의 계약 test 세 파일과 새 도우미에 적용한다.
계약 10(test_b26_rail_accessor.py)은 그 파일이 B26-1 병합 전이라 없으므로 이 시제품에 없다.
앵커가 하나라도 없으면 exit 1, 아무것도 쓰지 않는다.
"""
import os
import sys

ROOT = sys.argv[1]
C = os.path.join(ROOT, "skills", "analog-gmid-design", "assets", "tests", "contracts")


def rd(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return fh.read().replace("\r\n", "\n")


def sub(text, old, new, label):
    if text.count(old) != 1:
        raise SystemExit("앵커 %s: %d개(1개여야 한다)" % (label, text.count(old)))
    return text.replace(old, new)


HELPER = '''"""계약 test 공용 도우미 -- 정의 위치 해석 규칙 R-DEF(design 30-module-split §7.1).

엔진 소스 = `A/*.py`(하위 디렉터리 제외) + `<저장소 루트>/workspaces/run_harness.py`. 이름 n의 정의 파일 = 엔진 소스 중
최상위에서 n을 def·class·대입(주석 대입 포함)으로 바인딩하는 파일(메서드는 `Class.method`). import로 받은 이름은 정의가 아니다.
파일 이름이 `_`로 시작해 pytest가 수집하지 않는다.
"""
import ast
import pathlib

_ASSETS_DIR = pathlib.Path(__file__).resolve().parents[2]
_REPO_ROOT = _ASSETS_DIR.parents[2]
_RUN_HARNESS = _REPO_ROOT / "workspaces" / "run_harness.py"
_TREES = {}


def engine_source_files() -> list:
    return sorted(_ASSETS_DIR.glob("*.py")) + [_RUN_HARNESS]


def _tree(path: pathlib.Path) -> ast.Module:
    key = str(path)
    if key not in _TREES:
        _TREES[key] = ast.parse(path.read_text(encoding="utf-8"))
    return _TREES[key]


def _defined_names(tree: ast.Module) -> set:
    out = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.add(node.name)
        elif isinstance(node, ast.ClassDef):
            out.add(node.name)
            out |= {node.name + "." + m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
        elif isinstance(node, ast.Assign):
            out |= {x.id for t in node.targets for x in ast.walk(t) if isinstance(x, ast.Name)}
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out.add(node.target.id)
    return out


def _from_imported_names(tree: ast.Module) -> set:
    return {a.asname or a.name for node in tree.body if isinstance(node, ast.ImportFrom) for a in node.names}


def defining_files(name: str) -> list:
    return [p for p in engine_source_files() if name in _defined_names(_tree(p))]


def binding_files(name: str) -> list:
    return [p for p in engine_source_files()
            if name in _defined_names(_tree(p)) or name in _from_imported_names(_tree(p))]
'''

out = {os.path.join(C, "_engine_defs.py"): HELPER}

# ---------------------------------------------------------------- test_ic5.py (계약 2)
p = os.path.join(C, "test_ic5.py")
t = rd(p)
t = sub(t, "# oracle (d) design §5.6 영역 표(현존 21개). 키 = (파일 이름, 함수 이름), 값 = 영역 값 집합.",
        "# oracle (d) design §5.6 영역 표(현존 21개). 키 = 함수 이름(정의 위치는 대상 수집 결과로 찾는다 -- R-DEF), 값 = 영역 값 집합.", "ic5 comment")
import re as _re
block_start = t.index("_DOMAIN_TABLE = {")
block_end = t.index("\n}\n", block_start)
block = t[block_start:block_end]
new_block = _re.sub(r'\("[a-z_]+\.py", ("[A-Za-z_0-9]+")\)', r"\1", block)
if new_block.count('.py"') != 0 or block.count('.py"') != 21:
    raise SystemExit("ic5 표 키 치환 실패")
t = t[:block_start] + new_block + t[block_end:]
t = sub(t, """    # 표의 21개가 대상 집합 안에 있어야 (3)이 공허하지 않다.
    found_keys = {(f, n) for f, n, _, _ in targets}
    missing = sorted(set(_DOMAIN_TABLE) - found_keys)
    assert not missing, f"design §5.6 영역 표의 함수가 대상에 없다({len(missing)}개): {missing}"
""", """    # 표의 21개가 대상 집합 안에 정확히 하나씩 있어야 (3)이 공허하지 않고 모호하지 않다(위치는 R-DEF -- 파일 이름을 가정하지 않는다).
    hits = {name: [(f, lineno) for f, n, lineno, _ in targets if n == name] for name in _DOMAIN_TABLE}
    missing = sorted(name for name, h in hits.items() if not h)
    assert not missing, f"design §5.6 영역 표의 함수가 대상에 없다({len(missing)}개): {missing}"
    ambiguous = {name: [f"{f}:{ln}" for f, ln in h] for name, h in hits.items() if len(h) > 1}
    assert not ambiguous, f"design §5.6 영역 표의 함수가 대상에 둘 이상 있다(모호): {ambiguous}"
""", "ic5 missing")
t = sub(t, """        expected = _DOMAIN_TABLE.get((f, n))""", """        expected = _DOMAIN_TABLE.get(n)""", "ic5 get")
out[p] = t

# ---------------------------------------------------------------- test_dup_w_calc.py (계약 3)
p = os.path.join(C, "test_dup_w_calc.py")
t = rd(p)
t = sub(t, """    path = _ASSETS_DIR / "sizing_recipe.py"
    assert path.exists(), path
    assert_function_calls(_read(path), _CANON_FUNC, _NEW_FUNC, _rel(path))
""", """    files = defining_files(_CANON_FUNC)
    assert len(files) == 1, f"{_CANON_FUNC} 정의 파일이 정확히 하나가 아니다(R-DEF): {[_rel(x) for x in files]}"
    path = files[0]
    assert_function_calls(_read(path), _CANON_FUNC, _NEW_FUNC, _rel(path))
""", "dup test")
t = sub(t, "import pytest\n", "import pytest\nfrom _engine_defs import defining_files\n", "dup import")
out[p] = t

# ---------------------------------------------------------------- test_ts6_dead_probes.py (계약 4)
p = os.path.join(C, "test_ts6_dead_probes.py")
t = rd(p)
t = sub(t, """_SIZING_RECIPE = _ASSETS_DIR / "sizing_recipe.py"\n""", "", "ts6 const")
t = sub(t, """    source = _SIZING_RECIPE.read_text(encoding="utf-8")
    assert_source_binds_no_symbol(source, _MISSING_SYMBOL, _SIZING_RECIPE.name)
""", """    files = engine_source_files()
    assert files, "엔진 소스 파일이 없다"
    for path in files:
        assert_source_binds_no_symbol(path.read_text(encoding="utf-8"), _MISSING_SYMBOL, path.name)
""", "ts6 binds")
t = sub(t, """    source = _SIZING_RECIPE.read_text(encoding="utf-8")
    callers = assert_symbol_has_operational_caller(source, _AUDIT_FUNC, _SIZING_RECIPE.name)
""", """    callers = set()
    for path in engine_source_files():
        callers |= _operational_callers(path.read_text(encoding="utf-8"), _AUDIT_FUNC)
    assert callers, f"엔진 소스 어디에도 {_AUDIT_FUNC} 을 호출하는 운영 함수가 없다"
""", "ts6 caller")
t = sub(t, "import pytest\n", "import pytest\nfrom _engine_defs import engine_source_files\n", "ts6 import")
out[p] = t

for path, text in out.items():
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
print("installed", len(out))
