---
id: 20261007-b26-v4-legacy-strengthen
phase: 3
evidence_type: test-only
gate_change: no
---
## 의도

B26-1(`20260930-b26-rail-accessor-set`) 1차 시도에서 auditor 순서 3의 V4(`test_lint.py`, B26-1 interface card)가 **기존** test 4개의 규칙 (1)을 FAIL로 냈다.
SD selftest `skills/analog-gmid-design/assets/tests/unit/test_selftest_stick_diagram.py`의 7줄이다(base `6df4bd7` 줄, blob `fe724a8`).

| test | 줄 | 같은 피검 출력끼리의 `==` |
|---|---|---|
| test_s133_refine_differential_and_mirror_relations | 3090·3092·3094·3096 | 한 후보 사전 안의 두 소자 값 |
| test_s134__propose_vertical_stack_ids | 3129 | 같은 출력의 두 필드 |
| test_s135_section | 3153 | 한 후보 사전 안의 두 소자 값 |
| test_s159_apply_device_roles_gap_fill | 3926 | 기대값을 피검 호출(제안)로 만든 비교 |

B26-1 interface card가 이 card의 두 심볼(이 card '관찰 가능한 계약'의 첫 두 함수)을 피검으로 처음 올렸고, B26-1이 이 파일을 처음 고치는 card라서 걸렸다.
B26-1 1차 test 커밋 `c247a76` 위치로는(그 뒤 test 사슬 끝 `212f76a`는 SR selftest만 바꿨다 -- 이 파일 blob `ac2333a7` 같음) 3120·3122·3124·3126·3159·3183·3956이다(1차 auditor `order3_v4_compare.txt`. 같은 파일 SR selftest의 둘은 기존 면제 `20260923-c9-v4-exempt`가 덮는다).

사용자 결정(2026-10-07): 면제((가′)) 대신 **(다) 이 4 test를 리터럴 기대값으로 강화하는 test-only card를 B26-1 1차 정리 뒤·2차 시도 전에 둔다**. 원문은 '결정 필요 항목' U1이다.
근거는 분석 `_drafts/v4_legacy_4tests_analysis.md`(이 card의 '작성 전 실측'이 같은 사실을 다시 쟀다)다.
* s159는 **판정이 비어 있다**. 라이브러리 `folded_cascode.topology.json`이 제안 4쌍을 이미 모두 선언하고 있다. 그래서 동적 기대값이 `[]`이고, apply가 파일에 아무것도 쓰지 않아도 통과한다(실측 -- '작성 전 실측' 3).
  면제로 닫으면 공허한 판정을 승인하는 셈이다.
* s133·s135는 같은 그룹이라는 **관계만** 본다. 그래서 b-leg 위·아래 stack이 합쳐지거나 Mamb 그룹에 다른 소자가 끼어도 통과한다. 손으로 정한 분할을 리터럴로 쓰면 이것을 잡는다.
* s134는 관계 자체가 계약이다(그룹 이름은 기계적으로 생성된다). 장치 이름 리터럴로 **동치 재서술**만 한다. 더 강해지지는 않지만, 면제 기록과 T1 뒤 재면제가 필요 없어진다.

**원칙 기본안(결정 아님 -- 근거)**:
* 판정은 약해지지 않는다. 엔진·도구·레지스트리·library는 바꾸지 않는다(test-only).
* 기대값은 이 card의 리터럴이다. 넷리스트에서 손으로 유도했다(oracle 절). 피검 출력의 다른 필드나 피검 호출을 기대 쪽에 두지 않는다.
* test 이름·픽스처(`s128_state`, `library_dir`)·다른 test는 바꾸지 않는다. B26-1 2차 시도와 T1(`p3-test-relocate`)이 test id로 이 test들을 가리키기 때문이다.
* 정본 topology 무관 원칙: s133·s134·s135는 이미 합성 입력이다. s159는 기존대로 library 파일의 **임시 사본**을 입력으로 쓴다(파일 왕복이 이 test의 계약이다).
  다만 사본을 test가 직접 고쳐서 선언 쌍 상태를 정한다. 그러면 기대값이 라이브러리의 이후 변경(쌍 추가 선언)에 따라 공허해지지 않는다. 사본의 선언 상태는 계약 4 (a)가 단언으로 고정한다.

## 관찰 가능한 계약

