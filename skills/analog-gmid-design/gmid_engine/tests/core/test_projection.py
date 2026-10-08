"""CONTRACT §8 Projection -- 선언 열만 담고, fp 는 (열 값, extras) 지문이며 reads 선언 순서 무관, 선언 밖 열·없는 key 는 KeyError."""
import pytest

from gmid_engine.core import GraphSnapshot, Projection, WriterTable

TABLE = WriterTable([
    ("node", "v", "bias"),
    ("node", "u", "other"),
    ("device", "w", "sizer"),
])


def _snap(v=None, u=None, w=None, iv="i1"):
    s = GraphSnapshot.empty(TABLE)
    if v is not None:
        s = s.write("bias", iv, {("node", "v"): v})
    if u is not None:
        s = s.write("other", iv, {("node", "u"): u})
    if w is not None:
        s = s.write("sizer", iv, {("device", "w"): w})
    return s


READS = (("node", "v"), ("device", "w"))


def test_column_matches_snapshot_column():
    s = _snap(v={"b": 2.0, "a": 1.0}, w={"m1": 3.0}, u={"a": 9.0})
    p = Projection.from_snapshot(s, READS)
    assert p.column("node", "v") == (("a", 1.0), ("b", 2.0)) == s.column("node", "v")
    assert p.column("device", "w") == (("m1", 3.0),)


def test_empty_declared_column_is_empty_tuple():
    s = _snap(v={"a": 1.0})
    p = Projection.from_snapshot(s, READS)
    assert p.column("device", "w") == ()


def test_undeclared_column_key_error():
    s = _snap(v={"a": 1.0}, u={"a": 2.0})
    p = Projection.from_snapshot(s, READS)
    with pytest.raises(KeyError):
        p.column("node", "u")
    with pytest.raises(KeyError):
        p.value("node", "a", "u")


def test_value():
    s = _snap(v={"a": 1.0, "b": 2.0})
    p = Projection.from_snapshot(s, READS)
    assert p.value("node", "b", "v") == 2.0
    with pytest.raises(KeyError):
        p.value("node", "zz", "v")
    with pytest.raises(KeyError):
        p.value("device", "m1", "w")  # 선언했지만 빈 열


def test_extras_default_and_given():
    s = _snap(v={"a": 1.0})
    assert Projection.from_snapshot(s, READS).extras == ()
    p = Projection.from_snapshot(s, READS, (1, "x", (2.0,)))
    assert p.extras == (1, "x", (2.0,))


def test_fp_reads_order_independent():
    s = _snap(v={"a": 1.0}, w={"m1": 3.0})
    p1 = Projection.from_snapshot(s, READS)
    p2 = Projection.from_snapshot(s, tuple(reversed(READS)))
    assert p1.fp == p2.fp


def test_fp_same_values_different_snapshots():
    s1 = _snap(v={"a": 1.0}, w={"m1": 3.0}, iv="i1")
    s2 = _snap(v={"a": 1.0}, w={"m1": 3.0}, u={"a": 5.0}, iv="other_version")
    assert Projection.from_snapshot(s1, READS).fp == Projection.from_snapshot(s2, READS).fp


def test_fp_changes_with_declared_value_or_extras():
    s1 = _snap(v={"a": 1.0}, w={"m1": 3.0})
    base = Projection.from_snapshot(s1, READS).fp
    assert Projection.from_snapshot(_snap(v={"a": 1.5}, w={"m1": 3.0}), READS).fp != base
    assert Projection.from_snapshot(_snap(v={"a": 1.0, "b": 0.0}, w={"m1": 3.0}), READS).fp != base
    assert Projection.from_snapshot(s1, READS, (1,)).fp != base
    assert Projection.from_snapshot(s1, READS, (1,)).fp != Projection.from_snapshot(s1, READS, (2,)).fp
    assert Projection.from_snapshot(s1, READS, (0.0,)).fp != Projection.from_snapshot(s1, READS, (-0.0,)).fp


