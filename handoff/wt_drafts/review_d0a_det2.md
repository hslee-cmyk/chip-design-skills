# D0a det2 개정 독립 재검토 (review_d0a_det2)

작성 2026-10-06. 검토자는 det2 개정을 쓰지 않았다. 대상은 `draft_p3_d0a.spec.md`(sha256 앞 16자리 `a11239aad8cd65c9`, 개정 전 사본 `.pre-det2.bak`), `d0a_briefs.md`(`58e886c7a6ea2878`), `d0a_determinism.md`이다. 앞 검토는 `review_d0a_det.md`다.
기준은 gate `master` `6c724de`이고, 실제 저장소 HEAD와 gate/master가 모두 이 커밋이다. 실제 저장소는 읽기만 했다. `2183f2e..6c724de`의 diff는 b26pre spec·interface 두 파일뿐이다. design 30·계획 N3.10·레지스트리·`tools/`는 바뀌지 않았다.
스크래치는 `C:/g325`만 썼다(TMP/TEMP `C:/g325/tmp`, `git clone -c core.autocrlf=false --no-local --no-hardlinks`, origin 제거, cd 없음). 작업이 끝난 뒤 삭제했다. 작성자 키트 `p3kit_det2/`의 출력과 스크립트는 증거로 쓰지 않았고 열어 보지도 않았다.

## 판정: **S 1건, minor 4건. B 없음. 사용자 질문 없음.**

앞 검토의 S1과 m1~m6은 문언상 모두 반영되었다. 내가 card 문장만으로 단계를 다시 구현해 돌려 보니, 원소 4개·시드 0~7 구성은 S1이 지적한 누출(`unassigned`·`upward`·`conflicts`·`reg_mismatch`·`cycles` 바깥 순서)을 모두 잡는다.
그러나 card 문장을 **가장 단순하게 읽어 만든 구성**은 아래 다섯 종류의 잘못된 구현을 통과시킨다(S2). 그 가운데 하나(A-5 내용 비결정)는 card가 괄호 안에서 "(i)에서 FAIL한다"고 주장한 경우다.

## 1. 앞 검토 지적의 해소 여부

| 지적 | 해소 | 확인 |
|---|---|---|
| S1 원소 2개·시드 0·1 | 예 | 목록마다 원소 4개 이상, `cycles` 2개, 시드 0~7, 시드 증인 (v). 아래 재구현에서 S1이 다룬 누출은 모두 (i)·(ii)에서 FAIL했다 |
| m1 근거 인용 | 예(card) | design 30 §6.3 "CLI·출력·exit의 **정본은 D0a spec card 계약 1~4**"를 `6c724de`에서 확인했다. 다만 보고 `d0a_determinism.md` 46행은 아직 "§8.1(663행) … 결정적으로"를 근거로 든다(보고 전용이라 경미; 아래 m-d) |
| m2 정수·`mod_imports` 배치 | 예 | 정수는 수 오름차순. `__future__` → `from` 줄(모듈 이름순, 항목 문자열순) → `import` 줄(줄 문자열순)이고, 정의가 한 문장에만 있다 |
| m3 (e5) 범위·우선순위 | 예 | A-0·A-1·`conflicts`가 아닌 단위에 적용하고, A-2 판정 전에 보며, A-3보다 먼저 본다. 아래 2절 |
| m4 `upward` 수 | 예 | 재구현 구성에서 `upward` = 6(lift-cap 4 + 순환 2)을 실측했다 |
| m5 (iv) 별도 커밋 | 예 | C0의 자식 커밋 네 개. 재구현에서 (iv-a)~(iv-d)의 기대가 C0의 (i)~(iii)과 충돌하지 않았다 |
| m6 보고 인용 행 | 예 | `d0a_determinism.md` 19행이 m1 spec 130·175·212행으로 고쳐졌다 |

* `role_paths.parse_spec_card`(gate `6c724de` `git archive`): 개정 후와 개정 전 모두 통과했다. id `20260930-p3-move-plan-tool`, phase 3, red-green, gate_change no, approval은 그대로다.
* `interface_card.py --root <6c724de + G1 시제품("installed 4") 복제본>`: exit 0, **'기존 함수 0개'**.
* briefs 쪽 det2 반영(1절 5, 2절 7·9, 3.1)은 card 문언과 같다. 필수 단계 수는 20 그대로다.

## 2. (e5) 범위·우선순위와 design 30(`6c724de`)