모든 계약은 위 파일의 해당 test 함수 **본문 안**에서만 바꾼다(계약 6). 피검 호출 인자(`inputs=` 등)와 호출 순서는 그대로다.
판정 대상 함수(interface card):
* `stick_diagram.refine_differential_and_mirror_relations(transistors, inputs=…)`: 반환 사전의 `"vertical_stack_id_candidates"` 아래 `"groups"`(소자 이름 → 그룹 이름)와 `"ambiguous_alternatives"`(소자 이름 → 후보 그룹 이름 목록).
* `stick_diagram.propose_device_roles_gap_fill(transistors, device_roles, matching_pairs_meta)`: 반환 사전 `"matching_pairs_proposals"`(원소마다 `"names"`).
* `stick_diagram.apply_device_roles_gap_fill(topology_json_path, result)`: 파일에 쓰고 반환 사전 `"applied_matching_pairs"`(새로 쓴 쌍마다 이름 목록).
* `stick_diagram.load_topology(json_path)`: `(transistors, meta)` 튜플. meta에 `"symmetry"`(`"matching_pairs"`)와 `"device_roles"`가 있다.

1. **test_s133_refine_differential_and_mirror_relations -- leg 8소자 분할 리터럴**
   * 지금 있는 단언 중 `None` 아님·후보 키 집합(10소자)은 그대로 둔다. 같은 그룹 `==` 4줄(3090·3092·3094·3096)은 단언 하나로 바꾼다.
     그 단언은 다음과 같다. 8소자 `M1a M1b M2a M2b M3a M3b M4a M4b`를 "후보 그룹 이름이 같다"로 나눈 분할(소자 이름 frozenset들의 집합)이
     **리터럴** `{{M1a, M2a}, {M1b, M2b}, {M3a, M4a}, {M3b, M4b}}`와 같다.
     분할은 후보 사전에서 이름을 읽어 만들 수 있다(예: 각 소자 m마다 같은 이름을 가진 8소자 중의 frozenset). 비교의 기대 쪽은 리터럴만이다.
   * 뒤의 `!=` 2줄(M1a≠M1b, M1a≠M3a)과 접미사(`_a`·`_b`) 단언은 그대로 둔다. `!=` 2줄은 이 분할에 함의되지만 지우지 않는다(지우면 V5 발견만 는다).
   * M5·M6은 판정하지 않는다(소속을 손으로 확정할 근거가 약하고 legacy 의도에도 없다).
2. **test_s134__propose_vertical_stack_ids -- 동치 재서술**
   * `set(alt["Mup"]) == {groups["Mlo1"], groups["Mlo2"]}`(3129) 한 줄을 다음 두 단언으로 바꾼다.
     (a) `alt["Mup"]`의 이름은 모두 `groups`의 값 가운데 있다(부분집합, `<=`).
     (b) `groups`에서 그룹 이름이 `alt["Mup"]` 안에 있는 소자 이름을 정렬한 목록이 **리터럴** `["Mlo1", "Mlo2"]`이다.
   * 앞의 단언(`groups["Mup"] == "ambiguous_Mup"`, 격리 `!=`, `"Mup" in alt`)은 그대로 둔다.
     이 셋과 (a)·(b)를 합치면 원 단언과 동치다(세 소자 회로라서. 증명 스케치는 '작성 전 실측' 4).
3. **test_s135_section -- Mamb 그룹 = 정확히 {Mamb, Mout}**
   * `groups["Mamb"] == groups["Mout"]`(3153)를 다음 단언으로 바꾼다. `groups`에서 그룹 이름이 `groups["Mamb"]`와 같은 소자 이름을 정렬한 목록이 **리터럴** `["Mamb", "Mout"]`이다.
   * `"Mamb" not in ambiguous_alternatives`와 `!= M3b`(3155) 단언은 그대로 둔다(뒤의 것은 함의되지만 남긴다).
4. **test_s159_apply_device_roles_gap_fill -- 입력 사본 구성 + 리터럴 기대값**
   * 입력: 지금처럼 `library_dir`의 `folded_cascode.topology.json`을 임시 디렉터리로 복사한다. 그다음 `load_topology` **전에** test가 사본 JSON을 읽고 고쳐 다시 쓴다.
     고치는 것은 둘이다. `symmetry.matching_pairs`에서 이름 집합이 {M9, M10}·{M7, M8}·{M11, MN}인 원소 셋을 지운다. 나머지 원소는 그대로 둔다. 그리고 `device_roles`의 `"M9"` 항목을 지운다.
     **다른 키는 바꾸지 않는다**(특히 `supply_nets` -- B26-1 2차 test가 이 사본에서 레일 선언을 읽는다). 쓰기는 UTF-8 JSON이다.
   * (a) **입력 전제**: `load_topology(사본)`의 meta에서 선언 쌍의 이름을 각각 정렬해 정렬한 목록이 **리터럴** `[["M1", "M2"], ["M3", "M4"], ["M5", "M6"]]`이다.
     라이브러리가 바뀌어 이 전제가 깨지면 test가 여기서 실패한다. 조용히 공허해지지 않는다.
   * (b) 첫 적용: 지금처럼 `propose_device_roles_gap_fill(transistors, {}, [])`의 결과를 `apply_device_roles_gap_fill(사본 경로, 그 결과)`에 넘긴다.
     `sorted(applied_matching_pairs)`는 **리터럴** `[["M10", "M9"], ["M11", "MN"], ["M7", "M8"]]`이다.
     지금의 동적 기대값(제안에서 선언된 쌍을 뺀 comprehension)과 그것이 쓰던 '이전 쌍 수·이전 쌍 키' 변수는 지운다.
   * (c) 쓰인 파일: 다시 연 JSON의 `symmetry.matching_pairs`에서 이름을 각각 정렬해 정렬한 목록이 **리터럴**
     `[["M1", "M2"], ["M10", "M9"], ["M11", "MN"], ["M3", "M4"], ["M5", "M6"], ["M7", "M8"]]`이다. 지금의 '쌍 수 = 이전 + 새' 단언을 대신한다.
   * (d) `device_roles`에 `"M9"`가 있고 그 `"vsb"`는 `0.0`이다(지금 단언 그대로 -- 이제 사본에서 지운 항목을 apply가 다시 써야 참이다).
   * (e) 둘째 적용(멱등): 지금처럼 사본을 다시 `load_topology`하고 파일의 역할·쌍으로 제안해 적용한다. `applied_matching_pairs == []`(그대로).
   * 2026-08-14 주석("기대값을 하드코딩하지 않는다")은 새 입력 구성에 맞게 고친다(입력을 test가 만들므로 라이브러리 변화와 무관하다).
