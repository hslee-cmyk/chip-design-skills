"""CONTRACT §5.6 GraphSnapshot -- write 가 유일한 setter, 원본 불변, 열 교체 의미, 메타 규칙, 구조 공유(is),
아무것도 안 바뀌면 self, 내용 지문 fp, 권한 위반·잘못된 입력 거부(스냅샷 불변)."""
import pytest

from gmid_engine.core import FieldValue, GraphRecord, GraphSnapshot, WriterPermissionError, WriterTable

TABLE = WriterTable([
    ("node", "v", "bias"),
    ("node", "u", "other"),
    ("device", "w", "sizer"),
    ("device", "l", "sizer"),
    ("graph", "theta", "search"),
])


def _empty():
    return GraphSnapshot.empty(TABLE)


def _reads(s):
    """스냅샷의 모든 읽기 결과를 순수 값으로 모은다(원본 불변 비교용)."""
    out = {"kinds": s.kinds(), "fp": s.fp}
    for kind in ("device", "edge", "graph", "node"):
        out[("keys", kind)] = s.keys(kind)
        for f in ("v", "u", "w", "l", "theta"):
            out[("col", kind, f)] = s.column(kind, f)
            for key in s.keys(kind):
                fv = s.field(kind, key, f)
                out[("field", kind, key, f)] = None if fv is None else (
                    fv.value, fv.writer, fv.input_version, fv.write_count)
    for w in ("bias", "other", "sizer", "search", "nobody"):
        out[("bv", w)] = s.block_version(w)
    return out


# ---------- empty ----------

def test_empty_has_no_records():
    s = _empty()
    assert s.kinds() == ()
    assert s.keys("node") == ()
    assert s.record("node", "a") is None
    assert s.field("node", "a", "v") is None
    assert s.column("node", "v") == ()
    assert s.block_version("bias") is None
    with pytest.raises(KeyError):
        s.value("node", "a", "v")
    assert s.writers == TABLE


@pytest.mark.parametrize("bad", [None, (("node", "v", "bias"),), [("node", "v", "bias")], "table"])
def test_empty_requires_writer_table(bad):
    with pytest.raises(TypeError):
        GraphSnapshot.empty(bad)


# ---------- 기본 write / 읽기 ----------

def test_write_and_read_back():
    s0 = _empty()
    s1 = s0.write("bias", "iv1", {("node", "v"): {"b": 2.0, "a": 1.0}})
    assert s1 is not s0
    assert s1.kinds() == ("node",)
    assert s1.keys("node") == ("a", "b")
    assert s1.value("node", "a", "v") == 1.0
    assert s1.column("node", "v") == (("a", 1.0), ("b", 2.0))
    fv = s1.field("node", "a", "v")
    assert isinstance(fv, FieldValue)
    assert (fv.writer, fv.input_version, fv.write_count) == ("bias", "iv1", 1)
    rec = s1.record("node", "a")
    assert isinstance(rec, GraphRecord) and rec.get("v") is fv
    assert s1.block_version("bias") == "iv1"
    assert s1.block_version("sizer") is None


def test_value_missing_field_key_error():
    s = _empty().write("bias", "iv1", {("node", "v"): {"a": 1.0}})
    with pytest.raises(KeyError):
        s.value("node", "a", "u")
    with pytest.raises(KeyError):
        s.value("node", "zz", "v")


def test_kinds_sorted_multiple():
    s = _empty().write("search", "i", {("graph", "theta"): {"g": (1, 2)}})
    s = s.write("bias", "i", {("node", "v"): {"a": 1.0}})
    s = s.write("sizer", "i", {("device", "w"): {"m1": 1e-6}})
    assert s.kinds() == ("device", "graph", "node")


def test_writer_writes_multiple_columns_at_once():
    s = _empty().write("sizer", "i1", {("device", "w"): {"m1": 1.0}, ("device", "l"): {"m1": 2.0, "m2": 3.0}})
    assert s.column("device", "w") == (("m1", 1.0),)
    assert s.column("device", "l") == (("m1", 2.0), ("m2", 3.0))
    assert s.record("device", "m1").field_names() == ("l", "w")


