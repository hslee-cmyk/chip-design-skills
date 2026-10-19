"""MOD7 이름 정준 별칭표 계산 블록 (사용자 대원칙 '이름에 종속된 엔진 금지', U12 -- 사용자 지시 2026-10-09; 설계 40 v1.11.2 §2.4.8 '레이아웃 정준
별칭표' 행, 사용자 결정 O-36 (3)·O-39 (1)).

진입점: `canon_tables` -- core `@compute_block`(writer `ly_canonical_naming`, reads device `ly_point`·`ly_pins`·`ly_w_adjustable`·`ly_attrs`,
graph `ly_groups_in`·`ly_row_groups`·`ly_passives`, writes graph `ly_canon`·`ly_canon_rows`).

레이아웃 입력(소자 d·g·s·body 연결, 소자 종류·L·ID·gm/ID·W·VDS·VSB·diode, matching 그룹 소속·역할·hub 넷)을 회로 그래프로 보고
`graph.canonical_form` 의 정준 위치(이름 전단사에 불변, 남는 동률 = 자기동형 궤도)를 한 번 구한다. 소자·넷은 그 위치 순서로 별칭을 받는다
(`D000001`..., `N000001`...). matching 그룹·행 그룹·수동소자는 이름이 아닌 내용 키(역할·멤버 위치·hub 위치 / kind·body 위치·멤버 위치 /
면적)로 정렬해 별칭을 받는다. 별칭 범위가 다른 두 표를 쓴다 -- `ly_canon`(소자·넷·matching 그룹, `ly_pattern_select` 가 읽는다)과
`ly_canon_rows`(위 + 행 그룹·수동소자, `ly_rows` 가 읽는다). 별칭표를 만들 수 없으면(별칭 충돌) 그 표는 빈 `Canon` -- 번역 없음.
이 별칭은 계산 블록 안의 이름 정렬·동률 처리가 구조 정준 순서를 따르게 하는 수단이다(`canonical_naming.canonical_names` 가 읽어 번역한다).
참고 W(`ly_attrs` 의 `W_m`)는 정준 표지다 -- 정준 색은 표지 값의 순위로 정해지므로 W 가 바뀌면 이 블록은 다시 계산된다(별칭표 값이 같으면
아래 블록은 다시 계산하지 않는다).
"""
import collections
import dataclasses
import types

from gmid_engine.core import compute_block
from gmid_engine.graph import canonical_form

from ._helpers_alias import Canon
from ._ly_fields import (
    DEVICE,
    F_ATTRS,
    F_CANON,
    F_CANON_ROWS,
    F_GROUPS_IN,
    F_PASSIVES,
    F_PINS,
    F_POINT,
    F_ROW_GROUPS,
    F_W_ADJ,
    GRAPH,
    GRAPH_KEY,
    WRITER_CANON,
)

_MOS = "mos"


@dataclasses.dataclass(frozen=True)
class _Device:
    """네 입력 필드의 소자 칸을 이름 하나로 모은 값(이 블록 안에서만)."""

    name: str
    kind: str
    L_m: float
    ID_A: float
    gm_id: float
    vds_V: float
    vsb_V: float
    drain: str
    gate: str
    source: str
    W_adjustable: bool
    W_m: float
    body: str
    diode: bool


class _Source:
    """`canonical_form` 이 읽는 `.column(kind, field)` 만 가진 레이아웃 입력 어댑터."""

    def __init__(self, devices):
        nets = sorted({n for d in devices for n in (d.drain, d.gate, d.source, d.body)})
        self._columns = {
            ("device", "element_class"): [(d.name, _MOS) for d in devices],
            ("device", "kind"): [(d.name, d.kind) for d in devices],
            ("device", "is_diode"): [(d.name, d.diode) for d in devices],
            ("device", "pins"): [(d.name, (("d", d.drain), ("g", d.gate), ("s", d.source))) for d in devices],
            ("device", "bulk"): [(d.name, types.SimpleNamespace(net=d.body)) for d in devices],
            ("node", "port_direction"): [(n, None) for n in nets],
            ("node", "is_rail"): [(n, False) for n in nets],
        }

    def column(self, kind, field):
        return self._columns[(kind, field)]


