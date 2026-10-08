"""`dc_struct_colour(snapshot, element_marks, node_marks)` -- CONTRACT 3.0 [r2] + 3.0b [r11]: 구조 색·정준 라벨링·자기동형 궤도.

[r11] 기대값 갱신(종래 '색 = 1-WL 색 그대로' -> 3.0b '색 = (1-WL 색, 정준 위치) 쌍의 순위, 정점마다 유일'):
- 색 계약(`check_colour_contract`): 노드 ∪ 원소 전체 값 = 0..N−1 순열(정점마다 다른 정수), 1-WL 색(conftest `wl_colours`, 3.0 문장의 독립
  구현 -- oracle (b))이 다른 정점 사이 순서 = 1-WL 순서, 1-WL 색이 이미 유일한 회로에서는 값도 1-WL 색과 같다.
- 궤도(`node.dc_orbit`·`device.dc_orbit`): 손 회로의 구성 자기동형(oracle (a))으로 같은/다른 궤도, 궤도 ⊆ 1-WL 색 클래스, 다르게 선언된(원소 값·노드
  목표) 정점은 다른 궤도, 이름 전단사·원소 순서 섞기에 궤도 값이 전단사로 옮겨지고 '색 순서로 정렬한 정점 열의 (class, kind, 이웃 구조)'가 같다
  (3.0b 성질 (1)~(6)).
- 이름 치환 사례는 공개 진입점 `build_kernel_context`(선언 표시를 DcInputs·dc_rails 에서 만든다)로 만든다 -- 선언 표시 인자 형식은 interface card 에 없다.
sizing `.py` 소스는 열람하지 않았다.
"""
import json
import random

import pytest

from gmid_engine.graph import build_s1
from gmid_engine.sizing import DC_KEY, DcInputs, build_kernel_context, dc_struct_colour

from .conftest import (NINE, build_ctx, library_ctx, load_doc, mos, topo, two, wl_colours)


def colours(snap):
    return dict(snap.column("node", "dc_colour")), dict(snap.column("device", "dc_colour"))


def orbits(snap):
    return dict(snap.column("node", "dc_orbit")), dict(snap.column("device", "dc_orbit"))


def rename(doc, seed):
    """넷·원소 이름 전단사 σ(무작위). 반환 (새 doc, σ_net, σ_el)."""
    d = json.loads(json.dumps(doc))
    nets = set(d["supply_nets"]) | {k for k in d["ports"] if not k.startswith("_")}
    for e in d["netlist"]:
        nets |= {e["drain"], e["gate"], e["source"]} | ({e["bulk"]} if e.get("bulk") else set())
    for key in ("passive_elements", "ideal_sources"):
        for e in d.get(key) or []:
            nets |= set(e["terminals"])
    els = [e["name"] for e in d["netlist"]] + [e["name"] for k in ("passive_elements", "ideal_sources")
                                                for e in (d.get(k) or [])]
    rng = random.Random(seed)
    nl = sorted(nets)
    tn = ["n%03d_%d" % (i, seed) for i in range(len(nl))]
    rng.shuffle(tn)
    sn = dict(zip(nl, tn))
    te = ["E%03d_%d" % (i, seed) for i in range(len(els))]
    rng.shuffle(te)
    se = dict(zip(sorted(els), te))
    for e in d["netlist"]:
        e["name"] = se[e["name"]]
        for k in ("drain", "gate", "source", "bulk"):
            if k in e:
                e[k] = sn[e[k]]
    for key in ("passive_elements", "ideal_sources"):
        for e in d.get(key) or []:
            e["name"] = se[e["name"]]
            e["terminals"] = [sn[t] for t in e["terminals"]]
    d["supply_nets"] = [sn[n] for n in d["supply_nets"]]
    d["ports"] = {(k if k.startswith("_") else sn[k]): v for k, v in d["ports"].items()}
    for k in list(d):
        if k in ("device_roles", "symmetry", "sizing_roles", "compensation") or (k.startswith("_") and k != "_comment"):
            d.pop(k)
    if "bias_inputs" in d:                                   # authoring 9절 선언도 같은 σ 로 옮긴다(이름 전단사의 일부)
        d["bias_inputs"] = [sn[n] for n in d["bias_inputs"]]
    d["topology_name"] = d["topology_name"] + "_r%d" % seed
    return d, sn, se


