"""MOS 소신호 스탬프 -- 순수 함수 (설계 design_mod1_lut_mod5_mna 3.3 '소자 스탬프', 계획 N3.8 '단자별 gm·gmb·gds·cgg').

진입점: `mos_stamps`.

KCL 행 = 노드에서 나가는 전류. 채널 전류 I(d→s) = gm·(vg − vs) + gmb·(vb − vs) + gds·(vd − vs) 는 drain 행에 +, source 행에 −.
용량은 단자 쌍마다 2단자 스탬프(cgs g–s, cgd g–d, cgb g–b, cdb d–b, csb s–b). CS·CG·CD·pass 를 분기하지 않는다
(단자 스탬프가 전부 같다). bulk 가 source 와 같은 노드면 gmb 항은 스탬프 합에서 저절로 상쇄된다.
"""
from ._helpers_stamp import admittance_pair
from .records import MosSmallSignal, StampSet


def mos_stamps(device):
    """`MosSmallSignal` 하나 -> `StampSet`(노드 인덱스 공간의 (행, 열, 값) 목록). 값 0 항목은 내지 않는다."""
    if not isinstance(device, MosSmallSignal):
        raise TypeError("mos_stamps 는 MosSmallSignal 을 받는다: %r" % (device,))
    d, g, s, b = device.d, device.g, device.s, device.b
    gm, gmb, gds = device.gm, device.gmb, device.gds
    total = gm + gmb + gds
    g_entries = (
        (d, d, gds), (d, g, gm), (d, b, gmb), (d, s, -total),
        (s, d, -gds), (s, g, -gm), (s, b, -gmb), (s, s, total),
    )
    c_entries = ()
    for (x, y), value in (
        ((g, s), device.cgs),
        ((g, d), device.cgd),
        ((g, b), device.cgb),
        ((d, b), device.cdb),
        ((s, b), device.csb),
    ):
        if value:
            c_entries += admittance_pair(x, y, value)
    return StampSet(g=tuple(e for e in g_entries if e[-1]), c=c_entries)
