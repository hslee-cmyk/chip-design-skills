# QB 재측정 v3 -- 손가락 슬라이스 선택 규칙 R0~R3 (O-173 Q-P8 / 계획 DEC-105 (2) P:305, 상정 C1 (A))

작성 2026-11-07, 측정 agent(문서·분석). **권고 없음** -- 사실과 비교만 적는다(사용자 질문 '권고 없는 선택지'의 근거 자료).
대상 엔진 = master `faf69218`(WB-1 + LM-1e 병합본: tol_V mV 급 -- 비기준 슬라이스 중점 적재·봉인 10행 가드, W_min = PDK 선언 하나). 비교 기준 = v2(`wt/_drafts/evidence/2026-11-06/wb1_qa_qb_recommendation.md` '# 개정 v2' V2-2, WB-1 `607600d1` 사본).
원칙 8 용도 제한: 엔진 인용은 (1) 엔진 밖 사실(LUT 값·PDK 값) (2) 재작성 범위로만 쓴다. as-built 동작을 규칙의 근거로 쓰지 않는다.
O-229 아래: 엔진 수정 0, 커밋 0, pytest 0, ngspice 0, 새 도구 0(v2 스크립트 복사본만 실행, 복사본 수정은 아래 0.2).

## 0. 돌린 것

### 0.1 환경·명령

