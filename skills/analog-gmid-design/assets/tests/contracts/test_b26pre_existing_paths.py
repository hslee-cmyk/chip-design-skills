"""B26-1 선행 test-only card: E6·E7 경로와 차동 후보 trace 루프의 기존 동작 고정(20260930-b26-pre-test-strengthen).

spec card `docs/02-design/specs/20260930-b26-pre-test-strengthen.spec.md` 계약 1~8·10·11을 판정한다.
계약 9(변이 판정)는 auditor가 자기 스크립트로 잰다 -- 여기서 기대값을 박지 않는다.

입력 규칙(계약 8):
* 모든 입력은 합성 넷리스트·합성 topology다(소자 `M..`, 내부 넷 `n..`·`g..`·`vtail`). library 회로를 쓰지 않는다.
* 레일 넷은 `vdd`·`gnd`만 쓰고 topology에 `supply_nets: ["vdd", "gnd"]`·`schema_version: "2.0"`을 선언한다.
* 엔진 비공개 도우미(밑줄 시작 심볼)는 부르지 않는다. `stack_id`는 생성자 키워드로 준다.
* `AuditResult`·`Transistor` 객체를 `==`로 비교하지 않는다 -- 필드·이름 튜플로 비교한다.
* 판정 문장(`assert`)은 모두 `test_b26pre_` 함수 본문에 있다. `_b26pre_` 도우미는 입력을 만들거나 값을 계산해
  돌려줄 뿐 `assert`를 담지 않는다.
* `==` 판정의 한 쪽은 spec card 리터럴이다. `size_transistor` 결과에서 나온 `W0`·`S`는 입력 쪽에만 쓴다.
  같은 피검 출력의 두 값을 서로 `==`로 비교하지 않는다.

oracle 대조(계획 N3.12.3, spec card 'oracle 종류와 출처'):
* 계약 2·4·6·10·11 -- (a) 구성 입력. 넷 차수·후보 키·KCL 엣지·대칭 후보 수·같은 서명 branch 쌍이 넷리스트에서
  손으로 정해진다. 계약 11 (b)의 원소 **순서**만 (c) 기준선 값이다.
* 계약 1·3·5·7 -- (c) 기존 동작 기준선(착수 gate `master`, B26-1 이전 known-good). auditor가 그 기준선에서 독립으로
  다시 잰다. docstring에 값 자체가 없는 리터럴(`unresolved_reason` 3개, `unresolved_pair == "unknown"`,
  `_repair<i>`·`_seg<i>` 행 이름 형식, 계약 1 (d)의 stack_id 리터럴 `"pair_row_repair0_repair0_repair0"`,
  계약 5의 'M1·M2 한 그룹', 계약 7의 항목 모양)은 test 주석에 '(c) 기준선 값'으로 적었다.
* 피검 함수를 불러 기대값을 만들지 않는다. 기대값은 전부 spec card 문장에 적힌 리터럴이다.
"""
import json
import pathlib
import sys

# contracts -> tests -> assets(A)
_B26PRE_ASSETS = pathlib.Path(__file__).resolve().parents[2]
if str(_B26PRE_ASSETS) not in sys.path:
    sys.path.insert(0, str(_B26PRE_ASSETS))
import sizing_recipe  # noqa: E402
import stick_diagram  # noqa: E402

_B26PRE_L = 0.5e-6
_B26PRE_GM_ID = 12.0
_B26PRE_VDS = 0.6


# ---------------------------------------------------------------- 공통 입력(계약 1~3)

def _b26pre_sizing(toy_lut):
    """spec card 공통 입력: `r = size_transistor(...)`, `W0 = r.W`, 사이징 항목 `S`(입력 전용)."""
    r = sizing_recipe.size_transistor(gm=200e-6, gm_id=_B26PRE_GM_ID, L=_B26PRE_L, lut=toy_lut, vds=_B26PRE_VDS)
    w0 = r.W
    s = {
        "ID": r.ID, "W": w0, "L": _B26PRE_L, "gm": r.gm, "gm_id": _B26PRE_GM_ID,
        "gds": r.gm / toy_lut.gm_gds_ratio(_B26PRE_GM_ID, _B26PRE_L, _B26PRE_VDS, 0.0),
        "kind": "nmos", "vds": _B26PRE_VDS, "vsb": 0.0,
    }
    return w0, s


def _b26pre_t(name, kind, source, drain, gate, **kw):
    return sizing_recipe.Transistor(name, kind, source=source, drain=drain, gate=gate, **kw)


def _b26pre_star(w0):
    """`STAR`: 넷 `nx` 차수 3, `na`·`nb`·`nc` 차수 1 -- 홀수 차수 넷 4개(한 trail로 못 그림, 구성)."""
    return [
        _b26pre_t("M1", "nmos", "na", "nx", "g1", n_fingers=1, finger_w=w0, stack_id="row"),
        _b26pre_t("M2", "nmos", "nx", "nb", "g2", n_fingers=1, finger_w=w0, stack_id="row"),
        _b26pre_t("M3", "nmos", "nx", "nc", "g3", n_fingers=1, finger_w=w0, stack_id="row"),
    ]


