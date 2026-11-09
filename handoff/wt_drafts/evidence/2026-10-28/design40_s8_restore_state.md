# design 40 §8 '복원' 행의 엔진 상태 (2026-10-28 스냅샷)

- 작성: 계획 v6.38.3 다섯째 커밋에서 계획 N6.35에 두었던 표를 여섯째 커밋(검증 5 L-9 -- 계획/이력 분리)에서 이 파일로 옮겼다. 상태 기록이지 규칙 근거가 아니다(O-165 (b)).
- 엔진 `wt/integ-it12` `d759838a`, 읽기·`git grep`만. 동작 완성도는 소유 card가 착수 때 다시 잰다.

**design 40 §8 '복원' 행의 엔진 상태**(엔진 `wt/integ-it12` `d759838a` 읽기만, 파일·식별자 존재 `git grep` -- 동작 완성도는 소유 card가 착수 때 다시 잰다; 2026-10-28 이 판 작성에서 확인, 끝난 뒤 status 빈 출력):

| 행 | 결정 | 엔진 상태 | 남은 일·소유 |
|---|---|---|---|
| R2 GB3 결합 변수 y | 복원 | 부분 -- S0 `coupling_vars`(`E/graph/coupling_vars.py`) 있음, 층 0 조립 입력 소비는 미구현 | LA-1 |
| R3 GB4 DOF·수치 rank | 복원 | 구현 -- `E/metrics/dof_report.py`, 표본 수 설정 | -- |
| R4 U-49 계획 정정 | 복원 | 계획 문언 몫(엔진 무관) | -- |
| R5 블록 국소 모델·잔차·감도 게이트 | 복원 | 구현 -- `block_gain_model`·`_helpers_nodal`·`sensitivity_gate`; 게이트 fail-open = E-01 | UB-1(E-01·E-16) |
| R6 SP1 셀·루프 | 복원 | 구현 -- `cells`·`loops`·`loop_roles` | -- |
| R7 `rule_branch_coverage.json` | 축소 유지 승인 | 없음(승인대로) | -- |
| R8 GB5 `gm_req`·`comp_approx_gap` | 복원 | 부분 -- `gm_req`는 쓰기 계획 순서 힌트만, `comp_approx_gap`은 note 문언만(계산 없음) | LA-1(F-LA11 매크로 풀이·`comp_approx_gap` 기록) |
| R9 DC 동작 범위·`nqs_ratio`·`mismatch_sigma_v` | 복원 | 부분 -- `ls_fields`·`nqs_ratio`·`mismatch_sigma_v` 있음, 방향별 공급 능력(R9) 미구현 | DE-1·SB-1 |
| R10 `gain_budget_db_override` | 복원 | 구현 -- `E/authoring/spec_gain_override.py` | -- |
| R11 예산 점 풀이·`n_starts` | 복원 | 부분 -- `n_starts` 있음, 층 0 예산 점 풀이 미구현 | LA-1(E-25) |
| R12 MOD8 루프·LY7·재필터 | 구현 대상 | 부분 -- `convergence.converge` 있음, layout `revalidation` = `pending_wiring`, 재필터 0(E-24) | N6.1 구현 단위 MOD8 |
| R13 L 동치류 공유 | 복원 | 구현 -- θ 스키마 `l_ties` | -- |
| R14 미러 비 강제·DEC-95 (3) ratified·tol_I | 복원 | 부분 -- ratified·gm 요구 순서 힌트·자기 동작점 gm(tol_I) 구현, 미러 비 강제(D-GB7b, 새 θ 종류) 미구현 | 계획 card 없음 -- 미러 비 강제는 DEC-70 결정 몫, 승인 표 질문 |
| R15 뷰별 교류접지 | 복원 | 구현 -- `ac_ground_view`·`view_analysis` | -- |
| R16 대칭 θ 묶기 | 구현 | 구현 -- `orbit_ties`·`spec_untie` | -- |
| R20 ΔA_tie | 복원(계획 식) | 구현 -- `area_tie.area_tie_m2(a, b)`(두 점이 정함) | -- |
| R21 LY5 `W_adjustable` 즉시 완화 제거 | 복원 | 부분 -- `W_adjustable` = 쓰기 소자 여부로 정의(`E/convergence/layout_input.py:7`), 즉시 완화 경로 제거 여부 미확인 | LI-1 착수 때 재확인 |
| R22 LY8 확산 기하·수동소자 면적 | 구현 | 부분 -- 접합 변화·`passives_from_decl` 있음, 값 미정 수동소자 면적 = E-12 | SF-1 범위 9(E-12)·WB-1(손가락 기하) |
| R23 `verified_by`·모델 오차·`spice_unverifiable` | 구현 | 구현 -- `verified_by`·`model_error` | -- |
| R25 `vgs_for_current_density`·VS Hermite | 복원 | 구현 -- `vgs_current_density`·`_helpers_interp` | -- |
| R26 test 폴더 체계 | 축소 유지 승인 | 현행 체계(승인대로) | -- |
