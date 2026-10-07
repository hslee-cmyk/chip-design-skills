"""추출 도구 `tools/migrate/extract_selftest.py`의 test (변경 20260922-ts1-extract-tool, Phase 1 C1, red-green).

정본 명세: design `gain-budget-gmid-sizing.10-test-separation` v1.2 §5.1(섹션 경계·범주)·§5.2(명령·출력·exit code)·
§6.1 C1·§8 F1. 도구는 명령행 도구라 하위 프로세스로만 부른다(계약은 CLI -- interface card).

oracle: 전부 (a) 구성으로 정답이 정해진 합성 입력. 이 파일이 `tmp_path`에 쓰는 합성 모듈의 문장 하나하나가 기대값을
정한다 -- 기대값은 design 문장을 합성 입력에 손으로 적용한 것이고, 피검 도구의 출력에서 가져온 것은 없다.
실제 엔진 모듈에 대한 동등성은 C2(equivalence)의 몫이다.

red: 도구가 없는 base에서는 모든 test가 `_run`의 도구 존재 단언에서 실패한다(수집 오류가 아니라 test 실패).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

# 저장소 루트 = 이 파일(<root>/skills/analog-gmid-design/assets/tests/tooling/)에서 다섯 단계 위.
_REPO_ROOT = Path(__file__).resolve().parents[5]
_TOOL = _REPO_ROOT / "tools" / "migrate" / "extract_selftest.py"

# design §5.2-5 머리글 고정 텍스트의 `_ASSETS_DIR` 정의 줄(문서 문장 그대로).
_ASSETS_DIR_LINE = (
    '_ASSETS_DIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else '
    'os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))'
)
_MAIN_LINE = 'if __name__ == "__main__":'


def _env() -> dict:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """도구를 하위 프로세스로 부른다. 도구가 없으면(base) 여기서 실패한다 -- red의 원인을 test 안에서 드러낸다."""
    assert _TOOL.is_file(), f"추출 도구가 없다: {_TOOL}"
    return subprocess.run(
        [sys.executable, "-B", str(_TOOL), *args],
        cwd=str(cwd) if cwd else None,
        env=_env(),
        capture_output=True,
    )


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def _git_blob_id(data: bytes) -> str:
    # git blob id의 정의(`blob <len>\0<bytes>`의 sha1) -- 도구와 무관한 독립 계산.
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _line_of(text: str, needle: str) -> int:
    """합성 입력에서 `needle`이 든 유일한 줄의 1-기준 번호(구성으로 정해지는 값)."""
    hits = [i for i, line in enumerate(text.split("\n"), start=1) if needle in line]
    assert len(hits) == 1, (needle, hits)
    return hits[0]


# ---------------------------------------------------------------------------
# extract 합성 모듈
# ---------------------------------------------------------------------------
# 모듈 최상위에서 묶이는 이름: json(import), _os(import 별칭), math(import, 블록에서 안 읽음), _z(try 안 import),
# SCALE(대입), OFFSET(if 안 대입), double(def), Box(class), counter(대입).
_EXTRACT_TOP = '''"""합성 모듈 -- extract test용."""
import json
import os as _os
import math

try:
    import zlib as _z
except ImportError:
    _z = None

SCALE = 3

if True:
    OFFSET = 1


def double(x):
    return x * 2


class Box:
    def __init__(self, v):
        self.v = v


counter = 10


'''

# 블록: 주석(한글 포함)·빈 줄·공백만 있는 줄·들여쓰기가 다른 주석·끝 공백 주석·여러 줄 문장이 있다.
_EXTRACT_BLOCK = (
    'if __name__ == "__main__":\n'
    '    # 합성 블록: 주석은 그대로 옮겨져야 한다\n'
    '    here = _os.path.dirname(_os.path.abspath(__file__))\n'
    '    print("=== synthetic ===")\n'
    '\n'
    '    b = Box(double(SCALE))\n'
    '        # 들여쓰기가 다른 주석\n'
    '    print("  [box]", b.v)\n'
    '    assert b.v == 6\n'
    '    \n'
    '    def helper():\n'
    '        return json.dumps({"k": OFFSET})\n'
    '\n'
    '    print(helper())\n'
    '    # trailing spaces   \n'
    '    print(counter)\n'
    '    counter = 99\n'
    '    print(counter)\n'
    '    total = (SCALE +\n'
    '             double(1))\n'
    '    for i in range(2):\n'
    '        print("loop", i, total)\n'
    '    try:\n'
    '        int("x")\n'
    '    except ValueError as err:\n'
    '        print("caught", type(err).__name__)\n'
    '    print(_z is not None)\n'
    '    print(here)\n'
)

_EXTRACT_SOURCE = _EXTRACT_TOP + _EXTRACT_BLOCK

# design §5.2-3으로 손으로 정한 import 이름:
#   블록에서 읽히고 블록에서 저장되지 않는 비내장 이름 중 모듈 최상위에서 묶이는 것
#     = _os, Box, double, SCALE, json(중첩 함수 안), OFFSET(중첩 함수 안, if 안 최상위 대입), _z(try 안 import)
#   + 블록에서 저장도 되지만 첫 저장(`counter = 99`) 전 줄에서 읽히는 최상위 이름 = counter
#   제외: here·b·helper·total·i·err(블록 안에서만 저장, 첫 저장 전 읽기 없음), math(읽히지 않음),
#         print·int·range·type·ValueError(내장), __name__·__file__(모듈 최상위에서 묶이지 않음).
# 정렬: Python 문자열 정렬(sorted)의 정의 그대로 -- 대문자 < '_' < 소문자.
_EXPECTED_IMPORTS = ["Box", "OFFSET", "SCALE", "_os", "_z", "counter", "double", "json"]

# design §5.2-4: 유일한 치환은 `<X>.path.dirname(<X>.path.abspath(__file__))` 원문 조각 -> `_ASSETS_DIR`.
_EXPECTED_BODY = _EXTRACT_BLOCK.replace("_os.path.dirname(_os.path.abspath(__file__))", "_ASSETS_DIR")


def _do_extract(tmp_path: Path) -> dict:
    """도구 호출은 test 본문 안에서 한다(fixture setup 오류가 아니라 test 실패로 red가 드러나게)."""
    src = _write(tmp_path / "assets" / "synthmod.py", _EXTRACT_SOURCE)
    out = tmp_path / "out" / "selftest_synthmod.py"
    out.parent.mkdir(parents=True)
    proc = _run("extract", "--source", str(src), "--module", "synthmod", "--out", str(out))
    return {"src": src, "out": out, "proc": proc, "tmp": tmp_path}


def _header_and_body(out_text: str) -> tuple[list[str], str]:
    idx = out_text.index(_MAIN_LINE + "\n")
    return out_text[:idx].split("\n"), out_text[idx:]


def test_extract_exit0_and_writes_file(tmp_path: Path) -> None:
    extracted = _do_extract(tmp_path)
    # oracle (a): 블록이 정확히 하나이고 지원 구성뿐인 합성 입력 -> design §5.2-6 'exit 0'.
    proc = extracted["proc"]
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert extracted["out"].is_file()


def test_extract_body_is_block_verbatim_with_single_substitution(tmp_path: Path) -> None:
    extracted = _do_extract(tmp_path)
    # oracle (a): 기대 본문 = 합성 블록 원문에서 `__file__` 꼴 조각 하나만 `_ASSETS_DIR`로 바꾼 것(design §5.2-4).
    assert extracted["proc"].returncode == 0
    out_text = extracted["out"].read_bytes().decode("utf-8")
    _, body = _header_and_body(out_text)
    assert body.rstrip("\n") == _EXPECTED_BODY.rstrip("\n")
    assert "__file__" not in body


def test_extract_header_fixed_lines_in_order(tmp_path: Path) -> None:
    extracted = _do_extract(tmp_path)
    # oracle (a)+(design 문장): 머리글 고정 텍스트 순서 = 주석, import os, import sys, _ASSETS_DIR 정의,
    # sys.path.insert(0, _ASSETS_DIR), import 줄(design §5.2-5). 주석에는 원본 경로·원본 blob id가 있다.
    assert extracted["proc"].returncode == 0
    raw = extracted["out"].read_bytes()
    header, _ = _header_and_body(raw.decode("utf-8"))
    fixed = ["import os", "import sys", _ASSETS_DIR_LINE, "sys.path.insert(0, _ASSETS_DIR)"]
    positions = [header.index(line) for line in fixed]
    assert positions == sorted(positions)
    import_lines = [line for line in header if line.startswith("from synthmod import")]
    assert len(import_lines) == 1
    assert header.index(import_lines[0]) > positions[-1]
    # 고정 줄·import 줄 밖의 머리글 줄은 주석이거나 빈 줄이다.
    others = [line for line in header if line not in fixed and line not in import_lines]
    assert all(line == "" or line.lstrip().startswith("#") for line in others), others
    comments = "\n".join(line for line in others if line.lstrip().startswith("#"))
    # 원본 blob id = git blob 정의로 원본 바이트에서 독립 계산.
    assert _git_blob_id(extracted["src"].read_bytes()) in comments
    assert "synthmod.py" in comments
    assert "extract_selftest" in comments


def test_extract_import_line_names(tmp_path: Path) -> None:
    extracted = _do_extract(tmp_path)
    # oracle (a): 손으로 정한 _EXPECTED_IMPORTS(design §5.2-3을 합성 입력에 적용, 위 주석), 한 줄·괄호·정렬.
    assert extracted["proc"].returncode == 0
    header, _ = _header_and_body(extracted["out"].read_bytes().decode("utf-8"))
    import_lines = [line for line in header if line.startswith("from synthmod import")]
    assert len(import_lines) == 1
    m = re.fullmatch(r"from synthmod import \((.*)\)", import_lines[0])
    assert m is not None, import_lines[0]
    names = [n.strip() for n in m.group(1).split(",") if n.strip()]
    assert names == _EXPECTED_IMPORTS
    # 블록 안에서만 저장되는 이름은 가져오지 않는다 / 첫 저장 전에 읽히는 최상위 이름(counter)은 가져온다.
    for stored_only in ("here", "b", "helper", "total", "i", "err", "math", "__name__", "__file__"):
        assert stored_only not in names
    assert "counter" in names


def test_extract_encoding_utf8_no_bom_lf(tmp_path: Path) -> None:
    extracted = _do_extract(tmp_path)
    # oracle (a)+(design §5.2-6): UTF-8(BOM 없음), 줄 끝 LF. 합성 블록에 한글 주석이 있어 UTF-8 인코딩이 드러난다.
    assert extracted["proc"].returncode == 0
    raw = extracted["out"].read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw
    assert raw.endswith(b"\n")
    assert "# 합성 블록: 주석은 그대로 옮겨져야 한다".encode("utf-8") in raw


def test_extract_deterministic_bytes(tmp_path: Path) -> None:
    # oracle (a)+(design §5.2-6 결정론): 같은 입력 두 번 -> 바이트 동일.
    src = _write(tmp_path / "assets" / "synthmod.py", _EXTRACT_SOURCE)
    out1 = tmp_path / "o1" / "selftest_synthmod.py"
    out2 = tmp_path / "o2" / "selftest_synthmod.py"
    out1.parent.mkdir()
    out2.parent.mkdir()
    p1 = _run("extract", "--source", str(src), "--module", "synthmod", "--out", str(out1))
    p2 = _run("extract", "--source", str(src), "--module", "synthmod", "--out", str(out2))
    assert p1.returncode == 0 and p2.returncode == 0
    assert out1.read_bytes() == out2.read_bytes()


def test_extract_runs_and_matches_original_stdout(tmp_path: Path) -> None:
    extracted = _do_extract(tmp_path)
    # oracle (a): 원본 모듈을 직접 실행한 stdout(합성 블록의 실제 동작)이 기대값이다 -- 이관본을
    # `[python, 이관본, <원본 디렉터리>]`로 돌린 stdout이 바이트로 같아야 한다(design §6.1 C1 (2), §7 E1의 축소판).
    # 블록이 `here`(= 원본 디렉터리 절대 경로)를 출력하므로 _ASSETS_DIR 치환과 sys.path.insert도 함께 판정된다.
    assert extracted["proc"].returncode == 0
    assets = extracted["src"].parent
    orig = subprocess.run([sys.executable, "-B", str(extracted["src"])], cwd=str(assets),
                          env=_env(), capture_output=True)
    assert orig.returncode == 0, orig.stderr.decode("utf-8", "replace")
    moved = subprocess.run([sys.executable, "-B", str(extracted["out"]), str(assets)], cwd=str(assets),
                           env=_env(), capture_output=True)
    assert moved.returncode == 0, moved.stderr.decode("utf-8", "replace")
    assert moved.stdout == orig.stdout
    # 원본 블록이 실제로 돌았다(빈 stdout끼리 같은 것이 아니다): 합성 블록이 출력하는 줄로 확인.
    assert b"=== synthetic ===" in orig.stdout
    assert b"caught ValueError" in orig.stdout


# ---------------------------------------------------------------------------
# extract 거부 (design §5.2-1·2·3·5, §8 F1: exit 2·3·4, 출력 파일 없음)
# ---------------------------------------------------------------------------
_OK_BLOCK = 'if __name__ == "__main__":\n    print("x")\n'

_EXIT2_SOURCES = {
    # 블록 0개
    "no_block": "import os\n\nX = 1\n",
    # 블록 2개(작은따옴표 꼴도 블록 -- design §5.1 '작은따옴표를 큰따옴표로')
    "two_blocks": _OK_BLOCK + "\nif __name__ == '__main__':\n    print(\"y\")\n",
    # 파싱 실패
    "syntax_error": "def broken(:\n    pass\n" + _OK_BLOCK,
}


@pytest.mark.parametrize("case", sorted(_EXIT2_SOURCES))
def test_extract_rejects_input_errors_exit2(tmp_path: Path, case: str) -> None:
    # oracle (a): 구성으로 블록 수 0·2·파싱 불가인 합성 입력 -> design §5.2-1·exit code '2 입력 오류'.
    src = _write(tmp_path / "m.py", _EXIT2_SOURCES[case])
    out = tmp_path / "out.py"
    proc = _run("extract", "--source", str(src), "--module", "m", "--out", str(out))
    assert proc.returncode == 2
    assert not out.exists()


def test_extract_rejects_missing_source_exit2(tmp_path: Path) -> None:
    # oracle (a): 존재하지 않는 파일 -> design exit code '2 입력 오류(파일 없음)'.
    out = tmp_path / "out.py"
    proc = _run("extract", "--source", str(tmp_path / "nope.py"), "--module", "nope", "--out", str(out))
    assert proc.returncode == 2
    assert not out.exists()


def test_extract_rejects_unresolved_name_exit3(tmp_path: Path) -> None:
    # oracle (a): 블록이 어디서도 묶이지 않는 이름을 읽는 합성 입력 -> design §5.2-3 '목록을 출력하고 exit 3'.
    text = "X = 1\n\nif __name__ == \"__main__\":\n    print(X, undefined_name_qzx)\n"
    src = _write(tmp_path / "m.py", text)
    out = tmp_path / "out.py"
    proc = _run("extract", "--source", str(src), "--module", "m", "--out", str(out))
    assert proc.returncode == 3
    assert b"undefined_name_qzx" in proc.stdout + proc.stderr
    assert not out.exists()


_EXIT4_BLOCK_LINES = {
    # `__file__`이 든 식이 `<X>.path.dirname(<X>.path.abspath(__file__))` 꼴이 아닌 것(design §5.2-2)
    "file_dirname_only": "d = os.path.dirname(__file__)",
    "file_abspath_only": "d = os.path.abspath(__file__)",
    "file_realpath": "d = os.path.dirname(os.path.realpath(__file__))",
    "file_open": "d = open(__file__).read()",
    # 이름 해석을 보장할 수 없는 호출(design §5.2-2)
    "globals_call": "d = globals()",
    "locals_call": "d = locals()",
    "eval_call": 'd = eval("1")',
    "exec_call": 'exec("d = 1")',
    "dunder_import_call": 'd = __import__("json")',
    # 원본 블록이 이미 `_ASSETS_DIR`을 쓴다(design §5.2-5)
    "uses_assets_dir": '_ASSETS_DIR = "somewhere"',
}


@pytest.mark.parametrize("case", sorted(_EXIT4_BLOCK_LINES))
def test_extract_rejects_unsupported_constructs_exit4(tmp_path: Path, case: str) -> None:
    # oracle (a): 지원 밖 구성 한 줄만 넣은 합성 블록 -> design exit code '4 지원하지 않는 구성'.
    text = ("import os\n\nif __name__ == \"__main__\":\n    print(\"start\")\n    "
            + _EXIT4_BLOCK_LINES[case] + "\n")
    src = _write(tmp_path / "m.py", text)
    out = tmp_path / "out.py"
    proc = _run("extract", "--source", str(src), "--module", "m", "--out", str(out))
    assert proc.returncode == 4
    assert not out.exists()


# ---------------------------------------------------------------------------
# sections (design §5.1, §5.2 `sections`)
# ---------------------------------------------------------------------------
_SECTIONS_SOURCE = (
    'if __name__ == "__main__":\n'
    '    import json as _j\n'                       # S0 머리(P): _j 저장
    '    data = [1, 2, 3]\n'                        # S0: data 저장
    '    print("# Part one")\n'                     # 대 표지 -> S1 시작
    '    print("=== Test 1: sums ===")\n'           # 연속 대 표지 -> S1에 합침
    '    total = sum(data)\n'                       # S1: data 읽기(S0), total 저장
    '    assert total == 6\n'                       # S1: Assert -> A
    '    print("  [sub] check B")\n'                # 소 표지 -> S2 시작
    '    print("  [PASS] not a marker")\n'          # 정규식에 맞아 표지 아님, PASS 토큰 1
    '    print(f"  total={total} PASS")\n'          # total 읽기(S1), f-string 상수 조각 PASS 토큰 1 -> B
    '    print("  [ OK ] also not a marker")\n'     # `\s*OK` -- 표지 아님, 토큰 0
    '    print("  [불가] also not a marker")\n'     # 불가 -- 표지 아님, 토큰 0
    '    print("=== Info ===")\n'                  # 대 표지 -> S3
    '    print("static text only")\n'               # S3: 정적 문자열 print뿐 -> D
    '    print("  [info] C section")\n'             # 소 표지 -> S4
    '    y = _j.dumps(data)\n'                      # S4: _j·data 읽기(S0), 판정 없음 -> C
    '    print("  [raise] A by raise")\n'           # 소 표지 -> S5
    '    if y != "[1, 2, 3]":\n'
    '        raise AssertionError("bad")\n'         # S5: raise AssertionError -> A, y 읽기(S4)
)

# design §5.1을 위 합성 블록에 손으로 적용한 기대(주석의 줄별 판정).
_EXPECTED_SECTIONS = [
    # (index, kind, category, 시작 줄의 표지 텍스트 또는 None, asserts, raise_assertion>0, verdict_tokens, deps)
    (0, "prelude", "P", None, 0, False, 0, set()),
    (1, "major", "A", 'print("# Part one")', 1, False, 0, {("data", 0)}),
    (2, "sub", "B", 'print("  [sub] check B")', 0, False, 2, {("total", 1)}),
    (3, "major", "D", 'print("=== Info ===")', 0, False, 0, set()),
    (4, "sub", "C", 'print("  [info] C section")', 0, False, 0, {("_j", 0), ("data", 0)}),
    (5, "sub", "A", 'print("  [raise] A by raise")', 0, True, 0, {("y", 4)}),
]
# provides_to = deps의 역(섹션 i가 저장한 이름을 읽는 뒤 섹션 목록).
_EXPECTED_PROVIDES = {0: {1, 4}, 1: {2}, 2: set(), 3: set(), 4: {5}, 5: set()}


def _sections_list(payload):
    # design §5.2는 '섹션 목록 JSON'이라 한다 -- 최상위가 목록이거나 `sections` 키의 목록.
    lst = payload["sections"] if isinstance(payload, dict) else payload
    assert isinstance(lst, list)
    return lst


def _do_sections(tmp_path: Path) -> dict:
    src = _write(tmp_path / "secmod.py", _SECTIONS_SOURCE)
    out = tmp_path / "sections.json"
    proc = _run("sections", "--source", str(src), "--out", str(out))
    return {"proc": proc, "out": out}


def test_sections_exit0_and_count(tmp_path: Path) -> None:
    sections_result = _do_sections(tmp_path)
    # oracle (a): 표지 규칙(design §5.1)으로 합성 블록은 섹션 6개 -- 머리 1, 대 표지 2(연속 대 표지 둘은 하나로), 소 표지 3.
    proc = sections_result["proc"]
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    secs = _sections_list(json.loads(sections_result["out"].read_bytes().decode("utf-8")))
    assert [s["index"] for s in secs] == [e[0] for e in _EXPECTED_SECTIONS]


def test_sections_kind_and_category(tmp_path: Path) -> None:
    sections_result = _do_sections(tmp_path)
    # oracle (a): kind·category = design §5.1 규칙(대·소 표지, 연속 대 표지 병합, `  [PASS`·`  [ OK`·`  [불가`는 표지 아님,
    # 범주 P/D/A/B/C 위에서부터 처음 맞는 것)을 합성 블록에 적용한 손 기대.
    assert sections_result["proc"].returncode == 0
    secs = _sections_list(json.loads(sections_result["out"].read_bytes().decode("utf-8")))
    assert [s["kind"] for s in secs] == [e[1] for e in _EXPECTED_SECTIONS]
    assert [s["category"] for s in secs] == [e[2] for e in _EXPECTED_SECTIONS]
    assert {s["category"] for s in secs} == {"P", "D", "A", "B", "C"}


def test_sections_start_lines(tmp_path: Path) -> None:
    sections_result = _do_sections(tmp_path)
    # oracle (a): 표지 섹션의 시작 줄 = 합성 입력에서 그 표지 문장의 줄 번호(1-기준, 구성으로 정해짐).
    # 연속 대 표지 병합이면 S1은 첫 대 표지 줄에서 시작한다.
    assert sections_result["proc"].returncode == 0
    secs = _sections_list(json.loads(sections_result["out"].read_bytes().decode("utf-8")))
    for (idx, _k, _c, marker, *_rest), sec in zip(_EXPECTED_SECTIONS[1:], secs[1:]):
        assert sec["start"] == _line_of(_SECTIONS_SOURCE, marker), (idx, sec)
    ends = [s["end"] for s in secs]
    starts = [s["start"] for s in secs]
    assert all(ends[i] < starts[i + 1] for i in range(len(secs) - 1))
    assert ends[-1] == _line_of(_SECTIONS_SOURCE, 'raise AssertionError("bad")')


def test_sections_verdict_counts(tmp_path: Path) -> None:
    sections_result = _do_sections(tmp_path)
    # oracle (a): asserts = 섹션의 Assert 수, raise_assertion = `raise AssertionError` 유무,
    # verdict_tokens = design §7 T를 합성 print 인자에 손으로 적용(S2: "[PASS]" 1 + f-string 조각 " PASS" 1 = 2).
    assert sections_result["proc"].returncode == 0
    secs = _sections_list(json.loads(sections_result["out"].read_bytes().decode("utf-8")))
    assert [s["asserts"] for s in secs] == [e[4] for e in _EXPECTED_SECTIONS]
    assert [bool(s["raise_assertion"]) for s in secs] == [e[5] for e in _EXPECTED_SECTIONS]
    assert [s["verdict_tokens"] for s in secs] == [e[6] for e in _EXPECTED_SECTIONS]


def test_sections_deps_and_provides(tmp_path: Path) -> None:
    sections_result = _do_sections(tmp_path)
    # oracle (a): 의존 = 섹션 안 이름 읽기의 직전 저장이 앞 섹션에 있는 것(design §5.1). 합성 블록은 직선 코드라
    # (중첩 함수 없음) 후보 과대 계수가 생길 경로가 없어 기대가 정확히 정해진다. 의존은 최소 1건 이상 있다.
    assert sections_result["proc"].returncode == 0
    secs = _sections_list(json.loads(sections_result["out"].read_bytes().decode("utf-8")))
    got = [{(d["name"], d["section"]) for d in s["deps"]} for s in secs]
    assert got == [e[7] for e in _EXPECTED_SECTIONS]
    assert sum(len(g) for g in got) >= 1
    assert {s["index"]: set(s["provides_to"]) for s in secs} == _EXPECTED_PROVIDES


# ---------------------------------------------------------------------------
# sections 대 표지 병합 조건 (변경 20260922-sections-major-merge, Phase 1 C12, red-green)
# design §5.1 "연속한 대 표지 `print`는 하나로 합친다": 대 표지는 바로 앞 최상위 문장도 대 표지일 때만 앞 섹션에
# 합쳐진다. 세 합성 블록 모두 첫 표지 앞에 문장 하나(`v = 1`)를 두어 머리(P) 섹션이 반드시 있게 했다.
# oracle: 전부 (a) 구성으로 정답이 정해진 합성 입력 -- 기대(섹션 수·kind·category·start 줄·end 줄)는 §5.1 문장을
# 아래 줄별 주석대로 손으로 적용한 것이고, 피검 도구 출력에서 가져온 것은 없다.
# end 줄: §5.1 "섹션 = 표지부터 다음 표지 앞까지의 최상위 문장"이라 섹션 end = 그 섹션 마지막 문장의 줄(합성 입력의
# 문장은 모두 한 줄이라 줄 번호가 구성으로 정해진다). 기대 튜플의 넷째 칸이 그 마지막 문장의 텍스트다.
# ---------------------------------------------------------------------------
# (i) 연속한 대 표지 둘 -> 한 섹션(기존 규칙 유지, 무발동 입력).
_MERGE_CONSECUTIVE = (
    'if __name__ == "__main__":\n'
    '    v = 1\n'                                    # S0 머리(P)
    '    print("# Part M")\n'                        # 대 표지 -> S1 시작
    '    print("=== Test M ===")\n'                  # 바로 앞 문장이 대 표지 -> S1에 합침
    '    assert v == 1\n'                            # S1: Assert -> A
)
_EXPECTED_MERGE_CONSECUTIVE = [
    # (kind, category, 시작 줄의 표지 텍스트 또는 None, 끝 줄의 문장 텍스트)
    ("prelude", "P", None, "v = 1"),
    ("major", "A", 'print("# Part M")', "assert v == 1"),
]

# (i-b) 연속한 대 표지 둘이 블록 끝 -> 한 섹션이고, 두 번째 대 표지가 합친 섹션의 마지막 문장이다.
# 합친 섹션이 두 번째 대 표지 문장까지 포함해야 end가 그 줄이 된다(병합 분기에서 문장을 빠뜨리면 end가 첫 대 표지
# 줄에 머문다). 문장이 표지 print뿐이라 범주 D.
_MERGE_CONSECUTIVE_TAIL = (
    'if __name__ == "__main__":\n'
    '    v = 1\n'                                    # S0 머리(P)
    '    print("# Part T")\n'                        # 대 표지 -> S1 시작
    '    print("=== Test T ===")\n'                  # 바로 앞 문장이 대 표지 -> S1에 합침, S1의 마지막 문장
)
_EXPECTED_MERGE_CONSECUTIVE_TAIL = [
    ("prelude", "P", None, "v = 1"),
    ("major", "D", 'print("# Part T")', 'print("=== Test T ===")'),
]

# (ii) 대 표지·표지 아닌 문장·대 표지 -> 대 표지 섹션 둘(앞 섹션에만 assert -> A와 D로 갈린다).
_SPLIT_BY_STATEMENT = (
    'if __name__ == "__main__":\n'
    '    v = 1\n'                                    # S0 머리(P)
    '    print("=== First S ===")\n'                 # 대 표지 -> S1 시작
    '    assert v == 1\n'                            # S1: Assert -> A (표지 아닌 문장)
    '    print("=== Second S ===")\n'                # 바로 앞 문장이 표지 아님 -> 새 섹션 S2
    '    print("static text S")\n'                   # S2: 정적 문자열 print뿐 -> D
)
_EXPECTED_SPLIT_BY_STATEMENT = [
    ("prelude", "P", None, "v = 1"),
    ("major", "A", 'print("=== First S ===")', "assert v == 1"),
    ("major", "D", 'print("=== Second S ===")', 'print("static text S")'),
]

# (iii) 대 표지·소 표지·대 표지 -> 표지 섹션 셋.
_SPLIT_BY_SUB = (
    'if __name__ == "__main__":\n'
    '    v = 1\n'                                    # S0 머리(P)
    '    print("=== First U ===")\n'                 # 대 표지 -> S1 시작
    '    assert v == 1\n'                            # S1: Assert -> A
    '    print("  [sub] mid U")\n'                   # 소 표지 -> S2 시작, 문장은 표지뿐 -> D
    '    print("=== Second U ===")\n'                # 바로 앞 문장이 소 표지 -> 새 섹션 S3, 표지뿐 -> D
)
_EXPECTED_SPLIT_BY_SUB = [
    ("prelude", "P", None, "v = 1"),
    ("major", "A", 'print("=== First U ===")', "assert v == 1"),
    ("sub", "D", 'print("  [sub] mid U")', 'print("  [sub] mid U")'),
    ("major", "D", 'print("=== Second U ===")', 'print("=== Second U ===")'),
]


def _sections_of(tmp_path: Path, source: str) -> list:
    # 호출 방식은 위 `_do_sections`와 같다(하위 프로세스 `sections --source --out`).
    src = _write(tmp_path / "mergemod.py", source)
    out = tmp_path / "sections.json"
    proc = _run("sections", "--source", str(src), "--out", str(out))
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    return _sections_list(json.loads(out.read_bytes().decode("utf-8")))


def assert_sections_match(secs: list, source: str, expected: list) -> None:
    # 섹션 수·index 순서·kind·category·표지 섹션의 start 줄(합성 입력에서 표지 문장의 줄 번호, 구성으로 정해짐)·
    # 모든 섹션의 end 줄(그 섹션 마지막 문장의 줄 번호, 구성으로 정해짐).
    assert [s["index"] for s in secs] == list(range(len(expected)))
    assert [s["kind"] for s in secs] == [e[0] for e in expected]
    assert [s["category"] for s in secs] == [e[1] for e in expected]
    for (_kind, _cat, marker, _last), sec in zip(expected[1:], secs[1:]):
        assert sec["start"] == _line_of(source, marker), sec
    assert [s["end"] for s in secs] == [_line_of(source, e[3]) for e in expected]


def test_sections_consecutive_majors_merge_into_one(tmp_path: Path) -> None:
    # oracle (a): 경우 (i) -- 대 표지 둘이 연달아 있으면 §5.1대로 한 섹션(머리 + 대 표지 1 = 2개),
    # 합친 섹션은 첫 대 표지 줄에서 시작한다.
    secs = _sections_of(tmp_path, _MERGE_CONSECUTIVE)
    assert len(secs) == 2
    assert_sections_match(secs, _MERGE_CONSECUTIVE, _EXPECTED_MERGE_CONSECUTIVE)


def test_sections_consecutive_majors_merged_section_ends_at_second_major(tmp_path: Path) -> None:
    # oracle (a): 경우 (i-b) -- 연속한 대 표지 둘이 블록 끝이면 §5.1대로 한 섹션(머리 + 대 표지 1 = 2개)이고,
    # 합친 섹션은 첫 대 표지 줄에서 시작해 두 번째 대 표지 줄에서 끝난다(두 번째 대 표지 문장도 그 섹션의 문장).
    secs = _sections_of(tmp_path, _MERGE_CONSECUTIVE_TAIL)
    assert len(secs) == 2
    assert secs[1]["end"] == _line_of(_MERGE_CONSECUTIVE_TAIL, 'print("=== Test T ===")')
    assert_sections_match(secs, _MERGE_CONSECUTIVE_TAIL, _EXPECTED_MERGE_CONSECUTIVE_TAIL)


def test_sections_major_after_plain_statement_starts_new_section(tmp_path: Path) -> None:
    # oracle (a): 경우 (ii) -- 두 번째 대 표지의 바로 앞 문장이 `assert`(표지 아님)라 연속이 아니다 -> 새 섹션.
    # 섹션 3개(P, A, D). 앞 섹션만 assert가 있어 범주가 A와 D로 갈린다.
    secs = _sections_of(tmp_path, _SPLIT_BY_STATEMENT)
    assert len(secs) == 3
    assert_sections_match(secs, _SPLIT_BY_STATEMENT, _EXPECTED_SPLIT_BY_STATEMENT)


def test_sections_major_after_sub_marker_starts_new_section(tmp_path: Path) -> None:
    # oracle (a): 경우 (iii) -- 두 번째 대 표지의 바로 앞 문장이 소 표지라 연속한 대 표지가 아니다 -> 새 섹션.
    # 섹션 4개(P, major A, sub D, major D).
    secs = _sections_of(tmp_path, _SPLIT_BY_SUB)
    assert len(secs) == 4
    assert_sections_match(secs, _SPLIT_BY_SUB, _EXPECTED_SPLIT_BY_SUB)


def test_sections_rejects_missing_source_exit2(tmp_path: Path) -> None:
    # oracle (a): 없는 파일 -> design exit code '2 입력 오류(파일 없음)'.
    proc = _run("sections", "--source", str(tmp_path / "nope.py"), "--out", str(tmp_path / "s.json"))
    assert proc.returncode == 2


# ---------------------------------------------------------------------------
# scan (design §5.2 `scan`, §5.1 '인라인 self-test')
# ---------------------------------------------------------------------------
# 범주 A 섹션이 있는 블록(표지 뒤 assert).
_SCAN_A = 'X = 1\n\nif __name__ == "__main__":\n    print("=== t ===")\n    assert X == 1\n'
# 범주 B 섹션이 있는 블록(소 표지 뒤 PASS/FAIL 토큰 print).
_SCAN_B = ('X = 1\n\nif __name__ == "__main__":\n    print("  [check]")\n'
           '    print("  PASS" if X == 1 else "  FAIL")\n')
# CLI 블록: 표지 없음 -> 전부 머리(P). 머리는 A 조건(assert)이 있어도 P다(범주는 위에서부터 처음 맞는 것).
_SCAN_CLI = ('import sys\n\nif __name__ == "__main__":\n    args = sys.argv[1:]\n'
             '    assert isinstance(args, list)\n    print(args)\n')
# 블록 없음.
_SCAN_NONE = "def f():\n    return 1\n"
# 표지는 있지만 판정 없음(D·C 섹션만).
_SCAN_DC = ('if __name__ == "__main__":\n    print("=== info ===")\n    print("  [note] x")\n'
            '    v = 2 + 3\n')


@pytest.mark.parametrize(
    "files, expected",
    [
        ({"a.py": _SCAN_A, "n.py": _SCAN_NONE}, 1),
        ({"b.py": _SCAN_B, "n.py": _SCAN_NONE}, 1),
        ({"cli.py": _SCAN_CLI, "n.py": _SCAN_NONE, "dc.py": _SCAN_DC}, 0),
        ({"n.py": _SCAN_NONE, "sub/a.py": _SCAN_A, "sub/b.py": _SCAN_B}, 0),
    ],
    ids=["A_section_found", "B_section_found", "cli_and_dc_only", "selftest_only_in_subdir"],
)
def test_scan_exit_code(tmp_path: Path, files: dict, expected: int) -> None:
    # oracle (a): 디렉터리 구성으로 정해진 기대 -- 최상위 *.py 중 A·B 섹션 블록이 있으면 1, 없으면 0,
    # 하위 디렉터리는 보지 않는다(design §5.2 `scan`).
    root = tmp_path / "root"
    for rel, text in files.items():
        _write(root / rel, text)
    proc = _run("scan", "--root", str(root))
    assert proc.returncode == expected, proc.stderr.decode("utf-8", "replace")


def test_scan_out_json_lists_top_level_files_only(tmp_path: Path) -> None:
    # oracle (a): --out JSON은 `<디렉터리>/*.py`마다 쓴다 -- 최상위 파일 이름이 있고, 하위 디렉터리 파일 이름은 없다.
    root = tmp_path / "root"
    _write(root / "topsel.py", _SCAN_A)
    _write(root / "topnone.py", _SCAN_NONE)
    _write(root / "deep" / "hiddensel.py", _SCAN_B)
    out = tmp_path / "scan.json"
    proc = _run("scan", "--root", str(root), "--out", str(out))
    assert proc.returncode == 1
    text = out.read_bytes().decode("utf-8")
    json.loads(text)
    assert "topsel.py" in text
    assert "topnone.py" in text
    assert "hiddensel" not in text


def test_scan_rejects_missing_root_exit2(tmp_path: Path) -> None:
    # oracle (a): 없는 디렉터리 -> design exit code '2 입력 오류(파일 없음)'.
    proc = _run("scan", "--root", str(tmp_path / "no_such_dir"))
    assert proc.returncode == 2
