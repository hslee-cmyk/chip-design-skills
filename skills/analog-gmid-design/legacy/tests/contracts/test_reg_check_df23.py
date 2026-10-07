"""Phase 2 P10b 계약: 레지스트리 §8 DF-23 기록 대조 규칙 `reg_check.check_df23`·CLI `--df23-inventory`(20260930-df23-registry-record).

spec card `docs/02-design/specs/20260930-df23-registry-record.spec.md` 계약 1(§8 모양)·3(규칙·절/소절/행 경계·detail·입력 오류)·
4(CLI)를 합성 입력으로 판정한다. 신규 시그니처(interface card): `check_df23(registry_text: str, inventory: dict, inventory_rel: str) -> list`.
계약 5(실제 저장소 대조)는 card '왜 도구 규칙이고 영구 test가 아닌가'에 따라 auditor 측정이고 여기서 보지 않는다.

red 모양(card '판정 유형 근거'): tools 디렉터리를 `sys.path`에 넣은 뒤 모듈 머리의 첫 `reg_check` import 문이
`from reg_check import check_df23`이다. base에는 `check_df23`이 없어 수집 단계 ImportError(`reg_check`, `check_df23`)이고,
병합본에서 green이다. import를 test 함수 안에 두지 않는다. exit 2 test는 같은 test 안에서 정상 입력의 exit 0을 짝으로 본다.

판정 문장 모양(card oracle 절): 피검 심볼 `check_df23(...)`·`main([...])`은 test 본문에서 직접 부른다(helper는 입력 문자열·dict·argv를
만들고 출력 문자열을 나누는 데만 쓴다). 모든 test 본문에 직접 assert가 있다. 빈 발견은 `assert len(findings) == 0`.

oracle 대조(계획 N3.12.3):

* 합성 목록 `_P10B_ITEMS`(항목 9) -- (a) 구성 입력. 이름은 지어낸 이름(`alpha_fn`, `Gamma.beta_m`, `mod_a.py` 등)만 쓴다.
  §8.1·§8.2 기대 행(`_P10B_ROWS_81`·`_P10B_ROWS_82`)은 계약 1 문장(role·phase 값별 개수; (function, 파일 이름) 묶음,
  DF 번호 정수 오름차순 + 끝 `신규`, phase 문자열 오름차순)을 이 항목에 손으로 적용해 리터럴로 적었다(표 주석에 항목 번호).
  도구를 불러 기대값을 만들지 않는다.
* test_p10b_clean_* / test_p10b_ignores_* -- (a) 위 기대 행으로 구성한 §8. 기대 '발견 0'은 계약 3 규칙 문장과 card '발견하면 안 되는 것'.
* test_p10b_boundary_* / test_p10b_adjacent_* -- (a) 계약 3 '절·소절·행 경계' 문장으로 구성한 레지스트리(§8 뒤 절(하나·둘 이상), 두 번째 제목,
  다른 ### 소절, 같은 모양 소절 두 개, 빈 줄 없이 붙은 제목·소절 제목·다음 줄, §8 제목 바로 앞 줄, 칸 모자람·많음).
* test_p10b_detail_* -- (a) 계약 3 `detail` 정의 문장에 손으로 넣은 문자열 리터럴.
* test_p10b_section_* / path / measured_at / total / function -- (a) 조각 하나만 어긋나게 구성, 기대 (rule, name)은 계약 3 문장.
* test_p10b_value_error_* -- (a) 계약 3 입력 오류 (o)·(i)~(v). 기대 `ValueError`(계약 3 문장).
* test_p10b_cli_* -- (a) 합성 루트(tmp_path). exit 0/1/2 규칙, 마지막 줄 `reg_check: 발견 0`, 알 수 없는 인자 2,
  PYTHONIOENCODING=ascii 실행은 계약 4 문장.

판정하지 않은 것(규칙 문장이 정하지 않음): `section` 문자열, 값이 다른 행이 아닌 발견의 `detail`, 발견 순서(CLI 합치기 순서 제외),
빠진 소절 표가 있을 때 `df23-total`·`df23-function` 발견의 유무, `measured_at:`·`목록:` 줄이 빠졌을 때 `df23-measured-at`·`df23-path` 발견의 유무.
"""
import copy
import json
import os
import pathlib
import subprocess
import sys

import pytest

# contracts -> tests -> assets(A) -> analog-gmid-design -> skills -> 저장소 루트
_P10B_TESTS_DIR = pathlib.Path(__file__).resolve().parents[1]
_P10B_TOOLS_DIR = _P10B_TESTS_DIR / "tools"
_P10B_ASSETS_REL = pathlib.PurePosixPath("skills", "analog-gmid-design", "assets")

if str(_P10B_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_P10B_TOOLS_DIR))

from reg_check import check_df23, main  # noqa: E402  (check_df23은 base에 없는 신규 심볼 -- red의 근원)

_P10B_RECORD_KEYS = {"rule", "section", "name", "detail"}
_P10B_BEHAVIOR = "동작을 정함"
_P10B_MESSAGE = "메시지뿐"
_P10B_INV_REL = "docs/an/df23_inv.json"
_P10B_MEASURED = "0123456789abcdef0123456789abcdef01234567"
_P10B_CLEAN_LINE = "reg_check: 발견 0"   # 계약 4 문장의 출력 줄 그대로


def _p10b_item(file, function, role, phase, plan_mapping):
    return {"file": file, "function": function, "role": role, "phase": phase, "plan_mapping": plan_mapping,
            "line": 1, "literal": "x"}


# 합성 목록(oracle (a) 구성 입력). 번호는 아래 기대 행 주석이 가리킨다.
_P10B_ITEMS = [
    _p10b_item("pkg/x/mod_a.py", "alpha_fn", _P10B_BEHAVIOR, "4", "DF-19(설명)"),             # 1
    _p10b_item("pkg/x/mod_a.py", "alpha_fn", _P10B_BEHAVIOR, "3", "DF-4"),                    # 2
    _p10b_item("pkg/x/mod_a.py", "alpha_fn", _P10B_BEHAVIOR, "4", "신규(계획 밖)"),            # 3
    _p10b_item("pkg/x/mod_a.py", "alpha_fn", _P10B_BEHAVIOR, "7b", "DF-19"),                  # 4
    _p10b_item("pkg/x/mod_a.py", "Gamma.beta_m", _P10B_BEHAVIOR, "7b", "DF-7(설명)"),         # 5
    _p10b_item("ws/mod_b.py", "<module>", _P10B_BEHAVIOR, "7a", "신규"),                      # 6
    _p10b_item("ws/mod_b.py", "<module>", _P10B_BEHAVIOR, "해당 없음", "신규(다른 설명)"),     # 7
    _p10b_item("ws/mod_b.py", "delta_fn", _P10B_MESSAGE, "해당 없음", "DF-31(메시지)"),        # 8 메시지뿐: §8.2 대상 아님
    _p10b_item("pkg/x/mod_a.py", "eps_fn", _P10B_MESSAGE, "해당 없음", "기타 표기"),           # 9 메시지뿐: 형식 검사 대상 아님
]

# §8.1 기대 행 -- 계약 1: 항목 전부의 role 값별·phase 값별 개수(0인 값 행 없음).
_P10B_ROWS_81 = [
    ("role", _P10B_BEHAVIOR, "7"),   # 1~7
    ("role", _P10B_MESSAGE, "2"),    # 8, 9
    ("phase", "3", "1"),             # 2
    ("phase", "4", "2"),             # 1, 3
    ("phase", "7a", "1"),            # 6
    ("phase", "7b", "2"),            # 4, 5
    ("phase", "해당 없음", "3"),      # 7, 8, 9
]

# §8.2 기대 행 -- 계약 1: role = 동작을 정함 항목을 (function, file 마지막 성분)으로 묶음.
# DF = `^DF-(\d+)` 번호 정수 오름차순 중복 없이 + `신규`로 시작하는 항목이 있으면 끝에 `신규`; 담당 Phase = phase 문자열 오름차순 중복 없이.
_P10B_ROWS_82 = [
    ("`alpha_fn`", "mod_a.py", "4", "DF-4, DF-19, 신규", "3, 4, 7b"),   # 1~4: DF-19 두 번, 4 < 19(정수), 신규 3
    ("`Gamma.beta_m`", "mod_a.py", "1", "DF-7", "7b"),                  # 5
    ("`<module>`", "mod_b.py", "2", "신규", "7a, 해당 없음"),            # 6, 7: '7a' < '해당 없음'(코드포인트)
]

_P10B_HDR_81 = ("축", "값", "항목 수")
_P10B_HDR_82 = ("함수", "파일", "항목 수", "DF", "담당 Phase")
_P10B_TITLE = "## 8. DF-23 -- 엔진 이름 리터럴 종속 (전수 목록 기록)"
_P10B_SUB81 = "### 8.1 총계"
_P10B_SUB82 = "### 8.2 함수별 (role = 동작을 정함)"
_P10B_LIST_LINE = f"목록: `{_P10B_INV_REL}`"
_P10B_MEAS_LINE = f"measured_at: `{_P10B_MEASURED}`"

