"""MOD7 판정 축 면적 동률 폭 ΔA_tie (계획 DEC-79, DEC-95 (2), U12 D-LY1).

진입점: `area_tie_m2(a, b) -> float`.

`a`·`b` = 두 점의 `FloorplanSummary`. ΔA_tie = MANUFACTURINGGRID x max(두 점 bbox 의 변 네 개) -- 외곽 변 하나가 격자 한 칸 어긋나면
면적이 최대 grid x (큰 변) 달라지므로, 그 이내 차이는 레이아웃 해상도 밖이다. 옛 `grid^2` 는 변이 아니라 격자 한 칸 면적이라
외곽이 클 때 한 칸 어긋남보다 훨씬 작은 폭이었다. 두 점의 격자는 같아야 한다(다르면 `ValueError`). 대칭이고 `a`·`b` 가 같아도 0 이 아니다.
소비자: MOD8 판정 축 재필터(`search.pareto.nondominated` 의 `ties` 폭 함수, 점 id -> `FloorplanSummary`).
"""


def area_tie_m2(a, b):
    if a.grid_m != b.grid_m:
        raise ValueError("area_tie_m2: 두 점의 제조 격자가 다르다 (%r, %r)" % (a.grid_m, b.grid_m))
    return a.grid_m * max(a.bbox_width_m, a.bbox_height_m, b.bbox_width_m, b.bbox_height_m)
