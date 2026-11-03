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
from gmid_engine.search import open_run
from gmid_engine.sizing import (DC_KEY, KERNEL_KEY, S2_WRITERS, DcInputs, KernelContext, LutAccess, ThetaSchema,
                                build_kernel_context)

from .conftest import (NINE, SUPPLIES, W_KEYS, build_ctx, circuit_cs_pmos_load, detail, library_ctx, load_doc,
                       mos, new_access, topo, two)
from .conftest import inject_l_classes, kfixed, kplan, kres, kschema, kties  # [U17 ①-b] graph/kernel 필드 읽기(설계 40 v1.9.1 §2.4.7 KernelContext 행)

# [U17 ①-d] 40 §6-8 D-2: 구조 색 블록 = graph 대칭 블록 s1_symmetry(S1 이 같은 표시로 계산했으면 재사용)
PLAN = ("dc_rails", "s1_symmetry", "dc_current_basis", "dc_writer_plan", "dc_scc_order", "dc_theta_schema")


def _fresh():
    """[XRUN-F1 card B C0·C6] 새 실행 하나의 두 객체(build_kernel_context 키워드). 부를 때마다 새 open_run() 쌍."""
    donors, counters = open_run()
    return dict(donors=donors, counters=counters)


@pytest.fixture
def parts(tmp_path, toy_access):
    td = load_doc(tmp_path, circuit_cs_pmos_load())
    s1 = build_s1(td, dict(SUPPLIES), **_fresh())
    return s1, DcInputs(tuple(sorted(SUPPLIES.items()))), toy_access


def test_returns_context(parts):
    s1, inputs, acc = parts
    ctx = build_kernel_context(s1, inputs, acc, **_fresh())
    assert isinstance(ctx, KernelContext)
    assert ctx.inputs is inputs and ctx.lut is acc
    assert ctx.base.writers == S2_WRITERS
    assert isinstance(kschema(ctx), ThetaSchema)
    # [U17 ①-b] 설계 40 v1.9.1 §2.4.8 D8: θ 스키마 필드는 graph/kernel `theta_schema`(옛 graph/dc `dc_theta_schema` 를 옮김), writer dc_theta_schema 유지.
    assert ctx.base.field("graph", KERNEL_KEY, "theta_schema").writer == "dc_theta_schema"
    assert ctx.base.record("graph", DC_KEY) is None or "dc_theta_schema" not in {n for n, _ in ctx.base.record("graph", DC_KEY).fields}
    # 옛 plan_versions = 계획 블록 (writer, block_version) -- §2.4.7 'plan_versions 는 쓰기 계획 블록의 block_version 읽기로 대체'
    for w in PLAN:
        assert ctx.base.block_version(w) is not None
    assert kfixed(ctx) == () and kres(ctx) == ()


def test_type_errors(parts):
    s1, inputs, acc = parts
    with pytest.raises(TypeError):
        build_kernel_context(s1.snapshot, inputs, acc, **_fresh())
    with pytest.raises(TypeError):
        build_kernel_context(s1, dict(SUPPLIES), acc, **_fresh())
    with pytest.raises(TypeError):
        build_kernel_context(s1, inputs, acc.memo, **_fresh())


@pytest.mark.parametrize("missing", ["donors", "counters", "both"])
def test_run_pair_keywords_required(parts, missing):
    """B-T16(card B C6): build_kernel_context 의 donors·counters 는 필수 키워드(기본값 없음) -- 빠지면 TypeError."""
    s1, inputs, acc = parts
    kw = {k: v for k, v in _fresh().items() if missing != "both" and k != missing}
    with pytest.raises(TypeError):
        build_kernel_context(s1, inputs, acc, **kw)


