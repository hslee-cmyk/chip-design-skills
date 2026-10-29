---
id: 20260923-d-delete-telescopic
phase: 2
evidence_type: equivalence
gate_change: no
approval: 20260923-u02-d-list
---

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260923-d-delete-telescopic.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 2(죽은 코드·DUP 정리) card이고 Phase 2는 폐기됐다(계획 N6.1 '옛 Phase 처리' 2행 -- 새 엔진은 모듈 지도 N3.10으로 처음부터 개념당 정본 하나). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 본문은 기록이며 덧대지 않는다(O-169).

## 의도

design `20-dead-code-dup` v1.1 §6.4·§8 P5b: 파일럿 전용 CMRR·PSRR 폐형식 사슬을 지운다. 이 사슬은 **선언으로 도달 가능하다**
(`_CMRR_ESTIMATOR_REGISTRY`·`_PSRR_ESTIMATOR_REGISTRY`의 `telescopic_class_ab`·`telescopic_class_ab_cmfb` 키, `sizing_recipe.py:5185`·`:5296`)
-- 그래서 "지금 회로가 안 고른다"는 삭제 근거가 아니다. 삭제 근거는 **G-3(b)**다: 이 사슬은 파일럿 topology **파일 경로를 코드에 박아** 열고
(`_load_telescopic_topology_cached`, `sizing_recipe.py:5003`) 파일럿 넷 이름(`Vbias1`~`Vbias4`·`Vip`·`Vim`·`Vcmfb`·`Vop1`·`Vom1`)으로
31소자 부분망을 세운다(DF-29). **새 회로가 이 family를 선언하면 그 회로가 아니라 파일럿 값을 계산한다** -- 남겨 두는 쪽이 미래
topology에 더 위험하다. 일반 대체는 회로 무관 MNA `_metric_smallsignal_ratio_db`(입력을 선언에서 받는다)이고 파일럿이 이미 그쪽을 쓴다.
A = `skills/analog-gmid-design/assets`.

## 관찰 가능한 계약

1. 다음 9개 정의, 사슬 전용 상수·필드 2개, 레지스트리 키 4개가 없어진다(줄 번호는 base 98bd969 기준, 2026-09-29 정정).

| 대상 | 위치 | 도달 경로 |
|---|---|---|
| `_cmrr_telescopic_class_ab` | `sizing_recipe.py:4785` | `_CMRR_ESTIMATOR_REGISTRY['telescopic_class_ab']` |
| `_cmrr_telescopic_class_ab_cmfb` | `sizing_recipe.py:5118` | `_CMRR_ESTIMATOR_REGISTRY['telescopic_class_ab_cmfb']` |
| `_psrr_telescopic_class_ab` | `sizing_recipe.py:5204` | `_PSRR_ESTIMATOR_REGISTRY['telescopic_class_ab']` |
| `_psrr_telescopic_class_ab_cmfb` | `sizing_recipe.py:5260` | `_PSRR_ESTIMATOR_REGISTRY['telescopic_class_ab_cmfb']` |
| `_cmfb_amp_gain_diode_load` | `sizing_recipe.py:4867` | 위 둘에서만 |
| `_load_telescopic_topology_cached` | `sizing_recipe.py:4993` | 사슬 내부 |
| `_telescopic_class_ab_open_loop_response` | `sizing_recipe.py:5012` | 사슬 내부 |
| `_telescopic_open_loop_device_names` | `sizing_recipe.py:5063` | 사슬 내부 |
| `_telescopic_class_ab_open_loop_gains` | `sizing_recipe.py:5078` | 사슬 내부 |
| `_TELESCOPIC_FIXED_BASE`(모듈 상수, 파일럿 넷 이름 `Vbias1`~`Vbias4`) | `sizing_recipe.py:5009` | `_telescopic_class_ab_open_loop_response`에서만 (2026-09-29 추가) |
| `SizingContext._open_loop_gains_cache`(필드) | `sizing_recipe.py:2943` | `_telescopic_class_ab_open_loop_gains`에서만 (2026-09-29 추가) |