# ---------- 원본 불변 ----------

def test_original_unchanged_after_write():
    s0 = _empty().write("bias", "iv1", {("node", "v"): {"a": 1.0, "b": 2.0}})
    s0 = s0.write("sizer", "iv1", {("device", "w"): {"m1": 1.0}})
    before = _reads(s0)
    s1 = s0.write("bias", "iv2", {("node", "v"): {"a": 5.0, "c": 6.0}})
    s2 = s1.write("sizer", "iv3", {("device", "w"): {}})
    assert _reads(s0) == before
    assert _reads(s1) != before
    assert s2.keys("device") == ()
    assert s0.keys("device") == ("m1",)


# ---------- 열 교체 의미 ----------

def test_column_replace_removes_unlisted_keys():
    s1 = _empty().write("bias", "i1", {("node", "v"): {"a": 1.0, "b": 2.0}})
    s2 = s1.write("bias", "i2", {("node", "v"): {"b": 3.0, "c": 4.0}})
    assert s2.keys("node") == ("b", "c")
    assert s2.record("node", "a") is None
    assert s2.column("node", "v") == (("b", 3.0), ("c", 4.0))


def test_column_replace_keeps_record_with_other_fields():
    s = _empty().write("bias", "i1", {("node", "v"): {"a": 1.0, "b": 2.0}})
    s = s.write("other", "i1", {("node", "u"): {"a": 9.0}})
    s2 = s.write("bias", "i2", {("node", "v"): {"b": 2.5}})
    assert s2.keys("node") == ("a", "b")
    assert s2.record("node", "a").field_names() == ("u",)
    assert s2.field("node", "a", "v") is None
    assert s2.value("node", "a", "u") == 9.0


def test_empty_column_removes_all():
    s = _empty().write("bias", "i1", {("node", "v"): {"a": 1.0}})
    s2 = s.write("bias", "i2", {("node", "v"): {}})
    assert s2.kinds() == ()
    assert s2.keys("node") == ()


# ---------- 필드 메타 ----------

def test_write_count_increments_on_rewrite():
    s1 = _empty().write("bias", "i1", {("node", "v"): {"a": 1.0}})
    s2 = s1.write("bias", "i2", {("node", "v"): {"a": 2.0}})
    s3 = s2.write("bias", "i3", {("node", "v"): {"a": 3.0}})
    assert s1.field("node", "a", "v").write_count == 1
    assert s2.field("node", "a", "v").write_count == 2
    assert s3.field("node", "a", "v").write_count == 3
    assert s3.field("node", "a", "v").input_version == "i3"


def test_same_value_same_version_keeps_fieldvalue_object():
    s1 = _empty().write("bias", "i1", {("node", "v"): {"a": 1.0, "b": 2.0}})
    s2 = s1.write("bias", "i1", {("node", "v"): {"a": 1.0, "b": 7.0}})
    assert s2.field("node", "a", "v") is s1.field("node", "a", "v")
    assert s2.field("node", "a", "v").write_count == 1
    assert s2.field("node", "b", "v").write_count == 2


def test_same_value_new_version_is_new_field():
    s1 = _empty().write("bias", "i1", {("node", "v"): {"a": 1.0}})
    s2 = s1.write("bias", "i2", {("node", "v"): {"a": 1.0}})
    fv1, fv2 = s1.field("node", "a", "v"), s2.field("node", "a", "v")
    assert fv2 is not fv1
    assert fv2.input_version == "i2" and fv2.write_count == 2
    assert s2.record("node", "a") is not s1.record("node", "a")
    assert s2.fp == s1.fp


def test_removed_then_rewritten_counts_from_one():
    s1 = _empty().write("bias", "i1", {("node", "v"): {"a": 1.0}})
    s2 = s1.write("bias", "i2", {("node", "v"): {}})
    s3 = s2.write("bias", "i3", {("node", "v"): {"a": 1.0}})
    assert s3.field("node", "a", "v").write_count == 1