def _b26pre_pair(w0):
    """`PAIR`: 공통 source `vtail`, gate 다른 차동 쌍."""
    return [
        _b26pre_t("Ma", "nmos", "vtail", "nda", "ga", n_fingers=1, finger_w=w0, stack_id="seg1"),
        _b26pre_t("Mb", "nmos", "vtail", "ndb", "gb", n_fingers=1, finger_w=w0, stack_id="seg1"),
    ]


def _b26pre_metrics():
    return {"pair_area": {"type": "sum_area", "devices": ["Ma", "Mb"]}}


def _b26pre_loose(w0):
    return [{"metric": "pair_area", "op": "<=", "value": 2 * w0 * _B26PRE_L * 3.0}]


def _b26pre_net_entry(t):
    return {"name": t.name, "kind": t.kind, "source": t.source, "drain": t.drain, "gate": t.gate}


def _b26pre_nl(name, kind, source, drain, gate):
    return {"name": name, "kind": kind, "source": source, "drain": drain, "gate": gate}


def _b26pre_write_topology(tmp_path, stem, netlist, symmetry=None, **extra):
    """계약 8 형식의 합성 topology 파일을 `tmp_path`에 쓰고 경로 문자열을 돌려준다."""
    doc = {
        "topology_name": stem,
        "schema_version": "2.0",
        "supply_nets": ["vdd", "gnd"],
        "netlist": netlist,
        "symmetry": symmetry if symmetry is not None else {"matching_pairs": [], "dispositions": []},
    }
    doc.update(extra)
    path = tmp_path / f"{stem}.topology.json"
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return str(path)


def _b26pre_ctx(names, s, topology_path):
    return sizing_recipe.SizingContext(sized={n: dict(s) for n in names}, topology_path=topology_path)


def _b26pre_names(rows):
    """행 dict의 소자 이름을 중복을 지우지 않고 모아 정렬한다."""
    return sorted(t.name for devs in rows.values() for t in devs)


def _b26pre_euler_view(res):
    """계약 3 `EULER_OK(res)`의 두 조건에 쓸 값만 계산해 돌려준다(판정은 test 본문).

    반환: (반환 audit의 `"1. euler["` 체크 `(이름, ok)` 목록, 반환 rows로 만든 stick diagram의 `{행 키: status}`).
    """
    euler = [(c.name, c.ok) for c in res["audit"].checks if c.name.startswith("1. euler[")]
    sticks = stick_diagram.build_stick_diagram([t for v in res["rows"].values() for t in v])
    statuses = {k: st.status for k, st in sticks.items()}
    return euler, statuses


# ---------------------------------------------------------------- 계약 1

def test_b26pre_ofcb_lutless_repair(tmp_path, toy_lut):
    """계약 1: `lut_by_kind` 없는 spec의 bare `repair_matching_safety` 폴백(E6-a).

    oracle 대조: (c) 기존 동작 기준선. 근거 -- (a) 코드 주석(sizing_recipe.py 9363~9367) 'lut_by_kind가 없는 구형
    spec은 ... bare repair_matching_safety()로 폴백'; (b) offset 쌍은 3c 필수, `repair_matching_safety` docstring
    (stick_diagram.py 7555~7557) 'n_fingers가 1이면 dx<=0.5 달성 못 함'; (c) 같은 docstring 7532 행 이름
    `f"{원래행}_repair{i}"`; (d) 코드 주석(9408~9412) 'repaired_rows를 최종 정본으로 승격' + `max_iter` 기본값 3과
    docstring '(4) 다시 (1)로' -- 리터럴 `"pair_row_repair0_repair0_repair0"` 자체는 (c) 기준선 값(spec card 계약 1 (d)).
    빈 문자열 역할 값은 입력 구성이다(자동 채움·L/gm/ID 유도를 막는다).
    """
    w0, s = _b26pre_sizing(toy_lut)
    pair = _b26pre_pair(w0)
    path = _b26pre_write_topology(
        tmp_path, "b26pre_lutless",
        [_b26pre_net_entry(t) for t in pair],
        symmetry={
            "matching_pairs": [{"names": ["Ma", "Mb"], "matching_sensitivity": "offset", "current_forced": False}],
            "dispositions": [],
        },
        device_roles={"Ma": {"gm_id_role": "", "L_role": ""}, "Mb": {"gm_id_role": "", "L_role": ""}},
        sizing_roles={
            "metrics": {"pair_area": {"type": "sum_area", "unit": "m^2", "devices": ["Ma", "Mb"]}},
            "constraints": [{"metric": "pair_area", "op": "<=", "value": 2 * w0 * _B26PRE_L * 3}],
        },
    )
    spec = {
        "known_sizing": {"Ma": s, "Mb": s},
        "min_finger_w": 0.1e-6,
        "max_finger_w": 40e-6,
        "L_min": 0.1e-6,
        "gm_id_bounds": (2.0, 28.0),
        "stack_groups_override": {"pair_row": ["Ma", "Mb"]},
    }
    res = sizing_recipe.optimize_full_circuit_budget(path, spec)
    pr = res["pipeline_result"]
    # (a) bare repair 폴백 -- 수리 결과 키가 있고 핑거증가 키는 없다(주석 9363~9367).
    assert "repaired_rows" in pr
    assert "repaired_audit" in pr
    assert "growth_rounds" not in pr
    # (b) 3c가 핑거 1개로 풀리지 않는다(docstring 7555~7557).
    assert res["audit_ok"] is False
    c3c = [c for c in pr["repaired_audit"].checks if c.name.startswith("3c.")]
    assert len(c3c) == 1, [c.name for c in pr["repaired_audit"].checks]
    assert c3c[0].ok is False
    # (c) 행 이름 `<원래행>_repair<i>`(docstring 7532), 소자 보존(입력 PAIR의 이름 리터럴).
    assert all(k.startswith("pair_row_repair") for k in pr["repaired_rows"]), sorted(pr["repaired_rows"])
    assert _b26pre_names(pr["repaired_rows"]) == ["Ma", "Mb"]
    # (d) 승격 정합: 두 판정 모두 오른쪽은 spec card 리터럴((c) 기준선 값). 두 필드끼리 비교하지 않는다(계약 8).
    assert {t.stack_id for t in pr["transistors"]} == {"pair_row_repair0_repair0_repair0"}
    assert set(pr["repaired_rows"]) == {"pair_row_repair0_repair0_repair0"}


