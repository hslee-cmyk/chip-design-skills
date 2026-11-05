# -*- coding: utf-8 -*-
"""core/ir.py -- 회로 중간 표현(design §4.1). 넷리스트 텍스트를 중간 표현으로 쓰지 않는다.

IR 값은 SI 그대로다(단위 환산·병렬 배수 전달은 어댑터 방언 몫, design §10.6). 원소 종류는 필드(클래스)다.
테스트벤치 원소 이름은 코어가 `tb:<용도>:<대상>` 으로 만든다. 방언에서 쓸 수 있는 이름으로 바꾸는 것은 어댑터 몫이다.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Diffusion:
    ad: float
    as_: float
    pd: float
    ps: float


@dataclass(frozen=True)
class Lod:
    sa: float
    sb: float
    sd: float


@dataclass(frozen=True)
class Pulse:
    v1: float
    v2: float
    td: float
    tr: float
    tf: float
    pw: float
    per: float


@dataclass(frozen=True)
class Mos:
    name: str
    kind: str
    d: str
    g: str
    s: str
    b: str
    L: float
    finger_w: float
    n_fingers: int
    diffusion: Diffusion | None = None
    lod: Lod | None = None


@dataclass(frozen=True)
class Resistor:
    name: str
    a: str
    b: str
    value: float


@dataclass(frozen=True)
class Capacitor:
    name: str
    a: str
    b: str
    value: float


@dataclass(frozen=True)
class Inductor:
    name: str
    a: str
    b: str
    value: float


@dataclass(frozen=True)
class VSource:
    name: str
    p: str
    n: str
    dc: float
    ac_mag: float = 0.0
    ac_phase: float = 0.0
    tran: Pulse | None = None


@dataclass(frozen=True)
class ISource:
    name: str
    p: str
    n: str
    dc: float
    ac_mag: float = 0.0


@dataclass(frozen=True)
class Vcvs:
    name: str
    p: str
    n: str
    cp: str
    cn: str
    gain: float


@dataclass(frozen=True)
class Circuit:
    elements: tuple
    role: dict            # {원소 이름: 'circuit' | 'testbench'}
    meta: dict            # 방언이 모르는 부가 정보(예: {'ground': 기준 넷 이름}) -- 값 사본이 아니라 IR 해석에 필요한 이름만

    def by_name(self) -> dict:
        return {e.name: e for e in self.elements}


def element_nets(e) -> tuple:
    """원소가 닿는 넷 이름들."""
    k = type(e).__name__
    if k == "Mos":
        return (e.d, e.g, e.s, e.b)
    if k in ("Resistor", "Capacitor", "Inductor"):
        return (e.a, e.b)
    if k in ("VSource", "ISource"):
        return (e.p, e.n)
    if k == "Vcvs":
        return (e.p, e.n, e.cp, e.cn)
    raise TypeError(f"IR 원소 밖: {k}")
