"""GL-1 규칙 G 확장 `check_g8`: kind마다 위반과 바로 옆 경계, 허용 모듈 14개, 빈 트리, 결정성.

oracle 종류 (d): 회로 해석이 아니라 사용자가 선언한 계약(interface card 20261103-gl1 §1, design 40 §2.4.10)이다.
기대 목록은 fixtures/rule_g8/bad 소스의 줄을 손으로 읽어 적은 것이다(검사기 출력을 옮기지 않았다).
각 줄의 주석이 읽은 소스 줄이다. 허용 모듈 14개 목록도 interface §1.2의 선언을 그대로 옮겼다.
"""
from __future__ import annotations

ALLOWED = (
    "core/graph_snapshot.py", "core/compute_block.py", "core/projection.py", "core/graft.py",
    "core/donors.py", "core/field_value.py", "core/graph_record.py", "core/writer_table.py",
    "lut/lut_memo.py", "lut/table_cache.py", "core/bounded_lru.py", "search/archive.py",
    "search/s3_index.py", "core/run_counters.py",
)

# (kind, path, line, detail)
EXPECTED_G8_BAD = [
    # attr.py -- 메서드 첫 매개변수의 속성에 가변 값 대입
    ("g8_attr_container", "attr.py", 3, "Holder.a"),      # self.a = {}
    ("g8_attr_container", "attr.py", 4, "Holder.b"),      # self.b: dict = {}
    ("g8_attr_container", "attr.py", 5, "Holder.c"),      # self.c = [1, 2]
    ("g8_attr_container", "attr.py", 6, "Holder.d"),      # dict 컴프리헨션
    ("g8_attr_container", "attr.py", 7, "Holder.e"),      # ({}, 1) 가변 원소 tuple
    ("g8_attr_container", "attr.py", 8, "Holder.f"),      # defaultdict(list)
    ("g8_attr_container", "attr.py", 20, "Holder.z"),     # 메서드 안 중첩 def 의 self.z = set()
    ("g8_attr_container", "attr.py", 26, "Holder.reg"),   # cls.reg = []
    ("g8_attr_container", "attr.py", 33, "Inner.q"),      # 가장 안쪽 클래스, bytearray()
    #   (None, (), tuple(x), frozenset(x), (1, 2), self.a[k] = v, 일반 객체 obj.a = {}, 함수 x.a = {} 는 없다)
    # classc.py -- 클래스 본문 바로 아래 가변 값
    ("g8_class_container", "classc.py", 2, "Table.a"),    # a = {}
    ("g8_class_container", "classc.py", 3, "Table.b"),    # b: list = []
    ("g8_class_container", "classc.py", 7, "Table.f"),    # {1, 2}
    ("g8_class_container", "classc.py", 8, "Table.g"),    # dict 컴프리헨션
    ("g8_class_container", "classc.py", 9, "Table.h"),    # ([], 2)
    ("g8_class_container", "classc.py", 10, "Table.i"),   # deque()
    ("g8_class_container", "classc.py", 19, "Inner.z"),   # 중첩 클래스
    #   (None, (), 3, 메서드 지역 loc = {} 는 없다)
    # factory.py
    ("g8_default_factory", "factory.py", 7, "Rec.a"),     # field(default_factory=dict)
    ("g8_default_factory", "factory.py", 8, "Rec.b"),     # dataclasses.field(default_factory=list)
    ("g8_default_factory", "factory.py", 9, "Rec.c"),     # field(default_factory=set)
    ("g8_default_factory", "factory.py", 15, "build"),    # 클래스 본문 밖은 qualname
    #   (field(default=0), field(default_factory=tuple) 는 없다)
    # graph/registered.py -- 유효한 복사 등록부에 등록된 정의도 면제하지 않는다
    ("g8_default_factory", "graph/registered.py", 5, "build"),
    # cached.py
    ("g8_cached_property", "cached.py", 6, "Box.a"),      # @cached_property
    ("g8_cached_property", "cached.py", 10, "Box.b"),     # @functools.cached_property
    #   (@property 는 없다)
    # cachecall.py
    ("g8_cache_call", "cachecall.py", 9, "<module>"),     # lru_cache(maxsize=1)(f) 는 한 건
    ("g8_cache_call", "cachecall.py", 10, "<module>"),    # functools.lru_cache(maxsize=2)(f)
    ("g8_cache_call", "cachecall.py", 11, "<module>"),    # cache(f)
    ("g8_cache_call", "cachecall.py", 12, "<module>"),    # functools.cache(f)
    ("g8_cache_call", "cachecall.py", 27, "C.meth"),      # 메서드 안 lru_cache(maxsize=4)
    #   (obj.cache(...) 13·22 줄, 데코레이터 자리 @lru_cache(maxsize=3) 16 줄은 없다)
    # modcache.py
    ("g8_module_cache", "modcache.py", 5, "A"),           # BoundedLRU(3)
    ("g8_module_cache", "modcache.py", 6, "B"),           # LutMemo()
    ("g8_module_cache", "modcache.py", 7, "C"),           # OrderedDict()
    ("g8_module_cache", "modcache.py", 8, "D"),           # WeakValueDictionary()
    ("g8_module_cache", "modcache.py", 9, "E"),           # collections.OrderedDict() 끝 이름
    ("g8_module_cache", "modcache.py", 13, "G"),          # if 안
    ("g8_module_cache", "modcache.py", 16, "H"),          # try 안
    ("g8_module_cache", "modcache.py", 21, "I"),          # with 안
    ("g8_module_cache", "modcache.py", 24, "J"),          # for 안
    ("g8_module_cache", "modcache.py", 28, "M"),          # match 안
    #   (F = dict() 10 줄, 함수 안 K 32 줄, 클래스 안 L 36 줄은 없다)
    # idcall.py, edges.py, metrics/run_counters.py
    ("g8_id_call", "idcall.py", 2, "f"),                  # id(x)
    ("g8_id_call", "idcall.py", 7, "C.m"),                # 컴프리헨션 안
    ("g8_id_call", "idcall.py", 10, "<module>"),          # key = id(3)
    ("g8_id_call", "edges.py", 1, "<module>"),            # 첫 줄
    ("g8_id_call", "edges.py", 3, "<module>"),            # 끝 줄(끝 개행 없음), 같은 키 두 건
    ("g8_id_call", "metrics/run_counters.py", 2, "f"),    # 같은 이름이 다른 폴더면 허용 아님
    # memocall.py
    ("g8_memo_call_form", "memocall.py", 17, "bad_noarg"),        # memo.call()
    ("g8_memo_call_form", "memocall.py", 21, "bad_lambda"),       # lambda
    ("g8_memo_call_form", "memocall.py", 25, "bad_partial"),      # partial(...) 호출
    ("g8_memo_call_form", "memocall.py", 29, "bad_param"),        # 매개변수 fn
    ("g8_memo_call_form", "memocall.py", 33, "bad_param_attr"),   # 뿌리 obj 가 매개변수
    ("g8_memo_call_form", "memocall.py", 38, "bad_local"),        # 지역 대입 helper
    ("g8_memo_call_form", "memocall.py", 45, "bad_nested"),       # 중첩 def inner
    ("g8_memo_call_form", "memocall.py", 49, "bad_expr_memo"),    # p.memo.call(lambda: 2)
    #   (10~13 줄 모듈 함수·import 이름·pkg_mod.fn 은 없다)
    # memolookup.py
    ("g8_memo_lookup_form", "memolookup.py", 2, "a"),     # memo.lookup(k)
    ("g8_memo_lookup_form", "memolookup.py", 6, "b"),     # memo.lookup_persistent(k)
    ("g8_memo_lookup_form", "memolookup.py", 10, "c"),    # p.memo.lookup(k)
    ("g8_memo_lookup_form", "memolookup.py", 14, "d"),    # p.memo.lookup_persistent(k)
    #   (memo.lookup_other, p.lookup, memo.call(KEY, k) 는 없다)
]
# 허용 모듈 14개 파일은 모두 `return id(x)` 를 담지만 위 목록에 한 건도 없다.


