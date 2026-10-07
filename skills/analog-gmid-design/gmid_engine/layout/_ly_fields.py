"""MOD7 레이아웃 graph 필드 이름과 writer 권한표 (design_mod7_layout.md 4절, 계획 N3.4·DEC-83 '필드 = 캐시').

공개 정의(함수·클래스) 없음 -- 상수 표. 레이아웃 결과는 core `GraphSnapshot` 의 필드로만 쓰고, 필드마다 writer 하나
(`LY_WRITERS`), 값과 함께 그 값을 만든 입력 버전이 기록된다(core `compute_block`). 같은 입력 버전이면 다시 계산하지 않는다.

입력 필드(writer `WRITER_INPUT`, `run.run_layout` 이 계약 `LayoutInput` 을 풀어 쓴다):
  device `F_DEVICE` (소자별 `LayoutDevice`), graph `F_PDK`·`F_GROUPS_IN`·`F_ROW_GROUPS`·`F_BOX_RATIO`·`F_REJECTED`.
계산 필드(writer = 계산 블록 이름):
  device `F_FW_CAND`(finger_candidates), graph `F_GROUPS`(pattern_select), device `F_FINGER`(finger_geometry),
  graph `F_ROWS`(rows), graph `F_FLOORPLAN`(floorplan).
graph kind 필드의 key 는 `GRAPH_KEY` 하나다.
"""
from gmid_engine.core import WriterTable

DEVICE = "device"
GRAPH = "graph"
GRAPH_KEY = "layout"

F_DEVICE = "ly_device"
F_PDK = "ly_pdk"
F_GROUPS_IN = "ly_groups_in"
F_ROW_GROUPS = "ly_row_groups"
F_BOX_RATIO = "ly_box_ratio"
F_REJECTED = "ly_rejected"
F_FW_CAND = "ly_fw_cand"
F_GROUPS = "ly_groups"
F_FINGER = "ly_finger"
F_ROWS = "ly_rows"
F_FLOORPLAN = "ly_floorplan"

WRITER_INPUT = "ly_input"
WRITER_FW_CAND = "ly_finger_candidates"
WRITER_GROUPS = "ly_pattern_select"
WRITER_FINGER = "ly_finger_geometry"
WRITER_ROWS = "ly_rows"
WRITER_FLOORPLAN = "ly_floorplan"

INPUT_FIELDS = (
    (DEVICE, F_DEVICE),
    (GRAPH, F_PDK),
    (GRAPH, F_GROUPS_IN),
    (GRAPH, F_ROW_GROUPS),
    (GRAPH, F_BOX_RATIO),
    (GRAPH, F_REJECTED),
)

LY_WRITERS = WriterTable(
    tuple((kind, field, WRITER_INPUT) for kind, field in INPUT_FIELDS)
    + (
        (DEVICE, F_FW_CAND, WRITER_FW_CAND),
        (GRAPH, F_GROUPS, WRITER_GROUPS),
        (DEVICE, F_FINGER, WRITER_FINGER),
        (GRAPH, F_ROWS, WRITER_ROWS),
        (GRAPH, F_FLOORPLAN, WRITER_FLOORPLAN),
    )
)

BLOCK_WRITERS = (WRITER_FW_CAND, WRITER_GROUPS, WRITER_FINGER, WRITER_ROWS, WRITER_FLOORPLAN)
