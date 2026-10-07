"""반환 `relaxed_pairs[i]["interdig_ok"]` = 반환 audit의 3b 판정(20261001-b26-backfill-interdig-final-audit).

spec card `docs/02-design/specs/20261001-b26-backfill-interdig-final-audit.spec.md` 계약 1을 판정한다.
계약 2(바뀌지 않는 것)·3(기존 test 불변)은 auditor가 base·병합본 대조로 잰다 -- 여기서 base 값을 박지 않는다.

피검: `sizing_recipe.run_matching_safety_with_finger_growth`. `size_transistor`·`gm_gds_ratio`는 입력(W0·S)을 만드는
데만 쓴다.

oracle 대조(계획 N3.12.3, spec card 'oracle 종류와 출처'):
* 판정 -- (d) 사용자 결정 U-BF, 승인 기록 `20261001-b26-backfill-interdig-fix`: relaxed_pairs[i]["interdig_ok"]는
  반환 audit(euler 정리 뒤 최종 물리 구조)의 3b 판정. 그래서 판정은 같은 반환 안 두 필드의 일치(`is`) 하나다.
  기대값을 True/False 리터럴로 박지 않고, 최종 rows 모양도 단언하지 않는다(rows 불변은 계약 2, auditor 몫).
* 입력 -- (a) 구성. 행 `seg1 = [Ma, Mb, Mp]`는 넷 n2 차수 3, n1·n4·n5 차수 1(홀수 차수 넷 4개)이라 한 trail로
  못 그려(euler-blocked) 정리가 행을 바꾼다. gm/ID 범위 (11.9, 12.1)이 사이징 값 12.0 둘레로 좁아 핑거증가가
  막히고 offset 쌍 (Ma, Mb)가 완화된다(relaxed_pairs에 든다).
* `unresolved_reason` 리터럴은 spec card 계약 1의 반환 자리 목록((i)~(v), 반환 docstring의 관찰 가능한 값)이다 --
  입력이 의도한 반환 자리에 도달했는지 확인하는 용도다.

반환 자리별 test(계약 1 '반환 자리마다 test'):
* (ii) "relaxed_to_layout" -- test_b26bf_in_loop_relaxed_to_layout(m=2, red 증거).
* (v) "max_rounds_exceeded" -- test_b26bf_after_loop_max_rounds_exceeded(m=1, red 증거).
* (iii) "pair_not_found" -- test_b26bf_site_pair_not_found: 둘째 쌍 (Mc, Mx), Mx는 어느 행에도 없음.
* (iv) "no_finger_w" -- test_b26bf_site_no_finger_w: 둘째 쌍 (Mc, Md)의 finger_w=None.
* (iv) "growth_not_applicable" -- test_b26bf_site_growth_not_applicable: 둘째 쌍 (Mc, Md)의 n_fingers가 1·2로 다름.
* (iv) "gm_id_violation" -- 비어 있지 않은 relaxed_pairs와 함께 도달하는 합성 입력을 만들지 못했다(test 없음).
  시도(모두 max_rounds=3, 첫 쌍 (Ma, Mb) offset, gm_id_bounds (11.9, 12.1)):
  - allow_layout_relaxation=False, 쌍 (Ma, Mb)만 → unresolved_reason "gm_id_violation", relaxed_pairs == [] (완화가
    꺼져 CONSISTENT 대상 항목이 없다).
  - allow_layout_relaxation=True(기본)에서 둘째 쌍 (Mc, Md)를 pmos(lut_by_kind에 없음)·서로 다른 행·finger_w 2배 차이·
    seg1과 같은 행으로 둔 4가지 → 모두 "relaxed_to_layout", relaxed_pairs == [(Ma, Mb), (Mc, Md)] (gm/ID 위반이
    사유로 반환되지 않고 완화됐다).
  이 자리는 spec card 계약 1대로 구조 보장(모든 반환이 정리 함수를 거침)으로 남고 auditor가 병합본 코드에서 확인한다.
* (i) 성공 None -- relaxed_pairs가 비지 않은 채 도달하지 않는 자리(spec card 계약 1 서술 근거)라 test하지 않는다.
  위 시도 중 이 자리에 도달한 입력은 없었다.
* 참고: 기존 test(test_b26pre_existing_paths.py 계약 3(e))가 단언하는 반환 값 "only_3b_failures_left"는 spec card
  계약 1의 반환 자리 목록 (i)~(v)에 없다. relaxed_pairs가 비지 않은 채 이 값에 도달하는 입력은 시도하지 않았다(보고).

V4: 판정 assert는 모두 test 본문에 있다. `_b26bf_` 도우미는 입력을 만들거나 판정에 쓸 체크 목록을 골라 돌려줄 뿐
assert를 담지 않는다.
"""
import json
import pathlib
import sys

