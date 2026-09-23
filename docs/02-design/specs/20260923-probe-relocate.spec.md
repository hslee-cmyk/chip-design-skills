---
id: 20260923-probe-relocate
phase: 2
evidence_type: test-only
gate_change: no
approval: 20260923-20-dead-code-dup-design
---
## 의도

TS6(계획 N3.11), design `20-dead-code-dup` v1.1 §5·§8 P2: 승격하지도 삭제하지도 않는 probe 32개를 `A/tests/probes/`로 옮기고,
운영 도구 `A/tests/derive_achievable_bounds.py`를 `A/tests/tools/`로 옮긴다(N3.11 TS6 문장: 도구 이동은 code 커밋으로 추가한 뒤
test 커밋으로 원본을 지운다). 옮기는 김에 probe 안의 Windows 절대 경로를 저장소 기준 상대 경로로 바꾼다 -- 다른 기계·격리 복제본에서
실행조차 되지 않던 것을 고치는 경로 수정이고 계산은 건드리지 않는다. A = `skills/analog-gmid-design/assets`.

## 관찰 가능한 계약

1. probe 32개가 `A/tests/probes/<같은 이름>.py`에 있고 `A/tests/`에는 없다. 목록은 design §5와 실측 `probe_inventory.json`(삭제 3·승격 7을 뺀 나머지).
2. 옮긴 파일의 내용은 **절대 경로 치환을 뺀 나머지가 바이트 그대로**다: 각 파일에 대해 (원본 바이트 == 새 파일 바이트) 또는 (치환한 경로 리터럴만 다르고 그 밖의 줄은 모두 같다)가 성립한다.
3. 절대 경로 치환: 대상 12개(`probe_L_search_window`·`probe_allocation_solvers`·`probe_diode_min_vgs`·`probe_diode_self_consistency`·`probe_diode_vds_window`·`probe_gmid_gain_landscape`·`probe_metric_tiers`·`probe_mirror_ratio_error`·`probe_runtime_budget`·`probe_stack_headroom_feasibility`·`probe_supply_current`·`probe_vds_assignment_paths`). 치환 뒤 그 파일에 Windows 절대 경로 리터럴(`^[A-Za-z]:[\\/]`)이 0개다. 경로는 파일 위치에서 계산한다(`os.path.dirname(os.path.abspath(__file__))` 기준).
4. `A/tests/tools/derive_achievable_bounds.py`가 있고 `A/tests/derive_achievable_bounds.py`는 없다. 내용은 경로 계산 줄을 뺀 나머지가 원본과 같다.
5. pytest 수집이 바뀌지 않는다: `--collect-only -q`의 test id 집합이 base와 같다(`probes/`는 `test_*.py`가 아니라 수집 대상이 아니다).
6. 엔진 소스(`A/*.py`, `workspaces/run_harness.py`)는 바뀌지 않는다.
7. 판정식 T(design `10-test-separation` §7)의 대상 정의는 그대로다 -- `A/tests/**` 중 `probes/**`·`tools/**` 제외. 옮긴 파일이 그 제외 안에 들어가므로 TS3 대조 test는 base와 같은 결과를 낸다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

test-only(계획 N3.12.3 개정 P5). 도구 이동분은 code 커밋 + test 커밋 두 개다(N3.11 TS6). 증거는 이동 동일성(계약 2·4)과 수집 불변(계약 5), 동작 보존(E-LIB·E-INST).

## oracle 종류와 출처

(c) 이동 전후 동일성: 기대값은 base 트리의 파일 바이트와 `--collect-only` 출력이다. 새 기대값을 만들지 않는다.

## 거부해야 할 입력

해당 없음(이동). 계약 3의 정규식 판정은 합성 문자열(절대 경로가 있는 줄)로 실제 거부를 보인다.

## library 회로 적용 여부

해당 없음. 동작 보존은 E-LIB·E-INST로 확인한다.

## 무동작 판정 입력(무발동 값)

삭제·승격 대상이 아닌 다른 test 전부 -- 판정이 base와 같다(계약 5).

## 재현할 수치

없음.

## 결정 필요 항목

없음(U-02 승인 `20260923-u02-d-list` 2항).
