# 측정 m_j1b -- K3·K10: 실제 출발점(사다리 칸 0 t*)이 반전 수준 하한 행·전도 여유 행(K10)과 출발값 규칙(K3)에 따라 바뀌는가 (2026-10-31)

측정만 했다. 저장소·계획·git 쓰기 0, 엔진 파이프라인(`run_stage_*`·`start_intervals`) 호출 0. 스크립트·원자료: `wt/_drafts/evidence/2026-10-31/m_j1b/` (`measure_j1b.py` 본체, `devices_j1b.jsonl` 소자마다 1줄(115줄, 조합 210개씩), `pooled_j1b.json`, `tables_j1b.txt` 전수 표, `tolv.py`·`tolv_cells.json` LOO tol_V, `agg*.py`·`gen_report.py`). 정의 정본 = 후보 문서 K3·K10 'M-J1b 측정 정의'. 앞선 측정 `m_j1/`(분류·VSB 마디·f_req) 재사용.

## 0. 먼저 읽을 사실

1. **시도점(예산 무시)에서 누설 영역 출발은 D2뿐이다**: D2 (가) 다수 설정 기준 S 0/52 | F 25/63(전부 gbw 선언 없는 4회로의 F: common_gate 1·current_reuse 16·folded_cascode 4·pushpull_follower 4). D1·D2+는 행이 전도 여유를 요구하므로 0/N이다(정의상 귀결).
2. **면적 예산이 있는 회로(10/13, 48소자 = S 16·F 32)에서는 예산이 F 시도점을 거의 다 옮긴다**(ID 1e-6~1e-5: F 25/32, S 0/16; ID 1e-3: F 28/32, S 12/16). 옮긴 뒤 t*에서는 D1·D2+·D2 차가 거의 사라진다. 즉 K10의 실효 차는 예산이 없거나 느슨한 곳에만 남는다. 단 전류 ID는 경우 나눔(1e-7~1e-3 A)이다(§4 한계 1).
3. **D1 대 D2+ 차는 pfet 일부뿐**(전도 여유 경계 아래에 gm/ID 정점이 있는 곡선)이고 nfet은 0이다(정점 = VGS 0 격자점).
4. **(가) 대 (나) 차는 pfet이고 속도 행이 아래 끝을 중간 반전 쪽 골짜기에 놓는 소자에 몰린다**(M-J1과 같은 현상). nfet은 0이다.
5. **엔진 경로는 막혔다**: `run_stage_a`가 `pdk_source_sha256_mismatch`로 거부된다(저장소에 이미 있는 선언 불일치). 우회는 하지 않았다. gm_req·KCL 전류는 못 쟀다(§4 한계 1).

## 1. 입력과 구현한 정의 (표지)

