"""제약 행의 이름 없는 정준 순서 (CONTRACT 3.25, 사용자 대원칙 '이름에 종속된 엔진 금지').

진입점: `canonical_row_key(sctx) -> key 함수(행 이름)`.

행 이름은 `<접두>:<소자>`(`w_min`·`seal6_bulk`·`inversion_floor`·`current_cone`) 또는 `<접두>:<번호>:<metric>…`(`ss`·`spec`, 번호는 선언 순서)이다.
key = (접두, 소자 구조 색 또는 -1, 나머지 이름) -- 소자 구조 색 `device.dc_colour`(1-WL 색 + 정준 위치, 정점마다 유일, 이름 없음)이라 행 순서가 이름 치환에
불변이다(이름은 소자가 아닌 꼬리에만 남는다). SLSQP 제약 벡터·Jacobian 행 순서가 이름을 따라 합산 순서가 바뀌어 끝자리가 달라지는 일을 막는다.
"""


def canonical_row_key(sctx):
    colour = dict(sctx.dc.base.column("device", "dc_colour"))

    def key(name):
        head, sep, tail = name.partition(":")
        if sep and tail in colour:
            return (head, colour[tail], tail)
        return (head, -1, tail)

    return key
