"""Phase 2 P7 계약: 레지스트리 검사 도구 `A/tests/tools/reg_check.py`(20260930-registry-grade-fix).

spec card `docs/02-design/specs/20260930-registry-grade-fix.spec.md` 계약 6과 계약 1·2의 일부를 판정한다. 신규 시그니처(interface card):

* `check(registry_text: str, engine_names: set) -> list` -- 발견 목록.
* `main(argv: list) -> int` -- `--registry <레지스트리 경로> --root <저장소 루트>`. 엔진 정의 이름(`A/*.py` 최상위 def·class와 클래스
  메서드 `Class.method`, `workspaces/run_harness.py` 최상위)을 AST로 모아 판정하고, 발견을 한 줄 JSON(`{"rule", "section", "name",
  "detail"}`)씩 출력한다. 발견 0이면 0, 1개 이상 1, 입력 오류(없는 파일·§7 없음) 2.
* 규칙 `stale`(§7 표 첫 칸의 백틱 이름이 엔진 정의 이름에 없다), `disposition`(§7 표에 `처리` 열이 없거나 값이
  `^보류\\(Phase [0-9]+[a-z]?\\)`에 맞지 않는다), `count`(§1 표의 파일별 D 열 값과 §7 해당 소절 표의 행 수가 다르다, 소절 제목 괄호 수도).

도구는 base에 없으므로 이 파일은 base에서 수집 단계 ImportError(red)이고, 도구와 레지스트리 정정을 병합한 병합본에서 green이다.
계약 1·2의 나머지(옮긴 등급 표·호출자 근거)와 계약 3~5의 문서 내용은 auditor가 본다 -- 기대 문장을 여기서 만들면 자기참조다.

합성 레지스트리의 형식은 실제 레지스트리(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`)를 따른다: §1 제목
`## 1. 집계`와 표 머리 `| 파일 | R0 | R1 | R2 | D | DUP | 비고 |`, §7 제목 `## 7. D -- 운영 경로 호출 0 (배선/삭제 결정 필요)`, 소절
`### <파일> (<수>)`, 표 머리 `| 함수 | 책임 | 이관 목적지 | ... | 비고 |`. `처리` 열의 자리는 spec card가 정하지 않았으므로
'비고' 앞(기본)과 맨 끝 두 자리를 모두 쓴다.

oracle 대조(계획 N3.12.3):

* test_clean_registry_has_no_findings[*] -- (a) 합성 조각: 세 규칙을 모두 만족하도록 구성한 레지스트리(모든 §7 이름이 엔진 이름 집합에
  있고, `처리`가 `보류(Phase n)`, §1 D = 소절 괄호 수 = 행 수). 기대 '발견 0'은 계약 6 규칙 문장에서 나온다.
* test_stale_finds[*] -- (a) 합성 조각: §7 첫 칸 백틱 이름을 엔진 이름 집합에서 빼 두었다. 기대(규칙 `stale`, 그 이름)는 구성으로 정해진다.
* test_stale_ignores[*] -- (a) 합성 조각: spec card '거부해야 할 입력'의 '발견하면 안 되는 것'(백틱 없는 설명 칸의 이름, §7 밖 표의 이름,
  엔진에 있는 `Class.method`)과 규칙 문장이 첫 칸만 본다는 것(설명 칸의 백틱 이름). 기대 `stale` 0.
* test_disposition_finds_missing_column / test_disposition_finds_bad_value[*] -- (a) 합성 조각: `처리` 열 없음, 정규식에 맞지 않는 값
  (`보류` 아닌 값, Phase 없는 값, Phase 번호 없는 값). 기대 규칙 `disposition` 발견은 계약 6 정규식 문장.
* test_disposition_accepts[*] -- (a) 합성 조각: 정규식에 맞는 값(숫자, 숫자+소문자, 뒤에 글이 붙은 값 -- 정규식이 `^`로만 고정). 기대 0.
* test_count_finds[*] -- (a) 합성 조각: §1 D 값·소절 괄호 수·행 수 중 하나만 어긋나게 구성. 기대 규칙 `count` 발견.
* test_count_finds_unmatched_file[*] -- (a) 합성 조각(2차 시도 추가, 1차 V3 생존 변이 두 분기): (1) §7 소절의 파일 행이 §1 표에 없음,
  (2) §1 D 값이 0이 아닌데 그 파일의 §7 소절이 없음. 계약 6 `count` 문장("§1 표의 파일별 D 열 값과 §7 해당 소절 표의 행 수가
  다르다")에서 (1)은 §1 값이 없어 행 수와 같을 수 없고, (2)는 소절 행 수 0이 D 값과 다르다 -- 둘 다 `count` 발견.
* test_main_* -- (a) 합성 루트(tmp_path): 엔진 파일(`skills/analog-gmid-design/assets/*.py`, `workspaces/run_harness.py`)과 레지스트리를
  구성으로 만들어 어떤 이름이 '엔진 정의 이름'인지 정한다(최상위만, 메서드는 `Class.method`, `A/tests/tools/`와 중첩 함수는 아님).
  exit 0/1/2와 JSON 한 줄의 키 넷은 계약 6 문장.
* test_main_on_this_repository_is_clean -- 계약 6 끝 문장 "병합본 레지스트리에 `main`을 돌리면 exit 0(발견 0)".
* test_repository_section7_lacks_r4_names -- 계약 1 문장: `render_report`·`gm_from_fT`·`_optimize_theta_slsqp_block_coordinate`·
  `SharedFingerWCandidate`가 §7에 없다(이름은 계약 1 문장에서 옮겼다). 계약 2(삭제·이관 이름)는 `stale` 규칙 + 위 저장소 판정이 덮는다.

판정하지 않은 것(규칙 문장이 정하지 않음): `section`·`detail` 문자열의 값, `count` 발견의 `name` 값, 발견 순서, 발견 0일 때 JSON이
아닌 요약 줄의 유무.
"""
import json
import pathlib
import sys

