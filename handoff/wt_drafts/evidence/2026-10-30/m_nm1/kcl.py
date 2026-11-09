# -*- coding: utf-8 -*-
"""DC 전류 기저: KCL 행렬(연결만)에서 열 순서에 따라 독립(pivot) 열 / 자유 열을 가른다."""
from fractions import Fraction


def driven_nets(M):
    """KCL 행을 세우지 않는 넷: 레일, bias 입력, 입력 포트(이상 전압원이 구동)."""
    s = set(M.rails) | set(M.bias)
    for n, r in M.ports.items():
        if r.startswith("differential_input") or r.startswith("single_ended_input"):
            s.add(n)
    return s


def columns(M):
    """가지 전류 열: MOS 채널(d->s), 저항(t0->t1), 값 미선언 이상 전류원. 게이트·커패시터 0, 값 선언 전류원은 상수라 열 아님."""
    cols = {}
    for k, m in M.mos.items():
        cols["D:" + k] = (m["d"], m["s"])
    for k, p in M.pas.items():
        if p["kind"] == "resistor":
            cols["D:" + k] = (p["t"][0], p["t"][1])
    for k, p in M.isrc.items():
        if not p["decl"]:
            cols["D:" + k] = (p["t"][0], p["t"][1])
    return cols


def vectors(M):
    drv = driven_nets(M)
    cols = columns(M)
    vec = {}
    for c, (a, b) in cols.items():
        v = {}
        if a != b:
            if a not in drv: v[a] = v.get(a, 0) + 1     # 가지 전류가 a 에서 나감
            if b not in drv: v[b] = v.get(b, 0) - 1     # b 로 들어옴
        vec[c] = v
    return vec


def free_set(vec, order):
    """order 순으로 훑어 앞 열들과 선형독립이면 pivot(종속 변수), 아니면 자유 열. 반환 (자유 열 집합, pivot 집합)."""
    basis = {}   # pivot row -> reduced vector(dict, 해당 row 계수 1)
    free, piv = set(), set()
    for c in order:
        v = {r: Fraction(x) for r, x in vec[c].items() if x}
        # 기약
        changed = True
        while v and changed:
            changed = False
            for r in list(v):
                if r in basis and r in v:
                    f = v[r]
                    for rr, xx in basis[r].items():
                        nv = v.get(rr, 0) - f * xx
                        if nv: v[rr] = nv
                        else: v.pop(rr, None)
                    changed = True
                    break
        if v:
            r0 = sorted(v)[0]
            f = v[r0]
            basis[r0] = {rr: xx / f for rr, xx in v.items()}
            piv.add(c)
        else:
            free.add(c)
    return free, piv
