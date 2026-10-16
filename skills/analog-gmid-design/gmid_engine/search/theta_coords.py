"""탐색 좌표 x <-> θ 값 -- ln 좌표 원값 보존 정본 (설계 40 §2.4.14 (2), 사용자 결정 X-1 (1)·X-14).

진입점: `ThetaCoords`(frozen dataclass). `ThetaCoords.start(variables, theta)` 로 만들고 `coords.to_theta(x)` 로 되돌린다.

* 시작 좌표 `x0`ᵢ = log 변수면 ln θᵢ, 아니면 θᵢ. **자르지 않는다**(변수 bounds 밖이어도 그대로 -- clip 인자 없음, X-14). 외층·층 0 은 부르는 쪽에서 자기 상자로
  자른 좌표를 풀이기에 주고, 풀이기가 돌려준 x 도 자른 뒤 `to_theta` 에 넘긴다. 감도 게이트는 자르지 않는다.
* `to_theta(x)`: 변수마다 v = float(xᵢ). v 가 시작 좌표 x0ᵢ 와 float 정확 일치하면 시작 θ 원값(ln -> exp 왕복의 ulp 오차 없음), 아니면 log 변수는 exp(v), 아니면 v.
  변수 밖 성분은 `theta` 의 값 그대로다.
* 성질: `to_theta(x0)` 는 `theta` 와 성분마다 비트 동일. 좌표 하나만 움직인 x(FD 시험점)의 나머지 성분도 `theta` 와 비트 동일.
* 풀이 하나 동안의 좌표 변환 값이다 -- 설계 값 저장소가 아니다.
"""
import dataclasses
import math


@dataclasses.dataclass(frozen=True)
class ThetaCoords:
    variables: tuple
    x0: tuple
    raw: tuple
    fixed: tuple

    @classmethod
    def start(cls, variables, theta):
        """`variables` = `Variable`(component, log, ...) 의 순서 있는 묶음, `theta` = 시작 θ 전체 사전."""
        variables = tuple(variables)
        raw = tuple(theta[v.component] for v in variables)
        x0 = tuple(math.log(value) if v.log else value for v, value in zip(variables, raw))
        names = {v.component for v in variables}
        return cls(variables, x0, raw, tuple((k, value) for k, value in theta.items() if k not in names))

    def to_theta(self, x):
        out = dict(self.fixed)
        for v, start, raw, value in zip(self.variables, self.x0, self.raw, x):
            value = float(value)
            out[v.component] = raw if value == start else (math.exp(value) if v.log else value)
        return out
