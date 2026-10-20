"""`dc_writer_plan(snapshot, target_nets, input_dc_declared)` -- CONTRACT 3절 [r2].

- 손 회로: 구조상 선택이 하나뿐인 경우 NodeWrite·DeviceCoord 를 손으로 적고 비교. [r11] 대칭 회로의 선택은 구조 색 dc_colour(3.0b, 정점마다
  유일 -- 1-WL 색 + 정준 위치)가 정하고 TieBreak 는 생기지 않는다: 기대값은 스냅샷 입력 열 dc_colour 로 3절 규칙을 손으로 적용한다.
- 9회로: 불변식(종속 수 = G_vgs 순환수, W4 수)은 test_kernel_context. 여기서는 metamorphic:
  (1) 순서 섞기 -> 계획 비트 동일, (2) 이름 전단사 σ -> (writer 집합, θ 스키마 키 집합) = σ(원래 것), 차이는 모두 원래 계획의
  dc_tie_breaks·CurrentBasis.ties 후보 안(9절).
"""
import json
import random

import pytest

from gmid_engine.core import StructureUnresolvedError
from gmid_engine.graph import build_s1
from gmid_engine.sizing import (DC_KEY, INPUT_GROUP_KEY, DeviceCoord, NodeWrite, TieBreak, build_kernel_context,
                                dc_writer_plan)

from .conftest import (NINE, build_ctx, circuit_cs_pmos_load, circuit_cs_res, circuit_empty_window, detail,
                       library_ctx, load_doc, mos, topo, two)
from .conftest import kschema  # [U17 ①-b] graph/kernel 필드 읽기(설계 40 v1.9.1 §2.4.7 KernelContext 행)
from .conftest import rename
from .conftest import block_row, row_delta, run_of  # [XRUN-F1 card B C1·C4]
from gmid_engine.search import open_run


def plan(ctx):
    b = ctx.base
    nw = dict(b.column("node", "dc_writer"))
    co = dict(b.column("device", "dc_coord"))
    ties = b.value("graph", DC_KEY, "dc_tie_breaks")
    return nw, co, ties


def strip(nw):
    """order 를 뺀 (tier, relation, element, known, y_key)."""
    return {n: (w.tier, w.relation, w.element, w.known, w.y_key) for n, w in nw.items()}


def test_circuit_c(ctx_c):
    nw, co, ties = plan(ctx_c[2])
    assert strip(nw) == {
        "gnd": ("W0", "rail", None, None, None), "vdd": ("W0", "rail", None, None, None),
        "in": ("W2", "vgs_gate", "M1", "gnd", None), "pb": ("W2", "vgs_gate", "M2", "vdd", None),
        "out": ("W4", "free_window", None, None, "out")}
    assert co == {"M1": DeviceCoord("writer", "tree"), "M2": DeviceCoord("writer", "tree")}
    assert ties == ()
    # order: 레일(1단계) 먼저, G_vgs 밖 노드(6단계) 마지막
    assert {nw["gnd"].order, nw["vdd"].order} == {0, 1} and nw["out"].order == 4
    assert all(isinstance(w, NodeWrite) for w in nw.values())


def test_resistor_drop_writer(ctx_a):
    nw, co, ties = plan(ctx_a[2])
    assert strip(nw)["out"] == ("W2", "resistor_drop", "R1", "vdd", None)
    assert strip(nw)["in"] == ("W2", "vgs_gate", "M1", "gnd", None)
    assert co == {"M1": DeviceCoord("writer", "tree")}


