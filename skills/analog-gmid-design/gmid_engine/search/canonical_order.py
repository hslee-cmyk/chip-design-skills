"""θ 변수의 이름 없는 정준 순서 (사용자 대원칙 'topology 에 종속된 엔진 금지', CONTRACT 3.23).

진입점: `canonical_order(sctx, variables) -> (정렬된 변수 tuple, 변수별 차원 index list, 차원 수)`.

* 정렬 키 = (L 인가, 성분 종류, 키 궤도 id), 이름은 같은 키 안에서만 tie-break. 키 궤도 id = graph 대칭 블록 필드 `graph/s1: orbits`(정준 라벨링의 자기동형
  궤도, 이름을 읽지 않음)의 원소 궤도; `y` 성분의 키가 넷이면 넷 궤도, 둘 다 아니면 -1. 묶이지 않은 변수끼리는 키가
  유일하다(묶음은 `orbit_ties` 가 먼저 한 변수로 합친다) -- 같은 키가 남는 건 spec 이 묶음을 푼 궤도(`untie_orbits`)뿐. L 은 칸이 정해진 뒤 붙는 변수라 맨 뒤.
* 차원 = 서로 다른 (성분 종류, 구조 색) 키의 순위(L 키는 맨 뒤). 같은 키의 변수(자기동형 궤도 후보)는 같은 차원이다.
* 이름 전단사·원소 순서 섞기에 대해 키·차원은 불변이다. 같은 키 안 변수의 상대 순서만 이름을 따른다(결정론 유지) -- 그 순서가 만드는
  차이는 부동소수 잡음 수준이다(CONTRACT 3.23).
"""
from gmid_engine.graph import GRAPH_KEY
from gmid_engine.sizing import THETA_L


def _key(colours, var):
    kind, element = var.component
    devices, nodes = colours
    c = devices.get(element)
    if c is None:
        c = nodes.get(element, -1)
    return (kind == THETA_L, kind, c)


def canonical_order(sctx, variables):
    base = sctx.dc.base
    orbits = base.value("graph", GRAPH_KEY, "orbits")
    colours = (dict(orbits.devices), dict(orbits.nodes))
    tie = {**dict(base.column("node", "dc_colour")), **dict(base.column("device", "dc_colour"))}      # 같은 키(묶음을 푼 궤도) 안은 유일한 구조 색
    ordered = tuple(sorted(variables, key=lambda v: (_key(colours, v), tie.get(v.component[1], -1), v.component[1])))
    keys = [_key(colours, v) for v in ordered]
    rank = {k: i for i, k in enumerate(sorted(set(keys)))}
    return ordered, [rank[k] for k in keys], len(rank)
