"""S0 수준 graph 스냅샷의 디스크 영속화 -- 타입 있는 gzip JSON 코덱, 검증, 원자적 쓰기, 옛 키 정리
(설계 40 §2.4.1 표 (d), §2.4.3, §2.4.12 Q1·Q2, §3.10.11 U-68; 계획 NFR-2·DEC-83·N3.3·N3.5).

진입점: `S0SnapshotStore(directory, code_fp)`.

* 키 = 호출자가 준 S0 입력 지문 `inputs`(문자열 -> 문자열 또는 None 의 매핑: S0 전체 지문 구성요소(P N3.3 v6.4)와 `structure.json` 사실 지문)
  + 입력 파일 `sources`({역할: (경로 | None, 원본 바이트 sha256 | None)} -- topology·spec·structure·LUT·PDK 선언 파일, 사용자 결정 U-68 원문 범위)
  + 엔진 코드 지문 `code_fp`(`engine_code_fp()`, 키 이름 `KEY_CODE_FP`). 입력 파일마다 키에 `source.<역할>.path`(저장소 안이면
  `repo:<저장소 기준 posix 상대 경로>`, 밖이면 `abs:<절대 posix 경로>`, 경로 없음이면 None)와 `source.<역할>.sha256`(파일이 없으면 None)을 넣는다.
  저장소 = 엔진 폴더 위로 처음 `.git` 이 있는 폴더(worktree 포함). 파일 이름 = `<fp_of(키)>.json.gz`. 키가 다르면 없는 것으로 본다(SC-d).
  정규화 지문(topology 연결 지문 등)은 원본 바이트와 엔진 코드의 함수이므로, 원본 sha·위치·엔진 코드 지문이 같으면 같은 키가 다시 만들어진다
  -- 아래 정리가 이것으로 재현 가능성을 엔진 실행 없이 판정한다. 저장된 키가 곧 스냅샷 메타다(문서 `key`).
* `load(inputs, sources) -> (GraphSnapshot | None, outcome)`: outcome ∈ {`OUTCOME_HIT`, `OUTCOME_MISS`, `OUTCOME_CORRUPT`}. 파일이 없으면 miss.
  읽은 뒤 본문 sha256(`body_sha256`), 형식 판(`schema_version`), 저장된 키, writer 권한표 대조, 스냅샷 `fp` 재계산을 확인한다 --
  하나라도 틀리면(디코더가 등록부 밖 타입을 만난 경우 포함) 손상(corrupt, RuntimeWarning)이고 스냅샷을 돌려주지 않는다.
* `save(inputs, sources, snapshot) -> 경로 | None`: 키 파일이 이미 있고 검증을 통과하면 쓰지 않는다. 아니면(없음·손상) 같은 폴더의 임시 파일에
  쓰고 fsync 뒤 `os.replace` 로 교체한다(원자적, 손상 파일은 같은 키로 교체된다). 쓰기 실패는 RuntimeWarning 뒤 None(계산 결과는 그대로).
  쓴 뒤 옛 파일 정리(U-68, 아래 -- 프로세스의 첫 쓰기에서만).
* 형식: gzip(mtime 0) JSON 하나 `{schema_version, key{...}, writers[[kind, field, writer]...], block_versions{writer: 입력 버전},
  records[{kind, key, fields{name: {value, writer, input_version, write_count}}}], fp, body_sha256}`. `body_sha256` = 그 칸을 뺀
  문서의 정준 JSON 바이트(키 정렬·구분자 고정·ASCII) sha256. 값은 타입 있는 인코딩이다: None·bool·int·str 는 JSON 그대로,
  float = `{"__type__": "float", "hex": float.hex}`, bytes = `{"__type__": "bytes", "hex": ...}`, tuple = `{"__type__": "tuple", "items": [...]}`,
  frozenset = `{"__type__": "frozenset", "items": [...]}`(원소 `fp_of` 정렬 = 정준 순서), frozen dataclass =
  `{"__type__": "<모듈>.<클래스>", "fields": {이름: 값}}`(init 필드만 -- 디코더가 생성자로 다시 만든다). dataclass 는 타입 등록부
  (`type_registry`)에 있는 것만 인코드·디코드한다(목록 밖은 인코드 `TypeError`, 디코드 = 손상). 옛 S3 `_plain`(repr 직렬화)은 쓰지 않는다.
* 위치: `S0SnapshotStore.default(code_fp)` = 환경 변수 `GMID_S0_SNAPSHOT_DIR`(`SNAPSHOT_DIR_ENV`)가 비어 있지 않으면 그 폴더, 아니면
  `gmid_engine/.s0_snapshot/`(저장소 `.gitignore` 등록, P N3.5). 환경 변수 이름은 LUT 파생표 캐시 `GMID_LUT_TABLE_CACHE_DIR` 관례를 따른다
  (test 격리 수단 -- 기본 위치는 바뀌지 않는다).
* 옛 파일 정리(U-68, 쓰기 시점 1회 = **프로세스의 첫 쓰기 1회**): 승인된 tol_V 캐시 정리('첫 쓰기 때만')와 같은 방식이다. 프로세스에서 처음으로
  파일을 실제로 쓴 `save` 만 정리하고(적중·이미 있는 키는 쓰기가 아니다), 같은 프로세스의 다음 쓰기는 정리하지 않는다(실측: 엔진 코드가 바뀐 뒤
  쓰기마다 worktree ~100개 지문을 다시 재 test 하나가 102 s). 표시는 모듈 수준 `threading.Event` 하나(`_CLEANUP_STARTED`, 값 캐시가 아닌 실행 계수
  성격의 1비트 -- 정리를 시작하기 전에 켠다: 정리가 실패해도 그 프로세스에서 다시 시도하지 않는다). 폴더의 `<64 hex>.json.gz` 형식 파일(방금 쓴 파일·심볼릭 링크·폴더 밖·형식이 다르거나 읽을 수 없는 파일 제외)
  중 **어떤 checkout 으로도 그 키를 만들 수 없는 것**만 지운다. 판정(엔진 실행 없음): 키의 `abs:` 입력 파일은 지금 그 경로 파일의 원본 sha 가
  저장된 값과 같아야 하고(없음 = None), 이 저장소·`git worktree list` 의 어느 worktree W 에서 `W/<엔진 상대 경로>` 의 엔진 코드 지문이 키의
  것과 같고 `repo:` 입력 파일마다 `W/<상대 경로>` 의 원본 sha 가 저장된 값과 같으면(없음 = None) 재현 가능 -- 보존한다. worktree 는 이 저장소부터
  하나씩 재고 남은 후보가 없어지면 멈춘다(실측: worktree 104개 전부 재면 약 80 s). 정리 중 잰 파일 sha 는 그 정리 한 번 안에서만 다시 쓰고,
  worktree 나열이 실패하면 아무것도 지우지 않는다.
"""
import dataclasses
import gzip
import hashlib
import json
import os
import re
import subprocess
import tempfile
import threading
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
SNAPSHOT_DIR_ENV = "GMID_S0_SNAPSHOT_DIR"
FILE_SUFFIX = ".json.gz"
KEY_CODE_FP = "engine_code_fp"
SOURCE_PREFIX = "source."
SOURCE_PATH = ".path"
SOURCE_SHA = ".sha256"
LOCATOR_REPO = "repo:"
LOCATOR_ABS = "abs:"
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
_GIT_MARK = ".git"
_WORKTREE_LINE = "worktree "
_SOURCE_PAIR = ("path", "sha256")
_FILE_NAME = re.compile(r"[0-9a-f]{64}" + re.escape(FILE_SUFFIX))
# U-68 정리 '프로세스의 첫 쓰기 1회' 표시(모듈 머리 '옛 파일 정리') -- 켜지면 그 프로세스의 다음 쓰기는 정리하지 않는다
_CLEANUP_STARTED = threading.Event()
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