- LUT: `assets/lut_v2_location.json` -> `sky130_nfet_pfet_lut_v2_r2.npz`(cap_npz)만. 축 L 18 x VGS 49(0~1.8 V, 간격 37.5 mV) x VDS 49 x VSB 10, W_ref 5 um 슬라이스, 보간 없음(격자 원값). **(L, VDS, VSB) 격자 = M-J1과 같다**(L 18 전부, VDS >= 0.3 V 41개, VSB는 M-J1 `devices.jsonl`의 `vsb_idx` 재사용: 소스 넷이 선언 전위면 |V_b - V_s| 마디, bulk 미선언 = kind별 레일, 아니면 0이 아닌 9 마디).
- 소자 115 = M-J1과 같음(S 52·F 63; nfet 59·pfet 56). S·F 분류·f_req도 M-J1 값 그대로(재측정 아님).
- **S_d 행**: ① 포화 VDSAT <= VDS ② 속도 f_T = GM/(2 pi CGG) >= f_req(**C 열 CGG 포함**, gbw 선언 9회로만; M-J1 그대로, f_T는 자기 CGG만 본 필요조건이라 느슨함) ③ **최소 폭**: W = ID L / IDu >= W_min  <=>  ID_node(W_ref) <= ID_dev x W_ref / W_min, **W_min = PDK 선언 `min_finger_w_m` = difftap.2 = 0.42 um**(`periphery.csv` 321행에서 읽음) ④ [K10] **반전 수준 하한**: 노드 >= 그 (L, VDS, VSB) 곡선 gm/ID 가장 왼쪽 argmax(floor_m = 곡선 전체 기준; M-J1 '정점' 정의) ⑤ [K10] **전도 여유**: I_off <= (gm/ID) tol_V ID  <=>  GM(노드) tol_V >= ID(VGS = 0 노드)(같은 W, I_off = LUT VGS = 0 누설, 계획 DEC-88 봉인 9). tol_V **예시 3 경우**: 0.1 mV · 1 mV · **LOO 셀값**.
- **LOO tol_V 셀값**: 엔진 `gmid_engine.lut.tol_v_table`(읽기 전용 import, 규칙 선언 경로 미사용)의 `id_equivalent_v`(W 5 um 슬라이스, (L 앵커, VDS) 칸 최댓값). nfet 2.5e-6~4.5e-2 V(중앙 2.4e-3), pfet 3.3e-6~2.3e-2 V(중앙 3.7e-3). **tol_V 정본 지표(`id_equivalent_v` 대 `gm_id_inverse_v`)와 셀 구성은 Q-T0 미결이라 예시값**이다.
- 변형: **D1** = ①②③④⑤ / **D2+** = ①②③⑤ / **D2** = ①②③(ID > 0 노드 전부). 격자 노드의 ln IDu는 VGS에 엄격 증가라 'S_d 아래 끝' = 가장 낮은 VGS 노드.
- **출발점**(design 41 §6.1-9 칸 0 = 면적 <= 예산인 최대 t*): 면적 W L = ID_dev L W_ref / ID_node는 ln IDu에 대해 감소라 실행 가능 집합은 위 끝 쪽 집합이다. (가) 시도점 = S_d 가장 낮은 노드, t* = S_d ∩ 면적 실행 가능 가운데 가장 낮은 노드. (나) 시도점 = S_d 안 gm/ID 가장 왼쪽 argmax, t* = 그 노드 이상에서 S_d ∩ 면적 실행 가능인 가장 낮은 노드(**(나)의 t 매개화는 설계에 정의가 없어 이렇게 둠 -- 표지**). t*는 격자 노드 단위(37.5 mV)이며 bracket_root 연속 경계가 아니다.
- **면적 예산 경우**(spec `area_search_m2`; cnr_ota·erfc_ota·r2r_opamp·rfc_ota 4회로는 **예산 선언 없음 -> 면적이 출발점을 못 옮긴다**, 나머지 9회로 선언 = 소자 48): `none` = 예산 무시(S_d만) / `full` = 소자 하나가 예산 전체 B를 쓴다(필요조건, 옮김의 하한) / `share` = B / n_SF(회로 S·F 수) 균등 몫(**가정이 아니라 경우 나눔**). **B 역할 소자(부하·미러·tail)와 수동소자 면적은 뺐다** -> 실제 예산 압박은 더 크다(옮김은 하한).
- **ID_dev 경우 나눔 1e-7·1e-6·1e-5·1e-4·1e-3 A**: gm_req(매크로)·KCL 전류를 엔진 없이 못 재서(§4 한계 1) 값을 주장하지 않고 5칸으로 나눴다.
- 조합: S_d 7종({D1,D2+} x tol 3 + D2) x 규칙 2 x ID 5 x 예산(3 또는 1). 소자마다 1줄(`devices_j1b.jsonl`)에 시도점·t*의 ln IDu·VGS·gm/ID·W의 [최소, 중앙, 최대](설정 분포)와 `moved`(t* != 시도점 설정 수)·`leak_att`·`leak_ts`(tol별)가 있다. 조합 키(`ID1e-05`)가 ID 값이다.

## 2. 변형별 표

### 2.1 누설 영역 출발 n/N (시도점, 면적 예산 무관; N = 115 = S 52 + F 63; ID = 1e-5 A 값)

누설 영역 = 전도 여유 행 위반(I_off > (gm/ID) tol_V ID). '다수' = 그 소자의 S_d 비지 않은 설정 중 >= 50 %에서 시도점이 누설, '1개 이상' = 설정 하나라도. ID 5칸 사이 다수 열은 같고 '1개 이상' 열은 (나) D2에서만 S 13~16으로 달라진다.

