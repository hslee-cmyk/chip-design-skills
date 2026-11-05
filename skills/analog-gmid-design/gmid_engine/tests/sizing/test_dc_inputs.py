"""`dc_inputs_from_spec(spec) -> DcInputs` -- CONTRACT 1.1·1.2: 사람 선언 투영. 결정 대기 칸은 '미선언'으로 투영하고 막지
않는다(pending 에 기록만).

입력: library `*.sizing_spec.json` 을 authoring `load_sizing_spec` 으로 읽은 `SizingSpecDoc`(입력 생성용) + 그 필드를
`dataclasses.replace` 로 바꾼 변형. 기대값은 1.2 의 투영 규칙을 이 파일에서 따로 적용한다.
"""
import dataclasses
import json

import pytest

from gmid_engine.authoring import (REGION_TRIODE, InputDc, PendingMark, RegionDecl, ElementValue, load_sizing_spec,
                                   load_topology)
from gmid_engine.core import SchemaRejectedError
from gmid_engine.sizing import DcInputs, dc_inputs_from_spec

from .conftest import LIBRARY, NINE, spec_catalog

CATALOG = spec_catalog()
TRIODE = "triode"          # [r9] CONTRACT 1.2 / SPEC_CONTRACT 1절: intended_region 영역 어휘 정본(이 파일이 계약 문구에서 옮김)

_CACHE = {}


def spec_of(name):
    if name not in _CACHE:
        topo = load_topology(str(LIBRARY / (name + ".topology.json")))
        _CACHE[name] = load_sizing_spec(str(LIBRARY / (name + ".sizing_spec.json")), topo, CATALOG)
    return _CACHE[name]


def expected_projection(spec):
    """CONTRACT 1.2 규칙을 독립 적용."""
    idc = spec.input_dc
    if idc.mode == "net":
        input_dc_v = dict(spec.supplies_v)[idc.net]
    elif idc.mode == "value":
        input_dc_v = idc.value_v
    else:
        input_dc_v = None
    nt = spec.node_voltage_targets_v if isinstance(spec.node_voltage_targets_v, tuple) else ()
    ev = tuple((e.name, e.value if e.mode == "value" else None) for e in spec.element_values)
    regions = ()
    if isinstance(spec.intended_region, tuple):
        # [EO-1 범위 4] card §3: DcInputs.regions = RegionDecl tuple 이름순(옛 linear_devices 자리 -- triode 만 거르던 투영이 선언 전체로)
        regions = tuple(sorted(spec.intended_region, key=lambda r: r.device))
    pend = tuple(sorted((p.path, p.decision) for p in spec.pending))
    # [r5] engine_elements = element_values 중 mode == "engine" 인 원소 이름 정렬 tuple(pending 은 들지 않는다)
    eng = tuple(sorted(e.name for e in spec.element_values if e.mode == "engine"))
    # [TB-1 interface §1·J-T1] 세 bool 칸 = spec 선언 유무(값은 읽지 않는다). oracle (손): library spec 에서 손으로 센 선언 --
    # gbw_target_hz·settling 은 compensation_targets 에 결정 대기 아닌 항목이 있으면 True, has_rout_limit 은 제약 metric 중 정확히 rout_ss_ohm 이 있으면 True.
    # (two_stage_ota 류 gbw 선언, current_reuse_telescopic_ota 만 settling 선언, pushpull·sf_pushpull·two_stage_ota_sf 만 rout 제약)
    ct = dict(spec.compensation_targets) if isinstance(spec.compensation_targets, tuple) else {}
    declared = lambda k: k in ct and getattr(ct[k], "decision", None) is None            # noqa: E731
    cons = spec.constraints if isinstance(spec.constraints, tuple) else ()
    return DcInputs(tuple(spec.supplies_v), input_dc_v, nt, ev, regions, pend, eng,
                    has_gbw_target=declared("gbw_target_hz"), has_rout_limit=any(getattr(c, "metric", None) == "rout_ss_ohm" for c in cons),
                    has_settling=declared("settling"))


@pytest.mark.parametrize("name", NINE)
def test_library_projection(name):
    spec = spec_of(name)
    got = dc_inputs_from_spec(spec)
    assert isinstance(got, DcInputs)
    assert got == expected_projection(spec)
    assert got.supplies_v == spec.supplies_v
    # 결정 대기 칸이 있어도 막지 않고 pending 에 모두 남긴다
    assert len(got.pending) == len(spec.pending)


def test_pending_not_blocking_and_recorded():
    spec = spec_of("two_stage_ota")
    assert spec.input_dc.mode == "pending"
    got = dc_inputs_from_spec(spec)
    assert got.input_dc_v is None
    assert got.node_targets == ()            # PendingMark -> ()
    assert ("human.input_dc", "SP-2") in got.pending
    assert list(got.pending) == sorted(got.pending)