5. **거부 증명 -- auditor 변이 측정**('거부해야 할 입력'). 변이 넷은 auditor 자신의 스크립트로 만든다. 피검 함수를 감싸 출력을 바꾸는 방식이고, 엔진 파일은 바꾸지 않는다.
   * M-a: apply가 파일에 쓰지 않음(반환값은 그대로). 원 test(base)는 PASS, 새 test는 **s159 FAIL**.
   * M-b: s133 입력에서 M3b·M4b의 후보 그룹을 M1b의 것으로 바꿈(b-leg 위·아래 stack 합침). 원 test는 PASS, 새 test는 **s133 FAIL**.
   * M-c: s135 입력에서 M5의 그룹을 Mamb의 것으로 바꿈. 원 test는 PASS, 새 test는 **s135 FAIL**.
   * M-d(동치 확인): s134 입력에서 `ambiguous_alternatives["Mup"]`을 Mlo1 그룹 하나로 줄임. 원 test와 새 test **둘 다 s134 FAIL**.
   * 기준 실행(변이 없음): 원 test·새 test 모두 4 passed.
6. **V4 형태**:
   * 모든 판정은 test 본문의 `assert`다. 판정을 보조 함수에 넣지 않는다(V4 규칙 (4) -- b26pre 1차 시도 선례).
   * `==` 단언의 기대 쪽에는 리터럴만 둔다. 같은 피검 출력의 두 자리를 `==`로 맞대는 단언을 새로 만들지 않는다(V4 규칙 (1)).
     출력에서 값을 고르는 비교(분할을 만들 때 그룹 이름끼리 비교)는 단언 밖의 식 안에서만 한다.
   * 이 card interface card와 B26-1 interface card(`20260930-b26-rail-accessor-set.interface.md`) **둘 다**로 잰 `test_lint.py` 규칙 (1) FAIL이 이 파일에서 0이다.
     B26-1 2차 시도가 이 test들에 `rails=`만 더한 판에서도 0이다(시뮬레이션 실측 -- '작성 전 실측' 3).
7. **범위**: 이 card `Change-Id` 커밋들의 diff는 위 파일 하나다. 그 안에서도 네 test 함수의 본문(docstring의 oracle 문장 포함)만 바꾼다.
   test 이름, 다른 test, 픽스처(`s128_state` 등), conftest, 다른 파일은 바꾸지 않는다.
   docstring의 "판정을 그대로 옮겼다" 문장은 "이 card로 리터럴 기대값을 강화했다(oracle (a))"로 고친다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

test-only다. code 커밋이 없다. 엔진·도구·레지스트리·library가 바뀌지 않고, 기존 test 파일 하나만 바뀐다(`Role: test`).
* 모양: design 05 §9.2-4 표의 test-only 행 -- "`old..new^`는 첫 부모 사슬이고 전부 `Role: test`(1개 이상), `new`는 `Role: audit` 1개, 병합 없음, T = `new^`, K 없음".
* V2: 변경 전 test 집합이 base에서 통과시킨 것은 변경 후에도 모두 PASS해야 한다. 바뀐 네 test도 base 엔진에서 PASS한다(시제품 실측, '작성 전 실측' 3).
* red 대신 계약 5(auditor 변이 측정)로 거부를 증명한다. 기존 동작을 바꾸지 않는 강화라서 base에서 실패하는 test 커밋이 없다.
* V3는 code 변경이 없어 N/A다. V5는 **발견이 예정되어 있다**(기존 test의 비교·리터럴 변경). 승인 기록 하나로 덮는다('결정 필요 항목' U2, '두 번 시도 절차').

