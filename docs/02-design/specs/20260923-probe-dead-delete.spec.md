---
id: 20260923-probe-dead-delete
phase: 2
evidence_type: test-only
gate_change: no
approval: 20260923-20-dead-code-dup-design
---
## 의도

TS6(계획 N3.11)의 첫 단계, design `20-dead-code-dup` v1.1 §5·§8 P1: DF-21이 이름을 댄 probe 3개를 지운다. 세 파일 모두 판정 경로가
아니라 진단 스크립트이고, 각각 **실행 자체가 불가능하거나 아무것도 판정하지 않는다**(실측 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/probe_inventory.json`).
A = `skills/analog-gmid-design/assets`. code 커밋이 없는 test-only 변경이다(엔진 소스 불변).

## 관찰 가능한 계약

1. 다음 세 파일이 없어진다: `A/tests/probe_mirror_common_L_wiring.py`, `A/tests/probe_node_voltage_audit.py`, `A/tests/probe_vs_semantics.py`.
2. 삭제 전 각 파일의 상태를 **삭제 근거로 기록**한다(test가 그 사실을 단언한다 -- 아래 계약 3). 근거:
   * `probe_mirror_common_L_wiring`: 엔진에서 없어진 `sizing_recipe._L_ROLE_MULTIPLIERS`를 읽어(66·142행) import 즉시 `AttributeError`. 42개 probe 중 심볼 결손은 이것 하나뿐이다.
   * `probe_node_voltage_audit`: 감사 대상 `audit_vsb_consistency`가 이미 운영 경로에 배선돼 있다(`sizing_recipe.py:9481`) -- 이 probe의 docstring이 적은 존재 이유("호출부 0")가 사실과 다르다.
   * `probe_vs_semantics`: 소자마다 `"vs" not in e`로 건너뛰는데 지금 `instance.json`은 `vsb`만 가진다 -- 전 소자 skip(무동작).
3. `A/tests/contracts/test_ts6_dead_probes.py`(신설)가 위 세 가지를 **판정**한다: (a) 세 경로가 저장소에 없다 (b) `sizing_recipe`에 `_L_ROLE_MULTIPLIERS`가 없다 (c) `audit_vsb_consistency`가 `sizing_recipe` 운영 경로에서 호출된다(AST) (d) 파일럿 `instance.json` 스키마에 `vs` 키가 없고 `vsb`가 있다. 합성 입력으로 (b)~(d)의 반대 경우에 그 판정이 실제로 실패하는 것도 단언한다.
4. 다른 probe 39개와 `tests/**`의 다른 파일은 바뀌지 않는다.
5. 엔진 소스(`A/*.py`, `workspaces/run_harness.py`)는 한 바이트도 바뀌지 않는다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

test-only(계획 N3.12.3 개정 P5): 대상 코드 불변. 증거는 삭제 전 상태를 고정한 contract test(계약 3)와 동작 보존(E-LIB·E-INST, design §3).

## oracle 종류와 출처

(a) 구성으로 정답이 정해진 입력: 삭제 근거 세 가지는 저장소의 현재 상태(심볼 유무, 호출부, instance.json 스키마)에서 직접 나온다. 판정기의 거부는 합성 소스·합성 dict로 보인다. 피검 출력으로 기대값을 만들지 않는다.

## 거부해야 할 입력

계약 3의 합성 반대 경우: `_L_ROLE_MULTIPLIERS`가 있는 합성 모듈, `audit_vsb_consistency` 호출이 없는 합성 소스, `vs` 키가 있는 합성 instance dict -- 각각 판정이 실패해야 한다.

## library 회로 적용 여부

해당 없음(probe 삭제). 동작 보존은 E-LIB·E-INST로 별도 확인한다.

## 무동작 판정 입력(무발동 값)

남는 probe 39개와 기존 test 전부 -- 판정이 base와 같다.

## 재현할 수치

없음.

## 결정 필요 항목

없음(U-02 승인 `20260923-u02-d-list` 2항: probe 삭제는 DF-21 3개로 한정).
