"""`dc_theta_schema(snapshot, engine_passives)` -- CONTRACT 4.4 [r2][r5]:
[U17 ①-b] 설계 40 v1.9.1 §2.4.8 D8: θ 스키마 필드는 graph/kernel `theta_schema`(옛 graph/dc `dc_theta_schema`), writer dc_theta_schema 유지.
`declared_resistors` 는 extras 가 아니라 커널 구조 파생 필드 graph/kernel `resistor_values` 의 이름으로 읽힌다(§2.4.7 KernelContext 행).
ThetaSchema(components, current_cone, fixed, zero_cancel).

components(정렬): (ln_idu, writer MOS), (L, 모든 MOS), (y, W4 y 키), (current, free 원소), (resistance, DC 저항 중 선언 밖)
+ [r5] (capacitance, engine 커패시터), (ss_resistance, 가지치기된 engine 저항 중 zero_cancel reason 이 None 아닌 것).
current_cone = MOS 이름순 ((MOS, 그 MOS 의 rows 항), ...), fixed = basis.fixed. 기대값은 계획 필드(dc_writer·dc_coord·basis
-- 각각 다른 파일에서 독립 판정)와 S1 연결 필드로부터 4.4 문장대로 다시 모은다. 영점 상쇄 구조 규칙(zero_cancel)은
`zero_cancel_oracle` 이 4.4 의 1~3 단계를 S1 필드(terminals·is_rail·port_direction·ac_ground_class·pins·bulk·element_class·
kind)에 직접 적용해 만든다(피검 함수 결과를 쓰지 않는다).
"""
import pytest

from gmid_engine.sizing import (DC_KEY, KERNEL_KEY, ZC_MIXED_DIRECTION, ZC_MULTIPLE_RESISTORS, ZC_NO_CAPACITOR, ZC_NO_CELL,
                                ZC_RESISTOR_END, ThetaSchema, ZeroCancel, dc_theta_schema)

from .conftest import NINE, build_ctx, circuit_cs_res, library_ctx, mos, topo, two
from .conftest import kschema  # [U17 ①-b] graph/kernel 필드 읽기(설계 40 v1.9.1 §2.4.7 KernelContext 행)


# ---------------------------------------------------------------------------
# 독립 oracle
# ---------------------------------------------------------------------------

def _pins(snap, e):
    return dict(snap.value("device", e, "pins"))


def zero_cancel_oracle(snap, engine_passives):
    """CONTRACT 4.4 [r5] 영점 상쇄 구조 규칙의 독립 구현. engine_passives 중 basis.pruned 에 든 저항마다 ZeroCancel(이름순)."""
    basis = snap.value("graph", DC_KEY, "dc_current_basis")
    pruned = set(basis.pruned)
    cls = dict(snap.column("device", "element_class"))
    kind = dict(snap.column("device", "kind"))
    passive = {e for e, c in cls.items() if c == "passive"}
    bulk_nets = set()
    for m, c in cls.items():
        if c == "mos":
            b = snap.value("device", m, "bulk")
            if b is not None and b.net is not None:
                bulk_nets.add(b.net)

    def internal(n):
        if snap.value("node", n, "is_rail"):
            return False
        if snap.value("node", n, "port_direction") is not None:
            return False
        t = snap.value("node", n, "terminals")
        if not t:
            return False
        if any(e not in passive for e, _ in t):
            return False
        return n not in bulk_nets

    out = []
    for r in sorted(e for e in engine_passives if e in passive and kind[e] == "resistor" and e in pruned):
        rn = set(_pins(snap, r).values())
        elems, boundary, seen, stack = {r}, set(), set(), sorted(rn)
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            if internal(n):
                for e, _ in snap.value("node", n, "terminals"):
                    elems.add(e)
                    stack.extend(_pins(snap, e).values())
            else:
                boundary.add(n)
        ends = [n for n in rn if n in boundary]
        end = ends[0] if len(ends) == 1 else None
        far = tuple(sorted(boundary - rn))
        if not any(kind[e] == "capacitor" for e in elems):
            out.append(ZeroCancel(r, end, far, (), ZC_NO_CAPACITOR))
            continue
        if any(kind[e] == "resistor" and e != r for e in elems):
            out.append(ZeroCancel(r, end, far, (), ZC_MULTIPLE_RESISTORS))
            continue
        if end is None:
            out.append(ZeroCancel(r, end, far, (), ZC_RESISTOR_END))
            continue
        drain_side, gate_side = [], []
        for m in sorted(x for x, c in cls.items() if c == "mos"):
            p = _pins(snap, m)
            if snap.value("node", p["s"], "ac_ground_class") is None:
                continue
            if p["d"] == end and p["g"] in far:
                drain_side.append(m)
            elif p["g"] == end and p["d"] in far:
                gate_side.append(m)
        cells = tuple(sorted(drain_side + gate_side))
        if not cells:
            out.append(ZeroCancel(r, end, far, (), ZC_NO_CELL))
        elif drain_side and gate_side:
            out.append(ZeroCancel(r, end, far, cells, ZC_MIXED_DIRECTION))
        else:
            out.append(ZeroCancel(r, end, far, cells, None))
    return tuple(out)


