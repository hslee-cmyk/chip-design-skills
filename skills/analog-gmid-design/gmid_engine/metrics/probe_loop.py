"""절단 회로 계의 Middlebrook 루프 이득 인수 (7a design 2.4·2.6, metrics CONTRACT 3.10 'PM 정의').

진입점: `probe_factor(response, pairs, weights) -> ProbeFactor`.

`response` = `cut_circuit` 의 프로브 여기 열·관측으로 조립한 계 하나의 `SystemResponse`(오라클의 두 `.ac` 실행 = 같은 계의 여기
열들 -- 조립 1회, ω 마다 LU 1회로 4k 열이 모두 풀린다). 열·관측은 이름이 아니라 구조로 찾는다: 노드 v 의 관측 = `Sense(v)`,
전류 열 = 전압·전하 없이 v 에만 전류를 넣는 열, 전하 열 = 전압·전류 없이 v 에만 전하를 넣는 열. 없거나 둘 이상이면 ValueError.
`pairs` = (n_k, x_k) 노드 쌍(`CutCircuit.pairs`), `weights` = 쌍마다 0 아닌 유한 가중(7a design 2.3 포트 role 가중).
격자 위 T 표본은 `_helpers_probe.probe_value`(오라클 `loop_gain` 과 같은 식)로 한 번 계산해 보관한다(재계산 없음 -- 인수 하나에
1회). T 의 극점·영점(상단 괄호용)은 항등식 1/(1 + T) = Q, Q·wᵀw = wᵀV_n(전압 주입) + wᵀ(w − I)(전류 주입) 에서 구한다:
Q 는 프로브 전압원 k 개를 넣은 절단 회로(= 원래 회로) 두 벌을 묶은 한 계의 전달함수 H + wᵀw 라서,
T = −H/(H + wᵀw) -- 영점 = H 의 영점, 극점 = H + wᵀw 의 영점(증강 pencil, `_helpers_pencil.finite_eigs`). 공통 근(분리 모드)은
극점·영점 양쪽에 같이 들어가 상계를 느슨하게 할 뿐 틀리게 하지 않는다.
"""
import dataclasses
import math

import numpy

from ._helpers_pencil import finite_eigs
from ._helpers_probe import probe_value
from .mna_types import ProbeFactor, SystemResponse


def _check(response, pairs, weights):
    if not isinstance(response, SystemResponse):
        raise TypeError("probe_factor 는 SystemResponse 를 받는다")
    if not isinstance(pairs, tuple) or not pairs:
        raise TypeError("probe_factor: pairs 는 비어 있지 않은 (n, x) 노드 쌍 tuple 이어야 한다")
    nodes = []
    for pair in pairs:
        try:
            first, second = pair
        except (TypeError, ValueError) as exc:
            raise TypeError("probe_factor: pairs 원소는 (정수, 정수) 쌍이어야 한다: %r" % (pair,)) from exc
        if not isinstance(pair, tuple) or not all(isinstance(v, int) and not isinstance(v, bool) for v in pair):
            raise TypeError("probe_factor: pairs 원소는 (정수, 정수) 쌍이어야 한다: %r" % (pair,))
        nodes.extend((first, second))
    if len(set(nodes)) != len(nodes):
        raise ValueError("probe_factor: pairs 에 같은 노드가 두 번 나온다: %r" % (pairs,))
    if not isinstance(weights, tuple) or len(weights) != len(pairs):
        raise TypeError("probe_factor: weights 는 pairs 와 같은 길이의 tuple 이어야 한다")
    for w in weights:
        if isinstance(w, bool) or not isinstance(w, (int, float)) or not math.isfinite(w) or w == 0:
            raise ValueError("probe_factor: 가중은 0 아닌 유한 실수여야 한다: %r" % (w,))


def _single(found, what, node):
    if len(found) != 1:
        raise ValueError("probe_factor: 노드 %r 의 %s 이 정확히 하나가 아니다(%d 개) -- cut_circuit 의 프로브 열·관측으로 "
                         "조립한다" % (node, what, len(found)))
    return found[0]


def _layout(system, nodes):
    rows, cur, chg, cur_scale, chg_scale = [], [], [], [], []
    for node in nodes:
        if node not in system.nodes:
            raise ValueError("probe_factor: 절단 노드 %r 이 미지수 노드가 아니다(고정 노드는 끊을 수 없다)" % (node,))
        rows.append(_single([r for r, s in enumerate(system.senses) if s.pos == node and s.neg is None],
                            "관측", node))
        j = _single([j for j, e in enumerate(system.excitations)
                     if not e.voltages and not e.charges and len(e.currents) == 1 and e.currents[0][0] == node
                     and e.currents[0][1]], "전류 주입 열", node)
        cur.append(j)
        cur_scale.append(system.excitations[j].currents[0][1])
        j = _single([j for j, e in enumerate(system.excitations)
                     if not e.voltages and not e.currents and len(e.charges) == 1 and e.charges[0][0] == node
                     and e.charges[0][1]], "전하 주입 열", node)
        chg.append(j)
        chg_scale.append(system.excitations[j].charges[0][1])
    return tuple(rows), tuple(cur), tuple(chg), tuple(cur_scale), tuple(chg_scale)