import pytest

# contracts -> tests -> assets(A) -> analog-gmid-design -> skills -> 저장소 루트
_TESTS_DIR = pathlib.Path(__file__).resolve().parents[1]
_ASSETS_DIR = _TESTS_DIR.parent
_REPO_ROOT = _ASSETS_DIR.parents[2]
_TOOLS_DIR = _TESTS_DIR / "tools"
_REGISTRY_REL = pathlib.PurePosixPath("docs", "03-analysis", "gain-budget-gmid-sizing.function-registry.md")
_ASSETS_REL = pathlib.PurePosixPath("skills", "analog-gmid-design", "assets")

if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import reg_check  # noqa: E402  (base에 없다 -- red의 근원)

_RECORD_KEYS = {"rule", "section", "name", "detail"}

# ---------------------------------------------------------------------------------------------------------------
# 합성 레지스트리 조립 -- 형식은 실제 레지스트리 §1·§7을 따른다
# ---------------------------------------------------------------------------------------------------------------
_S7_TITLE = "## 7. D -- 운영 경로 호출 0 (배선/삭제 결정 필요)"
_HDR_DEFAULT = ("함수", "책임", "이관 목적지", "처리", "비고")      # 처리 열: 비고 앞
_HDR_DISP_LAST = ("함수", "책임", "이관 목적지", "비고", "처리")    # 처리 열: 맨 끝
_HDR_NO_DISP = ("함수", "책임", "이관 목적지", "비고")              # 처리 열 없음
_OK_DISP = "보류(Phase 3)"

_ENGINE = {"alive_a", "alive_b", "alive_c", "Box", "Box.meth"}


def _md_row(cells):
    return "| " + " | ".join(cells) + " |"


def _table(header, rows):
    lines = [_md_row(header), "|" + "---|" * len(header)]
    lines += [_md_row(r) for r in rows]
    return "\n".join(lines)