def engine_passives_of(ctx):
    """1.4: build_kernel_context 가 넘기는 engine 수동소자 = engine_elements 중 S1 element_class passive(이름 정렬)."""
    cls = dict(ctx.base.column("device", "element_class"))
    return tuple(sorted(e for e in ctx.inputs.engine_elements if cls.get(e) == "passive"))


def expected(ctx, declared=None):
    b = ctx.base
    if declared is None:
        declared = tuple(n for n, v in ctx.inputs.element_values if v is not None)
    basis = b.value("graph", DC_KEY, "dc_current_basis")
    coords = dict(b.column("device", "dc_coord"))
    kind = dict(b.column("device", "kind"))
    comps = {("ln_idu", m) for m, c in coords.items() if c.role == "writer"}
    comps |= {("L", m) for m in coords}
    comps |= {("y", w.y_key) for _, w in b.column("node", "dc_writer") if w.tier == "W4"}
    comps |= {("current", k) for k in basis.free}
    comps |= {("resistance", r) for r in basis.resistors if r not in declared}
    eng = engine_passives_of(ctx)
    zc = zero_cancel_oracle(b, eng)
    comps |= {("capacitance", e) for e in eng if kind[e] == "capacitor"}
    comps |= {("ss_resistance", z.resistor) for z in zc if z.reason is not None}
    rows = dict(basis.rows)
    cone = tuple((m, rows[m]) for m in sorted(basis.mos))
    return tuple(sorted(comps)), cone, basis.fixed, zc


def schema_tuple(s):
    return s.components, s.current_cone, s.fixed, s.zero_cancel


# ---------------------------------------------------------------------------
# 기존 (r2) 동작
# ---------------------------------------------------------------------------

def test_circuit_c_hand(ctx_c):
    s = kschema(ctx_c[2])
    assert isinstance(s, ThetaSchema)
    assert s.components == (("L", "M1"), ("L", "M2"), ("current", s.components[2][1]), ("ln_idu", "M1"),
                            ("ln_idu", "M2"), ("y", "out"))
    assert schema_tuple(s) == expected(ctx_c[2])
    assert s.fixed == () and s.zero_cancel == ()


def test_resistance_only_undeclared(tmp_path, toy_access):
    doc = circuit_cs_res()
    doc["topology_name"] = "ts_res_decl"
    ctx = build_ctx(tmp_path, doc, toy_access, element_values=(("R1", 5e4),))[2]
    assert ("resistance", "R1") not in kschema(ctx).components
    ctx2 = build_ctx(tmp_path, circuit_cs_res(), toy_access)[2]
    assert ("resistance", "R1") in kschema(ctx2).components


def test_fixed_source_in_cone(tmp_path, toy_access):
    doc = topo("ts_fixed", [mos("M1", "nmos", "n", "in", "gnd"), mos("M2", "nmos", "n", "b2", "gnd")],
               {"in": ("input", "x"), "n": ("output", "y")}, sources=[two("I1", "current_source", "vdd", "n")],
               bias=["b2"])                                                                  # b2: M2 gate 에만
    ctx = build_ctx(tmp_path, doc, toy_access, element_values=(("I1", 3e-5),))[2]
    s = kschema(ctx)
    assert s.fixed == (("I1", 3e-5),)
    assert schema_tuple(s) == expected(ctx)
    srcs = {t.source for _, terms in s.current_cone for t in terms}
    assert "I1" in srcs                                     # pivot MOS 행이 고정값을 쓴다


