"""OP-3 실행 캐시(core.cache.cache_key + 캐시 상태 miss/hit/None/시간 초과) -- interface §6 T3-9, T3-10, design §9.

oracle (a): 구성으로 정해진 합성 입력 -- 다섯 항 가운데 하나만 바꾸면 키가 달라야 한다는 규칙 문장(D §9 '키에 없는 입력이 결과를
바꾸면 결함')과 첫 실행 miss / 둘째 hit / 폴더 없음 None / 시간 초과 저장 안 함(D §9 끝 문단). 캐시 상태는 stub 가 아니라
결과 파일 `sim.cache.main` 으로 읽는다(코어가 `RunStatus.cache_state` 를 옮긴 칸, D §6.1).
해석: `cache_key(adapter_fp: str, text: str, bundle_lf: list[str], args: tuple[str, ...], spiceinit_sha: str) -> str`.
"""
import json
from pathlib import Path

import pytest

from core.cache import cache_key

from op23_support import World, read_json_glob
from stub_adapter import StubAdapter

BASE = dict(adapter_fp="fp1", text="t1", bundle_lf=["h1", "h2"], args=("-b",), spiceinit_sha="")


def key(**over):
    a = dict(BASE)
    a.update(over)
    return cache_key(a["adapter_fp"], a["text"], a["bundle_lf"], a["args"], a["spiceinit_sha"])


def test_t3_9_each_of_five_terms_changes_the_key():
    k0 = key()
    assert key() == k0                                                  # 양성 대조: 같은 입력 = 같은 키(결정성)
    variants = {
        "adapter_fp": key(adapter_fp="fp2"),
        "text": key(text="t2"),
        "bundle_lf": key(bundle_lf=["h1", "h3"]),
        "args": key(args=("-b", "-x")),
        "spiceinit_sha": key(spiceinit_sha="abc"),
    }
    for name, k in variants.items():
        assert k != k0, name
    assert len(set(variants.values()) | {k0}) == 6                       # 서로도 다름


def test_t3_9_bundle_list_order_insensitive():
    assert key(bundle_lf=["h2", "h1"]) == key(bundle_lf=["h1", "h2"])    # 정렬 뒤 같으면 같은 키


def devices():
    return {"M1": {"gm": 6e-4, "gds": 1.0 / 60000.0}}


def cache_state(out: Path):
    return read_json_glob(out, "*.sim.json")["cache"]["main"]


def test_t3_10_miss_then_hit_and_none_and_timeout_not_stored(tmp_path):
    w = World(tmp_path)
    stub = StubAdapter(devices())
    cdir = tmp_path / "cache"
    rc1, o1 = w.run(stub, out=tmp_path / "o1", extra=["--cache-dir", cdir])
    assert cache_state(o1) == "miss"
    rc2, o2 = w.run(stub, out=tmp_path / "o2", extra=["--cache-dir", cdir])
    assert cache_state(o2) == "hit"
    assert read_json_glob(o2, "*.sim.json")["ac"] == read_json_glob(o1, "*.sim.json")["ac"]     # 재사용은 같은 결과
    rc0, o0 = w.run(stub, out=tmp_path / "o0")                                                  # 캐시 폴더 없음
    assert cache_state(o0) is None


def test_t3_10_timed_out_run_is_not_stored(tmp_path):
    w = World(tmp_path)
    stub = StubAdapter(devices())
    cdir = tmp_path / "cache"
    stub.force_timeout = True
    w.run(stub, out=tmp_path / "t", extra=["--cache-dir", cdir])
    assert not cdir.exists() or not list(cdir.glob("*"))                 # 시간 초과 실행은 슬롯을 만들지 않음
    stub.force_timeout = False
    rc, o = w.run(stub, out=tmp_path / "after", extra=["--cache-dir", cdir])
    assert cache_state(o) == "miss"                                      # 시간 초과 뒤 첫 정상 실행은 여전히 miss


def test_t3_10_changed_circuit_misses(tmp_path):
    w = World(tmp_path)
    stub = StubAdapter(devices())
    cdir = tmp_path / "cache"
    w.run(stub, out=tmp_path / "a", extra=["--cache-dir", cdir])
    inp2 = json.loads(json.dumps(w.inp))
    inp2["passives"][0]["value"] = 22000.0                               # 넷리스트(회로)가 바뀜
    rc, o = w.run(stub, inp=inp2, out=tmp_path / "b", extra=["--cache-dir", cdir])
    assert cache_state(o) == "miss"