| 변형 | 규칙 | tol_V | 다수 S | 다수 F | 1개 이상 S | 1개 이상 F | 비고 |
|---|---|---|---|---|---|---|---|
| D1 | (가) 아래 끝 | 0.1 mV | 0/52 | 0/63 | 0/52 | 0/63 | 행이 전도 여유를 요구 -> 정의상 0 |
| D1 | (가) 아래 끝 | 1 mV | 0/52 | 0/63 | 0/52 | 0/63 | 행이 전도 여유를 요구 -> 정의상 0 |
| D1 | (가) 아래 끝 | LOO | 0/52 | 0/63 | 0/52 | 0/63 | 행이 전도 여유를 요구 -> 정의상 0 |
| D2+ | (가) 아래 끝 | 0.1 mV | 0/52 | 0/63 | 0/52 | 0/63 | 행이 전도 여유를 요구 -> 정의상 0 |
| D2+ | (가) 아래 끝 | 1 mV | 0/52 | 0/63 | 0/52 | 0/63 | 행이 전도 여유를 요구 -> 정의상 0 |
| D2+ | (가) 아래 끝 | LOO | 0/52 | 0/63 | 0/52 | 0/63 | 행이 전도 여유를 요구 -> 정의상 0 |
| D2 | (가) 아래 끝 | 0.1 mV | 0/52 | 25/63 | 24/52 | 38/63 |  |
| D2 | (가) 아래 끝 | 1 mV | 0/52 | 25/63 | 18/52 | 32/63 | 다수 F = gbw 없는 4회로 |
| D2 | (가) 아래 끝 | LOO | 0/52 | 25/63 | 17/52 | 31/63 |  |
| D1 | (나) argmax | 0.1 mV | 0/52 | 0/63 | 0/52 | 0/63 | 행이 전도 여유를 요구 -> 정의상 0 |
| D1 | (나) argmax | 1 mV | 0/52 | 0/63 | 0/52 | 0/63 | 행이 전도 여유를 요구 -> 정의상 0 |
| D1 | (나) argmax | LOO | 0/52 | 0/63 | 0/52 | 0/63 | 행이 전도 여유를 요구 -> 정의상 0 |
| D2+ | (나) argmax | 0.1 mV | 0/52 | 0/63 | 0/52 | 0/63 | 행이 전도 여유를 요구 -> 정의상 0 |
| D2+ | (나) argmax | 1 mV | 0/52 | 0/63 | 0/52 | 0/63 | 행이 전도 여유를 요구 -> 정의상 0 |
| D2+ | (나) argmax | LOO | 0/52 | 0/63 | 0/52 | 0/63 | 행이 전도 여유를 요구 -> 정의상 0 |
| D2 | (나) argmax | 0.1 mV | 0/52 | 25/63 | 13/52 | 27/63 |  |
| D2 | (나) argmax | 1 mV | 0/52 | 25/63 | 13/52 | 27/63 |  |
| D2 | (나) argmax | LOO | 0/52 | 25/63 | 17/52 | 31/63 |  |

D2의 누설 출발 F 25 = gbw 선언 없는 4회로(속도 행 없음)의 F 전부. gbw 선언 회로의 S·F는 속도 행이 아래 끝을 올려 다수 설정에서 누설이 아니다('1개 이상' S 17~24는 낮은 f_req(2~12 MHz)에서 VGS = 0 노드가 속도 행을 통과하는 설정).

### 2.2 면적 예산 적용 뒤 t*의 누설 영역 (D2만 해당; D1·D2+는 0), 예산 회로 N = 48 (S 16 + F 32), tol_V = 1 mV

| 규칙 | 예산 | ID 1e-7 | ID 1e-6 | ID 1e-5 | ID 1e-4 | ID 1e-3 |
|---|---|---|---|---|---|---|
| (가) | none | 다수 S 0·F 25 / 1개↑ S 3·F 25 | 다수 S 0·F 25 / 1개↑ S 3·F 25 | 다수 S 0·F 25 / 1개↑ S 3·F 25 | 다수 S 0·F 25 / 1개↑ S 3·F 25 | 다수 S 0·F 25 / 1개↑ S 3·F 25 |
| (가) | full | 다수 S 0·F 2 / 1개↑ S 3·F 25 | 다수 S 0·F 0 / 1개↑ S 3·F 20 | 다수 S 0·F 0 / 1개↑ S 3·F 14 | 다수 S 0·F 0 / 1개↑ S 3·F 10 | 다수 S 0·F 0 / 1개↑ S 0·F 2 |
| (가) | share | 다수 S 0·F 0 / 1개↑ S 3·F 25 | 다수 S 0·F 0 / 1개↑ S 3·F 12 | 다수 S 0·F 0 / 1개↑ S 3·F 12 | 다수 S 0·F 0 / 1개↑ S 1·F 0 | 다수 S 0·F 0 / 1개↑ S 0·F 0 |
| (나) | none | 다수 S 0·F 25 / 1개↑ S 3·F 25 | 다수 S 0·F 25 / 1개↑ S 3·F 25 | 다수 S 0·F 25 / 1개↑ S 3·F 25 | 다수 S 0·F 25 / 1개↑ S 3·F 25 | 다수 S 0·F 25 / 1개↑ S 3·F 25 |
| (나) | full | 다수 S 0·F 2 / 1개↑ S 3·F 25 | 다수 S 0·F 0 / 1개↑ S 3·F 20 | 다수 S 0·F 0 / 1개↑ S 3·F 14 | 다수 S 0·F 0 / 1개↑ S 3·F 10 | 다수 S 0·F 0 / 1개↑ S 0·F 2 |
| (나) | share | 다수 S 0·F 0 / 1개↑ S 3·F 25 | 다수 S 0·F 0 / 1개↑ S 3·F 12 | 다수 S 0·F 0 / 1개↑ S 3·F 12 | 다수 S 0·F 0 / 1개↑ S 1·F 0 | 다수 S 0·F 0 / 1개↑ S 0·F 0 |

### 2.3 면적 예산이 시도점을 옮긴 소자 수 (예산 회로 N = 48: S 16·F 32; '다수' = 비지 않은 설정 중 >= 50 %에서 t* != 시도점)

