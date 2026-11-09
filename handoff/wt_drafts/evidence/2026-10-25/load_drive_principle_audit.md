# 부하 구동 원칙 초안(L0~L4) 전수 감사 -- 계획·design·엔진 규칙 대조, 초안 물리 검토, library 영향

- 작성: 감사 agent, 2026-10-25. 계획·design·엔진·spec은 고치지 않았다. 이 파일과 임시 파일(`wt/_scratch_loaddrive/`)만 썼다.
- 사용자 원문(2026-10-25): "부하전류원, 저항부하, 캡 부하. 이 3가지는 토파로지의 전류를 결정하는 중요요소야. 난 사이징을 위한 일관된 개념이 필요하다고 봐. dc부하와 ac부하의 개념을 생각해보면 토팔로지의 사이징이 이 두가지 개념의 부하를 드라이빙하기에 충분한 전류를 공급할 수 있어야 해. 이 부분의 개념을 다듬고 일관적인 원칙을 만들어서 사이징을 위한 gmid방법론의 구현계획을 다듬고 싶어."
- 대조 자료(읽기만)
  - 계획 master v6.37: `chip-design-skills/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(줄 번호는 이 파일 기준). v6.38 미승인안(`wt/plan-v638` `182124fa`)은 DEC 행 줄 번호가 같고, N3.7 출력 구동 규칙은 597행이다(+2).
  - design v1.14.2 미승인(`wt/design-v1142` `ca58c8a1`): 40-engine, 41-gain-budget.
  - 엔진 integ/it12 `34585913`(`wt/integ-it12/skills/analog-gmid-design/gmid_engine`, 아래 `E/`).
  - 사용자 결정 `wt/_drafts/user_decisions.md`: O-26(645행), O-29~O-32(648~652행), O-43(663행), O-115(800행), O-119~O-126(826~879행).
  - 앞선 근거: `evidence/2026-10-24/min_current_from_load.md`(§8 포함), `b80_pushpull_front_zero.md`, `classb_gmid_op_point.md`, `evidence/2026-10-23/slew_estimate_vs_bound.md`.
- 원자료(`wt/_scratch_loaddrive/`)
  - `scripts/survey.py` → `out/survey.txt`: library 9회로 topology `passive_elements`·`ideal_sources`·포트, spec `element_values`·제약·보상 목표 전수.
  - `scripts/handcalc.py` → `out/handcalc.txt`: L1·L2(a) 손계산.
  - `scripts/outstage_recheck.py`(앞선 `_scratch_mincur/scripts/outstage.py`의 출력 경로만 바꾼 사본, `_scratch_b80/scripts/probe.py`를 import) → `out/outstage_recheck.jsonl`: 층 0 시작점 출력단 전류 재측정. 실행 전후 `git -C wt/integ-it12 status --short` 둘 다 빈 출력(`out/git_status_before.txt`·`after.txt`).
- heldout은 근거로 쓰지 않았다(소비자 grep 적중 수만 사실로 적었다). SPICE는 새로 돌리지 않았다.

## 0. 결론

1. **초안의 큰 줄기는 맞다.** 부하가 바이어스 전류를 요구하는 길은 셋이다. DC 부하(L1)는 DC 양이고, 소신호(L2(a))는 이미 계획의 보상·매크로·θ 제약 경로다. 대신호(L2(b))는 속도 선언이 있을 때만 정의된다. 교과서 근거도 같다(Allen L040 p.040-3: "|I_OUT| > C_L·SR, |I_OUT| > v_OUT(peak)/R_L. The maximum current will be determined by **both** …").
2. **고쳐야 할 물리 결함이 넷 있다.**
   - (F1) L3은 공급 능력을 O-26 (1) 정의로 잰다. 그런데 그 정의는 노드를 **동작점 전압**에 고정한다. 요구(L1)는 **범위 끝 전압**에서 최대다. 같은 전압에서 비교해야 한다. β 전류원은 범위 끝에서 VDS가 줄어 전류가 준다(CLM). 포화를 벗어나기도 한다.
   - (F2) class-A의 신호(σ) 방향에서 부하가 받는 전류는 σ 소자 최대 전류에서 반대쪽 β 전류를 뺀 값이다(Allen L040 p.040-3 "Maximum sinking current = K'W/2L(…)² − I_Q"). as-built `ls_fields`는 공급 셀 전류의 합만 센다(`E/metrics/ls_fields.py:73-77`). 순 전류가 아니다.
   - (F3) L3이 class-A/class-AB로 값 규칙을 가른다. DEC-65는 그 구조 분류를 "값 판정에 쓰지 않는다"고 적었다(264행). 'class-A β 최대 = 정지전류'는 레일에 source가 붙은 β만 맞다. 내부 단자 β(폴딩 캐스코드 M6처럼 source가 신호 따라 전류가 바뀌는 노드)는 정지전류보다 큰 전류를 낼 수 있다(O-122 근거 '내부 단자 β 1.19×').
   - (F4) L0의 세 형식(I_L, R_L→V_ref, C_L)은 기준 전압이 고정된 단자형만 담는다. 차동 출력 사이 저항, 되먹임 망(Cf·Cs), 기준이 움직이는 부하는 담지 못한다. 가장 일반적인 형태는 "출력 포트를 전압 V에 고정했을 때 응용 망(DEC-100)이 그 포트에서 끌어가는 DC 전류"다. 세 형식은 그 특수형이다.
3. **L2(b)는 O-122와 같은 것이다.** '속도 선언 → 엔진이 바이어스 하한을 유도해 θ 제약·층 0 역산에 넣음'은 O-121 B-1 (나′)(출력 노드 전류 하한 = 탐색 경계)와 같은 장치다. O-122는 그것을 "엔진 관여 없음"으로 바꿨다. 넣으려면 O-122를 다시 결정해야 하고, 원래 취지와 다르다. 엔진에 넣지 않는 길은 둘이다. 사용자가 손계산한 피크 전류를 선언하거나(`load_peak_amp`), oracle `.tran` 판정만 두는 것이다.
4. **L3은 U-115에 의존한다.** β 방향은 U-115와 무관하다(θ 전류). σ 방향(class-A 신호 쪽, push-pull 두 방향)은 U-115 규칙이 없으면 값이 없다. 게다가 (F1)·(F2) 때문에 U-115 후보 셋 모두 '동작점 전압 고정·공급 셀 합'이라 L3에 그대로 쓸 수 없다. U-115 질문 자체를 '범위 끝 전압에서의 순 전류'로 넓혀야 한다.
5. **DEC-103 판정**
   - L1 요구는 spec(부하 원소 값 + 선언 범위)에서만 나온다. 회로와 무관하다. 단, 범위의 **위치**가 선언되지 않으면 그렇지 않다. `swing_out_v`는 폭만 선언한다. 위치를 동작점 중심으로 두면 요구가 회로(DC 동작점)에 기대게 된다.
   - 공급 능력은 두 틀로 갈린다. 사이징에서 '얼마의 전류를 둘까'는 설계점 질문이라 θ 고정 손계산('추정' 하한)이다. '이 회로가 범위 끝에서 그 전류를 내는가'는 정해진 회로를 흔드는 질문이라 W·바이어스 고정 KCL(DE-1 선형 감도 끝)과 oracle `.dc`다. 초안 L4가 이 둘을 '손계산 하한 / oracle 판정'으로 나눈 것은 맞다. 다만 KCL 틀의 엔진 자리(DE-1)를 적지 않았다.
6. **선언 형식**: `load_dc_amp`는 netlist 전류원 원소와 같은 양이다. 지우는 것을 권고한다. `load_peak_amp`는 엔진이 L1에서 유도할 수 있는 몫과 사용자만 낼 수 있는 대신호 몫이 섞인 양이다. 남긴다면 '사용자가 손계산한 대신호 몫'으로 뜻을 좁혀야 한다. `slew_rate_v_per_s`와 `compensation_targets.settling`은 속도 선언이다. `constraints[]`의 `.tran` metric(oracle에 이미 `slew_rate_v_per_s`·`settle_s` 측정 이름이 있다)으로 한곳에 모으는 안을 권고한다. 그러면 `driving_spec`은 없어진다.
7. **library 영향**: L1이 0이 아닌 회로는 nmcnr 하나다(R_L 25 kΩ, 10 µA, 위치는 추정). L2(a)는 GBW·PM이 선언된 5회로에서 정의된다(출력 극점 하한 gm_out ≥ 0.36~1.41 mS). L2(b)가 정의되는 회로는 0이다. 층 0 출발 전류를 L1이 묶는 회로는 0이다(nmcnr 층 0 M302 1.154 mA, 이번 재측정 -- 요구의 115배). B80 front 0의 원인과 해법(LA-1 rout·gain 국소 제약)은 바뀌지 않는다.
8. **계획 개정은 원칙 하나(DEC 신설) + 정의 하나(O-26 (1) 확장) + 선언 정리(N3.15·N3.16) + 기존 행 셋(DEC-58·DEC-71 (3)·DEC-100) 정정**으로 묶인다. 사용자 결정이 필요한 항목은 일곱이다(§7.2).

## 1. 규칙별 판정표

판정: 맞음 = 초안과 같은 뜻 / 어긋남 = 초안과 반대이거나 다른 정의 / 빠짐 = 초안이 요구하는데 계획에 자리가 없음 / 범위 밖 = 부하 구동과 무관.

| # | 규칙(자리) | 원문 인용(요지, 줄) | L0 | L1 | L2(a) | L2(b) | L3 | L4 | 비고 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | DEC-58 (계획 255행) | "`driving_spec`(슬루율·부하 전류, 부하 용량은 부하 요소 참조 -- N3.15)에서 슬루율은 oracle `.tran`만 판정·탐색하고 엔진 슬루 제약은 없으며(v6.37 O-122 …), 부하 전류가 선언되면 출력 포트 노드의 방향별 최대 출력 전류 ≥ 부하 전류다(N3.7 출력 구동 규칙)" | **어긋남**: 부하 전류의 선언 자리가 `driving_spec`(netlist 밖) | 빠짐: R_L 범위 끝 요구 없음 | 범위 밖 | 맞음(엔진 관여 없음) -- 초안 L2(b)의 엔진 하한과는 **어긋남** | **어긋남**: 비교 대상 = 동작점 전압의 방향 최대 전류(F1), 부하 전류 방향 없음 | 맞음 | 계획은 '출력 구동 규칙'을 N3.7(595행)로 인용한다. 과제의 'N3.8'은 N3.7이다 |
| 2 | DEC-65 (264행) | "노드 k·방향(충전/방전)별 최대 전류 = **노드 k를 동작점 전압에 고정하고** 입력 …을 허용 입력 범위(레일 범위) 끝까지 몬 DC 해에서 k로 드는 그 방향 전류다 … 구조 분류 … 값 판정에 쓰지 않는다" | -- | -- | -- | -- | **어긋남**: (F1) 전압 = 동작점, (F2) 순/총 전류 불명, (F3) 초안은 분류로 값 규칙을 가름 | 맞음(정확값 oracle `.dc`) | "엔진 계산 -- 규칙 미결(U-115)" |
| 3 | DEC-66 (265행) | "`rout_ss_ohm(port)` = 전체회로 MNA에서 … 출력 포트에 단위 전류를 주입해 얻은 저주파 개루프 전압 … 엔진은 임계값을 만들지 않고 spec에 선언된 `rout_ss_ohm` 제약만 판정" | 범위 밖(DUT 속성) | -- | 맞음(L3 class-AB 정지전류 근거로 인용) | -- | 맞음 | -- | 부하 R_L과 DUT rout을 섞지 않는다 |
| 4 | DEC-67 (266행) | "DC 양(동작점·동작 범위)은 DC 풀이로, AC 양은 봉인 DC 점에서의 MNA 소신호로 … 대신호(슬루율(정의 `.tran` …) -- 판정·탐색 모두 oracle만, 엔진 칸 0 -- O-121 B-2·O-122))" / "영역 판정 기준 … `.op`·`.dc` 훑기 → DC(… 방향별 최대 전류), `.ac`·`.noise` → 소신호 `ss`, `.tran` → 대신호 `ls`" | -- | 맞음(DC) | 맞음(ss) | 정의는 맞음(ls). **'L2(b) → DC 바이어스 하한'은 대신호 → DC 되먹임**이라 DEC-70 θ 제약으로만 허용되는데 DEC-70이 슬루를 뺐다 → 어긋남 | 맞음(DC) | 맞음 | -- |
| 5 | DEC-70 (269행) | "AC·대신호 결과는 … 결정변수 θ … 의 **제약**으로만 되돌아간다: 보상 `gm_i(θ) ≥ gm_req(C(θ))`, 기생 극점 … (슬루율은 θ 제약이 아니다 -- v6.37 O-122, oracle `.tran`만 …)" | -- | -- | **맞음**(gm_req(C)) | **어긋남**(초안 L4 'θ 제약에 들어간다') | -- | 맞음 | L1은 DC 제약이라 DEC-70 대상이 아님 |
| 6 | DEC-71 (3) (270행) | "입력 = 그 블록의 gain 예산 …, 기둥별 레일 전압차, 블록 전류(KCL·선언 -- '슬루 하한'은 v6.37 O-122로 없음), 소자 간 등식" / "그런 블록에는 선언된 출력 저항 상한(`rout_ss_ohm`)을 블록 국소 모델의 테브난 출력 저항에 건 것을 국소 AC 제약으로 대신 쓴다" | -- | 맞음(자리 = '선언') -- 다만 **규칙 빠짐**(무엇을 어떻게 거는지 없음) | 맞음(국소 AC = gain·rout) | **어긋남**('슬루 하한' 삭제) | 빠짐(국소 문제에 공급 능력 제약 없음) | 맞음 | design 41 892행도 같은 문구 |
| 7 | DEC-71 (4) (270행) | "(a) 필요 gm에서 `gm_id = gm / ID` 역산 (b) 목표 이득에서 필요한 gm/gds …" | -- | **빠짐**(전류 하한에서 역산하는 갈래 없음) | 맞음(필요 gm) | 어긋남 | 빠짐 | 맞음 | design 41 924행 S 소자: 필요 gm은 매크로·rout에서만 정의 |
| 8 | DEC-100 (299행) | "(2) 모든 해석 … = DUT ⊕ 측정 구성별 응용 망 (3) 해석에서 외부 소자를 빼지 않는다 (4) … `measurement_load: true` 한 자리 … 커패시터·저항만 받음 … (7) 이상 전류원(`implementable: false`)은 `measurement_load` 표지를 받지 못한다" | 맞음(해석은 부하를 그대로 씀) / **빠짐**: I_L 원소를 응용 망으로 표지할 길이 없음((7)) / **어긋남(뜻)**: 초안은 표지를 '면적·layout만'이라 하지만 부하 판별에도 이 표지가 필요 | -- | -- | -- | -- | -- | 2단계 = card AP-1 |
| 9 | DEC-103 (302행) | "어떤 W·전류로 설계할지 정하는 일 … 은 θ 고정 …, 이미 정해진 회로를 흔들 때의 반응 … 은 W·바이어스 전압을 고정한 KCL 선형화" | -- | 맞음(요구는 spec 양) | 맞음 | -- | **빠짐**: 공급 능력의 두 틀(설계점 θ / 판정 KCL·oracle) 미기재 | 맞음 | §3.6 |
| 10 | N3.7 출력 구동 규칙 (595행) | "`driving_spec`에 부하 피크 전류(`load_peak_amp`)가 선언되면 출력 포트 노드의 방향별 최대 출력 전류 ≥ 그 값이고, DC 부하 전류(`load_dc_amp`)가 선언되면 출력 포트 KCL에 넣는다 … 슬루율이 선언되지 않으면 KCL 전류만 쓴다" | **어긋남**: `load_dc_amp` = netlist 전류원과 같은 양(이중 생산자, graph 규칙 1) | 빠짐(범위 끝) | -- | 맞음(oracle) | 어긋남(F1·방향) | 맞음 | as-built `load_dc_amp` 소비자 0(min_current_from_load G1) |
| 11 | N3.7 단일단 (593행) | "기본안 gm_1 요구량 `gm_1 ≥ 2π·gbw_target_hz·C_out,total`은 손계산(출발값) 표기 … C_out,total = 봉인점 출력노드 용량 + 부하 요소 값" | -- | -- | **맞음**(초안 L2(a)의 식 그대로) | -- | -- | 맞음(판정 = DEC-92 MNA) | 다단은 출력 비주극점 하한(design 41 §6.3)이 대응 |
| 12 | N3.8 metric 표 (625·626행) | 방향별 최대 전류 = DC `.dc` "노드를 동작점 전압에 고정"; 슬루율·정착 = `ls` `.tran` "엔진 값 없음 -- 판정·탐색 = oracle만" | -- | -- | -- | 맞음(oracle) | 어긋남(F1) | 맞음 | `settle_s`가 metric 이름으로 있다 |
| 13 | N3.8 스윙·입력 범위 (609행) | `swing_out_v` = 출력 범위(DC), 폭 선언 | -- | **빠짐**: 범위 **위치** 규칙 없음 | -- | -- | -- | -- | min_current_from_load §6-3 |
| 14 | N3.15 (894행) | "`element_values{<요소 이름>: {value_ohm \| value_farad \| value_dc_amp}}` … `driving_spec`(슬루율, `load_peak_amp`, `load_dc_amp`)" | **어긋남**: 부하 선언 자리 둘(element_values + driving_spec) | -- | -- | 속도 선언 자리 셋(driving_spec SR, compensation_targets.settling, f·Vp 없음) | -- | -- | -- |
| 15 | N3.16 명명표 (913·914·939행) | "부하 용량 = 부하 요소(예 `CL`)의 `value_farad`" / "측정 부하 = `element_values.<el>.measurement_load: true`" | **맞음** | -- | 맞음 | -- | -- | -- | -- |
| 16 | DEC-08 (208행) | "`value_dc_amp` … 가 null이면 자유 탐색, 값이 있으면 그 값을 실제 전류로 고정" | **빠짐**: 부하 I_L은 값이 반드시 선언돼야 한다(자유 θ면 부하가 아니라 설계 변수) | -- | -- | -- | -- | -- | -- |
| 17 | J12-f (2124행) | "합류 노드 KCL `I_M1 = I_M2`(출력 DC 부하 전류 없음 전제)" | -- | **충돌 가능**: I_L·R_L(V_out ≠ V_ref)이면 전제가 깨짐 | -- | -- | -- | -- | pushpull·sf_pushpull 해석 전제 |
| 18 | GBW 매크로 (design 41 §6.5 1601행~, `E/search/macro_poles.py:21·107·126-161·291`) | "노드 용량: 부하 + 소자 cgg 추정 + 보상 수동소자" / "GBW 목표 없음: 매크로 모델을 돌리지 않는다(`macro_inactive`)" / `c_ref = max(고정 커패시터)` | -- | -- | **맞음**(부하 C·값 선언 R 모두 스탬프 -- `_passives`가 resistor도 받음) | -- | -- | -- | `c_ref`는 출력 부하가 아니라 고정 C 최댓값(출발값 전용) |
| 19 | 출발 구간 (design 41 §6.3·§6.5, `start_intervals`) | §6.3 "비주극점 조건: f_np ≥ GBW / tan(90° − PM)" / §6.5 "전류: I = gm / (gm/ID) … 남는 θ 전류는 상자 기하 중심" | -- | **빠짐**(DC 부하 전류 하한 없음) | 맞음 | -- | -- | -- | as-built는 LUT 포락선 상자 중점(§6.6 '상태: MISS') |
| 20 | U-115 (2263행) | "방향별 최대 전류(피크 부하 전류 행 소비자, DEC-58)의 엔진 손계산 규칙 … 미결 -- 사용자 결정 대상, 후보 (가)(나)(다)" | -- | -- | -- | -- | **의존**(σ 방향) | -- | §3.5 |
| 21 | O-122 (user_decisions 849행) | "슬루 판정과 탐색 모두 oracle `.tran` … 엔진은 슬루에 관여하지 않는다 … 원래 취지와 다름: O-121 B-1의 '엔진 = 출력 노드 전류 경계'를 '엔진 관여 없음'으로" | -- | -- | -- | **충돌**(§3.3) | -- | 맞음 | -- |
| 22 | `measurement_load` (`E/authoring/spec_elements.py:9·37·66-71`) | "`measurement_load: true`(값 또는 engine 항목, 커패시터·저항 요소만) = 설계가 아닌 측정 부하 -- 면적 `area_search_m2` 에서 뺀다" | 맞음(C·R) / 빠짐(I_L) | -- | -- | -- | -- | -- | 소비자 = 면적·layout뿐(DEC-100 (4)) |
| 23 | `current_source`/`value_dc_amp` (`spec_elements.py:41`, design 41 578행 `I_k,cert`) | "선언된 이상 전류원(`value_dc_amp`)과 KCL로 값이 고정된 가지 전류" | **빠짐**: 바이어스 전류원과 부하 전류원을 가르는 자리 없음 | -- | -- | -- | -- | -- | library 이상 전류원 3개는 모두 바이어스(Iref·Ibg·IBias, 출력 포트에 안 닿음 -- survey) |
| 24 | design 40 §3.8-3 (963·1248·1251행) | `driving_spec` 모양 `{slew_rate_v_per_s?, load_peak_amp?, load_dc_amp?, source}` / 피크 행 c = (출력 포트 노드 방향 전류 최솟값 − 피크) ÷ 분해능 / "(다) `load_dc_amp` … 출력 포트 넷 KCL에 이상 전류원 항으로 더한다 … 상태 MISS" | 어긋남(10과 같음) | -- | -- | 맞음(`oracle_judged`) | **어긋남**: 두 방향 최솟값 − 스칼라 피크(`E/metrics/ls_fields.py:99-102`) = 방향 없는 부하 | -- | -- |
| 25 | card DE-1 (d) (1635행) | "방향별 최대 전류(피크 부하)·엔진 슬루 몫 삭제 … 엔진 계산 = 규칙 미결 U-115" | -- | -- | -- | 맞음 | 의존(F1·F2를 같이 고칠 자리) | 맞음 | 선형 감도 끝(DE-1 (a)(b))이 KCL 틀 자리 |
| 26 | card VB-1 (1925행) | 슬루율 oracle 판정 대응(`verified_by`) | -- | -- | -- | 맞음(oracle 판정) | -- | 맞음 | `oracle_compare.py:85` `TRANSIENT_MEASURES = ("slew_rate_v_per_s", "settle_s")` |
| 27 | `compensation_targets.settling` (`E/authoring/spec_targets.py:12-13`) | "과도 metric 이 레지스트리에 없어 보상 목표로만 쓰이고 합격 판정 대상이 아니다" | -- | -- | -- | 속도 선언인데 소비자 0(G2) -- **빠짐**(정의·판정 자리) | -- | -- | current_reuse 40/30 ns |
| 28 | O-43 D1 (b) (user_decisions 663행) | "(b) 슬루 방향 전류 = dc_current_basis 전류 기저로 그 노드로 몰 수 있는 θ 전류 합, '추정'" | -- | -- | -- | -- | 후보(U-115 (나)) -- 동작점 전압·총 전류라 (F1·F2) 그대로 남음 | -- | -- |

## 2. 초안 물리 검토

### 2.1 L1 -- DC 부하 요구

- 식 I_DC,req(V) = I_L + (V − V_ref)/R_L는 R_L·I_L이 선형이고 기준이 고정일 때 맞다. 커패시터는 DC에서 열려 있으므로 C_L은 L1에 들어가지 않는다(맞음).
- **결함 L1-a (위치)**: 범위 [V_lo, V_hi]의 위치가 선언되지 않는다. `swing_out_v`는 폭만 있다(N3.8 609행). nmcnr에서 위치가 결과를 바꾼다(`out/handcalc.txt`).
  - V_ref(agnd 0.9 V) 중심: [0.65, 1.15] V → 공급 10 µA(V_hi)·흡수 10 µA(V_lo).
  - 앞선 층 0 동작점(1.658 V) 중심: [1.408, 1.908] V → 위 끝이 vdd 1.8 V를 넘어 범위 자체가 성립하지 않는다.
  - 그래서 '동작점 중심'은 물리적으로 쓸 수 없는 경우가 있다. 위치는 spec 선언이 필요하다(§7.2 D2).
- **결함 L1-b (방향별 최대만 취함)**: L1은 방향마다 최대만 남긴다. 그러나 공급 능력도 V의 함수다(§2.4 F1). 비교는 같은 V에서 해야 한다. R·I 부하는 V에 대해 1차라서 요구의 극값은 범위 끝에 있다. 그러므로 '범위 두 끝에서 방향별 요구 ≤ 그 끝의 공급 능력'으로 쓰면 충분하다(능력이 범위 안에서 단조라는 전제 -- 포화를 벗어나는 지점이 끝 안쪽이면 그 지점이 끝이다).
- **결함 L1-c (일반형)**: 초안은 세 단자형만 담는다. 가장 일반적인 정의는 다음이다.
  - I_DC,req,p(V) = 응용 망(DEC-100 (2), DUT 밖 원소 전부)을 DC로 풀 때, 출력 포트 p를 V에 고정하면 그 포트에서 응용 망으로 흘러나가는 전류.
  - 이 정의는 차동 출력 사이 저항(기준 = 반대 출력, 움직임), 되먹임 저항(기준 = 입력 노드), 여러 출력 포트(포트 전압 벡터), 비선형 부하를 모두 담는다. 세 단자형은 응용 망이 원소 하나일 때의 특수형이다.
  - 계산은 응용 망만의 선형 DC 풀이라 손계산 수준이다(DUT 무관, 같은 MNA 스탬프).
- **결함 L1-d (동작점에서는 이미 KCL이 센다)**: 부하가 netlist 원소면 동작점 DC 전류는 엔진 DC 풀이가 이미 센다(nmcnr 실측: I(M302) − I(M301) ≈ 30 µA = (1.658 − 0.9)/25 kΩ, min_current_from_load §3.2). L1이 새로 더하는 것은 **범위 끝**의 요구다. 같은 양을 `load_dc_amp`로 다시 선언하면 이중 계수다(graph 규칙 1).
- **DUT 내부 부하**: current_reuse의 R1·R2(출력 사이 CM 검출 저항, θ 값), nmcnr의 Rm(보상)은 출력 포트에 닿지만 DUT 원소다. DC 전류는 KCL이 센다. L0 정의(응용 망 원소)에 넣지 않는 것이 맞다. 다만 공급 능력 판정(L3)은 '응용 망 요구 + DUT 내부 가지 전류'를 모두 감당해야 하므로, 판정은 DUT ⊕ 응용 망 전체 DC 해(DE-1·oracle `.dc`)에서 한다.

### 2.2 L2(a) -- 소신호 AC 부하

- 단일단 gm ≥ 2π·GBW·C_out은 맞다(계획 593행). 다단은 출력 노드가 비주극점이 되어 gm_out ≥ 2π·f_np·C_out, f_np ≥ GBW/tan(90° − PM)(2극점 근사, design 41 §6.3)가 출력단 하한이다. 초안이 '같은 조건'이라 묶은 것은 다단에 그대로 맞지 않는다.
- **빠진 항 (R_L이 DC 이득을 깎음)**: Allen L040 p.040-4 "v_out/v_in = −g_m1/(g_ds1 + g_ds2 + G_L)". R_L이 지배하면 그 단의 이득 요구가 gm ≥ A_단·(G_L + gds)를 만든다. 계획은 이것을 블록 국소 모델(N3.8)과 GB4로 판정한다(국소 모델이 값 선언 저항을 고정 컨덕턴스로 받음 -- `E/metrics/block_gain_model.py:17`). 그래서 새 규칙은 필요 없다. L2(a)를 'C_L·R_L이 들어간 MNA로 판정하는 모든 ss 제약(GBW·PM·이득·rout)'으로 넓혀 적으면 된다.
- L2(a)는 새 계산이 아니라 이미 있는 경로(DEC-02 보상 먼저, DEC-70 gm_req(C), DEC-92 GBW MNA 판정, 매크로 §6.5)의 이름이다. 초안이 '지금 매크로가 이 길'이라 적은 것은 맞다.

### 2.3 L2(b) -- 대신호 AC 부하

- 물리: dV/dt = I/C이므로 SR ≥ X ⇒ 출력 노드 전류 ≥ X·C_tot ≥ X·C_L. 필요조건이다. 속도 선언이 없으면 하한이 없다(어떤 I > 0도 시간이 지나면 끝 상태에 닿는다). 맞다.
- full-power f·Vp → SR_req = 2πf·Vp(ADI MT-045), 정착 t_s·ΔV → 평균 기울기 ΔV/t_s(하한). 맞다.
- C_tot에는 C_L 말고도 노드 기생과 그 노드에 걸린 보상·되먹임 C가 든다(Allen ECE6412 L140 p.140-6, O-120). C_L만 쓰면 필요조건으로는 안전하다(C_L ≤ C_tot).
- 교과서 사이에 차이가 있다. Allen L040 p.040-3은 "both"라 적고 Example 5.5-1은 큰 값 하나(C·SR)만 골랐다. Allen L26 Example 26-2(R_L = 500 Ω, C_L = 100 pF, SR = 10 V/µs)도 "SR = 10V/µs and 100pF capacitor give I15 = 1mA"로 C·SR만 썼다. 1 V 진폭이면 R 항(2 mA)이 더 크다(`out/handcalc.txt`). 초안의 '계단은 합'이 물리적으로 정확하다(min_current_from_load §1.3).

### 2.4 L3 -- 공급 능력

- **F1 (전압 불일치)**: O-26 (1)·DEC-65 정의는 노드를 동작점 전압에 고정한다. 요구는 범위 끝에서 최대다. 레일에 source가 붙은 β 전류원이 끌어올리는 방향이면 위 끝에서 VDS가 가장 작아 전류가 가장 작다(CLM). 포화를 벗어나면 급감한다. 동작점 값과 끝 값의 차이는 회로마다 다르다(O-121 실측 꼬리 CLM 1.6~4.7×는 반대 방향 예). 그래서 비교 전압을 끝으로 옮겨야 한다. 정의 확장이다(§7.2 D6).
- **F2 (순 전류)**: 부하가 받는 전류는 노드 KCL의 순 전류다. class-A의 σ 방향 = I_σ,max(V) − I_β(V)(Allen L040 p.040-3 "−I_Q"). push-pull은 반대쪽 σ가 끊기는 정도에 따라 다르다. as-built는 공급 셀 합(`ls_fields.py:73-77`)이라 σ 방향을 I_β만큼 과대평가한다. DEC-65 문언 "k로 드는 그 방향 전류"를 '노드를 V에 고정하는 원천이 내보내는 순 전류'로 못박아야 한다(oracle `.dc`에서 고정 원천의 전류 = 순 전류라 oracle 정의와 같아진다).
- **F3 (분류로 값 규칙)**: 초안은 class-A면 '최대 = 정지전류 → 정지전류 하한', class-AB면 '최대 ≫ 정지전류'로 나눈다.
  - DEC-65는 구조 분류를 "값 판정에 쓰지 않는다"고 적었다(264행). 분류는 보고 표지다.
  - 'β 최대 = 정지전류'는 source가 레일인 β에만 맞다. 폴딩 캐스코드 M6(β, source X -- `outstage.jsonl` terms)처럼 source가 신호에 따라 전류가 바뀌는 노드면 최대 전류는 그 가지의 KCL이 정한다. O-122 근거 '내부 단자 β 1.19×'가 이 경우다.
  - 일반형: 공급 능력 = 정의(범위 끝 V에서 입력을 끝까지 몬 DC 해의 순 전류) 하나. 분류는 '손계산 규칙을 어떤 꼴로 쓰는가'(U-115)에만 영향을 준다. 값 규칙의 갈래로 두지 않는다.
- **class-AB 정지전류**: 초안 'class-AB 정지전류는 L2(a)와 rout·안정도가 정한다'는 맞다. 근거: Xie & Chen 2019 p.2 §II.B("The limitation of reducing the current further more is the stability requirement", `assets/library/sources/current_reuse_telescopic_ota__xie_chen_2019/paper.md` 271-279행), Allen L26 p.26-10("the common-source, push-pull is ideal if the quiescent current can be controlled"). 다만 이것은 class-AB 전용 규칙이 아니라, '부하 요구가 정지전류를 묶지 않을 때 정지전류는 ss 제약이 정한다'는 일반 사실이다. class-A에서도 ss 하한(예: two_stage_ota_sf rout → 54.6 µA)이 L1보다 크면 ss가 정한다.
- **파형별 합성**: 계단 = 합(램프 끝에서 두 항이 동시에 최대 -- 정확), 사인 = Vp·√(1/R² + (ωC)²)(합은 최대 √2배 과대), I_L = 상수 더함. 맞다(min_current_from_load §1.3). 단 L2(b)가 엔진에 없으면(§2.5) 엔진 쪽 L3는 L1만 검사하고, 합성은 사용자 손계산 선언(`load_peak_amp`) 또는 oracle `.tran`에서만 생긴다.

### 2.5 L2(b)와 O-122 -- 같은 것인가

- O-122 원문: "슬루 판정과 탐색 모두 oracle `.tran` … 엔진은 슬루에 관여하지 않는다 … 엔진 슬루 경계 행 … 삭제 대상 … 원래 취지와 다름: O-121 B-1의 '엔진 = 출력 노드 전류 경계'를 '엔진 관여 없음'으로 바꿈".
- O-121 B-1 (나′) 원문: "엔진 손계산은 출력 노드 전류 하한(dV/dt = I/C 물리 필요조건: SR >= X이면 출력 노드 공급 전류 >= X*C) 탐색 경계로만".
- 초안 L2(b)+L4: "속도 선언 → C_L을 요구 속도로 움직이는 전류 → 사이징의 손계산 하한 → θ 제약(DEC-70)·층 0 역산(DEC-71 (4))".
- 판정: **같은 장치다.** (나′)의 'X·C 하한 = 탐색 경계'와 L2(b)의 'C·SR 하한 = θ 제약·층 0 하한'은 같은 식, 같은 쓰임(탐색 공간을 자름)이다. 차이는 둘뿐이다. (i) L2(b)는 속도 선언을 SR 하나에서 f·Vp·정착으로 넓혔다. (ii) L3에서 R 항과 합성한다. 둘 다 O-122의 결정 대상(엔진이 속도에서 경계를 만드는가)을 바꾸지 않는다. DEC-71 (3) 원문도 "'슬루 하한'은 v6.37 O-122로 없음"이다.
- 다른 길(충돌 없음): 사용자가 C·SR + ΔV/R + I_L을 직접 손계산해 피크 전류로 선언한다. 엔진은 그것을 DC 공급 능력 요구로만 다룬다(속도 판단을 엔진이 하지 않음). min_current_from_load §5 권고와 같다.
- O-121·O-122 실측이 L3에 주는 위험
  - '셀 최대 전류가 상한도 하한도 아님'(내부 단자 β 1.19×, 꼬리 CLM 1.6~4.7×)은 엔진 공급 능력 추정이 증명된 경계가 아니라는 뜻이다(backlog B79).
  - L3을 **탐색을 자르는 제약**으로 쓰면: 엔진 추정 < 실제(내부 단자 β 1.19× 쪽)이면 실제로 되는 점을 버린다(거짓 거부). 엔진 추정 > 실제(끝에서 CLM·포화 이탈)이면 안 되는 점을 남긴다(oracle이 잡음).
  - 안전한 쓰임: β가 레일 source이고 요구 방향 끝에서 VDS가 줄어드는 경우 I_q ≥ I_β(V_끝) ≥ 요구이므로 'I_q ≥ 요구'는 필요조건이다(놓침 0). 이 조건 밖(내부 단자 β, σ 방향)은 '추정' 표기 출발값으로만 쓰고 자르지 않는 것이 맞다(fail-closed는 oracle `.dc`가 맡는다).

### 2.6 DEC-103에 비춘 L1·L3

- L1 요구: spec 원소 값과 선언 범위만 쓴다 → 회로 무관(틀 무관). 위치를 선언하면 이 성질이 지켜진다. 동작점 중심이면 θ 고정 설계점에 기대므로 회로 의존이 된다(§2.1 L1-a, nmcnr에서 성립 불능 사례).
- 공급 능력: 질문이 둘이다.
  - 사이징 '이 β 전류를 얼마로 둘까' = 설계점 → θ 고정. β(레일 source) 하한 I_θ ≥ I_req,끝(필요조건, '추정'), σ 쪽은 출발값.
  - 판정 '이 회로가 끝에서 그 전류를 내는가' = 정해진 회로의 섭동 → W·바이어스 고정 KCL. 엔진 자리는 DE-1 선형 감도 끝(봉인점 DC 야코비안), 정확값은 oracle `.dc`.
  - 초안 L4는 판정을 oracle에만 두었다. DE-1 KCL 자리를 함께 적어야 DEC-103과 맞는다.

## 3. 수정 제안 (초안 v2 -- 사용자 결정 전 기본안)

- **L0′ 부하 정의**: 부하 = 응용 망(DEC-100 -- DUT 밖) 원소 가운데 출력 포트에 닿는 망. 원소 종류는 이상 전류원·저항·커패시터(필요하면 그 밖의 선형 원소). 값의 선언 자리는 netlist 원소 + spec `element_values` 하나다. 값은 반드시 선언한다(engine·pending이면 부하가 아니라 설계 변수 -- fail-closed). DUT/응용 망 소속 표지는 `measurement_load` 하나이고, 그 소비자는 면적·layout·부하 요구다(같은 축: 소속). 이상 전류원에도 이 표지를 허용한다(DEC-100 (7) 개정 -- §7.2 D5).
- **L1′ DC 부하 요구**(영역 DC, `.dc`): 출력 포트 p마다, 선언 출력 범위의 두 끝 V ∈ {V_lo, V_hi}(위치 포함 선언 -- §7.2 D2)에서 I_req,p(V) = 응용 망만의 DC 풀이로 포트 p가 내보내야 하는 전류(부호 = 방향). 단자형 특수형: I_L + (V − V_ref)/R_L. 차동·다출력은 포트 전압 벡터의 선언 범위 꼭짓점에서 푼다.
- **L2′(a) 소신호**(영역 ss): 부하는 MNA 원소로 모든 ss 제약(GBW·PM·이득·rout·잡음)에 그대로 들어간다(DEC-100 (2)). 손계산 출발값은 단일단 gm_1 ≥ 2π·GBW·C_out, 다단 출력 gm_out ≥ 2π·f_np·C_out(design 41 §6.3·§6.5). 새 규칙 없음.
- **L2′(b) 대신호**(영역 ls, `.tran`): 속도 선언(SR, f·Vp, 정착+계단)은 `constraints[]`의 `.tran` metric으로 두고 판정·탐색은 oracle만(O-122 유지). 엔진은 속도에서 전류를 유도하지 않는다. 사용자가 손계산한 대신호 몫을 선언하면(§4 `load_peak_amp` 재정의) L3에서 DC 요구에 더한다. -- O-122를 다시 결정하면 이 항목만 바뀐다(§7.2 D1).
- **L3′ 공급 능력**(영역 DC): 정의 = 출력 포트를 범위 끝 V에 고정하고 입력을 허용 입력 범위 끝까지 몬 DUT ⊕ 응용 망 DC 해에서, 포트를 V에 고정하는 원천이 내보내는(받는) 순 전류(O-26 (1)의 전압을 '동작점'에서 '범위 끝'으로, 전류를 '순 전류'로 확장 -- §7.2 D6). 조건: 방향마다 공급 능력(V_끝) ≥ L1′ 요구(V_끝) + (선언된) 대신호 몫. 구조 분류(class-A/AB)는 보고 표지이고 값 규칙의 갈래가 아니다(DEC-65 유지).
- **L4′ 계산 틀**(DEC-103): 요구 = spec 양(틀 무관). 사이징(θ 고정): 레일 source β 쪽은 I_θ ≥ 요구(필요조건, 층 0 국소 DC 제약 -- DEC-71 (3) '선언'), 그 밖은 '추정' 출발값. 판정: 엔진 = DE-1 KCL 선형 감도 끝에서 공급 능력, 정확값 = oracle `.dc`. 대신호 판정 = oracle `.tran`(O-122).

## 4. 선언 형식 정리안

### 4.1 소비자 실측 (integ/it12 `34585913`, `git -C … grep`)

| 선언 | 엔진 비test 소비자 | test | 계획·design 자리 | library 선언 |
|---|---|---|---|---|
| `driving_spec.load_dc_amp` | 0(읽기만: `authoring/spec_driving.py:17·41`, `spec_model.py:228`; `search/ls_constraints.py:5`는 주석 -- '있다'는 서술은 사실과 다름) | `tests/authoring/test_spec_driving.py`, `test_spec_model.py` | DEC-58, N3.7 595행, N3.15 894행, design 40 963·1251 (다) | 0 |
| `driving_spec.load_peak_amp` | `metrics/ls_fields.py:99-102`(`load_peak_margin_a` = 두 방향 최솟값 − 피크), `search/ls_constraints.py:20·27·48-57`(행 `ls:load_peak_amp>=`) | `tests/metrics/test_ls_fields.py`, `tests/search/test_ls_constraints.py` | DEC-58, DEC-65, N3.7, N3.8 625행, DE-1 (d), U-115, O-123 | 0 |
| `driving_spec.slew_rate_v_per_s` | `search/ls_constraints.py:19·27·38-47`(슬루 행 -- DE-1 (d) 삭제 대상, 선언 표시 `oracle_judged`만 남음) | 같은 test 둘 | N3.8 610·626행, VB-1 | 0 |
| `compensation_targets.settling` | 0(`authoring/spec_targets.py:12-13` 읽기만) | -- | -- | current_reuse 1 |
| oracle 측정 이름 | `tools/spice_oracle/oracle_compare.py:85` `TRANSIENT_MEASURES = ("slew_rate_v_per_s", "settle_s")`(`not_measured`) | `tools/spice_oracle/tests/test_oracle_transient.py` | N3.8 626행 | -- |
| `element_values.<el>.measurement_load` | 면적 `search/area_decl.py`, layout(DEC-100 (4)) | `tests/integration/test_stage_b_library.py:218` | DEC-100, N3.16 939행 | C·R 9개(CL 8회로·CL1/CL2·RL) |
| `current_source` `value_dc_amp` | KCL 고정 전류(`spec_elements.py:41`, design 41 578행) | -- | DEC-08 | 2(Iref 1.2 µA, IBias 50 µA -- 둘 다 바이어스) |

heldout spec 3개(cnr·erfc·rfc)에도 `driving_spec` 선언이 있다(적중 1~4). 근거로 쓰지 않았고, 지우면 그 파일들도 같은 변경에서 옮겨야 한다는 사실로만 적는다.

### 4.2 정리안 (기본안)

| 선언 | 처리 | 이유(원칙) | 같은 변경에서 고칠 것 |
|---|---|---|---|
| `load_dc_amp` | **삭제**. 정적 부하 전류는 netlist 이상 전류원 원소(출력 포트에 닿음) + `element_values.<I>.value_dc_amp` + 응용 망 표지로만 선언(표지 허용은 D5 -- 기본안 (다)면 AP-1 전까지 출력 포트 이상 전류원 부하는 fail-closed, library 해당 0) | graph 규칙 1(같은 양 두 생산자 금지 -- G3), L0′ '선언 자리 하나' | authoring `VALUE_KEYS`(spec_driving.py:17), spec_model `DrivingDecl`, SPEC_CONTRACT 71행, test 둘, 계획 N3.7·N3.15·DEC-58, design 40 963·1251 (다), heldout spec 이관 |
| `load_peak_amp` | **뜻을 좁혀 남김**(D3 기본안): '사용자가 손계산한 대신호 몫 I_ls,방향'만. 엔진은 L1′(DC)을 원소에서 유도하고 L3′ 판정에서 둘을 더한다. 방향별 두 값(source/sink)으로 바꾼다 | graph 규칙 1·3(엔진이 유도하는 몫과 사용자 몫을 한 칸에 섞지 않음), O-122(엔진은 속도에서 유도 안 함) | `ls_fields.py:99-102`(두 방향 최솟값 → 방향별), `ls_constraints.py:48-57`, DE-1 (d) |
| `slew_rate_v_per_s` | **자리 이동**: `constraints[]`의 `.tran` metric(N3.8 방향별 `slew_rise_v_per_s`·`slew_fall_v_per_s`, 하나만 선언하면 두 방향 적용) | 속도 선언 자리 하나(D7), oracle 이름과 맞춤 | `ls_constraints.py` 선언 표시 경로(`_METRIC_SLEW`), VB-1 |
| `compensation_targets.settling` | **자리 이동**: `constraints[]` `settle_s`(+ 계단 크기 선언 -- 없으면 하한 정의 불능) | 소비자 0(G2) 해소, 속도 선언 자리 하나 | `spec_targets.py:12-13·23·42`, current_reuse spec |
| `driving_spec` 섹션 | 위 셋이 빠지면 **섹션 삭제** | 자리 하나 | 로더 미지 필드 거부 목록, `_module_map.py:437·830`, `search_context.py:129` |
| `measurement_load` | **뜻 명확화 + 이상 전류원 허용**: 'DUT/응용 망 소속'(소비자 = 면적·layout·부하 요구) | DEC-100 (1)의 축 그대로, graph 규칙 3(같은 축 하나) | `spec_elements.py` `LOAD_KINDS`, DEC-100 (4)(7), SD-1 |
| 출력 범위 위치 | **새 선언**(D2 기본안: `swing_out_v` 제약에 선택 칸 `range_v: [lo, hi]` 또는 별도 `output_range_v`) -- 이름은 design | L1′ 정의에 필요, 상수 발명 금지(위치를 추정하지 않음), fail-closed(없으면 R 항 '미측정') | N3.8 609행, N3.15 |

## 5. library 영향 (heldout 제외)

손계산 = `out/handcalc.txt`, 층 0 전류 = `out/outstage_recheck.jsonl`(이번 재측정) 대조 앞선 `_scratch_mincur/out/outstage.jsonl`.

재측정 사실: 층 0 시작점 6회로의 출력단 전류는 앞선 값과 같다(two_stage_ota M6·M7 24.83 µA, two_stage_ota_sf M8·M9 27.09 µA, folded M6·M8 1.13 µA, ngcc M12 44.23 µA, nmcnr M302 1.154 mA·M301 1.123 mA, pushpull M1·M2 0.152 nA). sf_pushpull·current_reuse는 층 0 실패(B81)라 다시 돌리지 않았다. common_gate는 앞선 값(0.15 nA)을 인용했다.

| 회로 | 출력 포트·구조(S1v, 실측) | 부하(spec `element_values`) | L1 DC 요구 | L2(a) 소신호(손계산 하한) | L2(b) 대신호 | 층 0 출력단(재측정) | 층 0 출발 전류·B80 front 0 영향 |
|---|---|---|---|---|---|---|---|
| pushpull_follower_buffer | vout push_pull(M1 σ / M2 σ) | CL 1 pF | 0(R·I 부하 없음) | 정의 안 됨(GBW·PM 없음). 참고: rout ≤ 1 kΩ은 DUT ss 제약 → Σ(gm+gmb) ≥ 1 mS(층 0 gm/ID에서 19.3 µA, B80) | 없음 | M1·M2 0.152 nA | 없음. B80 원인·해법(LA-1 rout 국소 제약) 그대로 |
| sf_pushpull_output_opamp | vout push_pull(M22 σ / M21 σ) | CL 1 pF | 0 | f_np ≥ 60 MHz/tan 20° = 164.8 MHz → gm_out ≥ 2π·f_np·C_L = 1.036 mS(rout 1 mS와 비슷) | 없음 | 층 0 실패(B81) | 없음(봉인점 없음이 먼저) |
| two_stage_ota | OUT class_a(M6 σ / M7 β) | CL 3 pF | 0 | f_np ≥ 19.23 MHz → gm6 ≥ 0.3625 mS | 없음 | M6·M7 24.83 µA, gm6 = 24.83 µA × 14.83 = 0.368 mS(하한 위 1.6 %) | 없음. 층 0 점이 이미 L2(a) 하한에 붙어 있다 -- 매크로 경로가 L2(a)를 쓰고 있다는 사실 |
| two_stage_ota_sf | vout class_a(M8 σ / M9 β) | CL 3 pF | 0 | gm8 ≥ 0.3625 mS(f_np 19.23 MHz). rout ≤ 1 kΩ(DUT) → ≥ 1 mS가 더 큼 | 없음 | M8·M9 27.09 µA, gm8 = 0.497 mS, vout 0.206 V(M9 VDS 0.206 V) | 없음. rout 하한(54.6 µA, min_current_from_load §3.2)이 지배 |
| folded_cascode | out class_a(M6 β, **source X = 내부 단자** / M8 σ) | CL 1 pF | 0 | 정의 대기(GBW SP-5 pending) | 없음 | M6·M8 1.13 µA | 없음. F3 실례: β의 source가 내부 노드라 'β 최대 = 정지전류'가 성립한다는 보장이 없다 |
| common_gate_amplifier | vout none(M3 β / M2 β) | 없음(SP-6(c)) | 0 | 정의 안 됨(C_L·GBW 없음) | 없음 | 0.15 nA(앞선 값) | 없음(이미 front 2) |
| ngcc_3stage_ff | Vout class_a(M12 β / M13·M14 σ, M7 κ) | CL 10 pF | 0 | f_np ≥ 10 MHz/tan 26.6° = 19.97 MHz → gm13+gm14 ≥ 1.255 mS(2극점 근사 하한, 3단 실제 요구는 더 큼) | 없음 | M12 44.23 µA; M13 28.18 µA × 20.24 + M14 14.53 µA × 21.34 = 0.880 mS(하한 아래 -- 층 0 최소형이 ss를 안 씀, B80 F-LA12와 같은 현상) | 없음(부하 쪽 요구가 아니라 ss 하한 미사용이 원인) |
| nmcnr_amplifier | Vout class_a(M302 β / M301 σ) | CL 100 pF, RL 25 kΩ → agnd 0.9 V | **10 µA**(공급 V_hi·흡수 V_lo, 범위 0.5 V를 V_ref 중심에 둔 '추정'; 동작점 중심이면 범위가 vdd를 넘어 성립 불능) | f_np ≥ 2.242 MHz → gm301 ≥ 1.409 mS(2극점 근사 하한). R_L 이득 몫 gm_out·R_L ≈ 35 V/V(출력단 이득 상한, 하한 가정 시) | spec 없음(topology `_paper_target_spec` SR 0.36 V/µs만 -- 채택하면 C·SR = 36 µA, 계단 합 46 µA) | M302 1.154 mA(VDS 0.142 V), M301 1.123 mA(gm 25.3 mS) | L1 비구속(115배). 다만 M302 VDS 0.142 V라 V_hi 쪽에서 β 포화가 먼저 깨진다 -- F1의 실례(전류가 아니라 범위 끝 헤드룸이 묶음) |
| current_reuse_telescopic_ota | Vop·Vom push_pull(M25/M26, M15/M16) | CL1·CL2 1 pF, Cf·Cs 0.5 pF(되먹임 망, `measurement_load` 표지는 아직 없음 -- SD-1 D1 대상) | 응용 망 0(R1·R2는 DUT CM 검출, KCL) | 정의 안 됨(GBW 미선언). C_out ≈ 1.25 pF(되먹임 직렬 등가, 추정) | 정의 불능(정착 40/30 ns 선언, 계단 크기 없음 -- 소비자 0, G2) | 층 0 실패(B81) | 없음 |

- 정의되는 수: L1 ≠ 0은 1/9(nmcnr), L2(a)는 5/9(sf_pushpull·two_stage_ota·two_stage_ota_sf·ngcc·nmcnr) + 대기 1(folded), L2(b)는 0/9.
- 층 0 출발 전류: L1이 묶는 회로 0. L2(a)는 매크로(GBW 선언 회로)에서 이미 쓴다(two_stage_ota 점이 하한에 붙음). B80 front 0(9회로 중 8)의 원인·해법(LA-1의 rout·gain 국소 제약)은 이 원칙으로 바뀌지 않는다.
- 이 원칙이 library에서 실제로 바꾸는 것은 판정 쪽(F1)이다: nmcnr·two_stage_ota_sf처럼 β의 동작점 VDS가 작은 회로는 범위 끝에서 공급 능력이 먼저 무너진다. 이것은 DE-1 출력 범위(스윙) 판정과 같은 자리에서 잡힌다.

## 6. 원칙 점검 (이 감사의 권고)

| 원칙 | 판정 | 근거 |
|---|---|---|
| graph 단일 정본 | 지킴: 부하 값 = spec 원소 값(writer = authoring), 요구 = 그 값을 READS하는 계산, 공급 능력 = DE-1 필드. 새 cache·memo·사본 0. `load_dc_amp` 삭제로 이중 생산자 제거 | §4.2 |
| 상수 발명 금지 | 지킴: 범위 위치·속도는 선언에서만. 예시 gm/ID 10·20은 `handcalc.txt`의 보고용이며 규칙에 쓰지 않음 | §2.1 L1-a |
| fail-closed | 지킴: 위치·값 미선언이면 L1′ '미측정', 이상 전류원 부하 값 미선언이면 거부 | §3 L0′ |
| DC/AC 분리 | 지킴: L1′·L3′ DC(`.dc`), L2′(a) ss, L2′(b) ls(`.tran`) | §3 |
| DEC-103 | 지킴: 요구 = spec, 설계점 = θ, 판정 = KCL·oracle | §2.6 |
| 손계산 속도 | 지킴: 응용 망 DC 풀이·한 줄 식 | §2.1 |
| 회로 이름 | 지킴: 구조(포트·소속 표지·β/σ 분류는 보고만) | §2.4 F3 |
| heldout | 지킴: 소비자 수만 사실로 | §4.1 |
| 계획 우선 | 지킴: §7 개정 골격이 계획 → design → 구현 순서 | §7 |

## 7. 계획 개정 골격과 사용자 결정

### 7.1 개정 골격 (계획 우선 순서)

1. **N2 결정 표 -- 새 DEC '부하 구동 원칙'(L0′~L4′)** + 용어집 '부하'·'응용 망 요구'·'공급 능력' 행 + history H1. (D1~D7 결정 뒤)
2. **DEC-65 / O-26 (1) 정의 확장**: 전압 = 범위 끝, 전류 = 순 전류. 구조 분류는 보고만(문언 유지). U-115 질문을 '범위 끝 순 전류의 손계산 규칙'으로 넓힘. (D6)
3. **DEC-100 정정**: (4) 표지 뜻 = 응용 망 소속(소비자에 부하 요구 추가), (7) 이상 전류원 표지 허용 또는 AP-1까지 fail-closed. (D5)
4. **DEC-58·N3.7 출력 구동 규칙 재작성**: `driving_spec` 문언 삭제, L1′ 요구(범위 끝)·L3′ 판정(방향별)·대신호 몫(D1·D3). J12-f '출력 DC 부하 전류 없음 전제'에 L1′ 참조를 단다.
5. **N3.8**: 출력 범위 위치 규칙(D2), metric 표 625행 방향별 최대 전류 정의 갱신, `settle_s`·`slew_*` 제약 선언 자리(D7).
6. **N3.15·N3.16**: `driving_spec` 섹션 삭제(또는 D3 (나)이면 축소), `constraints[]` 속도 metric, 범위 위치 칸, `measurement_load` 뜻.
7. **DEC-71 (3)(4)**: 블록 전류 입력 '선언' = L1′ 요구(레일 source β 방향 필요조건 하한, '추정' 표기) -- 출력 포트를 덮는 블록만. (4)에 '전류 하한이 있는 소자: ID ≥ I_req에서 gm/ID 정의역을 자름' 갈래 추가.
8. **DEC-70**: D1 (가)를 택할 때만 θ 제약 목록 변경(아니면 손대지 않음).
9. **N7.2 U 항목**: U-115 범위 확장, 새 U(범위 위치·I_L 표지·L2(b) 엔진 여부)를 D 결정으로 닫음.
10. **card**
    - LA-1(N6.14): 범위에 'L1′ 층 0 국소 DC 제약(β 방향)' 추가. library 효과 0(§5)이라 완료 조건은 바꾸지 않음.
    - DE-1(N6.8) (d): 공급 능력 = 범위 끝 순 전류(KCL 감도 끝 자리 재사용), 피크 행 방향별, `load_dc_amp` 소비 경로 삭제.
    - 새 card(가칭 LD-1, spec 형식): `driving_spec` 삭제·속도 metric 이동·범위 위치 칸·`measurement_load` 이상 전류원 허용·heldout spec 이관. 또는 SD-1(N6.21) 확장.
    - VB-1(N6.18): `settle_s` oracle 정의(계단 크기 선언 필요).
    - AP-1(N6.22): 응용 망 분리 2단계에서 L1′ 응용 망 DC 풀이를 그 topology로 옮김.
11. 그 뒤 design 40 §3.8-3(963·1248·1251행)·design 41 §5.3.1(892행)·§5.3.3(924행)·§6.5 개정(S-7).

### 7.2 사용자 결정 항목 (대안 비교)

#### D1. L2(b) 대신호 몫을 엔진이 유도하는가

| 칸 | (가) 엔진이 속도 선언에서 C·SR 하한을 유도해 θ 제약·층 0 하한에 건다(초안 L2(b)) | (나) 사용자가 손계산한 대신호 몫을 선언하고 엔진은 DC 요구로만 더한다 | (다) oracle `.tran`만, 엔진 0(현행 O-122) |
|---|---|---|---|
| 물리 정합 | 필요조건(C_L ≤ C_tot)은 맞다. 공급 능력 추정이 경계가 아니라 거짓 거부 위험(§2.5) | 사용자 계산 정확도에 따름. 엔진 쪽은 DC 비교라 물리 정합 | 정의 그대로 |
| 손계산 일치 | 한 줄 식 | 한 줄 식(사용자) | -- |
| design 단순성 | 낮음: O-122로 지우는 C_tot 필드·행을 되살림 | 중간: 방향별 선언 칸 하나 | 높음 |
| 실측 | library SR 선언 0 → 효과 0. (나′) 60점에서 자른 점 0~12 % | 효과 0(선언 0) | 효과 0 |
| 원칙 | ⚠ 원칙 경고: O-122(엔진 슬루 관여 없음) — 속도에서 탐색 경계를 만드는 것은 O-122가 지운 O-121 B-1 (나′)와 같은 장치다 — user_decisions 849행, 계획 DEC-71 (3) "'슬루 하한'은 v6.37 O-122로 없음". **원래 취지와 다름**. ⚠ 원칙 경고: graph 단일 정본 — 삭제 예정 `c_slew_farad`를 되살림 — DE-1 (d) 삭제 목록 | 정합(엔진은 속도 판단 안 함). graph: 사용자 몫 칸과 엔진 L1′ 칸이 분리됨 | 정합 |
| **권고** | | **(나)** -- 사용자 원문 '두 개념의 부하를 드라이빙하기에 충분한 전류'를 O-122 안에서 담는 길 | (나)가 필요 없으면 (다) |

#### D2. 출력 범위 위치

| 칸 | (가) spec이 절대 범위 [V_lo, V_hi]를 선언 | (나) 폭만 선언 + V_ref(부하 기준) 중심 | (다) 폭만 + 동작점 중심 | (라) 선언 없이 DE-1 측정 창을 씀 |
|---|---|---|---|---|
| 물리 정합 | 정확 | V_ref가 여럿·움직이면 정의 불능 | nmcnr 층 0 점에서 범위가 vdd를 넘어 성립 불능(§2.1) | **틀림**: 요구를 회로 능력으로 정의(순환) |
| 손계산 일치 | 한 줄 | 한 줄 | 한 줄 | -- |
| design 단순성 | 칸 하나 | 규칙 하나 | 규칙 하나 | 없음 |
| 실측 | library 범위 선언 2(nmcnr 0.5 V, current_reuse 2.4 V) 모두 폭만 → 위치 선언 필요 | nmcnr 10 µA | nmcnr 40 µA(성립 불능) | -- |
| 원칙 | 정합(상수 0, fail-closed) | ⚠ 원칙 경고: 상수 발명 금지 — '중심'이라는 위치 규칙은 선언이 아니라 관례 — feedback_compare_alternatives_and_warn('관례를 정의로 쓰지 말 것') | ⚠ 원칙 경고: DEC-103 — 요구(spec 양)가 설계점(θ 동작점)에 기대게 됨 — 계획 302행 | ⚠ 원칙 경고: 물리 정합 — 요구와 능력의 정의가 같아져 판정이 항상 통과 |
| **권고** | **(가)**, 미선언이면 L1′ R 항 '미측정'(fail-closed) | | | |

#### D3. `load_peak_amp`

| 칸 | (가) 삭제(L1′ 엔진 유도 + 대신호 oracle만) | (나) 유지 = 사용자 대신호 몫만, 방향별 | (다) 유지 = 사용자 총 요구(엔진 L1′을 대체) |
|---|---|---|---|
| 물리 정합 | 정합 | 정합 | 사용자가 R 항을 빼먹으면 과소 |
| 손계산 일치 | -- | 한 줄 | 한 줄 |
| design 단순성 | 높음 | 중간 | 중간(어느 쪽이 정본인지 규칙 필요) |
| 실측 | library 선언 0 | 0 | 0 |
| 원칙 | 정합(D1 (다)와 짝) | 정합(D1 (나)와 짝) | ⚠ 원칙 경고: graph 단일 정본 — 엔진이 원소에서 유도하는 R·I 몫과 사용자 선언이 같은 양의 두 생산자 — CLAUDE.md graph 규칙 1 |
| **권고** | D1 (다)면 (가) | **D1 (나)면 (나)** | |

#### D4. `load_dc_amp`

| 칸 | (가) 삭제, netlist 이상 전류원 원소로만 | (나) 유지하고 KCL에 배선 + 같은 포트 원소와 이중 선언 금지 검사 |
|---|---|---|
| 물리 정합 | 정합 | 정합(검사가 있으면) |
| 손계산 일치 | 같음 | 같음 |
| design 단순성 | 높음(경로 하나) | 낮음(KCL 두 입력 경로 + 검사) |
| 실측 | 소비자 0·선언 0 | 같음 |
| 원칙 | 정합 | ⚠ 원칙 경고: graph 단일 정본 — 같은 물리량의 선언 자리 둘 — graph 규칙 1·3, min_current_from_load G3 |
| **권고** | **(가)** | |

#### D5. 이상 전류원 부하 표지

| 칸 | (가) `measurement_load`를 이상 전류원에도 허용(뜻 = 응용 망 소속) | (나) 구조 규칙(출력 포트와 레일 사이 이상 전류원 = 부하) | (다) AP-1까지 미구현, 출력 포트 이상 전류원은 fail-closed |
|---|---|---|---|
| 물리 정합 | 정합 | DUT 바이어스 원천이 출력에 닿는 회로를 오판 | 정합 |
| 손계산 일치 | -- | -- | -- |
| design 단순성 | 작음(LOAD_KINDS 한 줄 + DEC-100 (7) 개정) | 중간 | 가장 작음 |
| 실측 | library 출력 포트 이상 전류원 0(survey) → 효과 0 | 0 | 0 |
| 원칙 | 정합(표지 하나, 축 하나). DEC-100 (7) "1단계에서 할 일은 없고 … AP-1이 정한다"를 앞당기는 것이라 **원래 취지와 다름**(작음) | ⚠ 원칙 경고: 회로 해석은 공동분석 — 구조만으로 DUT/응용 망을 가르는 것은 회로 해석 — feedback_circuit_analysis_from_connectivity_only, DEC-100 (7) | 정합 |
| **권고** | | | **(다)** 지금, AP-1에서 (가) -- library 효과 0이라 서두를 근거 없음 |

#### D6. 공급 능력 정의(O-26 (1) 확장)

| 칸 | (가) 범위 끝 전압 + 순 전류(L3′) | (나) 현 정의(동작점 전압·총 전류) 유지 | (다) 초안 L3(분류별: class-A β = 정지전류, AB = 최대 전류) |
|---|---|---|---|
| 물리 정합 | 정합(Allen L040 p.040-3 순 전류, 끝에서 비교) | F1·F2 결함 | F3 결함(내부 단자 β), DEC-65와 어긋남 |
| 손계산 일치 | LUT 조회(끝 VDS)·KCL 한 줄 | 같음 | 한 줄 |
| design 단순성 | 중간: DE-1 KCL 감도 끝 재사용(새 풀이기 없음) | 높음 | 중간(분류 갈래) |
| 실측 | library 피크 선언 0, L1′ 비구속(§5) → 효과 0 | 0 | 0 |
| 원칙 | 정의 변경이라 **원래 취지와 다름**(O-26 (1) "노드 k를 동작점 전압에 고정") -- 사용자 결정 | ⚠ 원칙 경고: 물리 정합 — 요구(끝)와 능력(동작점)을 다른 전압에서 비교 — Allen L040 p.040-3 | ⚠ 원칙 경고: 구조 분류를 값에 씀 — DEC-65 "값 판정에 쓰지 않는다" — 계획 264행 |
| **권고** | **(가)** | | |

#### D7. 속도 선언 자리

| 칸 | (가) `constraints[]` `.tran` metric(`slew_*`·`settle_s`+계단 크기) | (나) `driving_spec` 유지 + settling은 `compensation_targets` |
|---|---|---|
| 물리 정합 | 같음 | 같음 |
| 손계산 일치 | -- | -- |
| design 단순성 | 높음(제약 한 자리, oracle 이름과 같음) | 낮음(자리 셋) |
| 실측 | library SR 0·settling 1(소비자 0) | 같음 |
| 원칙 | 정합(선언 자리 하나) | ⚠ 원칙 경고: graph 규칙 3 — 같은 종류(속도 요구) 선언이 여러 자리 — settling 소비자 0(G2) |
| **권고** | **(가)** | |

## 8. 미확인

1. RL(nmcnr)이 출력 블록 국소 모델(`block_gain_model`)에 실제로 들어가는지: 모델이 값 선언 저항을 고정 컨덕턴스로 받는 것(`block_gain_model.py:17`)만 확인했다. nmcnr 출력 블록의 `spec.passives`에 RL이 드는지는 실행하지 않았다.
2. '내부 단자 β 1.19×'의 원측정 파일을 찾지 못했다. O-122 행(user_decisions 849행)의 근거 문구만 인용했다.
3. 공급 능력의 범위 끝 손계산(β 끝 VDS LUT 조회)의 정확도는 재지 않았다(oracle `.dc` 대조 없음).
4. Johns & Martin·Razavi 교과서 쪽은 저장소 원문이 없어 쓰지 않았다.
5. 다단 출력 비주극점 하한(2극점 근사)은 3단(ngcc·nmcnr)에서 하한일 뿐이다. 실제 요구는 더 크다(Cm 값 미정).
6. current_reuse 되먹임 망 등가 C(1.25 pF)는 입력 게이트 용량을 뺀 손계산이다.

## 9. 근거 링크

- Allen ECE6412 L040 'CE and CS Output Stages' p.040-3(최대 sink = K'W/2L(VDD−VSS−VT)² − I_Q, 최대 source ≤ I_Q, "both"), p.040-4(gain −gm1/(gds1+gds2+G_L)), p.040-5(Example 5.5-1): https://pallen.ece.gatech.edu/Academic/ECE_6412/Spring_2004/L040-CS&CEOut(2UP).pdf · 로컬 `wt/_scratch_mincur/dl/L040.pdf`(이번에 1~5쪽 직접 열람)
- Allen Lecture 26 'Buffered Op Amps' p.26-2("Ability to sink and source sufficient current (CL·SR)"), p.26-10("the common-source, push-pull is ideal if the quiescent current can be controlled"), Example 26-2(R_L = 500 Ω, C_L = 100 pF, SR 10 V/µs → I15 = 1 mA): https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf · 로컬 `skills/analog-gmid-design/assets/library/sources/pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf`(paper.md 50-56·440-470·1215-1232행)
- Xie & Chen 2019 p.2 §II.B: 로컬 `…/sources/current_reuse_telescopic_ota__xie_chen_2019/source.pdf`(paper.md 271-279행), 웹 찾지 못함
- ADI MT-045(f_FPBW = SR/2πVp): https://wcm-cce.cldnet.analog.com/media/cn/training-seminars/tutorials/MT-045_cn.pdf
