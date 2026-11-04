"""`dc_writer_plan(snapshot, target_nets, input_dc_declared)` -- CONTRACT 3절 [r2].

- 손 회로: 구조상 선택이 하나뿐인 경우 NodeWrite·DeviceCoord 를 손으로 적고 비교. [r11] 대칭 회로의 선택은 구조 색 dc_colour(3.0b, 정점마다
  유일 -- 1-WL 색 + 정준 위치)가 정하고 TieBreak 는 생기지 않는다: 기대값은 스냅샷 입력 열 dc_colour 로 3절 규칙을 손으로 적용한다.
- 9회로: 불변식(종속 수 = G_vgs 순환수, W4 수)은 test_kernel_context. 여기서는 metamorphic:
  (1) 순서 섞기 -> 계획 비트 동일, (2) 이름 전단사 σ -> (writer 집합, θ 스키마 키 집합) = σ(원래 것), 차이는 모두 원래 계획의
  dc_tie_breaks·CurrentBasis.ties 후보 안(9절).
"""
import json
import random
from pathlib import Path

import gmid_engine

import pytest

from gmid_engine.core import StructureUnresolvedError
from gmid_engine.graph import build_s1
from gmid_engine.sizing import (DC_KEY, DeviceCoord, NodeWrite, TieBreak, build_kernel_context,
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
                {"inp": ("input", "differential_input_p"), "inn": ("input", "differential_input_n"),
                 "o1": ("output", "b"), "o2": ("output", "b")},                              # [IT-1 DEC-106] 입력 점 규칙의 차동쌍 role
                bias=["pb", "vb"])                                                           # vb: M5 gate, pb: M3·M4 gate


def _lo_hi(col, pair):
    """같은 1-WL 색 짝 중 구조 색(dc_colour -- 3.0b, 정점마다 유일) 작은 쪽, 큰 쪽."""
    lo, hi = sorted(pair, key=lambda k: col[k])
    return lo, hi


def test_symmetric_diffpair_choices_by_canonical_position(tmp_path, toy_access):
    """[r11] 3.0b: 모든 정렬 키의 구조 색이 정점마다 유일해 이름이 결정을 가르지 않는다 -> dc_tie_breaks = ().
    손계산(3절 규칙, 이름 대신 dc_colour): [IT-1 DEC-106 -- 입력 점] 입력 포트 둘(p inp, n inn)을 한 점 P 로 묶는다. 성분 {P, t} 에 F 없음 -> 뿌리 = 입력 점
    (두 포트 모두 W4 input_point, y 키 = p 포트 inp). P-t 엣지 M1·M2 는 묶은 뒤 같은 (gate, source) -> 하나만 트리(어느 쪽인지 단언 안 함), 다른 쪽 parallel_vgs.
    M3·M4 (pb, vdd) -> 색 작은 쪽 트리, 다른 쪽 parallel_vgs(partner = 트리 쪽). 색은 스냅샷 입력 열."""
    ctx = build_ctx(tmp_path, diffpair(), toy_access)[2]
    nw, co, ties = plan(ctx)
    ecol = dict(ctx.base.column("device", "dc_colour"))
    assert tuple(ties) == ()
    assert [(strip(nw)[x][:2], strip(nw)[x][4]) for x in ("inp", "inn")] == [(("W4", "input_point"), "inp")] * 2
    w12 = [m for m in ("M1", "M2") if co[m].role == "writer"]                       # 입력쌍 평행: 어느 쪽이 종속인지는 단언하지 않는다(interface)
    d12 = [m for m in ("M1", "M2") if co[m].role == "dependent"]
    assert len(w12) == 1 and len(d12) == 1
    w12, d12 = w12[0], d12[0]
    assert co[w12] == DeviceCoord("writer", "tree")
    assert co[d12] == DeviceCoord("dependent", "parallel_vgs", w12)
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
        pair = {"inp", "inn"}                                                     # 입력 점: τ 는 연결 자기동형이라 p·n 을 맞바꿀 수 있다(DC 는 p·n 을 가르지 않는다)
        f = lambda x: "P" if x in pair else (ec.get(x, nc.get(x, x)) if x is not None else None)   # noqa: E731
        nodes = {nc[n]: (w.tier, w.relation, f(w.element), f(w.known), f(w.y_key))
                 for n, w in nw.items() if n not in pair}
        point = sorted((nw[n].tier, nw[n].relation, f(nw[n].y_key)) for n in pair)
        coords = {ec[m]: (c.role, c.relation, f(c.partner)) for m, c in co.items()}
        return nodes, point, coords, tuple(ties)
    assert by_colour(a) == by_colour(b)
    assert by_colour(b)[3] == ()
    assert plan(a)[0]["inp"].y_key == plan(a)[0]["inn"].y_key == plan(b)[0]["inp"].y_key == plan(b)[0]["inn"].y_key == "inp"   # y 키 = role p 포트(이름 맞바꿈과 무관)


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

    def tau(c, doc):
        ec = dict(c.base.column("device", "dc_colour"))
        nc = dict(c.base.column("node", "dc_colour"))
        pair = {k for k, v in doc["ports"].items() if isinstance(v, dict) and v.get("role") in ("differential_input_p", "differential_input_n")}
        return lambda x: ("P",) if x in pair else (("d", ec[x]) if x in ec else (("n", nc[x]) if x in nc else ("k", x)))
    t1, t2 = tau(ctx, raw), tau(ctx2, d2)
    w1 = {t1(m) for m, c in ctx.base.column("device", "dc_coord") if c.role == "writer"}
    w2 = {t2(m) for m, c in ctx2.base.column("device", "dc_coord") if c.role == "writer"}
    assert w1 == w2, "정준 대응 아래 writer 선택이 다르다"
    k1 = {(k, t1(key)) for k, key in kschema(ctx).components}
    k2 = {(k, t2(key)) for k, key in kschema(ctx2).components}
    assert k1 == k2, "정준 대응 아래 θ 키가 다르다"
    # 개수 구조는 항상 같다
    assert len(w1) == len(w2) and len(k1) == len(k2)
    # y 키는 role 을 따른다: σ 로 옮기면 같은 입력 점 키
    pk = [k for k, v in raw["ports"].items() if isinstance(v, dict) and v.get("role") == "differential_input_p"]
    if pk and ("y", pk[0]) in set(kschema(ctx).components):
        assert ("y", sn[pk[0]]) in set(kschema(ctx2).components)
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