def _row(first, disp=_OK_DISP, header=_HDR_DEFAULT, resp="책임 설명", note="비고"):
    """header의 열 이름에 맞춰 한 행을 만든다(`처리` 열이 없으면 disp는 버린다)."""
    by_col = {"함수": first, "책임": resp, "이관 목적지": "목적지", "처리": disp, "비고": note}
    return [by_col[c] for c in header]


def _sub(fname, rows, header=_HDR_DEFAULT, heading_n=None):
    """§7 소절 하나: (파일, 표 머리, 행들, 소절 제목 괄호 수). 괄호 수 기본값은 구성한 행 수."""
    return {"file": fname, "header": header, "rows": rows,
            "heading_n": len(rows) if heading_n is None else heading_n}


def _registry(subs, s1_d=None, before="", after="", s1_omit=(), s1_extra=()):
    """§0 머리 + §1 집계 + (before) + §7 소절들 + (after). §1 D 기본값은 구성한 행 수.

    s1_omit: §1 표에서 뺄 파일 이름들. s1_extra: §7 소절 없이 §1 표에만 더할 (파일, D) 쌍들.
    """
    s1_d = s1_d or {}
    s1_rows = [[s["file"], "10", "5", "1", str(s1_d.get(s["file"], len(s["rows"]))), "2", "표 행 기준"]
               for s in subs if s["file"] not in s1_omit]
    s1_rows += [[f, "10", "5", "1", str(d), "2", "표 행 기준"] for f, d in s1_extra]
    parts = [
        "# 함수 재사용 레지스트리 -- synthetic",
        "",
        "## 0. 사용 규칙 (강제)",
        "",
        "설명 문단.",
        "",
        "## 1. 집계",
        "",
        _table(("파일", "R0", "R1", "R2", "D", "DUP", "비고"), s1_rows),
        "",
    ]
    if before:
        parts += [before, ""]
    parts += [_S7_TITLE, ""]
    for s in subs:
        parts += [f"### {s['file']} ({s['heading_n']})", "", _table(s["header"], s["rows"]), ""]
    if after:
        parts += [after, ""]
    return "\n".join(parts)


def _clean_subs(header=_HDR_DEFAULT):
    return [
        _sub("sizing_recipe.py", [_row("`alive_a`", header=header), _row("`alive_b`", "보류(Phase 6a)", header=header)],
             header=header),
        _sub("stick_diagram.py", [_row("`Box`", "보류(Phase 4)", header=header),
                                  _row("`Box.meth`", header=header)], header=header),
        _sub("기타 모듈", [_row("`alive_c`", header=header)], header=header),
    ]


def _check(text, engine=_ENGINE):
    return reg_check.check(text, set(engine))


def _by_rule(findings, rule):
    return [f for f in findings if f["rule"] == rule]


def assert_no_findings(findings):
    assert findings == [], findings


def assert_rule_names(findings, rule, names):
    """규칙 `rule` 발견의 `name` 집합이 정확히 `names`여야 한다."""
    got = {f["name"] for f in _by_rule(findings, rule)}
    assert got == set(names), findings


def assert_rule_found(findings, rule):
    assert _by_rule(findings, rule), findings


def assert_rule_absent(findings, rule):
    assert _by_rule(findings, rule) == [], findings


# ---------------------------------------------------------------------------------------------------------------
# check(): 발견 0 기준 조각
# ---------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("header", [_HDR_DEFAULT, _HDR_DISP_LAST], ids=["disp-before-note", "disp-last"])
def test_clean_registry_has_no_findings(header):
    # oracle (a): 세 규칙을 모두 만족하도록 구성한 조각 -- 발견 0.
    assert_no_findings(_check(_registry(_clean_subs(header))))