def test_diode_tree_mirror_parallel(tmp_path, toy_access):
    """diode MOS 가 그 밖 MOS 보다 순위가 앞 -> M1(diode) 트리(W1), M2 는 같은 (gate, source) -> parallel_vgs(partner M1)."""
    doc = topo("wp_mirror",
               [mos("M1", "nmos", "nb", "nb", "gnd"), mos("M2", "nmos", "out", "nb", "gnd"),
                mos("M3", "pmos", "out", "in", "vdd")],
               {"in": ("input", "x"), "out": ("output", "y")}, sources=[two("I1", "current_source", "vdd", "nb")])
    nw, co, ties = plan(build_ctx(tmp_path, doc, toy_access)[2])
    assert strip(nw)["nb"] == ("W1", "vgs_gate", "M1", "gnd", None)
    assert co["M1"] == DeviceCoord("writer", "tree")
    assert co["M2"] == DeviceCoord("dependent", "parallel_vgs", "M1")
    assert strip(nw)["in"] == ("W2", "vgs_gate", "M3", "vdd", None)
    assert strip(nw)["out"] == ("W4", "free_window", None, None, "out")
    assert ties == ()


def test_fixed_vgs(tmp_path, toy_access):
    nw, co, _ = plan(build_ctx(tmp_path, circuit_empty_window(), toy_access)[2])
    assert co["MA"] == DeviceCoord("dependent", "fixed_vgs") and co["MB"] == DeviceCoord("dependent", "fixed_vgs")
    assert co["MC"] == DeviceCoord("writer", "tree")
    assert strip(nw)["x"] == ("W4", "free_window", None, None, "x")


def test_cycle_vgs_behind_resistor(tmp_path, toy_access):
    """R2(g3, vdd)(잎 가지치기 저항도 G_vgs 엣지) 가 순위 앞 -> 트리, M2 (g3, vdd) 는 비트리 cycle_vgs."""
    doc = topo("wp_cycle", [mos("M1", "nmos", "out", "in", "gnd"), mos("M2", "pmos", "out", "g3", "vdd")],
               {"in": ("input", "x"), "out": ("output", "y")}, passives=[two("R2", "resistor", "g3", "vdd")])
    nw, co, _ = plan(build_ctx(tmp_path, doc, toy_access)[2])
    assert co["M2"] == DeviceCoord("dependent", "cycle_vgs")
    assert strip(nw)["g3"] == ("W2", "resistor_drop", "R2", "vdd", None)


def test_input_dc_declared_makes_fixed(tmp_path, toy_access):
    nw, co, _ = plan(build_ctx(tmp_path, circuit_cs_pmos_load(), toy_access, input_dc_v=0.7)[2])
    assert strip(nw)["in"] == ("W2", "input_dc", None, None, None)
    assert co["M1"] == DeviceCoord("dependent", "fixed_vgs")          # gate·source 둘 다 F


def test_target_priority_over_input_dc(tmp_path, toy_access):
    nw, _, _ = plan(build_ctx(tmp_path, circuit_cs_pmos_load(), toy_access, input_dc_v=0.7,
                              node_targets=(("in", 0.65), ("out", 0.9)))[2])
    assert strip(nw)["in"] == ("W3", "declared_target", None, None, None)
    assert strip(nw)["out"] == ("W3", "declared_target", None, None, None)


def diffpair():
    return topo("wp_diff",
                [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"),
                 mos("M5", "nmos", "t", "vb", "gnd"), mos("M3", "pmos", "o1", "pb", "vdd"),
                 mos("M4", "pmos", "o2", "pb", "vdd")],
                {"inp": ("input", "a"), "inn": ("input", "a"), "o1": ("output", "b"), "o2": ("output", "b")},
                bias=["pb", "vb"])                                                           # vb: M5 gate, pb: M3·M4 gate


def _lo_hi(col, pair):
    """같은 1-WL 색 짝 중 구조 색(dc_colour -- 3.0b, 정점마다 유일) 작은 쪽, 큰 쪽."""
    lo, hi = sorted(pair, key=lambda k: col[k])
    return lo, hi


