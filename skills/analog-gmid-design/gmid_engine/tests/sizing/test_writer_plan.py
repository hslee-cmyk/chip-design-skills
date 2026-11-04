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
# [card IT-2b] `node.dc_output_structure` -- 출력 구조 분류 (design 41 v1.12.8 4.7-1a, 계획 N3.8 '출력 구조 분류 -- 규칙 하나')
# (규칙 H 1:1: 이 필드의 writer 는 쓰기 계획 블록 `dc_writer_plan` 이라 옛 `test_output_structure.py` 의 T-OS 13개를 이 파일로 옮겼다 -- test 이름·단언·
#  허용오차·리터럴은 그대로, helper 이름도 이 파일의 기존 이름과 겹치지 않아 그대로.)
#
# writer = 쓰기 계획 블록 `dc_writer_plan` 하나. 값 = 출력 포트 넷마다 "high_impedance" | "kvl_fixed"(출력 아닌 넷은 항목 없음).
# 분류 규칙(손): F' = 레일 + (입력 DC 선언이면 입력 포트), W3 목표 넷은 F' 에 넣지 않는다. G_vgs 엣지(MOS gate-source, 저항 양 끝)에서 출력 넷부터
# 너비 우선으로 성분을 걷어 F' 에 닿으면 kvl_fixed, 닿지 않거나 출력 넷이 G_vgs 엣지의 끝점이 아니면 high_impedance.
# oracle: (손) toy 연결에서 위 규칙을 손으로 적용한 기대값(피검 함수 출력으로 기대값을 만들지 않는다, toy 는 이름 없는 연결),
#         (독립) `RunCounters` 증분·`block_version`·소스 문자열 수(`git grep` 과 같은 뜻의 텍스트 수).
# ===========================================================================
import re  # noqa: E402
from pathlib import Path  # noqa: E402

import gmid_engine  # noqa: E402

from .conftest import Oracle, free_currents, node_voltages, run_blocks  # noqa: E402

HI = "high_impedance"
KVL = "kvl_fixed"


def _structure(ctx):
    return dict(ctx.base.column("node", "dc_output_structure"))


def _follower(i="in", o="out", m1="M1", m2="M2", extra_input=False):
    """source follower: m1 nmos (vdd, i, o)(출력에 MOS source writer), m2 nmos (o, vb, gnd)(풀다운, gate 는 외부 바이어스).
    G_vgs 엣지: (i, o), (vb, gnd). extra_input 이면 둘째 입력 포트 in2 -- m3 nmos (z, in2, gnd) + 저항 R3 (vdd, z): in2 의 성분은 레일에 닿는다."""
    net = [mos(m1, "nmos", "vdd", i, o), mos(m2, "nmos", o, "vb", "gnd")]
    ports = {i: ("input", "x"), o: ("output", "y")}
    passives = ()
    if extra_input:
        net.append(mos("M3", "nmos", "z", "in2", "gnd"))
        ports["in2"] = ("input", "x")
        passives = [two("R3", "resistor", "vdd", "z")]
    return topo("os_follower", net, ports, passives=passives, bias=["vb"])


# ---------------------------------------------------------------- OS (a)~(k)

def test_it2b_os_a_drain_only_output_is_high_impedance(tmp_path, toy_access):
    """oracle 대조: (손) OS (a). 출력 out 은 M1·M2 의 드레인에만 닿는다 -> G_vgs 엣지 끝점이 아니다 -> high_impedance. 항목은 출력 넷 하나뿐."""
    ctx = build_ctx(tmp_path, circuit_cs_pmos_load(), toy_access)[2]
    assert _structure(ctx) == {"out": HI}


def test_it2b_os_b_follower_output_without_fixed_end_is_high_impedance(tmp_path, toy_access):
    """oracle 대조: (손) OS (b). follower(M1 source = out): G_vgs 성분 {in, out}, 레일·선언 입력 DC 없음 -> F' 에 닿지 않음 -> high_impedance."""
    ctx = build_ctx(tmp_path, _follower(), toy_access)[2]
    assert _structure(ctx) == {"out": HI}


