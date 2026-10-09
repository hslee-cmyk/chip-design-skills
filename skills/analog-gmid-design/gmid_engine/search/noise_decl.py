"""잡음 선언 -- spec feedback·샘플링 커패시터와 S1v 입력 셀 -> metrics `NoiseDecl` (설계 41 §7.1·7.3, 단위 U8).

진입점: `noise_decl(spec, s1v) -> NoiseDecl`(S0 당 1회, `build_search_context` 가 부른다).

* `feedback` = spec `feedback` 소자 이름 tuple(빈 tuple = 되먹임 없음). 결정 대기·거부(PendingMark·None)면 None -- 폐루프 모드를 정할 수 없다(`noise_feedback_undeclared`).
* `sampling_caps` = spec `noise_testbench.sampling_caps` 의 커패시터 이름(선언이 없으면 빈 tuple -- 스위치 kT/C 항 0, 이 항의 선언 여부는 사용자 결정 대기).
* `input_cells` = S1v 전달 뷰(`transfer:<순번>`)마다 (여기 넷, 감지 넷, 입력 셀 MOS 이름): **그 뷰의 첫 이득 블록**(이득 블록 중 stage 가 가장 작은 것, 같으면 블록 키 순)의
  AC 역할이 input 인 소자 -- 41 §7.1 `noise_excess_th` 의 '입력 소자'. 이득 블록이 없거나 input 소자가 없는 뷰는 싣지 않는다(그 뷰의 excess 는 정의 불가
  `noise_input_cell_undefined`). `s1v` 가 None 이면 빈 tuple. 소비자(`metrics_ss`)는 요청 뷰의 여기·감지 넷이 같은 뷰를 찾는다 -- 이름이 아니라 구조로 정해진다.
"""
from gmid_engine.metrics import NoiseDecl

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


def noise_decl(spec, s1v):
    feedback = tuple(spec.feedback) if isinstance(spec.feedback, tuple) else None
    testbench = spec.noise_testbench
    caps = () if testbench is None else tuple(c.element for c in testbench.sampling_caps)
    cells = []
    for view in () if s1v is None else s1v.views:
        if view.kind != TRANSFER_VIEW:
            continue
        devices = _input_cell(view)
        if devices:
            cells.append((tuple(sorted(net for net, _w in view.excite)), tuple(sorted(view.sense)), devices))
    return NoiseDecl(feedback, caps, tuple(cells))
