# current_reuse class-AB 부유 배터리 -- 물리 결정자 계획 점검 (2026-10-29)

사용자 지시: "current_reuse 배터리 결정자도 계획에서 점검해". 읽기·측정만 했다(문서·코드 수정 0).
계획 기준: master `gain-budget-gmid-sizing.plan.md` v6.38.4(O-173). 줄 번호는 worktree `wt/plan-v6385` HEAD `6276faf1`(v6.38.5) 기준이다. v6.38.5 diff에서 class-AB 관련 문언 변경은 0이다. Q-ZG1의 '부유 전지'는 erfc CBAT(커패시터 전지, DR-1)라서 이 꼴과 다르다.
증거 폴더: `wt/_drafts/evidence/2026-10-29/classab_battery/`
- 스크립트: `s1_cycles.py`, `writer_plan.py`, `bench.py`, `design.py`, `rep_point.py`, `run_all.py`, `scan13.py`
- 출력: `*.out.txt`, `results.jsonl`, `design_out.jsonl`, `all_out.jsonl`, `ac_mag.txt`, `runs/`

원문: Xie & Chen, 'A 126µW Current-Reuse Telescopic OTA with Class-AB Output Stage', `assets/library/sources/current_reuse_telescopic_ota__xie_chen_2019/source.pdf`
- p.2 §II.B: class-AB, "barely-on", Vop1 ≈ 0.5 V가 1단 NMOS 헤드룸을 누름
- p.7 Fig.7(a)(b): 치수와 DC 동작점
- 웹 링크는 찾지 못했다(spec 기록과 같다).

## 0. 연결 판독 (태그 미사용, topology.json `netlist`에서 직접 읽음) -- 오케스트레이터 1차 판독 **확인**

| 소자 | D | G | S | 역할(연결로 유도) |
|---|---|---|---|---|
| M15 pmos | Vom | Vg15 | vdd | 출력 push |
| M16 nmos | Vom | Vop1 | gnd | 출력 pull. gate = 1단 출력 Vop1이 직접 구동 |
| M9a pmos | Vop1 | N11b | Vg15 | 부유 배터리. 채널 Vg15↔Vop1 |
| M9b nmos | Vg15 | N14a14b | Vop1 | 부유 배터리. 상보 병렬 |
| M11a / M11b pmos | 다이오드 사슬 | | vdd→N11a11b→N11b | M12 싱크(N11b) |
| M14b / M14a nmos | 다이오드 사슬 | | gnd→N14a_14b→N14a14b | M13 소스(N14a14b) |
| M8 pmos | Vg15 | Vbias1 | vdd | 배터리 전류원 |
| M10 nmos | Vop1 | Vbias4 | gnd | 배터리 전류 싱크 |

- 반대쪽은 M18a/M18b(Vg25↔Vom1), M20a/M20b + M21, M22 + M23a/M24b, M17, M19, M25/M26으로 같은 꼴이다.
- 엔진 `s1_gvgs` 실측(`s1_cycles.out.txt`): `kvl_branch`(v2_rail)는 정확히 4개다. 이 넷이 곧 translinear 고리다.
  - {M11a, M11b, M15, M9a}: VSG11a + VSG11b = VSG15 + VSG9a
  - {M14a, M14b, M16, M9b}: VGS14a + VGS14b = VGS16 + VGS9b
  - 대칭 2개
- J12-c의 열린 물음('파일럿 레일 경유 4사이클이 J3 정지전류 루프와 같은가')은 **같다**로 답할 수 있다.
- 원문 Fig.7(b)에서 고리를 손으로 확인했다(같은 공정 안에서 원문이 이미 닫혀 있음).
  - pmos 고리: 0.4676 + 0.5999 = 1.0675 = 0.487 + 0.5806
  - nmos 고리: 0.584 + 0.478 = 1.062 = 0.475 + 0.587

## 1. 결정자별 표