def test_mos_cone_rows_are_box_for_free_mos(ctx_c):
    """기저 원소가 MOS 자신인 행 = θ_I > 0 상자 하한."""
    s = kschema(ctx_c[2])
    free = {k for t, k in s.components if t == "current"}
    for m, terms in s.current_cone:
        if m in free:
            assert len(terms) == 1 and terms[0].source == m and (terms[0].num, terms[0].den) == (1, 1)


@pytest.mark.parametrize("name", NINE)
def test_library_schema(name, toy_access):
    raw, td, spec, inputs, s1, ctx = library_ctx(name, toy_access)
    declared = tuple(n for n, v in inputs.element_values if v is not None)
    s = kschema(ctx)
    assert schema_tuple(s) == expected(ctx, declared)
    assert ctx.base.field("graph", KERNEL_KEY, "theta_schema").writer == "dc_theta_schema"      # [U17 ①-b] D8 필드 위치
    n_mos = len(raw["netlist"])
    assert sum(1 for t, _ in s.components if t == "L") == n_mos
    assert len(s.current_cone) == n_mos
    # [r5] engine 커패시터는 모두 capacitance θ, 값 선언 커패시터는 θ 가 아니다(raw topology 에서 직접 셈)
    caps = {e["name"] for e in raw.get("passive_elements") or [] if e["kind"] == "capacitor"}
    eng = set(inputs.engine_elements)
    assert {k for t, k in s.components if t == "capacitance"} == caps & eng
    # 한 이름이 두 θ 종류에 동시에 들지 않는다(4.4)
    passive_keys = [k for t, k in s.components if t in ("resistance", "ss_resistance", "capacitance")]
    assert len(passive_keys) == len(set(passive_keys))


# 작성자 측 판정(10.3·O15)을 test 쪽이 topology JSON 을 손으로 읽어 다시 유도한 값:
#  two_stage_ota: Rz(O1, N_cc_rz)–Cc(N_cc_rz, OUT), N_cc_rz 내부 -> 경계 {O1, OUT}, end O1, far (OUT,);
#    M6 pmos (d OUT, g O1, s vdd) = gate 쪽 셀 -> S = (M6,), reason None.
#  nmcnr_amplifier: Rm(NodeCM, Vout), NodeCM 에 Cm1(NodeM2)·Cm2(NodeS2) -> 경계 {Vout, NodeM2, NodeS2}, end Vout,
#    far (NodeM2, NodeS2); M301 nmos (d Vout, g NodeS2, s vss) = drain 쪽 셀 -> S = (M301,), reason None.
HAND_ZC = {
    "two_stage_ota": (ZeroCancel("Rz", "O1", ("OUT",), ("M6",), None),),
    "nmcnr_amplifier": (ZeroCancel("Rm", "Vout", ("NodeM2", "NodeS2"), ("M301",), None),),
}


@pytest.mark.parametrize("name", sorted(HAND_ZC))
def test_library_zero_cancel_hand(name, toy_access):
    ctx = library_ctx(name, toy_access)[5]
    assert kschema(ctx).zero_cancel == HAND_ZC[name]
    keys = set(kschema(ctx).components)
    for z in HAND_ZC[name]:          # 구조 규칙이 정한 저항은 θ 가 아니다
        assert not any(k == z.resistor for _, k in keys)


def test_block_reuse(ctx_c):
    base = ctx_c[2].base
    dc_theta_schema.reset_stats()
    assert dc_theta_schema(base, ()) is base              # [U17 ①-b] extras = (engine_passives,) -- 선언 저항은 graph/kernel resistor_values 필드
    assert dc_theta_schema.stats().reuses == 1


# ---------------------------------------------------------------------------
# [r5] 손 회로: 원소 종류별 θ 와 구조 규칙 판정(각 reason 을 실제로 일으킨다)
# ---------------------------------------------------------------------------
# 공통 골격: M1 nmos (out, in, gnd) + RL (vdd, out) -- RL 은 DC 경로 저항(값 미선언 -> θ resistance).

PORTS = {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}


def cs(name, passives, extra_mos=(), ports=None, m1=None):
    nl = [m1 or mos("M1", "nmos", "out", "in", "gnd")] + list(extra_mos)
    return topo(name, nl, ports or PORTS, passives=[two("RL", "resistor", "vdd", "out")] + list(passives))