2. **G-4(명시적 거부)**: 삭제 뒤 `circuit_family: "telescopic_class_ab"`(또는 `_cmfb`)를 선언한 spec을 평가하면 `ValueError`가 나고 메시지에 등록된 family 목록이 들어간다. 조용한 무동작·기본값 대입·0 반환이 없다.
3. **일반 경로가 그 판정을 대신할 수 있다**: 합성 topology(라이브러리 밖 이름·넷)에 `smallsignal_ratio_db` metric을 선언하면 값이 나온다. 즉 삭제로 없어지는 것은 '회로 전용 지름길'이지 '판정 능력'이 아니다.
4. **G-3(b)의 증거**: test가 `_load_telescopic_topology_cached`가 열던 경로 리터럴과 사슬이 쓰는 넷 이름 리터럴이 **삭제 전 소스에 실재했음**을 기록하고(AST·문자열 리터럴), 삭제 뒤 `A/*.py`에서 그 경로 리터럴이 0건임을 단언한다.
5. **E-LIB·E-INST**: library 로드 가능한 회로 전부와 사이징 스펙 선언 회로(파일럿·`folded_cascode`)의 결과가 base와 같다. 파일럿은 이미 `smallsignal_ratio_db`를 쓰므로 값이 바뀌지 않아야 한다.
6. **NEW-TOPO**: 합성 topology로 로드·파이프라인 결과가 전후 동일.
7. **GONE**: 삭제한 이름 11개(정의 9 + `_TELESCOPIC_FIXED_BASE` + 필드 `_open_loop_gains_cache`)의 AST 참조가 `A/*.py`·`workspaces/run_harness.py`·`A/tests/**`에서 0. `workspaces/**`의 진단 스크립트는 판정 경로 밖이고 U-02 승인 3항대로 손대지 않는다(깨진다).
8. 레지스트리 §7의 해당 행과 §2 CMRR 행의 중복 셀을 같은 커밋에서 갱신한다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

equivalence: 선언된 회로의 결과가 바뀌면 안 된다. red는 없고(동작 보존), 증거는 E-LIB·E-INST·NEW-TOPO와 계약 2·3의 거부·대체 확인이다.

## oracle 종류와 출처

(c) 동작 보존(기대값 = base 실행 결과) + (a) 구성 입력(합성 topology와 합성 spec 선언으로 거부·대체를 보인다). 피검 함수의 출력으로 기대값을 만들지 않는다.

## 거부해야 할 입력

삭제한 family를 선언한 spec(계약 2) -- `ValueError`. 등록 목록에 없는 임의 family 문자열도 같은 거부.

## library 회로 적용 여부

적용: E-LIB·E-INST. 파일럿은 CMRR·PSRR을 일반 경로로 계산하므로 값 불변이 확인 대상이다.

## 무동작 판정 입력(무발동 값)

library 회로 전부 -- 판정과 산출물이 base와 같다.

## 재현할 수치

없음.

## 결정 필요 항목

없음(U-02 승인 3항: `workspaces` 진단 스크립트는 깨져도 두고, 필요하면 그때 되살린다). E-INST가 달라지면 F1로 보고하고 이 card를 되돌린다.
V5: 삭제 사슬을 판정하던 unit test 3개(`test_s066_family`·`test_s068_family`·`test_s069_section`) 삭제는 사용자 승인 `20260929-p5b-chain-tests`(DEC-40, 2026-09-29).

## 재시도 기록

1차 시도(2026-09-29, test 3adc173): auditor 순서 3에서 V5 FAIL(test 함수 삭제 3건, 승인 없음) -- R1 운반(`docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/v5-carry/20260923-d-delete-telescopic/`)
뒤 사용자 승인. auditor가 삭제 뒤 고아가 되는 `_TELESCOPIC_FIXED_BASE`·`SizingContext._open_loop_gains_cache`와 이 card의 옛 줄 번호를 찾아 계약 1·7을
개정했다(사용자 승인 질문에 포함). 같은 id로 1부터 다시 한다.

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260923-d-delete-telescopic.spec.md`.