| # | 물리 결정자(유도) | 계획 자리 | 엔진 계산(손계산) | 판정 | 확신도 |
|---|---|---|---|---|---|
| 1 | **정지 전류 I_Q**: 게이트-소스만으로 된 KVL 고리 두 개가 결정한다(레일 병합 ΔV = 0). 두 고리는 KCL I9a + I9b = I8(Vg15 마디)로 묶인다. 고정 W에서는 크기 비가 I_Q를 정한다. gm/ID 매개화에서는 VGS = f(gm/ID, L, VDS, VSB)에 ID가 없으므로 쌍대가 된다. 즉 I_Q·I9a·I8은 θ 전류이고, 고리마다 멤버 ln IDu 하나가 종속이다. | DEC-64 (v2) 263행, DEC-70 269행('루프 등식은 전류를 정하지 못하고 멤버 gm_id 하나를 종속'), DEC-104 (0)·R6·L-11 303행, `ID_source` theta_current 663행, 봉인 8(`sizing/seal_kvl_branch.py`), J3-dc 2362행(7b ratify), U-06 | **θ 기저 손계산 실측**: θ = (I_Q = 20 µA, I9a = I9b = 0.6 µA, 출력·다이오드 치수). 종속 소자 W는 고리 KVL로 정했다(M9a 23.4 µm, M9b 1.93 µm). 같은 W로 전체 SPICE를 돌리면 I_Q = 19.997 µA(−0.014 %), 분배 0.5999 / 0.6001 µA였다(`design_out.jsonl`). 고리 전압 오차 감도는 d ln I_Q/dδ = 5.8~6.3 /V이다(5 mV면 약 3 %, `all_out.jsonl` sens). O-127과 맞는다: translinear 고리는 KVL 종속 성분이다. | **맞음.** 단 종속 멤버 선택 문언이 충돌한다(아래 R-B). as-built 사실: 탐지 4/4, 봉인 8 판정 있음. θ 수준 R6 종속은 미구현(TB-1). 커널 쓰기 계획은 OrderHints 스텁이 미배선이라(sizing CONTRACT 14.4) **M15·M16을 dependent(cycle_vgs)**로, M9a·M9b·다이오드를 writer로 둔다(`writer_plan.out.txt`). 이는 DEC-95 (3)②('GB5 gm 요구 소자는 독립')와 다르다. | 물리 높음 / 문언 충돌 중 |
| 2 | **대신호 최소 전류(꺼지는 쪽)**: 한쪽이 세게 밀면 그쪽 배터리 소자 전류가 0으로 가고 반대쪽 배터리 소자가 I8 전부를 받는다. 그 고리 KVL에서 I_min이 정해진다. 약반전 닫힌 식은 I_min,16 = I_Q·I9b,Q/I8, I_min,15 = I_Q·I9a,Q/I8이다. | 명시 행 없음. 간접 자리 둘: DEC-65·DEC-104 R9(범위 끝 순 전류 = 미는 소자 조회 − '반대쪽 가지 전류(같은 극단 상태 그 가지 단자 전압으로 조회)'), 대신호 정착 = oracle `.tran`(O-132·O-134, SF-1) | 엔진 칸 0. 실측(I_L ±300 µA, Vom = 0.9 V 서보, `all_out.jsonl` imin): <br>• 분배 0.5/0.5: 0.54 / 0.40 (예측 0.50 / 0.50) <br>• 분배 0.25/0.75: 0.75 / 0.22 (예측 0.75 / 0.25) <br>• 분배 0.75/0.25: 0.27 / 0.56 (예측 0.25 / 0.75) <br>nmos 쪽은 8 % 안이다. pmos 쪽은 M9a 체적 효과 때문에 최대 26 % 벗어난다. 300 µA 밀 때 V_bat는 0.30 → 0.15 V로 줄고 Vop1은 거의 그대로다(Monticelli 거동). | **보고만으로 충분.** spec 제약이 없고(정착은 oracle), current_reuse의 R8 요구(R1·R2 감지 저항 전류, µA급)는 I_cap(수백 µA)보다 훨씬 작다. I_min 오차는 결정을 바꾸지 않는다(E-1 (a)). R9의 '반대쪽 단자 전압'이 배터리 결합 gate에서 정의되지 않은 것은 문언 공백이다(R-C). | 높음 |
| 3 | **배터리 기생 극점과 PM**: Vg15 마디의 저임피던스 단자는 M9a source다. M9b drain은 gds뿐이다. 극점 p ≈ (gm9a + gmb9a + gds9a + gds9b)/C(Vg15)이고, M15 gate C가 지배한다. M16 직접 경로와 병렬이라 doublet이 된다. 저주파 배터리 전달은 H0 = (gm9b + gmb9b + gds)/(gm9a + gmb9a + gds)로 1이 아니다. | DEC-25 225행(PM·기생 PM = 봉인 전체 MNA. 모든 MOS 스탬프, DEC-91 접합 C 포함), DEC-70 제약, R3 '극점 미포함' 규칙, 출발 매크로 = design 41 §6.5 | 판정 MNA가 자동으로 포함한다. 실측(`all_out.jsonl` battery_pole, `ac_mag.txt`): <br>• I8 = 0.6 / 1.2 / 2.4 / 4.8 µA에서 극점 3.2 / 6.3 / 11.9 / 25 MHz <br>• 손 식 7.0 MHz 대 실측 6.3 MHz(I8 = 1.2 µA) <br>• 원문 폐루프 대역 36.6 MHz(원문 식 (2))에서 2단 유효 Gm = DC의 0.48~0.63배, 위상 −6~−26° <br>• H0 = 1.40~1.53 <br>as-built 매크로(`search/macro_poles.py` 머리)의 마디 = 블록 출력 + 수동소자로만 닿는 넷이다. 그래서 Vg15는 없고 doublet도 없다. | **판정은 맞음**(MNA). 출발 매크로는 낙관적이다(R-D). 출발값은 판정에 쓰이지 않으므로(EP-7) fail-open이 아니다. E-2 조건부. | 높음 |
| 4 | **배터리 DC 헤드룸**: <br>• V_bat = V(Vg15) − V(Vop1) = vdd − VSG15 − VGS16 ≥ VDsat(M9a), VDsat(M9b) <br>• VSD8 = VSG15 ≥ VDsat8 <br>• VDS10 = VGS16 ≥ VDsat10 <br>• VDS12 = vdd − VSG11a − VSG11b(= vdd − VSG15 − VSG9a) ≥ VDsat12 <br>• VSD13 = vdd − VGS14a − VGS14b ≥ VDsat13 | DEC-27 227행(V_bat 일반형), DEC-64 VDS-1, headroom-chain R-1′(N3.1, 만드는 card TB-1, HC-1 소비자), 봉인 7(LUT VDSAT) | as-built VDS-1 행(`s1_cycles.out.txt`): (M9a, M16, M15), (M9b, M15, M16), (M8, M15), (M10, M16), (M12, M11b, M11a), (M13, M14a, M14b), 대칭 쪽 동일 -- 전부 있음. 대표점 실측: V_bat = 0.300 V, VDsat ≈ 0.05~0.06 V, V(N11b) = 0.24 V. sky130 pfet은 체적 효과가 커서 M12 여유가 빠듯하다. | **맞음**(일반 규칙이 다 덮는다). 단 spec의 `classab_centering_dev_v ≤ 0.15`(결정 대기 MOD5)는 물리 결정자가 없는 제약이다(R-A). | 높음 |
| 5 | **배터리 전압·정지 전류의 PVT 민감도**: 고리 멤버의 L이 서로 다르고(원문 M15 0.36, M11 0.18, M9a 0.54 µm) VSB도 달라 Vth가 따라가지 않는다. pmos 고리와 nmos 고리가 I8 분배를 다툰다. | 164행 'PVT 코너 스윕': 합격 = TT 27 °C 한 조건(DEC-96 (3)). 코너는 기록만 하고 범위 밖이다(사용자 승인 2026-10-12 P-14). | 엔진 칸 0. 실측(바이어스 전류 이상원 고정, `all_out.jsonl` pvt): I_Q는 TT 27 °C 20 µA 기준 3.8~63 µA(×0.19~×3.2). ss/fs −40 °C에서 V_bat 0.02 V(배터리 붕괴), V(N11b) < 0(M12 포화 불가). | **계획대로 보고만**(범위는 사용자 결정). ⚠ 위험 기록: 코너가 범위에 들어오면 class-AB I_Q가 가장 민감한 항목이다. | 높음(측정) / 범위는 사용자 몫 |
| 6 (추가) | **1단 출력 DC = VGS16**: 고리가 Vop1을 출력 소자 VGS에 묶어 1단 NMOS 사슬(M3b·M4b·M5) 헤드룸을 누른다(원문 p.2). | headroom-chain R-1′(W4 소거), DEC-64 VDS-1(M4b·M3b 행), DEC-67 스윙·ICMR | VDS-1 (M4b, M3b, M63) 등과 R-1′ 그래프가 일반형으로 덮는다. 대표점 Vop1 = 0.624 V. | **맞음** | 중(R-1′ as-built 미완, 계획 문언 기준) |
| 7 (추가) | **배터리 저주파 전달 H0 ≠ 1**: 2단 DC Gm = gm16 + H0·gm15. 실측 0.906 mS 대 gm15 + gm16 = 0.753 mS, +1.6 dB. | J3 'M15/M16 한 블록 병렬 셀'(블록 국소 모델), DEC-05·DEC-66 블록 대 MNA 잔차 기록 | 블록 모델이 gm15 + gm16으로 두면 잔차로 기록된다. 판정 = MNA. | **보고만**(잔차 기록 규칙 그대로) | 높음 |

