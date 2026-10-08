"""feedforward 묶음의 상호컨덕턴스 비 r_ff = G_ff / gm_in(B_b) (설계 41 §1.12.2-5, 40 §3.8-8 `ff_gm_ratio`, 체크리스트 D-J2).

진입점: `ff_gm_ratio(ss, vstruct, rel_tols=None) -> FfRatio`.

* G_ff = **B_b 입력 넷 전압에서 merge 노드 단락 전류까지의 FF 경로 트랜스컨덕턴스**(FF 안의 미러 비 포함). B_b = 처음 우회한 주경로 블록. B_b 의 국소 해
  (`block_local_gain`: 입력 구동 = 단위 구동 -- 하나 1 V·둘 ±1/2 V, 차동 입력 1 V)에 FF 묶음 소자를 합류시키고 merge 넷을 접지(단락)한 채, FF 소자들이 merge 로 내는
  전류 크기 |I_ff|(FF 소자 컨덕턴스 행렬의 merge 행·해 벡터)를 입력 차동 1 V 로 나눈다. 탭이 B_b 입력 넷이면(2단 우회) FF 셀이 입력 넷에 직접 게이트, 탭이 B_b 내부
  노드이면(1단 우회) B_b 의 입력 셀 -> 탭 -> FF 셀 경로가 모두 이 풀이에 든다.
* gm_in(B_b) = B_b input 셀들의 gm 평균(차동 쌍이면 한 쪽 gm = 쌍의 차동 트랜스컨덕턴스, 입력 셀이 하나면 그 gm).
* 부호: 값은 크기 비 r_ff = |G_ff|/gm_in(관계 r_ff = 1 이 영점 상쇄 후보). 경로 부호는 `block_residual` 의 `ff_contrib.sign` 이 싣는다.
* metric 값 `ratio` = FF 묶음 r_ff 의 최댓값, 묶음별 표 `per_ff` = (id, r_ff, G_ff, gm_in). 묶음이 없으면 값 없음(`no_feedforward`).
* 분해능: 풀이에 스탬프된 소자의 gm·gmb·gds 를 한 번에 하나씩 +ε_i·|p|(`rel_tols` = (gm/ID)·tol_V)로 흔든 재풀이의 |Δr| 합(최대 r 묶음).
  허용오차가 없는 소자가 있으면 None.
* 정의 불가: 묶음 없음(`no_feedforward`), 우회 블록·merge 블록을 구조에서 못 찾음(`bypassed_block_missing`), input 셀 없음(`bypassed_input_cells_missing`),
  gm_in = 0(`gm_in_zero`), 계 특이(`singular_dc`).
"""
import dataclasses

import numpy

from ._helpers_nodal import conductance_matrix
from ._helpers_view import PARAMETER_ORDER
from .aux_types import FfRatio
from .block_model import block_local_gain
from .mna_types import Undefined
from .records import SmallSignalCircuit

QUANTITY = "ratio"


def _undefined(code, detail=()):
    return (Undefined(QUANTITY, code, "definitional", detail),)


def _one(ss, f, vstruct):
    """묶음 하나 -> (r_ff, G_ff, gm_in, 스탬프 소자 라벨 tuple) 또는 사유 코드 문자열."""
    blocks = {b.key: b for b in vstruct.blocks}
    bb = blocks.get(f.bypassed)
    if bb is None:
        return "bypassed_block_missing"
    if not f.bypassed_input_cells:
        return "bypassed_input_cells_missing"
    index = {net: i for i, net in enumerate(ss.nodes)}
    every = {n for b in vstruct.blocks for n in b.nodes}
    others_ff = tuple(sorted({m for g in vstruct.ff if g.id != f.id for m in g.members}))
    found = block_local_gain(ss, bb, None, others=every - set(bb.nodes), exclude=others_ff, extra=f.members)
    if found.gain is None and any(u.code == "singular_dc" for u in found.undefined):
        return "singular_dc"
    volt = numpy.zeros(len(ss.nodes))
    for net, v in found.node_v:
        volt[index[net]] = v
    mos = {m.label: m for m in ss.circuit.mos}
    ff_circuit = SmallSignalCircuit(mos=tuple(m for m in ss.circuit.mos if m.label in f.members),
                                    resistors=tuple(r for r in ss.circuit.resistors if r.label in f.members))
    current = (conductance_matrix(ff_circuit, len(ss.nodes)) @ volt)[index[f.merge]]
    gm_in = sum(mos[c].gm for c in f.bypassed_input_cells if c in mos) / len(f.bypassed_input_cells)
    if not gm_in > 0:
        return "gm_in_zero"
    return abs(float(current)) / gm_in, abs(float(current)), gm_in, found.members


def _perturbed(ss, label, parameter, step):
    mos = tuple(dataclasses.replace(m, **{PARAMETER_ORDER[parameter]: getattr(m, PARAMETER_ORDER[parameter]) + step}) if m.label == label else m
                for m in ss.circuit.mos)
    return dataclasses.replace(ss, circuit=dataclasses.replace(ss.circuit, mos=mos))


def ff_gm_ratio(ss, vstruct, rel_tols=None):
    if not vstruct.ff:
        return FfRatio(None, undefined=_undefined("no_feedforward"))
    rows = []
    for f in vstruct.ff:
        found = _one(ss, f, vstruct)
        if isinstance(found, str):
            return FfRatio(None, undefined=_undefined(found, (("ff", f.id),)))
        rows.append((f, found))
    per_ff = tuple((f.id, r[0], r[1], r[2]) for f, r in rows)
    top_f, top = max(rows, key=lambda row: row[1][0])
    tols = rel_tols or {}
    mos = {m.label: m for m in ss.circuit.mos}
    resolution = 0.0
    for label in top[3]:
        if label not in mos:
            continue
        eps = tols.get(label)
        if eps is None:
            resolution = None
            break
        for parameter, name in enumerate(PARAMETER_ORDER):
            value = getattr(mos[label], name)
            if value == 0.0 or eps == 0.0:
                continue
            again = _one(_perturbed(ss, label, parameter, eps * value), top_f, vstruct)
            if isinstance(again, str):
                resolution = None
                break
            resolution += abs(again[0] - top[0])
        if resolution is None:
            break
    return FfRatio(top[0], per_ff, resolution)
