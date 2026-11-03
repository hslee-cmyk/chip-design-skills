"""ω → 0 극한 식 공용 helper (사용처: `dc_limit.py` 극한 해, `sensitivity.py` 극한 해의 1차 민감도).

공개 함수: `limit_matrix(g, c, charge)` -- G 사본의 전하 행을 C 행으로 바꾼 극한 행렬(전하 보존 행 교체의 유일한 자리),
`dc_limit_parts(system)` -- (쌓은 실수 행렬, 우변, 전하 주입 열). 블록 국소 풀이·전회로 노달 풀이(`_helpers_nodal.nodal_factor`)도 같은 `limit_matrix` 를 부른다.

용량 전용 노드 F(`charge_nodes`) 행은 전하 보존 C_F·x = BC_F, 나머지 행 R 은 G_R·x = BG_R(metrics CONTRACT 3.3). 이 행렬이 극한 식
그 자체다 -- 두 사용처가 같은 식을 따로 쓰지 않게 한 곳에 둔다. 전하 주입 열 = BG_F ≠ 0 인 열(직류 전류가 용량 노드에 쌓여 극한 발산).
"""
import numpy


def limit_matrix(g, c, charge):
    """`g` 사본에서 `charge` 행(전하 보존 행)을 `c` 의 같은 행으로 바꾼 행렬. `g` 는 바꾸지 않는다. 우변 쌍(BG, BC)에도 같은 식을 쓴다."""
    out = numpy.array(g)
    rows = [int(i) for i in charge]
    out[rows, :] = numpy.asarray(c)[rows, :]
    return out


def dc_limit_parts(system):
    """`MnaSystem`(결함 없음, 미지수 1개 이상) -> (행렬 (n, n), 우변 (n, m), ((열, 주입 노드 tuple), ...) -- 발산 열)."""
    charge = list(system.charge_nodes)
    matrix = limit_matrix(system.G, system.C, charge)
    rhs = limit_matrix(system.BG, system.BC, charge)
    injected = []
    for j in range(len(system.excitations)):
        nodes = tuple(system.nodes[i] for i in charge if system.BG[i, j])
        if nodes:
            injected.append((j, nodes))
    return matrix, rhs, tuple(injected)