## oracle 종류와 출처

* 계약 1·3·4 -- **(a) 구성 입력**. 기대값은 넷리스트에서 손으로 정한다. 피검 함수를 불러 기대값을 만들지 않는다.
  * 계약 1(s133, 픽스처 `s128_state._t35_fixture` 10소자): stack 간선은 같은 kind의 drain→source 직렬 내부 노드이고, 그 노드의 단자가 정확히 2개일 때만 생긴다.
    N1(M1a.d·M2a.s), N2(M1b.d·M2b.s), N3(M4a.d·M3a.s), N4(M4b.d·M3b.s)가 그런 노드다. Vx(M6.d·M1a.s·M1b.s)와 Vy(M4a.s·M4b.s·M5.d)는 단자가 3개라 잇지 않는다.
    Nout1·Nout2는 pmos drain·nmos drain이 만나는 출력이라 잇지 않는다(이으면 기존 `M1a != M3a` 단언과 모순).
    그래서 8소자 분할은 `{M1a,M2a} {M1b,M2b} {M3a,M4a} {M3b,M4b}`다. legacy 의도(이관본 S133 "cascode-stack composite + leg a/b")와 같다.
  * 계약 3(s135, 위 10소자 + Mamb(nmos, s=Nout2, d=Vg_out) + Mout(nmos, s=gnd, d=Nout2)): Mamb의 fan-in 후보는 drain이 Nout2인 nmos 둘(M3b·Mout)이다.
    M3b는 differential branch 소속이라 빠지고(docstring 0-B 재판정, legacy S135 의도), Mout으로 확정된다. Mout의 source는 레일(gnd)이라 더 잇지 않는다. 그래서 그 그룹은 정확히 `{Mamb, Mout}`이다.
  * 계약 4(s159, library `folded_cascode` 넷리스트 13소자): 제안은 diode 기준 미러와 공통 source 차동쌍이다.
    M1/M2(pmos, source `tail` 공유, gate vin_n·vin_p), M9/M10(M9 diode Vg9, M10 gate Vg9), M7/M8(M7 diode Vg7, M8 gate Vg7), M11/MN(MN diode vb2, M11 gate vb2)이 제안된다.
    M3/M4는 gate vb1을 MP(diode)와 셋이 공유해서 쌍으로 제안하지 않는다(s158이 단언). M5/M6는 diode 기준이 없다. 그래서 제안은 4쌍이다.
    사본의 선언 쌍 {M3,M4}·{M1,M2}·{M5,M6}을 빼면 새로 쓰는 쌍은 3쌍이다. 리터럴 `[["M10","M9"],["M11","MN"],["M7","M8"]]`은 이름 목록을 각각 정렬한 뒤 전체를 정렬한 순서다(문자열 정렬: "M10" < "M9").
    M9의 `vsb` 0.0은 source가 낮은 레일(gnd)이라는 구성에서 나온다(기존 단언과 그 메시지 "vs 기본값(템플릿 관례)").
* 계약 2 -- (a) 관계 불변식. docstring "후보 그룹 이름 목록 = fan-in 후보 lo 각각이 속한 그룹"을 장치 이름 리터럴(`["Mlo1","Mlo2"]`)로 다시 쓴다. 그룹 이름은 기계적 생성(순번)이라 리터럴로 쓰지 않는다.
* **작성자≠검증자**:
  * 기대값은 이 card 문장이 정한다. test-author는 interface card와 이 card, 그리고 고칠 test 파일(test 분류 -- 열람 가능)만 보고 쓴다.
  * 시제품(오케스트레이터 사전 측정, 모래상자 `C:/g441` 커밋 `f4aeb09` -- 측정 뒤 삭제)은 test-author·auditor에게 건네지 않는다. 판정 증거로도 쓰지 않는다. **시제품이 test 커밋이 될 수 없다** -- 오케스트레이터는 tests를 쓰지 않는다(N3.12.1).
  * 계약 5는 auditor 자신의 스크립트로 잰다. auditor는 기대값마다 이 절과 대조해 `checks.V4.basis`에 `oracle 대조:` 줄을 적는다. 바뀐 단언 다수가 V4 (2) `UNJUDGED`다(피검 출력 사전을 거치는 식).

## 거부해야 할 입력

계약 5의 변이 M-a·M-b·M-c(새 test가 FAIL, 원 test는 PASS -- 강화의 증거)와 M-d(둘 다 FAIL -- s134 동치의 증거).
통과해야 하는 것: base 엔진(이 card 착수 base), 그리고 B26-1 병합본(B26-1은 이 경로를 동작 보존으로 바꾼다. B26-1 2차 시도의 V1·V2가 잰다).

## library 회로 적용 여부