def _base():
    return spec_of("two_stage_ota")


def test_input_dc_net_mode_reads_supply_value():
    spec = dataclasses.replace(_base(), input_dc=InputDc("net", "vdd", None, None, None))
    assert dc_inputs_from_spec(spec).input_dc_v == dict(spec.supplies_v)["vdd"]


def test_input_dc_value_mode():
    spec = dataclasses.replace(_base(), input_dc=InputDc("value", None, 0.75, None, None))
    assert dc_inputs_from_spec(spec).input_dc_v == 0.75


@pytest.mark.parametrize("mode", ["engine", "pending"])
def test_input_dc_engine_or_pending_is_none(mode):
    spec = dataclasses.replace(_base(), input_dc=InputDc(mode, None, None, None, "SP-2" if mode == "pending" else None))
    assert dc_inputs_from_spec(spec).input_dc_v is None


def test_node_targets_tuple_passed_through():
    nt = (("o1", 0.9), ("out", 0.8))
    spec = dataclasses.replace(_base(), node_voltage_targets_v=nt)
    assert dc_inputs_from_spec(spec).node_targets == nt


def test_node_targets_pending_or_none_is_empty():
    for v in (PendingMark("human.node_voltage_targets_v", "CI-15"), None):
        spec = dataclasses.replace(_base(), node_voltage_targets_v=v)
        assert dc_inputs_from_spec(spec).node_targets == ()


def test_element_values_value_vs_other_modes():
    evs = (ElementValue("CL", "value", "value_farad", 3e-12, None, None),
           ElementValue("Cc", "engine", None, None, None, None),
           ElementValue("Rz", "pending", None, None, None, "SP-9"))
    spec = dataclasses.replace(_base(), element_values=evs)
    assert dc_inputs_from_spec(spec).element_values == (("CL", 3e-12), ("Cc", None), ("Rz", None))


def test_engine_elements_engine_only_sorted_pending_excluded():
    """[r5] 1.2: engine_elements = mode engine 원소만(이름 정렬). value·pending 은 들지 않는다(결정 대기 값은 엔진이 고르지
    않는다). 수동소자·이상원 모두 이름이 든다(1.1)."""
    evs = (ElementValue("Rz", "engine", None, None, None, None),
           ElementValue("CL", "value", "value_farad", 3e-12, None, None),
           ElementValue("Cc", "engine", None, None, None, None),
           ElementValue("Cp", "pending", None, None, None, "SP-9"),
           ElementValue("Ib", "engine", None, None, None, None))
    spec = dataclasses.replace(_base(), element_values=evs)
    got = dc_inputs_from_spec(spec)
    assert got.engine_elements == ("Cc", "Ib", "Rz")
    assert "Cp" not in got.engine_elements and "CL" not in got.engine_elements
    # element_values 투영 규칙은 그대로(engine·pending 모두 None)
    assert dict(got.element_values) == {"Rz": None, "CL": 3e-12, "Cc": None, "Cp": None, "Ib": None}


def test_engine_elements_default_empty():
    assert DcInputs((("gnd", 0.0),)).engine_elements == ()
    spec = dataclasses.replace(_base(), element_values=(ElementValue("CL", "value", "value_farad", 3e-12, None,
                                                                     None),))
    assert dc_inputs_from_spec(spec).engine_elements == ()


def test_region_vocabulary_single_source():
    """[r9] 1.2: authoring REGION_TRIODE = "triode"(같은 개념 한 정의). [EO-1 범위 4] sizing `LINEAR_REGION` 은 interface card 에 없어
    (영역 어휘 정본 = authoring REGION_TRIODE·REGION_OFF) 이 단언에서 뺐다 -- 뜻(어휘가 한 정의)은 authoring 쪽에서 유지."""
    assert REGION_TRIODE == TRIODE


def test_triode_devices_from_intended_region_sorted():
    """[r9 -> EO-1 범위 4] 투영은 이제 선언 전체(regions, 이름순)이고, 그중 region == "triode" 인 소자 이름은 ("M3", "M7")
    (손으로 만든 RegionDecl 은 로더를 거치지 않아 어휘 검사 없이 투영 규칙만 본다)."""
    regions = (RegionDecl("M7", TRIODE, None), RegionDecl("M1", "saturation", None),
               RegionDecl("M3", TRIODE, None), RegionDecl("M5", "linear", None))
    spec = dataclasses.replace(_base(), intended_region=regions)
    got = dc_inputs_from_spec(spec).regions
    assert [r.device for r in got] == ["M1", "M3", "M5", "M7"]
    assert tuple(r.device for r in got if r.region == TRIODE) == ("M3", "M7")