def test_run_pair_fields_are_passed_objects(parts):
    """B-T16(card B C6): 결과 KernelContext 칸 donors·counters 는 넘긴 객체 그 자체(is)."""
    s1, inputs, acc = parts
    donors, counters = open_run()
    ctx = build_kernel_context(s1, inputs, acc, donors=donors, counters=counters)
    assert ctx.donors is donors
    assert ctx.counters is counters


def test_supplies_rejected_schema(parts):
    s1, _, acc = parts
    with pytest.raises(SchemaRejectedError):
        build_kernel_context(s1, DcInputs((("vdd", 1.8),)), acc, **_fresh())              # gnd 레일 전위 없음
    with pytest.raises(SchemaRejectedError):
        build_kernel_context(s1, DcInputs((("gnd", 0.0), ("vdd", 1.8), ("zz", 1.0))), acc, **_fresh())


def test_supplies_differ_from_s1(parts):
    s1, _, acc = parts
    with pytest.raises(ValueError):
        build_kernel_context(s1, DcInputs((("gnd", 0.0), ("vdd", 1.5))), acc, **_fresh())


def test_w_keys_missing_kind(parts, toy_lut):
    s1, inputs, _ = parts
    acc = LutAccess(LutMemo(toy_lut, point=16, curve=16, root=16), (("nmos", 100),))
    with pytest.raises(ValueError):
        build_kernel_context(s1, inputs, acc, **_fresh())


def test_w_key_not_in_slice_map(parts, toy_lut):
    s1, inputs, _ = parts
    acc = LutAccess(LutMemo(toy_lut, point=16, curve=16, root=16), (("nmos", 100), ("pmos", 200)))
    with pytest.raises(ValueError):
        build_kernel_context(s1, inputs, acc, **_fresh())


def test_node_target_not_s1_node(parts):
    s1, _, acc = parts
    with pytest.raises(ValueError):
        build_kernel_context(s1, DcInputs(tuple(sorted(SUPPLIES.items())), node_targets=(("nowhere", 0.5),)), acc, **_fresh())


def test_fixed_values_w3_and_input_dc(tmp_path, toy_access):
    doc = topo("hand_two_in",
               [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "out", "inn", "t"),
                mos("M3", "pmos", "o1", "o1", "vdd"), mos("M4", "pmos", "out", "o1", "vdd"),
                mos("M5", "nmos", "t", "vb", "gnd")],
               {"inp": ("input", "differential_input_p"), "inn": ("input", "differential_input_n"), "out": ("output", "c")},   # [IT-1 DEC-106] role 만
               bias=["vb"])                                                                  # vb: M5 gate 에만(o1 은 M3 drain)
    # input_dc 만
    _, _, ctx = build_ctx(tmp_path, doc, toy_access, input_dc_v=0.9)
    assert kfixed(ctx) == (("inn", 0.9), ("inp", 0.9))
    # W3 가 입력 포트 값보다 우선, 이름순
    _, _, ctx = build_ctx(tmp_path, doc, toy_access, input_dc_v=0.9, node_targets=(("t", 0.3), ("inp", 1.0)))
    assert kfixed(ctx) == (("inn", 0.9), ("inp", 1.0), ("t", 0.3))
    # input_dc 없음 + W3 만
    _, _, ctx = build_ctx(tmp_path, doc, toy_access, node_targets=(("t", 0.3),))
    assert kfixed(ctx) == (("t", 0.3),)


