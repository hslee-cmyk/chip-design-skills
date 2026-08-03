# 세션 컨텍스트 (2026-08-03)

## 작업 디렉토리
`C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills`

## 세션 목적
`docs/04-report/analog-topology-json-library.do.md`(2324줄)에 기술된 스펙이 실제로
어느 정도 구현되었는지, 문서의 "완료" 표시를 그대로 믿지 않고 실제 코드/파일을
직접 확인해 검증한다.

## 배경 — analog-topology-json-library 기능
- **WHY**: topology netlist가 Python 코드 하드코딩이라 재현 불가능, agent마다 해석이 달라짐
- **핵심 산출물**: `topology.json` 스키마(netlist/symmetry/compensation 3개 고정 섹션,
  이후 sizing_roles/area_priors 2개 섹션 추가) + 오케스트레이션 레이어(load_topology,
  run_topology_pipeline, save_instance_json, load_sizing_targets, write_sizing_results,
  run_sizing_pipeline)
- **관련 문서**:
  - `docs/01-plan/features/analog-topology-json-library.plan.md`
  - `docs/02-design/features/analog-topology-json-library.design.md`
  - `docs/03-analysis/analog-topology-json-library.gap-findings.md`
  - `docs/04-report/analog-topology-json-library.do.md` (본 조사 대상, Option C 승인,
    구현 중 3차 스키마 수정 반영)
  - `skills/analog-gmid-design/references/consistency-map.md` (원칙 변경 이력 정본)

## 조사 방법
- do.md 전체(2324줄)를 offset 페이징으로 완독
- general-purpose agent를 위임(foreground)해 문서의 각 배치 claim을 실제 코드로 대조:
  `skills/analog-gmid-design/assets/stick_diagram.py`,
  `skills/analog-gmid-design/assets/sizing_recipe.py`,
  `skills/analog-gmid-design/assets/topology_library.py`,
  `skills/analog-gmid-design/assets/library/*.topology.json`,
  `docs/03-analysis/analog-topology-json-library.gap-findings.md`,
  `skills/analog-gmid-design/references/consistency-map.md`,
  `workspaces/current-reuse-telescopic-ota-report/` 산출물 타임스탬프까지 확인.
  self-test(`stick_diagram.py`/`sizing_recipe.py`)도 직접 실행해 exit 0 재현.

## 조사 결과 요약

### 배치 1~6 — 완료, 문서 주장과 실측 일치
- `load_topology`(stick_diagram.py:3374) / `run_topology_pipeline`(:3437) /
  `save_instance_json`(:3579) 실존 확인
- self-test exit 0 확인 (Test 26 등)
- telescopic OTA 리포트 산출물(`final_report.html` 등) 실존 — 단 타임스탬프가
  Jul 28~29로 **배치 7 착수 이전 버전**

### 배치 7 — 세부 항목별 판정

| 배치 | 판정 | 비고 |
|---|---|---|
| 7-1, 7-2 | ✅ 완료 | self-test로 실측 |
| 7-3 (4번째 topology_fn: `current_reuse_telescopic_topology`) | ✅ 완료 | `topology_library.py:248` 등록, `_COMPENSATION_REGISTRY` 반영 |
| 7-3b (`allocate_stack_headroom`) | ✅ 완료 | |
| 7-3c (zero-base 사슬, 분석 문서) | 해당 없음(코드 아님) | 7-3.2로 코드 반영 |
| 7-3.2 (A/B/C/F 엔진: `propagate_topology_forced_currents` 등) | ✅ 완료 | |
| 7-3d (`optimize_full_circuit_budget`, `_THETA_FEED_REGISTRY`) | ✅ 완료(골격, 한계 자인) | 51개 소자 전체 자동 조립은 미완 — 문서도 인정 |
| 7-3e (`search_gm_id_for_role`) | ✅ 완료 | :966 |
| 7-3f (`select_L_by_role`) | ✅ 완료 | `_L_ROLE_MULTIPLIERS`, :1027 |
| 7-3g (1/f 노이즈) | ✅ 완료(계산 경로만) | 실측 LUT 재스윕 미수행 — 문서와 일치 |
| 7-3h (mismatch) | ✅ 완료 | `estimate_mismatch_sigma` |
| 7-3i (CMRR/PSRR) | CMRR ✅ / **PSRR은 placeholder** | `_PSRR_ESTIMATOR_REGISTRY`엔 diff_pair_tail만 |
| 7-4 (`repair_matching_safety`) | ✅ 완료 | Test 28 PASS |
| 7-4b (`select_layout_tool`, `estimate_area_budget`) | ✅ 완료 | Test 28 PASS |
| 7-6 (`derive_stack_groups`, `assign_finger_geometry`) | ✅ 완료 | Test 29 PASS |
| **7-5 (harness만으로 51소자 전체 재생성 — "최종 증거")** | ❌ **미완료** | 함수는 다 있으나 실제 51소자 전체를 harness만으로 끝까지 재생성한 실행 증거 없음. `workspaces/current-reuse-telescopic-ota-report/`가 여전히 배치 7 착수 전(Jul 28~29) 버전 |
| 배치 8 (추출 harness) | 계획만, 미구현 | 문서도 명시적으로 계획 단계 |

### 결론
함수/코드 단위로는 배치 7의 거의 전 항목(11개 중 10개+)이 실제 구현되어 있고
self-test도 통과한다. 다만 배치 7 전체의 원래 목적("harness만으로 51소자 실회로를
처음부터 끝까지 완주")을 증명하는 **배치 7-5 최종 증거만 비어 있다**는 게 유일한
실질적 미완료 항목.

### 부수 발견 (불일치 사항)
1. `current_reuse_telescopic_ota.topology.json`의 `device_roles`가 45개 필요분 중
   38개만 채워짐
2. `consistency-map.md`가 2026-07-27 이후 갱신 안 됨 — 배치 7 작업 전체가 이 정본
   문서에 미반영(기록 지연)
3. 문서 §10.3 결론("gap 없음")은 "배치 7-1~7-6이 전부 구현되면"이라는 가정형 문장이며,
   실제 실행 검증(배치 7-5)은 문서 스스로도 미결로 남겨둠 — 오독 여지 있음

## 다음에 이어서 할 수 있는 작업 (미결정, 사용자 확인 필요)
- 배치 7-5(harness-only 51소자 전체 재생성) 실제 실행 여부
- `consistency-map.md`에 배치 7 이력 반영
- `current_reuse_telescopic_ota.topology.json`의 `device_roles` 7개 소자 추가 채움

## 참고 — 사용자 협업 메모리 (관련)
- 최종 보고는 항상 한글로 (추론은 영어 가능)
- 상상으로 채우지 말고 근거·실제 확인 후 진행 (이번 조사에서 문서 claim을 그대로
  믿지 않고 코드/파일을 직접 대조한 이유)
- topology.json이 유일한 토폴로지 소스 — connectivity/device 정보는 항상
  `load_topology()`로 JSON을 읽어 쓸 것, 손타이핑 금지