def test_it2b_os_c_resistor_load_to_rail_is_kvl_fixed(tmp_path, toy_access):
    """oracle 대조: (손) OS (c). 차동 입력 단일 출력: 부하 저항 R1 이 out 과 vdd 를 잇는다 -> 저항 엣지로 레일에 닿음 -> kvl_fixed.
    o2 는 출력 포트가 아니므로 항목이 없다."""
    doc = topo("os_diffres", [mos("M1", "nmos", "out", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"),
                              mos("M5", "nmos", "t", "vb", "gnd")],
               {"inp": ("input", "differential_input_p"), "inn": ("input", "differential_input_n"), "out": ("output", "y")},   # [IT-1 DEC-106]
               passives=[two("R1", "resistor", "vdd", "out"), two("R2", "resistor", "vdd", "o2")], bias=["vb"])
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    assert _structure(ctx) == {"out": KVL}


def test_it2b_os_d_w3_output_without_fixed_end_is_high_impedance(tmp_path, toy_access):
    """oracle 대조: (손) OS (d). 출력 out 이 W3 목표(0.9 V) -- 핀을 뺀 성분 {in, out} 에 F' 없음 -> high_impedance
    (v1.12.1 의 값 `w3_target` 이 나오면 red)."""
    ctx = build_ctx(tmp_path, _follower(), toy_access, node_targets=(("out", 0.9),))[2]
    assert _structure(ctx) == {"out": HI}
    assert "w3_target" not in _structure(ctx).values()


def _diode_load():
    """M1 diode nmos (out, out, gnd) + M2 nmos (out, in, gnd) + 이상 전류원 I1 (vdd -> out). G_vgs 엣지: (out, gnd), (in, gnd)."""
    return topo("os_diode", [mos("M1", "nmos", "out", "out", "gnd"), mos("M2", "nmos", "out", "in", "gnd")],
                {"in": ("input", "x"), "out": ("output", "y")}, sources=[two("I1", "current_source", "vdd", "out")])


def _rail_gate_source_out():
    """M1 nmos (vdd, vdd, out): gate = 레일, source = out. M2 nmos (out, in, gnd). G_vgs 엣지: (vdd, out), (in, gnd)."""
    return topo("os_railgate", [mos("M1", "nmos", "vdd", "vdd", "out"), mos("M2", "nmos", "out", "in", "gnd")],
                {"in": ("input", "x"), "out": ("output", "y")})


@pytest.mark.parametrize("make", [_diode_load, _rail_gate_source_out], ids=["diode_load", "gate_at_rail_source_out"])
def test_it2b_os_e_w3_output_on_hard_path_is_kvl_fixed(tmp_path, toy_access, make):
    """oracle 대조: (손) OS (e). W3 목표 출력이 MOS 엣지로 레일에 닿는다(diode 부하의 source = gnd, 또는 gate = vdd·source = out) ->
    G_vgs 걷기가 레일(F')에 닿음 -> kvl_fixed. W3 출력을 일괄 고임피던스로 두면 red(O-64 경우 1)."""
    ctx = build_ctx(tmp_path, make(), toy_access, node_targets=(("out", 0.9),))[2]
    assert _structure(ctx) == {"out": KVL}


def test_it2b_os_f_other_w3_node_in_component_is_not_a_fixed_end(tmp_path, toy_access):
    """oracle 대조: (손) OS (f). 출력 성분 {in, out} 에 출력 아닌 W3 목표 노드(in = 0.9 V)만 있고 레일·선언 입력 DC 없음 ->
    W3 목표 넷은 F' 가 아니다 -> high_impedance (그 W3 를 F 로 세면 kvl_fixed -- red)."""
    ctx = build_ctx(tmp_path, _follower(), toy_access, node_targets=(("in", 0.9),))[2]
    assert _structure(ctx) == {"out": HI}


def test_it2b_os_g_declared_input_dc_reaches_output_through_gate_source(tmp_path, toy_access):
    """oracle 대조: (손) OS (g). 같은 연결에서 입력 DC 선언이면 in 이 F' -> M1 gate-source 엣지로 out 에 닿음 -> kvl_fixed,
    미선언이면 high_impedance."""
    (tmp_path / "decl").mkdir()
    (tmp_path / "undecl").mkdir()
    declared = build_ctx(tmp_path / "decl", _follower(), toy_access, input_dc_v=0.7)[2]
    assert _structure(declared) == {"out": KVL}
    undeclared = build_ctx(tmp_path / "undecl", _follower(), toy_access)[2]
    assert _structure(undeclared) == {"out": HI}


@pytest.mark.parametrize("input_dc, expected", [(None, HI), (0.7, KVL)], ids=["undeclared", "declared"])
def test_it2b_os_h_swapped_names_give_same_values(tmp_path, toy_access, input_dc, expected):
    """oracle 대조: (손) OS (h). 넷 in <-> out 과 소자 M1 <-> M2 이름을 맞바꾼 toy(입력 포트 이름이 "out", 출력 포트 이름이 "in") 도
    연결이 같으므로 같은 값. 출력 포트는 이제 "in" 이다."""
    kw = {} if input_dc is None else {"input_dc_v": input_dc}
    ctx = build_ctx(tmp_path, _follower(i="out", o="in", m1="M2", m2="M1"), toy_access, **kw)[2]
    assert _structure(ctx) == {"in": expected}


def _follower_theta(ctx, vgs2):
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 0.9, 0.5),
          ("ln_idu", "M2"): Oracle.ln_idu("nmos", vgs2, 0.6, 0.0)}
    th.update({(k, key): 0.7 for k, key in kschema(ctx).components if k == "y"})
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5}))
    assert set(th) == set(kschema(ctx).components)
    return th


