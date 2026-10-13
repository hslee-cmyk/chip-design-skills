"""잡음 선언 -- spec feedback·샘플링 커패시터와 S1v 입력 셀 -> metrics `NoiseDecl` (설계 41 §7.1·7.3, 단위 U8).

진입점: `noise_decl`(`@compute_block`, writer `noise_decl`) -- `noise_decl(snapshot, feedback, sampling_caps)`. S0 수준 필드 `graph/s1v: noise_input_cells`
(값 = metrics `NoiseDecl` 전체, 설계 40 §2.4.8 v1.9.1 D7) -- S0 당 1회(`build_search_context` 가 부르고 평가는 필드를 읽는다). reads `graph/s1v: views`(없으면 입력 셀 없음),
extras: `feedback` = spec `feedback`(소자 이름 tuple 또는 결정 대기·거부면 None), `sampling_caps` = spec `noise_testbench.sampling_caps` 의 커패시터 이름 tuple.

* `feedback` = spec `feedback` 소자 이름 tuple(빈 tuple = 되먹임 없음). 결정 대기·거부(PendingMark·None)면 None -- 폐루프 모드를 정할 수 없다(`noise_feedback_undeclared`).
* `sampling_caps` = spec `noise_testbench.sampling_caps` 의 커패시터 이름(선언이 없으면 빈 tuple -- 스위치 kT/C 항 0, 이 항의 선언 여부는 사용자 결정 대기).
* `input_cells` = S1v 전달 뷰(`transfer:<순번>`)마다 (여기 넷, 감지 넷, 입력 셀 MOS 이름): **그 뷰의 첫 이득 블록**(이득 블록 중 stage 가 가장 작은 것, 같으면 블록 키 순)의
  AC 역할이 input 인 소자 -- 41 §7.1 `noise_excess_th` 의 '입력 소자'. 이득 블록이 없거나 input 소자가 없는 뷰는 싣지 않는다(그 뷰의 excess 는 정의 불가
  `noise_input_cell_undefined`). S1v 뷰 필드가 없으면 빈 tuple. 소비자(`metrics_ss`)는 요청 뷰의 여기·감지 넷이 같은 뷰를 찾는다 -- 이름이 아니라 구조로 정해진다.
"""
from gmid_engine.core import compute_block
from gmid_engine.graph import S1V_KEY
from gmid_engine.metrics import NoiseDecl

from .s0_fields import NOISE_DECL_WRITER, NOISE_DECL_WRITES

TRANSFER_VIEW = "transfer"      # graph s1v_values.VIEW_TRANSFER (graph `__all__` 밖이라 값을 그대로 둔다)
GAIN_BLOCKS = ("gain", "composite")   # graph s1v_values.BLOCK_GAIN·BLOCK_COMPOSITE -- 이득을 만드는 블록(버퍼 제외)
INPUT_ROLE = "input"            # graph s1v_values.ROLE_INPUT


def _input_cell(view):
    blocks = sorted((b for b in view.blocks if b.kind in GAIN_BLOCKS), key=lambda b: (b.stage, b.key))
    for block in blocks:
        devices = tuple(sorted(name for name, role in block.roles if role == INPUT_ROLE))
        if devices:
            return devices
    return ()


@compute_block(NOISE_DECL_WRITER, reads=(("graph", "views"),), writes=NOISE_DECL_WRITES)
def noise_decl(projection):
    feedback, caps = projection.extras
    cells = []
    for view in dict(projection.column("graph", "views")).get(S1V_KEY, ()):
        if view.kind != TRANSFER_VIEW:
            continue
        devices = _input_cell(view)
        if devices:
            cells.append((tuple(sorted(net for net, _w in view.excite)), tuple(sorted(view.sense)), devices))
    return {("graph", "noise_input_cells"): {S1V_KEY: NoiseDecl(feedback, caps, tuple(cells))}}
