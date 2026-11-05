"""`dc_region_decl(snapshot, regions, *, donors, counters)` -> S0 필드 `device.region_decl = {소자: RegionDecl}` -- interface card
20261104-eo1r4-sf1l §3 (T-D1). `off` 소자는 dc_op·쓰기 계획·θ 스키마·전류 기저에 없고, 대칭에서 짝과 갈린다.

회로 twin: Ma·Mb nmos 가 (out, g, gnd) 에 병렬(서로 맞바꿈 대칭 -- 같은 궤도), R1 (vdd, out) 부하. Mb 를 `off` 로 선언하면 Ma 한 소자 회로(= conftest
회로 A 꼴)와 같은 점이 된다. 입력은 `build_ctx(..., regions=(RegionDecl(...),))`.
oracle (손): twin 의 Mb off 쪽 DC 점은 회로 A 와 같은 닫힌 식(V(out) = 1.8 - I·R, conftest r4 해석식 `r4_ln_idu`). 대칭 궤도는 card §3 문장
('짝 두 소자 중 하나만 off 면 graph.orbits 에서 갈린다')을 손으로 옮겼다.
"""
import pytest

from gmid_engine.authoring import RegionDecl
from gmid_engine.core import StructureUnresolvedError
from gmid_engine.sizing import DC_KEY, size_and_seal

from .conftest import build_ctx, circuit_cs_pmos_load, detail, kschema, mos, r4_ln_idu, topo, two

OFF_MB = RegionDecl("Mb", "off", None, ("gain_ss_db",), 1e-6, 1e-6)