def test_block_version_per_writer():
    s1 = _empty().write("bias", "i1", {("node", "v"): {"a": 1.0}})
    s2 = s1.write("sizer", "j1", {("device", "w"): {"m": 1.0}})
    assert s2.block_version("bias") == "i1"
    assert s2.block_version("sizer") == "j1"
    s3 = s2.write("bias", "i2", {("node", "v"): {"a": 1.5}})
    assert s3.block_version("bias") == "i2"
    assert s3.block_version("sizer") == "j1"


# ---------- self 반환 ----------

def test_no_change_returns_self():
    s1 = _empty().write("bias", "i1", {("node", "v"): {"a": 1.0, "b": 2.0}})
    s2 = s1.write("bias", "i1", {("node", "v"): {"b": 2.0, "a": 1.0}})
    assert s2 is s1


def test_new_version_same_values_not_self():
    s1 = _empty().write("bias", "i1", {("node", "v"): {"a": 1.0}})
    s2 = s1.write("bias", "i2", {("node", "v"): {"a": 1.0}})
    assert s2 is not s1
    assert s2.block_version("bias") == "i2"
    assert s1.block_version("bias") == "i1"


# ---------- 구조 공유 ----------

def _rich():
    s = _empty().write("bias", "i1", {("node", "v"): {"a": 1.0, "b": 2.0}})
    s = s.write("other", "o1", {("node", "u"): {"c": 3.0, "a": 4.0}})
    s = s.write("sizer", "z1", {("device", "w"): {"m1": 1.0, "m2": 2.0}})
    s = s.write("search", "t1", {("graph", "theta"): {"g": (0.5, 0.25)}})
    return s


def test_structural_sharing_unchanged_records_same_object():
    s0 = _rich()
    s1 = s0.write("bias", "i1", {("node", "v"): {"a": 1.5, "b": 2.0}})
    # 바뀐 레코드
    assert s1.record("node", "a") is not s0.record("node", "a")
    # 같은 kind 의 다른 key(값·버전 같음)
    assert s1.record("node", "b") is s0.record("node", "b")
    # 같은 kind, 이번 열에 없는 key
    assert s1.record("node", "c") is s0.record("node", "c")
    # 다른 kind
    for key in ("m1", "m2"):
        assert s1.record("device", key) is s0.record("device", key)
    assert s1.record("graph", "g") is s0.record("graph", "g")
    # 바뀐 레코드 안의 바뀌지 않은 필드 객체도 그대로
    assert s1.field("node", "a", "u") is s0.field("node", "a", "u")


def test_new_input_version_makes_new_record_even_if_value_same():
    s0 = _rich()
    s1 = s0.write("bias", "i2", {("node", "v"): {"a": 1.0, "b": 2.0}})
    assert s1.record("node", "b") is not s0.record("node", "b")
    assert s1.record("node", "a") is not s0.record("node", "a")
    assert s1.record("node", "c") is s0.record("node", "c")
    assert s1.record("device", "m1") is s0.record("device", "m1")
    assert s1.fp == s0.fp


# ---------- fp ----------

def test_fp_path_independent():
    a = _empty().write("bias", "x1", {("node", "v"): {"a": 1.0, "b": 2.0}})
    a = a.write("sizer", "x2", {("device", "w"): {"m1": 3.0}})
    b = _empty().write("sizer", "y9", {("device", "w"): {"m1": 99.0}})
    b = b.write("bias", "y8", {("node", "v"): {"b": 2.0, "a": 1.0, "zz": 5.0}})
    b = b.write("sizer", "y7", {("device", "w"): {"m1": 3.0}})
    b = b.write("bias", "y6", {("node", "v"): {"b": 2.0, "a": 1.0}})
    assert a is not b
    assert a.fp == b.fp
    assert a != b  # == 는 객체 동일성
    assert a == a


