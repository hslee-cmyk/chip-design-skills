"""core/s0_slot.py -- `S0Slot(store, inputs, sources)`: 한 S0 의 스냅샷 저장소와 키 입력을 묶은 값 (설계 40 v1.9.1 §2.4.3 '저장 시점(D6)'·'키'·'쓰기').

oracle (d) 설계 문장:
- §2.4.3 D6: 단계 A 가 키 입력을 한 번 만들어 넘기고, 단계 A·B 는 읽기만, `build_search_context` 끝에서 1회 쓴다 -> 자리 값은 (저장소, 키 입력, 입력 파일)을 담고
  load·save 를 그 저장소의 같은 키로 위임한다.
- §2.4.3 '쓰기': 키가 이미 있고 검증을 통과하면 쓰지 않는다. '무효화': 키가 다르면 없는 것으로 본다(miss).
- §2.4.1 단계 B 층은 직렬화하지 않는다 -> save(transient=) 로 넘긴 writer 의 필드는 파일에 없다.
- 형식 검사: store 는 S0SnapshotStore, inputs·sources 는 tuple(위반 TypeError).
기대값은 저장소 자신의 키 경로(`path_of`)와 손으로 만든 작은 스냅샷 -- 자리 값을 거치든 저장소를 직접 부르든 같은 파일·같은 결과여야 한다.
"""
from __future__ import annotations

import threading

import pytest

from gmid_engine.core import GraphSnapshot, S0Slot, WriterTable
from gmid_engine.core import snapshot_codec
from gmid_engine.core.snapshot_codec import S0SnapshotStore

WRITERS = WriterTable([("graph", "alpha", "w_a"), ("graph", "beta", "w_b")])
INPUTS = (("topology_fp", "t" * 8), ("spec_fp", None))
SOURCES = (("topology", (None, None)),)


@pytest.fixture(autouse=True)
def no_cleanup(monkeypatch):
    """프로세스의 첫 쓰기 정리(U-68) 기회를 이 test 가 쓰지 않게 '이미 시작함'으로 둔다(test_snapshot_codec 관례)."""
    done = threading.Event()
    done.set()
    monkeypatch.setattr(snapshot_codec, "_CLEANUP_STARTED", done)


def _snap():
    s = GraphSnapshot.empty(WRITERS)
    s = s.write("w_a", "iv-a", {("graph", "alpha"): {"g": 1.5}})
    return s.write("w_b", "iv-b", {("graph", "beta"): {"g": (1, 2)}})


def _slot(tmp_path, inputs=INPUTS):
    return S0Slot(S0SnapshotStore(str(tmp_path), "c" * 16), inputs, SOURCES)


@pytest.mark.parametrize("bad", [dict(store="x"), dict(inputs={"a": "b"}), dict(sources=[("t", (None, None))])])
def test_type_checked(tmp_path, bad):
    kw = dict(store=S0SnapshotStore(str(tmp_path), "c" * 16), inputs=INPUTS, sources=SOURCES)
    kw.update(bad)
    with pytest.raises(TypeError):
        S0Slot(**kw)


def test_load_before_save_is_miss(tmp_path):
    snap, outcome = _slot(tmp_path).load()
    assert snap is None and outcome == "miss"


def test_save_then_load_hits_same_key_file(tmp_path):
    slot = _slot(tmp_path)
    path = slot.save(_snap())
    assert path == slot.store.path_of(dict(INPUTS), dict(SOURCES))
    got, outcome = slot.load()
    assert outcome == "hit" and got.fp == _snap().fp
    assert slot.save(_snap()) == path                       # 이미 검증되는 파일 -> 쓰지 않고 같은 경로


def test_different_inputs_are_a_different_key(tmp_path):
    _slot(tmp_path).save(_snap())
    other = _slot(tmp_path, (("topology_fp", "u" * 8), ("spec_fp", None)))
    assert other.load() == (None, "miss")


def test_transient_writer_not_persisted(tmp_path):
    slot = _slot(tmp_path)
    slot.save(_snap(), transient=("w_b",))
    got, outcome = slot.load()
    assert outcome == "hit"
    assert got.value("graph", "g", "alpha") == 1.5
    assert got.record("graph", "g").get("beta") is None
    assert got.block_version("w_b") is None