# ---------------------------------------------------------------- 계약 2

def test_b26pre_euler_fixup_group_split(tmp_path, toy_lut):
    """계약 2: euler-blocked 연결 행의 그룹 분할(E6-b, 공개 진입점 경유).

    oracle 대조: (a) 구성 -- `STAR`는 홀수 차수 넷 4개라 trail이 최소 2개 필요하고, gm/ID 범위 (11.9, 12.1)이
    사이징 값 12.0 둘레로 좁아 핑거증가 후보가 검증을 못 통과해 2순위 그룹분할로 간다(정리 함수 docstring).
    '그룹분할은 순수 재배치라 W/n_fingers 불변'(n_fingers 집합 {1} = 입력 STAR의 값)은 docstring·주석 서술.
    행 이름 `row_seg<i>` 형식은 (c) 기준선 값. 어느 소자가 어느 세그먼트에 가는지는 계약이 아니다.
    """
    w0, s = _b26pre_sizing(toy_lut)
    star = _b26pre_star(w0)
    path = _b26pre_write_topology(tmp_path, "b26pre_star", [_b26pre_net_entry(t) for t in star])
    ctx = _b26pre_ctx(["M1", "M2", "M3"], s, path)
    res = sizing_recipe.run_matching_safety_with_finger_growth(
        {"row": star}, [], {}, ctx, {"nmos": toy_lut}, {}, [], gm_id_bounds=(11.9, 12.1))
    rows = res["rows"]
    assert set(rows) == {"row_seg0", "row_seg1"}
    # 중복을 지우지 않은 정렬 목록 비교 한 번이 '겹치지 않음'까지 판정한다(계약 2).
    assert _b26pre_names(rows) == ["M1", "M2", "M3"]
    # 오른쪽 리터럴 -- 각 행이 비지 않음도 함께 판정한다.
    assert {t.stack_id for t in rows["row_seg0"]} == {"row_seg0"}
    assert {t.stack_id for t in rows["row_seg1"]} == {"row_seg1"}
    assert {t.n_fingers for devs in rows.values() for t in devs} == {1}


# ---------------------------------------------------------------- 계약 3

def _b26pre_growth_setup(tmp_path, toy_lut):
    """계약 3 공통: PAIR·STAR를 다 담은 합성 topology 하나(계약 8 허용)."""
    w0, s = _b26pre_sizing(toy_lut)
    path = _b26pre_write_topology(
        tmp_path, "b26pre_pair_star",
        [_b26pre_net_entry(t) for t in _b26pre_pair(w0) + _b26pre_star(w0)])
    return w0, s, path