def test_fp_ignores_block_versions():
    a = _empty().write("bias", "x1", {("node", "v"): {"a": 1.0}})
    b = a.write("bias", "x2", {("node", "v"): {"a": 1.0}})
    assert a.block_version("bias") != b.block_version("bias")
    assert a.fp == b.fp


def test_fp_differs_on_any_value():
    base = _rich()
    assert base.write("bias", "i1", {("node", "v"): {"a": 1.0, "b": 2.0000001}}).fp != base.fp
    assert base.write("sizer", "z1", {("device", "w"): {"m1": 1.0}}).fp != base.fp  # m2 제거
    assert base.write("search", "t1", {("graph", "theta"): {"g": (0.5, -0.25)}}).fp != base.fp
    assert base.write("other", "o1", {("node", "u"): {"c": 3.0, "a": 4.0, "d": 0.0}}).fp != base.fp
    z = _empty().write("bias", "i", {("node", "v"): {"a": 0.0}})
    nz = _empty().write("bias", "i", {("node", "v"): {"a": -0.0}})
    assert z.fp != nz.fp


def test_empty_fp_stable():
    assert _empty().fp == _empty().fp
    assert _empty().fp != _empty().write("bias", "i", {("node", "v"): {"a": 1.0}}).fp


# ---------- 읽기 전용 매핑 ----------

def test_tables_and_block_versions_read_only():
    s = _rich()
    with pytest.raises(TypeError):
        s.tables["node"] = ()
    with pytest.raises(TypeError):
        s.block_versions["bias"] = "hacked"
    assert s.block_version("bias") == "i1"


# ---------- 실패 (스냅샷 불변) ----------

def test_permission_violation_rejected_and_snapshot_unchanged():
    s = _rich()
    before = _reads(s)
    with pytest.raises(WriterPermissionError):
        s.write("sizer", "i9", {("node", "v"): {"a": 9.0}})
    with pytest.raises(WriterPermissionError):
        s.write("bias", "i9", {("node", "undeclared"): {"a": 9.0}})
    with pytest.raises(WriterPermissionError):
        s.write("nobody", "i9", {("node", "v"): {"a": 9.0}})
    # 권한 있는 열과 없는 열을 섞어도 전부 거부
    with pytest.raises(WriterPermissionError):
        s.write("bias", "i9", {("node", "v"): {"a": 9.0}, ("node", "u"): {"a": 9.0}})
    assert _reads(s) == before


@pytest.mark.parametrize("iv", ["", 1, None])
def test_bad_input_version_rejected(iv):
    s = _rich()
    before = _reads(s)
    with pytest.raises(ValueError):
        s.write("bias", iv, {("node", "v"): {"a": 9.0}})
    assert _reads(s) == before


@pytest.mark.parametrize(
    "columns",
    [
        [(("node", "v"), {"a": 1.0})],
        "columns",
        {("node", "v"): [("a", 1.0)]},
        {("node", "v"): 1.0},
    ],
    ids=["columns_list", "columns_str", "column_value_list", "column_value_scalar"],
)
def test_non_mapping_columns_rejected(columns):
    s = _rich()
    before = _reads(s)
    with pytest.raises(TypeError):
        s.write("bias", "i9", columns)
    assert _reads(s) == before


@pytest.mark.parametrize("key", [1, None, ("a",)])
def test_non_str_key_rejected(key):
    s = _rich()
    before = _reads(s)
    with pytest.raises(TypeError):
        s.write("bias", "i9", {("node", "v"): {key: 1.0}})
    assert _reads(s) == before


@pytest.mark.parametrize("value", [[1.0], {"x": 1}, {1}, bytearray(b"x")])
def test_mutable_value_rejected(value):
    s = _rich()
    before = _reads(s)
    with pytest.raises(TypeError):
        s.write("bias", "i9", {("node", "v"): {"a": value}})
    assert _reads(s) == before


