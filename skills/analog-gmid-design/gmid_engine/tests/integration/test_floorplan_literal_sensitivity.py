"""CONTRACT(layout) 4.17 복사 floorplan 본문 리터럴의 A_L 민감도 (Q8 (ix)) -- test 화.

방법(계약 그대로): `floorplan_pack.py` 의 면적 관련 리터럴을 하나씩 ±1 단계(정수 ±1, 소수 끝자리 ±1, 1e-9 는 x10·/10) 바꾼
임시 모듈(저장소 밖, AST 변형 후 exec)로 `floorplan.floorplan_of` 가 쓰는 복사 함수를 바꿔 끼우고 `outline_area_m2` 를 원본과 비교한다.
대상 10 리터럴 x 2 = 20 변경: `pack_floorplan` 0.3·2.2·40·2.0, `pack_floorplan_grouped` 2.0·40, `skyline_pack_best_width` 60·3,
`pack_to_height` 60, `skyline_pack` 1e-9. 판정: ΔA_L 이 격자 한 칸(grid^2) 미만. 양성 대조: 큰 변경(2.2 -> 0.1)은 A_L 을 바꾼다
(계측이 실제로 걸린다는 증거). 입력은 계약 4.17 의 PDK 길이·격자, 무작위 seed 1~3(실행 시간 때문에 계약의 7 입력 중 일부 크기).
배치(규칙 H): 원본 파일과 1:1 이 아닌 교차 관심사라 `tests/integration/`.
"""
from __future__ import annotations

import ast
import importlib.util
import random
import sys
from pathlib import Path

import pytest

from gmid_engine.layout import LayoutPdk
from gmid_engine.layout import floorplan as floorplan_mod
from gmid_engine.layout import floorplan_pack
from gmid_engine.layout.contract_input import PDK_RULE_QUANTITIES
from gmid_engine.layout.contract_output import RowLayout

GRID = 5e-9
TARGETS = (("pack_floorplan", 0.3), ("pack_floorplan", 2.2), ("pack_floorplan", 40), ("pack_floorplan", 2.0),
           ("pack_floorplan_grouped", 2.0), ("pack_floorplan_grouped", 40), ("skyline_pack_best_width", 60),
           ("skyline_pack_best_width", 3), ("pack_to_height", 60), ("skyline_pack", 1e-9))


def _steps(v):
    if v == 1e-9:
        return (1e-8, 1e-10)
    if isinstance(v, int):
        return (v - 1, v + 1)
    s = repr(v)
    q = len(s.split(".")[1]) if "." in s else 0
    d = 10.0 ** (-q)
    return (round(v - d, q), round(v + d, q))


SRC = Path(floorplan_pack.__file__)


def _mutated_module(func, value, new, tag):
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    hit = 0
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func:
            # 규칙 D 가 허용하는 첨자·슬라이스 안 숫자는 manifest 리터럴이 아니다(1.1) -- 바꾸지 않는다
            in_subscript = {id(c) for s in ast.walk(node) if isinstance(s, ast.Subscript) for c in ast.walk(s.slice)}
            for sub in ast.walk(node):
                if id(sub) in in_subscript:
                    continue
                if isinstance(sub, ast.Constant) and type(sub.value) is type(value) and sub.value == value:
                    sub.value = new
                    hit += 1
    assert hit >= 1, "%s 안에 리터럴 %r 없음" % (func, value)
    name = "gmid_engine.layout._fp_literal_mut_%s" % tag
    spec = importlib.util.spec_from_loader(name, loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "gmid_engine.layout"
    sys.modules[name] = mod
    try:
        exec(compile(ast.fix_missing_locations(tree), str(SRC) + "<mut>", "exec"), mod.__dict__)
    finally:
        sys.modules.pop(name, None)
    return mod


def _patch(monkeypatch, mod):
    n = 0
    for attr, obj in list(vars(floorplan_mod).items()):
        if callable(obj) and getattr(floorplan_pack, attr, None) is obj and hasattr(mod, attr):
            monkeypatch.setattr(floorplan_mod, attr, getattr(mod, attr))
            n += 1
    assert n >= 1, "floorplan 이 floorplan_pack 함수를 이름으로 쓰지 않는다 -- 계측 불가"


def _pdk():
    return LayoutPdk(GRID, (("nmos", (100,)),), 0.0, 0.27e-6, 0.15e-6, 0.17e-6, 1.27e-6,
                     tuple((q, "R." + q) for q in PDK_RULE_QUANTITIES), "fp")


def _inputs():
    out = []
    for seed, n_rows, n_groups in ((1, 6, 4), (2, 12, 4), (3, 20, 8)):
        rnd = random.Random(seed)
        rows, bodies = [], {}
        for g in range(n_groups):
            bodies["g%d" % g] = "sub" if g % 2 == 0 else "nw"
        for i in range(n_rows):
            grp = "g%d" % rnd.randrange(n_groups)
            fw = rnd.choice((100, 200, 336, 600)) * GRID
            nf = rnd.randint(1, 12)
            width = nf * rnd.choice((0.15e-6, 0.5e-6, 1e-6, 1.5e-6, 4e-6))      # 행 폭 = nf x L (LUT L 앵커 범위)
            seq = ("M%d" % i,) * nf
            nodes = tuple("a" if j % 2 == 0 else "b" for j in range(nf + 1))
            rows.append(RowLayout("%s/r%02d" % (grp, i), grp, "nmos", round(fw / GRID), fw, width, (("M%d" % i, nf),), seq,
                                  nodes, ((seq, nodes),), "euler", 0, 1, True, None, False))
        out.append((tuple(rows), bodies))
    return out


INPUTS = _inputs()


@pytest.fixture(scope="module")
def base_areas():
    return [floorplan_mod.floorplan_of(r, b, _pdk()).outline_area_m2 for r, b in INPUTS]


@pytest.mark.parametrize("func, value", TARGETS)
def test_one_step_literal_change_keeps_area(monkeypatch, base_areas, func, value):
    for k, new in enumerate(_steps(value)):
        mod = _mutated_module(func, value, new, "%s_%d" % (func, k))
        with monkeypatch.context() as m:
            _patch(m, mod)
            for (rows, bodies), a0 in zip(INPUTS, base_areas):
                a1 = floorplan_mod.floorplan_of(rows, bodies, _pdk()).outline_area_m2
                assert abs(a1 - a0) < GRID * GRID, "%s %r->%r: A_L %g -> %g" % (func, value, new, a0, a1)


def test_large_change_is_detected(monkeypatch, base_areas):
    # 양성 대조: H 스윕 상한 2.2 -> 0.1 은 면적을 바꾼다(계약 실측 +28 %) -- 바꿔 끼우기가 실제로 걸린다
    mod = _mutated_module("pack_floorplan", 2.2, 0.1, "control")
    changed = 0
    with monkeypatch.context() as m:
        _patch(m, mod)
        for (rows, bodies), a0 in zip(INPUTS, base_areas):
            a1 = floorplan_mod.floorplan_of(rows, bodies, _pdk()).outline_area_m2
            changed += abs(a1 - a0) >= GRID * GRID
    assert changed >= 1