def _keys(violations):
    return [(v.kind, v.path, v.line, v.detail) for v in violations]


def test_g8_allowed_modules_is_the_declared_fourteen(checks):
    assert isinstance(checks.G8_ALLOWED_MODULES, tuple)
    assert len(ALLOWED) == 14
    assert set(checks.G8_ALLOWED_MODULES) == set(ALLOWED)
    assert len(checks.G8_ALLOWED_MODULES) == 14


def test_g8_rejects_bad_fixture_exactly(checks, fixture_tree, report):
    n, v = checks.check_g8(fixture_tree("rule_g8", "bad"))
    report(n, len(v))
    # 대상 파일 수: 허용 모듈 14 + metrics/run_counters 1 + 위반 소스 10 + graph/registered, graph/_copy_manifest 2
    assert n == 27
    assert _keys(v) == sorted(EXPECTED_G8_BAD), "\n".join(str(x) for x in v)


def test_g8_allowed_modules_emit_nothing(checks, fixture_tree):
    _, v = checks.check_g8(fixture_tree("rule_g8", "bad"))
    paths = {x.path for x in v}
    assert paths.isdisjoint(ALLOWED), sorted(paths & set(ALLOWED))


def test_g8_same_name_other_folder_is_not_allowed(checks, fixture_tree):
    _, v = checks.check_g8(fixture_tree("rule_g8", "bad"))
    assert ("g8_id_call", "metrics/run_counters.py", 2, "f") in _keys(v)
    assert all(x.path != "core/run_counters.py" for x in v)


