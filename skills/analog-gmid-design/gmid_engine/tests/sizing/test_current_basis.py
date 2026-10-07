"""`dc_current_basis(snapshot, declared_sources)` -- CONTRACT 4.2: 원소 단위 KCL 기저.

기대값: 이 파일의 `expected_basis` 가 topology dict 에서 직접 계산한다 -- DC 원소(MOS·저항·이상원, 잎 가지치기 저항 제외),
ends(nmos (d, s), pmos (s, d), 2단자 (t0, t1)), 레일 아닌 넷마다 KCL 행, 정확 유리수 RREF(열 왼쪽부터 pivot, conftest
`rref_free`), pivot 원소 = −(RREF 계수) × (free·고정 원소).
"""
from fractions import Fraction

import pytest

from gmid_engine.core import InfeasibleTargetError, StructureUnresolvedError
from gmid_engine.sizing import DC_KEY, CurrentBasis, CurrentTerm

from .conftest import build_ctx, circuit_cs_pmos_load, circuit_cs_res, detail, mos, topo, two


def leaf_pruned(doc):
    """graph 계약 4.3 잎 가지치기(저항 하나뿐인 레일·포트 아닌 넷) -- 라운드 반복."""
    rails = set(doc["supply_nets"])
    ports = set(doc["ports"])
    edges = {}
    for e in doc["netlist"]:
        edges[e["name"]] = ("mos", (e["drain"], e["source"]))
    for e in doc.get("passive_elements", []):
        if e["kind"] == "resistor":
            edges[e["name"]] = ("res", tuple(e["terminals"]))
    for e in doc.get("ideal_sources", []):
        edges[e["name"]] = ("src", tuple(e["terminals"]))
    pruned = []
    while True:
        deg = {}
        for n, (_, (a, b)) in edges.items():
            deg.setdefault(a, []).append(n)
            deg.setdefault(b, []).append(n)
        leaves = sorted(net for net, els in deg.items()
                        if net not in rails and net not in ports and len(els) == 1 and edges[els[0]][0] == "res")
        if not leaves:
            return sorted(pruned)
        for net in leaves:
            el = deg[net][0]
            if el in edges:
                pruned.append(el)
                del edges[el]


def expected_basis(doc, declared):
    rails = set(doc["supply_nets"])
    pruned = leaf_pruned(doc)
    ends = {}
    kinds = {}
    for e in doc["netlist"]:
        kinds[e["name"]] = e["kind"]
        ends[e["name"]] = (e["drain"], e["source"]) if e["kind"] == "nmos" else (e["source"], e["drain"])
    resistors = []
    for e in doc.get("passive_elements", []):
        if e["kind"] == "resistor" and e["name"] not in pruned:
            ends[e["name"]] = tuple(e["terminals"])
            resistors.append(e["name"])
    sources = {}
    for e in doc.get("ideal_sources", []):
        ends[e["name"]] = tuple(e["terminals"])
        sources[e["name"]] = e["kind"]
    fixed = {n: float(v) for n, v in declared if v is not None and sources.get(n) == "current_source"}
    cols = sorted(n for n in ends if n not in fixed)
    fixed_names = sorted(fixed)
    allcols = cols + fixed_names
    nets = sorted({x for ab in ends.values() for x in ab} - rails)
    rows = []
    for net in nets:
        r = {}
        for n, (f, t) in ends.items():
            if f == net:
                r[n] = r.get(n, 0) + 1
            if t == net:
                r[n] = r.get(n, 0) - 1
        rows.append(r)
    # 고정 열은 오른쪽에 두어 pivot 이 되지 않게 한다(고정 열 pivot 은 = 불일치 행)
    from .conftest import rref_free
    piv, free_all, expr = rref_free(allcols, rows)
    conflict = [c for c in piv if c in fixed]
    free = [c for c in free_all if c not in fixed]
    out_rows = {}
    for n in sorted(ends):
        if n in expr:
            out_rows[n] = {k: v for k, v in expr[n].items()}
        else:
            out_rows[n] = {n: Fraction(1)}
    return {"ends": tuple((n,) + ends[n] for n in sorted(ends)),
            "mos": tuple(sorted(kinds)), "free": tuple(free), "fixed": tuple((n, fixed[n]) for n in fixed_names),
            "rows": out_rows, "pruned": tuple(pruned), "resistors": tuple(sorted(resistors)),
            "conflict": conflict}


