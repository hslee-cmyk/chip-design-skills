"""[U5 2026-10-08] spec `human.gain_budget_db_override` -- 설계 40 §3.1(필드 표), 41 §5.7(override), 41 §1.7-3(블록 키 = 출력노드
넷 이름을 정렬한 배열), SPEC_CONTRACT 1절·2절·3절(거부 규칙 이름·결과 형식).

기대값 출처(oracle):
* (d) 설계 문장: 형식 `[{block: [넷...], value_db, source}]`, 블록 키는 '정렬한 배열', source 필수.
* (d) 계약 문장: 위반 규칙 이름 `block_not_sorted`·`block_net_unknown`·`block_duplicate`·`type`, 결과 `GainOverrideDecl` 블록 키순 tuple,
  섹션이 없으면 `()`, 결정 대기 표지 불가, kind user_spec 만.
* (a) 구성으로 정답이 정해진 합성 입력: fx_spec_amp 의 넷(n_mid·n_outp·...)을 손으로 골라 넣고, 정렬·중복 여부는 Python 문자열 비교
  (사전순)로 이 test 가 정한다. 피검 로더 출력을 기대값으로 쓰지 않는다.
"""
from __future__ import annotations

import copy
import json

import pytest

from gmid_engine.core import SchemaRejectedError

from gmid_engine.authoring import GainOverrideDecl, SpecSource

GATE = "gain_budget_db_override"    # SPEC_CONTRACT 2절 표 '게이트' 열
US = {"kind": "user_spec", "record": "fixture gain override", "decided": "2026-10-08"}


def _item(block, value_db=20.0, source=None):
    return {"block": list(block), "value_db": value_db, "source": copy.deepcopy(US if source is None else source)}


def _set(sc, items):
    sc.human[GATE] = items


# ---------------------------------------------------------------- 통과

def test_absent_section_is_empty_tuple(sc):
    assert GATE not in sc.human
    assert sc.load().gain_budget_db_override == ()


def test_single_block_loads(sc):
    _set(sc, [_item(["n_outp"], 34.0)])
    (g,) = sc.load().gain_budget_db_override
    assert isinstance(g, GainOverrideDecl)
    assert g.block == ("n_outp",)
    assert g.value_db == 34.0
    assert isinstance(g.source, SpecSource) and g.source.kind == "user_spec"


def test_multi_net_block_and_result_sorted_by_block_key(sc):
    """블록 키순 tuple(계약 3절): JSON 순서 [("n_outp",), ("n_mid", "n_outp"), ("n_inn",)] -> 키 사전순."""
    items = [_item(["n_outp"], 10.0), _item(["n_mid", "n_outp"], 20.0), _item(["n_inn"], 30.0)]
    _set(sc, items)
    got = [(g.block, g.value_db) for g in sc.load().gain_budget_db_override]
    want = sorted((tuple(i["block"]), i["value_db"]) for i in items)   # (a) 키 사전순 = 튜플 비교
    assert got == want
    assert got == [(("n_inn",), 30.0), (("n_mid", "n_outp"), 20.0), (("n_outp",), 10.0)]


def test_negative_and_zero_value_db_are_finite_numbers(sc):
    """value_db 는 '비유한 수'만 거부(계약 2절) -- 0·음수 dB 는 받는다(블록 gain < 1 은 버퍼·감쇠 블록에서 정당)."""
    _set(sc, [_item(["n_mid"], 0.0), _item(["n_outp"], -3.0)])
    assert [g.value_db for g in sc.load().gain_budget_db_override] == [0.0, -3.0]


def test_empty_list_is_empty_tuple(sc):
    _set(sc, [])
    assert sc.load().gain_budget_db_override == ()


# ---------------------------------------------------------------- 거부 (모양 + 규칙 이름)

def test_block_not_sorted(sc):
    assert "n_outp" > "n_mid"                                   # (a) 입력이 내림차순임을 고정
    _set(sc, [_item(["n_outp", "n_mid"])])
    sc.reject_only("block_not_sorted", GATE)


