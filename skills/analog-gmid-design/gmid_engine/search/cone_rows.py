"""θ 전류 원뿔 제약 행 (sizing CONTRACT 4.4·5.1 `current_cone`, 설계 6.2).

진입점: `cone_rows(schema, theta) -> tuple[ConstraintRow]`(MOS 이름순).

* MOS 마다 전류 I_m = Σ (num/den)·(θ 전류 또는 고정값) 을 유리수로 정확히 잰다(`check_theta` 와 같은 식 -- 그래서 여기서
  모두 > 0 이면 커널이 정의역 밖으로 거부하지 않는다). 정규화 c_m = I_m / Σ|항|(항 크기 합 -- 무차원, 상수 없음, 원뿔 안에서
  (0, 1]). c_m ≤ 0 인 θ 는 커널을 부르지 않는다(정의역 밖, `STATUS_OUTSIDE_DOMAIN`).
* 기저 원소가 MOS 자신인 행(항 하나, 계수 1)은 c = 1 로 늘 만족이다(ln 좌표가 θ_I > 0 을 보장).
"""
from fractions import Fraction

from gmid_engine.sizing import THETA_CURRENT

from .search_values import CON_CONE, ConstraintRow


def cone_rows(schema, theta):
    source = {key: Fraction(v) for (kind, key), v in theta if kind == THETA_CURRENT}
    source.update({name: Fraction(v) for name, v in schema.fixed})
    rows = []
    for mos, terms in schema.current_cone:
        parts = tuple(Fraction(t.num, t.den) * source[t.source] for t in terms)
        scale = sum(abs(p) for p in parts)
        total = sum(parts)
        c = float(total / scale) if scale else float(total)
        if total > 0 and not c > 0:
            raise ArithmeticError("cone_rows: 양의 유리수 전류가 float 0 으로 사라졌다 " + repr((mos, total)))
        rows.append(ConstraintRow(CON_CONE + ":" + mos, c, False))    # 정의역 제약 -- NFR-5 활성 보고 대상 아님
    return tuple(rows)
