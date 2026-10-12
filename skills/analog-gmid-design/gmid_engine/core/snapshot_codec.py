"""S0 수준 graph 스냅샷의 디스크 영속화 -- 타입 있는 gzip JSON 코덱, 검증, 원자적 쓰기, 옛 키 정리
(설계 40 §2.4.1 표 (d), §2.4.3, §2.4.12 Q1·Q2, §3.10.11 U-68; 계획 NFR-2·DEC-83·N3.3·N3.5).

진입점: `S0SnapshotStore(directory, code_fp)`.

* 키 = 호출자가 준 S0 입력 지문 `inputs`(문자열 -> 64자 hex 문자열 또는 None 의 매핑: S0 전체 지문 구성요소(P N3.3 v6.4)와
  `structure.json` 사실 지문) + 엔진 코드 지문 `code_fp`(`engine_code_fp()`, 키 이름 `KEY_CODE_FP`). 파일 이름 = `<fp_of(키)>.json.gz`.
  키가 다르면 없는 것으로 본다(SC-d) -- 부분 재사용은 하지 않는다.
* `load(inputs) -> (GraphSnapshot | None, outcome)`: outcome ∈ {`OUTCOME_HIT`, `OUTCOME_MISS`, `OUTCOME_CORRUPT`}. 파일이 없으면 miss.
  읽은 뒤 본문 sha256(`body_sha256`), 형식 판(`schema_version`), 저장된 키, writer 권한표 대조, 스냅샷 `fp` 재계산을 확인한다 --
  하나라도 틀리면(디코더가 등록부 밖 타입을 만난 경우 포함) 손상(corrupt, RuntimeWarning)이고 스냅샷을 돌려주지 않는다.
* `save(inputs, snapshot) -> 경로 | None`: 키 파일이 이미 있고 검증을 통과하면 쓰지 않는다. 아니면(없음·손상) 같은 폴더의 임시 파일에
  쓰고 fsync 뒤 `os.replace` 로 교체한다(원자적, 손상 파일은 같은 키로 교체된다). 쓰기 실패는 RuntimeWarning 뒤 None(계산 결과는 그대로).
  쓴 뒤 1회 옛 파일 정리(U-68, 아래).
* 형식: gzip(mtime 0) JSON 하나 `{schema_version, key{...}, writers[[kind, field, writer]...], block_versions{writer: 입력 버전},
  records[{kind, key, fields{name: {value, writer, input_version, write_count}}}], fp, body_sha256}`. `body_sha256` = 그 칸을 뺀
  문서의 정준 JSON 바이트(키 정렬·구분자 고정·ASCII) sha256. 값은 타입 있는 인코딩이다: None·bool·int·str 는 JSON 그대로,
  float = `{"__type__": "float", "hex": float.hex}`, bytes = `{"__type__": "bytes", "hex": ...}`, tuple = `{"__type__": "tuple", "items": [...]}`,
  frozenset = `{"__type__": "frozenset", "items": [...]}`(원소 `fp_of` 정렬 = 정준 순서), frozen dataclass =
  `{"__type__": "<모듈>.<클래스>", "fields": {이름: 값}}`(init 필드만 -- 디코더가 생성자로 다시 만든다). dataclass 는 타입 등록부
  (`type_registry`)에 있는 것만 인코드·디코드한다(목록 밖은 인코드 `TypeError`, 디코드 = 손상). 옛 S3 `_plain`(repr 직렬화)은 쓰지 않는다.
* 위치: `S0SnapshotStore.default(code_fp)` = `gmid_engine/.s0_snapshot/`(저장소 `.gitignore` 등록, P N3.5).
* 옛 파일 정리(U-68, 쓰기 시점 1회): 폴더의 `<64 hex>.json.gz` 형식 파일 중 저장된 엔진 코드 지문이 이 저장소·`git worktree list` 의
  모든 worktree 의 현재 엔진 코드 지문 어느 것과도 다른 파일만 지운다(그 키는 어떤 checkout 으로도 만들 수 없다). 방금 쓴 파일·심볼릭
  링크·폴더 밖·형식이 다르거나 읽을 수 없는 파일은 건드리지 않고, worktree 나열·지문 계산이 실패하면 아무것도 지우지 않는다.
  저장된 코드 지문이 모두 현재 것과 같으면 git 을 부르지 않고, worktree 지문은 남은 후보가 모두 재현될 때까지만 잰다(실측: worktree 104개
  전부 재면 약 80 s). 입력 파일(topology·spec·LUT·PDK 선언) 쪽 재현 가능성은 보지 않는다
  (정규화 지문은 그 checkout 의 엔진 코드로만 다시 만들 수 있다) -- 지우는 쪽으로 틀리지 않는다.
"""
import dataclasses
import gzip
import hashlib
import json
import os
import re
import subprocess
import tempfile
import warnings
import zlib
from collections.abc import Mapping
from pathlib import Path