def ctx_of(tmp_path, doc, toy_access, engine, values=(), supplies=None):
    ev = tuple(sorted(dict(values, **{e: None for e in engine}).items()))
    return build_ctx(tmp_path, doc, toy_access, supplies, element_values=ev,
                     engine_elements=tuple(sorted(engine)))[2]


def check(ctx, zc, cap=(), ss_res=(), res=()):
    """스키마 = 독립 oracle, 그리고 손으로 적은 zero_cancel·수동 θ 성분."""
    s = kschema(ctx)
    assert schema_tuple(s) == expected(ctx)
    assert s.zero_cancel == zc
    assert sorted(k for t, k in s.components if t == "capacitance") == sorted(cap)
    assert sorted(k for t, k in s.components if t == "ss_resistance") == sorted(ss_res)
    assert sorted(k for t, k in s.components if t == "resistance") == sorted(res)


def test_rule_drain_side_cell(tmp_path, toy_access):
    """Rz(out, m)–Cc(m, in): m 내부 -> 경계 {out, in}, end out, far (in,), M1 (d out, g in, s gnd 레일) drain 쪽 셀 ->
    reason None, Rz 는 θ 가 아니고 Cc 는 capacitance."""
    doc = cs("zc_drain", [two("Rz", "resistor", "out", "m"), two("Cc", "capacitor", "m", "in")])
    ctx = ctx_of(tmp_path, doc, toy_access, ("Rz", "Cc"))
    check(ctx, (ZeroCancel("Rz", "out", ("in",), ("M1",), None),), cap=("Cc",), res=("RL",))
    # Rz 는 가지치기 저항(S1 잎 가지치기) -- 구조 규칙 대상 전제
    assert "Rz" in ctx.base.value("graph", DC_KEY, "dc_current_basis").pruned


def two_stage(name, passives):
    """2단: M0 nmos (g1, in, gnd) + R0 (vdd, g1) -> M1 nmos (out, g1, gnd) + RL (vdd, out). g1 = 1단 출력(MOS drain 넷)."""
    return topo(name, [mos("M0", "nmos", "g1", "in", "gnd"), mos("M1", "nmos", "out", "g1", "gnd")], PORTS,
                passives=[two("R0", "resistor", "vdd", "g1"), two("RL", "resistor", "vdd", "out")] + list(passives))


def test_rule_gate_side_cell(tmp_path, toy_access):
    """O15 순서 무관 해석(two_stage_ota 배치): Rz(g1, m)–Cc(m, out) -> end g1, far (out,), M1 (g g1, d out, s gnd) gate == end·
    drain ∈ far -> gate 쪽 셀, reason None. M0 은 drain == end 지만 gate in ∉ far 라 셀이 아니다."""
    doc = two_stage("zc_gate", [two("Rz", "resistor", "g1", "m"), two("Cc", "capacitor", "m", "out")])
    ctx = ctx_of(tmp_path, doc, toy_access, ("Rz", "Cc"))
    check(ctx, (ZeroCancel("Rz", "g1", ("out",), ("M1",), None),), cap=("Cc",), res=("R0", "RL"))


def test_reason_no_capacitor(tmp_path, toy_access):
    """Rz(out, m), m 은 M2 의 gate(수동소자 아닌 단자) -> 내부 넷 아님 -> 망 {Rz}, 커패시터 없음.
    경계 = {out, m} 둘 다 R 의 넷 -> end None, far ()."""
    doc = cs("zc_nocap", [two("Rz", "resistor", "out", "m")], extra_mos=[mos("M2", "nmos", "out", "m", "gnd")])
    ctx = ctx_of(tmp_path, doc, toy_access, ("Rz",))
    check(ctx, (ZeroCancel("Rz", None, (), (), ZC_NO_CAPACITOR),), ss_res=("Rz",), res=("RL",))


