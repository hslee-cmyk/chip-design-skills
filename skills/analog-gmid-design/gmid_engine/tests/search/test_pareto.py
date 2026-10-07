"""CONTRACT 3.1 `nondominated` + 불변식 I-7. 기대값: 손 예 + conftest `ref_nondominated`(계약 문장의 독립 구현)."""
import random

import pytest

from gmid_engine.search import ParetoResult, nondominated

from .conftest import ref_nondominated


def ids(points, idx):
    return tuple(points[i][0] for i in idx)


def pairs(points, prs):
    return {(points[a][0], points[b][0]) for a, b in prs}


def test_axis_count_mismatch_rejected():
    with pytest.raises(ValueError):
        nondominated((("a", (1.0, 2.0), 0.0),), (0.1,))
    with pytest.raises(ValueError):
        nondominated((("a", (1.0,), 0.0), ("b", (1.0, 2.0), 0.0)), (0.1,))


def test_hand_example_fold_and_dominate():
    pts = (("a", (1.0, 5.0), 0.0), ("b", (2.0, 4.0), 0.0), ("c", (3.0, 6.0), 0.0), ("d", (1.05, 5.0), 1.0))
    r = nondominated(pts, (0.1, 0.1))
    assert isinstance(r, ParetoResult)
    # 순서 a(1.0) d(1.05) b c: d 는 a 와 모든 축 동률 -> 접힘, c 는 먼저 남은 a 가 지배.
    assert r.kept == (0, 1)
    assert r.folded == ((3, 0),)
    assert r.dominated == ((2, 0),)


def test_new_point_evicts_dominated_kept():
    pts = (("p", (1.0, 9.0), 0.0), ("q", (1.04, 3.0), 0.0))
    r = nondominated(pts, (0.1, 0.1))
    # q: 첫 축 동률(폭 0.1), 둘째 축 나음 -> p 를 지배 -> p 를 dominated 에 (p, q) 로 빼고 q 남김.
    assert ids(pts, r.kept) == ("q",)
    assert r.dominated == ((0, 1),)
    assert r.folded == ()


def test_slack_then_name_order_picks_fold_representative():
    # 모든 축 동률: 처리 순서 = (첫 축 값, slack 내림, id) -> slack 큰 점(이름 앞선 b)이 남는다.
    pts = (("a", (1.0, 1.0), 0.0), ("b", (1.0, 1.0), 5.0), ("c", (1.0, 1.0), 5.0))
    r = nondominated(pts, (0.0, 0.0))
    assert ids(pts, r.kept) == ("b",)
    assert pairs(pts, r.folded) == {("a", "b"), ("c", "b")}


def test_callable_tie_width():
    res = {"a": 0.5, "b": 0.01, "c": 0.01}

    def wp(p, q):
        return max(res[p], res[q])
    pts = (("a", (1.0, 3.0), 0.0), ("b", (1.4, 3.0), 0.0), ("c", (1.6, 3.0), 0.0))
    r = nondominated(pts, (wp, 0.0))
    # a-b: |0.4| <= 0.5 동률, 둘째 축 동률 -> b 접힘(a 에). a-c: |0.6| > 0.5 -> a 가 c 지배.
    assert ids(pts, r.kept) == ("a",)
    assert pairs(pts, r.folded) == {("b", "a")}
    assert pairs(pts, r.dominated) == {("c", "a")}
    assert (r.kept, r.folded, r.dominated) == ref_nondominated(pts, (wp, 0.0))


def _random_points(rng, n, dims=2):
    out = []
    for i in range(n):
        out.append(("p%03d" % i, tuple(round(rng.uniform(0, 10), 2) for _ in range(dims)), round(rng.uniform(0, 3), 1)))
    return tuple(out)


@pytest.mark.parametrize("seed", range(8))
def test_matches_reference_and_invariants(seed):
    rng = random.Random(seed)
    pts = _random_points(rng, 40)
    ties = (0.3, 0.2)
    r = nondominated(pts, ties)
    assert (r.kept, r.folded, r.dominated) == ref_nondominated(pts, ties)
    # I-7: kept 안 두 점은 서로 지배하지 않고 모든 축 동률도 아니다.
    for i in r.kept:
        for j in r.kept:
            if i == j:
                continue
            pi, pj = pts[i][1], pts[j][1]
            tied = all(abs(a - b) <= t for a, b, t in zip(pi, pj, ties))
            dom = all(a <= b + t for a, b, t in zip(pi, pj, ties)) and any(a < b - t for a, b, t in zip(pi, pj, ties))
            assert not tied and not dom
    # 모든 점이 kept / folded / dominated 중 정확히 한 곳.
    placed = list(r.kept) + [a for a, _ in r.folded] + [a for a, _ in r.dominated]
    assert sorted(placed) == list(range(len(pts)))


@pytest.mark.parametrize("seed", range(4))
def test_permutation_invariant(seed):
    rng = random.Random(100 + seed)
    pts = _random_points(rng, 30)
    ties = (0.25, 0.25)
    base = nondominated(pts, ties)
    for _ in range(3):
        perm = list(pts)
        rng.shuffle(perm)
        perm = tuple(perm)
        r = nondominated(perm, ties)
        assert ids(perm, r.kept) == ids(pts, base.kept)
        assert pairs(perm, r.folded) == pairs(pts, base.folded)
        assert pairs(perm, r.dominated) == pairs(pts, base.dominated)


def test_three_axes():
    pts = (("a", (1.0, 1.0, 5.0), 0.0), ("b", (1.0, 1.0, 4.0), 0.0), ("c", (0.5, 2.0, 9.0), 0.0))
    r = nondominated(pts, (0.0, 0.0, 0.0))
    assert set(ids(pts, r.kept)) == {"b", "c"}
    assert pairs(pts, r.dominated) == {("a", "b")}
