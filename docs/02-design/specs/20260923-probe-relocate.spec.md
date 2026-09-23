---
id: 20260923-probe-relocate
phase: 2
evidence_type: equivalence
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
2. 옮긴 파일의 내용은 **경로 줄을 뺀 나머지가 바이트 그대로**다: 각 파일에 대해 (원본 바이트 == 새 파일 바이트) 또는 (바뀐 줄이 전부 **경로 줄**이고 그 밖의 줄은 모두 같다)가 성립한다. 경로 줄 = 파일 경로 리터럴을 담은 줄과, 파일 위치에서 경로를 유도하는 줄(`os.path.dirname(...)`·`os.path.join(...)`·`sys.path.insert(...)`). 계산·판정 줄은 바뀌지 않는다(design §5 '경로만, 계산 불변').
3. **이동 깊이 보정(계약 2의 경로 줄)**: `A/tests/` 직속에서 `A/tests/probes/`로 한 단계 깊어지므로, 파일 위치에서 `assets`를 유도하던 줄의 `os.path.dirname` 중첩 수를 하나 늘린다. 실측 대상 22개(`ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` 형태). 보정 뒤 각 probe의 `ASSETS`가 `A`(=`skills/analog-gmid-design/assets`)로 해석되고 `sys.path` 삽입·`library/**`·LUT npz 경로가 이동 전과 **같은 실제 경로**를 가리킨다 -- test가 그 경로들이 존재함을 단언한다. 보정하지 않으면 이동이 probe를 깨뜨리므로 이 계약은 동작 보존의 일부다.
4. 절대 경로 치환: 대상 12개(`probe_L_search_window`·`probe_allocation_solvers`·`probe_diode_min_vgs`·`probe_diode_self_consistency`·`probe_diode_vds_window`·`probe_gmid_gain_landscape`·`probe_metric_tiers`·`probe_mirror_ratio_error`·`probe_runtime_budget`·`probe_stack_headroom_feasibility`·`probe_supply_current`·`probe_vds_assignment_paths`). 치환 뒤 그 파일에 Windows 절대 경로 리터럴(`^[A-Za-z]:[\\/]`)이 0개다. 경로는 파일 위치에서 계산한다(`os.path.dirname(os.path.abspath(__file__))` 기준).
5. `A/tests/tools/derive_achievable_bounds.py`가 있고 `A/tests/derive_achievable_bounds.py`는 없다. 내용은 경로 계산 줄을 뺀 나머지가 원본과 같다.
6. pytest 수집이 바뀌지 않는다: `--collect-only -q`의 test id 집합이 base와 같다(`probes/`는 `test_*.py`가 아니라 수집 대상이 아니다).
7. 엔진 소스(`A/*.py`, `workspaces/run_harness.py`)는 바뀌지 않는다.
8. 판정식 T(design `10-test-separation` §7)의 대상 정의는 그대로다 -- `A/tests/**` 중 `probes/**`·`tools/**` 제외. 옮긴 파일이 그 제외 안에 들어가므로 TS3 대조 test는 base와 같은 결과를 낸다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

**equivalence**(계획 N6.1 Phase 2 행의 판정 유형, N3.11 TS6 '운영 도구 이동은 code 커밋과 test 커밋 두 개'). 이 변경은 운영 도구를 `tests/tools/`로 옮기므로 **code 커밋과 병합이 생긴다** -- test-only의 커밋 모양(병합 0·code 커밋 없음, `00-common` §8.1 `code_commit: null`)과 맞지 않는다(1차 시도 auditor가 base 판 merge gate로 실측해 확인: "test-only에 병합이 있다").
동작 보존 변경이라 red가 없고, 증거는 이동 동일성(계약 2·3·5), 수집 불변(계약 6), 회로 동작 보존(design §3 E-LIB·E-INST)이다. `equivalence.commands`에는 E-LIB·E-INST 명령과 계약 2·3·5 대조 명령을 적고 `outputs_hash`에는 그 출력 해시를 적는다.

## oracle 종류와 출처

(c) 이동 전후 동일성이 주다: 기대값은 base 트리의 파일 바이트와 `--collect-only` 출력, library·하네스 실행 결과다. 새 기대값을 만들지 않는다.
(a) 구성으로 정답이 정해진 입력도 함께 쓴다: 실측 `probe_inventory.json`의 목록(42 = 삭제 3 + 승격 7 + 이동 32), 경로 성분 수로 정하는 `dirname` 중첩 기대값, 절대 경로 판정기의 합성 소스.

## 거부해야 할 입력

해당 없음(이동). 계약 4의 정규식 판정은 합성 문자열(절대 경로가 있는 줄)로 실제 거부를 보인다.

## library 회로 적용 여부

해당 없음. 동작 보존은 E-LIB·E-INST로 확인한다.

## 무동작 판정 입력(무발동 값)

삭제·승격 대상이 아닌 다른 test 전부 -- 판정이 base와 같다(계약 6).

## 재현할 수치

없음.

## 결정 필요 항목

없음(U-02 승인 `20260923-u02-d-list` 2항).
