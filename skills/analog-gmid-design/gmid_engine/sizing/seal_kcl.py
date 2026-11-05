"""봉인 3 KCL 잔차 계산 블록 (계획 N3.6 항목 3·tol_I 식, 설계 3.5·3.6).

진입점: `dc_seal_kcl`(`@compute_block`) -- `dc_seal_kcl(snapshot, resistances)`.

레일이 아닌 노드마다 원소 전류를 **노드전압에서 다시 계산**해 |Σ 나감 − Σ 들어옴| ≤ tol_I:
MOS = 순방향 LUT IDu(노드 VGS·VDS·VSB, `dc_op.idu_forward`) × W/L, DC 저항 = (V(t0) − V(t1))/R(`resistances` = spec 선언 + θ), 이상 전류원 =
`dc_current`(선언·θ), 잎 가지치기 저항 = 0. tol_I(노드) = 그 노드에 채널이 닿는 MOS 의 tol_V × 자기 동작점 gm(`dc_gm`, dc 단계
`dc_tolerances` 가 쓴 ID × LUT gm/ID) 최댓값(N3.6 v6.4, 설계 40 §3.7-3 -- parent 무관). MOS 가 닿지 않는 노드는 LUT 오차원이 없어 부동소수 한계
n·eps·Σ|I|. MOS 가 닿는데 tol_V 가 모두 미정이면 undefined. 규칙은 레일이 아닌 모든 넷의 KCL 검사 하나다.
"""
import sys

from gmid_engine.core import compute_block
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_PASSIVE

from ._helpers_seal import judge, node_values
from .s2_values import DC_KEY, DC_SEAL_KCL_WRITER, SEAL_KCL

READS = (
    ("device", "dc_op"), ("device", "dc_current"), ("device", "dc_tol_v"), ("device", "dc_gm"),
    ("device", "element_class"), ("node", "dc_v"), ("node", "dc_rail_v"), ("graph", "dc_current_basis"),
)
WRITES = (("graph", "dc_seal_3"),)


@compute_block(DC_SEAL_KCL_WRITER, reads=READS, writes=WRITES)
def dc_seal_kcl(projection):
    (resistances,) = projection.extras
    resistances = dict(resistances)
    values = node_values(projection)
    rails = set(dict(projection.column("node", "dc_rail_v")))
    ops = dict(projection.column("device", "dc_op"))
    currents = dict(projection.column("device", "dc_current"))
    tol_v = dict(projection.column("device", "dc_tol_v"))
    gm = dict(projection.column("device", "dc_gm"))
    classes = dict(projection.column("device", "element_class"))
    basis = projection.value("graph", DC_KEY, "dc_current_basis")
    flows = {}
    for name, a, b in basis.ends:
        if classes[name] == ELEMENT_MOS:
            op = ops[name]
            current = op.idu_forward * op.W / op.L
        elif classes[name] == ELEMENT_PASSIVE:
            current = (values[a] - values[b]) / resistances[name]
        else:
            current = currents[name]
        for net, sign in ((a, 1), (b, -1)):
            if net not in rails:
                flows.setdefault(net, []).append((name, sign * current))
    rows = []
    for net, items in sorted(flows.items()):
        residual = abs(sum(i for _n, i in items))
        mos = tuple(sorted(n for n, _i in items if classes[n] == ELEMENT_MOS))
        if mos:
            defined = [tol_v[m] * gm[m] for m in mos if tol_v[m] is not None]
            tol = max(defined) if defined else None
        else:
            tol = len(items) * sys.float_info.epsilon * sum(abs(i) for _n, i in items)
        rows.append((net, residual, tol, mos, (net,)))
    return {("graph", "dc_seal_3"): {DC_KEY: judge(SEAL_KCL, rows)}}