# ===========================================================================
# [IT-1] 입력 DC 미선언 입력 포트 -- 입력 점 규칙 (card 20261104-it1-input-point, 설계 41 v1.16.3 §4.7-1·§6.7-1a, 계획 DEC-106)
# ===========================================================================
# oracle: (손) toy 연결에서 손으로 유도한 writer·종속 분류·순환 수. (식) interface 의 정지 detail 꼴. (독립) 어휘·소스 부재.
# 규칙(DEC-106): 입력 DC 미선언이고 입력 포트가 둘이며 role 이 differential_input_p·differential_input_n 각 하나이면 두 포트를 G_vgs 에서 한 점(입력 점)으로
# 묶는다. 점이 F(레일·목표·선언 입력)에 닿지 않으면 성분의 W4 뿌리 = 입력 점 하나(두 포트 모두 relation input_point, y 키 = p 포트 넷), 닿으면 y 성분 0.
# 묶은 뒤 (gate, source)·kind 가 같아지는 쌍은 하나가 parallel_vgs. 종속 수 = F 한 점·입력 점 한 점으로 묶은 G_vgs 의 순환수 E - V + C.
# 그 밖(차동쌍 둘, 차동쌍 없는 입력 둘 이상, 차동쌍 + 다른 입력)은 탐색 전 정지 input_cm_undefined. 입력 DC 선언이면 표 전체 무동작.
# 평행 쌍 어느 쪽이 종속인지·n 포트의 known 은 단언하지 않는다(대칭).

import gmid_engine.sizing as _SZ                                                                   # noqa: E402
import gmid_engine.sizing.s2_values as _S2V                                                         # noqa: E402

_IT1_RELATIONS = {"rail", "declared_target", "input_dc", "vgs_gate", "vgs_source", "resistor_drop", "free_window", "input_point"}
_IT1_COORD_RELATIONS = {"tree", "parallel_vgs", "cycle_vgs", "fixed_vgs"}


def _it1_rank(edges):
    """oracle (식): 순환수 E - V + C (V = 엣지가 닿는 노드, C = 성분 수). edges = 손으로 적은 (노드, 노드) 목록 -- 레일은 모두 'F', 입력 포트 둘은 'P'."""
    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in edges:
        parent.setdefault(a, a)
        parent.setdefault(b, b)
    for a, b in edges:
        parent[find(a)] = find(b)
    return len(edges) - len(parent) + len({find(x) for x in parent})


def _it1_ports(p, n, outs=("o1", "o2")):
    d = {p: ("input", "differential_input_p"), n: ("input", "differential_input_n")}
    d.update({o: ("output", "b") for o in outs})
    return d


def _it1_diff_doc(pname="inp", nname="inn", mp="M1", mn="M2", t="t", name="it1_diff"):
    """차동 입력 toy: (mp: o1, pname, t), (mn: o2, nname, t), 꼬리 M5(t, vb, gnd), 부하 M3(o1, pb3, vdd)·M4(o2, pb4, vdd)(게이트가 달라 부하 평행 없음).
    G_vgs(입력 점 P, 레일 F): P-t 둘(mp·mn), vb-F, pb3-F, pb4-F."""
    return topo(name,
                [mos(mp, "nmos", "o1", pname, t), mos(mn, "nmos", "o2", nname, t), mos("M5", "nmos", t, "vb", "gnd"),
                 mos("M3", "pmos", "o1", "pb3", "vdd"), mos("M4", "pmos", "o2", "pb4", "vdd")],
                _it1_ports(pname, nname), bias=["vb", "pb3", "pb4"])


_IT1_DIFF_EDGES = [("P", "t"), ("P", "t"), ("vb", "F"), ("pb3", "F"), ("pb4", "F")]


def _it1_ftouch_doc():
    """입력 점이 F 에 닿는 toy: 입력쌍 source 가 레일. M1(o1, inp, gnd)·M2(o2, inn, gnd), 부하 M3(o1, pb3, vdd)·M4(o2, pb4, vdd).
    G_vgs: P-F 둘, pb3-F, pb4-F -> V={F,P,pb3,pb4} E=4 C=1 -> 순환수 1."""
    return topo("it1_ftouch",
                [mos("M1", "nmos", "o1", "inp", "gnd"), mos("M2", "nmos", "o2", "inn", "gnd"),
                 mos("M3", "pmos", "o1", "pb3", "vdd"), mos("M4", "pmos", "o2", "pb4", "vdd")],
                _it1_ports("inp", "inn"), bias=["pb3", "pb4"])


