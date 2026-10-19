"""MOD7 레이아웃 공개 진입점 (design_mod7_layout.md 1절 `run.py`, 3절 7단계, 4절 graph 필드, 사용자 결정 2026-10-07 Q4·Q8,
설계 40 v1.6 §2.4.7 `LayoutResult` 행·§2.4.8 '레이아웃 결과' 행 -- 레이아웃 필드는 그 설계점 스냅샷의 S2 `layout` 필드, 별도 lineage 없음).

진입점: `run_layout(layout_input, memo, design_point, previous=None, *, donors, counters) -> LayoutResult`.
`donors`·`counters` = 필수 키워드(기본값 없음) -- 호출자(`place_layout` <- `converge_point` 의 `sctx.dc`)가 넘기는 실행 하나의 블록 결과 색인·계수. 네 계산 블록에 그대로 넘긴다.

1. 쓸 스냅샷 = `previous.snapshot`(같은 설계점 위 앞 호출 -- 레이아웃 재시도는 같은 설계점 lineage 의 새 스냅샷) 또는 설계점 스냅샷
   `design_point`(봉인 S2). 권한표는 설계점 권한표에 레이아웃 권한표(`LY_WRITERS`)를 더한 것으로 넓힌다(core `extend_writers` -- 레코드·
   block_version 공유). `previous` 가 다른 설계점 위의 것이면(설계점 writer 의 block_version 이 하나라도 다르면) `ValueError`.
2. 계약 `LayoutInput` 을 graph 입력 필드(writer `ly_input`)로 쓴다 -- 바뀌지 않은 입력 열만 읽는 블록은 다시 계산하지 않는다(필드 = 캐시,
   core `compute_block`).
3. 폭 슬라이스별 보존량 실현(`slice_density`, LUT 조회는 `memo` = MOD1 `LutMemo`)을 device `ly_slices`로 쓴다 -- 정식
   `@compute_block` `ly_slice_density`(writer 이름 그대로, reads device `ly_point` -- `ly_input` 이 쓰는 소자별 보존량·동작점 `ConservedPoint`,
   참고 W 는 `ly_device` 에만 있어 W 만 바뀌면 다시 조회하지 않는다. reads graph `ly_pdk` -- 폭 키는 그 필드가 정본. 추가 인자 `_LutHandle` = graph 밖 허용 입력(LUT memo)뿐).
   입력 버전 = (블록 코드, `ly_point`·`ly_pdk` 지문, LUT 지문) -- 같으면 재사용·이식, 다시 조회하지 않는다
   (LUT memo 는 허용 저장소). 같은 보존량·동작점의 소자는 한 번만 조회한다. `memo.lut.fp` 가 `pdk.source_fp` 와 다르면 `ValueError`.
4. 계산 블록을 차례로: `finger_candidates` -> `pattern_select` -> `finger_geometry` -> `compose_rows`(행 + floorplan + ly.diffusion).
5. 결과 = `LayoutResult(snapshot)` -- 레이아웃 값은 스냅샷의 `ly_*` 필드에서 읽는다(사본 없음). 이번 호출에서 어느 블록이 계산·이식·재사용됐는지는 `counters`(`RunCounters` 행)가 정본이다. 필드에서 파생하는
   review_needed·W_requests·coverage·불변식·재검증 요청은 `layout_outputs(snapshot)`.
"""
import dataclasses

from gmid_engine.core import GraphSnapshot, WriterTable, compute_block, fp_of

from ._ly_fields import (
    DEVICE,
    F_DEVICE,
    F_GROUPS_IN,
    F_PASSIVES,
    F_PDK,
    F_POINT,
    F_REJECTED,
    F_ROW_GROUPS,
    F_SLICES,
    GRAPH,
    GRAPH_KEY,
    LY_WRITERS,
    WRITER_INPUT,
    WRITER_SLICES,
)
from .contract_output import ConservedPoint, LayoutResult
from .finger_candidates import finger_candidates
from .finger_geometry import finger_geometry
from .pattern_select import pattern_select
from .rows import compose_rows
from .slice_density import slice_density

