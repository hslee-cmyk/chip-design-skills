"""PDK 선언 읽기 -- PDK 마다 데이터 파일 하나가 '길이 이름 -> PDK 규칙 식'을 정하고, 값은 PDK 원본 파일에서 계산한다
(계획 N3.16 'PDK 상수' 행, U-30, WP-03, DEC-80 (i), DEC-93 (5), LY10; 소비자 MOD7 `LayoutPdk`, layout CONTRACT 4.1·4.10).

진입점: `read_pdk_decl`.

* 엔진 코드에는 PDK 이름·규칙 번호·숫자·경로가 없다. 선언 파일(JSON)이 원본 파일(경로·sha256·형식·단위)과
  길이마다 규칙 식(`max(poly.2, licon.1 + 2 * licon.11)` 같은 산술식, 이름 = 원본 파일의 규칙 번호)을 정한다.
* 원본 형식 두 가지(선언의 `format`): `lef_statement`(줄 머리 `KEY 값 ;`, 예 tlef `MANUFACTURINGGRID`)와
  `rule_table_csv`(절 머리 행 + 규칙 행 표, 열 번호·절 머리 정규식은 선언이 준다). 규칙 하나가 원본에 두 번 나오면
  모호 -- 식이 그 규칙을 쓸 때만 거부한다.
* 원본 파일은 매 호출 sha256 을 다시 재서 선언값과 대조하고(다르면 거부), 파싱 결과는 부르는 쪽 `BoundedLRU` 에
  (형식, sha256, 파싱 인자) 키로 둔다 -- 같은 파일은 sha256 당 한 번만 파싱한다. 모듈 수준 캐시는 없다(규칙 G).
* 실패는 전부 `SchemaRejectedError(detail={"reason": ...})`(로드 게이트 거부, 사유 키는 core CONTRACT 9절).
"""
import ast
import codecs
import csv
import dataclasses
import hashlib
import io
import json
import math
import operator
import os
import re

from .bounded_lru import BoundedLRU
from .determinism import sorted_items
from .failure_errors import SchemaRejectedError

_SCHEMA = "gmid_pdk_decl/1"
_TOP_KEYS = ("note", "pdk", "pdk_root", "quantities", "schema", "sources")
_QUANTITY_KEYS = ("basis", "expression", "source")
_FORMAT_LEF = "lef_statement"
_FORMAT_TABLE = "rule_table_csv"
_SOURCE_KEYS = (
    (_FORMAT_LEF, ("encoding", "format", "note", "path", "sha256", "units_m")),
    (_FORMAT_TABLE, ("encoding", "format", "id_column", "note", "path", "section_column", "section_pattern",
                     "sha256", "unit_column", "units_m", "value_column")),
)
_PARSE_KEYS = (
    (_FORMAT_LEF, ("encoding",)),
    (_FORMAT_TABLE, ("encoding", "id_column", "section_column", "section_pattern", "unit_column", "value_column")),
)
_FUNCTIONS = (("max", max), ("min", min))
_BINOPS = ((ast.Add, operator.add), (ast.Sub, operator.sub), (ast.Mult, operator.mul), (ast.Div, operator.truediv))
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_REFERENCE = re.compile(r"(?<![0-9.A-Za-z_])[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)*")
_LEF_STATEMENT = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s+(\S+)\s*;\s*$")
_PLACEHOLDER = "ref_"
_SHA256 = re.compile(r"[0-9a-f]{64}")


def _reject(reason, **detail):
    return SchemaRejectedError(detail={"reason": reason, **{k: str(v) for k, v in detail.items()}})


@dataclasses.dataclass(frozen=True)
class PdkRule:
    """식이 쓴 규칙 하나: 원본 파일의 값 글자·단위 글자·행 번호(1부터, CSV 는 그 레코드가 끝나는 줄)와 m 값."""

    rule_id: str
    value_m: float
    value_text: str
    unit_text: str
    source: str
    path: str
    sha256: str
    line: int


@dataclasses.dataclass(frozen=True)
class PdkQuantity:
    """선언 길이 하나: `expression`(규칙 번호 식, 그대로 `rule_ids` 에 실린다)을 원본 값으로 계산한 `value_m`(m).
    `rules` = 식에 나온 규칙(식 등장 순, 중복 없음), `basis` = 선언 파일이 적은 유도 근거."""

    name: str
    value_m: float
    expression: str
    rules: tuple
    basis: str


