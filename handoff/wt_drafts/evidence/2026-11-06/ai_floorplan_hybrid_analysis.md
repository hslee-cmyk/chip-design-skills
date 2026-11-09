# AI 배치 + 코드 피드백 혼합안 분석 (MOD7 레이아웃 · MOD8 수렴 루프)

- 작성 2026-11-06, 역할: 분석 문서 작성자(문서만 -- 엔진 수정·커밋 없음). 독립 점검(작성자 ≠ 점검자)은 아직 하지 않았다.
- 대상 코드: WB-1 worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261105-wb1-c`, HEAD `716c83d8`. 아래에서 `L/` = `skills/analog-gmid-design/gmid_engine/layout/`, `C/` = `.../gmid_engine/convergence/`, `P` = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(WB-1 판 v6.38.24).
- 엔진 인용의 용도는 원칙 8에 따라 둘로 한정한다. (1) 엔진 밖 사실(PDK·LUT·원문) (2) 재작성 범위(바꿀 코드와 그 소비자). as-built 구조는 판단 근거로 쓰지 않는다.
- 임시 규칙 O-229: 이 문서는 분석만 한다. 아래 단계안은 모두 **LA-1 뒤** 항목이다(5절).

## 사용자 제안 (원문)

> "오일러 패스를 구해서 finger 수를 결정하는 것은 code로 할 수 있을지 몰라도 배치와 routing 영역을 고려해서 각 소자의 W와 finger를 결정하는 것은 순서가 ai가 현재 정해진 각 소자 row의 전체크기를 가지고 compact하게 배치해보고 finger수를 조절하여 row의 크기를 조절할 필요가 있다고 판단하면 이 값을 code로 피드백해주는 방식은 어떨까? 배치를 box형으로 하도록 하는 것을 현재와 같이 code로 구현할 경우와 비교해서 검토해줘"

추가 요구 (원문):

> "ai가 레이아웃 routing 영역을 추정과 finger수를 검토할 때 routing영향분석도 간략하게 수행해서 나중에 layout agent가 finger를 수정하지 않도록 해"

---

## 0. 요지

1. **비교 결론.** 판정은 코드만 하고, AI는 코드가 만든 후보 안에서 제안만 하는 혼합안 (C)를 권고한다. AI가 기하를 직접 정하는 (B)는 권고하지 않는다. (B)는 원칙 위반이 다섯 가지다: fail-closed(E-0), 결정성(graph reuse·S3 graft 키), 상수 발명(원칙 11), PDK 이식성(O-197), 손계산 속도(원칙 1). 그리고 AI 좌표를 받아들이려면 겹침·간격·DRC 검사기가 어차피 코드로 있어야 하므로, (B)도 결국 (A)의 판정 기구를 다시 만든다.
2. **AI가 실제로 더하는 몫은 생각보다 좁다.** 코드는 이미 면적을 목적으로 행 접기·hub 병합·패턴 재구성을 **자동으로** 한다(`L/rows.py:233-280`, LY9). 그래서 사용자 제안의 "finger 수로 행 크기 조절" 가운데 코드에 실제로 비어 있는 자리는 둘뿐이다.
   - (a) 행 그룹마다 finger_w 폭 키를 고를 때 면적을 보지 않는다(`L/finger_geometry.py:31-52`).
   - (b) 배선 영역·배선 기생 모델이 없다. packer에 `net_weights`도 넘기지 않는다(`L/floorplan.py:52,56`).
   (a)는 코드로 닫을 수 있다(A′). (b)는 코드든 AI든 **판정 축이 되려면 코드 모델이 필요하다**. 그래서 AI의 남는 몫은 "큰 조합 공간에서 좋은 후보를 고르는 제안자"와 "배선 의도(배치 순서·인접)의 제안"이다.
3. **혼합안의 핵심.**
   - 코드가 후보를 낸다: 폭 키 × nf(`ly_fw_cand`), 행 접기 n, `WRequest` 손가락.
   - AI는 그 후보 id만 골라 **레이아웃 계획 입력** 하나로 낸다. 이 입력은 graph 입력 필드(writer `ly_input` 하나)이고, AI 응답 기록은 `record_id` 참조로만 붙는다.
   - 코드가 받아들이는 조건: 후보 밖이 아니고, E-0·Euler·matching이 나빠지지 않고, 판정 축 면적이 ΔA_tie보다 더 줄어야 한다.
   - W가 바뀌는 제안은 기존 LY3 `WRequest`와 MOD8 루프(LY7 재평가·K_max·NONCONVERGENT)를 그대로 탄다.
   - test와 재실행은 기록된 계획을 재생한다.
   - AI 호출 자리는 **수렴이 끝난 front 점마다 한 번**(루프 밖)을 권고한다.
4. **routing 영향 분석 (추가 요구).** 항목마다 대부분 **PDK 이미 선언된 출처**(tech LEF `sky130_fd_sc_hd.tlef` -- `PITCH`·`WIDTH`·`RESISTANCE RPERSQ`·`CAPACITANCE CPERSQDIST`·`EDGECAPACITANCE`·`DCCURRENTDENSITY`, 이미 제조 격자 출처로 쓰는 파일)와 엔진 필드(`dc_op` 전류, `ly_rows`, `ly_floorplan` 좌표)에서 상수 없이 정할 수 있다. 단 게이트 poly 시트 저항은 선언 출처를 확인하지 못했다. 판정 방식은 셋으로 나눈다(표 3.6).
   - **코드 fail-closed**: EM(소자 전류 ÷ finger 수 ≤ PDK 전류밀도 × finger 피치 안에 들어가는 배선 폭), 배선 트랙 수용.
   - **코드 추정 + 기록**: 배선 길이·기생 C·R.
   - **AI 기록만**: 배선 의도 서술.
   finger 확정 규칙: MOD8 수렴 스냅샷의 `RealizedGeometry`(nf, finger_w, 행 확산)가 정본이다. 이후 상세 배치·배선 단계가 이를 바꾸면 sign-off 불가(fail-closed)다. 바꿀 필요가 있으면 `WRequest{reason=routing_*}` 재진입 레코드로 MOD8에 돌아온다.
5. **결정 질문 9개**(6절). 핵심은 다음 넷이다.
   - Q1: 진행할지, 언제 할지. 권고 = LA-1 + O-225 재점검 뒤, A′ 먼저.
   - Q3: 배선을 판정 축에 넣을지.
   - Q7: 배선 기생을 손계산(AC)에 넣을지. 권고 = EM·트랙만 지금, 기생은 oracle과 함께 다음 card.
   - Q8: finger 확정 뒤 변경을 금지하고 재진입시킬지.

---

## 1. 현행 레이아웃 파이프라인 사실 (원 파일:행)

### 1.1 흐름

`C/converge_point.py:65-152` (front 점마다)
→ `place_layout`(`C/place_layout.py:128-146`, 평가 커널 0)
→ `run_layout`(`L/run.py:110-119`)
→ 블록을 코드에 고정된 순서로 돈다(`L/run.py:52`): `_slice_block` → `canon_tables` → `finger_candidates` → `pattern_select` → `finger_geometry` → `compose_rows`
→ `effective_placement`(`C/effective_placement.py:86-106`) → `realized_geometry`
→ 고정점 비교(`C/converge_point.py:101-103`)
→ `evaluate(geometry=)` 1회(`:121-122`)
→ 통과면 새 현재 점, 위반이면 요청 거부, 그다음 행 그룹 폭 키 제외(`C/key_exclusion.py:59-68`), 마지막으로 INFEASIBLE.

| 단계 | 사실 | 위치 |
|---|---|---|
| 폭 슬라이스 | 보존량에서 폭 키마다 W_need = ID / J_slice. LUT 공개 API로만 읽는다. 사용할 수 없는 폭은 사유를 남긴다. | `L/slice_density.py:25-42` |
| 손가락 후보 | 폭 키마다 nf = floor·ceil(W_need/fw). 오차가 실효 허용오차(`w_tolerance` = max(tol_V·gm/ID, grid/(2fw))) 안이면 ok, 밖이어도 기록한다. MOD8이 뺀 키는 제외한다. | `L/finger_candidates.py:21-33`, `L/w_tolerance.py:14-18` |
| 손가락 확정 | 패턴 그룹 멤버는 그룹이 고른 값을 쓴다. 그 밖의 소자는 행 그룹마다 "ok인 소자가 가장 많은 키 → nf 합 최소 → 큰 키" 순서로 고른다. **면적·행 길이는 보지 않는다.** ok인 후보가 없으면 오차 최소 후보를 잠정으로 쓰고 `WRequest{reason="finger_quantization"}`. | `L/finger_geometry.py:31-52, 74-82` |
| 행 | 행 폭 = Σ nf·(L + `finger_pitch_overhead_m`), 높이 = finger_w. 패턴 행은 `check_walk_sequence`로, 나머지는 `row_euler`(Euler → 거울 trail → 최소 crossover)로 순서를 정한다. W는 바뀌지 않는다. | `L/rows.py:95-96, 98-118`, `L/row_euler.py:46-91` |
| hub 병합 | stage를 넘는 공유 넷 행을 합쳐 판정 축 면적이 줄면 채택한다. 노이즈 우려는 기록만 한다. | `L/rows.py:148-180` (LY11) |
| 행 접기·재구성 | **자동**(LY9). matching 없는 행은 `apply_explicit_row_split` n = 2..max nf로 접어 면적이 줄면 채택한다. matching 패턴 행은 패턴 함수 k행으로 다시 짓고, matching(dx·dy·crossover)이 나빠지면 거부한다. 소자 nf·fw는 바뀌지 않는다. | `L/rows.py:193-280` |
| box | 행 폭 비·길이 비를 **기록만** 한다(하드 게이트 없음, Q8 (vi)). | `L/box_shape.py:12-20` |
| floorplan | 행 블록(+ 양끝 dummy) → 행 그룹마다 `pack_group_as_unit` + tap 띠 → well 묶음(kind, body)마다 `pack_floorplan` → 묶음·수동소자 블록을 `pack_floorplan`(gap = max(행 간격, well 간격)). 판정 축 면적 = bbox. 길이는 격자 칸 단위의 물리 치수다. | `L/floorplan.py:41-66, 91-123` |
| packer 목적 | 높이 후보 H를 sweep해 결합 결과의 **aspect ratio 최소**를 고른다. sweep 폭 상수(`height_steps=40`, `width_steps=60`, `height_tolerance=1.0`, `width_tolerance=2.0`, H = h0·(0.3 + 2.2·i/steps))는 복사본 리터럴로 manifest에서 예외 처리돼 있다. | `L/floorplan_pack.py:324-405`, design_mod7 §2.2 |
| 배선 | `net_weights`·`connections` 인자는 있지만(`L/floorplan_pack.py:46-73`) `floorplan.py`가 넘기지 않는다(`:52`, `:56`). 행 간격은 PDK `row_gap_m` 하나다. **배선 채널·배선 기생 모델 없음.** PDK 레이아웃 양은 다섯 개뿐이다(`L/contract_input.py:43` `PDK_RULE_QUANTITIES`). | |
| 확산 기하 | 최종 행 Euler에서 소자별 ad/as/pd/ps(finger 평균). 오라클 `w = finger_w`, `m = nf`. | `L/diffusion.py:50-66` (LY8, DEC-91 (2)) |
| W 요청 | `WRequest(device, W_old_m, W_new_m, nf, finger_w_m, reason, group)`. 레이아웃은 W를 적용하지 않는다. | `L/contract_output.py:110-120` (LY3) |
| MOD8 | K_max = k_max(max\|ln W실현/W사이징\|, min tol)를 첫 레이아웃에서 한 번 정한다. 같은 상태의 DC 상태(입력 손가락)로 돌아오는 주기는 즉시 NONCONVERGENT. 레이아웃 안 재시도는 커널 0. 레이아웃 입력 기준점은 늘 front 점 스냅샷이다. | `C/w_loop_bound.py:15-22`, `C/converge_point.py:104-113`, `:1-21` docstring |
| 호출처 | `converge` 비test 호출처는 0이다(`run_gmid_design_pipeline` 정의 grep 0). **LA-1 측정 경로 밖**(A-124와 일치). | grep 실측 |

### 1.2 오케스트레이터 1차 검토 요지와 원 파일 대조 (정정 3건)

| 1차 검토 문언 | 원 파일 | 판정 |
|---|---|---|
| "행 접기는 명시 선언 때만(`row_fold.py` '설계자 판단')" | 복사본 docstring(`L/row_fold.py:11-31`)은 그렇게 쓰지만, 호출 측 `compose_rows._fold`·`_improve`(`L/rows.py:233-280`)가 matching 없는 행을 **면적 목적으로 자동 접는다**(계획 LY9, DEC-93 (3)). 복사본 docstring은 수정 금지 상태라 호출 측과 어긋난 채 남아 있다. | **틀림** -- 자동 접기 |
| "`floorplan_pack.py`(크기는 비율 대리값이라 주석)" | 복사 docstring(`L/floorplan_pack.py:13-15`)은 '비율 프록시'라고 쓰지만, `floorplan.py:47-49`는 (행 폭 + dummy)/격자, finger_w/격자 = **물리 길이(격자 칸)**를 넘기고 bbox에 격자를 곱해 m²로 돌린다. | **조건부** -- 주석은 낡았고 값은 물리 치수 |
| "W = nf·finger_w·PDK 선언 규칙으로 행 크기" | 행 **폭** = Σ nf·(L + finger 피치 여유)이고, 행 **높이** = finger_w다(`L/rows.py:95-96`, `L/floorplan.py:49`). nf·finger_w는 W이지 행 폭이 아니다. | **정정** |
| "MOD8 … AC 제약 재판정" | 재평가는 평가 커널 1회 + 봉인 + spec 제약 행 전부다(`C/converge_point.py:55-58, 121-124`). AC만이 아니다. | **정정**(범위가 더 넓음) |
| 나머지(오일러 trail, 정합 패턴, box 기록만, 배선 영역 모델 없음, `WRequest` 7칸) | 위 표와 같다. | 맞음 |

### 1.3 AI가 들어갈 수 있는 자리 (재작성 범위)

| 자리 | 지금 정하는 것 | AI 제안이 바꿀 수 있는 것 | 판정 주체 |
|---|---|---|---|
| ① `finger_geometry` 폭 키 선택 | 소자 수·nf 합·큰 키(면적 무관) | 행 그룹별 폭 키(= 행 높이·nf → 행 길이) | 코드(면적·E-0) |
| ② `_improve` 접기 n·순서 | 폭 내림차순 탐욕, 면적이 줄면 채택 | 행별 n, 시도 순서 | 코드(면적·matching) |
| ③ hub 병합 | 면적 비교 | 병합 묶음 | 코드 |
| ④ floorplan 배치 순서·인접 | skyline + aspect 최소, 연결 무시 | 배치 순서·인접 쌍(배선 의도) | 코드(면적 + 배선 모델이 생기면 그 모델) |
| ⑤ `WRequest` | `finger_quantization`·`cc_nf` | `reason=floorplan`/`routing_*` 요청(후보 손가락 안) | MOD8 재평가 |

---

## 2. 대안 비교표

- (A) 현행 코드 확장: 배선 영역 모델과 2D 패킹 목적함수를 더한다. A′는 그 가운데 ① 폭 키 선택을 면적 탐색에 넣는 최소안이다.
- (B) AI가 기하(좌표·nf·finger_w)를 직접 정한다.
- (C) 혼합안: 코드가 후보와 판정, AI가 후보 안에서 선택을 제안한다.

| 기준 | (A) 코드 확장 | (B) AI 직접 결정 | (C) 혼합안 |
|---|---|---|---|
| 배치 품질 | 휴리스틱 한계. packer 스스로 "non-slicing 전체 최적화는 SA급 B*-tree가 필요하고 범위 밖"이라고 적어 둔다(`L/floorplan_pack.py:345-350`). A′로 ① 공백은 닫힌다. | 배선 의도·전체 배치 감각은 강할 수 있다. 검증 불가 부분이 남는다. | AI 제안이 면적을 줄일 때만 채택하므로 **(A) 이상이 보장**된다. 배선 품질은 코드 모델이 있어야 판정된다. |
| 원칙 1 (손계산 속도, 호출 수) | 블록 ms 단위, 레이아웃 안 재시도는 커널 0(LY7). front 점 × (K_max + 키 제외 수) 레이아웃 호출. | front 점 × 레이아웃 호출마다 AI 1회면 초~수십 초 × 호출 수 ⚠. 루프 안 AI는 원칙 1 위반 꼴이다. | AI는 **수렴 뒤 점마다 1회**(루프 밖) → AI 호출 = 최종 front 점 수. 코드 루프는 그대로 빠르다. |
| 원칙 11 (상수 발명) | 배선 모델 계수는 PDK 선언(tlef 피치·RPERSQ·CPERSQDIST)에서 유도할 수 있다. packer sweep 리터럴은 기존 예외 그대로다(LY11). | ⚠ AI의 "필요하다고 판단" 문턱은 선언되지 않은 암묵 상수다. 원문 경험값(예: 원본 316쪽 'finger 폭 1~3 µm 최적')을 끌어올 위험이 있다(원칙 13). | 채택 기준이 코드 판정 축(면적 > ΔA_tie, `L/area_tie.py:12-15`)이라 AI 문턱은 결과에 들어가지 않는다. |
| 결정성·재현성 (graph reuse·S3 graft) | 순수 함수라 입력 버전이 같으면 재사용된다. | ⚠ 같은 입력에 다른 출력 → 입력 버전 키가 결과를 정하지 못한다. IC2(`test_order_shuffle_invariance`) 위반 꼴이다. | AI 출력 = **입력 필드**(지문이 키). 재실행·test는 기록 재생이라 결정적이다. |
| 물리 정합·fail-closed (E-0) | 기존 게이트 그대로다. | ⚠ AI 좌표·nf가 겹침·간격·EM·matching을 어기면 거를 코드가 필요하다 → 결국 (A)의 검사기를 만든다. | 후보 밖·E-0 위반·matching 악화·면적 미개선이면 **거부하고 사유를 기록**한다. AI가 응답하지 않아도 코드 결과가 그대로 판정 결과다(아래 ⚠ 참조). |
| graph 단일 정본 | 필드·writer를 그대로 둔다. ① 개선은 폭 키 선택을 `compose_rows` 탐색과 **같은 블록**으로 옮기는 재작성이 필요하다(지금처럼 `finger_geometry`가 `ly_finger`를 쓰고 `compose_rows`가 다시 고르면 둘째 생산자 ⚠). | ⚠ AI 값의 writer가 graph 밖이다. | 계획 = `ly_input` writer가 쓰는 입력 필드 하나(`ly_plan` 가칭). AI 응답 원문은 evidence 기록이고 `record_id`로만 참조한다(값 사본 아님). |
| O-197 PDK 이식성 | 배선 양은 역할 이름(배선 층 피치·시트 저항·면 용량·변 용량·전류밀도)으로 선언하고 값은 PDK 선언에만 둔다. | ⚠ AI 프롬프트·응답에 공정 경험값이 섞인다. | AI 입력은 코드가 낸 수치(역할 이름 키)뿐이다. AI 출력은 후보 id라 PDK 값을 담지 않는다. |
| 원칙 9 (만들면 배선) | ① A′는 `finger_geometry` 선택 규칙을 **대체**한다(옛 규칙 삭제). | 무엇을 대체하는지 불명확하다. | AI 계획은 ①②④의 코드 기본 선택을 **대체**하는 입력이다(계획이 없으면 코드 기본). ⚠ "계획 있음/없음" 두 갈래가 생긴다 → 아래 A-139 점검. |
| A-139 (새 집합·갈래 불필요 복잡도) | 새 갈래 0(A′). 배선 모델은 필드 1~2개. | 갈래·검사기가 많다. | ⚠ 갈래 1개(계획 입력이 있는가). 갈래를 없애려면 "코드 기본 선택도 계획 한 꼴로 쓴다"(코드가 기본 계획을 만들고 AI는 그 계획을 고친다)로 하나로 묶는다 → 갈래 0. 권고는 이 꼴이다. |
| 비용 | 구현·test만 든다. | AI 호출 비용 × 호출 수 + 검사기. | AI 호출 = 최종 front 점 수. 계획 스키마·검사·재생 test. |
| 실패 모드 | 국소 최적에 머문다(지금 수준). | 응답 실패·형식 오류·불일치 시 동작이 정해지지 않는다 ⚠. | 응답 실패·형식 오류 → 계획 없음 = 코드 기본 계획(**우회가 아니라 정의**: AI는 제안자라 없어도 판정 자리가 비지 않는다). 후보 밖 id → 그 항목 거부 + 사유(조용히 고치지 않음). 재생 시 후보 집합이 달라짐(입력 변화) → 계획 무효 사유 기록(`plan_stale`), 코드 기본 계획. |

⚠ 요약:
- (B)는 E-0·결정성·원칙 11·O-197·원칙 1 다섯 축에서 위반이다.
- (C)의 "AI 실패 = 코드 기본 계획"은 원칙 10(우회 금지)과 부딪히는지 따로 확인해야 한다. 근거: 판정 대상은 언제나 코드가 만든 기하이고 AI는 선택을 제안할 뿐이므로, AI가 없는 경우는 '판정 skip'이 아니라 '제안 없음'이다. 단 **AI가 낸 계획을 코드가 거부한 경우**는 거부 사유가 결과에 반드시 남아야 한다(조용한 소실 금지, IC3).
- (A)·(C) 모두 배선을 판정 축에 넣으려면 **코드 배선 모델이 먼저**다.

---

## 3. 혼합안 설계 초안

### 3.1 후보 생성 범위 (코드 몫 / AI 몫)

| 항목 | 코드가 내는 후보 | AI 몫 | 근거 |
|---|---|---|---|
| 행 그룹 폭 키 | `ly_fw_cand` ok 후보의 폭 키(행 그룹 공통; 패턴 그룹은 패턴 후보) | 행 그룹마다 키 하나 선택 | LY2, `L/finger_candidates.py` |
| nf | 그 키의 floor·ceil(W_need/fw) 중 ok인 것 | 선택(ok 밖은 `WRequest` 후보로만) | LY1·LY3 |
| 행 접기 | matching 없는 행의 n ∈ {1..max nf}(확산 안전 분할점), matching 행은 패턴 함수 k | 행별 n | LY9 |
| hub 병합 | `find_hub_merge_candidates` 후보 | 병합 묶음 선택 | LY11 |
| 배치 | 블록 목록(크기는 코드가 계산) | 배치 순서·인접 쌍·well 묶음 순서(좌표는 코드 packer가 계산) | LY10 |
| W 변경 | `WRequest` 후보 = ok 밖 후보의 (nf, finger_w), cc_nf 후보 | 요청할 소자·후보 선택 + 사유 | LY3·LY5 |
| 정확히 풀리는 것 | Euler·거울 trail·crossover·패턴표·면적·확산 기하 | 없음 | LY4·LY8 |

AI는 **좌표·W·finger_w 수치를 직접 내지 않는다**. 후보 id만 낸다. 이렇게 해야 원칙 11과 O-197을 지킨다.

### 3.2 AI 입력·출력 스키마 (초안)

- **입력** (코드가 수렴 스냅샷에서 만든다, 값은 모두 graph 필드 READS):
  - 행 목록 {row_id, kind, body, 폭 m, 높이 m, 소자·nf, Euler 방법·crossover}
  - 행 그룹별 폭 키 후보와 그 후보의 행 폭·높이·면적 변화
  - 접기 후보 n별 면적(`FoldAttempt`에 이미 있다)
  - 현재 floorplan 배치·외곽 면적·ΔA_tie
  - 3.6 routing 영향 분석 표(코드 계산값)
  - 넷 연결(행 사이 공유 넷)
- **출력** = `LayoutPlan`: {plan_id, 기준 입력 지문, 항목[{kind: fw_key|fold|merge|order|w_request, 대상, 후보 id, 근거 문장}], record_id}

### 3.3 AI 결정 기록의 graph 자리

| 안 | 내용 | 판정 |
|---|---|---|
| (가) 입력 필드 하나 | `LayoutInput`에 `plan` 열을 더한다 → `run.py` `_input_columns`가 graph 입력 필드로 쓴다(writer `ly_input` 하나). 소비 블록(폭 키·접기·배치)이 READS. 입력 지문이 graph reuse·S3 graft 키에 들어간다. | **권고** -- 원칙 7 규칙 1·2·4 충족 |
| (나) 실행 기록 | AI 결과를 실행 기록(sctx·결과 객체)에 둔다. | ⚠ 새 sctx 슬롯·값 사본 = 원칙 7 금지 |
| 계획 파일 | AI 응답을 evidence 파일로 둔다. | **선언 입력**(spec·topology와 같은 부류)으로 정의할 때만 허용한다. AI 재호출을 피하는 memo로 쓰면 graph 밖 cache ⚠. 이 분류의 정본 자리는 계획 N3.3에 없다 → **S-7: 계획 개정이 먼저**(Q4). |

### 3.4 재생 규칙

1. 계획은 `기준 입력 지문`(그 계획을 만든 레이아웃 입력의 `fp_of`)을 갖는다.
2. 재실행할 때 각 항목의 후보 id가 지금 후보 집합에 있으면 적용한다. 없으면 그 항목을 `plan_stale` 사유로 거부·기록한다.
3. test는 기록 계획 파일만 쓴다(AI 호출 0).
4. 같은 계획 + 같은 입력 → 비트가 같은 결과(IC2).

### 3.5 검증 경로 (코드가 거부하는 것)

| 거부 | 사유 |
|---|---|
| 후보 id가 후보 집합 밖 | `plan_out_of_candidates` |
| 실현 W 허용오차 밖인데 `WRequest`가 아님 | LY3 위반 |
| 행 Euler(walk) 실패, matching dx·dy·crossover 악화 | LY9와 같은 거부 |
| 판정 축 면적이 코드 기본안 대비 ΔA_tie를 넘게 줄지 않음 | `area_not_decreased` -- 개선 없는 AI 안은 채택하지 않는다 |
| EM·트랙 수용 위반(3.6) | E-0 꼴 물리 관문 |
| 소자 집합 불일치(coverage) | IC3 |

### 3.6 routing 영향 분석 (추가 요구 (1))

목적: finger 결정을 이 단계에서 확정해, 뒤의 상세 배치·배선 단계(layout agent)가 finger를 다시 바꿀 이유를 미리 없앤다. 항목마다 계산은 코드가 한다(AI는 이 표를 읽고 제안한다).

**확인한 PDK 출처 사실**: PDK 선언 `assets/sky130_pdk_decl.json:8`이 이미 tech LEF `sky130_fd_sc_hd/tech/sky130_fd_sc_hd.tlef`를 sha 고정 출처로 쓴다(제조 격자, `:106`). 그 파일에 배선층마다 `PITCH`·`WIDTH`·`RESISTANCE RPERSQ`·`CAPACITANCE CPERSQDIST`·`EDGECAPACITANCE`·`DCCURRENTDENSITY AVERAGE`·`ACCURRENTDENSITY RMS`, via마다 via당 `DCCURRENTDENSITY`가 있다(`/c/pdk/sky130_fd_sc_hd/tech/sky130_fd_sc_hd.tlef:59-260`, li1·met1~met5, mcon·via~via4). 지금 레이아웃 PDK 양은 다섯 개뿐이다(`L/contract_input.py:43`). 아래 항목은 **새 역할 이름 선언**이 필요하다(값은 선언 한 곳, O-197). 게이트 poly 시트 저항은 tlef에 poly 층이 없어 **출처를 확인하지 못했다**(모델 카드 rshg 등은 미확인).

| # | 항목 | 정하는 식·입력 (상수 없음 여부) | 출처 | 판정 |
|---|---|---|---|---|
| R1 | 배선층 수·방향 | tlef `LAYER` 목록(라우팅층) 선언. 아날로그 블록 사용 층 수는 선언 몫(사용자·PDK 선언) | tlef | 기록(선언값) |
| R2 | 배선 채널 폭 | 행 사이 경계를 지나는 넷 수 × 그 층 `PITCH`. 넷 수는 행 사이 공유 넷(`ly_rows` 넷 순서·핀)에서 센다. 상수 없음. | tlef PITCH + `ly_rows` | **코드 추정 → 판정 축 면적 반영 여부는 Q3**. 반영하면 `row_gap_m` 대신 max(행 간격, 채널 폭) |
| R3 | 정합 쌍 대칭 배선·교차 수 | 패턴 결과의 crossover·고립쌍(이미 있음) + 정합 쌍 넷이 같은 층·같은 길이로 가는지(HPWL 차) | `ly_groups`, `ly_rows` | crossover는 이미 판정(LY4 정렬 키), 길이 차는 기록 |
| R4 | 전류밀도 EM (finger당 S/D 띠) | 띠 하나 전류 = \|ID\|/(nf+1)·(공유 확산 수) 꼴, 상한 = `DCCURRENTDENSITY` × 띠 폭; 띠 폭 ≤ finger 피치 안 확산 길이(`finger_pitch_overhead_m`, 이미 선언). via·contact는 개수 × via당 한도. ID = `dc_op`. 상수 없음. | tlef + 엔진 `dc_op` + 기존 PDK 양 | **코드 fail-closed**(물리 한도 = E-0 꼴): 위반이면 nf를 늘리는 `WRequest{reason=routing_em}` 후보를 만든다 -- finger를 뒤에서 바꾸는 가장 흔한 원인을 지금 닫는 자리 |
| R5 | 게이트 저항 | 분포 RC: R_g ∝ R□_poly × finger_w / L / nf (분포 계수는 접촉 방식에서 나오는 유도값이지 경험 상수가 아님) | poly R□ **출처 미확인** | 기록만(출처 확정 전). 전기 효과(잡음·극)는 R7 결정에 따름 |
| R6 | S/D·공통 넷 배선 저항 | R = RPERSQ × 길이/폭, 길이 = 배치 좌표 HPWL, 폭 = R4가 정한 폭 | tlef + `ly_floorplan` | 기록(전압 강하 = R × ID는 DC 양 -- 원칙 3, 판정하려면 새 필드·DC 반영 필요 → Q7) |
| R7 | 신호 마디 기생 C | C = CPERSQDIST × 폭 × 길이 + EDGECAPACITANCE × 2 × 길이, 마디 = 넷. 극점·PM 영향의 **방향**(그 넷이 지배 극/비지배 극 마디인지)은 엔진 AC 필드에서 읽는다 | tlef + `ly_floorplan` + 엔진 극점 필드 | 기록 또는 AC 반영(3.8, Q7) |
| R8 | dummy·guard ring 자리 | 행 끝 dummy는 이미 판정 축 면적에 있다(`dummy_w_m`). guard ring은 PDK 양이 선언되지 않았다(tap 띠만 있음, `tap_w_m`) | 기존 PDK 양 | dummy·tap 판정 축 그대로, guard ring은 선언 생기면 (Q9) |

결론 (원칙 11): R1~R4·R6·R7은 **이미 고정된 PDK 출처(tlef) + 엔진 필드**로 상수 없이 계산할 수 있다(역할 이름 선언 추가 필요). R5는 출처 미확인이라 지금은 상수 없이 할 수 없다 → 출처를 확인하기 전에는 계산하지 않는다(멈춤). 판정은 **R4(EM)만 fail-closed 물리 관문**으로 권고하고, R2는 판정 축 편입 여부를 묻는다(Q3). 나머지는 기록 또는 Q7에 따른다.

### 3.7 finger 확정 규칙 (추가 요구 (2))

1. **정본** = MOD8 수렴 스냅샷의 `RealizedGeometry`(소자별 nf, finger_w, 행 확산 기하). 이것이 SPICE 합격 기하이기도 하다(LY8).
2. 상세 배치·배선 단계(뒤의 layout agent)는 이 값을 **입력으로만 받는다**. 바꿀 수 있는 것은 좌표·배선뿐이고, 행 소속·nf·finger_w·접기는 바꿀 수 없다.
3. **검사**: 그 단계 산출(추출 기하)의 (nf, finger_w, 확산 통계)를 정본과 비교한다. 다르면 sign-off 불가(fail-closed). 이미 있는 고정점 비교(`C/converge_point.py:101-103`, `realized_geometry` 동등)와 같은 정의를 쓴다(새 비교 정의 없음).
4. **재진입 경로**: 바꿀 필요가 생기면(예: 실제 배선에서 EM·채널 부족) layout agent는 finger를 고치지 않는다. 대신 `WRequest{device, W_new, nf, finger_w, reason=routing_em|routing_channel}`(LY3 레코드 그대로, reason 값만 추가)를 낸다 → MOD8 `converge_point`가 같은 front 점 스냅샷에서 레이아웃을 다시 놓고 LY7 재평가 → 통과하면 새 정본, 위반이면 `rejected_requests` → LY5 완화 판정 또는 키 제외 → INFEASIBLE.
5. **반복 상한**: 재진입은 새 상태(거부·요청 집합이 바뀜)이므로 K_max는 그 레이아웃에서 다시 센다. 같은 DC 상태로 돌아오면 주기 → NONCONVERGENT(기존 규칙). 무한 재진입을 막는 상한이 따로 필요한지는 Q8.
6. 3.6 R4를 이 단계에서 fail-closed로 두는 이유가 바로 4의 재진입 빈도를 줄이기 위해서다. R2·R6·R7을 기록만 하면 그 축 때문에 뒤에서 finger가 바뀔 위험이 남는다(아래 ⚠).

### 3.8 routing 기생을 손계산에 넣을지 (추가 요구 (3))

| 안 | 내용 | 물리 정합 | 손계산 속도 | graph | 정의 동일성(oracle) | ⚠ |
|---|---|---|---|---|---|---|
| (가) 엔진 metric 반영 | 레이아웃 블록 `ly_routing`(writer 하나)이 넷별 C_wire·R_wire를 쓰고, LY7 재평가의 AC 스탬프·DC(R×I)가 READS | 높음(PM·GBW가 배선 C를 본다) | 재평가는 원래 레이아웃마다 1회 → 커널 호출 증가 0, 스탬프 항만 증가 | 새 필드 1, 소비자 = 평가 커널(≥1) | oracle 넷리스트에도 같은 C·R 소자를 넣어야 한다. 아니면 엔진과 SPICE의 정의가 다르다 | ⚠ DEC-89 (5)·LY8(SPICE 기하 = finger·확산만) 개정 필요, ⚠ 레이아웃 전 사이징엔 배선이 없어 레이아웃 뒤 재평가에서 판정이 뒤집힐 수 있다(기록 대상) |
| (나) 판단 근거로만 | 3.6 값을 기록하고 AI·사람이 finger 판단에 참고 | 낮음(PM 위반을 못 잡는다) | 0 | 기록 필드(출력 전용 선언) | 해당 없음 | ⚠ 뒤 단계 finger 변경 위험이 남는다(요구 (2) 취지 미달) |
| (다) 물리 한도만 판정 + 기생 기록 | R4(EM)·트랙 수용은 fail-closed, C·R은 기록 | 한도 축은 높음, 기생 축은 낮음 | ≈0 | 판정 필드 1(EM 여유), 기록 필드 | 해당 없음 | ⚠ 기생에 따른 PM 이동은 SPICE(배선 추출 뒤)만 본다 |

권고: **(다) → (가) 2단계**. (다)는 상수 없이 바로 정의되고 요구 (2)의 가장 큰 원인(EM에 따른 finger 증가)을 닫는다. (가)는 oracle 넷리스트 개정(DEC-89 (5)·LY8)과 함께 해야 정의가 같아지므로 별도 card로 둔다.

### 3.9 MOD8·K_max·NONCONVERGENT·oracle과의 관계

- AI 계획은 수렴이 끝난 점 위에서 만든다. 적용은 **그 점의 다음 레이아웃 입력**이다(LY1: 기준점 = front 점 스냅샷) → MOD8 루프를 한 번 더 돈다. 계획이 W를 바꾸지 않으면(폭 키·접기·배치만) LY7 재평가 1회로 끝나고, `WRequest`를 포함하면 기존 루프를 탄다.
- K_max는 계획을 적용한 첫 레이아웃에서 다시 정한다(`w_loop_bound`, 새 상수 없음).
- 계획 적용 결과가 NONCONVERGENT·INFEASIBLE이면 그 점의 계획을 거부하고 코드 기본 결과를 유지한다. 근거: 기본 결과는 이미 수렴·봉인된 점이다. 이것이 우회인지는 Q5에서 확인한다.
- oracle: 넷리스트 기하 = 수렴 스냅샷 (finger_w, nf, ad/as/pd/ps)(LY8). 계획이 행을 바꾸면 확산 기하가 바뀌고 LY7 재평가가 접합 C를 다시 반영한다(DEC-91). 배치 좌표는 지금 oracle 소비자가 없다(3.8 (가)를 하면 생긴다).
- 판정 축 재필터(`C/refilter.py`)·교대 K_alt(`C/alternation_bound.py`)는 계획을 적용한 면적을 그대로 쓴다(새 정의 없음).

---

## 4. 기존 결정과의 관계 (작성자 자기 점검 -- 독립 점검 필요)

| 결정 | 관계 | 판정 |
|---|---|---|
| Q8 (vi) / LY10 / DEC-93 (4) | box 비는 기록만 하고 목적은 판정 축 면적이다. 사용자 제안의 "box형 배치"를 목적으로 쓰면 이 결정을 바꾸는 것이다. | 혼합안은 면적 목적을 유지(일치). "box를 목적에" 넣는다면 **원래 취지와 다름** → Q6 |
| LY2 | "finger_w·nf·행은 레이아웃이 고른다". 레이아웃 = MOD7(코드). AI가 선택을 제안하는 것은 행위 주체를 바꾸는 것이다. | **원래 취지와 다름(표지)** -- 채택하면 LY2 문언 개정 |
| LY3 / A-140 / A-141 | 요청 레코드 `{device, W_new, nf, finger_w, reason}`를 그대로 쓰고 reason 값(`floorplan`, `routing_em`, `routing_channel`)만 더한다. 코드는 `W_old_m`·`group` 칸도 갖는다(`L/contract_output.py:110-120`). | 일치(reason 집합 확장은 계획 개정) |
| LY5 | 차동쌍 완화 판정은 MOD8 몫. AI가 완화를 직접 정하지 않는다. | 일치(AI 후보에 '완화' 없음) |
| LY7 / DEC-89 (2) | 레이아웃 결과마다 재평가 1회. 계획 적용도 같다. | 일치 |
| LY8 / DEC-89 (5) | SPICE 기하 = finger·확산. 3.8 (가)는 배선 C·R을 더한다. | (가)를 택하면 개정 필요 |
| LY9 / DEC-93 (3) | 자동 접기·재구성 + matching 재판정. AI 접기 제안도 같은 판정. | 일치 |
| LY11 / DEC-93 (6)(7) | 복사 floorplan 리터럴 값 변경은 A_L 민감도 실측 + 승인 뒤. packer 순서 입력(배치 순서)을 더하는 것은 값 변경이 아닌 입력 추가라 재작성 범위 표 대상이다. | 조건부(design 범위 표 필요) |
| O-186 (L2) / LY1 | 보존량 (ID, VGS, L). 폭 키 변경은 W_need로 실현되고 재평가가 판정한다. | 일치 |
| DEC-91 (접합 기하) | 행 변화 → 확산 기하 변화 → 재평가. A-140이 DEC-91의 BSIM 식 전제를 재점검 입력으로 올려 두었다. | 일치, A-140 열린 항목과 상호작용(접합 C 정본 자리가 바뀌면 3.6 R7 기생 C 정의도 같은 원칙으로) |
| DEC-105 (2) | 레이아웃 **전** 손가락 선택 함수 하나. 혼합안은 레이아웃 **뒤**만 건드린다. | 일치(레이아웃 전 선택 함수는 그대로). 단 A′가 `finger_geometry` 선택 규칙을 재작성할 때 '같은 선택 함수 하나'(LY2 v6.38.2 문언)와 모순되지 않는지 design에서 대조 필요 |
| DEC-79 (b) | 판정 축 = 레이아웃 면적. 3.6 R2 채널 폭을 넣으면 판정 축 정의가 바뀐다. | Q3 (원래 취지와 다름 후보) |
| O-173 E-0/E-1 | E-0 물리 관문은 fail-closed. R4 EM을 E-0 꼴 관문으로 두는 것은 확장이다. E-1: 판정은 코드·oracle이고 AI는 판정하지 않는다. | 일치(R4 관문 추가는 계획 개정) |
| O-200 | 물리 정합 > 손계산. AI는 손계산 경로에 넣지 않는다(루프 밖). 3.8 (가)는 물리 정합을 높인다. | 일치 |
| O-197 | AI 출력에 PDK 값 없음. 배선 양은 역할 이름 선언. | 일치(선언 추가 필요) |
| O-229 | LA-1 전 새 인프라 금지. A-124: `converge` 비test 호출처 0, LA-1 측정 경로 밖 → 이 작업은 LA-1을 막지 않는다. | **LA-1 뒤**로 둔다(단계안) |
| O-238 | 원 결정·card 취지 유지. 혼합안은 LY 규칙을 번복하지 않고, 개정이 필요한 문언(LY2·LY8·DEC-79)은 질문으로 올린다. | 일치 |
| O-244~O-246 | 측정 구성 원 넷·LUT 열 정의·D1~D7. 레이아웃 뒤 재평가 꼴을 공유하고 직접 충돌은 없다. D5(C 열 폭, 레이아웃 뒤 접합 보정)는 3.8 (가)·R7과 같은 축. | 상호작용 기록(D5 결정 뒤 R7 정의 정렬) |
| A-124 | 레이아웃 뒤 루프는 LA-1 경로 밖. 레이아웃 입력 기준점 = 사이징 점. | 일치(3.9) |
| A-139 | 새 집합·갈래 점검. "계획 있음/없음" 갈래 → 코드 기본 계획도 같은 꼴로 써 갈래를 0으로. reason 값 3개 추가는 집합 확장이다. | 조건부(갈래 0 꼴 채택 시) |
| 원칙 9 | 만들면 대체. AI 계획 입력은 ①②④ 코드 기본 선택을 대체하는 정본 입력이다. A′는 `finger_geometry` 규칙을 대체하고 옛 규칙을 지운다. | 일치(설계 시 삭제 목록 필요) |
| 원칙 10 | AI 실패 시 코드 기본안 = 우회인가. 3.5·3.9의 근거로 '제안 없음'으로 정의. | **불확실 → Q5** |

⚠ 이 표는 작성자 자기 점검이다. 원칙 26 ⑩(결정 간 모순 점검)은 점검자 ≠ 작성자 기록이 필요하므로 **아직 없음**.

### 원본 참고 사실

- Jespers & Murmann 2017 부록 3 (`C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/references/gmid_sources/jespers_murmann_2017/extracted/layout-dependence.pdf`)
  - 315쪽: 사이징 때는 레이아웃을 모르므로 설계자가 소자마다 finger 폭·수를 정해 SPICE에서 1차 LDE를 본다. 레이아웃 뒤 추출은 "verification only"이고 "should not lead to a re-sizing". LUT는 고정 기준 레이아웃으로 만든다.
    → 원본 흐름은 finger 분할을 **사이징 단계 입력**으로 확정하고 뒤에서 바꾸지 않는다. 추가 요구 (2)의 'finger 확정'과 같은 방향이다. 우리 엔진의 W_request 루프(LY3)는 원본보다 한 단계 더 나간 승인 결정이다.
  - 316쪽: 기준 레이아웃 W = 10 µm, 5 finger × 2 µm. finger 폭은 게이트 저항(넓을 때)과 측벽·fringe 기생(좁을 때) 사이 절충이고, '1~3 µm 최적'은 65·90 nm RF 기준 문헌값이다.
    → 경험값이라 엔진 상수로 쓰지 않는다(원칙 13). 게이트 저항이 finger 폭의 함수라는 물리만 R5에 쓴다.
  - 317쪽 식 (C.3.1): n_f = max(round(W/2µm), 1). finger 폭은 W에 따라 톱니 모양으로 움직인다.
  - 318쪽: W > 2 µm에서 gm/ID·gm/gds·gm/Cgg 오차 ≲ 1.5 %. 최소폭에서는 gm/Cgg 오차가 40 %까지 간다.
  - 319쪽: gm/gds는 긴 채널 약반전에서 10~20 %.
    → 우리 엔진은 폭 슬라이스별 LUT(LY2, DEC-105 (2))라 원본의 고정 기준폭 근사보다 1차 효과를 직접 반영한다. 행 폭 키가 바뀌면 LY7 재평가가 판정한다(일치).
- 저장소 `skills/analog-gmid-design/references/stick-diagram-euler-layout.md`
  - §1 (19~40행): layout 판정 결과를 sizing으로 되먹이는 루프가 전제다.
  - §4.2 (679~725행): 세로 스택(행 폭 통일, finger_w 자유) 대 가로 배치(finger_w 통일)의 선택은 숫자로 재확인해야 한다(NGCC 행 폭 비 131:1 사례).
    → ① 폭 키 선택이 행 길이를 직접 정한다는 근거. 코드가 지금 이 선택을 면적 무관하게 하는 것이 A′ 대상이다.
  - §8.3 (976~996행): finger_w를 바꾸면 그 폭에서 전류를 재확인해야 한다(우리 LY1·LY7이 처리).
  - §8.4 (998~1029행): box PASS여도 그 finger_w가 PDK에서 실현되는지는 별개다(우리는 특성화 폭만 쓰므로 해소).
  - §8.5 (1031~1057행): FAIL을 받아들일 때 필요한 분할 행 수를 숫자로 남긴다(우리 `FoldAttempt` 기록이 해당).
  - §9.5 (1143~1167행): 기하 재시도는 비싼 sizing 탐색과 분리한다.
    → AI를 수렴 루프 밖에 두는 근거와 같다.

---

## 5. 원래 취지와 다름 · 단계안

### 5.1 원래 취지와 다름 (채택 시 바뀌는 결정·문언)

1. LY2 "레이아웃(MOD7 코드)이 finger_w·nf·행을 고른다" → 코드 후보 + AI 선택 제안.
2. 사용자 제안 "box형 배치" ↔ Q8 (vi)(box 비 기록만). 혼합안은 면적 목적을 유지하므로 box를 목적으로 하지 않는다(사용자 표현과 다름 -- 표지).
3. 사용자 제안 "AI가 필요하다고 판단하면 피드백" → 혼합안은 AI 판단이 아니라 **코드 판정 축 개선**이 채택 기준이다(AI는 제안만 함).
4. (3.6 R2 채택 시) DEC-79 (b)·LY10 판정 축에 배선 채널 폭을 더한다.
5. (3.8 (가) 채택 시) LY8·DEC-89 (5) SPICE 기하에 배선 C·R을 더한다.
6. LY3 reason 집합 확장(`floorplan`, `routing_em`, `routing_channel`). 뒤 단계 finger 변경 금지 + 재진입 규칙은 새 규칙이다.
7. 원본(Jespers 315쪽)은 레이아웃 뒤 재사이징을 하지 않는다. 이미 승인된 LY3에 재진입 경로가 하나 더 붙는다.
8. 1차 검토 정정 3건(1.2): 자동 접기, packer 값의 물리성, 행 폭 정의.

### 5.2 단계안 (모두 LA-1 + O-225 재점검 뒤 -- O-229 4)

| 순서 | card 후보 | 내용 | 시점·조건 |
|---|---|---|---|
| S0 | (실측만) | library 회로 n/N에서 ① 폭 키를 바꿀 때의 판정 축 면적 변화폭, 행 그룹 수 × 폭 키 수(조합 크기, LUT 폭 슬라이스 32개 -- `assets/lut_v2_location.json` 설명), front 점당 레이아웃 호출 수를 잰다. 이 값이 A′와 AI가 각각 얼마나 이득을 내는지 정한다. | LA-1 뒤. **미측정** -- 권고 전 필수(원칙 22 ⑤) |
| S1 | LY-A′ | 폭 키 선택을 `compose_rows` 면적 탐색과 한 블록으로 재작성(writer 하나), 옛 `finger_geometry` 선택 규칙 삭제 | S0에서 면적 이득이 ΔA_tie 이상일 때 |
| S2 | LY-R1 | 배선 역할 이름 PDK 선언(tlef 출처) + 3.6 R4 EM fail-closed + R2·R6·R7 기록 필드(출력 전용 선언) + 3.7 finger 확정·재진입 규칙(reason 확장) | 계획 개정(LY3·E-0) 뒤 |
| S3 | LY-P1 | 계획 입력 필드 `ly_plan`(코드 기본 계획 = 같은 꼴, 갈래 0) + 검증 경로 + 재생 test | Q4(정본 자리) 승인 뒤 |
| S4 | LY-AI1 | AI 제안자 연결(수렴 뒤 점당 1회), 기록 파일 = 선언 입력, record_id | S3 뒤, S0/S1에서 코드 탐색 공백이 실측됐을 때만 |
| S5 | LY-R2 | 3.8 (가) 배선 기생 엔진 반영 + oracle 넷리스트 정의 정렬 | O-246 D5·A-140 재점검 결론 뒤 |

---

## 6. 사용자 결정 질문 (초안)

- **Q1 진행 여부·시점**
  - (가) LA-1 + O-225 뒤 S0 실측부터, A′ 먼저 **(권고)**
  - (나) 지금 착수(⚠ O-229 4 위반)
  - (다) 보류
- **Q2 AI 호출 자리**
  - (가) 수렴 뒤 front 점마다 1회 **(권고)**
  - (나) 회로마다 1회 크기 무관 구조 의도(크기가 바뀌면 후보 id가 자주 무효가 된다)
  - (다) 레이아웃 호출마다(⚠ 원칙 1·결정성)
- **Q3 배선 채널 폭(R2)을 판정 축 면적에 넣을지**
  - (가) 넣는다: DEC-79 (b)·LY10 개정, 원래 취지와 다름
  - (나) 기록만
  - 권고 = (가). 근거: 배선 영역은 물리 면적이고 기록만 하면 AI의 배선 고려가 판정되지 않는다. 단 S0 실측 뒤 확정.
- **Q4 AI 계획의 정본 자리**
  - (가) `LayoutInput` 입력 필드(writer `ly_input`), 응답 파일 = 선언 입력·record_id **(권고)**
  - (나) 실행 기록(⚠ 원칙 7)
  - 계획 N3.3에 '선언 입력 부류' 문언 추가가 필요하다(S-7).
- **Q5 AI 응답 실패·계획 거부 시 코드 기본 계획 사용**이 원칙 10 우회가 아닌지
  - 권고 = '제안 없음' 정의로 허용하되 거부 사유는 반드시 기록. 독립 점검 필요.
- **Q6 box 모양을 목적에 넣을지**
  - (가) Q8 (vi) 유지, 면적만 **(권고)**
  - (나) box 비를 목적에 추가(Q8 (vi) 재검토, O-208)
- **Q7 배선 기생을 손계산에 넣을지 (3.8)**
  - (다)→(가) 2단계 **(권고)**
  - (나) 판단 근거로만(⚠ 요구 (2) 미달)
  - (가) 즉시(⚠ oracle 정의 불일치 기간)
- **Q8 finger 확정 뒤 변경 규칙 (3.7)**
  - 상세 배치·배선 단계의 finger 변경 금지 + 불일치 fail-closed + `WRequest{reason=routing_*}` 재진입 **(권고)**
  - 재진입 횟수에 별도 상한을 둘지: 권고 = 두지 않고 기존 주기·K_max 규칙, 새 상수 없음.
- **Q9 PDK 선언 추가**
  - 배선층 피치·폭·시트 저항·면/변 용량·전류밀도(tlef), guard ring 양, 게이트 poly 시트 저항(출처 미확인)을 역할 이름으로 선언할지
  - 권고 = tlef 양은 S2에서 선언하고, poly R□는 출처 확인 전 계산하지 않음.

---

## 부록: 실측 출처 (이 문서 작성자가 직접 연 파일)

- 코드: `L/run.py`, `L/finger_candidates.py`, `L/finger_geometry.py`, `L/w_tolerance.py`, `L/slice_density.py`, `L/rows.py`, `L/row_euler.py`, `L/row_fold.py`, `L/box_shape.py`, `L/floorplan.py`, `L/floorplan_pack.py`(1-80, 324-432, 475-530), `L/diffusion.py`, `L/area_tie.py`, `L/contract_output.py:110-132`, `L/contract_input.py:43,108-222`, `L/pattern_select.py:1-30`, `C/converge_point.py`, `C/converge.py:1-40`, `C/w_loop_bound.py`, `C/alternation_bound.py`, `C/key_exclusion.py`, `C/effective_placement.py`, `C/place_layout.py`.
- grep 실측: `converge` 비test 호출처, `run_gmid_design_pipeline` 정의 0, `net_weights` 사용처(floorplan.py 미전달), 엔진 안 AI 호출 코드 0.
- 계획 `P` N3.17 LY1~LY12(1100-1117행), DEC-79·89·91·93·105 행. design `wt/_drafts/engine/design_mod7_layout.md` §0·§2.2·§3·§8.
- 결정: `wt/_drafts/user_decisions.md` O-186·O-200·O-229·O-238·O-244·O-245·O-246 행. `wt/_drafts/la1_auto_decisions.md` A-124·A-139·A-140·A-141 행.
- PDK: `assets/sky130_pdk_decl.json`(tlef 출처 8·106행, 선언 양 목록), `/c/pdk/sky130_fd_sc_hd/tech/sky130_fd_sc_hd.tlef` 59-260행.
- 원본: 위 PDF 315~321쪽, `references/stick-diagram-euler-layout.md` 해당 절.
- 미측정(권고 전 필수): S0 항목 전부, poly 게이트 시트 저항 출처, front 점당 실제 레이아웃 호출 수.
