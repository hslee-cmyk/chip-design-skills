"""재검증이 거절한 기하의 폭 키 하나를 레이아웃 후보에서 뺀다 (계획 N3.17 LY3 '위반하면 W_request 경로', 설계 40 §3.9 U14, 계약 CONTRACT.md 7절).

진입점: `key_exclusion(pdk, placements, kinds, sized_w) -> (excluded, narrower_pdk)`.

실현 기하의 재평가가 봉인·제약을 어기고 거부할 W_request 도 없으면, 어느 kind 의 폭 키(finger_w) 선택이 그 W 어긋남을 만들었는지 가린다: 사이징 W 대비 실현 W 의 어긋남
`|ln(W_m / sized_w)|` 이 가장 큰 소자(동률은 소자 이름순)의 지금 finger 폭 키(그 배치 `p.key`)를 그 kind 후보에서 뺀다(WB-1: kind 당 슬라이스 하나라는 제약이 없어졌으므로 키는 소자의 배치 키다). 이름·회로 무관, 새 상수 없음.
반환 `excluded` = (kind, 폭 키), `narrower_pdk` = 그 키를 뺀 `LayoutPdk`. 그 kind 에 남는 키가 없으면 `(excluded, None)` -- 더 시도할 폭이 없다.
키를 하나 빼므로 반복은 PDK 폭 키 수 이하에서 끝난다(단조 감소).
"""
import dataclasses
import math


def key_exclusion(pdk, placements, kinds, sized_w):
    worst = min(placements, key=lambda p: (-abs(math.log(p.W_m / sized_w[p.name])), p.name))
    kind, key = kinds[worst.name], worst.key
    remaining = tuple(tuple(k for k in ks if k != key) if name == kind else tuple(ks) for name, ks in pdk.slice_width_keys)
    if not remaining[[name for name, _ks in pdk.slice_width_keys].index(kind)]:
        return (kind, key), None
    narrower = dataclasses.replace(pdk, slice_width_keys=tuple((name, ks) for (name, _old), ks in zip(pdk.slice_width_keys, remaining)))
    return (kind, key), narrower