def test_reason_multiple_resistors(tmp_path, toy_access):
    """Rz(out, m)–Cc(m, k)–R2(k, g1): 망 = {Rz, Cc, R2} -> 두 저항 모두 network_multiple_resistors -> ss_resistance 폴백.
    end·far 는 저항마다(Rz: out / (g1,), R2: g1 / (out,)), reason 이 먼저 정해져 cells = ()."""
    doc = two_stage("zc_multi", [two("Rz", "resistor", "out", "m"), two("Cc", "capacitor", "m", "k"),
                                 two("R2", "resistor", "k", "g1")])
    ctx = ctx_of(tmp_path, doc, toy_access, ("Rz", "Cc", "R2"))
    check(ctx, (ZeroCancel("R2", "g1", ("out",), (), ZC_MULTIPLE_RESISTORS),
                ZeroCancel("Rz", "out", ("g1",), (), ZC_MULTIPLE_RESISTORS)),
          cap=("Cc",), ss_res=("R2", "Rz"), res=("R0", "RL"))


def test_reason_resistor_end_unreachable_through_loader(tmp_path, toy_access):
    """ZC_RESISTOR_END(end_net None)는 커패시터가 있고 저항이 하나인 망에서 R 의 두 넷이 모두 내부일 때만 생긴다(두 넷이 모두
    비내부면 망 = {R} 라 커패시터 없음이 먼저). 그런데 그 두 넷은 R 로만 DC 연결된 섬이라 authoring 로더가 hidden_rail
    (DEC-60 (iii))로 거부한다 -- 공개 로더 경로로는 도달하지 않는 방어 분기임을 기록한다(보고 대상)."""
    from gmid_engine.core import SchemaRejectedError
    doc = cs("zc_end", [two("C1", "capacitor", "out", "m1"), two("Ra", "resistor", "m1", "m2"),
                        two("C2", "capacitor", "m2", "in")])
    with pytest.raises(SchemaRejectedError) as ei:
        ctx_of(tmp_path, doc, toy_access, ("C1", "Ra", "C2"))
    hits = dict(ei.value.record.detail)["hits"]
    assert {h.rule for h in hits} == {"hidden_rail"} and {h.where for h in hits} == {"m1", "m2"}


def test_reason_no_cs_cell(tmp_path, toy_access):
    """Rz(out, m)–Cz(m, gnd): 경계 {out, gnd}, far (gnd,) -- gate 가 gnd 이거나 drain 이 gnd 인 셀 없음 -> no_cs_cell."""
    doc = cs("zc_nocell", [two("Rz", "resistor", "out", "m"), two("Cz", "capacitor", "m", "gnd")])
    ctx = ctx_of(tmp_path, doc, toy_access, ("Rz", "Cz"))
    check(ctx, (ZeroCancel("Rz", "out", ("gnd",), (), ZC_NO_CELL),), cap=("Cz",), ss_res=("Rz",), res=("RL",))


def test_reason_mixed_direction(tmp_path, toy_access):
    """Rz(out, m)–Cc(m, x): end out, far (x,). M1 (d out, g x) drain 쪽, M2 (d x, g out) gate 쪽 -> 섞임, cells 채움."""
    doc = cs("zc_mixed", [two("Rz", "resistor", "out", "m"), two("Cc", "capacitor", "m", "x"),
                          two("RL2", "resistor", "vdd", "x")],
             extra_mos=[mos("M2", "nmos", "x", "out", "gnd"), mos("M3", "nmos", "out", "in", "gnd")],
             m1=mos("M1", "nmos", "out", "x", "gnd"))
    ctx = ctx_of(tmp_path, doc, toy_access, ("Rz", "Cc"))
    check(ctx, (ZeroCancel("Rz", "out", ("x",), ("M1", "M2"), ZC_MIXED_DIRECTION),), cap=("Cc",), ss_res=("Rz",),
          res=("RL", "RL2"))


def test_cell_source_must_be_ac_ground(tmp_path, toy_access):
    """셀 조건의 source ac_ground_class: M1 source 를 저항 Rs(s, gnd) 위 넷 s(ac_ground_class None)로 옮기면
    drain_side 와 같은 연결에서도 셀이 아니다 -> no_cs_cell."""
    doc = cs("zc_degen", [two("Rz", "resistor", "out", "m"), two("Cc", "capacitor", "m", "in"),
                          two("Rs", "resistor", "s", "gnd")], m1=mos("M1", "nmos", "out", "in", "s"))
    ctx = ctx_of(tmp_path, doc, toy_access, ("Rz", "Cc"), values=(("Rs", 1e3),))
    assert ctx.base.value("node", "s", "ac_ground_class") is None
    check(ctx, (ZeroCancel("Rz", "out", ("in",), (), ZC_NO_CELL),), cap=("Cc",), ss_res=("Rz",), res=("RL",))


