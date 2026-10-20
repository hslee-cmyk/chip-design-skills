"""정준 순서·궤도 묶음 test 공용 입력(search CONTRACT r11·r12 3.21 3a·3.23~3.25, sizing 3.0b) -- 입력 생성과 대응 계산만, 기대값 아님.

- 손 회로 SYM: 완전 대칭 차동단(포트 inp·inn 입력, o1·o2 출력 둘 다 포트) + 출력마다 engine 커패시터 CL1·CL2.
  구성으로 정한 자기동형 σ = (M1 M2)(M3 M4)(CL1 CL2)(inp inn)(o1 o2) -- 나머지(M5·t·vb·pb·레일)는 고정점. (oracle (a))
- ASYM: sizing conftest 회로 C(단일 종단 CS + pmos 부하) -- 자기동형 궤도 모두 단일.
- 정점 대응 τ: 두 컨텍스트의 같은 `dc_colour`(정점마다 유일, 이름 없음) 끼리 짝(3.0b 성질 (7)).
search `.py` 소스는 열람하지 않았다.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace

from .conftest import CODE_FP, SRC, SUPPLIES, mos, new_access, topo, two, write_decls

US = {"kind": "user_spec", "record": "canon test fixture", "decided": "2026-10-08"}
C_BOX = (1e-13, 1e-11)

# 구성 자기동형 σ(SYM) -- 원소·넷 이름 쌍
SYM_SIGMA = {"M1": "M2", "M2": "M1", "M3": "M4", "M4": "M3", "CL1": "CL2", "CL2": "CL1",
             "inp": "inn", "inn": "inp", "o1": "o2", "o2": "o1"}


def sym_doc(name="hand_sym_canon", caps=True):
    """완전 대칭 차동단. bias = authoring 9절 gate 전용 넷 선언(pb: M3·M4 gate, vb: M5 gate)."""
    pas = [two("CL1", "capacitor", "o1", "gnd"), two("CL2", "capacitor", "o2", "gnd")] if caps else []
    return topo(name,
                [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"),
                 mos("M5", "nmos", "t", "vb", "gnd"), mos("M3", "pmos", "o1", "pb", "vdd"),
                 mos("M4", "pmos", "o2", "pb", "vdd")],
                {"inp": ("input", "differential_input"), "inn": ("input", "differential_input"),
                 "o1": ("output", "differential_output"), "o2": ("output", "differential_output")},
                passives=pas, bias=["pb", "vb"])


SYM_ELEMENTS = (("CL1", "capacitor", None), ("CL2", "capacitor", None))


def asym_doc():
    """회로 C(sizing conftest): M1 nmos (out, in, gnd) + M2 pmos (out, pb, vdd), pb 는 gate 전용(선언)."""
    return topo("hand_cs_canon", [mos("M1", "nmos", "out", "in", "gnd"), mos("M2", "pmos", "out", "pb", "vdd")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}, bias=["pb"])


def rename_doc(doc, mapping, new_name):
    """topology dict 의 원소·넷 이름을 mapping 으로(없는 이름은 그대로). bias_inputs 도 옮긴다."""
    d = json.loads(json.dumps(doc))
    f = lambda n: mapping.get(n, n)                                        # noqa: E731
    for e in d["netlist"]:
        e["name"] = f(e["name"])
        for k in ("drain", "gate", "source", "bulk"):
            if k in e:
                e[k] = f(e[k])
    for key in ("passive_elements", "ideal_sources"):
        for e in d.get(key) or []:
            e["name"] = f(e["name"])
            e["terminals"] = [f(t) for t in e["terminals"]]
    d["supply_nets"] = [f(n) for n in d["supply_nets"]]
    d["ports"] = {f(k): v for k, v in d["ports"].items()}
    if "bias_inputs" in d:
        d["bias_inputs"] = [f(n) for n in d["bias_inputs"]]
    d["topology_name"] = new_name
    return d


def make_case(tmp, topo_doc, lut, elements=(), boxes=None, untie=None, cbounds=None, supplies=None, eval_budget=40,
              archive_root=None, build_sctx=True):
    """spec JSON(metrics conftest `spec_json`) + search.theta_bounds(boxes {원소: (min, max)}) + search.untie_orbits(원소 목록)
    -> authoring 로더 -> KernelContext -> SearchContext. 반환 SimpleNamespace(td, spec, dc, pdk, rule, settings, sctx, spec_bounds, untie)."""
    from gmid_engine.authoring import THETA_BOUNDS, UNTIE_ORBITS, load_sizing_spec, load_topology
    from gmid_engine.graph import build_s1
    from gmid_engine.metrics import metric_catalog
    from gmid_engine.search import SearchSettings, build_search_context
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec
    from metrics.conftest import spec_json

    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    tp = tmp / (topo_doc["topology_name"] + ".topology.json")
    tp.write_text(json.dumps(topo_doc, indent=1), encoding="utf-8")
    td = load_topology(str(tp))
    doc = spec_json(td, dict(SUPPLIES if supplies is None else supplies), list(elements), (), ())
    if boxes is not None:
        doc["human"]["search"]["theta_bounds"] = {n: {"min": lo, "max": hi, "source": dict(US)}
                                                  for n, (lo, hi) in boxes.items()}
    if untie is not None:
        doc["human"]["search"]["untie_orbits"] = {n: {"source": dict(US)} for n in untie}
    sp = tmp / (topo_doc["topology_name"] + ".sizing_spec.json")
    sp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    spec = load_sizing_spec(str(sp), td, metric_catalog())
    inputs = dc_inputs_from_spec(spec)
    from gmid_engine.search import open_run
    donors, counters = open_run()          # [XRUN-F1 card B C0·C6] 이 case 하나 = 실행 하나
    dc = build_kernel_context(build_s1(td, dict(inputs.supplies_v), donors=donors, counters=counters), inputs, new_access(lut),
                              donors=donors, counters=counters)
    pdk, rule = write_decls(tmp / "pdk")
    settings = SearchSettings(600.0, eval_budget, None, SRC, cbounds)
    sctx = build_search_context(dc, spec, settings, archive_root, pdk, rule, code_fp=CODE_FP) if build_sctx else None
    tb = [s.value for s in spec.search if s.field == THETA_BOUNDS]
    ut = [s.value for s in spec.search if s.field == UNTIE_ORBITS]
    return SimpleNamespace(td=td, spec=spec, dc=dc, pdk=pdk, rule=rule, settings=settings, sctx=sctx,
                           spec_bounds=tb[0] if tb else (), untie=tuple(e for e, _ in ut[0]) if ut else ())


def colour_maps(dc):
    """({원소: dc_colour}, {넷: dc_colour}) -- 입력 열 읽기."""
    b = dc.base
    return dict(b.column("device", "dc_colour")), dict(b.column("node", "dc_colour"))


def tau(dc):
    """θ 키 (종류, 이름) -> (종류, 정점 대응 키). 원소 = ("d", dc_colour), 넷 = ("n", dc_colour), 그 밖(입력 묶음 y 키) = 이름 그대로."""
    dv, nv = colour_maps(dc)

    def f(key):
        kind, name = key
        if name in dv:
            return kind, ("d", dv[name])
        if name in nv:
            return kind, ("n", nv[name])
        return kind, name
    return f


def tie_groups(ties):
    """ties -> {frozenset(대표 ∪ 구성원)}."""
    return {frozenset((rep,) + tuple(members)) for rep, members in ties}


def expected_sym_groups(components, sigma=SYM_SIGMA):
    """구성 자기동형 σ 로 짝지어지는 같은 종류 성분 쌍(둘 다 스키마에 있을 때) -- oracle (a)."""
    comps = set(components)
    out = set()
    for kind, name in comps:
        other = sigma.get(name)
        if other is not None and other != name and (kind, other) in comps:
            out.add(frozenset({(kind, name), (kind, other)}))
    return out


def mid_theta(domain):
    """정의역 변수 상자 중점(ln 변수는 ln 중점의 exp) + L = 대표 MOS 첫 칸 lo. 반환 (θ dict, cells)."""
    th = {}
    for v in domain.variables:
        x = 0.5 * (v.lo + v.hi)
        th[v.component] = math.exp(x) if v.log else x
    for m, cells in domain.l_cells:
        th[("L", m)] = cells[0][0]
    return th, tuple(0 for _ in domain.l_cells)


LIBRARY = Path(__file__).resolve().parents[3] / "assets" / "library"


def library_doc(name):
    """library topology·spec JSON(dict) -- 원본 그대로 읽기."""
    raw = json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))
    spec = json.loads((LIBRARY / (name + ".sizing_spec.json")).read_text(encoding="utf-8"))
    return raw, spec


def flip_terminals(doc, element):
    """2단자 원소 하나의 terminals 순서를 뒤집은 사본(연결은 같다 -- 끝 방향만)."""
    d = json.loads(json.dumps(doc))
    for key in ("passive_elements", "ideal_sources"):
        for e in d.get(key) or []:
            if e["name"] == element:
                e["terminals"] = list(reversed(e["terminals"]))
    return d


def build_library_case(tmp, topo_doc, spec_doc, lut, eval_budget=40):
    """library topology·spec(dict) -> SearchContext. meta.topology_fp 는 (바뀐) topology 지문으로 맞춘다(입력 준비).
    metric 이름표 = sizing conftest `spec_catalog`(레지스트리 + 보충). θ 수동소자 상자는 spec theta_bounds 그대로(재정의 없음)."""
    import copy

    from gmid_engine.authoring import load_sizing_spec, load_topology
    from gmid_engine.graph import build_s1
    from gmid_engine.search import SearchSettings, build_search_context
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec
    from sizing.conftest import spec_catalog

    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    tp = tmp / (topo_doc["topology_name"] + ".topology.json")
    tp.write_text(json.dumps(topo_doc), encoding="utf-8")
    td = load_topology(str(tp))
    spec_doc = copy.deepcopy(spec_doc)
    spec_doc["meta"]["topology_fp"] = td.connectivity_fp
    sp = tmp / (topo_doc["topology_name"] + ".sizing_spec.json")
    sp.write_text(json.dumps(spec_doc), encoding="utf-8")
    spec = load_sizing_spec(str(sp), td, spec_catalog())
    inputs = dc_inputs_from_spec(spec)
    from gmid_engine.search import open_run
    donors, counters = open_run()          # [XRUN-F1 card B C0·C6] 이 case 하나 = 실행 하나
    dc = build_kernel_context(build_s1(td, dict(inputs.supplies_v), donors=donors, counters=counters), inputs, new_access(lut),
                              donors=donors, counters=counters)
    pdk, rule = write_decls(tmp / "pdk")
    return build_search_context(dc, spec, SearchSettings(600.0, eval_budget, None, SRC, None), None, pdk, rule,
                                code_fp=CODE_FP)
