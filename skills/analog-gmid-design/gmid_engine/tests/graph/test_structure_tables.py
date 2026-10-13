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
    # [U17 ①-b 기준 변경, 설계 40 v1.9.1 §2.4.8 'graph/s1v: views, l_classes, findings, declared, applied_facts'(D1, 옛 key 칸 없음),
    #  graph CONTRACT 10.1 'structure_tables(source)(필드를 읽는다 -- 옛 key 칸 없음)'] 표는 S1v 필드 값만 담는다.
    # oracle (a) 구성: 입력 차이가 S1v 필드 값을 바꾸는 쌍 -- b = CMFB 에서 소자 M9 이름만 M19 로(표에는 모든 소자 이름이 나타난다,
    # 위 test_tables_mention_views_cells_classes_and_records), c = 다른 회로(MILLER). 세 표 지문이 모두 다르다.
    _, a = H.build(tmp_path, H.CMFB)
    _, b = H.build(tmp_path, H.rename(H.CMFB, {}, {"M9": "M19"}, seed=3), stem="cmfb_m19")
    _, c = H.build(tmp_path, H.MILLER)
    assert '"M19"' in json.dumps(structure_tables(b)) and '"M19"' not in json.dumps(structure_tables(a))
    assert len({fp_of(structure_tables(x)) for x in (a, b, c)}) == 3


def test_tables_carry_no_reuse_key(tmp_path):
    # [U17 ①-b, 설계 40 v1.9.1 D1] 옛 표의 `key`(S1v 재사용 키) 칸은 없앴다 -- 블록 입력만 다르고 S1v 필드 값이 같은 두 입력은 같은 표다.
    # oracle (a) 구성: CMFB 의 CM 루프는 넷 cm 에서 끊긴다(위 test 의 뷰 id 'loop:M5:cm'). 같은 끊는 점을 선언(`declared_loop_cuts=("cm",)`)하면
    # 블록 입력(선언 끊는 넷)은 다르지만 뷰·셀·L 동치류·기록은 같다 -> 블록 입력 버전 다름, 표 지문 같음.
    _, a = H.build(tmp_path, H.CMFB, stem="nocut")
    _, b = H.build(tmp_path, H.CMFB, declared_loop_cuts=("cm",), stem="cut")
    assert a.key != b.key
    assert fp_of(structure_tables(a)) == fp_of(structure_tables(b))
    assert "key" not in structure_tables(a)


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