def test_b26pre_growth_zero_rounds(tmp_path, toy_lut):
    """계약 3(a): 라운드 0개 소진.

    oracle 대조: (c) 기존 동작 기준선. `unresolved_pair == "unknown"`, `unresolved_reason == "max_rounds_exceeded"`,
    행 이름 `seg1_repair...`는 docstring에 없는 반환 리터럴 -- (c) 기준선 값. 루프가 돌지 않아도 마지막 수리 1회와
    정리를 거친다(코드 주석 11784~11786 '모든 반환 지점'). offset 쌍·핑거 1개라 3c 불통(audit.ok False).
    소자 이름 ["Ma", "Mb"]은 입력 PAIR(구성).
    """
    w0, s, path = _b26pre_growth_setup(tmp_path, toy_lut)
    res = sizing_recipe.run_matching_safety_with_finger_growth(
        {"seg1": _b26pre_pair(w0)}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"},
        _b26pre_ctx(["Ma", "Mb"], s, path), {"nmos": toy_lut}, _b26pre_metrics(), _b26pre_loose(w0),
        gm_id_bounds=(2.0, 28.0), max_rounds=0)
    assert res["growth_rounds"] == []
    assert res["unresolved_pair"] == "unknown"
    assert res["unresolved_reason"] == "max_rounds_exceeded"
    assert res["audit"].ok is False
    rows = res["rows"]
    assert "seg1" not in rows
    assert all(k.startswith("seg1_repair") for k in rows), sorted(rows)
    assert _b26pre_names(rows) == ["Ma", "Mb"]


def test_b26pre_growth_zero_rounds_euler(tmp_path, toy_lut):
    """계약 3(b): 라운드 0개 + euler 정리.

    oracle 대조: (c) 기존 동작 기준선 + 코드 주석(11784~11786) '모든 반환 지점에서 euler 정리'.
    `STAR` 행은 구성상 한 trail로 못 그리므로 정리를 거치지 않으면 EULER_OK가 깨진다(구성).
    EULER_OK 둘째 조건은 피검 모듈의 `build_stick_diagram`으로 판정한다(spec card '판정기 독립성 한계').
    """
    w0, s, path = _b26pre_growth_setup(tmp_path, toy_lut)
    res = sizing_recipe.run_matching_safety_with_finger_growth(
        {"seg1": _b26pre_pair(w0), "row": _b26pre_star(w0)}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"},
        _b26pre_ctx(["Ma", "Mb", "M1", "M2", "M3"], s, path), {"nmos": toy_lut}, _b26pre_metrics(),
        _b26pre_loose(w0), gm_id_bounds=(2.0, 28.0), max_rounds=0)
    euler, statuses = _b26pre_euler_view(res)
    # EULER_OK 조건 1: "1. euler[" 체크가 1개 이상이고 전부 ok.
    assert len(euler) >= 1, [c.name for c in res["audit"].checks]
    assert all(ok for _name, ok in euler), euler
    # EULER_OK 조건 2: 반환 rows의 stick diagram이 전부 "ok".
    assert len(statuses) >= 1
    assert all(st == "ok" for st in statuses.values()), statuses


def test_b26pre_growth_already_ok(tmp_path, toy_lut):
    """계약 3(c): 처음부터 통과.

    oracle 대조: (c) 기존 동작 기준선. ratio 쌍은 3c 필수가 아니고(3b만 필수) 같은 행에 인접한 두 소자로 이미
    통과한다(docstring '(2) ok면 성공 종료'). 행·핑거·stack_id가 입력 PAIR 그대로다(구성 -- 리터럴).
    """
    w0, s, path = _b26pre_growth_setup(tmp_path, toy_lut)
    res = sizing_recipe.run_matching_safety_with_finger_growth(
        {"seg1": _b26pre_pair(w0)}, [("Ma", "Mb")], {("Ma", "Mb"): "ratio"},
        _b26pre_ctx(["Ma", "Mb"], s, path), {"nmos": toy_lut}, _b26pre_metrics(), _b26pre_loose(w0),
        gm_id_bounds=(2.0, 28.0))
    assert res["unresolved_pair"] is None
    assert res["unresolved_reason"] is None
    assert res["growth_rounds"] == []
    assert res["relaxed_pairs"] == []
    assert res["audit"].ok is True
    flat = {k: [(t.name, t.n_fingers, t.stack_id) for t in devs] for k, devs in res["rows"].items()}
    assert flat == {"seg1": [("Ma", 1, "seg1"), ("Mb", 1, "seg1")]}


def test_b26pre_growth_pair_not_found(tmp_path, toy_lut):
    """계약 3(d): 실패 쌍의 소자(`Mx`)가 어느 행에도 없음.

    oracle 대조: (c) 기존 동작 기준선. `"pair_not_found"`는 docstring에 없는 반환 리터럴 -- (c) 기준선 값.
    `Mx`가 행에 없음은 입력 구성이다. EULER_OK는 코드 주석(11784~11786) '모든 반환 지점'.
    """
    w0, s, path = _b26pre_growth_setup(tmp_path, toy_lut)
    res = sizing_recipe.run_matching_safety_with_finger_growth(
        {"seg1": _b26pre_pair(w0), "row": _b26pre_star(w0)}, [("Ma", "Mx")], {("Ma", "Mx"): "offset"},
        _b26pre_ctx(["Ma", "Mb", "M1", "M2", "M3"], s, path), {"nmos": toy_lut}, _b26pre_metrics(),
        _b26pre_loose(w0), gm_id_bounds=(2.0, 28.0))
    assert res["unresolved_pair"] == ("Ma", "Mx")
    assert res["unresolved_reason"] == "pair_not_found"
    assert res["growth_rounds"] == []
    assert res["relaxed_pairs"] == []
    euler, statuses = _b26pre_euler_view(res)
    # EULER_OK 조건 1·2(계약 3).
    assert len(euler) >= 1, [c.name for c in res["audit"].checks]
    assert all(ok for _name, ok in euler), euler
    assert len(statuses) >= 1
    assert all(st == "ok" for st in statuses.values()), statuses