def check(basis, exp):
    assert isinstance(basis, CurrentBasis)
    assert basis.ends == exp["ends"]
    assert basis.mos == exp["mos"]
    assert basis.free == exp["free"]
    assert basis.fixed == exp["fixed"]
    assert basis.pruned == exp["pruned"]
    assert basis.resistors == exp["resistors"]
    got = {}
    for name, terms in basis.rows:
        assert all(isinstance(t, CurrentTerm) for t in terms)
        assert all(t.num != 0 for t in terms)                       # 0 계수 생략
        got[name] = {t.source: Fraction(t.num, t.den) for t in terms}
    assert [n for n, _ in basis.rows] == sorted(got)
    assert got == exp["rows"]


def basis_of(ctx):
    return ctx.base.value("graph", DC_KEY, "dc_current_basis")


def mirror(i1_kind="current_source"):
    """B: I1 (vdd -> nb), M1 diode, M2 미러 출력, M3 pmos 부하(gate = 입력 포트)."""
    return topo("hand_mirror",
                [mos("M1", "nmos", "nb", "nb", "gnd"), mos("M2", "nmos", "out", "nb", "gnd"),
                 mos("M3", "pmos", "out", "in", "vdd")],
                {"in": ("input", "x"), "out": ("output", "y")},
                sources=[two("I1", i1_kind, "vdd", "nb")])


def test_circuit_c(tmp_path, toy_access):
    doc = circuit_cs_pmos_load()
    _, _, ctx = build_ctx(tmp_path, doc, toy_access)
    b = basis_of(ctx)
    check(b, expected_basis(doc, ()))
    # 손계산: out 행 M1(+1) − M2(−1 은 pmos to=out) -> pivot M1 = M2
    assert b.ends == (("M1", "out", "gnd"), ("M2", "vdd", "out"))
    assert b.free == ("M2",)
    assert dict(b.rows)["M1"] == (CurrentTerm("M2", 1, 1),)


def test_resistor_orientation_t0_t1(tmp_path, toy_access):
    doc = circuit_cs_res()
    _, _, ctx = build_ctx(tmp_path, doc, toy_access)
    b = basis_of(ctx)
    check(b, expected_basis(doc, ()))
    assert ("R1", "vdd", "out") in b.ends and b.resistors == ("R1",)
    # 손계산: out 행 = M1(+1) + R1(−1) -> pivot M1 = +R1
    assert b.free == ("R1",)
    rows = dict(b.rows)
    assert rows["M1"] == (CurrentTerm("R1", 1, 1),)


def test_resistor_reversed_gives_negative_coefficient(tmp_path, toy_access):
    doc = topo("hand_cs_res_rev", [mos("M1", "nmos", "out", "in", "gnd")],
               {"in": ("input", "x"), "out": ("output", "y")}, passives=[two("R1", "resistor", "out", "vdd")])
    _, _, ctx = build_ctx(tmp_path, doc, toy_access)
    b = basis_of(ctx)
    check(b, expected_basis(doc, ()))
    rows = {n: {t.source: Fraction(t.num, t.den) for t in ts} for n, ts in b.rows}
    assert rows["M1"] == {"R1": Fraction(-1)}           # out 행 = M1(+1) + R1(+1)


def test_mirror_free_source(tmp_path, toy_access):
    doc = mirror()
    _, _, ctx = build_ctx(tmp_path, doc, toy_access)
    b = basis_of(ctx)
    check(b, expected_basis(doc, ()))
    # 손계산: 열 (I1, M1, M2, M3), nb: −I1 + M1, out: M2 − M3 -> pivot I1·M2, free M1·M3
    assert b.free == ("M1", "M3")
    rows = dict(b.rows)
    assert rows["I1"] == (CurrentTerm("M1", 1, 1),)
    # 미러 출력 M2 는 M1 이 아니라 KCL 상 M3 로 정해진다(matching_ratio 는 전류를 강제하지 않음)
    assert rows["M2"] == (CurrentTerm("M3", 1, 1),)


