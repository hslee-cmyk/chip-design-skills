"""MOD7 matching 그룹 패턴 선택 계산 블록 -- 행 구성 단계에서 먼저, 패턴표 우선 (계획 N3.17 LY4·LY5·LY6, design 3절 2단계,
사용자 결정 2026-10-07 Q4 (i)·Q8 (i)~(iv)).

진입점: `pattern_select` -- core `@compute_block`(writer `ly_pattern_select`, reads device `ly_device`·`ly_fw_cand`,
graph `ly_pdk`·`ly_groups_in`·`ly_rejected`, writes graph `ly_groups`·`ly_dispositions`).

0. role 이 `EXCLUDED_ROLES`(bias_distribution·feedback_shared)인 그룹은 레이아웃 matching 에서 빼고 근거와 함께
   `MatchingDisposition` 으로 기록한다(Q8 (iii)) -- 그 멤버는 일반 행 소자로 배치된다.
그룹마다 독립으로, 전 그룹을 판정한다(첫 실패에서 멈추지 않음, LY6):
1. 전제: hub-leaf 그룹(diff_pair·mirror)은 멤버를 hub 넷 쪽이 source 가 되게 세운다(`orient`). branch_symmetric 은 hub 가
   없는 쌍이라 멤버가 모두 같은 gate 인지만 본다. 전제 밖이면 사유를 기록하고 패턴 없이 둔다(행 Euler 가 처리).
2. 후보 = 멤버 모두에게 실효 허용오차 안인 공통 finger_w(같은 unit geometry) x 멤버별 nf(내림·올림) 조합.
3. 후보마다 패턴 함수를 부른다:
   common-centroid -- branch_symmetric 이면 `row_swap_layout`(행 수 = 멤버 수, Q8 (ii)). 그 밖은 nf 같고 nf >= 멤버 수면
   `common_centroid_layout(n_rows=None)`(회전 exact), 2멤버 nf 다르면 `n_rows=멤버 수`(표 경로 -> 탐색), 그 밖은 전제 밖.
   interdigitation -- `INTERDIGITATION_PATTERNS` 에서 글자 수 = 멤버 수이고 글자별 개수가 멤버 nf 와 정확히 같은 base
   (`table_base`), 없으면 base=None(탐색).
4. 정렬 키(사전식, 상수 가중치 없음) = 머리 + 꼬리. 머리 = (mirror 만: interdigitation 성립 아니면 1 (Q8 (ii)),
   무게중심 일치 아님, 방법(표·회전 0 / 그 밖 1), crossover, 고립쌍, residual), 꼬리 = (행 폭 칸 수, 최대 오차, 폭 키,
   패턴, nf). 머리가 모두 0 인 후보를 찾은 뒤 더 넓은 조합은 키가 앞설 수 없으므로 평가하지 않는다.
   interdigitation 성립 = 패턴 interdigitation 이 배치를 냈고 crossover 0.
5. 차동쌍·branch_symmetric(LY5, Q8 (ii)): common-centroid 만 먼저 -> (i) 무게중심 일치 후보가 있으면 채택(같은 보존량에서
   nf 조정) (ii) 없고 멤버 모두 `W_adjustable`·MOD8 거부 없음이면 `W_request`(nf = 멤버 수, finger_w = 특성화 폭 중
   max W_need(폭)/멤버 수 에 가장 가까운 것, 모든 멤버 같은 값) + `pending`(배치는 잠정) (iii) 그 밖(조정 불가·거부·사용 가능 폭 없음)은
   **즉시 완화하지 않는다**(U12, LY5 마지막 문장 -- 완화 판정은 MOD8 몫): pattern None + 사유(`w_not_adjustable` 등)로 두고
   `review_needed` 에 올린다. 시도는 순서대로 전부 `attempts` 에 남긴다(무게중심 불일치 (i) 시도의 dx·dy 포함).
6. 패턴을 고를 때 그룹 멤버 L 이 같은지 본다(LY4): 다르면 `GroupLayout.l_mismatch` = ((멤버, L_m), ...) 로 기록만 한다(거부 사유 아님,
   L 통일은 LR2 소관).
"""
import itertools
from collections import Counter

