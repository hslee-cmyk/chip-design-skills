"""θ 전류 성분의 대칭 관계 -- 자기동형이 만드는 부호 묶음과 구조적 0 (사용자 결정 2026-10-08 '대칭 묶음 방식: b', search CONTRACT 3.24).

진입점: `current_symmetry(dc_ctx, untied) -> CurrentSymmetry(ties, negated, zeros)`.

* 입력: sizing 의 전류 기저 `graph.dc_current_basis`(원소 전류 = 독립 θ 전류와 선언 전류원의 선형식 `rows`)와 정준형이 쓴 자기동형 생성자
  `graph.dc_symmetry`(움직인 정점만, sizing `dc_struct_colour`), 원소 구조 색 `device.dc_colour`·궤도 `device.dc_orbit`.
* 대칭 동작점의 전류는 군 불변이다: 생성자 γ 마다 모든 DC 원소 e 에 `I(γ e) = σ_γ(e) · I(e)`. σ = −1 은 방향 없는 2단자 수동소자(저항 등)의 앞 끝
  (단자 이름 순서 첫 단자의 넷, `current_basis._ends`)이 γ 아래 앞 끝으로 대응하지 않을 때(자기동형이 단자 순서를 뒤집음), 그 밖(MOS, 방향 있는 이상원)은 +1.
  `I(x)` 는 독립 θ 전류의 선형식이라 이 식들은 독립 θ 전류에 대한 선형 연립이다. 구조 색이 큰 쪽이 먼저 소거되도록 기약 행사다리꼴(유리수)을 만든다.
* 연립의 행 중 **독립 θ 전류 하나에 대한 `x_p = ±x_q` (q 는 소거되지 않는 변수)** 는 부호 묶음(대표 q = 구조 색 작은 쪽), **`x_p = 0`** 은 구조적 0(대칭 점에서
  이 가지 전류는 KCL·대칭이 0 으로 정한다 -- 예: 파일럿의 CMFB 감지 저항 R1/R2 는 Voc 가 게이트만 구동해 직렬이므로 I = 0)이다. 그 밖(항이 둘 이상이거나 상수가
  남는 행)은 묶지 않는다(탐색 공간이 넓어질 뿐 정확하다). 구조적 0 은 θ 전류 성분을 값 0 으로 고정한다(탐색 변수가 아니다).
* `untied` = spec `search.untie_orbits` 원소 이름: 그 원소의 궤도에 속한 원소가 소거 변수이거나 대표인 관계는 받지 않는다(연립은 그대로 풀되 결과 관계를 거른다 -- 다른 원소의
  대칭이 KCL 로 만드는 관계도 그 궤도 변수에는 걸지 않는다). 원소가 없으면 `SchemaRejectedError`(gate `search_domain`, reason
  `untie_element_unknown`), 궤도가 그 원소 하나뿐이면 `untie_orbit_trivial`.
* 반환: `ties` = ((대표 성분, (묶인 성분, ...)), ...)(성분 = ("current", 원소)), `negated` = 부호 −1 로 묶인 성분 tuple, `zeros` = 구조적 0 성분 tuple.
  이름을 읽지 않는다(원소 이름은 키로만 쓰이고 순서는 구조 색).
"""
import dataclasses
from fractions import Fraction

from gmid_engine.core import SchemaRejectedError
from gmid_engine.graph import ELEMENT_PASSIVE
from gmid_engine.sizing import DC_KEY, THETA_CURRENT

_ELEMENT = "e"
_NODE = "n"


@dataclasses.dataclass(frozen=True)
class CurrentSymmetry:
    ties: tuple
    negated: tuple
    zeros: tuple


def _reject(reason, element):
    raise SchemaRejectedError(detail={"gate": "search_domain", "reason": reason, "element": element})


def _free_orbits(base, untied):
    orbit = dict(base.column("device", "dc_orbit"))
    size = {}
    for o in orbit.values():
        size[o] = size.get(o, 0) + 1
    free = set()
    for name in untied:
        if name not in orbit:
            _reject("untie_element_unknown", name)
        if size[orbit[name]] == 1:
            _reject("untie_orbit_trivial", name)
        free.add(orbit[name])
    return orbit, free


