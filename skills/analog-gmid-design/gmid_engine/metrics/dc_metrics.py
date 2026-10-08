"""봉인 DC 점 -> 전력·탐색 축 면적 metric 계산 블록 (설계 design_mod1_lut_mod5_mna 3.4 `supply_current_dc`·`power_dc_w`·
`area_search_m2`, 계획 DEC-78·DEC-79 (a), metrics CONTRACT 7절).

진입점: `metrics_dc`(`@compute_block`) -- `metrics_dc(snapshot, passive_values, counted_rails[, area_decl])`.

* reads `device.{dc_op, dc_current, element_class, pins}`, `node.{dc_v, dc_rail_v}`, `graph.dc_current_basis`;
  extras `passive_values` = ((수동소자, 값), ...)(DC 저항 값 = spec 선언 ∪ θ), `counted_rails` = 합산 레일 넷 tuple(DEC-78 선언 --
  기본값 없음). writes `graph.metrics_dc`(key `METRICS_KEY`) = `MetricBundle`(supply_current_dc·power_dc_w·area_search_m2).
* DC 점 레코드(`DcOperatingPoint`, 노드 인덱스 = 레일 ∪ 노드전압 넷 이름 정렬 위치):
  - MOS 채널: `basis.ends` 의 (from, to) 가 양의 전류 방향이므로 drain = from 이면 drain→source 전류 = +ID, 아니면 −ID
    (극성 표를 따로 두지 않는다).
  - DC 저항(`basis.resistors`, 잎 가지치기 제외 -- 가지치기 저항은 전류 0): 값은 `passive_values`.
  - 이상 전류원(ends 의 나머지 DC 원소): (from, to, `dc_current`) -- 선언값 또는 θ 전류.
* `counted_rails` = 합산 레일의 **넷 이름** tuple(노드 인덱스 아님). 레일(`dc_rail_v` 넷) 밖 이름(회로에 없는 넷 포함)·중복 ->
  ValueError(선언 결함, 2절 표 '합산 레일 선언' -- KeyError 는 미등록 metric 이름 전용).
* `counted_rails` 가 비면 `supply_current_dc` 는 정의 불가 `counted_rails_undeclared`(definitional) -- 레일별 전류·전력은 합산 선언과
  무관하므로 그대로 낸다(`supply_currents` 는 빈 선언을 거부하므로 레일 전부를 넘겨 부르고 합만 버린다).
* 면적: MOS 마다 `GateArea(W, L)`(dc_op), 값이 있는 수동소자 `PassiveArea(값, 단위 면적)`. 단위 면적과 제외 소자는 선택 extra
  `area_decl`(`PassiveAreaDecl`, 사용자 결정 11) -- 없으면(기본) 단위 면적 선언 없음·제외 없음이라 전부 `passive_area_undeclared`.
  `area_decl.excluded`(측정 부하)는 면적 항에서도 `passive_area_undeclared` 에서도 뺀다. 값이 없는 수동소자는 detail
  `passive_value_missing`.
"""
from gmid_engine.core import compute_block
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_PASSIVE, MOS_TERMINAL_NAMES
from gmid_engine.sizing import DC_KEY, METRICS_DC_WRITER, METRICS_KEY

from .area import area_search
from .evaluate import metric_value
from .mna_types import MetricResult, Undefined
from .records import ChannelCurrent, CurrentSource, DcOperatingPoint, GateArea, PassiveArea, PassiveAreaDecl, RailBias, Resistor
from .registry import metric_registry
from .ss_types import MetricBundle, MetricRequest
from .supply import supply_currents

READS = (
    ("device", "dc_op"), ("device", "dc_current"), ("device", "element_class"), ("device", "pins"),
    ("node", "dc_v"), ("node", "dc_rail_v"), ("graph", "dc_current_basis"), ("node", "dc_colour"), ("device", "dc_colour"),
)
WRITES = (("graph", "metrics_dc"),)
SUPPLY_METRICS = ("power_dc_w", "supply_current_dc")
AREA_METRICS = ("area_search_m2",)
CODE_COUNTED_RAILS = "counted_rails_undeclared"