D1·D2+·D2와 (가)·(나)에서 거의 같아(차 <= 2 소자: D2의 F ID 1e-7 25 대 D1 23) 한 표로 둔다(D1, (가), tol 1 mV 값; 전수는 `devices_j1b.jsonl`).

| 예산 | ID 1e-7 | ID 1e-6 | ID 1e-5 | ID 1e-4 | ID 1e-3 |
|---|---|---|---|---|---|
| full | S 0/16 · F 23/32 (1개↑ S 0·F 25) | S 0/16 · F 25/32 (1개↑ S 0·F 25) | S 0/16 · F 25/32 (1개↑ S 0·F 25) | S 3/16 · F 27/32 (1개↑ S 4·F 27) | S 12/16 · F 28/32 (1개↑ S 14·F 28) |
| share | S 0/16 · F 25/32 (1개↑ S 0·F 25) | S 0/16 · F 25/32 (1개↑ S 0·F 25) | S 0/16 · F 25/32 (1개↑ S 4·F 27) | S 4/16 · F 27/32 (1개↑ S 9·F 28) | S 14/16 · F 28/32 (1개↑ S 16·F 32) |

옮김 크기(D1 (가) full, 소자별 설정 중앙값의 t* - 시도점 ln IDu 차):

| ID | S 중앙 / p90 / 최대 | F 중앙 / p90 / 최대 |
|---|---|---|
| 1e-7 | 0.00 / 0.00 / 0.00 | 6.20 / 17.83 / 18.74 |
| 1e-6 | 0.00 / 0.00 / 0.00 | 8.48 / 19.98 / 20.90 |
| 1e-5 | 0.00 / 0.00 / 0.00 | 11.00 / 22.20 / 22.95 |
| 1e-4 | 0.00 / 1.01 / 1.19 | 13.38 / 24.37 / 25.12 |
| 1e-3 | 1.21 / 3.18 / 3.27 | 15.40 / 26.52 / 27.20 |

(ln IDu 1 = 전류 밀도 e배. F의 옮김 6~27은 전도 여유 경계(약반전, W 수 mm~m 급)에서 예산이 허락하는 강한 반전 쪽으로 e^6~e^27배 올라간다는 뜻이다. 예산 하한 계산에서도 그렇다.)

### 2.4 t* 차 분포 (S·F 따로, nfet·pfet 따로; 설정 pool)

각 칸 = 차 있음 비율 (ln IDu 차 > 1 비율) / |Δ ln IDu| p90·max / |ΔVGS| p90·max(V) / |Δgm/ID| max(S/A). 차 = 같은 설정에서 두 변형 t*의 값 차(둘 다 정의된 설정만). K10 = 앞 변형 - 뒤 변형, K3 = (나) - (가). **ID = 1e-5 A, tol_V = 1 mV**. 전수(ID 5칸·tol 3·예산 3) = `tables_j1b.txt`.

**예산 무시(S_d만의 차)**

| 비교 | 규칙 | S nfet | S pfet | F nfet | F pfet |
|---|---|---|---|---|---|
| K10 D1 - D2+ | (가) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.5% (>e배 0.5%) / lnIDu p90 0.00 max 1.28 / VGS p90 0.000 max 0.038 / gm/ID max 0.00 |
| K10 D1 - D2+ | (나) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 |
| K10 D1 - D2 | (가) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.1% (>e배 0.1%) / lnIDu p90 0.00 max 2.28 / VGS p90 0.000 max 0.150 / gm/ID max 2.44 | 34.5% (>e배 34.5%) / lnIDu p90 4.45 max 4.64 / VGS p90 0.150 max 0.188 / gm/ID max 0.10 | 41.3% (>e배 41.3%) / lnIDu p90 4.29 max 5.13 / VGS p90 0.150 max 0.262 / gm/ID max 9.41 |
| K10 D1 - D2 | (나) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.1% (>e배 0.1%) / lnIDu p90 0.00 max 6.22 / VGS p90 0.000 max 0.412 / gm/ID max 1.51 | 34.5% (>e배 34.5%) / lnIDu p90 4.45 max 4.64 / VGS p90 0.150 max 0.188 / gm/ID max 0.10 | 39.8% (>e배 39.8%) / lnIDu p90 4.37 max 9.76 / VGS p90 0.150 max 0.600 / gm/ID max 9.41 |
| K10 D2+ - D2 | (가) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.1% (>e배 0.1%) / lnIDu p90 0.00 max 2.28 / VGS p90 0.000 max 0.150 / gm/ID max 2.44 | 34.5% (>e배 34.5%) / lnIDu p90 4.45 max 4.64 / VGS p90 0.150 max 0.188 / gm/ID max 0.10 | 41.3% (>e배 41.3%) / lnIDu p90 4.28 max 4.69 / VGS p90 0.150 max 0.262 / gm/ID max 9.41 |
| K10 D2+ - D2 | (나) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.1% (>e배 0.1%) / lnIDu p90 0.00 max 6.22 / VGS p90 0.000 max 0.412 / gm/ID max 1.51 | 34.5% (>e배 34.5%) / lnIDu p90 4.45 max 4.64 / VGS p90 0.150 max 0.188 / gm/ID max 0.10 | 39.8% (>e배 39.8%) / lnIDu p90 4.37 max 9.76 / VGS p90 0.150 max 0.600 / gm/ID max 9.41 |
| K3 (나)-(가) [D1] | - | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 17.4% (>e배 10.1%) / lnIDu p90 0.68 max 6.31 / VGS p90 0.038 max 0.375 / gm/ID max 1.17 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 11.2% (>e배 8.6%) / lnIDu p90 0.67 max 6.19 / VGS p90 0.038 max 0.375 / gm/ID max 1.16 |
| K3 (나)-(가) [D2+] | - | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 17.4% (>e배 10.1%) / lnIDu p90 0.68 max 6.31 / VGS p90 0.038 max 0.375 / gm/ID max 1.17 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 11.7% (>e배 9.0%) / lnIDu p90 0.67 max 6.19 / VGS p90 0.038 max 0.375 / gm/ID max 1.16 |
| K3 (나)-(가) [D2] | - | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 17.3% (>e배 10.0%) / lnIDu p90 0.67 max 6.31 / VGS p90 0.038 max 0.375 / gm/ID max 1.17 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 17.3% (>e배 14.7%) / lnIDu p90 1.26 max 6.19 / VGS p90 0.038 max 0.375 / gm/ID max 1.16 |