## 2. 일반성 (13회로, 연결만 -- `scan13.out.txt`, `r2r_cycles.out.txt`)

**부유 상보쌍**(같은 두 비레일 넷 사이 nmos·pmos 채널, D/S 교차, gate가 비레일 바이어스 넷)이 있는 회로는 2/13이다.
- current_reuse: 2쌍(M9a/M9b, M18a/M18b). 출력 짝 M15/M16, M25/M26.
- heldout r2r_opamp: 2쌍.
  - M19/M20: class-AB 제어. 출력 M25/M26.
  - M27/M28: 떠 있는 전류원. 같은 바이어스 n_abn/n_abp를 쓰고 원문은 "같은 구조"라고 적는다.

나머지 11회로는 0이다. erfc의 '부유 전지'는 커패시터 전지라 다른 꼴이다(Q-ZG1, DR-1).

DEC-64 v2 탐지는 r2r에서도 고리 4개를 자동으로 찾는다: {M19, M23, M24, M26}, {M20, M21, M22, M25}, {M17, M19, M26, M27}, {M11, M20, M25, M28}.
→ 결정자 1~4는 **일반 규칙**(DEC-64, R-1′, MNA)이 회로 이름 없이 덮는다. r2r의 정지 전류 180 µA는 `pending_constraints`(U-75, 판정 안 함)다.

