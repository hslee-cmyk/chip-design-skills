"""감도 게이트 -- 분해 값이 읽지 않는 소자를 건드렸는데 MNA 값만 움직이는 오류 검출 (설계 40 §3.8-2, 체크리스트 D-SG).

진입점: `sensitivity_gate(base, runs) -> GateResult`.

as-built `sensitivity.py`(LUT 파라미터 adjoint 로 metric 분해능을 내는 것)와는 다른 양이다. 게이트는 블록 분해 합성값이 **읽지 않는 소자**(어느 블록 국소 모델에도 스탬프되지 않은 소자 --
`BlockGain.members` 밖)의 θ 성분을 섭동해, 분해 값 변화 ≤ ε 인데 MNA 전회로 값 변화 > ε 이면 오류(분해가 놓친 결합)로 본다. S0 지문이 바뀔 때와 최종 해에서 돈다
(섭동 점 평가는 호출자 몫 -- metrics 는 평가 커널을 모른다).

* `base` = (분해 이득 dB, 전회로 이득 dB, 풀이 상대 잔차) -- 기준 점의 `BlockResidual`(`decomposed_gain_db`·`full_gain_db`·`solve_residual`).
* `runs` = ((섭동 이름, 분해 이득 dB, 전회로 이득 dB, 풀이 상대 잔차), ...) -- 섭동 점마다.
* ε = 풀이 상대 잔차(‖A·x − b‖₂/‖b‖₂, `nodal_solve` 의 사후 잔차 -- 기준과 섭동 점 중 큰 쪽) × 그 metric 의 x 감도. 이득 dB = 20·log10|x| 의 x 상대 변화에 대한 감도 =
  20/ln 10 (dB / 상대 변화, 단위 환산 계수 `AMPLITUDE_DB_PER_DECADE`/ln 10 -- 새 상수 없음). 잔차가 0 이면 부동소수 해상도를 바닥으로 쓴다.
* 값이 하나라도 정의 안 되면(None) 그 섭동은 검사하지 못한 것(`checks` 에 error None)으로 남기고 오류로 세지 않는다.
"""
import math
import sys

from gmid_engine.core import AMPLITUDE_DB_PER_DECADE

from .aux_types import GateResult


def sensitivity_gate(base, runs):
    dec0, full0, res0 = base
    sensitivity = AMPLITUDE_DB_PER_DECADE * math.log10(math.e)         # 20/ln 10 (dB per 상대 변화)
    checks = []
    errors = []
    widest = None
    for label, dec, full, res in runs:
        if None in (dec, full, dec0, full0, res, res0):
            checks.append((label, None, None, None, None))
            continue
        eps = max(res0, res, sys.float_info.epsilon) * sensitivity
        d_dec, d_full = abs(dec - dec0), abs(full - full0)
        bad = d_dec <= eps and d_full > eps
        checks.append((label, d_dec, d_full, eps, bad))
        if bad:
            errors.append(label)
        widest = eps if widest is None else max(widest, eps)
    return GateResult(not errors, tuple(checks), tuple(errors), widest)