def test_internal_net_excludes_bulk_net(tmp_path, toy_access):
    """내부 넷 조건 1: 어떤 MOS 의 bulk 넷도 아니어야 한다. drain 쪽 셀 회로에서 M1 bulk 를 m 으로 선언하면 m 이 내부가 아니라
    망 = {Rz} -> 커패시터 없음."""
    doc = cs("zc_bulk", [two("Rz", "resistor", "out", "m"), two("Cc", "capacitor", "m", "in")],
             m1=mos("M1", "nmos", "out", "in", "gnd", "m"))
    ctx = ctx_of(tmp_path, doc, toy_access, ("Rz", "Cc"))
    check(ctx, (ZeroCancel("Rz", None, (), (), ZC_NO_CAPACITOR),), cap=("Cc",), ss_res=("Rz",), res=("RL",))


def test_port_leaf_resistor_is_dc_resistor_not_rule(tmp_path, toy_access):
    """m 을 출력 포트로 선언하면 S1 잎 가지치기가 포트에 붙은 잎 저항을 남긴다(graph 4.3 '포트·레일에 붙은 잎 저항은 남는다')
    -> Rz 는 가지치기 저항이 아니라 DC 저항 -> engine 이어도 resistance θ, zero_cancel 에 없음(4.4 '가지치기 안 된 engine
    저항은 resistance')."""
    ports = dict(PORTS, m=("output", "aux_output"))
    doc = cs("zc_port", [two("Rz", "resistor", "out", "m"), two("Cc", "capacitor", "m", "in")], ports=ports)
    ctx = ctx_of(tmp_path, doc, toy_access, ("Rz", "Cc"))
    assert "Rz" not in ctx.base.value("graph", DC_KEY, "dc_current_basis").pruned
    check(ctx, (), cap=("Cc",), res=("RL", "Rz"))


def test_element_class_rules(tmp_path, toy_access):
    """원소 종류별(4.4): engine DC 경로 저항 RL -> resistance(ss_resistance·zero_cancel 아님), 값 선언 가지치기 저항 Rd 와
    pending(engine 아님) 가지치기 저항 Rp 는 zero_cancel·θ 어디에도 없음, 값 선언 커패시터 CL 은 θ 아님, engine 이상원은
    무시(수동소자만), engine 커패시터 Cc 만 capacitance."""
    doc = cs("zc_classes", [two("Rz", "resistor", "out", "m"), two("Cc", "capacitor", "m", "in"),
                            two("Rd", "resistor", "out", "md"), two("Cd", "capacitor", "md", "in"),
                            two("Rp", "resistor", "out", "mp"), two("Cp", "capacitor", "mp", "in"),
                            two("CL", "capacitor", "out", "gnd")])
    doc["ideal_sources"] = [two("Ib", "current_source", "vdd", "out")]
    ctx = build_ctx(tmp_path, doc, toy_access,
                    element_values=(("CL", 1e-12), ("Cc", None), ("Cd", 1e-12), ("Cp", None), ("Ib", None),
                                    ("RL", None), ("Rd", 2e3), ("Rp", None), ("Rz", None)),
                    engine_elements=("Cc", "Ib", "RL", "Rz"))[2]
    s = kschema(ctx)
    assert schema_tuple(s) == expected(ctx)
    assert [z.resistor for z in s.zero_cancel] == ["Rz"]
    kinds = {}
    for t, k in s.components:
        if t in ("resistance", "ss_resistance", "capacitance"):
            kinds.setdefault(k, set()).add(t)
    assert kinds["RL"] == {"resistance"}
    assert kinds["Cc"] == {"capacitance"}
    for k in ("Rd", "Rp", "Cd", "Cp", "CL", "Ib", "Rz"):
        assert not (kinds.get(k, set()) & {"resistance", "ss_resistance", "capacitance"}), k


