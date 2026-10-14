"""PDK 선언 읽기 -- PDK 마다 데이터 파일 하나가 '길이 이름 -> PDK 규칙 식'을 정하고, 값은 PDK 원본 파일에서 계산한다
(계획 N3.16 'PDK 상수' 행, U-30, WP-03, DEC-80 (i), DEC-93 (5), LY10; 소비자 MOD7 `LayoutPdk`, layout CONTRACT 4.1·4.10).

진입점: `read_pdk_decl`.

* 엔진 코드에는 PDK 이름·규칙 번호·숫자·경로가 없다. 선언 파일(JSON)이 원본 파일(경로·sha256·형식·단위)과
  길이마다 규칙 식(`max(poly.2, licon.1 + 2 * licon.11)` 같은 산술식, 이름 = 원본 파일의 규칙 번호)을 정한다.
* 원본 형식 네 가지(선언의 `format`): `lef_statement`(줄 머리 `KEY 값 ;`, 예 tlef `MANUFACTURINGGRID`),
  `rule_table_csv`(절 머리 행 + 규칙 행 표, 열 번호·절 머리 정규식은 선언이 준다), `spice_model_card`(SPICE `.model`
  블록의 `키 = 값` -- 블록 이름 정규식은 선언이 준다, bin 공통 키와 bin 별 `모델.키`, DEC-91 접합 파라미터),
  `spice_instance_line`(정규식이 고른 SPICE 소자 줄의 `키=값` -- 예 LUT 생성기 DUT 줄의 확산 기하). 규칙 하나가 원본에
  두 번 나오면(모델 카드는 bin 마다 값이 다르면) 모호 -- 식이 그 규칙을 쓸 때만 거부한다.
* 원본 경로 기준은 `pdk_root`(기본) 또는 선언 파일 폴더(원본의 `base` = `"decl_dir"`, PDK 밖 원본).
* 양의 값(`value_m`)은 원본 단위 표(`units_m`)로 환산한 SI 값이다(길이면 m, 면적 m², 접합 용량 F/m² 등 -- 이름이 단위를 적는다).
* 원본 파일은 매 호출 sha256 을 다시 재서 선언값과 대조하고(다르면 거부), 파싱 결과는 부르는 쪽 `BoundedLRU` 에
  (형식, sha256, 파싱 인자) 키로 둔다 -- 같은 파일은 sha256 당 한 번만 파싱한다. 모듈 수준 캐시는 없다(규칙 G).
* 실패는 전부 `SchemaRejectedError(detail={"reason": ...})`(로드 게이트 거부, 사유 키는 core CONTRACT 9절).
* [2026-10-08 U3] 선택 최상위 키 두 개. `mismatch_models`: kind 마다 모델 카드 원본(`spice_model_card`)과 slope 원본(`spice_instance_line`,
  `.param 이름=값` 줄)을 연결해 `.model` 블록마다 (lmin·lmax·wmin·wmax, 변수별 slope 이름·값)의 bin 지도 `PdkMismatchModel` 을 만든다
  (카드가 변수를 `p0 + p_slope_spectre·(slope/sqrt(l·w·mult))` 꼴로 흔드는 식에서 slope 이름을 읽는다 -- 이름은 bin 마다 다를 수 있다).
  `resistor_types`: 후보 저항 종류마다 선언 양(시트 저항·최소 폭·머리 면적)을 가리키고, 본체 Ω당 면적 W²/R□ 가 가장 작은 종류의 양을
  `<selected_as>_sheet_ohm_per_sq`·`_min_w_m`·`_head_area_m2` 양으로 낸다(규칙이지 고정 상수가 아니다, 계획 Q9).
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
_TOP_KEYS = ("mismatch_models", "note", "pdk", "pdk_root", "quantities", "resistor_types", "schema", "sources")
_OPTIONAL_TOP_KEYS = ("mismatch_models", "note", "resistor_types")
_MISMATCH_KEYS = ("model_source", "parameters", "slope_source")
_RESISTOR_KEYS = ("candidates", "selected_as")
_RESISTOR_CANDIDATE_KEYS = ("head_area_m2", "min_w_m", "sheet_ohm_per_sq")
_BOUND_KEYS = ("lmin", "lmax", "wmin", "wmax")
_SLOPE_REF = re.compile(r"([A-Za-z_][A-Za-z0-9_]*_slope[0-9]*)\s*/\s*sqrt")
_QUANTITY_KEYS = ("basis", "expression", "source")
_FORMAT_LEF = "lef_statement"
_FORMAT_TABLE = "rule_table_csv"
_FORMAT_MODEL = "spice_model_card"
_FORMAT_INSTANCE = "spice_instance_line"
_OPTIONAL_SOURCE_KEYS = ("base", "newline", "note")
_SOURCE_KEYS = (
    (_FORMAT_LEF, ("base", "encoding", "format", "newline", "note", "path", "sha256", "units_m")),
    (_FORMAT_TABLE, ("base", "encoding", "format", "id_column", "newline", "note", "path", "section_column",
                     "section_pattern", "sha256", "unit_column", "units_m", "value_column")),
    (_FORMAT_MODEL, ("base", "encoding", "format", "model_pattern", "newline", "note", "path", "sha256", "units_m")),
    (_FORMAT_INSTANCE, ("base", "encoding", "format", "line_pattern", "newline", "note", "path", "sha256",
                        "units_m")),
)
_PARSE_KEYS = (
    (_FORMAT_LEF, ("encoding",)),
    (_FORMAT_TABLE, ("encoding", "id_column", "section_column", "section_pattern", "unit_column", "value_column")),
    (_FORMAT_MODEL, ("encoding", "model_pattern")),
    (_FORMAT_INSTANCE, ("encoding", "line_pattern")),
)
_PATTERN_KEYS = (
    (_FORMAT_LEF, ()),
    (_FORMAT_TABLE, ("section_pattern",)),
    (_FORMAT_MODEL, ("model_pattern",)),
    (_FORMAT_INSTANCE, ("line_pattern",)),
)
# 원본 경로의 기준: pdk_root(기본) 또는 선언 파일이 있는 폴더(PDK 밖 원본 -- 예 LUT 생성기 소스)
_BASE_PDK_ROOT = "pdk_root"
_BASE_DECL_DIR = "decl_dir"
_BASES = (_BASE_PDK_ROOT, _BASE_DECL_DIR)
# 원본 바이트 그대로(기본) 또는 CRLF -> LF 로 맞춘 바이트로 sha256 을 재고 푼다("lf": git 이 체크아웃마다 줄 끝을 바꾸는
# 저장소 안 원본 -- 선언 sha256 = 저장소 blob 내용)
_NEWLINE_LF = "lf"
_CRLF = b"\r\n"
_LF = b"\n"
_MODEL_HEAD = re.compile(r"^\s*\.model\s+(?P<name>\S+)\s+\S+(?P<rest>.*)$", re.IGNORECASE)
_SPICE_PARAM = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\{[^}]*\}|'[^']*'|[^\s(){}=']+)")
_SPICE_VALUE = re.compile(r"(?P<number>[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)(?P<scale>[A-Za-z]*)")
_SPICE_INLINE_COMMENT = re.compile(r"\s[$;].*$")
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
class PdkMismatchBlock:
    """모델 카드 `.model` 블록(bin) 하나: 이름·경계(m)·변수별 slope. `slopes` = ((변수, slope 이름 또는 None, slope 값 또는 None,
    slope 원본 행 또는 None), ...) 선언 순서 -- slope 이름이 None 이면 그 블록이 변수를 흔드는 식(`p0 + p_slope_spectre·slope/sqrt(l·w·mult)`)을
    갖지 않는다. `line` = 블록 경계 `lmin` 의 모델 카드 행."""

    model: str
    lmin_m: float
    lmax_m: float
    wmin_m: float
    wmax_m: float
    slopes: tuple
    line: int


@dataclasses.dataclass(frozen=True)
class PdkMismatchModel:
    """kind 하나의 mismatch 모델 bin 지도: `parameters` = 흔드는 변수(모델 카드 BSIM 파라미터 이름), `blocks` = PdkMismatchBlock
    ((wmin, wmax, lmin, lmax, 이름) 정렬), 원본 sha256(파일 경로는 값에 담지 않는다 -- checkout 마다 달라 S0 값이 checkout 에 묶인다)."""

    kind: str
    parameters: tuple
    blocks: tuple
    model_sha256: str
    slope_sha256: str


@dataclasses.dataclass(frozen=True)
class PdkDecl:
    """선언 파일 하나의 결과. `quantities` = ((이름, PdkQuantity), ...) 이름 정렬, `sources` = ((이름, sha256), ...)(경로 없음).
    [U3] `mismatch_models` = ((kind, PdkMismatchModel), ...) kind 정렬(선언에 없으면 ())."""

    pdk: str
    decl_sha256: str
    sources: tuple
    quantities: tuple
    mismatch_models: tuple = ()

    def quantity(self, name):
        """이름의 PdkQuantity. 선언에 없으면 `SchemaRejectedError(pdk_quantity_undeclared)`."""
        found = dict(self.quantities).get(name)
        if found is None:
            raise _reject("pdk_quantity_undeclared", quantity=name, decl=self.decl_sha256)
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

    def mismatch_model(self, kind):
        """kind 의 PdkMismatchModel. 선언에 없으면 `SchemaRejectedError(pdk_mismatch_undeclared)`."""
        found = dict(self.mismatch_models).get(kind)
        if found is None:
            raise _reject("pdk_mismatch_undeclared", kind=kind, decl=self.decl_sha256)
        return found


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


def _spice_entry(raw, line_no):
    """SPICE 값 글자 하나 -> (값 글자, 배율 글자(소문자), 행). 수 + 배율 글자 꼴이 아니면(`{식}` 등) 값 글자 그대로, 배율 ""
    -- 식이 그 규칙을 쓰면 `pdk_rule_not_numeric` 으로 거부된다."""
    value = _SPICE_VALUE.fullmatch(raw)
    if value is None:
        return raw, "", line_no
    return value.group("number"), value.group("scale").lower(), line_no


def _parse_model_card(text, params):
    """`.model <이름> <형> ...` + `+` 이어진 줄의 `키 = 값` 묶음. 이름이 `model_pattern` 에 맞는 블록만 읽는다.

    규칙 이름(전부 소문자, SPICE 는 대소문자 무관): `<모델 이름>.<키>`(bin 별, 블록마다 하나) 그리고 `<키>`(bin 공통) --
    맞은 블록 전부가 같은 값 글자를 가지면 항목 하나(첫 블록의 행), 블록마다 값이 다르거나 어느 블록에 키가 없으면 항목이
    둘 이상이라 식이 쓸 때 `pdk_rule_ambiguous`(그때는 bin 별 이름을 써야 한다)."""
    model_re = re.compile(params["model_pattern"])
    blocks = []
    current = None
    for line_no, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("*"):
            continue
        body = _SPICE_INLINE_COMMENT.sub("", raw)
        head = _MODEL_HEAD.match(body)
        if head:
            current = None
            if not model_re.fullmatch(head.group("name")):
                continue
            current = (head.group("name").lower(), line_no, {})
            blocks.append(current)
            body = head.group("rest")
        elif stripped.startswith("+"):
            if current is None:
                continue
            body = body.strip()[len("+"):]
        else:
            current = None
            continue
        for key, value in _SPICE_PARAM.findall(body):
            current[2].setdefault(key.lower(), []).append(_spice_entry(value, line_no))
    entries = {}
    for name, _, found in blocks:
        for key, values in found.items():
            entries.setdefault(name + "." + key, []).extend(values)
    for key in sorted({k for _, _, found in blocks for k in found}):
        distinct = {}
        for _, head_line, found in blocks:
            for value_text, unit_text, line_no in found.get(key, (("", "", head_line),)):
                distinct.setdefault((value_text, unit_text), line_no)
        entries[key] = [(value_text, unit_text, line_no) for (value_text, unit_text), line_no in distinct.items()]
    return entries


def _parse_instance_line(text, params):
    """`line_pattern` 이 맞는 줄마다(그룹이 있으면 그룹 1 글자, 없으면 맞은 글자 전체) `키=값` 을 규칙 `키`(소문자)로.
    두 줄 이상에 나온 키는 항목이 둘 이상이라 쓰일 때 `pdk_rule_ambiguous`."""
    line_re = re.compile(params["line_pattern"])
    entries = {}
    for line_no, raw in enumerate(text.splitlines(), start=1):
        found = line_re.search(raw)
        if found is None:
            continue
        body = found.group(1) if line_re.groups else found.group(0)
        for key, value in _SPICE_PARAM.findall(body):
            entries.setdefault(key.lower(), []).append(_spice_entry(value, line_no))
    return entries


def _parse_lef_text(text, params):
    return _parse_lef(text)


_PARSERS = (
    (_FORMAT_LEF, _parse_lef_text),
    (_FORMAT_TABLE, _parse_table),
    (_FORMAT_MODEL, _parse_model_card),
    (_FORMAT_INSTANCE, _parse_instance_line),
)


def _parsed(fmt, text, params):
    entries = dict(_PARSERS)[fmt](text, params)
    return tuple((rid, tuple(found)) for rid, found in sorted_items(entries))


def _load_source(root, decl_dir, name, spec, memo):
    if not isinstance(spec, dict):
        raise _reject("pdk_decl_shape", where="sources." + name)
    fmt = spec.get("format")
    allowed = dict(_SOURCE_KEYS).get(fmt)
    if allowed is None:
        raise _reject("pdk_source_format_unknown", source=name, format=fmt)
    _require_keys("sources." + name, spec, allowed, tuple(k for k in allowed if k not in _OPTIONAL_SOURCE_KEYS))
    units_m = spec["units_m"]
    if not isinstance(units_m, dict) or not units_m or any(
            not isinstance(f, (int, float)) or isinstance(f, bool) or not math.isfinite(f) or f <= 0
            for f in units_m.values()):
        raise _reject("pdk_source_units_invalid", source=name)
    _check_source_shape(name, fmt, spec)
    base = decl_dir if spec.get("base", _BASE_PDK_ROOT) == _BASE_DECL_DIR else root
    path = base.rstrip("/\\") + "/" + spec["path"]
    if not os.path.isfile(path):
        raise _reject("pdk_source_missing", source=name, path=path)
    with open(path, "rb") as fh:
        data = fh.read()
    if spec.get("newline") == _NEWLINE_LF:
        data = data.replace(_CRLF, _LF)
    digest = hashlib.sha256(data).hexdigest()
    if digest != spec["sha256"]:
        raise _reject("pdk_source_sha256_mismatch", source=name, path=path, declared=spec["sha256"], actual=digest)
    params = tuple((k, spec[k]) for k in dict(_PARSE_KEYS)[fmt])
    table = memo.lookup((fmt, digest, params), lambda: _parsed(fmt, data.decode(spec["encoding"]), dict(params)))
    return path, digest, dict(table)


def _check_source_shape(name, fmt, spec):
    """원본 선언 값의 모양: path·encoding 비지 않은 문자열(encoding 은 파이썬 코덱 이름), sha256 = 64자 소문자 hex,
    선택 `base` ∈ {"pdk_root", "decl_dir"}, 선택 `newline` = "lf", 정규식 키(section_pattern·model_pattern·line_pattern)는
    컴파일되는 문자열, rule_table_csv 열 번호는 0 이상 정수. 위반 -> `pdk_decl_shape`."""
    where = "sources." + name
    for key in ("path", "encoding", "sha256"):
        if not isinstance(spec[key], str) or not spec[key]:
            raise _reject("pdk_decl_shape", where=where + "." + key)
    if not _SHA256.fullmatch(spec["sha256"]):
        raise _reject("pdk_decl_shape", where=where + ".sha256")
    if not isinstance(spec.get("base", _BASE_PDK_ROOT), str) or spec.get("base", _BASE_PDK_ROOT) not in _BASES:
        raise _reject("pdk_decl_shape", where=where + ".base")
    if "newline" in spec and spec["newline"] != _NEWLINE_LF:
        raise _reject("pdk_decl_shape", where=where + ".newline")
    try:
        codecs.lookup(spec["encoding"])
    except LookupError:
        raise _reject("pdk_decl_shape", where=where + ".encoding") from None
    if fmt == _FORMAT_TABLE:
        for key in ("section_column", "id_column", "value_column", "unit_column"):
            column = spec[key]
            if isinstance(column, bool) or not isinstance(column, int) or column < 0:
                raise _reject("pdk_decl_shape", where=where + "." + key)
    for key in dict(_PATTERN_KEYS)[fmt]:
        if not isinstance(spec[key], str):
            raise _reject("pdk_decl_shape", where=where + "." + key)
        try:
            re.compile(spec[key])
        except re.error:
            raise _reject("pdk_decl_shape", where=where + "." + key) from None


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
    return PdkRule(rule_id, float(value_text) * factor, value_text, unit_text, source_name, digest, line)


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


def _number(table, rule_id, units_m, path):
    """원본 표 `table` 의 규칙 `rule_id` 하나(모호하면 거부)를 SI 값으로 -> (값, 행)."""
    found = table.get(rule_id)
    if not found:
        raise _reject("pdk_rule_missing", rule=rule_id, path=path)
    if len(found) != 1:
        raise _reject("pdk_rule_ambiguous", rule=rule_id, path=path, lines=tuple(line for _, _, line in found))
    value_text, unit_text, line = found[0]
    if not _NUMBER.fullmatch(value_text):
        raise _reject("pdk_rule_not_numeric", rule=rule_id, value=value_text, line=line)
    factor = units_m.get(unit_text)
    if factor is None:
        raise _reject("pdk_rule_unit_unknown", rule=rule_id, unit=unit_text, line=line)
    return float(value_text) * factor, line


def _mismatch_blocks(kind, item, sources, source_specs):
    """kind 하나의 PdkMismatchModel -- 모델 카드의 `.model` 블록마다 변수 식에서 slope 이름을 읽고 slope 원본에서 값을 읽는다."""
    _require_keys("mismatch_models." + kind, item, _MISMATCH_KEYS, _MISMATCH_KEYS)
    params = item["parameters"]
    if not isinstance(params, list) or not params or any(not isinstance(p, str) or not p for p in params) \
            or len(set(params)) != len(params):
        raise _reject("pdk_decl_shape", where="mismatch_models." + kind + ".parameters")
    for key in ("model_source", "slope_source"):
        if item[key] not in sources:
            raise _reject("pdk_source_undeclared", quantity="mismatch_models." + kind, source=item[key])
    model_path, model_sha, model_table = sources[item["model_source"]]
    slope_path, slope_sha, slope_table = sources[item["slope_source"]]
    model_units = source_specs[item["model_source"]]["units_m"]
    slope_units = source_specs[item["slope_source"]]["units_m"]
    names = sorted(rid[:-len("." + _BOUND_KEYS[0])] for rid in model_table if rid.endswith("." + _BOUND_KEYS[0]))
    if not names:
        raise _reject("pdk_mismatch_no_blocks", kind=kind, path=model_path)
    blocks, used = [], set()
    for name in names:
        bounds = {key: _number(model_table, name + "." + key, model_units, model_path) for key in _BOUND_KEYS}
        slopes = []
        for param in params:
            expr = model_table.get(name + "." + param)
            ref = _SLOPE_REF.search(expr[0][0]) if expr and len(expr) == 1 else None
            if ref is None:
                slopes.append((param, None, None, None))
                continue
            value, line = _number(slope_table, ref.group(1).lower(), slope_units, slope_path)
            slopes.append((param, ref.group(1), value, line))
            used.add(param)
        blocks.append(PdkMismatchBlock(name, bounds["lmin"][0], bounds["lmax"][0], bounds["wmin"][0], bounds["wmax"][0],
                                       tuple(slopes), bounds["lmin"][1]))
    unused = sorted(set(params) - used)
    if unused:
        raise _reject("pdk_mismatch_parameter_unused", kind=kind, parameters=tuple(unused), path=model_path)
    blocks.sort(key=lambda b: (b.wmin_m, b.wmax_m, b.lmin_m, b.lmax_m, b.model))
    return PdkMismatchModel(kind, tuple(params), tuple(blocks), model_sha, slope_sha)


def _mismatch_models(spec, sources, source_specs):
    if spec is None:
        return ()
    if not isinstance(spec, dict) or not spec:
        raise _reject("pdk_decl_shape", where="mismatch_models")
    return tuple((kind, _mismatch_blocks(kind, item, sources, source_specs)) for kind, item in sorted_items(spec))


def _resistor_quantities(spec, quantities):
    """`resistor_types` 선언 -> 본체 Ω당 면적(W_min²/R□)이 가장 작은 후보의 양을 `<selected_as>_...` 이름으로 낸 PdkQuantity tuple.
    동률이면 후보 이름 순. 후보가 가리키는 양이 선언에 없으면 `pdk_quantity_undeclared`."""
    if spec is None:
        return ()
    _require_keys("resistor_types", spec, _RESISTOR_KEYS, _RESISTOR_KEYS)
    candidates = spec["candidates"]
    if not isinstance(spec["selected_as"], str) or not spec["selected_as"] or not isinstance(candidates, dict) or not candidates:
        raise _reject("pdk_decl_shape", where="resistor_types")
    table = dict(quantities)
    ranked = []
    for name, item in sorted_items(candidates):
        _require_keys("resistor_types.candidates." + name, item, _RESISTOR_CANDIDATE_KEYS, _RESISTOR_CANDIDATE_KEYS)
        picked = {}
        for key in _RESISTOR_CANDIDATE_KEYS:
            if item[key] not in table:
                raise _reject("pdk_quantity_undeclared", quantity=item[key], where="resistor_types.candidates." + name)
            picked[key] = table[item[key]]
        sheet, width = picked["sheet_ohm_per_sq"].value_m, picked["min_w_m"].value_m
        if not sheet > 0:
            raise _reject("pdk_quantity_invalid", quantity=item["sheet_ohm_per_sq"], value=sheet)
        ranked.append((width * width / sheet, name, picked))
    ranked.sort(key=lambda r: (r[0], r[1]))
    area_per_ohm, chosen, picked = ranked[0]
    basis = ("저항 종류 선택 규칙: 본체 Ω당 면적 W_min²/R□ 가 가장 작은 후보(동률은 이름 순). 후보 = " +
             ", ".join("%s (%.6g m²/Ω)" % (n, a) for a, n, _ in ranked) + " -> " + chosen)
    out = []
    for key in _RESISTOR_CANDIDATE_KEYS:
        quantity = picked[key]
        out.append((spec["selected_as"] + "_" + key,
                    PdkQuantity(spec["selected_as"] + "_" + key, quantity.value_m, "select_min_area_per_ohm(" + chosen + "." + key + ")",
                                quantity.rules, basis + " | " + quantity.basis)))
    return tuple(out)


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
    _require_keys("decl", decl, _TOP_KEYS, tuple(k for k in _TOP_KEYS if k not in _OPTIONAL_TOP_KEYS))
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
    decl_dir = os.path.dirname(os.path.abspath(decl_path))
    sources = {name: _load_source(root, decl_dir, name, spec, memo) for name, spec in sorted_items(source_specs)}
    quantities = tuple((name, _quantity(name, spec, sources, source_specs))
                       for name, spec in sorted_items(quantity_specs))
    selected = _resistor_quantities(decl.get("resistor_types"), quantities)
    clash = sorted(set(dict(quantities)) & set(dict(selected)))
    if clash:
        raise _reject("pdk_quantity_duplicate", quantities=tuple(clash))
    quantities = tuple(sorted(quantities + selected, key=lambda item: item[0]))
    return PdkDecl(decl["pdk"], hashlib.sha256(raw).hexdigest(),
                   tuple((name, digest) for name, (_path, digest, _) in sorted_items(sources)), quantities,
                   _mismatch_models(decl.get("mismatch_models"), sources, source_specs))
