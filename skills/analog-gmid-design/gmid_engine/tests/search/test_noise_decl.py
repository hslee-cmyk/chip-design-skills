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
from graph.s1v_hand import BIG_BUDGET, LIBRARY, build_lib

NAME = "two_stage_ota"


def _lib_spec(td):
    return load_sizing_spec(str(LIBRARY / (NAME + ".sizing_spec.json")), td, metric_catalog())


def _decl_of_library():
    td = load_topology(str(LIBRARY / (NAME + ".topology.json")))
    spec = _lib_spec(td)
    _s1, s1v = build_lib(NAME, spec)
    return spec, s1v, noise_decl(spec, s1v)


def test_two_stage_input_cell_is_differential_pair():
    spec, _s1v, d = _decl_of_library()
    assert isinstance(d, NoiseDecl)
    assert d.feedback == () and d.sampling_caps == ()
    hits = [cell for cell in d.input_cells if set(cell[0]) == {"vin_n", "vin_p"} and tuple(cell[1]) == ("OUT",)]
    assert len(hits) == 1, d.input_cells
    assert tuple(hits[0][2]) == ("M1", "M2")


def test_no_s1v_no_input_cells():
    td = load_topology(str(LIBRARY / (NAME + ".topology.json")))
    d = noise_decl(_lib_spec(td), None)
    assert d.input_cells == ()
    assert d.feedback == ()


def test_feedback_and_sampling_caps_from_spec():
    spec = SimpleNamespace(feedback=("Cf2", "Cf1"),
                           noise_testbench=SimpleNamespace(sampling_caps=(SimpleNamespace(element="Cs1", source=None),
                                                                          SimpleNamespace(element="Cs2", source=None))))
    d = noise_decl(spec, None)
    assert d.feedback == ("Cf2", "Cf1")
    assert d.sampling_caps == ("Cs1", "Cs2")


def test_pending_feedback_is_none():
    """결정 대기 표지(tuple 아님) -> None(폐루프 모드 미정, noise_feedback_undeclared 로 이어진다)."""
    spec = SimpleNamespace(feedback=object(), noise_testbench=None)
    assert noise_decl(spec, None).feedback is None


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
    s1 = build_s1(td, {mapping[k]: v for k, v in {"vdd": 1.8, "gnd": 0.0}.items()})
    moved = noise_decl(spec, build_s1v(s1, spec, count_budget=BIG_BUDGET, stop_on_unsupported=False))
    _spec, _s1v, base = _decl_of_library()

    def mapped(cells, fn):
        return {(frozenset(map(fn, a)), frozenset(map(fn, b)), frozenset(map(fn, c))) for a, b, c in cells}

    assert base.input_cells
    assert mapped(moved.input_cells, lambda x: x) == mapped(base.input_cells, lambda x: mapping.get(x, x))
    assert moved.feedback == tuple(mapping.get(x, x) for x in base.feedback)