def test_symmetric_diffpair_choices_by_canonical_position(tmp_path, toy_access):
    """[r11] 3.0b: 모든 정렬 키의 구조 색이 정점마다 유일해 이름이 결정을 가르지 않는다 -> dc_tie_breaks = ().
    손계산(3절 규칙, 이름 대신 dc_colour): F 밖 입력 포트 inp·inn -> 같은 DC 엣지; 성분 {inn, inp, t} 에 F 없음 -> 뿌리 = 입력 포트 중
    색 최소(W4 free_window, y 키 INPUT_GROUP_KEY), 다른 포트 = input_tie(known 뿌리). M1·M2(같은 순위) 중 색 작은 쪽이 트리(vgs_source 로 t),
    다른 쪽 cycle_vgs. M3·M4 (pb, vdd) -> 색 작은 쪽 트리, 다른 쪽 parallel_vgs(partner = 트리 쪽). 색은 스냅샷 입력 열."""
    ctx = build_ctx(tmp_path, diffpair(), toy_access)[2]
    nw, co, ties = plan(ctx)
    ncol = dict(ctx.base.column("node", "dc_colour"))
    ecol = dict(ctx.base.column("device", "dc_colour"))
    assert tuple(ties) == ()
    root, other = _lo_hi(ncol, ("inp", "inn"))
    assert strip(nw)[root] == ("W4", "free_window", None, None, INPUT_GROUP_KEY)
    assert strip(nw)[other] == ("W2", "input_tie", None, root, None)
    w12, d12 = _lo_hi(ecol, ("M1", "M2"))
    assert co[w12] == DeviceCoord("writer", "tree")
    assert co[d12] == DeviceCoord("dependent", "cycle_vgs")
    w34, d34 = _lo_hi(ecol, ("M3", "M4"))
    assert co[w34] == DeviceCoord("writer", "tree")
    assert co[d34] == DeviceCoord("dependent", "parallel_vgs", w34)
    assert strip(nw)["t"][:3] == ("W2", "vgs_source", w12)
    assert strip(nw)["vb"] == ("W2", "vgs_gate", "M5", "gnd", None)


def test_renamed_diffpair_plan_follows_colour_correspondence(tmp_path, toy_access):
    """[r11] M1↔M2 이름 맞바꿈(연결 그대로): 계획이 정점 대응 τ(같은 dc_colour 끼리, 3.0b 성질 (7)) 아래 같다 -- 이름이 아니라 정준 위치가
    선택을 정한다. 동률 기록 없음."""
    a = build_ctx(tmp_path, diffpair(), toy_access)[2]
    d = diffpair()
    d["topology_name"] = "wp_diff_sw"
    for e in d["netlist"]:
        e["name"] = {"M1": "M2", "M2": "M1"}.get(e["name"], e["name"])
    b = build_ctx(tmp_path, d, toy_access)[2]

    def by_colour(ctx):
        nw, co, ties = plan(ctx)
        nc = dict(ctx.base.column("node", "dc_colour"))
        ec = dict(ctx.base.column("device", "dc_colour"))
        f = lambda x: ec.get(x, nc.get(x, x)) if x is not None else None          # noqa: E731
        nodes = {nc[n]: (w.tier, w.relation, f(w.element), f(w.known), w.y_key if w.y_key == INPUT_GROUP_KEY else f(w.y_key))
                 for n, w in nw.items()}
        coords = {ec[m]: (c.role, c.relation, f(c.partner)) for m, c in co.items()}
        return nodes, coords, tuple(ties)
    assert by_colour(a) == by_colour(b)
    assert by_colour(b)[2] == ()


def test_resistor_cycle_stop(tmp_path, toy_access):
    doc = topo("wp_rcycle", [mos("M1", "nmos", "out", "in", "gnd")], {"in": ("input", "x"), "out": ("output", "y")},
               passives=[two("R1", "resistor", "vdd", "out"), two("R2", "resistor", "out", "gnd")])
    with pytest.raises(StructureUnresolvedError) as ei:
        build_ctx(tmp_path, doc, toy_access)
    d = detail(ei.value)
    assert d["rule_branch"] == "dc_resistor_cycle" and d["reason"] == "unsupported_rule_branch"
    assert set(d["nets"]) == {"out"} | ({"vdd"} if "vdd" in d["nets"] else {"gnd"})
    assert len(ei.value.record.devices) == 1


