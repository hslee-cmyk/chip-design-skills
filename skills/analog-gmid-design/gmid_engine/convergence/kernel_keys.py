"""kind 마다 평가 커널이 쓸 폭 슬라이스 키 (계획 N3.17 LY7 '바뀐 폭 키를 읽는 필드만 재계산', 설계 40 §3.9 U14).

진입점: `kernel_keys(placements, kinds, current) -> (keys, conflicts)`.

평가 커널의 LUT 손잡이(`LutAccess.w_keys`)는 kind 마다 폭 슬라이스 하나다 -- 소자마다 다른 슬라이스를 줄 수 없다(sizing 계약). 레이아웃은 소자·행·그룹마다
다른 finger_w 를 고를 수 있으므로, 한 kind 의 배치가 둘 이상의 폭 키를 쓰면 충돌이다: 호출부(`place_layout`)가 레이아웃의 PDK 폭 키를 한 키로 좁혀 다시 놓는다.

* `placements` = `effective_placement` 결과, `kinds` = {소자: kind}, `current` = ((kind, 키), ...) 지금 커널이 쓰는 키(배치 소자가 없는 kind 는 이 값을 그대로 둔다).
* 반환 `keys` = ((kind, 키), ...) kind 순(`current` 의 모든 kind) -- 충돌 kind 의 자리는 사용 키 중 가장 작은 값이라 충돌이 없을 때만 의미가 있다. `conflicts` = ((kind, (사용 키 오름차순)), ...)
  둘 이상 쓰는 kind 만.
"""


def kernel_keys(placements, kinds, current):
    used = {}
    for p in placements:
        used.setdefault(kinds[p.name], set()).add(p.key)
    keys, conflicts = [], []
    for kind, old in sorted(current):
        found = used.get(kind)
        keys.append((kind, old if not found else min(found)))
        if found and len(found) > 1:
            conflicts.append((kind, tuple(sorted(found))))
    return tuple(keys), tuple(conflicts)
