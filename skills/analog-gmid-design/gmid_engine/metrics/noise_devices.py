"""봉인 DC 점 -> MOS 소자별 LUT 잡음 값 (설계 41 §7.2 API·§7.3 '잡음원', lut/CONTRACT.md 9.3·9.4, 단위 U8).

진입점: `noise_devices(snapshot, lut, junction, decl) -> NoiseInput`.

* 읽는 것: `device.dc_op`(GB7 `DeviceOp` -- kind·L·W·VGS·VDS·VSB·폭 키). 소자마다 같은 동작점에서 LUT `noise_params`(게이트 환산 S_vg(f) = A/f^EF + B,
  기준 폭 `w_m` 값)를 읽고 폭 W 배율 `w_m/W` 를 곱한다(S_vg 는 같은 전류밀도에서 폭에 반비례 -- 9.3). `B` 가 미상(`b_status` != known)이면 `b` None.
* 허용오차: `tol_noise_table(memo, kind).at(L, VDS, "thermal"|"flicker")`(9.4, 로그 면의 상대 오차) -- 칸이 정의되지 않으면 None(분해능을 정하지 않는다).
* LUT 질의 실패(잡음 파일 없음·L/축 밖 등 `SealViolationError`)는 이 소자의 `failure`(원래 사유)에 적고 예외로 올리지 않는다 -- 잡음 metric 만 정의 불가가 되고
  다른 제약 metric 은 계속 잰다. 잡음 데이터 자체의 부재는 탐색 시작 때 `require_lut_data` 가 거른다(search 컨텍스트).
* `f_lo` = 쓰는 kind 들의 잡음 표 가장 낮은 주파수 점 중 가장 높은 것(모든 kind 에서 실측이 있는 하한 -- 외삽하지 않는다). `kt` = 볼츠만 상수 × (LUT 측정 온도
  [°C] + 0 °C 의 K 값)(PDK/ngspice 와 같은 온도 -- `JunctionSource.temp_c`, 상수는 scipy.constants 의 CODATA 값이지 새로 박은 숫자가 아니다).
* 주의: 이 함수는 LUT memo 를 읽을 뿐 쓰는 것은 memo 의 point/derived 영역이다(상한이 있는 캐시 -- `lut.LutMemo`).
"""
from scipy import constants

from gmid_engine.core import SealViolationError
from gmid_engine.lut import noise_params, tol_noise_table

from .noise_types import NoiseDevice, NoiseInput

TOL_THERMAL = "thermal"          # lut TOL_NOISE_METRICS 원소 (ln B 면)
TOL_FLICKER = "flicker"          # lut TOL_NOISE_METRICS 원소 (ln S_vg(f_lo) 면)


def _reason(exc):
    return dict(exc.record.detail).get("reason") or type(exc).__name__


def _device(memo, name, op):
    try:
        params = noise_params(memo, op.kind, op.w_key, op.L, op.vgs, op.vds, op.vsb)
        table = tol_noise_table(memo, op.kind)
        tol_thermal = table.at(op.L, op.vds, TOL_THERMAL)
        tol_flicker = table.at(op.L, op.vds, TOL_FLICKER)
    except SealViolationError as exc:
        return NoiseDevice(name, failure=_reason(exc))
    scale = params.w_m / op.W
    return NoiseDevice(name, a=params.A * scale, b=None if params.B is None else params.B * scale, ef=params.ef,
                       b_status=params.b_status, tol_flicker=tol_flicker, tol_thermal=tol_thermal)


def _f_lo(memo, kinds):
    lows = [memo.lut.noise[k].freqs[0] for k in kinds if k in memo.lut.noise]
    return float(max(lows)) if lows else None


def noise_devices(snapshot, lut, junction, decl):
    """`snapshot` = S2 스냅샷(`device.dc_op` 가 있다), `lut` = sizing `LutAccess`, `junction` = metrics `JunctionSource`(온도), `decl` = `NoiseDecl`."""
    memo = lut.memo
    ops = sorted(snapshot.column("device", "dc_op"), key=lambda item: item[0])
    devices = tuple(_device(memo, name, op) for name, op in ops)
    kt = constants.k * (junction.temp_c + constants.zero_Celsius)
    return NoiseInput(decl, devices, _f_lo(memo, {op.kind for _name, op in ops}), float(kt))
