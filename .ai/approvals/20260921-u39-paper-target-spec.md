---
id: 20260921-u39-paper-target-spec
date: 2026-09-21
target_kind: decision
target: U-39
scope: MG0의 `_paper_target_spec` 처리를 계획 N7.2 U-39 기본안대로 확정
---

## 사용자 원문

> U-39는 기본안대로 하고 05 승인할게

## 범위 설명

덮는 것: 계획 N7.2 U-39 기본안 -- 지금의 `_paper_target_spec` 컨테이너(사용자가 확정한 스펙, U-25·U-34)를
`_declared_target_spec`로 옮기고 문헌 값만 새 `_paper_target_spec`에 둔다. N6.2 0.5 DoD는 JSON 파싱 기준(5회로에
`_declared_target_spec` 있음, `sky130_supplies_v`·`input_dc_v` 키 0, `_paper_target_spec`에는 문헌 출처 필드만)으로 고친다.

덮지 않는 것: 회로별로 어느 값이 사용자 확정인지의 분류. 기본안대로 MG0 작업 때 회로별 분류표를 사용자에게 보여 확인받는다
(topology.json 변경이라 U-16 승인도 그때 따로 받는다).
