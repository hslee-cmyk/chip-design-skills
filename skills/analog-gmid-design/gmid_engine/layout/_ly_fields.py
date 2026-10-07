"""MOD7 레이아웃 graph 필드 이름과 writer 권한표 (design_mod7_layout.md 4절, 계획 N3.4·DEC-83 '필드 = 캐시').

공개 정의(함수·클래스) 없음 -- 상수 표. 레이아웃 결과는 core `GraphSnapshot` 의 필드로만 쓰고, 필드마다 writer 하나
(`LY_WRITERS`), 값과 함께 그 값을 만든 입력 버전이 기록된다(core `compute_block`). 같은 입력 버전이면 다시 계산하지 않는다.

입력 필드(writer `WRITER_INPUT`, `run.run_layout` 이 계약 `LayoutInput` 을 풀어 쓴다):
  device `F_DEVICE` (소자별 `LayoutDevice`), graph `F_PDK`·`F_GROUPS_IN`·`F_ROW_GROUPS`·`F_REJECTED`.
LUT 슬라이스 필드(writer `WRITER_SLICES`, `run.run_layout` 이 `slice_density` 로 채운다 -- LUT memo 는 가변이라 계산 블록
  인자가 될 수 없어 블록 밖에서 쓰고, 입력 버전 = (LUT 지문, 소자 보존량·동작점, 폭 키)):
  device `F_SLICES`.
계산 필드(writer = 계산 블록 이름):
  device `F_FW_CAND`(finger_candidates), graph `F_GROUPS`·`F_DISPOSITIONS`(pattern_select), device `F_FINGER`(finger_geometry),
  graph `F_ROWS`·`F_FLOORPLAN`(rows -- 행 구성이 판정 축 면적을 목적으로 쓰므로 floorplan 을 같은 블록에서 낸다).
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
F_REJECTED = "ly_rejected"
F_SLICES = "ly_slices"
F_FW_CAND = "ly_fw_cand"
F_GROUPS = "ly_groups"
F_DISPOSITIONS = "ly_dispositions"
F_FINGER = "ly_finger"
F_ROWS = "ly_rows"
F_FLOORPLAN = "ly_floorplan"

WRITER_INPUT = "ly_input"
WRITER_SLICES = "ly_slice_density"
WRITER_FW_CAND = "ly_finger_candidates"
WRITER_GROUPS = "ly_pattern_select"
WRITER_FINGER = "ly_finger_geometry"
WRITER_ROWS = "ly_rows"

INPUT_FIELDS = (
    (DEVICE, F_DEVICE),
    (GRAPH, F_PDK),
    (GRAPH, F_GROUPS_IN),
    (GRAPH, F_ROW_GROUPS),
    (GRAPH, F_REJECTED),
)

LY_WRITERS = WriterTable(
    tuple((kind, field, WRITER_INPUT) for kind, field in INPUT_FIELDS)
    + (
        (DEVICE, F_SLICES, WRITER_SLICES),
        (DEVICE, F_FW_CAND, WRITER_FW_CAND),
        (GRAPH, F_GROUPS, WRITER_GROUPS),
        (GRAPH, F_DISPOSITIONS, WRITER_GROUPS),
        (DEVICE, F_FINGER, WRITER_FINGER),
        (GRAPH, F_ROWS, WRITER_ROWS),
        (GRAPH, F_FLOORPLAN, WRITER_ROWS),
    )
)

BLOCK_WRITERS = (WRITER_FW_CAND, WRITER_GROUPS, WRITER_FINGER, WRITER_ROWS)