_IT1_FTOUCH_EDGES = [("P", "F"), ("P", "F"), ("pb3", "F"), ("pb4", "F")]


def _it1_check_diff(ctx, p, n, mp, mn, t):
    """차동 toy 의 입력 점 결과를 단언하고 (nw, co) 를 돌려준다(이름 전단사 test 가 구조를 비교한다)."""
    nw, co, ties = plan(ctx)
    assert all(w.relation in _IT1_RELATIONS for w in nw.values())
    assert all(c.relation in _IT1_COORD_RELATIONS for c in co.values())
    assert [(nw[x].tier, nw[x].relation, nw[x].y_key) for x in (p, n)] == [("W4", "input_point", p)] * 2   # 두 포트 같은 점, y 키 = p 포트 넷
    dep_pair = [m for m in (mp, mn) if co[m].role == "dependent"]
    tree_pair = [m for m in (mp, mn) if co[m].role == "writer"]
    assert len(dep_pair) == 1 and len(tree_pair) == 1                                   # 묶은 뒤 (gate, source) 같은 쌍: 하나만 종속
    assert co[tree_pair[0]] == DeviceCoord("writer", "tree")
    assert co[dep_pair[0]] == DeviceCoord("dependent", "parallel_vgs", tree_pair[0])
    assert (nw[t].tier, nw[t].relation, nw[t].element) == ("W2", "vgs_source", tree_pair[0])
    assert (nw["vb"].tier, nw["vb"].relation, nw["vb"].element) == ("W2", "vgs_gate", "M5")
    assert co["M3"] == DeviceCoord("writer", "tree") and co["M4"] == DeviceCoord("writer", "tree")
    assert sum(1 for c in co.values() if c.role == "dependent") == _it1_rank(_IT1_DIFF_EDGES) == 1   # 불변식: 종속 수 = 순환수
    ys = {k for tk, k in kschema(ctx).components if tk == "y"}
    assert ys == {p, "o1", "o2"}                                                         # θ 키 y 하나(n 포트 키 없음)
    assert not any(tb.decision == "input_tie_order" for tb in ties)
    return nw, co


def test_it1_t1a_undeclared_diffpair_one_input_point(tmp_path, toy_access):
    """T-1a (손): 두 포트가 같은 꼬리 source 에 닿는 차동 toy -> 두 포트 모두 input_point·W4·y 키 = p 포트(inp), 입력쌍 둘째 소자 parallel_vgs,
    종속 수 = 묶은 순환수 1 (P-t 평행 하나). base 는 둘째 포트가 vgs_gate W2 다."""
    ctx = build_ctx(tmp_path, _it1_diff_doc(), toy_access)[2]
    _it1_check_diff(ctx, "inp", "inn", "M1", "M2", "t")


def _it1_two_comp_doc():
    """입력 포트 in1(p)·in2(n) 가 서로 다른 G_vgs 성분({in1,t1}·{in2,t2})에 있는 toy: M1(o1,in1,t1) M2(o2,in2,t2), 꼬리 M5(t1,vb,gnd)·M6(t2,vb,gnd),
    부하 MP1(o1,pb1,vdd)·MP2(o2,pb2,vdd). 한 점 P 로 묶으면 P-t1, P-t2, vb-F 둘(M5·M6 평행), pb1-F, pb2-F: V=7 E=6 C=2 -> 1."""
    return topo("it1_two_comp",
                [mos("M1", "nmos", "o1", "in1", "t1"), mos("M2", "nmos", "o2", "in2", "t2"),
                 mos("M5", "nmos", "t1", "vb", "gnd"), mos("M6", "nmos", "t2", "vb", "gnd"),
                 mos("MP1", "pmos", "o1", "pb1", "vdd"), mos("MP2", "pmos", "o2", "pb2", "vdd")],
                _it1_ports("in1", "in2"), bias=["vb", "pb1", "pb2"])


def test_it1_t1b_two_gvgs_components_become_one_point(tmp_path, toy_access):
    """T-1b (손): 두 포트가 서로 다른 G_vgs 성분 -> 정지 없이 한 점 P(성분 {P,t1,t2} 는 F 에 닿지 않음), W4 뿌리 하나(y 키 in1). 입력쌍 M1·M2 는 둘 다
    트리(P-t1, P-t2 는 평행이 아님), 평행 종속은 꼬리 M5·M6 (vb, gnd) 하나뿐 = 순환수 1. 입력 점에서 두 꼬리 넷이 KVL 로 쓰인다(vgs_source)."""
    ctx = build_ctx(tmp_path, _it1_two_comp_doc(), toy_access)[2]
    nw, co, _ties = plan(ctx)
    assert all(w.relation in _IT1_RELATIONS for w in nw.values())
    assert [(nw[x].tier, nw[x].relation, nw[x].y_key) for x in ("in1", "in2")] == [("W4", "input_point", "in1")] * 2
    assert co["M1"] == DeviceCoord("writer", "tree") and co["M2"] == DeviceCoord("writer", "tree")
    dep = sorted((m, c.relation) for m, c in co.items() if c.role == "dependent")
    assert len(dep) == 1 and dep[0][0] in ("M5", "M6") and dep[0][1] == "parallel_vgs"
    assert sum(1 for c in co.values() if c.role == "dependent") == _it1_rank(
        [("P", "t1"), ("P", "t2"), ("vb", "F"), ("vb", "F"), ("pb1", "F"), ("pb2", "F")]) == 1
    assert (nw["t1"].tier, nw["t1"].relation, nw["t1"].element) == ("W2", "vgs_source", "M1")
    assert (nw["t2"].tier, nw["t2"].relation, nw["t2"].element) == ("W2", "vgs_source", "M2")
    assert {k for tk, k in kschema(ctx).components if tk == "y"} == {"in1", "o1", "o2"}


