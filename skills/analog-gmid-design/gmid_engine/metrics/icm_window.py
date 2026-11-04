"""ICMR 세 metric -- `graph.icm_config` V_cm 칸에서 (계획 N3.8 '창 필드', 설계 41 §4.7-5, 사용자 결정 O-109 C1·O-111~O-113·O-215(임시), 카드 IT-2d).

진입점: `icm_window_metrics(config, ports, input_dc) -> IcmWindow` (순수 함수).

입력 = `IcmConfig`(`graph.icm_config`)의 V_cm 칸 `vcm0`·`vcm_lo`·`vcm_hi`. 입력 포트 창 `lo`·`hi`(`IcmPort`)는 보고 열 전용이라 산술에 쓰지 않는다.
* `icm_margin_v` = min(vcm0 − vcm_lo, vcm_hi − vcm0), `icmr_v` = vcm_hi − vcm_lo, `window` = (vcm_lo, vcm_hi), `v_icm` = vcm0.
* `required_input_cm_v` = `input_dc == "pending"` 이면 (vcm0, vcm_lo, vcm_hi), `"declared"` 이면 None.
* 분해능: `margin_resolution` = 첫 포트 `tol_v`, `icmr_resolution` = 2·`tol_v`(두 끝), `tol_v` None 이면 None.
* 정의 불능(세 양 값 None, 양마다 `Undefined` 하나): 구성 None 이면 `IcmConfig.undefined` 의 code·category·detail 을 그대로 옮긴다(앞선다). 그다음 어느 포트든 `missing` 이 있으면
  `input_window_unmeasured`(category `numeric`, detail `("port", 첫 미측정 넷)`·`("missing", 그 사유)`).
"""
from .aux_types import IcmWindow
from .mna_types import Undefined

QUANTITIES = ("icmr_v", "icm_margin_v", "required_input_cm_v")
CODE_UNMEASURED = "input_window_unmeasured"
INPUT_DC_STATES = ("pending", "declared")
RESOLUTION_ENDS = 1 + 1                                 # icmr 분해능 = 창 두 끝의 tol_v


def _undefined(detail_source):
    return IcmWindow(None, None, undefined=tuple(Undefined(q, *detail_source) for q in QUANTITIES))


def icm_window_metrics(config, ports, input_dc):
    if input_dc not in INPUT_DC_STATES:
        raise ValueError("icm_window_metrics: input_dc %r 은 %r 밖이다" % (input_dc, INPUT_DC_STATES))
    if config.config is None:
        if not config.undefined:
            raise ValueError("icm_window_metrics: 구성 None 인데 icm_config.undefined 가 비었다")
        first = config.undefined[0]
        return _undefined((first.code, first.category, first.detail))
    if not ports:
        raise ValueError("icm_window_metrics: 입력 포트 0 -- 구성이 있는데 포트가 없다")
    lacking = next((p for p in ports if p.missing), None)
    if lacking is not None:
        return _undefined((CODE_UNMEASURED, "numeric", (("port", lacking.net), ("missing", tuple(lacking.missing)))))
    if None in (config.vcm0, config.vcm_lo, config.vcm_hi):
        raise ValueError("icm_window_metrics: 포트는 모두 측정됐는데 V_cm 칸이 None -- icm_config 불일치")
    centre, low, high = config.vcm0, config.vcm_lo, config.vcm_hi
    tol = ports[0].tol_v
    return IcmWindow(high - low, min(centre - low, high - centre), (centre, low, high) if input_dc == "pending" else None,
                     (low, high), centre, input_dc, None if tol is None else RESOLUTION_ENDS * tol, tol)
