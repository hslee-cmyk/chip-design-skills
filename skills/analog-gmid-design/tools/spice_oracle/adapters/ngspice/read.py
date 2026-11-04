# -*- coding: utf-8 -*-
"""adapters/ngspice/read.py -- ngspice 로그·데이터 파일 -> 정규화 결과 (design §6, card 20261104-op23).

내부 벡터 이름 대응(`@m.<인스턴스>.<내부 소자>[<파라미터>]`), 극성 정규화(`signed_id`), 인스턴스 기하 보고 원값, wrdata 열 읽기를 한다.
극성 정규화는 어댑터 몫이고 `signed_id` 정의는 이 파일 한 곳이다: ngspice BSIM4 의 @id 는 소스/드레인 역할이 뒤바뀌어도 양수(채널 전류 크기)이고
@vds 는 선언 단자 방향 부호를 유지하므로 ID = @id x sign(@vds)(역방향 전도 = 음수, 선언 단자 방향 부호).
기하 보고값은 **원값 그대로** 싣는다(단위를 되돌리지 않는다 -- 같은 규칙을 두 번 적용해 전달 오류가 상쇄되는 것을 막는다, design §6).
"""
from __future__ import annotations

import os
import re

import numpy as np

from adapters.ngspice import dialect
from core.requests import expr_key
from core.results import FreqSeries, OpTable

_NUM = r"([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)"


def _grab(text, expr):
    m = re.search(r"^\s*" + re.escape(expr) + r"\s*=\s*" + _NUM, text, re.I | re.M)
    return float(m.group(1)) if m else None


def signed_id(op_id, op_vds):
    """크기 규칙 ID(부호 포함) = @id x sign(@vds). @vds = 0 이면 0, 둘 중 하나가 없으면 None."""
    if op_id is None or op_vds is None:
        return None
    return op_id * (1.0 if op_vds > 0 else (-1.0 if op_vds < 0 else 0.0))


def _slice(log, rid):
    a, b = log.find(dialect.op_marker(rid, False)), log.find(dialect.op_marker(rid, True))
    return log[a:b] if 0 <= a < b else ""


def parse_op(log, req, circuit, name_map, descriptor, resolution) -> OpTable:
    text = _slice(log, req.id)
    info = dialect._mos_probe_info(circuit, descriptor, name_map)
    names = list(info) if req.outputs.devices == "all" else list(req.outputs.devices)
    devices, geom = {}, {}
    for n in names:
        inst, inner, params = info[n]
        row = {p: _grab(text, dialect.probe(inst, inner, p)) for p in params}
        if "id" in row:
            row["id"] = signed_id(row["id"], row.get("vds"))
        devices[n] = row
        geom[n] = {f: _grab(text, dialect.probe(inst, inner, col)) for f, col in dialect.GEOMETRY_FIELDS.items()}
    nodes = {n: _grab(text, f"v({n.lower()})") for n in req.outputs.nodes}
    currents = {c: _grab(text, f"i({name_map[c].lower()})") for c in req.outputs.currents}
    return OpTable(devices=devices, nodes=nodes, currents=currents, resolution=resolution, error=None,
                   instance_geometry_reported=geom)


def _cols(path):
    """wrdata(wr_singlescale) 파일 -> (주파수 배열, [복소 열 배열 목록]) 또는 None."""
    if not path or not os.path.exists(path):
        return None
    fr, rows = [], []
    with open(path) as f:
        for line in f:
            try:
                vals = [float(x) for x in line.split()]
            except ValueError:
                continue
            if len(vals) < 3:
                continue
            fr.append(vals[0])
            rows.append([complex(vals[i], vals[i + 1]) for i in range(1, len(vals) - 1, 2)])
    if not fr:
        return None
    arr = np.array(rows, dtype=complex)
    return np.array(fr), [arr[:, k] for k in range(arr.shape[1])]


def min_digits(path):
    """데이터 파일에 찍힌 가수 유효숫자 수의 최솟값(없으면 None)."""
    if not path or not os.path.exists(path):
        return None
    d_min = None
    with open(path) as f:
        for line in f:
            for tok in line.split():
                mant = re.split(r"[eE]", tok.lstrip("+-"), maxsplit=1)[0]
                if not re.fullmatch(r"[0-9]+\.?[0-9]*|\.[0-9]+", mant):
                    continue
                digits = mant.replace(".", "").lstrip("0")
                if digits and (d_min is None or len(digits) < d_min):
                    d_min = len(digits)
    return d_min


def data_rel(path, declared_digits):
    """데이터 파일의 상대 분해능 u = 0.5 * 10^(1 - d). d = 보정값 선언 자릿수와 파일에서 읽은 최솟값 가운데 작은 쪽(거친 쪽)."""
    seen = min_digits(path)
    d = declared_digits if seen is None else min(declared_digits, seen)
    return 0.5 * 10.0 ** (1 - d)


def parse_ac(path, req, resolution_for) -> FreqSeries | None:
    c = _cols(path)
    if c is None:
        return None
    f, cols = c
    if len(cols) != len(req.outputs):
        return None
    return FreqSeries(f=f, values={expr_key(ex): col for ex, col in zip(req.outputs, cols)}, resolution=resolution_for(path), error=None)
