"""봉인점 소신호 DC 극한 노달 계 계산 블록 (계획 N3.8 '봉인점 DC 야코비안'·O-59 (1), 설계 41 §4.7-3b `graph.ss_nodal`, 카드 IT-2c).

진입점: `ss_nodal_system`(`@compute_block`, writer `ss_nodal`) -- `ss_nodal_system(snapshot, donors=, counters=)`, 추가 인자 없음.
reads `graph.ss_circuit`(조립된 소신호 회로), `device.kind`; writes `graph.ss_nodal`(key `METRICS_KEY`) = `NodalSystem` 또는 `Undefined`.

* 값 `NodalSystem(nodes, fixed, g, g_bound, factor)`: G = `conductance_matrix(ss.circuit, n, bound=True)` 의 컨덕턴스 행렬(MOS gm·gmb·gds 와 저항, **용량 개방**), g_bound = 그 조립
  오차의 항목별 상계 E, 고정 = 교류접지 ∪ 입력 넷의 색인, `factor` = `nodal_factor(g, fixed)`. ndarray 는 모두 읽기 전용이다. **G 의 조립은 이 블록 하나**다 --
  offset·systematic·블록 잔차(`metrics_aux` 의 세 조립 자리)와 측정 구성(`icm_config`)이 이 필드를 READS 로 읽는다.
* 저항 결측: DC 전도 경로를 이루는 수동소자(`is_dc_conducting_passive` -- 저항뿐) 가운데 값이 없는 것이 있으면 G 가 불완전하다 -> `Undefined("ss_nodal",
  "passive_value_undeclared", "definitional", (("elements", 결측 저항 이름 정렬 tuple),))`. 용량만 결측이면 용량은 DC 에서 개방이라 G 에 들지 않으므로 `NodalSystem` 이다.
* `nodal_of(ss)`: `SsCircuit` 하나 -> `NodalSystem`(블록이 부르는 조립 함수, G·g_bound·인수분해를 만드는 자리는 여기 하나). 필드를 거치지 않고 `SsCircuit` 만 가진 단위 호출
  (offset·블록 잔차 함수를 직접 부르는 곳)이 같은 함수를 부른다 -- 블록 경로(`metrics_aux`)는 필드를 넘긴다.
"""
import sys

import numpy

from gmid_engine.core import compute_block
from gmid_engine.sizing import METRICS_KEY, SS_NODAL_WRITER

from ._helpers_nodal import capacitance_matrix, charge_seeded, nodal_factor
from .aux_types import NodalSystem
from .mna_types import Undefined
from .ss_circuit import CODE_PASSIVE_MISSING, is_dc_conducting_passive
from .stamp_mos import mos_stamps
from .stamp_two_terminal import two_terminal_stamps

READS = (("graph", "ss_circuit"), ("device", "kind"))
WRITES = (("graph", "ss_nodal"),)
QUANTITY = "ss_nodal"


def _gamma(count, unit_roundoff):
    """γ_m = m·u / (1 − m·u) (m = 연산 수, γ_0 = 0) -- 부동소수 연산 m 번 누적 오차의 상대 상계(Higham 식 γ_m)."""
    return count * unit_roundoff / (1 - count * unit_roundoff)


def conductance_matrix(circuit, size, *, bound=False):
    """`SmallSignalCircuit`(정수 노드 < size) -> (size, size) 실수 G -- MOS(gm·gmb·gds)와 저항. 용량은 G 에 넣지 않는다(`capacitance_matrix`).

    `bound=True` 면 `(G, g_bound)`: g_bound 는 G 조립 오차의 항목별 상계 E_ij = γ_{max(k_ij−1, 0)}·S_ij + C_ij + γ_{n+1}·|Ĝ_ij|
    (S_ij = Σ|ĝ_s|, k_ij = 항목의 스탬프 항 수, C_ij = Σ γ_{c_s}·|ĝ_s|, c_s = 스탬프 항의 연산 수 `StampSet.g_ops`, n = size, Ĝ = 계산된 G, u = ε/2;
    값 0 항목은 스탬프에서 빠지므로 세지 않는다). 스탬프가 없는 항목은 0. 기본 `False` 면 G 하나(옛 소비자 값 불변)."""
    g = numpy.zeros((size, size))
    stamps = tuple(mos_stamps(m) for m in circuit.mos) + tuple(two_terminal_stamps(r) for r in circuit.resistors)
    terms = {}
    for stamp in stamps:
        for (row, col, value), ops in zip(stamp.g, stamp.g_ops):
            g[row, col] += value
            terms.setdefault((row, col), []).append((value, ops))
    if not bound:
        return g
    unit_roundoff = sys.float_info.epsilon / 2
    g_bound = numpy.zeros((size, size))
    for (row, col), items in terms.items():
        magnitude = sum(abs(value) for value, _ops in items)
        stamp_error = sum(_gamma(ops, unit_roundoff) * abs(value) for value, ops in items)
        g_bound[row, col] = (_gamma(max(len(items) - 1, 0), unit_roundoff) * magnitude + stamp_error
                             + _gamma(size + 1, unit_roundoff) * abs(g[row, col]))
    return g, g_bound


def nodal_of(ss):
    index = {net: i for i, net in enumerate(ss.nodes)}
    g, g_bound = conductance_matrix(ss.circuit, len(ss.nodes), bound=True)
    fixed = frozenset(index[net] for net in tuple(ss.ground_nets) + tuple(ss.input_nets))
    c = capacitance_matrix(ss.circuit, len(ss.nodes)) if charge_seeded(g, fixed) else numpy.zeros(g.shape)
    return NodalSystem(tuple(ss.nodes), fixed, g, g_bound, nodal_factor(g, fixed, c=c))   # 용량 전용 노드(G 행 0)가 있을 때만 C 조립 -- 전하 보존 행(NL-1)


@compute_block(SS_NODAL_WRITER, reads=READS, writes=WRITES)
def ss_nodal_system(projection):
    ss = projection.value("graph", METRICS_KEY, "ss_circuit")
    kinds = dict(projection.column("device", "kind"))
    missing = tuple(name for name in ss.missing if is_dc_conducting_passive(kinds[name]))
    if missing:
        value = Undefined(QUANTITY, CODE_PASSIVE_MISSING, "definitional", (("elements", missing),))
    else:
        value = nodal_of(ss)
        if ss.missing and value.factor[5]:               # 전하 넷이 있는데 값 없는 수동소자가 있으면 C 가 일부다 -- 남은 용량만으로 풀지 않는다(NL-1 T-4f)
            value = Undefined(QUANTITY, CODE_PASSIVE_MISSING, "definitional", (("elements", tuple(sorted(ss.missing))),))
    return {("graph", "ss_nodal"): {METRICS_KEY: value}}
