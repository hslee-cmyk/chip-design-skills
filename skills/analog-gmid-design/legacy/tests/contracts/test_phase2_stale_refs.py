"""Phase 2에서 지우거나 옮긴 엔진 이름을 skill 문서가 표시 없이 안내하지 않는다(20260930-p10-df23-inventory 계약 5).

spec card `docs/02-design/specs/20260930-p10-df23-inventory.spec.md` 계약 5(문서 백로그 B22 (b), 전 범위)를 판정한다.
판정 대상 문서 D = `skills/analog-gmid-design/references/**/*.md`, `skills/analog-gmid-design/SKILL.md`,
`skills/analog-gmid-design/skill-validation-prompt.md`. 이름 집합 N과 삭제/이동 분류는 card가 Phase 2 커밋(P5 2a123ba·
P5b 6612902·P6 1c5b920)의 사실로 **고정한 데이터**다 -- 엔진 소스를 읽지 않는다(분류가 base 사실과 같은지는 계약 7 (f)
auditor 측정). 이름은 문자열 상수로만 든다(import·호출·딕셔너리 값 아님 -- GONE 스캔·이동 소비자 검사와 겹치지 않게).

N의 이름 n이 D의 한 줄에 나오면(식별자 경계 대조, 호출형 `.fT(`·`.junction_cap(`은 부분 문자열):
* 이동 이름 -> 그 줄에 `Phase 2에서`와 그 이름의 `tests/tools/<모듈>.py`가 함께 있다.
* 삭제 이름 -> 그 줄에 `Phase 2에서 삭제`가 있다.

oracle 대조(계획 N3.12.3):

* test_docs_mark_phase2_removed_names -- (d) spec card 계약 5의 이름 집합 N·삭제/이동 분류·표시 문구(Phase 2 삭제·이동
  커밋의 사실로 card가 고정). 문서 작성자의 판단을 기대값으로 쓰지 않는다.
* test_p10_doc_judge_rejects_* / test_p10_doc_judge_accepts_* / test_p10_doc_judge_ignores_* -- (a) 판정기 자기 점검: card
  '거부해야 할 입력'의 합성 문서 줄(표시 없는 표 행, 코드 블록 import 줄, 새 경로 없는 이동 표시, 식별자 일부만 겹치는 이름)을
  손으로 만들어 거부·통과·대상 아님이 구성으로 정해진다.
"""
import pathlib
import re

import pytest

_CONTRACTS_DIR = pathlib.Path(__file__).resolve().parent
# contracts -> tests -> assets -> analog-gmid-design -> skills -> 저장소 루트
_REPO_ROOT = _CONTRACTS_DIR.parents[4]
_P10_SKILL = _REPO_ROOT / "skills" / "analog-gmid-design"

# oracle (d) card 계약 5: Phase 2에서 삭제된 이름(식별자 경계 대조).
_P10_DELETED_IDENTS = (
    "converge_with_parasitics", "slew_rate", "render_stick_diagram", "suggest_headroom_stack_groups",
    "_cmrr_telescopic_class_ab", "_cmrr_telescopic_class_ab_cmfb", "_psrr_telescopic_class_ab",
    "_psrr_telescopic_class_ab_cmfb", "_cmfb_amp_gain_diode_load", "_load_telescopic_topology_cached",
    "_telescopic_class_ab_open_loop_response", "_telescopic_open_loop_device_names",
    "_telescopic_class_ab_open_loop_gains", "_TELESCOPIC_FIXED_BASE",
    "telescopic_class_ab", "telescopic_class_ab_cmfb",
)
# oracle (d) card 계약 5: 삭제된 메서드의 호출형(부분 문자열 대조).
_P10_DELETED_CALLS = (".fT(", ".junction_cap(")
# oracle (d) card 계약 5: 이동 이름과 새 위치(`tests/tools/<모듈>.py`).
_P10_MOVED = (
    ("find_interleaved_symmetric_splits", "tests/tools/interleave_splits.py"),
    ("run_regression_case", "tests/tools/regression_runner.py"),
    ("_run_optimize_multistage_case", "tests/tools/regression_runner.py"),
    ("RegressionVerdict", "tests/tools/regression_runner.py"),
    ("_REGRESSION_ENGINES", "tests/tools/regression_runner.py"),
)
_P10_MARK_ANY = "Phase 2에서"
_P10_MARK_DELETED = "Phase 2에서 삭제"


def _p10_ident_re(name):
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])")


_P10_DELETED_RES = tuple((n, _p10_ident_re(n)) for n in _P10_DELETED_IDENTS)
_P10_MOVED_RES = tuple((n, _p10_ident_re(n), dest) for n, dest in _P10_MOVED)


def _p10_line_violations(line):
    """한 줄의 위반 이름 목록(표시가 맞으면 빈 목록)."""
    bad = []
    deleted_hit = [n for n, rx in _P10_DELETED_RES if rx.search(line)]
    deleted_hit += [c for c in _P10_DELETED_CALLS if c in line]
    if deleted_hit and _P10_MARK_DELETED not in line:
        bad.extend(deleted_hit)
    for n, rx, dest in _P10_MOVED_RES:
        if rx.search(line) and not (_P10_MARK_ANY in line and dest in line):
            bad.append(n)
    return bad