# ---------------------------------------------------------------------------------------------------------------
# stale
# ---------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("first, name", [
    ("`gone_fn`", "gone_fn"),            # 엔진에 없는 함수(삭제·이관된 이름의 모양)
    ("`Box.gone`", "Box.gone"),          # 클래스는 있으나 메서드가 없다
    ("`Ghost.meth`", "Ghost.meth"),      # 메서드 이름은 있으나 다른 클래스
    ("`meth`", "meth"),                  # 메서드를 클래스 없이 적음 -- 엔진 이름은 `Box.meth`뿐
], ids=["missing-function", "missing-method", "other-class-method", "bare-method-name"])
def test_stale_finds(first, name):
    # oracle (a): §7 첫 칸 백틱 이름을 엔진 이름 집합(_ENGINE)에 없게 구성 -- 규칙 `stale`, 그 이름 하나.
    subs = _clean_subs()
    subs[0]["rows"].append(_row(first))
    subs[0]["heading_n"] += 1
    findings = _check(_registry(subs, s1_d={"sizing_recipe.py": 3}))
    assert_rule_names(findings, "stale", {name})
    assert_rule_absent(findings, "count")
    assert_rule_absent(findings, "disposition")


def test_stale_finds_each_name_in_every_subsection():
    # oracle (a): 소절 셋에 하나씩 엔진에 없는 이름 -- 셋 모두 발견(첫 소절만 보는 구현을 거른다).
    subs = _clean_subs()
    for s, nm in zip(subs, ("gone_x", "Gone.y", "gone_z")):
        s["rows"].append(_row(f"`{nm}`"))
        s["heading_n"] += 1
    findings = _check(_registry(subs, s1_d={s["file"]: len(s["rows"]) for s in subs}))
    assert_rule_names(findings, "stale", {"gone_x", "Gone.y", "gone_z"})


_OUTSIDE_TABLE = _table(_HDR_NO_DISP, [["`outside_ghost`", "책임", "목적지", "비고"]])


@pytest.mark.parametrize("case", [
    "plain-name-in-description",
    "backtick-name-in-non-first-cell",
    "table-before-section7",
    "table-after-section7",
    "method-present",
])
def test_stale_ignores(case):
    # oracle (a): spec card '거부해야 할 입력'의 '발견하면 안 되는 것' + 규칙 문장(§7 표 첫 칸만) -- `stale` 0.
    subs = _clean_subs()
    before = after = ""
    if case == "plain-name-in-description":
        subs[0]["rows"][0] = _row("`alive_a`", resp="ghost_plain 을 대신한다")
    elif case == "backtick-name-in-non-first-cell":
        subs[0]["rows"][0] = _row("`alive_a`", note="`ghost_ticked`(삭제됨)와 같은 개념")
    elif case == "table-before-section7":
        before = "## 3. R0 -- 수정 없이 그대로 재사용\n\n### sizing_recipe.py (1)\n\n" + _OUTSIDE_TABLE
    elif case == "table-after-section7":
        after = "## 8. 부록\n\n" + _OUTSIDE_TABLE
    elif case == "method-present":
        pass  # _clean_subs의 `Box.meth`가 엔진 이름 집합에 있다 -- 아래 판정은 그것이 발견이 아님을 본다
    findings = _check(_registry(subs, before=before, after=after))
    assert_rule_absent(findings, "stale")


def test_stale_depends_on_engine_names():
    # oracle (a): 같은 조각에서 엔진 이름 집합만 바꾼다 -- `alive_b`를 빼면 그 이름이 stale.
    findings = _check(_registry(_clean_subs()), engine=_ENGINE - {"alive_b"})
    assert_rule_names(findings, "stale", {"alive_b"})


