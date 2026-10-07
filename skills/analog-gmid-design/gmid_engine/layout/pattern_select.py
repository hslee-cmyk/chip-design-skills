"""MOD7 matching 그룹 패턴 선택 계산 블록 -- 행 구성 단계에서 먼저, 패턴표 우선 (계획 N3.17 LY4·LY5·LY6, design 3절 2단계).

진입점: `pattern_select` -- core `@compute_block`(writer `ly_pattern_select`, reads device `ly_device`·`ly_fw_cand`,
graph `ly_pdk`·`ly_groups_in`·`ly_rejected`, writes graph `ly_groups`).

그룹마다 독립으로, 전 그룹을 판정한다(첫 실패에서 멈추지 않음, LY6):
1. 멤버를 hub 넷 쪽이 source 가 되게 세운다(MOS source/drain 대칭). hub 가 없거나 멤버가 hub 에 닿지 않거나 leaf 가
   겹치면 패턴 함수 전제 밖 -- 사유를 기록하고 패턴 없이 둔다(행 Euler 가 처리).
2. 후보 = 멤버 모두에게 상한 안인 공통 finger_w(같은 unit geometry) x 멤버별 nf(내림·올림) 조합.
3. 후보마다 복사 패턴 함수를 부른다:
   common-centroid -- nf 같고 nf >= 멤버 수면 `n_rows=None`(회전 exact), 2멤버 nf 다르면 `n_rows=멤버 수`(표 경로 -> 탐색),
   그 밖은 전제 밖. `max_candidates` = 그룹 총 finger 수(리터럴 없음).
   interdigitation -- `INTERDIGITATION_PATTERNS` 에서 글자 수 = 멤버 수이고 어떤 repeat 의 글자별 개수가 멤버 nf 와
   정확히 같은 base 를 골라 넘긴다(표 경로 실사용, 멤버<->글자 = nf 내림차순 + 이름). 없으면 base=None(탐색).
4. 정렬 키(사전식, 상수 가중치 없음): (무게중심 일치 아님, 방법(표·회전 0 / 탐색 1), crossover, 고립쌍, residual,
   행 폭 합 sum(nf x (L + PDK 여유)) 의 격자 칸 수, 최대 W 오차, 폭 키, 패턴, nf). 앞 다섯 칸이 최소(완전)인 후보를 찾은 뒤
   더 넓은 후보는 키가 앞설 수 없으므로 평가하지 않는다.
5. 차동쌍(LY5): common-centroid 만 먼저 -> (i) 무게중심 일치 후보가 있으면 채택(같은 총 W 에서 nf 조정)
   (ii) 없고 멤버 모두 `W_adjustable`·MOD8 거부 없음이면 `W_request`(nf = 멤버 수, finger_w = 특성화 폭 중
   max W / 멤버 수 에 가장 가까운 것, 모든 멤버 같은 값) + `pending`(배치는 잠정) (iii) 그 밖이면 interdigitation 완화
   + `relaxed=True`. 시도는 순서대로 전부 `attempts` 에 남긴다.
node_sequence 는 `canonical_row` 로 정규화한다.
"""
import itertools
from collections import Counter
from fractions import Fraction

from gmid_engine.core import compute_block

from ._ly_fields import (
    DEVICE,
    F_DEVICE,
    F_FW_CAND,
    F_GROUPS,
    F_GROUPS_IN,
    F_PDK,
    F_REJECTED,
    GRAPH,
    GRAPH_KEY,
    WRITER_GROUPS,
)
from .canonical_rows import canonical_row
from .contract_input import PATTERN_COMMON_CENTROID, PATTERN_INTERDIGITATION, PATTERNS, ROLE_DIFF_PAIR
from .contract_output import GroupAttempt, GroupLayout, PatternRow, WRequest
from .patterns_common_centroid import COMMON_CENTROID_PATTERNS, common_centroid_layout
from .patterns_interdigitate import INTERDIGITATION_PATTERNS, interdigitate_layout
from .transistor import Transistor

