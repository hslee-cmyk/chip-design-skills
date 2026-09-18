# review27 -- `00-common` design v1.6 좁은 확인(review26 T-01~T-11 닫힘)

* 대상: 작업 트리의 커밋 안 된 변경(`git diff HEAD -- docs/01-plan docs/02-design`)
  * `docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md` v1.6
  * `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(판 번호는 5.19 그대로. history 관례상 '같은 v5.19 안' 개정)
  * history의 'v1.5 좁은 확인(review26) 반영' 문단
* 기준: review26의 T-01~T-11과 지정 점검 2~5
* 범위: 이 diff가 건드린 곳만 본다. 바뀌지 않은 부분은 다시 감사하지 않았다. 범위 밖이지만 점검 2의 답에 직접 걸리는 기존 결함 하나는 §5.4에 따로 적었다.
* 검증자: 독립 검증 agent. 이 설계도, review21~26도 쓰지 않았다.
* 측정 스크립트는 저장소 밖 scratchpad `review27/`에 있다.
  * `sim/conftest.py` + `sim/tests/test_ic11.py`: v1.6 §9.3 규칙(케이스 키, `--gmid-strict`, `--gmid-dod`)을 그대로 구현한 모의 conftest. IC11 세 케이스(`rail2` `"4"`, `rail3` `"6a"`, `reject` `"6a"`)와 §8.1 red 수집 훅을 넣었다. 실행 결과는 `sim/results.txt`에 있다.
    * 환경: pytest 9.0.2, Python 3.14.
    * `VALIDATE_STRICT=1`은 수정 제안(엄격 키 검증)을 켜는 스위치다. 설계 규칙에는 없다.
  * `pre/`: conftest가 없는 상태, 곧 CC-3 병합 전 상태
  * `git2/`: pre-commit hook이 어느 git 명령에서 도는지 실측(git 2.52.0.windows.1)
  * `t09/t.py`: 신규 심볼 쌍 만들기와 `PlanTables` JSON 직렬화 실측
  * `cells.py`(+`cells.txt`): 표 셀 수 검사(review26 스크립트 재사용)
* 저장소에서 바꾼 파일은 이 보고서 하나다.
* 심각도: **S1** = 승인을 막는다 / **S2** = 승인 전에 고친다 / **S3** = 경미

---

## 1. 닫힘 표

| ID | 판정 | 근거(인용) |
|---|---|---|
| T-01 | **닫힘** | §9.3: "`@pytest.mark.gmid_ic("<IC>", phase="<Phase>", case="<case>")` … 3레일 케이스는 `phase="6a", case="rail3"`, 선행 거부 케이스는 `phase="6a", case="reject"` … 같은 Phase에 표식이 같은 케이스 둘(IC11 `reject`·`rail3`)은 각자 활성화 card에서 따로 엄격해진다". 실측 A1·A2(§2): `--gmid-strict IC11:reject`에서 `rail3`는 XFAIL로 남고 `reject`만 엄격해진다. review26의 '2 failed' 막힘은 없어졌다. |
| T-02 | **닫힘**(새 결함 N-01·N-02 동반) | §9.3: "`--gmid-strict <IC:case,...>`: **이번 spec card의 '활성화 IC 케이스' 필드(N3.12.3) ∪ 같은 Phase에서 이미 병합된 card들의 그 필드** … merge gate가 이 집합을 계산한다 … `auditor_run.commands`의 V1 명령에 … 정확히 그 집합 … 다르면 거부". 계획 N3.12.3 필드 목록에도 "활성화 IC 케이스(`<IC>:<case>` 목록 …)"가 들어갔다. 실측 B1: 뒤 card가 `reject`를 다시 깨면 FAIL이다. 실측 B2: auditor가 strict를 빠뜨리면 XFAIL이지만, gate가 명령 문자열을 대조하므로 거부된다. 남은 틈 둘은 새 결함으로 적는다. 하나는 존재하지 않는 케이스 키가 조용히 통과하는 것이고(N-01), 다른 하나는 CC-3 전 card가 막히는 것이다(N-02). |
| T-03 | **부분** | 계획 EL3: "**계획서 판정 표 검사**: staged 경로에 계획서가 있으면 HEAD 판과 staged 판의 판정 표 … 값이 다르면 그 값에 대응하는 승인 기록(`target_kind: plan_tables` …)이 같은 커밋이나 그 전에 있어야 한다". §9.1도 "EL3(커밋 시점) … EL4(병합 시점)"로 나뉘었다. `git commit` 경로는 닫혔다. 그러나 `git revert`·`git cherry-pick`·`git merge`는 pre-commit을 돌리지 않는다(실측 §3.3). EL1도 이 명령들을 막지 않는다. 그래서 오케스트레이터의 계획서 되돌리기가 검사 없이 base에 들어간다(N-03, S2). |
| T-04 | **닫힘** | 공격 16: "(i) … `담당 Phase`·`강제 test` … (a) 직접 커밋 (b) 병합으로 시도 (ii) … (a) 직접 커밋 (b) 병합 head로 시도 (iii) 흐름 밖에서 깨진 base 위에서 병합을 시도 \| (i)(a)·(ii)(a) EL3 차단, (i)(b)·(ii)(b) EL4 거부, (iii) merge gate가 판정하지 않고 거부". 오거부 0 케이스에 "판정 표 값이 바뀌지 않는 문장 수정"도 추가됐다. |
| T-05 | **닫힘** | §14 CC-4: "**앞부분**(Phase 4에서 CC-7·CC-8보다 먼저): … **나머지**: DF-37 광범위 except 재raise". CC-7: "DF-35·CC-4 앞부분 뒤". CC-8: "DF-35·36·CC-4 앞부분 뒤". 계획 N6.1 4행의 '나머지:'는 "→ 나머지. Phase 4 전체 범위: …"로 순서 목록과 범위 목록이 갈렸다. |
| T-06 | **닫힘**(S3 하나 동반) | §11.1: "CC-4 앞부분은 실패 경로(예외 클래스·exit code)만 바꾸므로 성공한 실행의 산출물은 그대로이고, 그 증거는 성공 경로의 `equivalence`(그 spec card)다". 판정 유형이 섞이는 문제는 N-09(S3)에 적는다. |
| T-07 | **닫힘** | §9.3: "표식 Phase가 현재보다 앞이면 언제나 활성이다. **엄격 대상**(표식 Phase = 현재 Phase인 케이스에만 뜻이 있다)". 실측 E3: Phase 4에서 `IC11:rail3`(표식 6a)를 strict로 줘도 XFAIL이다. 문장과 조건식이 맞는다. |
| T-08 | **닫힘** | §8.1: "`… -p tools.gates.merge_gate --continue-on-collection-errors --gmid-phase <spec card Phase> --gmid-strict <§9.3 엄격 집합> …`(CC-3 전에는 두 `--gmid-*` 옵션이 없다), 병합본에서 엄격 대상 케이스는 PASS여야 하며 XPASS는 엄격 대상이 아닌 케이스에서만 나온다". 계획 V2: "새·바뀐 test(그리고 이 변경의 '활성화 IC 케이스'로 엄격 대상이 된 기존 계약 test 케이스)가 base에서 assertion FAIL". 실측 A1: base에서 활성화 케이스가 FAIL하고 수집 훅이 기록한다. |
| T-09 | **닫힘**(S3 하나 동반) | §8.1: "**(모듈, 심볼) 쌍** 목록 … `ModuleNotFoundError` → (`name`, `*`) / `from M import X`의 `ImportError` → (`name`, `name_from`) / `AttributeError` → (`obj.__name__`, `name`) … 그 쌍이 목록에 있을 때만". 느슨함은 닫혔다. 대신 흔한 신규 형태 셋이 잘못된 쌍을 만든다(N-10, S3). |
| T-10 | **닫힘** | EL4: "head는 병합할 브랜치 끝 커밋이다 … 승인 기록은 `target_kind: plan_tables`이고 `target`이 head 판정 표 파싱 값의 해시와 같아야 한다". 중간 커밋 파손은 이제 EL3가 커밋마다 잡는다. |
| T-11 | **닫힘**(S3 하나 동반) | history: "거부 케이스 24건(v1.0 시점. 이후 30건)". 원자료 `common00_schema_reject_check.txt`에는 실행이 세 번 있고, 첫 실행이 `24/24`, 뒤 두 실행이 `30/30`이다. 수치는 맞다. 다만 이 실측 문장이 review25 문단에서 빠져 review26 문단 끝으로 옮겨졌다(N-11). |

**집계: 닫힘 10(T-01·02·04·05·06·07·08·09·10·11) / 부분 1(T-03) / 안 닫힘 0**

---

## 2. 점검 2: 누적 strict 규칙 모의 실측

모의 conftest는 v1.6 §9.3 문장을 그대로 구현했다.
* xfail 조건: "표식 > 현재", 또는 "표식 = 현재이고 `--gmid-dod`가 아니고 케이스 키가 `--gmid-strict`에 없음"
* red 수집 훅: §8.1대로 `pytest_runtest_makereport`에서 `call.excinfo`를 기록한다.
* `IMPL`: 구현된 계약 목록

| # | 시나리오 | 실행 | IMPL | 결과 | 수집 훅 기록 |
|---|---|---|---|---|---|
| A1 | 6a에서 `IC11:reject`를 활성화하는 card의 **base**(`rail3`는 아직 비활성) | `--gmid-phase 6a --gmid-strict IC11:reject` | rail2 | 1 failed(reject), 1 passed, 1 xfailed | rail3 `AssertionError`, reject **`builtins.Failed`** |
| A2 | 같은 card의 병합본 | 같음 | rail2,reject | 2 passed, 1 xfailed | rail3만 |
| B1 | 뒤 6a card가 `reject`를 깸(누적 집합) | `--gmid-strict IC11:reject` | rail2 | **1 failed** | reject |
| B2 | 같은 회귀에서 auditor가 strict를 빠뜨림 | strict 없음 | rail2 | 1 passed, 2 xfailed(조용함) | -- |
| C1 | 6a DoD(`reject`만 구현) | `--gmid-dod` | rail2,reject | 1 failed(rail3), 2 passed | -- |
| C2 | 6a DoD(모두 구현) | `--gmid-dod` | 전부 | 3 passed | -- |
| D1 | `rail3` 활성화 card의 base(누적 `rail3,reject`) | `--gmid-strict IC11:rail3,IC11:reject` | rail2,reject | 1 failed(rail3), 2 passed | rail3 |
| D2 | 같은 card의 병합본 | 같음 | 전부 | 3 passed | -- |
| E1 | card가 오타 키 `IC11:rejct`를 선언 | `--gmid-strict IC11:rejct` | rail2 | **1 passed, 2 xfailed** | -- |
| E2 | card가 표식 없는 키 `IC99:x`를 선언 | `--gmid-strict IC99:x` | rail2 | **1 passed, 2 xfailed** | -- |
| E3 | Phase 4 card가 표식 6a 키 `IC11:rail3`를 선언 | `--gmid-phase 4 --gmid-strict IC11:rail2,IC11:rail3` | rail2 | **1 passed, 2 xfailed** | -- |
| E4 | (수정 제안) conftest가 모르는 키를 거부 | E1 + `VALIDATE_STRICT=1` | rail2 | UsageError "strict keys without marker at current phase: ['IC11:rejct']", exit 4 | -- |
| F1 | 빈 집합을 `--gmid-strict=`로 줌 | | rail2 | 1 passed, 2 xfailed | -- |
| F2 | 빈 집합을 값 없이 `--gmid-strict`로 줌 | | rail2 | argparse "expected one argument" | -- |
| G1 | strict 밖 케이스가 우연히 통과 | `--gmid-strict IC11:reject` | 전부 | 2 passed, **1 xpassed** | -- |
| H1 | 7a 실행, `rail3` 깨짐 | `--gmid-phase 7a` | rail2,reject | 1 failed | -- |
| P1 | CC-3 전(conftest 옵션 없음) | `--gmid-phase 1` | -- | **"unrecognized arguments: --gmid-phase", exit 4** | 없음 |

시나리오별 판정:

1. **6a에서 `IC11:reject`만 활성화(`rail3` 비활성)**: 막히지 않는다(A1·A2). T-01은 닫혔다.
2. **뒤 6a card가 `IC11:reject`를 깸**: 누적 집합 때문에 V1이 FAIL한다(B1). auditor가 strict를 빠뜨리면 pytest 결과는 조용하지만(B2), merge gate의 명령 대조가 거부한다. T-02는 닫혔다.
3. **Phase 6a DoD**: 표식이 6a인 케이스가 전부 엄격해진다. `rail3`가 미구현이면 막히고(C1), 전부 구현하면 통과한다(C2). 의도대로다.
4. **활성화 card의 base 쪽 red를 만들 수 있나**: 만들 수 있다. base에서 FAIL하고 수집 훅이 기록한다(A1·D1).
   * 다만 거부 계약은 보통 `pytest.raises`로 쓴다. 이때 기록되는 타입 문자열은 `builtins.Failed`다. `_pytest.outcomes.Failed.__module__ == "builtins"`이기 때문이다(실측).
   * §8.1 허용 목록의 문자열은 `_pytest.outcomes.Failed`다. 문자열로 대조하면 이 red는 허용 타입이 아니어서 거부된다.
   * 이 결함은 v1.6 diff 밖이다(§8.1 302행은 바뀌지 않았다). 그러나 `IC11:reject` 활성화 card를 직접 막으므로 §5.4 X-01로 따로 적는다.
5. **표식 없는 케이스 키를 활성화한다고 선언**: **조용히 통과한다**(E1·E2·E3).
   * merge gate가 대조하는 두 값(명령의 strict 집합과 spec card 필드)은 모두 spec card에서 나온다. 그래서 오타가 있어도 둘이 같고, gate가 통과시킨다.
   * conftest는 표식이 없는 키를 무시한다. 결국 활성화 card와 그 뒤 card 모두 엄격 확인을 받지 않는다. 이 구멍은 DoD(`--gmid-dod`)에서야 드러난다. T-02가 막으려던 증상이 오타 하나로 되살아난다(N-01, S2).
   * 표식-계획서 대조 test(§9.3)는 Phase 집합만 보고 케이스 키는 보지 않는다. 그래서 이 대조 test도 잡지 못한다.
6. **CC-3 전 card**: §9.3의 gate 대조에는 "V1 명령에 `--gmid-phase <Phase>`가 있어야 한다"는 조건만 있고 예외가 없다. 한편 CC-3 전에는 그 옵션이 존재하지 않는다(§8.1 자신이 "CC-3 전에는 두 `--gmid-*` 옵션이 없다"고 적는다).
   * 옵션을 넣으면 pytest가 exit 4로 끝난다(P1).
   * 넣지 않으면 gate가 거부한다.
   * 계획 N6.1 Phase 1 행은 TS7(CC-3)을 첫 card로 정하지 않는다. 그래서 Phase 1에서 CC-3보다 먼저 오는 card는 모두 막힌다(N-02, S2).
7. **빈 집합**: 활성화 card가 아직 없는 Phase는 집합이 비어 있다. 이때 V1 명령을 어떻게 적는지(`--gmid-strict=`, `--gmid-strict ""`, 또는 옵션 생략)가 정해지지 않았다. 값 없이 쓰면 argparse 오류가 난다(F2). gate의 "정확히 그 집합" 대조 형식도 정해야 한다(N-08, S3).
8. XPASS(G1)는 §8.1 문장대로 엄격 대상이 아닌 케이스에서만 나온다. 비엄격 xfail이므로 V1을 막지 않는다. 의도와 맞다.

---

## 3. 점검 3: EL3 계획서 판정 표 검사와 `target_kind: plan_tables`

### 3.1 정합

| 대상 | 판정 |
|---|---|
| EL4 | 정합. EL4는 base..head 순 diff를 보고 `target` = head 파싱 값 해시다. EL3는 HEAD→staged를 보고 `target` = staged 파싱 값 해시다. 둘은 같은 식이다(§9.1 "두 곳에서 같은 함수로 한다"). |
| N4.3 공격 16 (i)(ii)(iii) | 정합. (a) 직접 커밋은 EL3, (b) 병합은 EL4, (iii) 흐름 밖에서 깨진 base는 판정 없는 거부다. 오거부 0 케이스(승인 있는 개정, 표 값이 그대로인 문장 수정)도 §9.1의 "원문 문장 수정은 변경이 아니다"와 맞다. |
| N3.12.5 | 정합. 승인 기록의 대상이 "diff 해시, 결정 ID, 또는 계획서 판정 표 파싱 값의 해시"로 늘었다. |
| §8.2 | 정합. `target_kind` 열거에 `plan_tables`가 들어갔고, `target`은 64자리 16진이며 `diff_*` 키는 금지다. |
| §2 정정 문단·§9 머리 | 정합. 둘 다 "EL3(커밋 시점)과 EL4(병합 시점)"로 고쳐졌다. |

### 3.2 부트스트랩과 순서

* **해시를 커밋 전에 계산할 수 있나**: 원리상 가능하다. 오케스트레이터가 고친 계획서를 `read_plan_tables`로 읽어 해시를 내고, 승인 기록을 쓴 뒤 둘을 함께 stage하면 된다. 그러나 두 가지가 비어 있다.
  * 첫째, 직렬화가 정의되지 않았다. `PlanTables`는 `ICPart` dataclass와 tuple을 담는다. 그래서 "키 정렬 JSON"을 그대로 적용하면 `json.dumps`가 `TypeError: Object of type ICPart is not JSON serializable`로 실패한다(실측). 구분자 기본값(`", "`)과 압축형(`","`)만 달라도 해시가 다르다(실측). 오케스트레이터·EL3(`role_commit_gate.py`)·EL4(`merge_gate.py`)가 각자 구현하면 올바른 승인도 거부된다.
  * 둘째, 해시를 내는 함수나 CLI가 산출물 목록에 없다(N-04, S3).
* **같은 커밋에서 표와 승인을 함께 바꾸는 경우**: "같은 커밋이나 그 전에"로 허용된다. 다만 EL3가 승인 기록을 어디서 찾는지 정해지지 않았다(index인지 작업 트리인지).
  * 작업 트리에서 찾으면, stage하지 않은 승인 파일이 검사를 통과시키고 커밋에는 들어가지 않는다.
  * 이 경로는 base 직접 커밋이다. 그래서 뒤에서 EL4가 볼 기회도 없다.
  * EL4 쪽도 승인 기록을 base에서 찾는지 head에서 찾는지 정하지 않았다(N-05, S3).
* **순서**: 공격 16 (i)(a)·(ii)(a)는 부트스트랩 ③에서 실행한다. 그런데 `.githooks/pre-commit` 갱신은 ④다. 그래서 ③에서는 `role_commit_gate.py`를 직접 호출해 증명해야 한다. 이 점이 적혀 있지 않지만, 공격 1~12에도 같은 사정이 있는 기존 구조라 새 결함으로 세지 않는다.
* **구현 소유**: §14 CC-2 행에는 여전히 "EL4의 판정 표 diff 승인 검사"만 있다. 계획 N9.1 `05-role-separation` 행의 CC-2 설명도 "(계획서 판정 표 읽기와 표 파손 거부)"다. EL3 쪽 검사, 곧 `role_commit_gate.py`가 `read_plan_tables`를 쓰는 부분의 소유 행이 없다(N-07, S3).

### 3.3 우회 경로 실측(git 2.52.0.windows.1, `core.hooksPath` = `.githooks`)

| 명령 | pre-commit 실행 |
|---|---|
| `git commit`(c1, c2) | 1회씩 |
| `git revert --no-edit HEAD` | **0**(계획서가 앞 판으로 돌아감) |
| `git cherry-pick <commit>` | **0** |
| `git merge --no-ff` | **0**(pre-merge-commit hook이 따로 있어야 한다) |
| `git merge --squash` 뒤 `git commit` | 1 |
| `git commit-tree` + `git update-ref` | **0** |

EL1의 차단 목록은 `--no-verify`, `git commit -n`, `core.hooksPath`, `git push`, `git reset --hard`, `git checkout -- <tests>`다. `revert`·`cherry-pick`·`merge`는 이 목록에 없다.

EL4는 base..head만 비교한다. 그래서 이 명령들로 base에 들어간 판정 표 변경은 **어느 겹에서도 다시 검사되지 않는다**. 그 뒤의 병합에서는 이미 base 값이기 때문이다.

v1.6은 "흐름 안에서는 깨진 계획서가 base에 들어가지 않는다"고 단언한다. 또 계획서 개정의 정상 경로가 오케스트레이터 직접 커밋이라고 전제한다. 그런데 되돌리기(`git revert`)는 그 정상 경로에서 흔한 동작이다(N-03).

---

## 4. 점검 5: 표 셀 수

`cells.py`로 셌다. 이스케이프되지 않은 `|` 기준이고 코드 블록은 뺐다.

| 파일 | 표 | 파손 행 |
|---|---|---|
| 설계 v1.6 | 16 | **0** |
| 계획(작업 트리) | 42 | **0** |
| history | 115 | 8(3790·3804·3810·5289·5514·5517·5519·5542). review26이 적은 기존 8행이 문단 추가로 2줄 밀린 것이다. 이번 diff가 더하거나 바꾼 행은 없다. |

diff가 바꾼 표 행(설계 §2 CC-3 행, §14 CC-3·CC-4·CC-7·CC-8 행, 계획 EL3·EL4·V2·공격 16·N6.1 4행)은 모두 머리 셀 수와 같다. EL3 행의 `Role: code\|test\|audit\|doc` 이스케이프도 유지됐다.

---

## 5. 새 결함(v1.6 diff에서 생긴 것만)

### 5.1 S1

없음.

### 5.2 S2

#### N-01 (S2) '활성화 IC 케이스' 키를 검증하는 곳이 없어, 오타나 표식 없는 키가 엄격 확인 없이 조용히 통과한다
* **위치**: §9.3 "`--gmid-strict <IC:case,...>` … merge gate가 이 집합을 계산한다 … V1 명령에 … 정확히 그 집합", 계획 N3.12.3 '활성화 IC 케이스'
* **근거**: §2 실측 E1·E2·E3. 오타 키, 없는 IC, 표식 Phase가 card Phase와 다른 키가 모두 "1 passed, 2 xfailed"다.
  * gate가 대조하는 두 쪽은 모두 spec card 필드에서 나오므로 서로 같다.
  * conftest는 모르는 키를 무시한다.
  * 표식-계획서 대조 test는 Phase 집합만 본다.
* **영향**: 활성화 card와 그 Phase의 뒤 card 전부가 그 케이스를 XFAIL로 넘긴다. T-02가 막으려던 증상이 오타 하나로 되살아나고, DoD에서야 드러난다.
* **수정**:
  * conftest가 `--gmid-strict`의 키마다 "수집된 표식 중 그 키이고 표식 Phase = `--gmid-phase`인 것"이 있는지 확인하고, 없으면 UsageError를 낸다. E4가 이 방식이 동작함을 보였다.
  * 누적 집합은 과거 spec card에서 계산하므로 바꿀 수 없다. 그래서 케이스 키 이름을 바꾸는 규칙도 함께 둔다. 예: 이름 변경은 test 커밋과 같은 card의 활성화 필드에 새 키를 적고, 옛 키는 승인 기록으로 은퇴시킨다. 이 규칙이 없으면 검증을 넣은 뒤 이름 변경 하나가 그 Phase의 뒤 card를 전부 막는다.

#### N-02 (S2) merge gate의 V1 명령 대조에 CC-3 전 예외가 없어, Phase 1에서 CC-3보다 먼저 오는 card가 모두 막힌다
* **위치**: §9.3 "V1 명령에 `--gmid-phase <Phase>`와 … `--gmid-strict`가 있는지 대조한다. 다르면 거부". 이 문장은 §8.1 "(CC-3 전에는 두 `--gmid-*` 옵션이 없다)"와 어긋난다.
* **근거**: 실측 P1. conftest 옵션이 없는 상태에서 `--gmid-phase 1`을 주면 "unrecognized arguments", exit 4다. merge gate(CC-1·CC-2)는 Phase 0.5에 들어오고 CC-3은 Phase 1 TS7의 일부다. 계획 N6.1 Phase 1 행("TS0, TS1, TS2, TS3, TS5, TS7 선언")은 순서를 정하지 않는다.
* **수정**: 둘 중 하나를 문장으로 정한다. (a) gate 대조는 base에 CC-3 conftest가 있을 때만 한다. (b) Phase 1 순서에서 TS7(CC-3)을 첫 card로 둔다. (a)를 고르면 "CC-3이 있는가"의 판정 입력(파일 존재 또는 CC-3 판정 기록 존재)도 적는다.

#### N-03 (S2) EL3 계획서 판정 표 검사가 `git revert`·`cherry-pick`·`merge`·plumbing 커밋에서 돌지 않고, 이 경로로 base에 들어간 변경은 어느 겹도 다시 보지 않는다
* **위치**: 계획 EL3 "staged 경로에 계획서가 있으면 …", §9.1 "두 검사가 뒤 판을 못 읽으면 막으므로 흐름 안에서는 깨진 계획서가 base에 들어가지 않는다"
* **근거**: §3.3 실측. EL1 차단 목록에 이 명령들이 없다. EL4는 base..head 전이만 본다.
* **영향**: 오케스트레이터가 승인된 표 개정을 `git revert`로 되돌리면 승인 없는 판정 표 변경이 base에 조용히 들어간다. 공격 16이 막으려는 '표 한 칸으로 검사 끄기'와 같은 결과다. 표 파손도 같은 경로로 들어간다. 그러면 다음 병합부터 (iii) 거부가 되어 교착에 빠진다.
* **수정**: **상태 기반 검사**를 더한다. EL4가 병합마다(그리고 EL3가 커밋마다) "base 판정 표 파싱 값의 해시에 대응하는 `plan_tables` 승인 기록이 base에 있다"를 확인한다. 이렇게 하면 어느 git 명령으로 들어왔든 다음 병합에서 잡힌다. 부트스트랩 시점의 표 값에는 최초 승인 기록 하나를 둔다. 보조 수단으로 EL1 차단 목록에 `git revert`·`git cherry-pick`·`git commit-tree`·`git update-ref`를 더하거나, 이 명령들이 계획서를 건드리면 거부하게 한다. 공격 16 (i)에 (c) '되돌리기 커밋' 케이스를 더한다.

### 5.3 S3

* **N-04** `plan_tables` 해시의 직렬화가 정의되지 않았다(§8.2 "키 정렬 JSON").
  * `ICPart` dataclass는 JSON으로 바로 직렬화되지 않는다. tuple과 list의 구분, 구분자, `ensure_ascii`, 행 순서(`ic_parts` 원소 순서)가 해시를 바꾼다. 이 중 dataclass와 구분자는 실측으로 확인했다.
  * `merge_gate.py`에 `plan_tables_hash(PlanTables) -> str` 하나를 두고, 오케스트레이터·EL3·EL4가 모두 그것만 부르게 적는다. 승인 기록을 쓰기 전에 계산할 수 있도록 CLI 진입점도 둔다.
* **N-05** 승인 기록을 찾는 위치가 정해지지 않았다.
  * EL3은 index(staged 트리)에서 찾아야 한다. 작업 트리에서 찾으면, stage하지 않은 승인 파일로 통과한 직접 커밋이 기록 없이 base에 남는다.
  * EL4는 head에서 찾는지 base에서 찾는지를 적는다.
  * EL3는 "staged 판"(해시 대상)을 index blob으로 읽는다는 것도 명시한다. 부분 stage하면 작업 트리 파일로 계산한 해시와 달라진다.
* **N-06** `target`이 뒤 판 해시 하나뿐이다.
  * 그래서 예전에 승인된 표 상태로 되돌리는 변경은 옛 승인 기록으로 통과한다. 사용자가 그 뒤에 승인한 결정이 조용히 취소된다.
  * 앞 판 해시를 함께 묶거나(`target` = sha256(앞 해시 + 뒤 해시)), 되돌림이 허용된다는 뜻을 명시한다. N-03의 상태 기반 검사를 고르면 '되돌림 허용'이 자연스러운 쪽이다. 그렇다면 그 뜻을 적는다.
* **N-07** EL3 판정 표 검사의 구현 소유 행이 없다. §14 CC-2 행("EL4의 판정 표 diff 승인 검사")과 계획 N9.1 `05-role-separation` 행에 `role_commit_gate.py`의 판정 표 검사(EL3)를 더한다.
* **N-08** §9.3 "`auditor_run.commands`의 V1 명령"을 식별하는 방법이 없다. §8.1 스키마의 `commands`는 라벨 없는 문자열 목록이다. 빈 집합의 표기(`--gmid-strict=`, 생략, 또는 `""`)도 정해지지 않았다. 값 없이 쓴 `--gmid-strict`는 argparse 오류다(F2). 예: V1 명령은 `commands[0]`, 또는 `checks.V1.basis`에 명령 인덱스를 적는다. 빈 집합이면 옵션을 생략한다.
* **N-09** §11.1은 CC-4 앞부분의 무동작 증거를 "성공 경로의 `equivalence`(그 spec card)"라고 적는다. 그런데 §14 CC-4 행의 판정 유형은 `red-green`이다. N3.12.3은 "판정 유형이 섞이면(red-green + equivalence) 나눈다"고 정한다. CC-7처럼 equivalence card를 따로 두거나, 다른 증거(성공 실행 산출물의 바이트 비교를 V8/§11 도구 없이 하는 방법)를 적는다.
* **N-10** T-09 쌍 만들기가 흔한 신규 형태 셋에서 잘못된 쌍을 만든다(Python 3.14 실측). 모두 오거부 쪽이라 안전하지만, 정당한 red를 막는다.
  * `from pkg import newsub`(신규 하위 모듈)은 `ImportError(name='pkg', name_from='newsub')`이 되어 (`pkg`, `newsub`)가 나온다. 목록의 선언은 (`pkg.newsub`, `*`)이다.
  * 기존 클래스의 신규 메서드는 `AttributeError.obj.__name__ == 'C'`이다. 모듈 경로가 아니다.
  * 인스턴스 속성에서는 `obj`에 `__name__`이 없다. 쌍을 만들 수 없어 구현에 따라 예외가 난다.
  * `from newpkg.sub import f`(둘 다 신규)는 (`newpkg`, `*`)가 된다.
  * 수정 방향: `ModuleNotFoundError`는 선언 모듈의 접두어 일치로 판정한다. `from M import X`는 (`M.X`, `*`)도 함께 대조한다. `AttributeError`는 `obj`가 모듈일 때만 인정한다고 적는다.
* **N-11** history에서 실측 문장("스키마는 올바른 기록 3종을 통과시키고 거부 케이스 24건…")이 'v1.4 확인(review25) 반영' 문단에서 빠지고 'v1.5 좁은 확인(review26) 반영' 문단 끝으로 옮겨졌다. 이 실측은 v1.4 반영의 근거이므로, 원래 문단에 두고 수치만 고치는 편이 이력으로서 정확하다.

### 5.4 범위 밖 관찰(기존 결함, 점검 2의 답에 직결)

* **X-01 (S2 상당, v1.6 diff 밖)** §8.1 허용 예외 타입의 `_pytest.outcomes.Failed`는 실제 기록 문자열과 맞지 않는다.
  * `red_failure_hash`는 `f"{exc_type.__module__}.{exc_type.__qualname__}"`를 쓴다. 그런데 pytest 9.0.2의 `Failed.__module__`은 `"builtins"`다(실측. `pytest.fail.Exception is _pytest.outcomes.Failed`).
  * 그래서 `pytest.raises` "DID NOT RAISE"와 `pytest.fail`로 된 red는 수집 문자열이 `builtins.Failed`이고, 허용 목록 문자열과 대조하면 거부된다(§2 A1).
  * 거부 계약(`IC11:reject`, 공격 13·14 계열)은 보통 `pytest.raises`로 쓰므로, 활성화 card가 red를 인정받지 못한다.
  * 허용 판정을 클래스 동일성(`issubclass(t, _pytest.outcomes.Failed)`)으로 하거나, 목록 문자열을 `builtins.Failed`로 고치고 실측 근거를 적는다. 공격 15 케이스에 `pytest.raises` red를 더한다.

---

## 6. 집계와 판정

| 구분 | 건수 | ID |
|---|---|---|
| 닫힘 | 10 | T-01, T-02, T-04, T-05, T-06, T-07, T-08, T-09, T-10, T-11 |
| 부분 | 1 | T-03(`git commit` 경로는 닫힘. revert·cherry-pick·merge 경로는 EL3 밖 -- N-03) |
| 안 닫힘 | 0 | -- |
| 새 S1 | 0 | -- |
| 새 S2 | 3 | N-01(활성화 키 검증 없음 → 오타·표식 없는 키가 조용히 통과), N-02(gate의 `--gmid-phase` 대조에 CC-3 전 예외 없음 → Phase 1 앞쪽 card 막힘), N-03(EL3가 revert·cherry-pick·merge에서 돌지 않고 EL4는 전이만 봐서 base 표 변경이 영구히 미검사) |
| 새 S3 | 8 | N-04 ~ N-11 |
| 범위 밖 | 1 | X-01(`_pytest.outcomes.Failed` 문자열 불일치, S2 상당) |

v1.6은 review26의 S2 세 건 가운데 둘을 모의 실측 수준에서 닫았다.
* 케이스 단위로 바꿔 6a IC11의 `reject`/`rail3`이 따로 활성화된다.
* 누적 집합과 gate 대조로 활성화 뒤 회귀가 card 단위에서 잡힌다.
* 계획서 개정의 `git commit` 경로에는 EL3가 붙었다.

남은 결함은 모두 문장 몇 개로 고칠 수 있는 국소 규정이다.
* 모르는 strict 키를 conftest가 거부하고, 키 이름 변경 규칙을 둔다(N-01).
* CC-3 전 예외를 적는다(N-02).
* 판정 표에 상태 기반 승인 검사를 더한다(N-03).

**판정: 수정 후 승인.**
