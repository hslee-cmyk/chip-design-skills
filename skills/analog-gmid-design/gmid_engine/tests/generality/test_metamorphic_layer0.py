"""metamorphic: 층 0 시작점이 이름 치환·순서 섞기에 비트 동일한가 (search CONTRACT r11·r12 3.21 3a·3.23 4, sizing 3.0b 성질 (7)).

변형 = 모든 원소·넷 이름의 무작위 전단사 σ(topogen `random_renaming` + `rename`) + 원소·포트·키 순서 섞기(`shuffle_order`). spec 도 같은 σ 로
옮긴다(이름 자리 = 키·문자열 값, 출처 객체는 그대로; meta.topology_fp 는 새 topology 지문으로 맞춘다 -- 입력 준비).
oracle (a): 기대값 = 변형 전 실행 결과(같은 함수의 다른 입력)를 정점 대응 τ 로 옮긴 것. τ = 두 컨텍스트에서 `dc_colour`(정점마다 유일, 3.0b)가
같은 정점끼리의 짝 -- 궤도 구성원은 서로 바뀔 수 있어 σ 가 아니라 τ 로 비교한다(3.0b 성질 (7)).
비교(허용오차 없음, float.hex): `layer0_start` 의 start θ(τ 키)·L 칸(τ 키)·t·origin_point·kernel_calls·stop·probes, 그리고 S3 evals 줄 순서대로
평가한 모든 θ(τ 키)·상태 -- 시작점이 없는 회로(toy LUT 에서 봉인 실패)도 시험 점 열 전체가 같아야 한다.
대상: library 9회로(two_stage_ota_sf 는 spec 이 two_stage_ota 를 value_from_file 로 참조해 원본 두 파일을 같은 폴더에 둔다) + 합성 3종
(syn_cs_load·syn_diffpair5·syn_follower -- syn_cascode 는 전압원이라 sizing 지원 밖) + 대칭 손 회로(궤도 묶음 있음).
LUT = sizing conftest r4 toy(빠르고 결정론). search·sizing `.py` 소스는 열람하지 않았다.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from .topogen import random_renaming, rename, shuffle_order, synthetic_topologies

LIBRARY = Path(__file__).resolve().parents[3] / "assets" / "library"
LIB = ("common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
       "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf")
SYN = ("syn_cs_load", "syn_diffpair5", "syn_follower")
SYN_SUPPLIES = {"qp_hi": 1.8, "qp_lo": 0.0}
EVAL_BUDGET = 40
VALUE_KEYS = ("value_ohm", "value_farad", "value_amp", "value_volt")


@pytest.fixture(scope="module")
def lut(tmp_path_factory):
    from search.conftest import write_r4_lut
    return write_r4_lut(tmp_path_factory.mktemp("l0m_lut"))


@pytest.fixture
def roots():
    made = []

    def new():
        d = tempfile.mkdtemp(prefix="l0m", dir=os.environ.get("TEMP") or None)
        made.append(d)
        return d
    yield new
    for d in made:
        shutil.rmtree(d, ignore_errors=True)


def ren_spec(obj, m):
    """spec dict 의 이름 자리를 σ 로: 키·문자열 값(정확히 같은 문자열만), 출처 객체(source)는 그대로."""
    if isinstance(obj, dict):
        return {m.get(k, k): (v if k == "source" else ren_spec(v, m)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [ren_spec(x, m) for x in obj]
    if isinstance(obj, str):
        return m.get(obj, obj)
    return obj


def _syn_spec(td, doc, m):
    from metrics.conftest import spec_json
    els = [(e["name"], e["kind"], next(e[k] for k in VALUE_KEYS if k in e))
           for key in ("passive_elements", "ideal_sources") for e in doc.get(key) or []]
    return spec_json(td, {m.get(k, k): v for k, v in SYN_SUPPLIES.items()}, els, (), ())


def build(tmp, topo_doc, spec_doc, lut, archive_root, extra_files=(), m=None):
    """topology·spec(dict 또는 None -> 합성 spec) -> SearchContext. extra_files = 같은 폴더에 둘 참조 파일 경로."""
    from gmid_engine.authoring import load_sizing_spec, load_topology
    from gmid_engine.graph import build_s1
    from gmid_engine.search import SearchSettings, build_search_context
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec
    from search.conftest import SRC, new_access, write_decls
    from sizing.conftest import spec_catalog

    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    for f in extra_files:
        shutil.copy(f, tmp / Path(f).name)
    tp = tmp / (topo_doc["topology_name"] + ".topology.json")
    tp.write_text(json.dumps(topo_doc), encoding="utf-8")
    td = load_topology(str(tp))
    spec_doc = _syn_spec(td, topo_doc, m or {}) if spec_doc is None else copy.deepcopy(spec_doc)
    spec_doc["meta"]["topology_fp"] = td.connectivity_fp
    spec_doc["meta"]["circuit"] = td.name
    sp = tmp / (topo_doc["topology_name"] + ".sizing_spec.json")
    sp.write_text(json.dumps(spec_doc), encoding="utf-8")
    spec = load_sizing_spec(str(sp), td, spec_catalog())
    inputs = dc_inputs_from_spec(spec)
    dc = build_kernel_context(build_s1(td, dict(inputs.supplies_v)), inputs, new_access(lut))
    pdk, rule = write_decls(tmp / "pdk")
    settings = SearchSettings(600.0, EVAL_BUDGET, (1e3, 1e6), SRC, (1e-13, 1e-11))
    return build_search_context(dc, spec, settings, archive_root, pdk, rule)


def tau(sctx):
    b = sctx.dc.base
    dv = dict(b.column("device", "dc_colour"))
    nv = dict(b.column("node", "dc_colour"))

    def f(key):
        kind, name = key
        if name in dv:
            return kind, "d", dv[name]
        if name in nv:
            return kind, "n", nv[name]
        return kind, "k", name
    return f


def signature(sctx, r, root):
    t = tau(sctx)
    start = None
    if r.start is not None:
        start = (sorted((t(k), float(v).hex()) for k, v in r.start.theta),
                 sorted((t(("L", m)), c) for (m, _), c in zip(sctx.domain.l_cells, r.start.cells)))
    lines = []
    p = Path(root) / sctx.context_fp / "evals.jsonl"
    if p.exists():
        for ln in p.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                d = json.loads(ln)
                lines.append((d["status"], sorted((t(tuple(k)), float(v).hex()) for k, v in d["theta"])))
    return {"start": start, "t": None if r.t is None else float(r.t).hex(), "origin": r.origin_point,
            "kernel_calls": r.kernel_calls, "stop": r.stop, "probes": r.probes, "evals": lines,
            "n_vars": len(sctx.domain.variables), "ties": len(sctx.domain.ties)}


def _case(name):
    """-> (topology dict, spec dict | None, 참조 파일들)."""
    if name in SYN:
        return synthetic_topologies()[name], None, ()
    if name == "hand_sym":
        from search.canon_cases import sym_doc
        return sym_doc("hand_sym_l0m"), "SYM", ()
    raw = json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))
    spec = json.loads((LIBRARY / (name + ".sizing_spec.json")).read_text(encoding="utf-8"))
    # [U8 2026-10-09] 값 있는 잡음 제약은 잡음 r1 LUT 를 요구한다(search CONTRACT 11절 noise_lut_missing) -- 이 test 의 LUT 는 잡음 없는 r4 toy 라
    # 잡음 제약만 뺀다(층 0 비트 동일성이 목적; 잡음 metric 의 이름 치환 불변은 실데이터 하네스(Env, 잡음 r1 포함)와 tests/metrics 잡음 test 가 본다)
    spec["human"]["constraints"] = [c for c in spec["human"]["constraints"] if not str(c.get("metric", "")).startswith("noise_")]
    extra = ()
    if name == "two_stage_ota_sf":                           # value_from_file 참조 대상(원본 그대로)
        extra = (LIBRARY / "two_stage_ota.topology.json", LIBRARY / "two_stage_ota.sizing_spec.json")
    return raw, spec, extra


def _sym_spec(td_doc, m=None):
    """대칭 손 회로 spec: CL1·CL2 engine + 같은 상자(묶음 가능)."""
    from metrics.conftest import spec_json

    from gmid_engine.authoring import load_topology
    f = (lambda n: n) if m is None else (lambda n: m.get(n, n))
    tmp = Path(tempfile.mkdtemp(prefix="l0s", dir=os.environ.get("TEMP") or None))
    try:
        tp = tmp / (td_doc["topology_name"] + ".topology.json")
        tp.write_text(json.dumps(td_doc), encoding="utf-8")
        td = load_topology(str(tp))
        doc = spec_json(td, {f("vdd"): 1.8, f("gnd"): 0.0}, [(f("CL1"), "capacitor", None), (f("CL2"), "capacitor", None)], (), ())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    src = {"kind": "user_spec", "record": "l0 metamorphic", "decided": "2026-10-08"}
    doc["human"]["search"]["theta_bounds"] = {f(n): {"min": 1e-13, "max": 1e-11, "source": dict(src)} for n in ("CL1", "CL2")}
    return doc


@pytest.mark.parametrize("name", LIB + SYN + ("hand_sym",))
def test_layer0_bit_identical_under_renaming_and_shuffle(name, tmp_path, lut, roots):
    from gmid_engine.search import layer0_start
    doc, spec, extra = _case(name)
    m = random_renaming(doc, 5)
    doc2 = shuffle_order(rename(doc, m), 9)
    if spec == "SYM":
        spec1, spec2 = _sym_spec(doc), _sym_spec(doc2, m)
    else:
        spec1, spec2 = spec, (None if spec is None else ren_spec(spec, m))
    ra, rb = roots(), roots()
    a = build(tmp_path / "a", doc, spec1, lut, ra, extra)
    b = build(tmp_path / "b", doc2, spec2, lut, rb, extra, m)
    sa = signature(a, layer0_start(a), ra)
    sb = signature(b, layer0_start(b), rb)
    assert sa["evals"]                                                   # 공허한 비교 아님(평가가 있었다)
    assert sb == sa
    assert name != "hand_sym" or sa["ties"] > 0                          # 대칭 손 회로는 묶음 경로를 실제로 지난다(구성)
