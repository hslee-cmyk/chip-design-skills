# gm/ID 엔진 MVP 범위 분류 (합격 시험 기준) -- 초안

작성 2026-10-07, 읽기 전용 분석. 기준 커밋 `6df4bd7`(master). 계획서 = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(이하 P), 줄 번호는 P의 행 번호.
design 문서는 `00-common`·`05`·`10`·`20`·`30`만 있고 **Phase 4~7c design(40·50·6a·6b·6c·7a·7b·7c)은 아직 없다**(P 1160~1167은 목록만). 그래서 Phase 4 이후 항목의 근거는 P 본문이다.

## 0. 합격 시험(제안)과 해석

- 입력: topology.json + 스펙 + gm/ID LUT
- 출력: 모든 소자의 W, L, 바이어스 전류·전압 + 전력·면적 최소화 해
- 합격: 4개 회로 각각 ngspice에서 소자 영역(포화)·gain·GBW·PM 스펙 만족, 엔진 예측 대 SPICE 차가 허용오차 안

**해석 가정(확인 필요)**: "library 4개 회로" = 현재 `run_harness.SPECS`의 기존 4개(`two_stage_ota`·`current_reuse_telescopic_ota`(파일럿)·`folded_cascode`·`nmcnr_amplifier`)로 읽었다. library에는 9개 회로가 있다(`assets/library/`). 신규 5개(sf·pushpull·ngcc·two_stage_sf·common_gate)를 넣으면 6a(구조 유도)·DEC-63/65/81이 필수로 올라온다.

### 0.1 '최소화'의 계획서 정의 (DEC-77~80)

| 근거 | 내용 |
|---|---|
| P 141 (N1.1 (f)), P 271 DEC-77 | 성능 스펙(gain·GBW·PM 등)은 전부 **제약**이고 최적화 축은 **(전력, 면적) 2목적**. 가중합 같은 단일 스칼라로 합치지 않는다. 산출물은 해 하나가 아니라 **제약을 만족하는 (전력, 면적) 비지배 front**. 예산이 선언되면 그 예산 안의 front 점 하나를 함께 내고, **예산이 없으면 front를 제시하고 정지**(자동 선택 금지). 두 축 눈금이 확정·구현되기 전의 front는 '추정' 표기 |
| P 272 DEC-78 | **전력 축 = 레일에서 들어오는 공급 전류의 합**(DC 정지 전류, `_metric_supply_current` 계열). `sum_current`(소자 ID 단순 합)는 직렬 기둥 중복 계상이라 목적 축 금지(DF-16) |
| P 273 DEC-79 | **면적 축 두 단계**: (a) 탐색 축 = Σ(W·L) + **선언된** 수동소자 면적(미선언이면 0으로 두고 매 실행 보고) (b) 판정·보고 축 = 레이아웃 면적(MOD7 stick_diagram, MOD8 수렴 루프). **비지배 판정의 정본은 판정 축 (b)**. 보상·부하 수동소자가 있는 회로에서 수동소자 면적 미선언이면 front는 `review_needed` |
| P 274 DEC-80 | 면적 축 눈금 둘: (i) 레이아웃 격자 분해능(PDK 선언에서 계산) (ii) bin 폭 = max(격자 분해능, 면적 축 모델 오차). 모델 오차 미측정이면 면적 축 판정 '보류' |
| P 185 NFR-5 | 두 목적 축에서는 **비지배성이 판정 기준**. 예산이 선언된 축은 그 예산 안에서 다른 축을 최소화. 활성 제약 여유 ≤ max(격자 분해능, 모델 오차) |
| P 472 (N3.7 외층) | 스칼라화는 **ε-제약**: 면적 상한 고정 → 전력 최소화, 상한을 bin 폭씩 밀고, **반대 방향(전력 상한 → 면적 최소)도** 돌아 front 양 끝을 덮는다. 지배당한 해는 버린다 |

→ 계획서 기준 "전력·면적 최소화된 해" = **(supply 전류 기반 전력, ΣWL+수동소자 면적) 비지배 front + (예산 선언 시) 그 예산을 ε로 고정한 최적점**. 스칼라 `minimize power_uA`(현 4개 회로 topology의 `objective`, 실측 확인)는 이 정의에 맞지 않는다.

### 0.2 시험 정의 자체에 필요한 결정(분류 대상 아님, 사용자 결정 필요)

1. **SPICE 허용오차의 출처**: 계획서는 SPICE 차를 **측정해 모델 오차 선언값으로 저장**한다(DEC-72, P 266·499 "산출은 abs(모델 − SPICE) = 모델 오차 선언값"). 합격/불합격 임계가 아니다. 합격 시험은 사전 임계가 필요하다 -- P 499의 비교 허용오차(노드전압 `tol_V`, ID `tol_V × gm`, AC gain은 노드 허용오차의 소신호 감도 전파)를 그대로 쓰는 안, 또는 사용자가 metric별 허용오차를 선언하는 안 중 택1.
2. **SPICE 통과를 요구할 front 점**: front 전 점 / 양 끝점 + 예산점 / 예산점만.
3. **4개 회로의 GBW·PM·gain 스펙 값**: `folded_cascode`·`nmcnr_amplifier`는 topology `constraints`가 **빈 리스트**다(실측: `sizing_roles.constraints = []`). `folded`는 실행 spec에 GBW·CL도 없다(`workspaces/run_harness.py:212~246`, CL 1 pF는 U-31 P 1108에서 스펙 확정). gain 54 dB(파일럿)·57 dB(two_stage)도 U-19(P 1096)에서 재도출 대상이다.
4. **면적 판정 축**: 정본이 레이아웃 면적(DEC-79 (b))인데 MVP에서 탐색 축(ΣWL)으로 비지배 판정을 하면 계획서와 어긋난다 -- 축소 승인 필요.