s159가 library `folded_cascode.topology.json`을 **임시 사본**으로 읽는다(지금과 같다). library 파일은 바꾸지 않는다. 엔진이 바뀌지 않으므로 E-LIB·E-INST는 base와 같다.

## 무동작 판정 입력(무발동 값)

엔진·library·다른 test 전부 base와 판정이 같다(test-only). 새 산출물 필드는 없다.

## 재현할 수치

auditor가 판정 기록에 다시 잰다.
* V1: 전체 test(`--gmid-phase=3`). 기대는 base와 같은 수의 passed·xfailed다(바뀐 test 4개는 이름이 같고 수는 그대로).
* 계약 5: 변이 4 × (원 test, 새 test) 결과표.
* V4: 이 card interface card로 이 파일 규칙 (1) FAIL 0. 참고로 B26-1 interface card로도 0.
* V5: `diff_paths` = [위 파일], `diff_hash` = 승인 기록 target, `approved: true`(2차 시도).

## 결정 필요 항목

* **U1(결정됨 -- 이 card의 근거)**: 사용자 자유 답 **"다로 하자."**(2026-10-07 15:18 KST. 세션 jsonl `63c6146a-ab1d-4035-a169-bae810986922` 사용자 메시지 uuid `c42c4c06-8f48-4245-9917-06b8160f5340`, timestamp `2026-10-07T06:18:32.468Z`.
  직전 assistant 메시지 uuid `0ad6f546-b96f-4208-8e83-794e20345649`가 (다)를 "강화 card를 1차와 2차 시도 사이에 넣기"로 설명했다). 앞선 AskUserQuestion 답 [B26-1 V4] "(가′) 면제 + 재검토 줄 (Recommended)"을 대체한다. 그 면제 기록은 만들지 않는다(`_drafts/approval_20261007-b26-v4-exempt.dropped.md`).
  AskUserQuestion 답이 아니라서 운반 검사기(`t0_quote_check`·`b26_1_quote_bind`)로 묶을 수 없다. 그래서 이 답만으로 승인 기록을 만들지 않는다. U2의 질문 하나가 (다) 확인과 V5 승인을 함께 받는다.
* **U2(사용자 승인 필요 -- 착수 조건)**: V5 기준 약화 승인 기록 `20261007-b26-v4-legacy-strengthen-v5`(`target_kind: diff`). 질문 원문은 `_drafts/b26_v4_legacy_v5_question.md`이고, 문안은 `_drafts/approval_20261007-b26-v4-legacy-strengthen-v5.md`이다.
  * 승인 범위는 이 파일 하나다. 발견 단위는 네 test 안이어야 한다. 발견 종류는 'assert 삭제'(s133만, assert 수 6 이상)·'비교 완화'·'리터럴 변경'이어야 한다.
  * target(diff 해시)은 1차 시도 auditor가 잰 값이다. 운반 스크립트가 1차 `weakening_diff.py` 출력과 위 범위를 대조해 채운다.
    범위 밖 발견이 나면 그 기록을 쓰지 않고, 실제 diff 해시와 발견 목록을 보여 다시 묻는다(T0 양식, `t0_quote_check.check_record`).
  * 이 card는 `gate_change: no`라 게이트는 머리 `approval` 줄을 요구하지 않는다(`merge_gate.gate_change_ok`).
    기록이 gate에 들어가는 운반 커밋의 card 개정으로 머리에 `approval: 20261007-b26-v4-legacy-strengthen-v5`를 더한다. 없는 기록 id는 미리 적지 않는다(선례 B26-1 승인 줄 4·5).
* **U3(순서 -- 원칙 기본안)**: B26-1 1차 정리 → B26-1 운반 `Role: doc` 커밋 → **이 card 순서 0**(두 커밋을 push 한 번으로 묶어도 된다) → 이 card 1차 시도 → 정리·운반 → 2차 시도 → 병합 → 운반 디렉터리 삭제(`Role: doc`, B26-1 card 개정과 같은 커밋 가능) → B26-1 2차 시도(B26-1 base B2 = 그 master).
  * 한 번에 변경 하나다. B26-1 역할 브랜치가 남아 있는 동안에는 이 card 순서 0의 gate push를 EL1이 거부한다(`role_hooks._judge_push`).
* **착수 조건**(오케스트레이터가 순서 0 커밋 전에 gate `master`에서 확인한다. `H=$(git -C "$R" rev-parse gate/master)`):
  1. B26-1 1차 정리 완료: `git -C "$R" for-each-ref refs/heads/role/` 출력 0줄.
  2. U2 답이 승인 선택지다(사전 승인. 아니면 '1차 diff를 보고 승인' 경로 -- 1차 시도 뒤 질문).
  3. 이 파일 blob이 B26-1 base와 같다: `git -C "$R" rev-parse "$H:skills/analog-gmid-design/assets/tests/unit/test_selftest_stick_diagram.py"` = `fe724a8c0e0571016332da41a77ac7286c535d5b`.
     다르면 줄 번호·계약 입력을 다시 잰다(B26-1 운반 커밋은 이 파일을 바꾸지 않는다).
