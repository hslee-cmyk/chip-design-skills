# U-114 -- card LA-1 선행 근거 재확인 (DE-1 및 그 밖의 선행 card)

- 작성: 분석 agent, 2026-10-24. 파일 수정 없음(이 증거 파일과 `wt/_scratch_u114/` 임시 사본만).
- 대상 판:
  - 계획: master `56dd1f8a`의 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(v6.37 승인본, 2347행). `wt/plan-v637` worktree는 조사 중 정리되어 없어졌다. 줄 번호는 plan/v637 HEAD와 같다(1201·1833·2262행 대조로 확인). 사본 `wt/_scratch_u114/plan.md`.
  - 옛 판 대조: `cfa0034b`(v6.36) 1827행.
  - design 41: `wt/integ-it12/docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md` v1.14.1(`wt/design-v1131`은 병합 뒤 정리되어 없음; integ/it12 `34585913`이 design v1.14.1 병합을 포함).
  - 엔진 as-built: `wt/integ-it12/skills/analog-gmid-design/gmid_engine`(integ/it12 HEAD `34585913`).
  - 다른 계획: master의 `headroom-chain.plan.md`(v0.7.8), `graph-consumption.plan.md`(v0.13).
- 사용자 결정 O-125(`_drafts/user_decisions.md` 869행): "IT-2c 뒤 바로 LA-1 (권고) -- U-114를 실측해 DE-1 선행이 꼭 필요한지 확인, 필요 없으면 LA-1을 IT-2c 바로 뒤로 앞당김. 순서 변경은 계획 개정(v6.38)·검증."

## 0. 결론

1. **DE-1 선행 근거는 남아 있지 않다.** 계획에 적힌 유일한 근거(v6.36 1827행 "DE-1(슬루 방향 전류 -- 블록 전류 슬루 하한이 그 정본을 읽음, 같은 양 두 계산 금지)")는 O-122로 소멸했다(계획 DEC-71 (3) 270행이 이미 "'슬루 하한'은 v6.37 O-122로 없음"). 다른 겹침(파일·graph 필드·함수)을 전수로 봤고 선행 근거가 되는 것은 없다(§2). → DE-1을 LA-1 선행에서 뺀다. U-114 닫음 권고.
2. **'IT-2c 바로 뒤'는 문자 그대로는 성립하지 않는다.** LA-1은 integ/it12 통합 브랜치(IT-2c와 IT-2d 사이)에 들어갈 수 없다 -- IT-1 + IT-2는 master 병합이 한 번(1537행, O-19 (2))이고, LA-1은 U17 ②와 자기 통합 병합(LA-Q5, 1834행)이며, 동작 변경 card끼리는 같은 통합 병합에 넣지 않는다(1211행·O-38 (3)). LA-0 기준선도 'base = LA-1의 실제 base'(1817행)다. 그래서 가장 이른 자리는 **IT-1 + IT-2 통합 병합(IT-2d·IT-2e 포함) 직후**다. design 개정(S-7)은 지금 병렬로 시작할 수 있다.
3. **DE-1 말고도 아직 유효한 선행이 셋 있다**: UB-1(+NL-1 같은 통합 병합; 사용자 결정 O-38 (2) "LA-1 앞 별도 card"), HC-S(`sat_threshold` 정본 함수 -- as-built에 없음, graph 규칙 1·6), EO-1(LA-1 범위 안 U17 ② front 판정 배선이 EO-1 생산자를 부름 -- 코드 의존). 이 셋은 모두 아직 master에 없다(§1). 그래서 O-125의 '바로 뒤'를 이루려면 이 셋에 대한 결정이 따로 필요하다(§4 대안).
4. **겹침만인 선행 셋**(FX-1, GC-9, HC-1)은 순서를 뒤집을 수 있다 -- 파일 겹침이거나 LA-1이 그 card의 함수를 '쓰는' 자리(범위 11)를 그 card로 넘기면 된다. HC-1은 이미 자기 범위에 '층 0 거르기(U-H9)'를 갖고 있다(headroom-chain 517행).

## 1. LA-1 선행 card 전수와 원문 근거

출처: 계획 1201행(N6.1 LA-1 행), 1833행(N6.14 '선행 card'), 1832행(착수 조건), 1834행(U17 ②), 1824·1832행(완료 시점).