# 계약 1·3과 어긋나는 값의 표(경계 test에서 읽히면 발견이 생기도록 일부러 틀린 값)
_P10B_WRONG_81 = [("role", "엉뚱한 값", "77"), ("phase", "3", "50")]
_P10B_WRONG_82 = [("`ghost_fn`", "mod_z.py", "9", "DF-1", "3"), ("`alpha_fn`", "mod_a.py", "99", "DF-1", "3")]


def _p10b_inventory(items=None, **top):
    inv = {"measured_at": _P10B_MEASURED, "totals": {"n_items": 9},
           "items": copy.deepcopy(_P10B_ITEMS if items is None else items)}
    inv.update(top)
    return inv


def _p10b_md_row(cells):
    return "| " + " | ".join(cells) + " |"


def _p10b_table(header, rows):
    lines = [_p10b_md_row(header), "|" + "---|" * len(header)]
    lines += [_p10b_md_row(r) for r in rows]
    return "\n".join(lines)


def _p10b_join(*chunks):
    """줄 조각을 빈 줄 없이 그대로 잇는다(빈 줄이 필요하면 조각으로 "" 를 넣는다)."""
    return "\n".join(chunks)


def _p10b_section8(rows81=None, rows82=None, path=_P10B_INV_REL, measured=_P10B_MEASURED, title=_P10B_TITLE,
                   hdr81=_P10B_HDR_81, hdr82=_P10B_HDR_82, omit=(), table81=True, table82=True,
                   after81="", after82=""):
    """계약 1 모양의 §8.

    omit: 뺄 조각 이름(`목록`·`measured_at`·`8.1`·`8.2` -- 소절 제목째 뺀다).
    table81/table82: False면 소절 제목만 두고 그 아래 표를 두지 않는다.
    after81/after82: 해당 소절 뒤에 그대로 붙일 글(다른 `### ` 소절 등).
    """
    rows81 = _P10B_ROWS_81 if rows81 is None else rows81
    rows82 = _P10B_ROWS_82 if rows82 is None else rows82
    parts = [title, ""]
    if "목록" not in omit:
        parts.append(f"목록: `{path}`")
    if "measured_at" not in omit:
        parts.append(f"measured_at: `{measured}`")
    parts += ["", "목록을 다시 재면 이 절을 같은 Phase 안에서 갱신한다(대조: `reg_check.py --df23-inventory`).", ""]
    if "8.1" not in omit:
        parts += [_P10B_SUB81, ""]
        if table81:
            parts += [_p10b_table(hdr81, rows81), ""]
    if after81:
        parts += [after81, ""]
    if "8.2" not in omit:
        parts += [_P10B_SUB82, ""]
        if table82:
            parts += [_p10b_table(hdr82, rows82), ""]
    if after82:
        parts += [after82, ""]
    return "\n".join(parts)


_P10B_S7_TITLE = "## 7. D -- 운영 경로 호출 0 (배선/삭제 결정 필요)"
_P10B_KEPT = "p10b_kept_fn"


def _p10b_registry(section8=None, s7_name=_P10B_KEPT, s7_extra="", tail="", s7_last_line=""):
    """§0 + §1 집계 + §7(기존 규칙 발견 0이 되게: 엔진 파일 `engine_p10b.py`의 정의 하나) + (§8) + (tail).

    s7_last_line: §7 마지막 줄로(빈 줄 없이 §8 제목 바로 앞에) 둘 줄.
    """
    parts = [
        "# 함수 재사용 레지스트리 -- synthetic p10b",
        "",
        "## 0. 사용 규칙 (강제)",
        "",
        "설명 문단.",
        "",
        "## 1. 집계",
        "",
        _p10b_table(("파일", "R0", "R1", "R2", "D", "DUP", "비고"), [["engine_p10b.py", "3", "1", "0", "1", "0", "표 행 기준"]]),
        "",
        _P10B_S7_TITLE,
        "",
        "### engine_p10b.py (1)",
        "",
        _p10b_table(("함수", "책임", "이관 목적지", "처리", "비고"), [[f"`{s7_name}`", "책임", "목적지", "보류(Phase 3)", "비고"]]),
        "",
    ]
    if s7_extra:
        parts += [s7_extra, ""]
    if s7_last_line:
        parts.append(s7_last_line)
    if section8 is not None:
        parts.append(section8)
    if tail:
        parts += [tail, ""]
    return "\n".join(parts)


def _p10b_names(findings, rule):
    return [f["name"] for f in findings if f["rule"] == rule]


def _p10b_pairs(findings):
    return sorted((f["rule"], f["name"]) for f in findings)


# ---------------------------------------------------------------------------------------------------------------
# check_df23: 발견 0
# ---------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("eol", ["\n", "\r\n"], ids=["lf", "crlf"])
def test_p10b_clean_registry_has_no_findings(eol):
    # oracle (a): 계약 1 규칙을 합성 목록에 손으로 적용한 §8 -- 발견 0. CRLF: 계약 1 "줄 끝 문자는 판정에 들지 않는다".
    findings = check_df23(_p10b_registry(_p10b_section8()).replace("\n", eol), _p10b_inventory(), _P10B_INV_REL)
    assert len(findings) == 0, findings


def test_p10b_clean_ignores_row_order():
    # oracle (a): card '발견하면 안 되는 것' -- 행 순서만 다른 레지스트리(도구는 행 집합만 본다).
    text = _p10b_registry(_p10b_section8(rows81=list(reversed(_P10B_ROWS_81)), rows82=list(reversed(_P10B_ROWS_82))))
    findings = check_df23(text, _p10b_inventory(), _P10B_INV_REL)
    assert len(findings) == 0, findings


def test_p10b_ignores_wrong_totals_field():
    # oracle (a): 계약 3 "모든 기대값은 items에서 계산한다(목록의 totals를 믿지 않는다)" -- totals가 틀려도 §8이 items와 같으면 발견 0.
    inv = _p10b_inventory(totals={"n_items": 999, "by_role": {_P10B_BEHAVIOR: 1}, "by_phase": {"3": 50}})
    findings = check_df23(_p10b_registry(_p10b_section8()), inv, _P10B_INV_REL)
    assert len(findings) == 0, findings


def test_p10b_ignores_tables_outside_section8():
    # oracle (a): card '발견하면 안 되는 것' -- §0~§7의 표. §7 안에 §8.1·§8.2와 같은 머리의 틀린 표를 두어도 발견 0.
    bogus = "\n".join([_P10B_SUB81, "", _p10b_table(_P10B_HDR_81, _P10B_WRONG_81), "",
                       _P10B_SUB82, "", _p10b_table(_P10B_HDR_82, _P10B_WRONG_82)])
    findings = check_df23(_p10b_registry(_p10b_section8(), s7_extra=bogus), _p10b_inventory(), _P10B_INV_REL)
    assert len(findings) == 0, findings


@pytest.mark.parametrize("mapping", ["아무 표기", "DF-31(메시지)", "신규(메시지)"], ids=["other", "df-number", "new"])
def test_p10b_ignores_message_only_items_mapping(mapping):
    # oracle (a): card '발견하면 안 되는 것' -- role 메시지뿐 항목은 §8.2 대상이 아니고 plan_mapping 형식 검사((v))도 받지 않는다
    # (DF 번호로 시작해도, 신규로도 DF로도 시작하지 않아도). 메시지뿐 항목 9의 mapping을 바꿔도 발견 0, ValueError 없음.
    items = copy.deepcopy(_P10B_ITEMS)
    items[8]["plan_mapping"] = mapping
    findings = check_df23(_p10b_registry(_p10b_section8()), _p10b_inventory(items), _P10B_INV_REL)
    assert len(findings) == 0, findings


# ---------------------------------------------------------------------------------------------------------------
# 계약 3 '절·소절·행 경계'
# ---------------------------------------------------------------------------------------------------------------
def test_p10b_boundary_tables_after_section8_not_read():
    # oracle (a): 계약 3 "§8 = 첫 제목 줄부터 그 뒤 처음 `## `로 시작하는 줄 전까지(§8 뒤 절의 줄·표는 읽지 않는다)".
    # §8(정답) 뒤 `## 9.` 절에 §8.1·§8.2 소절 제목·표 머리와 같은 틀린 표, 다른 `목록:`·`measured_at:` 줄 -> 발견 0.
    s9 = "\n".join(["## 9. 다른 절", "", "목록: `docs/an/other.json`", f"measured_at: `{'f' * 40}`", "",
                    _P10B_SUB81, "", _p10b_table(_P10B_HDR_81, _P10B_WRONG_81), "",
                    _P10B_SUB82, "", _p10b_table(_P10B_HDR_82, _P10B_WRONG_82)])
    findings = check_df23(_p10b_registry(_p10b_section8(), tail=s9), _p10b_inventory(), _P10B_INV_REL)
    assert len(findings) == 0, findings


