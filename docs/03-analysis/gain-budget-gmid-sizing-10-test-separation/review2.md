# review2 -- `10-test-separation` design v1.1 반영 확인(좁은 확인)

* 대상: design v1.1(603줄). 기준: review1의 S1-1~S1-4, S2-1~S2-6.
* 범위: 오케스트레이터 지시대로 다음 둘만 봤다. 다른 절의 새 지적은 하지 않았다.
  1. 각 지적이 반영됐는가.
  2. 반영이 새 범위 안 결함(실행 불가·게이트 거부·정상 흐름 오거부·계획 모순)을 만들었는가.
* 실측 도구: 게이트 코드 캐시 판 `.git/gmid-gate-cache/89d257c3…/`의 `role_paths.allowed`와 `role_hooks.run("PreToolUse", …)`를 in-process로 불렀다(파일을 쓰지 않는 판정만).
* 스크래치 스크립트: `el1probe.py`, 인라인 probe. 결과 파일은 `el1probe.json`, `el1probe_test.json`.

## 판정: **추가 수정 1건(S1) 뒤 승인 가능**

반영 항목 10건은 모두 들어갔다. 새로 생긴 범위 안 결함은 하나다. C11 계약의 `--gmid-strict` 값 전달이 conftest의 '모르는 케이스 키 거부'와 부딪혀 C8의 V3를 다시 막는다(아래 N1). 이것만 고치면 승인 가능이다.

## 반영 확인

| review1 | 반영 위치(v1.1) | 반영 | 반영이 만든 결함 |
|---|---|---|---|
| S1-1 Test 26 | §4 순서 8, §6.7 '이관본 Test 26 정정', §9 C8 행(R1 대상에 C8 추가, §11·§12·U-42) | 됨 | 없음. (가)는 거부 try 형태라 C9에서 `pytest.raises`가 된다. base에서는 (가)의 AssertionError로 이관본이 exit 1이 되어 `test_legacy_selftests`가 red이고, 병합본에서는 통과한다. test 경로만 바꾸므로 EL3 문제도 없다. |
| S1-2 V3 옵션 | 새 card C11 `v3-gmid-options`(§4 순서 7a, §6.10, §9) | 됨 | **N1(S1)** 아래. 쓰기 경로는 문제없다: `tools/gates/mutate_changed.py`는 code-author가 게이트 변경 조건 참일 때 True(거짓이면 False), `tools/gates/redteam/**`는 test-author가 조건 참일 때 True. redteam을 test로 쓰는 red-green은 선례가 있다(`.ai/verification/20260921-gate-output-utf8.json` red.test_ids가 `tools/gates/redteam/attacks/...`). 도구는 게이트 코드 캐시에서 실행되므로 재설치가 필요 없다는 주장도 맞다. |
| S1-3 R1 conftest 운반 | §12 R1 2·3단계(`<blob id>.blob` + `paths.tsv`, bash `git cat-file blob >`, `cp` 복원), §9 R1 행 | 됨 | 없음(EL1 실측 아래). |
| S1-4 U 번호 | U-41·U-42·U-43, 참조 줄 전부 | 됨 | 없음. 문서에 `U-40`이 0건이고 계획 N7.2와 겹치지 않는다. |
| S2-1 토큰 354 | §3, §6.3, §9 C4, §7 T 식 | 됨 | 없음. |
| S2-2 C8 V3 입력 | §6.7 'V3 대상과 죽일 입력'(연결 파일 픽스처, 등가 변이는 decision 승인으로만) | 됨 | 없음. 픽스처는 WP-07 '로드·변형' 범위이고 test 경로다. |
| S2-3 C6 V1 | §6.5("C6의 병합본 실행부터 `--gmid-phase=1`, base 쪽 실행은 붙이지 않음") | 됨 | 없음. merge gate는 C6 때 대조하지 않고 `--gmid-phase=` 토큰은 허용 목록에 있다(`merge_gate.py:981-985`, `:1209-1213`). |
| S2-4 빈 엄격 집합 | §5.4(`00-common` §9.3 인용 + "빈 값 = 키 없음") | 됨 | 없음. |
| S2-5 V4 (3) 섹션 | §6.8 규칙 6 | 됨 | 없음. 조건을 assert로 더하는 것은 판정 추가라 M2(≥)에 맞는다. 근거를 댈 수 없으면 멈춘다. |
| S2-6 05 §18 | §12 R2 | 됨 | 없음. R2는 05 design 문언 개정이고 05는 계획서가 아니라서 plan_tables와는 **해당 없음**이다. 확인으로 계획서는 수정되지 않았고(`git status --porcelain docs/01-plan` 빈 출력) 해시는 여전히 `7167e02839f86c4ecbcd91a63a9833c4d83a8aab8008bfe2d8cfc36206d2596d`이다(캐시 `merge_gate.py plan-tables-hash`). P1~P5 문언은 v1.0과 같아 review1의 '해시 불변' 실측이 그대로 유효하다. |

### R1 운반 절차 -- 쓰기 경로와 EL1 실측

`role_paths.allowed`(부트스트랩 완료 기준):

