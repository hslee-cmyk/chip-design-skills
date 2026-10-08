"""`build_kernel_context(s1graph, inputs, lut)` -- CONTRACT 1.3·1.4: 인자 검사·실패 조건·KernelContext 구성.

- 형식 위반 TypeError, supplies 거부 SchemaRejectedError 그대로, S1 과 다른 supplies ValueError, w_keys 누락·슬라이스 없음
  ValueError, node_targets 넷이 S1 노드 아님 ValueError, 계획 블록 정지는 그대로 전파.
- fixed_values = W3 ∪ 입력 포트(input_dc_v), W3 우선, 이름순. resistor_values = 가지치기 안 된 저항 중 값 있는 것.
  plan_versions = 계획 블록 5개 (writer, block_version) 순서.
- LutAccess: require_immutable 통과, fp_of 는 memo 상태와 무관.
"""
import pytest

from gmid_engine.core import (InfeasibleTargetError, SchemaRejectedError, StructureUnresolvedError, fp_of,
                              require_immutable)
from gmid_engine.graph import build_s1
from gmid_engine.lut import LutMemo, op_point
from gmid_engine.sizing import (DC_KEY, S2_WRITERS, DcInputs, KernelContext, LutAccess, ThetaSchema,
                                build_kernel_context)

from .conftest import (NINE, SUPPLIES, W_KEYS, build_ctx, circuit_cs_pmos_load, detail, library_ctx, load_doc,
                       mos, new_access, topo, two)

PLAN = ("dc_rails", "dc_struct_colour", "dc_current_basis", "dc_writer_plan", "dc_scc_order", "dc_theta_schema")


@pytest.fixture
def parts(tmp_path, toy_access):
    td = load_doc(tmp_path, circuit_cs_pmos_load())
    s1 = build_s1(td, dict(SUPPLIES))
    return s1, DcInputs(tuple(sorted(SUPPLIES.items()))), toy_access


def test_returns_context(parts):
    s1, inputs, acc = parts
    ctx = build_kernel_context(s1, inputs, acc)
    assert isinstance(ctx, KernelContext)
    assert ctx.inputs is inputs and ctx.lut is acc
    assert ctx.base.writers == S2_WRITERS
    assert isinstance(ctx.schema, ThetaSchema)
    assert ctx.base.value("graph", DC_KEY, "dc_theta_schema") == ctx.schema
    assert tuple(w for w, _ in ctx.plan_versions) == PLAN
    for w, v in ctx.plan_versions:
        assert v == ctx.base.block_version(w) and v is not None
    assert ctx.fixed_values == () and ctx.resistor_values == ()


def test_type_errors(parts):
    s1, inputs, acc = parts
    with pytest.raises(TypeError):
        build_kernel_context(s1.snapshot, inputs, acc)
    with pytest.raises(TypeError):
        build_kernel_context(s1, dict(SUPPLIES), acc)
    with pytest.raises(TypeError):
        build_kernel_context(s1, inputs, acc.memo)


def test_supplies_rejected_schema(parts):
    s1, _, acc = parts
    with pytest.raises(SchemaRejectedError):
        build_kernel_context(s1, DcInputs((("vdd", 1.8),)), acc)              # gnd 레일 전위 없음
    with pytest.raises(SchemaRejectedError):
        build_kernel_context(s1, DcInputs((("gnd", 0.0), ("vdd", 1.8), ("zz", 1.0))), acc)


def test_supplies_differ_from_s1(parts):
    s1, _, acc = parts
    with pytest.raises(ValueError):
        build_kernel_context(s1, DcInputs((("gnd", 0.0), ("vdd", 1.5))), acc)


def test_w_keys_missing_kind(parts, toy_lut):
    s1, inputs, _ = parts
    acc = LutAccess(LutMemo(toy_lut, point=16, curve=16, root=16), (("nmos", 100),))
    with pytest.raises(ValueError):
        build_kernel_context(s1, inputs, acc)


