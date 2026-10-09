"""MOD7 floorplan -- 행 블록 패킹과 판정 축 외곽 면적 (design_mod7_layout.md 3절 6단계, 사용자 확정 12번 (나),
사용자 결정 2026-10-07 Q8 (vi)(vii)).

진입점: `floorplan_of(rows, bodies, pdk, passives=()) -> FloorplanSummary`.

* 물리 행마다 블록 하나: 폭 = 행 폭 + 행 끝 dummy 둘(양끝, `pdk.dummy_w_m` 씩), 높이 = finger_w. 행 그룹을 `spine_groups` 로
  묶는다(LR8). 길이는 제조 격자 칸 단위로 넘긴다(복사 본문의 탐색 해상도·비교 여유가 길이 단위와 무관하게 같은 뜻이 되도록).
* body tap(LY10, U12): 행마다가 아니라 **행 그룹 경계에만** 하나 -- 그룹을 복사 함수 `pack_group_as_unit` 으로 먼저 묶은 뒤 그 외곽
  오른쪽에 폭 `pdk.tap_w_m`, 높이 = 그룹 높이인 tap 띠(`tap:<행 그룹>` 배치)를 붙여 그룹 블록을 만든다.
* well 묶음 = (kind, body 넷) -- 같은 kind·같은 body 넷 행들은 한 well(또는 같은 기판) 안이다. 묶음 안은 그룹 블록들을 복사 함수
  `pack_floorplan`(gap = PDK 행 간격, `pack_floorplan_grouped` 와 같은 순서)으로 배치한다. 묶음이 여럿이거나 수동소자 블록이 있으면 묶음마다
  만든 뒤 묶음들과 수동소자 블록을 `pack_floorplan`(gap = max(행 간격, well 간격))으로 배치한다 -- well 간격은 well 이 다른 묶음 사이
  (nmos 행 대 pmos 행, 또는 body 넷이 다른 행)에만 들어가고 같은 well 행 사이에는 들어가지 않는다(사용자 ratify 2026-10-08).
* 수동소자 블록(D-LY4, 사용자 결정 11·Q9): `passives`(`LayoutPassive`)마다 면적 A(= 탐색 축과 같은 정본 식)를 격자 칸 단위 직사각형으로
  둔다 -- 폭 = ceil(sqrt(A)/g) 칸, 높이 = ceil(A/(g² 폭)) 칸(면적 이상 가장 정사각형에 가까운 격자 블록, 모양에 대한 PDK 선언이 없어 새 수치를
  만들지 않는다). MIM 배치 여유 = 블록 사이 배치 간격(max(행 간격, well 간격)). 외곽 bbox 에 포함된다.
* 행 순서(`transistor_sequences`)는 행 결과를 재사용한다(Euler 재계산 없음). 대칭 블록 쌍(`mirror_pairs`)은 비운다.
* 외곽 면적 = bbox 폭 x 높이(판정 축 면적). 동률 폭 ΔA_tie 는 두 점이 정하므로 `area_tie.area_tie_m2(a, b)` 가 낸다(이 요약은 `grid_m` 만 싣는다).
  `included` = 면적에 넣은 PDK 항목과 규칙 번호.
"""
import math

from .contract_output import (
    AREA_ITEM_FINGER_OVERHEAD,
    AREA_ITEM_PASSIVES,
    AREA_ITEM_ROW_END_DUMMY,
    AREA_ITEM_ROW_GAP,
    AREA_ITEM_TAP,
    AREA_ITEM_WELL_SPACING,
    FloorplanSummary,
)
from .floorplan_pack import FloorplanBlock, pack_floorplan, pack_group_as_unit

_BODY_BLOCK = "body:"
_WELL_SEP = ":"
_TAP_BLOCK = "tap:"
_PASSIVE_BLOCK = "passive:"
_PASSIVE_RULE = "PassiveArea.area_m2 (PDK mim_cap_density_f_per_m2 / poly_res_*)"


