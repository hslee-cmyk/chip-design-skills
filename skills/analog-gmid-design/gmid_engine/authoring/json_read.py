"""엔진 입력 JSON 읽기 -- 엔진에서 `json` 파싱은 이 파일에만 둔다 (설계 design_mod3_s1_graph 2.1 `json_read.py`, C00 §6.2).

진입점: `load_json_checked(path, where) -> CheckedJson`.

거부(모두 `SchemaRejectedError`, detail `gate="json_read"`, `hits` = 걸린 곳 전부):
* `bom` -- UTF-8 BOM 으로 시작한다.
* `not_utf8` -- UTF-8 로 해독되지 않는다.
* `json_syntax` -- JSON 문법 오류(첫 오류 위치 하나만 알 수 있다).
* `duplicate_key` -- 같은 객체 안에 같은 키가 두 번 이상(조용히 뒤 값으로 덮어쓰지 않는다). 모든 중복을 모은다.
* `non_finite` -- `NaN`·`Infinity`·`-Infinity` 상수와 float 범위를 넘는 수(`1e999`). 모든 등장을 모은다.
파일을 열 수 없는 OS 오류는 스키마 문제가 아니라서 그대로 전파한다.
"""
import dataclasses
import hashlib
import json
import math

from ._rejection import reject
from .topology_model import SchemaHit

_GATE = "json_read"
_UTF8_BOM = b"\xef\xbb\xbf"


@dataclasses.dataclass(frozen=True)
class CheckedJson:
    """검사를 통과한 JSON 문서. `data` = 파싱 결과(최상위 값), `sha256` = 파일 바이트의 sha256 hex."""

    data: object
    sha256: str


def load_json_checked(path, where):
    """`path` 의 JSON 을 엄격 규칙으로 읽는다. `where` 는 위반 메시지에 붙는 문서 이름(보통 경로 문자열)."""
    with open(path, "rb") as handle:
        raw = handle.read()
    digest = hashlib.sha256(raw).hexdigest()
    if raw.startswith(_UTF8_BOM):
        reject(_GATE, where, (SchemaHit("bom", where, "UTF-8 BOM 으로 시작한다(BOM 없는 UTF-8 만 받는다)"),))
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        reject(_GATE, where, (SchemaHit("not_utf8", where, "UTF-8 해독 실패: " + str(exc)),))
    hits = []

    def pairs_hook(pairs):
        seen = set()
        for key, _value in pairs:
            if key in seen:
                hits.append(SchemaHit("duplicate_key", where, "같은 객체 안에 키 " + repr(key) + " 가 두 번 이상 있다"))
            seen.add(key)
        return dict(pairs)

    def float_hook(token):
        value = float(token)
        if not math.isfinite(value):
            hits.append(SchemaHit("non_finite", where, "유한 범위를 넘는 수 " + token + " (유한 수만 받는다)"))
        return value

    def constant_hook(token):
        hits.append(SchemaHit("non_finite", where, "유한 수가 아닌 상수 " + token + " (유한 수만 받는다)"))
        return None

    try:
        data = json.loads(text, object_pairs_hook=pairs_hook, parse_float=float_hook,
                          parse_constant=constant_hook)
    except json.JSONDecodeError as exc:
        reject(_GATE, where, tuple(hits) + (SchemaHit("json_syntax", where, "JSON 문법 오류: " + str(exc)),))
    if hits:
        reject(_GATE, where, tuple(hits))
    return CheckedJson(data, digest)
