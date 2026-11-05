"""LUT 조회 memo -- graph 밖에 남는 유일한 memo (확정 사항 4, 설계 MOD1 2.6·2.9).

진입점: `LutMemo`.

* 영역 4개(`REGIONS`): point(OpPoint·gmb·용량·[r6] VDsat·[r7] 잡음 계수·mismatch 감도·소자 σ), curve(Curve·gm/ID 축 곡선 표),
  root(VGS 근·역산), derived(tol_V 표·곡선 보고·[r6] VDsat 허용오차 표·중점 검증·[r7] 잡음 면·잡음/mismatch 허용오차 표).
  영역마다 `core.BoundedLRU` 하나를 이 객체가 소유한다(모듈 수준 캐시 없음).
* 키 = (LutSet 지문, 함수 이름) + 호출부가 넘긴 값(kind, w_key, 축 float 그대로 -- 반올림 없음). 객체·`id()` 키는
  `TypeError`(BoundedLRU 의 불변 검사).
* 상한: point·curve·root 는 한 평가 sweep 고유 키 상계 `B = (n_theta + 1) * U_eval`. 생성자 memo 는 부르는 쪽이 계산해 넘기고(처음부터 `"fixed"`),
  `LutMemo.counting` memo 는 **계수 상태**로 시작해 값을 상한 없이 모으다가 실행의 첫 커널 평가(`open_count` ~ `fix_bound`)에서 조회한 서로 다른 키 수
  U_eval 로 상한을 고정한다(설계 40 §2.4.6 '첫 평가 버림 제거'; 상태 `bound_state` = counting -> window_open -> fixed 한 방향).
  derived 상한 = 슬라이스 수 * 파생 표 종류 수(`DERIVED_TABLES`) -- 퇴출이 없도록 개수 그대로(계수 대상 아님).
* [2026-10-08] 비싼 파생 표는 `lookup_persistent` 로 디스크 캐시(`TableCache`, CONTRACT 2.1)를 거친다. memo(메모리)는 그대로다.
"""
from collections import OrderedDict

from gmid_engine.core import BoundedLRU, LruStats, canonical_key

from .table_cache import TableCache

REGIONS = ("curve", "derived", "point", "root")
DERIVED_TABLES = ("curve_report", "edge_costs", "midpoint_l_bin_checks", "noise_planes", "tol_mismatch_table", "tol_noise_table",
                  "tol_v_table", "tol_vdsat_table", "vds_floor")      # edge_costs·vds_floor: lut.derived_fns(슬라이스당 하나, 설계 40 §2.4.6 v1.9.1 D10; vds_floor = card HC-S)
SWEEP_REGIONS = ("curve", "point", "root")


class _Unmemoized:
    """상한 0 영역(`fix_bound` 에서 첫 커널 평가가 한 번도 안 쓴 영역): 저장 없이 매번 계산한다. 같은 키를 다시 부르면 다시 계산(CONTRACT 2.2).
    계수 상태 동안의 hits·misses 를 이어받는다."""

    def __init__(self, hits=0, misses=0):
        self._hits = hits
        self._misses = misses

    def lookup(self, key, compute):
        self._misses += 1
        return compute()

    def stats(self):
        return LruStats(0, 0, self._hits, self._misses, 0, 0)


class _Counted:
    """고정된 영역: 상한 LRU 하나 + 계수 상태 동안의 hits·misses(옮기기는 계수를 바꾸지 않으므로 합쳐서 낸다)."""

    def __init__(self, lru, hits, misses):
        self._lru = lru
        self._hits = hits
        self._misses = misses

    def lookup(self, key, compute):
        return self._lru.lookup(key, compute)

    def stats(self):
        s = self._lru.stats()
        return LruStats(s.capacity, s.size, s.hits + self._hits, s.misses + self._misses, s.evictions, s.recomputes_after_eviction)


class _Counting:
    """계수 상태 영역: 상한 없이 값을 모은다(같은 키는 한 번만 계산, 마지막 접근 순서 = `BoundedLRU` 와 같은 최근성 규칙). 창(`open`) 안에서 조회한
    서로 다른 키(`canonical_key` 동치)를 센다. 창 안에서 `compute()` 가 예외로 끝난 조회는 세지 않는다(`misses` 에는 센다)."""

    def __init__(self):
        self._entries = OrderedDict()       # canonical_key -> (원 key, 값) -- 고정 때 원 key 를 `BoundedLRU.adopt` 에 넘긴다
        self._seen = None
        self._hits = 0
        self._misses = 0

    def lookup(self, key, compute):
        memo_key = canonical_key(key)
        if memo_key in self._entries:
            self._hits += 1
            self._entries.move_to_end(memo_key)
            value = self._entries[memo_key][1]
        else:
            self._misses += 1
            value = compute()
            self._entries[memo_key] = (key, value)
        if self._seen is not None:
            self._seen.add(memo_key)
        return value

    def open(self):
        self._seen = set()

    def fixed(self, n_theta):
        """상한 (n_θ + 1)·U 로 고정한 영역(U = 창 안 서로 다른 키 수; 0 이면 `_Unmemoized`). 오래된 것부터 옮긴다."""
        unique = len(self._seen)
        if unique == 0:
            return _Unmemoized(self._hits, self._misses)
        lru = BoundedLRU((n_theta + 1) * unique)
        for orig_key, value in self._entries.values():
            lru.adopt(orig_key, value)
        return _Counted(lru, self._hits, self._misses)

    def stats(self):
        return LruStats(None, len(self._entries), self._hits, self._misses, 0, 0)