from gmid_engine.core import compute_block

from ._helpers_pattern import offsets, orient, pattern_rows
from ._ly_fields import (
    DEVICE,
    F_DEVICE,
    F_DISPOSITIONS,
    F_FW_CAND,
    F_GROUPS,
    F_GROUPS_IN,
    F_PDK,
    F_REJECTED,
    GRAPH,
    GRAPH_KEY,
    WRITER_GROUPS,
)
from .contract_input import (
    CC_REQUIRED_ROLES,
    EXCLUDED_ROLES,
    PATTERN_COMMON_CENTROID,
    PATTERN_INTERDIGITATION,
    PATTERNS,
    ROLE_BIAS_DISTRIBUTION,
    ROLE_BRANCH_SYMMETRIC,
    ROLE_DIFF_PAIR,
    ROLE_MIRROR,
)
from .contract_output import GroupAttempt, GroupLayout, MatchingDisposition, WRequest
from .patterns_common_centroid import COMMON_CENTROID_PATTERNS, common_centroid_layout
from .patterns_interdigitate import INTERDIGITATION_PATTERNS, interdigitate_layout
from .patterns_row_swap import row_swap_layout
from .transistor import Transistor

_EXACT_METHODS = ("pattern_table", "rotation_exact")
# 표 경로(`_try_pattern_table_match`)가 받는 멤버 수 = 표 key 의 글자 종류 수(복사본은 2-소자 표만 쓴다).
_TABLE_MEMBERS = len(set("".join(min(COMMON_CENTROID_PATTERNS))))
_SENS_DIFF = "offset"
_SENS_OTHER = "ratio"
_DISPOSITION = "excluded_from_layout_matching"
_REASON_BIAS = ("gate shared by a diode reference and consumers in other blocks: bias distribution, "
                "not a matched pair (Q8 (iii))")
_REASON_FEEDBACK = "loop signal gate shared: feedback sharing, not a matched pair (Q8 (iii))"


def _exclusion_reason(role):
    return _REASON_BIAS if role == ROLE_BIAS_DISTRIBUTION else _REASON_FEEDBACK


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


def _branch_ends(group, devices):
    """branch_symmetric 전제: 멤버 kind·gate 가 모두 같다(hub 없음). 소자 그대로의 (이름, source, drain)."""
    gates = {(devices[n].kind, devices[n].gate) for n in group.members}
    if len(gates) != 1:
        return None, "branch_gate_differs"
    return tuple((n, devices[n].source, devices[n].drain) for n in group.members), ""