@dataclasses.dataclass(frozen=True)
class PdkDecl:
    """선언 파일 하나의 결과. `quantities` = ((이름, PdkQuantity), ...) 이름 정렬, `sources` = ((이름, 경로, sha256), ...)."""

    pdk: str
    decl_path: str
    decl_sha256: str
    sources: tuple
    quantities: tuple

    def quantity(self, name):
        """이름의 PdkQuantity. 선언에 없으면 `SchemaRejectedError(pdk_quantity_undeclared)`."""
        found = dict(self.quantities).get(name)
        if found is None:
            raise _reject("pdk_quantity_undeclared", quantity=name, decl=self.decl_path)
        return found

    def value(self, name):
        """이름의 값(m)."""
        return self.quantity(name).value_m

    def values(self, names):
        """`names` 순서대로 값(m) tuple."""
        return tuple(self.value(name) for name in names)

    def rule_ids(self, names):
        """`names` 순서대로 ((이름, 규칙 식), ...) -- MOD7 `LayoutPdk.rule_ids` 형식."""
        return tuple((name, self.quantity(name).expression) for name in names)


def _require_keys(where, record, allowed, required):
    if not isinstance(record, dict):
        raise _reject("pdk_decl_shape", where=where)
    unknown = sorted(set(record) - set(allowed))
    missing = sorted(set(required) - set(record))
    if unknown or missing:
        raise _reject("pdk_decl_keys", where=where, unknown=tuple(unknown), missing=tuple(missing))


def _parse_lef(text):
    entries = {}
    for line_no, raw in enumerate(text.splitlines(), start=1):
        match = _LEF_STATEMENT.match(raw.split("#", 1)[0])
        if match:
            key, value = match.groups()
            entries.setdefault(key, []).append((value, "", line_no))
    return entries


def _parse_table(text, params):
    section_re = re.compile(params["section_pattern"])
    sec_col, id_col = params["section_column"], params["id_column"]
    val_col, unit_col = params["value_column"], params["unit_column"]
    entries = {}
    prefix = None
    reader = csv.reader(io.StringIO(text, newline=""))
    for row in reader:
        head = row[sec_col].strip() if len(row) > sec_col else ""
        section = section_re.match(head)
        if section:
            prefix = section.group(1).strip()
            continue
        rid = row[id_col].strip() if len(row) > id_col else ""
        if prefix is None or not rid:
            continue
        value = row[val_col].strip() if len(row) > val_col else ""
        unit = row[unit_col].strip() if len(row) > unit_col else ""
        entries.setdefault(prefix + "." + rid, []).append((value, unit, reader.line_num))
    return entries


def _parsed(fmt, text, params):
    entries = _parse_lef(text) if fmt == _FORMAT_LEF else _parse_table(text, params)
    return tuple((rid, tuple(found)) for rid, found in sorted_items(entries))


def _load_source(root, name, spec, memo):
    if not isinstance(spec, dict):
        raise _reject("pdk_decl_shape", where="sources." + name)
    fmt = spec.get("format")
    allowed = dict(_SOURCE_KEYS).get(fmt)
    if allowed is None:
        raise _reject("pdk_source_format_unknown", source=name, format=fmt)
    _require_keys("sources." + name, spec, allowed, tuple(k for k in allowed if k != "note"))
    units_m = spec["units_m"]
    if not isinstance(units_m, dict) or not units_m or any(
            not isinstance(f, (int, float)) or isinstance(f, bool) or not math.isfinite(f) or f <= 0
            for f in units_m.values()):
        raise _reject("pdk_source_units_invalid", source=name)
    _check_source_shape(name, fmt, spec)
    path = root.rstrip("/\\") + "/" + spec["path"]
    if not os.path.isfile(path):
        raise _reject("pdk_source_missing", source=name, path=path)
    with open(path, "rb") as fh:
        data = fh.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != spec["sha256"]:
        raise _reject("pdk_source_sha256_mismatch", source=name, path=path, declared=spec["sha256"], actual=digest)
    params = tuple((k, spec[k]) for k in dict(_PARSE_KEYS)[fmt])
    table = memo.lookup((fmt, digest, params), lambda: _parsed(fmt, data.decode(spec["encoding"]), dict(params)))
    return path, digest, dict(table)


