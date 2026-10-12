"""대칭 블록 -- S1 하나에서 구조 색·자기동형 궤도·전류 부호를 정한다 (설계 40 §6, §2.4.1 '대칭 탐색'·§2.4.8 `graph/s1: orbits, current_symmetry`,
사용자 결정 2026-10-08 '정준 라벨링 + 대칭 변수 묶음'·'대칭 묶음 방식: b', 2026-10-12 "6. 가"·D-1~D-3).

진입점: `s1_symmetry`(`@compute_block`) -- `s1_symmetry(snapshot, supplies, marks)`. θ 무관(S0 당 1회). `build_s1` 이 부르고, sizing 커널 컨텍스트는 같은 블록을
같은 입력으로 다시 불러 재사용한다(계산 0 -- 선언 표시가 다를 때만 그 입력으로 계산한다).

* extras: `supplies` = `supplies_declaration` 이 정규화한 ((레일, V), ...) 또는 None, `marks` = `SymmetryMarks`(사람 선언 표시).
* 선언 표시(자기동형이 보존해야 하는 값): 노드 = 레일 전위(`rail_v`, supplies), 노드 목표(`target_v`), 입력 포트 공통 DC(`input_dc_v`), 원소 = `marks.elements`
  (값 선언·engine·선형 영역). `canonical_form` 의 처음 색에 들어간다.
* 계산: `canonical_form`(선언 표시를 넣은 그래프 하나 -- `wl`·정준 위치·자기동형 생성자, D-2) -> `automorphism_orbits`.
* writes
  - `device.dc_colour`·`node.dc_colour` = (`wl`, 정준 위치) 쌍의 정렬 순위 -- 서로 다른 1-WL 색 사이의 순서는 `wl`, 같은 색 안은 정준 위치(정점마다 유일, 이름 무관).
  - `graph.orbits` = `Orbits`(원소·넷 궤도 id = 구성원 정준 위치 최솟값).
  - `graph.current_symmetry` = `CurrentSigns` -- 생성자마다 (원소, 상, 부호). 부호 −1(`reverses_orientation`) = MOS 의 drain 이 상 MOS 의 drain 으로 가지 않음(d/s 맞바꿈),
    방향 없는 2단자 수동소자의 첫 단자(단자 이름 순서 첫 단자) 넷이 상의 첫 단자 넷으로 가지 않음. 방향 있는 이상원은 +1.
* **정지**(40 §6-8 '자기 맞바꿈 = 구조적 0 전류'): 군의 어떤 원소가 **전도 MOS**(DC 전도 그래프에서 가지치기되지 않은 MOS) 하나를 자기 자신으로 보내며 d/s 를
  맞바꾸면 그 소자 전류는 I = −I 로 구조적 0 이고 gm/ID·VGS 역산이 정의되지 않는다(ID > 0 전제, 봉인 7). 이 분기의 계산 규칙은 만들지 않고(DEC-76) core
  `StructureUnresolvedError`(reason `unsupported_rule_branch`, rule_branch `ds_self_swap_zero_current`, devices = 그 소자, detail generators = 그 소자의 부호 궤도에
  닿는 생성자)로 탐색 전에 멈춘다. 판정은 생성자 하나가 아니라 군 전체에서 한다: (원소, 방향) 쌍의 궤도를 생성자로 union-find 하고 (e, +)·(e, −) 가 같은 궤도면
  자기 맞바꿈이다.
"""
from gmid_engine.authoring import INPUT_DIRECTION
from gmid_engine.core import StructureUnresolvedError, compute_block

from .automorphism_orbits import automorphism_orbits
from .canonical_form import canonical_form
from .s1_values import (
    BRANCH_DS_SELF_SWAP,
    ELEMENT_MOS,
    ELEMENT_PASSIVE,
    GRAPH_KEY,
    MOS_DRAIN,
    S1_SYMMETRY_WRITER,
    SYMMETRY_READS,
    SYMMETRY_WRITES,
    UNSUPPORTED_RULE_BRANCH,
    CurrentSigns,
    Orbits,
)

_NODE, _ELEMENT = ("n", "e")


def _pack(table):
    return tuple((n, tuple(sorted(marks))) for n, marks in sorted(table.items()))