**예산 full**

| 비교 | 규칙 | S nfet | S pfet | F nfet | F pfet |
|---|---|---|---|---|---|
| K10 D1 - D2+ | (가) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 |
| K10 D1 - D2+ | (나) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 |
| K10 D1 - D2 | (가) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.2% (>e배 0.1%) / lnIDu p90 0.00 max 2.28 / VGS p90 0.000 max 0.150 / gm/ID max 2.44 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.88 / VGS p90 0.000 max 0.038 / gm/ID max 0.01 | 0.8% (>e배 0.5%) / lnIDu p90 0.00 max 4.62 / VGS p90 0.000 max 0.262 / gm/ID max 8.22 |
| K10 D1 - D2 | (나) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.2% (>e배 0.1%) / lnIDu p90 0.00 max 6.22 / VGS p90 0.000 max 0.412 / gm/ID max 1.51 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.88 / VGS p90 0.000 max 0.038 / gm/ID max 0.01 | 0.8% (>e배 0.5%) / lnIDu p90 0.00 max 8.98 / VGS p90 0.000 max 0.562 / gm/ID max 7.42 |
| K10 D2+ - D2 | (가) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.2% (>e배 0.1%) / lnIDu p90 0.00 max 2.28 / VGS p90 0.000 max 0.150 / gm/ID max 2.44 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.88 / VGS p90 0.000 max 0.038 / gm/ID max 0.01 | 0.8% (>e배 0.5%) / lnIDu p90 0.00 max 4.62 / VGS p90 0.000 max 0.262 / gm/ID max 8.22 |
| K10 D2+ - D2 | (나) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.2% (>e배 0.1%) / lnIDu p90 0.00 max 6.22 / VGS p90 0.000 max 0.412 / gm/ID max 1.51 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.88 / VGS p90 0.000 max 0.038 / gm/ID max 0.01 | 0.8% (>e배 0.5%) / lnIDu p90 0.00 max 8.98 / VGS p90 0.000 max 0.562 / gm/ID max 7.42 |
| K3 (나)-(가) [D1] | - | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 16.4% (>e배 11.7%) / lnIDu p90 1.32 max 6.31 / VGS p90 0.075 max 0.375 / gm/ID max 1.17 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 5.0% (>e배 4.0%) / lnIDu p90 0.00 max 5.48 / VGS p90 0.000 max 0.375 / gm/ID max 0.98 |
| K3 (나)-(가) [D2+] | - | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 16.4% (>e배 11.7%) / lnIDu p90 1.32 max 6.31 / VGS p90 0.075 max 0.375 / gm/ID max 1.17 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 5.0% (>e배 4.0%) / lnIDu p90 0.00 max 5.48 / VGS p90 0.000 max 0.375 / gm/ID max 0.98 |
| K3 (나)-(가) [D2] | - | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 16.3% (>e배 11.6%) / lnIDu p90 0.69 max 6.31 / VGS p90 0.038 max 0.375 / gm/ID max 1.17 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 4.8% (>e배 3.8%) / lnIDu p90 0.00 max 1.97 / VGS p90 0.000 max 0.112 / gm/ID max 0.81 |

**예산 share**