_EXACT_METHODS = ("pattern_table", "rotation_exact")
# 표 경로(`_try_pattern_table_match`)가 받는 멤버 수 = 표 key 의 글자 종류 수(복사본은 2-소자 표만 쓴다).
_TABLE_MEMBERS = len(set("".join(min(COMMON_CENTROID_PATTERNS))))


def _orient(group, devices):
    """(hub 쪽이 source 인 (이름, source, drain) tuple, None) 또는 (None, 사유)."""
    hub = group.hub_net
    if hub is None:
        return None, "no_hub_net"
    ends = []
    for name in group.members:
        d = devices[name]
        if d.source == hub:
            ends.append((name, d.source, d.drain))
        elif d.drain == hub:
            ends.append((name, d.drain, d.source))
        else:
            return None, "member_not_on_hub:" + name
    if len({leaf for _, _, leaf in ends}) != len(ends):
        return None, "leaf_net_shared"
    return tuple(ends), ""


def _table_base(names, nf_of):
    """(base, 글자 정렬 순 멤버 이름) -- 표에 맞는 base 가 없으면 (None, nf 내림차순·이름 순)."""
    order = sorted(names, key=lambda n: (-nf_of[n], n))
    for base in sorted(INTERDIGITATION_PATTERNS):
        table = INTERDIGITATION_PATTERNS[base]
        letters = sorted(set(table[min(table)]))
        if len(letters) != len(order):
            continue
        for rep in sorted(table):
            counts = Counter(table[rep])
            letter_order = sorted(letters, key=lambda ch: (-counts[ch], ch))
            if [counts[ch] for ch in letter_order] == [nf_of[n] for n in order]:
                mapping = dict(zip(letter_order, order))
                return base, tuple(mapping[ch] for ch in letters)
    return None, tuple(order)


def _offsets(rows, members):
    """멤버 무게중심(finger 피치 단위, 행 가운데 기준)의 x·y 최대 차 -- 정확한 유리수로 계산."""
    sums = {m: [0, 0, 0] for m in members}
    n_rows = len(rows)
    for r, row in enumerate(rows):
        length = len(row.transistor_sequence)
        for i, name in enumerate(row.transistor_sequence):
            acc = sums[name]
            acc[0] += 2 * i - (length - 1)
            acc[1] += 2 * r - (n_rows - 1)
            acc[2] += 1
    xs = [Fraction(acc[0], 2 * acc[2]) for acc in sums.values() if acc[2]]
    ys = [Fraction(acc[1], 2 * acc[2]) for acc in sums.values() if acc[2]]
    return max(xs) - min(xs), max(ys) - min(ys)


def _pattern_rows(result, transistors):
    out = []
    for row in result["rows"]:
        row = canonical_row(row, transistors)
        segments = tuple((tuple(s["transistor_sequence"]), tuple(s["node_sequence"])) for s in row.get("segments") or ())
        out.append(PatternRow(tuple(row["transistor_sequence"]), tuple(row["node_sequence"]), segments,
                              tuple(row.get("crossover_after") or ())))
    return tuple(out)