# contracts -> tests -> assets(A)
_B26BF_ASSETS = pathlib.Path(__file__).resolve().parents[2]
if str(_B26BF_ASSETS) not in sys.path:
    sys.path.insert(0, str(_B26BF_ASSETS))
import sizing_recipe  # noqa: E402

_B26BF_L = 0.5e-6
_B26BF_GM_ID = 12.0
_B26BF_VDS = 0.6
_B26BF_BOUNDS = (11.9, 12.1)


# ---------------------------------------------------------------- 공통 입력(구성 -- oracle (a) 입력)

def _b26bf_sizing(toy_lut):
    """spec card 공통 입력: `r = size_transistor(...)`, `W0 = r.W`, 사이징 항목 `S`(입력 전용)."""
    r = sizing_recipe.size_transistor(gm=200e-6, gm_id=_B26BF_GM_ID, L=_B26BF_L, lut=toy_lut, vds=_B26BF_VDS)
    w0 = r.W
    s = {
        "ID": r.ID, "W": w0, "L": _B26BF_L, "gm": r.gm, "gm_id": _B26BF_GM_ID,
        "gds": r.gm / toy_lut.gm_gds_ratio(_B26BF_GM_ID, _B26BF_L, _B26BF_VDS, 0.0),
        "kind": "nmos", "vds": _B26BF_VDS, "vsb": 0.0,
    }
    return w0, s


def _b26bf_t(name, source, drain, gate, finger_w, stack_id, n_fingers=1):
    return sizing_recipe.Transistor(name, "nmos", source=source, drain=drain, gate=gate,
                                    n_fingers=n_fingers, finger_w=finger_w, stack_id=stack_id)


def _b26bf_seg1(w0):
    """행 seg1 = [Ma, Mb, Mp]: n2 차수 3, n1·n4·n5 차수 1 -- euler-blocked(구성). Mp가 Ma·Mb 사이에 낀다."""
    return [
        _b26bf_t("Ma", "n2", "n1", "ga", w0, "seg1"),
        _b26bf_t("Mb", "n4", "n2", "gb", w0, "seg1"),
        _b26bf_t("Mp", "n2", "n5", "gp", w0, "seg1"),
    ]


def _b26bf_run(tmp_path, toy_lut, s, rows, matching_pairs, pair_sensitivity, max_rounds):
    """합성 topology를 `tmp_path`에 쓰고 ctx를 만들어 피검 함수를 한 번 부른다(입력 구성만, 판정 없음)."""
    devs = [t for v in rows.values() for t in v]
    doc = {
        "topology_name": "b26bf",
        "schema_version": "2.0",
        "supply_nets": ["vdd", "gnd"],
        "netlist": [{"name": t.name, "kind": t.kind, "source": t.source, "drain": t.drain, "gate": t.gate}
                    for t in devs],
        "symmetry": {"matching_pairs": [], "dispositions": []},
    }
    path = tmp_path / "b26bf.topology.json"
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    ctx = sizing_recipe.SizingContext(sized={t.name: dict(s) for t in devs}, topology_path=str(path))
    return sizing_recipe.run_matching_safety_with_finger_growth(
        rows, matching_pairs, pair_sensitivity, ctx, {"nmos": toy_lut}, {}, [],
        gm_id_bounds=_B26BF_BOUNDS, max_rounds=max_rounds)


