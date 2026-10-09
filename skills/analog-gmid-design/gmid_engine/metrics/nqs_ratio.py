"""준정적(NQS) 위반 위험 지표 `nqs_ratio` = ugf_ss_hz / 신호 경로 소자 최소 f_T (설계 40 §3.8-4, 체크리스트 D-GB8b).

진입점: `nqs_ratio(devices, ugf_hz) -> NqsRatio`.

* 소자 f_T = gm / (2π·cgg), gm·cgg 는 봉인 `ss_dev`(소신호 선형화) 값 -- `devices` = ((라벨, gm, cgg), ...) 신호 경로 소자(S1v 뷰의 순방향 신호 셀 MOS).
  cgg ≤ 0 인 소자는 f_T 를 정의하지 않아 건너뛰고 사유를 `undefined` 에 남기지 않는다(아래 모두 건너뛰면 `ft_undefined`).
* 값 = ugf / 최소 f_T. 1 에 가까울수록 UGF 가 소자 한계에 닿아 준정적 모형이 틀린다 -- 보고 전용(제약 어휘 밖). UGF 가 없으면(`ugf_ss_hz` 요청이 없어 계산되지 않았거나 교차 없음)
  `ugf_unavailable`.
"""
import math

from .aux_types import NqsRatio
from .mna_types import Undefined

QUANTITY = "ratio"


def nqs_ratio(devices, ugf_hz):
    if ugf_hz is None:
        return NqsRatio(None, undefined=(Undefined(QUANTITY, "ugf_unavailable", "definitional"),))
    fts = [(gm / (2 * math.pi * cgg), label) for label, gm, cgg in devices if cgg > 0 and gm > 0]
    if not fts:
        return NqsRatio(None, undefined=(Undefined(QUANTITY, "ft_undefined", "definitional"),))
    low, label = min(fts)
    return NqsRatio(ugf_hz / low, low, label)