# =====================================================================================================================
# 2026-10-08 개정(사용자 승인 1, sizing O7) -- CONTRACT §5.6 `column_fields`, `extend_writers`.
# oracle 종류: 전부 (a) 구성으로 정답이 정해진 합성 입력 -- 기대값(key 집합·write_count·writer·input_version)은 이 test 가
# 넣은 write 순서로 정해지고(§5.6 write 메타 규칙), 피검 함수 출력으로 만들지 않는다.
# =====================================================================================================================

from gmid_engine.core import fp_of  # noqa: E402  (§5.4 value_fp == fp_of(value) 확인용; 피검 함수 아님)

TABLE_TRIPLES = (
    ("node", "v", "bias"),
    ("node", "u", "other"),
    ("device", "w", "sizer"),
    ("device", "l", "sizer"),
    ("graph", "theta", "search"),
)
WIDE = WriterTable(list(TABLE_TRIPLES) + [("node", "vb", "s2"), ("device", "gm", "s2"), ("edge", "i", "s2")])


def _populated():
    """메타가 구성으로 정해진 스냅샷: node a 의 v 는 같은 값·새 input_version 으로 두 번 써서 write_count 2(§5.6 '이전 + 1'),
    node b 의 v 는 값이 바뀌어 write_count 2, node c 는 v 없이 u 만, device m1 은 w·l."""
    s = _empty().write("bias", "i1", {("node", "v"): {"a": 1.0, "b": 2.0}})
    s = s.write("bias", "i2", {("node", "v"): {"a": 1.0, "b": 3.0}})
    s = s.write("other", "o1", {("node", "u"): {"a": 5.0, "c": 6.0}})
    s = s.write("sizer", "z1", {("device", "w"): {"m1": 0.5}, ("device", "l"): {"m1": 1e-6}})
    s = s.write("search", "t1", {("graph", "theta"): {"g": (1.0, 2.0)}})
    return s


# ---------- column_fields ----------

def test_column_fields_same_keys_and_order_as_column_with_fieldvalues():
    s = _populated()
    for kind, field, expected_keys in (("node", "v", ("a", "b")), ("node", "u", ("a", "c")),
                                       ("device", "w", ("m1",)), ("graph", "theta", ("g",))):
        cf = s.column_fields(kind, field)
        col = s.column(kind, field)
        assert isinstance(cf, tuple)
        assert tuple(k for k, _ in cf) == tuple(k for k, _ in col) == expected_keys
        for (key, fv), (_, val) in zip(cf, col):
            assert isinstance(fv, FieldValue)
            assert fv.value == val
            assert fv.value_fp == fp_of(val)
            ref = s.field(kind, key, field)
            assert (fv.value, fv.writer, fv.input_version, fv.write_count) == (
                ref.value, ref.writer, ref.input_version, ref.write_count)


def test_column_fields_meta_from_construction():
    # oracle (a): _populated 의 write 순서로 정해진 메타.
    cf = dict(_populated().column_fields("node", "v"))
    assert (cf["a"].writer, cf["a"].input_version, cf["a"].write_count) == ("bias", "i2", 2)
    assert (cf["b"].writer, cf["b"].input_version, cf["b"].write_count, cf["b"].value) == ("bias", "i2", 2, 3.0)


def test_column_fields_omits_records_lacking_field():
    s = _populated()
    assert "c" not in dict(s.column_fields("node", "v"))      # node c 는 u 만 있다
    assert "b" not in dict(s.column_fields("node", "u"))      # node b 는 v 만 있다
    assert s.column_fields("edge", "i") == ()
    assert s.column_fields("node", "nobody_writes_this") == ()
    assert _empty().column_fields("node", "v") == ()


# ---------- extend_writers ----------

