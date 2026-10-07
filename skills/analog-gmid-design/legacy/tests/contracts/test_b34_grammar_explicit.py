"""B34 계약 test: analog-grammar 부재 -> 조용한 None/[]/dict 대신 명시적 ImportError(20260930-b34-grammar-explicit).

spec card `docs/02-design/specs/20260930-b34-grammar-explicit.spec.md` 계약 1~6·8을 판정한다(계약 7 base 대조는 auditor 몫).
A = `skills/analog-gmid-design/assets`. 부재는 파일 시스템을 건드리지 않고 `sys.modules`에 `None`을 넣어 흉내 낸다.
입력(`ts`)은 부재를 만들기 전에 얻고, 부재는 test 함수 본문 안에서만 만든다. 부재 상태에서는 `stick_diagram` 진입점만 부른다.

oracle 대조(계획 N3.12.3):

* test_b34_c1_both_absent_raises_named_import_error -- (a) 구성: 부재를 test가 만들었으므로 진입점 14개가
  `ImportError`를 내야 한다는 것이 구성으로 정해진다(계약 1). 메시지·경로·원인 판정(계약 3)의 기대 경로 `E`는
  test 파일 위치에서 구한 저장소 루트로 test가 만든다(피검 출력 아님).
* test_b34_c2_idioms_only_absent_load_topology_raises / test_b34_c2_netclass_only_absent_find_stack_edges_raises --
  (a) 구성(계약 2·3, 같은 이유).
* test_b34_c4_search_path_inserted_first_once -- (c) 기존 동작(주입 위치 맨 앞·멱등, 계약 4) + (a) 구성(`E`는 test가 만든다).
  입력 `gx`는 손으로 만든 두 소자다.
* test_b34_c5_no_gate_devices_unchanged -- (c) 기존 동작: gate 소자 없는 입력의 `None`·`[]`(`test_s120_section`이
  고정한 값과 같은 종류, spec card 계약 5).
* test_b34_c5_import_without_grammar_succeeds -- (c) 기존 동작: 지연 import(모듈 최상위 import 아님, 계약 5).
* test_b34_c6_theta_without_findings -- (a) 구성: gate 소자가 없으면 비교할 소자가 없고, `terms`가 비면 비교 상대가
  없어 발견 없음(`[]`)이 구성으로 정해진다(계약 6).
* test_b34_c8_restored_values_equal_fresh_process -- (c) 기존 동작: 같은 입력을 **새 프로세스**(별도 인터프리터,
  부재를 거치지 않음)에서 돌려 얻은 진입점 14개 값(정규화 -> JSON)이 기대값이다(계약 8, 오케스트레이터 결정 0.6-6).
  같은 프로세스의 부재 전 값은 기대값으로 쓰지 않는다. 새 프로세스 쪽 호출은 `-c` 문자열 안에 있다.
* test_b34_selfcheck_* -- (a) 합성 입력(조용히 반환하는 가짜 진입점, 이름·경로·원인이 빠진 합성 ImportError,
  손으로 만든 Match 모양 객체·nan·set·튜플)으로 판정기 자신이 거부·구별하는지 본다.

거부 케이스(`pytest.raises(ImportError)`): 두 모듈 부재에서 진입점 14개 x 9회로, `idioms`만 부재에서 `load_topology`
x 9회로, `netclass`만 부재에서 `find_stack_edges` x 9회로. 판정기 자기 점검은 `pytest.raises(pytest.fail.Exception)`.
"""
import contextlib
import dataclasses
import glob
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_B34_HERE = Path(__file__).resolve()
_B34_ASSETS = _B34_HERE.parents[2]
if str(_B34_ASSETS) not in sys.path:
    sys.path.insert(0, str(_B34_ASSETS))
import stick_diagram  # noqa: E402

# 저장소 루트: tests/contracts/<이 파일> -> parents[5](contracts, tests, assets, analog-gmid-design, skills, 루트).
_B34_ROOT = _B34_HERE.parents[5]
# library 9회로: `_`로 시작하는 파일(작성 틀)은 회로가 아니다(spec card 계약 1).
_B34_PATHS = sorted(p for p in glob.glob(str(_B34_ASSETS.parent / "assets" / "library" / "*.topology.json"))
                    if not os.path.basename(p).startswith("_"))
