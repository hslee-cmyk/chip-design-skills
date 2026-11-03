"""card IT-2c -- `sizing/_helpers_dc_solve.py` 의 `Circuit` / `region_rows` 정적 구조 (interface 20261104-it2c-icm-config 'Circuit 계약', T-D).

IT-2b 의 `block_columns._Circuit`·`region_rows` AST test (옛 tests/sizing/test_block_columns.py `test_it2b_d_region_rows_*`, 동작 보존 이동)를
새 위치로 옮기고 IT-2c 규칙(tol 항 없음, 전도 필드 읽기 0, EO-1 모듈 import 0)을 더했다.
oracle: (독립) 정적 AST(docstring·주석 제외). 피검 함수를 불러 기대값을 만들지 않는다.
"""
import ast as _ast
import inspect
from pathlib import Path as _Path

import pytest

import gmid_engine as _gmid_engine

ENGINE = _Path(_gmid_engine.__file__).resolve().parent
HELPER = ENGINE / "sizing" / "_helpers_dc_solve.py"


def _docstring_ids(tree):
    ids = set()
    for node in _ast.walk(tree):
        if isinstance(node, (_ast.Module, _ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, _ast.Expr) and isinstance(first.value, _ast.Constant) and isinstance(first.value.value, str):
                ids.add(id(first.value))
    return ids


def _identifiers_and_strings(tree):
    """식별자(이름·속성·정의·인자·키워드·import 이름)와 문자열 상수(docstring 제외)만 -- 주석은 AST 에 없다."""
    skip = _docstring_ids(tree)
    names, strings = set(), set()
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Name):
            names.add(node.id)
        elif isinstance(node, _ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, _ast.arg):
            names.add(node.arg)
        elif isinstance(node, _ast.keyword) and node.arg:
            names.add(node.arg)
        elif isinstance(node, _ast.alias):
            names.update(part for part in ((node.asname or node.name).split(".")) if part)
        elif isinstance(node, _ast.ImportFrom) and node.module:
            names.update(node.module.split("."))
        elif isinstance(node, _ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            strings.add(node.value)
    return names, strings


def _region_rows_scope():
    """`sizing/_helpers_dc_solve.py` (클래스 `Circuit`) 에서 `region_rows` 정의와 그것이 (직접·간접) 부르는 같은 모듈 함수 정의들. 못 찾으면 AssertionError(red)."""
    tree = _ast.parse((HELPER).read_text(encoding="utf-8"))
    defs = {}
    for node in _ast.walk(tree):
        if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            defs.setdefault(node.name, []).append(node)
    assert "region_rows" in defs, "_helpers_dc_solve 에 region_rows 정의가 없다"
    scope, todo = {}, ["region_rows"]
    while todo:
        name = todo.pop()
        if name in scope or name not in defs:
            continue
        scope[name] = defs[name]
        for fn in defs[name]:
            for call in _ast.walk(fn):
                if isinstance(call, _ast.Call):
                    f = call.func
                    callee = f.id if isinstance(f, _ast.Name) else (f.attr if isinstance(f, _ast.Attribute) else None)
                    if callee in defs:
                        todo.append(callee)
    return tree, [fn for fns in scope.values() for fn in fns]


def _const_strings(value):
    if isinstance(value, _ast.Constant) and isinstance(value.value, str):
        return {value.value}
    if isinstance(value, (_ast.Tuple, _ast.List, _ast.Set)):
        parts = [_const_strings(e) for e in value.elts]
        if parts and all(p is not None for p in parts):
            return set().union(*parts)
    return None


def _module_string_constants(path):
    """모듈 수준 `NAME = "문자열"`(또는 문자열 tuple/list/set) 대입 -> {이름: 문자열 집합}."""
    if not path.exists():
        return {}
    out = {}
    for node in _ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, _ast.Assign):
            values = _const_strings(node.value)
            if values is not None:
                for target in node.targets:
                    if isinstance(target, _ast.Name):
                        out[target.id] = values
    return out


def _imported_engine_modules(tree):
    """_helpers_dc_solve.py(= ENGINE/sizing) 가 import 하는 엔진 모듈 파일 경로들(상대 import 와 `gmid_engine.` 절대 import)."""
    paths = []
    for node in _ast.walk(tree):
        if not isinstance(node, _ast.ImportFrom):
            continue
        if node.level:
            base = ENGINE / "sizing"
            for _ in range(node.level - 1):
                base = base.parent
            parts = (node.module or "").split(".") if node.module else []
        elif node.module and node.module.split(".")[0] == "gmid_engine":
            base, parts = ENGINE, node.module.split(".")[1:]
        else:
            continue
        for rel in [parts] + [parts + [a.name] for a in node.names]:
            stem = base.joinpath(*rel) if rel else base
            for cand in (stem.with_suffix(".py"), stem / "__init__.py"):
                if cand.exists() and cand not in paths:
                    paths.append(cand)
    return paths


