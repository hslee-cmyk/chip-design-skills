"""묶인 θ 성분 값 채우기 (CONTRACT 3.24).

진입점: `expand_ties(ties, theta) -> dict` -- `ties` = `SearchDomain.ties`, `theta` = 대표 성분만(또는 전체)을 가진 θ 매핑.
묶인 성분마다 대표의 값을 복사한 새 dict 를 돌려준다(입력은 바꾸지 않는다). 묶음이 없으면 입력의 사본.
"""


def expand_ties(ties, theta):
    out = dict(theta)
    for rep, members in ties:
        value = out[rep]
        for member in members:
            out[member] = value
    return out