## 1. 분류 표

범례: **필수** / **필수-축소**(최소 형태 기재) / **미룸** / **완료** / **별도 결정 대기**(gate·역할 분리 인프라). 규모 = 작음/중간/큼. "추측" 표시는 실측·근거 없이 판단한 것.
구현 여부는 `skills/analog-gmid-design/assets/`(이하 A) grep으로 확인.

### 1.1 Phase 0 ~ 3 (P 997~1002)

| 항목 | 분류 | 근거 | 구현 상태 |
|---|---|---|---|
| Phase 0 레지스트리 | 완료 | P 997 "✅ 완료" | 완료 |
| 0(문서) `00-common` | 완료 | P 998, design 00-common 존재 | 완료 |
| Phase 0.5 역할 분리 인프라·공격 28건 | **별도 결정 대기** | P 999, N3.12 | `.claude/hooks/role_guard.py` 동작 중(이 분석 중 EL1 거부 실측) |
| Phase 1 TS0·1·2·3·5·7, IC3·IC5 | 완료 | P 1000; `.ai/verification/20260922-ts*`, `-ic3-completeness`, `-ic5-gate-docstrings` 판정 기록 존재 | 완료 |
| Phase 2 TS6·D 삭제·DUP 통합·DF-23 목록 | 완료 | P 1001; 판정 기록 `20260923-d-delete-*`·`20260930-p10-df23-inventory`, 승인 `20261001-b26-phase3-cards`가 "Phase 2 DoD 뒤"라 적음 | 완료 |
| Phase 3 10모듈 이동·`sizing_recipe.py` 삭제 | 미룸 | P 1002·1020: 판정 유형 equivalence(동작 보존) -- 시험 결과(W·L·SPICE)를 바꾸지 않는다. 단 N6.1 공통 착수 조건 "이전 Phase DoD PASS"(P 993)를 지키면 Phase 4 이후를 막는다 → 순서 규칙 완화 여부는 별도 결정 대기와 묶임 | design 30 승인(v8.5), 미실행(`sizing_recipe.py` 12,013줄 존재) |

### 1.2 Phase 4 (P 1003, DF는 P 913~949)

