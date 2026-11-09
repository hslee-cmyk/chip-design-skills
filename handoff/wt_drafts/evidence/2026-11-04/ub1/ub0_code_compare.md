# UB-1 착수 사실: UB-0 규칙 차이 자리, M-LA16 대조, 판정 소비자 0

계획 N6.1 측정 게이트 표 (나)(코드 대조, LUT·커널 평가 0). 기준 master `7620f5ee`. `E/` = `skills/analog-gmid-design/gmid_engine/`.
재현: `measure_ub0.py` → `ub0_structure.jsonl`·`ub0_summary.txt`, `measure_ub0_extra.py` → `ub0_extra.jsonl`·`facts.txt`, `m_la16_grep.txt`.
13회로 구조는 `tests/graph/s1v_hand.build_lib`(S1v), 값은 `tests/metrics/u7_ngcc.library_case`의 합성 값이다. **합성 잔차는 참고이고 UB-0 값 차이((가), LA-1 측정 시점)가 아니다.** 시제품 풀이는 구현물이 아니다.

## 1. 두 구현 규칙 차이 (library 13회로, 전달 뷰 13, 블록 30)

대조 결과: MOS 집합 같음 21/30, 미지수 집합 같음 23/30, 막다른 저항이 있는 블록 3/30, 뷰 교류접지가 전 뷰 접지와 다른 뷰 1/13.

| # | 자리 | `block_local_gain`(`E/metrics/block_model.py`) | `block_gain_model_of`·`row_gains` | 발동 실측 | §2.5 처리 |
|---|---|---|---|---|---|
| R1 | 소자 집합 | netlist 인접, MOS 채널 따라 미지수 확장(`_select`, :61) | S1v `roles`(`_block_spec`, `achievability.py:153`) | 9/30 다름 | §2.5-1·2 '넓히지 않음'. 단 R2·R7 때문에 문언 부족 |
| R2 | 블록 밖 부하 소자 gds | 인접으로 스탬프 | 없음 | 버퍼 블록 5개: `pushpull_follower_buffer` vout(M5, M6), `sf_pushpull_output_opamp` vout(M17, M20), `two_stage_ota_sf` vout(M9), `cnr_ota` VCON·VCOP(x4[*]·x1[*].M1) | **§2.5-2는 '다음 블록 입력'만 적어 빠짐 -- 개정 G1** |
| R3 | 다음 블록 source 입력 | 인접으로 스탬프 | 없음 | **0/30**(비멤버 스탬프 소자 중 다른 블록 멤버 0) | §2.5-2. toy로만 잠근다 |
| R4 | 교류접지 | `ss.ground_nets`(모든 뷰) | `view.ac_ground` | 1/13: `current_reuse_telescopic_ota` Vbias2·Vbias3(as-built가 이 넷을 미지수로 풀고 M57·M61·M64·M68까지 넓힘) | §2.5-1 '그 뷰의 교류접지' -- `ViewStruct`에 자리 필요(G5) |
| R5 | 멤버 단자가 블록 노드 밖 | 미지수 | 접지로 둠(`block_gain_model.py:150` attach 규칙) | `sf_pushpull_output_opamp` Y(N5·N56·N7·N78·N13·N1314) | §2.5-1 '블록 소자 단자가 닿는 넷' = 미지수. :150 삭제 |
| R6 | 막다른 저항 | 미지수로 풂 | 뺌(`_active_resistors`, :108) | 3/30: `current_reuse` Rz1·Rz2, `nmcnr` Rm, `two_stage_ota` Rz. 저항 끝 넷을 읽는 gate 0/13 | §2.5-3. 단 gate 독자 조건이 문언에 없음(G2), as-built U9는 출력 예외도 없음 |
| R7 | FF 셀(merge 블록) | `extra`로 스탬프(gds 부하 포함) | 주경로 spec에 없음 | `ngcc_3stage_ff` Vout | **§2.5-4 '스탬프하지 않는다'와 충돌 -- 멈춤 S1(FF 귀속 공동분석)** |
| R8 | 폐포의 멈춤 | 남의 블록 넷에서 멈춤(`others`) | 해당 없음 | `decomposed_only` 블록: `cnr_ota` VCON·VCOP, `current_reuse` Vom·Vop, `erfc_ota` 큰 블록 | §2.5-2는 '교류접지·여기 넷'까지만 적음 -- 남의 블록 넷 멈춤 추가(G3) |
| R9 | 용량 전용 노드 | `floating` = 0 V(`_helpers_nodal.py:42`) | gate를 교류접지로 읽음 | **0/13**(전회로 d·s·저항 단자 없는 넷, 레일·bias·입력 제외) | §2.5-7·9. 행 모드 처리 G4 |
| R10 | 여기 패턴 | 차동 ±½ 하나 | 가중 없으면 차동 + 공통 둘의 최대(`_patterns`, :87) | 코드 대조, 발동 수 미측정 | 상한 건전성용. 이 card에서 안 바꿈, 표지 |
| R11 | Z_out·경로 기여·부호 | 있음 | 없음(|gain|만) | -- | 소비자 없으니 행 모드에 만들지 않음(원칙 9) |