- 측정 worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261107-qb-measure`(`git worktree add --detach … master` = faf69218). 측정 뒤 추적 파일 변경 0 확인 후 제거.
- 스크립트 복사본: `C:/Users/HSLEE/AppData/Local/Temp/la1s_qb3/scripts/`(원본 `…/la1s_wb1_rec13/scripts/` 미수정). 출력 `C:/Users/HSLEE/AppData/Local/Temp/la1s_qb3/out/`(케이스마다 append).
- 실행: `OPENBLAS_NUM_THREADS=1 PYTHONIOENCODING=utf-8 C:\Python314\python.exe -P <script> <worktree> <out> [<회로>]`. 회로마다 별도 프로세스로 하나씩 순서대로(`la1s_qb3/run_seq.py` -- 착수 전 여유 < 3.7 GB면 10 s sleep 대기, 실행 중 < 1 GB면 그 자식 PID만 정지; 실측 여유 5.1~5.3 GB, 대기·정지 0회, 회로당 12~39 s).

| # | 스크립트(복사본) | 출력 | 내용(v2와 같음) |
|---|---|---|---|
| S7 | `qb2_rules_realize.py` | `out/qb2_rules_realize.txt` (+ `.runlog`) | 규칙 R0~R3 각각 탐색 평가 → 그 (m, w_s)로 실현 평가(`evaluate(..., realized=RealizedFinger(...))`, W′·바이어스 고정 KCL 재풀이 + 봉인 전 항목) |
| S8 | `qb2_summary.py` | `out/qb2_summary.txt` | S7 요약 |
| S4 | `qb_slice_rules.py` | `out/qb_slice_rules.txt` | 소자별 후보, 연결로 판정한 정합 쌍, 두 슬라이스 gm/ID, 손가락 수 분포, gbw 행 |
| S5 | `qb_pairs_consistent.py` | `out/qb_pairs_consistent.txt` | 쓰기-종속 같은 전류 쌍 R1 일관 추정 m |
| S9 | `qb2_probe_kcl.py` | `out/qb2_probe_kcl.txt` | two_stage_ota HS, R0·R1 실현 스냅샷 노드 이동·MOS 전류만의 노드 KCL 합 |
| S6 | `qb2_probe_domain.py` | `out/qb2_probe_domain.txt` | 못 잰 회로 사유 |

### 0.2 복사본에서 바꾼 것 (각 파일 머리에 적음)

1. 모든 복사본: 임시 폴더 `dir=`를 `la1s_wb1_rec13` → `la1s_qb3`(출력 격리).
2. 엔진 API 이름 맞춤: **없음**. 스크립트가 부르는 이름 전부(`generality.pipeline` Env·Pipe·map_cells·map_theta·LIBRARY, `search.evaluate(realized=)`, `core.fp_of`·`CANDIDATE_FAILURE_CLASSES`, `sizing.RealizedFinger`·`is_servo_branch`, `sizing.block_dc.finger_slice`·`_Circuit.pick_writer`·`pick_dependent`, `lut.finger_slice` FingerSlice·reachable_slices·_finger_count, `lut.op_point`, `LutSpec.min_finger_w_m`·`manufacturing_grid_m`)를 `git diff 607600d1 faf69218`로 대조 -- 바뀐 것 0. 바뀐 것은 값뿐: 하네스 `Env`가 `min_finger_w_m`을 PDK 선언에서 채움(S4 `SPEC_MIN_FINGER` nmos·pmos 4.2e-7 m = `PDK_DECL_min_finger` 4.2e-7 m), tol_V 셀(LM-1e).
3. `qb2_rules_realize.py`만: ALT 대체 점(층 0 출발점이 없는 회로)에 θ의 L 성분(`THETA_L`)을 칸 안 값(1.75 µm, 칸 밖이면 칸 중앙)으로 채움. v2 ALT 점은 L 성분을 빠뜨려 current_reuse(`expand_ties` 대표 없음)·sf_pushpull(`check_theta` 빠짐)에서 평가 전에 실패했다(v2 '대체 점 구성의 결함'). 규칙 정의·지표는 그대로.

## 1. 측정 범위: **7/13 회로**(v2와 같은 7), 8점 76소자(층 0 69 + HS 7)

측정: common_gate_amplifier, folded_cascode, ngcc_3stage_ff, nmcnr_amplifier, pushpull_follower_buffer, two_stage_ota(층 0 + 손 봉인 HS), two_stage_ota_sf. 층 0 점은 전류 하한 근처 퇴화 점(ID ~1e-10~1e-14 A, W 수 cm)이고 대표점은 HS 하나(ID ~1e-5 A) -- v2와 같다.

못 잰 6회로(S6·S7 원문):

| 회로 | 사유 v3 | v2 대비 |
|---|---|---|
| cnr_ota | 엔진 구조 미지원 `StructureUnresolvedError`(`writer_plan.py:211`, `dc_resistor_cycle`, nets VCR·VDD_1V8) | 같음 |
| erfc_ota | 엔진 구조 미지원(`current_basis.py:134`, `mos_zero_current_structural`, M19·M20·M21) | 같음 |
| current_reuse_telescopic_ota | 층 0 출발점 없음(`start_lut_query_failed+probe_eval_budget`, M3a tol_v 셀 VDS −0.63 V 축 밖). ALT 점(L 성분 보강 뒤)은 `outside_domain`(4규칙 모두) | ALT 실패 사유가 θ 구성 오류 → `outside_domain`으로 바뀜 |
| r2r_opamp | 층 0 출발점 없음(`start_lut_query_failed+probe_eval_budget`, M26 `lut_curve_undefined`). ALT `outside_domain` | 같음 |
| rfc_ota | 층 0 출발점 없음, 정지 사유 **`start_tol_v_undefined+probe_eval_budget`**. ALT `outside_domain` | 정지 사유 바뀜(v2 `start_lut_query_failed`) -- LM-1e 봉인 10행 가드가 출발 단계에서 걸림(사실 기록, 원인 분해 안 함) |
| sf_pushpull_output_opamp | 층 0 출발점 없음, 정지 사유 **`start_tol_v_undefined+probe_eval_budget`**. ALT 점은 이제 평가까지 가지만 4규칙 모두 탐색 평가 봉인 7 실패(M21, `no_root_in_window` 꼴 item 7) -- 손가락 비교 불가 | 사유 바뀜(v2 θ 구성 오류) |

S4(`qb_slice_rules.py`)는 6회로(two_stage_ota_sf는 이 스크립트에 사례 폴더 spec 복사가 없어 `ref_unresolved` -- v2와 같은 하네스 한계, S7은 복사로 잼).

## 2. 규칙 (v2 V2-0 정의 그대로)

- **R0** 현행 `finger_slice`: |m·w_s/W(s) − 1| 최소, 같으면 큰 w_s(C1 (A), P:305).
- **R1** 넓은 우선: 도달 슬라이스를 큰 폭부터, W(s) ≥ w_s인 첫 슬라이스, m = W(s)/w_s 최근접 정수; 없으면 가장 작은 도달 슬라이스 m = 1.
- **R2** 같은 W bin 안 잔차 최소(m0 = ⌈W/w_hi⌉의 w_c가 든 bin).
- **R3** 연결 묶음 공유(미러 꼴 = 같은 kind·gate·source 넷·L, 차동 꼴 = 같은 kind·source 넷·L이고 gate가 서로 다른 입력 포트 넷; 태그·device_roles 0 -- 원칙 14). 묶음 쓰기 소자의 R0 키를 공유.

## 3. 결과

### 3.1 잔차·손가락 수 (S8, 탐색 평가 `dc_finger.residual`)

| 규칙 | 76소자 max \|r\| | p50 | p90 | p99 | m ≤ 3 | HS max \|r\| | HS 최대 m | HS m 목록 | v2 대비 변화 |
|---|---|---|---|---|---|---|---|---|---|
| R0 | 4.6e-3 | 4.1e-4 | 1.9e-3 | 4.2e-3 | 0/76 | 5.7e-4 | 299 | [13, 13, 13, 26, 63, 267, 299] | p50 1.8e-4 → 4.1e-4, p90 1.4e-3 → 1.9e-3(좁은 키 72·78 제외 효과). HS M1 키 84 m 88 → **키 128 m 63** |
| R1 | 0.250(pushpull M4, m = 1) | 3.8e-3 | 6.6e-2 | 0.128 | 12/76(전부 층 0) | 2.6e-2 | 33 | [7, 8, 8, 9, 16, 28, 33] | **변화 0**(모든 소자 키 1000 -- 기준 폭 tol은 v2에서도 mV 급) |
| R2 | R1과 같음(8점 전부 같은 선택) | | | | 12/76 | 2.6e-2 | 33 | 같음 | 변화 0 |
| R3 | 0.117 | 4.1e-4 | 7.1e-3 | 0.106 | 1/76 | 9.6e-3 | 299 | [13, 13, 61, 63, 78, 163, 299](S4) | p90 4.6e-3 → 7.1e-3, HS max 8.6e-3 → 9.6e-3 |

층 0 최대 m: R0 1,572,439, R1 27,764(S8) -- 퇴화 점이라 두 규칙 모두 크기 의미 없음(v2와 같은 결론).

### 3.2 W_min 아래 손가락 (S7 DEV `w_key` 최소)

| 규칙 | 최소 키(폭) | W_min(PDK 선언 0.42 µm) 아래 소자 | v2 대비 |
|---|---|---|---|
| R0 | 84 (0.42 µm, folded M11 등) | **0/76** | v2 7소자(키 78 = 0.39 µm, two_stage_ota·_sf M2·M5, nmcnr 5소자) → 0 |
| R1·R2 | 1000 (5 µm) | 0/76 | 같음 |
| R3 | 84 (0.42 µm) | 0/76 | v2 R3도 R0 키를 공유해 키 78 포함 → 0 |

### 3.3 정합 묶음 같은 W bin (연결만, 원칙 14)

| 규칙 | S7 묶음 23(8점) | S4 쌍 24(6회로 L0 21 + HS 3) | HS 묶음 3 | v2 대비 |
|---|---|---|---|---|
| R0 | **3/23**(folded M10/M9, folded M1/M2, HS M3/M4) | 3/24 | 1/3(M3/M4; M5/M7 키 600/120, M1/M2 키 128/600 갈림) | S7 3/23 같음, S4 4/24 → 3/24 |
| R1 = R2 | 23/23 | 24/24 | 3/3 | 같음 |
| R3 | 23/23(정의상) | 24/24 | 3/3 | 같음 |

### 3.4 실현 전류 비 오차 (S7 GRP, 실현 비/θ 비 − 1)

| 규칙 | 같은 전류 쌍 max (n) | 비 다른 미러 max (n) | HS 같은 전류 / 미러 M5/M7 | v2 대비 |
|---|---|---|---|---|
| R0 | 0.48 %(15; ngcc M6A/M7) | **366 %**(12; nmcnr '차동 꼴' M102/M103 -- θ 전류 비 0.0115인 비정합 쌍, 아래 3.6). 그 쌍 제외 max 0.34 %(ngcc M1/M2) | 0.11 % / 0.04 % | 같은 전류 0.45 → 0.48 %. 미러 0.15 % → 366 %(nmcnr R0가 v2에서 실현 실패라 안 잰 쌍이 이번에 실현됨) |
| R1 = R2 | **11.5 %**(13; ngcc M6A/M7 m 4/3, M14/M8 10.5 %) | 4.2 %(10; folded M11/MN m 6/4) | 5e-5 / 3.8 % | 변화 0 |
| R3 | 11.4 %(13) | 1.3 %(10; ngcc M3/M4) | 0.92 % / 0.61 % | 미러 8.2 % → 1.3 %(v2 max였던 nmcnr이 이번엔 R3 실현 실패라 안 잼), n 15 → 13 |

S5 일관 추정(R1, 쓰기-종속 쌍 21): m 같음 + 비 그대로인 쌍 다수, 반올림이 비를 바꾼 쌍 = ngcc M8/M14 θ W 비 1.128 → 실현 1.25, M6A/M7 0.847 → 0.75, folded MN/M11 1.581 → 1.5, two_stage_ota L0 M5/M7 0.474 → 0.455, HS M5/M7 1.947 → 1.875 -- **v2와 같은 값**.

### 3.5 실현 평가 결과 (8점)

| 규칙 | 실현 탈락 | 봉인 7 깨짐(실현 VDS − VDSAT < 0) | 가장 큰 여유 감소 | v2 대비 |
|---|---|---|---|---|
| R0 | **0/8** | 0/76 | nmcnr M101 −18.3 mV(0.455 → 0.437 V) | 2/8 → 0/8(common_gate 봉인 3·nmcnr Newton 상한 둘 다 해소 -- µV tol 결합 해소와 맞는 꼴) |
| R1 = R2 | 1/8(nmcnr `newton_line_search`) | 0/76 | **common_gate M3 −150 mV**(입력 고정 구성) | 변화 0 |
| R3 | 1/8(nmcnr `newton_line_search`) | 0/76 | 0(이동 없음) | 탈락 회로 common_gate(봉인 3) → nmcnr(Newton) |

입력 고정 구성 2회로(common_gate, pushpull): R0 실현 통과·VDS 이동 0(common_gate는 v2 실현 실패 → 통과), R1 common_gate M3 VDS 0.600 → 0.450 V(여유 0.559 → 0.409 V)·pushpull M6 −9.7 mV(v2와 같음), R3 이동 0.

### 3.6 servo 회로 입력 차 이동 ΔV_id (실현 − 탐색, S8 DVID)

| 규칙 | folded | ngcc | nmcnr | two_stage_ota 층 0 / HS | two_stage_ota_sf | v2 대비 |
|---|---|---|---|---|---|---|
| R0 | 0 | 0 | **+47.9 mV** | 0 / **0** | 0 | v2 −30 µV·−40 µV·(실패)·8 µV/102 µV·8 µV → nmcnr 외 전부 0 |
| R1 = R2 | −37 µV | −276 µV | (실현 실패) | 0 / 0 | 0 | 변화 0 |
| R3 | 0 | 0 | (실현 실패) | 0 / 0 | 0 | v2 −29 µV·−430 µV·2.6 mV·15/564 µV·15 µV → 0 |

- '0'은 '효과 0'이 아니라 '잔차 효과가 봉인 3 tol_I 안이라 풀이가 출발 점을 수렴으로 받음'이다. S9 확인: HS **R0도 이제 모든 노드 이동 0**이고 MOS 전류만의 노드 KCL 합 OUT 2.6e-8·CS −2.9e-8·D3 1.1e-8 A(v2 R0는 노드가 움직이고 KCL 합 ≤ 2e-11 A). R1은 v2와 같음(OUT 1.29e-6 A). → v2 V2-1.2의 예측('LM-1 뒤에는 모든 슬라이스가 mV 급이 되어 잔차 수 % 이하 효과는 실현 평가에서 보이지 않는다')이 R0에서도 실측으로 맞음.
- nmcnr R0 +47.9 mV: 층 0 퇴화 점(M103 전류 1.0e-14 A, M102 9.1e-13 A)에서 실현 재풀이가 입력 차를 옮겼고, 그 결과 연결상 '차동 꼴' M102/M103의 실현 전류가 8.72e-13·4.68e-14 A로 바뀌어 비 오차 366 %가 나왔다. 계획 1차 식 ln(1 + r)/(gm/ID)(r ≤ 4.6e-3)로는 ~mV 이하라 이 이동은 잔차 크기로 설명되지 않는다 -- 원인 분해 안 함(불확실 4.3). R1·R3는 같은 점에서 Newton 실패라 비교 불가.

### 3.7 두 슬라이스 gm/ID (S4, HS 종속 소자, 같은 노드 점)

| 소자 | R0 키 gm/ID | 키 1000 gm/ID | 차 | v2 대비 |
|---|---|---|---|---|
| M1 | 128: 17.81 | 18.18 | 2.0 % | v2 키 84: 16.92 대 18.17(7 %) → R0 키가 128로 바뀌어 2.0 % |
| M4 | 600: 11.21 | 11.98 | 6.4 % | 같음 |
| M7 | 120: 17.32 | 17.61 | 1.7 % | 같음 |

### 3.8 대표점 HS(two_stage_ota) gbw 행 c (탐색 / 실현)

| 규칙 | v3 | v2 | 비고 |
|---|---|---|---|
| R0 | **−0.0691 / −0.0724** (active, 거부) | −330.20 / −330.93 | tol 정규화 행 -- 같은 규칙에서 4천 배 줄어든 것은 tol_V µV → mV(분모) 효과. 부호는 여전히 음(spec 미달) |
| R1 = R2 | **+0.0491 / +0.1366** | +0.049 / +0.137 | 같음 |
| R3 | −0.0014 / −0.0252 | −3.40 / −9.94 | 부호 음 유지 |

- 이제 R0와 R1이 같은 tol 잣대(모든 슬라이스 mV 급)라 v2 ⚠('잣대가 달라 비교 불가')는 풀렸다. 같은 θ 점에서 R1(키 1000 전부)은 gbw 행 통과, R0·R3(M1 키 128 등 좁은 슬라이스)는 미달. 차의 물리 원인 후보는 M1 gm/ID(키 128 17.81 대 키 1000 18.18, −2 %)·용량 열(기준 폭 표 W 비례 근사) 등이며 **분해는 미측정**. 어느 쪽이 SPICE와 맞는지는 oracle(E-1) 몫이고 이 측정에 없다.
- 층 0 점 gbw 행: 7회로 모두 4규칙에서 부호 같음(spec 미달 점).

## 4. 원칙·Q-P8 근거 대조 (사실 대조, 물리 판정은 칸마다)

Q-P8 근거(v1 §2.1, P:305 원문 직접 확인): ① SPICE는 손가락 폭 w_f로 bin 모델을 고른다 ② 슬라이스 폭에서는 LUT 값 = 그 폭의 SPICE 스윕(보간 0) ③ IDu(w)는 bin 경계 연속·bin 안 0.54~1.74배 -- '가까운 슬라이스 값'·'기준 폭 한 장'은 부정합 ④ 동률 규칙 근거 "용량·잡음·mismatch 열을 기준 폭 표에서 읽으므로 손가락 기하를 기준 폭에 가깝게" ⑤ "같은 W의 matching 쌍은 같은 (m, w_s)라 비가 보존되고, 비가 다른 미러는 비 오차가 계통 offset metric에 나타난다(E-1)".

물리 판정 표기: 맞음 / 조건부 / 틀림 / 불확실 -- '그 규칙이 그 근거·원칙을 물리적으로 지키는가'에 대한 판정.

| 항목 | R0 현행 | R1 넓은 우선 | R2 bin 안 잔차 최소 | R3 연결 묶음 공유 |
|---|---|---|---|---|
| ①② 슬라이스 고정(w_f = 슬라이스 폭, 보간 0) | 지킴 -- **맞음** | 지킴 -- **맞음** | 지킴 -- **맞음** | 지킴 -- **맞음** |
| ③ bin 안 IDu 변화 반영(가까운 슬라이스 대체 없음) | 지킴 -- **맞음** | 지킴 -- **맞음** | 지킴 -- **맞음** | 지킴(키를 바꾸면 그 키의 W(s)로 m 재계산) -- **맞음** |
| ④ 기준 폭 가까이(용량·잡음·mismatch 기준 폭 표 W 비례 근사) | 어김: HS 최대 m 299, M1 키 128(0.64 µm) -- **틀림**(근사가 가장 나쁜 쪽; 단 v2 키 84 → 128로 덜 좁아짐) | 지킴: W ≥ w_hi 소자는 손가락 = 기준 폭 -- **맞음**; W < w_hi 소자는 최소 슬라이스 m = 1로 가므로 **조건부**(측정 점 해당 0건) | R1과 같음 -- **조건부** | 어김(키 = 쓰기 소자 R0 키) -- **틀림** |
| ⑤ 전반부 '같은 W 정합 쌍 → 같은 (m, w_s)' | 붕괴: 묶음 같은 W bin 3/23, HS 1/3 -- **틀림**(정합 묶음이 다른 bin 모델) | 같은 W bin 23/23 -- **맞음**(측정 점에서; W 근처 w_s인 쌍 0건이라 일반성 **불확실**) | **맞음**(R1과 같음) | 23/23(정의상) -- **맞음**. 단 연결만의 '차동 꼴'이 비정합 쌍(nmcnr M102/M103, θ 전류 비 0.0115)을 묶음 -- **조건부** |
| ⑤ 후반부 '비 보존 / 비 다른 미러는 비 오차가 E-1에서 보임' | 같은 전류 0.48 %, 미러 0.34 %(nmcnr 비정합 쌍 제외) -- **맞음**. nmcnr 366 %는 퇴화 점 재풀이 이동(3.6) -- **불확실** | 같은 전류 11.5 %·미러 4.2 %(m 작은 소자 정수 양자화 ≤ 1/(2m)) -- **조건부**(E-1이 판정할 양이나 크기가 R0보다 1~2자리 큼) | R1과 같음 -- **조건부** | 같은 전류 11.4 %, 미러 1.3 % -- **조건부** |
| 원칙 1·6 물리 정합(E-0: 봉인 7·실현 가능·W_min) | 봉인 7 깨짐 0/76, 실현 탈락 0/8, W_min 아래 0/76 -- **맞음**(E-0 위반 0). 정합 묶음 bin 분리는 E-0이 아니라 설계 품질 -- 그 물리 손실 크기는 **불확실**(oracle 몫) | 깨짐 0/76, W_min 아래 0, 실현 탈락 1/8(nmcnr Newton) -- **맞음**(E-0 위반 0). 입력 고정 구성 출력 노드 150 mV 이동(P:305 입력 고정 구성 물리 결정자 꼴) -- 이번 점은 여유 안이라 **조건부** | R1과 같음 -- **조건부** | 깨짐 0, W_min 아래 0, 탈락 1/8 -- **맞음**(E-0) / 묶음 정의는 **조건부** |
| 원칙 6 '제한은 물리 근거로' | 선택 기준(잔차 최소)이 바꾸는 물리량(gm/ID 1.7~6.4 %)보다 잔차(≤ 5.7e-4 HS)가 1~2자리 작음 -- 선택 기준의 물리 결정자 **불확실** | 새 제한 없음(④를 선택 기준으로 올림) -- **조건부**(W < w_hi 갈래 m = 1 규칙) | bin 열거 갈래 추가, 이 LUT에서 R1과 결과 차 0 -- **조건부** | 연결 묶음 정의(새 집합) -- 원칙 14 아래 정합 판정 불가 -- **불확실** |
| 원칙 7 graph 정본(필드 writer 하나·새 cache 0) | 현행 `dc_finger` writer = DC 블록 하나 -- 변경 0 -- 해당 없음(규칙 변경 없음) | 선택식만 바뀜, 필드·writer 그대로, 새 저장 0 -- **맞음**(꼴상) | 같음 -- **맞음** | 소자 선택이 다른 소자(묶음 쓰기 소자)의 선택을 READS → DC 블록 안 소자 간 결합; 새 필드 없이 가능한지 design 미검토 -- **불확실** |
| 원칙 11 상수 발명 | 0(선언·LUT·PDK) -- **맞음** | 0(w_s·W(s)·W_min만) -- **맞음** | w_hi = 기준 폭 bin 위 끝(LUT bin 지도) -- **맞음** | 0 -- **맞음**. (측정 스크립트의 ALT 점 1.75 µm·10 µA는 측정용 점, 규칙 상수 아님) |
| 원래 취지 | C1 (A) 그대로 | C1 (A) 선택식 변경 + O-166·U-130 머리 규칙(넓은 손가락) 취지 부분 복원 -- O-173이 대체한 방향과 반대(v2 V2-4 2) | R1과 같음 + 규칙 복잡 | C1 (A) 위 묶음 결합 추가 |

## 5. v2 대비 바뀐 결론 (사실만)

1. **R0의 v2 실현 결과 중 µV tol 결합분이 사라졌다**: 실현 탈락 2/8 → 0/8, servo ΔV_id(nmcnr 제외) 수십~백 µV → 0, HS 노드 이동 → 0(S9). v2 V2-1.2 예측이 R0에서 실측으로 맞음.
2. **HS gbw 행 c 비교가 같은 잣대가 됐다**: R0 −0.069(미달) 대 R1 +0.049(통과), R3 −0.0014(미달). v2의 −330은 tol 효과였음. 같은 θ에서 선택 규칙만으로 spec 행 부호가 갈린다 -- 원인 분해(M1 gm/ID −2 %, 용량 근사 등)는 미측정.
3. **W_min 아래 손가락 0/76**(v2 R0 7소자). R0 HS M1 키 84 → 128(gm/ID 차 7 % → 2 %).
4. **R1·R2는 수치 변화 0**(모든 소자 기준 폭 키 -- QA·W_min 수정 영향 없음). 전류 비 양자화 11.5 %·입력 고정 노드 이동 150 mV는 그대로 남는다.
5. **R0 정합 묶음 bin 분리는 그대로**(3/23, HS 1/3). QA·W_min 수정은 이 지표를 바꾸지 않았다.
6. **새로 보인 것**: R0 nmcnr 실현 통과 + ΔV_id 47.9 mV + 연결상 '차동 꼴' 비정합 쌍 비 오차 366 %(퇴화 점). R3 미러 비 오차 max 8.2 % → 1.3 %는 nmcnr이 R3에서 실현 실패라 그 쌍을 안 잰 결과(개선 아님).
7. 측정 회로 수는 v2와 같은 7/13. ALT 점 L 성분 보강으로 current_reuse·sf_pushpull이 평가 단계까지 갔으나 각각 `outside_domain`·탐색 봉인 7 실패. rfc·sf_pushpull 층 0 정지 사유가 `start_tol_v_undefined`로 바뀜(LM-1e 가드).

## 6. 남은 불확실

1. 대표점은 여전히 HS 1점, 나머지 7점은 전류 하한 퇴화 점(69/76 소자). 6/13 회로 미측정(구조 미지원 2, 층 0 출발점 없음 4).
2. 실현 평가의 '이동 0'은 tol_I 분해능 안 수렴이라 잔차·bin 분리·양자화의 실제 물리 효과(SPICE)는 이 측정에 없다 -- oracle(E-1) 몫. 특히 HS gbw 행 부호 차(R0 미달 / R1 통과)가 SPICE에서도 같은 방향인지 모른다.
3. HS gbw c 차의 원인 분해(gm/ID 대 용량·잡음 열 기준 폭 근사) 미측정.
4. nmcnr R0 ΔV_id 47.9 mV의 원인(잔차 크기로는 설명 안 됨, 퇴화 전류 1e-14 A 영역) 미분해. R1·R3는 같은 점에서 Newton 실패라 대조 불가.
5. W가 w_s~2·w_s인 정합 쌍(R1 m = 1~2, 갈림 위험)과 W < w_hi 소자(R1 최소 슬라이스 m = 1 갈래)는 측정 점에 0건.
6. 입력 고정 구성 봉인 7 위험은 2회로·각 1점(깨짐 0, 최대 이동 R1 150 mV). P:305 '10~37 % 꼬리 → 0.2~0.7 V'는 재현도 반증도 아님.
7. rfc·sf_pushpull 층 0 정지 사유가 `start_tol_v_undefined`로 바뀐 원인(어느 소자·셀)은 이 측정 범위 밖(기록만).
8. 결정 간 모순 점검(⑩)은 이 문서 작성자가 채울 수 없다 -- 질문 상정 전 점검자 배정 필요.

## 7. 출처

| 내용 | 출처 | 구분 |
|---|---|---|
| 규칙별 탐색·실현 평가, 잔차·m·여유·전류·입력 전압·묶음·gbw | `la1s_qb3/out/qb2_rules_realize.txt`, 요약 `out/qb2_summary.txt` | 실측(직접) |
| 소자 후보·정합 쌍·두 슬라이스 gm/ID·MDIST·W_min 선언 값 | `out/qb_slice_rules.txt` | 실측(직접) |
| 같은 전류 쌍 일관 추정 | `out/qb_pairs_consistent.txt` | 실측(직접) |
| HS R0·R1 노드 이동·KCL 합 | `out/qb2_probe_kcl.txt` | 실측(직접) |
| 못 잰 회로 사유 | `out/qb2_probe_domain.txt`, `out/qb2_rules_realize.txt` ERR·NO_THETA0 줄 | 실측(직접) |
| 실행 기록(메모리·시간) | `out/*.runlog` | 실측(직접) |
| v2 값 | `la1s_wb1_rec13/out/qb2_summary.txt`·`qb2_rules_realize.txt`, 권고 문서 V2-2 | 원 파일 직접 읽음 |
| Q-P8 근거·선택식·물리 결정자 | 계획 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` P:305 DEC-105 (2)(faf69218) | 원문 직접 읽음 |
