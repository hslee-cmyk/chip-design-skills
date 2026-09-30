---
id: 20260930-p4-relocate-test-retire
date: 2026-09-30
target_kind: diff
target: d705921ce8e620409e3ab68ec5a0934c8335b7bd03a5caaec3646bdc6ade0c4e
diff_base: 3a82a712a35583329acf6fbec91b98b98113e01f
diff_head: 637ef079a4164de1c0395544c86c997f6a6386c8
diff_path: skills/analog-gmid-design/assets/tests/contracts/test_ts6_probe_relocate.py
diff_path: skills/analog-gmid-design/assets/tests/probes/probe_diode_vds_window.py
diff_path: skills/analog-gmid-design/assets/tests/probes/probe_mirror_design_space.py
diff_path: skills/analog-gmid-design/assets/tests/probes/probe_mirror_gain_ranking.py
diff_path: skills/analog-gmid-design/assets/tests/probes/probe_mirror_wiring_readiness.py
diff_path: skills/analog-gmid-design/assets/tests/probes/probe_ratio_pair_analysis.py
diff_path: skills/analog-gmid-design/assets/tests/probes/probe_supply_current.py
scope: P4 -- P2 영구 바이트 대조 test 폐기와 probe 6개의 엔진 식 인라인 리터럴 -> 정본 호출 교체 DEC-40 승인(V5 발견 9건)
---

## 사용자 원문

> 승인

(질문: P4 V5 승인 -- diff_hash d705921ce8e6…(base 3a82a71 → 637ef07, 경로 7개: test_ts6_probe_relocate.py + probe 6개). 발견 = 계약 5 test 함수
삭제와 그 docstring 한 줄, probe 6개의 인라인 엔진 식 리터럴이 정본 호출로 바뀌며 사라진 것(probe 출력은 12개 모두 base와 동일) -- 선택지 '승인'.
앞서 사용자: P4 개정 제안 ①~⑤ "제안대로 승인", "끝나면 승인 받고 push까지 진행해")

## 범위 설명

덮는 것: 위 diff_path의 base→head blob 변경 -- `test_ts6_probe_relocate.py::test_relocated_probes_match_base_except_path_lines` 삭제(P2 이동 증거는
P2 판정 기록에 있고 이 영구 대조가 이후 probe 수정을 막는다)와 그 파일 머리 docstring의 oracle 목록 한 줄, probe 6개에서 미러군 키·`gate == drain`·
레일 이름 집합·`IDu<=0` 가드 등 인라인 엔진 식 리터럴이 정본 호출(`true_current_mirror_groups`·`is_diode_connected`·`_DEFAULT_RAIL_*`·
`size_transistor`)로 바뀌며 사라진 것, `probe_ratio_pair_analysis` 표시 서식(서식 튜플 → 이름 붙은 dict 서식, 출력 동일).
덮지 않는 것: 이 blob과 다른 내용, 다른 test 파일, 파일 안 다른 test의 판정 변경.
diff_head 637ef07은 1차 시도 test 브랜치의 끝이다(브랜치는 정리됨, blob은 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/v5-carry/20260929-probe-engine-dup/`에 운반).