## 3. 계획 개정 후보 (손계산 우선 O-173 E-0·E-1·E-2 기준. 정밀화 권고 0건)

### R-A [중] spec 결정 대기 제약 `옛 classab_centering_dev_v ≤ 0.15`(= |VGS16 − VSG15|) 철회 권고 -- ⚠ 사용자 결정(U-35 user_spec) 재검토

**물리 결정자가 없다.** 배터리 헤드룸·출력 소자 포화·1단 헤드룸은 VDS-1·R-1′ 행이 이미 일반형으로 판정한다(결정자 4·6). history 4191행 기록대로, 이 제약은 V_bat 합을 보지 못해 V_bat < 0인 점을 통과시킨 전례가 있다.

**공정 의존 상수다.**
- 원문 180 nm 동작점: |0.475 − 0.487| = 0.012 V
- sky130 대표점(물리 정상, 모든 소자 포화): |0.624 − 0.876| = **0.252 V**. 이 제약이 정상 점을 거부한다.
- 근거 숫자 0.15의 유도는 없다(상수 발명).

**지금 상태**: metric 미등록(pending MOD5)이라 판정은 꺼져 있다. 그러나 MOD5가 이름을 붙이는 순간 켜진다.

| 안 | 내용 | 평가 |
|---|---|---|
| (가) **삭제 (권고)** | 제약 행 삭제(spec data 커밋, 소비자 0 확인 -- design 문서 grep 0건) | 물리 정합(P0), 상수 발명 제거(P1), 새 필드 0 |
| (나) 출력 전용 보고 metric으로 둠 | 소비자 0인 새 metric을 구현해야 함 | 만들고 안 씀(배선 원칙) -- 비권고 |
| (다) 유지 | ⚠ 원칙 경고: 물리 결정자 없음, 상수 발명, sky130 정상 점 거짓 거부 | 비권고 |