class LutMemo:
    """`LutMemo(lut, point=, curve=, root=, table_cache=None)`: `lut`(LutSet) 조회 memo. 상한 인자는 1 이상 정수(처음부터 `bound_state == "fixed"`).
    `table_cache`: 디스크 캐시(`TableCache`) -- None = 저장소 설정·환경 변수로 정한 기본 캐시(`TableCache.default()`),
    끄려면 `TableCache(None)`.
    `LutMemo.counting(lut, n_theta, table_cache=None)`: 계수 상태 memo -- point·curve·root 를 상한 없이 모으다 `open_count()` ~ `fix_bound()` 창(그 실행의 첫 커널
    평가)에서 조회한 서로 다른 키 수 U 로 영역 상한 (n_theta + 1)·U 를 고정한다."""

    def __init__(self, lut, *, point, curve, root, table_cache=None):
        self.lut = lut
        self.table_cache = TableCache.default() if table_cache is None else table_cache
        bounds = {"point": point, "curve": curve, "root": root}
        self._lru = {
            **{r: BoundedLRU(v) for r, v in bounds.items()},
            "derived": BoundedLRU(len(lut.slice_map) * len(DERIVED_TABLES)),
        }
        self._state = "fixed"
        self._n_theta = None

    @classmethod
    def counting(cls, lut, n_theta, *, table_cache=None):
        """계수 상태 memo(`bound_state == "counting"`). derived 영역은 처음부터 상한 LRU(계수 대상 아님)."""
        memo = cls(lut, point=1, curve=1, root=1, table_cache=table_cache)
        memo._lru.update({r: _Counting() for r in SWEEP_REGIONS})
        memo._state = "counting"
        memo._n_theta = n_theta
        return memo

    @property
    def bound_state(self):
        """"counting" | "window_open" | "fixed" (생성자 memo 는 처음부터 "fixed")."""
        return self._state

    def open_count(self):
        """창 열기: 이 호출부터 `fix_bound()` 까지 조회한 서로 다른 키를 센다. "counting" 에서만 부를 수 있다(아니면 `ValueError`)."""
        if self._state != "counting":
            raise ValueError("LutMemo.open_count: 계수 상태(counting)에서만 부를 수 있다(지금 " + self._state + ")")
        for r in SWEEP_REGIONS:
            self._lru[r].open()
        self._state = "window_open"

    def fix_bound(self):
        """창 닫기 + 상한 고정: 영역 r 상한 = (n_θ + 1)·U_r. "window_open" 에서만 부를 수 있다(아니면 `ValueError`)."""
        if self._state != "window_open":
            raise ValueError("LutMemo.fix_bound: 창이 열린 상태(window_open)에서만 부를 수 있다(지금 " + self._state + ")")
        for r in SWEEP_REGIONS:
            self._lru[r] = self._lru[r].fixed(self._n_theta)
        self._state = "fixed"

    def lookup(self, region, fn_name, key, compute):
        """영역 `region` 에서 키 `(lut.fp, fn_name) + key` 의 값. 없으면 `compute()` 결과를 저장해 돌려준다."""
        return self._lru[region].lookup((self.lut.fp, fn_name) + tuple(key), compute)

    def lookup_persistent(self, region, fn_name, key, compute, inputs, settings=()):
        """`lookup` + 디스크 캐시: memo 에 없으면 디스크 칸(키 = 코드 버전 + `inputs` 내용 + 설정)에서 읽고, 없거나 키가 다르거나
        깨졌으면 `compute()` 로 만들어 칸에 쓴다. `inputs`: 계산이 읽는 LUT 자료(배열·dataclass·tuple), `settings`: 결과에
        영향을 주는 호출부 상수(지문 가능한 값). 결과는 디스크 캐시를 거치든 아니든 같다(비트 동일)."""
        return self.lookup(region, fn_name, key, lambda: self.table_cache.fetch(
            self.lut.fp, TableCache.data_id(self.lut.provenance), fn_name, key, inputs, settings, compute))

    def stats(self):
        """((영역, LruStats), ...) 영역 이름 정렬."""
        return tuple((r, self._lru[r].stats()) for r in REGIONS)