def test_it2b_os_i_value_is_theta_independent_and_not_recomputed(tmp_path, toy_access):
    """oracle 대조: (독립) OS (i), G-10. 서로 다른 θ 둘(M2 의 vgs 0.55 / 0.65)로 커널 평가한 스냅샷의 이 필드 값과 쓰기 계획 블록의 block_version 이
    base 와 같고(같음·다름만 본다), 평가 때문에 `dc_writer_plan` computes 가 늘지 않는다(RunCounters 증분 0)."""
    ctx = build_ctx(tmp_path, _follower(), toy_access)[2]
    before_structure = _structure(ctx)
    assert before_structure == {"out": HI}
    version = ctx.base.block_version("dc_writer_plan")
    computes0 = block_row(ctx.counters, dc_writer_plan.name)
    for vgs2 in (0.55, 0.65):
        snap = run_blocks(ctx, _follower_theta(ctx, vgs2), upto="columns")
        assert dict(snap.column("node", "dc_output_structure")) == before_structure
        assert snap.block_version("dc_writer_plan") == version
    assert row_delta(block_row(ctx.counters, dc_writer_plan.name), computes0)[4] == 0


# [IT-1 A-76 폐기 기록] 옛 test_it2b_os_k_no_same_dc_edge_between_input_ports 는 폐기(A-42 이행, retired_tests): 입력 DC 미선언 두 입력 포트의 전제
# (role 없는 두 입력, 따로 선 성분)가 DEC-106 입력 점 규칙(차동쌍 아닌 입력 둘은 input_cm_undefined 정지)으로 바뀌어 성립하지 않는다.


# ---------------------------------------------------------------- OS (j) 둘째 생산자 부재 (텍스트 수 -- git grep 과 같은 뜻)

ENGINE = Path(gmid_engine.__file__).resolve().parent


def _count(rel, pattern):
    path = ENGINE / rel
    return len(re.findall(pattern, path.read_text(encoding="utf-8"))) if path.exists() else 0


def test_it2b_os_j_single_writer_site_and_no_second_producer():
    """oracle 대조: (독립) OS (j). 권한표 행은 `sizing/s2_values.py` 의 DC_WRITES 하나(필드 이름 문자열 1회), 쓰기 자리는 `sizing/writer_plan.py`
    (WRITES 에 1회 이상 -- 블록 안 대입은 같은 파일), G_vgs 성분 걷기(`_edges` 호출)는 측정 구성·다듬은 창·front 블록 파일에 0,
    `IcmConfig` 에 `output_structure` 칸 없음."""
    assert _count("sizing/s2_values.py", r'"dc_output_structure"') == 1
    assert _count("sizing/writer_plan.py", r'"dc_output_structure"') >= 1
    for rel in ("metrics/icm_config.py", "sizing/window_refine.py", "metrics/icm_front.py"):
        assert _count(rel, r"\b_edges\b") == 0, rel
    assert _count("metrics/aux_types.py", r"\boutput_structure\b") == 0


# ===========================================================================
# [card 20261104-tb1-theta-class] 종속 멤버 선택 -- θ 분류 순위 + 구조 위치(이름 키 없음) (interface §2·§4 T-T3~T-T7·T-T9·T-T10)
# ===========================================================================
# 폐기: 옛 [U4] DEC-95 (3) 순서 힌트 test 일곱 개 + diode 짝 네 개 + 빈 힌트 동일·트리 전용 소자 무변화·이름 전단사 test 는 힌트 입력이 없어져
# 지웠다(retired_tests, 이유 O-187·O-189·O-194). 이름 동률 기대값은 아래 test_dependent_member_* 가 바뀐 규칙(구조 위치)으로 다시 쓴다.
#
# 규칙(interface §2): kvl_branch 고리 -- B 멤버가 있으면 B 가 종속(B 안: diode -> 대칭 궤도 대표 -> 소스 사슬 하류 -> 정준 위치, 앞이 먼저 종속),
# B 가 없으면 독립 유지 순위 diode -> 뒤 stage -> 정준 위치(앞이 독립), 남는 쪽이 종속. 정준 위치 = device.dc_colour 오름차순(작은 쪽이 앞).
# 그 밖 비트리 관계(평행): 독립 유지 diode -> R13 S·뒤 stage -> 대칭 궤도 대표 -> 정준 위치.
# oracle: (손) 합성 toy 의 연결에서 위 규칙을 손으로 적용(분류는 theta_class 열에 test 가 직접 넣고, dc_colour 는 스냅샷 입력 열에서 읽는다),
# (식) interface §2 ratify 표, (비교) 이름 전단사 쌍. 피검 함수 출력으로 기대값을 만들지 않는다.

