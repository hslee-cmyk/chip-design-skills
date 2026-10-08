"""graph/structure_tables.py -- `structure_tables(s1v) -> dict`(계약 10.1, 불변량 1, pipeline CONTRACT 2절 `tables`).

oracle (a): JSON 직렬화 가능(왕복 동일), 같은 입력이면 `fp_of(structure_tables(s1v))` 가 프로세스·PYTHONHASHSEED·netlist 순서와 무관하게
같고, 입력이 다르면 다르다. 표는 뷰·셀·L 동치류·기록을 담는다 -- 키 이름은 계약에 없어 내용(뷰 id·소자 이름·기록 코드)이 직렬화
문자열에 나타나는지로만 본다.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from gmid_engine.core import fp_of
from gmid_engine.graph import structure_tables

import s1v_hand as H

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[2]


JSON_SCALARS = (str, int, float, bool, type(None))


def _non_json(node, path="$"):
    """JSON 값 형식(dict[str] · list · 스칼라)이 아닌 자리의 경로 목록 -- tuple·set·dataclass 등은 왕복에서 형이 바뀐다."""
    if isinstance(node, dict):
        bad = [path + " key " + repr(k) for k in node if not isinstance(k, str)]
        return bad + [b for k, v in node.items() for b in _non_json(v, path + "." + str(k))]
    if isinstance(node, list):
        return [b for i, v in enumerate(node) for b in _non_json(v, "%s[%d]" % (path, i))]
    return [] if isinstance(node, JSON_SCALARS) else [path + " " + type(node).__name__]


def test_tables_are_plain_json_values(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    tables = structure_tables(s1v)
    assert isinstance(tables, dict)
    assert _non_json(tables) == []                      # 그래서 json.dumps -> json.loads 왕복이 같은 값이다


def test_tables_mention_views_cells_classes_and_records(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    text = json.dumps(structure_tables(s1v))
    for token in ("transfer:0", "loop:M5:cm", "cm_loop_unconstrained", "loop_view"):
        assert token in text
    for dev in H.json_mos(H.CMFB):
        assert '"%s"' % dev in text


def test_same_input_same_fingerprint_and_shuffle_invariant(tmp_path):
    _, a = H.build(tmp_path, H.CMFB, stem="a")
    _, b = H.build(tmp_path, H.CMFB, stem="b")
    shuffled = H.rename(H.CMFB, {}, {}, seed=7)          # 이름 그대로, netlist·수동소자 순서만 섞음
    _, c = H.build(tmp_path, shuffled, stem="c")
    fps = {fp_of(structure_tables(x)) for x in (a, b, c)}
    assert len(fps) == 1


def test_different_input_different_fingerprint(tmp_path):
    _, a = H.build(tmp_path, H.CMFB)
    _, b = H.build(tmp_path, H.CMFB, declared_loop_cuts=("cm",))
    _, c = H.build(tmp_path, H.MILLER)
    assert len({fp_of(structure_tables(x)) for x in (a, b, c)}) == 3


SCRIPT = r"""
import sys
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
import s1v_hand as H
from gmid_engine.core import fp_of
from gmid_engine.graph import structure_tables
_, s1v = H.build(sys.argv[3], H.CMFB)
print(fp_of(structure_tables(s1v)))
"""


def test_fingerprint_independent_of_hash_seed(tmp_path):
    outs = set()
    for seed in ("1", "2", "3"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        r = subprocess.run([sys.executable, "-c", SCRIPT, str(SKILL), str(HERE), str(tmp_path)], env=env,
                           capture_output=True, text=True, check=True)
        outs.add(r.stdout.strip())
    _, here = H.build(tmp_path, H.CMFB)
    assert outs == {fp_of(structure_tables(here))}
