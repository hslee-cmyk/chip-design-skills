"""블록 국소 모델의 행(축 index 조합) 묶음 풀이 (설계 41 §4.2 '행마다 봉인 없이 블록 국소 모델을 풀어 gain 을 구한다').

진입점: `row_gains(model, tables, idx, cont=None) -> ndarray (B,)`  (`model` = `BlockModel`, `tables` = `ParamTables`, `idx` = (B, 축 수) 정수 격자 index,
`cont` = {축 index: (B,) 실수} 연속 축(`current`·`resistor`)의 값을 격자 값 대신 직접 줄 때).

행마다 소신호 MNA 를 조립한다(ω → 0): MOS 는 `gm = x·I`, `gds = y·I`, `gmb = z·I`(x, y, z = 파라미터 표, I = 전류식을 행의 θ 전류 값으로 평가), 저항은 컨덕턴스.
KCL 행렬 `A·V = R` 을 (B, n, n) 묶음으로 풀고 gain = max_패턴 |Σ 부호·V(출력)| 를 낸다(진폭 비, dB 아님). 유효하지 않은 행(파라미터 NaN·전류 ≤ 0·특이 행렬)은 NaN.
미지수가 없으면(`nodes` 비어 있음) 출력은 구동 넷의 가중 합이다. 행 사이 계산은 서로 독립이고 입력만으로 정해지므로 결정론적이다.
"""
import numpy as np


def _solve(a, r):
    try:
        return np.linalg.solve(a, r)
    except np.linalg.LinAlgError:
        out = np.full(r.shape, np.nan)
        for b in range(a.shape[0]):
            try:
                out[b] = np.linalg.solve(a[b], r[b])
            except np.linalg.LinAlgError:
                continue
        return out


def row_gains(model, tables, idx, cont=None):
    idx = np.asarray(idx, dtype=int)
    batch = idx.shape[0]
    cont = {} if cont is None else cont
    position = {net: i for i, net in enumerate(model.nodes)}
    n_nodes, n_pat = len(model.nodes), len(model.patterns)
    weights = {net: np.asarray([dict(p).get(net, 0) for p in model.patterns], dtype=float) for net in model.driven}
    a = np.zeros((batch, n_nodes, n_nodes))
    r = np.zeros((batch, n_nodes, n_pat))
    valid = np.ones(batch, dtype=bool)

    def axis_value(axis):
        return np.asarray(cont[axis], dtype=float) if axis in cont else np.asarray(model.axes[axis].values, dtype=float)[idx[:, axis]]

    def put(row_net, col_net, coeff):
        row = position.get(row_net)
        if row is None:
            return
        col = position.get(col_net)
        if col is not None:
            a[:, row, col] += coeff
        elif col_net in weights:
            r[:, row, :] -= coeff[:, None] * weights[col_net][None, :]

    for m in model.mos:
        i_vgs = idx[:, m.vgs_axis]
        i_vds = idx[:, m.vds_axis] if m.vds_axis >= 0 else tables.vds_of_vgs[i_vgs]
        i_vsb = idx[:, m.vsb_axis] if m.vsb_axis >= 0 else np.zeros(batch, dtype=int)
        x, y, z = tables.lookup(m.kind, idx[:, m.l_axis], i_vds, i_vsb, i_vgs)
        current = np.zeros(batch)
        for axis, coeff in m.current:
            current = current + (coeff if axis < 0 else coeff * axis_value(axis))
        valid &= np.isfinite(x) & np.isfinite(y) & np.isfinite(z) & (current > 0)
        gm, gds, gmb_ = x * current, y * current, z * current
        bulk = m.bulk
        for row_net, sign in ((m.d, 1), (m.s, -1)):
            put(row_net, m.g, sign * gm)
            put(row_net, m.d, sign * gds)
            put(row_net, bulk, sign * gmb_)
            put(row_net, m.s, -sign * (gm + gds + gmb_))
    for res in model.res:
        g = np.full(batch, res.g_fixed) if res.axis < 0 else axis_value(res.axis)
        for row_net, col_net, sign in ((res.a, res.a, 1), (res.b, res.b, 1), (res.a, res.b, -1), (res.b, res.a, -1)):
            put(row_net, col_net, sign * g)
    solved = _solve(a, r) if n_nodes else np.zeros((batch, 0, n_pat))
    total = np.zeros((batch, n_pat))
    for net, sign in model.outputs:
        if net in position:
            total = total + sign * solved[:, position[net], :]
        elif net in weights:
            total = total + sign * weights[net][None, :]
    gain = np.max(np.abs(total), axis=1)
    return np.where(valid & np.isfinite(gain), gain, np.nan)
