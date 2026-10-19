"""레이아웃 결과 -> 소자별 실효 배치 (계획 N3.17 LY3·LY5 (ii)·LY7, 설계 40 §3.9 U14).

진입점: `effective_placement(snapshot, grid_m) -> (placements, unplaced)`.

`snapshot` = 레이아웃 필드를 쓴 설계점 스냅샷(`LayoutResult.snapshot`, 설계 40 v1.6 §2.4.7) -- 소자 이름 = `ly_point` 열 key, finger = `ly_finger`, 그룹 = `ly_groups`.
* 놓인 소자(`ly_finger` 값 있음): `Placement(이름, 폭 키 = round(finger_w / 격자), finger_w, nf, W = 레이아웃 실현 W, False, 실효 허용오차)`.
* W_request 응답 대기 그룹(`GroupLayout.pending`)의 멤버: 레이아웃은 그 그룹을 잠정으로만 놓았다(W 를 바꾸지 않는다, LY3). MOD8 은 요청한 W 로 평가해야
  하므로 놓인 곳이 아니라 요청한 (폭 키, nf) 를 쓴다 -- 마지막 시도(`GroupAttempt`, `finger_w_m` = 요청 W / 멤버 수, `n_fingers` = 멤버별 nf)에서 읽는다.
  W = nf x (키 x 격자) -- 레이아웃이 후보 실현 W 를 만드는 식(`n_fingers * finger_w`, `finger_w = 키 x 격자`)과 같아서 다음 레이아웃이 그 폭에 놓이면 비트가 같다.
* `unplaced` = 어떤 폭 슬라이스로도 놓지 못한 소자 이름(이름순) -- 호출부가 `STATUS_UNPLACEABLE` 로 기록한다.
소자 이름순 tuple.
"""
from gmid_engine.layout import F_FINGER, F_GROUPS, F_POINT, LAYOUT_KEY

from .convergence_values import Placement


def effective_placement(snapshot, grid_m):
    fingers = dict(snapshot.column("device", F_FINGER))
    pending = {}
    for group in snapshot.value("graph", LAYOUT_KEY, F_GROUPS):
        if not group.pending:
            continue
        last = group.attempts[-1]
        key = round(last.finger_w_m / grid_m)
        for member, nf in zip(group.members, last.n_fingers):
            pending[member] = (key, nf)
    out, unplaced = [], []
    for name, _point in snapshot.column("device", F_POINT):
        f = fingers.get(name)
        if name in pending:
            key, nf = pending[name]
            fw = key * grid_m
            out.append(Placement(name, key, fw, nf, nf * fw, True, None if f is None else f.tol_effective))
        elif f is None:
            unplaced.append(name)
        else:
            out.append(Placement(name, round(f.finger_w_m / grid_m), f.finger_w_m, f.n_fingers, f.W_realized_m, False,
                                 f.tol_effective))
    return tuple(sorted(out, key=lambda p: p.name)), tuple(sorted(unplaced))
