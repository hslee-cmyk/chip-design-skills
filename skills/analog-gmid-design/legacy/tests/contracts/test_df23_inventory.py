"""Phase 2 DF-23 전수 목록 계약(20260930-p10-df23-inventory, design 20 §8 P10·§10 E3, 계획 DF-23·N6.2 `2`).

spec card `docs/02-design/specs/20260930-p10-df23-inventory.spec.md` 계약 1~4를 판정한다(계약 5는 `test_phase2_stale_refs.py`).
판정 대상은 오케스트레이터가 쓴 목록 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json`이다.
엔진 소스는 읽지 않는다. 줄 번호·blob·`function` 값의 정의 일치(계약 7)와 `measured_at` 거부 확인(계약 8)은 auditor 측정이라
여기서 다루지 않는다 -- 영구 test는 형식과 계획서·library 대조만 본다.

* 계약 1: 최상위 키 `measured_at`(40자리 소문자 16진)·`scope`·`method`·`vocabulary`·`totals`·`items`. 항목마다 `file`(저장소 루트
  기준 `/` 경로, 범위 파일 8개 중 하나)·`line`·`literal`·`source_line`·`role`(∈ {동작을 정함, 메시지뿐})·`context`(`운영`/`픽스처`로
  시작)·`function`(`<module>` 또는 식별자 하나 또는 `식별자.식별자`, 빈 문자열 없음)·`plan_mapping`·`phase`.
* 계약 2: `phase` ∈ {phase_order에서 `2` 뒤 원소} ∪ {해당 없음}. `해당 없음`이거나 `plan_mapping`이 `^DF-\\d+`가 아니면 비지 않은
  `phase_reason`. `메시지뿐`이면 `phase == 해당 없음`.
* 계약 3: 동작 항목 중 `^DF-(\\d+)`는 N5.2 DF 표에 행이 있고 `phase` ∈ (`수정 Phase` 열 괄호 밖 토큰 - {2}). 그 밖의 동작
  항목은 `신규`로 시작. 레일 규칙: 동작·`context == 운영`·`literal` ∈ R(library `supply_nets` 합집합)이면 `DF-19`/`DF-26`으로 시작.
* 계약 4: `totals.n_items == len(items)`, `by_role`·`by_phase`·`by_plan_mapping`이 항목에서 센 값과 같다.

oracle 대조(계획 N3.12.3):

* test_inventory_top_level / test_inventory_item_fields -- (d) spec card 계약 1 문장(키 이름·값 형식·범위 파일 8개 =
  card 계약 1 `scope` 문장의 A/*.py 7개 + run_harness). 목록 작성자의 판단을 기대값으로 쓰지 않는다.
* test_inventory_phase_closed_set -- (d) 계획서 N6.1 Phase 순서(`merge_gate.read_plan_tables(...).phase_order`, 게이트 표 읽기
  정본)에서 `2` 뒤 원소 + `해당 없음`(card 계약 2).
* test_inventory_phase_matches_df_table -- (d) 계획서 N5.2 DF 표 `수정 Phase` 열(`role_paths.read_section_table` +
  `merge_gate.plan_phase_tokens` 괄호 밖 토큰, card 계약 3). 열 이름은 머리 줄에서 찾는다(추측하지 않는다).
* test_inventory_rail_literals_on_df19_df26 -- (d) base library `A/library/*.topology.json` 최상위 `supply_nets` 합집합 R(card
  계약 3 레일 규칙, B26-1 계약 1과 같은 정의).
* test_inventory_totals -- (a) 불변식: 총계는 항목을 센 값과 같아야 한다(구성으로 정답이 정해짐).
* test_p10_judge_rejects_* / test_p10_judge_accepts_* -- (a) 판정기 자기 점검: card '거부해야 할 입력'의 합성 목록·합성 DF 표·합성
  library를 손으로 만들어, 거부 사유가 구성으로 정해진 입력은 거부되고 통과 입력은 위반 0임을 본다.
"""
import collections
import json
import pathlib
import re
import sys

import pytest

