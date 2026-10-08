"""자기동형 궤도 -- 정준형의 생성자로 만든 정점 궤도 (설계 40 §6 2).

진입점: `automorphism_orbits(canon) -> {정점: 궤도 id}`. `canon` = `canonical_form` 결과.

* 궤도 = 생성자들이 만드는 군 아래 정점의 동치류(union-find). **궤도 id = 구성원의 정준 위치 최솟값** -- 정준 그래프에서 궤도가 차지하는 위치 집합은 라벨링에
  불변이라 이름을 읽지 않는다. 같은 궤도 ⇔ 같은 값.
* 생성자가 없으면 모든 정점이 자기 궤도(id = 자기 위치).
* 선언 표시와 레일·포트 role 은 `canonical_form` 의 처음 색에 들어 있어 이미 보존된다. 차동 포트 p/n 은 같은 색(port_direction)이라 서로 바뀔 수 있다.
"""


def automorphism_orbits(canon):
    parent = {v: v for v in canon.position}

    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    for generator in canon.generators:
        for v, image in generator:
            rv, ri = find(v), find(image)
            if rv != ri:
                parent[ri] = rv
    least = {}
    for v, p in canon.position.items():
        root = find(v)
        least[root] = min(least.get(root, p), p)
    return {v: least[find(v)] for v in canon.position}
