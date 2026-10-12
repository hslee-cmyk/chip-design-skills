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
* 파일 이름 = `<키 지문>.json.gz`. 키가 다르면 없는 것으로 본다(SC-d).
* U-68: 키가 다른 옛 파일 정리 = 쓰기 시점에, 어떤 checkout 으로도 만들 수 없는 키의 파일만 삭제. 방금 쓴 파일·링크·폴더 밖·형식 다른
  파일 제외, 실패 시 아무것도 지우지 않음.
* §2.4.9 `test_s0_snapshot_roundtrip`: 직렬화 -> 읽기 -> `fp` 비트 동일. 손상 파일은 재계산 후 같은 키로 교체. 등록부 밖 타입은 거부.

기대값 도출: 피검 코드를 부르지 않는다. 비교 기준은 (1) 입력으로 만든 원본 `GraphSnapshot`(기존 core API -- 이번 변경 대상 아님)의
`fp`·필드 메타, (2) 파이썬 값의 타입·`float.hex` 비트, (3) design 이 정한 파일 형식의 최상위 이름과 float 표기, (4) compute 호출 횟수·
파일 바이트·mtime 의 직접 관찰이다.

이름 미정: design 은 모듈 경로(`core/snapshot_codec.py`, `core/type_registry.py`)와 `register(cls)` 만 정한다. 아래 `_PENDING`
한 곳에 개념 -> 임시 이름을 모았다(interface card 가 정하면 이 표만 고친다). 손상·거부 예외 클래스도 design 이 정하지 않았다.
`test_g10_second_run_s0_zero`(§2.4.9 판정 2)는 RunCounters(단계 ②)의 S0 블록 `computes` 계수가 필요해 이 파일에 쓰지 않았다
-- 이 단위에서 판정 가능한 부분(같은 키 두 번째 읽기 = compute 0회·`fp` 동일)은 `test_second_fetch_same_key_is_hit_without_compute`.
"""
import dataclasses
import gzip
import json
import math
import os
import shutil

import pytest

from gmid_engine.core import GraphSnapshot, WriterTable

# design 이 이름을 정하지 않은 API(이름 미정) -- 개념 -> 임시 이름.
_PENDING = {
    "encode": "encode",                  # (snapshot, key) -> bytes(gzip JSON 한 파일의 바이트)
    "decode": "decode",                  # bytes -> GraphSnapshot (검증 포함, 손상·미등록 타입 거부)
    "fetch": "fetch",                    # (directory, key, compute, retained=...) -> GraphSnapshot (hit/miss/corrupt·원자적 쓰기·U-68 정리)
    "s0_key": "s0_key",                  # 키 구성(§2.4.3 (i)~(iii)) -> key 매핑
    "engine_code_fp": "engine_code_fp",  # (root) -> 엔진 코드 지문 (iii)
}
_FETCH_RETAINED_KW = "retained"          # U-68 정리의 '보존 키 집합' 주입 인자(0 인자 callable -> 키 지문 = 파일 이름 앞부분 집합)
_REJECT = (TypeError, ValueError, KeyError)  # 등록부 밖 타입 거부 예외 -- 클래스 이름 미정
_SUFFIX = ".json.gz"
_TOP_LEVEL = {"schema_version", "key", "writers", "block_versions", "records", "fp", "body_sha256"}


def _codec():
    from gmid_engine.core import snapshot_codec   # 모듈 경로는 design §2.4.10·§11 U17 ① 이 정한 것
    return snapshot_codec


def _api(concept):
    mod = _codec()
    name = _PENDING[concept]
    fn = getattr(mod, name, None)
    if fn is None:
        pytest.fail("이름 미정: core.snapshot_codec 에 '%s' 개념의 함수(임시 이름 %r)가 없다" % (concept, name))
    return fn


def _register(cls):
    from gmid_engine.core import type_registry
    type_registry.register(cls)
    return cls


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


def _key(**override):
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
    return _api("s0_key")(**parts)


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


def _fetch(directory, key, compute, retained=None):
    kwargs = {} if retained is None else {_FETCH_RETAINED_KW: retained}
    return _api("fetch")(str(directory), key, compute, **kwargs)


# =====================================================================
# §2.4.9 test_s0_snapshot_roundtrip -- 직렬화 -> 읽기 -> fp 비트 동일(타입 보존)
# =====================================================================

def test_s0_snapshot_roundtrip():
    orig = _snapshot()
    data = _api("encode")(orig, _key())
    got = _api("decode")(data)
    _assert_same_snapshot(orig, got)


def test_roundtrip_through_disk_fetch(tmp_path):
    orig = _snapshot()
    compute, calls = _counting(orig)
    first = _fetch(tmp_path, _key(), compute)
    assert len(calls) == 1
    _assert_same_snapshot(orig, first)
    second = _fetch(tmp_path, _key(), _must_not_compute)
    _assert_same_snapshot(orig, second)


def test_encoding_is_deterministic():
    # 같은 스냅샷·같은 키 -> 같은 바이트(정준 순서, frozenset 정준 순서 포함). gzip 머리의 시각 칸이 고정돼야 한다.
    a = _api("encode")(_snapshot(), _key())
    b = _api("encode")(_snapshot(), _key())
    assert gzip.decompress(a) == gzip.decompress(b)


# ---------- 파일 형식(§2.4.3 '형식' 행) ----------

def _payload(data):
    return json.loads(gzip.decompress(data).decode("utf-8"))


def test_file_is_single_gzip_json_with_design_top_level_fields():
    orig = _snapshot()
    doc = _payload(_api("encode")(orig, _key()))
    assert set(doc) == _TOP_LEVEL
    assert doc["fp"] == orig.fp            # 저장된 fp = 스냅샷 내용 지문


def test_record_fields_carry_value_writer_input_version_write_count():
    doc = _payload(_api("encode")(_snapshot(), _key()))
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
    text = gzip.decompress(_api("encode")(_snapshot(), _key())).decode("utf-8")
    for name in ("f_tenth", "f_subnormal", "f_max"):
        assert float.hex(_FLOAT_PROBES[name]) in text, name
    assert float.hex(-0.0) in text


def test_registered_dataclass_written_with_qualified_type_name():
    text = gzip.decompress(_api("encode")(_snapshot(), _key())).decode("utf-8")
    for cls in (_Point, _Wrap):
        assert '"__type__"' in text
        assert cls.__module__ + "." + cls.__qualname__ in text


def test_key_is_stored_in_file():
    a = _payload(_api("encode")(_snapshot(), _key()))["key"]
    b = _payload(_api("encode")(_snapshot(), _key(pdk_decl_fp="other")))["key"]
    assert isinstance(a, dict) and a != b


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
        _api("encode")(_snapshot_with(value), _key())


def test_fetch_writes_nothing_when_value_type_unregistered(tmp_path):
    compute, _ = _counting(_snapshot_with(_AlsoNeverRegistered(1.0)))
    try:
        _fetch(tmp_path, _key(), compute)
    except _REJECT:
        pass
    assert _files(tmp_path) == []


def test_decode_rejects_unregistered_type_name_without_constructing_it():
    # 등록된 _Point 의 이름 자리를 import 가능한 미등록 클래스 이름으로 바꾼 파일 -> 거부, 그 클래스는 만들어지지 않는다.
    # (body_sha256 의 정확한 범위를 design 이 정하지 않아 무결성 검사로 먼저 거부될 수도 있다 -- 어느 쪽이든 받지 않아야 한다.)
    good = _snapshot_with(_Point(1.0, "x", ()))
    text = gzip.decompress(_api("encode")(good, _key())).decode("utf-8")
    src = _Point.__module__ + "." + _Point.__qualname__
    dst = _NeverRegistered.__module__ + "." + _NeverRegistered.__qualname__
    assert src in text
    tampered = gzip.compress(text.replace(src, dst).encode("utf-8"))
    before = len(_CONSTRUCTED)
    with pytest.raises(Exception):
        _api("decode")(tampered)
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
    assert got.fp == orig.fp
    with open(path, "rb") as fh:
        assert fh.read() == bytes_before            # 검증 통과한 파일은 다시 쓰지 않는다
    assert os.stat(path).st_mtime_ns == mtime_before
    assert _files(tmp_path) == [os.path.basename(path)]


def test_file_name_is_key_fingerprint_with_json_gz_suffix(tmp_path):
    _fetch(tmp_path, _key(), _counting(_snapshot())[0])
    name = os.path.basename(_one_file(tmp_path))
    assert name.endswith(_SUFFIX) and len(name) > len(_SUFFIX)


def test_other_key_is_a_miss(tmp_path):
    compute, calls = _counting(_snapshot())
    _fetch(tmp_path, _key(), compute)
    _fetch(tmp_path, _key(spec_fp="other"), compute)
    assert len(calls) == 2
    assert len(_files(tmp_path)) == 2


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
    got = _fetch(tmp_path, _key(), compute)
    assert len(calls) == 2, "손상 파일을 받아들였다(재계산 안 함)"
    _assert_same_snapshot(orig, got)
    assert _files(tmp_path) == [os.path.basename(path)], "같은 키 파일을 교체하지 않고 새 이름을 만들었다"
    again = _fetch(tmp_path, _key(), _must_not_compute)   # 교체된 파일은 검증을 통과한다
    _assert_same_snapshot(orig, again)


def test_corrupt_file_rejected_by_decode():
    data = _api("encode")(_snapshot(), _key())
    doc = json.loads(gzip.decompress(data).decode("utf-8"))
    doc["fp"] = "f" * 64
    with pytest.raises(Exception):
        _api("decode")(gzip.compress(json.dumps(doc).encode("utf-8")))


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
        got = _fetch(tmp_path, _key(), compute)
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
# 키 구성(§2.4.3 키 (i)~(iii), §2.4.12 Q1 PDK 선언 해시)
# =====================================================================

_KEY_PARTS = ("topology_fp", "lut_fp", "spec_fp", "pdk_decl_fp", "rule_code_fp", "metric_code_fp",
              "structure_facts_fp", "engine_code_fp")


def test_same_parts_give_same_key():
    assert _key() == _key()


@pytest.mark.parametrize("part", _KEY_PARTS)
def test_each_key_part_changes_key(part):
    assert _key(**{part: "changed"}) != _key()


def test_pdk_decl_hash_is_required_key_part():
    parts = {p: "x" for p in _KEY_PARTS if p != "pdk_decl_fp"}
    with pytest.raises(TypeError):
        _api("s0_key")(**parts)


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


# ---------- 엔진 코드 지문 (iii) ----------

_TREE = {
    "__init__.py": "X = 0\n",
    "core/__init__.py": "",
    "core/a.py": "A = 1\n",
    "core/CONTRACT.md": "contract\n",
    "lut/l.py": "L = 1\n",
    "report/b.py": "B = 1\n",
    "pipeline/c.py": "C = 1\n",
    "layout/d.py": "D = 1\n",
    "convergence/e.py": "E = 1\n",
    "authoring/f.py": "F = 1\n",
    "tests/__init__.py": "",
    "tests/conftest.py": "T = 0\n",
    "tests/core/test_a.py": "def test_a():\n    pass\n",
}


def _make_tree(root):
    for rel, text in _TREE.items():
        p = root.joinpath(*rel.split("/"))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
    return root


def _code_fp(root):
    return _api("engine_code_fp")(str(root))


def test_engine_code_fp_is_independent_of_checkout_location(tmp_path):
    # U-68: 다른 worktree 의 같은 코드로 같은 키를 만들 수 있어야 보존 판정이 성립한다 -> 위치 무관.
    a = _make_tree(tmp_path / "wt_a" / "gmid_engine")
    b = _make_tree(tmp_path / "wt_b" / "deeper" / "gmid_engine")
    assert _code_fp(a) == _code_fp(b)


@pytest.mark.parametrize("rel", ["core/a.py", "lut/l.py", "report/b.py", "pipeline/c.py", "layout/d.py",
                                 "convergence/e.py", "authoring/f.py"])
def test_engine_code_fp_changes_when_any_non_test_package_file_changes(tmp_path, rel):
    root = _make_tree(tmp_path / "gmid_engine")
    before = _code_fp(root)
    p = root.joinpath(*rel.split("/"))
    p.write_bytes(p.read_bytes() + b"# edit\n")
    assert _code_fp(root) != before


def test_engine_code_fp_changes_when_non_test_file_added(tmp_path):
    root = _make_tree(tmp_path / "gmid_engine")
    before = _code_fp(root)
    (root / "report" / "new_module.py").write_bytes(b"N = 1\n")
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
    assert _code_fp(root) == before


# =====================================================================
# U-68 옛 파일 정리(§2.4.12 Q2, §3.10.11) -- 쓰기 시점, 보존 키 밖만, 방금 쓴 파일·링크·폴더 밖·형식 다른 파일 제외, 실패 시 0
# 보존 키 집합은 주입한다(저장소·모든 worktree 를 실제로 훑는 일은 이 단위 test 범위 밖).
# =====================================================================

def _stem(path):
    return os.path.basename(path)[: -len(_SUFFIX)]


def _write_old(directory, **key_override):
    """다른 키의 정상 스냅샷 파일 하나를 만들고 그 경로를 돌려준다."""
    before = set(_files(directory))
    _fetch(directory, _key(**key_override), _counting(_snapshot())[0], retained=lambda: set())
    added = sorted(set(_files(directory)) - before)
    assert len(added) == 1
    return os.path.join(directory, added[0])


def _new_name(directory, before):
    added = sorted(set(_files(directory)) - set(before))
    assert len(added) == 1
    return added[0]


def test_cleanup_removes_unreproducible_key_file_at_write(tmp_path):
    old = _write_old(tmp_path, spec_fp="old")
    before = _files(tmp_path)
    _fetch(tmp_path, _key(spec_fp="new"), _counting(_snapshot())[0], retained=lambda: set())
    new = _new_name(tmp_path, before)
    assert not os.path.exists(old)
    assert os.path.exists(os.path.join(tmp_path, new)), "방금 쓴 파일은 보존 키 밖이어도 남긴다"


def test_cleanup_keeps_reproducible_key_file(tmp_path):
    old = _write_old(tmp_path, spec_fp="old")
    _fetch(tmp_path, _key(spec_fp="new"), _counting(_snapshot())[0], retained=lambda: {_stem(old)})
    assert os.path.exists(old)


def test_cleanup_does_not_run_on_hit(tmp_path):
    _fetch(tmp_path, _key(spec_fp="cur"), _counting(_snapshot())[0], retained=lambda: set())
    old = _write_old(tmp_path, spec_fp="old")          # 'cur' 파일은 여기서 지워질 수 있다 -> 다시 만든다
    _fetch(tmp_path, _key(spec_fp="cur"), _counting(_snapshot())[0], retained=lambda: {_stem(old)})
    assert os.path.exists(old)
    _fetch(tmp_path, _key(spec_fp="cur"), _must_not_compute, retained=lambda: set())   # 적중: 쓰기 없음 -> 정리 없음
    assert os.path.exists(old)


def test_cleanup_failure_deletes_nothing(tmp_path):
    old = _write_old(tmp_path, spec_fp="old")

    def failing():
        raise OSError("worktree listing failed")

    got = _fetch(tmp_path, _key(spec_fp="new"), _counting(_snapshot())[0], retained=failing)
    assert got.fp == _snapshot().fp
    assert os.path.exists(old)


def test_cleanup_skips_other_format_files(tmp_path):
    old = _write_old(tmp_path, spec_fp="old")
    others = ["notes.txt", "readme.md", _stem(old) + ".json", _stem(old) + _SUFFIX + ".bak"]
    for name in others:
        (tmp_path / name).write_bytes(b"x")
    _fetch(tmp_path, _key(spec_fp="new"), _counting(_snapshot())[0], retained=lambda: set())
    for name in others:
        assert (tmp_path / name).exists(), name


def test_cleanup_skips_subdirectory_and_files_outside_folder(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    old = _write_old(cache, spec_fp="old")
    outside = tmp_path / os.path.basename(old)          # 폴더 밖 같은 이름 파일
    shutil.copyfile(old, outside)
    sub = cache / "nested"
    sub.mkdir()
    inner = sub / os.path.basename(old)                 # 하위 폴더 안 같은 이름 파일
    shutil.copyfile(old, inner)
    dir_like = cache / ("0" * 64 + _SUFFIX)             # 형식 이름을 가진 폴더
    dir_like.mkdir()
    _fetch(cache, _key(spec_fp="new"), _counting(_snapshot())[0], retained=lambda: set())
    assert outside.exists()
    assert inner.exists()
    assert dir_like.is_dir()


def test_cleanup_skips_symlink(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    old = _write_old(cache, spec_fp="old")
    target = tmp_path / "elsewhere.bin"
    target.write_bytes(b"keep")
    link = cache / ("1" * 64 + _SUFFIX)
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError):
        pytest.skip("이 환경은 심볼릭 링크를 만들 수 없다")
    _fetch(cache, _key(spec_fp="new"), _counting(_snapshot())[0], retained=lambda: {_stem(old)})
    assert os.path.islink(link)
    assert target.read_bytes() == b"keep"
