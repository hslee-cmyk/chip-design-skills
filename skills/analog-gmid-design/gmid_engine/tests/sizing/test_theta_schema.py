"""`dc_theta_schema(snapshot, declared_resistors)` -- CONTRACT 4.4 [r2]: ThetaSchema(components, current_cone, fixed).

components(정렬): (ln_idu, writer MOS), (L, 모든 MOS), (y, W4 y 키), (current, free 원소), (resistance, DC 저항 중 선언 밖).
current_cone = MOS 이름순 ((MOS, 그 MOS 의 rows 항), ...), fixed = basis.fixed. 기대값은 계획 필드(dc_writer·dc_coord·basis
-- 각각 다른 파일에서 독립 판정)로부터 4.4 문장대로 다시 모은다.
"""
import pytest

from gmid_engine.sizing import DC_KEY, ThetaSchema, dc_theta_schema

from .conftest import NINE, build_ctx, circuit_cs_res, library_ctx, mos, topo, two


def expected(ctx, declared=()):
    b = ctx.base
    basis = b.value("graph", DC_KEY, "dc_current_basis")
    coords = dict(b.column("device", "dc_coord"))
    comps = {("ln_idu", m) for m, c in coords.items() if c.role == "writer"}
    comps |= {("L", m) for m in coords}
    comps |= {("y", w.y_key) for _, w in b.column("node", "dc_writer") if w.tier == "W4"}
    comps |= {("current", k) for k in basis.free}
    comps |= {("resistance", r) for r in basis.resistors if r not in declared}
    rows = dict(basis.rows)
    cone = tuple((m, rows[m]) for m in sorted(basis.mos))
    return tuple(sorted(comps)), cone, basis.fixed


def test_circuit_c_hand(ctx_c):
    s = ctx_c[2].schema
    assert isinstance(s, ThetaSchema)
    assert s.components == (("L", "M1"), ("L", "M2"), ("current", s.components[2][1]), ("ln_idu", "M1"),
                            ("ln_idu", "M2"), ("y", "out"))
    assert (s.components, s.current_cone, s.fixed) == expected(ctx_c[2])
    assert s.fixed == ()


def test_resistance_only_undeclared(tmp_path, toy_access):
    doc = circuit_cs_res()
    doc["topology_name"] = "ts_res_decl"
    ctx = build_ctx(tmp_path, doc, toy_access, element_values=(("R1", 5e4),))[2]
    assert ("resistance", "R1") not in ctx.schema.components
    ctx2 = build_ctx(tmp_path, circuit_cs_res(), toy_access)[2]
    assert ("resistance", "R1") in ctx2.schema.components


def test_fixed_source_in_cone(tmp_path, toy_access):
    doc = topo("ts_fixed", [mos("M1", "nmos", "n", "in", "gnd"), mos("M2", "nmos", "n", "b2", "gnd")],
               {"in": ("input", "x"), "n": ("output", "y")}, sources=[two("I1", "current_source", "vdd", "n")])
    ctx = build_ctx(tmp_path, doc, toy_access, element_values=(("I1", 3e-5),))[2]
    s = ctx.schema
    assert s.fixed == (("I1", 3e-5),)
    assert (s.components, s.current_cone, s.fixed) == expected(ctx)
    srcs = {t.source for _, terms in s.current_cone for t in terms}
    assert "I1" in srcs                                     # pivot MOS 행이 고정값을 쓴다


def test_mos_cone_rows_are_box_for_free_mos(ctx_c):
    """기저 원소가 MOS 자신인 행 = θ_I > 0 상자 하한."""
    s = ctx_c[2].schema
    free = {k for t, k in s.components if t == "current"}
    for m, terms in s.current_cone:
        if m in free:
            assert len(terms) == 1 and terms[0].source == m and (terms[0].num, terms[0].den) == (1, 1)


@pytest.mark.parametrize("name", NINE)
def test_library_schema(name, toy_access):
    raw, td, spec, inputs, s1, ctx = library_ctx(name, toy_access)
    declared = tuple(n for n, v in inputs.element_values if v is not None)
    s = ctx.schema
    assert (s.components, s.current_cone, s.fixed) == expected(ctx, declared)
    assert ctx.base.value("graph", DC_KEY, "dc_theta_schema") == s
    n_mos = len(raw["netlist"])
    assert sum(1 for t, _ in s.components if t == "L") == n_mos
    assert len(s.current_cone) == n_mos


def test_block_reuse(ctx_c):
    base = ctx_c[2].base
    dc_theta_schema.reset_stats()
    assert dc_theta_schema(base, ()) is base
    assert dc_theta_schema.stats().reuses == 1