def test_resistor_values_exclude_pruned_and_undeclared(tmp_path, toy_access):
    # R3 = source 저항(sdeg–gnd): G_vgs 에서 R1(out–F)·M1(in–sdeg)·R3(sdeg–F) 는 숲(저항 비트리 없음)
    doc = topo("hand_rvals", [mos("M1", "nmos", "out", "in", "sdeg")],
               {"in": ("input", "x"), "out": ("output", "y")},
               passives=[two("R1", "resistor", "vdd", "out"), two("R2", "resistor", "out", "leaf"),
                         two("R3", "resistor", "sdeg", "gnd"), two("C1", "capacitor", "out", "gnd")])
    _, _, ctx = build_ctx(tmp_path, doc, toy_access,
                          element_values=(("C1", 1e-12), ("R1", 1e4), ("R2", 5e3), ("R3", None)))
    assert kres(ctx) == (("R1", 1e4),)


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
    # [IT-1 K-3] 입력 DC 미선언이어도 '같은 DC' 엣지(입력 포트끼리 사슬)는 없다
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
        run = _fresh()                                     # 섞은 netlist = 다른 실행
        ctx2 = build_kernel_context(build_s1(td2, dict(inputs.supplies_v), **run), inputs, toy_access, **run)
        assert ctx2.base.fp == ctx.base.fp
        assert kschema(ctx2) == kschema(ctx)


def test_same_inputs_same_base_fp(parts):
    s1, inputs, acc = parts
    a = build_kernel_context(s1, inputs, acc, **_fresh())
    b = build_kernel_context(s1, inputs, new_access(acc.memo.lut), **_fresh())
    assert a.base.fp == b.base.fp
    assert kplan(a) == kplan(b)


# ====================================================================

# [U4] L 동치류 L 공유 (D-GB7a, 설계 40 §3.7-1·§3.2 보완 1 'θ 스키마는 동치류당 L 변수 하나', 계획 LR1, CONTRACT 14.1)
# ===========================================================================
# oracle (a) 구성: circuit_mirror 의 M1·M2 는 같은 gate 넷(nb)·같은 source 넷(gnd)·같은 kind(nmos) -- LR1 규칙의 L 동치류가 되는
# 쌍이다(동치류 유도는 U1 몫이라 test 가 LClassStub 로 준다). 기대: derived 동치류만 묶이고, θ 의 L 성분은 주인 하나뿐이다.

from gmid_engine.sizing import check_theta, size_and_seal                                      # noqa: E402

from .conftest import LClassStub, build_ctx_u4, circuit_mirror, theta_mirror                    # noqa: E402

_MIR_VALUES = (("I1", 1e-5),)


def _l_components(ctx):
    return sorted(k for t, k in kschema(ctx).components if t == "L")


@pytest.mark.parametrize("members", [("M1", "M2"), ("M2", "M1"), ("M2",)])
def test_l_class_derived_ties_member_to_owner(tmp_path, r4_access, members):
    """derived 동치류 {M1(주인), M2}: l_ties = (("M2", "M1"),)(비주인 멤버만), θ L 성분 = M1·M3(M2 없음). 멤버 목록에 주인이
    있든 없든·순서가 어떻든 같다."""
    _, ctx = build_ctx_u4(tmp_path, circuit_mirror(), r4_access, l_classes=(LClassStub("M1", members),),
                          element_values=_MIR_VALUES)
    assert kties(ctx) == (("M2", "M1"),)
    assert _l_components(ctx) == ["M1", "M3"]


@pytest.mark.parametrize("status", ["review_needed", "proposed"])
def test_l_class_not_derived_is_not_tied(tmp_path, r4_access, status):
    """derived 가 아닌 동치류는 묶지 않는다(설계 40 §3.2 'review_needed 가 남으면 정지' 는 GB4 앞 U1 몫, 여기서는 소자마다 L)."""
    _, ctx = build_ctx_u4(tmp_path, circuit_mirror(), r4_access, l_classes=(LClassStub("M1", ("M1", "M2"), status),),
                          element_values=_MIR_VALUES)
    assert kties(ctx) == ()
    assert _l_components(ctx) == ["M1", "M2", "M3"]


def test_no_l_classes_same_plan_as_before(tmp_path, r4_access):
    """동치류가 없으면 l_ties = () 이고 계획 스냅샷이 인자 없는 호출과 비트 같다(CONTRACT 14.1 'extras 를 3번째까지 주지 않는다')."""
    s1, a = build_ctx_u4(tmp_path / "a", circuit_mirror(), r4_access, element_values=_MIR_VALUES)
    b = build_kernel_context(s1, a.inputs, r4_access, **_fresh())
    assert kties(a) == () == kties(b) and a.base.fp == b.base.fp and kschema(a) == kschema(b)


