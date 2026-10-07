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
