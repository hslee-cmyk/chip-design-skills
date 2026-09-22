"""IC3 계약 test: 조용한 소실·덮어쓰기 -- 이름 전역 유일, 저장 필드 목록 단일 정의, 커버리지 재검증(20260922-ic3-completeness).

계획 N4.1 IC3, design `10-test-separation` §5.5·§6.7, spec card `20260922-ic3-completeness`.
표식 (1, ""): oracle (d) 계획서 N4.1 IC3 행(C6 `20260922-ts7-ic-xfail`이 단 그대로, 대조 test 대상).
A = `skills/analog-gmid-design/assets`. 새 심볼은 test 안에서 import한다(base에는 없어 ImportError가 red).

oracle 대조:
* test_coverage_and_field_completeness
  - 1 (a) 구성으로 정답이 정해진 입력: 사이징 이름 {A,B,C} 대 행 {r:[A,B]} -- 행에 넣지 않은 C가 곧 누락이다.
  - 2 (a) 손으로 만든 instance dict: 무엇을 뺐는지가 곧 그 필드의 기대값이다(design §5.5 필드 정의를 손으로 적용).
    이름 검사기도 (a) 손으로 만든 이름 목록: 겹치게 넣은 이름이 곧 기대값이다.
  - 상수 두 개의 값 (d) design §5.5 원문 튜플과 `save_instance_json` docstring의 입력 계약
    `{"W","L","ID","gm","gm_id"}`(interface card 인용).
  - 3 (a) library `two_stage_ota`를 `run_topology_pipeline`에 넣은 결과 + 손으로 만든 sizing: sizing에서 소자를
    뺐는지·필드를 뺐는지가 곧 거부 여부다. 입력 sizing 값은 판정 대상이 아닌 구성 입력이다.
  - 4 (a) library topology를 로드·변형한 임시 파일(WP-07): 이름을 무엇과 겹치게 바꿨는지가 곧 거부 여부다.
    오거부 0은 library JSON의 netlist·passive_elements 이름을 직접 읽은 목록에 충돌이 없다는 것(design §3
    A-4 실측 충돌 0)과 load_topology가 그 이름을 그대로 돌려준다는 것(로드는 합치기만 한다)에서 온다.
* test_linked_topology_files_merge_and_collision -- (a) library 회로 하나의 netlist를 두 파일로 나눈 픽스처
  (design §6.7 (5)): 나눈 파일을 합치면 원본과 같다는 것이 구성으로 정해진다. 나뉜 두 파일에 같은 이름을
  넣었는지가 곧 거부 여부다.

거부 입력(`pytest.raises(ValueError)`): sizing 소자 누락·sizing 필드 누락 `save_instance_json`(파일 없음),
소자 이름 중복·소자=수동소자·대소문자만 다른 겹침 `load_topology`, 연결 파일 두 곳의 같은 소자 이름·연결 파일
소자=수동소자 이름 `load_topology`.
"""
import copy
import json
import pathlib
import sys

import pytest

_ASSETS_DIR = pathlib.Path(__file__).resolve().parents[2]
_LIBRARY_DIR = _ASSETS_DIR / "library"
if str(_ASSETS_DIR) not in sys.path:
    sys.path.insert(0, str(_ASSETS_DIR))

# oracle (d) design §5.5 원문(`save_instance_json`이 지금 쓰는 키 전부, 선택 키 `scope_note` 제외).
_EXPECTED_TOP = ("schema_version", "topology_ref", "sizing", "netlist",
                 "floorplan", "box_shape", "audit_row_split", "coverage")
# oracle (d) `save_instance_json` docstring 입력 계약(interface card 인용, SizingResult 필드명).
_EXPECTED_SIZING = ("W", "L", "ID", "gm", "gm_id")
_OPTIONAL_TOP = "scope_note"


def _library_topologies():
    # `_TEMPLATE`은 회로가 아니라 작성 틀이다(파일 이름 `_` 머리) -- 나머지가 library 9회로.
    return sorted(p for p in _LIBRARY_DIR.glob("*.topology.json") if not p.name.startswith("_"))


def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def _netlist_names(topo):
    return [e["name"] for e in topo["netlist"]]


def _passive_names(topo):
    return [e["name"] for e in (topo.get("passive_elements") or [])]


def _sizing_entry(value):
    # 구성 입력: 다섯 필드를 모두 가진 sizing 한 소자분(값은 판정 대상이 아니다).
    return {k: value for k in _EXPECTED_SIZING}