def test_b26pre_growth_only_3b_left(tmp_path, toy_lut):
    """계약 3(e): 3c 실패 없음(euler만).

    oracle 대조: (c) 기존 동작 기준선. `"only_3b_failures_left"`는 docstring에 없는 반환 리터럴 -- (c) 기준선 값
    (코드 주석 11823~11826이 3b 실패 없이 이 분기 도달을 인정한다). 매칭 쌍이 없으므로 euler 정리 뒤 audit은 통과.
    """
    w0, s, path = _b26pre_growth_setup(tmp_path, toy_lut)
    res = sizing_recipe.run_matching_safety_with_finger_growth(
        {"row": _b26pre_star(w0)}, [], {},
        _b26pre_ctx(["M1", "M2", "M3"], s, path), {"nmos": toy_lut}, {}, [],
        gm_id_bounds=(2.0, 28.0))
    assert res["unresolved_pair"] is None
    assert res["unresolved_reason"] == "only_3b_failures_left"
    assert res["growth_rounds"] == []
    assert res["audit"].ok is True
    euler, statuses = _b26pre_euler_view(res)
    # EULER_OK 조건 1·2(계약 3).
    assert len(euler) >= 1, [c.name for c in res["audit"].checks]
    assert all(ok for _name, ok in euler), euler
    assert len(statuses) >= 1
    assert all(st == "ok" for st in statuses.values()), statuses


# ---------------------------------------------------------------- 계약 4

_B26PRE_KEY_HUB_GND = ("hub_merge", "nmos", "gnd")
_B26PRE_KEY_HUB_TAIL = ("hub_merge", "nmos", "ntail")
_B26PRE_KEY_MIRROR = ("current_mirror", "nmos", "nb")
_B26PRE_KEY_DIFF = ("diff_pair", "nmos", "ntail")
# 구성으로 정해지는 후보 키 4개(spec card 계약 4, `run_full_circuit_audit_from_topology` docstring의 정의):
# M1·M2 source 공유(gnd) / Ma·Mb source 공유(ntail) / M1·M2 gate 공유(nb) / 레일 아닌 같은 source에 gate 다름(ntail).
_B26PRE_ALL_KEYS = (_B26PRE_KEY_HUB_GND, _B26PRE_KEY_HUB_TAIL, _B26PRE_KEY_MIRROR, _B26PRE_KEY_DIFF)


def _b26pre_full_audit_c3(tmp_path, omit):
    """계약 4 입력으로 전체 감사를 돌려 이름이 `"3."`으로 시작하는 체크 목록을 돌려준다(판정은 test 본문)."""
    netlist = [
        _b26pre_nl("M1", "nmos", "gnd", "nb", "nb"),
        _b26pre_nl("M2", "nmos", "gnd", "nout", "nb"),
        _b26pre_nl("Ma", "nmos", "ntail", "nda", "nga"),
        _b26pre_nl("Mb", "nmos", "ntail", "ndb", "ngb"),
    ]
    dispositions = [
        {"tag": t, "kind": k, "key": n, "category": "real_match", "reason": "b26pre 합성 입력 처분"}
        for (t, k, n) in _B26PRE_ALL_KEYS if (t, k, n) != omit
    ]
    path = _b26pre_write_topology(
        tmp_path, "b26pre_full_audit", netlist,
        symmetry={"matching_pairs": [], "dispositions": dispositions},
        _netlist_sections_structured={"blk": {"devices": ["M1", "M2", "Ma", "Mb"]}},
    )
    result = stick_diagram.run_full_circuit_audit_from_topology(path)
    return [c for c in result.checks if c.name.startswith("3.")]


def test_b26pre_full_audit_all_disposed(tmp_path):
    """계약 4: 4키 전부 처분이면 체크 3 통과. oracle 대조: (a) 구성 -- 후보 키 4개가 넷리스트에서 정해지고 전부 처분됨."""
    c3 = _b26pre_full_audit_c3(tmp_path, None)
    assert len(c3) == 1, [c.name for c in c3]
    assert c3[0].ok is True, c3[0].detail