def test_it1_t1c_input_point_touching_f_has_no_y_component(tmp_path, toy_access):
    """T-1c (손): 입력쌍 source 가 레일 -> 입력 점 P 가 F 에 닿는다(P-F 평행 둘). v_cm 은 KVL 종속이라 어느 포트 항목에도 y 키가 없고 θ 에 ("y", "inp") 가
    없으며, 쌍 둘째 소자는 parallel_vgs. 종속 수 = 순환수 1. 어느 포트가 어떤 relation 인지는 단언하지 않는다(어휘 안인지만)."""
    ctx = build_ctx(tmp_path, _it1_ftouch_doc(), toy_access)[2]
    nw, co, _ties = plan(ctx)
    assert all(w.relation in _IT1_RELATIONS for w in nw.values())
    assert nw["inp"].y_key is None and nw["inn"].y_key is None
    assert {k for tk, k in kschema(ctx).components if tk == "y"} == {"o1", "o2"}
    tree = [m for m in ("M1", "M2") if co[m].role == "writer"]
    dep = [m for m in ("M1", "M2") if co[m].role == "dependent"]
    assert len(tree) == 1 and len(dep) == 1
    assert co[dep[0]] == DeviceCoord("dependent", "parallel_vgs", tree[0])
    assert sum(1 for c in co.values() if c.role == "dependent") == _it1_rank(_IT1_FTOUCH_EDGES) == 1


def _it1_isolated_doc(with_other_root=True):
    """iso = 드레인에만 닿는 입력 포트(G_vgs 밖 고립). with_other_root 면 in1 도 다른 입력 포트."""
    net = [mos("M7", "nmos", "iso", "vb", "gnd"), mos("MP", "pmos", "o1", "pb", "vdd"), mos("MQ", "pmos", "iso", "pb", "vdd")]
    ports = {"iso": ("input", "a"), "o1": ("output", "b")}
    if with_other_root:
        net += [mos("M1", "nmos", "o1", "in1", "t1"), mos("M5", "nmos", "t1", "vb", "gnd")]
        ports["in1"] = ("input", "a")
    else:
        net.append(mos("M1", "nmos", "o1", "vb", "gnd"))
    return topo("it1_iso", net, ports, bias=["vb", "pb"])


def test_it1_t1d_declared_input_plan_unchanged(tmp_path, toy_access):
    """T-1d (손, 무동작 -- base 에서도 통과): 입력 DC 선언 -> 입력 포트 둘 = F(relation input_dc, y 키 없음). M1(F-t)·M2(F-t) 는 게이트 넷이 달라
    parallel 이 아니라 둘 중 하나가 cycle_vgs. 부하 M3·M4 는 게이트가 달라 둘 다 트리. 종속 수 = 순환수: F,t,vb,pb3,pb4 / 엣지 F-t 둘·vb-F·pb3-F·pb4-F = 1."""
    ctx = build_ctx(tmp_path, _it1_diff_doc(), toy_access, input_dc_v=0.7)[2]
    nw, co, _ties = plan(ctx)
    assert tuple(_ties) == ()                                                            # dc_tie_breaks 비어 있음(구조 색이 정한다)
    assert strip(nw)["inp"] == ("W2", "input_dc", None, None, None) and strip(nw)["inn"] == ("W2", "input_dc", None, None, None)
    w12 = [m for m in ("M1", "M2") if co[m].role == "writer"]
    d12 = [m for m in ("M1", "M2") if co[m].role == "dependent"]
    assert len(w12) == 1 and len(d12) == 1 and co[w12[0]] == DeviceCoord("writer", "tree")
    assert co[d12[0]] == DeviceCoord("dependent", "cycle_vgs")
    gate = {"M1": "inp", "M2": "inn"}
    assert (nw["t"].tier, nw["t"].relation, nw["t"].element, nw["t"].known) == ("W2", "vgs_source", w12[0], gate[w12[0]])
    assert co["M3"] == DeviceCoord("writer", "tree") and co["M4"] == DeviceCoord("writer", "tree")
    assert sum(1 for c in co.values() if c.role == "dependent") == _it1_rank(
        [("F", "t"), ("F", "t"), ("vb", "F"), ("pb3", "F"), ("pb4", "F")]) == 1
    assert {k for tk, k in kschema(ctx).components if tk == "y"} == {"o1", "o2"}


def test_it1_t1d_single_input_unchanged(tmp_path, toy_access):
    """T-1d (손, 무동작 -- base 에서도 통과): 입력 포트 하나(source follower M1 nmos (vdd, in, out) + M2 nmos (out, vb, gnd)). G_vgs: in-out, vb-F -> 성분 {in,out}
    에 F 없음 -> 입력 포트 in 이 W4 뿌리(free_window, y 키 in), M1 트리."""
    doc = topo("it1_follower", [mos("M1", "nmos", "vdd", "in", "out"), mos("M2", "nmos", "out", "vb", "gnd")],
               {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}, bias=["vb"])
    nw, co, _ties = plan(build_ctx(tmp_path, doc, toy_access)[2])
    assert tuple(_ties) == ()                                                            # dc_tie_breaks 비어 있음
    assert (nw["in"].tier, nw["in"].relation, nw["in"].y_key) == ("W4", "free_window", "in")
    assert co["M1"] == DeviceCoord("writer", "tree")