# ---------------------------------------------------------------------------
# [EO-1 범위 4, interface card 20261104-eo1r4-sf1l §3 T-L2] DcInputs.regions = RegionDecl tuple(이름순, 옛 linear_devices 자리)
# oracle (식): card §3 'DcInputs 칸 regions = RegionDecl tuple (이름순, linear_devices 자리)'. 손으로 만든 RegionDecl 은 로더를 거치지 않는다.
# ---------------------------------------------------------------------------

def test_region_dc_inputs_field_regions_replaces_linear_devices():
    names = [f.name for f in dataclasses.fields(DcInputs)]
    assert "regions" in names and "linear_devices" not in names
    assert not hasattr(DcInputs((("gnd", 0.0),)), "linear_devices")
    assert DcInputs((("gnd", 0.0),)).regions == ()


def test_region_dc_inputs_projects_all_declared_regions_sorted():
    """triode·off 모두 투영(off 를 떨구지 않는다), 이름순 tuple, 원소는 RegionDecl 그대로."""
    r7 = RegionDecl("M7", TRIODE, None)
    r2 = RegionDecl("M2", "off", None, ("gain_ss_db",), 1e-6, 2e-6)
    r5 = RegionDecl("M5", TRIODE, None)
    spec = dataclasses.replace(_base(), intended_region=(r7, r2, r5))
    got = dc_inputs_from_spec(spec).regions
    assert isinstance(got, tuple)
    assert [r.device for r in got] == ["M2", "M5", "M7"]
    assert got == (r2, r5, r7)
    assert (got[0].w_m, got[0].l_m, got[0].judged_by) == (1e-6, 2e-6, ("gain_ss_db",))


def test_region_dc_inputs_pending_or_empty_is_empty_tuple():
    from gmid_engine.authoring import PendingMark
    for v in (PendingMark("human.intended_region", "CI-18"), ()):
        spec = dataclasses.replace(_base(), intended_region=v)
        assert dc_inputs_from_spec(spec).regions == ()


# ---------------------------------------------------------------------------
# [r9] spec 경로 끝까지: JSON spec -> load_sizing_spec -> dc_inputs_from_spec
# ---------------------------------------------------------------------------

US = {"kind": "user_spec", "record": "r9 test triode declaration", "decided": "2026-10-08"}


def _spec_with_regions(tmp_path, regions):
    """library two_stage_ota spec 의 human.intended_region 만 바꿔 tmp 에 쓰고 로더로 읽는다(형식: SPEC_CONTRACT 1절
    {소자: {region, source}})."""
    name = "two_stage_ota"
    raw = json.loads((LIBRARY / (name + ".sizing_spec.json")).read_text(encoding="utf-8"))
    raw["human"]["intended_region"] = {d: {"region": r, "source": dict(US)} for d, r in regions.items()}
    p = tmp_path / (name + ".sizing_spec.json")
    p.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    topo = load_topology(str(LIBRARY / (name + ".topology.json")))
    return load_sizing_spec(str(p), topo, CATALOG)


def test_spec_path_triode_populates_regions(tmp_path):
    """spec JSON 에 triode 선언 -> regions 가 그 소자들(이름순). r8 까지는 spec 경로로 늘 비었다(O19)."""
    spec = _spec_with_regions(tmp_path, {"M7": TRIODE, "M5": TRIODE})
    assert {(r.device, r.region) for r in spec.intended_region} == {("M7", TRIODE), ("M5", TRIODE)}
    got = dc_inputs_from_spec(spec)
    assert [(r.device, r.region) for r in got.regions] == [("M5", TRIODE), ("M7", TRIODE)]
    assert got == expected_projection(spec)


def test_spec_path_empty_declaration(tmp_path):
    spec = _spec_with_regions(tmp_path, {})
    assert spec.intended_region == () and dc_inputs_from_spec(spec).regions == ()


@pytest.mark.parametrize("word", ["linear", "saturation"])
def test_spec_loader_rejects_non_triode_region(tmp_path, word):
    """SPEC_CONTRACT 1절: 영역 어휘 밖 낱말(예 "linear", "saturation")은 `type` -> SchemaRejectedError(gate intended_region)."""
    with pytest.raises(SchemaRejectedError) as ei:
        _spec_with_regions(tmp_path, {"M7": word})
    d = dict(ei.value.record.detail)
    assert "type" in [h.rule for h in d["hits"]]
    assert d["rejected_gates"] == ("intended_region",)


def test_regions_pending_region_is_empty():
    spec = dataclasses.replace(_base(), intended_region=PendingMark("human.intended_region", "CI-18"))
    assert dc_inputs_from_spec(spec).regions == ()


@pytest.mark.parametrize("bad", [None, {}, "spec", DcInputs((("gnd", 0.0),))])
def test_type_error_for_non_spec(bad):
    with pytest.raises(TypeError):
        dc_inputs_from_spec(bad)
