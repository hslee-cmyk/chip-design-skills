"""MOD7 floorplan -- 행 블록 패킹과 판정 축 외곽 면적 (design_mod7_layout.md 3절 6단계, 사용자 확정 12번 (나),
사용자 결정 2026-10-07 Q8 (vi)(vii)).

진입점: `floorplan_of(rows, bodies, pdk) -> FloorplanSummary`.

* 물리 행마다 블록 하나: 폭 = 행 폭 + 행 끝 dummy 둘(양끝, `pdk.dummy_w_m` 씩) + body tap 하나(`pdk.tap_w_m`),
  높이 = finger_w. 행 그룹을 `spine_groups` 로 묶는다(LR8). 길이는 제조 격자 칸 단위로 넘긴다(복사 본문의 탐색 해상도·
  비교 여유가 길이 단위와 무관하게 같은 뜻이 되도록).
* body 넷이 하나뿐이면 복사 함수 `pack_floorplan_grouped`(gap = PDK 행 간격) 한 번. body 넷이 여럿이면 body 마다
  `pack_floorplan_grouped`(gap = 행 간격)로 묶음을 만든 뒤, 묶음들을 복사 함수 `pack_floorplan`(gap = max(행 간격, well 간격))
  으로 배치한다 -- well 간격은 body 가 다른 묶음 사이에만 들어간다.
* 행 순서(`transistor_sequences`)는 행 결과를 재사용한다(Euler 재계산 없음). 대칭 블록 쌍(`mirror_pairs`)은 비운다.
* 외곽 면적 = bbox 폭 x 높이(판정 축 면적), 동률 해상도 = 격자 한 칸 면적. `included` = 면적에 넣은 PDK 항목과 규칙 번호.
"""
from .contract_output import (
    AREA_ITEM_FINGER_OVERHEAD,
    AREA_ITEM_ROW_END_DUMMY,
    AREA_ITEM_ROW_GAP,
    AREA_ITEM_TAP,
    AREA_ITEM_WELL_SPACING,
    FloorplanSummary,
)
from .floorplan_pack import FloorplanBlock, pack_floorplan, pack_floorplan_grouped

_BODY_BLOCK = "body:"


def _pack_body(rows, grid, pdk):
    """한 body 넷의 행들 -> (bbox 폭, bbox 높이, {행 id: (x, y, 폭, 높이)} 원점 = bbox 왼쪽 아래) 격자 칸 단위."""
    extra = 2 * pdk.dummy_w_m + pdk.tap_w_m
    spine_groups = {}
    for r in rows:
        spine_groups.setdefault(r.row_group, []).append(
            FloorplanBlock(r.row_id, (r.width_m + extra) / grid, r.finger_w_m / grid))
    sequences = {r.row_id: list(r.transistor_sequence) for r in rows}
    packed = pack_floorplan_grouped(spine_groups, [], gap=pdk.row_gap_m / grid, transistor_sequences=sequences)
    x0 = min(p.x for p in packed.placements.values())
    y0 = min(p.y for p in packed.placements.values())
    places = {name: (p.x - x0, p.y - y0, p.width, p.height) for name, p in packed.placements.items()}
    return packed.bbox_width, packed.bbox_height, places


def _included(pdk, well_applied):
    rule = dict(pdk.rule_ids)
    items = [
        (AREA_ITEM_FINGER_OVERHEAD, pdk.finger_pitch_overhead_m, rule["finger_pitch_overhead_m"]),
        (AREA_ITEM_ROW_END_DUMMY, pdk.dummy_w_m, rule["dummy_w_m"]),
        (AREA_ITEM_TAP, pdk.tap_w_m, rule["tap_w_m"]),
        (AREA_ITEM_ROW_GAP, pdk.row_gap_m, rule["row_gap_m"]),
    ]
    if well_applied:
        items.append((AREA_ITEM_WELL_SPACING, pdk.well_spacing_m, rule["well_spacing_m"]))
    return tuple(items)


def floorplan_of(rows, bodies, pdk):
    """`rows`(`RowLayout` 들, 비어 있지 않음), `bodies` = {행 그룹 id: body 넷}, `pdk`(`LayoutPdk`) -> `FloorplanSummary`(m)."""
    grid = pdk.manufacturing_grid_m
    by_body = {}
    for r in rows:
        by_body.setdefault(bodies[r.row_group], []).append(r)
    packs = {body: _pack_body(body_rows, grid, pdk) for body, body_rows in sorted(by_body.items())}
    if len(packs) == 1:
        width, height, places = next(iter(packs.values()))
    else:
        gap = max(pdk.row_gap_m, pdk.well_spacing_m) / grid
        blocks = [FloorplanBlock(_BODY_BLOCK + body, w, h) for body, (w, h, _) in packs.items()]
        top = pack_floorplan(blocks, [], gap=gap)
        x0 = min(p.x for p in top.placements.values())
        y0 = min(p.y for p in top.placements.values())
        width, height, places = top.bbox_width, top.bbox_height, {}
        for body, (_, _, inner) in packs.items():
            anchor = top.placements[_BODY_BLOCK + body]
            for name, (x, y, w, h) in inner.items():
                places[name] = (anchor.x - x0 + x, anchor.y - y0 + y, w, h)
    placements = tuple((name, x * grid, y * grid, w * grid, h * grid) for name, (x, y, w, h) in sorted(places.items()))
    block_area = sum(w * h for _, _, _, w, h in placements)
    width_m = width * grid
    height_m = height * grid
    area = width_m * height_m
    return FloorplanSummary(width_m, height_m, area, grid * grid, max(width_m, height_m) / min(width_m, height_m),
                            block_area / area, placements, _included(pdk, len(packs) > 1))