def _p10_line_targets(line):
    """한 줄에 나오는 N의 이름(대상 여부만)."""
    hit = [n for n, rx in _P10_DELETED_RES if rx.search(line)]
    hit += [c for c in _P10_DELETED_CALLS if c in line]
    hit += [n for n, rx, _d in _P10_MOVED_RES if rx.search(line)]
    return hit


def _p10_doc_files(skill_dir):
    skill_dir = pathlib.Path(skill_dir)
    files = sorted((skill_dir / "references").rglob("*.md"))
    for name in ("SKILL.md", "skill-validation-prompt.md"):
        p = skill_dir / name
        if p.is_file():
            files.append(p)
    return files


def _p10_doc_violations(skill_dir):
    out = []
    for p in _p10_doc_files(skill_dir):
        rel = p.relative_to(_REPO_ROOT).as_posix() if _REPO_ROOT in p.parents else p.name
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            for n in _p10_line_violations(line):
                out.append("%s:%d %s" % (rel, i, n))
    return out


def test_docs_mark_phase2_removed_names():
    files = _p10_doc_files(_P10_SKILL)
    # 판정 대상 문서가 실제로 있다(공허하지 않음): references 문서와 SKILL.md.
    assert any(p.name == "SKILL.md" for p in files)
    assert any(p.parent.name == "references" or "references" in p.parts for p in files)
    assert _p10_doc_violations(_P10_SKILL) == []


# ---------------------------------------------------------------- 판정기 자기 점검(합성 문서 줄, oracle (a))
@pytest.mark.parametrize("line", [
    pytest.param("| slew-rate 계산 | `slew_rate(ID, C)` | |", id="table_row_deleted_unmarked"),
    pytest.param("from sizing_recipe import converge_with_parasitics", id="code_import_deleted_unmarked"),
    pytest.param("    Transistor, build_stick_diagram, render_stick_diagram,", id="code_import_continued"),
    pytest.param("`fT_dev = lut.fT(gm_id, L, VDS, vs)`", id="method_call_unmarked"),
    pytest.param("`telescopic_class_ab` CMRR 폐형식", id="selection_key_unmarked"),
    pytest.param("`find_interleaved_symmetric_splits()`(Phase 2에서 이동)", id="moved_without_path"),
    pytest.param("`run_regression_case()`(Phase 2에서 tests/tools/interleave_splits.py로 이동)", id="moved_wrong_path"),
    pytest.param("`RegressionVerdict` -> tests/tools/regression_runner.py", id="moved_path_without_phase2"),
    pytest.param("`slew_rate()`(Phase 2에서 tests/tools/interleave_splits.py로 이동)", id="deleted_marked_as_moved"),
])
def test_p10_doc_judge_rejects_line(line):
    assert _p10_line_violations(line) != []


@pytest.mark.parametrize("line", [
    pytest.param("| slew-rate 계산 | `slew_rate(ID, C)` (Phase 2에서 삭제) | |", id="deleted_marked"),
    pytest.param("`lut.fT()`(Phase 2에서 삭제)가 `x.fT(a)`를", id="method_call_marked"),
    pytest.param("`find_interleaved_symmetric_splits()`(Phase 2에서 tests/tools/interleave_splits.py로 이동)",
                 id="moved_marked"),
    pytest.param("`_REGRESSION_ENGINES`(Phase 2에서 tests/tools/regression_runner.py로 이동)", id="moved_runner_marked"),
])
def test_p10_doc_judge_accepts_line(line):
    assert _p10_line_targets(line) != []  # 대상 줄이다
    assert _p10_line_violations(line) == []


@pytest.mark.parametrize("line", [
    pytest.param("`slew_rate_limit`는 다른 이름이다", id="identifier_prefix_only"),
    pytest.param("단어 fT는 물리량 표기다(fT_dev, gm/2piC)", id="ft_word_not_call"),
    pytest.param("`my_render_stick_diagram_v2`", id="identifier_embedded"),
])
def test_p10_doc_judge_ignores_partial_identifier(line):
    assert _p10_line_targets(line) == []
    assert _p10_line_violations(line) == []


def test_p10_doc_judge_scans_files(tmp_path):
    # (a) 합성 skill 디렉터리: references 하위 폴더까지·SKILL.md를 읽고, 표시 없는 줄만 위반으로 낸다.
    (tmp_path / "references" / "sub").mkdir(parents=True)
    (tmp_path / "references" / "sub" / "a.md").write_text(
        "ok\n`slew_rate(ID, C)` (Phase 2에서 삭제)\n", encoding="utf-8")
    (tmp_path / "SKILL.md").write_text("x\n`converge_with_parasitics()` 사용\n", encoding="utf-8")
    bad = _p10_doc_violations(tmp_path)
    assert bad == ["SKILL.md:2 converge_with_parasitics"]
