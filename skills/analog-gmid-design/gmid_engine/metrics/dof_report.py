"""구조 DOF -- 변수와 등식의 이분 매칭 rank (설계 41 §4.5, D-GB4e; GB4 단계 A7 `dof`).

진입점: `dof_report(variables, equations) -> DofReport`  (`variables` = 변수 이름 iterable, `equations` = {등식 이름: 그 등식이 읽는 변수 이름 iterable}).

최대 이분 매칭(증가 경로, Kuhn)의 크기가 구조 rank 다. 이름 순서로 훑는 결정론적 절차라 같은 입력이면 같은 매칭이다.
* 매칭되지 않은 등식이 있으면 `status = overconstrained` -- 그 등식 집합이 변수 수보다 많아 풀이가 없는 구조다(`achievability` 가 INFEASIBLE_TARGET `overconstrained` 로 정지).
  `competing_pairs` = 매칭 못 한 등식과, 그 등식이 쓰려던 변수를 이미 가져간 등식의 쌍(증가 경로가 막힌 곳 -- 어느 등식끼리 한 변수를 두고 겨루는지).
* 매칭되지 않은 변수는 `free_variables`(탐색이 고르는 자유도, 41 §4.5 'underdetermined 목록'), 없고 등식도 다 매칭이면 `square`, 있으면 `free_dof`.
* 수치 rank(41 §4.5 단계 B2: B1 표본의 등식 잔차 FD Jacobian, `numpy.linalg.matrix_rank`)는 평가 커널 표본이 필요한 단계 B 몫이라 이 함수는 `numeric_ranks = ()` 로 둔다.
등식·변수 집합을 만드는 쪽(`achievability`)이 S1·S2 구조에서 조립한다 -- 이 함수는 그래프 구조만 본다.
"""
from .achievability_types import DofReport

STATUS_OVERCONSTRAINED = "overconstrained"
STATUS_FREE = "free_dof"
STATUS_SQUARE = "square"


def _augment(eq, adjacency, owner, seen):
    for var in adjacency[eq]:
        if var in seen:
            continue
        seen.add(var)
        if var not in owner or _augment(owner[var], adjacency, owner, seen):
            owner[var] = eq
            return True
    return False


def dof_report(variables, equations):
    adjacency = {name: tuple(sorted(set(vs))) for name, vs in sorted(equations.items())}
    all_vars = sorted(set(variables) | {v for vs in adjacency.values() for v in vs})
    owner = {}
    unmatched, competing = [], []
    for eq in adjacency:
        seen = set()
        if not _augment(eq, adjacency, owner, seen):
            unmatched.append(eq)
            competing.extend((eq, owner[v]) for v in sorted(seen) if v in owner and owner[v] != eq)
    matched_vars = set(owner)
    free = tuple(v for v in all_vars if v not in matched_vars)
    status = STATUS_OVERCONSTRAINED if unmatched else (STATUS_FREE if free else STATUS_SQUARE)
    return DofReport(status, len(owner), len(all_vars), len(adjacency), tuple(unmatched), free, (), tuple(sorted(set(competing))))
