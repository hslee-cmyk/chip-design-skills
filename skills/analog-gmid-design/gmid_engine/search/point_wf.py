"""평가된 점의 w_f 칸 입력 (FS-1, 계획 DEC-108 (4)·LR10 (W-a), 설계 40 §3.7-B 2·7, interface card §5).

진입점: `point_wf(snapshot) -> WfInput` -- 한 평가 스냅샷이 쓴 평가 입력 w_f 칸을 그 스냅샷 필드에서 읽는다: 칸 구조 = `graph/start: wf_start` 값 객체(참조), 칸 키 = 칸 첫 멤버의 `DeviceOp.w_key`
(DC 블록이 그 평가 입력 칸 키를 참조 키로 쓴 것 -- 값 사본이 아니라 필드 읽기). 평가 결과 객체에 `WfInput` 사본 칸을 두지 않는다: 시작점에서 이어 평가하는 자리(이웃 시험·ε 점 warm start·실현 평가·레이아웃 뒤 평가)가
점의 입력 칸을 이 함수로 읽는다. 스냅샷에 필드나 소자 행이 없으면 조회 오류를 그대로 낸다(fail-closed).
"""
from gmid_engine.sizing import WfInput

from .s0_fields import START_KEY


def point_wf(snapshot):
    cells = snapshot.value("graph", START_KEY, "wf_start")
    ops = dict(snapshot.column("device", "dc_op"))
    return WfInput(cells, tuple(ops[cell.members[0]].w_key for cell in cells))
