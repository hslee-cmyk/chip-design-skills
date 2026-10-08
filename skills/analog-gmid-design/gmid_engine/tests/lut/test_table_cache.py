"""`TableCache` -- lut/CONTRACT.md 2.1(파생 표 디스크 캐시, 사용자 승인 2026-10-08 "tol_V표를 파일로 캐시해.",
정리 규칙 "그 방식으로 진행해", 삭제 코드 허용 "캐시 정리 삭제 코드 넣는 것을 허용해") 의 test 작성자용 불변식 (1)~(8).

oracle 표기(00-common 8.1 규칙 10) -- 기대값마다 주석에 적는다:
  (a) 구성으로 정답이 정해진 합성 입력(같은 입력 두 번 = 적중, 한 비트 바꾼 입력 = 미스, 일부러 깨뜨린 파일 = 깨짐 등)
  (b) 다른 방법 -- 캐시를 끈 계산(`TableCache(None)`)과 비트 대조, 파일 형식을 계약 문장대로 직접 파싱·sha256 재계산
  (d) 계약 선언값(CONTRACT 2.1 문장: 이벤트 이름, 파일 이름 형식, 정리 대상 규칙)
피검 함수로 기대값을 만들지 않는다 -- 기대값은 compute 호출 횟수·파일 목록·캐시 끔 결과·계약 문장이다.

모든 디스크 test 는 임시 폴더(`tmp_path`)에서만 한다 -- 실제 캐시 폴더(설정 default)는 건드리지 않는다
(`TableCache.default()` 를 부르는 test 는 `GMID_LUT_TABLE_CACHE_DIR` 를 임시 폴더로 덮어쓴 뒤에만 부른다).
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import multiprocessing
import os
import pickle
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import warnings
from pathlib import Path

import numpy as np
import pytest

import gmid_engine.lut as lut_pkg
from gmid_engine.lut import (LutMemo, curve_report, tol_v_table, tol_vdsat_table, widths)

from .conftest import (MID_L_SOURCE, REALDATA_MARKER, copy_tree, mid_point_arrays, standard_toy_slices)

ENV = "GMID_LUT_TABLE_CACHE_DIR"                      # (d) CONTRACT 2.1 위치: 설정 table_cache.env 이름
MAGIC = b"GMIDTBL1\n"                                  # (d) CONTRACT 2.1 파일 머리
EVENTS = ("hit", "miss", "stale_key", "corrupt", "read_error", "write", "write_error", "unstorable", "disabled",
          "cleanup_removed", "cleanup_skipped", "cleanup_failsafe")   # (d) CONTRACT 2.1 이벤트 목록
NAME_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)-([0-9a-f]{64})-([0-9a-f]{64})\.tbl$")   # (d) 2.1 칸 파일 이름 형식
ENGINE_DIR = Path(__file__).resolve().parents[2]       # .../gmid_engine
FN = "tol_v_table"


# ---------------------------------------------------------------------------
# 공통
# ---------------------------------------------------------------------------

def hx(label):
    """임의 64자 소문자 hex(구성상 어느 설정도 가리키지 않는 자료 id·지문 자리에 쓴다)."""
    return hashlib.sha256(label.encode()).hexdigest()


LFP = hx("lut-fp")
DID = hx("data-id")


class Counter:
    def __init__(self, value):
        self.value = value
        self.n = 0

    def __call__(self):
        self.n += 1
        return self.value


def parse_file(data):
    """(b) CONTRACT 2.1 파일 형식을 직접 파싱: MAGIC + 키(64 hex) + \\n + 본문 sha256(64 hex) + \\n + pickle 본문."""
    assert data.startswith(MAGIC)
    rest = data[len(MAGIC):]
    key, nl1, h, nl2, body = rest[:64], rest[64:65], rest[65:129], rest[129:130], rest[130:]
    assert nl1 == b"\n" and nl2 == b"\n"
    assert re.fullmatch(rb"[0-9a-f]{64}", key) and re.fullmatch(rb"[0-9a-f]{64}", h)
    assert hashlib.sha256(body).hexdigest().encode() == h
    return key.decode(), body


def assert_bit_identical(a, b, where="root"):
    """(b) 속성 전부 같고 float 은 8바이트 같다(NaN 포함). dataclass·tuple·list·Mapping·ndarray·그 밖 객체(__reduce_ex__ 상태)."""
    assert type(a) is type(b), (where, type(a), type(b))
    if isinstance(a, float):
        assert struct.pack("<d", a) == struct.pack("<d", b), (where, a, b)
    elif isinstance(a, np.ndarray):
        assert a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes(), where
    elif isinstance(a, np.generic):
        assert a.dtype == b.dtype and a.tobytes() == b.tobytes(), where
    elif isinstance(a, type) or callable(a):
        assert a is b, where
    elif isinstance(a, (str, bytes, int, bool, type(None))):
        assert a == b, (where, a, b)
    elif isinstance(a, (tuple, list)):
        assert len(a) == len(b), where
        for i, (x, y) in enumerate(zip(a, b)):
            assert_bit_identical(x, y, "%s[%d]" % (where, i))
    elif isinstance(a, (dict, frozenset, set)):
        if isinstance(a, dict):
            assert list(a.keys()) == list(b.keys()), where
            for k in a:
                assert_bit_identical(a[k], b[k], "%s[%r]" % (where, k))
        else:
            assert a == b, where
    elif dataclasses.is_dataclass(a):
        for f in dataclasses.fields(a):
            assert_bit_identical(getattr(a, f.name), getattr(b, f.name), "%s.%s" % (where, f.name))
    else:
        ra, rb = a.__reduce_ex__(4), b.__reduce_ex__(4)
        assert_bit_identical(tuple(ra[1:]), tuple(rb[1:]), where + "<reduce>")


def tbl_files(d):
    return sorted(n for n in os.listdir(d) if n.endswith(".tbl"))


@pytest.fixture
def sd():
    """짧은 임시 폴더(시스템 임시 폴더 바로 아래). 칸 파일 이름이 약 150자라 test 가 직접 하는 파일 조작(Path.read_bytes 등,
    확장 길이 접두 없음)이 깊은 경로에서 MAX_PATH 에 걸리지 않게 한다. 깊은 경로 자체의 캐시 동작은
    test_long_windows_path_* 가 따로 잰다(CONTRACT 2.1 'Windows 경로 길이')."""
    d = tempfile.mkdtemp(prefix="gtc")
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def TC(toy, monkeypatch, tmp_path):
    """TableCache 클래스. 공개 API(`gmid_engine.lut.TableCache`)가 없으면 공개 객체 `LutMemo(...).table_cache` 의 형으로 얻는다
    (CONTRACT 0절 test import 규칙 -- 파일 모듈 직접 import 금지). 그 경로의 default() 는 임시 폴더로 돌린다."""
    cls = getattr(lut_pkg, "TableCache", None)
    if cls is None:
        monkeypatch.setenv(ENV, str(tmp_path / "_tc_probe"))
        cls = type(LutMemo(toy, point=1, curve=1, root=1).table_cache)
    return cls


def test_table_cache_is_public_api():
    """(d) CONTRACT 0절: 진입점 `TableCache`(table_cache.py), 2.1: `LutMemo(..., table_cache=TableCache(None))` 로 끈다 --
    test·호출부는 `from gmid_engine.lut import ...` 만 쓰므로 `__all__` 에 있어야 한다."""
    assert "TableCache" in lut_pkg.__all__
    assert hasattr(lut_pkg, "TableCache")


# ---------------------------------------------------------------------------
# (1) 구성요소별 적중/미스
# ---------------------------------------------------------------------------

def _inputs():
    return (np.arange(12, dtype=np.float64).reshape(3, 4), ("nmos", 100), {"a": 1.5, "b": (2.0, 3.0)})


def test_miss_then_hit_compute_once(TC, tmp_path, sd):
    t = TC(str(sd / "c"))
    c = Counter(("table", 1.25, (3.5,)))
    v1 = t.fetch(LFP, DID, FN, ("nmos", 100), _inputs(), ("s",), c)
    # (a) 빈 폴더 첫 호출 = 미스 + 쓰기, compute 1회
    assert c.n == 1 and v1 == ("table", 1.25, (3.5,))
    assert t.events == (("miss", FN), ("write", FN))
    path = t.path_of(LFP, DID, FN, ("nmos", 100))
    assert os.path.isfile(path) and tbl_files(sd / "c") == [os.path.basename(path)]
    # (d) 2.1 파일 이름 = <fn_name>-<자료 id>-<64 hex>.tbl, 자료 id 칸 = 넘긴 data_id
    m = NAME_RE.match(os.path.basename(path))
    assert m and m.group(1) == FN and m.group(2) == DID
    # (b) 파일 형식 직접 파싱: 키 = key_digest, 본문 = 값의 pickle
    key, body = parse_file(Path(path).read_bytes())
    assert key == t.key_digest(LFP, FN, ("nmos", 100), _inputs(), ("s",))
    assert pickle.loads(body) == v1
    # (a) 같은 객체·새 객체 모두 적중, compute 0회
    for obj in (t, TC(str(sd / "c"))):
        before = len(obj.events)
        c2 = Counter(("other",))
        assert obj.fetch(LFP, DID, FN, ("nmos", 100), _inputs(), ("s",), c2) == v1
        assert c2.n == 0 and obj.events[before:] == (("hit", FN),)
    assert dict(t.stats()) == {"hit": 1, "miss": 1, "write": 1}
    # (d) stats 는 이벤트 이름 정렬
    assert [k for k, _ in t.stats()] == sorted(k for k, _ in t.stats())


def _flip_bit(arr):
    out = arr.copy()
    out.reshape(-1).view(np.uint8)[5] ^= 1          # 한 원소의 한 비트(연속 배열 copy 의 평탄 view)
    return out


@pytest.mark.parametrize("change", [
    "array_bit_flip", "array_dtype_same_bytes", "array_shape_same_bytes", "tuple_element", "mapping_value",
    "settings",
])
def test_component_change_recomputes_and_overwrites_same_cell(TC, tmp_path, change, sd):
    """(a) 2.1 불변식 (1): 입력 내용(배열 dtype·shape·바이트, tuple·Mapping 내용)·settings 중 하나를 바꾸면 같은 칸(같은 경로)에서
    stale_key -> compute 1회 -> 덮어쓰기. 이어서 바꾼 쪽으로 다시 부르면 적중."""
    d = sd / "c"
    t = TC(str(d))
    base_in, base_set = _inputs(), ("s",)
    t.fetch(LFP, DID, FN, ("nmos", 100), base_in, base_set, Counter(("old",)))
    path = t.path_of(LFP, DID, FN, ("nmos", 100))
    old_key, _ = parse_file(Path(path).read_bytes())
    arr, tup, mp = base_in
    new_in, new_set = base_in, base_set
    if change == "array_bit_flip":
        new_in = (_flip_bit(arr), tup, mp)
    elif change == "array_dtype_same_bytes":
        new_in = (arr.view(np.int64), tup, mp)
    elif change == "array_shape_same_bytes":
        new_in = (arr.reshape(4, 3), tup, mp)
    elif change == "tuple_element":
        new_in = (arr, ("nmos", 101), mp)
    elif change == "mapping_value":
        new_in = (arr, tup, {"a": 1.5, "b": (2.0, 3.0000000000000004)})
    else:
        new_set = ("s2",)
    t2 = TC(str(d))
    c = Counter(("new",))
    assert t2.fetch(LFP, DID, FN, ("nmos", 100), new_in, new_set, c) == ("new",)
    assert c.n == 1
    ev = [e for e, _ in t2.events]
    assert "stale_key" in ev and "write" in ev and "hit" not in ev
    # 같은 칸(경로 불변), 파일 하나, 키가 새 키로 바뀜
    assert t2.path_of(LFP, DID, FN, ("nmos", 100)) == path and tbl_files(d) == [os.path.basename(path)]
    new_key, body = parse_file(Path(path).read_bytes())
    assert new_key != old_key and new_key == t2.key_digest(LFP, FN, ("nmos", 100), new_in, new_set)
    assert pickle.loads(body) == ("new",)
    c3 = Counter(("x",))
    assert TC(str(d)).fetch(LFP, DID, FN, ("nmos", 100), new_in, new_set, c3) == ("new",) and c3.n == 0
    # 옛 구성으로 돌아가면 다시 stale (칸 하나 -- 키가 다른 표를 쓰지 않는다)
    c4 = Counter(("old",))
    assert TC(str(d)).fetch(LFP, DID, FN, ("nmos", 100), base_in, base_set, c4) == ("old",) and c4.n == 1


@pytest.mark.parametrize("which", ["key", "fn_name", "lut_fp", "data_id"])
def test_cell_identity_components_give_other_file(TC, tmp_path, which, sd):
    """(a)(d) 2.1 칸 = (lut.fp, 자료 id, fn_name, key): 하나라도 다르면 다른 파일(미스, compute 1회), 원래 파일은 그대로."""
    d = sd / "c"
    t = TC(str(d))
    t.fetch(LFP, DID, FN, ("nmos", 100), _inputs(), (), Counter(1))
    args = {"lut_fp": LFP, "data_id": DID, "fn_name": FN, "key": ("nmos", 100)}
    args[which] = {"key": ("nmos", 200), "fn_name": "curve_report", "lut_fp": hx("other-fp"),
                   "data_id": hx("other-id")}[which]
    c = Counter(2)
    v = t.fetch(args["lut_fp"], args["data_id"], args["fn_name"], args["key"], _inputs(), (), c)
    assert v == 2 and c.n == 1
    assert t.events[-2:] == (("miss", args["fn_name"]), ("write", args["fn_name"]))
    assert len(tbl_files(d)) == 2
    p = t.path_of(args["lut_fp"], args["data_id"], args["fn_name"], args["key"])
    assert NAME_RE.match(os.path.basename(p)).group(2) == args["data_id"]


# --- 코드 버전 = lut·core 패키지 .py 소스 바이트(복사한 패키지를 하위 프로세스로 돌려 바꾼다) -------------------------

_CODE_PROBE = r'''
import importlib, json, sys
sys.path.insert(0, sys.argv[1])
import numpy as np
import gmid_engine
cls = getattr(importlib.import_module(sys.argv[3]), sys.argv[4])
t = cls(sys.argv[2])
calls = []
v = t.fetch("%s", "%s", "tol_v_table", ("nmos", 1), (np.arange(4.0),), ("s",), lambda: calls.append(1) or ("v", 1.5))
with open(sys.argv[5], "w", encoding="utf-8") as f:
    json.dump({"calls": len(calls), "events": [list(e) for e in t.events], "v": list(v),
               "engine": gmid_engine.__file__}, f)
''' % (LFP, DID)


def _copy_engine(dst_parent):
    dst = Path(dst_parent) / "gmid_engine"
    shutil.copytree(ENGINE_DIR, dst, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    return dst


def _append(path, text):
    with open(path, "ab") as f:
        f.write(text)


def test_code_version_change_recomputes(TC, tmp_path, sd):
    """(a) 2.1 키 = 코드 버전(lut·core `.py` 소스 바이트 전부) + ...: 복사한 엔진에서 lut 또는 core 의 .py 한 파일 끝에 주석 한 줄을
    더하면 stale_key -> compute 1회, 같은 코드로 다시 부르면 적중. lut·core 밖 .py·.py 가 아닌 파일 변경은 키에 없다(적중)."""
    pkg_parent = tmp_path / "pkg"
    eng = _copy_engine(pkg_parent)
    cache = sd / "cache"
    script = tmp_path / "probe.py"
    script.write_text(_CODE_PROBE, encoding="utf-8")
    runs = []

    def run():
        out = tmp_path / ("out%d.json" % len(runs))
        r = subprocess.run([sys.executable, str(script), str(pkg_parent), str(cache), TC.__module__, TC.__qualname__,
                            str(out)], capture_output=True, text=True, timeout=300)
        assert r.returncode == 0, r.stderr
        res = json.loads(out.read_text(encoding="utf-8"))
        assert Path(res["engine"]).resolve().is_relative_to(eng.resolve())       # 복사본을 import 했는가
        assert res["v"] == ["v", 1.5]
        runs.append(res)
        return res["calls"], [e for e, _ in res["events"]]

    assert run() == (1, ["miss", "write"])
    assert run() == (0, ["hit"])
    lut_py = sorted(p for p in (eng / "lut").glob("*.py"))[0]
    _append(lut_py, b"\n# code version probe (lut)\n")
    calls, ev = run()
    assert calls == 1 and "stale_key" in ev and "write" in ev
    assert run() == (0, ["hit"])
    core_py = sorted(p for p in (eng / "core").glob("*.py"))[0]
    _append(core_py, b"\n# code version probe (core)\n")
    calls, ev = run()
    assert calls == 1 and "stale_key" in ev
    assert run() == (0, ["hit"])
    # lut·core 밖 패키지 .py, lut 의 .md -> 키 불변(적중)
    others = sorted(p for p in eng.iterdir() if p.is_dir() and p.name not in ("lut", "core") and any(p.glob("*.py")))
    assert others, "lut·core 밖 하위 패키지가 없다"
    _append(sorted(others[0].glob("*.py"))[0], b"\n# not lut/core\n")
    _append(eng / "lut" / "CONTRACT.md", b"\nprobe\n")
    assert run() == (0, ["hit"])


# ---------------------------------------------------------------------------
# (2) 깨짐
# ---------------------------------------------------------------------------

def _valid_file(TC, d, value=("table", 2.5, (1.0, float("nan")))):
    t = TC(str(d))
    t.fetch(LFP, DID, FN, ("k",), _inputs(), (), Counter(value))
    path = Path(t.path_of(LFP, DID, FN, ("k",)))
    return path, path.read_bytes(), value


def _corrupt_cases(data):
    """(a) 계약 형식(2.1)으로 정답이 '깨짐'인 파일 내용."""
    key_start = len(MAGIC)
    hash_start = key_start + 65
    body_start = hash_start + 65
    bad_body = b"definitely not a pickle stream"
    return {
        "truncated_body": data[:(body_start + len(data)) // 2],
        "truncated_header": data[:key_start + 10],
        "body_byte_flipped": data[:-1] + bytes([data[-1] ^ 0xFF]),
        "bad_magic": b"X" + data[1:],
        "header_hash_zeroed": data[:hash_start] + b"0" * 64 + data[hash_start + 64:],
        "header_key_not_hex": data[:key_start] + b"Z" * 64 + data[key_start + 64:],
        "empty": b"",
        "garbage": bytes(range(256)) * 7,
        "unpicklable_body_valid_hash": data[:hash_start] + hashlib.sha256(bad_body).hexdigest().encode() + b"\n"
        + bad_body,
    }


@pytest.mark.parametrize("case", ["truncated_body", "truncated_header", "body_byte_flipped", "bad_magic",
                                  "header_hash_zeroed", "header_key_not_hex", "empty", "garbage",
                                  "unpicklable_body_valid_hash"])
def test_corrupt_file_recomputed_and_replaced(TC, tmp_path, case, sd):
    """(a)(d) 2.1 불변식 (2): 깨진 파일 -> 예외 없음, RuntimeWarning, 이벤트 corrupt, compute 1회, 깨끗한 파일로 교체."""
    d = sd / "c"
    path, data, value = _valid_file(TC, d)
    path.write_bytes(_corrupt_cases(data)[case])
    t = TC(str(d))
    c = Counter(value)
    with pytest.warns(RuntimeWarning):
        v = t.fetch(LFP, DID, FN, ("k",), _inputs(), (), c)
    assert c.n == 1 and v is value
    assert ("corrupt", FN) in t.events and ("write", FN) in t.events and ("hit", FN) not in t.events
    key, body = parse_file(path.read_bytes())                       # (b) 교체된 파일이 형식대로 온전하다
    assert key == t.key_digest(LFP, FN, ("k",), _inputs(), ())
    assert_bit_identical(pickle.loads(body), value)
    assert tbl_files(d) == [path.name]                             # 임시 파일 안 남음
    c2 = Counter(None)
    assert_bit_identical(TC(str(d)).fetch(LFP, DID, FN, ("k",), _inputs(), (), c2), value)
    assert c2.n == 0


def test_other_valid_key_is_stale_without_warning(TC, tmp_path, sd):
    """(d) 2.1: 형식은 맞는데 키가 다르면 stale_key(경고 없음), 다시 계산해 덮어쓴다 -- 그 파일 값을 쓰지 않는다."""
    d = sd / "c"
    path, data, value = _valid_file(TC, d)
    ks = len(MAGIC)
    other_key = hx("someone else's key").encode()
    path.write_bytes(data[:ks] + other_key + data[ks + 64:])
    t = TC(str(d))
    c = Counter(("fresh",))
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        v = t.fetch(LFP, DID, FN, ("k",), _inputs(), (), c)
    assert v == ("fresh",) and c.n == 1
    ev = [e for e, _ in t.events]
    assert "stale_key" in ev and "corrupt" not in ev and "hit" not in ev
    assert pickle.loads(parse_file(path.read_bytes())[1]) == ("fresh",)


def test_write_failure_returns_result_no_temp_left(TC, tmp_path, sd):
    """(a) 2.1 불변식 (3): 목적 경로를 폴더가 차지해 교체가 불가능 -> 예외 없음, write_error, 계산 결과 그대로,
    폴더에 임시 파일이 남지 않는다. 다음 호출도 같은 값(읽기 실패가 결과를 바꾸지 않는다)."""
    d = sd / "c"
    t = TC(str(d))
    path = Path(t.path_of(LFP, DID, FN, ("k",)))
    path.mkdir(parents=True)
    value = ("v", 3.0)
    for i in range(2):
        c = Counter(value)
        assert t.fetch(LFP, DID, FN, ("k",), _inputs(), (), c) is value and c.n == 1
    assert ("write_error", FN) in t.events and ("write", FN) not in t.events
    assert os.listdir(d) == [path.name] and path.is_dir() and os.listdir(path) == []


# ---------------------------------------------------------------------------
# (3) 원자성 -- 여러 프로세스가 동시에 쓰고 읽어도 부분 파일을 보지 않는다
# ---------------------------------------------------------------------------

_N_PAYLOAD = 200_000


def _payload(s):
    """settings 마다 다른 큰 값(pickle 약 1.8 MB) -- 쓰기 창을 넓힌다."""
    return (s, tuple(float(s) + i * 1e-3 for i in range(_N_PAYLOAD)))


def _mp_writer(cls, d, n, q):
    """칸 하나에 settings 0/1 을 번갈아 써서 매번 stale -> 덮어쓰기."""
    bad = 0
    t = cls(d)
    for i in range(n):
        s = i % 2
        v = t.fetch(LFP, DID, FN, ("k",), (np.arange(8.0),), (s,), lambda s=s: _payload(s))
        bad += v != _payload(s)
    q.put(("writer", bad, [e for e, _ in t.events]))


def _mp_reader(cls, d, n, q):
    """fetch 로 읽는 프로세스: 받은 값은 언제나 그 settings 의 값, corrupt 는 한 번도 없어야 한다(부분 파일 = corrupt)."""
    bad = 0
    t = cls(d)
    for i in range(n):
        s = (i + 1) % 2
        v = t.fetch(LFP, DID, FN, ("k",), (np.arange(8.0),), (s,), lambda s=s: _payload(s))
        bad += v != _payload(s)
    q.put(("reader", bad, [e for e, _ in t.events]))


def test_concurrent_writers_never_expose_partial_file(TC, tmp_path, sd):
    """(a)(b) 2.1 불변식 (3): writer 3 + fetch reader 1 프로세스(spawn)와 이 프로세스의 원시 읽기가 동시에 돈다.
    원시 읽기로 연 파일은 전부 형식·본문 sha256 이 맞는 완성 파일(b: 형식 직접 파싱), reader 의 corrupt 0, 값 불일치 0,
    끝난 뒤 폴더엔 칸 파일 하나만(임시 파일 0)."""
    d = sd / "c"
    d.mkdir()
    t = TC(str(d))
    path = t.path_of(LFP, DID, FN, ("k",))
    ctx = multiprocessing.get_context("spawn")
    q = ctx.Queue()
    procs = [ctx.Process(target=_mp_writer, args=(TC, str(d), 12, q)) for _ in range(3)]
    procs.append(ctx.Process(target=_mp_reader, args=(TC, str(d), 12, q)))
    for p in procs:
        p.start()
    complete = partial = 0
    deadline = time.monotonic() + 600
    while any(p.is_alive() for p in procs) and time.monotonic() < deadline:
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:                       # 아직 없음·교체 중 잠김 -- 부분 파일이 아니다
            continue
        try:
            parse_file(data)
            complete += 1
        except AssertionError:
            partial += 1
    results = [q.get(timeout=600) for _ in procs]
    for p in procs:
        p.join(timeout=60)
        assert p.exitcode == 0
    assert partial == 0
    assert complete > 0, "원시 읽기가 완성 파일을 한 번도 보지 못했다(경쟁 창이 없음)"
    for role, bad, ev in results:
        assert bad == 0, role
        assert "corrupt" not in ev, (role, ev)
    writers = [ev for role, _, ev in results if role == "writer"]
    assert sum(ev.count("write") for ev in writers) >= 3
    assert os.listdir(d) == [os.path.basename(path)]
    parse_file(Path(path).read_bytes())


# ---------------------------------------------------------------------------
# (4) 비트 동일 -- toy(모든 (kind, w_key)) + 실 LUT 작은 조각
# ---------------------------------------------------------------------------

def _tables(memo, lut, kw_pairs):
    out = [("curve_report", curve_report(memo))]
    for kind, wk in kw_pairs:
        out.append(("tol_v_table", tol_v_table(memo, kind, wk)))
        out.append(("tol_vdsat_table", tol_vdsat_table(memo, kind, wk)))
    return out


def _mid_lut(mid_toy_build):
    return mid_toy_build("bit", mid=mid_point_arrays((3.5e-6,), l_source=MID_L_SOURCE)).load()


def test_bit_identity_toy_all_slices(TC, mid_toy_build, tmp_path, sd):
    """(b) 2.1 불변식 (4): 모든 (kind, w_key) 의 tol_v_table·tol_vdsat_table 과 curve_report 가 캐시 끔 / 켬(미스·쓰기) / 적중
    (새 memo·새 객체)에서 속성 전부·float 바이트 같다. 적중 쪽은 compute 가 없어야 하므로 이벤트가 hit 뿐이다."""
    lut = _mid_lut(mid_toy_build)
    pairs = sorted(lut.slice_map)
    off = _tables(LutMemo(lut, point=64, curve=64, root=64, table_cache=TC(None)), lut, pairs)
    d = sd / "c"
    on_cache = TC(str(d))
    on = _tables(LutMemo(lut, point=64, curve=64, root=64, table_cache=on_cache), lut, pairs)
    assert {e for e, _ in on_cache.events} == {"miss", "write"}
    assert sorted(NAME_RE.match(n).group(1) for n in tbl_files(d)) == sorted(n for n, _ in off)
    hit_cache = TC(str(d))
    hit = _tables(LutMemo(lut, point=64, curve=64, root=64, table_cache=hit_cache), lut, pairs)
    assert {e for e, _ in hit_cache.events} == {"hit"} and len(hit_cache.events) == len(off)
    for (n0, a), (n1, b), (n2, c) in zip(off, on, hit):
        assert n0 == n1 == n2
        assert_bit_identical(a, b, n0 + ":on")
        assert_bit_identical(a, c, n0 + ":hit")


@pytest.mark.lut_realdata
def test_bit_identity_real_lut_slice(TC, real_lut, tmp_path, sd):
    """(b) 실 LUT v2 작은 조각: nmos 최소 폭의 tol_v_table, nmos·pmos 최소 폭의 tol_vdsat_table, curve_report(전체) --
    캐시 끔 / 미스 / 적중 비트 동일. (실데이터 마커 lut_realdata: 경로가 없으면 conftest 가 FAIL)"""
    assert REALDATA_MARKER == "lut_realdata"
    nk = widths(real_lut, "nmos")[0]
    pk = widths(real_lut, "pmos")[0]

    def run(cache):
        m = LutMemo(real_lut, point=4096, curve=4096, root=4096, table_cache=cache)
        return [("tol_v_table", tol_v_table(m, "nmos", nk)),
                ("tol_vdsat_table", tol_vdsat_table(m, "nmos", nk)),
                ("tol_vdsat_table", tol_vdsat_table(m, "pmos", pk)),
                ("curve_report", curve_report(m))]
    off = run(TC(None))
    d = sd / "c"
    c_on = TC(str(d))
    on = run(c_on)
    assert {e for e, _ in c_on.events} == {"miss", "write"}
    c_hit = TC(str(d))
    hit = run(c_hit)
    assert c_hit.events == tuple(("hit", n) for n, _ in off)
    for (n, a), (_, b), (_, c) in zip(off, on, hit):
        assert_bit_identical(a, b, n + ":on")
        assert_bit_identical(a, c, n + ":hit")


# ---------------------------------------------------------------------------
# (5) 환경 변수·설정 / (6) 끔 / unstorable
# ---------------------------------------------------------------------------

def _cfg(path, cache_default=None, files=None, extra=None):
    doc = {"schema": "test"}
    if cache_default is not None:
        doc["table_cache"] = {"env": ENV, "default": str(cache_default)}
    if files is not None:
        doc["files"] = files
    if extra:
        doc.update(extra)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


def _dir_of(t):
    return os.path.dirname(t.path_of(LFP, DID, FN, ("k",)))


@pytest.mark.parametrize("env_kind", ["set", "empty", "absent"])
def test_from_config_env_priority_and_creates_folder(TC, tmp_path, monkeypatch, env_kind, sd):
    """(d) 2.1 위치·불변식 (5): env 매핑 값이 비어 있지 않으면 그 폴더, 빈 값·없음이면 설정 default; from_config 는 os.environ
    을 읽지 않는다; 폴더가 없으면 만든다(쓰기가 성공한다)."""
    dflt = sd / "dflt" / "nested"
    envd = sd / "envd" / "deep"
    cfg = _cfg(tmp_path / "cfg.json", cache_default=dflt)
    monkeypatch.setenv(ENV, str(tmp_path / "from_os_environ"))
    env = {"set": {ENV: str(envd)}, "empty": {ENV: ""}, "absent": {}}[env_kind]
    t = TC.from_config(cfg, env)
    want = envd if env_kind == "set" else dflt
    assert os.path.normcase(os.path.abspath(_dir_of(t))) == os.path.normcase(os.path.abspath(want))
    c = Counter(7)
    assert t.fetch(LFP, DID, FN, ("k",), (), (), c) == 7 and c.n == 1
    assert len(tbl_files(want)) == 1
    assert not (tmp_path / "from_os_environ").exists()


def test_from_config_uncreatable_folder_disables(TC, tmp_path):
    """(a)(d) 2.1: 폴더를 만들 수 없으면(경로 중간이 일반 파일) RuntimeWarning + disabled, 계산은 매번 그대로, 파일 0."""
    blocker = tmp_path / "blocker.txt"
    blocker.write_text("x")
    cfg = _cfg(tmp_path / "cfg.json", cache_default=tmp_path / "unused")
    with pytest.warns(RuntimeWarning):
        t = TC.from_config(cfg, {ENV: str(blocker / "sub")})
    assert "disabled" in dict(t.stats())
    c = Counter(5)
    for _ in range(2):
        assert t.fetch(LFP, DID, FN, ("k",), (), (), c) == 5
    assert c.n == 2
    assert t.path_of(LFP, DID, FN, ("k",)) is None
    assert blocker.read_text() == "x"


@pytest.mark.parametrize("variant", ["no_config_file", "no_table_cache_entry"])
def test_from_config_without_cache_entry_is_off(TC, tmp_path, variant):
    """(d) 2.1: 설정 파일·table_cache 항목이 없으면 꺼짐 -- path_of None, 매번 계산, 파일 0."""
    cfg = str(tmp_path / "none.json") if variant == "no_config_file" else _cfg(tmp_path / "cfg.json")
    t = TC.from_config(cfg, {ENV: str(tmp_path / "envd")})
    assert t.path_of(LFP, DID, FN, ("k",)) is None
    c = Counter(1)
    t.fetch(LFP, DID, FN, ("k",), (), (), c)
    t.fetch(LFP, DID, FN, ("k",), (), (), c)
    assert c.n == 2
    assert not (tmp_path / "envd").exists() or tbl_files(tmp_path / "envd") == []


def test_default_uses_repo_config_and_os_environ(TC, toy, tmp_path, monkeypatch, sd):
    """(d) 2.1: `TableCache.default()` 와 `LutMemo(..., table_cache 생략)` = 저장소 설정 + os.environ -> 환경 변수 폴더."""
    envd = sd / "env_cache"
    monkeypatch.setenv(ENV, str(envd))
    for t in (TC.default(), LutMemo(toy, point=1, curve=1, root=1).table_cache):
        assert isinstance(t, TC)
        assert os.path.normcase(os.path.abspath(_dir_of(t))) == os.path.normcase(os.path.abspath(envd))


_AUDIT_ON = []          # 비어 있지 않을 때만 기록(감사 훅은 프로세스 끝까지 남으므로 꺼 두면 비용 0에 가깝다)
_AUDIT = []
_IO_EVENTS = ("open", "os.replace", "os.rename", "os.remove", "os.unlink", "os.mkdir", "os.listdir", "os.scandir",
              "subprocess.Popen", "tempfile.mkstemp", "shutil.rmtree")


def _audit_hook(event, args):
    if _AUDIT_ON and event in _IO_EVENTS:
        _AUDIT.append((event, args[:1]))


sys.addaudithook(_audit_hook)


def test_disabled_cache_does_no_file_io(TC, toy):
    """(a) 2.1 불변식 (6): `TableCache(None)` 은 파일 입출력 0(감사 훅으로 open·replace·mkdir·listdir·subprocess 를 센다),
    매번 compute, path_of None. LutMemo 에 넘겨 tol_v_table 을 불러도 0."""
    t = TC(None)
    m = LutMemo(toy, point=8, curve=8, root=8, table_cache=t)
    assert m.table_cache is t
    c = Counter(("v",))
    _AUDIT.clear()
    _AUDIT_ON.append(True)
    try:
        t.fetch(LFP, DID, FN, ("k",), _inputs(), (), c)
        t.fetch(LFP, DID, FN, ("k",), _inputs(), (), c)
        tol_v_table(m, "nmos", 100)
    finally:
        _AUDIT_ON.clear()
    assert _AUDIT == []
    assert c.n == 2 and t.path_of(LFP, DID, FN, ("k",)) is None


@dataclasses.dataclass(frozen=True)
class _WithArray:
    x: float
    arr: object


@pytest.mark.parametrize("make", [lambda: (1.0, np.zeros(3)), lambda: _WithArray(1.0, np.ones(2)),
                                  lambda: {"a": (np.arange(2),)}])
def test_result_with_ndarray_is_unstorable(TC, tmp_path, make, sd):
    """(d) 2.1: 결과에 ndarray 가 들어 있으면 저장하지 않는다(unstorable) -- 같은 객체를 돌려주고, 파일 0, 다음에도 compute."""
    d = sd / "c"
    t = TC(str(d))
    value = make()
    c = Counter(value)
    assert t.fetch(LFP, DID, FN, ("k",), (), (), c) is value
    assert ("unstorable", FN) in t.events and ("write", FN) not in t.events
    assert not d.exists() or tbl_files(d) == []
    t.fetch(LFP, DID, FN, ("k",), (), (), c)
    assert c.n == 2


def test_events_vocabulary(TC, tmp_path, sd):
    """(d) 2.1 관찰: 지금까지 일으킨 이벤트 이름이 전부 계약 목록 안에 있다(미스·쓰기·적중·stale·unstorable)."""
    t = TC(str(sd / "c"))
    t.fetch(LFP, DID, FN, ("k",), (), ("a",), Counter(1))
    t.fetch(LFP, DID, FN, ("k",), (), ("a",), Counter(1))
    t.fetch(LFP, DID, FN, ("k",), (), ("b",), Counter(2))
    t.fetch(LFP, DID, FN, ("u",), (), (), Counter((np.zeros(1),)))
    assert all(e in EVENTS for e, _ in t.events)
    assert all(n == FN for _, n in t.events)
    assert dict(t.stats()) == {e: [x for x, _ in t.events].count(e) for e, _ in t.events}


# ---------------------------------------------------------------------------
# 자료 id
# ---------------------------------------------------------------------------

def test_data_id_follows_file_contents_not_folder(TC, toy_build, mid_toy_build, tmp_path):
    """(a) 2.1 자료 id = (manifest, cap_npz, verify_midpoints) sha256 의 지문: 같은 파일을 다른 폴더로 옮겨도 같고,
    manifest 바이트·cap 바이트·중점 파일 유무/내용이 바뀌면 다르다. 64자 소문자 hex."""
    b = toy_build("orig")
    a = TC.data_id(b.load().provenance)
    assert re.fullmatch(r"[0-9a-f]{64}", a)
    moved = copy_tree(b.root, tmp_path / "moved")
    from .conftest import TOY_SPEC
    from gmid_engine.lut import load_lut_set
    same = load_lut_set(str(moved / "manifest.json"), str(moved / "cap_ref.npz"), TOY_SPEC)
    assert TC.data_id(same.provenance) == a
    other_manifest = toy_build("gen", generator_sha256="1" * 64).load()
    from .conftest import toy_cap_arrays
    cap = toy_cap_arrays()
    cap["extra_unused"] = np.zeros(1)
    other_cap = toy_build("cap", cap=cap).load()
    ids = {a, TC.data_id(other_manifest.provenance), TC.data_id(other_cap.provenance)}
    assert len(ids) == 3
    mt1 = mid_toy_build("m1", mid=mid_point_arrays((3.5e-6,), l_source=MID_L_SOURCE))
    mt2 = mid_toy_build("m2", mid=mid_point_arrays((3.5e-6,), scale=1.5, l_source=MID_L_SOURCE))
    with_mid = TC.data_id(mt1.load().provenance)
    without_mid = TC.data_id(mt1.load(verify_midpoints=None).provenance)
    other_mid = TC.data_id(mt2.load().provenance)
    assert len({with_mid, without_mid, other_mid}) == 3


# ---------------------------------------------------------------------------
# (8) 정리 -- 임시 git 저장소 + git worktree add
# ---------------------------------------------------------------------------

CFG_REL = "cfg/lut_location.json"


def _git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, (args, r.stderr)
    return r.stdout


def _scaled_toy(toy_build, sub, factor):
    sl = standard_toy_slices()
    for k in ("ID", "GM", "GDS"):
        sl[0][2][k] = sl[0][2][k] * factor
    return toy_build(sub, slices=sl)


def _files_of(build):
    from .conftest import sha256_file
    return {"manifest": {"path": "manifest.json", "sha256": sha256_file(build.manifest)},
            "cap_npz": {"path": "cap_ref.npz", "sha256": sha256_file(build.cap)}}


class CleanupWorld:
    """저장소 R(설정 -> LUT A), worktree W1(설정 -> LUT B), W2(설정에 cap_npz 항목 없음), W3(설정 파일 삭제).
    LUT C 의 자료 id 는 어느 설정도 가리키지 않는다. 캐시 폴더는 임시 폴더."""

    def __init__(self, TC, toy_build, base, cache_parent):
        self.TC = TC
        base = Path(base)
        base.mkdir(parents=True)
        self.builds = {"A": toy_build("lutA"), "B": _scaled_toy(toy_build, "lutB", 3.0),
                       "C": _scaled_toy(toy_build, "lutC", 5.0)}
        self.ids = {k: TC.data_id(b.load().provenance) for k, b in self.builds.items()}
        assert len(set(self.ids.values())) == 3
        self.cache = Path(cache_parent) / "cache"
        self.cache.mkdir()
        self.repo = base / "repo"
        self.repo.mkdir()
        _git("-C", str(self.repo), "init", "-q")
        self.cfg = {"R": _cfg(self.repo / CFG_REL, cache_default=base / "unused_default",
                              files=_files_of(self.builds["A"]))}
        _git("-C", str(self.repo), "add", "-A")
        _git("-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "i")
        top = _git("-C", str(self.repo), "rev-parse", "--show-toplevel").strip()
        assert os.path.normcase(os.path.abspath(top)) == os.path.normcase(os.path.abspath(self.repo))
        self.wt = {}
        for name in ("W1", "W2", "W3"):
            p = base / ("wt_" + name)
            _git("-C", str(self.repo), "worktree", "add", "-q", str(p), "-b", "b_" + name.lower())
            self.wt[name] = p
        self.cfg["W1"] = _cfg(self.wt["W1"] / CFG_REL, cache_default=base / "unused_default",
                              files=_files_of(self.builds["B"]))
        f2 = _files_of(self.builds["C"])
        del f2["cap_npz"]
        self.cfg["W2"] = _cfg(self.wt["W2"] / CFG_REL, cache_default=base / "unused_default", files=f2)
        os.unlink(self.wt["W3"] / CFG_REL)
        self.outside = Path(cache_parent) / "outside"
        self.outside.mkdir()

    def name(self, fn, did, label):
        return "%s-%s-%s.tbl" % (fn, did, hx(label))

    def populate(self):
        """정리 후보 파일들. 반환: (지워져야 할 이름 집합, 남아야 할 이름 집합) -- (d) 2.1 정리 규칙으로 정한다."""
        ida, idb, idc = self.ids["A"], self.ids["B"], self.ids["C"]
        rnd = hx("random-id")
        doomed = {self.name("tol_v_table", idc, "c1"), self.name("curve_report", rnd, "r1")}
        kept = {self.name("tol_v_table", ida, "a1"), self.name("tol_vdsat_table", idb, "b1"),
                "notes.txt", "tol_v_table-%s.tbl" % idc,                        # 형식 다름(지문 칸 없음)
                "tol_v_table-%s-%s.tbl" % (idc.upper(), hx("u")),               # 대문자 hex
                "tol_v_table-%s-%s.tbl" % (idc[:-1], hx("s")),                  # 63자
                self.name("tol_v_table", idc, "c2") + ".tmp",                   # 확장자 다름
                self.name("tol_v_table", idc, "c3") + ".bak"}
        for n in doomed | kept:
            (self.cache / n).write_bytes(b"junk " + n.encode())
        sub = self.cache / "sub"
        sub.mkdir()
        (sub / self.name("tol_v_table", idc, "c4")).write_bytes(b"junk")       # 하위 폴더 안
        (self.cache / self.name("tol_v_table", idc, "dir")).mkdir()            # 이름은 맞지만 폴더
        (self.outside / self.name("tol_v_table", idc, "out")).write_bytes(b"junk")   # 캐시 폴더 밖
        kept |= {"sub", self.name("tol_v_table", idc, "dir")}
        return doomed, kept

    def obj(self, which="R"):
        return self.TC.from_config(self.cfg[which], {ENV: str(self.cache)})

    def write(self, t, data_id, label):
        """t 로 새 칸 하나를 쓴다(미스 -> 쓰기). 반환 = 쓴 파일 이름."""
        c = Counter(("val", label))
        t.fetch(LFP, data_id, FN, (label,), (), (), c)
        assert c.n == 1
        return os.path.basename(t.path_of(LFP, data_id, FN, (label,)))

    def untouched_outside(self):
        assert sorted(os.listdir(self.outside)) == [self.name("tol_v_table", self.ids["C"], "out")]
        assert os.listdir(self.cache / "sub") == [self.name("tol_v_table", self.ids["C"], "c4")]


@pytest.fixture
def world(TC, toy_build, tmp_path, sd):
    return CleanupWorld(TC, toy_build, tmp_path / "w", sd)


def _removed(t):
    return sorted(n for e, n in t.events if e == "cleanup_removed")


@pytest.mark.parametrize("which", ["R", "W1"])
def test_cleanup_keeps_ids_referenced_by_repo_and_all_worktrees(world, which):
    """(d) 2.1 정리: 첫 쓰기 직후 1회. 남기는 집합 = 저장소·모든 worktree 설정이 가리키는 자료 id(A: 저장소, B: W1) --
    W2(cap_npz 항목 없음)·W3(설정 없음)은 id 없음. C·임의 id 의 형식 맞는 파일만 지워지고, 방금 쓴 C 파일은 남는다.
    형식 다른 이름·하위 폴더·이름 맞는 폴더·폴더 밖 불변. 어느 worktree 의 설정으로 만든 객체든 같은 결과."""
    doomed, kept = world.populate()
    t = world.obj(which)
    just = world.write(t, world.ids["C"], "fresh")
    left = set(os.listdir(world.cache))
    assert left == kept | {just}
    assert not (left & doomed)
    assert _removed(t) == sorted(NAME_RE.match(n).group(1) for n in doomed)
    assert not [e for e, _ in t.events if e in ("cleanup_skipped", "cleanup_failsafe")]
    world.untouched_outside()


def test_cleanup_only_on_first_write_per_object(world):
    """(d) 2.1: 같은 객체의 두 번째 쓰기·읽기 적중에선 정리하지 않는다; 새 객체는 첫 쓰기에서 다시 정리한다
    (그때는 앞 객체가 쓴 C 파일도 가리켜지지 않으니 지운다 -- 방금 쓴 파일만 예외)."""
    world.populate()
    t1 = world.obj()
    first = world.write(t1, world.ids["C"], "one")
    n_removed = len(_removed(t1))
    late = world.name("curve_report", hx("late-random"), "late")
    (world.cache / late).write_bytes(b"junk")
    second = world.write(t1, world.ids["C"], "two")                 # 두 번째 쓰기
    c = Counter(None)
    t1.fetch(LFP, world.ids["C"], FN, ("one",), (), (), c)           # 적중
    assert c.n == 0
    assert len(_removed(t1)) == n_removed
    assert {late, first, second} <= set(os.listdir(world.cache))
    t2 = world.obj()
    c2 = Counter(None)
    t2.fetch(LFP, world.ids["C"], FN, ("one",), (), (), c2)          # 새 객체 읽기 적중 -> 정리 안 함
    assert c2.n == 0 and _removed(t2) == [] and late in os.listdir(world.cache)
    third = world.write(t2, world.ids["C"], "three")
    left = set(os.listdir(world.cache))
    assert third in left and not ({late, first, second} & left)
    assert sorted(_removed(t2)) == sorted(["curve_report", FN, FN])
    world.untouched_outside()


@pytest.mark.skipif(sys.platform != "win32", reason="열린 파일 삭제 불가는 Windows 공유 모드 동작(POSIX 는 unlink 가 성공)")
def test_cleanup_permission_error_is_skipped(world):
    """(a) 2.1: 삭제가 OSError(사용 중 -- Windows 에서 연 파일)면 cleanup_skipped, 예외 없음, 그 파일은 남고 나머지는 지워진다."""
    doomed, kept = world.populate()
    locked = sorted(doomed)[0]
    with open(world.cache / locked, "rb"):
        t = world.obj()
        just = world.write(t, world.ids["C"], "fresh")
    assert ("cleanup_skipped", NAME_RE.match(locked).group(1)) in t.events
    assert set(os.listdir(world.cache)) == kept | {just, locked}


def _assert_failsafe(t, world, before):
    assert ("cleanup_failsafe" in [e for e, _ in t.events])
    assert not [e for e, _ in t.events if e == "cleanup_removed"]
    assert set(os.listdir(world.cache)) == before


def test_cleanup_failsafe_broken_worktree_json(world):
    """(a) 2.1: worktree 설정 JSON 이 깨짐 -> cleanup_failsafe, 삭제 0(쓴 파일만 늘어남)."""
    world.populate()
    Path(world.cfg["W1"]).write_text("{ not json", encoding="utf-8")
    before = set(os.listdir(world.cache))
    t = world.obj()
    just = world.write(t, world.ids["C"], "fresh")
    _assert_failsafe(t, world, before | {just})


def test_cleanup_failsafe_git_not_runnable(world, monkeypatch):
    """(a) 2.1: git 실행 실패(PATH 에서 git 을 찾을 수 없음) -> cleanup_failsafe, 삭제 0."""
    world.populate()
    before = set(os.listdir(world.cache))
    monkeypatch.setenv("PATH", "")
    t = world.obj()
    just = world.write(t, world.ids["C"], "fresh")
    _assert_failsafe(t, world, before | {just})


def test_cleanup_failsafe_config_outside_git(world, tmp_path):
    """(a) 2.1: 설정 파일이 git 저장소 밖 -> cleanup_failsafe, 삭제 0."""
    world.populate()
    outside_root = tmp_path / "nogit"
    cfg = _cfg(outside_root / CFG_REL, cache_default=tmp_path / "unused", files=_files_of(world.builds["A"]))
    r = subprocess.run(["git", "-C", str(outside_root), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    assert r.returncode != 0, "전제: 임시 폴더가 git 저장소 밖이어야 한다"
    before = set(os.listdir(world.cache))
    t = world.TC.from_config(cfg, {ENV: str(world.cache)})
    just = world.write(t, world.ids["C"], "fresh")
    _assert_failsafe(t, world, before | {just})


def test_plain_directory_cache_never_cleans(world):
    """(d) 2.1: `TableCache(directory)`(설정 경로 없음)는 정리하지 않는다 -- 여러 번 써도 삭제 0, 정리 이벤트 0."""
    world.populate()
    before = set(os.listdir(world.cache))
    t = world.TC(str(world.cache))
    written = {world.write(t, world.ids["C"], "x%d" % i) for i in range(3)}
    assert set(os.listdir(world.cache)) == before | written
    assert not [e for e, _ in t.events if e.startswith("cleanup")]


# ---------------------------------------------------------------------------
# 2.1 'Windows 경로 길이' -- 폴더 경로가 ~97자를 넘어도 쓰기·읽기·깨짐 교체가 된다
# ---------------------------------------------------------------------------

_XLEN = "\\\\?\\"                                  # Windows 확장 길이 접두(백슬래시 2개 + ? + 백슬래시)


def _long(p):
    """test 쪽 파일 조작용 확장 길이 표기(Windows). 다른 OS 는 그대로."""
    p = os.path.abspath(str(p))
    return _XLEN + p if os.name == "nt" and not p.startswith(_XLEN) else p


def _deep_dir(base):
    d = Path(base) / ("d" * 60) / ("e" * 60)                 # (a) 폴더 경로 > 120자 -> 칸 파일 전체 경로 > 260자
    assert len(str(d)) > 120
    return d


def test_long_windows_path_write_hit_and_corrupt_replace(TC, tmp_path):
    """(d) 2.1 'Windows 경로 길이': 깊은 폴더(전체 경로 > MAX_PATH)에서도 폴더 생성·쓰기(write, write_error 아님)·새 객체 적중·
    깨진 파일 교체가 된다. path_of 는 보통 표기이고 파일 이름 형식은 그대로다."""
    d = _deep_dir(tmp_path)
    t = TC(str(d))
    value = ("deep", 1.5)
    c = Counter(value)
    assert t.fetch(LFP, DID, FN, ("k",), _inputs(), (), c) == value and c.n == 1
    assert t.events == (("miss", FN), ("write", FN))
    path = t.path_of(LFP, DID, FN, ("k",))
    assert len(path) > 260 and not path.startswith(_XLEN)
    assert NAME_RE.match(os.path.basename(path))
    key, body = parse_file(Path(_long(path)).read_bytes())          # (b) 형식 직접 파싱
    assert key == t.key_digest(LFP, FN, ("k",), _inputs(), ()) and pickle.loads(body) == value
    c2 = Counter(None)
    t2 = TC(str(d))
    assert t2.fetch(LFP, DID, FN, ("k",), _inputs(), (), c2) == value and c2.n == 0 and t2.events == (("hit", FN),)
    Path(_long(path)).write_bytes(b"garbage")
    t3 = TC(str(d))
    c3 = Counter(value)
    with pytest.warns(RuntimeWarning):
        assert t3.fetch(LFP, DID, FN, ("k",), _inputs(), (), c3) == value
    assert c3.n == 1 and ("corrupt", FN) in t3.events and ("write", FN) in t3.events
    assert sorted(os.listdir(_long(d))) == [os.path.basename(path)]     # 임시 파일 안 남음


def test_long_windows_path_from_config_and_memo(TC, toy, tmp_path):
    """(d) 2.1: 설정 경로로 만든 깊은 폴더(env)도 만들어지고, LutMemo 경유 tol_v_table 이 디스크에 써지고 새 memo 가 적중한다."""
    d = _deep_dir(tmp_path)
    cfg = _cfg(tmp_path / "cfg.json", cache_default=tmp_path / "unused")
    t1 = TC.from_config(cfg, {ENV: str(d)})
    a = tol_v_table(LutMemo(toy, point=8, curve=8, root=8, table_cache=t1), "nmos", 100)
    assert ("write", "tol_v_table") in t1.events and "write_error" not in dict(t1.stats())
    t2 = TC(str(d))
    b = tol_v_table(LutMemo(toy, point=8, curve=8, root=8, table_cache=t2), "nmos", 100)
    assert t2.events == (("hit", "tol_v_table"),)
    assert_bit_identical(a, b, "tol_v_table")
