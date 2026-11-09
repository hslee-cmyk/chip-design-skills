# off 선언 원리 후보 -- off·전도·꺼짐·반전 하한 규칙 전수 감사 (2026-11-06)

- 역할: 감사자(문서·분석, 커밋 없음). 작성자 자기 점검만 했고 독립 모순 점검은 따로 해야 한다.
- 원리 후보(사용자 제안, 오케스트레이터 정리, "진행해"): 'off는 선언(`intended_region` `off`, EO-1 범위 4·A-2)으로만 존재한다. 선언 안 된 소자는 선언 방향으로 전도해야 한다(부호만 보고 문턱은 없다).'
- 읽은 기준판:
  - 계획 = `wt/20261106-o248-plan`(브랜치 `plan/o248`, 머리 `18d82225` = 커밋 B, v6.38.27, 판정 중). 줄 번호는 이 판 기준이고 P:줄로 적는다.
  - 엔진·oracle = `wt/20261105-wb1-c`(머리 `6887bc3e`). `E/` = `skills/analog-gmid-design/gmid_engine/`, `O/` = `skills/analog-gmid-design/tools/spice_oracle/`.
  - master `4d7d8f45`에서 `_conduction_floor`·`_conduction_ok`·`_peak_floor`·`CON_INVERSION` 자리가 같은지 `git grep`으로 확인했다(줄만 ±1 다름).
- 엔진 인용 용도(원칙 8): 지울·바꿀 코드와 그 소비자를 적는 재작성 범위로만 썼다. as-built는 판정 근거로 쓰지 않았다.
- 측정: 읽기 전용 스크립트 하나를 돌렸다(`C:/Users/HSLEE/AppData/Local/Temp/la1s_off40/sat_vs_sign.py`, 결과 `sat_vs_sign.out.txt`). LUT v2 기준 npz(`lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz`)를 읽었고 ngspice·pytest는 돌리지 않았다.

## 0. 결론 요약

1. **분류 39행**: (가) 11, (나) 12, (다) 7, (라) 9.
   - 결정 층(O-202~O-212)은 이미 원리와 같은 쪽이다. O-205 (1)은 전도 = 선언 방향 ID > 0으로 정했고, O-203은 S_d에 전도 여유 행을 두지 않았고, O-207은 P-7을 철회했고, O-202·O-212는 off를 선언으로만 다룬다.
   - **남은 (가)는 엔진 탐색·LUT 파생 코드, 계획·design 문언, graph-consumption 문언에 있다.** 핵심은 넷이다: `_conduction_floor`, `_conduction_ok`의 ε 항과 분지 요구, graph-consumption `conduction_mask` 신설 계획, 커밋 B의 '전도 하한 집계 규칙' 문언.
2. **탐색 전도 하한 `E/search/cell_floor.py:53-85` `_conduction_floor` = (가)이고 삭제 대상이다.**
   - 식이 옛 봉인 9 `I_off ≤ ε·ID`, ε = (gm/ID)·tol_V 그대로다(docstring :15-22). O-205 (1)이 지운 바로 그 식이다.
   - O-203은 'S_d·탐색 개방 범위에 전도 여유 행을 두지 않는다'고 정했다. design 40 :345도 '`conduction_floor` 삭제(O-205)', :1448도 '폐기'라고 이미 적었다.
   - 그래서 커밋 B(`18d82225`)의 N3.6 표 10행 (ii)와 N6.40 LM-1e 3b (ii)가 이 하한에 집계 규칙을 적용하는 것은 지울 코드를 고쳐 쓰는 일이다. 같은 design 40 문서 안에서도 서로 어긋난다(:345·:1448 대 :1259).
   - 계획 LA-1 완료 8에는 `CON_INVERSION`·`_peak_floor`만 있고 `_conduction_floor`가 빠져 있다. 지금은 이 하한을 지우는 card가 없다.
3. **(다) 유지 근거를 바로잡아야 한다.** '포화 판정만으로는 ID ≈ 0 소자를 못 잡는다'는 사실이지만 부호 판정도 그런 소자를 못 잡는다. LUT 실측은 이렇다.
   - 포화를 통과한 칸의 ID 최솟값은 nfet 3.2e-19 A, pfet 2.9e-26 A다. 이 칸들은 모두 ID > 0이라 부호 판정도 통과한다. 원리상 이 소자들은 전도(깊은 약반전)이고 기능 판정은 spec 제약이 맡는다.
   - 부호 판정을 유지할 실제 근거는 셋이다.
     - (i) 엔진 정의역 조건이다. ln IDu·gm/ID는 ID > 0에서만 정의된다(O-203). θ 경로에서는 θ 전류 원뿔이 이미 보장하므로 봉인 9 cutoff는 fail-closed 가드다.
     - (ii) oracle에서 선언 없는 소자는 포화 판정이 이미 함의한다. LUT에서 VDSAT > 0이 432180/432180칸이고, VDS > 0이면서 ID ≤ 0인 칸은 0/423360이다. 그래서 ID ≤ 0 ⇒ VDS ≤ 0 < VDSAT ⇒ 포화 FAIL이다. 부호 판정은 사유 표지만 더한다.
     - (iii) `triode` 선언 소자에서는 부호 판정이 꺼짐과 triode를 가르는 유일한 판정이다.
   - 이 근거들은 모두 '꺼짐 분류'가 아니라 정의역·방향 정합이다.
4. **처리 권고**(card +0):
   - LM-1e 3b (ii)에서 `_conduction_floor`를 뺀다(재작성하지 않음).
   - LA-1 O-207 묶음 완료 8에 다음을 더한다: `_conduction_floor`, `ln_idu_floors`, `sctx.cell_floors`, `_conduction_ok`의 ε 항과 분지 요구가 0이어야 한다.
   - graph-consumption GC-7의 `conduction_mask` 신설을 철회한다. 술어가 ID > 0이면 기존 LUT `on_mask`와 같은 정의라서다(graph 규칙 3).
   - LA-1 차단 여부: `_conduction_floor`는 S_d 정의(O-203)를 어기므로 **차단**이다. `_conduction_ok` ε 항은 물리 경계를 tol_V가 정하는 꼴이라 **차단**이다(작성자 판단, 영향 미측정). 나머지는 비차단이다.

