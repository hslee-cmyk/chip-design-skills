# D0b T-E 결정 사실 표본 대 Phase 4 #2 삭제 -- 처리안 판정 (review_b41_at_863a037 B1)

읽은 것: `_drafts/review_b41_at_863a037.md` B1, `_drafts/draft_p3_d0b.spec.md`(계약 6·11·12, oracle (d)-1 표 136~169행, 작성 전 실측 2'~6'),
`_drafts/draft_p3_d0a.spec.md`(계약 2 A-6·A-7 104~110행, 합성 단계 `a6-ref-follow`·`a7-isolated` 282~283행), design 30 at gate `863a037`
(`git -C … show 863a037:docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md` §8 D0b 행 614행),
`_drafts/draft_p4_first.spec.md`(의도 표 D-2·D-4, 계약 3·6·7·9, V5 승인 범위 180~188행), `_drafts/draft_phase4_design.md`, `_drafts/prep_deferred_rows.md`,
D0b UD-6 키트 원자료 `_drafts/p3ud6_kit/out/plan_names_{base,q,rg}.json`. 저장소는 `git -C` 읽기 전용. 쓰기는 이 파일 하나.

---

## 0. 결론

**(c)를 택하고, D0b에는 두 가지를 더한다**: (c-1) 표본 부재는 skip이 아니라 FAIL이며 그 표본을 없애는 card가 V5로 표 행을 지운다는 **수명 규칙**,
(c-2) 재생성 뒤에도 A-6을 실제로 거치는 **행 없는 A-6 표본 `search_shared_finger_w`** 1개 추가(기존 표본은 그대로).
(a) 단독은 A-7에 대체 표본이 없어 성립하지 않고, (b)는 T-E의 존재 이유(손적용 기대값 -- 동어반복 방지)를 없앤다.

---

## 1. 사실 (근거)

1. **A-6·A-7 단위 전수(D0b UD-6 키트 `plan_names_base.json`·`plan_names_q.json`, 트리 `4a286f0` 사슬 -- `863a037`에는 `tools/migrate/move_plan.py`가 없어(`git ls-tree 863a037 tools/migrate/` = `extract_selftest.py`뿐) 도구를 다시 돌릴 수 없다. 관찰이고 D0b base에서 다시 잰다)**:
   * A-6 일곱: `build_toy_lut`·`node_pole_estimate`·`solve_diode_stack_current`(SR), `find_differential_and_mirror_forks`·`folded_cascode_example`·`search_shared_finger_w`·`two_stage_ota_example`(SD).
   * A-7 둘: `MultiLeafHubParityVerdict`·`check_multi_leaf_hub_parity`(SD) -- **이게 전부다.**
