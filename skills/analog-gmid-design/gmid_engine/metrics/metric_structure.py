"""S1v -> metrics 구조 입력 (설계 41 §2, §1.12.2, 40 §3.8-8 -- `block_residual`·`offset_analysis`(offset_excess)·`ff_gm_ratio`·`nqs_ratio` 의 구조 사실).

진입점: `metric_structure`(`@compute_block`, writer `metric_structure`) -- `metric_structure(snapshot)`. reads `graph/s1v: views`, writes S0 수준 필드
`graph/s1v: metric_structure`(설계 40 §2.4.8 'metric 구조 입력', MOD5) -- 값 = `MetricStructure`, S1v 뷰 필드가 없는 스냅샷이면 None(구조 의존 값은 정의 불가 -- 미측정).

S1v 의 전달 뷰(`kind == transfer`)마다 `ViewStruct` 하나: 주경로 블록 사슬(stage 순 -- FF 묶음 소자는 S1v 가 이미 뺀 뒤 구성한 블록이다, 41 §1.12.2-3),
feedforward 묶음(`FfStruct` -- merge 노드를 출력으로 갖는 주경로 블록과 처음 우회한 블록 B_b), 첫 이득 블록(최소 stage)의 input 셀, 순방향 신호 셀 MOS.
이름 없는 구조 사실만 옮긴다(회로 이름·소자 이름 분기 없음). S0 당 1회 계산 블록으로 쓰고(S1v 가 같으면 재사용) 평가(`ss_evaluate` 호출자)는 필드를 읽는다.
"""
from gmid_engine.core import compute_block
from gmid_engine.graph import BLOCK_GAIN, CELL_OFF, ROLE_INPUT, S1V_KEY, VIEW_TRANSFER

from .aux_types import BlockStruct, FfStruct, MetricStructure, ViewStruct
from .s0_fields import METRIC_STRUCTURE_WRITER, METRIC_STRUCTURE_WRITES


def _block(b):
    return BlockStruct(b.key, b.kind, b.stage, b.inputs, b.outputs, b.nodes,
                       tuple(sorted(name for name, role in b.roles if role == ROLE_INPUT)), tuple(sorted(name for name, _role in b.roles)))


def _ff(f, blocks):
    merge_block = next((b.key for b in blocks if f.merge in b.outputs), ())
    first = f.bypassed_blocks[0] if f.bypassed_blocks else ()
    by_key = {b.key: b for b in blocks}
    inputs = by_key[first].input_cells if first in by_key else ()
    return FfStruct(f.id, f.tap, f.merge, tuple(sorted(f.cells + f.bias_cells + f.load_cells)), merge_block, first, inputs)


@compute_block(METRIC_STRUCTURE_WRITER, reads=(("graph", "views"),), writes=METRIC_STRUCTURE_WRITES)
def metric_structure(projection):
    found = dict(projection.column("graph", "views"))
    if S1V_KEY not in found:
        return {("graph", "metric_structure"): {S1V_KEY: None}}
    views = []
    for v in found[S1V_KEY]:
        if v.kind != VIEW_TRANSFER:
            continue
        blocks = tuple(sorted((_block(b) for b in v.blocks), key=lambda b: (b.stage, b.key)))
        gain = [b for b in blocks if b.kind == BLOCK_GAIN]
        first = min(gain, key=lambda b: (b.stage, b.key)) if gain else None
        views.append(ViewStruct(v.id, tuple(v.excite), tuple(v.sense), blocks, tuple(_ff(f, blocks) for f in v.feedforward),
                                first.input_cells if first else (),
                                tuple(sorted(c.dev for c in v.cells if c.forward and c.kind != CELL_OFF)),
                                tuple(sorted(p.net for p in v.pole_nodes)),
                                tuple((d.net, d.topology, tuple(d.charge), tuple(d.discharge)) for d in v.output_direction),
                                tuple(sorted(v.ac_ground))))
    return {("graph", "metric_structure"): {S1V_KEY: MetricStructure(tuple(views))}}