## 1. 분류 표

열 설명: 분류 / 자리 / 문언 인용(요지) / 소비자 / 원 결정 근거 / 분류 이유 / 처리(재작성 범위·card)

### (가) 문턱으로 off·전도·반전을 분류하는 규칙 -- 지울 후보 (11)

| # | 자리 | 문언 인용 | 소비자 | 원 결정 | 분류 이유 | 처리 |
|---|---|---|---|---|---|---|
| G1 | `E/search/cell_floor.py:53-85` `_conduction_floor`, docstring :15-22 | "전도 MOS 는 I_off ≤ ε·ID, I_off = IDu(VGS=0)·W/L, ε = (gm/ID)·tol_V ... ln IDu(VGS) + ln(gm/ID(VGS)·tol_V) ≥ ln IDu(0) -- 좌표 하한" | `ln_idu_floors`(:105, 모든 `ln_idu` 성분) → `search/slsqp_outer.py:68`(외층 상자 하한), `search/layer0_center.py:285·:468·:566`(층 0 상자) | r8/r9 봉인 9(U-69·O-50 G3) → **O-205 (1) 삭제, O-203 S_d·탐색 개방 미적용, U-69 철회**(P:2822) | 분해능 tol_V가 VGS 하한을 정한다. O-205 (1) 근거 '분해능 tol_V가 VGS 문턱을 정해 원칙 1에 어긋남'(P:678)이 그대로 걸린다. 탐색 상자를 S_d(O-203) 밖으로 자른다 | **삭제**. 지금 맡은 card가 없다(LA-1 완료 8 P:2114에 없음, GC-7 P:2651은 '존폐는 GC-7 몫'). §4 권고: LA-1 O-207 묶음 |
| G2 | `E/search/cell_floor.py:35-50` `_peak_floor` | "gm/ID 정점 마디의 ln IDu ... 강반전 분지 시작 위" | `ln_idu_floors`(one_var_only일 때 1변수 writer) | P-7 → **O-207 철회** | 반전 수준 하한이다(정점 = 수치 잡음 위치, O-207 실측) | 삭제 -- LA-1 O-207 묶음(P:2114 완료 8, 이미 배정) |
| G3 | `E/search/search_values.py:35` `CON_INVERSION = "inversion_floor"`, `search/layer0_center.py:62·:73`(경성 제약 접두), `search/search_domain.py:12`, `search/realize_front.py:10` | "조회점별 실제 하한은 부등식 제약(constraints `inversion_floor`)" | 층 0 경성 제약, 실현 front 손실 사유 | P-7 → **O-207 철회** | 반전 수준 문턱 행이다 | 삭제 -- LA-1 O-207 묶음(이미 배정) |
| G4 | `E/lut/derived_fns.py:39-50` `_conduction_ok`의 `gm·tol_V ≥ I_off` 항, docstring :8-10 | "VGS 엣지 비용 = 봉인 9(전도 여유)를 지킬 수 있는 격자 행 ... VGS = 0 마디는 꺼진 소자라 이 조건이 뺀다" | `edge_costs` → `metrics/achievability.py:280` `_headroom` → `headroom_bound`(달성 가능성 헤드룸 하한), `search/_helpers_curves.py:84`·`iv_headroom.py:156`(VGS 엣지 비용) | 옛 봉인 9 ε → **O-205 (1) 삭제**. 'VGS = 0 마디는 깊은 약반전 채널 동작점(누설점 아님)'(O-203·O-212) | ε 문턱으로 전도 행을 고르고 VGS = 0 마디를 꺼짐으로 분류한다. O-203 문언과 정반대다 | **ε 항 삭제**(ok = 분지·on만). N3.6 정본 (7)이 'GC-7 -- 술어 = ID > 0으로 줄어듦'이라고 적었지만 GC-7은 LA-1 뒤일 수 있다(P:1368 '착수 전'). §4 권고: LA-1 O-207 묶음 |
| G5 | `E/lut/derived_fns.py:43-45` `_conduction_ok`의 `branch`(VGS ≥ gm/ID 정점) | "분지 마디(VGS ≥ gm/ID 정점)" | 같은 `edge_costs` | P-7·옛 gm/ID 역산 분지 → **O-207 철회, O-186**('가장 큰 VGS 해 같은 gm/ID 분지 규칙은 두지 않는다', DEC-88 P:288) | 반전 수준(정점) 문턱이다 | 삭제. **배정 누락**: LA-1 완료 8은 `peak_index` 소비만 적고 `_conduction_ok` 안의 인라인 argmax는 적지 않는다 |
| G6 | graph-consumption 계획 U-G4·GC-7·GD-12·F-G14(gc :209·:643·:758·:784, 0.14.10) | "칸별 전도 술어의 정본은 LUT memo 파생 함수 `conduction_mask(kind, w_key)` 하나(마스크와 곡선별 첫 전도 마디·보간 근, VGS = 0 마디 찾기도 이 한 곳)" | 계획 문언뿐(코드 없음, `git grep conduction_mask` 정의 0) | O-13 (가)·O-15 (A). O-205는 '원래 취지와 다름'에 'O-15 (A)·GC-7 ... 대상 소멸·축소'를 적었다(user_decisions O-205 행) | 술어가 ID > 0이면 '첫 전도 마디'는 `on_mask` 첫 마디다. 기존 LUT 필드 `on_mask`((ID > 0) & (GM > 0), `E/lut/lut_set.py:197`)와 같은 정의라 graph 규칙 3에 걸린다. VGS = 0 마디 찾기는 G1·G4가 지워지면 소비자가 G7 하나만 남고, G7도 재정의하면 0이다 | **신설 철회**(새 집합·갈래 불필요). gc 문언 정정은 LA-1 재점검 입력. 코드가 없어 비차단 |
| G7 | `E/search/current_box.py:5-7·:24-28` I_off 근거와 `lut_vgs_zero_missing` 거부 | "이보다 작은 전류는 어느 동작점에서도 꺼진 소자와 구별되지 않는다" | `search_domain`(θ 전류 상자 하한), `metrics/block_gain_bound.py:118`, `search/start_values.py:155` | S-3(2026-10-08). design 41 §4.2 :516은 '하한은 S_d와 같은 정의: 선언 방향 ID > 0 ∩ LUT 정의역(O-203·O-212), 옛 I_off와 다르면 재작성 범위' | **근거 문언과 VGS = 0 요구가 (가)**다. 값 자체는 정의역 최소 ID와 같다(VGS 격자 최소 = 0 V 실측, ID가 VGS에 단조라 최소가 VGS = 0 면에 옴 -- 작성자 유도) | 값 불변. 근거를 'LUT 정의역(on_mask) 최소 ID'로 고치고 VGS = 0 마디 요구를 지운다. 비차단, LA-1 재점검 입력(또는 S_d를 쓰는 LA-1에서 같은 정의를 READS) |
| G8 | `O/core/compare.py:26·:211-223·:253-257` `off_current_A` 문턱(\|ID\| < thr → region 'off', `conduction_check` FAIL = ID ≤ thr), `O/oracle_swing.py:15`, `O/oracle_input.schema.json:417-421·:749`, `O/smoke/smoke_judge.json:4` | "\|ID\| 가 이보다 작으면 영역 'off'" | oracle 합격·범위 판정 | 옛 C23·O-45 U2 → **O-205 (2)·O-210 RR-2 삭제** | 전류 문턱으로 꺼짐을 분류한다 | 삭제 -- OP-5(N3.6 정본 (7) P:684, oracle N3.9 :438, 이미 배정). OP-5는 LA-1 측정 시점 전(위임 A-8) |
| G9 | `O/core/compare.py:271-272` `vov_spice`·`below_vth_spice` | "below_vth_spice: vov < 0" | 기록 전용 | VTH 열 소비자 0 → **O-246 D3 삭제**(LG-1) | VTH 문턱으로 꺼짐·약반전 표지를 단다(판정엔 안 씀) | 삭제 -- LG-1(N6.41, LA-1 뒤, 이미 배정). 비차단 |
| G10 | 커밋 B `18d82225`: P:663 표 10행 '규칙의 범위' (ii)의 "탐색 상자 전도 하한(곡선마다 tol 셀을 쓰는 근의 max)도 같은 규칙", P:2651 LM-1e 3b (ii) "`search/cell_floor.py` `_conduction_floor`의 '정의된 항만' 집계 → 항에 None이 있으면 None ... 옛 봉인 9 ε 꼴(O-205로 판정 쪽 삭제)인 이 하한의 존폐는 graph-consumption GC-7 몫", P:2654 완료 (1) '3b (ii) toy -- ... 전도 하한 항 일부 None → None', design 40 :1259 끝 문장, design 42 :349 D-LM1e | -- | LM-1e spec card·test 작성자 | 위임 A-144(`la1_auto_decisions.md`:150) | 지울 (가)를 살린다는 전제로 고쳐 쓴다. 'O-205로 판정 쪽 삭제'는 사실과 다르다 -- O-203이 탐색 쪽도 지웠다(S_d·탐색 개방 미적용). design 40 :345 '`conduction_floor` 삭제', :1448 '폐기'와 모순이다 | **plan/o248 판정 중 정정**: 표 10행 (ii)에서 전도 하한 항을 빼고(b_P·ICMR cfg `tol_v`는 유지), 3b (ii)와 완료 (1)의 전도 하한 toy를 지운다. '존폐는 GC-7 몫'을 '삭제 = LA-1 O-207 묶음'으로 고친다. design 40 :1259·D42 :349도 같이 고친다 |
| G11 | 문언 잔재: `E/sizing/s2_values.py:81` "[r8] 전도 여유: VGS=0 누설 ≤ ε·ID", `E/search/search_context.py:12·:68`(`cell_floors`), `E/search/slsqp_outer.py:7`, headroom-chain :86 인용 `seal_saturation.py:55-56`(파일 없음 -- `seal_region.py`로 바뀜) | -- | 동작 0 | -- | (가) 문언이 남았다(동작 없음) | 해당 코드를 지우는 card에서 같이 지운다. headroom-chain 인용은 LA-1 재점검 입력 |