@pytest.mark.parametrize("name", NINE)
def test_library_reorder_bit_identical(name, tmp_path, toy_access):
    raw, td, spec, inputs, s1, ctx = library_ctx(name, toy_access)
    d = json.loads(json.dumps(raw))
    random.Random(11).shuffle(d["netlist"])
    random.Random(12).shuffle(d["passive_elements"])
    donors, counters = open_run()                     # 섞은 netlist = 다른 실행
    ctx2 = build_kernel_context(build_s1(load_doc(tmp_path, d), dict(inputs.supplies_v), donors=donors, counters=counters),
                                inputs, toy_access, donors=donors, counters=counters)
    assert plan(ctx2) == plan(ctx)
    for f in ("dc_writer", "dc_colour"):
        assert ctx2.base.column("node", f) == ctx.base.column("node", f)


@pytest.mark.parametrize("seed", [1, 2])
@pytest.mark.parametrize("name", NINE)
def test_library_renaming_metamorphic(name, seed, tmp_path, toy_access):
    raw, td, spec, inputs, s1, ctx = library_ctx(name, toy_access)
    d2, sn, se = rename(raw, seed)
    sigma = dict(sn)
    sigma.update(se)
    sigma[INPUT_GROUP_KEY] = INPUT_GROUP_KEY
    inputs2 = type(inputs)(tuple(sorted((sn[k], v) for k, v in inputs.supplies_v)), inputs.input_dc_v,
                           tuple((sn[k], v) for k, v in inputs.node_targets),
                           tuple(sorted((se.get(k, k), v) for k, v in inputs.element_values)),
                           tuple(sorted(se[k] for k in inputs.linear_devices)), inputs.pending,
                           tuple(sorted(se[k] for k in inputs.engine_elements)))          # [r5] 7번째 칸도 σ 로
    donors, counters = open_run()                     # 이름 바꾼 회로 = 다른 실행
    ctx2 = build_kernel_context(build_s1(load_doc(tmp_path, d2), dict(inputs2.supplies_v), donors=donors, counters=counters),
                                inputs2, toy_access, donors=donors, counters=counters)
    # [r11] 3.0b 성질 (7): 이름 대신 정준 위치가 선택을 정하고 TieBreak 기록은 비므로, 비교는 σ 가 아니라 τ(두 사례의 같은 dc_colour 짝) 아래서 한다
    assert tuple(ctx2.base.value("graph", DC_KEY, "dc_tie_breaks")) == ()

    def tau(c):
        ec = dict(c.base.column("device", "dc_colour"))
        nc = dict(c.base.column("node", "dc_colour"))
        return lambda x: ("d", ec[x]) if x in ec else (("n", nc[x]) if x in nc else ("k", x))
    t1, t2 = tau(ctx), tau(ctx2)
    w1 = {t1(m) for m, c in ctx.base.column("device", "dc_coord") if c.role == "writer"}
    w2 = {t2(m) for m, c in ctx2.base.column("device", "dc_coord") if c.role == "writer"}
    assert w1 == w2, "정준 대응 아래 writer 선택이 다르다"
    k1 = {(k, t1(key)) for k, key in kschema(ctx).components}
    k2 = {(k, t2(key)) for k, key in kschema(ctx2).components}
    assert k1 == k2, "정준 대응 아래 θ 키가 다르다"
    # 개수 구조는 항상 같다
    assert len(w1) == len(w2) and len(k1) == len(k2)
    tiers = lambda c: sorted(w.tier for _, w in c.base.column("node", "dc_writer"))   # noqa: E731
    assert tiers(ctx) == tiers(ctx2)
    # [r5] 수동소자 θ 성분과 영점 상쇄 판정(연결만으로 정해짐 -- 동률 기록 없음)은 σ 를 그대로 따른다(9절 + 4.4)
    pk = ("capacitance", "ss_resistance")
    assert {(t, sigma[k]) for t, k in kschema(ctx).components if t in pk} == {
        (t, k) for t, k in kschema(ctx2).components if t in pk}
    zc1 = {(sigma[z.resistor], sigma[z.end_net] if z.end_net is not None else None,
            tuple(sorted(sigma[n] for n in z.far_nets)), tuple(sorted(sigma[c] for c in z.cells)), z.reason)
           for z in kschema(ctx).zero_cancel}
    zc2 = {(z.resistor, z.end_net, tuple(z.far_nets), tuple(z.cells), z.reason) for z in kschema(ctx2).zero_cancel}
    assert zc1 == zc2