import json as _json  # noqa: E402

from gmid_engine.graph import S1V_KEY, S1Graph, build_s1v, load_structure_facts, s1_symmetry, structure_rule_fp  # noqa: E402
from gmid_engine.sizing import DcInputs  # noqa: E402            (ThetaClass·theta_class 는 새 이름이라 호출 시점에 _SZ 로 읽는다 -- base 에서 이 파일의 기존 test 를 깨지 않는다)

from .conftest import SUPPLIES, tamper  # noqa: E402


def _tri(a="A", b="B", c="C", extra_mirror=False):
    """KVL 삼각형 toy: A diode nmos(n1, n1, gnd)(I1: vdd -> n1), B nmos(o1, n2, n1), C nmos(o2, n2, gnd), 부하 P1(o1, pb1, vdd)·P2(o2, pb2, vdd).
    G_vgs 엣지: A (n1, F), B (n2, n1), C (n2, F), P1, P2 -> 삼각형 하나 = 종속 1. B 의 source 넷 n1 의 전압은 A 의 VGS 로 정해진다(소스 사슬 하류).
    extra_mirror 면 A 와 같은 (gate n1, source gnd)의 거울 A2(o3, n1, gnd)(평행 짝)와 부하 P3 을 더한다."""
    net = [mos(a, "nmos", "n1", "n1", "gnd"), mos(b, "nmos", "o1", "n2", "n1"), mos(c, "nmos", "o2", "n2", "gnd"),
           mos("P1", "pmos", "o1", "pb1", "vdd"), mos("P2", "pmos", "o2", "pb2", "vdd")]
    ports = {"n2": ("input", "single_ended_input"), "o1": ("output", "y"), "o2": ("output", "y")}
    bias = ["pb1", "pb2"]
    if extra_mirror:
        net += [mos("A2", "nmos", "o3", "n1", "gnd"), mos("P3", "pmos", "o3", "pb3", "vdd")]
        ports["o3"] = ("output", "y")
        bias.append("pb3")
    return topo("tb1_tri%s" % ("_m" if extra_mirror else ""), net, ports, sources=[two("I1", "current_source", "vdd", "n1")], bias=bias)


def _inv(mn="Mn", mp="Mp"):
    """인버터 toy: mn nmos(out, x, gnd)·mp pmos(out, x, vdd). G_vgs 엣지 (x, gnd)·(x, vdd) -- 레일 둘이 한 점 F 라 고리 하나, 두 소자 source 는 레일(사슬 아님)."""
    return topo("tb1_inv", [mos(mn, "nmos", "out", "x", "gnd"), mos(mp, "pmos", "out", "x", "vdd")],
                {"x": ("input", "single_ended_input"), "out": ("output", "single_ended_output")})


def _sym4(a="MA", b="MB", c="MC", d="MD"):
    """고리 밖 평행 쌍 둘(대칭 궤도 둘): (a, b) nmos gate pb(입력)·(c, d) pmos gate pc(바이어스). 각 쌍은 (gate, source) 가 같은 평행 관계."""
    return topo("tb1_sym", [mos(a, "nmos", "oa", "pb", "gnd"), mos(b, "nmos", "ob", "pb", "gnd"),
                            mos(c, "pmos", "oa", "pc", "vdd"), mos(d, "pmos", "ob", "pc", "vdd")],
                {"pb": ("input", "x"), "oa": ("output", "y"), "ob": ("output", "y")}, bias=["pc"])


def _co(snap):
    return dict(snap.column("device", "dc_coord"))


def _with_classes(tmp_path, doc, access, kinds, **kw):
    """build_ctx 뒤 theta_class 열의 kinds 항목을 덮어 쓰고(writer = theta_class 블록) 쓰기 계획을 다시 돌린 스냅샷, 그리고 그 ctx.
    kinds 에 없는 소자는 그대로 둔다. 쓰기 계획 인자는 build_ctx 와 같다(목표 넷 없음, 입력 DC 미선언)."""
    ctx = build_ctx(tmp_path, doc, access, **kw)[2]
    snap = tamper(ctx.base, _SZ.theta_class.name, "device", "theta_class", {m: _SZ.ThetaClass(k) for m, k in kinds.items()})
    return dc_writer_plan(snap, (), False, **run_of(ctx)), ctx          # 입력 DC 미선언·목표 넷 없음 = build_ctx 기본 입력과 같다


def _deps(snap, among):
    return sorted(m for m, c in _co(snap).items() if c.role == "dependent" and m in among)


