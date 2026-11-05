"""블록 국소 모델의 스탬프 조립과 행(축 index 조합) 묶음 풀이 (설계 41 §2.5 스탬프 조립 하나, §4.2 '행마다 봉인 없이 블록 국소 모델을 풀어 gain 을 구한다').

공개 함수:
* `block_stamp_matrix(nets, mos, res, batch=1) -> ndarray (batch, N, N)` -- 블록 국소 모델 KCL 행렬 조립의 유일한 자리(봉인 모드 `block_model.block_local_gain` 과 행 모드 `row_gains` 와
  FF 전류 `ff_gm_ratio` 가 같은 함수를 부른다: 값 출처만 다르고 미지수 집합과 조립이 같다). `nets` = 행렬 행·열의 넷 이름 순서, `mos` = `(d, g, s, b, gm, gds, gmb)`
  (넷 이름, 값은 스칼라 또는 (batch,)), `res` = `(a, b, g)`. MOS 는 단자별 스탬프 `i(d→s) = gm·(vg−vs) + gds·(vd−vs) + gmb·(vb−vs)` -- drain 행 +, source 행 −,
  CS·CG·CD 를 분기하지 않는다. `nets` 밖 단자의 항은 버린다(그 넷 전압은 0 -- 구동 넷은 부르는 쪽이 `nets` 에 넣어 우변으로 옮긴다).
* `row_gains(model, tables, idx, cont=None) -> ndarray (B,)`  (`model` = `BlockModel`, `tables` = `ParamTables`, `idx` = (B, 축 수) 정수 격자 index,
  `cont` = {축 index: (B,) 실수} 연속 축(`current`·`resistor`)의 값을 격자 값 대신 직접 줄 때, `L` 축이면 그 L(m)을 `tables.lookup_at_l` 로 읽는다 -- 같은 bin 안쪽 점).

행마다 소신호 MNA 를 조립한다(ω → 0): MOS 는 `gm = x·I`, `gds = y·I`, `gmb = z·I`(x, y, z = 파라미터 표, I = 전류식을 행의 θ 전류 값으로 평가), 저항은 컨덕턴스.
KCL 행렬 `A·V = R` 을 (B, n, n) 묶음으로 풀고 gain = max_패턴 |Σ 부호·V(출력)| 를 낸다(진폭 비, dB 아님). 유효하지 않은 행(파라미터 NaN·전류 ≤ 0·특이 행렬)은 NaN.
미지수가 없으면(`nodes` 비어 있음) 출력은 구동 넷의 가중 합이다. 행 사이 계산은 서로 독립이고 입력만으로 정해지므로 결정론적이다.
"""
import numpy as np


def block_stamp_matrix(nets, mos, res, batch=1):
    position = {net: i for i, net in enumerate(nets)}
    a = np.zeros((batch, len(nets), len(nets)))

    def put(row_net, col_net, coeff):
        row, col = position.get(row_net), position.get(col_net)
        if row is not None and col is not None:
            a[:, row, col] += coeff

    def value(v):
        return np.broadcast_to(np.asarray(v, dtype=float), (batch,))

    for d, g, s, b, gm, gds, gmb in mos:
        gm, gds, gmb = value(gm), value(gds), value(gmb)
        for row_net, sign in ((d, 1), (s, -1)):
            put(row_net, g, sign * gm)
            put(row_net, d, sign * gds)
            put(row_net, b, sign * gmb)
            put(row_net, s, -sign * (gm + gds + gmb))
    for net_a, net_b, g in res:
        g = value(g)
        for row_net, col_net, sign in ((net_a, net_a, 1), (net_b, net_b, 1), (net_a, net_b, -1), (net_b, net_a, -1)):
            put(row_net, col_net, sign * g)
    return a


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
    valid = np.ones(batch, dtype=bool)

    def axis_value(axis):
        return np.asarray(cont[axis], dtype=float) if axis in cont else np.asarray(model.axes[axis].values, dtype=float)[idx[:, axis]]

    stamps = []
    for m in model.mos:
        i_vgs = idx[:, m.vgs_axis]
        i_vds = idx[:, m.vds_axis] if m.vds_axis >= 0 else tables.vds_of_vgs[i_vgs]
        i_vsb = idx[:, m.vsb_axis] if m.vsb_axis >= 0 else np.zeros(batch, dtype=int)
        if m.l_axis in cont:                                            # E-16: 앵커 사이 같은 bin 안쪽 L 점
            x, y, z = tables.lookup_at_l(m.kind, np.asarray(cont[m.l_axis], dtype=float), i_vds, i_vsb, i_vgs)
        else:
            x, y, z = tables.lookup(m.kind, idx[:, m.l_axis], i_vds, i_vsb, i_vgs)
        current = np.zeros(batch)
        for axis, coeff in m.current:
            current = current + (coeff if axis < 0 else coeff * axis_value(axis))
        valid &= np.isfinite(x) & np.isfinite(y) & np.isfinite(z) & (current > 0)
        stamps.append((m.d, m.g, m.s, m.bulk, x * current, y * current, z * current))
    resistors = tuple((res.a, res.b, np.full(batch, res.g_fixed) if res.axis < 0 else axis_value(res.axis)) for res in model.res)
    nets = tuple(model.nodes) + tuple(model.driven)
    full = block_stamp_matrix(nets, stamps, resistors, batch)
    a = full[:, :n_nodes, :n_nodes]
    drive_weights = np.stack([weights[net] for net in model.driven], axis=0) if model.driven else np.zeros((0, n_pat))
    r = -(full[:, :n_nodes, n_nodes:] @ drive_weights)                 # 구동 넷 전압(패턴 가중)을 우변으로
    solved = _solve(a, r) if n_nodes else np.zeros((batch, 0, n_pat))
    total = np.zeros((batch, n_pat))
    for net, sign in model.outputs:
        if net in position:
            total = total + sign * solved[:, position[net], :]
        elif net in weights:
            total = total + sign * weights[net][None, :]
    gain = np.max(np.abs(total), axis=1)
    return np.where(valid & np.isfinite(gain), gain, np.nan)
