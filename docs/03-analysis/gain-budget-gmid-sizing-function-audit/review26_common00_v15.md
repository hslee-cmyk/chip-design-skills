# review26 -- `00-common` design v1.5 좁은 확인(review25 Q-01~Q-05·R-02 잔여 닫힘)

* 대상: 커밋 `cb8cb4a`의 `docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md` v1.5(609줄), `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` v5.19, history의 'v1.4 확인(review25) 반영' 문단
* 기준: review25의 Q-01~Q-05, R-02 잔여, 지정 점검 1~6
* 범위: v1.5 diff가 건드린 곳만 본다. 바뀌지 않은 부분은 다시 감사하지 않았다.
* 검증자: 독립 검증 agent. 이 설계도, review21~25도 쓰지 않았다.
* 측정 스크립트는 저장소 밖 scratchpad `review26/`에 있다.
  * `conftest.py` + `tests/test_ic11.py`: §9.3 xfail 규칙을 그대로 구현한 모의 conftest와 IC11 세 케이스(2레일 `"4"`, 3레일 `"6a"`, 거부 `"6a"`). red 수집 훅 포함. pytest 9.0.2, Python 3.14.
  * `cells.py`(+`cells.txt`): 표 셀 수 검사
* 저장소에서 바꾼 파일은 이 보고서 하나다.
* 심각도: **S1** = 승인을 막는다 / **S2** = 승인 전에 고친다 / **S3** = 경미

---

## 1. 닫힘 표

| ID | 판정 | 근거(인용) |
|---|---|---|
| Q-01 | **닫힘** | 계획 N6.1 4행: "TS4 → DF-35 → DF-36 → `00-common` CC-4의 앞부분(실패 클래스·`FailureRecord`·`exit_code_for`와 DF-37의 하네스 `run()` 몫) → CC-7·CC-8 → 나머지". 같은 순서가 설계 §11.1, §18.1("TS4 → DF-35 → DF-36 → CC-4 앞부분 → CC-7·CC-8 → CC-4 나머지(DF-37 광범위 except)·CC-5와 나머지 DF"), §10 '적용 시작'("그 앞 card(TS4, DF-35·36, CC-4 앞부분, CC-7 자신"), 계획 DF-35 행("CC-7·CC-8보다 먼저")에 있다. CC-7·CC-8이 기대는 `FAILURE_CLASSES`·`exit_code_for`·`FailureRecord`·하네스 `run()` 삼킴 제거가 모두 앞부분에 든다. 남은 것은 표기뿐이다: §14 CC-4·CC-7·CC-8 행이 갱신되지 않았다(T-05, S3). |
| Q-02 | **부분** | §9.3: "**xfail 조건**: 표식 Phase가 현재 Phase보다 뒤이거나, 같고 엄격 대상이 아닐 때 … **엄격 대상**: `--gmid-dod` … 와 `--gmid-strict <IC,...>`". '만료 = Phase 시작' 모순은 풀렸다. Phase 4 첫 card TS4는 더 이상 막히지 않는다(§2 실측). 그러나 엄격 적용이 IC 단위이고 활성화 card 한 건에만 걸린다. 그래서 새 결함 두 건이 생겼다: 6a에서 막히는 경로(T-01)와 활성화 뒤 회귀가 DoD까지 조용히 통과하는 경로(T-02). |
| Q-03 | **닫힘** | §8.1: "실행 명령에 `--continue-on-collection-errors`를 붙인다 -- 수집 오류 하나가 세션을 멈추면 같은 실행의 실행 단계 red가 기록되지 않는다(review25 Q-03)". |
| Q-04 | **부분** | §9.1: "base와 head 계획서를 같은 `read_plan_tables`로 파싱해 **파싱 값**(`v_intro`, `ic_parts`, `ic_test`, `phase_order`)이 다르면 diff다 … **head 계획서의 표를 못 읽으면 그 병합을 거부**한다". 계획 EL4에도 '강제 test' 열과 파싱 값 정의가 들어갔다. 남은 것은 셋이다. (1) '흐름 안에서는 base가 깨지지 않는다'는 전제가 오케스트레이터의 계획서 직접 커밋에서 성립하지 않는다(T-03, S2). (2) 공격 16이 갱신되지 않았다(T-04, S3). (3) 'head'가 어느 커밋인지, 승인 기록을 표 diff에 대응시키는 규칙이 없다(T-10, S3). |
| Q-05 | **닫힘** | `grep`(설계·계획): `PHASE_ORDER`, `일치 test 명세`, `V_CHECKS`, `IC_TABLE`, `ic_table`, `자기검사` 모두 0건. 계획 N6.2 `0(문서)`와 N9.1 `00-common` 행은 "검증 도구가 계획서에서 직접 읽는 규칙(사본 없음 …)"으로 바뀌었다. N9.1 `05` 행은 "N6.1 전체(Phase 순서)", 설계 §15 'V/IC 표·Phase 순서' 행은 "검증 도구가 계획서에서 직접 읽는 규칙"이다. 남은 옛 흔적은 설계 §2 표 52·57행의 "일치 검사"와 §18.2 `common-ic-table`뿐이다(review25 Q-11, S3). |
| R-02 잔여 | **닫힘**(S3 하나) | §8.1 '신규 심볼 판정': "입력은 interface card의 '신규 시그니처' 절의 모듈 경로와 심볼 이름 목록이다. 예외의 `name` … 이나 `name_from` … 이 그 목록에 있으면 신규 심볼 import다". 판정 입력이 정해졌다. 대조 방식이 느슨한 점은 T-09(S3)에 적는다. |