def _colour(ctx, m):
    return dict(ctx.base.column("device", "dc_colour"))[m]


# ---------------------------------------------------------------- T-T3: 고리 안 B 순위

def test_dependent_member_in_loop_b_diode_first(tmp_path, toy_access):
    """oracle (손): 삼각형 {A diode, B, C} 셋 다 B -> B 안 순위 첫째 diode 가 종속(A). 나머지 B·C 는 트리(writer)."""
    snap, _ = _with_classes(tmp_path, _tri(), toy_access, {"A": "B", "B": "B", "C": "B"})
    assert _deps(snap, {"A", "B", "C"}) == ["A"]
    assert _co(snap)["B"].role == "writer" and _co(snap)["C"].role == "writer"


def test_dependent_member_in_loop_b_source_chain_downstream(tmp_path, toy_access):
    """oracle (손): A 는 F(B 아님) -> 후보 {B, C}. diode 없음, 대칭 궤도 없음(B·C 는 연결이 달라 같은 궤도가 아니다). B 의 source 넷 n1 전압이
    다른 고리 멤버 A 의 VGS 로 정해지고 C 의 source 는 레일 -> B 가 소스 사슬 하류 = 종속."""
    snap, _ = _with_classes(tmp_path, _tri(), toy_access, {"A": "F", "B": "B", "C": "B"})
    assert _deps(snap, {"A", "B", "C"}) == ["B"]


def test_dependent_member_in_loop_b_beats_non_b_regardless_of_position(tmp_path, toy_access):
    """oracle (손): 인버터 고리 {Mn, Mp} 에서 B 인 쪽이 종속 -- 정준 위치(dc_colour)가 어느 쪽이 앞이든. 두 방향 모두."""
    for i, (kb, kn) in enumerate((("Mn", "Mp"), ("Mp", "Mn"))):
        (tmp_path / str(i)).mkdir()
        snap, _ = _with_classes(tmp_path / str(i), _inv(), toy_access, {kb: "B", kn: "F"})
        assert _deps(snap, {"Mn", "Mp"}) == [kb]


def test_dependent_member_in_loop_b_canonical_position_first_is_dependent(tmp_path, toy_access):
    """oracle (손): 인버터 고리 둘 다 B, source 사슬 아님·궤도 아님·diode 아님 -> 정준 위치가 앞(dc_colour 작은 쪽)인 소자가 종속."""
    snap, ctx = _with_classes(tmp_path, _inv(), toy_access, {"Mn": "B", "Mp": "B"})
    first = min(("Mn", "Mp"), key=lambda m: _colour(ctx, m))
    assert _deps(snap, {"Mn", "Mp"}) == [first]


def _symloop(a1="A1", a2="A2", b1="B1", b2="B2"):
    """대칭 4소자 고리: diode a1·a2 와 분기 b1·b2 가 같은 게이트 n2 를 공유해 G_vgs 4-사이클 F-n1a-n2-n1b-F 하나. 부하 P1·P2 는 같은 gate pb1 (평행 짝 하나)."""
    return topo("tb1_sym_loop",
                [mos(a1, "nmos", "n1a", "n1a", "gnd"), mos(a2, "nmos", "n1b", "n1b", "gnd"),
                 mos(b1, "nmos", "o1", "n2", "n1a"), mos(b2, "nmos", "o2", "n2", "n1b"),
                 mos("P1", "pmos", "o1", "pb1", "vdd"), mos("P2", "pmos", "o2", "pb1", "vdd")],
                {"n2": ("input", "single_ended_input"), "o1": ("output", "y"), "o2": ("output", "y")},
                sources=[two("I1", "current_source", "vdd", "n1a"), two("I2", "current_source", "vdd", "n1b")], bias=["pb1"])


def test_dependent_member_symmetric_orbit_representative(tmp_path, toy_access):
    """oracle (손): 대칭 4소자 고리. A 둘은 F, B 둘은 B -> 후보 {B1, B2} 는 같은 궤도(연결 대칭). 궤도 대표 = 그 궤도의 dc_colour 최소 멤버 = 종속."""
    doc = _symloop()
    snap, ctx = _with_classes(tmp_path, doc, toy_access, {"A1": "F", "A2": "F", "B1": "B", "B2": "B"})
    rep = min(("B1", "B2"), key=lambda m: _colour(ctx, m))
    assert _deps(snap, {"A1", "A2", "B1", "B2"}) == [rep]


# ---------------------------------------------------------------- T-T4: B 없는 고리 -- 독립 유지 순위