class _Evaluator:
    """그룹 하나의 후보 평가기(블록 호출 안에서만 산다 -- 같은 패턴 호출은 한 번만)."""

    def __init__(self, group, ends, devices, fw_cand, pdk):
        self.group = group
        self.ends = ends
        self.devices = devices
        self.fw_cand = fw_cand
        self.pdk = pdk
        self.calls = {}
        self.attempts = []
        self.combos = self._combos()

    def _combos(self):
        """(폭 키, 멤버별 FingerCandidate) 후보를 (행 폭 칸 수, 최대 오차, 폭 키) 순으로."""
        members = self.group.members
        ok = {n: [c for c in self.fw_cand[n] if c.ok] for n in members}
        keys = set.intersection(*[{c.finger_w_key for c in ok[n]} for n in members])
        grid = self.pdk.manufacturing_grid_m
        out = []
        for key in sorted(keys):
            options = [tuple(c for c in ok[n] if c.finger_w_key == key) for n in members]
            for choice in itertools.product(*options):
                width = sum(c.n_fingers * (self.devices[n].L_m + self.pdk.finger_pitch_overhead_m)
                            for n, c in zip(members, choice))
                out.append((int(width // grid), max(c.err_rel for c in choice), key, choice))
        return sorted(out, key=lambda item: item[:-1])

    def _call(self, pattern, nf_of):
        members = self.group.members
        ends = {name: (s, d) for name, s, d in self.ends}
        total = sum(nf_of.values())
        if pattern == PATTERN_COMMON_CENTROID:
            nfs = [nf_of[n] for n in members]
            equal = len(set(nfs)) == 1
            if equal and nfs[0] >= len(members):
                n_rows = None
            elif not equal and len(members) == _TABLE_MEMBERS:
                n_rows = len(members)
            else:
                return None, "cc_precondition"
            order = tuple(members)
            arg = n_rows
        else:
            base, order = _table_base(members, nf_of)
            arg = base
        trs = [Transistor(n, self.devices[n].kind, source=ends[n][0], drain=ends[n][1], n_fingers=nf_of[n])
               for n in order]
        memo_key = (pattern, arg, tuple((t.name, t.n_fingers) for t in trs))
        if memo_key not in self.calls:
            if pattern == PATTERN_COMMON_CENTROID:
                result = common_centroid_layout(trs, n_rows=arg, max_candidates=total)
            else:
                result = interdigitate_layout(trs, base=arg)
            self.calls[memo_key] = (result, trs)
        return self.calls[memo_key], ""

    def best(self, patterns, step):
        """`patterns` 로 후보 전부(완전 후보 뒤 더 넓은 것은 생략)를 평가해 최선 (정렬 키, 결과 묶음) 또는 None."""
        best = None
        for width_cells, max_err, key, choice in self.combos:
            if best is not None and best[0][:5] == (0, 0, 0, 0, 0.0) and width_cells > best[0][5]:
                break
            nf_of = {n: c.n_fingers for n, c in zip(self.group.members, choice)}
            nfs = tuple(nf_of[n] for n in self.group.members)
            realized = tuple(c.W_realized_m for c in choice)
            for pattern in patterns:
                called, reason = self._call(pattern, nf_of)
                if called is None:
                    self.attempts.append(GroupAttempt(step, pattern, choice[0].finger_w_m, nfs, realized, None, None,
                                                      None, False, reason))
                    continue
                result, trs = called
                rows = _pattern_rows(result, trs)
                dx, dy = _offsets(rows, self.group.members)
                centred = dx == 0 and dy == 0
                self.attempts.append(GroupAttempt(step, pattern, choice[0].finger_w_m, nfs, realized, result["method"],
                                                  float(dx), float(dy), centred, "evaluated"))
                sort_key = (0 if centred else 1, 0 if result["method"] in _EXACT_METHODS else 1,
                            result["crossover_count"], result["isolated_pairs"], float(result["residual"]),
                            width_cells, max_err, key, pattern, nfs)
                if best is None or sort_key < best[0]:
                    best = (sort_key, pattern, result, rows, choice, dx, dy)
        return best


def _layout(group, chosen, attempts, *, relaxed=False, pending=False, reason="", w_requests=()):
    members = group.members
    if chosen is None:
        return GroupLayout(group.gid, group.role, members, None, None, None, None, (), (), None, None, None, None, None,
                           False, relaxed, pending, False, reason, tuple(attempts), tuple(w_requests))
    sort_key, pattern, result, rows, choice, dx, dy = chosen
    return GroupLayout(group.gid, group.role, members, pattern, result["method"], choice[0].finger_w_key,
                       choice[0].finger_w_m, tuple((n, c.n_fingers) for n, c in zip(members, choice)), rows,
                       float(result["residual"]), result["crossover_count"], result["isolated_pairs"], float(dx),
                       float(dy), sort_key[0] == 0, relaxed, pending, pending, reason, tuple(attempts),
                       tuple(w_requests))


def _w_requests(group, devices, pdk, keys):
    n = len(group.members)
    target = max(devices[m].W_m for m in group.members) / n
    grid = pdk.manufacturing_grid_m
    key = min(keys, key=lambda k: (abs(k * grid - target), k))
    w_new = n * key * grid
    return tuple(WRequest(m, devices[m].W_m, w_new, "cc_nf", group.gid) for m in group.members)


def _why(chosen, ev, ok_reason):
    if chosen is not None:
        return ok_reason
    return "no_applicable_pattern" if ev.combos else "no_common_finger_w"


def _place(group, devices, fw_cand, pdk, rejected):
    ends, reason = _orient(group, devices)
    if ends is None:
        attempt = GroupAttempt("precondition", None, None, (), (), None, None, None, False, reason)
        return _layout(group, None, [attempt], reason=reason)
    ev = _Evaluator(group, ends, devices, fw_cand, pdk)
    allowed = tuple(p for p in PATTERNS if p in group.allowed_patterns)
    if group.role != ROLE_DIFF_PAIR:
        chosen = ev.best(allowed, "select")
        return _layout(group, chosen, ev.attempts, reason=_why(chosen, ev, "selected"))
    chosen = ev.best((PATTERN_COMMON_CENTROID,), "cc_same_W")
    if chosen is not None and chosen[0][0] == 0:
        return _layout(group, chosen, ev.attempts, reason="cc_same_W")
    adjustable = all(devices[m].W_adjustable and m not in rejected for m in group.members)
    if adjustable:
        keys = dict(pdk.slice_width_keys)[devices[group.members[0]].kind]
        requests = _w_requests(group, devices, pdk, keys)
        ev.attempts.append(GroupAttempt("w_request", PATTERN_COMMON_CENTROID, requests[0].W_new_m / len(group.members),
                                        tuple(len(group.members) for _ in group.members),
                                        tuple(r.W_new_m for r in requests), None, None, None, False, "cc_nf"))
        return _layout(group, chosen, ev.attempts, pending=True, reason="w_request_pending", w_requests=requests)
    why = "w_request_rejected" if any(m in rejected for m in group.members) else "w_not_adjustable"
    ev.attempts.append(GroupAttempt("w_request", PATTERN_COMMON_CENTROID, None, (), (), None, None, None, False, why))
    relaxed = ev.best((PATTERN_INTERDIGITATION,), "relax") if PATTERN_INTERDIGITATION in allowed else None
    return _layout(group, relaxed, ev.attempts, relaxed=relaxed is not None,
                   reason=("relaxed:" + why) if relaxed is not None else _why(None, ev, why))


@compute_block(
    WRITER_GROUPS,
    reads=((DEVICE, F_DEVICE), (DEVICE, F_FW_CAND), (GRAPH, F_PDK), (GRAPH, F_GROUPS_IN), (GRAPH, F_REJECTED)),
    writes=((GRAPH, F_GROUPS),),
)
def pattern_select(projection):
    """matching 그룹마다 `GroupLayout`(gid 정렬 tuple)."""
    devices = dict(projection.column(DEVICE, F_DEVICE))
    fw_cand = dict(projection.column(DEVICE, F_FW_CAND))
    pdk = projection.value(GRAPH, GRAPH_KEY, F_PDK)
    groups = projection.value(GRAPH, GRAPH_KEY, F_GROUPS_IN)
    rejected = set(projection.value(GRAPH, GRAPH_KEY, F_REJECTED))
    placed = tuple(_place(g, devices, fw_cand, pdk, rejected) for g in sorted(groups, key=lambda g: g.gid))
    return {(GRAPH, F_GROUPS): {GRAPH_KEY: placed}}
