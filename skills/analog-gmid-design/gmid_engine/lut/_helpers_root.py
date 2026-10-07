"""gm/ID 곡선의 분지 판정·VGS 근 공용 helper (설계 MOD1 2.1 `_solve_vgs` 블록 복사 + 분지 규칙 새로).

분지 규칙(정본, lut/CONTRACT.md 3절): 곡선의 **정점**(gm/ID 최댓값의 첫 격자 index p) 오른쪽, 곧 VGS ≥ VGS[p] 인
구간만 강반전 분지로 본다. 목표를 품는 구간은 그 분지 안에서만 찾고 그중 가장 오른쪽을 고른다.
분지 안에 목표를 품는 구간이 없으면 None 을 돌려준다 -- 정점 왼쪽(누설·약반전 꼬리) 해로 내려가지 않는다.

옛 `_solve_vgs`(SR:478)는 분지 안에 해가 없을 때 정점 왼쪽 누설 분지(VGS≈0)의 교차를 조용히 돌려줬다
(tol_V 실측: 유효 목표의 2.13%, 오차 최대 1.78 V). 그래서 구간 선택 문장(분지 거르기·해 없음 처리)은 새로 썼고,
구간을 고른 뒤의 2점 역보간 문장만 본문 그대로 복사했다(복사 구간 A·B 해시는 CONTRACT.md 6절).
"""
import numpy as np


def peak_index(g):
    """gm/ID 격자 값 `g`(1차원) 의 정점 index(최댓값이 여럿이면 가장 왼쪽)."""
    return int(np.argmax(g))


def strong_inversion_root(g, vgs_grid, gm_id):
    """강반전 분지(정점 오른쪽)에서 gm/ID = `gm_id` 인 가장 큰 VGS. 분지 안에 해가 없으면 None."""
    # 복사 구간 A (SR:539~540): 목표를 품는 인접 구간 -- 두 끝점 편차 곱이 0 이하.
    d = g - gm_id
    idx = np.flatnonzero(d[:-1] * d[1:] <= 0.0)
    # 새로: 정점 왼쪽 구간을 버린다(분지 규칙). 남은 것이 없으면 해 없음.
    idx = idx[idx >= peak_index(g)]
    if idx.size == 0:
        return None
    # 복사 구간 B (SR:548~561): 가장 오른쪽 구간에서 옛 구현과 같은 방향·순서의 2점 보간.
    i = int(idx[-1])
    ga, gb = g.item(i), g.item(i + 1)
    va, vb = vgs_grid.item(i), vgs_grid.item(i + 1)
    if ga <= gb:
        x0, x1, y0, y1 = ga, gb, va, vb
    else:
        x0, x1, y0, y1 = gb, ga, vb, va
    if x1 == x0:                    # 평탄 구간 -- 가장 큰 VGS 쪽 끝점을 취한다
        result = vb
    else:
        result = (y1 - y0) / (x1 - x0) * (gm_id - x0) + y0
    return result