# ---------------------------------------------------------------------------------------------------------------
# disposition
# ---------------------------------------------------------------------------------------------------------------
def test_disposition_finds_missing_column():
    # oracle (a): 한 소절 표에 `처리` 열이 없다 -- 규칙 `disposition` 발견.
    subs = _clean_subs()
    subs[1] = _sub("stick_diagram.py", [_row("`Box`", header=_HDR_NO_DISP), _row("`Box.meth`", header=_HDR_NO_DISP)],
                   header=_HDR_NO_DISP)
    findings = _check(_registry(subs))
    assert_rule_found(findings, "disposition")
    assert_rule_absent(findings, "stale")
    assert_rule_absent(findings, "count")


@pytest.mark.parametrize("value", [
    "삭제 후보",          # 보류 아닌 값
    "보류",               # Phase 없음
    "보류(Phase)",        # Phase 번호 없음
    "보류(Phase x)",      # 번호가 숫자가 아님
    "보류 (Phase 3)",     # 정규식은 `보류\(` 붙여 쓰기
    "(Phase 3) 보류",     # `^`에 맞지 않음
    "",                   # 빈 칸
], ids=["not-hold", "no-phase", "phase-without-number", "phase-letter-only", "space-before-paren",
        "not-at-start", "empty"])
def test_disposition_finds_bad_value(value):
    # oracle (a): 계약 6 정규식 `^보류\(Phase [0-9]+[a-z]?\)`에 맞지 않는 값 한 칸 -- `disposition` 발견.
    subs = _clean_subs()
    subs[0]["rows"][1] = _row("`alive_b`", value)
    findings = _check(_registry(subs))
    assert_rule_found(findings, "disposition")
    assert_rule_absent(findings, "stale")
    assert_rule_absent(findings, "count")


@pytest.mark.parametrize("value", [
    "보류(Phase 3)",
    "보류(Phase 6a)",
    "보류(Phase 12)",
    "보류(Phase 4) -- 배선 승인 필요",
], ids=["digit", "digit-letter", "two-digits", "trailing-text"])
def test_disposition_accepts(value):
    # oracle (a): 정규식에 맞는 값(`^`로만 고정되어 뒤 글은 허용) -- `disposition` 0.
    subs = _clean_subs()
    subs[0]["rows"][1] = _row("`alive_b`", value)
    assert_rule_absent(_check(_registry(subs)), "disposition")


# ---------------------------------------------------------------------------------------------------------------
# count
# ---------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("case", ["s1-differs", "heading-differs", "rows-differ"])
def test_count_finds(case):
    # oracle (a): §1 D·소절 괄호 수·행 수 셋 중 하나만 다른 값으로 구성 -- 규칙 `count` 발견.
    subs = _clean_subs()          # stick_diagram.py: 행 2
    s1_d = {}
    if case == "s1-differs":
        s1_d = {"stick_diagram.py": 3}                 # 괄호 2, 행 2, §1 3
    elif case == "heading-differs":
        subs[1]["heading_n"] = 5                        # 괄호 5, 행 2, §1 2
    elif case == "rows-differ":
        subs[1]["rows"].append(_row("`alive_c`"))       # 행 3, 괄호 2, §1 2
        s1_d = {"stick_diagram.py": 2}
    findings = _check(_registry(subs, s1_d=s1_d))
    assert_rule_found(findings, "count")
    assert_rule_absent(findings, "stale")
    assert_rule_absent(findings, "disposition")


def test_count_checks_every_file_row():
    # oracle (a): 마지막 파일 행(`기타 모듈`)만 어긋나게 -- 첫 파일만 보는 구현을 거른다.
    findings = _check(_registry(_clean_subs(), s1_d={"기타 모듈": 7}))
    assert_rule_found(findings, "count")