**집계: 닫힘 4(Q-01·Q-03·Q-05·R-02) / 부분 2(Q-02·Q-04) / 안 닫힘 0**

review25 S3의 상태:

| ID | 상태 |
|---|---|
| Q-06 `from_phase` 소비자 없음 | 닫힘. 필드를 지웠다(§9.1 `ICPart`에 `from_phase` 없음, §9.2 "별도 필드가 필요 없다") |
| Q-07 IC11 거부 케이스 표식 | 부분. "IC11의 선행 거부 케이스(N4.1)는 … `6a` 표식을 단다"로 정했다. 대신 T-01이 생겼다 |
| Q-08 열 식별·인접성·줄 끝·파서 재사용 | 남음 |
| Q-09 red 명령에 `--gmid-phase` 없음 | 남음. v1.5에서 더 무거워졌다(T-08) |
| Q-10 diff 해시 경계 입력 | 닫힘. §8.2 "거부: 경로가 정규화되지 않음 …, 양쪽 모두 없음, base·head blob이 같음 …, `git cat-file -t`가 `blob`이 아님" |
| Q-11 · Q-12 · R-11 · R-13 · R-14 | 남음. 모두 v1.5가 건드리지 않은 곳이다 |

---

## 2. 지정 점검 2: 새 xfail 규칙 시나리오(모의 실측)

모의 conftest는 §9.3 문장을 그대로 구현했다. 조건은 "표식 > 현재 → xfail", "표식 = 현재이고 `--gmid-dod`도 아니고 `--gmid-strict`에 그 IC가 없음 → xfail(non-strict)"이다. red 수집 훅은 §8.1대로 `pytest_runtest_makereport`에서 `call.excinfo`를 기록한다. 실측 결과(IMPL2 = DEC-60 2레일 구현 여부):

| 실행 | IMPL2 | 결과 | 수집 훅 기록 |
|---|---|---|---|
| `--gmid-phase 4` | 0 | 3 xfailed | 세 케이스 모두 AssertionError |
| `--gmid-phase 4` | 1 | 2 xfailed, **1 xpassed** | 3rail·reject |
| `--gmid-phase 4 --gmid-strict IC11` | 0 | **1 failed**(2rail), 2 xfailed | 세 케이스 |
| `--gmid-phase 4 --gmid-strict IC11` | 1 | 1 passed, 2 xfailed | 3rail·reject |
| `--gmid-phase 4 --gmid-dod` | 0 / 1 | 1 failed / 1 passed, 2 xfailed | -- |
| `--gmid-phase 6a --gmid-strict IC11` (2레일만 구현) | 1 | **2 failed**(3rail·reject), 1 passed | -- |
| 옵션 없음 | -- | UsageError, 수집 없음 | 없음 |

**수집 훅은 xfail 케이스의 `call.excinfo`도 받는다.** 그래서 red 해시는 strict 여부와 무관하게 재현된다. 다만 병합본 쪽 결과가 strict가 없으면 PASS가 아니라 XPASS다.

시나리오별 판정:

