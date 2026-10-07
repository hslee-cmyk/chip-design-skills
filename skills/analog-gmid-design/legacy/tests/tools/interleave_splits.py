"""홀수 finger 쌍 교차 대칭 분할 test 도구.

`stick_diagram.py`에서 이관됐다(spec card 20260930-d-move-tests, 운영 호출 0 -- self-test 전용).
본문은 바이트 그대로이며 엔진 이름을 import하지 않는다.
"""


def find_interleaved_symmetric_splits(count_a: int, count_b: int) -> list:
    """A, B가 서로 swap 파트너(예: pair_map={"A":"B","B":"A"})이고 **개별 finger 총합이
    홀수**라 각자 단독으로는 좌우 절반씩 나눌 수 없을 때, 두 소자를 섞어 배치하면 전체 대칭을
    살릴 수 있다 — folded cascode bottom row의 실제 사례(M9=3, M10=3, 둘 다 홀수)가 정확히
    이 경우다: 원본 시퀀스 `...9xxoo99nno...`에서 M9는 좌1/우2, M10은 좌2/우1로 **불균등하게**
    나뉘어 있지만, 두 소자가 서로의 불균형을 정확히 상쇄해 전체는 대칭이 된다.

    수학적으로: A가 왼쪽에 `a_left`개, B가 왼쪽에 `b_left`개 있으면, 대칭이 성립하려면
    `a_left == count_b - b_left`(B의 오른쪽 개수)이고 `b_left == count_a - a_left`(A의
    오른쪽 개수)여야 한다 — 이 두 식을 풀면 **count_a == count_b일 때만** 정수해가 존재한다
    (다르면 잔여 불균형이 남아 다른 소자로 흡수하거나, 폴디드 캐스코드의 MP처럼 축 위에 단독
    배치해야 한다).

    **"최대한 섞는다" 원칙(우선순위 정렬)**: 대칭 조건을 만족하는 후보가 여러 개일 때 전부
    matching 효과가 같은 건 아니다 — 한쪽에 몰아넣는 분할(`(0,3,3,0)`처럼 A와 B가 사실상 안
    섞이고 각자 한쪽 절반을 통째로 차지)은 그 방향의 공정 gradient를 전혀 상쇄하지 못하고,
    양쪽에 고르게 나뉜 분할(`(1,2,2,1)`처럼 양쪽 다 A·B가 섞여 있음)일수록 gradient 상쇄
    효과가 커진다 — interdigitation의 근본 목적(§2.5) 그 자체다. 그래서 이 함수는 결과를
    **"얼마나 고르게 섞였는가"(`|a_left - a_right|` 오름차순) 순으로 정렬**해서 반환한다 —
    맨 앞이 matching 효과가 가장 좋은 후보다. 실제 folded cascode(M9=3, M10=3)에서 pptx가
    채택한 `(1,2,2,1)`이 정확히 이 정렬의 1순위 후보와 일치한다(§9 Test 9).

    반환: `count_a == count_b`이면 `[(a_left, a_right, b_left, b_right), ...]`를 매칭 효과
    내림차순(=|a_left-a_right| 오름차순)으로 정렬해 반환, 아니면 빈 리스트. 정렬은 matching
    효과 기준일 뿐 오일러 조건(§3)까지 보장하지는 않는다 — 앞쪽 후보부터 순서대로 실제 stack에
    적용해 오일러 조건도 만족하는지 확인해서 최종 채택할 것.
    """
    if count_a != count_b:
        return []
    splits = [(k, count_a - k, count_a - k, k) for k in range(count_a + 1)]
    splits.sort(key=lambda s: abs(s[0] - s[1]))
    return splits
