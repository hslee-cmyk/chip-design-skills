"""계통 offset -- 봉인 DC 동작점의 입력 0 출력 오차 / 차동 이득 (설계 40 §3.8-8 `offset_sys_mv`, 체크리스트 D-OF3).

진입점: `offset_systematic(ss, view, node_v, targets, node_tol_v=None) -> OffsetSystematic`.

* 출력 오차(입력 차 0): 감지가 쌍(p, n)이면 **차동 출력** = V_dc(p) − V_dc(n). 감지가 하나면 **단일 출력** = V_dc(out) − 선언된 출력 기준 DC
  (`targets` = spec `node_voltage_targets_v` 의 (넷, V) -- 그 출력 넷에 선언이 없으면 값을 내지 않고 `reference_undeclared`로 보고한다).
* 나누는 이득 A_dm = 같은 뷰의 DC 극한 전달(`offset_analysis` 와 같은 계, 부호 포함). 값은 크기 |오차| / |A_dm| 를 mv 로(상한 제약 `<=` 용),
  부호 있는 오차는 `output_error_v` 로 싣는다.
* `node_v` = {넷: 봉인 DC 전압}(동작점 -- 실제 VDS 반영), `node_tol_v` = {넷: 그 넷 전압의 허용오차 V}(호출자가 넷에 닿은 MOS 의 tol_V 합으로 만든다,
  DC tol 의 전파). 분해능 = 오차를 이루는 넷들의 허용오차 합 / |A_dm|. 허용오차가 없으면 None.
* 정의 불가: 뷰가 전달 뷰가 아님(`unsupported_view`), 계 특이(`singular_dc`), A_dm = 0(`gain_zero`), 출력 DC 없음(`output_dc_missing`),
  단일 출력 기준 없음(`reference_undeclared`).
"""
from gmid_engine.core import MV_PER_V

from ._helpers_nodal import conductance_matrix, nodal_factor, nodal_solve
from ._helpers_view import view_system
from .aux_types import OffsetSystematic
from .mna_types import Undefined

QUANTITY = "sys_mv"


def _bare(code, detail=(), **fields):
    return OffsetSystematic(None, undefined=(Undefined(QUANTITY, code, "definitional", detail),), **fields)


def offset_systematic(ss, view, node_v, targets, node_tol_v=None):
    system = view_system(ss, view)
    if system is None:
        return _bare("unsupported_view", (("mode", getattr(view, "mode", None)),))
    fixed, drive, sense, _pairs, (sense_p, sense_n) = system
    volts = dict(node_v)
    if sense_p not in volts or (sense_n is not None and sense_n not in volts):
        return _bare("output_dc_missing", (("nets", tuple(n for n in (sense_p, sense_n) if n is not None and n not in volts)),))
    if sense_n is not None:
        error = volts[sense_p] - volts[sense_n]
        nets = (sense_p, sense_n)
    else:
        reference = dict(targets).get(sense_p)
        if reference is None:
            return _bare("reference_undeclared", (("net", sense_p),))
        error = volts[sense_p] - reference
        nets = (sense_p,)
    size = len(ss.nodes)
    factor = nodal_factor(conductance_matrix(ss.circuit, size), fixed)
    volt, _residual = nodal_solve(factor, size, drive)
    if volt is None:
        return _bare("singular_dc", output_error_v=error)
    a_dm = float(sense @ volt)
    if not abs(a_dm) > 0:
        return _bare("gain_zero", output_error_v=error, a_dm=a_dm)
    tol = dict(node_tol_v or {})
    resolution = None if any(tol.get(n) is None for n in nets) else sum(tol[n] for n in nets) / abs(a_dm) * MV_PER_V
    return OffsetSystematic(abs(error) / abs(a_dm) * MV_PER_V, error, a_dm, resolution)
