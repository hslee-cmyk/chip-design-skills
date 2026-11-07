"""search CONTRACT 3.24 [U2] 2·3 `current_symmetry(dc_ctx, untied) -> CurrentSymmetry(ties, negated, zeros)` + `expand_ties(..., negated, zeros)`.
[U17 ①-b] 첫 인자 = 필드 질의가 되는 스냅샷(`dc.base`) 또는 블록 투영(search_domain 블록 안에서 부른다) -- 커널 컨텍스트 객체가 아니다.

oracle:
- (b) 계약 3.24 2 문장의 독립 구현(`expected_symmetry`): 입력 = 스냅샷 입력 열(sizing `graph.dc_current_basis` 의 rows·ends·free·fixed,
  `graph.dc_symmetry` 생성자, `device.dc_colour`, S1 `device.element_class`·`pins`). 생성자 γ·DC 원소 e 마다 I(γe) − σ·I(e) = 0(σ = −1 ⇔ 2단자 수동소자의
  앞 끝(t0 넷)이 γ 아래 γe 의 앞 끝으로 가지 않음), I 를 독립 θ 전류(+ 선언 전류 상수)의 선형식으로 바꿔 유리수 RREF(열 = 구조 색 큰 쪽부터) ->
  행 분류 (i) x_p = ±x_q -> 묶음(부호 −1 이면 negated), (ii) x_p = 0 -> zeros, (iii) 그 밖 -> 묶지 않음.
- (a) 구성: 손 회로 셋 -- 직렬 감지 저항(o1 -R1- m -R2- o2, m 은 게이트만 구동) -> 대칭·KCL 로 I = 0(구조적 0), 끝을 뒤집어 그린 부하 저항 -> 부호 −1 묶음,
  선언 꼬리 전류원이 상수를 남기는 행(x = I1 − x) -> 묶지 않음.
search `.py` 소스는 열람하지 않았다.
[U17 ①-d] 40 v1.8 §2.4.8·§6-8: 생성자와 전류 부호의 출처가 sizing `graph.dc_symmetry`(정점 사상) -> graph 대칭 블록 필드 `graph/s1: current_symmetry`
(생성자마다 (원소, 상, 부호))로 바뀌었다. 부호 유도(수동소자 앞 끝·MOS d/s 맞바꿈)는 graph 의 책임이고 tests/graph/test_s1_symmetry.py 가 손 유도로
본다 -- 여기 oracle 은 그 필드의 (원소, 상, 부호)를 입력으로 받아 계약 3.24 2 의 연립·RREF·행 분류만 독립으로 다시 한다(판정 내용 불변).
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.search import CurrentSymmetry, current_symmetry, expand_ties
from .conftest import evaluate      # [FS-1 서명 맞춤] 손 wf 를 끼운 evaluate 래퍼
from gmid_engine.sizing import DC_KEY

from .canon_cases import make_case, mid_theta, tie_groups
from .conftest import schema_of  # [U17 ①-b] graph/kernel 필드 읽기
from .conftest import mos, topo, two

DIFF = [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"), mos("M5", "nmos", "t", "vb", "gnd")]
DIFF_PORTS = {"inp": ("input", "differential_input_p"), "inn": ("input", "differential_input_n"),          # [IT-1 DEC-106]
              "o1": ("output", "b"), "o2": ("output", "b")}
R_BOX = (1e3, 1e6)


LOADS = [mos("M3", "pmos", "o1", "pb", "vdd"), mos("M4", "pmos", "o2", "pb", "vdd")]


def series_sense():
    """pmos 부하 M3·M4, 감지 R1 (o1, m)·R2 (m, o2) 직렬, m 은 M6 게이트만 구동(M6: vdd -> gnd 고정점). 대칭 γ 가 R1↔R2 를 끝을 뒤집어
    대응시키므로 I(R2) = −I(R1), KCL(m) 은 I(R1) = I(R2) -> I = 0(구성)."""
    return topo("cs_series", DIFF + LOADS + [mos("M6", "nmos", "vdd", "m", "gnd")], DIFF_PORTS,
                passives=[two("R1", "resistor", "o1", "m"), two("R2", "resistor", "m", "o2")], bias=["vb", "pb"])


def reversed_load():
    """부하 R1 (vdd, o1), R2 (o2, vdd) -- 끝을 뒤집어 그림 -> I(R2) = −I(R1)(구성)."""
    return topo("cs_rev", DIFF, DIFF_PORTS,
                passives=[two("R1", "resistor", "vdd", "o1"), two("R2", "resistor", "o2", "vdd")], bias=["vb"])


def multi_term():
    """선언 꼬리 전류원 I1 (t -> gnd) + pmos 부하: 독립 전류 하나 x 에 대해 짝 전류 = I1 − x 라 대칭식이 x = I1 − x(상수 남음) -> 묶지 않는 행(구성)."""
    return topo("cs_multi", DIFF[:2] + LOADS, DIFF_PORTS, sources=[two("I1", "current_source", "t", "gnd")], bias=["pb"])


I_TAIL = 2e-5                     # 선언 꼬리 전류(입력)


def _case(tmp, doc, lut, untie=None):
    rs = [e["name"] for e in doc["passive_elements"]]
    srcs = tuple((e["name"], e["kind"], I_TAIL) for e in doc.get("ideal_sources") or [])
    return make_case(tmp, doc, lut, elements=tuple((r, "resistor", None) for r in rs) + srcs,
                     boxes={r: R_BOX for r in rs} if rs else None, untie=untie)


# ---------------------------------------------------------------- 독립 oracle (계약 3.24 2 문장)

def expected_symmetry(dc):
    b = dc.base
    basis = b.value("graph", DC_KEY, "dc_current_basis")
    gens = b.value("graph", "s1", "current_symmetry").generators      # [U17 ①-d] ((원소, 상, 부호), ...) 생성자마다
    colour = dict(b.column("device", "dc_colour"))
    fixed = dict(basis.fixed)
    rows = {el: {t.source: Fraction(t.num, t.den) for t in terms} for el, terms in basis.rows}
    free = list(basis.free)

    def expr(el):                                       # I(el) -> ({free 변수: 계수}, 상수)
        lin, const = {}, Fraction(0)
        for src, c in rows[el].items():
            if src in fixed:
                const += c * Fraction(fixed[src])
            else:
                lin[src] = lin.get(src, 0) + c
        return lin, const

    eqs = []
    for g in gens:
        acts = {el: (img, sg) for el, img, sg in g}
        for el in rows:
            img, sign = acts.get(el, (el, 1))
            if img not in rows:
                continue
            a, ca = expr(img)
            e, ce = expr(el)
            row = dict(a)
            for k, v in e.items():
                row[k] = row.get(k, 0) - sign * v
            const = ca - sign * ce
            row = {k: v for k, v in row.items() if v != 0}
            if row or const != 0:
                eqs.append((row, const))
    cols = sorted(free, key=lambda k: -colour[k])        # 구조 색 큰 쪽부터 소거
    M = [[Fraction(r.get(c, 0)) for c in cols] + [Fraction(const)] for r, const in eqs]
    piv, r = [], 0
    for ci in range(len(cols)):
        p = next((i for i in range(r, len(M)) if M[i][ci] != 0), None)
        if p is None:
            continue
        M[r], M[p] = M[p], M[r]
        inv = M[r][ci]
        M[r] = [v / inv for v in M[r]]
        for i in range(len(M)):
            if i != r and M[i][ci] != 0:
                f = M[i][ci]
                M[i] = [x - f * y for x, y in zip(M[i], M[r])]
        piv.append(ci)
        r += 1
    ties, negated, zeros, untied_rows = {}, set(), set(), 0
    for ri, ci in enumerate(piv):
        others = [(cols[j], M[ri][j]) for j in range(len(cols)) if j != ci and M[ri][j] != 0]
        const = M[ri][-1]
        p = ("current", cols[ci])
        if not others and const == 0:
            zeros.add(p)
        elif len(others) == 1 and const == 0 and abs(others[0][1]) == 1:
            q = ("current", others[0][0])
            ties.setdefault(q, set()).add(p)
            if -others[0][1] == -1:
                negated.add(p)
        else:
            untied_rows += 1
    return {frozenset({q} | ms) for q, ms in ties.items()}, negated, zeros, untied_rows


def got_symmetry(dc, untied=()):
    cs = current_symmetry(dc.base, untied)
    return tie_groups(cs.ties), set(cs.negated), set(cs.zeros)


# ---------------------------------------------------------------- 손 회로

def test_series_sense_resistors_structural_zero(tmp_path, lut_sealed):
    case = _case(tmp_path, series_sense(), lut_sealed)
    cs = current_symmetry(case.dc.base, ())
    assert isinstance(cs, CurrentSymmetry)
    g, neg, zeros = got_symmetry(case.dc)
    eg, eneg, ezeros, _ = expected_symmetry(case.dc)
    assert (g, neg, zeros) == (eg, eneg, ezeros)
    assert zeros and zeros <= {("current", "R1"), ("current", "R2")}            # 구성: 감지 저항 전류 0
    d = case.sctx.domain
    assert set(d.zeros) == zeros
    assert not zeros & {v.component for v in d.variables}                       # 구조적 0 은 탐색 변수가 아니다


def test_reversed_resistor_negated_tie(tmp_path, lut_sealed):
    case = _case(tmp_path, reversed_load(), lut_sealed)
    g, neg, zeros = got_symmetry(case.dc)
    assert (g, neg, zeros) == expected_symmetry(case.dc)[:3]
    assert frozenset({("current", "R1"), ("current", "R2")}) in g
    assert neg & {("current", "R1"), ("current", "R2")}
    th, cells = mid_theta(case.sctx.domain)
    got = dict(evaluate(case.sctx, th, cells).theta)
    assert got[("current", "R2")] == -got[("current", "R1")]                    # 평가 θ 확장(3.24 5)


def test_multi_term_rows_left_untied(tmp_path, lut_sealed):
    """(iii): 항이 둘 이상이거나 상수가 남는 행은 묶지 않는다 -- oracle 이 그런 행을 실제로 만든다(공허하지 않음). 전류 묶음·0 이 없다."""
    case = _case(tmp_path, multi_term(), lut_sealed)
    eg, eneg, ezeros, untied_rows = expected_symmetry(case.dc)
    assert untied_rows > 0
    assert got_symmetry(case.dc) == (eg, eneg, ezeros)
    assert (eg, eneg, ezeros) == (set(), set(), set())


def test_asymmetric_circuit_empty(tmp_path, lut_sealed):
    from .canon_cases import asym_doc
    case = make_case(tmp_path, asym_doc(), lut_sealed)
    cs = current_symmetry(case.dc.base, ())
    assert (cs.ties, cs.negated, cs.zeros) == ((), (), ())
    assert case.dc.base.value("graph", "s1", "current_symmetry").generators == ()      # [U17 ①-d] graph 필드


def test_each_component_one_role(tmp_path, lut_sealed):
    """3.24 3: 한 성분은 대표·구성원·구조적 0·묶이지 않음 중 하나(사슬 없음); negated ⊆ 구성원."""
    for doc in (series_sense(), reversed_load(), multi_term()):
        case = _case(tmp_path / doc["topology_name"], doc, lut_sealed)
        cs = current_symmetry(case.dc.base, ())
        reps = [r for r, _ in cs.ties]
        mem = [m for _, ms in cs.ties for m in ms]
        allc = reps + mem + list(cs.zeros)
        assert len(allc) == len(set(allc))
        assert set(cs.negated) <= set(mem)


def test_untie_removes_relations_of_orbit(tmp_path, lut_sealed):
    """3.24 7: untie 한 원소의 궤도 원소가 들어간 관계·구조적 0 은 받지 않는다."""
    case = _case(tmp_path, reversed_load(), lut_sealed)
    g, neg, zeros = got_symmetry(case.dc, ("R2",))
    involved = {c for grp in g for c in grp} | zeros
    assert not involved & {("current", "R1"), ("current", "R2")}
    with pytest.raises(SchemaRejectedError) as e:
        current_symmetry(case.dc.base, ("Nope",))
    assert dict(e.value.record.detail)["reason"] == "untie_element_unknown"
    with pytest.raises(SchemaRejectedError) as e:
        current_symmetry(case.dc.base, ("M5",))
    assert dict(e.value.record.detail)["reason"] == "untie_orbit_trivial"


def test_dimension_accounting(tmp_path, lut_sealed):
    """3.24 9 (a): 차원(변수 + L 칸 대표) + 묶인 구성원 수 + 구조적 0 수 = 스키마 성분 수."""
    for doc in (series_sense(), reversed_load(), multi_term()):
        case = _case(tmp_path / doc["topology_name"], doc, lut_sealed)
        d = case.sctx.domain
        members = sum(len(ms) for _, ms in d.ties)
        assert len(d.variables) + len(d.l_cells) + members + len(d.zeros) == len(schema_of(case.dc).components)


# ---------------------------------------------------------------- expand_ties negated·zeros (3.24 3·5·9 (b))

def test_expand_ties_negated_and_zeros_pure():
    ties = ((("current", "A"), (("current", "B"), ("current", "C"))),)
    th = {("current", "A"): 2.5e-6, ("current", "B"): 9.0, ("current", "Z"): 4.0}
    before = dict(th)
    out = expand_ties(ties, th, (("current", "C"),), (("current", "Z"),))
    assert th == before and out is not th
    assert out[("current", "B")] == 2.5e-6
    assert out[("current", "C")] == -2.5e-6
    assert out[("current", "Z")] == 0.0
    assert out[("current", "A")] == 2.5e-6