**회로 해석 발동**: R7(FF 귀속)만 §2.5 표 '멈추고 공동분석'에 걸린다. 블록 경계는 발동 0.

## 2. 합성 체인 잔차 (참고, dB)

| 회로 | as-built | §2.5 시제품(G1·G3 + 뷰 접지) |
|---|---|---|
| common_gate_amplifier, folded_cascode, ngcc_3stage_ff, nmcnr_amplifier, pushpull_follower_buffer, rfc_ota, two_stage_ota_sf | 0.0 | 0.0 |
| two_stage_ota | −7.1e−15 | −7.1e−15 |
| sf_pushpull_output_opamp | 7.9e−4 | 7.9e−4 |
| cnr_ota | 0.0995 | 0.0995 |
| erfc_ota | 53.46 | 53.46 |
| current_reuse_telescopic_ota | −4.883 | −6.123 |
| r2r_opamp | None | None |

`tests/metrics/test_block_residual.py::test_library_residual_floor`의 7회로는 시제품에서도 바닥을 유지한다(기준 약화 불필요).
FF 문언 대조(`ngcc_3stage_ff`): §2.5-4 문언 그대로 = 잔차 **1.074 dB**, 주경로 사슬만 = **−4.475 dB**, FF gds를 merge에 스탬프(as-built, 시제품) = **0.0 dB**.

## 3. M-LA16 (정의 자리별 C 열)

| 정의 자리 | C 사용 | 판정 | 소유 |
|---|---|---|---|
| U9 `row_gains`(ω → 0 gain) | 없음 | gain·Z_out은 정의상 C 무관(§2.5-9). 어긋남은 용량 전용 노드 하나(R9, 0/13) | **UB-1이 고침** |
| `block_local_gain`(ω → 0) | 없음 | 같음 | **UB-1이 고침** |
| `E/lut/cap_query.py:50` `cgg_minus_cgd_at_gs` 갈래 | cgs = cgg − cgd | 정의 위반 갈래 | LA-1 범위 16(계획이 배정) |
| 출발 매크로 `E/search/iv_currents.py:112`, `macro_poles.py:6-7` | cgg, cdd(없으면 cgd) | C 열 사용, '없으면 cgd' 갈래 남음 | LA-1 design 전 대조(UB-1 밖) |
| 층 0 | `m_la16_grep.txt` 기준 `search/layer*` C 읽기 0 | 층 0 주파수 metric은 LA-1이 정함 | LA-1 design 전 대조 |

## 4. 판정 소비자 (UB-1 완료 (3))

`block_local_gain` 호출: `block_residual.py:58`, `ff_gm_ratio.py:46`. `block_residual` 호출: `metrics_aux.py:229`(보고).
보고 소비자: `search/kernel.py:60-88`(S3 기록), `search/gate_run.py:30`(메모), `search/residual_probe.py:62`(호출자 0 -- `residual_probe(` 정의만 있음, 별건 표지).
제약 행·봉인·front 비지배 소비자 **0**. '대상 없음' 성립.
`ff_gm_ratio`는 `registry.py:63` metric이라 spec이 제약을 선언하면 제약 행이 된다. library spec 선언 0개(`git grep`), `verified_by.py:47` `spice_unverifiable`. 계획 완료 (3)이 이름을 든 두 함수 밖이라 멈춤 아님, 표지.

## 5. IT 전제

`graph.ss_nodal`은 master·`integ/it12`(`b9351eac`) 트리에 아직 없다(`metrics/ss_nodal.py` 없음). 순서상 UB-1 base에는 있어야 한다(D40 v1.16.3 진행 순서). 착수 때 재측정.