1. **Phase 4 첫 card TS4(IC11 2레일 케이스 있음)**: `--gmid-phase 4`이고 strict가 없다. `"4"` 케이스는 XFAIL이고 V1은 통과한다. **Q-02의 원래 막힘은 풀렸다.**
2. **IC11을 활성화하는 card(MG1, 계획 720행 "옛 키 거부 게이트 + IC11 … DF-19·24·26과 같은 변경 단위")**: base에서 `--gmid-strict IC11`로 돌리면 `"4"` 케이스가 FAIL(AssertionError, 허용 타입)이고, 병합본에서는 PASS다. **V2 red-green은 기계적으로 만족할 수 있다.** 조건은 둘이다.
   * (i) red 수집 명령과 merge gate 재실행 명령에 `--gmid-phase 4`가 있어야 한다. 없으면 UsageError로 전부 실패한다(T-08).
   * (ii) V2의 "새·바뀐 test"에 **Phase 1부터 있던 IC11 test**가 들어가는지 정해야 한다. 활성화 card의 test 커밋은 이 test를 바꾸지 않을 수 있다. xfail은 conftest가 계산하기 때문이다(T-08).
3. **Phase 4 DoD 실행**: `--gmid-dod`에서 `"4"`는 엄격하고 `"6a"` 케이스는 xfail이다. 맞다.
4. **6a, IC7(6a + 괄호 6c)**: `"6a"` 케이스는 활성화 card의 strict나 DoD에서 엄격해진다. `"6c"` 정지 케이스는 표식이 현재보다 뒤라 strict여도 xfail이다. 조건식은 맞다. 문장 "엄격 대상의 test는 xfail 없이 PASS여야 한다"는 IC 전체로 읽히므로 조건식과 어긋난다(T-07).
5. **6a, IC11 3레일과 거부 케이스(둘 다 `"6a"`)**: 두 케이스는 **다른 card**가 활성화한다. 거부 케이스는 GB0 로드 게이트(공격 13)가 먼저이고, 3레일은 그 뒤다. 그런데 strict는 IC 단위다. 그래서 GB0 card가 `--gmid-strict IC11`을 받으면 아직 구현되지 않은 3레일 케이스까지 엄격해져 V1이 FAIL한다(실측 마지막 줄 "2 failed"). 받지 않으면 거부 케이스는 자기 구현 card에서 엄격 확인을 받지 못한다. **막히거나 확인이 빠진다(T-01, S2).**
6. **이후 7a 실행**: 모든 표식이 ≤ 6c < 7a이므로 전부 활성이다. IC7의 "6a 이후 매 Phase"도 성립한다. 맞다.
7. **활성화 뒤 같은 Phase의 다음 card**(예: Phase 4에서 MG1 card 뒤에 오는 U-27 LUT 재생성·CC-5·다른 DF): strict는 "그 IC를 활성화하는 spec card"에만 걸린다. 그래서 다음 card가 IC11 `"4"`를 다시 깨도 결과는 XFAIL이고 V1은 PASS다. **Phase DoD까지 조용히 통과한다**(T-02, S2). 회귀를 낸 card도 특정되지 않는다.
   * strict 목록의 출처도 문제다. spec card '관찰 가능한 계약'이라는 산문 칸이고(계획 N3.12.3 필드 목록에 기계 판독 필드가 없다), merge gate는 auditor가 `--gmid-strict`를 줬는지 검사하지 않는다. auditor가 빠뜨리면 활성화 card 자신도 조용히 통과한다.

---

## 3. 지정 점검 3: Q-04

