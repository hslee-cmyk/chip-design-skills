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

from .conftest import build_ctx, circuit_cs_pmos_load, kschema, mos, r4_ln_idu, topo, two

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