| 항목 | 분류 | 근거 | 구현 상태 |
|---|---|---|---|
| TS4 자기참조 기대값 제거 | 미룸 | P 561·1003: test 품질 항목. 엔진 출력·SPICE 결과와 무관 | 미구현 |
| DF-01 vsb 버전 혼재(W·gm·gds가 옛 vsb) | **필수-축소** (작음) | P 913: vsb를 고친 뒤 W·gm이 옛 값 → SPICE에 넣는 W가 엔진 예측 동작점과 다른 동작점을 만든다. 최소형: `reconcile_vsb_from_nodes` 뒤 해당 소자 W·gm·gds 재계산(Phase 4 몫). 6b 구조 제거는 미룸 | 미수정(`setdefault("vsb", ref_vds)` A/sizing_recipe.py:7578) |
| DF-02 노드전압 충돌 미판독 | **필수-축소** (작음) | P 914: 같은 노드에 다른 전압이 도달한 해는 SPICE에서 하나의 전압으로 풀리며 예측과 어긋난다. 최소형: `propagate_node_voltages`의 `conflicts`(A/sizing_recipe.py:3723·3758)가 tol_V 초과면 후보 실현 불가 처리 | 미수정 |
| DF-03 게이트 ValueError가 탐색 전체 중단 | **필수-축소** (작음) | P 915: ε-스윕은 여러 번의 탐색이고 한 점의 예외가 front 전체를 끊는다. 최소형: 후보 단위 실패 클래스로 바꿔 그 후보만 실현 불가로 기록(CC-4 앞부분 최소판) | 미수정 |
| DF-04 소자명 부분문자열 | 미룸 (추측) | P 916: 4개 회로 이름(M1a/M11a, M101~M302 등)에서 실제로 걸리는지 미측정. DEC-28 상태 "구현됨(DF-04)"(P 223)와 DF 표가 어긋남 -- 확인 필요 | 확인 안 함 |
| DF-05 미러비 오차를 첫 두 소자만 | **필수** (작음) | P 917: 파일럿 bias 미러는 18소자(DEC-09, P 204). 나머지 멤버 비율이 틀리면 SPICE 미러 전류가 엔진 ID와 달라 bias 전류·영역이 어긋난다 | 미수정 |
| DF-06 광범위 except가 필드 원천 버림 | **필수-축소** (작음) | P 918: `_mna_stamp_capacitance`(A/sizing_recipe.py:4029)가 용량을 조용히 빠뜨리면 GBW·PM 예측이 SPICE와 벌어진다. 최소형: 이 사이트와 `node_pole_estimate`만 재raise. 나머지 사이트 미룸 | 미수정 |
| DF-07 캐시 상한 시 캐싱 중단 | 미룸 | P 919: 성능(NFR-2). 값은 맞다 | 미수정 |
| DF-08·DF-22 spec 지문 불일치 노트 | 미룸 | P 920·934: 정본 spec만 쓰면 발동하지 않는다(추측) | 미수정 |
| DF-09 `estimate_area_budget` α 상쇄 | 미룸 | P 921: 이 함수는 사이징 경로에서 호출되지 않는다(A/sizing_recipe.py 안 호출 0, 정의 2765만). 면적 축은 `sum_area` | 미수정 |
| DF-10 이분 역산 단조성 미검사 | 미룸 (추측) | P 922: 비단조 구간에서 틀린 ID를 낼 수 있으나 4개 회로에서 발동 여부 미측정. SPICE 대조에서 ID 불일치가 나오면 승격 | 미수정 |
| DF-11 적층 diode `idu_up = 1.0` 대입 | **필수-축소** (작음) | P 923: 파일럿 class-AB battery 적층 diode에서 LUT 실패 시 조용히 틀린 W → SPICE bias 어긋남. 최소형: 대입 대신 후보 실패 | 미수정 |
| DF-12 오프셋 소자 누락 | 미룸 | P 924: 오프셋은 합격 시험 metric 아님 | 미수정 |
| DF-13 `id(lut)` 키·무상한 캐시 | 미룸 | P 925: 한 실행에서 LUT 객체가 고정이라 값 오류 경로 없음(추측) | 미수정 |
| DF-14 except → 폴백 | **필수-축소** (작음) | P 926: `lut_vdsat_headroom`·`_hr_resolve_vertical_group` 폴백은 헤드룸을 조용히 바꿔 SPICE에서 선형 영역 소자를 만들 수 있다. 최소형: 이 두 함수의 폴백을 실패로. V8 `fallback_events` 계측은 별도 결정 대기(V 검사) | 미수정 |
| DF-15 Rz 캐시 키 | 미룸 (조건부) | P 927: "실행 재현 전". 재현되면 Rz 값이 넷리스트에 틀리게 들어가 PM이 어긋나므로 그때 필수 | 미수정 |
| DF-16 전력 축 `sum_current` 중복 계상 | **필수** (작음) | P 928·272(DEC-78): '전력 최소화'의 정의 자체. 4개 회로 objective가 전부 `power_uA = sum_current`(실측). `_metric_supply_current`(A/sizing_recipe.py:4339) 존재 -- ideal source 전류 미계상(그 docstring "검사하지 않는 것" (2))도 같이 처리 | 부분(metric 있음, 목적 미교체) |
| DF-17 Test 16 FAIL 박제 | 완료 | Phase 1 TS0(`20260922-ts0-test16-fixture`) | 완료 |
| DF-18 실패해도 exit 0, θ* 출력만 | **필수-축소** (작음) | P 930: 시험이 자동이려면 결과(θ*, W·L·ID·노드전압, metric, front)를 파일로 쓰고 실패를 exit code로 내야 한다. 현재 `run()`은 `except Exception`으로 print만(workspaces/run_harness.py:422~530) | 미수정 |
| DF-19·DF-26 레일 넷 이름 집합 | 미룸 | P 931·938: 4개 회로의 레일(vdd/gnd/vss)은 이름 집합 `_DEFAULT_RAIL_HI/LO`(A/sizing_recipe.py:3714)로 이미 읽힌다. B26-1은 진행 중(spec card `6df4bd7`) | 진행 중 |
| DF-20 근거 없는 폴백 상수(`min_vds_by_role` 등) | 미룸 | P 932: 원칙 위반이지만 선언값으로 동작은 정해져 있다. SPICE 포화 실패 원인이 이 값이면 승격(추측) | 미수정 |
| DF-21 무의미 probe 3개 | 완료 | Phase 2 TS6(`20260923-probe-dead-delete`) | 완료 |
| DF-23 이름 리터럴 일반 규칙 교체 | 미룸 | P 935: 4개 회로에서는 리터럴이 그 회로 자신을 가리켜 동작한다. 전수 목록(Phase 2 몫)은 완료 | 부분 |
| DF-24 vsb bulk 가정 | 미룸 | P 936: 4개 회로 모두 최저 레일 0 V 단일 기준이라 현재 경로에서는 맞다(P 936 본문). 단 넷리스트 bulk 연결을 엔진 가정과 같게 쓰는 것은 아래 SPICE 항목에 포함 | 미수정 |
| DF-25 포화 하한 강반전 근사 `2/(gm/ID)` | 미룸 (조건부, 추측) | P 937: SPICE 영역 판정이 시험 조건이므로 엔진 포화 여유가 SPICE vdsat보다 낙관적이면 FAIL. 약반전에서 `2/(gm/ID)`가 SPICE vdsat보다 큰지 작은지는 미측정 → 첫 SPICE 실행 결과로 승격 판단 | 미수정 |
| DF-27 LUT VS 축 0~0.8 V | 미룸 (조건부, 추측) | P 939: push-pull follower용 결함. 4개 회로에서 vsb > 0.8 V 소자가 있는지 미측정(파일럿 적층 PMOS 가능성) | 미수정 |
| DF-28 CGS·CGB 열 없음 | 미룸 (조건부) | P 940: CD 셀용. 4개 회로 CD 0(P 1023). 단 LUT에 접합용량(CDB·CSB)이 없어 PM·GBW 예측 오차의 원인이 될 수 있다(추측) -- SPICE 차가 크면 U-27 LUT 재생성 승격 | 미구현 |
| DF-29 파일럿 전용 metric 3개 | 미룸 | P 941: CMRR·PSRR은 시험 metric 아님 | 미수정 |
| DF-30 회로별 gain/PM metric(folded·nmcnr) | **필수-축소** (작음~중간) | P 942: 폐형식 gain/PM은 "sympy 전수 유도·ngspice 교차검증 전"(workspaces/run_harness.py:225). SPICE와 맞춰야 하므로 전회로 MNA로 바꾼다. 최소형: 두 회로 topology `metrics` 선언을 기존 `smallsignal_gain_db`(A/sizing_recipe.py:5042)와 아래 MNA GBW·PM metric으로 교체(ports는 U-08로 선언 완료). 옛 함수 삭제·레지스트리 정리는 미룸 | 미수정 |
| DF-31 회로별 보상 함수 | 미룸 | P 943: 4개 회로 보상 함수가 모두 있다(folded는 단일단). 일반 규칙 DEC-70은 신규 회로용 | 회로별 구현 있음 |
| DF-32 헤드룸 역할 라벨 | 미룸 | P 944 | 미수정 |
| DF-33 실행 spec 소자 이름 리터럴 | 미룸 | P 945: 손선언으로 동작 | 미수정 |
| DF-34 Phase 4 몫(PDK 상수 한 곳 선언, U-30) | **필수-축소** (작음) | P 946·1107(U-30): `two_stage_ota`만 `min_finger_w = 0.1e-6`(run_harness.py `_spec_two_stage_ota`)이고 sky130 최소 채널 폭 0.42/0.36 µm(difftap.2) 미만 → SPICE 모델 bin 밖 소자가 나올 수 있다. 최소형: PDK 최소 W·L 한 곳 선언과 4개 spec이 그 값을 참조. 수동소자 단위 면적(U-36)도 여기 함께 | 미수정 |
| DF-35 하네스 절대 경로 | 완료 | `.ai/verification/20260930-df35-harness-paths.json` | 완료 |
| DF-36 instance.json 절대 경로 | 완료 | `.ai/verification/20260930-df36-instance-relpath.json` | 완료 |
| DF-37 광범위 except 전수 | 미룸 (하네스 `run()` 몫만 DF-18에 포함) | P 949: 전수 교체는 품질 항목. 시험 경로에 걸리는 사이트는 DF-03·06·14에서 개별 처리 | 미수정 |
| CC-4 실패 클래스·`exit_code_for` | **필수-축소** (작음) | 00-common 551~559 CC-4: DF-03·DF-18 최소형이 쓰는 몫만 | 미구현 |
| CC-7 성능 측정 도구 | 미룸 | 00-common CC-7: 성능 보고용 | 미구현 |
| CC-8 무동작 판정 도구 | 미룸 | 00-common CC-8: 회귀 증명 인프라 | 미구현 |
| MG1 레일 전압 이름 변경 | 미룸 | P 1003: 이름 변경 | 미구현 |
| U-27 LUT 재생성 | 미룸 (조건부) | P 1104: DF-27·DF-28 조건이 걸리면 승격 | 미실행 |
| Phase 2에서 배선을 고른 함수 배선 | 미룸 | P 1003 | -- |
| V8 `fallback_events` | **별도 결정 대기** | N4.2 V8(P 846) | 미구현 |
| I-C11 기존 4개 회로 실행 가능성(U-09) | **필수** (중간) | P 981·1086: `two_stage_ota`는 현재 KVL 위반으로 FAIL(`workspaces/regress_check_two_stage_ota_session44.log`: "stage1_out 그룹의 VDS 합 2.60373V가 vdd 1.8V와 불일치"). 실행이 안 되면 시험 불가. nmcnr `stage2_diode_ref` 이월도 같은 항목 | 미해결 |
| IC11 활성(2레일) | 미룸 | P 831: 원점 이동 불변성. 4개 회로는 0 V 기준 | xfail(test_ic11.py) |

