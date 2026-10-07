"""GB7 공용 LUT 조회 helper -- 소자 단자 전압·순방향 조회·tol_V 셀·실패에 소자 이름 붙이기 (설계 3.3·3.5, DEC-88,
lut CONTRACT 4·5절).

공개 함수(각각 sizing 안 두 파일 이상이 쓴다, 규칙 A 보충 (3)):

* `terminal_voltages(kind, v_d, v_g, v_s, v_b)` -> (vgs, vds, vsb) 크기(LUT 부호 규약: nmos 그대로, pmos 부호 반전).
  kind 부호의 유일한 정의다(V(g) = V(s) + s·VGS 의 s = `terminal_voltages(kind, 0, 1, 0, 0)[0]`).
* `w_key_of(lut, kind)` -> 레이아웃 전 사이징이 쓰는 그 kind 의 폭 슬라이스 키(`LutAccess.w_keys`).
* `with_device(exc, device, query)` -> LUT `SealViolationError` 에 소자 이름을 붙인 새 예외(LUT 는 소자를 모른다 -- lut
  CONTRACT 머리 '호출부가 덧붙인다'). detail: reason `lut_query_failed`, `lut_reason` = 원래 사유, `device_query`.
* `forward_point(lut, device, kind, L, vgs, vds, vsb)` -> lut.OpPoint(순방향 조회 -- 봉인 2·3·8·종속 좌표·gm_id 보고).
* `tol_v_cell(lut, device, kind, L, vds)` -> id_equivalent tol_V(V) 또는 None(셀 미정의).
"""
from gmid_engine.core import SealViolationError
from gmid_engine.lut import op_point, tol_v_table

from .s2_values import REASON_LUT_QUERY

_SIGNS = (("nmos", 1), ("pmos", -1))
_ID_EQUIVALENT = "id_equivalent"


def terminal_voltages(kind, v_d, v_g, v_s, v_b):
    """노드 전압에서 LUT 축 값(크기): vgs = s·(V(g) − V(s)), vds = s·(V(d) − V(s)), vsb = s·(V(s) − V(b))."""
    sign = dict(_SIGNS)[kind]
    return sign * (v_g - v_s), sign * (v_d - v_s), sign * (v_s - v_b)


def w_key_of(lut, kind):
    return dict(lut.w_keys)[kind]


def with_device(exc, device, query):
    detail = dict(exc.record.detail)
    detail["device_query"] = query
    detail["lut_reason"] = detail.get("reason")
    detail["reason"] = REASON_LUT_QUERY
    return SealViolationError(devices=(device,), margin=exc.record.margin, detail=detail)


def forward_point(lut, device, kind, L, vgs, vds, vsb):
    """순방향 조회 OpPoint(IDu, gm_over_id, ...)."""
    try:
        return op_point(lut.memo, kind, w_key_of(lut, kind), L, vgs, vds, vsb)
    except SealViolationError as exc:
        raise with_device(exc, device, "forward_point") from exc


def tol_v_cell(lut, device, kind, L, vds):
    """(kind, w_key, L 앵커, VDS) 셀의 id_equivalent tol_V. 정의된 셀이 없으면 None."""
    try:
        return tol_v_table(lut.memo, kind, w_key_of(lut, kind)).at(L, vds, _ID_EQUIVALENT)
    except SealViolationError as exc:
        raise with_device(exc, device, "tol_v_cell") from exc
