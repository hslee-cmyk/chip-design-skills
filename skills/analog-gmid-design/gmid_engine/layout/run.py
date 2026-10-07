"""MOD7 레이아웃 공개 진입점 (design_mod7_layout.md 1절 `run.py`, 3절 7단계, 4절 graph 필드).

진입점: `run_layout(layout_input, previous=None) -> LayoutResult`.

1. 계약 `LayoutInput` 을 graph 입력 필드(writer `ly_input`)로 쓴다. `previous`(앞 호출의 `LayoutResult`)를 주면 그 스냅샷
   위에 쓴다 -- 바뀌지 않은 입력 열만 읽는 블록은 다시 계산하지 않는다(필드 = 캐시, core `compute_block`).
2. 계산 블록을 차례로: `finger_candidates` -> `pattern_select` -> `finger_geometry` -> `compose_rows` -> `floorplan`.
3. coverage(`check_stick_diagram_coverage`: 입력 소자 이름 집합 = 행 소자 이름 집합), W_requests 모음, 불변식
   (상한을 넘는 소자는 모두 W_request 가 있고, 행별 finger 합 = 소자 finger 수 -- 행 접기·crossover 전후 총 W 불변).
"""
from gmid_engine.core import GraphSnapshot, fp_of

from ._ly_fields import (
    DEVICE,
    F_BOX_RATIO,
    F_DEVICE,
    F_FINGER,
    F_FLOORPLAN,
    F_GROUPS,
    F_GROUPS_IN,
    F_PDK,
    F_REJECTED,
    F_ROW_GROUPS,
    F_ROWS,
    GRAPH,
    GRAPH_KEY,
    LY_WRITERS,
    WRITER_INPUT,
)
from .contract_output import DeviceLayout, LayoutResult
from .coverage import check_stick_diagram_coverage
from .finger_candidates import finger_candidates
from .finger_geometry import finger_geometry
from .floorplan import floorplan
from .pattern_select import pattern_select
from .rows import compose_rows

_BLOCKS = (finger_candidates, pattern_select, finger_geometry, compose_rows, floorplan)


def _input_columns(layout_input):
    return {
        (DEVICE, F_DEVICE): {d.name: d for d in layout_input.devices},
        (GRAPH, F_PDK): {GRAPH_KEY: layout_input.pdk},
        (GRAPH, F_GROUPS_IN): {GRAPH_KEY: layout_input.matching_groups},
        (GRAPH, F_ROW_GROUPS): {GRAPH_KEY: layout_input.row_groups},
        (GRAPH, F_BOX_RATIO): {GRAPH_KEY: layout_input.box_max_row_ratio},
        (GRAPH, F_REJECTED): {GRAPH_KEY: tuple(sorted(layout_input.rejected_requests))},
    }


def run_layout(layout_input, previous=None):
    """레이아웃 7단계를 graph 필드로 실행하고 `LayoutResult` 를 돌려준다(`snapshot` = 다음 호출의 캐시)."""
    snapshot = GraphSnapshot.empty(LY_WRITERS) if previous is None else previous.snapshot
    snapshot = snapshot.write(WRITER_INPUT, fp_of(layout_input), _input_columns(layout_input))
    computed = []
    for block in _BLOCKS:
        before = snapshot.block_version(block.name)
        snapshot = block(snapshot)
        if snapshot.block_version(block.name) != before:
            computed.append(block.name)

    fingers = dict(snapshot.column(DEVICE, F_FINGER))
    groups = snapshot.value(GRAPH, GRAPH_KEY, F_GROUPS)
    rows_layout = snapshot.value(GRAPH, GRAPH_KEY, F_ROWS)
    per_device = {}
    for row in rows_layout.rows:
        for name, n_fingers in row.devices:
            per_device.setdefault(name, []).append((row.row_id, n_fingers))

    requests = [r for g in groups for r in g.w_requests]
    requests += [f.w_request for _, f in sorted(fingers.items()) if f.w_request is not None]
    requests = tuple(sorted(requests, key=lambda r: (r.device, r.reason)))
    requested = {r.device for r in requests}

    devices = []
    invariant = True
    for d in layout_input.devices:
        f = fingers[d.name]
        placed = tuple(per_device.get(d.name, ()))
        invariant = invariant and sum(n for _, n in placed) == f.n_fingers
        invariant = invariant and (f.err_rel <= f.upper or d.name in requested)
        devices.append(DeviceLayout(d.name, f.finger_w_m, f.n_fingers, placed, d.W_m, f.W_realized_m, f.err_rel,
                                    f.lower, f.upper, f.origin))
    coverage = check_stick_diagram_coverage([d.name for d in layout_input.devices],
                                            {r.row_id: [n for n, _ in r.devices] for r in rows_layout.rows})
    return LayoutResult(tuple(devices), groups, rows_layout.rows, rows_layout.box,
                        snapshot.value(GRAPH, GRAPH_KEY, F_FLOORPLAN), coverage.ok, tuple(sorted(coverage.missing)),
                        requests, invariant, tuple(computed), snapshot)