def _hand_instance(names):
    # 손으로 만든 완전한 instance: 모든 최상위 키, 소자마다 sizing 다섯 필드, netlist에 모든 소자, coverage 누락 없음,
    # 선택 키 scope_note 포함(완전성 판정 대상 아님).
    return {
        "schema_version": "2.0",
        "topology_ref": "hand/made.topology.json",
        "sizing": {n: _sizing_entry(1.0) for n in names},
        "netlist": [{"name": n, "kind": "nmos", "source": "s", "drain": "d", "gate": "g"} for n in names],
        "floorplan": {"placements": {}},
        "box_shape": {"ok": True},
        "audit_row_split": {"ok": True, "checks": []},
        "coverage": {"ok": True, "missing": []},
        _OPTIONAL_TOP: "선택 키",
    }


def _verdict_fields(v):
    return {
        "missing_top": tuple(v.missing_top),
        "missing_sizing": tuple(v.missing_sizing),
        "missing_fields": {k: tuple(f) for k, f in dict(v.missing_fields).items()},
        "missing_netlist": tuple(v.missing_netlist),
        "coverage_missing": tuple(v.coverage_missing),
    }


_NO_MISSING = {"missing_top": (), "missing_sizing": (), "missing_fields": {},
               "missing_netlist": (), "coverage_missing": ()}


