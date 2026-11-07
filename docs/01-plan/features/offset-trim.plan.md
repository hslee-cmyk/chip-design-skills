---
template: plan
version: 0.7.0
---

# offset-trim Planning Document

> **Summary**: gm/ID 엔진(`skills/analog-gmid-design/gmid_engine/`)에 **입력 offset 전류 주입 trim**을 넣는다. v0.7(사용자 결정 O-258)부터 흐름은 상위 gain-budget DEC-110의 AI 설계·레이아웃 5단계 안에 놓인다(자리표 N3.10).
> 1. **trim 필요 판단과 후보(엔진, 국면 1)**: 원본 topology의 엔진 σ_in·V_id*로 trim이 필요한지 보고, 기존 수반(adjoint) offset 해석으로 주입 노드 쌍 후보·극성별 headroom·잡음 영향을 낸다. 엔진 σ_in은 trim 사양을 정하지 않는다.
> 2. **trim 사양(oracle MC)**: 5단계 (2) SPICE 닫기 뒤의 실현 점(실현 w_f·m 반영)을 oracle MC로 재어 σ_MC를 얻고, trim 사양(범위 = k·σ_MC + |계통 offset|, LSB 상한 ← V_res, 비트 수 하한)을 기록한다. 표본 수는 spec의 σ 정확도 선언에서 유도한다.
> 3. **trim 파일과 승인**: AI가 엔진 후보표·MC 근거로 trim 구조를 별도 선언 파일 `<회로>.trim.topology.json`(role: trim, 포트, 연결표, 코드 입력 선언)과 의도 문서로 제안하고, 사용자가 승인한 뒤에만 로더 블록 하나가 원본 topology와 그 파일을 결정적으로 합성한다(소자마다 출처 칸). 원본 topology는 바뀌지 않는다. 옛 `augment_trim`(파생 topology 생성)은 없앤다.
> 4. **합성 회로 사이징과 trim 부담(국면 2)**: 같은 θ에서 원본만 변형 대 원본 + trim(중간 코드) 변형의 차를 trim 부담으로 재고, spec 부담 예산 안에서 trim 소자를 사이징한다(목적 = 주입 넷 C·컨덕턴스·trim 전력 최소, 제약 = 범위·LSB·부담). 부담을 못 지키면 원본 θ까지 합성 회로 기준으로 다시 푼다. 그 뒤 합성 회로 (2) 닫기와 trim 뒤 잔여 MC(표본마다 최적 코드)로 (3) floorplan 확정 전에 trim을 포함해 확정한다.
>
> DAC는 차동 전류 steering 이진 가중이고, DNL이 부족하면 상위 비트를 thermometer로 둔다. 디지털 코드의 탐색·저장은 엔진 밖이고, 엔진은 코드 입력·코드 상태 선언만 읽는다.
>
> 5. **SPICE 온도 보정 루프**(v0.5, T-29~T-32): 엔진 탐색은 LUT 한 조건 그대로 두고, offset·trim 잔여의 합격은 SPICE 오라클이 선언 온도 범위에서 판정한다. 불합격이면 오라클이 잰 metric별 방향 여유 Δ_T(측정 기록)로 다음 변형의 제약 문턱을 조여 같은 실행 계획 안에서 다시 돈다(D-24 안 B). 범위 판정과 루프는 오라클 능력 기록이 확인된 (PDK, 시뮬레이터) 조합에서만 동작한다. 아니면 fail-closed다. 능력 확인 절차는 oracle-portability 계획(T-33)이 소유한다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code
> **Status**: **v0.7.0 -- 사용자 결정 O-258 반영(2026-11-07 "동의해" -- (A) offset MC 시점: 엔진 σ_in = trim 필요 판단·후보 탐색, 5단계 (2) 닫기 뒤 oracle MC σ_MC로 trim 사양, 표본 수 = σ 정확도 선언 유도, 승인, 합성 회로 (1)(2) 재실행·trim 뒤 잔여 MC, (3) 전 확정, (5) 뒤 확인만; (B) trim 구성: `augment_trim` 파생 topology → 원본 topology + trim 파일 두 선언 합성(로더 블록 하나, 소자 출처 칸), 코드 입력·코드 상태 선언(O-249), trim 부담 = 같은 θ 원본만 대 원본 + trim 변형 차(offset-strategy 변형 틀), 디지털 코드 탐색·저장 엔진 밖), 상위 gain-budget v6.39.0 DEC-110 5단계 자리(N3.10, 상위 병합 master `57a014b2`), card TR-* 재배열(LA-1 뒤 -- O-229 4), **원래 취지와 다름**(O-258이 바꾸는 결정 -- N7.2 'v0.7' 표), 독립 판정 전**(2026-11-07, 브랜치 `plan/20261107-trim-compose`, base master `faf69218`; 경위·옛 문언 history 'v0.7.0') 이전 판: **v0.6.5 -- 상위 gain-budget v6.38.8 전파(상위 사용자 결정 O-222 -- G2-a `triode` 선언 소자 포함, on 스위치 첫 소비자 후보), 승인됨(사용자 결정 O-226 위임 -- la1_auto_decisions.md A-25, 2026-11-03, plan/v6388 HEAD `28ec6bf6`, 계획 검증 재판정 Major 0)**(경위 history Version History 0.6.5 행) 이전 판: **v0.6.4 -- 상위 gain-budget v6.38.6 열다섯째 커밋 전파(상위 사용자 결정 O-202·O-205·O-210·O-212 -- off 선언 = 사이징·포화 요구 제외 + 0 모형 + 1차 ΔV·O-h(`judged_by`)·VGS < 0 off 점 E-0 정지, 선언 영역 대조 삭제, 온도 점 전도 판정 = 부호 비교; LUT 확장 = TR card 착수 조건; **원래 취지와 다름(승인 상위 O-202·O-212)**), 승인됨(상위 gain-budget v6.38.6 사용자 결정 O-216, 2026-11-02 -- plan/v6386 HEAD `e71aa597`)**(2026-10-31, 브랜치 `plan/v6386`; 경위 history Version History 0.6.4 첫째~넷째 커밋 행 -- 셋째·넷째 = 상위 열일곱째·열여덟째 커밋(계획 검증 51·52)) 이전 판: **v0.6.3 -- 상위 gain-budget v6.38.6 아홉째 커밋 전파(상위 사용자 결정 O-197 PDK 이식성 -- OP-6 능력 기록 표기를 '현재 PDK 기술자' 역할로, 사례 표지; 의미 변경 0), 검증 대기**(2026-10-31, 브랜치 `plan/v6386`; 경위 history Version History 0.6.3 행) 이전 판: **v0.6.2 -- 승인됨(상위 사용자 결정 O-173, 2026-10-29; 넷째~일곱째 커밋(상위 v6.38.5 전파) = 상위 사용자 결정 O-193, 2026-10-31) (v6.38.4 열넷째 커밋 백로그 재감사 반영 -- 삭제 7·배정 4·질문 0, 검증 대기) -- 상위 gain-budget v6.38.3 열두째 커밋(사용자 대원칙 O-169) 판정 W 행·`offset_sys_mv` 행 재작성(상위 N6.35 E-05·U-108: 커널에서도 V_id* 성분 (1)(2)로 판정, front는 판정 W로 성분 (3)을 더해 재판정 -- 옛 '커널에서는 ΔW = 0이라 V_id* = 0' 삭제), **원래 취지와 다름 -- 승인 O-170**(상위 승인 표 #23), 승인됨(상위 사용자 O-170, 2026-10-29)**(승인 커밋 -- 상위 gain-budget v6.38.3 승인 O-170; 경위 history 승인 행)(2026-10-28, 브랜치 `plan/v6383`; 둘째 커밋 -- 상위 열셋째 커밋·상위 독립 검증 11 L-4: 판정 W 행 머리의 낡은 'DEC-74 front 전용 예외'를 상위 DEC-74·U-108(커널 + front 재판정)로; 경위 history 0.6.2 행) 이전 판: **v0.6.1 -- 승인됨(사용자 O-60 "병합 승인", 2026-10-20, `wt/_drafts/user_decisions.md` O-60 행). O-58·O-59 후속 정정**(2026-10-20, 브랜치 `plan/offset-trim-v061`(승인·병합됨 O-60, 최종 머리 `2ca73b7b`), base master `2e707d5d` = v0.6 승인본; 사용자 결정 O-59 (4) DV-13 -- `wt/_drafts/user_decisions.md` O-59 행; 근거 `wt/_drafts/evidence/2026-10-20/o59_plans_revalidation.md` §6 '다른 계획 후속 정정 행'; 상위 정본 gain-budget v6.21 `plan/gb-v621` `54a3a328` DEC-23 '이동의 기준점'(223행) -- 인용은 절 이름, 해시는 병합 뒤 맞춤(승인·병합됨 O-60, 최종 머리 `54a3a328`)). 내용: DEC-23 V_id* 인용 세 자리(N2 O-53 행, `offset_sys_mv` 행, matching 유도 제약 행)에 기준점 V_id,0 인용, 온도 조건 V_id*(T)의 기준점 확인. 경위 history 0.6.1 행. 이전 판: **v0.6 -- 승인됨(사용자 O-57 "병합 승인", 2026-10-20, `wt/_drafts/user_decisions.md` O-57 행; 독립 최종 diff 재확인 '병합 가능'). O-53·정합 감사 반영**(2026-10-20). 근거: 사용자 결정 O-53(2026-10-20 "권고대로 진행해", `wt/_drafts/user_decisions.md` O-53 행 -- A2·A3·B1·B2·B3)과 O-23~O-52(특히 O-34, O-44, O-45 U3, O-46·O-47·O-50 G1), 정합 감사 요약 `wt/_drafts/evidence/2026-10-20/offset_audit_summary.md`(이 계획 몫 A1·A3·A4·A5·B1~B5·C2·D1~D4·E1~E3). 정본 인용(다시 정의하지 않음): gain-budget v6.20(`plan/gb-v620` `f2579b2f` -- DEC-23, DEC-74, DEC-90, N3.8, LR6, N6.1, N6.3, N6.18 VB-1, N6.20 EO-1), oracle-portability v0.6.10(`plan/oracle-v0610` `64687b21` -- G-18, OP-3, OP-5, OP-6, PC-10, N3.9), offset-strategy v0.7(`plan/offset-strategy-v07` `5f99a49a` -- N3.3, matching 합성 제약 판정 위치 O-53 A2의 정본), headroom-chain v0.7.7(`plan/headroom-v077` `64c115ba` -- HC-O intended_region 칸). 전체 정합 검증 4차(`wt/_drafts/evidence/2026-10-20/full_audit4_summary.md`)와 사용자 결정 O-54·O-55를 같은 판에 반영했다. 직전 승인판은 v0.5.5(T-29~T-38)·v0.5.6(T-39)이고, 그 상태 문장은 history H1 '2026-10-20' 절로 옮겼다. 근거는 사용자 결정 T-1~T-39, O-23~O-53, offset-strategy S-1~S-12와 원문 7편(N8)이다.
> **이력**: 경위, 제안 원문 요지, 원문 검토 기록, 검증 반영 기록, 버전 이력은 [offset-trim.history.md](offset-trim.history.md)에 있다.
> **상위 계획**: [gain-budget-gmid-sizing.plan.md](gain-budget-gmid-sizing.plan.md). 이 계획은 상위 계획의 원칙(N1.4 NFR, N2 결정)을 그대로 따른다. 충돌하면 상위 계획이 이기고, 충돌은 N7에 올린다.
> **상위 O-202~O-212 전파**(v0.6.4, 상위 gain-budget v6.38.6 열다섯째 커밋): off 선언 소자의 판정 정의는 상위 gain-budget N3.6 '전도·포화 경계·`off` 선언 정본' (5)가 정본이다 -- 이 계획의 옛 'off 선언 대조·꺼짐 판정 = LUT I_off·off 유지 경계'는 그 정본이 이긴다(본문 해당 자리 정정). **TR card 착수 조건 추가**: LUT 확장(단자 전류 열 + VGS < 0 축 -- 상위 사용자 결정 O-212, 원칙 33) 결정과 off 소자별 `judged_by` 선언(사용자 몫 -- ratify와 같은 때). LUT 확장 작업은 상위 card PD-1(R10 PDK 루트 정의 필드) 뒤다(상위 N6.1 병합 순서 규칙 표 #20, 상위 사용자 결정 O-213).

---

## N0. 문서 안내

* **담는 것**: 목적·범위, 확정 결정, 요구, 엔진 반영 구조와 규칙, 적용 판정 방법, 단계(card 후보)와 완료 조건, 위험, 원문 근거, 열린 결정.
* **담지 않는 것**: 경위와 검토 과정. 이것은 history에 둔다.
* **값 원칙**: 이 문서에는 수치 상수를 두지 않는다.
  * 범위 배수 k, 잔여 offset V_res, trim 온도, 판정 온도 범위, 보정 루프 반복 상한은 사용자 선언값이다.
  * 판정 온도 범위는 spec에 한 번만 선언한다(T-34). 보고 sweep과 범위 판정은 그 선언을 참조하고, 이 문서와 코드에는 그 숫자를 적지 않는다.
  * (v0.7, O-258) σ 정확도 선언 r_σ(oracle MC σ 추정의 상대 표준오차 목표), metric별 trim 부담 예산, 승인된 σ_MC 선언(출처 = oracle MC 기록 id)은 사용자 선언값이다(N3.10·N3.11). MC 표본 수는 r_σ에서 유도하고 새 상수를 두지 않는다.
  * PDK별 오라클 사실(모델 경로, 불일치·온도 지정 방법, 공정 문서의 불일치 계수)은 oracle-portability 계획의 선언이다(N3.9). 이 계획은 값을 두지 않는다.
  * 방향 여유 Δ_T는 오라클이 잰 측정 기록이다(N3.8, O-1). 상수가 아니고 출처 지문과 함께만 쓴다. 엔진에는 변형 제약 입력으로만 들어간다.
  * 나머지는 엔진 해석값, LUT, PDK 선언에서 유도한다.
  * 회로 이름과 PDK 이름은 규칙에 넣지 않는다. sky130은 적용 사례로만 나온다.
  * 원문 수치(N8)는 인용하지 않는다.
* **인용 규칙**: 코드는 `파일:줄`로 인용하고 기준은 base `cfe2e31`이다. 경로에서 `skills/analog-gmid-design/`은 뺐고, `E/`는 `gmid_engine/`이다. 다른 계획은 절 번호·항목 ID와 브랜치·커밋으로 인용하고, 그 정의를 이 문서에 다시 적지 않는다(gain-budget N9.4 인용 규칙과 같음, 단일 정본).

### N0.1 용어

| 용어 | 정의 |
|---|---|
| σ_in | 엔진 `offset_in_sigma_mv`의 값이다. 모든 MOS의 게이트 오차원을 수반 해석으로 출력에 보내 합친 분산을 여기 방향 DC 극한 전달 A_dc로 입력 환산한 1σ 값이다. 정의는 gain-budget DEC-23(`offset_in_sigma_mv`)·N3.8을 인용한다(A_dc = 봉인점 DC 방정식의 여기 방향 DC 극한 전달, 오라클 쪽 A = `.tf` -- oracle-portability N3.9 `offset_in_sigma_mv` 행, O-43 D1 (d); 감사 A4). 국면 2에서는 합성 회로에서 계산하므로 DAC 소자의 mismatch가 들어 있다. (v0.7, O-258 (A)) σ_in은 trim 필요 판단·후보 탐색에만 쓰고, trim 사양은 σ_MC로 정한다 |
| σ_MC | (v0.7, O-258 (A)) 5단계 (2) SPICE 닫기 뒤 실현 점(실현 w_f·m -- 상위 DEC-108 (6))의 원본 회로를 oracle 네이티브 MC로 잰 입력 환산 offset 1σ다(측정 출처 = oracle MC 기록, 정의 = σ_in과 같은 양의 SPICE 정의 `.op` MC -- 상위 DEC-23·DE-Q3 (다)). σ_in과 정의는 같고 측정 출처가 다르다(축 = 엔진 손계산 대 oracle 측정, graph 규칙 3). trim 사양에 쓰는 값은 사용자가 승인한 **σ_MC 선언**(spec `offset_trim` 칸, 출처 = 그 MC 기록 id) 하나다 |
| r_σ | (v0.7) σ 정확도 선언. σ_MC 추정의 상대 표준오차 목표(spec `offset_trim` 칸, 사용자 값). 표본 수 n = 1 + ⌈1/(2·r_σ²)⌉(σ̂ 상대 표준오차 1/√(2(n − 1)) ≤ r_σ인 최소 n -- F-21의 기존 식, 입력만 엔진 분해능에서 이 선언으로 바뀜) |
| trim 사양 기록 | (v0.7) 엔진 밖 trim 구동기(G-12 자리)가 oracle MC 기록(σ_MC)·oracle `.dc` 계통 offset 기록(V_id*, OP-5)·spec k·V_res에서 내는 기록: 범위 R = k·σ_MC + \|V_id*\|, LSB 입력 환산 상한 = 2·V_res(DNL 없는 상한 -- 판정은 N3.4 잔여), 비트 수 하한 N_min = ⌈log2(R/V_res + 1)⌉(N3.4 필요조건). writer = 그 구동기 함수 하나. AI 제안의 근거이고 엔진 입력이 아니다(N3.10) |
| V_id* | 계통 offset. 정본은 gain-budget DEC-23의 **부호 있는 V_id* 한 칸**이다(사용자 결정 O-50 G1; 계산 O-46 (1)·O-47 -- ΔW 1차 감도 ΔV_out = −G⁻¹·ΔI, ΔI_k = ID_k·ΔW_k/W_k, V_id* = −ΔV_out/A_dc, '1차' 표기, 정확값 오라클 `.dc`). 이 계획은 크기 칸을 따로 두지 않고 제약 판정 때 \|V_id*\|로 비교한다. 옛 기호 V_sys·V_sys,s(크기 칸, `output_error_v`/A_dm)는 쓰지 않는다(감사 A1, 옛 정의는 history H1 2026-10-20) |
| z[n] | 감지 관측에 대한 수반 해의 노드 n 성분이다. 노드 n에 넣은 전류 I가 출력에 주는 값은 z[n]·I다(F-1) |
| 주입 쌍 | 입력 diff_pair 두 소자의 drain 넷 (n_p, n_n)이다(N3.2) |
| t | 주입 쌍에 차동 전류 +δ/2, −δ/2를 넣을 때 δ 한 단위의 입력 환산 전달이다. 정의는 t = (z[n_p] − z[n_n]) / (2·A_dc)이고 단위는 V/A다. A_dc는 σ_in 환산과 같은 양이다(DEC-23 인용, 감사 A4). 국면 2 값은 합성 회로의 봉인 점에서 계산한다 |
| I_u | 단위 셀 하나의 steering 전류다 |
| I_T | steering 총전류다. I_T = (단위 셀 수)·I_u이고, I_A + I_B = I_T는 코드와 무관하다(T-3) |
| δ | 차동 출력 I_A − I_B다. 단위 셀 하나가 A에서 B로 바뀌면 δ는 2·I_u만큼 변한다. 그래서 **I_LSB = 2·I_u**다. 단위 셀 수가 홀수(2^N − 1)이므로 δ는 I_u의 홀수배이고, **δ = 0 코드는 없다** |
| I_FS | δ의 양 끝 크기다. 단위 셀이 모두 한쪽이면 \|δ\| = I_T이므로 **I_FS = I_T**다 |
| N, m | DAC bit 수와 이진 하위 비트 수다. 상위 N − m 비트는 thermometer(단위 2^m·I_u 셀 2^(N−m) − 1개)다. 순수 이진은 m = N − 1과 같은 최악 전이를 가진다. (v0.7) N·m은 승인된 trim 파일의 선언값이다(N = 코드 입력 비트 수, m = 이진 하위 비트 수 -- N3.3) |
| σ_U | 단위 셀 전류의 상대 σ다(Bertotti 2012 σ_I,Rel). F-3 경로(σ_VGS·gm/ID)로 계산한다 |
| trim_dac | trim 소자의 구조 역할이다. 신호 경로 셀·블록 역할에서 빠지고, 바이어스·잡음·용량·mismatch 기여는 남긴다 |
| trim 파일 | (v0.7, O-258 (B)) `<회로>.trim.topology.json`(이름은 design). 원본 topology에 붙일 trim 구조의 **선언** 파일이다: `role: trim` 선언, 포트(주입·전원·bias·코드 입력), trim 소자 목록(원본 소자 스키마 F-7과 같은 키), 연결표(trim 포트 ↔ 원본 넷), 코드 입력 선언, 코드 상태 선언, 근거 칸(N3.3). AI가 의도 문서와 함께 제안하고 사용자 승인 뒤에만 로딩한다(원칙 15, FR-T4). 원본 topology.json은 바뀌지 않는다 |
| 합성 회로 | (v0.7) 합성 로더 블록 하나(writer 하나)가 원본 topology와 승인된 trim 파일에서 결정적으로 만든 회로 입력이다(실행마다 다시 만들고 디스크에 쓰지 않는다). spec 판정은 합성 회로에서 한다. 옛 '파생 topology'(`augment_trim` 산출)를 대체한다 |
| 소자 출처 칸 | (v0.7) 합성 회로의 소자마다 그 소자가 선언된 파일(원본 topology / trim 파일)을 적은 칸. writer = 합성 로더 하나, 선언 유래(추론 태그 아님 -- 원칙 14). `trim_dac` 역할(FR-T5)과 부담 변형(N3.11)이 이 칸을 READS한다 |
| 코드 입력 선언 | (v0.7) trim 파일의 디지털 입력 선언: 비트마다 게이트 넷(포트), on/off 레벨(레일 역할 참조 -- `supply_nets`, D-10), 비트 값 → 소자 on/off 표, on 스위치 영역 칸(triode/saturation -- O-53 B1 ratify 대상). 스위치의 on/off는 코드로 정해지는 **선언**이다(O-249 -- 엔진은 전류 크기로 off를 분류하지 않는다) |
| 코드 상태 선언 | (v0.7) trim 파일이 선언하는 평가 코드 벡터: 봉인 코드(중간 코드 δ = +I_u)와 포화 검사 코드(δ = −I_u, δ = ±I_T)(N3.5, D-17). 엔진은 코드를 찾지 않고 이 선언만 평가한다(N3.12) |
| trim 부담 | (v0.7, O-258) 같은 θ에서 원본만 변형의 metric과 원본 + trim(중간 코드) 변형의 metric의 차를, 그 metric 제약을 어기는 방향으로 잰 크기(≥ 0)다(N3.11) |
| 부담 예산 | (v0.7) spec `offset_trim`의 metric별 허용 저하 선언(사용자 값, 선택). 선언이 없는 metric은 부담 제약 없이 합성 회로 spec 통과만 본다 |
| 국면 | (v0.7 정의 갱신, 정본 offset-strategy N0.1) 국면 1 = 승인 기록 없음 -- 원본 topology로 trim 필요 판단·후보표, 그 뒤 엔진 밖에서 oracle MC·trim 사양 기록·AI 제안. 국면 2 = 승인 기록 있음 -- 합성 회로의 부담 사이징·닫기·잔여 MC |
| trim_decl | **(v0.7 폐지)** 옛 정의: spec trim 필드와 승인 기록의 선택(주입 쌍, 극성, N, m, on 스위치 영역)을 로더가 합친 `augment_trim` 입력. 선택·영역은 trim 파일 선언으로, spec 값은 spec `offset_trim` 칸으로 각자 자리에서 읽는다(합친 사본을 두지 않음 -- graph 규칙 4). 옛 행 원문은 history 'v0.7.0' |
| intended_region | 소자의 의도 영역 선언. 값 집합 {triode, off}, 선언 없음 = 포화(사용자 결정 O-53 B1). 칸의 정본은 spec 선언 triode 칸과 oracle-portability G-18 입력 스키마이고, 이 계획은 trim 소자의 값을 합성 로더가 코드 상태 선언과 코드 입력 선언에서 코드 상태마다 만드는 규칙만 둔다(N3.5, O-249) |
| T_j | 판정 온도. 그 실행 LUT 묶음의 측정 조건 `temp_c`다(design §5.3). 엔진 탐색과 엔진 제약 판정은 이 한 조건에서만 한다 |
| 판정 온도 범위 | offset·trim 잔여의 합격을 판정할 온도 구간이다. 사용자 선언값이고(T-34, 값은 T-14의 범위), spec의 offset 요구 안에 한 번만 선언한다(스키마 정본 offset-strategy N3.2). TR-7 온도 보고 sweep과 범위 판정이 모두 이 선언을 참조한다. T_j를 포함해야 한다 |
| 범위 판정 | SPICE 오라클이 판정 온도 범위의 온도 점에서 offset·trim 잔여를 재서 합격·불합격을 내는 것이다(T-29, N3.8.2) |
| Δ_T(metric) | 방향 여유. 같은 설계 점·같은 표본 집합에서 오라클이 잰 '판정 온도 범위의 최악값 − T_j 값'을, 제약을 어기는 방향으로만 잰 크기다(≥ 0). 엔진 제약 문턱을 그만큼 조인다(N3.8.3) |
| 보정 루프 | 엔진 탐색 → 범위 판정 → Δ_T 측정 기록 → 문턱을 조인 다음 변형 추가를 멈춤 규칙까지 되풀이하는 절차다(T-30, D-24 안 B, N3.8) |
| 오라클 능력 기록 | (PDK, 시뮬레이터) 조합에서 MC 불일치·온도 의존이 실제로 동작함을 확인 절차로 잰 기록이다. 형식·절차·유효성은 oracle-portability 계획(T-31, T-33)이 정한다. 이 계획에서는 범위 판정과 보정 루프의 전제다(N3.9) |

---

## N1. 목적·범위·요구

### N1.1 목적

지금은 랜덤 offset 사양을 입력쌍 면적(L·W)만으로 맞춘다. 이 기능은 그 대신 작은 입력쌍과 trim DAC의 조합을 엔진이 사이징할 수 있게 한다.

목표는 다음 두 조건을 만족하는 해를 (전력, 면적) front 위에서 찾는 것이다.
* trim 뒤 잔여 offset이 spec 목표 안에 든다.
* trim 보정 구간이 trim 전 offset 분포를 spec 수율 배수만큼 덮는다.

**(v0.7, 사용자 결정 O-258)** trim 사양(덮을 분포의 폭)은 엔진 손계산 σ_in이 아니라 실현 점의 oracle MC σ_MC로 정한다(손계산은 오차를 전제하고 SPICE로 확정한다 -- 원칙 2). trim 구조는 원래 topology에 붙는 별도 선언 파일로 두고 graph 정본에 합성되어 trim 소자임이 출처 칸으로 드러나며, 원래 회로 성능에 주는 영향(trim 부담)이 최소가 되도록 사이징한다.

**온도 범위 합격(v0.5, T-29~T-32)**: offset과 trim 잔여는 선언 온도 범위 전체에서 합격해야 한다. 이때 gm/ID 방법의 장점(작은 노력, SPICE와 작은 오차, 빠른 설계 -- 이번 개발의 가장 큰 이유, 사용자 취지 2026-10-16)을 지킨다.
* 엔진 탐색은 LUT 한 조건(T_j) 그대로다. 다온도 LUT로 엔진을 넓히지 않는다(기각 경위는 history H1 2026-10-16).
* 온도 범위는 SPICE 판정 단계에서 따진다. 불합격이면 오라클이 잰 여유로 엔진 제약 문턱만 조여 다시 돌린다(보정 루프, N3.8).
* 오라클은 능력 기록이 확인된 PDK·시뮬레이터에서만 범위를 판정한다(N3.9, 절차는 oracle-portability 계획).

### N1.2 범위

| 포함 | 제외 |
|---|---|
| 정적 offset의 전류 주입 trim이다. 패키지 뒤 한 온도에서 코드를 한 번 정한다고 가정한다 | 코드 저장 방식(OTP·퓨즈·레지스터)과 디지털 디코더 면적이다(T-1) |
| 주입 쌍 후보 계산·순위(엔진), trim 사양 기록(oracle MC, N3.10), trim 파일 스키마·합성 로더·소자 출처 칸·합성 회로 connectivity 표, 승인 흐름, trim 부담 판정(N3.11)이다(v0.7 -- 옛 '추천 구성, 파생 topology, `augment_trim`'은 O-258 (B)로 대체) | trim 알고리즘(코드 탐색·저장 -- 엔진 밖, N3.12), 측정·자기 trim 비교기, 생산 시험 흐름이다(Staudt 2011 §II.B의 비교기 잡음 모델 포함). AI의 trim 구조 제안 자체(엔진은 제안을 판정할 숫자와 관문만 낸다 -- DEC-110 역할) |
| 차동 전류 steering DAC의 단위 전류 유도, 보정 구간·잔여 판정, 단위 소자 W·L·gm/ID, 극성 규칙이다 | chopper·auto-zero 같은 동적 offset 제거다(Lu 2007, Zhou 2017 Fig.3) |
| trim 소자의 DC 바이어스·headroom·잡음·극점·mismatch 기여를 기존 해석으로 그대로 계산하는 것이다 | laser·저항 trim, 입력쌍 소스 저항 trim(Zhou 2017 Fig.2), 입력 단자 level shifter trim(Mohamed 2013)이다. 이것들은 비교 근거로만 쓴다 |
| offset spec 의미 전환이다. trim이 선언된 회로에서 σ_in은 덮어야 할 분포가 된다 | drift trim이다. CMOS에서는 offset이 drift에 비례하지 않아서 한 온도 offset trim이 drift를 보정하지 않는다(Kay 2024 §1.2, PDF p.7). 엔진에는 drift metric이 없다(F-6). 보고서에 이 한계를 적는다. v0.5에서도 trim은 한 온도에서 코드를 정한다. 남는 drift는 보정하지 않고, 범위 판정(T-29)이 그것까지 넣어 합격을 가린다 |
| library 13회로(상위 O-182 Q-LB1)의 적용 판정과 일반성 측정이다 | held-out 회로 확장이다. 상위 U-75 뒤에 한다 |
| **(v0.5)** offset·trim 잔여의 오라클 범위 판정과 SPICE 온도 보정 루프(N3.8), 오라클 능력 기록에 대한 의존 규칙(N3.9)이다. 능력 확인 절차 자체는 oracle-portability 계획 범위다 | 다온도 LUT와 엔진 안 다온도 탐색이다(T-29 '엔진 탐색은 LUT 한 조건 그대로'). GBW·PM·포화 등 다른 metric의 온도·코너 범위 판정도 이번에는 제외한다(T-32) |

### N1.3 기능 요구

| ID | 요구 |
|---|---|
| FR-T1 | **spec trim 선언**(T-1): 회로 spec에 trim 선언을 새로 둔다. 필드는 잔여 offset 목표 V_res, 수율 배수 k(또는 수율 목표, D-2 -- k의 출처는 offset-strategy XS-6으로 요구 `coverage_multiple`), trim 온도 조건이다. **(v0.7, O-258)** 칸 셋을 더한다: σ 정확도 선언 r_σ(국면 1부터), σ_MC 선언(승인 뒤 -- 값 출처 = oracle MC 기록 id, 사용자 승인값), metric별 부담 예산(선택, N3.11). 칸 이름·형식은 design(DEC-68). 값과 출처는 사용자 몫이다. 선언이 없는 실행은 완료 조건 (1)의 변경 종류 기준(발동하지 않는 입력 = 순수 리팩터링 필드별, 결정성 = 비트 동일 -- O-34 (1), 감사 E1)으로 판정한다 |
| FR-T2 | **국면 1 후보표**(엔진): 주입 쌍(N3.2)마다 다음을 결과 JSON에 낸다. 후보 규칙은 구조 규칙이고 회로 이름을 쓰지 않는다.<br>• front 위 t의 범위와 부호<br>• 극성별 headroom 창<br>• 잡음 영향(N3.7)<br>• trim 필요 판단 값: front 점마다 k·σ_in + \|V_id*\|와 요구 `offset_in_max_v`의 대조(보고 -- 판정 아님, 최종 사양은 σ_MC)<br>(v0.7, O-258) 옛 '추천 N·m', '그 구성의 파생 topology와 connectivity 표'는 내지 않는다 -- N·m은 trim 사양 기록(FR-T13)과 AI 제안(trim 파일)이, connectivity 표는 승인 전 합성 회로 표(FR-T4)가 대신한다 |
| FR-T3 | **trim 파일과 합성 로더**(O-258 (B), 옛 T-2 `augment_trim` 대체): trim 파일 스키마(N3.3)를 두고, 로더 블록 하나가 원본 topology + 승인된 trim 파일을 결정적으로 합성해 합성 회로와 소자 출처 칸을 쓴다(writer 하나). 원본 파일·trim 파일은 고치지 않는다. 엔진은 trim 구조를 만들지 않는다(구조는 AI 제안·사용자 승인 선언) |
| FR-T4 | **승인 흐름**(T-2의 승인 게이트 유지, O-258 (B), 원칙 15): AI가 trim 파일·의도 문서·근거(엔진 후보표 id, trim 사양 기록 id)를 제안한다. 합성 로더로 만든 합성 회로 connectivity 표(`assets/topology_to_markdown.py` 형식 -- 같은 합성 함수를 부름, 둘째 합성 구현 금지)를 사용자가 보고 승인한다. 승인 기록이 있을 때만 trim 파일이 로딩된다. 결속 규칙은 N3.3이다 |
| FR-T5 | **구조 역할 `trim_dac`**: S1·S1v가 소자 출처 칸이 trim 파일인 소자를 신호 경로 셀·블록 역할(`input`·`load`·`mirror`·`tail_source` 등)에 넣지 않는다(역할 유도 입력 = 출처 칸 READS -- 이름·태그 추론 없음). DC writer, 잡음원, MNA 용량 스탬프, offset 해석의 mismatch 원에는 그대로 포함한다 |
| FR-T6 | **DAC 규칙**(N3.4): 국면 2에서 trim 파일이 선언한 N·m에 대해 단위 전류 I_u(θ, T-7)를 정하고, 보정 구간·잔여를 제약으로 판정한다(DNL은 잔여 판정 안에 들어간다). 불가능하면 `trim_config_infeasible`로 멈추고, AI가 trim 파일을 다시 제안해 재승인받는다(엔진이 N·m을 바꾸지 않음) |
| FR-T7 | **offset spec 의미 전환**(N3.6) |
| FR-T8 | **끝 코드 DC 검사**(N3.5, 사용자 결정 O-53 A3): 보정 구간 판정과 같은 봉인점 1차 감도 추정으로 한다(엔진 안 고정 기하 DC 균형 풀이 없음). 정확값은 오라클 `.dc` 코드 스윕이다 |
| FR-T9 | **보고**: 다음을 결과 JSON과 보고서에 적는다.<br>• trim metric, 후보표, 승인 기록 id<br>• (v0.7) trim 파일 sha256, trim 사양 기록 id와 그 oracle MC 기록 id(표본 수·r_σ), 부담 표(metric마다 원본만 값·합성 회로 값·부담·예산 -- 값은 각 변형 스냅샷의 기록 참조), 부담 재풀이 여부(N3.11)<br>• 'drift·1/f는 trim 대상 아님' 문구<br>• 합격 조건(온도)<br>• 판정 입력 DC 한 점이라는 한계<br>• **단일 온도 trim 한계**(T-5, v0.5에서 T-29로 고침): 'trim 코드 결정과 엔진 판정은 T_j·LUT 코너 한 조건이다. CMOS offset trim은 drift를 보정하지 않는다(Kay 2024 §1.2 PDF p.7; Zhou 2017 p.1 e-Trim은 패키지 뒤 trim이라 패키지 응력 이동을 피함). offset·trim 잔여의 합격은 오라클 범위 판정(판정 온도 범위)이 정한다.' 범위 판정 결과, 보정 루프 이력(N3.8.6), 오라클 능력 기록 id를 함께 싣는다. 범위 판정을 하지 못한 실행(능력 기록 없음, 판정 불능)은 '범위 미판정'으로 적고 합격으로 세지 않는다 |
| FR-T10 | **범위 판정**(T-29, N3.8.2): offset 요구 판정과 trim 잔여의 합격을 오라클이 판정 온도 범위에서 판정한다. 범위는 사용자 선언값이다. 엔진 탐색과 엔진 판정은 T_j 한 조건 그대로다 |
| FR-T11 | **SPICE 온도 보정 루프**(T-30, N3.8): 범위 불합격이면 metric별 Δ_T를 측정 기록(출처 지문 포함)으로 만들고, 구동기가 대조한 뒤 문턱을 그만큼 조인 다음 변형을 같은 실행 계획에 추가한다(D-24 안 B). 불합격 몫 분해로 크기 조정이 불가능하면 다시 돌리지 않고 보고·정지한다. 멈춤 규칙과 반복 상한은 N3.8.5다 |
| FR-T12 | **오라클 능력 의존**(T-31, T-33, N3.9): 범위 판정과 루프는 유효한 오라클 능력 기록이 있는 (PDK, 시뮬레이터) 조합에서만 허용한다. 기록이 없거나 낡았으면 거부한다(fail-closed). 능력 확인 절차·PDK 기술자·확인 test는 oracle-portability 계획이 소유한다. (v0.7) trim 사양을 정하는 oracle MC(FR-T13)도 같은 능력 기록 전제다(T-31) |
| FR-T13 | **MC 시점과 trim 사양 기록**(O-258 (A), N3.10): 국면 1의 원본 회로가 5단계 (2) SPICE 닫기를 지난 실현 점(실현 w_f·m)에서 oracle 네이티브 MC로 σ_MC를, oracle `.dc`(OP-5)로 V_id*를 잰다. 표본 수 = r_σ에서 유도(N0.1). 엔진 밖 trim 구동기 함수 하나가 trim 사양 기록(R, LSB 상한, N_min)을 쓴다. 기록은 AI 제안·사용자 승인의 근거이고 엔진 입력이 아니다(엔진은 oracle 결과 파일을 읽지 않음 -- X-23·S-3). 능력 기록 없음·r_σ 미선언·닫기 미완료 점이면 거부(fail-closed) |
| FR-T14 | **trim 부담**(O-258, N3.11): 국면 2에서 같은 θ의 원본만 변형 대 합성 회로(중간 코드) 변형의 metric 차를 부담으로 재어 부담 예산을 제약으로 걸고 trim 소자를 사이징한다(목적 = 주입 넷 부가 C·부가 컨덕턴스·trim 전력 최소). 부담 제약을 만족하는 trim 해가 없으면 원본 θ까지 합성 회로 기준으로 다시 푼다. offset-strategy 실행 계획 변형 틀을 재사용한다(새 인프라 금지) |
| FR-T15 | **디지털 코드**(O-258, N3.12): 코드 탐색·저장은 엔진 밖이다. 엔진은 trim 파일의 코드 입력·코드 상태 선언만 읽는다. oracle 검증 = MC 표본마다 최적 코드를 고른 뒤 잔여 분포 ≤ V_res(완료 조건 3) |

### N1.4 비기능 요구

상위 계획 N1.4의 NFR-1~NFR-6과 N2.2 작업 원칙을 그대로 적용한다. 이 기능에서는 특히 다음을 강제한다.

| ID | 요구 |
|---|---|
| NFR-T1 | **topology 무관**: 후보 규칙, 역할 유도, 설계식은 구조와 해석값만 읽는다. 회로·소자·넷 이름 리터럴은 금지다. library 13회로에서 선언이 없으면 무동작임을 측정해 증거로 낸다 |
| NFR-T2 | **상수 발명 금지**: 범위 배수, DNL 배수, 잔여 여유에 경험 상수를 박지 않는다. 사용자 선언값(V_res, k)을 참조하거나 정의에서 유도한다. 원문 수치는 인용하지 않는다 |
| NFR-T3 | **graph 단일 정본**: 노드 수반 벡터 z, t, 후보표, DAC 유도값, **Δ_T가 들어간 변형 제약 입력**은 Circuit State Graph 필드다. 안 B(D-24)에서 Δ_T는 변형 제약 입력 하나로만 들어오고 writer도 하나다(N3.8.7 표). 문턱 합성은 그 입력을 읽는 제약 행 계산 한 곳에서만 한다(사본 금지). 각 필드는 writer가 하나이고 입력 버전을 함께 기록한다(상위 DEC-83). (v0.7) 합성 회로와 소자 출처 칸은 합성 로더 블록 하나가 실행마다 원본 topology·trim 파일에서 만들고 디스크 사본을 두지 않는다(상위 NFR-2와 정합). trim 사양 기록(writer = 엔진 밖 구동기 함수 하나)과 부담 문턱 항목(writer = 같은 구동기의 변형 추가 한 번 -- N3.11)도 writer가 하나다. 같은 값을 다른 자리에서 다시 계산하지 않는다 |
| NFR-T4 | **결정성**: (v0.7) 합성 로더는 같은 입력(원본 topology·trim 파일 바이트)이면 비트 동일한 합성 회로를 낸다. trim 파일의 소자·내부 넷 이름은 trim 파일이 선언한 그대로 쓰고(엔진이 이름을 만들지 않음), 원본 이름과 충돌하면 거부한다(상위 NFR-4). 옛 문언('`augment_trim`은 … 이름은 정렬된 규칙으로 만들고')은 history 'v0.7.0' |
| NFR-T5 | **만들면 배선**: 후보 계산, 변환, 승인 검사, metric은 엔진 진입점의 실제 경로에 배선한다. 배선이 불가능하면 사용자 승인을 받는다 |
| NFR-T6 | **작성자≠검증자**: design 문서는 독립 검증 agent가 검증한다. test·기대값·판정 기준은 구현자가 소유하지 않는다. 판정자는 SPICE 오라클이다(코드 스윕 + Monte-Carlo) |
| NFR-T7 | **공정·시뮬레이터 무관**(T-31, T-33): 이 계획이 만드는 것(범위 판정 규칙, Δ_T 선언·지문, 루프 도구)에 PDK 이름, 모델 변수 이름, 단위 배율, 소자 subckt 이름, 시뮬레이터 이름·방언 리터럴을 두지 않는다(리터럴 lint로 확인). PDK·시뮬레이터에 따라 다른 사실은 오라클 쪽 선언(oracle-portability 계획)에서만 읽는다 |
| NFR-T8 | **재사용 원칙과 정합**(상위 NFR-2, 사용자 결정 2026-10-15 '실행 사이 재사용 제거'와 그 취지 "처음 topology를 실행할 때 계산하고 그 값을 나머지 최적화에서 재사용"): 엔진은 이전 실행의 결과 JSON·S3·front 점을 읽지 않는다. 이전 반복에서 넘어가는 것은 대조를 통과한 Δ_T뿐이다. 반복은 실행 계획 안의 변형이다(D-24 안 B, 사용자 결정 T-35). 그래서 단계 A·S0·블록 결과 색인을 실행 계획 수명 동안 공유하고, 문턱에 의존하는 블록만 다시 계산한다(N3.8.7) |
| NFR-T9 | **순차 실행**: 보정 루프 구동기는 엔진 계산과 오라클 실행을 차례로 하나씩 돈다(동시에 띄우지 않음). 오라클 안의 시뮬레이터 병렬 수는 실행 설정의 선언값을 따른다. 다른 작업과 메모리를 나눠 쓰는 환경이라서다 |

---

## N2. 확정 결정

| ID | 결정 | 출처 |
|---|---|---|
| T-1 | spec 필드: trim 뒤 잔여 offset 목표 V_res, 수율 배수 k(또는 수율 목표), trim 온도 조건을 spec에 새로 둔다. 값은 사용자 몫이다. 코드 저장 방식(OTP·퓨즈·레지스터)은 아날로그 sizing 범위 밖이다 | 사용자 2026-10-15 "권고대로 해" |
| T-2 | 파생 topology 승인: 엔진이 결정적 변환 `augment_trim(topology, trim_decl)`로 trim 소자를 붙인 파생 topology와 출처 기록을 만든다. 주입 노드 후보와 순위는 엔진이 수반 해석으로 계산해 제시한다. 사용자가 승인(ratify)한 뒤에만 쓴다. topology.json은 엔진이 고치지 않는다. **(v0.7 → O-258 (B)로 대체)**: 파생 topology 생성(`augment_trim`)은 원본 topology + trim 파일 두 선언 합성으로 바뀐다. 남는 것 = 승인 게이트·원본 불변·후보 순위는 엔진 계산(N3.1·N3.3) | 같음 |
| T-3 | DAC 구조 기본안: 차동 전류 steering 이진 가중(I_A + I_B 일정)이다. DNL이 부족하면 상위 비트만 thermometer로 바꾼다 | 같음 |
| T-4 | 착수 시점: 엔진 구현은 NFR-4 card 2 → XRUN-F1 A·B·C 뒤에 한다. 계획 문서 초안과 원문 검토·보관은 지금 병렬로 한다(엔진 코드 무변경) | 같음 |
| T-5 | 온도 한계: 판정은 27 °C·TT(엔진 합격 조건과 같음)다. 보고 전용 검증으로 다음을 낸다. 샘플마다 27 °C에서 trim한 뒤 코드를 고정하고 온도를 sweep한 잔여 offset, 코너별 보정 구간, 끝 코드 headroom의 온도 의존, 엔진 σ_in 대 SPICE σ_in 일치. 결과 보고서에 단일 온도 trim 한계를 명시한다. **v0.5: offset·trim 잔여의 합격은 T-29로 바뀌었다**(엔진 판정·trim 코드 결정은 여전히 한 조건, 고정 코드 온도 sweep은 trim 잔여에서 판정이 됨. 코너별 보정 구간·끝 코드 headroom 온도 의존은 보고 전용 그대로) | 사용자 2026-10-15 "1~3 권장대로"(원문 `wt/_drafts/user_decisions.md` 'NFR-4 card 2·offset trim 결정' T-5) |
| T-6~T-28 | 계획 v0.4 승인(T-6)과 design 단계 결정(T-7~T-28). 반영 위치는 design `offset-trim.design.md` §1.1·§18.1이다 | 원문 `wt/_drafts/user_decisions.md` 2026-10-15 절들 |
| T-29 | **offset·trim 잔여 합격 = 온도 범위 판정(SPICE 오라클)**. T-6(범위는 보고만 -- 그 내용의 출처는 T-5이고 T-6은 그것을 담은 계획 v0.4 승인이다)과 상위 DEC-96 (3)(합격 = TT 27 °C 한 조건)을 이 범위 안에서 바꾼다. 엔진 탐색은 LUT 한 조건 그대로다 | 사용자 2026-10-16 "2번의 경우 sky130으로 한정하면 안 돼. 공정무관한 방법론이어야 해. 그래야 다른 fab에서도 사용할 수 있으니까. 이 부분을 수정하고 모두 권고대로 진행해"(원문 `wt/_drafts/user_decisions.md` '## SPICE 온도 보정 루프') |
| T-30 | 'SPICE 온도 보정 루프'를 이 계획의 보완으로 진행한다. 엔진 탐색 → 오라클 범위 판정 → 불합격이면 metric별 방향 여유 Δ_T(측정 선언, 출처 지문, 지문 불일치 무효) → 제약 문턱을 조여 재실행 → 반복. 불합격 몫 분해 (i)(ii)(iii)로 크기 조정이 불가능하면((ii) 지배) 반복 없이 보고·정지. 멈춤 = Δ_T 변화가 오라클 측정 분해능 안이거나 front가 빔. **v0.5.6(T-39)**: 측정 분해능은 matching σ 항 = MC 표준오차, trim 잔여 = 오라클 DC 풀이 허용오차를 입력 환산으로 전파한 값이다(고정 표본 집합이라 추출 잡음 없음). 원문의 '(MC 신뢰 구간)'을 이렇게 고쳤다. 반복 상한 = 사용자 선언값. 여유는 k·σ 경계 기준. model_error(상위 DEC-72)의 분해능 용도는 상위 사용자 결정 O-178로 폐지(DEC-72 = 엔진·oracle 대조 기록). 순서 = TR-7 뒤 | 같음(분해능 문언은 T-39) |
| T-39 | trim 잔여 Δ_T 수렴 분해능 = 오라클 DC 풀이 허용오차를 입력 환산으로 전파한 값이다(새 상수 없음, design S7-1 (가)). design X-T17~X-T20을 수용한다 | 사용자 2026-10-16 "모두 권고대로"(코디네이터 전달) |
| T-31 | 선행 card는 sky130 한정이 아니라 **공정 무관 방법론**이다. 어떤 PDK·시뮬레이터 모델이든 MC 불일치·온도 의존이 실제로 동작하는지 확인하는 절차(PDK 기술자 선언 + 확인 test)다. 회로·PDK 이름을 규칙에 넣지 않는다. sky130은 첫 적용 사례일 뿐이다 | 같음 |
| T-32 | 처음 범위 = offset·trim 잔여만. GBW·PM 등 코너 확장은 나중이다 | 같음 |
| T-34 | 판정 온도 범위 = T-14에서 정한 범위다. spec에 한 번만 선언한다(정본 하나, offset 요구 안 칸, 스키마 정본은 offset-strategy N3.2). TR-7 온도 보고 sweep과 보정 루프 범위 판정이 모두 그 선언을 참조하므로, spec에서 바꾸면 둘 다 함께 바뀐다(숫자 사본 금지) | 사용자 2026-10-16 "D-18은 이전에 정했던 온도범위를 쓰고, 이 범위를 스펙에서 바꾸면 연동되어 바뀌는 것이 일관될 것 같아." |
| T-35 | D-19(반복 상한 = 실행 설정, 기본값 없음, 선언 없으면 첫 범위 판정만), D-22(정지·보고까지), D-24 안 B(반복 = 실행 계획 안의 변형), X-20 정의(O-3)를 권고대로 확정한다. oracle-portability v0.4와의 충돌(그 계획 X-16)은 G-14를 네이티브 MC 표본 안에서 풀어 해소한다. 같은 seed 표본을 온도마다 다시 재고 꼬리의 실제 표본으로 범위 판정하며, 결정적 벡터 대안과 PC-11 요구는 철회한다. D-20·D-25는 대기였다(주석: 뒤에 T-36으로 닫힘) | 사용자 2026-10-16 "D-20, D-25를 제외하고는 권고대로 진해"(코디네이터 전달) |
| T-36 | D-20 (가): 사용자 선언 결정적 규칙으로 front 점 하나를 고른다(규칙 값은 시험 회로 실행 때 선언 가능). D-25 (c) 출처 무결성 + (c-2) 엔진 밖 구동기 대조 | 사용자 2026-10-16 "D-20, D-25, X-15,X-17은 권고대로 해"(코디네이터 전달) |
| T-37 | X-23 수용: 직전 변형 결과로 잰 Δ_T를 다음 변형 입력으로 넣는 것은 S-3 취지 안이다(offset-strategy XS-18) | 사용자 2026-10-16 "모두 권고대로 해"(코디네이터 전달) |
| (관련) S-11·S-12 | offset-strategy 사용자 결정이다. S-11: card OS-V(matching 유도 제약에 오라클 측정·`verified_by`, OS-2·oracle-portability 코어 뒤, TR-TL 앞). S-12: XS-16(실행 중 변형 추가로 목록이 늘어남), XS-17(공개 진입 `run_plan` + 세션 인터페이스, 사슬 하나), XS-18(= X-23), XS-19(보정 루프 동안 메모리 동시 점유, 반복마다 메모리 보고, OS-L 병합 전 반복당 색인 크기 측정) 허용 | 원문 `wt/_drafts/user_decisions.md` S-11·S-12 |
| T-33 | SPICE 오라클은 시뮬레이터 무관이어야 한다(T-31 공정 무관과 함께). 수정은 bkit 순서(계획 → design → 구현 → 판정)로 한다. **이 계획에서의 뜻**: T-31 절차·PDK 기술자·확인 test는 새 계획 oracle-portability가 소유하고, 이 계획은 능력 기록 의존만 둔다(코디네이터 범위 조정 2026-10-16) | 사용자 2026-10-16 "현재 구현되어 있는 spice 오라클도 simulator 무관한 것이어야 해. 이걸 확인하고 수정이 필요하면 수정해."(원문 `wt/_drafts/user_decisions.md` T-33) |
| O-53 | (v0.6) 이 계획 몫: **A2** matching 합성 제약 판정 위치(정본 offset-strategy v0.7 -- 이 계획은 인용, trim 방식은 A3 보정 구간으로 판정), **A3** 엔진 안 고정 기하 DC 균형 풀이(Newton) 삭제 -- 보정 구간·끝 코드 포화 = 봉인점 1차 감도 추정(코드 상태 간 trim 주입 전류 변화 ΔI를 −G⁻¹·ΔI로 옮김, off 소자는 G 기여 없음), 정확값 = 오라클 `.dc` 코드 스윕(원래 취지와 다름 X-29), **B1** intended_region {triode, off}·`augment_trim` 코드 상태별 생성·on 스위치 영역 선언 칸·선언 대조 거부·off 소자 LUT·gm/ID 경로 제외(G-1 해소, X-30), **B2** 온도 점 전도 판정 입력 출처(X-31), **B3** offset 기준 정의 자리 = DEC-23 하나, PC-10 = OP-5 `offset_sys_mv` `.dc`를 온도 조건에서 돌린 것(G-6·G-15 닫힘; 이동의 기준점 V_id,0도 DEC-23 '이동의 기준점'(v6.21 `54a3a328` 223행) 하나 -- 사용자 결정 O-59 (4) DV-13, 이 계획은 인용) | 사용자 2026-10-20 "권고대로 진행해"(원문 `wt/_drafts/user_decisions.md` O-53 행) |
| O-46·O-47·O-50 G1 | 계통 offset 정본 = gain-budget DEC-23 부호 있는 V_id* 한 칸(ΔW 1차 감도, A_dc 환산). 이 계획의 V_sys·V_sys,s·크기 칸·`offset_systematic` 인용을 지운다(감사 A1) | 원문 같은 파일 O-46·O-47·O-50 행 |
| O-45 U3 | 계통 offset 선언 제약은 단위 9 전 sizing W, 단위 9 뒤 실현 W로 다시 판정하고 위반 점은 front에서 빼고 비지배 재필터한다. 보정 구간 하한의 \|V_id*\|도 같은 판정 W 규칙이다(감사 A5, N3.4 '판정 W') | 원문 O-45 행 |
| O-34 | 변경 종류별 판정 기준(정본 gain-budget N6.3). 완료 조건의 '비트 동일'을 변경 종류 표시로 바꾸고(감사 E1), TR-7·TR-TL 판정에 동작 변경 네 다리와 모델 오차 규칙(DEC-72)을 쓴다(감사 B5, N6)(→ 상위 O-178: 모델 오차 판정 규칙 폐지, SPICE 다리 = oracle 판정) | 원문 O-34 행 |
| O-44 | EO-1(gain-budget N6.20) = 엔진 점 → oracle 입력 생산자 하나. 이 계획의 오라클 입력도 그 생산자로 내고(감사 B4), 동작 변경 card의 완료 판정은 EO-1 뒤다(감사 D2, N5) | 원문 O-44 행 |
| O-249 | off는 선언으로만 존재한다(상위 DEC-107). trim 스위치 off는 사용자 선언(이 계획에서는 승인된 trim 파일의 코드 입력·코드 상태 선언)이고 `judged_by`·G2-a·oracle이 판정한다. 전류 크기·문턱으로 off를 분류하지 않는다 | 원문 O-249 행 |
| O-255·O-256 (상위 DEC-110) | AI 설계·레이아웃 5단계: (1) 사이징 + floorplan 추정 (2) SPICE 닫기 (3) floorplan 확정(설계 확정) (4) 상세 레이아웃(AI, 엔진 관여 0) (5) 확인 루프. 역할: 엔진 = 숫자와 관문, AI = 판단과 생성 스크립트·의도 문서, AI는 엔진 수치를 대신하지 않음. 이 계획의 자리는 N3.10 | 원문 O-255·O-256 행, 상위 gain-budget v6.39.0 DEC-110(master 병합 `57a014b2`) |
| O-257 (상위 DEC-108) | 해법 S: w_f 이산 칸, 정합 묶음 공유, 탐색 = 연속 W, 실현(front 점) = 정수 m. 이 계획에서 '실현 점'은 DEC-108 (6) 실현 평가 점이다(oracle MC의 입력 기하) | 원문 O-257 행 |
| O-258 | **offset MC 시점 + trim 구성**(사용자 "동의해", 2026-11-07). (A) 엔진 σ_in = trim 필요 판단·탐색, (2) 닫기 뒤 oracle MC(실현 w_f·m)로 σ 실측 → trim 사양(범위 = k·σ_MC + \|계통 offset\|, LSB ← V_res, 비트 수), 사용자 승인, 합성 회로로 (1)(2) 재실행(trim 뒤 잔여 MC), (3) 전 trim 포함 확정, (5) 뒤 MC·계통 offset 확인만, 표본 수 = σ 정확도 선언 유도(상대 오차 ≈ 1/√(2N)), 선행 = oracle MC 능력 기록(T-31). (B) 원래 topology 불변, trim 파일(role: trim, 포트, 연결표)을 AI가 의도 문서와 함께 제안·사용자 승인 뒤 로딩(원칙 15, FR-T4), 로더 블록 하나가 결정적 합성(writer 하나), 소자 출처 칸, 코드 비트 = 디지털 입력 선언, 스위치 on/off = 코드가 정하는 선언(O-249), spec 판정 = 합성 회로, trim 부담 = 같은 θ 원본만 대 원본 + trim(중간 코드) 차(offset-strategy 변형 틀), 부담 예산 = spec 선언(없으면 합성 회로 spec 통과만), trim 사이징 목적 = 주입 넷 C·컨덕턴스·trim 전력 최소, 제약 = 범위·LSB·부담, 부담 위반이면 원본 θ까지 재풀이, 디지털 코드 탐색·저장 엔진 밖, 첫 구현 = 기존 전류 주입 DAC, `augment_trim`은 두 파일 합성으로 대체. 이 계획 반영: N3.1·N3.3·N3.4·N3.5·N3.10~N3.12·N5, 바뀌는 결정 = N7.2 'v0.7' 표 | 원문 `wt/_drafts/user_decisions.md` O-258 행 |

**v0.5 결정과 관련 계획의 관계**:
* offset-strategy S-1(요구 `offset_requirement`, 방식별 유도 제약), S-5·S-6(XS·DS-U 승인)은 그대로다.
* **S-9 'T-30 연결'(2026-10-16 사용자 "W-1,F-1,T-30을 권고대로 진행")**: 보정 루프(Δ_T)는 이 계획이 소유한다. offset-strategy는 matching 유도 제약의 문턱 = `offset_in_max_v` − Δ_T(선언 여유가 있을 때)라는 연결점만 정의한다. 그래서 T-29의 'offset 판정'은 S-1의 matching 유도 제약이다(X-21, 결정됨). 그 제약의 판정 위치(커널 k·σ_in ≤ `offset_in_max_v`, front k·σ_in + \|V_id*\| ≤ `offset_in_max_v`를 ΔW 1차 값으로, 단위 9 뒤 실현 W로 재판정, 위반 점 front 제외·비지배 재필터)는 사용자 결정 O-53 A2이고 정본은 offset-strategy v0.7 N3.3이다(인용만).
* S-7(계획과 다르면 계획부터 고쳐 bkit 절차), S-8(PD-1~PD-8, 특히 PD-1 '변형 제약 별도 입력 derived'), S-10(PD-9)은 offset-strategy 계획 v0.5의 결정이다. 이 계획이 거기에 기대는 곳은 실행 계획의 변형 제약 입력 형식(D-24 안 B)과 OS-2 순서(N5)다.
* S-3(엔진은 이전 실행 결과를 입력으로 받지 않음)과의 관계는 N3.8.7이다.
* 실행 계획(S-2, 변형 = (topology 변형, 제약 집합))과의 관계: 보정 루프 반복 = 실행 계획 안의 변형이다(D-24 안 B, 사용자 결정 T-35, N3.8.7). 실행 중 변형 추가 인터페이스는 offset-strategy 계획 연결 항목이다.

---

## N3. 엔진 반영 구조

### N3.0 현황 사실(읽기 확인, base `cfe2e31`)

| ID | 사실 | 근거 |
|---|---|---|
| F-1 | (v0.6에서 history H3로 옮김 -- 옛 `offset_analysis` 사실, 감사 E3). σ_in의 정의는 gain-budget DEC-23 인용, 환산 이득은 A_dc다(N0.1) | history H3 |
| F-2 | 노드별 수반 벡터 z는 밖으로 나오지 않는다. 지역 `state`에만 있고, 결과는 소자별 `z_ohm` = z[s]−z[d]뿐이다. t를 계산하려면 z를 graph 필드로 노출하는 엔진 변경이 필요하다 | `E/metrics/offset_analysis.py:95-100`, `E/metrics/aux_types.py:110-134` |
| F-3 | σ_VGS는 Pelgrom 상수식이 아니다.<br>• LUT 감도 열 DVGS_k에 PDK bin slope를 곱해 RSS하고, √(W_ref/W)로 기하 환산한다.<br>• 폭이 bin 최대를 넘으면 finger로 나누고 σ/√n으로 계산한다.<br>• slope는 graph 필드 `MismatchSource`에서 읽는다.<br>• 전류 mismatch σ(ΔI/I) = √((gm/ID_a·σ_a)² + (gm/ID_b·σ_b)²)는 `mirror_ratio`에 있다 | `E/metrics/device_sigma.py:17-33`, `E/lut/mismatch_sigma.py:5`, `E/metrics/mismatch_field.py:14-17`, `E/metrics/mirror_ratio.py:9, :36` |
| F-4 | `iv_matching_l.matching_bounds`는 **출발값 전용**이다(EP-7). 판정은 봉인 스냅샷의 `offset_in_sigma_mv`·`offset_excess`가 한다.<br>• L 하한은 `offset_in_sigma_mv <=`가 있을 때만 켜진다.<br>• `offset_excess <= E`는 부하 gm/ID 상한으로 간다.<br>• 부하 역할은 `mirror`·`diode_load`·`load`이다 | `E/search/iv_matching_l.py:5-16, :106, :120-125`, `E/search/_helpers_guard.py:15-29` |
| F-5 | 입력 셀은 graph 필드 `metric_structure`의 `input_cells`다. S1v transfer 뷰 gain 블록 가운데 (stage, key)가 가장 작은 블록의 `ROLE_INPUT` 소자다. 잡음 쪽(`noise_decl`)에도 같은 규칙의 두 번째 구현이 있다. 이 기능은 `metric_structure` 필드 하나만 읽는다 | `E/metrics/metric_structure.py:30-47`, `E/search/noise_decl.py:9` |
| F-6 | spec offset metric은 `offset_in_sigma_mv`(1σ), `offset_excess`, `offset_sys_mv`이다. **수율·3σ·drift·온도 필드는 없다.** 제약 항목 키는 `metric, op, value, view, source` + `value_from_constraint`·`value_from_file`이다. 합격 조건은 TT 27 °C 한 조건이다(상위 DEC-96 (3)) | `E/metrics/registry.py:56-58`, `E/authoring/spec_constraints.py:54-55`, `E/authoring/_spec_fields.py:25`, `E/authoring/spec_schema.py:22-33` |
| F-7 | topology 소자 키는 `name, kind, drain, gate, source`(+`bulk`)뿐이고, 그 밖의 키는 거부한다. 역할은 엔진이 유도한다. 파생 topology 기제는 없다(비어 있지 않은 `linked_topology_files`는 거부). `ideal_sources`와 `bias_inputs`는 선택 키다 | `E/authoring/devices.py:17-19`, `E/authoring/topology_schema.py:18-23`, `E/authoring/linked_files.py:21-25` |
| F-8 | `<name>.structure.json`은 승인 사실 파일이다(`topology_hash`, `rule_hash`, `facts[...approval_id]`).<br>• `topology_hash`가 현재 `topology_fp`와 다르거나 `rule_hash`가 현재 `structure_rule_fp()`와 다르면, 사실을 적용하지 않고 `structure_fact_stale`(**review_needed**)로 되돌린다. 정지하지 않는다.<br>• concept 어휘는 닫혀 있고 8개다.<br>• library에서 이 파일이 있는 회로는 current_reuse_telescopic_ota, nmcnr_amplifier다 | `E/graph/structure_load.py:14-15, :148`, `E/graph/s1v_values.py:31-33`, `assets/library/*.structure.json` |
| F-9 | `rule_fp = structure_rule_fp()`는 단계 A에서 구조 파일 로드에 쓰인다. S1·S1v 규칙 파일이 바뀌면 이 지문이 바뀐다 | `E/pipeline/stage_a.py:205-207` |
| F-10 | spec `meta.topology_fp`가 topology의 `connectivity_fp`와 다르면 `topology_fp_mismatch`로 거부한다. 소자를 더한 파생 topology는 원본과 지문이 다르다 | `E/authoring/spec_meta.py:32-34` |
| F-11 | 자기동형 궤도: 완전 차동 쌍은 두 drain 넷이 같은 궤도다. **단일 종단 출력(미러 부하)은 두 drain 넷이 다른 궤도다** | `E/tests/graph/test_automorphism_orbits.py:125-129` |
| F-12 | S1 matching group 종류 `diff_pair`(`MATCH_DIFF_PAIR`)가 있다. 차동쌍 후보 규칙은 같은 (kind, 비레일 source) 묶음에서 바이어스 형제를 빼고 남은 멤버가 정확히 2이면 derived, 3 이상이면 review_needed다 | `E/graph/s1_values.py:94`, `E/graph/matching_groups.py:20-22` |
| F-13 | 블록 AC 역할 어휘는 `input, cascode, follower, pass, mirror, load, tail_source, diode_load`다. DC 역할은 `diode_reference, bias_current_source, signal, diode_reference_composite(_cascode)`다. 모두 유도값이다 | `E/graph/s1v_values.py:86-96`, `E/graph/s1_values.py:65-69` |
| F-14 | 잡음원은 모든 MOS와 저항에 하나씩 있고 역할로 거르지 않는다. MNA 용량 스탬프도 셀 종류로 가르지 않는다 | `E/metrics/noise_sources.py:5, :45`, `E/metrics/stamp_mos.py:5-6` |
| F-15 | headroom·포화 검사: `headroom_bound`, `iv_headroom.headroom_bounds`, 봉인 7 `dc_seal_saturation`, DC 제약 행 `constraint_rows` | `E/metrics/headroom_bound.py:111`, `E/search/iv_headroom.py:152`, `E/sizing/seal_saturation.py:51`, `E/search/constraints.py:31` |
| F-16 | θ 종류는 `ln_idu, L, y, current, resistance, capacitance, ss_resistance`다. metric 레지스트리는 `_ROWS`이고, 이름은 `metric_catalog()`로 검증한다 | `E/sizing/s2_values.py:57-65`, `E/metrics/registry.py:36-63, :81`, `E/metrics/catalog.py:20` |
| F-17 | mismatch LUT는 `sky130_nfet_pfet_lut_v2_mismatch_r1.npz`(git 밖)다. 축은 L·VGS·VDS·VS이고 w_ref_m이 있다. 변수는 nmos `toxe, vth0, voff`, pmos는 여기에 `nfactor`를 더한 것이다 | `assets/lut_v2_location.json`, `E/lut/CONTRACT.md:938-948`, `assets/sky130_pdk_decl.json:454-465` |
| F-18 | 엔진 코드에 'trim'은 없다 | grep 2026-10-15 |

**v0.5 추가 사실**(읽기 확인, base `d783efe`, 2026-10-16. 경로의 `O/`는 `tools/spice_oracle/`이다):

| ID | 사실 | 근거 |
|---|---|---|
| F-19 | 오라클 넷리스트의 코너와 온도는 엔진 LUT npz의 메타(`corner`, `temp_c`)에서만 온다. `.temp`는 LUT `temp_c`이고, include 경로의 `{corner}` 자리를 LUT 코너로 채운다. LUT와 다른 온도를 지정하는 **전용 입력은 없다**. `testbench.options`로 온도 옵션을 넣는 우회가 가능할 수는 있지만 판정 경로로 쓰지 않는다. 쓰더라도 능력 기록 요구 항목 '결과에서 읽은 실제 온도 = 요청 온도'(N3.9-3)가 덮는다 | `O/oracle_netlist.py:32-33, :77, :112-120, :314-318`, `O/oracle_input.schema.json:15, :25` |
| F-20 | 오라클 MC는 한 PDK의 관례(불일치 변수 이름 패턴, 단위 배율, 분포 가정)를 코드에 담고 있다. 모델 파일이 없거나 패턴이 안 맞으면 소자 변수 0개로 그대로 진행한다(코드 읽기). 그러면 분산 0이 오류 없이 나올 수 있다(실측으로 확인하지 않음). 이 문제의 해결(공정·시뮬레이터 무관화)은 oracle-portability 계획 범위다(T-33). 이 계획에는 '능력 기록 없이 MC 판정을 믿지 않는다'는 의존 규칙(N3.9)의 근거로만 남긴다 | `O/oracle_offset_mc.py:18-23, :52-66, :145-153`, 조사 `wt/_scratch_oracle_port/survey.md` §0 |
| F-20a | 오라클 MC가 내는 offset은 **흔들림만의 것**이다. 표본마다 V_os,k = (V_out,k − V_out,0)/A − (V_id,k − V_id,0)이고 기준 해(표본 0)와의 차로 계통 offset을 뺀다. 계통 offset V_sys를 재는 오라클 측정은 없다 | `O/oracle_offset_mc.py:25-28, :183-184` |
| F-21 | 오라클 MC 표본 수는 N = ⌈1 + 1/(2r²)⌉이다(r = 엔진 offset 분해능의 상대값). σ 추정의 상대 표준오차는 1/√(2(N−1))이다. 상한에 걸리면 `n_capped`와 실제 상대 표준오차를 보고한다 | `O/oracle_offset_mc.py:9-13, :43-49` |
| F-22 | (oracle-portability 계획으로 넘김: PDK 선언과 오라클 모델 경로의 이중 위치 사실. 초안 `wt/_drafts/oracle_capability_handoff_from_offset_trim_v05.md` §1) | -- |
| F-23 | (v0.6에서 history H3로 옮김 -- 옛 모델 오차 경로 사실, 감사 E3). 모델 오차(e_m)는 상위 사용자 결정 O-178로 폐지됐다(상위 DEC-72 = 엔진·oracle 대조 기록, card ME-1 삭제 -- 그 자리 card CL-1 oracle 닫기). 이 계획에 남는 사실은 '`value_from_spec`은 옛 이름이라 로더가 거부한다'뿐이다(N3.8.3에서 인용) | history H3 |

### N3.1 흐름(국면 1 → 엔진 밖 사양·제안 → 승인 → 국면 2; v0.7, O-258 -- DEC-110 자리는 N3.10)

1. **국면 1(엔진, 후보)**: trim 선언이 있는 spec으로 원본 topology를 평가한다. 랜덤 offset 판정은 N3.6 의미로 바꿔 둔다. 주입 쌍과 극성마다 다음을 낸다(FR-T2).
   * front 위 t의 범위와 부호
   * headroom 창
   * 잡음 영향
   * trim 필요 판단 값(FR-T2)

   topology 파일은 바꾸지 않는다. 엔진은 추천 N·m·파생 topology를 내지 않는다(v0.7, O-258 -- 옛 1·2·3·4 문언은 history 'v0.7.0').
2. **trim 사양(엔진 밖, O-258 (A))**: 같은 원본 회로가 5단계 (2) SPICE 닫기를 지난 실현 점에서 oracle MC로 σ_MC를, oracle `.dc`로 V_id*를 잰다(표본 수 = r_σ 유도, 능력 기록 전제). 엔진 밖 trim 구동기가 trim 사양 기록(R, LSB 상한, N_min)을 쓴다(N3.10, FR-T13).
3. **AI 제안**(DEC-110 역할 -- AI = 판단·선언 작성, 엔진 수치를 대신하지 않음): AI가 엔진 후보표(주입 쌍·극성)와 trim 사양 기록을 근거로 trim 파일(N ≥ N_min, m, 극성, 바이어스 원천 -- D-9, 코드 입력·코드 상태 선언)과 의도 문서를 쓴다. AI가 고른 값은 국면 2 엔진 관문(N3.4 판정·N3.11 부담·E-0)과 oracle 판정을 지나야 판정이 된다.
4. **승인**: 사용자가 trim 파일·의도 문서·근거와 합성 회로 connectivity 표를 보고 승인한다(FR-T4, 원칙 15). 승인된 N·m·코드 선언은 국면 2에서 **고정값**이다. 사용자는 같은 승인에서 σ_MC 선언(spec `offset_trim` 칸, 출처 = MC 기록 id)을 채택한다.
5. **국면 2(합성 회로)**: 로더 블록 하나가 원본 topology + 승인된 trim 파일을 합성하고(N3.3), 결속 검사를 통과하면 부담 사이징(N3.11) → 합성 회로 5단계 (2) 닫기 → trim 뒤 잔여 MC(표본마다 최적 코드, N3.12)를 돈다. 온도 범위 판정·보정 루프(N3.8)는 그 뒤, 5단계 (3) 전이다.
   * N·m은 고정이다. 단위 전류 I_u는 θ다(T-7, N3.4).
   * 보정 구간·잔여·부담은 제약으로 판정한다.
6. **되돌림**: 국면 2에서 선언 N·m으로 가능한 해가 없으면(부담 재풀이 뒤에도 -- N3.11) 사유(`trim_config_infeasible`와 위반 경계)를 보고하고 멈춘다. 다음 행동은 AI의 trim 파일 재제안과 재승인이다. 엔진이 N·m·코드 선언을 스스로 바꾸지 않는다.

### N3.2 주입 쌍 규칙(구조 규칙, 이름 없음)

* **쌍 정의**: S1 matching group 가운데 상태가 derived(멤버 정확히 2)인 `diff_pair` 그룹(F-12)에서, 두 멤버가 모두 `metric_structure.input_cells`(F-5)에 드는 것이다. 주입 쌍은 그 두 소자의 drain 넷 (n_p, n_n)이다. p/n 구분은 게이트 넷의 포트 역할(`differential_input_p/n`)로 한다.
* **이 정의를 쓰는 이유**: 자기동형 궤도로 짝을 지으면 미러 부하(단일 종단 출력) 회로에서 성립하지 않는다(F-11).
* **미러 부하에서도 차동 주입이 유효하다는 원리**: 다이오드 쪽 drain 넷에 전류 +I를 넣으면 다이오드 소자 전류가 I만큼 줄고, 미러 출력 전류도 같은 비율로 준다. 그래서 출력 넷에서 보면 −I를 넣은 것과 같은 방향의 효과가 난다. 즉 z[n_diode] ≈ −z[n_out]이다(미러 비 1, 다이오드 노드 임피던스가 출력 노드보다 훨씬 낮을 때의 근사). 따라서 쌍 차동 주입의 전달 t = (z[n_p] − z[n_n])/(2·A_dc)은 0이 되지 않는다. 엔진은 근사식을 쓰지 않고 z를 그대로 계산한다.
* **정의되지 않는 경우**: derived `diff_pair`가 입력 셀 안에 없으면 `trim_pair_undefined`를 보고하고 후보를 내지 않는다. diff_pair가 review_needed(멤버 3 이상)이거나 입력 셀 밖이어도 같다. 조용한 대체는 금지다.
* **상보 입력쌍**(입력 셀 안에 nmos·pmos `diff_pair` 두 개): 쌍마다 따로 후보를 낸다(D-7).
* **단일 입력 회로**: 차동 입력 포트가 없어 `diff_pair`가 입력 셀에 없다. 이 범위에서는 `trim_single_input_unsupported`다(D-8, X-11).
* **극성**(쌍마다 둘): nmos 싱크 셀은 주입 넷에서 하단 레일 쪽으로 전류를 뺀다. pmos 소스 셀은 상단 레일 쪽에서 넣는다. 극성마다 headroom 창을 경로 합(F-15)으로 계산한다. 창은 국면 1 봉인 점 주입 넷 전압과 그 레일 사이에서 셀 출력 소자 VDsat + 스위치 VDS가 들어갈 여유다. 이 창은 DC 양이고 정의는 gain-budget N3.8 스윙·입력 범위(DC 동작 범위 -- DC 범위 조건 = 모든 MOS가 선언 영역(선언 없음 = 포화, triode, off)에 머무름, 훑기 중 이탈 = 범위 끝; 사용자 결정 O-54) 꼴을 인용한다. 봉인점 값으로 낸 이 여유는 **'추정'** 표기 손계산이다(사용자 결정 O-29 (2)·O-31, 감사 E2). 정확값은 오라클 끝 코드 `.dc`다(N3.5).
* **순위 키**: 기본안은 headroom 창이 비지 않은 (쌍, 극성) 가운데 \|t\| 내림차순이다. 잡음은 값으로 보고만 한다(D-5).

### N3.3 trim 파일, 합성 로더, 승인 기록, 결속(v0.7, O-258 (B) -- 옛 `augment_trim` 절 원문은 history 'v0.7.0')

**원리**: 원래 topology는 바뀌지 않는다. trim 구조는 별도 선언 파일이고, 연결 선언은 AI가 제안하고 사용자가 승인한다(topology connectivity = 사용자 몫, 원칙 15). 엔진은 trim 구조를 만들거나 고르지 않는다(옛 `augment_trim`의 소자 생성·이름 규칙·선택 칸 삭제). 엔진 몫은 두 선언을 결정적으로 합성하는 것과, 합성 회로를 판정할 숫자·관문이다(DEC-110 역할).

**trim 파일 스키마**(`<회로>.trim.topology.json` -- 파일·칸 이름과 형식은 design G-21, DEC-68):

| 칸 | 내용 | 로더 검사(fail-closed, 사유 이름 design) |
|---|---|---|
| role | `trim` 선언 하나(이 파일 소자가 trim 로직임을 선언) | 없음·다른 값 거부 |
| base | 원본 topology `connectivity_fp` | 현재 원본 지문과 다르면 거부 |
| ports | trim 포트와 종류 {주입, 전원, bias, 코드 입력} | 닫힌 어휘 밖 거부 |
| devices | trim 소자 -- 원본 소자 스키마(F-7) 키 그대로(name, kind, drain, gate, source, bulk). 내부 넷 이름은 이 파일 안에서 정의 | 원본 소자·넷 이름과 충돌 거부(이름을 바꿔 붙이지 않음, NFR-T4) |
| connections(연결표) | trim 포트 ↔ 원본 넷(원본 topology 이름 그대로). 주입 포트는 주입 쌍(N3.2) 넷에, 전원 포트는 레일(`supply_nets`)에, bias 포트는 선언된 바이어스 넷 또는 새 `bias_inputs` 항목(D-9)에 붙는다 | 원본에 없는 넷, 연결 안 된 포트, 한 포트가 둘 이상 넷에 연결 거부 |
| code_inputs(코드 입력 선언) | 비트마다 {게이트 넷(코드 입력 포트), on·off 레벨 = 레일 역할 참조(D-10, 숫자 사본 없음), 비트 값별 on 소자 집합·off 소자 집합, on 스위치 영역 triode/saturation(O-53 B1 ratify 대상)} | 한 비트 값에서 같은 소자가 on·off 둘 다, 어느 비트에도 걸리지 않은 스위치 거부 |
| code_states(코드 상태 선언) | 평가 코드 벡터: 봉인 코드 하나와 포화 검사 코드들(N3.5) | 벡터 길이 ≠ N 거부 |
| dac | N, m, 극성(N3.2), 바이어스 원천(D-9) | m > N − 1, N < 1 거부 |
| basis(근거) | 엔진 후보표의 실행 id, trim 사양 기록 id, 의도 문서 경로·sha256(DEC-110 AI 산출물 규약) | 참조 대상 없음 거부. 엔진은 이 칸을 승인 결속 지문에만 넣고 값을 계산에 읽지 않는다(oracle 유래 기록을 엔진 입력으로 쓰지 않음 -- X-23) |

* **N ≥ N_min 검사의 자리**: trim 사양 기록(N0.1)의 N_min은 필요조건이고 그 대조는 AI 제안 도구·승인 단계(엔진 밖) 몫이다. 엔진은 국면 2에서 선언 N·m의 실현 가능성을 N3.4 판정으로만 본다(같은 검사를 엔진에 두 번 두지 않음 -- graph 규칙 1).
* **합성 로더 블록**(writer 하나, 블록 이름·층 자리는 design G-22): 입력 = (원본 topology, trim 파일). 실행(사이징) 경로에서는 승인 기록이 가리키는 trim 파일만 넣고 아래 결속 검사를 지난 뒤에만 부른다. 승인 전 connectivity 표 도구는 같은 블록에 제안 trim 파일을 넣어 표만 낸다(사이징·판정 경로 아님). 출력 = 합성 회로(원본 소자 + trim 소자, trim 포트 넷은 연결표의 원본 넷으로 묶임), **소자 출처 칸**(원본 / trim 파일), 코드 상태별 intended_region 선언(N3.5). 결정적 순수 계산이고 파일을 쓰지 않는다. 재사용은 graph reuse·블록 결과 색인만이다(새 cache 없음). 승인 전 connectivity 표 도구도 이 블록을 그대로 부른다(둘째 합성 구현 금지).
* **스키마**: 원본 topology 파일 스키마(F-7)는 바꾸지 않는다. 출처 칸은 합성 회로(로더 출력) 안에만 있고, trim 역할 유도(FR-T5)와 부담 변형(N3.11)이 이 칸을 READS한다.
* **승인 기록**: 파일 `<name>.trim.json`(기본안 유지, 이름은 design)에 둔다. 담는 것은 `approval_id`, 원본 `connectivity_fp`, trim 파일 sha256, 합성 회로 `connectivity_fp`, 합성 규칙 지문이다. on 스위치 영역 선언·코드 선언은 trim 파일 안에 있어 trim 파일 sha256으로 승인 결속(아래 1·3)에 묶인다. 국면은 이 기록 유무로 정한다(offset-strategy N3.5, DO-2).
* **결속**(B4, 기본안 D-13 -- 파생 지문을 trim 파일·합성 회로 지문으로 바꿈):
  1. **spec**: `meta.topology_fp`(F-10)는 원본 topology에 묶인다. 승인 기록이 있는 실행에서 로더는 spec 지문을 원본 지문과, trim 파일·합성 회로 지문을 승인 기록과 대조한다.
  2. **structure.json**(F-8): 사실은 원본 지문에 묶인 채로 두고, 합성 회로 실행에서도 출처 칸이 원본인 소자에만 적용한다. 엔진은 합성 S1·S1v에서 출처 칸이 trim 파일인 소자를 뺀 유도 결과가 원본 실행의 유도 결과와 같은지 본다(비교 필드 G-2). 다르면 `trim_structure_divergent`로 정지한다.
  3. **승인 기록**: trim 파일 sha256, 다시 합성한 회로의 지문, 합성 규칙 지문 가운데 하나라도 승인 기록과 다르면 `trim_approval_stale`로 **정지**한다(fail-closed). structure.json 선례(review_needed로 되돌리고 계속)와 다르다(X-13). 승인되지 않은 회로를 사이징하는 것이 되기 때문이다.
* **규칙 지문 변화**(F-9): TR-4가 S1·S1v 규칙 파일(`trim_dac` 역할 유도)을 바꾸면 `structure_rule_fp()`가 바뀐다. 그러면 trim 선언과 무관하게 current_reuse_telescopic_ota와 nmcnr_amplifier의 structure.json 사실이 review_needed로 돌아간다. 두 파일을 재승인하는 것(사실 내용은 같고 `rule_hash`만 갱신)은 사용자 승인 사항이고, TR-4 병합 조건이다(N5, N9).

### N3.4 DAC 규칙(유도, 상수 없음)

기호: σ_in, σ_MC, V_id*, t, k, V_res, σ_U(N0.1). 단위 셀 수는 2^N − 1이고 I_T = (2^N − 1)·I_u, I_LSB = 2·I_u, I_FS = I_T다.

**DNL**(Bertotti 2012 식(3), p.2): 분할 DAC의 최악 전이는 thermometer 셀 하나가 켜지고 이진 하위 셀이 모두 꺼지는 코드다. 이때 바뀌는 단위 셀 수는 2^(m+1) − 1이다. 그 전이의 DNL 분산(LSB²)은 다음과 같다.

  E[DNL²_worst] = (2^(m+1) − 1 − 1/(2^N − 1))·σ_U²

차동 steering에서 단위 셀 하나가 δ를 2·I_u(1 + ε) 바꾸므로 상대 오차 ε는 σ_U 그대로이고, 식은 LSB 단위로 같다. 순수 이진은 m = N − 1의 최악 전이와 같다(Staudt 2011 Table I, p.3의 σ_U·√(2^n−1)과 정합).

σ_DNL(m) = σ_U·√(2^(m+1) − 1 − 1/(2^N − 1))로 쓴다(LSB 단위 최악 전이 DNL의 1σ). σ_U의 기준점(어느 θ·어느 봉인 점의 단위 셀 σ인가)은 G-5에서 정한다.

**부호 규약**(v0.6, 감사 A1): 계통 offset의 정의와 부호는 gain-budget DEC-23(부호 있는 V_id* -- 출력을 기준값으로 되돌리는 여기 방향 입력 이동량)을 그대로 인용한다(사용자 결정 O-50 G1). 그래서 랜덤 offset이 없는 회로에서 출력을 기준값에 두는 입력 이동량은 V_id* 자체다. 옛 문언('−V_sys,s', `offset_systematic` 인용)은 history H1 2026-10-20.

**음의 DNL은 trim에 해가 없다**: 음의 DNL은 인접 보정 간격을 좁힐 뿐이라 잔여 상한을 키우지 않는다. 잔여를 넓히는 것은 양의 DNL뿐이다(Staudt 2011 §III, PDF p.3, `paper.md` 696-712행: 꼬리는 양의 DNL이 만들고, 의도적으로 음의 DNL 쪽으로 기운 trim DAC가 좋다). 그래서 DNL 자체에 별도 한계를 두지 않고, 양의 DNL이 들어가는 잔여 판정 하나로 판정한다.

**N·m의 출처**(v0.7, O-258 -- 옛 '1단계 추천' 표(엔진이 σ_in으로 N·m 추천)는 history 'v0.7.0'):

| 항목 | 규칙 |
|---|---|
| N | 승인된 trim 파일의 선언값이다. 필요조건 N ≥ N_min = ⌈log2(R/V_res + 1)⌉(R = k·σ_MC + \|V_id*\|, trim 사양 기록)은 아래 I_u 하한 ≤ 상한에서 σ_DNL ≥ 0으로 나오는 식이다(\|t\|가 약분되어 엔진 값 없이 정해짐). 대조 자리는 엔진 밖(N3.3) |
| m | 승인된 trim 파일의 선언값이다(m ≤ N − 1). T-3의 'DNL 부족'은 '이진 비트가 많아 σ_DNL(m)이 커져 잔여 창이 닫히는 것'으로 유도하고, 국면 2 잔여 판정이 그 창을 판정한다(m 제안 근거는 AI 몫, σ_U 기준은 G-5) |
| 극성 | 엔진 후보표의 N3.2 순위를 근거로 AI가 제안하고 trim 파일에 선언한다 |

**국면 2 판정**(N·m = trim 파일 선언, 합성 회로):

| 항목 | 규칙 | 근거 |
|---|---|---|
| I_u 경계 | 하한(보정 구간의 선형 근사): \|t\|·(2^N − 1)·I_u ≥ k·σ_MC + \|V_id*\|(σ_MC = 승인된 σ_MC 선언 참조, 사본 없음; V_id*는 합성 회로 엔진 값이고 판정 W는 아래 '판정 W' 행). 상한(잔여): \|t\|·I_u·(1 + k·σ_DNL(m)) ≤ V_res, 곧 아래 잔여 판정의 Δ_max/2 ≤ V_res(Δ_max = \|t\|·2·I_u·(1 + k·σ_DNL)). I_u는 θ이고(사용자 결정 T-7 -- 옛 D-16 '하한값') 목적의 전력 최소가 하한으로 이끈다. 하한 > 상한이면 `trim_config_infeasible`(N3.1-6). 계통 offset 몫을 랜덤 몫과 따로 두는 이유: R의 \|V_id*\|(oracle, 사양 기록)를 문턱에 넣으면 끝 코드 V_in(±end)가 이미 품은 합성 회로 V_id*와 두 번 센다(v0.3 C1과 같은 꼴) | 선형 근사는 유도용이다. 판정은 아래 보정 구간 판정(봉인점 1차 감도 추정, O-53 A3)이다 |
| 보정 구간 판정 | 끝 코드 두 개의 입력 환산 보정 끝 V_in(−end), V_in(+end)를 **봉인점 1차 감도 추정**으로 낸다(사용자 결정 O-53 A3): 봉인 기준 코드에서 그 끝 코드로 바뀔 때의 trim 주입 전류 변화 ΔI를 봉인점 DC 방정식으로 −G⁻¹·ΔI만큼 출력에 옮기고(off 소자는 G 기여 없음), DEC-23과 같은 환산(출력을 기준값으로 되돌리는 여기 방향 입력 이동량, A_dc)으로 입력에 옮겨 V_id*에 더한다. 표기는 '1차 감도 추정'이고 정확값은 오라클 `.dc` 코드 스윕이다. 조건은 **[−k·σ_MC, +k·σ_MC] ⊆ [min V_in(±end), max V_in(±end)]**다(v0.7, O-258 (A) -- 옛 σ_in). 선형 근사에서 V_in(±end) ≈ V_id* ± \|t\|·I_T이므로 이 조건은 \|t\|·I_T ≥ k·σ_MC + \|V_id*\|, 곧 위 하한과 같다. 합성 회로의 DAC mismatch 몫(엔진 σ_in에 들어 있음)은 잔여 판정과 trim 뒤 잔여 MC(완료 조건 3)가 판정한다. 추정값과 선형 근사의 차는 결과 JSON에 기록한다. 엔진 안 고정 기하 DC 균형 풀이(Newton)는 두지 않는다(X-29) | Staudt 2011 §II.A(p.1-2), Mohamed 2013 식(3)(p.3), O-53 A3 |
| 잔여 판정 | 인접 코드 사이 보정 간격의 최댓값을 Δ_max라 하자. 최적 코드를 고를 때 잔여 상한은 Δ_max/2다. 간격을 넓히는 것은 양의 DNL뿐이고, 그 상한을 k·σ_DNL(m)로 두면 Δ_max = \|t\|·I_LSB·(1 + k·σ_DNL(m))이다. 조건은 **Δ_max/2 ≤ V_res** 하나다. 제안의 \|t\|·I_LSB ≤ V_res는 DNL을 따로 묶은 경우의 보수 근사다(X-12) | Staudt 2011 §II.C·§III(p.2-3), Bertotti 2012 식(3)(4)(5)(p.2-3) |
| σ_U | 단위 셀 θ(ln IDu·L)에서 F-3 경로로 계산한다. Pelgrom 상수는 쓰지 않는다. k를 전이 DNL 배수로 쓰는 한계는 D-3이다 | F-3 |
| θ | 단위 셀 gm/ID(`ln_idu` 계열)와 L만 둔다. I_u·I_T는 유도값이다(X-3) | 상위 NFR-5, F-16 |
| 자기일관 | t, σ_in(DAC mismatch 포함, 보고), V_id*는 합성 회로의 봉인 점 값이다. σ_MC는 승인된 선언값이고 국면 2에서 다시 재지 않는다(재면 둘째 생산자). 유도값과 판정값이 다르면 판정값이 이긴다 | 상위 DEC-74, graph 규칙 1 |
| 판정 W | 보정 구간 판정의 V_id*는 gain-budget DEC-23·DEC-74·U-108(커널 + front 판정 W 재판정)을 따른다. 커널(θ 프레임 봉인점)에서는 판정 W = θ 유도 W라 V_id* = 상위 DEC-23 (나′) 성분 (1)(2)(성분 (3) = 0)로 판정하고(상위 U-108), front 점에서 판정 W(단위 9 전 sizing W)로 성분 (3)을 더한 \|V_id*\|로 다시 판정하며, 단위 9 뒤 실현 W로 다시 판정한다. 위반 점은 front에서 빼고 비지배 재필터한다(감사 A5). matching 쪽 같은 꼴은 O-53 A2(정본 offset-strategy v0.7) | DEC-23, DEC-74, O-45 U3 |

**제약**: 국면 2(승인 기록 있음)에서만 생기고, 출처는 spec 선언을 참조한다. 보정 구간 포함과 잔여 Δ_max/2 ≤ V_res 둘에, 부담 변형에서는 부담 제약(N3.11)이 더해진다. DNL만의 별도 제약은 두지 않는다(유도되지 않은 상수가 필요하기 때문이다, NFR-T2).

**metric**: 이름은 상위 DEC-68 규칙으로 design이 정한다(제안 이름 trim_lsb, trim_range, trim_dnl, trim_power, trim_area).
* LSB 입력 환산값
* 보정 구간(양 끝 입력 환산값)과 선형 근사와의 차
* 잔여 상한 Δ_max/2(입력 환산)
* 최악 전이 DNL의 1σ σ_DNL(m)(LSB, 보고용)
* steering 공급 전력(`power_dc_w`에 이미 포함되므로 보고용)
* DAC 소자 면적(탐색 축 면적에 포함)
* (v0.7, N3.11) 주입 넷 부가 용량·부가 컨덕턴스(출처 칸이 trim 파일인 소자가 주입 넷에 스탬프하는 몫 -- 값은 기존 MNA 스탬프 필드를 READS하는 metric 블록 하나가 쓴다, 새 스탬프 계산 없음), trim 전력(출처 칸이 trim 파일인 소자의 공급 전류 몫). 부담 변형의 목적 축이다

각 metric은 `verified_by`(SPICE 오라클)가 생긴 뒤에만 제약으로 쓴다(상위 N3.8).

### N3.5 코드 상태와 DC 검사

* **평가하는 코드 상태는 trim 파일이 선언한 넷이다**(v0.7 -- 코드 상태 선언, N3.3). 중간 코드 두 개(δ = +I_u, δ = −I_u. δ = 0 코드는 없음)와 끝 코드 두 개(δ = ±I_T)다. 봉인은 δ = +I_u에서 하고, 나머지 셋은 포화 검사만 한다(D-17). 엔진은 코드를 찾거나 만들지 않는다(N3.12). 코드 상태 선언은 벡터마다 역할(봉인 / 포화 검사)과 뜻하는 δ(I_u 배수)를 함께 적고, 합성 로더가 코드 입력 선언에서 그 δ를 셀 수 있으면 대조해 다르면 거부한다(fail-closed; 셈의 정의는 design G-21).
* **전류 0 소자와 영역 선언**(사용자 결정 O-53 B1, G-1 해소; v0.7 -- O-249 'off는 선언으로만'): 합성 로더가 코드 상태 선언과 코드 입력 선언(비트 값별 on/off 소자 집합)에서 코드 상태마다 소자별 intended_region을 결정적으로 만든다(옛 '`augment_trim`이 만든다'). 엔진은 전류 크기·문턱으로 off를 분류하지 않는다.
  * 그 코드 상태에서 off로 선언된 steering 소자와 스위치 = `off`. 모든 코드에 off 소자가 있으므로 봉인 기준 코드(δ = +I_u)에도 있다.
  * on 스위치 = trim 파일 코드 입력 선언의 on 스위치 영역 칸(triode/saturation, 사용자 ratify 대상, N3.3). `triode`는 intended_region `triode`로, `saturation`은 intended_region **선언 없음**(= 포화 기본)으로 옮긴다. intended_region 값 집합 {triode, off}에 새 값을 더하지 않는다(감사 4차 B-6).
  * 동작점(봉인점·합격 판정 점·범위 측정 공칭 점)에서 선언 영역과 실제를 대조한다(우회 금지). 원인 구분은 gain-budget N3.8·DEC-90 (1) 정본을 인용한다(사용자 결정 O-55 U1): 선언된 triode 소자 불일치 = 선언 오류 거부(판정 불능 집계), 선언 없는 소자 비포화 = 설계 실패 FAIL -- off 선언 소자는 영역 대조 대상 밖이다(상위 사용자 결정 O-202). 범위 훑기 도중 선언 영역을 벗어나면 그 점이 범위의 끝이다(측정 거부 아님, O-54). 꺼짐·전도의 정의는 상위 gain-budget N3.6 '전도·포화 경계·`off` 선언 정본'(선언 방향 ID 부호, 상위 O-205 (1)·O-210 RR-2)이다.
  * off 선언 소자는 **사이징·역산 경로**(LUT·gm/ID 조회로 W·L·바이어스를 정하는 자리)와 포화 요구에서 빠진다(상위 사용자 결정 O-202 -- 옛 '꺼짐 판정 = 공용 판정 함수가 LUT I_off'·'범위 훑기 off 유지 경계 = VGS 감도 + 봉인 9 전도 VGS'(O-55 V5) 삭제, **원래 취지와 다름(승인 상위 O-202)**). 봉인점 KCL은 off 전류 0 모형, 효과는 1차 ΔV(상위 gain-budget N3.6 '전도·포화 경계·`off` 선언 정본' (5)). off 소자 (W, L) = `off` 항목 `w_m`·`l_m`(상위 위임 A-1, 상위 사용자 결정 O-226). (v0.7) trim 소자는 코드 상태에 따라 on/off가 바뀌므로 (W, L)은 국면 2 θ(단위 셀) 유도값 하나이고, 같은 값을 `off` 항목 `w_m`·`l_m`에 다시 적지 않는다(같은 값 두 자리 금지, graph 규칙 3) -- 코드 상태별 off 선언의 기하 출처를 상위 off 항목 정의가 받는지는 상위 개정 입력(history 'v0.7.0' gain-budget 입력 목록 GI-3). **VGS < 0 off 소자가 있는 평가점은 그 점 E-0 정지**(상위 사용자 결정 O-212) -- trim off 스위치는 대개 VGS < 0이라(연결 구조 추론, 확신 중간 -- off 레벨은 trim 파일 코드 입력 선언의 레일 역할 참조) LUT 확장(단자 전류 열 + VGS < 0 축) 전에는 trim 회로 후보가 대개 정지한다; 그 LUT 확장 결정은 TR card 착수 조건이다(N6). 꺼짐이 충분한지는 그 off 소자의 `judged_by` metric(사용자 선언 -- trim 잔여·DNL 등, 상위 O-202 O-h)이 판정한다: 칸이 없거나 그 metric이 `verified_by`를 갖지 않으면 E-0 정지 -- 이 계획 metric은 `verified_by`가 생긴 뒤에만 제약이므로(N3.4 끝) TR card가 `verified_by`를 붙일 때까지(완료 조건 2) 정지한다.
  * 오라클 입력에는 oracle-portability G-18이 같은 칸을 싣는다(EO-1 생산자, N6).
* **정상 동작점**: 중간 코드 가운데 기본안은 δ = +I_u(D-17)이고, 일반 DC 봉인 1~8로 검사한다. 두 주입 넷에 steering 공통 전류(각 ≈ I_T/2)가 들어가므로 입력 셀 부하 전류 균형이 바뀐다(Lu 2007 식(10), p.2). 이 변화는 DC writer가 trim 소자를 바이어스 전류원으로 다루면 자동으로 들어간다.
* **끝 코드**(사용자 결정 O-53 A3): 끝 코드 포화 여유(봉인 7)는 보정 구간 판정(N3.4)과 같은 **봉인점 1차 감도 추정**으로 낸 노드 전압에서 검사한다. 검사 점은 출력을 DEC-23 기준값에 둔 점(끝 코드 ΔI와 그것을 되돌리는 여기 방향 입력 이동을 같은 1차 감도로 함께 옮긴 점)이다(기본안 -- 끝 코드는 표본 offset이 보정 구간 끝에 있을 때 출력이 기준값에 놓이는 동작 상태라서다, 물리 정합). intended_region이 `off`인 소자는 포화 검사에서 빠진다(영역 대조 없음 -- 상위 O-202). 정확값은 오라클 `.dc` 코드 스윕이다. 옛 '출력 균형 입력 전압을 함께 푼 DC 해'(X-4)는 엔진 안 균형 풀이라 지웠다(X-29, 옛 문장은 history H1 2026-10-20).

### N3.6 offset spec 의미 전환과 기존 해석과의 관계

| 대상 | trim 선언 없음(지금) | trim 선언 있음 |
|---|---|---|
| `offset_in_sigma_mv` | 절대 제약(current_reuse)이거나 보고 | 국면 1: trim 필요 판단 입력(보고). 국면 2: 합성 회로 값(DAC mismatch 포함, 보고). (v0.7) 덮을 분포의 폭은 σ_MC 선언이다(N3.4). 보고는 유지한다. 같은 spec에 이 제약이 함께 있을 때의 처리는 D-4다 |
| `offset_excess` 가드 | 구조 가드 | trim 소자는 분자에 들어가고 분모(입력 셀)는 그대로다. 처리는 D-4다 |
| `offset_sys_mv`(정본 DEC-23 V_id*; 이동의 기준점 V_id,0 = DEC-23 '이동의 기준점'(v6.21 `54a3a328` 223행; 선언 입력 DC의 여기 방향 좌표, 선언 없으면 정의 불능 -- 사용자 결정 O-59 (4) DV-13), 이 계획은 인용만) | 상한 = 랜덤 예산(DEC-23), 판정 위치 = 커널 + front 판정 W 재판정(DEC-74·U-108 -- v0.6.2) | 부호 있는 V_id*가 보정 구간 끝(N3.4 1차 감도 추정)에 더해진다. 하한에서는 \|V_id*\|로 쓰고 판정 W는 N3.4 '판정 W' 행이다. 상한 규칙은 D-4다 |
| `iv_matching_l` L 하한 | 출발값 | 끈다. 판정은 바뀌지 않는다(F-4, X-5). 새 출발값 규칙은 design이 정한다. 층 0 조립(gain-budget LA-1) 출발 규칙과의 정본 관계는 G-12(감사 C2)다 |
| `iv_matching_l` 가드 부하 | 부하 역할 소자 | trim 소자는 `trim_dac` 역할이라 들어가지 않는다(FR-T5) |
| 잡음 metric 4종 | 모든 MOS | trim 소자 잡음이 들어간다(F-14). `noise_excess_th` 분모는 그대로다 |
| 극점·PM·GBW | 모든 MOS 용량 | 주입 넷에 cdb·cgd가 더해진다. 전회로 MNA로 판정한다 |
| headroom·스윙 | 경로 합 | 셀 출력 소자 여유가 주입 넷 경로에 더해진다(N3.2 극성, N3.5) |
| 전력·면적 축 | DC 공급 전력, `sum_area` | I_T와 DAC 면적이 자동으로 들어간다. 디지털 디코더·코드 저장 면적은 넣지 않는다 |
| drift·1/f | 없음 / 보고 | 바꾸지 않는다. 보고서에 'offset trim은 drift와 1/f를 보정하지 않음'을 적는다(Kay 2024 §1.2, PDF p.7. 1/f는 chopper가 없앤다는 대비: Zhou 2017 p.2) |

### N3.7 잡음 영향 지표(후보표용)

DAC 출력 전류 잡음 i_n이 주입 쌍에 들어가면 입력 환산 잡음은 대략 \|t\|·i_n이다. 보정 구간 경계에서 I_T ∝ 1/\|t\|이고, i_n²은 출력 소자 gm에 비례한다. 그래서 쌍 선택은 잡음과 전력·면적 사이의 교환이다. 후보표 값은 기존 잡음 해석(adjoint, LUT 잡음 데이터)으로 계산하고 γ 같은 상수 모델은 쓰지 않는다(상위 DEC-96 (3)). Lu 2007 식(9)(p.2)는 주입 소자 transconductance를 작게 둘수록 주입 오차가 줄어든다는 같은 방향의 근거다.

### N3.8 SPICE 온도 보정 루프(T-29, T-30, T-32)

#### N3.8.1 범위와 대상 metric

| 대상 | 범위 판정 | 이유 |
|---|---|---|
| matching 유도 제약(O-53 A2 두 판정 -- 커널 k·σ_in ≤ 문턱, front k·σ_in + \|V_id*\| ≤ 문턱; 정본 offset-strategy v0.7 N3.3, 이 계획은 인용) | 판정한다. 온도 점마다 σ̂(T)와 **계통 offset V_id*(T)**를 모두 오라클로 잰다(V_id*(T) = OP-5 `offset_sys_mv` `.dc`를 그 온도 조건에서 돌린 것 = PC-10, O-53 B3. 같은 양을 온도 조건에서 잰 것이므로 기준점도 같은 DEC-23 '이동의 기준점'(v6.21 `54a3a328` 223행) V_id,0이다 -- V_id,0은 spec 입력 DC 선언에서 정해지는 값이라 온도 점마다 바뀌지 않는다(O-59 (4) DV-13 'spec 값'), 온도 점의 servo 해는 기준점이 아니다(DEC-23 같은 문장)) | T-29 'offset'(S-9로 결정됨, X-21) |
| trim 잔여 `trim_residual`(design §10.6) | 판정한다. 표본마다 T_j에서 고른 코드를 고정하고 온도 점마다 잔여를 잰다(N5.1 3번이 판정이 된다) | T-29 'trim 잔여' |
| trim 보정 구간 `trim_range` | 범위 판정하지 않는다. T_j 판정 그대로다 | 코드는 trim 온도에서 한 번 정한다(N1.2). 보정 구간이 분포를 덮어야 하는 곳은 코드를 고르는 온도뿐이다. 다른 온도에서 남는 것은 잔여이고, 그것은 위 행이 판정한다 |
| `trim_states_saturation`, 코너별 보정 구간, 끝 코드 headroom 온도 의존 | 보고 전용 그대로다(N5.1 4·5번) | T-32 '처음 범위 = offset·trim 잔여만' |
| GBW·PM·잡음·스윙 등 나머지 metric | 대상이 아니다 | T-32 |

* **엔진은 바뀌지 않는다**: 엔진 탐색과 엔진 제약 판정은 T_j·LUT 코너 한 조건이다. D-12(trim 온도 = T_j, 다르면 거부)도 그대로다. 범위 판정은 오라클만 한다.
* **전제(판정 순서, 기본안 O-7)**: 범위 판정은 TR-7 판정 전제와 T_j 판정(design §17-1 σ_in 일치, §17-2 T_j 잔여)을 통과한 점에서만 한다. T_j에서 이미 불합격이면 그것은 온도 몫이 아니라 엔진·오라클 판정 문제(상위 O-178: 정의 관문·oracle 닫기·대조 기록)이므로 루프를 돌지 않고 보고한다(N3.8.4).
* **범위는 T_j를 포함한다(기본안 O-8)**: 판정 온도 범위가 T_j를 포함하지 않으면 범위 판정을 거부한다(Δ_T의 기준점이 T_j이기 때문이다).
* **matching의 V_id*(T) 측정**(v0.5.1, v0.6 사용자 결정 O-53 B3로 정의 닫힘): 지금 오라클 MC는 기준 해와의 차로 계통 offset을 빼므로(F-20a) 온도 점 계통 offset은 따로 잰다. 그 측정은 oracle-portability OP-5의 `offset_sys_mv` `.dc` 측정(출력을 기준값에 고정하고 입력 차를 푸는 것)을 온도 조건에서 돌린 것 하나이고, 그것이 PC-10이다. 공칭 MC 표본 offset은 V_id* 출처가 아니다. 기준값의 정의 자리는 gain-budget DEC-23 하나다(spec 선언 기준 종류 셋 -- 값 = 선언 목표 전압, 넷 = 출력이 다른 넷과 같아야 함, 입력 추종 = 출력이 입력 CM을 따름 -- 과 차동 출력 기본 V(p) − V(n) = 0, 선언 없는 단일 출력은 정의 불능, 추론 금지). 같은 정의를 온도 점마다 그 온도의 해에서 쓴다(G-15 닫힘). 이 측정은 오라클 확장 목록(N6), 능력 기록 요구 항목(N3.9-3), TR-TL 범위(N5)에 들어간다.
* **오라클 능력 전제**: 범위 판정을 요청한 실행의 PDK에 유효한 오라클 능력 기록(N3.9)이 없으면 범위 판정과 루프를 거부한다(fail-closed).

#### N3.8.2 범위 판정 규칙

* **온도 점**: 판정 온도 범위(T-34, spec 선언 참조)의 두 끝점과 T_j다. design §17-3의 보고 전용 점 규칙과 같다. 범위 안에서 metric이 단조가 아닐 위험은 G-11에서 design이 닫는다.
* **온도 점의 전도 판정**(사용자 결정 O-53 B2, X-31 -- 상위 O-205 (1)·O-210 RR-2로 판정 = 그 온도 SPICE op 채널 ID 부호·포화 비교가 되어 'I_off = 그 온도 소자 개별 풀이·tol_V = T_j LUT 셀' 입력 출처 규칙은 대상 소멸, **원래 취지와 다름(승인 상위 O-205)**): 온도 점 판정은 그 온도의 SPICE op 값으로 상위 DEC-90 (1)과 같은 식을 쓴다. 엔진 탐색이 T_j LUT 한 조건이라는 T-29는 그대로다.
  * **담당 card**(감사 4차 V3): 온도 점 판정 절차의 담당은 oracle-portability **OP-5**다(온도 점 SPICE op 값, `plan/oracle-v0610` `64687b21`). 엔진 쪽 둘째 단계 판정은 상위 O-205 (2)·O-210 RR-2로 삭제했다(오라클 한 단계 부호 판정). **이 계획은 그 절차를 구현하지 않고 부른다.** 오라클은 엔진을 import하지 않는다.
* **표본**: TR-7 표본 규칙(design §17, 사용자 결정 T-12)을 그대로 쓴다.
  * k·σ 경계는 T_j에서 정한다. 표본 선택 창 [V_nom − k·σ̂, V_nom + k·σ̂]를 T_j 기준으로 고르고, **같은 seed의 네이티브 MC 표본(같은 불일치 값)을 모든 온도 점에서 다시 잰다**. 그래서 오라클이 표본 정체를 온도 사이에 보존하는지가 이 계획이 능력 기록에 요구하는 항목이다(N3.9-3).
  * **꼬리 판정(G-14 닫힘, 사용자 결정 T-35)**: 범위 판정과 Δ_T는 네이티브 MC 표본 안에서만 한다(oracle-portability v0.4 O-1: 오라클 MC = 네이티브 MC, 결정적 섭동은 진단만).
    * 꼬리는 창 안의 실제 MC 표본, 특히 창 경계 쪽 표본을 온도마다 다시 잰 값으로 판정한다. 결정적 불일치 벡터는 쓰지 않는다.
    * design §17-2의 결정적 끝 표본(소자 공칭 + 입력 직렬 이상 전압 ±k·σ_eng)은 이상 전압원 온도 계수가 0이라 꼬리의 원본 offset drift (i)을 빠뜨린다. 그래서 범위 판정과 Δ_T에 넣지 않고 진단 보고만 한다.
    * 한계 문구: '꼬리는 표본이 닿은 데까지만 확인한다.' 표본 수는 식 S 그대로이고 줄이지 않는다. T_j 판정(끝 표본으로 k·σ 경계)과의 꼬리 범위 차이, 그리고 oracle-portability 비용 알림에 대한 응답은 X-28이다.
    * T_j 판정에서 결정적 끝 표본의 역할을 oracle-portability v0.4와 맞추는 일은 TR-0T(design §17 개정)가 한다.
  * 표본 수 n은 trim 잔여에서 식 S(design §17)다. matching 제약의 n 규칙은 G-10이다.
  * 비용 표를 실행 전에 낸다. 한도를 넘으면 '판정 불능(표본 부족)'이고 n·창·온도 점을 줄이지 않는다(T-12 검증자 조건 (3), 기준 약화 금지).
* **합격**: 모든 온도 점에서 T_j 판정과 같은 합격 규칙을 통과한다. trim 잔여는 창 안 네이티브 MC 표본 전부의 잔여 ≤ V_res다(design §17-2 창 규칙을 온도 점마다. 결정적 끝 표본은 진단만, G-14). matching은 온도 점마다 k·σ̂(T) + \|V_id*(T)\| ≤ `offset_in_max_v`다(V_id*(T) = PC-10).
* **판정 소유**: 범위 판정 규칙과 합격선은 TR-7과 같이 독립 검증자가 확정·소유한다(NFR-T6).

#### N3.8.3 방향 여유 Δ_T(측정 기록)

* **정의**: 대상 metric마다, 범위 판정을 한 설계 점과 그 표본 집합에서 Δ_T = max(0, (판정 온도 범위 온도 점들의 최악값) − (T_j 값))이다. '최악'과 부호는 그 제약을 어기는 방향이다(≤ 제약이면 큰 쪽). 두 값 모두 오라클 값이다. 엔진 값은 들어가지 않는다.
  * trim 잔여에는 두 정의가 가능하다(N-4, 선택은 G-9):
    * (가) 집합 최댓값끼리의 차: (모든 온도 점·표본의 \|잔여\| 최댓값) − (T_j에서 표본 \|잔여\| 최댓값). 두 최댓값이 서로 다른 표본에서 나올 수 있다.
    * (나) 표본별 증가량의 최댓값: max_표본 [max_T \|잔여(T)\| − \|잔여(T_j)\|]. 같은 표본 안의 온도 몫만 센다.
    * 문턱 조임의 목적(T_j 문턱을 지킨 점이 범위에서도 지키게 함)에는 (나)가 표본마다 필요한 여유를 직접 잰다. 그러나 (가)보다 클 수 있다. 둘 중 무엇을 쓸지와 근거는 design G-9에서 정한다.
  * matching: k·σ̂(T) + \|V_id*(T)\|의 온도 점 최댓값 − T_j 값.
  * 정확한 식과 분해능 식은 G-9에서 design이 닫는다.
* **방향**: Δ_T는 문턱을 조이는 쪽으로만 쓴다. 온도가 유리하게 작용해도(차가 음수) 문턱을 풀지 않는다(0으로 둔다). spec 문턱보다 느슨한 판정은 만들지 않는다.
* **문턱 적용**: 엔진 제약 문턱 = spec 선언 문턱 − Δ_T다. 숫자를 복사하지 않고 두 선언을 참조해 합성한다.
  * spec 쪽은 지금 로더가 받는 참조 형식이다. `value_from_spec`은 옛 이름이라 로더가 거부한다(F-23). design §10.6의 `value_from_spec` 표기도 TR-0T에서 함께 고친다.
  * Δ_T 쪽은 구동기가 대조를 통과한 측정 기록으로 만든 변형 제약 입력 하나다(D-24 안 B, N3.8.7 표).
  * 합성 형식은 design G-9다. trim 잔여는 V_res − Δ_T(잔여), matching은 `offset_in_max_v` − Δ_T(matching)이다(S-9 연결점).
* **갱신 규칙(기본안 O-6)**: 반복마다 Δ_T는 **새로 잰 값으로 바꾼다**(누적하지 않는다).
  * 근거: Δ_T는 'T_j 값 대비 그 점에서 온도가 더하는 몫'으로 정의되고, 문턱 대비 양이 아니다. 앞 반복의 Δ_T를 더하면 같은 온도 몫을 두 번 세게 된다.
  * 대안: 단조 최댓값 Δ_T(j) = max(Δ_T(j−1), 새 측정)이다. 문턱이 단조로 조여지므로 수렴(또는 front 빔)이 보장되지만, 한 번 큰 점의 여유가 남아 과하게 조일 수 있다. 교체 안은 진동할 수 있고, 그것은 멈춤 규칙과 반복 상한이 막는다. 선택을 바꾸는 것은 사용자 몫이다.
* **기록·입력 형식(기본안 O-1, D-24 안 B 기준)**: Δ_T는 값·단위·출처 지문을 가진 측정 기록이다(값·단위·출처 지문 -- 옛 상위 DEC-72 `model_error_<metric>` 형식은 상위 O-178로 삭제, 이름·형식은 design). 이름은 상위 DEC-68 규칙으로 design이 정한다(후보: `temp_margin_<metric>`, `range_margin_<metric>`, `delta_t_<metric>`). 쓰는 주체는 보정 루프 구동기(엔진 밖)다.
  * **엔진 입력 경로는 하나**: 구동기가 대조를 통과한 Δ_T로 다음 변형의 제약 입력(offset-strategy PD-1 '변형 제약 별도 입력', S-8)을 만든다. 문턱 합성값은 그 변형 제약 필드 하나에 writer 하나다(NFR-T3).
  * spec 측정 선언 절(지금 없음: 최상위 키는 `meta`·`human`뿐, F-23)은 Δ_T에 쓰지 않는다. 그 절은 쓰지 않는다(옛 상위 DEC-72 spec 형식은 상위 O-178로 삭제) -- TR-TL 범위가 아니다.
  * 그래서 TR-TL 범위의 배선은 구동기 → 변형 제약 입력 → 제약 행 문턱이다(만들면 배선, NFR-T5).
* **출처 지문**(T-30 '점·코드 해시·LUT·오라클 실행·표본 수, 지문 불일치 무효'): 원문 항목은 (c) 출처 무결성으로 대조하고, 대조 주체는 엔진 밖 구동기다(D-25, 사용자 결정 T-36).

| 묶음 | 항목 | 다음 실행에서 |
|---|---|---|
| 환경 항목(모든 해석에서 대조) | 엔진 코드 지문(`code_fp`), LUT 묶음 지문(파일 sha256·측정 조건), topology 지문(원본과, trim이면 trim 파일 sha256·합성 회로 지문·승인 기록 id), spec 지문(안 B에서 Δ_T는 spec에 들어가지 않으므로 spec 전체), 오라클 능력 기록 id(PDK·시뮬레이터 쪽 지문은 그 기록이 묶는다, N3.9), 오라클 코드 지문, 판정 온도 범위와 온도 점, k | 하나라도 다르면 그 Δ_T는 무효다. **엔진 밖 구동기가 거부한다**(`..._stale`, 이름은 design, fail-closed). 무효인 Δ_T는 엔진에 들어가지 않는다(T-36 (c-2)). 조용히 무시하거나 0으로 바꾸지 않는다 |
| 원문 항목 | 설계 점(front 점 id와 θ), 표본 수 n, 시드, 오라클 실행 id, 반복 번호 | (c) 출처 무결성(T-36): Δ_T가 인용한 오라클 결과 기록이 있고 그 내용과 일치하는지 구동기가 대조한다. 불일치하면 무효(정지) |

* **대조 기록(상위 DEC-72)과의 역할 구분**:

| 양 | 정의 | 쓰임 |
|---|---|---|
| 대조 기록(상위 DEC-72, 상위 사용자 결정 O-178 개정) | 같은 점·같은 조건(T_j)에서 엔진 값 대 SPICE 값 | 판정 기준 아님 -- 기록, 상위 oracle 닫기·E-2 근거(옛 '분해능 바닥(NFR-5)·front 판정 보류 해제'는 O-178로 폐지) |
| Δ_T | 같은 점에서 SPICE(범위 최악) − SPICE(T_j) | 엔진 제약 문턱 조임. 대조 기록과는 더하지 않는다(정의가 다름); 상위 닫기 Δ와의 문턱 합성은 상위 개정 전까지 하지 않는다(아래 문단·N3.8.7) |

  두 양은 서로의 자리에 쓰지 않는다. 멈춤 규칙(N3.8.5)의 분해능에는 오라클 측정 분해능을 쓴다. 상위 oracle 닫기의 Δ(상위 O-178 -- (점, metric)별 엔진 재풀이 입력)는 Δ_T(metric별 변형 입력, oracle − oracle)와 정의·축이 달라 자리를 통일하지 않는다(상위 DEC-72 (5)); 두 루프가 함께 돌 때의 문턱 합성 순서·자리는 상위 Q-W1 실현 평가와 함께 상위 계획이 정한다 -- 정해지기 전에는 합성하지 않는다(graph 규칙 6).

#### N3.8.4 불합격 몫 분해와 정지 판정

trim 잔여가 범위 불합격이면 design §3.8 분해를 불합격 표본·온도 점마다 쓴다. 잔여 R(T) = V_os(T) + s·t(T)·δ(T)에서
* (i) 원본 offset drift 몫(R(T) − s·δ_Tj·t(T)의 T_j 대비 변화)
* (ii) DAC 전류 drift 몫 s·(δ(T) − δ_Tj)·t(T)
* (iii) 전달 drift 몫 s·δ_Tj·(t(T) − t_Tj)
* 닫힘 잔차.

design §3.8의 '27 °C'는 T_j로 읽는다.

| 판정 | 규칙 | 행동 |
|---|---|---|
| **(ii) 지배**(O-3, X-20 정의 -- 사용자 결정 T-35로 확정) | 불합격 표본·온도 점 가운데 하나라도, (i)과 (iii)을 0으로 두어도 \|R_Tj + (ii)\| > V_res인 곳이 있다. 곧 크기(θ)로 줄일 수 있는 몫을 모두 없애도 불합격이다 | 다시 돌리지 않는다. `..._bias_drift_dominant`(이름은 design)로 정지하고 분해표를 보고한다. (ii)는 DAC 바이어스 원천(D-9)의 온도 특성이 정하는 몫이고 이 계획의 θ로 줄이는 경로가 없다. 다음 행동(바이어스 원천 변경)은 사용자 결정이다(D-22) |
| 닫힘 잔차가 분해 몫보다 크다 | 소신호 분해가 실제 DC 잔여를 설명하지 못한다 | 분해로 판정하지 않는다. 정지하고 보고한다(문턱 없이 값만, design §3.8과 같음) |
| 그 밖 | (i)·(iii)이 크기 조정으로 줄일 수 있는 몫이다 | Δ_T로 문턱을 조여 다시 돈다 |

* matching 제약에는 DAC가 없으므로 (ii)·(iii)이 없고 분해 정지 판정이 없다. 멈춤 규칙(N3.8.5)만 적용한다.
* T_j에서 이미 불합격(N3.8.1 전제 위반)이면 분해하지 않는다. 엔진·오라클 판정 문제(상위 O-178: 정의 관문·닫기)로 보고한다.

#### N3.8.5 루프와 멈춤 규칙

1. 엔진 실행(현재 spec, Δ_T 선언이 있으면 문턱에 적용) → front.
2. 판정 대상 점 선택(D-20 사용자 선언 규칙, 결정적).
3. 오라클 T_j 판정(TR-7 §17-1·2) → 실패면 정지(엔진·오라클 판정 문제 -- 상위 O-178, N3.8.4).
4. 오라클 범위 판정(N3.8.2) → 합격이면 **정지(합격)**.
5. 불합격 몫 분해(N3.8.4) → (ii) 지배 또는 닫힘 실패면 **정지(크기 조정 불가)**.
6. Δ_T 측정·선언(N3.8.3) → 멈춤 규칙 검사 → 통과하지 못하면 1로.

**멈춤 규칙**(상수 없음):

| 사유 | 조건 | 근거 |
|---|---|---|
| 수렴(불합격) | 모든 대상 metric에서 \|Δ_T(j) − Δ_T(j−1)\| ≤ 오라클 측정 분해능이다. 분해능 = 두 Δ_T의 측정 분해능을 합친 폭이다(T-39).<br>• matching σ 항: MC 표준오차에 신뢰 배수를 곱한 폭이다. 신뢰 배수는 spec k다(기본안 O-5, design X-T13 선례: 새 신뢰 상수를 만들지 않음). 한계: k는 '덮을 분포 폭'의 배수이지 신뢰 수준이 아니다. 같은 수를 신뢰 배수로 다시 쓰면, k를 바꿀 때 멈춤 기준도 함께 바뀐다. 보고서에 이 한계를 적는다.<br>• matching의 σ 항은 표준오차 σ̂/√(2(n−1))이 있다(F-21).<br>• trim 잔여(T-39): 오라클 DC 풀이 허용오차를 입력 환산으로 전파한 값이다. 같은 seed의 고정 표본 집합에서 재므로 반복 사이에 표본 추출 잡음이 없다. 그래서 이 양은 결정적 측정의 분해능이고 새 상수가 없다.<br>• 결정적 끝 표본은 Δ_T에 들어가지 않는다(G-14, 진단만) | T-30 '오라클 측정 분해능'(분해능 정의는 T-39). 같은 여유를 다시 걸어도 결과가 측정으로 구별되지 않으면 더 돌 이유가 없다 |
| front 빔 | 조인 문턱으로 돈 실행의 front가 비었다 | T-30 'front 빔'. 크기 조정 범위 안에서 범위 합격 해가 없다는 뜻이다 |
| 반복 상한 | 반복 수가 사용자 선언 상한에 닿았다 | T-30 '반복 상한 = 사용자 선언값'. **기본 상한은 만들지 않는다.** 선언이 없으면 루프를 시작하지 않고 첫 범위 판정 결과만 보고한다(D-19) |
| 판정 불능 | 비용 한도 초과·표본 부족(N3.8.2) | T-12 검증자 조건 (3) |
| 능력·지문 | 오라클 능력 기록 무효, Δ_T 지문 불일치 | fail-closed(N3.8.3, N3.9) |

모든 정지는 사유 코드(이름은 design)와 반복 이력(N3.8.6)을 남긴다. 수렴·front 빔·상한 정지는 '범위 불합격'이고 합격으로 세지 않는다.

#### N3.8.6 기록과 보고

반복마다 결과에 남긴다: 반복 번호, 적용한 Δ_T와 그 지문, 판정 대상 점, 범위 판정 표(온도 점 × metric 최악값), 분해표(trim), 비용 표와 실제 오라클 시간, 정지 사유. 결과 보고서는 마지막 반복의 front와 함께 이 이력을 싣는다.

#### N3.8.7 재사용 원칙과의 정합(반복 구조 D-24)
* **상위 oracle 닫기(사용자 결정 O-178)와의 관계**: 상위 닫기는 '그 점의 최적화를 다시 푼다'라 이 절의 '구동기는 이전 front 점을 시작점으로 주지 않는다'·X-23 '엔진은 오라클 결과 파일을 읽지 않는다'와 경계가 겹친다. 경계(실행 사이냐 한 실행 계획 안이냐, 엔진이 oracle 여유를 받는 경로)와 Δ_T·닫기 Δ의 문턱 합성은 상위 Q-W1 실현 평가와 함께 상위 계획 개정으로 정한다(상위 DEC-72 (5)) -- 그 전에는 이 계획 경로에 닫기를 넣지 않는다(graph 규칙 6).

**공통 규칙**(어느 안이든):
* 엔진은 이전 실행의 결과 JSON·S3 기록·front 점·graph 스냅샷을 읽지 않는다(U-89, S-3).
* 이전 반복에서 넘어가는 것은 대조를 통과한 오라클 측정값 Δ_T뿐이다.
* 구동기는 이전 반복의 front 점을 다음 탐색의 시작점으로 주지 않는다.
* 오라클은 별도 프로세스이고 엔진을 import하지 않는다(N6).
* S-3과의 경계: Δ_T는 엔진 계산 결과가 아니라 오라클 측정값이다. 안 B(확정)에서는 구동기가 대조한 뒤 다음 변형의 제약 입력으로만 넣는다. 엔진은 오라클 결과 파일을 읽지 않는다(X-23).

**반복 구조 두 안**(D-24 → **안 B로 확정, 사용자 결정 T-35**. 원래 취지와 다름 X-26 해소):

| 안 | 구조 | 반복 사이 계산 | 취지와의 관계 |
|---|---|---|---|
| A. 반복 = 별도 엔진 실행 | 구동기가 반복마다 Δ_T를 넣은 spec으로 엔진을 새 프로세스로 처음부터 돌린다 | 같은 topology의 단계 A·S0·블록 결과를 반복마다 다시 계산한다(입력이 Δ_T만 다름) | '실행 사이 재사용 금지'는 지킨다. 그러나 원래 취지("처음 topology를 실행할 때 계산하고 그 값을 나머지 최적화에서 재사용")와 gm/ID '빠른 설계' 취지에서 벗어난다 |
| **B. 반복 = 실행 계획 안의 변형(확정, T-35)** | 엔진 밖 구동기가 같은 프로세스에서 offset-strategy 실행 계획(S-2)을 유지한다. 변형 = 같은 topology + 문턱만 다른 제약 집합이다. 변형 하나가 끝나면 오라클(별도 프로세스)을 부르고, Δ_T가 들어간 다음 변형을 계획에 추가한다 | 단계 A·S0·블록 결과 색인을 실행 계획 수명 동안 공유한다. 문턱에 의존하는 블록만 다시 계산한다 | 원래 취지에 맞다. 실행 수명은 '실행 계획 하나'(OS N3.6, XS-7)이므로 실행 사이 재사용이 아니다. 메모리 순차(NFR-T9)와도 맞는다 |

**두 안의 입력 경로·대조·대가(v0.5.2)**:

| 항목 | 안 A | 안 B |
|---|---|---|
| Δ_T 입력 경로 | spec 측정 선언 절 하나(F-23의 미구현 경로를 TR-TL이 만든다). 엔진은 새 프로세스에서 spec을 로드할 때 받는다 | **같은 프로세스의 다음 변형 제약 집합 하나**. 구동기가 변형을 추가할 때 문턱 = spec 문턱 − Δ_T를 그 변형의 제약 입력(offset-strategy PD-1 '변형 제약 별도 입력', S-8)으로 넣는다. spec 측정 선언 절로는 넣지 않는다(입력 경로 둘 금지, graph 단일 정본: 문턱 합성값은 그 변형 제약 필드 하나에 writer 하나) |
| 지문 대조 시점·주체 | 시점 = 엔진 spec 로드 때. 주체 = 엔진 로더(환경 항목) + 구동기(원문 항목, D-25 (c)) | 시점 = 변형 추가 직전. 주체 = 구동기(환경 항목·원문 항목 모두). 엔진에는 대조를 통과한 값만 변형 제약으로 들어간다 |
| spec 측정 선언 절 | Δ_T와 DEC-72 모델 오차가 함께 쓴다 | 상위 사용자 결정 O-178로 DEC-72 옛 spec 형식이 삭제되어 남는 쓰임이 없다. Δ_T에도 쓰지 않으므로 그 절의 로더·배선은 만들지 않는다 |
| 대가 | 반복마다 단계 A·S0·블록 결과 재계산(시간) | 엔진 프로세스가 실행 계획(S0·블록 결과 색인)을 메모리에 든 채로 오라클 MC가 돈다. 실행은 순차지만 메모리는 동시에 점유한다. 실행 계획에 '실행 중 변형 추가' 인터페이스가 필요하다 |

* **안 B에 필요한 것**: 실행 계획이 **실행 중에 변형을 추가하는** 인터페이스가 있어야 한다.
  * 지금 offset-strategy의 `build_run_plan`은 실행 전 결정적 순수 함수로 변형 목록을 고정한다.
  * 그래서 offset-strategy 계획과의 연결 항목이다. 변형 정체(제약 집합 지문)가 반복마다 다르다는 점, 변형별 예산(XS-12), Σ 색인 상한(OS N3.7)이 함께 걸린다.
  * 오라클 결과가 들어오는 입력은 대조를 통과한 Δ_T 하나로 제한한다.
  * '문턱에 의존하는 블록' 목록(완료 조건 7의 '문턱 무관 블록 재계산 0' 측정용)은 G-12에서 정한다.
* **안 B의 S-3 경계**: 오라클 측정값 Δ_T가 같은 실행 계획 안에서 다음 변형 입력이 된다. 이전 변형의 엔진 결과(front 점 등)는 입력이 아니다.
* 안 B가 확정됐으므로(T-35) 안 A 열은 기각된 대안의 기록이다. 이 계획의 TR-TL 범위·완료 조건은 안 B 기준이다.

### N3.9 오라클 능력 의존(T-31, T-33 -- 절차는 oracle-portability 계획 소유)

**소유 경계**: 공정 무관 오라클 능력 확인의 절차, PDK 기술자, 확인 test, 능력 기록 형식은 새 계획 **oracle-portability**(SPICE 오라클 시뮬레이터·공정 무관화, 사용자 결정 T-33)가 정한다. 이 계획은 그 결과를 **의존**으로만 쓴다. 이 계획에 쓰던 초안은 `wt/_drafts/oracle_capability_handoff_from_offset_trim_v05.md`로 옮겨 그 계획의 입력으로 넘겼다(history H1 2026-10-16).

**이 계획의 의존 규칙**:
1. **허용 조건**: 범위 판정(N3.8.2)과 보정 루프(N3.8.5)는 유효한 **오라클 능력 기록**이 있는 (PDK, 시뮬레이터) 조합에서만 허용한다. 능력 기록의 형식과 유효성(지문 대조)은 oracle-portability가 정한다.
2. **fail-closed**: 유효한 기록이 없거나 낡았으면 범위 판정과 루프를 거부하고 사유를 보고한다. 조용히 T_j 한 조건 판정으로 내려가 '합격'을 내지 않는다. 결과에는 '범위 미판정'을 적는다(FR-T9).
3. **이 계획이 능력 기록에 요구하는 확인 항목**(내용 요구일 뿐이고 절차·합격 규칙은 oracle-portability 소유):
   * MC 불일치가 실제로 분산을 만든다(네이티브 MC, oracle-portability v0.4 O-1). 그 크기가 공정 문서의 선언 계수와 일관한지는 **능력 기록이 아니라 TR-7 판정**(§17-1 σ_in 일치)에서 확인한다(oracle-portability v0.4 변경).
   * 온도 지정이 동작점을 실제로 바꾼다. 결과에서 읽은 실제 온도가 요청 온도와 같다.
   * 같은 seed의 네이티브 MC 표본(같은 불일치 값)의 정체가 온도 사이에 보존된다(N3.8.2 '같은 표본을 모든 온도 점에서'). 꼬리 판정(G-14)이 이 항목에 기댄다.
   * 오라클 모델이 엔진 LUT와 같은 모델이다(모델 파일 해시 대조).
   * 오라클이 LUT `temp_c`와 따로 온도를 받을 수 있다(지금은 전용 입력이 없음, F-19).
   * **(v0.5.1, v0.6)** 온도 점마다 계통 offset V_id*(T)를 잴 수 있다. 지금 MC는 계통 offset을 빼고 흔들림만 잰다(F-20a). 측정은 PC-10 = OP-5 `offset_sys_mv` `.dc`를 온도 조건에서 돌린 것이고 기준은 DEC-23이다(O-53 B3, G-15 닫힘).
   * (철회, v0.5.4) 결정적 불일치 벡터 표본 요구(oracle-portability 쪽 PC-11)는 G-14를 네이티브 MC 표본 안에서 풀어서 필요 없다(T-35). 결정적 섭동은 진단 전용이다(oracle-portability v0.4 O-1).
4. **지문 연결**: Δ_T 출처 지문(N3.8.3)의 대조 항목에 능력 기록 id를 넣는다. 능력 기록이 바뀌면 Δ_T는 무효다.
5. **공정·회로 이름 금지**: 이 계획의 범위 판정·루프 규칙과 루프 도구에도 PDK 이름·모델 변수 이름을 넣지 않는다(NFR-T7). sky130은 첫 적용 사례일 뿐이다(T-31).

**순서 의존**(v0.6, 감사 D4 -- 옛 '오라클 계획은 아직 초안' 사실 정정): oracle-portability 계획은 v0.6.9가 승인·병합됐고(사용자 O-48) v0.6.10(사용자 O-57, 최종 머리 `64687b21`)과 현행 v0.6.11(사용자 O-60, 최종 머리 `83530559`)도 승인·병합됐다. 이 계획의 오라클 판정 선행은 **OP-3**(입력 형식 전환·코어 판정) → **EO-1**(gain-budget N6.20, 엔진 점 → oracle 입력 생산자) → **OP-5**(불일치 σ의 A = `.tf`, 계통 offset `.dc` V_id*, 오라클 한 단계 전도 판정 -- 상위 O-205 (2)·O-210 RR-2, 네이티브 MC) → **OP-6**(능력 확인, 현재 PDK 기술자의 능력 기록 -- 사례: sky130)이다. TR-7(§17-1부터 MC를 씀)과 TR-TL의 오라클 판정은 OP-6 능력 기록 뒤에야 판정으로 센다. card 순서의 정본은 gain-budget N6.1이다(N5). (v0.7) trim 사양을 정하는 oracle MC(N3.10)도 같은 OP-6 능력 기록 뒤에만 사양 근거로 센다(T-31, O-258 (A) '선행').

### N3.10 MC 시점과 DEC-110 5단계 자리(v0.7, 사용자 결정 O-258 (A))

상위 gain-budget v6.39.0 DEC-110(master 병합 `57a014b2`)의 5단계 안에서 offset 쪽 규칙의 자리는 다음 하나다. 단계 번호는 DEC-110의 것이고, 국면 2는 같은 (1)(2)를 합성 회로로 다시 도는 것이다(5단계 순서를 바꾸지 않음).

| DEC-110 단계 | 엔진(숫자와 관문) | 엔진 밖(구동기·oracle·AI·사용자) | offset 규칙 |
|---|---|---|---|
| (1) 사이징 + floorplan 추정 -- 원본(국면 1) | θ 탐색·front, σ_in·V_id*, 후보표(FR-T2), trim 필요 판단 값 | AI: 방식(요구 `strategy`)은 사용자 선언 -- AI는 근거만 제시 | matching이면 offset-strategy N3.3 유도 제약, trim이면 랜덤 offset 판정 없음(N3.6). 엔진 σ_in은 trim 사양을 정하지 않는다 |
| (2) SPICE 닫기 -- 원본 | E-1 닫기(상위 N6.3) | **닫힌 실현 점에서 oracle MC**(σ_MC)와 oracle `.dc`(V_id*, OP-5) → trim 사양 기록(구동기 함수 하나) → AI가 trim 파일·의도 문서 제안 → 사용자 승인 + σ_MC 선언 채택 | MC 시점·표본 수·사양 규칙(아래). 승인 게이트가 실행을 끊는다(국면 1 → 국면 2) |
| (1′) 사이징 -- 합성 회로(국면 2) | 합성 로더(N3.3), 부담 사이징(N3.11), 국면 2 판정(N3.4), E-0 | -- | 같은 θ 부담 → 위반이면 원본 θ까지 재풀이(N3.11) |
| (2′) SPICE 닫기 -- 합성 회로 | E-1 닫기 | **trim 뒤 잔여 MC**(oracle, 표본마다 최적 코드 -- N3.12), 온도 범위 판정·보정 루프(N3.8 -- Δ_T 변형) | 잔여 판정·범위 판정. 합격 = trim 포함 설계 확정 입력 |
| (3) floorplan 확정 -- 설계 확정 | MOD7 행 구성(상위 LY13)이 합성 회로의 실현 (m, w_f, L)을 읽음 -- trim 소자도 같은 행 구성 규칙(출처 칸으로 규칙을 가르지 않음, 이름 무관) | AI: 패턴·종횡비 | **trim은 (3) 전에 확정**: 승인 기록·잔여 MC·범위 판정 합격 없이 (3)에 들어가지 않는다(fail-closed) |
| (4) 상세 레이아웃 | 관여 0 | AI(trim 소자 포함 생성 스크립트·의도 문서) | -- |
| (5) 확인 루프 | 추출 기하 재평가(상위 LY7 꼴) | oracle MC·`.dc` V_id* **확인만**(trim 사양을 다시 정하지 않음) | 불합격이면 상위 LY14 판독: 레이아웃 원인 → (3), 모형 밖 양 → (1′); trim 사양 자체가 모자라면 trim 파일 재제안·재승인(엔진이 사양을 바꾸지 않음). (5)의 추출 기하 입력 자리는 상위 N5.3 Q-AF1 **정본 자리 미정** -- 개정 전에는 (5) offset 확인의 추출 기하 몫을 '미정'으로 표지하고 판정으로 세지 않는다(graph 규칙 6) |

**MC 시점 규칙**:
* trim 사양을 정하는 MC는 (2) 닫기를 지난 **실현 점**(상위 DEC-108 (6) 실현 평가 -- 정수 m·w_f, floorplan 추정 포함 입력은 EO-1 생산자가 냄)에서만 돈다. 탐색 평가 점(연속 W)·닫기 전 점은 실현 기하가 아니라서 거부한다(fail-closed).
* σ_MC와 엔진 σ_in은 같은 정의의 다른 측정 출처이고(N0.1), 둘의 차는 대조 기록(상위 DEC-72)이며 판정 기준이 아니다(원칙 2).
* **표본 수** n = 1 + ⌈1/(2·r_σ²)⌉(r_σ = spec σ 정확도 선언, N0.1 -- 새 상수 없음). r_σ가 없으면 사양 MC를 거부한다. 비용 표를 실행 전에 내고, 한도를 넘으면 '판정 불능(표본 부족)'이며 n을 줄이지 않는다(T-12 (3)). trim 잔여 MC의 표본 수(design §17 식 S)와는 측정 목적이 다른 양이다(축 = σ 추정 정확도 대 잔여 꼬리 판정).
* **trim 사양 기록**(writer = 엔진 밖 trim 구동기 함수 하나, 자리 G-12): R = k·σ_MC + \|V_id*\|(V_id* = 같은 실현 점 oracle `.dc` 기록), LSB 입력 환산 상한 = 2·V_res, N_min = ⌈log2(R/V_res + 1)⌉. k·V_res는 spec 참조, σ_MC·V_id*는 oracle 기록 id 참조(값 사본 없음). 출처 지문 = oracle 능력 기록 id·EO-1 입력 지문·표본 수·시드(N3.8.3 출처 지문과 같은 묶음 규칙).
* **승인 뒤 σ_MC 선언**: spec `offset_trim`의 σ_MC 칸은 사용자가 채택한 선언값이고 출처 칸에 MC 기록 id를 적는다(T-1 V_res와 같은 사용자 선언 성질; 기록과의 일치 대조는 승인 단계 -- 엔진 밖). 엔진은 이 칸만 읽고 oracle 기록을 읽지 않는다(X-23·S-3). 정의가 다른 두 자리(측정 기록 대 채택 선언)이므로 같은 정의 필드 둘이 아니다(축 = 출처: 측정 대 채택, graph 규칙 3).
* **(5) 뒤 확인**: 레이아웃 뒤 실현 기하에서 같은 MC·`.dc` 측정으로 잔여 분포와 계통 offset을 확인만 한다. 확인 불합격은 위 표 (5) 행.
* **선행**: oracle MC 능력 기록(T-31, oracle-portability OP-6)이 없거나 낡았으면 사양 MC·잔여 MC를 거부한다(N3.9, fail-closed).

### N3.11 trim 부담(v0.7, 사용자 결정 O-258 -- offset-strategy 실행 계획 변형 틀 재사용)

**정의**: spec 판정 제약이 있는 metric μ마다, 같은 θ에서 원본만 변형의 값 v_O와 합성 회로 변형(봉인 코드 = 중간 코드)의 값 v_C를 잰다. 부담 = max(0, s_μ·(v_C − v_O))이고 s_μ는 그 제약을 어기는 방향이다(≤ 제약이면 +1, ≥ 제약이면 −1 -- N3.8.3 Δ_T 방향 규칙과 같은 꼴). 판정 제약이 없는 metric은 부담을 보고만 한다.

**부담 제약**: 부담 예산 B_μ가 선언된 metric은 부담 ≤ B_μ, 곧 합성 회로 값의 문턱 s_μ·v_C ≤ s_μ·v_O + B_μ다. 선언이 없는 metric은 부담 제약 없이 합성 회로 spec 판정만 받는다(O-258). 예산 값은 사용자 선언이고 기본값은 없다(새 상수 금지).

**변형**(정본 offset-strategy N3.12 '추가할 수 있는 변형' (ii)(iii) -- 새 인프라 없음):
1. **변형 O** = (원본 topology, spec 제약): 국면 1과 같은 탐색 → front → 판정 대상 점 선택 규칙(D-20, 사용자 선언 결정적 규칙)으로 θ_0. 국면 1 결과를 읽지 않고 같은 실행 안에서 다시 얻는다(S-3·U-89 -- 결정성으로 국면 1과 같은 점). θ_0는 σ_MC를 잰 닫힌 점과 다를 수 있고, 그 차는 trim 뒤 잔여 MC가 판정한다.
2. **변형 C** = (합성 회로, spec 제약 + 국면 2 trim 제약(N3.4) + 부담 제약; **고정 θ 성분** = 출처 칸이 원본인 소자의 θ 성분 = θ_0(참조 = 변형 O 선택 점 기록 id, 값 사본 없음), 탐색 = trim θ 성분만): 목적 = 주입 넷 부가 용량·부가 컨덕턴스·trim 전력(N3.4 metric, 비지배 front -- 가중치 상수 없음). 엔진 밖 구동기가 O가 끝난 뒤 추가하고, 부담 문턱 항목(v_O 기록 참조 + B_μ spec 참조)을 추가 한 번에 한 번 만들어 변형 제약 별도 입력 `derived`로 넣는다(Δ_T 문턱과 같은 경로·같은 writer 규칙 -- offset-strategy N3.12 ①②).
3. **변형 C′**(C의 front가 비었을 때만) = (합성 회로, spec 제약 + 국면 2 trim 제약, 고정 θ 없음, 부담 제약 없음 -- 원본 θ가 바뀌면 '같은 θ' 비교가 정의되지 않으므로): 원본 θ까지 합성 회로 기준으로 다시 푼다(O-258 '부담 위반이면 원본 θ까지 재풀이'). C′도 비면 `trim_config_infeasible`로 멈추고 AI 재제안(N3.1-6).

**θ 성분 소속**: θ 성분의 소유 소자가 모두 원본이면 원본 성분, 모두 trim이면 trim 성분이다. 둘이 섞인 성분(같은 L 동치류·같은 KVL 고리 성분 등)이 있으면 고정이 정의되지 않으므로 변형 C를 추가하지 않고 사유를 기록한 뒤 C′로 간다(fail-closed가 아니라 정의역 규칙 -- 섞임 판정은 소자 출처 칸 READS, design G-24).

**보고**: 부담 표(FR-T9), 어느 변형이 front를 냈는지(C / C′), 섞인 θ 성분 목록.

### N3.12 디지털 코드(v0.7, 사용자 결정 O-258)

* **엔진 몫**: trim 파일의 코드 입력 선언·코드 상태 선언만 읽는다. 코드를 탐색하거나 저장하지 않는다. 코드 상태별 intended_region은 합성 로더가 선언에서 만든다(N3.5, O-249).
* **엔진 밖 몫**: 코드 탐색(표본마다 최적 코드 선택)은 oracle 쪽 확장(레인 P, N6)이고, 코드 저장 방식(OTP·퓨즈·레지스터)·디코더는 범위 밖이다(T-1).
* **oracle 검증**: trim 뒤 잔여 MC에서 표본마다 코드 공간 안의 최적 코드를 고른 뒤(결정적, 탐색 방식은 oracle 쪽 design) 잔여 분포를 잰다. 합격 = 창 안 표본 전부의 잔여 ≤ V_res(design §17-2 창 규칙, 완료 조건 3). 코드 공간 = trim 파일 코드 입력 선언의 비트 전 조합이다(엔진·oracle이 같은 선언을 읽음).

---

## N4. library 13회로 적용 판정 방법

판정은 규칙으로 하고, 단계마다 '해당 없음'은 사유 코드로 남긴다.

1. spec에 trim 선언이 없으면 → 무동작이다(완료 조건 (1)).
2. 입력 셀 안에 derived `diff_pair`가 없으면 → 차동 입력 포트가 없는 경우는 `trim_single_input_unsupported`(D-8), 그 밖은 `trim_pair_undefined`.
3. 모든 (쌍, 극성)의 \|t\| = 0이거나 headroom 창이 비면 → `trim_injection_infeasible`. 탐색 전에 유도와 함께 보고한다.
4. 그 밖은 → 후보표를 낸다.

**적용 예상**(2026-10-15 topology 연결 읽기 기준이고 엔진 실행 결과가 아니다. 확정은 card TR-7의 측정이다. trim 선언 여부와 값은 사용자 몫, D-11):

| 회로 | 입력 | 입력 쌍 (n쪽 게이트 / p쪽 게이트) | 예상 주입 쌍 drain 넷 | 부하 형태(연결로 본 것) | 현재 offset 항목 | 예상 판정 |
|---|---|---|---|---|---|---|
| current_reuse_telescopic_ota | 차동, 상보 | pmos M1a/M1b, nmos M4a/M4b | N1a2a/N1b2b, N3a4a/N3b4b | 각 drain → 캐스코드(M2a/b, M3a/b) | `offset_in_sigma_mv <= 3.3`, `offset_sys_mv` | 후보 두 쌍(D-7). 기존 절대 제약과 공존 처리 D-4 |
| folded_cascode | 차동 | nmos M1/M2 | X/Y | fold 넷(M3·M6 / M4·M5) | `offset_excess` | 후보 |
| ngcc_3stage_ff | 차동 | pmos M1/M2 | ND/V1 | 미러 부하(M3/M4), 단일 종단 | `offset_excess` | 후보(z[diode] ≈ −z[out]) |
| nmcnr_amplifier | 차동 | pmos M102/M103 | NodeF1/NodeF2 | fold 넷(M104·M106 / M105·M107) | `offset_excess` | 후보 |
| sf_pushpull_output_opamp | 차동 | nmos M1/M2 | N1/N2 | MOS 소스·drain 연결 없음(수동소자 부하로 보임) | `offset_excess` | 후보 |
| two_stage_ota | 차동 | nmos M1/M2 | D3/O1 | 미러 부하(M3/M4), 단일 종단 | `offset_excess` | 후보 |
| two_stage_ota_sf | 차동 | nmos M1/M2 | D3/O1 | 미러 부하(M3/M4), 단일 종단 | `offset_excess` | 후보 |
| common_gate_amplifier | 단일(소스 구동) | 없음 | -- | -- | 없음 | `trim_single_input_unsupported` |
| pushpull_follower_buffer | 단일 | (M3 pmos, M4 nmos가 같은 입력 게이트) | -- | -- | 없음 | `trim_single_input_unsupported` |

* 예상 차동 입력 후보는 7회로다. 각 회로에서 derived `diff_pair`가 실제로 생기는지는 TR-2에서 측정한다. 생기지 않으면 2번 사유로 보고한다.
* 근거는 `assets/library/<회로>.topology.json`(ports, netlist)과 `<회로>.sizing_spec.json`(current_reuse :225-242, folded_cascode :49-51 등)이다.

---

## N5. 단계 분할 초안(card 후보)

**공통 착수 조건**:
* T-4 순서를 지킨다(NFR-4 card 2 → XRUN-F1 A·B·C 병합 뒤). 그 뒤 순서는 offset-strategy S-4와 그 계획 v0.5의 card 이름대로 **… → XRUN-F1 C → OS-2(실행 계획 구현) → TR-1**이다.
* **순서 정본과 선행 규칙**(v0.6, 감사 D1·D2·D3·D4): card 순서의 유일한 정본은 gain-budget N6.1이다. 이 표는 이 계획 card의 선행 관계만 적는다. gain-budget N6.1은 'offset-trim TR-* 전부' 행(다른 계획 card 인용 규칙)으로 이 계획 card를 인용한다(옛 'gain-budget 쪽 개정 몫(N7.4 후속)' -- v0.6.2 백로그 재감사 OT-B9로 닫음).
  * (a) 동작 변경 card(TR-2~TR-6, TR-7, TR-TL)의 **완료 판정**은 EO-1(gain-budget N6.20) 완료 판정 뒤다. 병합 선행이 아니다(gain-budget N6.3 보류 다리 규칙).
  * (b) 오라클 판정 선행 = OP-3·OP-5, 그리고 MC·온도 판정은 OP-6 능력 기록(N3.9).
  * (c) 계통 offset의 엔진 `verified_by` 연결은 gain-budget VB-1(N6.18)이 선행이고, 이 계획은 다시 연결하지 않는다.
* **v0.5 card 순서**: TR-0T(design 보완) → … → TR-6 → TR-7 → TR-TL(보정 루프).
  * 외부 선행: oracle-portability 계획 승인과, 그 계획의 능력 확인 card가 만든 현재 PDK 기술자의 능력 기록이다(사례: sky130). 이것이 있어야 TR-7·TR-TL의 오라클 판정이 판정으로 센다(N3.9. card 이름·시점은 그 계획 소유).
  * TR-TL의 matching 쪽 적용은 offset-strategy OS-2 뒤다. 그리고 offset-strategy card **OS-V**(matching 유도 제약에 오라클 측정·`verified_by` 붙이기, 사용자 결정 S-11)가 TR-TL 앞이다.
  * **임계 경로**(v0.6 갱신): G-15(V_id*(T) 출력 기준)는 사용자 결정 O-53 B3으로 닫혔다. 그래서 oracle-portability OP-6의 G-15 착수 조건은 이 계획 쪽에서 충족된다(그 계획에 알림, N7.4). TR-0T는 TR-7 판정의 design 선행으로 남고, 다른 TR card 진행과 병렬로 먼저 끝낸다.
  * TR-TL은 안 B(D-24, T-35 확정)다. (v0.7) offset-strategy 실행 계획의 '실행 중 변형 추가' 인터페이스(card OS-L)의 **첫 소비자는 부담 변형 card TR-B**가 된다(N3.11 -- 변형 C·C′ 추가). '만들면 배선'(offset-strategy v0.6 근거)대로 OS-L은 TR-B와 **같은 변경**에서 병합하고, TR-TL은 그 인터페이스를 쓰는 둘째 소비자다(옛 'OS-L은 TR-TL과 같은 변경' -- 원래 취지와 다름 X-38).
* **(v0.7) LA-1과의 자리**(사용자 결정 O-229 (4) -- 새 card는 LA-1을 실제로 막을 때만 LA-1 안): TR-* card는 **전부 상위 card LA-1 병합 뒤**다. 근거: (i) 상위 N6.1의 LA-1 선행·완료 조건 어디에도 trim 필드·trim card가 없고 LA-1 측정(2회로 연기)은 trim 선언 없는 실행이다(trim 없는 실행 = 이 기능 무동작, 완료 조건 1) (ii) TR card의 외부 선행이 이미 LA-1 뒤다 -- offset-strategy OS-2는 LA-1 뒤(상위 N6.1 병합 순서 규칙 표 #8·#9, O-183), off 스위치 LUT 확장(O-212)은 PD-1 뒤(표 #20), oracle 판정은 EO-1·OP-5·OP-6 뒤 (iii) 상위 DEC-110 흐름의 card(LY-1·WR-1·AF-1)도 LA-1 뒤다. 그래서 TR-0(design 문서)도 LA-1 뒤에 착수한다(O-229 (3)(4) -- LA-1 전 문서 작업은 이 계획 개정까지).
* design 문서 `docs/02-design/features/offset-trim.design.md`가 있고, 독립 검증과 사용자 승인을 받았다(bkit PDCA).
* 그 card가 읽는 N7 결정이 닫혀 있다.

| card | 범위 | 선행 | 읽는 결정 |
|---|---|---|---|
| TR-0 (문서, v0.7 묶음) | design 개정 하나로 묶는다(옛 TR-0T 개정 몫 포함 -- 작은 문서 card 묶기): (1) O-258 몫 -- trim 파일 스키마(G-21), 합성 로더 블록·층·소자 출처 칸(G-22), 코드 입력·코드 상태 선언과 코드 상태별 intended_region 생성 규칙(N3.5), spec `offset_trim` 새 칸(r_σ·σ_MC·부담 예산 -- 이름 DEC-68), trim 사양 기록 형식·구동기 서명(N3.10), 부담 변형 O·C·C′와 부담 metric 집합·방향(G-23)·θ 성분 소속(G-24), 국면 정의, 승인 기록 형식, 실패 코드, test 목록 (2) v0.6 N7.5 후속 정정 여덟 행 (3) v0.6.2 TR-0T 개정(OT-B3·B6·B10) (4) N7.6 낡은 자리 표 전수. 옛 §7(`augment_trim`)·§6.3(`trim_decl` 합성)·§9.4·§9.5(추천·파생 출력)는 같은 변경에서 지운다. 독립 검증·design↔계획 gap 0 | 이 계획 v0.7 승인, 상위 card LA-1 병합(O-229 (4)) | D-1~D-25(v0.7 대상 소멸 표지 포함), G-1~G-15, G-21~G-24, O-258 |
| TR-1 | spec `offset_trim` 스키마와 로더(새 칸 r_σ·σ_MC·부담 예산 포함, 요구 섹션 로더와 함께 -- offset-strategy N3.9 'TR-1 범위'), 로더 규칙(요구와 수단 제약 공존 = offset-strategy N3.2), spec 지문 결속(N3.3-1). (v0.7) 옛 `trim_decl` 합성(D-15)은 없다 | TR-0, offset-strategy OS-2 | D-1·D-2·D-4·D-12·D-13 |
| TR-2 | 노드 수반 벡터 z의 graph 필드 노출(F-2), 주입 쌍 규칙(N3.2), t·극성 headroom·잡음, trim 필요 판단 값, 국면 1 후보표 결과 JSON(FR-T2), offset-strategy 국면 1 행(N3.5 PD-2 TR-2 몫). 보고만 한다. (v0.7) 옛 '1단계 N·m 추천'은 없다 | TR-1, OS-2(T-15) | D-3·D-5·D-6·D-7 |
| TR-MC (v0.7 새) | trim 사양 구동기(엔진 밖, G-12 자리 -- TR-TL 구동기와 같은 도구): 닫힌 실현 점의 oracle MC(표본 수 = r_σ 유도)·`.dc` V_id* 호출(oracle 입력 = EO-1 생산자), trim 사양 기록 쓰기(N3.10), 비용 표 선보고, 능력 기록 의존 거부. **만들면 배선**: 소비자 = trim 파일 제안·승인 단계의 근거 칸(N ≥ N_min 대조) -- 같은 card에서 그 대조를 배선한다 | TR-2, 상위 card CL-1(E-1 닫기 -- 닫힌 실현 점의 생산자; 그 전에는 '닫기 전 점' 거부로 사양 MC가 돌지 않음), 오라클 선행 OP-3·EO-1·OP-5·OP-6 능력 기록 | O-258 (A), T-31 |
| TR-3 | trim 파일 로더(N3.3 스키마 검사), 합성 로더 블록(합성 회로·소자 출처 칸·코드 상태별 intended_region), 승인 기록 로더·결속 검사·낡은 승인 정지(N3.3-3), 합성 회로 connectivity 표 도구(같은 블록 호출), offset-strategy 국면 2 분기(PD-2 TR-3 몫), 진입점 배선. (v0.7) 옛 `augment_trim`·출처 기록·파생 topology 출력은 없다 | TR-2, 사용자 승인된 시험 회로 trim 파일(T-24 fixture -- 배선 증거 입력, 승인 전에는 쓰지 않음 -- T-9·T-17) | D-9·D-10·D-13, O-249 |
| TR-4 | `trim_dac` 역할 유도(소자 출처 칸 READS -- S1·S1v 신호 경로 제외, DC writer 바이어스 전류원), 가드·부하 집합 제외, 합성 대 원본 구조 동일 검사(N3.3-2, G-2). **착수 조건**: 규칙 지문 변경에 따른 structure.json 2개 재승인 계획을 사용자가 승인한다. **병합 조건**: 재승인을 마친다 | TR-3 | D-13·D-14 |
| TR-5 | DAC 규칙(N3.4)의 I_u(θ, T-7)와 보정 구간(σ_MC 선언 참조)·잔여 제약과 metric(주입 넷 부가 용량·부가 컨덕턴스·trim 전력 포함), 끝 코드 봉인점 1차 감도 추정(N3.5, O-53 A3 -- 균형 풀이 없음), 보정 구간 판정 W(N3.4, O-45 U3), 되돌림 사유. (v0.7) 국면 2 탐색 게이트 해제는 TR-B로 옮긴다(TR-B와 같은 통합 병합 -- offset-strategy N3.5 v0.8 항목) | TR-4, LUT 확장(O-212 -- 상위 N6.1 표 #20 PD-1 뒤) | D-1·D-3·D-17, T-7 |
| TR-B (v0.7 새) | trim 부담(N3.11): 변형 O·C·C′, 고정 θ 성분(출처 칸으로 소속 판정), 부담 문턱 항목(구동기 → `derived`), 부담 표 보고, 국면 2 탐색 게이트 해제(옛 TR-5 몫). **offset-strategy OS-L(실행 중 변형 추가)과 같은 변경**(첫 소비자 -- 만들면 배선), TR-5와 같은 통합 병합(TR-5 metric·제약의 제품 경로 소비자가 국면 2 변형이라서) | TR-5, offset-strategy OS-5(다변형 공유 -- TR-2와 함께 이미 병합), OS-L 범위(같은 변경), DS-1 결정(O-176 Ⅵ (나)) | O-258, XS-21·XS-22(offset-strategy) |
| TR-6 | offset spec 의미 전환(N3.6), `iv_matching_l` 변경 | TR-B | D-4 |
| TR-7 | library 13회로 일반성 측정(N4 사유표), 선언 회로 E2E(시험 회로 + 승인된 trim 파일), SPICE 오라클 대조(코드 스윕·trim 뒤 잔여 MC -- 표본마다 최적 코드, N3.12), 온도 검증(N5.1: v0.5부터 trim 잔여는 범위 판정, 나머지는 보고) | TR-6, TR-MC, 오라클 확장(레인 P: 코드 입력·표본별 코드 선택·LUT와 따로 받는 온도 입력 -- OP-5 새 코어 위, 그 입력 칸은 EO-1 생산자를 G-18 + U-6 규칙으로 갱신해 낸다(감사 B4)), **외부 선행: OP-3·EO-1·OP-5와 OP-6 능력 기록(현재 PDK 기술자 -- 사례: sky130)**(N3.9). 판정 = O-34 동작 변경 네 다리(상위 N6.3 -- SPICE 다리 = 상위 O-178 oracle 판정: 정의 관문 + 닫힌 점, 수치 차 = 대조 기록)(감사 B5, N6) | D-11, D-18 |
| **TR-0T** (문서, v0.5 -- **v0.7: card TR-0에 합침**, 아래 범위는 TR-0 (3) 몫으로 그대로 읽는다) | design `offset-trim.design.md` 보완: §3.8(분해를 범위 판정·정지 판정에 씀, '27 °C' → T_j), §5.3(엔진 판정 온도는 그대로, 범위는 오라클), §10.6(문턱 = spec − Δ_T 합성. 옛 이름 `value_from_spec` 표기 정정, `verified_by`), §17(3번 판정 승격, 범위 판정·같은 seed 네이티브 MC 표본 정체 보존, 결정적 끝 표본은 범위 판정·Δ_T에서 빼고 진단만(G-14 닫힘, T-35), T_j 판정의 끝 표본 역할을 oracle-portability v0.4 O-1(결정적 섭동은 진단만)과 맞춤, §17-1에 '크기 일관'(선언 계수 대비 σ) 판정 이관, **§17-3·5의 T-14 숫자 표기를 spec 판정 온도 범위 선언 참조로 바꿈**(T-34)), 새 절(Δ_T 기록 형식·지문, 구동기·실행 중 변형 추가 서명·사유 코드, 능력 기록 의존 검사의 위치). G-9~G-13, G-15를 닫는다. 독립 검증과 사용자 승인. **(v0.6.2 백로그 재감사 OT-B3·B6·B10) design 개정 `plan_version` 0.6.2**: (1) G-12 '문턱 의존 블록 목록'에 상위 LA-1 역산 조립 블록을 넣고 L 하한은 상위 LR6 인용(사본 금지), G-1·G-6·G-15의 O-53 해소 문언 반영(OT-B3) (2) N7.5 design 후속 정정 여덟 행 반영 + 함수 레지스트리 §2 '고정 기하 DC 균형 풀이' 행 삭제(같은 변경, OT-B10) (3) Δ_T 측정 기록 형식(이름 DEC-68) -- 상위 ME-1·`model_error_<metric>` 형식은 상위 O-178로 삭제되어 인용 대조 대상 없음(OT-B6 대상 소멸). **완료 측정**: design↔계획 gap 0, design grep '균형 풀이'·'A_dm'·'V_sys,s'·`offset_systematic` 0(history 제외) | 이 계획 v0.5.4 승인(T-29~T-37, 사용자 결정 모두 닫힘 -- 착수 가능). 능력 기록 형식은 oracle-portability v0.4.2(master `d579939`) design을 인용하고, 실행 계획 연결은 offset-strategy v0.6.1(master `194981f`)을 인용한다 | D-18~D-20, D-22, D-24, D-25, O-1, O-3~O-8, G-9~G-15 |
| **TR-TL** (보정 루프) | 범위 판정(N3.8.2), **Δ_T 입력 경로 배선(D-24 안 B)**: 구동기 → 다음 변형 제약 입력 → 제약 행 문턱(만들면 배선. spec 측정 선언 절은 만들지 않음 -- 상위 O-178), Δ_T 지문 대조(fail-closed, 주체 = 구동기, 원문 항목 처리는 D-25), 문턱 합성(엔진 쪽 제약 행), **오라클 V_id*(T) 측정**(matching, F-20a -- 측정 정의는 OP-5 `.dc` = PC-10, O-53 B3. 구동기가 오라클에 넘기는 입력(코드 벡터·표본별 코드·온도)은 EO-1 생산자 호출로 내고 확장 칸은 G-18 + U-6 규칙이다(감사 B4). 판정은 O-34 네 다리(SPICE 다리 = 상위 O-178 oracle 판정)(감사 B5). 소유 경계: T_j 한 조건의 matching 오라클 측정과 `verified_by`는 offset-strategy OS-V 소유이고, TR-TL은 그 측정을 판정 온도 범위의 온도 점으로 넓히는 몫만 맡는다), 불합격 몫 분해 정지(N3.8.4), 구동기(엔진 밖, 순차 실행)와 멈춤 규칙(N3.8.5), 기록(N3.8.6), 능력 기록 의존 거부(N3.9), 실행 계획 '실행 중 변형 추가' 연결((v0.7) offset-strategy card OS-L은 TR-B와 같은 변경에서 이미 병합 -- TR-TL은 Δ_T 추가 종류를 쓰는 둘째 소비자, 대상 = 국면 2 합성 회로 변형 C 또는 C′). matching 쪽 적용은 offset-strategy OS-2 병합과 matching 유도 제약의 `verified_by`가 생긴 뒤 | **TR-7 뒤**(T-30), oracle-portability 승인·능력 기록, OS-2·**OS-V**(matching 쪽, S-11). 실행 중 변형 추가 인터페이스(OS-L)는 (v0.7) TR-B 병합으로 선행 | D-18~D-20, D-22, D-24, D-25, O-1, O-3~O-8, G-9~G-15 |

**완료 조건**(기능 전체):
1. **trim 선언이 없는 실행**((v0.7) trim 파일·승인 기록이 없는 실행 포함; 변경 종류: 이 기능 규칙이 발동하지 않는 입력 = 순수 리팩터링, O-34 (1) -- headroom-chain O-35와 같은 규칙, 감사 E1): library 13회로 결과가 base와 필드별로 같다(이산 정확, 연속은 선언 분해능 이내). 결정성(같은 코드·환경·입력 두 번 실행 비트 동일)은 항상 검사한다. 범위는 D-14다. 기본안은 structure.json 2개를 새 `rule_hash`로 재승인한 뒤에 잰다. 그 두 회로 결과 가운데 `rule_hash` 값 자체를 담는 필드는 비교에서 뺀다.
2. 선언 회로에서 trim 제약·metric이 `verified_by`를 가진다.
3. SPICE 오라클 코드 스윕 판정을 통과한다. 내용은 Monte-Carlo 표본마다 잔여 ≤ V_res인 코드가 있는 비율이다. 판정 규칙과 합격선은 TR-0에서 독립 검증자가 정하고 소유한다. 변경 종류 = 동작 변경(O-34 (1))이고 네 다리(정의 손계산 오라클 toy, 봉인 불변식 -- KVL·KCL·영역과 intended_region 대조, SPICE oracle 판정 -- 정의 관문 + 닫힌 점, 수치 차 = 대조 기록(상위 O-178), 검증자 변화표 -- 원인 미설명 0)로 판정한다(감사 B5).
4. 모든 새 함수가 진입점에서 호출된다(배선 증거).
5. 상위 N6.3의 graph 단일 정본·재계산 계수·파일 분할 확인과 design 대 구현 gap 분석을 통과한다.
6. **(v0.5) 오라클 능력 의존**: 능력 기록이 없거나 낡은 (PDK, 시뮬레이터) 조합에서 범위 판정·루프를 요청하면 실제로 거부된다(거부 test가 먼저). 결과에는 '범위 미판정'이 적힌다. 능력 확인 절차 자체의 완료 조건은 oracle-portability 계획이 정한다.
7. **(v0.5, TR-TL)** 보정 루프:
   * 시험 회로(T-24)에서 범위 판정이 돌고, 루프가 N3.8.5의 정지 사유 가운데 하나로 끝나며, 사유 코드와 반복 이력이 결과에 있다.
   * Δ_T 지문의 대조 항목(D-25로 정한 범위)을 하나씩 바꾼 픽스처마다 엔진 밖 구동기가 거부한다(fail-closed). 그 Δ_T는 엔진에 들어가지 않는다(엔진 입력 0).
   * Δ_T가 구동기 → 변형 제약 입력 → 제약 행 문턱 한 경로로 실제로 이어진다(호출 grep + 실행 경로 test). Δ_T 하나를 바꾸면 해당 제약 행 문턱만 바뀐다. 다른 경로(spec 측정 선언 절, 오라클 결과 파일 직접 읽기)로 Δ_T가 들어가는 길은 0이다.
   * Δ_T가 없는 실행: 변경 종류 = 순수 리팩터링(발동하지 않는 입력) -- v0.5 전과 필드별로 같고, 결정성 비트 동일은 항상 검사한다(완료 조건 1과 같은 규칙, O-34 (1), 감사 E1).
   * 엔진이 이전 결과 JSON·S3·front 점을 읽지 않는다(읽기 경로 0, 시작점 주입 0). 변형 사이에 문턱 의존 블록(G-12 목록) 밖의 블록은 재계산이 0이다.
   * matching 범위 판정이 온도 점마다 오라클 V_id*(T)(PC-10 = OP-5 `.dc`)를 쓴다(흔들림만의 MC 값·공칭 MC 표본 offset으로 대신하지 않음).
   * (ii) 지배 픽스처에서 재실행 없이 정지한다(엔진 실행 수 = 1).
   * 반복 상한 선언이 없으면 루프를 시작하지 않는다.
   * 비용 표가 오라클 실행 전에 나오고, 엔진과 오라클이 동시에 돌지 않는다(실행 시각 기록).
   * 범위 판정 규칙·합격선은 독립 검증자가 소유한다.
8. **(v0.6, O-53 B1 -- 상위 O-202·O-212 개정)** 코드 상태별 intended_region: triode 선언이 실제와 다른 픽스처에서 엔진이 거부하고, VGS < 0 off 소자가 있는 평가점과 `judged_by` 칸 없음·그 metric `verified_by` 없음 픽스처에서 E-0 정지한다(거부 test가 먼저, 우회 0; 옛 'off 선언 소자가 전도하는 픽스처 거부'는 대상 소멸). off 선언 소자가 LUT·gm/ID 경로 호출에 나타나지 않는다(호출 계수).
9. **(v0.6, O-53 A3)** 엔진 안 고정 기하 DC 균형 풀이가 0이다(`git grep` -- grep 정의(상위 사용자 결정 O-176 Ⅳ, O-32 원문 범위): 보정 구간 끝·끝 코드 포화 같은 대신호 양을 정확히 내려는 고정 기하 균형(Newton) 풀이 경로 0; 봉인 정의를 실현 입력 W′에 다시 적용하는 E-0 재봉인 경로는 대상 밖). 보정 구간 끝과 끝 코드 포화는 봉인점 1차 감도 추정 경로 하나로 계산되고, 정확값 대조는 오라클 `.dc` 코드 스윕이다.
10. **(v0.7, O-258 (B)) 합성 로더**: 같은 입력 두 번 합성이 비트 동일하다. N3.3 스키마 검사 행마다 거부 픽스처가 실제로 거부한다(거부 test가 먼저 -- role 없음, base 지문 불일치, 이름 충돌, 원본에 없는 넷, 연결 안 된 포트, 코드 표 모순, 승인 기록 지문 불일치 `trim_approval_stale`). 합성 회로를 만드는 자리가 엔진에 하나다(`git grep` -- connectivity 표 도구도 그 블록을 부름). 엔진 코드에 `augment_trim`·trim 소자 생성 경로가 0이다. 원본 topology 파일·trim 파일 바이트가 실행 전후 같다.
11. **(v0.7) 소자 출처 칸**: writer가 합성 로더 하나이고(소유표), 소비자 ≥ 1(`trim_dac` 역할 유도·부담 변형 θ 소속)이다. 역할 유도가 이름·태그를 읽지 않는다(출처 칸만 READS -- 호출 grep).
12. **(v0.7, O-258 (A)) MC 시점**: 탐색 평가 점·닫기 전 점에서 사양 MC 요청이 거부된다. 사양 MC 표본 수가 r_σ에서 n = 1 + ⌈1/(2·r_σ²)⌉로 나오고 r_σ 미선언이면 거부된다. 엔진이 oracle MC 기록·trim 사양 기록을 읽는 경로가 0이다(σ_MC는 spec 칸으로만 들어옴).
13. **(v0.7) trim 부담**(변경 종류 = 동작 변경, O-34 (1) 네 다리): 정의 손계산 toy에서 부담 = max(0, s_μ·(v_C − v_O))와 예산 문턱이 맞게 통과·거부하고(거부 먼저), 변형 C의 원본 θ 성분이 θ_0와 비트 동일하며(고정 확인), C front가 빈 픽스처에서만 C′가 추가된다. 부담 문턱 항목이 구동기 → `derived` 한 경로로 들어간다(Δ_T와 같은 경로, 둘째 경로 0). 예산 미선언 metric에는 부담 제약 행이 0이다.
14. **(v0.7) 디지털 코드**: 엔진에 코드 탐색 경로가 0이다(엔진은 코드 상태 선언만 평가). oracle 잔여 MC가 표본마다 최적 코드를 고른 결과로 판정한다(완료 조건 3과 같은 판정).

### N5.1 TR-7 검증 항목(T-5, v0.5에서 T-29로 3번 승격)

**판정**(합격·불합격): 엔진 판정과 trim 코드 결정은 T_j·LUT 코너 한 조건이다(엔진 합격 조건, 상위 DEC-96 (3)). **v0.5**: offset·trim 잔여의 합격은 여기에 오라클 범위 판정(아래 3번, N3.8.2)을 더한 것이다(T-29). 범위 판정은 1·2번을 통과한 뒤에만 한다.

**순서**: 아래 1번(엔진 σ_in 대 SPICE σ_in 일치)을 TR-7에서 맨 먼저 확인한다. 이것이 맞지 않으면 나머지 Monte-Carlo 결과로 엔진 판정을 해석할 수 없다.

| # | 항목 | 성격 |
|---|---|---|
| 1 | 엔진 `offset_in_sigma_mv`(합성 회로, DAC mismatch 포함) 대 SPICE Monte-Carlo σ_in 일치(정의 동일성 관문 + 대조 기록 -- 상위 O-178; 국면 1 사양 MC의 σ_MC 대 엔진 σ_in 대조 기록도 같은 표에 싣는다) | 판정 전제(첫 확인) |
| 2 | 27 °C 잔여 분포: 샘플마다 trim 절차를 흉내 낸다(측정 → 코드 선택 → 잔여). 잔여 ≤ V_res 비율을 잰다 | 판정(완료 조건 (3)) |
| 3 | 고정 코드 온도 sweep: 샘플마다 T_j에서 고른 코드를 고정하고, 판정 온도 범위의 온도 점에서 잔여 offset을 잰다. 표본은 2번과 같은 표본(정체 보존, N3.9-3)이다 | **판정(v0.5, T-29, N3.8.2)**. 분해표(design §3.8)를 함께 낸다 |
| 4 | 코너별 보정 구간: 공정 코너마다 오라클 `.dc` 코드 스윕으로 끝 코드 구간 [V_in(−end), V_in(+end)]를 잰다(엔진 1차 감도 추정과의 차는 대조 기록, O-53 A3) | 보고 전용 |
| 5 | 끝 코드 headroom의 온도 의존: 3번과 같은 온도 점(판정 온도 범위 spec 선언 참조, T-34)에서 끝 코드 포화 여유를 잰다 | 보고 전용 |

**한계**(보고서에 적는다):
* 샘플 수는 k 꼬리를 확인할 수 있는 규모여야 한다. k가 클수록 필요한 샘플이 늘어나는 비용 한계가 있다. 샘플 수 규칙은 TR-0에서 독립 검증자가 정한다.
* 몬테카를로는 샘플마다 trim 절차(측정 → 코드 선택 → 잔여)를 흉내 내야 한다. 코드를 하나로 고정한 일반 MC는 trim 뒤 분포를 재지 못한다.
* 패키징 응력, 장기 drift, trim 측정 잡음은 DC 몬테카를로의 범위 밖이다(Zhou 2017 p.1: 패키지 뒤 trim이 응력 이동을 피하는 이유; Kay 2024 §1.2 p.7: CMOS drift는 offset과 비례하지 않음).
* 온도 drift는 DAC 바이어스 원천(D-9)에 직접 의존한다. t(T)와 δ(T)가 온도에 따라 함께 변하고, 그 변화의 방향과 크기는 바이어스 원천이 어떤 온도 특성의 전류를 주는지로 정해진다(G-8).

---

## N6. 검증 원칙

* 판정자는 SPICE 오라클(`tools/spice_oracle/`, 엔진 import 금지)이다. trim은 코드 스윕과 Monte-Carlo가 필요하다. 오라클 확장(코드 입력, 표본별 최적 코드 선택, LUT와 따로 받는 온도 입력, **온도 점별 계통 offset V_id*(T) 측정**(F-20a -- 정의는 OP-5 `.dc` = PC-10, O-53 B3), 같은 seed 네이티브 MC 표본을 온도마다 다시 재기, (v0.7) 사양 MC의 표본 수 입력 = r_σ(N3.10)·합성 회로 입력(소자 출처 무관 -- 같은 회로 IR))은 레인 P 작업이다(오라클 MC 구현은 oracle-portability v0.4 O-1).
* **(v0.5)** 오라클의 MC·온도 판정은 유효한 오라클 능력 기록(N3.9, oracle-portability 계획 소유)이 있을 때만 판정으로 센다.
* **(v0.6, 감사 B4) 오라클 입력 생산자 하나**: TR-7·TR-TL이 오라클에 넘기는 입력(봉인점, 코드 벡터, 표본별 코드, 온도, intended_region)은 gain-budget EO-1 생산자 하나가 낸다. 확장 칸의 정본은 oracle-portability G-18 스키마이고, 그 칸을 쓰는 card의 통합 병합에 EO-1 생산자 갱신 커밋(Role: code)을 넣는다(oracle U-6 규칙). 이 계획의 구동기가 오라클 입력을 따로 조립하는 자리는 0이다.
* **(v0.6, 감사 B5) 판정 다리**: TR-7·TR-TL 판정은 gain-budget N6.3 동작 변경 기준의 네 다리(정의 손계산 오라클 toy, 봉인 불변식, SPICE oracle 대조, 검증자 변화표)로 한다(SPICE 다리 = 상위 O-178 oracle 판정: 정의 관문 + 닫힌 점; 엔진 대 SPICE 차 = 대조 기록, oracle 미배선이면 N6.3 (i) 보류). 보류 다리를 통과로 세지 않는다.
* **(v0.5.1)** 오라클은 언제나 별도 프로세스이고 엔진을 import하지 않는다. 보정 루프 구동기의 구조는 D-24 안 B(T-35 확정)다. 아래 안 A 항목은 기각된 대안의 기록이다.
  * 안 A: 엔진도 별도 프로세스로 부르고 결과 JSON과 spec 파일만 주고받는다.
  * 안 B: 구동기가 엔진 실행 계획을 같은 프로세스에서 유지하고, 오라클만 별도 프로세스로 부른다.
* 엔진 쪽 test는 interface card만 보고 쓴다. 기대값은 피검 함수를 불러 만들지 않는다.
* 일반성: library 13회로 전수에서 사유 코드를 측정해 보고한다.

---

## N7. 열린 항목

### N7.1 사용자 결정 (전부 승인·닫힘 -- 기록용)

(v0.6.2 백로그 재감사 OT-B1·B2) D-1~D-17은 계획 v0.4 승인 T-6으로 기본안 전부 승인됐다(D-16은 T-7로 변경 -- 행 안 표기, design `offset-trim.design.md` 55행). D-18~D-25는 행마다 닫혔다(T-34·T-35·T-36). 옛 표제·머리 문장은 history.

**(v0.7, 사용자 결정 O-258 (B)) 대상이 바뀐 행**(행 원문은 기록으로 두고 여기서 읽는 뜻을 정한다): D-9(바이어스 원천)·D-10(스위치·코드 표현)은 엔진 기본안이 아니라 **trim 파일 선언 칸**의 뜻이다(AI 제안·사용자 승인 -- 트랜지스터 스위치·전용 게이트 넷·on/off 레벨 = 레일 역할 참조는 그대로). D-13(결속)은 '파생 지문' 대신 trim 파일 sha256·합성 회로 지문으로 읽는다(N3.3). D-15(선택의 위치 `trim_decl`)는 대상 소멸(선택은 trim 파일 선언). D-17(봉인 코드 δ = +I_u)은 trim 파일 코드 상태 선언의 봉인 역할로 읽는다. D-16은 이미 T-7(I_u = θ)로 바뀌었다. 바뀐 결정 목록은 N7.2 'v0.7' 표.

| ID | 질문 | 기본안 |
|---|---|---|
| D-1 | V_res의 뜻: 잔여 offset의 최악 한계인가, 잔여 분포의 1σ인가 | 최악 한계(N3.4 잔여 판정 Δ_max/2 ≤ V_res) |
| D-2 | 수율 표현: k만 받을지, 수율 목표 Y도 받아 k로 환산할지. 환산에는 정규·양측 가정이 필요하다 | k만 받는다(분포 가정을 엔진에 넣지 않음). T-1을 좁히는 안이다(X-8) |
| D-3 | 잔여 판정 안 양의 DNL 상한 배수로 spec k를 그대로 쓸지(k·σ_DNL(m)). 한계: k는 offset 분포 한쪽 꼬리의 배수다. 양의 DNL 상한은 최악 전이 여러 개(thermometer 경계마다)에 동시에 걸리므로, 같은 k로는 '모든 전이 만족' 확률이 offset 수율과 같지 않다(전이 수만큼 낮다) | spec k를 그대로 쓰고 이 한계를 보고에 적는다. 따로 선언하는 안은 사용자 선택이다 |
| D-4 | 같은 spec에 기존 offset 제약(`offset_in_sigma_mv <=`, `offset_excess`, `offset_sys_mv` 상한)과 trim 선언이 함께 있을 때의 처리 | 로더가 `offset_in_sigma_mv <=`와 trim 선언의 공존을 거부한다(spec 수정은 사용자 몫). `offset_excess`와 `offset_sys_mv` 상한은 보고로 내린다 |
| D-5 | 후보 순위 키에 DAC 잡음 영향을 넣을지 | 넣지 않고 값만 보고한다 |
| D-6 | front 위에서 t의 부호나 크기가 크게 바뀌는 쌍의 처리 | 표시하고 거르지 않는다 |
| D-7 | 상보 입력쌍 회로에서 DAC를 쌍마다 둘지, 하나만 둘지 | 쌍마다 하나씩 둔다(제안 '상보 입력쌍은 trim 각각'). 판정이 입력 DC 한 점이라는 한계를 보고한다 |
| D-8 | 단일 입력 회로 지원 | 이번 범위에서는 정지한다(X-11) |
| D-9 | 단위 셀 게이트 바이어스 원천: 기존 바이어스 넷 미러인가, 새 `bias_inputs` 항목인가. 이 선택은 온도 drift에 직접 영향을 준다(t(T)·δ(T), N5.1·G-8). 27 °C 판정에는 드러나지 않고 TR-7 온도 sweep에서만 보인다 | 새 `bias_inputs` 항목. 기존 바이어스 기둥과 L 동치류를 바꾸지 않는다 |
| D-10 | steering 스위치 표현과 코드 표현: 트랜지스터 + 전용 게이트 넷 + `trim_decl` DC 값 벡터인가, 이상 스위치 + 선언 VDS 예산인가 | 트랜지스터. 스위치마다 전용 게이트 넷을 두고, 코드는 `trim_decl`의 DC 값 벡터(connectivity 지문 밖, 승인 결속은 `trim_decl` 해시)로 표현한다. on/off 레벨은 회로 레일 전압(`supply_nets`)이다 |
| D-11 | trim 선언을 넣을 회로와 V_res·k·온도 값 | 사용자 몫이다. 엔진 검증용은 `origin: fixture` 픽스처 spec으로 따로 둔다 |
| D-12 | trim 온도와 상위 DEC-96 (3) '합격 = TT 27 °C 한 조건'의 관계 | trim 온도 = 합격 조건 온도로 제한하고, 다르면 거부한다(X-1). **v0.5**: 엔진 쪽 규칙은 그대로다(trim 온도 = T_j). offset·trim 잔여의 합격은 T-29로 오라클 범위 판정이 더해졌다 |
| D-13 | 파생 topology 결속 방식(N3.3): spec·structure.json은 원본 지문에 묶고, 파생 지문은 승인 기록에만 묶는 안. 대안은 파생 topology용 spec·structure.json을 따로 두는 것이다 | 원본 결속 + 파생 대 원본 구조 동일 검사 + 승인 기록 fail-closed. 근거: 사용자 값(spec)과 회로 해석 승인(structure)을 한 곳에만 두고(단일 정본), 파생 회로만 따로 승인한다 |
| D-14 | 완료 조건 (1) '비트 동일'의 범위. TR-4의 규칙 파일 변경으로 `rule_hash`가 바뀌면 structure.json이 있는 두 회로는 재승인 전까지 결과가 달라진다 | trim 선언이 없는 실행만 대상이다. 기본안은 두 structure.json을 새 `rule_hash`로 재승인(사실 내용 동일)한 뒤 잰다. 비교에서 빼는 것은 '규칙 지문을 담는 모든 필드'다. `rule_hash`, S1 지문 `S1Key.rule_fp`(`E/graph/s1_values.py:5, :233-237`), 그것을 입력 버전으로 품은 필드 지문이 포함된다. 정확한 목록은 G-3이다 |
| D-15 | 선택(쌍·극성·N·m)의 위치: `trim_decl` 안(로더가 spec + 승인 기록을 합성)인가, 별도 인자 `selection`인가 | `trim_decl` 안. T-2 서명 `augment_trim(topology, trim_decl)`을 지킨다(X-9) |
| D-16 | 2단계 I_u를 하한(보정 구간 경계, 전력 최소)으로 둘지, 상한(잔여 경계)으로 둘지, θ로 둘지 | 하한. 상위 NFR-5와 전력 목적 축 때문이다(X-3) **→ 사용자 결정 T-7(2026-10-15 "TD-1은 θ안")로 변경: I_u는 θ 변수, 범위·잔여는 I_u 제약, 전력 최소화가 하한으로(design `offset-trim.design.md` §10.3, X-T14)** |
| D-17 | 정상 동작점으로 쓸 중간 코드: δ = +I_u인가, −I_u인가, 둘 다인가 | +I_u 하나로 봉인하고, −I_u는 끝 코드와 함께 포화 검사만 한다 |

**v0.5 사용자 결정**(T-29~T-32 보완 -- D-18~D-25 행마다 닫힘(T-34·T-35·T-36), 기록용; v0.6.2 백로그 재감사 OT-B2):

| ID | 질문 | 권고 |
|---|---|---|
| D-18 | **판정 온도 범위의 값과 위치** | **닫힘(사용자 결정 T-34)**: 값은 T-14에서 정한 범위다. spec에 한 번만 선언한다. 칸은 offset 요구 안에 두고, 스키마 정본은 offset-strategy N3.2다. TR-7 온도 보고 sweep과 보정 루프 범위 판정이 모두 그 선언을 참조한다(숫자 사본 금지) |
| D-19 | **보정 루프 반복 상한의 값과 위치** | 위치는 루프 도구의 실행 설정이다(회로 성질이 아니라 실행 제어라서 spec이 아님). 출처를 기록하는 사용자 선언값이고 기본값은 없다. 선언이 없으면 루프를 돌지 않고 첫 범위 판정만 보고한다. **닫힘(사용자 결정 T-35, 권고대로)** |
| D-20 | **오라클 판정 대상 점의 선택 규칙**. front 전부를 범위 판정하면 비용이 front 크기에 비례한다 | 사용자가 결정적 선택 규칙 하나를 선언한다(예: front 위 목적 축 하나의 최소 점). 반복마다 같은 규칙으로 고른다. 규칙이 없으면 범위 판정을 하지 않는다. front 전수 판정은 비용 표를 보고 사용자가 고를 수 있는 선택지로 남긴다. **닫힘(T-36, 권고 (가))**: 사용자 선언 결정적 규칙으로 front 점 하나를 고른다. 규칙 값은 시험 회로 실행 때 선언할 수 있다 |
| D-22 | **(ii) 지배로 정지한 뒤의 다음 행동**. DAC 바이어스 원천(D-9 '새 `bias_inputs` 항목', design §3.8 '오라클에서 T_j 봉인 전압의 이상 전압원')의 온도 특성을 바꿀 것인가 | 이번 범위에서는 정지·보고까지만 한다. 바이어스 원천 변경(온도 특성이 있는 기준 사용 등)은 회로 해석이므로 공동분석 뒤 별도 결정으로 둔다. **닫힘(T-35, 권고대로)** |
| D-24 | **보정 루프 반복 구조**(X-26, N3.8.7 표). 안 A = 반복마다 별도 엔진 실행(단계 A·S0·블록 결과를 반복마다 다시 계산). 안 B = 반복을 offset-strategy 실행 계획 안의 변형(같은 topology + 문턱만 다른 제약 집합)으로 두고, 구동기가 같은 프로세스에서 실행 계획을 유지한 채 오라클(별도 프로세스)을 부른 뒤 다음 변형을 추가한다 | **안 B -- 닫힘(T-35)**. 원래 취지("처음 topology를 실행할 때 계산하고 그 값을 나머지 최적화에서 재사용")와 gm/ID 빠른 설계 취지에 맞다. 대가는 실행 계획에 '실행 중 변형 추가' 인터페이스가 필요하다는 것이다(offset-strategy 계획 연결 항목: 지금 `build_run_plan`은 실행 전 고정 목록). 메모리 순차(NFR-T9)와 맞는다 |
| D-25 | **Δ_T 출처 지문의 원문 항목(점·표본 수·오라클 실행) 처리**(X-22). (a) 다음 실행과 모두 대조: 루프 불성립 (b) 기록만(v0.5의 O-2) (c) 출처 무결성: Δ_T 선언이 인용한 오라클 결과 기록(점·n·시드·실행 id가 담긴 판정 기록)이 있고, 그 내용과 선언이 일치하는지 대조한다. 원문 항목 모두가 무효 조건으로 남고, 루프도 성립한다.<br>**(c)의 대조 주체**(v0.5.2):<br>(c-1) 엔진 로더가 대조한다. 그러면 엔진이 오라클 결과 파일을 읽는 새 입력 경로가 생긴다(S-3·X-23 경계를 넘음).<br>(c-2) 엔진 밖 구동기가 대조하고, 엔진에는 대조를 통과한 값만 넣는다 | **(c)와 (c-2)**. T-30 원문 '지문 불일치 무효'를 모든 항목에 지키면서 루프를 막지 않는다. 엔진 입력 경로도 늘리지 않는다. **닫힘(T-36)**: (c) 출처 무결성 + (c-2) 엔진 밖 구동기가 대조한다 |

### N7.3 TR-0 design에서 반드시 닫을 항목

사용자 결정이 아니라 design 작성·검증에서 근거와 함께 닫아야 하는 기술 항목이다. 닫히지 않으면 해당 card를 시작하지 않는다.

| ID | 항목 | 관련 card |
|---|---|---|
| G-1 | **해소(사용자 결정 O-53 B1)**: 전류 0 MOS는 (v0.7, X-36) 합성 로더가 trim 파일 코드 입력·코드 상태 선언에서 코드 상태마다 intended_region `off`로 선언하고(옛 '`augment_trim`이'), 그 소자는 사이징·역산 경로(LUT·gm/ID)와 포화 요구에서 빠지고, 효과는 0 모형 + 1차 ΔV·O-h·VGS < 0 점 정지다(상위 O-202·O-212, N3.5 -- 옛 '꺼짐 판정은 LUT I_off·선언 대조 거부' 대체). 옛 질문 문장은 history H1 2026-10-20 | TR-3·TR-5 |
| G-2 | 파생 대 원본 구조 동일 검사(N3.3-2 -- v0.7: 합성 회로에서 출처 칸이 trim인 소자를 뺀 것 대 원본)의 비교 필드 범위. 주입 넷이 가지 끝 넷이 되면 원본 소자에 대해서도 `_sibling_rule`·`_counterparts`·column 규칙(matching group, 대응 넷) 결과가 달라질 위험이 있다. 비교 필드를 정의하고, TR-2·TR-4 전에 library 13회로에서 그 차이를 측정하는 단계를 둔다 | TR-2·TR-4 |
| G-3 | D-14 비교 제외 필드 목록: 규칙 지문을 담는 모든 필드(`rule_hash`, `S1Key.rule_fp` `E/graph/s1_values.py:5, :233-237`, 그것을 입력 버전으로 품은 필드 지문) | TR-4·완료 조건 (1) |
| G-4 | **(v0.7 대상 소멸, O-258)** 옛: 1단계 N 추천의 입력점과 N·m을 정하는 순서. N·m은 trim 파일 선언이고 N_min은 trim 사양 기록(σ_MC, N3.10)이 낸다 | -- |
| G-5 | σ_U의 기준: (v0.7) 엔진 추천이 없어져 국면 1 쪽 질문(1단계 추천에서 어느 θ의 σ_U를 쓰는가)은 AI 제안의 근거 기준이 된다(엔진 판정 아님). 국면 2 판정에서는 봉인 점의 θ 값이고, thermometer 셀은 단위 셀 2^m개 복제(독립)로 본다 | TR-5 |
| G-6 | **닫힘(사용자 결정 O-53 B3)**: 출력 기준의 정의 자리는 gain-budget DEC-23 하나다(spec 선언 기준 종류 셋 -- 값·넷·입력 추종 -- 과 차동 출력 기본 V(p) − V(n) = 0, 선언 없는 단일 출력은 정의 불능). 엔진 균형 풀이는 지웠으므로(O-53 A3) 이 계획의 '출력 기준값'은 DEC-23 기준값을 뜻한다. 옛 문장(`offset_systematic` 인용)은 history H1 2026-10-20 | TR-5 |
| G-7 | **(v0.7 닫힘, O-258 (B))** 코드 상태는 trim 파일의 코드 상태 선언이고 승인 결속은 trim 파일 sha256이다(옛 질문: DC 값 벡터를 승인 해시에 넣을지 규칙으로 유도할지) | -- |
| G-8 | 바이어스 원천(D-9)별로 t(T)·δ(T)의 온도 의존을 TR-7 온도 sweep(N5.1 3번)에 어떻게 보고할지 | TR-7 |

**v0.7 TR-0(design 개정)에서 닫을 항목**(O-258 -- 번호는 oracle-portability G-16~G-18과 겹치지 않게 G-21부터):

| ID | 항목 | 관련 card |
|---|---|---|
| G-21 | trim 파일 스키마의 칸 이름·형식(N3.3 표), 코드 상태 선언의 δ 셈 정의, 의도 문서 위치와 지문 규칙(상위 DEC-110 AI 산출물 규약 인용), 승인 기록 형식 | TR-3 |
| G-22 | 합성 로더 블록의 이름·층 자리(단계 A 전 topology 로드 자리), 소자 출처 칸의 필드 이름·형식, 합성 회로 connectivity 표 도구가 그 블록을 부르는 자리 | TR-3·TR-4 |
| G-23 | 부담 metric 집합(spec 판정 제약이 있는 metric 전부인가, 이름 목록 없음 -- 규칙으로), 방향 s_μ 표, 부담 예산 칸 형식, 부담 문턱 항목의 `derived` 형식(offset-strategy N3.12 소유 형식 안), 변형 C 목적 축의 metric 이름(DEC-68) | TR-B |
| G-24 | θ 성분 소속 판정(출처 칸 READS -- 원본·trim·섞임), 섞인 성분의 목록 보고 형식, 고정 θ 성분을 변형에 싣는 형식(offset-strategy XS-21) | TR-B |

**v0.5 TR-0T(design 보완)에서 닫을 항목**:

| ID | 항목 | 관련 card |
|---|---|---|
| G-9 | Δ_T의 metric별 정확한 식, 그 분해능(멈춤 규칙의 측정 분해능. matching σ 항 = MC 표준오차, trim 잔여 = DC 풀이 허용오차 전파, T-39) 식, 문턱 합성의 표현(spec 문턱 참조와 Δ_T 변형 제약 입력을 함께 읽는 제약 행 형식, 상위 DEC-68 이름) | TR-TL |
| G-10 | matching 제약 범위 판정의 표본 수 규칙. 식 S(design §17)는 LSB_in을 쓰므로 matching에는 정의되지 않는다. spec·엔진 값에서만 유도하고 새 상수를 쓰지 않는다 | TR-TL |
| G-11 | 온도 점 규칙: 끝점 + T_j(design §17-3)로 충분한가. 범위 안 비단조 위험을 어떤 측정으로 드러낼지(상수 간격 금지) | TR-7·TR-TL |
| G-12 | 구동기의 위치와 구조(D-24 안에 따라: 안 A는 `tools/` 아래 엔진·오라클 모두 import 금지, 안 B는 엔진 실행 계획 인터페이스와 변형 추가 서명. 어느 안이든 오라클 import 금지), 서명, 정지 사유 코드 이름(O-7 원인별 포함), 반복 이력 형식, 실행 설정(반복 상한·시뮬레이터 병렬 수) 칸. **안 B의 '문턱에 의존하는 블록' 목록**: 제약 문턱을 입력(extras·입력 버전)으로 읽는 블록을 블록 레지스트리에서 전수로 뽑는다. 후보 예는 제약 행 계산, `iv_matching_l` L 하한, 출발 구간, 탐색 정의역 중 제약에서 온 것이다. 목록 밖 블록의 변형 사이 재계산 0을 완료 조건 7에서 잰다. **(v0.6, 감사 C2)** 목록에 층 0 조립 블록(gain-budget N6.14 LA-1 역산 조립) 가운데 문턱(Δ_T로 조인 `offset_in_max_v` 등)을 입력으로 읽는 것을 넣는다(offset-strategy v0.7 `plan/offset-strategy-v07` `5f99a49a` 후속 정정 (1)과 같음). L 하한의 정본은 gain-budget **LR6**(`plan/gb-v620` `f2579b2f` -- offset 요구 커널 판정 포함, LA-1 역산 L에 LR6 경계)이고, offset-strategy design G-S2(`iv_matching_l` L 하한)와 LA-1 역산 조립 출발 규칙은 LR6을 읽는 자리다. design은 읽는 자리만 정한다(사본 금지, 감사 4차 B-2) | TR-TL |
| G-13 | Δ_T 출처 지문의 정확한 필드 목록, 원문 항목 처리(D-25), spec 지문에서 Δ_T 칸을 빼는 규칙, 지문 불일치 사유 코드 | TR-TL |
| G-14 | **결정적 끝 표본의 범위 판정**(v0.5.1): design §17-2의 '소자 공칭 + 입력 직렬 이상 전압 ±k·σ_eng'는 이상 전압원 온도 계수가 0이라 꼬리의 원본 offset drift (i)을 과소 추정한다(거짓 합격 위험). **닫힘(사용자 결정 T-35, oracle-portability v0.4 O-1과의 충돌 X-16 해소)**:
* 꼬리는 네이티브 MC 표본 안에서 판정한다. 같은 seed 표본을 온도마다 다시 재고, 꼬리 쪽 실제 표본으로 범위 판정한다.
* 결정적 끝 표본은 범위 판정·Δ_T에서 빼고 진단만 한다. 결정적 불일치 벡터 대안과 그 오라클 요구(PC-11)는 철회했다.
* design §17 개정(T_j 판정에서 끝 표본 역할 포함)은 TR-0T가 한다 | TR-0T·TR-7·TR-TL |
| G-15 | **닫힘(사용자 결정 O-53 B3)**: matching V_id*(T)의 출력 기준은 DEC-23 정의 하나를 온도 점마다 그 온도의 해에서 쓴다(선언 기준 종류가 값이면 선언 전압, 넷이면 그 넷, 입력 추종이면 입력 CM). 오라클 측정 = OP-5 `offset_sys_mv` `.dc`를 온도 조건에서 돌린 것(PC-10). 공칭 MC 표본 offset은 V_id* 출처가 아니다. 옛 질문 문장은 history H1 2026-10-20 | TR-TL |

### N7.2 원래 취지와 다름(따로 보고)

| ID | 내용 |
|---|---|
| X-1 | T-1의 'trim 온도 조건' 필드는 두지만, 엔진 합격 조건이 TT 27 °C 하나라서 다른 온도는 평가할 수 없다. D-12 기본안은 사실상 27 °C 고정이다. 다른 온도를 지원하려면 LUT 온도 축이나 오라클 온도 옵션이라는 별도 범위가 필요하다. **v0.5**: 사용자가 오라클 온도 쪽을 골랐다(T-29). 엔진 trim 온도는 여전히 T_j 하나다 |
| X-3 | 제안은 θ 후보로 'I_LSB 또는 I_T·단위 gm/ID·L'을 들었다. 기본안은 I_u(따라서 I_LSB·I_T)를 θ에서 빼고 경계에서 유도한다(D-16) |
| X-4 | **(v0.6 대체 -- X-29, O-53 A3)** 옛 내용: 제안의 '코드 양 끝 DC 동작점 검사'를 '출력 균형 입력 전압을 함께 푼 해'로 구체화했다. 꺼진 셀은 포화 검사에서 뺀다. v0.6: 끝 코드 검사는 봉인점 1차 감도 추정이고 정확값은 오라클 `.dc` 코드 스윕이며, 꺼진 소자는 intended_region `off` 선언(O-53 B1)으로 다룬다(N3.5) |
| X-5 | 제안의 'iv_matching_l 완화'는 판정을 바꾸지 않는다. `iv_matching_l`은 출발값 전용(F-4)이고, 의미 전환의 실체는 spec 제약 처리(D-4)다 |
| X-6 | 제안의 'drift·1/f는 유지'에서, 엔진에는 drift metric이 없다(F-6). '유지'는 '보정 대상 아님 + 보고 문구'로만 구현한다 |
| X-7 | 제안의 t_n = z[n]/A_dm(노드 하나)은 차동 steering에서 쌍의 차 t = (z[n_p] − z[n_n])/(2·A_dc)로 바뀐다(v0.6: 환산 이득 A_dc, DEC-23 인용). z 벡터 노출이라는 엔진 변경이 필요하다(F-2) |
| X-8 | D-2 기본안(k만)은 T-1 'k(또는 수율 목표)'를 좁힌다 |
| X-9 | 검증 지적: v0.1의 서명 `augment_trim(topology, trim_decl, selection)`은 T-2 서명 `(topology, trim_decl)`과 달랐다. v0.2 기본안(D-15)은 selection을 `trim_decl` 안에 넣어 T-2 서명으로 돌아왔다. 다만 `trim_decl`이 spec 값만이 아니라 승인 선택까지 담는다는 점은 T-2 원문에 없는 해석이다 |
| X-10 | 승인 대상: T-2는 '파생 topology 승인'이다. v0.1은 후보 노드를 승인하는 흐름이라 사용자가 파생 topology를 보지 않았다. v0.2는 1단계가 파생 topology와 connectivity 표를 내고 사용자가 그것을 승인한다(FR-T2·FR-T4). 원문과 일치시켰고, 기록을 위해 남긴다 |
| X-11 | D-8 기본안('단일 입력 회로는 범위 밖 정지')은 제안 '단일 입력 회로는 spec에 offset 항목이 있을 때만'을 좁힌다. 제안은 offset 항목이 있으면 단일 입력도 대상으로 본다 |
| X-12 | 제안의 LSB 식 I_LSB ≤ V_res/\|t\|와 'DNL < LSB/2'를 잔여 판정 하나 Δ_max/2 ≤ V_res(Δ_max = \|t\|·I_LSB·(1 + k·σ_DNL(m)))로 바꿨다. 최적 코드 잔여 상한의 정확한 표현이고, 양의 DNL만 잔여를 넓힌다는 근거(Staudt §III)를 따른다. 제안의 'DNL < LSB/2'는 별도 제약으로 두지 않는다 |
| X-13 | 승인 기록 결속 실패는 정지(fail-closed)다. structure.json 선례(F-8: review_needed로 되돌리고 계속)와 다르다 |
| X-14 | **(v0.6: (b) '판정은 전회로 균형 풀이'는 X-29로 대체. (a)의 포함 조건 꼴은 유지하고 끝 전압은 봉인점 1차 감도 추정, 계통 offset은 V_id*)** 제안의 범위식 I_range ≥ k·σ_in/\|t\|를 다음 두 가지로 바꿨다. (a) 균형 풀이 끝 코드 전압으로 한 포함 판정 [−k·σ_in, +k·σ_in] ⊆ [V_in(−end), V_in(+end)]. 끝 코드 전압이 계통 offset을 이미 품고 있고, 선형 근사에서는 \|t\|·I_T ≥ k·σ_in + \|V_sys,s\|와 같다(v0.2의 [V_sys ± k·σ_in] 형태는 계통 offset을 두 번 센 오류여서 v0.3에서 고쳤다). (b) 판정은 전회로 균형 풀이이고 선형식은 유도용이다. 제안의 N = ⌈log2(2·I_range/I_LSB)⌉은 1단계 추천 식으로만 남고, 2단계 N은 승인 고정값이다(B3) |
| X-15 | FR-T1 '선언이 없으면 지금과 비트 동일'은 v0.1에서 무조건이었지만, v0.2부터 완료 조건 (1)의 범위(D-14: trim 선언 없는 실행, structure.json 재승인 뒤, 규칙 지문 필드 제외)로 좁혀졌다. 규칙 파일 변경(TR-4)이 지문을 바꾸기 때문이다 |
| X-16 | v0.2에서는 'k·σ_DNL ≤ 1/2'의 1/2(유도 안 된 상수)가 T-3 'DNL 부족'의 기준이었다. v0.3에서 DNL 별도 제약을 지우고, 'DNL 부족'을 잔여 창(I_u 하한 ≤ 상한)이 닫히는 것으로 유도해 **해소**했다 |

**v0.5 원래 취지와 다름**(사용자 결정 T-29~T-32 반영으로 생긴 것과 그 해석):

| ID | 내용 | 상태 |
|---|---|---|
| X-17 | **원래 결정과 다름(사용자 승인됨 2026-10-16, T-29)**: offset·trim 잔여의 합격을 'TT 27 °C 한 조건'(상위 DEC-96 (3), 이 계획 T-5·T-6)에서 '오라클 범위 판정'으로 바꾼다. T-5의 고정 코드 온도 sweep(N5.1 3번)은 보고 전용에서 trim 잔여의 판정으로 올라간다. 엔진 판정과 탐색은 한 조건 그대로다. **상위 계획 DEC-96 (3) 문언 개정은 이 커밋에 없다**(N7.4 후속; v0.6.2 백로그 재감사 OT-B4: 필요 -- 상위 v6.38.4에 예외 문장 반영 요청, 상위 DEC-96 grep 'T-29' ≥ 1 확인 뒤 닫음) | 승인됨 |
| X-18 | **원래 결정과 다름(사용자 승인됨 2026-10-16, T-29)**: FR-T9 '단일 온도 trim 한계' 문구가 '다른 온도에서 V_res를 넘을 수 있다(보고)'에서 '잔여 합격은 범위 판정이 정한다'로 바뀐다. trim이 drift를 보정하지 않는다는 사실(Kay 2024 p.7)은 그대로이고, 남는 drift는 크기 여유(Δ_T)로 흡수한다 | 승인됨 |
| X-19 | T-14는 '보고 전용' 범위로 정한 값이었다. 판정 범위로 쓰는 것은 사용자 결정 T-34로 확인됐다. 보고 sweep과 판정이 같은 spec 선언 하나를 참조한다 | **해소(T-34)** |
| X-20 | **해석**: T-30 '(ii) 지배'를 '(i)·(iii)을 0으로 두어도 불합격'(O-3)으로 정의했다. 결정 원문에는 '지배'의 판정식이 없다. 세 몫 가운데 (ii)가 가장 크다는 식(argmax)도 가능하지만, 그 식은 (ii)가 가장 커도 (i)·(iii)을 줄여 합격할 수 있는 경우를 정지시킨다. O-3은 '크기 조정으로 닫을 수 없음'을 직접 유도한다 | **확정(T-35, 권고 정의)** |
| X-21 | T-29·T-32의 'offset' = offset-strategy matching 유도 제약(O-53 A2 두 판정 -- 커널 k·σ_in ≤ 문턱, front k·σ_in + \|V_id*\| ≤ 문턱; 정본 offset-strategy v0.7 N3.3, 이 계획은 인용). 사용자 결정 S-9 'T-30 연결'로 정해졌다. 루프는 이 계획이, 문턱 연결점(`offset_in_max_v` − Δ_T)은 offset-strategy가 소유한다. matching 쪽 적용은 OS-2 병합 뒤다 | **결정됨(S-9)** |
| X-22 | **해석 대기**: T-30 '출처 지문(점·코드 해시·LUT·오라클 실행·표본 수), 지문 불일치 무효'의 원문 항목 처리에는 세 해석이 있다(D-25).<br>(a) 점·표본 수·오라클 실행까지 다음 실행과 대조한다. 루프는 점이 바뀌도록 문턱을 조이므로 Δ_T가 언제나 무효가 되어 루프가 성립하지 않는다.<br>(b) 원문 항목은 기록만 한다(v0.5의 O-2). 루프는 성립하지만 원문 '불일치 무효'가 그 항목들에는 적용되지 않는다.<br>(c) 출처 무결성: Δ_T 선언이 인용한 오라클 결과 기록과 대조한다. 원문 항목 모두가 무효 조건으로 남고 루프도 성립한다.<br>**(c) 채택(T-36)**. 대조 주체는 엔진 밖 구동기다(c-2) | **확정(T-36)** |
| X-23 | **취지 경계 확인**: S-3 '엔진은 이전 실행 결과를 입력으로 받지 않는다'와의 관계. Δ_T는 이전 변형의 설계 점에서 오라클이 잰 값이 다음 변형의 제약 입력으로 들어오는 것이다(D-24 안 B). 엔진 계산 결과·front 점·S3는 들어오지 않고, 엔진은 오라클 결과 파일도 읽지 않는다(대조는 구동기, D-25 (c-2) 권고). T-30이 '측정 선언'을 명시했으므로 취지 안으로 본다. **수용(T-37)**: 직전 변형 결과로 잰 Δ_T를 다음 변형 입력으로 넣는 것은 S-3 취지 안이다(offset-strategy XS-18). (→ 상위 사용자 결정 O-178 oracle 닫기와의 경계는 N3.8.7 '상위 oracle 닫기와의 관계' -- 상위 Q-W1과 함께 정함) | **수용(T-37)** |
| X-24 | `trim_range`(보정 구간)는 범위 판정하지 않고 T_j 판정 그대로 둔다(N3.8.1). T-29 원문은 'offset·trim 잔여'라서 보정 구간은 원문 범위 밖이고, 코드를 고르는 온도가 T_j 하나라는 정의에서 나온 결론이다 | 기록 |
| X-25 | T-31은 능력 확인을 '선행 card'로 이 계획 보완 안에 두었다. T-33 뒤 코디네이터 범위 조정(2026-10-16)으로 절차·PDK 기술자·확인 test는 oracle-portability 계획이 소유하고, 이 계획은 의존 규칙(N3.9)만 둔다. 그래서 이 계획의 card 목록에 능력 확인 card가 없다. 순서 의존(TR-7·TR-TL 앞)은 그대로다 | 기록(코디네이터 조정) |
| X-26 | **원래 취지와 다름(v0.5.1, 결정 필요 D-24)**: v0.5의 '반복 = 별도 엔진 실행'(안 A)은 같은 topology의 단계 A·S0·블록 결과를 반복마다 다시 계산한다. 원래 취지(사용자 2026-10-15 "계산 재사용은 처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용되게 한다는 것이 원래 취지였어")와 gm/ID '빠른 설계' 취지(T-29 취지 문장)에 맞지 않는다. 대안 안 B(반복 = 실행 계획 안의 변형, N3.8.7 표)는 취지에 맞지만, offset-strategy 실행 계획에 '실행 중 변형 추가' 인터페이스가 필요하다. 두 안을 사용자에게 올렸다(권고 안 B) | **해소(T-35, 안 B)** |
| X-27 | oracle-portability v0.4 O-1(오라클 MC = 네이티브 MC, 결정적 섭동은 진단만, PC-4 삭제)과 v0.5.1 G-14 대안(결정적 불일치 벡터)의 충돌이 있었다. 그 계획의 X-16에 해당한다. G-14를 네이티브 MC 표본 안에서 풀어 해소했고, 결정적 벡터 요구(PC-11)는 철회했다. 같은 v0.4 변경으로 '크기 일관'(선언 계수 대비 σ)은 능력 기록 항목에서 TR-7 판정(§17-1)으로 옮겼다 | **해소(T-35)** |
| X-28 | **꼬리 범위 차이(v0.5.5, 보고 문구)**: T_j 판정과 범위 판정이 확인하는 꼬리의 범위가 다르다.<br>• T_j 판정(design §17-2)은 결정적 끝 표본으로 k·σ 경계까지 확인한다.<br>• 범위 판정(G-14, T-35)은 네이티브 MC 표본이 실제로 닿은 꼬리까지만 확인한다.<br>보고서에 '온도 범위 합격은 표본이 닿은 꼬리까지이고, k·σ 경계는 T_j에서만 결정적으로 확인했다'를 적는다.<br>**oracle-portability '비용 알림'(그 계획 263행: k 꼬리를 실제 표본으로 보려면 표본 수가 급증)에 대한 응답**:<br>• 표본 수는 식 S(design §17, T-12)를 유지한다. 표본 수를 늘리거나 줄여 기준을 바꾸지 않는다.<br>• 범위 판정의 꼬리 한계는 위 문구로 보고한다.<br>• k 꼬리를 온도 범위에서도 확인하려면 표본 수 증가(비용 표 선보고, 한도 초과 시 판정 불능)를 쓴다. 그 선택은 비용 표를 보고 사용자가 정한다. 결정적 섭동은 진단 전용(oracle-portability O-1)이라 대안이 되지 않는다 | 기록(보고 문구) |

**v0.6 원래 취지와 다름**(사용자 결정 O-53 반영):

| ID | 내용 | 상태 |
|---|---|---|
| X-29 | **원래 취지와 다름(사용자 승인됨 O-53 A3)**: 승인된 X-4·X-14 계열 '판정 = 전회로 균형 풀이'(v0.4 T-6 승인, design §10.5 `trim_code_states`)를 뒤집는다. 엔진 안 고정 기하 DC 균형 풀이(Newton)를 지우고 보정 구간·끝 코드 포화를 봉인점 1차 감도 추정(코드 상태 간 trim 주입 전류 변화 ΔI → −G⁻¹·ΔI, off 소자는 G 기여 없음)으로 낸다. 정확값은 오라클 `.dc` 코드 스윕이다. 맞춘 원칙: gm/ID 손계산 속도 우선·물리 정합(O-30·O-31), 엔진 안 순풀이 기계 금지(O-32), DC 대신호 양 계산 규칙 하나(O-43 D1 (a)). design 자리 정정은 N7.5 | 승인됨(O-53) |
| X-30 | **원래 취지와 다름(사용자 승인됨 O-53 B1)**: v0.5까지 전류 0 소자는 '포화 검사에서 뺀다'(N3.5)였고 표현은 design G-1 몫이었다. v0.6은 코드 상태마다 intended_region {triode, off}를 결정적으로 만들어 선언하고, 실제와 다르면 거부하며(우회 금지), on 스위치 영역은 `trim_decl`의 새 칸으로 사용자가 ratify한다(승인 대상이 늘어남) | 승인됨(O-53) |
| X-31 | **원래 취지와 다름(사용자 승인됨 O-53 B2)**: 합격 판정 입력 출처 규칙(gain-budget DEC-90 (1), O-46 (2)·O-50 G5 -- I_off·tol_V = 그 SPICE op 점의 엔진 LUT 조회)을 T_j 밖 온도 점에서는 바꾼다. gm/ID·I_off = 그 온도의 SPICE(I_off는 소자 개별 VGS = 0 풀이), tol_V = T_j LUT 셀(판정 분해능, 온도 무관, 출처 표기). LUT가 T_j 한 조건이라서다(T-29 유지) | 승인됨(O-53) -- 상위 O-205 (1)·O-210 RR-2로 대상 소멸(온도 점 판정 = 부호·포화 비교) |

**v0.7 원래 취지와 다름**(사용자 결정 O-258이 바꾸는 기존 결정과, 그 적용에서 작성자가 유도한 것 -- 상태 칸 '승인됨(O-258)' = 결정 원문에 있음, '작성자 유도 -- 검증·확인 대상' = 원문에 없는 적용 판단):

| ID | 내용 | 상태 |
|---|---|---|
| X-32 | T-2 '엔진이 결정적 변환 `augment_trim(topology, trim_decl)`로 trim 소자를 붙인 파생 topology를 만들고 사용자가 그것을 승인'(FR-T3·N3.3, 옛 X-10 승인 대상)을 '원본 topology + AI가 제안한 trim 파일(role: trim, 포트, 연결표, 코드 입력) 두 선언을 로더 블록 하나가 합성, 사용자는 trim 파일을 승인'으로 바꾼다. 엔진은 trim 소자를 만들지 않는다. 승인 게이트·원본 불변·후보 순위 = 엔진은 유지 | 승인됨(O-258 (B)) |
| X-33 | `trim_decl`(D-15, X-9 -- spec 값 + 승인 선택의 합성 선언)을 없앤다. 선택·코드·영역은 trim 파일, spec 값은 spec `offset_trim` 칸에서 각자 읽는다(합친 사본 없음) | 작성자 유도 -- 검증·확인 대상(O-258 (B) '두 선언 파일 합성'에서 유도) |
| X-34 | 국면 1의 엔진 출력에서 '추천 N·m'(N3.4 1단계 추천, FR-T2)과 '파생 topology·connectivity 표'를 지운다. N·m은 trim 사양 기록(σ_MC)의 N_min과 AI 제안(trim 파일)이 정한다. 그래서 offset-strategy XS-2(국면 1이 {N, N+1} 두 구성의 파생 topology를 냄)는 대상이 '승인된 trim 파일마다 변형'으로 바뀐다(그 계획 XS-2 행 갱신). G-4 대상 소멸 | 승인됨(O-258 (A) 'σ_in은 trim 필요 판단·탐색에만'·(B) 'AI가 제안') -- {N, N+1} 처리는 작성자 유도 |
| X-35 | 덮을 분포의 폭을 '파생 topology 엔진 σ_in'(N3.4 보정 구간 판정·I_u 하한, N3.6 σ_in 행)에서 '승인된 σ_MC 선언'으로 바꾼다. 계통 offset 몫은 합성 회로 엔진 V_id*(판정 W 규칙 그대로)이고, 사양 기록의 oracle \|V_id*\|는 N_min 근거로만 쓴다(두 번 세지 않음) | 승인됨(O-258 (A) '범위 = k·σ_MC + \|계통 offset\|') -- 랜덤·계통 몫 분리는 작성자 유도(v0.3 C1 원리) |
| X-36 | 코드 상태별 intended_region을 만드는 주체를 `augment_trim`(O-53 B1)에서 합성 로더(trim 파일 코드 입력·코드 상태 선언 읽기)로 바꾼다. off는 선언으로만(O-249) | 승인됨(O-258 (B) '스위치 on/off는 코드로 정해지는 선언') |
| X-37 | 국면 2를 '승인된 파생 topology 하나의 사이징'에서 '부담 변형 O(원본) → C(합성 회로, 원본 θ 고정) → (C front 빔이면) C′(합성 회로, 전 θ)'로 바꾼다. offset-strategy 변형 정의에 '고정 θ 성분'이 더해지고(그 계획 XS-21), 실행 중 추가 허용 종류가 늘어난다(XS-22). θ_0는 국면 1 결과를 읽지 않고 같은 실행 안 변형 O에서 다시 얻는다(S-3) | 승인됨(O-258 'trim 부담 = 같은 θ … 변형 틀', '부담 위반이면 원본 θ까지 재풀이') -- 변형 구성(O·C·C′, 고정 θ 칸, θ_0 재획득, 섞인 θ 성분 → C′)은 작성자 유도 |
| X-38 | offset-strategy card OS-L(실행 중 변형 추가)을 'TR-TL과 같은 변경'에서 '첫 소비자 TR-B와 같은 변경'으로 옮긴다(만들면 배선 근거 그대로, 소비자가 앞당겨짐) | 작성자 유도 -- 검증·확인 대상 |
| X-39 | D-9(바이어스 원천)·D-10(스위치·코드 표현)의 기본안이 엔진 생성 규칙에서 trim 파일 선언 칸의 뜻으로 바뀐다(AI 제안·사용자 승인). 내용(트랜지스터 스위치·전용 게이트 넷·레일 역할 참조 레벨·새 `bias_inputs`)은 유지 | 승인됨(O-258 (B) 'AI가 제안·사용자 승인') |
| X-40 | NFR-T4의 '이름은 정렬된 규칙으로 만든다'(엔진 이름 생성)를 'trim 파일이 선언한 이름 그대로, 충돌이면 거부'로 바꾼다 | 작성자 유도 -- 검증·확인 대상 |
| X-41 | trim 사양 MC의 표본 수 입력을 '엔진 offset 분해능의 상대값 r'(F-21, design §20.1 G-10 식)에서 'spec σ 정확도 선언 r_σ'로 바꾼다(식 n = 1 + ⌈1/(2r²)⌉은 같음). matching 범위 판정 표본 수(G-10)는 바꾸지 않는다 | 승인됨(O-258 (A) '표본 수는 σ 정확도 선언에서 유도') -- G-10 유지는 작성자 판단 |
| X-42 | card 구성: TR-0T를 TR-0에 합치고, TR-MC(trim 사양 구동기)·TR-B(부담)를 새로 두며, TR-* 전부를 LA-1 뒤로 둔다(N5 근거 (i)~(iii)) | 작성자 유도 -- 오케스트레이터 승인 대상(O-229 (7) 위임 범위) |
| X-43 | 시험 회로(T-24·T-28)의 2단계 입력이 '파생 topology'에서 '시험 회로 spec + 사용자 승인 trim 파일'로 바뀐다. trim 파일도 topology 연결이므로 사용자 승인 전에는 쓰지 않는다(T-9·T-17, 원칙 15) | 작성자 유도 -- 사용자 몫 입력(trim 파일 승인) |

### N7.4 v0.5 오케스트레이터 기본안(원칙으로 확정, 사용자가 바꿀 수 있음)

| ID | 기본안 | 원칙·근거 |
|---|---|---|
| O-1 | Δ_T 기록 = DEC-72 `model_error_<metric>`과 같은 모양의 측정 기록(값·단위·출처 지문)(→ 상위 O-178로 그 옛 형식 삭제 -- 모양 인용만 무효, 기록 성질은 그대로). 이름은 상위 DEC-68로 design이 정함(후보 `temp_margin_<metric>`·`range_margin_<metric>`·`delta_t_<metric>`). 쓰는 주체 = 구동기. 엔진 입력은 다음 변형의 제약 입력 하나다(D-24 안 B). spec 측정 선언 절은 Δ_T에 쓰지 않는다 | 상위 DEC-72 모델 오차 선례(같은 기록 모양), T-30 '측정 선언', 입력 경로 하나(NFR-T3) |
| O-2 | (v0.5.1에서 내림. 원문 항목 처리는 사용자 결정 T-36으로 D-25 (c)+(c-2) 확정) | X-22 |
| O-3 | '(ii) 지배' = (i)·(iii)을 0으로 두어도 불합격. **확정(T-35)** | X-20. 상수 없이 '크기 조정 불가'를 직접 유도 |
| O-4 | 온도 점 = 판정 범위 끝점 + T_j | design §17-3 선례. 비단조 위험은 G-11 |
| O-5 | 멈춤 규칙 신뢰 배수 = spec k. 한계: k는 덮을 분포 폭의 배수이지 신뢰 수준이 아니다. k를 바꾸면 멈춤 기준도 바뀐다. 보고서에 적는다 | design X-T13 선례(새 신뢰 상수 금지) |
| O-6 | Δ_T는 반복마다 새 값으로 바꾸고(누적 안 함), 문턱을 조이는 쪽으로만 쓴다(음수면 0). 대안 = 단조 최댓값(수렴 보장, 과조임 위험) | Δ_T가 'T_j 대비 온도 몫'으로 정의되어 누적하면 같은 몫을 두 번 셈(N3.8.3), 기준 약화 금지 |
| O-7 | T_j 판정(TR-7 §17-1·2)이 불합격이면 루프를 돌지 않고 원인별 사유 코드로 보고한다(이름은 design G-12). 원인은 셋이다. (1) 정의·판정 문제(상위 사용자 결정 O-178): §17-1 σ_in 정의 동일성 관문(PDK 선언에서 읽은 면적 지수·bin 환산 대 엔진 식 -- 거부 관문) 위반, 또는 엔진·오라클 판정 뒤집힘(대조 기록 -- 최종 offset 합격은 오라클 MC, 수치 차는 판정 기준 아님). (2) MC 표본 꼬리: 창 안 네이티브 MC 표본의 잔여가 V_res 초과. (3) 끝 표본 판정: design §17-2 결정적 끝 표본이 T_j 판정에 남는 경우에만 해당한다(G-14 닫힘으로 범위 판정에서는 진단만. T_j 판정에서의 역할은 TR-0T가 oracle-portability v0.4와 맞춰 정함) | Δ_T는 온도 몫만 다룬다. 같은 조건의 실패는 원인을 나눠야 다음 행동(정의 관문·닫기, 표본 수, 끝 표본 규칙)이 정해진다 |
| O-8 | 판정 온도 범위는 T_j를 포함해야 한다. 아니면 범위 판정을 거부한다 | Δ_T의 기준점이 T_j다 |

**후속(이 커밋 밖, 오케스트레이터)**:
* 상위 계획 DEC-96 (3) 문언에 'offset·trim 잔여는 T-29 범위 판정' 예외를 더한다(X-17). (v0.6.2 백로그 재감사 OT-B4: 상위 반영 필요 목록에 올림, 상위 반영 확인 뒤 닫음.)
* (→ Δ_T 측정 기록 모양 대조는 TR-0T 범위로 옮김 -- v0.6.2 백로그 재감사 OT-B6, 원문 history.)
* (v0.6, 감사 D1·O-53 B3 -- **해소**) gain-budget N6.1의 offset card 행·인용 규칙과 DEC-23 기준 종류 셋(값·넷·입력 추종)은 gain-budget v6.20 `768f6ca1`이 넣었다(감사 4차, 이 계획 쪽 남은 일 없음).
* (v0.6) design `offset-trim.design.md` 후속 정정 목록은 N7.5다.

### N7.5 design 후속 정정 목록(v0.6 -- 이 커밋에서 design은 고치지 않는다; → card TR-0T design 개정 범위, v0.6.2 백로그 재감사 OT-B10)

design 개정은 TR-0T 범위다(S-7: 계획 → design). 줄 번호는 master `9401e98f`의 `docs/02-design/features/offset-trim.design.md`다.

| design 자리 | 정정 내용 | 근거 |
|---|---|---|
| §10.5 `trim_code_states` 코드 상태 균형 풀이(602행) | 엔진 안 고정 기하 DC 균형 풀이 삭제. 보정 구간·끝 코드 포화 = 봉인점 1차 감도 추정, 정확값 = 오라클 `.dc` 코드 스윕 | O-53 A3, X-29 |
| 상수 원칙 행 '반복 상한(균형 풀이 newton)은 `k_max`'(84행) | 균형 풀이가 없어지므로 그 문구 삭제 | O-53 A3 |
| 함수 레지스트리 개념 행 '고정 기하 DC 균형 풀이'(810행) | 행 삭제. 1차 감도 추정은 gain-budget DEC-23 계산(O-43 D1 (a))과 같은 꼴이므로 레지스트리 §2 정본표를 먼저 대조한다 | O-53 A3, 단일 정본 |
| TR-5c '코드 상태 균형 풀이' test(846행) | 1차 감도 추정 대 오라클 `.dc` 코드 스윕 대조(차는 대조 기록)로 바꾼다 | O-53 A3 |
| E-4(104행) '봉인 9는 ID > 0 소자만' | 코드 상태별 intended_region 생성·대조(O-55 U1 원인 구분), off 소자 사이징·역산 경로 제외(꺼짐 판정 = 상위 N3.6 정본 부호 비교, off 선언 대조 삭제 -- 상위 O-202) | O-53 B1, O-55 V5 |
| `output_reference` 칸(730행) | DEC-23 인용 하나로(기준 종류 셋 + 차동 기본, 정의 자리 DEC-23) | O-53 B3 |
| A_dm 환산(σ_in·t) 자리 | A_dc(DEC-23·N3.8) 인용으로 | 감사 A4 |
| V_sys,s·`offset_systematic` 인용 자리 | DEC-23 V_id* 인용으로 | 감사 A1 |

**(v0.7, O-258 -- 원칙 19 전수 대조)** 바뀐 결정(N7.2 'v0.7' 표)을 읽는 design·다른 계획 문언의 낡은 자리 목록은 history 'v0.7.0' '낡은 자리 목록'에 있다(이 커밋에서 design·다른 계획은 고치지 않음 -- design은 card TR-0 범위, 다른 계획은 각 계획 개정 입력).

---

## N8. 원문 근거표

* 보관 위치: `skills/analog-gmid-design/assets/technique/sources/<폴더>/`(`source.pdf`·`paper.md`). 쪽 렌더는 `python tools/pdf_to_md.py ensure`로 만든다.
* 쪽 번호는 PDF 쪽이다. 수치는 인용하지 않는다.
* v0.5(온도 보정 루프)는 새 원문을 쓰지 않는다. 'CMOS offset trim은 drift를 보정하지 않음'은 R7(Kay 2024 §1.2 p.7), '패키지 뒤 trim'은 R3(Zhou 2017 p.1)이다. 표본 수·신뢰 구간 식은 design §17과 오라클 코드(F-21)의 유도식이다. PDK 문서 출처(불일치 계수 등)는 oracle-portability 계획의 PDK 기술자가 항목마다 웹 링크·로컬 PDF 경로·쪽으로 단다.

| R | 원문 | 웹 | 로컬 PDF | 쪽·위치 | 이 계획에서 쓰는 곳 |
|---|---|---|---|---|---|
| R1 | A. R. Mohamed, M. F. Ibrahim, F. Farag, 'Input Offset Cancellation Trimming Technique for Operational Amplifiers', SIECPC 2013 | [pure.kfupm.edu.sa](https://pure.kfupm.edu.sa/en/publications/input-offset-cancellation-trimming-technique-for-operational-ampl/) | `offset_trim__mohamed_2013/source.pdf` (원본 `G:/내 드라이브/work/Todoc/논문모음/input offset cancellation trimming technique for operational amplifier_mohamed2013.pdf`) | p.2 Fig.2·식(1)(2), p.3 Fig.4·식(3)(4)(7), p.4 Fig.9·11 | 범위 밖 대안(신호 경로 level shifter: 버퍼 이득 1 미만, 대역 제한) 비교. 주입항이 offset을 상쇄하는 구조(N3.4) |
| R2 | H. M. von Staudt, 'Trim DAC Design with Minimum DNL for Self-Trim with Self-Test Schemes', IEEE IMS3TW 2011 | [doi:10.1109/IMS3TW.2011.34](https://doi.org/10.1109/IMS3TW.2011.34) | `offset_trim__staudt_2011/source.pdf` (원본 `.../논문모음/(Bible - self trim) Trim DAC Design with Minimum DNL for Self-Trim with Self-Test Schemes__staudt2011.pdf`) | p.1-2 §II.A, p.2-3 §II.C·Table I·Fig.4, p.3-4 §III·Table II·III | 범위가 분포를 덮을 조건과 'µ = 0' 가정(X-14), 이진 주 전이 DNL, 양의 DNL 꼬리, 잔여와 DNL(N3.4) |
| R3 | Y. Zhou, A. Kay, 'Offset Correction Methods: Laser Trim, e-Trim, and Chopper', TI SBOT037A, 2017 | [ti.com/lit/SBOT037](https://www.ti.com/lit/SBOT037) | `offset_trim__zhou_2017/source.pdf` (원본 `.../논문모음/(Reference - trim) Offset Correction Methods_Laser Trim, e-Trim , and Chopper.pdf`) | p.1 laser·e-Trim, p.2 Fig.2·Fig.3·Table 1 | 패키지 뒤 내부 보정 전류원 trim(e-Trim, 'low offset voltage and drift' 제품군, p.1). chopper는 시간·온도 drift를 평균해 없애고 1/f를 제거한다(p.2). 한 온도 trim이 drift를 보정하지 못한다는 근거는 R7이다 |
| R4 | G. Bertotti et al., 'An 8 bit current steering DAC for offset compensation purposes in sensor arrays', Adv. Radio Sci. 10:201-206, 2012 | [doi:10.5194/ars-10-201-2012](https://doi.org/10.5194/ars-10-201-2012) | `offset_trim__bertotti_2012/source.pdf` (원본 `G:/내 드라이브/work/Todoc/기술문서/ADC/An 8 bit current steering DAC for offset compensation purposes in sensor arrays_ars-10-201-2012.pdf`) | p.2 §2·§3 식(2)(3), p.3 식(4)(5), p.4 Fig.3·4, p.5 Fig.5-8 | 분할 DAC 최악 DNL 분산 식(3)(N3.4 DNL), 차동 steering 셀(T-3), 단위 전류 σ의 동작 영역 의존 |
| R5 | C.-W. Lu, 'An Offset Cancellation Technique for Two-Stage CMOS Operational Amplifiers', IEEE ICICDT 2007 | 찾지 못함 | `offset_trim__lu_2007/source.pdf` (원본 `.../기술문서/ADC/(Ref) An Offset Cancellation Technique for Two-Stage CMOS OPamp.pdf`) | p.2 Fig.2·3, 식(6)-(10) | 1단 출력 넷 전류 주입, 주입 소자를 더할 때 부하 전류 균형(N3.5), 주입 오차 ∝ G_m,aux/G_m1(N3.7) |
| R6 | V. Srinivasan et al., 'A Precision CMOS Amplifier Using Floating-Gate Transistors for Offset Cancellation', IEEE JSSC 42(2), 2007 | [doi:10.1109/JSSC.2006.889365](https://doi.org/10.1109/JSSC.2006.889365) | `offset_trim__srinivasan_2007/source.pdf` (웹 다운로드) | p.1 §I·Fig.1 | current-mode DAC로 부하 전류를 조정하는 offset 보상(N3.2 주입 쌍 = 입력쌍 drain) |
| R7 | A. Kay, 'Op Amp Offset Voltage and Bias Current Limitations', TI SBOA590, 2024 | [ti.com/lit/pdf/sboa590](https://www.ti.com/lit/pdf/sboa590) | `offset_trim__kay_2024/source.pdf` (웹 다운로드) | §1.2: p.6 Figure 1-6, p.7 Figure 1-8 문단 | CMOS drift는 offset에 비례하지 않아 한 온도 trim이 drift를 보정하지 않는다(N1.2, N3.6) |

---

## N9. 위험과 대응

| 위험 | 대응 |
|---|---|
| trim 소자가 S1v에서 `load`·`tail_source`로 분류돼 offset·잡음 가드와 `iv_matching_l` 부하 집합을 오염시킨다 | `trim_dac` 역할을 먼저 둔다(TR-4, 소자 출처 칸 READS). 합성 대 원본 구조 동일 검사(N3.3-2)로 막는다 |
| TR-4 규칙 파일 변경으로 `structure_rule_fp()`가 바뀌어 current_reuse_telescopic_ota·nmcnr_amplifier의 structure.json 사실이 review_needed로 돌아간다(trim 선언과 무관) | 재승인은 사용자 승인 사항이다. TR-4 착수 조건(재승인 계획 승인)과 병합 조건(재승인 완료)에 넣는다. 완료 조건 (1)의 범위는 D-14다 |
| spec `meta.topology_fp`가 합성 회로 지문과 맞지 않아 로드가 거부된다 | D-13 결속: spec은 원본 지문에 묶고, trim 파일·합성 회로 지문은 승인 기록에 묶는다(TR-1·TR-3, N3.3) |
| t가 θ에 따라 변해서 승인한 쌍·N·m이 국면 2에서 불가능해진다 | 국면 1 후보표에 front 위 t 범위를 적는다. 국면 2는 부담 재풀이(C′) 뒤에도 해가 없으면 `trim_config_infeasible`로 멈추고, AI 재제안·재승인으로 되돌린다(N3.1-6). 엔진이 몰래 N·m을 바꾸지 않는다 |
| **(v0.7)** AI가 제안한 trim 구조가 물리적으로 맞지 않거나(주입 넷 headroom·극성) 원본 회로 성능을 크게 깎는다 | AI 값은 엔진·oracle 관문을 지나야 판정이 된다(DEC-110 역할): 합성 로더 스키마 검사(N3.3), 국면 2 판정·E-0, 부담 제약(N3.11), trim 뒤 잔여 MC. 근거 칸(후보표 id·사양 기록 id·의도 문서 지문)으로 제안 출처를 추적한다 |
| **(v0.7)** σ_MC를 잰 닫힌 점과 국면 2의 θ_0(변형 O 선택 점)가 달라 사양이 실제 분포와 어긋난다 | trim 뒤 잔여 MC(합성 회로 닫힌 점)가 최종 판정한다. 불합격이면 trim 파일 재제안(사양 다시 잼). 차는 결과에 기록한다 |
| **(v0.7)** 사양 MC 비용(n = 1 + ⌈1/(2·r_σ²)⌉ × 실행 시간)이 크다 | 비용 표 선보고, 한도 초과는 '판정 불능(표본 부족)'이고 n을 줄이지 않는다. r_σ는 사용자 선언 -- 정확도와 비용의 교환을 사용자가 고른다 |
| **(v0.7)** 원본 θ를 고정한 부담 변형 C에서 원본·trim 소자가 θ 성분을 공유해 고정이 정의되지 않는다 | 섞인 성분이 있으면 C를 건너뛰고 C′로 가며 섞인 목록을 보고한다(N3.11, G-24) |
| 주입 넷(fold 넷 등)의 headroom이 셀 출력 소자 VDsat + 스위치 VDS를 못 받친다 | 극성별 headroom 창('추정')으로 후보를 거른다(N3.2). 끝 코드 포화를 봉인점 1차 감도 추정으로 검사하고 정확값은 오라클 `.dc` 코드 스윕이다(N3.5, O-53 A3) |
| DAC 용량이 비주극점을 낮춰 PM이 떨어진다 | 전회로 MNA 판정에 자동으로 들어간다. 후보표에 주입 넷 용량 증가를 보고한다 |
| 합성 회로 디스크 사본이 원본·trim 파일과 어긋난다(stale) | 합성 회로는 디스크에 쓰지 않는다. 실행마다 합성 로더가 다시 만들고 trim 파일 sha256·합성 회로 지문을 승인 기록과 대조한다(NFR-T3, N3.3-3) |
| 범위·DNL 유도에 원문 관례값(±5σ, 5 %, 'DNL < LSB/2' 같은 경계 등)이 섞인다 | NFR-T2. 숫자 리터럴 lint와 design 검증 항목에 넣는다 |
| 상보 입력쌍 회로에서 한 CM 점 판정이 ICMR 전체 보정을 보장하지 않는다 | D-7 보고 문구. ICMR 여러 점 판정은 범위 밖이다 |
| T_j 한 온도에서 trim하므로 다른 온도에서 잔여가 V_res를 넘는다(CMOS drift는 offset과 비례하지 않음, Kay 2024 §1.2 p.7) | v0.5(T-29): trim 잔여는 고정 코드 온도 sweep으로 범위 판정한다(N5.1 3번, N3.8.2). 불합격이면 보정 루프(N3.8)로 크기 여유를 준다. 코너별 보정 구간·끝 코드 headroom 온도 의존은 보고 전용 그대로다. 보고서에 'trim은 drift를 보정하지 않음'을 적는다(FR-T9) |
| DAC 바이어스 원천(D-9)의 온도 특성이 t(T)·δ(T)를 바꿔 보정량 자체가 온도에 따라 변한다 | D-9 설명과 G-8. TR-7 온도 sweep으로 드러낸다 |
| 엔진 σ_in이 SPICE σ_in과 맞지 않으면 MC 잔여 결과로 엔진 판정을 해석할 수 없다 | N5.1 1번을 TR-7 첫 확인으로 둔다 |
| MC 샘플 수가 k 꼬리를 확인하기에 부족하다(비용 한계) | 샘플 수 규칙을 TR-0에서 독립 검증자가 정한다. 부족하면 결과에 '꼬리 미확인'으로 적는다 |
| 패키징 응력·장기 drift·trim 측정 잡음은 DC MC로 재지 못한다 | 범위 밖으로 보고서에 적는다(N5.1 한계) |
| 기존 offset 제약과 trim 선언이 함께 있으면 한쪽이 조용히 무력화된다 | D-4 기본안: 로더 거부 |
| 전류 0 소자(꺼진 스위치·꺼진 출력)가 DC writer·LUT 경로에서 정의되지 않은 값을 낸다 | intended_region `off` 선언·LUT 경로 제외·0 모형 + 1차 ΔV·O-h·VGS < 0 점 정지(O-53 B1·상위 O-202·O-212, G-1 해소) |
| trim 소자를 붙이면 원본 소자의 matching group·대응 넷 유도가 바뀐다 | G-2 비교 필드 정의와 TR-2·TR-4 전 library 13회로 측정 |
| 같은 k로 양의 DNL 상한을 두면 다중 전이 때문에 실제 수율이 offset 수율보다 낮다 | D-3 한계 문구. 오라클 Monte-Carlo 판정(완료 조건 (3))이 실제 비율을 잰다 |
| **(v0.5)** 보정 루프가 국소 여유로 수렴하지 않는다. Δ_T는 한 점에서 잰 값인데, 조인 문턱으로 다시 돌면 front 점이 바뀌어 그 점의 온도 몫이 다를 수 있다(진동·발산) | 멈춤 규칙(N3.8.5): 수렴(분해능 안) 또는 front 빔 또는 사용자 반복 상한. 반복 이력(Δ_T, 점, 판정)을 모두 남겨 진동을 드러낸다. 판정 대상 점은 결정적 선택 규칙(D-20)으로 고른다 |
| **(v0.5)** MC 비용: n(식 S) × 온도 점 × 코드 전수 × 반복 수로 늘어난다 | 반복마다 오라클 실행 전에 비용 표를 낸다. 한도를 넘으면 '판정 불능(표본 부족)'으로 멈추고, n·창·온도 점을 줄이지 않는다(T-12 (3)). 판정 대상 점은 하나(D-20)가 기본이다 |
| **(v0.5)** 메모리: 엔진 탐색과 오라클 MC 시뮬레이션이 다른 작업과 메모리를 나눠 쓴다 | 구동기는 엔진 계산과 오라클을 차례로 하나씩 돈다(NFR-T9). 시뮬레이터 병렬 수는 실행 설정 선언값이다 |
| **(v0.5.1)** 결정적 끝 표본(이상 전압원, 온도 계수 0)이 꼬리 표본의 원본 offset drift를 빼서 k·σ 경계에서 거짓 합격을 낸다 | G-14 닫힘(T-35): 범위 판정·Δ_T는 같은 seed 네이티브 MC 표본을 온도마다 다시 잰 실제 꼬리 표본으로 하고, 결정적 끝 표본은 진단만 한다(N3.8.2). 남는 한계는 '꼬리는 표본이 닿은 데까지'이고 보고서에 적는다 |
| **(v0.5.1)** matching 범위 판정에 계통 offset V_id*(T)가 필요한데 오라클 MC는 그것을 빼고 잰다(F-20a). 단일 종단 회로는 온도마다 출력 기준 문제가 다시 생긴다 | V_id*(T) = OP-5 `.dc`를 온도 조건에서 돌린 것(PC-10). 기준 정의 자리는 DEC-23 하나이고 선언 없는 단일 출력은 정의 불능이다(O-53 B3, G-15 닫힘) |
| **(v0.5.1)** Δ_T를 받을 엔진 입력 경로가 없다(spec 측정 선언 절도 없고 옛 DEC-72 형식은 상위 O-178로 삭제, F-23). 만든 함수가 쓰이지 않는다 | D-24 안 B(T-35): 구동기 → 변형 제약 입력 → 제약 행 배선을 TR-TL 범위와 완료 조건 7에 넣는다(만들면 배선). spec 측정 선언 절은 만들지 않는다(상위 O-178) |
| **(v0.5.1)** 반복마다 같은 topology의 단계 A·S0를 다시 계산해 gm/ID '빠른 설계' 취지를 깎는다 | D-24 안 B 확정(T-35): 실행 계획 안의 변형으로 색인을 공유한다. 대가인 메모리 동시 점유와 변형 추가 인터페이스는 N3.8.7 표 |
| **(v0.5)** (ii) DAC 바이어스 drift는 θ로 줄일 수 없는데 루프가 계속 문턱을 조여 front를 비운다 | 분해 정지(N3.8.4): (ii) 지배면 재실행 없이 정지·보고. 바이어스 원천 변경은 사용자 결정(D-22) |
| **(v0.5)** 오라클 MC·온도 경로가 조용히 동작하지 않는다(불일치 변수를 못 찾아 분산 0, 온도 지정 무시). 그러면 범위 판정이 거짓 합격을 낸다 | 능력 기록 의존 fail-closed(N3.9). 절차는 oracle-portability 계획 |
| **(v0.5)** Δ_T가 model_error와 섞여 같은 차이를 두 번 센다 | 역할 구분(N3.8.3 표): Δ_T는 오라클끼리의 차(범위 최악 − T_j), 대조 기록(상위 DEC-72, O-178)은 같은 조건의 엔진 − SPICE 차이고 판정 기준이 아니다. T_j 판정 실패는 Δ_T로 처리하지 않는다 |
| **(v0.5)** 이전 Δ_T가 다른 코드·LUT·능력 기록에서 잰 값인데 조용히 쓰인다 | 출처 지문 대조 항목 불일치는 정지(N3.8.3, fail-closed) |
| **(v0.6)** 봉인점 1차 감도 추정(O-53 A3)이 끝 코드의 큰 전류 변화에서 실제 끝 전압·포화 여유와 다르다 | 정확값은 오라클 `.dc` 코드 스윕이다. 차는 대조 기록(상위 DEC-72)이고 판정은 오라클이 한다 -- oracle 미배선이면 판정 다리 보류(gain-budget N6.3 (i))로 통과로 세지 않는다 |
| **(v0.6)** off 선언 소자가 실제로 전도하거나 on 스위치 영역 선언이 실제와 달라 판정이 조용히 틀린다 | (상위 O-202·O-212로 고침) `off` 선언 소자는 대조하지 않고, 그 효과는 상위 gain-budget N3.6 '전도·포화 경계·`off` 선언 정본' (5)가 막는다 -- 0 모형 + 1차 ΔV·G2-a 관문(보정 포화 여유 < 0 = E-0, `triode` 선언 소자 보정 여유 ≥ 0 = E-0 -- 상위 사용자 결정 O-222; 이 계획 on 스위치 + off 스위치가 첫 소비자 후보, O-212로 LUT 확장 전 미발동)·O-h(`judged_by` 선언 검증 불능 = 정지)·VGS < 0 off 점 E-0 정지(해소 = LUT 확장, TR card 착수 조건); on 스위치 영역 선언(`triode`, `saturation` → 선언 없음 사상)은 선언 대조 거부(O-53 B1, 우회 금지)와 그 거부 test; 옛 '완료 조건 8 off 전도 픽스처 거부'는 대상 소멸(완료 조건 8) |