@pytest.mark.parametrize("kind", ["F", "S"])
def test_dependent_member_no_b_diode_stays_independent(tmp_path, toy_access, kind):
    """oracle (손): 고리 {A diode, B, C} 에 B 가 없으면 독립 유지 순위 diode 가 먼저 남는다(A 는 writer). 남은 {B, C} 중 정준 위치가 뒤(dc_colour
    큰 쪽)가 종속 -- 앞이 독립. (B 있는 고리와 방향이 반대)"""
    snap, ctx = _with_classes(tmp_path, _tri(), toy_access, {"A": kind, "B": kind, "C": kind})
    assert _co(snap)["A"].role == "writer"
    last = max(("B", "C"), key=lambda m: _colour(ctx, m))
    assert _deps(snap, {"A", "B", "C"}) == [last]


@pytest.mark.parametrize("kind", ["F", "S"])
def test_dependent_member_no_b_canonical_position_last_is_dependent(tmp_path, toy_access, kind):
    """oracle (손): 인버터 고리 둘 다 B 아님, diode 없음 -> 정준 위치가 앞인 쪽이 독립, 뒤(dc_colour 큰 쪽)가 종속."""
    snap, ctx = _with_classes(tmp_path, _inv(), toy_access, {"Mn": kind, "Mp": kind})
    last = max(("Mn", "Mp"), key=lambda m: _colour(ctx, m))
    assert _deps(snap, {"Mn", "Mp"}) == [last]


# ---------------------------------------------------------------- T-T5: 평행 관계와 고리가 같은 diode 를 가질 때

def test_dependent_member_parallel_keeps_diode_and_loop_chooses_among_rest(tmp_path, toy_access):
    """oracle (손): A(diode)와 A2 는 같은 (gate n1, source 레일) 평행 -> 평행에서 diode A 가 독립 유지, A2 가 종속(parallel_vgs, 짝 A).
    삼각형 {A, B, C} 의 고리 종속은 A 가 이미 독립으로 묶여 후보가 아니므로 남은 B 멤버 {B, C} 중 소스 사슬 하류 B. 이 toy 는 base 에서 통과할 수 있다(green 유지 가능)."""
    snap, _ = _with_classes(tmp_path, _tri(extra_mirror=True), toy_access,
                            {m: "B" for m in ("A", "B", "C", "A2", "P1", "P2", "P3")})
    co = _co(snap)
    assert co["A"].role == "writer" and co["A2"].role == "dependent" and co["A2"].partner == "A"
    assert co["B"].role == "dependent" and co["C"].role == "writer"


# ---------------------------------------------------------------- T-T6: 이름 전단사 metamorphic (고리 안·고리 밖)

def _dep_by_rename(tmp_path, access, make, names_a, names_b, among_a):
    """같은 연결에 이름만 다른 두 입력 -> 종속 소자 집합. 반환 ({σ(a 의 종속)}, {b 의 종속}), σ = zip(names_a, names_b)."""
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    ca = build_ctx(tmp_path / "a", make(*names_a), access)[2]
    cb = build_ctx(tmp_path / "b", make(*names_b), access)[2]
    sigma = dict(zip(names_a, names_b))
    da = {sigma[m] for m, c in _co(ca.base).items() if c.role == "dependent" and m in among_a}
    db = {m for m, c in _co(cb.base).items() if c.role == "dependent" and m in set(names_b)}
    return da, db


@pytest.mark.parametrize("make,names_a,names_b", [
    (_inv, ("Mn", "Mp"), ("Zn", "Ap")),                                     # 이름 순서가 뒤집힌다: Mn < Mp  ->  Zn > Ap
    (_tri, ("A", "B", "C"), ("A", "C", "B")),                               # B <-> C 이름 맞바꿈(B 의 연결이 'C' 라는 이름을 받는다)
    (_symloop, ("A1", "A2", "B1", "B2"), ("Z1", "Z2", "Z4", "Z3")),         # 대칭 고리: 분기 둘의 이름 순서 맞바꿈
    (_symloop, ("A1", "A2", "B1", "B2"), ("Q2", "Q1", "B2", "B1")),
], ids=["loop_inverter", "loop_triangle", "loop_symmetric_a", "loop_symmetric_b"])
def test_dependent_member_name_bijection_in_loop(tmp_path, toy_access, make, names_a, names_b):
    """oracle (비교): 고리 안 -- 소자 이름 전단사 뒤 종속 멤버 = σ(원래 종속 멤버). 어느 키에도 이름이 없다(base 는 이름 키로 갈려 red)."""
    da, db = _dep_by_rename(tmp_path, toy_access, make, names_a, names_b, set(names_a))
    assert len(db) == 1 and da == db