### R-B [중-낮] DEC-64 (v2) '종속 소자 선택 우선순위'(DEC-95 (3))와 DEC-104 R6·L-11('고리 종속 = B ln IDu, B는 어느 층에서도 독립 아님')의 층 구분 문언

class-AB 고리 {다이오드 B 둘, 출력 S 하나, 배터리 하나}에서 두 규칙이 서로 다른 멤버를 고른다.
- DEC-95 (3)(다이오드 독립 → gm 요구 소자 독립)는 배터리 M9a를 종속으로 고른다.
- DEC-104는 B 다이오드 하나를 종속으로, 나머지 B를 가드 구간 선택점으로 둔다.
- 배터리 소자의 R13 분류(F 대 B)는 TB-1 전이라 미정이다.

권고(문언 정정만, 새 필드·규칙 0):
- DEC-64 v2에 다음을 적는다: "DEC-95 (3) 순서는 커널 쓰기 계획(실현 평가, W 고정 순방향 DC 풀이)의 writer 트리에만 쓴다. θ 기저의 고리 종속 멤버는 DEC-104 R6(B 멤버)이 정한다."
- 같은 고리에서 두 층의 '종속'이 다른 멤버라는 점과 그 정의 축(목표 θ 대 실현 dc_op)을 적는다(graph 규칙 3).

물리 근거: 교과서 Monticelli 손계산 순서(P3)는 출력 소자 = AC 요구, 배터리 = 극점·분배, 기준 다이오드 = 고리를 닫는 복제다. 다이오드 종속이 순서에 맞고, 배터리 gm/ID를 PM 좌표로 남긴다. 실측으로 확인한 것은 둘 다 KVL에 정합하다는 것(I_Q 오차 0.014 %)까지다. 어느 쪽이 더 나은지는 탐색 효율 문제다.

as-built 사실: OrderHints 미배선으로 커널은 M15·M16을 종속으로 둔다. 실현 평가는 W가 주어지면 순방향으로 같은 값에 수렴하므로 판정 영향은 없다(봉인 3·8이 거부). 이 배선을 맡은 card는 계획에서 찾지 못했다. 백로그 기록을 권고한다.

### R-C [낮] R9 '반대쪽 가지 단자 전압'의 배터리 결합 gate 정의 (card DE-1 design 몫)

class-AB에서 꺼지는 쪽 gate 전압은 바이어스 고정이 아니다. 같은 극단 상태의 kvl_branch 고리(배터리 반대쪽 소자가 I8 전부, KCL)로 정해진다.
- 정지값을 쓰면 보수적이다(I_Q 대 실제 0.4~0.75 I_Q).
- 구동단 범위 끝(≈ 0)을 쓰면 fail-open이다(I_min을 0으로 봄).

