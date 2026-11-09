"""B41 test 공백 보강 초안: `save_instance_json`의 선택 키 `scope_note` 복사(test-only, 기존 동작 고정).

선언(oracle (d) docstring 원문, `stick_diagram.save_instance_json`):
  "`pipeline_result`에 `scope_note`(str)를 선택적으로 넣으면 그대로 옮겨 쓴다 -- 이 instance가 전체 회로가 아니라 일부만
   감사/배치했을 때 그 범위를 정직하게 밝히는 용도"
그리고 design 10 IC3 §5.5 저장 필드 목록(`INSTANCE_TOP_FIELDS`)은 `scope_note`를 **선택 키**로 뺀다(test_ic3 `_OPTIONAL_TOP`).

* 계약 S1: `pipeline_result["scope_note"]`가 비지 않은 문자열이면 쓴 파일의 최상위 `scope_note`가 그 문자열과 같다.
* 계약 S2: `pipeline_result`에 `scope_note` 키가 없으면 쓴 파일에 최상위 `scope_note` 키가 없다.

입력 구성은 `test_df36_instance_relpath.py`·`test_ic3.py`와 같은 공개 경로(library topology를 `run_topology_pipeline`에 넣은
결과 + 소자마다 다섯 필드 sizing) -- 판정 대상이 아닌 구성 입력이다. 기대값 = test가 만든 문자열(oracle (a) 구성), 피검 출력으로 만들지 않는다.
library 회로 전부로 돈다(회로 이름을 박지 않는다).
"""
import copy
import functools
import json
import os
import pathlib
import sys

import pytest

# contracts(0) -> tests(1) -> assets(2)
_THIS_FILE = pathlib.Path(__file__).resolve()
_ASSETS_DIR = _THIS_FILE.parents[2]
_LIBRARY_DIR = _ASSETS_DIR / "library"
if str(_ASSETS_DIR) not in sys.path:
    sys.path.insert(0, str(_ASSETS_DIR))

_SIZING_FIELDS = ("W", "L", "ID", "gm", "gm_id")


def _library_topologies():
    # `_TEMPLATE`은 회로가 아니라 작성 틀이다(파일 이름 `_` 머리) -- test_ic3·test_df36과 같은 규칙.
    return sorted(p for p in _LIBRARY_DIR.glob("*.topology.json") if not p.name.startswith("_"))


_LIBRARY_NAMES = [p.name for p in _library_topologies()]


def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@functools.lru_cache(maxsize=16)
def _pipeline_inputs(name: str):
    """library 회로 하나의 (topology 절대 경로, sizing, pipeline_result) -- 구성 입력, 회로마다 한 번."""
    from stick_diagram import run_topology_pipeline
    topo_path = _LIBRARY_DIR / name
    names = [e["name"] for e in _read_json(topo_path)["netlist"]]
    overrides = {n: {"n_fingers": 2, "finger_w": 1.0, "w": 2.0, "stack_id": f"stack_{n}"} for n in names}
    pipeline_result = run_topology_pipeline(str(topo_path), overrides)
    sizing = {n: {k: 1.0 for k in _SIZING_FIELDS} for n in names}
    return topo_path, sizing, pipeline_result


def _save(out_path, name: str, **extra) -> dict:
    from stick_diagram import save_instance_json
    topo_path, sizing, pipeline_result = _pipeline_inputs(name)
    pr = copy.deepcopy(pipeline_result)
    pr.pop("scope_note", None)
    pr.update(extra)
    save_instance_json(str(out_path), str(topo_path), copy.deepcopy(sizing), pr)
    assert os.path.exists(out_path), f"파일이 생기지 않았다: {out_path}"
    return _read_json(out_path)


@pytest.mark.parametrize("name", _LIBRARY_NAMES)
def test_scope_note_copied_verbatim(tmp_path, name):
    # 계약 S1. oracle (a): 기대값 = 이 test가 만든 문자열(비 ASCII·공백·구두점 포함 -- 가공 없이 옮기는지).
    note = f"부분 범위: {name} -- cells 1/3 (b41)"
    data = _save(tmp_path / "with_note.instance.json", name, scope_note=note)
    assert data.get("scope_note") == note, f"scope_note {data.get('scope_note')!r} != 넣은 값 {note!r}"


@pytest.mark.parametrize("name", _LIBRARY_NAMES)
def test_scope_note_absent_when_not_given(tmp_path, name):
    # 계약 S2. oracle (d): scope_note는 선택 키 -- 넣지 않으면 파일에 없다.
    data = _save(tmp_path / "no_note.instance.json", name)
    assert "scope_note" not in data, f"넣지 않은 scope_note가 있다: {data.get('scope_note')!r}"