def circuit_twin():
    return topo("rd_twin",
                [mos("Ma", "nmos", "out", "g", "gnd"), mos("Mb", "nmos", "out", "g", "gnd")],
                {"g": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                passives=[two("R1", "resistor", "vdd", "out")])


def theta_twin(i=1e-5, r=9e4, vgs=0.6, l1=1e-6):
    vout = 1.8 - i * r
    return {("L", "Ma"): l1, ("ln_idu", "Ma"): r4_ln_idu("nmos", vgs, vout, 0.0), ("current", "R1"): i,
            ("resistance", "R1"): r}


def orbit_of(ctx):
    return dict(ctx.base.value("graph", "s1", "orbits").devices)


def test_region_decl_field_value_writer_and_declared_only(tmp_path_factory, r4_access):
    ctx = build_ctx(tmp_path_factory.mktemp("rd1"), circuit_twin(), r4_access, regions=(OFF_MB,))[2]
    col = dict(ctx.base.column("device", "region_decl"))
    assert col == {"Mb": OFF_MB}                                   # 선언 소자만
    f = ctx.base.field("device", "Mb", "region_decl")
    assert f is not None and f.writer == "dc_region_decl"          # 필드마다 writer 하나
    assert ctx.base.field("device", "Ma", "region_decl") is None
    assert ctx.base.field("device", "R1", "region_decl") is None


def test_region_decl_triode_is_declared_too(tmp_path_factory, r4_access):
    tri = RegionDecl("M1", "triode")
    ctx = build_ctx(tmp_path_factory.mktemp("rd2"), circuit_cs_pmos_load(), r4_access, regions=(tri,))[2]
    assert dict(ctx.base.column("device", "region_decl")) == {"M1": tri}
    assert ctx.base.field("device", "M2", "region_decl") is None


def test_region_decl_no_declaration_no_field(tmp_path_factory, r4_access):
    ctx = build_ctx(tmp_path_factory.mktemp("rd3"), circuit_twin(), r4_access)[2]
    assert [k for k in ctx.base.keys("device") if ctx.base.field("device", k, "region_decl") is not None] == []


def test_region_decl_precedes_the_write_plan(tmp_path_factory, r4_access):
    """쓰기 계획이 선언을 읽는다: 계획 필드가 있는 S0 스냅샷에 region_decl 이 이미 있고, 계획이 Mb 를 다루지 않는다."""
    ctx = build_ctx(tmp_path_factory.mktemp("rd4"), circuit_twin(), r4_access, regions=(OFF_MB,))[2]
    assert ctx.base.field("device", "Mb", "region_decl") is not None
    assert ctx.base.field("device", "Ma", "dc_coord") is not None
    assert ctx.base.field("device", "Mb", "dc_coord") is None
    assert ctx.base.block_version("dc_region_decl")


def test_region_decl_off_device_absent_from_plan_schema_and_basis(tmp_path_factory, r4_access):
    ctx = build_ctx(tmp_path_factory.mktemp("rd5"), circuit_twin(), r4_access, regions=(OFF_MB,))[2]
    base = ctx.base
    # [A-88] 쓰기 계획 필드는 dc_coord(S0). dc_L 은 S2 평가 블록(dc_lengths)의 필드라 S0 base 에 값이 없고, dc_colour 는 graph 대칭 블록이
    # 모든 원소에 쓰는 필드(Mb 도 든다)라 둘은 '쓰기 계획에 없다'의 증거가 아니어서 뺐다 -- 뜻(off 가 쓰기 계획·θ·전류 기저에 없다)은 아래 단언이 유지.
    assert "Mb" not in dict(base.column("device", "dc_coord"))
    assert "Ma" in dict(base.column("device", "dc_coord"))
    writers = dict(base.column("node", "dc_writer"))
    assert all(w.element != "Mb" for w in writers.values())
    assert "Mb" not in repr(kschema(ctx))                           # θ 스키마
    assert "Ma" in repr(kschema(ctx))                               # 양성 대조
    assert "Mb" not in repr(base.value("graph", DC_KEY, "dc_current_basis"))   # 전류 기저 항


def test_region_decl_off_device_absent_from_dc_op(tmp_path_factory, r4_access):
    ctx = build_ctx(tmp_path_factory.mktemp("rd6"), circuit_twin(), r4_access, regions=(OFF_MB,))[2]
    ev = size_and_seal(ctx, theta_twin())
    assert ev.sealed is not None
    ops = dict(ev.snapshot.column("device", "dc_op"))
    assert set(ops) == {"Ma"}                                      # Mb 는 dc_op 키에 없다


def test_region_decl_pair_splits_orbit_only_when_one_is_off(tmp_path_factory, r4_access):
    ctx_plain = build_ctx(tmp_path_factory.mktemp("rd7a"), circuit_twin(), r4_access)[2]
    ctx_off = build_ctx(tmp_path_factory.mktemp("rd7b"), circuit_twin(), r4_access, regions=(OFF_MB,))[2]
    plain, off = orbit_of(ctx_plain), orbit_of(ctx_off)
    assert plain["Ma"] == plain["Mb"]                              # 대조: 선언 없으면 같은 궤도
    assert off["Ma"] != off["Mb"]                                  # 하나만 off -> 갈림(θ 가 묶이지 않는다)


def test_region_decl_both_off_stay_in_one_orbit(tmp_path_factory, r4_access):
    """짝 둘 다 같은 선언이면 갈리지 않는다(표시가 같다). 같은 폭·길이일 때."""
    both = (RegionDecl("Ma", "off", None, ("gain_ss_db",), 1e-6, 1e-6), OFF_MB)
    # [A-88] 게이트 넷 g 가 off 소자로만 정해지면 off_only_node 로 정지한다 -- g 에 도통 소자(다이오드 연결 Md, 저항 R2 부하)를 하나 이어 입력을 고친다.
    doc = topo("rd_twin_anchor",
               [mos("Ma", "nmos", "out", "g", "gnd"), mos("Mb", "nmos", "out", "g", "gnd"), mos("Md", "nmos", "g", "g", "gnd")],
               {"g": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
               passives=[two("R1", "resistor", "vdd", "out"), two("R2", "resistor", "vdd", "g")])
    ctx = build_ctx(tmp_path_factory.mktemp("rd8"), doc, r4_access, regions=both)[2]
    orb = orbit_of(ctx)
    assert orb["Ma"] == orb["Mb"]


def test_region_decl_node_only_set_by_off_device_stops(tmp_path_factory, r4_access):
    """노드 x 는 Moff 의 게이트에만 닿는다. 선언 없음 -> Moff 의 VGS 가 x 를 정한다(빌드 통과). off 선언 -> x 의 writer 가 없다 -> 기존 정지."""
    doc = topo("rd_offnode",
               [mos("M1", "nmos", "out", "in", "gnd"), mos("Moff", "nmos", "out", "x", "gnd")],
               {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
               passives=[two("R1", "resistor", "vdd", "out")], bias=["x"])
    build_ctx(tmp_path_factory.mktemp("rd10a"), doc, r4_access)                     # 대조: 통과
    off = RegionDecl("Moff", "off", None, ("gain_ss_db",), 1e-6, 1e-6)
    doc2 = dict(doc, topology_name="rd_offnode_b")
    with pytest.raises(StructureUnresolvedError):
        build_ctx(tmp_path_factory.mktemp("rd10b"), doc2, r4_access, regions=(off,))


# ---------------------------------------------------------------------------------------------------------------------------------------------
# [A-91 M-1] off_only_node: off 소자 d·s 가 닿는 비고정 넷 중, off 채널을 뺀 전압 결정 DC 요소(켜진 소자 채널, R, L, 전압원)로 고정 넷에 닿지
# 않는 넷이 있으면 구조 정지. 게이트·C·전류원은 전압을 정하지 못한다.
# oracle (a)/(d): 물리 불변식·회로 해석 결론 -- DC 에서 C 는 열림, 전류원은 전류만 정하고 MOS gate 는 전류 0 이므로 그 넷의 DC 전위를 정할 경로가
# 없다(KCL 만으로 전위가 자유 -> 정지가 맞다). 통과 사례는 같은 넷이 R·켜진 채널로 레일에 묶이는 구성(KVL 이 전위를 정한다).
# ---------------------------------------------------------------------------------------------------------------------------------------------
OFF_X = RegionDecl("Moff", "off", None, ("gain_ss_db",), 1e-6, 1e-6)
_PORTS = {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}


def _off_doc(name, extra_mos=(), passives=(), sources=(), bias=(), off_d="y", off_s="gnd"):
    net = [mos("M1", "nmos", "out", "in", "gnd"), mos("Moff", "nmos", off_d, "in", off_s), *extra_mos]
    return topo(name, net, _PORTS, passives=[two("R1", "resistor", "vdd", "out"), *passives], sources=sources, bias=bias)


def _stops(tmp, doc, access, regions=(OFF_X,)):
    with pytest.raises(StructureUnresolvedError) as ei:
        build_ctx(tmp, doc, access, regions=tuple(regions))
    d = detail(ei.value)
    assert d["rule_branch"] == "off_only_node" and d["reason"] == "unsupported_rule_branch", d   # 사유까지(다른 정지 사유면 실패)


def test_off_only_node_drain_with_capacitor_only_stops(tmp_path_factory, r4_access):
    """(a) off drain y 에 C 만 닿는다(C 는 DC 열림)."""
    doc = _off_doc("oo_a", passives=[two("C1", "capacitor", "y", "gnd")])
    _stops(tmp_path_factory.mktemp("oo_a1"), doc, r4_access)


def test_off_only_node_resistor_island_with_capacitor_stops(tmp_path_factory, r4_access):
    """(b) x-R-z, z-C 섬: R 로 이어진 두 넷 모두 고정 넷에 DC 경로가 없다."""
    doc = _off_doc("oo_b", passives=[two("Rz", "resistor", "y", "z"), two("C1", "capacitor", "z", "gnd")])
    _stops(tmp_path_factory.mktemp("oo_b"), doc, r4_access)


def test_off_only_node_drain_with_current_source_only_stops(tmp_path_factory, r4_access):
    """(c) off drain y + 전류원뿐(전류원은 전압을 정하지 못한다)."""
    doc = _off_doc("oo_c", sources=[two("IY", "current_source", "vdd", "y")])
    _stops(tmp_path_factory.mktemp("oo_c"), doc, r4_access)


def test_off_only_node_drain_with_on_device_gate_only_stops(tmp_path_factory, r4_access):
    """(d) off drain y + 켜진 소자 M2 의 gate 뿐(gate 는 전류 0)."""
    doc = _off_doc("oo_d", extra_mos=[mos("M2", "nmos", "out", "y", "gnd")])
    _stops(tmp_path_factory.mktemp("oo_d"), doc, r4_access)


def test_off_only_node_series_middle_between_two_off_stops(tmp_path_factory, r4_access):
    """(e2) 직렬 중간 넷 x: 두 소자 모두 off 이면 x 에 채널 전압원이 없다."""
    doc = topo("oo_e2", [mos("M1", "nmos", "out", "in", "gnd"), mos("Mo1", "nmos", "out", "in", "x"),
                         mos("Mo2", "nmos", "x", "in", "gnd")], _PORTS, passives=[two("R1", "resistor", "vdd", "out")])
    both = (RegionDecl("Mo1", "off", None, ("gain_ss_db",), 1e-6, 1e-6), RegionDecl("Mo2", "off", None, ("gain_ss_db",), 1e-6, 1e-6))
    _stops(tmp_path_factory.mktemp("oo_e2"), doc, r4_access, both)


@pytest.mark.parametrize("name,doc_kw", [
    ("f_resistor_to_rail", dict(passives=[two("Rz", "resistor", "y", "vdd")])),                                 # (f) x-R-레일
    ("g_on_channel_to_rail", dict(extra_mos=[mos("M2", "nmos", "y", "in", "gnd")],
                                  sources=[two("IY", "current_source", "vdd", "y")])),                    # (g) 켜진 소자 채널(전류는 전류원이 댄다)
])
def test_off_only_node_passes_when_node_tied_to_rail(tmp_path_factory, r4_access, name, doc_kw):
    build_ctx(tmp_path_factory.mktemp("oo_" + name), _off_doc("oo_" + name, **doc_kw), r4_access, regions=(OFF_X,))


def test_off_only_node_series_middle_with_one_on_device_passes(tmp_path_factory, r4_access):
    """(e3) 직렬 중간 x 에 켜진 소자 Mo2 의 채널(x-gnd)이 닿는다 -> 통과(Mo2 전류는 전류원 IX 가 댄다)."""
    doc = topo("oo_e3", [mos("M1", "nmos", "out", "in", "gnd"), mos("Mo1", "nmos", "out", "in", "x"),
                         mos("Mo2", "nmos", "x", "in", "gnd")], _PORTS, passives=[two("R1", "resistor", "vdd", "out")],
               sources=[two("IX", "current_source", "vdd", "x")])
    build_ctx(tmp_path_factory.mktemp("oo_e3"), doc, r4_access, regions=(RegionDecl("Mo1", "off", None, ("gain_ss_db",), 1e-6, 1e-6),))


def test_off_only_node_passes_when_drain_is_fixed_rail(tmp_path_factory, r4_access):
    """(h) off 소자의 d 가 고정 넷(레일)에 직접 닿는다: 비고정 넷이 없어 정지 대상 없음."""
    doc = _off_doc("oo_h", off_d="vdd", off_s="gnd")
    build_ctx(tmp_path_factory.mktemp("oo_h"), doc, r4_access, regions=(OFF_X,))


# ---------------------------------------------------------------------------------------------------------------------------------------------
# [A-92] off 소자 gate: 고정 넷에서 DC 전도로 닿지 않는 넷에 off 소자 g 가 닿고 켜진 소자 gate 는 닿지 않으면 구조 정지.
# oracle (a)/(d): 물리 불변식 -- 게이트는 전류 0 이고 C 는 DC 열림이라, 그 넷의 DC 전위를 정할 경로가 없다(off 전류의 결정자 미정).
# 켜진 소자 gate 를 공유하는 넷은 기존 W2·bias 규칙 몫이라 off_only_node 로 정지하면 안 된다(A-92 결정).
# ---------------------------------------------------------------------------------------------------------------------------------------------
def _off_gate_doc(name, extra_mos=(), bias=()):
    # Moff: d=vdd, s=gnd 모두 고정 넷(d·s 규칙 (1)에 걸리지 않음), gate 는 비고정 넷 gg, gg 에는 C1 만(DC 열림)
    net = [mos("M1", "nmos", "out", "in", "gnd"), mos("Moff", "nmos", "vdd", "gg", "gnd"), *extra_mos]
    return topo(name, net, _PORTS, passives=[two("R1", "resistor", "vdd", "out"), two("C1", "capacitor", "gg", "gnd")], bias=bias)


def test_off_only_node_off_gate_with_capacitor_only_stops(tmp_path_factory, r4_access):
    """(i) off gate 넷 gg 에 C 뿐, off 소자 d·s 는 고정 넷 -> off_only_node 구조 정지."""
    _stops(tmp_path_factory.mktemp("oo_i"), _off_gate_doc("oo_i"), r4_access)


# [A-93] 규칙 하나: 전도 엣지(device.dc_nets - off - current_source)로 전압 결정 넷(레일·고정 넷, 선언 bias, 입력 포트)에서 닿지 않는 넷 중
# off 소자 d·g·s 가 닿는 넷은 구조 정지. 게이트 예외 없음.
# oracle (a)/(d): 물리 불변식 -- 켜진 gate + off gate + C 만 닿는 넷은 DC 전위 결정자가 없다(KCL 만으론 자유, off 전류도 미정).
# 통과 사례는 같은 넷에 전위 결정자(입력 포트·선언 bias·R 로 레일)가 있는 구성.
def _passes(tmp, doc, access):
    ctx = build_ctx(tmp, doc, access, regions=(OFF_X,))[2]
    assert ctx.base.field("device", "M1", "dc_coord") is not None      # 다른 사유 없이 쓰기 계획이 나왔다
    assert ctx.base.field("device", "Moff", "dc_coord") is None        # off 소자는 계획 밖


def test_off_gate_shared_with_on_device_gate_and_capacitor_stops_as_off_only_node(tmp_path_factory, r4_access):
    """(j) 켜진 M2 gate + off gate + C 가 gg 를 공유, gg 는 DC 구동·선언 없음 -> off_only_node 구조 정지."""
    doc = _off_gate_doc("oo_j", extra_mos=[mos("M2", "nmos", "out", "gg", "gnd")])
    _stops(tmp_path_factory.mktemp("oo_j"), doc, r4_access)


def test_off_only_node_passes_when_off_gate_on_input_port(tmp_path_factory, r4_access):
    """(k) off gate 가 입력 포트 in 에 닿는다(입력 포트는 전압 결정 넷)."""
    doc = topo("oo_k", [mos("M1", "nmos", "out", "in", "gnd"), mos("Moff", "nmos", "vdd", "in", "gnd")], _PORTS,
               passives=[two("R1", "resistor", "vdd", "out")])
    _passes(tmp_path_factory.mktemp("oo_k"), doc, r4_access)


def test_off_only_node_passes_when_off_drain_on_input_port(tmp_path_factory, r4_access):
    """(l) off drain 이 입력 포트 in 에 닿는다."""
    doc = topo("oo_l", [mos("M1", "nmos", "out", "in", "gnd"), mos("Moff", "nmos", "in", "vdd", "gnd")], _PORTS,
               passives=[two("R1", "resistor", "vdd", "out")])
    _passes(tmp_path_factory.mktemp("oo_l"), doc, r4_access)


def test_off_only_node_passes_when_shared_gate_net_is_declared_bias(tmp_path_factory, r4_access):
    """(m) off gate + 켜진 gate 가 선언 bias 넷 gg 를 공유."""
    net = [mos("M1", "nmos", "out", "in", "gnd"), mos("Moff", "nmos", "vdd", "gg", "gnd"), mos("M2", "nmos", "out", "gg", "gnd")]
    doc = topo("oo_m", net, _PORTS, passives=[two("R1", "resistor", "vdd", "out")], bias=["gg"])   # bias 넷은 gate 전용(C 없음)
    _passes(tmp_path_factory.mktemp("oo_m"), doc, r4_access)


def test_off_only_node_passes_when_shared_gate_net_tied_to_rail_by_resistor(tmp_path_factory, r4_access):
    """(n) off gate + 켜진 gate 공유 넷 gg 가 R 로 레일에 닿는다(KVL 이 전위를 정한다)."""
    net = [mos("M1", "nmos", "out", "in", "gnd"), mos("Moff", "nmos", "vdd", "gg", "gnd"), mos("M2", "nmos", "out", "gg", "gnd")]
    doc = topo("oo_n", net, _PORTS, passives=[two("R1", "resistor", "vdd", "out"), two("Rg", "resistor", "vdd", "gg"),
                                              two("C1", "capacitor", "gg", "gnd")])
    _passes(tmp_path_factory.mktemp("oo_n"), doc, r4_access)


def test_dc_writer_plan_reads_device_dc_nets():
    """graph 정본: 전도 엣지는 정본 필드 device.dc_nets 를 읽는다(둘째 정의 금지, 계획 N3.3·A-92)."""
    from gmid_engine.sizing import dc_writer_plan
    assert ("device", "dc_nets") in set(dc_writer_plan.reads)