@pytest.mark.parametrize("case", ["section7-file-missing-in-s1", "s1-file-missing-in-section7"])
def test_count_finds_unmatched_file(case):
    # oracle (a): 계약 6 `count` 문장 -- §1 파일별 D 값과 §7 해당 소절 행 수가 다르면 발견.
    # (1) §7 소절 `stick_diagram.py`(행 2)가 있으나 §1 표에 그 파일 행이 없다 -- 비교할 D 값이 없어 행 수 2와 같지 않다.
    # (2) §1 표에 `extra_module.py` D=3이 있으나 §7에 그 소절이 없다 -- 소절 행 수 0이 D 3과 다르다.
    # 나머지 파일은 모두 일치하게 구성했으므로 `count` 발견은 이 불일치에서만 나온다.
    subs = _clean_subs()
    if case == "section7-file-missing-in-s1":
        text = _registry(subs, s1_omit=("stick_diagram.py",))
    else:
        text = _registry(subs, s1_extra=(("extra_module.py", 3),))
    findings = _check(text)
    assert_rule_found(findings, "count")
    assert_rule_absent(findings, "stale")
    assert_rule_absent(findings, "disposition")


# ---------------------------------------------------------------------------------------------------------------
# main(argv): 합성 루트
# ---------------------------------------------------------------------------------------------------------------
_ENGINE_SRC = (
    "import os\n"
    "\n"
    "CONST = 1\n"
    "\n"
    "def alive_a():\n"
    "    def nested_fn():\n"
    "        return 1\n"
    "    return nested_fn()\n"
    "\n"
    "\n"
    "class Box:\n"
    "    def meth(self):\n"
    "        return 2\n"
)
_ENGINE2_SRC = "def alive_b():\n    return 3\n"
_HARNESS_SRC = "def harness_fn():\n    return 4\n"
_TOOLS_SRC = "def moved_fn():\n    return 5\n"


