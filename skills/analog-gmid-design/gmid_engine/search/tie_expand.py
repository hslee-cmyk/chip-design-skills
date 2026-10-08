"""묶인 θ 성분 값 채우기 (CONTRACT 3.24).

진입점: `expand_ties(ties, theta, negated=(), zeros=()) -> dict` -- `ties` = `SearchDomain.ties`, `theta` = 대표 성분만(또는 전체)을 가진 θ 매핑.
묶인 성분마다 대표의 값을 복사한 새 dict 를 돌려준다(입력은 바꾸지 않는다): `negated` 에 든 구성원은 −대표 값(자기동형이 단자 순서를 뒤집는 방향 없는 수동소자의
가지 전류), `zeros` 의 성분은 0.0(대칭·KCL 이 정하는 구조적 0). 묶음이 없으면 입력의 사본.
"""


def expand_ties(ties, theta, negated=(), zeros=()):
    out = dict(theta)
    flipped = frozenset(negated)
    for rep, members in ties:
        value = out[rep]
        for member in members:
            out[member] = -value if member in flipped else value
    for component in zeros:
        out[component] = 0.0
    return out