### 1.3 Phase 5 (P 1004)

| 항목 | 분류 | 근거 | 구현 상태 |
|---|---|---|---|
| 실패 캐시, 시작점 선택(S3 v1), margin | 미룸 | P 1004·1022: 재평가 0·warm start는 시간 절약. ε-스윕이 느리면 θ* 재사용을 축소판으로 당겨올 수 있음(추측) | 미구현 |

### 1.4 Phase 6a (P 1005, 구조 유도)

| 항목 | 분류 | 근거 | 구현 상태 |
|---|---|---|---|
| MG2·GB0 의미·로드 게이트·영역 표기 | 미룸 | P 1005: 4개 회로는 선언 stage·역할로 이미 사이징한다 | 미구현 |
| S0 LUT 메타 배선(I-A5) | 미룸 | P 957 | 미배선 |
| GB1 DC 역할·G_vgs 사이클(DEC-64)·기둥 유도(DEC-71)·엣지 domain | 미룸 | P 1005: 층 0 presolve(DEC-71)의 입력. 층 0을 미루면 함께 미룸 | 미구현 |
| GB2 SP1 stage 분할 shadow·셀 분류·DEC-63/65 | 미룸 | P 1005: 4개 회로 CD 0·버퍼 묶음 0(P 1023). 신규 회로를 넣을 때 필수 | 미구현 |
| 규칙 분기 발동표(DEC-59) | 미룸 | P 253 | 미구현 |
| N3.2-8 (iii)(vi) 측정 목록·J 공동분석·`structure.json` | 미룸 | P 1005 | 미구현 |
| ports(U-08)·supply_nets(U-26 (b)) 선언 | 완료(선언) | P 1005 "2026-09-17 선언 완료"; topology 실측 4개 모두 `ports`·`supply_nets` 있음 | 완료 |
| IC7(library 회로 실행) | **필수-축소** (작음) | P 827: 합격 시험 자체가 4개 회로 실행이다. 최소형: 4개 회로 end-to-end 실행 + SPICE 대조 회귀 1개. 규칙 분기·`unsupported_rule_branch` 몫은 미룸 | xfail(test_ic7.py) |

