# 부하 선언에서 최소 정지전류 유도 -- 물리 유도, 계획 대조, library 실측

- 작성: 분석 agent, 2026-10-24. 엔진·계획·design은 고치지 않았다. 엔진 `wt/integ-it12/.../gmid_engine`(integ/it12 HEAD `34585913`)은 import해서 실행만 했다. 실행 전후 `git -C integ-it12 status --short`가 같다(`_scratch_mincur/git_status_before.txt` = `after.txt`, 둘 다 빈 출력).
- 사용자 질문(원문): "앞서 있는 load dc amp가 있으면 dc동작점 전류가 정해지지 않나? … 저항과 cap이 있다면 dc전류는 저항전류+full swing 가능전류(ac스펙에서 유도)가 될 것 같은데 load dc amp까지 고려해서 최소전류문제를 더 깊게 검토해줘"
- 원자료(`wt/_scratch_mincur/`):
  - 스크립트 `scripts/outstage.py`(층 0 출력단 전류·셀 종류), `lsmax.py`(as-built `ls_fields` 방향 전류), `ppmax.py`(push-pull 최대 전류 손계산), `rout_start.py`(rout 선언 출발점), `trace_front.py`(B80 사본, 출력 경로만 바꿈), `specsum.py`.
  - 결과 `out/outstage.jsonl`, `lsmax.jsonl`, `ppmax.jsonl`, `rout_start.jsonl`, `start_sf_rout.json`, `trace_sf_rout.jsonl`. B80 출발점 `_scratch_b80/out/start_handcalc.json`·`start_grid10.json`은 읽기만 했다.
  - 진단 장치: `lsmax.py`는 `ls_fields`가 `driving` 선언이 있을 때만 계산되므로(`metrics/metrics_aux.py:235`) 메모리 안에서 `DrivingDecl(None, 1e-12, None)`(1 pA 피크, 슬루 없음)를 넣었다. 파일 수정은 없다.
- heldout 회로는 근거로 쓰지 않았다. SPICE는 새로 돌리지 않았다.

## 0. 결론

1. **사용자 가설 판정**
   - (가) "C_L만 있으면 full swing 가능 전류가 최소전류": **조건부로 맞다.** 속도 선언(SR, 또는 주파수+진폭, 또는 슬루 시간+계단 크기)이 있어야 하한이 생긴다. C_L만 있고 속도 선언이 없으면 DC 전류 하한은 **생기지 않는다**. 커패시터는 DC 끝 상태를 바꾸지 않고, 어떤 I > 0도 시간만 주면 끝까지 충전한다.
   - (나) "저항 부하가 있으면 최소전류가 생긴다": **맞다. 이것은 DC 양이다.** 스윙 끝에서 bias 쪽 방향 전류 ≥ |V_끝 − V_R|/R_L이다. 다만 스윙(출력 범위) 선언이 있어야 값이 나온다. 동작점에서 V_out,dc ≠ V_R이면 그 DC 전류는 netlist KCL에 이미 들어 있다(nmcnr 실측 30.3 µA, §3).
   - (다) "R+C이면 DC 전류 = 저항전류 + full swing 전류": **class-A의 bias 방향에 한해 맞다.** 슬루(램프) 계단이 스윙 끝까지 슬루하면 단순 합이 **정확한 필요조건**이다. 사인파면 피크가 Vp·√(1/R² + (ωC)²)라서 단순 합은 **보수적 상한**이다(ωRC = 1에서 최대 √2배 과대). Allen 교재의 max(C·SR, Vp/R)는 오히려 최대 2배 과소다(§1.3).
   - (라) "load_dc_amp가 있으면 동작점 전류가 정해진다": **절대값은 정해지지 않는다.** 정해지는 것은 출력 노드 KCL의 **차**(I_공급 − I_흡수 = I_dc)다. 정지전류 하한은 "I_dc가 bias 방향일 때 I_B ≥ I_dc"뿐이다. class-AB에서는 I_q에 하한을 주지 않는다.
   - (마) class-AB: 부하 피크는 **정지전류가 아니라 최대 출력 전류**(O-26 (1))가 감당한다. θ 좌표에서는 I_max = I_q·J(V_GS,max)/J(V_GS,q)라서 I_q ≥ I_peak·J_q/J_max(θ)가 된다. 실측 배율 J_max/J_q는 19~658배다(§3.3). 그래서 부하 쪽 하한은 I_q에서 거의 묶이지 않는다. I_q 하한은 rout·안정도 같은 소신호 spec에서 온다. Xie & Chen p.2도 "더 줄이는 한계는 안정도 요구"라고 적었다.
2. **library 실측(9회로)**
   - `driving_spec`(슬루율·`load_peak_amp`·`load_dc_amp`) 선언 0, 슬루율 선언 0, 슬루 시간+계단 크기 선언 0이다.
   - 부하에서 유도되는 하한이 **정의되는** 회로는 nmcnr 하나다(R_L 25 kΩ + `swing_out_v` ≥ 0.5 V → 10 µA). 이 값도 층 0 전류 1.15 mA보다 115배 작아서 **묶이지 않는다**.
   - **B80 front 0 회로 8개 가운데 부하 하한으로 출발 전류가 정해지는 회로는 0개다.** 그래서 부하 하한 출발 실험은 대상이 없다.
   - 출발 전류를 실제로 바꾸는 하한은 소신호 spec(rout·GBW·PM)이다. pushpull rout 1 kΩ → 19.3~24.1 µA(B80 §3), two_stage_ota_sf rout 1 kΩ → 54.6 µA.
   - 보충 실험: two_stage_ota_sf에 rout 출발점을 넣어도 front는 0이다(gain·offset 행이 남는다, §3.4). gain 회로는 DEC-71 (4) gain 모드가 필요하다는 B80 결론과 맞는다.
3. **계획과의 관계**
   - R 항과 `load_dc_amp`·`load_peak_amp`는 **DC 양**이다. 계획 DEC-58·N3.8 '출력 구동 규칙'과 DEC-71 (3) '블록 전류(KCL·선언)'에 이미 자리가 있다. 원칙 충돌은 없다.
   - C·SR 항은 **과도(대신호) 양**이다. 엔진이 이 항으로 바이어스를 유도하면 O-122("슬루 판정과 탐색 모두 oracle, 엔진 관여 없음")와 정면 충돌한다. O-122는 DEC-71 (3) 입력에서 '슬루 하한'을 지웠다. 이 항을 되살리는 것은 원래 취지와 다르다.
   - 소신호 하한(rout·GBW·PM → gm_req/(gm/ID))은 DEC-70 θ 제약·DEC-71 (3)(4)의 영역이다. B80 해법(LA-1)이 이것이다.