| # | 선행 card | 원문 근거(줄) | 상태(실측) |
|---|---|---|---|
| P1 | XRUN-F1 card B | 1833 "블록 결과 색인 -- 조립 graft가 쓴다" | **병합됨**(master `138a6db3`, `E/search/s3_index.py` 있음) |
| P2 | headroom-chain HC-S | 1833 "`sat_threshold` 정본 -- VDS 배분 문턱"; 1773(F-LA9) "엔진에 아직 없다(`git grep` 0)"; 1828 완료 조건 7 "포화 문턱 `sat_threshold` 외 계산 0"; 1801 점검표 '포화 문턱 = `sat_threshold` 정본 하나' | 미병합. integ/it12 `git grep sat_threshold\|dc_sat_v` 0. headroom-chain H-12(634행) HC-0 → HC-D → HC-S 순, HC-0·HC-D 병합 기록 없음 |
| P3 | UB-1 | 1833 "블록 국소 모델 U9 하나로 통합 -- O-38 (2)"; 1784 범위 4 "**LA-1 앞 별도 card UB-1**"; 1878 O-38 (2) 원문 "LA-1 안이 아니라 LA-1 앞 별도 card로(NL-1과 함께)" | 미병합. `block_local_gain`(`E/metrics/block_model.py:98`)과 `block_gain_model_of`(`block_gain_model.py:132`) 둘 다 있음 |
| P4 | IT-1·IT-2 | 1833 "입력 포트 창·W4 y 키 -- 조립의 입력 CM 처리" | IT-1·IT-2a·IT-2b PASS(integ/it12), IT-2c 진행, IT-2d·IT-2e 남음, master 병합 전 |
| P5 | DE-1 | 1833 "옛 근거 '블록 전류 슬루 하한이 슬루 방향 전류 정본을 읽음'은 v6.37 O-122로 슬루 하한이 없어져 소멸 -- 다른 겹침이 선행 근거로 남는지 착수 때 재확인 -- N7.2 U-114"; 옛 판 v6.36 1827 "DE-1(슬루 방향 전류 -- 블록 전류 슬루 하한이 그 정본을 읽음, 같은 양 두 계산 금지)" | 미착수. 착수 조건 (iii) U-115 = 사용자 보류(O-123), EO-1 병합 선행(1643) |
| P6 | FX-1 | 1833 "근거 = 파일 겹침 -- `layer0_center` 사다리·`start_intervals.py`; FX-1 고정점은 층 0 무동작 회로·조립 실패 경로의 출발점에서만 돌므로 층 0 손계산 경로의 입력 출처는 아니다"; 1683 "FX-1은 LA-1의 선행이므로 FX-1 → U17 ②·LA-1" | 미병합 |
| P7 | NL-1 | 1833 "`_helpers_nodal`·`block_model` 파일 겹침 -- UB-1과 함께"; 1202(N6.1 UB-1 행) "NL-1과 같은 통합 병합" | 미병합 |
| P8 | headroom-chain HC-1 | 1833 "R-1′ 관계식 거르기 -- 범위 11"; 1791 범위 11 "HC-1이 만든 R-1′ 관계식 거르기를 같은 함수로 적용 ... 선행 card = HC-1" | 미병합(선행 HC-S·XRUN-F1 card C·IT-1·EO-1) |
| P9 | graph-consumption GC-9 | 1833 "`current_cone` 소비자 → `dc_current_basis`, 파일 겹침 `layer0_center`·`fd_jacobian`"; 1215 "GC-9 → LA-1 순서(LA-1이 그 정본 위에서 층 0 경로를 다시 쓴다)" | 미병합(`layer0_center.py:160, :185, :196`·`fd_jacobian.py:50`이 아직 `current_cone`을 읽음) |
| P10 | EO-1(완료 판정 선행) | 1833 "완료 판정 선행 EO-1(SPICE 다리 -- 병합 선행 아님, N6.3 (iv))"; 1834 "LA-1과 함께 남는 U17 ② 몫은 front 판정 배선(front 점을 EO-1 생산자로 oracle에 넣고 결과를 front 판정에 쓰는 자리)" | 미병합(OP-3도 미병합; design만 병합 `3e2e7606`) |
| (완료) | ME-1 | 1201 "완료는 ME-1 뒤에만"; 1824 완료 조건 4 | 완료 시점 조건 -- 병합 순서와 무관 |