* **B26-1 card에 넣을 인계**(B26-1 운반 커밋의 card 개정 몫):
  * 2차 base B2 = 이 card 병합 뒤 master다. B1..B2에서 이 파일이 바뀐다(이 card).
    B26-1의 `git diff --quiet B1 B2 -- <V5 경로>` 검사 대상(P9 test·B34 test)은 이 card가 바꾸지 않는다. 그래서 B26-1 기록 4의 해시 식 입력은 같다.
  * 2차 test-author는 T1.patch의 이 파일 hunk 중 네 test 몫(`rails=` 추가 4줄 -- s133·s134·s135 각 1, s159 2)을 **강화된 본문 위에** 다시 쓴다. 호출 줄은 이 card가 바꾸지 않으므로 '+' 줄 그대로다.
  * 2차 auditor 기대: V4 규칙 (1) 이 파일 0(1차의 7줄 소멸, 시뮬레이션 실측). 면제 기록 없음.
* **후속 정정(이 card 밖)**: T1 초안(`_drafts/draft_p3_t1.spec.md`)의 SD base blob `fe724a8`(V5 경로 표)은 B26-1과 이 card 병합으로 바뀐다. T1 착수 재측정 때 고친다(관계는 같다).
  백로그 B67은 닫는다(`_drafts/backlog_additions.md` 116행 갱신 그대로).

## 두 번 시도 절차

**한 번의 시도로는 할 수 없다(계획된 재시도).** 근거는 셋이다.
* V5 승인은 auditor의 `checks.V5` 해시와 같은 `target_kind: diff` 기록이 **head 트리**에 있어야 통과한다. `merge_gate.py` 9: `load_approvals(new_view)`.
* test-only 모양은 `old..new^`가 전부 `Role: test`이고 `new`가 `Role: audit`이다. 승인 기록(`.ai/approvals/**`)은 오케스트레이터만 쓴다(N3.12.2). 그래서 기록은 사슬 안에 들어갈 수 없고, 시도 시작 전 base(gate `master`)에 있어야 한다.
* 그 기록의 target(diff 해시)은 test 커밋의 blob id로 정해진다(`00-common` §8.2). test-author가 커밋하기 전에는 알 수 없다. 오케스트레이터 시제품을 test 커밋으로 쓰면 작성자≠검증자를 어긴다(N3.12.1).

정본 = design 05 §12 'V5 승인 운반' 행(gate `6df4bd7`). 이 card는 그 절차를 그대로 따른다(선례 T0 `_drafts/t0_carry.sh`, B26-1 card '두 번 시도 절차').

| 단계 | 주체 | 동작 | 멈춤 |
|---|---|---|---|
| 1. 1차 시도(병합 안 함) | 오케스트레이터·test-author·auditor | base B1(착수 조건 충족 master)에서 §12 순서 0~3 → T1. test-only라 순서 4·5가 없다.<br>auditor 순서 3은 freeze와 함께 다음을 `$W/<id>-audit/.ai/verification/<id>/`(`base_check.json`과 원출력)에 남긴다.<br>(i) V5 `weakening_diff.py --base B1 --head T1`(기대 FAIL, `diff_paths` = [이 파일]).<br>(ii) V4 두 interface card(이 card·B26-1).<br>(iii) V1 네 test와 전체 V2.<br>(iv) 계약 5 변이 4. | V5 발견이 U2 범위 밖이면 멈추고 실제 해시·발견으로 다시 묻는다. V1·V2·V4 FAIL이나 계약 5 불일치면 멈춘다(card·test 결함 -- 재설계). |
| 2. 운반 | 오케스트레이터 | (a) 정리 **전**: §12 (2)대로 `git -C $W/<id>-test cat-file blob T1:<이 파일> > D/<blob id>.blob`, 대응표 `D/paths.tsv`(한 줄)를 만든다. `D` = `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/v5-carry/20261007-b26-v4-legacy-strengthen/`.<br>같은 사본과 `base_check.json`·원출력·`SHA256SUMS`를 저장소 밖 `_drafts/b26v4s_attempt1/`에 보관한다. 승인 기록 작성: `diff_base` = B1, `diff_head` = T1, `diff_path` = 이 파일, `target` = 1차 `diff_hash`. 확인은 `merge_gate.py parse-approval` exit 0과 인용 검사기다.<br>(b) 정리: `git worktree remove --force` 두 경로(test·audit), `git branch -D role/{test,audit}/<id>`. `refs/heads/role/` 0줄을 확인한다.<br>(c) `Role: doc` 커밋 하나에 기록 + `D` + card 개정(머리 `approval:` 줄, '1차 시도 기록' 문단)을 담는다.<br>(d) `git push gate master:master` 단독 실행, 전체 출력 확인. | 기록 파싱·인용 검사 실패면 (b) 전에 멈춘다. push 거부면 출력 전체를 보고하고 멈춘다(재시도 루프 금지). |
| 3. 2차 시도 | test-author | base B2 = 2의 master. 착수 전 `git diff --quiet B1 B2 -- <이 파일>`(base blob 같음 → 해시 식 입력 같음). test-author는 `paths.tsv`대로 `.blob`을 `cp`로 원래 경로에 두고 커밋만 한다(손으로 다시 쓰지 않는다 -- 1바이트라도 다르면 해시가 바뀐다). | B1·B2 blob이 다르면 멈추고 1부터. |
| 4. 2차 판정 | auditor | §12 순서 3·7: V1~V10. V5 `approved: true`이고 해시 = 기록 target이다. basis에 "B1·B2 사이 이 파일 blob 같음"을 적는다. 1차 근거(`_drafts/b26v4s_attempt1/`, `SHA256SUMS` 대조 뒤)는 판정 기록에 옮겨 싣는다. 판정 기록 `approvals[]` = 이 기록 id. → §12 순서 8 push. | 해시가 다르면 기록을 쓰지 않고 멈춘다. |
| 5. 정리 | 오케스트레이터 | 병합 뒤 `D` 삭제(`Role: doc`, §12 (4)). B26-1 card 개정과 같은 커밋으로 해도 된다. | -- |

