"""봉인 3 KCL 잔차 계산 블록 (계획 N3.6 항목 3·tol_I 식, 설계 3.5·3.6).

진입점: `dc_seal_kcl`(`@compute_block`) -- `dc_seal_kcl(snapshot, resistances)`.

레일도 입력 포트도 아닌 노드마다 원소 전류를 **노드전압에서 다시 계산**해 |Σ 나감 − Σ 들어옴| ≤ tol_I:
MOS = 순방향 LUT IDu(노드 VGS·VDS·VSB, `dc_op.idu_forward`) × W/L, DC 저항 = (V(t0) − V(t1))/R(`resistances` = spec 선언 + θ), 이상 전류원 =
`dc_current`(선언·θ), 잎 가지치기 저항 = 0. tol_I(노드) = 그 노드에 채널이 닿는 MOS 의 tol_V × 자기 동작점 gm(`dc_gm`, dc 단계
`dc_tolerances` 가 쓴 ID × LUT gm/ID) 최댓값(N3.6 v6.4, 설계 40 §3.7-3 -- parent 무관). MOS 가 닿지 않는 노드는 LUT 오차원이 없어 부동소수 한계
n·eps·Σ|I|. MOS 가 닿는데 그 tol_V 가운데 미정이 하나라도 있으면 tol_I 는 미정(집계 규칙 하나 -- 계획 N3.6 표 10행)이라 undefined.
판정 대상 = 레일도 입력 포트도 아닌 모든 넷의 KCL 검사 하나다(servo 출력·spec 목표 넷·내부 넷 행 유지).
**입력 포트 넷**(`input_port_nets` -- 측정 구성 원이 구동하는 넷, 계획 N3.6 '측정 구성 원 넷'): 원이 닫는 넷의 KCL 은 방정식이 아니라 판정하지 않고, 그 넷의 원 DC
전류(= 원소 끝이 닿는 부호 합, 행 잔차와 같은 부호)를 같은 레코드 detail `input_source_current` = ((넷, 합), ...) 에 **출력 전용**으로 기록한다(판정 소비자 0).
"""
import sys

from gmid_engine.authoring import input_port_nets
from gmid_engine.core import compute_block
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_PASSIVE

from ._helpers_seal import judge, node_values
from .s2_values import DC_KEY, DC_SEAL_KCL_WRITER, SEAL_KCL

READS = (
    ("device", "dc_op"), ("device", "dc_current"), ("device", "dc_tol_v"), ("device", "dc_gm"),
    ("device", "element_class"), ("node", "dc_v"), ("node", "dc_rail_v"), ("node", "port_direction"), ("graph", "dc_current_basis"),
)
INPUT_SOURCE_CURRENT = "input_source_current"          # detail 칸 이름(출력 전용 기록)
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
    inputs = input_port_nets(projection.column("node", "port_direction"))
    rows, source_current = [], []
    for net, items in sorted(flows.items()):
        total = sum(i for _n, i in items)
        if net in inputs:                                   # 원이 구동하는 넷 -- 판정 행 아님, 원 전류만 기록
            source_current.append((net, total))
            continue
        residual = abs(total)
        mos = tuple(sorted(n for n, _i in items if classes[n] == ELEMENT_MOS))
        if mos:
            terms = [None if tol_v[m] is None else tol_v[m] * gm[m] for m in mos]
            tol = None if None in terms else max(terms)        # 집계 항에 None 이 있으면 집계 = None
        else:
            tol = len(items) * sys.float_info.epsilon * sum(abs(i) for _n, i in items)
        rows.append((net, residual, tol, mos, (net,)))
    return {("graph", "dc_seal_3"): {DC_KEY: judge(SEAL_KCL, rows, ((INPUT_SOURCE_CURRENT, tuple(source_current)),))}}