## 2. DE-1 겹침 전수 (판정 방법: 파일·함수·graph 필드)

### 2.1 DE-1이 고치는 것(계획 N6.8, 1609-1672행)

- 파일: `E/metrics/ls_swing.py`(자체 제약계 삭제), `ls_fields.py`(σ 경계 입력·β/σ/κ·슬루 칸 삭제, 방향 전류는 U-115), `offset_systematic.py`(삭제 → V_id* writer), `offset_analysis.py:76`(A_dm → A_dc, 갈래), `metrics_aux.py`, `aux_types.py`, `verified_by.py`, `pending_metrics.py`, `_helpers_view.py`, `ss_evaluate.py`, `E/search/ls_constraints.py`(슬루 행 삭제·피크 행 정리), `E/metrics/CONTRACT.md`, test 다수. 소비자 표에 `E/search/iv_headroom.py`(읽기만), `E/sizing/block_columns.py`·`input_window.py`(1641행).
- graph 필드: `node.dc_window_def`(정의 창, writer = IT-2c 측정 구성 블록에 정의 기준 추가), 출력 창 별도 필드(이름 design), V_id*(DEC-23 (나′)), A_dc 갈래, 방향별 전류(U-115 미결). `node.dc_window`(θ 프레임 탐색 창)는 "`block_columns.saturation_rows` 현행 식"(1632행 (a)(ii)) -- **DE-1이 바꾸지 않는다**.

### 2.2 LA-1이 고치는 것과 읽는 것(N6.14, design 41 §5)

- 고치는 파일: `E/search/layer0_center.py`, `find_front.py`, `start_points.py`, `search/CONTRACT.md`, `_module_map.py`, `E/sizing/size_and_seal_local.py`(+ `local_values.py`), 새 층 0 모듈(design 41 §5), U17 ② 분할·graft·S3 색인·층 0 필드.
- 읽는 것: `dc_current_basis`(있음 -- `E/sizing/current_basis.py`), `sat_threshold`(없음), U9 블록 국소 모델, 커널 쓰기 계획 W0~W4, 평가 커널 결과(봉인·제약 판정·`ss` 스냅샷 MNA 값), LUT, A_eff(LR6 L 하한).
- design 41 §5(843-1440행)에서 `swing|icmr|ls_|dc_window|block_columns|input_window|offset|slew|iv_headroom|ls_fields` grep: §5.3.6 163-164행(= 1005-1006행 부근)의 `block_columns.py` `k_max` 언급은 **인용(읽기 참조)**, 그 밖은 슬루 하한 2곳뿐(아래 G5).

### 2.3 겹침 후보별 판정