* **닫힌 것**: 파싱 값 diff, head 파싱 실패 시 거부, '강제 test' 열의 보호(§9.1, 계획 EL4).
* **틈 1 -- 흐름을 타지 않는 계획서 커밋(T-03, S2)**: §9.1은 "흐름 안에서는 base 계획서가 깨진 채 병합되지 않는다. 흐름 밖(**사용자 직접 커밋**)에서 base가 깨지면 …"이라고 한다. 그러나 계획서를 쓰는 주체는 오케스트레이터다(N3.12.2 '`docs/01-plan/**`'). EL4는 spec card 병합(N3.12.3 순서 6·7)에만 돈다. 게다가 판정 기록이 없으면 거부하므로, 계획서만 바꾸는 커밋은 구조상 EL4를 통과할 수 없다. 그래서 계획서 개정은 base에 직접 커밋된다. 이 `cb8cb4a`도 master 직접 커밋이다.
  * 결과: §2 정정의 근거인 "사본이 막던 경로는 EL4의 '판정 표 diff 승인 기록 필수'가 막는다"가 **계획서 개정의 정상 경로에서 발동하지 않는다.** review22 N-01 같은 표 파손도 같은 경로로 base에 들어간다.
  * 표 파손 쪽은 교착이 아니다(오케스트레이터가 다음 직접 커밋으로 고칠 수 있다). 하지만 "사용자 직접 커밋"이라는 서술은 사실과 다르다.
  * 수정: 계획서 개정이 base에 들어오는 경로를 하나로 정한다. 예: EL3 pre-commit이 `docs/01-plan/**` staged 변경에 `read_plan_tables`(head 파싱)와 판정 표 diff 승인 검사를 돌린다. 또는 계획서 개정도 판정 기록 없는 `doc` 모드로 merge gate를 거친다. 이렇게 정한 뒤 §9.1의 '흐름 밖' 문장을 고친다.
* **틈 2 -- 'head'와 승인 대응(T-10, S3)**
  * `<base>..<branch>`에서 head가 브랜치 끝(순서 6의 audit 병합 커밋)이라는 것이 적혀 있지 않다. 중간 커밋의 표 개정·파손은 순 diff에서 사라지는데, 순 diff 기준이 의도라면 그렇다고 적는다.
  * 표 diff를 덮는 승인 기록의 대응 규칙이 없다. 조건은 `diff_path`에 계획서가 있고, 그 경로의 base/head blob이 이번 base/head의 계획서 blob과 같아야 한다.
  * base 브랜치가 앞서 나간 뒤(재기반 안 함) 비교하면 다른 병합의 표 개정이 거꾸로 diff로 잡힌다. 오거부 쪽이라 안전하다.
* **base가 흐름 밖에서 깨진 경우**: 모든 병합이 거부된다(공격 16 (ii)). v1.5는 복구를 흐름 밖에 맡겼다. 틈 1을 고치면 이 경우는 사용자 직접 커밋으로만 좁혀진다.

---

## 4. 지정 점검 4: Q-01 순서의 정합

| 위치 | 문구 | 정합 |
|---|---|---|
| 계획 N6.1 4행 | TS4 → DF-35 → DF-36 → CC-4 앞부분 → CC-7·CC-8 → 나머지: TS4, DF-01~…·35~37, … | 순서는 맞다. '나머지:' 목록이 앞에 나온 TS4·DF-35·36·37을 다시 적어 범위 목록과 순서 목록이 섞였다(S3, T-05) |
| 설계 §10 '적용 시작' | 그 앞 card(TS4, DF-35·36, CC-4 앞부분, CC-7 자신) | 맞음 |
| 설계 §11.1 | TS4 → DF-35 → DF-36 → CC-4 앞부분(…) → CC-7·CC-8 → 나머지. "두 도구의 실패 처리와 oracle이 CC-4 앞부분에 기댄다" | 순서는 맞다. 다만 '그 앞 card의 무동작' 목록(TS4, DF-35·36, CC-7·CC-8)에 **CC-4 앞부분 card가 없다**. 이 card는 동작 변경이다(하네스 `run()`이 예외를 삼키지 않고 비0 exit). 지금 예외로 끝나는 회로(I-C11 대상)의 결과가 바뀐다(T-06, S3) |
| 설계 §18.1 | … → CC-4 앞부분 → CC-7·CC-8 → CC-4 나머지(DF-37 광범위 except)·CC-5와 나머지 DF → CC-9(5) → CC-6(6a) | 맞음 |
| 설계 §14 CC-4 | "§7.1(MOD2·MOD4 형식), §9.3 N3.14 부분, DF-37 광범위 except 재raise, 진입점 exit code" | 앞부분/나머지 구분이 없다(T-05) |
| 설계 §14 CC-7 / CC-8 | "DF-35 뒤" / "DF-35·36 뒤" | **CC-4 앞부분 뒤**가 빠졌다. §14만 보고 card를 나누면 Q-01이 되살아날 수 있다(T-05) |
| 계획 DF-35·36·37 행 | "4(`00-common` CC-7·CC-8보다 먼저)", "4(CC-8보다 먼저)", "4(`00-common` CC-4)" | 맞음 |

---

## 5. 새 결함(v1.5 diff에서 생긴 것만)

### S1

없음.

