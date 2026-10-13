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
from gmid_engine.core import fp_of
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
    # [U17 ①-b 기준 변경, 설계 40 v1.9.1 §2.4.2 '블록이 선언한 입력만 읽으므로 입력 버전이 같으면 다시 계산하지 않는다' + D1,
    #  graph CONTRACT 10.1 'extras = (spec 판정 제약, N_S, declared, 사실, stale 기록, 선언 루프 끊는 넷)'] 재사용 키 = S1v 블록 입력 버전.
    # oracle (a)·(d): 블록이 읽는 입력(계수 예산·declared·ratified 사실·선언 끊는 넷)을 하나만 바꿔도 기준과 키가 달라야 한다(5개 서로 다름).
    # 옛 6번째 입력(supplies 전압값만 바꿈)은 아래 test 로 옮겼다 -- S1v 가 읽는 값을 바꾸지 않으므로 같은 키가 design 의 기대다.
    _, base = H.build(tmp_path, H.MILLER)
    _, budget = H.build(tmp_path, H.MILLER, count_budget=H.BIG_BUDGET + 1)
    _, declared = H.build(tmp_path, H.MILLER, declared=(("comp", (("M1", "M2"), ("M6",))),))
    fact = StructureFact("drive_kind", "out", "voltage", "T-1", ("out",))
    _, ratified = H.build(tmp_path, H.MILLER, structure=StructureFacts(facts=(fact,), findings=()))
    _, cuts = H.build(tmp_path, H.MILLER, declared_loop_cuts=("o1",))
    keys = [x.key for x in (base, budget, declared, ratified, cuts)]
    assert len(set(keys)) == len(keys) == 5


def test_supply_value_only_change_keeps_key_and_s1v_fields(tmp_path):
    # [U17 ①-b, 설계 40 v1.9.1 §2.4.2(재사용 = 블록 입력 버전 일치) + D1(graph/s1v 5필드, 옛 `S1v.key` 칸 폐기)]
    # oracle (a) 구성: 레일 넷 집합(vdd·gnd)은 그대로이고 전압값만 1.8 -> 3.3 V. S1v(뷰·교류접지·셀·L 동치류·기록)는 어느 넷이 레일인지로만
    # 정해지는 구조라(graph CONTRACT 10.2 '교류접지: 레일 ∪ ...') 다섯 필드 값이 같고, 그래서 블록 입력 버전(키)도 같아 재계산이 없다.
    _, base = H.build(tmp_path, H.MILLER, stem="v18")
    _, hv = H.build(tmp_path, H.MILLER, supplies={"vdd": 3.3, "gnd": 0.0}, stem="v33")
    for name in ("views", "l_classes", "findings", "declared", "applied_facts"):
        assert fp_of(getattr(base, name)) == fp_of(getattr(hv, name)), name
    assert hv.key == base.key


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


# ---------------------------------------------------------------- [U17 ①-d] `l_owner` 사실과 재사용 키(40 v1.6 §3.2-3)
# 40 §3.2-3: "같은 topology라도 사실이 다르면 S1이 다르다", "`l_classes.py`가 `structure_rule_fp` 대상이다: S1V_RULE_FILES에 이미 있다".
# l_owner 는 S1v(`l_classes.py`)가 소비하므로 그 사실의 지문은 S1v 재사용 키를 바꿔야 한다(같은 키면 이전 S1v 를 재사용해 주인 덮기가 사라진다).
# 사실 지문을 S1Key.facts_fp 에 넣는지(= S1 키)까지는 design 이 정하지 않는다(§3.2-3 파이프라인 3 은 dc_role 만 적는다) -- S1v 키로만 본다.

def test_l_owner_fact_changes_s1v_key(tmp_path):
    import jrules_hand as J
    _, plain = H.build(tmp_path, H.FOLDED)
    _, owned = H.build(tmp_path, H.FOLDED, structure=J.facts(("l_owner", '["M3","M4"]', "M4", "C-3t")))
    _, other = H.build(tmp_path, H.FOLDED, structure=J.facts(("l_owner", '["M3","M4"]', "M3", "C-3t")))
    assert len({plain.key, owned.key, other.key}) == 3


def test_l_classes_is_a_structure_rule_file():
    assert "l_classes.py" in S1V_RULE_FILES
