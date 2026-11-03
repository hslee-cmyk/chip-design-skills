"""분해 합성 gain·MNA 잔차·FF 경로 기여·rout 잔차 (설계 41 §2.2, §1.12.2-4, 체크리스트 D-BM·D-J2).

진입점: `block_residual(ss, view, vstruct) -> BlockResidual`.

한 전달 뷰의 주경로 블록 사슬(stage 순)을 **앞 블록의 국소 해 전압을 다음 블록 입력으로** 이어 풀고(`block_local_gain` 을 블록마다 한 번, 입력 구동 = 사슬 전압),
감지 노드의 값을 분해 합성값으로 읽는다. 부호·차동 방향이 사슬 안에서 자동으로 일치하므로 블록 gain 의 곱 Π A_i 와 같다(단일 블록 사슬이면 정확히 같은 양).
* `gain_residual_db` = 전회로 DC 이득(본 모듈 노달 풀이 `full_gain_db`, `gain_ss_db` 의 T(0) 와 같은 양) − 20·log10|A_decomp|.
* feedforward 묶음(41 §1.12.2-4): FF 묶음 소자는 다른 블록에서는 뺀다(`exclude`)만 merge 블록의 국소 모형에는 **항상** 들어간다 -- FF 소자의 gds 부하는
  merge 블록(Z_merge)의 일부라 블록 gain·Z_out 에 반영된다. 주경로 사슬(탭 구동 없음) 감지값 = Π_main A_i(부하 포함 Z_merge). A_decomp 는 거기에 FF 탭 전압(사슬 해의
  탭 넷 전압)을 구동한 사슬 = Π_main A_i + Σ_ff A_in→tap·G_ff·Z_merge (선형 중첩, merge 블록이 마지막이 아니면 뒤 블록이 이어 받는다).
  `ff_contrib` = 그 묶음의 경로 항 A_in→tap·G_ff·Z_merge (그 묶음 탭만 구동한 사슬 − 구동 없는 사슬), `gain_db` = 20·log10|항|,
  `sign` = 항이 주경로 감지값과 같은 방향이면 +1(보강)·반대면 −1(상쇄).
* `rout_residual_ohm` = 전회로 출력 저항(출력 감지 쌍에 단위 전류, 입력 접지) − 감지 넷을 출력으로 갖는 마지막 블록의 국소 Z_out (DEC-66). 마지막 블록이 없으면 None.
* 블록 국소 gain 은 주경로 사슬(FF 없음)에서 낸다. 되먹임 수동소자(`decomposed_only`)가 있는 블록은 '분해값'으로만 표시된다(41 §2.2).
* 정의 불가(값으로): 뷰가 전달 뷰가 아님(`unsupported_view`), 전회로 계 특이(`singular_dc`), 합성값 0(`decomposed_zero`), 블록 없음(`no_blocks`).
"""
import math

from gmid_engine.core import AMPLITUDE_DB_PER_DECADE

from ._helpers_nodal import capacitance_matrix, conductance_matrix, nodal_factor, nodal_solve
from ._helpers_view import view_system
from .aux_types import BlockResidual, FfContribution
from .block_model import block_local_gain
from .mna_types import Undefined

QUANTITY = "gain_residual_db"


def _bare(view_id, code, detail=()):
    return BlockResidual(view_id, None, undefined=(Undefined(QUANTITY, code, "definitional", detail),))


def _db(value):
    return AMPLITUDE_DB_PER_DECADE * math.log10(abs(value)) if value != 0 else None


def _sense_value(volts, sense_p, sense_n):
    return volts.get(sense_p, 0.0) - (0.0 if sense_n is None else volts.get(sense_n, 0.0))