def test_it1_t1d_isolated_single_input_builds(tmp_path, toy_access):
    """T-1d (손, 무동작): 고립 입력 포트가 하나뿐이면 정지하지 않고 y 키 = 그 넷(옛 규칙 그대로)."""
    ctx = build_ctx(tmp_path, _it1_isolated_doc(with_other_root=False), toy_access)[2]
    assert tuple(plan(ctx)[2]) == ()                                                     # dc_tie_breaks 비어 있음
    w = dict(ctx.base.column("node", "dc_writer"))["iso"]
    assert (w.tier, w.relation, w.y_key) == ("W4", "free_window", "iso")


# [IT-1 A-39 폐기 기록] 옛 test_it1_ring_cycle_vgs_after_port_delta_elimination·test_it1_dependent_count_equals_cycle_rank 는 같은 DC 엣지 삭제(옛 IT-1)의
# 전제(입력 포트를 따로 트리 경로로 씀)가 DEC-106 입력 점 묶음으로 바뀌어 폐기하고 T-1a/b/c/i 가 대신한다(retired_tests).

def _it1_triangle_doc():
    """입력 점 P 와 꼬리 t, u 가 삼각형을 이루는 toy: M1(o1, inp, t) M2(o2, inn, u) M3(o3, t, u), 꼬리 M5(t, vb, gnd)·M6(u, vb, gnd), 부하
    MP1(o1, pb1, vdd)·MP2(o2, pb2, vdd)·MP3(o3, pb3, vdd). G_vgs(P = inp ∪ inn): P-t, P-u, t-u, vb-F 둘, pb1-F, pb2-F, pb3-F -> V=8 E=8 C=2 -> 2."""
    return topo("it1_triangle",
                [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "o2", "inn", "u"), mos("M3", "nmos", "o3", "t", "u"),
                 mos("M5", "nmos", "t", "vb", "gnd"), mos("M6", "nmos", "u", "vb", "gnd"),
                 mos("MP1", "pmos", "o1", "pb1", "vdd"), mos("MP2", "pmos", "o2", "pb2", "vdd"), mos("MP3", "pmos", "o3", "pb3", "vdd")],
                _it1_ports("inp", "inn", outs=("o1", "o2", "o3")), bias=["vb", "pb1", "pb2", "pb3"])


def test_it1_t1i_triangle_through_input_point_has_one_cycle_vgs(tmp_path, toy_access):
    """T-1i (손): 입력 점으로 묶으면 P-t(M1), P-u(M2), t-u(M3) 삼각형이 생긴다 -> {M1, M2, M3} 중 정확히 하나만 cycle_vgs(비평행이라 parallel 아님),
    꼬리 M5·M6 (vb, gnd) 평행 하나 parallel_vgs, 종속 수 = 순환수 2. 어느 소자가 종속인지는 단언하지 않는다."""
    ctx = build_ctx(tmp_path, _it1_triangle_doc(), toy_access)[2]
    nw, co, _ties = plan(ctx)
    assert [(nw[x].tier, nw[x].relation, nw[x].y_key) for x in ("inp", "inn")] == [("W4", "input_point", "inp")] * 2
    assert [m for m in ("M1", "M2", "M3") if co[m].relation == "cycle_vgs"] and len(
        [m for m in ("M1", "M2", "M3") if co[m].relation == "cycle_vgs"]) == 1
    assert len([m for m in ("M1", "M2", "M3") if co[m].role == "dependent"]) == 1
    assert len([m for m in ("M5", "M6") if co[m].relation == "parallel_vgs"]) == 1
    assert sum(1 for c in co.values() if c.role == "dependent") == _it1_rank(
        [("P", "t"), ("P", "u"), ("t", "u"), ("vb", "F"), ("vb", "F"), ("pb1", "F"), ("pb2", "F"), ("pb3", "F")]) == 2


def _it1_two_pairs_doc():
    """차동쌍 둘: (ip1 p, in1 n) 과 (ip2 p, in2 n) 네 입력 포트."""
    return topo("it1_two_pairs",
                [mos("M1", "nmos", "o1", "ip1", "t1"), mos("M2", "nmos", "o2", "in1", "t1"), mos("M5", "nmos", "t1", "vb", "gnd"),
                 mos("M6", "nmos", "o1", "ip2", "t2"), mos("M7", "nmos", "o2", "in2", "t2"), mos("M8", "nmos", "t2", "vb", "gnd"),
                 mos("M3", "pmos", "o1", "pb3", "vdd"), mos("M4", "pmos", "o2", "pb4", "vdd")],
                {"ip1": ("input", "differential_input_p"), "in1": ("input", "differential_input_n"),
                 "ip2": ("input", "differential_input_p"), "in2": ("input", "differential_input_n"),
                 "o1": ("output", "b"), "o2": ("output", "b")}, bias=["vb", "pb3", "pb4"])


def _it1_no_pair_doc():
    """차동쌍 없는 입력 둘: 두 포트 role 이 single_ended_input 둘."""
    return topo("it1_no_pair",
                [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"), mos("M5", "nmos", "t", "vb", "gnd"),
                 mos("M3", "pmos", "o1", "pb3", "vdd"), mos("M4", "pmos", "o2", "pb4", "vdd")],
                {"inp": ("input", "single_ended_input"), "inn": ("input", "single_ended_input"),
                 "o1": ("output", "b"), "o2": ("output", "b")}, bias=["vb", "pb3", "pb4"])