* **D-31·§6.2와 어긋나지 않는다.** D-31은 승격·단조 고정점이고, §6.2는 한 단위 키에 레지스트리 행이 여럿인 경우를 정하지 않는다. (e5)는 배정을 새로 만들지 않고 fail-closed 정지(exit 2)만 더한다.
  A-1 `conflicts`를 빼는 것은 conf 문언(그 단위는 뒤 규칙이 칸을 읽지 않음)과 맞는다. A-3보다 먼저 보는 것은 "어긋난 칸을 조용히 버리지 않는다"는 원칙과 맞는다.
* **실제 트리 재측정(`6c724de`, 독립 스크립트)**: 레지스트리 함수 표 행은 379개다. 행이 둘 이상인 키는 `SemiEmpiricalGmIdLUT`(14행, MOD 하나짜리 칸이 모두 MOD4, N3.10 MOD1 토큰이라 A-1) 하나뿐이다. 나머지 하나는 단위가 아닌 중첩 행 `└ topology_fn`이다.
  (e5) 조건이 참인 키는 **범위를 어떻게 잡아도 0**이다. 그래서 범위·우선순위를 어떻게 정하든 실제 트리의 배정은 바뀌지 않는다. A-3 행이 둘 이상인 키도 0이다.
  내 키 집계는 이름 363개로 보고의 359개와 다르다. 함수 칸을 읽는 방식(중첩 행 기호 등)의 차이일 뿐이고, 결론(0)은 같다.
* (minor m-a) **A-2 포함의 근거 문장.** card는 A-0·A-1을 빼는 이유로 "배정에 레지스트리 칸을 읽지 않으므로"를 든다. 그런데 A-2로 정해지는 레코드 클래스도 칸을 읽지 않는다. 그래서 그 이유만으로는 A-2 단위를 넣는 결정이 설명되지 않는다.
  넣는 것 자체는 옳다고 본다. A-2는 참조자에 N3.10 MOD 배정이 없으면 A-3·A-4로 떨어질 수 있고, 그 여부는 고정점 뒤에야 정해진다. 그러니 고정점 전에 정적으로 보는 편이 결정적이다. 이 이유를 한 문장으로 적을 것.
  덧붙여 (iv) 네 갈래는 A-2 포함을 고정하지 않는다. A-2 단위를 (e5)에서 빼는 구현(`e5_noA2`)이 두 구성 모두에서 PASS했다. 고정하려면 (iv-e)를 둘 것: 참조자가 있는 dataclass `Q`에 칸 `m2`·`m5` 두 행 → exit 2.
* (minor m-b) **A-3 행이 여럿인 경우.** A-3은 "셀의 가장 작은 MOD 번호"이고, 한 키에 MOD 둘 이상인 칸이 여러 행이며 그 최솟값이 서로 다른 경우는 어느 문장도 정하지 않는다. (e5)의 이유("어느 행에서 읽을지 근거가 없다")가 이 경우에도 그대로 적용된다.
  첫 A-3 행을 고르는 구현이 card 문언을 어기지 않고 (iv)도 통과한다. 결정성 문단의 일반 문장("표 행을 읽는 순서와 무관")이 그런 구현을 금지하기는 하지만, 어떤 결정적 규칙을 쓸지는 비어 있다.
  실제 트리에서는 0이다. 한 문장을 더할 것: "모든 A-3 칸의 가장 작은 MOD들의 최솟값"(시제품 방식) 또는 (e5)처럼 exit 2.

## 3. 합성 단계 `determinism`의 재구현 실측

방법: card 286~299행 문장만 보고 구성기와 판정기를 새로 썼다(`C:/g325/stage.py`, 삭제함). 판정 내용은 다음과 같다.
* (i) 시드 0~7 stdout 바이트가 같다. exit 1, `FAIL`.
* (ii) 첫 세 키, 모든 사전 키가 이름순이다. 다섯 목록은 코드 포인트 원소 정렬 순서이고 원소는 구성의 집합과 같다.
* (iii) `check --card ALL` base = head에서 시드 0~7 바이트가 같다.
* (iv-a~d) C0의 자식 커밋에서 확인한다.
* (v) 시드 증인. 실측에서 시드 8개가 집합 반복 순서 8가지를 냈다.

