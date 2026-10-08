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

import pytest

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


# ---------------------------------------------------------------- [U1b] 40 3.2-3 rule_hash = structure_rule_fp()
import shutil  # noqa: E402

from gmid_engine.graph import structure_rule_fp  # noqa: E402

# 40 3.2-3: 대상 = S1V_RULE_FILES ∪ {composite_diode.py, dc_roles.py, gs_groups.py, matching_groups.py, feedforward_cells.py,
# loop_roles.py} -- 사실이 대조하거나 덮어쓰는 값을 만드는 graph 파일 전부
STRUCTURE_EXTRA = ("composite_diode.py", "dc_roles.py", "gs_groups.py", "matching_groups.py", "feedforward_cells.py", "loop_roles.py")

_FP_SCRIPT = ("import sys; sys.path.insert(0, sys.argv[1]);"
              "from gmid_engine.graph import s1v_rule_fp, structure_rule_fp; print(s1v_rule_fp(), structure_rule_fp())")


def _fps(root):
    r = subprocess.run([sys.executable, "-c", _FP_SCRIPT, str(root)], capture_output=True, text=True, check=True,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    return tuple(r.stdout.split())


def test_structure_rule_fp_is_stable_hex_and_differs_from_s1v():
    a, b = structure_rule_fp(), structure_rule_fp()
    assert a == b and re.fullmatch(r"[0-9a-f]{64}", a)
    assert a != s1v_rule_fp()


@pytest.mark.parametrize("target", STRUCTURE_EXTRA)
def test_structure_rule_fp_tracks_s1_side_consumer_files(tmp_path, target):
    # 패키지 사본(tmp)에서 파일 하나에 주석 한 줄을 더하면 structure_rule_fp 가 바뀐다(작업 트리 엔진 파일은 건드리지 않는다).
    # S1V_RULE_FILES 밖 파일이면 s1v_rule_fp 는 그대로다 -- 그래서 as-built s1v_rule_fp 로는 S1 쪽 변경 stale 을 못 잡았다(40 3.2-3)
    graph_dir = Path(graph_pkg.__file__).resolve().parent
    dst = tmp_path / "pkg"
    shutil.copytree(graph_dir.parent, dst / "gmid_engine", ignore=shutil.ignore_patterns("tests", "__pycache__", "*.pyc"))
    s1v_before, st_before = _fps(dst)
    assert (s1v_before, st_before) == (s1v_rule_fp(), structure_rule_fp())
    f = dst / "gmid_engine" / "graph" / target
    f.write_bytes(f.read_bytes() + b"\n# structure rule change marker\n")
    s1v_after, st_after = _fps(dst)
    assert st_after != st_before
    assert (s1v_after == s1v_before) == (target not in S1V_RULE_FILES)
