"""행 손가락 열 찾기(AI 판단을 규칙으로 옮긴 부분 -- 엔진이라면 이 탐색이 '행 기하' 블록).

규칙(two_stage_ota 손 레이아웃에서 쓴 꼴의 일반형):
  - 행 = kind 하나(방안 B). 모든 소자를 두 반으로 나눠(손가락 수 짝수) 왼쪽 반을 만들고 오른쪽 반은 거울(같은 소자,
    순서 반대) -> 모든 소자의 중심이 행 가운데 = 행 전체 공통 중심(common centroid), 대칭 짝은 자동 성립.
  - 왼쪽 반 = 소자 블록(그 소자 반 손가락이 이어진 구간)의 순열. 블록 안 손가락은 S/D 를 번갈아 써서 확산을 공유한다
    (h 개 손가락 블록이 넷 a 에서 시작하면 h 짝수 -> a 에서 끝, 홀수 -> 반대 넷).
  - 이웃 블록은 앞 블록 끝 넷 = 다음 블록 시작 넷이면 이어진다(Euler 연속), 아니면 끊김 1(확산 틈).
  - 가운데: 왼쪽 반 마지막 손가락과 오른쪽 반 첫 손가락은 같은 소자라 같은 넷을 공유 -- 끊김 없음.
  고르는 순서: 끊김 수 -> (같으면) 블록 순서의 사전순(결정적).
"""
import itertools, json, sys


def walk(order, half, dev, start):
    """order: 소자 이름 순열, half: 소자별 반 손가락 수. 반환 (끊김 수, 손가락 열 [(소자, 왼넷, 오른넷)])."""
    seq, breaks, cur = [], 0, start
    for name in order:
        a, b = dev[name]["s"], dev[name]["d"]
        if cur == a:
            l = a
        elif cur == b:
            l = b
        else:
            breaks += 1
            l = None
        if l is None:
            # 끊김: 다음 블록은 자유 시작 -- 블록 끝이 다음 블록과 이어지기 쉬운 쪽은 탐색이 순열로 덮는다(여기선 s 시작)
            l = a
            seq.append(("GAP", None, None))
        r = b if l == a else a
        for k in range(half[name]):
            seq.append((name, l, r))
            l, r = r, l
        cur = l  # 마지막 손가락의 오른쪽 넷
    return breaks, seq


_memo = {}


def best_row(names, half, dev):
    # 이어짐은 각 블록 손가락 수의 홀짝만으로 정해진다 -- 홀짝 꼴마다 순열 탐색 한 번(같은 결과, 결정적)
    pkey = tuple(sorted((n, half[n] % 2, dev[n]["s"], dev[n]["d"]) for n in names))
    if pkey not in _memo:
        h1 = {n: 1 + (half[n] % 2 == 0) for n in names}  # 홀짝만 같은 대표 길이(1 또는 2)
        best = None
        for order in itertools.permutations(sorted(names)):
            first = dev[order[0]]
            for start in sorted({first["s"], first["d"]}):
                br, _ = walk(order, h1, dev, start)
                key = (br, order, start)
                if best is None or key < best:
                    best = key
        _memo[pkey] = best
    br, order, start = _memo[pkey]
    _, left = walk(order, half, dev, start)
    right = [(n, r, l) for (n, l, r) in reversed(left)]
    return {"breaks": 2 * br, "order": list(order), "start": start, "seq": left + right}


if __name__ == "__main__":
    des = json.load(open(sys.argv[1], encoding="utf-8"))
    out = {}
    for row in des["rows"]:
        half = {n: des["devices"][n]["m"] // 2 for n in row["devices"]}
        out[row["name"]] = best_row(row["devices"], half, des["devices"])
    json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), indent=1)
