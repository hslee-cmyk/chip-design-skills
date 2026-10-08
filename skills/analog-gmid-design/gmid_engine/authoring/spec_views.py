"""view 를 적지 않은 제약의 기본 뷰 유도 -- 선언(spec feedback·topology ports·수동소자 단자)에서만 (7a design 2.2·2.3·2.5·3.1).

진입점: `default_views(topology, feedback) -> DefaultViews`.

spec 로드 한 번에 한 번 계산해 모든 제약이 같이 쓴다(제약마다 다시 유도하지 않는다). 회로·넷·소자 이름 리터럴과 숫자
상수가 없다 -- 가중은 포트 수와 role 부호, 0·1 은 정의값.

* 입력 포트 role 가중(2.3): 차동 입력 포트 집합 D(role `ROLE_DIFFERENTIAL_INPUT_P`/`_N`)의 p = +1/|D|, n = −1/|D|
  (|D| = 2 → v_id = 1, v_cm = 0), 단일 입력(`ROLE_SINGLE_ENDED_INPUT`) = 1. 그 밖 role 의 입력 포트는 가중이 없다.
* `port`(전달·루프 β = 1 의 포트 뷰): 여기 = 입력 포트가 차동쌍 1개(p·n 각 1개, 다른 입력 없음) 또는 단일 입력 1개일 때 그
  role 가중, 관측 = 출력 포트가 1개면 그 넷 single_ended, role `ROLE_DIFFERENTIAL_OUTPUT_P`/`_N` 쌍 2개면 differential.
  아니면 `view_required` 사유 문자열.
* `loop`(2.2·2.5): feedback 결정 대기면 `ViewDecl("pending", decision=그 ID)`(실행 전 정지가 모은다). 빈 tuple 이면
  β = 1 -- 포트 뷰와 같은 여기·관측(`beta` unity, 같은 MnaSystem 이라 `pm_ss_deg` = 기본 포트 뷰 `parasitic_pm_ss_deg`).
  비어 있지 않으면 β 루프 -- 소자마다 입력 포트 넷 쪽 단자(`_feedback_cuts`)가 절단 넷, `cuts` = (소자, 절단 넷),
  `weights` = 절단 넷의 role 가중(가중 없는 role 이면 `view_required` 사유). feedback 이 거부돼 None 이거나 소자 절단
  단자가 정확히 하나가 아니면(elements 게이트가 이미 거부) 유도하지 않은 `ViewDecl("loop")`.
* `cm_loop`(공통 모드 루프 `pm_cm_ss_deg`, 사용자 결정 2026-10-08): **출력 포트 CM 주입** -- 차동 출력 포트 쌍(role `ROLE_DIFFERENTIAL_OUTPUT_P`/`_N`)이
  선언돼 있으면 `ViewDecl("cm_output", weights=((p, 1/2), (n, 1/2)))`(두 출력 넷에 동일 부호 Middlebrook 전압·전류 주입, 입력은 전부 교류접지). 절단
  원소(출력 넷의 소비자 쪽 단자)는 metrics 가 소신호 회로에서 구조로 정한다 -- CM 감지가 평균 저항이든 DDA 든 buffer 든 보지 않는다(이름·구조 리터럴
  없음). 차동 출력쌍이 없으면 `view_required` 사유; 스위치드 커패시터 선언(수동소자·이상원 kind ∈ `SWITCHED_KINDS`)이 있으면 명시적 정지 사유.
* `sense`(출력 포트 뷰 기본, 3.1): 출력 포트가 정확히 1개면 그 넷 single_ended, 아니면 `view_required` 사유.
* `fixed_nets`: 감지 노드로 쓸 수 없는 고정 넷 = 레일 ∪ 입력 포트 넷 ∪ gate 전용 미구동 넷(레일·입력 포트가 아니고 단자가
  전부 MOS gate -- graph `ac_ground_class` gate_only_undriven 과 같은 정의, authoring 은 graph 를 import 하지 않아 TopologyDoc
  에서 같은 판정을 한다).
"""
import dataclasses