class _Evaluator:
    """그룹 하나의 후보 평가기(블록 호출 안에서만 산다 -- 같은 패턴 호출은 한 번만)."""

    def __init__(self, group, ends, devices, fw_cand, pdk):
        self.group = group
        self.ends = {name: (s, d) for name, s, d in ends}
        self.devices = devices
        self.fw_cand = fw_cand
        self.pdk = pdk
        self.calls = {}
        self.attempts = []
        self.combos = self._combos()
        members = sorted(group.members)
        self.pairs = list(zip(members[0::2], members[1::2]))
        sens = _SENS_DIFF if group.role == ROLE_DIFF_PAIR else _SENS_OTHER
        self.sens = {p: sens for p in self.pairs}

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
        total = sum(nf_of.values())
        if pattern == PATTERN_COMMON_CENTROID and self.group.role == ROLE_BRANCH_SYMMETRIC:
            order, arg = tuple(members), len(members)
        elif pattern == PATTERN_COMMON_CENTROID:
            nfs = [nf_of[n] for n in members]
            equal = len(set(nfs)) == 1
            if equal and nfs[0] >= len(members):
                n_rows = None
            elif not equal and len(members) == _TABLE_MEMBERS:
                n_rows = len(members)
            else:
                return None, "cc_precondition"
            order, arg = tuple(members), n_rows
        else:
            arg, order = _table_base(members, nf_of)
        trs = [Transistor(n, self.devices[n].kind, source=self.ends[n][0], drain=self.ends[n][1], n_fingers=nf_of[n])
               for n in order]
        memo_key = (pattern, arg, tuple((t.name, t.n_fingers) for t in trs))
        if memo_key not in self.calls:
            if pattern == PATTERN_COMMON_CENTROID and self.group.role == ROLE_BRANCH_SYMMETRIC:
                result = row_swap_layout(trs, arg, self.pairs, self.sens)
            elif pattern == PATTERN_COMMON_CENTROID:
                result = common_centroid_layout(trs, n_rows=arg, max_candidates=total)
            else:
                result = interdigitate_layout(trs, base=arg)
            self.calls[memo_key] = (result, trs)
        return self.calls[memo_key], ""

    def best(self, patterns, step):
        """`patterns` 로 후보 전부(완전 후보 뒤 더 넓은 것은 생략)를 평가해 최선 (정렬 키, 머리 길이, 결과 묶음) 또는 None."""
        best = None
        for width_cells, max_err, key, choice in self.combos:
            if best is not None and not any(best[0][:best[1]]) and width_cells > best[0][best[1]]:
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
                rows = pattern_rows(result, trs)
                dx, dy = offsets(rows, self.group.members)
                centred = dx == 0 and dy == 0
                self.attempts.append(GroupAttempt(step, pattern, choice[0].finger_w_m, nfs, realized, result["method"],
                                                  float(dx), float(dy), centred, "evaluated"))
                head = (0 if centred else 1, 0 if result["method"] in _EXACT_METHODS else 1,
                        result["crossover_count"], result["isolated_pairs"], float(result["residual"]))
                if self.group.role == ROLE_MIRROR:
                    feasible = pattern == PATTERN_INTERDIGITATION and result["crossover_count"] == 0
                    head = (0 if feasible else 1,) + head
                sort_key = head + (width_cells, max_err, key, pattern, nfs)
                if best is None or sort_key < best[0]:
                    best = (sort_key, len(head), pattern, result, rows, choice, dx, dy)
        return best


def _layout(group, chosen, attempts, *, pending=False, reason="", w_requests=(), l_mismatch=()):
    members = group.members
    if chosen is None:
        return GroupLayout(group.gid, group.role, members, None, None, None, None, (), (), None, None, None, None, None,
                           False, pending, pending, reason, tuple(attempts), tuple(w_requests), l_mismatch)
    _, _, pattern, result, rows, choice, dx, dy = chosen
    return GroupLayout(group.gid, group.role, members, pattern, result["method"], choice[0].finger_w_key,
                       choice[0].finger_w_m, tuple((n, c.n_fingers) for n, c in zip(members, choice)), rows,
                       float(result["residual"]), result["crossover_count"], result["isolated_pairs"], float(dx),
                       float(dy), dx == 0 and dy == 0, pending, pending, reason, tuple(attempts),
                       tuple(w_requests), l_mismatch)


def _w_requests(group, fw_cand, pdk):
    """LY5 (ii) W_request: 멤버 모두에게 사용 가능한 폭 키 중 |fw - max W_need(fw)/n| 최소(동률은 작은 키), nf = n."""
    n = len(group.members)
    grid = pdk.manufacturing_grid_m
    need = {}
    for m in group.members:
        for c in fw_cand[m]:
            need.setdefault(c.finger_w_key, {})[m] = c.W_need_m
    keys = [k for k, by in need.items() if len(by) == n]
    if not keys:
        return ()
    key = min(keys, key=lambda k: (abs(k * grid - max(need[k].values()) / n), k))
    return tuple(WRequest(m, need[key][m], n * key * grid, "cc_nf", group.gid) for m in group.members)


def _why(chosen, ev, ok_reason):
    if chosen is not None:
        return ok_reason
    return "no_applicable_pattern" if ev.combos else "no_common_finger_w"


def _l_mismatch(group, devices):
    """LY4 `matching_L_mismatch`: 멤버 L 이 모두 같으면 (), 아니면 ((멤버, L_m), ...) 멤버 순서."""
    lengths = tuple((m, devices[m].L_m) for m in group.members)
    return lengths if len({length for _, length in lengths}) > 1 else ()


