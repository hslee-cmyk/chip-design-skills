"""MNA 조립 1회 (설계 design_mod1_lut_mod5_mna 3.3 '조립', 옛 `build_ac_network` SR:4067 의 목적만 계승).

진입점: `build_mna`.

ω 와 무관한 실수 G·C 와 여기 열 BG·BC 를 한 번 만든다. 주파수마다 다시 스탬프하지 않는다(옛 SR:4104 결함).
고정 노드 = 교류접지(선언 인덱스) ∪ 전압 구동 노드. 이름 리터럴('gnd' 등)·저항 기본값이 없다.

미지수 x(미지수 노드 전압), 고정 노드 전압 u = U·e_j(열 j 의 구동 진폭)에서 KCL:
    (G_uu + sC_uu)·x = −(G_uf + sC_uf)·u + i_inj   ->   BG = −G_uf·U + I_inj,  BC = −C_uf·U.
관측 y = c_u·x + c_f·u  ->  `sense_row` = c_u, `sense_direct` = c_f·U.
"""
import numpy

from gmid_engine.core import StructureUnresolvedError

from .mna_types import MnaSystem
from .records import Excitation, Sense, SmallSignalCircuit
from .stamp_mos import mos_stamps
from .stamp_two_terminal import two_terminal_stamps


def _reject(reason, **detail):
    detail["reason"] = reason
    raise StructureUnresolvedError(detail=detail)


def _check_inputs(circuit, excitations, sense):
    if not isinstance(circuit, SmallSignalCircuit):
        raise TypeError("build_mna: circuit 는 SmallSignalCircuit 이어야 한다")
    if not isinstance(excitations, tuple) or not excitations:
        raise TypeError("build_mna: excitations 는 비어 있지 않은 Excitation tuple 이어야 한다")
    for e in excitations:
        if not isinstance(e, Excitation):
            raise TypeError("build_mna: excitations 원소는 Excitation 이어야 한다: %r" % (e,))
    names = tuple(e.name for e in excitations)
    if len(set(names)) != len(names):
        _reject("excitation_name_duplicate", columns=names)
    if not isinstance(sense, Sense):
        raise TypeError("build_mna: sense 는 Sense 여야 한다")


def build_mna(circuit, excitations, sense):
    """`SmallSignalCircuit` + 여기 열 tuple + `Sense` -> `MnaSystem`. 소자마다 스탬프 함수를 정확히 한 번 부른다.

    거부(`StructureUnresolvedError`, detail `reason`): 여기 열 이름 중복, 구동 노드가 교류접지와 겹침,
    전류 주입 노드가 고정 노드, 관측 노드가 구동되지 않는 고정 노드뿐, 고립 미지수 노드(미지수 블록에서 G·C 의 그 행이
    모두 0 = KCL 식 없음, 또는 그 열이 모두 0 = 미지수가 어느 식에도 없음 -- 모든 ω 에서 특이).
    `dc_floating` = 미지수 블록 G 의 그 행 또는 열이 0 인 노드(용량으로만 이어짐, ω = 0 에서만 특이)."""
    _check_inputs(circuit, excitations, sense)
    ground = frozenset(circuit.ac_ground)
    driven = frozenset(n for e in excitations for n, _ in e.voltages)
    clash = sorted(ground & driven)
    if clash:
        _reject("driven_node_is_ac_ground", nodes=tuple(clash))
    fixed = ground | driven
    stamps = tuple(mos_stamps(m) for m in circuit.mos) + tuple(
        two_terminal_stamps(p) for p in circuit.resistors + circuit.capacitors
    )
    touched = set(fixed)
    for st in stamps:
        for row, col, _ in st.g + st.c:
            touched.add(row)
            touched.add(col)
    for e in excitations:
        touched.update(n for n, _ in e.currents)
    touched.add(sense.pos)
    if sense.neg is not None:
        touched.add(sense.neg)
    unknown = tuple(sorted(touched - fixed))
    fixed_order = tuple(sorted(fixed))
    injected_fixed = sorted({n for e in excitations for n, _ in e.currents} & fixed)
    if injected_fixed:
        _reject("current_injection_into_fixed_node", nodes=tuple(injected_fixed))
    index = {n: i for i, n in enumerate(unknown + fixed_order)}
    total = len(index)
    g_full = numpy.zeros((total, total))
    c_full = numpy.zeros((total, total))
    for st in stamps:
        for row, col, value in st.g:
            g_full[index[row], index[col]] += value
        for row, col, value in st.c:
            c_full[index[row], index[col]] += value
    n = len(unknown)
    isolated = tuple(
        unknown[i] for i in range(n)
        if not (g_full[i, :n].any() or c_full[i, :n].any()) or not (g_full[:n, i].any() or c_full[:n, i].any())
    )
    if isolated:
        _reject("isolated_node", nodes=isolated)
    dc_floating = tuple(unknown[i] for i in range(n) if not (g_full[i, :n].any() and g_full[:n, i].any()))
    m = len(excitations)
    drive = numpy.zeros((len(fixed_order), m))
    inject = numpy.zeros((n, m))
    for j, e in enumerate(excitations):
        for node, amp in e.voltages:
            drive[index[node] - n, j] = amp
        for node, amp in e.currents:
            inject[index[node], j] = amp
    full_sense = numpy.zeros(total)
    full_sense[index[sense.pos]] += 1.0
    if sense.neg is not None:
        full_sense[index[sense.neg]] -= 1.0
    sense_direct = full_sense[n:] @ drive
    observable = full_sense[:n].any() or any(full_sense[index[x]] for x in sorted(driven))
    if not observable:
        _reject("sense_on_undriven_fixed_node", nodes=(sense.pos, sense.neg))
    return MnaSystem(
        nodes=unknown,
        fixed_nodes=fixed_order,
        G=g_full[:n, :n],
        C=c_full[:n, :n],
        BG=inject - g_full[:n, n:] @ drive,
        BC=-(c_full[:n, n:] @ drive),
        sense_row=full_sense[:n],
        sense_direct=sense_direct,
        excitations=excitations,
        sense=sense,
        dc_floating=dc_floating,
    )
