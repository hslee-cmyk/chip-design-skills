# V4 규칙 (1) -- 이관 legacy test 4개 분석 (B26-1 interface card 기준, gate `6df4bd7`)

읽기 전용 분석. 스크래치 `C:/g436`(복제 `-c core.autocrlf=false`, `tools/gates`는 `git archive 6df4bd7`), 끝나고 삭제.
대상 파일 `skills/analog-gmid-design/assets/tests/unit/test_selftest_stick_diagram.py`(blob `fe724a8`).

## 0. 발견 재현

`test_lint.py --root <복제> --interface-card docs/02-design/specs/20260930-b26-rail-accessor-set.interface.md --head 6df4bd7 <파일>`
→ verdict FAIL, 규칙 (1) **7줄**(그 밖의 FAIL 0):

| 줄 | test | 같은 피검 호출(인라인 뒤) |
|---|---|---|
| 3090·3092·3094·3096 | `test_s133_refine_differential_and_mirror_relations` | `refine_differential_and_mirror_relations(_t35_fixture, inputs=("Vip","Vim"))` |
| 3129 | `test_s134__propose_vertical_stack_ids` | `refine_differential_and_mirror_relations(_t41_fixture, inputs=())` |
| 3153 | `test_s135_section` | `refine_differential_and_mirror_relations(_t42_fixture, …)` |
| 3926 | `test_s159_apply_device_roles_gap_fill` | `propose_device_roles_gap_fill(_t55_trs, {}, [])` |

피검별 분리 실행(`--subject stick_diagram:<심볼>`): `refine_…` 단독 → 6줄(s133·s134·s135), `propose_device_roles_gap_fill` 단독 → 3926 1줄,
`load_topology`·`apply_device_roles_gap_fill` 단독 → 0. 즉 **B26-1 card가 이 두 심볼을 피검으로 처음 올리면서** 걸린다.

- 규칙 (1)은 `==`(와 `abs(a-b)<tol`·`isclose`) 쌍만 본다 -- 같은 test의 `!=` 단언(3098·3100·3128·3155)은 걸리지 않는다.
- B26-1 test-author가 이 호출들에 `rails=`를 더해도 두 쪽이 같은 변수에서 인라인되므로 키가 같아 **계속 걸린다**.
- 앞선 card: b34(`c851e54`)·b26pre는 같은 심볼을 피검으로 가졌지만 test diff가 새 contracts 파일뿐이라 이 파일을 lint하지 않았다. B26-1이 이 파일을 처음 M으로 만드는 card다.
- B26-1 spec card는 이 7줄을 예상하지 않는다(V4 언급은 285행 계약 14 비교뿐). '두 번 시도 절차' 단계 1은 "V1·V2·V4 등 다른 검사 FAIL도 멈춘다" -- **1차 시도 착수 전에 처리해야 한다.**

### 다른 interface card에서

- **T0**(`p3-tests-location-free`, 모의 피검 `size_transistor`·`width_from_id_density`·`check_quasi_static`·`_build_theta_evaluator`·`load_topology`) ∪ **C9**(`optimize_full_circuit_budget`) = T1 초안 계약 11의 피검 집합으로 같은 파일 lint → **PASS, 규칙 (1) 0**.
  s159의 `load_topology`는 튜플 언패킹이라 불투명 이름이 되어 호출 키가 생기지 않는다.
- 따라서 T1(옮긴 파일 전체가 A)에서는 이 4개가 걸리지 않는다. 다만 **이후 `refine_…`/`propose_device_roles_gap_fill`을 피검으로 올리고 이 파일(또는 T1 뒤 `test_mod*.py`)을 고치는 card마다 다시 걸린다** -- 면제로 닫으면 id가 바뀔 때마다(T1) 다시 받아야 한다(T1-2와 같은 구조).

## 1. test별 분석

### test_s133 (줄 3090·3092·3094·3096)

```python
assert _t40_cand["M1a"] == _t40_cand["M2a"]   # 3090
assert _t40_cand["M1b"] == _t40_cand["M2b"]   # 3092
assert _t40_cand["M3a"] == _t40_cand["M4a"]   # 3094
assert _t40_cand["M3b"] == _t40_cand["M4b"]   # 3096
```

