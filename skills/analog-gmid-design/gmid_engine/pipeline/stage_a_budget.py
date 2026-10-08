"""단계 A 계수 예산 N_S (설계 41 §0, 40 §10.1 `count_budget`).

진입점: `structure_count_budget(lut, kinds, declared=None) -> int`.

N_S = 이 회로에 쓰이는 kind 들의 LUT 격자점 수 합 = Σ_kind Σ_(그 kind 의 폭 슬라이스) |L|·|VGS|·|VDS|·|VS|. 근거는 "상한 계산 한 번이 LUT 전체를 한 번
훑는 양을 넘지 않는다"이고 LUT 파일에서 정해지는 값이라 새 상수가 아니다. 시간과 무관해 같은 LUT·kind 면 늘 같다.

**정의역**: 합이 1 미만이면(`kinds` 가 비었거나 그 kind 의 LUT 폭 슬라이스가 없으면) N_S 는 정의되지 않는다(계수 예산은 1 이상 int, `build_s1v`) -- `ValueError`.
`run_stage_a` 는 이를 잡아 `StructureUnresolvedError`(reason `count_budget_undefined`)로 바꿔 보고서에 정지 사유로 쓴다(exit 2, 보고서 항상 기록). spec `structure_count_budget` 선언(U5 로더)이 있으면 그 값이 대체한다(`declared`, 40 §3.1).
구현은 U9 `search/count_budget.py` 로 옮겼고 이 함수는 단계 A 진입점이 부르는 얇은 호출이다(공개 이름 유지).
"""
from gmid_engine.search import count_budget


def structure_count_budget(lut, kinds, declared=None):
    """단계 A 계수 예산 N_S -- 구현은 `search.count_budget` 한 곳이다(U9). `declared` = spec `structure_count_budget`(`CountBudgetDecl` 또는 None)."""
    return count_budget(lut, kinds, declared)