def rename_inputs(inputs, sn, se):
    """DcInputs 의 이름 자리(레일·노드 목표·원소 값·선형 소자·engine 원소)를 σ 로 옮긴다(입력 구성, 기대값 아님)."""
    return DcInputs(tuple(sorted((sn[k], v) for k, v in inputs.supplies_v)), inputs.input_dc_v,
                    tuple(sorted((sn[k], v) for k, v in inputs.node_targets)),
                    tuple(sorted((se[k], v) for k, v in inputs.element_values)),
                    tuple(sorted(se[k] for k in inputs.linear_devices)), inputs.pending,
                    tuple(sorted(se[k] for k in inputs.engine_elements)))


def _links(snap, e):
    cls = snap.value("device", e, "element_class")
    kind = snap.value("device", e, "kind")
    pins = dict(snap.value("device", e, "pins"))
    if cls == "mos":
        out = [(t, pins[t]) for t in ("d", "g", "s")]
        bf = snap.field("device", e, "bulk")
        if bf is not None and bf.value is not None and bf.value.net is not None:
            out.append(("b", bf.value.net))
        return out
    if cls == "ideal_source" and kind == "current_source":
        return [("t0", pins["t0"]), ("t1", pins["t1"])]
    return [("t", pins["t0"]), ("t", pins["t1"])]


def canonical_structure(snap):
    """색 순서로 정렬한 정점 열의 (class, kind, 이웃 구조) -- 이름 없음(3.0b 성질 (1)). 2단자 라벨은 3.0 그래프 그대로(t 방향 없음)."""
    nc, ec = colours(snap)
    nb = {("n", n): [] for n in nc}
    nb.update({("e", e): [] for e in ec})
    for e in ec:
        for lab, net in _links(snap, e):
            nb[("e", e)].append((lab, nc[net]))
            nb[("n", net)].append((lab, ec[e]))
    rows = []
    for e in ec:
        f = snap.field("device", e, "is_diode")
        rows.append((ec[e], "e", snap.value("device", e, "element_class"), snap.value("device", e, "kind"),
                     bool(f.value) if f is not None else False, tuple(sorted(nb[("e", e)]))))
    for n in nc:
        pd = snap.value("node", n, "port_direction")
        rows.append((nc[n], "n", bool(snap.value("node", n, "is_rail")), pd or "", "", tuple(sorted(nb[("n", n)]))))
    return sorted(rows)


def check_colour_contract(snap):
    nc, ec = colours(snap)
    wn, we = wl_colours(snap)
    assert set(nc) == set(snap.keys("node")) and set(ec) == set(snap.keys("device"))
    allv = list(nc.values()) + list(ec.values())
    assert all(isinstance(v, int) and not isinstance(v, bool) for v in allv)
    assert sorted(allv) == list(range(len(allv)))                          # 정점마다 다른 정수(3.0b 성질 (5))
    pairs = [(wn[k], c) for k, c in nc.items()] + [(we[k], c) for k, c in ec.items()]
    bad = [(p, q) for p in pairs for q in pairs if p[0] < q[0] and not p[1] < q[1]]
    assert bad == []                                                       # 1-WL 색이 다른 정점 사이 순서 = 1-WL 순서
    unique = len(set(list(wn.values()) + list(we.values()))) == len(allv)
    assert (not unique) or (nc, ec) == (wn, we)                            # 1-WL 색이 이미 유일 -> 값도 종래와 같다


def check_orbits_refine_wl(snap):
    on, oe = orbits(snap)
    wn, we = wl_colours(snap)
    for o, w in ((on, wn), (oe, we)):
        groups = {}
        for k, v in o.items():
            groups.setdefault(v, set()).add(w[k])
        assert all(len(g) == 1 for g in groups.values())                  # 궤도 ⊆ 1-WL 색 클래스(3.0b 성질 (3))


def test_hand_circuit_colour_contract(ctx_c, ctx_a):
    for ctx in (ctx_c[2], ctx_a[2]):
        check_colour_contract(ctx.base)
        check_orbits_refine_wl(ctx.base)


@pytest.mark.parametrize("name", NINE)
def test_library_colour_contract(name, toy_access):
    base = library_ctx(name, toy_access)[5].base
    check_colour_contract(base)
    check_orbits_refine_wl(base)
    on, oe = orbits(base)
    assert set(on) == set(base.keys("node")) and set(oe) == set(base.keys("device"))
    assert all(isinstance(v, int) for v in list(on.values()) + list(oe.values()))


