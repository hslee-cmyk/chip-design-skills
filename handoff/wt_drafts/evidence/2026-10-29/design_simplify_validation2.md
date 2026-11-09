# design v1.15.2 2차 단순화 독립 검증 (`git diff fc874bd6 190e764c`, 커밋 10개)

- 2026-10-29, 독립 검증자(작성자 아님). 대상 worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115`, 대상 = 커밋 blob `fc874bd6..190e764c`(git은 `git -C`·`show`·`diff`·`grep`만, 작업 트리 파일은 읽지 않음). 주의: 검증 시작 때 HEAD 190e764c·작업 트리 깨끗이었으나, 끝날 때 HEAD가 `2e926daf`(13:21)로 바뀌고 40·41·42에 미커밋 수정(+81/−75줄, 13:44~13:46)이 생김 -- 다른 작성 주체의 병행 작업이며 이 검증 범위 밖(그 변경은 보지 않았다).
- 기준: 사용자 근본원칙(gm/ID 손계산 우선·손계산 오차 감수·DEC-72 model_error·최종 확정 SPICE; O-173 E-0 물리 관문·E-1 결정 불변·E-2 정밀화 조건; SPICE 수치 동일성은 기준 아님), O-169·O-153(덧댄 것·옛 본문 공존 금지), graph 단일 정본, 상수 발명 금지, design = 규칙·정의·인터페이스·완료 조건.
- 측정 자료(모두 `design_simplify_validation2/`): 커밋별 diff `commit_<h>.diff`; 판 사본 `40|41|42_<fc874bd6|09e5b13a|190e764c>.md`; `hunk_worddiff.py`(덩이별 낱말 diff) → `c028_41.worddiff.md`·`c_<h>.worddiff.md`; `moved_check2.py`·`.out.jsonl`(지운 구간 → 이력 파일 원문 대조); `hist_reverse_check.py`·`.out.json`(이력 H 절 → 옮기기 전 본문 역대조); `mech_check.py`·`mech_<h>.json`·`mech_dels_list.txt`(기계 정리 세 커밋 줄별 문자 diff·지운 조각 분류); `mech_sample.py`·`.out.md`(표본 48곳); `names_check.py`·`.out.jsonl`(status_only_names 48개 고유 이름 grep -- 계획·design·이력·엔진 master·integ/it12); `residual_scan.py`·`.out.json`·`.lines.jsonl`(남은 O-169 꼴·경위 단서); `section_sizes.py`·`.out.json`(절별 분량 전후); `principle_check.py`·`.out.json`(새 backtick 이름·fail-closed 단서·새 숫자·회로 이름); `failclosed_removed.out.md`(지운 fail-closed 문맥 24건); `r_table_check.out.txt`(40 §8 R 표 권고 열 대조); `status_to_42.out.txt`(옮긴 상태표 항목 ↔ 42 행); `internal_lineref.out.txt`(문서 안 줄 번호 참조).
- 구분: '실측' = 위 스크립트 출력, '판독' = 검증자가 문맥을 읽은 판단.

## 판정 요약

| 항목 | 결과 |
|---|---|
| Critical | 0 |
| Major | 2 (MJ-A 41 §4.7 옛 본문 잔존 -- 정본 표와 충돌, MJ-B `INPUT_STATUS_UNMEASURED`·`Window.input_status`·`tol_v` 삭제 대 cfg 사용 -- 계획 쪽 원인) |
| Minor | 6 (m-A~m-F) |
| 1. 09e5b13a 결함 정정 | MJ-1·MJ-2·m-1~m-7 **9건 모두 해소**(실측 낱말 diff + 판독) |
| 2. 뜻 보존 | 41 §4.7 일곱 자리 재작성: 규칙 누락·변경 0, 단 '`dc_window_cfg` 부분은 그대로' 구절 삭제로 '같은 `Window` 꼴' 문장이 MJ-B 모순을 키움. 기계 정리 표본 48곳: 뜻 변화 1(m-B, 'P1' 출처 번호 삭제). status_only 48개: 현행 규칙을 잃은 이름 0 |
| 3. 옮긴 원문 보존 | **100 %**(정방향: 지운 40자 이상 구간 160개 중 158 이력에 원문, 나머지 2 = 끝 '변경 이력' 절의 evidence 경로 교체 -- 본문 유지; 역방향: H40-01~29·H41-01~20 49절 원문 줄 전부 옮기기 전 본문에 그대로) |
| 4. 남은 과잉 | 40 −107.5 KB(추정 100~140 안), 41 −83.8 KB(추정 150~200의 절반) -- 41 §4.7(210 KB, 문서의 40 %)이 IT-2c 미구현 규칙이라 남은 것이 주원인. 멈춘 자리 판단 4개 중 3개 맞음, 1개(41 §4.7-8 (8)) 계획 판단 불요 |
| 5. 작성자 지적 모순 둘 | (가) 실제 모순, **계획 쪽 원인**(WB-1 범위 3 '지울 상태'·완료 조건 grep 0이 cfg 공유를 빼지 않음) + design 4.7-V 2행·40 §3.11-1이 그대로 옮기고 `tol_v`까지 넓힘 (나) 실제 끊긴 참조, **design 쪽**(계획 문언 '노드 풀이 블록의 마지막 풀이 = 봉인이 보는 점'은 E-13 뒤에도 성립) |
| 6. 원칙 | fail-closed 약화 0(지운 fail-closed 문맥 24건 = 폐지·대상 소멸·이력·구현 끝난 card), 새 필드·cache·상수·회로 이름 조건 0 |

## 1. 09e5b13a 결함 정정 확인 (실측 `wd_09e5b13a.txt`)

| ID | 정정 자리(190e764c 줄) | 판정 |
|---|---|---|
| MJ-1 | 40:1016 -- '차는 출발점 품질에만' 삭제, '구조 조건 밖(A–G 결합 용량 경로 없음)에서는 R_S = R_null(nmcnr T 망 R_m = 1/g_m3도 R_null)', 결합 경로면 'R_S > R_null이고 R_null이 §3.1-1 (b) 상자 밖일 수 있어 … 탐색 도달 범위를 바꿈' → fail-closed 근거 복원 | 해소. 물리: 과소평가된 Σgm → R_S = 1/Σgm > R_null = 1/G_m(∞), 상자 [1/max Σgm, 1/min Σgm] 밖 가능 -- moved_text S1의 절점식 결론과 같음. 내부 모순(출발점만 대 fail-closed) 없음 |
| MJ-2 | 40:1016 '출발값과 MNA의 차 = `comp_approx_gap` -- DEC-92 (2)'; 40:2230 원칙 요약도 같은 정정 | 해소(기록 자리 하나, graph 규칙 1·3 맞음) |
| m-1 | 40:1012 'S 셀 집합' 제목 인용, 42:352 D-PW·42:355 D-CAB 갱신 | 해소 |
| m-2 | 40:1182, 41:1440 '동작 변경 -- 새로 거부되는 점' 복원 | 해소 |
| m-3 | 40:865 '계획 결정 뒤 그 후보의 toy만 card SF-1 완료 조건 …(새 상수·칸 0)' | 해소 |
| m-4 | 40:1016 '(구동 쪽 끝 A, 출력 쪽 끝 B) … MOS(gate = A, drain = B)' | 해소 |
| m-5 | 41:1448 (i) P8 등록·출처 `handcalc_principle_audit.md`:31·112, 40:1156 출처 | 해소(0.54~1.74는 출처 있는 측정값 -- 상수 아님) |
| m-6 | 41:1446 '계획 승인 표지가 있는 항목은 … 세지 않음' 복원 | 해소 |
| m-7 | 40:1621 '폐지된 옛 생략 예외 `cm_reference_undetermined`와 다른 이름' | 해소(계획 :304가 'v1.15.1 생략 예외는 이 규칙으로 대체'라 '폐지된' 맞음) |

## 2. 뜻 보존

### 2.1 41 §4.7 재작성(028bea62) -- 덩이별 대조(실측 `c028_41.worddiff.md`, 이력 H41-02~08 원문)

| 옛 자리 | 새 정본 문장 | 옛 규칙 대비 | 판정 |
|---|---|---|---|
| 4.7-1 4 다중 입력 뿌리 정지 | '4.7-V 1행이 정본(DEC-106 입력 점, 그 밖 다중 입력 = 탐색 전 정지 `input_cm_undefined`)' | 옛 `input_port_multiple_roots` 정지는 DEC-106이 대체(승인 O-168). '탐색 전'·`unsupported_rule_branch` 4.7-V 1행에 있음. `domain.ties`·뿌리별 포화 창 미구현은 4.7-3 3에 남음 | 보존 |
| 4.7-2 `node.dc_window` 행 | 'θ y 범위 = KVL 순서 창(4.7-V 2행 … θ 고정, DEC-103; 상태 칸 없음). 항목 = W4 뿌리만(입력 점 뿌리 포함 -- O-109 D1·DEC-106)' | 옛 '포화 판정 여유 창·선형 감도 끝·상태 칸 출력 전용'은 E-13(승인 표 #34)이 대체. 4.7-V 2행과 같음 | 보존 |
| 4.7-2 값 형식 | '`node.dc_window` = `Window(lo, hi, constraints)`(상태 칸 없음)' + cfg 문장 그대로 | 옛 커널 상태 어휘·커널 tol 문언 삭제는 E-13대로. **단 옛 표지의 '`dc_window_cfg` 부분은 그대로'가 빠지고 'cfg는 같은 `Window` 꼴'이 남아, 상태 칸 없는 꼴과 cfg `input_status`·`tol_v`(예시 `Window(0.33, 1.18, 0, input_status="measured", tol_v=1.2e-4)`)가 한 문단에서 어긋남** → MJ-B | 규칙 보존, 문언 모순 |
| 4.7-2 예시 | 커널 `Window(0.31, 1.12, 2)` | 4.7-V 2행과 같음 | 보존 |
| 4.7-3 1 뿌리 | 'KVL 순서 창(되풀이·`k_max`·`_interior_solution`·상태 칸 없음) … 포화 밖 점은 봉인 7이 거부' + O-109 D2 문장 유지 | 옛 A6 되풀이·판정 tol·A6 b 도달 조건은 E-13 대체. 거부 경로(봉인 7)는 4.7-V 2행 문장 그대로 | 보존 |
| 4.7-3 4 측정 실패 | '커널 쪽 대상 없음. cfg 자기 측정 실패는 4.7-3b `"unmeasured"` → metric 정의 불능(N3.14). DE-1 나머지는 DE-1 몫' | 커널 쪽 fail-closed 대상 소멸(순서 창은 레일 범위로 늘 정의), cfg 쪽 fail-closed 그대로 | 보존 |
| 4.7-3 5 `tol_v` | '(삭제 -- 칸 없음 …)' | E-13대로 | 보존 |

그 밖 028bea62 이동분(4.7-1a 취소선 본문 H41-09, 옛 S-1~S-3 H41-10, 4.7-4 모듈 이름·5 줄별 문언 H41-11·12, 4.7-9 D1~D6·옛 멈춤·후속 정정 H41-13~15): 남은 문장이 같은 규칙을 담음(4.7-4 5는 '배선 만들지 않음·front 값 = 커널 스냅샷 `metrics_aux`·운반자 `snapshot_ref`·graph reuse·S3 graft뿐·블록 계수 행'이 그대로; 빠진 것은 as-built `entry["res"]` 설명과 파일 이름 `front_windows.py` -- 뜻 무관).

**재작성 범위가 표 자신의 '옛 자리' 목록보다 좁다**(판독): 4.7-V 1행 옛 자리 = '4.7-1 2·4·4.7-1 test interface (d)', 2행 = '… 4.7-7 L12 (a)'. 028bea62는 4.7-1 4만 바꿨고 4.7-1 2·5·test interface (d)와 L12 (a) 본문은 그대로다 → MJ-A.

### 2.2 기계 정리(4e31a88b·e3dc6585·ad63532e) -- 실측 `mech_check.py`

| 커밋 | 바뀐 줄 | 지운 조각 | 넣은 문자 | 분류 밖 조각 |
|---|---|---|---|---|
| 4e31a88b | 150 | 275(전부 `:줄` 꼴) | 0 | 0 |
| e3dc6585 | 240 | 295(판 표지) | 0 | 3(difflib 정렬 조각 -- 줄 확인 결과 판 표지 `(v1.9.4, ` 등) |
| ad63532e | 41 | 52(검증 번호) | 0 | 0 |

표본 48곳(커밋당 16, seed 20261029 -- `mech_sample.out.md`) 판독: 규칙 문장 뜻 변화 **1곳**(m-B). 나머지 47곳은 괄호 머리 판 표지·검증 회차 번호·as-built 줄 번호만 빠지고 규칙·조건·이름·출처 결정 번호는 그대로. 관찰: 40:658처럼 앞 인용의 줄만 지워 뒤 `:41`·`:49`가 파일 없이 남은 곳이 있음(뜻은 같은 파일로 읽힘 -- 무해).

### 2.3 status_only_names.txt(23 + 30 = 53, 고유 48) -- 실측 `names_check.out.jsonl`

| 판정 | 이름 |
|---|---|
| 폐지·대체 확인(계획·design 본문에서 대체 규칙 있음) | `..._source_unsupported`·`icm_config_feedback_source_unsupported`(→ `_element_unsupported`, 그 뒤 servo O-115로 갈래 소멸), `high_impedance`·`kvl_fixed`·`w3_target`·`IcmConfig.output_structure`(출력 구조 분류 O-109 D4 폐지 -- integ/it12 엔진엔 남아 IT-2c가 지움), `input_status="op_mismatch"`(본문엔 `"op_mismatch"`로 EO-1 예약 이름 유지), `(lo, hi, constraints, input_status=None, tol_v=None)`(E-13), `INPUT_STATUS_*`(→ MJ-B), `IcmConfig.transfer`·`IcmWindow.config`·`saturation_window(…, roots, …)`·`fixed_values[p]`·`input_window_unsettled`·`metrics_aux._ss_of`·`ss_circuit_of(…)`·`_dc_feedback_reaches(…)`·`device.element_class == ELEMENT_MOS`·`element_class == ELEMENT_SOURCE and kind == CURRENT_SOURCE`·`input_terminal_nets`·`__code__`(L10 (a) 삭제), `STAGE_B_WRITERS`·`disk_hits`(S0 디스크 폐지), `block_columns.k_max`(E-13) |
| 구현 끝난 card 기록(현행 규칙 아님) | `DeviceView`·`device_views`·`_Device`·`(DEVICE, F_DEVICE)`(XRUN-F1 A), `co_filename`(code_hash card 완료), `lu_factor`(NFR-4 측정), `noise_input_cells`·`block_index_bound`·`donors.find_failure`·`MOS_TERMINAL_NAMES`·`composite_diode._walk`·`graph.dc_segments`·`dc_resistor_cycle`·`def _feedback`·`DC_CONDUCTING_PASSIVE_KINDS`(판 경위 속 인용) |
| 일반 낱말·조각(이름 아님) | `"elements"`·`elements`·`slope`·`_canon`·`B, IT-2e`·`(config, pivot_a_e, …)`·`IcmPort.missing`(본문엔 `IcmPort(…, missing)`로 현행) ·첫 줄 조각 |

현행 규칙을 Status에만 두고 있던 이름 **0**. 참고: 작성자 목록의 '지금 본문에 없음'은 backtick 꼴 기준이고, 낱말 꼴로는 `_canon`·`slope`·`elements` 등이 본문에 있다(무해).

## 3. 옮긴 원문 보존 (실측)

- 정방향(`moved_check2.out.jsonl`): 028bea62·7e57ee63·c7a51e41·2d84ffbb·ca5e8557·190e764c에서 지운 40자 이상 낱말 구간 160개 -- 158개가 이력 파일에 공백 정규화 원문 그대로. 못 찾은 2개 = 190e764c가 40 끝 '변경 이력' 절의 evidence 경로 문장을 새 문장으로 바꾼 것(경로는 새 문장에 그대로 있음 -- 원문 보존 대상 아님).
- 역방향(`hist_reverse_check.out.json`): H40-01~29·H41-01~20 49절, 40자 이상 원문 줄 292줄 전부 옮기기 전 본문(부모 커밋 40·41·42)에 그대로 -- 이력에서 문언을 고친 곳 0.
- 40 §8 R 표(2d84ffbb, `r_table_check.out.txt`): R1~R33 33행 모두 '축소 내용'·'처리(권고)' 열이 옛 표와 글자 같음.
- 기계 정리 세 커밋은 이력이 아니라 evidence jsonl 목록(`strip_*.out.jsonl`)과 git diff가 원문 -- 4e31a88b 275곳 수가 실측과 같음.

## 4. 남은 과잉

### 4.1 분량(실측 `section_sizes.out.json`)

| 문서 | 09e5b13a | 190e764c | 차 | 1차 검증 추정 과잉 |
|---|---|---|---|---|
| 40 | 698.8 KB | 591.3 KB | −107.5 KB | 100~140 KB |
| 41 | 611.1 KB | 527.3 KB | −83.8 KB | 150~200 KB |
| 42 | 96.1 KB | 95.7 KB | −0.4 KB | -- |

**41이 덜 준 이유**(실측 + 판독): §4.7이 210 KB(41의 40 %)이고 재작성은 4.7-V '대체' 일곱 자리(−31 KB)뿐이다. 남은 몫 4.7-3b 44 KB·4.7-7 42 KB·4.7-5 18 KB·4.7-3c 16 KB·4.7-3a 16 KB·4.7-9 14 KB는 **IT-2c 미구현 규칙**(integ/it12에 cfg 상수·`icm_config` 없음 -- 엔진 grep)이라 옮길 수 없다. 그 안의 경위 단서(§4.7 안 판 표지 112·커밋 해시 29·검증 번호 39·`.py:줄` 108)는 문장 속이라 괄호 머리만 지운 기계 정리가 닿지 않았다. 1차 추정(60~90 KB)은 이 미구현 규칙 몫을 과대 계산했다.

### 4.2 멈춘 자리 판단

| 자리 | 작성자 판단 | 검증 판정 |
|---|---|---|
| 40 §4 C10·Nyquist | oracle-portability design이 정본을 40 §4로 지정 -- 옮기면 정본 소실 | **맞음**(실측: `oracle-portability.design.md:629` '창 판정 규칙의 정본은 계약 문서와 design 40 §4') |
| 41 §7.2·§7.6·§6.4-2 | 받을 문서에 같은 내용 없음, 측정 문장 하나만 옮김 | **맞음**. §7.6(1.2 KB)은 오라클 벤치 규칙, §6.4 1606 '단위 확인'은 완료 단계 규칙. 단 41:1616 '한계 기록(제안서 실측 W 5 µm …)'은 측정 경위라 옮길 수 있음 |
| 40 §3.1·§3.6·§3.7·§6 상태표 | 설계 문장이 섞여 유지 | **맞음**(행 단위 분리가 필요 -- 다음 판 몫) |
| 41 §4.7-8 (8) 커널 y 끝 | E-13 뒤 유효 범위 불확실 -- 계획 판단 | **계획 판단 불요**(판독, 확신 중): (8)은 IT-2b(병합됨) 변경 종류 기록이고 대상인 'A6 선형 끝'은 4.7-V 2행이 이미 대체했다. 순서 창 끝점의 봉인 7 거부는 40 §3.11-1 ⚠ P4·E-13 재상정 기준이 다룬다. (9)처럼 이력으로 옮기고 한 줄 지시면 된다. 같은 이유로 4.7-8 (11) 'O-61 P5 커널 창 미수렴 표시 = 동작 변경, card 0이 발동률 잰다'도 대상 소멸인데 표지 없이 남음(4.7-8a 표 787은 '대상 소멸' 표지) |
| 경위 괄호 나머지 | 문장 속이라 하나씩 판단 | 맞음. 남은 수(실측): 판 표지 40 = 238·41 = 224·42 = 109, 커밋 해시 40 = 27·41 = 39·42 = 21 |

### 4.3 추가로 줄일 목록(우선순위)

1. **MJ-A 해소 = 41 §4.7·§6.7·§9의 O-169 잔여 재작성**: 4.7-1 2(뿌리 규칙·y 키 → DEC-106 입력 점 키), 4.7-1 5(`_solve_input_window`·`_interior_solution`·'4의 둘 이상이면 정지'), 4.7-1 test interface (d), 4.7-3a 3 판정 점(m-A), 4.7-7 L12 (a) 본문(5.9 KB 줄 -- '대상 소멸' 표지 뒤 옛 (a) 전문), 4.7-8 (8)·(11), §6.7-1a 41:1724 옛 '개정' 항목(다음 항목이 대체), §9 41:2014 행(옛 단언 + 'v1.15.2 대체' 덧댐).
2. **40 §11 구현 단위 표**(42 KB, 판 표지 48): 40:2180(7.9 KB)·2181(5.5 KB) 행 안 완료 card 상태 기록('결정 10 code_hash card(상태: 완료(af10c9b, 판정 ecda471 …)' 등)·v1.9~v1.11 경위.
3. **40 §2.4.8 소유표**(46 KB, 문장 속 판 표지 42)·**§2.4.13**(46.6 KB, 측정 단서 35 -- NFR-4 card 끝남; 규칙 (2)~(5)만 남기고 측정 문장 이관)·**41 §5.13**(측정 단서 13).
4. **42 머리 4.6 KB + §4 상태 집계 판별 이력 약 10 KB**(v1.10~v1.15.2) -- 40·41 머리처럼 이력 파일로.
5. **머리 낡은 메타**: 40 'Planning Doc … v6.11', 40·41 'as-built 기준 master `004b7d2`'·옛 브랜치 목록.
6. **4.7-0 as-built 사실 표**(3.7 KB, master `9401e98f` 줄 번호) → 42·evidence(O-153).
7. 문서 안 줄 번호 참조 정정(m-D).

## 5. 작성자 지적 모순 둘

### 5.1 (가) 4.7-V `INPUT_STATUS_UNMEASURED` 삭제 대 cfg `"unmeasured"` 사용 -- **실제 모순, 원인 = 계획**

- 사실(실측):
  - 계획 :2292 WB-1 범위 3 '지울 상태 = 상수 `INPUT_STATUS_UNMEASURED`·`INPUT_STATUS_UNSETTLED`(`E/sizing/s2_values.py:117-118`)와 `Window.input_status` 값 집합(`:362-368`)', 완료 조건 :2347 '측정 창 경로 grep 0(상수 `INPUT_STATUS_UNMEASURED`·…) -- `search/*`의 `unmeasured`만 대상 아님'.
  - 같은 계획 :1639 IT-2c 완료 조건은 'cfg 항목의 `tol_v`'를 쓴다.
  - design 41 4.7-2(41:671) cfg `input_status` ∈ {`"measured"`, `"unmeasured"`}·cfg `tol_v`·예시 `Window(0.33, 1.18, 0, input_status="measured", tol_v=1.2e-4)`; 41 4.7-4(41:730·759)·40:1935·40:2180 `sizing.__all__`에 `INPUT_STATUS_UNMEASURED` 공개.
  - design 4.7-V 2행(41:630)·40:1457 '계획 WB-1 범위 3 지울 상태 그대로'로 같은 상수 삭제, 4.7-V는 `tol_v` 칸까지 삭제 대상에 넣음(계획 문언엔 `tol_v` 없음).
  - 엔진: master엔 `INPUT_STATUS_*` 없음, integ/it12(IT-2b)엔 커널 쪽만 있음(`block_columns.py:66-67·755-796`), cfg(IT-2c)는 미구현(card/it2c 동결만).
- 판정: 계획의 삭제 목록이 IT-2b as-built(커널 상태만 있던 때)를 보고 쓰여 IT-2c cfg가 같은 상수·같은 `Window` 칸을 쓴다는 design 결정(v1.13.0·v1.14.1)을 빼지 않았다. design은 그 목록을 옮기면서 모순을 품었고, 028bea62가 옛 표지의 '`dc_window_cfg` 부분은 그대로'를 지워 4.7-2 한 문단 안에서 '상태 칸 없는 `Window`' = 'cfg와 같은 `Window` 꼴'로 모순이 드러났다. WB-1 3a 구현자가 grep 0을 지키면 IT-2c가 쓸 이름·칸을 지운다(순서에 따라 지웠다 되살리는 변경).
- 권고(계획 v6.38.4 새 P 항목 -- design 혼자 못 고침, 계획 먼저):

| 안 | 내용 | 물리 정합 | 손계산·단순성 | graph 규칙 |
|---|---|---|---|---|
| **A(권고)** | 지울 상태 = 커널 쪽(`node.dc_window`) 상태 쓰기·`INPUT_STATUS_UNSETTLED`·커널 tol; `INPUT_STATUS_MEASURED`·`INPUT_STATUS_UNMEASURED`·`Window.input_status`·`Window.tol_v`는 cfg(`icm_config`) 전용으로 남김, grep 0 범위 = `sizing/block_columns.py` 커널 경로(cfg 경로·`sizing.__all__` 제외), WB-1 3a 대 IT-2c 순서 문언 | 무관(이름·자료 꼴) | 변경 최소 | E-13 뒤 상태 생산자는 `icm_config` 하나 -- 같은 이름 두 뜻 없음 |
| B | cfg 전용 새 타입(`CfgWindow` 등)으로 가르고 계획 목록 그대로 | 무관 | 새 타입·IT-2c design 재개정 | 규칙 위반 없음, 변경 큼 |
- design 쪽 즉시 정정(계획 결정 뒤): 4.7-V 2행·40 §3.11-1 '지우는 것' 문언, 4.7-2 값 형식 '같은 `Window` 꼴' 문장.

### 5.2 (나) 41 §4.7-3a 3 끊긴 참조 -- **실제, design 쪽**

- 41:694 '판정 점 = 커널 마지막 풀이 … **4.7-3 1의 마지막 `override` 풀이 해**' -- 4.7-3 1은 이제 '되풀이·`override` 없음'(4.7-V 2행). 계획 :1589 원문은 '노드 풀이 블록의 마지막 풀이 = 봉인이 보는 점'으로 E-13 뒤(한 번 풀이)에도 그대로 성립 → 계획 정정 불요.
- 고칠 꼴: '노드 풀이 블록이 그 평가의 θ y로 푼 해(4.7-3 1 -- 봉인이 보는 점)'. 같은 꼴의 끊긴 참조: 4.7-1 5(`_interior_solution`), 4.7-7 L12 (a) 본문(MJ-A).

## 6. 결함 표

| ID | 등급 | 자리 | 요지 | 처리 권고 |
|---|---|---|---|---|
| MJ-A | Major | 41 §4.7-1 2·5·test interface (d), 4.7-3a 3, 4.7-7 L12 (a), 4.7-8 (8)·(11), §6.7-1a 41:1724, §9 41:2014 | 4.7-V 정본과 옛 본문 공존(O-169). test interface (d)는 4.7-V가 지운 `input_port_multiple_roots` 정지를 단언하고, 4.7-1 2의 뿌리·y 키 규칙((구조 색, 이름) 최소 뿌리, 키 = 뿌리 넷)은 DEC-106 키 `(y, <differential_input_p 넷>)`와 어긋남. 028bea62 이전부터 있던 것이나 재작성이 표 자신의 옛 자리 목록보다 좁게 끝남 | 위 자리 정본 문장으로 재작성, 옛 문언 이력 이동(4.3 목록 1) |
| MJ-B | Major | 41:630·671·730·759, 40:1457·1935·2180; 계획 :2292·:2347 | 커널 상태 삭제 목록이 cfg 공유 상수·`Window` 칸까지 지움 -- 구현 순서에 따라 IT-2c 깨짐. 원인 계획 | 5.1 안 A로 계획 v6.38.4 P 항목, 뒤 design 정정 |
| m-A | Minor | 41:694 | 끊긴 참조 '4.7-3 1의 마지막 `override` 풀이 해' | 5.2 꼴 |
| m-B | Minor | 41:1448 (e) | ad63532e가 '-- 검증 M-3, P1'을 통째로 지워 계획 정정 후보 (e)의 P1 표지 소실(커밋 문언 '출처 번호 유지'와 다름) | '(… `constraint_classes.judged`, P1)'로 복원 |
| m-C | Minor | 40 §3.4·§3.5·§3.8·§4 '42가 정본' 문장 | 옮긴 상태표 항목 중 42에 대응 행이 없는 것: U-12 단일단 gm_1 규칙(MISS), `pm_cm_ss_deg`가 `ORACLE_MEASURES`에 없음, `op_point` FC 위반 칸 사유 기록 없음(PART) -- 실측 `status_to_42.out.txt` | 42에 행 추가 또는 그 셋을 40에 한 줄씩 |
| m-D | Minor | 40 '41 §4.7-3b 744'·'§4.7-4 760'(×2), 41 '4.7-5 793'(×3)·'4.7-5 789'·'4.7-5 785'·'4.7-3c 757'·'(757)'·'4.7-1a 719'·'4.7-3b 744'·'§5.1 861', 42 '§3.8-3 1248'·'§3.8-6 1256'·'D42:200' | 문서 안 줄 번호 참조가 −190 KB 이동으로 엉뚱한 줄을 가리킴(전부터 있던 꼴, 이번에 더 어긋남) | 절·항 번호 참조로 |
| m-E | Minor | 41 4.7-9 → H41-15 | 다른 문서 후속 정정 목록(headroom-chain HC-S 이름, 계획 F-DE5·F-I2 줄 인용)이 미결일 수 있는데 이력으로만 감 -- 계획 :1682 F-DE5는 아직 옛 경로 인용 | 미결 항목은 41 4.7-9에 한 줄 남기거나 계획 정정 후보로 |
| m-F | Minor | 40 머리 'Planning Doc … v6.11', 40·41 'as-built 기준 master `004b7d2`'·옛 브랜치 | 낡은 메타 | 현재 판·as-built 기준으로 |

## 7. 원칙 점검(실측 `principle_check.out.json`, `failclosed_removed.out.md`)

| 항목 | 결과 | 구분 |
|---|---|---|
| fail-closed 약화 | 0. 단서 수는 40 fail-closed 84 → 73·41 45 → 33으로 줄었으나 지운 24건 = 폐지된 A6 c·S-OS1·S-OS2(O-109·O-115), 판 이력 Status, 구현 끝난 card test 목록, v1.5 처리표('유지(§5.4·§5.6)' -- 규칙은 그 절에 있음). 현행 거부 경로(봉인 7, cfg `"unmeasured"` → 정의 불능, `input_cm_undefined`, `zero_cancel_s_coupled`, `finger_below_min`, `slice_cycle`, `cm_reference_unclassified`) 모두 본문에 있음 | 실측 + 판독 |
| 새 graph 필드·cache·memo·사본 | 0(새 backtick = 줄 번호 뗀 파일 경로·이력·evidence 경로·예시 리터럴 `Window(0.31, 1.12, 2)`) | 실측 |
| 상수 발명 | 0(새 숫자 '0.54' = 출처 있는 측정값, m-5 정정) | 실측 |
| 회로 이름 조건 | 0(회로 이름 출현 수 증가 0) | 실측 |
| E-0·E-1·E-2(O-173) | 규칙·결정 변경 없음(E-1 지킴). MJ-1 정정은 물리 정합 회복(R_null 상자 밖 → fail-closed) | 판독 |
| 이 검증의 문서 수정 | 0(git `show`·`diff`·`grep`·`log`만, reset·checkout·stash·commit 없음) | 실측 |
| 한계 | 분류 스크립트는 패턴·낱말 기준 -- 뜻 판정은 표본 판독; 표본 밖 기계 정리 조각은 패턴 일치·삽입 0으로만 확인 | -- |
