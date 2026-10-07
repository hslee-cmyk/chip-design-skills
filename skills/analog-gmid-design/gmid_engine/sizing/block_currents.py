"""② 원소 전류 계산 블록 (설계 3.2 1, 계획 DEC-70 θ 전류 기저, DEC-08 값 선언 이상원).

진입점: `dc_currents`(`@compute_block`) -- `dc_currents(snapshot, theta_currents)`.

* reads `graph.dc_current_basis` 만(노드전압을 읽지 않는다 -- gm/ID 매개화에서 VGS 가 ID 를 포함하지 않는다, DEC-70).
* extras `theta_currents` = ((원소, A), ...) θ 전류 성분(기저 `free` 와 같은 키, 아니면 `ValueError`).
* writes `device.dc_current` = 모든 DC 원소 전류(전도 방향 양수) + 잎 가지치기 저항 0.0, `device.dc_drop_current` = 그중
  저항(가지치기 포함)만 -- 노드전압 블록(`dc_columns`)은 저항 강하에 쓰는 이 필드만 읽는다(MOS·이상원 전류만 바뀐 θ 에서
  노드전압 블록과 그 하류가 다시 돌지 않게).
* 전도 MOS 전류 ≤ 0(유리수로 정확히 잼)은 θ 정의역(`ThetaSchema.current_cone`) 밖이라 `check_theta` 가 먼저 거부한다.
  이 블록을 정의역 밖 θ 로 직접 부르면 `ValueError`(호출 계약 위반, 후보 실패가 아니다).
"""
from fractions import Fraction

from gmid_engine.core import compute_block

from .s2_values import DC_CURRENTS_WRITER, DC_KEY

READS = (("graph", "dc_current_basis"),)
WRITES = (("device", "dc_current"), ("device", "dc_drop_current"))


@compute_block(DC_CURRENTS_WRITER, reads=READS, writes=WRITES)
def dc_currents(projection):
    (theta_currents,) = projection.extras
    basis = projection.value("graph", DC_KEY, "dc_current_basis")
    source = dict(theta_currents)
    if set(source) != set(basis.free):
        raise ValueError("dc_currents: θ 전류 키가 기저와 다르다: " + repr(sorted(set(source) ^ set(basis.free))))
    source.update(basis.fixed)
    exact = {name: sum(Fraction(t.num, t.den) * Fraction(source[t.source]) for t in terms) for name, terms in basis.rows}
    bad = tuple(sorted(name for name in basis.mos if not exact[name] > 0))
    if bad:
        raise ValueError("dc_currents: θ 전류가 정의역(전도 MOS 전류 > 0) 밖이다 " + repr(bad))
    currents = {name: float(value) for name, value in exact.items()}
    currents.update({name: 0.0 for name in basis.pruned})
    drops = {name: currents[name] for name in basis.resistors + basis.pruned}
    return {("device", "dc_current"): currents, ("device", "dc_drop_current"): drops}
