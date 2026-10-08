"""graph/s1v_key.py -- `s1v_rule_fp()`·`S1V_RULE_FILES`·S1v 재사용 키(계약 10.1·10.3 불변량 1, S1v docstring `key`).

oracle (d): 설계 41 1절 파일 표(SP1 규칙 파일 -- views·ac_ground_view·signal_reach·cells·drive_kind·stage_bfs·blocks·pole_nodes·
loops·loop_classify·loop_cuts·polarity·buffer_bundles·output_direction·composite_blocks·declared_compare·s1v_build)는 규칙 지문
대상이어야 한다(`rule_coverage.py` 는 발동표 파일을 만들지 않기로 한 41 1.10 결정으로 없다).
oracle (a): 같은 입력이면 같은 키, 계수 예산·declared·ratified 사실·뷰 입력 중 하나라도 바뀌면 다른 키. 규칙 지문은 프로세스·
PYTHONHASHSEED 와 무관.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import gmid_engine.graph as graph_pkg
from gmid_engine.graph import S1V_RULE_FILES, StructureFact, StructureFacts, s1v_rule_fp

import s1v_hand as H

DESIGN_41_FILES = ("views.py", "ac_ground_view.py", "signal_reach.py", "cells.py", "drive_kind.py", "stage_bfs.py",
                   "blocks.py", "pole_nodes.py", "loops.py", "loop_classify.py", "loop_cuts.py", "polarity.py",
                   "buffer_bundles.py", "output_direction.py", "composite_blocks.py", "declared_compare.py", "s1v_build.py")


def test_rule_fp_is_stable_hex():
    a, b = s1v_rule_fp(), s1v_rule_fp()
    assert a == b
    assert re.fullmatch(r"[0-9a-f]{64}", a)


def test_rule_files_cover_design_table_and_exist():
    graph_dir = Path(graph_pkg.__file__).resolve().parent
    assert set(DESIGN_41_FILES) <= set(S1V_RULE_FILES)
    assert all((graph_dir / f).is_file() for f in S1V_RULE_FILES)
    assert list(S1V_RULE_FILES) == sorted(set(S1V_RULE_FILES))


def test_rule_fp_independent_of_hash_seed():
    skill = Path(__file__).resolve().parents[3]
    outs = set()
    for seed in ("0", "11", "123"):
        r = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]);"
                            "from gmid_engine.graph import s1v_rule_fp; print(s1v_rule_fp())", str(skill)],
                           env=dict(os.environ, PYTHONHASHSEED=seed), capture_output=True, text=True, check=True)
        outs.add(r.stdout.strip())
    assert len(outs) == 1 and re.fullmatch(r"[0-9a-f]{64}", outs.pop())


def test_key_same_for_same_inputs(tmp_path):
    _, a = H.build(tmp_path, H.MILLER, stem="a")
    _, b = H.build(tmp_path, H.MILLER, stem="b")
    assert a.key == b.key


def test_key_changes_with_each_input(tmp_path):
    _, base = H.build(tmp_path, H.MILLER)
    _, budget = H.build(tmp_path, H.MILLER, count_budget=H.BIG_BUDGET + 1)
    _, declared = H.build(tmp_path, H.MILLER, declared=(("comp", (("M1", "M2"), ("M6",))),))
    fact = StructureFact("drive_kind", "out", "voltage", "T-1", ("out",))
    _, ratified = H.build(tmp_path, H.MILLER, structure=StructureFacts(facts=(fact,), findings=()))
    _, cuts = H.build(tmp_path, H.MILLER, declared_loop_cuts=("o1",))
    supplies = H.build(tmp_path, H.MILLER, supplies={"vdd": 3.3, "gnd": 0.0})[1]
    keys = [x.key for x in (base, budget, declared, ratified, cuts, supplies)]
    assert len(set(keys)) == len(keys)