def _place(group, devices, fw_cand, pdk, rejected):
    mismatch = _l_mismatch(group, devices)
    if group.role == ROLE_BRANCH_SYMMETRIC:
        ends, reason = _branch_ends(group, devices)
    else:
        ends, reason = orient(group, devices)
    if ends is None:
        attempt = GroupAttempt("precondition", None, None, (), (), None, None, None, False, reason)
        return _layout(group, None, [attempt], reason=reason, l_mismatch=mismatch)
    ev = _Evaluator(group, ends, devices, fw_cand, pdk)
    allowed = tuple(p for p in PATTERNS if p in group.allowed_patterns)
    if group.role not in CC_REQUIRED_ROLES:
        chosen = ev.best(allowed, "select")
        return _layout(group, chosen, ev.attempts, reason=_why(chosen, ev, "selected"), l_mismatch=mismatch)
    chosen = ev.best((PATTERN_COMMON_CENTROID,), "cc_same_W")
    if chosen is not None and chosen[0][0] == 0:
        return _layout(group, chosen, ev.attempts, reason="cc_same_W", l_mismatch=mismatch)
    adjustable = all(devices[m].W_adjustable and m not in rejected for m in group.members)
    requests = _w_requests(group, fw_cand, pdk) if adjustable else ()
    if requests:
        n = len(group.members)
        ev.attempts.append(GroupAttempt("w_request", PATTERN_COMMON_CENTROID, requests[0].W_new_m / n,
                                        tuple(n for _ in group.members), tuple(r.W_new_m for r in requests), None,
                                        None, None, False, "cc_nf"))
        return _layout(group, chosen, ev.attempts, pending=True, reason="w_request_pending", w_requests=requests,
                       l_mismatch=mismatch)
    if any(m in rejected for m in group.members):
        why = "w_request_rejected"
    elif adjustable:
        why = "no_usable_slice"
    else:
        why = "w_not_adjustable"
    ev.attempts.append(GroupAttempt("w_request", PATTERN_COMMON_CENTROID, None, (), (), None, None, None, False, why))
    # LY5: W_request 를 낼 수 없어도 즉시 완화(interdigitation·무게중심 불일치 배치)하지 않는다 -- 판정은 MOD8.
    return _layout(group, None, ev.attempts, reason=why if ev.combos else "no_common_finger_w", l_mismatch=mismatch)


@compute_block(
    WRITER_GROUPS,
    reads=((DEVICE, F_DEVICE), (DEVICE, F_FW_CAND), (GRAPH, F_PDK), (GRAPH, F_GROUPS_IN), (GRAPH, F_REJECTED)),
    writes=((GRAPH, F_GROUPS), (GRAPH, F_DISPOSITIONS)),
)
def pattern_select(projection):
    """레이아웃 matching 그룹마다 `GroupLayout`(gid 정렬 tuple), 뺀 그룹마다 `MatchingDisposition`(gid 정렬 tuple)."""
    devices = dict(projection.column(DEVICE, F_DEVICE))
    fw_cand = dict(projection.column(DEVICE, F_FW_CAND))
    pdk = projection.value(GRAPH, GRAPH_KEY, F_PDK)
    groups = sorted(projection.value(GRAPH, GRAPH_KEY, F_GROUPS_IN), key=lambda g: g.gid)
    rejected = set(projection.value(GRAPH, GRAPH_KEY, F_REJECTED))
    placed = tuple(_place(g, devices, fw_cand, pdk, rejected) for g in groups if g.role not in EXCLUDED_ROLES)
    dispositions = tuple(MatchingDisposition(g.gid, g.role, g.members, _DISPOSITION,
                                             _exclusion_reason(g.role))
                         for g in groups if g.role in EXCLUDED_ROLES)
    return {(GRAPH, F_GROUPS): {GRAPH_KEY: placed}, (GRAPH, F_DISPOSITIONS): {GRAPH_KEY: dispositions}}