4. **gap(실측, 새로 찾음)**
   - (G1) `load_dc_amp`는 as-built에서 소비자가 0이다. `authoring` 밖 `git grep load_dc` 적중은 `search/ls_constraints.py:5` 주석("DC 봉인의 KCL 입력이라 여기 행이 없다") 하나다. DC 봉인 쪽 소비자는 없다. 계획 N3.8 "선언되면 출력 포트 KCL에 넣는다"와 다르다. 코퍼스 선언이 0이라 지금 결과에는 영향이 없다.
   - (G2) `compensation_targets.settling`(current_reuse total 40 ns, linear 30 ns)도 소비자가 0이다(`authoring/` 밖 적중 0). `spec_targets.py:13`에는 "보상 목표로만 쓰인다"고 적혀 있지만 실제 소비자는 없다.
   - (G3) 이중 계수 위험: R_L이 netlist 요소이면 그 DC 전류는 KCL이 이미 센다. 같은 물리 부하를 `load_dc_amp`로도 선언하면 같은 양을 두 생산자가 만든다(graph 단일 정본 규칙 1). 계획에 이를 막는 규칙이 없다.
5. **권고**: 지금 엔진 변경은 **(c) 쓰지 않음**이다(library 효과 0). 계획에는 **(a′)**를 기록할 것을 권고한다. (a′)는 선언된 DC 부하 전류(`load_dc_amp`, `load_peak_amp`)를 class-A bias(β) 방향의 층 0 국소 DC 제약으로 쓰는 안이다. 자리는 card LA-1이 DEC-71 (3) '블록 전류(KCL·선언)'를 구현할 때다. C·SR 항은 넣지 않는다(⚠ O-122). 사용자가 원하면 C·SR + Vp/R을 직접 계산해 `load_peak_amp`로 선언하는 길이 있다. 이 길은 O-122와 충돌하지 않는다. 비교는 §5에 있다.

## 1. 물리 유도

### 1.1 기호와 전제

- 출력 노드에 부하 R_L(다른 끝 전압 V_R)·C_L이 붙고, 정적 부하 전류 I_dc(`load_dc_amp`, netlist 밖 부하)가 흐른다. 출력이 흔들리는 범위는 [V_lo, V_hi]다(`swing_out_v`, DC 양 -- DEC-67).
- 출력 노드에 전류를 대는 셀은 방향마다 둘로 나뉜다(DEC-65 구조 분류, as-built `S1v output_direction`).
  - β: 게이트가 바이어스인 전류원. 최대 전류 ≈ 정지전류 I_B다(CLM만큼 변한다 -- O-122 근거 '내부 단자 β 1.19×').
  - σ: 게이트가 신호인 소자. 최대 전류 = 입력을 끝까지 몬 DC 해의 전류(O-26 (1))이고, 정지전류보다 훨씬 크다.
- class-A = 한 방향이 β, class-AB/B = 두 방향 모두 σ다(DEC-65).
- 부하가 요구하는 출력 노드 전류(bias 방향 부호):
  i_req(t) = C_tot·dV/dt + (V(t) − V_R)/R_L + I_dc
  - C_tot = C_L + 노드 기생 + 그 노드에 걸린 되먹임·보상 C(Allen ECE6412 L140 p.140-6이 SR = min(I5/Cc, (I6−I5−I7)/CL)로 노드별 I/C를 따로 적는 것과 같다 -- O-120 근거).

### 1.2 무엇이 I_q 하한을 정하는가 (출력단·부하별)

| # | 출력단 | 부하 | 하한식 | 필요조건/근사 | 필요한 선언 | 영역(DEC-67) |
|---|---|---|---|---|---|---|
| 1 | class-A(CS+전류원, SF+전류원) | C만, 속도 선언 없음 | **없음**(I_B > 0이면 시간이 걸릴 뿐 끝 상태에 닿는다) | -- | -- | -- |
| 2 | class-A | C만 + SR | I_B ≥ C_tot·SR(bias 방향만) | 필요조건. β CLM만큼 근사 | `slew_rate_v_per_s` | 대신호 과도(.tran) |
| 3 | class-A | C만 + 주파수 f, 진폭 Vp(사인) | I_B ≥ 2πf·Vp·C_tot(= C·SR_FP, f_FP = SR/(2πVp)) | 필요조건(사인 최대 기울기) | f, Vp | 과도 |
| 4 | class-A | C만 + 슬루 시간 t_s, 계단 ΔV | I_B ≥ C_tot·ΔV/t_s | 필요조건(평균 기울기라 하한) | t_s, ΔV | 과도 |
| 5 | class-A | R만 | I_B ≥ max_끝 \|V_끝 − V_R\|/R_L(bias 방향 끝) | 필요조건(그 끝에서 β 포화 유지 전제) | 출력 범위(위치 포함) | **DC** |
| 6 | class-A | R‖C, 슬루 계단이 끝까지 슬루 | I_B ≥ C_tot·SR + \|V_끝 − V_R\|/R_L | 필요조건(**단순 합이 정확** -- 램프 끝에서 두 항이 동시에 최대) | SR + 범위 | 과도+DC |
| 7 | class-A | R‖C, 사인 f | I_B ≥ Vp·√(1/R_L² + (2πf·C_tot)²) | 필요조건(위상 90° 차). 단순 합은 최대 √2배 과대 | f, Vp | 과도 |
| 8 | class-A | +정적 I_dc | 위 각 식에 + I_dc(I_dc가 bias 방향일 때). 반대 방향이면 신호 소자 쪽 전류가 I_B + I_dc로 늘 뿐 I_B 하한은 없다 | 필요조건(KCL) | `load_dc_amp` | **DC** |
| 9 | class-AB | 무엇이든 | I_q 하한 없음. I_max,dir ≥ i_req,peak(O-26 (1))이고, θ 좌표에서는 I_q ≥ i_req,peak·J_q/J_max(θ)(§1.4) | 필요조건(I_max 정의는 DC 해, 엔진 규칙은 U-115 미결) | `load_peak_amp` 등 | DC |
| 10 | class-AB | -- | I_q 하한 = 소신호: rout ≤ R_t → I_q ≥ 1/(R_t·Σ(gm/ID)); 출력 극점 gm_out/C_L ≥ 안정도 요구; 교차 왜곡 | 손계산(gmb·gds 생략 시 근사) | `rout_ss_ohm`, PM 등 | ss |
| 11 | class-B | -- | I_q = 0(정의상). 소신호 spec이 있으면 성립 불가 → class-AB | -- | -- | -- |