from .engine_code_fp import engine_code_fp
from .field_value import FieldValue
from .fingerprint import fp_of
from .graph_record import GraphRecord
from .graph_snapshot import GraphSnapshot
from .type_registry import type_registry
from .writer_error import WriterPermissionError
from .writer_table import WriterTable

SCHEMA_VERSION = 1
SNAPSHOT_DIR_NAME = ".s0_snapshot"
FILE_SUFFIX = ".json.gz"
KEY_CODE_FP = "engine_code_fp"
OUTCOME_HIT = "hit"
OUTCOME_MISS = "miss"
OUTCOME_CORRUPT = "corrupt"

_TYPE = "__type__"
_ITEMS = "items"
_FIELDS = "fields"
_HEX = "hex"
_T_FLOAT = "float"
_T_BYTES = "bytes"
_T_TUPLE = "tuple"
_T_FROZENSET = "frozenset"
_BODY_SHA = "body_sha256"
_FILE_NAME = re.compile(r"[0-9a-f]{64}" + re.escape(FILE_SUFFIX))
# 손상으로 보는 예외: 파일·gzip·JSON·형식 위반과, 깨진 문서로 레코드·필드 값·권한표를 다시 만들 때 나는 예외(모양이 틀린 칸의 속성 접근 포함)
_READ_ERRORS = (OSError, EOFError, zlib.error, gzip.BadGzipFile, UnicodeDecodeError, ValueError, TypeError, KeyError, AttributeError,
                WriterPermissionError)


def _encode(value):
    kind = type(value)
    if value is None or kind in (bool, int, str):
        return value
    if kind is float:
        return {_TYPE: _T_FLOAT, _HEX: float.hex(value)}
    if kind is bytes:
        return {_TYPE: _T_BYTES, _HEX: value.hex()}
    if kind is tuple:
        return {_TYPE: _T_TUPLE, _ITEMS: [_encode(item) for item in value]}
    if kind is frozenset:
        return {_TYPE: _T_FROZENSET, _ITEMS: [_encode(item) for item in sorted(value, key=fp_of)]}
    try:
        name = type_registry().name_of(kind)
    except KeyError:
        raise TypeError("snapshot_codec: 인코드할 수 없는 값 형식 " + kind.__qualname__
                        + " (스칼라·tuple·frozenset·타입 등록부에 올린 frozen dataclass 만)") from None
    return {_TYPE: name, _FIELDS: {f.name: _encode(getattr(value, f.name)) for f in dataclasses.fields(value) if f.init}}


def _decode(obj):
    kind = type(obj)
    if obj is None or kind in (bool, int, str):
        return obj
    if kind is not dict:
        raise TypeError("snapshot_codec: 타입 없는 JSON 값 " + kind.__name__)
    tag = obj[_TYPE]
    if tag == _T_FLOAT:
        return float.fromhex(obj[_HEX])
    if tag == _T_BYTES:
        return bytes.fromhex(obj[_HEX])
    if tag == _T_TUPLE:
        return tuple(_decode(item) for item in obj[_ITEMS])
    if tag == _T_FROZENSET:
        return frozenset(_decode(item) for item in obj[_ITEMS])
    cls = type_registry().lookup(tag)
    fields = obj[_FIELDS]
    names = {f.name for f in dataclasses.fields(cls) if f.init}
    if type(fields) is not dict or set(fields) != names:
        raise ValueError("snapshot_codec: " + tag + " 필드가 선언과 다르다")
    return cls(**{name: _decode(item) for name, item in fields.items()})