current_reuse에서는 결정이 바뀌지 않는다(R8 요구 µA 대 I_cap 수백 µA). 그래서 정밀화가 아니라 **정의 한 줄**이다: "반대쪽 소자 gate가 kvl_branch 고리에 묶이면 그 고리 KVL과 극단 상태 KCL로 단자 전압을 정한다 -- LUT 조회 2회, 끝 풀이 없음". 새 필드 0(기존 `rel_kvl_branch` READS).

### R-D [낮, E-2 조건부] 출발 매크로(design 41 §6.5)에 pass 셀 내부 마디(배터리 Vg15) 포함 여부

as-built 매크로에는 없다. 그래서 2단 Gm을 gm15 + gm16으로 봐서 낙관적이다. 실측으로는 fu에서 0.48~0.63배, −6~−26°다.

판정은 전체 MNA라서 fail-closed다. R3 '극점 미포함' 규칙에 따라 I8은 하한 행 최대로 출발한다. 지금 바꿀 근거는 E-2를 만족하지 않는다(출발값은 판정에 쓰이지 않음).

조건부 권고: card LA-1·ME-1 변화표에서 current_reuse·r2r 출발점이 PM으로 거부되는 비율이 높으면, design 41 §6.5 '출력노드가 아닌 극점 노드'에 다음을 명시한다.
- pass 셀 source 마디를 포함한다.
- 병렬 셀 VCCS는 셀마다 gate 넷에서 둔다(일반 규칙, 회로 이름 없음).

### R-E [낮, 문언]

- DEC-15(215행) '파일럿 적용: M11a/M11b/M20a/M20b'는 고리 멤버 일부만 적었다. 실측 4고리(위 0절)로 바꾼다.
- J12-c 하위 물음은 이 실측(4 v2_rail 사이클 = J3 정지전류 고리)으로 닫을 수 있다.

## 4. 원칙 점검

- **graph 단일 정본**: 새 필드·cache·사본 권고 0이다. R-C는 기존 `rel_kvl_branch`와 R9 조회 함수를 쓰고, R-D는 기존 매크로 마디 규칙을 쓴다. 둘째 생산자 0이다.
- **θ 틀**(설계점 = θ 고정, 섭동 = KCL)
  - 결정자 1은 θ 고정 사이징이다(I_Q θ 전류, 고리 종속 ln IDu).
  - 결정자 2·5는 정해진 W를 흔드는 분석(고정 W KCL·KVL)이라 θ 커널 밖이다(DEC-103과 맞음).
- **DC/AC 분리**
  - 1·2·4·5·6은 DC다.
  - 3·7은 동작점 소신호다.
- **새 상수**: 0이다. R-A는 상수를 제거한다.
- **회로 이름**: 0이다. 13회로 일반형으로 확인했다.
- **E-2**: 정밀화 권고 0이다. R-D는 실측 조건부다.

## 5. 측정 조건 (재현)

- sky130 tt.pm3 + mismatch.corner + lod, ngspice-46(`ngspice_con.exe -b`), 27 °C
- 반쪽 2단: 바이어스 M8·M10·M12·M13은 이상 전류원, Vop1은 1 F 저역 VCCS 서보(DC만 Vom = 0.9 V), C_L = 1 pF
- 원문 치수를 그대로 sky130에 옮기면 M9a가 꺼진다(32 pA, `results.jsonl` q_tt27). 공정 Vth 차 때문이다. 그래서 대표점은 M15를 200/0.36, M9a L을 0.15로 바꾸고 나머지는 원문 치수다. M9a·M9b W는 고리 KVL 종속으로 손계산했다.
- 손계산 = 단일 소자 ngspice `.dc`(LUT 대용, 단자 전압 = 손계산 노드전압)
- AC: Vop1에 AC 전류를 넣고, Vom은 1 F로 AC 단락한 단락 전류로 잰다.