_BLOCKS = (finger_candidates, pattern_select, finger_geometry, compose_rows)
_LY_WRITER_NAMES = frozenset(writer for _field, writer in LY_WRITERS.entries)


def _input_columns(layout_input):
    return {
        (DEVICE, F_DEVICE): {d.name: d for d in layout_input.devices},
        (DEVICE, F_POINT): {d.name: ConservedPoint(d.kind, d.L_m, d.ID_A, d.gm_id, d.vds_V, d.vsb_V) for d in layout_input.devices},
        (GRAPH, F_PDK): {GRAPH_KEY: layout_input.pdk},
        (GRAPH, F_GROUPS_IN): {GRAPH_KEY: layout_input.matching_groups},
        (GRAPH, F_ROW_GROUPS): {GRAPH_KEY: layout_input.row_groups},
        (GRAPH, F_REJECTED): {GRAPH_KEY: tuple(sorted(layout_input.rejected_requests))},
        (GRAPH, F_PASSIVES): {GRAPH_KEY: tuple(sorted(layout_input.passives, key=lambda p: p.name))},
    }


@dataclasses.dataclass(frozen=True)
class _LutHandle:
    """`ly_slice_density` 의 추가 인자 -- graph 밖 허용 입력(LUT memo)뿐. 지문(`__canonical__`)은 LUT 내용 지문 -- memo 상태(캐시)는
    결과에 영향이 없어 들지 않는다. 소자 보존량 점은 `ly_point`, PDK 폭 키는 `ly_pdk` 가 정본이라 여기 없다."""

    memo: object

    def __canonical__(self):
        return self.memo.lut.fp


@compute_block(WRITER_SLICES, reads=((DEVICE, F_POINT), (GRAPH, F_PDK)), writes=((DEVICE, F_SLICES),))
def _slice_block(projection):
    """소자마다 `slice_density` tuple. 같은 보존량·동작점의 소자는 한 번만 조회한다."""
    (lut,) = projection.extras
    keys_of = dict(projection.value(GRAPH, GRAPH_KEY, F_PDK).slice_width_keys)
    by_point = {}
    out = {}
    for name, point in projection.column(DEVICE, F_POINT):
        if point not in by_point:
            by_point[point] = slice_density(lut.memo, point, keys_of[point.kind])
        out[name] = by_point[point]
    return {(DEVICE, F_SLICES): out}


def _base(design_point, previous):
    """레이아웃 필드를 쓸 스냅샷: 설계점 스냅샷(권한표에 레이아웃 권한표를 더함) 또는 같은 설계점 위 앞 호출의 스냅샷."""
    if not isinstance(design_point, GraphSnapshot):
        raise TypeError("run_layout: design_point 는 설계점(봉인 S2) GraphSnapshot 이어야 한다")
    if previous is None:
        entries = tuple((kind, field, writer) for (kind, field), writer in design_point.writers.entries + LY_WRITERS.entries)
        return design_point.extend_writers(WriterTable(entries))
    snapshot = previous.snapshot
    own = {w: v for w, v in design_point.block_versions.items() if w not in _LY_WRITER_NAMES}
    theirs = {w: v for w, v in snapshot.block_versions.items() if w not in _LY_WRITER_NAMES}
    if own != theirs:
        raise ValueError("run_layout: previous 는 같은 설계점 lineage 의 레이아웃 결과여야 한다(설계점 block_version 이 다르다)")
    return snapshot


def run_layout(layout_input, memo, design_point, previous=None, *, donors, counters):
    """레이아웃을 설계점 스냅샷의 `ly_*` 필드로 실행하고 `LayoutResult(snapshot)` 를 돌려준다."""
    if memo.lut.fp != layout_input.pdk.source_fp:
        raise ValueError("run_layout: LUT memo 지문이 pdk.source_fp 와 다르다(다른 LUT 로 만든 PDK 폭 키)")
    snapshot = _base(design_point, previous)
    snapshot = snapshot.write(WRITER_INPUT, fp_of(layout_input), _input_columns(layout_input))
    snapshot = _slice_block(snapshot, _LutHandle(memo), donors=donors, counters=counters)
    for block in _BLOCKS:
        snapshot = block(snapshot, donors=donors, counters=counters)
    return LayoutResult(snapshot)
