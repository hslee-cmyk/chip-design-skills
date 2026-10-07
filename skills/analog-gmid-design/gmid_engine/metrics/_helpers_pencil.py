"""일반화 고유값의 유한 근 공용 helper (사용처: `pencil_roots.py` 계 극점·영점, `probe_loop.py` 루프 이득 T 의 극점·영점).

공개 함수: `finite_eigs(a, e)` -- pencil (a, −e) 의 유한 고유값(원점 판정 포함), 정렬 (|s|, 실부, 허부).

'유한' 판정은 상수가 아니라 QZ 동차 좌표 (α, β)로 한다: |β| ≤ 차원·기계 엡실론·‖e‖_F 이면 무한대(β 가 반올림 오차 수준) --
특이 pencil 의 불확정 고유값(α·β 모두 반올림 수준)도 같은 판정으로 빠진다. 같은 방식으로 |α| ≤ 차원·eps·‖a‖_F 이면 그 고유값은
원점(s = 0, 정확히 0 으로 낸다)이다 -- 용량 전용 노드의 전하 모드가 반올림 잡음으로 작은 |s| 가 되어 격자 꺾임점에 들어가지
않게 한다(분해능 상수 없음).
"""
import numpy
import scipy.linalg


def finite_eigs(a, e):
    """정사각 실수·복소 행렬 a, e -> (a + s·e) 가 특이한 유한 s 의 tuple(정렬)."""
    size = a.shape[0]
    if size == 0:
        return ()
    alpha, beta = scipy.linalg.eig(a, -e, right=False, homogeneous_eigvals=True)
    eps = numpy.finfo(float).eps
    tol_beta = size * eps * numpy.linalg.norm(e)
    tol_alpha = size * eps * numpy.linalg.norm(a)
    out = []
    for al, be in zip(alpha, beta):
        if abs(be) <= tol_beta:
            continue
        out.append(complex(0, 0) if abs(al) <= tol_alpha else complex(al / be))
    return tuple(sorted(out, key=lambda z: (abs(z), z.real, z.imag)))
