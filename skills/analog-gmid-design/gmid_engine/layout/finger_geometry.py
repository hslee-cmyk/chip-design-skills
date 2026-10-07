"""MOD7 소자별 finger 확정 계산 블록 -- 행별 finger_w (계획 N3.17 LY1·LY2, design 3절 3단계·L6, 사용자 결정 Q4).

진입점: `finger_geometry` -- core `@compute_block`(writer `ly_finger_geometry`, reads device `ly_fw_cand`,
graph `ly_groups`·`ly_row_groups`, writes device `ly_finger`).

* 패턴으로 배치된 matching 그룹 멤버: 그 그룹이 고른 finger_w·nf(잠정 배치 포함).
* 그 밖의 소자(행 그룹마다): 자기 행 그룹 소자들의 후보만 쓴다(다른 행의 finger_w 를 전파하지 않음, 단위셀 폴백 없음).
  남은 소자 중 가장 많은 소자에게 실효 허용오차 안인 폭 키 -> (그 폭의 finger 수 합 최소 -> 큰 폭 키) 를 골라 그 소자들에
  주고, 남은 소자로 반복한다(한 물리 행 안 finger_w 는 하나 -- 폭이 다르면 행이 나뉜다). 소자마다 그 폭에서 오차 최소 nf.
* 어떤 폭으로도 실효 허용오차를 못 지키는 소자: 오차 최소 후보를 잠정으로 쓰고 `W_request{reason="finger_quantization",
  W_old = 그 폭의 W_need, W_new = 그 후보의 실현 W}`(레이아웃은 W 를 바꾸지 않는다, LY3). 그 소자에 matching 그룹
  W_request(LY5 (ii))가 이미 있으면 그 요청이 대신한다(같은 소자에 요청 두 개를 내지 않는다).
"""
from gmid_engine.core import compute_block

from ._ly_fields import DEVICE, F_FINGER, F_FW_CAND, F_GROUPS, F_ROW_GROUPS, GRAPH, GRAPH_KEY, WRITER_FINGER
from .contract_output import DeviceFinger, WRequest


def _finger(name, cand, origin, group, w_request):
    return DeviceFinger(name, cand.finger_w_key, cand.finger_w_m, cand.n_fingers, cand.W_need_m, cand.W_realized_m,
                        cand.err_rel, cand.lower, cand.upper, cand.tol_effective, cand.grid_dominated, cand.ok, origin,
                        group, w_request)


def _best_at(cands, key):
    """폭 키 `key` 의 실효 허용오차 안 후보 중 오차 최소(동률이면 nf 작은 것)."""
    return min((c for c in cands if c.ok and c.finger_w_key == key), key=lambda c: (c.err_rel, c.n_fingers))


def _row_group_fingers(names, fw_cand):
    out = {}
    pending = sorted(names)
    while pending:
        valid = {n: {c.finger_w_key for c in fw_cand[n] if c.ok} for n in pending}
        keys = sorted(set().union(*valid.values()))
        if not keys:
            break

        def rank(key):
            users = [n for n in pending if key in valid[n]]
            return (-len(users), sum(_best_at(fw_cand[n], key).n_fingers for n in users), -key)

        key = min(keys, key=rank)
        for n in [n for n in pending if key in valid[n]]:
            out[n] = _finger(n, _best_at(fw_cand[n], key), "row", None, None)
        pending = [n for n in pending if n not in out]
    for n in pending:
        if fw_cand[n]:
            cand = min(fw_cand[n], key=lambda c: (c.err_rel, c.n_fingers, -c.finger_w_key))
            out[n] = _finger(n, cand, "row", None, None)
    return out, tuple(pending)


@compute_block(
    WRITER_FINGER,
    reads=((DEVICE, F_FW_CAND), (GRAPH, F_GROUPS), (GRAPH, F_ROW_GROUPS)),
    writes=((DEVICE, F_FINGER),),
)
def finger_geometry(projection):
    """소자마다 `DeviceFinger`(사용 가능한 폭 슬라이스가 하나도 없는 소자는 값이 없다 -- `run_layout` 이 기록한다)."""
    fw_cand = dict(projection.column(DEVICE, F_FW_CAND))
    groups = projection.value(GRAPH, GRAPH_KEY, F_GROUPS)
    row_groups = projection.value(GRAPH, GRAPH_KEY, F_ROW_GROUPS)
    out = {}
    requested = {r.device for g in groups for r in g.w_requests}
    for g in groups:
        if g.pattern is None:
            continue
        nf_of = dict(g.n_fingers)
        for name in g.members:
            cand = next(c for c in fw_cand[name] if c.finger_w_key == g.finger_w_key and c.n_fingers == nf_of[name])
            out[name] = _finger(name, cand, "group", g.gid, None)
    for rg in sorted(row_groups, key=lambda r: r.rid):
        fingers, unresolved = _row_group_fingers([n for n in rg.members if n not in out], fw_cand)
        for name, finger in fingers.items():
            if name in unresolved and name not in requested:
                request = WRequest(name, finger.W_need_m, finger.W_realized_m, "finger_quantization", None)
                finger = _finger(name, next(c for c in fw_cand[name] if c.finger_w_key == finger.finger_w_key
                                            and c.n_fingers == finger.n_fingers), "row", None, request)
            out[name] = finger
    return {(DEVICE, F_FINGER): out}