def sym_doc(name="hand_sym", o2_port=True, caps=False):
    ports = {"inp": ("input", "a"), "inn": ("input", "a"), "o1": ("output", "b"), "o2": ("output", "b")}
    if not o2_port:
        del ports["o2"]
    return topo(name,
                [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"),
                 mos("M5", "nmos", "t", "vb", "gnd"), mos("M3", "pmos", "o1", "pb", "vdd"),
                 mos("M4", "pmos", "o2", "pb", "vdd")],
                ports, passives=[two("CL1", "capacitor", "o1", "gnd"), two("CL2", "capacitor", "o2", "gnd")] if caps else (),
                bias=["pb", "vb"])                                                            # vb: M5 gate, pb: M3·M4 gate


def test_symmetric_pair_same_orbit_and_port_direction_separates(tmp_path, toy_access):
    """(a) 구성 자기동형 (M1 M2)(M3 M4)(inp inn)(o1 o2) -> 같은 궤도, M5 는 고정점. o2 를 포트에서 빼면 대칭이 깨져 궤도가 갈린다."""
    _, _, ctx = build_ctx(tmp_path, sym_doc(), toy_access)
    on, oe = orbits(ctx.base)
    assert oe["M1"] == oe["M2"] and oe["M3"] == oe["M4"] and oe["M1"] != oe["M5"] and oe["M1"] != oe["M3"]
    assert on["inp"] == on["inn"] and on["o1"] == on["o2"] and on["t"] != on["o1"]
    check_colour_contract(ctx.base)
    _, _, ctx2 = build_ctx(tmp_path, sym_doc("hand_sym2", o2_port=False), toy_access)
    on2, oe2 = orbits(ctx2.base)
    assert on2["o1"] != on2["o2"] and oe2["M1"] != oe2["M2"] and oe2["M3"] != oe2["M4"]
    check_colour_contract(ctx2.base)


def test_declared_values_split_orbits(tmp_path, toy_access):
    """3.0b 성질 (4): 같은 값 CL1·CL2 -> 같은 궤도, 다른 값 -> 다른 궤도(대칭 쌍 M1·M2 도 따라 갈린다)."""
    _, _, same = build_ctx(tmp_path, sym_doc("hand_sym_c", caps=True), toy_access,
                           element_values=(("CL1", 1e-12), ("CL2", 1e-12)))
    _, _, diff = build_ctx(tmp_path, sym_doc("hand_sym_c", caps=True), toy_access,
                           element_values=(("CL1", 1e-12), ("CL2", 2e-12)))
    so, do = orbits(same.base)[1], orbits(diff.base)[1]
    assert so["CL1"] == so["CL2"] and so["M1"] == so["M2"]
    assert do["CL1"] != do["CL2"] and do["M1"] != do["M2"]


def test_node_target_splits_orbits(tmp_path, toy_access):
    """3.0b 성질 (4): 노드 목표 표시 -- o1·o2 목표가 같으면 대칭 유지, 다르면 M1·M2 다른 궤도."""
    _, _, eq = build_ctx(tmp_path, sym_doc("hand_sym_t"), toy_access, node_targets=(("o1", 0.9), ("o2", 0.9)))
    _, _, ne = build_ctx(tmp_path, sym_doc("hand_sym_t"), toy_access, node_targets=(("o1", 0.9), ("o2", 1.0)))
    assert orbits(eq.base)[1]["M1"] == orbits(eq.base)[1]["M2"] and orbits(eq.base)[0]["o1"] == orbits(eq.base)[0]["o2"]
    assert orbits(ne.base)[1]["M1"] != orbits(ne.base)[1]["M2"] and orbits(ne.base)[0]["o1"] != orbits(ne.base)[0]["o2"]


NET = [mos("M1", "nmos", "a", "in", "gnd"), mos("M2", "nmos", "b", "in", "gnd"),
       mos("M3", "pmos", "a", "pb", "vdd"), mos("M4", "pmos", "b", "pb", "vdd")]
PORTS = {"in": ("input", "x"), "a": ("output", "y"), "b": ("output", "y")}