def _make_root(tmp_path, registry_text, extra=None):
    """tmp_path를 저장소 루트로: 엔진 두 파일·run_harness·tests/tools 파일과 레지스트리(docs/reg.md)를 쓴다."""
    files = {
        str(_ASSETS_REL / "engine_one.py"): _ENGINE_SRC,
        str(_ASSETS_REL / "engine_two.py"): _ENGINE2_SRC,
        "workspaces/run_harness.py": _HARNESS_SRC,
        str(_ASSETS_REL / "tests" / "tools" / "moved.py"): _TOOLS_SRC,
        "docs/reg.md": registry_text,
    }
    files.update(extra or {})
    for rel, text in files.items():
        p = tmp_path.joinpath(*pathlib.PurePosixPath(rel.replace("\\", "/")).parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path, tmp_path / "docs" / "reg.md"


def _json_lines(text):
    """출력 가운데 JSON 객체 줄만(발견 0일 때 요약 줄의 유무는 판정하지 않는다)."""
    recs = []
    for ln in text.splitlines():
        ln = ln.strip()
        if ln.startswith("{"):
            recs.append(json.loads(ln))
    return recs


def _run_main(root, registry, capsys):
    rc = reg_check.main(["--registry", str(registry), "--root", str(root)])
    return rc, _json_lines(capsys.readouterr().out)


def _main_registry(names):
    """§7 한 소절(sizing_recipe.py)에 `names`를 한 행씩."""
    return _registry([_sub("sizing_recipe.py", [_row(f"`{n}`") for n in names])])


def test_main_exit_0_when_all_names_are_engine_definitions(tmp_path, capsys):
    # oracle (a): 레지스트리 이름이 모두 구성한 엔진 정의(A/*.py 최상위 def·class, 메서드 `Class.method`, run_harness 최상위)
    # -- exit 0, 발견 줄 없음.
    root, reg = _make_root(tmp_path, _main_registry(["alive_a", "alive_b", "Box", "Box.meth", "harness_fn"]))
    rc, recs = _run_main(root, reg, capsys)
    assert recs == []
    assert rc == 0


@pytest.mark.parametrize("name", ["moved_fn", "nested_fn", "meth", "CONST", "never_defined"],
                         ids=["only-in-tests-tools", "nested-function", "bare-method", "module-constant", "absent"])
def test_main_exit_1_on_non_engine_name(tmp_path, capsys, name):
    # oracle (a): 계약 6의 '엔진 정의 이름'에 들지 않게 구성한 이름 -- A/tests/tools/에만 있음(A/*.py 밖), def 안 중첩 함수
    # (최상위 아님), 클래스 없이 적은 메서드, 모듈 상수(def·class 아님), 어디에도 없음. exit 1, 그 이름의 stale 한 줄.
    root, reg = _make_root(tmp_path, _main_registry(["alive_a", name]))
    rc, recs = _run_main(root, reg, capsys)
    assert [(r["rule"], r["name"]) for r in recs] == [("stale", name)], recs
    assert rc == 1


def test_main_json_line_has_four_keys(tmp_path, capsys):
    # oracle (a): 발견 둘(stale 하나 + disposition 하나) -- 줄마다 계약 6의 키 넷, exit 1.
    reg_text = _registry([_sub("sizing_recipe.py", [_row("`alive_a`", "삭제 후보"), _row("`gone_fn`")])])
    root, reg = _make_root(tmp_path, reg_text)
    rc, recs = _run_main(root, reg, capsys)
    assert {r["rule"] for r in recs} == {"stale", "disposition"}, recs
    for r in recs:
        assert set(r) == _RECORD_KEYS, r
    assert rc == 1


def test_main_exit_2_on_missing_registry(tmp_path):
    # oracle (a): 레지스트리 파일이 없다 -- 입력 오류 exit 2.
    root, reg = _make_root(tmp_path, _main_registry(["alive_a"]))
    assert reg_check.main(["--registry", str(tmp_path / "docs" / "absent.md"), "--root", str(root)]) == 2


def test_main_exit_2_without_section7_title(tmp_path):
    # oracle (a): §7 제목 줄을 지운 레지스트리(표는 남김) -- 입력 오류 exit 2.
    text = _main_registry(["alive_a"]).replace(_S7_TITLE, "## 6. DUP -- §2 정본으로 통합")
    assert _S7_TITLE not in text
    root, reg = _make_root(tmp_path, text)
    assert reg_check.main(["--registry", str(reg), "--root", str(root)]) == 2


# ---------------------------------------------------------------------------------------------------------------
# 실제 저장소(계약 6 끝·계약 1)
# ---------------------------------------------------------------------------------------------------------------
_REGISTRY_PATH = _REPO_ROOT.joinpath(*_REGISTRY_REL.parts)

# spec card 계약 1 문장에서 옮긴 이름(운영 경로 호출자가 있어 §7에 있으면 안 된다).
_R4_NAMES = ("render_report", "gm_from_fT", "_optimize_theta_slsqp_block_coordinate", "SharedFingerWCandidate")


def test_main_on_this_repository_is_clean(capsys):
    # 계약 6 끝: 병합본 레지스트리·루트에서 발견 0, exit 0.
    assert _REGISTRY_PATH.is_file(), _REGISTRY_PATH
    rc, recs = _run_main(_REPO_ROOT, _REGISTRY_PATH, capsys)
    assert recs == []
    assert rc == 0


def _section7_first_cells(text):
    """레지스트리 §7(`## 7.` 줄부터 다음 `## ` 줄 전까지) 표 행의 첫 칸 문자열."""
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if ln.startswith("## 7.")]
    assert len(starts) == 1, starts
    cells = []
    for ln in lines[starts[0] + 1:]:
        if ln.startswith("## "):
            break
        if ln.startswith("|"):
            cells.append(ln.split("|")[1].strip())
    return cells


def test_repository_section7_lacks_r4_names():
    # 계약 1: R-4 네 이름이 §7 표 첫 칸에 없다. 판정이 공허하지 않도록 §7 표 행이 실제로 있는지도 본다.
    cells = _section7_first_cells(_REGISTRY_PATH.read_text(encoding="utf-8"))
    assert len(cells) > 2, cells
    for name in _R4_NAMES:
        assert f"`{name}`" not in cells, (name, cells)