def test_fp_ignores_undeclared_columns():
    s1 = _snap(v={"a": 1.0}, u={"a": 1.0})
    s2 = _snap(v={"a": 1.0}, u={"a": 2.0})
    assert Projection.from_snapshot(s1, READS).fp == Projection.from_snapshot(s2, READS).fp


def test_fp_empty_reads_vs_column_differs():
    s = _snap(v={"a": 1.0})
    assert Projection.from_snapshot(s, (("node", "v"),)).fp != Projection.from_snapshot(s, (("device", "w"),)).fp


@pytest.mark.parametrize("extras", [([1],), ({"a": 1},), ({1},), (object(),)],
                         ids=["list", "dict", "set", "object"])
def test_mutable_extras_rejected(extras):
    s = _snap(v={"a": 1.0})
    with pytest.raises(TypeError):
        Projection.from_snapshot(s, READS, extras)


# =====================================================================================================================
# 2026-10-08 개정(사용자 승인 1, sizing O9) -- 투영 지문 = 값 지문 합성. CONTRACT §8 '불변식'·'실패', §1(fp_of 태그 규칙).
# oracle 종류: 전부 (a) 구성으로 정답이 정해진 합성 입력 -- 기대값은 "같은 내용 -> 같은 fp / 한 곳이 다르면 다른 fp" 라는
# 동치 관계(§8 '옛 fp_of((columns, extras)) 와 같은 동치 관계')이며, fp 문자열 자체를 기대값으로 쓰지 않는다(§8: 문자열은 옛
# 식과 다르고 어떤 소비자도 다시 만들지 않는다). 피검 식(열 지문 sha256 인코딩)은 test 에 다시 쓰지 않는다.
# 직접 생성 형식: interface `Projection(columns, extras)`, columns = 정렬된 (((kind, field), ((key, value), ...)), ...).
# =====================================================================================================================

VCOL = (("a", 1.0), ("b", 2.0))
WCOL = (("m1", 3.0),)


def _direct(v=VCOL, w=WCOL, extras=()):
    """(kind, field) 정렬 순: ("device", "w") < ("node", "v")."""
    return Projection(((("device", "w"), w), (("node", "v"), v)), extras)


def test_direct_and_from_snapshot_identical_fp_and_columns():
    # oracle (a): 스냅샷에 VCOL·WCOL 과 같은 값을 다른 writer·input_version 으로 넣었으므로(선언 밖 열 u 도 섞음) 두 경로의
    # 열 값·extras 가 구성상 같다 -> §8 '두 경로의 fp 가 같다'.
    s = _snap(v={"b": 2.0, "a": 1.0}, w={"m1": 3.0}, u={"a": 9.0}, iv="lineage_x")
    extras = (1, "x", (2.0,))
    p = Projection.from_snapshot(s, READS, extras)
    q = _direct(extras=extras)
    assert p.fp == q.fp
    for kind, field in READS:
        assert p.column(kind, field) == q.column(kind, field)
    assert p.column("node", "v") == VCOL
    assert p.column("device", "w") == WCOL
    assert p.extras == q.extras == extras
    assert q.value("node", "b", "v") == 2.0


def test_direct_same_content_same_fp():
    # oracle (a): 내용이 같은 새 tuple 객체 두 벌 -> 같은 fp(결정론, §8).
    a = _direct(v=tuple((k, float(x)) for k, x in (("a", 1), ("b", 2))), extras=("e", 0.5))
    b = _direct(v=(("a", 1.0), ("b", 2.0)), extras=("e", 0.5))
    assert a.fp == b.fp


def test_from_snapshot_fp_independent_of_reads_order_all_permutations():
    # oracle (a): 같은 스냅샷·같은 선언 집합, 순서만 다름 -> §8 'reads 선언 순서와 무관'. 빈 선언 열(("graph", "x"))도 섞는다.
    import itertools
    s = _snap(v={"a": 1.0, "b": 2.0}, w={"m1": 3.0}, u={"c": 4.0})
    reads = (("node", "v"), ("device", "w"), ("node", "u"), ("graph", "x"))
    fps = {Projection.from_snapshot(s, perm, (7,)).fp for perm in itertools.permutations(reads)}
    assert len(fps) == 1