### 1.5 Phase 6b (P 1006, 노드전압·봉인)

| 항목 | 분류 | 근거 | 구현 상태 |
|---|---|---|---|
| `_evaluate` cProfile 계측 | 미룸 | P 1006: 탐색 층 결정용(NFR-2) | 미실행 |
| W 티어 W0~W4·SC-a~e·버전 카운터·S2 `dc/ss/ls` 분리·계산 블록 memo | 미룸 | P 382~421·1006: 구조적 재발 방지. 최종 해의 정합은 아래 '최종 해 봉인 검사'로 대신 확인 가능 | 미구현 |
| 봉인 항목 1·2·3·6·7(노드 충돌·VGS 정합·KCL·벌크 역바이어스·포화 여유)을 **최종 해 검사 + 후보 제약**으로 | **필수-축소** (중간) | P 428~434: 이 다섯이 SPICE `.op`가 엔진 동작점과 같은지(영역·ID·노드전압)를 결정한다. 최소형: 평가 결과에 대해 다섯 잔차를 계산해 tol_V/tol_I 초과면 후보 실현 불가, 최종 해에 판정 기록. 항목 4·5(버전·writer)는 W 티어와 함께 미룸, 항목 8은 1·2 통과 시 자동 성립(P 435) | 부분: `kcl_residual`·`stack_headroom_slack` metric(파일럿만, A/sizing_recipe.py:5098·5100), `conflicts` 수집만 |
| tol_V(LUT LOO)·tol_I·K_max 식 | **필수-축소** (작음) | P 437~441: 위 검사와 SPICE 비교 허용오차(P 499 "같은 tol_V를 SPICE 비교 노드전압 허용오차로")의 근거. 최소형: `tests/probes/probe_interp_scheme_loo.py` 방법을 함수로 올려 tol_V만. K_max·NONCONVERGENT 미룸 | probe만 존재 |
| DF-25 VDsat 유도 | 미룸 (조건부) | 1.2 표 참고 | 미수정 |
| CD source 노드 W2 | 미룸 | 4개 회로 CD 0(P 1023) | 미구현 |
| IC1 VGS 정합 test | **필수-축소** (작음) | P 821: 위 봉인 항목 2와 같은 판정 -- 최종 해에서 4개 회로 test로 활성 | xfail(test_ic1.py) |
| IC2 순서 섞기 결정론 | 미룸 | P 822 | xfail |
| IC9 중복 원시 대입 | 미룸 | P 829 | xfail |
| IC10 캐시 키 가변 상태 | 미룸 (추측) | P 830: stale 값이 결과를 바꾸는 사례가 4개 회로에서 확인된 적 없음 | xfail |
| I-A7 순환 블록 수렴·I-B8 KCL 잔차 제약·I-B12 set 순회·I-B13 출처 태그 | I-B8만 필수-축소(위 봉인 항목 3), 나머지 미룸 | P 959~970 | -- |

### 1.6 Phase 6c (P 1007)

| 항목 | 분류 | 근거 | 구현 상태 |
|---|---|---|---|
| 결합 잔차 측정, GB3 결합 블록 y | 미룸 | P 1007·460: 진단·할당 신뢰 판정용. 판정은 외층 전회로(DEC-74) | 미구현 |
| GB4 달성가능성(블록 gain 상한)·DOF | 미룸 | P 174 FR-8: 탐색 **전** 불가 보고. 시험은 해를 찾는 회로에서만 돌므로 없어도 통과 가능. 스펙이 불가능하면 진단 시간이 늘어난다(추측) | 미구현 |
| `review_needed`·`unsupported_rule_branch` 정지 | 미룸 | P 1007 | 미구현 |
| IC4·IC6·IC8 | 미룸 | P 824·826·828 | xfail |

### 1.7 Phase 7a (P 1008, metric·SPICE)

