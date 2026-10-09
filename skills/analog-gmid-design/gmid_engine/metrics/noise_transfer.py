"""잡음원에서 관측까지의 전달 -- as-built MNA 수반(adjoint) 풀이 (설계 41 §7.3 '전달', 단위 U8).

진입점: `noise_transfer(system, row, a_nodes, b_nodes, omegas, *, column=None, parameters=None, with_omega=False) -> NoiseTransfer`.

* 같은 조립 `MnaSystem`(G, C)을 쓴다 -- 다시 조립하지 않는다(WP-23). 관측 행 `row` 의 수반 y = (G + jωC)⁻ᵀ·sᵀ(ω 마다 풀이 1회, 격자는 한 번의 묶음 풀이)에서
  모든 잡음원의 전달이 한꺼번에 나온다: 잡음원 k = 노드 b_k 에서 a_k 로 흐르는 단위 전류이면 Z_k = y[a_k] − y[b_k](고정 노드는 0).
* 전달 뷰 열 j 가 주어지면 H = yᵀ·(BG_j + jω·BC_j) + sense_direct(입력 환산의 분모 -- 선언된 전달 뷰의 전달함수, gain metric 과 같은 계).
* `parameters`(`ParameterSet`)가 주어지면 1차 미분을 낸다: ∂Z_k/∂p = −yᵀ(∂A/∂p)·X_k, X = A⁻¹·E(E = 잡음원 주입 열 -- 격자당 풀이 1회 더),
  ∂H/∂p = −yᵀ(∂A/∂p)·x_full(x_full = 열 j 의 해 + 구동 고정 노드 진폭). ∂A/∂p 는 `lut_parameters` 가 만든 단위 스탬프 항목(스탬프 식의 정본 하나)이고
  C 항목에는 jω 를 곱한다. 항목 -> 파라미터 합산은 희소 one-hot 행렬이고 ω 점마다 (항목 × 잡음원) 중간 배열 하나만 만든다(격자 전체 3차원 중간 배열 없음).
  `with_omega` 면 ∂Z/∂ω = −yᵀ(jC)X, ∂H/∂ω = yᵀ·j(BC_j − C·x_j) 도 낸다(`response_sensitivity` 와 같은 식).
* 예외를 던지지 않는다 -- 구조 결함·특이는 `undefined`(값 배열 None). ω 는 모두 양수(ω = 0 의 전하 보존 극한은 이 함수의 일이 아니다).
"""
import numpy
from scipy import sparse

from .mna_types import Undefined
from .noise_types import NoiseTransfer


def _fail(omegas, code, category, detail=()):
    return NoiseTransfer(omegas, undefined=(Undefined("response", code, category, detail),))


def _injections(count, n, rows_a, rows_b):
    inject = numpy.zeros((n, count))
    at = numpy.arange(count)
    inject[rows_a[rows_a < n], at[rows_a < n]] += 1.0
    inject[rows_b[rows_b < n], at[rows_b < n]] -= 1.0
    return inject


def _entries(system, parameters):
    """파라미터 항목 -> (행 미지수 번호 또는 -1, 열 전체 번호(미지수 다음 고정 노드), 항목 -> 파라미터 희소 one-hot (P, E))."""
    nodes = numpy.array(system.nodes + system.fixed_nodes, dtype=int)
    n = len(system.nodes)
    order = numpy.argsort(nodes)
    wanted = numpy.concatenate((parameters.rows, parameters.cols)).astype(int)
    found = numpy.searchsorted(nodes[order], wanted)
    found[found >= nodes.size] = 0
    missing = sorted({int(v) for v in wanted[nodes[order][found] != wanted]})
    if missing:
        raise ValueError("noise_transfer: 파라미터 스탬프 노드 %r 가 이 계에 없다(다른 회로의 ParameterSet)" % (missing,))
    full = order[found].astype(int)
    size = parameters.rows.size
    rows = numpy.where(full[:size] < n, full[:size], -1)
    cols = full[size:]
    onehot = sparse.csr_matrix((numpy.ones(size), (parameters.owner, numpy.arange(size))), shape=(len(parameters.params), size))
    return rows, cols, onehot