def test_block_is_theta_free_and_reused(ctx_c):
    # oracle 대조: card B C4 판정 1 -- 같은 lineage 재호출 = reuse, ctx 실행 계수(C1) 증분 = (calls 1, reuses 1)
    ctx = ctx_c[2]
    base = ctx.base
    before = block_row(ctx.counters, dc_writer_plan.name)
    assert dc_writer_plan(base, (), False, **run_of(ctx)) is base
    assert row_delta(block_row(ctx.counters, dc_writer_plan.name), before) == (1, 1, 0, 0, 0, 0)


# ===========================================================================
# [U4] DEC-95 (3) 종속 소자 선택 전체 순서 (D-GB7c, 설계 40 §3.7-4, 계획 DEC-95 (3)·DEC-64, CONTRACT 14.4)
# ===========================================================================
# oracle (d) 사용자 결정 DEC-95 (3) 의 우선순위 문언: ratified 선택 -> diode -> GB5 gm 요구·뒤 stage 소자는 독립 유지 -> 대칭 궤도
# 대표 -> 이름. 'Kruskal 키가 작은 엣지가 트리(독립 = writer)' 이므로 같은 equal_vgs 묶음 안에서 누가 writer 가 되는지가 관찰값이다.
# 회로: (i) circuit_mirror -- diode M1 과 거울 M2 가 같은 (gate nb, source gnd) 평행 엣지, (ii) 대칭 4소자 -- MA·MB(gate pb = 입력
# 포트), MC·MD(gate pc = 바이어스) 가 서로 대칭이라 구조 색이 같고 힌트가 없으면 이름이 정한다.

from gmid_engine.sizing import NO_ORDER_HINTS, OrderHints                                       # noqa: E402

from .conftest import build_ctx_u4, circuit_mirror                                              # noqa: E402


def _sym_doc(names=("MA", "MB", "MC", "MD")):
    a, b, c, d = names
    return topo("u4_sym", [mos(a, "nmos", "oa", "pb", "gnd"), mos(b, "nmos", "ob", "pb", "gnd"),
                           mos(c, "pmos", "oa", "pc", "vdd"), mos(d, "pmos", "ob", "pc", "vdd")],
                {"pb": ("input", "x"), "oa": ("output", "y"), "ob": ("output", "y")}, bias=["pc"])


def _roles(ctx):
    return {k: v.role for k, v in ctx.base.column("device", "dc_coord")}


def _writer_of(ctx, net):
    return dict(ctx.base.column("node", "dc_writer"))[net].element


def _sym(tmp_path, r4_access, hints, names=("MA", "MB", "MC", "MD")):
    return build_ctx_u4(tmp_path, _sym_doc(names), r4_access, order_hints=hints)[1]


def _mir(tmp_path, r4_access, hints):
    return build_ctx_u4(tmp_path, circuit_mirror(), r4_access, order_hints=hints, element_values=(("I1", 1e-5),))[1]