def test_current_source_direction_matters(tmp_path, toy_access):
    """이상 전류원은 t0·t1 방향 라벨: a -> b 전류원은 a·b 를 구별(1-WL 색부터 다름). 커패시터(t, DC 엣지 아님)는 방향 없음 -> a·b 같은 궤도."""
    src = topo("hand_src_dir", NET, PORTS, sources=[two("I1", "current_source", "a", "b")], bias=["pb"])
    cap = topo("hand_cap_dir", NET, PORTS, passives=[two("C1", "capacitor", "a", "b")], bias=["pb"])
    _, _, cs = build_ctx(tmp_path, src, toy_access)
    _, _, cc = build_ctx(tmp_path, cap, toy_access)
    check_colour_contract(cs.base)
    check_colour_contract(cc.base)
    assert wl_colours(cs.base)[0]["a"] != wl_colours(cs.base)[0]["b"]
    assert orbits(cs.base)[0]["a"] != orbits(cs.base)[0]["b"]
    assert orbits(cc.base)[0]["a"] == orbits(cc.base)[0]["b"]
    assert orbits(cc.base)[1]["M1"] == orbits(cc.base)[1]["M2"]


def test_b_dc_resistor_is_undirected(tmp_path, toy_access):
    """[사용자 결정 2026-10-08 '대칭 묶음 방식: b' -- 2단자 수동소자는 방향 없음] DC 전류가 흐르는 저항 R1 (a, b) 도 a·b 를 구별하지 않는다:
    a↔b, M1↔M2, M3↔M4 맞바꿈은 R1 의 두 끝을 맞바꿀 뿐인 자기동형 -> a·b 같은 궤도, M1·M2 같은 궤도. (oracle (a) 구성 + (d) 사용자 결정)"""
    res = topo("hand_res_dir", NET, PORTS, passives=[two("R1", "resistor", "a", "b")], bias=["pb"])
    _, _, cr = build_ctx(tmp_path, res, toy_access)
    on, oe = orbits(cr.base)
    assert on["a"] == on["b"]
    assert oe["M1"] == oe["M2"] and oe["M3"] == oe["M4"]


def test_b_resistor_terminal_order_irrelevant(tmp_path, toy_access):
    """(b): 저항 terminals 순서를 뒤집어 그려도 궤도 분할이 같다(방향 없음)."""
    a = topo("hand_res_ab", NET, PORTS, passives=[two("R1", "resistor", "vdd", "a"), two("R2", "resistor", "vdd", "b")],
             bias=["pb"])
    b = topo("hand_res_ba", NET, PORTS, passives=[two("R1", "resistor", "vdd", "a"), two("R2", "resistor", "b", "vdd")],
             bias=["pb"])
    _, _, ca = build_ctx(tmp_path, a, toy_access)
    _, _, cb = build_ctx(tmp_path, b, toy_access)
    assert orbits(ca.base)[1]["R1"] == orbits(ca.base)[1]["R2"]                 # 같은 방향(대조) -- 현재 코드도 통과
    assert orbits(cb.base)[1]["R1"] == orbits(cb.base)[1]["R2"]                 # 뒤집어 그림 -- (b) 에서만 통과
    assert orbits(cb.base)[1]["M1"] == orbits(cb.base)[1]["M2"]


def _renamed_ctx(tmp_path, name, seed, toy_access):
    raw, td, spec, inputs, s1, ctx = library_ctx(name, toy_access)
    d2, sn, se = rename(raw, seed)
    inputs2 = rename_inputs(inputs, sn, se)
    s1b = build_s1(load_doc(tmp_path, d2), dict(inputs2.supplies_v))
    return ctx, build_kernel_context(s1b, inputs2, toy_access), sn, se


@pytest.mark.parametrize("seed", [1, 2, 3])
@pytest.mark.parametrize("name", ["two_stage_ota", "folded_cascode", "current_reuse_telescopic_ota"])
def test_renaming_transports_orbits_and_structure(name, seed, tmp_path, toy_access):
    """3.0b 성질 (1): 이름 전단사 σ -> dc_orbit 이 σ 로 옮겨진다(값 불변), 색 순서 정점 열의 이름 없는 구조가 같다."""
    ctx, ctx2, sn, se = _renamed_ctx(tmp_path, name, seed, toy_access)
    on, oe = orbits(ctx.base)
    on2, oe2 = orbits(ctx2.base)
    assert {sn[k]: v for k, v in on.items()} == on2
    assert {se[k]: v for k, v in oe.items()} == oe2
    assert canonical_structure(ctx2.base) == canonical_structure(ctx.base)
    check_colour_contract(ctx2.base)