def _reduce(rows, width):
    """rows: list[list[Fraction]](앞 width 열이 변수, 마지막 열이 상수). 기약 행사다리꼴 -> (rows, pivots)."""
    pivots = []
    r = 0
    for c in range(width):
        pick = next((i for i in range(r, len(rows)) if rows[i][c] != 0), None)
        if pick is None:
            continue
        rows[r], rows[pick] = rows[pick], rows[r]
        scale = rows[r][c]
        rows[r] = [v / scale for v in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][c] != 0:
                factor = rows[i][c]
                rows[i] = [a - factor * b for a, b in zip(rows[i], rows[r])]
        pivots.append(c)
        r += 1
    return rows[:r], pivots


def current_symmetry(dc_ctx, untied):
    base = dc_ctx.base
    orbit, free_orbits = _free_orbits(base, untied)
    basis = base.value("graph", DC_KEY, "dc_current_basis")
    generators = base.value("graph", DC_KEY, "dc_symmetry")
    colour = dict(base.column("device", "dc_colour"))
    classes = dict(base.column("device", "element_class"))
    pins = {name: dict(p) for name, p in base.column("device", "pins")}
    forms = {name: {t.source: Fraction(t.num, t.den) for t in terms} for name, terms in basis.rows}
    fixed = {name: Fraction(value) for name, value in basis.fixed}
    variables = sorted(basis.free, key=lambda n: (-colour[n], n))        # 구조 색이 큰 쪽이 왼쪽 = 먼저 소거(대표는 색 작은 쪽)
    column = {name: i for i, name in enumerate(variables)}
    width = len(variables)

    def first_net(element):
        terminals = pins[element]
        return terminals[min(terminals)]

    seen, matrix = set(), []
    for generator in generators:
        emap = {v[1]: image[1] for v, image in generator if v[0] == _ELEMENT}
        nmap = {v[1]: image[1] for v, image in generator if v[0] == _NODE}
        for element, form in forms.items():
            image = emap.get(element, element)
            if image not in forms:
                continue
            sign = 1
            if classes[element] == ELEMENT_PASSIVE:               # 방향 없는 2단자: 앞 끝이 앞 끝으로 안 가면 부호 −1
                a, b = first_net(element), first_net(image)
                if nmap.get(a, a) != b:
                    sign = -1
            if image == element and sign == 1:
                continue
            row = [Fraction(0)] * (width + 1)
            for source, coeff in forms[image].items():
                if source in column:
                    row[column[source]] += coeff
                else:
                    row[width] += coeff * fixed[source]
            for source, coeff in form.items():
                if source in column:
                    row[column[source]] -= sign * coeff
                else:
                    row[width] -= sign * coeff * fixed[source]
            key = tuple(row)
            if key in seen or not any(row):
                continue
            seen.add(key)
            matrix.append(row)
    reduced, pivots = _reduce(matrix, width)
    groups, negated, zeros = {}, [], []
    for row, p in zip(reduced, pivots):
        rest = [(c, row[c]) for c in range(width) if c != p and row[c] != 0]
        if row[width] != 0 or len(rest) > 1:
            continue
        member = (THETA_CURRENT, variables[p])
        touched = [variables[p]] + [variables[c] for c, _v in rest]
        if any(orbit[name] in free_orbits for name in touched):      # 묶음을 푼 궤도의 원소에 걸치는 관계는 받지 않는다
            continue
        if not rest:
            zeros.append(member)
            continue
        c, coeff = rest[0]
        if abs(coeff) != 1:
            continue
        rep = (THETA_CURRENT, variables[c])
        groups.setdefault(rep, []).append(member)
        if coeff == 1:                               # x_p + x_q = 0 -> 부호 −1 ; x_p − x_q = 0 -> 부호 +1
            negated.append(member)
    ties = tuple((rep, tuple(sorted(ms, key=lambda m: (colour[m[1]], m[1])))) for rep, ms in
                 sorted(groups.items(), key=lambda kv: (colour[kv[0][1]], kv[0][1])))
    return CurrentSymmetry(ties, tuple(sorted(negated)), tuple(sorted(zeros)))
