"""규칙 L 검사기가 공허하지 않음을 보인다 -- 거부 먼저.

oracle (a): 픽스처(`fixtures/rule_l/<id>/gmid_engine/`)는 구성으로 정답이 정해진 합성 입력이고, 기대 위반
(키, code)는 픽스처 소스를 읽고 손으로 적었다(check_rule_l 출력을 옮긴 것이 아니다). 위반 집합 전체를 `==`로
비교한다(없는 것도, 더 있는 것도 실패). 근거 표 = interface card 20261104-gc1-rule-l '픽스처'.
부채·지문 test(L6·L6b·L6c·L7·L10)는 입력을 test 안에서 손으로 짠다.

해석이 card에서 갈리는 자리는 아래 `LOOSE_*`로 따로 둔다(주석에 이유).
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from rule_l_checks import DebtReport, Violation, check_debt, check_rule_l, fingerprint  # noqa: E402
from rule_l_debt import DebtItem  # noqa: E402
from rule_l_tables import CLEARED_FILE, PARAMS, RuleLParams, load_op_copy_cleared  # noqa: E402

FIX = HERE / "fixtures" / "rule_l"
CLEARED_NAME = "rule_l_op_copy_cleared.json"      # 손 분류 표 데이터 파일 이름(interface: 같은 폴더). 상수가 바뀌면 test_..._file_name_is_fixed 가 실패한다
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
    # (O-241 재판정 M-5) 출력 함수 면제는 (iii) 결과 JSON·보고 객체 자리뿐이다: `_report` 는 보고 객체를 돌려줄 뿐 graph 쓰기는 호출자가 한다.
    # 면제 목록에 없으면 호출자가 사본을 graph 에 쓰니 사본을 만든 `_report` 와 쓴 `run_stage_a` 가 둘 다 위반이다(L5b-1 의 `_row`·`place` 와 같은 꼴).
    ("L5h-off", "L5h-exempt", params(l5_concepts=OP_COPY),
     [(("L-5", "op_copy", "graph/op_user.py", "_report"), OPC), (("L-5", "op_copy", "pipeline/stage_a.py", "run_stage_a"), OPC)]),
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
    need = set(EXACT) | {"L9c", "LT", "L5a-11", "L3x", "L10b", "LW2", "L5p-path-field", "L5p-path-two", "L5q-two-forms",
                        "L5q-whole-copy"} | {c[1] for c in ADD}
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

def _fp_inputs(tmp_path, checks=b"a = 1\n", tables=b"b = 2\n", cleared=b"[]\n"):
    c, t = tmp_path / "rule_l_checks.py", tmp_path / "rule_l_tables.py"
    c.write_bytes(checks)
    t.write_bytes(tables)
    (tmp_path / CLEARED_NAME).write_bytes(cleared)          # 표 데이터 파일: tables 와 같은 폴더(지문 함수의 기본 자리)
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


# ---------------------------------------------------------------- O-241: 칸 경로·sink 꼴 출력, 손 분류 표(op_copy_cleared), 고정점 fail-closed

PLACE = ("L-5", "op_copy", "graph/op_user.py", "place")
OPC_PARAMS = dict(l5_concepts=OP_COPY)
# sink 꼴 = 영속 자리 종류 + 대상 식 문자열. 호출 sink 는 호출 식 전체(공백 정규화), 대입 sink 는 대상 식. 픽스처 소스를 읽고 손으로 적었다.
F_POINT = "write:snapshot.write('lay', 'iv', {('graph', 'ly_point'): {'m1': row}})"
F_I2 = "write:snapshot.write('lay', 'i2', {('graph', 'ly_i'): {'m1': op.current}})"
F_SAVED = "attr:snapshot.ctx.saved"


def _op(fid, **kw):
    return check_rule_l(root(fid), params(**OPC_PARAMS, **kw))


def test_rule_l_op_copy_reports_caught_field_paths():
    """(칸 경로, sink 꼴) 쌍 출력: 객체의 `current` 칸이 닿으면 ('current',), 정본 값 전체가 닿으면 ()이다. 위반 키는 interface 키 꼴 그대로.
    oracle (a): L5p-path-field 는 Row(current=동작점 값, n=상수)를 묶음째 쓴다 -> 오염된 칸은 current 하나, 자리는 그 write 호출.
    L5p-path-two 는 더해서 값 자체를 다른 write 로 쓴다 -> 쌍이 둘."""
    one = _op("L5p-path-field")
    assert [(v.key, v.paths, v.sinks) for v in one] == [(PLACE, (("current",),), ((("current",), F_POINT),))]
    two = _op("L5p-path-two")
    assert [(v.key, v.paths, v.sinks) for v in two] == [(PLACE, ((), ("current",)), (((), F_I2), (("current",), F_POINT)))]


def test_rule_l_op_copy_reports_callee_made_copy_path_and_caller_sink_form():
    """사본을 만든 피호출(`_row`)의 칸 경로는 피호출이 돌려준 칸이고, 지역 sink 가 없는 키의 sink 꼴은 호출자의 것이다.
    oracle (a): L5b-1 의 `_row` 는 Row(current=...)를 돌려주기만 하고(저장 없음) `place` 가 write 로 쓴다."""
    got = {v.key: (v.paths, v.sinks) for v in _op("L5b-1", output_functions=())}
    assert got[("L-5", "op_copy", "graph/op_user.py", "_row")] == ((("current",),), ((("current",), F_POINT),))
    assert got[PLACE] == (((),), (((), F_POINT),))


def _row(path, form, key=PLACE, ref="graph/op_user.py:12"):
    return (key, path, form, ref)


def test_rule_l_op_copy_cleared_row_hides_only_listed_pair():
    """표 행이 (키, 칸 경로, sink 꼴)을 가린다. 구성: path-field 는 (('current',), F_POINT) 하나만 잡힌다 -> 그 행이면 위반 0."""
    assert _op("L5p-path-field", op_copy_cleared=(_row(("current",), F_POINT),)) == ()


def test_rule_l_op_copy_cleared_source_whitespace_is_normalized():
    """행의 sink 꼴은 소스 공백을 정규화해 비교한다. 구성: 같은 꼴에 공백을 늘려 적어도 가려진다."""
    spaced = "write:snapshot.write('lay',   'iv',   {('graph', 'ly_point'):  {'m1': row}})"
    assert _op("L5p-path-field", op_copy_cleared=(_row(("current",), spaced),)) == ()


def test_rule_l_op_copy_cleared_new_path_still_violation():
    """새 칸 경로 = 위반. 구성: path-two 는 ((), F_I2) 와 (('current',), F_POINT) 둘이 잡힌다. 둘째 행만 있으면 첫째 쌍이 남는다."""
    got = _op("L5p-path-two", op_copy_cleared=(_row(("current",), F_POINT),))
    assert [(v.key, v.code, v.paths, v.sinks) for v in got] == [(PLACE, "op_copy", ((),), (((), F_I2),))]


def test_rule_l_op_copy_cleared_new_sink_form_same_path_still_violation():
    """새 sink 꼴 = 위반(칸 경로가 같아도). 구성: L5q-two-forms 는 같은 Row 를 write 에도 쓰고 `snapshot.ctx.saved` 속성에도 담는다 ->
    쌍 둘 (('current',), F_POINT), (('current',), F_SAVED). write 행만 적으면 속성 쌍이 위반으로 남는다."""
    both = _op("L5q-two-forms")
    assert [(v.key, v.sinks) for v in both] == [(PLACE, ((("current",), F_SAVED), (("current",), F_POINT)))]
    got = _op("L5q-two-forms", op_copy_cleared=(_row(("current",), F_POINT),))
    assert [(v.key, v.code, v.sinks) for v in got] == [(PLACE, "op_copy", ((("current",), F_SAVED),))]


def test_rule_l_op_copy_cleared_whole_copy_new_sink_not_hidden_by_empty_path_row():
    """같은 함수에 진짜 새 사본을 통째(경로 ()) 저장하면 새 sink 꼴이라 잡힌다. 구성: L5q-whole-copy 는 `op.current` 를 write(경로 ())하고
    `snapshot.ctx.saved = op` 로 객체 전체를 담는다(경로 ()). 표가 첫째 쌍만 적었으면 둘째가 남는다 -- 경로 ()가 키 전체를 덮지 않는다."""
    got = _op("L5q-whole-copy", op_copy_cleared=(_row((), F_I2),))
    assert [(v.key, v.code, v.sinks) for v in got] == [(PLACE, "op_copy", (((), F_SAVED),))]
    assert _op("L5q-whole-copy", op_copy_cleared=(_row((), F_I2), _row((), F_SAVED))) == ()


def test_rule_l_op_copy_cleared_callee_made_copy_is_compared_by_caller_sink_form():
    """지역 sink 가 없는 키는 호출자 sink 꼴로 비교한다. 구성: L5b-1 의 `_row`(저장 없음)는 호출자 `place` 의 write 꼴로만 가려진다."""
    row_key = ("L-5", "op_copy", "graph/op_user.py", "_row")
    rows = (_row(("current",), F_POINT, key=row_key), _row((), F_POINT))
    assert _op("L5b-1", output_functions=(), op_copy_cleared=rows) == ()
    wrong = (_row(("current",), "write:snapshot.write('other')", key=row_key), _row((), F_POINT))
    got = _op("L5b-1", output_functions=(), op_copy_cleared=wrong)
    assert sorted((v.key, v.code) for v in got) == sorted([(("L-5", "op_copy_cleared", "graph/op_user.py", "_row"), "op_copy_cleared_stale"),
                                                           (row_key, "op_copy")])


def test_rule_l_op_copy_cleared_row_for_other_key_hides_nothing():
    """행의 키가 다르면 가리지 않는다. 구성: 키의 함수 이름만 다른 행(`other`)은 place 를 가리지 못하고, 자기는 낡은 항목이다."""
    other = ("L-5", "op_copy", "graph/op_user.py", "other")
    got = _op("L5p-path-field", op_copy_cleared=(_row(("current",), F_POINT, key=other),))
    assert sorted((v.key, v.code) for v in got) == sorted([(("L-5", "op_copy_cleared", "graph/op_user.py", "other"), "op_copy_cleared_stale"),
                                                           (PLACE, "op_copy")])


def test_rule_l_op_copy_cleared_stale_row_is_violation():
    """잡히지 않는 행 = 위반(op_copy_cleared_stale). 구성: (('current',), F_POINT) 는 잡히지만 칸 경로가 다른 행과 sink 꼴이 다른 행은 잡히지 않는다
    -> 낡은 행 둘이 한 위반(키는 op_copy 와 다르다)으로 나온다."""
    rows = (_row(("current",), F_POINT), _row(("n",), F_POINT), _row(("current",), "attr:snapshot.ctx.gone"))
    got = _op("L5p-path-field", op_copy_cleared=rows)
    assert [(v.key, v.code, v.paths, v.sinks) for v in got] == [
        (("L-5", "op_copy_cleared", "graph/op_user.py", "place"), "op_copy_cleared_stale", (("current",), ("n",)),
         ((("current",), "attr:snapshot.ctx.gone"), (("n",), F_POINT)))]


def test_rule_l_op_copy_cleared_stale_when_nothing_caught():
    """깨끗한 트리에 행이 있으면 모두 낡은 항목이다. 구성: L5g-clean 은 위반 0 이므로 어떤 행도 가릴 것이 없다."""
    row = _row((), "attr:x", key=("L-5", "op_copy", "graph/op_user.py", "lay"))
    got = _op("L5g-clean", op_copy_cleared=(row,))
    assert [(v.key, v.code) for v in got] == [(("L-5", "op_copy_cleared", "graph/op_user.py", "lay"), "op_copy_cleared_stale")]


def test_rule_l_op_copy_cleared_default_empty_changes_nothing():
    """표가 비면(기본) 행 없는 호출과 같다. 구성: 같은 트리, 행 인자 유무."""
    assert _op("L5p-path-field") == _op("L5p-path-field", op_copy_cleared=())
    assert len(_op("L5p-path-field")) == 1


@pytest.mark.parametrize("row", [
    (PLACE, ("current",), "ref"),                                  # sink 꼴 칸이 없는 옛 3칸 행
    (PLACE, ("current",), F_POINT, "ref", "extra"),
])
def test_rule_l_op_copy_cleared_malformed_row_is_rejected(row):
    """행 모양이 (키, 칸 경로, sink 꼴, 근거) 넷이 아니면 조용히 넘기지 않고 거부한다. 구성: 칸 수가 모자라거나 넘치는 행."""
    with pytest.raises(ValueError):
        _op("L5p-path-field", op_copy_cleared=(row,))


def test_rule_l_fingerprint_includes_op_copy_cleared(tmp_path):
    """표는 지문 대상이다: 행 하나가 늘면 지문이 바뀌고 sink 꼴만 달라도 바뀐다(N3.1-6 (d)). 구성: 같은 입력에서 행만 다르다."""
    c, t = _fp_inputs(tmp_path)
    base = fingerprint(PARAMS, c, t)
    changed = fingerprint(PARAMS._replace(op_copy_cleared=((PLACE, ("current",), F_POINT, "graph/op_user.py:12"),)), c, t)
    assert changed != base
    other_path = fingerprint(PARAMS._replace(op_copy_cleared=((PLACE, ("n",), F_POINT, "graph/op_user.py:12"),)), c, t)
    assert other_path != changed
    other_form = fingerprint(PARAMS._replace(op_copy_cleared=((PLACE, ("current",), F_I2, "graph/op_user.py:12"),)), c, t)
    assert other_form != changed


# ---------------------------------------------------------------- GC-1 f3: 손 분류 표를 데이터 파일로(rule_l_op_copy_cleared.json)

GOOD_ROW_JSON = b'[[["L-5","op_copy","graph/op_user.py","place"],["current"],"%s","graph/op_user.py:12"]]\n'


def test_rule_l_op_copy_cleared_file_name_is_fixed_and_params_read_it():
    """표 데이터 파일은 tables 와 같은 폴더의 `rule_l_op_copy_cleared.json` 이고(두 모듈의 상수가 같다), PARAMS.op_copy_cleared 는 그 파일을 읽은 것이다.
    구성: 이름은 interface 가 정한 리터럴로 손으로 적었고, 파일 내용 비교는 loader 를 같은 파일에 다시 부른 값과 한다(행 내용은 검증자 몫이라 비어 있다고 단언하지 않는다)."""
    import rule_l_checks
    import rule_l_tables
    assert CLEARED_FILE == CLEARED_NAME == rule_l_checks.CLEARED_FILE
    path = Path(rule_l_tables.__file__).with_name(CLEARED_NAME)
    assert path.is_file()
    assert load_op_copy_cleared(path) == PARAMS.op_copy_cleared
    assert isinstance(PARAMS.op_copy_cleared, tuple)


def test_rule_l_op_copy_cleared_loader_returns_tuple_rows_that_hide_the_pair(tmp_path):
    """파일 행(목록)이 tuple 행이 되어 표와 같이 가린다. 구성: path-field 는 (('current',), F_POINT) 하나만 잡히므로 그 행을 파일에서 읽으면 위반 0이고,
    같은 행의 sink 꼴을 다르게 쓴 파일이면 가려지지 않아 위반 하나와 낡은 행 하나가 나온다."""
    f = tmp_path / CLEARED_NAME
    f.write_bytes(GOOD_ROW_JSON % F_POINT.encode("utf-8"))        # F_POINT 에 큰따옴표가 없어 JSON 문자열로 그대로 들어간다
    rows = load_op_copy_cleared(f)
    assert rows == ((PLACE, ("current",), F_POINT, "graph/op_user.py:12"),)
    assert _op("L5p-path-field", op_copy_cleared=rows) == ()
    f.write_bytes(GOOD_ROW_JSON % b"write:snapshot.write('other')")
    other = _op("L5p-path-field", op_copy_cleared=load_op_copy_cleared(f))
    assert sorted((v.key, v.code) for v in other) == sorted([(PLACE, "op_copy"), (("L-5", "op_copy_cleared", "graph/op_user.py", "place"),
                                                                                   "op_copy_cleared_stale")])


def test_rule_l_op_copy_cleared_empty_file_is_accepted(tmp_path):
    """빈 목록(시작 상태)은 받아들여 빈 tuple 이 된다. 구성: `[]` 만 있는 파일."""
    f = tmp_path / CLEARED_NAME
    f.write_bytes(b"[]\n")
    assert load_op_copy_cleared(f) == ()


def test_rule_l_op_copy_cleared_missing_file_is_rejected(tmp_path):
    """파일이 없으면 빈 표로 넘어가지 않고 거부한다(fail-closed). 구성: 존재하지 않는 경로."""
    with pytest.raises(FileNotFoundError):
        load_op_copy_cleared(tmp_path / CLEARED_NAME)


@pytest.mark.parametrize("raw", [
    b"",                                                               # 빈 파일
    b"not json",                                                       # JSON 아님
    b'{"rows": []}',                                                   # 최상위가 목록이 아님
    b'\xff\xfe\x00',                                                   # UTF-8 아님
    b'[[["L-5","op_copy","a.py","f"],["current"],"form"]]',            # 3칸 행
    b'[[["L-5","op_copy","a.py","f"],["current"],"form","ref","x"]]',  # 5칸 행
    b'[["L-5 op_copy",["current"],"form","ref"]]',                     # 위반 키가 목록이 아니라 문자열
    b'[[["L-5","op_copy","a.py","f"],"current","form","ref"]]',        # 칸 경로가 목록이 아님
    b'[[["L-5","op_copy","a.py","f"],["current",1],"form","ref"]]',    # 칸 경로 원소가 문자열이 아님
    b'[[["L-5",7,"a.py","f"],["current"],"form","ref"]]',              # 키 원소가 문자열이 아님
    b'[[["L-5","op_copy","a.py","f"],["current"],["form"],"ref"]]',    # sink 꼴이 문자열이 아님
    b'[[["L-5","op_copy","a.py","f"],["current"],"form",null]]',       # 근거가 문자열이 아님
    b'[null]',                                                         # 행이 목록이 아님
])
def test_rule_l_op_copy_cleared_malformed_file_is_rejected(tmp_path, raw):
    """모양이 틀린 파일은 조용히 넘기지 않고 ValueError 로 거부한다. 구성: 최상위·행 칸 수·칸 자료형을 하나씩 어긴 입력."""
    f = tmp_path / CLEARED_NAME
    f.write_bytes(raw)
    with pytest.raises(ValueError):
        load_op_copy_cleared(f)


def test_rule_l_fingerprint_includes_op_copy_cleared_file_bytes(tmp_path):
    """표 데이터 파일의 바이트는 지문 대상이다. 구성: 행으로 읽으면 같은 두 파일(`[]` 대 `[ ]`)도 지문이 다르다(파싱 값이 아니라 바이트),
    줄바꿈 CRLF 대 LF는 같다. 파일 한 글자 변경, 같은 폴더 기본 위치 대 명시 경로가 같은 값을 낸다."""
    a = tmp_path / "a"
    b = tmp_path / "b"
    c_ = tmp_path / "c"
    for d in (a, b, c_):
        d.mkdir()
    ca, ta = _fp_inputs(a, cleared=b"[]\n")
    cb, tb = _fp_inputs(b, cleared=b"[ ]\n")
    cc, tc = _fp_inputs(c_, cleared=b"[]\r\n")
    base = fingerprint(PARAMS, ca, ta)
    assert fingerprint(PARAMS, cb, tb) != base
    assert fingerprint(PARAMS, cc, tc) == base
    assert fingerprint(PARAMS, ca, ta, a / CLEARED_NAME) == base
    assert fingerprint(PARAMS, ca, ta, b / CLEARED_NAME) == fingerprint(PARAMS, cb, tb)


def test_rule_l_fingerprint_missing_op_copy_cleared_file_is_rejected(tmp_path):
    """표 데이터 파일이 없으면 지문을 만들지 않고 거부한다(빈 표로 넘어가면 같은 지문이 나올 수 있다). 구성: 파일을 지운다."""
    c, t = _fp_inputs(tmp_path)
    (tmp_path / CLEARED_NAME).unlink()
    with pytest.raises(FileNotFoundError):
        fingerprint(PARAMS, c, t)


def test_rule_l_fingerprint_covers_every_listed_input(tmp_path):
    """지문 대상 목록을 고정한다: checks 바이트, tables 바이트, 표 데이터 파일 바이트, PARAMS(표 행 포함) 각각이 하나라도 바뀌면 지문이 바뀐다.
    구성: 서로 다른 입력 5개의 지문이 모두 다르다."""
    dirs = [tmp_path / n for n in "pqrs"]
    for d in dirs:
        d.mkdir()
    c0, t0 = _fp_inputs(dirs[0])
    c1, t1 = _fp_inputs(dirs[1], checks=b"a = 2\n")
    c2, t2 = _fp_inputs(dirs[2], tables=b"b = 3\n")
    c3, t3 = _fp_inputs(dirs[3], cleared=b"[ ]\n")
    fps = {fingerprint(PARAMS, c0, t0), fingerprint(PARAMS, c1, t1), fingerprint(PARAMS, c2, t2), fingerprint(PARAMS, c3, t3),
           fingerprint(PARAMS._replace(op_copy_cleared=((PLACE, ("n",), F_POINT, "r"),)), c0, t0)}
    assert len(fps) == 5


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
    """허용 목록 금지(O-241): 이름으로 면제·직렬화를 가르던 상수와 외부 수신자 면제가 도구에 없고, 닫힌 목록은 내용 자체가 고정돼 있다.
    oracle (d): 목록 내용은 사용자가 선언한 '값을 보관하지 않음이 언어 정의로 확정된 내장' 한정(N3.1-5)이라 손으로 적었다. 목록에 이름 하나를 더하면(print·setattr 등)
    이 test 가 실패한다 -- 목록 변경은 기준 변경(N3.1-6 (e))이다.
    구성: rule_l_checks 의 최상위 이름과 클래스 메서드 이름을 AST 로 보고, 닫힌 목록 상수를 리터럴과 비교한다."""
    import ast
    import rule_l_checks as m
    tree = ast.parse(Path(m.__file__).read_text(encoding="utf-8"))
    names = {t.id for n in ast.walk(tree) if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
    names |= {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert not names & {"BENIGN_METHODS", "SERIALIZERS", "_ext_receiver"}
    assert m.BUILTIN_PURE_FUNCS == frozenset({"abs", "all", "any", "bin", "callable", "chr", "divmod", "hasattr", "hash", "hex", "id", "isinstance",
                                              "issubclass", "len", "oct", "ord", "pow", "range", "round", "sum"})
    assert m.BUILTIN_FLOW_FUNCS == frozenset({"float", "int", "str", "bool", "dict", "tuple", "list", "set", "frozenset", "sorted", "reversed",
                                              "getattr", "min", "max", "zip", "enumerate", "iter", "next", "filter", "map"})
    assert m.BUILTIN_TYPE_METHODS == {
        "str": frozenset({"capitalize", "casefold", "center", "count", "encode", "endswith", "expandtabs", "find", "format", "format_map", "index",
                          "isalnum", "isalpha", "isascii", "isdecimal", "isdigit", "isidentifier", "islower", "isnumeric", "isprintable",
                          "isspace", "istitle", "isupper", "join", "ljust", "lower", "lstrip", "partition", "removeprefix", "removesuffix",
                          "replace", "rfind", "rindex", "rjust", "rpartition", "rsplit", "rstrip", "split", "splitlines", "startswith", "strip",
                          "swapcase", "title", "translate", "upper", "zfill"}),
        "list": frozenset({"clear", "copy", "count", "index", "pop", "remove", "reverse", "sort"}),
        "dict": frozenset({"clear", "copy", "get", "items", "keys", "pop", "popitem", "values"}),
        "set": frozenset({"clear", "copy", "difference", "discard", "intersection", "isdisjoint", "issubset", "issuperset", "pop", "remove",
                          "symmetric_difference", "union"}),
        "tuple": frozenset({"count", "index"}),
    }
    assert m.BUILTIN_TYPE_ADD == {"list": frozenset({"append", "extend", "insert"}), "dict": frozenset({"setdefault", "update"}),
                                  "set": frozenset({"add", "update"})}
    assert m._NONFLOW_METHODS == frozenset({"count", "endswith", "find", "index", "isalnum", "isalpha", "isascii", "isdecimal", "isdigit",
                                            "isidentifier", "islower", "isnumeric", "isprintable", "isspace", "istitle", "isupper", "isdisjoint",
                                            "issubset", "issuperset", "rfind", "rindex", "startswith"})
    assert m._SAFE_DECORATORS == frozenset({"staticmethod", "classmethod", "property", "abstractmethod", "setter", "getter", "deleter"})
    assert m._DATACLASS_DECORATORS == frozenset({"dataclass"})
    assert m.SRC_BASES == frozenset({"S", "SP", "SD"})


# ---------------------------------------------------------------- O-241 재판정 M-5: 모델 밖 구문은 기본이 위반(fail-closed 뿌리)
# 소스를 test 안에서 짠다(기본 트리 = L5b-1: op_block 이 device.dc_op 를 쓰는 블록, stage_a 가 place(snapshot) 를 부른다).
# 기대 = 사본 자리 함수 한정 이름 목록. 출처 값이 변형 없이 영속 자리에 닿거나 추적이 끊기면 그 함수가 위반이고, 산술로 끊기거나 지역 임시 묶음이면 위반 0이다.
# 기대는 N3.1-5 '사본의 정의'·'fail-closed'에서 손으로 적었다(도구 출력을 옮긴 것이 아니다). oracle (a).
BASE_TREE = FIX / "L5b-1" / "gmid_engine"
OPV = 'op = snapshot.value("device", "m1", "dc_op")\n'
COL = 'ops = dict(snapshot.column("device", "dc_op"))\n'
WRT = 'return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": v}})\n'
GLB = "STORE = []\n\n\n"
BLOCK_KEEP = ('from gmid_engine.core.compute_block import compute_block\n\n\n@compute_block("keep", reads=(), writes=(("graph", "k"),))\n'
              'def keep_block(projection):\n    (v,) = projection.extras\n    return {("graph", "k"): {"g": v}}\n\n\n')


ASYNC_HEAD = ("async def f(x):\n    return x\n\n\nasync def g(snapshot):\n    " + OPV + "    v = await f(op.current)\n    " + WRT + "\n\n")

# (id, 함수 앞 정의, place 본문(줄마다 함수 본문 기준 상대 들여쓰기), 기대 사본 자리 함수들)
SHAPES = [
    # BUILTIN_FLOW_FUNCS: 전 인자 라벨을 합쳐 넘긴다
    ("flow_max", "", [OPV, "v = max(op.current, 0.0)\n", WRT], ["place"]),
    ("flow_min_one", "", [COL, "v = min(ops.values(), key=id).current\n", WRT], ["place"]),
    ("flow_next_iter", "", [COL, "v = next(iter(ops.values())).current\n", WRT], ["place"]),
    ("flow_enumerate", "", [COL, "for _i, o in enumerate(ops.values()):\n    v = o.current\n", WRT], ["place"]),
    ("flow_zip", "", [COL, 'for o, _n in zip(ops.values(), ("a",)):\n    v = o.current\n', WRT], ["place"]),
    ("flow_zip_write", "", [COL, "v = dict(zip(ops, ops.values()))\n", WRT], ["place"]),
    ("flow_filter", "", [COL, "v = tuple(filter(None, ops.values()))\n", WRT], ["place"]),
    # 콜백 인자: 따라갈 수 없으면 sink
    ("flow_map_engine", GLB + "def _keep(o):\n    STORE.append(o.current)\n\n\n", [COL, "v = list(map(_keep, ops.values()))\n", WRT], ["place"]),
    ("flow_map_ext", "", [COL, "v = list(map(snapshot.ctx.rows.append, ops.values()))\n", WRT], ["place"]),
    ("flow_sorted_key_cb", "", [COL, "v = sorted(ops.values(), key=snapshot.ctx.rows.append)\n", WRT], ["place"]),
    ("flow_iter_store", "", [COL, "snapshot.ctx.it = iter(ops.values())\nv = 1.0\n", WRT], ["place"]),
    ("min_key_engine", GLB + "def _keep(o):\n    STORE.append(o)\n    return 0\n\n\n", [OPV, "min([op], key=_keep)\nv = 1.0\n", WRT], ["place"]),
    ("lambda_param_map", "", [COL, "v = list(map(lambda o: o.current, ops.values()))\n", WRT], ["place"]),
    # 값 열을 이름에 담아 도는 루프·컴프리헨션, 두 칸 풀기의 왼쪽
    ("loop_list_values", "", [COL, "for o in list(ops.values()):\n    snapshot.ctx.rows.append(o.current)\nv = 1.0\n", WRT], ["place"]),
    ("loop_named_values", "", [COL, "vals = tuple(ops.values())\nfor o in vals:\n    snapshot.ctx.rows.append(o.current)\nv = 1.0\n", WRT], ["place"]),
    ("comp_named_values", "", [COL, "vals = tuple(ops.values())\nv = tuple(o.current for o in vals)\n", WRT], ["place"]),
    ("loop_pair_left", "", [OPV, 'for o, _n in [(op, "m1")]:\n    v = o.current\n', WRT], ["place"]),
    # 클로저·람다: 바깥 함수 변수 조회
    ("closure_read", "", [OPV, "def g():\n    return op.current\nv = g()\n", WRT], ["place", "place.g"]),
    ("closure_store", "", [OPV, "def g():\n    snapshot.ctx.rows.append(op.current)\ng()\nv = 1.0\n", WRT], ["place.g"]),
    ("lambda_immediate", "", [OPV, "v = (lambda: op.current)()\n", WRT], ["place"]),
    ("lambda_store", "", [OPV, "f = lambda: snapshot.ctx.rows.append(op.current)\nf()\nv = 1.0\n", WRT], ["place"]),
    ("once_cache", "", [OPV, 'cache = {}\ndef once(k, make):\n    cache[k] = make()\n    return cache[k]\nv = once("a", lambda: op.current)\n', WRT],
     ["place", "place.once"]),
    # with as, 워러스, match, raise
    ("with_as", "import contextlib\n@contextlib.contextmanager\ndef hold(x):\n    yield x\n\n\n",
     [OPV, "with hold(op) as h:\n    v = h.current\n", WRT], ["place"]),
    ("walrus", "", [OPV, "if (v := op.current) > 0:\n    pass\n", WRT], ["place"]),
    ("walrus_store", "", ['if (op := snapshot.value("device", "m1", "dc_op")) is not None:\n    v = op.current\n', WRT], ["place"]),
    ("match_case", "", [OPV, "match op:\n    case x:\n        v = x.current\n", WRT], ["place"]),
    ("except_as_none", "", [OPV, "v = op.current if op else None\n", WRT], ["place"]),
    ("exc_detail", "class Bad(Exception):\n    pass\n\n\n", [OPV, "raise Bad(op.current)\n"], ["place"]),
    ("exc_kw_helper", "def fail(**detail):\n    return ValueError(detail)\n\n\n", [OPV, "raise fail(value=float(op.vds))\n"], ["place"]),
    # *args·**kwargs, 생성자 본문, 장식된 함수, 블록 extras
    ("star_args", GLB + "def keep(*a):\n    STORE.append(a)\n\n\n", [OPV, "keep(op.current)\nv = 1.0\n", WRT], ["place"]),
    ("star_kwargs", GLB + "def keep(**k):\n    STORE.append(k)\n\n\n", [OPV, "keep(i=op.current)\nv = 1.0\n", WRT], ["place"]),
    ("star_args_ret", "def keep(*a):\n    return a\n\n\n", [OPV, "v = keep(op.current)\n", WRT], ["place"]),
    ("default_kw_ret", 'def keep(x=None, **k):\n    return k["i"]\n\n\n', [OPV, "v = keep(i=op.current)\n", WRT], ["place"]),
    ("init_stores_global", GLB + "class K:\n    def __init__(self, x):\n        STORE.append(x)\n\n\n", [OPV, "K(op.current)\nv = 1.0\n", WRT], ["K.__init__"]),
    ("post_init_store", "import dataclasses\n" + GLB + "@dataclasses.dataclass\nclass K:\n    x: float\n    def __post_init__(self):\n        STORE.append(self.x)\n\n\n",
     [OPV, "K(op.current)\nv = 1.0\n", WRT], ["place"]),
    ("ctor_no_args_via_star", "class R:\n    def __init__(self, *a):\n        self.a = a\n\n\n", [OPV, "v = R(op.current)\n", WRT], ["place"]),
    ("lru_decorator", "import functools\n@functools.lru_cache(maxsize=None)\ndef f(x):\n    return 1.0\n\n\n", [OPV, "f(op.current)\nv = 1.0\n", WRT], ["place"]),
    ("block_extra", BLOCK_KEEP, [OPV, "return keep_block(snapshot, op.current)\n"], ["place"]),
    ("param_dict_called", 'def keep(cache, op):\n    cache["m1"] = op.current\n\n\n', [OPV, "keep(snapshot.ctx, op)\nv = 1.0\n", WRT], ["keep"]),
    # 값을 보관하거나 문자열로 옮기는 내장·서식은 목록에 없다
    ("type_3arg", "", [OPV, 'v = type("T", (), {"i": op.current})\n', WRT], ["place"]),
    ("str_flow", "", [OPV, "v = str(op.current)\n", WRT], ["place"]),
    ("repr_form", "", [OPV, "v = repr(op.current)\n", WRT], ["place"]),
    ("format_form", "", [OPV, "v = format(op.current)\n", WRT], ["place"]),
    ("ascii_form", "", [OPV, "v = ascii(op.current)\n", WRT], ["place"]),
    ("fstring_form", "", [OPV, 'v = f"{op.current}"\n', WRT], ["place"]),
    ("str_format_method", "", [OPV, 'v = "{}".format(op.current)\n', WRT], ["place"]),
    ("str_join_method", "", [OPV, 'v = ",".join([op.current])\n', WRT], ["place"]),
    ("dict_key", "", [OPV, "v = {op.current: 1}\n", WRT], ["place"]),
    ("dict_key_comp", "", [COL, "v = {o.current: 1 for o in ops.values()}\n", WRT], ["place"]),
    ("dict_kw_ctor", "", [OPV, "v = dict(i=op.current)\n", WRT], ["place"]),
    ("dict_merge_kw", "", [OPV, "v = dict({}, i=op.current)\n", WRT], ["place"]),
    ("set_value", "", [OPV, "v = {op.current}\n", WRT], ["place"]),
    ("print_file", "", [OPV, "print(op.current, file=snapshot.fh)\nv = 1.0\n", WRT], ["place"]),
    ("print_plain", "", [OPV, "print(op.current)\nv = 1.0\n", WRT], ["place"]),
    ("setattr_ctx", "", [OPV, 'setattr(snapshot.ctx, "x", op.current)\nv = 1.0\n', WRT], ["place"]),
    ("vars_op", "", [OPV, "v = vars(op)\n", WRT], ["place"]),
    ("slice_list", "", [COL, "v = list(ops.values())[0:1]\n", WRT], ["place"]),
    ("shadow_list_name", "class list:\n    def __init__(self, x):\n        STORE.append(x)\n\n\n" + GLB, [OPV, "list(op.current)\nv = 1.0\n", WRT],
     ["list.__init__"]),
    ("local_alias_add", "", [OPV, "rows = []\nother = rows\nother.append(op.current)\nsnapshot.ctx.k = rows\nv = 1.0\n", WRT], ["place"]),
    ("local_then_escape", "", [OPV, "rows = []\nsnapshot.ctx.k = rows\nrows.append(op.current)\nv = 1.0\n", WRT], ["place"]),
    ("nested_fresh", "", [OPV, 'rows = {"a": []}\nrows["a"].append(op.current)\nsnapshot.ctx.k = rows\nv = 1.0\n', WRT], ["place"]),
    ("param_append", "def keep(rows, op):\n    rows.append(op.current)\n\n\n", [OPV, "keep(snapshot.ctx.rows, op)\nv = 1.0\n", WRT], ["keep"]),
    # 매개변수는 형이 확정되지 않는다: 안에서 새 list 로 다시 묶는 갈래가 있어도 넘겨받은 컨테이너일 수 있다(Param-typed)
    ("param_append_reassigned", "def keep(rows, op):\n    if not rows:\n        rows = []\n    rows.append(op.current)\n\n\n",
     [OPV, "keep(snapshot.ctx.rows, op)\nv = 1.0\n", WRT], ["keep"]),
    # 출처를 알아보지 못하던 접근 꼴: 키워드 인자, 메서드 별칭, getattr, partial
    ("src_kw_field", "", ['op = snapshot.value("device", "m1", field="dc_op")\nv = op.current\n', WRT], ["place"]),
    ("src_kw_all", "", ['ops = snapshot.column(kind="device", field="dc_op")\nv = ops\n', WRT], ["place"]),
    ("src_alias_method", "", ['col = snapshot.column\nv = col("device", "dc_op")\n', WRT], ["place"]),
    ("src_getattr_method", "", ['v = getattr(snapshot, "column")("device", "dc_op")\n', WRT], ["place"]),
    ("src_partial", "import functools\n", ['col = functools.partial(snapshot.column, "device")\nv = col("dc_op")\n', WRT], ["place"]),
    # 새 구문도 기본이 위반: await 를 모델에 넣지 않았다
    ("await_expr", ASYNC_HEAD, ["g(snapshot)\nv = 1.0\n", WRT], ["g"]),
    # 대조: 산술·내장 산술·지역 임시 묶음·다른 칸·키 이름만은 위반이 아니다
    ("clean_arith", "", [OPV, "v = op.current * 2.0\n", WRT], []),
    ("clean_unary_compare", "", [OPV, "v = (-op.current, op.current > 0.0)\n", WRT], []),
    ("clean_temp_abs", "", [OPV, "v = abs(op.current)\n", WRT], []),
    ("clean_local_sum", "", [COL, "rows = []\nfor o in ops.values():\n    rows.append(o.current)\nv = sum(rows)\n", WRT], []),
    ("clean_ctor_other_slot", "class Row:\n    def __init__(self, i, n):\n        self.i = i\n        self.n = n\n\n\n", [OPV, "v = Row(op.current, 1.0).n\n", WRT], []),
    ("clean_names_only", "", [COL, "v = tuple(sorted(ops))\n", WRT], []),
    ("clean_pair_key_side", "", [COL, "v = [m for m, _o in sorted(ops.items())]\n", WRT], []),
    ("clean_key_callback_lambda", "", [COL, "v = len(sorted(ops.values(), key=lambda o: o.current))\n", WRT], []),
    # ---- GC-1 f3: 사본이 풀리지 않는 호출로 새는 꼴(두 층 점검의 주입 U1·U4·L2·X1). 호출 자체가 sink 이므로 한 층에서 잡힌다 ----
    # 기대는 소스를 읽고 손으로: 받는 함수가 넘겨받은 동작점 값을 풀리지 않는 호출(수신자 형 모름·외부 모듈)에 넘기므로 그 함수가 사본 자리다(호출자는 아니다).
    ("leak_sctx_slot_append", "def _stash(sctx, op_):\n    sctx.memo_slot.append(op_)\n\n\n", [OPV, "_stash(snapshot.ctx, op)\nv = 1.0\n", WRT], ["_stash"]),
    ("leak_s3_append_eval", 'def _rec(sctx, op_):\n    sctx.archive.append_eval({"vgs": op_.vgs})\n\n\n', [OPV, "_rec(snapshot.ctx, op)\nv = 1.0\n", WRT], ["_rec"]),
    ("leak_subscript_after_copy", "import copy\n\n\ndef _keep(x, k, op_):\n    x[k] = copy.copy(op_)\n\n\n",
     [OPV, '_keep(snapshot.ctx.cache, "m1", op)\nv = 1.0\n', WRT], ["_keep"]),
    ("leak_raise_detail_kw", "class Rejected(Exception):\n    pass\n\n\n", [OPV, 'raise Rejected(detail={"vgs": op.vgs})\n'], ["place"]),
    ("leak_raise_detail_via_param", "class Rejected(Exception):\n    pass\n\n\ndef _fail(detail):\n    raise Rejected(detail=detail)\n\n\n",
     [OPV, '_fail({"vgs": op.vgs})\n'], ["_fail"]),
    # ---- GC-1 f3: 튜플 풀기. 왼쪽 이름별로 자기 오른쪽 식의 라벨만 받는다(칸 수가 같고 `*` 없음). 기대는 대입의 의미(a, b = x, y 는 a = x; b = y)에서 손으로 ----
    # 거부: 오염된 칸을 받은 이름이 영속 자리에 닿는다(맨 앞, 맨 뒤, 중첩, 리스트 대상, 이름 하나에 여럿 풀기)
    ("unpack_first_name_leaks", "", [OPV, "a, b = op.current, 1.0\nsnapshot.ctx.k = a\nv = 1.0\n", WRT], ["place"]),
    ("unpack_second_name_leaks", "", [OPV, "a, b = 1.0, op.current\nsnapshot.ctx.k = b\nv = 1.0\n", WRT], ["place"]),
    ("unpack_nested_leaks", "", [OPV, "(a, b), c = (op.current, 1.0), 2.0\nsnapshot.ctx.k = a\nv = 1.0\n", WRT], ["place"]),
    ("unpack_nested_second_leaks", "", [OPV, "(a, b), c = (1.0, op.current), 2.0\nsnapshot.ctx.k = b\nv = 1.0\n", WRT], ["place"]),
    ("unpack_list_target_leaks", "", [OPV, "[a, b] = op.current, 1.0\nsnapshot.ctx.k = a\nv = 1.0\n", WRT], ["place"]),
    ("unpack_attr_leaf_leaks", "", [OPV, "snapshot.ctx.k, b = op.current, 1.0\nv = 1.0\n", WRT], ["place"]),
    ("unpack_subscript_leaf_leaks", "", [OPV, "snapshot.ctx.k[0], b = op.current, 1.0\nv = 1.0\n", WRT], ["place"]),
    # 거부: 오른쪽이 이름·호출·`*` 포함이면 짝지을 수 없으니 모든 이름이 오염을 받는다(모르는 꼴은 위반이라는 기본값)
    ("unpack_name_rhs_all_leak", "", [OPV, "pair = (op.current, 1.0)\na, b = pair\nsnapshot.ctx.k = b\nv = 1.0\n", WRT], ["place"]),
    ("unpack_call_rhs_all_leak", "def _two(x):\n    return x, 1.0\n\n\n", [OPV, "a, b = _two(op.current)\nsnapshot.ctx.k = b\nv = 1.0\n", WRT], ["place"]),
    ("unpack_starred_rhs_all_leak", "", [OPV, "a, b = (op.current, 1.0, 2.0)[:2]\nsnapshot.ctx.k = b\nv = 1.0\n", WRT], ["place"]),
    ("unpack_starred_target_all_leak", "", [OPV, "a, *b = op.current, 1.0, 2.0\nsnapshot.ctx.k = b\nv = 1.0\n", WRT], ["place"]),
    ("unpack_starred_value_all_leak", "", [OPV, "rest = (1.0, 2.0)\na, b, c = op.current, *rest\nsnapshot.ctx.k = c\nv = 1.0\n", WRT], ["place"]),
    # 거부: 풀기로 만든 지역 컨테이너도 호출·대입으로 빠져나가면 위반이고, 짝이 안 맞는 이름·다시 묶인 이름은 형이 확정되지 않는다
    ("unpack_local_container_escapes", "", [OPV, "rows, seen = [], {}\nrows.append(op.current)\nsnapshot.ctx.k = rows\nv = 1.0\n", WRT], ["place"]),
    ("unpack_untyped_partner_append", "", [OPV, "rows, other = [], snapshot.ctx.rows\nother.append(op.current)\nv = 1.0\n", WRT], ["place"]),
    ("unpack_unmatched_rhs_not_typed", "", [OPV, "rows, other = snapshot.ctx.pair\nrows.append(op.current)\nv = 1.0\n", WRT], ["place"]),
    ("unpack_rebound_not_typed", "", [OPV, "rows, other = [], []\nrows, other = snapshot.ctx.pair\nrows.append(op.current)\nv = 1.0\n", WRT], ["place"]),
    ("unpack_typed_then_loop_rebound", "", [OPV, "rows, other = [], []\nfor rows in snapshot.ctx.groups:\n    rows.append(op.current)\nv = 1.0\n", WRT], ["place"]),
    # 허용: 상수를 받은 이름은 깨끗하다(옛 합집합 라벨에서는 위반이었던 자리), 풀기로 만든 지역 컨테이너에만 담기, 산술로 끊김
    ("unpack_const_name_clean", "", [OPV, "a, b = op.current, 1.0\nsnapshot.ctx.k = b\nv = 1.0\n", WRT], []),
    ("unpack_const_first_clean", "", [OPV, "a, b = 1.0, op.current\nsnapshot.ctx.k = a\nv = 1.0\n", WRT], []),
    ("unpack_nested_other_clean", "", [OPV, "(a, b), c = (op.current, 1.0), 2.0\nsnapshot.ctx.k = (b, c)\nv = 1.0\n", WRT], []),
    ("unpack_arith_clean", "", [OPV, "a, b = op.current * 2.0, 1.0\nsnapshot.ctx.k = a\nv = 1.0\n", WRT], []),
    ("unpack_local_containers_clean", "", [OPV, "rows, seen = [], {}\nrows.append(op.current)\nseen[1] = op.current\nv = len(rows) + len(seen)\n", WRT], []),
    ("unpack_attr_leaf_other_clean", "", [OPV, "snapshot.ctx.k, b = 1.0, op.current\nv = 1.0\n", WRT], []),
]


def _shape_src(head, lines):
    body = "".join("    " + ln for ln in "".join(lines).splitlines(keepends=True))
    return head + "def place(snapshot):\n" + body


def _run_tree(tmp_path, op_user, p, extra=None):
    d = tmp_path / "gmid_engine"
    shutil.copytree(BASE_TREE, d, ignore=shutil.ignore_patterns("__pycache__"))
    (d / "graph" / "op_user.py").write_text(op_user, encoding="utf-8")
    for rel, text in (extra or {}).items():
        (d / rel).write_text(text, encoding="utf-8")
    return sorted((v.key[2], v.key[3]) for v in check_rule_l(d, p) if v.key[0] == "L-5")


@pytest.mark.parametrize("name", [s[0] for s in SHAPES])
def test_rule_l_op_copy_model_outside_shapes_are_violations(name, tmp_path):
    """주입 꼴 하나씩: 출처 값이 영속 자리에 닿거나 추적이 끊기는 꼴은 사본 자리 함수가 위반이고, 대조 꼴(산술·지역 임시 묶음·키 이름만)은 위반 0이다.
    oracle (a): 기대는 소스를 읽고 손으로 적었다(SHAPES 주석 참고)."""
    _, head, lines, want = next(s for s in SHAPES if s[0] == name)
    got = _run_tree(tmp_path, _shape_src(head, lines), params(**OPC_PARAMS))
    assert got == sorted(("graph/op_user.py", w) for w in want)


def test_rule_l_op_copy_output_function_graph_write_is_still_violation(tmp_path):
    """출력 함수 면제는 N3.1-5 (iii) 결과 JSON·보고 객체 자리뿐이다. 구성: 면제 목록에 있는 함수가 동작점 값을 graph 필드로 쓰면((i) 자리) 위반이다."""
    src = _shape_src("", [OPV, "v = op.current\n", WRT])
    p = params(**OPC_PARAMS, output_functions=("graph/op_user.py:place",))
    assert _run_tree(tmp_path, src, p) == [("graph/op_user.py", "place")]


def test_rule_l_op_copy_value_passed_to_output_function_that_stores_is_violation(tmp_path):
    """구성: 면제 목록에 있는 함수 `rep` 가 넘겨받은 동작점 값을 전역 목록에 저장한다((iv) 자리). 면제는 반환 객체뿐이라 저장하는 `rep` 가 위반이다."""
    head = GLB + "def rep(x):\n    STORE.append(x)\n\n\n"
    src = _shape_src(head, [OPV, "rep(op.current)\nv = 1.0\n", WRT])
    p = params(**OPC_PARAMS, output_functions=("graph/op_user.py:rep",))
    assert _run_tree(tmp_path, src, p) == [("graph/op_user.py", "rep")]


OP_BLOCK_WITH_HELPER = '''from ..core.compute_block import compute_block


@compute_block("op_block", reads=[], writes=[("device", "dc_op")])
def op_block(projection):
    return {("device", "dc_op"): {"m1": 1.0}}


STORE = []


def stash(snapshot):
    STORE.append(snapshot.value("device", "m1", "dc_op"))
'''


def test_rule_l_op_copy_writer_exemption_is_the_writing_block_only(tmp_path):
    """정본 쓰기 면제는 `device.dc_op` 를 쓰는 블록 자신이다(writer 파일 전체가 아니다). 구성: 같은 파일의 블록 아닌 함수 `stash` 가 dc_op 를 읽어
    전역에 저장하면 위반이다. 블록 자신의 같은 읽기·저장은 L5i-writer 가 clean 으로 둔다."""
    src = "from .op_block import stash\n\n\ndef place(snapshot):\n    stash(snapshot)\n    v = 1.0\n    " + WRT
    got = _run_tree(tmp_path, src, params(**OPC_PARAMS), extra={"graph/op_block.py": OP_BLOCK_WITH_HELPER})
    assert got == [("graph/op_block.py", "stash")]
