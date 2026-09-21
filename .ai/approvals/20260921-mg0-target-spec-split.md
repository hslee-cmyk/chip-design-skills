---
id: 20260921-mg0-target-spec-split
date: 2026-09-21
target_kind: staged_diff
target: 68f9e2eaa794aa32ff64755eb73ca0b8b64365ce1ab2db4db8d6c2e2230c62e6
diff_base: e9fde7fe98afd42dd39836668fb6fe1ea7391dba
diff_path: skills/analog-gmid-design/assets/library/_TEMPLATE.topology.json
diff_path: skills/analog-gmid-design/assets/library/ngcc_3stage_ff.topology.json
diff_path: skills/analog-gmid-design/assets/library/nmcnr_amplifier.topology.json
diff_path: skills/analog-gmid-design/assets/library/pushpull_follower_buffer.topology.json
diff_path: skills/analog-gmid-design/assets/library/sf_pushpull_output_opamp.topology.json
diff_path: skills/analog-gmid-design/assets/library/two_stage_ota_sf.topology.json
scope: MG0(계획 N3.16) -- 5회로 문서 전용 스펙 필드를 _declared_target_spec / _paper_target_spec로 분리(U-39), _TEMPLATE vsb 안내·matching_pairs 예시 정정
---

## 사용자 원문

> MG0 진행해

> 기본안대로 확정 (Recommended)

(질문: 회로별 분류표 -- ngcc·nmcnr은 `sky130_supplies_v` → `_declared_target_spec.supplies_v`와 사용자 확정 목표, 논문 원값은
`_paper_target_spec`; pushpull·sf_pushpull·two_stage_ota_sf는 현재 내용 전부를 `_declared_target_spec`로, 도면·강의 원값만
`_paper_target_spec`; nmcnr DC gain > 100 dB와 kg는 declared에 넣지 않음 -- 기본안대로 확정을 골랐다.)

## 범위 설명

덮는 것: 위 6개 파일의 문서 전용 스펙 필드 재구성(`_paper_target_spec` 블록을 `_declared_target_spec`·`_paper_target_spec` 두 블록으로,
`input_dc_v`·`input_common_mode` → `input_dc_net`)과 `_TEMPLATE`의 `vs` → `vsb` 안내, matching_pairs 예시·설명을 두 축
(`current_forced`·`matching_sensitivity`)으로. 검증: 두 스펙 블록 밖의 키·값·순서가 HEAD와 같다(connectivity 불변), JSON 파싱 DoD 통과.

덮지 않는 것: connectivity, sizing_roles, 엔진 코드. 사이징 제약으로의 이관(7b, MG3).
