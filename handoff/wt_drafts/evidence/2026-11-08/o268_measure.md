verdict: 창 안 0/13, 창 밖 0/13, 미측정 13 (O-268 출력 스윙 중심 = 정의 자리 없음 13/13 -- 계획 정의 생산자 card DE-1 착수 전; 엔진 출발점 자체도 미측정 8/13). O-269 갈래값 판정(엔진 측정 5회로 한정, ICMR 측정 창 대리): 해석 A 창 안 4/5·창 밖 1/5(common_gate), 해석 B 창 안 1/5·정의 자리 없음 4/5.

# O-268 / O-269 실현 가능성 실측 (측정자, 엔진 code 수정 0)

- 대상: master `bbcc83a0` 격리 복제본 `C:/o268_iso`(`git clone --no-hardlinks`, origin 제거). library 13회로.
- 스크립트: `wt/_drafts/evidence/2026-11-08/o268_measure.py`(driver/worker, 회로마다 별도 프로세스), 집계 `o268_summary.py` -> `o268_summary.json`. 원 결과 `o268_measure.jsonl`(회로마다 append, current_reuse는 2줄 -- 첫 줄은 측정 스크립트 기록 버그(`Layer0Result.failure` 없는 속성)로 실패 사유를 못 적어 같은 조건으로 1회 재실행; 시스템 회수가 아니라 스크립트 결함이라 재실행함. 집계는 마지막 줄).
- 엔진 출발점 = `layer0_start`가 처음 받아들인 평가(사다리 칸·보정·Halton 시험점 -- `_maxmin`에 들어가는 `first`). 측정 도구 안에서 `_maxmin` 진입 때 멈춤(엔진 파일 무변경). 탐색 설정 = θ 수동소자 상자는 spec `search.theta_bounds`(13회로 모두 spec 상자로 통과, 대체 상자 사용 0), 평가 예산 E_B = 40(generality test fixture·la1a 측정 도구와 같은 값 -- 측정 입력이지 근거 아님).
- 메모리: 착수 대기 3.7 GB·정지 1 GB 규칙 적용. two_stage_ota_sf는 실행 중 여유 0.95 GB로 그 PID만 멈춤(미측정, 재실행 안 함). 끝난 뒤 python 프로세스 0 확인.

## 1. 정의 자리 점검 (엔진 READS 가능 여부)

| 양 | 계획 정의 자리 | master 생산자 | 판정 |
|---|---|---|---|
| (a) 출력 스윙 창 [V_out,min, V_out,max]·중심 | 계획 N3.8 '스윙·입력 범위' (2) 출력 스윙(입력 공통모드를 **동작점에 고정**하고 차동 입력을 DC로 훑을 때 모든 MOS가 선언 영역에 머무는 출력 구간), 값 = card DE-1(N6.8, DEC-104 R2 (c)·R9) | **없음** -- card DE-1 '착수 전'(계획 1377행). 옛 `metrics/ls_swing.py`(경로 합, metric `swing_out_v`)는 O-23·O-26이 삭제 방향으로 정했고 metric은 O-154 Q3로 계획에서 삭제됨 | **정의 자리 없음 13/13**. 손 계산으로 메우지 않음. `ls_swing` 값은 아래 참고 열에만(정의 아님) |
| (b) 입력 공통모드 창(DEC-106 (5) = R5′ (2) W4 규칙 ∩ 레일, "모든 포화 행·writer_root 행") | DEC-106 (5), DEC-104 R5′ (2) | **정확한 정의의 생산자 없음.** 커널 `node.dc_window`(block_dc `kvl_window`)는 W4 뿌리마다 **VDS ≥ 0 KVL 순서 창(VDSAT 항 없음)** -- 포화 행이 아니라 더 넓은 창. 입력 뿌리는 게이트라 채널 제약 0 -> 대부분 레일 전체 | 정의 자리 없음(불확실). 대리 둘을 적음: (b1) 커널 W4 창, (b2) ICMR 측정 창 |
| (c) ICMR 창 | N3.8 'ICMR 측정 구성'(servo, O-115) | `metrics/icm_config.py` `graph.icm_config` (vcm_lo, vcm_hi) -- 봉인점마다 계산(VDS = VDSAT, KCL 틀) | 측정 5회로에서 READS. 단 **spec이 ICMR '창'을 선언한 회로 0/13**(ngcc `icmr_v >= 0.6`, nmcnr `icmr_v >= 0.5`는 폭만; r2r는 `_input_dc_comment`에 원문 CMR 범위 서술만, 제약 아님) |
| (d) 레일 중앙값 | (V⁺+V⁻)/2 = supplies_v 최대·최소의 평균 | spec 파일 | 13/13 = 0.9 V |