@pytest.mark.parametrize("piece", ["목록", "measured_at", "8.1", "8.2"])
def test_p10b_boundary_piece_only_after_section8_is_missing(piece):
    # oracle (a): 같은 경계 문장 -- §8에서 조각 하나를 빼고 그 조각(정답 값)을 `## 9.` 절에만 두면 §8에서 빠진 것이다:
    # `df23-section` name = 빠진 것(계약 3).
    s9_body = {
        "목록": _P10B_LIST_LINE,
        "measured_at": _P10B_MEAS_LINE,
        "8.1": "\n".join([_P10B_SUB81, "", _p10b_table(_P10B_HDR_81, _P10B_ROWS_81)]),
        "8.2": "\n".join([_P10B_SUB82, "", _p10b_table(_P10B_HDR_82, _P10B_ROWS_82)]),
    }[piece]
    text = _p10b_registry(_p10b_section8(omit=(piece,)), tail="## 9. 다른 절\n\n" + s9_body)
    findings = check_df23(text, _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_names(findings, "df23-section") == [piece], findings


@pytest.mark.parametrize("piece", ["목록", "measured_at", "8.1", "8.2"])
def test_p10b_boundary_several_sections_after_section8_end_at_first(piece):
    # oracle (a): 계약 3 "§8 = ... 그 뒤 **처음** `## `로 시작하는 줄 전까지" -- §8 뒤에 `## 9.`·`## 10.`·`## 11.` 세 절.
    # §8에서 조각 하나를 빼고 그 조각(정답 값)을 둘째 절이 아닌 **첫** 뒤 절 `## 9.`에 둔다(그 뒤에 `## 10.`·`## 11.`이 더 있다)
    # -> §8은 `## 9.` 앞에서 끝나므로 빠진 것: `df23-section` name = 빠진 것.
    s9_body = {
        "목록": _P10B_LIST_LINE,
        "measured_at": _P10B_MEAS_LINE,
        "8.1": "\n".join([_P10B_SUB81, "", _p10b_table(_P10B_HDR_81, _P10B_ROWS_81)]),
        "8.2": "\n".join([_P10B_SUB82, "", _p10b_table(_P10B_HDR_82, _P10B_ROWS_82)]),
    }[piece]
    tail = "\n".join(["## 9. 다음 절", "", s9_body, "", "## 10. 또 다음 절", "", "본문.", "", "## 11. 끝 절", "", "본문."])
    findings = check_df23(_p10b_registry(_p10b_section8(omit=(piece,)), tail=tail), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_names(findings, "df23-section") == [piece], findings


def test_p10b_boundary_several_sections_after_section8_not_read():
    # oracle (a): 같은 문장 -- §8(정답) 뒤 `## 9.`·`## 10.` 두 절 모두에 다른 `목록:`·`measured_at:` 줄과 같은 머리의 틀린 표 -> 발견 0.
    def wrong_section(head):
        return "\n".join([head, "", "목록: `docs/an/other.json`", f"measured_at: `{'e' * 40}`", "",
                          _P10B_SUB81, "", _p10b_table(_P10B_HDR_81, _P10B_WRONG_81), "",
                          _P10B_SUB82, "", _p10b_table(_P10B_HDR_82, _P10B_WRONG_82)])
    tail = "\n".join([wrong_section("## 9. 다음 절"), "", wrong_section("## 10. 또 다음 절")])
    findings = check_df23(_p10b_registry(_p10b_section8(), tail=tail), _p10b_inventory(), _P10B_INV_REL)
    assert len(findings) == 0, findings


def test_p10b_boundary_second_title_wrong_tables_not_read():
    # oracle (a): 계약 3 "`## 8.`로 시작하고 `DF-23`을 담은 **첫** 제목 줄" -- 정답 §8 뒤에 같은 모양의 두 번째 제목과
    # 틀린 값의 §8(다른 measured_at·경로·표) -> 첫 절만 읽어 발견 0.
    second = _p10b_section8(rows81=_P10B_WRONG_81, rows82=_P10B_WRONG_82, path="docs/an/other.json",
                            measured="f" * 40, title=_P10B_TITLE + " (사본)")
    findings = check_df23(_p10b_registry(_p10b_section8(), tail=second), _p10b_inventory(), _P10B_INV_REL)
    assert len(findings) == 0, findings


def test_p10b_boundary_second_title_correct_section_not_used():
    # oracle (a): 같은 문장의 반대 방향 -- 첫 §8에 `### 8.2`가 없고 두 번째 같은 모양 제목의 절이 정답 전부를 가져도
    # 첫 절 기준으로 `df23-section` 8.2 발견.
    second = _p10b_section8(title=_P10B_TITLE + " (사본)")
    findings = check_df23(_p10b_registry(_p10b_section8(omit=("8.2",)), tail=second), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_names(findings, "df23-section") == ["8.2"], findings


def test_p10b_boundary_other_subsection_tables_not_read():
    # oracle (a): 계약 3 "§8.1/§8.2 표 = `### 8.1`/`### 8.2`로 시작하는 첫 줄부터 그 뒤 처음 `### `로 시작하는 줄 전까지 ...
    # (다른 `###` 소절 아래 같은 머리의 표는 읽지 않는다)" -- 8.1 뒤와 8.2 뒤 각각 `### 참고` 소절에 같은 머리의 틀린 표 -> 발견 0.
    other81 = "\n".join(["### 참고 A", "", _p10b_table(_P10B_HDR_81, _P10B_WRONG_81)])
    other82 = "\n".join(["### 참고 B", "", _p10b_table(_P10B_HDR_82, _P10B_WRONG_82)])
    findings = check_df23(_p10b_registry(_p10b_section8(after81=other81, after82=other82)), _p10b_inventory(), _P10B_INV_REL)
    assert len(findings) == 0, findings


@pytest.mark.parametrize("which", ["8.1", "8.2"])
def test_p10b_boundary_table_only_under_other_subsection(which):
    # oracle (a): 같은 문장 -- 소절 제목 `### 8.1`(또는 `### 8.2`) 아래에는 표가 없고, 그 뒤 다른 `### 참고` 소절 아래에만
    # 정답 표가 있다 -> 그 소절에 계약 1 표 머리를 가진 표가 없다: `df23-section` name = 소절.
    if which == "8.1":
        other = "\n".join(["### 참고 A", "", _p10b_table(_P10B_HDR_81, _P10B_ROWS_81)])
        sec = _p10b_section8(table81=False, after81=other)
    else:
        other = "\n".join(["### 참고 B", "", _p10b_table(_P10B_HDR_82, _P10B_ROWS_82)])
        sec = _p10b_section8(table82=False, after82=other)
    findings = check_df23(_p10b_registry(sec), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_names(findings, "df23-section") == [which], findings


def test_p10b_boundary_two_same_subsections_first_read_81():
    # oracle (a): 계약 3 "`### 8.1`로 시작하는 **첫** 줄부터 그 뒤 처음 `### ` 전까지" -- §8 안에 같은 모양의 `### 8.1 총계` 소절 둘.
    # 첫 소절 = 정답 표, 둘째 소절 = 틀린 값의 표 -> 첫 소절만 읽어 발견 0.
    second = "\n".join([_P10B_SUB81, "", _p10b_table(_P10B_HDR_81, _P10B_WRONG_81)])
    findings = check_df23(_p10b_registry(_p10b_section8(after81=second)), _p10b_inventory(), _P10B_INV_REL)
    assert len(findings) == 0, findings


def test_p10b_boundary_two_same_subsections_first_read_82():
    # oracle (a): 같은 문장(§8.2) -- 첫 `### 8.2` 소절 = 정답 표, 둘째 같은 모양 소절 = 틀린 값의 표 -> 발견 0.
    second = "\n".join([_P10B_SUB82, "", _p10b_table(_P10B_HDR_82, _P10B_WRONG_82)])
    findings = check_df23(_p10b_registry(_p10b_section8(after82=second)), _p10b_inventory(), _P10B_INV_REL)
    assert len(findings) == 0, findings


def test_p10b_boundary_two_same_subsections_first_wrong_81():
    # oracle (a): 같은 문장의 반대 방향 -- 첫 `### 8.1` 소절의 `phase | 7a` 행 수가 1이 아닌 2, 둘째 같은 모양 소절 = 정답 표.
    # 첫 소절만 읽으므로 `df23-total` phase:7a 하나, detail = f"항목 수 {'2'!r} != {'1'!r}"(계약 3 detail 정의, 손으로 적은 리터럴).
    rows81 = [(a, v, "2" if (a, v) == ("phase", "7a") else c) for a, v, c in _P10B_ROWS_81]
    second = "\n".join([_P10B_SUB81, "", _p10b_table(_P10B_HDR_81, _P10B_ROWS_81)])
    findings = check_df23(_p10b_registry(_p10b_section8(rows81=rows81, after81=second)), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-total", "phase:7a")], findings
    assert findings[0]["detail"] == "항목 수 '2' != '1'", findings


def test_p10b_boundary_two_same_subsections_first_wrong_82():
    # oracle (a): 같은 문장(§8.2) -- 첫 `### 8.2` 소절에서 `<module>` 묶음 행이 빠졌고, 둘째 같은 모양 소절 = 정답 표 -> 첫 소절만 읽어
    # `df23-function` mod_b.py::<module> 하나(빠진 행).
    second = "\n".join([_P10B_SUB82, "", _p10b_table(_P10B_HDR_82, _P10B_ROWS_82)])
    findings = check_df23(_p10b_registry(_p10b_section8(rows82=_P10B_ROWS_82[:2], after82=second)),
                          _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-function", "mod_b.py::<module>")], findings


def test_p10b_boundary_short_row_81_no_exception():
    # oracle (a): 계약 3 "행의 칸이 표 머리보다 적으면 모자란 칸을 빈 문자열로 보고(예외를 내지 않는다)" --
    # `| phase | 7a |`(항목 수 칸 없음) -> phase:7a 다른 수 발견 하나, detail = `항목 수 '' != '1'`(계약 3 detail 정의, 손으로 적은 리터럴).
    rows81 = [r if (r[0], r[1]) != ("phase", "7a") else ("phase", "7a") for r in _P10B_ROWS_81]
    findings = check_df23(_p10b_registry(_p10b_section8(rows81=rows81)), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-total", "phase:7a")], findings
    assert findings[0]["detail"] == "항목 수 '' != '1'", findings


def test_p10b_boundary_short_row_82_no_exception():
    # oracle (a): 같은 문장 -- `alpha_fn` 행을 세 칸(함수·파일·항목 수)만 -> 다른 칸 발견 하나,
    # detail의 reg = ('4', '', '')(모자란 칸 ""), exp = 계약 1 값(손으로 적은 리터럴).
    rows82 = [("`alpha_fn`", "mod_a.py", "4")] + _P10B_ROWS_82[1:]
    findings = check_df23(_p10b_registry(_p10b_section8(rows82=rows82)), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-function", "mod_a.py::alpha_fn")], findings
    assert findings[0]["detail"] == "(항목 수, DF, 담당 Phase) ('4', '', '') != ('4', 'DF-4, DF-19, 신규', '3, 4, 7b')", findings


def test_p10b_boundary_long_rows_extra_cells_ignored():
    # oracle (a): 계약 3 "많으면 표 머리 칸 수 뒤의 칸은 무시한다" -- §8.1·§8.2 모든 행 끝에 칸 하나씩 더해도 앞 칸이 맞으면 발견 0.
    rows81 = [r + ("덧칸",) for r in _P10B_ROWS_81]
    rows82 = [r + ("비고 칸", "또 하나") for r in _P10B_ROWS_82]
    findings = check_df23(_p10b_registry(_p10b_section8(rows81=rows81, rows82=rows82)), _p10b_inventory(), _P10B_INV_REL)
    assert len(findings) == 0, findings


def test_p10b_boundary_long_row_81_detail_excludes_extra_cells():
    # oracle (a): 계약 3 "많으면 표 머리 칸 수 뒤의 칸은 무시한다" + `detail` 정의 -- `| phase | 3 | 2 | 9 | 덧칸 |`(항목 수 2, 센 수 1)
    # -> `df23-total` phase:3 하나, detail의 reg는 `항목 수` 칸 '2'뿐(덧칸 '9'·'덧칸'은 들어가지 않음): `항목 수 '2' != '1'`.
    rows81 = [r if (r[0], r[1]) != ("phase", "3") else ("phase", "3", "2", "9", "덧칸") for r in _P10B_ROWS_81]
    findings = check_df23(_p10b_registry(_p10b_section8(rows81=rows81)), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-total", "phase:3")], findings
    assert findings[0]["detail"] == "항목 수 '2' != '1'", findings


def test_p10b_boundary_long_row_82_detail_excludes_extra_cells():
    # oracle (a): 같은 두 문장(§8.2) -- `alpha_fn` 행 항목 수 5(센 수 4)에 덧칸 두 개 -> `df23-function` 하나,
    # detail의 reg는 표 머리 칸 수(5) 안의 세 칸 tuple뿐(덧칸 미포함): 손으로 적은 리터럴.
    rows82 = [("`alpha_fn`", "mod_a.py", "5", "DF-4, DF-19, 신규", "3, 4, 7b", "덧칸", "DF-99")] + _P10B_ROWS_82[1:]
    findings = check_df23(_p10b_registry(_p10b_section8(rows82=rows82)), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-function", "mod_a.py::alpha_fn")], findings
    assert findings[0]["detail"] == (
        "(항목 수, DF, 담당 Phase) ('5', 'DF-4, DF-19, 신규', '3, 4, 7b') != ('4', 'DF-4, DF-19, 신규', '3, 4, 7b')"), findings


# ---------------------------------------------------------------------------------------------------------------
# 계약 3 경계 -- 빈 줄 없이 붙은 줄(제목·소절 제목과 바로 다음 줄, §8 제목 바로 앞 줄)
# ---------------------------------------------------------------------------------------------------------------
def test_p10b_adjacent_title_then_list_line_is_read():
    # oracle (a): 계약 3 "§8 = 첫 제목 줄**부터**" -- 제목 바로 다음 줄(빈 줄 없음)이 `목록:`, 그 다음 줄이 `measured_at:`,
    # 소절 제목 바로 다음 줄이 표 머리 -> 모두 §8 안이라 발견 0.
    sec = _p10b_join(_P10B_TITLE, _P10B_LIST_LINE, _P10B_MEAS_LINE,
                     _P10B_SUB81, _p10b_table(_P10B_HDR_81, _P10B_ROWS_81),
                     _P10B_SUB82, _p10b_table(_P10B_HDR_82, _P10B_ROWS_82))
    findings = check_df23(_p10b_registry(sec), _p10b_inventory(), _P10B_INV_REL)
    assert len(findings) == 0, findings


def test_p10b_adjacent_title_then_measured_at_line_is_read():
    # oracle (a): 같은 문장 -- 제목 바로 다음 줄이 `measured_at:`(목록 줄은 그 뒤) -> 발견 0.
    sec = _p10b_join(_P10B_TITLE, _P10B_MEAS_LINE, _P10B_LIST_LINE, "",
                     _P10B_SUB81, "", _p10b_table(_P10B_HDR_81, _P10B_ROWS_81), "",
                     _P10B_SUB82, "", _p10b_table(_P10B_HDR_82, _P10B_ROWS_82))
    findings = check_df23(_p10b_registry(sec), _p10b_inventory(), _P10B_INV_REL)
    assert len(findings) == 0, findings


def test_p10b_adjacent_title_then_list_line_wrong_value_found():
    # oracle (a): 같은 문장 -- 제목 바로 다음 줄의 `목록:` 경로만 다르다 -> 그 줄을 읽어 `df23-path`, name = 레지스트리 쪽 값.
    other = "docs/an/adjacent_other.json"
    sec = _p10b_join(_P10B_TITLE, f"목록: `{other}`", _P10B_MEAS_LINE, "",
                     _P10B_SUB81, "", _p10b_table(_P10B_HDR_81, _P10B_ROWS_81), "",
                     _P10B_SUB82, "", _p10b_table(_P10B_HDR_82, _P10B_ROWS_82))
    findings = check_df23(_p10b_registry(sec), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-path", other)], findings


def test_p10b_adjacent_title_then_subsection_81_first_line():
    # oracle (a): 같은 문장 -- `### 8.1`이 §8의 첫 줄(제목 바로 다음 줄), 그 바로 다음 줄이 표 머리.
    # `목록:`·`measured_at:` 줄은 §8 안 뒤쪽(`### 출처` 소절)에 둔다 -> 발견 0.
    sec = _p10b_join(_P10B_TITLE, _P10B_SUB81, _p10b_table(_P10B_HDR_81, _P10B_ROWS_81), "",
                     _P10B_SUB82, _p10b_table(_P10B_HDR_82, _P10B_ROWS_82), "",
                     "### 출처", "", _P10B_LIST_LINE, _P10B_MEAS_LINE)
    findings = check_df23(_p10b_registry(sec), _p10b_inventory(), _P10B_INV_REL)
    assert len(findings) == 0, findings


def test_p10b_adjacent_title_then_subsection_81_first_line_wrong_value():
    # oracle (a): 같은 구성에서 §8.1 `role | 동작을 정함` 수만 8(센 수 7) -> 첫 줄 소절의 표를 읽어 `df23-total` 하나,
    # detail = `항목 수 '8' != '7'`(손으로 적은 리터럴).
    rows81 = [(a, v, "8" if (a, v) == ("role", _P10B_BEHAVIOR) else c) for a, v, c in _P10B_ROWS_81]
    sec = _p10b_join(_P10B_TITLE, _P10B_SUB81, _p10b_table(_P10B_HDR_81, rows81), "",
                     _P10B_SUB82, _p10b_table(_P10B_HDR_82, _P10B_ROWS_82), "",
                     "### 출처", "", _P10B_LIST_LINE, _P10B_MEAS_LINE)
    findings = check_df23(_p10b_registry(sec), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-total", "role:" + _P10B_BEHAVIOR)], findings
    assert findings[0]["detail"] == "항목 수 '8' != '7'", findings


def test_p10b_adjacent_title_then_next_section_ends_section8():
    # oracle (a): 계약 3 "그 뒤 처음 `## `로 시작하는 줄 전까지" -- 제목 바로 다음 줄이 `## 9.` 제목이면 §8은 제목 한 줄뿐이다.
    # `## 9.` 절에 정답 조각 전부를 두어도 §8에서 넷 다 빠진 것: `df23-section` name = 목록·measured_at·8.1·8.2.
    rest = _p10b_section8(title="## 9. 다음 절")
    text = _p10b_registry(_p10b_join(_P10B_TITLE, rest))
    findings = check_df23(text, _p10b_inventory(), _P10B_INV_REL)
    assert sorted(_p10b_names(findings, "df23-section")) == sorted(["목록", "measured_at", "8.1", "8.2"]), findings


@pytest.mark.parametrize("which", ["8.1", "8.2"])
def test_p10b_adjacent_subsection_then_table_header_is_read(which):
    # oracle (a): 계약 3 "§8.1/§8.2 표 = `### 8.1`/`### 8.2`로 시작하는 첫 줄**부터**" -- 소절 제목 바로 다음 줄(빈 줄 없음)이 표 머리이고
    # 그 표의 한 행 값이 틀렸다 -> 그 표를 읽어 해당 규칙 발견 하나(빈 줄 없이 붙은 표도 소절 안이다).
    if which == "8.1":
        rows81 = [(a, v, "3" if (a, v) == ("phase", "7b") else c) for a, v, c in _P10B_ROWS_81]   # 7b: 센 수 2
        sub = _p10b_join(_P10B_SUB81, _p10b_table(_P10B_HDR_81, rows81), "",
                         _P10B_SUB82, "", _p10b_table(_P10B_HDR_82, _P10B_ROWS_82))
        expected = [("df23-total", "phase:7b")]
    else:
        rows82 = [r if r[0] != "`Gamma.beta_m`" else ("`Gamma.beta_m`", "mod_a.py", "2", "DF-7", "7b") for r in _P10B_ROWS_82]
        sub = _p10b_join(_P10B_SUB81, "", _p10b_table(_P10B_HDR_81, _P10B_ROWS_81), "",
                         _P10B_SUB82, _p10b_table(_P10B_HDR_82, rows82))
        expected = [("df23-function", "mod_a.py::Gamma.beta_m")]
    sec = _p10b_join(_P10B_TITLE, "", _P10B_LIST_LINE, _P10B_MEAS_LINE, "", sub)
    findings = check_df23(_p10b_registry(sec), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == expected, findings


@pytest.mark.parametrize("which", ["8.1", "8.2"])
def test_p10b_adjacent_subsection_then_table_header_clean(which):
    # oracle (a): 같은 문장 -- 소절 제목 바로 다음 줄이 정답 표의 머리 -> 발견 0(`df23-section` 소절 발견 없음).
    if which == "8.1":
        sub = _p10b_join(_P10B_SUB81, _p10b_table(_P10B_HDR_81, _P10B_ROWS_81), "",
                         _P10B_SUB82, "", _p10b_table(_P10B_HDR_82, _P10B_ROWS_82))
    else:
        sub = _p10b_join(_P10B_SUB81, "", _p10b_table(_P10B_HDR_81, _P10B_ROWS_81), "",
                         _P10B_SUB82, _p10b_table(_P10B_HDR_82, _P10B_ROWS_82))
    sec = _p10b_join(_P10B_TITLE, "", _P10B_LIST_LINE, _P10B_MEAS_LINE, "", sub)
    findings = check_df23(_p10b_registry(sec), _p10b_inventory(), _P10B_INV_REL)
    assert len(findings) == 0, findings


@pytest.mark.parametrize("which", ["8.1", "8.2"])
def test_p10b_adjacent_subsection_then_other_subsection_ends_it(which):
    # oracle (a): 계약 3 "그 뒤 처음 `### `로 시작하는 줄 전까지" -- `### 8.1`(또는 `### 8.2`) 바로 다음 줄이 `### 참고` 소절 제목이고
    # 정답 표는 그 `### 참고` 아래에만 있다 -> 소절은 제목 한 줄뿐이라 표 머리가 없다: `df23-section` name = 소절.
    if which == "8.1":
        sub = _p10b_join(_P10B_SUB81, "### 참고 A", _p10b_table(_P10B_HDR_81, _P10B_ROWS_81), "",
                         _P10B_SUB82, "", _p10b_table(_P10B_HDR_82, _P10B_ROWS_82))
    else:
        sub = _p10b_join(_P10B_SUB81, "", _p10b_table(_P10B_HDR_81, _P10B_ROWS_81), "",
                         _P10B_SUB82, "### 참고 B", _p10b_table(_P10B_HDR_82, _P10B_ROWS_82))
    sec = _p10b_join(_P10B_TITLE, "", _P10B_LIST_LINE, _P10B_MEAS_LINE, "", sub)
    findings = check_df23(_p10b_registry(sec), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_names(findings, "df23-section") == [which], findings


@pytest.mark.parametrize("piece, line", [("목록", _P10B_LIST_LINE), ("measured_at", _P10B_MEAS_LINE)],
                         ids=["list-line", "measured-at-line"])
def test_p10b_adjacent_line_before_title_is_outside(piece, line):
    # oracle (a): 계약 3 "§8 = ... 제목 줄**부터**" -- §8에서 그 조각 줄을 빼고 정답 값의 같은 줄을 §8 제목 **바로 앞 줄**(빈 줄 없이 §7 끝)에 둔다
    # -> §8 밖이므로 빠진 것: `df23-section` name = 빠진 것.
    text = _p10b_registry(_p10b_section8(omit=(piece,)), s7_last_line=line)
    findings = check_df23(text, _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_names(findings, "df23-section") == [piece], findings


def test_p10b_adjacent_wrong_lines_before_title_not_read():
    # oracle (a): 같은 문장 -- §8 제목 바로 앞 두 줄(빈 줄 없이)에 다른 경로의 `목록:`·다른 값의 `measured_at:` 줄, §8 안은 정답 -> 발견 0.
    before = _p10b_join("목록: `docs/an/before_title.json`", f"measured_at: `{'d' * 40}`")
    findings = check_df23(_p10b_registry(_p10b_section8(), s7_last_line=before), _p10b_inventory(), _P10B_INV_REL)
    assert len(findings) == 0, findings


# ---------------------------------------------------------------------------------------------------------------
# 계약 3 `detail` (값이 다른 행)
# ---------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("axis, value, reg, detail", [
    ("role", _P10B_BEHAVIOR, "8", "항목 수 '8' != '7'"),
    ("phase", "해당 없음", "2", "항목 수 '2' != '3'"),
], ids=["role-8-vs-7", "phase-2-vs-3"])
def test_p10b_detail_total(axis, value, reg, detail):
    # oracle (a): 계약 3 `detail` -- `df23-total` 다른 수 -> f"항목 수 {reg!r} != {exp!r}"를 손으로 채운 리터럴
    # (reg = 레지스트리 칸 문자열, exp = 항목에서 센 수의 10진 문자열; 센 수는 _P10B_ROWS_81 주석의 항목 번호).
    rows81 = [(a, v, reg if (a, v) == (axis, value) else c) for a, v, c in _P10B_ROWS_81]
    findings = check_df23(_p10b_registry(_p10b_section8(rows81=rows81)), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-total", f"{axis}:{value}")], findings
    assert findings[0]["detail"] == detail, findings


@pytest.mark.parametrize("row, detail", [
    (("`alpha_fn`", "mod_a.py", "5", "DF-4, DF-19, 신규", "3, 4, 7b"),
     "(항목 수, DF, 담당 Phase) ('5', 'DF-4, DF-19, 신규', '3, 4, 7b') != ('4', 'DF-4, DF-19, 신규', '3, 4, 7b')"),
    (("`alpha_fn`", "mod_a.py", "4", "DF-19, DF-4, 신규", "7b, 4, 3"),
     "(항목 수, DF, 담당 Phase) ('4', 'DF-19, DF-4, 신규', '7b, 4, 3') != ('4', 'DF-4, DF-19, 신규', '3, 4, 7b')"),
], ids=["count", "order"])
def test_p10b_detail_function(row, detail):
    # oracle (a): 계약 3 `detail` -- `df23-function` 다른 칸 -> f"(항목 수, DF, 담당 Phase) {reg!r} != {exp!r}"를 손으로 채운 리터럴
    # (reg = 레지스트리 세 칸 tuple, exp = _P10B_ROWS_82 alpha 행의 계약 1 값).
    findings = check_df23(_p10b_registry(_p10b_section8(rows82=[row] + _P10B_ROWS_82[1:])), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-function", "mod_a.py::alpha_fn")], findings
    assert findings[0]["detail"] == detail, findings


# ---------------------------------------------------------------------------------------------------------------
# df23-section
# ---------------------------------------------------------------------------------------------------------------
def test_p10b_section_missing_title_only_finding():
    # oracle (a): §8 없는 레지스트리 -- 계약 3 "제목 줄이 없으면 이 발견 하나만 내고 다른 규칙은 보지 않는다".
    findings = check_df23(_p10b_registry(None), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-section", "title")], findings


def test_p10b_section_title_without_df23():
    # oracle (a): `## 8.`로 시작하지만 `DF-23`을 담지 않은 제목 -- 계약 3 제목 조건 불충족, title 발견 하나만.
    findings = check_df23(_p10b_registry(_p10b_section8(title="## 8. 부록 -- 기록")), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-section", "title")], findings


def test_p10b_section_df23_title_not_starting_with_8():
    # oracle (a): `DF-23`을 담지만 `## 8.`로 시작하지 않는 제목(`## 9.`) -- 계약 3 제목 조건 불충족, title 발견 하나만.
    findings = check_df23(_p10b_registry(_p10b_section8(title="## 9. DF-23 -- 기록")), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-section", "title")], findings


@pytest.mark.parametrize("piece", ["목록", "measured_at", "8.1", "8.2"])
def test_p10b_section_missing_piece(piece):
    # oracle (a): §8 조각 하나를 뺐다 -- 계약 3 `df23-section`, name = 빠진 것.
    findings = check_df23(_p10b_registry(_p10b_section8(omit=(piece,))), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_names(findings, "df23-section") == [piece], findings


def test_p10b_section_missing_both_tables():
    # oracle (a): 계약 3 "빠진 것마다 발견 하나" -- 8.1·8.2 둘 다 빠지면 df23-section 둘.
    findings = check_df23(_p10b_registry(_p10b_section8(omit=("8.1", "8.2"))), _p10b_inventory(), _P10B_INV_REL)
    assert sorted(_p10b_names(findings, "df23-section")) == ["8.1", "8.2"], findings


@pytest.mark.parametrize("which, hdr81, hdr82", [
    ("8.1", ("축", "값", "수"), _P10B_HDR_82),
    ("8.2", _P10B_HDR_81, ("함수", "파일", "수", "DF", "담당 Phase")),
    ("8.2", _P10B_HDR_81, ("파일", "함수", "항목 수", "DF", "담당 Phase")),
], ids=["81-header-differs", "82-header-differs", "82-columns-swapped"])
def test_p10b_section_header_differs(which, hdr81, hdr82):
    # oracle (a): card '거부해야 할 입력' "§8.2 표 머리 다름" -- 소절 아래 계약 1 표 머리를 가진 표가 없다 -> `df23-section`, name = 소절.
    findings = check_df23(_p10b_registry(_p10b_section8(hdr81=hdr81, hdr82=hdr82)), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_names(findings, "df23-section") == [which], findings


# ---------------------------------------------------------------------------------------------------------------
# df23-path / df23-measured-at
# ---------------------------------------------------------------------------------------------------------------
def test_p10b_path_mismatch():
    # oracle (a): `목록:` 줄 경로만 다르게 -- 계약 3 `df23-path`, name = 레지스트리 쪽 값.
    other = "docs/an/other_inv.json"
    findings = check_df23(_p10b_registry(_p10b_section8(path=other)), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-path", other)], findings


def test_p10b_path_follows_inventory_rel_argument():
    # oracle (a): 같은 레지스트리에 inventory_rel 인자만 다르게 -- 비교 기준은 인자(계약 3).
    findings = check_df23(_p10b_registry(_p10b_section8()), _p10b_inventory(), "docs/an/moved.json")
    assert _p10b_pairs(findings) == [("df23-path", _P10B_INV_REL)], findings


def test_p10b_measured_at_mismatch():
    # oracle (a): card '거부해야 할 입력' "measured_at 한 글자 다름" -- `df23-measured-at`, name = 레지스트리 쪽 값.
    off = _P10B_MEASURED[:-1] + "8"
    assert off != _P10B_MEASURED
    findings = check_df23(_p10b_registry(_p10b_section8(measured=off)), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-measured-at", off)], findings


def test_p10b_measured_at_follows_inventory():
    # oracle (a): 레지스트리는 그대로, 목록 measured_at만 다르게 -- 비교 기준은 목록 값(계약 3).
    findings = check_df23(_p10b_registry(_p10b_section8()), _p10b_inventory(measured_at="f" * 40), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-measured-at", _P10B_MEASURED)], findings


# ---------------------------------------------------------------------------------------------------------------
# df23-total
# ---------------------------------------------------------------------------------------------------------------
def _p10b_rows81_without(axis, value):
    return [r for r in _P10B_ROWS_81 if (r[0], r[1]) != (axis, value)]


def _p10b_rows81_replace(axis, value, n):
    return [(a, v, n if (a, v) == (axis, value) else c) for a, v, c in _P10B_ROWS_81]


@pytest.mark.parametrize("rows81, name", [
    (_p10b_rows81_without("phase", "7a"), "phase:7a"),                    # phase 값 행 하나 빠짐
    (_p10b_rows81_without("role", _P10B_MESSAGE), "role:" + _P10B_MESSAGE),  # role 값 행 하나 빠짐
    (_P10B_ROWS_81 + [("phase", "6c", "1")], "phase:6c"),                 # 목록에 없는 값 행
    (_P10B_ROWS_81 + [("phase", "6b", "0")], "phase:6b"),                 # 개수 0인 값의 행(계약 1: 없어야 한다)
    (_p10b_rows81_replace("role", _P10B_BEHAVIOR, "8"), "role:" + _P10B_BEHAVIOR),  # 수 1 차이(7 -> 8)
    (_p10b_rows81_replace("phase", "해당 없음", "2"), "phase:해당 없음"),   # 수 1 차이(3 -> 2)
    (_P10B_ROWS_81 + [("phase", "3", "1")], "phase:3"),                   # 같은 (축, 값) 두 번(두 번째 행이 발견)
], ids=["missing-phase-row", "missing-role-row", "extra-row", "zero-count-row", "role-count-off",
        "phase-count-off", "duplicate-row"])
def test_p10b_total_finds(rows81, name):
    # oracle (a): §8.1 행 집합 하나만 어긋나게 구성 -- 계약 3 `df23-total` 하나, name = `<축>:<값>`. §8.2는 그대로라 다른 규칙 0.
    findings = check_df23(_p10b_registry(_p10b_section8(rows81=rows81)), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-total", name)], findings


def test_p10b_total_counts_items_not_rows82():
    # oracle (a): 항목 하나(메시지뿐 9)를 목록에서 뺐다 -- items에서 센 값이 role 메시지뿐 1, phase 해당 없음 2가 되어
    # 기존 §8.1의 두 행이 다르다. §8.2(동작 항목만)는 그대로 맞다.
    findings = check_df23(_p10b_registry(_p10b_section8()), _p10b_inventory(_P10B_ITEMS[:8]), _P10B_INV_REL)
    assert _p10b_pairs(findings) == sorted([("df23-total", "role:" + _P10B_MESSAGE), ("df23-total", "phase:해당 없음")]), findings


# ---------------------------------------------------------------------------------------------------------------
# df23-function
# ---------------------------------------------------------------------------------------------------------------
_P10B_ALPHA = _P10B_ROWS_82[0]


def _p10b_rows82_alpha(**cells):
    """`alpha_fn` 행의 칸만 바꾼 §8.2 행들."""
    idx = {"fn": 0, "file": 1, "n": 2, "df": 3, "ph": 4}
    row = list(_P10B_ALPHA)
    for k, v in cells.items():
        row[idx[k]] = v
    return [tuple(row)] + _P10B_ROWS_82[1:]


@pytest.mark.parametrize("rows82, names", [
    (_P10B_ROWS_82[:2], ["mod_b.py::<module>"]),                                             # 묶음 하나 빠짐
    (_P10B_ROWS_82 + [("`delta_fn`", "mod_b.py", "1", "DF-31", "해당 없음")], ["mod_b.py::delta_fn"]),  # 메시지뿐 함수의 행
    (_P10B_ROWS_82 + [("`zeta_fn`", "mod_a.py", "1", "신규", "4")], ["mod_a.py::zeta_fn"]),  # 목록에 없는 (함수, 파일)
    (_p10b_rows82_alpha(n="5"), ["mod_a.py::alpha_fn"]),                                     # 항목 수 1 차이
    (_p10b_rows82_alpha(df="DF-4, DF-19"), ["mod_a.py::alpha_fn"]),                          # DF 칸에 신규 빠짐
    (_p10b_rows82_alpha(df="DF-19, DF-4, 신규"), ["mod_a.py::alpha_fn"]),                    # DF 번호가 정수 오름차순이 아님
    (_p10b_rows82_alpha(df="신규, DF-4, DF-19"), ["mod_a.py::alpha_fn"]),                    # 신규가 끝이 아님
    (_p10b_rows82_alpha(df="DF-4, DF-19, DF-19, 신규"), ["mod_a.py::alpha_fn"]),             # DF 번호 중복
    (_p10b_rows82_alpha(ph="7b, 4, 3"), ["mod_a.py::alpha_fn"]),                             # 담당 Phase가 문자열 오름차순이 아님
    (_p10b_rows82_alpha(ph="3, 4"), ["mod_a.py::alpha_fn"]),                                 # 담당 Phase 하나 빠짐
    (_P10B_ROWS_82 + [_P10B_ALPHA], ["mod_a.py::alpha_fn"]),                                 # 같은 (함수, 파일) 두 번
], ids=["missing-group", "message-only-function-row", "unknown-row", "count-off", "df-missing-new",
        "df-not-int-order", "df-new-not-last", "df-duplicate", "phase-not-str-order", "phase-missing",
        "duplicate-row"])
def test_p10b_function_finds(rows82, names):
    # oracle (a): §8.2 행 집합 하나만 어긋나게 구성 -- 계약 3 `df23-function`, name = `<파일>::<함수>`. §8.1은 그대로라 다른 규칙 0.
    findings = check_df23(_p10b_registry(_p10b_section8(rows82=rows82)), _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == sorted(("df23-function", n) for n in names), findings


def test_p10b_function_wrong_file_cell():
    # oracle (a): `alpha_fn` 행의 파일 칸을 다른 파일 이름으로 -- (함수, 파일) 키가 달라 빠진 행과 남는 행 둘.
    findings = check_df23(_p10b_registry(_p10b_section8(rows82=_p10b_rows82_alpha(file="mod_b.py"))),
                          _p10b_inventory(), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-function", "mod_a.py::alpha_fn"), ("df23-function", "mod_b.py::alpha_fn")], findings


def test_p10b_function_groups_by_file_name():
    # oracle (a): `alpha_fn` 동작 항목 하나를 다른 파일(`ws/mod_b.py`)에 두면 계약 1 묶음 규칙상 (alpha_fn, mod_b.py) 묶음이 새로 생기고
    # (alpha_fn, mod_a.py)는 3항목이 된다 -- 기존 §8.2의 alpha 행은 칸이 다르고 mod_b 행은 빠진 행.
    items = copy.deepcopy(_P10B_ITEMS)
    items[1]["file"] = "ws/mod_b.py"   # 항목 2(phase 3, DF-4)
    findings = check_df23(_p10b_registry(_p10b_section8()), _p10b_inventory(items), _P10B_INV_REL)
    assert _p10b_pairs(findings) == [("df23-function", "mod_a.py::alpha_fn"), ("df23-function", "mod_b.py::alpha_fn")], findings
    # 위 구성에 맞춰 손으로 고친 §8.2: alpha/mod_a = 항목 1,3,4 (DF-19, 신규; 4, 7b), alpha/mod_b = 항목 2 (DF-4; 3) -- 발견 0.
    rows82 = [("`alpha_fn`", "mod_a.py", "3", "DF-19, 신규", "4, 7b"),
              ("`alpha_fn`", "mod_b.py", "1", "DF-4", "3")] + _P10B_ROWS_82[1:]
    findings = check_df23(_p10b_registry(_p10b_section8(rows82=rows82)), _p10b_inventory(items), _P10B_INV_REL)
    assert len(findings) == 0, findings


# ---------------------------------------------------------------------------------------------------------------
# 입력 오류 -> ValueError
# ---------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("inventory", [[], "text", None, 7], ids=["list", "str", "none", "int"])
def test_p10b_value_error_inventory_not_dict(inventory):
    # oracle (a): 계약 3 (o) -- inventory가 dict가 아니다 -> ValueError(TypeError 등으로 새지 않는다).
    with pytest.raises(ValueError):
        check_df23(_p10b_registry(_p10b_section8()), inventory, _P10B_INV_REL)


@pytest.mark.parametrize("items", [{}, "abc", None, ({"file": "x"},)], ids=["dict", "str", "none", "tuple"])
def test_p10b_value_error_items_not_list(items):
    # oracle (a): 계약 3 (o) -- items가 list가 아니다 -> ValueError.
    inv = _p10b_inventory()
    inv["items"] = items
    with pytest.raises(ValueError):
        check_df23(_p10b_registry(_p10b_section8()), inv, _P10B_INV_REL)


@pytest.mark.parametrize("bad", ["x", ["file", "function"], None, 3], ids=["str", "list", "none", "int"])
def test_p10b_value_error_item_not_dict(bad):
    # oracle (a): 계약 3 (o) -- 항목 하나가 dict가 아니다 -> ValueError.
    items = copy.deepcopy(_P10B_ITEMS) + [bad]
    inv = _p10b_inventory()
    inv["items"] = items
    with pytest.raises(ValueError):
        check_df23(_p10b_registry(_p10b_section8()), inv, _P10B_INV_REL)


@pytest.mark.parametrize("key", ["measured_at", "items"])
def test_p10b_value_error_missing_top_key(key):
    # oracle (a): 계약 3 (i) -- 목록에 measured_at·items가 없다.
    inv = _p10b_inventory()
    del inv[key]
    with pytest.raises(ValueError):
        check_df23(_p10b_registry(_p10b_section8()), inv, _P10B_INV_REL)


@pytest.mark.parametrize("key", ["file", "function", "role", "phase", "plan_mapping"])
def test_p10b_value_error_missing_item_key(key):
    # oracle (a): 계약 3 (ii) -- 항목 하나에 필드 하나가 없다(메시지뿐 항목 8에서 빼도 마찬가지 -- 모든 항목이 대상).
    items = copy.deepcopy(_P10B_ITEMS)
    del items[7][key]
    with pytest.raises(ValueError):
        check_df23(_p10b_registry(_p10b_section8()), _p10b_inventory(items), _P10B_INV_REL)


@pytest.mark.parametrize("index", [4, 8], ids=["behavior-item", "message-item"])
def test_p10b_value_error_empty_function(index):
    # oracle (a): 계약 3 (iii) -- function 빈 문자열(역할 구분 없이 모든 항목).
    items = copy.deepcopy(_P10B_ITEMS)
    items[index]["function"] = ""
    with pytest.raises(ValueError):
        check_df23(_p10b_registry(_p10b_section8()), _p10b_inventory(items), _P10B_INV_REL)


def test_p10b_value_error_ambiguous_file_name():
    # oracle (a): 계약 3 (iv) -- 서로 다른 file 값(`pkg/x/mod_a.py`, `other/mod_a.py`)이 같은 마지막 경로 성분.
    items = copy.deepcopy(_P10B_ITEMS)
    items.append(_p10b_item("other/mod_a.py", "theta_fn", _P10B_MESSAGE, "해당 없음", "신규"))
    with pytest.raises(ValueError):
        check_df23(_p10b_registry(_p10b_section8()), _p10b_inventory(items), _P10B_INV_REL)


@pytest.mark.parametrize("mapping", ["기타", "df-19", "(DF-19)", "계획 DF-19", "DF-", " 신규"],
                         ids=["other-word", "lowercase-df", "paren-first", "df-not-at-start", "df-no-number", "space-new"])
def test_p10b_value_error_behavior_mapping(mapping):
    # oracle (a): 계약 3 (v) -- 동작 항목 plan_mapping이 `^DF-\d+`에도 맞지 않고 `신규`로도 시작하지 않는다.
    items = copy.deepcopy(_P10B_ITEMS)
    items[5]["plan_mapping"] = mapping
    with pytest.raises(ValueError):
        check_df23(_p10b_registry(_p10b_section8()), _p10b_inventory(items), _P10B_INV_REL)


# ---------------------------------------------------------------------------------------------------------------
# CLI main(argv) --df23-inventory: 합성 루트
# ---------------------------------------------------------------------------------------------------------------
_P10B_ENGINE_SRC = f"def {_P10B_KEPT}():\n    return 1\n"


def _p10b_make_root(base, registry_text, inventory=None, inv_rel=_P10B_INV_REL):
    """base/repo를 저장소 루트로: 엔진 파일 하나, 레지스트리(docs/reg.md), 목록 JSON(inv_rel; inventory가 None이면 쓰지 않음)."""
    root = base / "repo"
    files = {str(_P10B_ASSETS_REL / "engine_p10b.py"): _P10B_ENGINE_SRC, "docs/reg.md": registry_text}
    if inventory is not None:
        files[inv_rel] = json.dumps(inventory, ensure_ascii=False)
    for rel, text in files.items():
        p = root.joinpath(*pathlib.PurePosixPath(rel.replace("\\", "/")).parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root, root / "docs" / "reg.md", root.joinpath(*pathlib.PurePosixPath(inv_rel).parts)


def _p10b_argv(root, registry, inv=None, extra=()):
    """main에 줄 argv(호출은 test 본문)."""
    argv = ["--registry", str(registry), "--root", str(root)]
    if inv is not None:
        argv += ["--df23-inventory", str(inv)]
    return argv + list(extra)


def _p10b_clean_argv(tmp_path):
    """exit 2 test의 짝: 다른 하위 디렉터리에 정상 입력을 만들고 같은 인자 모양의 argv를 돌려준다(호출·판정은 test 본문)."""
    root, reg, inv = _p10b_make_root(tmp_path / "ok", _p10b_registry(_p10b_section8()), _p10b_inventory())
    return _p10b_argv(root, reg, inv)


def _p10b_json_lines(text):
    recs = []
    for ln in text.splitlines():
        ln = ln.strip()
        if ln.startswith("{"):
            recs.append(json.loads(ln))
    return recs


def test_p10b_cli_clean_exit_0(tmp_path, capsys):
    # oracle (a): 기존 규칙 발견 0 + 계약 1 §8이 목록과 같다 -- 계약 4 exit 0, 발견 줄 없음, 마지막 줄 `reg_check: 발견 0`.
    rc = main(_p10b_clean_argv(tmp_path))
    out = capsys.readouterr().out
    recs = _p10b_json_lines(out)
    assert rc == 0
    assert len(recs) == 0, recs
    assert out.splitlines()[-1] == _P10B_CLEAN_LINE, out


def test_p10b_cli_without_option_keeps_old_behavior(tmp_path, capsys):
    # oracle (d): card '거부해야 할 입력' 끝 "`--df23-inventory` 없이 §8 없는 레지스트리 -> 기존 규칙만(발견 0이면 exit 0)".
    root, reg, _ = _p10b_make_root(tmp_path, _p10b_registry(None))
    rc = main(_p10b_argv(root, reg))
    out = capsys.readouterr().out
    recs = _p10b_json_lines(out)
    assert rc == 0
    assert len(recs) == 0, recs
    assert out.splitlines()[-1] == _P10B_CLEAN_LINE, out


def test_p10b_cli_missing_section8_exit_1(tmp_path, capsys):
    # oracle (a): 같은 §8 없는 레지스트리에 --df23-inventory를 주면 `df23-section` title 발견, exit 1, 줄마다 키 넷.
    root, reg, inv = _p10b_make_root(tmp_path, _p10b_registry(None), _p10b_inventory())
    rc = main(_p10b_argv(root, reg, inv))
    recs = _p10b_json_lines(capsys.readouterr().out)
    assert [(r["rule"], r["name"]) for r in recs] == [("df23-section", "title")], recs
    assert all(set(r) == _P10B_RECORD_KEYS for r in recs), recs
    assert rc == 1


def test_p10b_cli_inventory_rel_is_root_relative_slash_path(tmp_path, capsys):
    # oracle (a): 계약 4 inventory_rel = 루트 기준 상대 경로를 `/`로 이은 것. 목록을 더 깊은 하위 경로에 두고 §8 `목록:`에 그 `/` 경로를
    # 적으면 exit 0, 다른 경로(앞 디렉터리 하나 빠짐)를 적으면 `df23-path`(name = 레지스트리 쪽 값), exit 1.
    deep = "docs/an/deeper/inv_p10b.json"
    root, reg, inv = _p10b_make_root(tmp_path / "a", _p10b_registry(_p10b_section8(path=deep)), _p10b_inventory(), deep)
    rc = main(_p10b_argv(root, reg, inv))
    recs = _p10b_json_lines(capsys.readouterr().out)
    assert len(recs) == 0, recs
    assert rc == 0
    wrong = "docs/an/inv_p10b.json"
    root, reg, inv = _p10b_make_root(tmp_path / "b", _p10b_registry(_p10b_section8(path=wrong)), _p10b_inventory(), deep)
    rc = main(_p10b_argv(root, reg, inv))
    recs = _p10b_json_lines(capsys.readouterr().out)
    assert [(r["rule"], r["name"]) for r in recs] == [("df23-path", wrong)], recs
    assert rc == 1


def test_p10b_cli_appends_after_existing_findings(tmp_path, capsys):
    # oracle (a): 계약 4 "기존 판정 발견 뒤에 check_df23 발견을 더해" -- §7 이름을 엔진에 없는 이름으로(기존 `stale`)
    # + measured_at 한 글자 다름(`df23-measured-at`). 두 발견 모두, 기존 발견이 앞, exit 1.
    off = _P10B_MEASURED[:-1] + "8"
    text = _p10b_registry(_p10b_section8(measured=off), s7_name="p10b_gone_fn")
    root, reg, inv = _p10b_make_root(tmp_path, text, _p10b_inventory())
    rc = main(_p10b_argv(root, reg, inv))
    recs = _p10b_json_lines(capsys.readouterr().out)
    assert [r["rule"] for r in recs] == ["stale", "df23-measured-at"], recs
    assert rc == 1


def test_p10b_cli_exit_2_missing_inventory_file(tmp_path, capsys):
    # oracle (a): 계약 4 입력 오류 -- 목록 파일 없음 -> exit 2. 짝: 정상 입력 exit 0.
    root, reg, _ = _p10b_make_root(tmp_path / "bad", _p10b_registry(_p10b_section8()))
    absent = root / "docs" / "an" / "absent_p10b.json"
    assert not absent.exists()
    rc_bad = main(_p10b_argv(root, reg, absent))
    capsys.readouterr()
    rc_ok = main(_p10b_clean_argv(tmp_path))
    recs_ok = _p10b_json_lines(capsys.readouterr().out)
    assert rc_bad == 2
    assert rc_ok == 0 and len(recs_ok) == 0, recs_ok


@pytest.mark.parametrize("payload", ["{not json", "[1, 2, 3]", "\"text\"", "null"],
                         ids=["not-json", "top-list", "top-string", "top-null"])
def test_p10b_cli_exit_2_bad_inventory_json(tmp_path, capsys, payload):
    # oracle (a): 계약 4 입력 오류 -- JSON 아님·최상위가 dict 아님 -> exit 2. 짝: 정상 입력 exit 0.
    root, reg, inv = _p10b_make_root(tmp_path / "bad", _p10b_registry(_p10b_section8()), _p10b_inventory())
    inv.write_text(payload, encoding="utf-8")
    rc_bad = main(_p10b_argv(root, reg, inv))
    capsys.readouterr()
    rc_ok = main(_p10b_clean_argv(tmp_path))
    recs_ok = _p10b_json_lines(capsys.readouterr().out)
    assert rc_bad == 2
    assert rc_ok == 0 and len(recs_ok) == 0, recs_ok


@pytest.mark.parametrize("case", ["empty-function", "missing-phase", "missing-measured-at", "ambiguous-file",
                                  "behavior-mapping-other", "items-not-list", "item-not-dict"])
def test_p10b_cli_exit_2_value_error(tmp_path, capsys, case):
    # oracle (a): card '거부해야 할 입력' "입력 오류 -> ValueError(CLI exit 2)" 사례 + 계약 3 (o) 형 오류. 짝: 정상 입력 exit 0.
    items = copy.deepcopy(_P10B_ITEMS)
    if case == "empty-function":
        items[0]["function"] = ""
    elif case == "missing-phase":
        del items[2]["phase"]
    elif case == "ambiguous-file":
        items.append(_p10b_item("other/mod_b.py", "theta_fn", _P10B_MESSAGE, "해당 없음", "신규"))
    elif case == "behavior-mapping-other":
        items[4]["plan_mapping"] = "기타"
    elif case == "item-not-dict":
        items.append("x")
    inv_obj = _p10b_inventory(items)
    if case == "missing-measured-at":
        del inv_obj["measured_at"]
    elif case == "items-not-list":
        inv_obj["items"] = {"a": 1}
    root, reg, inv = _p10b_make_root(tmp_path / "bad", _p10b_registry(_p10b_section8()), inv_obj)
    rc_bad = main(_p10b_argv(root, reg, inv))
    capsys.readouterr()
    rc_ok = main(_p10b_clean_argv(tmp_path))
    recs_ok = _p10b_json_lines(capsys.readouterr().out)
    assert rc_bad == 2
    assert rc_ok == 0 and len(recs_ok) == 0, recs_ok


def test_p10b_cli_exit_2_inventory_outside_root(tmp_path, capsys):
    # oracle (a): 계약 4 "루트 밖이면 exit 2" -- 목록을 루트(base/repo) 밖 형제 디렉터리에 둔다. 짝: 정상 입력 exit 0.
    root, reg, _ = _p10b_make_root(tmp_path / "bad", _p10b_registry(_p10b_section8()))
    outside = tmp_path / "bad" / "elsewhere" / "inv_p10b.json"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_text(json.dumps(_p10b_inventory(), ensure_ascii=False), encoding="utf-8")
    root_n = os.path.normcase(os.path.realpath(str(root)))
    out_n = os.path.normcase(os.path.realpath(str(outside)))
    assert os.path.commonpath([root_n, out_n]) != root_n   # 구성 확인: 정말 루트 밖
    rc_bad = main(_p10b_argv(root, reg, outside))
    capsys.readouterr()
    rc_ok = main(_p10b_clean_argv(tmp_path))
    recs_ok = _p10b_json_lines(capsys.readouterr().out)
    assert rc_bad == 2
    assert rc_ok == 0 and len(recs_ok) == 0, recs_ok


@pytest.mark.parametrize("extra", [("--p10b-bogus-flag",), ("--p10b-bogus-opt", "v"), ("stray_positional",)],
                         ids=["unknown-flag", "unknown-opt-value", "positional"])
def test_p10b_cli_unknown_argument_returns_2(tmp_path, capsys, extra):
    # oracle (a): 계약 4 "알 수 없는 인자는 SystemExit로 새지 않고 main이 정확히 2를 돌려준다" -- 정상 입력에 알 수 없는 인자만 더함.
    # 짝: 같은 입력 인자 추가 없이 exit 0. SystemExit가 새면 이 test는 오류로 끝난다.
    root, reg, inv = _p10b_make_root(tmp_path / "bad", _p10b_registry(_p10b_section8()), _p10b_inventory())
    rc_bad = main(_p10b_argv(root, reg, inv, extra=extra))
    capsys.readouterr()
    rc_ok = main(_p10b_argv(root, reg, inv))
    recs_ok = _p10b_json_lines(capsys.readouterr().out)
    assert rc_bad == 2
    assert rc_ok == 0 and len(recs_ok) == 0, recs_ok


def test_p10b_cli_script_ascii_stdout_prints_utf8(tmp_path):
    # oracle (a): 계약 4 "PYTHONIOENCODING=ascii로 스크립트를 실행해도 UnicodeEncodeError 없이 exit 0과 UTF-8 바이트 `reg_check: 발견 0`".
    root, reg, inv = _p10b_make_root(tmp_path, _p10b_registry(_p10b_section8()), _p10b_inventory())
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "ascii"
    env["PYTHONUTF8"] = "0"
    proc = subprocess.run(
        [sys.executable, "-B", str(_P10B_TOOLS_DIR / "reg_check.py"),
         "--registry", str(reg), "--root", str(root), "--df23-inventory", str(inv)],
        capture_output=True, env=env, timeout=300)
    assert b"UnicodeEncodeError" not in proc.stderr, proc.stderr
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert proc.stdout.splitlines()[-1] == _P10B_CLEAN_LINE.encode("utf-8"), proc.stdout