_CONTRACTS_DIR = pathlib.Path(__file__).resolve().parent
# contracts -> tests -> assets -> analog-gmid-design -> skills -> 저장소 루트
_REPO_ROOT = _CONTRACTS_DIR.parents[4]
_GATES_DIR = str(_REPO_ROOT / "tools" / "gates")
if _GATES_DIR not in sys.path:
    sys.path.append(_GATES_DIR)  # 끝에 -- V1은 게이트 코드 캐시를 PYTHONPATH 맨 앞에 둔다(05 §12-7)

import merge_gate  # noqa: E402
import role_paths  # noqa: E402

_P10_INVENTORY = _REPO_ROOT / "docs" / "03-analysis" / "gain-budget-gmid-sizing-20-dead-code-dup" / "df23_inventory.json"
_P10_LIBRARY = _REPO_ROOT / "skills" / "analog-gmid-design" / "assets" / "library"
_P10_PLAN = _REPO_ROOT / merge_gate.PLAN_PATH

# oracle (d) card 계약 1 `scope` 문장: A/*.py 7개 + workspaces/run_harness.py.
_P10_A = "skills/analog-gmid-design/assets/"
_P10_SCOPE_FILES = frozenset([_P10_A + n + ".py" for n in (
    "audit_current_forced", "design_report", "sizing_recipe", "sky130_lut_sweep", "stick_diagram",
    "topology_library", "topology_to_markdown")] + ["workspaces/run_harness.py"])
# oracle (d) card 계약 1.
_P10_TOP_KEYS = ("measured_at", "scope", "method", "vocabulary", "totals", "items")
_P10_ITEM_KEYS = ("file", "line", "literal", "source_line", "role", "context", "function", "plan_mapping", "phase")
_P10_ROLE_ACT = "동작을 정함"
_P10_ROLE_MSG = "메시지뿐"
_P10_NA = "해당 없음"
_P10_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_P10_IDENT = r"[A-Za-z_][A-Za-z0-9_]*"
_P10_FUNC_RE = re.compile(r"^(?:<module>|%s(?:\.%s)?)$" % (_P10_IDENT, _P10_IDENT))
_P10_DF_RE = re.compile(r"^DF-(\d+)")
# oracle (d) card 계약 3: 계획서 N5.2 절 제목 접두와 열 이름.
_P10_DF_SECTION = "### N5.2 "
_P10_DF_PHASE_COL = "수정 Phase"
_P10_DF_ID_COL = "ID"
# oracle (d) card 계약 3 레일 규칙: DF-19 또는 DF-26.
_P10_RAIL_DFS = ("DF-19", "DF-26")


# ---------------------------------------------------------------- 판정기(입력 -> 위반 목록)
def _p10_closed_phases(phase_order):
    """계약 2 닫힌 집합: phase_order에서 `2` 뒤 원소 + `해당 없음`. `2`가 없으면 빈 집합(전부 위반)."""
    order = list(phase_order)
    if "2" not in order:
        return frozenset()
    return frozenset(order[order.index("2") + 1:]) | {_P10_NA}


def _p10_df_phases(plan_text):
    """N5.2 DF 표 -> ({DF 번호(int): 허용 Phase 집합}, 위반 목록). 열 이름이 없으면 위반(표를 쓰지 않는다)."""
    header, rows = role_paths.read_section_table(plan_text, _P10_DF_SECTION)
    cells = [h.strip() for h in header]
    bad = []
    for name in (_P10_DF_ID_COL, _P10_DF_PHASE_COL):
        if cells.count(name) != 1:
            bad.append("DF 표 머리에 %r 열이 정확히 하나 있지 않다: %r" % (name, cells))
    if bad:
        return None, bad
    i_id, i_ph = cells.index(_P10_DF_ID_COL), cells.index(_P10_DF_PHASE_COL)
    table = {}
    for r in rows:
        m = re.match(r"^DF-(\d+)$", r[i_id].strip())
        if not m:
            continue
        outside, _inside = merge_gate.plan_phase_tokens(r[i_ph])
        table[int(m.group(1))] = frozenset(outside) - {"2"}
    return table, []