| 항목 | 분류 | 근거 | 구현 상태 |
|---|---|---|---|
| gain 제약을 전회로 MNA gain으로 통일(`gain_ss_db`) | **필수-축소** (작음) | P 488·972(I-B21): 파일럿 gain 제약 `gain_stages_sum`은 미러 부하를 못 봐 전회로 MNA와 26.15 dB 벌어진다 → SPICE gain과 맞을 수 없다. 최소형: 4개 회로 gain 제약을 이미 있는 `smallsignal_gain_db`(A/sizing_recipe.py:5042, 파일럿은 `gain_full_circuit_db`로 선언돼 있음)로 바꾼다. 이름 변경(MG)·옛 metric 삭제 미룸 | metric 있음, 제약 미교체(파일럿·folded·nmcnr) |
| **GBW metric(전회로 MNA 단위이득 주파수)** | **필수** (작음~중간) | 합격 조건 GBW. A에 GBW를 재는 metric 없음(grep `gbw` metric 0). 현 PM metric은 크로스오버를 **재지 않고** 보상 함수가 노출한 설계값 `omega_c`를 쓴다(A/sizing_recipe.py:4221). 최소형: `full_circuit_response_at_omega`(A/sizing_recipe.py:4104) 스윕으로 |H|=1 주파수를 찾는 metric | 미구현 |
| PM을 측정 크로스오버에서 계산 | **필수-축소** (작음) | 위와 같은 이유. `_metric_parasitic_pm_deg`(4166)의 위상 누적을 측정 크로스오버 기준으로 바꾼 판 | 부분 |
| gmb 유도와 MNA 반영 | **필수-축소** (작음~중간) | P 490: "현 MNA가 gmb를 넣지 않는 것은 7a에서 함께 고친다". A 전체 `gmb` 0건(실측). 캐스코드 다수(파일럿 텔레스코픽, folded)라 gain이 SPICE보다 낮게 예측된다(크기 추측, 수 dB 가능). 최소형: LUT VS 축 수치미분 gmb 함수 + MNA 스탬프. 블록 국소 모델은 미룸 | 미구현 |
| 블록 국소 소신호 모델·잔차·감도 게이트 | 미룸 | P 489·492·493: 할당 분해용. 판정은 전회로(DEC-74) | 미구현 |
| `rout_ss_ohm`(DEC-66)·스윙·입력 범위(I-A6) | 미룸 | 시험 metric 아님(P 491·497) | 미구현 |
| DF-28 CGS·CGB 스탬프 | 미룸 (조건부) | 1.2 표 참고 | 미구현 |
| 전력 축 DEC-78 교체 | **필수** (작음) | = DF-16 | 부분 |
| 면적 탐색 축 DEC-79 (a) | **필수-축소** (작음) | P 273·496: `sum_area`(A/sizing_recipe.py:2854) + **수동소자 면적**(U-36 단위 면적 선언). 4개 회로 중 보상 커패시터가 있는 회로는 면적 0이면 Cc 증가에 대가가 없어 front가 왜곡된다(DEC-79 본문) | `sum_area`만 |
| 면적 판정 축 DEC-79 (b)·MOD8 수렴 루프·두 축 차 기록 | 미룸 (축소 승인 필요) | P 273: 정본 비지배 축이지만 레이아웃 루프(MOD8, 7b) 전체를 요구. 시험 출력 '면적 최소화'를 탐색 축으로 정의하면 미룰 수 있다 -- 계획서와 어긋나므로 0.2-4 결정 | 미구현(stick_diagram 산출 면적은 있음) |
| DEC-80 면적 축 두 눈금·bin·예산 게이트 | 미룸 | P 274: 층 0·DP bin용. ε-스윕 간격만 정하면 된다(아래 7b 행) | 미구현 |
| metric DUP 3쌍(gain/PM/CMRR) 통합 | 미룸 (gain/PM은 DF-30 축소판으로 처리) | P 1008 | 미구현 |
| **트랜지스터 레벨 SPICE 대조(U-11)**: 넷리스트 생성 + ngspice `.op/.ac` 실행 + 영역·gain·GBW·PM 추출 + 엔진 대비 차 | **필수** (큼) | P 499·1088: 합격 시험의 판정 장치 자체. 일반 넷리스트 생성기·실행기는 없다(A grep: `write_spice_netlist`·`run_ngspice` 0). 재사용 후보: `workspaces/current-reuse-telescopic-ota-report/spice/gen_single_device.py`(sky130 include 패턴), `stage3_full_circuit_ngspice_crosscheck.py`(topology에서 연결을 읽는 51소자 AC 대조, 단 이상화 소신호), `A/sky130_lut_sweep.py:121 _gen_netlist`. 포함해야 할 것: 소자 W·L·nf, bulk 연결(엔진 가정과 같게, DF-24), 보상·부하 수동소자 값(U-31 CL), ideal source 값(엔진 해의 바이어스 전류 -- I-B14 우회), bias 전압원, 개루프 측정 회로(고이득 노드 DC를 잡는 대형 L/C 되먹임 등 -- 방법 결정 필요, 추측), 영역 판정(`@m[vds]`·`@m[vdsat]` 등) | 미구현(파일럿 전용 스크립트만) |
| 모델 오차 선언값 저장(DEC-72)·`verified_by` | **필수-축소** (작음) | P 266·498: 최소형: 위 대조 결과를 회로·metric별 `abs(모델 − SPICE)`로 판정 기록 파일에 저장. `derived.model_error_*`·`value_from_model_error` 참조 배선은 미룸 | 미구현 |
| bisection 임계값 재도출(DEC-22·75) | 미룸 | 기본 비활성(P 217) | 미구현 |
| U-19 gain 기준 재도출, U-17 mismatch σ | 미룸 (스펙 값 결정은 0.2-3) | P 1096·1094 | -- |

### 1.8 Phase 7b (P 1009, 보상·할당·front)

