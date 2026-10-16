"""gmid_engine 구조 규칙 검사기 (tests/structure 전용).

엔진 코드를 import 하지 않는다 -- 소스 파일을 AST 로만 읽는다. 그래서 같은 검사기를
진짜 엔진 트리와 위반 픽스처 트리(tests/structure/fixtures/, import 불가)에 똑같이 건다.

규칙 출처(저장소 밖 초안, 2026-10-07):
  D  = _drafts/engine/NEW_ENGINE_DESIGN_REQUIREMENTS.md
  UD = _drafts/user_decisions.md 끝 '2026-10-07' 항목
  P  = docs/01-plan/features/gain-budget-gmid-sizing.plan.md
각 상수·규칙 위에 행/절을 적는다. 규칙 문자는 tests/structure/README.md 와 같다.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

ENGINE_PACKAGE = "gmid_engine"

# (C) 하위 패키지 층 번호. 출처: D 3.1 '규칙' 첫 항목(158행)
#   "core(0) < lut(1) < authoring(2) < graph(3) < sizing(4) < metrics(5) < search(6)
#    < layout(7) < convergence(8) < report(9) < pipeline(10). 작은 번호 쪽으로만."
LAYER_ORDER = (
    "core", "lut", "authoring", "graph", "sizing", "metrics",
    "search", "layout", "convergence", "report", "pipeline",
)
LAYER = {name: number for number, name in enumerate(LAYER_ORDER)}

# (A) 예외 = 레지스트리 등록 데코레이터로 묶인 같은 시그니처 변형군. 데코레이터 이름 출처:
#   D 1.1 (나)2 "계산 블록 데코레이터 `@compute_block(name, reads=(...), domain=...)`(`core/memo.py`)"
#   D 1.1 (나)3 "모든 캐시는 `core.memo.Registry`에 등록" -> compute_block 은 레지스트리 등록 데코레이터.
#   D 1.2 (나)4 (A) 의 예시 'metric 레지스트리 항목들'은 데코레이터 이름이 설계 문서에 없다(README '애매한 점' 1).
#   새 레지스트리 데코레이터를 만들면 설계 문서에 이름을 적고 여기에 더한다.
REGISTRY_DECORATORS = ("compute_block",)

# (D) 숫자 리터럴 허용 집합 {0, 1, -1, 산술식의 2, 인덱스·슬라이스} + 같은 줄 `# derive: <함수명>`
#   (그 함수가 엔진에 있어야 함). 출처: P 844행 V6, D 1.3 (나) 마지막 항목.
DERIVE_TAG = re.compile(r"#\s*derive:\s*([A-Za-z_][A-Za-z0-9_]*)")
# D 1.3 (나) "단위 환산 계수는 `core/units.py` 한 곳" -> 단위 환산 계수 리터럴이 놓이는 유일한 파일.
NUMERIC_LITERAL_HOME = ("core/units.py",)

# (F) 광범위 except. 출처: 과제 지시(except:, Exception, BaseException), P N3.14(734~751행),
#   D 1.6 (다) "`test_no_broad_except` ... 진입점 1곳 예외" + D 3.1 표 pipeline `entry.py`(exit code).
BROAD_EXCEPTION_NAMES = ("Exception", "BaseException")
BROAD_EXCEPT_ENTRY_FILE = "pipeline/entry.py"
BROAD_EXCEPT_ENTRY_MAX = 1

# (G) 모듈 수준 가변 캐시. 출처: D '확정 사항' 5 "계산 블록은 graph setter 로만 결과를 쓴다
#   (모듈 수준 dict·전역 캐시 lint FAIL)", 확정 사항 1·4(graph 밖은 LUT 조회 memo 하나뿐),
#   D 1.1 (나)3 "모듈 전역 dict 캐시·`functools.lru_cache(maxsize=None)` ... 금지".
MUTABLE_CONSTRUCTORS = (
    "dict", "list", "set", "bytearray",
    "defaultdict", "OrderedDict", "Counter", "deque", "ChainMap",
    "WeakValueDictionary", "WeakKeyDictionary", "WeakSet",
)
CACHE_DECORATORS = ("lru_cache", "cache")
MODULE_LEVEL_EXEMPT_NAMES = ("__all__",)  # 공개 API 목록(D 1.2 (나)1) -- 상태가 아니다

# (D·E·G 예외) 복사 등록부. 출처: wt/_drafts/engine/design_mod7_layout.md 8절 2 기본안
#   "복사본 내부 탐색 상한 리터럴: manifest 한정 예외 + 리터럴 집합 test 고정", 같은 문서 1.1·2.1·2.2.
#   하위 패키지 폴더의 이 이름 파일이 등록부다(층 무관). 형식·검증 절차는 README '복사 등록부'.
COPY_MANIFEST_NAME = "_copy_manifest.py"
COPY_MANIFEST_SOURCE = "COPY_SOURCE"            # 원본 파일(저장소 기준 상대 경로) 문자열
COPY_MANIFEST_TABLE = "COPIED_DEFINITIONS"      # (파일, 정의 이름, "시작~끝", sha256 hex, 리터럴 문자열 tuple) tuple
COPY_ROWS = re.compile(r"^(\d+)~(\d+)$")
COPY_HASH = re.compile(r"^[0-9a-f]{64}$")
COPY_SOURCE_KINDS = ("copy_source_missing", "copy_source_in_engine", "copy_source_mismatch")

# (H) 엔진 하위 패키지가 아닌 tests/ 하위 폴더(교차 관심사). 출처: D 3.1 'test 배치'(162행).
CROSS_CUTTING_TEST_DIRS = ("structure", "contracts", "integration", "regression", "oracles", "perf", "unit")

# (K) front 조회(다른 실행의 출력 조회) 전용 읽기 경로를 엔진 안에서 부르지 않는다. 출처: 설계 40 v1.10 §2.4.3 'front 조회 전용 읽기 경로'
#   표 '검사' 행(사용자 결정 2026-10-15 "나로 해" -- 실행 사이 재사용 제거, U-90 front 조회 유지) + '부를 수 있는 곳' 행
#   "엔진 안에서는 없다. 정의(search/front_query.py, search/front_entries.py)와 재수출(search/__init__.py)만 이름을 가진다".
FRONT_QUERY_ALLOWED_FILES = ("search/front_query.py", "search/front_entries.py", "search/__init__.py")
FRONT_QUERY_NAMES = ("node_across_front", "read_front_entries")          # (K-a) 공개 이름
FRONT_QUERY_MODULES = ("front_query", "front_entries")                   # (K-b) 모듈 이름(상대·절대 import)
SNAPSHOT_READ_ATTRS = ("read_snapshot", "_read_snapshot_file")           # (K-c) 속성 이름(호출 아닌 참조 포함)
SNAPSHOT_READ_NAMES = ("_read_snapshot_file",)                           # (K-c) 이름

# (M) 실행 비공유 -- 색인·계수(`open_run()` 의 두 객체)는 실행 하나에만 산다. 출처: XRUN-F1 card B interface card C9
#   (설계 40 §2.4.5 '수명' (2), 사용자 결정 X-20 2026-10-16 "권고대로 구조로 막는 방향으로 진행해", X-21 승인).
#   대상 = 엔진 트리 전체(`tests/` 포함 -- C9 'test 쪽에도 걸린다'), 단 이 폴더의 위반 픽스처(`tests/structure/fixtures/`)는 뺀다.
OPEN_RUN_NAME = "open_run"
OPEN_RUN_ALLOWED_FILES = ("search/open_run.py", "search/__init__.py")       # (M-a) C9 '엔진 소스에서 open_run 참조는 이 둘뿐'
RUN_OBJECT_HOMES = {                                                        # (M-b) C9 '생성 호출은 그 정의 모듈과 open_run.py 에만'
    "S3Index": ("search/s3_index.py", "search/open_run.py"),
    "RunCounters": ("core/run_counters.py", "search/open_run.py"),
}
RUN_ENTRY = "run_stage_a"                                                   # (M-c) C9 대상 호출
RUN_PAIR_KEYWORDS = ("donors", "counters")                                  # (M-c) C6 run_stage_a 필수 키워드(튜플 풀기 순서 그대로)
PAIR_ATTRS = ("donors", "counters")                                         # C6 결과 칸(StageAResult·KernelContext·sctx.dc)
PAIR_HOLDER_PRODUCERS = ("run_stage_a", "run_stage_b", "build_kernel_context", "build_search_context")   # C6: 결과가 두 객체를 쥐는 진입
# C6: 두 객체를 칸으로 쥔 값에 이르는 속성 -- `sctx.dc`(KernelContext). test 가 쓰는 컨텍스트 칸 이름(sctx·kctx·ctx·stage_a)도 같은 값으로 본다.
# 그 밖 속성(결과의 s1·spec·report·base 스냅샷 등)은 두 객체를 담지 않는다.
CONTEXT_ATTRS = ("dc", "sctx", "kctx", "ctx", "stage_a")
CONTAINER_BUILDERS = ("dict", "list", "tuple", "set", "frozenset", "partial", "SimpleNamespace", "deque", "OrderedDict",
                      "defaultdict", "ChainMap")                            # 인자를 그대로 쥐는 생성 호출
LONG_FIXTURE_SCOPES = ("session", "module", "package", "class")             # (M-d) C9 'session·module·package 범위 fixture'(+ class: test 하나보다 김)
CONTAINER_MUTATORS = ("append", "extend", "add", "update", "setdefault", "insert", "__setitem__")   # (M-d) C9 '모듈 수준 컨테이너 변경'
CONFIG_NAMES = ("config", "pytestconfig")                                   # (M-d) C9 'request.config·config.cache·config.stash'
CONFIG_HOOKS = ("pytest_configure", "pytest_sessionstart")                  # (M-d) C9 'conftest pytest_configure'(세션 시작 훅 포함)
SERIALIZER_MODULES = ("pickle", "json", "shelve", "marshal")                # (M-f) C9
SERIALIZER_WRITES = ("dump", "dumps")                                       # (M-f) C9 '쓰기 함수(dump·dumps·Shelf 항목 대입 등)'
M_EXCLUDED_PREFIX = ("tests", "structure", "fixtures")                      # 이 폴더의 위반 픽스처 트리


@dataclass(frozen=True, order=True)
class Violation:
    kind: str
    path: str      # 엔진 루트 기준 posix 상대 경로
    line: int
    detail: str

    def __str__(self) -> str:
        return "%s:%d [%s] %s" % (self.path, self.line, self.kind, self.detail)


# ---------------------------------------------------------------- 공통

def engine_files(root: Path) -> list[Path]:
    """엔진 소스 파일(tests/ 와 숨김·__pycache__ 폴더 제외), 정렬."""
    root = Path(root)
    if not root.is_dir():
        return []
    out = []
    for p in sorted(root.rglob("*.py")):
        parts = p.relative_to(root).parts
        if parts[0] == "tests":
            continue
        if any(x == "__pycache__" or x.startswith(".") for x in parts):
            continue
        out.append(p)
    return out


def rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def parse(p: Path) -> ast.Module:
    return ast.parse(p.read_text(encoding="utf-8"), filename=str(p))


def _parents(tree: ast.AST) -> dict[int, ast.AST]:
    par = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            par[id(c)] = n
    return par


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _is_private(name: str) -> bool:
    return name.startswith("_") and not _is_dunder(name)


def _decorator_name(d: ast.expr) -> str:
    if isinstance(d, ast.Call):
        d = d.func
    if isinstance(d, ast.Attribute):
        return d.attr
    if isinstance(d, ast.Name):
        return d.id
    return ""


def _module_of(root: Path, p: Path) -> list[str]:
    """파일의 모듈 경로(패키지 이름 포함). pkg/__init__.py -> [gmid_engine, pkg]."""
    parts = list(p.relative_to(root).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return [ENGINE_PACKAGE] + parts


def _package_of(root: Path, p: Path) -> list[str]:
    mod = _module_of(root, p)
    return mod if p.name == "__init__.py" else mod[:-1]


def resolve_from(root: Path, p: Path, node: ast.ImportFrom) -> str:
    """ImportFrom 의 절대 모듈 이름(상대 import 해석)."""
    if node.level == 0:
        return node.module or ""
    pkg = _package_of(root, p)
    keep = len(pkg) - (node.level - 1)
    base = pkg[:max(keep, 0)]
    if node.module:
        base = base + node.module.split(".")
    return ".".join(base)


def module_file(root: Path, dotted: str) -> Path | None:
    """엔진 안 모듈 이름 -> 파일(없으면 None)."""
    parts = dotted.split(".")
    if not parts or parts[0] != ENGINE_PACKAGE:
        return None
    sub = parts[1:]
    if not sub:
        f = root / "__init__.py"
        return f if f.is_file() else None
    f = root.joinpath(*sub).with_suffix(".py")
    if f.is_file():
        return f
    f = root.joinpath(*sub, "__init__.py")
    return f if f.is_file() else None


def _is_engine_module(dotted: str) -> bool:
    return dotted == ENGINE_PACKAGE or dotted.startswith(ENGINE_PACKAGE + ".")


# ---------------------------------------------------------------- (A)

def _signature(n: ast.AST) -> tuple:
    if isinstance(n, ast.ClassDef):
        return ("class",)
    a = n.args
    return (
        tuple(x.arg for x in a.posonlyargs), tuple(x.arg for x in a.args),
        a.vararg.arg if a.vararg else None, tuple(x.arg for x in a.kwonlyargs),
        a.kwarg.arg if a.kwarg else None,
    )


def entry_points(tree: ast.Module) -> tuple[list[str], list[tuple]]:
    """(독립 진입점 이름 목록, 개념 목록). 개념 = 진입점 하나 또는 레지스트리 변형군 하나."""
    defs = [n for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not n.name.startswith("_")]
    refs_by_stmt = [(s, {x.id for x in ast.walk(s) if isinstance(x, ast.Name)}) for s in tree.body]
    roots = []
    for d in defs:
        used = any(d.name in names for s, names in refs_by_stmt if s is not d)
        if not used:
            roots.append(d)
    concepts = []
    for d in roots:
        regs = sorted({_decorator_name(x) for x in d.decorator_list} & set(REGISTRY_DECORATORS))
        key = ("registry", regs[0], _signature(d)) if regs else ("def", d.name)
        if key not in concepts:
            concepts.append(key)
    return [d.name for d in roots], concepts


# (A) 보충 판정 -- 오케스트레이터 결정(2026-10-07, 사용자 규칙 취지 '한 파일에 너무 많은 함수'):
#   (1) 데이터 선언 모듈(스키마 한 개념) (2) 공개 정의 0 파일 통과 (3) 비공개 모듈 = 공유 helper 검사.
DATA_CLASS_DECORATORS = ("dataclass",)
DATA_CLASS_BASES = ("NamedTuple", "Enum", "IntEnum", "StrEnum", "Flag", "IntFlag",
                    "Exception", "BaseException")
EXCEPTION_NAME_SUFFIXES = ("Error", "Exception", "Warning")   # Exception 계열 기반(ValueError 등)
DATA_CLASSMETHOD_PREFIX = "from_"                           # classmethod 생성자


def _base_name(b: ast.expr) -> str:
    if isinstance(b, ast.Subscript):
        b = b.value
    return b.attr if isinstance(b, ast.Attribute) else (b.id if isinstance(b, ast.Name) else "")


def _data_method_ok(n: ast.stmt) -> bool:
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        decs = [_decorator_name(d) for d in n.decorator_list]
        if _is_dunder(n.name) and not decs:
            return True
        if decs == ["property"]:
            return True
        return decs == ["classmethod"] and n.name.startswith(DATA_CLASSMETHOD_PREFIX)
    return not isinstance(n, ast.ClassDef)          # 필드·대입·docstring 은 허용, 중첩 클래스는 불허


def is_data_module(tree: ast.Module) -> bool:
    """최상위 공개 정의가 전부 클래스이고 각 클래스가 dataclass/NamedTuple/Enum/Exception 계열이며
    자체 메서드가 dunder·property·classmethod 생성자(from_*)뿐인 모듈."""
    public = [n for n in tree.body
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not n.name.startswith("_")]
    if not public or not all(isinstance(n, ast.ClassDef) for n in public):
        return False
    data = set()
    changed = True
    while changed:                                  # 같은 파일의 데이터 클래스를 기반으로 삼는 클래스도 계열
        changed = False
        for c in tree.body:
            if not isinstance(c, ast.ClassDef) or c.name in data:
                continue
            bases = [_base_name(b) for b in c.bases]
            kin = (any(_decorator_name(d) in DATA_CLASS_DECORATORS for d in c.decorator_list)
                   or any(b in DATA_CLASS_BASES or b in data or b.endswith(EXCEPTION_NAME_SUFFIXES) for b in bases))
            if kin and all(_data_method_ok(s) for s in c.body):
                data.add(c.name)
                changed = True
    return all(c.name in data for c in public)


def helper_public_functions(tree: ast.Module) -> dict[str, int]:
    """비공개 모듈의 공개 함수 이름 -> 행. 공개 최상위 def 와, 같은 파일 최상위 함수 이름을 값으로 갖는
    공개 대입(별칭, 예: `build_rows = _build_rows`)을 모두 센다(별칭으로 공개한 helper 도 2파일 사용 조건 적용).
    오케스트레이터 결정 2026-10-07."""
    defs = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    out = {}
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("_"):
            out[n.name] = n.lineno
        elif isinstance(n, (ast.Assign, ast.AnnAssign)) and isinstance(n.value, ast.Name) and n.value.id in defs:
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            for t in targets:
                if isinstance(t, ast.Name) and not t.id.startswith("_"):
                    out.setdefault(t.id, n.lineno)
    return out


def helper_users(root: Path, p: Path) -> dict[str, set[str]]:
    """비공개 모듈 p 의 공개 함수 -> 그것을 import(또는 모듈 import 뒤 속성 사용)하는 같은 패키지 파일 집합."""
    tree = parse(p)
    users = {f: set() for f in helper_public_functions(tree)}
    dotted = ".".join(_module_of(root, p))
    parts = p.relative_to(root).parts
    scope = [q for q in engine_files(root)
             if q != p and (len(parts) == 1 or q.relative_to(root).parts[0] == parts[0])]
    for q in scope:
        bindings = set()
        qt = parse(q)
        for n in ast.walk(qt):
            if isinstance(n, ast.ImportFrom):
                mod = resolve_from(root, q, n)
                for a in n.names:
                    if mod == dotted and a.name in users:
                        users[a.name].add(rel(root, q))
                    elif mod + "." + a.name == dotted:
                        bindings.add(a.asname or a.name)
        for n in ast.walk(qt):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) \
                    and n.value.id in bindings and n.attr in users:
                users[n.attr].add(rel(root, q))
    return users


HELPER_MIN_USERS = 2   # '두 파일 이상에서 쓰이는 helper 만 공용 helper 모듈'(D 1.2 (나)4 (B))


def check_a(root: Path) -> tuple[int, list[Violation]]:
    root = Path(root)
    targets = [p for p in engine_files(root) if p.name != "__init__.py"]
    out = []
    for p in targets:
        tree = parse(p)
        if p.name.startswith("_"):
            lines = helper_public_functions(tree)
            for f, who in helper_users(root, p).items():
                if len(who) < HELPER_MIN_USERS:
                    out.append(Violation("helper_single_user", rel(root, p), lines[f],
                                         "공용 helper %s 사용 파일 %d개(2개 이상이어야 함, 하나면 그 파일로 옮김): %s"
                                         % (f, len(who), sorted(who))))
            continue
        names, concepts = entry_points(tree)
        if not concepts and not names:
            public = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                      and not n.name.startswith("_")]
            if not public:
                continue                            # (2) 공개 정의 0(상수·단위 표)
        if is_data_module(tree):
            continue                                # (1) 스키마 한 개념
        if len(concepts) != 1:
            out.append(Violation("entry_points", rel(root, p), 1,
                                 "독립 진입점 개념 %d개(정확히 1개여야 함): %s" % (len(concepts), names)))
    return len(targets), out


# ---------------------------------------------------------------- (B)

def check_b(root: Path) -> tuple[int, list[Violation]]:
    root = Path(root)
    targets = engine_files(root)
    out = []
    for p in targets:
        tree = parse(p)
        bound = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    bound.add(a.asname or a.name.split(".")[0])
            elif isinstance(n, ast.ImportFrom):
                mod = resolve_from(root, p, n)
                for a in n.names:
                    bound.add(a.asname or a.name)
                    if a.name == "*" or not _is_private(a.name):
                        continue
                    # 모듈 파일 자체(예: from . import _helpers_geom)는 '다른 파일의 _ 이름'이 아니다.
                    if _is_engine_module(mod) and module_file(root, mod + "." + a.name) is not None:
                        continue
                    out.append(Violation("private_import", rel(root, p), n.lineno,
                                         "from %s import %s" % (mod, a.name)))
        for n in ast.walk(tree):
            if isinstance(n, ast.Attribute) and _is_private(n.attr):
                base = n.value
                while isinstance(base, ast.Attribute):
                    base = base.value
                if isinstance(base, ast.Name) and base.id in bound:
                    out.append(Violation("private_attr", rel(root, p), n.lineno,
                                         "%s 의 _ 이름 접근 .%s" % (base.id, n.attr)))
    return len(targets), out


# ---------------------------------------------------------------- (C)

def public_api(root: Path, pkg: str) -> tuple[str, ...] | None:
    """하위 패키지 __init__.py 의 정적 __all__(없거나 정적이 아니면 None)."""
    f = Path(root) / pkg / "__init__.py"
    if not f.is_file():
        return None
    for s in parse(f).body:
        targets = s.targets if isinstance(s, ast.Assign) else ([s.target] if isinstance(s, ast.AnnAssign) else [])
        if any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets):
            v = s.value
            if isinstance(v, (ast.Tuple, ast.List)) and all(
                    isinstance(e, ast.Constant) and isinstance(e.value, str) for e in v.elts):
                return tuple(e.value for e in v.elts)
            return None
    return None


def _subpackages(root: Path) -> list[str]:
    pk = set()
    for p in engine_files(root):
        parts = p.relative_to(root).parts
        if len(parts) > 1:
            pk.add(parts[0])
    return sorted(pk)


def _sccs(nodes: list[str], edges: dict[str, set[str]]) -> list[list[str]]:
    index, low, on, stack, out = {}, {}, set(), [], []
    counter = [0]

    def visit(v: str) -> None:
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        for w in sorted(edges.get(v, ())):
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            out.append(sorted(comp))

    for v in sorted(nodes):
        if v not in index:
            visit(v)
    return out


def check_c(root: Path) -> tuple[int, list[Violation]]:
    root = Path(root)
    files = engine_files(root)
    out = []
    for pkg in _subpackages(root):
        if pkg not in LAYER:
            out.append(Violation("unknown_layer", pkg, 0, "층 번호가 없는 하위 패키지(설계 3.1 표 밖)"))
    edges: dict[str, set[str]] = {}
    for p in files:
        r = rel(root, p)
        parts = p.relative_to(root).parts
        own = parts[0] if len(parts) > 1 else None   # None = 루트 모듈(gmid_engine/__init__.py 등)
        edges.setdefault(r, set())

        def edge(dotted: str) -> None:
            f = module_file(root, dotted)
            if f is not None and f != p:
                edges[r].add(rel(root, f))

        for n in ast.walk(parse(p)):
            if isinstance(n, ast.Import):
                for a in n.names:
                    if not _is_engine_module(a.name):
                        continue
                    sub = a.name.split(".")
                    edge(a.name)
                    tgt = sub[1] if len(sub) > 1 else None
                    if tgt != own:
                        out.append(Violation("import_form", r, n.lineno,
                                             "import %s -- 다른 하위 패키지는 'from %s.<pkg> import <공개 이름>'만"
                                             % (a.name, ENGINE_PACKAGE)))
                continue
            if not isinstance(n, ast.ImportFrom):
                continue
            mod = resolve_from(root, p, n)
            if not _is_engine_module(mod):
                continue
            sub = mod.split(".")
            edge(mod)
            for a in n.names:
                if a.name != "*":
                    edge(mod + "." + a.name)
            tgt = sub[1] if len(sub) > 1 else None
            if tgt is None:
                for a in n.names:
                    if own is not None and a.name != own:
                        out.append(Violation("import_form", r, n.lineno,
                                             "from %s import %s -- 루트·하위 패키지 모듈 객체 import 금지"
                                             % (mod, a.name)))
                continue
            if tgt == own:
                continue
            if own is not None:
                if own not in LAYER or tgt not in LAYER:
                    out.append(Violation("unknown_layer", r, n.lineno, "%s -> %s: 층 번호 없음" % (own, tgt)))
                elif LAYER[tgt] >= LAYER[own]:
                    out.append(Violation("layer_order", r, n.lineno, "%s(%d) -> %s(%d): 작은 번호 쪽으로만"
                                         % (own, LAYER[own], tgt, LAYER[tgt])))
            if len(sub) > 2:
                out.append(Violation("non_public_path", r, n.lineno,
                                     "from %s import ... -- 다른 하위 패키지는 %s.%s(__init__)에서만"
                                     % (mod, ENGINE_PACKAGE, tgt)))
                continue
            api = public_api(root, tgt)
            for a in n.names:
                if api is None or a.name == "*" or a.name not in api:
                    out.append(Violation("not_in_all", r, n.lineno,
                                         "from %s import %s -- %s/__init__.py __all__ 밖(__all__=%s)"
                                         % (mod, a.name, tgt, api)))
    for comp in _sccs(list(edges), edges):
        if len(comp) > 1 or comp[0] in edges.get(comp[0], ()):
            out.append(Violation("import_cycle", comp[0], 0, "순환: %s" % " <-> ".join(comp)))
    return len(files), out


# ---------------------------------------------------------------- 복사 등록부 (D·E·G 예외)
#
# 옛 엔진 정의를 본문 그대로 복사한 최상위 정의는 하위 패키지의 `_copy_manifest.py`에 등록한다.
# 등록 정의 노드 범위 안의 D·E·G 위반만 면제하되, 아래가 전부 성립할 때만이다(하나라도 깨지면 면제 취소 + 위반):
#   (1) 등록부 형식이 맞다 (2) 그 정의가 manifest 폴더의 그 파일에 최상위로 정확히 1개
#   (3) 복사본 정의의 AST 해시 == 등록 해시 (4) 정의 안 규칙 D 밖 리터럴 목록 == 등록 목록
#   (5) 원본 파일(엔진 밖)의 등록 행 범위에 같은 이름 정의가 있고 그 AST 해시 == 등록 해시.
# 해시·리터럴은 이 검사기가 직접 다시 잰다(등록부 작성자의 계산을 쓰지 않는다 -- 작성자≠검증자).

def _def_name(n: ast.stmt) -> str | None:
    """최상위 정의 이름: def·class, 이름 하나에 대한 대입(Assign·AnnAssign). 그 밖은 None."""
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return n.name
    if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
        return n.targets[0].id
    if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
        return n.target.id
    return None


def copy_hash(node: ast.AST) -> str:
    """정의 노드의 AST 해시 = sha256(ast.dump(annotate_fields=True, include_attributes=False)).
    docstring·데코레이터 포함, 주석·위치 제외. ast.dump 출력은 Python 버전에 따라 다를 수 있다(README)."""
    text = ast.dump(node, annotate_fields=True, include_attributes=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _literal_text(n: ast.Constant, parent: dict[int, ast.AST]) -> str:
    par = parent.get(id(n))
    negated = isinstance(par, ast.UnaryOp) and isinstance(par.op, ast.USub)
    return ("-%r" if negated else "%r") % (n.value,)


def copy_literals(node: ast.AST, parent: dict[int, ast.AST]) -> tuple[str, ...]:
    """정의 안 숫자 리터럴 중 규칙 D 허용 집합 밖인 것의 repr(음수는 '-' 앞붙임), 정렬, 중복 유지.
    derive 태그는 보지 않는다(복사본은 원본 그대로라 태그가 없다)."""
    return tuple(sorted(_literal_text(n, parent) for n in ast.walk(node)
                        if isinstance(n, ast.Constant) and type(n.value) in (int, float, complex)
                        and not _number_allowed(n, parent)))


def _literal(node: ast.AST | None):
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return None


def _plain_relative(text: str, suffix: str = "") -> bool:
    p = PurePosixPath(text)
    return bool(text) and "\\" not in text and not p.is_absolute() and ".." not in p.parts \
        and ":" not in text and p.name.endswith(suffix)


def _entry_ok(e) -> bool:
    return (isinstance(e, tuple) and len(e) == 5 and all(isinstance(x, str) for x in e[:4])
            and isinstance(e[4], tuple) and all(isinstance(x, str) for x in e[4])
            and _plain_relative(e[0], ".py") and PurePosixPath(e[0]).name != COPY_MANIFEST_NAME
            and COPY_ROWS.match(e[2]) is not None and COPY_HASH.match(e[3]) is not None)


def _find_source(root: Path, text: str) -> Path | None:
    """원본 경로 = 엔진 루트의 조상 폴더 중 처음으로 <조상>/<COPY_SOURCE> 파일이 있는 곳(진짜 트리: 저장소 루트)."""
    for anc in root.parents:
        f = anc / text
        if f.is_file():
            return f.resolve()
    return None


@dataclass(frozen=True)
class CopyAudit:
    entries: int            # 등록부 항목 수(형식 위반 포함)
    compared: int           # 원본과 대조한 항목 수
    exempt: dict            # 엔진 상대 경로 -> 면제 정의 이름 frozenset (검증 통과 항목만)
    violations: tuple


def copy_audit(root: Path) -> CopyAudit:
    root = Path(root).resolve()
    out: list[Violation] = []
    exempt: dict[str, set[str]] = {}
    entries = compared = 0
    cache: dict[Path, tuple] = {}

    def load(p: Path) -> tuple:
        if p not in cache:
            t = parse(p)
            cache[p] = (t, _parents(t))
        return cache[p]

    for m in engine_files(root):
        if m.name != COPY_MANIFEST_NAME:
            continue
        mr = rel(root, m)
        if len(m.relative_to(root).parts) < 2:
            out.append(Violation("copy_manifest_location", mr, 0, "등록부는 하위 패키지 폴더 안에만(루트 등록부는 무시)"))
            continue
        top = {}
        for s in parse(m).body:
            if isinstance(s, (ast.Assign, ast.AnnAssign)) and _def_name(s) in (COPY_MANIFEST_SOURCE, COPY_MANIFEST_TABLE):
                top[_def_name(s)] = s
        src_stmt, tab_stmt = top.get(COPY_MANIFEST_SOURCE), top.get(COPY_MANIFEST_TABLE)
        src_text = _literal(src_stmt.value) if src_stmt is not None else None
        if not (isinstance(src_text, str) and _plain_relative(src_text)):
            out.append(Violation("copy_manifest_format", mr, src_stmt.lineno if src_stmt is not None else 0,
                                 "%s 는 저장소 기준 상대 경로 문자열 상수여야 함" % COPY_MANIFEST_SOURCE))
            continue
        if tab_stmt is None or not isinstance(tab_stmt.value, (ast.Tuple, ast.List)):
            out.append(Violation("copy_manifest_format", mr, tab_stmt.lineno if tab_stmt is not None else 0,
                                 "%s 는 항목 tuple 들의 정적 tuple 이어야 함" % COPY_MANIFEST_TABLE))
            continue
        source = _find_source(root, src_text)
        if source is None:
            out.append(Violation("copy_source_missing", mr, src_stmt.lineno, "원본 %r 없음" % src_text))
        elif root in source.parents:
            out.append(Violation("copy_source_in_engine", mr, src_stmt.lineno,
                                 "원본 %r 이 엔진 트리 안(복사본을 원본으로 삼을 수 없음)" % src_text))
            source = None
        rows = []
        for el in tab_stmt.value.elts:
            entries += 1
            e = _literal(el)
            if not _entry_ok(e):
                out.append(Violation("copy_manifest_format", mr, el.lineno,
                                     "항목 형식 (manifest 폴더 안 .py, 정의 이름, '시작~끝', sha256 hex, 리터럴 문자열 tuple) 아님"))
                continue
            rows.append((el.lineno, e))
        counts = Counter((e[0], e[1]) for _, e in rows)
        seen = set()
        for line, (fname, name, span, digest, lits) in rows:
            if counts[(fname, name)] > 1:
                if (fname, name) in seen:
                    out.append(Violation("copy_manifest_duplicate", mr, line, "%s:%s 중복 등록(모두 면제 안 함)" % (fname, name)))
                seen.add((fname, name))
                continue
            ok = True
            target = m.parent / fname
            nodes = []
            if target.is_file():
                tree, parent = load(target)
                nodes = [n for n in tree.body if _def_name(n) == name]
            if len(nodes) != 1:
                out.append(Violation("copy_missing_definition", mr, line,
                                     "%s 의 최상위 정의 %s %d개(정확히 1개여야 함)" % (fname, name, len(nodes))))
                ok = False
            else:
                node, tr = nodes[0], rel(root, target)
                if copy_hash(node) != digest:
                    out.append(Violation("copy_definition_changed", tr, node.lineno,
                                         "복사 정의 변경: %s 의 AST 해시가 등록부와 다름(면제 취소)" % name))
                    ok = False
                got = copy_literals(node, parent)
                if got != tuple(sorted(lits)):
                    out.append(Violation("copy_literal_mismatch", tr, node.lineno,
                                         "%s 리터럴 %s != 등록부 %s(면제 취소)" % (name, list(got), sorted(lits))))
                    ok = False
            if source is None:
                ok = False
            else:
                compared += 1
                a, b = (int(x) for x in COPY_ROWS.match(span).groups())
                stree, _ = load(source)
                hits = [n for n in stree.body if _def_name(n) == name and n.lineno == a and n.end_lineno == b]
                if len(hits) != 1:
                    out.append(Violation("copy_source_mismatch", mr, line,
                                         "원본 %s %s행에 최상위 정의 %s 없음" % (src_text, span, name)))
                    ok = False
                elif copy_hash(hits[0]) != digest:
                    out.append(Violation("copy_source_mismatch", mr, line,
                                         "원본 %s %s행 %s 의 AST 해시가 등록부와 다름" % (src_text, span, name)))
                    ok = False
            if ok:
                exempt.setdefault(rel(root, target), set()).add(name)
    return CopyAudit(entries, compared, {k: frozenset(v) for k, v in exempt.items()}, tuple(sorted(out)))


def _exempt_nodes(tree: ast.Module, names) -> set[int]:
    """면제 정의(최상위) 노드와 그 하위 노드 전부의 id."""
    ids = set()
    for s in tree.body:
        if _def_name(s) in names:
            ids.update(id(x) for x in ast.walk(s))
    return ids


def check_copy_manifest(root: Path) -> tuple[int, list[Violation]]:
    """등록부 형식 + 복사본 쪽 대조((1)~(4)). 대상 수 = 등록부 항목 수."""
    a = copy_audit(root)
    return a.entries, [v for v in a.violations if v.kind not in COPY_SOURCE_KINDS]


def check_copy_source(root: Path) -> tuple[int, list[Violation]]:
    """원본 쪽 대조((5)). 대상 수 = 원본과 대조한 항목 수."""
    a = copy_audit(root)
    return a.compared, [v for v in a.violations if v.kind in COPY_SOURCE_KINDS]


# ---------------------------------------------------------------- (D)

def defined_functions(root: Path) -> set[str]:
    names = set()
    for p in engine_files(root):
        for n in parse(p).body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(n.name)
    return names


def _number_allowed(n: ast.Constant, parent: dict[int, ast.AST]) -> bool:
    v = n.value
    if isinstance(v, complex):
        return False
    par = parent.get(id(n))
    negated = isinstance(par, ast.UnaryOp) and isinstance(par.op, ast.USub)
    if v == 0 or v == 1:
        return True                     # 0, 1, -1 (-0 은 0)
    if v == 2 and not negated and (isinstance(par, ast.BinOp)
                                    or (isinstance(par, ast.AugAssign) and par.value is n)):
        return True                     # 산술식의 2
    cur, up = n, par                    # 인덱스·슬라이스: x[3], x[-2], x[1:5], x[:, 2]
    while isinstance(up, (ast.UnaryOp, ast.Tuple, ast.Slice)):
        cur, up = up, parent.get(id(up))
    return isinstance(up, ast.Subscript) and up.slice is cur


def check_d(root: Path) -> tuple[int, list[Violation]]:
    root = Path(root)
    targets = [p for p in engine_files(root) if rel(root, p) not in NUMERIC_LITERAL_HOME]
    known = defined_functions(root)
    exempt = copy_audit(root).exempt
    out = []
    for p in targets:
        text = p.read_text(encoding="utf-8")
        lines = text.split("\n")
        tree = ast.parse(text, filename=str(p))
        parent = _parents(tree)
        skip = _exempt_nodes(tree, exempt.get(rel(root, p), ()))
        for n in ast.walk(tree):
            if not (isinstance(n, ast.Constant) and type(n.value) in (int, float, complex)):
                continue
            if _number_allowed(n, parent) or id(n) in skip:
                continue
            m = DERIVE_TAG.search(lines[n.lineno - 1])
            if m and m.group(1) in known:
                continue
            shown = _literal_text(n, parent)
            why = " (derive 태그의 함수 %r 없음)" % m.group(1) if m else ""
            out.append(Violation("numeric_literal", rel(root, p), n.lineno, shown + why))
    return len(targets), out


# ---------------------------------------------------------------- (E)

TERMINAL_KEYS = ("drain", "gate", "source", "bulk", "body")


def library_names(library_dir: Path) -> tuple[list[str], dict[str, list[str]]]:
    """(회로 목록, 이름 -> 출처 목록). 회로 이름·파일 이름·소자·수동소자·이상원 이름,
    넷(단자·terminals·포트·supply_nets -- 레일 포함). '_' 로 시작하는 파일(_TEMPLATE)·키는 제외."""
    names: dict[str, set[str]] = {}
    circuits = []

    def add(v, origin: str) -> None:
        if isinstance(v, str) and v:
            names.setdefault(v, set()).add(origin)

    def take(path: Path, circuit: str, seen: set) -> None:
        if path in seen or not path.is_file():
            return
        seen.add(path)
        d = json.loads(path.read_text(encoding="utf-8"))
        add(d.get("topology_name"), circuit + ":topology_name")
        for e in d.get("netlist") or []:
            add(e.get("name"), circuit + ":device")
            for k in TERMINAL_KEYS:
                add(e.get(k), circuit + ":net")
        for key in ("passive_elements", "ideal_sources"):
            for e in d.get(key) or []:
                add(e.get("name"), circuit + ":" + key)
                for t in e.get("terminals") or []:
                    add(t, circuit + ":net")
        for k in (d.get("ports") or {}):
            if not k.startswith("_"):
                add(k, circuit + ":port")
        for k in d.get("supply_nets") or []:
            add(k, circuit + ":supply_net")
        for linked in d.get("linked_topology_files") or []:
            take(path.parent / linked, circuit, seen)

    for f in sorted(Path(library_dir).glob("*.topology.json")):
        if f.name.startswith("_"):
            continue
        circuit = f.name[:-len(".topology.json")]
        circuits.append(circuit)
        add(circuit, circuit + ":file")
        take(f, circuit, set())
    return circuits, {k: sorted(v) for k, v in names.items()}


def check_e(root: Path, names: dict[str, list[str]]) -> tuple[int, list[Violation]]:
    root = Path(root)
    targets = engine_files(root)
    exempt = copy_audit(root).exempt
    out = []
    for p in targets:
        tree = parse(p)
        skip = _exempt_nodes(tree, exempt.get(rel(root, p), ()))
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in names and id(n) not in skip:
                out.append(Violation("name_literal", rel(root, p), n.lineno,
                                     "%r = %s" % (n.value, ", ".join(names[n.value][:4]))))
    return len(targets), out


# ---------------------------------------------------------------- (F)

def _broad(h: ast.ExceptHandler) -> bool:
    if h.type is None:
        return True
    elts = h.type.elts if isinstance(h.type, ast.Tuple) else [h.type]
    return any((isinstance(x, ast.Name) and x.id in BROAD_EXCEPTION_NAMES)
               or (isinstance(x, ast.Attribute) and x.attr in BROAD_EXCEPTION_NAMES) for x in elts)


def check_f(root: Path) -> tuple[int, list[Violation]]:
    root = Path(root)
    targets = engine_files(root)
    out = []
    for p in targets:
        r = rel(root, p)
        hits = sorted((h.lineno for h in ast.walk(parse(p)) if isinstance(h, ast.ExceptHandler) and _broad(h)))
        allowed = BROAD_EXCEPT_ENTRY_MAX if r == BROAD_EXCEPT_ENTRY_FILE else 0
        for line in hits[allowed:]:
            out.append(Violation("broad_except", r, line, "except:/Exception/BaseException"))
    return len(targets), out


# ---------------------------------------------------------------- (G)

def _module_level(body: list[ast.stmt]):
    """모듈 최상위 문장(if/try/with/for/while/match 블록 안 포함, def·class 안은 제외)."""
    for s in body:
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        yield s
        for field in ("body", "orelse", "finalbody"):
            sub = getattr(s, field, None)
            if isinstance(sub, list):
                yield from _module_level(sub)
        for h in getattr(s, "handlers", []) or []:
            yield from _module_level(h.body)
        for c in getattr(s, "cases", []) or []:
            yield from _module_level(c.body)


def _mutable_value(v: ast.expr | None) -> bool:
    if v is None:
        return False
    if isinstance(v, (ast.Dict, ast.List, ast.Set, ast.DictComp, ast.ListComp, ast.SetComp)):
        return True
    if isinstance(v, ast.Tuple):
        return any(_mutable_value(e) for e in v.elts)
    if isinstance(v, ast.Call):
        f = v.func
        name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        return name in MUTABLE_CONSTRUCTORS
    return False


def check_g(root: Path) -> tuple[int, list[Violation]]:
    root = Path(root)
    targets = engine_files(root)
    exempt = copy_audit(root).exempt
    out = []
    for p in targets:
        r = rel(root, p)
        tree = parse(p)
        skip = _exempt_nodes(tree, exempt.get(r, ()))
        for s in _module_level(tree.body):
            if id(s) in skip:
                continue
            if isinstance(s, ast.Assign):
                tnames = [t.id for t in s.targets if isinstance(t, ast.Name)]
                value = s.value
            elif isinstance(s, ast.AnnAssign):
                tnames = [s.target.id] if isinstance(s.target, ast.Name) else []
                value = s.value
            else:
                continue
            if tnames and all(t in MODULE_LEVEL_EXEMPT_NAMES for t in tnames):
                continue
            if _mutable_value(value):
                out.append(Violation("module_mutable", r, s.lineno,
                                     "모듈 수준 가변 객체 대입 %s" % (tnames or "<target>")))
        for n in ast.walk(tree):
            if id(n) in skip:
                continue
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for d in n.decorator_list:
                    if _decorator_name(d) in CACHE_DECORATORS:
                        out.append(Violation("global_cache", r, d.lineno,
                                             "@%s on %s" % (_decorator_name(d), n.name)))
            if isinstance(n, ast.Global):
                out.append(Violation("global_stmt", r, n.lineno, "global %s" % ", ".join(n.names)))
    return len(targets), out


# ---------------------------------------------------------------- (H)

def h_exempt(p: Path) -> bool:
    """H 제외(오케스트레이터 결정 2026-10-07, 근거: 공개 동작이 없는 등록부·표): `_`로 시작하는 모듈 중
    최상위 함수·클래스가 하나도 없는 것(상수 표·등록부, 예: `_copy_manifest.py`) 또는 데이터 선언 모듈."""
    if not p.name.startswith("_"):
        return False
    tree = parse(p)
    if not any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for n in tree.body):
        return True
    return is_data_module(tree)


def check_h(root: Path) -> tuple[int, list[Violation]]:
    root = Path(root)
    sources = [p for p in engine_files(root)
               if p.name != "__init__.py" and len(p.relative_to(root).parts) > 1 and not h_exempt(p)]
    out = []
    for p in sources:
        parts = p.relative_to(root).parts
        want = root.joinpath("tests", *parts[:-1], "test_" + parts[-1])
        if not want.is_file():
            out.append(Violation("missing_test", rel(root, p), 0, "없음: %s" % rel(root, want)))
    pkgs = set(_subpackages(root)) | set(LAYER_ORDER)
    tests_dir = root / "tests"
    if tests_dir.is_dir():
        for t in sorted(tests_dir.rglob("test_*.py")):
            tparts = t.relative_to(tests_dir).parts
            if len(tparts) < 2 or tparts[0] not in pkgs or tparts[0] in CROSS_CUTTING_TEST_DIRS:
                continue
            src = root.joinpath(*tparts[:-1], tparts[-1][len("test_"):])
            if not src.is_file():
                out.append(Violation("orphan_test", rel(root, t), 0, "원본 없음: %s" % rel(root, src)))
    return len(sources), out


# ---------------------------------------------------------------- (I)
#
# 회로별 정보로 행동을 정하지 않는다. 사용자 대원칙(2026-10-07): "topology 에 종속된 엔진은 만들지 않는다.
# 임의의 topology 에 적용할 수 있어야 한다." 두 부분:
#   (a) 회로 식별·태그 키 문자열 리터럴로 조회 금지(아래 키 목록, 출처는 줄마다).
#   (b) 회로·소자·넷 이름을 문자열 리터럴과 비교해 분기하는 코드 금지 -- 리터럴이 library 이름 집합의 원소이면
#       규칙 E 가 이미 잡으므로 (b)는 그 밖 리터럴만 본다(E 와 겹치지 않는 부분).
# 규칙 E 와 마찬가지로 문자열 전체 일치·대소문자 구분. 예외는 (파일, 허용 키) 명시 목록 + 사유만.

# (a) 키 목록 -- 출처:
#   AC = gmid_engine/authoring/CONTRACT.md 머리 10행 "태그 키는 읽지 않는다: device_roles·symmetry·sizing_roles·
#        compensation" (= authoring topology_schema.IGNORED_TAG_KEYS, IC4)
#   U50 = P U-50(1197행) "유도 입력으로 쓰지 않는 키: device_roles, vertical_stack_id, fold_group, headroom_role,
#        shared_gm_id_groups, budget_reference_device, 손선언 theta·stage 구성"
#   IC4 = P IC4(852행) "headroom_role/gm_id_role/L_role 전부 제거해도 결과 동일"
#   LIB = assets/library/*.topology.json 의 태그 섹션(AC 4개) 하위 키 중 역할·대응 선언인 것 -- 섹션 전체가 유도 입력이
#        아니므로(AC·U50) 그 하위 키로 바로 조회하는 것도 같은 우회다(README '규칙 I' 해석 2)
#   ID = 회로 식별 키(과제 지시 2026-10-07 + schema REQUIRED_KEYS): 이름으로 회로를 고르는 입구
TAG_SECTION_KEYS = ("device_roles", "symmetry", "sizing_roles", "compensation")                 # AC
TAG_ROLE_KEYS_U50 = ("vertical_stack_id", "fold_group", "headroom_role",
                     "shared_gm_id_groups", "budget_reference_device")                          # U50
TAG_ROLE_KEYS_IC4 = ("gm_id_role", "L_role")                                                  # IC4 (headroom_role 은 U50)
TAG_ROLE_KEYS_LIBRARY = ("gm_id_match_vgs_of", "vds_match_vgs_of", "same_as_device",           # LIB device_roles.*
                         "matching_pairs",                                                    # LIB symmetry.*
                         "stage_devices", "vds_kvl_groups")                                   # LIB compensation.* (U50 'stage 구성')
CIRCUIT_ID_KEYS = ("topology_name",)                                                          # ID
FORBIDDEN_LOOKUP_KEYS = (TAG_SECTION_KEYS + TAG_ROLE_KEYS_U50 + TAG_ROLE_KEYS_IC4
                         + TAG_ROLE_KEYS_LIBRARY + CIRCUIT_ID_KEYS)
# 일부러 뺀 태그 하위 키(README '규칙 I' 해석 3): device_roles.*.vsb(물리량 이름 -- 엔진이 유도한 값의 키와 겹친다),
# sizing_roles.{theta, metrics, constraints, objective}·compensation.{function, notes, parameters}·symmetry.dispositions
# (일반 낱말 -- spec·constraints 는 U50 이 입력으로 둔다). 섹션 키 자체는 위 목록에 있어 섹션을 거쳐 읽는 길은 막힌다.
# library 태그 섹션에 새 하위 키가 생기면 둘 중 어디에 넣을지 정해야 test 가 통과한다(test_rule_i_library_tag_subkeys_classified).
TAG_SUBKEYS_NOT_BANNED = ("vsb", "theta", "metrics", "constraints", "objective",
                          "function", "notes", "parameters", "dispositions")

# (a) 조회 형식: x["k"], x.get("k")/pop/setdefault/__getitem__/__contains__("k"), "k" in x, getattr/hasattr(x, "k"),
#     match 의 {"k": ...} 패턴, 속성 x.k
LOOKUP_METHODS = ("get", "pop", "setdefault", "__getitem__", "__contains__")
LOOKUP_BUILTINS = ("getattr", "hasattr")

# (a) 예외: (엔진 상대 경로 또는 '폴더/' 접두, 허용 키 tuple, 사유). 파일 단위 명시 목록.
TAG_LOOKUP_EXEMPT = (
    ("authoring/topology_schema.py", ("topology_name",),
     "스키마 화이트리스트 검사 -- topology_name 의 존재·형식(비어 있지 않은 문자열)만 본다(authoring CONTRACT 3.2)"),
    ("authoring/topology_load.py", ("topology_name",),
     "로드 결과 TopologyDoc.name 에 출처 기록으로 담는다 -- connectivity_fp 투영 밖, 행동 결정 아님(authoring CONTRACT 2절)"),
    ("report/", ("topology_name",),
     "보고 모듈이 topology_name 을 결과 JSON·보고서 출력용으로 담는다(과제 지시 2026-10-07)"),
)

# (b) 식별 표현: 회로·원소·넷 이름을 담는 속성·키. 비교 상대가 문자열 리터럴이면 이름 분기다.
#     출처: authoring CONTRACT 2절 필드(TopologyDoc.name·connectivity_fp·file_sha256, DeviceDecl name·d·g·s·bulk,
#     PassiveDecl/SourceDecl name·terminals, PortDecl net, DcEdge element·nets) + topology JSON 원소 키(3.4·3.6).
IDENTITY_ATTRS = ("name", "topology_name", "connectivity_fp", "file_sha256",
                  "d", "g", "s", "bulk", "terminals", "net", "nets", "element")
IDENTITY_KEYS = ("name", "topology_name", "drain", "gate", "source", "bulk", "terminals")
IDENTITY_STR_METHODS = ("startswith", "endswith", "find", "rfind", "index", "rindex", "count", "__contains__", "__eq__")
REGEX_FUNCS = ("match", "search", "fullmatch")


def _str_const(n) -> str | None:
    return n.value if isinstance(n, ast.Constant) and isinstance(n.value, str) else None


def _tag_exempt(path: str, key: str) -> bool:
    return any((path == place or (place.endswith("/") and path.startswith(place))) and key in keys
               for place, keys, _ in TAG_LOOKUP_EXEMPT)


def _tag_lookups(tree: ast.Module):
    """(행, 키, 형식) -- (a) 조회."""
    keys = set(FORBIDDEN_LOOKUP_KEYS)
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript):
            k = _str_const(n.slice)
            if k in keys:
                yield n.lineno, k, "x[%r]" % k
        elif isinstance(n, ast.Call):
            f, args = n.func, n.args
            if isinstance(f, ast.Attribute) and f.attr in LOOKUP_METHODS and args and _str_const(args[0]) in keys:
                yield n.lineno, args[0].value, "x.%s(%r)" % (f.attr, args[0].value)
            elif isinstance(f, ast.Name) and f.id in LOOKUP_BUILTINS and len(args) >= 2 and _str_const(args[1]) in keys:
                yield n.lineno, args[1].value, "%s(x, %r)" % (f.id, args[1].value)
        elif isinstance(n, ast.Compare):
            ops = [n.left] + n.comparators
            for i, op in enumerate(n.ops):
                k = _str_const(ops[i])
                if isinstance(op, (ast.In, ast.NotIn)) and k in keys:
                    yield n.lineno, k, "%r in x" % k
        elif isinstance(n, ast.MatchMapping):
            for kn in n.keys:
                k = _str_const(kn)
                if k in keys:
                    yield n.lineno, k, "case {%r: ...}" % k
        elif isinstance(n, ast.Attribute) and n.attr in keys:
            yield n.lineno, n.attr, "x.%s" % n.attr


def _is_identity(n) -> bool:
    if isinstance(n, ast.Attribute):
        return n.attr in IDENTITY_ATTRS
    if isinstance(n, ast.Subscript):
        return _str_const(n.slice) in IDENTITY_KEYS
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get" and n.args:
        return _str_const(n.args[0]) in IDENTITY_KEYS
    return False


def _str_literals(n) -> list[str]:
    """비교 상대의 문자열 리터럴: 상수 하나, 또는 상수들의 tuple/list/set(멤버십). 빈 문자열은 이름이 아니다."""
    if _str_const(n):
        return [n.value]
    if isinstance(n, (ast.Tuple, ast.List, ast.Set)):
        return [e.value for e in n.elts if _str_const(e)]
    return []


def _pattern_literals(p) -> list[str]:
    if isinstance(p, ast.MatchValue):
        return [p.value.value] if _str_const(p.value) else []
    if isinstance(p, ast.MatchOr):
        return [s for q in p.patterns for s in _pattern_literals(q)]
    if isinstance(p, ast.MatchAs) and p.pattern is not None:
        return _pattern_literals(p.pattern)
    return []


def _name_branches(tree: ast.Module):
    """(행, 리터럴 목록, 형식) -- (b) 이름 분기."""
    for n in ast.walk(tree):
        if isinstance(n, ast.Compare):
            ops = [n.left] + n.comparators
            for i in range(len(n.ops)):
                a, b = ops[i], ops[i + 1]
                for ident, other in ((a, b), (b, a)):
                    lits = _str_literals(other)
                    if _is_identity(ident) and lits:
                        yield n.lineno, lits, "이름 비교"
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            f, args = n.func, n.args
            if f.attr in IDENTITY_STR_METHODS and _is_identity(f.value):
                lits = [s for a in args for s in _str_literals(a)]
                if lits:
                    yield n.lineno, lits, "이름 문자열 검사 .%s" % f.attr
            elif f.attr in REGEX_FUNCS and len(args) >= 2 and _is_identity(args[1]) and _str_const(args[0]):
                yield n.lineno, [args[0].value], "이름 정규식 %s" % f.attr
            elif f.attr == "get" and isinstance(f.value, ast.Dict) and args and _is_identity(args[0]):
                lits = [k.value for k in f.value.keys if _str_const(k)]
                if lits:
                    yield n.lineno, lits, "이름 키 표 {...}.get"
        elif isinstance(n, ast.Subscript) and isinstance(n.value, ast.Dict) and _is_identity(n.slice):
            lits = [k.value for k in n.value.keys if _str_const(k)]
            if lits:
                yield n.lineno, lits, "이름 키 표 {...}[...]"
        elif isinstance(n, ast.Match) and _is_identity(n.subject):
            lits = [s for c in n.cases for s in _pattern_literals(c.pattern)]
            if lits:
                yield n.lineno, lits, "이름 match"


def check_i(root: Path, names=()) -> tuple[int, list[Violation]]:
    """규칙 I. names = 규칙 E 이름 집합(library_names 의 둘째 값) -- (b)에서 그 원소인 리터럴은 E 몫이라 뺀다."""
    root = Path(root)
    targets = engine_files(root)
    known = set(names)
    out = []
    for p in targets:
        r = rel(root, p)
        tree = parse(p)
        for line, key, form in _tag_lookups(tree):
            if not _tag_exempt(r, key):
                out.append(Violation("tag_key_lookup", r, line, "회로 식별·태그 키 조회 %s" % form))
        for line, lits, form in _name_branches(tree):
            rest = sorted(set(lits) - known)
            if rest:
                out.append(Violation("name_branch", r, line, "%s: %s" % (form, rest)))
    return len(targets), out


# ---------------------------------------------------------------- (K)

def _front_query_refs(root: Path, p: Path, tree: ast.Module):
    """(종류, 행, 설명) -- 규칙 K 의 세 형식. 같은 노드가 두 형식에 걸리면 둘 다 낸다(check_k 가 (종류, 경로, 행, 설명) 중복을 하나로)."""
    names, modules = set(FRONT_QUERY_NAMES), set(FRONT_QUERY_MODULES)
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if modules & set(a.name.split(".")):
                    yield "front_query_module", n.lineno, "import %s" % a.name
                if a.asname in names:
                    yield "front_query_name", n.lineno, "import 별칭 %s" % a.asname
                if a.asname in SNAPSHOT_READ_NAMES:
                    yield "snapshot_read", n.lineno, "import 별칭 %s" % a.asname
        elif isinstance(n, ast.ImportFrom):
            mod = resolve_from(root, p, n)
            if modules & set(mod.split(".")):
                yield "front_query_module", n.lineno, "from %s import ..." % mod
            for a in n.names:
                if a.name in modules:
                    yield "front_query_module", n.lineno, "from %s import %s(모듈)" % (mod, a.name)
                for x in (a.name, a.asname):
                    if x in names:
                        yield "front_query_name", n.lineno, "import 이름 %s" % x
                    if x in SNAPSHOT_READ_NAMES:
                        yield "snapshot_read", n.lineno, "import 이름 %s" % x
        elif isinstance(n, ast.Name):
            if n.id in names:
                yield "front_query_name", n.lineno, "이름 %s" % n.id
            if n.id in SNAPSHOT_READ_NAMES:
                yield "snapshot_read", n.lineno, "이름 %s" % n.id
        elif isinstance(n, ast.Attribute):
            if n.attr in names:
                yield "front_query_name", n.lineno, "속성 .%s" % n.attr
            if n.attr in SNAPSHOT_READ_ATTRS:
                yield "snapshot_read", n.lineno, "속성 .%s" % n.attr


def check_k(root: Path) -> tuple[int, list[Violation]]:
    """규칙 K. 대상 = 엔진 소스(tests/ 제외) 중 허용 파일(FRONT_QUERY_ALLOWED_FILES) 밖 전부. 거부: (K-a) front 조회 공개 이름
    참조(import 이름·별칭, 이름, 속성), (K-b) front 조회 모듈 import(상대·절대), (K-c) 스냅샷 파일 읽기 속성 참조(호출 아닌 참조 포함)와
    이름 `_read_snapshot_file`."""
    root = Path(root)
    targets = [p for p in engine_files(root) if rel(root, p) not in FRONT_QUERY_ALLOWED_FILES]
    out = set()
    for p in targets:
        r = rel(root, p)
        for kind, line, detail in _front_query_refs(root, p, parse(p)):
            out.add(Violation(kind, r, line, detail))
    return len(targets), sorted(out)


# ---------------------------------------------------------------- (M)
# 판정 종류(README M 행):
#   open_run_ref       (M-a) 허용 파일 밖 엔진 소스의 open_run 참조(import 이름·별칭·모듈, 이름, 속성)
#   direct_construct   (M-b) 정의 모듈·open_run.py 밖의 S3Index(...)·RunCounters(...) 호출(import 별칭 포함, test 포함)
#   run_pair_source    (M-c) run_stage_a 의 donors·counters 인자가 같은 함수 본문 `a, b = open_run()` 의 (첫째, 둘째) 이름이 아니다
#                            (매개변수·속성·결과 칸·첨자·다른 호출 반환·자유 변수·두 번 묶인 이름·순서 바뀜·함수 밖 호출)
#   run_pair_reused    (M-c) 같은 이름이 그 함수 안 run_stage_a 호출 둘 이상에 쓰인다
#   run_pair_loop      (M-c) run_stage_a 가 반복문 본문(내포식·generator 식 포함) 안인데 그 open_run() 이 같은 반복문 본문에 없다
#   run_pair_packed    (M-c) run_stage_a(*args)·run_stage_a(**kw)
#   run_pair_stored    (M-d) 두 객체(또는 그것을 쥔 값)를 수명이 test 하나보다 긴 곳에 둔다
#   run_pair_persisted (M-f) 두 객체·내부 칸을 pickle·json·shelve·marshal 쓰기에 넘긴다
# '쥔 값'(holder) = open_run() 결과와 그 이름, 두 객체를 결과 칸으로 쥐는 진입(PAIR_HOLDER_PRODUCERS)의 결과, 속성 donors·counters와
#   컨텍스트 칸 속성(CONTEXT_ATTRS), 쥔 값의 첨자, 그 값을 담은 tuple·list·dict·set·생성 호출(CONTAINER_BUILDERS), 그 이름을 닫아 쥔 lambda.
#   그 밖 함수 호출의 결과와 쥔 값의 그 밖 속성(res.s1·res.spec 같은 스냅샷·선언 칸)은 쥔 값이 아니다(두 객체를 담지 않는다).
# 한계(정적 검사): getattr·exec 같은 동적 호출, 다른 파일 helper 를 거친 보관은 보지 못한다 -- 리뷰 항목(spec card 1.7.1).

_SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
_FUNC_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
_LOOP_NODES = (ast.For, ast.AsyncFor, ast.While, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def m_files(root: Path) -> list[Path]:
    """규칙 M 대상: 엔진 트리의 *.py 전부(tests/ 포함), 숨김·__pycache__·이 폴더의 위반 픽스처 제외, 정렬."""
    root = Path(root)
    if not root.is_dir():
        return []
    out = []
    for p in sorted(root.rglob("*.py")):
        parts = p.relative_to(root).parts
        if any(x == "__pycache__" or x.startswith(".") for x in parts):
            continue
        if parts[:len(M_EXCLUDED_PREFIX)] == M_EXCLUDED_PREFIX:
            continue
        out.append(p)
    return out


def _callee(n: ast.Call) -> str | None:
    f = n.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def _body_nodes(scope) -> list:
    if isinstance(scope, ast.Lambda):
        return [scope.body]
    return list(scope.body)


def _own_nodes(scope):
    """scope 자신의 노드(중첩 def·lambda·class 의 본문 제외 -- 그 노드 자신과, 바깥에서 평가되는 데코레이터·기본값·기반 클래스는 포함)."""
    stack = list(reversed(_body_nodes(scope)))
    while stack:
        n = stack.pop()
        yield n
        if isinstance(n, _SCOPE_NODES):
            extra = list(getattr(n, "decorator_list", []))
            if isinstance(n, ast.ClassDef):
                extra += list(n.bases) + [k.value for k in n.keywords]
            else:
                extra += [d for d in list(n.args.defaults) + list(n.args.kw_defaults) if d is not None]
            stack.extend(reversed(extra))
            continue
        stack.extend(reversed(list(ast.iter_child_nodes(n))))


def _target_names(t) -> list[str]:
    if isinstance(t, ast.Name):
        return [t.id]
    if isinstance(t, (ast.Tuple, ast.List)):
        return [x for e in t.elts for x in _target_names(e)]
    if isinstance(t, ast.Starred):
        return _target_names(t.value)
    return []


def _bindings(scope) -> Counter:
    """scope 안에서 이름이 묶이는 횟수(대입·for·with·walrus·내포식·import·except·중첩 def/class 이름·매개변수)."""
    c = Counter()
    if isinstance(scope, _FUNC_NODES):
        a = scope.args
        for x in list(a.posonlyargs) + list(a.args) + list(a.kwonlyargs) + [a.vararg, a.kwarg]:
            if x is not None:
                c[x.arg] += 1
    for n in _own_nodes(scope):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                c.update(_target_names(t))
        elif isinstance(n, (ast.AnnAssign, ast.AugAssign)):
            c.update(_target_names(n.target))
        elif isinstance(n, (ast.For, ast.AsyncFor, ast.comprehension)):
            c.update(_target_names(n.target))
        elif isinstance(n, ast.withitem) and n.optional_vars is not None:
            c.update(_target_names(n.optional_vars))
        elif isinstance(n, ast.NamedExpr):
            c.update(_target_names(n.target))
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            c.update((a.asname or a.name).split(".")[0] for a in n.names)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            c[n.name] += 1
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            c[n.name] += 1
    return c


def _params(scope) -> set[str]:
    if not isinstance(scope, _FUNC_NODES):
        return set()
    a = scope.args
    return {x.arg for x in list(a.posonlyargs) + list(a.args) + list(a.kwonlyargs) + [a.vararg, a.kwarg] if x is not None}


def _is_open_run_call(n) -> bool:
    return isinstance(n, ast.Call) and _callee(n) == OPEN_RUN_NAME


def _holder(e, tainted, producers=PAIR_HOLDER_PRODUCERS) -> bool:
    """e 가 두 객체(또는 그것을 쥔 값)인가 -- 모듈 머리 설명 '쥔 값'. producers = 결과가 쥔 값인 호출 이름(같은 파일에서 쥔 값을
    돌려주는 함수 포함 -- helper 를 한 겹 거친 보관도 잡는다)."""
    if e is None:
        return False
    if isinstance(e, ast.Name):
        return e.id in tainted
    if isinstance(e, ast.Attribute):
        return e.attr in PAIR_ATTRS or e.attr in CONTEXT_ATTRS
    if isinstance(e, ast.Subscript):
        return _holder(e.value, tainted, producers)
    if isinstance(e, ast.Call):
        name = _callee(e)
        if name == OPEN_RUN_NAME or name in producers:
            return True
        if name in CONTAINER_BUILDERS:
            return any(_holder(a, tainted, producers) for a in list(e.args) + [k.value for k in e.keywords])
        return False
    if isinstance(e, (ast.Tuple, ast.List, ast.Set)):
        return any(_holder(x, tainted, producers) for x in e.elts)
    if isinstance(e, ast.Dict):
        return any(_holder(x, tainted, producers) for x in list(e.keys) + list(e.values))
    if isinstance(e, (ast.Starred, ast.NamedExpr, ast.Await)):
        return _holder(e.value, tainted, producers)
    if isinstance(e, ast.IfExp):
        return _holder(e.body, tainted, producers) or _holder(e.orelse, tainted, producers)
    if isinstance(e, ast.BoolOp):
        return any(_holder(x, tainted, producers) for x in e.values)
    if isinstance(e, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
        return _holder(e.elt, tainted, producers)
    if isinstance(e, ast.DictComp):
        return _holder(e.key, tainted, producers) or _holder(e.value, tainted, producers)
    if isinstance(e, ast.Lambda):
        return any(isinstance(x, ast.Name) and x.id in tainted for x in ast.walk(e.body))
    return False


_holder_base = _holder


def _taint(scope, inherited: frozenset, producers=PAIR_HOLDER_PRODUCERS) -> frozenset:
    """scope 안 '쥔 값' 이름(고정점). 바깥 scope 의 쥔 이름은 이 scope 가 다시 묶지 않으면 물려받는다(자유 변수)."""
    local = _bindings(scope)
    tainted = set(x for x in inherited if x not in local)
    changed = True
    while changed:
        changed = False
        for n in _own_nodes(scope):
            pairs = []
            if isinstance(n, ast.Assign):
                pairs = [(t, n.value) for t in n.targets]
            elif isinstance(n, (ast.AnnAssign, ast.AugAssign)) and n.value is not None:
                pairs = [(n.target, n.value)]
            elif isinstance(n, ast.NamedExpr):
                pairs = [(n.target, n.value)]
            elif isinstance(n, (ast.For, ast.AsyncFor, ast.comprehension)):
                pairs = [(n.target, n.iter)]
            elif isinstance(n, ast.withitem) and n.optional_vars is not None:
                pairs = [(n.optional_vars, n.context_expr)]
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if any(isinstance(x, ast.Name) and x.id in tainted for b in n.body for x in ast.walk(b)):
                    if n.name not in tainted:
                        tainted.add(n.name)
                        changed = True
            for t, v in pairs:
                if _holder(v, tainted, producers):
                    for name in _target_names(t):
                        if name not in tainted:
                            tainted.add(name)
                            changed = True
    return frozenset(tainted)


def _pair_names(scope) -> frozenset:
    """'쌍 이름' P: open_run() 튜플 풀기·단일 대입으로 묶인 이름과, 속성 donors·counters 를 대입받은 이름(M-f 내부 칸 판정용)."""
    out = set()
    for n in _own_nodes(scope):
        if isinstance(n, ast.Assign) and (_is_open_run_call(n.value) or
                                          (isinstance(n.value, ast.Attribute) and n.value.attr in PAIR_ATTRS)):
            for t in n.targets:
                out.update(_target_names(t))
    return frozenset(out)


def _scopes(tree: ast.Module):
    """(scope, 바깥 scope) -- 모듈부터 깊이 우선. 각 scope 의 바깥 scope 를 함께 낸다."""
    stack = [(tree, None)]
    while stack:
        s, outer = stack.pop()
        yield s, outer
        for n in _own_nodes(s):
            if isinstance(n, _SCOPE_NODES):
                stack.append((n, s))


def _innermost_loop(node, scope, parent) -> int | None:
    """scope 안에서 node 를 감싸는 가장 안쪽 반복문(내포식·generator 식 포함) 노드 id, 없으면 None."""
    cur = parent.get(id(node))
    while cur is not None and cur is not scope:
        if isinstance(cur, _LOOP_NODES):
            return id(cur)
        cur = parent.get(id(cur))
    return None


def _enclosing_scope(node, parent):
    cur = parent.get(id(node))
    while cur is not None and not isinstance(cur, (ast.Module,) + _SCOPE_NODES):
        cur = parent.get(id(cur))
    return cur


def _decorator_parts(d) -> tuple[str, ast.Call | None]:
    """데코레이터 -> (마지막 이름, 호출이면 그 Call)."""
    call = d if isinstance(d, ast.Call) else None
    f = d.func if call is not None else d
    if isinstance(f, ast.Attribute):
        return f.attr, call
    if isinstance(f, ast.Name):
        return f.id, call
    return "", call


def _long_fixture(fn) -> bool:
    """(M-d) pytest fixture 이고 scope 가 test 하나보다 긴가(문자열 상수가 아니면 fail-closed 로 긴 범위)."""
    for d in fn.decorator_list:
        name, call = _decorator_parts(d)
        if name != "fixture" or call is None:
            continue
        for k in call.keywords:
            if k.arg == "scope":
                if isinstance(k.value, ast.Constant) and isinstance(k.value.value, str):
                    return k.value.value in LONG_FIXTURE_SCOPES
                return True
    return False


def _cache_decorated(fn) -> bool:
    return any(_decorator_parts(d)[0] in CACHE_DECORATORS for d in fn.decorator_list)


def _chain_root(e):
    while isinstance(e, (ast.Attribute, ast.Subscript)):
        e = e.value
    return e


def _chain_attrs(e) -> list[str]:
    out = []
    while isinstance(e, (ast.Attribute, ast.Subscript)):
        if isinstance(e, ast.Attribute):
            out.append(e.attr)
        e = e.value
    if isinstance(e, ast.Name):
        out.append(e.id)
    return out


def _config_chain(e) -> bool:
    return any(x in CONFIG_NAMES for x in _chain_attrs(e))


def _module_names(tree: ast.Module) -> set[str]:
    return set(_bindings(tree))


def _run_object(e, pair, tainted, top=True) -> bool:
    """(M-f) 인자 e 가 두 객체 자신·그것을 쥔 값·그 내부 칸을 담는가. 메서드 호출 결과(`counters.snapshot()`)는 객체가 아니다."""
    if isinstance(e, ast.Name):
        return e.id in (tainted if top else pair)
    if isinstance(e, ast.Attribute):
        return e.attr in PAIR_ATTRS or _run_object(e.value, pair, tainted, top=False)
    if isinstance(e, ast.Subscript):
        return _run_object(e.value, pair, tainted, top=False)
    if isinstance(e, ast.Call):
        return any(_run_object(a, pair, tainted) for a in list(e.args) + [k.value for k in e.keywords])
    if isinstance(e, (ast.Tuple, ast.List, ast.Set)):
        return any(_run_object(x, pair, tainted) for x in e.elts)
    if isinstance(e, ast.Dict):
        return any(_run_object(x, pair, tainted) for x in list(e.keys) + list(e.values) if x is not None)
    if isinstance(e, ast.Starred):
        return _run_object(e.value, pair, tainted)
    if isinstance(e, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
        parts = [e.key, e.value] if isinstance(e, ast.DictComp) else [e.elt]
        parts += [g.iter for g in e.generators]
        return any(_run_object(x, pair, tainted) for x in parts)
    return False


def _serializer_aliases(tree: ast.Module) -> tuple[dict[str, str], set[str]]:
    """(모듈 별칭 -> 직렬화 모듈 이름, 쓰기 함수로 import 된 이름)."""
    mods, funcs = {}, set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name in SERIALIZER_MODULES:
                    mods[a.asname or a.name] = a.name
        elif isinstance(n, ast.ImportFrom) and n.module in SERIALIZER_MODULES:
            for a in n.names:
                if a.name in SERIALIZER_WRITES:
                    funcs.add(a.asname or a.name)
    return mods, funcs


def _m_refs(r: str, tree: ast.Module):
    """(M-a) 엔진 소스의 open_run 참조."""
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if OPEN_RUN_NAME in a.name.split(".") or a.asname == OPEN_RUN_NAME:
                    yield "open_run_ref", n.lineno, "import %s" % a.name
        elif isinstance(n, ast.ImportFrom):
            if n.module and OPEN_RUN_NAME in n.module.split("."):
                yield "open_run_ref", n.lineno, "from %s import ..." % n.module
            for a in n.names:
                if OPEN_RUN_NAME in (a.name, a.asname):
                    yield "open_run_ref", n.lineno, "import 이름 %s" % a.name
        elif isinstance(n, ast.Name) and n.id == OPEN_RUN_NAME:
            yield "open_run_ref", n.lineno, "이름 open_run"
        elif isinstance(n, ast.Attribute) and n.attr == OPEN_RUN_NAME:
            yield "open_run_ref", n.lineno, "속성 .open_run"


def _m_construct(r: str, tree: ast.Module):
    """(M-b) 정의 모듈·open_run.py 밖 생성 호출(import 별칭 포함)."""
    alias = {k: k for k in RUN_OBJECT_HOMES}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            for a in n.names:
                if a.name in RUN_OBJECT_HOMES and a.asname:
                    alias[a.asname] = a.name
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            name = _callee(n)
            cls = alias.get(name) if isinstance(n.func, ast.Name) else (name if name in RUN_OBJECT_HOMES else None)
            if cls is not None and r not in RUN_OBJECT_HOMES[cls]:
                yield "direct_construct", n.lineno, "%s(...) 직접 생성" % cls


def _entry_aliases(tree: ast.Module) -> frozenset:
    """(M-c, fail-closed) 파일 안에서 run_stage_a 를 가리키는 이름: 본 이름, `from ... import run_stage_a as X` 의 X, 그리고 어느 scope 에서든
    `X = run_stage_a`·`X = <식>.run_stage_a`·`X = <별칭>`(고정점)으로 대입된 이름. 별칭 이름을 부르는 호출은 run_stage_a 호출로 본다
    (같은 이름이 다른 값도 받는 경우까지 호출로 보는 쪽 -- 과잉 판정은 위반으로 드러나 고치는 쪽이 안전하다)."""
    names = {RUN_ENTRY}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            for a in n.names:
                if a.name == RUN_ENTRY and a.asname:
                    names.add(a.asname)
    changed = True
    while changed:
        changed = False
        for n in ast.walk(tree):
            pairs = []
            if isinstance(n, ast.Assign):
                pairs = [(t, n.value) for t in n.targets]
            elif isinstance(n, (ast.AnnAssign, ast.NamedExpr)) and n.value is not None:
                pairs = [(n.target, n.value)]
            for t, v in pairs:
                ref = (isinstance(v, ast.Name) and v.id in names) or (isinstance(v, ast.Attribute) and v.attr == RUN_ENTRY)
                if ref and isinstance(t, ast.Name) and t.id not in names:
                    names.add(t.id)
                    changed = True
    return frozenset(names)


def _is_entry_call(n, aliases) -> bool:
    """(M-c) run_stage_a 호출인가: 이름(별칭 포함) 호출, `<식>.run_stage_a(...)`, `getattr(<식>, "run_stage_a")(...)`."""
    if not isinstance(n, ast.Call):
        return False
    f = n.func
    if isinstance(f, ast.Name):
        return f.id in aliases
    if isinstance(f, ast.Attribute):
        return f.attr == RUN_ENTRY
    if isinstance(f, ast.Call) and isinstance(f.func, ast.Name) and f.func.id == "getattr" and len(f.args) >= 2:
        a = f.args[1]
        return isinstance(a, ast.Constant) and a.value == RUN_ENTRY
    return False


def _stmt_slot(node, parent):
    """node 를 담은 문장 목록 (목록 객체, 그 안 위치) -- 문장이 아니면 None."""
    p = parent.get(id(node))
    if p is None:
        return None
    for field in ("body", "orelse", "finalbody", "handlers"):
        seq = getattr(p, field, None)
        if isinstance(seq, list):
            for i, x in enumerate(seq):
                if x is node:
                    return seq, i
    return None


def _dominates(assign, call, scope, parent) -> bool:
    """assign 문장이 call 보다 앞에 있고, call 을 감싸는 문장 사슬 중 하나와 같은 문장 목록에 있다(구조적 앞섬 -- if 가지 안 대입은 그 가지
    밖 호출을 앞서지 않는다)."""
    slot = _stmt_slot(assign, parent)
    if slot is None:
        return False
    seq, i = slot
    cur = call
    while cur is not None and cur is not scope:
        for j, x in enumerate(seq):
            if x is cur:
                return j > i
        cur = parent.get(id(cur))
    return False


def _m_calls(tree: ast.Module, parent):
    """(M-c) run_stage_a 호출마다 판정. 낸 값: (종류, 행, 설명).
    design 40 §2.4.5 (M-c): 인자 donors·counters = 같은 함수 본문 `open_run()` 튜플 풀기로 대입된 두 이름, 그 대입 하나는 run_stage_a 호출
    **하나**에만 쓰인다. 같은 이름을 새 `open_run()` 튜플 풀기로 다시 대입해 다음 호출에 쓰는 꼴은 대입마다 호출 하나라 허용이다(판정 단위 =
    대입 문장). 호출이 쓰는 대입 = 그 호출을 구조적으로 앞서는(_dominates) 같은 이름 대입 중 마지막 것. 그 이름의 다른 묶임(매개변수·for·
    다른 대입 등)이 있으면 출처를 정적으로 알 수 없어 위반(fail-closed)."""
    aliases = _entry_aliases(tree)
    uses = {}                    # 대입 문장 id -> [(호출 행, 이름)]
    found = []
    for call in ast.walk(tree):
        if not _is_entry_call(call, aliases):
            continue
        scope = _enclosing_scope(call, parent)
        if any(isinstance(a, ast.Starred) for a in call.args) or any(k.arg is None for k in call.keywords):
            found.append(("run_pair_packed", call.lineno, "묶음 인자 *args/**kw"))
        kws = {k.arg: k.value for k in call.keywords if k.arg in RUN_PAIR_KEYWORDS}
        if not kws:
            continue
        if not isinstance(scope, _FUNC_NODES):
            found.append(("run_pair_source", call.lineno, "함수 밖 run_stage_a"))
            continue
        bind = _bindings(scope)
        params = _params(scope)
        assigns = {}             # 이름 -> [(대입 문장, 위치)]
        for n in _own_nodes(scope):
            if (isinstance(n, ast.Assign) and _is_open_run_call(n.value) and len(n.targets) == 1
                    and isinstance(n.targets[0], ast.Tuple) and len(n.targets[0].elts) == len(RUN_PAIR_KEYWORDS)
                    and all(isinstance(e, ast.Name) for e in n.targets[0].elts)):
                for i, e in enumerate(n.targets[0].elts):
                    assigns.setdefault(e.id, []).append((n, i))
        bad, origin = [], set()
        for i, kw in enumerate(RUN_PAIR_KEYWORDS):
            if kw not in kws:
                continue
            v = kws[kw]
            if not isinstance(v, ast.Name):
                bad.append("%s=%s(이름 아님)" % (kw, type(v).__name__))
                continue
            cands = assigns.get(v.id, [])
            if (not cands or v.id in params or bind[v.id] != len(cands) or any(pos != i for _n, pos in cands)):
                bad.append("%s=%s(같은 함수 open_run() 튜플 풀기 %d번째 이름 아님)" % (kw, v.id, i + 1))
                continue
            before = [(n, pos) for n, pos in cands if _dominates(n, call, scope, parent)]
            if not before:
                bad.append("%s=%s(호출을 앞서는 open_run() 대입 없음)" % (kw, v.id))
                continue
            got = max(before, key=lambda x: (x[0].lineno, x[0].col_offset))
            origin.add(id(got[0]))
            uses.setdefault(id(got[0]), []).append((call.lineno, v.id))
            if _innermost_loop(call, scope, parent) != _innermost_loop(got[0], scope, parent):
                found.append(("run_pair_loop", call.lineno, "%s: open_run() 이 같은 반복문 본문에 없다" % kw))
        if len(origin) > 1:
            bad.append("donors·counters 가 서로 다른 open_run() 에서 왔다")
        if bad:
            found.append(("run_pair_source", call.lineno, "; ".join(bad)))
    for _aid, hits in uses.items():
        lines = sorted({line for line, _ in hits})
        if len(lines) > 1:
            names = sorted({name for _, name in hits})
            for line in lines:
                found.append(("run_pair_reused", line, "open_run() 대입 하나(이름 %s)가 run_stage_a %d곳에 쓰인다" % (", ".join(names), len(lines))))
    return found


def _m_storage(tree: ast.Module):
    """(M-d)·(M-f) 보관·직렬화."""
    found = []
    scopes = list(_scopes(tree))
    # 같은 파일에서 쥔 값을 돌려주는 함수도 producer 로 본다(고정점) -- helper 한 겹을 거친 보관.
    producers = set(PAIR_HOLDER_PRODUCERS)
    while True:
        taint, pairs = {}, {}
        for scope, outer in scopes:
            taint[id(scope)] = _taint(scope, taint.get(id(outer), frozenset()) if outer is not None else frozenset(),
                                      frozenset(producers))
            pairs[id(scope)] = _pair_names(scope) | (pairs.get(id(outer), frozenset()) if outer is not None else frozenset())
        returns_holder = set()
        for scope, _outer in scopes:
            if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
                t = taint[id(scope)]
                if any(isinstance(n, (ast.Return, ast.Yield)) and _holder_base(n.value, t, frozenset(producers))
                       for n in _own_nodes(scope)):
                    returns_holder.add(scope.name)
        if returns_holder <= producers:
            break
        producers |= returns_holder
    producers = frozenset(producers)

    def _holder(e, t, _p=producers):          # 이 함수 안에서는 늘 같은 producer 집합
        return _holder_base(e, t, _p)

    module_names = _module_names(tree)
    mods, funcs = _serializer_aliases(tree)
    long_classes = set()
    for n in _own_nodes(tree):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name):
            long_classes.add(n.value.func.id)

    def stored(line, why):
        found.append(("run_pair_stored", line, why))

    for scope, outer in _scopes(tree):
        t = taint[id(scope)]
        p = pairs[id(scope)]
        local = _bindings(scope)
        globals_here = {x for n in _own_nodes(scope) if isinstance(n, ast.Global) for x in n.names}
        is_module = isinstance(scope, ast.Module)
        is_class = isinstance(scope, ast.ClassDef)
        in_long_class_method = (isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)) and isinstance(outer, ast.ClassDef)
                                and outer.name in long_classes)
        shelves = set()
        for n in _own_nodes(scope):
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and _callee(n.value) == "open" and \
                    isinstance(n.value.func, ast.Attribute) and isinstance(n.value.func.value, ast.Name) and \
                    mods.get(n.value.func.value.id) == "shelve":
                for tt in n.targets:
                    shelves.update(_target_names(tt))
            if isinstance(n, ast.withitem) and isinstance(n.context_expr, ast.Call) and \
                    isinstance(n.context_expr.func, ast.Attribute) and isinstance(n.context_expr.func.value, ast.Name) and \
                    mods.get(n.context_expr.func.value.id) == "shelve" and n.optional_vars is not None:
                shelves.update(_target_names(n.optional_vars))

        def module_level(name):
            return name in module_names and (name not in local or name in globals_here)

        for n in _own_nodes(scope):
            # ---- 대입 sink
            targets, value = [], None
            if isinstance(n, ast.Assign):
                targets, value = n.targets, n.value
            elif isinstance(n, (ast.AnnAssign, ast.AugAssign)) and n.value is not None:
                targets, value = [n.target], n.value
            if targets and _holder(value, t):
                for tg in targets:
                    if is_module:
                        stored(n.lineno, "모듈 수준 이름")
                    elif is_class:
                        stored(n.lineno, "클래스 속성")
                    elif isinstance(tg, ast.Name) and tg.id in globals_here:
                        stored(n.lineno, "global 이름")
                    elif isinstance(tg, (ast.Attribute, ast.Subscript)):
                        root = _chain_root(tg)
                        if _config_chain(tg):
                            stored(n.lineno, "pytest config")
                        elif isinstance(root, ast.Name) and module_level(root.id):
                            stored(n.lineno, "모듈 수준 객체·컨테이너")
                        elif isinstance(root, ast.Name) and root.id == "self" and in_long_class_method:
                            stored(n.lineno, "모듈 수준 객체의 인스턴스 속성")
            if targets and value is not None:
                for tg in targets:
                    if isinstance(tg, ast.Subscript) and isinstance(_chain_root(tg), ast.Name) and \
                            _chain_root(tg).id in shelves and _run_object(value, p, t):
                        found.append(("run_pair_persisted", n.lineno, "shelve 항목 대입"))
            # ---- 호출 sink
            if isinstance(n, ast.Call):
                args = list(n.args) + [k.value for k in n.keywords]
                f = n.func
                if isinstance(f, ast.Attribute) and f.attr in CONTAINER_MUTATORS and any(_holder(a, t) for a in args):
                    root = _chain_root(f.value)
                    if _config_chain(f.value):
                        stored(n.lineno, "pytest config")
                    elif isinstance(root, ast.Name) and module_level(root.id):
                        stored(n.lineno, "모듈 수준 컨테이너 변경")
                elif isinstance(f, ast.Attribute) and _config_chain(f.value) and any(_holder(a, t) for a in args):
                    stored(n.lineno, "pytest config")
                name = _callee(n)
                if name in CACHE_DECORATORS and n.args and isinstance(n.args[0], ast.Name) and n.args[0].id in returns_holder:
                    stored(n.lineno, "cache 감싼 함수의 반환")
                if isinstance(f, ast.Call) and _callee(f) in CACHE_DECORATORS and n.args and \
                        isinstance(n.args[0], ast.Name) and n.args[0].id in returns_holder:
                    stored(n.lineno, "lru_cache 감싼 함수의 반환")
                serial = (isinstance(f, ast.Name) and f.id in funcs) or (
                    isinstance(f, ast.Attribute) and f.attr in SERIALIZER_WRITES and (
                        (isinstance(f.value, ast.Name) and f.value.id in mods) or
                        (isinstance(f.value, ast.Call) and isinstance(f.value.func, ast.Attribute) and
                         isinstance(f.value.func.value, ast.Name) and f.value.func.value.id in mods)))
                if serial and any(_run_object(a, p, t) for a in args):
                    found.append(("run_pair_persisted", n.lineno, "직렬화 쓰기 인자"))
            # ---- 기본 인자값
            if isinstance(n, _FUNC_NODES):
                for d in list(n.args.defaults) + [x for x in n.args.kw_defaults if x is not None]:
                    if _holder(d, t):
                        stored(d.lineno, "함수 기본 인자값")
        # ---- 함수 단위 sink
        if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
            rets = [n for n in _own_nodes(scope) if isinstance(n, (ast.Return, ast.Yield, ast.YieldFrom)) and _holder(n.value, t)]
            if _long_fixture(scope):
                for n in rets:
                    stored(n.lineno, "test 하나보다 긴 범위 fixture")
            if _cache_decorated(scope):
                for n in rets:
                    if isinstance(n, ast.Return):
                        stored(n.lineno, "lru_cache·cache 함수의 반환")
            if scope.name in CONFIG_HOOKS:
                for n in _own_nodes(scope):
                    if isinstance(n, ast.Call) and _holder(n, frozenset()):
                        stored(n.lineno, "conftest %s" % scope.name)
    return found


def m_run_stage_a_calls(root: Path) -> int:
    """대상 트리의 run_stage_a 호출 수(규칙 M M-c 가 실제로 본 호출 수 -- 공허 통과 방지)."""
    total = 0
    for p in m_files(root):
        tree = parse(p)
        aliases = _entry_aliases(tree)
        total += sum(1 for n in ast.walk(tree) if _is_entry_call(n, aliases))
    return total


def check_m(root: Path) -> tuple[int, list[Violation]]:
    """규칙 M(실행 비공유). 대상 = m_files(엔진 트리 전체, tests/ 포함, 위반 픽스처 제외). (M-a) 은 tests/ 밖 엔진 소스만,
    (M-b)~(M-f) 은 전부. 판정 종류는 위 머리 설명."""
    root = Path(root)
    targets = m_files(root)
    out = set()
    for p in targets:
        r = rel(root, p)
        tree = parse(p)
        parent = _parents(tree)
        found = []
        if p.relative_to(root).parts[0] != "tests" and r not in OPEN_RUN_ALLOWED_FILES:
            found.extend(_m_refs(r, tree))
        found.extend(_m_construct(r, tree))
        found.extend(_m_calls(tree, parent))
        found.extend(_m_storage(tree))
        merged = {}
        for kind, line, detail in found:                 # 같은 (종류, 행)은 하나로(설명은 합친다)
            merged.setdefault((kind, line), [])
            if detail not in merged[(kind, line)]:
                merged[(kind, line)].append(detail)
        for (kind, line), details in merged.items():
            out.add(Violation(kind, r, line, "; ".join(details)))
    return len(targets), sorted(out)