def test_w_key_not_in_slice_map(parts, toy_lut):
    s1, inputs, _ = parts
    acc = LutAccess(LutMemo(toy_lut, point=16, curve=16, root=16), (("nmos", 100), ("pmos", 200)))
    with pytest.raises(ValueError):
        build_kernel_context(s1, inputs, acc)


def test_node_target_not_s1_node(parts):
    s1, _, acc = parts
    with pytest.raises(ValueError):
        build_kernel_context(s1, DcInputs(tuple(sorted(SUPPLIES.items())), node_targets=(("nowhere", 0.5),)), acc)


def test_fixed_values_w3_and_input_dc(tmp_path, toy_access):
    doc = topo("hand_two_in",
               [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "out", "inn", "t"),
                mos("M3", "pmos", "o1", "o1", "vdd"), mos("M4", "pmos", "out", "o1", "vdd"),
                mos("M5", "nmos", "t", "vb", "gnd")],
               {"inp": ("input", "a"), "inn": ("input", "b"), "out": ("output", "c")},
               bias=["vb"])                                                                  # vb: M5 gate 에만(o1 은 M3 drain)
    # input_dc 만
    _, _, ctx = build_ctx(tmp_path, doc, toy_access, input_dc_v=0.9)
    assert ctx.fixed_values == (("inn", 0.9), ("inp", 0.9))
    # W3 가 입력 포트 값보다 우선, 이름순
    _, _, ctx = build_ctx(tmp_path, doc, toy_access, input_dc_v=0.9, node_targets=(("t", 0.3), ("inp", 1.0)))
    assert ctx.fixed_values == (("inn", 0.9), ("inp", 1.0), ("t", 0.3))
    # input_dc 없음 + W3 만
    _, _, ctx = build_ctx(tmp_path, doc, toy_access, node_targets=(("t", 0.3),))
    assert ctx.fixed_values == (("t", 0.3),)


def test_resistor_values_exclude_pruned_and_undeclared(tmp_path, toy_access):
    # R3 = source 저항(sdeg–gnd): G_vgs 에서 R1(out–F)·M1(in–sdeg)·R3(sdeg–F) 는 숲(저항 비트리 없음)
    doc = topo("hand_rvals", [mos("M1", "nmos", "out", "in", "sdeg")],
               {"in": ("input", "x"), "out": ("output", "y")},
               passives=[two("R1", "resistor", "vdd", "out"), two("R2", "resistor", "out", "leaf"),
                         two("R3", "resistor", "sdeg", "gnd"), two("C1", "capacitor", "out", "gnd")])
    _, _, ctx = build_ctx(tmp_path, doc, toy_access,
                          element_values=(("C1", 1e-12), ("R1", 1e4), ("R2", 5e3), ("R3", None)))
    assert ctx.resistor_values == (("R1", 1e4),)


def test_resistor_cycle_stops_before_search(tmp_path, toy_access):
    doc = topo("hand_rcycle", [mos("M1", "nmos", "out", "in", "gnd")],
               {"in": ("input", "x"), "out": ("output", "y")},
               passives=[two("R1", "resistor", "vdd", "out"), two("R2", "resistor", "vdd", "out")])
    with pytest.raises(StructureUnresolvedError) as ei:
        build_ctx(tmp_path, doc, toy_access)
    d = detail(ei.value)
    assert d["reason"] == "unsupported_rule_branch"
    assert d["rule_branch"] == "dc_resistor_cycle"
    devs = ei.value.record.devices
    assert devs and set(devs) <= {"R1", "R2"}
    assert ei.value.record.margin is None


def test_kcl_conflict_propagates(tmp_path, toy_access):
    doc = topo("hand_kcl_conflict2",
               [mos("M1", "nmos", "out", "in", "gnd"), mos("M2", "pmos", "out", "pb", "vdd")],
               {"in": ("input", "x"), "out": ("output", "y")},
               sources=[two("I1", "current_source", "vdd", "m"), two("I2", "current_source", "m", "gnd")],
               bias=["pb"])                                                                  # pb: M2 gate 에만
    with pytest.raises(InfeasibleTargetError):
        build_ctx(tmp_path, doc, toy_access, element_values=(("I1", 3e-6), ("I2", 1e-6)))