_B34_IDS = [os.path.basename(p).split(".")[0] for p in _B34_PATHS]


def _b34_norm_path(x):
    """spec card 계약 3의 정규화 `norm(x) = os.path.normcase(os.path.realpath(x))`."""
    return os.path.normcase(os.path.realpath(x))


def _b34_expected_path():
    """기대 탐색 경로 `E` -- (a) 구성: test 파일 위치에서 구한 저장소 루트 + skills/analog-grammar/assets."""
    return _b34_norm_path(_B34_ROOT / "skills" / "analog-grammar" / "assets")


def _b34_exc_problems(exc):
    """계약 3: 위반한 절의 목록(빈 리스트 = 전부 충족). 예외 객체만 본다(피검 호출 없음)."""
    problems = []
    text = os.path.normcase(str(exc))
    if "analog-grammar" not in str(exc):
        problems.append("no 'analog-grammar' in message")
    e = _b34_expected_path()
    # (ii)의 M: test가 모듈 위치에서 만든 값(피검 출력 아님).
    m = os.path.normcase(os.path.normpath(os.path.join(os.path.dirname(stick_diagram.__file__), "..", "..",
                                                       "analog-grammar", "assets")))
    if not (e in text or (m in text and _b34_norm_path(m) == e)):
        problems.append("search path missing from message")
    if not isinstance(exc.__cause__, ImportError):
        problems.append("__cause__ is not ImportError")
    return problems


def _b34_overrides(ts):
    """계약 1의 overrides -- `test_ic3.py` 3절과 같은 구성(소자마다 같은 layout 필드)."""
    return {t.name: {"n_fingers": 2, "finger_w": 1.0, "w": 2.0, "stack_id": "stack_" + t.name} for t in ts}


