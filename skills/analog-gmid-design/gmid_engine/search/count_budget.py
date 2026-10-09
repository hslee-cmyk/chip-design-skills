"""계수 예산 N_S (설계 41 §0, 40 §10.1 `count_budget`, D-NS) -- 시간과 무관한 구조 계수 상한.

진입점: `count_budget(lut, kinds, declared=None) -> int`.

* **기본값**: N_S = 이 회로에 쓰이는 kind 들의 LUT 격자점 수 합 = Σ_kind Σ_(그 kind 의 폭 슬라이스) |L|·|VGS|·|VDS|·|VS|. 근거는 "상한 계산 한 번이 LUT 전체를
  한 번 훑는 양을 넘지 않는다"이고 LUT 파일에서 정해지는 값이라 새 상수가 아니다. 같은 LUT·kind 면 늘 같다(결정론, 시간 무관).
* **선언값**: spec human `structure_count_budget{value, source}`(authoring `CountBudgetDecl`)가 주어지면 기본값 대신 그 값을 쓴다. 이 값은 S0 지문에 든다(spec 지문).
* **정의역**: 기본값의 합이 1 미만이면(`kinds` 가 비었거나 그 kind 의 LUT 폭 슬라이스가 없으면) N_S 는 정의되지 않는다(계수 예산은 1 이상 int) -- `ValueError`.
  선언값은 spec 로더가 양의 정수(bool 아님)로 이미 거른다.
* **쓰임**(적용 대상 41 §0): 블록 gain 상한의 격자 곱 Π(`metrics.block_gain_bounds`, 넘으면 '미상'), 복합 블록 Π, 사이클 열거(`build_s1v(count_budget=)`), 조합 DP 상태 수.
  `metrics` 는 `search` 보다 아래 층이라 이 함수를 부르지 않고 파이프라인(`pipeline.run_stage_a`·`run_stage_b`)이 값을 만들어 넘긴다.
"""
import math


def count_budget(lut, kinds, declared=None):
    if declared is not None:
        return int(declared.value)
    total = sum(math.prod(len(axis) for axis in s.grids) for (kind, _w_key), s in lut.slice_map.items() if kind in kinds)
    if total < 1:
        raise ValueError("count_budget: 쓰는 kind " + repr(sorted(kinds)) + " 의 LUT 슬라이스가 없다")
    return total
