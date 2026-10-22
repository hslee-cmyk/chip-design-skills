---
template: design
version: 1.12.9
plan_version: 6.32
---

# gain-budget-gmid-sizing -- 40-engine Design Document (새 엔진 `gmid_engine`, 색인·아키텍처)

> **Summary**: 새 gm/ID 사이징 엔진(`skills/analog-gmid-design/gmid_engine/`)의 설계 정본이다. 계획서 N3.1 흐름 GB0~GB9를 패키지·파일에 대응시키고, 단계마다 알고리즘·입출력·불변식·실패 코드·as-built 상태를 적는다. 계획서가 요구하고 실행 로드맵에서 빠졌던 gain-budget 흐름(FR-1·FR-2·FR-4·FR-8)은 `41-gain-budget`에서 전부 설계한다. gap 분석 기준표는 `42-gap-checklist`다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code
> **Date**: 2026-10-22 · **Status**: v1.12.9 **계획 v6.32(master `559f4da2`, 사용자 O-96·O-97) 맞춤판 -- 재검증 대기**(둘째 커밋 = 독립 검증 `wt/_drafts/evidence/2026-10-22/design_v1129_validation.md` 90/100 S-1·S-2·S-3(수정 수용 -- 셀 연산만 정함, 출처 하나 기준 기각)·S-4·S-5·N-1·N-2와 design↔계획 gap G1~G4 반영: §2.4.7 '정의' 개수 박은 문언 → 구성 상수·실측, '전달' 옛 부착 문장 정정, §11 파일 표 card 열 `B, IT-2e`, IT-2e test를 card B 행에서 IT 행으로, IT 행 결정 목록 O-94·O-96·순서 인용)(41 v1.12.9와 같은 변경 -- 백로그 B69 해소, card IT-2e: 이 문서는 §2.4.7 '실패 평가의 부분 스냅샷' 표 '정의'(DC 블록·봉인 항목 블록 실패 = 들어간 스냅샷을 base writer ∪ 앞 블록으로 줄인 것, 봉인 위반 = `dc_seal_report` 유지)·'형식'(근거)·'전달'(부착 자리가 집합 함수 `writers_in_scope`로 줄인 뒤 붙임, 재연 예외도 같음) 행, §11 card B 파일 표 `seal_versions.py`·`kernel_run.py`/`seal.py` 행과 test 행, §11 IT 행. 40은 v1.12.8을 건너뜀 -- 41 v1.12.8은 41만 바꿈. 줄 추가 없음). 아래는 v1.12.7 머리(대체됨): v1.12.7 **계획 v6.28(`e87092b3`, 사용자 O-85·O-86) 맞춤판 -- design 검증·사용자 승인 대기**(41 v1.12.7과 같은 변경 -- 이 문서는 §2.4.8 `icm_config` 행: 지원 밖 원소 = S1 `device.unsupported` READS·code `icm_config_feedback_element_unsupported`(옛 `..._source_unsupported`); 둘째 커밋(사용자 O-87 (1)): 차동 출력 결합·`icm_config_feedback_outputs_split`은 S-OS2 일반형 card 몫(이름 예약), IT-2c 차동 출력 + 선언 = S-OS2 code, 판정 서명에 출력 인자; 셋째 커밋(사용자 O-88): MOS 식별 = S1 정본 필드 `device.element_class` READS -- 둘째 커밋의 `device.pins` gate 단자 추정 대체). 아래는 v1.12.6 머리(대체됨): v1.12.6 **계획 v6.27(`dae968ec`, 사용자 O-81·O-82·O-83; O-84) 맞춤판**(41 v1.12.6과 같은 변경 -- 이 문서는 §2.4.8 `icm_config` 행: v1.12.5·v1.12.6 정의 불능 갈래 `icm_config_feedback_no_dc`(경로 판정 -- 41 §4.7-3b (1))·`icm_config_feedback_source_unsupported`, READS S1 다섯; §6 8 d/s 반대 선언의 S0 정지 한 줄(O-84). 40은 v1.12.5를 건너뜀 -- 41 v1.12.5는 41만 바꿈). 아래는 v1.12.4 머리(대체됨): v1.12.4 **계획 v6.24(`59ecc88e`, 사용자 O-70 (2)) 맞춤판**(41 v1.12.4와 같은 변경 -- 이 문서는 §2.4.8 `icm_config` 행: `transfer` resolution = δA_num(판정 분해능 정의 함수 `_transfer_resolution`, 41 §4.7-3b), S-OS2 일반형은 후속 card). 아래는 v1.12.3 머리(대체됨): v1.12.3 검증·gap 반영판(41 v1.12.3과 같은 변경 -- 이 문서는 §2.4.8 `node.dc_output_structure` 행에 권한표·소유표 등록(MF-3), `icm_config` 행에 멈춤 S-OS1·S-OS2 fail-closed code(MF-2·MF-4)). 아래는 v1.12.2 머리(대체됨): v1.12.2 맞춤판(41 v1.12.2와 같은 변경, 사용자 결정 O-63 (4)·O-64 (1)(2) -- 이 문서는 §2.4.8 표: 새 행 `node.dc_output_structure`(S0, writer `dc_writer_plan` 하나, 값 {`high_impedance`, `kvl_fixed`} -- 41 §4.7-1a), `icm_config` 행에서 `output_structure` 칸·값 `w3_target` 삭제, 다듬은 창 범위에서 `as_is_single_input` 포트·출발 창 미수렴 포트 제외(41:751 멈춤 해소), `node.dc_window_cfg` 행 '선형 감도 끝만 정의되는 구성의 정본 칸'). 아래는 v1.12.1 머리(대체됨): v1.12.1 **검증·gap 반영판 -- 계획 v6.22(`de301d2d`, O-62) 맞춤**(41 v1.12.1과 같은 변경 -- 이 문서는 §2.4.8 IT-2 행: W1 철회(`node.dc_window_cfg` 모든 구성, `node.dc_window` 값 독자 = 커널 탐색뿐), `input_status` 어휘를 41 §4.7-2와 맞춤(검증 M4), 다듬은 창 범위의 제외(M5), `output_structure` 세 값·분류 계산 자리 하나(M1·N6), 행 열 수를 표 머리 4열에 맞춤(N1), parent 무효화 공백 문언을 §4.7-3c 규칙으로 정정). 아래는 v1.12 머리: v1.12 **최종안 -- 계획 v6.22(`de301d2d`, 사용자 O-62 병합 승인 2026-10-21) 맞춤 완료; design 재검증·사용자 승인 대기**(41 v1.12 최종안과 같은 변경: 계획 v6.22 대기 표시 해소 -- 이 문서는 §2.4.8 `icm_config` 행(`kvl` 칸 → `output_structure`, O-61 P3)·§10 `saturation_window` 서명(`roots` 쌍·`slope`, O-61 P2)·§11 IT 행(keep 집합 = `ctx.base` writer ∪ 호출 블록, O-61 P1); 계획 v6.23 몫(O-62 P10·P11)은 설계하지 않음). 아래는 이 판의 앞 초안 머리: v1.12 **초안 -- 계획 v6.20(사용자 O-57 승인본) 맞춤 판**(41 v1.12와 같은 변경; 독립 검증 C1·M1·W1~W6·I1·I2 정정은 41 머리말, 이 문서는 §2.4.8 두 행·§10 서명 두 줄·§11 IT 행; S-1~S-4·T-1은 계획 v6.21(사용자 O-60 승인) 맞춤으로 41 §4.7-3a·3b·3c에 설계됨(O-58 반영, 2026-10-20 -- Status 초안·design 재검증 대기); §2.4.5 줄 인용 정정(단일 정본 감사 F4)): 사용자 결정 O-49 P1~P6(옛 결정 대기 D1~D6)을 결정으로 반영 -- §2.4.8 `node.dc_window_def_refined` 행에 기준 칸 `criterion`(P5)·사유 `window_end_saturation_unconfirmed`(P6), 다듬은 창 READS에 `node.dc_v` 없음(P1), 층 0 front 후보 호출 자리 = card LA-1 범위 12(P4); §11 IT 행 착수 조건을 '멈춘 항목 S-1~S-4(41 §4.7-3a·§4.7-3b -- O-50 G4·O-52·O-53 A-1 측정 구성의 층 순서·소유 card, O-55 V5 `off` 경계의 EO-1 선행)'로; O-54·O-55 창 경계 행은 41 §4.7-3a, EO-1 범위(O-56)는 41 §4.7-9 표시. 옛 초안 문장(계획 v6.19 기준)은 git 이력(`f10436ea`). 아래는 초안 머리 문장이다 -- card IT-1·IT-2 착수 전 design(옛 기준 계획 v6.19 N6.5·N6.6): §2.4.8 필드 소유표에 입력 포트 창 필드 셋(`node.dc_window` 범위 확대·`node.dc_window_def` DE-1 예약·`node.dc_window_def_refined` 새 writer `dc_window_refine`)과 `graph.metrics_icm_front`(새 writer `metrics_icm_front`) 행, §3.7 W0~W4 writer 계획 행(IT-1 '같은 DC' 엣지 폐기·다중 입력 뿌리 정지), §3.8-3·§3.8-8 `icmr_v`·`icm_margin_v`가 읽는 필드(IT-Q2 (다) 정의, 형식 불변 -- `swing_out_v`·`offset_sys_mv` 정의는 DE-1 몫이라 그대로), §10.1 API 행, §11 U17 표에 IT-1·IT-2 행과 J 표 U4·U7 행 개정 표시. 옛 문장은 계획 history H2 'IT-1·IT-2 design' 행.
>
> v1.11.3 -- card B(xrunf1b) 독립 design↔구현 gap 분석(S-7, 2026-10-20, 구현 `integ/xrunf1b-r5` da38429f)이 찾은 문구 불일치 3건을 구현에 맞춰 정밀화(원래 취지와 같음, 동작·범위 변경 없음): (1) §2.4.8 '세 블록 READS' 행 W-2 -- `w_requests`는 `W_m` 칸이 없으므로 참고 W에서 오는 `no_usable_slice` 요청(`E/layout/outputs.py:59`)의 `W_old_m`·`W_new_m`만 새 값이고 계산 필드에서 오는 그룹·`finger_quantization` 요청은 두 실행에서 같다고 적음 (2) §2.4.14 (4) `F_DEVICE`·`ly_device` 행과 `(DEVICE, F_DEVICE)` 행 '남아도 되는 곳' = 부재 검사 test의 검사 이름 목록과 그 근거 주석(`tests/structure/test_removed_names.py:33-35`)만 (3) §2.4.14 파일 표 -- 세 블록 행에 `_helpers_pattern.py`의 `DeviceView`·`device_views`(읽기 전용 조합 값, 필드 아님), `canon_block.py` 행에 블록 안 `_Device`·`_canon`. 옛 문장은 git 이력(v1.11.2 = master 9401e98f).
>
> v1.11.2 **승인됨**(사용자 2026-10-19 "승인", 독립 검증 승인 가능 -- O-42) -- 레이아웃 필드 소유 정정(사용자 결정 O-24·O-19 (1)·O-17 (3)·O-27 2026-10-19, card B 범위 안): §2.4.8 새 필드 `device: ly_point`(보존량 점, writer `ly_input`, 읽기 `ly_slice_density`), `ly_slice_density` 정식 `@compute_block`(READS `ly_point`·`ly_pdk`(폭 키 정본), WRITES `ly_slices`, 추가 인자 LUT memo만 `_LutHandle(memo)` -- as-built c3c50f14 대조), 사용자 결정 O-36 (3) 2026-10-19 "권고대로": (a) `ly_finger_candidates`·`ly_pattern_select`·`ly_rows` READS를 `ly_device` 열 통째에서 실제로 읽는 칸의 필드로 좁힘(`ly_point` 재사용 -- 칸 단위 문언과 다름은 O-39 (2) 승인 + 새 `device: ly_pins`·`ly_w_adjustable`), 정준 별칭표를 새 블록 `ly_canonical_naming`(새 파일 `E/layout/canon_block.py` 진입점 `canon_tables`, WRITES graph `ly_canon`·`ly_canon_rows`)으로 분리, `staged_snapshot` interface, 완료 조건 W-1~W-4(W만 2배로 바꾼 두 실행에서 세 블록 계산 0, auditor 격리 판정), (c) 정준 이름 W 표지 = 참고 `W_m` 유지와 근거; 사용자 결정 O-39 (1) "권고대로" (b): `ly_input`이 `LayoutDevice`를 겹치지 않는 네 필드(`ly_point`·`ly_pins`·`ly_w_adjustable`·새 `ly_attrs` = `DeviceAttrs(W_m, body, diode)`)로 나눠 쓰고 `ly_device` 삭제(공개 필드 계약 변경 승인, 새 사본 0, 소비자 전부 이전), §2.4.14 (3)·(4) card B 행 추가, `ly_point` = `dc_op` 두 단계 사본 부채와 후속 card 'layout 입력 정본화' LI-1(O-27, 원래 취지와 다름 -- 후속 card까지 사본 잔존; LI-1 범위에서 READS 좁히기·`staged_snapshot`은 O-36 (3) (a)로 card B에 들어오고 W 표지 변경은 (c)로 폐기), §2.4.7과 §2.3 경계 표 `LayoutResult` = (스냅샷)·§11 U14 행 옛 칸 이름 정정, `LayoutResult.computed_blocks` 삭제(정본 = `RunCounters`). 옛 문장은 계획 history.
>
> v1.11.1 -- §2.4.5 구조 규칙 M (M-c) 문언 정정(사용자 결정 O-17 (1)(2) 2026-10-19 "card B 1~3 권고대로", 원래 취지와 같음): 판정 단위 = `open_run()` 대입 문장(같은 이름 새 `open_run()` 재대입 허용), 가지(`if`/`else`·`with`·`try`·`match`)·반복문 본문 안 대입은 그 밖의 호출을 앞서지 않는다는 거부를 원문보다 엄격한 안전 쪽 해석으로 기록, 반복문 규칙 = 같은 가장 안쪽 반복문 본문, §2.4.14 (5) B 행 M-c 위반 픽스처 목록(design-validator 경미 3 반영). 동작·범위 변경 없음. 옛 문장은 계획 history.
>
> v1.11 -- XRUN-F1 실행 안 재사용 완성(사용자 결정 2026-10-15 "권고대로 진행해", X-1~X-5, 원문 `_drafts/user_decisions.md` 'XRUN-F1 design 착수 결정'. 사용자 취지 "계산 재사용은 처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용되게 한다는 것이 원래 취지였어"): §2.4.5 블록 결과 색인((블록, 분할, 입력 버전) → 그 값을 담은 스냅샷 참조, 계보 무관, 실행 수명, 상한 = §2.4.9 증거 집합 식)과 보존 규칙 = 실행 수명 동안 계산 원천 보존(보존 소유자 표·`retain`·`release`·`regenerated_after_release` 폐지), §2.4.4 호출 규칙(`donors`·`counters` 필수, 원천 = 블록 결과 색인, 키마다 원천 하나), §2.4.6 첫 평가 버림 제거(U17 ③에서 XRUN-F1 card A로 앞당김), §2.4.7 실패 평가의 부분 스냅샷·`KernelContext` 참조 칸, §2.4.9 계수 = 실행 전체 모든 (블록, 분할)·결과 JSON `perf.blocks`·판정 6 대상 소멸, §2.4.12 Q3 대상 소멸·Q12·Q13 열림(이후 X-8·X-9로 Q12·Q13 닫힘, `recomputes_same_input_failed` 칸 폐기), §2.4.13 (4)·(7), §2.4.14 신설(출처별 처리, ln 좌표 원값 보존 정본 `ThetaCoords`, 재작성 범위, 삭제·변경 목록, card A·B), §2.2·§2.3·§2.4.1·§2.4.10·§7.3·§11 U17 ②·③. 옛 문장·측정은 history. 같은 v1.11에 design 독립 검증(81, 조건부) 반영: 이식 전제를 모든 블록의 의무로(`*` 블록도 이식 대상, 섞인 성공·예외 fail-closed), §2.4.6 계수 창·`LutMemo.counting`·`open_count`·`fix_bound`·n_θ 출처·옮기는 순서·커널 평가 없는 실행·독립 계수 test, card A 판정을 단위 test 기준으로(블록 재계산은 보고만), `Donors`를 `core/donors.py`로, 감도 게이트는 clip 없이 원값 보존만(이후 X-14로 clip 인자 자체를 없앰), `perf.block_index_entries`·`block_index_bound`·`recomputes_same_input_failed`(Q13 결정 전 규칙), 레지스트리·`centre_start` docstring 갱신 목록, 줄 번호 f23aec8 기준. 같은 v1.11에 card C 결정 X-15·X-16(사용자 결정 2026-10-15 "1, 2번 둘 다 권고대로 해") 반영: 모든 실행에서 커널 평가 수 ≤ E_total(E_B 유도 실행 포함 -- 유도값은 실행 전체 평가 수, 넘치면 fail-closed), 감도 게이트 예약 R = 2 × 정의역 변수 수를 탐색 예산에서 먼저 떼어 게이트는 항상 돈다, `fd_jacobian` 예산 부족 = 예외 `FdBudgetShortfall`(N-3 오케스트레이터 기본안), 탐색 예산 계산 자리 `search_ceiling`. 같은 v1.11에 card C 검증(84) 반영과 사용자 결정 X-17(2026-10-15 "나로 해"): 선언 E_B = 탐색 예산, E_total = E_B + N_T + R(§2.4.9 정의 갱신), 선언 실행은 예산 fail-closed 없음(선언 40 그대로), 유도 실행은 E_total = D·탐색 예산 = D − N_T − R이고 남는 탐색 예산이 없을 때만 fail-closed(`ValueError`, N-4 오케스트레이터 기본안). 같은 v1.11에 재검증(88) B-4(Q13 결정 전 규칙 엄격안)와 사용자 결정 X-6~X-13(사용자 결정 2026-10-15 "3번 나, 4번 가, 나머지는 8번까지는 권고대로. 9번은 좀더 설명해줘", 원문 `_drafts/user_decisions.md` 'XRUN-F1 design 결정 1~8') 반영: 감도 게이트 RT 대체 확정(X-6), `donors` 필수 확정(X-7), Q12 닫힘 = 모든 커널 평가를 E_total에 넣고 묶음은 시작 전 확인·색인 상한 등록 때 fail-closed(X-8, 새 card C), Q13 닫힘 = 결정적 도메인 실패를 색인에 등록해 재연(X-9, `recomputes_same_input_failed` 대신 `replays`), evals `snapshot_fp`(X-10), U17 ② 항목 card B 앞당김(X-11), 색인 수명 단계 A부터(X-12), `KernelContext`·`StageAResult` 과도기 참조 칸(X-13). 같은 v1.11에 사용자 결정 X-14(2026-10-15 "9번 권고대로 해"): `ThetaCoords`는 좌표 변환과 시작 좌표 원값 보존만 맡고 clip 인자를 두지 않는다. 외층·층 0은 호출부에서 자기 상자로 자르는 단계를 명시하고, 감도 게이트는 자르지 않는다.
>
> v1.10 -- 사용자 결정 2026-10-15 "나로 해"(실행 사이 재사용 제거, 사용자 취지 "계산 재사용은 처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용되게 한다는 것이 원래 취지였어"): §2.4.3 전체 재작성(S0 수준 층 = 실행 수명, 디스크 스냅샷·S0 키·코덱·타입 등록부·U-68 정리·PDK 선언 경로 인자 삭제), §2.4.1 (d) 폐지(graph 밖 허용은 셋), §2.4.2·§2.4.5(S3를 실행 사이에 읽지 않음, `regenerated_from_prior_run` 폐지)·§2.4.6 U_S0·§2.4.9 판정 2·test·§2.4.10 허용 모듈·§2.4.12 Q1·Q2·Q4·Q9·Q10·§2.4.13(NFR-4 나머지: 키 (iv)·Q-N1·Q-N5·Q-N8 대상 소멸, 실행 환경 지문 = 결과 기록 칸)·§11 행. 삭제 목록은 §2.4.3 '삭제·변경 목록'. 옛 문장은 history. 원래 취지와 다른 판단 후보(LUT 파생표 디스크 캐시)는 결정 대기(Q9)(이후 결정: U-87 유지). 같은 v1.10에 3차 검증 남은 지적 반영: `env_fp` 단일 출처(N-6), 보존되지 않는 평가점 θ·`centre_u` 판정 불능(N-8), MOS가 닿지 않는 노드 판정 불능(N-10), S3 읽기 API 삭제에 딸린 CONTRACT·docstring·test 위치(N-4), conftest 인용 23-27(N-11). 같은 v1.10에 design 검증(91, 차단 0) 비차단 지적 반영: 삭제 목록 완료 규칙(이름 grep 0)과 빠진 소비자(모듈 지도·재수출·CONTRACT·docstring·`disk_hits`·결과 JSON 칸), front 조회 파일 경로 행(사용자 결정 대기, U-90)(이후 결정: 유지), S3 `snapshots/` 인코딩은 U17 ② 착수 전 정의, 옛 문장 대상 소멸 표시, Q9 결정 대기 표시(test 쪽 LUT 캐시 포함)(이후 결정: 유지), NFR4-F2·Q10 사용자 결정 대기(이후 결정: 분리 승인·유지). 같은 v1.10에 사용자 결정 2026-10-15 "U-87은 LUT는 관리복잡도가 없다는 네 판단근거에 따라 유지. 나머지는 기본안대로": Q9 유지(원래 취지의 예외), Q10 유지, Q11 제거 확정, NFR4-F2 분리 승인, front 조회 유지(조회 전용 읽기 경로) -- 결정 대기 표시를 모두 결정 규칙으로 바꿨다. 같은 v1.10에 델타 검증(84) 반영: grep 0 규칙을 이름별 범위로(살아 있는 PDK 선언 검사의 거부 사유 2개는 남김), front 조회 전용 읽기 경로의 구현 규칙(`read_front_entries`, `read_snapshot`을 `front_query.py`로 이동, 구조 규칙 J), `snapshots/` 인코딩 제약, 목록 줄 보강. 같은 v1.10에 델타 검증(86) 반영: 읽기 함수를 새 파일 `search/front_entries.py`로(규칙 A), `node_across_front` 서명 유지(`archive.dir`), 구조 규칙 글자 J → K와 하위 검사 K-a~K-c(K-c는 모든 `ast.Attribute`), `runs.jsonl` 단일 독자 범위 = 엔진 소스(기계 강제 아님), `STAGE_B_WRITERS` 무조건 삭제, CONTRACT 위치 추가.
>
> v1.10.1 -- card 1 xrun 구현(7e1b4be) 뒤 gap 분석 반영(사용자 결정 J-8 2026-10-15 "권고대로 진행해", 원문 `_drafts/user_decisions.md`): §2.4.3 'PDK 선언 값' 행에 J-1(`run_stage_a` 값 인자 `pdk_decl`·`lut_rule_decl` 삭제, 2026-10-15) 반영, §2.4.1·소유표의 `disk_failures` as-built 서술을 삭제 사실로. 동작 변경 없음.
>
> v1.9.4 -- 사용자 결정 2026-10-15 "1안·3안 진행하고 ③ 기준 변경도 승인해"(원문 `_drafts/user_decisions.md` 'NFR-4 BLAS 결정성'; 2안 = 순수 Python SQP 교체는 하지 않음): §1.2 EP-9 신설(결정성의 범위), §2.4.3 키 (iv) 실행 환경 지문과 'BLAS 스레드 고정'·'실행 환경 지문' 행(1안), §2.4.9 판정 2의 '같은 S0' = 같은 실행 환경, §2.4.13 신설 -- BLAS 고정 규칙(1안), 검증 기준(③: 같은 환경·같은 코드 = 비트 동일, 다른 환경·수치 보존 리팩터링 = 필드별), 필드 분류(D·C·K), 분해능 출처 표, 비교기 위치와 감사 사용, 캐시 키 비트 지문 유지 근거, 영향, 열린 질문 Q-N1~Q-N6(검증 반영 뒤 Q-N1~Q-N10), §11 U17 ② 선행의 'NFR-4 결정론 원인 수정'을 이 결정의 card로 교체. 3안(판정 경계 위 배치점 규칙)은 41 §5.13. 같은 v1.9.4에 독립 검증(88/100) 지적 반영: 1차 검사의 비트 동일 집합(T 시간 칸 제외)·전제(E_B 선언, 벽시계 정지 없음)·판정 불능과 벽시계 의존 경로 전수(B-1), pushpull 다른 환경 FAIL 처리 Q-N7·(5)(b) 기대 결과(B-2), 키 (i)~(iv)(N2), 매크로 분해능을 pm·두 번째 극점만 남기고 Q-N3으로(N3), BLAS 경유 호출 전수 표(N4), 미결 질문 동안 판정 불능·card 완료 조건(N5), Q-N6 측정(LUT 파생표 BLAS 호출 0)(N6), IC2 분류와 Q-N10(N7), 키 범위 Q-N8(N8), 끌어올림 s < 0 Q-N9(41 §5.13), 적재 모듈 열거로 세 번째 BLAS 검출·재확인 지점 (a)~(e)(N12). 같은 v1.9.4에 사용자 결정 2026-10-15 "기본안대로 진행해"(Q-N1~Q-N10 전부 기본안): §2.4.3·§2.4.13 질문을 확정 규칙으로, Q-N5 S3 실행 환경 지문 명세, 후속 card NFR4-F1, 결정 전 구현 금지 문구 삭제(자료가 없는 칸의 판정 불능은 유지). 2차 독립 검증(92) 반영: §11 U17 ② 행·42 D-ND3의 질문 범위를 §2.4.13 (5) 완료 조건으로(X-1), L-b 종료 사유 기록을 code 몫·완료 조건으로(N-a), (5)(a) 실행마다 빈 S3(N-b), 매크로 칸 전부 Q-N3으로(N-c), 복소 `lu_factor` 행(N-d), 결정 시점 문구 통일(N-e). 경위·측정은 history.
>
> v1.9.3 -- 사용자 결정 10(2026-10-14 "10도 권고대로", 방식 "재귀 정규화, marshal 없음"·"줄 번호 빼기"·"감싼 블록(__wrapped__) 포함", 원문 `_drafts/user_decisions.md` '결정 10' 두 항목): §2.4.3 '블록 코드 해시' 행 신설 -- `ComputeBlock.code_hash` = 블록 함수 code 객체(중첩 code 재귀, `__wrapped__` 사슬 포함)의 코드 내용 지문(파일 경로·줄 번호 제외, marshal 미사용, core `fp_of`, 상수 타입 명시 인코딩·미지원 타입 fail-closed `TypeError`), §2.4.3 'checkout 무관' 행의 미결 문구 삭제, §2.4.3 키 (iii) 문장, §2.4.9 판정 2 다른 checkout 단서를 결정 결과로, §11 U17 ② 선행에 결정 10 card(방식 확정). 같은 v1.9.3에 U-68 복구 정정(3차 판정 `wt/_audit_u17_1b_r3/audit_report.md` N-2, 사용자 결정 2026-10-14 "U-68은 권고대로 복구해"·"(가) 경로 인자 필수"·거부 기록 `decl=` "그대로 둠"): §2.4.3 '무효화' 행 -- PDK 선언·LUT 생성 규칙 선언이 U-68 정리 대상 입력 파일, `run_stage_a` 키워드 전용 필수 인자 `pdk_decl_path`·`lut_rule_decl_path`(경로는 키 메타 위치에만, S0 값·스냅샷 `fp`·`context_fp` 밖), 진입에서 경로 파일 sha ≠ `decl_sha256`이면 거부(fail-closed, 구현 7eb4865). 같은 v1.9.3에 as-built 문서 정정(판정 u17-1b-r4 988eef4·codehash ecda471의 경미 지적, 버전 번호 불변): '블록 코드 해시' 행 (2) import 시점 `RuntimeError`·(3) 상수 전 타입 (타입 이름, 값) 감쌈, '무효화' 행·§11 U17 ② 선행의 상태 문장을 구현·판정 결과로. 경위는 history.
>
> v1.9.2 -- U17 ①-b 독립 판정(`wt/_audit_u17_1b/audit_report.md`) 뒤 사용자 결정 2026-10-14 "3~9 모두 권고대로" 중 4~9 반영(원문 `_drafts/user_decisions.md` 마지막 항목: "4 run_stage_b settings 필수 인자(기본값 제거). 5 as-built b(context_fp)·c(SearchContext 옛 이름 읽기 속성) 수용, design 정정 v1.9.2 기록. 6 D6로 단계 A non-ok 회로 S0 24블록 재계산 수용(fail-closed), 정정 기록. 7 checkout 경로를 S0 값에서도 제거(로딩 시 해석) ... 8 test 환경 OPENBLAS 스레드 1 고정 + 엔진 결정론 원인 수정은 2 착수 전(백로그). 9 sizing CONTRACT 1.5 '덮지 않으면 TypeError'로 정정(v1.9.2)."): §2.4.3 `run_stage_b`의 `settings` 필수 인자(결정 4), §2.4.7 `context_fp` 문언을 as-built(평가 커널의 S0 입력 지문)로 정정·`SearchContext` 옛 칸 이름 읽기 속성 과도기 주석(결정 5), §2.4.3·§2.4.9 D6 저장 시점의 결과(단계 A가 ok가 아닌 회로는 스냅샷 없음, fail-closed 수용)와 G-10 판정 2 적용 범위 = 단계 A ok 회로(결정 6), §2.4.3 S0 값에 checkout 경로 없음(결정 7), §11 U17 ② 선행에 NFR-4 결정론 원인 수정(결정 8), sizing CONTRACT 1.5 TypeError 문구(결정 9, 이 문서 밖). core `ComputeBlock.code_hash`의 `co_filename` 경로 의존은 v1.9.3(결정 10)에서 정한다. 경위는 history.
>
> v1.9.1 -- U17 ①-b 착수 전 as-built 실측 정정(오케스트레이터 기본안 2026-10-13 U17 ①-b D1~D10, 원칙 근거·사용자 변경 가능, 사용자 결정 아님. 원문 `_drafts/user_decisions.md` 마지막 항목): §2.4.2 S0 레코드 값 형식과 `Placement` 위치 문장(`Placement`는 MOD8 `E/convergence/convergence_values.py`라 S0 아님), §2.4.3 저장 시점(D6), §2.4.1·§2.4.7·§2.4.8 소유표(`graph/s1v` 필드와 `coverage` 폐기 D1, `graph/ach` 필드와 `block_bounds` 폐기 D2, `graph/start` 필드 D3·`placement` ② 이월 D4, 단계 B 배선 ② 이월 D5, `noise_input_cells` 값 D7, `coupling`·`kernel` `theta_schema`·`constraint_classes` D8, `local_inputs` 값 형식 D9, LUT 파생 `E/lut/derived_fns.py` D10), §11 U17 ①·② 행. 정정마다 근거 한 줄(사본 금지·단일 writer·소비자 위치·동작 변경 회피)을 붙였다. 경위는 history.
>
> v1.9 -- 사용자 결정 2026-10-13 "1은 권고, 2도 권고, 3도 권고대로" (3)과 "①, ②, ③ 권고대로 진행해" ① 반영: §10.5 A' 판정 기준 신설(판정자 ngspice·독립 대조군 AI 손분석·피검 엔진 시작점·front, 판정 규칙, U17 단계 ② 완료 조건 -- 시작점과 front 점(U-45)의 ngspice 판정, MOD8 전 점은 T4-pre), §11 U17 ② 행 확인 행 D-AP1·test 열 완료 조건 인용. 결정 원문 밖 세부는 계획 U-76 기본안(사용자 변경 가능). 계획 v6.8 DEC-98·U-75·U-76. 경위는 history.
>
> v1.8.2 -- 사용자 결정 2026-10-13 "1은 권고"(d/s 비트 동일 범위 (라))와 U17 ①-a·①-c·①-d 실측 정정 반영: §6-8 D-2·D-3·§3.10.11 U-62·§10.2 -- topology d/s 표기 = 물리 방향 선언(사용자만 수정하는 정본), d/s 표기 맞바꿈에 대해 대칭 결과(궤도·정준 위치·`dc_colour`)는 비트 동일, 전류 부호는 표기 기준 방향 변환 뒤 동일, 사이징 결과(writer 계획·θ 스키마·ties·front)는 선언 방향을 따르고 틀린 선언은 봉인 7이 거부(`no_root_in_window`). 정정(결정 아님): §2.4.8 `dc_colour` 소유자 = graph 대칭 블록 `s1_symmetry`, §6-8 D-1 예시 toy 교체(완전 차동 직렬 가지 + 출력 사이 R1), §2.4.10 허용 모듈에 `core/snapshot_codec.py`, §2.4.3 U-68 정리 = 프로세스당 첫 실제 쓰기 1회·환경 변수 `GMID_S0_SNAPSHOT_DIR`, §2.4.4 분할 대상에 GB5 `passive_values`(단계 ② 이월 기록). 경위는 history.
>
> v1.8.1 -- U17 ①-d·①-e 실측에 문구를 맞춘 정정(사용자 결정 변경 아님): §6-3·§6-8·§10.2 (전류 묶음 수, 탐색 θ 변수 수) 정의를 `len(SearchDomain.ties)`(전체 묶음 수)·`len(SearchDomain.variables)`로(파일럿 29/38, 그중 전류 묶음 7), §6-3 열 순서 방향(자유 열 선택에서 비자명 궤도 우선 = 열 정렬 키에서는 비자명 궤도 원소를 뒤로), §6-5·§10.2 review 기록 코드 `diff_pair_orbit_split`, §2.3·§3.9 `LayoutResult` 칸 문구 → 설계점 스냅샷 `ly_*` 필드·`layout_outputs(snapshot)`. 경위는 history.
>
> v1.8 -- 사용자 결정 2026-10-12 다섯 건과 구현·검증 실측 정정 반영: §6-5 diff_pair review (나')("나'로 진행해"), §3.2-3 sf `drive_kind` 사실 없음·파일럿 `rule_hash` 재기록("1, 가로 해"·"2번 승인."), §6-3·§6-8 전류 기저 열 순서 규칙("3번 권고대로"), §2.4.8·§11 U16 `layout_outputs`("4번 권고대로"), §6-8 `tied_current_box_empty`, §2.4.3 `s0_snapshot` 보고서 키·PDK 선언 필수 인자·U-68 재현 판정, §2.4.8·§2.4.12 Q7 측정 완료·Q8 열림(`constraint_rows` ②로 이월), §2.4.9·§11 `test_g10_second_run_s0_zero` ②로, §10.2 test 3행. 경위는 history.
>
> v1.7 -- `budget_ref` 폐지(사용자 결정 2026-10-12 "다로 해"): `budget_ref` 엣지·concept를 만들지 않는다. 옛 `budget_reference_device`의 역할은 S1 레일-레일 기둥(DEC-71 (1), `E/graph/columns.py`)이 흡수한다. §3.2 `budget_ref` 문단, §3.7-8 폐기(노드 변수 writer = 쓰기 계획 규칙)와 구현 단위 측정 의무, §9.4 J8. 직전 안("가로 해"의 구조 유도 규칙, 열린 질문 BR-1·BR-2)은 이 결정으로 대체·소멸.
>
> v1.6 -- **v1.6 graph 정본 개정 (사용자 결정 2026-10-12), 사용자 승인(2026-10-12 "design 승인")**. 사용자 결정 2026-10-12 "1~4까지 새로고친 네 제안대로 해"(graph 단일 정본 + 계산 중복 제거)와 "G는 승인"(G-5·G-7·G-8·G-9·G-10)을 설계로 옮겼다.
> - §2.4 신설: graph 밖 허용 저장소 넷, S0 수준 층 필드와 디스크 영속화, 이식(graft)과 분할 계산 블록, S3 메모리 색인·스냅샷 보존, LUT memo 순수성·인스턴스 하나·상한 식, 값 사본 제거, 필드 소유표, G-10 계수·test, G-8 강제 장치, 열린 질문 Q1~Q7
> - §1.2 EP-2, §2.2 상태 층 표, §2.3 API, §3.7-3 tol_I, §7.3 성능·캐시 표, §11 단위 U17(3단계) 갱신. 42에 D-GR1~D-GR15 추가
> - 사용자 결정 2026-10-12 "P-1~P-15까지 권고대로 고쳐"(사용자 승인(2026-10-12 P)): §3.10 신설(P-2·P-3·P-6·P-7·P-10·P-11·P-12·P-13), §3.1 옛 이름·포트(P-4), §3.6 DEC-88 행(P-7), §3.9 MOD8 열린 항목 닫음(P-6), §10.3a DF 재발 금지 표(P-8). 42에 D-P2~D-P13 추가, DEC-22 행 정정
> - 계산값 재사용 확인 추가(사용자 지시 2026-10-12 "coding시에 계산값 재사용원칙도 준수되었는지 확인하는 과정을 넣고 이 확인내용을 항상 보고해"): §10.4·§11 공통 완료 조건, 단위 보고 필드
> - design 승인(사용자 승인(2026-10-12 "design 승인")): 승인 표시, §10.4·§11 공통 완료 조건에 graph 단일 정본 확인·gap 분석 단계 추가
> - U-04 결정(사용자 결정 2026-10-12 "U-04 권고대로"): §3.1 spec origin 행
> - U-51 결정(사용자 결정 2026-10-12 "U-51은 (나)로"): §3.6 외층 보상 단 폴백, §3.10.8·§3.10.10
> - U-71 결정(사용자 결정 2026-10-12 "U-71승인"): §3.10.3 (c)
> - K-2·GQ1·GQ3·GQ4·U-14·U-20·U-32·U-45 결정(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로"): §2.4.5 Q4, §2.4.12 Q1·Q4·Q7, §3.10.8 U-20, §3.10.10
> - U-67 결정(사용자 결정 2026-10-12 "U-67은 (나)로"): §3.10.8 I-A13, §3.10.11, §3.9 MOD7(LY4 대칭·`ly.lod`), §4 LOD 오라클 입력
> - C-3 결정(사용자 결정 2026-10-12 "C-3은 네 제안대로 해"): nmcnr L 주인 M105, §3.2-3 사실 표·상태
> - U-66 결정(사용자 결정 2026-10-12 "U-66은 (가)로"): §3.10.8·§3.10.11
> - U-63 결정(사용자 결정 2026-10-12 "U-63은 (가)로"): §3.10.11
> - U-60 결정(사용자 결정 2026-10-12 "U-60은 (가)로"): §2.4.6 (가) 확정, (나)는 한 줄 기록, DF-07 주석
> - C-1·C-3(사용자 결정 2026-10-12 "7절 권고대로"): 41 §1.5-4 혼재 노드 구동 종류 규칙 일반화, `structure.json` concept `l_owner` 추가(§3.2-3, 41 §1.12.5), C-6 파일럿 사실 파일 상태, U-65·U-68·U-69·U-70 결정("GQ2, N1, N3, K2 권고대로")
> - 결정 반영 동기화(2026-10-12): §6-8 d/s 맞바꿈 그래프 하나·D-1·D-3 결정("5절 권고대로"), §3.10.11 U-60~U-70 상태(U-61·62·64 결정, U-68~70 신설), §3.10.9 PN1~PN5 결정("4절도 권고대로"), §3.7-8 `budget_ref` 경로
> - 최종 검증·gap 재분석 반영(2026-10-12): 이식 투영 = 값 기반 정준 사상(N1), 열린 질문 해소·U-60~U-67 등록(N3), LUT memo 퇴출 판정 (가) 권고·(나) 함수 분류(N4), d/s 자기 맞바꿈 정지(N5), §3.7 DEC-12·13, §3.10.8 행 추가, §3.10.9~3.10.11, §9.4 남은 J 표, §10.4 단위 DoD 명령
> - design-validator 반영(2026-10-12, needs fixes → M1~M9·m1~m8): 분할 SCC·위상 순서·θ 배정, 이식 전제(시드 금지), 코덱 타입 등록부 계층, 색인 `local`/`solved`, memo 순수성 구조 강제, 퇴출 판정 사용자 결정 두 안, KernelContext·SearchContext 칸 배정·`metrics_dc` 분해능·단계 B 층·층 0 필드, 계수 소유 `RunCounters`, 보존 소유자. Q1~Q7 기본안(Q6만 사용자 결정)
>
> v1.5(2026-10-08): 사용자 결정 "j해석은 네의견에 모두 동의해."(J 공동분석)를 반영했다.
> - §3.2-3: `structure.json` concept 어휘 5개 신규, override/confirm 소비, `structure_rule_fp`, 단계 A 파이프라인 수정(`declared_loop_cuts`·사실 로드 순서), 회로별 사실 표(U1b 병합 뒤 작성)
> - §3.8-8: `ff_gm_ratio`, SP-2 (c) `icm_margin_v`
> - §9.2: sf `icm_margin_v` 제약
> - §9.3: J 결정 표 신설
> - §10.1: API 추가
> - §11: 구현 단위 U1b와 J 추가 범위
> - 구조 규칙은 41 §1.12에 있다
>
> v1.4는 사용자 결정 2026-10-08 "q3,q4는 네 제안대로 해"를 반영했다: §3.8-8 offset·미러비·스윙·ICMR metric 7개(닫힌 어휘), §9 Q3·Q4 확정과 §9.2 회로별 선언, §9 Q7 J 목록 추가, §10.2 오라클 Monte-Carlo·DC 스윕, §11 U3·U5·U6·U7·U9·U13 범위. v1.3은 사용자 결정 2026-10-08 "Q1~Q11 모두 네 의견대로 진행해"(§8·§9 확정)를 반영하고, §11 구현 단위를 추가했다. 아래는 v1.2에서 반영한 내용이다.
> - 재검증 지적 N1~N9와 Low 항목
> - 잡음 경로를 범위 안으로 넣기로 한 사용자 결정(2026-10-08)
> - `[ng-layer0-canon]` 49283c6 대칭 실측
> - v1.1에서 반영한 C1~C4, H1~H8, M1~M14, L1~L8과 R19 정정은 유지한다.
> **Planning Doc**: [gain-budget-gmid-sizing.plan.md](../../01-plan/features/gain-budget-gmid-sizing.plan.md) v6.11
> **as-built 기준**: master `004b7d2`(ng-perf-sizing 병합분 포함). 아직 병합되지 않은 브랜치도 함께 본다: `ng-cmfb-pm`(6a6e4c7), `ng-oracle-early`(d56ba66), `ng-tolv-cache`(674a6a1), `ng-layer0-canon`(0c5dc20), `ng-area-budget`(538eeab), `worktree-agent-a90dfb25fa6fe9f04`(7090b9f, LUT r2), `ng-bridge`(d529ea5).

진행 순서는 bkit PDCA다: 이 design → 구현 → gap 분석(`42-gap-checklist`).

## 문서 구성

| 파일 | 내용 |
|---|---|
| `40-engine`(이 문서) | §1 범위·원칙 / §2 아키텍처(흐름·상태 층·패키지 API·§2.4 graph 단일 정본·재사용 규칙) / §3 단계별 설계 GB0~GB9(gain-budget 외, §3.2-3 `structure.json` 개념·파이프라인) / §4 SPICE 오라클 / §5 CM(CMFB) 루프 / §6 대칭 / §7 면적 예산·성능 / §8 승인 없이 축소된 범위와 계획 이탈 / §9 사용자 결정(2026-10-08 확정, Q3·Q4 포함, §9.2 회로별 offset·스윙·ICMR 선언, §9.3 J 결정) / §10 신규 API·검증(오라클·DoD·IC test) / §11 구현 단위(병렬 배분) |
| `41-gain-budget` | FR-1(SP1 stage 유도, §1.12 J 구조 규칙), FR-2(블록 gain 모델과 MNA 잔차), FR-3 연계, FR-8(탐색 전 달성 불가), FR-4(층 0 gain 예산 조합 front와 `gain_budget_db`), 스펙에서 gm/ID·L 출발값 유도 |
| `42-gap-checklist` | FR·NFR·DEC·설계 항목마다 한 행: 설계 절, as-built 상태, 증거 위치 |
| `offset-trim.design.md`(별도 기능) | offset 전류 주입 trim(계획 `offset-trim.plan.md`). 이 문서의 §2.4(graph 단일 정본·XRUN-F1 색인·E_total)를 전제로 trim 필드·블록·card를 정한다 |

**표기**: `E/` = `skills/analog-gmid-design/gmid_engine/`. `P` = 계획서. 상태 어휘는 **OK**(as-built가 설계와 같음) / **DEV**(as-built가 설계와 다름. 어떻게 다른지 함께 적음) / **PART**(일부만 있음) / **MISS**(없음). 브랜치에만 있는 것은 `[브랜치명]`을 붙인다.

---

## 1. 범위와 원칙

### 1.1 범위

계획서 N1.3의 FR-1~FR-9, N1.4의 NFR-1~NFR-6, N3.1의 GB0~GB9를 구현한다. 지원 범위와 합격 기준은 계획서 그대로다(N1.2, DEC-59, DEC-85, N6.2 T1~T9). 옛 엔진(`legacy/`)은 참고로만 쓴다(DEC-82). 단위별 옛 엔진 대조는 범위 밖이다(P N6.3, 사용자 승인 2026-10-12 P-14).

### 1.2 엔진 원칙(설계 제약)

이 원칙들은 계획서와 사용자 결정에 근거하며, 아래 모든 절의 알고리즘이 지킨다.

| ID | 원칙 | 근거 |
|---|---|---|
| EP-1 | **topology 무관.** 회로·소자·넷 이름으로 분기하지 않는다. 지원하지 않는 구조를 만나면 `unsupported_rule_branch`로 정지한다. 일반성은 library 밖의 합성·변형(metamorphic) test로 잰다 | 사용자 2026-10-07 대원칙 3, DEC-62, WP-05 |
| EP-2 | **같은 값을 다시 계산하지 않는다.** 필드가 곧 캐시다(writer 1개 + 입력 버전). graph 밖에는 LUT memo(순수 함수, S0당 하나, 상한 있음)·S3 기록(출력)과 실행 안 메모리 색인·실행 계수만 둔다. 다른 lineage의 같은 입력 버전 결과는 이식한다. S0 수준 값은 실행마다 처음 한 번 계산하고 그 실행의 나머지 최적화에서 재사용한다. 실행 사이에 재사용하는 설계 값은 없다(§2.4.3) | 사용자 2026-10-07 대원칙, 2026-10-12 graph 단일 정본 결정, 사용자 결정 2026-10-15 "나로 해" 취지 "계산 재사용은 처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용되게 한다는 것이 원래 취지였어", NFR-2, WP-23, DEC-83 |
| EP-3 | **책임별 파일 분할.** 파일 구성 규칙 A~D를 따른다. 구조 test 규칙 A~K(K = §2.4.3 front 조회 규칙, v1.10)(`E/tests/structure/structure_checks.py`)는 인용만 하고 여기서 다시 정의하지 않는다 | 사용자 대원칙 2, WP-24 |
| EP-4 | **상수를 지어내지 않는다.** 모든 임계값은 선언값 하나(PDK·LUT·spec)에서 식으로 계산한다. 이 문서도 식만 적는다 | WP-03, N9.2-3 |
| EP-5 | **작성자 ≠ 검증자.** 기대값은 오라클 4종에서만 만든다 | WP-13, N3.11 |
| EP-6 | **LUT·PDK가 출처다.** 공정량(VDSAT·fT·gm/gds·IDu·잡음·용량·격자·MIM 밀도·mismatch 계수)은 LUT 열이나 PDK 선언에서 읽는다. 출처(파일·sha256·행)를 함께 기록한다 | DEC-87, DEC-91, N3.16 PDK 상수 |
| EP-7 | **판정과 출발값을 구분한다.** 근사식·구간·예산 배분은 출발점(층 0)과 보고에만 쓴다. 판정은 언제나 봉인된 스냅샷의 전회로 계산(DEC-74)과 SPICE 오라클이 한다 | DEC-67, DEC-74, DEC-92 (2) |
| EP-8 | **충돌은 보고하고 조용히 풀지 않는다.** 구간이 비거나 선언과 유도가 어긋나면 레코드로 남긴다(`review_needed`·실패 레코드·충돌 표) | DEC-44, WP-02 |
| EP-9 | **결정성의 범위.** 엔진은 실행 환경을 고정하고(BLAS 스레드 1, 확인 못 하면 거부) 그 지문을 결과 기록에 남긴다(v1.10: S0 키는 없어졌다). 같은 실행 환경·같은 코드의 산출물은 비트 동일이다. 다른 실행 환경이나 수치 보존 리팩터링의 산출물은 이산 판단이 정확히 같고 연속값이 선언 분해능 이내다. 필드별 비교에서 경로 계수(K)는 빼고 보고만 하고, 분해능이 선언되지 않은 연속값의 폭은 상류 허용오차 섭동의 감도 전파값, 선언 분해능보다 덜 재현되는 연속값의 폭은 max(선언 분해능, 감도 전파값)이다(Q-N2~Q-N4, 사용자 결정 2026-10-15 "기본안대로 진행해", §2.4.13). 판정 경계 위에 일부러 놓는 점은 선언량의 닫힌 식으로 만들고 판정 쪽으로 √ε 여유를 둔다(41 §5.13). 캐시 키(블록 입력 버전)는 비트 지문 그대로다 | 계획 NFR-4, 사용자 결정 2026-10-15 "1안·3안 진행하고 ③ 기준 변경도 승인해" |

---

## 2. 아키텍처

### 2.1 데이터 흐름 GB0~GB9와 패키지 대응

```
spec + topology + LUT + PDK 선언
  └─ GB0 authoring.load_topology / load_sizing_spec ─────────────── S0 지문
       └─ GB1 graph.build_s1 (DC 역할·미러·L 동치류·가지·기둥·G_vgs·matching) ── S1
            └─ GB2 graph.build_s1v (SP1: 뷰·셀·구동 종류·stage·블록·루프·극점 노드) ── S1v   [41 §1]
                 └─ GB3 graph.coupling_vars (K1~K8, 기둥↔블록 매핑) ── S1v
                      └─ GB4 metrics.achievability (블록 gain 상한·구조 DOF·면적 하한) ─ INFEASIBLE_TARGET  [41 §4]
                           └─ start_intervals (스펙 → gm/ID·L·I 출발 구간) ── 보고 표       [41 §6]
                                └─ GB6 search.layer0 (블록 국소 front → 조합 DP → gain_budget_db → 조립점) [41 §5]
                                     └─ GB6 search.find_front (외층 ε-제약 SLSQP, 비지배 필터)
                                          │  후보 θ마다 평가 커널:
                                          │   GB7 sizing.size_and_seal → 봉인 → GB5 제약 판정 → GB8 metrics.ss_evaluate
                                          └─ GB9 S3 archive, MOD7 layout ⇄ MOD8 W_request, 판정 축 재필터, SPICE 오라클
```

| 단계 | 패키지(MOD) | 주 진입점(공개 API) | 설계 절 | 상태 |
|---|---|---|---|---|
| GB0 spec | `authoring`(MOD2) | `load_topology`, `load_sizing_spec`, `rail_declaration` | §3.1 | PART |
| GB1 구조 | `graph`(MOD3) | `build_s1` 계열(`s1_dc_roles`, `s1_columns`, `s1_gvgs`, `s1_matching_groups`) | §3.2 | PART |
| GB2 stage | `graph`(MOD3) | **신규** `build_s1v` | 41 §1 | MISS |
| GB3 결합 | `graph`(MOD3) | **신규** `coupling_vars`, `column_block_map` | §3.3 | MISS |
| GB4 달성가능성 | `metrics`(MOD5) | **신규** `achievability` | 41 §4 | MISS |
| GB5 보상 | `metrics`(MOD5) + `sizing` θ 스키마 | `ss_evaluate`, `dc_theta_schema`(zero_cancel) | §3.5 | PART |
| GB6 할당 | `search`(MOD6) | `find_front`, **신규** `layer0_budget` | 41 §5, §3.6 | PART |
| GB7 DC | `sizing`(MOD4) | `size_and_seal`, `seal_dc`, `build_kernel_context` | §3.7 | OK(일부 DEV) |
| GB8 metric | `metrics`(MOD5) | `ss_evaluate`, `metric_value`, `area_search`, `supply_currents` | §3.8 | PART |
| GB9 탐색·검증 | `search`·`layout`(MOD7)·`convergence`(MOD8)·`report`(MOD9)·`pipeline`(MOD10)·`tools/spice_oracle` | `archive`, `run_layout`, **신규** `run_gmid_design_pipeline` | §3.9, §4 | PART |

위 그림은 대략의 흐름이다. 실제 계산 순서(S0당 1회 단계 A, 봉인 평가가 필요한 단계 B, 탐색 단계 C)와 그 사이에 순환이 없다는 규칙의 정본은 41 §0의 DAG다.

import 계층은 `core` < `lut` < `authoring` < `graph` < `sizing` < `metrics` < `search` < `layout` < `convergence` < `report` < `pipeline` 이다(P N3.10). GB4·GB5가 MOD5에 있는 이유는 P N3.1 '모듈 열 정정'이다.

### 2.2 상태 층(S0~S3)

| 층 | 정본 | writer | as-built |
|---|---|---|---|
| S0 지문 | topology·LUT·spec·유도 규칙 코드 해시 | `authoring`·`graph.s1_key` | OK |
| S1 구조 | 노드·소자·수동소자·관계 엣지·가지·기둥·matching | `graph` | PART(`l_class` proposed만, declared/ratified 전이 없음) |
| S1v 뷰 | 뷰별 셀·구동 종류·stage·블록·극점 노드·루프·끊는 점 | `graph.build_s1v`(신규) | DEV: 객체(`S1v`)로 컨텍스트에 실린다. §2.4.8에서 S0 수준 필드로 |
| S0 수준 파생(v1.6) | 결합 변수 y·매핑, GB4 상한표, 출발 구간, metric 구조 입력 | `coupling_vars`·`achievability`·`start_intervals`·`metric_structure` | DEV: 객체 사본(`sctx.ach`·`sctx.start`·`StartContext`·`CurveBook`). §2.4.8 |
| S2 `dc`/`ss`/`ls`/`layout` + 수동소자 값·`dc_gm`·제약 행(v1.6) | 노드전압·소자 op / 소신호 / 대신호 / 레이아웃 / 수동소자 값 / tol_I·`ss` 공용 gm / 제약 행 | `sizing` / `metrics` / `metrics`(신규 `ls`) / `layout` / GB5 블록 / `dc_tolerances` / search 제약 블록 | dc OK, ss OK, ls MISS, layout DEV(별도 lineage), 수동소자 값·`dc_gm`·제약 행 MISS |
| S3 탐색 기억 | evals·runs jsonl, front 점 스냅샷 참조, 메모리 색인(v1.6) | `search.archive`, `search.s3_index`(신규) | OK(기록 타입 결함 §3.9). 색인 MISS(as-built `sctx.cache` 등, §2.4.5) |

불변 스냅샷·구조 공유·필드 = 캐시는 `E/core/graph_snapshot.py:34,148-200`, `E/core/field_value.py:12-35`, `E/core/compute_block.py:77`에 구현되어 있다(OK). 재사용은 같은 lineage 안에서만 일어난다(블록 이름 하나의 `block_version`). lineage를 넘는 재사용(이식)과 분할 입력 버전은 §2.4.4가 더한다. v1.11: 실행 안 재사용은 계보와 무관하다 -- 실행 수명 블록 결과 색인(§2.4.5)이 다른 lineage에서 같은 입력으로 계산한 결과를 이식으로 준다(XRUN-F1, §2.4.14).

### 2.3 패키지 간 인터페이스(공개 API)

이미 있는 이름은 각 패키지의 `__all__` 그대로다. **신규**는 이 설계가 추가하는 것이다.

| 공급 → 소비 | API | 형식 | 상태 |
|---|---|---|---|
| core → 전체 | `GraphSnapshot`, `FieldValue`, `compute_block`, `LutMemo`(lut), `FailureRecord`, `exit_code_for`, `normalized_margin`, `read_pdk_decl`, `MetricSignature` | 기존 | OK |
| core → 전체(v1.6) | **신규** `graft`, `Donors`(v1.11: 추상 기반 `find`·`register`, 구현 = search `S3Index`), `compute_block(..., partition=)`(v1.11: 호출 `block(snapshot, *extras, donors=, counters=)` -- 두 키워드 모두 필수, §2.4.4), `GraphSnapshot.write(name, part, input_version, rows)`·`block_version(name, part)`(서명 변경), `RunCounters`(`run_counters`). (v1.10: 스냅샷 코덱·타입 등록부는 실행 사이 재사용 제거로 만들지 않는다 -- §2.4.3) `LutMemo.call(fn, *args)`가 `lookup`을 대체하고 memo 함수는 `lut/derived_fns.py` | §2.4.3·2.4.4·2.4.6·2.4.9 | MISS |
| search 내부(v1.6) | **신규** `S3Index{find, register, get, failure, local, solved}`(v1.11: `register` 추가, `retain`·`release` 폐지 -- 실행 수명 보존. `find`·`register`는 XRUN-F1 card B, 나머지는 U17 ②) | §2.4.5 | MISS |
| lut → sizing·metrics·layout | `op_point`, `vgs_for_gm_id`, `vdsat`, `gmb`, `caps`, `tol_v_table`, `tol_vdsat_table`, `curve_report`, `load_lut_set` | 기존 | OK |
| lut → 41 §6 | **신규** `ft_curve(kind, L, VDS, VSB)`, `intrinsic_gain_curve(...)`, `vdsat_curve(...)`, `idu_curve(...)`(gm/ID 축 곡선), **신규** `vgs_for_current_density`(DEC-88) | (gm/ID 배열 → 값 배열), LUT 곡선 표 memo | MISS(조합으로는 계산 가능) |
| authoring → graph·search | `SizingSpec`(제약·목표·θ 범위·설정), **신규 필드** `gain_budget_db_override`, `driving_spec`, `untie_orbits`(옛 설계 이름 `symmetry_untie`), `cm_sense_elements`[ng-cmfb-pm], `element_values.*.measurement_load`[ng-area-budget] | spec 로더 | PART |
| graph → sizing·search·metrics | S1(기존), **신규** `S1v{views[], l_classes, findings, declared, applied_facts}`(블록·복합 블록·극점 노드·루프·끊는 점은 `ViewS1v` 안. `coverage`는 폐기 -- v1.9.1 D1, 사본 금지, 필드는 §2.4.8), **신규** `orbits`(자기동형 궤도) | S1v 스냅샷 필드 | MISS |
| sizing → search | `size_and_seal`, `build_kernel_context`, `dc_theta_schema`, `dc_current_basis` | 기존 | OK |
| metrics → search | `ss_evaluate`, `metric_value`, **신규** `block_local_gain`, `achievability`, `ls_fields` | | PART |
| search → layout·report·pipeline | `find_front` → `FrontPoint`, `node_across_front`, **신규** `layer0_budget` → `BudgetCombination{gain_budget_db, ...}` | | PART |
| layout ⇄ convergence | `run_layout` → 설계점 스냅샷의 S2 `ly_*` 필드(§2.4.7·§2.4.8, `LayoutResult` = (스냅샷), 계산·이식 기록은 `RunCounters`), 파생 값(`w_requests`·`revalidation` 등)은 `layout_outputs(snapshot)`, **신규** `converge(snapshot)` | | MISS(MOD8) |
| pipeline | **신규** `run_gmid_design_pipeline(spec, *, search, output_dir, instrument, activations_out)` | exit code = `exit_code_for` | MISS(`[ng-bridge]`에 오라클 입력 생산자만) |


### 2.4 graph 단일 정본·재사용 규칙 (v1.6 graph 정본 개정)

> **v1.6 graph 정본 개정**(사용자 결정 2026-10-12 "1~4까지 새로고친 네 제안대로 해", 같은 날 "G는 승인"). **design 문안은 사용자 승인(2026-10-12 "design 승인")됐다**. 결정 자체(1~4절, G-5·G-7·G-8·G-9·G-10)는 승인됐고, 이 절은 그 결정을 엔진 설계로 옮긴 것이다. 계획 근거는 DEC-83·NFR-2·WP-23·N3.3·N3.5·N3.6(v6.4 정정)이다. 41(gain 예산)은 이 절을 "40 §2.4"로 인용한다.
>
> **as-built 기준**: `u15-layer0-tests` @bd19cc6(`wt/u15-layer0-tests`). 아래 증거 줄 번호는 모두 그 커밋의 `E/` 기준이다.
>
> **design-validator 반영**(2026-10-12, M1~M9·m1~m6): 분할과 SCC(§2.4.4), 이식 비트 동일 전제(§2.4.4), 코덱 타입 등록부의 import 계층(§2.4.3), 색인 API 분리(§2.4.5), memo 순수성의 구조 강제(§2.4.6), 퇴출 판정은 U-60 (가)(§2.4.6, "U-60은 (가)로"), 빠진 항목(§2.4.7·2.4.8), 계수 소유(§2.4.9), 보존 소유자(§2.4.5). 열린 질문은 기본안을 정해 두었다(§2.4.12, 사용자 승인(2026-10-12 "design 승인")).

#### 2.4.1 상태 층과 graph 밖에 허용되는 것

설계 값은 Circuit State Graph 필드에만 있다. 필드마다 writer 하나와 그 값을 만든 입력 버전이 있다(필드가 곧 캐시, DEC-83). 층은 수명으로 나눈다.

| 층 | 담는 것 | 수명·키 | writer |
|---|---|---|---|
| **S0 수준 층** | S1(구조), S1v(뷰·셀·stage·블록·루프·극점 노드·끊는 점·L 동치류), 결합 변수 y와 기둥↔블록 매핑(GB3), GB4 달성가능성(블록 gain 상한표·곡선 검사·구조 DOF·면적 하한·헤드룸 행·판정·층 0 정의역 상한), 출발 구간(41 §6), metric 구조 입력, 커널 컨텍스트의 구조 파생(θ 스키마·고정 노드·L 묶음, §2.4.7) | 실행마다 스냅샷 하나. 실행 안에서만 재사용하고 디스크에 쓰지 않는다(§2.4.3) | 단계 A의 GB1~GB4·A8·A9 계산 블록(§2.4.8) |
| **단계 B 층** | 결합 잔차 분포 r̂(41 B1), 수치 rank(41 B2) | 실행 수명. S0 수준 스냅샷 위에 쓴다: 표본이 그 실행에서 이미 평가한 점(`residual_probe(pool=)`)에서 오므로 S0만의 함수가 아니다. (v1.10: S0 수준 층도 실행 수명이 되어 '직렬화 제외' 구분은 없어졌다) | `residual_probe`, `dof_numeric`. v1.9.1 D5: U17 ①-b는 필드 자리만 두고, 블록 배선은 소비자(층 0, 41 §5)와 함께 U17 ②에서 한다(근거: 동작 변경 회피 -- ①에서 배선하면 평가 수·탐색 궤적이 바뀌어 base 비교가 안 된다; 소비자 위치) |
| **설계점 층(S2)** | `dc`·`ss`·`ls`·`layout`·수동소자 값·제약 행·목적 분해능. 평가마다 S0 수준 스냅샷 위에 쓴다(구조 공유) | 설계점 스냅샷. 보존 규칙은 §2.4.5 | 평가 커널·봉인·GB5·GB8·MOD7 블록 |
| **층 0 층** | 블록 국소 후보의 커널 결과와 블록 범위 metric, 매크로 풀이 결과, 조립 기록, 회차 기록(41 §5) | 국소·조립 스냅샷. S3 색인으로 찾는다(§2.4.5) | 평가 커널 블록(같은 writer), 층 0 블록(§2.4.8) |

**graph 밖에 허용되는 것은 셋뿐이다**(결정 G-1·G-2'). 이 밖의 저장소는 구조 test가 거부한다(§2.4.10 G-8).

| # | 저장소 | 담을 수 있는 것 | 담을 수 없는 것 |
|---|---|---|---|
| (a) | **LUT memo**(S0당 인스턴스 하나, §2.4.6) | `lut` 패키지의 순수 함수 결과. 디스크 LUT 파생표(tol_V·tol_VDsat·곡선 표 등)와 1변수 근을 포함한다. 디스크 파생표는 실행 사이에 유지한다 -- **유지**(U-87, 사용자 결정 2026-10-15 "U-87은 LUT는 관리복잡도가 없다는 네 판단근거에 따라 유지. 나머지는 기본안대로"): 원래 취지('처음 topology를 실행할 때는 항상 계산')의 **예외**로 기록한다. 근거 = 입력 파일(LUT)의 순수 함수 파생표라 키가 LUT 내용 + LUT 코드 버전으로 완결되고, S0 같은 키 관리 부담이 없다(§2.4.12 Q9) | graph 필드를 읽어 만든 값, 소자 이름을 키로 한 설계 값 |
| (b) | **S3 기록**과 **S3 메모리 색인** | evals·runs jsonl(디스크 -- 출력 기록이고 엔진은 읽지 않는다, v1.10), 평가 요약 + 스냅샷 지문 + 스냅샷 참조, 블록 결과 색인((블록, 분할, 입력 버전) → 그 값을 담은 스냅샷 참조)(메모리, 실행 수명, §2.4.5 v1.11). 실패 캐시는 그 실행에서 평가한 실패를 담은 색인의 보기다 | 요약에 없는 설계 값의 사본 |
| (c) | **실행 계수**(`core/run_counters.py` 하나, §2.4.9) | 호출 수, 시간, 평가 예산 N_T·E_B, 마감, 블록·분할 계수와 그 증거 집합. 실행 수명이고 상한은 실행 평가 수로 정해진다 | 값 캐시 |

**의도적 재계산**(결정 3절)은 둘뿐이다. 계수(§2.4.9)는 이 둘을 따로 센다.
- SPICE 오라클: 독립 검증이므로 엔진 값을 쓰지 않는다(§4).
- FD 스텝: θ가 다르므로 입력 버전이 다르다. 그 성분을 읽는 블록만 계산한다(WP-23 (5)).

**대칭 탐색**(D-2): 자기동형 궤도와 d/s 맞바꿈 검출(사용자 2026-10-12 결정 "6. 가")은 S1 하나에서 한다. 궤도 결과는 S0 수준 필드다. 알고리즘은 §6(대칭)의 몫이다. 다른 브랜치 초안 f786dc6은 병합하지 않고 참고만 한다.

#### 2.4.2 S0 수준 층의 필드

S0 수준 값은 계산 블록(`core.compute_block`)으로 만들고 S0 수준 스냅샷에 쓴다. 블록이 선언한 입력만 읽으므로 같은 실행 안에서 입력 버전이 같으면 다시 계산하지 않는다. 실행마다 처음 한 번 계산한다(§2.4.3).

- 레코드 key: S0 수준 graph 레코드는 개념마다 key 하나다. S1 = `s1`(as-built `graph.GRAPH_KEY`). 신규는 `s1v`, `coupling`, `ach`, `start`, `kernel`이다. 소자별 값은 `device` 레코드의 필드다(필드 이름 접두 `s1v.`·`ach.`·`start.`).
- 값 형식: as-built frozen dataclass(`E/graph/s1v_values.py`의 `ViewS1v`(:379) 등, `E/metrics/achievability_types.py`, `E/search/start_values.py`의 `StartRow`·`StartConflict`·`MacroResult`·`StartRung`)를 필드 값으로 그대로 쓴다. 묶음 객체(`S1v`(`s1v_values.py:485`), `Achievability`(`achievability_types.py:203`), `StartIntervals`(`start_values.py:142`))는 필드 묶음으로 풀고 사본을 두지 않는다. 레코드별 필드 목록은 §2.4.8이다. v1.9.1 D4 정정: 옛 문장은 `Placement`를 `start_values.py`의 값 형식으로 적었으나 as-built `Placement`는 MOD8 레이아웃 재검증 입력(`E/convergence/convergence_values.py:47`)이라 S0 수준 값이 아니다(근거: 소비자 위치 -- MOD8). `graph/start: placement`(41 §6.1-9 출발 θ 생성기 입력)는 그것과 다른 필드이고 U17 ②에서 U15 `placer`와 함께 만든다.
- 읽기: 소비자는 S0 수준 스냅샷의 필드를 읽는다. 컨텍스트 객체에 그 값을 옮겨 담지 않는다(§2.4.7).

#### 2.4.3 S0 수준 층의 수명 -- 실행 안에서만 (v1.10)

사용자 결정 2026-10-15 "나로 해"(원문 `_drafts/user_decisions.md` '실행 사이 재사용 제거'). 근거는 사용자 취지 문장 "계산 재사용은 처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용되게 한다는 것이 원래 취지였어"이다. 옛 결정 G-2'(S0 수준 스냅샷 디스크 영속화, 2026-10-12)와 그것에 딸린 규칙(키 (i)~(iv), 코덱·타입 등록부, 손상 처리, 저장 시점 D6, U-68 정리, 결정 7의 checkout 경로 제거 근거, 결정 10의 checkout 무관 근거)은 폐지했고 옛 문장은 history에 있다.

| 항목 | 규칙 |
|---|---|
| 수명 | S0 수준 층(§2.4.1 표 첫 행)은 실행마다 처음부터 계산한다. 그 실행의 나머지(단계 B, 탐색 컨텍스트, 층 0, 외층)는 같은 스냅샷을 메모리 값으로 받아 재사용한다(필드가 곧 캐시 -- 입력 버전이 같으면 계산 0, §2.4.9 판정 1). 실행이 끝나면 버린다 |
| 디스크 | S0 수준 층을 디스크에 쓰지도 읽지도 않는다. S0 키·스냅샷 코덱·타입 등록부·손상 처리·정리(U-68)를 두지 않는다 |
| 단계 사이 전달 | 단계 A → 단계 B → `build_search_context`는 같은 실행 안에서 S0 수준 스냅샷을 결과 값(`StageAResult`·`StageBResult`의 스냅샷 참조)으로 넘긴다. 단계 A 보고서에 `s0_snapshot` 키를 두지 않는다 |
| S3 | 엔진은 S3 evals·runs를 실행 사이에 읽지 않는다(U-89 확정 (사용자 결정 2026-10-15 "U-87은 LUT는 관리복잡도가 없다는 네 판단근거에 따라 유지. 나머지는 기본안대로", 원문 `_drafts/user_decisions.md` 'U-87~U-89·NFR4-F2·front 조회') -- §2.4.12 Q11). 이전 실행 front 점을 시작점으로 쓰지 않고(as-built `E/search/start_points.py:33-47` `_s3_thetas`), 디스크 실패 기록을 읽지 않는다(as-built `E/search/search_context.py:137-149·234-235` `_disk_failures`, `E/search/kernel.py:105`). S3 jsonl과 `snapshots/`는 결과 기록(출력)으로 계속 쓴다 |
| 실행 사이 재사용 | 설계 값(graph 필드, S3 평가)은 실행 사이에 재사용하지 않는다. 예외 하나: LUT 파생표 디스크 캐시(엔진 `GMID_LUT_TABLE_CACHE_DIR`, test 쪽 `lut_table_cache_tests`)는 **유지**(U-87, 사용자 결정 2026-10-15 "U-87은 LUT는 관리복잡도가 없다는 네 판단근거에 따라 유지. 나머지는 기본안대로"): 원래 취지('처음 topology를 실행할 때는 항상 계산')의 **예외**로 기록한다. 근거 = 입력 파일(LUT)의 순수 함수 파생표라 키가 LUT 내용 + LUT 코드 버전으로 완결되고, S0 같은 키 관리 부담이 없다(§2.4.12 Q9) |
| 엔진 코드 지문 | `engine_code_fp()`(`E/core/engine_code_fp.py`)는 S0 키에서 빠진다. 결과 기록의 출처 칸(S3 줄 `code_fp`, `run_id`, `E/search/find_front.py:138`)으로만 남는다(출력에 어느 코드가 만들었는지 적는 일이라 재사용이 아니다) |
| 블록 코드 해시 | `ComputeBlock.code_hash`(결정 10 방식: 재귀 정규화, 경로·줄 정보 제외, `__wrapped__` 포함)는 실행 안 블록 입력 버전 식(§2.4.4)에 그대로 쓴다. checkout 무관 성질의 근거(다른 checkout이 같은 S0 폴더를 읽는 것)는 사라졌다. 그 성질은 유지한다(U-88, 사용자 결정 2026-10-15 "U-87은 LUT는 관리복잡도가 없다는 네 판단근거에 따라 유지. 나머지는 기본안대로") |
| PDK 선언 값 | 선언 값(`PdkDecl`)은 읽을 때 원본 바이트로 잰 `decl_sha256`을 담는다(`E/core/pdk_decl.py:619`). 출처 기록은 이것으로 충분하다. `run_stage_a`의 키워드 필수 인자 `pdk_decl_path`·`lut_rule_decl_path`와 진입 sha 대조(거부 사유 `pdk_decl_missing`·`pdk_source_sha256_mismatch`)는 U-68 정리의 재료였고 다른 소비자가 없다 → 지운다(아래 목록). 같은 이유로 `run_stage_a`의 값 인자 `pdk_decl`·`lut_rule_decl`도 S0 키에만 쓰였으므로 지운다(사용자 결정 J-1 2026-10-15 "권고대로 진행해", 구현 7e1b4be): 서명 `run_stage_a(topology_path, spec_path, lut, *, output_dir, supplies_v=None, structure_path=None)`. 탐색 준비 `build_search_context`의 같은 이름 인자는 자기 계산에 쓰므로 그대로 둔다 |

**삭제·변경 목록**(2026-10-15 grep, 34932a9 + 이 브랜치 문서 기준 as-built. 코드 변경은 이 결정의 code card 몫 -- 같은 변경에서 옛 코드를 지운다). **완료 규칙**: 아래 이름을 **이름마다 정한 범위**에서 grep(단어 단위)한 결과가 0이 될 때까지 지운다(history·이 design의 '옛' 문장 제외). 범위와 남기는 쓰임은 2026-10-15에 이름마다 `grep -rlw`로 확인했다(델타 검증 B-1).

| 이름 | grep 범위(이 안에서 0) | 범위 밖에 남는 쓰임(지우지 않는다) |
|---|---|---|
| `S0SnapshotStore`, `S0Slot`, `snapshot_codec`, `type_registry`, `KEY_CODE_FP`, `OUTCOME_HIT`·`OUTCOME_MISS`·`OUTCOME_CORRUPT`, `SNAPSHOT_DIR_ENV`, `_CLEANUP_STARTED`, `GMID_S0_SNAPSHOT_DIR`, `_disk_failures`, `load_evals`, `load_runs`, `_s3_thetas`, `STAGE_B_WRITERS` | 엔진 전체(`gmid_engine/` 소스·CONTRACT·`tests/`) | 없음(모든 쓰임이 이 결정의 삭제 대상이다) |
| `disk_failures`, `disk_hits` | 엔진 전체 | 없음. test 쪽 `tests/search/test_find_front.py:19`(`PERF_KEYS`), `tests/search/test_layer0_center.py:345`도 고친다 |
| `s0_snapshot` | 엔진 소스·CONTRACT·`tests/`(아래 픽스처 제외) | `tests/integration/fixtures/u17_1b_s0_baseline.json` `_source` 설명 문자열 -- 기준선 재측정(§2.4.13 (7)) 때 새 설명으로 다시 쓴다 |
| `pdk_decl_path`, `lut_rule_decl_path` | 엔진 전체 | 없음(모든 쓰임이 `run_stage_a` 서명·`pipeline/CONTRACT.md`·그 호출 test) |
| `pdk_decl_missing`, `pdk_source_sha256_mismatch` | `E/pipeline/stage_a.py`, `E/pipeline/CONTRACT.md`, `E/tests/pipeline/test_stage_a.py`(`:710` 주석 포함)만 | **남긴다**: `E/core/pdk_decl.py:340`(원본 파일 sha 대조 -- 선언이 가리키는 PDK 원본 파일의 sha가 선언값과 다르면 거부)·`:592`(선언 파일 없음), `E/core/CONTRACT.md:317·372·376·420`, `E/tests/core/test_pdk_decl.py`(`:535·583·594·626·754·1120·1128·1410`). 이것들은 PDK 선언을 읽는 살아 있는 검사이고 U-68과 무관하다 |

표의 위치는 2026-10-15에 줄마다 grep으로 다시 확인했다.

| 대상 | 위치(as-built) | 처리 | 이유 |
|---|---|---|---|
| S0 스냅샷 코덱·저장소 `S0SnapshotStore`, 손상 처리, U-68 정리(`_CLEANUP_STARTED`, worktree 열거) | `E/core/snapshot_codec.py`(431줄 전체) | 삭제 | 디스크 S0 스냅샷 폐지 |
| S0 키 자리 `S0Slot` | `E/core/s0_slot.py`(36줄 전체) | 삭제 | 같은 이유 |
| 모듈 지도·재수출 | `E/_module_map.py:46·52·53·238·244·247`(`type_registry.py`·`snapshot_codec.py`·`s0_slot.py` 항목), `E/core/__init__.py:30-37·65·73-75·83·84·102`(`S0Slot`·`KEY_CODE_FP`·`OUTCOME_*`·`S0SnapshotStore`·`type_registry` 재수출과 `__all__`), 패키지별 코덱 등록 주석 `E/graph/__init__.py:208`·`E/sizing/__init__.py:163`·`E/metrics/__init__.py:174`·`E/search/__init__.py:102` | 삭제 | 모듈 삭제에 딸림 |
| 계약 문서 | `E/core/CONTRACT.md:4·5`(머리 요약), `:525-579`(§11 S0 영속화 -- §11.1 `type_registry`, §11.3 `S0SnapshotStore`. §11.2 `engine_code_fp`는 용도 변경 문구로 고침), `E/pipeline/CONTRACT.md:5·8·14·45`(`run_stage_a` 서명·키 칸·`s0`), `E/search/CONTRACT.md:7`(`s0` 저장), `:438`(`disk_failures`), `:440·450`(`disk_hits` 계수·디스크 실패 적중 단계), `:473-474`(§3.12 S3 front 점 후보) | 삭제·고침 | 같은 변경에서 계약을 맞춘다 |
| docstring | `E/pipeline/stage_a.py:3·28-32·45·93`, `E/search/search_context.py:11·21-22·29·41·217·226`, `E/search/s0_fields.py:9`(단계 B 층 '직렬화 제외' 설명), `E/graph/s1_build.py:9`(`previous`가 디스크 스냅샷일 수 있다는 문장), `E/search/start_points.py:7`, `E/search/archive.py:8-9` | 고침 | 같은 이유 |
| 타입 등록부 | `E/core/type_registry.py`(63줄), 등록 호출 `E/core/__init__.py:38·46`, `E/graph/__init__.py:6·216`, `E/metrics/__init__.py:8·182`, `E/sizing/__init__.py:8·167`, `E/search/__init__.py:8·106` | 삭제 | 소비자가 코덱뿐이다(`E/core/snapshot_codec.py:59·110·132`) |
| S0 키 입력 만들기 | `E/pipeline/stage_a.py:198-224`(`_s0_inputs`·`_s0_sources`), `:265-268`(`S0Slot` 생성·`load`), 보고서 `s0_snapshot` 칸 `:110·272·279·301`, `StageAResult.s0` | 삭제. `:268`은 `GraphSnapshot.empty(S0_WRITERS)`에서 시작하도록 바꾼다 | 키·읽기 폐지 |
| PDK 선언 경로 인자와 진입 sha 대조 | `E/pipeline/stage_a.py:236`(서명), `:242-248`(대조·거부 2종) | 삭제 | U-68 재료였고 독립 근거 없음: 선언 값이 이미 원본 sha를 담는다(`E/core/pdk_decl.py:619`), 경로를 읽는 소비자는 `_s0_sources`뿐 |
| S0 저장 | `E/search/search_context.py:225-229`(`s0` 인자 검사·`save`), 서명 `:215` `s0=` | 삭제 | 저장 폐지 |
| 직렬화 제외 writer 목록 | `E/search/s0_fields.py:35` `STAGE_B_WRITERS`, 재수출 `E/search/__init__.py:47·130`, 소비 `E/search/search_context.py:41·229` | 삭제(무조건 -- 엔진 소비자는 `save(..., transient)` 하나였다. test `tests/search/test_s0_fields.py:51`·`tests/pipeline/test_stage_a.py`의 단언도 지운다) | 유일한 쓰임이 `save(..., transient)`였다 |
| 환경 변수 `GMID_S0_SNAPSHOT_DIR`, 기본 폴더 `.s0_snapshot/` | `E/core/snapshot_codec.py`(`SNAPSHOT_DIR_ENV`), `.gitignore:39`, `E/tests/conftest.py:52-61` | 삭제 | 폴더가 없다 |
| 디스크 실패 기록 읽기 | `E/search/search_context.py:63·137-149·160·234-235`(`disk_failures`·`_disk_failures`), `:65`(계수 `disk_hits`), `E/search/kernel.py:105·108-112`(디스크 분기 전체 -- `:106-107` 원뿔 행 계산은 남는다) | 삭제 | S3 실행 사이 읽기 제거(Q11) |
| 결과 JSON `perf.disk_hits` | `E/search/find_front.py:13`(docstring)과 `perf`의 `disk_hits` 칸(카운터 `E/search/search_context.py:65`) | 삭제 -- **결과 JSON 형식 변경**(칸 하나가 빠진다) | 계수의 대상이 없다 |
| 이전 실행 front 점 시작점 | `E/search/start_points.py:33-47`(`_s3_thetas`, 출처 "s3") | 삭제 | 같은 이유 |
| S3 읽기 API | `E/search/archive.py:58-78`(`load_evals`·`load_runs`), 모듈 docstring `:8-9`. 딸린 문서·docstring(N-4): `E/search/CONTRACT.md:438`(`disk_failures` 문장), `:473-474`(§3.12 `start_points` 후보 'S3 runs front 점 먼저'), `E/search/start_points.py:7`(docstring), `E/search/search_context.py:21-22`(평가 캐시 docstring의 디스크 실패 캐시 문장) | 삭제(소비자가 위 둘뿐). CONTRACT §3.18(`:529`)의 `S3Archive(root, context_fp, code_fp)` 서명은 바뀌지 않는다(Q-N5 대상 소멸로 `env_fp` 생성자 인자는 없다) | 같은 이유. `append_eval`·`append_run`·`write_snapshot`은 출력이라 유지. `read_snapshot`은 지우고 그 읽기를 `front_query.py`의 비공개 함수로 옮긴다(아래 'front 조회 전용 읽기 경로') |
| front 조회 `node_across_front`의 파일 경로 | `E/search/front_query.py:3·5·30-31·49-57`(`archive=None` 인자로 `archive.read_snapshot`을 부름), `E/search/archive.py:99-102`(`read_snapshot`), 재수출 `E/search/__init__.py:27·190`, 계약 `E/search/CONTRACT.md:172·206·524-525` | **유지**(U-90, 사용자 결정 2026-10-15 "U-87은 LUT는 관리복잡도가 없다는 네 판단근거에 따라 유지. 나머지는 기본안대로"). 규칙은 아래 'front 조회 전용 읽기 경로' | 출력 조회이고 계산 재사용이 아니다. 메모리 `FrontPoint` 경로(실행 안)는 그대로 남는다 |
| 엔진 코드 지문 | `E/core/engine_code_fp.py`, `E/pipeline/stage_a.py:249` | 유지(용도 변경) | S3 줄·`run_id`의 출처 칸 |
| 블록 코드 해시 | `E/core/compute_block.py` `code_hash` | 유지 | 실행 안 입력 버전. checkout 무관 성질은 Q10 |
| 계수 | `perf.s0_snapshot`(계획만, as-built 없음), `regenerated_from_prior_run`(design만) | 삭제 | 대상 없음 |

**front 조회 전용 읽기 경로**(U-90 결정의 구현 규칙, 델타 검증 B-2·B-3. **원래 취지 보호 장치**: 다른 실행의 출력이 계산으로 새지 않게 막는다 -- 사용자 결정 2026-10-15 "나로 해"):

| 항목 | 규칙 |
|---|---|
| 파일 나눔(규칙 A) | 규칙 A(`E/tests/structure/structure_checks.py:198-214` `entry_points`, `:334-336`)는 파일당 독립 공개 진입점 하나를 요구하고 `E/_module_map.py:921`도 `front_query.py`에 진입점 하나를 등록한다. 그래서 읽기 함수는 새 파일 `E/search/front_entries.py`에 둔다(진입점 `read_front_entries` 하나). `front_query.py`는 지금처럼 `node_across_front` 하나다 |
| 읽기 함수 | `read_front_entries(run_dir) -> tuple[dict, ...]`(`E/search/front_entries.py`). `run_dir` = S3 실행 폴더 `<archive_root>/<context_fp>`(= 출력 기록기 `S3Archive.dir`). `runs.jsonl`을 줄 순서대로 읽어 각 줄의 `front`·`pending_front` 항목을 원래 dict 그대로 돌려주고, 항목마다 그 줄의 `run_id`·`code_fp`를 더한다(거르지 않는다 -- 조회 결과를 보는 쪽이 판단한다). 파일이 없으면 `()`. **엔진 소스(`tests/` 제외)에서 `runs.jsonl`을 읽는 곳은 이 함수 하나다.** 이것은 기계적으로 강제하지 않는다(파일 이름 문자열 검사는 쓰기 쪽 `E/search/archive.py`의 `"runs.jsonl"`과 구분이 어려워 두지 않는다) -- 대신 아래 규칙 K가 이 함수와 스냅샷 읽기를 엔진 안에서 부르지 못하게 막고, 리뷰가 '`runs.jsonl` 읽기 = `front_entries.py`만'을 확인한다 |
| 스냅샷 파일 읽기 | `S3Archive.read_snapshot`(`E/search/archive.py:99-102`)을 지운다. 그 읽기는 `E/search/front_query.py`의 비공개 함수 `_read_snapshot_file(path)`(같은 gzip JSON 읽기)로 옮긴다 -- `node_across_front`만 스냅샷을 읽고, 비공개 이름을 파일 밖으로 import하지 않기 위해 `front_entries.py`가 아니라 `front_query.py`에 둔다(검증 지적의 안 (가)와 다른 점, 근거 = 비공개 함수의 파일 밖 사용 회피·규칙 A 진입점 하나 유지). `S3Archive`에는 쓰기(`append_eval`·`append_run`·`write_snapshot`)와 폴더 `.dir`만 남는다 |
| `node_across_front` 서명 | **바꾸지 않는다**(N-7, 사용자 확정 조회): `node_across_front(front, node, archive=None) -> tuple[NodeRow]`. 파일 항목(dict)은 `archive.dir / entry["snapshot_ref"]`를 `_read_snapshot_file`로 읽는다. `archive`가 없으면 지금처럼 `ValueError`. 파일 front 항목을 얻는 쪽은 `read_front_entries(archive.dir)`를 부른다(조회하는 쪽 -- 지금은 test) |
| 재수출 | `E/search/__init__.py:27·190`의 `node_across_front` 재수출은 **유지**하고 `read_front_entries`를 더한다. 규칙 C(`E/tests/structure/structure_checks.py:433-505`)가 다른 패키지에 `from gmid_engine.search import <공개 이름>`만 허락하므로, 금지는 모듈 이름과 함께 공개 이름으로도 건다 |
| 부를 수 있는 곳 | 엔진 안에서는 **없다**. 정의(`search/front_query.py`, `search/front_entries.py`)와 재수출(`search/__init__.py`)만 이름을 가진다. 지금 호출자는 test뿐이다(`E/tests/search/test_front_query.py`, 새 `E/tests/search/test_front_entries.py`) -- 엔진 호출자는 필요 없다. '보고 쪽 조회'(`E/report/`)는 지금 `__init__.py`뿐이라 호출 파일이 없다. 필요해지면 이 표의 허용 목록에 파일을 더하는 design 변경이 먼저다. 'pipeline 단계 실행' = `E/pipeline/` 전부 -- 금지다 |
| 검사 | 새 구조 규칙 **K**(글자 J는 J 공동분석·`test_j_rules_library.py`·41 §5 'J3' 등과 겹쳐 K를 쓴다 -- 2026-10-15 grep `rule_k`·`check_k`·`규칙 K`·`K-a` 0건). `E/tests/structure/structure_checks.py`에 `check_k`, `E/tests/structure/README.md` 규칙 표에 K 행, 위반·허용 픽스처 `E/tests/structure/fixtures/rule_k/{bad,good}/gmid_engine/`, `test_structure_rules.py`와 `test_structure_rules_reject_fixtures.py`에 K. 엔진 소스(`tests/` 제외) 전체를 AST로 훑어, 허용 파일(`search/front_query.py`, `search/front_entries.py`, `search/__init__.py`) 밖에서 다음을 거부한다: (K-a) 이름 `node_across_front`·`read_front_entries`의 참조(import 별칭, `ast.Name`, `ast.Attribute.attr`) (K-b) 모듈 `front_query`·`front_entries`의 import(상대·절대) (K-c) `attr`이 `read_snapshot`·`_read_snapshot_file`인 모든 `ast.Attribute`(호출이 아닌 참조 `f = sctx.archive.read_snapshot` 포함)와 이름 `_read_snapshot_file`. 층 순서상 `sizing`·`metrics`·`graph`·`lut`·`authoring`·`core`는 이미 `search`를 import할 수 없다(규칙 C) -- K는 `search` 안 다른 모듈과 `layout`·`convergence`·`report`·`pipeline`을 잡는다. 위반 픽스처는 K-a·K-b·K-c를 하나씩 담는다(예: `pipeline/run.py`의 `from gmid_engine.search import node_across_front`, `search/start_points.py`의 `from .front_entries import read_front_entries`, `search/kernel.py`의 `reader = sctx.archive.read_snapshot`) |
| 모듈 지도 | `E/_module_map.py`에 `ModuleEntry("search/front_entries.py", "entry", "read_front_entries", "다른 실행의 runs.jsonl front 항목을 읽는 출력 조회 전용 함수(엔진 계산 경로는 부르지 않는다)", ("N3.3", "U-90"))`를 더한다. 규칙 H(`test_structure_test_mapping`)에 맞춰 test 파일 `E/tests/search/test_front_entries.py`를 둔다 |
| 결과의 쓰임 | 읽은 값은 graph 필드·시작점·실패 캐시·S3 메모리 색인에 넣지 않는다(K가 엔진 안 호출 자체를 막으므로 구조로 보장된다) |
| 계약 문서 | `E/search/CONTRACT.md:172`(`S3Archive.read_snapshot` 계약 -- 삭제), `:206`(파일별 진입점 표에 `front_entries.py` | `read_front_entries` 행 추가), `:524-525`(§3.17 `node_across_front`: dict 원소는 `archive.dir`의 스냅샷 파일을 `_read_snapshot_file`로 읽는다, 서명 그대로)와 새 절 `read_front_entries` |

**test 삭제·변경 목록**(2026-10-15 grep `E/tests/`): 삭제 -- `core/test_snapshot_codec.py`, `core/test_s0_slot.py`, `core/test_type_registry.py`, `integration/test_code_hash_checkout.py`(다른 checkout의 S0 적중을 보는 test), `integration/test_s0_layer_9circuits.py`의 두 번째 실행 적중 test(`:326` `test_second_run_hits_s0_snapshot_with_zero_block_computes`)와 S0 폴더 조작(`:56·152·175-190`). 삭제(S3 실행 사이 읽기, N-4) -- `search/test_start_points.py:60-78`(`test_previous_run_front_points_come_first`)와 같은 파일 docstring `:1`, `search/test_kernel.py:147-167`(`test_disk_failure_hit_same_code_and_invalid_when_code_differs`). 변경 -- `search/test_search_context.py:76`(`disk_failures` 칸 단언), `search/test_archive.py:2·71-72`(`read_snapshot` 왕복 단언 → `front_query`의 스냅샷 읽기로 옮김), `search/test_front_query.py:1·75·83`(서명 그대로, dict 항목을 `read_front_entries(archive.dir)`로 얻도록), `search/test_s0_fields.py:51`(`STAGE_B_WRITERS` 단언 삭제), 새 `search/test_front_entries.py`(규칙 H), `conftest.py:52-61`(S0 폴더 고정 삭제), `pipeline/test_stage_a.py`(67곳: `pdk_decl_path`·`lut_rule_decl_path` 인자·`s0_snapshot` 칸·적중 단언), `pipeline/test_stage_a_report.py:38-41·68`(`s0_snapshot` 칸), `pipeline/test_stage_a_loop_cut.py`·`test_stage_b.py`·`integration/test_stage_a_library.py`·`test_stage_b_library.py`·`test_j_rules_library.py`·`test_blas_thread_determinism.py:106`·`generality/pipeline.py`·`search/conftest.py`·`search/test_cell_floor.py`·`search/u13_hand.py`·`search/u13_real.py`·`metrics/gb4_hand.py`·`sizing/test_current_basis.py`·`sizing/test_bracket_root.py`(경로 인자·`s0=`·`code_fp` 호출 형식), 타입 등록부 이름을 읽는 단언 `search/test_start_intervals.py:216-217`·`search/test_constraint_classes.py:81`·`pipeline/test_stage_a.py:885-886`·`pipeline/test_stage_b.py:248-249`(등록부가 없어지므로 그 단언을 지운다), `core/test_engine_code_fp.py`(S0 키 문구만). 개수는 grep 줄 수이고 정확한 변경 범위는 test 작성 주체가 정한다.

**실행 시간 영향**(측정·정적 판단, history H4): S0 디스크 적중 대비 미적중의 9회로 단계 A+B+탐색 컨텍스트 합 차는 402.8 s(회로당 평균 약 45 s)다 -- 같은 회로를 다시 실행할 때 이만큼 늘어난다. test 세션에서 S0 스냅샷을 저장하는 호출은 자기 폴더를 쓰는 두 test(`integration/test_code_hash_checkout.py:73`, `integration/test_s0_layer_9circuits.py:136`)뿐이라 다른 test가 잃는 적중은 0이다. 그래서 test 쪽 보완책은 두지 않는다. 나중에 같은 S0를 여러 test가 다시 계산해 느려지면 pytest 세션 범위 fixture가 메모리에서 한 번 계산해 나눠 주는 방식만 쓴다(프로세스 안, 실행 사이 디스크 캐시가 아니다).

#### 2.4.4 이식(graft) 연산

결정 1절 #1이다. 서로 다른 lineage의 스냅샷에서 **입력 버전이 같은 블록 결과**를 가져오고, 공유량이 닿는 결과만 계산한다. 국소 스냅샷 조회는 S3 색인(§2.4.5)으로 한다.

**v1.11(XRUN-F1, 사용자 결정 X-1 (3))**: 이식은 실행 안 **모든 계산 블록 호출**의 재사용 경로다. 원천은 실행 수명 블록 결과 색인(§2.4.5)이고 계보(parent·lineage)와 무관하다 -- 단계 A부터 탐색 끝까지 같은 실행의 어느 lineage에서 계산한 결과든 같은 (블록, 분할, 입력 버전)이면 가져온다. 분할을 도입하기 전(U17 ② 전)에는 모든 블록의 분할 key가 `*` 하나라 블록 전체 결과를 이식한다(as-built `GraphSnapshot.write(writer, input_version, columns)` 서명 그대로). 층 0 조립(41 §5.5)은 분할 이식의 첫 소비자다(U17 ②).

**분할 계산 블록**(core 확장): as-built 계산 블록은 열 전체를 한 번에 쓰고, 재사용 판정도 블록 이름 하나의 `block_version`으로 한다(`E/core/compute_block.py:73-90`, `E/core/graph_snapshot.py:144-200`). 이 상태로는 국소 결과를 합친 조립점의 투영이 어느 국소 스냅샷과도 같지 않아 이식할 것이 없다. 그래서 블록에 분할을 둔다.
- 선언: `compute_block(name, reads=..., writes=..., partition=<분할 함수>)`. 분할 함수는 S0 수준 필드(S1 기둥·가지, S1v L 동치류, 쓰기 계획)만 읽어 `{분할 key: (쓰는 레코드 key 집합, 읽는 레코드 key 집합, 읽는 θ 성분 집합)}`을 낸다. 분할이 없으면 분할 key는 `*` 하나다(as-built와 같다).
- **분할 key 규칙**:
  1. 기둥 하나에만 덮이는 소자·넷은 그 기둥 id다. 둘 이상의 기둥에 덮이는 소자·넷(공유 소자, 기둥 경계 넷)은 `shared:<기둥 id 정렬>`이다. 덮는 집합은 as-built `size_and_seal_local.covered_sets`(`E/sizing/size_and_seal_local.py:65-85`)와 같은 정의다.
  2. **SCC를 쪼개지 않는다**: 블록 내부 의존 그래프(같은 블록이 쓰는 행 → 그 행을 읽는 같은 블록의 행)의 강연결 성분이 두 분할에 걸치면 그 분할들을 하나로 합친다. 합친 분할의 key는 합친 기둥 id들로 만든 `shared:<…>`다. 예: 기둥 둘에 걸친 W2 순환 블록(as-built `dc_columns`의 SCC 고정점)은 한 분할이다.
  3. **θ 성분 배정**: θ 성분은 그 성분이 정하는 행이 속한 분할에 배정한다. 여러 분할의 행을 정하는 성분(블록을 가로지르는 L 동치류의 L, 결합 변수 y, 공유 전류)은 그 분할들을 덮는 `shared:<…>` 분할에 배정한다. 블록을 가로지르는 L 동치류의 멤버 소자 행도 같은 `shared:` 분할로 간다.
  4. **실행 순서**: 분할 사이 의존(한 분할이 쓴 행을 다른 분할이 읽음)은 SCC를 합친 뒤 DAG다. 분할은 이 DAG의 위상 순서(같은 순위는 분할 key 정렬)로 판정·계산한다.
- 입력 버전: 분할마다 `fp_of((name, 코드 해시, 그 분할의 투영 지문))`. 기록은 `block_versions[(writer, 분할 key)]`다.
- **투영 지문 = 값 기반 정준 사상**(design-validator N1): 분할이 읽는 모든 양을 `{(kind, key, field): value_fp}` 하나로 모은 정준 사상(키 정렬)의 지문 + 그 분할에 배정된 θ 성분 + 나머지 extras다. writer·input_version·쓰기 횟수는 넣지 않는다. 그래서 같은 양이 스냅샷 행에서 오든(조립점: 이웃 분할이 쓴 행) 국소 봉인의 `fixed` extras에서 오든(국소 후보: 이웃 값을 고정 입력으로 받음) 같은 값이면 같은 지문이다. 이것이 국소 스냅샷 → 조립점 이식이 맞는 조건이다.
- **`fixed`는 extras로만 넘긴다**: 국소 봉인(41 §5.3.9)은 `fixed` 값을 graph 행으로 쓰지 않는다(그 행의 writer는 다른 분할·블록이다). 분할 블록은 읽는 양을 투영에서 찾고, 행에 없으면 `fixed` extras의 같은 (kind, key, field) 칸에서 읽는다. 둘 다 있으면 호출 계약 위반(`ValueError`)이다.
- **이식이 비트 동일인 전제**(v1.11: 분할 블록만이 아니라 `*` 블록을 포함한 **모든 계산 블록의 의무**): 블록은 투영(선언한 열 + extras) 밖의 어떤 입력도 읽지 않는다. 반복 풀이의 초기값도 투영의 함수다. 직전 스냅샷(S2p)·parent·이전 반복의 값을 시드로 쓰지 않는다. as-built 블록은 모두 이 전제를 만족한다: 블록 함수의 인자는 `Projection` 하나이고(`E/core/compute_block.py:12-13`), extras는 투영 지문에 들어가며(`E/core/projection.py:8-11`), 평가 커널의 `parent`는 같은 lineage 재사용에만 쓰인다(`E/sizing/kernel_run.py:6`). 그래서 `*` 블록도 이식 대상이다(옛 문장 '시드가 필요한 블록은 `*` 하나로 남는다(이식 대상 아님)'은 삭제 -- 그런 블록은 없다). 시드가 필요한 블록을 새로 만들 때는 그 시드를 extras로 넘겨 입력 버전에 넣어야 하고, 넣지 못하면 계산 블록으로 만들지 않는다. **fail-closed**: 구조 test가 블록 함수의 인자가 `Projection` 하나뿐인지 확인하고(as-built 규칙 그대로) 규칙 G가 모듈 수준 상태를 막는다. 실행 중에 같은 (블록, 분할, 입력 버전)에서 성공과 예외가 섞이면 전제 위반이므로 `RunCounters`가 그 결과를 기록하는 순간 `ValueError`를 낸다(§2.4.9 '실패 재계산').
- 쓰기: graph setter 서명을 `GraphSnapshot.write(name, part, input_version, rows)`로 바꾼다. `rows` = `{(kind, field): {key: value}}`이고 key는 그 분할의 쓰는 레코드 key 집합과 정확히 같아야 한다(다르면 `ValueError`). 분할 밖 행은 건드리지 않는다. `block_version(name, part)`가 `input_version`이 된다. 분할 없는 블록은 `part = "*"`이고 동작은 as-built `write`와 같다. 한 블록의 분할들은 서로 다른 행을 쓰므로 writer 하나 규칙(SC-a)은 그대로다.
- 대상: 평가 커널 ②~⑤와 봉인 항목 블록, 층 0 블록 범위 metric, GB5 수동소자 블록 `passive_values`(§2.4.8 `device: passive_value`. 읽는 레코드 = 영점 상쇄 셀 소자의 `dc_gm`. 분할이 없으면 전류 θ만 바뀐 자식에서도 블록 전체가 다시 계산되므로 이 분할로 해소한다 -- U17 ①-c 재검증 기록, **U17 단계 ②로 이월**). 분할이 정의되지 않는 블록(전회로 MNA, 전역 metric)은 `*`이다.

**API**(`E/core/graft.py`·`E/core/donors.py`, 신규. v1.11: 규칙 A(파일당 진입점 하나)에 맞춰 `graft`와 `Donors`를 두 파일로 나눈다 -- `graft`는 `Donors`를 이름으로 참조하지 않아 한 파일에 두면 진입점이 둘이 된다):

```python
def graft(target: GraphSnapshot, block: ComputeBlock, part: str, donor: GraphSnapshot, input_version: str) -> GraphSnapshot
# v1.11 card B 보완(card B J-2, 오케스트레이터 기본안): input_version = 호출 규칙이 target 위에서 이미 잰 그 분할 입력 버전
# (`block.input_version(target, *extras)` -- 아래 '입력 버전 정본'). graft 는 투영을 다시 만들지 않는다(같은 입력 두 번 투영 금지,
# extras 를 받지 않는 서명으로도 성립). donor.block_version(block.name, part) == input_version 일 때만 donor 의 그 분할 행(block.writes 열)을
# target.write(block.name, part, input_version, 그 행) 로 쓴다. 다르면 ValueError(호출 계약 위반 -- 판정은 아래 호출 규칙이 먼저 한다).
# 분할 도입(U17 ②) 전: part 는 "*" 만 받는다(아니면 ValueError). 쓰기·읽기는 as-built 서명 그대로 -- block_version(block.name),
# write(block.name, input_version, 그 행) (§11 U17 ② 행: 분할 서명은 ②).

class Donors(abc.ABC):          # core/donors.py. v1.11: 추상 기반(구현 = search `S3Index`, §2.4.5). 옛 `Protocol` 대체
    def find(self, writer: str, part: str, input_version: str) -> GraphSnapshot | None: ...
    def register(self, writer: str, part: str, input_version: str, snapshot: GraphSnapshot) -> None: ...
    def find_failure(self, writer: str, part: str, input_version: str) -> FailureRecord | None: ...
    def register_failure(self, writer: str, part: str, input_version: str, record: FailureRecord) -> None: ...
# v1.11 card B 보완(card B J-5, 오케스트레이터 기본안): 네 메서드 모두 추상(abc.abstractmethod). 근거: 호출 규칙 3·'실패 재연'이
# donors.find_failure·register_failure 를 부르고, ComputeBlock 이 확인하는 형식은 `Donors` 하위뿐이므로 기반 계약에 있어야 fail-closed 가
# 성립한다(하위가 메서드를 빠뜨리면 생성 때 TypeError). Donors 는 상태·생성자 인자가 없다.

# 입력 버전 정본(v1.11 card B 보완 card B J-11, 오케스트레이터 기본안): ComputeBlock.input_version(snapshot, *extras) -> str
# = fp_of((name, code_hash, Projection.from_snapshot(snapshot, reads, extras).fp)) -- 식 그대로(as-built `E/core/compute_block.py:136-137`).
# __call__ 과 봉인 4(`E/sizing/seal_versions.py:20-21` 의 같은 식 사본)가 이 메서드를 부르고 사본은 지운다(레지스트리 §0 규칙 4).
# extras 불변 검사(TypeError)는 이 메서드 안 투영에서 한 번(as-built 와 같다).
# (검증 N-2) __call__ 은 같은 파일의 비공개 helper 하나로 (투영, 입력 버전)을 한 번만 만들어 판정 1~3 과 블록 함수 호출에 함께 쓴다
# (투영을 두 번 만들지 않는다). 공개 input_version() 은 그 helper 를 쓰는 바깥 호출자(봉인 4, test)용이고, graft 는 호출 규칙이 넘긴 값을 받는다.
# (검증 N-8) fail-closed (2)(이식 원천의 block_version ≠ 요청 입력 버전)의 검사 주체는 graft 하나다 -- 호출 규칙 2 는 따로 비교하지 않고
# graft 가 내는 ValueError 를 그대로 올린다. 확인 test = test_graft.py(버전이 다른 donor -> ValueError)와 test_compute_block.py(가짜 Donors 가
# 버전이 다른 스냅샷을 줄 때 블록 호출이 ValueError, 블록 함수 호출 0).

# ComputeBlock.__call__(snapshot, *extras, donors: Donors, counters: RunCounters)
# v1.11: 두 키워드 모두 필수(옛 `donors=None` 기본값 폐지 -- 색인을 거치지 않는 호출 경로가 없어야 계보 무관 재사용이 성립한다. 사용자 결정 X-7).
# 빠지면 TypeError, `donors` 가 Donors 하위가 아니면 TypeError(fail-closed).
```

**호출 규칙**(v1.11 갱신): 계산 블록은 분할마다 위상 순서로 다음을 판정한다.
1. 같은 lineage 재사용: `snapshot.block_version(name, part)`가 입력 버전과 같으면 아무것도 하지 않는다(as-built와 같다). 계수 `reuse`.
2. 이식: `donors.find(name, part, 입력 버전)`가 스냅샷을 주면 `graft(snapshot, block, part, 그 스냅샷, 입력 버전)`으로 그 행을 가져온다. 계수 `graft`. 받은 스냅샷의 그 블록(분할) `block_version`이 입력 버전과 다르면 `ValueError`(색인 손상, fail-closed -- 검사는 `graft`가 한다, 위 N-8).
3. 계산: 셋 다 아니면 그 분할만 계산한다. 계수 `compute`는 블록 함수를 부르기 **전에** 센다(예외로 끝난 계산도 계산이다). 성공하면 결과를 쓴 스냅샷을 `donors.register(name, part, 입력 버전, 그 스냅샷)`으로 한 번 등록하고 `counters.result(block, part, 입력 버전, ok=True)`를 알린다. **결정적 도메인 실패**(core `failure_errors`의 N3.14 분류 예외 -- `InfeasibleSizingError` 하위와 `SchemaRejectedError`, 그 `.record`는 불변 `FailureRecord`)로 끝나면 그 실패 기록을 `donors.register_failure(name, part, 입력 버전, record)`로 등록하고 `counters.result(..., ok=False)`를 알린 뒤 예외를 그대로 올린다(사용자 결정 X-9, Q13 닫힘). 그 밖의 예외(호출 계약 위반 `ValueError`·`TypeError`, 예산·벽시계 중단, `MemoryError`, `KeyboardInterrupt` 등 입력의 함수가 아닌 것)는 등록하지 않고 알리지도 않고 그대로 올린다. 판정 순서: `InfeasibleSizingError`가 `ValueError` 하위이므로(`E/core/failure_errors.py:20`) 먼저 N3.14 분류 예외인지 `isinstance`로 판정하고(맞으면 등록), 그 밖의 `ValueError`는 등록하지 않는다.
   - 실패 재연(호출 규칙 2 다음, v1.11 X-9): `donors.find_failure(name, part, 입력 버전)`가 실패 기록을 주면 블록을 부르지 않고 그 기록의 분류 예외를 다시 던진다 -- `FAILURE_CLASSES[record.failure_class].exc.from_record(record)`(core 신규 classmethod, 새 예외의 `.record`는 등록된 같은 객체 -- 비트 동일). 계수 `replay`. v1.11 card B 보완(card B J-3, 오케스트레이터 기본안): `from_record`는 두 기반 `InfeasibleSizingError`와 `SchemaRejectedError` 모두에 둔다 -- 결정적 도메인 실패 정의(위 3)가 둘을 함께 등록하므로 재연도 둘 다 되어야 한다(`SchemaRejectedError`는 `Exception` 직접 하위라 `InfeasibleSizingError`에서 물려받지 못한다, `E/core/failure_errors.py:20·60`). `from_` 접두 classmethod라 `failure_errors.py`의 규칙 A 데이터 선언 모듈 판정은 그대로다(`E/tests/structure/structure_checks.py:241-249` `_data_method_ok`). 분류 키가 `exc` 없는 후보 실패 레코드 행(`structure_inconsistent`·`local_infeasible`, `E/core/failure_classes.py`)이면 예외로 던져진 적이 없어 등록되지 않으므로 재연 대상이 아니다 -- 그런 기록이 오면 `ValueError`(색인 손상). 판정 순서는 1 같은 lineage → 2 이식 → 실패 재연 → 3 계산이다.

공유량(공유 소자, 결합 변수 y, 블록을 가로지르는 L 동치류, 기둥 경계 넷)이 바뀐 분할은 투영이 달라져 입력 버전이 어느 원천과도 맞지 않는다. 그래서 '공유량이 닿는 필드만 계산'은 별도 규칙 없이 위 판정에서 나온다. 앞 분할이 계산되어 값이 바뀌면 그 행을 읽는 뒤 분할의 투영도 바뀌어 계산된다(위상 순서라 판정 시점에 입력이 확정되어 있다).

**불변식과 결정론**:
- 이식한 행은 계산한 행과 값이 같다. 블록은 투영만의 순수 함수이므로(위 전제) 같은 입력 버전이면 같은 값이다. test: 같은 θ를 (가) 빈 lineage에서 전부 계산, (나) 국소 스냅샷들에서 이식한 두 결과의 스냅샷 `fp`와 모든 필드 `value_fp`가 같다.
- **원천은 키마다 하나**(v1.11): 블록 결과 색인은 (블록, 분할, 입력 버전)마다 처음 계산한 결과 스냅샷 하나만 갖는다(호출 규칙 3에서만 등록, 재사용·이식은 등록하지 않음, 같은 키 재등록은 `ValueError`). 그래서 원천을 고르는 규칙이 필요 없다(옛 '원천이 여럿이면 seq 최소·원천 순서 섞기 test'는 history). test `test_index_single_source`.
- 봉인 4(버전 일치, `E/sizing/seal_versions.py`)와의 관계: `graft`는 이식한 행을 요청 입력 버전으로 쓰므로 그 행의 `FieldValue.input_version` = `block_version`이고, 봉인 4가 다시 잰 입력 버전과도 같다(계산한 행과 같은 판정).
- writer 권한: `graft`는 `GraphSnapshot.write`(graph setter)만 쓴다. 새 쓰기 경로가 없으므로 SC-a·SC-b 검사가 그대로 적용된다.
- 계수: 블록 계수에 `grafts`를 더한다. `calls = reuses + grafts + computes`(§2.4.9. v1.11: 실패 재연 `replays`를 더해 `calls = reuses + grafts + replays + computes` -- X-9).

#### 2.4.5 S3 메모리 색인과 스냅샷 보존 (v1.11 블록 결과 색인·실행 수명 보존)

결정 1절 #2와 G-5다. as-built `sctx.cache`(`{EvalKey: EvalResult}`, `E/search/search_context.py:58`), `computed_keys`(:59; 실패 캐시 `disk_failures`는 v1.10 실행 사이 재사용 제거로 삭제됨, 구현 7e1b4be)를 색인 하나로 바꾼다(줄 번호 master `b9af2d6f` 재측정, v1.12 -- 단일 정본 감사 F4; 옛 인용 `local_seal_memo`(옛 :88)는 엔진 소스에서 이미 없어졌다 -- `git grep -w local_seal_memo` 엔진 0). 오케스트레이터 초안 EvalCache(MOD6)와 `local_seal_memo`는 철회한다(G-5).

**색인 항목**(`E/search/s3_index.py`, 신규) = S3 evals 한 줄과 같은 내용 + 메모리 전용 칸:
- S3 줄 내용: 평가 키, seq, θ, 상태, 실패 레코드, 목적 값(전력·면적·b_P), 제약 행(c, active), 미측정, 경고, origin(단계·시작점·층 0 블록 키·기둥·bin·회차), `snapshot_fp`. 이 값들은 스냅샷 필드에서 한 번 읽어 쓴다(writer = S3 기록기). 설계 값의 새 정본이 아니다.
- 메모리 전용: 분할 입력 버전 표 `{(writer, 분할 key): 입력 버전}`, 스냅샷 참조(v1.11: 늘 -- 실행 수명 보존. 옛 '보존 중이면'·'보존 소유자 집합'은 폐지).

**블록 결과 색인**(v1.11, 사용자 결정 2026-10-15 "권고대로 진행해" X-1 (3), 원문 `_drafts/user_decisions.md` 'XRUN-F1 design 착수 결정'). 실행 안 같은 입력 재사용을 계보와 무관하게 만드는 S3 메모리 색인의 한 부분이다. §2.4.4 `Donors`의 구현이다.

| 항목 | 규칙 |
|---|---|
| 키 | (블록 이름(= writer), 분할 key, 입력 버전). 입력 버전은 §2.4.4 식 그대로(`fp_of((name, 코드 해시, 투영 지문))`, 비트 지문 -- §2.4.13 (6)). 분할 도입(U17 ②) 전에는 분할 key `*` 하나 |
| 값 | 그 블록이 그 입력 버전으로 계산해 쓴 결과 스냅샷(`GraphSnapshot`)의 **참조**. 값 사본을 두지 않는다(DEC-83 graph 단일 정본): 이식(`graft`)은 원천 스냅샷의 필드 값 객체를 graph setter(`GraphSnapshot.write`)로 대상 lineage에 쓴다. 또는(사용자 결정 X-9) 결정적 도메인 실패로 끝난 키의 **실패 기록**(불변 `FailureRecord`, `fp_of`로 지문 가능). 실패 기록은 설계 값이 아니라 '그 입력에서 이 블록은 이 분류로 실패한다'는 판정 기록이고 graph 필드가 아니다 -- graph 밖 (b) S3 색인의 실패 캐시와 같은 종류다(§2.4.1) |
| 등록 | 계산 블록이 그 (블록, 분할)을 계산해 쓴 직후 한 번(§2.4.4 호출 규칙 3). 결정적 도메인 실패면 실패 기록을 한 번 등록한다(X-9). 재사용·이식·실패 재연은 등록하지 않는다. 입력과 무관한 예외는 등록하지 않는다 |
| 조회 | 모든 계산 블록 호출이 같은 lineage 재사용 다음에 `find`로 찾는다(§2.4.4 호출 규칙 2). parent 유무·lineage와 무관하다 |
| 수명 | 실행 하나(사용자 결정 X-12: 단계 A부터 -- S1·S1v 블록 포함). 실행 경계에서 `RunCounters`(§2.4.9)와 함께 새로 만들고, 그 실행의 모든 블록 호출에 같은 객체를 넘기며, 실행이 끝나면 버린다. v1.11 card B 보완(PD-8, offset-strategy 계획 v0.6.2 사용자 승인 S-8): 실행 경계 = **두 객체를 만드는 호출자**다 -- `run_stage_a`는 만들지 않고 받는다(아래 '전달'). 만드는 쪽은 card B 시점에 단계 A → B → 커널 컨텍스트 → 탐색 컨텍스트 → `find_front` 사슬을 잇는 하네스·test이고(엔진 소스에 이 사슬의 제품 진입이 아직 없다 -- `run_stage_a` 엔진 내 호출 0), 그 뒤에는 offset-strategy OS-2의 실행 계획 세션이 만든다(그 문구 개정은 offset-strategy XS-7(승인 S-5), card B 범위 밖). **실행 사이 비공유는 구조 규칙으로 막는다**(사용자 결정 2026-10-16 "권고대로 구조로 막는 방향으로 진행해", 우려 원문 "원래 취지와 다른 실행에 색인을 넘기는 문제가 이전에 폐기했던 아주 큰 hash코드 redundancy를 다시 만드는 것이 아닌지 걱정돼." -- PD-8로 생성 자리가 엔진 밖 호출자로 옮겨 생긴 빈틈을 닫는다. 경위는 계획 history): (1) **단일 생성 함수**: 두 객체는 `open_run() -> (donors, counters)`로만 만든다(새 파일 `E/search/open_run.py`, 진입점 하나. 자리는 search -- `S3Index`가 search에 있고 규칙 C 층 순서상 core는 search를 import할 수 없다). 반환 = 새 `S3Index`와 새 `RunCounters`의 쌍. `S3Index`·`RunCounters`의 생성자는 비공개 계약이다: 정의 모듈과 `open_run.py` 밖에서 `S3Index(...)`·`RunCounters(...)`를 부르지 않는다(아래 (2)가 검사). card C·OS-5가 생성자에 필수 인자를 더하면 `open_run`이 같은 필수 인자를 받아 넘긴다(기본값 없음, PD-7 원칙 그대로). (2) **구조 test 규칙 M**(규칙 K식 AST 정적 검사, `E/tests/structure/structure_checks.py` `check_m`, 픽스처 `E/tests/structure/fixtures/rule_m/{bad,good}/`, 2f684d6 grep `rule_m`·`check_m`·`규칙 M` 0건 -- 글자 L은 '규칙 L2'·`test_lut_rule_l_…`과 겹쳐 쓰지 않는다): (M-a) 엔진 소스(`tests/` 제외)에서 `open_run` 참조는 정의·재수출(`search/open_run.py`, `search/__init__.py`)과 허용 목록 파일뿐이다 -- card B의 엔진 소스 허용 목록은 **비어 있다**(엔진 안 사슬 진입이 없다), OS-2가 실행 계획 세션 열기 파일 하나를 더한다(design 변경으로만). (M-b) `S3Index(`·`RunCounters(` 생성 호출은 그 정의 모듈과 `open_run.py`에만. (M-c) **`run_stage_a` 호출 지점과 `open_run` 1:1 동반**(엔진 소스·test·하네스 모두, 마지막 재확인 차단 반영 -- 옛 'fixture 하나·호출 횟수' 규칙과 M-e를 이것으로 대체): `run_stage_a` 호출의 `donors`·`counters` 인자는 같은 함수 본문에서 `open_run()`의 튜플 풀기(`donors, counters = open_run()`)로 대입된 두 이름이고, **`open_run()` 대입 문장 하나는 그 함수 안 `run_stage_a` 호출 하나의 인자에만 닿는다**(두 이름 = 같은 `open_run()` 대입 문장의 첫째·둘째 이름. 판정 단위 = `open_run()` 튜플 풀기 대입 문장. v1.11.1 문언 정정, 사용자 결정 O-17 (1) 2026-10-19 "card B 1~3 권고대로" -- 취지 '`run_stage_a` 호출마다 `open_run` 1:1'이 정본이고 옛 문언 '그 이름은 … 호출 하나에만'은 이 뜻으로 읽는다. 원래 취지와 같음. 같은 이름에 새 `open_run()` 튜플 풀기를 **다시 대입**해 다음 `run_stage_a` 호출에 쓰는 꼴은 대입마다 호출 하나라 허용이다. 호출이 쓰는 대입 = 그 호출을 구조적으로 앞서는(같은 문장 목록 또는 바깥 문장 목록에서 앞선) 같은 이름 대입 중 마지막 것. 대입 하나가 `run_stage_a` 호출 둘 이상의 인자가 되면 위반)(최종 확인 반영: 쌍은 키워드 두 개로 나눠 넘겨야 하므로 호출식 안에서 바로 넘기는 꼴은 `**` 묶음뿐이고, 그것은 아래 판정으로 위반이다). 그 이름이 `open_run()` 튜플 풀기 말고 다른 방식(매개변수·`for` 대상·다른 대입)으로도 묶이면 위반이다. 호출을 구조적으로 앞서는 같은 이름 `open_run()` 대입이 없으면 위반이다. **해석(원문보다 엄격한 안전 쪽, 사용자 결정 O-17 (2))**: `if`/`else`·`with`·`try`·`match` 가지 안이나 반복문 본문 안의 대입은 그 밖의 호출을 앞서는 것으로 치지 않는다. 앞서는 대입이 있으면 그 가운데 마지막 것이 호출이 쓰는 대입이다. **판정은 fail-closed**: 바깥 함수에서 대입된 쌍을 안쪽 `def`·`lambda`에서 `run_stage_a`에 쓰면(자유 변수) 위반, 리스트·집합·사전 내포식과 generator 식은 반복문 본문으로 본다(그 안의 `run_stage_a`에는 같은 내포식 안 `open_run`이 필요 -- 사실상 위반), `run_stage_a(**kw)`·`run_stage_a(*args)`처럼 `donors`·`counters`의 출처를 AST로 알 수 없는 묶음 인자는 위반이다. `run_stage_a` 호출이 반복문 본문 안이면 그 `open_run()`도 같은 가장 안쪽 반복문 본문(내포식·generator 식 포함) 안이어야 한다. 함수 매개변수·속성·결과 칸(`StageAResult`·`KernelContext`·`sctx.dc` 등)·다른 호출의 반환에서 온 `donors`·`counters`를 `run_stage_a`에 넘기면 위반이다 -- 그래서 `run_stage_a`를 부르는 helper는 스스로 `open_run`을 부른다(쌍을 매개변수로 받지 않는다). 예외 = 실행 계획 세션 열기 파일(OS-2 design이 M-a 허용과 함께 더한다 -- 같은 실행 계획 안 변형 공유는 그 파일 안에서만). test에서 `open_run` 직접 호출은 허용한다(fixture 하나 강제 없음): 결정성·비교 test가 한 함수 안에서 `run_stage_a`를 여러 번 부르는 것은 호출마다 자기 `open_run()`을 동반하면 그대로 성립한다(실측 b0077a8·2f684d6: 한 test 함수 안 `run_stage_a` 2회 이상 = `tests/integration/test_stage_a_library.py` `test_stage_a_library_circuit`(2)·`test_structure_json_declared_comparison`(3), `tests/integration/test_j_rules_library.py` `test_pilot_stage_a_with_spec_has_no_unmatched_cut`(2), `tests/pipeline/test_stage_a.py` 다섯 함수(각 2) -- 모두 이 규칙으로 유지된다). `run_stage_a` 결과 이후 단계(`run_stage_b`·`build_kernel_context`·`build_search_context`)가 그 실행의 결과 칸에서 두 객체를 꺼내 쓰는 것은 같은 실행 안이라 허용이다(대상은 `run_stage_a` 인자뿐). **범위 한정**(최종 확인 반영): 1:1 규칙은 `run_stage_a` 인자에만 건다. `build_s1`·`build_s1v`·`build_kernel_context`·`seal_dc`·`run_layout`·`place_layout`·`ComputeBlock.__call__`을 직접 부르는 단위 test는 '실행 = test 함수 하나'로 본다(그 함수 안에서 `open_run()`으로 얻은 쌍을 여러 호출에 넘겨도 된다 -- 잘못 공유해도 피해는 그 test의 계수 단언에 국한되고 제품 경로와 무관하다. 엔진 소스에서 이 함수들은 `run_stage_a` 결과의 두 객체만 받는다 -- 위 '전달'). 보관 금지(M-d)·직접 생성 금지(M-b)는 단위 test에도 그대로 건다. (M-d) `open_run` 결과(또는 그 두 객체)를 보관하는 길을 막는다(규칙 G와 같은 뜻 -- 두 실행 경계로 넘어가는 길을 없앤다): 모듈 수준 이름, 클래스 속성, session·module·package 범위 fixture, 함수 기본 인자값, `functools.lru_cache`·`functools.cache`(데코레이터·호출형)를 씌운 함수의 반환, 모듈 수준 컨테이너 변경(`append`·`extend`·`add`·`update`·`setdefault`·항목 대입), conftest의 `pytest_configure`와 `request.config`·`config.cache`·`config.stash`에 넣기, 수명이 test 하나보다 긴 객체의 인스턴스 속성 대입(`self.<a> = open_run()` 등 -- 함수 지역·반환은 허용). 위반 픽스처 `rule_m/bad/`에 경로마다 하나. (M-e는 M-c에 흡수되어 없다 -- 글자는 비워 둔다.) (M-f) **디스크 저장 금지 검사**: `S3Index`·`RunCounters` 객체 또는 그 내부 칸(이름이 `_`로 시작하는 속성 접근 포함)이 `pickle`·`json`·`shelve`·`marshal`의 쓰기 함수(`dump`·`dumps`·`Shelf` 항목 대입 등) 인자에 나타나면 위반이다(엔진 소스·test 모두, 위반 픽스처 하나씩). 아래 (4)의 구조 검사다. (3) **색인 키는 (블록, 분할, 입력 판)뿐이다**: 입력 판 = §2.4.4 입력 버전 식(블록 이름·블록 코드 해시·투영 지문) 그대로다. 엔진 코드 지문 `code_fp`, 실행 환경 지문 `env_fp`, spec 지문, `context_fp`, `run_id` 등 실행 바깥 지문을 키에 더하지 않는다 -- 그런 키는 실행 사이 재사용을 전제로 한 옛 S0 키(§2.4.3에서 폐지)의 재도입이다. 실행 사이 재사용은 새 사용자 결정 사항이다. (4) **색인은 디스크에 쓰지 않는다**: 실행 사이 재사용 제거 결정(§2.4.3, card 1)을 그대로 유지한다. 색인 내용(스냅샷 참조·실패 기록)을 파일·환경 변수 경로로 내보내거나 읽는 코드를 두지 않는다(S3 jsonl·`snapshots/`는 출력 기록이고 엔진은 읽지 않는다 -- §2.4.3 'S3' 행 그대로). 모듈·프로세스 수준에 두지 않는다(규칙 G). 실행 사이에 넘기지 않는다(§2.4.3 -- 원래 취지 '처음 topology를 실행할 때는 항상 계산') |
| 전달 | v1.11 card B 보완(PD-8): 호출자가 `open_run()`(위 '수명' (1))으로 만든 `donors`·`counters`를 `run_stage_a`가 **필수 키워드**로 받는다(만들지 않는다, 빠지면 `TypeError`): `run_stage_a(topology_path, spec_path, lut, *, output_dir, donors, counters, supplies_v=None, structure_path=None)`. 서명은 card B에서 한 번만 바꾼다(PD-8 (ii) -- OS-2는 같은 서명을 쓴다). 단계 A는 받은 두 객체를 `build_s1`·`build_s1v` 등 자기가 부르는 블록에 넘기고 단계 결과(`StageAResult`)에 참조로 싣는다(정지 경로 결과 포함 -- 넘긴 객체 그대로). 단계 B(`run_stage_b`, 서명 불변)는 `StageAResult`의 두 칸을 쓴다. 두 객체를 받는 감쌈 함수의 서명(오케스트레이터 기본안 card B J-4, 근거 = 사용자 결정 X-7 '기본값 None 폐지'와 PD-7 '기본값 인자로 피하지 않는다'의 같은 원칙): `build_s1`·`build_s1v`·`build_kernel_context`·`seal_dc`·`run_layout`·`place_layout`은 키워드 `donors`·`counters`를 기본값 없이 필수로 받는다. `KernelContext`·`sctx`를 받는 함수(`size_and_seal`·`size_and_seal_local`·`run_kernel`·`ss_evaluate`·`evaluate`·`build_search_context`·`find_front`·`converge_point`)는 서명을 바꾸지 않고 거기서 꺼낸다(`converge_point`는 `sctx.dc`에서 꺼내 `place_layout`에 넘긴다). 단계 B의 `build_kernel_context`가 받아 `KernelContext`의 참조 칸 `donors`·`counters`에 둔다(§2.4.7). `StageAResult`·`KernelContext`의 이 칸은 **과도기 칸**이다(사용자 결정 X-13 -- U17 ② G-7 재작성에서 정리). 그 뒤의 블록 호출(탐색 컨텍스트의 S0 블록, 평가 커널 ②~⑤·봉인·GB5·`metrics_dc`·`ss_evaluate`, MOD7 레이아웃 블록)은 `KernelContext`에서 꺼내 넘긴다 |
| 상한 | §2.4.9 증거 집합 식 '블록·분할별 계산한 입력 버전 ≤ Σ_블록 분할 수 × (E_total + 1)'(사용자 결정 X-1 (3) -- 새 상수 없음). 키 집합은 그 증거 집합의 부분집합이다(계산한 키 -- 성공 스냅샷 + 결정적 실패 기록). 퇴출하지 않는다(퇴출하면 같은 입력 재계산이 생겨 §2.4.9 판정 1을 깬다). 식의 전제(실행의 커널 평가 수 ≤ E_total)는 as-built에서 성립하지 않는다(history H4: 선언 E_B 40에서 커널 평가 43·49·64·66, 블록별 서로 다른 입력 버전 최대 63 -- 외층 FD 한 묶음과 감도 게이트가 예산 검사 없이 돈다). **사용자 결정 X-8**(Q12 닫힘 = (나)): 모든 커널 평가를 E_total에 넣어 전제를 구조로 성립시키고(card C, §2.4.14 (5)), 그 결과로 색인 상한이 성립한다. card C 병합 뒤에는 등록할 때 항목 수가 식의 값을 넘으면 fail-closed(아래 (5)). card C 병합 전(card B까지)은 실행 끝 항목 수와 식의 값을 보고만 한다. 실패 기록 항목도 같은 키 집합에 들어 같은 식으로 센다. 결과 JSON 키: `perf.block_index_entries`(실행 끝 항목 수), `perf.block_index_bound`(식의 값 = (그 실행에서 불린 (블록, 분할) 수) × (E_total + 1). E_total이 정해지지 않은 실행(E_B 미선언·유도 전)은 null). card B의 E_total(오케스트레이터 기본안 card B J-6): `find_front`가 결과를 쓸 때 §2.4.9 E_total 정의를 지금 있는 예산 값으로 한 번 계산한다 -- `eval_budget_source`가 `declared`면 `sctx.eval_budget` + N_T + R(as-built N_T = 0, R = 2 × `len(sctx.domain.variables)`), 유도(`derived_once:...`)면 `sctx.eval_budget`(= D), `sctx.eval_budget`이 None이면 null. 새 상수 없음(정의식 그대로). (검증 N-4) card C의 `search_ceiling`은 **탐색 예산**(E_total이 아니다, §2.4.14 (5) C (3))이므로 이 식을 그대로 받지 않는다: card C가 E_total 계산 자리를 한 곳으로 정하고(색인 상한 검사 (5)·실행 끝 확인 (8)·이 칸이 같은 값을 쓰게), `find_front`의 card B 식을 같은 변경에서 지운다(§2.4.14 (3)·(4) C 행에 적음) |
| 결정성 | 조회는 키 일치뿐이고 색인을 순회하지 않는다. 블록은 투영만의 순수 함수라(§2.4.4 '이식이 비트 동일인 전제') 이식한 행과 계산한 행의 `value_fp`·스냅샷 `fp`가 같다. 그래서 색인 적중 여부는 평가 결과를 바꾸지 않는다(바뀌는 것은 계수와 시간 칸뿐 -- §2.4.13 T 부류). 실패 재연도 같은 분류·같은 `FailureRecord` 객체를 던지므로 계산했을 때와 결과가 같다 |
| fail-closed | (1) `donors`·`counters` 없는 블록 호출, `Donors` 하위가 아닌 `donors` → `TypeError`(§2.4.4) (2) `find`가 준 스냅샷의 그 블록(분할) `block_version` ≠ 요청 입력 버전 → `ValueError` (3) 같은 키 재등록 → `ValueError` (4) 등록하는 스냅샷의 `block_version` ≠ 키의 입력 버전 → `ValueError` (5)(card C 뒤, X-8) 등록 때 항목 수가 상한 식의 값을 넘으면 `RuntimeError`. E_total이 아직 정해지지 않았으면(E_B 미선언·유도 전) 정해지는 순간 한 번 확인한다 (6) 한 키에 성공 스냅샷과 실패 기록이 함께 등록되려 하면 `ValueError`(블록 순수성 위반 -- `RunCounters.result`의 섞임 검사와 같은 뜻) |

**조회 API**:

```python
class S3Index(Donors):           # search/s3_index.py
    def find(self, writer: str, part: str, input_version: str) -> GraphSnapshot | None   # 블록 결과 색인(§2.4.4 Donors). 계보 무관 -- XRUN-F1 card B
    def register(self, writer: str, part: str, input_version: str, snapshot: GraphSnapshot) -> None   # 계산 직후 한 번 -- XRUN-F1 card B
    def find_failure(self, writer: str, part: str, input_version: str) -> FailureRecord | None        # 실패 재연(X-9) -- card B
    def register_failure(self, writer: str, part: str, input_version: str, record: FailureRecord) -> None   # 결정적 도메인 실패 한 번(X-9) -- card B
    def get(self, key: EvalKey) -> IndexEntry | None                       # 같은 θ 재요청. 적중이면 커널 0 -- U17 ②(그때까지 as-built `sctx.cache`)
    def failure(self, key: EvalKey) -> FailureRecord | None                # 실패 캐시 보기 -- U17 ②
    def local(self, block_key: str, column: frozenset[str], theta_block_fp: str, fixed_fp: str) -> GraphSnapshot | None
        # 41 §5.3.9 국소 후보 찾기(v1.11: 늘 보존되므로 스냅샷). 찾으면 다시 봉인하지 않는다 -- U17 ②
    def solved(self, block_key: str, bin_key: str, fixed_fp: str) -> bool  # 41 §5.3.2 L-3: (목표 bin, 고정 입력 지문) 쌍을 이미 풀었는지 -- U17 ②
```
v1.11 card B 보완(card B J-5, 오케스트레이터 기본안): **생성자 `S3Index()`는 인자가 없고 비공개 계약이다** -- `open_run()`만 부른다('수명' (1)·규칙 M (M-b)). card B 범위는 위 네 메서드와 fail-closed (1)~(4)·(6). 상한 검사 (5)에 필요한 값은 card C가 생성자 필수 인자로 더하고(검사 자체는 사용자 결정 X-8, 생성자 인자 형식·'기본값 인자로 피하지 않는다'는 offset-strategy 계획 PD-7(S-8)·OS-5 행), OS-5가 B_S0 필수 인자를 더한다(계획 PD-7·OS-5 -- card B는 미리 자리를 두지 않는다). 생성자가 바뀌는 card는 `open_run`과 그 호출부를 같은 변경에서 고친다. 생성 자리는 `open_run` 하나라(규칙 M (M-b)) 생성자 변경은 `open_run` 서명 변경으로 모이고, 호출부는 `open_run` 호출 그대로 인자만 더한다(검증 N-3 -- fixture 하나로 모으기는 강제하지 않는다, 마지막 재확인 반영). 읽기 조회 `entry_count() -> int`(실행 끝 항목 수 = 성공 키 + 실패 키, `perf.block_index_entries`의 출처) 하나를 더한다(값 사본 아님, 개수. 이름은 `WriterTable.entries` 칸과 겹치지 않게 -- 2f684d6 grep `entry_count` 0건). `find_failure`가 준 기록은 등록한 그 객체(`is`)다.

v1.11: 옛 `retain(key, owner)`·`release(owner)`는 없앤다(아래 보존 규칙 -- 실행 안에서 놓지 않는다).
- `failure`의 출처: 그 실행에서 평가한 실패만 담는다. 시작할 때 디스크에서 재구성하지 않는다(v1.10, §2.4.3 'S3').
- `solved`의 출처: 층 0 회차 기록 필드(§2.4.8 'L-3 회차 기록')를 색인할 때 (블록 키, bin, 고정 입력 지문) 쌍을 함께 등록한다.

**정보(m8, v1.10 정정)**: 이전 실행의 S3 점을 시작점으로 쓰지 않는다(§2.4.3 'S3'). 그래서 `regenerated_from_prior_run` 계수도 없다.

**보존 규칙**(v1.11, 사용자 결정 X-2 -- 원래 취지 회복. 옛 결정 1절 #2의 '소유자가 있는 동안만'과 보존 소유자 표(SLSQP 풀이·외층 시작점 대기열·층 0 단계·front·채택)는 폐지, 원문은 history): **실행 수명 동안 계산 원천을 보존한다.** 계산 원천 = 블록 결과 색인이 참조하는 스냅샷 전부와 그 실행의 평가 결과 스냅샷(성공 평가의 평가 스냅샷, 실패 평가의 부분 스냅샷 -- §2.4.7). 실행 안에서는 놓지 않는다. 실행이 끝나면 색인과 함께 버린다. 디스크에는 지금처럼 front·채택 점만 S3 `snapshots/`에 쓴다(as-built `write_snapshot`). 스냅샷은 구조 공유라 보존 비용은 각 스냅샷이 바꾼 레코드뿐이다(측정은 history H4). v1.10 정정: 옛 문장 '§2.4.3과 같은 타입 있는 인코딩'은 §2.4.3 코덱 폐지로 대상이 없다. as-built 인코딩은 `E/search/archive.py:19-36` `_plain`(타입 없는 repr, 비유한 float는 문자열)이다. `snapshots/`의 인코딩 요구(타입 보존 여부·float 표현)는 **U17 ② 착수 전에 정의할 항목**으로 둔다 -- S0 코덱을 되살리지 않는다. 제약(U-90 유지 결정의 결과): `front_query._from_file`이 읽는 형식을 지킨다 -- 문서 최상위 `records`, 레코드마다 `kind`·`key`·`fields`, 필드마다 `value`, 노드의 `dc_v`·`dc_rail_v` 값과 `dc_writer` 값의 `tier`, 소자의 `dc_op` 값 칸(`vgs`·`vds`·`vsb`·`current`·`gm_id`·`W`·`L`)(`E/search/front_query.py:30-46`). 형식을 바꾸면 같은 변경에서 `_from_file`을 고친다.

**놓은 스냅샷이 다시 필요할 때**(Q4, **결정**(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로"), GQ3 = U-73):
- (v1.11 대상 소멸) 옛 규칙 '같은 실행에서 만든 θ를 다시 기준점으로 쓰느라 스냅샷을 재생성하면 FAIL, 계수 `regenerated_after_release`'는 실행 안에서 스냅샷을 놓지 않으므로(위 보존 규칙) 대상이 없다. 같은 입력의 재계산은 §2.4.9 판정 1이 잡는다.
- 이전 실행의 S3 점에서 시작하지 않는다(v1.10, §2.4.3 'S3').

#### 2.4.6 LUT memo: 순수성·인스턴스 하나·상한

결정 G-4'·#8이다.

**순수성의 구조 강제**:
- memo 함수는 **`lut` 패키지 안에만** 정의한다(`E/lut/derived_fns.py`와 기존 lut 조회 파일). import 계층(P N3.10)상 `lut`은 `graph`·`sizing`·`metrics`·`search`를 import할 수 없으므로 graph 필드를 읽을 길이 구조적으로 없다.
- 호출은 `memo.call(fn, *args)`뿐이다. 클로저 `compute`를 받는 as-built `lookup(region, fn_name, key, compute)`(`E/lut/lut_memo.py:60-62`)는 없앤다.
- 정적 검사(규칙 G 확장, §2.4.10): `memo.call`의 첫 인자는 모듈 수준 이름(`ast.Name`·`ast.Attribute`)이어야 한다. lambda·중첩 함수·부분 적용은 거부한다.
- 실행 시 검사(`call` 안): `fn.__closure__ is None`, `fn.__qualname__ == fn.__name__`(모듈 수준), `fn.__module__`이 `gmid_engine.lut` 패키지 이름(`gmid_engine.lut.__name__`에서 읽는다, 문자열 리터럴 아님) + `.`으로 시작. 하나라도 어기면 `TypeError`.
- 인자: 첫 인자는 `LutSet`이고 나머지는 숫자·문자열·bool·None과 그것들의 tuple이다(as-built `BoundedLRU` 불변 키 검사, `E/core/bounded_lru.py:7-9`). 키 = (LUT 지문, `fn.__module__`, `fn.__name__`, 인자).
- 디스크 파생표는 같은 규칙에 디스크 층만 더한다(as-built `lookup_persistent`·`TableCache`, `E/lut/table_cache.py`)(v1.10: 실행 사이 유지 -- U-87 결정, §2.4.12 Q9).

**memo로 옮기는 것**(LUT와 숫자 인자만의 함수인데 지금 다른 곳에 있는 것). 모두 `lut/derived_fns.py`의 모듈 수준 함수가 된다.

| as-built | 위치 | memo 함수와 인자 |
|---|---|---|
| `solve_self` 1변수 근 | `E/sizing/block_columns.py:335-398`(키 :397) | `self_node_root(lut, kind, w_key, L, ln_idu, relation, known, vds0, vds1, vsb0, vsb1, lo, hi, tol)`. 인코딩: `relation` = 관계 어휘 문자열(as-built `REL_VGS_GATE`·`REL_VGS_SOURCE` 값), `known` = 그 1변수 노드 식이 읽는 이미 정해진 노드전압의 float tuple(식의 단자 순서 고정: gate·drain·source·bulk 중 미지수가 아닌 것). 객체·dict는 넘기지 않는다 |
| `cell_floors` 칸 정점 하한·전도 하한 | `E/search/cell_floor.py:47-60`(`sctx.cell_floors`, `search_context.py:84`) | `peak_floor(lut, kind, w_key, lo, hi)`, `conduction_floor(lut, kind, w_key, lo, hi)` |
| `edge_costs` | `E/metrics/edge_cost_bounds.py:51`. `E/search/iv_curves.py:49-52`(`CurveBook._edges`)와 `E/metrics/achievability.py:233`이 따로 계산한다 | `edge_costs(lut, kind, w_key)` |
| `CurveBook._ref`(기준 VDS)·`_tol`(tol_vdsat 최댓값) | `E/search/iv_curves.py:84-87,125-139` | `reference_vds(lut, kind, w_key, L)`, `tol_vdsat_max(lut, kind, w_key, L, vds)` |
| `ParamTables` 행(x, y, z) | `E/metrics/block_param_tables.py:37-54`. `achievability.py:308`과 `iv_context.py:69`가 S0마다 두 벌을 만든다 | `param_row(lut, kind, w_key, i_l, i_d, i_s)` |
| `block_columns.tol_cells` | `E/sizing/block_columns.py:177` | `tol_v_table(...).at`(이미 lut 함수)을 memo로 직접 부른다 |

`one_var_writers`(`cell_floor.py:38`의 `_ONE_VAR_KEY`)는 LUT 함수가 아니라 쓰기 계획의 파생이므로 S0 수준 필드다(§2.4.8).

**인스턴스 하나**: S0마다 `LutMemo` 하나를 만들고 준비 단계(GB4·출발 구간)와 탐색이 같은 것을 쓴다. as-built는 둘이다. 준비 memo는 `StartContext.memo`·`LocalInputs.memo`·`ParamTables._memo`가 계속 쥐고 있고, `_wire_sweep_memo`(f23aec8 `E/search/search_context.py:134-150`)가 탐색용 새 memo를 만들며 계수용 첫 평가를 임시 컨텍스트에서 돌리고 버린다(:141-147). (v1.11: 첫 평가 버림과 `sweep_memo.py`(`_CountingMemo`)는 XRUN-F1 card A가 없앤다 -- 아래 '첫 평가 버림 제거'. 인스턴스 하나는 단계 ③ 그대로.)

**첫 평가 버림 제거**(v1.11, 사용자 결정 X-1 (2) -- U17 ③에서 XRUN-F1 card A로 앞당김. 아래 '공통 규칙'의 '계수 평가가 곧 실제 첫 평가'를 지금 구현한다). as-built는 `E/search/search_context.py:134-150`(f23aec8)이다.
| 항목 | 규칙 |
|---|---|
| 만들기 | `_wire_sweep_memo`가 먼저 n_θ를 정하고(아래), 그다음 `LutMemo.counting(lut, n_theta, *, table_cache=None)`(classmethod, 신규. `table_cache` 기본값 None = as-built `from_sweep`·`LutMemo` 생성자와 같은 뜻 `TableCache.default()` -- J-4 (g), 오케스트레이터 기본안(원칙 근거, 사용자 결정 아님): as-built 의미 보존)로 **계수 상태** memo를 만들어 `ctx.dc`의 `LutAccess`에 넣는다. 영역 point·curve·root는 상한 없이 값을 모은다. derived 영역은 as-built처럼 처음부터 `BoundedLRU(슬라이스 수 × len(DERIVED_TABLES))`다(`E/lut/lut_memo.py:50`, 계수 대상 아님). `build_search_context` 안 커널 평가 = 0(임시 컨텍스트·버리는 평가 없음) |
| U_eval을 재는 점 | as-built는 `centre_start(ctx)`의 점(`E/search/search_context.py:138` -- 사다리가 있으면 칸 0, 없으면 상자 중심 + 전류 중심)을 임시 컨텍스트에서 평가해 셌다. 새 규칙은 그 실행의 첫 커널 평가 점이다. 둘은 보통 같다(층 0이 사다리 칸 0부터 평가한다, `layer0_center.py:646-652`). 다를 수 있는 경우: 칸 0이 원뿔 밖이면 as-built는 커널 0인 평가로 키 0개를 셌지만(그 영역 상한 0 → `_Unmemoized`) 새 규칙은 실제로 처음 커널을 부른 다음 칸·Halton 점에서 센다. 이 차이는 사용자 결정 X-1 (2) '계수 평가 = 실제 첫 평가'에서 나오는 **의도된 변화**이고, 바뀌는 것은 memo 상한·퇴출 수·적중 계수뿐이다(값은 memo가 순수 함수라 같다). §2.4.14 (6) 기준선 재측정 대상이다 |
| n_θ | as-built와 같은 값: `len(centre_start(ctx)[0])`(`E/search/search_context.py:138·149`, 상자 중심 변수 = 정의역 변수 + 구간인 L 칸 변수, 정준 순서). 계수 상태 memo를 넣기 **전에** 잰다 -- 그 사이 LUT 조회는 as-built처럼 호출자가 준 memo로 간다 |
| U_eval,r에 넣는 조회 | **as-built `_CountingMemo` 의미를 보존한다**(`E/lut/sweep_memo.py:14-25`: 첫 평가 안의 조회만 센다). 계수 창 = 그 실행의 **첫 커널 평가** 하나 -- `evaluate`가 커널을 부르는 평가(평가 캐시 적중·정의역 밖은 아님) 중 처음 것의 커널 호출 직전부터 그 `evaluate`가 결과를 만들 때까지(ss·제약 행 조회 포함, as-built 첫 평가가 `evaluate` 전체였던 것과 같다). 창 밖 조회(memo를 넣은 뒤 첫 커널 평가 전의 조회 -- 예: 층 0의 칸 하한 `ln_idu_floors`)는 값을 모으되 U_eval,r에 세지 않는다. U_eval,r = 창 안에서 조회한 서로 다른 키 수(영역별). **'서로 다른 키'의 동치**(J-4 (c), 오케스트레이터 기본안(원칙 근거, 사용자 결정 아님)): `BoundedLRU`와 같은 `canonical_key`(`E/core/bounded_lru.py:7-9` -- 0.0과 −0.0은 다른 키, NaN은 같은 내용이면 같은 키, 1·1.0·True는 서로 다른 키). 근거: 고정 뒤 항목이 들어갈 `BoundedLRU`의 키 동치와 같아야 U_eval,r이 실제로 필요한 칸 수와 같다(as-built `_CountingMemo`의 Python `==`(`sweep_memo.py:22-24`)는 ±0·NaN·1/1.0에서 칸 수를 잘못 센다 -- 이 차이만 as-built와 다르고 키가 일반 float인 조회에서는 같다). **창 안에서 `compute()`가 예외로 끝난 조회**(J-4 (d)): U_eval,r에 넣지 않는다(as-built `_CountingMemo`는 저장된 키만 셌다 -- 보존). 계수 상태의 `misses`에는 `BoundedLRU`처럼 센다 |
| 창 열기·닫기 | `memo.open_count()`(창 열기), `memo.fix_bound()`(창 닫기와 상한 고정). 상태(J-4 (e)·(f), 오케스트레이터 기본안(원칙 근거, 사용자 결정 아님) -- 원칙: 순서 위반은 fail-closed, 결정성): `LutMemo.counting`이 만든 memo는 `"counting"` → `open_count` → `"window_open"` → `fix_bound` → `"fixed"` 한 방향뿐이고, 그 밖의 호출(창 없이 `fix_bound`, 두 번째 `open_count`, 고정 뒤 `open_count`·`fix_bound`)은 모두 `ValueError`다. `LutMemo(...)` 생성자로 만든 memo(처음부터 상한 있음)도 상태가 `"fixed"`이고, `"fixed"` 상태에서 두 메서드를 부르면 생성자 memo든 고정된 계수 memo든 똑같이 `ValueError`다(N-2, 오케스트레이터 기본안: fail-closed, 출처 구분 표지가 필요 없다). `evaluate`는 아래처럼 `bound_state`가 `"counting"`·`"window_open"`일 때만 부르므로 생성자 memo로 돌던 경로는 그대로 돈다. `evaluate`는 커널을 부르기 직전 `memo.bound_state == "counting"`이면 `open_count`, 결과를 만든 직후(성공·후보 실패 모두) `"window_open"`이면 `fix_bound`를 부른다 -- 그래서 첫 커널 평가에서만 창이 열린다. 상태 조회 = 읽기 전용 속성 `LutMemo.bound_state` ∈ {`"counting"`, `"window_open"`, `"fixed"`} |
| 상한 고정 | 영역 r 상한 = (n_θ + 1)·U_eval,r(as-built `LutMemo.from_sweep` 식 그대로). U_eval,r = 0이면 as-built처럼 `_Unmemoized`(이 card는 바꾸지 않는다 -- ③). 그 밖은 `BoundedLRU(상한)`을 만들어 모은 항목을 옮긴다 |
| 옮기는 순서(결정성) | 계수 상태는 영역마다 마지막 접근 순서(`OrderedDict` + 적중 때 `move_to_end` -- `BoundedLRU`와 같은 최근성 규칙, `E/core/bounded_lru.py:37·55`)를 지킨다. 고정 때 오래된 것부터 새 `BoundedLRU`에 넣는다. **넣는 방법**(J-4 (b), 오케스트레이터 기본안(원칙 근거, 사용자 결정 아님)): `BoundedLRU`에 새 메서드 `adopt(key, value)`(**원 key**를 받아 안에서 `lookup`과 같은 `canonical_key`를 적용한다 -- 계수 상태는 원 key를 보관해 넘기고 정규화한 키를 넘기지 않는다(이중 정규화 금지, N-1, 오케스트레이터 기본안). 계수 hits·misses를 바꾸지 않고 넣는다. 상한을 넘으면 공개 `lookup`과 같은 규칙으로 가장 오래된 것을 퇴출하고 `evictions`에 세며 퇴출 키를 퇴출 기록에 남긴다 -- 그 키를 나중에 다시 계산하면 `recomputes_after_eviction`이 센다)를 쓴다. 근거: 공개 `lookup`으로 넣으면 이미 계산한 항목이 `misses`로 한 번 더 세어져 계수가 뜻을 잃는다(miss = 실제 계산). 퇴출 기록은 판정 3(퇴출 뒤 재계산)이 쓰므로 남겨야 한다. `E/core/bounded_lru.py`를 §2.4.14 (3) 재작성 범위(card A)에 넣는다. 모은 항목이 상한보다 많으면 가장 오래된 것부터 퇴출되고 그 수는 `BoundedLRU`의 퇴출 계수에 든다(as-built에서도 첫 평가 밖의 조회는 상한 있는 memo에 들어갔다 -- 퇴출 시점은 다를 수 있고 값은 같다). 순서는 조회 순서만의 함수라 결정론적이다 |
| `stats()`(J-4 (a), 오케스트레이터 기본안(원칙 근거, 사용자 결정 아님)) | 계수 상태(`"counting"`·`"window_open"`)에서 point·curve·root 영역은 `LruStats(capacity=None, size=모은 항목 수, hits, misses, evictions=0, recomputes_after_eviction=0)` -- `capacity=None` = 상한이 아직 없다(0은 as-built `_Unmemoized`의 '저장 안 함'과 겹치므로 쓰지 않는다). 고정 뒤에는 `BoundedLRU` 계수에 계수 상태 동안의 hits·misses를 더해 낸다(capacity·size·evictions·recomputes_after_eviction은 `BoundedLRU` 것). derived 영역은 처음부터 `BoundedLRU` 그대로. 소비자: `find_front`는 `evictions`만 합한다(`E/search/find_front.py:126`) -- 영향 없음 |
| 첫 커널 평가가 없는 실행 | 상한을 고정하지 않은 채 끝난다(계수 상태 유지). 커널 평가가 없으면 조회는 창 밖 조회뿐이라 유한하다. 거부하지 않고 결과 JSON `perf.lut_memo_bound` = `"unfixed_no_kernel_eval"`(`bound_state`가 `"fixed"`면 `"fixed"` -- 생성자 memo로 돈 탐색도 `"fixed"`, J-4 (f))로 보고한다. 실행이 `"window_open"`으로 끝나는 경우는 첫 커널 평가 도중 예외가 올라간 실행뿐이라 결과 JSON이 없다. 근거: 시작점이 모두 정의역 밖인 실행도 정상 결과(시작점 없음)라 예외로 바꾸지 않는다 |
| 독립 계수(test) | test의 기대 U_eval,r은 피검 memo의 자기 계수를 읽지 않고 만든다: test가 `LutMemo.lookup`을 클래스 수준에서 감싸 (영역, `(lut.fp, fn_name) + key`)를 기록하고, `evaluate`(또는 `size_and_seal`)를 감싸 첫 커널 평가 구간을 표시해, 그 구간의 서로 다른 키 수를 `canonical_key` 동치로 센다(위 (c)와 같은 동치, `compute()`가 예외로 끝난 조회는 뺀다). 단언은 고정된 영역별 용량 = (n_θ + 1) × 그 수, n_θ = test가 `centre_start`로 따로 잰 값 |

- B_r의 나머지 항(U_S0,r·층 0 항), 인스턴스 하나, `call` 형식, `_Unmemoized` 제거는 단계 ③ 그대로다(이 card는 바꾸지 않는다).
- 삭제: `E/lut/sweep_memo.py` 전체(`_CountingMemo`·`sweep_memo`), `LutMemo.from_sweep`, `_wire_sweep_memo`의 임시 컨텍스트 평가(`first_eval`, `copy.copy(ctx)`). 이름별 grep 범위는 §2.4.14 (4).

**상한과 퇴출 판정 -- 결정(사용자 결정 2026-10-12 "U-60은 (가)로", U-60 = (가))**
- 키: 연속 축 값 그대로(as-built와 같다).
- 상한(영역 r = point·curve·root마다): B_r = U_S0,r + Σ_i K_max,i·(U_pass,i,r + U_macro,i,r) + (n_θ + 1)·U_eval,r.
  - U_S0,r = S0 수준 층을 계산하며 센 서로 다른 키 수다(실행마다 계산하므로 늘 센다, v1.10).
  - U_L0,r = Σ_i K_max,i·(U_pass,i,r + U_macro,i,r). 블록 i의 **첫 후보 하나**에서 한 번 센다(U_pass = 첫 후보 고정점 한 바퀴의 서로 다른 키 수, U_macro = 같은 바퀴 매크로 호출의 키 수, K_max,i = 그 바퀴의 N3.6 반복 상한). N_T를 곱하지 않는다. 41 §5.8에 같은 문장이 있다. 층 0이 꺼진 회로는 0이다.
  - U_eval,r = 외층 첫 평가가 센 서로 다른 키 수다.
  - 세 항 모두 실행 시작 쪽에서 한 번 세고 고정한다. N_T·E_B·벽시계에 의존하지 않는다(결정론, NFR-4).
- **판정**: 퇴출은 허용하고 퇴출 수는 `perf`에 보고한다. 퇴출된 키를 다시 계산하면(`recomputes_after_eviction` > 0) FAIL이다. 계획 NFR-2·N3.5를 이 문구로 고쳤다.
- 기록(대안, 채택 안 됨): (나) 격자 마디 키·퇴출 0 FAIL은 root 영역 상한이 E_total(N_T)에 의존해 쓰지 않았다.

**공통 규칙**:
- memo는 계수 상태로 시작한다(상한 없음, 키를 센다). 상한의 항을 다 셌으면 상한을 고정한다. 이미 모은 항목은 그대로 둔다. 계수 평가가 곧 실제 첫 평가이고 S3 색인에 기록된다.
- 계수 0 영역을 '저장 없이 매번 계산'으로 두는 `_Unmemoized`(`E/lut/lut_memo.py:25-36`)는 없앤다(같은 키 재계산이 생긴다).
- DF-07(상한에 닿으면 LRU 퇴출, 캐싱 중단 금지, §10.3a)은 그대로다. 퇴출은 정상 동작이고, 퇴출된 키의 재계산만 FAIL이다.

#### 2.4.7 값 사본 제거

결정 #5·#6·#9와 G-7이다. 아래 객체는 graph 필드나 S0 수준 필드의 사본을 들고 있다. 사본을 지우고 필드를 읽는다.

| 객체 | as-built 사본 | 바뀐 형태 |
|---|---|---|
| `SearchContext`(G-7) | `E/search/search_context.py:54-89`의 모든 칸 | **참조**(S0 수준 스냅샷 뿌리, LUT memo, spec, PDK 선언, S3 경로) + **S3 메모리 색인** + **실행 계수**만 둔다. `__slots__`와 frozen으로 고정하고, 바꾸는 길은 S3 색인 API와 계수 API뿐이다. 칸마다 갈 곳은 아래 'SearchContext 칸 배정' 표. **과도기(v1.9.2 결정 5)**: U17 ①-b as-built는 옛 칸 이름(`domain`·`junction`·`mismatch`·`model_error`·`area_decl`·`structure`·`noise_decl`·`judged_constraints`·`ss_constraints`·`constraint_notes`·`rungs`·`schema_fp`·`element_values`·`driving`)을 읽기 전용 속성으로 남긴다. 속성은 부를 때마다 S0 수준 필드(또는 spec 참조)를 읽고 사본을 두지 않는다. 이 속성과 남은 실행 수명 칸은 ② G-7 재작성에서 위 형태로 정리한다(근거: `wt/_audit_u17_1b/audit_report.md` 7절 as-built (c) -- 원칙 위반 아님) |
| `KernelContext` | `base`, `inputs`, `lut`, `schema`(θ 스키마, `zero_cancel` 포함), `fixed_values`, `resistor_values`, `plan_versions`, `l_ties`(`E/sizing/s2_values.py:429-443`) | v1.11: 참조 칸 `donors`(그 실행의 블록 결과 색인 `S3Index`, §2.4.5)·`counters`(그 실행의 `RunCounters`, §2.4.9)를 더한다 -- 값 사본이 아니라 실행 수명 객체의 참조이고, 커널 블록 호출이 §2.4.4 필수 인자를 여기서 받는다(XRUN-F1 card B). **과도기 칸**(사용자 결정 X-13, `StageAResult`의 같은 칸 포함) -- U17 ② G-7 재작성에서 정리한다. 설계 값은 S0 수준 필드: `graph/kernel`: `theta_schema`(`zero_cancel` 포함. as-built `graph: dc_theta_schema` 필드(`E/sizing/theta_schema.py:63`)를 `graph/kernel`로 옮긴 것이고 writer `dc_theta_schema` 블록은 그대로다 -- v1.9.1 D8, 단일 writer), `fixed_values`, `resistor_values`, `l_ties`. `plan_versions`는 쓰기 계획 블록의 `block_version` 읽기로 대체한다. 남는 칸은 참조(`base` = S0 수준 스냅샷, `lut` = LUT memo와 폭 키, `inputs` = spec 파싱 결과) |
| `StartContext` | `cls`, `kinds`, `pins`, `rails`, `rail_v`, `node_colour`, `l_owner`, `basis`, `element_values`, `zero_cancel`, `l_cells`, `box` 등 graph 열 사본과 `curves`·`memo`·`block_local`(`E/search/start_values.py:186-235`) | 없앤다. 출발 구간 블록이 선언한 입력 필드를 투영으로 읽는다 |
| `CurveBook` | LUT 파생 사전 3개와 `points`(`E/search/iv_curves.py:37-40,102-108`) | 없앤다. LUT 파생은 memo 함수(§2.4.6) -- `E/lut/derived_fns.py` 모듈 함수로 U17 ①에서 옮기고 as-built `memo.lookup` 형식으로 부른다(`call` 형식 전환은 ③, v1.9.1 D10). `points`는 소자 필드 `start.point`(§2.4.8) |
| `S1v`·`Achievability`·`StartIntervals` 묶음 객체 | 컨텍스트와 단계 결과(`StageAResult`·`StageBResult`)에 객체째 실린다 | S0 수준 필드(§2.4.2). 단계 결과는 S0 수준 스냅샷 참조만 넘긴다 |
| `SsEvaluation` | `ss`·`dc` `MetricBundle`(`E/metrics/ss_types.py:79-88`) | `lineage`(스냅샷)만 둔다. metric은 `graph/metrics` 필드에서 읽는다 |
| `EvalResult` | `objectives`, `constraints`, `unmeasured`, `warnings`(`E/search/search_values.py:146-162`) | (평가 키, 색인 항목, 스냅샷). v1.11: 스냅샷은 늘 있다(실행 수명 보존) -- 성공 = 평가 스냅샷, 후보 실패 = 부분 스냅샷(아래 '실패 평가의 부분 스냅샷'), 정의역 밖(커널 0) = 없음. 목적 값과 분해능은 `metrics_dc` 필드에서, 제약 행은 `graph/metrics: constraint_rows`에서 읽는다(옛 문장 '스냅샷을 놓았으면 색인 항목(S3 기록)에서 읽는다'는 v1.11 실행 수명 보존으로 대상 소멸). ε 행은 풀이 매개변수라 필드가 아니다 |
| `Objectives`(search) | `gate_area_m2`(Σ dc_op W·L), `power_resolution_w`(b_P)를 search가 다시 계산한다(`E/search/objectives.py:12-14,31-45`) | `metrics_dc`가 `gate_area_m2`와 새 필드 `power_resolution_w`(읽기: `dc_gm`, `dc_tol_v`, `dc_current_basis`, `dc_rail_v`)를 쓴다. search의 재계산(`_power_resolution`)을 지운다 |
| `LayoutResult` | `devices`, `groups`, `rows`, `floorplan`, `diffusion`, `w_requests` 등과 별도 lineage `snapshot`(`E/layout/contract_output.py:366-387`, `E/layout/run.py:109`의 `GraphSnapshot.empty(LY_WRITERS)`) | 레이아웃 필드는 그 **설계점 스냅샷**의 S2 `layout` 필드다. 별도 lineage는 없다. 레이아웃 재시도는 같은 설계점 lineage의 새 스냅샷이다. `LayoutResult`는 스냅샷 하나만 둔다(`LayoutResult(snapshot)`). v1.11.2(사용자 결정 O-17 (3) 2026-10-19): `LayoutResult.computed_blocks`를 삭제한다 -- 같은 정보('이번 호출에서 계산·이식·재사용한 writer')의 정본은 `RunCounters` 행(결과 JSON `perf.blocks`)이고 칸은 그 사본이었다(근본원칙). test는 `RunCounters`를 읽는다. `E/layout/contract_output.py` docstring과 `E/layout/CONTRACT.md` 해당 문구를 같은 변경에서 고친다. 옛 문장(v1.11 card B J-9 '`computed_blocks`는 출력 전용으로 두고 뜻만 고친다')은 계획 history |
| `LocalSeal` | `snapshot_fragment`, `gain_db`, `power_w`, `area_m2`(`E/sizing/size_and_seal_local.py:119-129`) | 국소 스냅샷(41 §5.3.9). 봉인 통과·실패 레코드는 봉인 필드, 국소 전력·면적·gain·Z_out은 블록 범위 metric 필드(§2.4.8) |
| 수동소자 값 | `passive_values()`를 부를 때마다 다시 만든다(`E/metrics/passive_values.py:16-31`의 호출처 `ss_evaluate.py:96`, `E/convergence/converge_point.py:49`). 봉인 아닌 점은 `kernel.py:146-150`이 같은 규칙을 다시 적는다. `sctx.spec_passive_values`(`search_context.py:206-207`)도 있다 | S2 필드 `device.passive_value`(§2.4.8). 영점 상쇄 R = 1/Σ`dc_gm`(dc 단계 필드)이라 봉인 전에도 정의되고, `kernel.py:146-150` 사본과 '봉인 아닌 점은 값 없음' 분기를 지운다 |

**실패 평가의 부분 스냅샷**(v1.11, 사용자 결정 X-3, XRUN-F1 card B). as-built(f23aec8)는 후보 실패면 평가 스냅샷을 버린다(`E/search/kernel.py:119-122` -- `evaluation`이 None으로 남는다, `:129-135` ss 단계 실패도 같음, `E/sizing/seal.py:50-58`은 봉인 보고서를 쓴 스냅샷을 만든 뒤 예외를 낸다). 2f684d6 재측정 줄: `E/search/kernel.py:121-125`·`:132-138`, `E/sizing/seal.py:49-57`.

| 항목 | 규칙 |
|---|---|
| 정의 | 후보 실패(core `CANDIDATE_FAILURE_CLASSES`)로 끝난 커널 평가가 실패 직전까지 쓴 마지막 스냅샷을 **base writer ∪ 그 평가에서 실패 전에 부른 블록**으로 줄인 것(v1.12.9, 계획 v6.32 N3.3 '실패 평가의 부분 스냅샷', 사용자 결정 O-96 -- 41 §4.7-3c '실패 평가의 부분 스냅샷 파생'). 커널 블록(steps·later 구성원 -- 구성은 IT-2d 병합 head 실측) 실패 = 그 블록에 들어간 스냅샷을 base writer ∪ 앞 블록(앞 커널 블록)으로 줄인 것. 봉인 항목 블록(구성 = `SEAL_ITEM_BLOCKS` 상수) 실패 = 그 블록에 들어간 스냅샷을 base writer ∪ 커널 블록 ∪ 앞 봉인 항목 블록으로 줄인 것. 봉인 보고서 블록 실패 = base writer ∪ 커널 블록 ∪ `SEAL_ITEM_BLOCKS`의 블록 전부로 줄인 것. '실패 전에 부른 블록' = 계획의 '실패 전에 성공한 블록'(첫 실패에서 멈추므로 같은 집합). 실패한 블록 자신과 그 뒤 블록의 필드는 넣지 않는다(parent에서 파생한 스냅샷에 남은 그 블록들의 parent 값 -- 이번 평가가 계산하지도 확인하지도 않은 값). 봉인 위반이면 `dc_seal_report`까지 쓴 스냅샷이고 보고서 블록도 부른 블록이라 남긴다(보고서를 지우지 않는다). ss 단계(`ss_evaluate`) 실패면 그 단계가 실패 직전까지 쓴 스냅샷(적어도 봉인 스냅샷 -- 시작 스냅샷 = 봉인 스냅샷이고 ss writer는 파생 keep 밖이라 이미 이 규칙을 충족, 줄이는 자리 없음; 계획 N3.3). 봉인 아닌 점의 `passive_values`·`metrics_dc` 후보 실패는 범위 밖(백로그) |
| 형식 | 새 타입을 두지 않는다 -- `GraphSnapshot` 그대로. 어디까지 계산했는지는 그 스냅샷의 `block_versions`가 말한다. 근거(v1.12.9): 위 '정의'대로 줄인 뒤에는 parent가 있든 없든 `block_versions` 키 = base writer ∪ 실패 전에 부른 블록이라 이 문장이 참이다(줄이기 전에는 parent 경로에서 실패 블록과 그 뒤 블록이 parent 버전으로 남아 거짓이었다 -- 근거 `wt/_drafts/evidence/2026-10-22/b69_partial_snapshot_analysis.md` 2절). 그래서 부분 스냅샷 지문은 (평가 키, 실패 지점)만으로 정해지고 parent와 무관하다(evals 실패 줄 `snapshot_fp`의 결정성). parent 없는 평가는 스냅샷 writer가 이미 그 집합 안이라 줄여도 바뀌지 않는다(지문 불변) |
| 전달 | 후보 실패 예외의 기반(core `InfeasibleSizingError`)에 칸 `partial`(`__init__`이 None으로 둔다)을 둔다. 부착은 **`failure_errors.py` 밖의 함수**다(v1.11 card B 보완 card B J-3, 오케스트레이터 기본안): 새 파일 `E/core/failure_partial.py`, 진입점 `attach_partial(exc, snapshot) -> None`(`exc`가 `InfeasibleSizingError` 하위가 아니거나 `snapshot`이 `GraphSnapshot`이 아니면 `TypeError`, `exc.partial`이 이미 있으면 바꾸지 않는다 -- 가장 안쪽이 이긴다). 근거: `failure_errors.py`는 데이터 선언 모듈(`E/_module_map.py:228` kind `"data"`)이고 규칙 A는 데이터 클래스 메서드를 dunder·`property`·`from_*` classmethod로만 허용한다(`E/tests/structure/structure_checks.py:241-249` `_data_method_ok`, `:252-272` `is_data_module`). 일반 메서드 `attach_partial`을 예외 클래스에 두면 데이터 모듈이 아니게 되고, 파일 안에서 참조되지 않는 공개 클래스 6개가 진입점 개념 6개가 되어 규칙 A 위반이다(2f684d6 실측). 구조 규칙은 바꾸지 않는다. test `E/tests/core/test_failure_partial.py`(규칙 H). 스냅샷을 쥔 쪽 -- sizing `run_kernel`(커널 블록 단계마다), `seal_dc`(봉인 항목 블록·봉인 보고서 블록 실패, 봉인 위반), metrics `ss_evaluate`(ss 단계) -- 이 후보 실패 클래스를 **이름으로** 잡아 `attach_partial`로 붙이고 다시 낸다(넓은 except 금지 그대로, 규칙 F; sizing 자리는 아래 '줄인 뒤 붙임'대로 줄인 스냅샷을 붙인다). `seal_dc`는 스스로 내는 `SealViolationError`에 보고서까지 쓴 스냅샷을 줄여(`dc_seal_report` 포함) 붙인 뒤 낸다. 재연한 예외(§2.4.4 '실패 재연')는 블록 호출이 새로 만든 예외라 `partial`이 None으로 시작하고, 바깥 부착 자리(`run_kernel`의 `_call_block`·`seal_dc`)가 그 블록에 들어간 스냅샷을 줄여 붙인다(계산했을 때와 같은 부분 스냅샷). 블록 함수는 투영만 받으므로 붙이지 않는다. **줄인 뒤 붙임**(v1.12.9, 계획 v6.32 N3.3, 41 §4.7-3c '실패 평가의 부분 스냅샷 파생'): sizing의 부착 자리는 들어간 스냅샷을 그대로 붙이지 않고 `snapshot.derive_child(writers_in_scope(base, 앞 블록))`으로 줄인 스냅샷을 `attach_partial`에 넘긴다 -- 집합 함수 `writers_in_scope(base, blocks) -> frozenset`(`E/sizing/seal_versions.py`, base writer = `ctx.base.block_versions` 키 ∪ 블록 객체 이름; 'base writer ∪ 블록 이름' 집합의 정의 하나 -- 같은 함수를 `run_kernel` 파생 keep·봉인 4 coverage도 부른다). 자리와 앞 블록: `run_kernel`의 `_call_block`(커널 블록 실패 -- 인자 `before` = 커널 호출 순서의 앞부분 slice), `seal_dc` 봉인 항목 블록 실패·봉인 보고서 블록 실패(지역 `calls`의 블록), 봉인 위반(`calls`의 블록 + `dc_seal_report`). 재연한 예외도 같은 자리에서 같은 앞 블록으로 줄여서 붙는다(계산했을 때와 같은 부분 스냅샷). `attach_partial`·`ss_evaluate` 부착은 바꾸지 않는다. 새 필드·cache·값 사본·writer·블록 호출 없음(구조 공유 파생, reuse·graft·compute 계수 변화 0) |
| 결과 | `EvalResult`에 칸 `partial`(후보 실패 = 부분 스냅샷, 성공·정의역 밖 = None)을 더한다. 이것은 U17 ② G-7 재작성 전의 과도 형식이고 최종 형식은 위 표 'EvalResult' 행이다. S3 evals 줄은 실패 평가에도 `snapshot_fp` = 부분 스냅샷 `fp`를 쓴다(**evals 줄 형식 변경**: 실패 줄에 칸 하나가 생긴다 -- 사용자 결정 X-10 허용) |
| 재사용 | 부분 스냅샷 안의 블록 결과는 계산 직후 이미 블록 결과 색인에 등록돼 있다(§2.4.5 '등록'). 그래서 실패한 평가가 계산한 블록 결과도 다른 평가에서 이식된다. 부분 스냅샷을 parent로 쓰지는 않는다(parent 규칙은 그대로) |
| 보존 | 실행 수명(§2.4.5 보존 규칙) |

**SearchContext 칸 배정**(Q5, design 기본안(최종 승인에 포함)):

| as-built 칸 | 갈 곳 |
|---|---|
| `dc` | 참조: S0 수준 스냅샷 뿌리 + LUT memo(위 `KernelContext` 행) |
| `domain`(`SearchDomain`: 변수·상자·원뿔·묶음·W_min·격자·면적 분해능) | S0 수준 필드 `graph/kernel: search_domain`(writer `search_domain`, 읽기: θ 스키마·S1·PDK 선언·spec θ 범위·면적 예산·untie) |
| `settings` | spec 참조(실행 설정) |
| `context_fp`, `schema_fp`, `code_fp` | `context_fp` = **평가 커널의 S0 입력 지문**: (S1 블록·커널 계획 블록(`PLAN_WRITERS`)의 블록 입력 버전, LUT 손잡이, `DcInputs`)의 지문. 정의역 상자·출발 구간·접합 선언 같은 탐색 쪽 S0 필드는 평가 결과를 바꾸지 않으므로 넣지 않는다. 의미는 base의 '평가 커널 S0 입력'과 같다. `schema_fp` = `graph/kernel: theta_schema` 필드의 값 지문을 읽는다. `code_fp` = 단계 A가 잰 엔진 코드 지문(`StageAResult.code_fp`, v1.10: 옛 '§2.4.3 키 (iii)'은 대상 소멸 -- 출력 출처 칸, §2.4.3 '엔진 코드 지문')을 받는다(v1.9.2 결정 5 정정; 근거: as-built `build_search_context`(`E/search/search_context.py`)가 옛 문언 'S0 지문과 §2.4.3 키에서 읽는다(사본 없음)'과 달랐다, `wt/_audit_u17_1b/audit_report.md` 7절 as-built (b)) |
| `element_values`, `spec_passive_values` | 수동소자 값 필드(S2) |
| `judged_constraints`, `ss_constraints`, `constraint_notes` | S0 수준 필드 `graph/kernel: constraint_classes`(spec 제약의 목적 축·ss·미측정 분류, writer = 제약 분류 블록, 읽기: spec·metric 등록부 지문). 값 = 새 frozen dataclass(v1.9.1 D8; 근거: as-built `constraint_notes`는 dict 행이라 graph 값의 불변 규칙에 맞지 않는다 -- v1.10: 옛 근거 'S0 스냅샷 코덱이 받지 않는다'는 코덱 폐지로 사라졌고 불변 근거만 남는다) |
| `junction`(`JunctionSource`), `mismatch`(`MismatchSource`) | S0 수준 필드 `graph/kernel: junction_source`, `mismatch_source`(PDK 선언·LUT 생성 규칙 선언의 파생) |
| `driving` | spec 참조(`spec.driving_spec`, 파생 없음) |
| `area_decl` | S0 수준 필드 `graph/kernel: passive_area_decl` |
| `model_error` | S0 수준 필드 `graph/kernel: model_error`(오라클 대조 결과는 spec `derived.model_error_*` 선언에서 온다) |
| `structure`, `noise_decl`, `s1v`, `ach`, `start` | S0 수준 필드(§2.4.8) |
| `spec` | 참조 |
| `archive` | S3 경로 참조(색인이 소유) |
| `cache`, `computed_keys`, `local_seal_memo` | S3 메모리 색인 (`disk_failures`는 v1.10에서 삭제, 7e1b4be) |
| `cell_floors` | LUT memo(§2.4.6) + `dc_self_referential` 필드 |
| `counters`, `eval_times`, `seq`, `eval_budget`, `eval_budget_source`, `deadline` | 실행 계수(`core/run_counters.py`) |

#### 2.4.8 필드 소유표

graph 밖에 있던 값마다 갈 곳을 정한다. '층'의 S0 = S0 수준 층, B = 단계 B 층, S2 = 설계점 층, L0 = 층 0 층이다. 이 표에 없는 graph 밖 설계 값이 발견되면 같은 방식으로 행을 더한다(G-8 위치 검사가 찾는다). §2.4.7의 `KernelContext`·`SearchContext` 칸 배정도 이 표의 일부다.

| 값(as-built 위치) | 필드(kind/key: field) | writer(계산 블록) | 층 |
|---|---|---|---|
| S1v 전체(`sctx.s1v`, `StageAResult.s1v`) | `graph/s1v`: `views`(as-built `ViewS1v` tuple 그대로 -- 블록·복합 블록·극점 노드·루프·끊는 점은 뷰 안 칸), `l_classes`, `findings`, `declared`, `applied_facts`. v1.9.1 D1: 옛 별도 필드 `blocks`·`composite_blocks`·`pole_nodes`·`loops`·`cuts`는 `views`의 사본이라 만들지 않고, `coverage`는 폐기한다(근거: 사본 금지) | `build_s1v`(GB2) | S0 |
| 자기동형 궤도·d/s 맞바꿈 부호(§6) | `graph/s1`: `orbits`, `current_symmetry` | graph 대칭 블록 `s1_symmetry`(`graph/s1_symmetry.py`, §6) | S0 |
| 구조 색(정준 순서, as-built master writer = sizing `dc_struct_colour`, `E/sizing/struct_colour.py:20`) | `device: dc_colour`, `node: dc_colour` = (`wl`, 정준 위치) 쌍의 정렬 순위(정점마다 유일, 이름 무관) | graph 대칭 블록 `s1_symmetry`(graph/s1, §6). sizing·search·metrics는 읽기만 한다 | S0 |
| 결합 변수 y, 기둥↔블록 매핑(보고서에만 있음, `E/pipeline/stage_a.py:101-121`) | `graph/coupling`: `vars`, `column_block_map`, `bias_columns`. v1.9.1 D8: `column_block_map` = as-built `ColumnBlockMap.rows`, `bias_columns` = `ColumnBlockMap.bias_columns`(`E/graph/coupling_values.py:68`) -- `ColumnBlockMap` 묶음은 필드로 두지 않는다(근거: 사본 금지) | `coupling_vars`(GB3) | S0 |
| GB4 `Achievability`(`sctx.ach`, `StageBResult`) | `graph/ach`: `curve_checks`, `gain_checks`(`GainCheck` \| None), `area_bound`, `headroom_rows`, `buffer_window_report`, `warnings`, `reasons`, `verdict`, `dof`(**구조 DOF만**, 41 A7 -- `DofReport`의 `numeric_ranks` = `()`), `count_budget`, `local_inputs`(아래 행). v1.9.1 D2: 옛 `block_bounds`는 `GainCheck.blocks`(`E/metrics/achievability_types.py:130`)의 사본이라 만들지 않는다. 블록 상한은 `gain_checks`에서 읽는다(근거: 사본 금지) | `achievability`(GB4, 41 A4~A7) | S0 |
| 층 0 정의역 상한 A_i,max^L0(41 A9, §4.2) | `graph/ach: block_bounds_l0` | `block_bounds_l0`(41 A9) | S0 |
| 결합 잔차 분포 r̂(41 B1) | `graph/stage_b: residual_probe`(r̂, r̂_spread, 표본) | `residual_probe`(as-built `E/search/residual_probe.py:66`). v1.9.1 D5: 블록 배선은 소비자(층 0)와 함께 U17 ②, ①-b는 필드 자리·직렬화 제외 규칙만(근거: 동작 변경 회피) | B |
| 수치 rank(41 B2) | `graph/stage_b: dof_numeric` | `dof_numeric`. v1.9.1 D5: `residual_probe`와 같이 U17 ②에서 배선 | B |
| 출발 구간 `StartIntervals`(`sctx.start`) | `device`: `start.row`(`StartRow`), `start.point`(옛 `CurveBook.points`). `graph/start`: `kvl_model`(쓰기 계획·고정 전위·종속 소자·의존 묶음, 41 §6.7), `kvl_rows`(선택점 행 표), `records`(U17 ①-b = as-built 매크로 모델 기록 `StartIntervals.records`. `kvl_adjusted`·`kvl_macro_recheck`·`kvl_unsatisfied` 등 KVL 기록은 U17 ②에서 더한다), `conflicts`(`StartConflict`), `inactive`(비활성 경계와 사유), `macro`(`MacroResult`), `rungs`(as-built `StartIntervals.ladder` = `StartRung` tuple 그대로 -- 칸 0 = 선택점, 정의는 41 §6.1-9), `area_est_m2`·`area_fraction`·`uncovered`(as-built `StartIntervals` 같은 이름 칸), `noise_inputs`(β·C_eff 입력, 41 §7.5 -- U17 ②에서 β·C_eff 계산과 함께), `placement`(선택점 둘레 출발 θ 생성기 입력, 정의는 41 §6.1-9 -- U17 ②에서 U15 `placer`와 함께. as-built MOD8 `Placement`와 다른 것이다). v1.9.1 D3·D4: `StartIntervals`의 `theta`·`cells`·`current_ref`는 `rungs` 칸 0의 사본이라 필드로 두지 않는다(근거: 사본 금지; `noise_inputs`·`placement`는 소비자 위치) | `start_intervals`(41 §6, A8) | S0 |
| metric 구조 입력 `metric_structure(s1v)`(`sctx.structure`) | `graph/s1v: metric_structure` | `metric_structure`(MOD5) | S0 |
| 잡음 입력 셀 `noise_decl(spec, s1v)`(`sctx.noise_decl`) | `graph/s1v: noise_input_cells`. 값 = as-built `NoiseDecl` 전체(`E/metrics/noise_types.py:23`, v1.9.1 D7) | `noise_decl`(MOD5) | S0 |
| 1변수 writer 집합(`sctx.cell_floors[("one_var_writers",)]`) | `device: dc_self_referential` | 쓰기 계획 블록(sizing) | S0 |
| 블록 국소 모델 입력 `LocalInputs`(`achievability.py:77-113`, `iv_context.py:63-69`에서 두 번) | `graph/ach: local_inputs`. 값 형식(v1.9.1 D9): as-built `LocalInputs`(`E/metrics/achievability_types.py:221`)의 dict 칸을 tuple로 바꾸고 `memo` 칸을 뺀 형식으로 재정의한다(근거: graph 값은 불변이어야 한다 -- v1.10: 옛 근거 'S0 스냅샷 코덱 직렬화'는 사라졌다. memo는 LUT memo 참조, §2.4.6) | `achievability`(GB4). 출발 구간이 같은 필드를 읽는다 | S0 |
| 커널 컨텍스트 구조 파생(`KernelContext.schema`·`fixed_values`·`resistor_values`·`l_ties`) | `graph/kernel`: `theta_schema`, `fixed_values`, `resistor_values`, `l_ties` | `build_kernel_context`를 블록으로(sizing). v1.9.1 D8: `theta_schema`는 as-built `graph: dc_theta_schema` 필드(`E/sizing/theta_schema.py:63`)를 옮긴 것이고 writer `dc_theta_schema` 블록을 유지한다(근거: 단일 writer) | S0 |
| `SearchDomain`, 제약 분류, 접합·mismatch 출처, 면적 선언, 모델 오차 | `graph/kernel`: `search_domain`, `constraint_classes`(새 frozen dataclass, v1.9.1 D8), `junction_source`, `mismatch_source`, `passive_area_decl`, `model_error` | 각각 search·metrics의 S0 블록(§2.4.7 표) | S0 |
| 수동소자 값(spec ∪ θ ∪ 영점 상쇄 R = 1/Σ`dc_gm`) | `device: passive_value` | GB5 수동소자 블록(`passive_values`를 블록으로). 엔진·오라클 입력(U16)·레이아웃 어댑터가 이 필드를 읽는다 | S2 |
| tol_I의 gm(`dc_gm_bound`, S2p 의존, `E/sizing/seal_tolerances.py:36-45`, `E/sizing/kernel_run.py:51-96`) | `device: dc_gm` = ID × (그 동작점의 LUT gm/ID) | `dc_tolerances`(dc 단계, writer 1개). 봉인 3·`ss_dev`·b_P·수동소자 R이 읽는다(§3.7-3) | S2 |
| 입력 포트 탐색·판정 창(v1.12 card IT-2, 계획 N6.6 범위 1 -- 옛 as-built: W4 뿌리에만 쓰고 커널 안에서 `_refine_ends` 끝 풀이까지 했으며, metric은 `ls_swing`이 경로 합으로 둘째 창을 따로 쟀다, 41 §4.7-0 A6·A8·A9) | `node: dc_window` = `Window(lo, hi, constraints, input_status, tol_v, status_detail)`. 범위 = **모든 입력 포트와 W4 뿌리**. 입력 포트 항목 = 포화 판정 여유(+tol_VDsat) 창의 **선형 감도 끝**(손계산 '추정', 41 §4.7-3), `input_status` ∈ {`measured`, `unsettled`, `unmeasured`, `op_mismatch`, `f_component_undeclared`}(어휘·우선순위 정본 = 41 §4.7-2 '값 형식'); 그 밖 W4 뿌리 = 순서 창(`input_status=None`) | `dc_columns`(평가 커널, 모든 평가). 읽는 쪽: `fd_jacobian` y 스텝(relation `free_window` 넷만, 41 §4.7-6) -- 값 독자는 이것뿐(계획 N6.6 범위 1 '커널 탐색만'); `icm_config`는 상태 칸만 읽음(41 §4.7-3b) | S2 |
| 쓰기 계획 필드(v1.12 card IT-1, 계획 N6.5 완료 조건 4 (c) -- 형식 불변, 값 어휘 변경) | `node: dc_writer`(`NodeWrite` -- relation `input_tie` 없어짐, 입력 포트 W4 뿌리 `y_key` = 뿌리 넷(옛 `input_common_mode`)), `device: dc_coord`(`DeviceCoord(role, relation, partner)` -- 같은 DC 엣지로 생긴 `cycle_vgs` 없어짐), `graph: dc_tie_breaks`(`TieBreak` decision `input_tie_order` 없어짐) | `dc_writer_plan`(S0, 그대로). 읽는 쪽: `dc_columns`·`dc_window_refine`(쓰기 계획·y 키), `theta_schema`(y 성분), `scc_order`, `achievability`(DOF), 41 §6.7 KVL 출발(U17 ②) | S0 |
| 출력 구조 분류(v1.12.2 card IT-2, 사용자 결정 O-64 (1) -- 계획 N3.8 '출력 구조 분류 -- 규칙 하나') | `node: dc_output_structure` = 출력 포트 넷마다 `"high_impedance"` \| `"kvl_fixed"`(출력 G_vgs 성분에서 W3 목표 핀을 모두 뺀 뒤 F′ = 레일 ∪ 선언 입력 DC에 닿으면 `kvl_fixed`, 아니거나 G_vgs 밖이면 `high_impedance`; W3 출력 여부는 `node.dc_writer`가 정본이라 표지 값 없음 -- 41 §4.7-1a) | `dc_writer_plan`(S0, θ 무관, WRITES에 추가 -- 같은 블록의 G_vgs 엣지 목록(IT-1 뒤, `_TIE` 없음)을 블록 안에서 씀, 둘째 생산자 없음; 권한표 `DC_WRITES` `DC_WRITER_PLAN_WRITER` 행(`E/sizing/s2_values.py:146`)·`E/sizing/CONTRACT.md` 소유표 행 추가 -- v1.12.3). 읽는 쪽(READS만): `icm_config`, `dc_window_refine`, card DE-1 (b) 출력 스윙 | S0 |
| 입력 포트 정의 창(card DE-1 (a) 예약 -- 이 판에서 만들지 않는다) | `node: dc_window_def`(VDS ≥ VDSAT·전도 끝 = 봉인 9 식, tol 없음, '추정') | DE-1 블록(DE-1 design). 읽는 쪽: DE-1 뒤 metric 값 | S2 |
| 입력 포트 다듬은 창(v1.12 card IT-2, 사용자 결정 O-21·O-33 (3)·O-25 (3)) | `node: dc_window_def_refined` = `RefinedWindow(lo, hi, lo_end, hi_end, tol_v, criterion)`, 끝 = `WindowEnd(x, v, reason)`(`v` = 끝 풀이 해의 그 포트 전압 보관, `reason` ∈ {None, `window_end_solve_failed`, `window_end_k_max_exhausted`, `window_end_saturation_unconfirmed`(O-49 P6 -- (ii) 끝 포화 미확인)}). 범위 = 입력 포트 가운데 41 §4.7-4 2 '쓰지 않는 포트'(F 성분 미선언 포트, 선형 감도 끝만 정의되는 구성(`kvl_fixed` 출력 구조·`as_is_single_input` -- O-63 (4))의 입력 포트 전부, 출발 창 없는 포트, 출발 창 미수렴 포트 -- O-64 (2))를 뺀 포트. 기준 칸 `criterion`(O-49 P5, 계획 X-IT12): 이 card = `"tol_judgement"`(+tol_VDsat 지금 식), DE-1 뒤 = `"definition"` | 새 `@compute_block` `dc_window_refine`(`E/sizing/window_refine.py` 진입점 `refine_input_windows`, 41 §4.7-4). 수락 반복·front에서만(`E/search/front_windows.py` `refine_front_windows`가 부른다; 층 0 front 후보 점의 호출 자리는 card LA-1 범위 12 -- O-49 P4) -- 커널·FD 열에서 `computes` 0. 재사용은 graph 규칙(S3 색인 graft)만 -- 새 캐시 없음; 다듬은 결과는 커널 캐시 `sctx.cache`·수락 반복 `parent`에 넣지 않는다(parent는 as-built 커널 결과; parent → child 파생 때 커널 밖 writer 필드는 지워지고 봉인 4가 coverage·서로소를 단언 -- 41 §4.7-3c, O-59 (2)·O-61 P1). 포트 창 = 두 끝 전압 [min, max] ∩ 레일, 한 끝 결측이면 `lo` = `hi` = None(41 §4.7-2). READS에 `node.dc_v`·`node.dc_window` 없음, 출발 창 = `node.dc_window_cfg`(O-49 P1·O-61 P6). 읽는 쪽: `metrics_icm_front` | S2 |
| 봉인점 컨덕턴스 계·인수분해(v1.12 card IT-2, 사용자 결정 O-59 (1)) | `graph: ss_nodal` = `NodalSystem(nodes, fixed, g, factor)`(41 §4.7-3b, `__canonical__` = (nodes, fixed, shape, dtype, g 바이트)) | 새 `@compute_block` `ss_nodal`(`E/metrics/ss_nodal.py` 진입점 `ss_nodal_system`, `SS_WRITES`). 자리: `E/metrics/ss_evaluate.py:101` 뒤, 조건 = `metrics_aux`와 같음(`:107`). 읽는 쪽: `icm_config`·`metrics_aux`(offset_analysis·offset_systematic·block_residual 세 자리 -- 조립 삭제) | S2 |
| 측정 구성·반전 입력 식별(v1.12 card IT-2, O-58 S-1~S-3·O-53 A-1) | `graph: icm_config` = `IcmConfig(config, inverting_port, tied_ports, transfer, undefined)`(v1.12.2: `output_structure` 칸 삭제 -- 출력 구조는 S0 필드 `node.dc_output_structure`를 READS, 사용자 결정 O-64 (1); v1.12.3: 멈춤 S-OS1·S-OS2 갈래는 `config` None + `definitional` code `icm_config_output_root_w3`·`icm_config_differential_output_structure`(41 §4.7-1a); v1.12.5·v1.12.6: 단일 출력 + 선언 되먹임의 DC 되먹임 판정(계획 v6.27 N3.8 경로 판정 -- `icm_config.py` 비공개 `_dc_feedback_reaches`, READS S1 `device.element_class`(MOS 식별 = `ELEMENT_MOS` -- v1.12.7 셋째 커밋, 사용자 O-88)·`device.kind`·`device.pins`·`device.dc_nets`·`device.unsupported`·`node.is_rail`·`node.port_direction`, 측정 구성 선택 전)이 없음이면 `config` None + `icm_config_feedback_no_dc`, 지원 밖 원소(`device.unsupported`)면 `icm_config_feedback_element_unsupported`(v1.12.7, 41 §4.7-3b (1); 차동 출력 결합·`icm_config_feedback_outputs_split`은 S-OS2 일반형 card 몫 -- 사용자 O-87 (1)), 절단 넷 = authoring 순수 함수 `feedback_cut_nets` 하나; `transfer` 출력 전용(resolution 칸 = δA_num = δV_out/레일 폭, δV_out = |z_u|ᵀ|r| -- 계획 v6.24 N3.8 576, 정의 함수 `_transfer_resolution` 하나, 41 §4.7-3b); `kvl` 칸 없음 -- KVL 고정 포트의 끝은 `node.dc_window_cfg` 한 칸, 사용자 결정 O-61 P3, 41 §4.7-3b) | 새 `@compute_block` `icm_config`(`E/metrics/icm_config.py` 진입점 `icm_config_window`, `SS_WRITES`). 자리: `ss_nodal` 뒤. 읽는 쪽: `dc_window_refine`(`config` -- `as_is_single_input` 판정)·`metrics_aux`·`metrics_icm_front`(구성 None 갈래) | S2 |
| 측정 구성 판정 창(v1.12 card IT-2, O-58 S-1) | `node: dc_window_cfg` = `Window`(`node.dc_window`와 같은 꼴; **모든 측정 구성에서 씀**(`as_is_single_input` 포함 -- v1.12.1 W1 철회, θ 프레임 창과 측정 구성 축이 다른 양), 구성 None이면 쓰지 않음; 상태 칸이 커널 미수렴·F 성분 미선언을 이어받음 -- O-61 P4·P5; 선형 감도 끝만 정의되는 구성(KVL 고정 출력 구조·`as_is_single_input`) 포트 끝의 유일한 칸 -- O-61 P3·O-63 (4)) | `icm_config`(평가 커널, 봉인 뒤). 읽는 쪽: 커널 ICMR 제약·커널 metric(`metrics_aux`), `dc_window_refine` 출발 창(DE-1 전, O-61 P6), `metrics_icm_front`(다듬은 창 항목 없는 포트), DE-1 뒤 선언 제약 판정 | S2 |
| 입력 창 metric의 front·보고 값(v1.12 card IT-2) | `graph: metrics_icm_front` = {METRICS_KEY: `IcmWindow`}(41 §4.7-5) | 새 `@compute_block` `metrics_icm_front`(`E/metrics/icm_front.py` 진입점 `icm_front`). 호출 자리 = `dc_window_refine`과 같음. 읽는 쪽: front 점 보고(front 점 run 레코드의 `snapshot_ref` 스냅샷에 실린다 -- run 레코드 키·형식 불변, `E/search/find_front.py` `_point_record`), DEC-98 oracle 대조 값(EO-1 생산자)·U16 보고서. 제약 판정에는 쓰지 않는다(DEC-74). **출력 전용**(EO-1 전 -- 엔진 소비자 없음, 41 §4.7-5 출력 전용 선언; `sources`(포트별 출처 필드 참조)·`model_error_ref`·perf `window_end_solves`도 같음; `IcmWindow`에 `criterion`·`config` 사본 칸 없음 -- v1.12.1 M6) | S2 |
| 게이트 면적·전력 분해능(search가 다시 계산, `E/search/objectives.py:31-45`) | `graph/metrics`: `gate_area_m2`, `power_resolution_w` | `metrics_dc` | S2 |
| 제약 행(`EvalResult.constraints`) | `graph/metrics: constraint_rows` | search 제약 블록. **U17 단계 ②로 이월**(①-c 범위 밖). 미측정(`EvalResult.unmeasured`) 값의 자리는 미정 -- ② design 보완 때 정한다(§2.4.12 Q8) | S2 |
| 레이아웃 결과(`LayoutResult` 값들, 별도 lineage) | S2 `layout` 필드(as-built `E/layout/_ly_fields.py` 필드 이름 그대로) | MOD7 블록 | S2 |
| 레이아웃 보존량 점(v1.11.2, 사용자 결정 O-24 2026-10-19 "1번 권고대로" (가) -- 옛 as-built: `run_layout`이 블록 밖에서 `(kind, L, ID, gm/ID, VDS, VSB)`를 입력 버전으로 삼아 `ly_slices`를 직접 썼고, card B 중간안은 같은 점을 블록 추가 인자로 넘겼다(정본 우회)) | `device: ly_point` = 소자별 `ConservedPoint(kind, L_m, ID_A, gm_id, vds_V, vsb_V)`(`E/layout/contract_output.py`) -- 보존량·동작점만, 참고 W는 넣지 않는다(W만 바뀌면 값이 같아 슬라이스를 다시 조회하지 않는다) | `ly_input`(입력 필드, `LayoutInput`을 풀어 쓴다 -- as-built `E/layout/run.py:50-59` `_input_columns`, role/code/xrunf1b 9d4b28b8에서 신설·c3c50f14 그대로; v1.11.2 O-39 (1) 뒤 `ly_input`은 `LayoutDevice`를 겹치지 않는 네 필드 `ly_point`·`ly_pins`·`ly_w_adjustable`·`ly_attrs`로 나눠 쓰고 `ly_device`는 없다 -- 아래 '`ly_device` 삭제' 행). 칸별 소비자: `kind`·`L_m` = `ly_slice_density`·`ly_canonical_naming`·`ly_pattern_select`·`ly_rows`·`layout_outputs`, `gm_id` = `ly_slice_density`·`ly_canonical_naming`·`ly_finger_candidates`·`layout_outputs`, `ID_A`·`vds_V`·`vsb_V` = `ly_slice_density`·`ly_canonical_naming`·`layout_outputs`(`RealizedDevice`, `E/layout/outputs.py:77-79`). 소자 이름 목록(열의 key)은 이 필드에서 읽는다: `layout_outputs`(:45·:58·:65·:80)와 `convergence.effective_placement`(`E/convergence/effective_placement.py:29`, 이름만 -- 공개 export `F_POINT`로). **사본 부채(사용자 결정 O-27 2026-10-19 "권고대로", 원래 취지와 다름 -- 후속 card까지 잔존)**: `ly_point`와 `LayoutInput` 동작점은 `device: dc_op`(`E/sizing/s2_values.py:381-396`)의 두 단계 사본이다(`dc_op` → `LayoutInput` → `ly_point`). GC-1 부채 목록에 card id를 붙여 등록하고 늘리지 않는다(card id = gain-budget 계획 v6.18 후속 card LI-1). O-39 (1)로 card B는 새 사본을 만들지 않는다(네 필드는 `LayoutDevice` 칸을 나눈 것이라 서로 겹치지 않고, 옛 `ly_point`↔`ly_device` 중복도 없어진다). `ly_input`은 `snapshot.write`로 직접 쓰는 입력 필드라 G-10 계수 밖이다. **LI-1('layout 입력 정본화')에 남는 일**: layout이 봉인 스냅샷의 정본 필드를 직접 READS로 읽어 `LayoutInput` 소자 칸과 네 입력 필드를 1:1로 옮긴다 -- `ly_point` ← `dc_op`, `ly_pins`·`ly_attrs`의 `body`·`diode` ← S1 `device: pins`·`bulk`·`is_diode`, `ly_w_adjustable` ← `dc_coord` writer 역할(쓰기 소자), 참고 `W_m` ← 그 정본(LI-1 design에서 필드 확인). 선결 과제: S1 `pins` 값은 `(("d", 넷), ...)` tuple이라 정준 별칭 번역(`Canon._walk`)이 단자 표지 문자열을 넷·소자 이름으로 잘못 바꿀 위험이 있다(아래 `ly_pins` 행) -- LI-1이 먼저 막는다. 그 밖에 자리표시자 설계점 test 도구, layout W_min 검사(슬라이스 W_need < W_min이면 그 슬라이스 불사용·`w_request`·기록, fail-closed). 옛 LI-1 항목 중 '세 블록 READS 좁히기'·`staged_snapshot` 수정은 O-36 (3) (a)로 card B에 들어왔고, '정준 이름 W 표지를 보존량으로'는 O-36 (3) (c)로 폐기되었다 | S2 |
| 폭 슬라이스별 보존량 실현(`slice_density`) | `device: ly_slices` | 정식 `@compute_block` `ly_slice_density`(v1.11.2, 사용자 결정 O-19 (1) -- writer 이름 그대로, READS device `ly_point`·graph `ly_pdk`(PDK 폭 키는 `ly_pdk`에서 읽는다), WRITES device `ly_slices`, block_version·S3 색인·`RunCounters`·G-10 계수 안). 폭 키 = `projection.value(GRAPH, GRAPH_KEY, F_PDK).slice_width_keys`(같은 값을 추가 인자로 한 번 더 넘기지 않는다 -- 두 경로 금지). 추가 인자는 graph 밖 허용 입력인 LUT memo 하나뿐이다: `_LutHandle(memo)`, 지문(`__canonical__`) = `memo.lut.fp`(memo 상태는 들지 않는다 -- §2.4.6). LUT와 폭 키의 짝은 `run_layout` 입구 검사(`memo.lut.fp` ≠ `pdk.source_fp`면 `ValueError`)가 지킨다. as-built role/code/xrunf1b c3c50f14: `E/layout/run.py:62-85`(`_LutHandle`·`_slice_block`, READS 선언 :74), 호출 `E/layout/run.py:110`, 계약 `E/layout/CONTRACT.md` §4.12 3. 블록 순서 `ly_slice_density` → `ly_canonical_naming`(v1.11.2 O-36 (3), 아래 정준 별칭표 행) → `ly_finger_candidates` → `ly_pattern_select` → `ly_finger_geometry` → `ly_rows`(코드 고정) | S2 |
| `ly_device` 삭제(v1.11.2, 사용자 결정 O-39 (1) 2026-10-19 "권고대로" (b) -- 공개 필드 계약 변경 승인. 옛: `device: ly_device` = 소자별 `LayoutDevice` 통째, 2단계 입력 필드) | 필드 없음. 계약 입력 클래스 `LayoutDevice`(`LayoutInput.devices`)는 그대로 남고, `ly_input`이 그 칸을 겹치지 않게 나눈다: `kind`·`L_m`·`ID_A`·`gm_id`·`vds_V`·`vsb_V` → `ly_point`, `drain`·`gate`·`source` → `ly_pins`, `W_adjustable` → `ly_w_adjustable`, `W_m`·`body`·`diode` → `ly_attrs`, `name` = 네 필드의 열 key. 칸 하나는 필드 하나에만 든다(사본 0) | 옛 소비자를 같은 변경에서 모두 새 필드로 옮긴다: `ly_canonical_naming`(네 필드), `ly_finger_candidates`·`ly_pattern_select`·`ly_rows`(아래 '세 블록 READS' 행), `layout_outputs`(`ly_point`·`ly_attrs`, 실제 읽는 칸 `kind`·`ID_A`·`gm_id`·`L_m`·`vds_V`·`vsb_V`·`diode`·`W_m`, `E/layout/outputs.py:58·70·75·77-79`), `convergence.effective_placement`(:29, 이름만 → `ly_point` 열 key), 공개 export `F_DEVICE`(`E/layout/__init__.py:5·27·37` → `F_POINT`), `E/convergence/CONTRACT.md:59·63`, `E/layout/CONTRACT.md`(:209·280·287·415·452·456·464). test 쪽(test 작성 주체 몫): `tests/layout/test_run.py:408`(`ly_device` 값의 `W_m` 단언 → `ly_attrs` 값의 `W_m`), `tests/layout/conftest.py:323`, `tests/layout/test_outputs.py:87`, `tests/layout/test_contract_input.py:21-36`(공개 필드 이름 표), `tests/convergence/conftest.py:24·75`, `tests/convergence/test_converge_point.py:323`. 옛 서술(v1.11.2 초안: `ly_device`는 `W_m`을 가진 채 유지, 읽기 = `layout_outputs`·정준 이름 블록)은 O-39 (1)로 대체 -- 옛 문장은 계획 history | S2 |
| 레이아웃 소자 부가 칸(v1.11.2, 사용자 결정 O-39 (1)) | `device: ly_attrs` = 소자별 `DeviceAttrs(W_m, body, diode)`(새 frozen dataclass, `E/layout/contract_output.py`). `W_m`은 보존량이 아니라 sizing 참고 W(파생값 W = ID/(ID/W)(gm/ID, L, VDS, VSB), O-24). 이름 충돌 grep(`ly_attrs`·`DeviceAttrs`·`F_ATTRS`, 엔진·tests·docs, 2026-10-19 c3c50f14) 0 | `ly_input`. 칸별 소비자: `W_m` = `ly_canonical_naming`(W 표지 `("W", W_m)`, as-built `canonical_naming.py:55`)·`layout_outputs`(`DeviceLayout.W_m`·`WRequest`, `outputs.py:58·70·75`), `body` = `ly_canonical_naming`(정준 그래프의 bulk 넷, as-built `canonical_naming.py:28·34`), `diode` = `ly_canonical_naming`(`is_diode`, :32)·`layout_outputs`(`RealizedDevice` `not d.diode`, `outputs.py:78`). W만 바뀌면 이 필드만 바뀐다 -- 그래서 `W_m` 변경은 `ly_canonical_naming`과 출력 파생만 다시 만든다 | S2 |
| 레이아웃 소자 단자 연결(v1.11.2, 사용자 결정 O-36 (3) (a) 2026-10-19 "권고대로") | `device: ly_pins` = 소자별 `DevicePins(drain, gate, source)`(새 frozen dataclass, `E/layout/contract_output.py`). 칸 = 세 블록이 읽는 단자 넷만. body는 넣지 않는다 -- 세 블록 본문은 body를 읽지 않는다(행 body 넷은 `ly_row_groups`의 `body_net`에서 읽는다, `rows.py:76`). 값을 `(("d", 넷), ...)` tuple이 아니라 dataclass로 두는 근거: 정준 별칭 번역(`_helpers_alias.Canon._walk`)은 값 안의 문자열을 이름과 정확히 같으면 바꾼다 -- 단자 표지 문자열 `"d"`·`"g"`·`"s"`가 넷·소자 이름과 같으면 잘못 바뀐다. dataclass 칸 이름은 번역 대상이 아니다(as-built `LayoutDevice`와 같은 성질) | `ly_input`(`LayoutInput.devices`에서 `DevicePins(d.drain, d.gate, d.source)`). 칸별 소비자: `drain`·`source` = `ly_pattern_select`(`_helpers_pattern.orient` :14-30, `_branch_ends` `pattern_select.py:99-104`, `Transistor` :156)·`ly_rows`(`_Rows.transistor` `rows.py:89-92`, `_group_transistors` :182-189, `diffusion_geometry` `diffusion.py:36`은 `source`), `gate` = `ly_pattern_select`(`_branch_ends` :101)·`ly_rows`(`_Rows.transistor` :92), 세 칸 모두 `ly_canonical_naming`(정준 그래프의 d·g·s 단자, as-built `canonical_naming.py:28·33`). `LayoutDevice`의 단자 칸을 옮긴 것이라 사본이 아니다(O-39 (1), `ly_device` 삭제) | S2 |
| 레이아웃 W 조정 허용(v1.11.2, 사용자 결정 O-36 (3) (a)) | `device: ly_w_adjustable` = 소자별 `bool`(`LayoutDevice.W_adjustable` -- 봉인 스냅샷 → `LayoutInput` 어댑터가 쓰기 소자 여부로 정한다, `E/convergence/layout_input.py:7`) | `ly_input`. 소비자: `ly_pattern_select`(`_place`의 W_request 가능 판정, `pattern_select.py:258`)·`ly_canonical_naming`(표지 `("adj", …)`, as-built `canonical_naming.py:56`). 옮긴 칸이라 사본이 아니다(O-39 (1)) | S2 |
| 레이아웃 정준 별칭표(v1.11.2, 사용자 결정 O-36 (3) (a)·(c) -- 옛 as-built: 데코레이터 `canonical_names`가 `ly_pattern_select`·`ly_rows` 블록 함수 안에서 `ly_device` 열 통째를 읽어 별칭표를 만들었다, `E/layout/canonical_naming.py:88-105`. 그래서 두 블록의 입력 버전에 `W_m`이 들었다) | `graph: ly_canon` = matching 범위 별칭표 `Canon`(소자·넷·matching 그룹 별칭, as-built `_build(devices, groups, (), (), …)`와 같은 값), `graph: ly_canon_rows` = 행 범위 별칭표 `Canon`(위 + 행 그룹·수동소자 별칭, as-built `_build(devices, groups, row_groups, passives, …)`와 같은 값). 두 필드는 다른 개념이다: 별칭 범위가 다르고 별칭 충돌 검사(충돌이면 빈 `Canon`, `canonical_naming.py:83-84`) 범위도 다르다 -- 하나로 합치면 `ly_pattern_select`가 행 그룹 변경에도 다시 계산된다(as-built `rows=False`의 취지 '안 읽는 블록의 캐시 키를 넓히지 않는다', `canonical_naming.py:90`). 값 지문과 불변 검사는 `Canon`의 dataclass 칸 `pairs`·`orders`만 본다(사실 확인: `fp_of`는 dataclass를 `dataclasses.fields`로만 순회하고 `E/core/fingerprint.py:73-79`, `require_immutable`도 frozen dataclass의 `dataclasses.fields`만 본다 `E/core/immutability.py:22-25`. `_helpers_alias.py:28-38`의 `cached_property` 사전은 둘 다의 밖이고, 같은 칸에서 나오는 파생 캐시라 값 의미를 바꾸지 않는다. `Canon`은 frozen dataclass라 graph 값 불변 조건을 만족한다) | 새 정식 `@compute_block` `ly_canonical_naming`(READS device `ly_point`·`ly_pins`·`ly_w_adjustable`·`ly_attrs`, graph `ly_groups_in`·`ly_row_groups`·`ly_passives`, WRITES graph `ly_canon`·`ly_canon_rows`, block_version·S3 색인·`RunCounters`·G-10 계수 안). **파일**: 새 `E/layout/canon_block.py`, 공개 정의는 `@compute_block` 진입점 `canon_tables` 하나(writer 이름 `ly_canonical_naming`). 별칭표를 만드는 비공개 정의 `_Source`·`_marks`·`_build`는 `canonical_naming.py`에서 이 파일로 옮긴다. 근거: 구조 규칙 A의 '변형군 + 일반 공개 함수' 금지(`tests/structure/README.md:102`의 `decorated_and_plain.py`) -- `canonical_naming.py`에는 일반 공개 함수(데코레이터 공장 `canonical_names`)가 있어 블록을 같은 파일에 둘 수 없다. 규칙 B(다른 모듈의 `_` 이름 import 금지) 때문에 비공개 정의는 쓰는 파일로 옮긴다. 규칙 H로 `tests/layout/test_canon_block.py`가 필요하다(test 작성 주체 몫). 정준 위치(`canonical_form`)는 블록 호출 하나에서 한 번 구하고 두 별칭표가 같이 쓴다. as-built 데코레이터가 읽던 `ly_rejected`는 `_build`가 쓰지 않는 인자다(`canonical_naming.py:67-85` 본문에 `rejected` 사용 0) -- READS에 넣지 않고 그 인자를 지운다. `canonical_names`(`canonical_naming.py`에 남는 유일한 공개 정의)는 별칭표를 만들지 않고 투영의 `ly_canon`(`rows=True`면 `ly_canon_rows`)을 읽어 번역만 한다. 모듈 docstring(:3 '블록은 `reads`에 소자 `ly_device`와 …를 선언해야 한다')은 '블록은 `reads`에 `ly_canon`(또는 `ly_canon_rows`)을 선언한다'로 고친다. **W 표지(사용자 결정 O-36 (3) (c))**: `_marks`의 `("W", d.W_m)`(as-built `canonical_naming.py:55`)는 참고 `W_m` 그대로 두고 `ly_attrs`의 `W_m`에서 읽는다. 근거: 정준 색은 표지 값의 정렬 순위로 정해진다(`graph/canonical_form.py:65`·`_rank` :75-77) -- 다른 표지가 같은 두 소자는 W로만 갈린다. 그래서 정준 이름은 W에 실제로 의존하고, W가 바뀌면 이 블록을 다시 계산하는 것은 정당하다. 다른 두 안은 쓰지 않는다: 슬라이스 실현 W는 `ly_finger`(`ly_finger_geometry`, `ly_pattern_select` 뒤)에서 정해져 `ly_pattern_select`가 읽는 별칭표보다 늦다(블록 순서 충돌), 표지 제거는 W만 다른 소자의 자기동형 구분을 잃는다. 이 블록이 다시 계산되어도 별칭표 값이 같으면 아래 블록은 다시 계산하지 않는다(입력 버전 = 값 지문, `E/core/projection.py` 투영 지문). 블록 순서 `ly_slice_density` → `ly_canonical_naming` → `ly_finger_candidates` → `ly_pattern_select` → `ly_finger_geometry` → `ly_rows`(코드 고정) | S2 |
| 세 블록 READS(v1.11.2, 사용자 결정 O-36 (3) (a) "권고대로" -- 세 블록이 실제로 읽는 칸만 담은 필드로 좁힌다. 옛 as-built 9d4b28b8·c3c50f14: 셋 모두 `ly_device` 열 통째, `finger_candidates.py:36`·`pattern_select.py:278-283`·`rows.py:275-281`) | 칸 실측(master = c3c50f14 같은 파일, 블록 본문과 그 본문이 부르는 함수): `ly_finger_candidates`는 `LayoutDevice`에서 `gm_id`만(`finger_candidates.py:44-47`). `ly_pattern_select`는 `kind`·`L_m`·`drain`·`gate`·`source`·`W_adjustable`(`diode`·`body`는 읽지 않는다 -- dispute 원문의 'diode'는 정준 표지 쪽이다). `ly_rows`는 `kind`·`L_m`·`drain`·`gate`·`source`(`body`는 읽지 않는다 -- 같은 이유). 세 블록 모두 `W_m`을 읽지 않는다. `W_m`·`body`·`diode`·`ID_A`·`vds_V`·`vsb_V`를 읽던 것은 정준 표지(`canonical_naming.py:28-60`)뿐이다 | `ly_finger_candidates` READS device `ly_point`(`gm_id`)·`ly_slices`, graph `ly_pdk`. `ly_pattern_select` READS device `ly_point`(`kind`·`L_m`)·`ly_pins`·`ly_w_adjustable`·`ly_fw_cand`, graph `ly_pdk`·`ly_groups_in`·`ly_rejected`·`ly_canon`. `ly_rows` READS device `ly_point`(`kind`·`L_m`)·`ly_pins`·`ly_finger`, graph `ly_groups`·`ly_groups_in`·`ly_row_groups`·`ly_pdk`·`ly_passives`·`ly_canon_rows`(as-built의 `ly_rejected`는 정준 데코레이터 몫이었고 본문은 읽지 않는다 -- 뺀다). `kind`·`L_m`·`gm_id`는 보존량 점과 같은 개념이라 새 필드를 만들지 않고 `ly_point`를 읽는다(단일 정본 -- 같은 개념 한 필드). 그래서 세 블록의 투영에는 읽지 않는 `ly_point` 칸도 든다(`ly_finger_candidates`: `kind`·`L_m`·`ID_A`·`vds_V`·`vsb_V`, `ly_pattern_select`·`ly_rows`: `ID_A`·`gm_id`·`vds_V`·`vsb_V`): 인과 사슬: 이 안 읽는 칸이 바뀌면 같은 `ly_point`를 읽는 `ly_slice_density`가 `ly_slices`(`W_need`)를 바꾸고, 그것이 `ly_fw_cand`(`ly_finger_candidates`)·`ly_finger`(`ly_finger_geometry`)를 거쳐 세 블록의 다른 입력을 바꾸므로 세 블록 재계산은 어차피 일어난다 -- 추가 재계산은 사실상 0이다. O-36 (3) 문언('실제로 읽는 칸만 담은 필드')과 칸 단위로는 다르나 취지('W만 바뀌면 세 블록 재계산 0')는 같다 -- 사용자 결정 O-39 (2) 2026-10-19 "권고대로" 승인(단일 정본 우선). 칸별 소비자(graph 계산값 소비 규칙, 소비자 ≥1): `ly_point`·`ly_pins`·`ly_w_adjustable`·`ly_attrs`는 각 행. `ly_canon` = `ly_pattern_select`, `ly_canon_rows` = `ly_rows`. **test 도구(test 작성 주체 몫, interface만)**: `tests/layout/conftest.py::staged_snapshot`은 (1) `GraphSnapshot.empty(LY_WRITERS)` 위에 writer `ly_input`으로 device `ly_point`(소자마다 `ConservedPoint(d.kind, d.L_m, d.ID_A, d.gm_id, d.vds_V, d.vsb_V)`)·`ly_pins`(`DevicePins(d.drain, d.gate, d.source)`)·`ly_w_adjustable`(`d.W_adjustable`)·`ly_attrs`(`DeviceAttrs(d.W_m, d.body, d.diode)`)과 graph(key `"layout"`) `ly_pdk`·`ly_groups_in`·`ly_row_groups`·`ly_rejected`(정렬 tuple)·`ly_passives`(이름순 tuple)를 `E/layout/run.py` `_input_columns`와 같은 key·형식으로 쓴다. `ly_device`는 쓰지 않는다 (2) `ly_slices`는 지금처럼 writer `ly_slice_density`로 직접 쓴다(값 = 소자마다 `slice_density(memo, 그 소자의 ly_point 값, 그 kind 폭 키)` -- 슬라이스 조회는 4.2에서 따로 판정하고 블록 단위 test는 그 뒤 블록만 본다. `run.py`의 비공개 `_slice_block`을 부르지 않는다, 규칙 B) (3) 블록은 한 번 만든 `search.open_run()`의 `donors`·`counters`를 키워드로 넘겨 부른다(`compute_block` 필수 키워드, §2.4.4) (4) `BLOCK_ORDER` = `("canon_tables", "finger_candidates", "pattern_select", "finger_geometry", "compose_rows")`(진입점 함수 이름), `block_objects()`에 `"canon_tables"`: `gmid_engine.layout.canon_block.canon_tables`를 더한다 -- 그래서 `upto`가 어느 블록이든 `canon_tables`가 먼저 돈다. **완료 조건(검증 가능, 판정 = verification-auditor가 격리 복제본에서 `RunCounters` 증분과 값 지문으로 잰다 -- 작성자 보고는 증거가 아니다)**: (W-1) 같은 설계점·같은 `LayoutInput`에서 모든 소자 `W_m`만 정확히 2배(k = 2, 2진 지수만 바뀌는 정확 배율)로 바꾼 두 번째 `run_layout`(`previous` = 첫 결과, 같은 실행의 `donors`·`counters`)의 `RunCounters` 증분: `ly_canonical_naming` `computes` +1, `ly_slice_density`·`ly_finger_candidates`·`ly_pattern_select`·`ly_finger_geometry`·`ly_rows` `computes` +0, 그리고 `ly_canon`·`ly_canon_rows` 값 지문이 두 실행에서 같다(같은 배율은 W 표지의 순서·동률을 보존하고 `_rank`는 순위만 쓴다) (W-2) 두 실행의 계산 필드 `ly_slices`·`ly_fw_cand`·`ly_groups`·`ly_dispositions`·`ly_finger`·`ly_rows`·`ly_floorplan`·`ly_diffusion` 값 지문이 같고, `layout_outputs`는 다시 만든다(출력 파생): `devices`의 `W_m`(참고 W)은 새 값이다. `w_requests` 중 참고 W에서 오는 요청 -- `ly_finger` 값이 없는 소자의 `no_usable_slice`(`WRequest(device, W_old_m = W_new_m = 참고 W_m, …)`, `E/layout/outputs.py:59`) -- 의 `W_old_m`·`W_new_m`은 새 값(2배)이고, 계산 필드에서 오는 나머지 요청(`ly_groups`의 그룹 요청, `ly_finger`의 `finger_quantization`)은 두 실행에서 같다(`WRequest`에는 `W_m` 칸이 없다) (W-3) 결정적 입력: 다른 표지(`kind`·`diode`·`ID_A`·`L_m`·`gm_id`·`vds_V`·`vsb_V`·`W_adjustable`·matching 소속)가 모두 같고, W를 빼면 자기동형 궤도가 같은 구조 대칭 쌍인 두 소자 A·B(예: 차동쌍 두 소자)를 둔 회로에서 -- 비대칭 쌍이면 연결 구조가 W보다 먼저 순서를 갈라 지문 차이가 보장되지 않는다 -- 첫 실행 W_A < W_B, 둘째 실행 W_A > W_B(나머지 그대로) -- `ly_canon` 값 지문이 다르다고 단언하고(정준 순위가 뒤바뀌어 별칭이 바뀐다), 이때 `ly_pattern_select`·`ly_rows` 재계산은 정당하다(O-36 (c)), `ly_finger_candidates`는 +0 (W-4) 변경 종류(O-34) = 순수 리팩터링(필드별): c3c50f14 대비 같은 입력에서 위 계산 필드 전부와 `layout_outputs` 칸이 이산 정확·연속 선언 분해능 이내 일치 + 재계산 감소(W-1). 9회로 G-10 판정 1(`recomputes_same_input` = 0)은 새 블록 행을 포함해 유지. 결과 JSON 형식 변경: `perf.blocks`에 `ly_canonical_naming` 행이 생긴다 | S2 |
| 레이아웃 파생 값(`review_needed`·`devices`·`coverage`·`w_requests`·`w_invariant_ok`·`revalidation`) | **필드 아님**. 반환값 함수 `layout_outputs(snapshot)`이 S2 `layout` 필드에서 그때 만든다(사용자 결정 2026-10-12 "4번 권고대로", (A)). U16 결과 JSON이 설계점마다 한 번 부르게 배선하는 것이 U16 완료 조건이다(42 D-LY5). U16 전까지 프로덕션 호출처 0(test만)은 사용자 승인 | -- | -- |
| 국소 봉인 결과(`LocalSeal`) | 국소 스냅샷의 봉인 필드(as-built 봉인 항목 필드 그대로) | 봉인 블록 | L0 |
| 블록 범위 국소 metric(41 §5.3.9: 국소 전력·면적·gain, rout 모드 Z_out) | `graph/local`: `power_w`, `area_m2`, `gain_db`, `z_out_ohm`. key = `local:<블록 키>`(분할 = 그 블록이 덮는 기둥) | 국소 metric 블록(MOD5, 봉인 통과 점에서만) | L0 |
| 층 0 매크로 풀이 결과(41 §5.3.6, `macro_solve(..., node_c, gm_bounds, gain_targets)`) | `graph/layer0: macro`(`MacroResult`). 입력 버전 = (`node_c`, `gm_bounds`, `gain_targets`, gm_id, lengths)를 extras로 넣은 투영 지문 | `layer0_macro` 블록(search) | L0 |
| `comp_approx_gap`(41 §5.5) | `graph/layer0: comp_approx_gap` = {approx: 극점·영점 목록·UGF·PM, mna: 극점·영점 목록·`ugf_ss_hz`·`pm_ss_deg`, gap: (ugf [Hz], pm [deg]) 스칼라 차} | `layer0_assembly_record` 블록(조립 스냅샷) | L0 |
| L-3 회차 기록(41 §5.3.2·§5.3.9: 회차 r의 예산·고정 입력 지문·푼 (bin, 고정 입력 지문) 쌍·조합 front·멈춤 사유) | `graph/layer0: rounds`(회차 순 tuple) | `layer0_budget` | L0 |
| 국소 봉인 결과 캐시(`sctx.local_seal_memo`) | 없음. 국소 스냅샷 + S3 색인 `local`·`solved`(§2.4.5) | -- | L0 |
| 평가 캐시·계산한 키 집합(`sctx.cache`·`computed_keys`; 디스크 실패 캐시 `disk_failures`는 v1.10에서 삭제, 7e1b4be) | 없음. S3 메모리 색인 | S3 기록기 | (b) |
| `cell_floors` 칸 하한, `CurveBook` LUT 파생, `ParamTables`, `edge_costs`, `tol_cells`, `solve_self` 근 | 없음. LUT memo 함수(§2.4.6). v1.9.1 D10: `CurveBook`·`ParamTables`의 LUT 파생과 `edge_costs`(as-built `E/metrics/edge_cost_bounds.py`, metrics → lut)는 U17 ①에서 `E/lut/derived_fns.py` 모듈 함수로 옮기고 as-built `memo.lookup` 형식으로 부른다. `call` 형식 전환은 ③(근거: 동작 변경 회피) | -- | (a) |
| `counters`, `eval_times`, `seq`, `eval_budget`, `deadline`, 블록 계수 | 없음. 실행 계수 | 계수 API | (c) |

#### 2.4.9 G-10 중복 계산 계수와 test

결정 4절이다. 시간은 판정에 쓰지 않고 계수만 쓴다(WP-23).

**계수의 소유**(M8): 실행 하나에 `RunCounters` 하나(`core/run_counters.py`)가 모든 계수와 그 증거 집합을 가진다. 계산 블록 객체(`ComputeBlock`)는 상태가 없다: as-built `_calls`·`_reuses`·`_computes`·`_recomputes`·`_seen_inputs`(f23aec8 `E/core/compute_block.py:129-133`)를 지우고, 호출이 `counters`를 인자로 받는다(§2.4.4 API). 다른 곳의 증거 상태도 옮긴다.

| 증거 집합 | as-built | 상한(실행 평가 수로) |
|---|---|---|
| 블록·분할별 계산한 입력 버전 | `ComputeBlock._seen_inputs`(모듈 수준 블록 객체에 실행을 넘어 남는다) | ≤ Σ_블록 분할 수 × (E_total + 1) (+1 = S0 수준 계산 한 번). v1.11: 블록 결과 색인(§2.4.5)의 키 집합은 이 집합의 부분집합이고 상한도 이 식이다. 식의 전제(커널 평가 수 ≤ E_total)가 as-built에서 깨지는 문제는 §2.4.12 Q12 |
| 퇴출된 memo 키 | `BoundedLRU._evicted`(`E/core/bounded_lru.py:38,58-65`) | ≤ 그 영역의 퇴출 수(U-60 결정 (가): point·curve·root 미적중 수 이하) |
| 디스크 파생표 사건 | `TableCache.events`(`E/lut/table_cache.py:195-228`, 끝없이 늘어나는 tuple) | ≤ 슬라이스 수 × 파생 표 종류 수 × 사건 종류 수 |

**E_total**(이 문서의 유일한 정의): 실행 하나의 커널 평가 수 상한 = E_B(외층 평가 예산, §3.6) + N_T(층 0 평가 예산, 41 §5.8) + R(감도 게이트 묶음 예약 = 2 × `len(sctx.domain.variables)`, v1.11 사용자 결정 X-17(2026-10-15 "나로 해")). E_B를 선언하지 않고 시간 예산에서 유도하는 실행은 유도값 D(그 시간 안 평가 총수)가 E_total이고 E_B = D − N_T − R이다(§2.4.14 (5) C). 이 문서의 다른 곳과 41은 이 정의를 인용한다(§2.4.5 색인 상한 식, §2.4.9 증거 집합 상한, §2.4.12 Q12, §2.4.14 (5) C 모두 이 E_total).

`RunCounters`는 실행 경계에서 새로 만든다(as-built `reset_stats`를 대체). 실행 계수는 graph 밖 (c)이다. v1.11: 블록 결과 색인과 같은 때 같은 쪽이 만든다(§2.4.5 '수명' -- card B 보완 PD-8: 실행 경계 = 두 객체를 만드는 호출자, `run_stage_a`는 필수 키워드로 받는다). 블록 계수 부분(`record`·`snapshot`의 블록 행)은 XRUN-F1 card B가 만들고, `evicted`·`recomputed`·`table_event`·`count`는 U17 ②·③이 더한다. **API**(바꾸는 길은 이것뿐):
- `record(block, part, outcome, input_version)`: outcome ∈ {`reuse`, `graft`, `replay`, `compute`}(`replay` = 실패 재연, X-9). `compute`면 (block, part, input_version)이 이미 있었는지 보고 `recomputes_same_input`을 센다.
- `result(block, part, input_version, ok)`(v1.11): `compute` 뒤 블록 함수가 성공(`ok` = True)했는지 결정적 도메인 실패(`ok` = False)로 끝났는지 알린다(입력과 무관한 예외는 알리지 않는다). 키마다 둘 중 하나만 있어야 한다 -- 섞이면 `ValueError`(§2.4.4 '이식이 비트 동일인 전제'의 fail-closed. 색인이 같은 키를 두 번 계산하게 두지 않으므로 섞임은 색인·순수성 결함의 신호다).
- `evicted(region, key)`, `recomputed(region, key) -> bool`: LUT memo가 퇴출·재계산을 알린다.
- `table_event(event, fn_name)`: 디스크 파생표 사건.
- `count(name, n=1)`: 그 밖의 이름 있는 계수(평가 수, 색인 적중 등).
- `snapshot() -> PerfCounters`: 불변 값으로 내보낸다(결과 JSON `perf`). 읽기는 이것으로만 한다. v1.11 card B 보완(card B J-8, 오케스트레이터 기본안): `PerfCounters`는 `core/run_counters.py` 안 frozen dataclass(그 파일의 진입점 `RunCounters`가 참조하므로 규칙 A 진입점이 아니다) -- 칸 `blocks` = 행 tuple(행 = frozen `(block, part, calls, reuses, grafts, replays, computes, recomputes_same_input)`, (block, part) 정렬, 한 번이라도 `record`된 것만), `block_totals` = 여섯 계수 칸 합. `find_front`가 결과 JSON의 `perf.blocks`(dict 목록)·`perf.block_totals`(dict)로 옮긴다. U17 ②·③이 칸을 더한다.

**계수**(결과 JSON `perf`, D0 계측 형식에 더한다):
- (블록, 분할)마다: `calls`, `reuses`(같은 lineage), `grafts`, `replays`(실패 재연, X-9 -- 검증 N-7로 목록에 더함), `computes`, `recomputes_same_input`. 마지막은 실행 안에서 이미 계산한 (블록, 분할, 입력 버전)을 다시 계산한 수다. `computes`는 블록 함수를 부르기 전에 센다(예외로 끝난 계산도 센다, §2.4.4 호출 규칙 3).
- **실패 재계산**(v1.11, 사용자 결정 X-9 -- Q13 닫힘 = (가)): 결정적 도메인 실패는 색인에 실패 기록으로 등록되고 같은 입력 재호출은 재연(`replays`)이라 계산하지 않는다. 입력과 무관한 예외로 끝난 계산은 등록되지 않으므로 같은 입력으로 다시 부르면 계산하고, 그 재계산은 `recomputes_same_input`에 들어간다. 판정 1은 엄격하다(재계산 0, 예외 열 없음). 앞 회차의 내역 칸 `recomputes_same_input_failed`는 의미가 없어져 만들지 않는다(형식 변경 목록에서도 뺀다).
- **범위**(v1.11, 사용자 결정 X-5): 실행 전체 -- 단계 A부터 탐색 끝까지 그 실행에서 불린 **모든 계산 블록·분할**이다. 옛 범위(as-built `E/search/find_front.py:44-59·131-133`: sizing 계산 블록 12개의 `find_front` 구간 차 합)를 대체한다. `RunCounters`가 실행 경계에서 만들어지므로 구간 차를 계산하지 않는다.
- **결과 JSON 형식**(v1.11, X-5 -- **형식 변경**): `perf.blocks` = 행 목록 `{block, part, calls, reuses, grafts, replays, computes, recomputes_same_input}`((block, part) 정렬, 그 실행에서 한 번이라도 불린 (블록, 분할)만, `calls = reuses + grafts + replays + computes`), `perf.block_totals` = 여섯 계수 칸의 합. 옛 칸 `block_calls`·`block_reuses`·`block_computes`·`block_recomputes_same_input`은 지운다.- 의도적 재계산은 `computes`에 들어가되 원인을 나눠 센다: `fd_step`(θ가 다름). (v1.11: 이 원인 칸은 U17 ②. XRUN-F1은 더하지 않는다)
- LUT memo: 영역마다 `hits`, `misses`, `evictions`, `recomputes_after_eviction`(as-built `LruStats`), 상한 B_r의 항.
- S3 색인: `hits`, `fail_hits`, `kernel_calls`, `outside_domain`(v1.11: 옛 `regenerated_after_release`는 대상 소멸 -- §2.4.5 보존 규칙). 블록 결과 색인: `perf.block_index_entries`(실행 끝 항목 수)와 `perf.block_index_bound`(상한 식의 값, §2.4.5 '상한') -- 보고, §2.4.12 Q12.

**판정**(FAIL 조건):
1. 실행 안에서 (블록, 분할)마다 `recomputes_same_input` = 0(v1.11: 실행 전체의 모든 (블록, 분할) -- 위 '범위'. 계보와 무관하게 같은 입력이면 재사용하므로 lineage가 달라도 예외가 아니다).
2. (v1.10 폐지) 옛 판정 '같은 S0로 두 번째 실행하면 S0 수준 블록 계산 0'은 실행 사이 재사용 제거(사용자 결정 2026-10-15 "나로 해")로 대상이 없다. S0 수준 블록은 실행마다 한 번 계산하고, 그 실행 안 재계산 0은 판정 1이 본다. 번호는 다른 문서의 인용 때문에 비워 둔다.
3. LUT memo `recomputes_after_eviction` = 0(U-60 결정 (가), "U-60은 (가)로"). `evictions`는 보고만 한다.
4. 층 0 조립점 평가에서 공유량이 닿지 않는 분할의 `computes` = 0(모두 `grafts`).
5. as-built `recompute_same_key`(f23aec8 `E/search/kernel.py:111-112`)는 S3 색인 `get` 적중 판정으로 대체되며 0이어야 한다.
6. (v1.11 대상 소멸) 옛 판정 '`regenerated_after_release` = 0'은 실행 안에서 스냅샷을 놓지 않아(§2.4.5 보존 규칙, 사용자 결정 X-2) 대상이 없다. 같은 입력 재계산은 판정 1이 본다. 번호는 비워 둔다.

**test**(R26에 따라 패키지 폴더 체계를 따르고, 9회로 실행은 `E/tests/integration/`):
- `test_g10_no_recompute_9circuits`: 9 library 회로 각각 단계 A부터 층 0 + 외층까지 짧은 평가 예산으로 한 실행에서 돌려 판정 1·3·4·5를 단언한다. S0 수준 블록마다 그 실행의 `computes` = 1(처음 계산)이고 나머지 호출은 `reuses` 또는 `grafts`다. v1.11: XRUN-F1 card B가 판정 1·5로 먼저 만든다(§2.4.14 (5)). 판정 4는 U17 ②, 판정 3은 ③이 더한다.
- (v1.10 삭제) `test_g10_second_run_s0_zero`·`test_s0_snapshot_roundtrip`: 대상 소멸(§2.4.3).
- `test_graft_equals_compute`(국소(`fixed` extras) → 조립 경로 포함: 두 블록 toy에서 각 블록을 이웃 값 `fixed`로 국소 봉인한 스냅샷을 원천으로 조립하면, 비공유 분할은 전부 이식되고 결과 `fp`가 빈 lineage 전체 계산과 같다. v1.11: 분할 `*`만의 형태는 XRUN-F1 card B가 먼저 만든다), `test_index_single_source`(v1.11: 키마다 원천 하나·재등록 `ValueError` -- 옛 `test_graft_donor_order_invariant` 대체), `test_partition_scc_not_split`(SCC가 두 기둥에 걸친 toy에서 한 분할): §2.4.4 불변식.
- `test_lut_memo_single_instance`: 실행 하나에서 만들어진 `LutMemo` 인스턴스 수 = 1(생성 계수).
- `test_lut_memo_purity`: lambda·중첩 함수·`lut` 밖 함수를 `call`에 주면 `TypeError`.
- NFR-4 결정성 test(BLAS 고정·실행 환경 지문·비교기)는 §2.4.13 (5)·(7)에 있다.

#### 2.4.10 강제 장치 (G-8, 사용자 승인 2026-10-12)

네 가지다. G-10(§2.4.9)이 그 위의 보강이다. 구조 규칙 A~K(K = §2.4.3 front 조회 규칙, v1.10)의 정의 파일은 `E/tests/structure/structure_checks.py`이고(EP-3), 여기서는 확장 내용만 적는다.

**① 구조 규칙 G 확장**. as-built 규칙 G는 모듈 수준 가변 대입, `lru_cache`·`cache` 데코레이터, `global` 문만 본다(`structure_checks.py:880-920`, 상수 :55-61). 다음을 더한다.

| 검사 | 거부 대상 |
|---|---|
| 인스턴스·클래스 속성 캐시 | 메서드 안 `self.<a> = {}`·`[]`·`set()`·`dict()` 등 가변 컨테이너 대입, 클래스 본문의 가변 컨테이너 속성 |
| dataclass 기본 컨테이너 | `field(default_factory=dict/list/set)` |
| `cached_property` | 데코레이터 |
| `lru_cache` 호출형 | `functools.lru_cache(...)(f)`, `cache(f)` 같은 호출 |
| 모듈 수준 캐시 객체 | 모듈 수준 `BoundedLRU(...)`·`LutMemo(...)`·`OrderedDict()`·`WeakValueDictionary()` 등 |
| `id(` 호출 | 허용 모듈 밖의 모든 `id(...)` 호출(쓰임과 무관하게. as-built 실측 tests 제외 0건) |
| memo 호출 형식 | `memo.call`의 첫 인자가 모듈 수준 이름이 아님(§2.4.6) |

**허용 모듈 목록**(고정, 이 밖은 예외 없음):
- core graph 모듈: `core/graph_snapshot.py`, `core/compute_block.py`, `core/projection.py`, `core/graft.py`, `core/donors.py`(v1.11), `core/field_value.py`, `core/graph_record.py`, `core/writer_table.py`
- LUT memo와 디스크 캐시: `lut/lut_memo.py`, `lut/table_cache.py`, `core/bounded_lru.py`
- S3: `search/archive.py`, `search/s3_index.py`
- 실행 계수 모듈 하나: `core/run_counters.py`(신규)

목록에 넣지 않는 것과 이유:
- `lut/sweep_memo.py`: XRUN-F1 card A가 지운다(v1.11, §2.4.6 '첫 평가 버림 제거' -- 옛 '단계 ③'). 남아 있는 동안에도 허용하지 않는다.
- `core/fingerprint.py`: 상태가 없다(as-built에 캐시·가변 속성 0). 목록에 넣을 이유가 없다.

as-built 실측(bd19cc6, tests 제외) 확장 검사에 걸리는 곳은 다음과 같다. 단계 ③(§11 U17)이 전부 해소한다.
- 속성 컨테이너: `graph/blocks.py:65-67`, `layout/pattern_select.py:116`, `layout/rows.py:80,86-87`, `metrics/block_param_tables.py:25-26`, `metrics/ss_metrics.py:102`, `search/iv_curves.py:37-40`, `search/macro_poles.py:92-95`, `search/search_context.py:65-66,84`, `sizing/block_columns.py:149,171,177-178`
- `default_factory`: `layout/euler_graph.py:19`, `layout/mirror_trail.py:46`
- `cached_property`: `layout/_helpers_alias.py:28,32,36`
- 계수 상태: `core/compute_block.py:67-71`(f23aec8 `:129-133`), `core/bounded_lru.py:38`, `lut/table_cache.py:199`(허용 모듈이지만 §2.4.9에 따라 `RunCounters`로 옮긴다)

한 함수 호출 안에서 만들고 버리는 작업 객체(그래프 탐색 중간 상태 등)는 캐시가 아니다. 그런 클래스는 허용 목록이 아니라 구조로 고친다. 상태를 함수 지역 변수로 옮기거나, 결과를 불변 값으로 돌려준다.

**② 설계 값 타입 위치 검사**(AST): 설계 값 타입 = §2.4.3 타입 등록부(`core/type_registry.py`)에 등록된 필드 값 형식이다. **v1.10**: 타입 등록부는 코덱과 함께 지운다(§2.4.3). 이 검사의 '설계 값 타입' 목록은 각 패키지의 필드 값 형식 선언(frozen dataclass 정의 모듈)을 AST로 모아 만든다(등록부 없이 같은 목록). 검사는 그 이름 목록으로 소스 AST를 훑는다. 허용 모듈 밖에서 다음을 거부한다.
- **주석**: 인스턴스 속성·클래스 속성·dataclass 필드·모듈 수준 이름의 형식 주석이 설계 값 타입이거나 설계 값 타입을 원소로 하는 컨테이너(`tuple[T, ...]`, `dict[K, T]` 등)인 것
- **대입**: 그런 자리(`self.<a>`, 클래스 본문, 모듈 수준)에 설계 값 타입 생성자 호출 결과나 그것을 원소로 하는 컨테이너 리터럴·컴프리헨션을 대입하는 것
- 제외: 원시 타입(숫자·문자열·bool·None)과 그 tuple, 함수 지역 변수, 반환값, 함수 인자, frozen dataclass 정의 자체(값 형식 선언 모듈)

**③ 계획 SC-a·SC-b lint**:
- SC-a 원시 대입: `object.__setattr__`은 core graph 모듈과 frozen dataclass의 `__post_init__` 정규화(as-built `metrics/records.py`, `metrics/mna_types.py`, `metrics/junction_cap.py`, `core/failure_record.py`, `authoring/topology_model.py`)에서만 허용한다. `GraphSnapshot`·`GraphRecord`·`FieldValue`의 속성과 `tables`·`block_versions`에 대한 대입·변경 호출은 core graph 모듈 밖에서 거부한다. 기존 IC9(`test_no_raw_duplicated_writes`, §10.3)와 같은 검사기를 쓴다.
- SC-b `setdefault`: 기본값 인자가 빈 리터럴 컨테이너나 상수가 아닌 `setdefault`(계산된 값을 '없을 때만' 넣는 형태)를 거부한다. 빈 컨테이너 그룹 묶기(`d.setdefault(k, []).append(x)`)는 허용한다. as-built 실측: `setdefault` 호출 147개 중 해당 16개(`convergence/place_layout.py:60`, `core/pdk_decl.py:283`, `graph/canonical_form.py:135`, `graph/composite_diode.py:103`, `graph/drive_kind.py:73`, `graph/feedforward_cells.py:224`, `graph/gvgs_cycles.py:75`, `graph/views.py:81`, `graph/view_analysis.py:163`, `layout/crossover.py:36,37`, `layout/diffusion.py:58`, `search/search_domain.py:144`, `sizing/writer_plan.py:78,148,151`). 단계 ③에서 각각 고치거나, 설계 값 재사용 건너뛰기가 아님을 보이고 허용 목록에 줄 단위로 근거를 적는다.

**④ 9회로 실행 test**: §2.4.9의 `test_g10_no_recompute_9circuits`가 ①~③의 정적 검사가 못 보는 실행 중 중복을 잡는다. 같은 실행에서 SearchContext·커널 컨텍스트의 도달 가능한 객체를 훑어 설계 값 타입 인스턴스가 graph 스냅샷·S3 색인 밖에 없는지도 확인한다(②의 동적 짝).

#### 2.4.11 tol_I 정정 요약

P N3.6 v6.4다. 상세는 §3.7-3에 있다. `device.dc_gm` 필드 하나를 dc 단계 블록이 쓰고, 봉인 3(tol_I = tol_V × 순환 블록 소자 gm 최댓값), `ss_dev`, 전력 분해능 b_P(`metrics_dc`의 `power_resolution_w`), 영점 상쇄 수동소자 R이 같은 필드를 읽는다. parent(S2p)에 의존하지 않으므로 같은 θ는 parent와 관계없이 같은 봉인 결과를 낸다.

#### 2.4.12 열린 질문과 기본안 (design 기본안(최종 승인에 포함))

design-validator 지적(2026-10-12)에 따라 기본안을 정했다. 사용자 승인 전까지 이 기본안으로 적는다.

| # | 질문 | 기본안 |
|---|---|---|
| Q1 | P N3.3 S0 지문 목록에 PDK 선언 파일 해시가 없었다(출발 구간·면적 선언·접합 출처가 PDK 선언을 읽는다) | 계획 N3.3 S0 행에 PDK 선언 파일 내용 해시를 더했다(v6.4). (v1.10: S0 키는 없어졌다. S0 지문은 S3 출력 폴더 이름·`context_fp`의 구성으로 남는다) -- **결정**(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로")(GQ1, U-72) |
| Q2 | 키가 다른 옛 S0 수준 스냅샷 파일의 정리 | **대상 소멸**(사용자 결정 2026-10-15 "나로 해": S0 스냅샷 파일이 없다). 옛 결정 U-68 기록은 계획 U 표·history에 남긴다 |
| Q3 | 층 0 국소 스냅샷의 보존 | **대상 소멸**(v1.11, 사용자 결정 X-2): 보존은 실행 수명이고 소유자 표가 없다(§2.4.5). 옛 기본안('층 0 단계(모든 회차)'·'외층 시작점 대기열' 소유자, M9)은 history |
| Q4 | 놓은 스냅샷의 θ를 다시 기준점으로 쓸 때의 재계산 | 같은 실행에서 만든 θ의 재생성은 FAIL. (v1.10: 이전 실행 S3 점에서 시작하지 않으므로 그 허용 문장은 대상 소멸) (v1.11: 실행 안에서 놓지 않으므로 재생성이 생기지 않는다 -- 같은 입력 재계산은 §2.4.9 판정 1) -- **결정**(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로")(GQ3, U-73) |
| Q5 | SearchContext의 선언 파생 입력 | §2.4.7 'SearchContext 칸 배정' 표 -- design 기본안(최종 승인에 포함) |
| Q6 | LUT memo 상한·퇴출 판정 | **결정**(사용자 결정 2026-10-12 "U-60은 (가)로"): §2.4.6 (가) |
| Q7 | tol_I가 자기 동작점 gm으로 바뀌면 b_P와 봉인 3 판정이 바뀐다 | 단계 ①에서 9회로 front를 다시 재고, 봉인 3 판정이 바뀐 점(옛 상계로 통과·새 gm으로 거부, 또는 반대)을 회로별로 기록한다 -- **결정**(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로")(GQ4, U-74). **측정 완료(①-c)**: 결과는 history에 기록했다 |
| Q9 | LUT 파생표 디스크 캐시(`GMID_LUT_TABLE_CACHE_DIR`, `E/lut/table_cache.py`)와 test 쪽 캐시(`E/tests/conftest.py:33-49` `_isolate_table_cache` -- 실제 캐시 옆 `lut_table_cache_tests` 폴더를 세션마다 같은 경로로 고정하고 세션 사이에 지우지 않는다)를 실행 사이에 유지하나 | **유지**(U-87, 사용자 결정 2026-10-15 "U-87은 LUT는 관리복잡도가 없다는 네 판단근거에 따라 유지. 나머지는 기본안대로"): 원래 취지('처음 topology를 실행할 때는 항상 계산')의 **예외**로 기록한다. 근거 = 입력 파일(LUT)의 순수 함수 파생표라 키가 LUT 내용 + LUT 코드 버전으로 완결되고, S0 같은 키 관리 부담이 없다. 엔진 캐시와 test 쪽 캐시 둘 다 지금 as-built 그대로다 |
| Q10 | 결정 10의 checkout 무관 성질(경로·줄 정보 제외)을 유지하나 | **유지**(U-88, 사용자 결정 2026-10-15 "U-87은 LUT는 관리복잡도가 없다는 네 판단근거에 따라 유지. 나머지는 기본안대로")(코드 변경 0, 성질이 해롭지 않고 줄 번호 이동만 한 편집이 실행 안 입력 버전을 바꾸지 않는다). 근거였던 다른 checkout의 S0 재사용은 사라졌으나 사용자가 유지를 정했다. `test_compute_block.py`의 경로 무관 단위 test는 남고, 다른 checkout 통합 test(`test_code_hash_checkout.py`)는 S0 적중을 보므로 어느 쪽이든 지운다 |
| Q11 | S3 기록의 실행 사이 재사용 제거(이전 실행 front 점 시작점, 디스크 실패 기록) | **제거**(U-89, 사용자 결정 2026-10-15 "U-87은 LUT는 관리복잡도가 없다는 네 판단근거에 따라 유지. 나머지는 기본안대로" -- 오케스트레이터 기본안 채택). §2.4.3 'S3'. 다른 실행 결과의 출력 조회(`node_across_front`)는 계산 재사용이 아니라 남긴다(U-90, §2.4.3 'front 조회' 행) |
| Q8 | `graph/metrics: constraint_rows`(§2.4.8)에서 미측정(`unmeasured`) 값의 자리 | **열림**: U17 단계 ②로 이월하면서 ② design 보완 때 정한다(①-c 구현에서 드러남). 정하기 전에는 `constraint_rows`를 쓰지 않는다 |
| Q12 | 블록 결과 색인 상한(§2.4.5, = §2.4.9 증거 집합 식 Σ_블록 분할 수 × (E_total + 1))의 실행 중 강제. 사실: 식의 전제 '실행의 커널 평가 수 ≤ E_total'이 as-built에서 깨진다 -- 선언 E_B 40에서 커널 평가 43·49·64·66(4회로), 블록별 서로 다른 입력 버전 최대 63(history H4). 원인: 외층·층 0의 FD 한 묶음(`E/search/fd_jacobian.py:86-111`)과 감도 게이트(`E/search/gate_run.py`, `E/search/find_front.py:84`)가 예산 검사 없이 돈다. 합계(Σ)로는 9회로 모두 식 안이다(최대 1036 ≤ 49 × 41) | **결정 (나)**(U-96, 사용자 결정 X-8 -- 사용자 결정 2026-10-15 "3번 나, 4번 가, 나머지는 8번까지는 권고대로. 9번은 좀더 설명해줘"): 모든 커널 평가(FD 묶음·감도 게이트 포함)를 평가 예산 E_total에 넣는다. 묶음은 시작 전에 묶음 전체가 남은 예산에 들어가는지 확인하고 안 들어가면 시작하지 않는다(평가 수 ≤ E_total 구조적 성립). 색인 상한은 그 결과로 성립하고 등록 때 넘으면 fail-closed. card C(§2.4.14 (5))가 하고, card C 병합 전까지 card B는 실행 끝 보고만. 탐색 궤적 변화는 X-4 기준선 재측정 범위 |
| Q13 | 블록 계산이 예외(후보 실패)로 끝난 (블록, 분할, 입력 버전)을 같은 실행에서 같은 입력으로 다시 부를 때. as-built: 다시 계산해 같은 예외를 내고 계수상 `recomputes_same_input`에 든다(v1.11: X-9로 재연 -- §2.4.9). 측정: 9회로 297건 중 2건(current_reuse·sf_pushpull의 `dc_columns` 봉인 위반), 둘 다 W 출처라 card A 뒤 0으로 예상(history H4) | **결정 (가)**(U-97, 사용자 결정 X-9): 결정적 도메인 실패(N3.14 분류 예외)로 끝난 블록 계산은 실패 기록(불변 `FailureRecord`)을 색인에 등록하고 같은 입력 재호출 때 같은 실패를 다시 던진다(비트 동일). 입력과 무관한 예외는 등록하지 않고 그대로 올린다. 판정 1 엄격(재계산 0). 규칙은 §2.4.4 호출 규칙 3·§2.4.5·§2.4.9 |

#### 2.4.13 결정성(NFR-4): 실행 환경 고정과 검증 기준 (v1.9.4, v1.10 정정)

사용자 결정 2026-10-15 "1안·3안 진행하고 ③ 기준 변경도 승인해"(원문 `_drafts/user_decisions.md` 'NFR-4 BLAS 결정성')다. 1안 = (1)이다(v1.10: S0 키가 없어져 실행 환경 지문은 결과 기록 칸이다 -- (1) '결과 값'). 3안 = 41 §5.13이다. ③ = (2)~(6)이다. 2안(SLSQP를 순수 Python SQP로 교체)은 하지 않는다. BLAS를 거치는 엔진 호출(2026-10-15 grep `linalg.`, tests 제외, 줄마다 확인)은 아래와 같다. 고정은 이 전부를 함께 덮는다. 경위·측정은 history에 있다.

| 묶음 | 자리 | 스레드 의존 |
|---|---|---|
| scipy SLSQP | `E/search/macro_poles.py:345`, `E/search/layer0_center.py:235`·`:374`, `E/search/slsqp_outer.py:195` | **실측 의존**(같은 입력 → 다른 반복점) |
| 복소 `scipy.linalg.lu_solve` | `E/metrics/point_solve.py:46-47`, `E/metrics/sensitivity.py:81-83`(ω > 0), `E/metrics/_helpers_probe.py:125·128·139·140` | **실측 의존**(n = 3, 5~11) |
| 복소 `scipy.linalg.lu_factor` | `E/metrics/point_solve.py:40`(행렬 G + jωC), `E/metrics/sensitivity.py:76`(ω > 0이면 복소, ω = 0이면 실수 `dc_limit_parts`), `E/metrics/_helpers_probe.py:122`(복소 z) | 무관 실측(n = 1~11, 1,000회) |
| 실수 `scipy.linalg.lu_factor`·`lu_solve` | `E/metrics/dc_limit.py:34·41`, `E/metrics/offset_analysis.py:123`, `E/metrics/_helpers_nodal.py:46·66·81`, `E/metrics/_helpers_probe.py:81·86`, `E/sizing/scc_newton.py:47·50` | 엔진 크기에서 무관 실측(n ≤ 39, 2,000회) |
| `numpy.linalg.solve` | `E/metrics/mna_solve.py:35`, `E/metrics/noise_transfer.py:77·91·92`, `E/search/macro_poles.py:206`, `E/sizing/input_window.py:42`, `E/metrics/block_gain_rows.py:15·20` | 무관 실측은 정사각 n ≤ 96까지, n ≥ 128에서 의존 |
| `numpy.linalg.lstsq` | `E/metrics/_helpers_pencil.py:36` | 엔진 크기에서 무관 실측 |
| `scipy.linalg.eig`(일반화) | `E/metrics/_helpers_pencil.py:48` | 엔진 크기에서 무관 실측 |
| `numpy.linalg.norm` | `E/metrics/_helpers_nodal.py:68·70`, `E/metrics/_helpers_pencil.py:50·51·55` | 미측정(판정 허용오차 크기에만 쓰임) |
| 행렬곱 `@`·`einsum` | 여러 곳(numpy가 BLAS gemm을 부를 수 있다) | 중간 크기 `@`·`einsum` 무관 실측 |

'무관 실측'의 출처: `wt/_drafts/engine/NFR4_BLAS_CARD_DRAFT.md` §1.4·§6.3·§6.5 (d). 크기 문턱이 있으므로 '무관'은 지금 회로 크기에서만이다. 고정이 필요한 까닭이 여기에 있다.

**(1) BLAS 스레드 고정 (1안)**

| 항목 | 규칙 |
|---|---|
| 대상 | 프로세스에 적재된 BLAS 라이브러리 전부다. 지금 환경에서는 numpy와 scipy가 각자 싣는 OpenBLAS 둘이다(실측 2026-10-15: numpy 2.4.6 `libscipy_openblas64_`, scipy 1.18.0 `libscipy_openblas`. 실행 시 `get_config`는 각각 'OpenBLAS 0.3.31.188.0 … Haswell'·'OpenBLAS 0.3.31.dev … Haswell') |
| 시점·위치 | `gmid_engine` 최상위 패키지를 import할 때 1회 한다. `gmid_engine/__init__.py`가 신규 `E/core/blas_env.py`의 `pin_blas_threads()`를 부른다. 하위 패키지 import는 언제나 최상위 `__init__`을 먼저 실행하므로 고정이 엔진의 모든 계산보다 앞선다. `blas_env`는 numpy·scipy를 모듈 수준이 아니라 함수 안에서 import한다(지금 core 모듈은 어느 것도 numpy·scipy를 모듈 수준에서 import하지 않는다 -- 2026-10-15 grep, cfe2e31 재확인, 그 상태를 지킨다). **파일·공개 이름(J-1, 오케스트레이터 기본안 -- 사용자 결정 아님)**: 새 파일은 `E/core/blas_env.py` 하나다. 공개 최상위 정의 = `BlasModule`(적재 모듈 하나의 기록, frozen), `BlasEnvironment`(확인 결과 값, frozen·hashable), `loaded_blas_modules() -> tuple[BlasModule, ...]`(적재 모듈 열거와 기호 찾기), `blas_environment() -> BlasEnvironment`(확인·거부·값), `pin_blas_threads() -> BlasEnvironment`(환경 변수·적재·설정 1 뒤 `blas_environment()`로 확인). 규칙 A: 앞 넷은 같은 파일의 다음 정의가 이름으로 부르므로 진입점은 `pin_blas_threads` 하나다. 근거: 고정·확인·환경 값은 'BLAS 스레드 1 고정과 그 확인' 한 개념이고, 확인 없는 고정은 없다(고정이 확인을 부른다). 파일을 나누면 열거·기호 찾기를 두 파일이 같이 써야 해서 공용 helper 파일이 하나 더 생긴다. `core/__init__.py`는 엔진이 쓰는 `pin_blas_threads`·`blas_environment`만 재수출한다(나머지는 test가 모듈 경로 `gmid_engine.core.blas_env`로 쓴다). 이름 충돌 0(2026-10-15 cfe2e31 grep: `blas_env`·`blas_environment`·`pin_blas_threads`·`BlasModule`·`BlasEnvironment`·`loaded_blas_modules`, 엔진·tests·tools). test = `E/tests/core/test_blas_env.py`(규칙 H), `_module_map.py` 항목(진입점 `pin_blas_threads`, 계획 ID NFR-4·EP-9) |
| 방법 | (i) 환경 변수 `OPENBLAS_NUM_THREADS`를 "1"로 둔다. 이것은 이 뒤에 적재되는 라이브러리와 하위 프로세스를 위한 것이다. (ii) numpy와 `scipy.linalg`를 import해 두 라이브러리를 싣는다. 각 라이브러리의 스레드 설정 API로 1을 넣는다. 기호 이름은 라이브러리마다 접두 `scipy_`·접미 `64_`가 다르다(실측: `scipy_openblas_set_num_threads64_`, `scipy_openblas_set_num_threads`). (iii) 같은 라이브러리의 조회 API로 1인지 확인한다. 환경 변수만으로는 고정되지 않는다. 호출자가 numpy를 먼저 import했으면 OpenBLAS가 이미 스레드 수를 정했기 때문이다(실측 아래) |
| 확인 실패 = 거부 | 다음이면 import 시점에 `RuntimeError`를 낸다(fail-closed, 조용한 대체 금지 -- `ComputeBlock.code_hash`의 import 시점 거부와 같은 방식). numpy·scipy 빌드 설정(`show_config`)의 BLAS 이름이 OpenBLAS 계열이 아니다. 그 패키지의 BLAS 공유 라이브러리를 찾지 못한다. 설정·조회 기호가 없다. 설정 뒤 조회 값이 1이 아니다. 지원 범위 밖 BLAS(MKL·Accelerate 등)를 쓰려면 이 표에 그 BLAS의 고정·확인 방법을 더하는 design 변경이 먼저다. 빌드 설정의 출처는 numpy·scipy의 공개 API `show_config(mode="dicts")["Build Dependencies"]["blas"]["name"]`이고, 이름에 `openblas`가 (대소문자 무시) 들어 있으면 OpenBLAS 계열이다(2026-10-15 실측: 둘 다 `scipy-openblas`) |
| BLAS 라이브러리 찾기 | 빌드 설정만 보지 않고 프로세스에 적재된 모듈을 열거한다. 다른 패키지가 세 번째 BLAS를 실을 수 있기 때문이다. 적재 모듈마다 알려진 스레드 API 기호(`openblas_set_num_threads`·`openblas_get_num_threads`의 접두 없음/`scipy_`, 접미 없음/`64_` 조합, `MKL_Set_Num_Threads`·`mkl_set_num_threads`, `bli_thread_set_num_threads`)를 찾는다. OpenBLAS 기호를 가진 모듈은 모두 고정·확인 대상이다. MKL·BLIS 기호를 가진 모듈이 있으면 고정 방법이 이 표에 없으므로 `RuntimeError`다. 실측(2026-10-15, Windows `EnumProcessModules` + `GetProcAddress`, `wt/_nfr4_design_scratch/pin/enum_probe.py`): 모듈 116개 중 OpenBLAS 기호를 가진 것은 numpy·scipy의 두 DLL뿐이었다(이름에 'blas'가 든 scipy 래퍼 `_fblas` 등 4개는 기호가 없어 제외됨). 열거 2.0 ms, 기호 검사 25 ms다(2026-10-15 card 초안 재측정: 엔진을 싣지 않고 numpy·`scipy.linalg`만 실은 프로세스에서 모듈 77개 중 OpenBLAS 기호 모듈 2개, 열거 + 기호 검사 22.6 ms -- 모듈 수는 실린 패키지에 따라 다르다). Linux는 `/proc/self/maps`로 같은 일을 한다(미측정). 열거 방법이 구현되지 않은 플랫폼은 `RuntimeError`다. **범위 밖(문서화)**: 알려진 스레드 API 기호를 내보내지 않는 BLAS는 찾을 수 없다. 이런 BLAS가 실리면 고정이 덮지 못한다 |
| 재확인 | 다음 지점마다 `blas_environment()`를 불러 다시 열거하고 조회만 한다. 다시 설정하지는 않는다. (a) 단계 A 진입(`run_stage_a`, `E/pipeline/stage_a.py`), (b) `build_search_context` 진입(`E/search/search_context.py`), (c) `find_front` 진입(`E/search/find_front.py`), (d) `layer0_start` 진입(`E/search/layer0_center.py`), (e) ε 풀이 한 번마다 시작할 때(`E/search/slsqp_outer.py` `solve_eps` 진입 -- 끝점·ε 풀이와 L-b가 모두 이 함수를 부르므로 함께 덮인다). 적재된 OpenBLAS 기호 모듈 중 조회 값이 1이 아닌 것이 있거나, MKL·BLIS 기호 모듈이 있거나, 위 '확인 실패 = 거부'의 다른 조건이면 같은 `RuntimeError`를 낸다. 실행 중에 누가 스레드 수를 바꿨다는 뜻이므로 조용히 고쳐 덮지 않는다. **비교 기준과 상태(J-2, 오케스트레이터 기본안 -- 사용자 결정 아님)**: 재확인은 무상태다 -- 고정 때의 모듈 집합을 어디에도 보관하지 않고, 지금 적재된 모듈 전부가 위 조건을 만족하는지만 본다. 근거: 규칙 G(모듈 수준 가변 상태·`global` 금지)와 규칙 C(core·pipeline·search는 고정을 부른 루트 `__init__`을 import할 수 없다) 아래에서 고정 때 값을 보관할 자리가 없고, 그 자리를 만들려면 import 시점 모듈 상수(core import 부작용)나 새 인자가 필요하다. 결정성에 필요한 것은 '엔진이 부르는 BLAS가 스레드 1'이고, 새로 실린 OpenBLAS 모듈도 조회 = 1이면 엔진 계산 경로는 바뀌지 않는다. 그 모듈은 재확인을 통과하되 `blas_environment()` 값에 항목으로 들어가므로 `env_fp`가 달라지고, 비교기가 같은 실행 안 두 `env_fp`가 다르면 그 실행을 판정 불능으로 낸다((2) 전제 (다)). 그래서 옛 문장 '새 BLAS 모듈이 생겼으면 `RuntimeError`'는 '새 모듈의 조회 ≠ 1이거나 MKL·BLIS면 `RuntimeError`, 조회 = 1인 새 OpenBLAS 모듈은 `env_fp` 차이로 드러남'으로 바뀐다(옛 design 문장과 다름 -- 보고 대상). 비용은 지점마다 약 27 ms(위 실측)다. 회로 하나의 ε 풀이는 수 회~수십 회라 실행 시간(50~290 s)에 비해 작다. 커널 평가마다 재확인하지는 않는다(평가 수가 수백이고 그 사이 변경은 다음 ε 풀이 시작에서 잡힌다) |
| 결과 값 | `blas_environment()`는 확인 결과를 불변 값으로 돌려준다. 그 core `fp_of`를 **실행 환경 지문** `env_fp`로 결과 기록(단계 A 보고서, S3 runs 줄 -- runs 줄이 `find_front`의 결과 JSON이다, 아래)에 남긴다. 키가 아니라 출력 칸이다(v1.10, 사용자 결정 2026-10-15 "나로 해": 옛 S0 키 (iv)는 대상 소멸). 구성: Python 구현·판, `sys.platform`·`platform.machine()`, numpy·scipy 판, BLAS마다 7칸 (계열, 소유 패키지, 라이브러리 파일 이름, 실행 시 `get_config`, `get_corename`, `get_parallel`, 확인한 스레드 수 -- J-3·interface C1과 같은 칸, v1.11 gap 분석 정정). 재확인도 고정 때와 같이 numpy·scipy 각각의 BLAS 라이브러리가 적재 모듈에 있는지 확인하고 없으면 같은 `RuntimeError`를 낸다(사용자 결정 2026-10-16 N-6). 비교기는 두 실행이 같은 실행 환경인지를 이 값으로 가른다. **기록 자리(J-4, 오케스트레이터 기본안 -- 사용자 결정 아님, 옛 N-6 '출처 하나·`build_search_context` 필수 인자'를 대체)**: 값의 정본은 함수 `blas_environment()` 하나이고, 기록은 그 함수를 부르는 재확인 지점 두 곳이 각자 한다. (i) `run_stage_a`는 재확인 (a)의 `blas_environment()` 반환값(한 번 부름 -- 재확인과 값 만들기가 같은 호출)의 core `fp_of`를 단계 A 보고서 최상위 키 `env_fp`에 둔다(정상·정지 경로 모두 -- 진입에서 만들므로. 보고서 최상위 키 13 → 14). `StageAResult`에는 칸을 더하지 않는다(보고서 dict `StageAResult.report`에 이미 있다. 받아 쓰는 엔진 코드가 없다). (ii) `find_front`는 재확인 (c)의 반환값 `fp_of`를 S3 runs 줄 최상위 키 `env_fp`에 둔다(`find_front`가 만드는 record dict에 넣는다 -- `E/search/archive.py`·`S3Archive` 생성자는 바뀌지 않는다, §2.4.3 'S3 읽기 API' 행의 생성자 불변과 맞다). '결과 JSON'은 `find_front`가 쓰는 유일한 JSON인 이 runs 줄이다(엔진에 다른 결과 JSON 파일이 없다 -- 2026-10-15 cfe2e31 실측. `SearchFront`에는 칸을 더하지 않는다). evals 줄에는 넣지 않는다. 재확인 (b)·(d)·(e)는 값을 기록하지 않는다. `build_search_context` 서명과 `SearchContext`는 바뀌지 않는다. 근거: `env_fp`의 쓰임은 card 1(실행 사이 재사용 제거) 뒤 비교기의 같은 환경 판별뿐이고, J-2 무상태 재확인은 기준 값이 필요 없다. 필수 인자를 더하면 호출부(엔진 0곳, tests 17파일 약 30곳)와 XRUN-F1 card A의 서명 불변 계약을 바꿔야 하는데 얻는 것이 없다(최소 변경). 같은 실행의 두 기록 `env_fp`가 같은지는 비교기 전제 (다)가 본다 |
| 비용 | 측정 3(9회로 단계 A → `find_front`, 순차 실행, LUT 적재 포함) 합: 스레드 1 = 896.4 s, 스레드 18 = 899.4 s. 고정 비용은 잡음 수준이다 |
| 쓰지 않는 것 | `threadpoolctl`은 이 환경에 설치돼 있지 않다(2026-10-15 확인). 쓰려면 새 의존성이 되므로 쓰지 않는다. 기존 test 환경 고정(`E/tests/conftest.py:21-25` 코드·`:15-20` 주석 -- cfe2e31 실측, 옛 문장 '23-27'을 정정, `E/tests/convergence/test_converge.py:243`, `E/tests/integration/test_no_s0_files_written.py:101` 하위 프로세스 허용 env의 `OPENBLAS_NUM_THREADS="1"`과 그 docstring `:7`)은 이 card의 같은 변경에서 거둔다(J-11 -- 대체한 옛 코드는 같은 변경에서 지운다. 남기면 그 test가 엔진 고정을 거치지 않는다) |
| test 주입·관찰 지점 | (J-3, 오케스트레이터 기본안 -- 사용자 결정 아님. 선례: XRUN-F1 card A J-3·card 1 J-5의 모듈 속성 교체 계약) 엔진 공개 서명에 test 전용 인자를 더하지 않는다. 대신 (i) 모듈 속성 `gmid_engine.core.blas_env.loaded_blas_modules`를 교체 지점으로 고정한다 -- 이름·인자 없는 서명·반환 형식(`BlasModule` tuple)·같은 파일의 `blas_environment`·`pin_blas_threads`가 모듈 전역 이름으로 부르는 방식을 바꾸지 않는다. `BlasModule` 칸 = `path`(str), `family`(`"openblas"`·`"mkl"`·`"blis"`), `set_threads`·`get_threads`(인자 하나·인자 없는 호출 가능 객체, 그 모듈이 기호를 내보내지 않으면 None), `config`·`corename`·`parallel`(인자 없는 호출 가능 객체, 기호가 없으면 None). None의 뜻(N-7): `family` `"openblas"`인 기록의 `set_threads`·`get_threads`가 None이면 '설정·조회 기호 없음'이라 `RuntimeError`다. `config`·`corename`·`parallel`이 None이면 거부하지 않고 `BlasEnvironment` 그 항목의 해당 값 칸이 None이 된다. `family`가 `"mkl"`·`"blis"`인 기록은 칸 값과 무관하게 있는 것만으로 `RuntimeError`다. **`BlasEnvironment`의 BLAS 항목**(N-3): 항목 = (family, 소유 패키지, 파일 이름, config, corename, parallel, 확인한 스레드 수). 소유 패키지 = 모듈 파일이 적재된 최상위 Python 패키지의 폴더(`sys.modules`의 그 패키지 `__file__`이 있는 폴더) 또는 그 형제 폴더 `<패키지>.libs` 안에 있으면 그 패키지 이름(지금 `numpy`·`scipy`), 아니면 None. 파일 이름 = 경로의 마지막 성분(절대 경로는 넣지 않는다 -- 같은 설치를 다른 폴더에 둔 것만으로 `env_fp`가 갈리지 않게). 항목 순서 = 항목 tuple의 사전식 정렬(None은 빈 문자열로 비교) -- 적재 순서·열거 순서와 무관하다. test는 Python 호출 가능 객체로 만든 가짜 기록(설정이 듣지 않음·조회 2·기호 없음·MKL·BLIS)을 돌려주게 바꿔 `blas_environment()`·`pin_blas_threads()`의 `RuntimeError`를 본다. (ii) 빌드 설정은 numpy·scipy 공개 API `show_config`를, 플랫폼은 `sys.platform`을 부르는 때 읽는다 -- test는 하위 프로세스에서 이 값을 바꿔(`numpy.show_config` 교체, `sys.platform` 대입) import 시점 거부를 본다. (iii) 실제 라이브러리로 만드는 경우(ctypes로 numpy 쪽 설정 API에 2 → 재확인 `RuntimeError`, numpy OpenBLAS DLL을 다른 이름으로 복사해 `ctypes.CDLL` → 재확인 통과·`BlasEnvironment`의 BLAS 항목 3개·`env_fp` 달라짐)는 교체 없이 하위 프로세스로 본다. 근거: 공개 API 변경 최소, 선례와 같은 방식, 컴파일러(가짜 DLL 빌드) 의존을 test에 들이지 않는다 |

고정 방법 실측(2026-10-15, `wt/_nfr4_design_scratch/pin/pin_probe.py`, 프로세스마다 장난감 SLSQP 60문제와 복소 `lu_solve` 300회의 결과 해시):

| 바깥 `OPENBLAS_NUM_THREADS` | 프로세스 안 조치 | 두 라이브러리 조회 값 | 결과 해시 |
|---|---|---|---|
| 1 | 없음 | 1·1 | 기준(스레드 1 경로) |
| 8 | 없음 | 8·8 | 다름 |
| 미지정 | 없음 | 18·18 | 다름(8과 같음) |
| 미지정, 8 | numpy import 전에 환경 변수 1 | 1·1 | 기준과 같음 |
| 미지정 | numpy import 뒤에 환경 변수 1 | 18·18 | 다름 → 환경 변수 방식은 import 순서에 기댄다 |
| 미지정, 8 | import 뒤 설정 API 1 | 1·1 | 기준과 같음 |

**(2) 검증 기준 (③)**

| 비교하는 두 실행 | 판정 |
|---|---|
| 같은 실행 환경(결과 기록의 `env_fp` 같음) · 같은 코드(엔진 코드 지문 같음) | **1차 검사: 비트 동일 집합이 비트 동일.** 다르면 FAIL이다. 필드별 비교로 넘어가지 않는다. 비트 동일 집합·전제·판정 불능은 아래 |
| 다른 실행 환경, 또는 수치 보존 리팩터링(코드가 다르고 spec card가 '수치 보존'이라고 선언한 변경) | **필드별 비교.** 이산(D)은 정확히 같다. 연속(C)은 \|Δ\| ≤ 분해능이다(같은 구역의 D가 모두 같을 때만 C를 비교한다 -- D가 다르면 이미 FAIL). 경로 계수(K)는 빼고 보고만 한다(Q-N2 확정, 사용자 결정 2026-10-15 "기본안대로 진행해", U-78 -- 기준 약화 승인). 전제·판정 불능은 1차 검사와 같다 |
| 같은 실행 환경·같은 코드, 입력 표현만 다름(계획 IC2 `test_order_shuffle_invariance`: 소자 dict·그룹 순서·set 순회를 섞은 입력) | 계획 IC2 문언은 '이산 완전 일치, 노드전압 ≤ tol_V, 전류 ≤ tol_I, 그 밖의 연속 ≤ tol_V 섭동의 감도 전파값'이다. 새 NFR-4 첫 문장('모든 반복은 정렬된 시퀀스 위에서')을 따르면 순서만 다른 입력은 정준화 뒤 같은 입력이므로 비트 동일이어야 한다. as-built test는 이미 비트 동일을 단언한다(`E/tests/sizing/test_size_and_seal.py:491-512`, 스냅샷 `fp` 같음). **비트 동일이다**(Q-N10 확정, 사용자 결정 2026-10-15 "기본안대로 진행해", U-86 -- 계획 IC2 문언을 비트 동일로 정정함). 비교 집합·전제는 1차 검사와 같다. 출처(N-1): 계획 N4.1 IC2 행(v6.9부터 비트 동일 문언). as-built test가 덮는 범위는 sizing 스냅샷 단계뿐이다(`test_size_and_seal.py:491-512`, `size_and_seal` 두 번) -- 단계 A부터의 파이프라인 단위 순서 섞기 test는 없고, 그것은 IC2 test 작성 몫이다 |

**비트 동일 집합**: 회로마다 S0 수준 스냅샷의 모든 필드 값(v1.10: 디스크 파일이 없으므로 실행 하네스(test 쪽)가 메모리 스냅샷을 필드별로 덤프한다 -- `fp_of`와 float는 `float.hex`, 엔진 코덱 아님), 단계 A·B 보고서, 층 0 결과(`Layer0Result`), 탐색 결과(front·pending·unmeasured 점, ε 풀이 기록, `failed_eps`, `perf`), S3 evals·runs 줄 전부에서 **시간 칸(T 부류, (3))만 뺀** 것이다. 시간 칸은 `perf.wall_s`·`perf.eval_time_median_s`(`E/search/find_front.py:129-130`), 수렴 `perf` `wall_s`(`E/convergence/converge.py:96`)다. 시간이 아닌 `perf` 계수(커널 호출 수·고유 키 수·`stops_*` 등)는 집합에 남는다: 아래 전제에서 이 값들은 시간에 기대지 않고, 측정 3의 같은 스레드 반복에서 9/9 회로 같았다.

**벽시계에 기대는 엔진 경로**(2026-10-15 grep `perf_counter`·`deadline`·`median`, tests 제외, 전수): (i) 바깥 정지 `wall_budget` -- `E/search/layer0_center.py:265-266`(층 0·Halton 시험·보정의 `_budget_stop`), `E/search/slsqp_outer.py:97-98`(ε 풀이), `E/search/l_bin_search.py:34`(v1.11 card C 뒤: 이 셋은 `E/search/search_stop.py` `search_stop` 한 자리로 모이고 `_budget_stop` 정의는 없어진다 -- §2.4.14 (5) C. 이 card(NFR-4 card 2, X-19로 card C보다 먼저)가 넣는 L-b 정지 사유 반환은 card C가 이어받는다: 사유 값 = `search_stop` 반환값, 바퀴에 수락이 없어 끝나면 `converged`). 기준 시각은 `E/search/find_front.py:76-78`(`deadline` = 시작 + `front_budget_s`). (ii) 평가 수 예산의 시간 유도 -- `E/search/kernel.py:153-158`(cfe2e31 실측, 옛 문장 '160-165'를 정정)이 E_B를 선언하지 않았을 때 ⌊B / 평가 시간 중앙값⌋으로 한 번 정한다(`E/search/eval_budget.py:35`). (iii) Halton 시험 한도 -- `E/search/layer0_center.py:590`은 `deadline`이 있으면 시험 수 상한을 두지 않는다. 원뿔 밖 점은 커널 0이라 평가 수 예산으로 끝나지 않고 벽시계로만 끝난다. (iv) 기록만 하는 시간 -- `E/search/kernel.py:116·152`(`eval_times` 시작 시각·추가, cfe2e31 실측, 옛 문장 '123·159'를 정정), 위 시간 칸. ε 게이트의 `costs`(`E/search/eps_sweep.py:77·91`)는 커널 호출 수라 시간이 아니다.

**1차 검사의 전제**(셋 다 실행 기록에서 확인): (가) E_B가 선언돼 있다(`SearchSettings`의 평가 수 예산이 None이 아님 -- 결과 `perf.eval_budget_source`가 선언을 가리킴). (나) 벽시계 정지가 없다: `perf.stops_wall_budget` = 0이고, 층 0 `stop`·Halton 사유·ε 풀이 `stop`·`aborts`·`failed_eps`·L-b 종료 사유 어디에도 `wall_budget`이 없다. **as-built 공백**: L-b(`polish_l_cells`, `E/search/l_bin_search.py:32-34`)의 정지는 bool만 내고 `:41`·`:49`에서 조용히 끝나며, `best`가 없는 `solve_eps` 결과는 `:63-65`에서 버려져 `E/search/find_front.py:137`의 `stops_wall_budget`에 세지지 않는다. 그래서 지금은 (나)를 기록에서 확인할 수 없다. 이 card의 code 몫으로 L-b 종료 사유(`converged`·`eval_budget`·`wall_budget`)를 결과 기록에 남기고(아래 (5) 'L-b 정지 사유 기록'), 그 전에는 (나)를 확인할 수 없으므로 L-b가 돈 실행은 판정 불능이다. (다) 같은 실행 안의 `env_fp` 기록(단계 A 보고서, S3 runs 줄 -- (1) '결과 값')이 모두 같다(J-2·J-4: 실행 중 새 BLAS 모듈이 실리면 여기서 드러난다). 탐색이 없는 실행(단계 A·B `review_needed` -- 예: `ngcc_3stage_ff`)은 단계 A 보고서 하나뿐이라 (다)가 그 하나로 성립한다. 탐색이 있는 실행인데 runs 줄이 없으면(`sctx.archive`가 None -- `archive_root` 없이 돌린 실행) (다)를 확인할 수 없으므로 판정 불능이다(N-4). 실행 하네스는 탐색 실행마다 `archive_root`를 준다. 전제를 하나라도 어긴 실행은 **판정 불능**이다(PASS도 FAIL도 아니다). 판정 불능이 하나라도 있으면 그 비교는 완료되지 않은 것으로 보고한다. 실측(2026-10-15): 측정 3과 이 설계 측정의 실행 191개(9회로, E_B = 40 선언, B = 600 s)에서 `stops_wall_budget`은 탐색이 있는 171개 모두 0이고, 다른 칸에도 `wall_budget`이 없었다(`ngcc_3stage_ff` 20개는 탐색 없음). 같은 스레드 반복은 9/9 회로에서 측정 3이 기록한 칸 전부(이산·연속, S0 `search_base.fp`, 단계 A·B 스냅샷 지문, `context_fp`)가 비트 동일했다. 측정 3이 기록하지 않은 칸(S3 줄 원문, 보고서 원문)의 비트 동일은 아직 재지 않았다. 비교기 첫 실행이 이것을 판정하고, 다르면 FAIL이다(미루는 것이 아니라 이 card의 완료 조건이다 -- (5)).

**(3) 필드 분류**

| 부류 | 정의 | 예 |
|---|---|---|
| **D 이산** | 값 형식이 bool·int·str·이름 tuple·frozenset·enum인 엔진 출력 칸, 그리고 연속 칸이 정의되었는가(None·NaN·무한 대 유한) | 단계 상태·정지 사유, 매크로 기록 코드·선택된 다중 출발·`macro_failed`, 출발 구간 충돌(소자, 양, 경계 키)·비활성·`uncovered`·사다리 칸 수와 `cells`·행 bin·경계 출처, 층 0 `hard_ok`·`stop`·`start_status`·`origin_point`·`aborts`·`frozen`·`restarts`, 시작점 목록(id·출처·`cells`), ε 풀이 `stop`·`aborts`·`frozen`·`restarts`·`best`(status, seq), front·pending·unmeasured 점 집합(점 id = 출처 tag), 평가마다 status·실패 class·실패 소자·active 제약 집합·cone active·미측정 목록·제약 행 이름, `failure.margin`이 있는가, S0 수준의 구조 값 전부(S1·S1v·θ 스키마·묶음·변수 목록 등) |
| **C 연속** | D·K가 아닌 float 칸 | (4) 표 |
| **K 경로 계수** | 풀이기·탐색이 걸은 길이를 세는 정수 | SLSQP `nit`, 층 0·ε 풀이 `iterations`, 풀이 이력 길이(`n_history`), `MacroResult.sweeps`, 커널 호출 수·평가 수·고유 키 수, 시간이 아닌 `perf` 계수, 기록 detail 안의 풀이기 원문 메시지. 1차 검사(같은 환경)에서는 비트 동일 집합에 든다. 필드별 비교에서는 빼고 보고만 한다(Q-N2 확정) |
| **T 시간** | 벽시계 값 | `perf.wall_s`, `perf.eval_time_median_s`, 수렴 `perf` `wall_s`, `eval_times`. 어떤 비교에도 넣지 않는다(보고만) |

엔진 출력이 아닌 것(풀이기 호출마다의 x·`status`·`success` 같은 관찰 기록)은 비교 대상이 아니다. 엔진이 그 결과로 내린 판단(D)만 비교한다.

**(4) 연속 필드의 분해능** -- 출처가 있는 것(비교는 절대차 \|Δ\|, 좌표가 ln이면 ln 좌표에서 잰다):

| 필드 | 좌표·단위 | 분해능 | 출처 |
|---|---|---|---|
| `ConstraintRow.c`(평가 c·cone, 층 0 경성 행) | 분해능 단위(여유 / 그 행 분해능) | 1 | `E/search/constraints.py:27-37`, `E/search/cone_rows.py:17-29` |
| W(`start.row` `w_m`, `dc_op.W`) | m | 제조 격자 `grid_m` | PDK `manufacturing_grid_m`, `E/search/search_values.py:79-80` |
| 면적(`area_m2`·`gate_area_m2`·`area_est_m2`·출발 구간 상태 면적) | m² | b_A = `grid_m` × `w_min_m` | `E/search/search_domain.py:172`, `E/search/search_values.py:76·80` |
| 전력 `power_w` | W | b_P = Σ_레일 \|V_k\|·tol_I,k | `E/metrics/dc_metrics.py:11` |
| metric 값(평가의 metric 열) | 그 metric 단위 | 그 값의 `MetricResult.resolution`. None이면 **판정 불능**이다(N-7: 그 metric의 상류 허용오차가 정해지지 않아 감도 전파를 만들 수 없다) | `E/metrics/mna_types.py:365`(NFR-5 '격자 분해능') |
| `kcl_residual_a`(레일 전류 합, 0이어야 함) | A | Σ_레일 tol_I,k(b_P와 같은 tol_I,k) | `E/metrics/supply.py:70`, `E/metrics/dc_metrics.py:11` |
| θ 성분(평가 θ, 층 0·탐색 시작점 θ, 층 0 최대-최소·외층 풀이의 x) | 변수 좌표(전류·저항·수동소자 = ln, `ln_idu`, `y`, L) | 그 점의 FD 스텝 hᵢ(기준 실행의 같은 점) | `E/search/fd_jacobian.py:9-20`(규칙), `:41-82`(`_steps`). hᵢ는 그 점 스냅샷의 `dc_op`·`dc_tol_v`가 있어야 계산된다. 실행이 끝난 뒤 전체 스냅샷이 남는 점은 S3 `snapshots/`의 front 점과 채택 해뿐이다(§2.4.5 보존 규칙 -- v1.11: 실행 안에서는 모든 계산 원천을 보존하지만 실행 끝에 버린다. 비교기는 실행 기록을 실행 뒤에 읽는다). 그래서 **다른 환경 비교에서 그 밖의 평가점 θ(층 0 시작점·외층 반복점 포함)는 판정 불능**이다(N-8) |
| 층 0 `t`, 층 0 최대-최소 x의 t 성분 | 봉인 허용오차 단위 | 1 | `E/search/layer0_center.py` 모듈 docstring 3('t 의 단위 = 허용오차 한 칸', ftol 1) |
| `failure.margin` | 그 실패 class 허용오차 단위 | 1 | `E/core/margin.py:1-8`(P N3.14 정규화식) |
| 노드 전압·소자 전류 | V·A | tol_V·tol_I | 계획 IC2(같은 출처), `E/sizing/seal_tolerances.py:5-11`. 노드 전압의 tol_V = 그 노드에 채널이 닿는 MOS의 `dc_tol_v` 최솟값(Q-N3 확정, 사용자 결정 2026-10-15 "기본안대로 진행해", U-79). 채널이 닿는 MOS가 없는 노드(수동소자·이상원만 닿음)는 tol_V 출처가 없어 **판정 불능**이다(N-10) |

출처가 없는 것: 측정 3에서 차이가 났고 선언 분해능이 없는 필드다. `layer0/centre_u`, `layer0_center:235`의 x(ln 전류 비), 출발 구간 행 `ln_idu`·`i_start`·`gm_id_lo`·`gm_id_hi`·`gm_id_chosen`·`source[].value`, 사다리 θ(L 성분 밖)·`current_ref`, `conflicts`의 `gap`·`bound`가 여기에 든다. 매크로 칸 전부(gm·용량·저항·`ugf_hz`·`pm_deg`·극점)와 매크로 풀이의 x도 여기에 든다. 근거: (i) 매크로의 √tol은 \|ln \|H(jω_GBW)\|\|에 걸린 허용폭이지 x나 gm에 걸린 것이 아니다(`E/search/macro_poles.py:353`). (ii) pm·두 번째 극점의 채택 판정(`:353-354`)은 한쪽 부등식(pm ≥ 목표 − √tol, \|p₂\|/ω_np − 1 ≥ −√tol)이다. 한쪽 한계는 받아들여진 두 해의 차를 묶지 못하므로 분해능이 아니다. (iii) 판정한 pm은 ω_GBW에서 잰 `mag_pm` 값이고, 저장되는 `MacroResult.pm_deg`는 실제 UGF에서 `net.analyse`로 잰 다른 값이다(`:365`). 'PM 제약이 활성일 때만'으로 좁혀도 (ii)·(iii)이 남으므로 그 안을 택하지 않고 감도 전파 묶음으로 옮긴다. 위 표의 '평가 θ'·`kcl_residual_a`·`failure.margin`은 이 절에서 출처를 찾았다. 나머지는 상수를 짓지 않고 **상류 허용오차 섭동의 감도 전파값**(계획 IC2의 '그 밖의 연속 필드' 형식)을 비교 폭으로 쓴다(Q-N3 확정, 사용자 결정 2026-10-15 "기본안대로 진행해", U-79). 계산: (i) 매크로 칸·매크로 x·출발 구간 필드(행·사다리·`conflicts`)의 상류는 매크로 채택 허용폭이다. 비교기는 기준 실행의 매크로 해 gm 벡터를 ln 좌표에서 ±√tol(`E/search/macro_poles.py:282·353`) 움직여 출발 구간 계산을 두 번 다시 하고, 칸마다 \|Δ\|의 큰 쪽을 폭으로 쓴다. 이 계산에 필요한 엔진 진입(매크로 해 주입)은 **후속 card NFR4-F2로 옮긴다**((8) 아래 -- 범위 변경, 사용자 승인 (사용자 결정 2026-10-15 "U-87은 LUT는 관리복잡도가 없다는 네 판단근거에 따라 유지. 나머지는 기본안대로", 원문 `_drafts/user_decisions.md` 'U-87~U-89·NFR4-F2·front 조회')). 그 card가 끝나기 전에는 (i)의 칸들이 판정 불능이다. (ii) `layer0/centre_u`와 `layer0_center:235`의 x는 ln 전류 좌표라 감도가 1이다. 폭 = 기준 실행 층 0 첫 평가점의 θ 전류 FD 스텝 hᵢ 최솟값(`E/search/fd_jacobian.py:69-71`)이다. 그 점의 스냅샷은 보존되지 않으므로(§2.4.5) 지금 규칙으로는 이 두 칸도 판정 불능이다(N-8). 비교기가 이 계산에 필요한 자료나 진입(매크로 해 주입, 층 0 첫 평가 스냅샷)을 갖지 못하면 그 칸은 판정 불능이다.

출처가 있어도 측정 차이가 분해능을 넘는 필드가 있다. 측정 3 스레드 1 대 8의 같은 점 비교에서 선언 분해능을 넘은 회로는 nmcnr_amplifier 하나다(`start.row` `w_m` 최대 15 격자 칸, `area_est_m2` 14.8 b_A. sf_pushpull·two_stage_ota·two_stage_ota_sf는 `w_m` 0.0006·0.0004·0.0001 격자 칸, `area_est_m2` 0·0.04·0 b_A -- 2026-10-15 재측정, 옛 문장 '4회로'를 정정). 이 필드는 매크로 풀이 하류라(매크로 해는 \|ln \|H\|\| ≤ √tol 안에서 같은 해로 받아들여진다) 선언 분해능보다 덜 재현된다. 문언대로 하면 다른 환경 비교가 nmcnr에서 FAIL이다. 감도 전파 폭이 이것을 덮는지(N-9) 선형 추정(2026-10-15, 측정 3 원자료): nmcnr의 같은 실행 쌍 매크로 gm 차 최대 \|Δln gm\| = 2.02e-6이고 전파 폭의 상류 섭동 √tol = 1.22e-4라 비는 60.4다. 차이가 gm 차에 선형이면 전파 폭 ≈ 903 격자 칸·895 b_A로 15 격자 칸·14.8 b_A를 약 60배로 덮는다. 실제 전파 계산이 아니라 선형 가정 추정이다. 폭이 측정 차이보다 훨씬 넓으므로 이 칸들의 C 비교는 약하다. 그래서 이런 칸의 비교 폭은 max(선언 분해능, 위 감도 전파값)이다(Q-N4 확정, 사용자 결정 2026-10-15 "기본안대로 진행해", U-80). 감도 전파값을 만들 수 없으면 그 칸은 판정 불능이다.

**(5) 비교기 위치와 감사 사용**

- **이 card의 완료 조건**(v1.10 정정): Q-N2·Q-N3·Q-N4·Q-N6·Q-N7·Q-N9·Q-N10은 결정대로 쓰고, Q-N1·Q-N5·Q-N8은 사용자 결정 2026-10-15 "나로 해"로 대상 소멸이다. 완료 조건은 (i) L-b 종료 사유가 결과 기록에 남는 것, (ii) 결과 기록 두 곳(단계 A 보고서, S3 runs 줄 -- (1) '결과 값')에 `env_fp`가 남는 것, (iii) 비교기 첫 실행(9회로, 같은 환경 두 번)에서 비트 동일 집합 전체가 같고 판정 불능 0인 것, (iv) 42 D-ND4가 알려진 결함으로 기록되고 후속 card NFR4-F1이 등록된 것이다. 옛 (iii) Q-N5 구현은 대상 소멸이다. 매크로 해 주입 진입(NFR4-F2)은 (i)~(iv)에 필요하지 않다: 같은 환경 1차 검사는 비트 비교라 분해능이 필요 없다. 필드별 비교(다른 환경)의 판정 불능 칸은 완료를 막지 않는다. U17 ②의 기준선 측정은 같은 환경 1차 검사만 쓰기 때문이다.
- **위치**(J-8, 오케스트레이터 기본안 -- 사용자 결정 아님): test 기반이다. 도우미 모듈 둘 -- 비교기 `E/tests/integration/nfr4_compare.py`(부류 판정·분해능 식·1차 검사·필드별 비교·보고 JSON, 엔진을 import하지 않는다)와 실행 하네스 `E/tests/integration/nfr4_run_dump.py`(회로 하나의 사슬을 그 프로세스에서 돌려 실행 기록을 파일로 덤프). 단위 test는 `E/tests/integration/test_nfr4_compare.py`. 둘로 나눈 근거: 비교(순수 함수)와 엔진 실행은 다른 개념이고, 비교기 단위 test가 엔진 실행 없이 돌아야 한다. 규칙 H는 `tests/integration/`을 교차 관심사로 빼고, 이름 충돌 0이다(2026-10-15 cfe2e31 grep `nfr4`·`compare_runs`·`field_class` 0, 쓰이는 `-k` 식 `test_ic`·`g10`·`ic1`·`ic2`·`ic9`·`ic10`·`ic11`·`rule_g`·`rule_k_`·`dup_`·`new_topology`·`kcl_residual`·`kvl_branch_residual`·`mna_` 어느 것에도 걸리지 않는다 -- test 함수 이름에 `kcl_residual`을 넣지 않는다). 엔진 런타임은 비교기를 부르지 않는다. 엔진에는 비교용 칸을 더하지 않는다.
- **결과 기록에 없는 칸**(J-7, 오케스트레이터 기본안 -- 사용자 결정 아님): (2)의 비트 동일 집합 중 지금 결과 기록에 없는 칸(2026-10-15 cfe2e31 목록: 성공한 ε 풀이의 `stop`·`aborts`·`frozen`·`restarts`·`iterations` -- runs 줄 `failed_eps`에는 실패 풀이만, `Layer0Result`의 `iterations`·`restarts`·`aborts`·`frozen`·`start_failure`·`rows` -- runs 줄 notes `E/search/find_front.py:107-113`에 없음, 평가마다 metric 열·cone 행 -- evals 줄 `E/search/kernel.py:68-88` `_record`에 없음)은 결과 기록에 더하지 않고 **실행 하네스가 같은 프로세스에서 모은다**. 관찰 지점(이름·서명·모듈 전역 이름으로 부르는 방식을 바꾸지 않는 계약, XRUN-F1 card A J-3 선례): 모듈 `gmid_engine.search.find_front`의 속성 `layer0_start`·`sweep_front`(하네스가 반환값을 기록하고 그대로 돌려주는 감싸개로 바꾼다 -- `gmid_engine.search.find_front`라는 이름은 같은 이름 함수로 가려지므로 모듈은 `sys.modules`로 얻는다), 그리고 공개 속성 `SearchContext.cache`(실행 뒤 읽기만). 근거: 위 원칙 '엔진에는 비교용 칸을 더하지 않는다'와 최소 변경(결과 JSON 형식을 늘리지 않는다). 예외 둘은 엔진이 기록한다: `env_fp`((1) '결과 값')와 L-b 정지 사유(아래 -- 완료 조건 (i)이 결과 기록을 요구한다).
- **L-b 정지 사유 기록**(J-5, 오케스트레이터 기본안 -- 사용자 결정 아님): `polish_l_cells(sctx, solved, origin)`의 반환을 `(수락 풀이 tuple, 정지 사유)`로 바꾼다(공개 API 형식 변경 -- 호출부 엔진 `E/search/eps_sweep.py:121` 1곳, test `E/tests/search/test_l_bin_search.py:24·42·50`). 정지 사유(B-1 검증 반영, 오케스트레이터 기본안 -- 사용자 결정 아님): **L-b가 끝날 때(반환 직전) 예산 확인을 한 번 더 하고**, 걸리면 그 사유, 걸리지 않으면 `converged`다. 끝나는 길(while 조건, 칸 이동 안 확인, 바퀴 수락 없음)과 무관하게 이 마지막 확인 하나가 사유를 정한다. 근거: as-built `E/search/l_bin_search.py:41` `while improved and not _exhausted(sctx)`는 단락 평가라 바퀴에 수락이 없으면 예산 확인 없이 끝나고, `:49`는 예산에 걸린 칸 이동을 조용히 건너뛰며, `:63-66`은 `best`가 없거나 개선이 1 미만인 `solve_eps` 결과(그 `stop`이 `wall_budget`일 수 있다)를 버린다 -- 그래서 진행 중 확인만으로는 사유가 `converged`로 남을 수 있다. 커널 호출 수는 줄지 않고 벽시계(`time.perf_counter`)는 단조 증가하므로, L-b 안 어느 `solve_eps`·칸 이동이 예산에 걸렸으면 끝의 확인도 반드시 걸린다 -- 마지막 확인 하나가 모든 빈틈을 덮는다(fail-closed: 수렴 직후 마감을 넘긴 실행은 `wall_budget`으로 적혀 판정 불능이 되지만, 벽시계 정지를 놓쳐 PASS로 세는 쪽은 생기지 않는다). L-b 안 모든 `solve_eps`의 `stop`을 따로 기록하는 안은 같은 정보를 더 큰 기록 형식으로 내므로 택하지 않는다(최소 변경). 우선순위는 as-built `_budget_stop`(`E/search/slsqp_outer.py:94-99`)·card C `search_stop`과 같다 -- 커널 호출 수 ≥ 평가 예산이면 `eval_budget`, 아니고 벽시계가 마감을 넘었으면 `wall_budget`(근거: 평가 수로 이미 멈출 자리면 정지는 시간과 무관하게 같은 곳에서 나므로 결정적이다. `wall_budget`은 벽시계가 정지를 정한 경우만 뜻해야 (2) 전제 (나)가 맞다). `sweep_front`는 L-b 실행마다 `{"class": 묶음 이름, "l_from": 점 id, "stop": 사유, "accepted": 수락 수}`를 실행 순서대로 모아 반환 dict 키 `lb_stops`(tuple)에 두고, `find_front`는 notes에 `{"verdict": "l_search", "rule": "LR10", "stops": [...]}`를 언제나 한 줄 더한다(L-b가 돌지 않았으면 빈 목록) -- runs 줄 notes와 `SearchFront.notes`에 함께 실린다. `perf` 키는 바꾸지 않는다(XRUN-F1 card A의 `perf` 키 수 단언과 겹치지 않게). 버려진 `solve_eps` 결과(`best` 없음 `:63-65`, 개선 1 미만 `:66`)의 정지는 따로 기록하지 않는다 -- 위 끝 확인이 덮는다. XRUN-F1 card C는 `_exhausted`의 예산 부분을 `search_stop`으로 바꿀 때 이 반환·기록을 이어받는다(§2.4.14 (3)).
- **실행 하네스와 9회로 test 실행 방식**(J-10, 실행 방식은 오케스트레이터 기본안, 기본 실행 제외는 사용자 결정 N-2): 회로마다 **새 프로세스 하나씩 순차로**(`subprocess.run`, 병렬 `Popen` 금지 -- 메모리 규칙 '무거운 실행은 한 번에 하나'), 환경 = 허용 목록으로 새로 만든 dict(PATH·SYSTEMROOT·APPDATA·TEMP/TMP(실행별 빈 폴더)·`GMID_LUT_TABLE_CACHE_DIR`(실행마다 빈 폴더)·`PYTHONDONTWRITEBYTECODE`·`PYTHONIOENCODING`, 그리고 비교할 바깥 `OPENBLAS_NUM_THREADS`), 실행마다 별도 S3 출력 폴더, E_B 40 선언, 벽시계 정지가 나지 않게 넉넉한 `front_budget_s`, 회로마다 결과를 파일로 쓴다(중간에 죽어도 남게). `test_blas_thread_determinism`의 9회로 결정성 test는 기본 실행에서 빼고 무거운 test 마커를 붙인다(아래 '무거운 test 마커', 사용자 결정 N-2 -- 옛 기본안 '기본 suite에 남김'을 대체). 비용: 9회로 사슬 한 벌 약 900 s(측정 3: 896.4 s) × 2 = 약 1,800 s. 범위(9회로)는 그대로다. **무거운 test 마커**(사용자 결정 N-2, 2026-10-15 "나로 해" -- 판정 범위는 줄지 않음. 같은 날 N-2 정정("1~3 권장대로", 원문 'NFR-4 card 2·offset trim 결정'): 이 test의 설정은 바깥 스레드 1과 max(2, cpu) 둘(약 1,800 s)이고, 다섯 설정(1·8·18·미지정·numpy 선행)은 판정 agent의 A-4 측정이다 -- 옛 기록 '스레드 설정 다섯 가지'는 기록 오류): 2026-10-15 cfe2e31 실측으로 엔진 tests에 `slow` 마커·pytest 마커 설정이 없다(`skills/analog-gmid-design/pyproject.toml` `[tool.pytest.ini_options]`는 `testpaths`만, `mark.slow` 사용처 0). 그래서 이 card가 정의한다(오케스트레이터 기본안 -- 사용자 결정 아님): 마커 이름 `slow`. 등록 위치 = `E/tests/conftest.py`(`pytest_addoption`의 옵션 `--run-slow`, `pytest_configure`의 `config.addinivalue_line("markers", ...)`) -- 선례 `E/tests/structure/conftest.py:37-55`(마커 `structure_test_mapping`을 등록하고 `pytest_collection_modifyitems`에서 기본 실행에서 뺀다). 빼는 방식 = `pytest_collection_modifyitems`가 `--run-slow`가 없으면 `slow` 표시 항목을 `pytest_deselected`로 뺀다. `-m` 식과 무관하게 옵션으로 가른다(근거: `-m`을 주면 규칙 H 마커 `structure_test_mapping`의 기본 제외가 꺼져 전체 suite 구성이 바뀐다). 대상 = `E/tests/integration/test_blas_thread_determinism.py` 파일 전체(모듈 수준 `pytestmark = pytest.mark.slow` -- 같은 파일의 `test_single_thread_start_fp_matches_base`도 무거운 module fixture `runs`를 함께 쓰므로 기본 실행에서 fixture가 돌지 않게 파일 단위로 표시한다). 41 §5.13 셋째 test `test_layer0_boundary_rows_positive_9circuits`는 층 0까지라 표시하지 않는다. 마커 동작 test(`--run-slow` 없으면 deselected, 있으면 수집)의 위치 = `E/tests/test_conftest_slow_marker.py`(하위 프로세스로 `python -m pytest --collect-only -q gmid_engine/tests/integration/test_blas_thread_determinism.py`를 `--run-slow` 있이·없이 돌려, 없으면 그 파일 항목 전부 deselected·있으면 전부 수집됨을 확인 -- 수집만 하므로 무거운 실행이 없고 임시 test 파일을 쓰지 않는다. `pytester` 플러그인은 지금 켜져 있지 않다). 규칙 H 예외 근거: 대상이 엔진 원본 파일이 아니라 `E/tests/conftest.py` 동작이고, 규칙 H 검사기는 `tests/` 바로 아래 파일(경로 성분 1개)을 짝·고아 검사에서 뺀다(`E/tests/structure/structure_checks.py:955`). 반드시 포함하는 실행(판정 agent의 전체 suite, 병합 직전 전체 suite) 명령 = `python -m pytest -q gmid_engine/tests -p no:cacheprovider --run-slow`(실행 위치 `skills/analog-gmid-design`). 기본 실행(`--run-slow` 없음)은 요약에 뺀 수를 `deselected`로 보인다. 전제: pytest-xdist(`-n`)를 쓰지 않는다(엔진 tests 사용 0 -- 한 프로세스 순차 실행), 이 test는 다른 9회로 test(`test_s0_layer_9circuits.py` 등)와 동시에 돌리지 않는다(메모리 규칙 '무거운 실행은 한 번에 하나' -- 병렬 셸·병렬 pytest 호출 금지).
- **기준선 변화 판정 규칙**(사용자 결정 N-1, 2026-10-15 "승인해", 원문 `_drafts/user_decisions.md` 'NFR-4 card 2 기준선 변화 사전 승인'): auditor가 base(cfe2e31)·head를 같은 하네스로 재어 실제 값 변화 목록(회로·칸·옛 값·새 값)을 판정 기록에 남긴다. 목록의 변화마다 아래 사전 승인 범위와 대조한다 -- **범위 안이면 통과**, **범위 밖이면 그 변화를 사용자 보고 대상으로 판정 기록에 따로 적고 병합 전에 사용자 결정을 받는다**(통과로 세지 않는다). 사전 승인 범위 = (가) folded_cascode 층 0 `hard_ok` False → True(와 그 원인인 시작점 `w_min:M8` c 부호), (나) common_gate_amplifier ε 풀이 `EA:s1` best seq 34 → 23·stop `converged` → `slsqp_8`, (다) 끌어올림 영향 toy test 고정값 중 파일 `E/tests/search/test_layer0_center.py`·`E/tests/search/test_find_front.py`·`E/tests/search/test_residual_probe.py`·`E/tests/convergence/test_converge_point.py`의 단언. (라) 사용자 결정 N-3(2026-10-15 "1~3 권장대로", 원문 'NFR-4 card 2·offset trim 결정'): 승인한 두 회로(folded_cascode, common_gate_amplifier)에서 (가)·(나)와 같은 원인으로 따라 바뀌는 칸(같은 풀이·같은 회로의 θ·목적값·평가 수·front 점·S3 줄 등)도 통과다. auditor는 그 칸마다 '같은 원인'의 근거(변화가 (가)의 층 0 시작점 또는 (나)의 `EA:s1` 풀이에서 시작해 이어짐)를 판정 기록에 적는다. 범위 밖(사용자 보고 대상 유지): `u17_1b_s0_baseline.json` 값 변화, 다른 회로의 변화, 승인한 두 회로에서 (가)·(나)와 다른 원인의 변화, 다른 test 파일(`test_eps_sweep.py`·`test_slsqp_outer.py`·`test_search_context.py` 등)의 단언 변화. `run_id`·S3 줄 `code_fp`는 코드 변경으로 당연히 바뀌는 칸으로 따로 적는다(판정 대상 아님). 아래는 기준선별 처리다(XRUN-F1의 X-4와 별개):
  - **B-1** `E/tests/integration/fixtures/u17_1b_s0_baseline.json`(9회로 S0 수준 칸 지문): 바뀌지 않을 것으로 본다((7) '기준선 재측정'). test 작성 주체가 head에서 독립으로 다시 재고, 다르면 승인 대상. `_source` 설명 문자열만 고치는 것은 승인 대상이 아니다(J-12).
  - **B-2** 층 0·탐색 결과(9회로 front·pending·unmeasured, ε 풀이 기록, 층 0 결과, 시간 칸 뺀 `perf`, S3 줄): 3안으로 바뀐다. 41 §5.13 (a2) 실측(34932a9, 스레드 1 -- cfe2e31에서는 재지 않음): **folded_cascode `hard_ok` False → True**(시작점 `w_min:M8` c −4.68e-10 → +1.25e-6), **common_gate_amplifier ε 풀이 `EA:s1` best seq 34 → 23, stop `converged` → `slsqp_8`**, 나머지 7회로 0건. auditor가 base(cfe2e31, 바깥 스레드 1)와 head를 같은 하네스로 재어 목록을 만든다. `run_id`·S3 줄 `code_fp`는 코드 변경으로 당연히 바뀌는 칸으로 따로 적는다.
  - **B-3** 탐색 값을 고정한 toy test 단언: 3안으로 바뀔 수 있는 후보(2026-10-15 card 초안 grep, 확정 아님) -- `E/tests/search/test_layer0_center.py`, `test_find_front.py:44-47`, `test_eps_sweep.py`, `test_slsqp_outer.py`, `test_residual_probe.py`(`centre_start` 전류를 쓴다), `test_search_context.py`(첫 평가 점 = `centre_start` → LUT memo 상한), `E/tests/convergence/test_converge_point.py:195·225·264·360`(`kernel_calls`). 이 중 사전 승인 범위(위 판정 규칙 (다))는 `test_layer0_center.py`·`test_find_front.py`·`test_residual_probe.py`·`test_converge_point.py` 넷이고, `test_eps_sweep.py`·`test_slsqp_outer.py`·`test_search_context.py`의 단언이 바뀌면 범위 밖이라 사용자 보고 대상이다. 새 값은 피검 출력 복사가 아니라 독립 판정의 값 변화 목록과 대조해 쓴다. 허용 폭 넓히기 금지.
  - 승인 불필요(기록만): `test_blas_thread_determinism` strict xfail 제거·범위 확장(기준 강화), 형식 변경(단계 A 보고서 최상위 키 13 → 14, runs 줄 `env_fp`, notes `l_search` 한 줄, `polish_l_cells`·`sweep_front` 반환 -- 이 절이 정한 형식). 옛 측정 파일(`wt/_scratch_xrun_audit/…`, `wt/_nfr4_design_scratch/all_variant_a2.json`)은 기준선으로 쓰지 않는다.
- **작성 주체**: test 작성 주체다. 분해능 식은 (4) 표를 독립 구현한다. 엔진 함수를 불러 폭을 만들지 않는다(WP-13 작성자 ≠ 검증자). 예외는 Q-N3·Q-N4의 감도 전파뿐이다. 이것은 엔진의 출발 구간 블록을 섭동 입력으로 다시 부른다(진입은 NFR4-F2). 입력 생성일 뿐 기대값을 만들지 않는다.
- **입력·출력**: 입력은 실행 기록 두 개(회로마다 실행 하네스가 덤프한 S0 수준 스냅샷 필드, 단계 보고서, 결과 JSON, S3 evals·runs)와 비교 종류(같은 환경 / 다른 환경 / 수치 보존 리팩터링)다. 출력은 비교 보고 JSON이다: 필드마다 부류, 기준 값, 비교 값, \|Δ\|, 분해능, 출처, 판정. 판정은 PASS·FAIL·**판정 불능** 셋이다. D 불일치·C 초과는 FAIL이다. T는 보고만 한다. 다음은 판정 불능이다(PASS로 세지도, 건너뛰지도 않는다): (i) (2)의 전제를 어긴 실행, (ii) 비교기가 분해능을 만들 자료가 없는 C 칸(예: FD 스텝에 필요한 스냅샷 칸이 기록에 없음, 감도 전파에 필요한 매크로 해 주입 진입이 없음(NFR4-F2 전), `MetricResult.resolution`이 None인 metric). K 칸은 필드별 비교에서 판정하지 않고 보고만 한다(Q-N2). 보고 맨 위에 판정 불능 칸 수를 따로 적는다.
- **감사 사용**: auditor는 격리 복제본에서 9회로를 실행해 판정 기록에 두 실행의 실행 환경 지문, 엔진 코드 지문, 비교 보고 경로를 남긴다. (a) 같은 환경 재현: 같은 커밋을 같은 환경에서 두 번 실행한다(별도 프로세스, 빈 표 캐시(LUT 파생표 캐시 Q9 결정 전), 실행마다 별도 S3 출력 폴더 -- v1.10부터 엔진은 S3를 읽지 않지만 두 실행의 출력 줄이 한 파일에 섞이지 않게 한다. 옛 근거 '`start_points.py:34-37`·`search_context.py:139`가 S3를 읽는다'는 그 코드 삭제로 사라진다). 1차 검사만 한다. (b) 환경 비교: 같은 커밋을 환경 A(기준)·B에서 실행한다. 환경 B의 예는 numpy·scipy 판이 다른 venv, corename이 다른 CPU다. 스레드 수는 엔진이 1로 고정하므로 환경 축이 아니다. **기대 결과**(대리 측정 = 고정 전 스레드 1 대 8·18, 41 §5.13): pushpull_follower_buffer는 D 불일치로 FAIL이다(외층 ε 풀이 `EP:s1`의 `frozen:L:M1`·재시작 2 대 6에서 시작해 평가 18번부터 다른 점). 이것은 알려진 결함이다(Q-N7 확정, 사용자 결정 2026-10-15 "기본안대로 진행해", U-83: 42 D-ND4로 기록하고 이 card를 끝낸다, 원인은 후속 card NFR4-F1). 나머지 8회로는 D가 같을 것으로 본다(대리 측정 D 차이 0). 출발 구간·매크로 C 칸은 감도 전파 진입(NFR4-F2)이 생기기 전에는 판정 불능이다. (c) 수치 보존 리팩터링: base·head를 같은 환경에서 실행해 비교기를 돌린다.

**(6) 캐시 키는 비트 지문 그대로**

블록 입력 버전 = 값 지문 합성(§2.4.4 `fp_of`, float = `float.hex`)은 바꾸지 않는다. ③의 허용은 검증 기준에만 있다. 캐시·재사용·이식 판정에는 없다. 근거(사용자 결정 2026-10-15): 같은 환경에서는 결과가 비트 재현되므로 반올림 키의 재사용 이득이 0이다. 반올림 키는 블록마다 '반올림한 입력이면 같은 출력'을 증명할 의무를 만든다. pushpull 사례는 결함(41 §5.13)이라 이 근거에 쓰지 않는다(사용자 2026-10-15).

**(7) 영향**

- **S0 스냅샷**(v1.10): 디스크 S0 스냅샷이 없어졌다(§2.4.3). 키 (iv)·Q-N1은 대상 소멸이다.
- **기준선 재측정**: `E/tests/integration/fixtures/u17_1b_s0_baseline.json`(단계 A·B·달성가능성·출발 구간·커널 칸 지문)은 다시 잰다. 1안은 스레드 1 경로를 고정하므로 이 값들이 바뀌지 않을 것으로 본다. 기존 기준선이 test 환경 스레드 1 고정(conftest) 안에서 잰 값이기 때문이다. 3안은 층 0 이후만 바꾸므로 이 기준선에 닿지 않을 것으로 본다(실측: 41 §5.13 채택안 (a2) 적용에서 `search_base.fp`·`context_fp`가 비교할 수 있는 7회로 모두 불변). 그래도 S0 계산 경로가 바뀌는 변경(§2.4.3 삭제 목록)과 같이 가므로 test 작성 주체가 새 코드에서 독립으로 다시 재고, 옛 값과 다르면 사용자 승인 대상으로 보고한다. 층 0·탐색 결과에 기대는 기준선·기대값(시작점·front·평가 수)은 3안으로 바뀐다(실측 41 §5.13 (a2): 스레드 1에서 folded 1건(`hard_ok` False → True), common_gate 2건(ε 풀이 best·stop)이 바뀌고 나머지 7회로는 0건). 그래서 다시 잰다.
- **다시 쓸 test**: `E/tests/conftest.py`의 스레드 1 강제(코드 21-25행: `_BLAS_THREAD_ENV` 21, numpy 선행 import 거부 22-23, 강제 24-25. 주석 15-20 -- cfe2e31 실측, 옛 문장 '23-27·17-22'를 정정. 표 캐시 고정 27-47은 남긴다)를 지운다. `E/tests/integration/test_blas_thread_determinism.py`는 strict xfail을 지우고 범위를 9회로 · S0 전 필드 · 층 0 · 탐색 결과로 넓힌다. 비교는 1차 검사(바깥 스레드 1 대 max(2, cpu), 엔진 고정 뒤라 같은 환경)로 한다. 지금 두 프로세스를 병렬 `Popen`으로 띄우는 것(cfe2e31 `:114`)은 순차로 바꾼다((5) '실행 하네스', J-10). 기준선 대조 test `test_single_thread_start_fp_matches_base`는 남긴다. `E/tests/convergence/test_converge.py:243`의 `OPENBLAS_NUM_THREADS="1"`, `E/tests/integration/test_no_s0_files_written.py:101` 하위 프로세스 허용 env의 같은 항목과 docstring `:7`을 지운다(J-11). 사실이 틀리게 되는 docstring 문장(`E/tests/integration/test_s0_layer_9circuits.py:11`의 'conftest가 `OPENBLAS_NUM_THREADS=1` 고정')을 '엔진 import가 고정'으로 고친다(같은 파일 `:26`은 옛 기준선 측정 조건 기록이고 `:275` 주석 '같은 BLAS 설정이면'은 여전히 참이라 둔다 -- N-2). 형식 변경으로 깨지는 test: `E/tests/pipeline/test_stage_a_report.py:34-35·62`(최상위 키 13개 → `env_fp` 더해 14개), `E/tests/pipeline/test_stage_a.py:449` `len(REPORT_KEYS) == 13`과 docstring `:447`(같은 키 수 -- N-1), `E/tests/search/test_l_bin_search.py:24·42·50`(`polish_l_cells` 반환). `E/tests/search/test_find_front.py`의 `perf` 키 단언은 바뀌지 않는다(J-5가 `perf`를 건드리지 않음). `E/tests/integration/fixtures/u17_1b_s0_baseline.json:2` `_source`의 `s0_snapshot` 설명은 test 작성 주체가 이 card에서 새 설명으로 고친다(값이 같으면 승인 대상 아님, §2.4.3 표, J-12).
- **새 test**: `test_blas_pin_verified`(import 뒤 두 라이브러리 조회 = 1, numpy를 먼저 import한 하위 프로세스에서도 1, 바깥 `OPENBLAS_NUM_THREADS` 1·8·18·미지정에서 `fp_of(blas_environment())`가 같음), `test_blas_pin_fail_closed`((1) '주입·관찰 지점'으로: 설정이 듣지 않는 가짜 기록·기호 없는 기록·MKL·BLIS 기록 → `RuntimeError`, 빌드 설정 비 OpenBLAS·열거 미구현 플랫폼 → import 시점 `RuntimeError`, ctypes로 조회를 2로 바꾼 뒤 재확인 지점 (a)~(e) 각각 → `RuntimeError`, 조회 1인 새 OpenBLAS 모듈(DLL 복사본 적재 -- 미측정, test 주체가 전제를 먼저 단언)은 재확인 통과·`blas_environment()` BLAS 항목 하나 더·`env_fp` 달라짐 -- J-2), `test_first_pass_preconditions`(E_B 미선언 실행·`wall_budget` 정지 실행(L-b 사유 포함)·같은 실행 안 `env_fp`가 다른 실행을 비교기가 판정 불능으로 낸다), `test_env_fp_recorded`(결과 기록 두 곳 -- 단계 A 보고서 dict와 파일(정상·정지 경로), S3 runs 줄 -- 에 `env_fp`가 있고 같은 프로세스의 `fp_of(blas_environment())`와 같다), L-b 정지 사유 test(`converged`·`eval_budget`·`wall_budget` 셋, 두 예산이 함께 닿으면 `eval_budget`, 바퀴에 수락이 없어 끝났어도 끝에 마감이 지났거나 평가 예산에 닿았으면 그 사유 -- 끝 확인, B-1), 무거운 test 마커 test(`--run-slow` 없으면 `slow` 항목이 deselected, 있으면 수집), 비교기 단위 test(D 불일치·C 초과 FAIL, 분해능 식이 (4) 표와 같음, 판정 불능 분류), 41 §5.13의 test. core 모듈 전부의 모듈 수준 numpy·scipy import 0(AST)도 `test_blas_env.py`가 본다.
- **XRUN-F1 card A·C와의 경계**(사용자 결정 X-19: 이 card가 먼저 병합): card A -- `build_search_context` 서명·`SearchContext`는 이 card가 바꾸지 않으므로 card A의 서명 불변 계약 그대로다. `find_front` `perf` 키도 바꾸지 않으므로 card A의 `perf` 키 수 단언과 겹치지 않는다. `layer0_center.py`는 이 card가 `_current_centre` 끌어올림과 `layer0_start` 진입만, card A가 `_maxmin`·`centre_start` docstring을 고친다(줄 번호는 card A가 병합 뒤 다시 잰다). 이 card의 층 0·탐색 값 변화는 card A의 base(card A 직전 master)에 들어가므로 card A 기준선에 따로 조치하지 않는다. card C -- L-b 정지 사유는 §2.4.14 (3) l_bin_search 행이 이어받는다. 재확인 (e)는 `solve_eps` 진입이라 card C의 `_budget_stop` → `search_stop` 교체와 겹치지 않는다.
- **XRUN-F1 기준선 재측정**(v1.11, 사용자 결정 X-4): card A의 RT 수정(§2.4.14 (2))으로 층 0·외층·감도 게이트의 탐색 궤적이 ulp 수준에서 바뀐다(같은 점이 같은 θ 비트가 되어 평가 캐시에 적중하고 FD 시험점이 바뀐다). 다시 잴 목록과 보고 형식은 §2.4.14 (6)이다. card B는 궤적을 바꾸지 않는다(§2.4.5 '결정성').
- **바꿀 코드 위치**(2026-10-15 cfe2e31 재확인): `gmid_engine/__init__.py`(`from gmid_engine.core import pin_blas_threads` 뒤 1회 호출 -- 규칙 C 루트 형식), 신규 `E/core/blas_env.py`, `E/core/__init__.py`(재수출 `pin_blas_threads`·`blas_environment`), `E/pipeline/stage_a.py`(진입 `:195-196` 재확인 (a)·보고서 `env_fp` -- 정지 `_stopped` `:93-97`·정상 `:240-243` 두 dict), `E/search/search_context.py` `build_search_context` 진입(재확인 (b), 서명 불변), `E/search/find_front.py` 진입 `:75`(재확인 (c), runs 줄 `env_fp`, notes `l_search`), `E/search/layer0_center.py` `layer0_start` 진입 `:638`(재확인 (d)), `E/search/slsqp_outer.py` `solve_eps` 진입 `:102`(재확인 (e)), `E/search/layer0_center.py:238-246`(41 §5.13 -- 옛 문장 '238-245'를 정정: 주석 238-239, `lift` 240, 루프 241-246, 반환 247), `E/search/l_bin_search.py`(정지 사유 반환), `E/search/eps_sweep.py:118-123`(`lb_stops` 모음), `_module_map.py` 등록, CONTRACT(`E/core/CONTRACT.md` 새 절, `E/pipeline/CONTRACT.md` 보고서 키, `E/search/CONTRACT.md` §3.14 `polish_l_cells`·§3.16 `find_front`·runs 줄 칸 목록·§3.21 전류 중심·U13.2 끌어올림 문장), 함수 레지스트리 §2(행 'BLAS 스레드 고정·실행 환경 값' = `gmid_engine.core.pin_blas_threads`·`blas_environment`, 행 '층 0 끌어올림(경계 배치점 닫힌 식)' = `layer0_center._current_centre` -- code 주체, 같은 변경). 바뀌지 않는 것: `E/search/archive.py`(`S3Archive` 생성자·쓰기 메서드), `build_search_context` 서명과 `SearchContext`·`StageAResult`·`SearchFront` 칸, `perf` 키, 블록 입력 버전 키(이 절 (6)), LUT 파생표 캐시 키(Q-N6).

**(8) 결정 Q-N1~Q-N10**(사용자 결정 2026-10-15 "기본안대로 진행해" -- 열 개 모두 기본안 채택, 원문 `_drafts/user_decisions.md` 'NFR-4 세부 결정 Q-N1~Q-N10', 계획 N7.2 U-77~U-86 닫힘. 질문 문장과 근거는 결정 경위로 남긴다. **v1.10**: Q-N1·Q-N5·Q-N8은 사용자 결정 2026-10-15 "나로 해"로 대상 소멸 -- 행은 기록으로 남긴다)

| # | 질문 | 결정(기본안 채택) | 근거 |
|---|---|---|---|
| Q-N1 | U-68 옛 S0 파일 정리가 실행 환경 지문 칸을 어떻게 보나 | **대상 소멸**(v1.10, 사용자 결정 2026-10-15 "나로 해" -- S0 파일·U-68 정리 없음). 옛 결정: 정리 판정에서 환경 칸은 보지 않는다 | U-68 원문은 '어떤 checkout으로도 재현할 수 없는 키만 지운다'이고 실행 환경은 checkout 속성이 아니다. 삭제 규칙을 넓히는 것은 사용자 몫이다 |
| Q-N2 | K(경로 계수)를 비교에서 빼고 보고만 하나 | 뺀다(보고만) | 측정 3에서 스레드 1 대 8의 경로 계수·풀이기 관찰 기록 차이가 5회로(키 수: current_reuse 7, nmcnr 8, sf_pushpull 8, two_stage_ota 7 -- 그중 1건은 매크로 SLSQP 종료 상태 9 대 8로 둘 다 실패, two_stage_ota_sf 2)에 있었다. 그런데 엔진 결정(D)은 바뀌지 않았다. 결과에 닿는 길이 차이(예산 소진 등)는 D 차이로 드러난다. 비교 항목을 빼는 것이라 기준 약화로 보고 사용자 결정으로 올린다 |
| Q-N3 | 선언 분해능이 없는 필드((4) '출처가 없는 것', 매크로 칸 전부와 x 포함)의 비교 폭, 노드 전압에 쓸 tol_V의 소자 | (가) 계획 IC2의 '그 밖의 연속 필드' 규칙과 같은 형식: 상류 허용오차 섭동의 감도 전파값. 매크로와 출발 구간 필드의 상류 = 매크로 채택 허용폭 \|ln \|H\|\| ≤ √tol, 층 0 전류 중심의 상류 = 그 점 θ 전류 FD 스텝이다. 노드 전압 = 그 노드에 채널이 닿는 MOS의 `dc_tol_v` 최솟값 | 새 상수를 만들지 않고 계획에 이미 있는 비교 규칙(IC2)을 쓴다. 대안 (나)는 비교에서 빼기(기준 약화), (다)는 사용자가 분해능 값을 선언하기다 |
| Q-N4 | 선언 분해능이 있으나 상류 풀이기 허용오차 때문에 그보다 덜 재현되는 필드(`w_m` 15 격자, `area_est_m2` 14.8 b_A)의 비교 폭 | (가) max(선언 분해능, Q-N3 (가)의 감도 전파값) | 엔진 스스로 매크로 해를 √tol 안에서 같은 해로 본다(`E/search/macro_poles.py:353`). 그 하류 값은 그보다 더 재현될 수 없다. (나) 문언대로 선언 분해능만 쓰면 numpy·scipy 판을 바꿀 때마다 이 4회로가 FAIL이고 기준선을 다시 재야 한다. 주: '4회로'는 결정 당시 문장이다. 2026-10-15 재측정으로 선언 분해능을 넘은 회로는 nmcnr 하나로 정정했다((4) 끝 문단) |
| Q-N5 | S3 실행 간 재사용(`E/search/archive.py` `load_evals`·`load_runs`의 `code_fp` 거르기)에도 실행 환경 지문을 넣나 | **대상 소멸**(v1.10, 사용자 결정 2026-10-15 "나로 해" 오케스트레이터 기본안 -- S3 실행 사이 읽기 없음, §2.4.12 Q11). 옛 결정: 넣는다. 명세는 history로 옮겼다 | 같은 이유(EP-2: 재사용은 같은 비트 결과일 때만). 결정 원문은 S0 키만 말하므로 범위를 넓히는 것이라 사용자 결정으로 올린다 |
| Q-N6 | LUT 파생표 디스크 캐시 키(지금 lut·core 소스 해시와 numpy·python 판 포함, `E/lut/table_cache.py:6-8`)에 BLAS 정보를 더하나 | 바꾸지 않는다 | 측정(2026-10-15, 정적 전수): 디스크 캐시를 거치는 파생표 6종(`E/lut/curve_check.py:52`, `mismatch_tolerance.py:63`, `noise_planes.py:75`, `noise_tolerance.py:54`, `tolerance.py:285`, `vdsat_tolerance.py:123`)의 계산은 모두 `E/lut/` 안에 있다. `E/lut/`은 numpy·math·core만 import하고 scipy를 import하지 않는다. `linalg`·`einsum`·`dot`·`matmul`·`@` 연산·`polyfit` 호출이 0이다(docstring의 `@m[vdsat]` 2건 제외). 그래서 BLAS를 부르지 않는다. 바꾸는 것은 결정 원문 범위 밖이라 사용자 결정이다 |
| Q-N7 | 다른 환경 비교에서 pushpull_follower_buffer가 FAIL할 것으로 예측된다((5) (b), 41 §5.13 '남은 위험' (2)) | 알려진 결함으로 기록하고(42 D-ND4) 이 card를 끝낸다. 원인(외층 FD 열 실패와 재시작 경로)은 별도 card로 조사한다. 2안은 다시 열지 않는다 | 원인이 경계 배치가 아니라 풀이기 경로 민감도다((a)·(a2) 시작점이 상대 1.5e-8 달라도 123건이 갈림). 같은 환경에서는 1안 고정으로 비트 재현되므로 U17 ② 기준선 측정은 막히지 않는다 |
| Q-N8 | 실행 환경 지문(키 (iv))이 결정 문언('BLAS 스레드 설정')보다 넓다(Python·플랫폼·numpy·scipy 판·BLAS config·corename) | **대상 소멸**(v1.10, 사용자 결정 2026-10-15 "나로 해" -- 키가 없다. 같은 구성은 결과 기록 칸 `env_fp`로 남는다, (1) '결과 값'). 옛 결정: 넓은 키 유지 | 같은 키 = 같은 비트 결과여야 S0 적중이 재계산을 대신할 수 있다(EP-2). numpy·scipy 판·corename이 바뀌면 같은 스레드 1에서도 비트가 바뀔 수 있다. 대가: numpy·scipy를 올리면 S0 캐시가 모두 무효가 된다 |
| Q-N9 | 층 0 끌어올림 닫힌 식의 값이 음수(s < 0, 전류를 낮춤)일 때(41 §5.13 '끌어올림 식의 가장자리') | s = max(0, 식의 값) -- as-built처럼 올리기만 한다 | as-built `lift`는 u ≥ 0이다(`E/search/layer0_center.py:232`). 낮추면 시작점의 전력·면적이 바뀌는 동작 변경이라 3안 결정 문언 밖이다 |
| Q-N10 | 계획 IC2(순서 섞기 불변)의 판정을 허용오차에서 비트 동일로 올리나((2) 표) | 올린다(계획 IC2 문언 정정) | 새 NFR-4 첫 문장(정렬된 순회)과 같은 환경·같은 코드 비트 동일에 맞는다. as-built test가 이미 비트 동일을 단언한다(`E/tests/sizing/test_size_and_seal.py:491-512`). 계획 문언을 바꾸는 것이라 사용자 결정이다 |

**후속 card NFR4-F1 -- pushpull 외층 FD 열 실패·재시작 경로 조사**(Q-N7 확정, 사용자 결정 2026-10-15 "기본안대로 진행해", U-83): 대상 = pushpull_follower_buffer 외층 ε 풀이 `EP:s1`이 시작점의 풀이기 잡음(`current/M4` 상대 5.6e-4)에 따라 `L:M1` FD 열 실패 → 변수 고정 → 재시작 2 대 6으로 갈리는 경로(41 §5.13 '남은 위험' (2), 42 D-ND4). 범위 = 원인 조사와 수정안 제시까지다(수정은 그 card의 design·사용자 결정을 거친다). 2안(순수 Python SQP)은 다시 열지 않는다. 이 card(NFR-4)의 완료를 막지 않는다. 등록 위치: 이 절과 42 D-ND4. 오케스트레이터 백로그에 같은 이름으로 올린다.

**후속 card NFR4-F2 -- 감도 전파용 매크로 해 주입 진입**(v1.10, **범위 변경 -- 사용자 승인됨** (사용자 결정 2026-10-15 "U-87은 LUT는 관리복잡도가 없다는 네 판단근거에 따라 유지. 나머지는 기본안대로", 원문 `_drafts/user_decisions.md` 'U-87~U-89·NFR4-F2·front 조회')): 대상 = Q-N3·Q-N4 (4) '계산 (i)'의 감도 전파에 필요한 엔진 진입(출발 구간 계산을 주어진 매크로 해로 다시 하는 공개 계약 -- test 전용 경로가 아니다). 이 card(NFR-4)의 완료 조건 (i)~(iv)는 이 진입이 필요 없다(같은 환경 1차 검사는 비트 비교). NFR4-F2가 끝나기 전에는 매크로·출발 구간 C 칸이 다른 환경 비교에서 판정 불능이다. 오케스트레이터 백로그에 같은 이름으로 올린다.

#### 2.4.14 XRUN-F1 실행 안 재사용 완성 (v1.11)

사용자 결정 2026-10-15 "권고대로 진행해"(원문 `_drafts/user_decisions.md` 'XRUN-F1 design 착수 결정' X-1~X-5). 취지(사용자 원문): "계산 재사용은 처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용되게 한다는 것이 원래 취지였어". 출처 분해·반사실 실험·결과 바이트 대조의 수치와 조건은 history H4에 있다. as-built 줄 번호는 master f23aec8 기준이다. 이 절이 정하는 것: 같은 실행 안에서 같은 입력의 계산 블록을 다시 계산하는 경로를 모두 없앤다(§2.4.9 판정 1 = 0, 실행 전체 모든 (블록, 분할)).

**(1) 출처와 처리**

| 출처 | 같은 입력을 다시 계산하는 경로(as-built) | 처리 | card |
|---|---|---|---|
| W | `_wire_sweep_memo`(`E/search/search_context.py:134-150`)가 LUT memo 상한을 재려고 임시 컨텍스트에서 첫 평가를 돌리고 결과를 버린다. 층 0이 같은 점(출발 사다리 칸 0)을 다시 평가한다 | §2.4.6 '첫 평가 버림 제거' | A |
| RT | 시작 θ에서 만든 좌표를 θ로 되돌릴 때 ln → exp 왕복으로 θ가 1~3 ulp 달라진다(H4 회로들의 θ 값 기준. 로그 균등 무작위 θ에서는 약 75 %가 바뀌고 최대 16 ulp -- history H4): 층 0 최대-최소 `_maxmin.to_theta`(`E/search/layer0_center.py:283-288`, 시작 좌표 `_coord` `:411-412`), 감도 게이트 `to_theta`(`E/search/gate_run.py:55-61`). 외층 `solve_eps`(`E/search/slsqp_outer.py:70-75·110-118`)에만 시작 θ 원값 보존이 있다. 그래서 같은 점이 다른 θ 비트가 되어 평가 캐시를 비켜 가고, 층 0 FD 시험점과 외층 FD 시험점이 어긋난다 | 아래 (2) 정본 하나 | A |
| L | 출발 사다리 칸 평가(`E/search/layer0_center.py:652`)와 Halton 시험점(`:622`)이 parent 없이 S0 스냅샷에서 시작해 같은 lineage 재사용을 못 한다 | §2.4.5 블록 결과 색인(계보 무관) | B |
| R | 수리 bisection(`E/search/layer0_center.py:495·509`)이 parent 없이 평가한다. 실패 평가는 스냅샷을 남기지 않았다 | §2.4.5 색인 + §2.4.7 부분 스냅샷 | B |
| X | 서로 다른 풀이(층 0·외층)의 FD 시험점이 다른 lineage에서 같은 블록 입력을 만든다 | §2.4.5 색인 | B |

RT를 고쳐도 색인은 필요하다(서로 다른 θ 비트는 다른 입력 버전이라 색인이 잇지 못한다 -- RT가 먼저 같은 점을 같은 비트로 만든다). 색인을 두어도 RT는 필요하다(RT 결함은 평가 캐시 적중을 막는다). 그래서 둘 다 한다.

**(2) ln 좌표 원값 보존 정본(RT, 사용자 결정 X-1 (1))**

| 항목 | 규칙 |
|---|---|
| 위치·이름 | 새 파일 `E/search/theta_coords.py`, 진입점 하나 = frozen dataclass `ThetaCoords`(규칙 A). 함수 레지스트리(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`) §2 개념별 정본표에 행 '탐색 좌표 x ↔ θ 값(ln 좌표 원값 보존)'을 더한다. 2026-10-15 확인: 엔진·test에서 `theta_coords`·`ThetaCoords` 0건, 레지스트리 §2에 같은 개념 없음. test `E/tests/search/test_theta_coords.py`(규칙 H), `E/_module_map.py` 항목 하나 |
| 만들기 | `ThetaCoords.start(variables, theta)`(사용자 결정 X-14(2026-10-15 "9번 권고대로 해"): 좌표 변환과 시작 좌표 원값 보존만 맡는다 -- clip 인자를 두지 않는다). `variables` = 그 풀이의 변수(외층·층 0은 상자 하한 조정 뒤 -- as-built `ln_idu_floors` 적용 뒤. 감도 게이트는 as-built처럼 조정 없는 `sctx.domain.variables`), `theta` = 시작 θ 전체 사전. 변수마다 시작 좌표 x0ᵢ = log 변수면 ln θᵢ, 아니면 θᵢ(자르지 않는다), 원값 rawᵢ = θᵢ. 변수 밖 성분은 `theta`의 값 그대로 고정한다. 외층은 L 단일 칸 고정값(as-built `_layout`의 `fixed`)을 넣은 시작 θ를 넘긴다(동작 그대로) |
| 되돌리기 | `to_theta(x)`: 변수마다 v = float(xᵢ). v == x0ᵢ(float 정확 일치)이면 rawᵢ, 아니면 log 변수는 exp(v), 아니면 v. 고정 성분은 그대로. 원값 보존 규칙은 as-built `E/search/slsqp_outer.py:110-118` 그대로다(사용자 결정 X-1 (1): 그 규칙을 공용 정본 하나로) |
| 상자 자르기(호출부, X-14) | 외층 `solve_eps`·층 0 `_maxmin`은 `ThetaCoords` 밖에서 **자기 상자로 자르는 단계를 명시적으로** 둔다: 풀이 시작 좌표 = clip(x0ᵢ; loᵢ, hiᵢ), 풀이기가 준 x는 clip(xᵢ; loᵢ, hiᵢ)한 뒤 `to_theta`에 넘긴다(as-built 두 경로의 clip 그대로). as-built 외층의 '잘리지 않았으면 원값' 판정(`E/search/slsqp_outer.py:70-75`)은 자른 좌표와 x0(자르지 않은 시작 좌표)의 비교로 유지된다 -- 시작 좌표가 상자 밖이면 자른 좌표가 x0와 같을 수 없어 원값을 쓰지 않는다. 감도 게이트는 자르지 않는다(as-built `E/search/gate_run.py:55-61` 그대로, 기준선 영향 없음). 근거: FD 열은 기준점과 한 좌표만 달라야 하고 `E/search/fd_jacobian.py:99-101`이 움직이는 좌표를 이미 상자 안으로 제한한다 -- 게이트에서 clip은 무동작이거나 기준점 좌표를 옮겨 FD를 조용히 틀리게 한다. 게이트 기준점이 상자 밖일 때 '검사 못 함'을 보고하는 것은 후속 항목이다(범위 밖, §11 U17 표 XRUN-F1 행 '후속') |
| 성질 | `to_theta(x0)`는 시작 θ와 성분마다 비트가 같다. 좌표 하나만 움직인 x(FD 시험점)의 나머지 성분은 시작 θ와 비트가 같다 |
| 쓰는 곳 | 시작 θ에서 좌표를 만들어 θ로 되돌리는 곳 전부(같은 변경에서 사본을 지운다, 레지스트리 §0 규칙 4): 외층 `solve_eps`(`_layout`의 x0·원값 계산과 `to_theta` 대체), 층 0 `_maxmin`(`to_theta`와 시작 좌표 `_coord` 대체), 감도 게이트 `run_sensitivity_gate`(x 계산과 `to_theta` 대체 -- 같은 결함의 세 번째 자리, 2026-10-15 grep `def to_theta` 3건. 사용자 결정 X-6으로 포함 확정, 기준선 재측정 대상). 새 점을 만드는 곳(상자 중심 `_box_centre`, Halton 시험점, 수리 bisection의 좌표 값)은 시작 θ의 왕복이 없어 대상이 아니다. `fd_jacobian`은 받은 `to_theta`를 그대로 부른다(서명 불변) |

**(3) 재작성 범위**(사용자 규칙 '틀린 구조는 전체 재작성': 수정마다 범위와 근거, 옛 코드는 같은 변경에서 삭제)

| 파일(`E/`) | card | 범위 | 근거 |
|---|---|---|---|
| `search/theta_coords.py` | A | 신규 | 정본 하나(위 (2)) |
| `search/slsqp_outer.py` | A | 부분 수정(`_layout`의 x0·원값 계산과 `solve_eps.to_theta`만. 상자 자르기 단계는 호출부에 명시 -- X-14) | 풀이 흐름은 맞고 좌표 변환 사본만 틀렸다 |
| `search/layer0_center.py` | A | 부분 수정(`_maxmin.to_theta`·`_coord`만. 상자 자르기 단계는 호출부에 명시 -- X-14). NFR-4 card 2 관찰 지점 계약 유지(§2.4.13 (1) J-3·(5) J-7, 41 §5.13 J-16): `layer0_center.scipy_minimize`를 모듈 전역 이름으로 부르는 방식(이름·키워드 호출·반환 `x` 읽기)을 그대로 둔다 | 같은 이유 |
| `search/gate_run.py` | A | 부분 수정(x 계산·`to_theta`만) | 같은 이유 |
| `lut/lut_memo.py` | A | 부분 수정(계수 상태와 상한 고정 추가, `from_sweep` 삭제) | 상한 식·LRU·디스크 층은 그대로다 |
| `core/bounded_lru.py` | A | 부분 수정(`adopt(key, value)` 추가 -- 원 key를 받아 `canonical_key` 적용, 계수 안 바꾸고 넣기, 상한 넘으면 퇴출·퇴출 기록) | 계수 상태 memo를 고정할 때 이미 계산한 항목이 miss로 두 번 세어지지 않게(J-4 (b)) |
| `lut/sweep_memo.py` | A | 삭제(파일 전체) | 첫 평가를 따로 돌리는 구조 자체가 틀렸다 |
| `search/search_context.py` `_wire_sweep_memo` | A | 단위 재작성(그 함수 전체) | 임시 컨텍스트·버리는 평가가 구조 결함이다. 남는 일 = 계수 상태 memo 설치와 n_θ 전달 |
| `search/kernel.py` | A·B | 부분 수정(A: 첫 커널 평가 뒤 상한 고정 호출 / B: 부분 스냅샷·S3 evals 실패 줄 `snapshot_fp`·블록 호출 인자) | 평가 흐름은 그대로다 |
| `core/compute_block.py` | B | 단위 재작성(`ComputeBlock.__call__`와 계수 상태 전부, `BlockStats`·`stats`·`reset_stats` 삭제). 코드 해시 부분(`_norm_const`·`_norm_code`·`_code_hash`)은 그대로 | 블록 객체가 프로세스 수준 계수를 쥐는 구조가 틀렸다(§2.4.9 M8) |
| `core/run_counters.py`, `core/graft.py`, `core/donors.py`, `search/s3_index.py` | B | 신규(각 진입점 하나: `RunCounters`, `graft`, `Donors`(추상 기반 -- `graft`와 한 파일이면 규칙 A 진입점이 둘), `S3Index`) | §2.4.4·§2.4.5·§2.4.9. `S3Index`는 `find`·`register`·`find_failure`·`register_failure`와 항목 수 조회만(`get`·`failure`·`local`·`solved`는 U17 ② -- card B 보완 card B J-5로 정정) |
| `core/failure_errors.py` | B | 부분 수정(칸 `partial`, classmethod `from_record` -- 두 기반 모두. 데이터 선언 모듈 유지) | §2.4.7 부분 스냅샷, §2.4.4 실패 재연 |
| `core/failure_partial.py` | B | 신규(진입점 `attach_partial(exc, snapshot)`, card B 보완 card B J-3) | 규칙 A 데이터 선언 모듈 판정 보존(§2.4.7 '전달') |
| `search/open_run.py` | B | 신규(진입점 `open_run() -> (donors, counters)`, 두 객체의 유일한 생성 자리. test `tests/search/test_open_run.py`) | 실행 비공유를 구조로(§2.4.5 '수명' (1), 사용자 결정 2026-10-16) |
| `tests/structure/structure_checks.py`(`check_m`), `tests/structure/README.md` 규칙 표 M 행, 픽스처 `tests/structure/fixtures/rule_m/{bad,good}/gmid_engine/`, `test_structure_rules.py`·`test_structure_rules_reject_fixtures.py`에 M | B | 신규 규칙 M(§2.4.5 '수명' (2) M-a·M-b·M-c·M-d·M-f, M-e 없음) | 생성 자리·생성 결과의 실행 경계 넘김을 정적으로 막는다(규칙 K 선례) |
| `sizing/seal_versions.py` | B, IT-2e | 부분 수정(입력 버전 식 사본 → `ComputeBlock.input_version`, card B 보완 card B J-11) | 입력 버전 정본 하나(§2.4.4). 봉인 4 판정은 그대로. **card IT-2e 추가**(v1.12.9, 계획 v6.32 N3.3·N3.6 4행): 집합 함수 `writers_in_scope(base, blocks) -> frozenset` 정의(같은 파일 -- `seal_versions`가 부르므로 구조 규칙 A 진입점 하나 유지), coverage 위반 writer = 필드 writer − `writers_in_scope(base, calls의 블록)`(옛 인라인 차집합식 삭제, 서로소 단언은 그대로) |
| `sizing/s2_values.py`(`KernelContext`), `sizing/kernel_context.py`, `sizing/kernel_run.py`, `sizing/seal.py` | B, IT-2e | 부분 수정(참조 칸 2개, 블록 호출 인자 전달, 부분 스냅샷 부착) | 블록 순서·봉인 판정은 그대로다. **card IT-2e 추가**(v1.12.9, §2.4.7 '전달'): `kernel_run.py` -- 파생 keep = `writers_in_scope(base, 커널 블록 + SEAL_ITEM_BLOCKS)`(옛 인라인 합집합식 삭제), `_call_block`에 인자 `before`·부착 전 `derive_child(writers_in_scope(ctx.base, before))`; `seal.py` -- 봉인 항목 블록 실패·봉인 보고서 블록 실패·봉인 위반 부착이 `writers_in_scope(base, …)`로 줄인 스냅샷을 붙임(위반은 `dc_seal_report` 포함) |
| `graph/s1_build.py`, `graph/s1v_build.py`, `metrics/ss_evaluate.py`, `layout/run.py`, `pipeline/stage_a.py`, `pipeline/stage_b.py`, `search/search_context.py`(S0 블록 호출) | B | 부분 수정(블록 호출에 `donors`·`counters`, 단계 A는 두 객체를 필수 키워드로 받아(호출자가 만든다 -- PD-8 card B 보완) 블록에 넘기고 `StageAResult` 참조. 감쌈 함수 `build_s1`·`build_s1v`·`run_layout`과 `convergence/place_layout.py`의 `place_layout`은 필수 키워드 둘(card B J-4), `convergence/converge_point.py`는 `sctx.dc`에서 꺼내 넘긴다) | 계산 내용은 그대로다 |
| `search/search_values.py`(`EvalResult`) | B | 부분 수정(칸 `partial`) | §2.4.7 |
| `search/find_front.py` | B | 부분 수정(`perf` 블록 계수 재작성: `_BLOCKS`·`_block_totals`·구간 차 삭제, `perf.blocks`·`perf.block_totals`(= `sctx.dc.counters.snapshot()`), `perf.block_index_entries`·`perf.block_index_bound`(E_total = §2.4.5 '상한' 행의 card B 계산, card B J-6 -- card C가 `search_ceiling`으로 옮긴다)). NFR-4 card 2 관찰 지점 계약 유지(§2.4.13 (1) J-3·(5) J-7, 41 §5.13 J-16): `find_front`가 `layer0_start`·`sweep_front`를 모듈 전역 이름으로 부르는 방식을 그대로 둔다 | 계수 출처가 `RunCounters`로 바뀐다 |
| `search/search_ceiling.py`, `search/search_stop.py` | C | 신규(각 진입점 하나) | 탐색 예산 숫자와 정지 사유를 한 자리로(X-8·X-16) |
| `search/fd_jacobian.py` | C | 부분 수정(묶음 상계 확인·`FdBudgetShortfall` 정의) | 열 평가 규칙은 그대로다 |
| `search/layer0_center.py`, `search/slsqp_outer.py` | C | 부분 수정(`_budget_stop` 정의 삭제 → `search_stop`, Halton 한도 → `search_ceiling`, `fd_jacobian` 호출부 `FdBudgetShortfall` 처리 4곳, 사다리 칸 평가 전 확인). NFR-4 card 2 관찰 지점 계약 유지(§2.4.13 (1) J-3·(5) J-7, 41 §5.13 J-16): `layer0_center.scipy_minimize`를 모듈 전역 이름으로 부르는 방식을 그대로 둔다. `layer0_start`·`solve_eps` 진입의 재확인 (d)·(e)도 그대로다 | 풀이 흐름은 그대로다 |
| `search/l_bin_search.py`, `search/eps_sweep.py`, `search/residual_probe.py` | C | 부분 수정(예산 확인·ε 계획 → 탐색 예산, 해상도 기록 칸 이름 `E_B` 그대로·값 `search_ceiling`). NFR-4 card 2(X-19로 먼저 병합)가 넣은 `polish_l_cells`의 정지 사유 반환과 `sweep_front`의 `lb_stops`·`find_front` notes `l_search` 기록은 그대로 이어받는다 -- 사유 값만 `search_stop` 반환값에서 온다(§2.4.13 (5) 'L-b 정지 사유 기록') | 같은 이유 |
| `search/gate_run.py`, `search/find_front.py` | C | 부분 수정(게이트는 E_total, 게이트 전 E_total 유도(정해지지 않았으면), 실행 끝 확인. **E_total 계산 자리를 한 곳으로 정하고 card B가 `find_front`에 둔 `perf.block_index_bound`용 E_total 식(§2.4.5 '상한' 행, card B J-6)을 같은 변경에서 지운다**(검증 N-4). `S3Index` 생성자에 상한 인자를 더하면 `open_run` 서명과 그 호출부 전부도 같은 변경에서 고친다(검증 N-3)). NFR-4 card 2 관찰 지점 계약 유지(§2.4.13 (1) J-3·(5) J-7, 41 §5.13 J-16): `find_front`가 `layer0_start`·`sweep_front`를 모듈 전역 이름으로 부르는 방식, 진입 재확인 (c)·runs 줄 `env_fp`·notes `l_search`를 그대로 둔다 | 같은 이유 |
| `search/kernel.py`, `search/start_points.py` | C | 부분 수정(kernel: E_B 유도 `:153-158` 삭제 -- `search_ceiling`으로 옮김. start_points: 주어진 시작점 평가 전 예산 확인) | 평가 흐름은 그대로다 |
| `_module_map.py`(`search_ceiling.py`·`search_stop.py` 항목), `search/CONTRACT.md`(예산·`_budget_stop` 문구. 그리고 한 줄: `sctx.eval_budget`과 결과 `perf.eval_budget`의 뜻은 선언 실행에서는 탐색 예산 E_B, 유도 실행에서는 D = E_total로 갈린다 -- 칸 이름·형식은 그대로, 어느 쪽인지는 `eval_budget_source`(`declared` / `derived_once:...`)가 말한다, N-3), §2.4.13 벽시계 경로 인용 | C | 갱신 | 같은 변경에서 지도·계약을 맞춘다 |
| `core/__init__.py`, `search/__init__.py`, `lut/__init__.py`, `_module_map.py`, CONTRACT(`core`·`lut`·`search`·`sizing`·`graph`·`metrics`·`layout`·`pipeline`), 함수 레지스트리 §2 | A·B | 갱신 | 공개 이름·모듈 지도·계약을 같은 변경에서 맞춘다 |
| 함수 레지스트리 `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md:633` 'LUT memo 상한 배선' 행(정본 `lut.sweep_memo`) | A | 고침: 정본을 `LutMemo.counting`·`open_count`·`fix_bound`(배선 = `_wire_sweep_memo`와 `evaluate`의 첫 커널 평가)로 바꾸고 `sweep_memo`·`from_sweep` 문구를 지운다. 새 행 '탐색 좌표 x ↔ θ 값(ln 좌표 원값 보존)' = `ThetaCoords` | 레지스트리 §0 규칙 4(대체하면 같은 커밋에서 갱신) |
| `search/layer0_center.py:631-632` `centre_start` docstring('`build_search_context`가 LUT memo 상한을 정하는 첫 평가도 이 점을 쓴다') | A | 고침: 첫 평가 버림이 없어졌으므로 'n_θ(변수 수)만 `_wire_sweep_memo`가 이 함수로 잰다'로 | 문구가 삭제된 동작을 가리킨다 |
| `layout/canon_block.py`(신규) | B | 신규: `@compute_block` 진입점 `canon_tables`(writer `ly_canonical_naming`) 하나 + `canonical_naming.py`에서 옮긴 비공개 `_Source`·`_marks`·`_build`(`_build`의 `rejected` 인자 삭제, 표지는 네 입력 필드에서). 블록 안 조합 값 `_Device`(네 필드 칸을 이름 하나로)와 별칭 충돌 검사 `_canon`을 이 파일에 둔다 | v1.11.2 O-36 (3)·O-39 (1), §2.4.8 정준 별칭표 행. 규칙 A(`decorated_and_plain`)·B·H |
| `layout/canonical_naming.py` | B | 재작성: 남는 공개 정의 = 데코레이터 공장 `canonical_names` 하나, 별칭표를 만들지 않고 투영의 `ly_canon`/`ly_canon_rows`를 읽어 번역만. 모듈 docstring :1(낡은 이름 `build_canon`)·:3 고침 | 블록 안에서 `ly_device`를 읽어 별칭표를 만드는 구조가 W 변경마다 두 블록을 다시 계산시켰다 -- 부분 수정으로는 READS를 좁힐 수 없다 |
| `_module_map.py`, `layout/_helpers_alias.py` docstring | B | 갱신: (i) `canon_block.py` 새 `ModuleEntry`(entry, 진입점 `canon_tables`, 설명 '정준 별칭표 계산 블록 -- 구조 정준 위치로 `ly_canon`·`ly_canon_rows`를 쓴다') (ii) `layout/canonical_naming.py` 항목(c3c50f14 `_module_map.py:1013-1015`) 설명을 '별칭표를 만들어'에서 '투영의 `ly_canon`·`ly_canon_rows`로 이름을 번역해'로 (iii) `layout/_helpers_alias.py` 항목(:1010-1012)과 그 모듈 docstring :4의 낡은 '만드는 쪽은 `canonical_naming.build_canon`'을 '만드는 쪽은 `canon_block.canon_tables`'로(`build_canon`은 as-built에도 없는 이름) | 모듈 지도·docstring을 같은 변경에서 맞춘다 |
| `layout/_ly_fields.py` | B | 부분 수정: `F_PINS`(`ly_pins`)·`F_W_ADJ`(`ly_w_adjustable`)·`F_ATTRS`(`ly_attrs`)·`F_CANON`(`ly_canon`)·`F_CANON_ROWS`(`ly_canon_rows`)·`WRITER_CANON`(`ly_canonical_naming`) 추가, `INPUT_FIELDS`에서 `(DEVICE, F_DEVICE)`를 빼고 세 입력 필드 추가, `LY_WRITERS`에 두 graph 필드 ← `WRITER_CANON`, `BLOCK_WRITERS` 맨 앞에 `WRITER_CANON`, `F_DEVICE` 삭제, 모듈 docstring 필드 목록 | O-39 (1) |
| `layout/contract_output.py` | B | 부분 수정: frozen dataclass `DevicePins(drain, gate, source)`·`DeviceAttrs(W_m, body, diode)` 추가 | §2.4.8 `ly_pins`·`ly_attrs` 행 |
| `layout/finger_candidates.py`, `layout/pattern_select.py`, `layout/rows.py` | B | 부분 수정: READS 선언·본문의 소자 칸 읽기·모듈 docstring을 §2.4.8 '세 블록 READS' 행대로(`rows.py`는 `ly_rejected` READS 삭제). `pattern_select`·`rows`가 같이 쓰는 소자 칸 읽기는 `layout/_helpers_pattern.py`의 `DeviceView`·`device_views(projection, adjustable=False)`(읽기 전용 조합 값, graph 필드 아님 -- 칸은 각 필드에 한 번만)로 한다 | O-36 (3) (a) |
| `layout/run.py` | B | 부분 수정: `_input_columns`를 네 필드로 나눠 쓰기(`ly_device` 없음), `_BLOCKS` = (`canon_tables`, `finger_candidates`, `pattern_select`, `finger_geometry`, `compose_rows`), 모듈 docstring 3·4 | §2.4.8 블록 순서 |
| `layout/outputs.py` | B | 부분 수정: `ly_point`(이름·`kind`·`ID_A`·`gm_id`·`L_m`·`vds_V`·`vsb_V`)·`ly_attrs`(`W_m`·`diode`)를 읽음, docstring :8-9 | O-39 (1) |
| `layout/__init__.py`, `convergence/effective_placement.py`, `convergence/CONTRACT.md:59·63` | B | 부분 수정: 공개 export `F_DEVICE` → `F_POINT`(:5·27·37), `effective_placement`(:5·13·29)는 `ly_point` 열 key로 이름만 | O-39 (1) 공개 필드 계약 변경 승인 |
| `layout/CONTRACT.md` | B | 갱신: :209(공개 필드 이름), :280·287·415(세 블록 READS), :452·456(4.12 2 입력 필드 네 개), :464(`devices` 순서 = `ly_point` key 순), 4.0 파일 표에 `canon_block.py`, 정준 별칭표 블록 절 | 계약을 같은 변경에서 맞춘다 |
| test(작성 주체 = gmid-test-author, design은 interface만): `tests/layout/conftest.py`(`staged_snapshot`·`BLOCK_ORDER`·`block_objects` -- §2.4.8 '세 블록 READS' 행 interface), `tests/layout/test_run.py:408`(`ly_attrs`의 `W_m`)·`:691` `MOD7_WRITERS`, `tests/layout/test_outputs.py:87`, `tests/layout/test_contract_input.py:21-36`, `tests/convergence/conftest.py:24·75`, `tests/convergence/test_converge_point.py:323`, `tests/convergence/test_effective_placement.py`(docstring :3의 `ly_device`, 손으로 만든 레이아웃 필드), 신규 `tests/layout/test_canon_block.py`(규칙 H), W-1~W-3 test | B | test 작성 | O-36 (3)·O-39 (1). code는 test를 고치지 않는다(작성자≠검증자) |

**(4) 삭제·변경 목록**(2026-10-15 `grep -rlw`, f23aec8. 완료 규칙: 이름마다 정한 범위에서 단어 단위 grep 0 -- history·design의 '옛' 문장 제외)

| 이름 | card | grep 범위(이 안에서 0) | 범위 밖에 남는 쓰임 |
|---|---|---|---|
| `_coord` | A | `E/search/` | 없음(지금 `layer0_center.py`뿐) |
| `def to_theta`(정의) | A | `E/search/` 중 `theta_coords.py` 밖(J-1 정정 -- 정본 `ThetaCoords.to_theta` 메서드는 `def to_theta`로 grep된다) | `E/search/theta_coords.py`의 `ThetaCoords.to_theta`(정본). `fd_jacobian`의 인자 이름 `to_theta`도 남는다 |
| `exact`(좌표 원값 목록) | A | `E/search/slsqp_outer.py` | 없음 |
| `sweep_memo`, `_CountingMemo`, `from_sweep`, `first_eval` | A | 엔진 전체(`gmid_engine/` 소스·CONTRACT·`tests/`) | 없음. 지금 쓰임: `_module_map.py`, `lut/CONTRACT.md`, `lut/__init__.py`, `lut/lut_memo.py`, `lut/sweep_memo.py`, `search/search_context.py`, `tests/lut/test_sweep_memo.py`(삭제), `tests/lut/test_lut_memo.py`, `tests/search/test_sweep_memo_wiring.py`(삭제 -- 원본 파일 없는 test라 규칙 H 고아, 검사는 `tests/search/test_search_context.py`로 옮긴다) |
| `BlockStats`, `reset_stats`, `_seen_inputs` | B | 엔진 전체 | 없음. 지금 쓰임: `core/compute_block.py`, `core/__init__.py`, `core/CONTRACT.md`, `graph/CONTRACT.md`, `sizing/CONTRACT.md`, test 39개(2026-10-15 grep `reset_stats`·`BlockStats` 32개 + 블록 `.stats()`만 쓰는 7개 -- 블록 계수를 읽던 test. 같은 단언을 `RunCounters.snapshot()`으로 다시 쓴다. 정확한 범위는 test 작성 주체) |
| `_block_totals`, `_BLOCKS` | B | `E/search/find_front.py` | `_BLOCKS`는 `E/layout/run.py`의 다른 이름이라 남는다 |
| `block_calls`, `block_reuses`, `block_computes`, `block_recomputes_same_input`(결과 JSON 칸) | B | 엔진 전체 | 없음. 지금 쓰임: `search/find_front.py`, `search/CONTRACT.md`, `tests/search/test_find_front.py:24` |
| `retain`, `release`, `regenerated_after_release` | B | 엔진 전체(지금 0) | design·계획 문장만(옛 문장은 history) |
| `_budget_stop` | C | `E/search/` | 없음(지금 정의 `layer0_center.py:262`·`slsqp_outer.py:94`와 그 호출) |
| card B의 E_total 사본 식(`find_front`의 `perf.block_index_bound`용, card B J-6) | C | `E/search/find_front.py`에 E_total 계산(`2 *` 변수 수 항·`eval_budget_source` 분기)이 남지 않음 -- card C가 정한 E_total 한 자리만 | card C가 정한 E_total 계산 자리(검증 N-4) |
| 예산 확인용 `sctx.eval_budget` 직접 읽기 | C | `E/search/`에서 `rg -n "eval_budget"`로 남는 곳이 아래뿐 | `search_ceiling.py`(정의·유도), `find_front.py`(perf 기록·`run_id`), `search_context.py`(생성), `search_values.py`(설정 정의), 해당 docstring |
| `F_DEVICE`, `ly_device`(v1.11.2 O-39 (1)) | B | 엔진 전체(`gmid_engine/` 소스·CONTRACT·`tests/`) | 부재 검사 test의 검사 이름 목록과 그 근거 주석(`tests/structure/test_removed_names.py:33-35`)만. 계약 입력 클래스 이름 `LayoutDevice`는 남는다(다른 이름). 지금 쓰임(2026-10-19 c3c50f14 `git grep`): 소스 `layout/{_ly_fields,run,canonical_naming,finger_candidates,pattern_select,rows,outputs,__init__}.py`, `convergence/effective_placement.py`, `layout/CONTRACT.md`, `convergence/CONTRACT.md`, tests `layout/{conftest,test_run,test_outputs,test_contract_input}.py`, `convergence/{conftest,test_converge_point,test_effective_placement}.py`. design·계획 history의 옛 문장은 범위 밖 |
| `_Source`, `_marks`, `_build`(정의) | B | `E/layout/` 중 `canon_block.py` 밖 | `canon_block.py`(옮긴 곳) |
| `_build`의 `rejected` 매개변수 | B | `E/layout/canon_block.py`(`def _build(` 시그니처에 `rejected` 없음) | 없음 |
| `(DEVICE, F_DEVICE)` READS·`projection.column(DEVICE, F_DEVICE)` | B | 위 `F_DEVICE`와 같은 범위로 함께 0 | 위 `F_DEVICE` 행과 같은 예외 |

**(5) card 분할**(의존 순서 A → B → C. 셋 다 U17 ②보다 먼저. 순서는 design → test·code → 독립 판정. C가 B 뒤인 근거: C의 색인 상한 fail-closed가 B의 `S3Index` 등록 경로에 있다 -- 예산 검사 부분만 보면 B와 독립이지만 card를 둘로 쪼개지 않는다. U17 ② 항목(`ComputeBlock` 무상태화, `BlockStats`·`reset_stats` 삭제와 test 39개 재작성, `RunCounters` 블록 부분, `test_g10_no_recompute_9circuits`)을 card B로 앞당기는 것은 사용자 결정 X-11)

| card | 범위 | 선행 | 완료 조건 | test 초안(이름은 착수 때 glob·규칙 A~K 충돌 확인) | 판정 측정 |
|---|---|---|---|---|---|
| **A** RT + W | (2) 정본과 세 자리 대체, §2.4.6 '첫 평가 버림 제거', (4)의 A 행 삭제 | 실행 사이 재사용 제거 card(병합 f23aec8) | (i) (4) A 행 grep 0 (ii) `build_search_context` 안 커널 평가 0, 첫 커널 평가 창의 독립 계수로 잰 U_eval,r에 대해 고정 용량 = (n_θ + 1)·U_eval,r(§2.4.6 표) (iii) `ThetaCoords`: 시작 좌표면 `to_theta` 결과가 시작 θ와 성분마다 비트 동일 -- 외층 `solve_eps`·층 0 `_maxmin`·감도 게이트 세 경로 모두 단위 test로 (iv) (6) 기준선 재측정과 값 변화 목록. **블록 재계산 계수는 card A의 기준이 아니다** -- 9회로 총계·블록별 값을 보고만 한다(출처 분류 없이). '재계산 0'은 card B 판정 1에서만 기준이다 | `test_theta_coords.py`: `to_theta(x0)` 비트 동일(ln·선형 성분), 좌표 하나 이동 시 나머지 비트 동일, 고정 성분 그대로, clip 인자 없음(넘기면 `TypeError`) / 외층·층 0 경로: 시작 좌표가 상자 안이면 자른 시작 좌표의 `to_theta`가 시작 θ와 비트 동일, 상자 밖이면 자른 좌표의 exp(원값 아님 -- as-built와 같음) / 감도 게이트 경로: 자르지 않음(기준점 좌표 그대로) / `test_layer0_center.py`·`test_gate_run.py`: 그 경로가 `ThetaCoords`를 쓰고 시작 좌표 `to_theta`가 시작 θ와 비트 동일(시작 θ를 log 왕복이 비트를 바꾸는 값으로 고른다 -- 이 두 경로는 base 코드에서 실패해야 한다) / `test_slsqp_outer.py`: 외층 `solve_eps`는 as-built가 이미 원값을 보존하므로(`E/search/slsqp_outer.py:70-75·110-118`) base 실패를 요구하지 않고, 정본 `ThetaCoords`를 쓰는지(사본 삭제)와 같은 비트 동일 성질만 확인 / `test_search_context.py`: 컨텍스트 생성 뒤 `kernel_calls` 0·`seq` 0, 계수 상태 memo, 첫 커널 평가 뒤 고정 용량 = (n_θ + 1) × 독립 계수(§2.4.6 '독립 계수'), 두 번째 `open_count`·`fix_bound` `ValueError`, 커널 평가 없는 실행의 `perf.lut_memo_bound` = `"unfixed_no_kernel_eval"` / `test_lut_memo.py`: 계수 상태 → 고정, 접근 순서대로 옮김, 넘치면 오래된 것부터 퇴출, 고정 직후 같은 키(원 key) 조회는 hit(계산 0, `misses` 불변), `"fixed"` 상태(생성자 memo·고정된 계수 memo 둘 다)에서 `open_count`·`fix_bound`는 `ValueError`, 창 없이 `fix_bound`·두 번째 `open_count`도 `ValueError` / `test_bounded_lru.py`: `adopt`가 원 key를 받아 `lookup`과 같은 키로 적중, 계수 불변, 넘치면 퇴출·퇴출 기록 | auditor가 격리 복제본에서 (ii)·(iii)·(iv)를 판정한다. 9회로(E_B 40 선언 = card 1 판정과 같음) 실행에서 블록 재계산을 `ComputeBlock.__call__` 클래스 수준 감쌈 계측(엔진 코드 무변경)으로 세어 총계·블록별로 **보고만** 한다(판정 아님, card B의 비교 자료) |
| **B** 색인 + 부분 스냅샷 + 계수 | §2.4.4 호출 규칙(v1.11), §2.4.5 블록 결과 색인·보존 규칙, §2.4.7 부분 스냅샷·`KernelContext` 참조, §2.4.9 계수 범위·`perf` 형식, (4)의 B 행 삭제 | card A 병합 | (i) (4) B 행 grep 0 (ii) 9회로 각각 한 실행에서 `perf.blocks` 모든 행 `recomputes_same_input` = 0과 `recompute_same_key` = 0(판정 1·5, ngcc_3stage_ff는 단계 A까지의 `RunCounters`). 판정 1은 엄격하다(실패 재연은 `replays`, 재계산 아님 -- X-9) (iii) card A 병합본 대비 같은 환경 비트 동일 집합(§2.4.13 (2))이 `perf` 블록 계수 칸·시간 칸·evals 실패 줄의 새 `snapshot_fp` 칸 말고 비트 동일(색인은 궤적을 바꾸지 않는다) (iv) `perf.block_index_entries`·`perf.block_index_bound` 보고(card C 병합 전에는 보고만 -- X-8) (v) v1.11.2 사용자 결정 O-36 (3): §2.4.8 '세 블록 READS' 행 완료 조건 W-1~W-4(W만 바꾼 두 `run_layout`에서 `ly_finger_candidates`·`ly_pattern_select`·`ly_rows` `computes` +0, `ly_canonical_naming` +1, 계산 필드 값 지문 같음, 변경 종류 = 순수 리팩터링(필드별) + 재계산 감소) | `test_run_counters.py`·`test_graft.py`·`test_donors.py`·`test_s3_index.py`(신규, 규칙 H): 기록·스냅샷, 결정적 도메인 실패 등록·같은 입력 재호출 때 같은 분류·같은 `FailureRecord` 객체 재연(블록 함수 호출 0, `replays` 1), 입력과 무관한 예외(예: 블록 안 `ValueError`·`KeyboardInterrupt` 흉내)는 등록 안 함, 같은 키 성공·실패 섞임 `ValueError`, `from_record`, `Donors` 하위 아닌 객체 거부, `test_graft_equals_compute`(`*`), `test_index_single_source`, fail-closed (1)~(4)·(6)(§2.4.5 표, (5)는 card C) / `test_compute_block.py` 다시 쓰기: 인자 없으면 `TypeError`, 같은 lineage `reuse`·다른 lineage `graft`·처음 `compute`, 블록 객체 무상태 / 계보 무관: parent 없는 두 평가가 같은 블록 입력이면 두 번째는 `graft` / 실행 격리(`tests/integration/test_run_isolation.py`, 규칙 M M-c를 지키는 꼴 -- `run_stage_a` 호출마다 자기 `open_run()`): 한 test 안에서 `open_run()`을 두 번 불러 얻은 두 쌍으로 두 번 실행하면 색인·계수를 나누지 않는다(두 번째 실행도 S0 블록 `computes` 1 -- card B 보완 PD-8) / `run_stage_a`·감쌈 함수(`build_s1`·`build_s1v`·`build_kernel_context`·`seal_dc`·`run_layout`·`place_layout`)는 `donors`·`counters`가 빠지면 `TypeError`(PD-8·card B J-4) / `test_failure_partial.py`(신규, 규칙 H): 부착 첫 값 유지·형식 거부, `from_record`(`SchemaRejectedError` 포함) / `graft`: `part` ≠ `"*"`·입력 버전 불일치 `ValueError`(card B J-2) / `Donors` 네 추상 메서드(card B J-5) / 실행 비공유 구조(사용자 결정 2026-10-16): `test_open_run.py`(신규, 규칙 H) -- `open_run()` 두 번 호출이 서로 다른 새 객체 쌍, `S3Index`·`RunCounters` 직접 생성이 규칙 M에 걸림(구조 test `test_structure_rules.py`·`test_structure_rules_reject_fixtures.py`에 M과 위반 픽스처 M-a·M-b·M-c(매개변수·결과 칸·반복문 밖 `open_run`·`open_run()` 대입 하나를 두 호출에 사용·`if` 가지 안 대입·`with` 본문 안 대입(호출은 본문 밖) 각각, 같은 이름 새 `open_run()` 재대입 1:1은 허용 픽스처)·M-d(보관 경로마다)·M-f 각 하나 / 기존 test 재작성 대상(규칙 M M-c, 2f684d6 AST): `run_stage_a`를 부르는 test·하네스 16파일 46곳 -- 호출마다 같은 함수 안 `open_run()`을 동반하게 고친다. `tests/integration/nfr4_run_dump.py`, `test_j_rules_library.py`, `test_layer0_boundary_rows.py`, `test_rerun_s3_independence.py`, `test_s0_layer_9circuits.py`, `test_stage_a_library.py`, `test_stage_b_library.py`, `tests/metrics/gb4_hand.py`, `tests/pipeline/test_stage_a.py`, `test_stage_a_loop_cut.py`, `test_stage_a_report.py`, `test_stage_b.py`, `tests/search/test_cell_floor.py`, `u13_hand.py`, `u13_real.py`, `tests/sizing/test_current_basis.py`. 그중 helper(`gb4_hand.py`·`u13_hand.py`·`u13_real.py` 등 `run_stage_a`를 감싸는 함수)는 쌍을 매개변수로 받지 않고 스스로 `open_run`을 부른다) / 부분 스냅샷: DC 블록 실패·봉인 위반·ss 실패 각각 `EvalResult.partial`의 `block_versions`, 실패 줄 `snapshot_fp`(parent가 있는 평가의 부분 스냅샷 test는 card IT-2e 몫 -- 아래 IT 행 test 칸·41 §4.7-7 L11 (e)) / `test_find_front.py`: `perf.blocks`·`perf.block_totals`, 옛 네 칸 없음 / `E/tests/integration/test_g10_no_recompute_9circuits.py`(판정 1·5) | 결과 JSON 형식 변경 목록(판정 기록이 확인): card A = `perf.lut_memo_bound`(새 칸), card B = `perf.blocks`·`perf.block_totals`(새 칸, 행에 `replays` 포함)·`perf.block_index_entries`·`perf.block_index_bound`(새 칸), `block_calls`·`block_reuses`·`block_computes`·`block_recomputes_same_input` 삭제, S3 evals 실패 줄 `snapshot_fp`(새 칸, X-10), `perf.blocks`의 새 행 `ly_canonical_naming`(v1.11.2 O-36 (3)). card C = 없음(X-16으로 게이트는 항상 돌아 옛 초안의 `not_run` 기록은 폐기). auditor가 9회로를 card A 병합본과 B 병합본에서 각각 실행(E_B 40 선언, 같은 환경): (ii) 결과 JSON으로, (iii) §2.4.13 비교기 1차 검사로. 독립 계측(A와 같은 감쌈)으로 `perf.blocks` 합과 대조 |
| **C** 예산 결함(사용자 결정 X-8·X-15·X-16·X-17) | 모든 커널 평가를 평가 예산 E_total에 넣는다 -- **E_B 선언 여부와 무관하게 모든 실행에서** '커널 평가 수 ≤ E_total'(X-15, 사용자 결정 2026-10-15 "1, 2번 둘 다 권고대로 해". 옛 초안 'E_B 선언 실행 한정'은 폐기 -- 결정 원문 X-8 회복). as-built 결함: 선언 E_B 40에서 커널 평가 43·49·64·66(history H4) -- FD 한 묶음(`E/search/fd_jacobian.py:86-111`)은 열마다 최대 두 방향을 예산 검사 없이 평가하고, 감도 게이트(`E/search/gate_run.py`, 호출 `E/search/find_front.py:84`)는 front 뒤 예산 밖에서 돈다. 규칙: (1) **정의**(사용자 결정 X-17(2026-10-15 "나로 해")): **선언 E_B = 탐색(외층) 예산**(§3.6 정의 그대로). 전체 상한 **E_total = E_B + N_T + R**(§2.4.9 유일 정의, R은 (2)). as-built에는 층 0 별도 예산 N_T가 없다(N_T = 0 -- 층 0은 외층과 같은 탐색 예산을 쓴다). 선언이 없는 실행은 as-built 식으로 시간 예산에서 유도한 값 D = `EvalBudget(front_budget_s, 첫 `len(sctx.domain.variables)` + 1개 평가 시간).limit()` = ⌊B / 평가 시간 중앙값⌋(as-built 유도 자리 `E/search/kernel.py:153-158` -- card C가 `search_ceiling`으로 옮긴다, (4). 식 `E/search/eval_budget.py:31-35`)이 그 시간 안 평가 총수이므로 **E_total = D**이고 **탐색 예산 = D − N_T − R**이다. 유도 전 평가도 이미 D 안에 든다(빼지 않는다 -- 두 번 세기). 선언 E_B 40은 그대로 동작한다(탐색 40 + 게이트 R). (2) **게이트 예약**(X-16): R = 2 × `len(sctx.domain.variables)`(감도 게이트의 변수 = 정의역 변수, `E/search/gate_run.py:49`; 2 = FD 열 하나의 시도 방향 수 `fd_jacobian.py:97` -- 새 상수 아님). 실제 게이트 묶음 상계(2 × 평가할 열 수)는 R 이하다. **탐색 예산** = 선언이면 E_B, 유도면 D − N_T − R(as-built N_T = 0). X-16의 문구 '탐색 예산 = E_total − 게이트 상계'는 같은 뜻의 다른 표기다(E_total − R = E_B + N_T, 탐색 = 층 0 + 외층, as-built N_T = 0이라 = E_B -- 사용자 결정 X-17(2026-10-15 "나로 해")). **`sctx.eval_budget`을 예산 확인에 직접 읽는 곳 전수**(609965d `rg -n "eval_budget" E/search E/sizing E/pipeline`, tests 제외로 재확인)를 탐색 예산으로 바꾼다: (a) `E/search/layer0_center.py:262-267` `_budget_stop`(층 0 최대-최소·Halton·수리) (b) `E/search/slsqp_outer.py:94-99` `_budget_stop`(ε 풀이) (c) `E/search/layer0_center.py:590-594` Halton 시험 한도(`tried >= sctx.eval_budget`) (d) `E/search/l_bin_search.py:33` `_exhausted`(L-b `polish_l_cells`, 호출 `E/search/eps_sweep.py:121`, 평가 `l_bin_search.py:57`) (e) `E/search/eps_sweep.py:93-94` ε 점 수 계획 n_ε = ⌊(E_B − E_fixed)/e_ε⌋와 해상도 기록 -- E_B 자리에 `search_ceiling(sctx)` 값을 쓴다. 기록 칸 이름 `E_B`는 그대로 둔다(선언 실행에서는 X-17로 E_B = 탐색 예산이라 뜻이 같고, 유도 실행에서는 값이 D − N_T − R이다 -- 결과 JSON 형식 변경 없음, **오케스트레이터 기본안**(원칙 근거, 사용자 결정 아님)) (f) `E/search/residual_probe.py:73` 정지 -- production 호출자가 없다(정의와 test뿐, 2026-10-15 grep). 그래도 같이 바꾼다: 근거 = U17 ②가 단계 B 층 블록으로 배선할 때 예산 규칙이 둘이 되지 않게(남겨 두면 E_B를 직접 읽는 확인이 하나 남는다). 예산 확인이 아닌 읽기는 그대로 둔다(`E/search/kernel.py:153-158`의 E_B 유도는 남기지 않는다 -- 아래 (4)로 `search_ceiling`에 옮긴다): `E/search/find_front.py:134·138`(perf `eval_budget` 기록, `run_id` 지문), `E/search/eps_sweep.py:85`(해상도 기록의 초기 칸 -- 이름 `E_B` 그대로, 값은 (e)와 같이 `search_ceiling`), `E/search/search_context.py:66-67`(생성), `E/search/search_context.py:146`(card A가 지움), docstring(`eps_sweep.py:9`, `l_bin_search.py:10`, `residual_probe.py:8`, `slsqp_outer.py:15`, `search_values.py:46`)은 같은 card에서 문구를 고친다. 감도 게이트만 E_total로 한다. (3) **계산 자리 하나**: 새 파일 `E/search/search_ceiling.py`, 진입점 `search_ceiling(sctx, *, final=False) -> int \| None`(탐색 예산 = 선언이면 E_B 그대로, 유도면 D − N_T − R. 유도 전이면 None. E_B 유도와 그 전이 확인도 여기서 한다 -- (4)). 정지 사유 판정은 새 파일 `E/search/search_stop.py`, 진입점 `search_stop(sctx) -> str \| None`(`eval_budget` = 커널 평가 수 ≥ 탐색 예산, `wall_budget` = as-built 벽시계 정지 그대로) 하나로 모은다(규칙 A: 숫자와 사유는 두 진입점이라 두 파일). (2)의 (a)·(b)·(d)·(f)는 `search_stop`을, (c)·(e)와 묶음 확인은 `search_ceiling`을 부른다. `_budget_stop` 두 정의와 `_exhausted`의 예산 부분은 지운다. 게이트가 시작된 뒤에는 `search_ceiling`·`search_stop`을 부르지 않는다(게이트는 E_total을 직접 쓴다). (4) **유도 실행의 확인**(사용자 결정 X-17(2026-10-15 "나로 해")): 선언 실행에는 예산 fail-closed가 없다(옛 초안 '선언 E_B < 1 + R이면 `eval_budget_below_gate_reserve`'는 폐기 -- 선언 E_B는 탐색 예산이고 게이트 R은 그 위에 따로 있으므로 넘칠 수 없다). 시간 예산에서 유도하는 실행만 확인한다. **유도 자리**(B-1, **오케스트레이터 기본안**(원칙 근거, 사용자 결정 아님) -- 근거: 유도와 적용·확인을 한 함수의 한 호출에 두면 '진행 중 묶음 한가운데의 유도'가 구조로 생기지 않고, 새 상태 칸 없이 None → D 전이 자체가 '한 번'을 표시한다): as-built `E/search/kernel.py:153-158`의 유도를 지우고 `evaluate`는 `eval_times`만 기록한다. `search_ceiling`이 `sctx.eval_budget is None`이고 평가 시간이 `len(sctx.domain.variables)` + 1개 이상이면 **첫 n_θ + 1개**로 D = `EvalBudget(front_budget_s, eval_times[:n_θ + 1]).limit()`(as-built 식 그대로)을 계산해 `sctx.eval_budget` = D, `eval_budget_source` = as-built 형식 그대로 `derived_once:floor(B/median_t_eval)@n_evals=<그 호출 때의 평가 수>`로 넣는다(규칙 G: 새 칸 없음). `search_ceiling`은 예산 확인 지점(묶음 시작 전·단일 평가 전)에서만 불리므로 진행 중인 묶음이 없다. **None → D 전이가 일어난 그 호출에서만**, 커널 평가 수(유도 전 평가 전부) ≥ 탐색 예산(D − N_T − R)이면 -- 유도 전 평가가 이미 탐색 예산을 넘었거나 남는 탐색 예산이 없으면 -- 그때만 fail-closed로 멈춘다. 확인이 한 번인 근거: 그 뒤에는 단일 평가가 '커널 평가 수 ≥ 탐색 예산이면 정지', 묶음이 '상계 ≤ 남은 탐색 예산이면 시작'이라 정상 정지(커널 평가 수 = 탐색 예산)와 fail-closed를 가르려면 적용 시점의 확인이어야 한다. 상태는 as-built 칸 `sctx.eval_budget`·`eval_budget_source`뿐이고 새 칸은 없다. **as-built와 달라지는 것**: D 값은 같은 첫 n_θ + 1개 평가 시간이라 같다. 유도 시점만 'n_θ + 1번째 평가 안'에서 '그 뒤 첫 예산 확인 지점'으로 늦어져, 그 사이 진행 중이던 묶음이 끝까지 돈다(as-built도 묶음 중간에 멈추지 않았으므로 평가 궤적은 같다). 기록 `eval_budget_source`의 `n_evals` 값은 늦어진 만큼 클 수 있다(형식은 같다). 그 뒤 `search_ceiling`은 상태 없이 불릴 때마다 커널 평가 수 > 탐색 예산이면 `RuntimeError`(구조 결함 -- 정상 실행에서는 생길 수 없다). **예외 분류**(N-4, **오케스트레이터 기본안** -- 사용자 결정 아님): `ValueError`(사유 `time_budget_below_search_reserve`: 시간 예산에서 유도한 평가 총수가 이미 한 평가와 게이트 예약 R을 담지 못한다). 원칙과 근거: (a) 후보 실패가 아니다 -- θ와 무관한 실행 설정(`front_budget_s`)의 문제라 `CANDIDATE_FAILURE_CLASSES`로 잡혀 S3 실패 줄로 묻히면 안 된다(`ValueError`는 그 잡기에 걸리지 않는다, `InfeasibleSizingError` 하위가 아닌 순수 `ValueError`) (b) 호출 계약 위반과 같은 종류다 -- 호출자가 준 시간 예산이 이 회로의 평가 비용에 비해 최소 탐색을 담지 못한다. 엔진은 넓은 except를 두지 않으므로 그대로 올라가 진입점의 '예상 밖' exit code가 된다 (c) N3.14에 새 분류를 더하는 안(exit code 따로)은 계획 표 변경이라 사용자 결정 몫이고, 예외 없이 정지 사유로 기록하는 안은 '평가 수 ≤ E_total' 보장을 조용히 깨진 채로 결과를 내므로 fail-closed가 아니다. **E_total이 끝까지 정해지지 않는 실행**(N-2: 평가 시간이 n_θ + 1개 미만이라 유도 조건에 닿지 않음 -- 평가가 하나도 없으면 `EvalBudget.limit()`도 None, `kernel.py:157`): 설계 기본안 -- `search_ceiling(sctx, final=True)`(키워드, `find_front`가 게이트 시작 전에 한 번 부른다)가 평가 시간이 1개 이상이면 지금까지의 평가 시간 전부로 같은 식을 계산해 같은 방식으로 넣는다(`eval_budget_source` 형식 그대로). 이때는 탐색이 이미 끝났으므로 fail-closed 조건은 커널 평가 수 > D − N_T − R(같으면 게이트까지 D 안에 든다)이다. 평가 시간이 하나도 없으면 커널 평가 0이라 '평가 수 ≤ E_total'은 E_total과 무관하게 성립하고 front가 없어 게이트도 돌지 않는다. (5) **묶음**: 묶음 상계 = 평가할 열 수 × 2(고정 열·스텝 0·None 열 제외, `fd_jacobian.py:89-94`). 탐색 예산이 있으면 시작하기 전에 남은 탐색 예산(탐색 예산 − 커널 평가 수) ≥ 상계인지 확인하고, 아니면 평가 0으로 '예산 부족'을 낸다. 탐색 예산이 아직 없으면(유도 전) as-built처럼 확인 없이 돈다 -- 그 평가는 (1)에 따라 E_B 안에 세고 (4)가 넘침을 잡는다. **단일 평가**(B-2, 원칙 X-8 '모든 커널 평가를 E_total에', **오케스트레이터 기본안**(원칙 근거, 사용자 결정 아님)): 탐색 단계의 단일 평가는 모두 평가 전에 `search_stop`을 확인하고 예산에 닿으면(커널 평가 수 ≥ 탐색 예산) 평가하지 않고 정지 사유 `eval_budget`이다. 609965d 전수(`rg -n "evaluate\(" E/search E/convergence E/pipeline`, tests 제외): 이미 확인이 있는 곳 -- `E/search/layer0_center.py:308`(최대-최소 `point`, `:304-307`), `:495`·`:509`(수리, 앞 `_budget_stop`), `:622`(Halton, 앞 `_budget_stop`), `E/search/slsqp_outer.py:129`(`point`, 앞 `_budget_stop`), `E/search/l_bin_search.py:57`(앞 `_exhausted`), `E/search/residual_probe.py:84`(앞 `:73`) -- 모두 (2)·(3)대로 `search_stop`으로 바꾼다. **확인이 없는 곳(이 card가 더한다)**: (가) `E/search/layer0_center.py:652` 출발 사다리 칸 -- 칸마다 평가 전 확인, 닿으면 사다리를 끝내고 `start_status` = `eval_budget`(그 뒤 Halton도 같은 확인으로 곧 끝난다) (나) `E/search/start_points.py:39` 시작점 확인 -- 층 0 시작점(이미 평가해 평가 캐시 적중, 커널 0)은 확인 없이 다시 읽고, 주어진 시작점(`given`)은 평가 전 확인해 닿으면 그 뒤 후보를 평가하지 않고 기록 `starts`에 `status` = `eval_budget`으로 남긴다(칸은 그대로, 값 하나가 새로 생긴다). 묶음 평가 `E/search/fd_jacobian.py:107`은 (5)·(6). `E/search/search_context.py:147`은 card A가 지운다. **MOD8** `E/convergence/converge_point.py:123`(`evaluate(geometry=...)`): `find_front` 안에서 불리지 않는다 -- 엔진 소스(tests 제외)에 `converge`·`place_layout`·`converge_point` 호출자가 없고(2026-10-15 grep), `find_front` 모듈 머리도 '`convergence.converge`가 이 front를 받아 한다; 패키지 순서상 여기서 부를 수 없고 U16 파이프라인이 부른다'(`E/search/find_front.py:12`)라고 적는다 -- 규칙 C 층 순서(search 6 < convergence 8)상 search는 convergence를 import할 수 없다. 엔진 안 호출은 convergence 패키지 안(`converge` → `converge_point`)뿐이다. 그래서 **find_front 범위 밖이고 E_total 대상이 아니다**. MOD8 재평가의 예산(K_max 등)은 U16 배선 card의 design 몫이다. (6) **'예산 부족' 형식**(N-3, **오케스트레이터 기본안** -- 사용자 결정 아님, 원칙: 기존 반환과 의미 구분·fail-closed·결정성): `fd_jacobian`은 평가를 하나도 하지 않고 예외 `FdBudgetShortfall(needed, remaining)`(`E/search/fd_jacobian.py` 안 정의, `Exception` 직접 하위 -- 후보 실패 클래스가 아니어서 커널의 후보 실패 잡기에 걸리지 않는다. `fd_jacobian`이 이름으로 참조하므로 규칙 A 진입점이 아니다)을 던진다. 근거: 반환값 자리의 표식은 기존 열 실패 `(None, h)`와 섞이거나 부르는 쪽이 놓쳐도 조용히 지나가지만, 예외는 잡지 않으면 실행이 멈춘다(fail-closed). 결정은 평가 수만의 함수라 결정적이다. 처리 경로(`fd_jacobian` 호출부 5곳 전부, 609965d): (i) 반복 중 야코비안 `E/search/slsqp_outer.py:148`(`solve_eps.jac_of`)·`E/search/layer0_center.py:322`(`_maxmin.jac_of`) -- 이름으로 잡아 그 파일의 `_Abort("eval_budget", entry["x"])`로 바꿔 던진다. 그 뒤는 as-built 예산 정지 경로 그대로다(`slsqp_outer.py:203-207`·`layer0_center.py:382-386`: `aborts`에 기록하고 반복을 끝내 수락점 중 best를 고른다). `FdBudgetShortfall`은 `_Abort`의 하위가 아니고 파일 밖으로 `_Abort`를 내보내지도 않는다(`_Abort`는 각 파일 안 신호 그대로) (ii) 첫 스텝 야코비안 `E/search/slsqp_outer.py:176`·`E/search/layer0_center.py:355`(반복 전 FD 스텝 h를 재는 묶음, as-built는 `_Abort` 처리 밖) -- 이름으로 잡아 곧바로 끝낸다: 수락 목록은 시작점 하나이고 best는 as-built 끝 블록의 선택 규칙(외층 `slsqp_outer.py:228-231`: c ≥ 0이면 시작점, 아니면 None)을 그 목록에 그대로 적용한다. 반복 0, 재시작 0, 정지 사유 `eval_budget`, `aborts` = (`eval_budget`,). 층 0은 `_maxmin` 반환 모양 그대로 best = 시작점 항목 (iii) 감도 게이트 `E/search/gate_run.py:63` -- 잡지 않는다. 예약 R 때문에 생길 수 없으므로 생기면 결함으로 실행을 멈춘다(fail-closed). (7) **게이트는 항상 돈다**(X-16): as-built 조건(front 점이 있을 때, `find_front.py:84`) 그대로 돌고 예산 소진으로 `not_run`이 되지 않는다(옛 초안의 `not_run` 기록은 폐기). (8) **실행 끝 확인**: `find_front` 끝에서 커널 평가 수 ≤ E_total을 확인하고 어기면 `RuntimeError`(구조 보장의 마지막 그물). (9) §2.4.5 fail-closed (5)(색인 상한 등록 검사)를 켠다 | card B 병합 | (i) 9회로에서 `perf.kernel_calls` ≤ E_total -- E_B 선언 실행과 E_B 유도 실행 둘 다 (ii) 색인 등록 상한 검사가 켜져 있고 9회로에서 위반 0 (iii) 기준선 재측정과 값 변화 목록((6)) -- 묶음이 탐색 예산 안에서만 시작하고(선언 실행) 유도 실행의 탐색 예산이 D − N_T − R로 줄어 결과가 바뀌는 것은 X-4 기준선 재측정 범위다 (iv) front가 있는 모든 실행에서 감도 게이트 실행(`not_run` 0) (v) 판정 실행과 `test_g10_no_recompute_9circuits`의 선언 E_B는 card 1·A·B와 같은 40 그대로다(사용자 결정 X-17(2026-10-15 "나로 해") -- 옛 기본안 '40 + R'은 폐기). E_total = 40 + R | `test_search_ceiling.py`·`test_search_stop.py`(신규, 규칙 H): 정지 사유 `eval_budget`·`wall_budget`, 게이트 뒤 호출 없음 / 선언 E_B → E_B 그대로(작은 선언값도 거부 없음), 유도 전 None, 평가 시간이 n_θ + 1개 이상이면 첫 n_θ + 1개로 D(더 많아도 같은 값), `eval_budget_source` 형식, `evaluate`는 유도하지 않음 / **경계값**(N-b): 전이 호출에서 커널 평가 수 = 탐색 예산이면 `ValueError`(`time_budget_below_search_reserve`), = 탐색 예산 − 1이면 통과 / 게이트 전(`final=True`) 유도는 커널 평가 수 = D − N_T − R이면 통과, + 1이면 `ValueError` / 전이 뒤 커널 평가 수 = 탐색 예산이면 `search_stop` = `eval_budget`(정상 정지, 예외 없음), + 1(주입)이면 `RuntimeError` / 단일 평가: 커널 평가 수 = 탐색 예산 − 1이면 평가, = 탐색 예산이면 평가 안 함 / `test_fd_jacobian.py`: 경계값 -- 남은 탐색 예산 = 상계면 실행, = 상계 − 1이면 평가 0·`FdBudgetShortfall`(needed·remaining 값), 탐색 예산 None이면 확인 없음 / `test_start_points.py`·`test_layer0_center.py`: 사다리 칸·주어진 시작점이 예산에 닿으면 평가 안 함(`eval_budget`), 층 0 시작점 재확인은 예산에 닿아도 캐시 적중으로 읽음 / `test_kernel.py`: `evaluate`가 `eval_budget`을 바꾸지 않음 / `test_layer0_center.py`·`test_slsqp_outer.py`: 반복 중 `FdBudgetShortfall`이면 정지 사유 `eval_budget`·`aborts` 기록, 첫 스텝에서면 반복 0·best = 시작점(c ≥ 0일 때), 커널 평가 수 ≤ 탐색 예산 / `test_l_bin_search.py`·`test_eps_sweep.py`·`test_residual_probe.py`: 탐색 예산으로 정지·계획, 해상도 기록 칸 `E_B` = `search_ceiling` 값 / E_total이 끝까지 정해지지 않는 실행(평가 n_θ 이하): 게이트 전 한 번 유도 / `test_gate_run.py`·`test_find_front.py`: 탐색이 탐색 예산을 다 써도 게이트가 돈다, 끝 확인 위반 `RuntimeError`(주입) / `test_s3_index.py`: 상한 초과 등록 `RuntimeError`, E_total 미정이면 정해질 때 한 번 검사 / `E/tests/integration/test_g10_no_recompute_9circuits.py`: 커널 평가 수 ≤ E_total 단언 추가, E_B 미선언(유도) 실행 한 회로 이상 포함 | auditor가 9회로를 card B 병합본과 C 병합본에서 실행(선언 E_B = 40, 같은 환경) + E_B 미선언 실행: (i)·(ii)·(iv) 결과 JSON, (iii) 값 변화 목록. 결과 JSON 형식 변경: 없음(옛 초안의 게이트 `not_run` 기록은 폐기). 다만 `perf.eval_budget`의 뜻은 선언 실행 = 탐색 예산 E_B, 유도 실행 = D = E_total로 갈린다(칸 이름·형식 그대로, `perf.eval_budget_source`로 구분 -- 판정 기록과 결과 문서 설명에 이 한 줄을 쓴다, N-3) |

배선(사용자 원칙 '만들면 반드시 배선'): `ThetaCoords`는 세 풀이가, 계수 상태 memo는 `build_search_context`와 `evaluate`가, `S3Index`·`RunCounters`·`graft`는 모든 블록 호출이, `partial`은 `evaluate`·S3 evals가, 실패 기록 등록·재연은 모든 블록 호출이, 묶음 예산 확인은 `fd_jacobian`과 그 호출자(층 0·외층·감도 게이트)가 같은 card 안에서 쓴다. 쓰이지 않는 새 이름을 남기지 않는다.

**(6) 기준선 재측정**(사용자 결정 X-4, card A 판정에서): RT로 층 0·외층·감도 게이트 궤적이 바뀌므로 다음을 새 코드에서 다시 재고, 판정 기록에 값 변화 목록(회로·칸·옛 값·새 값)을 남긴다.
- 9회로 탐색 결과(front·pending·unmeasured 점, ε 풀이 기록, 층 0 결과, `perf` 계수, S3 evals·runs) -- card 1 xrun 판정(029f9b7)이 쓴 값과의 차이.
- `E/tests/integration/fixtures/u17_1b_s0_baseline.json`(S0 수준 칸 지문): RT·W는 S0 수준 계산을 바꾸지 않으므로 같아야 한다. 다르면 결함으로 보고한다.
- LUT memo 계수(영역별 상한·`evictions`·`hits`·`misses`): U_eval을 재는 점이 '실행의 첫 커널 평가'로 바뀌어(§2.4.6 'U_eval을 재는 점', X-1 (2)의 의도된 변화) 회로에 따라 달라질 수 있다. 값 변화 목록에 넣는다.
- 탐색 값을 고정한 test 단언(층 0·외층·감도 게이트·`find_front`의 θ·평가 수·`seq` 등): test 작성 주체가 grep으로 목록을 만들고 새 값으로 다시 쓴다. 기준 약화(허용 폭 넓히기)는 하지 않는다.
- card B는 궤적을 바꾸지 않으므로 기준선을 다시 재지 않는다((5) B (iii)가 그 확인이다).
- card C(사용자 결정 X-8)는 FD 묶음·감도 게이트가 예산에 들어가 궤적이 바뀌므로 같은 방식으로 다시 재고 값 변화 목록을 보고한다(X-4 범위).

**(7) 결정**: Q12(U-96)·Q13(U-97)은 사용자 결정 X-8·X-9로, 감도 게이트 clip(9번)은 사용자 결정 X-14(2026-10-15 "9번 권고대로 해")로 닫혔다. 이 절에 남은 열린 질문은 없다. 후속(범위 밖): 감도 게이트 기준점이 상자 밖이면 '검사 못 함' 보고(§11 XRUN-F1 행).

---

## 3. 단계별 설계 (gain-budget 핵심은 41)

### 3.1 GB0 -- spec·topology 로드 (MOD2)

**알고리즘**: topology를 닫힌 어휘로 읽고 거부 게이트를 순서대로 적용한다: `supply_nets` 필수 → 숨은 레일 (iii) → 넷 대소문자 유일 → `bias_inputs` 선언·gate 전용 → `source_manifest` 수 대조 → 태그 키 무시(U-50). spec은 출처 필수 제약, 정본 이름, `optional_stages` 화이트리스트, θ 범위를 읽는다.

**출력**: 검증된 `Topology`, `SizingSpec`, S0 지문. **실패**: `SchemaRejectedError`(exit 7).

**이 설계가 추가하는 spec 필드**(MOD2 로더):

| 필드 | 형식 | 소비자 |
|---|---|---|
| `gain_budget_db_override` | `[{block: [출력노드 넷 이름, ...], value_db, source}]`. 블록 키는 출력노드 이름을 정렬한 배열이다(41 §1.7-3) | 41 §5.7 |
| `structure_count_budget` | `{value, source}`, 선택 항목. 없으면 LUT 격자에서 유도한 값을 쓴다(41 §0) | 41 §0 |
| 잡음 제약 `noise_th_in_v2hz`·`noise_fc_in_hz`(보고), `noise_excess_th`(가드), `noise_out_int_vrms`(폐루프 적분) -- 주파수·대역 필드 없음(41 §7.1: 주파수를 숫자로 고르지 않는다, `freq_hz`는 `unknown_key`). 옛 이름 `noise_in_density_ss_v_rthz`·`noise_in_integrated_ss_v`는 `metric_unknown` | `constraints[]` 행, `source` 필수 | 41 §7.1 |
| `driving_spec` | `{slew_rate_v_per_s?, load_peak_amp?, load_dc_amp?, source}` | §3.8 `ls` |
| `search.untie_orbits`(as-built, 옛 설계 이름 `symmetry_untie`) | `{원소 이름: {source}}`(MOS·수동소자, `user_spec`만, 원소가 topology에 없으면 `untie_element`) | §6 |
| `cm_sense_elements` | `[<요소 이름>]` + `source: user_spec` | §5 `[ng-cmfb-pm]` |
| `element_values.<el>.measurement_load` | bool | §7.1 `[ng-area-budget]` |

| 항목 | 상태 | 증거 |
|---|---|---|
| topology 게이트(supply_nets·숨은 레일·manifest·태그 키) | OK | `E/authoring/rails.py`, `hidden_rails.py:16`, `source_manifest.py:19`, `topology_schema.py:22` |
| gate 전용 바이어스 넷 | DEV(승인됨): `ports` role 대신 최상위 키 `bias_inputs`(사용자 Q9 (i)). 계획서 DEC-94 문구를 고쳐야 한다 | `E/authoring/bias_inputs.py:20` |
| 옛 이름 거부 | DEV: topology에는 `legacy_name` 표가 없다(닫힌 어휘로 대신 거부). topology `ports.direction`을 필수로 받는다(`E/authoring/ports.py:22,57-59`). spec 정본 이름 `input_dc_net`·`topology_hash`·`derived` 거부는 U5에서 고쳐졌다(bd19cc6 `_spec_fields.py:28`). **설계(사용자 승인(2026-10-12 P), P-4)**: (1) `ports`는 topology에만 있다(P N3.16 v6.5, N3.15 정정). spec의 `ports`는 위치가 틀린 필드로 거부한다 (2) 포트 방향은 role에서 유도한다(입력 role → input, 출력 role → output). `direction` 키는 흡수된 옛 이름이라 `SchemaRejectedError`로 거부한다(필수 아님). role 어휘 밖이라 방향을 유도할 수 없는 포트는 `port_role`로 거부한다 (3) 옛 이름 표는 같은 파일의 정본 이름과 겹치지 않는다: 로더 test가 두 집합의 교집합 = ∅를 단언한다 | `E/authoring/_spec_fields.py:28-36`, `E/authoring/ports.py:22-70`, `authoring/CONTRACT.md:151-152,201` |
| 문자열 값 안 옛 이름(P N3.16) | `tests/authoring/test_old_names_in_string_values.py`: library spec·topology의 **모든 문자열 값**(예 `value_from_spec: "PM_target_deg"`)을 훑어 옛 이름 표 원소가 0개임을 단언한다(키 검사는 로더가 하고 값 문자열은 이 test가 한다) | MISS | -- |
| `human.objective` 형식(P N3.15·DEC-77) | as-built 형식 `objective.budgets[{axis, value, source}]`(axis ∈ `OBJECTIVE_AXES` = `power_dc_w`·`area_search_m2`, `E/authoring/spec_settings.py:62`)이다. 최적화 축은 (전력, 면적)으로 고정이라 이 필드는 축 선택이 아니라 선택적 축 예산이다. 결정 11로 면적 예산은 판정 제약 `area_search_m2 <= 값`으로도 선언되므로, 같은 축의 예산이 두 곳에 있으면 로더가 `duplicate_axis_budget`로 거부한다(FR-9 개념 하나·위치 하나). 예산이 없으면 front를 내고 정지한다(DEC-77) | PART | `E/authoring/spec_settings.py:62` |
| spec `origin`(U-04, P N3.15 `meta.origin`, SC-d) | **결정**(사용자 결정 2026-10-12 "U-04 권고대로"): `meta.origin` ∈ {`canonical`, `fixture`} 필수, 없으면 로더 거부(`SchemaRejectedError`). `fixture` spec은 자기 지문을 선언하고 정본 유도 임계값(canonical spec의 `_derived`·`value_from_constraint` 대상)을 읽지 않는다 -- 참조하면 로더 거부 | MISS | -- |
| `gain_budget_db_override`·`driving_spec` | MISS: 로더가 `unknown_key`로 거부한다 | `authoring/SPEC_CONTRACT.md:226-228` |
| `spice_unverifiable[]` 사전 출력(DEC-90 (3)). **형식**(2026-10-09 정의): metric 서명(`MetricSignature`, 레지스트리와 계산 대기 카탈로그 모두)에 `oracle_measure: str \| None` 필드 -- 그 metric을 재는 오라클 measure 이름(`tools/spice_oracle` 출력 이름, 엔진은 이름만 들고 오라클을 import하지 않는다), 잴 수 없으면 None. spec 로더가 `SizingSpecDoc.spice_unverifiable` = 판정 제약(`judged`) 중 `oracle_measure is None`인 metric 이름 tuple(정렬)을 만들고, 단계 A 보고서 맨 앞에 실행 전 출력한다. 대응표는 metrics CONTRACT에 두고 U6 measure(잡음·offset MC·스윙·ICMR 포함)로 채운다 | MISS | -- |
| 면적 예산 제약 | PART: master는 `objective.budgets` 형식만 있다(9회로 모두 pending). 제약 행은 `[ng-area-budget]`에 있다 | `E/authoring/spec_settings.py:62` |

### 3.2 GB1 -- 구조 유도 (MOD3)

**알고리즘**은 P 용어집 '소자 역할'과 DEC-17·60·61·64·71·93을 따른다. 처리 순서: DC 전도 그래프(잎 가지치기·병렬 합침) → 가지·기둥 → DC 역할 → `equal_vgs`·kcl 그룹 → G_vgs 사이클 v0/v1/v2/VDS-1 → matching 레코드 → L 동치류와 그 주인.

**불변식**:
- 모든 유도 사실에 status와 evidence{rule, nets}가 있다.
- `review_needed`가 남아 있으면 GB4 앞에서 `StructureUnresolvedError`(exit 2)로 정지한다.

| 항목 | 상태 | 증거 |
|---|---|---|
| DC 역할(묶음 4개, 멤버 10) | OK. 규칙 (4) `structure.json` 상속은 MISS | `E/graph/dc_roles.py:52` |
| 가지·기둥(파일럿 41/62) | OK | `E/graph/columns.py` |
| G_vgs 분류 | OK | `E/graph/gvgs_cycles.py:56` |
| matching(J14·DEC-93, `mirror_tail_ratio`) | OK | `E/graph/matching_groups.py:78` |
| 차동쌍 유도 조건 '신호 gate 정확히 2' | PART: 뷰가 없어 바이어스 형제를 빼는 단계만 적용한다 | `graph/CONTRACT.md:538` |
| L 동치류 주인(DEC-17)과 L 공유(LR1) | DEV: `l_class`가 proposed라 평가 경로가 읽지 않는다. 소자마다 L이 따로 있다 | `graph/CONTRACT.md:220`, `E/sizing/theta_schema.py:6` |
| 교류접지 | PART: 정적 (1)(2)만 있다. (3) 이상 전압원은 정지, (4) 뷰별 바이어스 종속 넷은 41 §1.2로 넘긴다 | `E/graph/ac_ground_static.py` |
| 기둥↔블록 매핑표, `vertical_stack_id` 대조 | MISS. 블록(41 §1)이 생긴 뒤 §3.3에서 만든다 | -- |
| `structure.json` ratified 로드, declared/ratified 전이 | PART `[u1-sp1]`: 로더와 `drive_kind`·`stage_members` 소비만 있다. 아래 보완 3의 신규 concept, confirm 전이, `structure_rule_fp`는 MISS(U1b) | `[u1-sp1] E/graph/structure_load.py` |
| 복합 diode(41 §1.12.1)를 DC 역할 규칙 1로, `dc_role` 상속(규칙 4) | MISS(U1b) | `E/graph/dc_roles.py` 규칙 4 '구현하지 않는다' |
| L 동치류 주인 `main_path_signal`(41 §1.12.5) | MISS(U1b). as-built는 tail → current_source_member → name_order | `[u1-sp1] E/graph/l_classes.py` |
| 단계 A가 `declared_loop_cuts`를 넘김 | MISS(U1b) | `[u1-sp1] E/pipeline/stage_a.py` `run_stage_a`의 `build_s1v` 호출 |

**설계 보완**:
1. L 동치류는 GB1이 `derived`로 낸다. 증거는 LR1 규칙(같은 gate 넷·같은 source 넷·같은 kind인 `equal_vgs` 멤버)이다. θ 스키마는 동치류당 L 변수 하나를 둔다. 주인 선택은 DEC-17 순서를 따르되, 'gain 제약 전달 뷰의 첫 gain stage에 붙은 tail' 판정은 GB2 S1v가 생긴 뒤에 확정한다.
2. `structure.json` 로더를 둔다. `topology_hash`·`rule_hash`가 S0와 맞을 때만 ratified 사실을 적용하고, 다르면 해당 사실을 `review_needed`로 되돌린다(P N3.3 전이 표).
3. **`structure.json` 개념 어휘·소비 방식·파이프라인**(J 공동분석, 사용자 결정 2026-10-08 "j해석은 네의견에 모두 동의해."). 구조 규칙은 41 §1.12에 있다. 여기서는 회로 해석 사실을 담는 그릇과 그 소비만 정한다.

   **형식**(P N3.3 그대로): `{schema_version, topology_hash, rule_hash, facts[{concept, subject, value, status: "ratified", evidence{rule, nets[]}, approval_id}]}`. `subject`·`value`는 문자열이다. 넷·소자 이름 여럿을 담는 subject는 이름을 정렬한 **JSON 배열 텍스트**로 쓴다(예: `["M6","M8"]`). 구분자 문자열을 쓰지 않는 이유는 블록 키(41 §1.7-3)와 같다.

   **concept 어휘**(닫힌 어휘. 밖의 이름은 `SchemaRejectedError`, gate `structure_json`):

   | concept | subject | value 어휘 | 소비 방식 | 소비 코드 |
   |---|---|---|---|---|
   | `drive_kind`(기존) | 넷 | `voltage` \| `current` | override | `build_s1v`(구동 종류 고정, `[u1-sp1]` 구현됨) |
   | `stage_members`(기존) | 출처 이름 | 소자 이름(공백 구분, 기존 형식) | declared 대조 | 단계 A → `declared_compare`(`[u1-sp1]` 구현됨) |
   | `dc_role`(신규) | 소자 | `signal` \| `bias_current_source` \| `diode_reference` \| `diode_reference_composite` \| `diode_reference_composite_cascode` | 유도 결과가 J-U3-c `review_needed`인 소자는 **override**, 그 밖은 **confirm** | `E/graph/dc_roles.py` 규칙 4(상속, J-U3-b. 사실이 생겨 구현한다) |
   | `loop_role`(신규) | 루프 id | `loop_view` \| `compensation_internal` \| `composite_diode_internal` \| `bias_scc` | confirm | `E/graph/loop_roles.py` |
   | `feedforward_cell`(신규) | 소자 | `ff:<탭>-><merge>` \| `ff_bias:<탭>-><merge>` \| `ff_load:<탭>-><merge>` | confirm | `E/graph/feedforward_cells.py` |
   | `ac_ground_exception`(신규) | 넷 | 뷰 id | override(그 뷰 한정, 41 §1.12.6) | `E/graph/ac_ground_view.py` |
   | `matching_pair`(신규) | 소자·수동소자 쌍(JSON 배열) | `branch_symmetric` | override(레코드 추가, status ratified, evidence에 approval_id) | `E/graph/matching_groups.py` |
   | `l_owner`(신규, C-3 사용자 결정 2026-10-12 "7절 권고대로") | L 동치류 대표 멤버 목록(동치류 멤버 이름 정렬 JSON 배열) | 주인 소자 이름(그 동치류 멤버) | override(41 §1.12.5 주인 규칙 1~4를 덮음. 주인이 멤버가 아니거나 subject가 엔진 유도 동치류와 다르면 `structure_fact_mismatch`, 그 동치류가 없으면 `structure_fact_orphan`) | `E/graph/l_classes.py` |

   - 루프 id: 루프 뷰는 as-built 뷰 id `loop:<끊는 소자>:<끊는 넷>`이다. 루프 뷰가 아닌 사이클은 정준 회전(이름 정렬 첫 노드에서 시작)의 노드 이름 JSON 배열이다.
   - `<탭>`·`<merge>`가 넷 이름이므로 `feedforward_cell` value는 `->`로 잇는다. 넷 이름에 `->`가 들어 있는 topology는 로드에서 거부한다(`structure_value_ambiguous`).
   - **L 동치류 주인**은 기본적으로 41 §1.12.5 규칙의 산출이다. 구조 규칙이 이름 순서(`l_owner_name_order`)로만 가르는 동치류는 `l_owner` 사실이 덮는다(C-3). status·rule_hash 규칙은 다른 concept와 같다(`l_classes.py`가 `structure_rule_fp` 대상이다: S1V_RULE_FILES에 이미 있다). 회로별 주인은 사용자가 정한다(nmcnr {M104, M105} → M105, 사용자 결정 2026-10-12 "C-3은 네 제안대로 해").

   **소비 방식**(사실을 조용히 버리지 않는다, EP-8):
   - **override**: 엔진이 구조로 정하지 못하는 값을 사실이 정한다. 적용한 사실은 S1v `applied_facts`에 남긴다.
   - **confirm**: 엔진이 유도한 값과 대조한다.
     - 같으면 그 유도 레코드의 status를 `ratified`로 올리고 approval_id를 붙인다.
     - 다르면 `review_needed`(`structure_fact_mismatch{concept, subject, derived, ratified}`)다.
     - 엔진이 그 subject를 만들지 않았으면 `review_needed`(`structure_fact_orphan`)다.
   - **declared 대조**: 기존 그대로다.

   **rule_hash**:
   - `structure_rule_fp()`는 사실이 대조하거나 덮어쓰는 값을 만드는 모든 graph 파일의 지문이다. 대상 = `S1V_RULE_FILES` ∪ {`composite_diode.py`, `dc_roles.py`, `gs_groups.py`, `matching_groups.py`, `feedforward_cells.py`, `loop_roles.py`}.
   - 로더는 `s1v_rule_fp()` 대신 이 지문으로 stale을 판정한다. as-built는 S1v 파일만 보므로 S1 쪽 소비 파일이 바뀌어도 stale을 못 잡는다.
   - **작성 순서**: 사실 파일은 U1b 코드가 master에 병합된 **뒤에** 그 코드의 `structure_rule_fp()`로 쓴다. 먼저 쓰면 코드 병합 즉시 `structure_fact_stale`로 되돌아간다.
   - **규칙 파일이 나중에 바뀌면**: 사실은 stale(review_needed)이 된다.
     - confirm 사실은 오케스트레이터가 새 코드의 유도 결과가 사실과 전부 같음을 보인 대조 기록을 남기고 새 rule_hash로 다시 쓴다. 해석이 바뀌지 않았으므로 같은 approval_id를 쓴다.
     - override 사실은 사용자가 다시 확인해야 한다.

   **파이프라인 수정**(`E/pipeline/stage_a.py`, `[u1-sp1]` 기준 `run_stage_a`):
   1. 순서: A1 로드 → **사실 로드**(topology 지문 = `doc.connectivity_fp`라 `build_s1` 전에 이미 있다) → `build_s1(doc, supplies_v, structure=facts)`(`dc_role` 사실 소비) → `build_s1v(..., structure=facts, declared_loop_cuts=cuts)`.
   2. `cuts`: spec 루프 뷰 선언(`ViewDecl` kind loop)의 끊는 넷 중 안정도 제약 행(`pm_*` metric)이 그 뷰를 가리키는 것이다. 단계 A가 spec에서 직접 계산한다(authoring 소유 파일을 고치지 않는다). 지금 `[u1-sp1]` `stage_a.py`는 이 인자를 넘기지 않아, spec에 루프 안정도 제약을 선언해도 `undeclared_loop_constraint`가 풀리지 않는다.
   3. S1 키에 적용된 `dc_role` 사실의 지문을 넣는다. 같은 topology라도 사실이 다르면 S1이 다르다.
   4. 단계 A 보고서에 다음을 출력한다: `applied_facts`, `structure_fact_*` 기록, `ff_ratio_candidates`, `buffer_window_report`(41 §4.6), `required_input_cm_v`(SP-2 (c) 회로).

   **회로별 사실 표(작성 예정 -- U1b 병합 뒤 오케스트레이터가 쓴다)**: 아래는 J 결정이 정한 내용이다. confirm 사실은 U1b 9회로 실측 결과가 이 값과 같을 때만 쓴다. 다르면 쓰지 않고 차이를 보고한다.

   | 회로 | concept | subject | value | 방식 | 근거(패킷) |
   |---|---|---|---|---|---|
   | ngcc_3stage_ff | `feedforward_cell` | M6B, M6A, M7 / M5 | `ff:ND->Vout` / `ff_load:ND->Vout`(M6A) / `ff_bias:ND->Vout`(M5) | confirm | A.5 |
   | ngcc_3stage_ff | `feedforward_cell` | M14 | `ff:V1->Vout` | confirm | A.5 |
   | ngcc_3stage_ff | `loop_role` | `loop:M8:V1` | `compensation_internal` | confirm | B.5 |
   | ngcc_3stage_ff | `dc_role` | M8, M14(각 1행) | `signal` | override(J-U3-c 그룹) | F.3 |
   | nmcnr_amplifier | `loop_role` | `loop:M201:NodeM2` | `compensation_internal` | confirm | B.5 |
   | current_reuse(파일럿) | `ac_ground_exception` | Vbias2 | `loop:M37a:Voc` | override | C.6 |
   | current_reuse(파일럿) | `dc_role` | M58, M63 | `diode_reference_composite` | confirm | C.6 |
   | sf_pushpull_output_opamp | `dc_role` | M6, M8, M14 / M5, M7, M13 / M9, M17, M11, M16, M20 | `diode_reference_composite` / `diode_reference_composite_cascode` / `bias_current_source` | confirm | D.6 |
   | sf_pushpull_output_opamp | `loop_role` | 복합 diode 내부 사이클 3개({N1,N5}, {N2,N7}, {N12,N13}; U1b 실측) | `composite_diode_internal` | confirm | D.6 |
   | sf_pushpull_output_opamp | `matching_pair` | `["M6","M8"]`, `["M5","M7"]`, `["R1a","R1b"]` | `branch_symmetric` | override | D.5 |
   | sf_pushpull_output_opamp | `drive_kind` | (사실 없음) | -- | **쓰지 않는다**(사용자 결정 2026-10-12 "1, 가로 해", C-1 보완 (가)). 41 §1.5-4 규칙이 N17·N20 = `voltage`(근거 `follower`, M18·M19), N910·N1112·N1516 = `current`(근거 `cascode`)를 구조로 가른다. 9회로 발동표가 예상 집합과 다르면 사실로 메우지 않고 구현을 멈추고 보고한다 | D.6, J12-b, C-1 |
   | nmcnr_amplifier | `l_owner` | `["M104","M105"]` | `M105` | override -- **결정**(사용자 결정 2026-10-12 "C-3은 네 제안대로 해"). 근거: M104·M105는 folding 노드 NMOS 전류 싱크(gate 공통)이고, 주경로 Vin_p→M103→NodeF2→M107→NodeM2에서 F2 쪽 M105의 ro가 1단 R_out ≈ gm107·ro107·(ro105‖ro103)로 gain을 직접 정한다(J-F '주인 = 주경로 신호 소자'와 같은 취지). 사실 파일은 `l_owner` concept 구현(U1b structure 사실) 뒤 쓰고, 단계 A의 `l_owner_name_order` review가 사라지는지 확인한다 | C-3 |

   **사실 파일 상태**: 파일럿 `current_reuse_telescopic_ota.structure.json`(`ac_ground_exception` Vbias2, C-6 사용자 결정 2026-10-12 "7절 권고대로")은 별도 브랜치에서 작성 중이다. 단계 A 통과를 확인하고, 사실이 더 필요하면 다시 승인을 받는다. **`rule_hash` 재기록**(사용자 결정 2026-10-12 "2번 승인.", approval_id `user_decisions 2026-10-12 C-6 재확인`): 사실 내용은 바꾸지 않고 `rule_hash`만 새 `structure_rule_fp()`로 갱신한다. 시점 = ①-d의 마지막 규칙 변경(41 §1.5-4 C-1 보완 (가)·§6-3 전류 기저 열 순서 규칙 반영) 뒤 한 번. 갱신 뒤 파일럿 단계 A의 Vbias2 판정이 갱신 전과 같은지 확인해 보고한다. 달라지면 갱신하지 않고 사용자에게 다시 묻는다. 나머지 회로의 사실 파일은 위 표대로 U1b 병합 뒤 쓴다. nmcnr 파일에는 `l_owner` 사실(subject [M104, M105], value M105)이 들어가고, 쓴 뒤 nmcnr 단계 A 보고서에서 `l_owner_name_order` review가 없어져야 한다. 같은 패턴(전류원 멤버 동률)이 다른 회로에서 나오면 규칙 '동률이면 drain이 주경로 노드인 멤버'로 일반화한다(같은 결정 기록).

**`budget_ref` 엣지는 없다**(P DEC-55·N3.3 S1·N3.16, 사용자 결정 2026-10-12 "다로 해"). 옛 topology 선언 `budget_reference_device`(소자 X의 VDS 예산 기준 소자 Y)의 역할은 S1 레일-레일 기둥(DEC-71 (1), 위 표 '가지·기둥', `E/graph/columns.py`: 레일 쌍 사이 가지 그래프의 모든 노드 단순 경로)이 흡수한다. 노드 전압은 변수 하나이므로 공유 노드 n에서 V(n) = V(레일_Y) ± |VDS(Y)|(Y가 아래 레일 쪽이면 +, 위 레일 쪽이면 −) 항등과 예산 (V_top − V_bot) − |VDS(Y)|는 X·Y가 함께 있는 기둥의 KVL 식에서 저절로 성립한다. 그 노드 변수를 누가 쓰는지는 쓰기 계획 규칙(writer 유일, 봉인 5, DEC-95)이 정한다(§3.7-8).
- topology·spec 키 `budget_reference_device`는 유도 입력으로도, 대조용 declared 엣지로도 읽지 않는다(U-50 lint, 예외 없음). `structure.json` concept 어휘에도 `budget_ref`는 없다.
- 노드를 공유하지 않는 옛 선언 4건(M61→M5, M68→M6, M38→M36a, two_stage_ota M4→M5)은 계획 J8 엔진 유도 항목 그대로다(§9.4).
- 근거 실측(오케스트레이터, master `a3987ab` `build_s1`, 2026-10-12, topology `device_roles`의 `budget_reference_device` 9건):
  - 옛 선언: 노드를 공유하는 옛 선언 5건(파일럿: M9a→M10 Vop1, M9b→M8 Vg15, M18a→M19 Vom1, M18b→M17 Vg25, M60→M66 Vbias4)이 **모두 같은 S1 기둥에 함께 있다(빠짐 0)**. M60은 source = vdd라 아래 29쌍 규칙 밖이지만 기둥 vdd-M60-Vbias4-M66-gnd에 함께 있다.
  - 별도 근거(구조 규칙 후보, 옛 선언 여부와 무관): 'X.source 비레일·X.drain = n 비레일이고, n을 drain으로 쓰는 레일-source MOS Y' 후보 29쌍(파일럿 16 / nmcnr 4 / folded·ngcc·two_stage·two_stage_sf 각 2 / common_gate 1 / pushpull·sf_pushpull 0)이 **모두 이미 같은 기둥에 함께 있다(빠짐 0)**. 예(nmcnr): 기둥 vdd-M101-NodeTail-M102-NodeF1-M104-vss와 vdd-M108-M106-NodeF1-M104-vss.

### 3.3 GB3 -- 결합 변수 y와 기둥↔블록 매핑 (MOD3)

**왜 필요한가**: 41 §5의 층 0 조립은 블록 국소 해들을 이어 붙이면서 블록 경계를 넘는 관계를 등식으로 풀어야 한다. 그 관계 목록이 y다. 따라서 GB3은 정밀 경로만의 기능이 아니라 기본 경로 조립의 입력이다(§8 R2).

**알고리즘**: S1v 블록(41 §1)과 S1 관계 엣지를 대조해 아래 레코드를 만든다.
- K1: 부하 소자가 다른 블록의 미러·L 동치류에 속함.
- K2: 블록을 가로지르는 `equal_vgs`.
- K3: 블록 경계를 넘는 `stacked_vsb`.
- K4: 공유 가지·기둥의 노드전압(매핑표의 공유 소자).
- K7: 여러 뷰가 공유하는 소자.
- K8: 측면 주입(J12-d 계획 기본안. ratify되지 않았다, §9.4).

각 레코드는 `CouplingVar{kind, members, blocks, domain, init_rule}`이다. 매핑표 `column_block_map{column, block, device, shared}`는 S1 기둥과 S1v 블록을 교차해서 만든다.

**불변식**:
- 어느 블록에도, 어느 바이어스 기둥에도 속하지 않는 소자가 있으면 정지한다(`StructureUnresolvedError`, 사유 `column_unassigned`, DEC-71 (2)).

**U10 as-built 보완**(2026-10-09 오케스트레이터 결정, 모두 이름 없는 구조 규칙):
- **바이어스 기둥 = 의사 블록**: 어느 블록에도 속하지 않는 소자만으로 된 기둥(바이어스 기둥)을 K1·K2·K4 판정에서 의사 블록 `bias:<기둥>`으로 센다. 기준 diode(바이어스 기둥)와 블록 소자 사이 미러·`equal_vgs`도 층 0 조립이 지켜야 하는 관계이기 때문이다(예: sf M3↔M4, ngcc M6A↔M7).
- **K3 정의**: 비레일 넷에서 MOS e의 drain과 MOS d의 source가 만나고 둘의 블록이 다르면 `stacked_vsb`(d의 VSB가 e의 VDS에 묶임). 9회로 0건.
- **K1 부하 역할 집합**: {load, mirror, diode_load, tail_source}. 다른 블록·바이어스 의사 블록에서 미러로 전류를 받는 꼬리 전류원도 K1이다(실제 블록과 의사 블록에 같게 적용). 표현은 `BlockRef(view, ("bias:<기둥 id>",))`.
- **K7 범위**: 동작점이 있는 소자(MOS)만 센다. 커패시터·저항은 값이 뷰마다 같아 나눌 것이 없다.
- 레코드에 `nets`(관계가 걸린 넷), 매핑표 행에 `basis`(`block_member`·`column_mate`·`bias_column`)를 더한다.
- `column_unassigned` 범위 = DC 가지에 든 원소. 커패시터·가지치기된 저항은 KVL이 없어 제외한다.
- 소비자는 U15 층 0 조립이며, 그 전에는 단계 A 보고서 `coupling`이 유일한 출구다.
- 관찰(U7로 넘김): 버퍼 블록은 부하 수동소자를 블록에 붙이지 않는다(출력 CL이 블록 멤버가 아님). 이득 블록과 규칙이 다르다.
**상태**: MISS. as-built의 y는 W4 창 위치 [0, 1]로만 있다(`E/search/search_domain.py:97`).

### 3.4 GB4 -- 달성가능성 (MOD5) → 41 §4

41 §4는 다섯 단계로 이루어진다.
1. **LUT 곡선 검사 → 해법 매핑**(41 §4.1). 곡선 칸을 세 가지로 처리한다.
   - 단조이면 역산한다.
   - 비단조이거나 Fritsch–Carlson(FC) 조건을 어기면 격자 전수로 계산한다.
   - 단위가 맞지 않으면 로드를 거부한다.
2. **블록 gain 상한**(41 §4.2). LUT 격자를 전수 계산해 행 memo로 남긴다. 예산을 넘으면 그 상한은 '미상'으로 둔다.
3. **Σ 판정**(41 §4.3).
4. **인증된 면적 하한**(41 §4.4).
5. **DOF**(41 §4.5).

| 항목 | 상태 | 증거 |
|---|---|---|
| LUT 곡선 칸 분류 | PART: 분류는 있다. 해법 매핑이 없고, `op_point`는 FC 위반 칸에서 사유 기록 없이 선형으로 넘어간다 | `E/lut/lut_set.py:124-173`, `E/lut/curve_check.py:37` |
| 2~5 | MISS | `grep -rn "achievab\|block_gain_bound" E/` 0 |

### 3.5 GB5 -- 보상 (MOD5 + sizing θ)

**규칙**은 DEC-92다.
- 값이 선언되지 않은 보상 수동소자는 θ의 연속 성분이다.
- GBW·PM은 봉인된 `ss` 스냅샷의 전회로 MNA로 판정한다.
- 영점 상쇄 저항은 R = 1/Σgm(S)로 정한다(J7).
- `gm_req`는 같은 스냅샷 MNA에서 1-D 근으로 구한다.
- 근사식은 층 0 출발값에만 쓰고, 근사와 MNA의 차를 `comp_approx_gap`으로 기록한다.

**보상 수동소자 후보 집합**은 S1v 극점 노드 목록의 두 노드 사이에 걸린 수동소자다(41 §1.7). 다음 둘은 후보에서 뺀다.
- 루프 뷰 (3-b)의 복귀 경로에만 있고 (2) Miller 구간에 없는 수동소자. 예: CM 감지 평균 저항. 이것이 6a 열린 항목 ⑤의 해법이다.
- spec이 feedback이나 CM 감지 소자로 선언한 요소.

**단일단**: 단일단 여부는 태그가 아니라 구조로 판정한다. S1v에서 이득 블록이 하나이고 Miller (2) 루프가 없으면 단일단이다. `compensation: null` 태그는 읽지 않는다(U-50, DEC-85). 단일단이면 gm_1 ≥ 2π·`gbw_target_hz`·C_out,total을 θ 제약으로 둔다(U-12 기본안). C_out,total = `ss.node_c_farad`(출력노드) + 부하 요소 값이다. U-12가 확정되기 전에는 이 행을 '보고만' 한다. 출발값은 41 §6.5의 매크로 모델에서 같은 값이 나온다.

**CM 감지 소자**(사용자 결정 2026-10-07 'R1·R2 = (b)', 일반화 2026-10-08 "동의", M4): 감지 소자는 출력을 측정 가능하게 부하하지 않아야 하고, 값이 동작점과 무관한 감지 쪽 수동소자는 엔진이 값을 계산한다.

**대상**: CM 분할(§5 `authoring.cm_partition`, `cm_sense_elements` 선언을 반영한 결과 하나만 쓴다 -- 같은 도달 규칙을 다른 모듈에 복사하지 않는다)이 감지(소비) 쪽으로 분류한 소자에 닿은 **자유 수동소자 전부(R·C)**. 자유 = θ 성분이고 값이 DC 동작점을 바꾸지 않는다: DC 전류 기저에서 가지치기되었거나, U2 `current_symmetry`가 **구조적 전류 0**으로 판정한 소자(예: 대칭 출력 사이 직렬 감지 저항 -- CM 동작점에서 양끝 전위가 같다). 2026-10-09 정정: 가지치기만으로 정의하면 결정 (b)의 대상(파일럿 R1·R2)이 빠져 형태 표와 충돌했다. 출력 넷에 직접 닿는지는 보지 않는다.

| CMFB 형태 | 대상 | 값을 정하는 기준이 되는 metric(예) |
|---|---|---|
| 저항 분압(파일럿) | 감지 R | 차동 gain |
| 저항‖커패시터 | 감지 R, C | 차동 gain·PM, PM_cm |
| follower 완충 + 저항 | follower 뒤 R | T_cm(0)·PM_cm(출력은 gate만 부하) |
| triode MOS 평균, DDA | 없음(감지 MOS는 일반 θ 탐색이 정한다) | -- |
| 스위치드 커패시터 | 지원 안 함 | -- |

처리 순서(소자마다 1-D, 다른 θ 고정):
1. 외층이 풀이를 마친다.
2. 손실 행: 선언된 제약 metric m마다 Δm(x) = m(x) − m(소자 제거) 를 정의한다. 소자 제거 = R → ∞ 또는 C → 0 스탬프 제거(ω → 0 및 필요한 주파수에서 다시 푼다). 영향받는 metric = 소자 제거로 값이 분해능 이상 움직이는 metric.
3. 모든 영향받는 m에 대해 |Δm(x)| ≤ b_m(그 metric 분해능 `MetricResult.resolution`)을 만족하면서 **면적이 가장 작은 값**을 `bracket_root`로 찾는다(R은 작을수록, C는 클수록 부하가 크므로 각각 한쪽 경계). 범위는 θ 범위(사용자 결정 8).
4. 그 값으로 바꾼 뒤 평가 커널을 1회 돌려 모든 제약을 다시 판정한다.
5. 재판정에서 이전에 만족하던 행이 하나라도 위반되거나 미측정이 늘면 원래 값을 유지하고 사유를 기록한다.
6. **적용 범위**: 1~5는 front 점마다 한 번씩 따로 적용한다(M4). 모든 점에 적용한 뒤 front를 비지배 필터에 한 번 더 통과시킨다(수동소자 면적이 면적 축에 들어가므로, §9 Q9). 필터에서 빠진 점과 사유는 기록한다.

상수는 새로 두지 않는다. 허용 손실은 각 metric의 분해능이다.

**U11 test 후속 정의**(2026-10-09 오케스트레이터, 결정 (b)의 목적 = 출력 부하 최소화에서 유도):
- **감지 쪽 범위**: 감지 넷 = 레일·출력이 아니고 MOS gate만 걸리며 MOS channel이 닿지 않는 넷. 대상 = 감지 넷을 포함하는 **수동소자만으로 이어진 연결 성분**(channel이 닿는 넷에서 멈춤)에 든 자유 수동소자 전부. 그래서 출력과 감지 넷 사이 수동소자 중간 넷을 거치는 평균망(Ra·Rb·Rc)이 모두 대상이고, channel이 닿는 오차증폭 내부 넷의 커패시터는 대상이 아니다.
- **제거 극한에서 정의되지 않는 metric**: 소자를 없앴을 때 정의가 사라지는 metric(감지 넷이 DC로 떠서 PM·GBW가 미정, CM 루프가 끊겨 PM_cm 미정)은 그 소자의 손실 행에서 **그 metric만 뺀다**(소자 전체를 건너뛰지 않는다). 그 metric의 제약 만족은 4번 재판정이 지킨다. 남은 손실 행이 하나도 없으면 사유를 기록하고 원래 값을 둔다.
- **최소 면적 값**: 손실 경계의 근을 분해능 수준(그 소자 θ의 소신호 상대 분해능)까지 찾고, 근 위쪽 한 칸을 넘지 않는다. 소자 제거는 R → ∞·C → 0 극한으로 구현해도 되나, 그 값은 유도해 주석에 남긴다(as-built: R = √(float max)).

**면적 예산 출발점(as-built U11, 잠정)**: `fit_to_area_budget`이 예산을 넘는 시작점의 ln IDu를 모두 같은 Δ만큼 옮겨 예산 안으로 넣는다. 설계 정본은 41 §6.4 면적 상한으로 출발 구간을 자르는 것(U13)이며, U13이 들어오는 커밋에서 이 이동 방식을 지운다. 선언된 제약이 없어 분해능이 없으면 건드리지 않고 사유를 기록한다.

| 항목 | 상태 | 증거 |
|---|---|---|
| 보상 수동소자 θ 연속 성분 + MNA 판정 | OK | `metrics/CONTRACT.md:555-567` |
| Rz = 1/Σgm 구조 규칙 | OK(J7 ratify 대기) | `E/sizing/theta_schema.py:15-25,79,144`, `E/metrics/ss_evaluate.py:48` |
| `gm_req` 1-D 근, `comp_approx_gap` | MISS | `E/search/find_front.py:45-48`('범위 밖') |
| 극점 노드 목록에서 후보 집합 유도 | MISS(SP1이 없어서) | -- |
| 단일단 gm_1 규칙(U-12) | MISS(계획상 확정 대기) | -- |
| CM 감지 저항 최소 R | MISS | `grep -rn "load_loss\|cm_sense" E/` 0 |

### 3.6 GB6 -- 할당·탐색 (MOD6)

층 0과 gain 예산은 41 §5에 있다. 이 절은 외층이다.

**외층**(as-built를 유지한다):
- 시작점(층 0 조립점 → S3 feasible → x0)마다 ε-제약 SLSQP를 푼다.
- 끝점 E_P·E_A를 먼저 풀고, 면적 상한 쪽은 b_A 간격, 전력 상한 쪽은 b_P 간격으로 스윕한다.
- 비지배 필터를 거친 점에만 L-b를 적용한다(LR10).
- 예산이 없으면 front를 내고 정지한다.
- **보상 단 폴백**(U-51, 사용자 결정 2026-10-12 "U-51은 (나)로"): 보상 단 gm/ID는 θ에 포함한다(DEC-04). 폴백은 **계수 기반**이다: 외층 SLSQP가 그 시작점의 반복 상한(as-built `slsqp_outer` 식 maxiter = Σ_i max(⌈log2(상자폭_i / FD 스텝_i)⌉, 1), `E/search/slsqp_outer.py:179-181`) 안에 수렴하지 못하면 그 시작점에서만 보상 단 θ를 GB5 규칙값(gm_req = DEC-92 MNA 1-D 근, §3.5)으로 고정해 한 번 다시 푼다. 폴백 사실과 이유(`compensation_fixed_fallback{start, reason: slsqp_maxiter}`)를 기록하고 그 점을 '추정'으로 표시한다. 벽시계·U-47 예산에 의존하지 않는다(결정론). 9회로 실행에서 폴백 빈도를 재서 보고한다.

**이 설계가 바꾸는 것**:
1. **예산 점**: 목적 예산이나 면적 예산 제약이 선언되면 그 값을 ε로 고정해 한 번 풀고, 그 결과를 front와 함께 낸다(DEC-77, U-13). 결정 11의 `area_search_m2 <=` 제약은 탐색 축 예산이므로 '면적 ε = 예산 값'으로 전력을 최소화하는 풀이 하나를 추가한다.
2. **제약·목적의 척도화**(§7.2): 행마다 판정 단위와 풀이 단위를 나눈다.
3. **시작점 출처**: 층 0 조립점(41 §5)과 출발 구간 후보(41 §6)를 맨 앞에 둔다. as-built `layer0_center`(θ 상자 중심 + 전류 Chebyshev 중심)는 블록 국소 문제의 기준점 생성기로 옮긴다(41 §5.9 상태). 시작점 출처를 대체하므로 WP-01에 따라 옛 경로를 지운다.
4. `n_starts` 선언과 L-c '분지' 판정을 넣는다. L-c 분지 = bin 벡터가 다른 시작점(LR10).
5. **ε 간격과 점 예산**(DEC-80, H6):
   - **간격**: ε 간격은 격자 분해능이 아니라 DEC-80 (ii) 면적 bin 폭 = max(레이아웃 격자 분해능, 면적 축 모델 오차)다. 전력 쪽 간격은 max(b_P, 전력 모델 오차)다. 모델 오차가 측정되기 전에는 격자 분해능만 쓰고 front를 '추정'으로 표시한다.
   - **점 예산**: ε 점 수 상한 = 외층 예산 N_C = N − (단계 B 사용분)이다. N은 41 §5.8 식으로 구한다. 점 하나의 비용은 실측 풀이 평가 수 중앙값이다.
   - **예산 초과 시**: 간격을 2배씩 넓힌다. 이 2배는 DEC-80 예산 게이트 규칙 그대로이며 새 상수가 아니다. 넓힌 배수와 '해상도 굵음(배수 n)'을 front 표에 적는다.
6. **SLSQP·ε-제약·시작점 출처**(DEC-54): 스칼라화는 ε-제약 하나만 쓰고 가중합은 쓰지 않는다. 시작점 출처는 다음 순서다.
   1. 층 0 조립점(41 §5)
   2. 출발 구간 후보(41 §6.6)
   3. 지문이 일치하는 S3 feasible 점 상위 `n_starts`
   4. 선언 x0
   5. as-built `layer0_center` 점: t_eval을 처음 재는 데 쓰고 다른 출처가 없을 때만 시작점으로 쓴다

   준난수 전역 샘플(DEC-34)은 선언했을 때만 켠다(DEC-75).
7. **근방 반경**: 41 §5.9.

| 항목 | 상태 | 증거 |
|---|---|---|
| ε 두 방향·비지배·L-a/L-b | OK | `E/search/eps_sweep.py:1-14`, `pareto.py:31`, `slsqp_outer.py:49`, `l_bin_search.py:1-12` |
| ε 간격 = DEC-80 bin 폭 + 점 예산 | PART(간격 = b_A = grid × W_min와 2배 예산 게이트는 있음. 모델 오차 항, '추정' 표시, 41 §5.8 예산 식 연결이 없음) | `E/search/eps_sweep.py:1-14` |
| L-c 분지 판정 | PART(시작점마다 따로 돌고 키 중복만 제거) | `E/search/eps_sweep.py:4` |
| 예산 점 | MISS(`budget_point.py` 미작성) | `search/CONTRACT.md:537` |
| `n_starts`, Sobol 전역 샘플(DEC-34, 기본 비활성) | MISS / 비활성 | `search/CONTRACT.md:591` |
| front 표 필드 | PART: 판정 축 면적, gain 예산, gm_id·I0·ln IC 열이 없다 | `E/search/find_front.py:60-70` |
| SLSQP 척도 | DEV: `[ng-area-budget]`이 행·목적·ftol에 임의 양수 상수를 곱한다(§7.2에서 대체) | `[ng-area-budget] E/search/slsqp_outer.py` |
| DEC-88 ln IDu 연속 하한 | DEV: 1변수 writer의 칸 정점·전도 하한을 bounds로 조인다. 설계(사용자 승인(2026-10-12 P), P-7): 동작점 의존 연속 부등식 제약 행으로 바꾸고 bounds 조임을 지운다(§3.10.4) | `search/CONTRACT.md:573`, `E/search/cell_floor.py` |

### 3.7 GB7 -- DC 정본과 봉인 (MOD4)

**규칙**: P N3.4~N3.6. 평가 커널 = ② 전류 → ③ L → ④ 기둥·SCC → ⑤ W → 봉인 1~8. W_request가 있으면 그 소자의 W는 고정 입력이다(LY3).

**이 설계가 바꾸는 것**:
1. **L 동치류 공유**: §3.2-1을 따른다.
2. **미러 비율 강제**: `matching_ratio`(그룹의 W/L 비)를 전류 기저의 강제 관계로 넣는다(DEC-70). 비율의 출처는 θ 변수이며, 대칭 묶음(§6)이 같은 비율 1을 준다.
3. **tol_I**(v1.6 graph 정본 개정, 사용자 결정 2026-10-12 G-3' 승인, P N3.6 v6.4): tol_I = tol_V × 순환 블록 소자 gm의 최댓값이고, gm은 **후보 자기 동작점의 dc 단계 gm 필드 `device.dc_gm` 하나**를 읽는다. `dc_gm` = 그 소자 ID × 그 동작점(L, VGS, VDS, VSB)의 LUT gm/ID(`dc_op.gm_id`)이고 writer는 `dc_tolerances` 하나다. `ss_dev`(as-built는 `op.gm_id * op.current`를 따로 계산, `E/metrics/ss_linearize.py:70`), 봉인 3(`E/sizing/seal_kcl.py:35`), 전력 분해능 b_P(`E/search/search_values.py:123`)가 모두 이 필드를 읽는다. parent에 의존하지 않으므로 같은 θ는 parent와 무관하게 같은 봉인 결과를 낸다. 순환 없음: `dc_gm`은 ⑤ W 블록 뒤의 `dc_op`에서 계산하고 tol_I는 봉인 3에서만 쓴다(SCC 수렴은 tol_V를 쓴다). **폐기**: 옛 문언 'S2p `ss` gm, 첫 평가만 격자 최대 gm'과 as-built U4 경로(`previous_gm_id`·`inherited_gm_id`·`canonical_gm_id`, `E/sizing/kernel_run.py:51-96`, `gm_grid_max`, `dc_gm_bound` 필드). 수동소자 θ만 바뀐 자식의 DC 재사용은 parent 입력을 이어받는 특수 경로 없이 입력 버전 일치로 성립한다(`dc_gm`이 수동소자 θ를 읽지 않는다). 영점 상쇄 수동소자 R = 1/Σ`dc_gm`도 이 필드를 읽으므로 봉인 전 점에서도 정의된다(§2.4.7). **폐기하는 근거**: as-built의 '봉인은 어느 동작점에서나 안전한 상계(곡선 전체 최대 gm)가 필요하다'(`E/search/objectives.py:36-38`)는 쓰지 않는다. 봉인 3이 판정하는 것은 이 후보 동작점의 KCL 잔차이고, 그 허용오차의 gm은 이 동작점의 값이다(사용자 결정 G-3'). 판정 변화는 단계 ①에서 9회로로 재고 기록한다(§2.4.12 Q7).
4. **종속 소자 선택 DEC-95 (3)**: ratified 선택(`structure.json`)과 ② 'GB5 gm 요구·뒤 stage 독립'을 Kruskal 엣지 키 앞에 둔다. ②의 입력은 S1v stage 번호다.
5. **W4 초기값**: 층 0이 배분한 기둥 VDS를 쓴다(41 §5.3.4 (c) VDS 배분).
6. **DEC-12 diode 창**: diode 노드 창은 그 VGS를 공유하는 미러 멤버 전원의 W 한계를 함께 본다. 멤버 VDS가 아직 정해지지 않았으면 그 멤버의 포화 하한 = LUT `VDSAT` 열 보간 + tol_VDsat(DEC-88, 봉인 7과 같은 양)을 바닥으로 쓴다. 멤버의 L이나 ID가 정해지지 않았으면 창을 만들지 않고 `SealViolationError`(사유 `diode_window_member_undefined`, 멤버 기록)로 명시적으로 실패한다. 역할 라벨 바닥(`min_vds_by_role`, DF-20)은 쓰지 않는다.
7. **DEC-13 적층 diode**: `stacked_vsb`로 묶인 diode 두 개는 두 노드전압을 한 W2 블록에서 함께 푼다(2변수 고정점, 수렴·상한은 N3.6). 각 소자의 vsb는 DEC-61대로 그 순간의 노드전압과 bulk 넷에서 유도한다(두 bulk가 같으면 아래 vsb = 위 vsb + 위 vds가 그 특수형이다). 한 소자씩 차례로 풀지 않는다(DF-01 버전 혼재 방지: 두 소자의 W·gm은 같은 반복의 vsb로 계산된다).
8. **`budget_ref` 쓰기 경로 -- 폐기**(P DEC-55, N3.4 W1, N3.16; 사용자 결정 2026-10-12 "다로 해"; design 소관): `budget_ref` 엣지가 없으므로 그 로드·유도·쓰기 경로도 없다. 옛 선언 대상 노드 변수의 writer는 쓰기 계획 규칙(writer 유일, 봉인 5, DEC-95)이 정하고, 예산 관계는 기둥 KVL(§3.2 `budget_ref` 문단)이 낸다. topology·spec 키 `budget_reference_device`는 읽지 않는다(U-50 lint `TAG_ROLE_KEYS_U50`, 예외 없음).
   - **구현 단위 측정 의무**(이 항목이 걸린 구현 단위의 보고에 넣는다): **대상** = 노드를 공유하는 옛 선언 5건(파일럿: M9a→M10, M9b→M8, M18a→M19, M18b→M17, M60→M66). 나머지 8회로는 대상 0건으로 보고하고, 비공유 4건은 J8 소관이라 제외한다. 각 대상(X→Y, 공유 노드 n)에서 (a) 쓰기 계획에서 노드 n의 writer가 정확히 1개(티어·블록 기록), (b) X·Y가 같은 S1 기둥 id에 함께 있음, (c) |B_X − ((V_top − V_bot) − |VDS(Y)|)| ≤ tol_V(N3.6)를 재서 기록한다. V_top·V_bot = 그 기둥 양 끝 레일 전압, B_X = |V(n) − V(Y 반대쪽 끝 레일)|.
   - **as-built**: `E/graph/CONTRACT.md` 4.5의 "`budget_ref`(선언 전용)는 만들지 않는다"는 결과(엣지 없음)가 이 결정과 같다. 그 '선언 전용' 문구는 코드 쪽 정정 대상으로 42 후속 항목에 둔다.

| 항목 | 상태 | 증거 |
|---|---|---|
| W0~W4 writer 계획 | DEV(v1.12 정정): 입력 DC 미선언이면 입력 포트끼리 '같은 DC' 엣지(`input_tie`)로 같은 DC 등식을 커널이 푼다 -- 결정 B2·K-3·O-13 (1)과 다름. card IT-1(계획 N6.5, 41 §6.7-1a·§4.7-1)이 엣지·어휘를 지우고 입력 포트 W4 뿌리 y 키 = 뿌리 넷, 입력 포트 W4 뿌리 둘 이상 = `unsupported_rule_branch`(`input_port_multiple_roots`) 정지로 고친다. 나머지(W3는 9회로 모두 0, CI-15·18 대기)는 그대로 | `E/sizing/writer_plan.py:76-77, :104-105, :157-159, :213-214, :228-234` |
| SCC 고정점·K_max·NONCONVERGENT | OK(+ GS 실패 시 감쇠 Newton, Brent `bracket_root` -- master 병합됨) | `E/sizing/fixed_point.py:21`, `scc_newton.py:33` |
| 봉인 1~8 | OK(+ 계획에 없는 봉인 9 '전도 여유') | `E/sizing/seal.py:30` |
| tol_I | DEV(S2p gm/ID 또는 격자 최대 gm 상계. v1.6 정의 `dc_gm`과 다름) | `E/sizing/seal_tolerances.py:36-45`, `E/sizing/kernel_run.py:51-96`(bd19cc6) |
| 미러 비율 강제 | MISS | `sizing/CONTRACT.md:276` |
| DEC-95 (3) 전체 순서 | PART(① 구조 색·이름만) | `E/sizing/writer_plan.py:13-17` |
| W_request 고정 W | MISS | `E/sizing/block_widths.py:9` |

### 3.8 GB8 -- metric (MOD5)

**규칙**: P N3.8. 모든 metric 판정은 외층 전회로 계산 한 곳에서 한다(DEC-74).

**이 설계가 추가하는 것**:
1. **블록 국소 모델과 잔차**: 41 §2.
2. **감도 게이트**(N3.8): S0 지문이 바뀔 때와 최종 해에서 돈다. 분해 metric(블록 gain)이 읽지 않는 소자를 건드리는 θ 방향으로 섭동한다. ε = ‖A·x − b‖₂/‖b‖₂ × 그 metric의 x 감도로 정한다. 분해 값 변화 ≤ ε인데 MNA 값 변화 > ε이면 오류다. as-built `sensitivity.py`(LUT 파라미터 adjoint로 metric 분해능을 내는 것)는 다른 양이므로 유지하고, 게이트는 새 파일로 둔다.
3. **`ls` 필드**:
   - 방향별 최대 전류는 DEC-65의 β·σ·κ 규칙으로 계산한다.
   - 슬루 등가 용량 `ls.c_slew_farad`를 둔다.
   - 출력 스윙 한계는 P N3.8 경로 합으로 계산한다(card DE-1이 DC 끝점 손계산으로 바꾼다 -- 이 판 범위 밖). 입력 창(ICMR)은 경로 합으로 다시 재지 않고 §2.4.8 입력 포트 창 필드를 읽는다(v1.12 card IT-2, 41 §4.7). metric 정의는 아래 8이다.
   - `driving_spec`이 선언되면 이 값들로 제약 행을 만든다.
4. **보고 metric**:
   - `nqs_ratio` = `ugf_ss_hz` / 신호 경로 소자 최소 f_T. f_T는 봉인 `ss`의 gm/(2π·cgg)이다.
   - 옛 `mismatch_sigma_v`(matching 그룹별 Pelgrom 두 항)는 아래 8의 `offset_in_sigma_mv`·`mirror_ratio_sigma_pct`로 대체한다(사용자 결정 2026-10-08 Q3).
5. **전력 축 = Σ V·I**(`power_dc_w`, 사용자 결정 2026-10-08 Q6. U-10 변경, DEC-78 문구 정정 대상): 레일마다 전압 × 공급 전류를 계산해 더한다. '기둥마다 전류를 한 번 센' 값과의 대조는 매 실행 기록하고, 둘이 어긋나면 `review_needed`로 올린다.
6. **`verified_by`·모델 오차**: 레지스트리 항목에 `verified_by`·`model_error_ref`를 두고, 오라클 대조 결과(DEC-72)를 `derived.model_error_<metric>`에 쓴다.
7. **잡음**(사용자 결정 2026-10-08, 범위 안): 다음 넷을 둔다. 설계는 41 §7이다.
   - 입력 환산 잡음 밀도와 적분 잡음 metric
   - LUT 잡음 열(PDK BSIM4 `.noise` 특성화, 새 버전 파일)
   - MNA adjoint 잡음 해석과 소자별 기여 표
   - 오라클 `.noise` 대조
8. **offset·미러비·스윙·ICMR**(사용자 결정 2026-10-08 "q3,q4는 네 제안대로 해", 근거 `_drafts/engine/matching_swing_spec_proposal.md` §1). 닫힌 어휘로 MOD5 레지스트리에 `MetricSignature`로 등록하고, 레지스트리 밖 이름은 `metric_unknown`으로 거부한다. 옛 이름 `mismatch_sigma_mv`·`mirror_ratio_error_mv`·`mismatch_sigma_v`는 spec 옛 이름 표에 넣어 거부한다(새 이름으로 안내).

| metric | 정의 | 단위 | domain / view_kind | 분해능 | 쓰임 |
|---|---|---|---|---|---|
| `offset_in_sigma_mv` | **입력 환산 랜덤 offset 1σ**. 회로의 **모든 MOS** i에 독립 게이트 전압 오차원 σ_VGS,i(41 §6.4-2 A_eff 모델: LUT 감도 열 × bin별 slope / √(W_i·L_i))를 두고, 봉인 `ss` 스냅샷의 MNA 저주파(ω → 0) 전달로 출력(차동 출력이면 차동)까지 보낸 분산을 합해 차동 이득 A_dm으로 나눈다: σ²_in = Σ_i (Z_i·gm_i·σ_VGS,i)² / A_dm². Z_i는 소자 i 드레인 전류 → 출력 전달 임피던스이고, 잡음 해석(41 §7.3)과 같은 adjoint 해 한 번으로 모든 i를 얻는다 | mv | ss / transfer(gain 제약 전달 뷰) | LUT `tol_mismatch`와 소신호 tol의 adjoint 감도 전파 | 파일럿 제약, 나머지 보고 |
| `offset_excess` | `offset_in_sigma_mv` ÷ (입력 셀 소자만의 같은 합). 입력 셀은 S1v의 gain 제약 전달 뷰 첫 이득 블록 input 셀(`noise_excess_th`와 같은 구조 규칙) | ratio | ss / transfer | 위 두 값의 전파 | 구조 가드 `<= √2`(부하 분산 ≤ 입력쌍 분산의 경계) |
| `offset_sys_mv` | **계통 offset**: 봉인 DC 동작점(실제 VDS 반영)에서 입력 차 0일 때의 출력 오차 / A_dm. 출력 오차 기준은 차동 출력 = Vop − Vom, 단일 출력 = spec에 선언된 출력 기준 DC(선언이 없으면 값을 내지 않고 `reference_undeclared`로 보고) | mv | dc→ss / transfer | DC tol(tol_V)의 전파 | 상한 = `value_from_constraint: offset_in_sigma_mv`(기존 규칙 '계통 ≤ 랜덤 예산', 그 제약이 있는 회로만), 나머지 보고 |
| `mirror_ratio_sigma_pct` | S1 matching 그룹 중 mirror 계열(whole, consumer_symmetric, `mirror_tail_ratio`, bias_distribution)마다 랜덤 전류비 σ(ΔI/I) = (gm/ID)·σ_ΔVGS,pair | pct | dc→ss / 없음(뷰 불필요: 대상은 S1 미러 matching 그룹. view_kind `ratio`는 {num, den} 응답비 뷰라 해당 없음, U5 as-built 2026-10-08) | tol 전파 | 보고만 |
| `swing_out_v` | **포화 기준 출력 스윙**: 출력 DC 동작점을 중심으로, 출력 경로의 모든 MOS가 VDS ≥ VDSAT + tol_vdsat(사용자 SPICE 포화 규칙 + LUT `tol_vdsat_table`)를 지키는 대칭 peak-to-peak 폭. 단일 출력 = 2·min(V_hi − V_o, V_o − V_lo). 차동 출력(포트쌍 p/n) = 출력마다 계산한 반폭의 최솟값 × 4(차동 p-p). [V_lo, V_hi]는 P N3.8 경로 합(VDS 엣지 = 포화 하한, VGS 엣지 = 그 전류의 VSB 포함 VGS)이다. 구간 자체도 레코드로 낸다 | v | ls | tol_vdsat·tol_V 합 | 파일럿·nmcnr 제약, 나머지 보고 |
| `icmr_v` | 입력 공통모드 창의 폭 = 입력 포트 창 교집합 [max_p lo_p, min_p hi_p](각 창은 [rail_lo, rail_hi]로 자름, 레일 밖 입력 불허)의 min_p hi_p − max_p lo_p. **창은 §2.4.8 입력 포트 창 필드를 읽는다**(v1.12 card IT-2, 41 §4.7-5; DE-1 전 한정 -- 커널 = `node.dc_window_cfg`(측정 구성 판정 창, 선형 감도 끝 '추정'; 구성 `as_is_single_input`이면 `node.dc_window` -- 41 §4.7-2 W1), front·보고 = `node.dc_window_def_refined`(끝 풀이)). 경계 = 입력 경로 소자 전부 VDS ≥ VDSAT + tol_vdsat(판정 여유 포함 -- 정의 창 분리는 DE-1). 창이 비면 음수 폭(부족량)을 그대로 낸다. 창 결측·미수렴이면 정의 불능(`input_window_unmeasured`·`input_window_unsettled`·`input_window_end_missing`, 41 §4.7-5) | v | ls(영역 칸 `dc` 전환은 DE-1) | 아래 끝을 정한 포트 창 `tol_v` + 위 끝을 정한 포트 창 `tol_v` | ngcc·nmcnr 제약, 나머지 보고 |
| `icm_margin_v` | 포트별 margin_p = min(V_p − lo_p, hi_p − V_p)의 **최솟값**(IT-Q2 (다), 사용자 결정 O-13 (2)·O-15 (B), 계획 X-IT8 -- 판정이 (나)든 (다)든 계산 경로 하나; 포트 전압 차가 0이면 옛 '첫 포트' 값과 같다). V_p = 해의 그 포트 전압(`node.dc_v` -- 선언 입력 DC면 선언값과 같다), 창 = `icmr_v`와 같은 필드. 경계에 tol이 이미 들어 있으므로 ≥ 0이면 'LUT tol 여유를 두고 창 안'이다. 입력 DC가 SP-2 대기면 SP-2 (c)(J-E, 41 §4.6)에 따라 `required_input_cm_v{value, window}` = 최솟값을 낸 포트의 (V_p, lo_p, hi_p)를 함께 보고한다(결과 JSON 형식 불변). 정의 함수 하나 = `icm_window_metrics`(`E/metrics/icm_window.py`) | v | ls(같음) | 최솟값 포트 창 `tol_v` | 아래 규칙 |
| `ff_gm_ratio` | feedforward 묶음마다 r_ff = G_ff / gm_in(B_b)(41 §1.12.2-5). 묶음이 없는 회로는 값 없음 | ratio | ss / transfer | gm tol 전파 | 보고. spec이 값·`source`를 선언하면 제약(값은 사용자 몫, 출처 후보 You 1997·Leung & Mok 2001) |

   - **topology 무관**: offset은 회로 이름·그룹 규칙 없이 MNA 전달로 계산한다. S1 matching 그룹(J-U4)은 계산 대상이 아니라 **해석·대조**에만 쓴다: 소자별 기여 표 `offset_contrib[{device, share, matching_record}]`를 내고, 기여가 큰 소자가 matching 레코드에 들지 않으면 `review_needed`가 아니라 보고 행으로 남긴다(레이아웃 matching 대상 확인용).
   - **ICMR 제약 규칙**(사용자 결정 Q4 (4)): ICMR = 폭 + 선언 입력 DC 포함. `icmr_v >= w` 제약이 있는 회로는 입력 DC가 선언되면 `icm_margin_v >= 0`도 같은 출처로 함께 판정한다. 3σ 관례는 쓰지 않는다.
   - **판정 위치**: 다른 metric과 같이 외층 전회로 계산 한 곳(DEC-74). 출발 구간(41 §6.2·§6.4-2)은 출발값과 보고에만 쓴다(EP-7).
   - **단위 어휘**: `core/units.METRIC_UNITS`에 `pct`, `ratio`, `v`가 없으면 더한다(`ratio`·`v`는 잡음 경로와 공유).
   - 파일: `E/metrics/offset_analysis.py`(offset_in·excess·contrib), `offset_systematic.py`, `mirror_ratio.py`, `ls_swing.py`(swing, `ls_fields`가 부른다 -- v1.12: 입력 창 계산·인자 `inputs`·`input_dc_v` 삭제, card IT-2), `icm_window.py`(icmr·icm_margin 정의 함수 `icm_window_metrics`, 커널은 `metrics_aux`가, front·보고는 `icm_front.py`의 블록 `metrics_icm_front`가 부른다 -- v1.12, 41 §4.7-5).

| 항목 | 상태 | 증거 |
|---|---|---|
| MNA(ω 무관 조립 + ω별 풀이, gmb, 접합 용량, pencil) | OK | `E/metrics/mna_build.py:47`, `mna_solve.py:42`, `stamp_mos.py`, `junction_cap.py`, `pencil_roots.py` |
| `gain_ss_db`, `ugf`, `gbw`, `pm_ss_deg`(β 또는 β=1), ratio, `parasitic_pm_ss_deg` | OK | `metrics/CONTRACT.md:173-235` |
| `rout_ss_ohm` | PART(블록 테브난 잔차 없음) | `metrics/CONTRACT.md:205-213` |
| 블록 국소 모델·잔차, 감도 게이트 | MISS | `metrics/CONTRACT.md:13-14` |
| `ls`·스윙·ICMR·nqs | MISS | `metrics/CONTRACT.md:14` |
| offset·미러비·스윙·ICMR metric(8) | MISS: spec에 옛 이름 `mismatch_sigma_mv`·`mirror_ratio_error_mv`(파일럿·two_stage·two_stage_sf), ngcc `{metric: pending MOD5}`만 있고 레지스트리 항목이 없다 | `authoring/SPEC_CONTRACT.md:261`(S2), `E/core/units.py:7,13`, `assets/library/current_reuse_telescopic_ota.sizing_spec.json:215,224`, `ngcc_3stage_ff.sizing_spec.json:87` |
| 전력 축 | PART: Σ V·I는 OK(결정 Q6). 기둥 대조 없음 | `E/search/objectives.py:9` |
| 면적 탐색 축 | PART(master는 수동소자 단위 면적 None. MIM·측정 부하 제외는 `[ng-area-budget]`) | `E/metrics/dc_metrics.py:18-19,80-83` |
| `verified_by`, `spice_unverifiable` | MISS | `metrics/CONTRACT.md:246,424` |
| 잡음 metric·LUT 잡음 열·adjoint 해석 | MISS | `grep -rn "noise" E/metrics E/lut` 결과에 해석 코드 없음 |

### 3.9 GB9 -- 기록·레이아웃 수렴·보고·진입점

**S3**: as-built OK(`E/search/archive.py`). **결함**: 디스크 실패 캐시에서 레코드를 복원할 때 float가 repr 문자열로 돌아와 `layer0_center._repairable`에서 `TypeError`가 난다(h_lo). **설계 수정**: S3·실패 캐시 레코드를 타입이 있는 스키마로 둔다. 숫자는 `float.hex` 문자열로 쓰고, 읽을 때 스키마로 되돌리며, 스키마 밖 레코드는 무시하지 않고 거부한다(`archive_record_invalid`). 왕복(쓰기→읽기) 동일성 test를 둔다.

**MOD7 레이아웃**(P N3.17). 대부분 OK다(`E/layout/`). 이 설계가 고치는 것:

| 대상 | 수정 |
|---|---|
| ΔA_tie | `grid²` → `MANUFACTURINGGRID × max(두 점 bbox의 변 4개)`(DEC-79, DEC-95 (2))(`E/layout/floorplan.py:83`) |
| LY5 | `W_adjustable=False`로 바로 완화하는 경로를 지우고, 판정을 MOD8에 맡긴다 |
| LY4 | `matching_L_mismatch` 기록을 넣는다 |
| LY8 | 출력 계약에 `ly.diffusion{ad, as, pd, ps}`를 넣는다. BSIM4 perMod=1 둘레 규약을 따르고, 엔진 접합 용량과 오라클 입력이 같은 값을 쓴다 |
| LY10 | tap은 행마다 넣지 않고 그룹 경계에만 넣는다 |
| LY4 L 혼합 행 대칭(U-67) | L이 섞인 interdigitation 행에서 소자마다 finger 위치가 행 중심에 거울 대칭인지 검사한다. 어긋나면 그 matching 그룹 `review_needed`(사용자 결정 2026-10-12 "U-67은 (나)로") |
| LOD 기하(U-67) | 출력 계약에 소자별·finger별 `ly.lod{device: ((sa, sb, sd), ...)}`를 넣는다. sa·sb = 그 finger gate 가장자리에서 행의 확산 끝(OD 끝)까지 거리(왼쪽·오른쪽), sd = 이웃 finger gate 사이 확산 길이. 행 배치(`row` finger 순서, `finger_pitch_overhead_m`, dummy 폭)에서만 계산한다(DEC-91 `ly.diffusion`과 같은 출처 하나). 엔진 판정은 이 값을 읽지 않는다(사용자 결정 2026-10-12 "U-67은 (나)로") |
| 판정 축 면적 | 수동소자 면적(MIM 배치 면적 = 값/밀도 + PDK 여유)을 포함 항목으로 넣는다. 지금은 MOS 행만 들어간다 |

**MOD8 `convergence`**(U14 구현 2026-10-09, 계약 `E/convergence/CONTRACT.md`; U16 배선 대기). 알고리즘:
- (1) front 점마다 `run_layout`을 실행한다.
- (2) `W_requests`가 있거나 폭 키가 바뀌었으면 그 W를 고정 입력으로 평가 커널을 1회 돌리고 봉인 1~8을 확인한다(LY3·LY7).
- (3) K_max(P N3.6 식, 구간 = W 변경 비)까지 반복하고, 닿으면 NONCONVERGENT로 둔다.
- (4) 수렴한 스냅샷으로 판정 축 면적을 계산하고 front를 다시 비지배 필터에 통과시킨다. 동률 폭은 ΔA_tie다(DEC-79). 순위가 뒤집힌 점은 (1)로 돌아간다. 교대 횟수 상한도 K_max다.

**MOD8 구현 요약(U14)**:
- 진입점 `converge(sctx, pdk_decl, points, pool=(), slice_keys=None)`(점마다 `converge_point` -> `refilter` -> 교대). 호출자는 U16: `find_front(...)` 뒤 `converge(sctx, pdk_decl, front.front)`.
  `convergence` 는 패키지 순서상 `search` 위라 `find_front` 가 부를 수 없다(역방향 import 금지) -- 배선은 파이프라인 몫이다.
- `run_layout` 의 유일한 프로덕션 호출처는 `convergence.place_layout`, 평가 커널 재호출의 유일한 호출처는 `search.evaluate(geometry=)`(키의 `w_fixed_fp` 자리). 봉인 스냅샷 -> `LayoutInput` 어댑터는
  `layout_input_of`(`W_adjustable` = 쓰기 소자, matching = derived·ratified, 수동소자 = `layout.passives_from_decl(passive_values(...))`).
- LY7: 레이아웃 결과마다 실현 기하(모든 소자의 실현 W 고정 + 실현 폭 슬라이스 + 설계점 스냅샷 `ly_diffusion` 필드의 확산 기하)로 평가 커널 1회·봉인·제약 행 재확인. 같은 기하가 나오는 고정점에서 freeze,
  `K_max = k_max(max |ln(W_실현/W_사이징)|, min 실효 W 허용오차)`(첫 레이아웃에서 한 번)에 닿으면 NONCONVERGENT. 접합 용량은 `ss_evaluate(diffusion=)` -> `ss_dev` 가 실현 확산 기하로 계산한다.
- W_request: 그룹 요청(cc_nf)은 요청한 (폭 키, nf) 로 평가, 위반하면 거부(`rejected_requests`) -> 레이아웃은 pattern None -> **완화 판정**(`relaxation_decision`): common-centroid 를 요구하는 그룹이
  pattern None 이고 응답 대기도 아니면(nf 조정·W 조정 모두 불가) hub 가 있는 쌍은 interdigitation 전용 `mirror` role 로 다시 놓고 `Relaxation` 기록(맨 앞 review_needed 대상, dx·dy), hub 없는 branch_symmetric 은
  `not_relaxable` 로 배치 없이 기록한다.
- 판정 축 재필터: 축 (전력, 레이아웃 외곽 면적), 동률 폭 = (b_P 큰 값, `layout.area_tie_m2`) 를 `search.nondominated(ties=)` 에 넘긴다. 교대: `pool`(탐색 축에서 지배당한 봉인 점) 중 탐색 축 면적을 대리값으로 비지배인 점만
  레이아웃·재검증하고 다시 거른다(상한 `K_alt` = `k_max(면적 범위, ΔA_tie 최솟값)`).
- **설계 gap(열린 항목) -- 닫힘**(사용자 승인(2026-10-12 P), P-6): (a) kind당 폭 슬라이스 → §3.10.1(P-2), (b) 종속 소자 W 고정 → §3.10.2(P-3), (c) 쌍 전류비 → §3.10.3 전류비 보장 규칙, (d) 면적 모델 오차 → 선언 전까지 기록만, (e) front 생성 뒤 재측정(U16 완료 조건). 상세는 §3.10.3.

**MOD9 `report`**(MISS): 결과 JSON(DRS 8섹션 키, `perf`, front 표, 출발 구간 표 41 §6.6, `gain_budget_db`, 충돌 표, 실패 레코드)을 낸다.

**MOD10 `pipeline`**(MISS): `run_gmid_design_pipeline`이 GB0→…→GB9를 순서대로 부르고 `exit_code_for`로 끝낸다. `[ng-bridge]`의 `oracle_input`·`front_oracle`을 이 진입점 아래로 옮긴다.


### 3.10 계획 이탈·누락 반영 (사용자 승인 2026-10-12 P)

사용자 결정 2026-10-12 "P-1~P-15까지 권고대로 고쳐"(계획→design gap 분석의 이탈·누락)를 이 문서 몫만큼 옮긴다. 이 절의 내용은 **사용자 승인(2026-10-12 P)**된 것이다. P-1·P-9·P-15와 41 §4.5 문구는 41의 몫이다. P-4·P-5·P-14는 계획 정정이고, 40은 §3.1(P-4)만 고친다.

#### 3.10.1 P-2 레이아웃 finger 폭은 행별, sizing은 소자별 폭 슬라이스 (LY2)

- **규칙**: P LY2대로 finger_w는 물리 행마다 정한다. 한 kind 안에서도 행이 다르면 폭이 다를 수 있다.
- **sizing 쪽 변경**: 평가 커널의 폭 슬라이스를 kind당 하나에서 **소자당 하나**로 바꾼다.
  - `LutAccess.w_keys`: `{kind: 폭 키}` → `{소자: 폭 키}`. 레이아웃이 없을 때(사이징 단계) 기본값은 그 kind의 LUT 기준폭 키이고, 소자마다 같은 값을 넣는다.
  - `w_key_of(lut, kind)` → `w_key_of(lut, device)`. 호출부(as-built `block_columns`, `block_widths`, `seal_tolerances`, `ss_linearize` 등)를 같은 변경에서 바꾼다.
  - 소자 폭 키는 설계점 입력이다: MOD8 재평가의 `RealizedGeometry.w_keys`가 소자별 값을 준다. 평가 키의 `w_fixed_fp`가 이것을 덮는다(as-built 그대로).
  - `dc_op`의 폭 키 칸은 소자 값이다(같은 kind라도 다를 수 있다).
- **폐기**: kind당 폭 키 하나로 레이아웃의 PDK 폭 키를 좁히던 경로(`place_layout`의 `layout_score` 최소 키 선택). MOD8 설계 gap (a)는 이것으로 닫힌다(§3.9).

#### 3.10.2 P-3 차동쌍 시도 순서와 종속 소자의 W 고정 (LY5)

- **순서**: P LY5대로 (i) nf 조정(같은 (ID, gm/ID, L)에서 finger_w를 줄임) → (ii) W 조정(LY3 W_request로 MOD8 재평가) → (iii) 둘 다 안 되면 interdigitation 완화(`relaxed: true`, `attempts[{nf, W, reason}]`, 맨 앞 `review_needed`, dx·dy). 레이아웃은 소자를 미리 'W 조정 불가'로 분류하지 않는다.
- **종속 소자도 W를 고정 입력으로 받는다**: as-built는 종속 소자(좌표 = 노드 VGS 순방향, `dc_coord`)의 W를 고정할 수 없어 차동쌍 `cc_same_W`가 바로 완화로 갔다(MOD8 gap (b)).
  - W가 고정된 종속 소자는 ID와 W에서 전류밀도 ln IDu = ln(ID·L/W)가 정해진다. 그래서 그 소자의 VGS도 `vgs_for_current_density`로 정해진다.
  - 이 VGS와 그 소자를 묶는 관계(`equal_vgs` 등)가 정하는 VGS가 다를 수 있다. 이 차는 봉인 2(VGS 정합)가 판정한다. 위반이면 그 W_request는 거부되고(`rejected_requests`), 다음 순서(완화)로 간다.
  - **LY4 hub 없는 `branch_symmetric`**도 같은 순서(nf → W → 완화)를 따른다. 공유 hub가 없어 interdigitation 완화가 불가하면 배치 없이 `not_relaxable`로 맨 앞 `review_needed`에 올린다(as-built `relaxation_decision`과 같다).
  - 고정 W는 쓰기 계획을 바꾸지 않는다. 종속 소자의 좌표 종류는 그대로이고, ln IDu가 고정 입력으로 더해질 뿐이다.

#### 3.10.3 P-6 MOD8 열린 항목 닫기

§3.9 'MOD8 구현 요약'의 설계 gap (a)~(e)를 다음으로 닫는다. design에 남는 열린 질문은 없다(N9.2).

| 항목 | 처리 |
|---|---|
| (a) kind당 폭 슬라이스 | §3.10.1(P-2)로 해소 |
| (b) 종속 소자 W 고정 불가 | §3.10.2(P-3)로 해소 |
| (c) LY1 소자별 W 허용오차가 소자 사이 전류비를 보장하지 않음 | **결정**(사용자 결정 2026-10-12 "U-71승인", U-71). **전류비 보장 규칙**: matching·미러 그룹의 소자 쌍 (i, j)마다 실현 W 비의 차 \|ln(W_i/W_j)_실현 − ln(W_i/W_j)_사이징\| ≤ min(tol_V,i·(gm/ID)_i, tol_V,j·(gm/ID)_j)를 지킨다. 유도: 같은 VGS를 받는 쌍의 전류비 오차는 W 비 오차와 같고(ΔI/I = Δln W), 봉인 3의 KCL 허용오차가 tol_I = tol_V·gm이므로 ΔI ≤ tol_V·gm ⇔ Δln W ≤ tol_V·(gm/ID)다. 이 규칙은 소자별 LY1 허용오차 위에 더하는 쌍 조건이다. 레이아웃이 finger 후보를 고를 때 지키고, 못 지키면 W_request를 낸다. 결과적으로 재평가 봉인 3이 이 원인으로 거부하는 경우가 없어진다. as-built의 폭 키를 하나씩 빼며 재시도하는 `key_exclusion`은 지운다 |
| (d) DEC-80 (ii) 면적 모델 오차 선언값이 없음 | 선언 전까지 탐색 축 대 판정 축 차를 **기록만** 한다. `review_needed` 승격은 하지 않는다. 선언이 생기면 DEC-80 (ii) bin 폭에 들어간다 |
| (e) front가 0개라 손으로 봉인한 점으로 실측함 | 탐색이 library 회로에서 front를 낸 뒤 MOD8을 다시 잰다(U16 완료 조건) |

#### 3.10.4 P-7 DEC-88 반전 수준 하한 = 연속 부등식 제약

- **규칙**: P DEC-88대로 쓰기 소자 ln IDu의 반전 수준 하한(정점)은 상태(L, VDS, VSB)에 의존하므로 bounds가 아니라 SLSQP **연속 부등식 제약 행**이다.
- **행**: 쓰기 소자 m마다 c_m = (ln IDu_m − floor_m(L_m, VDS_m, VSB_m)) / b_m ≥ 0.
  - floor_m은 그 후보 동작점의 (kind, 소자 폭 키, L, VDS, VSB) 곡선에서 gm/ID 정점의 ln IDu다. LUT 순수 함수이므로 LUT memo 함수다(§2.4.6, as-built `cell_floor._peak_floor`의 칸 최댓값 대신 동작점 값).
  - as-built r9 전도 하한(봉인 9)도 같은 방식의 제약 행으로 둔다(**결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로") U-69, 계획 DEC-88에 봉인 9 명시): floor = 그 동작점에서 ln(gm·tol_V/I_off) = 0이 되는 ln IDu.
  - b_m(분해능)과 정규화는 N3.14 정규화 위반량 규칙을 따른다(다른 제약 행과 같다).
- **폐기**: 칸 정점·전도 하한으로 θ 상자를 조이는 경로(`E/search/cell_floor.py`의 `ln_idu_floors`가 bounds를 바꾸는 것, `search/CONTRACT.md:573`). §3.6 표의 DEC-88 행을 고친다.

#### 3.10.5 P-10 finger 피치 여유를 PDK에서 유도 (I-A12)

- **규칙**: 판정 축 면적(레이아웃 외곽 면적)의 finger 피치 여유 `finger_pitch_overhead_m`은 상수가 아니라 PDK 선언에서 계산한다. 옛 `stick_diagram.PROCESS_GEOMETRY`의 0.0은 쓰지 않는다.
- **식**: 사용자가 ratify한 PDK 레이아웃 규칙 식 다섯 개 중 하나를 그대로 쓴다(사용자 2026-10-08 "4번도 네 판단에 동의해", 대상: finger 피치 여유, 행 간격, dummy, tap, well 간격). 선언 파일은 `assets/sky130_pdk_decl.json`이다. 새 규칙을 만들지 않는다.
  - as-built `layout.LayoutPdk.from_lut`이 이 다섯 길이를 PDK 선언에서 읽는다(`E/layout/contract_input.py:43,129-152`, `layout/CONTRACT.md:226-239`).
  - 실측 sky130: (overhead, gap, dummy, tap, well) = (2.8e-7, 4.7e-7, 5.4e-7, 6.8e-7, 1.63e-6) m.
  - 행 폭 = Σ nf × (L + overhead). finger마다 접촉 확산 하나다(`layout/diffusion.py:7`).
- 판정 축 면적 항목 `AREA_ITEM_FINGER_OVERHEAD`(`E/layout/floorplan.py:79`)가 이 값과 규칙 출처를 함께 쓴다. 계획 I-A12는 옛 엔진 상수에 대한 기록이고, 새 엔진에서는 이 경로로 닫힌다.
- dummy(I-A13 일부)도 같은 ratify 식이다: 행 끝 하나당 `poly.1a + poly.7 + overhead/2` = 선언 `dummy_w_m`(피치/2 근사, `layout/CONTRACT.md:392`). 행마다 양끝 둘이 판정 축 면적에 들어간다(`row_end_dummy_x2_per_row`).

#### 3.10.6 P-11 최종 해의 활성 제약 여유 판정과 활성/비활성 보고 (NFR-5)

- **입력**: 최종 해(front 점과 채택 해)마다 제약 행 k의 판정 단위 c_k(§7.2)와 metric 여유 m_k = c_k·b_k.
- **바닥**: floor_k = max(b_k, ME_k). b_k = 그 metric의 격자 분해능(`MetricResult.resolution`), ME_k = 측정된 모델 오차(DEC-72). ME_k가 측정되지 않았으면 그 행은 **'여유 판정 보류'**다(통과로도 실패로도 세지 않는다).
- **분류**: m_k ≤ floor_k이면 **활성**, 그보다 크면 **비활성**.
- **NFR-5 판정**: (i) 두 목적 축에서 그 해가 front 위(비지배)인가, (ii) 제약마다 활성/비활성/보류와 여유·바닥을 보고했는가. 성능 스펙은 제약이므로 통과/실패가 아니라 활성/비활성과 여유를 적는다(P N6.3).
- **보고 위치**: 결과 JSON front 표의 점마다 `constraints[{metric, op, bound, value, margin, floor, b, model_error, state: active|inactive|margin_pending}]`. 예산 게이트로 bin 폭이 넓어졌으면 '해상도 굵음(배수 n)'과 함께 그 해상도 기준임을 적는다(DEC-80).

#### 3.10.7 P-12 규칙 분기 발동표를 결과 JSON에 출력 (DEC-59)

- **위치**: 결과 JSON `rule_branches`. 전용 파일 `rule_branch_coverage.json`은 만들지 않는다(R7).
- **형식**: `rule_branches[{branch, kind: computed|record_only, views[{view, activated, cells[], out_of_forward_cells[]}], library_activated_circuits, library_verified_circuits}]`.
  - `views`: 발동은 여기 뷰마다 센다. 셀 단위 분기는 순방향 경로 위 셀만 세고, 순방향 밖 셀은 `out_of_forward_cells`에 소자 이름으로 적는다.
  - `kind`: `계산 규칙 있음`(computed) / `기록만`(record_only).
  - `library_activated_circuits`·`library_verified_circuits`: library 회로 중 그 분기가 발동한 회로 수와 검증 발동 회로 수.
- **정지**: 검증 발동 회로가 0인 분기를 탄 회로와 `record_only` 분기를 탄 회로는 탐색 전에 `unsupported_rule_branch`로 정지한다(DEC-59 그대로).
- 실행 하나는 회로 하나라 library 집계(`library_*`)는 실행 안에서 계산하지 않는다. 실행마다 자기 회로 발동만 기록하고 9회로 합계는 U16 통합 test 보고가 모은다(§3.10.9 PN2 결정, "4절도 권고대로").

#### 3.10.8 P-13 그 밖의 누락 항목

| 항목 | design |
|---|---|
| `ID_source` 타입(P N3.7) | 소자 필드 `device.dc_id_source` ∈ {`kcl`(KCL·미러 비율로 정해짐), `ideal_source_ref`(값 선언 이상 전류원), `theta_current`(θ 전류 변수, DEC-70. class-AB 정지전류처럼 게이트-소스 KVL 루프가 있는 가지도 여기다. 그 루프는 전류가 아니라 멤버 gm_id 하나를 종속시킨다, DEC-64)}. writer = 계산 블록 ② 전류. 결과 JSON 소자 행에 싣는다 |
| `tol_V` 정의(P N3.6) | 셀 = (kind, 폭 키, L 점, VDS). 셀 값 = 그 셀 안 내부 격자점의 leave-one-out 보간 오차 최댓값이고, 축 VGS·VDS·VS와 bin 안 L을 쓴다(bin 경계를 넘지 않는다. L 점이 2개인 bin은 검증 전용 중점). 운영 보간과 같은 방법으로 재고, 간격 2배 격자 오차를 2^p(선형 2, Hermite 4)로 나눈다(Richardson, DEC-87). 지표 배정: 봉인 2·3·SCC 수렴·W 허용오차 = ID 환산 지표, 층 0 gm/ID 역산 = gm/ID 역산 지표, 봉인 1·6·8 = 그 전압을 만든 LUT 조회 종류(as-built는 ln IDu 좌표 역산이라 ID 환산 지표, `E/sizing/seal_tolerances.py:5-7`). 계산 함수 정본은 `lut` tol_V 파일이다. 양끝 격자점(leave-one-out 정의 불가)은 같은 bin 안 인접 내부점의 LOO 값을 쓴다(외삽 금지 DF-27, §3.10.9 PN3 결정) |
| 결합 잔차의 쓰임(P N3.7) | 41 B1 r̂(§2.4 단계 B 층)의 소비처 셋: (i) 진단 보고(결과 JSON `diagnostics.residual_probe`), (ii) 6c DoD의 결합 잔차 표(결과 JSON `residual_table[{block, metric, r_hat, r_spread, n_samples, seal_failures}]`), (iii) 신뢰 한계: 잔차가 그 metric의 모델 오차 선언값(DEC-72)보다 크면 그 블록 분해값을 할당 입력으로 쓸 때 `trust_limits[{block, metric, residual, model_error}]`를 함께 기록한다. 판정 위치는 바꾸지 않는다(DEC-74) |
| LY8 3열(P LY8, T8) | 결과 JSON `metric_columns[{metric, engine_at_sizing_w, engine_at_realized_w, spice_at_realized_w}]`. 모델 오차 파일(DEC-72)에는 2열 − 3열만 쓴다. sizing 직후 기하의 SPICE는 진단 실행(태그 `sizing`)이다 |
| 근방 반경 확장 규칙(P DEC-71 인계) | 초기 반경 = 41 §5.9의 r_j = max(\|θ_local − θ_조립\|, h_j)(h_j = 그 성분의 격자 분해능). feasible이 없으면 반경을 2배로 넓힌다. 2배는 DEC-80 예산 게이트와 같은 규칙이라 새 상수가 아니다. 멈춤: 반경이 전역 bounds에 닿거나, 확장에 쓴 평가 수가 DEC-34 예산 식(N = ⌊(B − T_fixed)/t_eval⌋)의 남은 몫을 넘을 때. 층 0은 전역 bounds를 줄이지 않는다 |
| IC3 필드 완전성 | `test_coverage_and_field_completeness`: 결과 JSON에 T1 필드(아래)가 소자·노드마다 빠짐없이 있고, 레이아웃 coverage(`check_stick_diagram_coverage` 대응) 누락 0, 이름 충돌 0. 필수 필드 목록은 결과 JSON 스키마 한 곳에서 정의하고 test가 그것을 읽는다 |
| IC7 무동작 계수 | `test_all_library_topologies_run`: DEC-47 대상 구분상 그 기능이 필요 없는 library 회로에서 그 기능의 발동 계수 = 0(규칙 분기 발동표 `views[].activated`와 블록 계수로 잰다) |
| IC11 거부 케이스 먼저 | P N4.1 IC11 문언 그대로: 같은 test 파일에서 먼저 **레일 셋 이상 또는 음전위 레일 회로를 `supply_nets` 없이 로드하면 GB0 로드 게이트가 거부함**을 증명한다(DEC-60). 거부 픽스처는 합성 음전위 레일 회로(`supply_nets` 없음)와 3레일 회로 `pushpull_follower_buffer`에서 `supply_nets`를 지운 변형 둘이다. 그 뒤 원점 이동 동등성을 단언한다: 2레일 `two_stage_ota` (1.8, 0) 대 (0.9, −0.9) V, 3레일 `pushpull_follower_buffer` (vdd 1.8 / vss 0 / agnd 0.9) 대 (0.9 / −0.9 / 0) V(2026-10-12 gap 재분석 정정: nmcnr는 Q8 정정 뒤 음전위 레일이 없어 쓰지 않는다) |
| 단위 보고 필드(P N6.3, U-18, P-14) | 구현 단위의 보고(결과 JSON과 별개인 단위 완료 보고 스키마)에 `broken_tests[{test, reason}]`와 `criteria_weakened[{criterion, before, after, reason, approval_id}]`를 둔다. 그 옆에 `graph_canon_check{lint_g, type_location, ownership_diff[], g10{recompute_same_input, s0_second_run_computes, lut_recompute_after_eviction}}`와 `reuse_check{g10{...}, blocks[{block, part, reuses, grafts, computes}], duplicate_arg_calls_in_loops, loop_invariants_hoisted[]}`를 숫자와 함께 **항상** 둔다(사용자 지시 2026-10-12 "coding시에 계산값 재사용원칙도 준수되었는지 확인하는 과정을 넣고 이 확인내용을 항상 보고해"). 0개면 빈 목록이다. 기준 약화는 매 건 승인 기록 id가 있어야 한다(U-18) |
| cProfile(NFR-2, U-49) | 진입점 `run_gmid_design_pipeline(..., profile_path=None)`과 CLI `--profile <path>`. 주면 그 경로에 cProfile 파일을 쓴다. P N6.1 단위 6 완료 조건(cProfile 기록 파일)에 들어가고, 그 기록 전에는 탐색 층을 늘리거나 줄이지 않는다(U-49). 시간 수치는 판정에 쓰지 않는다 |
| 공유 계산 블록 변경의 DoD(DEC-51) | 9회로 합격을 낸 뒤 `core`·`sizing`·`metrics`·`search`의 공유 계산 블록 알고리즘을 바꾸는 변경은 9회로 전후 차(노드전압, front, SPICE verdict)를 보고에 붙인다. 명령은 §10.4 '공유 블록 전후 대조'. SPICE verdict가 하나라도 바뀌면 사용자 확인을 받는다 |
| I-C10·U-20 `stack_headroom_slack_v` | **결정**(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로")(U-20): 봉인 항목 1·5가 같은 사실을 보므로 metric을 두지 않는다(봉인 검사로 흡수). 새 엔진 metric 등록부에 이 이름은 없다 |
| I-A13 dummy·LDE | **결정**(사용자 결정 2026-10-12 "U-67은 (나)로", U-67): dummy는 §3.10.5의 ratify 식으로 판정 축 면적에 들어간다. (1) L이 섞인 interdigitation 행의 좌우 대칭 검사를 구현한다: 행 finger 패턴에서 소자마다 finger 위치의 행 중심 거울상이 같은 소자의 finger인지 본다(LY4 common-centroid 정의, 새 상수 없음). 어긋나면 그 matching 그룹을 `review_needed`(`interdigitation_not_mirror_symmetric{group, row, device}`)로 올린다(U12). (2) LOD는 오라클 검증에만 넣는다(아래 §3.9 LY8·§4). 엔진 판정과 LUT에는 LOD가 없다. (3) WPE·PSE는 대상이 아니다(PDK 모델에 파라미터가 없어 규칙을 만들지 않는다) |
| I-A11 크로스오버 주파수 차이 | 옛 엔진의 선언식(36.6 MHz) 대 전체 응답(30.50 MHz) 차이다. 새 엔진은 GBW·PM을 봉인 스냅샷 전회로 MNA로만 판정하고(DEC-74, §3.5), 근사식은 층 0 출발값에만 쓰며 근사와 MNA의 차를 `comp_approx_gap`으로 기록한다(41 §5.5). 그래서 이 차이는 판정에 들어가지 않고 회로마다 측정량으로 남는다. 옛 엔진 원인 규명은 범위 밖이다(P-14) |
| 정밀 경로 선언(DEC-73·76) | spec `search_method`가 정밀 경로(내층 DP·중층 좌표강하)를 선언하면 탐색 전에 `unsupported_rule_branch`(사유 `precise_path_not_implemented`)로 정지한다. 정밀 경로는 기본 꺼짐이고(DEC-73) 구현이 없는 분기를 타면 정지한다(DEC-76 안전망). **결정**(사용자 결정 2026-10-12 "U-66은 (가)로", U-66). 정밀 경로 design은 U-33 측정이 기본 경로 부족을 보일 때만 시작한다 |
| 보상 단 폴백(U-51) | 사용자 결정 2026-10-12 "U-51은 (나)로": 보상 단 gm/ID는 θ에 포함한다(DEC-04). 폴백은 **계수 기반**이다: 외층 SLSQP가 그 시작점의 반복 상한(as-built `slsqp_outer` 식 maxiter = Σ_i max(⌈log2(상자폭_i / FD 스텝_i)⌉, 1), `E/search/slsqp_outer.py:179-181`) 안에 수렴하지 못하면 그 시작점에서만 보상 단 θ를 GB5 규칙값(gm_req = DEC-92 MNA 1-D 근, §3.5)으로 고정해 한 번 다시 푼다. 폴백 사실과 이유(`compensation_fixed_fallback{start, reason: slsqp_maxiter}`)를 기록하고 그 점을 '추정'으로 표시한다. 벽시계·U-47 예산에 의존하지 않는다(결정론). 9회로 실행에서 폴백 빈도를 재서 보고한다. 기록은 결과 JSON front 점의 `fallbacks[]`와 `perf.compensation_fixed_fallback` 계수 |
| 복합 블록 묶음 크기 상한(DEC-81) | 묶음 크기 상한을 계수 예산 N_S(`structure_count_budget`, 41 §0)로 둔다. 근거는 L-10과 같다(실행 시간에 의존하지 않아 결정론). **결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로")(U-65, 계획 DEC-81 정정) |
| T1·T7·T8 형식(P N6.2) | T1: 소자 행 `{W, L, finger_w, n_fingers, ID, VGS, VDS, VSB, gm_id, ID_source}`(오라클 넷리스트 `w = finger_w`, `m = n_fingers`), 노드전압 전부, 이상원·수동소자 값, metric, front 표, 실패 레코드, exit code. T7: SPICE를 돌리는 front 점 = U-45 기본안(양 끝점 + 예산 점)이고 넷리스트 기하는 그 점의 MOD8 수렴 기하(LY8). T8: 위 3열 |
| 바이어스 소자 gds 귀속과 '층 0 AC 무동작'(P DEC-71 (2)) | 바이어스 기둥 소자의 gds가 다른 블록의 국소 AC 이득에 들어가면 그 소자는 기여받는 블록의 국소 문제에 고정 입력으로 들어가고 공유 소자로 표시되며 확정은 조립에서 한다. 어느 블록에도 gds로 기여하지 않는 순수 기준전압 소자만 AC 제약 없이 풀고, 하한은 포화 여유·매칭 선언·DC 등식이다. 그 하한마저 없으면 결과 JSON `layer0.ac_inactive[{column, devices, reason}]`로 보고한다(조용히 자명해를 내지 않는다). 블록에도 바이어스 기둥에도 들지 않는 소자는 `column_unassigned`로 정지한다(as-built `stage_a`) |
| N3.13 bisection 켜기 경로 | 기본 비활성. spec `optional_stages`(DEC-75)에 bisection 대상 제약 metric 목록을 선언하면 켜진다. 진입점은 `achievable_metric_bound(mode="bisect")`이고 `run_gmid_design_pipeline` 위의 도구가 부른다(MOD10, 패키지 순서상 pipeline 위). 결과는 선언의 `value`와 `_derived{지문, 스텝 이력, 시각}`으로 기록한다. 42 DEC-22 행은 N/A가 아니라 MISS(기본 비활성, 켜기 경로 설계됨)다. 키는 `optional_stages.bisection.metrics: [...]`다(DEC-68 명명, §3.10.9 PN4 결정) |
| TS7 xfail 규칙(P N3.11) | 계약 test는 처음부터 `xfail(reason="<담당 단위 id>", strict=True)`로 둔다. 담당 단위가 완료되면 그 단위 변경에서 xfail 표시를 지운다. strict이므로 단위 완료 전에 통과하면(XPASS) FAIL이 나서 활성화를 강제한다 |

#### 3.10.9 정한 기본값 (design 소관, 열린 질문 없음 -- P N9.2-8)

아래 1~4와 마일스톤 범위 밖(PN5)은 사용자가 그대로 결정했다(사용자 결정 2026-10-12 "4절도 권고대로", PN1~PN5).

design이 정할 수 있는 것은 아래처럼 정했다. 사용자 결정이 필요한 것은 계획 N7.2 U-60~U-70으로 올렸다(§3.10.11).

1. **P-10 finger 피치 여유**: §3.10.5. 2026-10-08 ratify된 PDK 레이아웃 규칙 식을 쓰고 새 규칙은 만들지 않는다.
2. **P-12 `library_*` 합계**: 실행 하나의 결과 JSON은 **자기 회로의 발동만** 적는다(`views[].activated`, `cells`, `out_of_forward_cells`). 9회로 합계 `library_activated_circuits`·`library_verified_circuits`는 결과 JSON 필드가 아니다. U16 integration test(`test_all_library_topologies_run`, IC7)가 9회로 결과 JSON을 모아 test 보고에 낸다. 저장되는 coverage 파일은 없다(R7). 정지 판정(검증 발동 0 분기)에 쓰는 '검증 발동' 여부는 분기 목록의 속성이다(`kind`와 같은 자리, 코드 상수가 아니라 graph 규칙 등록부의 분기 레코드에 `verified_circuits` 목록으로 두고, U16 test가 9회로 실행과 대조한다).
3. **P-13 tol_V 양끝 격자점**: leave-one-out이 정의되지 않는 양끝 격자점의 셀 값은 **같은 bin 안에서 이웃한 내부 격자점의 leave-one-out 값**이다. 외삽하지 않는다(DF-27: 축 밖 입력은 실패 레코드). 이웃 내부점이 없는 축(점 2개)은 L 축과 같은 규칙으로 검증 전용 중점을 쓴다(P N3.6).
4. **P-13 bisection 켜기 키**: spec `optional_stages.bisection.metrics: [<metric 이름>, ...]`(DEC-68 이름 규칙, DEC-75). 목록에 든 제약 metric만 N3.13 절차를 탄다.

#### 3.10.10 실측으로 정하는 계획 항목의 측정 설계 (U-23·U-33)

계획이 '실측 후 결정'으로 둔 두 항목의 측정 방법이다. 판정 기준은 계획 문언 그대로이고, design은 실행 방법만 정한다.

| 항목 | 측정 도구 | 비교군 | 기록 | 판정(계획 문언) |
|---|---|---|---|---|
| U-33 층 0을 기본 경로로 | `tools/compare_paths.py`(pipeline 위 도구, MOD10). 같은 spec·탐색 인자로 회로마다 실행 | (i) 콜드 스타트(층 0 끔, 선언 x0. v1.10: 'S3 시작점'은 대상 소멸) (ii) 층 0 조립점 출발 (iii) 정밀 경로는 U-66 (가): 미구현 정지라 측정 대상이 아니다 | 평가 수(층 0 몫 포함), front 점 대조(두 축), 제약마다 활성/비활성·여유(§3.10.6), wall-clock, 국소 대 전역 차(ΔVGS, Δ노드전압, Δgm_id, 블록 gain 차) | 층 0이 평가 수를 줄이면서 목적값·활성 제약 여유가 max(격자 분해능, 모델 오차) 안에서 같거나 나으면 기본 경로 |
| U-23 입력-캐스코드 L 동일 강제 | 같은 도구, L 묶음 선언만 바꿔 실행 | (A) 독립 L (B) 동일 강제 (C) A + LR5 격자 확장 (D) A + VDS 균등 고정 | 평가 수, 목적값, 제약 여유, 레이아웃(행 안 L 종류 수, finger 배정 성공, finger 합·box 비, 파일럿만), tail 포화 여유, `parasitic_pm_ss_deg`, 미러 전류비 오차 | 계획 U-23 문언(B가 finger 배정 실패면 기각 등) |

- 두 측정 모두 결과를 파일에 회로마다 이어 쓴다(중간 종료에도 남는다). 판정은 사용자 결정 기록으로 닫는다.
- U-14(공유 VGS 후보 gain 차 ≤ 분해능이면 전력 작은 쪽), U-45(SPICE front 점 = 양 끝점 + 예산 점), U-32(단위 접미사는 사람이 선언하는 spec 값에만)는 **결정**(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로")이다. U-51은 **결정**(사용자 결정 2026-10-12 "U-51은 (나)로"): 보상 단 gm/ID는 θ에 포함하고, 외층 SLSQP가 반복 상한 안에 수렴하지 못한 시작점에서만 보상 단을 GB5 규칙값으로 고정해 다시 푼다(계수 기반, '추정' 표시, §3.6 외층).

#### 3.10.11 사용자 결정으로 올린 항목 (계획 N7.2 U-60~U-70)

design이 정하면 안 되는 것(범위·회로 해석·판정 기준 변경)은 계획 N7.2에 행을 더하고, 그 항목에 걸린 구현 단계의 착수 조건으로 둔다(N9.2-8). 결정된 행은 결정 원문을 적는다.

| U | 내용 | 상태와 내용 | 구현 단위 |
|---|---|---|---|
| U-60 | LUT memo 상한과 퇴출 판정(§2.4.6) | **결정**(사용자 결정 2026-10-12 "U-60은 (가)로"): (가) 퇴출 허용·퇴출 수 보고, `recomputes_after_eviction` = 0 판정, 상한 N_T 무관. U17 ③ 착수 조건 해소 | -- |
| U-61 | d/s 맞바꿈의 종류가 다른 소자 전류 묶음 상자(§6-8, D-1) | **결정**(사용자 결정 2026-10-12 "5절 권고대로"): 구성원 상자의 교집합, 비면 거부. 같은 궤도 안 불일치는 지금처럼 거부 | U2·U11(`search_domain`) |
| U-62 | d/s 맞바꿈과 DEC-97(§6-8, D-3) | **결정**(사용자 결정 2026-10-12 "5절 권고대로"): DEC-97 (3) '방향 없음'을 MOS d/s로 넓힘, 위치·`wl`·생성자 모두 그래프 하나(D-2), d/s 뒤집은 입력은 대칭 결과(궤도·정준 위치·`dc_colour`, 전류 부호는 표기 기준 방향 변환 뒤)만 비트 동일하고 사이징 결과는 선언 방향을 따른다(범위 (라), 사용자 결정 2026-10-13 "1은 권고", 틀린 선언은 봉인 7 거부), 9회로 `dc_colour` 순서 변화는 test 기대값 재생성 | U2 |
| U-63 | 층 0 정지 범위(41 PQ2, §5.3.11) | **결정**(사용자 결정 2026-10-12 "U-63은 (가)로", U-63): 정지는 경로 열거 예산 초과와 후보 격자 Π > N_S 둘뿐. N_T,i는 평가 상한(`layer0_candidates_truncated` 기록 + 블록 front '추정'). 현재 library 정지 0 | U15 |
| U-64 | 층 0 정의역 상한 A^L0의 쓰임(41 L-14) | **결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"): 층 0 전용(첫 배분 제외, bin 위 끝 보조). exit 3·41 §6.4-1은 축소 전 표 | U9 A9·U15 |
| U-65 | 복합 블록 묶음 크기 상한(DEC-81) = N_S | **결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로"): 계수 예산 N_S | U1 복합 블록 |
| U-66 | 정밀 경로 선언 시 정지(DEC-73·76) | **결정**(사용자 결정 2026-10-12 "U-66은 (가)로"): `unsupported_rule_branch` 정지, 조용한 폴백 없음. 정밀 경로 design은 U-33 측정이 기본 경로 부족을 보일 때만 | U11 |
| U-67 | LOD·WPE·PSE와 L 혼합 interdigitation 대칭 검사(I-A13) | **결정**(사용자 결정 2026-10-12 "U-67은 (나)로"): L 혼합 행 대칭 검사 구현, LOD는 오라클 sa/sb/sd로만, WPE·PSE 제외 | U12(대칭), U16·U6(LOD 오라클 입력) |
| U-68 | 키가 다른 옛 S0 수준 스냅샷 파일 정리(§2.4.3, GQ2) | **대상 소멸**(v1.10, 사용자 결정 2026-10-15 "나로 해": S0 스냅샷 파일이 없다). 옛 결정(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로")은 계획 U 표·history에 남는다 | 정리 코드 삭제(§2.4.3 목록) |
| U-69 | 봉인 9 전도 하한의 연속 제약화(§3.10.4)와 계획 DEC-88 정정 | **결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로"): 동작점별 연속 부등식 제약, 계획 DEC-88에 봉인 9 명시(정정함) | U17 ③·U11 제약 행 |
| U-70 | 반쪽 귀환이 비대칭인 차동 출력의 잡음 N_in 계수(41 §7.5, K-2 재확인) | **결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로"): N_in 구조 유도, 대칭 귀환(Cf1 = Cf2) 식, 비대칭 회로는 '추정' | U8·U13 잡음 출발 경계 |

---

## 4. SPICE 오라클 (`tools/spice_oracle/`)

**역할**: 엔진을 import하지 않는 독립 판정 장치다(P N3.8). 합격 조건은 free 모드에서 (i) 선언 성능 제약 만족 (ii) ID > 0인 모든 MOS 포화 (iii) 엔진이 전도로 예측한 MOS가 꺼지지 않음(`off_current_A`)이다. forced 모드는 진단 전용이다. 이 부분은 as-built OK다(README C22~C24).

**C10 폐루프 과도 판정**(`docs/03-analysis/oracle-c10-early-termination.contract.md`, `[ng-oracle-early]` d56ba66 개정본 위에 아래 규칙을 더한다):

1. **d56ba66에서 그대로 쓰는 것**. 아래 L번호는 개정 계약 파일 기준이다.
   - f_crit 대역: L14-15
   - n_pp, tmax: L25, L28
   - 분해능을 아는 창 판정 g: L37
   - 조기 unstable(엄격 증가): L40
   - 연장 실행 상한 n: L71-72
   - `wall_s_per_window` 유도: L75-78
   - 시간 초과·치명 오류 = `failed`: L79-81
2. **지속 진동은 불안정(한계 사이클)이다**(사용자 결정 2026-10-08 4번). 창 진폭 M_j가 아래를 모두 만족하면 `unstable`(사유 `limit_cycle`)이다.
   - 바닥보다 분해능 넘게 크다: M_j·(1 − reltol) > floor'.
   - 연속 창의 변화가 분해능 안이다: |M_j − M_{j−1}| ≤ (M_j + M_{j−1})·reltol + floor'.
   - g↓(감소)가 아니다.

   j ≥ 3인 창에서 이 조건이 j−1, j에 연속으로 성립하면 조기 종결한다. 창 수 3은 L40과 같은 정의이므로 새 상수가 아니다.
   - **안정 fixture 불변 조건**(계약 L63-64를 이어받음): 구현 커밋에서 기존 안정 판정 회로·fixture 전체(`stable`, `decaying`→`stable`)를 돌려, 이 한계 사이클 조건이 한 번도 성립하지 않았음을 확인하고 기록한다. 하나라도 성립하면 규칙 설계를 되돌린다.
   - **고Q 안정 회로의 표시**: 창 하나당 감쇠가 분해능보다 작으면, 고Q로 천천히 감쇠하는 안정 회로를 K 창 안에서 한계 사이클과 구별할 수 없다. 이 경우 판정은 보수적으로 `unstable(limit_cycle)` → FAIL이다. 대신 보고 맨 앞에 `limit_cycle_vs_slow_decay_unresolved{M_1..M_K, 창당 변화비}`를 둔다. 사용자가 이 FAIL이 판정 한계에서 나왔다는 것을 알아볼 수 있게 하기 위해서다.
3. 2번은 d56ba66의 다음 두 곳을 대체한다.
   - L48-52 '그 밖(분해능 안의 같음 포함) → undetermined'
   - L42-44·L52-54 '일정 진폭 지속 진동은 undetermined 유지(사용자 승인)'

   2026-10-08 사용자 결정이 이 문구보다 나중이다. `tools/spice_oracle/tests/test_oracle_c10_stability.py:710`의 `test_sustained_oscillation_undetermined_incomplete` 기대값도 바뀐다. 기대값은 test 작성 주체가 고친다.
4. 폐루프 과도에서 `unstable`(limit_cycle 포함)이 나오면 FAIL이다(사용자 결정 B).
5. **개루프 RHP 극점 처리**(조정자 정정, R19 / §9 Q10):
   - 개루프 RHP 극점이 있어도 폐루프는 안정할 수 있다(조건부 안정). 그래서 오라클은 개루프 RHP 극점만으로 FAIL을 내지 않는다.
   - 엔진의 결정 A('RHP 극점 → 위반 행')는 **탐색용 보수 규칙**이다. 엔진이 위반으로 본 점을 오라클이 합격으로 볼 수 있고, 그 차이는 T8 모델 오차와 함께 기록한다.
   - 이 처리는 결정 A의 문구('불안정(실패)')를 오라클 쪽에서 완화한다. 그래서 별도 질문으로 둔다(§9 Q10).
6. **Nyquist 판정 정의**(N2). 오라클은 엔진과 독립이며 엔진 값을 쓰지 않는다.
   - **P(개루프 RHP 극점 수)**: 오라클이 직접 구한다. 끊은 개루프 테스트벤치(같은 루프 절단)에서 선언된 시뮬레이터 어댑터의 pz 능력(첫 사례 ngspice `.pz`)으로 극점을 구해 실수부 > 0인 극점을 센다(능력이 없거나 독립 증거로 확인되지 않으면 P = 미정, oracle-portability design §8.5). 0 근처 극점은 분해능 밖으로 실수부가 양수인 것만 센다. 분해능 기준은 `.pz` 결과의 상대 정밀도(reltol)다.
   - **N(−1 둘레 감김 수)**: 같은 개루프 `.ac` 표본 L(jω)에서 1 + L의 위상을 펼쳐(unwrap) 센다. N = −Δ_{ω:0→∞} arg(1+L)/π이고, 음의 주파수 대칭을 쓴다.
   - **주파수 범위**: 하단은 |L|이 평탄해진 저주파(첫 표본에서 위상 기울기가 0으로 수렴), 상단은 |L| < 1이고 단조 감소하는 구간까지다.
   - **표본 조건**: 인접 표본 사이 arg(1+L) 변화가 π/2 이하여야 한다. 넘는 곳은 그 구간을 이분해 다시 `.ac`한다(상한 K_max). 그래도 넘으면 N은 '미정'이다.
   - **Z = N + P**. Z ≥ 1이면 불안정 FAIL, Z = 0이면 안정이다.
7. **최종 판정과 이행 순서**:
   - Z와 폐루프 과도를 함께 본다. Z ≥ 1 또는 과도 `unstable`이면 FAIL이다. Z = 0이고 과도가 stable/decaying이면 안정이다. 둘 다 결론을 못 내면 INCOMPLETE다.
   - **6이 구현되기 전에는 폐루프 과도만 쓴다.** 이때 Z는 '미정'으로 보고하고, 개루프 RHP만으로는 FAIL·INCOMPLETE를 정하지 않는다.
8. **U6 판정 규칙 보완**(사용자 결정 2026-10-09 "3개 모두 네의견대로 해", U6 구현 보고 반영):
   - **한계 사이클 = 감쇠하지 않음**: 2번의 '분해능 안에서 일정'을 대체한다. j ≥ 3에서 최근 두 창의 진폭 M_j가 앞 창보다 분해능 이상 줄지 않으면 지속 진동 `unstable(limit_cycle)`이다. 진폭이 출렁이는 지속 진동(rb1e6형)도 포함한다. 창마다 분해능 이상 계속 줄면 slow decay로 판정을 이어 간다.
   - **`.pz` 신뢰 규칙**: 큰 BSIM4 회로에서 `.pz`가 경고 없이 거짓 RHP 극점을 낸다(파일럿 23개, 개루프 `.tran`에 증가 없음). 그래서 폐루프 과도가 stable이면 `.pz`를 쓰지 않는다(Z = 0, P = −N). 과도 unstable이면 FAIL. 과도 미정이면 N ≥ 1 → FAIL, N = 0이면 **개루프 과도가 증가를 확인할 때만** `.pz` P를 쓰고 아니면 INCOMPLETE다. 과도 stable인데 `.pz`가 −N과 다르면 `pz_conflict`를 기록한다.
   - **자극 위치**: 폐루프 과도의 자극과 관측은 루프 끊는 점에 둔다. 그 루프의 폐루프 극점은 끊는 점에서 들뜨고 관측되므로, '자극이 모드를 못 들뜨게 해서 안정으로 남는' 위험을 그 루프 뷰 범위에서 닫는다. 남는 한계는 보고서에 적는다.
   - **조건부 안정**: Z = 0이고 과도 stable이면 `pm_valid`를 유지한다. PM은 모든 |T| = 1 교차의 최솟값이다. P ≥ 1이거나, 교차 주파수 아래 |T| > 1 구간에서 위상이 −180°를 넘으면 `conditionally_stable`을 표시하고 **하측 이득 여유**(루프 이득이 몇 dB 줄면 감김 수가 바뀌는지, 같은 `.ac`에서 읽음)를 보고한다. spec 값이 없으므로 제약이 아니라 보고다.
   - **U6 test 후속 정의**(2026-10-09 오케스트레이터): (i) 창 판정의 floor는 **관측 노드(루프 끊는 점)** 기준 reltol·|V_op| + vntol이다. (ii) 오라클 ICMR 좌표는 창 끝에서의 **실제 입력 공통모드 (V_inp + V_inn)/2**다(엔진 `icmr_v`와 같은 정의). (iii) 차동 입력이 없는 회로의 ICMR은 `unavailable`이다. (iv) 하측 이득 여유 필드 이름은 `low_side_gain_margin_db`. (v) `noise_excess_th`의 입력 셀 소자 이름은 오라클 넷리스트 이름으로 사상해 찾는다(수동소자 접두 포함). 선언된 이름 중 하나라도 못 찾으면(`input_cell_missing` 비어 있지 않음) 찾은 부분집합으로 계산하지 않고 `noise_excess_th`는 None + `excess_reason`(누락 이름)이며, 이 metric의 제약은 PASS가 아니라 INCOMPLETE/N/A다(fail-closed).

| 항목 | 상태 | 증거 |
|---|---|---|
| free/forced, 포화, off_current, CMRR/PSRR, 접합 기하 | OK | `tools/spice_oracle/README.md:60-69,114-117,146-147,300-318` |
| C10 조기 종결 계약 | PART(계약만 있고 master 미반영) | `[ng-oracle-early]` 계약 L14-81 |
| 지속 진동 = unstable | DEV: 계약과 test가 undetermined로 고정되어 있다 | 계약 L42-54, `tools/spice_oracle/tests/test_oracle_c10_stability.py:710` |
| 개루프 RHP: Nyquist Z + 과도로 판정, 결정 불가일 때만 INCOMPLETE | DEV: `pm_undefined`이면 무조건 N/A→INCOMPLETE | `[ng-cmfb-pm]` README '판정', `tools/spice_oracle/README.md:516` |
| `.pz` P 계수, N 위상 펼침 | MISS | `grep -n "\.pz" tools/spice_oracle` 0 |
| 잡음 `.noise` 대조 | MISS | 41 §7.6 |
| `pm_cm_ss_deg` 측정 | OK `[ng-cmfb-pm]`. `[ng-bridge]` `ORACLE_MEASURES`에는 없다 | -- |


**LOD 입력**(사용자 결정 2026-10-12 "U-67은 (나)로", U-67): 오라클 넷리스트의 MOS 인스턴스는 MOD8 수렴 레이아웃의 `ly.lod`에서 finger별 `sa`·`sb`·`sd`를 받는다(sky130 subckt 인자, 모델의 `lod.spice`·`saref`/`sbref`. 값이 0이면 응력 모델이 꺼진 기본 동작이다). finger별 값이 다르면 finger마다 인스턴스를 나눈다(`m`으로 묶지 않는다). 엔진 예측(LOD 없음)과 오라클 측정의 차는 metric별 `model_error_<metric>`(DEC-72)로 기록되어 제약 여유에 들어간다. 출처는 `ly.lod` 하나이고 오라클이 기하를 따로 계산하지 않는다(DEC-91과 같은 원칙). 담당: U16(엔진 → 오라클 입력), U6(넷리스트 인자).

---

## 5. 공통 모드(CMFB) 루프

사용자 결정(2026-10-08, CM 일반화·구동/소비 분류·결정 A·보완)을 그대로 설계로 둔다. 구현은 `[ng-cmfb-pm]`에 있다.

1. **루프 정의**: 차동 출력 포트쌍(role p/n)에 같은 부호(가중 ½, ½)로 Middlebrook 주입해 T_cm을 잰다. 평균 회로의 형태는 따지지 않는다. 오라클도 같은 정의를 쓴다.
2. **절단 분류**: 출력에 채널이 붙은 MOS마다 반대쪽 단자에서 채널·R·C를 따라간다. 이때 두 출력 넷은 통과하지 않는다.
   - 레일에 닿으면 구동(x)이다. 이상 전류원 단자는 레일로 본다.
   - 감지 넷·gate·다른 출력에서 끝나면 소비(n)다.
   - 판단이 애매하면 명시적으로 정지(`cm_partition_ambiguous`)하고 spec `cm_sense_elements` 선언(`user_spec`)을 요구한다.
3. **판정 규칙**:
   - `pm_cm_ss_deg` 제약은 spec에 선언된 회로에만 건다.
   - CM 루프에서 PM이 정의되지 않으면(T_cm(0) ≤ 1, 또는 0 dB 교차 없음) 위반이다(결정 A).
   - 개루프 RHP 극점이 있으면 위반이다.
   - 제약이 선언되지 않았어도 차동 포트쌍이 있으면 T_cm을 늘 계산해 보고한다. 이때 T_cm(0) > 1이면 경고 `cm_loop_unconstrained`를 낸다.
4. **위반 판정과 척도는 별개다**(M1).
   - **판정**: 결정 A에 해당하면 그 행은 **늘 위반**이다(부호가 위반). 이 판정은 척도에 의존하지 않는다.
   - **크기**: 판정 단위 크기는 c = 20·log10|T_cm(0)|/s다. 이 값은 ≤ 0이다. s는 그 metric의 분해능(`MetricResult.resolution`)이다.
   - **분해능이 없을 때**: as-built는 s = 1 dB로 대체하는데, 이것은 근거 없는 상수라 지운다(EP-4). 대신 행은 위반으로 유지하고, 풀이 단위 크기만 §7.2 규칙으로 정한다(s_k = max(|c 원값|, ...)). 그리고 front에 '분해능 미측정'을 표시한다.
   - RHP 극점 행(c = −max Re/|p|)도 같은 방식으로 다룬다.
5. **스위치드 커패시터 CMFB**는 `unsupported`로 명시 정지한다.

| 항목 | 상태 |
|---|---|
| 1·2·3·5 | OK `[ng-cmfb-pm]`(미병합) |
| 4 분해능 없을 때 1 dB 대체 | DEV(상수) |
| metrics CONTRACT 7.11의 '`cm_output_loop` boolean' 문구 | DEV(문서가 README·S-33과 모순) |
| 계획서 N3.16 view_kind에 `cm_loop` 없음 | 계획서 문구 갱신 필요 |

---

## 6. 대칭 -- 정준 라벨링과 자기동형 궤도 θ 묶기

사용자 결정(2026-10-08 "정준 라벨링 + 대칭 변수 묶음, 기본값 묶음")을 설계로 둔다.

1. **완전 정준 라벨링**(신규 `E/graph/canonical_form.py`): S1을 색 그래프로 본다. 꼭짓점 = 소자·넷, 색 = kind, 단자 종류, 레일 여부, 포트 role.
   - 1-WL 색 정제(as-built `E/sizing/struct_colour.py`)에서 출발한다.
   - 색 칸이 이산이 아니면 개별화와 정제를 반복하는 탐색 트리로 정준형을 정한다(nauty 방식). 탐색 트리의 가지 순서는 색 칸의 정준 순서다.
   - 이름을 쓰지 않는다. 결과는 정준 순서와 자기동형 생성자다.
2. **궤도**(신규 `E/graph/automorphism_orbits.py`): 생성자들로 소자 궤도를 만든다. 레일과 포트 role은 고정한다. 차동 포트 p/n은 서로 바뀔 수 있다.
3. **θ 묶기**(`E/sizing/theta_schema.py`): 같은 궤도의 소자는 θ 성분을 하나 공유한다. 대상은 ln IDu, L 동치류 L, 보상 수동소자 값이다. 전류 기저 성분은 궤도에 대해 대칭인 것끼리 묶는다. 이것이 기본값이다.
   - **전류 기저 열 순서 규칙**(사용자 결정 2026-10-12 "3번 권고대로", (가)): 결정 취지 = "대칭 궤도 원소를 자유 열로 먼저 남긴다"(위 '대칭인 것끼리 묶는다'의 규칙화). 자유 열 선택에서 비자명 궤도 원소를 우선한다. 행사다리꼴은 앞 열부터 pivot(종속)으로 잡으므로, **열 정렬 키에서는 비자명 궤도 원소를 뒤로** 둔다: 열 정렬 키 = (그 원소의 궤도가 비자명인가 -- 비자명이 뒤, `dc_colour`, 이름). (결정 원문의 키 표기 '비자명 먼저'는 자유 열 선택 순서를 뜻한다. 열 정렬에서 앞에 두면 비자명 원소가 pivot이 되어 파일럿이 27/40으로 나빠진다 -- ①-d 실측.) `current_basis`는 `graph/s1: orbits`(§2.4.8)를 읽는다. 측정 의무: (묶음 수, 탐색 θ 변수 수) = (`len(SearchDomain.ties)` -- 전류·L·ln IDu·수동소자 값 묶음 전체, `len(SearchDomain.variables)`). 그중 전류 묶음 수(대표가 θ 전류 성분인 묶음)는 함께 기록한다. 기준선 = master `8e46548` as-built 값(파일럿 29/38, 그중 전류 묶음 7. 나머지 8회로 각 회로 값)과 같아야 한다. ①-d 실측: 규칙 적용 뒤 파일럿 29/38·전류 묶음 7, 나머지 8회로 base와 같음. "D-3 반영 뒤·열 순서 규칙 전" 측정값(파일럿 28/39, 전류 묶음 6)은 기록만 한다. 파일럿 전류 묶음 구성: M1a~M1b 유지, M4a~M4b 대신 M19~M10.
4. **해제**: spec `search.untie_orbits: {원소: {source}}`(as-built 정본, 옛 이름 `symmetry_untie`)에 적힌 소자는 궤도에서 빼고 따로 변수를 둔다. 의도적 비대칭 사이징에 쓴다.
5. **불변식**:
   - **궤도와 matching 사이에는 포함 관계를 불변식으로 두지 않는다**(H1·N8, `[ng-layer0-canon]` 실측). 어느 쪽도 일반적으로 다른 쪽을 포함하지 않는다.
     - 비율 미러는 궤도가 아니다.
     - 반회로 대응은 궤도지만 matching 그룹 하나에 들어가지 않는다. 실측 예: 파일럿 M11a/M20a(class-AB KVL 루프 멤버), M37a/M37b(CMFB 쌍).
     - 대신 대조 표 `orbit_matching_crosstab`을 보고한다. MOS 궤도마다 그 궤도가 걸친 matching 레코드, 그리고 matching 레코드마다 그 레코드가 걸친 궤도를 적는다. 수동소자 궤도(Cc1/Cc2, Rz1/Rz2, R1/R2, CL1/CL2 등)는 matching 대상이 아니므로 표에서 뺀다.
     - `review_needed`로 올리는 것은 하나뿐이다(사용자 결정 2026-10-12 "나'로 진행해", (나')). `diff_pair` 레코드의 두 멤버가 다른 궤도이고, (a) 회로의 출력 포트(topology `ports`)가 차동 쌍(`differential_output_p/n`)이며 (b) 그 `diff_pair`의 두 gate가 회로의 차동 입력 포트 p/n일 때만이다. 기록 코드는 `diff_pair_orbit_split`이다(`orbit_matching_crosstab`의 `findings`, 단계 A 보고서 review 목록). 이 경우만 대칭 차동쌍의 정의와 직접 모순된다. 그 밖의 `diff_pair` 궤도 불일치는 `orbit_matching_crosstab`에 기록만 한다.
     - 9 library 회로 기대: review 0. 파일럿 M1a/M1b는 같은 궤도라 통과, M37a/M37b는 gate가 Voc/Voc_des라 대상 아님(CMFB 단일 출력 오차증폭기), 단일 출력 7회로는 (a)에 걸리지 않는다. 실제로 거부하는지는 파일럿에서 넷 하나를 비대칭으로 바꾼 합성 회로로 확인한다(§10.2).
   - 이름을 전단사로 바꾼 입력은 비트 단위로 같은 결과(front 정규화 해시)를 낸다.
   - 1-WL 결과와 정준형이 다른 회로는 그 목록을 보고한다.

| 항목 | 상태 | 증거 |
|---|---|---|
| 1-WL 색 정제 | OK(순서 tie-break 용도) | `E/sizing/struct_colour.py:1-15` |
| 완전 정준 라벨링(nauty 방식), `dc_orbit`, 꼭짓점마다 다른 `dc_colour` | PART `[ng-layer0-canon]` 49283c6(미병합) | `E/sizing/struct_canon.py` |
| 궤도 θ 묶기, 해제 | PART `[ng-layer0-canon]` | `E/search/orbit_ties.py`, `tie_expand.py`, `SearchDomain.ties`, spec `human.search.untie_orbits` |
| 이름 바꿈에도 비트 동일(정준 행·합·행렬 순서) | PART `[ng-layer0-canon]` | 실측: 8회로 + 합성 3개, 층 0 기준 |
| 9 library 회로에서 묶기 활성 | DEV: **9회로 모두에서 비활성**이다. 수동소자를 방향 있는 것으로 다루기 때문이며, 아래 7의 확정 규칙으로 고친다 | -- |
| 위치 | DEV: 설계의 `E/graph/canonical_form.py`·`automorphism_orbits.py` 대신 `sizing`·`search`에 있다. 다음 변경에서 정준형·궤도는 S1 구조 사실이므로 `graph`(MOD3)로 옮긴다(EP-3, 개념당 파일 하나) | -- |

6. **실측 회귀 기록**: canonical 시작점 변경 뒤 folded_cascode와 two_stage_ota가 하나뿐이던 front 점을 잃었다. 원인은 시작점 운이다. 대응은 41 §5(층 0 gain 예산 조합점)와 41 §6(스펙 기반 출발 구간)으로 시작점을 여러 개, 근거 있게 만드는 것이다. 이 두 회로를 회귀 추적 대상으로 `tests/integration`에 둔다.
7. **2단자 수동소자는 방향 없이 다룬다**(사용자 결정 2026-10-08 "대칭 묶음 방식: b", 확정 규칙):
   - **배경**: as-built 브랜치 실측에서 묶기가 9회로 모두 비활성이었다. 원인은 DC 전류가 흐르는 저항을 방향 있는 것으로 보아 방향 보존 자기동형만 허용한 데 있다. 파일럿 R1/R2는 단자 순서가 반대로 그려져 있어 거울 대칭이 잡히지 않았다.
   - **라벨링**: 정준 라벨링에서 R·C 같은 2단자 수동소자는 무향 엣지다. 단자 순서는 색에 넣지 않는다.
   - **묶기**: 궤도를 묶을 때 θ 값(R, C 값)은 같게 둔다. 예: R1 = R2.
   - **전류 변수**: 그 수동소자를 지나는 가지 전류 변수는, 자기동형이 단자 순서를 뒤집으면 부호 −1로 묶는다(I_R2 = −I_R1). 뒤집지 않으면 +1로 묶는다.
   - **topology**: library topology의 단자 순서는 바꾸지 않는다(WP-07).
   - **확인**: 이름을 전단사로 바꾸거나 수동소자 단자 순서를 바꾼 입력에서 궤도와 front 정규화 해시가 같은지 metamorphic test로 본다. 파일럿에서 R1/R2 궤도가 잡히는지도 test한다.
8. **MOS drain/source 맞바꿈**(사용자 결정 2026-10-12 "6. 가", 대칭 탐색 그래프 하나 = 사용자 결정 2026-10-12 "1~4까지 새로고친 네 제안대로 해" 1절 D-2, D-1·D-3 = 사용자 결정 2026-10-12 "5절 권고대로" -- **결정됨**):
   - **규칙**: MOS는 d/s에 대해 물리적으로 대칭이다. 자기동형은 한 MOS의 drain을 상 MOS의 source로 보낼 수 있다(자기 자신으로 가며 d/s를 맞바꾸는 것 포함). 계획 DEC-97 (3)의 '방향 없는 원소'를 2단자 수동소자에서 MOS d/s까지 넓힌 것이다(D-3).
   - **그래프 하나**(D-2): 정준 위치 `position`, 1-WL 색 `wl`, 자기동형 생성자를 **모두 같은 그래프 하나**에서 정한다. 그 그래프에서 MOS의 `d`·`s` 엣지는 같은 라벨 `c`(채널)다. `g`·`b` 라벨, 원소 처음 색(kind, is_diode, 선언 표시 `_declaration_marks`), 노드 색(레일, 포트 role, 선언 표시)은 그대로다. 그래서 맞바꿈은 gate·bulk 넷과 모든 선언이 보존될 때만 생긴다. 두 번 탐색하지 않는다. 이 그래프는 **대칭 결과**(궤도·정준 위치·`wl`·`dc_colour`·전류 부호)만 정한다. 사이징은 topology의 선언 d/s 방향을 그대로 쓴다(아래 비트 동일 범위, D-3).
   - **불변식 유지**: 한 그래프에서 정하므로 "개별화·정제 뒤 남는 동률 = 정확히 자기동형 궤도"와 graph CONTRACT 4.7 (h) "궤도 ⊆ `wl` 클래스"가 맞바꿈 궤도에서도 성립한다. 궤도 id(구성원 정준 위치 최솟값)와 대표(구조 색 최소)는 이름에 불변이다.
   - **비트 동일 범위**(DEC-97 (4), D-3, 범위 (라) = 사용자 결정 2026-10-13 "1은 권고"): topology의 d/s 표기는 **물리 방향 선언**이다(사용자만 수정하는 정본, 엔진은 고치지 않는다). 이름 전단사·수동소자 단자 순서 변경은 지금처럼 비트 동일 결과(궤도, 정준 위치, `dc_colour`, front 정규화 해시)를 낸다. **MOS d/s 표기 맞바꿈**에 대해서는 **대칭 결과**(궤도, 정준 위치, `dc_colour`)가 비트 동일이고, 전류 부호는 표기 기준 방향 변환(뒤집은 소자 f = −1을 원소·상에 곱함)을 적용하면 동일하다. **사이징 결과**(writer 계획, θ 스키마, ties, front)는 선언 방향을 따르므로 비트 동일 대상이 아니다. 근거: 엔진 51개 파일이 표기 source를 물리 source로 쓴다(U17 ①-d 구현 조사) -- 사이징까지 표기 무관으로 만들려면 엔진 전반을 바꿔야 하고, (라)는 엔진 변경 0이다. 틀린 선언은 봉인 7(VDS − VDsat ≥ tol)이 거부한다: 선언 VDS ≤ 0이라 창 안에 근이 없어 `no_root_in_window`(fail-closed). test: `tests/search/test_orbit_ties.py::test_ds_flip_symmetry_bit_identical`(옛 `test_ds_flip_ties_bit_identical` -- ties 비교를 빼고 대칭 결과만 비교), 봉인 7 거부는 `tests/sizing/test_block_columns.py`(d/s 반대 선언 거부, 바른 선언의 같은 동작점은 통과). **d/s 반대 선언과 입력 포트 뿌리**(v1.12.6, 사용자 결정 O-84): d/s 반대 선언이 입력 포트를 다른 G_vgs 성분으로 가르면 S0에서 `input_port_multiple_roots`로 정지한다(41 §4.7-1 4 정지 안전망, `dc_writer_plan` `StructureUnresolvedError` -- 올바른 fail-closed; 대칭 결과 비트 동일 test는 뒤집은 쪽을 S1까지만 짓는다).
   - **결과(측정 대상)**: d·s 구별이 사라지므로 9 library 회로의 정준 순서·`dc_colour` 순서가 바뀐다(궤도는 2026-10-12 측정에서 맞바꿈 자기동형이 없어 그대로다. 전류 묶음은 KCL 열 순서가 `dc_colour`를 따라 바뀌므로 '그대로'가 아니다 -- §6-3 전류 기저 열 순서 규칙으로 파일럿 (묶음 수 `len(SearchDomain.ties)`, 탐색 θ 변수 수 `len(SearchDomain.variables)`)를 master `8e46548` as-built 값 29/38(그중 전류 묶음 7)로 회복하고(전류 묶음 M1a~M1b 유지, M4a~M4b 대신 M19~M10) 나머지 8회로는 as-built 값 그대로 -- ①-d 실측 일치. 규칙 전 측정값 28/39(전류 묶음 6)는 기록만). 이 순서를 기대값으로 쓰는 test는 **독립 test 작성 주체가 기대값을 다시 만든다**(작성자 ≠ 검증자, 기준 약화 아님 -- 정준 순서 정의가 바뀐 결과).
   - **전류 부호**: 자기동형이 MOS의 drain을 상 MOS의 drain으로 보내지 않으면 그 전류 성분은 부호 −1로 묶인다(2단자 수동소자 규칙과 같다, graph `reverses_orientation`).
   - **자기 맞바꿈 = 구조적 0 전류 → 정지**(design-validator N5): 자기동형이 전도 MOS 하나를 자기 자신으로 보내며 d/s를 맞바꾸면 그 소자 전류는 `I = −I`로 구조적 0이다. 전류 0인 전도 MOS는 gm/ID·VGS 역산이 정의되지 않는다(ID > 0 전제, 봉인 7). 이 분기의 계산 규칙은 만들지 않고(DEC-76) 탐색 전에 `unsupported_rule_branch`(사유 `ds_self_swap_zero_current`, 소자·생성자 기록)로 정지한다. test: 합성 toy(U11 `pass_device` 변형 -- 대칭 두 출력 사이의 통과 MOS 하나)에서 정지와 사유를 단언한다(`tests/graph/test_s1_symmetry.py`, 원본 `graph/s1_symmetry.py`). 9 library 회로는 발동 0이다(측정 2026-10-12).
   - **종류가 다른 소자의 전류 묶음 상자**(D-1, 결정 사용자 결정 2026-10-12 "5절 권고대로"): 맞바꿈이 만든 대칭이 KCL과 함께 종류가 다른 소자의 전류를 묶을 수 있다(예: 완전 차동 직렬 가지 + 출력 사이 R1 toy -- 가지마다 nmos 입력과 pmos 부하가 출력 노드에서 만나고 두 출력 사이에 R1이 있다. 반사가 R1 단자 순서를 뒤집어 I_R1 = 0이고, KCL로 nmos 궤도 {M1, M2}와 pmos 궤도 {M3, M4}의 전류가 궤도를 넘어 묶인다. 옛 예시 'U11 `pass_device` 변형(통과 MOS Mx 포함)'은 위 자기 맞바꿈 정지(`ds_self_swap_zero_current`)에 먼저 걸려 `search_domain`에 닿지 않는다 -- U17 ①-d 통합 test 지적). 궤도를 넘는(KCL 유도) 전류 묶음의 탐색 상자 = 구성원 상자의 **교집합**이고, 비면 실패 레코드 `tied_current_box_empty`로 거부한다. 같은 궤도 안 상자 불일치는 지금처럼 `tied_orbit_bounds_differ`로 거부한다(search CONTRACT 3.24-4). `search_domain` 변경이다(승인됨).
   - **범위**: U2(`canonical_form`, `automorphism_orbits`, `current_symmetry`)와 `search_domain`(D-1 상자)이 바뀐다. 다른 모듈은 U2 결과를 그대로 소비한다. D-SYa~c·R16의 궤도·묶기·해제 규칙은 그대로다.
   - **계획 정정**: 계획 DEC-97 (1)(3)(4)를 같은 커밋에서 고쳤다(v6.5 정합 정정).

---

## 7. 면적 예산·척도화·성능

### 7.1 면적 예산(사용자 결정 11, 2026-10-08)

**규칙**:
- 회로별 spec 제약 `area_search_m2 <= 예산`을 둔다. 값은 결정 11의 표다.
- 면적 = MOS 게이트 면적 Σ W·L + 보상·내부 커패시터 면적이다.
- 커패시터 면적 = 값 / ρ_MIM이다. ρ_MIM은 `core` PDK 선언 양 `mim_cap_density_f_per_m2`를 `read_pdk_decl`로 읽은 값이고, 코드에 숫자를 적지 않는다.
  - 원본은 `C:/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice`의 `camimc`다(sha256과 행 번호를 선언에 기록).
  - 단위 환산(F/µm² → F/m²)은 선언 로더가 한다.
- spec `element_values.<el>.measurement_load: true`로 표시한 측정 부하(CL·CL1·CL2·RL)는 면적에서 뺀다. 이름이 아니라 선언으로 가른다.
- 저항 단위 면적은 선언이 없으면 `passive_area_undeclared`로 보고한다. 이 처리에는 두 결정이 걸린다(M3).
  - DEC-79: 보상·부하 수동소자가 있는 회로에서 수동소자 면적 선언이 없으면 front는 `review_needed`다.
  - 사용자 결정 11: 면적 = MOS 게이트 면적 + 커패시터 면적이고, 저항은 언급하지 않는다.
  - **결정**(Q9, 2026-10-08): 저항 면적을 포함한다.
    - **단위 면적 유도**: 폭 W_R, 시트 저항 R_□인 poly 저항의 면적은 R·W_R²/R_□ + 두 끝 접촉 머리 면적이다. 그러므로 Ω당 면적 = W_R,min²/R_□이고, 머리 면적은 저항마다 한 번 더한다.
    - **입력값**: R_□는 PDK 저항 모델 파일(`C:/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice`의 poly 저항 시트 파라미터)에서 읽는다. 최소 폭과 머리 길이는 PDK 규칙(periphery rules의 poly 저항 항목)에서 읽는다. 셋 다 `core` PDK 선언 양 `poly_res_sheet_ohm_per_sq`, `poly_res_min_w_m`, `poly_res_head_area_m2`로 두고 출처(sha256, 행·규칙 번호)를 함께 기록한다.
    - **저항 종류 선택**: PDK에 선언된 poly 저항 종류 중 Ω당 면적이 가장 작은 것을 쓴다. 고정 상수가 아니라 규칙이다.
    - **측정 부하 제외**: 측정 부하(`measurement_load`, 예: nmcnr RL)는 커패시터와 마찬가지로 면적에서 뺀다.
- 제약 행은 c = (v − A)/b_A다(판정 단위).

**S-3b 잠정 상한과 그 닫힘**:
- **잠정 상한**(L6): 예산이 없을 때 쓰는 as-built 전류 상자 상한이다. I_max는 그 kind의 모든 폭 슬라이스에서 단일 finger 기준 최대 ID다(`E/search/current_box.py:12-33`). 회로 근거가 없는 LUT 범위 값이라서 '잠정'이라 부른다.
- **닫힘**: 예산이 선언되면 I_max = IDu_max·A_budget/L_lo²로 바꾼다. 근거는 W·L = I·L²/IDu ≤ A_budget이다.

**설계가 더하는 것**:
1. **예산을 지키는 출발점**: 41 §6.4의 면적 상한(L ≤ √(A_budget·IDu/I), W ≤ A_budget/L)으로 출발 구간을 자른다. 층 0 국소 문제에도 면적 bin 상한을 예산으로 둔다.
2. **소자별 W 타당성**: 레이아웃 전에 W ≤ A_budget/L_min을 상자 제약으로 둔다. 예산이 없으면 S-3b 잠정 상한을 쓰되 보고에 '잠정'을 붙인다. W가 수 mm인 시작점은 이 제약에서 거부된다.
3. **면적 달성가능성**(GB4 확장, 41 §4.4): 인증된 면적 하한 A_lb만 정지 근거로 쓴다(C1).
   - A_lb에 넣는 전류는 선언되었거나 KCL로 고정된 전류뿐이고, 나머지는 0으로 둔다.
   - L은 LUT 최소 L, 커패시터는 θ 하한을 쓴다.
   - A_lb > 예산 + b_A이면 INFEASIBLE_TARGET(`area_budget_below_lower_bound`)으로 정지한다.
   - 출발값으로 만든 면적 추정 A_est는 보고만 하고 정지 근거로 쓰지 않는다.
4. **front를 잃은 4회로의 원인 보고**: B = 120 s 실측에서 folded·ngcc·nmcnr·pushpull은 front 0이었고, sf_pushpull·current_reuse는 시작점이 0이었다. 회로마다 다음을 결과 JSON에 쓴다.
   - (i) A_lb와 A_est를 예산과 비교한 값
   - (ii) 출발 구간 충돌 표(41 §6.6)
   - (iii) 예산 점 풀이의 위반 행
   이 정보로 '예산이 불가능' / '시작점 문제' / '탐색 문제'를 가른다. 예산 값을 고치는 것은 사용자 몫이다(§9 Q8).

| 항목 | 상태 | 증거 |
|---|---|---|
| 제약 행, MIM 밀도, 측정 부하 제외, S-3b I_max | OK `[ng-area-budget]`(미병합) | 538eeab, `E/search/area_decl.py` |
| 예산을 지키는 출발점, W 타당성, A_lb 사전 판정 | MISS | -- |
| 레이아웃 판정 축의 수동소자 면적, MOD8 재필터 | MISS | `E/layout/floorplan.py` |
| B = 120 s 결과 | front: common_gate 2, two_stage 1(최대 W 0.39 mm), two_stage_sf 1(최대 W 3.2 mm, 면적 7.3e-3 mm²). folded·ngcc·nmcnr·pushpull 0(folded·pushpull은 예산이 없을 때 예산의 약 2000배에서 front가 있었다). sf_pushpull·current_reuse는 시작점 0 | `[ng-area-budget]` 실행 보고 |

### 7.2 SLSQP 제약·목적 척도화

**문제**: 면적 행은 판정 단위 c = (v − A)/b_A가 약 1e6 규모라서 SLSQP가 status 4(제약 비호환)를 낸다. `[ng-area-budget]`은 이를 임의 양수 상수 곱으로 우회했다. 이 설계는 그 우회를 아래 규칙으로 대체한다.

**규칙**: 행 k의 **판정 단위** c_k = (경계 − 값)/b_k(b_k = 그 metric의 분해능)는 활성·동률·위반 판정과 보고에만 쓴다. **풀이 단위**는 ĉ_k = c_k · b_k / s_k이며, s_k = max(|경계_k|, |값_k(x_start)|, b_k)다. 즉 '경계에 대한 상대 여유'다. 목적은 f̂ = f / max(|f(x_start)|, b_f)이다. `ftol` = b_f / max(|f(x_start)|, b_f)로, 목적 분해능을 같은 척도로 옮긴 값이다.

s_k는 시작점마다 한 번 정하고 그 풀이 안에서는 고정한다. 그래야 SLSQP 문제가 반복 중에 바뀌지 않는다. 모든 양이 선언값·분해능·시작점 값에서 오므로 새 상수가 없다.

**불변식**: 척도화 전후의 활성 집합·위반 판정이 같다(판정은 c_k로만 한다).

**상태**: DEV(as-built `[ng-area-budget]`은 상수 곱).

### 7.3 성능·캐시

| 항목 | 설계 | 상태 |
|---|---|---|
| LUT memo 상한 | v1.6: S0당 인스턴스 하나, 계수 상태로 시작해 고정(첫 평가를 버리지 않는다), `memo.call(fn, *args)` 순수성(`lut` 패키지 함수만). 상한 식과 퇴출 판정은 U-60 결정 (가)(§2.4.6): 상한 N_T 무관, 퇴출 허용, 퇴출 뒤 재계산 0. test의 상수 4096을 지운다 | OK(XRUN-F1 card A, 판정 9930c28: `LutMemo.counting`·`open_count`·`fix_bound`, 컨텍스트 생성 커널 평가 0, 상한 (n_θ+1)·U 9회로 확인) |
| tol_V 디스크 캐시 | 키 = 코드 버전 + 입력 내용 sha + 설정 지문. 저장소 밖 경로, 원자적 쓰기, 깨지면 재계산. 정리는 첫 쓰기 때만, 저장소와 모든 worktree의 `lut_v2_location.json`이 가리키지 않는 자료 id만 지우고, 사용 중·링크·폴더 밖 파일은 건너뛴다(사용자 결정 2026-10-08) | PART `[ng-tolv-cache]`: `TableCache`가 `__all__`에 없고 test가 없다. 계획서 N3.5 '디스크 캐시 위치' 문구를 갱신해야 한다 |
| 1변수 풀이 | Brent `bracket_root` + 입력 재사용 memo + 평가 안 tol_V 셀 재사용. v1.6: `solve_self` 근은 LUT memo 순수 함수, `tol_cells`는 memo로(§2.4.6) | OK(master `004b7d2`, `E/sizing/bracket_root.py`). v1.6 형태는 DEV(클로저 memo, `block_columns.py:177,397-398`) |
| core 성능 2~5 | memo 키, 레코드 지문 보관, 투영 지문, 열 키 캐시 | OK(master 병합) |
| 블록 국소 모델 | 블록 노드 부분 MNA를 봉인 스냅샷당 한 번 조립하고, ω=0 극한 풀이만 한다(41 §2.3) | MISS |
| GB4 상한표·출발 구간 | S0 수준 graph 필드(§2.4.8). 실행마다 한 번 계산하고 그 실행 안에서 재사용한다(§2.4.3, v1.10) | DEV(S0당 한 번이지만 객체 사본이고 실행마다 다시 계산. `ParamTables`는 두 벌) |
| 중복 계산 계수(G-10) | (블록, 분할)별 reuses·grafts·computes·recomputes_same_input, memo·S3 색인 계수, 9회로 test(§2.4.9) | PART(`BlockStats`, `recompute_same_key`만) |
| LUT r2 데이터, 검증 중점 L (0.165, 0.85, 1.75, 3.25) | OK `[worktree-agent-a90df…]`(미병합, master보다 45커밋 뒤) | -- |

---

## 8. 승인 없이 축소된 범위와 계획 이탈 (승인하거나 되돌릴 대상)

아래 표는 두 종류를 함께 모았다.
- R1~R28: 로드맵(`_drafts/engine/ROADMAP.md`, 이하 R), 초안, CONTRACT가 계획 요구를 줄이거나 미룬 곳.
- R29~R33: **이 design 자체가 계획 문구와 다르게 정한 곳**.

**결정(사용자 2026-10-08, "Q1~Q11 모두 네 의견대로 진행해")**: 아래 목록이 정본이다. 표의 '상태' 열은 결정 이전 상태를 남겨 둔 것이다.

| 결정 | 해당 행 |
|---|---|
| **복원** | R2, R3, R4(U-49를 복원으로 닫음, 계획서 정정), R5, R6, R8, R9, R10, R11, R12, R13, R14, R15, R16, R20, R21, R22, R23, R25(LR3은 실측 bin 규칙으로 계획 정정) |
| **축소 유지 승인** | R7: `rule_branch_coverage.json`을 만들지 않는다. `기록만` 분기와 S1 지원 밖 분기의 `unsupported_rule_branch` 정지는 그대로 둔다(DEC-59 안전망). R26: test 폴더 체계는 현행 그대로 쓴다. 패키지별 `tests/<패키지>/`, `structure/`, `integration/`, `generality/`이고 §10.3·10.4 경로가 이를 따른다 |
| **수용** | R29: 층 0 첫 회차 = spec 출발 구간. knee 앵커는 추가 후보로 쓴다. R30: U-12를 구조 매크로 모델로 대체한다. R31: U-24에 CM 루프 예외를 둔다 |
| **다른 질문에서 결정** | R17 → Q2, R19 → Q10, R24 → Q6(전력 축 = Σ V·I, U-10 변경), R27 → 잡음 범위 안(Q11), R32 → Q5b |
| **이미 결정됨** | R1(사용자 철회), R18·R33(결정 4번), R28(계획 승인) |

| # | 축소 내용 | 출처 | 계획 근거 | 상태 | 권고 |
|---|---|---|---|---|---|
| R1 | 층 0을 최소형(시작점 하나)으로. 블록별 gain bin front·조합 DP·`gain_budget_db` 출력 없음 | R §4 D18, R §0.2, `search/CONTRACT.md:26-31` | FR-4, DEC-03·71·73·77 | **사용자가 철회(2026-10-08)** | 41 §5대로 복원 |
| R2 | GB3(결합 변수 y) 범위 밖 | R §0.2 행 32, D18 | GB3, DEC-71 (7) | 미결 | 복원: 층 0 조립의 입력(§3.3). 내층 DP·중층 좌표강하는 DEC-73대로 기본 꺼짐 유지 |
| R3 | GB4를 'INFEASIBLE_TARGET만'으로 축소, DOF·수치 rank 범위 밖 | R §0.2 행 33, K6. 계획 N6.1 단위 7('GB4 축소')에도 반영됨 | FR-8, GB4, IC6 | **복원**(Q1, 41 §4.5) | 구조 DOF와 수치 rank 복원(표본 수 = `dof_rank_sample_count`, 41 §4.5). 블록 gain 상한은 계획대로 격자 전수로 계산하고, 예산을 넘으면 '미상'으로 둔다(41 §4.2) |
| R4 | U-49 기본안(층 0 최소형, gain bin front·GB3 범위 밖)이 계획서 안에 있다 | P N7.2 U-49 | FR-4와 긴장 | 미결(계획서 안의 대기 결정) | 2026-10-08 지시로 U-49를 '복원'으로 닫고 계획서를 정정 |
| R5 | 블록 국소 모델·MNA 잔차·감도 게이트 범위 밖 | `metrics/CONTRACT.md:13-14`, 초안 M15:191, L7a:261 | FR-2, DEC-05·66, N3.8 | 미결 | 복원(41 §2, §3.8) |
| R6 | SP1(셀·0-1 BFS·stage·루프 (0)~(4)·끊는 점·R(u)·DEC-81) 연기, declared 대조 연기 | 초안 U25:196·201·133, R N5~N7 미착수 | FR-1, GB2, DEC-43·57·59·63·65·81 | 미결 | 복원(41 §1) |
| R7 | `rule_branch_coverage.json`과 검증 발동 0 분기 정지 없음 | graph CONTRACT | DEC-59 | 미결 | 복원(41 §1.10) |
| R8 | GB5 `gm_req`·`comp_approx_gap` 범위 밖 | `find_front.py:45-48` | DEC-92 (1)(2) | 미결 | 복원(§3.5) |
| R9 | `ls`(슬루·방향별 전류)·스윙·ICMR·`nqs_ratio`·`mismatch_sigma_v` 범위 밖 | `metrics/CONTRACT.md:14` | DEC-58·65·96, N3.8 | 미결 | 복원(§3.8) |
| R10 | spec 로더가 `gain_budget_db_override`·`driving_spec`을 거부 | `SPEC_CONTRACT.md:226-228`, R D5('N3.15 축소') | GB0, DEC-03, DEC-58 | 미결 | 복원(§3.1) |
| R11 | 예산 점 풀이 미작성, `n_starts`·x0 미작성 | `search/CONTRACT.md:535-537,591` | DEC-77, U-13, N3.5 | 미결 | 복원(§3.6) |
| R12 | MOD8 루프·LY7 재평가·판정 축 재필터 미구현(`pending_wiring`) | `layout/CONTRACT.md` 4.14, `search` S-14 | DEC-79 (b), DEC-84, LY3·LY7, 사용자 12번 (나) | 계획은 범위 안 | 구현(§3.9) |
| R13 | L 동치류 L 공유 사실상 꺼짐(`l_class` proposed) | `graph/CONTRACT.md:220` | DEC-17, LR1 | 미결 | 복원(§3.2) |
| R14 | 미러 비율 전류 강제 없음, DEC-95 (3) ratified·② 없음, tol_I 격자 최대 gm | `sizing/CONTRACT.md:276,741,766` | DEC-70, DEC-95, N3.6 | 미결 | 복원(§3.7) |
| R15 | 뷰별 교류접지(바이어스 종속 넷) U5로 연기. 차동쌍 '신호 gate 정확히 2' 조건 빠짐 | `graph/CONTRACT.md:491,538`, JU4:131 | SP1-1 (4), DEC-93 (1) | 미결 | 복원(41 §1.2) |
| R16 | 대칭 θ 묶기 열린 항목 | `search/CONTRACT.md` 3.23 (4) | 사용자 2026-10-08 대칭 결정 | 미결 | 구현(§6) |
| R17 | Pelgrom 계수 선언 없음 → mismatch 보고·matching L 하한 불가 | core 조사 | DEC-96 (2), N3.16 | 선행 조건 | PDK `*__mismatch.corner.spice`의 `vth0_slope`·`toxe_slope` 계열에서 A_VT·A_β를 유도하는 식과 단위 확인을 MOD1/`core` PDK 선언에 둠(§9 Q2). Q3(2026-10-08)로 A_eff 모델(전 slope 변수·bin별 slope·LUT 감도 열)로 확장(41 §6.4-2) |
| R18 | C10: 지속 진동을 undetermined로 유지(계약에 '사용자 승인'으로 기록) | `[ng-oracle-early]` 계약 L42-54 | 사용자 결정 2026-10-08 4번 | 사용자 결정과 모순 | 사용자 결정대로 되돌림(§4) |
| R19 | 오라클이 `pm_undefined`(개루프 RHP 극점 포함)를 일괄 INCOMPLETE로 판정 | `[ng-cmfb-pm]` README, `tools/spice_oracle/README.md:516` | 사용자 결정 A(엔진 탐색 규칙), P N3.6 오라클 합격 정의 | 미결 | Nyquist Z와 폐루프 과도로 판정하고, 둘 다 결정할 수 없을 때만 INCOMPLETE(§4-5). 개루프 RHP만으로 FAIL을 주지 않는다 |
| R20 | ΔA_tie = grid² | `E/layout/floorplan.py:83` | DEC-79, DEC-95 (2) | 미결 | 계획 식으로 수정 |
| R21 | LY5 `W_adjustable=False` 즉시 완화 | `layout/CONTRACT.md:217,306-311` | LY5 마지막 문장 | 미결 | 제거 |
| R22 | LY8 `ly.diffusion` 없음, 판정 축 면적에 수동소자 없음 | `E/layout/_ly_fields.py` | DEC-89 (5), DEC-91 (2), DEC-79 | 미결 | 구현(§3.9) |
| R23 | `verified_by`·모델 오차 레지스트리, `spice_unverifiable` 없음 | `metrics/CONTRACT.md:246,424` | DEC-72, DEC-90 (3), N3.8 | 미결 | 구현(§3.8) |
| R24 | 전력 축 = Σ V·I(`power_dc_w`). DEC-78은 공급 전류 합 | `E/search/objectives.py:9`, `metrics/CONTRACT.md:544,627` | DEC-78, U-10 | 정의 차이 | 사용자 결정(§9 Q6) |
| R25 | LUT: GMBS 열이 있는데 VS 축 선형, FC 위반 칸 선형 폴백, `vgs_for_current_density` 없음, bin 소속을 메타 대신 식으로 판정 | `lut/CONTRACT.md` 1.4, 4.0.1, 4.2 | DEC-87, DEC-88, LR3 | 미결 | `vgs_for_current_density`와 VS Hermite 구현. bin 소속은 실측 384/384 일치 근거로 식 유지를 제안하되 계획 LR3 정정이 필요(사용자 확인) |
| R26 | 새 test 체계의 `contracts/`·`regression/`·`oracles/`·`perf/` 폴더 없음 | `E/tests/` | N3.11, N6.2 T9, IC1~IC11 | 미결 | 단위별로 작성 |
| R27 | 슬루·정착은 SPICE 기록만 한다. 잡음 경로 없음 | 초안 SF:209, M15:43 | DEC-90 (2), DEC-96 (3) | 슬루·정착 '기록만'은 사용자 승인(Q5 (ii)). **잡음은 사용자 결정 2026-10-08로 범위 안이 됨**("노이즈 spec을 추가해서 코드를 만들어야지.") | 슬루·정착은 유지. 잡음은 41 §7대로 구현한다(spec 제약, LUT 잡음 열, adjoint 잡음 해석, 오라클 `.noise`). 계획서 N1.2와 DEC-96 (3)의 잡음 문구는 정정이 필요하다 |
| R28 | 정밀 경로(내층 DP·중층)·전역 샘플·bisection 기본 비활성 | 초안 M6:299 | DEC-73·75 | **계획 승인됨**(기본 비활성) | 유지 |
| R29 | (design 이탈) 층 0 첫 회차의 고정 입력을 LR5 knee 앵커가 아니라 41 §6 출발값으로 둔다 | 41 §5.3 | DEC-71 (3), LR5 | 사용자 확인 필요 | 채택 권고. 근거: 출발값은 스펙에서 나오고, knee는 스펙과 무관하다 |
| R30 | (design 이탈) U-12 단일단 규칙을 일반 매크로 모델(41 §6.5)의 특수해로 대신 낸다. 단일단 판정을 `compensation: null` 태그가 아니라 구조로 한다 | 41 §6.5, §3.5 | U-12, U-50, DEC-85 | U-12 미확정 | 채택 권고(같은 값이 나오고 태그에 의존하지 않음) |
| R31 | (design 이탈) U-24 정지에서 '포트쌍 CM 루프 대응' 루프 뷰를 빼고 사용자 CM 결정(보고 + 경고)을 적용한다 | 41 §1.8 | U-24, 사용자 2026-10-08 CM 결정 | 사용자 확인 필요 | 채택 권고(두 결정의 충돌을 구조적 대응으로 해소) |
| R32 | (design 결정) gain 제약·rout 제약이 모두 없는 회로는 층 0을 끄고 '성능 판정 보류'로 탐색. DEC-71 (3)은 '사이징 대상에서 뺀다' | 41 §5.1 | DEC-71 (3), DEC-85 | 사용자 결정 | §9 Q5b |
| R33 | (design 결정) 지속 진동 판정을 d56ba66 문구(undetermined, '사용자 승인')에서 사용자 결정 2026-10-08 4번(unstable)으로 바꾼다 | §4-2·3 | 사용자 결정 4번 | 사용자 결정이 근거 | 적용 |

---

## 9. 사용자 결정

**결정일 2026-10-08**. 사용자 원문은 "Q1~Q11 모두 네 의견대로 진행해"이며, 전문은 `_drafts/user_decisions.md`의 마지막 항목에 있다. 계획서 N7.2에 U id로 올리는 일은 계획서 정정 커밋에서 한다.

| # | U | 결정 |
|---|---|---|
| Q1 | U-53 | §8 결정 목록대로 |
| Q2 | U-54 | Pelgrom 계수는 PDK `*__mismatch.corner.spice`에서 가져온다. 유도식과 단위는 41 §6.4-2에 기록하고, MC 대조 test로 확정한다 |
| Q3 | U-17 확장 → U-55로 닫음 | **확정(2026-10-08 "q3,q4는 네 제안대로 해")**. mismatch 모델 = 유효 계수 A_eff(toxe의 Vth 기여·약반전 voff 항 포함, LUT 감도 열, bin별 slope -- 41 §6.4-2), 옛 식 대체. 파일럿 `offset_in_sigma_mv ≤ 3.3 mV`(옛 5 mV 대체). 출처 없는 회로는 절대값 대신 구조 가드 `offset_excess ≤ √2` + 보고. 아래 §9.2 |
| Q4 | U-55 | **확정(2026-10-08, 같은 원문)**. 스윙 = 포화 기준(`swing_out_v`), ICMR = 폭(`icmr_v`) + 선언 입력 DC 포함(`icm_margin_v`), 여유 = LUT tol, 레일 밖 입력 불허, 3σ 관례 미사용. 파일럿 스윙 ±1.2 V, nmcnr ICMR·스윙 ≥ 0.5 V, ngcc ICMR ≥ 0.6 V 유지. 헤드룸 불가는 탐색 전 보고(41 §4.6). 아래 §9.2 |
| Q5 | U-44 | topology `_declared_target_spec`(2026-09-21 확정)의 성능 목표를 제약으로 올린다. 회로별 현황은 아래 표 |
| Q5b | U-56 | 제약이 남지 않는 회로도 사이징에서 빼지 않는다. '성능 판정 보류'로 탐색하고 보고한다(41 §5.1) |
| Q6 | U-10 변경 | 전력 축 = Σ V·I(as-built `power_dc_w`). DEC-78 문구를 고친다. 기둥 대조 기록은 유지한다 |
| Q7 | U-06 | **SP1이 산출한 J 항목은 2026-10-08 결정으로 닫혔다(§9.3).** J 공동분석은 SP1 구현 뒤에 한다. Q3·Q4 결정(2026-10-08)으로 목록에 더한 항목: (i) 입력 DC 값 -- nmcnr 0 V(agnd 관례)는 L ≥ 0.5 µm 입력에서 ICMR 창 밖, 파일럿·two_stage·folded·ngcc·common_gate SP-2 값(41 §4.6), (ii) sf_pushpull 차동 대응 짝 M6↔M8·M5↔M7의 matching(서로 다른 gate 묶음이라 J-U4 대칭쌍 그룹이 없다, 레이아웃 matching 대상 확정), (iii) sf_pushpull·pushpull 4-팔로워 버퍼 스택의 헤드룸(41 §4.6 보고 결과를 보고 회로 해석) |
| Q8 | U-57 | 면적 예산은 그대로 둔다. 진단(§7.1-4) 결과를 보고 다시 논의한다 |
| Q9 | U-36 확장 | 저항 면적을 면적 축에 넣는다. 저항 단위 면적은 PDK에서 유도한다(§7.1) |
| Q10 | U-58 | 오라클 최종 판정은 Nyquist Z = N + P(`.pz`로 독립 측정)와 폐루프 과도로 한다. 둘 다 판정할 수 없을 때만 INCOMPLETE다. 탐색은 결정 A의 보수 규칙을 유지한다(§4-5~7) |
| Q11 | U-59 | 잡음: 파일럿은 `noise_out_int_vrms ≤ 300 µVrms`[^qs3](CMFB·바이어스 포함, 하한 1 Hz, 상한은 유도값)이다. 스위치 kT/C 항은 파일럿이 `sampling_caps`를 선언하지 않아 0이다(41 §7, 결정 C-2). 나머지 7회로는 `noise_excess_th ≤ 2`에 열잡음 평탄값·1/f corner 보고를 더한다. pushpull_follower는 보고만 한다. LUT에 저주파 점을 추가한다. DEC-96을 고친다(41 §7) |

[^qs3]: 2026-10-14 Q-S3 로 이 값은 450 µVrms 차동 출력으로 대체됐다(결정 원문은 보존, 경위는 history).

**Q5 회로별 성능 제약 현황**(spec `constraints` + `_declared_target_spec`):

| 회로 | 이미 제약에 있는 것 | 이번에 올리는 것 | 아직 없는 값 |
|---|---|---|---|
| current_reuse(파일럿) | gain ≥ 54, PM ≥ 70, CMRR·PSRR ≥ 60 | 잡음 ≤ 450 µVrms 차동 출력(2026-10-14 Q-S3). Q3·Q4(§9.2): offset σ ≤ 3.3 mV(옛 mismatch ≤ 5 대체), 출력 스윙 ±1.2 V | 입력 DC(SP-2) |
| two_stage_ota | gain ≥ 57 | GBW ≥ 7 MHz(보상 목표 `user_spec`을 제약으로). Q3: 옛 mismatch ≤ 5 폐기 → 가드 `offset_excess ≤ √2`. PM ≥ 70°(2026-10-14 Q-S2) | -- |
| two_stage_ota_sf | rout ≤ 1 kΩ, gain은 two_stage_ota를 참조 | GBW는 두 회로 상속. Q3: 옛 mismatch 참조 폐기 → 가드. PM ≥ 70°(2026-10-14 Q-S2) | -- |
| ngcc_3stage_ff | GBW ≥ 10 MHz, PM ≥ 63.4 | `icmr_v ≥ 0.6 V`(값 유지, 이름 부여). Q3: 가드 | gain |
| nmcnr_amplifier | GBW ≥ 816 kHz, PM ≥ 70 | Q4: `icmr_v ≥ 0.5 V`, `swing_out_v ≥ 0.5 V`. Q3: 가드 | gain(논문 > 100 dB는 채택하지 않음) |
| sf_pushpull_output_opamp | gain ≥ 65, GBW ≥ 60 MHz, rout ≤ 1 kΩ | Q3: 가드 `offset_excess ≤ √2`. PM ≥ 70°(2026-10-14 Q-S2) | -- |
| pushpull_follower_buffer | rout ≤ 1 kΩ | -- | (버퍼, 다른 값 불필요) |
| folded_cascode | 없음 | Q3: 가드 `offset_excess ≤ √2` | gain·GBW·PM 모두 → Q5b 판정 보류 |
| common_gate_amplifier | 없음 | -- | gain·GBW 모두 → Q5b 판정 보류 |

모든 회로에 공통으로 잡음 가드와 면적 예산 제약(결정 11)을 함께 둔다.

### 9.1 (기록) 결정 전 질문 원문

결정 이전의 질문 표다. 기록용으로 남긴다.

| # | U 후보 | 질문 | 왜 사용자 몫인가 | 막는 것 |
|---|---|---|---|---|
| Q1 | U-53 | §8 R2~R26과 R29~R31 각 행(R19는 Q10으로 따로 묻는다)을 복원할지, 승인(축소 유지)할지. 특히 R3(DOF 수치 rank), R4(U-49 닫기), R25(LR3 bin 소속 규칙 정정) | 범위 | 해당 구현 |
| Q10 | U-58 | 결정 A('RHP 극점으로 정의 불가 = 불안정(실패)')를 엔진 탐색 규칙으로만 두고, 오라클 최종 판정은 Nyquist Z와 폐루프 과도로 할지(§4-5~7, R19). 조건부 안정 회로를 합격시킬 수 있는 완화다 | 사용자 결정 문구의 해석 | 오라클 판정 |
| Q11 | U-59 | 회로별 잡음 제약 값: `noise_in_density_ss_v_rthz`(어느 주파수에서 얼마인가: 열잡음 영역, 1/f 영역), `noise_in_integrated_ss_v`(대역과 값). 어느 회로에 둘지도 정해야 한다 | spec 값 | 잡음 제약·출발 구간 활성(41 §7) |
| Q2 | U-54 | Pelgrom 계수 출처로 PDK `sky130_fd_pr__{n,p}fet_01v8__mismatch.corner.spice`(slope 파라미터, 체크아웃 f62031a1)를 쓸지. 유도식과 단위 확인은 엔진이 하고, 출처를 기록한다 | PDK 출처 채택 | matching L 하한(41 §6.4-2), `mismatch_sigma_v` |
| Q3 | U-17 확장 | 오프셋·미러비 오차 스펙 값. 파일럿 `mismatch_sigma_mv ≤ 5`는 U-17 pending이다. 나머지 8회로에도 둘지 | spec 값 | matching L 하한 활성 |
| Q4 | U-55 | 출력 스윙·ICMR 스펙 값. ngcc `icmr_v ≥ 0.6 V` 말고는 선언이 없다 | spec 값 | 헤드룸 gm/ID 하한의 스윙 몫(41 §6.2) |
| Q5 | U-44 | gain 제약이 없는 5회로(common_gate, folded, ngcc, nmcnr, pushpull)의 gain 값, 그리고 GBW·PM이 없는 회로의 값 | spec 값 | 그 회로의 gain 예산·속도 상한 비활성(41 §5.1) |
| Q5b | U-56 | gain 제약도 rout 제약도 없는 회로의 처리. DEC-71 (3)대로 사이징 대상에서 뺄지, 층 0 없이 탐색만 하고 '성능 판정 보류'로 둘지. DEC-85(9회로 전부 합격)와 충돌한다 | 범위 | 그 회로의 층 0·합격 판정 |
| Q6 | U-10 재확인 | 전력 목적 축을 DEC-78 '레일 공급 전류 합'(U-10 확정)으로 할지, as-built Σ V·I로 할지. 3레일 회로에서 front 순서가 달라질 수 있다 | 목적 축 정의 | §3.8 |
| Q7 | U-06 확장 | SP1 유도 뒤 J 공동분석: J2~J13, J12-a~i, 6a 열린 항목 ⑮(J 항목이 없는 DC 역할 그룹 둘) | 회로 해석 | GB2 `review_needed` 해소 → 탐색 |
| Q8 | U-57 | 7.1 진단 뒤에도 예산 안에 해가 없는 회로가 남으면 그 회로의 면적 예산을 바꿀지 | spec 값 | 그 회로 합격 |
| Q9 | U-36 확장 | 저항 면적을 면적 축에 넣을지(단위 면적 PDK 선언 필요), 결정 11 문구대로 뺄지 | 목적 축 정의 | §7.1, DEC-79 `review_needed` |

### 9.2 Q3·Q4 회로별 선언 (사용자 결정 2026-10-08 "q3,q4는 네 제안대로 해")

원문 전문은 `_drafts/user_decisions.md` 마지막 항목, 분석 근거는 `_drafts/engine/matching_swing_spec_proposal.md`다. metric 정의는 §3.8-8, 출발 구간은 41 §6.2·§6.4-2, 탐색 전 보고는 41 §4.6이다. 모든 제약 행은 `{metric, op, value, source}` 형식이고 `source`는 아래 '출처' 열이다.

| 회로 | offset (Q3) | 스윙·ICMR (Q4) | 출처·유도 |
|---|---|---|---|
| current_reuse(파일럿) | `offset_in_sigma_mv <= 3.3`(옛 `mismatch_sigma_mv <= 5` 대체). `offset_sys_mv <= value_from_constraint: offset_in_sigma_mv`(옛 `mirror_ratio_error_mv` 대체) | `swing_out_v >= 2.4`(차동 p-p, 논문 Table I 출력 스윙 스펙 ±1.2 V). `icm_margin_v >= 0`: 입력 DC는 SP-2 (c)(J-E)로 y_icm에서 판정하고 `required_input_cm_v`를 보고한다. 입력 창이 pfet 최단 L bin에서만 열리면 경고 `icmr_window_short_l_bin`(41 §4.6)을 낸다 | `user_spec`(2026-10-08). 3.3 mV 유도: 입력 용량이 논문 β ≈ 0.48 가정(Cf = Cs = 500 fF → Cgg1 ≈ 41.7 fF)을 넘지 않는 최대 면적에서 σ_os = (Σ A_i√c_i)/(2√Cin), gm/ID 15·L 0.5 µm A_eff 기준(제안서 §2.3 (C)). 이 값은 β 0.48 가정의 앵커이고, β 손실이 전력과 교환되는 점은 목적 함수가 다룬다. 정적 ½ LSB 규칙은 이 Cf/Cs에서 해가 없음(제안서 §2.3 (A))을 함께 기록한다 |
| two_stage_ota | 옛 5 mV 절대값 폐기 → `offset_excess <= √2` 가드 + `offset_in_sigma_mv`·`offset_sys_mv` 보고 | 보고만 | 가드 `user_spec`(부하 기여 ≤ 입력쌍 기여, 잡음 가드와 같은 등분 원칙) |
| two_stage_ota_sf | 옛 `value_from_file: two_stage_ota#mismatch_sigma_mv` 폐기 → 같은 가드 + 보고 | 보고만(출처의 '상한 제한'이 sky130에서 좁은 스윙으로 나타난다) | 같음 |
| folded_cascode, ngcc_3stage_ff, nmcnr_amplifier, sf_pushpull_output_opamp | 같은 가드 + 보고(출처에 offset 값 없음) | ngcc: `icmr_v >= 0.6`(값 불변, 이름만 부여, 1.8 V 기준 VDD/3). nmcnr: `icmr_v >= 0.5`, `swing_out_v >= 0.5`(원문 단위 이득 0.5 V 계단 측정 조건, 원문 절대값 그대로). 입력 DC는 SP-2 (c)(J-E: 창 안 자유 변수, agnd 0 V 관례 미적용, `required_input_cm_v` 보고). folded: 보고만. **sf_pushpull: 입력 DC 0.9 V(agnd) 유지 + `icm_margin_v >= 0` 제약**(J-E), 4-팔로워 출력 버퍼 창은 탐색 전 실현가능성 보고(41 §4.6 `buffer_window_report`) | ngcc: 기존 사용자 확정. nmcnr: `user_spec`(Leung et al. Table 1 측정 조건 앵커). sf_pushpull `icm_margin_v`: `user_spec`(J-E 2026-10-08, agnd = 분할 전원 중간 레일 확인). ICMR 제약 회로는 입력 DC가 선언되면 `icm_margin_v >= 0`을 함께 판정(§3.8-8) |
| pushpull_follower_buffer, common_gate_amplifier | 차동쌍이 없어 offset 제약·가드 없음. pushpull은 정지 전류 산포를 `mirror_ratio_sigma_pct`와 같은 식으로 보고 | 보고만(pushpull 선언 입력 DC agnd라 `icm_margin_v` 보고, common_gate 스윙은 출처 식 VDD − VDSAT3 − VDSAT1 − VDSAT2와 대조) | -- |
| 전 회로 | `mirror_ratio_sigma_pct` 보고 | 탐색 전 헤드룸 달성가능성 보고(41 §4.6) | -- |

**유지·이관 항목**:
- bulk 기본 규칙(NMOS = 최저 레일, PMOS = 최고 레일)은 유지한다(Q4 (6)).
- 입력 DC 변경, sf_pushpull M6↔M8·M5↔M7 matching, 버퍼 스택 헤드룸은 회로 해석이므로 J 공동분석 목록에 넣었다(위 Q7 행). 2026-10-08 J 결정으로 닫혔다(§9.3).
- Monte-Carlo offset 분포와 스윙·ICMR DC 스윕 확인은 오라클(U6)이 한다(§10.2).
- 옛 이름(`mismatch_sigma_mv`, `mirror_ratio_error_mv`)이 쓰인 library spec 3개(파일럿·two_stage·two_stage_sf)는 U5가 새 이름·값으로 바꾸고, 옛 이름은 로더 옛 이름 표로 거부한다.

### 9.3 J 공동분석 결정 (사용자 결정 2026-10-08 "j해석은 네의견에 모두 동의해.")

**근거와 원문**: 분석 패킷은 `_drafts/engine/J_joint_analysis_2026-10-08.md`(SP1 `[u1-sp1]` 9회로 실측)다. 결정 전문은 `_drafts/user_decisions.md` 마지막 항목이다. 패킷의 권장안(A2·B1·C1·D1·E·F1-a)을 모두 채택했다.

| 패킷 절 | 결정 | 설계 위치 | 닫는 계획 J 항목 |
|---|---|---|---|
| J-C·J-D 공통 | **복합 diode 구조 규칙 D1**: 같은 DC 가지를 따라가 자기 gate에 닿는 소자 = diode형 바이어스. 실측 발동 sf 6·파일럿 2, 나머지 7회로 무동작. DC 역할·미러 인식·루프 분류에 공통으로 쓴다 | 41 §1.12.1, §1.13 | J12-h, J11(레플리카 루프), N3.2-2 (나) 보류 |
| J-C | 파일럿 CMFB 루프 뷰에서만 Vbias2 교류접지(J1 예외), M58·M63 = 레플리카(D1). 'M58 전류 분할'은 GB7 꼬리 예산 항목(I_tail,eff = I6 + I7 − I68), AC 경로 아님. M7 이중 역할(DC 꼬리 + AC CM 주입) 공존 | 41 §1.12.6, §1.12.1 '바뀌지 않는 것', §3.2-3 사실 표 | J11(파일럿 CMFB·M58), J4 |
| J-D | sf: 세 그룹 = 저항 자기바이어스 캐스코드 미러의 복합 diode 기준(D1). M6↔M8·M5↔M7·R1a↔R1b `branch_symmetric` matching | 41 §1.12.1, §3.2-3 `matching_pair` | J12(sf 부분), J14(sf 부분), J12-h |
| J-A | ngcc A2: 주경로 3단 V1 → V2 → Vout + feedforward 셀 FF1·FF2. gain 예산은 주경로 곱에만 둔다. gmf = 우회한 단 gm 비율은 sizing 제약 후보(출처 기록) | 41 §1.12.2, §2.1·2.2, §4.3, §5.1, §6.5, §3.8-8 `ff_gm_ratio` | J12(ngcc 묶음 경계·gmf1 가지), J12-d 갈래(ngcc만 발동, K8 유지) |
| J-B | 중첩 Miller 내부 루프 = 보상 루프(루프 뷰 미생성). 안정도 = 전체 `pm_ss_deg` + 개루프 RHP 극점 없음(P = 0) | 41 §1.12.3 | J11(ngcc·nmcnr 루프 뷰) |
| J-F | 루프 극성 = 뷰의 DC 사이클 극성, 커패시터 경유 사이클은 `ac_only`. L 동치류 주인 = 주경로 신호 소자(구조 규칙 `main_path_signal`), ngcc {M8, M14} 주인 M8, DC 역할 신호 소자 | 41 §1.12.4·5, §3.2-3 `dc_role` | J7 |
| J-E | nmcnr 입력 DC = SP-2 (c) 창 안 자유 변수(agnd 0 V 관례 미적용). sf 0.9 V 유지 + `icm_margin_v >= 0` 제약 + 4-팔로워 출력 창 사전 보고. 파일럿 SP-2 (c) 유지 + 짧은 L bin 경고 | 41 §4.6 입력 DC 정책, §9.2 | Q7 (i)·(iii) |

**구현 전제(결정 원문 순서)**: design 개정(이 v1.5) → 공유 엔진 코드(U1b, §11) → 회로별 `structure.json`(§3.2-3 표, U1b 병합 뒤).

### 9.4 남은 J 항목 (계획 N7.1, ratify 전)

J-A~J-F(§9.3)가 닫은 것 밖의 J 항목이다. ratify 전에는 엔진 유도 결과(`derived`)를 쓰고, 선언과 어긋나면 `review_needed`로 GB4 전에 정지한다(P N3.3). 아래 '현재 기본안'은 계획 N7.1 문언에 기본안이 있으면 그것이고, 없으면 '엔진 유도'다. 어느 행도 ratify되지 않았다.

| J | 내용(요약) | 현재 기본안 | 상태 |
|---|---|---|---|
| J2 | diode gate 소자의 gate→drain을 같은 stage(미러)로 볼지(nmcnr M201→M203/M204) | 엔진 유도(41 §1 셀·stage 규칙) | 열림 |
| J3 | class-AB(J3-ac 블록 경계, J3-dc `kvl_branch`·정지전류·루프 종속 gm_id·방향별 전류) | stage1 출력노드 = Vop1(계획 문언 기본안) | 열림 |
| J5 | 5T 미러부하·NMCNR 폴딩 미러의 기모드 축약 | 엔진 유도 | 열림 |
| J6 | 출력노드 부하 귀속(파일럿 M18a/M19/M18b, nmcnr M104/M106) | 엔진 유도(규칙 3 load) | 열림 |
| J8 | `fold_group`·`shared_gm_id_groups`·노드 비공유 옛 `budget_reference_device` 선언 4건·의도 태그 | 엔진 유도(태그는 유도 입력이 아니다, U-50). `budget_ref` 엣지는 없다: 공유 노드 옛 선언의 역할은 기둥이 흡수한다(§3.2, 사용자 결정 2026-10-12 "다로 해"). 비공유 4건(M61, M68, M38, two_stage M4)은 이 J8 엔진 유도로 다룬다 | 열림(`budget_ref` 부분은 결정됨) |
| J10 | follower·pass 끝 경로의 독립 블록 여부 | 독립 버퍼 블록(DEC-57, DEC-63 경계 절차) | 열림 |
| J12-a | 버퍼 블록 경계 3건 | 엔진 유도(DEC-63) | 열림 |
| J12-b | A·B·N17·N20 구동 종류 | 전압 구동(용어집 혼재 우선 규칙). N17·N20은 41 §1.5-4 C-1 보완 (가)의 follower 판정이 구조로 정한다(사용자 결정 2026-10-12 "1, 가로 해", §3.2-3 사실 불필요) | 열림(A·B·값 의존 노드·load 귀속) |
| J12-c | G_vgs 사이클 판독·분류(DEC-64) | 엔진 유도 | 열림 |
| J12-d | M17/M20 = K8 측면 주입 대 분기·합류(DEC-81) | K8(계획 문언 기본안). **ratify되지 않았다** -- §3.3 K8 레코드는 이 기본안에서 나온다 | 열림 |
| J12-e | 출력 방향 분류(DEC-65) | 엔진 유도 | 열림 |
| J12-f | 루프 종속 gm_id 소자 선택·합류 노드 KCL | 엔진 유도 | 열림 |
| J12-g | two_stage_ota_sf follower M8의 Miller 루프 밖 여부 | 엔진 유도 | 열림 |
| J12-i | common_gate_amplifier 대조표 | 규칙 유도 결과 그대로(계획 문언) | 열림 |
| J13 | 가지·기둥 유도와 매핑표 대 `vertical_stack_id` | DEC-71 (1)(2) 유도 규칙 그대로, 불일치만 확정(계획 문언) | 열림 |
| J9 | folded·nmcnr `ports`, nmcnr·two_stage `passive_elements` 누락 | 선언 데이터로 해소 -- 현 library topology에 `ports`(각 4개)·`passive_elements`(folded 1, nmcnr 5, two_stage 3)가 있다(측정 2026-10-12 gap 재분석 정정). 회로 해석이 아닌 선언 누락이라 J ratify 없이 닫는다 | 닫힘 |
| J14(sf 밖 8회로) | matching 분류 9회로 대조표 중 sf 외 회로의 matching 레코드(`diff_pair`·`mirror`·`branch_symmetric`·`bias_distribution`·`feedback_shared`) ratify | 엔진 유도(DEC-93 (1) 규칙) | 열림 |

---

## 10. 신규 API·검증

### 10.1 신규 공개 API 서명

41 §8에 있는 API(`build_s1v`, `block_local_gain`, `achievability`, `start_intervals`, `layer0_budget`, `size_and_seal_local`, `count_budget`, `EvalBudget`, `noise_params`, `noise_analysis`, `mismatch_dvgs`, `headroom_bound`)에 아래를 더한다.

```python
def coupling_vars(s1: S1, s1v: S1v) -> Coupling                                    # E/graph/coupling_vars.py  {vars[CouplingVar], column_block_map}
def canonical_form(s1: S1) -> Canonical                                             # E/graph/canonical_form.py {order, generators}
def automorphism_orbits(s1: S1, canon: Canonical, untie: list[Untie]) -> Orbits     # E/graph/automorphism_orbits.py
def ls_fields(snap: GraphSnapshot, s1v: S1v, spec: SizingSpec) -> LsFields          # E/metrics/ls_fields.py
def offset_analysis(snap: GraphSnapshot, s1v: S1v, view_key: str) -> OffsetResult  # E/metrics/offset_analysis.py {sigma_in_mv, excess, contrib[], resolution}
def ls_swing(devices, rails, node_v, outputs, diff_outputs=False) -> SwingIcmr       # E/metrics/ls_swing.py (v1.12: 옛 swing_icmr 행 -- 출력 스윙만, 입력 칸은 기본값; metrics_aux 가 IcmWindow 를 dataclasses.replace 로 합친다, 41 §4.7-5)
def icm_window_metrics(ports: tuple[IcmPort, ...], input_dc: str) -> IcmWindow     # E/metrics/icm_window.py (v1.12 card IT-2, 41 §4.7-5) 정의 함수 하나
def refine_front_windows(sctx, result: EvalResult) -> EvalResult                     # E/search/front_windows.py (v1.12, 41 §4.7-4 5) 수락 반복·front 점에서 두 블록 실행
def saturation_window(unknown, roots, values, gradient, rows, *, slope=None) -> tuple | None       # E/sizing/input_window.py (dlo, dhi, slope{넷: dV/dx}) -- v1.12: 감도를 버리지 않는다, roots = 함께 움직이는 넷 tuple(x0 = 0 이동량; 원소 쌍 (행 넷, 고정 넷) = follower 행), rows = 5원소 (a, b, sign, slack, kind), slope 주면 끝만(KVL -- kvl_sensitivity 감도); 창 끝 식 정본 하나·부르는 블록 셋(O-61 P2, 41 §4.7-3·4.7-3a·4.7-3b)
@compute_block("dc_window_refine")  def refine_input_windows(projection) -> {node.dc_window_def_refined}   # E/sizing/window_refine.py (41 §4.7-4, 수락 반복·front 전용)
@compute_block("ss_nodal")          def ss_nodal_system(projection) -> {graph.ss_nodal}                  # E/metrics/ss_nodal.py (41 §4.7-3b, ss_evaluate.py:101 뒤)
@compute_block("icm_config")        def icm_config_window(projection, theta_items, fixed_values, resistor_values, lut, linear, feedback_decl) -> {node.dc_window_cfg, graph.icm_config}   # E/metrics/icm_config.py (41 §4.7-3b)
def kvl_sensitivity(nodal: NodalSystem, drive, closure) -> tuple                    # E/metrics/icm_config.py (KVL 고정 출력 감도 연립 정본 하나 -- DE-1 (b) 재사용)
@compute_block("metrics_icm_front") def icm_front(projection) -> {graph.metrics_icm_front}               # E/metrics/icm_front.py (41 §4.7-5, 수락 반복·front 전용)
def sensitivity_gate(snap: GraphSnapshot, s1v: S1v, metric: str) -> GateResult     # E/metrics/sensitivity_gate.py
def solve_budget_point(ctx: SearchContext, budget: ObjectiveBudget) -> FrontPoint   # E/search/budget_point.py
def converge(front: Front, ctx: SearchContext, pdk: PdkDecl) -> ConvergedFront      # E/convergence/converge.py (MOD8)
def build_report(result: PipelineResult) -> dict                                    # E/report/report_json.py (MOD9)
def run_gmid_design_pipeline(spec_path, *, search=None, output_dir=None, instrument=False, activations_out=None) -> int  # E/pipeline/run.py
# J 공동분석(§3.2-3, 41 §1.12) -- 단위 U1b
def structure_rule_fp() -> str                                                       # E/graph/s1v_key.py  (사실 stale 판정 지문, §3.2-3)
def build_s1(doc, supplies_v=None, previous=None, column_limit=None, *, structure=None) -> S1Graph  # E/graph/s1_build.py  (기존 서명에 keyword `structure` 추가 -- dc_role 사실 소비)
```

41 §8의 `composite_diodes`, `feedforward_cells`, `loop_roles`도 U1b가 만든다.

### 10.2 검증: 오라클 종류와 test

오라클 종류 (a) 손계산, (b) 참조구현, (c) SPICE, (d) 사용자 선언은 P N0.4를 따른다. 41 §9 표에 다음 행을 더한다.

| 항목 | 오라클 | test(신규) | 단언 |
|---|---|---|---|
| 대칭 궤도·θ 묶기 | (a) 5T·캐스코드 toy, (b) 전수 순열 자기동형(소자 ≤ 8 toy) | `tests/graph/test_canonical_form.py`, `test_automorphism_orbits.py` | diff_pair 두 멤버가 같은 궤도에 든다. crosstab을 생성한다. 이름 전단사나 수동소자 단자 순서를 바꿔도 front 해시가 같다. 파일럿 R1/R2가 한 궤도로 묶이고 전류 부호는 −1이다 |
| d/s 비트 동일 범위(§6-8 D-3, (라)) | (a) d/s 표기만 맞바꾼 입력(전류 부호는 뒤집은 소자 f = −1 손 유도 변환), (a) d/s를 반대로 선언한 toy(선언 VDS ≤ 0) | `tests/search/test_orbit_ties.py::test_ds_flip_symmetry_bit_identical`(옛 `test_ds_flip_ties_bit_identical`), `tests/sizing/test_block_columns.py`(봉인 7 거부) | 궤도·정준 위치·`dc_colour`(노드·원소) 비트 동일, 전류 부호는 뒤집은 소자 f = −1을 원소·상에 곱한 뒤 동일. ties·writer 계획·θ 스키마·front는 비교하지 않는다(선언 방향을 따름). 반대 선언 → 봉인 7 `no_root_in_window`(item 7) 거부, 바른 선언의 같은 동작점 → 봉인 7 통과 |
| diff_pair review(§6-5, (나')) | (d) 9 library 회로, (a) 파일럿에서 넷 하나를 비대칭으로 바꾼 합성 회로 | `tests/graph/test_orbit_matching_crosstab.py`(원본 `graph/orbit_matching_crosstab.py`) | 9회로 review 0(각 회로 `orbit_matching_crosstab` 기록). 합성 회로: (a)(b)를 만족하는 `diff_pair`가 다른 궤도가 되어 `review_needed`(코드 `diff_pair_orbit_split`). 출력 포트가 단일이거나 gate가 입력 포트가 아니면 crosstab 기록만 |
| 전류 기저 열 순서(§6-3) | (d) 9 library 회로 | `tests/sizing/test_current_basis.py`(기존 파일에 추가) | (묶음 수, 탐색 θ 변수 수) = (`len(SearchDomain.ties)`, `len(SearchDomain.variables)`): 파일럿 29/38, 그중 전류 묶음(대표가 θ 전류 성분) 7(M1a~M1b 묶임, M19~M10 묶임), 나머지 8회로는 master `8e46548` as-built 값과 같음. 28/39(규칙 전, 전류 묶음 6)는 기록만. 열 정렬에서 비자명 궤도 원소가 뒤(자유 열로 남음). 열 순서 키가 이름 전단사에 불변 |
| 궤도 넘는 전류 상자(§6-8 D-1) | (a) 완전 차동 직렬 가지 + 출력 사이 R1 toy(nmos·pmos 궤도 전류가 KCL로 묶임, 구성원 상자 교집합 빈 경우·안 빈 경우. `ds_self_swap` 정지에 걸리지 않는다) | `tests/search/test_search_domain.py`(기존 파일에 추가) | 빈 교집합 → `tied_current_box_empty` 거부, 같은 궤도 안 불일치 → `tied_orbit_bounds_differ` |
| MOD8 수렴·재필터 | (a) W_request 합성 픽스처 | `tests/convergence/test_converge.py` | 레이아웃 안 재시도에서 커널 호출 0. 결과마다 재평가 1회. K_max에 닿으면 NONCONVERGENT |
| C10 한계 사이클·Nyquist | (c) 지속 진동 fixture, 조건부 안정 fixture | `tools/spice_oracle/tests/test_oracle_c10_stability.py` | 지속 진동 → unstable(limit_cycle) FAIL. 개루프 RHP이면서 Z = 0이고 과도 안정 → 합격 |
| 척도화 | (a) 1e6 규모 행 픽스처 | `tests/search/test_slsqp_scaling.py` | status 4 없음. 척도화 전후 활성 집합 동일 |
| 아카이브 타입 | (a) 왕복 | `tests/search/test_archive_records.py` | float 왕복 비트 동일. 문자열 숫자는 거부 |
| CM 감지 저항 | (a) R 부하 손계산 | `tests/search/test_cm_sense_r.py` | 최소 R에서 ΔG ≤ b_gain |
| offset 해석(§3.8-8) | (a) 이름 없는 5T·2단 toy 손계산(입력쌍 + 차동쌍 drain 미러 부하), (b) 소자별 섭동 DC 재풀이(MNA 전달과 다른 방법) | `tests/metrics/test_offset_analysis.py` | σ_in이 resolution 안에서 일치. 캐스코드 기여가 1/(gm·ro) 배로 감쇠. 이름 전단사 불변 |
| 스윙·ICMR(§3.8-8) | (a) CS·캐스코드·follower toy 경로 합 손계산 | `tests/metrics/test_ls_swing.py` | 경계 = VDSAT + tol_vdsat, 레일 밖 자름, 빈 창은 음수 폭, 입력 DC 미선언이면 `input_dc_pending` |
| 오라클 offset Monte-Carlo | (c) 오라클 기술자가 선언한 시뮬레이터·PDK 네이티브 MC(능력 확인 PC-3 통과 조합, 오라클 측, 엔진 비의존. oracle-portability O-1). 크기 일관은 엔진 σ_in 대 MC σ_in 비교(offset-trim TR-7 §17-1). 표본 수는 MC σ 추정의 상대 표준오차가 엔진 resolution과 같아지도록 유도 | `tools/spice_oracle/tests/test_oracle_offset_mc.py` | MC 입력 offset σ와 엔진 `offset_in_sigma_mv`의 차를 `model_error_offset_in_sigma_mv`(DEC-72)로 기록. 파일럿 제약 판정에 오라클 값 사용 |
| 오라클 스윙·ICMR DC 스윕 | (c) 출력 DC(되먹임으로 이동)·입력 공통모드 `.dc` 스윕에서 모든 MOS VDS ≥ VDSAT 구간 측정 | `tools/spice_oracle/tests/test_oracle_swing_icmr.py` | 측정 구간과 엔진 [V_lo, V_hi]·창의 차를 모델 오차로 기록. 41 §4.6 '알려진 사례' 4건의 실제 창을 잰다 |

### 10.3 IC1~IC11 계약 test (P N4.1)

R26(축소 유지)에 따라 test 경로는 현행 체계를 따른다. 별도의 `contracts/` 폴더는 만들지 않는다.
- 각 IC test는 담당 패키지 폴더 `E/tests/<패키지>/test_ic<n>_<이름>.py`에 둔다.
- 9회로를 실행하는 test(IC7·IC11)는 `E/tests/integration/`에 둔다.

| IC | test | 입력 | 단언 | 단위 |
|---|---|---|---|---|
| IC1 | `test_vgs_consistency_all_devices` | 9회로 봉인 해 | 모든 소자 \|ΔlnIDu\|/(gm/ID) ≤ tol_V | 4 |
| IC2 | `test_order_shuffle_invariance` | 소자·그룹 순서를 섞은 입력 2벌 | 이산 필드 동일. 연속 필드는 tol 안 | 4 |
| IC3 | `test_coverage_and_field_completeness` | 레이아웃·결과 JSON | 소자 누락 0, 이름 충돌 0 | 9 |
| IC4 | `test_role_label_removal_invariance` | 태그 키가 있는 입력과 없는 입력 | 결과 해시 동일(T2) | 3 |
| IC5 | `test_gate_docstring_declares_blind_spots` | `check_*` 등 게이트 함수 전수 | docstring에 '검사하지 않는 것'과 `영역:` | 0 |
| IC6 | `test_ic6_dof` | 사고19 픽스처 | over/underdetermined 판정(41 §4.5) | 7 |
| IC7 | `test_all_library_topologies_run` | 9회로와 검증 발동 0 분기 변형 | 발동표 생성, 정지(exit 2) | 3 |
| IC8 | `test_unevidenced_derivation_stops_before_search` | 증거 없는 유도 픽스처 | exit 2 | 3 |
| IC9 | `test_no_raw_duplicated_writes` | 소스 AST | 원시 대입 0(구조 규칙 G와 같은 검사기 재사용) | 0 |
| IC10 | `test_cache_key_covers_mutable_state` | 같은 θ, 입력 필드 하나만 변경 | 옛 값 미반환 | 4 |
| IC11 | `test_rail_origin_shift_invariance` | 거부 먼저: 합성 음전위 레일 회로·`pushpull_follower_buffer`(`supply_nets` 삭제). 동등: `two_stage_ota` (1.8, 0) 대 (0.9, −0.9) V, `pushpull_follower_buffer` (1.8/0/0.9) 대 (0.9/−0.9/0) V(§3.10.8과 같은 회로) | VGS·VDS·VSB·gm_id·W·metric이 tol 안에서 같음 | 10 |

### 10.3a DF 재발 금지 표 (P N5.2, 사용자 승인 2026-10-12 P-8)

P N5.2의 DF는 옛 엔진의 결함 기록이고, 새 엔진에서는 재발 금지 계약이다. DF마다 계약 test 또는 구조 lint 하나를 두고, 그 test가 걸린 구현 단위(§11)의 완료 조건에 넣는다. test는 처음부터 TS7 규칙(§3.10.8)대로 `xfail(reason="<단위>", strict=True)`다. '상시'는 매 변경마다 도는 구조 test(`E/tests/structure/`, 규칙 A~K(K = §2.4.3 front 조회 규칙, v1.10)와 §2.4.10 확장)다. test 파일 이름은 test 작성 주체가 확정하며, 확정하면 이 표를 갱신한다.

| DF | 재발 금지 내용(새 엔진) | 계약 test | 담당 단위 |
|---|---|---|---|
| DF-01 | 옛 입력 버전으로 계산한 파생 필드는 봉인 4가 거부(버전 혼재 금지) | `tests/sizing/test_df01_stale_input_version_rejected` (+ IC10) | U4 |
| DF-02 | 노드 경로 충돌은 봉인 1이 거부 | `tests/sizing/test_df02_node_conflict_rejected` | U4 |
| DF-03 | 후보 실패는 `ValueError`가 아니라 N3.14 실패 레코드이고 탐색이 계속됨 | `tests/search/test_df03_candidate_failure_continues` | U11 |
| DF-04 | 소자는 정확한 이름(또는 구조)으로만 찾음, 부분문자열 금지 | 구조 규칙 E(이름 리터럴) + IC4 | 상시 |
| DF-05 | 미러비 σ는 그룹의 모든 쌍을 봄 | `tests/metrics/test_df05_mirror_ratio_all_pairs` | U7 |
| DF-06 | 광범위 except 금지 | 구조 규칙 F | 상시 |
| DF-07 | 상한에 닿으면 LRU 퇴출(캐싱 중단 금지). U-60 결정 (가)에서 퇴출은 정상 동작이고 퇴출된 키의 재계산만 FAIL이다(§2.4.6) | `tests/core/test_df07_bounded_lru_evicts` | U17 ③ |
| DF-08 | spec 지문 불일치면 유도 임계값을 쓰지 않고 거부 | `tests/authoring/test_df08_fingerprint_mismatch_rejected` | U5 |
| DF-09 | 면적 예산 식이 선언 계수를 상쇄하지 않음(§7.1 식 손계산 대조) | `tests/search/test_df09_area_budget_formula` | U11 |
| DF-10 | 역산(VGS·L·gm/ID)은 단조 구간 밖에서 근을 내지 않고 실패 레코드를 냄 | `tests/lut/test_df10_inverse_monotonic_guard` | U3 |
| DF-11 | LUT 조회 실패 시 대입값 금지(실패 레코드) | `tests/sizing/test_df11_no_substitute_on_lut_failure` | U4 |
| DF-12 | 입력환산 offset은 모든 소자의 기여를 셈(gm 없는 소자를 조용히 빼지 않음) | `tests/metrics/test_df12_offset_all_devices` | U7 |
| DF-13 | `id()` 키·상한 없는 캐시 금지 | 구조 규칙 G 확장(§2.4.10) | 상시(U17 ③에서 활성) |
| DF-14 | `except Exception` 폴백 금지 | 구조 규칙 F | 상시 |
| DF-15 | 영점 상쇄 R은 입력 버전 있는 필드(`device.passive_value`) | `tests/metrics/test_df15_zero_cancel_is_versioned_field` | U17 ① |
| DF-16 | 전력 축 = 선언 레일 Σ V·I(직렬 기둥 중복 계상 없음) | `tests/metrics/test_df16_power_rail_sum` | U7 |
| DF-17 | 기대값·기준선 파일에 실패 출력(FAIL 문자열, 예외 메시지, 실패 판정 값)이 들어 있지 않음. 아직 통과하지 못하는 계약은 `xfail(strict=True)`로만 표시 | `tests/structure/test_df17_no_failing_baseline`(기대값 파일 전수 검사 + `xfail`에 `strict=True` 없는 test 0) | 상시 |
| DF-18 | 실패하면 0이 아닌 exit code(`exit_code_for`), θ*는 결과 JSON에 기록 | `tests/pipeline/test_df18_exit_code_on_failure` | U16 |
| DF-19 | 레일은 선언(`supply_nets`·`supplies_v`)으로만 판정 | `tests/authoring/test_df19_rails_from_declaration` (+ IC11) | U5 |
| DF-20 | 근거 없는 폴백 상수 금지 | 구조 규칙(숫자 리터럴) | 상시 |
| DF-21 | 실행 불가 probe 금지 -- 새 엔진에는 probe 폴더가 없다 | 구조 규칙(파일 구성 A~D) | 상시 |
| DF-22 | 지문 불일치 기록은 거부로 이어짐(DF-08과 같은 test) | `test_df08_fingerprint_mismatch_rejected` | U5 |
| DF-23 | 소자·넷·회로 이름 리터럴이 동작을 정하지 않음 | 구조 규칙 E + IC4 | 상시 |
| DF-24 | vsb는 bulk 선언과 노드전압에서만 유도(레일 원점 가정 금지) | IC11 `test_rail_origin_shift_invariance` | U16 |
| DF-25 | 포화 하한은 LUT `VDSAT` 열(2/(gm/ID) 금지) | `tests/sizing/test_df25_seal7_uses_vdsat_column` | U4 |
| DF-26 | 레일 판정에 넷 이름 집합 금지(DF-19와 같은 test) | `test_df19_rails_from_declaration` + IC11 | U5 |
| DF-27 | LUT 축 밖 입력은 실패 레코드(클램프·외삽 금지) | `tests/lut/test_df27_axis_out_of_range_rejected` | U3 |
| DF-28 | CGS·CGB 열이 없으면 근사 표시를 기록(조용한 근사 금지) | `tests/metrics/test_df28_cgs_cgb_approximation_flagged` | U7 |
| DF-29 | metric이 회로 파일·넷 이름 리터럴을 열지 않음 | 구조 규칙 E + IC4 | 상시 |
| DF-30 | metric 등록부에 회로 이름 키 없음 | `tests/metrics/test_df30_registry_no_circuit_keys` | U7 |
| DF-31 | 보상 규칙에 회로별 함수 없음(구조 판정) | `tests/metrics/test_df31_no_circuit_compensation` | U7 |
| DF-32 | 헤드룸은 S1 유도 역할로만(라벨 금지) | IC4 `test_role_label_removal_invariance` | U13 |
| DF-33 | spec에 소자 이름 기반 override 필드 없음(로더 거부) | `tests/authoring/test_df33_device_override_rejected` | U5 |
| DF-34 | 회로마다 코드 추가 없이 9회로 실행(PDK 상수는 PDK 선언 하나) | IC7 `test_all_library_topologies_run` | U16 |
| DF-35 | 저장소 절대 경로를 코드에 박지 않음 | `tests/structure/test_df35_no_absolute_repo_paths` | 상시 |
| DF-36 | 산출물의 경로는 저장소 루트 기준 상대 경로 | `tests/report/test_df36_relative_paths` | U16 |
| DF-37 | 광범위 except가 N3.14 클래스를 삼키지 않음 | 구조 규칙 F | 상시 |

### 10.4 DoD 명령

`$PY` = `C:\Python314\python.exe`, 작업 위치는 저장소 루트다.

**공통 완료 조건**: 모든 엔진 코드 변경 단위는 아래 표의 해당 명령과 함께 **graph 단일 정본 확인**(사용자 결정 2026-10-12 "design 승인, 이후에는 design과 구현을 gap분석해. 그리고, 모든엔진은 graph 단일정본 원칙이 준수되었는지를 coding후에 항상 확인하는 과정을 넣어."): 엔진 코드를 바꾸는 모든 변경 단위는 병합 전에 다음 넷을 통과한다. (a) 구조 규칙 G 확장 lint(G-8, §2.4.10 ①) green (b) 설계 값 타입 위치 검사(§2.4.10 ②) green (c) 40 §2.4.8 필드 소유표 대조 -- graph 밖 저장소는 허용 셋(LUT memo 순수 함수, S3 기록·색인, 실행 계수)뿐이고 새로 생긴 값은 graph 필드다. 새 필드는 같은 변경에서 소유표에 행을 더한다 (d) G-10 중복 계산 계수(§2.4.9)를 그 변경이 건드린 회로에서 잰다: 같은 실행 안 같은 입력 버전 재계산 0, LUT memo 퇴출 뒤 재계산 0. 그리고 구현 단계(U17 ①②③과 각 구현 단위)가 끝날 때마다 design ↔ 구현 gap 분석(bkit gap-detector, 일치율 90% 이상, 미만이면 반복 개선)을 한다. 명령은 표의 'graph 단일 정본 확인' 행이다. **계산값 재사용 확인**(사용자 지시 2026-10-12 "coding시에 계산값 재사용원칙도 준수되었는지 확인하는 과정을 넣고 이 확인내용을 항상 보고해"): (a) G-10 계수 -- 같은 실행 안 같은 입력 버전 재계산 0, LUT memo 퇴출 뒤 재계산 0 (b) 계산 블록·분할·필드별 재사용(`reuses`·`grafts`)과 재계산(`computes`) 계수를 `perf`에 기록 (c) cProfile + 중복 인자 계측으로 루프 안 같은 인자 반복 호출 0(WP-10) (d) 루프 불변식이 루프 밖(S0 수준 필드, WP-23 (3))으로 나갔는지 확인. **두 확인(graph 단일 정본·계산값 재사용)의 결과는 숫자와 함께 단위 보고에 항상 넣는다**(단위 보고 필드 `graph_canon_check`·`reuse_check`).

| 범위 | 명령 |
|---|---|
| 전체(slow 제외 -- conftest가 `--run-slow` 없으면 slow를 뺀다) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests -q` |
| 전체(slow 포함, 판정용) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests -q --run-slow` |
| IC 계약 | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests -q -k "test_ic"` |
| 9회로 구조 표(S1v·A_max·Π·인증 비율) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration/test_structure_tables.py -q` |
| 9회로 E2E(T9) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration -q` |
| 오라클 | `$PY -m pytest skills/analog-gmid-design/tools/spice_oracle/tests -q` |
| graph 단일 정본 확인((a)(b) 정적, (d) 계수)과 계산값 재사용 확인((a)(b) `perf` 계수, (c) `--profile`, (d) 루프 불변식 대조) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/structure -q -k "rule_g or design_value_location"` 뒤 `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration -q -k "g10"`(건드린 회로). (c)는 변경 diff와 §2.4.8 소유표를 대조해 보고에 적는다 |
| design ↔ 구현 gap 분석 | bkit gap-detector(42 기준표 기준), 일치율 90% 이상 |
| 계산값 재사용 확인 (c) 중복 인자 호출 | `$PY -m gmid_engine.pipeline <spec> --profile runs/<run_id>/profile.out --instrument runs/<run_id>/dup_args.jsonl` 뒤 `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/perf -q -k "duplicate_args or loop_invariant"`: 루프 안 같은 인자 반복 호출 수 = 0(WP-10), 루프 불변 입력이 S0 수준 필드에서 읽힘(WP-23 (3)). 결과 숫자는 단위 보고 `reuse_check`에 넣는다 (사용자 지시 2026-10-12 "coding시에 계산값 재사용원칙도 준수되었는지 확인하는 과정을 넣고 이 확인내용을 항상 보고해") |
| P N6.2 단위 4(IC9, 공유 gate 넷 전압 하나, 4회로 KCL 잔차 ≤ tol_I, IC1·IC2·IC10) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/sizing -q -k "ic1 or ic2 or ic9 or ic10 or shared_gate_net or kcl_residual"` |
| P N6.2 단위 5(MNA 조립 계수 1, 풀이 계수 = ω 수) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/metrics -q -k "mna_assembly_count or mna_solve_count"` |
| P N6.2 단위 6(cProfile 기록 파일, WP-23 계수) | `$PY -m gmid_engine.pipeline <spec> --profile runs/<run_id>/profile.out` 뒤 `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/perf -q` |
| P N6.2 단위 10(IC11 2·3레일, push-pull 등식 잔차 ≤ 멤버 수 × tol_V) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration -q -k "ic11 or kvl_branch_residual"` |
| 공유 블록 전후 대조(DEC-51) | `$PY tools/compare_runs.py --before <base 결과 디렉터리> --after <변경 결과 디렉터리>`: 9회로 노드전압·front·SPICE verdict 차 표를 쓴다. verdict 차가 있으면 보고 맨 앞 |

### 10.5 A' 판정 기준 (P DEC-98, U17 단계 ② 완료 조건)

사용자 결정 2026-10-13 "1은 권고, 2도 권고, 3도 권고대로" (3)과 "①, ②, ③ 권고대로 진행해" ①. 이 절은 규칙만 적는다. 첫 사례(nmcnr 시범)의 경위·수치는 계획 history H1·H4에 있다. 'P U-76 (n)'은 결정 원문 밖이라 원칙으로 정한 기본안(사용자 변경 가능)이다.

| 역할 | 누구 | 규칙 |
|---|---|---|
| 판정자 | SPICE 오라클(`tools/spice_oracle/`, §4. 선언된 시뮬레이터 어댑터, 첫 사례 ngspice) | 합격 정의 = P N6.2 T4·T5(DEC-90). MOD8 전 점(시작점, MOD8 전 front 점)은 T4-pre 기하(아래). 엔진 점과 손분석 설계를 같은 정의로 판정한다 |
| 독립 대조군 | AI 손분석 | 결정 원문 "코드 없음"(해석: 엔진 코드를 보지 않는다. LUT 조회·계산 보조 스크립트는 허용). 회로마다 1회 문서로 고정한다. 값마다 유도 근거(회로 원리·LUT 조회·spec 값)를 적고 상수를 발명하지 않는다(P WP-03). 결과는 엔진 입력(spec·topology·`structure.json`·출발값)으로 쓰지 않고 판정 기준으로도 쓰지 않는다(판정은 SPICE 오라클). 손분석 작성 주체 ≠ 엔진 코드 작성 주체(P WP-13) |
| 피검 | 엔진 시작점(층 0·출발 구간, 41 §5·§6)과 front 점(P U-45 대상: 양 끝점 + 예산 점) | 둘 다 아래 완료 조건에서 SPICE 오라클로 판정한다 |

**판정 규칙**(결정 (3), 실패 정의는 P U-76 (7) 결정 문언 풀이)

| 엔진 | AI 손분석 | 분류 | 기록 | 그 회로의 완료 |
|---|---|---|---|---|
| 실패 | 통과 | 엔진 결함 | A' 대조표로 원인 | 아님(P U-76 (1)) |
| 통과 | 실패 | AI 해석 오류 | 사용자 공동분석(P N7.1) 기록 | 완료(P U-76 (8)) |
| 통과 | 통과 | -- | 전력·면적 차(출처 아래) | 완료 |
| 실패 | 실패 | 판정 불능(P U-76 (2)) | 사용자 공동분석(AI만 실패와 같은 경로) | 원인 확정 전 아님 |

* 엔진 쪽 조건(P U-76 (7)) = 봉인 통과(P N3.6) + spec 제약 행(`graph/metrics: constraint_rows`, §2.4.8) 전부 c ≥ 0. 엔진 실패 = 그런 점을 내지 못함 또는 그 점의 SPICE 오라클 불합격. AI 실패 = 손분석 설계의 SPICE 오라클 불합격. front 점(P U-45)에도 엔진 쪽 조건(봉인 통과 + c ≥ 0)을 적용하고, front 점의 SPICE 오라클 불합격도 엔진 실패로 A' 대조표 대상이다. 근거: 엔진 자기 예측도 spec 충족을 주장해야 SPICE 오라클 통과가 우연이 아니다.
* **T4-pre** = T4·T5와 같은 판정 정의에 MOD8 전 기하를 쓴 판정: 넷리스트 W = sizing W 그대로(레이아웃 전), 접합 기하 ad/as/pd/ps = LUT 특성화와 같은 규칙 -- `assets/sky130_lut_sweep.py` `DUT_LINE`(W = 5 µm 기준 ad = as = 2.5e-12 m²(= 2.5 µm², ngspice `2.5p`), pd = ps = 7e-6 m)을 W에 비례시킨다. 전도 문턱 `off_current_A`(DEC-90 (1))는 같은 엔진 코드로 sizing W에서 계산한다. 손분석 설계의 전도 집합은 손분석 문서가 선언한 집합이다. 그 점의 T5도 T4-pre 기하로 잰다(P U-76 (3)). MOD8 수렴 뒤 front 점은 기존 T4·T5다.
* 미측정 제약 행(§2.4.12 Q8)과 `spice_unverifiable[]` 제약은 c ≥ 0 판정에서 빼고 보고서에 목록으로 낸다. SPICE 오라클은 측정할 수 있는 항목만 판정한다(P U-76 (4)).
* 전력·면적 차의 출처(P U-76 (9)): 전력 = SPICE 오라클 측정, 면적 = 엔진 면적 코드(P DEC-79)에 손분석 W/L/finger를 넣은 값. 손계산 수치는 A' 문서 참고값으로만 쓴다(P WP-21). 손분석점과 front 점의 전력·면적 차는 기록만 하고 A' 판정 기준값이 아니다(P U-76 (6)).
* A' 대조표 = 같은 항목(소자 L·gm/ID·ID·W, 노드전압, 보상 소자 값, spec 제약 행 c 등)에서 손분석 값과 엔진 값을 맞대고, 갈린 항목마다 회로 원리 근거의 원인 가설을 적은 표. 손분석과 대조표는 `docs/03-analysis/aprime/<회로>.md` 한 문서이고 실측 원본(넷리스트·로그)은 그 문서에서 경로로 참조한다(P U-76 (6)).

**U17 단계 ② 완료 조건**

1. 대상 = library 9회로 + held-out 회로. held-out = library 9회로 밖이고 엔진 개발(코드·test 픽스처·`structure.json` 사실·spec 값 조정·발동표 측정)에 쓰지 않은 회로(P DEC-98 (4)). **선정은 사용자 몫**(P U-75).
2. 회로마다 (가) 엔진 시작점(층 0·출발 구간)이 엔진 쪽 조건을 만족하는 점을 내고 그 점이 SPICE 오라클 T4-pre·T5를 통과하고 (나) 엔진 front 점(P U-45 대상)도 SPICE 오라클을 통과한다 -- MOD8 전 점은 T4-pre, MOD8 수렴 뒤 점은 T4·T5.
3. 엔진 실패 회로(엔진만 실패·판정 불능)는 A' 대조표를 남기고, 그런 회로가 남으면 완료가 아니다(fail-closed). 회로별 예외는 그 회로의 대조표 + 사용자 결정으로만 둔다(P U-76 (1)). AI만 실패한 회로는 그 회로 완료로 보되 공동분석 기록을 남긴다(P U-76 (8)).
4. library 9회로 도달률(2를 만족한 회로 수 / 9)은 회귀 지표로만 기록한다. 일반성의 근거는 held-out 회로다.
5. held-out 정의 세부: held-out 회로의 실패를 고치려고 엔진을 바꾸면 그 회로는 개발 회로로 옮기고, 다음 일반성 판정에는 새 held-out 회로가 필요하다(P U-76 (5) 기본안).

---

## 11. 구현 단위 (병렬 배분용)

**목적**: 오케스트레이터가 code agent를 최대 6개까지 동시에 돌릴 수 있도록 구현을 독립 단위로 나눈다.

**배분 규칙**
- **파일 소유**: 한 단위가 고치는 파일은 그 단위만 고친다. 아래 '범위' 열이 파일 소유권이다.
- **공유 파일**
  - `E/_module_map.py`: 각 단위는 자기 행만 추가한다. 병합할 때 오케스트레이터가 합친다.
  - `E/<패키지>/__init__.py`의 `__all__`: 그 패키지를 소유한 단위만 고친다. 다른 단위의 새 API가 필요하면 아래 '선행' 열의 단위가 먼저 공개한다.
- **선행 단위가 끝나기 전**: 그 인터페이스(41 §8, 40 §10.1 서명)를 기준으로 toy 입력 test부터 쓴다. 실제 회로 test는 선행 단위가 병합된 뒤에 활성화한다.
- **완료 조건**(PDCA 구현 단계, 각 단위 공통)
  - 아래 '확인 행'의 42 기준표 행이 OK가 된다.
  - 그 단위의 test가 통과한다.
  - 전체 suite(`--run-slow`, 판정 때 한 번)가 통과한다.
  - 코드 작성 주체와 test 작성 주체가 다르다(WP-13).
  - **graph 단일 정본 확인**(사용자 결정 2026-10-12 "design 승인, 이후에는 design과 구현을 gap분석해. 그리고, 모든엔진은 graph 단일정본 원칙이 준수되었는지를 coding후에 항상 확인하는 과정을 넣어."): 엔진 코드를 바꾸는 모든 변경 단위는 병합 전에 다음 넷을 통과한다. (a) 구조 규칙 G 확장 lint(G-8, §2.4.10 ①) green (b) 설계 값 타입 위치 검사(§2.4.10 ②) green (c) 40 §2.4.8 필드 소유표 대조 -- graph 밖 저장소는 허용 셋(LUT memo 순수 함수, S3 기록·색인, 실행 계수)뿐이고 새로 생긴 값은 graph 필드다. 새 필드는 같은 변경에서 소유표에 행을 더한다 (d) G-10 중복 계산 계수(§2.4.9)를 그 변경이 건드린 회로에서 잰다: 같은 실행 안 같은 입력 버전 재계산 0, LUT memo 퇴출 뒤 재계산 0. 그리고 구현 단계(U17 ①②③과 각 구현 단위)가 끝날 때마다 design ↔ 구현 gap 분석(bkit gap-detector, 일치율 90% 이상, 미만이면 반복 개선)을 한다. **계산값 재사용 확인**(사용자 지시 2026-10-12 "coding시에 계산값 재사용원칙도 준수되었는지 확인하는 과정을 넣고 이 확인내용을 항상 보고해"): (a) G-10 계수 -- 같은 실행 안 같은 입력 버전 재계산 0, LUT memo 퇴출 뒤 재계산 0 (b) 계산 블록·분할·필드별 재사용(`reuses`·`grafts`)과 재계산(`computes`) 계수를 `perf`에 기록 (c) cProfile + 중복 인자 계측으로 루프 안 같은 인자 반복 호출 0(WP-10) (d) 루프 불변식이 루프 밖(S0 수준 필드, WP-23 (3))으로 나갔는지 확인. **두 확인(graph 단일 정본·계산값 재사용)의 결과는 숫자와 함께 단위 보고에 항상 넣는다**(단위 보고 필드 `graph_canon_check`·`reuse_check`).

**U0 -- 선행 병합**(오케스트레이터, code agent 아님)
- 대상 브랜치: `ng-cmfb-pm`, `ng-oracle-early`(계약), `ng-tolv-cache`, `ng-layer0-canon`, `ng-area-budget`, `worktree-agent-a90dfb25fa6fe9f04`(LUT r2), `ng-bridge`.
- 이 브랜치들을 병합하고, 병합할 때마다 전체 suite를 돌린다(사용자 결정 3).
- 이후 단위들은 병합된 master를 출발점으로 쓴다.

| 단위 | 범위(소유 파일·패키지) | 설계 절 | 선행 | 웨이브 | 확인 행(42) | test 계획 |
|---|---|---|---|---|---|---|
| **U1 SP1 구조** | `E/graph/` 신규 파일: `views`, `ac_ground_view`, `signal_reach`, `cells`, `drive_kind`, `stage_bfs`, `blocks`, `pole_nodes`, `loops`, `loop_classify`, `loop_cuts`, `polarity`, `buffer_bundles`, `output_direction`, `composite_blocks`, `declared_compare`, `s1v_build`. `structure.json` 로더. L 동치류 `derived` 처리와 주인 결정 | 41 §1, 40 §3.2 | U0 | 1 | FR-1, DEC-17·29·43·57·63·65·81, D-GB1a, D-GB2a~j | 41 §9 SP1·루프 행. toy 2~4소자(a), 9회로 표(d), 이름 전단사 |
| **U1b J 규칙 + structure 사실** | `E/graph/` 신규 파일 `composite_diode.py`, `feedforward_cells.py`, `loop_roles.py`. 수정 파일: `dc_roles.py`(규칙 1c 복합 diode, 규칙 4 `dc_role` 상속), `s1_build.py`(`structure` 인자, S1 키에 사실 지문), `drive_kind.py`(미러 입력 확장), `cells.py`(복합 diode 묶음 `diode_load`), `stage_bfs.py`(diode 단자 비용), `blocks.py`·`composite_blocks.py`(FF 분리, FF 합류는 복합 블록 아님), `loop_classify.py`((1.6) 추가, (나) 축소), `polarity.py`(DC 사이클 극성·`ac_only`), `l_classes.py`(`main_path_signal`), `view_analysis.py`, `ac_ground_view.py`(뷰 한정 예외), `matching_groups.py`(`matching_pair`), `structure_load.py`(concept 어휘·override/confirm·고아·불일치), `s1v_values.py`·`s1v_key.py`(`structure_rule_fp`), `s1v_build.py`(`loop_roles` 소비, `applied_facts`). `E/pipeline/stage_a.py`·`stage_a_report.py`(사실 로드 순서, `declared_loop_cuts`, 보고 행). `graph/CONTRACT.md`·`pipeline/CONTRACT.md` 해당 절 | 41 §1.12·§1.13, 40 §3.2-3, §9.3 | U1·U2 병합(U1 = `[u1-sp1]`·`[u1-sp1-tests]`) | 2 | D-J1~D-J7 | 41 §9의 J 행 5개(toy (a), 9회로 (d), 거부 확인, red test 먼저). 9회로 발동표: D1 = 41 §1.13 실측 집합, 나머지 7회로 무동작. FF는 ngcc만. 루프 뷰·정지·review 수의 U1 대비 변화표. 이름 전단사 불변. **사실 파일 작성은 이 단위가 아니다**: 병합 뒤 오케스트레이터가 §3.2-3 표를 실측과 대조해 쓴다 |
| **U2 대칭** | `ng-layer0-canon`의 정준 라벨링·궤도를 `E/graph/canonical_form.py`·`automorphism_orbits.py`로 옮긴다. 수동소자 무향 처리와 부호 −1 묶기. `orbit_matching_crosstab`(`E/graph/orbit_matching_crosstab.py`, test `tests/graph/test_orbit_matching_crosstab.py` -- diff_pair review (나') 포함). `E/search/orbit_ties.py`·`tie_expand.py` 갱신 | 40 §6 | U0 | 1 | D-SYa~d, R16 | 40 §10.2 대칭 행. 파일럿 R1/R2 궤도, 단자 순서 뒤집기 metamorphic |
| **U3 LUT·PDK 확장** | `E/lut/`: `vgs_for_current_density`, VS Hermite, FC 정책, `ft_curve`·`intrinsic_gain_curve`·`vdsat_curve`·`idu_curve`, `noise_params`, 잡음 LUT r1 로더, `LutMemo.from_sweep` 배선 도우미. `assets/sky130_lut_sweep.py`에 `.noise` 모드와 **mismatch 감도 모드**(Q3: `*_slope_spectre` 섭동 → DVGS 열, 새 버전 파일 `..._mismatch_r1.npz`, 공유 데이터 덮어쓰기 금지) 추가, `mismatch_dvgs` 로더·`tol_mismatch`. `E/core/pdk_decl.py`와 PDK 선언 json에 EF, mismatch slope(카드 `.model` 블록별 bin 지도 + slope 이름, pfet L < 0.5 µm `vth0_slope1` 등), poly 저항 양 추가 | 41 §4.1, §6.4-2·2b, §7.2, 40 §7.1, R25 | U0 | 1 | DEC-87·88, D-LUTc, D-NZ2, D-PF1·2, D-GB4a(분류 쪽), D-PG, D-MM1·2 | 격자점·칸 중앙 ngspice 대조(c), 감도 열 칸 중앙 섭동 대조(c), `vth0` 성분 = √2·slope(bin별)(a), 소자 쌍 MC 단위 확인(c), Ω당 면적 손계산(a) |
| **U4 sizing 보강** | `E/sizing/`: L 동치류 L 공유(θ 스키마), 미러 비 강제, S2p 기반 tol_I(v1.6 §3.7-3·U17 ①로 대체, G-3' -- 자기 동작점 `dc_gm`), DEC-95 (3) 전체 순서, W_request 고정 W, `size_and_seal_local` | 40 §3.7, 41 §5.3 | U0(② 순서 항목은 U1 인터페이스 필요) | 1 | DEC-17(θ 쪽)·32·70·95, D-GB7a~d, D-LS | IC1·IC2·IC10 test, 국소 봉인 toy |
| **U4b 미러 비 강제** | DEC-70 `matching_ratio` 전류 기저 강제 관계 I_out = ρ·I_ref. 비율 출처를 새 θ 종류로 두고, 그 θ를 아는 search 쪽(`search_domain`, `fd_jacobian`, `cone_rows`, `start_points`, `layer0_center`)과 대칭 쪽(`orbit_ties`, `current_symmetry`)을 같은 커밋에서 고친다. 상자는 멤버·기준 전류 상자에서 유도한다(상수 금지). 경위: U4가 sizing 쪽만으로는 search를 깨거나 안 쓰이는 코드가 되어 멈춤(`sizing/CONTRACT.md` 15절, 2026-10-08) | 40 §3.7, P N3.4 DEC-70 | U4, U11 | 2 | D-GB7b, DEC-70 | 미러 toy 손계산(ρ = 2, 3), 대칭 묶음 비율 1과 겹치지 않음, θ 원뿔 상한 유도 대조 |
| **U5 authoring·spec** | `E/authoring/`: `gain_budget_db_override`(배열 키), `driving_spec`, `structure_count_budget`, 잡음 metric 어휘, `noise_testbench`, 옛 이름 표 수정(`input_dc_net`·`topology_hash`·`derived`), `spice_unverifiable[]`. `E/core/units.py` 잡음 단위와 Q3·Q4 단위(`pct`, `ratio`, `v`). Q3·Q4 metric 어휘(`offset_in_sigma_mv`, `offset_excess`, `offset_sys_mv`, `mirror_ratio_sigma_pct`, `swing_out_v`, `icmr_v`, `icm_margin_v`)와 옛 이름 표(`mismatch_sigma_mv`, `mirror_ratio_error_mv`, `mismatch_sigma_v`). `assets/library/*.sizing_spec.json`에 Q5 승격·Q11 잡음 제약·**§9.2 Q3·Q4 선언**(파일럿 3.3 mV·스윙 2.4 V·icm_margin, 6회로 가드, ngcc·nmcnr ICMR, nmcnr 스윙) 반영 | 40 §3.1, §3.8-8, §9, §9.2, 41 §7.1 | U0 | 1 | FR-9, DEC-68·69·90(3), D-GB0a, D-NZ1, D-Q34 | 거부 test(옛 이름·출처 없음·`metric_unknown`), 9회로 로드, §9.2 표와 spec 대조 |
| **U6 오라클** | `tools/spice_oracle/`: C10 한계 사이클과 안정 fixture 불변, 고Q 표시, `.pz` P, 위상 펼침 N과 Z 판정, `.noise` 개루프·폐루프 SC 테스트벤치, **offset Monte-Carlo**(mismatch 블록 gauss, 입력 환산 분포)와 **스윙·ICMR `.dc` 스윕**(Q3·Q4 (8)), `ORACLE_MEASURES` 추가 | 40 §4, §10.2, 41 §7.6 | U0 | 1 | D-OR1~5, D-NZ6 | 40 §10.2 C10·offset MC·스윙 DC 스윕 행. 조건부 안정 fixture, `.noise` 손계산 저항 분압, MC 표본 수 유도 |
| **U7 metrics 이득·보고** | `E/metrics/`: `block_model`, `block_residual`, 결합 잔차 측정, `sensitivity_gate`, `ls_fields`(슬루·방향별 전류), `ls_swing`(`swing_out_v`·`icmr_v`·`icm_margin_v`), `nqs_ratio`, `offset_analysis`(`offset_in_sigma_mv`·`offset_excess`·`offset_contrib`, MNA adjoint 공유), `offset_systematic`, `mirror_ratio`(옛 `mismatch_sigma_v` 대체), `verified_by`·모델 오차 레지스트리 | 41 §2, 40 §3.8 | U1(블록 정의), U3(A_eff 감도 열) | 2 | FR-2, DEC-05·23·58·66·72·96, D-BM, D-SG, D-GB8a~c, D-OF1~3, D-MR, D-SW, D-ICM | CS·캐스코드 손계산, 단일 블록 잔차 0, offset toy 손계산·섭동 재풀이(b), 스윙·ICMR 경로 합 toy |
| **U8 metrics 잡음** | `E/metrics/noise_sources.py`, `noise_analysis.py`, 잡음 제약 행 연결 | 41 §7.3·7.4 | U3, U5 | 2 | D-NZ3·4 | 4kTR·4kTγgm 손계산(a), SPICE 오라클 noise(c) |
| **U9 GB4 달성가능성** | `E/metrics/achievability.py`, `curve_checks.py`, `block_gain_bound.py`, `dof_report.py`, `area_lower_bound.py`, `headroom_bound.py`(Q4 헤드룸 창 상한·유도 보고), `E/search/count_budget.py` | 41 §0, §4 | U1, U3 | 2 | FR-8, D-GB4a~f, D-NS, D-NM | 격자 직접 전수 toy(b), 불가능 스펙 exit 3, IC6 사고19, 계수 예산 결정론, follower 스택·두 극성 입력 toy 상한 |
| **U10 GB3 결합** | `E/graph/coupling_vars.py`, `column_block_map` | 40 §3.3 | U1 | 2 | D-GB3, DEC-71 (2)(7) | 9회로 매핑표, 귀속 안 된 소자 정지 |
| **U11 search 정비** | `E/search/`: SLSQP 척도화, 타입 있는 아카이브 레코드, 예산 점 풀이, `n_starts`·L-c 분지, ε 간격과 점 예산, CM 감지 저항 최소화, CM 1 dB 대체 제거, 면적 예산 출발점과 W 타당성 | 40 §3.6, §5-4, §7.1·7.2, §3.5 | U0 | 2 | D-SC, D-AC, D-BP, D-ST, D-EPS, D-CM4, D-CMR, D-AR2·3 | 1e6 행 픽스처, 왕복 비트 동일, 예산 점 1개 |
| **U12 layout 정비** | `E/layout/`: ΔA_tie, LY5 즉시 완화 제거, `matching_L_mismatch`, `ly.diffusion`, 그룹 경계 tap, 판정 축 면적에 수동소자(MIM·poly 저항) 포함 | 40 §3.9 | U3(저항 PDK 양) | 2 | D-LY1~4, R20~22 | 해시 대조, 면적 손계산 |
| **U13 출발 구간·매크로 모델** | `E/search/start_intervals.py`, `iv_*`(Q3·Q4: `iv_headroom`의 스윙·ICMR·입력 DC 예산 분할, `iv_matching_l`의 A_eff 기반 matching L 하한과 offset 가드 부하 gm/ID 상한), `macro_poles.py`, `dominant_node.py`, `eval_budget.py` | 41 §6(§6.2, §6.4-2·2a), §7.5, §5.8 | U1, U3, U9 | 3 | D-SIa~g, D-DN, D-NZ5 | 손계산 toy, 이상 VCCS 2·3극점, 절대 offset 회로에서만 L 하한 활성 |
| **U14 MOD8 수렴** | `E/convergence/`: `converge`(W_request 루프, LY7 재평가, 판정 축 재필터, K_max). **U12 인계(2026-10-09)**: 봉인 스냅샷 → `LayoutInput` 어댑터(수동소자는 `layout.passives_from_decl` 사용), `run_layout`의 유일한 프로덕션 호출처, ΔA_tie(`area_tie_m2`)를 `pareto.nondominated(ties=)`에 배선, 설계점 스냅샷 `ly_diffusion` 필드(옛 칸 이름 `LayoutResult.diffusion` -- U17 ①-e에서 필드로 옮겨 없어짐)·`RealizedDevice.diffusion` 재검증 소비, LY5 즉시 완화를 지운 뒤 W 조정 불가 그룹(pattern None)의 완화 판정 | 40 §3.9 | U4, U12 | 3 | D-M8, R12 | W_request 합성 픽스처, 커널 호출 계수 |
| **U15 층 0 gain 예산** | `E/search/`: `layer0_budget`, `gain_bins`, `local_candidates`, `local_front`, `combo_dp`, `assembly`, `budget_override`, `layer0_inverse`, `l_targets`(41 v1.6 §5.3·§5.10 구현 변경 목록). `layer0_center`는 대체되어 초기점 생성 전용이 된다 | 41 §5 | U4, U7, U9, U10, U13 | 4 | FR-4, DEC-03·10·71·73, D-L0a~i | 2블록 toy DP = 전수, 파일럿 `gain_budget_db` 출력 |
| **U16 보고·진입점·통합** | `E/report/`, `E/pipeline/`(`ng-bridge` 흡수). **인계(2026-10-09)**: (i) 엔진이 정한 finger 폭(mismatch σ의 bin 선택, U7 `device_sigma`: W/ceil(W/w_bin_max(L)))을 오라클 입력으로 넘겨 오라클 넷리스트 `w=finger_w m=n`이 같은 bin을 쓰게 한다(출처 하나); (ii) `build_search_context(s1v=)`로 S1v를 넘기는 진입점(구조 의존 metric·잡음 입력 셀); (iii) U7 `model_error_pairs` 적재(오라클 대조 결과); (iv) 내부 루프 뷰 `loop_cut` 선언의 PM metric 평가 경로(U1b 인계), (v) 결과 JSON이 설계점마다 `layout_outputs(snapshot)`을 한 번 부르는 배선(완료 조건, 사용자 결정 2026-10-12 "4번 권고대로", 42 D-LY5), `tests/integration/`의 9회로 E2E·구조 표·IC7·IC11·회귀 추적 | 40 §3.9, §10 | U14, U15, U6 | 5 | D-M9·M10, D-IC, D-T, T1~T9 | 9회로 E2E, 오라클 대조 |

**U17 graph 단일 정본·중복 계산 제거**(v1.6 graph 정본 개정, 사용자 결정 2026-10-12, design 문안 사용자 승인(2026-10-12 "design 승인")). 설계 절은 §2.4이고 확인 행은 42 D-GR1~D-GR15다. G-9에 따라 41 §5 층 0 개정(U15 재구현)과 같은 design 개정에 묶고, 구현은 세 단계로 순서대로 한다. 단계마다 옛 코드와 그 test를 같은 변경에서 지운다(WP-01). 재작성 범위는 사용자 규칙을 따른다: 옛 구조가 남는 곳은 전체 재작성, 나머지는 부분 수정이다.

| 단계 | 범위(소유 파일) | 재작성 범위 | 같은 변경에서 지우는 것 | 선행 | 확인 행 | test |
|---|---|---|---|---|---|---|
| **① graph 층 이동** | S1v 저장(`E/graph/s1v_build.py` 출력층, `s1v_values.py`의 `S1v` 묶음), GB3 출력(`coupling_vars.py`), U9 출력층(`E/metrics/achievability.py`·`achievability_types.py`의 `Achievability` 묶음), U13 데이터 흐름(`E/search/start_intervals.py`, `iv_context.py`, `iv_curves.py`, `start_values.py`의 `StartContext`·`StartIntervals`. `graph/start`의 `noise_inputs`·`placement`와 KVL 기록은 ② -- v1.9.1 D3·D4), S0 수준 스냅샷 직렬화(신규 `E/core/snapshot_codec.py`·`type_registry.py`, 패키지마다 `__init__` 등록, `E/pipeline/stage_a.py`·`stage_b.py` 배선, 저장 시점 = `build_search_context` 끝 1회 -- §2.4.3 v1.9.1 D6. **v1.10: 실행 사이 재사용 제거 card(② 선행)가 이 직렬화를 지운다**), 단계 B 층(`residual_probe`·`dof_numeric` 필드 자리와 직렬화 제외 규칙만. 블록 배선은 ② -- v1.9.1 D5), 커널 컨텍스트 구조 파생과 SearchContext 선언 파생의 S0 수준 필드(`E/sizing/kernel_context.py`, `E/search/search_domain.py`, 제약 분류, 접합·mismatch 출처, 면적 선언, 모델 오차), CurveBook·ParamTables의 LUT 파생과 `edge_costs`(metrics → lut)를 `E/lut/derived_fns.py` 모듈 함수로(as-built `memo.lookup` 형식으로 호출, `call` 형식 전환은 ③ -- v1.9.1 D10), `metrics_dc`의 `gate_area_m2`·`power_resolution_w`(search `_power_resolution` 삭제), 수동소자 값 블록(`E/metrics/passive_values.py` → 계산 블록, 소비자 `ss_evaluate.py`·`search/kernel.py`·`convergence/converge_point.py`. `search/_helpers_area.py`는 출발 구간(S0 층) 추정이라 S2 필드 `device.passive_value`를 읽을 수 없으므로 ①-b(S0 필드 이동)로 이월), tol_I gm 필드(`E/sizing/seal_tolerances.py`, `seal_kcl.py`, `kernel_run.py`, `seal.py`, `E/metrics/ss_linearize.py`, `search/objectives.py`·`search_values.py` b_P), 레이아웃 필드(`E/layout/run.py`, `contract_output.py`의 `LayoutResult`, `E/convergence/` 어댑터) | **전체 재작성**: S1v 저장, U9 출력층, U13 데이터 흐름(`StartContext`·`CurveBook` 폐기), S0 수준 스냅샷 경로. **부분 수정**: 수동소자 값(R = 1/Σ`dc_gm`), tol_I, 레이아웃 출력, `metrics_dc` | `StartContext`, `CurveBook`, `ParamTables` 두 벌 생성, `search/objectives.py`의 `_power_resolution`·`gate_area_m2` 계산, `S1v`·`Achievability`·`StartIntervals` 묶음 전달, `previous_gm_id`·`inherited_gm_id`·`canonical_gm_id`·`gm_grid_max`와 `dc_gm_bound` 필드, `kernel.py:146-150` 수동소자 규칙 사본, `sctx.spec_passive_values`, 레이아웃 별도 lineage(`GraphSnapshot.empty(LY_WRITERS)`), 이것들을 직접 단언하던 test | U9·U13 병합(as-built) | D-GR2·3·7·8·13, D-GR9(레이아웃 부분) | `test_s0_snapshot_roundtrip`(v1.10 대상 소멸), 수동소자 필드 단일 writer, tol_I parent 무관(같은 θ·다른 parent → 같은 봉인 결과), 9회로 front 재측정 기록(Q7) |
| **XRUN-F1 A·B·C**(v1.11, 사용자 결정 2026-10-15 X-1~X-14, ② 선행) | §2.4.14 (3)·(5): C = 모든 커널 평가를 E_total에(X-8). 후속(범위 밖, X-14): 감도 게이트 기준점이 상자 밖이면 '검사 못 함' 보고. A = ln 좌표 원값 보존 정본 `ThetaCoords`·첫 평가 버림 제거, B = 블록 결과 색인(계보 무관·실행 수명)·`*` 이식·`RunCounters` 블록 계수·`ComputeBlock` 무상태화·실패 평가 부분 스냅샷·`perf.blocks` | §2.4.14 (3) | §2.4.14 (4) | A: 실행 사이 재사용 제거 card(병합 f23aec8). B: A 병합 | 42 D-XR1~D-XR5, D-GR4·5·6·9·12·15(일부) | §2.4.14 (5) |
| **IT-1 + IT-2**(v1.12, 계획 v6.22 N6.5·N6.6, 사용자 결정 B2·K-3·O-13·O-15 (B)·O-16 (2)·O-19 (2)·O-21·O-33 (3)·O-49·O-50 G4·O-52·O-53 A-1·A-2·O-54·O-55 U1·V5·O-58·O-59 (1)(2)·O-61 P1~P6(O-62 승인)·O-94 (2)(3)(O-95 승인)·O-96(card IT-2e, O-97 승인); **하나의 통합 병합** -- 각자 test·code 커밋) | **IT-1**: `E/sizing/writer_plan.py`(같은 DC 엣지·`input_tie`·`input_tie_order` 삭제, 입력 포트 뿌리 y 키 = 넷, `input_port_multiple_roots` 정지), `s2_values.py`(`REL_TIE`·`PATH_TIE`·`INPUT_GROUP_KEY`·`TIE_INPUT_ORDER` 삭제, `BRANCH_INPUT_MULTIPLE_ROOTS` 추가), `__init__.py` export, `block_columns.py`(tie 사슬·`REL_TIE` 분기 삭제, `input_roots`, θ 키), `scc_order.py`(`:21`·`:26`·`:125`·`:137-140`, 41 §4.7-1 1), `E/metrics/achievability.py`(`tie:` 등식), CONTRACT(`E/sizing/CONTRACT.md:232-238`·`:497` 등, 41 §4.7-1 1) -- 계획 N6.5 소비자 표 전부. **IT-2**: `E/sizing/input_window.py`(`saturation_window` 감도 반환), `block_columns.py`(커널에서 `_refine_ends` 호출 제거, 모든 입력 포트 `node.dc_window`, `Window` 칸 둘, READS `node.port_direction`), 새 `E/sizing/window_refine.py`(`dc_window_refine`), 새 공용 helper `E/sizing/_helpers_dc_solve.py`(두 블록이 함께 쓰는 `Circuit`(메서드 `saturation_rows`·`input_windows` 포함)·`solve`·`FAILURES`만 옮김 -- 구조 규칙 A 보충 (3)·B, 41 §4.7-4; 끝 풀이는 `window_refine.py` 비공개 함수로 새로 씀), 새 `E/metrics/icm_window.py`·`icm_front.py`(`metrics_icm_front`), `metrics_aux.py`·`ls_swing.py`(입력 창 삭제, 새 서명)·`aux_types.py`(`IcmPort`·`IcmWindow`), 새 `E/search/front_windows.py`(`refine_front_windows`), `E/search/fd_jacobian.py`(W4 뿌리만), `E/search/slsqp_outer.py` `accept`·`E/search/find_front.py` `_point_record` 앞(호출 배선), 새 `E/metrics/ss_nodal.py`(`ss_nodal`)·`icm_config.py`(`icm_config`, `kvl_sensitivity`), `aux_types.py`(`NodalSystem`·`IcmConfig`), `offset_analysis.py:69`·`offset_systematic.py:46`·`block_residual.py:73`(조립 → `graph.ss_nodal` 읽기), `ss_evaluate.py`(`:101` 뒤 호출 배선), `E/core/graph_snapshot.py`(`derive_child`)·`E/sizing/kernel_run.py`(파생 자리·parent 일치 검사를 base writer 전부로 넓힘)·`seal_versions.py`(coverage·서로소 단언, 인자 `ctx.base`) -- 41 §4.7-3c, keep 집합 = `ctx.base` writer(`block_versions`) ∪ 호출 블록(계획 v6.22 N3.3, 사용자 결정 O-61 P1; `_CONTEXT_WRITERS`는 옮기지 않음; v1.12.9 card IT-2e -- 계획 v6.32 N6.6 범위 5, 사용자 결정 O-96: 그 집합의 정의 하나 = `seal_versions.writers_in_scope`, 실패 부분 스냅샷도 그 함수로 줄여 붙임 -- §2.4.7 '정의'·'전달'), `s2_values.py` `DC_WRITES`·`SS_WRITES`, `_module_map.py`, CONTRACT 소유표 -- 계획 N6.6 소비자 표 + 41 §4.7-0 A10·§4.7-6 | 부분 수정(쓰기 계획 규칙·창 배치), 새 블록 넷(`dc_window_refine`·`metrics_icm_front`·`ss_nodal`·`icm_config`) | `input_tie` 어휘·`REL_TIE` 분기·`INPUT_GROUP_KEY`·`ls_swing` 입력 창 계산·`block_columns._refine_ends`, 이것들을 단언하던 test 기대값(test 주체가 바꾼 규칙 기대값으로 다시 씀, `broken_tests` 이유 'K-3'·'IT-2') | XRUN-F1 card B 병합, 결정 6(충족), card 0 IT-0(검증자, M-I1~M-I7, 41 §4.7-8a), **S-1~S-4·T-1·O-59 (2)는 계획 v6.21(사용자 O-60 승인) 맞춤으로 41 §4.7-3a·§4.7-3b·§4.7-3c에 설계됨(새 블록 `ss_nodal`·`icm_config`, 새 필드 `graph.ss_nodal`·`graph.icm_config`·`node.dc_window_cfg`, `GraphSnapshot.derive_child`·`CONTEXT_WRITERS`; 착수 실측 멈춤 조건 41 §4.7-9; 옛 D1~D6은 O-49로 결정됨)**; 뒤: headroom-chain HC-S(`saturation_rows`를 고친다 -- IT-1·IT-2 → HC-S), DE-1, ME-1; 완료 판정 선행 EO-1(SPICE 다리 -- 계획 N6.3 (iv), 병합 선행 아님); card IT-2e 순서·착수 조건 = 41 §4.7-9(계획 v6.32 N6.6 순서) | 계획 N6.5 완료 조건 1~7, N6.6 완료 조건 (0)~(11) | 41 §9 §6.7-1a·§4.7 행, 41 §4.7-1·4.7-7 interface; **card IT-2e**(v1.12.9, 계획 v6.32 완료 조건 (11)(e), 41 §4.7-7 L11 (e)): parent가 있는 평가에서 블록별 실패(커널 블록(steps·later 구성원) 각각 -- 구성은 IT-2d 병합 head 실측, 봉인 항목 블록 각각 -- 구성 = `SEAL_ITEM_BLOCKS` 상수를 걷는다; 후보 실패 주입) -- `block_versions` 키 = base writer ∪ 앞 블록, 실패 블록과 그 뒤 블록 없음(parent 값이 남으면 red), fp = parent 없는 대조 평가(평가 키 캐시를 거치지 않고 다른 실행 쌍 `open_run`)의 부분 스냅샷 fp = 실패 줄 `snapshot_fp`(변성 관계, 사례 유효 조건 (가)(나)과 (가)의 관측 -- 41 L11 (e)); 봉인 위반 + parent 한 건 -- `dc_seal_report` 필드가 남고(지우면 red) fp가 대조 평가와 같음; `writers_in_scope(None, …)` `TypeError`(건너뛰면 red); AST 재구현 0 검사(셀 연산 = 41 4.7-3c)와 red 변형 둘; parent 없는 기존 부분 스냅샷 test 불변, 계수 변화 0 |
| **② search 상태·층 0** | (v1.11: `*` 이식·`Donors`·블록 결과 색인 `find`·`register`·`RunCounters` 블록 계수·`ComputeBlock` 무상태화·`EvalResult.partial`은 XRUN-F1 B가 먼저 한다. ②는 분할(선언·`write(name, part, ...)`·`block_version(name, part)`)과 아래 나머지) core 분할 계산 블록과 `graft`(`E/core/compute_block.py`, `graph_snapshot.py`의 `block_versions` 키, 신규 `core/graft.py`), 평가 커널 ②~⑤·봉인 블록의 분할 선언(`E/sizing/block_*.py`, `seal_*.py`), S3 메모리 색인과 보존(신규 `E/search/s3_index.py`, `local`·`solved` 분리, 보존 소유자 5종(v1.11 폐지 -- 실행 수명 보존, §2.4.5), `archive.py` `snapshots/` 인코딩 -- v1.10: 타입 있는 S0 코덱은 없다, §2.4.5 'U17 ② 착수 전 정의'), 계수 소유 이동(`ComputeBlock` 무상태화, 신규 `core/run_counters.py`, `BoundedLRU._evicted`·`TableCache.events` 이동), 층 0 필드(`graph/layer0: macro`·`comp_approx_gap`·`rounds`, `graph/local` 블록 범위 metric), 제약 행 `graph/metrics: constraint_rows`(①-c에서 이월, `unmeasured` 자리는 §2.4.12 Q8), 단계 B 층 블록 배선(`residual_probe`·`dof_numeric`, 소비자 층 0과 함께 -- ①에서 이월, v1.9.1 D5), `graph/start`의 `placement`(U15 `placer`와 함께, v1.9.1 D4)·`noise_inputs`(β·C_eff 계산과 함께)·KVL 기록(`records`에 추가, v1.9.1 D3), `SearchContext`(G-7), `kernel.evaluate`, `EvalResult`·`SsEvaluation` 사본 제거, 층 0의 이식 사용(`layer0_budget.py`, `local_candidates.py`, `local_front.py`, `combo_dp.py`, `assembly.py`, `size_and_seal_local.py`의 `LocalSeal`) | **전체 재작성**: search 상태층(`search_context.py`, `kernel.py`의 캐시·기록 부분, `EvalResult`), 층 0 데이터 흐름(41 §5 v1.6 U15 재구현과 한 변경). **부분 수정**: core 블록(분할 추가, 분할 없는 블록은 `*` 하나로 as-built와 같은 동작), 커널 블록 분할 선언 | `sctx.cache`·`disk_failures`·`computed_keys`·`cell_floors`·`local_seal_memo`, `_disk_failures`, `ComputeBlock`의 계수 칸·`_seen_inputs`·`reset_stats`(v1.11: XRUN-F1 B가 지운다), `SsEvaluation.ss/dc`, `EvalResult`의 값 칸, `LocalSeal.snapshot_fragment`·`power_w`·`area_m2`, 오케스트레이터 초안 EvalCache, 이것들을 단언하던 test | **XRUN-F1 card B**(v1.11, 위 행), ①(①-b 완료: 병합 eadb729, 4차 판정 988eef4 -- 차단 0), U15 design(41 §5 v1.6) 승인, **실행 사이 재사용 제거 card**(v1.10, 사용자 결정 2026-10-15 "나로 해": §2.4.3 삭제·변경 목록 전부, 옛 코드·test는 같은 변경에서 지운다. NFR-4 card보다 먼저 또는 같은 변경. LUT 파생표 디스크 캐시는 건드리지 않는다(Q9 유지). `code_hash`는 바꾸지 않는다(Q10 유지). S3 실행 사이 재사용은 지운다(Q11 제거). front 조회는 조회 전용 읽기 경로로 남긴다(U-90). 모두 사용자 결정 2026-10-15 "U-87은 LUT는 관리복잡도가 없다는 네 판단근거에 따라 유지. 나머지는 기본안대로"), **NFR-4 결정성 card**(v1.9.4, 사용자 결정 2026-10-15 "1안·3안 진행하고 ③ 기준 변경도 승인해" -- v1.9.2 결정 8의 '엔진의 원인 연산 수정'을 이 결정으로 대체한다. 결함 자체는 v1.9.2 기록 그대로다: 스레드 수에 따라 출발 구간 필드 지문이 비트 단위로 달라진다. 범위: 1안 BLAS 스레드 고정·실행 환경 지문(§2.4.3, §2.4.13 (1)), 3안 판정 경계 배치 규칙(41 §5.13), ③ 검증 기준·필드 분류·비교기(§2.4.13 (2)~(5)). 2안(순수 Python SQP)은 하지 않는다. 순서: design → test·code → 독립 판정이다. ②의 기준선 측정 전에 끝낸다. Q-N1~Q-N10은 모두 결정됐다(사용자 결정 2026-10-15 "기본안대로 진행해", §2.4.13 (8)). 완료 조건은 §2.4.13 (5) '이 card의 완료 조건'이다. pushpull 다른 환경 결함은 후속 card NFR4-F1(완료를 막지 않음). test 환경의 스레드 1 고정은 이 card의 같은 변경에서 거둔다), **결정 10 code_hash card**(상태: 완료(af10c9b, 판정 ecda471 -- gap 15/15, 차단 0). 방식 v1.9.3(옛 §2.4.3 '블록 코드 해시' 행 -- v1.10에 history로 옮김). 순서: design 정정 → test·code → 독립 판정. v1.10: 옛 완료 조건 '그 행 (9)'와 '판정 2의 다른 checkout 부분 (9) (b)'는 판정 2·S0 재사용 폐지로 대상 소멸이다. checkout 무관 성질은 유지한다(Q10, U-88, 사용자 결정 2026-10-15 "U-87은 LUT는 관리복잡도가 없다는 네 판단근거에 따라 유지. 나머지는 기본안대로"). code 범위에 `E/core/engine_code_fp.py:8` 주석과 `E/core/CONTRACT.md:237,245` 갱신을 포함한다) | D-GR1·4·5·9·10·14, D-AP1 | `test_graft_equals_compute`, `test_index_single_source`(v1.11, XRUN-F1 B -- 옛 `test_graft_donor_order_invariant` 대체), `test_partition_scc_not_split`, 분할 블록 시드 금지(같은 θ·다른 parent → 같은 분할 값), (v1.11 대상 소멸: 옛 '보존 규칙(풀이 중 기준점 유지·끝나면 놓음)' -- 실행 수명 보존), 색인 적중 = 커널 0, 층 0 조립점에서 비공유 분할 `computes` 0. **완료 조건 = A' 판정 기준**(§10.5, P DEC-98: library 9회로 + held-out 회로에서 시작점이 봉인 통과·spec 제약 행 c ≥ 0이고 SPICE 오라클(T4-pre·T5) 통과, front 점(P U-45)도 SPICE 오라클 통과, 엔진 실패 회로가 남으면 미완료·A' 대조표, 9회로 도달률은 회귀 지표) |
| **③ LUT memo·lint·G-10** | `E/lut/lut_memo.py`(`call`·계수 상태·상한 B_r), `sweep_memo.py`, LUT 순수 함수로 옮기는 것(`E/search/cell_floor.py`, `E/metrics/block_param_tables.py`, `edge_costs` 호출처, `E/sizing/block_columns.py`의 `solve_self`·`tol_cells`), 구조 규칙 G 확장·설계 값 타입 위치 검사·SC-a/SC-b lint(`E/tests/structure/structure_checks.py`, `_module_map.py` 필드 형식 열), memo 상한·퇴출 판정(§2.4.6 사용자 결정 (가)/(나)에 따라 -- 결정이 착수 조건), G-10 test(`E/tests/perf/`, `E/tests/integration/`) | **전체 재작성**: memo 생성·상한 배선(`_wire_sweep_memo`, `sweep_memo` -- v1.11: 첫 평가 버림·`sweep_memo` 삭제는 XRUN-F1 A가 먼저 한다. ③은 인스턴스 하나·B_r 전체 항), `ParamTables`. **부분 수정**: `cell_floor`·`solve_self`·`tol_cells`(memo 함수로 옮김), 구조 검사(규칙 추가) | `LutMemo.lookup`(클로저형), `_Unmemoized`, `_CountingMemo`·`sweep_memo.py`(v1.11: XRUN-F1 A가 지운다), 두 번째 memo 인스턴스, `ParamTables` 클래스와 두 벌 생성, `CurveBook`의 LUT 사전(①에서 클래스 삭제), §2.4.10 실측 위반 줄 전부, 이것들을 단언하던 test | ②, §2.4.6 사용자 결정, XRUN-F1 A(v1.11) | D-GR6·11·12·15 | `test_lut_memo_single_instance`, `test_lut_memo_purity`, `test_g10_no_recompute_9circuits`(v1.11: XRUN-F1 B가 판정 1·5로 만들고 ③은 판정 3을 더한다), 구조 규칙 G 확장의 거부 확인 픽스처(규칙마다 위반 예 1개가 실제로 거부됨) |

**U17과 다른 단위의 관계**:
- U15(층 0)는 ②와 한 변경이다. 41 §5.3.9의 `local_seal_memo` 문구는 41 개정이 §2.4.5를 인용해 바꾼다.
- U16(오라클 입력)은 수동소자 값을 `device.passive_value` 필드에서 읽는다(①).
- U2(대칭)의 궤도 결과는 S0 수준 필드다(§2.4.8). 별도 브랜치 초안 f786dc6은 병합하지 않는다.
- IT-1·IT-2(v1.12)의 helper 이동이 바꾸는 다른 문서의 코드 경로(후속 정정 -- 각 문서가 자기 개정에서): headroom-chain HC-S의 `block_columns.saturation_rows` → `_helpers_dc_solve.Circuit.saturation_rows`, gain-budget 계획 N6.8 DE-1 F-DE5의 `block_columns.py:246-257`(→ `Circuit.input_windows`)·`:663-694`(`_refine_ends` 삭제, 끝 풀이 = `window_refine.py`), N6.6 F-I2-1·F-I2-4·소비자 표 줄 번호, design 42 D-J5·D-ICM(41 §4.7-9).

**J 결정(§9.3)이 다른 단위에 더하는 범위**(파일 소유는 위 표 그대로이고, 범위만 더한다):

| 단위 | 더하는 범위 | 설계 절 | 확인 행 |
|---|---|---|---|
| U4 | SP-2 (c): 입력 DC 대기 회로의 W4 입력 공통모드 y_icm 범위 = 입력 창(봉인 시점 경계). v1.12: y 키 = 입력 포트 W4 뿌리 넷(최대 하나, card IT-1), 커널 경계 = 선형 감도 끝·끝 풀이는 수락 반복·front(card IT-2, 41 §4.7) | 41 §4.6, §4.7 | D-J5 |
| U5 | metric 어휘 `ff_gm_ratio`(단위 ratio). sf_pushpull spec에 `icm_margin_v >= 0`(`user_spec` J-E) | 40 §3.8-8, §9.2 | D-J2, D-J5 |
| U7 | FF 경로 기여, 분해 합성값 A_decomp 잔차, `ss.ff_contrib`, `ff_gm_ratio` 값. `icm_margin_v`를 y_icm에서 계산, `required_input_cm_v`(v1.12: 입력 포트 창 필드를 읽는 포트별 margin 최솟값으로 -- card IT-2, 41 §4.7-5, §3.8-8) | 41 §1.12.2-4·5, §2, 40 §3.8-8 | D-J2, D-J5 |
| U9 | 주경로 블록만 A_i,max. FF 상한을 더한 Σ 판정. `icmr_window_short_l_bin` 경고, `buffer_window_report` | 41 §4.3, §4.6 | D-J2, D-J5 |
| U13 | FF 묶음 출발값(G_ff = r_ff · gm_in(B_b), r_ff = 1) | 41 §6.5 | D-J2 |
| U15 | bin·조합·`gain_budget_db`는 주경로 블록만 | 41 §5.1 | D-J2 |
| U6 | 확인 항목: 보상 내부 루프 회로(ngcc·nmcnr)의 전체 PM 판정에 개루프 P = 0(`.pz`)이 들어가는지 | 41 §1.12.3, 40 §4 Q10 | D-J3 |

**웨이브 계획**(동시 6개 이하)

| 웨이브 | 단위 | 비고 |
|---|---|---|
| 1 | U1, U2, U3, U4, U5, U6 | 서로 소유 파일이 겹치지 않는다 |
| 2 | U1b, U7, U8, U9, U10, U11, U12 | 각 단위는 자기 선행 단위가 병합되는 대로 시작한다. U1b는 U1과 같은 `E/graph/` 파일을 고치므로 U1·U2 병합 뒤에 시작한다. U7·U9·U10은 블록 정의가 바뀌므로 U1b 인터페이스(41 §8, 주경로 블록·`feedforward_cells`)로 toy test를 쓰고, 실제 회로 test는 U1b 병합 뒤 켠다. 동시 6개 상한 때문에 U1b가 먼저 들어가고 U12가 한 칸 밀린다 |
| 3 | U13, U14 | -- |
| 4 | U15 | -- |
| 4' | U17 ①(U15 재구현 전), U17 ②(U15 재구현과 한 변경), U17 ③ | v1.6 graph 정본 개정. U15 재구현을 U17 ② 안에서 한다(G-9) |
| 5 | U16, 그 뒤 gap 분석(`42` 기준표 재측정) | J 공동분석은 J-A~J-F만 2026-10-08에 결정됐고(§9.3) 그 구현이 U1b다. 남은 J(§9.4)는 ratify 전이라 엔진 유도로 돌고, `review_needed`가 남는 회로는 GB4 전에 정지한다 |

**임계 경로**: U1 → U1b → U9 → U13 → U15 → U16. U9가 주경로 블록 정의를 읽으므로 U1b가 임계 경로에 들어간다. U1(SP1)이 가장 크므로, 하위 파일 단위로 나눠 같은 웨이브 안에서 순차로 커밋한다.