@pytest.mark.gmid_ic("IC3", phase="1", case="")
def test_coverage_and_field_completeness(tmp_path):
    from stick_diagram import (INSTANCE_SIZING_FIELDS, INSTANCE_TOP_FIELDS, check_instance_completeness,
                               check_stick_diagram_coverage, check_topology_name_uniqueness, load_topology,
                               run_topology_pipeline, save_instance_json)

    # ---- 상수: 저장 필드 목록 단일 정의(계약 1). oracle (d) design §5.5 원문·docstring 입력 계약.
    assert tuple(INSTANCE_TOP_FIELDS) == _EXPECTED_TOP
    assert tuple(INSTANCE_SIZING_FIELDS) == _EXPECTED_SIZING

    # ---- 1. 커버리지 재검증. oracle (a): 행에 A,B만 넣었으니 C가 누락, 전부 넣으면 누락 없음.
    cov = check_stick_diagram_coverage(["A", "B", "C"], {"r": ["A", "B"]})
    assert not cov.ok
    assert set(cov.missing) == {"C"}
    cov_full = check_stick_diagram_coverage(["A", "B", "C"], {"r": ["A", "B"], "s": ["C"]})
    assert cov_full.ok
    assert set(cov_full.missing) == set()

    # ---- 2. check_instance_completeness(계약 2). oracle (a): 뺀 것이 곧 그 필드의 기대값, 다른 필드는 비어 있다.
    names = ("M1", "M2", "M3")
    full = _hand_instance(names)
    v_ok = check_instance_completeness(full, names)
    assert v_ok.ok
    assert _verdict_fields(v_ok) == _NO_MISSING

    # 2-a 최상위 키 하나 뺌(sizing·netlist·coverage는 다른 필드의 입력이라 여기서는 나머지 다섯 키를 하나씩 뺀다).
    for key in ("schema_version", "topology_ref", "floorplan", "box_shape", "audit_row_split"):
        inst = copy.deepcopy(full)
        del inst[key]
        v = check_instance_completeness(inst, names)
        assert not v.ok, key
        assert _verdict_fields(v) == {**_NO_MISSING, "missing_top": (key,)}, key

    # 2-b 소자 하나를 sizing에서 뺌.
    inst = copy.deepcopy(full)
    del inst["sizing"]["M2"]
    v = check_instance_completeness(inst, names)
    assert not v.ok
    assert _verdict_fields(v) == {**_NO_MISSING, "missing_sizing": ("M2",)}

    # 2-c 소자 하나의 필드 하나를 뺌(다섯 필드 각각).
    for field in _EXPECTED_SIZING:
        inst = copy.deepcopy(full)
        del inst["sizing"]["M3"][field]
        v = check_instance_completeness(inst, names)
        assert not v.ok, field
        assert _verdict_fields(v) == {**_NO_MISSING, "missing_fields": {"M3": (field,)}}, field

    # 2-d netlist에서 소자 하나를 뺌.
    inst = copy.deepcopy(full)
    inst["netlist"] = [e for e in inst["netlist"] if e["name"] != "M1"]
    v = check_instance_completeness(inst, names)
    assert not v.ok
    assert _verdict_fields(v) == {**_NO_MISSING, "missing_netlist": ("M1",)}

    # 2-e coverage.missing이 비지 않음.
    inst = copy.deepcopy(full)
    inst["coverage"] = {"ok": False, "missing": ["M3"]}
    v = check_instance_completeness(inst, names)
    assert not v.ok
    assert _verdict_fields(v) == {**_NO_MISSING, "coverage_missing": ("M3",)}

    # 2-f 이름 검사기 직접(계약 3). oracle (a): 손으로 만든 이름 목록 -- 겹치게 넣은 이름이 곧 기대값.
    n_ok = check_topology_name_uniqueness(["M1", "M2"], ["CL"])
    assert n_ok.ok
    assert tuple(n_ok.duplicate_devices) == ()
    assert tuple(n_ok.device_passive_overlap) == ()
    assert tuple(n_ok.case_only_collisions) == ()
    n_dup = check_topology_name_uniqueness(["M1", "M2", "M1"], ["CL"])
    assert not n_dup.ok
    assert tuple(n_dup.duplicate_devices) == ("M1",)
    assert tuple(n_dup.device_passive_overlap) == ()
    assert tuple(n_dup.case_only_collisions) == ()
    n_pas = check_topology_name_uniqueness(["M1", "CL"], ["CL", "Cc"])
    assert not n_pas.ok
    assert tuple(n_pas.duplicate_devices) == ()
    assert tuple(n_pas.device_passive_overlap) == ("CL",)
    assert tuple(n_pas.case_only_collisions) == ()
    n_case = check_topology_name_uniqueness(["M1", "m1", "M2"], ["CL"])
    assert not n_case.ok
    assert tuple(n_case.duplicate_devices) == ()
    assert tuple(n_case.device_passive_overlap) == ()
    assert {frozenset(g) for g in n_case.case_only_collisions} == {frozenset({"M1", "m1"})}
    n_case_pas = check_topology_name_uniqueness(["M1", "cl"], ["CL"])
    assert not n_case_pas.ok
    assert tuple(n_case_pas.duplicate_devices) == ()
    assert tuple(n_case_pas.device_passive_overlap) == ()
    assert {frozenset(g) for g in n_case_pas.case_only_collisions} == {frozenset({"cl", "CL"})}

    # ---- 3. 배선(저장, 계약 4). library two_stage_ota를 파이프라인에 넣는다.
    # 구성 입력: 소자마다 자기 스택, n_fingers=2 x finger_w=1.0 = w=2.0(W가 finger_w의 정수배).
    topo_path = str(_LIBRARY_DIR / "two_stage_ota.topology.json")
    topo_names = _netlist_names(_read_json(topo_path))
    overrides = {n: {"n_fingers": 2, "finger_w": 1.0, "w": 2.0, "stack_id": f"stack_{n}"} for n in topo_names}
    pipeline_result = run_topology_pipeline(topo_path, overrides)
    sizing_full = {n: _sizing_entry(1.0) for n in topo_names}

    # 3-a sizing에서 소자 하나를 뺌 -> ValueError, 파일 없음. oracle (a): 뺀 소자가 곧 누락.
    dropped = topo_names[0]
    out_a = tmp_path / "drop_device.instance.json"
    sizing_drop = {n: s for n, s in sizing_full.items() if n != dropped}
    with pytest.raises(ValueError) as exc_a:
        save_instance_json(str(out_a), topo_path, sizing_drop, pipeline_result)
    assert dropped in str(exc_a.value)
    assert not out_a.exists()

    # 3-b 소자 하나의 필드 하나를 뺌 + 다른 소자 하나를 뺌 -> ValueError(모든 누락을 담는다), 파일 없음.
    field_dev, gone_dev = topo_names[1], topo_names[2]
    sizing_multi = copy.deepcopy(sizing_full)
    del sizing_multi[field_dev]["gm"]
    del sizing_multi[gone_dev]
    out_b = tmp_path / "multi.instance.json"
    with pytest.raises(ValueError) as exc_b:
        save_instance_json(str(out_b), topo_path, sizing_multi, pipeline_result)
    assert field_dev in str(exc_b.value)
    assert gone_dev in str(exc_b.value)
    assert not out_b.exists()

    # 3-c 빠짐없는 sizing -> 파일이 생기고, 다시 읽은 instance가 2의 검사에서 ok.
    # 계약 1: data 키 순서 = INSTANCE_TOP_FIELDS(json은 키 순서를 보존한다).
    out_c = tmp_path / "full.instance.json"
    save_instance_json(str(out_c), topo_path, sizing_full, pipeline_result)
    assert out_c.exists()
    saved = _read_json(out_c)
    assert [k for k in saved if k != _OPTIONAL_TOP] == list(_EXPECTED_TOP)
    assert saved["sizing"] == sizing_full
    assert sorted(e["name"] for e in saved["netlist"]) == sorted(topo_names)
    assert saved["coverage"]["missing"] == []
    v_saved = check_instance_completeness(saved, topo_names)
    assert v_saved.ok
    assert _verdict_fields(v_saved) == _NO_MISSING

    # ---- 4. 배선(로드, 계약 4·5, WP-07 library 로드·변형).
    # 4-0 오거부 0(계약 5): 변형하지 않은 library 9회로 전부. 이름 검사기가 원본 이름 목록을 통과시키고,
    # 원본 파일 그대로의 load_topology가 JSON netlist와 같은 이름 목록을 돌려준다.
    lib = _library_topologies()
    assert len(lib) == 9
    for p in lib:
        topo = _read_json(p)
        v_names = check_topology_name_uniqueness(_netlist_names(topo), _passive_names(topo))
        assert v_names.ok, p.name
        transistors, _meta = load_topology(str(p))
        assert [t.name for t in transistors] == _netlist_names(topo), p.name

    # 4-1 변형 거부: 수동소자가 있는 library 회로(ngcc_3stage_ff)의 두 번째 소자 이름을 바꾼다.
    base_topo = _read_json(_LIBRARY_DIR / "ngcc_3stage_ff.topology.json")
    first = base_topo["netlist"][0]["name"]
    passive0 = base_topo["passive_elements"][0]["name"]
    mutations = {
        "duplicate_device": first,           # (i) 다른 소자 이름과 같게
        "device_equals_passive": passive0,   # (ii) 수동소자 이름과 같게
        "case_only": first.swapcase(),       # (iii) 다른 소자와 대소문자만 다르게
    }
    assert mutations["case_only"] != first
    for label, new_name in mutations.items():
        mutated = copy.deepcopy(base_topo)
        mutated["netlist"][1]["name"] = new_name
        mpath = tmp_path / f"{label}.topology.json"
        _write_json(mpath, mutated)
        with pytest.raises(ValueError):
            load_topology(str(mpath))