def _engine_root():
    return Path(__file__).resolve().parents[1]


def _repo_top(engine_root):
    """엔진 폴더 위로 처음 `.git`(폴더 또는 worktree 의 파일)이 있는 폴더, 없으면 None."""
    for folder in (engine_root,) + tuple(engine_root.parents):
        if (folder / _GIT_MARK).exists():
            return folder
    return None


def _locator(path, top):
    """입력 파일 경로 -> `repo:<상대 posix>` | `abs:<절대 posix>`."""
    full = Path(path).resolve()
    if top is not None and full.is_relative_to(top):
        return LOCATOR_REPO + full.relative_to(top).as_posix()
    return LOCATOR_ABS + full.as_posix()


def _file_sha(path, seen):
    """원본 바이트 sha256(없으면 None). `seen` = 이 정리 한 번의 경로별 결과(같은 파일을 다시 읽지 않는다)."""
    if path not in seen:
        if os.path.isfile(path):
            with open(path, "rb") as fh:
                seen[path] = hashlib.file_digest(fh, "sha256").hexdigest()
        else:
            seen[path] = None
    return seen[path]


def _sources_of(key):
    """키의 ((locator, sha256 | None), ...) -- 경로가 있는 입력 파일만."""
    out = []
    for name, value in key.items():
        if name.startswith(SOURCE_PREFIX) and name.endswith(SOURCE_PATH) and value is not None:
            out.append((value, key[name[:-len(SOURCE_PATH)] + SOURCE_SHA]))
    return tuple(out)