| # | 겹침 후보 | 확인 | 판정 |
|---|---|---|---|
| G1 | 블록 전류 슬루 하한이 DE-1 슬루 방향 전류를 읽음(옛 근거) | 계획 DEC-71 (3) 270행 "'슬루 하한'은 v6.37 O-122로 없음"; DE-1 (d) 엔진 슬루 몫 삭제(1635행); as-built `layer0_center.py:7` "슬루 선언은 쓰지 않는다", 층 0·출발 구간 파일 `slew`·`슬루` grep 0 | **(ii) O-122로 소멸** |
| G2 | 층 0이 DC 동작 범위 필드(`ls_fields`·`ls_swing`·`dc_window`·`dc_window_def`·출력 창)를 READS | `layer0_center.py`·`find_front.py`·`start_points.py`·`size_and_seal_local.py` import에 metrics ls/offset 계열 0; design 41 §5 grep 0; LA-1 범위 12(1792행)는 "추가 호출 0 -- 그 점의 커널 평가가 쓴 측정 구성 판정 창 값". 엔진 전체에서 `ls_swing\|ls_fields\|offset_systematic\|ls_constraints\|offset_analysis`를 부르는 search 층 파일은 `kernel.py`(:33, :156)와 `ls_constraints.py`뿐 | **(iii) 겹침 아님** -- 층 0은 그 필드를 쓰지 않는다 |
| G3 | 조립점·수리점의 평가 커널 판정(LA-1 범위 3)에 DE-1이 바꾸는 행(`swing_out_v`, `offset_sys_mv`, `load_peak_amp` 피크 행, 슬루 행 삭제)이 들어감 | `kernel.py:156-158` `rows = seal_rows + _spec_rows + ss_rows + ls_rows` | **(iii) 결과 결합이지 선행이 아님.** 순서를 바꾸면 나중 card의 변화표에 앞 card 효과가 들어간다(각 card base = 병합 직전 master, O-34 (1)·IT-Q3 (가)). 같은 통합 병합에만 넣지 않으면 원인 귀속은 깨지지 않는다(OS-2 규칙 1211행과 같은 꼴) |
| G4 | B80 실측 IIS 행 중 DE-1 metric | B80 `out/trace_lib_*.jsonl` 행 이름 집계: 'offset'은 대부분 `offset_excess`(σ 구조 가드, `metrics_aux.py:194` → `offset_analysis`). DE-1 (c)의 A_dm → A_dc는 차동 입력 회로에서 비트 동일(1634행, 갈래 미발동 시). `swing_out_v`는 nmcnr 층 0 점 위반 행 | **(iii)**. 단 O-125 새 완료 조건(front ≥ 1)을 LA-1 base(as-built `ls_swing`)에서 재면, DE-1이 나중에 `swing_out_v` 값을 바꿀 때 front가 다시 변할 수 있다 -- DE-1 변화표의 원인 항목(위험 기록, 선행 근거 아님) |
| G5 | design 41 §5.3.1 892행 '블록 전류(KCL·선언·슬루 하한)', §5.3.3 924행 S 행 «ID ≥ I_slew» | design v1.14.1에 남음. recheck8(`plan_v637_recheck8.md` 104행) 정정 목록 3번(41 892·924행), O-124 "13곳은 후속 정정 ... DE-1 전에 따로 승인"(user_decisions 867행) | **(ii) 계획상 소멸, design 문장만 남음.** LA-1이 DE-1보다 먼저 오면 이 두 줄은 LA-1 design 개정(착수 조건 (1)) 전에 고쳐야 한다 -- O-124의 'DE-1 전에'를 'LA-1·DE-1 중 먼저 착수하는 card 전에'로 |
| G6 | σ 입력 환산 A_dm → A_dc(DE-1 (c))가 LR6 L 하한(LA-1 범위 1)에 들어감 | LR6(645행) 하한 = A_eff(게이트 환산, `E/search/iv_matching_l.py:6-9`, `E/lut/mismatch_sigma.py:11`), σ 목표 = 문턱/k. A_dm·A_dc를 쓰지 않음 | **(iii) 겹침 아님.** 커널 offset 요구 판정 값은 단일 입력 회로에서 바뀜(값 없음 → 값) -- G3과 같은 결과 결합 |
| G7 | 방향별 최대 전류(U-115)를 층 0 '블록 전류(KCL·선언)'가 읽음 | 270행 블록 전류 = KCL·선언(슬루 하한 삭제). 층 0 전류 정본 = `dc_current_basis`(점검표 1799행). `ls_fields`는 피크 행 소비자만(1635행 '남기는 것' (나)) | **(iii) 겹침 아님** |
| G8 | 파일 겹침 | 공통 파일: `_module_map.py`(서로 다른 행), `search/CONTRACT.md`(LA-1이 다시 쓰는 S-4 문단 717행 '슬루 하한 전류'; DE-1은 `ls_constraints` 행 절) -- 문서 텍스트 충돌만. `block_columns.py`는 LA-1이 고치지 않음(design 41 §5.3.6은 인용만, **착수 때 확인**) | **(iii) 텍스트 겹침** -- 나중 card가 rebase |
| G9 | 범위 12 front 보고 창 이름(DE-1 전 `node.dc_window_cfg`, 뒤 `node.dc_window_def` -- IT-2 범위 2, 1530행) | 배선 자리는 `metrics_aux`(IT-2d·DE-1 몫). LA-1에 호출 자리 0 | **(iii)** -- 범위 12 문언만 '측정 구성 판정 창(DE-1 뒤 정의 창)'처럼 순서 무관하게 적으면 됨 |

**DE-1 결론**: 선행 근거 0. 순서를 바꿨을 때 생기는 일 = (a) 두 card 변화표의 원인 항목이 서로를 포함(결과 결합 G3·G4·G6), (b) `search/CONTRACT.md`·`_module_map.py` 텍스트 rebase(G8), (c) design 41 892·924행 정정 시점이 앞당겨짐(G5). 재작업 0.

## 3. 그 밖의 선행 card 판정