def _b26bf_3b_checks(res, a, b):
    """반환 audit 체크 중 이름이 "3b."로 시작하고 f"[{a}/{b}]"를 담은 것만 골라 돌려준다(판정은 test 본문)."""
    return [c for c in res["audit"].checks if c.name.startswith("3b.") and f"[{a}/{b}]" in c.name]


# ---------------------------------------------------------------- 계약 1 (a)(b) -- red 증거

def test_b26bf_in_loop_relaxed_to_layout(tmp_path, toy_lut):
    """계약 1 (a) 루프 안 경로(반환 자리 (ii)): m=2 → "relaxed_to_layout"이고 CONSISTENT(res).

    oracle 대조: 20261001-b26-backfill-interdig-fix (d) 사용자 결정 -- relaxed_pairs[i]["interdig_ok"]는 반환
    audit(euler 정리 뒤 최종 물리 구조)의 3b 판정. 입력은 (a) 구성(모듈 docstring). "relaxed_to_layout"과 완화 쌍
    목록 [("Ma", "Mb")]는 spec card 계약 1 리터럴.
    """
    w0, s = _b26bf_sizing(toy_lut)
    res = _b26bf_run(tmp_path, toy_lut, s, {"seg1": _b26bf_seg1(w0)},
                     [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, 2)
    assert res["unresolved_reason"] == "relaxed_to_layout"
    rp = res["relaxed_pairs"]
    assert [e["pair"] for e in rp] == [("Ma", "Mb")]
    c3b = _b26bf_3b_checks(res, "Ma", "Mb")
    assert len(c3b) == 1, [c.name for c in res["audit"].checks]
    assert rp[0]["interdig_ok"] is c3b[0].ok


def test_b26bf_after_loop_max_rounds_exceeded(tmp_path, toy_lut):
    """계약 1 (b) 루프 뒤 경로(반환 자리 (v)): m=1 → "max_rounds_exceeded"이고 CONSISTENT(res).

    oracle 대조: 20261001-b26-backfill-interdig-fix (d) 사용자 결정 -- relaxed_pairs[i]["interdig_ok"]는 반환
    audit(euler 정리 뒤 최종 물리 구조)의 3b 판정. 입력은 (a) 구성(모듈 docstring). "max_rounds_exceeded"와 완화 쌍
    목록 [("Ma", "Mb")]는 spec card 계약 1 리터럴.
    """
    w0, s = _b26bf_sizing(toy_lut)
    res = _b26bf_run(tmp_path, toy_lut, s, {"seg1": _b26bf_seg1(w0)},
                     [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, 1)
    assert res["unresolved_reason"] == "max_rounds_exceeded"
    rp = res["relaxed_pairs"]
    assert [e["pair"] for e in rp] == [("Ma", "Mb")]
    c3b = _b26bf_3b_checks(res, "Ma", "Mb")
    assert len(c3b) == 1, [c.name for c in res["audit"].checks]
    assert rp[0]["interdig_ok"] is c3b[0].ok


# ---------------------------------------------------------------- 계약 1 반환 자리 (iii)·(iv)

def test_b26bf_site_pair_not_found(tmp_path, toy_lut):
    """반환 자리 (iii) "pair_not_found": 첫 쌍 (Ma, Mb) 완화 뒤 둘째 쌍 (Mc, Mx)의 Mx가 어느 행에도 없다.

    oracle 대조: 20261001-b26-backfill-interdig-fix (d) 사용자 결정 -- relaxed_pairs[i]["interdig_ok"]는 반환
    audit(euler 정리 뒤 최종 물리 구조)의 3b 판정. 입력은 (a) 구성: seg1(모듈 docstring) + 행 seg2 = [Mc],
    Mx는 입력 rows에 없음. "pair_not_found"는 spec card 계약 1 반환 자리 (iii) 리터럴.
    """
    w0, s = _b26bf_sizing(toy_lut)
    rows = {"seg1": _b26bf_seg1(w0), "seg2": [_b26bf_t("Mc", "vt", "nc", "gc", w0, "seg2")]}
    res = _b26bf_run(tmp_path, toy_lut, s, rows, [("Ma", "Mb"), ("Mc", "Mx")],
                     {("Ma", "Mb"): "offset", ("Mc", "Mx"): "offset"}, 3)
    assert res["unresolved_reason"] == "pair_not_found"
    rp = res["relaxed_pairs"]
    assert [e["pair"] for e in rp] == [("Ma", "Mb")]
    c3b = _b26bf_3b_checks(res, "Ma", "Mb")
    assert len(c3b) == 1, [c.name for c in res["audit"].checks]
    assert rp[0]["interdig_ok"] is c3b[0].ok


def test_b26bf_site_no_finger_w(tmp_path, toy_lut):
    """반환 자리 (iv) "no_finger_w": 첫 쌍 (Ma, Mb) 완화 뒤 둘째 쌍 (Mc, Md)의 finger_w가 None이다.

    oracle 대조: 20261001-b26-backfill-interdig-fix (d) 사용자 결정 -- relaxed_pairs[i]["interdig_ok"]는 반환
    audit(euler 정리 뒤 최종 물리 구조)의 3b 판정. 입력은 (a) 구성: seg1(모듈 docstring) + 행 seg2 = [Mc, Md]
    (공통 source vt, n_fingers 1, finger_w None). "no_finger_w"는 spec card 계약 1 반환 자리 (iv) 리터럴.
    """
    w0, s = _b26bf_sizing(toy_lut)
    rows = {"seg1": _b26bf_seg1(w0),
            "seg2": [_b26bf_t("Mc", "vt", "nc", "gc", None, "seg2"), _b26bf_t("Md", "vt", "nd", "gd", None, "seg2")]}
    res = _b26bf_run(tmp_path, toy_lut, s, rows, [("Ma", "Mb"), ("Mc", "Md")],
                     {("Ma", "Mb"): "offset", ("Mc", "Md"): "offset"}, 3)
    assert res["unresolved_reason"] == "no_finger_w"
    rp = res["relaxed_pairs"]
    assert [e["pair"] for e in rp] == [("Ma", "Mb")]
    c3b = _b26bf_3b_checks(res, "Ma", "Mb")
    assert len(c3b) == 1, [c.name for c in res["audit"].checks]
    assert rp[0]["interdig_ok"] is c3b[0].ok


def test_b26bf_site_growth_not_applicable(tmp_path, toy_lut):
    """반환 자리 (iv) "growth_not_applicable": 첫 쌍 (Ma, Mb) 완화 뒤 둘째 쌍 (Mc, Md)의 n_fingers가 1·2로 다르다.

    oracle 대조: 20261001-b26-backfill-interdig-fix (d) 사용자 결정 -- relaxed_pairs[i]["interdig_ok"]는 반환
    audit(euler 정리 뒤 최종 물리 구조)의 3b 판정. 입력은 (a) 구성: seg1(모듈 docstring) + 행 seg2 = [Mc(n_fingers 1),
    Md(n_fingers 2)](공통 source vt, finger_w W0). "growth_not_applicable"은 spec card 계약 1 반환 자리 (iv) 리터럴.
    """
    w0, s = _b26bf_sizing(toy_lut)
    rows = {"seg1": _b26bf_seg1(w0),
            "seg2": [_b26bf_t("Mc", "vt", "nc", "gc", w0, "seg2", n_fingers=1),
                     _b26bf_t("Md", "vt", "nd", "gd", w0, "seg2", n_fingers=2)]}
    res = _b26bf_run(tmp_path, toy_lut, s, rows, [("Ma", "Mb"), ("Mc", "Md")],
                     {("Ma", "Mb"): "offset", ("Mc", "Md"): "offset"}, 3)
    assert res["unresolved_reason"] == "growth_not_applicable"
    rp = res["relaxed_pairs"]
    assert [e["pair"] for e in rp] == [("Ma", "Mb")]
    c3b = _b26bf_3b_checks(res, "Ma", "Mb")
    assert len(c3b) == 1, [c.name for c in res["audit"].checks]
    assert rp[0]["interdig_ok"] is c3b[0].ok