def _it1_pair_plus_single_doc():
    """차동쌍 + 다른 입력: 차동쌍 (inp p, inn n) 에 단일 입력 ix(M6 gate)가 더해진다."""
    return topo("it1_pair_single",
                [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"), mos("M5", "nmos", "t", "vb", "gnd"),
                 mos("M3", "pmos", "o1", "pb3", "vdd"), mos("M4", "pmos", "o2", "pb4", "vdd"), mos("M6", "nmos", "o1", "ix", "gnd")],
                {"inp": ("input", "differential_input_p"), "inn": ("input", "differential_input_n"),
                 "ix": ("input", "single_ended_input"), "o1": ("output", "b"), "o2": ("output", "b")}, bias=["vb", "pb3", "pb4"])


def _it1_pair_plus_isolated_doc():
    """차동쌍 + 고립 입력 포트 iso(MOS gate·source 어디에도 안 닿고 M9·M10 drain 에만 닿음 -- 전류 경로 있음): 고립도 입력 포트로 센다."""
    return topo("it1_pair_iso",
                [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"), mos("M5", "nmos", "t", "vb", "gnd"),
                 mos("M3", "pmos", "o1", "pb3", "vdd"), mos("M4", "pmos", "o2", "pb4", "vdd"), mos("M9", "pmos", "iso", "pb3", "vdd"),
                 mos("M10", "nmos", "iso", "vb", "gnd")],
                {"inp": ("input", "differential_input_p"), "inn": ("input", "differential_input_n"),
                 "iso": ("input", "single_ended_input"), "o1": ("output", "b"), "o2": ("output", "b")}, bias=["vb", "pb3", "pb4"])


@pytest.mark.parametrize("doc_fn,ports", [
    (_it1_two_pairs_doc, {"ip1", "in1", "ip2", "in2"}),
    (_it1_no_pair_doc, {"inp", "inn"}),
    (_it1_pair_plus_single_doc, {"inp", "inn", "ix"}),
    (_it1_pair_plus_isolated_doc, {"inp", "inn", "iso"}),
], ids=["two_pairs", "no_pair_two_inputs", "pair_plus_single", "pair_plus_isolated"])
def test_it1_t1e_unsupported_input_combinations_stop(tmp_path, toy_access, doc_fn, ports):
    """T-1e (식): 입력 DC 미선언에서 (차동쌍 둘 / 차동쌍 없는 입력 둘 / 차동쌍 + 다른 입력(고립 포함)) 는 탐색 전 정지. reason·rule_branch 와
    ports(집합 비교 -- 순서 단언 금지) 는 interface '입력 점 규칙' 표. base 는 정지 없이 포트별 뿌리를 만든다."""
    with pytest.raises(StructureUnresolvedError) as ei:
        build_ctx(tmp_path, doc_fn(), toy_access)
    d = detail(ei.value)
    assert d["reason"] == "unsupported_rule_branch"
    assert d["rule_branch"] == "input_cm_undefined"
    assert len(d["ports"]) == len(ports) and set(d["ports"]) == ports


@pytest.mark.parametrize("doc_fn", [_it1_two_pairs_doc, _it1_no_pair_doc, _it1_pair_plus_single_doc], ids=["two_pairs", "no_pair", "pair_plus_single"])
def test_it1_t1e_declared_input_dc_disables_the_table(tmp_path, toy_access, doc_fn):
    """T-1e 대조 (식): 입력 DC 선언이면 위 표 전체가 무동작 -- 같은 toy 가 정지하지 않고 지어진다(입력 포트 = F, relation input_dc)."""
    nw, _co, _ties = plan(build_ctx(tmp_path, doc_fn(), toy_access, input_dc_v=0.7)[2])
    ins = [n for n in ("inp", "inn", "ip1", "in1", "ip2", "in2", "ix") if n in nw]
    assert ins and all(nw[n].relation == "input_dc" for n in ins)


@pytest.mark.parametrize("targets", [(("inp", 0.7),), (("inn", 0.7),)], ids=["only_p", "only_n"])
def test_it1_input_target_one_port_stops(tmp_path, toy_access, targets):
    """A-76 m1 (식, 물리 정합): 입력 DC 미선언 차동 입력의 두 포트 중 한 포트만 node_voltage_targets_v 로 선언하면 입력 점이 안 묶여 ΔV 가
    θ 함수가 되므로 탐색 전 정지. 분류는 input_cm_undefined 정지와 같은 꼴(reason unsupported_rule_branch + rule_branch)."""
    with pytest.raises(StructureUnresolvedError) as ei:
        build_ctx(tmp_path, _it1_diff_doc(), toy_access, node_targets=targets)
    d = detail(ei.value)
    assert d["reason"] == "unsupported_rule_branch"
    assert d["rule_branch"] == "input_target_one_port"


