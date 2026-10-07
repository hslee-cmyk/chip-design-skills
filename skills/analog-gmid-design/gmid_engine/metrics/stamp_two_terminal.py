"""2단자 수동소자 스탬프 -- 순수 함수 (설계 design_mod1_lut_mod5_mna 3.3 '저항: 값은 ss.passive 에서만', DF-06·DF-37).

진입점: `two_terminal_stamps`.

저항은 컨덕턴스 1/R 을 G 에, 커패시터는 C 에 넣는다. 값은 레코드가 이미 양수·유한으로 검사했다(기본값 없음).
"""
from ._helpers_stamp import admittance_pair
from .records import Capacitor, Resistor, StampSet


def two_terminal_stamps(element):
    """`Resistor` 또는 `Capacitor` 하나 -> `StampSet`. 다른 형식은 거부(조용한 누락 없음 -- DF-37)."""
    if isinstance(element, Resistor):
        return StampSet(g=admittance_pair(element.a, element.b, 1.0 / element.ohm))
    if isinstance(element, Capacitor):
        return StampSet(c=admittance_pair(element.a, element.b, element.farad))
    raise TypeError("two_terminal_stamps 는 Resistor·Capacitor 만 받는다: %r" % (element,))
