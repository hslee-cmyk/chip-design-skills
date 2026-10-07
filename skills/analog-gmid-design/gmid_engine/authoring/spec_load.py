"""회로 사이징 spec 로더 -- 모든 spec 게이트를 돌려 위반을 전부 모은 뒤 한 번에 거부 (설계 design_spec_format 3.2·3.3).

진입점: `load_sizing_spec(path, topology, metric_catalog) -> SizingSpecDoc`.

* `topology`: 이미 검증된 `TopologyDoc`(파일을 다시 읽지 않는다). **필수** -- 교차 검사를 끄는 None 경로가 없다
  (TopologyDoc 가 아니면 `TypeError`).
* `metric_catalog`: `{metric 이름: MetricSignature}` 매핑(MOD5 레지스트리 이름표를 MOD10 이 주입 -- MOD2 는 MOD5 를
  import 할 수 없다). **필수**(Mapping 이 아니거나 값이 MetricSignature 가 아니면 `TypeError`). 빈 매핑이면 모든 제약이
  `metric_unknown` 으로 거부된다(조용히 통과하지 않음).
* 순서: `load_json_checked`(JSON 수준 위반은 그 예외 그대로) -> `check_spec_schema` -> `meta_cross_check` ->
  `supplies_declaration` -> `input_dc_declaration` -> `element_value_declaration` -> `constraint_declaration` ->
  `compensation_target_declaration` -> `node_target_declaration` -> `intended_region_declaration` ->
  `settings_declaration` -> `resolve_spec_references`.
* 위반이 하나라도 있으면 `SchemaRejectedError` 한 번(개수로 자르지 않음): detail = {"gate": "spec_load", "where": 경로,
  "hits", "rejected_gates", "not_evaluated"}. `not_evaluated`: `all_sections`(최상위·meta·human 이 객체가 아님),
  `topology_cross_checks`(meta 의 회로 이름·topology 지문 불일치 -- 다른 회로판 교차 검사는 의미가 없어 섹션 형식만 본다),
  `references`(앞 게이트 위반이 있으면 참조를 해석하지 않는다). 필수 human 키가 빠진 섹션은 `missing_key` 하나로 보고하고
  그 섹션 검사는 돌리지 않는다(같은 위반을 두 번 세지 않음).
* `value_from_file` 참조 대상은 같은 디렉터리의 `<회로>.topology.json`(`load_topology`)과 `<회로>.sizing_spec.json`(이
  로더)을 읽는다. 한 로드 안에서 같은 회로는 한 번만 읽는다(로드 지역 memo, 함수가 끝나면 버림). 로드 사슬에 이미 있는
  파일을 다시 가리키면 `ref_cycle`.
* 결과를 캐시하지 않는다(graph 밖 memo 는 LUT 하나뿐) -- 같은 경로를 두 번 부르면 두 번 읽는다. 실행당 1회 로드.
* 배선: 공개 진입점이며 아직 엔진 안 호출자는 없다(파이프라인 MOD10 이 S0 입력으로 부를 예정, CONTRACT 'spec 로더' 절).
"""
from collections.abc import Mapping
from pathlib import Path

from gmid_engine.core import MetricSignature, SchemaRejectedError

from ._rejection import reject
from .json_read import load_json_checked
from .spec_constraints import constraint_declaration
from .spec_elements import element_value_declaration
from .spec_input_dc import input_dc_declaration
from .spec_meta import SPEC_SUFFIX, meta_cross_check
from .spec_model import SizingSpecDoc
from .spec_node_targets import node_target_declaration
from .spec_refs import resolve_spec_references
from .spec_regions import intended_region_declaration
from .spec_schema import HUMAN_REQUIRED, check_spec_schema
from .spec_settings import settings_declaration
from .spec_supplies import supplies_declaration
from .spec_targets import compensation_target_declaration
from .topology_load import load_topology
from .topology_model import SchemaHit, TopologyDoc

_GATE = "spec_load"
_TOPOLOGY_SUFFIX = ".topology.json"
_META_MISMATCH_RULES = ("circuit_name_mismatch", "topology_fp_mismatch")


def load_sizing_spec(path, topology, metric_catalog):
    if not isinstance(topology, TopologyDoc):
        raise TypeError("load_sizing_spec: topology 는 load_topology 가 만든 TopologyDoc 이어야 한다: "
                        + type(topology).__qualname__)
    if not isinstance(metric_catalog, Mapping) or not all(
            isinstance(k, str) and isinstance(v, MetricSignature) for k, v in metric_catalog.items()):
        raise TypeError("load_sizing_spec: metric_catalog 는 {metric 이름: MetricSignature} 매핑이어야 한다")
    return _load(Path(path), topology, metric_catalog, ())


