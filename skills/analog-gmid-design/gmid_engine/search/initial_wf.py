"""외층·층 0 첫 평가 입력 w_f 칸 (FS-1, 계획 DEC-108 (3), 설계 40 §3.7-B 2·3, interface card §3.4).

진입점: `initial_wf(snapshot) -> WfInput | None` -- 스냅샷 필드 `graph/start: wf_start` 값 객체를 `cells_ref` 로, 칸 `w_key` 를 `keys` 로 읽는다(READS 만, 저장 0).
칸 `w_key` 가 None 인 칸(출발 불능)이 하나라도 있으면 None -- 호출자가 '출발 불능' 으로 실행을 멈춘다. 필드가 없으면 None 으로 넘기지 않고 스냅샷 조회 오류(`KeyError`)를 그대로 낸다(fail-closed).
"""
from gmid_engine.sizing import WfInput

from .s0_fields import START_KEY


def initial_wf(snapshot):
    cells = snapshot.value("graph", START_KEY, "wf_start")
    if any(cell.w_key is None for cell in cells):
        return None
    return WfInput(cells, tuple(cell.w_key for cell in cells))