### (나) 선언 기반 규칙 -- 유지 (12)

| # | 자리 | 요지 | 원 결정 | 분류 이유 |
|---|---|---|---|---|
| N1 | spec `human.intended_region` {`triode`, `off`}, `E/authoring/spec_regions.py:1-19·:55`(`w_m`·`l_m`·`judged_by`는 `off`만) | 선언 어휘·칸 | O-53 B1, O-221, A-1 | 선언 그 자체 |
| N2 | P:682 정본 (5) (가), `E/sizing/current_basis.py`(off 열거 제외), `kernel_context.py:11`, `search_domain` kind 목록 | off 선언 = 사이징·역산·포화 요구에서 뺄 때만 | O-202 (1), O-55 V5·O-56 | 선언을 읽는 술어 하나 |
| N3 | 정본 (5) (나)(다)(라): 봉인점 off 전류 0 모형, ΔV = −G⁻¹·ΔI_off, `device.off_op`(`ss_off_op`), `graph.ss_off_delta`(`E/metrics/ss_off_delta.py`), 소신호 스탬프(A-2, `ss_linearize.py:66-83`) | off 소자 효과 1차 | O-202 (2), A-2·A-12 | 선언된 소자에만 |
| N4 | 정본 (5) (마) G2-a, `E/metrics/ss_off_gate.py` | 보정 포화 여유 s < 0 거부(tol 미사용) | O-202 (3), O-222 | 선언이 있을 때만 돈다 |
| N5 | 정본 (5) (바) O-h `judged_by` | off의 기능 결과 = 사용자가 선언한 metric | O-202 (4), O-221 | 판정 근거도 선언이다 |
| N6 | 정본 (5) VGS < 0 off 소자 점 E-0 정지(`ss_off_op`) | LUT 정의역 밖 | O-212 | 선언 소자 + 정의역 |
| N7 | 표 6행·정본 (3) off 소자 벌크 판정을 `off_op`에서(A-47) | 봉인 6과 같은 식 | O-210 RR-7, A-47 | 선언 소자 |
| N8 | `E/sizing/region_judge.py` 행 1(off → `not_judged`), 정본 (6) oracle off 대상 밖, design 41 :1043 predictions region = `region_decl` 사상 | 선언 영역 대조 없음 | O-202 (1) | 선언만 읽음 |
| N9 | offset-trim G-1(ot :654) `augment_trim`이 코드 상태마다 `off` 선언 | trim 스위치 = 선언 | O-53 B1 | 사용자 예시(trim)와 정확히 같다 |
| N10 | 정본 (11) g = s 소자 = 일반 선언 규칙 | '꺼짐' 분류 삭제 | O-210 RR-6 | 선언 없음 = 포화 기본 |
| N11 | gc :354 `cell_floor`는 off 선언을 다시 거르지 않음(θ 스키마를 따름) | 둘째 거르기 금지 | 규칙 L-5 | 선언 술어 하나 |
| N12 | 표 9행 다리 규칙에서 off 소자 엣지를 뺌 | 0 모형과 같은 뜻 | O-182, A-22 | 선언 반영 |