@pytest.mark.parametrize("v, w, extras", [
    ((("a", 1.5), ("b", 2.0)), WCOL, ()),                # 값 하나 다름
    ((("a", 1.0), ("b", 2.0)), (("m1", -3.0),), ()),     # 다른 열의 값 하나 다름(부호)
    ((("a", 1.0), ("c", 2.0)), WCOL, ()),                # key 하나 다름(값 같음)
    ((("a", 1.0),), WCOL, ()),                           # key 하나 빠짐
    ((("a", 1.0), ("b", 2.0), ("c", 2.0)), WCOL, ()),    # key 하나 더
    ((("a", 1.0), ("b", 2.0)), (), ()),                  # 열 하나가 빔
    (VCOL, WCOL, (1,)),                                  # extras 더함
    (VCOL, WCOL, ((),)),                                 # extras 빈 tuple 하나
], ids=["value", "value_other_col", "key", "key_missing", "key_extra", "column_emptied", "extras", "extras_empty_tuple"])
def test_one_difference_gives_different_fp(v, w, extras):
    # oracle (a): 기준 (VCOL, WCOL, ()) 과 정확히 한 곳만 다른 합성 입력 -> §8 '어느 값·key 하나 또는 extras 가 다르면 다른 fp'.
    base = _direct()
    other = _direct(v=v, w=w, extras=extras)
    assert other.fp != base.fp


@pytest.mark.parametrize("x, y", [
    (0.0, -0.0),        # §1: float.hex 로 직렬화 -- 부호 다른 0 은 다른 지문
    (1, 1.0),           # §1: int 와 float 은 다른 태그
    (True, 1),          # §1: bool 과 int 는 다른 태그
    ("1", 1),           # §1: str 과 int 는 다른 태그
    ((1, 2), (2, 1)),   # §1: 순서가 다르면 다르다
], ids=["signed_zero", "int_float", "bool_int", "str_int", "tuple_order"])
def test_value_fingerprint_tags_preserved_in_projection(x, y):
    # oracle (a)+(§1 규칙): 값 자리에 값의 지문(fp_of(value))을 쓰므로, fp_of 가 구별하는 두 값은 투영 fp 도 구별한다(§8).
    px = _direct(v=(("a", x),))
    py = _direct(v=(("a", y),))
    assert px.fp != py.fp


@pytest.mark.parametrize("extras_x, extras_y", [
    ((0.0,), (-0.0,)),
    ((("ab", "c"),), (("a", "bc"),)),
    ((1, 2), (2, 1)),
], ids=["signed_zero", "self_delimiting", "order"])
def test_extras_distinguished(extras_x, extras_y):
    # oracle (a)+(§1): extras 는 fp_of 그대로 들어가므로 §1 이 구별하는 extras 는 투영 fp 도 구별한다.
    assert _direct(extras=extras_x).fp != _direct(extras=extras_y).fp


def test_empty_column_is_part_of_projection():
    # oracle (a): §8 'from_snapshot 은 빈 열도 포함(column 이 ())'. 빈 선언 열이 있고 없음, 어느 열이 비었는가가 fp 에 들어간다.
    s = _snap(v={"a": 1.0, "b": 2.0})                                    # device w 는 비어 있음
    with_empty = Projection.from_snapshot(s, READS)
    without = Projection.from_snapshot(s, (("node", "v"),))
    other_empty = Projection.from_snapshot(s, (("node", "v"), ("node", "u")))
    assert with_empty.column("device", "w") == ()
    assert other_empty.column("node", "u") == ()
    assert with_empty.fp != without.fp
    assert with_empty.fp != other_empty.fp
    assert other_empty.fp != without.fp
    # 직접 생성에서도 빈 열은 열이다 -- 같은 내용의 from_snapshot 과 같다
    direct_empty = _direct(w=())
    direct_without = Projection(((("node", "v"), VCOL),), ())
    assert direct_empty.fp == with_empty.fp
    assert direct_without.fp == without.fp
    assert direct_empty.fp != direct_without.fp