def test_mirror_declared_source_fixed(tmp_path, toy_access):
    doc = mirror()
    _, _, ctx = build_ctx(tmp_path, doc, toy_access, element_values=(("I1", 2e-5),))
    b = basis_of(ctx)
    check(b, expected_basis(doc, (("I1", 2e-5),)))
    assert b.fixed == (("I1", 2e-5),)
    assert b.free == ("M3",)
    assert dict(b.rows)["M1"] == (CurrentTerm("I1", 1, 1),)
    assert dict(b.rows)["I1"] == (CurrentTerm("I1", 1, 1),)


def test_declared_none_source_stays_free(tmp_path, toy_access):
    doc = mirror()
    _, _, ctx = build_ctx(tmp_path, doc, toy_access, element_values=(("I1", None),))
    assert basis_of(ctx).fixed == ()
    check(basis_of(ctx), expected_basis(doc, ()))


def test_pruned_leaf_resistor_and_capacitor_not_dc(tmp_path, toy_access):
    doc = topo("hand_pruned", [mos("M1", "nmos", "out", "in", "gnd")],
               {"in": ("input", "x"), "out": ("output", "y")},
               passives=[two("R1", "resistor", "vdd", "out"), two("R2", "resistor", "out", "leaf"),
                         two("C1", "capacitor", "out", "gnd")])
    _, _, ctx = build_ctx(tmp_path, doc, toy_access)
    b = basis_of(ctx)
    check(b, expected_basis(doc, ()))
    assert b.pruned == ("R2",)
    assert b.resistors == ("R1",)
    assert all(e[0] not in ("R2", "C1") for e in b.ends)


def test_fractional_coefficients_two_sources(tmp_path, toy_access):
    """두 고정 이상원과 MOS 두 개가 한 넷을 나눠 쓰는 경우: n 행 M1 + M2 − I1 − I2 = 0."""
    doc = topo("hand_two_src",
               [mos("M1", "nmos", "n", "in", "gnd"), mos("M2", "nmos", "n", "b2", "gnd")],
               {"in": ("input", "x"), "n": ("output", "y")},
               sources=[two("I1", "current_source", "vdd", "n"), two("I2", "current_source", "vdd", "n")])
    _, _, ctx = build_ctx(tmp_path, doc, toy_access, element_values=(("I1", 1e-5), ("I2", 2e-5)))
    b = basis_of(ctx)
    check(b, expected_basis(doc, (("I1", 1e-5), ("I2", 2e-5))))
    rows = {n: {t.source: Fraction(t.num, t.den) for t in ts} for n, ts in b.rows}
    assert rows["M1"] == {"I1": 1, "I2": 1, "M2": -1}


def test_declared_kcl_conflict(tmp_path, toy_access):
    doc = topo("hand_kcl_conflict",
               [mos("M1", "nmos", "out", "in", "gnd"), mos("M2", "pmos", "out", "pb", "vdd")],
               {"in": ("input", "x"), "out": ("output", "y")},
               sources=[two("I1", "current_source", "vdd", "m"), two("I2", "current_source", "m", "gnd")])
    with pytest.raises(InfeasibleTargetError) as ei:
        build_ctx(tmp_path, doc, toy_access, element_values=(("I1", 1e-6), ("I2", 2e-6)))
    assert detail(ei.value)["reason"] == "declared_source_kcl_conflict"
    assert set(ei.value.record.devices) <= {"I1", "I2"} and ei.value.record.devices
    assert ei.value.record.margin is None
    # 같은 값이면 충돌 없음(대조)
    _, _, ctx = build_ctx(tmp_path, doc, toy_access, element_values=(("I1", 1e-6), ("I2", 1e-6)))
    assert basis_of(ctx).fixed == (("I1", 1e-6), ("I2", 1e-6))


def test_structural_zero_current_mos(tmp_path, toy_access):
    doc = topo("hand_zero_mos",
               [mos("M1", "nmos", "out", "in", "gnd"), mos("M2", "pmos", "out", "pb", "vdd"),
                mos("M3", "nmos", "z", "in", "gnd")],
               {"in": ("input", "x"), "out": ("output", "y")},
               passives=[two("Cz", "capacitor", "z", "gnd")])
    with pytest.raises(StructureUnresolvedError) as ei:
        build_ctx(tmp_path, doc, toy_access)
    d = detail(ei.value)
    assert d["reason"] == "unsupported_rule_branch"
    assert d["rule_branch"] == "mos_zero_current_structural"
    assert ei.value.record.devices == ("M3",)