### S2

#### T-01 (S2) xfail 엄격 적용이 IC 단위라, 같은 Phase 표식의 케이스를 서로 다른 card가 활성화하면 막히거나 확인이 빠진다
* **위치**: §9.3 "`--gmid-strict <IC,...>`(그 IC를 활성화하는 spec card의 V1·V2 실행)", "IC11의 선행 거부 케이스(N4.1)는 … `6a` 표식을 단다".
* **근거**: §2 시나리오 5와 실측 "`--gmid-phase 6a --gmid-strict IC11` → 2 failed". IC11의 `"6a"` 케이스는 둘이다. 거부 케이스는 GB0 로드 게이트 card가, 3레일 케이스는 3레일 지원 card가 만든다. IC7의 `"6a"` 케이스들(library 실행·발동 계수 0·발동표)도 한 함수에 묶인 계약 여럿이다.
* **영향**: 앞선 card가 strict를 받으면 뒤 card 몫 때문에 V1이 FAIL한다. 받지 않으면 그 card의 계약은 엄격 확인 없이 병합된다.
* **수정**: 엄격 단위를 케이스로 내린다. 예: 표식에 케이스 키 `gmid_ic("IC11", phase="6a", part="reject")`를 달고 `--gmid-strict IC11:reject`로 준다. 대조 test는 `phase`만 본다.

#### T-02 (S2) strict가 활성화 card 한 건에만 걸려, 활성화 뒤 같은 Phase의 회귀가 DoD까지 XFAIL로 통과한다
* **위치**: §9.3 "그래서 담당 Phase의 앞쪽 card는 그 IC 때문에 막히지 않고, IC를 활성화하는 card와 Phase DoD에서는 반드시 PASS가 확인된다".
* **근거**: §2 시나리오 7. 활성화 뒤 card의 V1은 `--gmid-strict` 없이 돈다. 그래서 IC 케이스가 다시 FAIL해도 XFAIL이다. 게다가 strict 목록의 출처가 산문('관찰 가능한 계약')이고 merge gate가 확인하지 않는다(WP-21·WP-02). auditor가 빠뜨리면 활성화 card 자신도 조용히 통과한다.
* **영향**: 계획 V1("전체 test 실행")이 활성화된 IC를 card 단위로 지키지 못한다. 회귀는 DoD에서야 드러나고, 원인 card가 특정되지 않는다.
* **수정**:
  * spec card에 기계 판독 필드 '활성화 IC 케이스'를 둔다(T-01의 케이스 키).
  * 엄격 대상 = 이번 card의 그 필드 ∪ **같은 Phase에서 이미 병합된 card들의 그 필드**로 한다. 누적이며, base의 판정 기록·spec card에서 계산한다.
  * merge gate가 이 집합을 계산하고, `auditor_run.commands`의 V1 명령에 그 집합이 들어 있는지 대조한다.

#### T-03 (S2) EL4 판정 표 diff 검사가 계획서 개정의 정상 경로(오케스트레이터 직접 커밋)에서 발동하지 않는다
* **위치**: §9 머리 "사본이 막던 경로 … 는 EL4가 막는다", §9.1 "흐름 밖(사용자 직접 커밋)".
* **근거와 수정**: §3 틈 1.

### S3

