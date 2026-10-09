"""이득 L 하한의 활성 판정 (설계 41 §6.4-1, H3; D-SIc).

진입점: `gain_l_status(ctx) -> ((경계 식, 사유), ...)`.

41 §6.4-1: 블록 목표 g_i = G·A_i,max / Σ A_max 를 만족하는 최소 L(블록 국소 모델 gain ≥ g_i, bin 오름차순 + bin 안 bisection). **A_max 가 미상이거나 gain 제약이 없으면 비활성**이다(H3).
이 단위는 비활성 판정과 그 사유 보고까지만 한다 -- U9 `achievability` 의 주경로 블록별 `BlockBound` 가 certified 일 때의 L 풀이(블록 국소 모델 `block_model`·`row_gains` 를
L 축으로 훑는 일)는 입력이 한 번도 certified 로 나오지 않은 상태라 연결하지 않았다(9회로 실측: 격자 곱 Π 가 N_S 를 넘어 거의 모든 블록이 미상, 인증된 블록은 L 에 무관한 버퍼 하나).
인증된 블록이 생기는 LUT·N_S 에서 이 판정이 `certified_block_local_model_not_wired` 를 내므로 조용히 통과하지 않는다. 비활성 사유는 보고 표 `inactive` 로 간다.
"""
from .start_values import SRC_GAIN_L, WHY_NO_CERT, WHY_NO_TARGET

_METRIC_GAIN = "gain_ss_db"
WHY_NOT_WIRED = "certified_block_local_model_not_wired"


def gain_l_status(ctx):
    if not any(m == _METRIC_GAIN and op == ">=" for m, op, _v in ctx.constraints):
        return ((SRC_GAIN_L, WHY_NO_TARGET),)
    gain = None if ctx.ach is None else ctx.ach.gain
    if gain is None or any(b.status != "certified" for b in gain.blocks):
        return ((SRC_GAIN_L, WHY_NO_CERT),)
    return ((SRC_GAIN_L, WHY_NOT_WIRED),)
