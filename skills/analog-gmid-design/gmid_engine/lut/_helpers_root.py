"""gm/ID 곡선의 분지 판정·VGS 근 공용 helper (분지 규칙 lut/CONTRACT.md 3절, 칸 안 근 = Hermite 미분, DEC-87).

분지 규칙(정본): 곡선의 **정점**(마디 gm/ID 최댓값의 첫 index p) 오른쪽, 곧 VGS ≥ VGS[p] 인 칸만 강반전 분지로 본다.
목표를 품는 칸(두 끝 마디 gm/ID 와 목표의 편차 곱 ≤ 0)은 그 분지 안에서만 찾고 그중 가장 오른쪽을 고른다. 분지 안에
그런 칸이 없으면 해 없음 -- 정점 왼쪽(누설·약반전 꼬리) 해로 내려가지 않는다.

칸 안의 근은 그 칸의 VGS Hermite(값 = 마디 ln ID, 기울기 = 마디 gm/ID) 미분이 목표와 같은 VGS 다(`hermite_root`
bisection). 그래서 역산 결과에서 `op_point` 를 다시 읽으면 같은 gm/ID 가 나온다(한 곡면). 두 끝 마디의 미분은 마디
gm/ID 그대로라 칸 선택(마디 값)과 칸 안 근이 어긋나지 않는다.

옛 `_solve_vgs`(SR:478)는 분지 안에 해가 없을 때 정점 왼쪽 누설 분지(VGS≈0)의 교차를 조용히 돌려줬다(tol_V 실측: 유효
목표의 2.13%, 오차 최대 1.78 V) -- 그래서 분지 거르기·해 없음 처리를 새로 썼다. r5 부터 칸 안 2점 선형 역보간(옛 복사
구간 B)도 Hermite 근으로 바뀌어 옛 복사 구간은 남지 않는다(CONTRACT 6절).
"""
import numpy as np

from ._helpers_interp import hermite_root


def peak_index(g):
    """gm/ID 격자 값 `g`(1차원) 의 정점 index(최댓값이 여럿이면 가장 왼쪽)."""
    return int(np.argmax(g))


def strong_inversion_root(v, y, m, targets):
    """곡선 묶음(행마다 독립)의 강반전 분지 근 `(vgs, cell)`.

    `v`·`y`·`m`: 모양 (R, n) -- 행마다 VGS 마디, 마디 ln ID, 마디 gm/ID. `targets`: 모양 (R,) 목표 gm/ID.
    반환: vgs (R,) (해 없음 = NaN), cell (R,) (고른 칸 index, 해 없음 = −1). 같은 칸 안 근은 Hermite 미분 = 목표.
    """
    v = np.asarray(v, dtype=float)
    y = np.asarray(y, dtype=float)
    m = np.asarray(m, dtype=float)
    targets = np.asarray(targets, dtype=float)
    d = m - targets[:, None]
    cross = d[:, :-1] * d[:, 1:] <= 0.0
    cols = np.arange(cross.shape[1])
    cross &= cols[None, :] >= np.argmax(m, axis=1)[:, None]
    has = cross.any(axis=1)
    last = cross.shape[1] - 1 - np.argmax(cross[:, ::-1], axis=1)
    rows = np.flatnonzero(has)
    i = last[rows]
    vgs = np.full(len(targets), np.nan)
    ends = (v[rows, i], v[rows, i + 1], y[rows, i], y[rows, i + 1], m[rows, i], m[rows, i + 1])
    tgt = targets[rows]
    if len(rows) == 1:                       # 1행 = 스칼라 경로(같은 산술, hermite_root docstring)
        ends = tuple(x.item() for x in ends)
        tgt = tgt.item()
    vgs[rows] = hermite_root(*ends, lambda value, slope: slope - tgt)
    return vgs, np.where(has, last, -1)


def monotone_end(q, p):
    """배열 `q` 에서 index `p` 부터 엄격히 증가하는 첫 구간의 끝 index(`q[p] < q[p+1] < ... < q[end]`; 증가가 없으면 p)."""
    end = p
    while end + 1 < len(q) and q[end + 1] > q[end]:
        end += 1
    return end
