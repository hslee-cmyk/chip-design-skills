"""후보 θ 검사·정규화 (설계 3.1 5 DOF 표, 3.4 y 정규화, 계획 DEC-70 θ 전류 변수).

진입점: `check_theta(schema, values) -> Theta`.

* `values`: {(kind, key): 수} Mapping 또는 그 쌍 iterable. 키 집합이 `schema.components` 와 정확히 같아야 한다(빠짐·남음
  -> `ValueError`, 목록을 메시지로). 값은 유한 실수(bool 제외).
* 정의역(탐색 bounds 가 아니라 θ 가 뜻을 갖는 집합): `y` ∈ [0, 1](창 안 위치), `L` > 0, `resistance` > 0,
  **θ 전류 = 전류 원뿔 `schema.current_cone`**: MOS 행마다 Σ (num/den)·(θ 전류 또는 `schema.fixed` 값) > 0(유리수로 정확히
  잰다). 밖이면 `ValueError`(MOS 이름과 그 전류 목록) -- 전도 MOS 전류 ≤ 0 은 평가 실패가 아니라 정의역 밖이다(탐색은 이
  선형 부등식을 제약으로 받는다). 기저 원소가 MOS 자신인 행은 θ_I > 0 상자 하한이다.
* 반환 `Theta(values)` = 키 정렬 (((kind, key), float), ...).
"""
import math
from collections.abc import Mapping
from fractions import Fraction

from .s2_values import THETA_CURRENT, THETA_L, THETA_RESISTANCE, THETA_Y, Theta, ThetaSchema


def check_theta(schema, values):
    if not isinstance(schema, ThetaSchema):
        raise TypeError("check_theta: schema 는 ThetaSchema 여야 한다")
    pairs = dict(values.items() if isinstance(values, Mapping) else values)
    expected = set(schema.components)
    missing = sorted(expected - set(pairs))
    extra = sorted(set(pairs) - expected, key=repr)
    if missing or extra:
        raise ValueError("check_theta: θ 키가 스키마와 다르다 -- 빠짐 " + repr(missing) + ", 남음 " + repr(extra))
    out = []
    for key in sorted(pairs):
        value = pairs[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("check_theta: 유한 실수가 아니다 " + repr((key, value)))
        value = float(value)
        kind = key[0]
        if kind == THETA_Y and not 0 <= value <= 1:
            raise ValueError("check_theta: y 는 [0, 1] 이다 " + repr((key, value)))
        if kind in (THETA_L, THETA_RESISTANCE) and not value > 0:
            raise ValueError("check_theta: 양수여야 한다 " + repr((key, value)))
        out.append((key, value))
    source = {key: Fraction(v) for (kind, key), v in out if kind == THETA_CURRENT}
    source.update({name: Fraction(v) for name, v in schema.fixed})
    outside = []
    for mos, terms in schema.current_cone:
        current = sum(Fraction(t.num, t.den) * source[t.source] for t in terms)
        if not current > 0:
            outside.append((mos, float(current)))
    if outside:
        raise ValueError("check_theta: θ 전류가 정의역(전도 MOS 전류 > 0) 밖이다 " + repr(outside))
    return Theta(tuple(out))
