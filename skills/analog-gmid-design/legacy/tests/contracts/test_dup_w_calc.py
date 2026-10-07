"""Phase 2 P8 계약: 소자 폭 식 W = L·ID/IDu 인라인을 식 함수 하나로(20260930-dup-w-calc).

spec card `docs/02-design/specs/20260930-dup-w-calc.spec.md` 계약 1·2·3을 판정한다. 정본 명세는 design
`gain-budget-gmid-sizing.20-dead-code-dup` v1.2 §3 DIFF-DUP·§6.1·§8 P8.
계약 4·5(E-LIB·E-INST 동작 보존, 실행 시간 관찰)는 auditor가 base와 병합본을 실행해 비교한다 -- 여기서 기대값을 박지 않는다.
계약 6(레지스트리 §2 문서)은 문서 판정이라 여기서 보지 않는다.

판정 셋:

* 계약 1: `sizing_recipe.width_from_id_density(L, ID, IDu)`의 결과가 같은 입력의 인라인 식 `L * ID / IDu`·`ID * L / IDu`와
  비트 단위로 같다(IEEE 754 곱셈은 교환적이고 연산 순서가 같다). 새 함수는 가드를 더하지 않으므로(spec card 의도 절)
  `IDu == 0.0`에서도 인라인 식과 같은 결과(`ZeroDivisionError`)를 낸다.
* 계약 2: 엔진 `A/*.py`(최상위만)·`workspaces/run_harness.py`에서 W 식 모양의 산술식이 `width_from_id_density` 본문 밖에 0개.
  모양(spec card 계약 2 문장 그대로): `(a * b) / c`에서 `c`의 이름(변수 이름·속성 이름·문자열 첨자 키)이 대소문자 무시 `idu`를
  포함하고, `a`·`b` 중 하나가 L 계열, 다른 하나가 ID 계열.
  L 계열 = 앞의 밑줄과 앞의 소문자 `m` 하나를 뗀 이름이 `L`이거나 `L_`로 시작하거나 `L` 뒤에 숫자 또는 `c`만 오는 것.
  ID 계열 = 이름이 `ID`를 포함하거나 `I`와 같은 것. base에서는 18개라 red이고 통합 뒤 green이다.
* 계약 3: `size_transistor` 본문이 `width_from_id_density`를 부르고, 시그니처가 interface card 표 그대로다.

oracle 대조(계획 N3.12.3):

* test_width_from_id_density_matches_inline_formula_* -- (b) 폐형식: 기대값은 방법론 식 1.18 `L * ID / IDu` 자체와
  IEEE 곱셈 교환성으로 얻은 `ID * L / IDu`(spec card 'oracle 종류와 출처' (b)). 피검 함수 출력으로 기대값을 만들지 않는다 --
  test 안에서 같은 입력에 대해 식을 직접 평가한다(이것이 곧 spec card가 정한 정답이다).
* test_width_from_id_density_zero_density_behaves_like_inline -- (b) 같은 폐형식: 인라인 식을 IDu=0.0으로 평가하면
  `ZeroDivisionError`이고, spec card 의도 절 '함수는 가드를 더하지 않는다'가 같은 행동을 요구한다.
* test_width_from_id_density_signature -- (d) 사용자가 승인한 spec card·interface card '신규 시그니처' 표.
* test_no_inline_w_formula_outside_new_function -- (a) 저장소의 현재 엔진 AST가 입력, 기대값은 '0개'(spec card 계약 2).
* test_w_formula_check_rejects_* / accepts_* -- (a) 합성 소스: spec card 이름 예시·'거부해야 할 입력'을 각각 넣어(또는 넣지
  않고) 손으로 만들었으므로 정답이 구성으로 정해진다. 판정이 실제로 거부·통과하는지 본다.
* test_size_transistor_calls_new_function, test_size_transistor_signature_unchanged -- (a) 현재 AST가 입력, 기대값은
  '호출 1개 이상'(spec card 계약 3) / (d) interface card 기존 시그니처 표.
* test_call_check_rejects_* / accepts_* -- (a) 합성 소스로 계약 3 판정의 거부·통과를 본다.
"""
import ast
import importlib
import inspect
import math
import pathlib
import random
import re
import struct
import sys

