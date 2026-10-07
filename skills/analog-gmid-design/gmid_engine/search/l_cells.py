"""L 칸(이산 bin 선택 + bin 안 연속) (설계 design_mod6_search_front 4.1·4.3, 계획 LR3·LR10·DEC-95 (1)).

진입점: `l_cells(lut_access, kind) -> tuple[(lo, hi)]`(L 오름차순).

* 레이아웃 전 폭 슬라이스(`lut_access.w_keys` 의 kind 폭)의 L 앵커와 PDK 모델 bin 지도(`DcSlice.l_bins`)에서 만든다.
  같은 bin 에 앵커가 둘 이상이면 칸 = [그 bin 의 최소 앵커, 최대 앵커](lut 가 그 안을 선형 보간한다, LR3), 하나면 [a, a].
* bin 지도가 없으면(`l_bins.bins == ()` -- lut 는 앵커 밖 L 을 `lut_l_not_anchor` 로 거부한다) 앵커마다 칸 하나(lo == hi).
* 외층은 칸 index 를 고정하고 칸 안 L 을 연속으로 움직인다(lo == hi 칸의 L 은 연속 변수가 아니다). 칸 index 이동은
  이산 탐색(L-b)뿐이다.
"""


def l_cells(lut_access, kind):
    w_key = dict(lut_access.w_keys)[kind]
    sl = lut_access.memo.lut.slice_map[(kind, w_key)]
    anchors = tuple(float(a) for a in sl.grids[0])
    if not sl.l_bins.bins:
        return tuple((a, a) for a in anchors)
    groups = {}
    for a, b in zip(anchors, sl.l_bins.anchor_bin):
        groups.setdefault(("bin", b) if b is not None else ("anchor", a), []).append(a)   # bin 밖 앵커 = 자기 칸
    return tuple(sorted((min(v), max(v)) for v in groups.values()))