- 방향 일반형: class-A에서 bias가 흡수 쪽이면(two_stage_ota M7) 하한은 하강 쪽 항이다: I_B ≥ C_tot·SR_fall + (V_R − V_lo)/R_L + I_dc,흡수. 공급 쪽 bias(nmcnr M302, ngcc M12)는 상승 쪽 항이다. 두 방향을 하나로 묶는 집계 규칙은 두지 않는다(N3.8 슬루 방향별 metric 원칙과 같다).
- 소신호 하한(#10)은 class-A에도 그대로 성립한다. 예: SF rout → gm_SF ≥ 1/R_t, two-stage PM → gm6 ≥ 2.2·(C_L/C_c)·gm1(Allen-Holberg 교과서 관례 -- 계획은 이 값을 상수로 쓰지 않고 PM metric으로 판정한다).

### 1.3 R과 C 전류의 합: 사용자 '저항전류 + full swing 전류' 판정

- 램프(슬루) 계단: V(t)가 V_0에서 V_끝까지 기울기 SR로 오르는 동안 i_req(t) = C·SR + (V(t) − V_R)/R은 V_끝에서 최대다. 그래서 단순 합 C·SR + (V_끝 − V_R)/R이 **정확한 최댓값**이다. 계단이 끝 전에 슬루를 마치면(선형 정착 꼬리) 단순 합은 상한이 된다.
- 사인 V = Vp·sin ωt: i = Vp(sin ωt / R + ωC cos ωt) → 피크 Vp·√(1/R² + (ωC)²). 단순 합/정확값 = (1 + x)/√(1 + x²), x = ωRC. x = 1에서 √2, x ≪ 1 또는 x ≫ 1에서 1이다.
- Allen ECE6412 L040 p.040-3: "|I_OUT| > C_L·SR, |I_OUT| > v_OUT(peak)/R_L. The maximum current will be determined by both …". Example 5.5-1(p.040-5)은 두 값(R 100 µA, C·SR 1000 µA)에서 큰 값 1 mA를 골랐다("Since the slew rate current >> the current for R_L, we can safely assume…"). 램프 계단 기준으로 이 max 규칙은 최대 2배 **과소**다. 두 항이 비슷하면 사용자의 합이 맞다.
- 판정: **사용자의 합 = 슬루 계단 기준 정확값, 사인 기준 보수적 상한(≤ √2배)이다.** 성립 조건은 class-A의 bias 방향이고, SR(또는 f·Vp)과 출력 범위가 선언된 경우다.

### 1.4 class-AB: 왜 정지전류가 아닌가 (θ 좌표 해석)

- σ 소자의 최대 전류는 I_max = W/L·IDu(V_GS,max)다. θ에서 W/L = I_q/IDu(V_GS,q)이므로 I_max = I_q·IDu(V_GS,max)/IDu(V_GS,q)다.
- 따라서 피크 요구 I_max ≥ I_peak는 I_q ≥ I_peak·J_q/J_max(θ)가 된다. 이 값은 θ(반전 밀도)에 따라 바뀌는 제약이고, 상수 출발 전류가 아니다.
- 약반전(높은 gm/ID)일수록 J_max/J_q가 커서 I_q 하한은 사라진다. 실측(§3.3): pushpull B80 손계산 점 658×(M1)·308×(M2), grid10 점 19×·37×.
- 원문 근거:
  - Xie & Chen 2019 p.2 §II.B(`assets/library/sources/current_reuse_telescopic_ota__xie_chen_2019/paper.md` 271-279행): "for a common source output stage, the slew will be limited because the load transistors are not able to provide the required current. However, by using the designed Class-AB output stage, instantaneous current will can be provided … The limitation of reducing the current further more is the stability requirement".
  - Allen L26 p.26-10(`…__allen_2014/paper.md` 466-469행): "the common-source, push-pull is ideal if the quiescent current can be controlled".

### 1.5 속도 선언의 출처 -- 'C_L만 있으면 하한 없음' 검토

- 하한을 만드는 속도는 다음 셋 중 하나다.
  1. SR 선언(`slew_rate_v_per_s`).
  2. full-power bandwidth: f와 진폭 Vp 선언 → SR_req = 2πf·Vp. ADI MT-045, LT1815 기사 "f_FPBW = SR/2πV_P".
  3. 정착 선언(t_settle, t_linear, 계단 ΔV) → SR ≥ ΔV/(t_settle − t_linear).
- GBW는 SR을 정하지 않는다.
  - 2단 Miller OTA에서 SR = I_tail/C_c, ω_GBW = gm1/C_c이므로 SR/ω_GBW = I_tail/gm1 = 2/(gm/ID)_1이다(Johns & Martin '1997 6장의 SR = V_eff·ω_ta 관계와 같은 꼴, 쪽 미확인).
  - 이 식은 GBW와 입력쌍 θ가 정해지면 SR이 **따라 나온다**는 결합 관계다. 부하에서 바이어스를 정하는 식이 아니다.
- 그래서 'C_L만 있고 속도 선언이 없으면 DC 전류 하한이 생기지 않는다'는 **맞다.** C_L이 GBW·PM 식에 들어가 소신호 경로로 전류를 정하는 것은 별개다(DEC-02 보상 먼저).
- library 실례 current_reuse: 정착(40 ns / 30 ns → 슬루 몫 10 ns)은 선언돼 있지만 계단 크기 ΔV는 선언되지 않았다.
  - 'full swing'을 가정하면 한 쪽 1.2 V / 10 ns × (1 pF + 피드백 직렬 C ≈ 0.25 pF) ≈ 150 µA/쪽이다.
  - 원문 총 전력은 126 µW(1.8 V에서 ≈ 70 µA 전체, Table I p.1)다.
  - 계단 크기를 지어내면 4배 넘게 과대해진다. 상수 발명 금지 원칙이 여기서 실질적으로 작동한다(**추정** -- 피드백 C 등가는 손계산).

## 2. 계획과의 관계 (원칙별)

| 원칙·자리 | R 항·`load_dc_amp`·`load_peak_amp`(DC) | C·SR 항(과도) | 소신호 하한(rout·GBW·PM) |
|---|---|---|---|
| DC/AC 분리(DEC-67, 사용자 근본원칙 2026-10-19) | DC 양(스윙 끝 DC 해의 KCL). 정합 | 과도(.tran) 양. DC 전류로 옮기면 '대신호 → DC' 되먹임이다. DEC-70은 θ 제약으로만 허용 | ss 양 → θ 제약(DEC-70). 정합 |
| DEC-103(설계점 = θ 고정, 섭동 = KCL) | 설계점(바이어스 결정)은 θ 고정 손계산: I_B ≥ ΔV/R + I_dc. 스윙 끝 판정은 W·바이어스 고정 KCL(DE-1 선형 감도 끝). β 전류원은 포화 안에서 두 틀 모두 같은 전류라 결론이 같다 | θ 고정 I_B ≥ C·SR. 판정은 oracle | θ 고정 I = gm_req/(gm/ID). 정합 |
| DEC-70(AC → θ 제약으로만) | DC 제약이라 해당 없음(KCL·선언 입력) | 슬루율은 θ 제약이 아니다(v6.37 O-122, DEC-70 본문) -- **충돌** | 정합 |
| O-122(엔진 슬루 관여 없음) | 슬루 아님. 충돌 없음 | 판정과 유도를 나눠 봐도 충돌한다: O-122는 '판정·탐색 모두 oracle'이고, O-121 B-1 (나′)의 '출력 노드 전류 하한 = 탐색 경계'를 명시적으로 대체했다. 층 0 하한·출발점은 탐색이다. ⚠ | 해당 없음 |
| DEC-58·N3.8 출력 구동 규칙 | `load_peak_amp` → 출력 포트 방향 최대 전류 ≥ 그 값. `load_dc_amp` → 출력 포트 KCL. **이미 계획에 있다**. as-built는 G1(`load_dc_amp` 소비자 0) | 슬루율 = oracle만 | rout = DEC-66(전회로 판정), 층 0 국소 = DEC-71 (3) |
| U-115(방향 최대 전류 엔진 규칙 미결) | β 셀(class-A bias 방향)은 I_max = 봉인점 I_q라 어느 후보 (가)(나)(다)에서도 같다. σ 셀(class-AB)만 U-115 결정이 필요하다 | -- | -- |
| DEC-71 (3) 블록 전류 입력 | 계획 원문 "블록 전류(KCL·선언 -- '슬루 하한'은 v6.37 O-122로 없음)". '선언'에 `load_dc_amp`·`load_peak_amp`가 들어갈 자리가 있다. design 41에는 아직 구체 규칙이 없다(design 41 892행은 '슬루 하한'이 남은 옛 문장 -- O-124 13곳 정정 대상) | O-122로 지움 | 버퍼: rout 국소(E10). 이득: (4) 역산 |
| 손계산 속도 우선(O-29~O-31) | 한 줄 식. 정합 | 한 줄 식(손계산은 쉽지만 O-122 근거 '추정 0.28~28×'는 σ·κ 셀 상한 쪽 문제다) | 정합 |
| graph 단일 정본 | 하한은 그 필드를 READS해야 한다: 부하 값 = spec 선언, I_q = 봉인점 θ 전류, 범위 끝 = DE-1 창 필드. 새 생산자 금지. G3(R_L netlist와 `load_dc_amp` 이중 계수) 규칙 필요 | 슬루 몫 필드는 O-122로 삭제 대상 | -- |

- **판정과 유도의 구분**(작업 지시 2항):
  - 물리로는 SR → I_B ≥ C·SR가 판정(SR을 재는 일)과 다른 '필요조건 유도'다. O-121 B-1 (나′)는 바로 이 구분으로 '놓침 0'을 보였다(`slew_estimate_vs_bound.md` 60점).
  - 그러나 사용자는 O-122 "A로 하자"로 그 안을 버리고 '엔진 관여 없음'을 택했다. 그래서 계획상 구분은 이미 결정됐다. 이를 되살리려면 원래 취지와 다른 재결정이 필요하다.
  - library에 SR 선언이 0이라, 되살려도 library 결과는 바뀌지 않는다.

## 3. library 실측

### 3.1 선언 표 (spec `human`·topology, integ/it12 `34585913`)

| 회로 | 출력 구조(S1v, 실측) | C_L | R_L | driving_spec | SR | 출력 스윙 | GBW | rout | 기타 |
|---|---|---|---|---|---|---|---|---|---|
| pushpull_follower_buffer | push_pull(M1 σ / M2 σ) | 1 pF | -- | 없음 | 없음 | 없음 | 없음 | ≤ 1 kΩ | -- |
| sf_pushpull_output_opamp | push_pull(M22 σ / M21 σ) | 1 pF | -- | 없음 | 없음 | 없음 | 60 MHz | ≤ 1 kΩ | IBias 50 µA 선언, PM 70 |
| two_stage_ota | class_a(M6 σ 상승 / M7 β 하강) | 3 pF | -- | 없음 | 없음 | 없음 | 7 MHz | -- | PM 70 |
| two_stage_ota_sf | class_a(M8 σ / M9 β 하강) | 3 pF | -- | 없음 | 없음 | 없음 | 파일 참조 | ≤ 1 kΩ | PM 70 |
| folded_cascode | class_a(M6 β 상승 / M8 σ 하강) | 1 pF | -- | 없음 | 없음 | 없음 | 미결 SP-5 | -- | -- |
| common_gate_amplifier | 'none'(M3 β / M2 β) | 없음(SP-6(c)) | -- | 없음 | 없음 | 없음 | 미결 | -- | -- |
| ngcc_3stage_ff | class_a(M12 β 상승 / M13·M14 σ, M7 κ 하강) | 10 pF | -- | 없음 | 없음 | 없음 | 10 MHz | -- | PM 63.4 |
| nmcnr_amplifier | class_a(M302 β 상승 / M301 σ 하강) | 100 pF | 25 kΩ(Vout–agnd 0.9 V) | 없음 | 없음(topology `_paper_target_spec`에 0.36/0.31 V/µs만, spec 아님) | ≥ 0.5 V | 816 kHz | -- | PM 70 |
| current_reuse_telescopic_ota | push_pull(M15/M16, M25/M26 σ/σ) | 1 pF ×2 | -- | 없음 | 없음 | ≥ 2.4 V(차동 p-p) | -- | -- | settling 40/30 ns(소비자 0, G2) |

### 3.2 유도식으로 낸 하한 (손계산) 대 층 0 전류 (`out/outstage.jsonl`)

| 회로 | 부하 유도 하한(§1.2) | 층 0 출력단 전류(bias 방향) | 부하 하한이 묶이나 | 소신호 하한(참고, #10) |
|---|---|---|---|---|
| pushpull | **정의 안 됨**(C만, 속도 선언 없음) | 0.15 nA | -- | rout: 1/(1 kΩ·(25.85 + 25.98)) = **19.3 µA**(층 0 gm/ID). B80 면적 보정 손계산 24.1 µA |
| sf_pushpull | 정의 안 됨 | 층 0 실패(B81 `start_lut_query_failed`) | -- | rout·GBW·PM에서 정해짐(미측정) |
| two_stage_ota | 정의 안 됨 | M7 24.8 µA(β = I_max 실측, §3.3) | -- | 매크로(GBW) 이미 작동 |
| two_stage_ota_sf | 정의 안 됨 | M9 27.1 µA | -- | rout: 1/(1 kΩ·18.33) = **54.6 µA**(손계산 2회 반복 수렴, 1000 Ω) |
| folded_cascode | 정의 안 됨 | M6 1.13 µA | -- | 없음(ss 선언 offset·noise뿐 → '층 0 무동작' 대상) |
| common_gate | 정의 안 됨(C_L 없음) | 0.15 nA | -- | 없음 |
| ngcc | 정의 안 됨 | M12 44.2 µA | -- | GBW·PM 매크로 |
| nmcnr | R 항(DC): 범위 0.5 V를 agnd 중심에 두면 0.25 V/25 kΩ = **10 µA**(M302 상승 방향). 범위 위치 선언이 없어 **추정** | M302 1.15 mA | **아니오(115배 여유)** | GBW·PM 매크로 |
| current_reuse | 정의 안 됨(ΔV 미선언, §1.5) | 층 0 실패(B81) | -- | -- |

- nmcnr 층 0 점에서 Vout = 1.658 V(입력 DC 미결 SP-2)이고, R_L DC 전류 = (1.658 − 0.9)/25 kΩ = 30.3 µA다.
  - KCL 실측: I(M302) − I(M301) = 1.15 mA − 1.12 mA ≈ 30 µA로 맞는다(`outstage.jsonl`).
  - **netlist 안의 저항 부하 DC 전류는 엔진 DC 풀이가 이미 센다.** 사용자 가설 (나)의 'DC 성분'은 이미 처리되고 있다. 따로 선언하면 이중 계수가 된다(G3).
  - 참고: M302 VDS = 0.142 V로 포화 여유가 작다. 출력 DC가 agnd에서 벗어난 것은 SP-2(입력 DC 미결) 때문이다. 이 보고의 범위는 아니다.
- 만약 원문 SR(0.36 V/µs)을 spec으로 선언한다면(가정, 선언 아님): C·SR = 100 pF × 0.36 V/µs = 36 µA, + R 10 µA = 46 µA다. 여전히 층 0 1.15 mA보다 25배 작다.

### 3.3 class-A 대 class-AB: 방향 최대 전류 / 정지전류 (실측)

| 점 | 출력 소자 | I_q | 방향 최대 전류(출처) | 비 |
|---|---|---|---|---|
| two_stage_ota 층 0 | M7(β, 하강) | 24.8 µA | 24.8 µA(as-built `ls_fields` β = 봉인점 ID, `lsmax.jsonl`) | **1** |
| two_stage_ota 층 0 | M6(σ, 상승) | 24.8 µA | 4.42 mA(as-built σ = LUT ID(V_GS,max), '추정' -- O-26 (1) gap) | 178 |
| pushpull B80 손계산 점 | M1(σ) | 24.1 µA | 15.9 mA(`ppmax.py`: vout 동작점 고정, 게이트 → 레일) | 658 |
| 같은 점 | M2(σ) | 24.1 µA | 7.43 mA | 308 |
| pushpull grid10 점 | M1 / M2 | 48.0 µA | 0.92 / 1.80 mA | 19 / 37 |
| pushpull 층 0 | M1 / M2 | 0.15 nA | 33.7 / 2.41 µA | 2.2e5 / 1.6e4 |

- two_stage_ota 출력 노드 C_tot = 3.49 pF(엔진 `c_slew_farad`)다. 층 0 점의 하강 SR 상한은 24.8 µA / 3.49 pF = 7.1 V/µs다. 이 값이 'bias 방향 I_B ≥ C·SR'의 실례다.
- pushpull은 as-built `ls_fields` 보고가 나오지 않았다(`ls_nodes` 없음 -- 버퍼 뷰의 swing bounds가 비는 것으로 보임, **미확인**). 그래서 `ppmax.py` 손계산으로 대신했다. σ 값은 O-26 (1) 정의(입력을 끝까지 몬 DC 해)의 근사이고 노드 A 상한 = vdd를 가정했다(**추정**).
- 결론: class-AB에서 I_q ≥ I_peak·J_q/J_max는 손계산 점에서 I_peak/300~650이다. pushpull에 1 pF·(예) 10 V/µs = 10 µA 피크를 주어도 I_q 하한은 0.03 µA 수준이다. rout 하한 24 µA가 지배한다.

### 3.4 출발점 실험

- **부하 유도 하한 출발점 실험: 대상 0회로.** §3.2에서 하한이 정의되는 회로는 nmcnr뿐이고, 그 하한은 층 0 전류보다 115배 작다. 넣어도 출발점이 바뀌지 않는다. 그래서 실행하지 않았다(엔진 무수정 원칙에서 의미 있는 대조가 없다).
- 보충 실험(소신호 하한, B80 일반화 확인): two_stage_ota_sf에 E10과 같은 rout 규칙(출력 follower M8의 gm으로 Z_out = 1 kΩ, θ 전류 전부 같은 배수, 면적 보정)을 적용한 출발점을 `given_starts`로 넣었다. eval 2000이고 엔진은 무수정이다(`rout_start.jsonl`, `trace_sf_rout.jsonl`).
  - 출발점: I(M8) 54.6 µA, Z_th 1000 Ω, 봉인됨. 음수 행 = gain_ss_db, offset_excess(rout 행 해소).
  - 결과: **front 0**이다. 끝점은 s1 power slsqp_4 / area slsqp_4, s2 power slsqp_4 / area slsqp_8이고, 109 s 걸렸다.
  - 판정: rout만으로는 gain 회로를 살리지 못한다. B80 §4의 'gain 행 IIS'와 맞는다. LA-1 gain 모드(DEC-71 (4))가 필요하다는 결론을 지지한다. 부하 쪽 하한은 이 문제와 무관하다.

## 4. 사용자 질문에 대한 답 (정리)

- "앞서 있는 load dc amp가 있으면 DC 동작점 전류가 정해지지 않나?"
  - 출력 노드 KCL의 차는 정해진다. 정지전류 하한은 bias 방향일 때 I_B ≥ I_dc만 생긴다.
  - class-A에서는 반대 방향 소자의 전류가 I_B ± I_dc가 된다. 전력은 V·(I_B + …)로 늘어난다.
  - class-AB에서는 I_q가 정해지지 않는다. 최대 전류가 I_dc + 피크를 감당해야 한다.
- "cap load만 있으면 … 감당할 전류량이 slew 최소전류 스펙"
  - SR(또는 f·Vp, t_s·ΔV)이 선언될 때만 그렇다. class-A bias 방향에서 I_B ≥ C_tot·SR이고, C_tot에는 C_L 말고도 노드 기생·되먹임 C가 들어간다.
- "AC 스펙에서 DC 전류 스펙을 유도할 수 있는 이유"
  - 두 갈래다. 대신호(SR) → I ≥ C·SR, 소신호(GBW·rout·PM·잡음) → I ≥ gm_req/(gm/ID)다.
  - gm/ID 방법론의 본체는 후자다(θ 고정에서 gm/ID가 고정되면 gm 요구가 곧 전류 요구다).
  - 이 계획에서 전자는 O-122로 엔진 밖(oracle)이고, 후자는 DEC-70·DEC-71 (3)(4)다.
- "저항 load → 최소전류"
  - 맞다. 스윙 끝 DC 해의 값이고, 출력 범위 선언이 있어야 한다. 범위 위치(어느 끝이 V_R에서 얼마나 먼지)도 필요하다. `swing_out_v`는 폭만 선언하므로 위치 규칙은 계획에 없다(미확인 항목 2).
- "R+C → 저항전류 + full swing 전류"
  - class-A bias 방향에서 슬루 계단이면 정확하고, 사인이면 ≤ √2배 보수적이다. Allen의 max 규칙보다는 정확하다.

## 5. 대안 비교

| 칸 | (a) 부하 선언 전부(C·SR 포함)로 I_q 하한을 층 0 국소 DC 제약에 건다 | (a′) DC 부하 항만(`load_dc_amp`·`load_peak_amp`·R 스윙 끝) class-A β 방향에 층 0 국소 DC 제약으로 건다 | (b) 같은 하한을 출발점에만 쓴다(`start_intervals` 자리값 대체) | (c) 쓰지 않는다(현행, B80 해법 = LA-1 rout·gain) |
|---|---|---|---|---|
| 물리 정합 | 필요조건(class-A bias 방향). class-AB에 I_q 하한으로 걸면 **틀리다**(§1.4, 비 19~658×) | 필요조건, DC 양. class-AB는 U-115 뒤 I_max 제약으로만 | 같은 식이지만 제약이 아니라 근사 출발. 위반해도 막지 않는다 | -- |
| 손계산 일치 | 한 줄 식 | 한 줄 식(I_B ≥ I_dc + ΔV/R) | 한 줄 식 | -- |
| design 단순성 | 중간: 방향·셀 종류 분기 + C_tot 필드 READS(O-122로 삭제 예정 필드를 되살려야 함) | 작음: DEC-71 (3) '블록 전류(KCL·선언)' 입력 규칙 하나(β 방향). R 항은 DE-1 창 필드 READS | 작음 | 0 |
| 실측 | library 효과 0(SR·driving 선언 0, nmcnr 비구속 115×) | library 효과 0(같은 이유) | 효과 0 | B80: rout 손계산 출발 front 1(pushpull). two_stage_ota_sf는 rout만으로 front 0(§3.4) |
| 원칙 | ⚠ 원칙 경고: O-122(엔진 슬루 관여 없음) — C·SR 항은 엔진이 슬루로 탐색 경계를 만드는 것이고, O-122가 O-121 B-1 (나′)와 DEC-71 (3) '슬루 하한'을 명시적으로 지웠다 — 계획 DEC-71 (3) 원문 "'슬루 하한'은 v6.37 O-122로 없음", user_decisions O-122. **원래 취지와 다름**. ⚠ 원칙 경고: graph 단일 정본 — `c_slew_farad`·슬루 몫 필드는 DE-1 삭제 대상이라 되살리면 삭제 결정과 충돌 | 정합: DC/AC 분리(DC 양), DEC-103(θ 고정 설계점), 상수 0(값 = 선언), fail-closed(범위 위치 미선언이면 R 항 '미측정'). 단 G3 이중 계수 규칙이 먼저 필요하다 | ⚠ 원칙 경고: 계획 우선(S-7) — 출발 구간(design 41 §6)에 두면 LA-1 도입 뒤 같은 하한을 두 자리(출발 구간 + 층 0)에서 계산하게 된다(둘째 생산자) — CLAUDE.md graph 규칙 1, B80 §6 (나)와 같은 이유 | 정합(현 계획 그대로) |
| 계획 변경 | 필요(O-122 재결정 = 사용자 결정) | 계획 문언은 이미 허용(DEC-58·N3.8·DEC-71 (3) '선언'). design 41 규칙 추가 + G3 규칙 + 범위 위치 규칙(U 항목) | 필요(design 41 §6) | 없음 |
| 넣을 자리 | -- (권고 안 함) | card LA-1(DEC-71 (3) 블록 전류 입력 구현 때). σ 방향은 DE-1 (d)(U-115 뒤) | -- | -- |

**권고**
- 지금: **(c)**. library 효과가 0이고, B80 front 0의 원인과 해법은 소신호(rout·gain) 쪽이다. 부하 쪽은 무관하다(실측).
- 계획 기록: **(a′)**를 LA-1 design 개정(지금 병렬 착수 중, O-126)에 '블록 전류 입력 = KCL + 선언 DC 부하 전류(β 방향)'로 명시할 것을 권고한다. 함께 할 것:
  - (1) G1 정정: `load_dc_amp`를 DC KCL 입력으로 배선하거나, 계획 N3.8에서 미구현으로 표기한다.
  - (2) G3 규칙: netlist 부하 요소의 DC 전류와 `load_dc_amp`의 이중 선언을 금지하거나 판정한다.
  - (3) R 항 범위 위치 규칙: `swing_out_v`는 폭만 선언하므로 U 항목으로 연다.
- C·SR 항: 엔진에 넣지 않는다. 사용자가 원하면 C·SR + ΔV/R + I_dc를 직접 손계산해 `load_peak_amp`로 선언할 수 있다. 엔진은 그것을 DC 양으로만 다루므로 O-122와 충돌하지 않는다.
- 원칙 점검(이 권고):
  - graph 정본: 새 필드·cache 0. 하한은 spec 선언·봉인점 θ 전류·DE-1 창 필드를 READS한다.
  - 상수: 0(값 = 선언).
  - fail-closed: 범위 위치 없으면 미측정.
  - 회로 이름: β/σ 셀 분류(DEC-65 구조 판정)만 쓴다.
  - DC/AC: DC 항만이다.
  - DEC-103: 설계점은 θ 고정이다.
  - 손계산: 한 줄 식이다.
  - 원래 취지와 다름: (a′)는 없다. (a)는 있다(O-122).

## 6. 미확인

1. pushpull 버퍼 뷰에서 as-built `ls_fields` 보고가 나오지 않은 원인(swing bounds 비어 있음으로 추정)을 가르지 않았다.
2. DE-1 출력 창(선형 감도 끝)이 '전도 하한 행 R0'(O-119 정정 4)을 출력 범위에도 적용해서 R 부하의 전류 한계 끝(V = V_R + I_B·R_L)을 잡는지 확인하지 못했다. 잡는다면 R 항은 별도 제약 없이 `swing_out_v` 판정으로 이미 걸린다.
3. `swing_out_v` 창의 위치(동작점 대비 위·아래 몫) 정의를 계획에서 찾지 못했다. nmcnr 10 µA는 agnd 중심 가정이다(**추정**).
4. σ 최대 전류(§3.3)는 as-built LUT 규칙·손계산 근사다. O-26 (1) 정의값(oracle `.dc`)과 대조하지 않았다.
5. Johns & Martin·Razavi 교과서 쪽 번호는 저장소에 원문이 없어 확인하지 못했다. 웹 근거로 대신했다(아래).
6. current_reuse 피드백 C 등가(0.25 pF)는 손계산 추정이다.

## 7. 근거 링크

- Allen ECE6412 L040 'CE and CS Output Stages' p.040-3·040-5(Example 5.5-1): https://pallen.ece.gatech.edu/Academic/ECE_6412/Spring_2004/L040-CS&CEOut(2UP).pdf (로컬 사본 `wt/_scratch_mincur/dl/L040.pdf`, 텍스트 `L040.txt`)
- Allen Lecture 26 'Buffered Op Amps' p.26-2("sink and source sufficient current (CL·SR)"), p.26-25(Example 26-2: "SR = 10V/µs and 100pF capacitor give I15 = 1mA"): https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf · 로컬 `skills/analog-gmid-design/assets/library/sources/pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf`(paper.md 56·1225·1296행)
- Xie & Chen 2019 p.2 §II.B(class-AB 슬루·안정도 한계), Table I p.1: 로컬 `…/sources/current_reuse_telescopic_ota__xie_chen_2019/source.pdf`(paper.md 70-100·271-279행), 웹 찾지 못함
- ADI MT-045(full-power bandwidth = SR/2πVp): https://wcm-cce.cldnet.analog.com/media/cn/training-seminars/tutorials/MT-045_cn.pdf · LT1815 기사: https://www-cce.cldnet.analog.com/media/en/technical-documentation/tech-articles/lt-journal-article/LT1815_0501_mag.pdf
- Allen ECE6412 L140 p.140-6(노드별 SR = I/C), TI SLOA332: O-120 근거(user_decisions O-120 행)를 재인용했고, 이번에 다시 열람하지는 않았다.


## 8. 부하 선언 전수 조사(추가, 2026-10-24 사용자 지시 "load를 topology화일들(structure등을 포함. measurement용으로 분리된 passive 소자)도 찾아보고 결정하자")

- 범위: library 9회로 파일 전부다.
  - `*.topology.json`: `passive_elements`, `_passive_elements_comment`, `_declared_target_spec`, `_paper_target_spec`
  - `*.structure.json` 2개, `*.topology.md` 6개
  - `*.sizing_spec.json`: `element_values`, `value_from_*`, `compensation_targets`
- 같은 스크립트를 integ/it12와 master 사본에 돌렸고 출력이 같았다(`_scratch_mincur/scripts/loadsurvey.py`, `out/loadsurvey_integ.txt` = `loadsurvey_master.txt`).
- 계획 쪽 정본:
  - DEC-100(DUT / 응용 망 분리, O-73)
  - N3.16 명명 표 '부하 용량 = 부하 요소(예 `CL`)의 `value_farad`'(계획 914행)
  - DEC-58 '부하 용량은 부하 요소 참조'

### 8.1 '측정용으로 분리된 수동소자'의 정본 자리 (실측)

- **값의 정본은 spec `human.element_values.<원소>`다**(`value_farad`·`value_ohm`, 출처 필수).
  - topology `passive_elements`의 값 칸은 F5 이관 전 옛 자리다. 값이 남아 있으면 spec과 같아야 하고, 다르면 `element_value_conflict`로 거부된다(`E/authoring/spec_elements.py:16·49-64`).
  - topology의 `value_from_spec`(current_reuse의 `C_Ltot`·`Cf`·`Cc`)은 허용되지만 읽지 않는 키다(`E/authoring/passives.py:10·19`).
  - 그래서 값에 둘째 생산자는 없다. 충돌 검사가 막는다.
- **측정 전용 표지는 spec `element_values.<원소>.measurement_load: true`다**(`E/authoring/spec_elements.py:9·37·70`, 커패시터·저항만 받는다).
  - 이 표지의 소비자는 면적·layout뿐이다.
    - `passive_area_decl`: `E/search/area_decl.py:7·39-42`(호출 `E/pipeline/stage_b.py:167`, `E/search/search_context.py:180`)
    - layout: `E/layout/passives.py:5`, `E/layout/contract_input.py:169`
  - topology 쪽에는 측정 전용 표지(role·kind)가 없다. 주석(`_comment`)뿐이다.
- **해석은 측정 부하를 그대로 쓴다.** 근거는 DEC-100 (2)(3)이다.
  - "모든 해석 -- DC 동작점·스윙·ICMR, AC 루프·PM·잡음, 과도 -- = DUT ⊕ 측정 구성별 응용 망"
  - "해석에서 외부 소자를 빼지 않는다(예: nmcnr·r2r RL은 출력 DC를 정한다)"
- 실측한 엔진 소비자:
  - 값 → 봉인 스냅샷 수동소자 필드: `E/metrics/passive_values.py:34-36`, `E/metrics/ss_evaluate.py:100`
  - AC MNA·노드 용량: `E/metrics/ls_fields.py:39`
  - GBW 매크로(출발 구간): `E/search/macro_poles.py:98·291`. GBW 목표가 있을 때만 돈다(`:21`).
  - DC KCL(저항): nmcnr 층 0에서 I(M302) − I(M301) ≈ 30 µA = (1.658 − 0.9)/25 kΩ(§3.2)
- `*.structure.json` 2개(current_reuse `ac_ground_exception`, nmcnr `l_owner`)에는 부하 정보가 없다.

### 8.2 회로별 표 (고친 판)

| 회로 | C_L 값·출처 | R_L | DC 부하 전류 | 측정 전용 | 엔진이 읽는 자리 | 속도 선언 |
|---|---|---|---|---|---|---|
| common_gate_amplifier | **없음.** topology `passive_elements` = `[]`(0개), spec 주석 "부하 CL 은 SP-6(c) 대기" | 없음 | 없음 | -- | -- | 없음 |
| current_reuse_telescopic_ota | CL1·CL2 각 1 pF, spec `element_values`(user_spec SP-10). topology는 값 null + `value_from_spec: "C_Ltot"`(읽지 않는 키) | 없음 | 없음 | 예 | passive_values·MNA. 층 0 실패(B81)라 실측 경로 없음 | spec `compensation_targets.settling` total 40 ns·linear 30 ns(user_spec, 원문 Xie & Chen III.A). **소비자 0**(G2). 계단 크기 ΔV 선언 없음 |
| folded_cascode | 1 pF, spec(user TQ Q5). topology에 1e-12(옛 자리, 같은 값) | 없음 | 없음 | 예 | passive_values·MNA. GBW 미결(SP-5)이라 매크로 꺼짐 | 없음 |
| ngcc_3stage_ff | 10 pF, spec(U-39 채택). topology null, 이관 원천은 `_declared_target_spec.loading.CL_farad` 1e-11 | 없음 | 없음 | 예 | passive_values·MNA·GBW 매크로(10 MHz) | 없음 |
| nmcnr_amplifier | 100 pF, spec + topology 1e-10 | 25 kΩ(Vout–agnd), spec + topology | netlist R_L을 KCL이 센다(층 0 30.3 µA). `load_dc_amp` 선언 없음 | 예(CL·RL 둘 다) | passive_values·MNA·DC KCL·GBW 매크로(816 kHz) | spec에는 없음. **topology `_paper_target_spec`에만** SR +0.36/−0.31 V/µs, settling 3.03/3.04 µs, "unity-feedback, 0.5V step input"(논문 값, 채택 기록 없음) |
| pushpull_follower_buffer | 1 pF, spec(U-39). topology null | 없음 | 없음 | 예 | passive_values·MNA(rout 판정) | 없음 |
| sf_pushpull_output_opamp | 1 pF, spec(U-39). topology null | 없음 | 없음 | 예 | passive_values·MNA·GBW 매크로(60 MHz). 층 0 실패(B81) | 없음 |
| two_stage_ota | 3 pF, spec + topology 3e-12 | 없음 | 없음 | 예 | passive_values·MNA·GBW 매크로(7 MHz) | 없음 |
| two_stage_ota_sf | 3 pF, spec(U-39). topology null | 없음 | 없음 | 예 | passive_values·MNA·GBW 매크로(two_stage_ota 파일 참조) | 없음 |

§3.1 대비 고친 점:
1. 값의 출처는 spec `element_values`(측정 부하 표지 포함)이고, topology에는 원소만 있다.
2. common_gate는 `passive_elements` = `[]`(명시적 없음)이다.
3. nmcnr의 원문 속도 값(SR·settling·0.5 V 계단)은 topology 주석 칸에만 있다.
4. structure 파일에는 부하 정보가 없다.

### 8.3 다시 판정

**1. '부하 하한이 정의되는 회로'**
- 정의되는 회로는 그대로 nmcnr 하나다(R 항 10 µA, 범위 위치는 추정).
- nmcnr 원문 값을 쓰면 다음과 같다.
  - C·SR = 36 µA
  - C·ΔV/t: settling 3.03 µs를 전부 슬루로 보아도 100 pF·0.5 V/3.03 µs = 16.5 µA
  - 둘 다 층 0 전류 1.15 mA의 1/30 아래다.
- 게다가 이 값들은 spec 선언이 아니라 쓸 수 없다(논문 값 그대로 인용 금지 원칙, spec 출처 규칙).
- **결론(library 효과 0)은 바뀌지 않는다.**

**2. C_L과 속도 선언의 쌍**
- spec 안에 쌍이 있는 회로는 current_reuse 하나다(C_L 1 pF ×2 + settling 40/30 ns → 슬루 몫 10 ns).
- 하한을 만들려면 계단 크기 ΔV가 필요한데 선언되지 않았다. 출력 스윙 [−1.2, 1.2] V(원문 Table I)는 출력 범위 양이지 계단 크기가 아니다(O-119 이름 분리와 같은 구분).
- 그래서 하한은 **정의 불능**이다. ΔV를 지어내면 원문 전력(126 µW)과 4배 넘게 어긋난다(§1.5). settling은 엔진 소비자도 0이다(G2).
- `compensation_targets`의 `gbw_target_hz`·`pm_target_deg`는 속도 선언이 아니라 소신호 목표다. C_L과 짝지어 소신호 하한 gm ≥ 2π·GBW·C_out(계획 593행)을 만든다. 이 경로는 이미 매크로가 쓴다.

**3. 측정 전용 부하는 사이징 부하와 같은 양인가**
- **같은 양이다.**
  - DEC-100 (2)(3)에 따라 DC·AC·과도 해석 모두가 같은 부하 원소 값을 쓴다.
  - 엔진도 값 칸 하나(spec `element_values`)를 passive_values → MNA·KCL·매크로가 함께 읽는다(8.1).
- `measurement_load`가 따로 정하는 축은 **면적·layout 소속**(DUT 대 응용 망) 하나다. 전기 값은 다르지 않다.
- graph 규칙 3에 비추면 맞는 처리다. 전기 값은 필드 하나이고, 다른 축(면적 소속)은 표지 하나다.
- '동작 조건 부하'를 따로 둘 근거는 없다. 측정 구성과 다른 동작 부하를 원문이 선언한 회로도 library에 없다.
- DEC-100 (5) 2단계(card AP-1)가 응용 회로를 별도 topology로 옮겨도 같은 양이 자리만 옮긴다.
- 주의: G3(R_L netlist 원소와 `load_dc_amp`의 이중 계수)는 측정 부하에도 그대로 해당한다. nmcnr R_L은 이미 원소이므로 같은 부하를 `load_dc_amp`로 다시 선언하면 안 된다.

**4. LA-1 완료 조건 9 (a)(층 0 활성 회로 판단)에 주는 영향**

대상 판단은 v6.38 초안(`wt/plan-v638` `182124fa`)의 "ss 선언 library 회로 front ≥ 1"이다. 부하·측정 선언은 **층 0을 살리지 못한다.**
- 층 0 활성 조건(design 41 §5.1: gain 제약·이득 블록·rout 선언)은 부하 선언만으로 켜지지 않는다.
- 출발 구간 매크로 조건(`gbw_target_hz`, `E/search/macro_poles.py:21`)도 부하 선언만으로 켜지지 않는다.

folded_cascode:
- C_L 1 pF는 선언돼 있다. 그러나 gain(SP-4)·GBW(SP-5)·PM(SP-3)이 `pending_constraints`라 층 0은 무동작이고 매크로도 꺼져 있다.
- ss 선언은 `offset_excess`·`noise_excess_th`(비 지표)뿐이다. 같은 θ 밀도에서 이 둘은 전류 배율과 무관하다(gm 비만 들어감, **추정** -- 전류 스케일 불변을 실측하지는 않았다). 그래서 부하가 있어도 전류가 정해지지 않는다.
- SP-5(GBW)가 정해지면 C_L 1 pF와 짝지어 매크로가 켜지고, 출발 전류가 spec에서 정해진다.
- SP-4가 정해지면 층 0 gain 모드가 켜진다.
- 즉 folded를 살리는 것은 부하가 아니라 SP-4·SP-5 사용자 결정이다. 부하는 이미 준비돼 있다.

common_gate:
- C_L 원소가 없다(SP-6(c)).
- GBW(SP-5)가 정해져도 출력 노드에 고정 커패시터가 없으면, 매크로 기준 용량 `c_ref = max(고정 커패시터)`(`macro_poles.py:291`)가 None이 된다(**추정** -- 이 경우의 매크로 동작은 실측하지 않았다).
- 그래서 SP-6(c)(부하 원소 추가, 사용자 connectivity)와 SP-5가 둘 다 있어야 한다.
- 다만 이 회로는 지금도 층 0 점에서 ss 위반이 0이라 front 2점이다(B80 §4). 부하 선언과 무관하게 9 (a)를 통과한다.

나머지 7회로:
- 9 (a) 판단은 rout·gain·GBW 선언으로 이미 정해져 있고, 부하 선언은 그 판단을 바꾸지 않는다. C_L은 이미 GBW·PM·rout 판정에 들어가 있다.

판단 권고:
- 9 (a) 대상 = 'ss 제약을 선언한 회로'를 유지한다.
- folded_cascode는 'ss 선언이 비 지표뿐이라 전류를 정할 spec이 없음 → 층 0 무동작 + 성능 판정 보류'로 분류하고, front ≥ 1 판정에서 빼서 따로 보고하는 것이 맞다고 본다.
- ⚠ 원칙 경고: 사용자 결정 대상 — 완료 조건 대상에서 회로를 빼는 것은 기준 변경이다 — O-125 원문 "ss 제약(rout·gain 등)을 선언한 library 회로"에 folded(offset·noise)가 드는지 문언이 모호하다. 그래서 이 분류는 오케스트레이터가 판단하지 않고 사용자 확인 사항으로 올린다.

### 8.4 바뀐 결론 요약

- 결론 1~5(§0)는 그대로다. library에서 부하 하한의 효과는 0이다. 권고도 그대로 지금은 (c), 계획 기록은 (a′)다.
- 더하는 사실:
  1. 측정 부하는 해석 부하와 같은 양이고, 다른 것은 면적·layout 소속 표지 하나다(DEC-100). 새 필드는 필요 없다.
  2. spec 안의 C_L+속도 쌍은 current_reuse settling 하나다. ΔV가 없어 정의 불능이고, 소비자도 0이다(G2).
  3. nmcnr 원문 속도 값은 topology `_paper_target_spec`에만 있고 spec 선언이 아니다. 채택하려면 사용자 결정이 필요하다.
  4. folded·common_gate를 살리는 것은 부하가 아니라 SP-4·SP-5(·SP-6(c)) 결정이다.
- 새 미확인 항목(§6에 이어서):
  - 7. C_L 원소가 없는 회로에서 GBW 매크로가 어떻게 동작하는지
  - 8. `offset_excess`·`noise_excess_th`가 전류 스케일에 불변인지(실측)