def test_member_l_component_rejected(tmp_path, r4_access):
    """멤버의 ("L", 멤버) 성분은 θ 에 없다 -> 넣으면 ValueError(check_theta·size_and_seal 모두, 후보 실패가 아님)."""
    _, ctx = build_ctx_u4(tmp_path, circuit_mirror(), r4_access, l_classes=(LClassStub("M1", ("M1", "M2")),),
                          element_values=_MIR_VALUES)
    th = theta_mirror()
    with pytest.raises(ValueError):
        check_theta(kschema(ctx), th)
    with pytest.raises(ValueError):
        size_and_seal(ctx, th)
    del th[("L", "M2")]
    check_theta(kschema(ctx), th)                                     # 멤버 L 을 빼면 통과


@pytest.mark.parametrize("classes", [
    (("M1", ("M1", "I1")),),                       # 이상원 멤버(MOS 아님)
    (("M1", ("M1", "ZZ")),),                       # S1 에 없는 멤버
    (("ZZ", ("M1",)),),                            # S1 에 없는 주인
    (("I1", ("M1",)),),                            # MOS 아닌 주인
    (("M1", ("M1", "M2")), ("M2", ("M2", "M3"))),   # 주인 M2 가 다른 동치류의 멤버
    (("M1", ("M1", "M2")), ("M3", ("M3", "M2"))),   # M2 가 두 동치류의 멤버
], ids=["member_source", "member_unknown", "owner_unknown", "owner_source", "owner_is_member", "two_classes"])
def test_l_class_rejects(tmp_path, r4_access, classes):
    """CONTRACT 14.1 거부 조건 -> ValueError(호출 계약 위반)."""
    with pytest.raises(ValueError):
        build_ctx_u4(tmp_path, circuit_mirror(), r4_access, l_classes=tuple(LClassStub(o, m) for o, m in classes),
                     element_values=_MIR_VALUES)


def test_l_class_order_invariance(tmp_path, r4_access):
    """IC2(설계 40 §10.3): 동치류 목록·멤버 순서를 섞어도 계획 스냅샷·스키마·l_ties 가 같다."""
    a = build_ctx_u4(tmp_path / "a", circuit_mirror(), r4_access,
                     l_classes=(LClassStub("M1", ("M1", "M2")), LClassStub("M3", ("M3",))), element_values=_MIR_VALUES)[1]
    b = build_ctx_u4(tmp_path / "b", circuit_mirror(), r4_access,
                     l_classes=(LClassStub("M3", ("M3",)), LClassStub("M1", ("M2", "M1"))), element_values=_MIR_VALUES)[1]
    # [U17 ①-b] L 동치류는 이제 S0 수준 필드 graph/s1v: l_classes 입력이다(설계 40 v1.9.1 §2.4.8 D1). 이 test 가 순서를 섞어 넣은 그 입력 필드 자체가
    # 스냅샷 지문에 들어가므로 base.fp 비교는 입력 차이를 잰다(정준 순서는 build_s1v 몫). 커널 구조 파생 결과(θ 스키마·l_ties)가 같은지만 본다.
    assert kschema(a) == kschema(b) and kties(a) == kties(b) == (("M2", "M1"),)