| 비교 | 규칙 | S nfet | S pfet | F nfet | F pfet |
|---|---|---|---|---|---|
| K10 D1 - D2+ | (가) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 |
| K10 D1 - D2+ | (나) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 |
| K10 D1 - D2 | (가) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.2% (>e배 0.1%) / lnIDu p90 0.00 max 2.28 / VGS p90 0.000 max 0.150 / gm/ID max 2.44 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.1% (>e배 0.0%) / lnIDu p90 0.00 max 2.26 / VGS p90 0.000 max 0.150 / gm/ID max 2.21 |
| K10 D1 - D2 | (나) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.2% (>e배 0.1%) / lnIDu p90 0.00 max 6.22 / VGS p90 0.000 max 0.412 / gm/ID max 1.51 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.2% (>e배 0.1%) / lnIDu p90 0.00 max 6.09 / VGS p90 0.000 max 0.412 / gm/ID max 1.38 |
| K10 D2+ - D2 | (가) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.2% (>e배 0.1%) / lnIDu p90 0.00 max 2.28 / VGS p90 0.000 max 0.150 / gm/ID max 2.44 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.1% (>e배 0.0%) / lnIDu p90 0.00 max 2.26 / VGS p90 0.000 max 0.150 / gm/ID max 2.21 |
| K10 D2+ - D2 | (나) | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.2% (>e배 0.1%) / lnIDu p90 0.00 max 6.22 / VGS p90 0.000 max 0.412 / gm/ID max 1.51 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 0.2% (>e배 0.1%) / lnIDu p90 0.00 max 6.09 / VGS p90 0.000 max 0.412 / gm/ID max 1.38 |
| K3 (나)-(가) [D1] | - | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 15.5% (>e배 10.6%) / lnIDu p90 0.69 max 6.31 / VGS p90 0.038 max 0.375 / gm/ID max 1.17 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 5.0% (>e배 4.0%) / lnIDu p90 0.00 max 5.48 / VGS p90 0.000 max 0.375 / gm/ID max 0.98 |
| K3 (나)-(가) [D2+] | - | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 15.5% (>e배 10.6%) / lnIDu p90 0.69 max 6.31 / VGS p90 0.038 max 0.375 / gm/ID max 1.17 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 5.0% (>e배 4.0%) / lnIDu p90 0.00 max 5.48 / VGS p90 0.000 max 0.375 / gm/ID max 0.98 |
| K3 (나)-(가) [D2] | - | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 15.4% (>e배 10.5%) / lnIDu p90 0.69 max 6.31 / VGS p90 0.038 max 0.375 / gm/ID max 1.17 | 0.0% (>e배 0.0%) / lnIDu p90 0.00 max 0.00 / VGS p90 0.000 max 0.000 / gm/ID max 0.00 | 4.8% (>e배 3.8%) / lnIDu p90 0.00 max 1.97 / VGS p90 0.000 max 0.112 / gm/ID max 0.81 |

tol_V 감도(예산 무시, (가), ID 1e-5, D2+ - D2: 아래 끝에서 전도 여유 경계까지의 거리):

| tol_V | S nfet | S pfet | F nfet | F pfet |
|---|---|---|---|---|
| 0.1 mV | 0.0% / lnIDu p90 0.00 / VGS p90 0.000 max 0.000 | 0.8% / lnIDu p90 0.00 / VGS p90 0.000 max 0.338 | 34.5% / lnIDu p90 6.71 / VGS p90 0.225 max 0.262 | 41.6% / lnIDu p90 6.39 / VGS p90 0.225 max 0.450 |
| 1 mV | 0.0% / lnIDu p90 0.00 / VGS p90 0.000 max 0.000 | 0.1% / lnIDu p90 0.00 / VGS p90 0.000 max 0.150 | 34.5% / lnIDu p90 4.45 / VGS p90 0.150 max 0.188 | 41.3% / lnIDu p90 4.28 / VGS p90 0.150 max 0.262 |
| LOO 셀값 | 0.5% / lnIDu p90 0.00 / VGS p90 0.000 max 0.112 | 0.0% / lnIDu p90 0.00 / VGS p90 0.000 max 0.075 | 34.3% / lnIDu p90 9.21 / VGS p90 0.338 max 0.412 | 41.3% / lnIDu p90 8.85 / VGS p90 0.262 max 0.412 |

D1 - D2+ (반전 수준 하한 행의 추가 효과)은 pfet F에서만 난다: 차 있음 비율 t0p1mV 0.01%(lnIDu max 0.0), t1mV 0.46%(lnIDu max 1.3), tLOO 1.60%(lnIDu max 3.8). nfet·S는 전 tol에서 0.

### 2.5 t* 차가 0이 아닌 소자가 남는 회로 (card LA-1 변화표로 넘길 후보; 표지만)

소자별 t* 분포([최소, 중앙, 최대])의 ln IDu·VGS 중 하나라도 두 조합에서 다르면 '차 있음'(근사 판정 -- 설정 단위 정확 비교는 §2.4). 예산 회로 48소자, ID 1e-5, tol 1 mV.