피검 구현은 `p3kit_m1/move_plan_sim.py`(시제품)를 바탕으로 내가 만들었다(`mk.py`, 측정 전용). '계약 순서' 구현은 정렬 출력에 det2 (e5)를 더한 것이다. 변형은 그 위에 누출 하나씩을 넣었다.
구성은 둘이다.
* **natural**: card 문장을 가장 단순하게 따랐다. 이름은 모두 소문자·밑줄이고, A-5 단위는 참조자가 하나, 배정 단위는 33개다.
* **rich**: natural에 다음을 더했다. 대소문자·`_` 접두가 섞인 이름, 참조자가 MOD3·MOD5 둘인 A-5 상수 4개, 한 MOD(`m6.py`)의 `mod_imports`에 `from` 줄 4개와 `import` 줄 4개. 배정 단위는 46개다.

| 구현 | natural | rich |
|---|---|---|
| 계약 순서(정답) | **PASS** | **PASS** |
| 시제품 그대로 | FAIL (i)·(ii)·(iv-a)·(iv-c) | FAIL (ii)·(iv-a)·(iv-c) |
| `unassigned`·`upward`·`conflicts`·`reg_mismatch` 집합 순서 누출 | FAIL (i)·(ii) | FAIL (i)·(ii) |
| `cycles` 바깥 순서 누출 | FAIL (i) | FAIL (i) |
| `check` `assigned`·발견 목록 누출 | FAIL (iii) | FAIL (iii) |
| `reexports` 줄 안 항목 누출 / `mod_imports` `from` 줄 안 항목 누출 | FAIL (i) | FAIL (i) |
| **`mod_imports` `from` 줄 순서 누출**(모듈 집합 반복) | **PASS(놓침)** | FAIL (i) |
| **원소 정렬 키 대소문자 무시(`str.lower`)** | **PASS(놓침)** | FAIL (ii) |
| **원소 정렬 키 사전식(구두점 무시·대소문자 무시 -- 로캘/ICU 모양)** | **PASS(놓침)** | FAIL (ii) |
| **A-5 참조자를 집합 첫 원소로(내용 비결정)** | **PASS(놓침)** | FAIL (i)(서로 다른 출력 6)·(ii)(`reg_mismatch` 7 ≠ 4) |
| **`import_conflicts` 집합 순서 누출** | **PASS(놓침)** | **PASS(놓침)** -- 두 구성 모두 `import_conflicts`가 빈 목록 |
| 첫 행 고름((e5) 없음) | FAIL (iv-a)·(iv-c) | FAIL (iv-a)·(iv-c) |
| (e5)를 A-3 뒤에(det 판 우선순위) | FAIL (iv-c) | FAIL (iv-c) |
| (e5)를 A-1 단위에도 | FAIL (iv-d) | FAIL (iv-d) |
| (e5)에서 A-2 단위 제외 | PASS | PASS (m-a) |

* **(S2) card 문장만으로 만든 구성은 결정성 문단이 금지하는 구현 다섯 종류를 통과시킨다.**
  card 괄호의 주장 "A-5 참조자를 집합의 첫 원소로 고르는 구현(내용 비결정)은 (i)에서 FAIL"은 **참조자가 서로 다른 MOD에 둘 이상인 A-5 단위가 있을 때만** 성립한다. 지금 문장("A-4·A-5·A-K 단위를 섞어")은 그런 단위를 요구하지 않는다.
  `mod_imports` 줄 순서는 D0b 산출물을 거쳐 M card MOD 파일 머리에 **그대로** 복사된다(`p3kit_m2_m9/gen_move.py`·`mkcards.py` "그대로"). 그래서 바이트 재현이 가장 직접적으로 필요한 목록인데, 한 MOD에 `from` 줄이 둘 이상이어야 한다는 요구가 없어 그 누출이 빠진다.
  코드 포인트 정렬(계약 문언)도 이름이 모두 소문자이면 대소문자 무시 정렬이나 로캘 정렬과 구별되지 않는다. 실제 트리에는 `SemiEmpiricalGmIdLUT`·`_kv_table` 같은 이름이 섞여 있어 갈린다.
  `import_conflicts`(와 `import_time_high`·`absent_split`)는 C0에서 빈 목록이라 순서를 겨누지 못한다.
  **고칠 문안**(구성 요구로 더한다):
  (a) 참조자가 서로 다른 MOD에 있는 A-5 단위(상수) 4개 이상, 기대 MOD = 가장 낮은 참조자 MOD.
  (b) 한 MOD의 `mod_imports`에 `from` 줄 4개 이상과 `import` 줄 2개 이상(서로 다른 외부 모듈), 그리고 그 목록 전체를 기대값으로 단언한다(줄 순서는 계약 2 `mod_imports` 문장대로).
  (c) 순서를 단언하는 목록의 단위 이름에 대문자로 시작하는 이름·`_` 접두 이름·소문자 이름을 섞는다. 코드 포인트 순서와 대소문자 무시 순서가 달라야 한다.
  (d) `import_conflicts`는 그 목록을 4개 이상 만드는 자식 커밋으로 겨누거나(split 파일 둘이 같은 이름 넷을 다른 출처로 묶고 같은 MOD로), 이 단계가 겨누지 않는 목록이라고 괄호에 명시한다.
  그리고 괄호 주장을 "(a)~(c)가 있는 이 구성에 대해서만"으로 고친다. rich 구성(a·b·c 포함)에서는 위 다섯 가운데 넷이 잡혔다. 남은 하나(`import_conflicts`)는 (d)가 닫는다.
  작성자 '작성 전 실측 12'의 "내용 비결정 FAIL"은 작성자 구성이 (a)를 갖췄기 때문으로 보인다(키트는 열지 않았다). 그 구성 요소가 card 문장에는 없다. 그래서 test-author가 card만 보고 만들면 결과가 갈린다. 앞 검토 S1과 같은 종류다.
