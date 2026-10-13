"""core/snapshot_codec.py -- S0 수준 graph 스냅샷의 디스크 영속화 (design 40 v1.6 §2.4.1 (d), §2.4.3, §2.4.9 test 목록,
§2.4.12 Q1·Q2, §3.10.11 U-68).

design 근거(§2.4.3 표):
* 키 = (i) S0 전체 지문(topology 정규화 해시, LUT 내용 해시 + 생성 메타, spec 전체 해시, **PDK 선언 파일 내용 해시**(Q1·U-72),
  유도 규칙 코드 해시, metric 정의 코드 해시) (ii) `structure.json` 사실 지문 (iii) 엔진 코드 지문 = `gmid_engine` 아래 **test 가 아닌
  모든 패키지**의 `.py` 파일 바이트 sha256(파일 경로 정렬).
* 형식 = gzip JSON 하나 `{schema_version, key{...}, writers, block_versions, records[{kind, key, fields{name: {value, writer,
  input_version, write_count}}}], fp, body_sha256}`. float = `float.hex`, tuple·frozenset(정준 순서)·frozen dataclass =
  `{"__type__": "<모듈>.<클래스>", ...}`.
* 타입 등록부 밖 타입은 거부. 검증 = 읽은 뒤 `fp` 를 다시 계산해 저장된 `fp` 와 비교, 다르거나 `body_sha256` 이 틀리면 손상.
* 손상 -> 다시 계산하고 같은 키의 파일을 원자적으로 교체. 쓰기는 같은 디렉터리 임시 파일 + 교체. 키가 있고 검증을 통과하면 쓰지 않는다.
* 위치 = `gmid_engine` 아래 `.gitignore` 등록 디렉터리, 파일 이름 = `<키 지문>.json.gz`. 키가 다르면 없는 것으로 본다(SC-d).
* U-68(사용자 결정 원문, user_decisions.md): "저장소·모든 worktree 의 현재 파일(topology·spec·LUT·PDK 선언·유도 규칙 코드·writer 코드
  지문)로 만들 수 있는 키는 보존, 어떤 checkout 으로도 만들 수 없는 키의 스냅샷 파일만 쓰기 시점에 1회 삭제, 방금 쓴 파일·링크·폴더 밖·
  형식 다른 파일 제외, 실패 시 아무것도 지우지 않음".
* §2.4.9 `test_s0_snapshot_roundtrip`: 직렬화 -> 읽기 -> `fp` 비트 동일. 손상 파일은 재계산 후 같은 키로 교체. 등록부 밖 타입은 거부.

기대값 도출: 피검 코드를 부르지 않는다. 비교 기준은 (1) 입력으로 만든 원본 `GraphSnapshot`(기존 core API -- 이번 변경 대상 아님)의
`fp`·필드 메타, (2) 파이썬 값의 타입·`float.hex` 비트, (3) design 이 정한 파일 형식의 최상위 이름과 float 표기, (4) compute 호출 횟수·
파일 바이트·mtime 의 직접 관찰, (5) 입력 파일 원본 sha256 은 `hashlib` 로 직접 잰다.

[통합 단계 2026-10-13] red-first `_PENDING` 임시 이름을 구현 공개 API 로 맞췄다(판정 의미 불변):
* 구현 API = `S0SnapshotStore(directory, code_fp)` 의 `key_of(inputs, sources)`·`path_of`·`load(inputs, sources) -> (스냅샷|None, outcome)`·
  `save(inputs, sources, snapshot) -> 경로|None`, outcome 상수 `OUTCOME_HIT|MISS|CORRUPT`, `KEY_CODE_FP`.
* 키 = `_Key(inputs, sources, code_fp)`: red-first 의 8부분 중 (iii) `engine_code_fp` 는 저장소의 `code_fp`, 나머지 7부분은 `inputs`,
  U-68 재현 재료(입력 파일 경로·원본 sha256)는 `sources`.
* encode/decode = 임시 폴더의 `save` 가 쓴 파일 바이트 / 그 바이트를 키 파일 자리에 놓고 `load` -- `hit` 가 아니면 거부(`_Rejected`).
* fetch(directory, key, compute) = 단계 A 의 사용 순서(`pipeline/stage_a.py`: `load` -> hit 면 그대로, 아니면 compute 뒤 `save`) 그대로.
* 키 구성 8부분 중 'PDK 선언 해시 필수'(§2.4.12 Q1 fail-closed)는 구현에서 키를 조립하는 `run_stage_a(pdk_decl=)` 가 강제한다 ->
  `tests/pipeline/test_stage_a.py::test_pdk_decl_required_*` 로 옮겼다. 엔진 코드 지문 (iii) test 는 원본 1:1 규칙 H 에 따라
  `tests/core/test_engine_code_fp.py` 로 옮겼다.
* U-68 정리의 '보존 키 집합' 주입(`retained`)은 구현에 없다 -- 구현은 사용자 원문대로 키의 입력 파일 원본 sha 와 엔진 코드 지문을
  이 저장소·worktree 의 현재 파일과 대조한다. 그래서 정리 test 는 진짜 판정 재료(임시 입력 파일 내용 바꾸기·지우기, 가짜 worktree 의
  엔진 트리)로 재현 가능/불가능을 만든다. worktree 나열(`git worktree list`)만 test 가 정한 목록으로 바꾼다(실제 저장소 worktree ~100개를
  훑으면 약 80 s, 결과가 저장소 상태에 따라 바뀐다). 나열 실패 주입도 같은 자리다.

`test_g10_second_run_s0_zero`(§2.4.9 판정 2)는 RunCounters(단계 ②)의 S0 블록 `computes` 계수가 필요해 이 파일에 쓰지 않았다
-- 이 단위에서 판정 가능한 부분은 `test_second_fetch_same_key_is_hit_without_compute`(compute 0회·`fp` 동일)와
`tests/graph/test_s1_build.py::test_previous_snapshot_reuses_every_block`(디스크 스냅샷 위 build_s1 의 블록 계산 0).
"""
import collections
import dataclasses
import gzip
import hashlib
import importlib
import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from gmid_engine.core import GraphSnapshot, WriterTable
from gmid_engine.core.snapshot_codec import KEY_CODE_FP, OUTCOME_CORRUPT, OUTCOME_HIT, OUTCOME_MISS, S0SnapshotStore

