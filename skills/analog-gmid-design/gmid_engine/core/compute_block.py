"""계산 블록 데코레이터 -- 선언한 입력만 투영해 넘기고, 입력 버전이 같으면 graph 의 기존 값을 재사용한다
(사용자 대원칙 2026-10-07 '같은 값을 반복 계산하는 loop 금지', 확정 사항 1·5, 계획 NFR-2·SC-a·SC-b·SC-d·SC-e).

진입점: `compute_block(name, reads=..., writes=...)`.

    @compute_block("blk", reads=(("device", "L"),), writes=(("device", "W"),))
    def blk(projection):
        return {("device", "W"): {key: ... for key, value in projection.column("device", "L")}}

    donors, counters = open_run()        # search.open_run -- 실행 하나의 색인·계수 (생성은 그 함수뿐)
    snapshot2 = blk(snapshot1, *extras, donors=donors, counters=counters)

* 블록 함수는 `Projection` 하나만 받는다(선언 밖 열은 읽을 수 없다). 추가 인자(`extras`)는 불변 값만 받고
  (`TypeError` -- dict·list·ndarray 는 거부) 투영에 함께 들어간다.
* 입력 버전 = fp_of((name, 블록 코드 해시, 투영 지문)) -- 정본은 `ComputeBlock.input_version(snapshot, *extras)` 하나(봉인 4 도 이것을 부른다).
* `donors`·`counters` 는 필수 키워드다(빠지면 `TypeError`, `donors` 가 `Donors` 하위가 아니어도 `TypeError`). 판정 순서(설계 40 §2.4.4):
  1 같은 lineage 재사용(`snapshot.block_version(name)` 이 같으면 `snapshot` 그대로, 계수 reuse) -> 2 이식(`donors.find` 가 스냅샷을 주면
  `graft`, 계수 graft) -> 실패 재연(`donors.find_failure` 가 기록을 주면 블록 함수 없이 그 분류 예외를 `from_record` 로 다시 던진다, 계수 replay)
  -> 3 계산(계수 compute 는 함수 호출 전에. 성공이면 `register`, N3.14 분류 예외면 `register_failure` 후 다시 던진다. 그 밖 예외는
  등록·알림 없이 그대로).
* 블록 객체는 상태가 없다(계수·색인은 호출자가 넘기는 `RunCounters`·`Donors` 에 산다).
* writer 이름 = 블록 이름. 권한표가 그 열을 이 블록에 배정하지 않았으면 `WriterPermissionError`.
* 코드 해시(설계 40 v1.9.3 결정 10) = 블록 함수 code 객체(중첩 code 재귀, `__wrapped__` 사슬 포함)의 **코드 내용만**의 지문.
  marshal 을 쓰지 않고(참조 수에 따라 바이트가 달라진다) 정규화 결과를 core `fp_of` 로 지문화한다. 파일 경로·줄 정보는 넣지 않아
  checkout 경로와 무관하다. 데코레이트 시점에 1회 계산해 속성으로 보관한다.
"""
from collections.abc import Mapping

from .donors import Donors
from .failure_classes import FAILURE_CLASSES
from .failure_errors import InfeasibleSizingError, SchemaRejectedError
from .fingerprint import fp_of
from .graft import graft
from .projection import Projection
from .writer_table import ENTITY_KINDS


# 코드 해시에 넣는 co_* 칸 13개 / 넣지 않는 칸 9개. 두 목록은 code 타입의 co_* 이름 전체(3.14 기준 22개)를 빠짐없이 나눈다.
_CODE_FIELDS_IN = (
    "co_code", "co_consts", "co_names", "co_varnames", "co_freevars", "co_cellvars",
    "co_argcount", "co_posonlyargcount", "co_kwonlyargcount", "co_flags", "co_exceptiontable",
    "co_name", "co_qualname",
)
_CODE_FIELDS_OUT = (
    "co_filename", "co_firstlineno", "co_linetable", "co_lnotab", "co_lines", "co_positions", "co_branches",
    "co_nlocals", "co_stacksize",
)
_unknown_code_fields = {n for n in dir(type(compile("0", "<fp>", "eval"))) if n.startswith("co_")}     | {n for n in dir(compile("0", "<fp>", "eval")) if n.startswith("co_")}
_unknown_code_fields -= set(_CODE_FIELDS_IN) | set(_CODE_FIELDS_OUT)
if _unknown_code_fields:   # 실행 Python 판에 새 co_* 칸이 생겼다 -- 넣을지 뺄지 사람이 정할 때까지 fail-closed
    raise RuntimeError("compute_block: code 객체의 모르는 co_* 칸 " + repr(sorted(_unknown_code_fields)) + " -- _CODE_FIELDS_IN/_OUT 에 분류할 것")