def test_self_delimiting_keys_do_not_collide():
    # oracle (a): §8 '자기 구분 인코딩된 ((key, fp_of(value)), ...)' + §1 '자기 구분적 인코딩' 예.
    # key 경계만 옮긴 두 열 ("a","bc") vs ("ab","c") (값 같음) -> 다른 fp.
    p1 = _direct(v=(("a", 1.0), ("bc", 1.0)))
    p2 = _direct(v=(("ab", 1.0), ("c", 1.0)))
    assert p1.fp != p2.fp
    # 같은 경계 이동을 스냅샷 경로로도
    s1 = _snap(v={"a": 1.0, "bc": 1.0}, w={"m1": 3.0})
    s2 = _snap(v={"ab": 1.0, "c": 1.0}, w={"m1": 3.0})
    assert Projection.from_snapshot(s1, READS).fp != Projection.from_snapshot(s2, READS).fp
    # 열 경계 이동: key "b" 를 node v 에서 device w 로 옮김(값 같음) -> 다른 fp
    p3 = _direct(v=(("a", 1.0), ("b", 1.0)), w=())
    p4 = _direct(v=(("a", 1.0),), w=(("b", 1.0),))
    assert p3.fp != p4.fp


@pytest.mark.parametrize("kx, ky", [
    (1, "1"),
    (("a",), "a"),
    (1, 1.0),
    (True, 1),
], ids=["int_vs_str", "tuple_vs_str", "int_vs_float", "bool_vs_int"])
def test_non_str_keys_handled_and_distinct(kx, ky):
    # oracle (a)+(§1 태그 규칙): 직접 생성은 str 이 아닌 key 도 받아 fp 를 만든다(예외 없음). §1 이 다른 지문을 주는 두 key 는
    # 자기 구분 인코딩에서도 구별돼야 한다(key 를 문자열로 뭉개면 충돌).
    px = _direct(v=((kx, 1.0),))
    py = _direct(v=((ky, 1.0),))
    assert isinstance(px.fp, str) and isinstance(py.fp, str)
    assert px.fp != py.fp


@pytest.mark.parametrize("extras", [([1],), ({"a": 1},), ({1},), (bytearray(b"x"),), (object(),)],
                         ids=["list", "dict", "set", "bytearray", "object"])
def test_direct_mutable_extras_rejected(extras):
    # 거부(§8 '실패: extras 가변 -> TypeError') -- 직접 생성 경로.
    with pytest.raises(TypeError):
        _direct(extras=extras)


def test_direct_undeclared_column_and_missing_key_rejected():
    # 거부(§8 '실패: 선언 밖 열 -> KeyError; 열에 없는 key 의 value -> KeyError') -- 직접 생성 경로.
    p = _direct()
    with pytest.raises(KeyError):
        p.column("node", "u")
    with pytest.raises(KeyError):
        p.value("node", "a", "u")
    with pytest.raises(KeyError):
        p.value("node", "zz", "v")
    with pytest.raises(KeyError):
        _direct(w=()).value("device", "m1", "w")


# =====================================================================================================================
# 2026-10-08 두 번째 개정(core 성능 5, CONTRACT §8: 행 지문 = 열마다 (kind, field) 자기 구분 텍스트 + 열 지문의 sha256) --
# 동치 관계 유지 확인. oracle 종류: 전부 (a) 구성으로 정답이 정해진 합성 입력(같은 내용 -> 같은 fp / 한 곳만 다름 -> 다른 fp).
# fp 문자열 자체는 기대값으로 쓰지 않는다(§8 '문자열은 옛 식과 다르다').
# =====================================================================================================================

def _cols_direct(cols, extras=()):
    """cols: {(kind, field): ((key, value), ...)} -> 정렬된 직접 생성 인자."""
    return Projection(tuple(sorted(cols.items())), extras)