2. **재생성 뒤(`plan_names_rg.json`)**: A-7 **0**, A-6 **셋**(`folded_cascode_example`·`search_shared_finger_w`·`two_stage_ota_example` -- 모두 레지스트리 행이 없는 단위). 행이 있는 A-6·A-7 단위는 재생성 뒤 자기 칸이 A-4 입력이 되어 `rule`이 A-4로 바뀐다(D0b 계약 6 (c), 실측 4' "A-7 2 → 0, A-6 7 → 3").
   → 지금 T-E의 A-6·A-7 표본 셋은 모두 행 있는 표본(○)이라 **D0b 병합 뒤 drift guard에서는 A-6·A-7이 아니라 A-4를 거친다**. A-6·A-7을 실제로 거치는 것은 D0b base(red 시점) 한 번뿐이다.
3. **각 A-6 대체 후보의 운명**:
   | 후보 | 레지스트리(`863a037`) | Phase 4 처리 | 후보 자격 |
   |---|---|---|---|
   | `build_toy_lut` | 행 있음(490행, `보류(Phase 4)`) | D-7 tests 픽스처로 이관(#4) -- 엔진에서 사라짐 | 불가 |
   | `node_pole_estimate` | 행 있음(494행) | D-6 test oracle로 이관 -- 엔진에서 사라짐 | 불가 |
   | `find_differential_and_mirror_forks` | 행 있음(506행) | UD-9 '6a 공동분석까지 유지' -- 그 뒤 삭제 가능 | 불안정 + 행 있음(재생성 뒤 A-4) |
   | `folded_cascode_example`·`two_stage_ota_example` | 행 없음 | 면제 E-a(예제 데이터) | **불가 -- D0b 계약 12 '회로 이름 없음'** |
   | `search_shared_finger_w` | **행 없음**(158행 첫 토큰은 `SharedFingerWCandidate`) | Phase 4 초안의 삭제·이관 목록에 없음(#2는 docstring 언급 1곳만 고침, `draft_p4_first.spec.md` 36·202행) | **가능** |
4. **`search_shared_finger_w` 손적용**(`863a037` SD 6179행, AST로 본 최상위 이름 참조): 엔진 안 참조자 0(사용처는 `workspaces/current-reuse-telescopic-ota-report/stick.py`·docstring뿐 -- `run_harness.py` 비도달, `d-dup-summary.md` 19행) → A-5 아님 → **A-6**:
   R(u) = {`SharedFingerWCandidate`(칸 `stick_diagram`, A-4 MOD7), `_quantize_to_grid`(칸 `stick_diagram(공용 유틸로 추출 가능)`, A-4 MOD7)} → 최댓값 MOD7 → 기대 줄기 `stick_diagram`(자기 파일 단위라 계약 5 MOD7 단언과도 맞다). 키트 `plan`(base·Q·RG)이 모두 `stick_diagram.py` A-6 -- 손적용과 같다.
5. **A-7의 규칙 검증은 실제 단위가 아니어도 이미 있다**: D0a test 합성 단계 `a7-isolated`(D0a card 283행)·`a6-ref-follow`(282행). design 30 §8 D0b 행도 "규칙 손적용 합성 입력은 D0a test 몫"이라 정했다.
6. **#2가 이미 같은 모양의 V5를 진다**: `test_ic5` `_DOMAIN_TABLE`의 `check_multi_leaf_hub_parity` 행 삭제(계약 6, V5 1~3), `test_s007_solve_diode_stack_current` 삭제(계약 7, V5 6). 지울 이름을 읽는 곳을 같은 card에서 정리하는 것이 #2의 원칙이다(의도 끝 문단). T-E 표 행은 그 목록에서 빠진 '읽는 곳' 하나다.
7. **#2 계약 3 GONE은 T-E를 잡지 못한다**: GONE은 `Name`·`Attribute`·`import`·정의를 센다. T-E 표는 이름을 문자열 상수로 든다 -- GONE은 통과하고 T-E만 FAIL한다(B1이 본 그대로).

---

## 2. 세 안 판정

### (a) 지워지지 않을 표본으로 바꾼다 -- **단독으로는 불가, A-6만 보강으로 채택**
* A-7: 대체 단위가 0이다(사실 1). 고를 것이 없다.
* A-6: 쓸 수 있는 후보는 `search_shared_finger_w` 하나(사실 3). 그것도 '엔진 참조자 없음'이 A-6의 정의라 **모든 A-6 단위는 본질적으로 미배선 코드 -- 언젠가 배선되거나 지워질 후보**다('만들면 배선' 원칙). 어떤 고정 표본도 영구 면역이 아니다.
* 그래도 보강할 이유가 있다(사실 2): 지금의 A-6 표본 `solve_diode_stack_current`는 행 있는 표본이라 D0b 병합 뒤 A-4만 거친다. 행 없는 A-6 표본은 이후 모든 card V1에서 실제로 A-6을 거친다 -- **Phase 4와 무관하게 지금 test 강도가 오른다.** 그래서 교체가 아니라 추가다(red 원천인 행 있는 표본은 그대로 둔다).

### (b) 표본을 실행 시점에 레지스트리에서 뽑는다(이름 하드코딩 없음) -- **기각**
* (d)-1의 존재 이유는 "도구 실행 없이 정해진 기대값"이다(D0b oracle 128~134행, design 30 §8 D0b 행 '동어반복 방지'). 기대값을 레지스트리·도구에서 실행 시점에 뽑으면 열 = 도구 출력(T-B)과 같은 동어반복이 되고, **거부 입력 R-E1(도구와 열이 함께 틀림)을 잡는 유일한 test가 사라진다**(D0b 168행: "이 표만 잡는다").
* 표본 '집합'만 실행 시점에 고르고 기대값은 고정하는 절충은 기대값이 이름에 묶이므로 이름 없이 불가능하다.
* '표본 단위가 트리와 레지스트리에 모두 없으면 은퇴' 같은 조건부 통과도 기각: 판정 대상 축소를 삭제 card의 code 커밋이 test·V5 없이 조용히 하게 된다(작성자≠검증자, '기준 약화는 사용자 승인', 메모리 '우회/skip 로직은 타당성 검토 후에만' -- 행 없는 표본은 정의가 실수로 사라져도 조용히 은퇴한다).
* 메모리 '이름·매직넘버를 코드에 넣지 마라'는 엔진 판정 코드가 회로·소자에 묶이는 것을 막는 규칙이다. 손적용 oracle 표의 정의 이름은 기대값 자체이고, D0b 계약 12는 이미 '회로·넷·소자 이름 0'과 '표본 이름은 oracle 표에서'를 구분해 허용한다. 위반 아님.

### (c) D0b는 고정 표본 그대로, #2가 V5로 T-E 표를 고친다 -- **채택**
* test 강도: D0b 시점 강도 그대로(A-6·A-7 손적용이 red 단언에 남는다). 삭제 뒤 잃는 것은 "존재하지 않는 단위 3개의 A-4 칸 drift guard"뿐이다(사실 2 -- 그 셋은 이미 재생성 뒤 A-4로 정해진다). 실질 손실 0.
* 작성자≠검증자: 판정 대상 축소가 삭제 card의 **test 커밋 + V5 승인 기록**으로만 일어난다. 사용자는 V5 범위 설명에서 축소를 본다.
* Phase 간 결합: 결합은 '삭제 card가 그 이름을 읽는 곳을 모두 정리한다'는 기존 원칙 하나로 흡수된다(#2가 IC5 표·`test_s007`로 이미 하는 일). D0b가 Phase 4 이름을 미리 알 필요가 없다.
* 대체 표본을 고르는 일은 D0b oracle의 몫이라 #2가 하지 않는다(B1 38행과 같음). A-7 실제 단위 표본은 0이 되지만 A-7 규칙 검증은 D0a 합성 단계 `a7-isolated`가 계속 맡는다(사실 5) -- 그래서 대체 card도 필요 없다.

---

## 3. D0b card 제안 문안 (`draft_p3_d0b.spec.md`)

**① oracle (d)-1 표 -- 161행 `solve_diode_stack_current` 다음에 한 행 추가**:

```
  | `search_shared_finger_w` | `stick_diagram` | × | A-6 | 레지스트리 행 없음(158행 첫 토큰은 `SharedFingerWCandidate`), 엔진 안 참조자 0(사용처는 workspaces 스크립트·docstring), 부르는 단위 `SharedFingerWCandidate`(칸 `stick_diagram`, MOD7)·`_quantize_to_grid`(칸 `stick_diagram(…)`, MOD7) → 최댓값 MOD7. 재생성 뒤에도 행이 없어 A-6으로 정해지는 표본 -- 행 있는 A-6·A-7 표본은 재생성 뒤 자기 칸(A-4)으로 정해진다(계약 6 (c)) |
```

**② 167행 괄호 수치 정정**: "(UD-6: 표본 26개·행 있는 24개 …)" → "(표본 **27**개·행 있는 24개 -- `_QUERY_CACHE_MAX`(UD-6)·`search_shared_finger_w`(행 없음)를 더함. …)". base red 크기(행 있는 표본 24 중 23)는 그대로.

**③ 130행 "규칙마다 한 행 이상(…)" 문장 뒤에 수명 규칙 추가**:

```
  '규칙마다 한 행 이상'은 **D0b base(재생성 전)에서 표본을 고를 때의 조건**이다 -- test는 규칙별 표본 수를 단언하지 않는다(규칙 손적용 검증의 영구 몫은 D0a 합성 단계 `a6-ref-follow`·`a7-isolated` 등).
  **표본 수명**: 표본 단위가 트리·레지스트리에서 사라지거나(삭제·이관) 배정이 바뀌어도 T-E는 그 표본을 건너뛰지 않고 FAIL한다(대상 행 아님·`plan` `mod` 없음·줄기 다름을 어긋난 표본 목록에 모은다).
  그 단위를 지우거나 옮기는 card가 **같은 card의 test 커밋에서** 이 표의 해당 행을 지우거나 기대값을 고치고, 그 변경을 V5 승인 범위(파일 `tests/contracts/test_p3_registry_dest.py`, 표를 담은 단위)에 올린다.
  남는 표본이 어느 규칙에서 0이 되어도 그 card가 대체 표본을 고르지 않는다(대체 표본 선택은 이 oracle의 몫 -- 필요하면 별도 card).
```

**④ 계약 11 (f) 끝에 표 위치 한 문장**(V5 단위를 미리 정해 뒤 card의 V5 범위 설명을 결정적으로):

```
    결정 사실 표본은 모듈 수준 상수 하나(`_P3RD_FACT_SAMPLES` -- 이름은 예시)의 리터럴로 둔다(원소 = 단위 이름·기대 줄기·행 유무·규칙 ID). 규칙 ID는 기록용이고 단언하지 않는다(계약 6 (c)와 같은 이유).
```

**⑤ '거부해야 할 입력' 표에 한 행 추가**(수명 규칙이 실제로 거부함을 보이는 반례 -- '게이트는 실제로 거부한다'):

```
| R-E2 | T-E 표본 부재 | 병합본 사본에서 행 있는 표본 하나의 정의와 레지스트리 행을 함께 지움(예: `check_multi_leaf_hub_parity` def와 그 행 -- `MultiLeafHubParityVerdict`는 남김) | D0b base에서 잰다(기대: `plan` 그 단위 없음, 그 밖 사상 0) / **T-E 표본**(대상 행 아님·`plan` `mod` 없음) · T-A~T-D 겨눔은 측정 결과로 적는다 |
```

(①~⑤는 test 커밋 전 문안 -- '기대값이 test 커밋 뒤에 바뀌지 않게'(134행). `search_shared_finger_w`의 근거는 D0b base에서 오케스트레이터가 다시 확인한다: 참조자 0·부르는 단위 둘의 칸, B26-1·B34 뒤에도 같은지.)

---

## 4. #2 card 제안 문안 (`draft_p4_first.spec.md`)

**① 계약 7 다음에 새 항목(번호는 card 편집 때)**:

```
7a. **D0b 결정 사실 표본(test, V5)**: `A/tests/contracts/test_p3_registry_dest.py`의 결정 사실 표본 표(D0b 계약 11 (f) 상수 -- 착수 때 D0b가 실제 커밋한 이름·구조로 확인)에서
    이 card가 지우는 단위의 행 -- `solve_diode_stack_current`(A-6), `MultiLeafHubParityVerdict`·`check_multi_leaf_hub_parity`(A-7) -- 셋을 지운다(D0b oracle (d)-1 '표본 수명').
    다른 행·기대값은 바꾸지 않고 대체 표본을 더하지 않는다. 지우지 않으면 병합본에서 T-E가 그 셋을 '대상 행 아님·`plan` `mod` 없음'으로 FAIL한다(계약 3 GONE은 문자열 상수라 잡지 않는다).
```

**② V5 승인 범위 목록(185행 뒤)에 추가**: `9 tests/contracts/test_p3_registry_dest.py, <표를 담은 단위>(D0b 커밋 판으로 확인 -- 모듈 상수면 '<module>')(예: 표 세 행 삭제)` → 승인 범위 **8건**.

**③ V5 범위 설명 원문 항목 추가**: `(d) D0b 결정 사실 표본에서 A-6 표본 1·A-7 표본 2 삭제 -- 실제 단위 A-7 표본이 0이 된다(A-7은 D0b 재생성 뒤 실제 트리에 이미 0; 규칙 검증은 D0a 합성 단계 a7-isolated가 맡는다). A-6은 행 없는 표본 search_shared_finger_w가 남는다(D0b ① 반영 시). 지워지는 셋은 재생성 뒤 A-4 칸으로 정해지던 표본이라 잃는 보호는 존재하지 않는 단위의 칸 drift guard뿐이다.`

**④ 계약 1·3 범위 문장**: '바뀌는 test 파일' 목록에 `tests/contracts/test_p3_registry_dest.py` 추가(V4 `test_lint`는 바뀐 test 파일 전체를 lint한다 -- 그 파일의 T-A~T-E는 판정 문장이 NO-SUBJECT라 #2 피검 22개와 겹치지 않는지 착수 때 재측정; B1·S2 연동).

**⑤ `p4_first_briefs.md`**: 1절 test-author 쓰기 경로·1.1 표·3.1 `git diff --name-only` 기대·3.3 V5 목록에 같은 파일 추가(review B1 §4 178·181행과 같음).

---

## 5. 착수 때 확인(정해진 것 아님 -- 측정)
* D0b가 실제 커밋한 표 구조·상수 이름·표본 수(27 기대), V5 단위 이름.
* D0b base에서 A-7 단위가 여전히 그 둘뿐인지, `search_shared_finger_w`가 여전히 행 없는 A-6인지(B26-1·B34·B33 병합 뒤 트리).
* #2 card base(F2 뒤)에서 그 세 표본이 표에 그대로 있는지(다른 card가 먼저 고쳤으면 그 판 기준).