| # | 선행 | 겹침 확인 | 판정 | 순서를 바꾸면 |
|---|---|---|---|---|
| P1 | card B | 병합됨 | 충족 | -- |
| P2 | HC-S | 봉인 7은 문턱을 블록 안에서 바로 계산한다(`E/sizing/seal_saturation.py` `_row`: `tol_vdsat_table(...).at(op.L, op.vds)`, `sat - op.vds + 2.0*tol`) -- 꺼내 쓸 함수가 없다. 사본이 셋 더 있다(`derived_fns._tol_vdsat_max:117`, `_tol_vdsat_grid:49`, `search/_helpers_curves.tol_vdsat`; headroom-chain 516행). LA-1 VDS 배분 1단계 채움 = "VDsat + tol_VDsat(봉인 7)"(design 41 §5.3.4) | **(i) 유효** -- LA-1이 먼저면 문턱을 (가) 새로 계산(둘째 생산자, graph 규칙 1 위반) 또는 (나) 봉인 7에서 함수를 꺼냄(= HC-S의 핵심을 LA-1이 가져감, headroom-chain 범위 변경). 완료 조건 7(1828행)도 `sat_threshold`를 전제 | HC-S가 뒤에 오면 LA-1 호출 자리를 한 번 더 바꾼다(작음). HC-S는 tol 정의 변경(동작 변경)이라 층 0 결과가 HC-S 변화표에 들어감 |
| P3 | UB-1 | 층 0 블록 이득 = U9(범위 4). UB-1이 U9 규칙(미지수 노드·폐포·막다른 가지·FF 묶음)을 하나로 바꿈(1888행) -- U9 값이 바뀔 수 있음 | **(i) 유효 -- 사용자 결정 O-38 (2)** "LA-1 앞 별도 card". 뒤집으면 **원래 취지와 다름**(사용자 결정 필요) | LA-1 bin·front가 UB-1 뒤 다시 변함(UB-1 변화표에 층 0 항목), 원인 귀속은 따로 병합이면 유지 |
| P7 | NL-1 | UB-1과 같은 통합 병합(1202행). U9 ω → 0 극한이 `_helpers_nodal`/`dc_limit` 두 정의 중 무엇인지 NL-1이 정함(1691-1693행) | **(i) P3에 묶여 유효** | P3과 같음 |
| P4 | IT-1 + IT-2 | IT-1이 쓰기 계획(W4 y 뿌리, `input_tie` 제거)을 바꿈. design 41 §5 실측도 IT-1 쓰기 계획 모사로 했음(design 41 §5.12.5 1198행 부근 'measure_v4 -- §6.7-1a 쓰기 계획 모사'). IT-2b 커널 창 W4 뿌리, IT-2c `graph.ss_circuit`·`ss_nodal`(UB-1·NL-1이 쓸 자리) | **(i) 유효** | LA-1이 먼저면 IT-1 쓰기 계획 개정이 층 0 조립을 다시 고치고, IT-0 기준선·IT-2 변화표가 섞임 |
| P5 | DE-1 | §2 | **(ii)+(iii) -- 근거 없음** | §2 끝 |
| P6 | FX-1 | 파일 겹침(`layer0_center` 사다리, `start_intervals.py`). 계획 스스로 "층 0 손계산 경로의 입력 출처는 아니다"(1833행) | **(iii) 파일 겹침만** | FX-1이 LA-1이 남긴 무동작·조립 실패 출발 경로 위에 rebase. 1683행 "FX-1 → U17 ②·LA-1" 문언 정정 필요 |
| P8 | HC-1 | LA-1 범위 11이 HC-1 함수를 세 자리에서 부름(쓰는 의존). 거르기는 커널 전 거르기(효율·탈락 기록)이고 판정은 커널 봉인이 함 -- 정합 근거 아님. headroom-chain HC-1 범위(517행)에 이미 '층 0 거르기(U-H9)' 있음 | **(i) 범위 11에 한해 유효, 뒤집기 가능** -- 범위 11을 HC-1로 넘기면 선행 근거 소멸 | HC-1이 새 층 0 세 자리에 거르기를 배선(HC-1 범위 문언 '사다리 칸' → 새 층 0 세 자리, 다른 계획 개정) |
| P9 | GC-9 | 순수 리팩터링(graph-consumption 580행). `current_cone` 소비 자리(`layer0_center.py:160-196` `_current_centre`, `fd_jacobian.py:50`)는 LA-1이 남기는 무동작 회로 출발 경로·외층에 있음. 층 0 손계산은 `dc_current_basis`를 바로 읽을 수 있음(이미 있음) | **(iii) 파일 겹침만** | GC-9가 LA-1 뒤 파일에 rebase, 비트 동일 판정은 LA-1 병합 master에서. 1215행·graph-consumption 669행 'GC-9 → LA-1' 정정 |
| P10 | EO-1 | 1834행: LA-1이 함께 하는 U17 ② 몫 = "front 점을 EO-1 생산자로 oracle에 넣고 결과를 front 판정에 쓰는 자리" -- 생산자 함수가 없으면 이 코드를 쓸 수 없음. EO-1은 OP-3 병합 선행, (S4-나)면 IT-1 + IT-2 병합 뒤(1185행) | **(i) 코드 의존으로 유효**(계획은 '병합 선행 아님'이라 적었지만 front 판정 배선 몫에는 병합 선행) | LA-1이 먼저면 front 판정 배선을 EO-1(또는 뒤 card)로 옮겨야 함 -- LA-Q5(O-36 (4)·O-38 (3)) 범위 변경 |