def test_block_repeated_net_is_not_strictly_increasing(sc):
    _set(sc, [_item(["n_mid", "n_mid"])])
    sc.reject_only("block_not_sorted", GATE)


def test_block_net_unknown(sc):
    _set(sc, [_item(["n_zz_not_in_topology"])])
    sc.reject_only("block_net_unknown", GATE)


def test_block_net_case_mismatch_is_unknown(sc):
    """넷 이름은 대소문자까지 그대로(topology 넷 대소문자 유일 게이트, 설계 40 §3.1) -- N_MID 는 다른 이름."""
    _set(sc, [_item(["N_MID"])])
    sc.reject_only("block_net_unknown", GATE)


def test_block_duplicate(sc):
    _set(sc, [_item(["n_mid", "n_outp"], 10.0), _item(["n_mid", "n_outp"], 12.0)])
    sc.reject_only("block_duplicate", GATE)


@pytest.mark.parametrize("bad", ["40", True, None, [1.0]], ids=["str", "bool", "null", "list"])
def test_value_db_type(sc, bad):
    _set(sc, [_item(["n_mid"], bad)])
    sc.reject_only("type", GATE)


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_value_db_non_finite(sc, token, catalog):
    """비유한 수(계약 2절 type). json 모듈이 읽는 비표준 토큰으로 파일에 직접 쓴다."""
    _set(sc, [_item(["n_mid"], 1.0)])
    path = sc.write_spec(sc.spec)
    text = open(path, encoding="utf-8").read().replace('"value_db": 1.0', '"value_db": ' + token)
    assert ('"value_db": ' + token) in text
    open(path, "w", encoding="utf-8").write(text)
    _reject_raw_file(sc, path, catalog)


@pytest.mark.parametrize("block", ["n_mid", {"n_mid": 1}, [1], ["n_mid", 2]], ids=["str", "obj", "num", "mixed"])
def test_block_shape_type(sc, block):
    _set(sc, [{"block": block, "value_db": 20.0, "source": copy.deepcopy(US)}])
    sc.reject_only("type", GATE)


def test_block_empty_rejected(sc):
    """빈 블록 키는 출력노드가 없는 블록 -- 설계 41 §1.7-3 키는 출력노드 이름 배열이라 받을 수 없다(규칙 이름은 계약이 정하지 않음)."""
    _set(sc, [_item([])])
    d = sc.reject()
    assert d["rejected_gates"] == (GATE,)


@pytest.mark.parametrize("section", [{"block": ["n_mid"], "value_db": 1.0}, "x", 3], ids=["object", "str", "num"])
def test_section_not_list(sc, section):
    _set(sc, section)
    d = sc.reject()
    assert sc.rules(d) == ["type"]


def test_item_not_object(sc):
    _set(sc, [["n_mid"]])
    sc.reject_only("type", GATE)


def test_pending_marker_not_accepted(sc):
    """결정 대기 표지는 받지 않는다(계약 1절 U5 문단; 표지를 받지 않는 자리는 그 섹션의 `type`)."""
    _set(sc, {"pending": "SP-2"})
    d = sc.reject()
    assert "type" in sc.rules(d)


def test_item_unknown_key(sc):
    item = _item(["n_mid"])
    item["block_db"] = 3
    _set(sc, [item])
    sc.reject_only("unknown_key", GATE)


def test_missing_value_db_rejected(sc):
    item = _item(["n_mid"])
    del item["value_db"]
    _set(sc, [item])
    d = sc.reject()
    assert d["rejected_gates"] == (GATE,)


def test_source_missing(sc):
    item = _item(["n_mid"])
    del item["source"]
    _set(sc, [item])
    sc.reject_only("source_missing", GATE)


@pytest.mark.parametrize("src", [{"kind": "pending_spice", "record": "r"}, {"kind": "reference"},
                                 {"kind": "plan_rule", "plan_id": "DEC-03"}], ids=["pending_spice", "reference", "plan_rule"])
