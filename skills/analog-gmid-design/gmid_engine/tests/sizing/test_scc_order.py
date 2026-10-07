"""`dc_scc_order(snapshot)` -- CONTRACT 4.3: 읽기 의존 그래프와 SCC(Tarjan) 풀이 순서, `dc_column_nbrs`.

기대값: 이 파일의 `deps_of` 가 4.3 의존 규칙을 스냅샷의 `node.dc_writer`(계획 결과 -- 이 판에서는 writer_plan 을 판정하지
않고 입력으로 쓴다)·`device.pins`·`device.bulk` 에서 따로 계산하고, 독립 SCC(Kosaraju)로 분할·순서를 확인한다.
"""
import pytest

from gmid_engine.sizing import DC_KEY, ColumnNeighbor, SccEntry

from .conftest import NINE, build_ctx, circuit_cs_pmos_load, circuit_cs_res, library_ctx, mos, topo, two

FIXED_RELS = {"rail", "declared_target", "input_dc"}


def _pins(snap):
    out = {}
    for name, pins in snap.column("device", "pins"):
        if snap.value("device", name, "element_class") == "mos":
            p = dict(pins)
            p["b"] = snap.value("device", name, "bulk").net
            out[name] = p
    return out


def deps_of(snap):
    writers = dict(snap.column("node", "dc_writer"))
    pins = _pins(snap)
    fixed = {n for n, w in writers.items() if w.relation in FIXED_RELS}
    # 입력 묶음(input_tie 로 이어진 노드) -- free_window 뿌리면 묶음 전원
    tie = {}
    for n, w in writers.items():
        if w.relation == "input_tie":
            tie.setdefault(w.known, set()).add(n)
            tie.setdefault(n, set()).add(w.known)

    def group(n):
        seen, stack = {n}, [n]
        while stack:
            for m in tie.get(stack.pop(), ()):
                if m not in seen:
                    seen.add(m)
                    stack.append(m)
        return seen

    deps = {}
    for n, w in writers.items():
        if n in fixed:
            continue
        if w.relation == "vgs_gate":
            p = pins[w.element]
            d = {p["s"], p["d"], p["b"], w.known}
        elif w.relation == "vgs_source":
            p = pins[w.element]
            d = {w.known, p["d"], p["b"], n}
        elif w.relation in ("resistor_drop", "input_tie"):
            d = {w.known}
        elif w.relation == "free_window":
            d = set()
            members = group(n)
            for p in pins.values():
                if p["d"] in members:
                    d.add(p["s"])
                if p["s"] in members:
                    d.add(p["d"])
        else:
            raise AssertionError("unknown relation %r" % (w.relation,))
        deps[n] = {x for x in d if x not in fixed}
    return deps, writers, pins


def sccs(deps):
    """Kosaraju -- {노드: 성분 id}."""
    order, seen = [], set()
    for s in sorted(deps):
        if s in seen:
            continue
        stack = [(s, iter(sorted(deps[s])))]
        seen.add(s)
        while stack:
            v, it = stack[-1]
            nxt = next((u for u in it if u not in seen), None)
            if nxt is None:
                order.append(v)
                stack.pop()
            else:
                seen.add(nxt)
                stack.append((nxt, iter(sorted(deps[nxt]))))
    rev = {v: set() for v in deps}
    for v, ds in deps.items():
        for u in ds:
            rev[u].add(v)
    comp = {}
    for s in reversed(order):
        if s in comp:
            continue
        cid = len(set(comp.values()))
        stack = [s]
        comp[s] = cid
        while stack:
            v = stack.pop()
            for u in rev[v]:
                if u not in comp:
                    comp[u] = cid
                    stack.append(u)
    return comp


def check_order(snap):
    entries = snap.value("graph", DC_KEY, "dc_scc_order")
    deps, writers, pins = deps_of(snap)
    comp = sccs(deps)
    assert all(isinstance(e, SccEntry) for e in entries)
    assert [e.index for e in entries] == list(range(len(entries)))
    flat = [n for e in entries for n in e.nodes]
    assert sorted(flat) == sorted(deps)                       # 고정 relation 밖 노드 전부, 한 번씩
    pos = {}
    for e in entries:
        assert len({comp[n] for n in e.nodes}) == 1           # 한 SCC
        for n in e.nodes:
            pos[n] = e.index
        members = set(e.nodes)
        assert len(members) == sum(1 for v in comp.values() if v == comp[e.nodes[0]])   # SCC 전체
        assert list(e.nodes) == sorted(e.nodes, key=lambda n: writers[n].order)
        self_dep = any(n in deps[n] for n in e.nodes)
        assert e.cyclic == (len(e.nodes) > 1 or self_dep)
        exp_dev = sorted(m for m, p in pins.items() if {p["d"], p["g"], p["s"]} & members)
        assert list(e.devices) == exp_dev
    for n, ds in deps.items():
        for u in ds:
            assert pos[u] <= pos[n], "의존 %s 가 %s 보다 뒤" % (u, n)
    return entries


