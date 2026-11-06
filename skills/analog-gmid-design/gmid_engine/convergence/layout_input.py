"""봉인 스냅샷 -> MOD7 `LayoutInput` 어댑터 (계획 N3.17 '레이아웃 입력·출력 계약', graph CONTRACT 4.5a 전달 정책, 설계 40 §3.9 U14).

진입점: `layout_input_of(snapshot, pdk, passives, rejected=(), relaxed=()) -> (LayoutInput, undelivered)`.

* `snapshot` = 봉인 점의 S2 스냅샷(`EvalResult.evaluation.snapshot` -- S1 필드와 `dc_op`·`dc_coord` 가 든다). 소자(MOS) 마다 `LayoutDevice`:
  kind·L·ID·gm/ID(보존량)·VDS·VSB 는 `dc_op`, 단자 넷·body 넷·diode 는 S1 `pins`·`bulk`·`is_diode`, 참고 W = `dc_op.W`.
  `W_adjustable` = sizing 이 그 소자 W 를 고정 입력으로 받을 수 있는지 = `dc_coord` 가 쓰기 소자(`COORD_WRITER` -- `size_and_seal(w_request=)` 가 좌표를
  ln(ID·L/W) 로 바꾸는 소자). 종속 소자는 KCL 이 전류를 정해 W 를 따로 못 정한다.
* matching 그룹 = S1 `matching_groups` 중 status derived·ratified 만(graph CONTRACT 4.5a '레이아웃 전달 정책' -- review_needed 는 matching 없이 배치),
  S1 `matching_dispositions` 중 bias_distribution·feedback_shared(멤버 2 이상)는 제외 role 그룹. role 은 S1 kind 와 같은 낱말이고 hub 넷 = 차동쌍 evidence 첫 넷
  (공통 source), 미러 evidence (gate, source) 의 source, branch_symmetric 은 hub 없음. 허용 패턴은 전부. gid = 규칙·멤버로 만든 문자열(이름 치환을 따라간다).
* 완화(`relaxed` = 완화할 gid 집합, LY5 MOD8 판정): 그 그룹의 role 을 `mirror`(hub-leaf 쌍의 일반 role), 허용 패턴을 interdigitation 만으로 바꿔 넘긴다.
  hub 없는 그룹은 바꾸지 않는다(호출부가 걸러 `not_relaxable` 로 기록).
* 행 그룹 = (kind, body 넷) 마다 하나(`LayoutInput` 불변식 '소자 (kind, body) == 행 그룹'). 한 그룹의 멤버가 둘 이상의 행 그룹에 걸치면 그 그룹은 넘기지 않고
  `undelivered` 에 ((gid, 사유), ...) 로 돌려준다(조용히 버리지 않는다).
* `passives` = `layout.passives_from_decl` 결과(호출부), `rejected` = 거부한 W_request 소자 이름, `excluded` = ((행 그룹 rid, (뺀 폭 키, ...)), ...) -- `key_exclusion` 이 행 그룹 단위로 뺀 폭 후보
  (그 행 그룹 `RowGroup.excluded_keys` 로 넘긴다; 다른 행 그룹의 후보는 그대로).
"""
from gmid_engine.graph import (
    DISPOSITION_BIAS_DISTRIBUTION,
    DISPOSITION_FEEDBACK_SHARED,
    GRAPH_KEY,
    MATCH_BRANCH_SYMMETRIC,
    MATCH_DIFF_PAIR,
    MATCH_MIRROR,
    MOS_TERMINAL_NAMES,
    STATUS_DERIVED,
    STATUS_RATIFIED,
)
from gmid_engine.layout import (
    EXCLUDED_ROLES,
    PATTERN_INTERDIGITATION,
    PATTERNS,
    ROLE_BIAS_DISTRIBUTION,
    ROLE_BRANCH_SYMMETRIC,
    ROLE_DIFF_PAIR,
    ROLE_FEEDBACK_SHARED,
    ROLE_MIRROR,
    LayoutDevice,
    LayoutInput,
    MatchingGroup,
    RowGroup,
)
from gmid_engine.sizing import COORD_WRITER

