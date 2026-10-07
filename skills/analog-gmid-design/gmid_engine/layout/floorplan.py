"""MOD7 floorplan 계산 블록 -- 행 블록 패킹과 외곽 면적 (design_mod7_layout.md 3절 6단계, 사용자 확정 12번 (나)).

진입점: `floorplan` -- core `@compute_block`(writer `ly_floorplan`, reads graph `ly_rows`·`ly_pdk`, writes graph `ly_floorplan`).

물리 행마다 블록 하나(폭 = 행 폭, 높이 = finger_w)를 만들고 행 그룹((kind, body 넷), LR8)을 `spine_groups` 로 묶어
복사 함수 `pack_floorplan_grouped` 를 부른다. 길이는 제조 격자 칸 단위로 넘긴다(복사 본문의 탐색 해상도·비교 여유가
길이 단위와 무관하게 같은 뜻이 되도록) -- gap = PDK 행 간격 / 격자. 행 순서(`transistor_sequences`)는 행 블록 결과를
재사용한다(Euler 재계산 없음). 대칭 블록 쌍(`mirror_pairs`)은 비운다: matching 그룹은 패턴 행 안에서 이미 한 블록이다.
외곽 면적 = bbox 폭 x 높이(판정 축 면적), 동률 해상도 = 격자 한 칸 면적.
"""
from gmid_engine.core import compute_block

from ._ly_fields import F_FLOORPLAN, F_PDK, F_ROWS, GRAPH, GRAPH_KEY, WRITER_FLOORPLAN
from .contract_output import FloorplanSummary
from .floorplan_pack import FloorplanBlock, pack_floorplan_grouped


@compute_block(WRITER_FLOORPLAN, reads=((GRAPH, F_ROWS), (GRAPH, F_PDK)), writes=((GRAPH, F_FLOORPLAN),))
def floorplan(projection):
    """`FloorplanSummary`(m 단위)."""
    rows = projection.value(GRAPH, GRAPH_KEY, F_ROWS).rows
    grid = projection.value(GRAPH, GRAPH_KEY, F_PDK).manufacturing_grid_m
    gap = projection.value(GRAPH, GRAPH_KEY, F_PDK).row_gap_m / grid
    spine_groups = {}
    for r in rows:
        spine_groups.setdefault(r.row_group, []).append(FloorplanBlock(r.row_id, r.width_m / grid, r.finger_w_m / grid))
    sequences = {r.row_id: list(r.transistor_sequence) for r in rows}
    packed = pack_floorplan_grouped(spine_groups, [], gap=gap, transistor_sequences=sequences)
    placements = tuple(
        (name, p.x * grid, p.y * grid, p.width * grid, p.height * grid)
        for name, p in sorted(packed.placements.items())
    )
    width = packed.bbox_width * grid
    height = packed.bbox_height * grid
    summary = FloorplanSummary(width, height, width * height, grid * grid, packed.aspect_ratio, packed.packing_density,
                               placements)
    return {(GRAPH, F_FLOORPLAN): {GRAPH_KEY: summary}}