def _load(path, topology, catalog, chain):
    where = str(path)
    doc = load_json_checked(path, where)
    hits = []
    rejected = set()
    not_evaluated = []

    def run(gate, found):
        if found:
            rejected.add(gate)
            hits.extend(found)

    schema_hits, marks = check_spec_schema(doc.data)
    run("spec_schema", schema_hits)
    data = doc.data
    if not (isinstance(data, dict) and isinstance(data.get("meta"), dict) and isinstance(data.get("human"), dict)):
        reject(_GATE, where, hits, rejected_gates=tuple(sorted(rejected)), not_evaluated=("all_sections",))
    meta = data["meta"]
    human = data["human"]
    meta_hits = meta_cross_check(meta, topology, path)
    run("spec_meta", meta_hits)
    topo = topology
    if any(h.rule in _META_MISMATCH_RULES for h in meta_hits):
        topo = None
        not_evaluated.append("topology_cross_checks")

    def section(gate, key, parse, *args):
        if key in HUMAN_REQUIRED and key not in human:
            return None
        value, found = parse(human.get(key), *args)
        run(gate, found)
        return value

    supplies = section("supplies", "supplies_v", supplies_declaration, topo)
    input_dc = section("input_dc", "input_dc", input_dc_declaration, topo, supplies)
    elements = feedback = None
    if "element_values" in human and "feedback" in human:
        elements, feedback, found = element_value_declaration(human["element_values"], human["feedback"], topo)
        run("elements", found)
    constraints = pending_constraints = None
    if "constraints" in human:
        constraints, pending_constraints, found = constraint_declaration(
            human["constraints"], human.get("pending_constraints"), topo, catalog)
        run("constraints", found)
    targets = section("compensation_targets", "compensation_targets", compensation_target_declaration)
    node_targets = section("node_targets", "node_voltage_targets_v", node_target_declaration, topo)
    regions = section("intended_region", "intended_region", intended_region_declaration, topo)
    settings, found = settings_declaration(human, catalog)
    run("settings", found)
    if hits or not_evaluated:
        not_evaluated.append("references")
        reject(_GATE, where, hits, rejected_gates=tuple(sorted(rejected)), not_evaluated=tuple(not_evaluated))

    loaded = {}
    here = (path.resolve(),) + chain

    def load_referenced(circuit):
        if circuit not in loaded:
            loaded[circuit] = _load_referenced(path.parent, circuit, catalog, here)
        return loaded[circuit]

    constraints, targets, ref_marks, ref_hits = resolve_spec_references(constraints, targets, load_referenced)
    run("references", ref_hits)
    if hits:
        reject(_GATE, where, hits, rejected_gates=tuple(sorted(rejected)), not_evaluated=())
    objective, search, spice_check, front_refilter = settings
    sections = {
        "supplies_v": supplies, "input_dc": input_dc, "element_values": elements, "feedback": feedback,
        "constraints": constraints, "pending_constraints": pending_constraints, "compensation_targets": targets,
        "node_voltage_targets_v": node_targets, "intended_region": regions, "objective": objective,
        "search": search, "spice_check": spice_check, "front_refilter": front_refilter,
    }
    return SizingSpecDoc.from_sections(meta["circuit"], meta["topology_fp"], meta["origin"], sections,
                                       marks + ref_marks, doc.sha256)


def _load_referenced(directory, circuit, catalog, chain):
    """(doc 또는 None, rule, hits). rule 은 doc 이 None 일 때 바깥 hit 의 rule(spec_refs 계약)."""
    spec_path = directory / (circuit + SPEC_SUFFIX)
    if spec_path.resolve() in chain:
        return None, "ref_cycle", (SchemaHit("ref_cycle", str(spec_path), "참조 파일 사슬이 순환한다: " + str(spec_path),
                                             (circuit,)),)
    try:
        topology = load_topology(directory / (circuit + _TOPOLOGY_SUFFIX))
        return _load(spec_path, topology, catalog, chain), None, ()
    except SchemaRejectedError as exc:
        return None, "ref_file_rejected", tuple(dict(exc.record.detail)["hits"])
    except FileNotFoundError:
        return None, "ref_unresolved", (SchemaHit("ref_unresolved", str(spec_path), "참조 회로 파일이 없다: " + circuit,
                                                  (circuit,)),)