import pytest

# contracts -> tests -> assets(A) -> analog-gmid-design -> skills -> 저장소 루트
_TESTS_DIR = pathlib.Path(__file__).resolve().parents[1]
_ASSETS_DIR = _TESTS_DIR.parent
_REPO_ROOT = _ASSETS_DIR.parents[2]
_RUN_HARNESS = _REPO_ROOT / "workspaces" / "run_harness.py"

_NEW_FUNC = "width_from_id_density"
_CANON_FUNC = "size_transistor"
# 판정 범위가 공허하지 않다는 근거: 새 함수와 size_transistor가 사는 파일 + run_harness.
_REQUIRED_ENGINE_FILES = ("sizing_recipe.py", "run_harness.py")


def _engine_files() -> list:
    """계약 2의 엔진 범위: `A/*.py`(하위 디렉터리 제외) + `workspaces/run_harness.py`."""
    return sorted(_ASSETS_DIR.glob("*.py")) + [_RUN_HARNESS]


def _rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(_REPO_ROOT).as_posix()


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _import_sizing_recipe():
    if str(_ASSETS_DIR) not in sys.path:
        sys.path.insert(0, str(_ASSETS_DIR))
    return importlib.import_module("sizing_recipe")


def _new_function():
    """피검 함수. 함수 안에서 가져온다 -- base(함수 없음)에서 test별 실패(red)가 되도록."""
    module = _import_sizing_recipe()
    assert hasattr(module, _NEW_FUNC), f"sizing_recipe 에 spec card 계약 1의 {_NEW_FUNC} 가 없다"
    return getattr(module, _NEW_FUNC)


def _bits(x: float) -> bytes:
    """IEEE 754 binary64 비트 패턴(부호 0 포함)."""
    return struct.pack("<d", x)


# --------------------------------------------------------------------------------------
# 계약 1: 새 함수 = 인라인 식(비트 단위)
# --------------------------------------------------------------------------------------
def assert_bitwise_equal_to_inline(fn, L: float, ID: float, IDu: float) -> None:
    """판정: fn(L, ID, IDu)가 인라인 식 `L * ID / IDu`·`ID * L / IDu`와 비트 단위로 같은 float다."""
    expected = L * ID / IDu            # oracle (b): 방법론 식 1.18 그대로
    expected_swapped = ID * L / IDu    # oracle (b): IEEE 곱셈 교환성 -- 18곳 중 곱 순서가 다른 호출부의 식
    got = fn(L, ID, IDu)
    got_kw = fn(L=L, ID=ID, IDu=IDu)
    for value, how in ((got, "위치 인자"), (got_kw, "키워드 인자")):
        assert type(value) is float, f"{how}: 반환형이 float가 아니다 {type(value)!r} (L={L!r}, ID={ID!r}, IDu={IDu!r})"
        assert value == expected, f"{how}: {value!r} != L*ID/IDu {expected!r} (L={L!r}, ID={ID!r}, IDu={IDu!r})"
        assert _bits(value) == _bits(expected), f"{how}: 비트 불일치 {value!r} vs {expected!r}"
        assert _bits(value) == _bits(expected_swapped), f"{how}: ID*L/IDu 와 비트 불일치 {value!r} vs {expected_swapped!r}"
        assert math.copysign(1.0, value) == math.copysign(1.0, expected), f"{how}: 부호 불일치 {value!r} vs {expected!r}"