- 검사 성질: 한 출력 안의 **동치류(같은 그룹) 소속** -- 직렬 stack(M1x-M2x via N1/N2, M4x-M3x via N3/N4)이 같은 `vertical_stack_id` 후보를 받는다. 기대값을 피검으로 "만든" 것이 아니라 분할(partition)의 관계다.
- legacy 원문(`2dd98f2` legacy 2362-2385, Test 40 "cascode-stack composite + leg a/b")과 글자 그대로 같다. 의도 = 직렬 stack × leg 분할.
- 그룹 **이름**은 리터럴로 고정하면 안 된다: 엔진 docstring이 "이름(`{idiom}_{순번}_{leg}`)은 기계적으로 생성" -- 순번은 순회 순서 산물(실측 `cascode-stack_1_a`·`_3_b`·`_2_a`·`_4_b`). 계약은 분할이다.
- 손 유도(엔진 미호출): 같은 kind의 drain→source 직렬 내부 노드가 단자 2개인 곳(N1: M1a.d·M2a.s, N2, N3: M4a.d·M3a.s, N4)만 stack을 잇는다.
  Nout1/Nout2는 drain-drain(출력)이라 잇지 않는다(그러면 기존 `M1a != M3a` 단언과 모순). → leg 8소자 분할 = `{M1a,M2a} {M1b,M2b} {M3a,M4a} {M3b,M4b}`.
  M5·M6(tail)의 소속은 손으로 확정할 근거가 약하고 legacy 의도에도 없어 넣지 않는다(새 판정을 더하지 않음).
- 분류: **(A) 관계이지만 (B)로 더 강하게 쓸 수 있음.** 현재 6단언(== 4 + != 2)은 b-leg 위·아래 stack 합침(M1b/M2b = M3b/M4b)을 못 잡는다(`!=`는 a-leg만 본다).
- 리터럴 형태(시제품):
  ```python
  _t40_leg8 = ("M1a", "M1b", "M2a", "M2b", "M3a", "M3b", "M4a", "M4b")
  _t40_part = {frozenset(n for n in _t40_leg8 if _t40_cand[n] == _t40_cand[m]) for m in _t40_leg8}
  assert _t40_part == {frozenset({"M1a", "M2a"}), frozenset({"M1b", "M2b"}),
                       frozenset({"M3a", "M4a"}), frozenset({"M3b", "M4b"})}
  ```
  엔진 확인(`6df4bd7`, 스크래치): 분할 `[[M1a,M2a],[M1b,M2b],[M3a,M4a],[M3b,M4b],[M5],[M6]]` -- 손 유도와 일치. 뒤의 `!=` 2줄은 이 분할에 함의된다((C), 남겨도 무해 -- 지우면 V5 발견만 는다).
- **권고: fix-with-literal.**

### test_s134 (줄 3129)

```python
assert set(_t41_alt["Mup"]) == {_t41_groups["Mlo1"], _t41_groups["Mlo2"]}
```

- 검사 성질: 같은 출력의 **두 필드 사이 참조 무결성** -- `ambiguous_alternatives["Mup"]`이 fan-in 후보 Mlo1/Mlo2가 실제로 속한 그룹 이름들과 같다(docstring: "후보 그룹 이름 목록 = fan-in 후보 lo 각각이 속한 그룹").
- legacy 원문(2389-2414, Test 41)과 같다. 바로 앞 `_t41_groups["Mup"] == "ambiguous_Mup"`은 리터럴(안 걸림).
- 그룹 이름은 기계적 이름이라 리터럴 금지(실측 `cascode-stack_1`/`_2`). 관계 자체가 계약이다.
- 분류: **(A) 관계 불변식 -- 면제 정당.** 리터럴 기대(장치 이름)로 **동치** 재서술은 가능하다(더 강하지는 않다):
  ```python
  assert set(_t41_alt["Mup"]) <= set(_t41_groups.values())
  assert sorted(n for n, g in _t41_groups.items() if g in set(_t41_alt["Mup"])) == ["Mlo1", "Mlo2"]
  ```
  (앞 줄 `Mup` 격리 단언과 함께 원 단언과 동치. `<=`는 규칙 (1) 쌍이 아니다.) 원문보다 덜 읽히므로 단독이면 면제가 낫다.