| 항목 | 분류 | 근거 | 구현 상태 |
|---|---|---|---|
| GB5 보상 규칙 일반화(DEC-70)·평가 커널 재배열 | **필수-축소** (작음) | P 1009·169 FR-3: GBW·PM을 만족해야 한다. 최소형: 회로별 보상 함수(DF-31, 4개 모두 있음)를 유지하고 GBW·PM을 위 MNA metric **제약**으로 판정. 단일단 folded는 U-12 `gm_1 ≥ 2π·GBW·C_out,total` 또는 측정 GBW 제약(P 1089). 일반 규칙·재배열은 미룸 | 회로별 함수 있음 |
| GB6 층 0 기둥 조립 presolve(DEC-71) | 미룸 | P 265·1009: U-33(P 1110) "실측 후 결정" 미결. 현 SLSQP multi-start로 파일럿이 수렴한다(run_harness.py `slsqp_kwargs`) | 미구현 |
| 외층 SLSQP 기본 경로 | 완료(부분) | DEC-54 "부분(multi-start만)"(P 248). folded는 1-D grid, two_stage·nmcnr은 grid(`SPECS`) | 부분 |
| 정밀 경로(내층 DP·중층 좌표강하) | 미룸 | DEC-73(P 267) 선언 시만 | 미구현 |
| **(전력, 면적) 비지배 front 산출 + ε-제약 스윕(두 방향) + 비지배 필터 + front 표** | **필수-축소** (중간) | P 271·472·1027·1035: '최소화'의 계획서 정의. 최소형: 외층 SLSQP에 면적 상한 제약을 걸고 전력 최소화를 상한 N개에서 반복 + 반대 방향 끝점(면적 최소) 1회 + 지배점 제거 + front 표(점마다 θ*, 전력, 면적, 활성 제약과 여유). 스윕 간격은 DEC-80 대신 임시 규칙(예: 두 끝점 사이 균등 N점 -- **상수이므로 근거 선언 필요**). 재사용: `tests/probes/probe_area_pareto.py`(면적 예산 스윕 + SLSQP 실측, 결과 `tests/probe_area_pareto.result.txt`) | 미구현(probe만) |
| 예산 선언 시 front 안 한 점 선택(U-13) | **필수-축소** (작음) | P 1090: 예산 미선언이면 front 제시 후 정지가 계획서 규칙. 시험이 '해 하나'를 요구하면 예산 선언이 필요 → 사용자 결정. 구현은 ε 고정 1회 풀이 | 미구현 |
| `sizing_spec.json` v5·MG3·로더 | 미룸 | P 753~764: 스펙은 현 `SPECS` + topology `constraints`로 입력 가능. 단 '입력 = topology + 스펙' 형식을 파일로 요구하면 축소판(constraints·compensation_targets·supplies_v만) 필요 -- 추측 | 미구현 |
| U-31 CL 부하 요소 추가(folded·nmcnr·two_stage) | **필수-축소** (작음) | P 1108: SPICE GBW·PM은 CL 없이 잴 수 없다. 최소형: 사용자 확인 후 topology `passive_elements`에 CL 추가(또는 넷리스트 생성기가 spec `CL`을 출력 포트에 붙임). `element_values` 이관은 미룸 | 미추가 |
| `value_dc_amp` 소비(DEC-08, I-B14) | 미룸 (넷리스트가 엔진 해 전류를 출력하는 것으로 대체) | P 203·971: 시험은 바이어스 전류를 **출력**으로 요구하므로 ideal source 값 = 엔진 해. 선언 고정값 소비는 미룸 | 미배선 |
| DEC-65 방향별 최대 전류·슬루 | 미룸 | 시험 metric 아님 | 미구현 |
| 루프 안정도 제약 게이트(U-24) | 미룸 | 4개 회로는 개루프 PM으로 판정 | 미구현 |
| MOD8 수렴 루프·면적 탐색 대 판정 축 차 | 미룸 | 위 DEC-79 (b) 참고 | 미구현 |
| 버퍼 대조 test(sf·pushpull), DEC-81 복합 블록 | 미룸 | 4개 회로 밖 | 미구현 |
| 다른 모델 전수탐색 대조(P 476) | 미룸 (축소 대안: multi-start 일치) | '최소'의 독립 증거. 최소형으로 front 점마다 시작점 3개 이상에서 같은 점에 수렴함을 기록(추측: 계획서 기준보다 약함) | 미구현 |
| wall-clock 예산 게이트(DEC-34) | 미룸 | P 228 | 미구현 |
| U-33·U-23 선측정 프로토타입 | 미룸 | 층 0 미루면 불필요 | 미실행 |
| `gain_budget_db` 출력(DEC-03) | 미룸 | P 199: 할당 산출물. 시험 출력 항목 아님 | 미구현 |
| 노드전압(바이어스 전압) 출력 | **필수-축소** (작음) | 시험 출력 '바이어스 전압'. 현 instance.json `sizing`에는 ID·W·L·vds·gm_id만 있고 노드전압이 없다(실측 `workspaces/folded-cascode-report/folded_cascode.instance.json`). `propagate_node_voltages`(A/sizing_recipe.py:3727) 결과를 결과 파일에 쓰면 된다 | 미구현 |

### 1.9 Phase 7c (P 1010)

| 항목 | 분류 | 근거 | 구현 상태 |
|---|---|---|---|
| SPICE `.op` 전 소자 대조 | **필수** (7a SPICE 항목에 합침) | P 1010·1028: 시험 조건 '소자 영역'은 전 소자 `.op`가 필요하다. 계획서는 7a에서 한 점, 7c에서 전 소자로 넓히지만 시험은 처음부터 전 소자 | 미구현 |
| S3 아카이브·재실행 적중 | 미룸 | P 1028 | 미구현 |
| Sobol 전역 샘플·분지 | 미룸 | DEC-75 기본 비활성 | 미구현 |
| IC1~IC11 전원 PASS | 미룸 (IC1·IC7만 축소 활성) | P 1028 | -- |

### 1.10 N4.1 IC1~IC11 요약 (P 821~831)

| IC | 분류 | 근거 |
|---|---|---|
| IC1 VGS 정합 | 필수-축소 | 봉인 항목 2 = SPICE 동작점 일치 조건 |
| IC2 순서 섞기 | 미룸 | 결정론, 시험 결과 무관(추측) |
| IC3 필드 완전성 | 완료 | Phase 1 판정 기록 |
| IC4 role 라벨 제거 불변 | 미룸 | 구조 유도(6a) 뒤 의미 |
| IC5 게이트 docstring | 완료 | Phase 1 판정 기록 |
| IC6 DOF 진단 | 미룸 | 6c |
| IC7 library 회로 실행 | 필수-축소 | 4개 회로 end-to-end가 곧 시험 |
| IC8 증거 없는 유도 정지 | 미룸 | 6c |
| IC9 중복 원시 대입 | 미룸 | 품질 |
| IC10 캐시 키 가변 상태 | 미룸(추측) | 4개 회로 발동 사례 없음 |
| IC11 레일 원점 이동 | 미룸 | 4개 회로 0 V 기준 |