_PLAIN_CONST_TYPES = (type(None), bool, int, float, str, bytes)


def _norm_const(value):
    """code 상수 하나를 `(타입 이름, 정규화 값)` 으로 -- 타입마다 이름을 감싸 다른 타입의 같은 모양과 구분한다. 모르는 타입은 TypeError."""
    kind = type(value)
    if kind in _PLAIN_CONST_TYPES:
        return (kind.__name__, value)
    if kind is tuple:
        return ("tuple", tuple(_norm_const(item) for item in value))
    if kind is frozenset:
        return ("frozenset", frozenset(_norm_const(item) for item in value))   # fp_of 가 원소 정준 바이트로 정렬한다
    if kind is complex:
        return ("complex", (value.real, value.imag))                            # float 규칙(float.hex)
    if kind is slice:
        return ("slice", (_norm_const(value.start), _norm_const(value.stop), _norm_const(value.step)))
    if value is Ellipsis:
        return ("ellipsis", None)
    if kind is type(_norm_const.__code__):
        return ("code", _norm_code(value))
    raise TypeError("compute_block: code 상수의 지원하지 않는 타입 " + kind.__qualname__ + " -- 코드 해시를 만들 수 없다")


def _norm_code(code):
    """code 객체 하나의 정규화(넣는 칸 13개만, 중첩 code 는 상수 정규화에서 재귀)."""
    return tuple((name, _norm_const(getattr(code, name)) if name == "co_consts" else getattr(code, name)) for name in _CODE_FIELDS_IN)


def _code_hash(fn):
    """블록 함수부터 `__wrapped__` 사슬 끝까지(순서대로)의 code 내용 지문. 순환 ValueError, `__code__` 없음 TypeError."""
    chain = []
    seen = set()
    link = fn
    while True:
        if id(link) in seen:
            raise ValueError("compute_block: __wrapped__ 사슬이 순환한다")
        seen.add(id(link))
        code = getattr(link, "__code__", None)
        if code is None:
            raise TypeError("compute_block: 블록 함수 사슬의 원소 " + repr(link) + " 에 __code__ 가 없다")
        chain.append(_norm_code(code))
        link = getattr(link, "__wrapped__", None)
        if link is None:
            return fp_of(tuple(chain))


_PART = "*"   # 분할 도입(U17 ②) 전에는 분할 key 가 "*" 하나


def _kind_fields(what, pairs):
    result = []
    for pair in pairs:
        if isinstance(pair, str):
            raise ValueError("compute_block: " + what + " 항목은 (kind, field) 쌍이어야 한다")
        kind, field = tuple(pair)  # 개수가 다르면 언패킹 ValueError
        if kind not in ENTITY_KINDS:
            raise ValueError("compute_block: " + what + " 의 모르는 kind " + repr(kind))
        if not isinstance(field, str) or not field:
            raise ValueError("compute_block: " + what + " 의 field 는 비어 있지 않은 문자열이어야 한다")
        result.append((kind, field))
    if len(set(result)) != len(result):
        raise ValueError("compute_block: " + what + " 에 같은 (kind, field) 중복")
    return tuple(result)