def _check_source_shape(name, fmt, spec):
    """원본 선언 값의 모양: path·encoding 비지 않은 문자열(encoding 은 파이썬 코덱 이름), sha256 = 64자 소문자 hex,
    rule_table_csv 는 section_pattern 이 컴파일되는 정규식이고 열 번호가 0 이상 정수. 위반 -> `pdk_decl_shape`."""
    where = "sources." + name
    for key in ("path", "encoding", "sha256"):
        if not isinstance(spec[key], str) or not spec[key]:
            raise _reject("pdk_decl_shape", where=where + "." + key)
    if not _SHA256.fullmatch(spec["sha256"]):
        raise _reject("pdk_decl_shape", where=where + ".sha256")
    try:
        codecs.lookup(spec["encoding"])
    except LookupError:
        raise _reject("pdk_decl_shape", where=where + ".encoding") from None
    if fmt != _FORMAT_TABLE:
        return
    for key in ("section_column", "id_column", "value_column", "unit_column"):
        column = spec[key]
        if isinstance(column, bool) or not isinstance(column, int) or column < 0:
            raise _reject("pdk_decl_shape", where=where + "." + key)
    if not isinstance(spec["section_pattern"], str):
        raise _reject("pdk_decl_shape", where=where + ".section_pattern")
    try:
        re.compile(spec["section_pattern"])
    except re.error:
        raise _reject("pdk_decl_shape", where=where + ".section_pattern") from None


def _rule(source_name, source, units_m, rule_id):
    path, digest, table = source
    found = table.get(rule_id)
    if not found:
        raise _reject("pdk_rule_missing", source=source_name, rule=rule_id, path=path)
    if len(found) != 1:
        raise _reject("pdk_rule_ambiguous", source=source_name, rule=rule_id,
                      lines=tuple(line for _, _, line in found))
    value_text, unit_text, line = found[0]
    if not _NUMBER.fullmatch(value_text):
        raise _reject("pdk_rule_not_numeric", source=source_name, rule=rule_id, value=value_text, line=line)
    factor = units_m.get(unit_text)
    if factor is None:
        raise _reject("pdk_rule_unit_unknown", source=source_name, rule=rule_id, unit=unit_text, line=line)
    return PdkRule(rule_id, float(value_text) * factor, value_text, unit_text, source_name, path, digest, line)


def _evaluate(node, values, expression):
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, values, expression)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return float(node.value)
    if isinstance(node, ast.Name) and node.id in values:
        return values[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_evaluate(node.operand, values, expression)
    if isinstance(node, ast.BinOp) and type(node.op) in dict(_BINOPS):
        left = _evaluate(node.left, values, expression)
        right = _evaluate(node.right, values, expression)
        if isinstance(node.op, ast.Div) and right == 0:
            raise _reject("pdk_expression_invalid", expression=expression, why="division_by_zero")
        return dict(_BINOPS)[type(node.op)](left, right)
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in dict(_FUNCTIONS)
            and node.args and not node.keywords):
        return dict(_FUNCTIONS)[node.func.id](_evaluate(arg, values, expression) for arg in node.args)
    raise _reject("pdk_expression_invalid", expression=expression, why=type(node).__name__)


def _check_expression_shape(node, expression):
    """식 모양 검사(규칙 이름을 찾기 전에): 수(int·float, bool 아님), 규칙 이름 자리표, 단항 `-`, `+ - * /`,
    `max`·`min` 호출(위치 인자 1개 이상, 키워드 없음)만. 그 밖(다른 함수·키워드·문자열·속성·`**` 등) -> `pdk_expression_invalid`."""
    if isinstance(node, ast.Expression):
        _check_expression_shape(node.body, expression)
        return
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return
    if isinstance(node, ast.Name) and node.id.startswith(_PLACEHOLDER):
        return
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        _check_expression_shape(node.operand, expression)
        return
    if isinstance(node, ast.BinOp) and type(node.op) in dict(_BINOPS):
        _check_expression_shape(node.left, expression)
        _check_expression_shape(node.right, expression)
        return
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in dict(_FUNCTIONS)
            and node.args and not node.keywords):
        for arg in node.args:
            _check_expression_shape(arg, expression)
        return
    raise _reject("pdk_expression_invalid", expression=expression, why=type(node).__name__)