- **권고: exempt -- 단, 아래 강화 card를 만든다면 그 안에서 동치 재서술로 함께 처리**(면제 기록과 T1 뒤 재면제를 없앤다).

### test_s135 (줄 3153)

```python
assert _t42_vsid["groups"]["Mamb"] == _t42_vsid["groups"]["Mout"]
```

- 검사 성질: fan-in 재판정(0-B) -- Mamb(source=Nout2)의 후보 M3b·Mout(drain=Nout2, nmos) 중 differential branch 밖인 Mout 하나로 확정되어 같은 그룹. 관계(동치류 소속).
- legacy 원문(2415-2435, Test 42)과 같다.
- 손 유도: Mamb의 그룹 = 정확히 `{Mamb, Mout}`(M3b는 diff branch 소속이라 제외, 다른 소자는 Nout2 fan-in 후보가 아니다).
- 분류: **(B)** -- 원 단언은 Mamb/Mout 그룹에 다른 소자가 끼어도(예: M5) 통과한다.
  ```python
  assert sorted(n for n, g in _t42_vsid["groups"].items() if g == _t42_vsid["groups"]["Mamb"]) == ["Mamb", "Mout"]
  ```
  엔진 확인: `Mamb`·`Mout` = `stack_1`, 그 그룹 멤버 둘뿐 -- 일치. 다음 줄 `!= M3b`(3155)는 이 단언에 함의((C), 남겨도 무해).
- **권고: fix-with-literal.**

### test_s159 (줄 3926) -- 판정력 결함

```python
_t55_result_empty = propose_device_roles_gap_fill(_t55_trs, {}, [])
_t55_expected_new = sorted((sorted(frozenset(p["names"])) for p in _t55_result_empty["matching_pairs_proposals"]
                            if frozenset(p["names"]) not in _t55_before_pair_keys))
_t55_apply1 = apply_device_roles_gap_fill(_t55_path, _t55_result_empty)
assert sorted(_t55_apply1["applied_matching_pairs"]) == _t55_expected_new   # 3926
```

- 검사 성질: `apply_…`가 "제안 − 이미 선언된 쌍"만 파일에 쓴다(필터 + 쓰기 왕복). 피검 `propose_…`는 apply의 **입력**이자 기대값 출처라 두 쪽에 같은 호출이 있다 -- 규칙 (1)의 의도(기대값을 피검으로 만듦)에 정확히 해당.
- legacy 원문(3091-3133, Test 55 "실제 파일 읽기/병합/쓰기 왕복 + 멱등성")과 같다. 동적 기대는 `fa2fcfb`(2026-08-14)에서 "라이브러리 파일이 더 채워져도 stale하지 않게" 넣은 것.
- **실측 결함**: `fa2fcfb` 그 커밋부터 `library/folded_cascode.topology.json`이 이미 6쌍(M3/M4·M9/M10·M1/M2·M5/M6·M7/M8·M11/MN)을 선언하고, 제안 4쌍(M1/M2·M9/M10·M7/M8·M11/MN)이 전부 그 안에 있다
  → `_t55_expected_new == []`, `applied == []`, 파일 쌍 수 6 = 6 + 0, `device_roles["M9"].vsb == 0.0`도 원본에 이미 있다. **쓰기 경로 판정이 전부 공허하다.**
  스크래치 변이: `apply_device_roles_gap_fill`을 아무것도 안 쓰는 함수로 바꿔도 `6df4bd7` test는 **PASS**.
- 손 유도(엔진 미호출, netlist): M1/M2 = 공통 source `tail`·gate vin_n/vin_p 차동쌍; M9/M10 = M9 diode(Vg9)·M10 gate Vg9 미러; M7/M8 = M7 diode(Vg7) 미러; M11/MN = MN diode(vb2)·M11 gate vb2 미러;
  M3/M4는 MP까지 3-way라 제안 안 함(s158이 단언), M5/M6은 diode 기준 없음 → 제안 4쌍. 엔진 확인: `[[M1,M2],[M10,M9],[M7,M8],[M11,MN]]` -- 일치.
