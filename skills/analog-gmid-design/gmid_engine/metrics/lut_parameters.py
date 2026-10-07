"""LUT 에서 온 MOS 소신호 파라미터와 그 불확실성 (계획 NFR-5 '격자 분해능', search S-19, metrics CONTRACT 9.1).

진입점: `lut_parameters(circuit, rel_tol) -> ParameterSet`.

* LUT 파라미터 = `LUT_PARAMETERS`(gm, gmb, gds, cgs, cgd, cgb) -- `ss_dev` 가 LUT 조회로 만든 값(gm = ID·(gm/ID) 의 gm/ID,
  gds·gmb 열, `caps` 의 CGS·CGD·CGB). cdb·csb 는 PDK 접합 파라미터 폐형식(DEC-91, ngspice 대조 2.3e-11)이라 LUT 조회 불확실성이
  없고, 수동소자 값은 선언·θ 값 그대로라 넣지 않는다.
* Δp = ε_d·|p|: ε_d = MOS d 의 LUT 상대 불확실성(`SsDevice.lut_rel_tol` = (gm/ID)·tol_V(id_equivalent), CONTRACT 9.1).
  용량은 부호 있는 값이라 크기 |p| 를 쓴다. 값이 0 인 파라미터는 넣지 않는다(Δp = 0 -- 그 스탬프 노드가 계에 없을 수도 있다).
* 단위 스탬프: 파라미터 p 하나만 1 로 둔 `MosSmallSignal` 을 `mos_stamps` 에 넣은 항목(스탬프 식의 정본 하나 -- 새로 쓰지 않는다).
  ∂A/∂p = 그 항목(G 항목은 컨덕턴스, C 항목은 용량 -- 계의 ω 가 jω 를 곱한다).
* ε 가 None(그 MOS 의 tol_V 셀 미정)이면 `undetermined` 에 순번을 적는다 -- 분해능을 정하지 않는다(미정을 0 으로 두지 않음).
"""
import dataclasses

import numpy

from .mna_types import ParameterSet
from .records import MosSmallSignal, SmallSignalCircuit
from .stamp_mos import mos_stamps

LUT_PARAMETERS = ("gm", "gmb", "gds", "cgs", "cgd", "cgb")
_VALUE_FIELDS = ("gm", "gmb", "gds", "cgs", "cgd", "cgb", "cdb", "csb")     # MosSmallSignal 값 필드(단위 스탬프에서 0 으로 둔다)


def _rel_tol(value, index):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("lut_parameters: rel_tol[%d] 는 실수 또는 None 이어야 한다: %r" % (index, value))
    value = float(value)
    if not numpy.isfinite(value) or value < 0:
        raise ValueError("lut_parameters: rel_tol[%d] 는 0 이상 유한해야 한다: %r" % (index, value))
    return value


def lut_parameters(circuit, rel_tol):
    """`SmallSignalCircuit`, MOS 순서의 상대 불확실성 tuple(원소 0 이상 유한 실수 또는 None) -> `ParameterSet`."""
    if not isinstance(circuit, SmallSignalCircuit):
        raise TypeError("lut_parameters: circuit 는 SmallSignalCircuit 이어야 한다")
    if not isinstance(rel_tol, tuple) or len(rel_tol) != len(circuit.mos):
        raise TypeError("lut_parameters: rel_tol 은 circuit.mos 와 같은 길이의 tuple 이어야 한다")
    tols = tuple(_rel_tol(v, i) for i, v in enumerate(rel_tol))
    params, delta, rows, cols, values, capacitive, owner = [], [], [], [], [], [], []
    for d, mos in enumerate(circuit.mos):
        if not isinstance(mos, MosSmallSignal):
            raise TypeError("lut_parameters: circuit.mos 원소는 MosSmallSignal 이어야 한다")
        for name in LUT_PARAMETERS:
            value = getattr(mos, name)
            if not value:
                continue
            unit = {field: (1.0 if field == name else 0.0) for field in _VALUE_FIELDS}
            stamps = mos_stamps(dataclasses.replace(mos, **unit))
            p = len(params)
            params.append((d, name))
            delta.append(abs(value) * (tols[d] or 0.0))
            for entries, is_cap in ((stamps.g, False), (stamps.c, True)):
                for row, col, amount in entries:
                    rows.append(row)
                    cols.append(col)
                    values.append(amount)
                    capacitive.append(is_cap)
                    owner.append(p)
    return ParameterSet(
        params=tuple(params), delta=numpy.array(delta, dtype=float), rel_tol=tols,
        rows=numpy.array(rows, dtype=int), cols=numpy.array(cols, dtype=int), values=numpy.array(values, dtype=float),
        capacitive=numpy.array(capacitive, dtype=bool), owner=numpy.array(owner, dtype=int),
        undetermined=tuple(i for i, v in enumerate(tols) if v is None),
    )
