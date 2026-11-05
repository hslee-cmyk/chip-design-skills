# -*- coding: utf-8 -*-
"""core/requests.py -- 해석 요청 자료형(design §5). 요청은 방언을 모른다. 출력은 IR 넷·원소 이름의 식(Expr)이다.

이 card 몫: Condition, Op, Ac, 식 넷(NodeV, DiffV, BranchI, Ratio). Noise·Tran·Pz·OpSweep·Mc*·Tf 는 OP-4·OP-5 몫이라 없다.
`exc` = 여기 덮어쓰기 ((원소 이름, 칸, 값) 목록; 칸 ∈ dc, ac_mag).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Condition:
    temp_c: float
    corner: str


@dataclass(frozen=True)
class NodeV:
    net: str


@dataclass(frozen=True)
class DiffV:
    net_p: str
    net_n: str


@dataclass(frozen=True)
class BranchI:
    element: str


@dataclass(frozen=True)
class Ratio:
    num: object
    den: object


@dataclass(frozen=True)
class OpOutputs:
    devices: object          # 이름 튜플 또는 'all'
    nodes: tuple
    currents: tuple          # 전류를 읽을 전압원 원소 이름


@dataclass(frozen=True)
class Op:
    id: str
    cond: Condition
    exc: tuple = ()
    outputs: OpOutputs = OpOutputs("all", (), ())


@dataclass(frozen=True)
class Ac:
    id: str
    cond: Condition
    exc: tuple
    f_start: float | None
    f_stop: float | None
    points_per_decade: int | None
    f_list: tuple | None
    outputs: tuple


def expr_key(ex) -> str:
    """결과 FreqSeries.values 의 키."""
    k = type(ex).__name__
    if k == "NodeV":
        return f"v({ex.net})"
    if k == "DiffV":
        return f"v({ex.net_p})-v({ex.net_n})"
    if k == "BranchI":
        return f"i({ex.element})"
    if k == "Ratio":
        return f"({expr_key(ex.num)})/({expr_key(ex.den)})"
    raise TypeError(f"식 밖: {k}")