def _drive(system, column):
    at = {node: i for i, node in enumerate(system.fixed_nodes)}
    drive = numpy.zeros(len(system.fixed_nodes))
    for node, amp in system.excitations[column].voltages:
        drive[at[node]] = amp
    return drive


def noise_transfer(system, row, a_nodes, b_nodes, omegas, *, column=None, parameters=None, with_omega=False):
    omegas = numpy.asarray(omegas, dtype=float).reshape(-1)
    if not (omegas > 0).all() or not numpy.isfinite(omegas).all():
        raise ValueError("noise_transfer: ω 는 모두 양의 유한 수여야 한다: %r" % (omegas,))
    n = len(system.nodes)
    if system.defects:
        return NoiseTransfer(omegas, undefined=system.defects)
    if n == 0:
        return _fail(omegas, "no_unknown_nodes", "structural")
    count, k = len(a_nodes), omegas.size
    index = {node: i for i, node in enumerate(system.nodes)}
    rows_a = numpy.array([index.get(int(v), n) for v in a_nodes], dtype=int)
    rows_b = numpy.array([index.get(int(v), n) for v in b_nodes], dtype=int)
    jw = complex(0, 1) * omegas
    amat = system.G[None, :, :] + jw[:, None, None] * system.C[None, :, :]
    sense = system.sense_rows[row].astype(complex)
    try:
        y = numpy.linalg.solve(amat.mT, numpy.broadcast_to(sense, (k, n))[..., None])[..., 0]
    except numpy.linalg.LinAlgError:
        return _fail(omegas, "singular_mna", "numeric")
    if not numpy.isfinite(y).all():
        return _fail(omegas, "singular_mna", "numeric")
    y_ext = numpy.concatenate((y, numpy.zeros((k, 1), dtype=complex)), axis=1)
    z = y_ext[:, rows_a] - y_ext[:, rows_b]
    h = rhs = None
    if column is not None:
        rhs = system.BG[:, column][None, :] + jw[:, None] * system.BC[:, column][None, :]
        h = numpy.einsum("kn,kn->k", y, rhs) + system.sense_direct[row, column]
    if parameters is None and not with_omega:
        return NoiseTransfer(omegas, z=z, h=h)
    inject = numpy.broadcast_to(_injections(count, n, rows_a, rows_b), (k, n, count))
    x = numpy.linalg.solve(amat, inject)
    x_col = None if column is None else numpy.linalg.solve(amat, rhs[..., None])[..., 0]
    dz = dh = dz_dw = dh_dw = None
    if parameters is not None:
        ent_row, ent_col, onehot = _entries(system, parameters)
        coeff = parameters.values[None, :] * numpy.where(parameters.capacitive[None, :], jw[:, None], 1.0)
        on_z = (ent_row >= 0) & (ent_col < n)
        select_z = onehot[:, numpy.nonzero(on_z)[0]]
        weight_z = -(coeff[:, on_z] * y[:, ent_row[on_z]])                      # (k, E'): −coeff·y[row]
        dz = numpy.empty((k, onehot.shape[0], count), dtype=complex)
        for i in range(k):
            dz[i] = select_z @ (weight_z[i][:, None] * x[i][ent_col[on_z], :])
        if column is not None:
            full = numpy.concatenate((x_col, numpy.broadcast_to(_drive(system, column), (k, len(system.fixed_nodes)))), axis=1)
            on_h = ent_row >= 0
            select_h = onehot[:, numpy.nonzero(on_h)[0]]
            dh = (select_h @ (-(coeff[:, on_h] * y[:, ent_row[on_h]] * full[:, ent_col[on_h]])).T).T
    if with_omega:
        c_y = y @ system.C
        dz_dw = -complex(0, 1) * numpy.einsum("km,kmj->kj", c_y, x)
        if column is not None:
            dh_dw = complex(0, 1) * (y @ system.BC[:, column] - numpy.einsum("km,km->k", c_y, x_col))
    return NoiseTransfer(omegas, z=z, h=h, dz=dz, dh=dh, dz_dw=dz_dw, dh_dw=dh_dw)