**순환 사실(O-268 열린 확인 1의 실측 근거):** 계획 출력 스윙 정의 자체가 "입력 공통모드를 동작점에 고정"을 전제로 한다(N3.8 (2)) -- 출력 스윙 중심으로 입력 고정점을 정하면 그 스윙은 입력 고정점에 의존한다. 엔진에서 이 순환을 푸는 자리는 없다.

## 2. 회로별 표

갈래 규칙(O-268 + O-269): 입력 DC 선언(`net`·`value`) -> **선언** / 피드백 구성 -> **출력 스윙 중심** / 그 밖 -> **레일 중앙값**.
'피드백 구성'의 판정 근거가 spec에 둘로 읽혀 두 해석을 나란히 적는다:
- 해석 A: `feedback.elements`가 비지 않은 회로만 피드백 구성(current_reuse 1회로 -- Cf1·Cf2).
- 해석 B: `feedback.elements: []`도 피드백 구성으로 봄 -- 12회로의 출처 기록이 "선언된 되먹임 수동소자가 없으면 beta=1 루프"(user_decisions 2026-10-07 9번, **PM 정의용 규칙**)라서 β = 1 루프 = 입력 DC = 출력 DC 구성으로 읽을 여지가 있음. 이것이 '측정 구성 선언'인지는 spec이 말하지 않음 -> 불확실.

창 판정 열은 (b2) ICMR 측정 창 [vcm_lo, vcm_hi](포화 행이 있는 유일한 엔진 창) 기준, 괄호는 (b1) 커널 W4 창.

