"""S1v -> metrics 구조 입력 (설계 41 §2, §1.12.2, 40 §3.8-8 -- `block_residual`·`offset_analysis`(offset_excess)·`ff_gm_ratio`·`nqs_ratio` 의 구조 사실).

진입점: `metric_structure(s1v) -> MetricStructure`.

S1v 의 전달 뷰(`kind == transfer`)마다 `ViewStruct` 하나: 주경로 블록 사슬(stage 순 -- FF 묶음 소자는 S1v 가 이미 뺀 뒤 구성한 블록이다, 41 §1.12.2-3),
feedforward 묶음(`FfStruct` -- merge 노드를 출력으로 갖는 주경로 블록과 처음 우회한 블록 B_b), 첫 이득 블록(최소 stage)의 input 셀, 순방향 신호 셀 MOS.
이름 없는 구조 사실만 옮긴다(회로 이름·소자 이름 분기 없음). 부르는 쪽(`ss_evaluate` 호출자)이 S0 당 1회 만들어 넘긴다(S1v 가 같으면 같은 값 --
튜플 불변이라 블록 입력 버전에 지문으로 든다).
"""
from gmid_engine.graph import BLOCK_GAIN, CELL_OFF, ROLE_INPUT, VIEW_TRANSFER

from .aux_types import BlockStruct, FfStruct, MetricStructure, ViewStruct


def _block(b):
    return BlockStruct(b.key, b.kind, b.stage, b.inputs, b.outputs, b.nodes,
                       tuple(sorted(name for name, role in b.roles if role == ROLE_INPUT)))


def _ff(f, blocks):
    merge_block = next((b.key for b in blocks if f.merge in b.outputs), ())
    first = f.bypassed_blocks[0] if f.bypassed_blocks else ()
    by_key = {b.key: b for b in blocks}
    inputs = by_key[first].input_cells if first in by_key else ()
    return FfStruct(f.id, f.tap, f.merge, tuple(sorted(f.cells + f.bias_cells + f.load_cells)), merge_block, first, inputs)


def metric_structure(s1v):
    views = []
    for v in s1v.views:
        if v.kind != VIEW_TRANSFER:
            continue
        blocks = tuple(sorted((_block(b) for b in v.blocks), key=lambda b: (b.stage, b.key)))
        gain = [b for b in blocks if b.kind == BLOCK_GAIN]
        first = min(gain, key=lambda b: (b.stage, b.key)) if gain else None
        views.append(ViewStruct(v.id, tuple(v.excite), tuple(v.sense), blocks, tuple(_ff(f, blocks) for f in v.feedforward),
                                first.input_cells if first else (),
                                tuple(sorted(c.dev for c in v.cells if c.forward and c.kind != CELL_OFF)),
                                tuple(sorted(p.net for p in v.pole_nodes)),
                                tuple((d.net, d.topology, tuple(d.charge), tuple(d.discharge)) for d in v.output_direction)))
    return MetricStructure(tuple(views))