| 비교 | 예산 | S | F | 회로(차 있는 소자/예산 회로 소자) |
|---|---|---|---|---|
| K10 D1 vs D2 | full | 3/16 | 14/32 | current_reuse_telescopic_ota 10/16; folded_cascode 2/4; nmcnr_amplifier 3/6; pushpull_follower_buffer 2/4 |
| K10 D1 vs D2 | share | 3/16 | 10/32 | current_reuse_telescopic_ota 8/16; folded_cascode 2/4; nmcnr_amplifier 3/6 |
| K10 D1 vs D2+ | full | 0/16 | 0/32 |  |
| K10 D1 vs D2+ | share | 0/16 | 0/32 |  |
| K3 (가)/(나) [D1] | full | 7/16 | 6/32 | folded_cascode 2/4; ngcc_3stage_ff 2/4; nmcnr_amplifier 3/6; pushpull_follower_buffer 2/4; sf_pushpull_output_opamp 2/6; two_stage_ota 1/3; two_stage_ota_sf 1/4 |
| K3 (가)/(나) [D1] | share | 7/16 | 14/32 | current_reuse_telescopic_ota 8/16; folded_cascode 2/4; ngcc_3stage_ff 2/4; nmcnr_amplifier 3/6; pushpull_follower_buffer 2/4; sf_pushpull_output_opamp 2/6; two_stage_ota 1/3; two_stage_ota_sf 1/4 |
| K3 (가)/(나) [D2] | full | 6/16 | 2/32 | ngcc_3stage_ff 2/4; nmcnr_amplifier 2/6; sf_pushpull_output_opamp 2/6; two_stage_ota 1/3; two_stage_ota_sf 1/4 |
| K3 (가)/(나) [D2] | share | 6/16 | 2/32 | ngcc_3stage_ff 2/4; nmcnr_amplifier 2/6; sf_pushpull_output_opamp 2/6; two_stage_ota 1/3; two_stage_ota_sf 1/4 |

예산 없는 4회로(cnr_ota·erfc_ota·r2r_opamp·rfc_ota; 67소자)는 면적이 출발점을 못 옮기므로 §2.1 시도점 표와 같다: 이 회로의 S·F는 전부 gbw 선언이 있어 속도 행이 있고 D1·D2+·D2 모두 같은 속도 행 아래 끝에서 출발하며 누설 출발 0이다.

## 3. 해석 표지 (판정 아님)

- **K10 선택의 실효**: 누설 영역 출발은 D2에서만 나고, 그것은 속도 행이 없는 회로(gbw 선언 없는 4회로, F 25소자)에 한정된다. 이 4회로는 모두 면적 예산이 있어 예산이 출발점을 올리므로, **t*에서의 D1·D2+·D2 차는 예산을 적용하면 거의 사라진다**(§2.4 예산 full/share: 차 있음 비율 0.0~0.8 %, 단 ID 1e-7 쪽 F nfet 2.4 %·F pfet 3.7 %). 다만 이것은 '출발점이 같아진다'가 아니라 '예산 경계가 출발점을 정한다'이다 -- t*가 약반전~중간반전의 면적 경계(W 수 mm~m 급)에 놓이는 것은 B36-M1 3(nfet VGS 0 근처에서 1 uA에 W ~ km)과 같은 종류의 현상이다.
- **D1 대 D2+**: 반전 수준 하한 행은 nfet에서 공허(정점 = VGS 0)하고 pfet 일부에서만 전도 여유 경계 위로 S_d를 더 자른다. 이 행의 pfet 정점은 약반전 plateau 반올림이 정하므로(M-J1 §4.6, 상대차 <= 1.3e-6) 그 차의 위치 자체가 수치 잡음이다. tol_V가 클수록 D1 - D2+ 차 비율이 커진다(0.1 mV 0.01 % -> 1 mV 0.46 % -> LOO 1.6 %).
- **전도 여유 경계 위치가 tol_V에 의존한다**: D2+ 경계까지 ln IDu 거리 p90 = 6.4~6.7(0.1 mV) / 4.3~4.4(1 mV) / 8.8~9.2(LOO)이다. LOO가 1 mV보다 더 먼 이유는 LOO 셀값이 이봉이기 때문이다: VDS >= 0.3 V 셀(18 L x 41) 중 1/3은 0.1 mV 미만(최소 2.5e-6 V)이고 2/3는 1 mV 초과(중앙 2.0~3.4 mV)다. 앞 1/3 셀의 전도 여유 경계가 더 높은 VGS에 있다(L 앵커별 분해는 하지 않았다).
- **K3 (가) 대 (나)**: 면적 예산과 무관하게 pfet의 설정 5~17 %에서 갈린다. nfet 0. 예산 full/share에서도 S pfet 15~16 %가 남는다(속도 행으로 아래 끝이 골짜기에 놓이는 소자, M-J1의 39/115 군). 이 차는 K10 선택(D1·D2+·D2)과 거의 무관하게 같다.
- **S 대 F**: S는 속도 행(gbw 선언 회로)이 아래 끝을 강반전~중간반전으로 올려 K10 차가 0이고 면적 예산도 ID <= 1e-5에서 못 옮긴다(옮김 0). F는 gbw 선언 없는 4회로에서 속도 행이 없어 K10이 직접 갈리고 예산이 크게 옮긴다. 전력 논거(K3 '물리 결정자')는 S에만 있으므로 위 F 결과는 K3 (가)/(나) 자체의 근거가 되지 못한다.