from ._feedback_cuts import input_terminal_nets
from ._terminal_nets import two_terminal_nets
from .ports import (INPUT_DIRECTION, OUTPUT_DIRECTION, ROLE_DIFFERENTIAL_INPUT_N, ROLE_DIFFERENTIAL_INPUT_P,
                    ROLE_DIFFERENTIAL_OUTPUT_N, ROLE_DIFFERENTIAL_OUTPUT_P, ROLE_SINGLE_ENDED_INPUT)
from .spec_model import PendingMark, SenseDecl, ViewDecl

SENSE_DIFFERENTIAL = "differential"
SENSE_SINGLE_ENDED = "single_ended"
SENSE_MODES = (SENSE_DIFFERENTIAL, SENSE_SINGLE_ENDED)
BETA_DECLARED = "declared"
BETA_UNITY = "unity"
CM_OUTPUT_MODE = "cm_output"           # ViewDecl.mode: 출력 포트 쌍 동일 부호(공통 모드) Middlebrook 주입 루프


@dataclasses.dataclass(frozen=True)
class DefaultViews:
    """`port`·`loop`·`sense`: 기본 `ViewDecl` 또는 `view_required` 사유 문자열. `fixed_nets`: 감지 금지 넷 frozenset."""

    port: object
    loop: object
    sense: object
    fixed_nets: frozenset
    cm_loop: object = None


def _role_weights(inputs):
    differential = [p for p in inputs if p.role in (ROLE_DIFFERENTIAL_INPUT_P, ROLE_DIFFERENTIAL_INPUT_N)]
    weights = {}
    for p in inputs:
        if p.role == ROLE_DIFFERENTIAL_INPUT_P:
            weights[p.net] = 1.0 / len(differential)
        elif p.role == ROLE_DIFFERENTIAL_INPUT_N:
            weights[p.net] = -1.0 / len(differential)
        elif p.role == ROLE_SINGLE_ENDED_INPUT:
            weights[p.net] = 1.0
    return weights


def _port_view(inputs, outputs, weights):
    roles = sorted(p.role for p in inputs)
    if roles not in (sorted((ROLE_DIFFERENTIAL_INPUT_P, ROLE_DIFFERENTIAL_INPUT_N)), [ROLE_SINGLE_ENDED_INPUT]):
        return ("입력 포트가 차동쌍 1개(role " + ROLE_DIFFERENTIAL_INPUT_P + "/" + ROLE_DIFFERENTIAL_INPUT_N
                + ") 또는 단일 입력 1개(role " + ROLE_SINGLE_ENDED_INPUT + ")가 아니라 기본 포트 뷰의 여기가 정해지지 "
                "않는다: " + repr(roles))
    by_role = {p.role: p.net for p in outputs}
    if len(outputs) == 1:
        sense = SenseDecl(outputs[0].net, None, SENSE_SINGLE_ENDED)
    elif len(by_role) == len(outputs) and sorted(by_role) == sorted((ROLE_DIFFERENTIAL_OUTPUT_P,
                                                                     ROLE_DIFFERENTIAL_OUTPUT_N)):
        sense = SenseDecl(by_role[ROLE_DIFFERENTIAL_OUTPUT_P], by_role[ROLE_DIFFERENTIAL_OUTPUT_N], SENSE_DIFFERENTIAL)
    else:
        return ("출력 포트가 1개 또는 차동 출력쌍(role " + ROLE_DIFFERENTIAL_OUTPUT_P + "/" + ROLE_DIFFERENTIAL_OUTPUT_N
                + ")이 아니라 기본 포트 뷰의 관측이 정해지지 않는다: " + repr(sorted(p.net for p in outputs)))
    return ViewDecl("port", weights=tuple(sorted((p.net, weights[p.net]) for p in inputs)), sense=sense)


