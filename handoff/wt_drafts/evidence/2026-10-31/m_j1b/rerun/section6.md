

## 6. 엔진 실제 값 재측정 (master 325ee241, 엔진 경로 열림 -- 추가 절; §0~5 경우 나눔 표는 그대로)

산출물: `m_j1b/rerun/` (`run_all.py`·`engine_calls.jsonl` 엔진 호출 기록, `measure_j1b_engine.py`, `devices_j1b_eng.jsonl`, `pooled_j1b_eng.json`, `agg_eng.py`, `reasons.py`). 엔진은 `probe_engine.py`로 `start_intervals._state`(current_model + macro_solve) 호출만 가로채 기록했다(우회 코드 없음, master 작업 트리 읽기만, output_dir 임시).

**값의 출처(표지)**: 호출 0번 = §6.5 1회차(gm/ID = 헤드룸 해 집합 위 끝 g_lo0, 즉 전류 밀도 상한 쪽이라 gm/ID가 가장 작고(0.5~2.4) **전류는 가장 큰 쪽 추정**). S: gm_req = 1회차 전류 x 그 gm/ID(= 매크로 블록 gm), 노드마다 ID = gm_req / (gm/ID). F: 1회차 전류 그대로. 그 밖 정의는 §1과 같다(S_d 행·면적 예산 3경우·tol_V 3경우).

### 6.1 엔진이 값을 준 소자는 16/115뿐이다 (S 11 + F 5)

| 구분 | 회로 (소자 수) | 사유 |
|---|---|---|
| 단계 A 정지 | cnr_ota 16, r2r_opamp 20 | `unsupported_rule_branch`(cs_output_low_impedance, loop_record_only 전역 피드백/교차결합, undeclared_loop_constraint) + `dc_role_unresolved_group`(gate 가 신호 넷인 같은 gate·source 묶음, dc_role 사실 필요). 단계 B도 정지 |
| 단계 A 정지 | erfc_ota 24 | spec 로드 거부 `topology_fp_mismatch`(spec `meta.topology_fp` 가 topology connectivity_fp `a5710202...` 와 다름). 단계 B 건너뜀 |
| review_needed | ngcc_3stage_ff 4, rfc_ota 7 | `dc_role_unresolved_group`(ngcc M14·M8; rfc M1a/M1b·M2a/M2b·Q15/Q16), rfc는 `l_owner_name_order`도. 단계 B도 review_needed라 출발 구간 미실행 |
| 단계 A·B ok지만 **전류 미정** | common_gate 1, current_reuse 16, folded_cascode 4, pushpull_follower 4, nmcnr 3 | 매크로가 gbw 비활성이라 전류를 못 정하고 엔진이 W_min 기반 **자리값**(`refs`)만 둔다(41 §6.5 '남는 θ 전류') -> 값으로 쓰지 않고 경우 나눔에 남김 |
| **값 있음** | nmcnr 3(S pfet M102·M103·M201), sf_pushpull 6(S 2 + F 4), two_stage_ota 3(S), two_stage_ota_sf 4(S 3 + F 1) | S 11·F 5 |

정지·review_needed 회로(cnr·r2r·erfc·ngcc·rfc, 71소자)와 전류 미정 소자(28)는 §0~5 경우 나눔 값으로 남는다. **K10 누설 출발의 주인공인 gbw 없는 4회로 F 25소자는 엔진도 전류를 못 정한다**(자리값뿐). 실제 값 결과는 속도 행이 있는 회로의 소자에만 있다.

### 6.2 실제 값 기준 변형별 표 (N = 16: S 11·F 5, tol_V 1 mV)