## 4. 한계

1. **엔진 경로 불가 -- ID 경우 나눔**: S의 gm_req(매크로 풀이 -- 보상 커패시터 Cc는 spec 상자 [0.1, 10] pF 안에서 엔진이 정함)와 F의 §6.5 1회차 전류는 `start_intervals`(`current_model`+`macro_solve`)를 불러야 얻는다. 이번 환경에서 엔진 경로(`run_stage_a`)는 `pdk_source_sha256_mismatch`(`sky130_lut_rule_decl.json`이 선언한 `sky130_lut_sweep.py` sha256과 현 master 파일의 LF 정규화 해시가 다름, **측정 전부터 있는 상태**)로 거부된다. 해시 검사를 우회해서 돌리는 것은 하지 않았다(첫 시도에서 자동 모드 판정기가 그 우회를 거부). 그래서 ID를 값으로 주장하지 않고 5칸으로 나눴다. **선언 sha256이 정정(또는 우회 승인)되면 `start_intervals._state`를 가로채는 읽기 전용 프로브(`probe_engine.py`, 작성만 됨·미실행; 우회 코드는 넣지 않았다)로 S의 gm_req와 F 1회차 전류를 실제 값으로 바꿔 §2.2~2.5를 다시 잴 수 있다.**
2. **면적 예산은 필요조건(하한)**: 소자 하나가 예산 전체(full) 또는 균등 몫(share)을 쓴다고 보았고, B 역할 소자·수동소자·다른 S·F 소자 합산은 뺐다. 실제 예산 압박은 더 크고 t*는 더 위쪽이다. 소자 합이 예산을 넘는 회로는 `share`보다 더 작은 몫이 맞다.
3. **매크로 근 조건 미반영**(정의대로 뺌): 실제 칸 0은 '면적 <= 예산 그리고 매크로 근 있음'이므로 t*는 더 위쪽으로 갈 수 있다. 면적 조건 행(§6.4-2, 절대 offset 제약 current_reuse 1/13)·부하 가드·잡음 가드·헤드룸 V_part 분할은 상한 행이라 (가) 시도점에는 영향이 없고 (나)의 argmax가 잘리는 설정에서만 영향이 있다.
4. **속도 행은 f_T 필요조건**(M-J1 한계 2와 같음, 자기 CGG만 봄)이라 실제 f_np 행이면 아래 끝이 더 올라간다 -> 속도 행이 있는 S의 K10 차는 더 작아질 수 있다.
5. **tol_V는 예시**: 0.1·1 mV와 LOO `id_equivalent_v`(W 5 um 슬라이스, (L 앵커, VDS) 셀의 VGS·VS 최댓값). 엔진이 `device.dc_tol_v`로 쓰는 지표·셀 구성은 Q-T0 미결이다.
6. **격자 동일 가중**: (L, VDS, VSB) 설정을 모두 같은 가중으로 센다(엔진이 실제로 고르는 점의 분포 아님). 면적은 L에 비례하므로 L이 큰 설정이 예산에 먼저 걸린다. S·F 소자 수는 소자 수이지 궤도 수가 아니다(M-J1 한계 5와 같음).
7. **t*는 격자 노드**(37.5 mV): 면적 경계가 노드 사이에 있으면 한 노드 위(안전 쪽)로 잡힌다. 약반전에서 노드 한 칸 ≈ ln IDu 1(e배)이다.
8. **(나)의 t 매개화**는 설계에 정의가 없다(§6.1-9의 t = 1은 선택 끝). 여기서는 argmax 노드 이상에서 면적 실행 가능한 가장 낮은 노드로 둠.
9. **LUT는 W_ref 5 um 슬라이스 하나**, tol_V 셀도 같은 슬라이스. 다른 W bin·보간 L 미사용.

## 5. front 차

**엔진 수정 없이 불가**(출발 선택을 J1 대 옛 규칙·D1/D2+/D2로 갈라 두 번 돌려야 하고 저장소 쓰기 0이며, 위 sha256 거부로 엔진 경로 자체가 막혔다). t* 차가 0이 아닌 소자가 남는 회로 = §2.5 표의 회로를 card LA-1 변화표(U-124 측정과 같은 판)로 넘길 후보로만 표지한다.

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
