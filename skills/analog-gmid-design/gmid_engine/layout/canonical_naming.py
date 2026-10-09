"""MOD7 이름 정준 별칭표 만들기 `build_canon` (사용자 대원칙 '이름에 종속된 엔진 금지', U12 -- 사용자 지시 2026-10-09).

진입점: `canonical_names` -- 계산 블록 함수 데코레이터(`compute_block` 안쪽). 블록은 `reads` 에 소자 `ly_device` 와 graph `ly_groups_in`·`ly_row_groups`·`ly_passives`·`ly_rejected`
를 선언해야 한다(별칭표를 이 입력 필드에서 만든다). 별칭표 = 모듈 안 `_build`.

레이아웃 입력(소자 d·g·s·body 연결, 소자 종류·L·ID·gm/ID·W·VDS·VSB·diode, matching 그룹 소속·역할·hub 넷)을 회로 그래프로 보고
`graph.canonical_form` 의 정준 위치(이름 전단사에 불변, 남는 동률 = 자기동형 궤도)를 구한다. 소자·넷은 그 위치 순서로 별칭을 받는다
(`D000001`..., `N000001`...). matching 그룹·행 그룹·수동소자는 이름이 아닌 내용 키(역할·멤버 위치·hub 위치 / kind·body 위치·멤버 위치 /
면적)로 정렬해 별칭을 받는다. 별칭표를 만들 수 없으면(별칭 충돌) 빈 `Canon` -- 번역 없음.
이 별칭은 계산 블록 안의 이름 정렬·동률 처리가 구조 정준 순서를 따르게 하는 수단이다(`canonical_names`).
"""
import collections
import functools
import types

from gmid_engine.graph import canonical_form

from ._ly_fields import DEVICE, F_DEVICE, F_GROUPS_IN, F_PASSIVES, F_REJECTED, F_ROW_GROUPS, GRAPH, GRAPH_KEY
from ._helpers_alias import AliasView, Canon

_MOS = "mos"


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


def _build(devices, groups, row_groups, passives, rejected):
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
    pairs = (_alias_table("D", dev_names) + _alias_table("N", net_names) + _alias_table("G", gids)
             + _alias_table("R", rids) + _alias_table("P", pnames))
    if len({a for _, a in pairs}) != len(pairs) or len({n for n, _ in pairs}) != len(pairs):
        return Canon()
    return Canon(tuple(pairs), tuple((g.gid, g.members) for g in groups))


def canonical_names(rows=False):
    """계산 블록 함수 데코레이터 공장: 블록이 읽는 이름을 구조 정준 별칭으로 바꿔 건네고 쓴 결과를 이름으로 되돌린다(`_helpers_alias`).
    `rows=True` 면 행 그룹·수동소자도 별칭을 받는다(블록이 `ly_row_groups`·`ly_passives` 를 읽을 때만 -- 안 읽는 블록의 캐시 키를 넓히지 않는다)."""

    def decorate(fn):
        @functools.wraps(fn)
        def run(projection):
            devices = tuple(sorted((d for _, d in projection.column(DEVICE, F_DEVICE)), key=lambda d: d.name))
            value = lambda field: tuple(projection.value(GRAPH, GRAPH_KEY, field))  # noqa: E731
            canon = _build(devices, value(F_GROUPS_IN), value(F_ROW_GROUPS) if rows else (),
                           value(F_PASSIVES) if rows else (), value(F_REJECTED))
            result = fn(AliasView(projection, canon))
            return {key: {k: canon.real_order(v) for k, v in canon.to_name(columns).items()}
                    for key, columns in result.items()}

        return run

    return decorate
