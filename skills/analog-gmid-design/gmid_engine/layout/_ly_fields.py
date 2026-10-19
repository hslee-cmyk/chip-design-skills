"""MOD7 레이아웃 graph 필드 이름과 writer 권한표 (design_mod7_layout.md 4절, 계획 N3.4·DEC-83 '필드 = 캐시').

공개 정의(함수·클래스) 없음 -- 상수 표. 레이아웃 결과는 그 **설계점 스냅샷**(봉인 S2)의 S2 `layout` 필드로만 쓴다(설계 40 v1.6
§2.4.7·§2.4.8, 별도 lineage 없음): `run.run_layout` 이 설계점 권한표에 `LY_WRITERS` 를 더해 넓힌다(core `extend_writers`). 필드마다 writer 하나,
값과 함께 그 값을 만든 입력 버전이 기록된다(core `compute_block`). 같은 입력 버전이면 다시 계산하지 않는다.

입력 필드(writer `WRITER_INPUT`, `run.run_layout` 이 계약 `LayoutInput` 을 풀어 쓴다):
  device `F_DEVICE` (소자별 `LayoutDevice`), device `F_POINT`(소자별 보존량·동작점 `ConservedPoint` -- 참고 W 를 빼서 W 만 바뀌면 값이 같다,
  소비자 `ly_slice_density`), graph `F_PDK`·`F_GROUPS_IN`·`F_ROW_GROUPS`·`F_REJECTED`·`F_PASSIVES`(판정 축 면적의
  수동소자 블록 `LayoutPassive` tuple, U12).
계산 필드(writer = 계산 블록 이름):
  device `F_SLICES`(`run.py` 의 ly_slice_density -- reads device `F_POINT`·graph `F_PDK`(폭 키), 추가 인자 = LUT 지문, LUT memo 는 graph 밖 허용 저장소),
  device `F_FW_CAND`(finger_candidates), graph `F_GROUPS`·`F_DISPOSITIONS`(pattern_select), device `F_FINGER`(finger_geometry),
  graph `F_ROWS`·`F_FLOORPLAN`·`F_DIFFUSION`(rows -- 행 구성이 판정 축 면적을 목적으로 쓰므로 floorplan 을 같은 블록에서 내고,
  `ly.diffusion`(LY8)은 최종 행의 공유 확산 통계라 같은 블록에서 낸다).
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
F_PASSIVES = "ly_passives"
F_POINT = "ly_point"
F_SLICES = "ly_slices"
F_FW_CAND = "ly_fw_cand"
F_GROUPS = "ly_groups"
F_DISPOSITIONS = "ly_dispositions"
F_FINGER = "ly_finger"
F_ROWS = "ly_rows"
F_FLOORPLAN = "ly_floorplan"
F_DIFFUSION = "ly_diffusion"

WRITER_INPUT = "ly_input"
WRITER_SLICES = "ly_slice_density"
WRITER_FW_CAND = "ly_finger_candidates"
WRITER_GROUPS = "ly_pattern_select"
WRITER_FINGER = "ly_finger_geometry"
WRITER_ROWS = "ly_rows"

INPUT_FIELDS = (
    (DEVICE, F_DEVICE),
    (DEVICE, F_POINT),
    (GRAPH, F_PDK),
    (GRAPH, F_GROUPS_IN),
    (GRAPH, F_ROW_GROUPS),
    (GRAPH, F_REJECTED),
    (GRAPH, F_PASSIVES),
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
        (GRAPH, F_DIFFUSION, WRITER_ROWS),
    )
)

BLOCK_WRITERS = (WRITER_FW_CAND, WRITER_GROUPS, WRITER_FINGER, WRITER_ROWS)