@pytest.mark.parametrize("seed", [1, 2])
def test_renaming_colours_equal_outside_nontrivial_orbits(seed, tmp_path, toy_access):
    """궤도가 단일인 정점의 색은 σ 로 그대로 옮겨진다(같은 정준 그래프의 같은 위치) -- 9회로 중 궤도가 단일뿐인 two_stage_ota."""
    ctx, ctx2, sn, se = _renamed_ctx(tmp_path, "two_stage_ota", seed, toy_access)
    nc, ec = colours(ctx.base)
    nc2, ec2 = colours(ctx2.base)
    on, oe = orbits(ctx.base)
    assert len(set(oe.values())) == len(oe) and len(set(on.values())) == len(on)   # 전제: 궤도 모두 단일
    assert {sn[k]: v for k, v in nc.items()} == nc2
    assert {se[k]: v for k, v in ec.items()} == ec2


@pytest.mark.parametrize("name", ["two_stage_ota", "sf_pushpull_output_opamp", "current_reuse_telescopic_ota"])
def test_reordering_identical(name, tmp_path, toy_access):
    raw, td, spec, inputs, s1, ctx = library_ctx(name, toy_access)
    d = json.loads(json.dumps(raw))
    random.Random(7).shuffle(d["netlist"])
    d["passive_elements"] = list(reversed(d["passive_elements"]))
    ctx2 = build_kernel_context(build_s1(load_doc(tmp_path, d), dict(inputs.supplies_v)), inputs, toy_access)
    assert orbits(ctx2.base) == orbits(ctx.base)
    assert colours(ctx2.base) == colours(ctx.base)
    assert canonical_structure(ctx2.base) == canonical_structure(ctx.base)


def test_deterministic(tmp_path, toy_access):
    """3.0b 성질 (6)(8): 같은 입력 -> 같은 색·궤도."""
    a = build_ctx(tmp_path, sym_doc("hand_sym_det", caps=True), toy_access)[2]
    b = build_ctx(tmp_path, sym_doc("hand_sym_det", caps=True), toy_access)[2]
    assert colours(a.base) == colours(b.base) and orbits(a.base) == orbits(b.base)
    assert list(a.base.column("device", "dc_colour")) == list(b.base.column("device", "dc_colour"))


def test_block_writer_and_version(ctx_c):
    """다섯 필드(dc_colour·dc_orbit 노드/원소 + graph.dc_symmetry) 모두 dc_struct_colour 가 쓰고, 입력 버전 = 컨텍스트 계획 버전(plan_versions)의 dc_struct_colour 항목."""
    base = ctx_c[2].base
    pv = dict(ctx_c[2].plan_versions)
    for kind in ("node", "device"):
        k = base.keys(kind)[0]
        for f in ("dc_colour", "dc_orbit"):
            fv = base.field(kind, k, f)
            assert fv.writer == "dc_struct_colour"
            assert fv.input_version == pv["dc_struct_colour"]
    sym = base.field("graph", DC_KEY, "dc_symmetry")                      # [U2] 생성자 필드도 같은 블록
    assert sym.writer == "dc_struct_colour" and sym.input_version == pv["dc_struct_colour"]
    assert dc_struct_colour.name == "dc_struct_colour"


def test_block_reuse_with_same_marks(ctx_c):
    """3.0b extras 형식(`((이름, ((표시 이름, float), ...)), ...)` 이름순): 회로 C 는 원소 표시 없음, 노드 표시 = 레일 전위 `rail_v`
    (DcInputs supplies: gnd 0.0, vdd 1.8 -- 입력에서 손으로 만든 표시). 컨텍스트가 같은 표시로 이미 계산했으므로 같은 표시로 다시 부르면 reuse.
    다른 표시(vdd 전위 다름)면 reuse 가 아니다."""
    base = ctx_c[2].base
    node_marks = (("gnd", (("rail_v", 0.0),)), ("vdd", (("rail_v", 1.8),)))
    dc_struct_colour.reset_stats()
    assert dc_struct_colour(base, (), node_marks) is base
    assert dc_struct_colour.stats().reuses == 1
    other = (("gnd", (("rail_v", 0.0),)), ("vdd", (("rail_v", 1.7),)))
    dc_struct_colour.reset_stats()
    assert dc_struct_colour(base, (), other) is not base
    assert dc_struct_colour.stats().reuses == 0
