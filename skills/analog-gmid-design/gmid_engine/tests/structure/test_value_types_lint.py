"""GL-1 설계 값 타입 lint `check_value_types`: 목록 타입 주석(vt_annotation)과 대입(vt_assign).

oracle 종류 (d): 사용자가 선언한 계약(interface card 20261103-gl1 §2, design 40 §2.4.10 ②).
기대 목록은 fixtures/rule_vt/bad 소스의 줄을 손으로 읽어 적은 것이다(검사기 출력을 옮기지 않았다).
목록 타입 = `@dataclass(frozen=True)` / `@dataclasses.dataclass(frozen=True)` 클래스(valtypes.py의 Pt, Zed, Holder,
core/graph_snapshot.py의 OnlyAllowed). 일반 @dataclass(Loose)·frozen=False(NotFrozen)·NamedTuple(Named)은 목록이 아니다.
"""
from __future__ import annotations

# (kind, path, line, detail)
EXPECTED_VT_BAD = [
    # use.py -- 모듈 수준 주석. detail = 이름:T
    ("vt_annotation", "use.py", 6, "A:Pt"),         # A: Pt
    ("vt_annotation", "use.py", 7, "B:Pt"),         # tuple[Pt, ...]
    ("vt_annotation", "use.py", 8, "C:Zed"),        # dict[str, Zed]
    ("vt_annotation", "use.py", 9, "D:Holder"),     # Optional[Holder]
    ("vt_annotation", "use.py", 10, "E:Pt"),        # 문자열 주석 "Pt"
    ("vt_annotation", "use.py", 11, "F:Pt"),        # mod.Pt
    ("vt_annotation", "use.py", 16, "K:Pt"),        # K: Pt = Pt(1.0) -- 둘 다 해당, vt_annotation 하나만
    ("vt_annotation", "use.py", 17, "L:Holder"),    # tuple[Zed, Pt, Holder] -- 이름 오름차순 첫째 Holder
    #   (G int, H Loose, I Named, J tuple[int, ...], M NotFrozen 은 없다)
    # assign.py -- 모듈 수준 대입
    ("vt_assign", "assign.py", 4, "a:Pt"),          # Pt(1.0)
    ("vt_assign", "assign.py", 5, "b:Pt"),          # (Pt(1.0), 2)
    ("vt_assign", "assign.py", 6, "c:Pt"),          # [Pt(1.0)]
    ("vt_assign", "assign.py", 7, "d:Pt"),          # {Pt(1.0)}
    ("vt_assign", "assign.py", 8, "e:Pt"),          # {"k": Pt(1.0)} 값
    ("vt_assign", "assign.py", 9, "f:Zed"),         # {Zed(1.0): 1} 키
    ("vt_assign", "assign.py", 10, "g:Pt"),         # 리스트 컴프리헨션
    ("vt_assign", "assign.py", 11, "h:Pt"),         # 제너레이터
    ("vt_assign", "assign.py", 12, "i:Pt"),         # tuple(제너레이터)
    ("vt_assign", "assign.py", 13, "j:Pt"),         # frozenset(제너레이터)
    ("vt_assign", "assign.py", 14, "k:Pt"),         # list(제너레이터)
    ("vt_assign", "assign.py", 20, "q:Zed"),        # {i: Zed(1.0) for ...} dict 컴프리헨션
    ("vt_assign", "assign.py", 21, "r:Pt"),         # {Zed(1.0), Pt(2.0)} -- 이름 오름차순 첫째 Pt
    #   (l Loose(1), m 3, n (1, 2), o = Pt, p [Loose(1)], s 원시 tuple 은 없다)
    # places.py -- 클래스 본문과 메서드 안 self.a. detail = 클래스.a:T
    ("vt_annotation", "places.py", 7, "Loose2.a:Pt"),     # frozen 아닌 클래스 본문 a: Pt
    ("vt_annotation", "places.py", 8, "Loose2.b:Zed"),    # tuple[Zed, ...]
    ("vt_assign", "places.py", 9, "Loose2.c:Pt"),         # c = Pt(1.0)
    ("vt_annotation", "places.py", 13, "Loose2.p:Pt"),    # 메서드 안 self.p: Pt = x
    ("vt_assign", "places.py", 14, "Loose2.q:Pt"),        # self.q = Pt(1.0)
    ("vt_assign", "places.py", 15, "Loose2.r:Zed"),       # self.r = [Zed(1.0)]
    ("vt_annotation", "places.py", 23, "Plain.v:Zed"),    # v: Zed
    ("vt_assign", "places.py", 24, "Plain.w:Pt"),         # w = (Pt(1.0), Pt(2.0))
    #   (d: int, self.s = 3, 지역 t: Pt·u = Pt(1.0), 반환값 Pt(1.0), 함수 인자·반환 주석·지역 변수는 없다)
    # 허용 모듈 밖: 목록 타입의 정의가 허용 모듈 안이어도 타입 이름은 목록에 든다
    ("vt_annotation", "use2.py", 3, "Y:OnlyAllowed"),
    ("vt_annotation", "metrics/run_counters.py", 3, "X:Pt"),  # 같은 이름이 다른 폴더면 허용 아님
]
# core/graph_snapshot.py(허용 모듈)는 `BAD: Pt = None`, `BAD2 = Pt(1.0)`를 담지만 위 목록에 없다.
# valtypes.py의 frozen 본문(Holder.p: Pt, Holder.q: tuple[Zed, ...])도 없다.


def _keys(violations):
    return [(v.kind, v.path, v.line, v.detail) for v in violations]


def test_value_types_rejects_bad_fixture_exactly(checks, fixture_tree, report):
    n, v = checks.check_value_types(fixture_tree("rule_vt", "bad"))
    report(n, len(v))
    # 대상 파일: valtypes, use, assign, places, core/graph_snapshot, metrics/run_counters, use2
    assert n == 7
    assert _keys(v) == sorted(EXPECTED_VT_BAD), "\n".join(str(x) for x in v)


def test_value_types_allowed_module_emits_nothing(checks, fixture_tree):
    _, v = checks.check_value_types(fixture_tree("rule_vt", "bad"))
    assert all(x.path != "core/graph_snapshot.py" for x in v)


def test_value_types_one_finding_when_annotation_and_assign_both_apply(checks, fixture_tree):
    _, v = checks.check_value_types(fixture_tree("rule_vt", "bad"))
    on_line = [x for x in v if x.path == "use.py" and x.line == 16]
    assert [(x.kind, x.detail) for x in on_line] == [("vt_annotation", "K:Pt")]


def test_value_types_accepts_good_fixture(checks, fixture_tree, report):
    n, v = checks.check_value_types(fixture_tree("rule_vt", "good"))
    report(n, len(v))
    assert n == 2
    assert v == [], "\n".join(str(x) for x in v)


def test_value_types_empty_tree(checks, tmp_path):
    root = tmp_path / "gmid_engine"
    root.mkdir()
    n, v = checks.check_value_types(root)
    assert n == 0
    assert v == []


def test_value_types_deterministic_and_sorted(checks, fixture_tree):
    root = fixture_tree("rule_vt", "bad")
    _, v1 = checks.check_value_types(root)
    _, v2 = checks.check_value_types(root)
    assert _keys(v1) == _keys(v2)
    assert _keys(v1) == sorted(_keys(v1))