### (다) 부호·방향 정합성 -- 유지 (근거는 §3에서 고침) (7)

| # | 자리 | 요지 | 원 결정 | 분류 이유 |
|---|---|---|---|---|
| D1 | P:662 표 9행 (i)·정본 (1), `E/sizing/region_judge.py:47-48`(current ≤ 0 → cutoff), `seal_region.py` 봉인 9 cutoff → fail | 선언 방향 ID > 0, ≤ 0 거부 | O-205 (1) | 부호만 본다 -- 정의역 조건 |
| D2 | θ 전류 원뿔 `current_cone`(`E/sizing/theta_schema.py:30-31`, `search/cone_rows.py`, `check_theta`), `sizing/block_currents.py:30-32`(전도 MOS 전류 ≤ 0이면 ValueError) | 엔진 정의역 ID > 0 | O-203, DEC-70 | θ 단계에서 보장하는 정의역 |
| D3 | LUT `on_mask` = (ID > 0) & (GM > 0)(`E/lut/lut_set.py:197`, `lut_types.py:133`) | 표본 정의역 | DEC-87 | ln·gm/ID 정의 조건(문턱 아님) |
| D4 | 정본 (9) S_d = 정의역 ∩ 선언 방향 ID > 0 ∩ 실현 ∩ 순방향 | 출발 정의역 | O-203 | 부호만 본다 |
| D5 | 정본 (6) oracle 채널 op ID ≤ 0 = FAIL, oracle N3.9 :436, offset-trim :346(온도 점 부호), headroom-chain :86·:373 | oracle 꺼짐 = 부호 | O-205 (2)·O-210 RR-2 | 엔진과 같은 식 |
| D6 | 표 9행 (ii) `triode` 선언 MOS 선언 방향 ID ≤ 0 = 선언 오류 | triode 쪽 방향 정합 | O-53 B1 | 부호. 원리 문장이 '선언 안 된 소자'만 말해서 따로 확인해야 한다(§6 C3) |
| D7 | T4·T4-pre 전도 = 채널 op ID 부호(P:1501·P:1516) | 판정 정의 | O-205 (2) | D5와 같은 정의 |

### (라) 기타 (9)

| # | 자리 | 설명 |
|---|---|---|
| R1 | 표 9행 KCL 항등 0 전류 MOS 예외(다리 규칙, O-182 Q-S9 (A′)), `E/sizing/current_basis.py` `mos_zero_current_structural` 정지(DR-1 대기) | 연결에서 나오는 구조적 0 전류다. 선언도 문턱도 아니다. 원리 문장이 "선언 안 된 소자는 전도해야 한다"고만 하면 이 집합과 충돌하므로 예외로 적어야 한다 |
| R2 | 정의역 경계 기록 `domain_edge`(`seal_region.py` 봉인 9 detail, O-212) | 출력 전용. 꺼짐 판정이 아니다 |
| R3 | `E/lut/derived_fns.py` `vds_floor` | `on_mask` 열이 전부 참인 첫 VDS = 정의역 데이터 사실 |
| R4 | `E/graph/dc_conduction.py`(S1 DC 전도 그래프 잎 가지치기) | 이름만 'conduction'이고 저항 가지치기다. 연결 구조 |
| R5 | `current_box` I_off의 **값** | G7과 짝. 정의역 최소 ID와 같은 값 |
| R6 | tol_VDsat '구별 불가' 띠(정본 (2)) | 포화 경계 기록. off와 무관(참고) |
| R7 | 정본 (1) 'VGS = 0 마디 = 채널 동작점'(O-203·O-212 문언) | 원리와 같다. G4 docstring이 이 문언과 반대다 |
| R8 | 비채널 누설(GIDL·접합)은 LUT 밖(O-212), LUT 확장 = TR 착수 조건 | off 판정이 아니라 데이터 범위다 |
| R9 | b_P `metrics/dc_metrics.py` `_power_resolution`, ICMR `metrics/icm_config.py` `_tol_v` (커밋 B 표 10행 (ii)) | off·전도와 무관한 tol 집계다. 커밋 B의 규칙 적용은 그대로 둔다(이 감사 범위 밖) |

## 2. 탐색 전도 하한 판정