* (minor m-c) **튜플 값 목록.** 결정성 문단은 "계약이 순서를 정한 것 밖은 모두 원소 정렬"이라고 한다. 이 문장을 문자 그대로 읽으면 `import_conflicts` `origins`의 `origin`(`binding_origin` 튜플 -- JSON 목록) 안 원소까지 정렬해야 한다. 그러면 뜻 있는 순서(`["def", 파일, 이름]`)가 깨진다.
  정렬하는 구현과 하지 않는 구현이 서로 다른 바이트를 내면서 둘 다 문언에 맞는다. "튜플 값(`origin` 등 출처 표기)은 목록이 아니라 위치에 뜻이 있는 값이라 정렬하지 않는다"를 예외 목록에 더할 것.

## 4. `mod_imports` 배치가 기존 측정과 같은 바이트인가

`p3kit_m1/move_plan_sim.py`(D0b 실측에 쓴 `plan`, `draft_p3_d0b.spec.md` 233행)와 `p3kit_m2_m9/move_plan_sim.py`(같은 파일, diff 0), 그리고 `move_plan_alltok.py`는 모두 같은 순서로 줄을 만든다.
* `from __future__ import <sorted>`
* `for m in sorted(frm)`: `from m import ", ".join(sorted(items))`(항목 = `n` 또는 `n as v`)
* `sorted(set(imp))`(`import` 줄 문자열순)

card det2 문장과 줄 단위로 같다. M card 생성기(`gen_move.py`·`gen226.py`)는 이 목록을 순서대로 head/tail로 나눌 뿐 다시 정렬하지 않는다. 그래서 **"기존 측정과 같은 바이트" 주장은 `mod_imports` 줄에 대해 맞다.**
다만 기존 측정 JSON 전체(최상위 키 순서, `conflicts`·`reg_mismatch` 원소 순서, `rule_counts_sim`)는 시제품 순서라 계약 출력과 바이트가 다르다. card가 주장하는 것은 줄 배치뿐이므로 충돌은 없다.

## 5. 고칠 곳 요약(오케스트레이터)

1. **S2**: `determinism` 구성에 (a) 다중 MOD 참조자 A-5 단위 4개, (b) 한 MOD에 `from` 줄 4개 이상·`import` 줄 2개 이상 + 그 목록 단언, (c) 대소문자·`_` 혼합 이름을 넣는다. (d) `import_conflicts`는 자식 커밋으로 겨누거나 범위 밖이라고 적는다. 괄호 주장의 범위를 고친다.
2. m-a: (e5)에 A-2 단위를 넣는 이유를 한 문장으로 적고, 선택으로 (iv-e)를 둔다.
3. m-b: A-3 행이 여럿이고 최솟값이 다를 때의 규칙을 한 문장으로 정한다.
4. m-c: 튜플 값 `origin`을 원소 정렬에서 뺀다.
5. (minor m-d) `d0a_determinism.md` 46행의 §8.1(663행) 근거 문장을 card m1 정정과 맞춘다(보고 전용).

card 해시가 다시 바뀌므로 interface card를 다시 생성할 것(이번 판은 '기존 함수 0개').