def _references(expression):
    """식의 규칙 이름(등장 순, 중복 없음)과 이름을 자리표로 바꾼 파이썬 식."""
    names = []
    functions = dict(_FUNCTIONS)

    def substitute(match):
        token = match.group(0)
        if token in functions:
            return token
        if token not in names:
            names.append(token)
        return _PLACEHOLDER + str(names.index(token))

    python_text = _REFERENCE.sub(substitute, expression)
    return tuple(names), python_text


def _quantity(name, spec, sources, source_specs):
    _require_keys("quantities." + name, spec, _QUANTITY_KEYS, _QUANTITY_KEYS)
    source_name, expression = spec["source"], spec["expression"]
    for key in ("source", "expression", "basis"):
        if not isinstance(spec[key], str):
            raise _reject("pdk_decl_shape", where="quantities." + name + "." + key)
    if not spec["basis"]:
        raise _reject("pdk_decl_shape", where="quantities." + name + ".basis")
    if source_name not in sources:
        raise _reject("pdk_source_undeclared", quantity=name, source=source_name)
    if not expression.strip():
        raise _reject("pdk_expression_invalid", quantity=name, expression=expression, why="empty")
    rule_names, python_text = _references(expression)
    try:
        tree = ast.parse(python_text, mode="eval")
    except SyntaxError:
        raise _reject("pdk_expression_invalid", quantity=name, expression=expression, why="syntax") from None
    _check_expression_shape(tree, expression)
    if not rule_names:
        raise _reject("pdk_expression_invalid", quantity=name, expression=expression, why="no_rule")
    units_m = source_specs[source_name]["units_m"]
    rules = tuple(_rule(source_name, sources[source_name], units_m, rid) for rid in rule_names)
    values = {_PLACEHOLDER + str(i): rule.value_m for i, rule in enumerate(rules)}
    value = _evaluate(tree, values, expression)
    if not math.isfinite(value) or value < 0:
        raise _reject("pdk_quantity_invalid", quantity=name, expression=expression, value=value)
    return PdkQuantity(name, value, expression, rules, spec["basis"])


def read_pdk_decl(decl_path, memo):
    """선언 파일 `decl_path`(JSON, 스키마 `gmid_pdk_decl/1`)를 읽어 길이마다 규칙 식을 원본 파일 값으로 계산한 `PdkDecl`.

    `memo` = 부르는 쪽 `BoundedLRU`(원본 파일 파싱 결과를 (형식, sha256, 파싱 인자) 키로 둔다)."""
    if not isinstance(memo, BoundedLRU):
        raise TypeError("read_pdk_decl: memo 는 core BoundedLRU 여야 한다(상한은 부르는 쪽이 정한다)")
    if not os.path.isfile(decl_path):
        raise _reject("pdk_decl_missing", path=decl_path)
    with open(decl_path, "rb") as fh:
        raw = fh.read()
    try:
        decl = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise _reject("pdk_decl_json", path=decl_path, error=exc.msg) from None
    _require_keys("decl", decl, _TOP_KEYS, tuple(k for k in _TOP_KEYS if k != "note"))
    if decl["schema"] != _SCHEMA:
        raise _reject("pdk_decl_schema", path=decl_path, schema=decl["schema"])
    source_specs = decl["sources"]
    quantity_specs = decl["quantities"]
    if not isinstance(source_specs, dict) or not source_specs or not isinstance(quantity_specs, dict) \
            or not quantity_specs:
        raise _reject("pdk_decl_shape", where="sources/quantities", path=decl_path)
    root = decl["pdk_root"]
    if not isinstance(root, str) or not root or not isinstance(decl["pdk"], str) or not decl["pdk"]:
        raise _reject("pdk_decl_shape", where="pdk/pdk_root", path=decl_path)
    sources = {name: _load_source(root, name, spec, memo) for name, spec in sorted_items(source_specs)}
    quantities = tuple((name, _quantity(name, spec, sources, source_specs))
                       for name, spec in sorted_items(quantity_specs))
    return PdkDecl(decl["pdk"], decl_path, hashlib.sha256(raw).hexdigest(),
                   tuple((name, path, digest) for name, (path, digest, _) in sorted_items(sources)), quantities)
