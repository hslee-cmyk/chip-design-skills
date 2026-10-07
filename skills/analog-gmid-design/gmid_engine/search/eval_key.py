"""평가 키 정의 한 곳 (설계 design_mod6_search_front 7.1, 계획 N3.5 실패 캐시 키).

진입점: `eval_key(context_fp, schema_fp, theta, cells, w_fixed_fp) -> EvalKey`.

* `theta` = ((kind, key), 값) 키 정렬 쌍(성분 목록은 스키마 지문이 정하므로 값만 `float.hex` 로 넣는다 -- 1 ulp 다르면 다른 키).
* `cells` = L 칸 index 벡터(소자 이름순), `w_fixed_fp` = MOD8 고정 W 집합 지문(없으면 None).
* ε·시작점·호출 출처는 평가 결과와 무관하므로 키 밖이다 -- 그래서 같은 θ 에 대한 fun·jac·constraints·ε 점 사이 재방문이
  커널 1회로 모인다(설계 0절 5).
"""
from .search_values import EvalKey


def eval_key(context_fp, schema_fp, theta, cells, w_fixed_fp):
    theta = tuple(theta)
    pair = len(("key", "value"))   # (키, 값) 쌍, 키 = (kind, key) 쌍
    if not all(isinstance(p, tuple) and len(p) == pair and isinstance(p[0], tuple) and len(p[0]) == pair
               for p in theta):
        raise ValueError("eval_key: θ 는 ((kind, key), 값) 쌍의 tuple 이어야 한다")
    keys = tuple(k for k, _v in theta)
    if keys != tuple(sorted(keys)):
        raise ValueError("eval_key: θ 는 키 정렬 쌍이어야 한다")
    return EvalKey(context_fp, schema_fp, tuple(cells), w_fixed_fp, tuple(float(v).hex() for _k, v in theta))
