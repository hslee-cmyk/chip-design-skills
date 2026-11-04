"""OP-7 어댑터 조각 `.spiceinit` 격리 -- interface 20261104-op7b §4 '어댑터 격리' T7-9a~c. **ngspice 를 실행하는 test 다(판정자가 돌린다, A7-3).**

oracle (a)(d): PDK 없는 저항 넷리스트(V1 = 1 V 가 R1 = 1 kΩ 에 걸림 -> V(a) = 1 V, KVL)와 사용자 선언 규칙(D §16: 실행 폴더의 설정 글은 선언 글,
`compat=None` 이면 빈 파일, 실행 뒤 로그 문장의 모드가 선언 모드와 다르면 거부). 사용자 HOME·USERPROFILE 에 비기본 모드 한 줄을 둔 `.spiceinit` 을 심어
두고, 어댑터가 그 파일이 아니라 실행 폴더의 파일만 쓰게 하는지 본다.
해석(interface 가 모호해 정한 것):
  * H-13 '기본 모드' = 실제 기술자의 `bin_rule_decl` 이 선언한 모드(`compat.mode`)이고, 선언 글·로그 문장은 어댑터 능력표 `compat_modes[mode]` 에서 읽는다.
  * H-14 실행 폴더의 `.spiceinit` = work_dir 아래 `.spiceinit` 이름의 파일 하나(재귀 탐색, 정확히 하나).
  * H-15 로그 = `result.status.log_path` 의 텍스트. 심은 비기본 모드 한 줄은 ngspice 의 호환 설정 `set ngbehavior=ps`(ngspice 사실, PDK 값 아님).
  * H-16 9c 의 '어긋남'은 `CompatDecl` 을 직접 만들어 선언 모드 = 기본, 글 = 비기본 으로 주는 것으로 구성한다(능력표를 건드리지 않음).
"""
import hashlib
import json
import os
from pathlib import Path

import pytest

from adapters.ngspice import Adapter
from adapters.ngspice.read import compat_mode_of
from core.bin_rule import CompatDecl, check_compat
from core.descriptor import load_descriptor
from core.ir import Circuit, Resistor, VSource
from core.requests import Condition, Op, OpOutputs
from core.results import OracleError

from conftest import NGSPICE, ORACLE_DIR

POISON = "set ngbehavior=ps\n"


@pytest.fixture
def poisoned_home(tmp_path, monkeypatch):
    h = tmp_path / "home"
    h.mkdir()
    (h / ".spiceinit").write_text(POISON, encoding="utf-8")
    monkeypatch.setenv("HOME", str(h))
    monkeypatch.setenv("USERPROFILE", str(h))
    return h


@pytest.fixture(scope="module")
def descriptor():
    return load_descriptor(ORACLE_DIR / "descriptors" / "sky130.oracle_descriptor.json", env=os.environ)


def adapter():
    return Adapter(exe=str(NGSPICE))


def bench():
    ckt = Circuit(elements=(VSource("V1", "a", "0", 1.0), Resistor("R1", "a", "0", 1000.0)),
                  role={"V1": "testbench", "R1": "circuit"}, meta={})
    req = (Op(id="op", cond=Condition(temp_c=27.0, corner="tt"), exc=(),
              outputs=OpOutputs(devices="all", nodes=("a",), currents=())),)
    return ckt, req


def default_compat(descriptor, ad):
    """H-13: 실제 기술자가 선언한 호환 모드를 어댑터 능력표로 만든 CompatDecl."""
    rel = Path(descriptor.doc["bin_rule_decl"]["path"])
    p = rel if rel.is_absolute() else Path(descriptor.path).parent / rel      # 기술자 폴더 기준 또는 절대(interface §2)
    return check_compat(json.loads(p.read_text(encoding="utf-8")), ad.capabilities()["compat_modes"])


def spiceinit_files(work):
    return [p for p in Path(work).rglob(".spiceinit") if p.is_file()]


def log_of(res):
    p = res.status.log_path
    assert p is not None
    return Path(p).read_text(encoding="utf-8", errors="replace")


def test_t7_9a_declared_text_in_run_folder_and_log_shows_declared_mode(poisoned_home, descriptor, tmp_path):
    ad = adapter()
    compat = default_compat(descriptor, ad)
    ckt, req = bench()
    res = ad.run(ckt, req, descriptor, str(tmp_path / "work"), None, None, compat)
    files = spiceinit_files(tmp_path / "work")
    assert len(files) == 1 and files[0].read_bytes() == compat.spiceinit_text.encode("utf-8")
    assert compat_mode_of(log_of(res), ad.capabilities()["compat_modes"]) == compat.mode
    assert res.status.error is None
    # 손 계산: V1 = 1 V 가 노드 a 를 직접 구동 -> V(a) = 1 V (KVL), 사용자 HOME 의 설정과 무관
    assert res.by_request["op"].nodes["a"] == pytest.approx(1.0, rel=1e-6)


def test_t7_9b_compat_none_gives_empty_spiceinit_and_default_mode_log(poisoned_home, descriptor, tmp_path):
    ad = adapter()
    declared = default_compat(descriptor, ad)                      # 기대 모드 이름을 얻기 위한 선언(실행에는 쓰지 않음)
    ckt, req = bench()
    res = ad.run(ckt, req, descriptor, str(tmp_path / "work"), None, None, None)
    files = spiceinit_files(tmp_path / "work")
    assert len(files) == 1 and files[0].read_bytes() == b""        # [B-3] 빈 파일
    assert compat_mode_of(log_of(res), ad.capabilities()["compat_modes"]) == declared.mode


def test_t7_9c_text_and_mode_name_disagree_is_compat_mismatch_and_no_result(poisoned_home, descriptor, tmp_path):
    ad = adapter()
    ok = default_compat(descriptor, ad)
    bad = CompatDecl(mode=ok.mode, spiceinit_text=POISON, spiceinit_sha256=hashlib.sha256(
        POISON.encode("utf-8")).hexdigest(), log_line=ok.log_line)
    ckt, req = bench()
    err, res = None, None
    try:
        res = ad.run(ckt, req, descriptor, str(tmp_path / "work"), None, None, bad)
    except OracleError as e:                                        # 코어가 받는 형태가 예외든 상태든 코드는 같다
        err = e
    code = err.code if err is not None else res.status.error
    assert code == "bin_rule_compat_mismatch"
    assert err is not None or res.by_request == {}                  # 그 벤치 결과 없음