def test_g8_registered_copy_is_not_exempt(checks, fixture_tree):
    _, v = checks.check_g8(fixture_tree("rule_g8", "bad"))
    assert ("g8_default_factory", "graph/registered.py", 5, "build") in _keys(v)


def test_g8_same_key_several_sites_reported_separately(checks, fixture_tree):
    _, v = checks.check_g8(fixture_tree("rule_g8", "bad"))
    same = [x.line for x in v if x.path == "edges.py" and x.kind == "g8_id_call" and x.detail == "<module>"]
    assert same == [1, 3]


def test_g8_accepts_good_fixture(checks, fixture_tree, report):
    n, v = checks.check_g8(fixture_tree("rule_g8", "good"))
    report(n, len(v))
    assert n == 2
    assert v == [], "\n".join(str(x) for x in v)


def test_g8_empty_tree(checks, tmp_path):
    root = tmp_path / "gmid_engine"
    root.mkdir()
    n, v = checks.check_g8(root)
    assert n == 0
    assert v == []


def test_g8_skips_tests_pycache_hidden(checks, tmp_path):
    root = tmp_path / "gmid_engine"
    for d in ("tests", "__pycache__", ".hidden", "core/__pycache__"):
        (root / d).mkdir(parents=True)
        (root / d / "x.py").write_text("y = id(1)\n", encoding="utf-8")
    n, v = checks.check_g8(root)
    assert n == 0
    assert v == []


def test_g8_deterministic_and_sorted(checks, fixture_tree):
    root = fixture_tree("rule_g8", "bad")
    n1, v1 = checks.check_g8(root)
    n2, v2 = checks.check_g8(root)
    assert n1 == n2
    assert _keys(v1) == _keys(v2)
    assert _keys(v1) == sorted(_keys(v1))


def test_g8_violation_path_is_posix_relative(checks, fixture_tree):
    _, v = checks.check_g8(fixture_tree("rule_g8", "bad"))
    for x in v:
        assert "\\" not in x.path and not x.path.startswith("/") and ":" not in x.path, x.path