def _node_marks(projection, supplies, marks):
    nodes = {}
    for net, volts in () if supplies is None else supplies:
        nodes.setdefault(net, []).append(("rail_v", float(volts)))
    for net, volts in marks.targets:
        nodes.setdefault(net, []).append(("target_v", float(volts)))
    if marks.input_dc_v is not None:
        for net, direction in projection.column("node", "port_direction"):
            if direction == INPUT_DIRECTION:
                nodes.setdefault(net, []).append(("input_dc_v", float(marks.input_dc_v)))
    return _pack(nodes)


def _rank(signature):
    order = {s: i for i, s in enumerate(sorted(set(signature.values())))}
    return {v: order[s] for v, s in signature.items()}


def _signs(classes, pins, generators):
    """생성자마다 ((원소, 상, 부호), ...) -- 움직이거나 방향을 뒤집는 원소만."""
    out = []
    for generator in generators:
        emap = {v[1]: image[1] for v, image in generator if v[0] == _ELEMENT}
        nmap = {v[1]: image[1] for v, image in generator if v[0] == _NODE}
        rows = []
        for element in sorted(classes):
            image = emap.get(element, element)
            terminals = pins[element]
            if classes[element] == ELEMENT_MOS:
                anchor, target = terminals[MOS_DRAIN], pins[image][MOS_DRAIN]
            elif classes[element] == ELEMENT_PASSIVE:
                anchor, target = terminals[min(terminals)], pins[image][min(pins[image])]
            else:
                anchor = target = None
            sign = -1 if anchor is not None and nmap.get(anchor, anchor) != target else 1
            if image != element or sign == -1:
                rows.append((element, image, sign))
        out.append(tuple(rows))
    return tuple(out)


def _self_swaps(conducting, signs):
    """전도 MOS 중 군의 어떤 원소가 자기 자신으로 보내며 d/s 를 맞바꾸는 것 -> ((소자, (생성자 번호, ...)), ...)."""
    parent = {}

    def find(v):
        parent.setdefault(v, v)
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for rows in signs:
        for element, image, sign in rows:
            union((element, 1), (image, sign))
            union((element, -1), (image, -sign))
    swapped = [name for name in conducting if find((name, 1)) == find((name, -1))]
    touched = []
    for name in swapped:
        root = find((name, 1))
        touched.append((name, tuple(i for i, rows in enumerate(signs) if any(find((e, 1)) == root for e, _i, _s in rows))))
    return tuple(touched)


@compute_block(S1_SYMMETRY_WRITER, reads=SYMMETRY_READS, writes=SYMMETRY_WRITES)
def s1_symmetry(projection):
    supplies, marks = projection.extras
    canon = canonical_form(projection, marks.elements, _node_marks(projection, supplies, marks))   # 그래프 하나(D-2)
    orbit = automorphism_orbits(canon)
    colour = _rank({v: (canon.wl[v], canon.position[v]) for v in canon.wl})
    classes = dict(projection.column("device", "element_class"))
    pins = {name: dict(p) for name, p in projection.column("device", "pins")}
    signs = _signs(classes, pins, canon.generators)
    pruned = {e for e, _round in projection.value("graph", GRAPH_KEY, "dc_pruned")}
    conducting = tuple(name for name in sorted(classes) if classes[name] == ELEMENT_MOS and name not in pruned)
    swaps = _self_swaps(conducting, signs)
    if swaps:
        raise StructureUnresolvedError(
            devices=tuple(name for name, _g in swaps),
            detail={"reason": UNSUPPORTED_RULE_BRANCH, "rule_branch": BRANCH_DS_SELF_SWAP,
                    "generators": tuple((name, tuple(signs[i] for i in idx)) for name, idx in swaps)})
    return {
        ("node", "dc_colour"): {key: c for (tag, key), c in colour.items() if tag == _NODE},
        ("device", "dc_colour"): {key: c for (tag, key), c in colour.items() if tag == _ELEMENT},
        ("graph", "orbits"): {GRAPH_KEY: Orbits(tuple(sorted((k, o) for (t, k), o in orbit.items() if t == _ELEMENT)),
                                                tuple(sorted((k, o) for (t, k), o in orbit.items() if t == _NODE)))},
        ("graph", "current_symmetry"): {GRAPH_KEY: CurrentSigns(signs)},
    }