## 4. 'IT-2c 바로 뒤' 성립 여부와 최소 선행 집합

- **문자 그대로(IT-2c와 IT-2d 사이)**: 불성립. 근거: 1537행 "넷 모두 ... 같은 통합 브랜치 ... master 병합은 IT-1과 함께 한 번(O-19 (2))", IT-2e는 "IT-2d 뒤, IT-1 + IT-2 master 병합 전"; 1834행 LA-1 = U17 ②와 같은 통합 병합; 1211행 동작 변경 card는 같은 통합 병합에 넣지 않음; 1817행 LA-0 base = LA-1의 실제 base.
- **실행 가능한 가장 이른 자리**: IT-1 + IT-2 통합 병합 직후. 그 사이(IT-2d·IT-2e 진행 중) 병렬로 할 수 있는 것: LA-1 design 개정(design 41 §5·design 40 §11 U15, 892·924행 슬루 정정 포함)과 design 검증·design↔계획 gap. LA-0은 병합 뒤.
- **최소 선행 집합**(원칙 위반 없이, 사용자 결정 뒤집지 않음): **IT-1 + IT-2 통합 병합, UB-1(+NL-1), HC-S, EO-1(front 판정 배선 몫)**. card B는 충족. DE-1·FX-1·GC-9는 뺌, HC-1은 범위 11을 HC-1로 넘기면 뺌.
- **IT-2 병합 바로 뒤에 LA-1을 두려면**(O-125 문언에 가장 가까움) 위 셋(UB-1·HC-S·EO-1)을 따로 풀어야 하고 셋 모두 '원래 취지와 다름' 또는 다른 계획 범위 변경이다(§5 안 C).

## 5. 대안 비교