_DELIVERED = (STATUS_DERIVED, STATUS_RATIFIED)
_ROLE_OF_MATCH = ((MATCH_DIFF_PAIR, ROLE_DIFF_PAIR), (MATCH_MIRROR, ROLE_MIRROR), (MATCH_BRANCH_SYMMETRIC, ROLE_BRANCH_SYMMETRIC))
_ROLE_OF_DISPOSITION = ((DISPOSITION_BIAS_DISTRIBUTION, ROLE_BIAS_DISTRIBUTION), (DISPOSITION_FEEDBACK_SHARED, ROLE_FEEDBACK_SHARED))
_SPAN = "members_span_row_groups"
_HUB_INDEX = ((MATCH_DIFF_PAIR, 0), (MATCH_MIRROR, 1))     # evidence.nets 안 hub(공통 source) 위치 -- graph CONTRACT 4.5a 표


def _hub(group):
    index = dict(_HUB_INDEX).get(group.kind)
    return None if index is None or len(group.evidence.nets) <= index else group.evidence.nets[index]


def _gid(tag, members):
    return tag + "|" + "+".join(sorted(members))


def layout_input_of(snapshot, pdk, passives, rejected=(), relaxed=(), excluded=()):
    ops = dict(snapshot.column("device", "dc_op"))
    diode = dict(snapshot.column("device", "is_diode"))
    coords = dict(snapshot.column("device", "dc_coord"))
    devices, body_of = [], {}
    for name in sorted(ops):
        op = ops[name]
        pins = dict(snapshot.value("device", name, "pins"))
        d, g, s = (pins[t] for t in MOS_TERMINAL_NAMES)
        body = snapshot.value("device", name, "bulk").net
        body_of[name] = (op.kind, body)
        devices.append(LayoutDevice(name, op.kind, d, g, s, body, float(op.W), float(op.L), float(op.current), float(op.gm_id),
                                    float(op.vds), float(op.vsb), bool(diode[name]), coords[name].role == COORD_WRITER))
    row_members = {}
    for name, key in body_of.items():
        row_members.setdefault(key, []).append(name)
    dropped = dict(excluded)
    row_groups = tuple(RowGroup(key[0] + "|" + key[1], key[0], key[1], tuple(sorted(members)), tuple(sorted(dropped.get(key[0] + "|" + key[1], ()))))
                       for key, members in sorted(row_members.items()))
    relaxed = frozenset(relaxed)
    groups, undelivered = [], []
    delivered = tuple(g for g in snapshot.value("graph", GRAPH_KEY, "matching_groups") if g.status in _DELIVERED)
    for g in delivered:
        role = dict(_ROLE_OF_MATCH)[g.kind]
        members = tuple(sorted(g.members))
        gid = _gid(g.evidence.rule, members)
        hub = _hub(g)
        patterns = tuple(PATTERNS)
        if gid in relaxed and hub is not None:
            role, patterns = ROLE_MIRROR, (PATTERN_INTERDIGITATION,)
        groups.append((gid, members, role, hub, patterns))
    for g in snapshot.value("graph", GRAPH_KEY, "matching_dispositions"):
        role = dict(_ROLE_OF_DISPOSITION).get(g.kind)
        if role is not None and len(g.members) > 1:        # 그룹은 멤버 둘 이상(LayoutInput 불변식)
            members = tuple(sorted(g.members))
            groups.append((_gid(g.kind, members), members, role, None, tuple(PATTERNS)))
    matching = []
    for gid, members, role, hub, patterns in groups:
        spans = {body_of[m] for m in members if m in body_of}
        if role not in EXCLUDED_ROLES and len(spans) > 1:
            undelivered.append((gid, _SPAN))
            continue
        matching.append(MatchingGroup(gid, members, role, hub, patterns))
    layout_input = LayoutInput(tuple(devices), tuple(matching), row_groups, pdk, tuple(sorted(rejected)), tuple(passives))
    return layout_input, tuple(undelivered)