**비용**(선례 b26pre 2차 시도 실측: card 개정 22:31 → test 22:40 → audit 23:07, 약 35분):
* 1차 약 40~60분이다. test-author 15~20분, auditor 순서 3이 V2 전체 + V4 두 번 + 변이 4.
* 운반은 15~20분이다(사전 승인이면 사용자 대기 없음).
* 2차는 30~40분이다. `cp` 커밋과 V1~V10 판정 기록, push.
* 합계 약 1.5~2시간에 사용자 답 1회(사전 승인). 사후 승인으로 가면 1차 뒤에 사용자 대기 1회가 더 든다. V3·code 단계가 없어 B26-1의 두 번 시도(V3 약 2시간)보다 짧다.

## 작성 전 실측

**measured at `6df4bd7`**(gate `master`, 2026-10-07, 저장소 읽기 전용, 모래상자 `C:/g441` -- `git clone -c core.autocrlf=false` 뒤 origin 제거, 게이트 코드는 `git archive 6df4bd7 tools/gates`, python `C:/Python314/python.exe -P`, `TMP`·`TEMP`·`PYTHONPYCACHEPREFIX`는 모래상자 안, 측정 뒤 삭제).

1. **사실 문장 재측정**:
   * 파일 blob `fe724a8c0e0571016332da41a77ac7286c535d5b`. def 줄: s133 3075, s134 3106, s135 3134, s159 3901.
     `==` 줄 3090·3092·3094·3096·3129·3153·3926(`sed -n`). s133 assert는 9개다(None·키 집합·`==` 4·`!=` 2·접미사).
   * 엔진 `stick_diagram.py` blob `9993047c`. def 줄: `refine_differential_and_mirror_relations` 2311, `propose_device_roles_gap_fill` 3820, `apply_device_roles_gap_fill` 4528, `load_topology` 8525.
   * library `folded_cascode.topology.json`: `supply_nets` `["vdd","gnd"]`. 선언 쌍 6 `[M3,M4] [M9,M10] [M1,M2] [M5,M6] [M7,M8] [M11,MN]`. `device_roles["M9"].vsb` 0.0. 넷리스트 13소자(oracle 절의 단자는 이 파일에서 읽었다).
   * `_t35_fixture` 10소자(파일 412~423행 `s128_state`): oracle 절의 단자와 같다.
   * B26-1 1차 시도(test 커밋 `c247a76`, 이 파일 blob `ac2333a7`. 2026-10-07 측정 중 test 사슬 끝은 `212f76a`(SR selftest만, code-author dispute 해소)로, code 끝은 `e92e6b8`로 움직였다 -- 이 파일 blob 같음) auditor 순서 3 산출물 `order3_v4_compare.txt`: 이 파일의 "기존 FAIL" 7줄(T1 위치 3120·3122·3124·3126·3159·3183·3956 ↔ base 3090…3926)과 SR selftest의 "기존 exempt" 2.
     같은 auditor의 V5 `diff_paths`는 `test_b34_grammar_explicit.py`·`test_dup_kcl_edges.py` 두 경로다. 이 파일은 없다 -- 이 card가 B26-1 V5 기록 해시를 바꾸지 않는다.