def test_lut_access_fingerprint_independent_of_memo_state(toy_lut):
    a = LutAccess(LutMemo(toy_lut, point=8, curve=8, root=8), W_KEYS)
    b = LutAccess(LutMemo(toy_lut, point=999, curve=7, root=3), W_KEYS)
    assert require_immutable(a) is None
    fa = fp_of(a)
    assert fa == fp_of(b)
    op_point(a.memo, "nmos", 100, 1e-6, 0.5, 0.9, 0.0)                       # memo 내용 변화
    assert fp_of(a) == fa
    c = LutAccess(LutMemo(toy_lut, point=8, curve=8, root=8), (("nmos", 100),))
    assert fp_of(c) != fa                                                    # w_keys 는 지문에 든다


# ---------------------------------------------------------------------------
# 9회로: 계획 단계 정지 없음 + 3절 불변식(JSON 으로 센 값) + 4.2 기저(독립 RREF)
# (writer 선택 tie-break 은 이번 판 밖 -- 개수·불변식만 본다)
# ---------------------------------------------------------------------------

def gvgs_counts(raw, input_dc_declared, targets=()):
    rails = set(raw["supply_nets"])
    ports_in = sorted(k for k, v in raw["ports"].items() if not k.startswith("_") and v["direction"] == "input")
    F = rails | set(targets) | (set(ports_in) if input_dc_declared else set())
    edges = [(e["gate"], e["source"]) for e in raw["netlist"]]
    edges += [tuple(e["terminals"]) for e in raw.get("passive_elements", []) if e["kind"] == "resistor"]
    if not input_dc_declared:
        free_in = [p for p in ports_in if p not in F]
        edges += list(zip(free_in, free_in[1:]))
    fp = "\0F"
    rep = lambda n: fp if n in F else n                             # noqa: E731
    E = [(rep(a), rep(b)) for a, b in edges]
    V = {x for ab in E for x in ab}
    parent = {v: v for v in V}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in E:
        parent[find(a)] = find(b)
    comps = {find(v) for v in V}
    cyclomatic = len(E) - len(V) + len(comps)
    f_root = find(fp) if fp in V else None
    f_less = len([c for c in comps if c != f_root])
    nodes = set()
    for e in raw["netlist"]:
        nodes |= {e["drain"], e["gate"], e["source"]} | ({e["bulk"]} if e.get("bulk") else set())
    for key in ("passive_elements", "ideal_sources"):
        for e in raw.get(key, []) or []:
            nodes |= set(e["terminals"])
    nodes |= rails
    outside = len([n for n in nodes if n not in F and n not in V])
    return cyclomatic, f_less + outside, nodes, F


@pytest.mark.parametrize("name", NINE)
def test_library_plan_invariants(name, toy_access):
    from .test_current_basis import check, expected_basis
    raw, td, spec, inputs, s1, ctx = library_ctx(name, toy_access)
    base = ctx.base
    cyc, w4, nodes, F = gvgs_counts(raw, inputs.input_dc_v is not None, [n for n, _ in inputs.node_targets])
    writers = dict(base.column("node", "dc_writer"))
    assert set(writers) == set(base.keys("node")) == nodes
    for n, w in writers.items():
        assert (w.tier == "W0") == base.value("node", n, "is_rail")
    assert sorted(w.order for w in writers.values()) == list(range(len(writers)))
    coords = dict(base.column("device", "dc_coord"))
    n_mos = sum(1 for e in raw["netlist"])
    assert len(coords) == n_mos
    dep = sum(1 for c in coords.values() if c.role == "dependent")
    assert n_mos == dep + sum(1 for c in coords.values() if c.role == "writer")
    assert dep == cyc, "종속 수 %d ≠ G_vgs 순환수 %d" % (dep, cyc)
    assert sum(1 for w in writers.values() if w.tier == "W4") == w4
    check(base.value("graph", DC_KEY, "dc_current_basis"), expected_basis(raw, inputs.element_values, base))


