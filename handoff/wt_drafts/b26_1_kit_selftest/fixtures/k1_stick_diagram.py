"""out_check_test 픽스처 -- K1 stick_diagram.py 대역(합성). 경로 노드 = range(i + 1, ...)의 1."""


def find_differential_pair_candidates(xs):
    out = []
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)):
            out.append((i, j))
    return out


def other(x):
    return x + 2
