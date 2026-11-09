"""V4(test_lint.py (1)) 모양 probe -- 계약 8(부재 → 복원 전후 같은 값) test 모양별 판정. 실행하지 않는 합성 test(정적 lint 입력)다.

측정(2026-10-01, 0f23786 test_lint.py, --interface-card = B34 interface card 모의 생성본, 격리 복제본 C:/g123/seq_P2):
  묶음 1(a·b·c) -> out/v4probe_abc.txt: verdict FAIL -- a(지역 변수 before/after 직접 호출) (1) FAIL, b(블록 안 대입)·c(dict 원소) (2) UNJUDGED
  묶음 2(d·e)   -> out/v4probe_de.txt : verdict PASS -- d(_b34_snapshot helper) (2) UNJUDGED, e(새 프로세스 기대값) (2) UNJUDGED
명령: C:/Python314/python.exe -B <seq>/tools/gates/test_lint.py --root <seq> --interface-card <seq>/docs/02-design/specs/20260930-b34-grammar-explicit.interface.md <이 파일 사본 경로>
"""
import json
import subprocess
import sys
import stick_diagram


def _b34_normalize(x):
    return x


def _b34_snapshot(ts):
    return _b34_normalize(stick_diagram.find_stack_edges(ts))


# ---- 묶음 1
def test_b34_a_plain(monkeypatch):              # (1) FAIL
    ts, _ = stick_diagram.load_topology("p")
    before = stick_diagram.find_stack_edges(ts)
    monkeypatch.setitem(sys.modules, "netclass", None)
    monkeypatch.undo()
    after = stick_diagram.find_stack_edges(ts)
    assert _b34_normalize(after) == _b34_normalize(before)


def test_b34_b_block(monkeypatch):              # (2) UNJUDGED
    ts, _ = stick_diagram.load_topology("p")
    before = stick_diagram.find_stack_edges(ts)
    with monkeypatch.context() as m:
        m.setitem(sys.modules, "netclass", None)
    for _ in range(1):
        after = stick_diagram.find_stack_edges(ts)
    assert _b34_normalize(after) == _b34_normalize(before)


def test_b34_c_dict(monkeypatch):               # (2) UNJUDGED
    ts, _ = stick_diagram.load_topology("p")
    vals = {}
    vals["before"] = stick_diagram.find_stack_edges(ts)
    monkeypatch.setitem(sys.modules, "netclass", None)
    monkeypatch.undo()
    vals["after"] = stick_diagram.find_stack_edges(ts)
    assert _b34_normalize(vals["after"]) == _b34_normalize(vals["before"])


# ---- 묶음 2
def test_b34_d_helper(monkeypatch):             # (2) UNJUDGED
    ts, _ = stick_diagram.load_topology("p")
    before = _b34_snapshot(ts)
    monkeypatch.setitem(sys.modules, "netclass", None)
    monkeypatch.undo()
    after = _b34_snapshot(ts)
    assert after == before


def test_b34_e_fresh_process(monkeypatch):      # (2) UNJUDGED
    ts, _ = stick_diagram.load_topology("p")
    exp = json.loads(subprocess.run([sys.executable, "-c", "print(1)"], capture_output=True).stdout)
    monkeypatch.setitem(sys.modules, "netclass", None)
    monkeypatch.undo()
    after = stick_diagram.find_stack_edges(ts)
    assert _b34_normalize(after) == exp