def test_it2b_d_region_rows_kinds_are_sat_and_triode_only():
    """oracle 대조: (독립) D (b) (S4-나) -- 정적 AST(docstring·주석 제외): `region_rows` 와 그것이 부르는 같은 모듈 함수의 문자열 상수 가운데 행 종류 어휘
    {"sat", "triode", "off"} 의 교집합 = {"sat", "triode"} (`off` 행 없음). 행 종류를 모듈 수준 상수 이름으로 쓰는 경우를 따라간다: 함수 본문의 이름 참조가
    `X = "sat"` 꼴(또는 문자열 tuple/list/set) 모듈 수준 대입을 가리키면 그 값을 더한다 -- _helpers_dc_solve 모듈 안 대입, 그리고 그 모듈이 import 한
    엔진 모듈(상대·절대)의 모듈 수준 대입까지(정적, docstring 제외, 측정 정의 그대로)."""
    tree, fns = _region_rows_scope()
    constants = _module_string_constants(HELPER)
    for path in _imported_engine_modules(tree):
        for name, values in _module_string_constants(path).items():
            constants.setdefault(name, values)
    strings = set()
    for fn in fns:
        strings |= _identifiers_and_strings(fn)[1]
        for name in _identifiers_and_strings(fn)[0]:
            strings |= constants.get(name, set())
    assert strings & {"sat", "triode", "off"} == {"sat", "triode"}, strings & {"sat", "triode", "off"}


def test_it2b_d_region_rows_has_no_zero_vgs_op_point_conduction_columns_or_eo1_import():
    """oracle 대조: (독립) D (c) -- 정적 AST(docstring·주석 제외): `region_rows` 와 그것이 부르는 같은 모듈 함수에 (1) VGS 상수 0 인 `op_point` 호출(5번째 위치
    인자 또는 vgs= 키워드가 숫자 0) 0 (2) `dc_off_current`·`dc_conduction_floor` 읽기(문자열·이름) 0, 그리고 (3) _helpers_dc_solve 모듈의 import 에 공용 전도 판정
    (EO-1) 모듈 이름(`conduct` 포함) 0."""
    tree, fns = _region_rows_scope()
    for fn in fns:
        names, strings = _identifiers_and_strings(fn)
        assert not {"dc_off_current", "dc_conduction_floor"} & (names | strings), fn.name
        for call in _ast.walk(fn):
            if not isinstance(call, _ast.Call):
                continue
            f = call.func
            callee = f.id if isinstance(f, _ast.Name) else (f.attr if isinstance(f, _ast.Attribute) else None)
            if callee != "op_point":
                continue
            vgs = call.args[4] if len(call.args) > 4 else next((k.value for k in call.keywords if k.arg == "vgs"), None)
            assert not (isinstance(vgs, _ast.Constant) and vgs.value == 0), (fn.name, "VGS = 0 op_point 호출")
    imported = set()
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, _ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(a.name for a in node.names)
    assert not [m for m in imported if "conduct" in m.lower()], imported


def test_it2c_region_rows_has_no_tolerance_term():
    """oracle 대조: (독립) T-D / 계약 '경계 = VDS = VDSAT, 판정 여유 0 (O-204), tol 항 없음': `region_rows` 와 그것이 부르는 같은 모듈 함수의 식별자·문자열에
    `tol_vdsat`(대소문자 무시)이 쓰이지 않는다 -- 행 slack 은 VDS − VDSAT 뿐이다."""
    _tree, fns = _region_rows_scope()
    for fn in fns:
        names, strings = _identifiers_and_strings(fn)
        assert not [x for x in (names | strings) if "tol_vdsat" in x.lower()], fn.name


def test_it2c_circuit_has_no_writer_head_or_declared_inputs():
    """oracle 대조: (d) 계약 '`writer_head`·`declared_inputs` 는 없다' + 공개 이름. `Circuit` 은 이 모듈의 클래스이고 생성 서명은 (projection, *, lut, linear)."""
    from gmid_engine.sizing._helpers_dc_solve import Circuit
    assert not hasattr(Circuit, "writer_head") and not hasattr(Circuit, "declared_inputs")
    params = inspect.signature(Circuit).parameters
    assert list(params) == ["projection", "lut", "linear"]
    assert params["lut"].kind is inspect.Parameter.KEYWORD_ONLY and params["linear"].kind is inspect.Parameter.KEYWORD_ONLY


@pytest.mark.parametrize("missing", ["lut", "linear", "both"])
def test_it2c_circuit_requires_lut_and_linear_keywords(missing):
    """oracle 대조: (d) 계약 'Circuit(projection, *, lut, linear). 두 키워드 빠지면 TypeError'."""
    from gmid_engine.sizing._helpers_dc_solve import Circuit
    kw = {k: object() for k in ("lut", "linear") if missing not in (k, "both")}
    with pytest.raises(TypeError):
        Circuit(object(), **kw)


@pytest.mark.parametrize("kind,sign", [("nmos", 1), ("pmos", -1)])
def test_it2c_kind_sign_is_plus_minus_one(kind, sign):
    """oracle 대조: (식) 계약 '정적 kind_sign(kind) -> ±1' -- 포화 행 (d, s, kind_sign, VDS − VDSAT): nmos 는 VDS = V_d − V_s 라 +1, pmos 는 VSD 라 −1."""
    from gmid_engine.sizing._helpers_dc_solve import Circuit
    assert Circuit.kind_sign(kind) == sign