def test_b26pre_full_audit_mirror_undisposed(tmp_path):
    """계약 4: current_mirror 키 미처분이면 체크 3 실패, detail에 그 키. oracle 대조: (a) 구성(M1·M2 gate 공유 nb)."""
    c3 = _b26pre_full_audit_c3(tmp_path, _B26PRE_KEY_MIRROR)
    assert len(c3) == 1, [c.name for c in c3]
    assert c3[0].ok is False
    assert repr(("current_mirror", "nmos", "nb")) in c3[0].detail, c3[0].detail


def test_b26pre_full_audit_diffpair_undisposed(tmp_path):
    """계약 4: diff_pair 키 미처분이면 체크 3 실패, detail에 그 키. oracle 대조: (a) 구성(레일 아닌 ntail 공유, gate 다름)."""
    c3 = _b26pre_full_audit_c3(tmp_path, _B26PRE_KEY_DIFF)
    assert len(c3) == 1, [c.name for c in c3]
    assert c3[0].ok is False
    assert repr(("diff_pair", "nmos", "ntail")) in c3[0].detail, c3[0].detail


def test_b26pre_full_audit_hub_gnd_undisposed(tmp_path):
    """계약 4: hub_merge(gnd) 키 미처분이면 체크 3 실패, detail에 그 키. oracle 대조: (a) 구성(M1·M2 source 공유 gnd)."""
    c3 = _b26pre_full_audit_c3(tmp_path, _B26PRE_KEY_HUB_GND)
    assert len(c3) == 1, [c.name for c in c3]
    assert c3[0].ok is False
    assert repr(("hub_merge", "nmos", "gnd")) in c3[0].detail, c3[0].detail


# ---------------------------------------------------------------- 계약 5·6 공통 입력

def _b26pre_cas():
    """캐스코드 차동 넷리스트 `CAS`(표기 source→drain)."""
    return [
        _b26pre_t("M1", "nmos", "ntail", "nx1", "ninp"),
        _b26pre_t("M2", "nmos", "ntail", "nx2", "ninn"),
        _b26pre_t("M1c", "nmos", "nx1", "no1", "nvc"),
        _b26pre_t("M2c", "nmos", "nx2", "no2", "nvc"),
        _b26pre_t("M3", "pmos", "vdd", "no1", "nvp"),
        _b26pre_t("M4", "pmos", "vdd", "no2", "nvp"),
        _b26pre_t("M5", "nmos", "gnd", "ntail", "nvb"),
    ]


# ---------------------------------------------------------------- 계약 5

def test_b26pre_resolve_stack_candidates():
    """계약 5: override·vertical_stack_id 선언 없는 회로의 후보 경로(docstring 우선순위 3번, sizing_recipe.py 6507~6509).

    oracle 대조: 반환 계약 `{stack_id: [device_name, ...]}`(소자 정확히 한 번 -- 입력 CAS 이름 리터럴)과
    'kind로 쪼갠 뒤'(그룹마다 kind 하나)는 docstring. 'M1·M2를 함께 담는 그룹이 있다'는 (c) 기준선 값
    (refine_differential_and_mirror_relations docstring의 composite 병합 서술과 모순 없음, 어느 composite인지는
    docstring이 정하지 않는다).
    """
    cas = _b26pre_cas()
    kinds = {t.name: t.kind for t in cas}
    groups = sizing_recipe.resolve_stack_layout(cas, [], {})
    # 중복을 지우지 않은 정렬 목록 비교 한 번이 '정확히 한 번'을 판정한다(계약 5).
    assert sorted(n for devs in groups.values() for n in devs) == ["M1", "M1c", "M2", "M2c", "M3", "M4", "M5"], groups
    for sid, devs in groups.items():
        assert len({kinds[n] for n in devs}) == 1, (sid, devs)
    assert any({"M1", "M2"} <= set(devs) for devs in groups.values()), groups


# ---------------------------------------------------------------- 계약 6

def test_b26pre_vsid_gap_fill_no_ports():
    """계약 6(a): 포트 인자 없음.

    oracle 대조: (a) 구성 -- 2단자 내부 넷 `nx1`(M1–M1c)·`no1`(M1c–M3)의 직렬 KCL 엣지만 `colA`를 전파한다.
    `ntail`은 3단자(M1·M2·M5)라 엣지가 아니다.
    """
    out = stick_diagram.propose_vertical_stack_id_gap_fill(
        _b26pre_cas(), [], {"M1": {"vertical_stack_id": "colA"}})
    assert out["proposals"] == {"M1c": "colA", "M3": "colA"}


