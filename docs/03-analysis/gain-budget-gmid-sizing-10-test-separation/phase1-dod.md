# Phase 1 완료 조건(DoD) 측정 기록

대상: gate `master` = `da03c0e`(Phase 1 마지막 card C10 완료 기록까지). 측정 주체 = `gmid-verification-auditor`(독립 측정, 2026-09-23).
측정 명령의 정본은 design `10-test-separation` v1.2 §10 표이고, 조건의 정본은 계획 N6.2 Phase 1 행이다. 아래 수치는 auditor 보고를
그대로 옮긴 것이고 오케스트레이터가 다시 계산하지 않았다(계획 §14 작성자≠검증자).

환경: 격리 복제본(`--no-hardlinks --no-local`, origin 제거, `core.longpaths=true`)에서 `da03c0e` detach. Python 3.14.2 / pytest 9.0.2.
게이트 코드 캐시 = `<메인 .git>/gmid-gate-cache/da03c0e…`. `PT`는 §10 정의 그대로. 측정 뒤 복제본과 메인 저장소 모두 추적 파일 변경 0.

## 판정

| ID | 조건(N6.2) | 판정 | 측정 결과 |
|---|---|---|---|
| D0 | TS0 판정 기록 | PASS | `cat-file -e HEAD:.ai/verification/20260922-ts0-test16-fixture.json` exit 0 |
| D1 | TS1 seed 1~5 stdout 전후 동일 | PASS | C2 기록의 equivalence 20쌍 + **auditor 독립 재측정 20/20 바이트 동일**(base = merged = `868de660…de289`, 자기 복제본 경로 기준) |
| D2 | 소스에 인라인 self-test 0 | PASS | `extract_selftest.py scan` exit 0, 대상 7개 파일 전부 `has_inline_selftest=false`. 판별력 대조: `7792f9c^` 판 소스에서 exit 1, 4/4 true |
| D3 | TS2 기본·셔플 순서 PASS | PASS | `--gmid-dod` 기본 + seed 1~5 여섯 번 전부 exit 0, **278 passed / 15 xfailed / 0 failed / 0 error**(1회 70.0~72.5 s) |
| D3b | 셔플이 순서를 바꿈(Q) | PASS | 수집 293개 고정, 순서 sha256 앞 16자리 -- 기본 `d3753c28cae7cd60`, seed1 `075551f08d4565a1`, seed2 `890519c6a053fc83`, seed3 `7e516cd4ec8a4163`, seed4 `b950eead10804bef`, seed5 `bd366cc8d032ae10`. 같은 seed 두 번은 동일 |
| D4 | TS3 판정 문자열 0 | PASS | `contracts/test_ts3_no_print_verdicts.py` 10케이스 PASS(판정식 T = 0) |
| D5 | TS5 기준선 참조 0 | PASS | git grep 0줄. 판별력 대조: `7781bde`(C5 전) 4줄, `d72475a^`(U-43 전) 1줄, HEAD 0줄 |
| D6 | IC3·IC5 PASS, 나머지 IC xfail 선언 | PASS | IC3 2케이스·IC5 9케이스 PASS, 대조 test PASS, IC xfail 12케이스가 정규식 `^IC\d+ -- 담당 Phase (p) -- 만료: (p) DoD`에 12/12 일치, FAILED·XPASS 0 |
| D7 | 사례 caa970b 적발 | PASS | `run_all.py --cases 1 --mode direct`: cases `{"SKIPPED":6,"PASS":1}`, steps `{"PASS":2}`. attack red 0건(pytest exit 0), control red 1건(`builtins.AssertionError`) |

xfail 12케이스의 담당 Phase: IC1(6b), IC2(6b), IC4(6c), IC6(6c), IC7\[run](6a), IC7\[stop](6c), IC8(6c), IC9(6b), IC10(6b), IC11\[rail2](4), IC11\[rail3](6a), IC11\[reject](6a).

## N6.3 공통 조건

* auditor 판정 기록: HEAD 트리 `.ai/verification/*.json` 15건 전부 V1~V10이 PASS 또는 N/A, 비-PASS 0건.
* merge gate(EL4): card마다 `merge`/`audit` 커밋이 gate `master` 조상에 있음(형식 확인).
* 동작 변경 card의 거부 입력 test: Phase 1의 동작 변경은 게이트 변경 card 셋(C11·C12·C13)뿐이고 전부 red-green 기록.
* 동작 보존 equivalence: D1이 TS1을 덮고 나머지 card는 test-only.

## 남긴 관찰(PASS, 차단 아님)

1. **B11(Phase 3 소관)**: `extract_selftest.py scan`이 비재귀다(`root.glob("*.py")`). 지금은 `assets/` 바로 아래 7개가 전부라 누락이 없음을 `rglob`로 확인했지만, Phase 3에서 소스가 하위 디렉터리로 내려가면 D2가 조용히 exit 0을 낼 수 있다. 재귀화 또는 D2 명령의 root 목록화가 필요하다.
2. **B12(Phase 4 소관)**: `unit/`의 I-C11 xfail 3건(`test_s051_optimize_full_circuit_budget`·`test_s054_section`·`test_s157_M1`)은 reason에 `만료: <p> DoD` 절이 없다(IC 계약 케이스가 아니라 D6 대상 밖). Phase 4 DoD에서 이 3건의 해소를 함께 세지 않으면 만료 없는 xfail로 남는다. 승인 기록 `20260923-c9-v4-exempt`·`20260923-ts2-pytest-split`의 재검토 줄, 백로그 B9와 같은 자리다.
3. **B13(문서)**: §10의 `PT`가 이미 `tests` 디렉터리를 인자로 가져 D4·D6에서 뒤에 경로를 더해도 좁혀지지 않는다(전체 수집의 합집합 -- 더 넓게 보므로 판정에는 영향 없음). 또 D1 기록의 `outputs_hash`는 복제본 절대 경로에 의존한다(`stick_diagram` 출력에 경로가 1회 박혀, 경로 길이 차 92 B가 그대로 해시 차가 된다). 두 가지를 §10·§6.1에 한 줄씩 적어 재측정자가 오독하지 않게 한다.