- **식**(`E/search/cell_floor.py:15-22`, :75): f(VGS) = log_GM(VGS) + ln tol_V(L, VDS) − log_ID(VGS = 0) ≥ 0, 즉 gm·tol_V ≥ I_off(VGS = 0). 작성자 표지가 적은 대로 옛 봉인 9 ε 꼴이다(ε = (gm/ID)·tol_V, I_off ≤ ε·ID ⇔ gm·tol_V ≥ I_off).
- **원 결정·근거**: r8/r9 봉인 9(CONTRACT §6·O17) 상자 = U-69 '봉인 9 전도 하한의 연속 제약화'(2026-10-12). 모두 철회됐다.
  - **O-205 (1)**: 전도 = 선언 방향 ID > 0만이고 식은 삭제한다. 근거는 'tol_V가 VGS 문턱을 정함 = 원칙 1 위반'(P:678)이다.
  - **O-203**: 'S_d에 봉인 9 전도 여유 행(U-69) 적용 안 함, VGS = 0 마디는 깊은 약반전 채널 동작점'. 계획 정본 (9) P:686은 'S_d·탐색 개방 범위에 두지 않는다'고 적었다.
  - **U-69 철회**(P:2822): '전도 여유 행은 봉인·S_d·탐색 어디에도 두지 않는다'.
  - **design**: design 40 :345 '`conduction_floor` 삭제(O-205)', :1448 '폐기: 칸 정점·전도 하한으로 θ 상자를 조이는 경로', design 41 W7(:669) '전도 문턱·반전 수준 하한 제약 철회(코드 구현 = card LA-1 O-207 묶음)'.
  - O-205 원문의 사용자 질문도 같은 쪽이다: "약반전 영역설계는 못한다는 뜻인가?" → 답 "P5는 약반전 전 구간을 전도로 받아 현행 봉인 9의 tol_V 하한을 없앰".
- **판정: (가)다.** 문턱(tol_V × gm 대 VGS = 0 전류)으로 '전도 가능 좌표'를 가른다. 판정을 하지 않는 상자라도 탐색이 닿을 수 있는 θ를 S_d 정의 밖 기준으로 자른다. 그래서 원리와 O-203 S_d 정의에 직접 어긋난다.
- **귀결**:
  - 커밋 B의 집계 규칙(표 10행 (ii)·LM-1e 3b (ii)) **적용 대상이 아니라 삭제 대상이다**. 3b (ii) 문언 '옛 봉인 9 ε 꼴(O-205로 판정 쪽 삭제)'의 '판정 쪽'은 틀렸다. O-203·U-69 철회가 탐색 쪽도 지웠다.
  - 커밋 B 스스로도 '(i) 뒤 실 LUT에서 대부분 하한 없음이 될 수 있다(탐색 상자가 넓어지는 쪽)'라고 유도했다. 고쳐 쓰는 일 자체가 삭제로 수렴하는 작업이라 들일 가치가 없다.
- **과도기 안전**(LM-1e를 이 하한 없이 병합하고 LA-1에서 지울 때):
  - LM-1e 3b (i)로 `table_at`이 None을 더 내면 `_conduction_floor`는 그 곡선을 건너뛴다(:70 `if not tol: continue`). 곡선 수가 줄어 max 하한이 같거나 낮아지고 상자는 넓어진다. 상자는 판정이 아니므로 fail-open이 아니다(작성자 유도, 측정 안 함).
  - 그래서 LM-1e가 이 하한을 건드리지 않아도 판정 안전성은 같다.
- **LA-1 차단**: **차단**이다. LA-1은 S_d를 O-203 정의로 구현하는 card다(design 41 W7). 이 하한이 남으면 그 card의 S_d 상자가 정의와 다르다. O-229 1 '물리 정합 완화 금지'에 해당한다. 계획 LA-1 완료 8(P:2114)에 `_conduction_floor` 0이 없다는 것이 배정 누락이다.

## 3. (다) 유지 근거 검증

### 3.1 LUT 실측 (`sat_vs_sign.out.txt`, 기준 npz)

격자: VGS 0~1.8 V(49), VDS 0~1.8 V(49), VS 0~1.8 V, L 18.

| 항목 | nfet | pfet |
|---|---|---|
| (a) VDS > 0 칸 중 ID ≤ 0 | 0 / 423360 | 0 / 423360 |
| (a) VDS = 0 칸의 \|ID\| 최대 | 0 (8820칸 전부 ID = 0) | 0 (8820칸) |
| (b) VDSAT ≤ 0 칸 | 0 / 432180, 최소 37.84 mV = 1.46 U_T | 0 / 432180, 최소 39.64 mV = 1.53 U_T |
| (c) VDS ≥ VDSAT 통과 칸 중 ID ≤ 0 | 0 / 373839 | 0 / 388473 |
| (c) 통과 칸 ID 최소 / p1 | 3.2e-19 A / 3.7e-17 A | 2.9e-26 A / 2.1e-23 A |
| (d) VGS = 0 면에서 포화 통과 | 8460 / 8820, ID 3.2e-19 ~ 5.8e-12 A | 8460 / 8820, ID 2.9e-26 ~ 4.2e-10 A |
| (e) VDSAT p50(VGS = 0 / 0.15 / 0.3 V) | 44.0 / 44.0 / 44.0 mV | 47.1 / 47.1 / 47.1 mV |
| (e) 같은 VGS의 ID p50 | 1.0e-15 / 7.6e-14 / 5.7e-12 A | 2.6e-20 / 3.0e-18 / 3.7e-16 A |

### 3.2 해석 (물리·회로이론, 원칙 21)