_REJECT = (TypeError, ValueError, KeyError)  # 등록부 밖 타입 거부 예외 -- 클래스 이름은 design 이 정하지 않았다
_SUFFIX = ".json.gz"
_TOP_LEVEL = {"schema_version", "key", "writers", "block_versions", "records", "fp", "body_sha256"}
_ENGINE_DIR = Path(__file__).resolve().parents[2]          # tests/core -> tests -> gmid_engine


def _codec_module():
    return importlib.import_module("gmid_engine.core.snapshot_codec")


def _register(cls):
    from gmid_engine.core.type_registry import type_registry
    type_registry().register(cls)
    return cls


class _Rejected(Exception):
    """decode 어댑터: load 가 hit 이 아니면(손상·등록부 밖 타입) 받지 않았다."""


# ---------- 값 형식 픽스처(회로·소자 이름 없음) ----------

@dataclasses.dataclass(frozen=True)
class _Point:
    x: float
    tag: str
    items: tuple


@dataclasses.dataclass(frozen=True)
class _Wrap:
    inner: _Point
    kinds: frozenset
    count: int


_CONSTRUCTED = []   # 미등록 타입이 디코딩 중 만들어지면 여기에 남는다


@dataclasses.dataclass(frozen=True)
class _NeverRegistered:
    x: float

    def __new__(cls, *args, **kwargs):
        _CONSTRUCTED.append(cls.__qualname__)
        return super().__new__(cls)


@dataclasses.dataclass(frozen=True)
class _AlsoNeverRegistered:
    x: float


_REGISTERED = []


@pytest.fixture(scope="module", autouse=True)
def _registered_types():
    # 등록부는 실행 전역이다. 이 모듈의 두 값 형식만 한 번 올린다(_NeverRegistered·_AlsoNeverRegistered 는 올리지 않는다).
    if not _REGISTERED:
        _register(_Point)
        _register(_Wrap)
        _REGISTERED.append(True)
    yield


_FLOAT_PROBES = {
    "f_tenth": 0.1,
    "f_negzero": -0.0,
    "f_subnormal": 5e-324,
    "f_max": 1.7976931348623157e308,
    "f_pinf": math.inf,
    "f_ninf": -math.inf,
    "f_nan": math.nan,
    "f_one": 1.0,
}
_OTHER_PROBES = {
    "i_zero": 0,
    "i_neg": -7,
    "i_big": 10 ** 40,
    "b_true": True,
    "b_false": False,
    "n_none": None,
    "s_empty": "",
    "s_hexlike": float.hex(1.0),          # float.hex 처럼 보이는 문자열도 str 로 남아야 한다
    "s_typekey": "__type__",
    "s_unicode": "한글 µ Ω",
    "t_empty": (),
    "t_nested": ((1, 2.5), ("a",), ()),
    "t_mixed": (1, True, 1.0, None, "1"),
    "z_str": frozenset({"b", "a", "c"}),
    "z_tuple": frozenset({(1, "x"), (0, "y")}),
    "z_empty": frozenset(),
}
_DATACLASS_PROBES = {
    "d_point": _Point(0.30000000000000004, "p", (1, 2.0, "s")),
    "d_wrap": _Wrap(_Point(-0.0, "", ()), frozenset({"u", "v"}), 3),
    "d_tuple_of_points": (_Point(1e-15, "a", ()), _Point(2.5, "b", (frozenset({1}),))),
}

_WRITERS = WriterTable([
    ("graph", "alpha", "w_a"),
    ("device", "gamma", "w_a"),
    ("device", "delta", "w_b"),
    ("node", "eps", "w_c"),
])


def _snapshot():
    """세 writer·세 입력 버전·write_count 2 인 필드를 가진 스냅샷."""
    s = GraphSnapshot.empty(_WRITERS)
    s = s.write("w_a", "iv-a-1", {("graph", "alpha"): {"g": 1.5}, ("device", "gamma"): dict(_FLOAT_PROBES)})
    s = s.write("w_a", "iv-a-2", {("graph", "alpha"): {"g": 2.5}, ("device", "gamma"): dict(_FLOAT_PROBES)})
    s = s.write("w_b", "iv-b-1", {("device", "delta"): dict(_OTHER_PROBES)})
    s = s.write("w_c", "iv-c-1", {("node", "eps"): dict(_DATACLASS_PROBES)})
    return s


# ---------- 키(§2.4.3 (i)~(iii)) -> 구현 API 의 (inputs, sources, code_fp) ----------

_Key = collections.namedtuple("_Key", "inputs sources code_fp")
_KEY_PARTS = ("topology_fp", "lut_fp", "spec_fp", "pdk_decl_fp", "rule_code_fp", "metric_code_fp",
              "structure_facts_fp", "engine_code_fp")


def _key(sources=None, **override):
    parts = {
        "topology_fp": "t" * 8,
        "lut_fp": "l" * 8,
        "spec_fp": "s" * 8,
        "pdk_decl_fp": "p" * 8,
        "rule_code_fp": "r" * 8,
        "metric_code_fp": "m" * 8,
        "structure_facts_fp": "f" * 8,
        "engine_code_fp": "e" * 8,
    }
    parts.update(override)
    code_fp = parts.pop("engine_code_fp")
    return _Key(parts, dict(sources or {}), code_fp)


def _store(directory, key):
    return S0SnapshotStore(str(directory), key.code_fp)


def _key_name(key):
    """키 동일성 = 파일 이름(design: 파일 이름 = <키 지문>.json.gz)."""
    with tempfile.TemporaryDirectory() as d:
        return os.path.basename(_store(d, key).path_of(key.inputs, key.sources))


def _encode(snapshot, key):
    """(snapshot, key) -> gzip JSON 파일 한 개의 바이트(임시 폴더의 save 가 쓴 그대로)."""
    with tempfile.TemporaryDirectory() as d:
        path = _store(d, key).save(key.inputs, key.sources, snapshot)
        assert path is not None, "save 가 쓰지 못했다"
        with open(path, "rb") as fh:
            return fh.read()


def _decode(data, key):
    """바이트를 그 키의 파일 자리에 두고 load. hit 가 아니면 `_Rejected`(검증 포함, 손상·미등록 타입 거부)."""
    with tempfile.TemporaryDirectory() as d:
        store = _store(d, key)
        with open(store.path_of(key.inputs, key.sources), "wb") as fh:
            fh.write(data)
        snap, outcome = store.load(key.inputs, key.sources)
    if outcome != OUTCOME_HIT:
        raise _Rejected(outcome)
    return snap