class ComputeBlock:
    """`compute_block` 이 만드는 호출 가능 객체. 직접 만들지 않는다."""

    def __init__(self, fn, name, reads, writes, keywords=()):
        self.fn = fn
        self.name = name
        self.reads = reads
        self.writes = writes
        self.keywords = keywords
        self.code_hash = _code_hash(fn)
        self.__doc__ = fn.__doc__

    def split(self, extras):
        """전체 추가 인자 tuple -> (위치 인자, {필수 키워드 이름: 값}). 필수 키워드 값은 전체 extras 의 맨 뒤에 `keywords` 순서로 들어 있다(투영·입력 버전은 이 전체 extras 를 본다)."""
        cut = len(extras) - len(self.keywords)
        return tuple(extras[:cut]), dict(zip(self.keywords, extras[cut:]))

    def _prepare(self, snapshot, extras):
        """(투영, 입력 버전) -- 한 번만 만든다. extras 불변 검사(`TypeError`)는 이 투영에서 한 번."""
        projection = Projection.from_snapshot(snapshot, self.reads, extras)
        return projection, fp_of((self.name, self.code_hash, projection.fp))

    def input_version(self, snapshot, *extras):
        """입력 버전 정본 -- 블록 호출과 봉인 4 가 같은 식을 쓴다. `extras` 는 필수 키워드 값을 맨 뒤에 포함한 전체 추가 인자다."""
        return self._prepare(snapshot, extras)[1]

    def __call__(self, snapshot, *extras, donors, counters, **named):
        if not isinstance(donors, Donors):
            raise TypeError("compute_block " + repr(self.name) + ": donors 는 Donors 하위여야 한다: " + type(donors).__qualname__)
        if set(named) != set(self.keywords):      # 필수 키워드(기본값 없음): 빠지거나 모르는 키워드가 있으면 TypeError
            raise TypeError("compute_block " + repr(self.name) + ": 필수 키워드 인자 " + repr(self.keywords) + " 와 다른 키워드 " + repr(tuple(sorted(named))))
        extras += tuple(named[k] for k in self.keywords)
        projection, version = self._prepare(snapshot, extras)
        name = self.name
        if snapshot.block_version(name) == version:
            counters.record(name, _PART, "reuse", version)
            return snapshot
        donor = donors.find(name, _PART, version)
        if donor is not None:
            counters.record(name, _PART, "graft", version)
            return graft(snapshot, self, _PART, donor, version)
        failure = donors.find_failure(name, _PART, version)
        if failure is not None:
            counters.record(name, _PART, "replay", version)
            entry = FAILURE_CLASSES.get(failure.failure_class)
            if entry is None or entry.exc is None:
                raise ValueError("compute_block " + repr(name) + ": 재연할 수 없는 실패 기록 분류 " + repr(failure.failure_class) + " (색인 손상)")
            raise entry.exc.from_record(failure)
        counters.record(name, _PART, "compute", version)
        try:
            result = self.fn(projection)
        except (InfeasibleSizingError, SchemaRejectedError) as failed:    # 결정적 도메인 실패: 같은 입력이면 늘 같다
            donors.register_failure(name, _PART, version, failed.record)
            counters.result(name, _PART, version, False)
            raise
        if not isinstance(result, Mapping) or set(result) != set(self.writes):
            raise ValueError(
                "compute_block " + repr(name) + ": 결과 키는 선언한 writes " + repr(self.writes)
                + " 와 정확히 같아야 한다"
            )
        written = snapshot.write(name, version, result)
        donors.register(name, _PART, version, written)
        counters.result(name, _PART, version, True)
        return written


def compute_block(name, reads=(), writes=(), keywords=()):
    """계산 블록 데코레이터. `name`: 비어 있지 않은 문자열(= writer 이름). `reads`·`writes`: (kind, field) 쌍들.

    `writes` 는 비어 있으면 안 된다. 선언 형식 위반은 데코레이트할 때 `ValueError`.
    `keywords`: 기본값 없는 필수 키워드 추가 인자 이름들(호출 `block(snapshot, *extras, 이름=값, donors=, counters=)`, 빠지면 `TypeError`).
    값은 위치 extras 뒤에 붙어 투영·입력 버전에 든다.
    """
    if not isinstance(name, str) or not name:
        raise ValueError("compute_block: name 은 비어 있지 않은 문자열이어야 한다")
    read_pairs = _kind_fields("reads", reads)
    write_pairs = _kind_fields("writes", writes)
    if not write_pairs:
        raise ValueError("compute_block: writes 가 비어 있다 -- 결과를 graph 에 쓰지 않는 블록은 계산 블록이 아니다")

    def decorate(fn):
        return ComputeBlock(fn, name, read_pairs, write_pairs, tuple(keywords))

    return decorate