def _loop_view(feedback, port, weights, topology):
    if feedback is None:
        return ViewDecl("loop")
    if isinstance(feedback, PendingMark):
        return ViewDecl("pending", decision=feedback.decision)
    if not feedback:
        if isinstance(port, str):
            return "β = 1(feedback 빈 list) 루프 뷰는 포트 뷰와 같다 -- " + port
        return ViewDecl("loop", beta=BETA_UNITY, weights=port.weights, sense=port.sense)
    cuts = []
    for name in feedback:
        nets = input_terminal_nets(name, topology)
        if nets is None or len(nets) != 1:
            return ViewDecl("loop")
        cuts.append((name, nets[0]))
    cut_nets = sorted({net for _, net in cuts})
    missing = [net for net in cut_nets if net not in weights]
    if missing:
        return ("절단 넷 " + repr(missing) + " 의 입력 포트 role 이 가중 어휘(" + ROLE_DIFFERENTIAL_INPUT_P + ", "
                + ROLE_DIFFERENTIAL_INPUT_N + ", " + ROLE_SINGLE_ENDED_INPUT + ") 밖이라 루프 가중이 정해지지 않는다")
    return ViewDecl("loop", beta=BETA_DECLARED, cuts=tuple(cuts), weights=tuple((net, weights[net]) for net in cut_nets))


SWITCHED_KINDS = ("switch", "clock")          # 스위치드 커패시터(이산시간) 선언 어휘 -- 수동소자·이상원 kind 로 선언된 것


def _cm_loop_view(topology, outputs):
    """출력 포트 CM 주입 루프 뷰 또는 `view_required` 사유(모듈 docstring `cm_loop`). 감지 구조(평균 방식)는 보지 않는다."""
    by_role = {p.role: p.net for p in outputs}
    if sorted(by_role) != sorted((ROLE_DIFFERENTIAL_OUTPUT_P, ROLE_DIFFERENTIAL_OUTPUT_N)) or len(by_role) != len(outputs):
        return ("차동 출력쌍(role " + ROLE_DIFFERENTIAL_OUTPUT_P + "/" + ROLE_DIFFERENTIAL_OUTPUT_N
                + ")이 없는 회로라 공통 모드 루프 뷰가 정해지지 않는다")
    switched = sorted(e.name for e in topology.passives + topology.sources if e.kind in SWITCHED_KINDS)
    if switched:
        return ("스위치드 커패시터(이산시간) CMFB 는 지원하지 않는다 -- 선언된 스위치·클록 원소 " + repr(switched)
                + " (연속시간 소신호 MNA 로 표현할 수 없다, 명시적 정지)")
    pair = sorted(by_role.values())
    return ViewDecl(CM_OUTPUT_MODE, weights=tuple((net, 1.0 / len(pair)) for net in pair))


def _gate_only_nets(topology, input_nets):
    driven = two_terminal_nets(topology.passives + topology.sources)
    for d in topology.devices:
        driven |= {d.d, d.s} | ({d.bulk} if d.bulk is not None else set())
    gates = {d.g for d in topology.devices}
    return frozenset(net for net in gates - driven if net not in topology.rails and net not in input_nets)


def default_views(topology, feedback):
    inputs = [p for p in topology.ports if p.direction == INPUT_DIRECTION]
    outputs = [p for p in topology.ports if p.direction == OUTPUT_DIRECTION]
    weights = _role_weights(inputs)
    port = _port_view(inputs, outputs, weights)
    if len(outputs) == 1:
        sense = ViewDecl("sense", sense=SenseDecl(outputs[0].net, None, SENSE_SINGLE_ENDED))
    else:
        sense = ("output 포트가 하나가 아니라 출력 포트 뷰의 감지 넷이 정해지지 않는다 -- view(sense_p·sense_n·sense_mode)를 "
                 "선언한다: " + repr(sorted(p.net for p in outputs)))
    input_nets = frozenset(p.net for p in inputs)
    fixed = frozenset(topology.rails) | input_nets | _gate_only_nets(topology, input_nets)
    return DefaultViews(port, _loop_view(feedback, port, weights, topology), sense, fixed,
                        _cm_loop_view(topology, outputs))
