"""GB7 공용 LUT 조회 helper -- 소자 단자 전압·tol_V 셀·실패에 소자 이름 붙이기 (설계 3.3·3.5, DEC-88, lut CONTRACT 4·5절).

공개 함수(각각 sizing 안 두 파일 이상이 쓴다, 규칙 A 보충 (3)):

* `terminal_voltages(kind, v_d, v_g, v_s, v_b)` -> (vgs, vds, vsb) 크기(LUT 부호 규약: nmos 그대로, pmos 부호 반전).
  kind 부호의 유일한 정의다(V(g) = V(s) + s·VGS 의 s = `terminal_voltages(kind, 0, 1, 0, 0)[0]`).
* `with_device(exc, device, query)` -> LUT `SealViolationError` 에 소자 이름을 붙인 새 예외(LUT 는 소자를 모른다 -- lut
  CONTRACT 머리 '호출부가 덧붙인다'). detail: reason `lut_query_failed`, `lut_reason` = 원래 사유, `device_query`. 이미 `slice_missing` 인
  예외는 reason 을 바꾸지 않는다(그대로 소자만 채운다).

폭 슬라이스 키는 이 파일이 정하지 않는다: 소자마다 `DeviceOp.w_key`(선택 결과, WB-1)가 정하고 부르는 쪽이 넘긴다.
"""
from gmid_engine.core import SealViolationError

from .s2_values import REASON_LUT_QUERY

_SIGNS = (("nmos", 1), ("pmos", -1))
_KEEP_REASONS = ("slice_missing",)


def terminal_voltages(kind, v_d, v_g, v_s, v_b):
    """노드 전압에서 LUT 축 값(크기): vgs = s·(V(g) − V(s)), vds = s·(V(d) − V(s)), vsb = s·(V(s) − V(b))."""
    sign = dict(_SIGNS)[kind]
    return sign * (v_g - v_s), sign * (v_d - v_s), sign * (v_s - v_b)


def with_device(exc, device, query):
    detail = dict(exc.record.detail)
    if detail.get("reason") in _KEEP_REASONS:
        return SealViolationError(devices=(device,), margin=exc.record.margin, detail=detail)
    detail["device_query"] = query
    detail["lut_reason"] = detail.get("reason")
    detail["reason"] = REASON_LUT_QUERY
    return SealViolationError(devices=(device,), margin=exc.record.margin, detail=detail)