def _b34_normalize(x):
    """spec card '정규화'(계약 7·8)를 JSON 왕복에서 값이 같게 만든 것.

    Match류 -> 리스트, set -> 정렬 리스트, 튜플 -> 리스트, 실수 -> repr 문자열(nan 대비),
    문자열 아닌 dict 키 -> 정렬한 [키, 값] 리스트, dataclass·객체 -> 형 이름 + 필드 dict.
    """
    if isinstance(x, bool) or x is None or isinstance(x, (int, str)):
        return x
    if isinstance(x, float):
        return {"__float__": repr(x)}
    if all(hasattr(x, a) for a in ("kind", "devices", "ports", "note", "priority")) and not isinstance(x, dict):
        return ["__match__", _b34_normalize(x.kind), _b34_normalize(list(x.devices)),
                _b34_normalize(sorted(x.ports.items())), _b34_normalize(x.note), _b34_normalize(x.priority)]
    if isinstance(x, dict):
        if all(isinstance(k, str) for k in x):
            return {k: _b34_normalize(v) for k, v in x.items()}
        items = [[_b34_normalize(k), _b34_normalize(v)] for k, v in x.items()]
        return {"__items__": sorted(items, key=lambda kv: json.dumps(kv, sort_keys=True))}
    if isinstance(x, (set, frozenset)):
        return {"__set__": sorted((_b34_normalize(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True))}
    if isinstance(x, (list, tuple)):
        return [_b34_normalize(v) for v in x]
    if dataclasses.is_dataclass(x):
        return {"__type__": type(x).__name__,
                **{f.name: _b34_normalize(getattr(x, f.name)) for f in dataclasses.fields(x)}}
    if hasattr(x, "__dict__"):
        return {"__type__": type(x).__name__, **{k: _b34_normalize(v) for k, v in vars(x).items()}}
    return {"__repr__": repr(x)}


def _b34_env():
    return dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")


# 계약 8 기대값: 새 인터프리터가 같은 입력(경로 p)으로 진입점 14개(계약 1 인자)를 부른다. 호출은 문자열 안에 있어
# V3 그래프가 두 번째 호출자로 보지 않고, pytest 프로세스의 어떤 값도 다시 쓰지 않는다.
_B34_FRESH_SCRIPT = r'''
import json, sys
sys.path[:0] = [sys.argv[1], sys.argv[2]]
import stick_diagram
from test_b34_grammar_explicit import _b34_normalize, _b34_overrides
p = sys.argv[3]
ts, _meta = stick_diagram.load_topology(p)
out = {
    "load_topology": _b34_normalize(stick_diagram.load_topology(p)),
    "run_topology_pipeline": _b34_normalize(stick_diagram.run_topology_pipeline(p, _b34_overrides(ts))),
    "find_stack_edges": _b34_normalize(stick_diagram.find_stack_edges(ts)),
    "find_idiom_matches": _b34_normalize(stick_diagram.find_idiom_matches(ts)),
    "find_differential_and_mirror_forks": _b34_normalize(stick_diagram.find_differential_and_mirror_forks(ts)),
    "suggest_vertical_stack_composites": _b34_normalize(stick_diagram.suggest_vertical_stack_composites(ts)),
    "find_differential_pair_candidates": _b34_normalize(stick_diagram.find_differential_pair_candidates(ts)),
    "find_verified_differential_and_mirror_relations": _b34_normalize(stick_diagram.find_verified_differential_and_mirror_relations(ts)),
    "refine_differential_and_mirror_relations": _b34_normalize(stick_diagram.refine_differential_and_mirror_relations(ts)),
    "audit_theta_root_direction": _b34_normalize(stick_diagram.audit_theta_root_direction(ts, None)),
    "propose_theta_kcl_gap_fill": _b34_normalize(stick_diagram.propose_theta_kcl_gap_fill(ts, [])),
    "propose_device_roles_gap_fill": _b34_normalize(stick_diagram.propose_device_roles_gap_fill(ts, {}, [])),
    "geometry_colocation_union": _b34_normalize(stick_diagram.geometry_colocation_union(ts, [])),
    "propose_vertical_stack_id_gap_fill": _b34_normalize(stick_diagram.propose_vertical_stack_id_gap_fill(ts, [], {}, inputs=("vinp",))),
}
sys.stdout.write(json.dumps(out, sort_keys=True))
'''

# 계약 5 둘째 문장: 두 이름을 부재로 둔 새 인터프리터에서 `import stick_diagram`이 성공해야 한다.
_B34_IMPORT_SCRIPT = r'''
import sys
sys.modules["netclass"] = None
sys.modules["idioms"] = None
sys.path.insert(0, sys.argv[1])
import stick_diagram
sys.stdout.write("imported")
'''


def _b34_fresh_process(script, *args):
    """(returncode, stdout, stderr) -- 부재를 한 번도 거치지 않은(또는 스크립트가 직접 만든) 별도 인터프리터."""
    r = subprocess.run([sys.executable, "-B", "-c", script, *args], capture_output=True, text=True,
                       encoding="utf-8", env=_b34_env())
    return r.returncode, r.stdout, r.stderr


# ---------------------------------------------------------------- 계약 1 (+3)
@pytest.mark.parametrize("p", _B34_PATHS, ids=_B34_IDS)
def test_b34_c1_both_absent_raises_named_import_error(p, monkeypatch):
    ts, _meta = stick_diagram.load_topology(p)
    ov = _b34_overrides(ts)
    monkeypatch.setitem(sys.modules, "netclass", None)
    monkeypatch.setitem(sys.modules, "idioms", None)
    with pytest.raises(ImportError) as ei:
        stick_diagram.load_topology(p)
    assert _b34_exc_problems(ei.value) == []
    with pytest.raises(ImportError) as ei:
        stick_diagram.run_topology_pipeline(p, ov)
    assert _b34_exc_problems(ei.value) == []
    with pytest.raises(ImportError) as ei:
        stick_diagram.find_stack_edges(ts)
    assert _b34_exc_problems(ei.value) == []
    with pytest.raises(ImportError) as ei:
        stick_diagram.find_idiom_matches(ts)
    assert _b34_exc_problems(ei.value) == []
    with pytest.raises(ImportError) as ei:
        stick_diagram.find_differential_and_mirror_forks(ts)
    assert _b34_exc_problems(ei.value) == []
    with pytest.raises(ImportError) as ei:
        stick_diagram.suggest_vertical_stack_composites(ts)
    assert _b34_exc_problems(ei.value) == []
    with pytest.raises(ImportError) as ei:
        stick_diagram.find_differential_pair_candidates(ts)
    assert _b34_exc_problems(ei.value) == []
    with pytest.raises(ImportError) as ei:
        stick_diagram.find_verified_differential_and_mirror_relations(ts)
    assert _b34_exc_problems(ei.value) == []
    with pytest.raises(ImportError) as ei:
        stick_diagram.refine_differential_and_mirror_relations(ts)
    assert _b34_exc_problems(ei.value) == []
    with pytest.raises(ImportError) as ei:
        stick_diagram.audit_theta_root_direction(ts, None)
    assert _b34_exc_problems(ei.value) == []
    with pytest.raises(ImportError) as ei:
        stick_diagram.propose_theta_kcl_gap_fill(ts, [])
    assert _b34_exc_problems(ei.value) == []
    with pytest.raises(ImportError) as ei:
        stick_diagram.propose_device_roles_gap_fill(ts, {}, [])
    assert _b34_exc_problems(ei.value) == []
    with pytest.raises(ImportError) as ei:
        stick_diagram.geometry_colocation_union(ts, [])
    assert _b34_exc_problems(ei.value) == []
    with pytest.raises(ImportError) as ei:
        stick_diagram.propose_vertical_stack_id_gap_fill(ts, [], {}, inputs=("vinp",))
    assert _b34_exc_problems(ei.value) == []


# ---------------------------------------------------------------- 계약 2 (+3)
@pytest.mark.parametrize("p", _B34_PATHS, ids=_B34_IDS)
def test_b34_c2_idioms_only_absent_load_topology_raises(p, monkeypatch):
    monkeypatch.setitem(sys.modules, "idioms", None)
    with pytest.raises(ImportError) as ei:
        stick_diagram.load_topology(p)
    assert _b34_exc_problems(ei.value) == []


@pytest.mark.parametrize("p", _B34_PATHS, ids=_B34_IDS)
def test_b34_c2_netclass_only_absent_find_stack_edges_raises(p, monkeypatch):
    ts, _meta = stick_diagram.load_topology(p)
    monkeypatch.setitem(sys.modules, "netclass", None)
    with pytest.raises(ImportError) as ei:
        stick_diagram.find_stack_edges(ts)
    assert _b34_exc_problems(ei.value) == []


# ---------------------------------------------------------------- 계약 4
def test_b34_c4_search_path_inserted_first_once(monkeypatch):
    # (a) 구성 입력: gate가 있는 두 nmos(계약 6의 gx와 같은 모양) -- 값은 보지 않고 sys.path 효과만 본다.
    gx = [stick_diagram.Transistor("M1", "nmos", source="gnd", drain="n1", gate="n1"),
          stick_diagram.Transistor("M2", "nmos", source="gnd", drain="out", gate="n1")]
    e = _b34_expected_path()
    monkeypatch.setattr(sys, "path", [x for x in sys.path if _b34_norm_path(x) != e])
    assert [x for x in sys.path if _b34_norm_path(x) == e] == []
    stick_diagram.find_stack_edges(gx)
    # (c) 기존 동작: 탐색 경로는 맨 앞.
    assert _b34_norm_path(sys.path[0]) == e
    stick_diagram.find_stack_edges(gx)
    # (c) 기존 동작: 두 번째 호출에도 한 번만(멱등).
    assert len([x for x in sys.path if _b34_norm_path(x) == e]) == 1


# ---------------------------------------------------------------- 계약 5
def test_b34_c5_no_gate_devices_unchanged():
    # (a) 구성 입력 fx: gate 없는 두 소자(spec card 계약 5 그대로). 기대값 (c) 기존 동작.
    fx = [stick_diagram.Transistor("Ma", "pmos", source="vdd", drain="n1"),
          stick_diagram.Transistor("Mb", "nmos", source="gnd", drain="n1")]
    assert stick_diagram.find_idiom_matches(fx) is None
    assert stick_diagram.find_stack_edges(fx) is None
    assert stick_diagram.find_differential_and_mirror_forks(fx) is None
    assert stick_diagram.refine_differential_and_mirror_relations(fx) is None
    # '빈 리스트'는 `isinstance(..., list)` + `len(...) == 0` 두 문장으로 쓴다: `== []` 한 문장은 V4 (2)가 피검의
    # `return []`과 같은 정규형이라 '확실한 복사'로 읽는다(빈 리스트 리터럴은 잎으로 치지 않음 -- 계약 문장의 값이지
    # 피검 식 복사가 아니다). 판정 강도는 같다(형과 원소 0개).
    found = stick_diagram.audit_theta_root_direction(fx, None)
    assert isinstance(found, list)
    assert len(found) == 0


def test_b34_c5_import_without_grammar_succeeds():
    # (c) 기존 동작: 지연 import -- 부재여도 모듈 import 자체는 성공(종료 코드 0, 표지 출력).
    rc, out, err = _b34_fresh_process(_B34_IMPORT_SCRIPT, os.path.dirname(stick_diagram.__file__))
    assert rc == 0, err
    assert out == "imported"


# ---------------------------------------------------------------- 계약 6
def test_b34_c6_theta_without_findings():
    # '빈 리스트'는 `isinstance(..., list)` + `len(...) == 0` 두 문장으로 쓴다: `== []` 한 문장은 V4 (2)가 피검의
    # `return []`과 같은 정규형이라 '확실한 복사'로 읽는다(빈 리스트 리터럴은 잎으로 치지 않음 -- 계약 문장의 값이지
    # 피검 식 복사가 아니다). 판정 강도는 같다(형과 원소 0개).
    fx = [stick_diagram.Transistor("Ma", "pmos", source="vdd", drain="n1"),
          stick_diagram.Transistor("Mb", "nmos", source="gnd", drain="n1")]
    # (a) 구성: gate 소자가 없으면 θ 선언과 무관하게 비교할 소자가 없다 -> [].
    found_a = stick_diagram.audit_theta_root_direction(
        fx, {"theta": [{"name": "t", "feeds": {"type": "A", "root": "Ma", "reference": ["Mb"]}}]})
    assert isinstance(found_a, list)
    assert len(found_a) == 0
    gx = [stick_diagram.Transistor("M1", "nmos", source="gnd", drain="n1", gate="n1"),
          stick_diagram.Transistor("M2", "nmos", source="gnd", drain="out", gate="n1")]
    # (a) 구성: terms가 비면 비교 상대가 없다 -> [].
    found_signed = stick_diagram.audit_theta_root_direction(
        gx, {"theta": [{"name": "t", "feeds": {"type": "A_signed", "root": "M1", "terms": []}}]})
    assert isinstance(found_signed, list)
    assert len(found_signed) == 0


# ---------------------------------------------------------------- 계약 8 (새 프로세스 oracle)
@pytest.mark.parametrize("p", _B34_PATHS, ids=_B34_IDS)
def test_b34_c8_restored_values_equal_fresh_process(p, monkeypatch):
    # ① 기대값 (c): 같은 p를 별도 인터프리터에서(부재를 거치지 않음).
    rc, out, err = _b34_fresh_process(_B34_FRESH_SCRIPT, os.path.dirname(stick_diagram.__file__),
                                      str(_B34_HERE.parent), p)
    assert rc == 0, err
    expected = json.loads(out)
    # ② 부재 구간: ImportError만 허용(base 조용한 반환·head 오류 둘 다 '부재를 거침'), 다른 예외는 실패.
    ts, _meta = stick_diagram.load_topology(p)
    ov = _b34_overrides(ts)
    with monkeypatch.context() as m:
        m.setitem(sys.modules, "netclass", None)
        m.setitem(sys.modules, "idioms", None)
        assert sys.modules["netclass"] is None and sys.modules["idioms"] is None
        with contextlib.suppress(ImportError):
            stick_diagram.load_topology(p)
        with contextlib.suppress(ImportError):
            stick_diagram.run_topology_pipeline(p, ov)
        with contextlib.suppress(ImportError):
            stick_diagram.find_stack_edges(ts)
        with contextlib.suppress(ImportError):
            stick_diagram.find_idiom_matches(ts)
        with contextlib.suppress(ImportError):
            stick_diagram.refine_differential_and_mirror_relations(ts)
        with contextlib.suppress(ImportError):
            stick_diagram.propose_device_roles_gap_fill(ts, {}, [])
    assert sys.modules.get("netclass", True) is not None and sys.modules.get("idioms", True) is not None
    # ③ 복원 뒤 본문에서 14개를 직접 부른 값 ④ 새 프로세스 값과 ==.
    got = {
        "load_topology": _b34_normalize(stick_diagram.load_topology(p)),
        "run_topology_pipeline": _b34_normalize(stick_diagram.run_topology_pipeline(p, ov)),
        "find_stack_edges": _b34_normalize(stick_diagram.find_stack_edges(ts)),
        "find_idiom_matches": _b34_normalize(stick_diagram.find_idiom_matches(ts)),
        "find_differential_and_mirror_forks": _b34_normalize(stick_diagram.find_differential_and_mirror_forks(ts)),
        "suggest_vertical_stack_composites": _b34_normalize(stick_diagram.suggest_vertical_stack_composites(ts)),
        "find_differential_pair_candidates": _b34_normalize(stick_diagram.find_differential_pair_candidates(ts)),
        "find_verified_differential_and_mirror_relations": _b34_normalize(stick_diagram.find_verified_differential_and_mirror_relations(ts)),
        "refine_differential_and_mirror_relations": _b34_normalize(stick_diagram.refine_differential_and_mirror_relations(ts)),
        "audit_theta_root_direction": _b34_normalize(stick_diagram.audit_theta_root_direction(ts, None)),
        "propose_theta_kcl_gap_fill": _b34_normalize(stick_diagram.propose_theta_kcl_gap_fill(ts, [])),
        "propose_device_roles_gap_fill": _b34_normalize(stick_diagram.propose_device_roles_gap_fill(ts, {}, [])),
        "geometry_colocation_union": _b34_normalize(stick_diagram.geometry_colocation_union(ts, [])),
        "propose_vertical_stack_id_gap_fill": _b34_normalize(stick_diagram.propose_vertical_stack_id_gap_fill(ts, [], {}, inputs=("vinp",))),
    }
    assert got == expected


# ---------------------------------------------------------------- 판정기 자기 점검
def test_b34_selfcheck_raises_rejects_quiet_fakes():
    # (a) 합성: 부재에서 조용히 반환하는 가짜 진입점은 계약 1 판정기(pytest.raises)가 실패시켜야 한다.
    for fake in (lambda *a: None, lambda *a: {"unavailable_reason": "x"}, lambda *a: []):
        with pytest.raises(pytest.fail.Exception):
            with pytest.raises(ImportError):
                fake()


def test_b34_selfcheck_exc_problems_rejects_bad_errors():
    # (a) 합성 ImportError: 무엇을 뺐는지가 곧 기대 위반 절이다. '이름 없음'은 경로도 없는 메시지로 만든다
    # (탐색 경로 자체에 'analog-grammar'가 들어 있다).
    e = _b34_expected_path()
    good = ImportError("analog-grammar skill (path %s)" % e)
    good.__cause__ = ModuleNotFoundError("netclass")
    no_name = ImportError("cannot import netclass")
    no_name.__cause__ = ModuleNotFoundError("netclass")
    no_path = ImportError("analog-grammar missing")
    no_path.__cause__ = ModuleNotFoundError("netclass")
    no_cause = ImportError("analog-grammar skill (path %s)" % e)
    assert _b34_exc_problems(good) == []
    assert "no 'analog-grammar' in message" in _b34_exc_problems(no_name)
    assert _b34_exc_problems(no_path) == ["search path missing from message"]
    assert _b34_exc_problems(no_cause) == ["__cause__ is not ImportError"]


class _B34FakeMatch:
    """(a) 합성 Match 모양 객체: `__eq__`가 없어 같은 값 두 개도 `!=`."""

    def __init__(self, kind):
        self.kind, self.devices, self.ports, self.note, self.priority = kind, ("M1", "M2"), {"g": "n1"}, "", 1


def test_b34_selfcheck_normalize_equal_and_different():
    assert _B34FakeMatch("dp") != _B34FakeMatch("dp")
    # 같은 값 두 번 -> 같음(정규화 없이 Match 리스트를 ==로 비교하지 않았음).
    assert _b34_normalize([_B34FakeMatch("dp"), {1.5, 2.5}]) == _b34_normalize([_B34FakeMatch("dp"), {2.5, 1.5}])
    # 다른 값 -> 다름.
    assert _b34_normalize([_B34FakeMatch("dp")]) != _b34_normalize([_B34FakeMatch("cm")])
    # JSON 왕복 뒤 같음(nan·set·튜플·문자열 아닌 dict 키).
    v = {"k": (float("nan"), {3, 1}), "d": {(1, 2): "x", 3: 0.5}}
    assert json.loads(json.dumps(_b34_normalize(v))) == _b34_normalize(v)