| 회로 | input_dc | feedback | swing·ICMR spec | 엔진 출발점 | 출발 v_cm [V] | 출발 V_out [V] | (b1) 커널 W4 창(입력 뿌리) | (b2)=(c) ICMR 측정 창 | (a) 출력 스윙 중심 | 레일 중앙 0.9 창 안? | 갈래 A -> 값 -> 창 안? | 갈래 B -> 값 -> 창 안? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cnr_ota | pending U-75 | [] | 없음 | 미측정(단계 A 정지: `cs_output_low_impedance`·`loop_record_only`·`column_unassigned` 등) | -- | -- | -- | -- | 정의 자리 없음 | 미측정 | 레일 중앙 0.9 -> 미측정 | 스윙 중심 -> 정의 자리 없음 |
| common_gate_amplifier | pending SP-2 | [] | 없음 | sealed | 0.600 | 1.200 | [0, 1.2] (제약 2) | [0.527, 0.665] | 정의 자리 없음 | **아니오** (W4 창 안) | 레일 중앙 0.9 -> **창 밖(fail-closed 대상)** | 스윙 중심 -> 정의 자리 없음 |
| current_reuse_telescopic_ota | pending SP-2 | [Cf1, Cf2] | `swing_out_v >= 2.4`, `icm_margin_v >= 0`, MOD5 pending | 미측정(출발점 없음: 사다리·보정 실패 후 Halton 33점이 E_B 40에 닿음, `no_root_in_window` @Ncmfb_tail, M37b) | -- | -- | -- | -- | 정의 자리 없음 | 미측정 | 스윙 중심 -> 정의 자리 없음 | 스윙 중심 -> 정의 자리 없음 |
| erfc_ota | value 0.8 | [] | 없음 | 미측정(단계 A 정지: `cs_output_low_impedance`·`column_unassigned` M21 등) | -- | -- | -- | -- | 정의 자리 없음 | 미측정 | 선언 0.8 -> 미측정 | 선언 0.8 -> 미측정 |
| folded_cascode | pending SP-2 | [] | 없음 | sealed | 0.900 | 0.814 | [0, 1.8] (제약 0) | [0.331, 1.720] | 정의 자리 없음 | 예 | 레일 중앙 0.9 -> 창 안 | 스윙 중심 -> 정의 자리 없음 |
| ngcc_3stage_ff | pending SP-2 | [] | `icmr_v >= 0.6`(폭만) | 미측정(단계 A review_needed `dc_role_unresolved_group` M8·M14 -- O-216 structure 사실이 master에 없음) | -- | -- | -- | -- | 정의 자리 없음 | 미측정 | 레일 중앙 0.9 -> 미측정 | 스윙 중심 -> 정의 자리 없음 |
| nmcnr_amplifier | pending SP-2 | [] | `icmr_v >= 0.5`, `swing_out_v >= 0.5` | sealed | 0.499 | 1.542 | [0, 1.8] (제약 0) | [0.072, 1.426] | 정의 자리 없음 (참고 ls_swing 경로 합: Vout [0.043, 1.751], 중심 0.897 -- 정의 아님) | 예 | 레일 중앙 0.9 -> 창 안 | 스윙 중심 -> 정의 자리 없음 |
| pushpull_follower_buffer | net agnd (0.9) | [] | `rout_ss_ohm`만 | sealed | 0.900 | 0.652 | 입력 W4 아님(선언 F) | [0.345, 1.749] | 정의 자리 없음 | 예 | 선언 0.9 -> 창 안 | 선언 0.9 -> 창 안 |
| r2r_opamp | pending U-75 | [] | 없음(원문 CMR 범위는 주석) | 미측정(단계 A 정지: `loop_record_only` 3·`dc_role_unresolved_group`) | -- | -- | -- | -- | 정의 자리 없음 | 미측정 | 레일 중앙 0.9 -> 미측정 | 스윙 중심 -> 정의 자리 없음 |
| rfc_ota | value 1.02 | [] | 없음 | 미측정(단계 A review_needed `dc_role_unresolved_group` 3묶음) | -- | -- | -- | -- | 정의 자리 없음 | 미측정 | 선언 1.02 -> 미측정 | 선언 1.02 -> 미측정 |
| sf_pushpull_output_opamp | net agnd (0.9) | [] | `rout_ss_ohm`, `icm_margin_v >= 0` | 미측정(출발점 없음: `lut_query_failed` M10 VDS −1.22 V, Halton 33점이 E_B 40에 닿음) | -- | -- | -- | -- | 정의 자리 없음 | 미측정 | 선언 0.9 -> 미측정 | 선언 0.9 -> 미측정 |
| two_stage_ota | pending SP-2 | [] | 없음 | sealed | 0.900 | 0.900 | [0, 1.8] (제약 0) | [0.574, 1.789] | 정의 자리 없음 | 예 | 레일 중앙 0.9 -> 창 안 | 스윙 중심 -> 정의 자리 없음 |
| two_stage_ota_sf | pending SP-2 | [] | `rout_ss_ohm`만 | **미측정(메모리: 여유 0.95 GB에서 PID 정지, peak RSS 4.93 GB)** | -- | -- | -- | -- | 정의 자리 없음 | 미측정 | 레일 중앙 0.9 -> 미측정 | 스윙 중심 -> 정의 자리 없음 |

## 3. 집계 (n/N)

spec 선언(파일만, 13회로):
- input_dc 선언 4/13(value: erfc 0.8·rfc 1.02, net agnd: pushpull·sf_pushpull), pending 9/13(SP-2 7, U-75 2), engine 0/13.
- feedback: elements 선언 1/13(current_reuse), `[]` 12/13, pending·누락 0/13. **피드백 미선언(pending·누락) 0/13**; 해석 A로 '피드백 구성 아님' 12/13.
- swing 제약 2/13(current_reuse, nmcnr), ICMR 폭 제약 2/13(ngcc, nmcnr), icm_margin 2/13(current_reuse, sf_pushpull), ICMR 창 선언 0/13, 출력 범위(창) 선언 0/13.

