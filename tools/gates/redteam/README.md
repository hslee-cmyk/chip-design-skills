# tools/gates/redteam -- 공격 재생·과거 사례 재생

05-role-separation v3.6 §13.2(공격 시나리오)·§13.3(과거 사례)의 재생 데이터와 실행기다. 부트스트랩 ①에서 **검증 agent가
design 문서만 보고, 게이트 작성본을 보기 전에** 썼다(§13.1 ①, 계획 N3.12.6). 기대값은 design 문장에서 나왔고 각 기대에
근거 절(`basis`)을 붙였다.

## 실행

```bash
PY=C:/Python314/python.exe
$PY tools/gates/redteam/run_all.py --phase 0.5 --mode direct     # 공격 시나리오(§19 DoD 첫 행)
$PY tools/gates/redteam/run_all.py --cases 0.5 --mode direct     # 과거 사례 5건(§19 DoD 둘째 행)
$PY tools/gates/redteam/run_all.py --mode installed              # 설치 모드 -- 이 단계에서는 선언만(NOT-IMPLEMENTED)
# 옵션: --only <이름 일부>(반복), --repo <시험 대상 저장소 루트>, --keep(임시 디렉터리 보존)
```

* 결과는 `logs/<시각>-<mode>[-cases].jsonl`에 **케이스마다 한 줄 append**하고 마지막에 요약 줄을 쓴다(WP-11). 화면에는
  케이스 판정과 FAIL·ERROR 단계의 사유가 나온다. 종료 코드는 FAIL·ERROR·MISSING이 하나라도 있으면 1.
* 케이스마다 `%TEMP%/gmid-redteam/<시각>-<mode>/<케이스>-*/` 아래 **새 저장소**(작업 저장소·gate bare 저장소·역할
  worktree)를 만든다. 실제 저장소에는 읽기 명령(`git show`·`cat-file`·`rev-parse`·`ls-tree`)만 쓴다(`lib/sb.py`의
  `_assert_temp`·`repo_read`가 강제). 판정 환경 이름의 파일(`conftest.py`, `pytest.ini`, `.pyc` 등)은 이 디렉터리에 두지
  않고 실행 중 임시 저장소에 만든다(§13.2 #17, review31 N-12).
* 시험 대상 게이트 코드는 `--repo`(기본: 이 redteam이 든 저장소)의 `tools/gates/*`, `hooks/role_*`다. 원천 blob
  (`e329283:…`, probe의 고정 커밋 `4fd0fd8`)은 같은 저장소의 이력에서 읽는다(`RT_HISTORY_REPO`로 바꿀 수 있다).

## 판정 값

| 값 | 뜻 |
|---|---|
| PASS | 게이트가 돌았고 기대와 같다 |
| FAIL | 게이트가 돌았고 기대와 다르다(거부해야 할 것을 통과, 통과해야 할 것을 거부, 예외 traceback, 메시지 누락) |
| MISSING | **게이트 코드 파일이 없어 돌리지 못했다 -- PASS가 아니다** |
| NOT-IMPLEMENTED | installed 모드 재생(부트스트랩 ④ 설치 상태가 필요)을 아직 만들지 않았다 |
| ERROR | 재생 하네스 자체의 오류 |
| SKIPPED | 케이스의 `modes`·실행 Phase가 이 실행과 다르다(사유를 로그에 적는다 -- 12·13·14는 6a) |
| RECORD | 판정하지 않고 동작을 로그로 남기는 단계(§13.5 알려진 한계, §13.2 #17 '로그로' 항목) |

## 케이스 형식

`attacks/<번호>-<이름>/`(§13.2), `cases/<커밋>-<이름>/`(§13.3), `v3_survivor/`·`v7_unwired/`(§10 거부 증명):

* `setup.sh` -- sandbox 준비(판정 아님). 게이트 코드가 없으면 97로 끝나 케이스가 MISSING이 된다.
* `run.sh` -- 판정 단계. 각 줄의 `rt <동작> <단계 이름> …`이 `$WORK/steps.jsonl`에 한 줄씩 남긴다.
* `expect.json` -- §13.2가 정한 `{"layer", "exit", "message_contains", "modes"}`에 더해:
  * `basis`(근거 절), `phase`(실행 Phase, 기본 0.5), `title`, `skip_reason`
  * `steps` -- 한 케이스가 여러 겹·대조군을 가질 때 단계별 기대 `{layer, exit, kind, message_contains, basis}`.
    `kind`: `attack`(거부 증명) / `control`(오거부 0 증명) / `record`(판정 없음) / `precondition`(재현 전제).
    `exit`는 정수·목록(허용 값들)·`"any"`.
  * `steps_from_records: true` -- 단계 기대를 데이터 파일이 단계마다 준다(공격 15 `cases/*.json`, `v.json`, 공격 23).
* 모든 거부·통과 기대에 기본으로 `Traceback (most recent call last)`가 출력에 없어야 한다(예외로 끝난 fail-closed는 판정이 아니다).
* `contested: true` 단계는 design 문장끼리 기대가 갈리는 곳이다. 결과는 로그에 남기되 케이스 판정에 넣지 않는다(검증 보고에 모순으로 적었다).

## 파일

| 경로 | 내용 |
|---|---|
| `run_all.py` | 실행기 |
| `lib/rt.py` | setup.sh·run.sh가 부르는 단계 동작(sandbox, 흐름, hook·EL3·EL4·V 도구 호출, 공격 15·23 전용 동작) |
| `lib/sb.py` | 임시 sandbox·변경 한 건 흐름(§12)·판정 기록 템플릿·승인 기록·diff 해시(00-common §8.2) |
| `lib/iface.py` | 게이트 인터페이스(경로·명령 모양) -- design이 고정하지 않은 모양은 `INTERFACE_ASSUMPTIONS.md` |
| `attacks/15-records/cases/*.json` | 공격 15 케이스(판정 기록 연산 `ops`·승인 기록·커밋형 staged_diff, 각 `expect` = accept/reject) |

공격 23은 `docs/03-analysis/gain-budget-gmid-sizing-function-audit/v4_rule_probe/`(케이스 67, 누적 회귀 코퍼스 94)를
**복사하지 않고** 고정 커밋 `4fd0fd8`의 blob을 읽는다 -- 부트스트랩 ①이 probe를 지워도 원천이 남는다.