- **물리 결정자**: 약반전 채널 전류는 I ∝ e^{VGS/nU_T}(1 − e^{−VDS/U_T})다. 포화 전압 VDSAT는 약반전에서 수 U_T 바닥에 머물고 ID와 무관하다. 실측 (e)에서 ID가 4자릿수 변해도 VDSAT p50은 그대로다. BSIM 2·vt 항이고 `o245_terminal_dc_columns.md` §2.2 BSIM VDSAT 약반전 p50 1.75 U_T와 같다.
- **'포화 판정만으로는 ID ≈ 0을 못 잡는다'**: **맞다**. 실측 (c)(d)에서 깊은 약반전 ID 1e-19~1e-26 A도 VDS ≥ VDSAT를 통과한다. 그런데 **부호 판정도 이 소자를 못 잡는다**(ID > 0). 그래서 이 문장은 부호 판정을 유지할 근거가 되지 못한다. 원리상 이 소자는 전도이고(O-205 답 '약반전 전 구간 전도'), 그 기능 결과(이득·GBW 등)는 spec 판정 제약이 판정한다.
- **부호 판정의 실제 역할**:
  1. **엔진**: ln IDu·gm/ID 좌표는 ID > 0에서만 정의된다(정의역, O-203 D2·D3).
     - θ 경로에서는 θ 전류 원뿔(`check_theta`, `block_currents.py:30-32`)이 모든 전도 MOS 전류 > 0을 먼저 보장한다. 봉인 9 cutoff 갈래는 θ 경로에서 닿지 않는 fail-closed 가드다(작성자 정적 유도).
     - 실현·레이아웃 뒤 재풀이(`block_dc._kcl_solve`, MOS = LUT IDu·W′/L)에서는 ID ≤ 0이 on_mask 밖(VDS ≤ 0)에서만 나온다. 그때는 `reverse_vds`(triode)나 정의역 밖으로 먼저 걸린다.
     - **중복이지만 규칙 하나·문턱 0**이라 지울 이득이 없다. 남기는 것은 정의역 단언이다.
  2. **oracle(선언 없는 소자)**: 채널 전류 부호 = VDS 부호다(실측 (a) 0/423360 -- 다만 LUT는 VDS ≥ 0만 있어 역방향은 대칭성으로 유도, ⚠ 아래). VDSAT > 0이다(실측 (b)). 그래서 ID ≤ 0 ⇒ VDS ≤ 0 < VDSAT ⇒ 포화 FAIL이 늘 함께 난다. 부호 판정은 FAIL 사유('꺼짐' 대 '비포화')를 가르는 표지만 더한다. 판정 결과는 바뀌지 않는다.
  3. **`triode` 선언 소자**: 포화 대조는 'VDS < VDSAT이면 선언대로'라서 ID ≤ 0(VDS ≤ 0)도 triode로 통과한다. 부호 판정만이 꺼짐·역방향을 선언 오류로 잡는다(표 9행 (ii), O-53 B1). 이것이 부호 판정이 **판정을 실제로 바꾸는 유일한 자리**다.
- **판정**: (다) 유지는 **조건부로 맞다**. 유지 근거를 '포화가 ID ≈ 0을 못 잡아서'에서 '정의역 단언(엔진) + 방향 정합(triode 선언·사유 표지)'으로 바꿔야 한다. 부호 판정은 꺼짐 분류가 아니다 -- 원리 문장에 그렇게 적는다.
- ⚠ **불확실**:
  - ngspice BSIM4에서 역방향 소자의 `@m[vds]`·`@m[vdsat]` 부호 관례는 실측하지 않았다(ngspice 금지 범위). 어댑터가 ID만 선언 방향 부호로 정규화한다(`O/core/compare.py:244` 주석). 그래서 oracle에서 '포화가 부호를 함의'하는지는 VDS 정규화 여부에 달렸다 → oracle 쪽 부호 판정은 지우지 않고 유지하는 것이 fail-closed다.
  - VDSAT 열이 없는 소자는 부호 판정만 남는다.

## 4. 원리 문장 초안과 처리 목록

### 4.1 원리 문장 초안 (근본원칙 후보 -- 원칙 19, 사용자 승인 전 적용 금지)

> **off는 선언으로만 존재한다.** MOS의 꺼짐(off)은 spec `intended_region` `off` 선언(N3.6 정본 (5))으로만 생긴다.
>
> 엔진·oracle·탐색·LUT 파생은 수치 문턱으로 소자를 꺼짐이나 비전도로 분류하지 않는다. 그런 문턱으로 정의역·탐색 상자·경로 비용을 자르지도 않는다. 수치 문턱이란 전류 크기, 분해능(tol_V·tol_I), 반전 수준(gm/ID 정점), VTH를 말한다.
>
> 선언 없는 소자와 `triode` 선언 소자는 선언 방향으로 전도한다. 전도 = 선언 방향 채널 ID > 0이고, 부호만 보며 문턱은 없다. 아무리 작은 양의 ID(깊은 약반전)라도 전도이고, 그 기능 결과는 spec 판정 제약이 판정한다.
>
> 부호 판정은 꺼짐 분류가 아니라 정의역 조건(ln IDu·gm/ID가 정의되는 범위)과 방향 정합 확인이다.
>
> **예외**: 연결에서 나오는 KCL 항등 0 전류 MOS(표 9행 다리 규칙)는 선언도 문턱도 아닌 구조 사실이다.
>
> 평상시에 꺼져 있어야 하는 소자(trim 스위치 등)는 사용자가 `off`로 선언한다. 그 꺼짐의 결과는 `judged_by`·G2-a·oracle이 판정한다.

- 기존 결정과의 관계: O-205 (1)·O-203·O-207·O-202·O-212를 하나로 묶고 적용 범위에 '탐색 상자·경로 비용·LUT 파생'을 명시한다.
- 규칙 새로 0, 상수 0, 필드 0.

### 4.2 지울 것 (재작성 범위 -- 원칙 8 (2))

| 항목 | 자리 | card(권고) | LA-1 차단 |
|---|---|---|---|
| `_conduction_floor` + `ln_idu_floors`의 전도 갈래 | G1 | **LA-1 O-207 묶음**(N6.14, 완료 8에 `_conduction_floor` 0 추가). `_peak_floor`와 같은 파일이라 둘이 빠지면 `ln_idu_floors`·`sctx.cell_floors`·호출 3곳(slsqp_outer :68, layer0_center :285·:468·:566)이 빈 하한이 되어 같은 변경에서 지운다 | **차단**(S_d 정의 O-203) |
| `_peak_floor`, `CON_INVERSION`·`inversion_floor` | G2·G3 | LA-1 O-207 묶음(이미 배정) | 차단(이미) |
| `_conduction_ok`의 ε 항 | G4 | LA-1 O-207 묶음(card +0). GC-7 R3 몫에서 옮긴다 | **차단**(작성자 판단: 물리 경계를 tol_V가 정함, O-229 1. 영향 = VGS 엣지 비용 최솟값을 올리는 쪽 → 달성 가능성 헤드룸 하한이 보수 -- 미측정) |
| `_conduction_ok`의 `branch`(정점) | G5 | LA-1 O-207 묶음(배정 누락 보완) | 차단(O-207과 같은 성격) |
| `conduction_mask` 신설 계획 | G6 | graph-consumption 문언 철회(U-G4·GC-7 R3·GD-12) | 비차단(코드 없음) |
| oracle `off_current_A` 문턱 | G8 | OP-5(이미) | 비차단(이미 LA-1 전 배정) |
| `vov_spice`·`below_vth_spice` | G9 | LG-1(이미) | 비차단 |
| 커밋 B 문언의 전도 하한 항 | G10 | plan/o248 판정 중 정정(표 10행 (ii)·LM-1e 3b (ii)·완료 (1) toy·design 40 :1259·D42 :349) | **차단**(판정 중 브랜치의 문언 결함 -- 범위 위반 꼴) |
| 문언 잔재 | G11 | 해당 코드를 지우는 card | 비차단 |