@pytest.mark.gmid_ic("IC3", phase="1", case="")
def test_linked_topology_files_merge_and_collision(tmp_path):
    """design §6.7 (5) 연결 파일 픽스처 -- `load_topology`의 연결 파일 루프를 실제로 지나게 한다."""
    from stick_diagram import load_topology

    src = _LIBRARY_DIR / "ngcc_3stage_ff.topology.json"
    topo = _read_json(src)
    orig_transistors, orig_meta = load_topology(str(src))
    netlist = topo["netlist"]
    k = len(netlist) // 2

    def write_split(dirname, part_b_netlist):
        # 진입 파일 part_a = 원본 그대로에 netlist 앞 절반, 형제 part_b = netlist 뒤 절반(서로를 연결 목록에 둔다).
        d = tmp_path / dirname
        d.mkdir()
        part_a = copy.deepcopy(topo)
        part_a["netlist"] = copy.deepcopy(netlist[:k])
        part_a["linked_topology_files"] = ["part_b.topology.json"]
        part_b = {"schema_version": topo["schema_version"], "symmetry": {"matching_pairs": []},
                  "netlist": part_b_netlist, "linked_topology_files": ["part_a.topology.json"]}
        _write_json(d / "part_a.topology.json", part_a)
        _write_json(d / "part_b.topology.json", part_b)
        return str(d / "part_a.topology.json")

    # (5-a) 합친 결과 = 원본. oracle (a): 원본 netlist를 둘로 나눴을 뿐이라 합치면 소자 수·이름·소자 내용이 같다.
    entry = write_split("split_ok", copy.deepcopy(netlist[k:]))
    merged, merged_meta = load_topology(entry)
    assert len(merged) == len(orig_transistors) == len(netlist)
    assert sorted(t.name for t in merged) == sorted(_netlist_names(topo))
    assert {t.name: t for t in merged} == {t.name: t for t in orig_transistors}
    # meta: 진입 파일은 원본의 비-netlist 필드를 그대로 가졌으니 같은 값이다. 연결 목록만 구성상 다르다 --
    # 원본은 연결 파일이 없고, 나눈 쪽은 진입 파일이 선언한 `part_b.topology.json` 하나를 읽었다.
    assert set(merged_meta) == set(orig_meta)
    for key in orig_meta:
        if key == "_linked_files_loaded":
            continue
        assert merged_meta[key] == orig_meta[key], key
    assert list(orig_meta["_linked_files_loaded"]) == []
    assert list(merged_meta["_linked_files_loaded"]) == ["part_b.topology.json"]

    # (5-b) 나뉜 두 파일에 같은 소자 이름 -> ValueError. oracle (a): part_b 첫 소자를 part_a 첫 소자 이름으로 바꿨다.
    dup_b = copy.deepcopy(netlist[k:])
    dup_b[0]["name"] = netlist[0]["name"]
    entry_dup = write_split("split_dup", dup_b)
    with pytest.raises(ValueError):
        load_topology(entry_dup)

    # (5-c) 연결 파일의 소자 이름 = 진입 파일의 수동소자 이름 -> ValueError. oracle (a): 겹치게 바꿨다.
    pas_b = copy.deepcopy(netlist[k:])
    pas_b[0]["name"] = topo["passive_elements"][0]["name"]
    entry_pas = write_split("split_passive", pas_b)
    with pytest.raises(ValueError):
        load_topology(entry_pas)