# 손으로 고른 표본: 서브마이크론~수십 um L, pA~수십 mA ID, 작은~큰 IDu, 부호 조합, 0, 부호 있는 0, 반올림이 갈리는 값.
_HAND_CASES = [
    (0.15e-6, 10e-6, 3.2),                  # sky130 최소 L 근처, 10 uA
    (0.5e-6, 1e-9, 0.02),                   # nA 전류, 작은 IDu
    (1e-6, 1e-3, 15.0),                     # mA 전류
    (20e-6, 50e-3, 1e-4),                   # 긴 L, 큰 전류, 작은 IDu
    (1.8e-7, 3.3e-12, 7.7e-6),              # pA 전류
    (0.35e-6, -25e-6, 4.1),                 # 음의 ID(PMOS 부호 규약으로 들어올 수 있는 값)
    (0.35e-6, 25e-6, -4.1),                 # 음의 IDu
    (-0.35e-6, -25e-6, -4.1),               # 부호 셋 다 음
    (0.0, 10e-6, 2.0),                      # L = 0
    (0.5e-6, 0.0, 2.0),                     # ID = 0
    (-0.0, 10e-6, 2.0),                     # 음의 0 -> 결과 -0.0 (부호 비트 판정)
    (0.5e-6, -0.0, 2.0),
    (0.1, 0.2, 0.3),                        # 이진 표현이 정확하지 않은 값 -- 반올림 경로
    (1.0 / 3.0, 3.0, 7.0),
    (0.1, 0.3, 0.7),                        # L*(ID/IDu) 와 (L*ID)/IDu 의 반올림이 갈리는 값
    (5e-324, 1.0, 1.0),                     # 서브노멀 입력
    (1e-200, 1e-200, 1.0),                  # 곱이 언더플로 -> 0
    (1e200, 1e200, 1e10),                   # 곱이 오버플로 -> inf (유한 입력, 인라인 식과 같은 결과여야 한다)
    (1.7976931348623157e308, 1.0, 2.0),     # 최대 유한값
]


@pytest.mark.parametrize(("L", "ID", "IDu"), _HAND_CASES)
def test_width_from_id_density_matches_inline_formula_hand_cases(L, ID, IDu):
    # oracle (b): 기대값 = 같은 입력으로 평가한 인라인 식 `L * ID / IDu`·`ID * L / IDu`(spec card 계약 1).
    assert_bitwise_equal_to_inline(_new_function(), L, ID, IDu)


def _log_uniform(rng: random.Random, lo_exp: float, hi_exp: float) -> float:
    return 10.0 ** rng.uniform(lo_exp, hi_exp)


def _random_cases(seed: int, n: int) -> list:
    """시드 고정 표본: 크기는 로그 균등, 부호는 무작위. 범위는 엔진 입력보다 넓게 잡는다."""
    rng = random.Random(seed)
    cases = []
    for _ in range(n):
        L = _log_uniform(rng, -8.0, -3.0)        # 10 nm ~ 1 mm
        ID = _log_uniform(rng, -13.0, -1.0)      # 0.1 pA ~ 100 mA
        IDu = _log_uniform(rng, -9.0, 3.0)       # 단위 폭 전류밀도 A/m 대역보다 넓게
        signs = [rng.choice((1.0, -1.0)) for _ in range(3)]
        cases.append((signs[0] * L, signs[1] * ID, signs[2] * IDu))
    return cases


def _random_finite_bit_patterns(seed: int, n: int) -> list:
    """시드 고정 표본: 임의 비트 패턴 중 유한한 binary64만(전 지수 범위)."""
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        triple = []
        while len(triple) < 3:
            x = struct.unpack("<d", rng.getrandbits(64).to_bytes(8, "little"))[0]
            if math.isfinite(x) and x != 0.0:
                triple.append(x)
        out.append(tuple(triple))
    return out


def test_width_from_id_density_matches_inline_formula_seeded_physical_range():
    # oracle (b): 시드 고정(20260930) 난수 표본 2000개, 각 표본의 기대값 = 인라인 식.
    fn = _new_function()
    cases = _random_cases(20260930, 2000)
    assert len(cases) == 2000
    for L, ID, IDu in cases:
        assert_bitwise_equal_to_inline(fn, L, ID, IDu)


def test_width_from_id_density_matches_inline_formula_seeded_bit_patterns():
    # oracle (b): 시드 고정(930) 임의 유한 비트 패턴 1000개(오버·언더플로 포함), 기대값 = 인라인 식.
    fn = _new_function()
    cases = _random_finite_bit_patterns(930, 1000)
    assert len(cases) == 1000
    for L, ID, IDu in cases:
        assert_bitwise_equal_to_inline(fn, L, ID, IDu)