| 칸 | 안 A: DE-1만 뺌(나머지 계획 그대로) | 안 B(권고): DE-1 뺌 + 겹침만인 FX-1·GC-9·HC-1 뒤집기, 유효 선행 UB-1(+NL-1)·HC-S·EO-1 유지 | 안 C: IT-2 병합 바로 뒤 LA-1(UB-1·HC-S·EO-1까지 뒤로) |
|---|---|---|---|
| 물리 정합 | 같음(커널 봉인이 판정) | 같음. 거르기(HC-1)가 없어도 커널 봉인이 판정 -- 정합 손실 없음, 커널 호출만 늘 수 있음 | 문턱을 봉인 7 식 그대로 쓰면 정합 같음. U9 통합 전 블록 이득으로 bin을 나눔(UB-1 뒤 값 이동) |
| design 단순성 | design 41 §5 그대로 | 범위 11을 HC-1로 옮김(LA-1 design 축소), FX-1·GC-9는 rebase만 | LA-1 design에 HC-S 핵심(정본 함수 추출)·EO-1 배선 분리가 들어가 커짐 |
| 재작업량 | 0. 단 LA-1 시점은 HC-0 → HC-D → HC-S → HC-1, OP-3 → EO-1, GC-9, FX-1을 모두 기다림(가장 늦음) | FX-1·GC-9·HC-1이 새 층 0 파일에 rebase(작음); HC-1 범위 문언 개정 | HC-S가 LA-1 호출 자리 재배선(작음), UB-1 뒤 층 0 값 재측정, front 판정 배선 이동 |
| 실측/근거 | §2 전수 | §2·§3 전수(FX-1 '입력 출처 아님' 1833행, GC-9 순수 리팩터링 gc 580행, HC-1 범위 hc 517행) | B80: 1차 원인 = 층 0 E10 미구현, 손계산 출발로 엔진 무수정 front 1 -- 앞당길 가치는 실측됨 |
| 원칙 | 위반 없음 | 위반 없음(graph 정본: LA-1이 `sat_threshold`·U9 정본·EO-1 생산자를 읽기만; 만들면 배선: 범위 11 함수 배선은 HC-1이 함수와 함께) | ⚠ 원칙 경고: graph 단일 정본 — `sat_threshold` 없이 VDS 문턱을 쓰면 둘째 생산자이거나 HC-S 범위를 가져가야 함 — 봉인 7 `seal_saturation.py` 인라인 계산·headroom-chain 516행. ⚠ 원칙 경고: 계획 우선(사용자 결정) — UB-1을 LA-1 뒤로 두는 것은 O-38 (2) "LA-1 앞 별도 card"를 뒤집음 — 계획 1878행. ⚠ 원칙 경고: 계획 우선 — front 판정 배선을 LA-1에서 떼면 LA-Q5(O-36 (4)·O-38 (3)) 범위가 바뀜 — 계획 1834행 |
| 원래 취지와 다름 | 없음 | 작음: FX-1 → LA-1(1683행)·GC-9 → LA-1(1215행)·HC-1 → LA-1 범위 11 순서 문언을 바꿈(작성자 기본안이던 순서, 사용자 결정 아님 -- 1215행 '작성자 기본안') | 큼: O-38 (2)·LA-Q5·headroom-chain HC-S 범위 |

**권고: 안 B.** DE-1은 선행 근거가 없으니 뺀다(U-114 닫음). 겹침만인 셋은 뒤집어 LA-1 대기열을 줄인다. 남는 유효 선행 UB-1(+NL-1)·HC-S·EO-1은 원칙(graph 정본·사용자 결정)에 근거하므로 유지하고, 이 셋을 더 당길지(안 C)는 원칙 경고와 함께 사용자에게 따로 묻는다. O-125 '바로 뒤'는 "IT-1 + IT-2 병합 뒤, 유효 선행 셋이 끝나는 즉시"로 해석된다 -- 문자 그대로와 다르므로 **원래 취지와 다름**으로 보고한다.

## 6. 계획 정정 자리(master `56dd1f8a` = plan/v637 줄 번호)