def test_circuit_c(ctx_c):
    entries = check_order(ctx_c[2].base)
    # 손계산: out(W4) 은 레일만 읽음 -> 먼저, in·pb 는 out(drain) 을 읽음
    assert entries[0].nodes == ("out",) and not entries[0].cyclic
    assert {e.nodes for e in entries[1:]} == {("in",), ("pb",)}


def test_circuit_a(ctx_a):
    entries = check_order(ctx_a[2].base)
    assert [e.nodes for e in entries] == [("out",), ("in",)]


def test_diode_self_dependency_cyclic(tmp_path, toy_access):
    doc = topo("hand_mirror_scc",
               [mos("M1", "nmos", "nb", "nb", "gnd"), mos("M2", "nmos", "out", "nb", "gnd"),
                mos("M3", "pmos", "out", "in", "vdd")],
               {"in": ("input", "x"), "out": ("output", "y")},
               sources=[two("I1", "current_source", "vdd", "nb")])
    _, _, ctx = build_ctx(tmp_path, doc, toy_access)
    entries = check_order(ctx.base)
    nb = [e for e in entries if "nb" in e.nodes][0]
    assert nb.nodes == ("nb",) and nb.cyclic                  # diode: gate 노드가 자기 drain 을 읽음
    assert nb.devices == ("M1", "M2")


def test_cross_coupled_two_node_scc(tmp_path, toy_access):
    doc = topo("hand_cross",
               [mos("M1", "nmos", "y", "x", "gnd"), mos("M2", "nmos", "x", "y", "gnd"),
                mos("M3", "pmos", "x", "gnd", "vdd"), mos("M4", "pmos", "y", "gnd", "vdd")],
               {"x": ("input", "a"), "y": ("output", "b")})
    _, _, ctx = build_ctx(tmp_path, doc, toy_access)
    entries = check_order(ctx.base)
    cyc = [e for e in entries if len(e.nodes) == 2]
    assert len(cyc) == 1 and set(cyc[0].nodes) == {"x", "y"} and cyc[0].cyclic
    assert cyc[0].devices == ("M1", "M2", "M3", "M4")


@pytest.mark.parametrize("name", NINE)
def test_library_order_valid(name, toy_access):
    ctx = library_ctx(name, toy_access)[5]
    check_order(ctx.base)


def test_column_neighbors_circuit_c(ctx_c):
    nb = dict(ctx_c[2].base.column("node", "dc_column_nbrs"))
    assert set(nb) == {"out"}                                 # 기둥 gnd -M1- out -M2- vdd 의 내부 노드
    (cn,) = nb["out"]
    assert isinstance(cn, ColumnNeighbor)
    assert cn.rails == ("gnd", "vdd")
    assert (cn.pred, cn.succ) == ("gnd", "vdd")
    assert cn.position * 2 == cn.length                       # 가운데


def test_column_neighbors_chain_positions(tmp_path, toy_access):
    """gnd -M1- a -M2- b -M3- vdd: a·b 는 기둥 위치 1/3·2/3, pred/succ 는 이웃 넷."""
    doc = topo("hand_chain",
               [mos("M1", "nmos", "a", "in", "gnd"), mos("M2", "nmos", "b", "vb", "a"),
                mos("M3", "pmos", "b", "pb", "vdd")],
               {"in": ("input", "x"), "b": ("output", "y")})
    _, _, ctx = build_ctx(tmp_path, doc, toy_access)
    nb = {k: v for k, v in ctx.base.column("node", "dc_column_nbrs")}
    assert set(nb) == {"a", "b"}
    (ca,), (cb,) = nb["a"], nb["b"]
    assert (ca.pred, ca.succ, cb.pred, cb.succ) == ("gnd", "b", "a", "vdd")
    assert ca.length == cb.length
    assert ca.position * 3 == ca.length and cb.position * 3 == 2 * cb.length
    check_order(ctx.base)