### 1.11 별도 결정 대기 (분류하지 않음)

Phase 0.5(P 999), N3.12 역할 분리 전체(P 567~724), V1~V10(P 837~848), EL1~EL4(P 694~704), N4.3 공격 시나리오(P 850~895), N6.3 공통 완료 조건의 auditor·merge gate 몫(P 1032), 그리고 이것들에 묶인 순서 규칙 "이전 Phase DoD PASS"(P 993). 이 결정이 Phase 3를 Phase 4 앞에 둘지를 정한다.

## 2. 요약

### 2.1 개수

| 분류 | 개수 | 항목 |
|---|---|---|
| 필수 | 5 | DF-05, DF-16(= DEC-78 전력 축, 한 번만 셈), I-C11(U-09), GBW metric, SPICE 대조 장치(7a U-11 + 7c 전 소자 `.op`를 한 건으로 셈) |
| 필수-축소 | 24 | DF-01, DF-02, DF-03, DF-06, DF-11, DF-14, DF-18(+DF-37 하네스 몫), DF-30, DF-34(U-30, +U-36 수동소자 단위 면적), CC-4 최소판, IC7, 봉인 항목 1·2·3·6·7 최종 검사, tol_V, IC1, gain 제약 MNA 통일, PM 측정 크로스오버, gmb, 면적 탐색 축 DEC-79(a), 모델 오차 기록, GB5 축소, (전력, 면적) front + ε-스윕, 예산점 선택(U-13), U-31 CL, 노드전압 출력 |

**필수 5 + 필수-축소 24 = 29건**. IC1은 봉인 항목 2와 같은 판정이고 CC-4는 DF-03·DF-18 안에서 끝나므로 실제 작업 단위는 약 27개.
조건부 승격 후보(첫 SPICE 결과로 판단): DF-10, DF-15, DF-20, DF-25, DF-27, DF-28(+U-27 LUT 재생성).

### 2.2 규모

| 규모 | 항목 |
|---|---|
| 큼 (1) | SPICE 대조 장치(넷리스트 생성·개루프 측정 회로·`.op/.ac` 실행·영역/gain/GBW/PM 추출·엔진 대비 비교) |
| 중간 (5) | I-C11(two_stage KVL 실패·nmcnr 이월), 봉인 항목 최종 검사(1·2·3·6·7), (전력, 면적) front ε-스윕, gmb 유도·MNA 반영, GBW metric(+PM 측정 크로스오버) |
| 작음 (나머지 23) | DF-01·02·03·05·06·11·14·16·18·30·34, CC-4, tol_V, gain 제약 MNA 교체, 면적 탐색 축(+수동소자 면적), 모델 오차 기록, GB5 축소(GBW·PM 제약), 예산점, CL 추가, 노드전압 출력, IC1·IC7 활성 |

### 2.3 의존 순서

1. **사용자 결정 먼저**: 0.2의 네 가지(SPICE 허용오차 출처, SPICE를 요구할 front 점, 4개 회로 gain·GBW·PM 스펙 값과 출처, 면적 판정 축 축소) + 1.11 별도 결정(Phase 3 선행 여부). U-31 CL 추가는 connectivity라 사용자 확인.
2. **실행 가능성**: I-C11(two_stage) → DF-18·CC-4·DF-03(결과 파일·exit code·후보 단위 실패) → DF-34/U-30(PDK 최소 W).
3. **동작점 정합**: tol_V → DF-01·DF-02·DF-05·DF-11·DF-14 → 봉인 항목 최종 검사(IC1). 이것이 SPICE `.op` 일치의 전제다.
4. **SPICE 장치**(3과 병렬 착수 가능, 현 엔진 해로 먼저 돌려 기준선을 얻는다): 넷리스트 생성(CL·수동소자·bulk·바이어스원) → `.op` 영역 판정 → `.ac` gain·GBW·PM.
5. **엔진 metric**: gmb → gain 제약 MNA 통일(DF-30 포함) → GBW metric·PM 측정 크로스오버 → GB5 축소(GBW·PM 제약). 4의 첫 결과로 DF-25·DF-27·DF-28(U-27)·DF-10의 승격 여부를 판단.
6. **목적 축**: DF-16(전력 = supply 전류) + 면적 탐색 축(수동소자 면적) → ε-제약 front → 예산점 → 노드전압 포함 결과 출력.
7. **합격 판정**: 4개 회로 × (front 지정 점) SPICE 대조 + 모델 오차 기록(IC7 회귀).

### 2.4 계획서와 어긋나는 점(축소 승인 필요)

- N6.1 순서(P 993)를 그대로 지키면 Phase 3(equivalence)·4 전부·5·6a·6b·6c를 지나야 7a·7b에 닿는다. 위 축소안은 Phase 4·6b·7a·7b의 일부를 앞당긴다.
- DEC-79: 비지배 판정 정본은 레이아웃 면적인데 축소안은 탐색 축(ΣWL + 수동소자)으로 판정한다.
- DEC-72: SPICE 차는 계획서상 '측정값'이지 합격 임계가 아니다.
- DEC-71·73(층 0 + 외층이 기본 경로): 축소안은 현 SLSQP multi-start를 그대로 쓴다(U-33 미결과 일치).
- front 스윕 간격을 DEC-80 없이 정하면 근거 선언 없는 상수가 된다(WP-03) -- 간격 규칙을 선언으로 둬야 한다.