### 4.3 바꿀 것

- `current_box` 근거(G7): '꺼진 소자와 구별 불가'를 'LUT 정의역(on_mask) 최소 ID'로 바꾸고, `lut_vgs_zero_missing` 요구를 지운다. 값은 그대로다(작성자 유도). LA-1 재점검 입력이고 비차단이다.
- (다) 유지 근거 문언(§3.2): 계획 정본 (1)·(6)의 근거를 '정의역·방향 정합'으로 적는다. 정의는 바뀌지 않는다. 다음 계획 판에 반영한다.
- 원리 문장(4.1): 승인되면 N3.6 정본 머리에 둔다(정의 자리 하나).

### 4.4 유지할 것

- (나) N1~N12 전부.
- (다) D1~D7 전부. 근거만 고친다.
- (라) R1~R9.

## 5. 원래 취지와 다름

1. **커밋 B(위임 A-144)**: 표 10행 (ii)·LM-1e 3b (ii)가 전도 하한에 집계 규칙을 적용하기로 한 취지를 철회하고 삭제로 바꾼다. 위임 결정을 고치는 것이다.
2. **graph-consumption O-15 (A)·U-G4**: `conduction_mask` 정본 신설을 철회한다. O-205가 '대상 소멸·축소'로 이미 적었지만 gc 문언은 남아 있다.
3. **GC-7 R3 몫 이동**: `_conduction_ok` ε 항·분지 삭제를 GC-7에서 LA-1 O-207 묶음으로 옮긴다. N3.6 정본 (7)의 'GC-7 -- 술어 = ID > 0'은 자리만 바뀐다.
4. **(다) 유지 근거 문언**: 오케스트레이터 정리('포화 판정만으로 ID ≈ 0을 못 잡음')를 '정의역·방향 정합'으로 바꾼다.
5. 원리 자체는 기존 결정 범위를 넘지 않는다. 다만 근본원칙으로 기록하는 것은 새 원칙이라 승인 대상이다(원칙 19).

## 6. 기존 결정과의 모순 후보 (작성자 자기 점검 -- 독립 점검 필요)

| # | 대조 결정 | 판정 | 내용 |
|---|---|---|---|
| C1 | O-205 (1)·O-203·U-69 철회·O-207 | 일치 | 원리가 이 결정들을 일반화한다 |
| C2 | O-182 Q-S9 (A′) KCL 항등 0 MOS 예외 | **조건부** | 원리 문장에 예외를 명시해야 모순이 없다(4.1에 넣음) |
| C3 | O-53 B1 (ii)·표 9행 (ii) `triode` 선언 ID ≤ 0 = 선언 오류 | **열린 점** | 원리 원문은 '선언 안 된 소자'만 말한다. 4.1은 triode 선언 소자도 선언 방향 전도로 묶었다. 물리: triode 스위치는 양방향으로 전류를 흘릴 수 있어 선언 방향 ID < 0이 기능상 정상인 회로가 있을 수 있다(작성자 의견, library triode 선언 0/13 -- CI-18, 발동 0) → 질문 Q3 |
| C4 | 위임 A-144(커밋 B) | **모순** | 전도 하한 항 → 정정(5-1) |
| C5 | gc O-13 (가)·O-15 (A)·GD-12 | **모순(낡음)** | `conduction_mask` 신설 → 철회(5-2) |
| C6 | O-202 (4)·O-221 `judged_by` | 일치 | 선언 기반 |
| C7 | O-212 VGS < 0 off 정지 | 일치 | 선언 + 정의역 |
| C8 | O-246 D3 VTH 삭제 | 일치 | G9 |
| C9 | O-229 4(새 인프라 금지) | 일치 | 새 함수·필드·측정 0, 삭제만 |
| C10 | design 40 :345·:1448, design 41 W7 | 일치 | 이미 삭제·폐기로 적힘 -- 커밋 B와 design 40 :1259만 어긋남 |
| C11 | O-210 RR-2(oracle ID ≤ 0 FAIL) | 일치 | 부호 판정 유지, 근거만 고침 |

## 7. 사용자 질문 초안 (원칙 26 5묶음은 아래 §8)

- **Q1 off 원리**(머리 'off 원리'): 4.1 문장을 근본원칙으로 채택할까?
  - (가) 4.1 그대로(판정·탐색 상자·경로 비용·LUT 파생 모두, KCL 항등 0 예외 명시) **(Recommended)**
  - (나) 판정 자리만, 탐색 상자·비용은 제외 ⚠ O-203 S_d 정의와 충돌(상자가 S_d 밖을 자름)
  - (다) 보류 ⚠ 커밋 B가 삭제 대상을 고쳐 쓰는 작업이 그대로 진행됨
- **Q2 하한 처리**(머리 '하한 처리'): 탐색 전도 하한 `_conduction_floor`와 엣지 비용 ε·분지 항을 어디서 지울까?
  - (가) LM-1e 3b (ii)에서 빼고 LA-1 O-207 묶음에서 삭제(card +0, `ln_idu_floors`·`sctx.cell_floors` 같이) **(Recommended)**
  - (나) LM-1e에서 바로 삭제 ⚠ LUT card에 탐색 동작 변경이 섞임(범위 위반 꼴)
  - (다) GC-7 유지 ⚠ GC-7은 LA-1 뒤일 수 있어 LA-1 S_d가 정의와 다르게 병합됨(O-229 1)