2. **이름 충돌**: 새 파일·새 test 이름이 없다. test id는 그대로다. `grep "test_s159\|test_s13[345]"`: `docs`·tests 다른 파일 0건. `_drafts`에서는 B26-1 브리핑과 이 card, 백로그뿐이다.
3. **시제품 측정**(`C:/g441` 커밋 `f4aeb09` = `6df4bd7` + 계약 1~4 상당, 이 파일 +24/−18, blob `70bfca3f`. 오케스트레이터 측정 전용):
   * 네 test, gate ini·`--gmid-phase=3`: base 4 passed, 시제품 4 passed(`PYTHONHASHSEED` 0·1).
   * 계약 5 변이(출력 감싸기 플러그인, seed 1): base는 M-a·M-b·M-c 모두 4 passed(원 test가 놓친다). 시제품은 M-a → s159 FAIL, M-b → s133 FAIL, M-c → s135 FAIL(나머지 3 passed).
   * V4 `test_lint.py`(gate `6df4bd7` 판):
     * base + B26-1 interface card: FAIL, 규칙 (1) 7(위 7줄).
     * 시제품 + B26-1 interface card: **PASS**, 규칙 (1) 0(UNJUDGED 181, NO-SUBJECT 198, PASS 1).
     * 시뮬레이션(B26-1 T1 `c247a76` + 같은 강화, 곧 B26-1 2차 test 상당) + B26-1 interface card: **PASS**, 규칙 (1) 0.
     * 이 card interface card: 시제품 **PASS**, 규칙 (1) 0(아래 6).
   * V5 `weakening_diff.py --base 6df4bd7 --head f4aeb09`: FAIL(예정). `diff_paths` = [이 파일], `diff_hash` `f3f3276a…`(시제품 값 -- 실제 target은 1차 T1 값).
     발견 9개: s133 'assert 삭제'(9 → 6)·'비교 완화'·'리터럴 변경', s134·s135·s159 각 '비교 완화'·'리터럴 변경'. U2 범위 안이다.
   * 전체(시제품, V1 형태 `-P -m pytest -c <gate ini> --rootdir --confcutdir <복제본>/skills/analog-gmid-design/assets/tests --gmid-phase=3`, seed 0): **1114 passed, 15 xfailed**(225초).
     base `6df4bd7` 트리 수(backfill 판정 기록 V1 1114 passed·15 xfailed)와 같다.
4. **s134 동치 스케치**: 앞 단언으로 `g(Mup) = "ambiguous_Mup"`이고 Mup은 Mlo1·Mlo2와 그룹이 다르다.
   * 원 단언 ⇒ 새 (a)·(b): alt = {g(Mlo1), g(Mlo2)} ⊆ 값이다. 그룹이 alt 안인 소자는 Mlo1·Mlo2이고, Mup은 그룹이 다르므로 빠진다.
   * 새 ⇒ 원: (b)로 alt 안 그룹을 가진 소자가 정확히 Mlo1·Mlo2이므로 g(Mlo1)·g(Mlo2) ∈ alt다. (a)로 alt의 각 이름은 어떤 소자의 그룹이고, 그 소자는 (b)에 따라 Mlo1·Mlo2뿐이다. 그래서 alt = {g(Mlo1), g(Mlo2)}다.
   * 계약 5 M-d가 이를 실행으로 확인한다.
5. **쓰기 경로**: test 파일은 gmid-test-author(`assets/tests/**`)가 쓴다. spec card·interface card·승인 기록·운반 blob은 오케스트레이터가 쓴다. 판정 기록·변이 측정은 auditor가 쓴다. 엔진·library는 바꾸지 않는다.
6. **parse_spec_card·interface card**(gate `6df4bd7` 판 `role_paths.parse_spec_card`, `interface_card.py`):
   * `parse_spec_card(…, expect_id=…)` → `id 20261007-b26-v4-legacy-strengthen`, `phase 3`, `evidence_type test-only`, `gate_change no`, `approval []`(운반 개정 전). 절 12개.
   * `interface_card.py` → 기존 함수 **4행**(`refine_differential_and_mirror_relations`·`propose_device_roles_gap_fill`·`apply_device_roles_gap_fill`·`load_topology`, 모두 `stick_diagram`). 밑줄 시작 0, 신규 시그니처 0행.
   * 이 card interface card로 잰 V4: base `6df4bd7`은 FAIL, 규칙 (1) 7(같은 7줄). 시제품은 **PASS**, 규칙 (1) 0(UNJUDGED 119, NO-SUBJECT 261).
     `--interface-card`는 절대 경로로 준다. 아직 커밋되지 않은 상대 경로는 실행 위치 기준으로 찾아 `FileNotFoundError`(ERROR)가 났다.
7. **계획서 소비자**: 지우거나 옮기는 이름이 없다. **미배선**: 새 def가 없다. **기존 계약 test**: `A/tests/contracts`에 이 네 test를 참조하는 것이 없다.