def test_width_from_id_density_zero_density_behaves_like_inline():
    # oracle (b): 인라인 식은 IDu=0.0에서 ZeroDivisionError. spec card 의도 절 '함수는 가드를 더하지 않는다(동작 보존)'.
    fn = _new_function()
    with pytest.raises(ZeroDivisionError):
        _ = 0.5e-6 * 10e-6 / 0.0   # 전제: 인라인 식의 행동
    with pytest.raises(ZeroDivisionError):
        fn(0.5e-6, 10e-6, 0.0)
    with pytest.raises(ZeroDivisionError):
        fn(0.5e-6, 10e-6, -0.0)


def test_width_from_id_density_signature():
    # oracle (d): spec card·interface card 신규 시그니처 `def width_from_id_density(L: float, ID: float, IDu: float) -> float`.
    sig = inspect.signature(_new_function())
    assert list(sig.parameters) == ["L", "ID", "IDu"], sig
    for p in sig.parameters.values():
        assert p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD, (p.name, p.kind)
        assert p.default is inspect.Parameter.empty, (p.name, p.default)


def test_bitwise_check_rejects_wrong_implementations():
    # oracle (a): 식과 다르도록 구성한 합성 구현 -> 판정이 실패해야 한다(판정이 공허하지 않다).
    wrong = [
        lambda L, ID, IDu: L * (ID / IDu),          # 연산 순서가 달라 반올림이 갈린다
        lambda L, ID, IDu: abs(L * ID / IDu),        # 부호 손실
        lambda L, ID, IDu: L * ID / max(IDu, 1e-30), # 가드 추가(0 근처·음수에서 다름)
    ]
    # 판정이 갈리는 입력(구성으로 고름): (0.1, 0.3, 0.7)은 L*(ID/IDu) 와 (L*ID)/IDu 의 반올림이 다르다 -- 전제를 확인.
    assert _bits(0.1 * 0.3 / 0.7) != _bits(0.1 * (0.3 / 0.7))
    with pytest.raises(AssertionError):
        assert_bitwise_equal_to_inline(wrong[0], 0.1, 0.3, 0.7)
    with pytest.raises(AssertionError):
        assert_bitwise_equal_to_inline(wrong[1], 0.35e-6, -25e-6, 4.1)
    with pytest.raises(AssertionError):
        assert_bitwise_equal_to_inline(wrong[2], 0.35e-6, 25e-6, -4.1)
    with pytest.raises(AssertionError):  # -0.0 과 0.0 은 == 이지만 비트가 다르다
        assert_bitwise_equal_to_inline(lambda L, ID, IDu: 0.0, -0.0, 10e-6, 2.0)
    with pytest.raises(AssertionError):  # numpy 스칼라 등 float 아닌 반환형
        assert_bitwise_equal_to_inline(lambda L, ID, IDu: _FloatSub(L * ID / IDu), 0.5e-6, 10e-6, 2.0)
    assert_bitwise_equal_to_inline(lambda L, ID, IDu: L * ID / IDu, 0.1, 0.2, 0.3)


class _FloatSub(float):
    """float가 아닌 반환형의 합성 대역(판정의 반환형 거부를 보이는 용도)."""


# --------------------------------------------------------------------------------------
# 계약 2: W 식 인라인 0
# --------------------------------------------------------------------------------------
_IDU_RE = re.compile("idu", re.IGNORECASE)
_L_TAIL_RE = re.compile(r"L(?:[0-9]+|c)")