def _canonical_json(doc):
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _document(key, snapshot):
    records = []
    for kind in snapshot.kinds():
        for record_key in snapshot.keys(kind):
            record = snapshot.record(kind, record_key)
            records.append({"kind": kind, "key": record_key, _FIELDS: {
                name: {"value": _encode(fv.value), "writer": fv.writer, "input_version": fv.input_version,
                       "write_count": fv.write_count} for name, fv in record.fields}})
    doc = {"schema_version": SCHEMA_VERSION, "key": dict(key),
           "writers": [[kind, field, writer] for (kind, field), writer in snapshot.writers.entries],
           "block_versions": dict(snapshot.block_versions), "records": records, "fp": snapshot.fp}
    doc[_BODY_SHA] = hashlib.sha256(_canonical_json(doc)).hexdigest()
    return doc


def _snapshot_of(doc, key):
    """검증을 통과한 문서의 GraphSnapshot. 형식·키·권한표·지문 위반은 ValueError(타입 위반은 TypeError·KeyError)."""
    stored_sha = doc.pop(_BODY_SHA)
    if hashlib.sha256(_canonical_json(doc)).hexdigest() != stored_sha:
        raise ValueError("snapshot_codec: body_sha256 불일치")
    if doc["schema_version"] != SCHEMA_VERSION or doc["key"] != dict(key):
        raise ValueError("snapshot_codec: 형식 판 또는 저장된 키가 다르다")
    writers = WriterTable(tuple(tuple(entry) for entry in doc["writers"]))
    tables = {}
    for row in doc["records"]:
        kind, record_key = row["kind"], row["key"]
        fields = []
        for name, cell in row[_FIELDS].items():
            if writers.writer_of(kind, name) != cell["writer"]:
                raise ValueError("snapshot_codec: 권한표와 다른 writer " + repr((kind, name, cell["writer"])))
            fields.append((name, FieldValue(_decode(cell["value"]), cell["writer"], cell["input_version"], cell["write_count"])))
        tables.setdefault(kind, {})[record_key] = GraphRecord(kind, record_key, tuple(fields))
    versions = doc["block_versions"]
    if any(not writers.fields_of(writer) or type(version) is not str for writer, version in versions.items()):
        raise ValueError("snapshot_codec: 권한표 밖 writer 의 block_version")
    snapshot = GraphSnapshot(writers, tables, versions)
    if snapshot.fp != doc["fp"]:
        raise ValueError("snapshot_codec: 스냅샷 fp 불일치")
    return snapshot


def _read_doc(path):
    with gzip.open(path, "rb") as fh:
        doc = json.loads(fh.read().decode("ascii"))
    if type(doc) is not dict:
        raise ValueError("snapshot_codec: 문서가 객체가 아니다")
    return doc


