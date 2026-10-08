"""색 정제 공용 helper (struct_colour 의 1-WL 색과 struct_canon 의 정준 라벨링이 같은 정제를 쓴다).

`refine_colours(colour, neighbours)` -> 정수 색. 새 색 = (옛 색, (라벨, 이웃 옛 색) 정렬 다중집합) 의 정렬 순위(0부터), 색 종류 수가 더 늘지 않으면
멈춘다(최대 정점 수 회 -- 매 회 늘거나 멈추므로 유한). 색의 순서는 옛 색 순서를 보존한다(서명의 첫 성분이 옛 색). 이름을 읽지 않는다(이름은 정점
키로만 쓰이고 색 값에 들어가지 않는다). `colour` = {정점: 정렬 가능한 서명}, `neighbours` = {정점: [(라벨, 이웃 정점)]}.
"""


def _ranked(signature):
    order = {s: i for i, s in enumerate(sorted(set(signature.values())))}
    return {v: order[s] for v, s in signature.items()}


def refine_colours(colour, neighbours):
    colour = _ranked(colour)
    for _round in range(len(colour)):
        signature = {v: (colour[v], tuple(sorted((label, colour[u]) for label, u in neighbours[v]))) for v in colour}
        refined = _ranked(signature)
        if len(set(refined.values())) == len(set(colour.values())):
            break
        colour = refined
    return colour