Fetched = collections.namedtuple("Fetched", "snapshot outcome")


def _fetch(directory, key, compute):
    """단계 A 의 사용 순서(pipeline/stage_a.py): load -> hit 면 그대로, 아니면 compute 뒤 save(손상이면 같은 키로 교체)."""
    store = _store(directory, key)
    snap, outcome = store.load(key.inputs, key.sources)
    if outcome == OUTCOME_HIT:
        return Fetched(snap, outcome)
    snap = compute()
    store.save(key.inputs, key.sources, snap)
    return Fetched(snap, outcome)


# ---------- 값 비교(타입 보존 + float 비트) ----------

def _same(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is float:
        return float.hex(a) == float.hex(b)   # -0.0·nan·subnormal 까지 비트 동일
    if type(a) is tuple:
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    if type(a) is frozenset:
        return len(a) == len(b) and all(any(_same(x, y) for y in b) for x in a)
    if dataclasses.is_dataclass(a):
        return all(_same(getattr(a, f.name), getattr(b, f.name)) for f in dataclasses.fields(a))
    return a == b


def _assert_same_snapshot(orig, got):
    assert isinstance(got, GraphSnapshot)
    assert got.fp == orig.fp
    assert got.writers == orig.writers
    assert dict(got.block_versions) == dict(orig.block_versions)
    assert got.kinds() == orig.kinds()
    for kind in orig.kinds():
        assert got.keys(kind) == orig.keys(kind)
        for key in orig.keys(kind):
            o_rec, g_rec = orig.record(kind, key), got.record(kind, key)
            assert g_rec.field_names() == o_rec.field_names()
            for name in o_rec.field_names():
                o, g = o_rec.get(name), g_rec.get(name)
                assert (g.writer, g.input_version, g.write_count) == (o.writer, o.input_version, o.write_count), (kind, key, name)
                assert _same(o.value, g.value), "타입/비트 불일치 %r: %r -> %r" % ((kind, key, name), o.value, g.value)


def _files(directory):
    return sorted(n for n in os.listdir(directory) if n.endswith(_SUFFIX))


def _one_file(directory):
    names = _files(directory)
    assert len(names) == 1, names
    return os.path.join(directory, names[0])


def _counting(snapshot):
    calls = []

    def compute():
        calls.append(1)
        return snapshot

    return compute, calls


def _must_not_compute():
    raise AssertionError("검증을 통과한 같은 키 파일이 있는데 다시 계산했다")


# =====================================================================
# §2.4.9 test_s0_snapshot_roundtrip -- 직렬화 -> 읽기 -> fp 비트 동일(타입 보존)
# =====================================================================

def test_s0_snapshot_roundtrip():
    orig = _snapshot()
    data = _encode(orig, _key())
    got = _decode(data, _key())
    _assert_same_snapshot(orig, got)


def test_roundtrip_through_disk_fetch(tmp_path):
    orig = _snapshot()
    compute, calls = _counting(orig)
    first = _fetch(tmp_path, _key(), compute)
    assert len(calls) == 1 and first.outcome == OUTCOME_MISS
    _assert_same_snapshot(orig, first.snapshot)
    second = _fetch(tmp_path, _key(), _must_not_compute)
    assert second.outcome == OUTCOME_HIT
    _assert_same_snapshot(orig, second.snapshot)


def test_encoding_is_deterministic():
    # 같은 스냅샷·같은 키 -> 같은 바이트(정준 순서, frozenset 정준 순서 포함). gzip 머리의 시각 칸이 고정돼야 한다.
    a = _encode(_snapshot(), _key())
    b = _encode(_snapshot(), _key())
    assert gzip.decompress(a) == gzip.decompress(b)


# ---------- 파일 형식(§2.4.3 '형식' 행) ----------

def _payload(data):
    return json.loads(gzip.decompress(data).decode("utf-8"))


def test_file_is_single_gzip_json_with_design_top_level_fields():
    orig = _snapshot()
    doc = _payload(_encode(orig, _key()))
    assert set(doc) == _TOP_LEVEL
    assert doc["fp"] == orig.fp            # 저장된 fp = 스냅샷 내용 지문


def test_record_fields_carry_value_writer_input_version_write_count():
    doc = _payload(_encode(_snapshot(), _key()))
    recs = doc["records"]
    assert isinstance(recs, list) and recs
    for rec in recs:
        assert {"kind", "key", "fields"} <= set(rec)
        for meta in rec["fields"].values():
            assert {"value", "writer", "input_version", "write_count"} <= set(meta)
    alpha = [r for r in recs if r["kind"] == "graph" and r["key"] == "g"]
    assert len(alpha) == 1
    assert alpha[0]["fields"]["alpha"]["write_count"] == 2
    assert alpha[0]["fields"]["alpha"]["input_version"] == "iv-a-2"


def test_floats_are_written_as_float_hex():
    text = gzip.decompress(_encode(_snapshot(), _key())).decode("utf-8")
    for name in ("f_tenth", "f_subnormal", "f_max"):
        assert float.hex(_FLOAT_PROBES[name]) in text, name
    assert float.hex(-0.0) in text


def test_registered_dataclass_written_with_qualified_type_name():
    text = gzip.decompress(_encode(_snapshot(), _key())).decode("utf-8")
    for cls in (_Point, _Wrap):
        assert '"__type__"' in text
        assert cls.__module__ + "." + cls.__qualname__ in text


def test_key_is_stored_in_file():
    a = _payload(_encode(_snapshot(), _key()))["key"]
    b = _payload(_encode(_snapshot(), _key(pdk_decl_fp="other")))["key"]
    assert isinstance(a, dict) and a != b


def test_stored_key_carries_engine_code_fp_and_input_file_sha(tmp_path):
    # U-68 재현 재료: 키(= 스냅샷 메타)에 엔진 코드 지문과 입력 파일 원본 sha256 이 있어야 엔진 실행 없이 checkout 마다 재현을 판정한다.
    src = tmp_path / "in.json"
    src.write_bytes(b'{"x": 1}')
    sha = hashlib.sha256(src.read_bytes()).hexdigest()
    key = _key(sources={"topology": (str(src), sha)}, engine_code_fp="c0de" * 16)
    stored = _payload(_encode(_snapshot(), key))["key"]
    assert stored[KEY_CODE_FP] == "c0de" * 16
    assert sha in stored.values()
    assert any(isinstance(v, str) and v.endswith(src.resolve().as_posix()) for v in stored.values()), stored


# =====================================================================
# 위치(§2.4.3 '위치': gmid_engine 아래 .gitignore 등록 디렉터리)
# =====================================================================

def test_default_location_is_gitignored_dir_under_engine():
    store = S0SnapshotStore.default("e" * 8)
    d = Path(store.directory).resolve()
    assert d.parent == _ENGINE_DIR
    probe = d / ("0" * 64 + _SUFFIX)
    done = subprocess.run(("git", "-C", str(_ENGINE_DIR), "check-ignore", "-q", str(probe)), capture_output=True)
    assert done.returncode == 0, "S0 스냅샷 폴더가 .gitignore 에 등록되지 않았다: %s" % d


# =====================================================================
# 등록부 밖 타입 거부(§2.4.3 '타입 등록부')
# =====================================================================

def _snapshot_with(value):
    return GraphSnapshot.empty(_WRITERS).write("w_c", "iv-x", {("node", "eps"): {"k": value}})


@pytest.mark.parametrize("value", [
    _AlsoNeverRegistered(1.0),
    (_AlsoNeverRegistered(1.0),),
    frozenset({_AlsoNeverRegistered(2.0)}),
    _Point(1.0, "x", (_AlsoNeverRegistered(3.0),)),
], ids=["bare", "in_tuple", "in_frozenset", "inside_registered"])
def test_encode_rejects_unregistered_type(value):
    with pytest.raises(_REJECT):
        _encode(_snapshot_with(value), _key())


def test_fetch_writes_nothing_when_value_type_unregistered(tmp_path):
    compute, _ = _counting(_snapshot_with(_AlsoNeverRegistered(1.0)))
    try:
        _fetch(tmp_path, _key(), compute)
    except _REJECT:
        pass
    assert _files(tmp_path) == []


def test_decode_rejects_unregistered_type_name_without_constructing_it():
    # 등록된 _Point 의 이름 자리를 import 가능한 미등록 클래스 이름으로 바꾼 파일 -> 거부, 그 클래스는 만들어지지 않는다.
    # (body_sha256 이 먼저 잡을 수 있다 -- 어느 쪽이든 받지 않아야 한다. 무결성 칸까지 맞춘 경우는 바로 아래 test.)
    good = _snapshot_with(_Point(1.0, "x", ()))
    text = gzip.decompress(_encode(good, _key())).decode("utf-8")
    src = _Point.__module__ + "." + _Point.__qualname__
    dst = _NeverRegistered.__module__ + "." + _NeverRegistered.__qualname__
    assert src in text
    tampered = gzip.compress(text.replace(src, dst).encode("utf-8"))
    before = len(_CONSTRUCTED)
    with pytest.raises(Exception):
        _decode(tampered, _key())
    assert len(_CONSTRUCTED) == before, "미등록 타입을 디코딩 중에 만들었다"


def _canonical_sha(doc):
    body = {k: v for k, v in doc.items() if k != "body_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()


def test_decode_rejects_unregistered_type_even_with_consistent_body_sha():
    # 무결성 칸(body_sha256)까지 다시 맞춘 변조 -> 등록부 검사 자체가 거부해야 한다(디코더는 목록 밖 타입을 받지 않는다).
    good = _snapshot_with(_Point(1.0, "x", ()))
    doc = _payload(_encode(good, _key()))
    assert _canonical_sha(doc) == doc["body_sha256"], "이 test 의 정준 바이트 재현이 구현과 달라 변조가 의미 없다"
    src = _Point.__module__ + "." + _Point.__qualname__
    dst = _NeverRegistered.__module__ + "." + _NeverRegistered.__qualname__
    tampered = json.loads(json.dumps(doc).replace(json.dumps(src), json.dumps(dst)))
    assert tampered != doc
    tampered["body_sha256"] = _canonical_sha(tampered)
    before = len(_CONSTRUCTED)
    with pytest.raises(_Rejected):
        _decode(gzip.compress(json.dumps(tampered).encode("utf-8")), _key())
    assert len(_CONSTRUCTED) == before, "미등록 타입을 디코딩 중에 만들었다"


# =====================================================================
# 읽기 적중·키 다름(§2.4.3 '쓰기'·'무효화')
# =====================================================================

def test_second_fetch_same_key_is_hit_without_compute(tmp_path):
    orig = _snapshot()
    compute, calls = _counting(orig)
    _fetch(tmp_path, _key(), compute)
    path = _one_file(tmp_path)
    with open(path, "rb") as fh:
        bytes_before = fh.read()
    mtime_before = os.stat(path).st_mtime_ns
    got = _fetch(tmp_path, _key(), _must_not_compute)
    assert len(calls) == 1
    assert got.outcome == OUTCOME_HIT and got.snapshot.fp == orig.fp
    with open(path, "rb") as fh:
        assert fh.read() == bytes_before            # 검증 통과한 파일은 다시 쓰지 않는다
    assert os.stat(path).st_mtime_ns == mtime_before
    assert _files(tmp_path) == [os.path.basename(path)]


def test_save_over_valid_same_key_file_does_not_write(tmp_path, monkeypatch):
    # '키가 이미 있고 검증을 통과하면 쓰지 않는다' -- 저장 함수 자신의 규칙(호출자가 hit 를 확인하지 않고 불러도).
    key = _key()
    store = _store(tmp_path, key)
    path = store.save(key.inputs, key.sources, _snapshot())
    with open(path, "rb") as fh:
        bytes_before = fh.read()
    mtime_before = os.stat(path).st_mtime_ns
    seen = []
    real_replace = os.replace

    def recording_replace(*args, **kwargs):
        seen.append(args)
        return real_replace(*args, **kwargs)

    monkeypatch.setattr(os, "replace", recording_replace)
    again = store.save(key.inputs, key.sources, _snapshot())
    monkeypatch.undo()
    assert os.path.normcase(os.path.abspath(again)) == os.path.normcase(os.path.abspath(path))
    assert seen == []
    with open(path, "rb") as fh:
        assert fh.read() == bytes_before
    assert os.stat(path).st_mtime_ns == mtime_before


def test_file_name_is_key_fingerprint_with_json_gz_suffix(tmp_path):
    _fetch(tmp_path, _key(), _counting(_snapshot())[0])
    name = os.path.basename(_one_file(tmp_path))
    assert name.endswith(_SUFFIX) and len(name) > len(_SUFFIX)
    assert name == _key_name(_key())


def test_other_key_is_a_miss(tmp_path):
    compute, calls = _counting(_snapshot())
    _fetch(tmp_path, _key(), compute)
    got = _fetch(tmp_path, _key(spec_fp="other"), compute)
    assert got.outcome == OUTCOME_MISS
    assert len(calls) == 2
    assert len(_files(tmp_path)) == 2


def test_file_moved_under_other_key_name_is_not_accepted(tmp_path):
    # 키가 다르면 없는 것으로 본다(SC-d): 다른 키의 파일을 이 키의 이름으로 옮겨도 받지 않는다(저장된 키 대조).
    a, b = _key(spec_fp="a"), _key(spec_fp="b")
    _fetch(tmp_path, a, _counting(_snapshot())[0])
    shutil.move(_one_file(tmp_path), os.path.join(tmp_path, _key_name(b)))
    compute, calls = _counting(_snapshot())
    got = _fetch(tmp_path, b, compute)
    assert len(calls) == 1 and got.outcome != OUTCOME_HIT


# =====================================================================
# 손상 -> 재계산 + 같은 키 파일 원자적 교체(§2.4.3 '검증'·'손상 처리')
# =====================================================================

def _rewrite_json(path, mutate):
    with open(path, "rb") as fh:
        doc = json.loads(gzip.decompress(fh.read()).decode("utf-8"))
    mutate(doc)
    with open(path, "wb") as fh:
        fh.write(gzip.compress(json.dumps(doc).encode("utf-8")))


def _rewrite_text(path, old, new):
    with open(path, "rb") as fh:
        text = gzip.decompress(fh.read()).decode("utf-8")
    assert old in text, "손상 주입 대상 %r 가 파일에 없다(design 형식: float = float.hex)" % old
    with open(path, "wb") as fh:
        fh.write(gzip.compress(text.replace(old, new).encode("utf-8")))


def _first_field_meta(doc):
    rec = doc["records"][0]
    return rec["fields"][sorted(rec["fields"])[0]]


def _corrupt_garbage(path):
    with open(path, "wb") as fh:
        fh.write(b"not a gzip file")


def _corrupt_truncated(path):
    with open(path, "rb") as fh:
        data = fh.read()
    with open(path, "wb") as fh:
        fh.write(data[: len(data) // 2])


def _corrupt_bad_json(path):
    with open(path, "wb") as fh:
        fh.write(gzip.compress(b"{not json"))


def _corrupt_body_sha(path):
    _rewrite_json(path, lambda d: d.__setitem__("body_sha256", "0" * 64))


def _corrupt_fp(path):
    _rewrite_json(path, lambda d: d.__setitem__("fp", "f" * 64))


def _corrupt_value(path):
    # 값만 바꾸고 fp·body_sha256 은 그대로 -> fp 재계산 불일치(또는 body_sha256 불일치). graph/g/alpha 의 마지막 값 = 2.5
    _rewrite_text(path, float.hex(2.5), float.hex(2.25))


def _corrupt_metadata(path):
    # fp 가 덮지 않는 writer 메타만 바꾼다 -> body_sha256 이 잡아야 한다
    _rewrite_json(path, lambda d: _first_field_meta(d).__setitem__("writer", "tampered"))


_CORRUPTIONS = {
    "garbage": _corrupt_garbage,
    "truncated": _corrupt_truncated,
    "bad_json": _corrupt_bad_json,
    "body_sha256_mismatch": _corrupt_body_sha,
    "fp_mismatch": _corrupt_fp,
    "value_tamper": _corrupt_value,
    "metadata_tamper": _corrupt_metadata,
}


@pytest.mark.parametrize("corruption", sorted(_CORRUPTIONS))
def test_corrupt_file_is_recomputed_and_replaced_under_same_key(tmp_path, corruption):
    orig = _snapshot()
    compute, calls = _counting(orig)
    _fetch(tmp_path, _key(), compute)
    path = _one_file(tmp_path)
    _CORRUPTIONS[corruption](path)
    with pytest.warns(RuntimeWarning):
        got = _fetch(tmp_path, _key(), compute)
    assert got.outcome == OUTCOME_CORRUPT, "손상 사실이 outcome(perf.s0_snapshot.corrupt 재료)에 남지 않았다"
    assert len(calls) == 2, "손상 파일을 받아들였다(재계산 안 함)"
    _assert_same_snapshot(orig, got.snapshot)
    assert _files(tmp_path) == [os.path.basename(path)], "같은 키 파일을 교체하지 않고 새 이름을 만들었다"
    again = _fetch(tmp_path, _key(), _must_not_compute)   # 교체된 파일은 검증을 통과한다
    assert again.outcome == OUTCOME_HIT
    _assert_same_snapshot(orig, again.snapshot)


def test_corrupt_file_rejected_by_decode():
    data = _encode(_snapshot(), _key())
    doc = json.loads(gzip.decompress(data).decode("utf-8"))
    doc["fp"] = "f" * 64
    with pytest.raises(Exception):
        _decode(gzip.compress(json.dumps(doc).encode("utf-8")), _key())


# =====================================================================
# 원자적 쓰기(§2.4.3 '쓰기': 같은 디렉터리 임시 파일 -> 교체)
# =====================================================================

def test_write_goes_through_same_directory_temp_and_replace(tmp_path, monkeypatch):
    seen = []
    real_replace = os.replace

    def recording_replace(src, dst, *args, **kwargs):
        seen.append((os.path.abspath(os.fspath(src)), os.path.abspath(os.fspath(dst))))
        return real_replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "replace", recording_replace)
    _fetch(tmp_path, _key(), _counting(_snapshot())[0])
    target = os.path.abspath(_one_file(tmp_path))
    hits = [(s, d) for s, d in seen if os.path.normcase(d) == os.path.normcase(target)]
    assert hits, "목표 파일을 os.replace 로 교체하지 않았다(직접 쓰기)"
    for src, dst in hits:
        assert os.path.normcase(os.path.dirname(src)) == os.path.normcase(os.path.dirname(dst))
        assert os.path.normcase(src) != os.path.normcase(dst)


def _failing_replace(*args, **kwargs):
    raise OSError("injected replace failure")


def test_failed_replace_keeps_old_file_bytes(tmp_path, monkeypatch):
    orig = _snapshot()
    compute, calls = _counting(orig)
    _fetch(tmp_path, _key(), compute)
    path = _one_file(tmp_path)
    _corrupt_body_sha(path)                     # 다시 쓰게 만든다
    with open(path, "rb") as fh:
        old_bytes = fh.read()
    monkeypatch.setattr(os, "replace", _failing_replace)
    try:
        got = _fetch(tmp_path, _key(), compute).snapshot
    except OSError:
        got = None
    monkeypatch.undo()
    if got is not None:
        _assert_same_snapshot(orig, got)
    with open(path, "rb") as fh:
        assert fh.read() == old_bytes, "교체 실패 중에 옛 파일이 바뀌었다(원자적 쓰기 아님)"
    assert _files(tmp_path) == [os.path.basename(path)]


def test_failed_replace_on_miss_leaves_no_target_file(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "replace", _failing_replace)
    try:
        _fetch(tmp_path, _key(), _counting(_snapshot())[0])
    except OSError:
        pass
    monkeypatch.undo()
    assert _files(tmp_path) == [], "교체 실패인데 반쯤 쓴 목표 파일이 남았다"


# =====================================================================
# 키 구성(§2.4.3 키 (i)~(iii)) -- 같은 부분 = 같은 키 파일, 어느 부분이든 바뀌면 다른 파일
# (PDK 선언 해시 '필수'는 키 조립 지점 run_stage_a 가 강제 -> tests/pipeline/test_stage_a.py)
# =====================================================================

def test_same_parts_give_same_key():
    assert _key_name(_key()) == _key_name(_key())


@pytest.mark.parametrize("part", _KEY_PARTS)
def test_each_key_part_changes_key(part):
    assert _key_name(_key(**{part: "changed"})) != _key_name(_key())


def test_input_file_sha_changes_key(tmp_path):
    src = tmp_path / "in.json"
    a = _key(sources={"topology": (str(src), "a" * 64)})
    b = _key(sources={"topology": (str(src), "b" * 64)})
    assert _key_name(a) != _key_name(b)


def test_pdk_decl_change_gives_other_file(tmp_path):
    compute, calls = _counting(_snapshot())
    _fetch(tmp_path, _key(pdk_decl_fp="decl-v1"), compute)
    _fetch(tmp_path, _key(pdk_decl_fp="decl-v2"), compute)
    assert len(calls) == 2 and len(_files(tmp_path)) == 2


def test_structure_fact_change_gives_other_file(tmp_path):
    compute, calls = _counting(_snapshot())
    _fetch(tmp_path, _key(structure_facts_fp="facts-v1"), compute)
    _fetch(tmp_path, _key(structure_facts_fp="facts-v2"), compute)
    assert len(calls) == 2 and len(_files(tmp_path)) == 2


def test_engine_code_fp_change_gives_other_file(tmp_path):
    compute, calls = _counting(_snapshot())
    _fetch(tmp_path, _key(engine_code_fp="code-v1"), compute)
    got = _fetch(tmp_path, _key(engine_code_fp="code-v2"), compute)
    assert got.outcome == OUTCOME_MISS and len(calls) == 2


# =====================================================================
# U-68 옛 파일 정리(§2.4.12 Q2, §3.10.11, 사용자 결정 원문) -- 쓰기 시점 1회, 어떤 checkout 으로도 만들 수 없는 키만,
# 방금 쓴 파일·링크·폴더 밖·형식 다른 파일 제외, 실패 시 0.
# 재현 재료 = 키의 입력 파일 원본 sha256 + 엔진 코드 지문(사용자 원문 '현재 파일(topology·spec·LUT·PDK 선언·유도 규칙 코드·writer 코드
# 지문)'). 기대값(보존/삭제)은 이 재료를 test 가 직접 바꿔 정한다.
# =====================================================================

_ROLES = ("topology", "spec", "structure", "pdk_decl", "lut_manifest")
_CURRENT_CODE = "e" * 8


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _inputs_dir(tmp_path):
    d = tmp_path / "inputs"
    d.mkdir(exist_ok=True)
    for role in _ROLES:
        p = d / (role + ".json")
        if not p.exists():
            p.write_bytes(('{"role": "%s"}' % role).encode("ascii"))
    return d


def _sources_now(inputs):
    """입력 파일의 지금 원본 sha256(hashlib 직접, 없는 파일은 None)."""
    out = {}
    for role in _ROLES:
        p = inputs / (role + ".json")
        out[role] = (str(p), _sha(p) if p.exists() else None)
    return out


def _write(directory, key):
    """키 파일 하나를 쓰고(miss -> compute -> save) 그 경로."""
    _fetch(directory, key, _counting(_snapshot())[0])
    path = os.path.join(directory, _key_name(key))
    assert os.path.exists(path)
    return path


def _repo_top():
    for folder in (_ENGINE_DIR,) + tuple(_ENGINE_DIR.parents):
        if (folder / ".git").exists():
            return folder
    raise AssertionError("엔진 폴더가 git 저장소 안에 없다")


def _listing(*worktrees):
    """`git worktree list --porcelain` 형식 -- 이 저장소 + test 가 정한 worktree."""
    return "".join("worktree %s\nHEAD %s\n\n" % (Path(w).as_posix(), "0" * 40) for w in (_repo_top(),) + worktrees)


@pytest.fixture(autouse=True)
def worktrees(monkeypatch):
    """worktree 나열을 test 가 정한 목록으로 바꾼다(판정 로직은 그대로). 기본 = 이 저장소 하나.
    이 파일의 모든 test 에 건다: 실제 나열이면 엔진 코드 지문이 다른 후보 하나에 저장소의 worktree ~100개를 모두 재어
    test 하나가 약 100 s 걸리고(실측 102 s, test_engine_code_fp_change_gives_other_file) 결과가 저장소 상태에 따라 바뀐다."""
    codec = _codec_module()
    state = {"listing": _listing(), "calls": 0}

    def fake_git(directory, *args):
        if args[:2] != ("worktree", "list"):
            raise AssertionError("정리가 예상 밖 git 명령을 불렀다: %r" % (args,))
        state["calls"] += 1
        if isinstance(state["listing"], Exception):
            raise state["listing"]
        return state["listing"]

    monkeypatch.setattr(codec, "_git", fake_git)
    return state


def test_cleanup_keeps_key_reproducible_from_current_files(tmp_path, worktrees):
    inputs = _inputs_dir(tmp_path)
    cache = tmp_path / "cache"
    old = _write(cache, _key(sources=_sources_now(inputs), spec_fp="old"))
    new = _write(cache, _key(sources=_sources_now(inputs), spec_fp="new"))
    assert os.path.exists(old) and os.path.exists(new)


@pytest.mark.parametrize("role", _ROLES)
def test_cleanup_removes_key_whose_input_file_changed(tmp_path, worktrees, role):
    inputs = _inputs_dir(tmp_path)
    cache = tmp_path / "cache"
    old = _write(cache, _key(sources=_sources_now(inputs)))
    (inputs / (role + ".json")).write_bytes(b'{"edited": true}')          # 이 입력 파일의 현재 내용으로는 옛 키를 못 만든다
    new = _write(cache, _key(sources=_sources_now(inputs)))
    assert not os.path.exists(old), role
    assert os.path.exists(new)


def test_cleanup_removes_key_whose_input_file_was_deleted(tmp_path, worktrees):
    inputs = _inputs_dir(tmp_path)
    cache = tmp_path / "cache"
    old = _write(cache, _key(sources=_sources_now(inputs)))
    os.remove(inputs / "spec.json")
    new = _write(cache, _key(sources=_sources_now(inputs)))
    assert not os.path.exists(old)
    assert os.path.exists(new)


def test_cleanup_keeps_key_whose_absent_input_is_still_absent(tmp_path, worktrees):
    # 키가 '파일 없음'(sha None)을 기록했고 지금도 없으면 같은 키를 만들 수 있다 -> 보존.
    inputs = _inputs_dir(tmp_path)
    cache = tmp_path / "cache"
    os.remove(inputs / "structure.json")
    old = _write(cache, _key(sources=_sources_now(inputs), spec_fp="old"))
    new = _write(cache, _key(sources=_sources_now(inputs), spec_fp="new"))
    assert os.path.exists(old) and os.path.exists(new)


def test_cleanup_removes_key_whose_engine_code_no_checkout_has(tmp_path, worktrees):
    inputs = _inputs_dir(tmp_path)
    cache = tmp_path / "cache"
    old = _write(cache, _key(sources=_sources_now(inputs), engine_code_fp="old-code"))
    new = _write(cache, _key(sources=_sources_now(inputs), engine_code_fp=_CURRENT_CODE))
    assert not os.path.exists(old)
    assert os.path.exists(new)
    assert worktrees["calls"] == 1          # 이 저장소에서 결정되지 않은 후보가 있어 worktree 를 나열했다


def _engine_rel():
    return _ENGINE_DIR.relative_to(_repo_top())


def _fake_worktree(root, engine_files):
    """worktree 하나: <root>/<엔진 상대 경로>/ 아래 .py 파일들."""
    engine = root / _engine_rel()
    for rel, text in engine_files.items():
        p = engine.joinpath(*rel.split("/"))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
    return engine


def _code_fp_of(engine):
    # 입력(옛 실행의 엔진 코드 지문) 생성용 -- 기대값(보존/삭제)은 이 값이 아니라 test 가 정한 worktree 구성에서 나온다.
    from gmid_engine.core.engine_code_fp import engine_code_fp
    return engine_code_fp(str(engine))


def test_cleanup_keeps_key_reproducible_in_another_worktree(tmp_path, worktrees):
    inputs = _inputs_dir(tmp_path)
    cache = tmp_path / "cache"
    other = tmp_path / "wt_other"
    other_code = _code_fp_of(_fake_worktree(other, {"__init__.py": "", "core/a.py": "A = 2\n"}))
    worktrees["listing"] = _listing(other)
    old = _write(cache, _key(sources=_sources_now(inputs), engine_code_fp=other_code))
    _write(cache, _key(sources=_sources_now(inputs), engine_code_fp=_CURRENT_CODE))
    assert worktrees["calls"] == 1
    assert os.path.exists(old), "다른 worktree 의 엔진 코드로 만들 수 있는 키를 지웠다"


def test_cleanup_removes_key_when_other_worktree_code_differs(tmp_path, worktrees):
    inputs = _inputs_dir(tmp_path)
    cache = tmp_path / "cache"
    other = tmp_path / "wt_other"
    engine = _fake_worktree(other, {"__init__.py": "", "core/a.py": "A = 2\n"})
    old_code = _code_fp_of(engine)
    (engine / "core" / "a.py").write_bytes(b"A = 3\n")                    # 그 worktree 의 코드가 바뀌었다
    worktrees["listing"] = _listing(other)
    old = _write(cache, _key(sources=_sources_now(inputs), engine_code_fp=old_code))
    _write(cache, _key(sources=_sources_now(inputs), engine_code_fp=_CURRENT_CODE))
    assert not os.path.exists(old)


def test_cleanup_ignores_worktree_without_engine(tmp_path, worktrees):
    inputs = _inputs_dir(tmp_path)
    cache = tmp_path / "cache"
    bare = tmp_path / "wt_bare"
    bare.mkdir()
    worktrees["listing"] = _listing(bare)
    old = _write(cache, _key(sources=_sources_now(inputs), engine_code_fp="old-code"))
    _write(cache, _key(sources=_sources_now(inputs), engine_code_fp=_CURRENT_CODE))
    assert not os.path.exists(old)


def test_cleanup_repo_relative_input_is_checked_per_worktree(tmp_path, worktrees):
    # 저장소 안 입력 파일은 checkout 마다 그 worktree 의 같은 상대 경로 파일로 재현을 판정한다.
    cache = tmp_path / "cache"
    repo_file = _ENGINE_DIR.parent / "assets" / "sky130_pdk_decl.json"
    assert repo_file.is_file()
    rel = repo_file.relative_to(_repo_top())
    other = tmp_path / "wt_other"
    other_code = _code_fp_of(_fake_worktree(other, {"__init__.py": "", "core/a.py": "A = 2\n"}))
    (other / rel).parent.mkdir(parents=True, exist_ok=True)
    (other / rel).write_bytes(b'{"other worktree": "pdk decl"}')
    worktrees["listing"] = _listing(other)
    kept = _write(cache, _key(sources={"pdk_decl": (str(repo_file), _sha(other / rel))}, engine_code_fp=other_code, spec_fp="k"))
    gone = _write(cache, _key(sources={"pdk_decl": (str(repo_file), "0" * 64)}, engine_code_fp=other_code, spec_fp="g"))
    here = _write(cache, _key(sources={"pdk_decl": (str(repo_file), _sha(repo_file))}, spec_fp="h"))
    _write(cache, _key(sources={"pdk_decl": (str(repo_file), _sha(repo_file))}, spec_fp="now"))
    assert os.path.exists(kept), "다른 worktree 의 현재 파일·코드로 만들 수 있는 키를 지웠다"
    assert not os.path.exists(gone), "어떤 checkout 으로도 만들 수 없는 키를 남겼다"
    assert os.path.exists(here), "이 checkout 의 현재 파일·코드로 만들 수 있는 키를 지웠다"


def test_just_written_file_is_kept_even_if_unreproducible(tmp_path, worktrees):
    inputs = _inputs_dir(tmp_path)
    cache = tmp_path / "cache"
    _write(cache, _key(sources=_sources_now(inputs), spec_fp="old"))
    stale = {"topology": (str(inputs / "topology.json"), "0" * 64)}      # 지금 파일과 다른 sha -- 그래도 방금 쓴 파일
    new = _write(cache, _key(sources=stale, spec_fp="new"))
    assert os.path.exists(new)


def test_cleanup_does_not_run_on_hit(tmp_path, worktrees):
    inputs = _inputs_dir(tmp_path)
    cache = tmp_path / "cache"
    cur = _key(sources=_sources_now(inputs), spec_fp="cur")
    _write(cache, cur)
    old = _write(cache, _key(sources=_sources_now(inputs), spec_fp="old"))
    (inputs / "topology.json").write_bytes(b'{"edited": true}')          # 이제 'old'·'cur' 둘 다 재현 불가
    got = _fetch(cache, cur, _must_not_compute)                          # 적중: 쓰기 없음 -> 정리 없음
    assert got.outcome == OUTCOME_HIT
    assert os.path.exists(old)


def test_cleanup_failure_deletes_nothing(tmp_path, worktrees):
    inputs = _inputs_dir(tmp_path)
    cache = tmp_path / "cache"
    topo_only = {"topology": _sources_now(inputs)["topology"]}
    old_code = _write(cache, _key(sources=topo_only, engine_code_fp="old-code"))   # worktree 나열이 필요한 후보(spec 을 읽지 않은 키)
    worktrees["listing"] = OSError("worktree listing failed")         # 다음 쓰기부터 나열 실패
    old_input = _write(cache, _key(sources=_sources_now(inputs), spec_fp="x"))
    assert os.path.exists(old_code)
    (inputs / "spec.json").write_bytes(b'{"edited": true}')            # old_input 은 이 저장소만으로도 삭제 대상
    got = _fetch(cache, _key(sources=_sources_now(inputs), spec_fp="new"), _counting(_snapshot())[0])
    assert got.snapshot.fp == _snapshot().fp
    assert worktrees["calls"] == 2, "나열 실패 주입이 실제로 판정 경로에 닿지 않았다"
    assert os.path.exists(old_code) and os.path.exists(old_input), "정리 실패인데 일부를 지웠다"


def test_cleanup_skips_other_format_files(tmp_path, worktrees):
    inputs = _inputs_dir(tmp_path)
    cache = tmp_path / "cache"
    old = _write(cache, _key(sources=_sources_now(inputs)))
    stem = os.path.basename(old)[: -len(_SUFFIX)]
    others = ["notes.txt", "readme.md", stem + ".json", stem + _SUFFIX + ".bak", "short" + _SUFFIX]
    for name in others:
        shutil.copyfile(old, cache / name)                               # 내용은 곧 재현 불가가 될 키의 정상 스냅샷
    garbage = cache / ("2" * 64 + _SUFFIX)                               # 형식 이름이지만 읽을 수 없는 파일
    garbage.write_bytes(b"x")
    (inputs / "topology.json").write_bytes(b'{"edited": true}')
    _write(cache, _key(sources=_sources_now(inputs)))
    assert not os.path.exists(old), "대조군: 형식 이름의 재현 불가 파일은 지워져야 한다(정리가 돌았다)"
    for name in others:
        assert (cache / name).exists(), name
    assert garbage.exists()


def test_cleanup_skips_subdirectory_and_files_outside_folder(tmp_path, worktrees):
    inputs = _inputs_dir(tmp_path)
    cache = tmp_path / "cache"
    old = _write(cache, _key(sources=_sources_now(inputs)))
    outside = tmp_path / os.path.basename(old)          # 폴더 밖 같은 이름 파일
    shutil.copyfile(old, outside)
    sub = cache / "nested"
    sub.mkdir()
    inner = sub / os.path.basename(old)                 # 하위 폴더 안 같은 이름 파일
    shutil.copyfile(old, inner)
    dir_like = cache / ("0" * 64 + _SUFFIX)             # 형식 이름을 가진 폴더
    dir_like.mkdir()
    (inputs / "topology.json").write_bytes(b'{"edited": true}')
    _write(cache, _key(sources=_sources_now(inputs)))
    assert not os.path.exists(old), "대조군: 정리가 돌았다"
    assert outside.exists()
    assert inner.exists()
    assert dir_like.is_dir()


def test_cleanup_skips_symlink(tmp_path, worktrees):
    inputs = _inputs_dir(tmp_path)
    cache = tmp_path / "cache"
    old = _write(cache, _key(sources=_sources_now(inputs)))
    target = tmp_path / "elsewhere.json.gz"
    shutil.copyfile(old, target)                        # 링크 대상 = 곧 재현 불가가 될 키의 정상 스냅샷
    link = cache / ("1" * 64 + _SUFFIX)
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError):
        pytest.skip("이 환경은 심볼릭 링크를 만들 수 없다")
    (inputs / "topology.json").write_bytes(b'{"edited": true}')
    _write(cache, _key(sources=_sources_now(inputs)))
    assert os.path.islink(link)
    assert target.exists()