def _git(directory, *args):
    done = subprocess.run(("git", "-C", str(directory)) + args, capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        raise OSError("git failed: " + done.stderr.strip())
    return done.stdout


def _unreproducible(engine_root, candidates):
    """`candidates`(저장된 코드 지문 집합) 중 이 저장소와 `git worktree list` 의 어느 worktree 의 같은 상대 경로 엔진 폴더 현재 지문과도 같지 않은 것.
    worktree 를 나열 순서대로 하나씩 재고, 남은 후보가 없어지면 멈춘다(모두 재현 가능 = 지울 것 없음). 실패는 OSError·ValueError·SubprocessError."""
    top = Path(_git(engine_root, "rev-parse", "--show-toplevel").strip()).resolve()
    rel = engine_root.resolve().relative_to(top)
    roots = [line[len("worktree "):] for line in _git(engine_root, "worktree", "list", "--porcelain").splitlines()
             if line.startswith("worktree ")]
    left = set(candidates)
    for root in roots:
        left.discard(engine_code_fp(Path(root) / rel))
        if not left:
            break
    return left


@dataclasses.dataclass(frozen=True)
class S0SnapshotStore:
    """S0 수준 스냅샷 저장소. `directory`: 저장 폴더(없으면 쓸 때 만든다). `code_fp`: 이 실행의 엔진 코드 지문(`engine_code_fp()`)."""

    directory: str
    code_fp: str

    def __post_init__(self):
        if not isinstance(self.directory, str) or not self.directory:
            raise ValueError("S0SnapshotStore.directory 는 비어 있지 않은 경로 문자열이어야 한다")
        if not isinstance(self.code_fp, str) or not self.code_fp:
            raise ValueError("S0SnapshotStore.code_fp 는 비어 있지 않은 문자열(engine_code_fp())이어야 한다")

    @classmethod
    def default(cls, code_fp):
        """`gmid_engine/.s0_snapshot/`(`.gitignore` 등록) 저장소."""
        return cls(str(Path(__file__).resolve().parents[1] / SNAPSHOT_DIR_NAME), code_fp)

    def key_of(self, inputs):
        """전체 키 dict = `inputs` + {`KEY_CODE_FP`: code_fp}. 이름은 비어 있지 않은 문자열, 값은 문자열 또는 None."""
        if not isinstance(inputs, Mapping) or KEY_CODE_FP in inputs:
            raise TypeError("S0SnapshotStore: inputs 는 " + KEY_CODE_FP + " 를 뺀 {이름: 지문 문자열 | None} 매핑이어야 한다")
        for name, value in inputs.items():
            if not isinstance(name, str) or not name or not (value is None or isinstance(value, str)):
                raise TypeError("S0SnapshotStore: inputs 항목 " + repr((name, value)) + " 형식 위반")
        key = dict(sorted(inputs.items()))
        key[KEY_CODE_FP] = self.code_fp
        return key

    def path_of(self, inputs):
        """키 파일 경로(`<fp_of(키)>.json.gz`)."""
        return os.path.join(self.directory, fp_of(self.key_of(inputs)) + FILE_SUFFIX)

    def _load_path(self, path, key):
        try:
            return _snapshot_of(_read_doc(path), key), OUTCOME_HIT
        except FileNotFoundError:
            return None, OUTCOME_MISS
        except _READ_ERRORS as exc:
            warnings.warn("S0SnapshotStore: 손상된 스냅샷 파일 -- 다시 계산해 같은 키로 교체한다: %s (%s)" % (path, exc), RuntimeWarning)
            return None, OUTCOME_CORRUPT

    def load(self, inputs):
        """(GraphSnapshot | None, outcome)."""
        key = self.key_of(inputs)
        return self._load_path(self.path_of(inputs), key)

    def save(self, inputs, snapshot):
        """`snapshot`(GraphSnapshot)을 키 파일로 쓴다. 이미 검증되는 파일이 있으면 쓰지 않는다. 쓴 경로 또는 None."""
        if not isinstance(snapshot, GraphSnapshot):
            raise TypeError("S0SnapshotStore.save: snapshot 은 GraphSnapshot 이어야 한다")
        key = self.key_of(inputs)
        path = self.path_of(inputs)
        if os.path.isfile(path) and self._load_path(path, key)[1] == OUTCOME_HIT:
            return path
        blob = gzip.compress(_canonical_json(_document(key, snapshot)), mtime=0)   # 인코드 실패(TypeError)는 전파 -- 등록부 밖 값
        tmp = None
        try:
            os.makedirs(self.directory, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=self.directory, prefix=os.path.basename(path) + ".", suffix=".tmp")
            with os.fdopen(fd, "wb") as fh:
                fh.write(blob)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
            tmp = None
        except OSError as exc:
            warnings.warn("S0SnapshotStore: 쓰지 못했다 %s (%s)" % (path, exc), RuntimeWarning)
            return None
        finally:
            if tmp is not None:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
        self._cleanup(path)
        return path

    def _cleanup(self, keep_path):
        """U-68: 어떤 checkout 의 엔진 코드로도 만들 수 없는 키(저장된 코드 지문이 어느 worktree 의 현재 지문과도 다름)의 파일만 지운다."""
        try:
            names = sorted(os.listdir(self.directory))
        except OSError:
            return
        stale = []
        for name in names:
            path = os.path.join(self.directory, name)
            if not _FILE_NAME.fullmatch(name) or path == keep_path or os.path.islink(path) or not os.path.isfile(path):
                continue
            try:
                stored = _read_doc(path)["key"][KEY_CODE_FP]
            except _READ_ERRORS:
                continue
            if isinstance(stored, str) and stored != self.code_fp:
                stale.append((path, stored))
        if not stale:
            return
        try:
            doomed = _unreproducible(Path(__file__).resolve().parents[1], {stored for _, stored in stale})
        except (OSError, ValueError, subprocess.SubprocessError):
            return
        for path, stored in stale:
            if stored not in doomed:
                continue
            try:
                os.unlink(path)
            except OSError:
                continue