HAND_DOCS = {
    "drain": lambda: cs("rn_drain", [two("Rz", "resistor", "out", "m"), two("Cc", "capacitor", "m", "in")]),
    "gate": lambda: two_stage("rn_gate", [two("Rz", "resistor", "g1", "m"), two("Cc", "capacitor", "m", "out")]),
    "multi": lambda: two_stage("rn_multi", [two("Rz", "resistor", "out", "m"), two("Cc", "capacitor", "m", "k"),
                                            two("R2", "resistor", "k", "g1")]),
    "nocell": lambda: cs("rn_nocell", [two("Rz", "resistor", "out", "m"), two("Cz", "capacitor", "m", "gnd")]),
    "mixed": lambda: cs("rn_mixed", [two("Rz", "resistor", "out", "m"), two("Cc", "capacitor", "m", "x"),
                                     two("RL2", "resistor", "vdd", "x")],
                        extra_mos=[mos("M2", "nmos", "x", "out", "gnd"), mos("M3", "nmos", "out", "in", "gnd")],
                        m1=mos("M1", "nmos", "out", "x", "gnd")),
}


@pytest.mark.parametrize("seed", [1, 2])
@pytest.mark.parametrize("case", sorted(HAND_DOCS))
def test_hand_renaming_zero_cancel_follows_sigma(case, seed, tmp_path, toy_access):
    """이름 전단사 σ(넷·원소): engine_elements 를 σ 로 옮기면 zero_cancel(resistor·end·far·cells·reason)과 수동 θ 성분이
    σ 로 옮겨진 것과 같다(구조 규칙은 연결만 쓴다 -- 이름이 결정을 가르지 않는다)."""
    from .conftest import rename
    doc = HAND_DOCS[case]()
    eng = tuple(sorted(e["name"] for e in doc["passive_elements"] if e["name"] not in ("RL", "R0", "RL2")))
    ctx = ctx_of(tmp_path, doc, toy_access, eng)
    d2, sn, se = rename(doc, seed)
    ctx2 = ctx_of(tmp_path, d2, toy_access, tuple(se[e] for e in eng), supplies={sn["vdd"]: 1.8, sn["gnd"]: 0.0})
    sig = dict(sn)
    sig.update(se)
    m = lambda x: None if x is None else sig[x]          # noqa: E731
    zc1 = {(m(z.resistor), m(z.end_net), tuple(sorted(m(n) for n in z.far_nets)), tuple(sorted(m(c) for c in z.cells)),
            z.reason) for z in kschema(ctx).zero_cancel}
    zc2 = {(z.resistor, z.end_net, z.far_nets, z.cells, z.reason) for z in kschema(ctx2).zero_cancel}
    assert zc1 == zc2 and len(zc1) == len(kschema(ctx).zero_cancel)
    pk = ("capacitance", "ss_resistance")
    assert {(t, sig[k]) for t, k in kschema(ctx).components if t in pk} == {
        (t, k) for t, k in kschema(ctx2).components if t in pk}
    assert schema_tuple(kschema(ctx2)) == expected(ctx2)


def test_engine_element_not_in_s1_rejected(tmp_path, toy_access):
    """1.4 [r5]: engine_elements 이름이 S1 원소가 아니면 ValueError."""
    doc = cs("zc_unknown", [two("Cc", "capacitor", "out", "in")])
    with pytest.raises(ValueError):
        ctx_of(tmp_path, doc, toy_access, ("Cc", "Cnope"))


def test_passive_theta_extras_change_only_schema_inputs(tmp_path, toy_access):
    """engine 집합이 같으면 같은 스키마(결정론), 다르면 스키마만 달라지고 계획 필드(dc_writer·basis)는 그대로."""
    doc = cs("zc_det", [two("Rz", "resistor", "out", "m"), two("Cc", "capacitor", "m", "in")])
    a = ctx_of(tmp_path, doc, toy_access, ("Rz", "Cc"))
    b = ctx_of(tmp_path, doc, toy_access, ("Rz", "Cc"))
    assert kschema(a) == kschema(b)
    c = ctx_of(tmp_path, doc, toy_access, ("Cc",), values=(("Rz", 1e3),))
    assert kschema(c).zero_cancel == ()
    assert kschema(c).current_cone == kschema(a).current_cone
    assert c.base.column("node", "dc_writer") == a.base.column("node", "dc_writer")
    assert (c.base.value("graph", DC_KEY, "dc_current_basis")
            == a.base.value("graph", DC_KEY, "dc_current_basis"))
