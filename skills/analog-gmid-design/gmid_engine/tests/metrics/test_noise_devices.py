"""[U8 2026-10-09] `noise_devices(snapshot, lut, junction, decl)` -- 봉인 DC 점 -> MOS 소자별 LUT 잡음 값 (설계 41 §7.2 API·§7.3 '잡음원', lut CONTRACT 9.3·9.6,
metrics CONTRACT 10.1).

oracle:
* (a) lut CONTRACT 9.6 손계산 toy(tests/lut conftest `NoiseToy`): 모든 점 S_vg = A0/f + B0, Cgd = 0 -> noise_params = (A0, B0, EF 1, known, 기준 폭 1 µm).
  폭 W 소자는 A·B 모두 w_m/W 배(9.3 '같은 전류밀도에서 S_vg 는 폭에 반비례') -> 기대 a = A0·w_m/W, b = B0·w_m/W.
  Cgd > 0 이면 모든 점 피드스루 탈락 -> B 미상(b None, b_status no_feedthrough_free_point).
* (d) kT = scipy.constants.k × (JunctionSource.temp_c + zero_Celsius)(계약 10.1), f_lo = 잡음 표의 가장 낮은 주파수 점(toy 1 Hz), LUT 질의 실패는 그 소자의
  failure(예외 아님), 잡음 파일이 없으면 f_lo None.
입력 스냅샷·LutAccess·JunctionSource 는 이 함수가 읽는 열·속성만 가진 대역(duck)이다(구성 입력).
"""
from types import SimpleNamespace

import numpy as np
import pytest
from scipy import constants

from gmid_engine.lut import LutMemo
from gmid_engine.metrics import NoiseDecl, NoiseInput, noise_devices
from gmid_engine.sizing import DeviceOp

from lut.conftest import TOY_SHAPE, NoiseToy

A0, B0 = 1e-12, 1e-16
W_REF = 1e-6                    # NoiseToy 기준 폭(w_ref_m) = 폭 키 100(격자 1e-8)


class _Snap:
    def __init__(self, ops):
        self._ops = tuple(ops.items())

    def column(self, kind, field):
        assert (kind, field) == ("device", "dc_op")
        return self._ops


def _op(L=2e-6, W=4e-6, vgs=0.5, vds=0.75, vsb=0.25, w_key=100):
    return DeviceOp("nmos", 1e-5, -13.0, 12.0, L, W, vgs, vds, vsb, w_key, 1.0)


def _access(tmp_path, cgd=0.0, with_noise=True):
    toy = NoiseToy(tmp_path, np.full(TOY_SHAPE, A0), np.full(TOY_SHAPE, B0), cgd=cgd)
    lut = toy.load() if with_noise else _no_noise(toy)
    return SimpleNamespace(memo=LutMemo(lut, point=256, curve=256, root=256))


def _no_noise(toy):
    from gmid_engine.lut import load_lut_set
    from lut.conftest import TOY_NOISE_SPEC
    return load_lut_set(str(toy.build.manifest), str(toy.build.cap), TOY_NOISE_SPEC, bin_rule=toy.build.bin_rule,
                         pdk_root=toy.build.tb.pdk_root)


JUNCTION = SimpleNamespace(temp_c=27.0)


@pytest.mark.parametrize("W", [1e-6, 4e-6, 2.5e-6])
def test_width_scaling_and_kt(tmp_path, W):
    decl = NoiseDecl(feedback=())
    out = noise_devices(_Snap({"M2": _op(W=W), "M1": _op(W=W)}), _access(tmp_path), JUNCTION, decl)
    assert isinstance(out, NoiseInput)
    assert out.decl == decl
    assert [d.name for d in out.devices] == ["M1", "M2"]                     # 이름순
    for d in out.devices:
        assert d.failure is None and d.b_status == "known" and d.ef == 1.0
        assert d.a == pytest.approx(A0 * W_REF / W, rel=1e-9)
        assert d.b == pytest.approx(B0 * W_REF / W, rel=1e-9)
    assert out.f_lo == 1.0
    assert out.kt == constants.k * (27.0 + constants.zero_Celsius)


def test_unknown_thermal_plateau(tmp_path):
    out = noise_devices(_Snap({"M1": _op()}), _access(tmp_path, cgd=2e-16), JUNCTION, NoiseDecl())
    d = out.devices[0]
    assert d.b is None and d.b_status == "no_feedthrough_free_point" and d.failure is None
    assert d.a == pytest.approx((A0 + B0) * W_REF / 4e-6, rel=1e-9)        # 9.6: 미상이면 A = S_lo·f_lo^EF


def test_query_failure_is_recorded_not_raised(tmp_path):
    out = noise_devices(_Snap({"M1": _op(L=10e-6), "M2": _op()}), _access(tmp_path), JUNCTION, NoiseDecl())
    bad, good = out.devices
    assert bad.name == "M1" and bad.failure and bad.a is None and bad.b is None
    assert good.failure is None and good.b == pytest.approx(B0 * W_REF / 4e-6, rel=1e-9)


def test_no_noise_file(tmp_path):
    out = noise_devices(_Snap({"M1": _op()}), _access(tmp_path, with_noise=False), JUNCTION, NoiseDecl())
    assert out.f_lo is None
    assert out.devices[0].failure == "lut_noise_unavailable"                # lut CONTRACT 9.3 사유
