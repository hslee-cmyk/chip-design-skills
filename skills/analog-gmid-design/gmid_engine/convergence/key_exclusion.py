"""재검증이 거절한 기하의 폭 후보 하나를 그 레이아웃 행 그룹에서 뺀다 (계획 N3.17 LY3 '위반하면 W_request 경로', 설계 40 §3.7-A 6 '키 제외 규칙 재정의', 계약 CONTRACT.md 7절).

진입점: `key_exclusion(pdk, row_groups, placements, sized_w, excluded, colour) -> ((행 그룹 rid, 폭 키), new_excluded | None)`.

실현 기하의 재평가가 봉인·제약을 어기고 거부할 W_request 도 없으면, 사이징 W 대비 실현 W 의 어긋남 `|ln(W_실현 / W_사이징)|` 이 가장 큰 소자(동률은 구조 색 `colour` 순, 이름은
마지막 -- 이름이 정하지 않는다)가 속한 레이아웃 행 그룹(`RowGroup` -- 같은 행은 finger_w 를 공유한다, LY2)의 지금 손가락 폭 후보(그 소자 배치 `p.key`)를 **그 행 그룹의 후보**에서 뺀다.
다른 행 그룹의 후보는 그대로다(WB-1: kind 당 슬라이스 하나라는 제약이 없어져 키 제외의 단위가 kind 에서 행 그룹으로 옮겨졌다). 이름·회로 무관, 새 상수 없음.

* `pdk` = 처음 후보(`LayoutPdk.slice_width_keys` -- kind 별 폭 키), `row_groups` = 레이아웃 입력의 행 그룹(`ly_row_groups`), `excluded` = 지금까지 뺀 ((rid, (폭 키, ...)), ...).
* 반환 `((rid, 키), new_excluded)` -- `new_excluded` 는 `excluded` 에 그 키를 더한 것(정렬 tuple), 입력은 바꾸지 않는다. 그 행 그룹에 남는 후보가 없으면 `((rid, 키), None)` -- 더 시도할 폭이 없다.
가장 어긋난 소자가 어느 행 그룹에도 속하지 않으면 `((None, 키), None)`(뺄 후보 없음 -> 호출부가 `STATUS_INFEASIBLE`, 새 사유 없음).
키를 하나 빼므로 반복은 (행 그룹 수 x PDK 폭 키 수) 이하에서 끝난다(단조 감소; 루프의 수렴 판정·상한은 바꾸지 않는다).
"""
import math


def key_exclusion(pdk, row_groups, placements, sized_w, excluded, colour):
    worst = min(placements, key=lambda p: (-abs(math.log(p.W_m / sized_w[p.name])), colour.get(p.name, 0), p.name))
    group = next((rg for rg in row_groups if worst.name in rg.members), None)
    if group is None:                       # 어느 행 그룹에도 없는 소자 = 뺄 후보가 없다 -> 더 시도할 폭이 없음(fail-closed, StopIteration 누출 금지)
        return (None, worst.key), None
    dropped = dict(excluded)
    now = tuple(sorted(set(dropped.get(group.rid, ())) | {worst.key}))
    if not [k for k in dict(pdk.slice_width_keys)[group.kind] if k not in now]:
        return (group.rid, worst.key), None
    return (group.rid, worst.key), tuple(sorted({**dropped, group.rid: now}.items()))