def _p10_rail_set(library_dir):
    """R = library_dir/*.topology.json 각 파일 최상위 `supply_nets` 리스트 원소의 합집합(선언 없는 파일은 보태지 않음)."""
    rails = set()
    for p in sorted(pathlib.Path(library_dir).glob("*.topology.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        sn = data.get("supply_nets") if isinstance(data, dict) else None
        if isinstance(sn, list):
            rails.update(x for x in sn if isinstance(x, str))
    return frozenset(rails)


def _p10_check_top(inv):
    bad = []
    if not isinstance(inv, dict):
        return ["목록이 객체가 아니다"]
    for k in _P10_TOP_KEYS:
        if k not in inv:
            bad.append("최상위 키 %r 없음" % k)
    ma = inv.get("measured_at")
    if not (isinstance(ma, str) and _P10_SHA_RE.match(ma)):
        bad.append("measured_at %r가 40자리 소문자 16진이 아니다" % (ma,))
    if not isinstance(inv.get("items"), list):
        bad.append("items가 리스트가 아니다")
    if not isinstance(inv.get("totals"), dict):
        bad.append("totals가 객체가 아니다")
    return bad


def _p10_check_items(items, scope_files=_P10_SCOPE_FILES):
    """계약 1 항목 필드·형식."""
    bad = []
    for k, it in enumerate(items):
        tag = "items[%d]" % k
        if not isinstance(it, dict):
            bad.append("%s 객체 아님" % tag)
            continue
        for key in _P10_ITEM_KEYS:
            if key not in it:
                bad.append("%s 키 %r 없음" % (tag, key))
        f = it.get("file")
        if not (isinstance(f, str) and f in scope_files):
            bad.append("%s file %r가 범위 파일(저장소 루트 기준 / 경로) 아님" % (tag, f))
        ln = it.get("line")
        if not (isinstance(ln, int) and not isinstance(ln, bool) and ln >= 1):
            bad.append("%s line %r" % (tag, ln))
        for key in ("literal", "source_line", "plan_mapping"):
            if key in it and not isinstance(it[key], str):
                bad.append("%s %s가 문자열 아님" % (tag, key))
        if it.get("role") not in (_P10_ROLE_ACT, _P10_ROLE_MSG):
            bad.append("%s role %r" % (tag, it.get("role")))
        ctx = it.get("context")
        if not (isinstance(ctx, str) and (ctx.startswith("운영") or ctx.startswith("픽스처"))):
            bad.append("%s context %r" % (tag, ctx))
        fn = it.get("function")
        if not (isinstance(fn, str) and _P10_FUNC_RE.match(fn)):
            bad.append("%s function %r 형식 위반" % (tag, fn))
    return bad


def _p10_check_phase(items, closed):
    """계약 2."""
    bad = []
    for k, it in enumerate(items):
        tag = "items[%d]" % k
        if "phase" not in it:
            bad.append("%s phase 없음" % tag)
            continue
        ph = it["phase"]
        if ph not in closed:
            bad.append("%s phase %r가 닫힌 집합 밖" % (tag, ph))
        pm = it.get("plan_mapping")
        needs_reason = ph == _P10_NA or not (isinstance(pm, str) and _P10_DF_RE.match(pm))
        if needs_reason:
            r = it.get("phase_reason")
            if not (isinstance(r, str) and r.strip()):
                bad.append("%s phase_reason 비었음(phase %r, plan_mapping %r)" % (tag, ph, pm))
        if it.get("role") == _P10_ROLE_MSG and ph != _P10_NA:
            bad.append("%s 메시지뿐인데 phase %r" % (tag, ph))
    return bad


def _p10_check_df(items, df_table, rails):
    """계약 3(동작 항목만). df_table은 `_p10_df_phases`의 첫 값."""
    bad = []
    for k, it in enumerate(items):
        if it.get("role") != _P10_ROLE_ACT:
            continue
        tag = "items[%d]" % k
        pm = it.get("plan_mapping")
        pm = pm if isinstance(pm, str) else ""
        m = _P10_DF_RE.match(pm)
        if m:
            n = int(m.group(1))
            if n not in df_table:
                bad.append("%s plan_mapping %r: 계획 DF 표에 행 없음" % (tag, pm))
            elif it.get("phase") not in df_table[n]:
                bad.append("%s plan_mapping %r phase %r가 수정 Phase %s 밖" % (tag, pm, it.get("phase"),
                                                                          sorted(df_table[n])))
        elif not pm.startswith("신규"):
            bad.append("%s 동작 항목 plan_mapping %r가 DF 번호도 신규도 아님" % (tag, pm))
        if it.get("context") == "운영" and it.get("literal") in rails and not pm.startswith(_P10_RAIL_DFS):
            bad.append("%s 운영 레일 리터럴 %r의 plan_mapping %r가 DF-19/DF-26 아님" % (tag, it.get("literal"), pm))
    return bad


def _p10_check_totals(inv):
    """계약 4."""
    items = inv.get("items") or []
    tot = inv.get("totals") or {}
    bad = []
    if tot.get("n_items") != len(items):
        bad.append("totals.n_items %r != 항목 수 %d" % (tot.get("n_items"), len(items)))
    for key, field in (("by_role", "role"), ("by_phase", "phase"), ("by_plan_mapping", "plan_mapping")):
        counted = dict(collections.Counter(it.get(field) for it in items))
        if tot.get(key) != counted:
            bad.append("totals.%s가 항목에서 센 값과 다르다" % key)
    return bad


def _p10_judge(inv, plan_text, phase_order, rails):
    """계약 1~4 전체 위반 목록."""
    bad = _p10_check_top(inv)
    if bad and not isinstance(inv, dict):
        return bad
    items = inv.get("items") if isinstance(inv.get("items"), list) else []
    bad += _p10_check_items(items)
    bad += _p10_check_phase(items, _p10_closed_phases(phase_order))
    df_table, df_bad = _p10_df_phases(plan_text)
    bad += df_bad
    if df_table is not None:
        bad += _p10_check_df(items, df_table, rails)
    bad += _p10_check_totals(inv)
    return bad


# ---------------------------------------------------------------- 실제 입력
@pytest.fixture(scope="module")
def p10_inventory():
    return json.loads(_P10_INVENTORY.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def p10_plan_text():
    return _P10_PLAN.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def p10_phase_order():
    return tuple(merge_gate.read_plan_tables(str(_P10_PLAN)).phase_order)


def test_inventory_top_level(p10_inventory):
    assert _p10_check_top(p10_inventory) == []
    assert isinstance(p10_inventory["scope"], str) and p10_inventory["scope"].strip()
    assert len(p10_inventory["items"]) > 0


def test_inventory_item_fields(p10_inventory):
    assert _p10_check_items(p10_inventory["items"]) == []


def test_inventory_phase_closed_set(p10_inventory, p10_phase_order):
    closed = _p10_closed_phases(p10_phase_order)
    # 닫힌 집합이 비지 않고 `2`(목록 자체의 Phase)를 담지 않는다 -- 판정이 공허하지 않음.
    assert "2" in p10_phase_order
    assert "2" not in closed and _P10_NA in closed and len(closed) > 1
    assert _p10_check_phase(p10_inventory["items"], closed) == []


def test_inventory_phase_matches_df_table(p10_inventory, p10_plan_text):
    df_table, df_bad = _p10_df_phases(p10_plan_text)
    assert df_bad == []
    assert df_table  # 계획서에서 DF 행을 읽었다
    act_df = [it for it in p10_inventory["items"]
              if it.get("role") == _P10_ROLE_ACT and _P10_DF_RE.match(it.get("plan_mapping") or "")]
    assert act_df  # 대조 대상이 있다(공허하지 않음)
    assert _p10_check_df(p10_inventory["items"], df_table, frozenset()) == []


def test_inventory_rail_literals_on_df19_df26(p10_inventory, p10_plan_text):
    rails = _p10_rail_set(_P10_LIBRARY)
    assert rails  # base library가 supply_nets를 선언한다
    df_table, df_bad = _p10_df_phases(p10_plan_text)
    assert df_bad == []
    assert _p10_check_df(p10_inventory["items"], df_table, rails) == []


def test_inventory_totals(p10_inventory):
    assert _p10_check_totals(p10_inventory) == []


# ---------------------------------------------------------------- 판정기 자기 점검(합성 입력, oracle (a))
_P10_SYN_PLAN = "\n".join([
    "# 합성 계획",
    "",
    "### N5.2 현존 결함 DF",
    "",
    "| ID | 결함 | 위치(함수) | 수정 Phase | 비고 |",
    "|---|---|---|---|---|",
    "| DF-19 | 레일 | x | 4(선언으로 교체, MG1) | |",
    "| DF-23 | 이름 | x | 2(전수 목록), 4(일반 규칙으로 교체) | |",
    "| DF-26 | 레일 | x | 4 | |",
    "| DF-30 | metric | x | 7a | |",
    "| DF-31 | 보상 | x | 7b | |",
    "| DF-34 | spec | x | 4, 7b | |",
    "",
    "### N5.3 다음",
    "",
])
_P10_SYN_PHASE_ORDER = ("0.5", "1", "2", "3", "4", "5", "6a", "6b", "6c", "7a", "7b", "7c")
_P10_SYN_SHA = "0123456789abcdef0123456789abcdef01234567"


def _p10_item(**kw):
    it = {"file": _P10_A + "sizing_recipe.py", "line": 10, "literal": "M1", "source_line": "x = 'M1'",
          "role": _P10_ROLE_ACT, "context": "운영", "function": "f", "plan_mapping": "DF-23", "phase": "4"}
    it.update(kw)
    return it


def _p10_inv(items, **top):
    inv = {"measured_at": _P10_SYN_SHA, "scope": "A/*.py + run_harness", "method": "m", "vocabulary": {},
           "items": items,
           "totals": {"n_items": len(items),
                      "by_role": dict(collections.Counter(i.get("role") for i in items)),
                      "by_phase": dict(collections.Counter(i.get("phase") for i in items)),
                      "by_plan_mapping": dict(collections.Counter(i.get("plan_mapping") for i in items))}}
    inv.update(top)
    return inv


@pytest.fixture()
def p10_syn_rails(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "a.topology.json").write_text(json.dumps({"supply_nets": ["vdd", "gnd"]}), encoding="utf-8")
    (lib / "_TEMPLATE.topology.json").write_text(json.dumps({"netlist": []}), encoding="utf-8")
    return _p10_rail_set(lib)


def _p10_no_phase():
    it = _p10_item()
    del it["phase"]
    return it


_P10_REJECT_ITEMS = [
    pytest.param([_p10_no_phase()], id="phase_missing"),
    pytest.param([_p10_item(phase="2")], id="phase_2"),
    pytest.param([_p10_item(phase="8")], id="phase_8"),
    pytest.param([_p10_item(phase="")], id="phase_empty"),
    pytest.param([_p10_item(plan_mapping="신규", phase=_P10_NA)], id="na_without_reason"),
    pytest.param([_p10_item(plan_mapping="DF-30", phase="4")], id="df30_phase_4"),
    pytest.param([_p10_item(plan_mapping="DF-99", phase="4")], id="df99_not_in_plan"),
    pytest.param([_p10_item(role=_P10_ROLE_MSG, plan_mapping="DF-31", phase="4")], id="message_phase_4"),
    pytest.param([_p10_item(function="")], id="function_empty"),
    pytest.param([_p10_item(function="a.b.c")], id="function_two_dots"),
    pytest.param([_p10_item(literal="vdd", plan_mapping="DF-23", phase="4")], id="rail_on_df23"),
    pytest.param([_p10_item(plan_mapping="기타", phase="4", phase_reason="r")], id="act_not_df_not_new"),
    pytest.param([_p10_item(role="동작")], id="role_outside_set"),
    pytest.param([_p10_item(context="기타")], id="context_outside"),
    pytest.param([_p10_item(file="skills\\analog-gmid-design\\assets\\sizing_recipe.py")], id="file_backslash"),
]


@pytest.mark.parametrize("items", _P10_REJECT_ITEMS)
def test_p10_judge_rejects_item(items, p10_syn_rails):
    assert _p10_judge(_p10_inv(items), _P10_SYN_PLAN, _P10_SYN_PHASE_ORDER, p10_syn_rails) != []


@pytest.mark.parametrize("top", [
    pytest.param({"measured_at": "766b5c2"}, id="measured_at_short"),
    pytest.param({"measured_at": "0123456789ABCDEF0123456789ABCDEF01234567"}, id="measured_at_upper"),
    pytest.param({"measured_at": None}, id="measured_at_none"),
])
def test_p10_judge_rejects_measured_at(top, p10_syn_rails):
    assert _p10_judge(_p10_inv([_p10_item()], **top), _P10_SYN_PLAN, _P10_SYN_PHASE_ORDER, p10_syn_rails) != []


def test_p10_judge_rejects_missing_measured_at(p10_syn_rails):
    inv = _p10_inv([_p10_item()])
    del inv["measured_at"]
    assert _p10_judge(inv, _P10_SYN_PLAN, _P10_SYN_PHASE_ORDER, p10_syn_rails) != []


def test_p10_judge_rejects_n_items_mismatch(p10_syn_rails):
    inv = _p10_inv([_p10_item()])
    inv["totals"]["n_items"] = 2
    assert _p10_judge(inv, _P10_SYN_PLAN, _P10_SYN_PHASE_ORDER, p10_syn_rails) != []


def test_p10_judge_rejects_by_phase_mismatch(p10_syn_rails):
    inv = _p10_inv([_p10_item()])
    inv["totals"]["by_phase"] = {"7a": 1}
    assert _p10_judge(inv, _P10_SYN_PLAN, _P10_SYN_PHASE_ORDER, p10_syn_rails) != []


def test_p10_judge_rejects_unnamed_phase_column(p10_syn_rails):
    """DF 표 머리의 열 이름이 `수정 Phase`가 아니면 판정기가 FAIL(열을 추측하지 않는다)."""
    plan = _P10_SYN_PLAN.replace("| 수정 Phase |", "| 담당 Phase |")
    assert _p10_judge(_p10_inv([_p10_item()]), plan, _P10_SYN_PHASE_ORDER, p10_syn_rails) != []


def test_p10_judge_accepts_valid_synthetic(p10_syn_rails):
    items = [
        _p10_item(plan_mapping="DF-34", phase="4"),
        _p10_item(plan_mapping="DF-34", phase="7b", function="Cls.meth"),
        _p10_item(plan_mapping="신규(픽스처)", phase="3", phase_reason="MOD7 사유", function="<module>"),
        _p10_item(role=_P10_ROLE_MSG, plan_mapping="DF-31(회로별 보상 함수)", phase=_P10_NA, phase_reason="메시지뿐"),
        _p10_item(context="픽스처(테스트 넷리스트)", literal="vdd", plan_mapping="신규(픽스처)", phase="3",
                  phase_reason="픽스처 넷리스트"),
        _p10_item(literal="vdd", plan_mapping="DF-19", phase="4"),
        _p10_item(literal="gnd", plan_mapping="DF-26", phase="4"),
        _p10_item(plan_mapping="DF-23", phase="4"),
        _p10_item(plan_mapping="DF-30(신규 위치)", phase="7a"),
    ]
    assert _p10_judge(_p10_inv(items), _P10_SYN_PLAN, _P10_SYN_PHASE_ORDER, p10_syn_rails) == []


def test_p10_rail_set_from_declarations(p10_syn_rails):
    # (a) 합성 library: 선언한 원소만, 선언 없는 _TEMPLATE은 보태지 않는다, 대소문자 변환 없음.
    assert p10_syn_rails == frozenset({"vdd", "gnd"})


def test_p10_df_table_tokens_drop_phase_2():
    # (a) 합성 표: `2(...), 4(...)` -> {4}, `4, 7b` -> {4, 7b}(괄호 밖 토큰 - {2}).
    table, bad = _p10_df_phases(_P10_SYN_PLAN)
    assert bad == []
    assert table[23] == frozenset({"4"})
    assert table[34] == frozenset({"4", "7b"})
    assert table[19] == frozenset({"4"})