@pytest.mark.parametrize("hints,writer", [
    (NO_ORDER_HINTS, "MA"),                                              # 동률 -> 이름(MA < MB)
    (OrderHints(independent=("MB",)), "MB"),                             # ratified 독립
    (OrderHints(gm_required=("MB",)), "MB"),                             # GB5 gm 요구
    (OrderHints(stage=(("MA", 1), ("MB", 2))), "MB"),                     # 뒤 stage
    (OrderHints(stage=(("MA", 2), ("MB", 1))), "MA"),
    (OrderHints(independent=("MA",), gm_required=("MB",)), "MA"),        # ratified > gm 요구
    (OrderHints(gm_required=("MA",), stage=(("MA", 1), ("MB", 2))), "MA"),  # gm 요구 > 뒤 stage
], ids=["none", "ratified", "gm", "stage_b", "stage_a", "ratified_over_gm", "gm_over_stage"])
def test_dec95_order_symmetric_pair(tmp_path, r4_access, hints, writer):
    ctx = _sym(tmp_path, r4_access, hints)
    other = "MB" if writer == "MA" else "MA"
    assert _writer_of(ctx, "pb") == writer
    assert _roles(ctx)[writer] == "writer" and _roles(ctx)[other] == "dependent"
    assert ("ln_idu", writer) in kschema(ctx).components and ("ln_idu", other) not in kschema(ctx).components


@pytest.mark.parametrize("hints,writer", [
    (NO_ORDER_HINTS, "M1"),                                              # diode 가 writer
    (OrderHints(independent=("M2",)), "M2"),                             # ratified > diode
    (OrderHints(gm_required=("M2",)), "M1"),                             # diode > gm 요구
    (OrderHints(stage=(("M1", 1), ("M2", 2))), "M1"),                     # diode > 뒤 stage
], ids=["none", "ratified_over_diode", "diode_over_gm", "diode_over_stage"])
def test_dec95_order_diode_pair(tmp_path, r4_access, hints, writer):
    ctx = _mir(tmp_path, r4_access, hints)
    other = "M2" if writer == "M1" else "M1"
    assert _writer_of(ctx, "nb") == writer
    assert _roles(ctx)[writer] == "writer" and _roles(ctx)[other] == "dependent"


def test_empty_hints_identical_to_default(tmp_path, r4_access):
    """힌트가 비면 종래 순서와 같다(CONTRACT 14.4): 인자 생략·NO_ORDER_HINTS·빈 OrderHints 의 계획 스냅샷 비트 동일."""
    a = build_ctx_u4(tmp_path / "a", _sym_doc(), r4_access)[1]
    b = _sym(tmp_path / "b", r4_access, NO_ORDER_HINTS)
    c = _sym(tmp_path / "c", r4_access, OrderHints((), (), ()))
    assert a.base.fp == b.base.fp == c.base.fp
    assert a.base.value("graph", DC_KEY, "dc_tie_breaks") == b.base.value("graph", DC_KEY, "dc_tie_breaks")


def test_hint_on_tree_only_device_changes_nothing(tmp_path, r4_access):
    """비트리 관계가 없는 소자(M3: 평행 짝 없음)에 대한 힌트는 writer 선택을 바꾸지 않는다."""
    a = _mir(tmp_path / "a", r4_access, NO_ORDER_HINTS)
    b = _mir(tmp_path / "b", r4_access, OrderHints(independent=("M3",), gm_required=("M3",), stage=(("M3", 9),)))
    for f in (("node", "dc_writer"), ("device", "dc_coord")):
        assert a.base.column(*f) == b.base.column(*f)
    assert kschema(a) == kschema(b)


@pytest.mark.parametrize("names", [("MA", "MB", "MC", "MD"), ("Z1", "A1", "MC", "MD")], ids=["ab", "swapped_order"])
def test_dec95_name_bijection(tmp_path, r4_access, names):
    """DEC-95 (3) 'metamorphic: 이름 전단사 후 결과 동일(이름 사상 적용)': 힌트가 가리키는 소자(σ(MB))가 writer -- 이름 순서가
    뒤집혀도(σ(MB) = A1 < σ(MA) = Z1) 같다. 힌트가 없으면 이름순이라 바뀌지만(동률의 마지막 규칙) 힌트가 있으면 구조가 정한다."""
    a, b = names[0], names[1]
    for i, hints in enumerate((OrderHints(independent=(b,)), OrderHints(stage=((a, 1), (b, 2))), OrderHints(gm_required=(b,)))):
        ctx = _sym(tmp_path / ("h%d" % i), r4_access, hints, names)
        assert _writer_of(ctx, "pb") == b