@pytest.mark.parametrize("name", NINE)
def test_library_plan_netlist_order_invariant(name, tmp_path, toy_access):
    """9절: netlist·수동소자 순서를 섞어도 계획 스냅샷(writer·기저·SCC·θ 스키마) 지문이 같다."""
    import json
    import random
    raw, td, spec, inputs, s1, ctx = library_ctx(name, toy_access)
    for seed in (1, 2, 3):
        d = json.loads(json.dumps(raw))
        random.Random(seed).shuffle(d["netlist"])
        random.Random(seed).shuffle(d["passive_elements"])
        td2 = load_doc(tmp_path, d)
        ctx2 = build_kernel_context(build_s1(td2, dict(inputs.supplies_v)), inputs, toy_access)
        assert ctx2.base.fp == ctx.base.fp
        assert ctx2.schema == ctx.schema


def test_same_inputs_same_base_fp(parts):
    s1, inputs, acc = parts
    a = build_kernel_context(s1, inputs, acc)
    b = build_kernel_context(s1, inputs, new_access(acc.memo.lut))
    assert a.base.fp == b.base.fp
    assert a.plan_versions == b.plan_versions


# ---- [U1] sizing CONTRACT 13절: build_kernel_context(..., l_classes=()) 와 KernelContext.l_ties
# oracle (d) 계약 문장: l_ties = ((멤버, 주인), ...) 이름순, status derived 동치류의 주인 아닌 멤버만, 생략하면 () 이고 θ 스키마 불변,
# 멤버 이름이 S1 원소가 아니면 ValueError. 동치류는 손으로 만든 LClass(입력)다.
def _three_pmos_mirror():
    return topo("hand_mirror3",
                [mos("M1", "nmos", "d", "in", "gnd"), mos("M2", "pmos", "d", "d", "vdd"),
                 mos("M3", "pmos", "out", "d", "vdd"), mos("M4", "pmos", "o2", "d", "vdd"),
                 mos("M5", "nmos", "out", "nb", "gnd"), mos("M6", "nmos", "o2", "nb", "gnd")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}, bias=["nb"])


def test_l_ties_default_empty_and_schema_unchanged(tmp_path, toy_access):
    from gmid_engine.graph import LClass
    s1, inputs, plain = build_ctx(tmp_path, _three_pmos_mirror(), toy_access)
    assert plain.l_ties == ()
    tied = build_kernel_context(s1, inputs, toy_access,
                                l_classes=(LClass(("M2", "M3", "M4"), "M2", "hand", "derived"),))
    assert tied.l_ties == (("M3", "M2"), ("M4", "M2"))
    assert tied.schema == plain.schema


def test_l_ties_only_derived_classes(tmp_path, toy_access):
    from gmid_engine.graph import LClass
    s1, inputs, _ = build_ctx(tmp_path, _three_pmos_mirror(), toy_access)
    ctx = build_kernel_context(s1, inputs, toy_access,
                               l_classes=(LClass(("M2", "M3", "M4"), "M2", "hand", "review_needed"),
                                          LClass(("M5", "M6"), "M6", "hand", "derived")))
    assert ctx.l_ties == (("M5", "M6"),)


def test_l_ties_unknown_member_rejected(tmp_path, toy_access):
    from gmid_engine.graph import LClass
    s1, inputs, _ = build_ctx(tmp_path, _three_pmos_mirror(), toy_access)
    with pytest.raises(ValueError):
        build_kernel_context(s1, inputs, toy_access, l_classes=(LClass(("M2", "Mzz"), "M2", "hand", "derived"),))
