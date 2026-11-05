"""DC 풀이 공용 회로 입력 묶음 `Circuit` -- 평가 커널(`dc_solve`)와 측정 구성(`icm_config`)이 같은 입력을 읽는다 (설계 41 §4.7-4, 카드 IT-2c).

공개: `Circuit(projection, *, lut, linear)` -- 블록이 투영(`.column(kind, field)` 질의만)에서 읽는 열을 한 번 풀어 읽기 전용 값(`MappingProxyType`·tuple·frozenset)으로 두는
묶음. 속성은 호출자가 바꿀 수 없다. 쓰기가 필요한 상태(θ·고정 값·tol 셀 등)는 이 클래스를 잇는 `block_dc._Circuit` 가 가진다.

* 읽는 열: `node.dc_writer`·`node.dc_rail_v`·`device.pins`·`device.kind`·`device.bulk`·`device.dc_L`·`device.dc_colour`·`device.dc_coord` (모두 `dc_solve` READS 의 부분집합).
  `lut` = `LutAccess`(VDSAT 조회), `linear` = `triode` 선언 소자 이름 집합 -- 두 키워드는 필수(빠지면 `TypeError`).
* `mos_point(m, values) -> (vgs, vds, vsb)`·`vds_vsb(m, values) -> (vds, vsb)`: 노드전압 `values` 에서 LUT 축 크기(kind 부호 반영, `_helpers_lut.terminal_voltages`).
* `canonical_writers()`: (넷, writer) 를 쓰기 순번 순으로(이름순이 아니다 -- 이름 치환이 행·합산 순서를 바꾸지 않게).
* `kind_sign(kind) -> ±1`(정적): V(g) = V(s) + s·VGS 의 s = `terminal_voltages(kind, 0, 1, 0, 0)[0]` -- 부호의 정의 하나.
* `region_rows(values, sat) -> tuple | None`: 창 경계 행(설계 41 4.7-3a, 4.7-W W2) -- `dc_coord` MOS 마다 5원소 행 `(a, b, sign, slack, kind)`, kind ∈ {"sat", "triode"}.
  선언 없음 = `(d, s, 부호, VDS − VDSAT, "sat")`, `triode` 선언 = `(d, s, −부호, VDSAT − VDS, "triode")`. 경계 = VDS = VDSAT, **판정 여유 0**(tol 항 없음, O-204).
  VDSAT = 포화 기준 `SatBound.vdsat_v`: `sat` = {MOS: `SatBound`}
  (봉인점 `device.dc_sat_v` 필드 -- 봉인점 창 행)를 읽는다(LUT 호출 0, WB-1: 시도 전압 LUT 경로 삭제). 값이 없는 사유(열 없음·정의역 밖·역방향 VDS)면 행을 정의할 수 없어 None(창을 좁히지 않고 호출자가 측정 실패로 본다).
  `values` 에 레일이 없으면 이 묶음의 `node.dc_rail_v` 로 채운다(레일 값은 입력이 아니라 선언이다). `off` 선언·전도 판정은 없다.
* `port_window(value, slope, dlo, dhi) -> (lo, hi)`: 포트 창 = 두 끝 전압 V + s·dlo, V + s·dhi 의 [min, max] ∩ [레일 최소, 레일 최대](감도 음수 포트는 아래 끝이 위 끝이 된다).
  감도 0 이면 포트가 x 를 따라 움직이지 않으므로 두 끝이 모두 V.
* `default_port_views(projection, directions) -> tuple`·`sense_signs(view, roles) -> tuple | None`: ICMR 측정 구성(`icm_config`)과 실현 평가 servo(`dc_solve`)가 같이 읽는
  기본 포트 전달 뷰와 감지 부호의 정의 한 곳(투영에 `graph.views`·`node.port_role` 열이 있어야 한다).
"""
import types

from gmid_engine.authoring import INPUT_DIRECTION, ROLE_DIFFERENTIAL_OUTPUT_N, ROLE_DIFFERENTIAL_OUTPUT_P
from gmid_engine.graph import MOS_TERMINAL_NAMES, S1V_KEY, VIEW_TRANSFER, default_port_seeds

from ._helpers_lut import terminal_voltages

_ROW_SAT = "sat"                                      # `region_rows` 행 종류: 선언 없음(포화)
_ROW_TRIODE = "triode"                                # `intended_region: triode` 선언 소자


def default_port_views(projection, directions):
    """기본 포트 전달 뷰 목록 -- S1v `graph.views` 가 있으면 그 `default_port` 뷰, 없으면 같은 규칙을 포트 사실에서(규칙 정의는 `graph/views.py` 하나)."""
    found = dict(projection.column("graph", "views"))
    if S1V_KEY in found:
        return tuple(view for view in found[S1V_KEY] if view.kind == VIEW_TRANSFER and view.default_port)
    roles = dict(projection.column("node", "port_role"))
    inputs = tuple((net, roles[net]) for net, d in sorted(directions.items()) if d == INPUT_DIRECTION)
    outputs = tuple((net, roles[net]) for net, d in sorted(directions.items()) if d is not None and d != INPUT_DIRECTION)
    return tuple(default_port_seeds(inputs, outputs))


def pivot_config(snapshot):
    """스냅샷의 servo 피벗 판정 `graph.icm_config.config`(IT-2c; 필드가 없으면 None) -- 실현 평가 갈래(`dc_solve`)와 갈래 대조(`realize_front`)가 같은 읽기 한 곳을 쓴다."""
    found = [cfg.config for _key, cfg in snapshot.column("graph", "icm_config")]
    return found[0] if found else None


def sense_signs(view, roles):
    """뷰 감지 넷 -> ((넷, 부호), ...): 출력 하나 = +1, 차동 출력쌍 = (p +1, n −1), 그 밖은 None."""
    sense = tuple(view.sense)
    if len(sense) == 1:
        return ((sense[0], 1.0),)
    plus = tuple(net for net in sense if roles.get(net) == ROLE_DIFFERENTIAL_OUTPUT_P)
    minus = tuple(net for net in sense if roles.get(net) == ROLE_DIFFERENTIAL_OUTPUT_N)
    if len(sense) == len(plus) + len(minus) and len(plus) == 1 and len(minus) == 1:
        return ((plus[0], 1.0), (minus[0], -1.0))
    return None


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

    def region_rows(self, values, sat):
        """창 경계 행 셋(모듈 머리말): `dc_coord` MOS 마다 `(a, b, sign, slack, kind)`. VDSAT 를 정의할 수 없으면 None."""
        point = {**self.rail_v, **values}
        rows = []
        for m in sorted(self.coord, key=lambda x: (self.device_colour.get(x, 0), x)):
            kind = self.kinds[m]
            d, _g, s = (self.pins[m][t] for t in MOS_TERMINAL_NAMES)
            _vgs, vds, _vsb = self.mos_point(m, point)
            bound = sat[m]
            if bound.vdsat_v is None:
                return None
            sign = self.kind_sign(kind)
            if m in self.linear:
                rows.append((d, s, -sign, bound.vdsat_v - vds, _ROW_TRIODE))
            else:
                rows.append((d, s, sign, vds - bound.vdsat_v, _ROW_SAT))
        return tuple(rows)

    def port_window(self, value, slope, dlo, dhi):
        """포트 창(모듈 머리말)."""
        if slope == 0:
            a = b = value
        else:
            a, b = value + slope * dlo, value + slope * dhi
        return max(min(a, b), self.lo), min(max(a, b), self.hi)