def _cascade(ss, vstruct, pairs, sense_nets, active, excluded):
    """주경로 사슬을 풀어 -> (감지값, 블록 결과 tuple, 켠 FF 의 탭 도달 여부). FF 소자는 항상 merge 블록 국소 모형에 스탬프한다(gds 부하는 merge 블록의
    일부 -- 블록 gain·Z_out 이 과대평가되지 않게). `active` 인 묶음만 탭 전압으로 구동한다(나머지는 탭 0 -> gm 항 없음, gds 부하만)."""
    volts = dict(pairs)
    results = []
    reached = True
    every = {n for b in vstruct.blocks for n in b.nodes}
    for block in vstruct.blocks:
        stamped = tuple(f for f in vstruct.ff if f.merge_block == block.key)
        here = tuple(f for f in active if f.merge_block == block.key)
        drive = {n: volts.get(n, 0.0) for n in block.inputs}
        for f in here:
            if f.tap in volts:
                drive[f.tap] = volts[f.tap]
            else:
                reached = False
        found = block_local_gain(ss, block, drive, others=every - set(block.nodes), exclude=excluded,
                                 extra=tuple(m for f in stamped for m in f.members), ground=vstruct.ac_ground)
        volts.update(dict(found.node_v))
        results.append(found)
    return _sense_value(volts, *sense_nets), tuple(results), reached


def block_residual(ss, view, vstruct):
    system = view_system(ss, view)
    if system is None:
        return _bare(vstruct.id, "unsupported_view", (("mode", getattr(view, "mode", None)),))
    if not vstruct.blocks:
        return _bare(vstruct.id, "no_blocks")
    fixed, drive_idx, sense, pairs, sense_nets = system
    size = len(ss.nodes)
    factor = nodal_factor(conductance_matrix(ss.circuit, size), fixed, c=capacitance_matrix(ss.circuit, size))
    volt, residual = nodal_solve(factor, size, drive_idx)
    if volt is None:
        return _bare(vstruct.id, "singular_dc")
    full = float(sense @ volt)
    inject = {}
    index = {net: i for i, net in enumerate(ss.nodes)}
    inject[index[sense_nets[0]]] = 1.0
    if sense_nets[1] is not None:
        inject[index[sense_nets[1]]] = -1.0
    zvolt, _zres = nodal_solve(factor, size, None, inject)
    rout_full = None if zvolt is None else float(sense @ zvolt)
    excluded = tuple(sorted({m for f in vstruct.ff for m in f.members}))
    main_out, main_blocks, _reached = _cascade(ss, vstruct, pairs, sense_nets, (), excluded)
    all_out, all_reached = (main_out, True) if not vstruct.ff else _cascade(ss, vstruct, pairs, sense_nets, vstruct.ff, excluded)[::2]
    contrib = []
    for f in vstruct.ff:
        out_f, _b, reached = _cascade(ss, vstruct, pairs, sense_nets, (f,), excluded)
        delta = out_f - main_out
        if not reached or delta == 0:
            contrib.append(FfContribution(f.id, None, 0))
        else:
            contrib.append(FfContribution(f.id, _db(delta), 1 if delta * main_out >= 0 else -1))
    solve = max([residual] + [b.solve_residual for b in main_blocks if b.solve_residual is not None])
    last = next((b for b, s in zip(main_blocks, vstruct.blocks) if set(sense_nets[0:1]) <= set(s.outputs)), None)
    rout_residual = None if last is None or last.zout_ohm is None or rout_full is None else rout_full - last.zout_ohm
    read = tuple(sorted({m for b in main_blocks for m in b.members} | set(excluded)))
    full_db = _db(full)
    decomposed_db = _db(all_out) if all_reached else None
    if decomposed_db is None or full_db is None:
        return BlockResidual(vstruct.id, None, main_blocks, tuple(contrib), rout_residual, full_db, decomposed_db, solve, read,
                             (Undefined(QUANTITY, "decomposed_zero", "definitional"),))
    return BlockResidual(vstruct.id, full_db - decomposed_db, main_blocks, tuple(contrib), rout_residual, full_db, decomposed_db, solve, read)
