"""원소 단위 KCL 해 공간 -- θ 전류 기저와 모든 DC 원소 전류의 선형식 (계획 DEC-70 전류 변수 정의, DEC-08, 설계 3.2 ②).

진입점: `dc_current_basis`(`@compute_block`) -- `dc_current_basis(snapshot, declared_sources)`.

* 미지수 = DC 원소(S1 `device.dc_nets` 가 있는 MOS·저항·이상원, 잎 가지치기된 저항 제외) 전류. 양의 방향 = nmos d->s,
  pmos s->d(전도 방향), 2단자 t0->t1(이상 전류원은 SPICE 규약: t0 에서 source 를 지나 t1 로).
* 방정식 = 레일이 아닌 넷마다 KCL(나가는 전류 합 − 들어오는 전류 합 = 0). 값이 선언된 이상 전류원은 고정값(DEC-08).
* 유리수(Fraction) 기약 행사다리꼴로 푼다(부동소수 허용오차 상수 없음). 열 순서 = 원소 이름순(결정론 tie-break);
  pivot 이 아닌 열 = θ 전류 성분(독립 기저), pivot 열 = 기저와 고정값의 선형식.
* `matching_ratio` 관계는 비율 값 선언이 어디에도 없어(S1·spec) 전류를 강제하지 않는다 -- 미러 출력 전류도 기저에 든다.
* 정지/실패: 고정값끼리 KCL 이 어긋남 -> `InfeasibleTargetError`(reason `declared_source_kcl_conflict`). KCL 상 전류가
  항상 0 인 MOS -> `StructureUnresolvedError`(rule_branch `mos_zero_current_structural`) -- 전도 소자로 사이징할 수 없다.
"""
from fractions import Fraction

from gmid_engine.core import InfeasibleTargetError, StructureUnresolvedError, compute_block
from gmid_engine.graph import (
    ELEMENT_MOS,
    ELEMENT_PASSIVE,
    ELEMENT_SOURCE,
    GRAPH_KEY,
    MOS_TERMINAL_NAMES,
    UNSUPPORTED_RULE_BRANCH,
)

from .s2_values import (
    BRANCH_MOS_ZERO_CURRENT,
    CURRENT_SOURCE,
    DC_CURRENT_BASIS_WRITER,
    DC_KEY,
    REASON_DECLARED_KCL,
    CurrentBasis,
    CurrentTerm,
)

READS = (
    ("device", "dc_nets"), ("device", "element_class"), ("device", "kind"), ("device", "pins"),
    ("node", "is_rail"), ("graph", "dc_pruned"),
)
WRITES = (("graph", "dc_current_basis"),)
_PMOS = "pmos"


def _ends(name, element_class, kind, pins):
    pins = dict(pins)
    if element_class == ELEMENT_MOS:
        drain, _gate, source = (pins[t] for t in MOS_TERMINAL_NAMES)
        return (source, drain) if kind == _PMOS else (drain, source)
    first, second = (net for _term, net in sorted(pins.items()))
    return first, second


def _rref(rows, n_cols):
    """rows: list[list[Fraction]] (앞 n_cols 열 소거, 뒤 열은 같이 변환). 반환 (rows, pivots)."""
    pivots = []
    r = 0
    for c in range(n_cols):
        pivot = next((i for i in range(r, len(rows)) if rows[i][c] != 0), None)
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        lead = rows[r][c]
        rows[r] = [x / lead for x in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][c] != 0:
                factor = rows[i][c]
                rows[i] = [a - factor * b for a, b in zip(rows[i], rows[r])]
        pivots.append(c)
        r += 1
    return rows, pivots


@compute_block(DC_CURRENT_BASIS_WRITER, reads=READS, writes=WRITES)
def dc_current_basis(projection):
    (declared,) = projection.extras
    declared = {name: value for name, value in declared if value is not None}
    pruned = tuple(sorted({element for element, _round in projection.value("graph", GRAPH_KEY, "dc_pruned")}))
    classes = dict(projection.column("device", "element_class"))
    kinds = dict(projection.column("device", "kind"))
    pins = dict(projection.column("device", "pins"))
    rails = {net for net, is_rail in projection.column("node", "is_rail") if is_rail}
    elements = tuple(name for name, nets in projection.column("device", "dc_nets")
                     if nets is not None and name not in pruned)
    ends = tuple((name,) + _ends(name, classes[name], kinds[name], pins[name]) for name in elements)
    fixed = tuple((name, float(declared[name])) for name in elements
                  if classes[name] == ELEMENT_SOURCE and kinds[name] == CURRENT_SOURCE and name in declared)
    fixed_names = tuple(name for name, _v in fixed)
    unknown = tuple(name for name in elements if name not in fixed_names)
    nets = sorted({net for _e, a, b in ends for net in (a, b)} - rails)
    col = {name: i for i, name in enumerate(unknown + fixed_names)}
    rows = []
    for net in nets:
        row = [Fraction(0)] * len(col)
        for name, a, b in ends:
            if a == net:
                row[col[name]] += 1
            if b == net:
                row[col[name]] -= 1
        rows.append(row)
    rows, pivots = _rref(rows, len(unknown))
    fixed_values = [Fraction(v) for _n, v in fixed]
    for row in rows[len(pivots):]:
        residual = sum(c * v for c, v in zip(row[len(unknown):], fixed_values))
        if residual != 0:
            raise InfeasibleTargetError(devices=fixed_names, detail={"reason": REASON_DECLARED_KCL,
                                                                     "residual_a": float(residual)})
    free = tuple(unknown[c] for c in range(len(unknown)) if c not in pivots)
    terms = {name: (CurrentTerm(name, 1, 1),) for name in free}
    terms.update({name: (CurrentTerm(name, 1, 1),) for name in fixed_names})
    for i, c in enumerate(pivots):
        row = rows[i]
        out = []
        for j, name in enumerate(unknown + fixed_names):
            if j == c or row[j] == 0:
                continue
            coeff = -row[j]
            out.append(CurrentTerm(name, coeff.numerator, coeff.denominator))
        terms[unknown[c]] = tuple(out)
    mos = tuple(name for name in elements if classes[name] == ELEMENT_MOS)
    dead = tuple(name for name in mos if not terms[name])
    if dead:
        raise StructureUnresolvedError(devices=dead, detail={"reason": UNSUPPORTED_RULE_BRANCH,
                                                             "rule_branch": BRANCH_MOS_ZERO_CURRENT})
    resistors = tuple(name for name in elements if classes[name] == ELEMENT_PASSIVE)
    basis = CurrentBasis(ends, mos, free, fixed, tuple((name, terms[name]) for name in elements), pruned, resistors)
    return {("graph", "dc_current_basis"): {DC_KEY: basis}}