def _marks(devices, groups):
    """소자·넷 선언 표시(이름 없는 수치·소속) -- 자기동형이 값과 matching 소속을 보존하게 한다."""
    member_of = collections.defaultdict(collections.Counter)
    hub_of = collections.Counter()
    for g in groups:
        size = len(g.members)
        for m in g.members:
            member_of[m][(g.role, size)] += 1
        if g.hub_net is not None:
            hub_of[g.hub_net] += 1
    element = []
    for d in devices:
        values = [("ID", d.ID_A), ("L", d.L_m), ("W", d.W_m), ("gm_id", d.gm_id), ("vds", d.vds_V), ("vsb", d.vsb_V),
                  ("adj", float(d.W_adjustable))]
        values += [("grp:%s:%d" % key, float(n)) for key, n in member_of[d.name].items()]
        element.append((d.name, tuple(sorted(values))))
    node = [(n, (("hub", float(c)),)) for n, c in hub_of.items()]
    return tuple(element), tuple(node)


def _alias_table(prefix, ordered):
    return [(name, "%s%06d" % (prefix, i + 1)) for i, name in enumerate(ordered)]


def _canon(pairs, groups):
    """별칭 쌍 -> `Canon`. 별칭 충돌(이름 또는 별칭이 겹침)이면 빈 `Canon`."""
    if len({a for _, a in pairs}) != len(pairs) or len({n for n, _ in pairs}) != len(pairs):
        return Canon()
    return Canon(tuple(pairs), tuple((g.gid, g.members) for g in groups))


def _build(devices, groups, row_groups, passives):
    """(matching 범위 `Canon`, 행 범위 `Canon`) -- 정준 위치는 한 번 구해 둘이 같이 쓴다."""
    element_marks, node_marks = _marks(devices, groups)
    canonical = canonical_form(_Source(devices), element_marks, node_marks)
    pos = canonical.position
    dev_pos = {d.name: pos[("e", d.name)] for d in devices}
    net_pos = {n: pos[("n", n)] for d in devices for n in (d.drain, d.gate, d.source, d.body)}
    dev_names = sorted(dev_pos, key=dev_pos.get)
    net_names = sorted(net_pos, key=net_pos.get)
    group_key = lambda g: (g.role, tuple(sorted(dev_pos[m] for m in g.members)),  # noqa: E731
                           -1 if g.hub_net is None else net_pos[g.hub_net], g.allowed_patterns)
    gids = [g.gid for g in sorted(groups, key=group_key)]
    row_key = lambda r: (r.kind, net_pos[r.body_net], tuple(sorted(dev_pos[m] for m in r.members)))  # noqa: E731
    rids = [r.rid for r in sorted(row_groups, key=row_key)]
    pnames = [p.name for p in sorted(passives, key=lambda p: (p.area_m2, p.name))]
    matching = _alias_table("D", dev_names) + _alias_table("N", net_names) + _alias_table("G", gids)
    return _canon(matching, groups), _canon(matching + _alias_table("R", rids) + _alias_table("P", pnames), groups)


@compute_block(
    WRITER_CANON,
    reads=((DEVICE, F_POINT), (DEVICE, F_PINS), (DEVICE, F_W_ADJ), (DEVICE, F_ATTRS),
           (GRAPH, F_GROUPS_IN), (GRAPH, F_ROW_GROUPS), (GRAPH, F_PASSIVES)),
    writes=((GRAPH, F_CANON), (GRAPH, F_CANON_ROWS)),
)
def canon_tables(projection):
    """정준 별칭표 둘: graph `ly_canon`(소자·넷·matching 그룹) / `ly_canon_rows`(위 + 행 그룹·수동소자)."""
    pins = dict(projection.column(DEVICE, F_PINS))
    adjustable = dict(projection.column(DEVICE, F_W_ADJ))
    attrs = dict(projection.column(DEVICE, F_ATTRS))
    devices = tuple(
        _Device(name, p.kind, p.L_m, p.ID_A, p.gm_id, p.vds_V, p.vsb_V, pins[name].drain, pins[name].gate, pins[name].source,
                adjustable[name], attrs[name].W_m, attrs[name].body, attrs[name].diode)
        for name, p in sorted(projection.column(DEVICE, F_POINT), key=lambda item: item[0]))
    value = lambda field: tuple(projection.value(GRAPH, GRAPH_KEY, field))  # noqa: E731
    matching, with_rows = _build(devices, value(F_GROUPS_IN), value(F_ROW_GROUPS), value(F_PASSIVES))
    return {(GRAPH, F_CANON): {GRAPH_KEY: matching}, (GRAPH, F_CANON_ROWS): {GRAPH_KEY: with_rows}}