| # | 줄 | 고칠 내용 |
|---|---|---|
| 1 | 11 | Status: v6.38 항목(U-114 닫음, LA-1 선행 정정, O-125) |
| 2 | 1201 | N6.1 LA-1 행 '선행' 열: "DE-1(선행 근거 재확인 -- N6.14, U-114)" 삭제. "IT-1·IT-2"를 "IT-1 + IT-2 통합 병합(IT-2a~IT-2e)"으로. (안 B) FX-1·GC-9 삭제, HC-1은 "범위 11 이관 시 삭제"로. 완료 조건 칸에 O-125 새 조건 참조 |
| 3 | 1195 | N6.1 DE-1 행: 선행·착수 열 변경 없음(LA-1을 선행으로 두지 않음 확인). 필요하면 비고 "LA-1과 선후 고정 없음(1211행 꼴)" |
| 4 | 1211 뒤 | 새 문단 "**DE-1과 LA-1의 선후**": 데이터 선행 없음(U-114 판정, 이 증거 파일), 같은 통합 병합 금지, 나중 card 변화표에 앞 card 효과(커널 행 `swing_out_v`·`offset_sys_mv`·피크 행·슬루 행 삭제)를 원인으로 적음, `search/CONTRACT.md`·`_module_map.py`는 나중 card가 rebase |
| 5 | 1215 | 'card 사이 파일 겹침 순서': "GC-9 → LA-1"을 (안 B) "어느 쪽이 먼저든 나중 card가 rebase(GC-9는 순수 리팩터링 비교를 병합 직전 master에서)"로 |
| 6 | 1643 | DE-1 '순서': "LA-1과 독립(U-114)" 한 줄. 착수 조건과 무관 |
| 7 | 1683 | FX-1 근거 문단 "FX-1은 LA-1의 선행이므로 FX-1 → U17 ②·LA-1" 정정(안 B) |
| 8 | 1791 | LA-1 범위 11 "선행 card = HC-1": (안 B) "HC-1이 먼저면 LA-1이 배선, LA-1이 먼저면 HC-1이 세 자리에 배선(headroom-chain HC-1 범위 '층 0 거르기')" |
| 9 | 1792 | LA-1 범위 12: 창 이름을 순서 무관 문언으로("측정 구성 판정 창 -- DE-1 뒤 정의 창") |
| 10 | 1832 | LA-1 착수 조건에 "(3) design 41 892·924행 슬루 하한·«ID ≥ I_slew» 정정(design v1.14.2 3번 -- O-124 'DE-1 전에'를 'LA-1·DE-1 중 먼저 착수하는 card 전에')" |
| 11 | 1833 | '선행 card'에서 DE-1 항목 삭제; (안 B) FX-1·GC-9 삭제, HC-1 조건부; IT-1·IT-2를 통합 병합으로 |
| 12 | 1834-1835 | 병렬 목록에 DE-1 추가(같은 통합 병합 금지) |
| 13 | 1828 근처 | 완료 조건에 O-125 추가분(ss 제약 선언 library 회로 front ≥ 1, B81 봉인점 없는 회로 제외·따로 보고, 끝점 `slsqp_4` 비율) -- U-114와 별개지만 같은 v6.38 |
| 14 | 2262 | U-114: "**닫힘(v6.38)**: 선행 근거 없음 -- 옛 근거 O-122 소멸, 다른 겹침은 결과 결합·텍스트뿐(`_drafts/evidence/2026-10-24/u114_la1_prereq.md`)" |
| 15 | 다른 계획 | (안 B) graph-consumption v0.13 669행 'GC-9·LA-1' 순서 문장, headroom-chain v0.7.8 517행 HC-1 '층 0 거르기' 대상(새 층 0 세 자리) -- 다른 계획 개정은 그 계획 판 번호로 |
| 16 | history H1 | 'v6.38' 이력(옛 선행 문언) |

## 7. 원칙 점검(이 권고)

- graph 단일 정본: LA-1은 `sat_threshold`(HC-S)·U9(UB-1)·EO-1 생산자를 READS만. 새 필드·cache·사본 0. DE-1 제거로 생기는 둘째 생산자 0(층 0은 DE-1 필드를 읽지도 쓰지도 않음).
- 계획 우선: 순서 변경은 v6.38 개정·검증 뒤(O-125). 사용자 결정(O-38 (2), LA-Q5)은 안 B에서 건드리지 않음.
- 만들면 배선: 범위 11을 HC-1로 넘길 때 함수와 배선이 같은 card(HC-1)에 있음.
- fail-closed·상수 발명·회로 이름: 해당 변경 없음.
- **원래 취지와 다름**: O-125 'IT-2c 바로 뒤'를 'IT-1 + IT-2 통합 병합 뒤 + 유효 선행 셋 뒤'로 해석(문자 그대로는 통합 병합 규칙과 충돌).

## 8. 미확인

- LA-1이 `E/sizing/block_columns.py`를 고치는지(design 41 §5.3.6은 인용만) -- 착수 실측. 고치면 HC-S·IT-2와 파일 겹침이 생김(DE-1과는 무관).
- U17 ②의 분할·graft·S3 색인이 `E/sizing/kernel_run.py`·`seal_versions.py`를 고치는지 -- 고치면 IT-2e(같은 파일, 1533행)와 겹침. IT-2e가 LA-1보다 먼저(통합 병합 안)라 순서 문제는 없음.
- B80 IIS의 `offset_excess` 값이 DE-1 뒤에도 비트 동일인지(차동 회로 A_dc 갈래 미발동 가정) -- DE-0 몫.
- HC-0·HC-D·OP-3 진행 상황은 master 로그 grep(병합 기록 없음)만으로 봤다. 브랜치·worktree의 진행 중 작업은 확인하지 않았다.
- design 41 924행은 파일 인코딩 때문에 원문을 부분만 확인했다(«ID ≥ I_slew» 존재는 recheck8 104행과 Python 읽기로 확인).