def test_dependent_member_name_bijection_outside_loop(tmp_path, toy_access):
    """oracle (비교): 고리 밖(평행 쌍 둘) -- 이름 순서를 뒤집은 전단사 뒤에도 각 쌍의 종속 멤버가 σ(원래 종속). base 는 이름순 동률 해소로 red."""
    names_a, names_b = ("MA", "MB", "MC", "MD"), ("Z1", "A1", "MC", "MD")
    da, db = _dep_by_rename(tmp_path, toy_access, _sym4, names_a, names_b, set(names_a))
    assert len(db) == 2 and da == db


# ---------------------------------------------------------------- T-T7: ratify (dependent_member)

def _ctx_with_facts(tmp_path, doc, access, rows):
    """S1 -> 사실 적재 -> S1v(structure=) -> 커널 컨텍스트. 정지(StructureUnresolvedError)는 어느 단계에서 나도 호출자에게 전파된다."""
    donors, counters = open_run()
    run = dict(donors=donors, counters=counters)
    s1 = build_s1(load_doc(tmp_path, doc), dict(SUPPLIES), **run)
    path = tmp_path / "facts.structure.json"
    path.write_text(_json.dumps({"schema_version": "1", "topology_hash": s1.key.topology_fp, "rule_hash": structure_rule_fp(),
                                 "facts": [{"concept": "dependent_member", "subject": _json.dumps(sorted(s)), "value": v,
                                            "status": "ratified", "evidence": {"rule": "hand", "nets": []}, "approval_id": "T-T7"}
                                           for s, v in rows]}), encoding="utf-8")
    facts = load_structure_facts(str(path), s1.key.topology_fp, structure_rule_fp())
    graph = build_s1v(s1, None, structure=facts, count_budget=10 ** 6, stop_on_unsupported=False, **run)
    return build_kernel_context(graph, DcInputs(tuple(sorted(SUPPLIES.items()))), access, **run)


def _stop_reason(tmp_path, doc, access, rows):
    with pytest.raises(StructureUnresolvedError) as ei:
        _ctx_with_facts(tmp_path, doc, access, rows)
    return detail(ei.value)["reason"]


def test_dependent_member_ratify_agreeing_fact_is_noop_and_disagreeing_stops(tmp_path, toy_access):
    """oracle (식): interface §2 ratify 표 -- 고리 사실 = 유도 결과 -> 무동작(사실 없음과 같은 좌표), 고리 사실 != 유도 결과 -> 정지 structure_fact_mismatch.
    인버터 고리 {Mn, Mp} 의 사실 둘(value Mn / value Mp) 가운데 정확히 하나가 유도 결과와 같아 무동작이고 다른 하나는 정지한다."""
    (tmp_path / "plain").mkdir()
    plain = build_ctx(tmp_path / "plain", _inv(), toy_access)[2]
    derived = [m for m, c in _co(plain.base).items() if c.role == "dependent" and m in ("Mn", "Mp")]
    assert len(derived) == 1
    other = "Mp" if derived[0] == "Mn" else "Mn"
    (tmp_path / "ok").mkdir()
    (tmp_path / "bad").mkdir()
    ok = _ctx_with_facts(tmp_path / "ok", _inv(), toy_access, [(("Mn", "Mp"), derived[0])])
    assert _co(ok.base) == _co(plain.base)
    assert _stop_reason(tmp_path / "bad", _inv(), toy_access, [(("Mn", "Mp"), other)]) == "structure_fact_mismatch"


@pytest.mark.parametrize("value", ["MA", "MB"])
def test_dependent_member_ratify_fact_outside_loop_overrides(tmp_path, toy_access, value):
    """oracle (식): 고리 밖 사실(평행 쌍 {MA, MB}) -> 그 멤버로 override. value 가 어느 쪽이든 그 소자가 종속(parallel_vgs, 짝 = 다른 쪽)."""
    ctx = _ctx_with_facts(tmp_path, _sym4(), toy_access, [(("MA", "MB"), value)])
    other = "MB" if value == "MA" else "MA"
    assert _co(ctx.base)[value] == DeviceCoord("dependent", "parallel_vgs", other)
    assert _co(ctx.base)[other].role == "writer"


def test_dependent_member_ratify_value_not_a_member_stops(tmp_path, toy_access):
    """oracle (식): value 가 멤버가 아니면 정지 structure_fact_mismatch (실제 평행 관계 {MA, MB} 에 멤버 아닌 MC)."""
    assert _stop_reason(tmp_path, _sym4(), toy_access, [(("MA", "MB"), "MC")]) == "structure_fact_mismatch"


def test_dependent_member_ratify_orphan_when_no_such_relation(tmp_path, toy_access):
    """oracle (식): 그 관계가 없는 사실(MA 와 MC 는 어떤 평행·고리 관계도 아님) -> structure_fact_orphan. 정지 예외 또는 S1v finding 으로 나타난다(둘 중 하나)."""
    try:
        ctx = _ctx_with_facts(tmp_path, _sym4(), toy_access, [(("MA", "MC"), "MA")])
    except StructureUnresolvedError as e:
        assert detail(e)["reason"] == "structure_fact_orphan"
        return
    codes = [f.code for f in ctx.base.value("graph", S1V_KEY, "findings")]
    assert "structure_fact_orphan" in codes


