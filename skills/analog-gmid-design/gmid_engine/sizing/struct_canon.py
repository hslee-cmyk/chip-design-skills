"""정준 라벨링과 자기동형 궤도 (individualization-refinement, nauty 식) -- helper 파일.

진입점: 없음(`_module_map` kind "helper"). 공개 이름: `canonical_labeling`.

`canonical_labeling(colour, neighbours) -> (위치 {정점: 0..n-1}, 궤도 id {정점: int})`.
* 입력: `struct_colour` 가 만든 처음 색과 이웃. 정제 단계는 `_helpers_colour.refine_colours`(1-WL 색과 같은 정제)를 그대로 쓴다.
* 탐색 트리: 평형(equitable) 분할에서 가장 앞(색 순위 최소)의 정점 둘 이상인 칸을 대상 칸으로 잡고, 칸의 정점을 하나씩 개별화(individualize)한 뒤
  다시 정제한다. 분할이 이산이면 잎 -- 잎의 위치 함수 pos 로 그래프를 다시 쓴 증명서 cert(처음 색 열 + 정렬한 (pos v, 라벨, pos u))를 만든다.
  **정준 라벨링 = cert 가 최소인 잎의 pos**. 개별화 순서와 칸 안 정점 순서는 탐색 순서만 정하고 결과(최소 cert, 궤도)는 바꾸지 않는다.
* 가지치기: 잎의 cert 가 같은 선조 마디 아래 이미 본 잎과 같으면 두 잎 사이 pos 대응이 자기동형(마디까지의 개별화 정점을 고정)이다.
  그 대응으로 궤도를 합치고, 두 잎의 최저 공통 선조 마디의 현재 자식 부분 트리를 버린다. 마디마다 지역 union-find(그 마디 접두를 고정하는
  자기동형이 만든 궤도)에서 이미 탐색한 자식과 같은 궤도인 자식은 건너뛴다. 뿌리 마디의 union-find 가 전체 궤도다.
* 궤도 id = 궤도 구성원의 정준 위치 최솟값 -- 정준 그래프에서 궤도가 차지하는 위치 집합은 라벨링에 불변이라 이름을 읽지 않는다.
* 남은 동률 = 정확히 자기동형 궤도(1-WL 색 동률과 달리 비자기동형을 같은 색으로 남기지 않는다).
"""
from ._helpers_colour import refine_colours


class _Union:
    def __init__(self, items):
        self.parent = {v: v for v in items}

    def find(self, v):
        while self.parent[v] != v:
            self.parent[v] = self.parent[self.parent[v]]
            v = self.parent[v]
        return v

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def canonical_labeling(colour0, neighbours):
    vertices = sorted(colour0, key=repr)                   # 탐색 순서만 정한다(결과 불변)
    start = refine_colours(colour0, neighbours)
    base_rank = refine_colours(colour0, {v: [] for v in colour0})     # 처음 색의 순위(정제 전)
    best = []                                              # [(cert, pos)]
    root_union = []                                        # [뿌리 마디 union-find]
    frames = []                                            # 마디마다 {"seen": {cert: pos}, "union": _Union}

    def certificate(pos):
        order = sorted(vertices, key=lambda v: pos[v])
        edges = sorted((pos[v], label, pos[u]) for v in vertices for label, u in neighbours[v])
        return tuple(base_rank[v] for v in order), tuple(edges)

    def individualize(colour, vertex):
        return refine_colours({v: (c, v != vertex) for v, c in colour.items()}, neighbours)

    def visit(colour):
        """반환: None(정상) 또는 가지치기로 돌아갈 마디 깊이."""
        classes = {}
        for v in vertices:
            classes.setdefault(colour[v], []).append(v)
        if len(classes) == len(vertices):
            cert = certificate(colour)
            if not best or cert < best[0][0]:
                best[:] = [(cert, dict(colour))]
            for d in range(len(frames) - 1, -1, -1):
                other = frames[d]["seen"].get(cert)
                if other is not None:
                    inverse = {p: v for v, p in other.items()}
                    for v, p in colour.items():
                        for k in range(d + 1):
                            frames[k]["union"].union(v, inverse[p])
                    return d
            for fr in frames:
                fr["seen"][cert] = dict(colour)
            return None
        target = classes[min(c for c, members in classes.items() if len(members) > 1)]
        frames.append({"seen": {}, "union": _Union(vertices)})
        here = len(frames) - 1
        explored = []
        for v in target:
            union = frames[here]["union"]
            if any(union.find(v) == union.find(w) for w in explored):
                continue
            ret = visit(individualize(colour, v))
            explored.append(v)
            if ret is not None and ret < here:
                frames.pop()
                return ret
        done = frames.pop()
        if not frames:
            root_union.append(done["union"])
        return None

    visit(start)
    pos = best[0][1]
    union = root_union[0] if root_union else _Union(vertices)
    least = {}
    for v in vertices:
        root = union.find(v)
        least[root] = min(least.get(root, pos[v]), pos[v])
    return pos, {v: least[union.find(v)] for v in vertices}
