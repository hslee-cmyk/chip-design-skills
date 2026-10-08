"""LUT 조회 memo -- graph 밖에 남는 유일한 memo (확정 사항 4, 설계 MOD1 2.6·2.9).

진입점: `LutMemo`.

* 영역 4개(`REGIONS`): point(OpPoint·gmb·용량·[r6] VDsat), curve(Curve), root(VGS 근·역산), derived(tol_V 표·곡선 보고·
  [r6] VDsat 허용오차 표·중점 검증).
  영역마다 `core.BoundedLRU` 하나를 이 객체가 소유한다(모듈 수준 캐시 없음).
* 키 = (LutSet 지문, 함수 이름) + 호출부가 넘긴 값(kind, w_key, 축 float 그대로 -- 반올림 없음). 객체·`id()` 키는
  `TypeError`(BoundedLRU 의 불변 검사).
* 상한: point·curve·root 는 부르는 쪽이 계산해 넘긴다 = 한 평가 sweep 고유 키 상계
  `B = (n_theta + 1) * U_eval`(`from_sweep`). derived 상한 = 슬라이스 수 * 파생 표 종류 수(`DERIVED_TABLES`) --
  퇴출이 없도록 개수 그대로.
* [2026-10-08] 비싼 파생 표는 `lookup_persistent` 로 디스크 캐시(`TableCache`, CONTRACT 2.1)를 거친다. memo(메모리)는 그대로다.
"""
from gmid_engine.core import BoundedLRU

from .table_cache import TableCache

REGIONS = ("curve", "derived", "point", "root")
DERIVED_TABLES = ("curve_report", "midpoint_l_bin_checks", "tol_v_table", "tol_vdsat_table")
SWEEP_REGIONS = ("curve", "point", "root")


class LutMemo:
    """`LutMemo(lut, point=, curve=, root=, table_cache=None)`: `lut`(LutSet) 조회 memo. 상한 인자는 1 이상 정수.
    `table_cache`: 디스크 캐시(`TableCache`) -- None = 저장소 설정·환경 변수로 정한 기본 캐시(`TableCache.default()`),
    끄려면 `TableCache(None)`."""

    def __init__(self, lut, *, point, curve, root, table_cache=None):
        self.lut = lut
        self.table_cache = TableCache.default() if table_cache is None else table_cache
        self._lru = {
            "point": BoundedLRU(point),
            "curve": BoundedLRU(curve),
            "root": BoundedLRU(root),
            "derived": BoundedLRU(len(lut.slice_map) * len(DERIVED_TABLES)),
        }

    @classmethod
    def from_sweep(cls, lut, n_theta, unique_keys_per_eval):
        """sweep 상계로 만든다: 영역 r 의 상한 = `(n_theta + 1) * unique_keys_per_eval[r]`(r = point·curve·root)."""
        per = dict(unique_keys_per_eval)
        return cls(lut, **{r: (n_theta + 1) * per[r] for r in SWEEP_REGIONS})

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