def _canonical(projection, kind):
    """정렬 키: (구조 색 `dc_colour`, 이름) -- sizing 의 색은 1-WL 색 안을 정준 위치로 구분해 정점마다 유일하다(이름은 색이 없는 이름 뿐, 합산·행렬 순서가 이름을 따르지 않게)."""
    orbit = dict(projection.column(kind, "dc_colour"))
    return lambda name: (orbit.get(name, -1), name)


def _operating_point(projection, index, values):
    device_key = _canonical(projection, "device")
    basis = projection.value("graph", DC_KEY, "dc_current_basis")
    pins = dict(projection.column("device", "pins"))
    classes = dict(projection.column("device", "element_class"))
    currents = dict(projection.column("device", "dc_current"))
    rails = tuple(RailBias(index[n], v) for n, v in projection.column("node", "dc_rail_v"))
    resistors = frozenset(basis.resistors)
    channels, res, sources, touched = [], [], [], set()
    for name, a, b in sorted(basis.ends, key=lambda e: device_key(e[0])):
        if classes[name] == ELEMENT_MOS:
            d, _g, s = (dict(pins[name])[t] for t in MOS_TERMINAL_NAMES)
            channels.append(ChannelCurrent(index[d], index[s], currents[name] if d == a else -currents[name]))
        elif name in resistors:
            res.append(Resistor(index[a], index[b], values[name], label=name))
            touched.update((a, b))
        elif classes[name] != ELEMENT_PASSIVE:
            sources.append(CurrentSource(index[a], index[b], currents[name]))
    volts = dict(projection.column("node", "dc_v"))
    node_v = tuple((index[n], volts[n]) for n in sorted(touched, key=index.get) if n in volts)
    return DcOperatingPoint(rails, node_v, tuple(channels), tuple(res), tuple(sources))


@compute_block(METRICS_DC_WRITER, reads=READS, writes=WRITES)
def metrics_dc(projection):
    passive_values, counted_rails, *rest = projection.extras
    area_decl = rest[0] if rest else PassiveAreaDecl()
    values = dict(passive_values)
    node_key = _canonical(projection, "node")
    device_key = _canonical(projection, "device")
    names = sorted({n for n, _v in projection.column("node", "dc_rail_v")} | {n for n, _v in projection.column("node", "dc_v")},
                   key=node_key)
    index = {net: i for i, net in enumerate(names)}
    op = _operating_point(projection, index, values)
    rails = {n for n, _v in projection.column("node", "dc_rail_v")}
    outside = tuple(n for n in counted_rails if n not in rails)
    if outside or len(set(counted_rails)) != len(counted_rails):
        raise ValueError("metrics_dc: 합산 레일 선언 결함(레일 밖 넷 %r 또는 중복 %r) -- counted_rails 는 레일 넷 이름"
                         % (outside, tuple(counted_rails)))
    counted = tuple(index[n] for n in counted_rails) or tuple(r.node for r in op.rails)
    supply = supply_currents(op, counted)
    classes = dict(projection.column("device", "element_class"))
    gates = tuple(GateArea(o.W, o.L, label=m) for m, o in sorted(projection.column("device", "dc_op"), key=lambda r: device_key(r[0])))
    passives = sorted((n for n, c in classes.items() if c == ELEMENT_PASSIVE), key=device_key)
    unit = dict(area_decl.unit_area)
    area = area_search(gates, tuple(PassiveArea(n, values[n], unit.get(n)) for n in passives
                                    if values.get(n) is not None and n not in area_decl.excluded))
    entries = []
    for name in SUPPLY_METRICS + AREA_METRICS:
        result = metric_value(name, supply if name in SUPPLY_METRICS else area)
        if name == "supply_current_dc" and not counted_rails:
            field = metric_registry()[name].field
            result = MetricResult(name, None, (Undefined(field, CODE_COUNTED_RAILS, "definitional"),))
        elif result.value is not None:
            result = MetricResult(name, float(result.value), result.undefined)
        entries.append((MetricRequest(name), result))
    detail = (
        ("counted_rails", tuple(counted_rails)),
        ("kcl_residual_amp", float(supply.kcl_residual_amp)),
        ("passive_area_undeclared", tuple(area.passive_area_undeclared)),
        ("passive_value_missing", tuple(n for n in passives if values.get(n) is None)),
        ("per_rail_amp", tuple((names[k], float(i)) for k, i in supply.per_rail)),
    )
    return {("graph", "metrics_dc"): {METRICS_KEY: MetricBundle(tuple(entries), (), detail)}}