def test_b26pre_vsid_gap_fill_ports():
    """계약 6(b): 포트 인자를 주면 differential 관계 M1–M2가 두 컬럼을 잇는다(docstring 2번).

    oracle 대조: (a) 구성 -- 컬럼 {M1,M1c,M3}과 {M2,M2c,M4}가 differential 엣지 M1–M2로 합쳐지고, M5는 3단자 ntail로만
    닿아 혼자 남는다.
    """
    out = stick_diagram.propose_vertical_stack_id_gap_fill(
        _b26pre_cas(), [], {"M1": {"vertical_stack_id": "colA"}},
        inputs=("ninp", "ninn"), outputs=("no1", "no2"), biases=("nvb", "nvc", "nvp"))
    assert out["proposals"] == {"M1c": "colA", "M2": "colA", "M2c": "colA", "M3": "colA", "M4": "colA"}
    assert out["conflicts"] == {}
    assert sorted(sorted(c) for c in out["components_used"]) == [["M1", "M1c", "M2", "M2c", "M3", "M4"], ["M5"]]


# ---------------------------------------------------------------- 계약 7

def test_b26pre_case_collisions(tmp_path):
    """계약 7: 대소문자만 다른 넷(`NQ`·`nq`) 보고.

    oracle 대조: 값 모양 `{lower: {실제 표기, ...}}`은 비공개 함수 docstring(stick_diagram.py 928~930), 그 값이
    `_device_roles_gap_fill_review_needed`의 `case_collisions` 항목으로 실리는 것은 (c) 기준선 동작이다.
    충돌 넷이 `NQ`/`nq` 하나뿐인 것은 입력 구성이다.
    """
    netlist = [
        _b26pre_nl("M1", "nmos", "ntail", "no1", "ninp"),
        _b26pre_nl("M2", "nmos", "ntail", "no2", "ninn"),
        _b26pre_nl("M3", "pmos", "vdd", "no1", "no1"),
        _b26pre_nl("M4", "pmos", "vdd", "no2", "no1"),
        _b26pre_nl("M5", "nmos", "gnd", "ntail", "nvb"),
        _b26pre_nl("M6", "nmos", "gnd", "NQ", "nvb"),
        _b26pre_nl("M7", "nmos", "gnd", "nq", "nvb"),
    ]
    path = _b26pre_write_topology(tmp_path, "b26pre_case", netlist)
    _t, meta = stick_diagram.load_topology(path)
    review = meta["_device_roles_gap_fill_review_needed"] or []
    collisions = [e["case_collisions"] for e in review if isinstance(e, dict) and "case_collisions" in e]
    assert collisions == [{"nq": {"NQ", "nq"}}]


# ---------------------------------------------------------------- 계약 10

def _b26pre_seed_common():
    return [
        _b26pre_nl("M1", "nmos", "ntail", "nd1", "ninp"),
        _b26pre_nl("M2", "nmos", "ntail", "nd2", "ninn"),
        _b26pre_nl("M3", "pmos", "vdd", "nd1", "nbp"),
        _b26pre_nl("M4", "pmos", "vdd", "nd2", "nbp"),
        _b26pre_nl("M5", "nmos", "gnd", "ntail", "nvb"),
    ]


def _b26pre_seed_load(tmp_path, stem, tap_gate, other_gate):
    """계약 10 입력(공통 + 탭 세 소자)으로 `load_topology`를 불러 판정에 쓸 값만 돌려준다(판정은 test 본문).

    반환: (`ROLES(n)` 값 dict -- `Mx1`·`Mx2`·`My`, `af = meta["_device_roles_autofilled"]`,
    `meta["_matching_pairs_needs_review"]` 원소의 `sorted(names)` 목록).
    """
    netlist = _b26pre_seed_common() + [
        _b26pre_nl("Mx1", "nmos", "gnd", "nx1", tap_gate),
        _b26pre_nl("Mx2", "nmos", "gnd", "nx2", tap_gate),
        _b26pre_nl("My", "nmos", "gnd", "ny", other_gate),
    ]
    path = _b26pre_write_topology(tmp_path, stem, netlist)
    _t, meta = stick_diagram.load_topology(path)
    af = meta["_device_roles_autofilled"]
    roles = {n: (af.get(n, {}).get("gm_id_role"), af.get(n, {}).get("L_role")) for n in ("Mx1", "Mx2", "My")}
    review_pairs = [sorted(e["names"]) for e in meta["_matching_pairs_needs_review"]]
    return roles, af, review_pairs


