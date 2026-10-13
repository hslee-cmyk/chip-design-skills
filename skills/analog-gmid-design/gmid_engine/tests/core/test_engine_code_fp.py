"""core/engine_code_fp.py -- 엔진 코드 지문 (design 40 v1.6 §2.4.3 키 (iii), §2.4.12 Q2·U-68).

design 근거(§2.4.3 '키' 행 (iii) 문언): "엔진 코드 지문 = `gmid_engine` 아래 **test가 아닌 모든 패키지**의 `.py` 파일 바이트
sha256(파일 경로 정렬). 블록 입력 버전의 코드 해시는 블록 함수 자신의 코드 객체만 덮으므로 실행 사이 재사용에는 (iii)이 필요하다.
as-built `search_context._code_fp`는 6개 패키지만 덮어 범위가 좁다".
U-68(사용자 결정 원문): 저장소·**모든 worktree** 의 현재 파일로 만들 수 있는 키는 보존 -- 다른 checkout 의 같은 코드가 같은 지문을
내야 이 판정이 성립한다(위치 무관).

판정(피검 함수로 기대값을 만들지 않는다 -- 같은 함수의 두 출력이 같은가/다른가만 본다):
* 덮는 범위: test 가 아닌 모든 패키지의 `.py`(옛 6개 패키지 밖 `authoring`·`layout`·`convergence`·`report`·`pipeline` 과 최상위
  모듈 포함) -- 바이트 하나가 바뀌거나 파일이 늘면 지문이 바뀐다.
* 덮지 않는 범위: `tests/` 아래 파일, `.py` 가 아닌 파일 -- 바뀌어도 지문이 같다.
* 위치 무관: 같은 트리를 다른 폴더에 두어도 같은 지문.
* 기본 대상 = 이 `gmid_engine` 폴더.
red-first `tests/core/test_snapshot_codec.py` 의 '엔진 코드 지문 (iii)' 절을 원본 1:1(규칙 H)에 따라 이 파일로 옮기고 위 범위를 보탰다.
"""
from pathlib import Path

import pytest

from gmid_engine.core.engine_code_fp import engine_code_fp

_ENGINE_DIR = Path(__file__).resolve().parents[2]          # tests/core -> tests -> gmid_engine

_TREE = {
    "__init__.py": "X = 0\n",
    "_module_map.py": "M = 0\n",
    "core/__init__.py": "",
    "core/a.py": "A = 1\n",
    "core/CONTRACT.md": "contract\n",
    "lut/l.py": "L = 1\n",
    "authoring/f.py": "F = 1\n",
    "graph/g.py": "G = 1\n",
    "sizing/s.py": "S = 1\n",
    "metrics/m.py": "M = 1\n",
    "search/q.py": "Q = 1\n",
    "layout/d.py": "D = 1\n",
    "convergence/e.py": "E = 1\n",
    "report/b.py": "B = 1\n",
    "pipeline/c.py": "C = 1\n",
    "tests/__init__.py": "",
    "tests/conftest.py": "T = 0\n",
    "tests/core/test_a.py": "def test_a():\n    pass\n",
}
_NON_TEST_PY = sorted(rel for rel in _TREE if rel.endswith(".py") and not rel.startswith("tests/"))


def _make_tree(root):
    for rel, text in _TREE.items():
        p = root.joinpath(*rel.split("/"))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
    return root


def _code_fp(root):
    return engine_code_fp(str(root))


def test_engine_code_fp_is_a_nonempty_string(tmp_path):
    fp = _code_fp(_make_tree(tmp_path / "gmid_engine"))
    assert isinstance(fp, str) and fp


def test_engine_code_fp_is_deterministic(tmp_path):
    root = _make_tree(tmp_path / "gmid_engine")
    assert _code_fp(root) == _code_fp(root)


def test_engine_code_fp_is_independent_of_checkout_location(tmp_path):
    # U-68: 다른 worktree 의 같은 코드로 같은 키를 만들 수 있어야 보존 판정이 성립한다 -> 위치 무관.
    a = _make_tree(tmp_path / "wt_a" / "gmid_engine")
    b = _make_tree(tmp_path / "wt_b" / "deeper" / "gmid_engine")
    assert _code_fp(a) == _code_fp(b)


@pytest.mark.parametrize("rel", _NON_TEST_PY)
def test_engine_code_fp_changes_when_any_non_test_package_file_changes(tmp_path, rel):
    root = _make_tree(tmp_path / "gmid_engine")
    before = _code_fp(root)
    p = root.joinpath(*rel.split("/"))
    p.write_bytes(p.read_bytes() + b"# edit\n")
    assert _code_fp(root) != before


@pytest.mark.parametrize("pkg", ["report", "pipeline", "core"])
def test_engine_code_fp_changes_when_non_test_file_added(tmp_path, pkg):
    root = _make_tree(tmp_path / "gmid_engine")
    before = _code_fp(root)
    (root / pkg / "new_module.py").write_bytes(b"N = 1\n")
    assert _code_fp(root) != before


def test_engine_code_fp_changes_when_non_test_file_removed(tmp_path):
    root = _make_tree(tmp_path / "gmid_engine")
    before = _code_fp(root)
    (root / "convergence" / "e.py").unlink()
    assert _code_fp(root) != before


@pytest.mark.parametrize("rel", ["tests/core/test_a.py", "tests/conftest.py"])
def test_engine_code_fp_ignores_test_file_changes(tmp_path, rel):
    root = _make_tree(tmp_path / "gmid_engine")
    before = _code_fp(root)
    p = root.joinpath(*rel.split("/"))
    p.write_bytes(p.read_bytes() + b"# edit\n")
    assert _code_fp(root) == before


def test_engine_code_fp_ignores_added_test_file(tmp_path):
    root = _make_tree(tmp_path / "gmid_engine")
    before = _code_fp(root)
    (root / "tests" / "core" / "test_new.py").write_bytes(b"def test_n():\n    pass\n")
    assert _code_fp(root) == before


def test_engine_code_fp_ignores_non_py_files(tmp_path):
    root = _make_tree(tmp_path / "gmid_engine")
    before = _code_fp(root)
    (root / "core" / "CONTRACT.md").write_bytes(b"changed contract\n")
    (root / "core" / "data.json").write_bytes(b"{}")
    assert _code_fp(root) == before


def test_default_root_is_this_engine_folder():
    # 기본 대상 = 이 gmid_engine 폴더(단계 A 가 인자 없이 부른다).
    assert engine_code_fp() == engine_code_fp(str(_ENGINE_DIR))


def test_real_engine_fp_ignores_engine_tests_folder(tmp_path):
    # 실제 엔진 트리에서도 tests/ 는 덮지 않는다: 실제 엔진의 test 밖 .py 만 복사한 트리와 지문이 같다.
    import shutil
    copy = tmp_path / "gmid_engine"
    for src in _ENGINE_DIR.rglob("*.py"):
        rel = src.relative_to(_ENGINE_DIR)
        if rel.parts[0] == "tests" or "__pycache__" in rel.parts or any(part.startswith(".") for part in rel.parts):
            continue
        dst = copy / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    assert engine_code_fp(str(copy)) == engine_code_fp(str(_ENGINE_DIR))
