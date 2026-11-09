# 백로그 추가 초안 (다음 문서 커밋 때 .ai/context.md에 Python 바이너리 append)

- B29 library topology.json 주석 필드의 삭제된 이름 안내 정리 -- current_reuse_telescopic_ota.topology.json 1250·1281(`suggest_headroom_stack_groups`)·1872(`_metrics_comment`), nmcnr_amplifier.topology.json 74(`slew_rate()`). 사용자 결정 2026-09-30 보류("topology.json주석은 보류해"). 고칠 때: 승인 기록(쓰기 경로표 634행·U-16), 주석 필드만·connectivity 불변, auditor가 주석 외 필드 동일·E-LIB 동일 확인. S0 지문 영향 여부 실측 먼저.
- B30 Phase 2 이전부터 낡은 이름 안내(references·SKILL.md) -- 예: SKILL.md:52 `run_sizing_pipeline`, consistency-map.md 약 20개. P10 사전 실측(_drafts/prep_p9_p10.md §9, b22_scan.out.txt)에 목록. 문서 card로 묶어 처리.
- B31 백로그 번호 겹침 -- 문서 백로그 B22(.ai/context.md 14943행)와 history 4002행 §10.3 B22(`diode_vds_window`, 2026-09-09 해소)가 같은 번호. 엔진 주석 SR 567·3425·7412·레지스트리 77행은 history 쪽 뜻. 제안: context 백로그를 이후 `BL-` 접두사로.
- B33 V7 호출 그래프 간선 누락 -- 클래스 → `__init__`, 레지스트리 dict → 값 함수 간선이 없어 HEAD 엔진 def 109개가 미도달로 셈(예: `SemiEmpiricalGmIdLUT.__init__`, `_feed_*`). Phase 3 이동 card의 V7 판정에 잡음이 되므로 G1 전후 검토(Phase 3 design v2 준비 agent 관찰, 2026-09-30).
- B34 `skills/analog-grammar` 부재 시 stick_diagram 조용한 폴백이 결과를 바꿈 -- current_reuse θ* 평가가 성공 → ValueError(vertical_stack_id 순환). 조용한 기본값/폴백 금지 원칙 위반 후보(B26 결정 자료 agent 관찰, 2026-09-30).
- B35 `skills/analog-grammar/assets/netclass.py` `RAILS`·`RAILS_POS`·`RAILS_NEG` 이름 집합 레일 판정 -- stick_diagram 11함수(운영 7)가 사용, code-author 쓰기 경로 밖(B26-1 초안 agent 관찰).
- B36 게이트 공백 -- `skills/analog-grammar`가 추적 파일인데 N3.12.2 쓰기 경로표 어느 행에도 없음: code-author는 못 쓰고 오케스트레이터·비 gmid agent 쓰기는 hook 통과, 게이트 도구(role_paths·V3·V7·source_lint·interface_card·weakening_diff) 범위 밖 -- 엔진 판정을 바꾸는 코드가 trailer·test·audit 없이 바뀔 수 있음. 결정 필요: 별도 skill로 게이트 범위 편입(기본안) 대 analog-gmid-design 흡수, 승인 2건. `install.py` SKILLS에 analog-grammar 추가는 사용자 작업(현재 설치본은 항상 B34 폴백으로 돔).
- B37 `load_topology`가 topology `ports` 선언을 analog-grammar에 넘기지 않아 운영 경로가 이름 정규식(`HINT_*`)으로 입력·바이어스 넷을 추정 -- topology 의존(B26과 같은 종류).
- B39 B34 범위 밖으로 넘긴 analog-grammar 부재 폴백 사이트 -- 사이트 4 `find_differential_and_mirror_forks`(기존 생존 변이 1개가 등가 `len(members) >= 2`→`>= 1`, 면제 승인 필요), 사이트 12 `propose_theta_kcl_gap_fill`(변이 242·인벤토리 5, 기존 생존 추정 ~48). B34(좁힌 범위) 뒤 처리.
- B40 `propose_device_roles_gap_fill`이 analog-grammar가 있어도 gate 없는 입력에 "analog-grammar를 import할 수 없어" 틀린 사유를 실음 -- B26-1에서 해당 분기 정리 때 함께(B34 초안 관찰).
- B41 DF-36 V3 판정(148bd6d, killed 22·exempt 4)의 exempt 4개는 `save_instance_json`이 바뀐 뒤 적용된 C8 승인(20260922-ic3-v3-exempt) id -- 승인 범위 밖 누수 실례. 판정 자동 번복 없음(3b 재판정은 V3 재실행 안 함). history 기록 + 면제 묶기 card(20260930-v3-exempt-binding) 근거로 인용. 필요하면 DF-36 V3 재측정.
- B42 V3 데코레이터 변이 NOOP -- `_replace_def`가 데코레이터 변이를 버림(실측, 예 topology_library.py:248 `lru_cache(maxsize=256)` 상수 변이가 적용 안 됨). 현행 규칙에도 있는 도구 결함.
- B43 V3 상수 변이에서 bool 제외 -- def 머리 기본값 bool 변경 등 동작 변경이 변이 0개가 될 수 있음(범위 정책 검토 B2).
- B32 레지스트리 누락 -- 픽스처 함수 `folded_cascode_example`·`two_stage_ota_example` 행 없음(P10 재측정에서 발견).
