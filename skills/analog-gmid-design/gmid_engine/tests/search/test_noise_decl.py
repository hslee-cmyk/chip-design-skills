"""[U8 2026-10-09] `search.noise_decl(spec, s1v) -> NoiseDecl` (설계 41 §7.1 '입력 소자는 S1v 에서 gain 제약 전달 뷰의 첫 이득 블록 input 셀',
§7.3 '폐루프 모드'·'스위치', search CONTRACT 11절).

oracle:
* (d) 회로 해석: two_stage_ota(library) 의 첫 이득 단은 차동쌍 M1(gate vin_n)·M2(gate vin_p) -- 전달 뷰(여기 vin_n·vin_p, 감지 OUT)의 입력 셀 = {M1, M2}.
  topology netlist(M1 d=D3 g=vin_n, M2 d=O1 g=vin_p, 꼬리 M5)에서 읽은 사실이다.
* (d) spec 문장: feedback 이 tuple 이면 그대로(빈 tuple = 되먹임 없음), 결정 대기(PendingMark 등 tuple 아님)면 None. `noise_testbench.sampling_caps` 의 element 이름.
  s1v 가 None 이면 input_cells = ()(search 11절 '미측정으로 보고 -- 조용히 통과하지 않는다').
* (a) 이름 전단사: 무작위 이름 치환(generality topogen)한 회로의 선언 = 원래 선언을 같은 치환으로 옮긴 것.
"""
import json
from pathlib import Path
from types import SimpleNamespace

from gmid_engine.authoring import load_sizing_spec, load_topology
from gmid_engine.graph import build_s1, build_s1v
from gmid_engine.metrics import NoiseDecl, metric_catalog
from gmid_engine.search.noise_decl import noise_decl          # search 패키지 `__all__` 밖(모듈 이름과 같음) -- 모듈에서 가져온다

from generality.topogen import random_renaming, rename, rename_spec
from graph.s1v_hand import BIG_BUDGET, LIBRARY, build_lib, fresh_run, lib_supplies

# [U17 ①-b] `noise_decl` 은 계산 블록이 됐다(설계 40 v1.9.1 §2.4.8 '잡음 입력 셀' 행, D7): `noise_decl(snapshot, feedback, sampling_caps)` -> S0 수준 필드
# `graph/s1v: noise_input_cells`(값 = NoiseDecl 전체), reads `graph/s1v: views`. spec -> extras 변환(feedback tuple 아니면 None, sampling_caps = testbench 의
# 커패시터 이름)은 `build_search_context` 가 한다(search_context._s0_blocks). 아래 `_decl` 은 S1Graph 를 S0 수준 권한표로 넓혀 블록을 부르고 필드를 읽는다.


def _decl(graph, feedback, caps):
    from gmid_engine.graph import S1V_KEY
    from gmid_engine.search.s0_fields import S0_WRITERS
    snap = noise_decl(graph.snapshot.widen(S0_WRITERS), feedback, caps, **fresh_run())    # [XRUN-F1 card B C4] 새 실행 하나
    return snap.value("graph", S1V_KEY, "noise_input_cells")


def _spec_extras(spec):
    """library spec 의 선언 그대로(two_stage_ota: feedback = (), noise_testbench 없음 -- 입력 값)."""
    tb = spec.noise_testbench
    return (tuple(spec.feedback) if isinstance(spec.feedback, tuple) else None,
            () if tb is None else tuple(c.element for c in tb.sampling_caps))

NAME = "two_stage_ota"


def _lib_spec(td):
    return load_sizing_spec(str(LIBRARY / (NAME + ".sizing_spec.json")), td, metric_catalog())


def _decl_of_library():
    td = load_topology(str(LIBRARY / (NAME + ".topology.json")))
    spec = _lib_spec(td)
    _s1, s1v = build_lib(NAME, spec)
    return spec, s1v, _decl(s1v.graph, *_spec_extras(spec))


def test_two_stage_input_cell_is_differential_pair():
    spec, _s1v, d = _decl_of_library()
    assert isinstance(d, NoiseDecl)
    assert d.feedback == () and d.sampling_caps == ()
    hits = [cell for cell in d.input_cells if set(cell[0]) == {"vin_n", "vin_p"} and tuple(cell[1]) == ("OUT",)]
    assert len(hits) == 1, d.input_cells
    assert tuple(hits[0][2]) == ("M1", "M2")


def test_no_s1v_no_input_cells():
    td = load_topology(str(LIBRARY / (NAME + ".topology.json")))
    s1 = build_s1(td, lib_supplies(NAME), **fresh_run())       # S1v 뷰 필드 없는 S0 수준 스냅샷
    d = _decl(s1, *_spec_extras(_lib_spec(td)))
    assert d.input_cells == ()
    assert d.feedback == ()


def test_feedback_and_sampling_caps_from_spec():
    # [U17 ①-b] 블록 extras 로 받은 feedback·sampling_caps 가 순서 그대로 필드 값에 실린다(spec -> extras 는 build_search_context).
    td = load_topology(str(LIBRARY / (NAME + ".topology.json")))
    d = _decl(build_s1(td, lib_supplies(NAME), **fresh_run()), ("Cf2", "Cf1"), ("Cs1", "Cs2"))
    assert d.feedback == ("Cf2", "Cf1")
    assert d.sampling_caps == ("Cs1", "Cs2")


def test_pending_feedback_is_none():
    """결정 대기 표지(tuple 아님) -> None(폐루프 모드 미정, noise_feedback_undeclared 로 이어진다).
    [U17 ①-b] 표지 -> None 변환은 build_search_context 가 extras 를 만들 때 한다 -- 블록은 None 을 그대로 필드에 싣는다."""
    td = load_topology(str(LIBRARY / (NAME + ".topology.json")))
    assert _decl(build_s1(td, lib_supplies(NAME), **fresh_run()), None, ()).feedback is None


def test_name_bijection(tmp_path):
    raw = json.loads((LIBRARY / (NAME + ".topology.json")).read_text(encoding="utf-8"))
    mapping = random_renaming(raw, 20261009)
    doc = rename(raw, mapping)
    tp = Path(tmp_path) / (doc["topology_name"] + ".topology.json")
    tp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    td = load_topology(str(tp))
    spec_doc = json.loads((LIBRARY / (NAME + ".sizing_spec.json")).read_text(encoding="utf-8"))
    sp = Path(tmp_path) / (doc["topology_name"] + ".sizing_spec.json")
    sp.write_text(json.dumps(rename_spec(spec_doc, mapping, td.connectivity_fp), indent=1), encoding="utf-8")
    spec = load_sizing_spec(str(sp), td, metric_catalog())
    run = fresh_run()                      # 이름 바꾼 회로 = 다른 실행
    s1 = build_s1(td, {mapping[k]: v for k, v in {"vdd": 1.8, "gnd": 0.0}.items()}, **run)
    moved = _decl(build_s1v(s1, spec, count_budget=BIG_BUDGET, stop_on_unsupported=False, **run), *_spec_extras(spec))
    _spec, _s1v, base = _decl_of_library()

    def mapped(cells, fn):
        return {(frozenset(map(fn, a)), frozenset(map(fn, b)), frozenset(map(fn, c))) for a, b, c in cells}

    assert base.input_cells
    assert mapped(moved.input_cells, lambda x: x) == mapped(base.input_cells, lambda x: mapping.get(x, x))
    assert moved.feedback == tuple(mapping.get(x, x) for x in base.feedback)