O-268 (출력 스윙 중심이 입력 창 안인가):
- 중심 정의 가능 0/13 -> 창 안 0/13, 창 밖 0/13, 미측정 13/13.

O-269 갈래:
- 해석 A: 선언 4 / 출력 스윙 중심 1 / 레일 중앙값 8. 값이 ICMR 측정 창 안 4(two_stage·folded·nmcnr 레일 중앙, pushpull 선언), **창 밖 1(common_gate 레일 중앙 0.9 ∉ [0.527, 0.665] -- fail-closed 대상)**, 미측정 8(엔진 미측정 7 + current_reuse 정의 자리 없음).
- 해석 B: 선언 4 / 출력 스윙 중심 9 / 레일 중앙값 0. 창 안 1(pushpull), 창 밖 0, 정의 자리 없음 9, 미측정(선언 회로 엔진 미측정) 3.
- 레일 중앙 0.9가 창 안(측정 5회로): ICMR 측정 창 4/5, 커널 W4 창 5/5(common_gate도 [0, 1.2] 안).

(d) 비교 -- 지금 엔진 출발점 v_cm(측정 5):
- 레일 중앙과 같음 3/5(two_stage·folded·pushpull 0.900). two_stage·folded는 W4 창이 레일 전체라 y = 0.5 상자 중심이 우연히 레일 중앙이 된 것(규칙이 레일 중앙을 고른 것이 아님), pushpull은 선언값.
- 다름 2/5: common_gate 0.600(W4 창 [0, 1.2]의 중점), nmcnr 0.499(사다리·보정·Halton 중 어느 출처인지 기록 안 함 -- 측정 스크립트가 `Layer0Result.source`를 잡지 않음).
- 출발점 V_out은 입력 v_cm과 같지 않음(β = 1 구성이면 같아야 함): folded 0.814 대 0.900, nmcnr 1.542 대 0.499, pushpull 0.652 대 0.900, common_gate 1.200 대 0.600 -- 지금 엔진 출발점은 입력 DC = 출력 DC 정합을 강제하지 않는다.

## 4. 정의 자리가 없거나 불확실한 것

1. **출력 스윙 창(O-268 (2)의 값)** -- master 생산자 0. card DE-1(N6.8)이 착수 전이고 순서는 LA-1 -> DE-1(N6.1 표 #2). O-268을 적용하려면 DE-1 값이 출발 단계보다 먼저 있어야 하는데, 계획상 DE-1은 봉인점 KCL(R9) 값이고 출발 단계는 그 앞이다 -> **층 순서 충돌**(출발 θ에서 잰다면 DE-1 블록이 출발 스냅샷에서도 돌아야 함).
2. **출력 스윙 정의의 입력 공통모드 의존** -- N3.8 (2)가 "입력 공통모드를 동작점에 고정"을 전제로 함. 입력 고정점 = 출력 스윙 중심이면 고정점 반복(또는 동시 풀이)이 필요하고 그 자리·멈춤 조건은 계획에 없다.
3. **DEC-106 (5) 입력 공통모드 창(R5′ (2), 포화 행 포함)** -- 정확한 정의의 엔진 생산자 없음. 커널 W4 창은 VDS ≥ 0(VDSAT 없음)이고 ICMR 측정 창은 W·바이어스 고정 KCL 틀(원칙 4의 다른 틀)이다. 이 표의 창 판정은 대리값이다.
4. **'피드백 구성' 판정 근거** -- spec에 측정 구성(입력 DC = 출력 DC) 선언 칸이 없다. `feedback: []`의 출처 기록은 PM β = 1 규칙이라 해석 A·B가 갈린다(위 집계 9 대 1 차이).
5. **ICMR spec 창** -- 선언 0/13(폭만 2). (c)는 판정할 spec 창이 없음.
6. **엔진 미측정 8/13** -- 단계 A 정지 5(cnr·erfc·ngcc·r2r·rfc), 출발점 없음 2(current_reuse·sf_pushpull, E_B 40 안), 메모리 정지 1(two_stage_ota_sf). E_B 40은 측정 입력이라 더 큰 예산이면 출발점이 생길 수 있음(재지 않음).