# ---------------------------------------------------------------- T-T9: W4 뿌리 동률 정지

def _two_roots():
    """W4 뿌리 후보가 둘인 toy: 입력 하나 in 이 M1·M3 gate, 출력 o1·o2 가 각각 G_vgs 밖(drain 만) -> 뿌리 후보 둘(o1, o2)."""
    return topo("tb1_two_roots",
                [mos("M1", "nmos", "o1", "in", "gnd"), mos("M2", "pmos", "o1", "pb1", "vdd"),
                 mos("M3", "nmos", "o2", "in", "gnd"), mos("M4", "pmos", "o2", "pb2", "vdd")],
                {"in": ("input", "single_ended_input"), "o1": ("output", "y"), "o2": ("output", "y")}, bias=["pb1", "pb2"])


def test_w4_root_tie_stops_with_dc_colour_not_unique(tmp_path, toy_access):
    """oracle (식): interface §2 W4 뿌리 -- 최소 (구조 색, 정준 위치) 후보가 둘 이상이면 정지, rule_branch dc_colour_not_unique.
    주입: 두 W4 후보 넷 o1·o2 의 node.dc_colour 를 같게(writer = 대칭 블록) 한 S1 로 커널 컨텍스트를 짓는다."""
    donors, counters = open_run()
    run = dict(donors=donors, counters=counters)
    s1 = build_s1(load_doc(tmp_path, _two_roots()), dict(SUPPLIES), **run)
    col = dict(s1.snapshot.column("node", "dc_colour"))
    snap = tamper(s1.snapshot, s1_symmetry.name, "node", "dc_colour", {"o2": col["o1"]})
    with pytest.raises(StructureUnresolvedError) as ei:
        build_kernel_context(S1Graph(s1.key, snap), DcInputs(tuple(sorted(SUPPLIES.items()))), toy_access, **run)
    d = detail(ei.value)
    assert d["rule_branch"] == "dc_colour_not_unique"


def test_w4_root_tie_no_decision_recorded_when_colours_unique(tmp_path, toy_access):
    """oracle (식): dc_colour 가 정점마다 유일한 정상 입력은 W4 뿌리를 정지 없이 고르고 dc_tie_breaks 에 decision w4_root 가 없다."""
    ctx = build_ctx(tmp_path, _two_roots(), toy_access)[2]
    assert "w4_root" not in {t.decision for t in plan(ctx)[2]}
    nw = plan(ctx)[0]
    assert {nw["o1"].tier, nw["o2"].tier} == {"W4"}


def test_w4_root_tie_vocabulary_is_gone():
    """oracle (독립): 어휘 `w4_root` 와 상수 TIE_ROOT 가 sizing 에 없다(따옴표 친 문자열 수 0)."""
    import gmid_engine.sizing as sz
    assert not hasattr(sz, "TIE_" + "ROOT")
    quoted = re.compile(r"""["']w4_root["']""")
    hits = [p.name for p in sorted((ENGINE / "sizing").rglob("*.py")) if quoted.search(p.read_text(encoding="utf-8"))]
    assert hits == []


# ---------------------------------------------------------------- T-T10: 순서 힌트 인자 폐기

def test_dependent_member_removed_hint_arguments_and_names(tmp_path, toy_access):
    """oracle (식): interface §3 -- 순서 힌트 인자를 주면 TypeError, 옛 이름들은 sizing 에 없다. (이름은 단어 grep 0 을 위해 이어 붙여 쓴다)"""
    import gmid_engine.sizing as sz
    donors, counters = open_run()
    s1 = build_s1(load_doc(tmp_path, _inv()), dict(SUPPLIES), donors=donors, counters=counters)
    with pytest.raises(TypeError):
        build_kernel_context(s1, DcInputs(tuple(sorted(SUPPLIES.items()))), toy_access, donors=donors, counters=counters,
                             **{"order" + "_hints": None})
    for name in ("Order" + "Hints", "NO_ORDER_" + "HINTS", "TIE_" + "ROOT"):
        assert not hasattr(sz, name), name


def test_dependent_member_without_views_still_builds_and_picks_one(tmp_path, toy_access):
    """oracle (손): S1v(views)가 없는 S1 -- stage 순위 경로는 건너뛰고(정지·예외 없음) 고리 종속은 정확히 하나."""
    ctx = build_ctx(tmp_path, _inv(), toy_access)[2]
    assert len([m for m, c in _co(ctx.base).items() if c.role == "dependent"]) == 1