def test_it1_input_target_both_or_neither_does_not_stop(tmp_path, toy_access):
    """A-76 m1 대조 (식): 두 포트 다 선언 / 둘 다 안 선언은 정지하지 않는다. 안 선언은 입력 점(input_point) 그대로, 다 선언은 입력 점이 아니다."""
    (tmp_path / "none").mkdir()
    (tmp_path / "both").mkdir()
    nw0, _c0, _t0 = plan(build_ctx(tmp_path / "none", _it1_diff_doc(), toy_access)[2])
    assert nw0["inp"].relation == nw0["inn"].relation == "input_point"
    nw1, _c1, _t1 = plan(build_ctx(tmp_path / "both", _it1_diff_doc(), toy_access, node_targets=(("inn", 0.7), ("inp", 0.7)))[2])
    assert nw1["inp"].relation in _IT1_RELATIONS and nw1["inn"].relation in _IT1_RELATIONS
    assert "input_point" not in {nw1["inp"].relation, nw1["inn"].relation}


def test_it1_t1g_renamed_diffpair_same_structure(tmp_path, toy_access):
    """T-1g (손): 넷·소자 이름 맞바꿈과 새 이름 -> 같은 구조 결과, y 키는 맞바꾼 이름(p role 이 옮겨 간 넷). role 이 구조를 정하고 이름 판별은 없다."""
    for sub in "abc":
        (tmp_path / sub).mkdir()
    a = build_ctx(tmp_path / "a", _it1_diff_doc(), toy_access)[2]
    b = build_ctx(tmp_path / "b", _it1_diff_doc("inn", "inp", "M2", "M1", "t", "it1_diff_sw"), toy_access)[2]
    c = build_ctx(tmp_path / "c", _it1_diff_doc("zq", "ab", "MZ", "MA", "tt", "it1_diff_new"), toy_access)[2]
    na, ca = _it1_check_diff(a, "inp", "inn", "M1", "M2", "t")
    nb, cb = _it1_check_diff(b, "inn", "inp", "M2", "M1", "t")
    nc, cc = _it1_check_diff(c, "zq", "ab", "MZ", "MA", "tt")
    shape = lambda nw, co: (sorted((w.tier, w.relation) for w in nw.values()),                  # noqa: E731
                            sorted((x.role, x.relation) for x in co.values()))
    assert shape(na, ca) == shape(nb, cb) == shape(nc, cc)


def test_it1_t1g_swapped_roles_follow_role_not_name(tmp_path, toy_access):
    """T-1g (손): 같은 연결에서 p/n role 만 맞바꾸면(inp 가 n, inn 이 p) y 키가 inn 으로 옮겨 간다 -- y 키는 이름 순서가 아니라 role 이 정한다."""
    doc = _it1_diff_doc()
    doc["ports"]["inp"]["role"], doc["ports"]["inn"]["role"] = "differential_input_n", "differential_input_p"
    doc["topology_name"] = "it1_diff_roleswap"
    nw, _co, _ties = plan(build_ctx(tmp_path, doc, toy_access)[2])
    assert [(nw[x].relation, nw[x].y_key) for x in ("inp", "inn")] == [("input_point", "inn")] * 2


def test_it1_vocabulary_and_branch_codes():
    """T-1 (독립): 어휘 — REL_INPUT_POINT 와 BRANCH_INPUT_CM_UNDEFINED 가 새로 있고 옛 이름(REL_TIE 등·BRANCH_INPUT_MULTIPLE_ROOTS)은 없다."""
    assert _SZ.REL_INPUT_POINT == "input_point"
    assert _S2V.BRANCH_INPUT_CM_UNDEFINED == "input_cm_undefined"
    for name in ("REL_TIE", "INPUT_GROUP_KEY", "PATH_TIE", "TIE_INPUT_ORDER", "BRANCH_INPUT_MULTIPLE_ROOTS"):
        assert not hasattr(_SZ, name), name
        assert not hasattr(_S2V, name), name


def test_it1_writer_block_owns_plan_fields():
    """graph 계약 I1: node.dc_writer·device.dc_coord·graph.dc_tie_breaks 는 dc_writer_plan 이 쓴다(필드 writer 하나). READS 에 node.port_role·
    graph.gvgs_summary 가 늘었다(interface '필드' 표)."""
    w = set(dc_writer_plan.writes)
    assert ("node", "dc_writer") in w and ("device", "dc_coord") in w
    r = set(dc_writer_plan.reads)
    assert ("node", "port_role") in r and ("graph", "gvgs_summary") in r
    from gmid_engine.sizing import dc_columns
    assert ("node", "port_direction") in set(dc_columns.reads)                                    # 41:672 -- dc_columns 가 S1 포트 방향을 READS 로 읽는다


# ---------------------------------------------------------------- [IT-1 T-5b] g = s 소자의 쓰기 계획 (O-210 RR-6)

def _it1_gs_doc():
    """단일 입력 CS 에 비레일 gate == source 소자 Mgs 를 더한 toy: M1 nmos (out, in, gnd), M2 pmos (out, pb, vdd), M4 nmos (x, vb, gnd)(x 의 싱크),
    Mgs nmos (drain out, gate x, source x). G_vgs 엣지: in-F, pb-F, vb-F. Mgs 는 gate 넷 == source 넷(x)이라 자기 고리 -- G_vgs 엣지가 아니다."""
    return topo("it1_gs",
                [mos("M1", "nmos", "out", "in", "gnd"), mos("M2", "pmos", "out", "pb", "vdd"), mos("M4", "nmos", "x", "vb", "gnd"),
                 mos("Mgs", "nmos", "out", "x", "x")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}, bias=["pb", "vb"])


