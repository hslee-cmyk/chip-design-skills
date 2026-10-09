"""주극점 노드를 구조로 판정 (설계 41 §6.3, D-DN, 계획 N3 -- 매크로 모델을 쓰지 않는다).

진입점: `dominant_node(view) -> DominantNode`  (`view` = gain 제약 전달 뷰 `graph.ViewS1v`).

* **Miller (2) 루프가 있으면**: 그 루프의 노드 중 극점 노드이고 블록에 속한 후보 가운데 앞 노드(블록 stage 가 작은 쪽, 같으면 수동소자 포함 BFS 거리 `dist` 가 작은 쪽)가
  주극점 노드다 -- Miller 증배가 걸리는 노드이기 때문이다. 루프가 여럿이면 블록 순서상 가장 앞 블록의 출력노드인 것을 쓴다(stage 가 같은 노드는 모두 낸다 --
  차동 쌍처럼 이름이 아니라 구조로는 가를 수 없는 동률을 이름으로 깨지 않는다).
* **Miller 루프가 없으면**: 전달 뷰의 감지(출력 포트) 넷 중 극점 노드 후보를 모두 낸다 -- 부하가 걸리는 노드다.
* **후보** = 블록 소속 극점 노드 중 임피던스 등급이 '낮음'이 아닌 것. 설계 문구는 "'높음'이 아닌 노드를 뺀다"이지만 U1 의 등급은 high·low·value_dependent 셋이고,
  Miller 앞 노드(예: 미러 부하 출력)는 value_dependent 로 나온다. 그 노드를 빼면 Miller 루프의 주극점이 사라지므로 value_dependent 를 후보에 둔다(설계 공백으로 보고).
* 출력 포트가 후보가 아니면(낮은 임피던스 버퍼 출력) 버퍼 앞 마지막 이득 블록의 높은 임피던스 출력노드가 주극점 노드다(`RULE_LAST_GAIN_BLOCK` -- 설계 41 §6.3 에 없는 경우, 설계 공백으로 보고).
* 후보가 없으면 `nets` 가 빈 tuple 이고 `rule` = `RULE_NONE`.
"""
import dataclasses

_LOOP_MILLER = "miller"       # graph/s1v_values.py LOOP_MILLER (graph 공개 API 가 이 상수를 내보내지 않아 같은 문자열을 둔다)
_IMPEDANCE_LOW = "low"        # graph/s1v_values.py IMP_LOW
_IMPEDANCE_HIGH = "high"      # graph/s1v_values.py IMP_HIGH
_BLOCK_GAIN = "gain"          # graph/s1v_values.py BLOCK_GAIN
RULE_MILLER_FRONT = "miller_front_node"
RULE_OUTPUT_PORT = "output_port_node"
RULE_LAST_GAIN_BLOCK = "last_gain_block_node"
RULE_NONE = "none"


@dataclasses.dataclass(frozen=True)
class DominantNode:
    """`nets` = 주극점 노드 넷 tuple(구조 동률이면 여럿), `rule` = RULE_*."""

    nets: tuple
    rule: str


def dominant_node(view):
    stage = {b.key: b.stage for b in view.blocks}
    dist = dict(view.dist)
    candidates = {p.net: stage[p.block] for p in view.pole_nodes if p.block and p.block in stage and p.impedance != _IMPEDANCE_LOW}
    fronts = []
    for loop in view.loops:
        if _LOOP_MILLER not in loop.classes:
            continue
        rows = sorted((candidates[n], dist.get(n, 0), n) for n in loop.nodes if n in candidates)
        if rows:
            key = rows[0][:2]
            fronts.append((key, tuple(n for s, d, n in rows if (s, d) == key)))
    if fronts:
        best = min(f[0] for f in fronts)
        return DominantNode(tuple(sorted({n for f in fronts if f[0] == best for n in f[1]})), RULE_MILLER_FRONT)
    ports = tuple(n for n in view.sense if n in candidates)
    if ports:
        return DominantNode(tuple(sorted(ports)), RULE_OUTPUT_PORT)
    # 출력 포트가 후보가 아니다(낮은 임피던스 버퍼 출력 -- 팔로어가 부하를 구동): 부하가 걸리는 노드는 버퍼 앞 마지막 이득 블록의 출력노드다.
    gain_stages = [stage[p.block] for p in view.pole_nodes if p.net in candidates and p.impedance == _IMPEDANCE_HIGH and _is_gain(view, p.block)]
    if gain_stages:
        last = max(gain_stages)
        return DominantNode(tuple(sorted(p.net for p in view.pole_nodes if p.net in candidates and p.impedance == _IMPEDANCE_HIGH
                                         and stage[p.block] == last and _is_gain(view, p.block))), RULE_LAST_GAIN_BLOCK)
    return DominantNode((), RULE_NONE)


def _is_gain(view, block_key):
    return any(b.key == block_key and b.kind == _BLOCK_GAIN for b in view.blocks)