@pytest.mark.parametrize("other", [
    {("node", "u"): VCOL, ("device", "w"): WCOL},         # field 이름만 다름(내용 같음)
    {("graph", "v"): VCOL, ("device", "w"): WCOL},        # kind 만 다름
    {("node", "v"): VCOL, ("device", "ww"): WCOL},        # 다른 열의 field 이름
    {("node", "v"): VCOL, ("edge", "w"): WCOL},           # 다른 열의 kind
    {("node", "v"): WCOL, ("device", "w"): VCOL},         # 두 열 내용 맞바꿈
    {("node", "vd"): VCOL, ("device", "w"): WCOL},        # (kind, field) 텍스트 경계: "v"+"d..." 류 접미
], ids=["field", "kind", "other_field", "other_kind", "swap_contents", "field_suffix"])
def test_kind_or_field_difference_gives_different_fp(other):
    # oracle (a): 기준 {node v: VCOL, device w: WCOL} 와 열 이름(kind 또는 field)만 다른 입력 -> §8 '정렬된 열마다 (kind, field)
    # 자기 구분 텍스트 + 열 지문' 이므로 다른 fp(옛 식 fp_of((columns, extras)) 와 같은 동치 관계).
    base = _cols_direct({("node", "v"): VCOL, ("device", "w"): WCOL})
    assert _cols_direct(other).fp != base.fp


def test_kind_field_text_boundary_does_not_collide():
    # oracle (a)+§8 '(kind, field) 자기 구분 텍스트 + 열 지문': field 이름과 첫 key 의 경계만 옮긴 쌍
    # (field "v" + key "ab" vs field "va" + key "b", 값 같음) -> 다른 fp.
    p1 = _cols_direct({("node", "v"): (("ab", 1.0),)})
    p2 = _cols_direct({("node", "va"): (("b", 1.0),)})
    assert p1.fp != p2.fp


def test_same_columns_extras_same_fp_across_paths_and_lineages():
    # oracle (a): 같은 열 값·extras 를 (1) 직접 생성 (2) writer·input_version 이 다른 두 lineage 스냅샷의 from_snapshot 으로 만든다.
    extras = (0.5, ("k", -0.0), frozenset({"a"}))
    d = _direct(extras=extras)
    s1 = _snap(v={"a": 1.0, "b": 2.0}, w={"m1": 3.0}, iv="L1")
    s2 = _snap(w={"m1": 3.0}, v={"b": 2.0, "a": 1.0}, u={"q": 0.0}, iv="L2")
    p1 = Projection.from_snapshot(s1, READS, extras)
    p2 = Projection.from_snapshot(s2, tuple(reversed(READS)), extras)
    assert d.fp == p1.fp == p2.fp


def test_fp_independent_of_access_order():
    # oracle (a): fp 를 먼저 읽든, 열·값을 먼저 읽든 같은 투영의 fp 는 같다(투영 불변).
    s = _snap(v={"a": 1.0, "b": 2.0}, w={"m1": 3.0})
    p_fp_first = Projection.from_snapshot(s, READS, (1,))
    f1 = p_fp_first.fp
    _ = p_fp_first.column("node", "v")
    p_cols_first = Projection.from_snapshot(s, READS, (1,))
    _ = p_cols_first.column("device", "w")
    _ = p_cols_first.value("node", "a", "v")
    assert p_cols_first.fp == f1 == p_fp_first.fp


@pytest.mark.parametrize("x, y", [
    (0.0, -0.0),
    (1, 1.0),
    (True, 1),
    ("1", 1),
    (b"x", "x"),
    ((1, 2), frozenset({1, 2})),
], ids=["signed_zero", "int_float", "bool_int", "str_int", "bytes_str", "tuple_frozenset"])
def test_from_snapshot_value_tags_distinguished(x, y):
    # oracle (a)+§1 태그 규칙: from_snapshot 은 값 자리에 FieldValue.value_fp(= fp_of(value)) 를 쓰므로 §1 이 구별하는 두 값은
    # 스냅샷 경로 투영 fp 도 구별한다(파이썬 == 로는 같은 쌍 포함).
    px = Projection.from_snapshot(_snap(v={"a": x}), (("node", "v"),))
    py = Projection.from_snapshot(_snap(v={"a": y}), (("node", "v"),))
    assert px.fp != py.fp
    assert px.fp == Projection(((("node", "v"), (("a", x),)),), ()).fp