def test_extend_writers_new_table_shared_records_and_meta():
    s = _populated()
    before = _reads(s)
    e = s.extend_writers(WIDE)
    assert isinstance(e, GraphSnapshot)
    assert e is not s
    assert e.writers == WIDE
    assert s.writers == TABLE                                  # 원본 불변
    assert _reads(s) == before
    assert e.kinds() == s.kinds()
    n = 0
    for kind in s.kinds():
        assert e.keys(kind) == s.keys(kind)
        for key in s.keys(kind):
            assert e.record(kind, key) is s.record(kind, key)  # 같은 객체
            n += 1
    assert n == 5                                              # 구성: node a·b·c + device m1 + graph g
    assert e.fp == s.fp
    assert _reads(e) == before                                 # 값·메타(writer·input_version·write_count)·block_version 같음
    for w in ("bias", "other", "sizer", "search"):
        assert e.block_version(w) == s.block_version(w)
    assert e.block_version("s2") is None
    assert dict(e.block_versions) == dict(s.block_versions)
    # 구성으로 정해진 메타가 그대로
    fa = e.field("node", "a", "v")
    assert (fa.writer, fa.input_version, fa.write_count) == ("bias", "i2", 2)


def test_extend_writers_then_write_uses_new_table_and_carried_meta():
    s = _populated()
    e = s.extend_writers(WIDE)
    # 새 표의 열은 확장된 스냅샷에서만 쓸 수 있다
    e2 = e.write("s2", "x1", {("node", "vb"): {"a": 0.3}})
    assert e2.value("node", "a", "vb") == 0.3
    with pytest.raises(WriterPermissionError):
        s.write("s2", "x1", {("node", "vb"): {"a": 0.3}})
    # 옮겨진 메타 위에서 write_count 가 이어진다(§5.6 '이전 + 1'): a 는 2 였다 -> 3
    e3 = e.write("bias", "i3", {("node", "v"): {"a": 1.0, "b": 3.0}})
    assert e3.field("node", "a", "v").write_count == 3
    # 확장된 스냅샷에 같은 값·같은 input_version 을 다시 쓰면 self(메타가 원본 그대로이므로)
    assert e.write("bias", "i2", {("node", "v"): {"a": 1.0, "b": 3.0}}) is e


def test_extend_writers_equal_table_returns_self():
    s = _populated()
    same = WriterTable(list(reversed(TABLE_TRIPLES)))         # 선언 순서만 다른 같은 표(§5.3 '==')
    assert s.extend_writers(same) is s
    assert s.extend_writers(TABLE) is s
    empty = _empty()
    assert empty.extend_writers(same) is empty


def test_extend_writers_on_empty_snapshot():
    empty = _empty()
    e = empty.extend_writers(WIDE)
    assert e.writers == WIDE
    assert e.kinds() == ()
    assert e.fp == empty.fp
    assert empty.writers == TABLE


@pytest.mark.parametrize("bad", [None, "table", TABLE_TRIPLES, list(TABLE_TRIPLES), (((("node", "v"), "bias"),),)],
                         ids=["none", "str", "triples_tuple", "triples_list", "entries_like"])
def test_extend_writers_requires_writer_table(bad):
    # 거부(§5.6 'WriterTable 아님 -> TypeError').
    s = _populated()
    before = _reads(s)
    with pytest.raises(TypeError):
        s.extend_writers(bad)
    assert _reads(s) == before
    assert s.writers == TABLE


@pytest.mark.parametrize("triples", [
    [t for t in TABLE_TRIPLES if t != ("graph", "theta", "search")] + [("node", "vb", "s2")],   # 항목 빠짐(데이터 있음)
    [t for t in TABLE_TRIPLES if t != ("device", "l", "sizer")],                               # 항목 빠짐
    [t for t in TABLE_TRIPLES if t != ("node", "v", "bias")] + [("node", "v", "s2")],          # 같은 열 다른 writer
    [("node", "vb", "s2")],                                                                    # 원본 항목 전부 빠짐
], ids=["missing_theta", "missing_l", "other_writer", "disjoint"])
def test_extend_writers_rejects_non_superset(triples):
    # 거부(§5.6 '원본 표의 항목이 빠졌거나 다른 writer -> WriterPermissionError(원본 불변)').
    table = WriterTable(triples)
    for s in (_populated(), _empty()):
        before = _reads(s)
        with pytest.raises(WriterPermissionError):
            s.extend_writers(table)
        assert _reads(s) == before
        assert s.writers == TABLE
