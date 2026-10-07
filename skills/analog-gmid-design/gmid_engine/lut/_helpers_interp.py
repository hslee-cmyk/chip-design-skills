"""LUT 다중선형 보간 공용 helper -- 옛 엔진 `legacy/sizing_recipe.py` 141·206행 두 함수의 본문 그대로 복사(설계 MOD1 2.1).

* 복사 범위: 함수 본문(docstring 제외 문장 목록). 이름만 바꿨다(`_multilinear_interp` -> `multilinear_interp`,
  `_multilinear_interp_point_multi` -> `multilinear_interp_point_multi`) -- 다른 파일이 `_` 이름을 import 하지
  않게(구조 규칙 B). AST 해시 대조는 lut/CONTRACT.md 6절.
* 알려진 결함(DF-27): 축 밖 입력을 조용히 클램프한다. 새 엔진은 모든 조회가 먼저 `check_axes` 로 축 밖을
  거부하므로 클램프 분기는 격자 끝점(정확값)에서만 닿는다.
* `grids` 는 축마다 오름차순 시퀀스(list·tuple), `values` 는 그 격자로 색인되는 N차원 배열.
"""
import numpy as np


def multilinear_interp(grids, values, points):
    """N차원 격자 다중선형보간. points: (M, N) 조회 좌표. 반환: (M,) 보간값 numpy 배열(복사본 -- 본문은 옛 141행)."""
    import bisect
    ndim = len(grids)
    # 2026-08-13(세션31, F 설계 1단계) -- 이미 plain list인 grid는 그대로 쓴다(재변환/재복사
    # 불필요 -- 이 함수는 grids를 읽기만 하고 절대 in-place mutate하지 않는다). 호출부
    # (`SemiEmpiricalGmIdLUT._query()`/`_gm_id_curve()`)가 `self._grids_list`(__init__에서
    # 한 번만 만든 캐시)를 넘기는 게 이제 기본 경로라, 매 호출마다 `list(g)` 얕은 복사를
    # 반복하던 낭비를 없앤다(감사 발견 -- session29가 `.tolist()` 자체를 이미 병목으로
    # 지목했으면서도 이 재변환/재복사는 남아있었다).
    grids = [g.tolist() if hasattr(g, "tolist") else g for g in grids]
    points_seq = points.tolist() if hasattr(points, "tolist") else points
    if points_seq and not hasattr(points_seq[0], "__len__"):
        points_seq = [points_seq]  # 1차원(단일 좌표, N개 스칼라)로 들어온 경우 (1,N)으로 승격

    result = []
    for point in points_seq:
        idx_lo, frac = [], []
        for d in range(ndim):
            g = grids[d]
            n = len(g)
            x = point[d]
            if x <= g[0]:
                i, f = 0, 0.0
            elif x >= g[-1]:
                i, f = n - 2, 1.0
            else:
                i = bisect.bisect_right(g, x) - 1
                if i < 0:
                    i = 0
                elif i > n - 2:
                    i = n - 2
                denom = g[i + 1] - g[i]
                f = (x - g[i]) / denom if denom != 0 else 0.0
            idx_lo.append(i)
            frac.append(f)
        total = 0.0
        for corner in range(2 ** ndim):
            weight = 1.0
            idx = []
            for d in range(ndim):
                bit = (corner >> d) & 1
                weight *= frac[d] if bit else (1 - frac[d])
                idx.append(idx_lo[d] + bit)
            if weight != 0.0:
                total += weight * float(values[tuple(idx)])
        result.append(total)
    return np.asarray(result)


def multilinear_interp_point_multi(grids, arrays, point):
    """단일 좌표 `point` 에서 `arrays` 여러 배열을 같은 가중치로 보간한 값 list(복사본 -- 본문은 옛 206행)."""
    import bisect
    ndim = len(grids)
    idx_lo, frac = [], []
    for d in range(ndim):
        g = grids[d]
        n = len(g)
        x = point[d]
        if x <= g[0]:
            i, f = 0, 0.0
        elif x >= g[-1]:
            i, f = n - 2, 1.0
        else:
            i = bisect.bisect_right(g, x) - 1
            if i < 0:
                i = 0
            elif i > n - 2:
                i = n - 2
            denom = g[i + 1] - g[i]
            f = (x - g[i]) / denom if denom != 0 else 0.0
        idx_lo.append(i)
        frac.append(f)
    totals = [0.0] * len(arrays)
    for corner in range(2 ** ndim):
        weight = 1.0
        idx = []
        for d in range(ndim):
            bit = (corner >> d) & 1
            weight *= frac[d] if bit else (1 - frac[d])
            idx.append(idx_lo[d] + bit)
        if weight != 0.0:
            idx_t = tuple(idx)
            for ai, arr in enumerate(arrays):
                totals[ai] += weight * float(arr[idx_t])
    return totals
