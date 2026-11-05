"""규칙 L 검사기가 공허하지 않음을 보인다 -- 거부 먼저.

oracle (a): 픽스처(`fixtures/rule_l/<id>/gmid_engine/`)는 구성으로 정답이 정해진 합성 입력이고, 기대 위반
(키, code)는 픽스처 소스를 읽고 손으로 적었다(check_rule_l 출력을 옮긴 것이 아니다). 위반 집합 전체를 `==`로
비교한다(없는 것도, 더 있는 것도 실패). 근거 표 = interface card 20261104-gc1-rule-l '픽스처'.
부채·지문 test(L6·L6b·L6c·L7·L10)는 입력을 test 안에서 손으로 짠다.

해석이 card에서 갈리는 자리는 아래 `LOOSE_*`로 따로 둔다(주석에 이유).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from rule_l_checks import DebtReport, Violation, check_debt, check_rule_l, fingerprint  # noqa: E402
from rule_l_debt import DebtItem  # noqa: E402
from rule_l_tables import PARAMS, RuleLParams  # noqa: E402

FIX = HERE / "fixtures" / "rule_l"
ENTRY = "pipeline/stage_a.py:run_stage_a"


def params(**kw):
    base = dict(
        entry_points=(ENTRY,),
        output_functions=(),
        dynamic_allowed_files=(),
        l5_concepts={},
        output_only_fields=(),
        output_only_slots=(),
        fingerprint_only_slots=(),
    )
    base.update(kw)
    return RuleLParams(**base)


def root(fid):
    p = FIX / fid / "gmid_engine"
    assert p.is_dir(), "픽스처 트리 없음: %s" % p
    return p


DIODE_GS = {
    "diode": ("device.is_diode", "graph/s1_structure.py"),
    "same_vgs": ("graph.gs_groups", "graph/gs_groups.py"),
}
OP_COPY = {"op_copy": ("device.dc_op", "graph/op_block.py")}

NR, NC, FD = "no_reader", "no_caller", "field_arg_dynamic"
PRED, OPC = "predicate_recomputed", "op_copy"


def l5(concept, fn="check", file="graph/user.py"):
    return [(("L-5", concept, file, fn), PRED)]


# id -> (RuleLParams, 기대 [(key, code), ...])  -- 손으로 적음
EXACT = {
    # L-1
    "L1a": (params(), [(("L-1", "graph.alpha"), NR)]),
    "L1b": (params(), [(("L-1", "graph.alpha"), NR), (("L-1x", "pipeline.stage_a._dead"), NC)]),
    "L1c": (params(), []),
    "L1d": (params(), [(("L-1", "graph.alpha"), NR)]),
    # L-2
    "L2a": (params(output_functions=("pipeline/stage_a.py:_report",)),
            [(("L-2", "graph.alpha"), "output_only_undeclared")]),
    "L2b": (params(output_functions=("pipeline/stage_a.py:_report",),
                   output_only_fields=(("graph.alpha", "pipeline/stage_a.py:_report", "표시용"),)), []),
    "L2c": (params(output_functions=("graph/tail.py:_report",),
                   output_only_fields=(("graph.alpha", "graph/tail.py:_report", "표시용"),)),
            [(("L-2", "graph.alpha"), "output_function_unreachable")]),
    # L-3
    "L3a": (params(), [(("L-3", "blk.graph.beta"), "reads_not_read")]),
    "L3b": (params(), [(("L-3", "blk.graph.beta"), "reads_not_read"),
                       (("L-3", "blk.graph.delta"), "reads_not_read")]),
    "L3c": (params(), []),
    "L3d": (params(), [(("L-3", "blk.graph.beta"), "reads_unverifiable")]),
    "L3e": (params(), [(("L-3", "blk.graph.beta"), "reads_unverifiable")]),
    # L-4
    "L4a": (params(), [(("L-4", "core.values.Row.unused"), "slot_no_reader")]),
    "L4b": (params(), []),
    "L4c": (params(), [(("L-4", "core.values.Row.inner"), "slot_no_reader")]),
    # L-5 diode / same_vgs
    "L5a-1": (params(l5_concepts=DIODE_GS), l5("diode")),
    "L5a-2": (params(l5_concepts=DIODE_GS), l5("diode")),
    "L5a-3": (params(l5_concepts=DIODE_GS), l5("diode")),
    "L5a-4": (params(l5_concepts=DIODE_GS), l5("diode")),
    "L5a-5": (params(l5_concepts=DIODE_GS), l5("same_vgs")),
    "L5a-6": (params(l5_concepts=DIODE_GS), l5("same_vgs")),
    "L5a-7": (params(l5_concepts=DIODE_GS), l5("same_vgs")),
    "L5a-8": (params(l5_concepts=DIODE_GS), l5("same_vgs")),
    "L5a-9": (params(l5_concepts=DIODE_GS), []),
    "L5a-10": (params(l5_concepts=DIODE_GS), []),
    # L-5 op_copy
    "L5b-1": (params(l5_concepts=OP_COPY), [(("L-5", "op_copy", "graph/op_user.py", "_row"), OPC),
                                            (("L-5", "op_copy", "graph/op_user.py", "place"), OPC)]),
    "L5b-2": (params(l5_concepts=OP_COPY), [(("L-5", "op_copy", "graph/op_user.py", "_current"), OPC),
                                            (("L-5", "op_copy", "graph/op_user.py", "lay"), OPC)]),
    "L5b-3": (params(l5_concepts=OP_COPY), [(("L-5", "op_copy", "graph/op_user.py", "lay"), OPC)]),
    "L5c-1": (params(l5_concepts=OP_COPY), []),
    "L5c-2": (params(l5_concepts=OP_COPY), []),
    "L5c-3": (params(l5_concepts=OP_COPY, output_functions=("graph/op_user.py:_report",)), []),
    # L-1x
    "L8a": (params(), [(("L-1x", "graph.unused.Orphan"), NC), (("L-1x", "graph.unused.orphan"), NC)]),
    "L8b": (params(), [(("L-1x", "graph.ghost.ghost_fn"), NC)]),
    "L8c": (params(), []),
    "L8d": (params(), []),
    "L8e": (params(), []),
    "L8f": (params(), []),
    # L-1d
    "L9a": (params(), [(("L-1", "graph.alpha"), NR), (("L-1d", "pipeline.stage_a.read_field"), FD)]),
    "L9b": (params(), [(("L-1", "graph.alpha"), NR), (("L-1d", "pipeline.stage_a.run_stage_a"), FD)]),
    "L9d": (params(dynamic_allowed_files=("core/graph_snapshot.py",)), []),
    "L9e": (params(), []),
}

# 판정 A-117 추가분 -- (case id, 픽스처 폴더, params, 기대). 같은 트리를 params만 바꿔 두 번 쓰는 자리가 있다.
# oracle (a): 기대는 픽스처 소스를 읽고 손으로 적었다. 뮤턴트 생존 10개를 겨냥하는 입력은 주석에 이름을 단다.
OPF = [(("L-5", "op_copy", "graph/op_user.py", "f"), OPC)]


def OPP(fn, file="graph/op_user.py"):      # noqa: N802
    return (("L-5", "op_copy", file, fn), OPC)


ADD = [
    # L-3 별칭: 별칭을 거친 읽기는 읽기이고, 안 읽으면 위반
    ("L3f", "L3f", params(), []),
    ("L3g", "L3g", params(), [(("L-3", "blk.graph.beta"), "reads_not_read")]),
    ("L3h", "L3h", params(), []),
    # diode / same_vgs 경계
    ("L5k-len", "L5k-len", params(l5_concepts=DIODE_GS), []),
    ("L5k-isinst", "L5k-isinst", params(l5_concepts=DIODE_GS), []),
    # canon((g, s)) 꼴(check)과 canon(g), canon(s) 꼴(edges, 묶음 키 성분을 사용자 함수로 감싼 꼴) 둘 다 위반
    ("L5k-canon", "L5k-canon", params(l5_concepts=DIODE_GS), l5("same_vgs") + l5("same_vgs", fn="edges")),
    # op_copy 끊김 아님(float, Op-float-cuts)과 sink 꼴
    ("L5e-float", "L5e-float", params(l5_concepts=OP_COPY), OPF),
    ("L5e-attr", "L5e-attr", params(l5_concepts=OP_COPY), OPF),
    ("L5e-gsub", "L5e-gsub", params(l5_concepts=OP_COPY), OPF),
    ("L5e-global", "L5e-global", params(l5_concepts=OP_COPY), OPF),
    ("L5e-gupd", "L5e-gupd", params(l5_concepts=OP_COPY), OPF),
    ("L5e-meth", "L5e-meth", params(l5_concepts=OP_COPY), OPF),
    ("L5e-json", "L5e-json", params(l5_concepts=OP_COPY), OPF),
    # 스냅샷 운반 함수는 키에서 제외, 사본을 만든 inner만
    ("L5f-carry", "L5f-carry", params(l5_concepts=OP_COPY),
     [(("L-5", "op_copy", "graph/op_user.py", "inner"), OPC)]),
    # 필드 단위 추적: 같은 객체의 다른 칸은 clean, 오염된 칸은 위반
    ("L5g-clean", "L5g-clean", params(l5_concepts=OP_COPY), []),
    ("L5g-taint", "L5g-taint", params(l5_concepts=OP_COPY),
     [(("L-5", "op_copy", "graph/op_user.py", "lay"), OPC)]),
    # 출력 함수 면제가 실제로 일한다(Op-output-exempt): 목록에 있으면 clean, 없으면 같은 코드가 위반
    ("L5h-on", "L5h-exempt", params(l5_concepts=OP_COPY, output_functions=("graph/op_user.py:_report",)), []),
    ("L5h-off", "L5h-exempt", params(l5_concepts=OP_COPY),
     [(("L-5", "op_copy", "graph/op_user.py", "_report"), OPC)]),
    # writer 파일 면제(Op-writer-exempt), 도달 조건(N3.1-5): 진입점에서 도달하지 않는 함수는 대상 밖, 같은 함수가 도달하면 위반
    ("L5i-writer", "L5i-writer", params(l5_concepts=OP_COPY), []),
    ("L5j-reach", "L5j-reach", params(l5_concepts=OP_COPY), []),
    ("L5j-reach-on", "L5j-reach-on", params(l5_concepts=OP_COPY),
     [(("L-5", "op_copy", "graph/tail.py", "_late"), OPC)]),
    # L-4 목록(L4-exempt): 출력 전용·지문 전용 목록의 칸은 면제, 다른 칸 이름은 면제 아님
    ("L4d-output", "L4d", params(output_only_slots=("Row.unused",)), []),
    ("L4d-fingerprint", "L4d", params(fingerprint_only_slots=("Row.unused",)), []),
    ("L4d-other", "L4d", params(output_only_slots=("Row.other",), fingerprint_only_slots=("Row.other",)),
     [(("L-4", "core.values.Row.unused"), "slot_no_reader")]),
    # 읽기 판정: kind 인자가 권한표 kind가 아니면 다른 객체의 메서드(Read-kindfilter)
    ("L10a", "L10a", params(), [(("L-1", "graph.alpha"), NR)]),
    # 지역 변수가 import 이름을 가림(Graph-shadow): 가려진 import는 호출이 아니다
    ("L11", "L11", params(), [(("L-1x", "graph.h.helper"), NC)]),
    # 블록 없는 WriterTable 행(Table-wt-off): 읽는 행은 clean, 안 읽는 행은 no_reader
    ("LW1", "LW1", params(), [(("L-1", "graph.beta"), NR)]),
    # ---- O-241: 허용 목록 없는 fail-closed. 기대는 픽스처 소스를 읽고 손으로 적었다(A-117 재판정 주입 21꼴, inject2.txt) ----
    # (iv) 호출보다 오래 사는지 풀리지 않는 객체에 담기: 컨텍스트 첨자·append·update, 넘겨받은 dict 첨자(인자로 받은 값, 직접 읽은 값), 인스턴스 속성
    ("L5m-ctx-subscript", "L5m-ctx-subscript", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-ctx-append", "L5m-ctx-append", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-ctx-update", "L5m-ctx-update", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-param-dict", "L5m-param-dict", params(l5_concepts=OP_COPY), [OPP("keep")]),
    ("L5m-param-dict-arg", "L5m-param-dict-arg", params(l5_concepts=OP_COPY), [OPP("keep")]),
    ("L5m-self-attr", "L5m-self-attr", params(l5_concepts=OP_COPY), [OPP("_K.keep")]),
    # (ii) 엔진에 같은 이름 메서드가 있는 S3 append_eval: 수신자 형이 안 풀리니 추적 불능(Arc 는 아무도 안 만든다 -> L-1x)
    ("L5m-s3-append-eval", "L5m-s3-append-eval", params(l5_concepts=OP_COPY),
     [(("L-1x", "graph.op_user.Arc"), NC), OPP("place")]),
    # (iii) 직렬화 이름 목록 없이: 이름 import, 외부 모듈 함수·메서드, 파일 객체 메서드
    ("L5m-from-json-dumps", "L5m-from-json-dumps", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-yaml-safe-dump", "L5m-yaml-safe-dump", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-numpy-save", "L5m-numpy-save", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-pickle-dump", "L5m-pickle-dump", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-writelines", "L5m-writelines", params(l5_concepts=OP_COPY), [OPP("place")]),
    # 흐름이 끊기던 꼴: dataclasses.replace, copy.copy, 칸 이름 != 인자 이름, 상속 칸, dict.pop, 메서드 반환, 깊은 중첩
    ("L5m-dc-replace", "L5m-dc-replace", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-copy-copy", "L5m-copy-copy", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-ctor-rename", "L5m-ctor-rename", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-ctor-base-field", "L5m-ctor-base-field", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-pop-bag", "L5m-pop-bag", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-method-getter", "L5m-method-getter", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-three-layers", "L5m-three-layers", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-three-layers-stored", "L5m-three-layers-stored", params(l5_concepts=OP_COPY), [OPP("place")]),
    # 외부 라이브러리 산술(math.log)도 엔진 안 정의로 안 풀리는 호출이다 -> 위반(옛 inject2 의 clean 기대는 O-241 로 바뀜, 검증자가 손 분류)
    ("L5m-ext-math", "L5m-ext-math", params(l5_concepts=OP_COPY), [OPP("place")]),
    # 같은 객체의 다른 칸(속성 이름이 인자 이름과 다른 __init__ 포함)은 오염 아님
    ("L5m-field-other-clean", "L5m-field-other-clean", params(l5_concepts=OP_COPY), []),
    # 예외 목록: 이름이 안 가려진 내장 함수, 내장 형으로 확정된 수신자의 그 형 메서드, 이 함수에서 새로 만든 컨테이너에 담기만
    ("L5m-builtin-pure-clean", "L5m-builtin-pure-clean", params(l5_concepts=OP_COPY), []),
    ("L5m-typed-method-clean", "L5m-typed-method-clean", params(l5_concepts=OP_COPY), []),
    ("L5m-local-container-clean", "L5m-local-container-clean", params(l5_concepts=OP_COPY), []),
    # 예외 조건이 일한다: 수신자 형을 못 정함(같은 이름 index), 내장 이름을 매개변수가 가림, 새 컨테이너가 호출로 빠져나감
    ("L5m-untyped-method", "L5m-untyped-method", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-shadow-builtin", "L5m-shadow-builtin", params(l5_concepts=OP_COPY), [OPP("place")]),
    ("L5m-local-container-escape", "L5m-local-container-escape", params(l5_concepts=OP_COPY), [OPP("place")]),
]


@pytest.mark.parametrize("case", [c[0] for c in ADD])
def test_rule_l_fixture_a117_added_violation_set(case):
    """A-117 추가 픽스처: (키, code) 집합이 손으로 적은 기대와 정확히 같다. oracle (a)."""
    _, fid, p, expected = next(c for c in ADD if c[0] == case)
    assert _got(fid, p) == sorted(expected)


def test_rule_l_l3x_unresolvable_reads_not_silent():
    """L3x(L3-unresolved-reads): 풀 수 없는 `reads=`(호출 결과)는 조용히 통과하지 않는다. code는 card에 없어 둘 중 하나로 본다."""
    got = check_rule_l(root("L3x"), params())
    assert got
    assert {v.code for v in got} <= {"reads_unverifiable", "writer_table_unresolved"}


def test_rule_l_writer_table_unresolved_row():
    """LW2(Table-wt-off): 풀 수 없는 WriterTable 행은 writer_table_unresolved(키 앞 칸 L-1, 파일 core/tables.py)."""
    got = check_rule_l(root("LW2"), params())
    assert [(v.key[0], v.key[2], v.code) for v in got] == [("L-1", "core/tables.py", "writer_table_unresolved")]


def test_rule_l_missing_entry_point_not_silent():
    """L10b(Entry-missing): 트리에 없는 진입점을 목록에 두면 조용히 무시하지 않고 위반으로 보고한다(fail-closed)."""
    got = check_rule_l(root("L10b"), params(entry_points=(ENTRY, "pipeline/stage_a.py:no_such_entry")))
    assert any("no_such_entry" in (str(v.key) + v.detail) for v in got)


def _got(fid, p):
    return [(v.key, v.code) for v in check_rule_l(root(fid), p)]


@pytest.mark.parametrize("fid", sorted(EXACT))
def test_rule_l_fixture_exact_violation_set(fid):
    """픽스처마다 위반 (키, code) 집합이 손으로 적은 기대와 정확히 같다. oracle (a), 구성으로 정해진 합성 입력."""
    p, expected = EXACT[fid]
    assert _got(fid, p) == sorted(expected)


def test_rule_l_fixture_count_covers_card_table():
    """card 픽스처 표의 트리 입력형 id가 모두 디스크에 있다(빠뜨린 픽스처를 막는다)."""
    need = set(EXACT) | {"L9c", "LT", "L5a-11", "L3x", "L10b", "LW2", "L5p-path-field", "L5p-path-two"} | {c[1] for c in ADD}
    have = {p.name for p in FIX.iterdir() if p.is_dir()}
    assert need == have


def test_rule_l_l5a_11_missing_writer_file():
    """L5a-11: 등록 writer 파일이 트리에 없다 -> writer_file_missing. 함수 칸 형식은 card에 없어 앞 3칸만 비교."""
    p = params(l5_concepts={"diode": ("device.is_diode", "graph/missing.py")})
    got = [(v.key[:3], v.code) for v in check_rule_l(root("L5a-11"), p)]
    assert got == [(("L-5", "diode", "graph/missing.py"), "writer_file_missing")]


def test_rule_l_l9c_closure_variable_is_dynamic():
    """L9c: 클로저 변수로 쓴 필드 인자 = 동적. 중첩 함수 키 표기(`_make` 또는 `_make.get`)는 card에 없어 접두로 비교."""
    got = check_rule_l(root("L9c"), params())
    dyn = [v for v in got if v.key[0] == "L-1d"]
    assert len(dyn) == 1
    assert dyn[0].code == FD
    assert dyn[0].key[1].startswith("pipeline.stage_a._make")
    assert [(v.key, v.code) for v in got if v.key[0] != "L-1d"] == [(("L-1", "graph.alpha"), NR)]


def test_rule_l_lt_unresolvable_writes():
    """LT: 풀 수 없는 `writes=`(호출 결과) -> writer_table_unresolved. 키 둘째 칸(<table>)은 card에 없어 비교하지 않는다."""
    got = check_rule_l(root("LT"), params())
    assert [(v.key[0], v.key[2], v.code) for v in got] == [("L-1", "graph/blk.py", "writer_table_unresolved")]


def test_rule_l_result_sorted_by_key_and_deterministic():
    """check_rule_l 반환은 키로 정렬이고 두 번 불러도 같다(결정성)."""
    p, _ = EXACT["L9a"]
    a = check_rule_l(root("L9a"), p)
    b = check_rule_l(root("L9a"), p)
    assert a == b
    assert [v.key for v in a] == sorted(v.key for v in a)
    assert all(isinstance(v, Violation) for v in a)


# ---------------------------------------------------------------- 부채 (L6, L6b, L6c, L7)

K1, K2, K3 = ("L-1", "graph.alpha"), ("L-1", "graph.beta"), ("L-1", "graph.gamma")
OK_ITEM = DebtItem("배선 대기", "GC-7", "근거")


def V(key):
    return Violation(key, "no_reader", "손으로 만든 위반")


def ids(seq):
    """report 칸의 항목을 키 집합으로(원소가 Violation이든 키든)."""
    return {x.key if isinstance(x, Violation) else x for x in seq}


def test_rule_l_debt_l6_deleted_item_and_addition_outside_baseline():
    """L6: 항목 삭제(K2) + 기준선 밖 추가(K3)는 실패한다. 기대는 손으로: K2 위반인데 목록에 없음, K3은 기준선에 없음."""
    r = check_debt([V(K1), V(K2), V(K3)], {K1: OK_ITEM, K3: OK_ITEM}, (K1, K2))
    assert isinstance(r, DebtReport)
    assert ids(r.missing) == {K2}
    assert ids(r.outside_baseline) == {K3}
    assert ids(r.stale) == set()
    assert ids(r.bad_items) == set()


def test_rule_l_debt_l6b_violation_without_item_is_missing():
    """L6b: 위반인데 부채 목록에 없다 -> missing."""
    r = check_debt([V(K1)], {}, (K1,))
    assert ids(r.missing) == {K1}
    assert ids(r.stale) == set() and ids(r.outside_baseline) == set() and ids(r.bad_items) == set()


def test_rule_l_debt_l7_fixed_but_still_listed_is_stale():
    """L7: 고쳐졌는데(위반 아님) 목록에 남은 항목 -> stale."""
    r = check_debt([V(K1)], {K1: OK_ITEM, K2: OK_ITEM}, (K1, K2))
    assert ids(r.stale) == {K2}
    assert ids(r.missing) == set() and ids(r.outside_baseline) == set() and ids(r.bad_items) == set()


def test_rule_l_debt_l6c_vocabulary_and_blank_card():
    """L6c: 처리 어휘 밖(K1)과 card 빈 칸(K2)은 bad_items, 정상(K3)은 아니다."""
    debt = {K1: DebtItem("없는 처리", "GC-7", "근거"), K2: DebtItem("배선 대기", "", "근거"), K3: OK_ITEM}
    r = check_debt([V(K1), V(K2), V(K3)], debt, (K1, K2, K3))
    assert ids(r.bad_items) == {K1, K2}
    assert ids(r.missing) == set() and ids(r.stale) == set() and ids(r.outside_baseline) == set()


def test_rule_l_debt_six_vocabulary_words_all_accepted():
    """처리 어휘 6개(N3.1-6)는 모두 허용한다. 출처: interface card '처리 어휘'."""
    words = ("배선 대기", "정본 읽기로 교체", "출력 전용 선언 대기", "삭제 승인 대기", "공동분석 대기",
             "정적 해석 형태로 바꾸기")
    keys = tuple(("L-1", "graph.f%d" % i) for i in range(len(words)))
    debt = {k: DebtItem(w, "GC-7", "근거") for k, w in zip(keys, words)}
    r = check_debt([V(k) for k in keys], debt, keys)
    assert (ids(r.bad_items), ids(r.missing), ids(r.stale), ids(r.outside_baseline)) == (set(),) * 4


# ---------------------------------------------------------------- 지문 (L10)

def _fp_inputs(tmp_path, checks=b"a = 1\n", tables=b"b = 2\n"):
    c, t = tmp_path / "rule_l_checks.py", tmp_path / "rule_l_tables.py"
    c.write_bytes(checks)
    t.write_bytes(tables)
    return c, t


def test_rule_l_fingerprint_changes_on_one_char_or_one_param(tmp_path):
    """L10: 지문 대상 파일 한 글자, PARAMS 한 항목이 바뀌면 지문이 바뀌고, 같은 입력은 같다. 구성으로 정해진 입력."""
    c, t = _fp_inputs(tmp_path)
    base = fingerprint(PARAMS, c, t)
    assert isinstance(base, str) and len(base) == 64 and set(base) <= set("0123456789abcdef")
    assert fingerprint(PARAMS, c, t) == base
    dx, dy = tmp_path / "x", tmp_path / "y"
    dx.mkdir()
    dy.mkdir()
    c2, t2 = _fp_inputs(dx, b"a = 2\n")
    assert fingerprint(PARAMS, c2, t2) != base                       # checks 한 글자
    c3, t3 = _fp_inputs(dy, tables=b"b = 3\n")
    assert fingerprint(PARAMS, c3, t3) != base                       # tables 한 글자
    assert fingerprint(PARAMS._replace(entry_points=PARAMS.entry_points + ("x/y.py:z",)), c, t) != base
    assert fingerprint(PARAMS._replace(output_functions=PARAMS.output_functions[:-1]), c, t) != base
    assert fingerprint(PARAMS._replace(output_only_fields=PARAMS.output_only_fields[:-1]), c, t) != base
    changed = dict(PARAMS.l5_concepts)
    changed["diode"] = ("device.is_diode", "graph/s1_structure2.py")
    assert fingerprint(PARAMS._replace(l5_concepts=changed), c, t) != base


def test_rule_l_fingerprint_newline_normalized(tmp_path):
    """L10: 줄바꿈 CRLF 대 LF는 지문이 같다(줄바꿈 정규화)."""
    lf = tmp_path / "lf"
    crlf = tmp_path / "crlf"
    lf.mkdir()
    crlf.mkdir()
    c1, t1 = _fp_inputs(lf, b"a = 1\nb = 2\n", b"x = 1\ny = 2\n")
    c2, t2 = _fp_inputs(crlf, b"a = 1\r\nb = 2\r\n", b"x = 1\r\ny = 2\r\n")
    assert fingerprint(PARAMS, c1, t1) == fingerprint(PARAMS, c2, t2)


# ---------------------------------------------------------------- O-241: 칸 경로 출력, 손 분류 표(op_copy_cleared), 고정점 fail-closed

PLACE = ("L-5", "op_copy", "graph/op_user.py", "place")
OPC_PARAMS = dict(l5_concepts=OP_COPY)


def _op(fid, **kw):
    return check_rule_l(root(fid), params(**OPC_PARAMS, **kw))


def test_rule_l_op_copy_reports_caught_field_paths():
    """칸 경로 출력: 객체의 `current` 칸이 닿으면 ('current',), 정본 값 전체가 닿으면 ()이다. 위반 키는 interface 키 꼴 그대로.
    oracle (a): L5p-path-field 는 Row(current=동작점 값, n=상수)를 묶음째 쓴다 -> 오염된 칸은 current 하나. L5p-path-two 는 더해서 값 자체를 쓴다."""
    one = _op("L5p-path-field")
    assert [(v.key, v.paths) for v in one] == [(PLACE, (("current",),))]
    two = _op("L5p-path-two")
    assert [(v.key, v.paths) for v in two] == [(PLACE, ((), ("current",)))]


def test_rule_l_op_copy_reports_callee_made_copy_path():
    """사본을 만든 피호출(`_row`)의 칸 경로는 피호출이 돌려준 칸이다. oracle (a): L5b-1 의 `_row` 는 Row(current=...)를 돌려준다."""
    got = {v.key: v.paths for v in _op("L5b-1", output_functions=())}
    assert got[("L-5", "op_copy", "graph/op_user.py", "_row")] == (("current",),)
    assert got[PLACE] == ((),)


def _row(path, key=PLACE, ref="graph/op_user.py:12"):
    return (key, path, ref)


def test_rule_l_op_copy_cleared_row_hides_only_listed_path():
    """표 행이 (키, 칸 경로)를 가린다. 구성: path-field 는 ('current',) 하나만 잡힌다 -> 그 행이면 위반 0."""
    assert _op("L5p-path-field", op_copy_cleared=(_row(("current",)),)) == ()


def test_rule_l_op_copy_cleared_new_path_still_violation():
    """새 칸 경로 = 위반. 구성: path-two 는 () 와 ('current',) 둘이 잡힌다. ('current',) 행만 있으면 () 는 위반으로 남고 남은 경로만 낸다."""
    got = _op("L5p-path-two", op_copy_cleared=(_row(("current",)),))
    assert [(v.key, v.code, v.paths) for v in got] == [(PLACE, "op_copy", ((),))]


def test_rule_l_op_copy_cleared_row_for_other_key_hides_nothing():
    """행의 키가 다르면 가리지 않는다. 구성: 키의 함수 이름만 다른 행(`other`)은 place 를 가리지 못하고, 자기는 낡은 항목이다."""
    other = ("L-5", "op_copy", "graph/op_user.py", "other")
    got = _op("L5p-path-field", op_copy_cleared=(_row(("current",), key=other),))
    assert sorted((v.key, v.code) for v in got) == sorted([(("L-5", "op_copy_cleared", "graph/op_user.py", "other"), "op_copy_cleared_stale"),
                                                           (PLACE, "op_copy")])


def test_rule_l_op_copy_cleared_stale_row_is_violation():
    """잡히지 않는 행 = 위반(op_copy_cleared_stale). 구성: ('current',) 는 잡히지만 ('n',) 은 잡히지 않는다 -> 낡은 행 하나만 위반이고 키는 op_copy 와 다르다."""
    got = _op("L5p-path-field", op_copy_cleared=(_row(("current",)), _row(("n",))))
    assert [(v.key, v.code, v.paths) for v in got] == [(("L-5", "op_copy_cleared", "graph/op_user.py", "place"), "op_copy_cleared_stale", (("n",),))]


def test_rule_l_op_copy_cleared_stale_when_nothing_caught():
    """깨끗한 트리에 행이 있으면 모두 낡은 항목이다. 구성: L5g-clean 은 위반 0 이므로 어떤 행도 가릴 것이 없다."""
    row = _row((), key=("L-5", "op_copy", "graph/op_user.py", "lay"))
    got = _op("L5g-clean", op_copy_cleared=(row,))
    assert [(v.key, v.code) for v in got] == [(("L-5", "op_copy_cleared", "graph/op_user.py", "lay"), "op_copy_cleared_stale")]


def test_rule_l_op_copy_cleared_default_empty_changes_nothing():
    """표가 비면(기본) 행 없는 호출과 같다. 구성: 같은 트리, 행 인자 유무."""
    assert _op("L5p-path-field") == _op("L5p-path-field", op_copy_cleared=())
    assert len(_op("L5p-path-field")) == 1


def test_rule_l_fingerprint_includes_op_copy_cleared(tmp_path):
    """표는 지문 대상이다: 행 하나가 늘면 지문이 바뀐다(N3.1-6 (d)). 구성: 같은 입력에서 행만 다르다."""
    c, t = _fp_inputs(tmp_path)
    base = fingerprint(PARAMS, c, t)
    changed = fingerprint(PARAMS._replace(op_copy_cleared=((PLACE, ("current",), "graph/op_user.py:12"),)), c, t)
    assert changed != base
    other_path = fingerprint(PARAMS._replace(op_copy_cleared=((PLACE, ("n",), "graph/op_user.py:12"),)), c, t)
    assert other_path != changed


def test_rule_l_op_copy_fixed_point_overflow_is_violation(monkeypatch):
    """고정점 상한을 넘으면 조용히 멈추지 않고 추적 실패(op_copy)로 낸다. 구성: 상한 1회로 낮추면 L5b-1(라벨이 두 함수를 거쳐 퍼짐)은 첫 회에 더 자란다.
    기본 상한에서는 같은 트리에 추적 실패 키가 없다."""
    import rule_l_checks
    key = ("L-5", "op_copy", "graph/op_block.py", "<fixed_point>")
    assert key not in {v.key for v in _op("L5b-1")}
    monkeypatch.setattr(rule_l_checks, "OP_COPY_ROUNDS", 1)
    got = [v for v in _op("L5b-1") if v.key == key]
    assert [v.code for v in got] == ["op_copy"]


def test_rule_l_op_copy_has_no_name_allowlists():
    """허용 목록 금지(O-241): 이름으로 면제·직렬화를 가르던 상수와 외부 수신자 면제가 도구에 없다. 예외는 닫힌 내장 목록 하나뿐.
    구성: rule_l_checks 의 최상위 이름과 클래스 메서드 이름을 AST 로 본다."""
    import ast
    import rule_l_checks
    tree = ast.parse(Path(rule_l_checks.__file__).read_text(encoding="utf-8"))
    names = {t.id for n in ast.walk(tree) if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
    names |= {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert not names & {"BENIGN_METHODS", "SERIALIZERS", "_ext_receiver"}
