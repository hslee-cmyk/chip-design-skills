"""기모드 여기의 자기대응 넷(대칭 가상접지) (설계 41 §1.2 '움직이지 않으면', 계획 N3.2-1 (4) '뷰별 판정').

진입점: `virtual_ground(model, excite) -> frozenset`.

여기가 정확히 두 넷이고 가중 합이 0(기모드)일 때, 두 여기 넷을 맞바꾸는 회로 자기동형 σ 가 있으면 σ 의 고정 넷은 이 뷰의 신호가 0 이다
(대칭 축약에서 자기대응 넷 = 가상접지). σ 는 맞짝 전파로 정한다:
* 시작: σ(p) = n, σ(n) = p, 레일·정적 교류접지 넷은 고정.
* 반복: 같은 종류·같은 단자 수의 원소 e1 중 단자 하나라도 σ 가 이미 정해진 것에 대해, σ 와 모순 없는 후보 원소(자기 자신 포함)가
  **정확히 하나**면 e1 ↔ 후보로 확정하고 아직 정해지지 않은 단자 넷을 짝짓는다(같은 넷이면 고정). 후보가 여럿이면 그 시점에는 건너뛴다.
  MOS 는 (d, g, s) 순서를 지키고, 수동소자는 두 단자의 순서를 보지 않는다(무향, 40 §6).
* 모든 원소가 짝을 얻어야 σ 가 회로 전체의 자기동형이다. 아니면(비대칭 회로·애매함) 빈 집합 -- 가상접지를 주장하지 않는다.
결과는 σ 의 고정 넷에서 레일·정적 교류접지를 뺀 집합이다. 이 파일은 U2 정준 라벨링·궤도(40 §6)가 들어오면 그 궤도로 대체된다.
"""
import typing

from .s1v_values import PAIR


class _Element(typing.NamedTuple):
    index: int
    kind: str
    terms: tuple
    unordered: bool


def _elements(model):
    out = [(m.kind, (m.d, m.g, m.s), False) for m in model.mos]
    out.extend((p.kind, (p.a, p.b), True) for p in model.passives)
    out.extend((s.kind, (s.a, s.b), False) for s in model.sources)
    return [_Element(i, *e) for i, e in enumerate(out)]


def _set_pair(partner, a, b):
    if partner.get(a, b) != b or partner.get(b, a) != a:
        return False
    partner[a] = b
    partner[b] = a
    return True


def _consistent(partner, terms1, terms2):
    for t1, t2 in zip(terms1, terms2):
        if t1 in partner:
            if partner[t1] != t2:
                return False
        elif t2 in partner:
            return False
    return True


def _orderings(element):
    return (element.terms, tuple(reversed(element.terms))) if element.unordered else (element.terms,)


def _candidates(partner, elements, matched, e1):
    options = []
    for e2 in elements:
        if e2.kind != e1.kind or len(e2.terms) != len(e1.terms) or e2.unordered != e1.unordered:
            continue
        if e2.index in matched and e2.index != e1.index:
            continue
        for order in _orderings(e2):
            if _consistent(partner, e1.terms, order):
                options.append((e2, order))
                break
    return options


def virtual_ground(model, excite):
    if len(excite) != len(PAIR) or sum(w for _, w in excite) != 0:
        return frozenset()
    partner = {net: net for net in model.static_ground | model.rails}
    (p, _), (n, _) = excite
    if not _set_pair(partner, p, n):
        return frozenset()
    elements = _elements(model)
    matched = {}
    changed = True
    while changed:
        changed = False
        for e1 in elements:
            if e1.index in matched or not any(t in partner for t in e1.terms):
                continue
            options = _candidates(partner, elements, matched, e1)
            if len(options) != 1:
                continue
            e2, order = options[0]
            if not all(t1 in partner or _set_pair(partner, t1, t2) for t1, t2 in zip(e1.terms, order)):
                return frozenset()
            matched[e1.index] = e2.index
            matched[e2.index] = e1.index
            changed = True
    if len(matched) != len(elements):
        return frozenset()
    return frozenset(net for net, other in partner.items() if net == other) - model.static_ground - model.rails
