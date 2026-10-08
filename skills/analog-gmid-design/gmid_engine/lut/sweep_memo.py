"""평가 sweep 용 LUT memo 상한 배선 도우미 -- 첫 평가가 센 서로 다른 키 수로 `LutMemo.from_sweep` 상한을 정한다 (설계 40 §7.3, lut/CONTRACT.md 2.2).

진입점: `sweep_memo`.

`LutMemo.from_sweep(lut, n_theta, unique_keys_per_eval)` 의 상한 = (n_θ + 1)·U_eval 에서 U_eval 은 **첫 평가가 센 서로 다른 키 수**다(영역 point·curve·root 마다).
이 도우미가 그 첫 평가를 계수용 memo 에서 한 번 돌려 U_eval 을 재고 운영 memo 를 만든다. 계수용 memo 는 그 평가 안에서만 값을 모아 두고(같은 키 재계산 없음)
평가가 끝나면 버려진다 -- 장수 memo 는 항상 상한 LRU(`LutMemo`)다.
첫 평가가 어떤 영역을 한 번도 안 쓰면 그 영역 상한은 0 = memo 하지 않음(오류 아님, CONTRACT 2.2).
호출부(소비자): search `build_search_context`(`_wire_sweep_memo`, layer0 첫 점의 첫 평가) -- 설계 40 §7.3.
"""
from .lut_memo import REGIONS, SWEEP_REGIONS, LutMemo


class _CountingMemo(LutMemo):
    """첫 평가용: 상한 없이 값을 모으며 영역별 서로 다른 키를 센다(평가 한 번 분량이라 유한)."""

    def __init__(self, lut, table_cache):
        super().__init__(lut, point=1, curve=1, root=1, table_cache=table_cache)
        self.seen = {region: {} for region in REGIONS}

    def lookup(self, region, fn_name, key, compute):
        full = (self.lut.fp, fn_name) + tuple(key)
        if full not in self.seen[region]:
            self.seen[region][full] = compute()
        return self.seen[region][full]


def sweep_memo(lut, n_theta, first_eval, table_cache=None):
    """`first_eval(memo)` 를 계수용 memo 로 한 번 돌려 영역별 서로 다른 키 수를 재고, `LutMemo.from_sweep(lut, n_theta, 그 수)` 를 돌려준다.
    `first_eval` = LUT 조회 함수에 memo 를 첫 인자로 주는 평가 한 번(예: 첫 θ 의 커널 평가). 반환 memo 는 새것이다(계수용 값은 넘기지 않는다)."""
    probe = _CountingMemo(lut, table_cache)
    first_eval(probe)
    return LutMemo.from_sweep(lut, n_theta, {region: len(probe.seen[region]) for region in SWEEP_REGIONS}, table_cache)