def _roots(system, pairs, weights):
    """T 의 (극점, 영점) -- 모듈 docstring 의 증강 pencil."""
    if system.defects:
        return (), ()
    n = system.G.shape[0]
    k = len(pairs)
    size = n + k
    w = numpy.array(weights, dtype=float)
    at = {node: i for i, node in enumerate(system.nodes)}
    n_idx = [at[a] for a, _ in pairs]
    x_idx = [at[b] for _, b in pairs]
    charge = sorted(system.charge_nodes)
    # 절단 노드가 용량 전용이면(ω = 0 열 선택과 같은 규칙) 프로브 전류 j = s·j', 2회 주입은 전하 w(= 전류 s·w)로 둔다 --
    # T 는 2회 실험의 공통 배율에 무관하고, 그 노드 KCL 행이 s 로 나뉘어 떨어진다.
    scaled = bool(set(n_idx + x_idx) & set(charge))
    probe = numpy.zeros((n, k))
    probe[n_idx, range(k)] = 1.0
    probe[x_idx, range(k)] = -1.0
    a0 = numpy.zeros((size, size))
    e0 = numpy.zeros((size, size))
    a0[:n, :n] = system.G
    e0[:n, :n] = system.C
    (e0 if scaled else a0)[:n, n:] = probe
    a0[n:, :n] = probe.T
    # 용량 전용 노드 행(G 행 0)은 s·(C_F·v + P_F·j') = s·(우변) 이라 s 로 나눈다(`solve_dc_limit` 의 전하 보존 식과 같은 변환,
    # 해 불변). 나누지 않으면 원점 근이 겹친 결함 고유값이 되어 QZ 가 eps^(1/m) 규모로 흩뜨린다(허위 근).
    a0[charge, :] = e0[charge, :]
    e0[charge, :] = 0.0
    bg = numpy.zeros(2 * size)
    bc = numpy.zeros(2 * size)
    c = numpy.zeros(2 * size)
    bg[n:size] = w                      # 1회: 프로브 전압 V(n) − V(x) = w
    c[n_idx] = w                        # 관측 wᵀV_n
    for i, wi in zip(n_idx, w):         # 2회: n 으로 주입(프로브 0 V) -- scaled 면 전하 w, 나눈 행에서는 상수
        (bc if scaled and i not in charge else bg)[size + i] = wi
    c[size + n:] = -w                   # 관측 −wᵀI (I = n → x 프로브 전류; scaled 면 j' = 배율 걷힌 I)
    full = 2 * size
    a = numpy.zeros((full + 1, full + 1))
    e = numpy.zeros((full + 1, full + 1))
    a[:size, :size] = a0
    a[size:full, size:full] = a0
    e[:size, :size] = e0
    e[size:full, size:full] = e0
    a[:full, full] = -bg
    e[:full, full] = -bc
    a[full, :full] = c
    zeros = finite_eigs(a, e)
    a[full, full] = w @ w
    poles = finite_eigs(a, e)
    return poles, zeros


def probe_factor(response, pairs, weights):
    """절단 회로 계 응답, (n, x) 노드 쌍, 가중 -> `ProbeFactor`(격자 위 T 표본·T 의 근·사유를 한 번 계산해 담는다)."""
    _check(response, pairs, weights)
    system = response.system
    nodes = tuple(a for a, _ in pairs) + tuple(b for _, b in pairs)
    rows, cur, chg, cur_scale, chg_scale = _layout(system, nodes)
    probe = ProbeFactor(
        response=response, pairs=pairs, weights=tuple(float(w) for w in weights), rows=rows, current_columns=cur,
        charge_columns=chg, current_scales=cur_scale, charge_scales=chg_scale,
    )
    zero_errors = numpy.zeros(system.sense_direct.shape)
    samples = []
    undefined = []
    for omega, values in zip(response.omegas, response.values):
        value, _, why = probe_value(probe, float(omega), values, zero_errors, response.undefined)
        samples.append(value)
        undefined.extend(u for u in why if u not in undefined)
    poles, zeros = _roots(system, pairs, probe.weights)
    return dataclasses.replace(
        probe, samples=numpy.array(samples, dtype=complex), poles=poles, zeros=zeros, undefined=tuple(undefined),
    )