def test_b26pre_seed_tap_p(tmp_path):
    """계약 10(a) `TAP_P`: 탭 두 개(Mx1·Mx2)가 `ninp`, 하나(My)가 `ninn`.

    oracle 대조: (a) 구성 + `find_structural_symmetry_candidates` docstring 규칙 3('정확히 하나면 채택, 0개나 2개
    이상이면 보류')과 씨앗(차동 gate ninp↔ninn 양방향 + vdd/gnd 자기 자신, L 역할 제안 함수 docstring).
    1라운드에서 Mx1·Mx2 중 먼저 처리된 쪽만 My를 채택한다 -- 어느 쪽인지는 계약이 아니다('정확히 하나').
    역할 값 이름 `matching`·`mirror`와 '파트너 없으면 키 없음'은 역할 제안 함수 docstring.
    """
    roles, af, review_pairs = _b26pre_seed_load(tmp_path, "b26pre_tap_p", "ninp", "ninn")
    assert roles["My"] == ("matching", "mirror"), (roles, af.get("My"))
    adopted = [n for n in ("Mx1", "Mx2") if roles[n] == ("matching", "mirror")]
    assert len(adopted) == 1, roles
    x = adopted[0]
    z = "Mx2" if x == "Mx1" else "Mx1"
    assert "gm_id_role" not in af.get(z, {}), af.get(z)
    assert "L_role" not in af.get(z, {}), af.get(z)
    assert sorted([x, "My"]) in review_pairs, review_pairs
    assert sorted([z, "My"]) not in review_pairs, review_pairs


def test_b26pre_seed_tap_n(tmp_path):
    """계약 10(b) `TAP_N`: 탭 입력 넷만 뒤집음(Mx1·Mx2가 `ninn`, My가 `ninp`) -- 씨앗의 반대 방향을 본다.

    oracle 대조: test_b26pre_seed_tap_p와 같다((a) 구성 + docstring 규칙).
    """
    roles, af, review_pairs = _b26pre_seed_load(tmp_path, "b26pre_tap_n", "ninn", "ninp")
    assert roles["My"] == ("matching", "mirror"), (roles, af.get("My"))
    adopted = [n for n in ("Mx1", "Mx2") if roles[n] == ("matching", "mirror")]
    assert len(adopted) == 1, roles
    x = adopted[0]
    z = "Mx2" if x == "Mx1" else "Mx1"
    assert "gm_id_role" not in af.get(z, {}), af.get(z)
    assert "L_role" not in af.get(z, {}), af.get(z)
    assert sorted([x, "My"]) in review_pairs, review_pairs
    assert sorted([z, "My"]) not in review_pairs, review_pairs


# ---------------------------------------------------------------- 계약 11

def _b26pre_br(n):
    """`BR(n)`: tail `Mt`(gnd→ntail) + branch k마다 `Mi<k>`(ntail→no<k>, gate ni<k>)·`Ml<k>`(vdd→no<k>, gate nbp)."""
    ts = [_b26pre_t("Mt", "nmos", "gnd", "ntail", "nb")]
    for k in range(1, n + 1):
        ts.append(_b26pre_t(f"Mi{k}", "nmos", "ntail", f"no{k}", f"ni{k}"))
        ts.append(_b26pre_t(f"Ml{k}", "pmos", "vdd", f"no{k}", "nbp"))
    return ts


def _b26pre_trace(r):
    """`TR(r)`: trace 방향 원소만 순서대로 `(direction, position, tuple(devices), shared_source)`.
    `layer1_fallback` 원소는 계약이 아니다(spec card 계약 11 '계약이 아닌 것')."""
    return [
        (c["direction"], c["position"], tuple(c["devices"]), c["shared_source"])
        for c in r["candidates"] if c["direction"] in ("vdd_to_gnd", "gnd_to_vdd")
    ]


def test_b26pre_trace_two_branches():
    """계약 11(a): n = 2.

    oracle 대조: (a) 구성 + docstring(stick_diagram.py 1507~1509·1539~1540) -- 같은 서명 branch 사슬 Ml–Mi–Mt에서
    위치 1(Mi)만 같은 kind·다른 gate·같은 non-rail source(ntail)라 후보, 방향별 1건씩.
    """
    r = stick_diagram.find_differential_pair_candidates(_b26pre_br(2))
    assert _b26pre_trace(r) == [
        ("vdd_to_gnd", 1, ("Mi1", "Mi2"), "ntail"),
        ("gnd_to_vdd", 1, ("Mi1", "Mi2"), "ntail"),
    ]


def test_b26pre_trace_three_branches_order():
    """계약 11(b): n = 3.

    oracle 대조: 원소 집합(방향마다 세 쌍, position 1, ntail)은 (a) 구성. 원소 **순서**(쌍 (i<j) 오름차순,
    `vdd_to_gnd` 먼저)는 docstring에 없다 -- (c) 기준선 값.
    """
    r = stick_diagram.find_differential_pair_candidates(_b26pre_br(3))
    assert _b26pre_trace(r) == [
        ("vdd_to_gnd", 1, ("Mi1", "Mi2"), "ntail"),
        ("vdd_to_gnd", 1, ("Mi1", "Mi3"), "ntail"),
        ("vdd_to_gnd", 1, ("Mi2", "Mi3"), "ntail"),
        ("gnd_to_vdd", 1, ("Mi1", "Mi2"), "ntail"),
        ("gnd_to_vdd", 1, ("Mi1", "Mi3"), "ntail"),
        ("gnd_to_vdd", 1, ("Mi2", "Mi3"), "ntail"),
    ]