def test_source_kind_not_user_spec(sc, src):
    _set(sc, [_item(["n_mid"], source=src)])
    sc.reject_only("source_kind_not_allowed_here", GATE)


def test_each_bad_item_reported_once_load(sc):
    """한 로드에서 위반을 모아 한 번(계약 0절): 정렬 위반 + 미지 넷 + 중복 -> 세 규칙이 함께 나온다."""
    _set(sc, [_item(["n_outp", "n_mid"]), _item(["n_zz"]), _item(["n_inn"]), _item(["n_inn"])])
    d = sc.reject()
    assert sorted(sc.rules(d)) == ["block_duplicate", "block_net_unknown", "block_not_sorted"]
    assert d["rejected_gates"] == (GATE,)


def _reject_raw_file(sc, path, catalog):
    """비유한 토큰(NaN·Infinity)은 JSON 수준 위반 -- SPEC_CONTRACT 0절 'JSON 수준 위반은 json_read 예외 그대로'(gate json_read).
    섹션 게이트까지 가지 않고 읽기에서 거부된다(계약 2절 '비유한 수 -> type' 보다 앞)."""
    from gmid_engine.authoring import load_sizing_spec
    with pytest.raises(SchemaRejectedError) as ei:
        load_sizing_spec(path, sc.topology(), catalog)
    assert dict(ei.value.record.detail)["gate"] == "json_read"


# ---------------------------------------------------------------- topology 무관(이름 전단사)
# (a) metamorphic: fx_spec_amp 의 넷 이름을 순서를 뒤집는 전단사로 바꿔(topology·spec 양쪽, 따옴표로 감싼 토큰 치환) 다시 쓰면,
# 같은 블록이 사상된 이름의 정렬 키로 나온다. 규칙이 회로·넷 이름을 읽지 않는다는 근거(설계 40 §1.2 엔진 원칙).
NET_MAP = {"n_inn": "w9", "n_inp": "w8", "n_mid": "w7", "n_outp": "w6", "n_tail": "w5", "n_bias": "w4", "n_fbk": "w3",
           "n_vcm": "w2", "rail_hi": "w1", "rail_lo": "w0"}


def _rename_text(text):
    for old, new in NET_MAP.items():
        text = text.replace('"%s"' % old, '"%s"' % new)
    return text


def test_bijective_net_rename_keeps_override_result(sc):
    assert len(set(NET_MAP.values())) == len(NET_MAP)
    assert ("n_mid" < "n_outp") and (NET_MAP["n_mid"] > NET_MAP["n_outp"])     # 전단사가 순서를 뒤집는다
    _set(sc, [_item(["n_mid", "n_outp"], 20.0), _item(["n_inn"], 30.0)])
    before = [(g.block, g.value_db) for g in sc.load().gain_budget_db_override]
    # 같은 블록을 새 이름으로 -- 새 이름에서 다시 정렬한 배열로 적는다(블록 키 = 정렬 배열)
    topo_text = _rename_text(json.dumps(sc.topo))
    sc.write_topo(json.loads(topo_text))
    spec = json.loads(_rename_text(json.dumps(sc.spec)))
    for item in spec["human"][GATE]:
        item["block"] = sorted(item["block"])
    sc.spec = spec
    sc.resync_fp()
    after = [(g.block, g.value_db) for g in sc.load().gain_budget_db_override]
    want = sorted((tuple(sorted(NET_MAP[n] for n in b)), v) for b, v in before)
    assert after == want
    assert after == [(("w6", "w7"), 20.0), (("w9",), 30.0)]


def test_bijective_net_rename_keeps_rejection(sc):
    """뒤집힌 순서로 적은 블록은 새 이름에서도 block_not_sorted -- 이름이 아니라 정렬 관계가 규칙이다."""
    topo_text = _rename_text(json.dumps(sc.topo))
    sc.write_topo(json.loads(topo_text))
    sc.spec = json.loads(_rename_text(json.dumps(sc.spec)))
    sc.resync_fp()
    _set(sc, [_item(["w7", "w6"])])
    sc.reject_only("block_not_sorted", GATE)