def _pack_body(rows, grid, pdk):
    """한 body 넷의 행들 -> (bbox 폭, bbox 높이, {블록 이름(행 id·`tap:<행 그룹>`): (x, y, 폭, 높이)} 원점 = bbox 왼쪽 아래) 격자 칸 단위."""
    extra = 2 * pdk.dummy_w_m
    tap = pdk.tap_w_m / grid
    gap = pdk.row_gap_m / grid
    spine_groups = {}
    for r in rows:
        spine_groups.setdefault(r.row_group, []).append(
            FloorplanBlock(r.row_id, (r.width_m + extra) / grid, r.finger_w_m / grid))
    group_blocks, inner = [], {}
    for gname, blocks in spine_groups.items():
        unit, places = pack_group_as_unit(gname, blocks, gap=gap)
        group_blocks.append(FloorplanBlock(gname, unit.width + tap, unit.height))
        inner[gname] = (unit.width, unit.height, places)
    sequences = {r.row_id: list(r.transistor_sequence) for r in rows}
    packed = pack_floorplan(group_blocks, [], gap=gap, transistor_sequences=sequences)
    x0 = min(p.x for p in packed.placements.values())
    y0 = min(p.y for p in packed.placements.values())
    places = {}
    for gname, p in packed.placements.items():
        width, height, blocks = inner[gname]
        for name, bp in blocks.items():
            places[name] = (p.x - x0 + bp.x, p.y - y0 + bp.y, bp.width, bp.height)
        if tap > 0:
            places[_TAP_BLOCK + gname] = (p.x - x0 + width, p.y - y0, tap, height)
    return packed.bbox_width, packed.bbox_height, places


def _passive_block(passive, grid):
    """수동소자 하나 -> 격자 칸 단위 블록(면적 >= passive.area_m2, 정사각형에 가까운 정수 칸)."""
    cells = passive.area_m2 / (grid * grid)
    width = max(1, math.ceil(math.sqrt(cells)))
    return FloorplanBlock(_PASSIVE_BLOCK + passive.name, float(width), float(math.ceil(cells / width)))


def _included(pdk, well_applied, passive_area_m2):
    rule = dict(pdk.rule_ids)
    items = [
        (AREA_ITEM_FINGER_OVERHEAD, pdk.finger_pitch_overhead_m, rule["finger_pitch_overhead_m"]),
        (AREA_ITEM_ROW_END_DUMMY, pdk.dummy_w_m, rule["dummy_w_m"]),
        (AREA_ITEM_TAP, pdk.tap_w_m, rule["tap_w_m"]),
        (AREA_ITEM_ROW_GAP, pdk.row_gap_m, rule["row_gap_m"]),
    ]
    if well_applied:
        items.append((AREA_ITEM_WELL_SPACING, pdk.well_spacing_m, rule["well_spacing_m"]))
    if passive_area_m2:
        items.append((AREA_ITEM_PASSIVES, passive_area_m2, _PASSIVE_RULE))
    return tuple(items)


def floorplan_of(rows, bodies, pdk, passives=()):
    """`rows`(`RowLayout` 들, 비어 있지 않음), `bodies` = {행 그룹 id: body 넷}, `pdk`(`LayoutPdk`), `passives`(`LayoutPassive` 들,
    이름순 아니어도 됨) -> `FloorplanSummary`(m)."""
    grid = pdk.manufacturing_grid_m
    by_body = {}
    for r in rows:
        by_body.setdefault((r.kind, bodies[r.row_group]), []).append(r)
    packs = {well: _pack_body(well_rows, grid, pdk) for well, well_rows in sorted(by_body.items())}
    passive_blocks = [_passive_block(p, grid) for p in sorted(passives, key=lambda p: p.name)]
    if len(packs) == 1 and not passive_blocks:
        width, height, places = next(iter(packs.values()))
    else:
        gap = max(pdk.row_gap_m, pdk.well_spacing_m) / grid
        blocks = [FloorplanBlock(_BODY_BLOCK + kind + _WELL_SEP + body, w, h) for (kind, body), (w, h, _) in packs.items()]
        top = pack_floorplan(blocks + passive_blocks, [], gap=gap)
        x0 = min(p.x for p in top.placements.values())
        y0 = min(p.y for p in top.placements.values())
        width, height, places = top.bbox_width, top.bbox_height, {}
        for (kind, body), (_, _, inner) in packs.items():
            anchor = top.placements[_BODY_BLOCK + kind + _WELL_SEP + body]
            for name, (x, y, w, h) in inner.items():
                places[name] = (anchor.x - x0 + x, anchor.y - y0 + y, w, h)
        for b in passive_blocks:
            p = top.placements[b.name]
            places[b.name] = (p.x - x0, p.y - y0, b.width, b.height)
    placements = tuple((name, x * grid, y * grid, w * grid, h * grid) for name, (x, y, w, h) in sorted(places.items()))
    block_area = sum(w * h for _, _, _, w, h in placements)
    width_m = width * grid
    height_m = height * grid
    area = width_m * height_m
    passive_area = sum(b.width * b.height for b in passive_blocks) * grid * grid
    return FloorplanSummary(width_m, height_m, area, grid, max(width_m, height_m) / min(width_m, height_m),
                            block_area / area, placements, _included(pdk, len(packs) > 1, passive_area), passive_area)