- **Q3 triode 방향**(머리 'triode 방향'): `triode` 선언 소자에도 선언 방향 ID > 0을 요구할까?
  - (가) 지금대로 요구(O-53 B1 (ii)), LA-1 재점검에서 양방향 스위치 사례를 잰다 **(Recommended -- 발동 0/13이라 지금 바꿀 근거 부족)**
  - (나) triode는 부호 무관 ⚠ 역방향·0 전류 triode를 선언 오류로 못 잡음(fail-open 쪽)
- 위임(O-229 7)으로 Q2·Q3은 오케스트레이터가 권고대로 채택할 수 있다. Q1은 근본원칙이라 원칙 19에 따라 사용자 승인 대상이다.

## 8. 보고 5묶음 (원칙 26)

### 8.1 bkit 단계표

| 계획 | design | 검증 | 승인 | test | code | 구현 gap | 감사 |
|---|---|---|---|---|---|---|---|
| 해당 없음(원리 후보 -- 계획 개정 전) | 해당 없음 | 안 함(이 문서가 작성자 감사, 독립 검증 대기) | 안 함 | 해당 없음(코드 변경 0) | 해당 없음 | 해당 없음 | 이 문서(작성자 자기 감사) |

### 8.2 단계별 점검표 (권고안 기준)

| 항목 | 결과 |
|---|---|
| graph 단일 정본 | 실측(경로): G6 `conduction_mask` = `on_mask` 중복 정의 → 철회 권고(`E/lut/lut_set.py:197`) |
| G-10 블록 재계산 / 블록 안 재계산 | 해당 없음(코드 변경 0) |
| 새 필드 소비자 | 해당 없음(새 필드 0, 삭제만) |
| 구조·파일 분할 | 해당 없음 |
| 회로 이름 0 | 실측: 원리·권고에 회로 이름 0 |
| fail-closed | 실측: §2 과도기·§3.2 -- 삭제는 상자를 넓히는 쪽(판정 불변), oracle 부호 판정 유지 |
| 상수 발명 0 | 실측: 상수 0(문턱을 지우기만 함) |
| DC·AC 분리 | 해당 없음(DC 영역 정의만) |
| 계획 먼저 | 권고 = 계획(plan/o248)·graph-consumption 문언부터 고치고 card로 |
| 작성자 ≠ 검증자 | 이 문서는 작성자 감사. 독립 점검은 따로(§6) |
| 일반성 n/N | 해당 없음(off·triode 선언 0/13 -- agent 인용 CI-18) |
| 만들면 배선 | G6 신설 철회 = 안 만듦. 삭제 대상의 호출부 4곳(§4.2) |

### 8.3 원래 취지와 다름

§5 1~5.

### 8.4 권고 실측 출처

- **직접 잼**:
  - LUT 부호·VDSAT·포화 통과 ID 분포(`C:/Users/HSLEE/AppData/Local/Temp/la1s_off40/sat_vs_sign.out.txt`)
  - 코드 자리 읽기: `E/search/cell_floor.py`, `E/lut/derived_fns.py:1-90`, `E/search/current_box.py`, `E/sizing/region_judge.py`, `seal_region.py`, `block_currents.py`, `current_basis.py:1-40`, `search/cone_rows.py`, `O/core/compare.py:205-272`
  - 계획 P:648-695·P:2640-2656·P:2114·P:1271·P:288
  - design 40 :345·:1141·:1259·:1448, design 41 :516·:669, D42 :349
  - gc :209·:643·:758
  - `user_decisions.md`:1183-1193, `la1_auto_decisions.md`:150
  - master `git grep` 4이름
- **agent 인용**: BSIM VDSAT 약반전 바닥(`o245_terminal_dc_columns.md` §2.2), library off·triode 선언 0/13(CI-18, 계획 문언), 실 LUT VDS = 0 셀 None 8/8(`lm1d_run_verdict.md` -- 계획 P:2651 인용).

### 8.5 권고 확인표 10항목 (Q1·Q2·Q3 공통)

| # | 항목 | 결과 |
|---|---|---|
| ① | 지적 사실 직접 재확인 | 실측(경로): cell_floor.py :15-22·:53-85, derived_fns.py :8-10·:39-50, P:2114 완료 8에 `_conduction_floor` 없음, design 40 :345 |
| ② | 계획 전체 grep | 실측: `전도 하한\|_conduction_floor\|cell_floor\|conduction` P 전체, gc·oracle·headroom·offset-trim 계획 grep |
| ③ | 원칙 전수 | 실측: 원칙 1·6·7·8·9·10·11·19·21 대조(§4·§6) |
| ④ | 대안 비교 + ⚠ | 실측: §7 각 질문 |
| ⑤ | 실현 가능성 | 실측: 호출부 4곳·소비자 목록(§4.2). 삭제 영향 수치는 미측정(O-229 4) |
| ⑥ | 열린 결정·design 영향 | 실측: LM-1e(판정 중 커밋 B)·LA-1 O-207 묶음·GC-7·OP-5·LG-1 |
| ⑦ | 원래 취지 | §5 |
| ⑧ | 원문 쪽 + 로컬 PDF | 해당 없음(회로 원문 무관. 약반전 식은 `o245` §2.2 인용) |
| ⑨ | 물리·회로이론 | 실측: §3.2(결정자 = 약반전 VDSAT 바닥·채널 전류 부호 = VDS 부호). 판정 = 조건부 맞음, ngspice 역방향 부호 관례는 불확실 |
| ⑩ | 결정 간 모순 점검 | **작성자 자기 점검만**(§6, 이 파일). 원칙 26에 따라 점검자 ≠ 작성자 기록이 따로 필요하다 -- 질문 전에 독립 점검 필수 |

## 돌린 범위

- 읽기·grep: 계획 4개(gain-budget plan/o248, graph-consumption, oracle-portability, headroom-chain, offset-trim), design 40·41·42, 결정 두 파일, 엔진·oracle 코드(WB-1 worktree), master `git grep` 1회.
- 스크립트 1개(읽기 전용 LUT npz, 결과 파일 append).
- pytest·ngspice 0, 커밋 0, 파일 수정은 이 문서 하나.