def _well_formed(key):
    """정리가 읽을 수 있는 키인가(코드 지문 문자열, 입력 파일 칸이 `repo:`·`abs:` 위치와 문자열|None sha)."""
    return (type(key) is dict and isinstance(key.get(KEY_CODE_FP), str)
            and all(isinstance(loc, str) and loc.startswith((LOCATOR_REPO, LOCATOR_ABS)) and (sha is None or isinstance(sha, str))
                    for loc, sha in _sources_of(key)))


def _unreproducible(engine_root, current_key, candidates):
    """`candidates`((파일 경로, 저장된 키), ...) 중 어떤 checkout 으로도 키를 만들 수 없는 것의 파일 경로 집합(모듈 머리 '옛 파일 정리').
    `current_key` = 방금 쓴 파일의 키 -- 이 실행이 잰 입력 파일 sha 와 엔진 코드 지문을 다시 재지 않고 쓴다.
    실패는 OSError·ValueError·SubprocessError(호출자는 아무것도 지우지 않는다)."""
    top = _repo_top(engine_root)
    if top is None:
        raise OSError("snapshot_codec: 엔진 폴더가 git 저장소 안에 없다")
    rel = engine_root.relative_to(top)
    current_code_fp = current_key[KEY_CODE_FP]
    seen = {}
    for loc, sha in _sources_of(current_key):
        if loc.startswith(LOCATOR_ABS):
            seen[loc[len(LOCATOR_ABS):]] = sha
        else:
            seen[str(top / loc[len(LOCATOR_REPO):])] = sha
    doomed, left = set(), []
    for path, key in candidates:
        sources = _sources_of(key)
        outside = [(loc[len(LOCATOR_ABS):], sha) for loc, sha in sources if loc.startswith(LOCATOR_ABS)]
        if any(_file_sha(p, seen) != sha for p, sha in outside):
            doomed.add(path)
        else:
            inside = [(loc[len(LOCATOR_REPO):], sha) for loc, sha in sources if loc.startswith(LOCATOR_REPO)]
            left.append((path, key[KEY_CODE_FP], inside))
    if not left:
        return doomed
    listed = [Path(line[len(_WORKTREE_LINE):]).resolve()
              for line in _git(engine_root, "worktree", "list", "--porcelain").splitlines() if line.startswith(_WORKTREE_LINE)]
    for root in [top] + [r for r in listed if r != top]:
        code = current_code_fp if root == top else engine_code_fp(root / rel)
        left = [(path, stored, inside) for path, stored, inside in left
                if not (stored == code and all(_file_sha(str(root / r), seen) == sha for r, sha in inside))]
        if not left:
            break
    return doomed | {path for path, _, _ in left}


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
        """환경 변수 `SNAPSHOT_DIR_ENV` 가 비어 있지 않으면 그 폴더, 아니면 `gmid_engine/.s0_snapshot/`(`.gitignore` 등록) 저장소."""
        return cls(os.environ.get(SNAPSHOT_DIR_ENV) or str(_engine_root() / SNAPSHOT_DIR_NAME), code_fp)

    def key_of(self, inputs, sources):
        """전체 키 dict = `inputs` + 입력 파일 칸(`source.<역할>.path`·`.sha256`) + {`KEY_CODE_FP`: code_fp}.
        `inputs`: {비어 있지 않은 이름(`KEY_CODE_FP`·`source.` 접두 금지): 문자열 | None}. `sources`: {비어 있지 않은 역할: (경로 | None, sha256 | None)}
        -- 경로가 None 이면 sha256 도 None. 위반은 `TypeError`."""
        if not isinstance(inputs, Mapping) or not isinstance(sources, Mapping):
            raise TypeError("S0SnapshotStore: inputs·sources 는 매핑이어야 한다")
        key = {}
        for name, value in inputs.items():
            if (not isinstance(name, str) or not name or name == KEY_CODE_FP or name.startswith(SOURCE_PREFIX)
                    or not (value is None or isinstance(value, str))):
                raise TypeError("S0SnapshotStore: inputs 항목 " + repr((name, value)) + " 형식 위반")
            key[name] = value
        top = _repo_top(_engine_root())
        for role, pair in sources.items():
            if not isinstance(role, str) or not role or not isinstance(pair, tuple) or len(pair) != len(_SOURCE_PAIR):
                raise TypeError("S0SnapshotStore: sources 항목 " + repr((role, pair)) + " 은 역할: (경로, sha256) 이어야 한다")
            path, sha = pair
            if (path is None and sha is not None) or not (sha is None or isinstance(sha, str)):
                raise TypeError("S0SnapshotStore: sources 항목 " + repr((role, pair)) + " 형식 위반")
            key[SOURCE_PREFIX + role + SOURCE_PATH] = None if path is None else _locator(path, top)
            key[SOURCE_PREFIX + role + SOURCE_SHA] = sha
        key = dict(sorted(key.items()))
        key[KEY_CODE_FP] = self.code_fp
        return key

    def _path_for(self, key):
        return os.path.join(self.directory, fp_of(key) + FILE_SUFFIX)

    def path_of(self, inputs, sources):
        """키 파일 경로(`<fp_of(키)>.json.gz`)."""
        return self._path_for(self.key_of(inputs, sources))

    def _load_path(self, path, key):
        try:
            return _snapshot_of(_read_doc(path), key), OUTCOME_HIT
        except FileNotFoundError:
            return None, OUTCOME_MISS
        except _READ_ERRORS as exc:
            warnings.warn("S0SnapshotStore: 손상된 스냅샷 파일 -- 다시 계산해 같은 키로 교체한다: %s (%s)" % (path, exc), RuntimeWarning)
            return None, OUTCOME_CORRUPT

    def load(self, inputs, sources):
        """(GraphSnapshot | None, outcome)."""
        key = self.key_of(inputs, sources)
        return self._load_path(self._path_for(key), key)

    def save(self, inputs, sources, snapshot):
        """`snapshot`(GraphSnapshot)을 키 파일로 쓴다. 이미 검증되는 파일이 있으면 쓰지 않는다. 쓴 경로 또는 None."""
        if not isinstance(snapshot, GraphSnapshot):
            raise TypeError("S0SnapshotStore.save: snapshot 은 GraphSnapshot 이어야 한다")
        key = self.key_of(inputs, sources)
        path = self._path_for(key)
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
        if not _CLEANUP_STARTED.is_set():
            _CLEANUP_STARTED.set()
            self._cleanup(path, key)
        return path

    def _cleanup(self, keep_path, keep_key):
        """U-68: 어떤 checkout 으로도 키를 만들 수 없는 파일만 지운다(모듈 머리 '옛 파일 정리'). 프로세스의 첫 쓰기에서만 불린다."""
        try:
            names = sorted(os.listdir(self.directory))
        except OSError:
            return
        candidates = []
        for name in names:
            path = os.path.join(self.directory, name)
            if not _FILE_NAME.fullmatch(name) or path == keep_path or os.path.islink(path) or not os.path.isfile(path):
                continue
            try:
                key = _read_doc(path)["key"]
                valid = _well_formed(key)
            except _READ_ERRORS:
                continue
            if valid:
                candidates.append((path, key))
        if not candidates:
            return
        try:
            doomed = _unreproducible(_engine_root(), keep_key, candidates)
        except (OSError, ValueError, subprocess.SubprocessError):
            return
        for path in sorted(doomed):
            try:
                os.unlink(path)
            except OSError:
                continue