- 분류: **(B) -- 반드시 고쳐야 할 (B)**(관계 면제로 닫으면 공허한 판정을 승인하는 셈).
- 리터럴 형태(시제품): 임시 사본에서 3쌍(M9/M10·M7/M8·M11/MN)과 `device_roles["M9"]`를 지우고(M1/M2는 남겨 "이미 선언된 쌍 거름"도 실제로 판정),
  ```python
  _t55_expected_new = [["M10", "M9"], ["M11", "MN"], ["M7", "M8"]]
  ```
  파일 쌍 수 3 → 6, M9 `vsb` 0.0이 apply로 실제 다시 써짐, 두 번째 apply `[]`(멱등). 2026-08-14 주석은 갱신 필요(입력을 test가 만들어 라이브러리 변화와 무관해짐).
- **권고: fix-with-literal(필수).**

## 2. 시제품 측정 (스크래치 커밋 `8c0137f` = `6df4bd7` + 위 4 test 재서술, 19+/16-)

| 측정 | 결과 |
|---|---|
| V4 `test_lint.py --interface-card <B26-1> --base 6df4bd7 --head 8c0137f` | **PASS**, FAIL 0 |
| 4 test, 엔진 `6df4bd7` (`-c pytest_gate.ini --gmid-phase=3`) | 원본 4 passed / 시제품 4 passed |
| 변이 `apply` no-op | 원본 4 passed / 시제품 **s159 FAIL** |
| 변이 b-leg 위·아래 stack 합침 | 원본 4 passed / 시제품 **s133 FAIL** |
| 변이 Mamb 그룹에 M5 끼움 | 원본 4 passed / 시제품 **s135 FAIL** |
| V5 `weakening_diff.py --base 6df4bd7 --head 8c0137f` | **FAIL**(예상) -- 발견 8(s133 assert 수 9→6·비교 변경·리터럴 변경, s134·s135 비교 변경·리터럴 변경, s159 리터럴 변경), `diff_hash bb7dd137…` |

어느 길이든 사용자 승인이 하나 필요하다: 고치면 V5 `target_kind: diff` 승인, 안 고치면 V4 `target_kind: decision` 면제.

## 3. 권고와 card 배치

| test | 분류 | 권고 |
|---|---|---|
| s133 | (A)+(B) | fix-with-literal(leg 8 분할) |
| s134 | (A) | exempt -- 강화 card를 만들면 그 안에서 동치 재서술 |
| s135 | (B) | fix-with-literal(Mamb 그룹 = {Mamb, Mout}) |
| s159 | (B), 현재 공허 | fix-with-literal(필수) |

card 배치:
- **T1(`p3-test-relocate`)은 부적합**: 계약 3이 옮긴 본문 `ast.dump` = base를 요구(본문 변경 불가)하고, T1 피검 집합에서는 애초에 안 걸린다.
- **T0도 부적합**(A군 3파일 위치 독립화, 이 파일 아님).
- **B26-1 안에서는 고칠 수 없다**: test-author 몫은 판정 불변 입력 갱신(`rails=`·`supply_nets`)이고, 이 파일 리터럴 변경은 V5 발견이라 '승인 줄 배치' (6) 별도 승인 + 두 번 시도 절차의 P9 경로 운반과 얽힌다.
  B26-1에서 닫으려면 test worktree 생성 **전**에 decision 면제(규칙 (1)만, target 4 test id) -- 선례 `20260923-c9-v4-exempt`·`20261002-p3-t0-v4-s009-exempt`. 이 경우 s159 공허는 남는다.
- **기본안: B26-1 1차 시도 전에 전용 test-only 강화 card**(선례 `20260930-b26-pre-test-strengthen` -- B26-1 앞 test-only card, V5 승인). 4 test를 위 형태로 한 번에(s134는 동치 재서술). interface card에 `refine_differential_and_mirror_relations`·`propose_device_roles_gap_fill`·`apply_device_roles_gap_fill`.
  효과: B26-1 V4 PASS(시제품 실측), 면제 기록 0, T1 뒤 재면제 불필요, s159 판정력 회복. 비용: B26-1 base B1이 그 병합본으로 옮겨진다(P9 경로 blob은 무관 -- 이 파일만 바뀜).
- 대안(B26-1을 늦추지 않으려면): B26-1에 decision 면제 4 test + 강화는 Phase 4 백로그. 단 s159 공허를 Phase 3 이동 card 동안 그대로 두게 된다 -- 원칙(판정력 있는 test)상 기본안이 아니다.