def _operand_name(node: ast.AST):
    """spec card 계약 2의 '이름': Name.id, Attribute.attr, 문자열 상수 첨자 키. 그 밖은 None."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        key = node.slice
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            return key.value
    return None


def is_l_family(name) -> bool:
    """L 계열: 앞의 밑줄과 앞의 소문자 `m` 하나를 뗀 이름이 `L` / `L_...` / `L`+숫자 / `Lc`."""
    if not name:
        return False
    stem = name.lstrip("_")
    if stem.startswith("m"):
        stem = stem[1:]
    return stem == "L" or stem.startswith("L_") or _L_TAIL_RE.fullmatch(stem) is not None


def is_id_family(name) -> bool:
    """ID 계열: 이름이 `ID`를 포함하거나 `I`와 같다."""
    return bool(name) and ("ID" in name or name == "I")


def _is_w_formula(node: ast.AST) -> bool:
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)):
        return False
    num = node.left
    if not (isinstance(num, ast.BinOp) and isinstance(num.op, ast.Mult)):
        return False
    denom = _operand_name(node.right)
    if denom is None or not _IDU_RE.search(denom):
        return False
    a, b = _operand_name(num.left), _operand_name(num.right)
    return (is_l_family(a) and is_id_family(b)) or (is_id_family(a) and is_l_family(b))


def _excluded_spans(tree: ast.AST) -> list:
    """`width_from_id_density` 정의 본문의 줄 구간 목록."""
    spans = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == _NEW_FUNC:
            spans.append((node.lineno, node.end_lineno))
    return spans


def inline_w_formulas(source: str) -> list:
    """소스 안의 W 식 모양 산술식(줄, 식 소스) -- `width_from_id_density` 본문 밖만, 정렬."""
    tree = ast.parse(source)
    spans = _excluded_spans(tree)
    hits = []
    for node in ast.walk(tree):
        if _is_w_formula(node):
            if any(lo <= node.lineno <= hi for lo, hi in spans):
                continue
            hits.append((node.lineno, ast.get_source_segment(source, node) or ast.unparse(node)))
    return sorted(hits)


def assert_no_inline_w_formula(source: str, where: str) -> None:
    """판정: `source`에 W 식 인라인(새 함수 본문 밖)이 없다."""
    hits = inline_w_formulas(source)
    assert hits == [], f"{where}: W = L*ID/IDu 인라인이 남아 있다(줄, 식) {hits}"


def assert_engine_scope_present(files: list) -> None:
    """판정 범위가 공허하지 않다: 새 함수가 들어갈 파일과 run_harness가 범위 안에 실재한다."""
    names = {p.name for p in files if p.exists()}
    missing = [n for n in _REQUIRED_ENGINE_FILES if n not in names]
    assert missing == [], f"판정 범위에 있어야 할 엔진 파일이 없다: {missing}"


def test_no_inline_w_formula_outside_new_function():
    # oracle (a): 저장소의 현재 엔진 AST가 입력, 기대값은 '0개'(spec card 계약 2). base에서는 18개라 red.
    files = _engine_files()
    assert_engine_scope_present(files)
    offenders = {}
    for path in files:
        hits = inline_w_formulas(_read(path))
        if hits:
            offenders[_rel(path)] = hits
    total = sum(len(v) for v in offenders.values())
    assert offenders == {}, f"계약 2 위반 -- W 식 인라인 {total}개: {offenders}"


# spec card 계약 2 이름 예시 각각: L 계열 8종 × ID 계열 4종(+ 계약 문장의 ID_m·ID2), 분모 4종.
_L_EXAMPLES = ["L", "_L", "mL", "L_m", "L_up", "L2", "Lc", 'dev["L"]']
_ID_EXAMPLES = ["ID", "ID_target", "I", 'dev["ID"]', "ID_m", "ID2"]
_IDU_EXAMPLES = ["idu", "IDu", "_idu_l", "idu2"]


def _reject_sources() -> list:
    cases = []
    for lname in _L_EXAMPLES:
        cases.append((f"W = {lname} * ID / IDu\n", f"L={lname}"))
    for iname in _ID_EXAMPLES:
        cases.append((f"W = L * {iname} / idu\n", f"ID={iname}"))
    for dname in _IDU_EXAMPLES:
        cases.append((f"W = ID * L / {dname}\n", f"IDu={dname}"))
    cases += [
        ("W = self.L * self.ID / self.IDu\n", "속성 이름"),
        ('W = row["L"] * row["ID"] / row["IDu"]\n', "첨자 키 셋"),
        ("W = ID_target * mL / lut.idu\n", "곱 순서 뒤집힘 + 속성 분모"),
        ("W = (L * ID) / IDu\n", "괄호"),
        ("def f(L, ID, IDu):\n    if IDu <= 0:\n        return None\n    return L * ID / IDu\n", "함수 안(가드 뒤)"),
        ("ws = [L2 * I / idu2 for _ in range(3)]\n", "컴프리헨션 안"),
        ("def width_from_id_density(L, ID, IDu):\n    return L * ID / IDu\n"
         "def g(L, ID, IDu):\n    return L * ID / IDu\n", "새 함수 밖의 두 번째 인라인"),
        ("W = max(Lc * ID / _idu_l, W_min)\n", "호출 인자 안"),
    ]
    return cases


@pytest.mark.parametrize(("source", "label"), _reject_sources(), ids=[c[1] for c in _reject_sources()])
def test_w_formula_check_rejects_synthetic_inline(source, label):
    # oracle (a): W 식 인라인을 하나 넣어 손으로 만든 합성 소스 -> 판정이 실패해야 한다.
    with pytest.raises(AssertionError):
        assert_no_inline_w_formula(source, f"합성 소스({label})")
    assert len(inline_w_formulas(source)) == 1, (label, inline_w_formulas(source))


@pytest.mark.parametrize(
    ("source", "label"),
    [
        ("A = L * L / idu\n", "L*L/idu(면적 대용, ID 계열 없음)"),
        ("idu = raw * L / self._w_ref_effective(L)\n", "raw*L/w_ref(IDu를 만드는 식)"),
        ("idu = raw * L / w_ref\n", "raw*L/w_ref 이름 분모"),
        ("W = L * ID / w_unit\n", "분모에 idu 없음"),
        ("W = L * ID / gm\n", "분모에 idu 없음(gm)"),
        ("def width_from_id_density(L, ID, IDu):\n    return L * ID / IDu\n", "새 함수 본문 안"),
        ("def width_from_id_density(L, ID, IDu):\n    w = ID * L / IDu\n    return w\n", "새 함수 본문 안(곱 순서 반대)"),
        ("# W = L * ID / IDu\nW = width_from_id_density(L, ID, IDu)\n", "주석 + 호출"),
        ('doc = "W = L * ID / IDu"\n', "문자열"),
        ('def f():\n    """W = L * ID / IDu (식 1.18)."""\n    return 0\n', "docstring"),
        ("W = L * ID * IDu\n", "나눗셈 없음"),
        ("W = L * (ID / IDu)\n", "(a*b)/c 모양 아님"),
        ("W = gm * L / IDu\n", "ID 계열 없음(gm)"),
        ("W = Lmin * ID / IDu\n", "L 계열 아님(Lmin)"),
        ("W = VDD * ID / IDu\n", "L 계열 아님(VDD)"),
        ("W = W_L * ID / IDu\n", "L 계열 아님(W_L)"),
        ("W = L * id_ / IDu\n", "ID 계열 아님(소문자 id_)"),
    ],
)
def test_w_formula_check_accepts_sources_without_inline(source, label):
    # oracle (a): spec card '거부해야 할 입력'의 '발견하면 안 되는 것' 및 모양 밖 식으로 구성한 합성 소스 -> 통과해야 한다.
    assert_no_inline_w_formula(source, f"합성 소스({label})")
    assert inline_w_formulas(source) == []


@pytest.mark.parametrize(
    ("name", "expected"),
    [("L", True), ("_L", True), ("mL", True), ("L_m", True), ("L_up", True), ("L2", True), ("L10", True),
     ("Lc", True),
     ("Lmin", False), ("Lcd", False), ("l", False), ("mm", False), ("W_L", False), ("mmL", False), ("VL", False),
     ("L2c", False), ("", False), (None, False)],
)
def test_l_family_rule(name, expected):
    # oracle (a): spec card 계약 2 L 계열 문장에서 구성으로 정해지는 분류. 예시 이름은 True, 규칙 밖 이름은 False.
    assert is_l_family(name) is expected, name


@pytest.mark.parametrize(
    ("name", "expected"),
    [("ID", True), ("ID_target", True), ("ID_m", True), ("ID2", True), ("I", True), ("tail_ID", True),
     ("id", False), ("Id", False), ("I2", False), ("IB", False), ("", False), (None, False)],
)
def test_id_family_rule(name, expected):
    # oracle (a): spec card 계약 2 ID 계열 문장('ID를 포함하거나 I와 같은 것')에서 구성으로 정해지는 분류.
    assert is_id_family(name) is expected, name


# --------------------------------------------------------------------------------------
# 계약 3: size_transistor가 새 함수를 부른다, 시그니처 불변
# --------------------------------------------------------------------------------------
def calls_in_function(source: str, func_name: str, callee: str) -> int:
    """`source` 안 모든 `def func_name` 본문에서 `callee(...)`/`x.callee(...)` 호출 수. 정의가 없으면 -1."""
    tree = ast.parse(source)
    defs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == func_name]
    if not defs:
        return -1
    count = 0
    for d in defs:
        for node in ast.walk(d):
            if isinstance(node, ast.Call):
                f = node.func
                if (isinstance(f, ast.Name) and f.id == callee) or (isinstance(f, ast.Attribute) and f.attr == callee):
                    count += 1
    return count


def assert_function_calls(source: str, func_name: str, callee: str, where: str) -> None:
    """판정: `func_name` 정의가 있고 그 본문이 `callee`를 한 번 이상 부른다."""
    n = calls_in_function(source, func_name, callee)
    assert n != -1, f"{where}: {func_name} 정의가 없다"
    assert n >= 1, f"{where}: {func_name} 본문이 {callee} 를 부르지 않는다"


def test_size_transistor_calls_new_function():
    # oracle (a): 현재 sizing_recipe AST가 입력, 기대값은 'size_transistor 본문에 width_from_id_density 호출 1개 이상'(계약 3).
    path = _ASSETS_DIR / "sizing_recipe.py"
    assert path.exists(), path
    assert_function_calls(_read(path), _CANON_FUNC, _NEW_FUNC, _rel(path))


def test_size_transistor_signature_unchanged():
    # oracle (d): interface card 기존 시그니처
    # `def size_transistor(gm: float, gm_id: float, L: float, lut: GmIdLUT, vds: float, vsb: float=0.0) -> SizingResult`.
    sig = inspect.signature(getattr(_import_sizing_recipe(), _CANON_FUNC))
    assert list(sig.parameters) == ["gm", "gm_id", "L", "lut", "vds", "vsb"], sig
    defaults = {k: p.default for k, p in sig.parameters.items() if p.default is not inspect.Parameter.empty}
    assert defaults == {"vsb": 0.0}, defaults


@pytest.mark.parametrize(
    ("source", "label"),
    [
        ("def size_transistor(gm, gm_id, L, lut, vds, vsb=0.0):\n    return L * gm / gm_id\n", "호출 없음"),
        ("def other():\n    return width_from_id_density(1, 2, 3)\n", "정의 없음"),
        ("def size_transistor(gm, gm_id, L, lut, vds, vsb=0.0):\n    return 0\n"
         "def g():\n    return width_from_id_density(1, 2, 3)\n", "다른 함수에서만 호출"),
        ("def size_transistor(gm, gm_id, L, lut, vds, vsb=0.0):\n    f = width_from_id_density\n    return 0\n",
         "참조만(호출 아님)"),
    ],
)
def test_call_check_rejects_synthetic_sources(source, label):
    # oracle (a): 호출이 없도록 구성한 합성 소스 -> 계약 3 판정이 실패해야 한다.
    with pytest.raises(AssertionError):
        assert_function_calls(source, _CANON_FUNC, _NEW_FUNC, f"합성 소스({label})")


@pytest.mark.parametrize(
    "source",
    [
        "def size_transistor(gm, gm_id, L, lut, vds, vsb=0.0):\n    return width_from_id_density(L, gm / gm_id, 1.0)\n",
        "import sizing_recipe as sr\n"
        "def size_transistor(gm, gm_id, L, lut, vds, vsb=0.0):\n    return sr.width_from_id_density(L, 1.0, 2.0)\n",
    ],
)
def test_call_check_accepts_synthetic_sources(source):
    # oracle (a): 본문에서 새 함수를 부르도록 구성한 합성 소스 -> 통과해야 한다.
    assert_function_calls(source, _CANON_FUNC, _NEW_FUNC, "합성 소스")
    assert calls_in_function(source, _CANON_FUNC, _NEW_FUNC) == 1
