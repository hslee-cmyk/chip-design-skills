"""DC 풀이 공용 회로 입력 묶음 `Circuit` -- 평가 커널(`dc_columns`)과 측정 구성(`icm_config`)이 같은 입력을 읽는다 (설계 41 §4.7-4, 카드 IT-2c).

공개: `Circuit(projection, *, lut, linear)` -- 블록이 투영(`.column(kind, field)` 질의만)에서 읽는 열을 한 번 풀어 읽기 전용 값(`MappingProxyType`·tuple·frozenset)으로 두는
묶음. 속성은 호출자가 바꿀 수 없다. 쓰기가 필요한 상태(θ·고정 값·`override`·tol 셀 등)는 이 클래스를 잇는 `block_columns._Circuit` 가 가진다.

* 읽는 열: `node.dc_writer`·`node.dc_rail_v`·`device.pins`·`device.kind`·`device.bulk`·`device.dc_L`·`device.dc_colour`·`device.dc_coord` (모두 `dc_columns` READS 의 부분집합).
  `lut` = `LutAccess`(VDSAT 조회), `linear` = `triode` 선언 소자 이름 집합 -- 두 키워드는 필수(빠지면 `TypeError`).
* `mos_point(m, values) -> (vgs, vds, vsb)`·`vds_vsb(m, values) -> (vds, vsb)`: 노드전압 `values` 에서 LUT 축 크기(kind 부호 반영, `_helpers_lut.terminal_voltages`).
* `canonical_writers()`: (넷, writer) 를 쓰기 순번 순으로(이름순이 아니다 -- 이름 치환이 행·합산 순서를 바꾸지 않게).
* `kind_sign(kind) -> ±1`(정적): V(g) = V(s) + s·VGS 의 s = `terminal_voltages(kind, 0, 1, 0, 0)[0]` -- 부호의 정의 하나.
* `region_rows(values) -> tuple | None`: 창 경계 행(설계 41 4.7-3a, 4.7-W W2) -- `dc_coord` MOS 마다 5원소 행 `(a, b, sign, slack, kind)`, kind ∈ {"sat", "triode"}.
  선언 없음 = `(d, s, 부호, VDS − VDSAT, "sat")`, `triode` 선언 = `(d, s, −부호, VDSAT − VDS, "triode")`. 경계 = VDS = VDSAT, **판정 여유 0**(tol 항 없음, O-204).
  VDSAT = LUT `vdsat` 조회(엔진 밖 데이터). LUT 에 VDSAT 열이 없거나 그 점이 조회 정의역 밖이면 행을 정의할 수 없어 None(창을 좁히지 않고 호출자가 측정 실패로 본다).
  `values` 에 레일이 없으면 이 묶음의 `node.dc_rail_v` 로 채운다(레일 값은 입력이 아니라 선언이다). `off` 선언·전도 판정은 없다.
* `port_window(value, slope, dlo, dhi) -> (lo, hi)`: 포트 창 = 두 끝 전압 V + s·dlo, V + s·dhi 의 [min, max] ∩ [레일 최소, 레일 최대](감도 음수 포트는 아래 끝이 위 끝이 된다).
  감도 0 이면 포트가 x 를 따라 움직이지 않으므로 두 끝이 모두 V.
"""
import types

from gmid_engine.core import SealViolationError
from gmid_engine.graph import MOS_TERMINAL_NAMES
from gmid_engine.lut import vdsat

from ._helpers_lut import terminal_voltages, w_key_of

_ROW_SAT = "sat"                                      # `region_rows` 행 종류: 선언 없음(포화)
_ROW_TRIODE = "triode"                                # `intended_region: triode` 선언 소자


class Circuit:
    """블록 한 번의 읽기 전용 입력 묶음(모듈 머리말)."""

    def __init__(self, projection, *, lut, linear):
        self.lut = lut
        self.linear = frozenset(linear)                # `triode` 선언 소자 -- 창 경계 행이 triode 행(`region_rows`)
        self.writers = types.MappingProxyType(dict(projection.column("node", "dc_writer")))
        self.rail_v = types.MappingProxyType(dict(projection.column("node", "dc_rail_v")))
        self.pins = types.MappingProxyType({n: types.MappingProxyType(dict(p)) for n, p in projection.column("device", "pins")})
        self.kinds = types.MappingProxyType(dict(projection.column("device", "kind")))
        self.bulk = types.MappingProxyType({n: b.net for n, b in projection.column("device", "bulk")})
        self.L = types.MappingProxyType(dict(projection.column("device", "dc_L")))
        self.coord = types.MappingProxyType(dict(projection.column("device", "dc_coord")))
        self.device_colour = types.MappingProxyType(dict(projection.column("device", "dc_colour")))
        volts = tuple(self.rail_v.values())
        self.lo, self.hi = min(volts), max(volts)

    @staticmethod
    def kind_sign(kind):
        """V(g) = V(s) + s·VGS 의 s -- `terminal_voltages` 의 부호 정의를 그대로 읽는다(정의 하나)."""
        return terminal_voltages(kind, 0.0, 1.0, 0.0, 0.0)[0]

    def mos_point(self, m, values):
        """(vgs, vds, vsb) 크기 -- 네 단자 값이 모두 있어야 한다."""
        d, g, s = (self.pins[m][t] for t in MOS_TERMINAL_NAMES)
        return terminal_voltages(self.kinds[m], values[d], values[g], values[s], values[self.bulk[m]])

    def vds_vsb(self, m, values):
        """(vds, vsb) 크기 -- gate 값을 읽지 않는다(writer 가 gate 를 쓰는 중일 수 있다)."""
        d, _g, s = (self.pins[m][t] for t in MOS_TERMINAL_NAMES)
        _vgs, vds, vsb = terminal_voltages(self.kinds[m], values[d], values[s], values[s], values[self.bulk[m]])
        return vds, vsb

    def canonical_writers(self):
        """(넷, writer) 를 쓰기 순번 순으로 -- 이름순이 아니다(이름 치환이 행·합산 순서를 바꾸지 않게)."""
        return sorted(self.writers.items(), key=lambda kv: kv[1].order)

    def region_rows(self, values):
        """창 경계 행 셋(모듈 머리말): `dc_coord` MOS 마다 `(a, b, sign, slack, kind)`. VDSAT 를 정의할 수 없으면 None."""
        point = {**self.rail_v, **values}
        rows = []
        for m in sorted(self.coord, key=lambda x: (self.device_colour.get(x, 0), x)):
            kind = self.kinds[m]
            d, _g, s = (self.pins[m][t] for t in MOS_TERMINAL_NAMES)
            vgs, vds, vsb = self.mos_point(m, point)
            try:
                sat = vdsat(self.lut.memo, kind, w_key_of(self.lut, kind), self.L[m], vgs, vds, vsb)
            except SealViolationError:
                return None
            sign = self.kind_sign(kind)
            if m in self.linear:
                rows.append((d, s, -sign, sat - vds, _ROW_TRIODE))
            else:
                rows.append((d, s, sign, vds - sat, _ROW_SAT))
        return tuple(rows)

    def port_window(self, value, slope, dlo, dhi):
        """포트 창(모듈 머리말)."""
        if slope == 0:
            a = b = value
        else:
            a, b = value + slope * dlo, value + slope * dhi
        return max(min(a, b), self.lo), min(max(a, b), self.hi)
