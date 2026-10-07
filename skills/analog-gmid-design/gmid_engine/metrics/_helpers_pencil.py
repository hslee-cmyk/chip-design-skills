"""일반화 고유값의 유한 근 공용 helper (사용처: `pencil_roots.py` 계 극점·영점, `probe_loop.py` 루프 이득 T 의 극점·영점).

공개 함수: `finite_eigs(a, e)` -- pencil (a, −e) 의 유한 고유값(원점 판정 포함), 정렬 (|s|, 실부, 허부).

* 균형(Ward 방법 -- LAPACK ggbal 의 배율): QZ 전에 행·열을 2 의 거듭제곱 대각 배율 D_r·(a + s·e)·D_c 로 바꾼다(고유값 불변,
  반올림 없는 정확한 변환). 지수는 a·e 의 0 아닌 원소 전부의 Σ(log2|x_ij| + r_i + c_j)² 최소제곱 해를 반올림한 것(한 번의
  lstsq, 반복·문턱 상수 없음). 노드 KCL 행(컨덕턴스 ~1e-5, 용량 ~1e-12)과 프로브·관측 행(~1)이 섞인 pencil 에서 아래 판정이
  행 크기에 끌려 실제 근을 원점·무한대로 오판하지 않게 한다(7a 예 7: 균형 없이는 −ω_p 극점이 원점으로 판정됐다).
* '유한' 판정은 상수가 아니라 QZ 동차 좌표 (α, β)로 한다(균형 뒤 행렬 기준): |β| ≤ 차원·기계 엡실론·‖e‖_F 이거나 |s| = |α/β|
  가 분해능 한계 ‖a‖_F/(차원·eps·‖e‖_F) 를 넘으면 무한대(β 가 반올림 오차 수준 / 상대 오차 1 이상) -- 특이 pencil 의 불확정
  고유값(α·β 모두 반올림 수준)도 같은 판정으로 빠진다. 같은 방식으로
  |α| ≤ 차원·eps·‖a‖_F 이면 그 고유값은 원점(s = 0, 정확히 0 으로 낸다)이다 -- 용량 전용 노드의 전하 모드가 반올림 잡음으로
  작은 |s| 가 되어 격자 꺾임점에 들어가지 않게 한다(분해능 상수 없음).
"""
import numpy
import scipy.linalg


def _balance(a, e):
    """Ward 균형(LAPACK ggbal 의 배율 방법): a·e 의 0 아닌 원소 전부에 대해 Σ(log2|x_ij| + r_i + c_j)² 를 최소로 하는 행·열
    지수 r·c 를 최소제곱으로 한 번에 풀고(lstsq -- 반복·문턱 없음) 정수로 반올림해 2 의 거듭제곱 배율로 쓴다(정확한 변환)."""
    size = a.shape[0]
    rows_idx, cols_idx, logs = [], [], []
    for matrix in (a, e):
        r, c = numpy.nonzero(matrix)
        rows_idx.append(r)
        cols_idx.append(c)
        logs.append(numpy.log2(numpy.abs(matrix[r, c])))
    r, c, target = numpy.concatenate(rows_idx), numpy.concatenate(cols_idx), -numpy.concatenate(logs)
    if not target.size:
        return a, e
    design = numpy.zeros((target.size, 2 * size))
    design[numpy.arange(target.size), r] = 1.0
    design[numpy.arange(target.size), size + c] = 1.0
    exponents = numpy.rint(numpy.linalg.lstsq(design, target, rcond=None)[0])
    row_scale = numpy.ldexp(1.0, exponents[:size].astype(int))
    col_scale = numpy.ldexp(1.0, exponents[size:].astype(int))
    return row_scale[:, None] * a * col_scale[None, :], row_scale[:, None] * e * col_scale[None, :]


def finite_eigs(a, e):
    """정사각 실수·복소 행렬 a, e -> (a + s·e) 가 특이한 유한 s 의 tuple(정렬)."""
    size = a.shape[0]
    if size == 0:
        return ()
    a, e = _balance(numpy.asarray(a), numpy.asarray(e))
    alpha, beta = scipy.linalg.eig(a, -e, right=False, homogeneous_eigvals=True)
    eps = numpy.finfo(float).eps
    tol_beta = size * eps * numpy.linalg.norm(e)
    tol_alpha = size * eps * numpy.linalg.norm(a)
    out = []
    for al, be in zip(alpha, beta):
        # 무한대: β 가 반올림 수준이거나, |s| = |α/β| 가 분해능 한계 ‖a‖/(차원·eps·‖e‖) 를 넘음(β 의 상대 오차가 1 초과)
        if abs(be) <= tol_beta or abs(al) * tol_beta > abs(be) * numpy.linalg.norm(a):
            continue
        out.append(complex(0, 0) if abs(al) <= tol_alpha else complex(al / be))
    return tuple(sorted(out, key=lambda z: (abs(z), z.real, z.imag)))