def test_l_ties_name_bijection(tmp_path, r4_access):
    """이름 전단사(소자 M1->Q9, M2->Q1, M3->Q5, I1->J2; 넷 nb->n7, out->o2, in->i4): l_ties·L 성분이 사상을 따라간다 -- 동치류
    주인은 이름이 아니라 주어진 owner 로 정해진다(이름순 첫 멤버 Q1 이 아니라 Q9)."""
    names = ("Q9", "Q1", "Q5", "J2")
    _, ctx = build_ctx_u4(tmp_path, circuit_mirror(names, ("n7", "o2", "i4")), r4_access,
                          l_classes=(LClassStub("Q9", ("Q1", "Q9")),), element_values=(("J2", 1e-5),))
    assert kties(ctx) == (("Q1", "Q9"),)
    assert _l_components(ctx) == ["Q5", "Q9"]

# ---- [U1] sizing CONTRACT 13절: build_kernel_context(..., l_classes=()) 와 KernelContext.l_ties
# oracle (d) 계약 문장: l_ties = ((멤버, 주인), ...) 이름순, status derived 동치류의 주인 아닌 멤버만, 생략하면 () 이고 θ 스키마 불변,
# 멤버 이름이 S1 원소가 아니면 ValueError. 동치류는 손으로 만든 LClass(입력)다.
def _three_pmos_mirror():
    return topo("hand_mirror3",
                [mos("M1", "nmos", "d", "in", "gnd"), mos("M2", "pmos", "d", "d", "vdd"),
                 mos("M3", "pmos", "out", "d", "vdd"), mos("M4", "pmos", "o2", "d", "vdd"),
                 mos("M5", "nmos", "out", "nb", "gnd"), mos("M6", "nmos", "o2", "nb", "gnd")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}, bias=["nb"])


def test_l_ties_default_empty_and_schema_drops_member_l(tmp_path, toy_access):
    """oracle (d) 설계 결론 D-GB7a(40 §3.7·§11 U4): θ 는 L 동치류마다 L 성분 하나(주인), 멤버 ("L", 멤버) 성분은 없다.
    기대 = plain 성분 - {("L","M3"),("L","M4")}(LClass 선언에서 손으로 정한 멤버, 피검 함수 출력 아님), 나머지 성분·순서는 그대로.
    (U1 시절 'schema 불변' 단언은 D-GB7a 와 모순 -- 오케스트레이터 결정으로 교체.)"""
    from gmid_engine.graph import LClass
    s1, inputs, plain = build_ctx(tmp_path, _three_pmos_mirror(), toy_access)
    assert kties(plain) == ()
    tied = build_kernel_context(inject_l_classes(s1, (LClass(("M2", "M3", "M4"), "M2", "hand", "derived"),)), inputs, toy_access,
                                **_fresh())
    assert kties(tied) == (("M3", "M2"), ("M4", "M2"))
    removed = {("L", "M3"), ("L", "M4")}
    assert removed <= set(kschema(plain).components)
    assert kschema(tied).components == tuple(c for c in kschema(plain).components if c not in removed)
    assert ("L", "M2") in kschema(tied).components
    assert (kschema(tied).current_cone, kschema(tied).fixed, kschema(tied).zero_cancel) == (
        kschema(plain).current_cone, kschema(plain).fixed, kschema(plain).zero_cancel)


def test_l_ties_only_derived_classes(tmp_path, toy_access):
    from gmid_engine.graph import LClass
    s1, inputs, _ = build_ctx(tmp_path, _three_pmos_mirror(), toy_access)
    ctx = build_kernel_context(inject_l_classes(s1, (LClass(("M2", "M3", "M4"), "M2", "hand", "review_needed"),
                                                     LClass(("M5", "M6"), "M6", "hand", "derived"))), inputs, toy_access,
                               **_fresh())
    assert kties(ctx) == (("M5", "M6"),)


def test_l_ties_unknown_member_rejected(tmp_path, toy_access):
    from gmid_engine.graph import LClass
    s1, inputs, _ = build_ctx(tmp_path, _three_pmos_mirror(), toy_access)
    with pytest.raises(ValueError):
        build_kernel_context(inject_l_classes(s1, (LClass(("M2", "Mzz"), "M2", "hand", "derived"),)), inputs, toy_access,
                             **_fresh())