- **누설 영역 출발(시도점)**: D1·D2+·D2 모두 다수 0/16 (S 0/11·F 0/5); D2 '1개 이상'만 S 3(nmcnr M102·M103·M201, 설정 11/6477·21/682). (가)·(나) 동일. 경우 나눔 §2.1의 D2 F 25/63은 이 16소자에 해당 소자가 없다(그 25는 전류 미정).
- **면적 예산이 시도점을 옮긴 소자(다수)**: full -- S 0/11, F 1/5 (two_stage_sf M8); share -- S 0/11, F 4/5 ((가); (나)는 3/5). 옮김 폭(중앙): M8 full ln IDu +0.9, share +2.1; sf_pushpull F share +0.3~0.7. S는 0(gm_req가 작아 ID 1e-8~1.5e-5).
- **t\* 차 (pool, 설정 단위; 앞 변형 - 뒤 변형)**: K10 D1-D2+ 전 칸 0.0 %. K10 D1-D2: S pfet 0.3 %(ln IDu max 2.3(가)·3.9(나), VGS max 0.15·0.26)만, 나머지 0. K3 (나)-(가): S pfet 13.9 %(p90 0.66, max 5.6, VGS max 0.34), **F pfet 36.1 %(none/full)·30.0 %(share)**(p90 1.3, max 2.0, VGS max 0.11), nfet(S·F) 0. K3 값은 D1·D2에서 같다. 예산 3경우 사이 K10 차는 같고 F pfet K3만 36->30 %.
- 소자별 값은 `devices_j1b_eng.jsonl`(조합 키 `...|IDeng|{none,full,share}`).

### 6.3 경우 나눔과의 차 (같은 16소자, share, D1 (가))

| 소자군 | 실제 ID_eff | 가장 가까운 경우 나눔 칸 | 결과 차 |
|---|---|---|---|
| nmcnr S pfet 3 | 1.4e-8~6.4e-8 A | 1e-7 | t\* 동일(ln IDu -21.8/-21.5, VGS 0.862/0.637), 옮김 0 동일 |
| two_stage·two_stage_sf S 6 | 2.4e-7(입력쌍 4)·1.5e-5·4.5e-6(2단 pfet) | 1e-7·1e-5 | t\* 동일(ln IDu -19.1~-19.3, 차 <= 0.1), 옮김 0 동일 |
| sf_pushpull S nfet 2 | 1.9e-6 | 1e-6 | ln IDu -16.8 대 -17.0, VGS 같음, 옮김 0 |
| sf_pushpull F 4 | 1.1~1.6e-3 | 1e-3 | t\* 같거나 ln IDu +0.4~0.6 위; **옮긴 설정 수는 실제값이 많다**(M19 3755 대 1442, M22 4387 대 1442, M21 4036 대 1034, M18 1770 대 1034 / 5255~5859) |
| two_stage_sf F(M8) | 5.6e-4 | 1e-3 | t\* ln IDu -17.1 대 -16.4(실제가 0.7 낮음), 옮김 6273 대 6253 / 6273 거의 같음 |

해석 표지: ① S는 경우 나눔 결과와 거의 같다(속도 행이 시도점을 정하고 예산이 못 건드림). ② F는 실제 1회차 전류가 1e-3 A 쪽(경우 나눔 상단)이라 §2.3 'F가 거의 다 옮겨진다'는 5 F 중 4에서만 성립하고 옮김 폭은 작다(0.3~2). ③ 경우 나눔의 큰 결론(gbw 없는 4회로 F에서 D2 누설 출발이 예산으로 올라감)은 **엔진 값으로 확인할 수 없다**(전류 미정). ④ 이 16소자에서 K10 변형 차는 사실상 0이고 K3 (가)/(나) 차는 pfet에서만 나며 경우 나눔(S pfet 15~17 %·F pfet 5~17 %)과 같은 방향이다(S pfet 13.9 %, F pfet 30~36 % -- F는 소자 4개분이라 크기 비교는 약하다).

### 6.4 한계 (추가)

- 값 있는 소자가 16/115라 pool 비율은 소자 수가 작다(S pfet n=15006 설정, F pfet n=10510 설정, 소자 4~5개 분).
- 1회차 전류는 gm/ID 상한 끝(강반전, 전류 최대) 기준이라 확정 전류(2회차·칸 0 위치)보다 F에서 크다. S의 gm_req(매크로 gm)도 gm/ID 의존 노드 용량 때문에 호출마다 변한다(two_stage O1: 1회차 6.7e-6, 다른 호출 1.2e-5·1.4e-4 등, `engine_calls.jsonl`). 여기서는 호출 0만 썼다.
- 엔진 호출은 as-built(옛 gm/ID 축 구간)이라 design v1.16의 ln IDu 좌표 규칙과 다르다. 전류(gm_req·F 전류)만 읽었고 S_d·t\*는 §1의 정의로 재계산했다.