| 주체 | 경로 | 결과(판정 행) |
|---|---|---|
| 오케스트레이터 | `docs/03-analysis/.../v5-carry/<id>/<40hex>.blob` | True (`docs/03-analysis/**`) |
| 오케스트레이터 | `.../v5-carry/<id>/paths.tsv` | True (`docs/03-analysis/**`) |
| test-author | 복원 대상 `tests/legacy/selftest_stick_diagram.py`, `tests/contracts/test_ic3.py` | True (`assets/tests/**`) |

`role_hooks.run("PreToolUse", …)`(Bash, 캐시 판):

| 주체 | 명령 | exit |
|---|---|---|
| 오케스트레이터 | `git -C <W>/<id>-test cat-file blob <T>:skills/.../tests/conftest.py > docs/03-analysis/.../v5-carry/<id>/<blob>.blob`(상대·절대 경로 둘 다) | 0 |
| 오케스트레이터 | `printf '…' > …/paths.tsv`, `mkdir -p …/v5-carry/<id>` | 0 |
| 오케스트레이터(대조) | 같은 리다이렉트를 원래 경로 이름 `…/v5-carry/<id>/skills/.../tests/conftest.py`로 | **2**(판정 환경 행 `**/conftest.py`). v1.0 결함이 실제로 거부되고, v1.1 이름 규칙이 그것을 피함을 확인했다. |
| test-author | `cp …/<blob>.blob <W>/<id>-test/skills/analog-gmid-design/assets/tests/conftest.py` | 0 |
| test-author | 같은 `cp`로 `tests/legacy/selftest_stick_diagram.py`, `tests/README.md`, `tests/baseline/stick_diagram.selftest.baseline.log` | 모두 0 |
| test-author(대조) | `cp`로 소스 `assets/stick_diagram.py`에 | 2(판정 트리) |
| test-author(대조) | `cp`로 docs 운반 디렉터리에 | 2(자기 worktree 밖) |

* test-author 판정은 가짜 worktree 경로 `<W>/<id>-test`를 `role/test/<id>` 브랜치로 보이게 `rp.worktree_of`·`rh.branch_of`만 바꿔 흉내 냈다. 스크래치 복제본에 실제 worktree를 만드는 시도는 Windows 경로 길이 제한으로 실패했고, 만든 것은 정리했다.
* `cp`의 원본(docs 쪽 `.blob`)은 읽기라 판정 대상이 아니다. 대상은 판정 환경·판정 트리에 걸리지 않는다.
* 결론: R1 절차의 명령은 EL1을 통과하고, 원래 이름을 쓰는 v1.0 형태는 거부된다.

## 새 결함(반영이 만든 것)

| # | 분류 | 지적 | 근거 | 최소 수정 |
|---|---|---|---|---|
| **N1** | **S1(A)** | **C11 계약이 C8의 V3를 다시 막는다.** §6.10은 "auditor는 V1 명령과 같은 값을 준다"고 적었다. C8의 V1 엄격 집합은 `IC3:,IC5:`(같은 Phase의 C7 `IC5:` 누적)이다. 그런데 `mutate_changed.py`는 **인벤토리 test만** 노드 id로 지정해 pytest를 돈다(`mutate_changed.py:216-219`). C8 인벤토리에는 `test_ic5`가 없다(AST만 읽고 엔진을 부르지 않아 정적 도달이 없다). conftest의 모르는 케이스 키 거부(`00-common` §9.3 `:405`: "키마다 **수집된** test 중 그 표식이 … 없으면 수집 오류")가 `IC5:`를 거부하므로, 변이 전 기준 실행이 UsageError → 모든 변이가 '살아남음'이 된다. S1-2와 같은 증상이 C11 뒤에도 남는다. §6.10의 redteam test(1)은 키 하나·test 하나라 이 경우를 잡지 못한다. | 위 조항들의 코드·문언 판독(인벤토리 선택 `mutate_changed.py:174-175`, 명령 `:216-219`) | C11 계약을 이렇게 바꾼다. `mutate_changed.py`는 받은 엄격 집합 중 **그 실행의 인벤토리 test에 표식이 있는 키만** 넘긴다. 남는 키가 없으면 `--gmid-strict=`(빈 값 = 키 없음, §5.4)을 넘긴다. redteam test에 "엄격 집합에 인벤토리 밖 키가 있어도 V3 PASS" 케이스(오거부 0)를 더한다. 막는 규칙은 넓히지 않는다(conftest 거부 규칙은 그대로다). |
| N2 | S3 | §6.10 test의 "`--gmid-phase`를 요구하는 conftest를 가진 합성 저장소"를 `tools/gates/redteam/**`에 **`conftest.py`라는 이름의 파일로 커밋하면** 판정 환경 행에 걸려 test-author가 쓸 수 없다(`role_paths.allowed` → False, `사용자 \| **/conftest.py \| 판정 환경`). 기존 redteam은 실행 때 임시 디렉터리에 만들어 쓴다(`redteam/lib/rt.py:789` `write(parent / "conftest.py", …)`, 커밋된 `conftest.py` 0건). 그래서 선례대로 하면 막히지 않는다. | `git ls-files tools/gates/redteam \| grep -i conftest` → `conftest.py` 이름 파일 0 | §6.10에 "합성 conftest는 실행 때 임시 저장소에 생성(커밋하지 않음)" 한 줄. |

N1만 고치면 반영 확인 기준으로 승인 가능이다.