def test_it1_t5b_nonrail_gate_equals_source_is_fixed_vgs_dependent(tmp_path, toy_access):
    """T-5b (손): 비레일 g = s 소자는 정지하지 않고 쓰기 계획에서 DeviceCoord("dependent", "fixed_vgs"). 자기 고리가 순환 1이라 종속 수에 든다 -- 이 toy 의
    종속 = Mgs 하나(나머지 M1·M2·M4 는 서로 다른 G_vgs 엣지 in-F·pb-F·vb-F 의 트리). 그 소자는 ln_idu θ 성분이 없다(종속)."""
    ctx = build_ctx(tmp_path, _it1_gs_doc(), toy_access)[2]
    nw, co, _ties = plan(ctx)
    assert co["Mgs"] == DeviceCoord("dependent", "fixed_vgs")
    assert [m for m, c in co.items() if c.role == "dependent"] == ["Mgs"]
    assert ("ln_idu", "Mgs") not in set(kschema(ctx).components)
    assert "Mgs" not in ctx.inputs.linear_devices                      # 영역 선언 입력에 없음 = 포화 기본·전도(선언 없음). 꺼짐 분류 칸은 쓰기 계획에 없다
    assert all(co[m] == DeviceCoord("writer", "tree") for m in ("M1", "M2", "M4"))


def test_it1_t5b_rail_gate_equals_source_same_plan_as_nonrail(tmp_path, toy_access):
    """T-5b (손): 레일 g = s(Moff nmos (out, gnd, gnd))도 같은 처리 -- fixed_vgs 종속 하나."""
    doc = topo("it1_gs_rail",
               [mos("M1", "nmos", "out", "in", "gnd"), mos("M2", "pmos", "out", "pb", "vdd"), mos("Moff", "nmos", "out", "gnd", "gnd")],
               {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}, bias=["pb"])
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    _nw, co, _ties = plan(ctx)
    assert co["Moff"] == DeviceCoord("dependent", "fixed_vgs")
    assert ("ln_idu", "Moff") not in set(kschema(ctx).components)                       # 종속이라 θ ln_idu 성분 없음
    assert [m for m, c in co.items() if c.role == "dependent"] == ["Moff"]


def test_it1_t5c_writer_plan_source_has_no_gate_source_equality():
    """T-5c (독립, AST): 쓰기 계획 소스(sizing/)에 gate 넷과 source 넷의 동등 비교가 없다 -- g = s 는 `gate_source_same`(READS)로만 읽고, 판정식은
    s1_gvgs 한 자리다. 비교 양쪽 식의 글자가 (gate|g|… , source|s|…) 짝이면 위반으로 센다."""
    import ast
    import re
    root = Path(gmid_engine.__file__).resolve().parent
    g_pat = re.compile(r"(\bgate\b|\bg\b|_gate\b|\bgate_|\[\s*['\"]g['\"]\s*\])", re.I)
    s_pat = re.compile(r"(\bsource\b|\bs\b|_source\b|\bsource_|\[\s*['\"]s['\"]\s*\])", re.I)
    hits = []
    for p in sorted((root / "sizing").rglob("*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Compare) and any(isinstance(o, (ast.Eq, ast.NotEq, ast.Is, ast.IsNot)) for o in n.ops):
                parts = [ast.unparse(x) for x in [n.left] + list(n.comparators)]
                for i in range(len(parts)):
                    for j in range(len(parts)):
                        if i != j and g_pat.search(parts[i]) and s_pat.search(parts[j]):
                            hits.append("%s:%d %s" % (p.relative_to(root).as_posix(), n.lineno, " | ".join(parts)))
    assert hits == []
    assert "gate_source_same" in (root / "sizing" / "writer_plan.py").read_text(encoding="utf-8")        # READS 로 읽는다


def test_it1_t5c_gvgs_is_only_gate_source_same_writer():
    """T-5c (독립): gate_source_same 칸의 writer = s1_gvgs 의 graph.gvgs_summary 하나, 쓰기 계획은 그 필드를 읽기만 한다(writes 에 없음)."""
    from gmid_engine.graph import s1_gvgs
    assert ("graph", "gvgs_summary") in set(s1_gvgs.writes)
    assert ("graph", "gvgs_summary") not in set(dc_writer_plan.writes)


# ===========================================================================
# [card IT-2c T-E9] `node.dc_output_structure`·`OUTPUT_*` 삭제 (계획 v6.38.8 N3.8, design 41 v1.16.3 §4.7-W). 옛 OS test 13개(IT-2b 출력 구조 분류,
# 이 파일 525~693행)는 대상이 소멸해 삭제하고(승인 동작 변경 O-205, 약화 아님) 이 test 로 대체한다.
# oracle: (독립) 권한표·어휘 객체의 이름 집합 -- 피검 함수 호출 없음.
# ===========================================================================

def test_it2c_e9_output_structure_not_in_field_or_vocabulary():
    """oracle 대조: (독립) T-E9. `node.dc_output_structure` 가 `DC_WRITES`·`PLAN_WRITERS`·`S2_WRITERS` 어디에도 없고,
    `gmid_engine.sizing`·`gmid_engine.sizing.s2_values` 에 `OUTPUT_` 로 시작하는 어휘 이름이 없다."""
    import gmid_engine.sizing as S
    from gmid_engine.sizing import s2_values
    assert ("node", "dc_output_structure") not in {kf for kf, _ in S.S2_WRITERS.entries}
    for _writer, fields in S.DC_WRITES:
        assert ("node", "dc_output_structure") not in fields
    for mod in (S, s2_values):
        assert [n for n in dir(mod) if n.startswith("OUTPUT_")] == []