* **T-04** 계획 N4.3 공격 16이 v1.5에 맞게 갱신되지 않았다. (iii) "head 판 표 파손 → 거부" 케이스가 없고, (i)의 표 목록에 EL4·§9.1이 새로 넣은 `강제 test` 열이 없다.
* **T-05** 설계 §14의 CC-4 행에 앞부분/나머지 구분이 없고, CC-7·CC-8 행에 "CC-4 앞부분 뒤"가 없다. 계획 N6.1 4행의 '나머지:' 목록은 TS4·DF-35~37을 다시 적는다(§4).
* **T-06** §11.1 '그 앞 card의 무동작' 목록에 CC-4 앞부분 card가 없다(§4).
* **T-07** §9.3 "엄격 대상의 test는 xfail 없이 PASS여야 한다"가 조건식과 어긋난다. 조건식에서는 표식이 현재 Phase보다 뒤인 케이스가 strict여도 xfail이다(IC7 `"6c"`, Phase 4의 IC11 `"6a"`). "엄격 대상 중 표식 Phase = 현재 Phase인 케이스"로 좁힌다.
* **T-08** §8.1 red 수집 명령(`$PY -m pytest --rootdir=… -p tools.gates.merge_gate …`)에 `--gmid-phase`와 `--gmid-strict`가 여전히 없다(Q-09). v1.5에서 모든 실행이 `--gmid-phase`를 요구하므로, CC-3 뒤에는 이 명령대로 돌린 red 재현이 전부 UsageError로 끝난다. 값의 출처(spec card `Phase`, T-02 필드)를 명령에 적는다. 함께 계획 V2의 "새·바뀐 test"에 '엄격 대상이 되어 처음 활성화되는 기존 IC test'가 red로 들어가는지 정한다. 실측상 수집 훅은 xfail 케이스의 excinfo도 받으므로 red 해시는 재현된다. 병합본 쪽 XPASS를 PASS로 볼지도 함께 정한다.
* **T-09** 신규 심볼 판정의 "`name`이나 `name_from`이 목록에 있으면"이 느슨하다.
  * 실측(Python 3.14): `from json import NEW_SYMBOL`의 `ImportError.name`은 `'json'`(기존 모듈)이고, `name_from`이 `'NEW_SYMBOL'`이다.
  * 그래서 목록에 모듈 경로가 있으면 그 모듈에서 나는 모든 ImportError(오타·삭제된 기존 심볼 포함)가 신규 심볼 red로 인정된다.
  * (모듈, 심볼) 쌍으로 대조하고, 목록의 모듈 경로 형식(파일 경로 대 점 표기, `ModuleNotFoundError.name`은 `'json.nosuch'` 같은 점 표기)을 정한다.
* **T-10** EL4의 'head' 커밋 정의와 승인 기록↔표 diff 대응 규칙이 없다(§3 틈 2).
* **T-11** history 'v1.4 확인(review25) 반영' 문단의 "거부 케이스 24건을 전부 거부"가 원자료 `common00_schema_reject_check.txt` 113행 "거부 기대 30/30"과 다르다. 같은 history 앞 문단도 30건이다.

---

## 6. 지정 점검 6: 표 셀 수

`cells.py`로 셌다. 이스케이프되지 않은 `|` 기준이고 코드 블록은 뺐다.

| 파일 | 표 | 파손 행 |
|---|---|---|
| 설계 v1.5 | 16 | **0** |
| 계획 v5.19 | 42 | **0** |
| history | 115 | 8(3788·3802·3808·5287·5512·5515·5517·5540). 모두 review25가 적은 기존 행이 2줄 밀린 것이고, `cb8cb4a`가 더한 행(머리 절, U-38, 5.19)은 정상이다 |

---

## 7. 집계와 판정

| 구분 | 건수 | ID |
|---|---|---|
| 닫힘 | 4 | Q-01, Q-03, Q-05, R-02 잔여 |
| 부분 | 2 | Q-02(모순은 풀렸으나 엄격 적용 단위·범위 결함), Q-04(파싱 값·head 거부는 닫힘, 계획서 직접 커밋 경로·공격 16 미갱신) |
| 안 닫힘 | 0 | -- |
| 새 S1 | 0 | -- |
| 새 S2 | 3 | T-01(strict가 IC 단위라 6a IC11 거부/3레일이 막히거나 확인 누락), T-02(strict가 활성화 card에만 걸려 활성화 뒤 회귀가 DoD까지 XFAIL로 통과, strict 목록이 산문 출처이고 gate가 검사 안 함), T-03(계획서 개정이 오케스트레이터 직접 커밋이라 EL4 표 diff 승인 검사가 발동하지 않음) |
| 새 S3 | 8 | T-04 ~ T-11 |

v1.5는 review25 S1 두 건의 핵심을 닫았다.
* Phase 4 순서는 네 곳에서 같다.
* xfail 만료는 이제 계획의 '만료 = DoD'와 맞다.
* Phase 4 첫 card, Phase 4 DoD, 7a 실행은 모의 실측에서 설계 의도대로 동작했다.
* 활성화 card의 V2 red-green도 `--gmid-strict` 아래에서 base FAIL → 병합본 PASS로 만족할 수 있다.

남은 결함은 전부 국소 규정이다. strict를 케이스 단위·누적으로 바꾸고 기계 필드로 만드는 것(T-01·T-02), 계획서 개정 경로에 표 검사를 거는 문장 하나(T-03)다.

**판정: 수정 후 승인.**
