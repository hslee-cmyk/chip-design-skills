---
template: plan
version: 0.8.0
---

# offset-strategy Planning Document

> **Summary**: spec이 offset을 **수단**(`offset_in_sigma_mv <=` 제약이나 `offset_trim` 선언)이 아니라 **요구**로 쓰게 한다. 요구는 `offset_requirement{offset_in_max_v, coverage_multiple, strategy}` 하나다. 엔진은 요구와 방식(`matching`·`trim`·`compare`)에서 판정 제약을 유도하고, **실행 계획**(변형 목록, 변형 = (topology 변형, 제약 집합))을 만들어 한 실행 안에서 차례로 돈다. 변형들은 단계 A·S0·블록 결과 색인을 공유한다. 이 일은 파이프라인 층 모듈을 다시 쓰는 것이고(S-2), 핵심 층(graph·블록·kernel·search)은 유지한다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code
> **Status**: **v0.8.0 -- 사용자 결정 O-258 반영(offset-trim v0.7.0과 같은 브랜치): topology 변형 = 원본 또는 **합성 회로**(원본 + 승인된 trim 파일, 옛 '승인된 파생 topology'), 국면 정의 갱신(국면 1 = 후보표 -- 추천 {N, N+1}·파생 topology 출력 없음, 국면 2 = 부담 변형 O·C·C′), 변형에 **고정 θ 성분** 칸(XS-21), 실행 중 추가 허용 종류 = Δ_T 문턱 + 부담 변형 C·C′(XS-22), OS-L 첫 소비자 = offset-trim TR-B(같은 변경), XS-2 대상 갱신, **원래 취지와 다름**(XS-21·XS-22·XS-2 갱신 -- N5), 독립 판정 전**(2026-11-07, 브랜치 `plan/20261107-trim-compose`, base master `faf69218`; 경위 history 'v0.8.0') 이전 판: **v0.7.8 -- 상위 gain-budget v6.38.7 둘째 커밋 전파(상위 사용자 결정 O-217·O-218 -- LR6 소비자 문단의 출발점 L 칸; 규칙 변경 0), 승인됨(상위 gain-budget v6.38.7 사용자 결정 O-219, 2026-11-03 -- plan/v6387 HEAD `93a7642d`)**(2026-11-03, 브랜치 `plan/v6387`; 경위 history Version History 0.7.8 행) 이전 판: **v0.7.7 -- 상위 gain-budget v6.38.6 열일곱째 커밋 전파(상위 사용자 결정 O-205 (2)·O-210 RR-2 -- N4 OS-V 선행 문언의 '2단계 전도 판정' 삭제, 판정 = 오라클 한 단계; 선행 card 집합 불변), 승인됨(상위 gain-budget v6.38.6 사용자 결정 O-216, 2026-11-02 -- plan/v6386 HEAD `e71aa597`)**(2026-11-01, 브랜치 `plan/v6386`; 경위 history Version History 0.7.7 첫째·둘째 커밋 행 -- 둘째 = 상위 스무째 커밋(사용자 결정 O-214 card LA-1a)) 이전 판: **v0.7.6 -- 승인됨(상위 사용자 결정 O-193, 2026-10-31) -- DS-1 = (나) 평가 1회 + 변형별 판정(조건 2개: 판정 행 graph 필드 `constraint_rows`·`EvalResult` 판정 칸 삭제, 요청별 분할 graft·새 요청 fail-closed; 상위 사용자 결정 O-176 Ⅵ -- S-14 (다) 번복, 원래 취지와 다름(승인)), 상위 gain-budget v6.38.5 열아홉째 커밋, 검증 대기**(2026-10-29, 브랜치 `plan/v6385`; 경위 history Version History 0.7.6 행) 이전 판: **v0.7.5 -- 승인됨(상위 사용자 결정 O-173, 2026-10-29) (상위 v6.38.4 열여덟째 커밋 계획 검증 7 반영 -- 고유 키 정의를 상위와 일치, 검증 대기; 상위 v6.38.4 열일곱째 커밋 계획 검증 6 반영 -- PS-7 열거 생산자 문언 = 먼저 병합 card, 검증 대기; 상위 v6.38.4 열여섯째 커밋 계획 검증 5 반영 -- 조건부 제작 단위 = 평가 키 부분·열거·계수·분할, 'U16 뒤'·'U17 ②' 순서 표지 정리, 검증 대기; 상위 v6.38.4 열다섯째 커밋 계획 검증 4 반영 -- PS-7 대상 = S3 색인 평가 키 부분·조건부 제작, OS-2 진입점 종료 코드·θ*, DS-U9 기본안, 검증 대기; v6.38.4 열넷째 커밋 백로그 재감사 반영 -- 삭제 2·배정 5·질문 3) -- 상위 gain-budget v6.38.4 재판정 P1 후속 정정(S-10 공존 검사의 판정 대상 = 상위 S0 필드 `constraint_classes` 판정 대상 칸 READS -- 술어 재호출 없음, 검사 자리 = 로더 → 그 S0 블록(제약 분류) 안 거부(첫 소비자 앞), **원래 취지와 다름**(자리 변경), 거부 범위·fail-closed 불변), 검증 대기**(2026-10-29, 브랜치 `plan/v6384`; 경위 history Version History 0.7.5 행) 이전 판: **v0.7.4 -- 상위 gain-budget v6.38.3 열두째 커밋(사용자 대원칙 O-169) 계통 offset 판정 자리 재작성(상위 N6.35 E-05·U-108·O-118 1번·O-119 인용: V_id* = DEC-23 (나′) 세 성분 합, 커널 + front 판정 W 재판정 -- 옛 'ΔW = 0이면 0 → 통과·커널 판정 제외' 문언 삭제)·S-10 공존 검사 = 출처 kind 술어(`judged` 칸 삭제), **원래 취지와 다름 -- 승인 O-170**(이 계획 승인 범위를 상위 판에서 다룸, 상위 승인 표 #23·#38), 승인됨(상위 사용자 O-170, 2026-10-29)**(승인 커밋 -- 상위 gain-budget v6.38.3 승인 O-170; 경위 history 승인 행)(2026-10-28, 브랜치 `plan/v6383`; 둘째 커밋 -- 상위 열셋째 커밋·상위 독립 검증 11 V11-M3·L-4·L-6: S-10·N3 공존 행의 판정 대상 술어를 출처 축·metric 결정 대기 축 둘을 담는 상위 SF-1 범위 8 술어 하나로, O-43 D1 (c) 행 판정 위치 인용의 낡은 'front 전용 예외'를 상위 DEC-74·U-108로, 자동 켬 번호 (i)~(iv); 경위 history 0.7.4 행) 이전 판: **v0.7.3.1 -- 상위 gain-budget v6.38.2 LR6 개정(DEC-105 (6), 사용자 결정 2026-10-14 Q-N2 B) 인용 정정, 승인됨(상위 사용자 결정 O-166, 2026-10-28)**(2026-10-28; 212·304·408·619행, 규칙 변경 없음 -- 전파; 경위 history 0.7.3.1 행) 이전 판: **v0.7.3 -- gb v6.23 정합, 승인됨(사용자 O-70 (2), 2026-10-21, 병합 `2dab561b`)**(base master `cd4c6951`). 근거: 승인된 사용자 결정 O-62 (3)·O-63 (1)·(2)·O-64 (2)(`wt/_drafts/user_decisions.md` 각 행)과 gain-budget v6.23(병합 `294bde4d`)의 'DE-1 후속 정정 표' offset-strategy 행(O-62 (3)·O-63 (1), 검증 D-2 -- 각 계획이 자기 개정에서 고친다), gap 재분석 `wt/_drafts/evidence/2026-10-21/os_design_v032_plan_gap.md` §5·N10~N17. 바뀐 것 넷: (1) front 합성 판정의 정의 불능 점 -- σ_in·V_id*가 DEC-23 'A_dc 정의 불능 갈래'(ΔW와 무관, 갈래 먼저)이거나 커널 출발 창 미수렴(O-64 (2))이면 fail-closed로 front에서 빼고 원인 = 그 사유(offset 위반 아님), ΔW = 0 → 0은 \|A_dc\| > 판정 분해능일 때만(N2 O-43 행, N3.3 ②, 완료 조건 10 (b) 정의 불능 toy, N9). (2) OS-V 대조에 oracle-portability N3.9 `offset_sys_mv` 행 (vi) '정의 경계 불일치' 인용(O-63 (2)). (3) OS-2 선행 칸에 gain-budget card DE-1 (c) 명시(지금까지 U17 ② ⇒ LA-1 ⇒ DE-1 사슬로 함의). (4) **계획 착수 조건 보강 -- 사용자 승인 대상**: OS-2 착수 조건에 PS-1 잔여(DEC-74 front 판정 기록 -- 자리 종류 = gain-budget 계획 개정, 이름 = card DE-1 design·착수 실측)와 PS-7(S3 색인 평가 키 열거 API, U17 ② design)을 더하고, `open_run` 서명 점검 항목을 둔다(N7.1, N7.2 OS-2 행, N10.4). (1)~(3)은 승인된 결정의 정렬이고 새 결정이 아니다. 같은 판 둘째 커밋에서 검증(`wt/_drafts/evidence/2026-10-21/os_plan_v073_validation.md`) M1·M2·N1~N5를 반영했다(커널 행 ① 정의 불능, PS-1 잔여 소유 통일, gb 알림 행 GB-N1). 상위 정본 현행판은 master의 gain-budget v6.23(병합 `294bde4d`)이다. 이전 Status 문단 원문은 history H1 'v0.7.3'에 있다.
>
> **규칙 근거(v0.7, 바뀌지 않음)**: v0.7은 승인됨(사용자 O-57 "병합 승인", 2026-10-20). 근거: 사용자 결정 O-53(2026-10-20 "권고대로 진행해", `wt/_drafts/user_decisions.md` O-53 행) A2(matching 합성 제약 판정 위치 분리 -- 원래 취지와 다름 승인, N5 XS-20)·B3(offset 기준 정의 자리 = DEC-23 하나), 정합 감사 요약 `wt/_drafts/evidence/2026-10-20/offset_audit_summary.md`의 OS 몫(A1, A2, C1, C2, C3, D2, D3, D4, E1), 상위 정본 gain-budget v6.20(`plan/gb-v620` `f2579b2f` -- DEC-23·DEC-74·N3.8·N3.9 LR6·N6.1·N6.3·LA-1·N6.18 VB-1·N6.20 EO-1), oracle-portability v0.6.10(`plan/oracle-v0610` `64687b21` -- OP-3·OP-5), offset-trim v0.6(`plan/offset-trim-v06` `23e6a142`). 정의는 정본 계획을 인용만 한다. 계획 v0.6.2까지는 사용자 승인됨(S-5~S-14, T-34~T-37). 이전 Status 문단과 바뀐 문장 원문은 history H1 'v0.7'·'v0.7.1'에 있다.
> **이력**: 경위, 결정 원문, 측정 조건, 버전 이력은 [offset-strategy.history.md](offset-strategy.history.md)에 있다.
> **상위 계획**: [gain-budget-gmid-sizing.plan.md](gain-budget-gmid-sizing.plan.md)(원칙 N1.4 NFR, N2 결정, N6.3 병합 전 확인). **관련 계획**: [offset-trim.plan.md](offset-trim.plan.md)(trim 방식의 규칙 정본). 충돌하면 상위 계획이 이기고, offset-trim과의 충돌은 N5(원래 취지와 다름)와 N9에 올린다.

---

## N0. 문서 안내

* **담는 것**: 목적·범위, 확정 결정, 요구, 엔진 반영 구조와 규칙, 원래 취지와 다른 항목, 선행 실측(착수 조건), 순서·card 초안, 완료 조건, 위험, 원문 근거, 열린 결정.
* **담지 않는 것**: 경위, 결정 원문 전문, 측정 조건의 세부, 정정 이력. 이것은 history에 둔다.
* **값 원칙**: 이 문서에는 수치 상수를 두지 않는다.
  * `offset_in_max_v`·`coverage_multiple`(k)·방식 선택, 1/f·면적 판정 값, trim 잔여 V_res·온도는 사용자 spec 값이다.
  * 예산은 선언(E_B)이나 정의(E_total, 상위 design 40 §2.4.9)에서 온다.
  * 나머지는 엔진 해석값·LUT·PDK 선언에서 유도한다. 원문 수치는 인용하지 않는다.
  * 예외: 사용자가 결정한 값과 fixture 지정(예: F-1의 회로·k·`offset_in_max_v`)은 출처(결정 기록)와 함께 적는다.
* **이름 원칙**: 규칙에 회로·소자·넷 이름을 쓰지 않는다. 회로 이름은 사실 표(N3.0)에만 나온다(옛 측정 대상 N6 M2는 v0.7.5 백로그 재감사 OS-B4로 삭제).
* **인용 규칙**: 코드는 `파일:줄`이고 기준은 base `067614c`(worktree `wt/ostrat-plan`)다. 경로에서 `skills/analog-gmid-design/`은 뺐고 `E/` = `gmid_engine/`이다. design 인용은 `40 §x`(`gain-budget-gmid-sizing.40-engine.design.md`), `OT §x`(`offset-trim.design.md` v0.2, 사용자 승인 T-18)다.

### N0.1 용어

| 용어 | 정의 |
|---|---|
| 요구(offset_requirement) | spec의 offset 요구 하나. 입력 환산 offset 한계 `offset_in_max_v`, 분포 배수 k(`coverage_multiple`), 방식 `strategy`(N3.2) |
| 방식(strategy) | `matching`(입력쌍 면적으로 랜덤 offset을 맞춘다), `trim`(offset-trim의 전류 주입 trim), `compare`(두 방식을 모두 돌려 나란히 낸다, N3.8) |
| 변형(variant) | 실행 계획의 한 항목 = (topology 변형, 제약 집합, 고정 θ 성분). topology 변형은 원본 topology 또는 **합성 회로**(원본 + 승인된 trim 파일을 합성 로더가 만든 것 -- offset-trim v0.7 N3.3; v0.8, O-258 -- 옛 '승인된 파생 topology(OT §7)')이고, 제약 집합은 spec 판정 제약 + 요구에서 유도한 제약이다. **고정 θ 성분**(v0.8, XS-21)은 비어 있는 것이 기본이고, 부담 변형 C에서만 '출처 칸이 원본인 소자의 θ 성분 = 같은 실행 안 다른 변형 선택 점의 기록 참조'다(값 사본 없음 -- offset-trim N3.11) |
| 실행 계획(run plan) | 한 실행에서 돌 변형의 순서 있는 tuple과 각 변형의 예산·국면 표지. 결정적 순수 함수가 spec·topology·승인 기록에서 만든다(N3.5) |
| 국면(phase) | trim이 들어간 방식의 단계(v0.8 -- 정의 정본은 이 행, offset-trim N0.1이 인용). 국면 1 = 승인 기록 없음 -- 원본 topology로 trim 필요 판단·후보표(offset-trim FR-T2; 그 뒤 엔진 밖 oracle MC·trim 사양 기록·AI 제안). 국면 2 = 승인 기록 있음 -- 부담 변형 O·C·C′(offset-trim N3.11). 국면 사이에 사용자 승인 게이트가 있다(T-2 게이트 유지, O-258 (B)) |
| 공통 판정 | 모든 변형에 똑같이 거는 판정: 1/f(`noise_fc_in_hz` 또는 `noise_out_int_vrms`)와 총면적 `area_search_m2`(S-1) |
| 핵심 층 | graph·계산 블록·kernel·search(S-2). 이 기능은 이 층을 다시 쓰지 않는다. 예외는 N5 승인 항목뿐이다 |
| 파이프라인 층 | `E/pipeline/`(단계 A·B 진입, 결과 기록). S-2의 재작성 범위 |
| 실행(run) | 사용자 호출 한 번. 블록 결과 색인·`RunCounters`의 수명 단위(40 §2.4.5). 이 기능에서는 실행 계획 하나를 끝까지 도는 것이다 |

---

## N1. 목적·범위·요구

### N1.1 목적

지금 spec은 offset을 수단으로 적는다. 랜덤 offset을 면적으로 맞추려면 `offset_in_sigma_mv <=`를 쓰고(`assets/library/current_reuse_telescopic_ota.sizing_spec.json:226`), trim을 쓰려면 승인된 design에서 `offset_trim` 섹션을 쓴다(OT §5.1). 그래서 방식을 바꾸려면 spec의 판정 제약 자체를 바꿔야 하고, 두 방식을 같은 조건으로 비교할 수 없다.

이 기능의 목적은 다음 셋이다.
1. 사용자는 요구(한계·배수·방식)만 쓰고, 방식별 판정 제약은 엔진이 요구에서 유도한다.
2. 방식에 따라 필요한 변형들을 실행 계획 하나로 묶어 한 실행 안에서 돌고, 그 사이에 계산을 공유한다. 사용자 취지 원문은 다음과 같다(사용자 2026-10-15, 원문 `wt/_drafts/user_decisions.md` '실행 사이 재사용 제거').
   > "계산 재사용은 처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용되게 한다는 것이 원래 취지였어"
3. `compare`에서는 두 방식의 결과를 같은 공통 판정 아래 나란히 놓는다. 권고는 하지 않는다(S-3).

### N1.2 범위

| 포함 | 제외 |
|---|---|
| spec `offset_requirement` 스키마와 로더 규칙(N3.2) | 기존 library spec을 요구 형식으로 옮기는 일. 사용자 몫이다(S-1, DS-U5) |
| 방식별 판정 제약 유도 규칙(N3.3), 공통 판정(N3.4) | trim 후보·추천·DAC 규칙 자체. offset-trim 계획·design이 정본이다 |
| 실행 계획(처음 변형 목록과 실행 중 추가, 결정성 = 같은 처음 입력 + 같은 추가 순서·문턱 입력)과 실행기, 단계 A·S0·블록 결과 색인 공유(N3.5, N3.6, N3.12) | 엔진 전체 재작성(S-2). 핵심 층 변경은 N5 승인 항목만 |
| 변형별 예산(N3.7) | 실행 사이 재사용. 이전 실행 결과를 엔진 입력으로 받지 않는다(S-3, 상위 U-89) |
| `compare` 두 국면과 읽기 전용 비교 도구(N3.8) | 엔진이 방식을 골라 주는 권고·자동 선택(S-3) |
| 옛 경로 삭제: OT §4의 `trim_approval_path` 인자 분기, OT §5.2의 D-4 공존 거부(N3.9) | chopper·auto-zero 같은 동적 offset 제거(offset-trim N1.2 제외 그대로) |
| 요구가 없는 spec의 무동작 증거(완료 조건 1) | held-out 회로 확장(상위 U-75 뒤) |

### N1.3 기능 요구

| ID | 요구 |
|---|---|
| FR-S1 | **요구 스키마**(S-1): spec에 선택 섹션 `offset_requirement`를 둔다. 키는 `offset_in_max_v`, `coverage_multiple`, `strategy`이고 값·출처는 사용자 몫이다(N3.2) |
| FR-S2 | **방식별 제약 유도**(S-1): 엔진이 요구에서 변형별 판정 제약을 만든다. 출처는 요구 선언을 참조하고(사본 금지), 유도한 제약은 결과에 출처와 함께 적는다(N3.3) |
| FR-S3 | **공통 판정**(S-1): 1/f 판정과 총면적 판정은 spec 선언 하나를 모든 변형에 똑같이 건다(N3.4) |
| FR-S4 | **실행 계획**(S-2): 결정적 순수 함수가 (spec, 원본 topology, 승인 기록)에서 처음 변형 tuple을 만든다. 실행 중에는 엔진 밖 구동기가 정해진 종류의 변형만 추가한다(N3.12). 같은 처음 입력과 같은 추가 순서·문턱 입력이면 같은 계획이다(N3.5) |
| FR-S5 | **실행기**(S-2): 실행 계획을 한 실행 안에서 차례로 돈다. 단계 A·S0·블록 결과 색인·`RunCounters`를 변형 사이에 공유한다(N3.6) |
| FR-S6 | **변형별 예산**: 변형마다 E_total을 둔다(기본안, N3.7) |
| FR-S7 | **결과 기록**: 결과 JSON에 실행 계획(변형 목록·국면·예산), 변형별 결과, 유도 제약과 출처를 싣는다. `compare`에도 권고 문장은 없다 |
| FR-S8 | **비교 도구**(S-3): 결과 JSON 두 개를 읽어 나란히 놓는 읽기 전용 도구. 엔진을 import하지 않고, 엔진 입력 경로가 없다(N3.8) |
| FR-S9 | **옛 경로 삭제**(S-2): OT §4의 `trim_approval_path` 진입 인자 분기와 OT §5.2의 공존 거부 규칙을 이 기능의 규칙으로 바꾸고, 바뀐 규칙만 남긴다(N3.9) |
| FR-S10 | **무동작**: `offset_requirement`가 없는 spec은 지금과 같은 흐름이다(실행 계획 = 원본 topology와 spec 제약의 변형 하나). 결과는 완료 조건 1(변경 종류 = 순수 리팩터링, 필드별 판정)의 범위에서 base와 같다 |

### N1.4 비기능 요구

상위 계획 N1.4 NFR-1~NFR-6과 N2.2 작업 원칙을 그대로 적용한다. 이 기능에서는 특히 다음을 강제한다.

| ID | 요구 |
|---|---|
| NFR-S1 | **재사용**: 한 실행 안의 모든 변형이 단계 A 결과(같은 topology 변형끼리), S0 수준 블록, 블록 결과 색인(40 §2.4.5)을 공유한다. **같은 입력의 재계산은 실행 전체에서 0**이다(40 §2.4.9 판정 1을 변형 경계를 넘어 적용). 실행 사이 재사용은 없다(상위 U-89, 원래 취지 문장) |
| NFR-S2 | **graph 단일 정본**: 요구 값은 spec 선언 한 곳에만 있다. 유도 제약은 그 선언을 참조하고(`value_from_spec`), 숫자 사본을 만들지 않는다. 실행 계획은 출력·실행 입력이고 graph 필드가 아니다. 새 graph 필드는 writer가 하나다(상위 DEC-83) |
| NFR-S3 | **topology 무관**: 유도 규칙·계획 규칙은 구조와 선언만 읽는다. 회로·소자·넷 이름 리터럴은 금지다. library 13회로(상위 O-182 Q-LB1)에서 요구가 없으면 무동작임을 측정해 증거로 낸다 |
| NFR-S4 | **fail-closed**: 요구와 수단 제약이 함께 있거나, 방식에 필요한 선언이 없거나, 유도 제약을 잴 수 없으면(예: 계통 offset 기준 미선언) 탐색 전에 사유 코드로 멈춘다. 조용한 대체·생략은 금지다 |
| NFR-S5 | **결정성**: 같은 처음 입력과 같은 추가 순서·문턱 입력이면 같은 실행 계획·같은 변형 순서다. 계획 안에서 돈 변형의 결과는 그 변형만 따로 돈 결과와 비트 동일하다. '따로 돈 결과'는 처음 변형이면 그 변형만 담은 계획의 결과이고, 실행 중 추가된 변형이면 새 세션을 열어 처음 변형은 실행하지 않고 같은 문턱 입력으로 그 변형만 추가해 실행한 결과다(N3.12)(범위: E_B를 선언한 실행. 시간 예산에서 E_B를 유도하는 실행은 DS-U9가 정해질 때까지 이 요구에서 빼고 결과에 표기한다 -- 완료 조건 2와 같은 범위). 다를 수 있는 것은 계수·시간 칸(40 §2.4.13 T 부류)뿐이다 |
| NFR-S6 | **상수 발명 금지**: 배수·한계·예산·판정 문턱은 선언이나 정의에서 온다. 비교 도구에 '어느 쪽이 낫다'를 가르는 가중치나 문턱을 두지 않는다 |
| NFR-S7 | **만들면 배선**: 계획 함수·실행기·유도 함수·비교 도구는 진입점의 실제 경로에서 쓰인다. 옛 경로는 같은 변경에서 지운다. 배선이 불가능하면 사용자 승인을 받는다 |
| NFR-S8 | **작성자≠검증자**: design은 독립 검증 agent가 검증한다. test·기대값·판정 기준은 구현자가 소유하지 않는다 |

---

## N2. 확정 결정

| ID | 결정 | 출처 |
|---|---|---|
| S-1 | spec은 수단이 아니라 요구로 쓴다: `offset_requirement{offset_in_max_v, coverage_multiple k, strategy: matching\|trim\|compare}`. 방식별 판정 제약은 엔진이 요구에서 유도한다. matching: k·σ_in + \|V_id*\| ≤ `offset_in_max_v`(V_id* = gain-budget DEC-23 부호 있는 계통 offset 한 칸 -- 결정 당시 기호 V_sys를 정본 기호로 바꿔 적음; 판정 위치는 O-53 A2로 커널·front 둘로 나뉨 -- 아래 O-53 행, N3.3). trim: `trim_range`·`trim_residual`, V_res ≤ `offset_in_max_v`는 로더 검사. 1/f 판정(`noise_fc_in_hz` 또는 `noise_out_int_vrms`)과 총면적 `area_search_m2` 하나를 두 방식 공통으로 둔다. D-4 공존 거부 대체·N을 {N, N+1}로 여는 것·compare 추가는 '원래 취지와 다름'으로 보고됐고 이 계획·design에서 다시 승인받는다 | 사용자 2026-10-16 "권고대로 해"(원문 `wt/_drafts/user_decisions.md` '## offset 방식 선택·실행 계획') |
| S-2 | 아키텍처 = 파이프라인 층 모듈 재작성. 실행 계획 = 변형 목록 (topology 변형, 제약 집합). 단계 A·S0·블록 결과 색인 공유. 옛 `trim_approval_path` 인자 분기 삭제. 핵심(graph·블록·kernel·search)은 유지하고 엔진 전체는 재작성하지 않는다 | 같음 |
| S-3 | compare는 두 국면이다(승인 게이트 유지). 국면 2의 최종 비교는 오케스트레이터 기본안: 엔진은 이전 실행 결과를 입력으로 받지 않는다. 두 결과 JSON을 읽는 읽기 전용 비교 도구(보고만)로 나란히 놓는다. 계산 재사용·엔진 입력 경로는 없다. 사용자가 달리 원하면 바꾼다 | 같음 |
| S-4 | 순서 = NFR-4 card 2 병합 → XRUN-F1 A → B → C → 실행 계획 구현 → trim TR-1. card A 진행 중에 계획 문서와 실측(평가 캐시 키의 제약 의존, matching·trim 1단계 θ 겹침 1회로)을 한다. OT §4(진입 인자 단계 선택) 개정은 실행 계획 design과 함께 재승인한다 | 같음 |

**이어받는 결정**(바꾸지 않는다):

| ID | 내용 | 이 계획에서 쓰는 곳 |
|---|---|---|
| 실행 사이 재사용 제거 | 실행마다 S0를 계산하고 그 실행 안에서만 재사용한다. 원문은 N1.1 인용 | NFR-S1, N3.6, N3.8 |
| U-89 | S3 기록을 실행 사이에 읽지 않는다. S3는 출력이다 | N3.8 비교 도구가 엔진 밖인 이유 |
| X-12 | 블록 결과 색인 수명 = 실행 하나, 단계 A부터 | N3.6 |
| X-17 | E_total = E_B + N_T + R(R = 2 × `len(sctx.domain.variables)`). 선언 40은 그대로 동작하고 판정·test 예산은 바꾸지 않는다 | N3.7 변형별 예산의 근거 |
| T-2, T-7, T-8 | 파생 topology는 사용자 승인 뒤에만 사이징한다. I_u = θ, θ 하나 = 커널 평가 1회, card C 예산 규칙 변경 없음 | N3.5 국면, N3.7 |
| T-15 | `run_trim_candidates` 제품 경로 배선 때문에 TR-2 병합은 OS-2(제품 진입 `run_plan`) 뒤다(상위 v6.38.4 열여섯째 커밋 계획 검증 5 m-2, 옛 'U16 뒤') | N7 순서 |
| T-19~T-23 | 단일 출력 회로의 출력 기준 DC는 '출력 기준 DC' 기능(XRUN-F1 뒤·TR-6 전)이 정한다. (v0.7) 기준의 **정의 자리**는 O-53 B3로 gain-budget DEC-23 하나다(아래 O-53 B3 행). 이 계획은 정의를 두지 않고 인용만 한다 | N3.3 matching 유도의 V_id* 전제 |
| S-5·S-6 | 계획 v0.4의 XS-1~XS-14 승인, DS-U1~DS-U9 결정(권고대로) | N5, N10.1 |
| S-7 | 계획과 다른 부분이 생기면 계획부터 고치고 bkit 절차(계획 개정 → 독립 검증 → 사용자 승인 → design 개정)로 진행한다 | N11 |
| S-8 | PD-1~PD-8 권고대로: PD-1 `derived` 별도 입력, PD-2 승인 로더 TR-3·N-22 배정·OD-3 기간 수용, PD-3 DS-2 '대상 없음'으로 닫음, PD-4 XS-10 범위 서술, PD-5 비교 제외 범위를 넓히지 않음(요구 섹션이 있을 때만 지문에 넣음), PD-6 공통 판정 검사 OS-5, PD-7 B_S0 = 변형 수와 card C `S3Index` 인터페이스 변경 확인, PD-8 `run_stage_a` 필수 키워드와 40 design '전달' 행 개정 확인(사용자 2026-10-16 "PD1~PD8은 권고대로") | N11 |
| S-9 | W-1 (i): `run_plan`을 엔진 사슬 진입점 정본으로 병합하고 하네스·test의 수작업 사슬을 같은 변경에서 대체, U16은 나중에 제품 CLI를 `run_plan`에 배선(사슬 두 벌 방지). (v0.7.2 정정, O-63 (3)) 하네스가 블록 결과 색인의 평가 키 부분 같은 실행 수명 값을 읽어야 하면 `run_plan` 결과가 아니라 같은 세션 인터페이스의 공개 API로 세션이 열린 동안 읽는다(열기 → 변형 실행 → 읽기 → 닫기, N3.12). 결과 객체는 색인·donors·계수 참조를 담지 않는다. 그 세션은 `run_plan`이 쓰는 사슬 그대로라 사슬은 하나다. F-1: OS-2 matching 검증 fixture = library current_reuse_telescopic_ota 사본(library 밖 fixture), offset 제약 둘을 요구로 바꿈 {strategy: matching, coverage_multiple = 3, offset_in_max_v = 3 × 3.3 mV(2026-10-08 Q3 (2)의 3.3 mV 유래, 사용자 승인 값)}, library spec 무변경. T-30 연결: 온도 보정 루프는 offset-trim 계획이 소유하고, 이 계획은 연결점만(사용자 2026-10-16 "W-1,F-1,T-30을 권고대로 진행") | N3.11, N7, N11 |
| S-10 | PD-9 (가): 공존 거부는 판정 제약(상위 SF-1 범위 8의 판정 대상 술어 하나 -- 출처 축: 출처 kind가 `user_spec`(참조는 사슬 끝 대상의 출처 kind를 따름 -- `pending_spice`는 대상 아님), metric 축: metric 결정 대기가 아님; 저장 사본 칸 `judged`는 지움, v0.7.4; 이 검사는 상위 S0 필드 `constraint_classes` 판정 대상 칸을 READS하고 술어를 다시 부르지 않음 -- 검사 자리 = 로더가 아니라 그 S0 블록(제약 분류) 안 -- 판정 대상 칸의 첫 소비자 앞, 상위 N3.3 G1, v0.7.5 둘째 커밋, v0.7.5 상위 v6.38.4 재판정 P1, **원래 취지와 다름**(자리 변경 -- 상위 v6.38.4 승인 대기 P1))만, `pending_spice` offset 항목과 `pending_constraints`는 허용(판정 제약이 되면 같은 블록 안 검사가 거부해 fail-closed 유지). design OB-6 수정은 design v0.2 몫(사용자 2026-10-16 "pd9도 권고대로") | N3.2, N10.1 DS-U2, N11 |
| S-11 | V-1 = OS-V card(선행 OS-2 + oracle-portability 코어, TR-TL 앞 -- v0.7: '오라클 코어' 선행 = OP-3·EO-1·OP-5, VB-1 인용, 감사 D3·D4, N7.1), F-1 fixture 위치 = 저장소 안·library 밖 확인, 계획 v0.5.x 권고대로 승인(사용자 2026-10-16 "offset-strategy 권고대로") | N3.11, N7, N11 |
| O-1 | oracle-portability 계획 승인: 오라클 MC = 시뮬레이터·PDK 네이티브 MC, PC-4 삭제, 크기 확인 = TR-7의 엔진 σ 대 오라클 MC σ 비교 | N7.2 OS-V |
| T-35 | offset-trim D-24 안 B: 보정 루프 반복 = 같은 실행 안 변형(같은 topology + 문턱만 다른 제약 집합), 단계 A·S0·블록 결과 색인 공유, 오라클 별도 프로세스, 엔진 밖 구동기가 실행 계획을 유지하고 다음 변형을 추가. 같은 결정에서 D-19 반복 상한 = 실행 설정(기본값 없음). D-20·D-25는 대기 | N3.11, N3.12, N7.2 OS-L |
| T-29~T-33 | offset·trim 잔여 합격 = SPICE 오라클 온도 범위 판정(T-29), SPICE 온도 보정 루프(T-30, offset-trim 계획 보완, 순서 TR-7 뒤), 공정 무관 방법론(T-31), 처음 범위 = offset·trim 잔여(T-32), 오라클 시뮬레이터 무관(T-33) | N3.11 |
| O-34 (1) | 변경 종류별 판정 기준(결정성 = 비트 동일·항상, 순수 리팩터링 = 필드별, 동작 변경 = 정의 손계산 toy + 봉인 불변식 + SPICE oracle 대조 + 검증자 변화표). 정본 = gain-budget N6.3 '변경 종류별 판정 기준'(인용만) | 완료 조건 머리·1·2·9·10, N7.2 OS-2·OS-V 행 |
| O-43 D1 (c)·O-45 U3·O-46 (1)·O-47·O-50 G1 | 계통 offset 정본 = 부호 있는 V_id* 한 칸 = 상위 DEC-23 일반형 (나′) 세 성분 합('1차' 표기; \|A_dc\| ≤ 판정 분해능이면 정의 불능 -- O-62 (3)·O-63 (1)), 판정 자리 = 커널(판정 W = θ 유도 W라 성분 (3) = 0, 성분 (1)(2)로 판정) + front 판정 W(단위 9 전 sizing W·뒤 실현 W) 재판정(성분 (3)을 더함), 위반 점 front 제외 후 비지배 재필터(상위 DEC-74·U-108·O-118 1번·O-119 인용 -- v0.7.4). 정의 정본 = gain-budget DEC-23, 판정 위치 정본 = 상위 DEC-74·U-108(커널 + front 판정 W 재판정, 인용만) | N3.3, N3.11, N8 |
| O-53 A2 | **matching 합성 제약의 판정 위치**(사용자 2026-10-20 "권고대로 진행해", `wt/_drafts/user_decisions.md` O-53 행): 커널에서 k·σ_in ≤ `offset_in_max_v`, front에서 k·σ_in + \|V_id*\| ≤ `offset_in_max_v`를 ΔW 1차 값으로 재판정, 단위 9 뒤 실현 W로 재판정, 위반 점은 front에서 빼고 비지배 재필터. trim 방식은 offset-trim의 보정 구간(O-53 A3)으로 판정. 원래 취지와 다름 승인(S-1 판정 위치 분리) -- N5 XS-20 | N3.3, N3.6, N3.10, N3.11, N10.3 G-S1·G-S2, 완료 조건 10 |
| O-53 B3 | offset 기준 정의 자리 = gain-budget DEC-23 하나. spec 선언 기준 종류 셋(값 = 선언 목표 전압, 넷 = 출력이 다른 넷과 같아야 함, 입력 추종 = 출력이 입력 CM을 따름) + 차동 출력 V(p) − V(n) = 0 기본, 선언 없는 단일 출력은 정의 불능(추론 금지). PC-10 = oracle-portability OP-5 `offset_sys_mv` `.dc` 측정을 온도 조건에서 돌린 것 하나(공칭 MC 표본 offset은 V_id* 출처가 아님 -- O-53 B3 원문을 v0.7.2에서 이 행에 옮겨 적음) | N3.3, N4-3, N7.1, N7.2 OS-V, N9 |
| O-63 (3) | **W-1 노출 자리**(사용자 2026-10-21 AskUserQuestion "(권고)", `wt/_drafts/user_decisions.md` O-63 행 (3)): 하네스는 세션이 열린 동안 공개 세션 API로 블록 결과 색인의 평가 키 부분을 읽는다(열기 → 변형 실행 → 읽기 → 닫기). `run_plan` 결과·변형 결과 등 결과 객체에는 색인·donors·계수 참조를 두지 않는다. 닫기 = 버린다(N3.12 ④·'수명', graph 규칙 2 실행 수명). `run_plan`은 얇은 진입 그대로이고, 평가 목록이 필요한 하네스가 세션 API를 써도 사슬은 하나다(W-1 '사슬 두 벌 금지') | S-9, N3.6, N3.12, N7.2 OS-2·OS-L·'v0.5 반영' W-1 |
| O-258 (v0.8) | offset MC 시점 + trim 구성(사용자 "동의해", 2026-11-07, `wt/_drafts/user_decisions.md` O-258 행). 이 계획 몫: (B) '원래 topology 불변, trim 파일 두 선언 합성(로더 블록 하나)' → topology 변형 = 원본 또는 합성 회로; 'trim 부담 = 같은 θ에서 원본만 변형 대 원본 + trim(중간 코드) 변형 차(offset-strategy 실행 계획 변형 틀)', '부담 위반이면 원본 θ까지 합성 회로 기준 재풀이' → 변형 O·C·C′와 고정 θ 성분(XS-21), 실행 중 추가 허용 종류(XS-22). trim 규칙 정본은 offset-trim v0.7(N3.3·N3.10·N3.11) | N0.1, N3.3, N3.5, N3.6, N3.8, N3.12, N5, N7.2 |
| O-44 (1)·O-45 U1 | 엔진 점 → oracle 입력 생산자·판정 배선 = gain-budget card EO-1(N6.20). 모든 동작 변경 card의 SPICE 다리는 EO-1을 **완료 판정 선행**으로 둔다(병합 선행 아님, gain-budget N6.3 (iii)·(iv)) | N7.2 OS-2·OS-V·OS-L 행, 완료 조건 10 |

---

## N3. 엔진 반영 구조

### N3.0 현황 사실(읽기 확인, base `067614c`)

| ID | 사실 | 근거 |
|---|---|---|
| F-1 | **평가 캐시 키에 제약 집합이 들어가지 않는다.** 평가 키 `EvalKey` = (`context_fp`, `schema_fp`, `cells`, `w_fixed_fp`, θ 값 hex)다. `context_fp` = (`_CONTEXT_WRITERS`의 블록 입력 버전, LUT 손잡이, `DcInputs`) 지문이고, `_CONTEXT_WRITERS` = S1 블록 ∪ 커널 계획 블록(`PLAN_WRITERS`)이다. 제약을 담는 S0 블록 `constraint_classes`와 S1v 블록 `build_s1v`는 여기에 없다. `DcInputs` 칸(레일·입력 DC·노드 목표·원소 값·선형 영역·결정 대기·engine 원소)에도 제약이 없다 | `E/search/eval_key.py:13-22`, `E/search/search_context.py:45-46, :188, :211`, `E/sizing/kernel_context.py:47-48`, `E/sizing/s2_values.py:187-200` |
| F-2 | **평가 결과는 제약 집합에 의존한다.** 커널은 평가 안에서 제약 행을 만든다(`rows = seal_rows + _spec_rows + ss_rows + ls_rows`). `_spec_rows`는 `sctx.judged_constraints`(목적 축 제약)를 읽고, `ss_constraint_rows`는 `sctx.ss_constraints`를 읽는다. 어떤 metric을 계산할지도 제약이 정한다: `ss_evaluate`가 `sctx.ss_constraints`에서 요청 목록을 만들고, 그 목록이 `metrics_ss`·`metrics_aux` 블록의 extras(입력 버전)에 들어간다. 이 행을 담은 `EvalResult`가 그대로 캐시에 들어간다 | `E/search/kernel.py:49-56, :130-133, :146-151, :159-161`, `E/metrics/ss_evaluate.py:50-57, :90-93, :98, :103`, `E/metrics/ss_metrics.py:377-379`, `E/metrics/metrics_aux.py:157-159` |
| F-3 | **S1v 블록 입력에 제약 tuple 전체가 들어간다.** 단계 A가 spec 객체를 `build_s1v`에 넘기고(`stage_a.py:225-227`), `build_s1v`가 판정 제약 tuple을 만들어(`s1v_build.py:39`) 블록 `s1v_fields`의 extras로 넘긴다. 안정도 제약의 루프 뷰 끊는 넷도 spec 제약에서 온다(`_declared_loop_cuts`, `stage_a.py:152-160`). 그래서 제약 집합이 다르면 같은 topology라도 S1v 블록의 입력 버전이 다르다 | `E/pipeline/stage_a.py:152-160, :225-227`, `E/graph/s1v_build.py:39-42`, `E/graph/s1v_fields.py:249-251` |
| F-3a | **S1v 값도 제약 집합에 따라 달라질 수 있다.** 전달 뷰 씨앗은 판정 제약의 `view` 선언(port·loop·transfer·ratio)에서 만들고, 선언이 하나도 없을 때만 기본 뷰를 쓴다. offset metric 셋은 transfer 뷰 metric이다. 그래서 view를 선언한 offset 제약이 빠지거나 더해지면 뷰 집합이 바뀔 수 있다 | `E/graph/views.py:51-63, :77-78`, `E/metrics/registry.py:56-58` |
| F-4 | **spec을 읽는 S0 경로**: 단계 B의 면적 예산과 달성 가능성 블록(`achievability(graph, spec, …)`), 탐색 컨텍스트의 θ 상자(면적 예산), 제약 분류, 출발 구간(`start_intervals(base, spec, …)`), `ss_constraints`(spec 제약을 위치로 고름), 잡음·mismatch LUT 데이터 필수 검사 | `E/pipeline/stage_b.py:153, :168`, `E/search/search_context.py:110-113, :156-168, :171-196`(출발 구간 :195) |
| F-5 | 실행 수명 상태(평가 캐시 `cache`, `computed_keys`, 계수, `eval_budget`, `deadline`)는 `SearchContext` 객체 하나에 있다. S3 기록기는 `S3Archive(root, context_fp, code_fp)`다. **XRUN-F1 card B와 상위 LA-1(범위 15 (iv)) 뒤에는**(상위 N6.1 병합 순서 규칙 표 #8; 옛 '먼저 병합되는 card 뒤') `sctx.cache`·`computed_keys`가 S3 메모리 색인(`search/s3_index.py`의 `S3Index`) 하나로 바뀌고, 블록 결과 색인(`find`·`register`)은 그 색인의 한 부분이다(평가 키 조회 `get`·`failure`와 같은 객체) | `E/search/search_context.py:53-69, :212`, 40 §2.4.5(평가 키·블록 결과 색인 API) |
| F-6 | `find_front`는 호출마다 벽시계 정지 시각을 정하고, 판정 metric의 검증 출처를 `sctx.ss_constraints`·`sctx.judged_constraints`에서 모은다 | `E/search/find_front.py:75-78, :94` |
| F-7 | 진입점 서명은 `run_stage_a(topology_path, spec_path, lut, *, output_dir, supplies_v=None, structure_path=None)`, `run_stage_b(stage_a, memo, pdk_decl, *, output_dir, settings, diagnostic=False)`다. 엔진 코드에 'trim'은 없다. `trim_approval_path`는 OT §4 design에만 있다 | `E/pipeline/stage_a.py:195`, `E/pipeline/stage_b.py:134`, grep 2026-10-16 |
| F-8 | XRUN-F1 card A·B·C는 base에 병합되지 않았다. 블록 결과 색인(`search/s3_index.py`)·`search_ceiling.py`·`search_stop.py`는 아직 없다. 색인 수명·상한·E_total 규칙은 design(40 §2.4.5, §2.4.9, §2.4.14)이다 | `ls E/search/` 2026-10-16 |
| F-9 | library에서 `offset_in_sigma_mv` 판정 제약을 가진 spec은 하나다. `offset_excess`는 6개 spec에 있다 | `assets/library/current_reuse_telescopic_ota.sizing_spec.json:226`, `folded_cascode…:49`, `ngcc_3stage_ff…:111`, `nmcnr_amplifier…:141`, `sf_pushpull_output_opamp…:131`, `two_stage_ota…:81`, `two_stage_ota_sf…:82` |
| F-10 | 1/f·면적 metric은 레지스트리에 있다: `noise_fc_in_hz`, `noise_out_int_vrms`, `area_search_m2`. offset metric은 `offset_in_sigma_mv`·`offset_excess`(`OffsetAnalysis`), `offset_sys_mv`(`OffsetSystematic`)다 | `E/metrics/registry.py:49, :52, :54, :56-58` |
| F-11 | 승인된 trim design은 2단계 실행에서 S0를 두 벌(원본·파생) 계산하므로 색인 상한을 Σ 분할 수 × (E_total + 2)로 둔다 | OT §10.1 |
| F-12 | **제약을 읽는 핵심 층 지점**: `SearchContext.ss_constraints`는 `constraint_classes`의 위치 index로 `self.spec.judged_constraints`를 고른다. 출발값 규칙은 `spec.judged_constraints`에서 (metric, op, 값) 목록을 만들고, `iv_matching_l`은 그 목록에서 이름 `offset_in_sigma_mv`(L 하한)·`offset_excess`(부하 가드)를 찾는다. `judged_constraints`는 `SizingSpecDoc.constraints`에서 뽑는 속성이고, spec 객체는 `spec_fp`·`section_fps` 지문을 칸으로 들고 있다 | `E/search/search_context.py:110-113`, `E/search/iv_context.py:89`, `E/search/iv_matching_l.py:40-41, :107-108`, `E/search/start_intervals.py:295, :332`, `E/authoring/spec_model.py:280-281, :287-290` |
| F-13 | **base에서 나오는 측정 칸**: S3 evals 한 줄 = `seq`, `schema_fp`, `cells`, `w_fixed_fp`, `theta_hex`, `theta`, `status`, `ok`, `origin`, (`fail`), (`objectives`), `constraints`, `unmeasured`, (`power_resolution_w`), (`snapshot_fp`), (`block_residual`)에 기록기가 덧붙이는 `code_fp`이다(`kernel.py:85-87`, `archive.py:53`). **평가별 시간 칸은 없다**. S3 폴더 이름이 `context_fp`다. `find_front` 결과 `perf`는 실행 합계(계수, `unique_keys`, `eval_time_median_s`, `wall_s`, `block_calls`·`block_reuses`·`block_computes`·`block_recomputes_same_input` 합계)이고 블록별 수는 없다 | `E/search/kernel.py:68-88`, `E/search/archive.py:42-43`, `E/search/find_front.py:127-133` |

### N3.1 M1 결과와 그 뜻

M1(평가 캐시 키에 제약 집합이 들어가는가)은 **들어가지 않는다**(F-1). 반면 평가 결과는 제약 집합에 의존한다(F-2). 이것이 이 계획에 주는 뜻은 다음과 같다.

1. **같은 topology 변형끼리 평가 캐시를 그대로 공유하면 틀린다.** matching 변형과 trim 국면 1 변형은 원본 topology가 같아 `context_fp`가 같다. 한 `SearchContext`의 캐시를 함께 쓰면, 한 변형의 제약 행을 담은 `EvalResult`가 다른 변형에 적중으로 돌아간다. 처리 선택지는 셋이다(DS-1, 아래 표).
2. **블록 결과 색인은 공유해도 맞다.** 색인 키는 (블록, 분할, 입력 버전)이고 블록은 투영만의 순수 함수다(40 §2.4.5 '결정성'). 그래서 변형이 달라도 입력이 같은 블록은 적중하고 결과는 비트 동일하다.
3. **다만 공유 범위가 제약 쪽에서 끊긴다.** metric 블록은 요청 목록이 extras에 들어가므로(F-2), 두 변형의 요청 목록이 다르면 같은 θ라도 다른 입력이다. S1v 블록도 제약 tuple 전체가 extras라서(F-3) 같은 topology여도 변형마다 한 번씩 계산된다. 이것은 입력 지문이 달라서 생기는 계산이라 40 §2.4.9 판정 1('같은 입력 재계산 0')을 형식상 깨지는 않는다. **그 결과 값이 같은지는 정해져 있지 않다**: 뷰는 제약의 view 선언에서 만들어지므로(F-3a) 변형 제약 집합에 view를 선언한 제약이 다르면 S1v 값도 다르다(이때는 재계산이 맞다). view 선언이 같으면 값이 같은데도 다시 계산하는 것이어서 원래 취지('그 계산된 값이 나머지 최적화를 진행할 때 재사용')와 거리가 있다. 어느 쪽인지는 유도 제약의 view 출처(G-S1)와 변형별 view 선언 집합으로 정해진다. (v0.5: design이 유도 제약을 S1v 밖 별도 입력으로 두어(PD-1) 같은 topology 변형끼리 S1v 입력이 같아졌고, DS-2는 '대상 없음'으로 닫혔다(PD-3, S-8). metric 블록 요청 목록이 다른 몫은 그대로 DS-1의 대상이다.)
4. **'평가 = 크기·metric(제약 무관) + 판정(변형별)' 분리는 범위를 kernel까지 넓힌다.** 분리하려면 (i) 커널이 계획 안 모든 변형의 metric 요청 합집합을 한 번에 계산하고(`kernel.py:130`의 요청 출처 변경), (ii) 캐시 값에서 제약 행을 빼서 변형별 판정 단계로 옮기고(`kernel.py:146-151, :159-161`), (iii) S1v 투영을 뷰 선언·루프 끊는 넷으로 좁혀야 한다(`s1v_fields.py:249-251`, graph 층). 셋 다 S-2 '핵심 유지' 밖이다. 그래서 **결정 항목 DS-1**로 둔다(N5 XS-5, N10).

**DS-1 선택지와 완료 조건 3**(완료 조건 3 = 실행 계획 전체에서 같은 입력의 블록 재계산 0, 같은 평가 키 재계산 0. 이 조건은 약화하지 않는다). 이 기능은 XRUN-F1 card B 뒤에 구현되므로 선택지는 **card B 뒤 구조**로 쓴다: 평가 캐시와 블록 결과 색인은 S3 메모리 색인 `S3Index` 한 객체의 두 부분이다(평가 키 조회 `get`·`failure`, 블록 결과 `find`·`register`, F-5, 40 §2.4.5).

| 선택지 | 내용 | 바뀌는 층 | 블록 재계산 0 | 같은 평가 키 재계산 0 | 원래 취지와의 관계 |
|---|---|---|---|---|---|
| (가) 평가 키 부분만 변형별 | 변형마다 평가 키 부분(`get`·`failure`)을 따로 두고, 블록 결과 부분(`find`·`register`)만 실행 계획 전체에서 공유한다. 키는 지금 그대로다. `S3Index`가 한 객체이므로 두 부분의 수명을 가르는 변경이 `search/s3_index.py`에 필요하다(card B 전 구조라면 변형별 `SearchContext`만으로 되지만, 구현 시점은 card B 뒤다) | search(`S3Index` 수명 분리) + pipeline | 지킨다(블록 결과 부분 공유) | **모순**. 같은 topology 변형은 `context_fp`가 같으므로(F-1) 두 변형이 같은 θ를 밟으면 **같은 평가 키**가 실행 안에서 두 번 계산된다 | 같은 실행 안에서 변형 사이의 커널 평가 재계산을 받아들인다(XS-8). card B 뒤에는 핵심 층(search)도 바뀐다(XS-5) |
| (나) 평가 분리 | 커널이 계획 안 모든 변형의 metric 요청 합집합을 한 번 계산하고, 평가 키 부분의 값은 제약 무관이다. 판정 행은 변형별 단계가 만든다. `S3Index` 하나를 실행 계획 전체에서 공유한다. S1v 투영을 좁히는 것(DS-2 (나))과 같이 간다 | kernel·`ss_evaluate` 호출(search·metrics), graph(S1v) | 지킨다 | 지킨다(같은 θ는 실행 안에서 한 번 평가) | 재사용 취지는 맞는다. 대신 S-2 '핵심 유지'와 다르다(XS-5) |
| (다) 키 분리 | 평가 키(또는 `context_fp`)에 변형 제약 집합 지문을 넣는다. `S3Index` 하나를 실행 계획 전체에서 공유한다 | search(`eval_key`·`context_fp`) | 지킨다 | 형식상 지킨다(변형마다 키가 다르다). 실제로는 같은 θ가 변형마다 커널을 한 번씩 거치고, 크기 결정 블록은 블록 결과 적중, 요청이 다른 metric 블록은 다시 계산된다 | 같은 값의 계산이 변형 사이에서 남는다(XS-8). 핵심 층(search) 변경이다(XS-5) |

* (가)를 고르고 완료 조건 3을 '변형 안 0 + 변형 사이 수는 보고'로 바꾸는 것은 **기준 약화**다. 사용자 승인 없이는 하지 않는다(N10 DS-U7).
* 결정됨(O-176 Ⅵ: (나) + 조건 2개, N10.1 DS-1 -- 옛 S-14 (다) 번복). 옛 'M2 숫자와 함께 받는다'는 v0.7.5 백로그 재감사 OS-B4로 지웠다(M2 측정의 소비처 없음).

### N3.2 요구 스키마 `offset_requirement`(TR-1과 함께 로더 확장)

spec 사람 선언의 선택 섹션이다. 형식은 기존 spec 값 칸(`value` + `source`, 출처 kind는 `user_spec`만)을 따른다. 정확한 스키마·사유 코드 이름은 design(OS-0)이 DEC-68 명명 규칙으로 정한다.

| 키 | 뜻 | 형식 검사 |
|---|---|---|
| `offset_in_max_v` | 입력 환산 offset 한계(V). matching에서는 커널 판정 k·σ_in과 front 판정 k·σ_in + \|V_id*\|의 상한(O-53 A2), trim에서는 V_res의 상한(N3.3) | 유한 양수 |
| `coverage_multiple` | k. 랜덤 offset 분포 σ_in의 배수. matching 상한과 trim 보정 구간이 같은 k를 쓴다 | 유한 양수 |
| `strategy` | `matching` \| `trim` \| `compare` | 닫힌 어휘 |
| 판정 온도 범위(칸 이름은 design이 DEC-68로 정한다. 후보 `judgment_temperature_range_c` = {하한, 상한}) | offset·trim 잔여 합격을 판정할 온도 구간(°C, 단위 접미 `_c`, OT §5.1 선례). spec에 이 한 곳에만 선언하고, TR-7 온도 보고 sweep과 SPICE 온도 보정 루프의 범위 판정이 모두 이 선언을 참조한다(바꾸면 연동, 숫자 사본 금지, T-34). 값은 사용자 선언이고(T-34의 결정 값은 T-14 범위) 기본값은 없다 | 두 값 모두 유한, 하한 < 상한. 출처 kind `user_spec`. trim 온도 T_j가 구간 안에 드는지의 검사는 offset-trim 소관(O-8)이다 |

**로더 규칙**(fail-closed, NFR-S4):

| 상황 | 처리(기본안) |
|---|---|
| 요구와 수단 제약(`offset_in_sigma_mv`·`offset_sys_mv`·`offset_excess`의 판정 제약)이 같은 spec에 있음 | 거부. 사유 코드는 design이 정한다. **범위(PD-9 승인, S-10)**: 판정 제약(상위 SF-1 범위 8의 판정 대상 술어 하나 -- 출처 축: 출처 kind가 `user_spec`(참조는 사슬 끝 대상의 출처 kind를 따름 -- `pending_spice`는 대상 아님), metric 축: metric 결정 대기가 아님; 저장 사본 칸 `judged`는 지움, v0.7.4; 이 검사는 상위 S0 필드 `constraint_classes` 판정 대상 칸 READS, 자리 = 그 S0 블록(제약 분류) 안 거부(첫 소비자 앞) -- v0.7.5)만 거부한다. 판정 제약이 아닌 `pending_spice` offset 항목과 `pending_constraints`(값 없는 이름 목록)는 허용한다. 그 항목이 판정 제약이 되는 순간 같은 검사(제약 분류 블록 안 거부)가 거부하므로 fail-closed는 유지된다(design OB-6의 '출처 kind와 무관하게 전부 거부'는 design v0.2에서 이 범위로 고친다). 한 spec에 offset 판정의 출처가 둘이면 어느 쪽이 판정인지 모호하다(단일 정본). 이 규칙은 OT §5.2(D-4: `offset_in_sigma_mv`만 거부, 나머지는 보고로 내림)를 대체한다(XS-1). `offset_excess`를 matching에서 구조 가드로 남길지는 DS-U1, 거부 범위는 DS-U2 |
| `strategy`가 `trim`·`compare`인데 `offset_trim` 섹션이 없음 | 거부(trim 선언 값 V_res·온도가 없다) |
| `strategy`가 `matching`인데 `offset_trim` 섹션이 있음 | 거부(쓰이지 않는 선언이 조용히 무동작이 되지 않게) |
| `offset_trim` 섹션은 있는데 `offset_requirement`가 없음 | 거부(사유 후보 `offset_trim_without_requirement`, 이름은 design). 이유: 이 기능 뒤 trim은 방식(`strategy`)의 한 값이고, k와 한계(`offset_in_max_v`)는 요구에만 있다(XS-6). 요구 없이 trim 선언만 있으면 k가 없어 보정 구간 제약을 유도할 수 없다. OT §5.1(요구 없이 `offset_trim` 단독)과 T-27·T-28 시험 회로 spec에 영향이 있다(XS-9) |
| `offset_trim.residual_offset_v`(V_res) > `offset_in_max_v` | 거부(S-1 로더 검사) |
| k의 출처 | 요구의 `coverage_multiple` 하나다. OT §5.1의 `offset_trim.coverage_multiple`은 두 번째 출처가 되므로 없앤다(XS-6, DS-U3) |
| 요구 섹션이 결정 대기 | 요구 없음과 같다(지금 흐름). 대기 표지는 기존 수집 경로로 보고 |

### N3.3 방식별 판정 제약 유도

유도 제약은 변형의 제약 집합에 spec 판정 제약과 함께 들어간다. 값은 요구 선언을 참조하고(`value_from_spec` 계열), 숫자를 복사하지 않는다(NFR-S2).

| 방식·국면 | 유도 제약 | 근거·전제 |
|---|---|---|
| matching | 식은 k·σ_in + \|V_id*\| ≤ `offset_in_max_v`(S-1) 하나이고, **판정 자리는 둘이다**(상위 DEC-74·U-108·O-119 -- 같은 정의를 다른 판정 W로 두 점에서 잼, 둘째 생산자 아님; v0.7.4):<br>① **커널 판정**: k·σ_in + \|V_id*\| ≤ `offset_in_max_v` -- 커널 점은 판정 W = θ 유도 W라 V_id*는 상위 DEC-23 (나′) 성분 (1)(2)(성분 (3) = 0). σ_in = `offset_in_sigma_mv`(F-10, 정의 gain-budget DEC-23·N3.8 '미스매치'). 평가 커널의 제약 행이다(DEC-74). (v0.7.3 검증 M1, 정렬이고 새 결정 아님 -- DEC-23·O-62 (3)·O-63 (1)) σ_in이 DEC-23 'A_dc 정의 불능 갈래'로 정의 불능이면 커널 행도 fail-closed로 그 점을 거르고, 원인은 갈래 사유 기록의 참조로 남긴다(offset 위반 아님, 사유 사본 없음). 커널 행 형식(G-S1)이 design 몫이라 그 기록 자리가 정해지지 않으면 PS-1 잔여와 같이 올린다(N7.1).<br>② **front 재판정**: 같은 식을 판정 W(단위 9 전 sizing W, 뒤 실현 W)로 -- V_id* = 부호 있는 계통 offset 한 칸 = 상위 DEC-23 일반형 (나′) 세 성분 합(인용, '1차' 표기; \|A_dc\| ≤ 판정 분해능이면 정의 불능 -- O-63 (1); 성분 (3) ΔW 1차 감도가 판정 W에서 더해짐). 판정 W = 단위 9 전 sizing W, 단위 9 뒤 실현 W로 다시 판정한다. 위반 점은 fail-closed로 front에서 빼고 비지배 재필터를 다시 돈 뒤 기록한다. **정의 불능 점**(v0.7.3): σ_in 또는 V_id*가 정의 불능인 점 -- DEC-23 'A_dc 정의 불능 갈래'(ΔW와 무관, O-62 (3)·O-63 (1)), 커널 출발 창 미수렴으로 front 값이 정의 불능인 점(O-64 (2) -- 그 규칙의 '선언 제약이 걸린 값'에 matching 유도 합성 제약이 들어간다) -- 도 fail-closed로 front에서 빼고 비지배 재필터를 다시 돌리되, 원인은 그 정의 불능 사유 기록의 참조로 남긴다(사유 사본 없음 -- graph 규칙 4, O-62 (2) P10 'reason 사본은 삭제'; offset 위반으로 적지 않는다 -- 원인 오귀속 금지; 정본 gain-budget v6.23 병합 `294bde4d`의 DEC-23 'front 판정'·DEC-74·'DE-1 후속 정정 표' offset-strategy 행, 인용만). 갈래 판정 자리는 gain-budget card DE-1 (c)가 고치는 A_dc 계산 자리 하나이고(DEC-23 '엔진 소비자', 이름은 착수 실측) 이 판정은 그 결과를 읽기만 한다(둘째 검사 없음, graph 규칙 1). 판정 자리는 상위 DEC-74·U-108의 커널·front 재판정 두 자리이고 새 자리를 만들지 않는다.<br>두 판정의 문턱은 같은 문턱 항목 하나다(요구 `offset_in_max_v` 참조, 보정 루프에서는 조인 문턱 항목, N3.11). σ_in은 mV, 한계는 V라서 단위 환산 규칙과 유도 제약의 view 출처가 필요하다(G-S1) | S-1, O-53 A2. 커널 행의 형식(k를 입력으로 받는 metric인가 제약 행인가)은 design G-S1이다. V_id*는 offset 기준이 있어야 정의된다. 기준의 정의 자리는 DEC-23 하나다(O-53 B3: spec 선언 기준 종류 셋 + 차동 출력 V(p) − V(n) = 0 기본, 선언 없는 단일 출력은 `reference_undeclared` 정의 불능). 기준이 정의되지 않는 회로는 탐색 전에 멈춘다(fail-closed, N4-3) |
| matching의 출발값 | `iv_matching_l` L 하한은 지금 `offset_in_sigma_mv <=`가 있을 때만 켜진다(offset-trim 계획 F-4). 이 matching 출발값의 **규칙 정본은 gain-budget N3.9 LR6**(gain-budget v6.38.2 개정 -- DEC-105 (6), 사용자 결정 2026-10-14 Q-N2 B: 절대 offset 면적 조건은 L 하한이 아니라 다른 경계가 정한 L에서의 입력 gm/ID 하한, 절대 offset 제약이 있는 회로에서만, A_eff로 계산 -- design 41 §6.4-2; 옛 인용 '하한은 mismatch 임계값')이다. 이 계획은 새 L 규칙을 두지 않고, LR6이 읽는 σ 목표의 **출처**만 정한다: 요구가 있으면 ① 커널 판정 k·σ_in ≤ 문턱이 절대 σ 제약이다(σ 목표 = 커널 판정 문턱(루프에서는 조인 문턱 항목) / k, 사본 없이 그 문턱 항목 참조 -- gain-budget LR6 문언과 같은 뜻). 판정은 바뀌지 않는다(출발값 전용). LR6의 소비자는 둘이고 같은 구현 하나를 쓴다: 출발 구간 `iv_matching_l`(층 0 무동작 회로·조립 실패 경로의 출발점)과 LA-1 층 0 역산 조립의 L 단계(LR5 격자가 LR6 경계에서 멈춤, gain-budget N3.9 LR5; 상위 사용자 결정 O-214·O-217·O-218: 층 0 출발점 L 칸 = DEC-105 (1) 이득 L 하한(오름차순 첫 bin 최소 L) -- 상위 card LA-1a가 근 찾기 핵심 함수를 만들고 LA-1 조립이 같은 함수를 부름(실패 분기는 호출 card 몫), 같은 LR6 구현을 읽음) -- C2 판단 근거는 history H1 'v0.7' | design G-S2, gain-budget LR6 |
| trim 국면 1 | 랜덤 offset 판정 제약을 두지 않는다(σ_in은 trim 필요 판단 값으로 보고한다). (v0.8, O-258) 엔진 출력은 후보표(주입 쌍·t·극성 headroom·잡음·trim 필요 판단 값 -- offset-trim FR-T2)이고 추천 N·m·파생 topology는 없다. 입력 k·V_res는 요구·`offset_trim`에서 읽는다 | offset-trim FR-T2, S-1 |
| trim 국면 2 | 변형 O(원본): spec 제약만. 변형 C·C′(합성 회로): `trim_range`(보정 구간이 [−k·σ_MC, +k·σ_MC]를 덮음 -- σ_MC = spec 승인 선언, v0.8)·`trim_residual`(Δ_max/2 ≤ V_res)·`trim_states_saturation`, 변형 C는 여기에 부담 제약(offset-trim N3.11 -- 문턱 = 변형 O 선택 점 metric 기록 참조 ∓ spec 부담 예산) | OT §10.6. V_res ≤ `offset_in_max_v`는 로더가 이미 확인했다(N3.2). (v0.7) trim 방식의 offset 판정은 offset-trim의 보정 구간 판정이다(O-53 A2 끝 문장·A3: 보정 구간·끝 코드 포화 = 봉인점 1차 감도 추정, 정확값 오라클 `.dc` 코드 스윕). 보정 구간의 정의·계통 offset 몫(\|V_id*\|)의 판정 자리는 offset-trim 계획 v0.6(`plan/offset-trim-v06` `23e6a142`)이 정본이고 이 계획은 인용만 한다. (v0.8) 덮을 분포 σ_MC·부담 정의도 offset-trim v0.7(N3.4·N3.10·N3.11)이 정본이다 |
| compare | matching 변형과 trim 변형 각각의 제약. 두 방식에 같은 k·같은 공통 판정을 쓴다 | S-1, N3.8 |

### N3.4 공통 판정

* 1/f 판정(`noise_fc_in_hz` 또는 `noise_out_int_vrms`, 사용자가 spec에 선언한 것)과 총면적 `area_search_m2 <=`는 spec 판정 제약 그대로 **모든 변형에 똑같이** 들어간다. 엔진은 값을 만들지 않는다.
* trim 변형의 면적·잡음에는 DAC 소자가 자동으로 들어간다(offset-trim N3.6). 그래서 같은 면적 상한과 같은 1/f 판정이 두 방식의 대가(입력쌍 면적 대 DAC 면적, 작은 입력쌍의 1/f 증가)를 같은 기준으로 드러낸다. offset trim은 1/f와 drift를 보정하지 않는다(N8 R1·R2).
* `compare`에서 1/f 판정이나 면적 상한이 없으면 두 결과를 같은 기준으로 놓을 수 없다. 기본안은 탐색 전 거부다(DS-U4). 이 검사의 구현 card는 OS-5다(**PD-6 승인, S-8**. compare를 거부하는 OS-2에서는 쓰는 곳이 없다). `matching`·`trim` 단독은 지금처럼 선언된 것만 판정한다.

### N3.5 실행 계획

**함수**: `build_run_plan(spec, topology, approvals) -> RunPlan`(이름은 design). 결정적 순수 함수이고 파일을 쓰지 않는다. 이 함수가 만드는 것은 **처음 변형 목록**이다. 실행 중에는 엔진 밖 구동기가 정해진 종류의 변형만 더할 수 있다(N3.12, v0.6). 그 밖의 방법으로 목록이 바뀌는 길은 없다. `approvals`는 정해진 위치(OT §8.1 `<circuit>.trim.json`, structure.json과 같은 규칙)에서 로더가 읽은 승인 기록이다(v0.8: 승인 기록은 승인된 trim 파일을 가리키고, 합성 회로는 offset-trim N3.3 합성 로더 블록이 만든다 -- 계획 함수는 합성하지 않고 그 블록의 출력을 topology 변형으로 받는다). 국면은 **승인 기록 유무로** 정한다. 진입 인자로 단계를 고르는 분기는 두지 않는다(S-2, N3.9).

| 요구 `strategy` | 승인 기록 | 변형 목록(순서대로) |
|---|---|---|
| 요구 없음 | -- | (원본 topology, spec 제약). 지금 흐름 그대로(FR-S10) |
| `matching` | -- | (원본, spec 제약 + matching 유도 제약) |
| `trim` | 없음(국면 1) | (원본, spec 제약 + trim 국면 1 규칙). 출력 = 후보표(offset-trim FR-T2). (v0.8, O-258) 옛 '추천 구성 {N, N+1}의 파생 topology와 connectivity 표, 승인 초안(OT §9.5 + XS-2)'은 없다 -- trim 사양 기록·trim 파일 제안·합성 회로 connectivity 표는 엔진 밖·승인 단계(offset-trim N3.1 2~4) |
| `trim` | 있음(국면 2) | 처음 목록 = (원본, spec 제약) 변형 O 하나. 실행 중 엔진 밖 구동기가 승인된 trim 파일마다 부담 변형 C(합성 회로, 원본 θ 고정)를, C front가 비면 C′(합성 회로, 전 θ)를 추가한다(N3.12 (ii)(iii), offset-trim N3.11). 승인된 trim 파일이 여럿이면(XS-2 갱신 -- N·N+1 등 AI 제안 대안) 파일마다 C(·C′)다 |
| `compare` | 없음(국면 1) | (원본, matching 변형), (원본, trim 국면 1). 두 변형은 같은 topology라 단계 A·S0 계산을 공유한다(N3.6) |
| `compare` | 있음(국면 2) | trim 국면 2 변형(위 `trim` 국면 2 행과 같음 -- 변형 O와 추가 C·C′). matching 결과는 국면 1의 결과 JSON에 있다. 엔진은 그것을 다시 읽지 않고, 다시 계산하지도 않는다(S-3). 최종 비교는 비교 도구(N3.8) |

* 변형의 정체 = (topology 변형 지문 `connectivity_fp`, 제약 집합 지문, 고정 θ 성분 지문 -- v0.8, 비어 있으면 빈 지문). 같은 정체가 계획에 두 번 나오면 계획 함수가 거부한다.
* **승인 기록이 낡았거나 맞지 않을 때**: 승인 기록이 있으면 국면 2 규칙을 쓴다. 결속 검사(v0.8: offset-trim N3.3 결속 -- trim 파일 sha256·합성 회로 지문·합성 규칙 지문·spec 지문 대조; 옛 OT §8.3 '파생 지문·변환 규칙 해시')에 실패하면 그 규칙대로 `trim_approval_stale` 등으로 **정지**한다(fail-closed). 국면 1로 조용히 돌아가지 않는다. 승인되지 않은 회로를 사이징하거나 사용자 모르게 다른 국면을 도는 일을 막기 위해서다.
* **승인 파일이 있는 상태에서 국면 1을 다시 돌기**: 국면은 승인 기록 유무로만 정하므로, 사용자가 승인 기록 파일을 정해진 위치에서 치우면(이름 바꾸기·옮기기) 국면 1이 돈다. 엔진은 승인 파일을 지우거나 고치지 않는다. 진입 인자로 국면을 강제하는 길은 두지 않는다(S-2 인자 분기 삭제). 이 방법은 DO-9(오케스트레이터 기본안)다.
* 처음 변형 순서는 위 표 순서로 고정한다(결정성, NFR-S5). 실행 중 추가된 변형은 추가된 순서로 뒤에 붙는다(N3.12). 순서가 결과 값을 바꾸지 않음은 완료 조건 2가 확인한다.
* trim·compare 변형은 TR card가 그 경로를 만든 뒤에만 실행된다. 그 전에는 계획 함수가 `strategy`를 거부한다(fail-closed, 조용한 생략 금지). 거부 사유 코드는 design이 정한다.
* **구현 시점**: 계획 함수의 trim·compare 행과 그것만 쓰는 일(① 국면 규칙(승인 기록 유무 → 국면 2), ② 승인 기록 로더, ③ 낡은 승인 정지, ④ 국면 2 분기)은 OS-2에 넣지 않는다. OS-2의 계획 함수는 요구 없음·`matching` 행과 trim·compare 거부만 가지고, `approvals` 입력도 없다. 이 일들은 아래 **TR card별 배정(PD-2 승인, S-8)**으로 나눠 들어간다. compare 다변형은 OS-5(TR-2와 함께)다.
  * TR-2: 국면 1 행, 그리고 승인 파일이 있으면 내용을 읽지 않고 국면 2 미구현으로 fail-closed.
  * TR-3: 승인 기록 로더, 결속·낡은 승인 정지, 국면 2 분기(v0.8: 합성 회로 단계 A -- 합성 로더 블록은 TR-3 범위, offset-trim N5). OT §14.1의 'TR-1 로더' 배정을 바꾼 것이다(TR-1에는 부르는 곳이 없다).
  * TR-4: 구조 동일 검사.
  * offset-trim TR-5 안의 국면 2 게이트 해제: 국면 2 탐색 게이트를 연다(옛 이름 'TR-5b'는 offset-trim card 표에 없는 이름이라 v0.7에서 고침). → (v0.8) offset-trim TR-B(TR-5와 같은 통합 병합)로 옮김(아래 v0.8 항목).
  * TR-3~TR-5(국면 2 게이트 해제) 사이에는 승인된 회로가 단계 A까지만 돌고 멈춘다(OD-3, 수용됨).
  * (v0.8) offset-trim TR-B: 국면 2 처음 목록 = 변형 O, 부담 변형 C·C′ 추가(N3.12 (ii)(iii)). C·C′는 실행 중 추가로만 생기므로 국면 2 탐색 게이트 해제는 TR-5가 아니라 **TR-B(TR-5와 같은 통합 병합)**가 한다(옛 'offset-trim TR-5 안의 국면 2 게이트 해제' -- XS-15 기간이 TR-3~TR-5·TR-B 통합 병합까지로 늘어남, N5 XS-15 행)

### N3.6 실행기와 공유 범위

**함수**: `run_plan(plan, ...)`(pipeline 층, 이름은 design). 한 실행 = 실행 계획 하나다. v0.6: `run_plan`은 N3.12의 세션 인터페이스(열기 → 처음 변형들 실행 → 닫기)를 그대로 쓰는 얇은 진입이다. 그래서 사슬 구현은 하나다(W-1 '사슬 두 벌 금지'). (v0.7.2, O-63 (3)) 하네스처럼 실행 수명 값(블록 결과 색인의 평가 키 부분 등)을 읽어야 하는 호출자는 `run_plan` 대신 같은 세션 인터페이스를 직접 써서 세션이 열린 동안 읽는다(열기 → 변형 실행 → 읽기 → 닫기). `run_plan` 결과에는 색인·donors·계수 참조가 없다. 두 길이 같은 세션 위에 있어 사슬 구현은 여전히 하나다.

| 대상 | 공유 규칙 | 근거 |
|---|---|---|
| 블록 결과 색인·`RunCounters` | 실행 계획 진입에서 한 번 만들고, 모든 변형의 모든 블록 호출에 같은 객체를 넘기고, 실행이 끝나면 버린다. 40 §2.4.5 '수명'의 실행 경계 문구(XRUN-F1 card B 보완 뒤 '두 객체를 만드는 호출자 -- `run_stage_a`는 받는다', PD-8)에서 그 호출자를 '실행 계획 진입(세션 열기)'으로 적는다. 실행 사이에는 넘기지 않는다 | X-12, 원래 취지 문장, XS-7 |
| 단계 A(S1·S1v·structure 사실·보고) | 같은 topology 변형끼리 공유한다. S1은 topology와 선언만의 함수라 변형 사이에 같은 입력이다. S1v는 사용자 판정 제약 tuple만 extras로 받는다(F-3). 유도 제약은 `derived`라 S1v 밖이므로 같은 topology 변형끼리 S1v 입력이 같다(PD-1·PD-3, S-8) | F-3 |
| S0 수준 탐색 블록과 단계 B(`search_domain`·`constraint_classes`·`achievability`·출발 구간 등) | 블록 결과 색인으로 공유한다. `derived` 방식이라 변형 사이에 입력이 달라질 수 있는 것은 `derived`를 읽는 출발 구간(`start_intervals`)뿐이고, 나머지는 적중이다(PD-1). 출발 구간 입력은 같은 topology 변형이라도 `derived`가 다르면 다르다. compare 국면 1(matching 대 trim 국면 1)은 `derived` 형태가 달라 출발 구간을 따로 계산한다. 같은 입력이라고 말할 수 있는 것은 OS-L 반복 사이(문턱만 다름)이고, 그것도 출발 구간이 문턱을 읽지 않을 때뿐이다(읽으면 offset-trim G-12 '문턱에 의존하는 블록' 목록 대상, N3.12). (v0.7) 층 0 조립 경로의 블록(gain-budget LA-1 -- 블록 국소 후보·국소 봉인·블록 국소 front·조합 DP·조립·수리, design 41 §5) 가운데 유도 제약 문턱을 입력 버전으로 읽는 블록(예: LR6 σ 목표를 읽는 L 단계)도 같은 G-12 목록 대상이다 | F-4 |
| 평가 캐시·`SearchContext`(card B 뒤 `S3Index`의 평가 키 부분) | 지금 키 그대로 하나의 캐시를 공유하는 것은 금지다(같은 topology 변형끼리 `context_fp`가 같아 틀린 결과가 적중한다, N3.1-1). 나누는 방법은 DS-1 = (나)(평가 1회 + 변형별 판정, 조건 2개 -- O-176 Ⅵ)다 | F-1, F-2 |
| 커널 안 블록(봉인·GB5·metric) | 블록 결과 색인으로 공유한다. 같은 θ의 크기 결정 블록은 변형 사이에 적중한다. metric 블록은 요청 목록이 같을 때만 적중한다(N3.1-3) | F-2 |
| S3 기록 | 변형마다 줄에 변형 정체를 싣는다. 같은 topology 변형은 `context_fp`가 같아 줄만으로 구분되지 않기 때문이다(F-5). S3는 출력이고 실행 사이에 읽지 않는다(U-89) | F-5 |
| (v0.8) 부담 변형 O·C·C′(offset-trim N3.11) | O(원본)와 C·C′(합성 회로)는 topology 변형이 달라 단계 A 입력이 다르다(공유는 입력이 같은 블록의 색인 적중뿐). C는 고정 θ 성분이 있어 정의역이 다르다. C·C′가 O의 결과를 쓰는 길은 구동기가 만든 문턱 항목(`derived`)과 고정 θ 성분 기록 참조 둘뿐이다(변형 결과를 서로 읽지 않음 -- 아래 행과 같은 원칙) | offset-trim N3.11, N3.12 |
| (v0.7) 층 0 조립·수리·외층 자동 켬 판정·비지배 재판정(gain-budget LA-1 범위 1~3·6·7, O-37 (A), O-41 (1)) | **변형 단위**다. 변형마다 자기 제약 집합(사용자 판정 제약 + 그 변형의 `derived`)으로 역산 조립을 하고, 조립점 봉인 실패면 그 변형 안에서 수리하고, 외층 자동 켬 규칙(DEC-73 (4) (i)~(iv), (iv) = 판정 기록 분기 목록 밖 분기)도 그 변형의 발동 기록으로 판정하며, 비지배 재판정(모든 조합의 조립·수리 결과를 모은 뒤 한 번, O-37 (A))과 matching front 판정의 위반 점 제외 뒤 재필터(N3.3 ②)도 그 변형의 front에서 한다. 변형 사이에 공유하는 것은 그 안의 블록 호출뿐이고(블록 결과 색인, 입력 버전이 같을 때만 적중), 조립점·수리점·front·자동 켬 판정 결과는 공유하지 않는다. 그래서 완료 조건 2(계획 안 결과 = 단독 결과)와 9(추가된 변형 = 새 세션 단독 추가 결과)가 이 경로에서도 그대로 성립한다(블록 순수성, 40 §2.4.5 결정성) | gain-budget LA-1, O-37 (A), O-41 (1), O-53 A2 |

### N3.7 예산

* **제안(확인 요청 XS-12): 변형마다 E_total을 둔다.** 변형 v의 E_total,v = E_B + N_T + R(X-17 식 그대로, R = 2 × 그 변형의 `len(sctx.domain.variables)`). 이유: X-17은 '선언 40은 그대로 동작, 판정·test 예산 변경 없음'을 지키려고 정해졌고, 변형마다 두면 변형 하나의 탐색이 지금 단독 실행과 같은 예산을 받아 NFR-S5(계획 안 결과 = 단독 결과)가 성립한다. 한 E_total을 변형들이 나누는 안은 변형별 탐색과 결과가 계획 구성에 따라 바뀌어 NFR-S5를 깬다.
* **이 제안은 승인된 정의를 바꾼다**: 40 §2.4.9의 E_total은 '실행 하나의 커널 평가 수 상한'이고 그 문서의 유일한 정의다. §2.4.5 색인 상한 식도 '실행 하나' 단위다. 한 실행에 변형이 여럿이면 '실행 하나의 상한'은 Σ_v E_total,v가 되고 E_total은 변형 단위 양이 된다. 그래서 오케스트레이터 기본안으로 두지 않고 XS-7처럼 확인 요청 항목(XS-12)으로 둔다. 확인 전에는 다변형 실행(OS-5)을 시작하지 않는다.
* 시간 예산에서 유도하는 실행(X-17 후반)은 변형마다 같은 규칙으로 유도한다. 벽시계 정지도 변형마다 정한다(F-6). 실행 전체 시간은 변형 시간의 합이다.
* **색인 상한**: Σ_블록 분할 수 × (Σ_v E_total,v + S0 계산 벌 수). S0 계산 벌 수는 계획 안 서로 다른 S0 입력의 수다(OT §10.1의 +2 일반화). (**PD-7 확인, S-8**: B_S0 = 변형 수로 정한다(design OB-12: 국면 2 계획에 원본 topology 변형이 없으면 구조 비교용 원본 S0 한 벌을 더한다). 실행 전에 계획만으로 계산되고, '서로 다른 S0 입력 수'보다 크거나 같다(안전 쪽). OS-5는 card C `S3Index` 생성자에 필수 인자 B_S0를 더하고 변형별 E_total,v를 등록하며, card C test를 같은 변경에서 고친다. 기본값 인자로 피하지 않는다.) card C의 등록 시 fail-closed 검사는 이 식을 쓴다.
* **실행 중 추가된 변형(v0.6, N3.12)**: 추가된 변형도 자기 E_total,v를 받는다(XS-12 그대로). 색인 상한의 Σ_v E_total,v와 B_S0(변형 수)는 변형이 추가되는 순간 그 몫만큼 늘고, 등록 시 상한 검사는 늘어난 값을 쓴다. 실행 전체 상한은 반복 상한(offset-trim D-19: 실행 설정 선언값, 기본값 없음)으로 닫힌다. 반복 상한 선언이 없으면 추가가 없다(첫 범위 판정만). 상한과 B_S0가 실행 중에 늘어나는 것은 card C `S3Index`에 '늘리는' 동작(API)을 더하는 변경이다. PD-7처럼 card C test를 같은 변경에서 고치고, 기본값 인자로 피하지 않는다.

### N3.8 compare 두 국면과 읽기 전용 비교 도구

1. **국면 1**(승인 기록 없음): matching 변형과 trim 국면 1 변형을 한 실행에서 돈다. 결과 JSON에 matching front와 trim 후보표를 싣는다(v0.8 -- 옛 '추천·파생 topology'는 없음).
2. **사양·제안·승인**(엔진 밖, offset-trim N3.1 2~4): 닫힌 실현 점의 oracle MC → trim 사양 기록 → AI trim 파일 제안 → 사용자가 trim 파일을 승인한다(T-2 게이트 유지, O-258 (B); 옛 '파생 topology(N, N+1 중 고른 것)').
3. **국면 2**(승인 기록 있음): 승인된 trim 파일의 부담 변형(O·C·C′)을 돈다. matching은 다시 돌지 않는다.
4. **최종 비교**(S-3 기본안): 읽기 전용 도구가 국면 1 결과 JSON(matching)과 국면 2 결과 JSON(trim)을 읽어 같은 칸(공통 판정 값, 전력·면적 front, offset 한계 대비 여유, 유도 제약의 판정, 출처 실행 id·code_fp)을 나란히 낸다.
   * 도구는 엔진 밖(`tools/`)에 두고 엔진을 import하지 않는다. 엔진은 도구 출력을 입력으로 받지 않는다. 두 결과의 계산 재사용도 없다.
   * 도구는 판정·권고 문장을 만들지 않는다. 두 결과의 `code_fp`나 공통 판정 선언이 다르면 그 사실을 표에 적는다(조용히 비교하지 않음).
   * 도구 위치와 이름은 design이 정한다.

### N3.9 옛 경로 삭제와 다른 문서의 개정

| 대상 | 바뀌는 것 | 시점 |
|---|---|---|
| OT §4 흐름 | 진입 인자 `trim_approval_path`로 단계를 고르는 문장, `trim_approval_without_decl` 사유를 지운다. 국면은 실행 계획(N3.5)이 승인 기록 유무로 정한다 | OS-0 design과 함께 재승인(S-4). 코드에는 아직 없으므로(F-7) 코드 삭제는 없다 |
| OT §5.1 | `coverage_multiple`을 요구 섹션으로 옮긴다(XS-6) | 같음 |
| OT §5.2(D-4) | 공존 거부 규칙을 N3.2 로더 규칙으로 대체한다(XS-1) | 같음 |
| OT §9.4·§9.5 | 추천을 N 하나에서 {N, N+1}로 연다(XS-2). **(v0.8) 대상 소멸** -- 엔진 추천·파생 topology 출력이 없어져(O-258) 두 절은 offset-trim TR-0에서 지운다; XS-2 취지(N·N+1 교환을 사용자가 봄)는 '승인된 trim 파일마다 변형'으로 남는다 | offset-trim TR-0 |
| OT §7·§6.3·§8 (v0.8) | `augment_trim`·`trim_decl` 합성·파생 결속을 trim 파일 스키마·합성 로더·trim 파일 결속으로 바꾼다(offset-trim v0.7 N3.3) | offset-trim TR-0 |
| OT §10.1 색인 상한 | N3.7 일반식으로 대체 | 같음 |
| 40 §2.4.5 수명 | 실행 경계 = 두 객체를 만드는 호출자(PD-8, card B 보완) → 그 호출자 = 실행 계획 진입(XS-7) | OS-0, XRUN-F1 card B 병합 뒤 |
| 40 §2.4.5 '전달' 행(PD-8, S-8) | '단계 A가 두 객체를 만든다'를 '`run_plan`이 만든 `donors`·`counters`를 `run_stage_a`가 필수 키워드로 받는다'로 | card B 코드 착수 전이면 card B design 개정으로, 이미 착수했으면 OS-2와 함께 |
| 40 §2.4.5·§2.4.9 상한·`S3Index` 생성자(PD-7, S-8) | B_S0와 변형별 E_total,v 등록 | OS-5 |
| OT §14.1·§15 TR card 배정(PD-2, S-8) | 승인 기록 로더 TR-1 → TR-3, 국면 2 분기 TR-3, 탐색 게이트 해제 = offset-trim TR-5 안의 국면 2 게이트 해제 → (v0.8) offset-trim TR-B(TR-5와 같은 통합 병합) | design v0.2와 함께 OT 개정 |
| offset-trim 계획 TR-1 범위 | spec trim 섹션 로더는 요구 섹션 로더와 함께 정의된다 | OS-0 |

### N3.10 층 분류(파이프라인만으로 되는가)

S-2는 '파이프라인 층 재작성, 핵심(graph·블록·kernel·search) 유지'다. 이 계획의 각 일이 어느 층을 건드리는지 F-1~F-3·F-12로 분류한다. authoring(spec 로더)은 S-2가 핵심으로 꼽지 않은 층이라 확장 대상으로 본다.

| 일 | 필요한 변경 | 분류 | S-2와의 관계 |
|---|---|---|---|
| 변형별 제약 집합 주입(PD-1 승인, S-8) | 로드한 spec 객체 하나를 모든 변형이 같이 쓰고, 변형의 유도 제약만 `build_search_context`의 별도 입력 `derived`로 넣는다. 사용자 판정 제약은 요구가 있으면 모든 변형에서 같다(수단 제약 공존 거부). spec 사본을 만들지 않으므로 spec을 extras로 받는 `achievability`(`stage_b.py:168`)는 변형마다 다시 계산되지 않는다. 유도 제약을 실제로 읽는 소비자(커널 요청·행, `start_intervals` extras, LUT mismatch 필수 검사)만 `derived`를 읽는다. S1v·`constraint_classes`·`search_domain`의 입력은 변형 사이에 같다 | **핵심 층 확장**(search: `build_search_context` 키워드와 전달 자리, PD-4 범위) | XS-10 범위 안(승인됨). spec 사본·`from_sections` 재생성 방식(v0.4 문언)은 쓰지 않는다 -- 옛 문장은 history |
| 유도 제약을 기존 metric으로 표현할 수 있는 경우(trim 국면 2의 `trim_range`·`trim_residual`, 공통 판정) | 위 주입으로 끝난다. trim metric 자체는 TR card 몫이다 | pipeline(+TR card) | 맞음 |
| G-S1 matching 판정(O-53 A2 두 자리) | ① 커널 판정 k·σ_in + \|V_id*\| ≤ 문턱(커널 점 V_id* = 성분 (1)(2) -- 상위 U-108): 지금 레지스트리에 이 양의 metric이 없다(F-10). (i) k를 입력으로 받는 새 metric을 레지스트리에 더하거나(metrics), (ii) `offset_in_sigma_mv`를 k배로 읽는 제약 행을 `ss_constraint_rows`에 더한다(search). ② front 판정 k·σ_in + \|V_id*\| ≤ 문턱: 상위 DEC-74·U-108 front 재판정 자리(판정 W로 성분 (3)을 더함, 위반 점 제외·비지배 재필터)에서 같은 V_id* 값을 읽어 판정한다. 새 판정 자리·새 V_id* 계산을 만들지 않는다. 한계를 σ와 V_id* 몫으로 나눠 따로 판정하는 것은 나누는 비율을 발명해야 해서 택하지 않는다(NFR-S6) | **핵심 층 확장**(① metrics 또는 search, ② search front 판정 자리의 소비자 추가) | 다름 → XS-10, XS-20 |
| G-S2 matching 출발값 | `iv_matching_l`은 이름 `offset_in_sigma_mv`로 L 하한을 켠다(`iv_matching_l.py:40, :107`). 요구만 있으면 L 하한이 꺼진다. 규칙 정본은 gain-budget LR6이고(N3.3 '출발값' 행; gain-budget v6.38.2 LR6 개정으로 그 출발값은 L 하한이 아니라 입력 gm/ID 하한 -- 그 계획 DEC-105 (6)), 바꾸는 것은 LR6 구현이 σ 목표를 읽는 출처(커널 판정 ① = 절대 σ 제약)뿐이다. 출발값 전용이라 판정은 바뀌지 않는다 | **핵심 층 확장**(search 출발값) | 다름 → XS-10 |
| 실행 계획·실행기·결과 기록 | pipeline 모듈 신설·재작성 | pipeline | 맞음 |
| 블록 결과 색인 수명 경계 | 색인을 만드는 자리(card B 뒤: `run_stage_a`를 부르는 호출자 -- PD-8)를 실행 계획 진입(세션 열기)으로 정한다. 색인 자체(search)는 바꾸지 않는다 | pipeline(+design 문구, XS-7) | 맞음 |
| DS-1 (가)·(나)·(다), DS-2 (나) | N3.1 표. (가)도 card B 뒤에는 `S3Index`의 두 부분 수명을 가르는 search 변경이다 | **핵심 층 변경** | 다름 → XS-5 |

### N3.11 SPICE 온도 보정 루프와의 연결(T-29~T-33, 사용자 승인 S-9)

**결정(S-9)**: 온도 보정 루프(Δ_T 선언과 반복)는 offset-trim 계획이 소유한다. 이 계획은 연결점만 둔다. 선언된 온도 여유가 있으면 matching 유도 제약 문턱 = `offset_in_max_v` − Δ_T이고, trim 변형은 offset-trim 계획 규칙을 따른다. 아래는 그 연결점의 세부다.

사용자 결정 T-29는 offset·trim 잔여의 합격을 SPICE 오라클의 온도 범위 판정으로 바꾸고, T-30은 'SPICE 온도 보정 루프'를 offset-trim 계획 보완으로 진행하게 했다(offset-trim 계획 v0.5, 브랜치 `trim-plan-r1`, N3.8). 그 계획은 T-29의 'offset 판정'을 이 계획의 matching 유도 제약으로 읽는다(그 계획의 해석 X-21).

**연결점**: 보정 루프는 matching 유도 제약의 문턱을 조인다. 보정 루프의 반복 j에서 엔진 문턱은 `offset_in_max_v` − Δ_T(matching)이다(offset-trim N3.8.3 '문턱 적용'). (v0.7) 이 문턱 항목 하나를 O-53 A2의 두 판정(커널 k·σ_in, front k·σ_in + \|V_id*\|)이 함께 읽는다(문턱 사본 없음, N3.3). Δ_T(matching)의 정의·방향·갱신 규칙은 offset-trim 계획 N3.8.3(v0.6, `plan/offset-trim-v06` `23e6a142`)이 정본이고, 이 계획은 사본을 두지 않는다.

**소유 경계**(한 규칙에 정본 하나):

| 대상 | 정본 | 이 계획이 하는 일 |
|---|---|---|
| matching 유도 제약의 형태 k·σ_in + \|V_id*\| ≤ 문턱과 판정 위치 둘(커널 k·σ_in, front 합성 -- O-53 A2), 단위 환산, view 출처, 커널 행 형식(G-S1) | **이 계획**(N3.3, design G-S1). V_id*의 정의·계산·기준과 front 판정 자리(판정 W, 단위 9 재판정, 위반 점 제외·비지배 재필터)는 gain-budget DEC-23·DEC-74가 정본 | 정의한다(V_id*·front 판정 자리는 인용만) |
| 그 문턱 값의 출처: 요구 `offset_in_max_v` 참조 | **이 계획**(N3.2) | 정의한다 |
| Δ_T의 정의·측정 선언 형식·출처 지문·무효 규칙, 문턱 합성 형식(spec 참조 − Δ_T 선언 참조, 숫자 사본 금지), 루프·멈춤·분해 정지 규칙, 범위 판정, 오라클 표본 수 | **offset-trim 계획**(N3.8, v0.6 `23e6a142`; design G-9·G-10) | 쓰지 않는다. 문턱 합성은 offset-trim이 정하는 함수 하나를 matching 합성 행이 부른다(사본 함수 금지) |
| 반복의 구조(T-35, D-24 안 B): 반복 하나 = **같은 실행 계획 안에 추가되는 변형**(같은 topology + 문턱만 다른 제약 집합). 단계 A·S0·블록 결과 색인을 공유한다. 오라클은 엔진 밖 별도 프로세스다 | 구조 결정은 offset-trim(D-24, T-35). **변형 추가 인터페이스와 그 규칙은 이 계획**(N3.12) | 변형 추가 인터페이스·허용 범위·수명·예산·변형 정체(반복 번호 포함)를 정한다. v0.5까지의 '반복 하나 = 실행 계획 하나를 처음부터 다시 도는 것, 반복 사이 공유 없음'(D-24 안 A 문언)은 대체됐다 |
| 요구 스키마 안 판정 온도 범위 칸(offset-trim v0.5 D-18이 `offset_requirement` 안 새 칸으로 제안) | 스키마(칸 이름·형식·로더 검사)는 **이 계획**(N3.2), 값과 채택은 **offset-trim D-18 -- 결정됨(T-34)**: T-14 범위, spec 한 곳 선언, 모든 소비자가 참조 | N3.2 스키마 표에 칸을 더했다(v0.5.3). T_j 포함 검사는 offset-trim O-8 |
| matching 유도 제약의 `verified_by`(오라클 measure) | 측정 규칙은 offset-trim N3.8(범위 판정·표본 수 G-10), 오라클 코어는 oracle-portability 계획(T-31·T-33) | **이 계획 쪽 card OS-V**(matching 합성 판정에 오라클 측정을 붙임, 승인 S-11)를 둔다. (v0.7, 감사 D3) OS-V 범위는 **합성 판정 행의 결속만**이다: `offset_sys_mv`(V_id*)의 `verified_by` 연결은 gain-budget card VB-1(N6.18)이 정본이고 OS-V는 그것을 선행으로 인용한다(새로 연결하지 않음). 선행(감사 D4)은 OS-2, gain-budget VB-1, 그리고 오라클 쪽 oracle-portability OP-3(입력 형식)·gain-budget EO-1(엔진 점 → 오라클 입력 생산자 -- 옛 '2단계 전도 판정 함수'는 상위 O-205 (2)·O-210 RR-2로 삭제)·oracle-portability OP-5(계통 offset `.dc` V_id*, 불일치 σ의 A = `.tf`, 오라클 한 단계 전도 판정)이고, offset-trim TR-TL의 선행이다. 그 전에는 합성 판정 metric이 `spice_unverifiable` 목록에 실행 전 출력된다(DEC-90 (3), OT §10.6 선례). card 배정은 V-1(승인됨, N7.2 OS-V 행) |
| 엔진 결과의 합격 표기 | 이 계획(결과 JSON) | T-29 뒤에는 엔진 front의 matching 판정(LUT 한 조건, V_id*는 '1차' 표기)이 최종 합격이 아니다. 결과 JSON에 '최종 합격은 오라클 범위 판정' 표기를 싣는다 |

**순서**: T-30 원문은 '순서 = TR-7 뒤'다. 그래서 matching만 쓰는 회로의 보정 루프도 TR-7 뒤에 열린다. matching에 한해 앞당기지 않는다(DS-T1, S-9로 권고대로 닫힘). OS-2는 Δ_T 입력 없이 요구 문턱만 쓰며, 문턱 합성 입력 자리는 보정 루프가 열릴 때(offset-trim 해당 card) 같은 변경에서 배선한다(만들면 배선 -- OS-2에서 빈 자리를 미리 만들지 않는다).

**T-31·T-33**: matching 유도 제약의 오라클 측정(`verified_by`)은 공정·시뮬레이터 무관 방법론 위에서만 한다. 그 방법론과 오라클 개정은 offset-trim 계획·오라클 개정 작업의 몫이다.

### N3.12 실행 중 변형 추가(T-35, offset-trim D-24 안 B, v0.6)

**배경**: T-35는 보정 루프 반복을 '같은 실행 안 변형'으로 정했다. 엔진 밖 구동기가 실행 계획을 유지한 채 오라클(별도 프로세스)을 부르고, 다음 변형을 계획에 더한다. 원래 취지('처음 topology를 실행할 때 계산하고 그 값을 나머지 최적화에서 재사용')에 맞는 구조이고, 실행 수명은 그대로 '실행 계획 하나'(XS-7)라서 실행 사이 재사용이 아니다.

| 항목 | 규칙 |
|---|---|
| 부르는 주체 | **엔진 밖 구동기**(offset-trim G-12, 위치·서명은 그 계획의 design)다. 엔진 안의 다른 코드(search·kernel·블록)는 변형을 더하지 않는다. 구동기는 엔진을 같은 프로세스에서 import해 실행 계획 세션을 쥐고, 오라클은 별도 프로세스로 부른다(오라클은 엔진을 import하지 않는다) |
| 인터페이스(이름은 design) | 실행 계획 세션: ① 열기(`build_run_plan`의 처음 목록, 블록 결과 색인·`RunCounters` 생성 = 실행 경계, XS-7) ② 변형 실행(변형 결과를 돌려준다: front·판정·결과 JSON 칸) ③ 변형 추가(아래 허용 범위만) ④ 닫기(색인·계수를 버린다. 닫은 뒤 그것에 닿는 길은 없다 -- v0.7.2, O-63 (3)). `run_plan`은 ①→처음 변형 모두 ②→④를 부르는 얇은 진입이다(사슬 하나, W-1). (v0.7.2, O-63 (3)) 색인의 평가 키 부분 같은 실행 수명 값은 ②와 ④ 사이에 세션 공개 API로만 읽는다. ②가 돌려주는 변형 결과와 `run_plan` 결과에는 색인·donors·계수 참조를 담지 않는다(읽기 API의 이름·형식은 design, 전수 열거 API는 N10.4 PS-7). **허용 동작**: 세션을 열고 처음 변형은 실행하지 않은 채 변형을 추가해 그 변형만 실행할 수 있다. 결정성 비교 기준(아래 '결정성' 행)이 이 동작을 쓴다. 추가의 기준이 되는 처음 변형은 계획에 있으면 되고 실행됐을 필요는 없다 |
| 추가할 수 있는 변형 | 닫힌 세 종류뿐이다(v0.8 -- 옛 '(i) 하나뿐'; 그 밖은 fail-closed 거부).<br>**(ii) 부담 변형 C**(offset-trim N3.11, O-258): 국면 2 처음 변형 O(원본)가 끝난 뒤, 승인된 trim 파일마다 (합성 회로, spec 제약 + 국면 2 trim 제약 + 부담 제약, 고정 θ 성분 = 출처 칸이 원본인 소자의 θ 성분 → 변형 O 선택 점 기록 참조). 부담 문턱 항목은 구동기가 추가 한 번에 한 번 만들어(변형 O 선택 점 metric 기록 참조 ∓ spec 부담 예산 참조, 숫자 사본 없음) `derived` 자리로 넣는다 -- 아래 (i) ①② 경로와 같은 자리·같은 writer 규칙. θ 성분이 원본·trim에 섞이면 C를 추가하지 않는다(offset-trim N3.11 'θ 성분 소속').<br>**(iii) 재풀이 변형 C′**(같은 근거): 그 trim 파일의 C front가 비었거나 C를 추가하지 못했을 때만, (합성 회로, spec 제약 + 국면 2 trim 제약, 고정 θ 없음, 부담 제약 없음).<br>(ii)(iii)은 topology가 처음 목록 변형(O = 원본)과 다르지만, 합성 회로는 승인 기록이 정하는 결정적 입력이라 세션 열기 때 이미 정해져 있다(새 topology를 실행 중에 만들지 않음 -- 합성은 세션 열기에서 한 번). 추가 순서는 (ii) → (iii) 고정이다(결정성).<br>**(i) Δ_T 문턱 변형**: **이미 계획에 있는 변형과 같은 topology 변형**이고, 제약 집합이 그 변형과 **유도 제약의 문턱만** 다른 것이다(고정 θ 성분은 그 변형 그대로). 문턱이 들어오는 방법(v0.6.2 정합):<br>① 엔진 밖 구동기가 offset-trim의 문턱 합성 함수(`tightened_threshold`, offset-trim design TR-0T §20.3 소유)를 **추가 한 번에 한 번** 부른다. 결과는 조인 문턱 항목이다(spec 참조 − Δ_T 기록 참조, 숫자 사본 없음, N3.11).<br>② 세션 변형 추가가 그 항목을 변형 제약 별도 입력 `derived`(PD-1)의 자리로 받는다. Δ_T가 들어가는 길은 이 하나다(offset-trim D-24 표).<br>③ 엔진은 평가마다 문턱을 합성하지 않는다(같은 입력 재계산 0). 합성 결과가 0 이하(`tightened_threshold_nonpositive`)면 구동기가 추가 전에 거부한다.<br>형식 소유: `derived` 항목 형식(항목 자리)은 이 계획, Δ_T 기록과 합성 함수는 offset-trim이다.<br> (i)에서 topology·사용자 판정 제약·요구·`strategy`·국면이 다르거나, 문턱 밖의 유도 제약 형태가 다른 추가, 그리고 (ii)(iii)의 조건 밖 추가(국면 1에서의 추가, 승인 기록에 없는 trim 파일, O 완료 전 C, C 성공 뒤 C′)는 fail-closed로 거부한다(사유 코드는 design) |
| 수명 | 색인·`RunCounters` = 실행 계획 하나(바뀌지 않음, XS-7). 세션을 닫으면 버린다. 세션 사이·실행 사이에 넘기지 않는다(U-89). 결과 객체에 참조를 남겨 닫은 뒤의 호출자에게 건네는 것도 넘기는 것이다(v0.7.2, O-63 (3) -- graph 규칙 2: 블록 결과 색인은 실행 수명 하나). 구동기는 이전 반복의 front 점을 다음 변형의 시작점으로 주지 않는다(offset-trim N3.8 '관계') |
| 예산 | 추가된 변형마다 E_total,v(XS-12). 색인 상한과 B_S0는 추가 때 늘어난다(N3.7). 반복 수는 offset-trim D-19(실행 설정 선언값, 기본값 없음)로 닫힌다. **이중 fail-closed 검토(design 몫)**: 세션 열기에서 반복 상한(D-19)을 받아, 상한을 넘는 추가는 엔진도 `iteration_cap` 계열 사유로 거부하는 안이다. 구동기의 상한 검사와 이중이다. 채택 여부와 사유 이름은 design이 정한다(상한 값의 정본은 실행 설정 하나 -- 사본 금지) |
| 변형 정체(XS-13) | **중복 판정 키** = (topology 변형 지문, 제약 집합 지문, 고정 θ 성분 지문(v0.8), 원인 지문 = Δ_T 기록 지문 또는 부담 문턱 항목 지문(v0.8))이다. 반복 번호는 키에 넣지 않는다. 반복 번호를 넣으면 추가마다 키가 달라져 중복 거부가 걸리지 않기 때문이다. 같은 키(같은 원인 지문 포함)를 다시 추가하면 거부한다.<br>**반복 번호**(처음 목록 = 0, 추가될 때마다 1씩)는 정체 **표시(보고) 칸**으로만 S3 줄·결과 JSON에 싣는다.<br>`run_id`에는 중복 판정 키를 반영한다. 키가 다르면 같은 S3 루트에서도 runs 줄이 겹치지 않는다 |
| 결정성 | 같은 처음 입력과 같은 추가 순서·문턱 입력이면 같은 결과다. 추가된 변형의 결과는 **새 세션을 열어 처음 변형은 실행하지 않고, 같은 문턱 입력으로 그 변형만 추가해 실행한 결과**와 비트 동일하다(위 '허용 동작'. E_B 선언 실행, 완료 조건 2·NFR-S5와 같은 범위). `build_run_plan`은 추가 변형을 만들지 못하므로 '그 변형만 담은 계획'을 기준으로 쓰지 않는다. (v0.8) (ii)(iii)은 변형 O 선택 점을 참조하므로 비교 기준 = 새 세션에서 변형 O를 실행한 뒤 같은 trim 파일로 그 변형만 추가해 실행한 결과다(O 결과는 입력이고 비교 대상이 아님) |
| 재사용 범위 | 문턱이 다르면 탐색 궤적이 바뀌므로, 커널 안 블록(봉인·GB5·metric)은 새 θ에서 정당하게 계산된다. 그래서 판정은 둘로 나눈다. ① **θ에 무관한 블록(단계 A·S0 수준)**은 추가된 변형에서 계산 0(전부 색인 적중)이다. 다만 제약 문턱을 입력으로 읽는 S0 수준 블록은 계산되고, 그 블록은 offset-trim G-12의 '문턱에 의존하는 블록' 목록 안에만 있어야 한다. 층 0 조립 경로(gain-budget LA-1)는 변형 단위라 추가된 변형에서 다시 돌고(N3.6 v0.7 행), 그 안에서 문턱을 읽는 블록도 같은 목록 대상이다. ② 실행 계획 전체에서 **같은 입력 재계산 0**(완료 조건 3, 블록과 평가 키 모두)이다 |
| 평가 키 | 추가된 변형도 같은 topology라 `context_fp`가 같다. 평가 키 부분의 처리(공유 금지·나누는 방법)는 DS-1을 그대로 따른다. 보정 루프는 같은 θ를 다시 밟을 가능성이 크므로 DS-1 결정의 영향이 크다. DS-1은 OS-L 전에 정해져야 한다 |
| S-3과의 관계 | **X-23 수용(T-37, 이 계획 XS-18 승인 S-12)**. 엔진은 이전 실행 결과를 읽지 않는다. Δ_T는 오라클 측정값이고, 구동기가 대조(D-25)한 뒤 변형 제약 입력으로만 넣는다(offset-trim X-23). 엔진은 오라클 결과 파일을 읽지 않는다(상위 O-178 oracle 닫기와의 경계 = 상위 Q-W1과 함께 정함 -- offset-trim N3.8.7) |
| D-25·D-20과의 관계 | **D-25(Δ_T 출처 지문 대조) 결정됨(T-36: (c) 출처 무결성 + (c-2) 엔진 밖 구동기)**: 대조 주체는 엔진 밖 구동기다. 그래서 엔진 인터페이스는 대조를 통과한 문턱 입력만 받는다(엔진 로더 대조 안은 채택되지 않아 서명에 선언·지문이 들어가지 않는다. 서명 세부는 design이 닫는다). **D-20(판정 대상 점) 결정됨(T-36 (가))**: 구동기가 오라클에 보낼 front 점을 고르는 규칙이다. 엔진 쪽은 변형 결과에 front 점을 읽기 전용으로 내는 것(W-1 노출 요구) 말고는 영향이 없다. (v0.7.2 확인, O-63 (3)) front 점은 변형의 탐색 결과이지 블록 결과 색인·donors·계수가 아니다. 그래서 변형 결과가 front 점을 읽기 전용으로 내는 것은 '결과 객체에 색인·donors·계수 참조를 두지 않는다'와 맞는다 |

---

## N4. library 13회로·요구 적용 판정

판정은 규칙으로 하고, 단계마다 '해당 없음'은 사유 코드로 남긴다.

1. spec에 요구가 없으면 → 무동작(완료 조건 1).
2. 요구와 수단 제약이 함께 있으면 → 로더 거부(N3.2).
3. matching인데 offset 기준이 정의되지 않으면(gain-budget DEC-23 `reference_undeclared` -- O-53 B3: 선언 없는 단일 출력) → 탐색 전 정지(N3.3).
4. trim·compare는 → offset-trim N4 판정을 그대로 따른다(단일 입력 회로 정지 등).

**지금 library**: 이관 전 9회로 spec에 요구 섹션이 없다. 그래서 이 기능 병합 뒤에도 library 결과는 바뀌지 않는다(완료 조건 1). 요구를 쓰는 검증은 `origin: fixture` spec으로 한다(offset-trim T-24·T-28의 시험 회로 경로와 같은 규칙). library spec을 요구 형식으로 옮길지는 사용자 몫이다(DS-U5).

---

## N5. 원래 취지와 다름(따로 보고, 각각 승인 필요)

사용자 규칙(2026-10-15 '원래 취지와 다른 판단 보고 규칙')에 따라, 승인 전에는 아래 항목을 기본안으로 삼지 않는다. (a)~(d)는 S-1·S-4가 '이 계획·design에서 다시 승인'으로 지정한 것이다.

| ID | 내용 | 원래 결정·취지 | 승인 |
|---|---|---|---|
| XS-1 (a) | **D-4 공존 거부 대체**: 승인된 D-4(`offset_in_sigma_mv`와 trim 선언 공존만 거부, `offset_excess`·`offset_sys_mv`는 보고로 내림, OT §5.2)를 '요구가 있으면 offset 수단 제약 전부 거부 + 방식별 유도'로 바꾼다 | offset-trim 계획 D-4(사용자 T-6 승인) | **필요** |
| XS-2 (b) | **N을 {N, N+1}로 연다**: OT §3.4·§9.4는 front 집계로 추천 N 하나(가능한 최소 N)를 낸다. 이 계획은 국면 1이 N과 N+1 두 구성의 파생 topology를 내고, 사용자가 승인한 것마다 국면 2 변형을 만든다. N+1은 LSB가 작아 잔여 조건에 여유가 생기는 대신 셀 수·면적이 는다. 이 교환을 사용자가 보게 하려는 것이다. N+1의 m 규칙은 DS-U6. **(v0.8, O-258) 대상 갱신**: 엔진 추천·파생 topology가 없어져 '국면 1이 두 구성을 낸다'는 대상 소멸. 같은 취지(교환을 사용자가 봄)는 'AI가 trim 파일 대안(N, N+1 등)을 제안하고 승인된 trim 파일마다 국면 2 변형'으로 남는다(N3.5). DS-U6(N+1의 m 집계)도 대상 소멸(m = trim 파일 선언) | OT §9.4(사용자 T-18 승인) | 승인(S-5) → **v0.8 대상 갱신 -- 작성자 유도, 검증·확인 대상** |
| XS-3 (c) | **compare 추가**: 방식 하나를 고르는 대신 두 방식을 같은 공통 판정으로 돌려 나란히 낸다. 엔진은 권고하지 않는다 | offset-trim 계획은 trim 선언 회로만 다룸 | **필요** |
| XS-4 (d) | **OT §4 개정**: 진입 인자(`trim_approval_path`)로 단계를 고르던 승인된 흐름을 실행 계획의 국면 규칙(승인 기록 유무)으로 바꾼다 | OT §4(사용자 T-18 승인) | **필요**(S-4: 실행 계획 design과 함께 재승인) |
| XS-5 | **DS-1 (가)·(나)·(다), DS-2 (나)는 핵심 층 변경**: card B 뒤 `S3Index`의 평가 키 부분과 블록 결과 부분의 수명을 가르면 search가(가), 평가를 크기·metric과 판정으로 나누면 kernel·`ss_evaluate` 호출이(나), 평가 키에 제약 지문을 넣으면 search의 `eval_key`·`context_fp`가(다), S1v 투영을 좁히면 graph 층이(DS-2 (나)) 바뀐다(N3.1). S-2 '핵심 유지'와 다르다 | S-2 | 승인(S-5 허용 범위). **DS-1 = (나) 결정(O-176 Ⅵ -- 옛 S-14 (다) 번복)**: 바뀌는 핵심 층은 kernel·`ss_evaluate` 요청 출처(계획 안 요청을 한 번에)와 판정 행 자리(graph 필드 `constraint_rows`, `EvalResult` 판정 칸 삭제)다. DS-2는 PD-3으로 닫힘 |
| XS-6 | **k 출처 이동**: `offset_trim.coverage_multiple`(OT §5.1, 시험 회로 값 T-25)을 요구의 `coverage_multiple`로 옮긴다. 승인된 스키마와 T-25의 기록 형식이 바뀐다(값은 같음) | OT §5.1, T-25 | **필요** |
| XS-8 | **DS-1 (가)·(다), DS-2 (가)는 같은 실행 안 변형 사이 재계산을 받아들이는 편차**: (가)는 같은 topology 변형이 같은 θ를 밟으면 같은 평가 키를 변형마다 다시 계산한다(완료 조건 3과 모순, N3.1 표). (다)는 키를 나눠 형식상 조건 3을 지키지만, 같은 θ의 커널 평가와 요청이 다른 metric 블록 계산이 변형마다 남는다. DS-2 (가)는 같은 topology의 S1v를 변형마다 다시 계산한다. 셋 다 '처음 계산한 값을 나머지 최적화에서 재사용'과 거리가 있다 | 원래 취지 문장(N1.1) | 승인(S-5 허용 범위). **DS-1 = (나) 결정(O-176 Ⅵ)으로 이 편차는 없어진다**: 같은 θ는 실행 안에서 한 번 평가하고 판정만 변형별이다; 남는 경우 = 추가 변형이 새 metric 요청을 가져올 때이고 그때는 fail-closed(조건 (2)). DS-2 (가) 편차는 PD-3으로 대상 없음 |
| XS-9 | **trim 시험 회로 spec 영향**: 승인된 T-27은 시험 회로 spec에 `offset_excess` 제약을 유지한다(강등 경로 확인용). T-28은 그 spec(`offset_trim` 섹션 = residual_offset_v·coverage_multiple·trim_temperature_c, T-25)을 TR-1 병합 뒤 `assets/fixture/trim/`에 둔다. 이 계획의 로더 규칙에서는 (1) 요구 없는 `offset_trim` 단독은 거부(N3.2), (2) 요구와 `offset_excess` 공존은 거부(DS-U2), (3) k는 요구로 옮긴다(XS-6). 그래서 그 spec은 요구 섹션(`strategy: trim`, k, `offset_in_max_v` ≥ V_res)으로 다시 써야 하고, '강등 경로 확인'이라는 T-27의 목적은 대상이 사라진다. `offset_in_max_v` 값은 사용자 몫이다 | T-25·T-27·T-28 | **필요**(재승인) |
| XS-10 | **matching 합성 판정과 출발값은 핵심 층 확장**: G-S1(새 metric 또는 합성 제약 행)과 G-S2(`iv_matching_l`이 합성 판정에서 σ 목표를 읽게 함)는 metrics·search 층을 고친다(N3.10). S-2 '핵심 유지'와 다르다. 확장 없이 기존 `offset_in_sigma_mv`·`offset_sys_mv` 두 제약으로 쓰려면 한계를 나누는 비율을 발명해야 해서 택하지 않는다 | S-2 | **필요** |
| XS-11 | **S-4 순서 문구를 나눈다**(권고안, N7.1): '실행 계획 구현 → TR-1'에서 TR-1 앞에는 단일 변형 실행 계획(요구 없음·matching)과 trim·compare 거부까지만 구현한다(OS-2). 다변형 공유·변형 정체 칸·Σ 상한·공통 판정 검사는 trim·compare를 처음 여는 TR card에 묶어 그때 배선한다(OS-5). 국면 규칙·승인 기록 로더·낡은 승인 정지·국면 2 분기는 N3.5 TR card별 배정(PD-2: TR-2 국면 1과 국면 2 미구현 fail-closed, TR-3 로더·결속·낡은 승인 정지·국면 2 분기, offset-trim TR-5 안의 국면 2 게이트 해제)을 따른다. 이유: 이것들은 trim·compare에서만 쓰이고, TR card 전에는 그 방식이 거부되므로 제품 경로에서 쓰는 곳이 없어 '만들면 배선'을 지킬 수 없다. OT §4 흐름은 코드에 없어(F-7) TR-1 앞에 대체할 옛 경로도 없다. 대안 (ii): 다변형 경로를 TR-1 앞에 다 구현하고, TR card 전까지는 fixture spec으로만 실행하는 것을 승인받는다 | S-4 | **필요** |
| XS-12 | **변형별 E_total**(N3.7): 40 §2.4.9 E_total('실행 하나의 커널 평가 수 상한', 유일한 정의)과 §2.4.5 색인 상한 식의 '실행 하나' 단위를 '변형 하나' 단위로 바꾸고, 실행 전체 상한은 Σ_v E_total,v가 된다. 식(E_B + N_T + R)은 X-17 그대로다 | X-17, 40 §2.4.9·§2.4.5 | 확인 요청 |
| XS-13 | **S3 evals·runs 줄에 변형 정체 칸 추가**: 같은 topology 변형은 `context_fp`가 같아 줄만으로 구분되지 않는다(F-5). S3 줄 형식 변경은 앞서 사용자 승인으로 처리했던 종류다(X-10: 실패 줄 `snapshot_fp` 칸) | X-10 선례 | 확인 요청 |
| XS-14 | **M2 실행 시점**: S-4 원문은 'card A 진행 중 실측'인데, 실행은 card A 병합 뒤 master에서 한다(준비만 진행 중에). 근거: card A의 θ 좌표 왕복 수정(X-1 (1)) 전후로 θ 키가 달라진다(N6 M2-3·8). (v0.7.5 백로그 재감사 OS-B4: M2·OS-M 삭제로 대상 소멸) | S-4 | 보고(확인) |
| XS-15 | **국면 2 탐색 게이트 기간(OD-3, PD-2)**: TR-3~TR-5(국면 2 게이트 해제) 사이에는 승인된 파생 topology가 단계 A까지만 돌고 국면 2 탐색 미개방으로 멈춰 사이징되지 않는다. OT 원래 흐름에 없던 정지다(추적 행). **(v0.8)** 게이트 해제가 offset-trim TR-B(TR-5와 같은 통합 병합)로 옮겨 기간이 TR-3 ~ TR-5·TR-B 통합 병합까지로 늘어난다(부담 변형 C·C′가 실행 중 추가로만 생기기 때문) | OT §4·§14.1, T-2 | **수용됨(S-8)** -- v0.8 기간 연장은 작성자 유도, 검증·확인 대상. TR-5·TR-B 통합 병합 때 정지가 지워졌는지 확인한다 |
| XS-16 (v0.6) | **실행 계획 목록이 실행 중에 늘어난다**: 승인된 S-2·N3.5는 '실행 계획 = (topology 변형, 제약 집합) 목록'을 계획 함수가 실행 전에 만들었다. v0.6은 엔진 밖 구동기가 실행 중 변형을 추가한다(같은 topology + 문턱만 다름, N3.12). 사용자 결정 T-35(D-24 안 B)를 따르는 개정이고 원래 취지(재사용)에 더 가깝지만, 승인된 계획 문언을 바꾸므로 보고한다 | S-2, N3.5 | 승인(S-12, 사용자 "모두 권고대로 해") |
| XS-17 (v0.6) | **엔진 공개 진입이 둘이 된다**: W-1(S-9)은 `run_plan`을 사슬 진입점 정본으로 정했다. v0.6은 구동기가 쓰는 실행 계획 세션 인터페이스(열기·변형 실행·추가·닫기)를 더 연다. `run_plan`이 그 세션을 쓰는 얇은 진입이라 사슬 구현은 하나지만, 공개 API는 둘이다 | W-1 | 승인(S-12, 사용자 "모두 권고대로 해") |
| XS-18 (v0.6.1) | **S-3 경계(offset-trim X-23)**: S-3은 '엔진은 이전 실행 결과를 입력으로 받지 않는다'다. 보정 루프에서는 같은 세션 안 앞 변형의 결과를 오라클이 재고, 그 측정에서 나온 Δ_T가 구동기를 거쳐 다음 변형의 문턱 입력이 된다. 엔진은 결과 파일을 읽지 않고 입력 경로는 변형 추가 하나뿐이지만, 같은 실행 안 결과가 간접적으로 다음 입력을 정한다. 이것이 S-3 범위 밖이라는 해석(offset-trim X-23)을 확인받는다(상위 O-178 oracle 닫기 경계는 상위 Q-W1과 함께 -- offset-trim N3.8.7) | S-3 | 승인(S-12, 사용자 "모두 권고대로 해", X-23 수용 T-37) |
| XS-19 (v0.6.1) | **메모리 동시 점유(운영 조건)**: 보정 루프 동안 엔진 프로세스가 모든 반복의 색인을 쥔 채 오라클 프로세스가 돈다. 사용자 메모리 제약 아래에서 이 동시 점유를 운영 조건으로 받아들일지 확인받는다. 대응은 N9 메모리 행 | 사용자 메모리 제약(순차 실행 운영 원칙) | 승인(S-12, 사용자 "모두 권고대로 해") |
| XS-20 (v0.7) | **matching 합성 제약의 판정 위치 분리**(O-53 A2): S-1의 matching 판정 k·σ_in + \|V_id*\| ≤ `offset_in_max_v`(DEC-23 기호)는 한 판정으로 읽혔다. 계통 offset은 θ 프레임 봉인점에서 구조적 0이라 커널에서 잴 수 없으므로(gain-budget DEC-74 front 전용 예외, O-43 D1 (c)), 커널에서는 k·σ_in ≤ `offset_in_max_v`, front에서는 k·σ_in + \|V_id*\| ≤ `offset_in_max_v`를 ΔW 1차 값으로 재판정하고 단위 9 뒤 실현 W로 다시 판정하며, 위반 점은 front에서 빼고 비지배 재필터한다. trim 방식은 offset-trim 보정 구간으로 판정한다. **v0.7.4 재작성(상위 N6.35 E-05·U-108·O-118 1번·O-119, 사용자 대원칙 O-169 -- 원래 취지와 다름, 승인 O-170 -- 상위 승인 표 #23)**: '계통 offset은 θ 프레임 봉인점에서 구조적 0이라 커널에서 잴 수 없다'는 근거는 오류로 판명(O-118 1번) -- 커널에서도 k·σ_in + \|V_id*\|(성분 (1)(2))로 판정하고 front는 판정 W로 재판정한다(N3.3 S-1 행) | S-1 | **승인(O-53, 사용자 2026-10-20 "권고대로 진행해" -- 원래 취지와 다름 승인)** |
| XS-21 (v0.8) | **변형에 고정 θ 성분 칸**: 승인된 S-2 '변형 = (topology 변형, 제약 집합)'에 셋째 칸 '고정 θ 성분'(기본 빈 값, 부담 변형 C만 -- 출처 칸이 원본인 소자의 θ 성분 = 같은 실행 안 변형 O 선택 점 기록 참조)을 더한다. O-258 '같은 θ에서 원본만 변형 대 원본 + trim 변형 차'를 변형 틀로 재려면 원본 θ를 묶는 칸이 필요해서다(제약 집합으로 표현하면 θ 등식 제약을 발명해야 함). 변형 정체·중복 키에 그 지문이 든다 | S-2, O-258 | **원래 취지와 다름 -- 작성자 유도, 검증·확인 대상**(O-258 원문에 '변형 틀 재사용'만 있음) |
| XS-22 (v0.8) | **실행 중 추가 허용 종류가 셋**: 승인된 N3.12(XS-16)는 '같은 topology + 문턱만 다른 변형'만 추가를 허용했다. v0.8은 국면 2에서 (ii) 부담 변형 C(합성 회로, 고정 θ)와 (iii) 재풀이 변형 C′(합성 회로)를 더한다 -- topology가 처음 목록 변형(원본)과 다르다. 합성 회로는 세션 열기 때 승인 기록으로 이미 정해진 결정적 입력이라 '실행 중 새 topology'는 아니다. OS-L의 첫 소비자가 offset-trim TR-TL에서 TR-B로 바뀐다(같은 변경 원칙 그대로) | XS-16, N3.12, OS-L 행 | **원래 취지와 다름 -- 작성자 유도, 검증·확인 대상**(O-258 '부담 위반이면 원본 θ까지 재풀이'를 변형 추가로 구현) |
| XS-7 | **색인 수명 경계 문구**: 40 §2.4.5의 실행 경계(옛 문구 '`run_stage_a` 진입', XRUN-F1 card B 보완 뒤 '두 객체를 만드는 호출자'(PD-8))를 '실행 계획 진입'으로 바꾼다(승인 S-5). 수명 단위('실행 하나, 실행 사이에 넘기지 않음')는 그대로라서 원래 취지와 맞는다고 보지만, 승인된 design 문구를 바꾸므로 보고한다 | X-12, 원래 취지 문장 | 확인 요청 |

**사용자 몫(이 계획이 하지 않음)**: 기존 library spec을 요구 형식으로 옮기는 것(DS-U5).

---

## N6. 선행 실측(착수 조건)

### M1. 평가 캐시 키에 제약 집합이 들어가는가 -- **실측 완료(2026-10-16, base `067614c`, 읽기)**

* **결과**: 들어가지 않는다. 사실과 근거는 N3.0 F-1(키), F-2(결과의 제약 의존), F-3(S1v 입력)이다.
* **결정 항목**: 평가를 '크기·metric(제약 무관) + 판정(변형별)'로 나누려면 범위가 kernel(`E/search/kernel.py:130, :146-151, :159-161`)과 graph(`E/graph/s1v_fields.py:249-251`)로 넓어진다. 처리 선택지 (가)·(나)·(다)와 완료 조건 3과의 관계는 N3.1 표다. 셋 다 원래 취지와 다르거나(XS-8) 핵심 층을 바꾸므로(XS-5) 기본안을 두지 않고 사용자 결정으로 올렸다 -- 결정됨(O-176 Ⅵ (나), DS-1 -- 옛 S-14 (다) 번복; 옛 'M2 숫자와 함께' -- v0.7.5 백로그 재감사 OS-B4).

### M2. (삭제 -- v0.7.5 백로그 재감사 OS-B4)

matching과 trim 국면 1의 θ 겹침 측정(card OS-M)은 소비처가 없어 지웠다: 소비처였던 DS-1은 결정됐고(O-176 Ⅵ (나)) DS-2는 PD-3로 '대상 없음'이다. 메모리 위험은 N3.7 상한 식의 fail-closed와 XS-19(OS-L 반복당 색인 크기 측정)가 맡는다. 측정 방법 원문은 history.

---

## N7. 순서·의존·card 초안

### N7.1 순서(S-4)

NFR-4 card 2 병합 → XRUN-F1 card A → B → C → **실행 계획 구현(OS-2)** → trim TR-1. 이 계획 문서(OS-0 전 단계)는 card A 진행 중에 한다(옛 'M2 준비(OS-M)' -- v0.7.5 백로그 재감사 OS-B4로 삭제). **OS-V**(V-1, S-11)는 OS-2·gain-budget VB-1과 오라클 선행(oracle-portability OP-3, gain-budget EO-1, oracle-portability OP-5) 뒤, offset-trim TR-TL 앞이다.

**순서 정본**(감사 D1): 엔진 card 순서의 유일한 정본은 gain-budget N6.1이다. 이 계획 card(OS-2·OS-V·OS-5·OS-L·OS-3)의 N6.1 행 또는 인용 규칙은 gain-budget 쪽 개정 몫이고(감사 D1, 이 계획은 고치지 않음), 그 개정이 들어오면 이 절은 그 행을 인용한다. 그 전까지 이 절의 선후는 이 계획 card 사이의 선후다.

**OS-2와 gain-budget LA-1의 선후**(v0.7, 감사 C3; 상위 사용자 결정 O-183 -- 순서 LA-1 → OS-2 고정, 상위 N6.1 병합 순서 규칙 표 #8·#9, **원래 취지와 다름**(옛 '어느 쪽이 먼저든', 승인 O-183)): 두 card는 서로 데이터 선행이 아니다(OS-2 = 사슬 진입점 `run_plan`과 요구 경로, LA-1 = `find_front` 기본 경로를 층 0 손계산 조립으로 바꾸고 층 0 front 후보 점의 입력 창 다듬기 호출 자리를 더함 -- O-49 P4). 다음 규칙을 지킨다.
* **같은 통합 병합에 넣지 않는다**: OS-2(요구 없는 spec = 순수 리팩터링)와 LA-1(동작 변경)을 한 병합에 묶으면 변화표의 원인 귀속이 섞인다(O-38 (3)과 같은 원칙).
* **OS-2의 완료 조건 1 base** = OS-2의 실제 base master(병합 직전 master)의 수작업 사슬이다(XRUN-F1 card C 병합 뒤 master라는 옛 고정 문언을 대체, N7.2 'v0.5 반영'·완료 조건 1). 그 수작업 사슬은 LA-1의 `find_front`를 부르고, 비교 대상은 같은 base 위 `run_plan`이다.
* **LA-1 몫**: 하네스 관찰 지점(`find_front` 모듈 속성 `layer0_start`·`sweep_front` 감싸기, NFR-4 card 2 J-3·J-7 계약)이 LA-1a·LA-1에서 바뀌면 그 계약 갱신과 확인은 바꾸는 card 몫이다(출발 휴리스틱·실패 사슬 삭제와 진입점 `layer0_start`가 돌려주는 출발점 = 상위 card LA-1a, 진입점·`find_front` 소비는 유지 -- 상위 사용자 결정 O-214·상위 계획 검증 55 M55-2)(사슬 두 벌 금지, W-1).
* **OS-2는 LA-1 뒤다**: 하네스 관찰 지점은 LA-1 뒤의 것이고, OS-2의 사슬 값 노출 전수(N7.2 'v0.5 반영')는 그 base에서 하네스를 다시 읽어 만든다.
* 순서의 정본은 상위 N6.1 병합 순서 규칙 표다(O-183).

**OS-2 착수 조건**(v0.7.1, 사용자 O-61 P9):
* **(v, L)의 graph 자리가 먼저다**: matching 합성 행의 값 (v, L)은 결과 객체 칸이 아니라, 합성 행을 쓰는 블록의 graph 필드 `graph/metrics: constraint_rows` 값이다(40 §2.4.8 소유표 '제약 행' 행, writer = search 제약 블록 하나). 이 필드는 U17 ②로 이월됐었고(U17 ②는 상위 card 표 id가 아님), 미측정 값의 자리(40 §2.4.12 Q8)는 열려 있다. Q8은 '정하기 전에는 `constraint_rows`를 쓰지 않는다'고 적는다. Q8은 사용자 결정이 아니라 생산 card 상위 LA-1의 design이 닫는 design 열린 질문이다(원문 '② design 보완 때 정한다' -- 상위 N6.1 LA-1 행 'design 완료 조건', 기본안 = `constraint_rows` 행 안 상태 칸 `unmeasured` + 사유). 그래서 OS-2 착수 조건은 상위 LA-1 병합(Q8 닫힘 포함)이고, `constraint_rows` 필드와 writer는 **상위 card LA-1이 만들고 OS-2는 읽기만 한다**(순서 LA-1 → OS-2 -- 상위 N6.1 병합 순서 규칙 표 #9, 상위 사용자 결정 O-183; 옛 v0.7.5 OS-B9 '첫 소비자인 OS-2가 만든다'·'선후 고정 없음', **원래 취지와 다름**(승인 O-183)).
  * 그 전에 과도기 자리를 두지 않는다. `EvalResult` 값 칸은 사본이고 지울 대상에 새 소비자를 다는 것이라 금지한다. 결과 JSON을 쓸 때 (v, L)을 다시 계산하는 길도 둘째 생산자라 금지한다(프로젝트 CLAUDE.md 'graph 단일 정본' 규칙 1·2).
* **design 개정이 먼저다**: 지금 design(`docs/02-design/features/offset-strategy.design.md` v0.2.6, 브랜치 `design/offset-strategy-ss1` `50d33b8e`, 머리 `plan_version: 0.6.2`)의 커널 합성 행은 계획 v0.6.2 식 v = k·σ + \|V_sys\|다. 계획 N3.3(v0.7.4 -- 상위 U-108)은 같은 식 k·σ_in + \|V_id*\| ≤ 문턱을 커널(V_id* 성분 (1)(2))과 front 재판정(판정 W, 성분 (3) 더함) 두 자리에서 판정한다. 새 계획 결정은 없고, design을 이 계획 v0.7 기준으로 개정한다(O-61 'offset-strategy design v0.7 개정', S-7 순서: 계획 → design). design이 고칠 것은 다섯이다.
  1. 커널 행을 단일 항 k·σ_in으로 한다. 분해능 규칙도 항 하나다.
  2. front 판정 자리를 적는다(DEC-74 자리의 소비자, N7.2 OS-2 행).
  3. front 판정 값은 front 점 자신의 스냅샷에서 읽는다(값 사본 없음).
  4. 기호 \|V_sys\|를 부호 있는 V_id*의 크기 \|V_id*\|로 바꾼다(gain-budget DEC-23, O-50 G1).
  5. 스냅샷 파생 규칙 점검 문단(design v0.2.6 129행)의 남는 필드 표기 '`_CONTEXT_WRITERS`(`S1_WRITERS` ∪ `PLAN_WRITERS`) ∪ 그 평가의 호출 블록'을 사용자 결정 O-61 P1 규칙 '`ctx.base`에 있는 writer ∪ 그 평가가 부르는 블록'으로 바꾼다(정본 gain-budget v6.22 N3.3 '스냅샷 파생 규칙', `de301d2d` 422행). 인용만 하고 이 계획에서 규칙을 다시 적지 않는다.

  개정된 design의 독립 검증·사용자 승인은 N7.2 '공통 착수 조건' 그대로다.

  **design 개정 때 확인할 항목**(결정이 아니라 점검 대상, v0.7.1 검증 N4):
  * N7.2 'v0.5 반영' W-1의 단계 B 진단 모드 표지(이 계획 491행 '결과에 그 표지를 싣는다'): `run_plan` 결과는 단계 B 보고서의 `diagnostic` 칸(`stage_b.py:129`)을 참조해야 하고 둘째 칸을 만들지 않는다(graph 단일 정본 규칙 4). design이 그 참조 자리를 적는다.
  * 같은 절 사슬 값 노출 목록의 `sctx.cache`(494행): 정본은 S3 메모리 색인의 평가 키 부분이고 `sctx.cache`는 지울 대상이다. design 개정 때 노출 자리가 그 색인 참조인지 확인한다.

* **(v0.7.3) 계획 착수 조건 보강 -- 사용자 승인 대상**(근거: gap 재분석 `wt/_drafts/evidence/2026-10-21/os_design_v032_plan_gap.md` §5 1·2, N7·N17):
  * **PS-1 잔여 -- DEC-74 front 판정 기록의 자리가 먼저다**: 커널 행 ①·front 합성 판정 ②(N3.3)의 기록(위반 점·정의 불능 점과 원인 참조)의 **자리 종류**는 정해졌다 -- 출력 기록(gain-budget v6.24 병합 `59ecc88e` DEC-74·N3.3 (b), 사용자 결정 O-68 (3); graph 규칙 6, O-62 (2) P10 선례 -- 'N3.3 정본 자리부터 계획에 명시'). **이름**은 gain-budget card DE-1 design 또는 착수 실측이 정한다(DEC-23 'front 판정' '자리 이름은 착수 실측'). 그 이름이 정해지기 전에는 OS-2를 시작하지 않는다. 이유: 정본 자리가 없으면 만들지 않는다(프로젝트 CLAUDE.md 'graph 단일 정본' 규칙 6). OS-2가 임시 기록 칸을 두면 그것이 둘째 자리가 된다(규칙 1·3). 이 계획은 자리를 정하지 않는다. 종류는 gain-budget v6.24가 정했고(O-68 (3)), 이름은 gain-budget card DE-1의 몫이므로 오케스트레이터의 gb 알림 대상이다(N10.4).
  * **PS-7 -- S3 색인 평가 키 부분의 열거 API는 상위 LA-1이 만든다**(순서 LA-1 → OS-2 -- 상위 N6.1 병합 순서 규칙 표 #8, 상위 사용자 결정 O-183; 옛 '먼저 병합되는 card'(상위 v6.38.4 열일곱째 커밋 계획 검증 6 n-1)): 열거 대상 = S3 색인 평가 키 부분(design 40 398-402 `S3Index.get·failure·local·solved`; as-built `sctx.cache` -- 지울 슬롯 위에 API를 쌓지 않는다). 그 평가 키 부분·이 읽기 전용 `seq` 열거 API·계수(G-10 원천 -- 고유 키 수 = 정의역 안 평가 항목 수(정의역 밖 seq −1 결과는 담되 세지 않음), 평가 수 = `kernel_calls`, 열거 순서 = (seq, EvalKey 정준) -- 상위 LA-1 범위 15 (iv) (다) 정의, 상위 v6.38.4 열여덟째 커밋 계획 검증 7 m7-1; 같은 키 = 재등록 거부)·분할은 **한 제작 단위로 상위 LA-1이 만든다**(상위 LA-1 범위 15 (iv), 상위 N6.1 병합 순서 규칙 표 #8). OS-2는 읽기만 한다. 하네스 사슬 대체(W-1, O-63 (3) 읽기 길 -- N3.12)는 열린 세션에서 평가 결과 전수(`seq` 순)를 읽어야 한다. 그래서 그 열거 API는 **소비자(하네스)를 대체하는 OS-2보다 먼저 상위 LA-1이 만들고, OS-2는 그 API로 하네스를 대체한다**(상위 N6.1 병합 순서 규칙 표 #8)(v0.7.5 백로그 재감사 OS-B8 -- 옛 착수 조건 'U17 ② design이 정한 뒤'는 삭제, U17 ②는 상위 card 표 id가 아님). 40 §2.4.5 조회 API 개정안은 OS-0 design 개정이 낸다(N10.4 PS-7). 이유: 그 API가 없으면 하네스를 대체할 수 없다(만들면 배선). OS-2가 평가 목록 사본·dict를 따로 두는 것은 graph 규칙 2·6 위반이라 대안이 아니다.
  * **점검 항목(결정 아님)**: OS-2 세션의 `open_run` 호출은 XRUN-F1 card C의 최종 서명(`S3Index`의 필수 상한 인자)을 따른다. 그 상한 인자가 단계 A·B보다 먼저 정해져야 하는지(PS-6과 같은 꼴의 순환 가능성)를 OS-2 착수 전에 확인한다. 이 계획은 순서를 정하지 않는다. 순환이면 design·40 §2.4.5 소유자 몫으로 올린다(계획 문언이 필요하면 S-7로 계획부터).

**권고안(XS-11, 승인 필요)**: S-4의 '실행 계획 구현'을 둘로 나눈다.
* **TR-1 앞(OS-2, 옛 OS-1 합침)**: 단일 변형 실행 계획(요구 없음·`matching`)과 trim·compare 거부까지. 국면 규칙·승인 기록 로더·낡은 승인 정지는 여기에 넣지 않는다. 이 셋은 trim·compare에서만 쓰이고, 그 방식은 이 card에서 거부되기 때문이다. OT §4의 단계 선택 흐름은 코드에 없으므로(F-7) 이 card에서 대체할 옛 코드 경로도 없다. OT §4 개정은 design 문서에서만 한다(N3.9). 이 범위는 병합 즉시 엔진 사슬 진입점(`run_plan`, W-1)과 그것을 부르는 하네스·test에서 쓰인다(`matching` 요구 spec, 요구 없는 spec).
* **trim·compare를 처음 여는 TR card에 묶음(OS-5)**: 다변형 실행(변형 사이 공유), 변형 정체 칸(S3·결과 JSON), Σ 색인 상한(N3.7)과 card C `S3Index` 인터페이스 변경(PD-7), 공통 판정 검사(PD-6), DS-1 처리. 이 경로를 쓰는 변형은 trim·compare뿐이라 TR card 전에 만들면 쓰는 곳이 없다(만들면 배선, NFR-S7).
* **국면 2 일의 TR card별 배정(PD-2, N3.5)**: TR-2 = '승인 기록 없음 → 국면 1'과 '승인 파일이 있으면 국면 2 미구현으로 fail-closed', TR-3 = 승인 기록 로더·결속·낡은 승인 정지·국면 2 분기, TR-4 = 구조 동일 검사, offset-trim TR-5 안의 국면 2 게이트 해제((v0.8) → TR-B, TR-5와 같은 통합 병합 -- N3.5).
* **대안 (ii)**: 다변형 경로를 TR-1 앞에 다 구현하고, TR card 전까지는 fixture spec으로만 실행하는 것을 사용자 승인으로 받는다.

추가 의존:
* matching front 판정의 V_id*는 offset 기준이 있어야 정의된다. 기준의 정의 자리는 gain-budget DEC-23 하나다(O-53 B3: spec 선언 기준 종류 셋, 차동 출력 V(p) − V(n) = 0 기본, 선언 없는 단일 출력은 정의 불능). 선언 없는 단일 출력 회로는 N4-3 사유로 멈춘다(fail-closed). '출력 기준 DC' 기능(T-19~T-23, XRUN-F1 뒤·TR-6 전)과의 관계는 offset-trim 계획이 정본이다. OS-2의 검증 fixture는 기준이 이미 정의되는 회로로 고른다. **F-1(사용자 승인 S-9)**: library current_reuse_telescopic_ota의 사본이다. 차동 출력이라 단일 출력 기준 DC 검사(design L4)에 걸리지 않는다. 사본은 library 밖 fixture 위치(`origin: fixture`, 저장소 안, T-28 선례 `assets/fixture/` 계열)에 둔다. 사본 spec은 offset 판정 제약 둘(`offset_in_sigma_mv`, 그것을 참조하는 `offset_sys_mv`)을 요구 `offset_requirement`로 바꾼다. 값은 사용자 승인 값으로 {`strategy`: matching, `coverage_multiple` = 3, `offset_in_max_v` = 3 × 3.3 mV}이고, 3.3 mV는 사용자 결정 2026-10-08 Q3 (2)에서 왔다. 값마다 출처(사용자 결정)를 spec `source`에 적는다. library spec은 바꾸지 않는다(DS-U5). **비교 한계**: 이 요구(커널 3·σ_in ≤ 3 × 3.3 mV, front 3·σ_in + \|V_id*\| ≤ 3 × 3.3 mV, O-53 A2)는 library 원 제약(σ_in ≤ 3.3 mV이고 \|V_id*\| ≤ 3.3 mV)과 같은 제약이 아니다(커널 몫은 값이 같지만 front 합성 판정이 다르다). 그래서 fixture 결과를 library 기준선과 비교할 수 없다. fixture 판정은 OS-2 완료 조건(유도 제약·로더·출발값이 실제 경로에서 동작함)에만 쓴다.
* trim·compare 변형은 TR card(TR-1 → … → TR-6)가 경로를 만든 뒤에 열린다(N3.5 마지막 항목). TR-2 병합은 OS-2(제품 진입) 뒤다(T-15, 상위 v6.38.4 열여섯째 커밋 계획 검증 5 m-2).

### N7.2 card 초안

**공통 착수 조건**: N7.1 순서. design 문서 `docs/02-design/features/offset-strategy.design.md`가 있고 독립 검증과 사용자 승인을 받았다(bkit PDCA). 그 card가 읽는 N10 결정이 닫혀 있다.

| card | 범위 | 선행 | 읽는 결정 |
|---|---|---|---|
| OS-0 (문서) | design: 요구 스키마·사유 코드·유도 제약의 metric/행 형식(G-S1)·출발값 규칙(G-S2)·변형 유도 제약의 별도 입력 `derived`(N3.10, PD-1)·`RunPlan` 형식·계획 함수와 실행기 서명·결과 JSON 칸·비교 도구 위치와 칸·예산 식·파일 분할·배선표·test 목록. OS-5 몫(변형 정체 지문·S3 변형 칸·Σ 상한)은 형식만 정한다. OT §4·§5.1·§5.2·§9.4·§9.5·§10.1과 40 §2.4.5 수명 문구 개정안, T-27·T-28 시험 회로 spec 재작성안(XS-9)을 같이 낸다. 독립 검증. **(v0.7.5 백로그 재감사 OS-B10·B5·B8) design 개정 `plan_version` 0.7.5**: v0.7.4(상위 E-05 V_id* 세 성분 재작성)·v0.7.5(P1 S-10 검사 자리) 개정분 반영, PS-6 순환을 푸는 40 §2.4.5 '수명' (1) 문언안(OS-5 착수 조건, OS-B5), S3 색인 평가 키 부분 열거의 40 §2.4.5 조회 API 개정안(OS-2 범위, OS-B8). **완료 측정**: design↔계획 gap 0 | 이 계획 승인(옛 선행 'M2 결과'는 OS-B4로 삭제) | XS-1~XS-15·XS-20, DS-1·DS-2, DS-U1~DS-U9, DS-T1, PD-1~PD-9, W-1, F-1, V-1, O-53 A2·B3 |
| OS-2 (옛 OS-1 합침) | 한 card로 함께 병합한다. 옛 OS-1의 유도 제약·G-S1·G-S2는 유도 제약 입력(`derived`)이 있어야 탐색에 들어가기 때문이다(나눠 병합하면 앞 card의 함수가 쓰이지 않는다).<br>• 요구 스키마 로더(N3.2, `offset_trim` 단독 거부 포함)<br>• matching 유도 제약(N3.3, G-S1 핵심 층 확장), 출발값(G-S2)<br>• 유도 제약의 별도 입력 `derived`(`build_search_context` 키워드와 전달 자리, N3.10·PD-1·PD-4)<br>• 파이프라인 층 재작성(단일 변형): `build_run_plan`(요구 없음·`matching` 행 + trim·compare fail-closed 거부, 승인 기록 입력 없음), 실행기 `run_plan`(엔진 사슬 진입점 정본, 하네스·test 수작업 사슬 대체, W-1. v0.7.2 O-63 (3): 실행 수명 값을 읽는 하네스는 같은 세션의 공개 API를 쓰므로, 세션의 열기·변형 실행·읽기·닫기는 이 card에 있고 OS-L은 변형 추가를 더한다), 블록 결과 색인·`RunCounters` 수명을 실행 계획 진입으로(`run_stage_a` 필수 키워드, PD-8), 결과 JSON<br>• 요구 없는 spec 무동작. 진입 흐름을 바꾸는 부분의 옛 코드는 같은 변경에서 지운다<br>• 공통 판정 검사(N3.4)는 이 card에 없다(OS-5, PD-6)<br>• (상위 v6.38.4 열다섯째 커밋 계획 검증 4 M-1) S3 색인 평가 키 부분·읽기 전용 `seq` 열거·계수·분할(한 제작 단위 -- 상위 LA-1 범위 15 (iv)) -- 상위 LA-1이 만들고 이 card는 읽는다(순서 LA-1 → OS-2 -- 상위 N6.1 병합 순서 규칙 표 #8, 상위 사용자 결정 O-183; 옛 'OS-2가 상위 LA-1보다 먼저 병합되면 이 card가 만든다'; 정의 참고: `sctx.cache`·`computed_keys` 삭제; 조회 = 커널 적중, 열거 = `find_front` note·하네스, 계수 = 고유 키 수 = 정의역 안 평가 항목 수(정의역 밖 seq −1 결과는 담되 세지 않음), 평가 수 = `kernel_calls`, 열거 순서 = (seq, EvalKey 정준) -- 상위 LA-1 범위 15 (iv) (다) 정의, 상위 v6.38.4 열여덟째 커밋 계획 검증 7 m7-1·같은 키 재등록 거부(fail-closed) -- G-10 '같은 키 재계산 0' 측정 유지; 완료 = 엔진 `git grep` `sctx.cache`·`computed_keys` 0·library 13회로 결과 같음(순수 리팩터링 필드별)·재등록 거부 toy·같은 키 재계산 0)<br>• (상위 v6.38.4 열다섯째 커밋 계획 검증 4 M-2 -- 상위 옛 DF-18) **진입점 종료 코드·결과 기록**(**card 성격 확장 -- 원래 취지와 다름**, 상위 v6.38.4 열여섯째 커밋 계획 검증 5 m-6: 단일 변형 실행 계획 card가 제품 진입 계약을 가져감): `run_plan` 진입이 상위 N3.14 분류 예외를 `exit_code_for`로 프로세스 종료 코드(비0)에 싣고, 탐색까지 간 실행은 결과 JSON에 θ*·실패 레코드를 쓴다; 구조 규칙 F 예외 파일 = 그 진입점 파일(상수 `BROAD_EXCEPT_ENTRY_FILE` 갱신 -- 옛 `pipeline/entry.py`는 엔진에 없음). **완료 측정**: 분류마다 합성 실패 픽스처 → 종료 코드 = N3.14 표 값, 결과 JSON θ* 칸, 규칙 F 예외 1곳 = 진입점<br>• (v0.7.5 백로그 재감사 OS-B8 -- PS-7) S3 색인 평가 키 부분의 읽기 전용 열거(`seq` 순)를 세션 공개 API에 둔다(참조 읽기, 사본·결과 객체 칸 0 -- O-63 (3)); 하네스는 그 API로 읽는다. **완료 측정**: 하네스가 그 API로 읽음, `sctx.cache` 직접 읽기 grep 0<br>• (v0.7.5 백로그 재감사 OS-B9 -- **원래 취지와 다름**, 상위 v6.38.4 승인 대기 BL-OS-B9) `graph/metrics: constraint_rows` 필드와 writer(search 제약 블록 하나)는 상위 LA-1이 만들고 이 card의 matching 유도 제약 행은 읽기만 한다(writer 하나 -- 상위 N6.1 병합 순서 규칙 표 #9, 상위 사용자 결정 O-183, 옛 OS-B9 '이 card가 만든다' 대체). **완료 측정**: writer 1곳(상위 LA-1), `EvalResult` 값 칸·결과 JSON 재계산 0<br>• (v0.7, O-53 A2) matching 판정 두 자리: 커널 행 k·σ_in ≤ 문턱(G-S1 ①)과 front 합성 판정(G-S1 ② -- gain-budget DEC-74 front 판정 자리의 소비자, 위반 점 제외·비지배 재필터, 정의 불능 점(A_dc 갈래·커널 출발 창 미수렴) 제외·원인 = 그 사유 -- v0.7.3, N3.3 ②, O-63 (1)·O-64 (2)). 단위 9 뒤 실현 W 재판정은 단위 9 card가 그 자리를 다시 부를 때 같은 소비자가 돈다(이 card는 단위 9를 만들지 않는다)<br>**변경 종류**(감사 E1·D2, O-34 (1) -- 정본 gain-budget N6.3): 요구 없는 spec = **순수 리팩터링**(완료 조건 1, 필드별), matching 요구 spec = **동작 변경**(완료 조건 10). 동작 변경 판정의 SPICE 다리는 gain-budget EO-1(N6.20)을 **완료 판정 선행**으로 둔다(병합 선행 아님, N6.3 (iii)·(iv)). EO-1·OP-5·OS-V 전에는 그 다리가 '보류'이고(N6.3 (i)), 합성 판정은 판정 소비자가 있으므로 '대상 없음'(N6.3 (ii))으로 세지 않는다 -- 그동안 이 card는 미완료이고 병합 여부는 오케스트레이터가 사용자에게 올린다 | OS-0(계획 v0.7 기준 design 개정 포함, N7.1 'OS-2 착수 조건'), XRUN-F1 C, F-1 fixture, 40 §2.4.12 Q8(상위 LA-1 design이 닫음 -- 사용자 결정 아님; v0.7.1 O-61 P9; `constraint_rows` 필드·writer는 상위 card LA-1이 만듦, 상위 사용자 결정 O-183), gain-budget card LA-1(`constraint_rows`·S3 색인 열거 API 생산 -- 순서 LA-1 → OS-2, 상위 N6.1 병합 순서 규칙 표 #8·#9), gain-budget card DE-1(범위 (c) 포함 -- 순서 LA-1 → DE-1 → OS-2, 상위 N6.1 병합 순서 규칙 표 #2; 옛 'U17 ②와 같은 통합 병합인 LA-1의 선행'은 낡은 문언(O-126 안 B·O-183과 어긋남), gain-budget v6.23 병합 `294bde4d`; (c)가 DEC-23 'A_dc 정의 불능 갈래' 판정 자리를 고친다, v0.7.3 명시), **(v0.7.3, 계획 착수 조건 보강 -- 사용자 승인 대상)** PS-1 잔여(DEC-74 front 판정 기록 -- 자리 종류 = 출력 기록(gain-budget v6.24 병합 `59ecc88e` DEC-74·N3.3 (b), O-68 (3) -- 정해짐), 이름 = card DE-1 design·착수 실측)(PS-7 열거 API는 선행에서 빼 이 card 범위로 -- v0.7.5 백로그 재감사 OS-B8), `open_run` 서명 점검(점검, 결정 아님 -- N7.1 'OS-2 착수 조건'). 완료 판정 선행: gain-budget EO-1(SPICE 다리), oracle-portability OP-5·이 계획 OS-V(합성 판정 오라클 다리) | XS-1·XS-6·XS-7·XS-9·XS-10·XS-11·XS-20, DS-U1~DS-U3, PD-1·PD-4·PD-5·PD-8, W-1, F-1, O-53 A2·B3, O-34 (1), O-61 P9, O-62 (3), O-63 (1)·(3), O-64 (2) |
| OS-V (V-1, S-11) | matching 합성 판정(커널 k·σ_in ≤ 문턱, front k·σ_in + \|V_id*\| ≤ 문턱 -- O-53 A2)의 `verified_by`를 붙인다.<br>**범위(v0.7 경계, 감사 D3)**: **합성 판정 행의 결속만**이다.<br>• 엔진 쪽: 합성 판정 행(커널 행과 front 합성 판정)을 그 구성 metric의 오라클 measure에 결속한다.<br>• 판정 대조: matching σ_in·V_id*를 오라클 값과 대조한다. 엔진과 오라클 중 한쪽만 'A_dc 정의 불능 갈래'가 발동한 점은 값 오차가 아니라 '정의 경계 불일치'로 검증자 변화표에 적는다(범주 이름·정의 = oracle-portability N3.9 `offset_sys_mv` 행 (vi), v0.6.13 병합 `20532810`, 인용만; gain-budget DEC-23; v0.7.3, O-63 (2)).<br>**인용(이 card가 하지 않음)**: `offset_sys_mv`(V_id*)의 `verified_by` = `SPICE_ORACLE` + OP-5 measure 연결은 gain-budget card VB-1(N6.18)이 한다. OS-V는 VB-1을 선행으로 인용하고 그 행을 다시 만들지 않는다.<br>**재사용(새로 만들지 않음)**:<br>• oracle-portability OP-5의 계통 offset `.dc` 측정(부호 있는 V_id* 칸. 이 측정을 온도 조건에서 돌린 것 하나가 PC-10이다 -- O-53 B3. 공칭 MC 표본 offset은 V_id* 출처가 아니다 -- oracle-portability OP-5·PC-10 행, offset-trim G-15·N3.8 'matching의 V_id*(T) 측정'과 같은 문언, v0.7.2 정렬)<br>• V_id* 정의 = gain-budget DEC-23(offset-trim 쪽 정의 인용도 DEC-23으로 간다, 감사 A1)<br>• 불일치 σ의 A = `.tf`(OP-5, O-43 D1 (d))<br>• 오라클 MC = 시뮬레이터·PDK 네이티브 MC(O-1). 크기 확인은 그 계획대로 TR-7에서 엔진 σ 대 오라클 MC σ로 한다.<br>**만들지 않는 것**: 오라클 코어(O/core) 파일은 만들지 않는다. oracle-portability와 파일이 겹치지 않는다.<br>이 card 전까지 합성 판정 metric은 `spice_unverifiable` 목록에 나간다.<br>**변경 종류**: 동작 변경(대조 대상이 바뀜, O-34 (1)) -- VB-1 완료 조건과 같은 꼴(정의 이름 대조 test, 검증자 변화표, 결정성) | OS-2, gain-budget VB-1, 오라클 선행 oracle-portability OP-3·gain-budget EO-1·oracle-portability OP-5(감사 D4) | V-1, N3.11, O-53 A2·B3, O-63 (2) |
| OS-L (v0.6, offset-trim TR-TL과 함께 → **v0.8: offset-trim TR-B와 함께**) | 실행 중 변형 추가(N3.12 -- v0.8 허용 종류 (i) Δ_T 문턱·(ii) 부담 변형 C·(iii) 재풀이 변형 C′, 고정 θ 성분 칸 XS-21): 실행 계획 세션의 변형 추가(세션의 열기·변형 실행·읽기·닫기와 `run_plan`의 세션 사용은 OS-2에 있다 -- v0.7.2, O-63 (3)의 귀결), 추가 허용 범위 검사(fail-closed), 추가 때 E_total,v·B_S0·색인 상한 갱신(card C `S3Index`의 '늘리는' API 변경 -- card C test를 같은 변경에서 고치고 기본값 인자로 피하지 않음, PD-7과 같은 원칙), 변형 정체에 반복 번호·원인 지문.<br>**만들면 배선**: (v0.8) 변형 추가를 처음 쓰는 것은 부담 변형 구동기(offset-trim TR-B, 종류 (ii)(iii))이므로 TR-B와 **같은 변경**에서 병합한다(옛: 처음 쓰는 것은 보정 루프 구동기라 TR-TL과 같은 변경 -- XS-22). 종류 (i)은 TR-TL이 둘째 소비자로 쓴다. offset-trim 계획(`trim-plan-r1` 512행 부근)은 이 인터페이스를 TR-TL의 '선행'으로 적었으나, 이 계획의 문언('같은 변경')이 맞다. 그 계획에는 정정 알림이 간다(오케스트레이터 전달). matching 루프도 T-30 순서로 TR-TL과 같이 열린다(DS-T1).<br>**병합 전 측정**: 반복당 색인 크기(바이트)를 잰다(N9 메모리 행) | OS-5(다변형 공유), DS-1 결정, D-25 결정(인터페이스 서명), XS-18(X-23) 확인, (v0.8) offset-trim TR-5(같은 통합 병합), XS-21·XS-22 확인. 옛 선행 OS-V·TR-7은 종류 (i)(Δ_T, TR-TL) 쪽 선행으로 TR-TL 행에 남는다 | XS-16·XS-17·XS-18·XS-19, XS-12·XS-13, T-35 |
| OS-3 | 읽기 전용 비교 도구(N3.8). **TR-1 뒤, trim 국면 2(TR-6) 병합 뒤**에 한다. 비교 입력인 trim 국면 2 결과 JSON은 TR-6 뒤에야 생기기 때문이다(그 전에 만들면 쓰는 곳이 없다) | OS-2, OS-5, TR-6 | XS-3 |
| OS-5 (TR card에 묶음) | **TR-1 뒤**, trim 국면 1을 처음 제품 경로에 여는 TR card(TR-2, OS-2 뒤, T-15 -- 상위 v6.38.4 열여섯째 커밋 계획 검증 5 m-2)와 함께:<br>• 다변형 실행(compare 국면 1 = matching + trim 국면 1), 변형 사이 공유, DS-1 = (나) 처리(kernel 요청 출처·판정 행 자리 -- 핵심 층 변경)<br>• 변형 정체 칸, Σ 색인 상한과 card C `S3Index` 인터페이스 변경(B_S0, PD-7), 변형별 예산<br>• 공통 판정 검사(N3.4, DS-U4, PD-6)<br>국면 2 일은 N3.5 TR card별 배정(PD-2)을 따른다: TR-2 = '승인 기록 없음 → 국면 1'과 '승인 파일이 있으면 국면 2 미구현으로 fail-closed', TR-3 = 승인 기록 로더·결속·낡은 승인 정지·국면 2 분기, TR-4 = 구조 동일 검사, offset-trim TR-5 안의 국면 2 게이트 해제((v0.8) → TR-B) | OS-2, TR-2, DS-1 결정, XS-12·XS-13 확인 | XS-4·XS-5·XS-8·XS-11·XS-12·XS-13, PD-2·PD-6·PD-7 |
| (TR 연결) | TR card가 trim 국면 1·2 변형을 계획에 연결하고 거부를 푼다. 범위 조정은 OS-0의 OT 개정안이 정한다. (v0.8) 국면 2 = TR-3(합성 회로 단계 A) → TR-5·TR-B 통합 병합(부담 변형·게이트 해제, OS-L 같은 변경). card 목록·순서 정본은 offset-trim v0.7 N5(TR-* 전부 LA-1 뒤) | 각 TR card 선행 그대로 | XS-2·XS-4·XS-21·XS-22 |

**TR-1 앞/뒤**: OS-0·OS-2는 TR-1 앞, OS-5는 TR-1 뒤(TR-2와 함께), OS-3은 TR-6 뒤다.

**v0.5 반영**(N11):
* **W-1 (i)(사용자 승인 S-9)**: OS-2의 `run_plan`이 엔진 사슬 진입점의 정본이다. 하네스(`tests/integration/nfr4_run_dump.py` 등)와 test의 수작업 사슬(`run_stage_a` → `run_stage_b` → `build_kernel_context` → `build_search_context` → `find_front`)을 같은 변경에서 `run_plan` 호출로, 또는 실행 수명 값을 읽어야 하는 하네스는 같은 세션 인터페이스 호출(열기 → 변형 실행 → 읽기 → 닫기 -- v0.7.2, O-63 (3))로 대체하고 옛 수작업 사슬을 지운다. 제품 진입(종료 코드·θ* 기록)도 `run_plan`에 둔다 -- OS-2 범위(상위 v6.38.4 열다섯째 커밋 계획 검증 4 M-2; 옛 'U16은 나중에 제품 CLI를 `run_plan`에 배선' -- U16은 상위 card 표에 없는 이름이라 정리, 사슬을 두 벌 두지 않는다). design이 정할 요구(검증 B-1):
  * 단계 B 진단 모드: 하네스는 `run_stage_b(..., diagnostic=True)`를 부르고(`nfr4_run_dump.py:387`) 보고서 `diagnostic` 칸(`stage_b.py:129`)을 쓴다. `run_plan`은 진단 모드를 같은 뜻(측정만 하고 단계 A 상태·exit code 유지)으로 단계 B에 넘기고 결과에 그 표지를 싣는다.
  * 사슬 값 노출: 하네스가 지금 사슬에서 읽거나 넘기는 값 **전부**에 자리가 있어야 한다. 입력은 `run_plan`·세션 열기가 같은 뜻으로 받고, 결과는 읽기 전용 참조로 낸다. **블록 결과 색인·donors·계수에 닿는 값**(아래 평가 키 부분)은 세션이 열린 동안 공개 세션 API로만 읽고, 결과 객체(`run_plan` 결과·변형 결과)에는 그 참조를 두지 않는다(v0.7.2, O-63 (3) -- N3.12 ④ '닫기 = 버린다', graph 규칙 2 실행 수명). 그 밖의 값을 결과 객체에 둘지 열린 세션 API로 낼지는 design이 정한다. 목록은 design이 하네스를 전수로 읽어 만든다. 지금 보이는 것(`nfr4_run_dump.py:316-329, :377-424`)은 다음과 같다.
    * 단계 A의 `code_fp`, 단계 A·B `report_paths`, 단계 A·B S1 스냅샷 지문
    * `sctx.context_fp`, `sctx.cache`(XRUN-F1 card B와 상위 LA-1(범위 15 (iv)) 뒤에는(상위 N6.1 병합 순서 규칙 표 #8) S3 메모리 색인의 평가 키 부분 -- F-5. 열린 세션의 공개 API로만 읽고 사본·결과 객체 칸을 만들지 않는다, O-63 (3). 전수 열거 API는 N10.4 PS-7), `sctx.domain.w_min_m`, `sctx.dc.base`
    * `find_front` 결과 객체(front는 탐색 결과라 변형 결과의 읽기 전용 참조로 낼 수 있다 -- N3.12 'D-25·D-20' 행 확인)
    * 입력 쪽: `LutMemo` 크기 인자, S3 루트, `settings` 전달
    * `find_front` 모듈 속성(`layer0_start`·`sweep_front`)을 감싸는 관찰 방식. 이 관찰 지점 계약(NFR-4 card 2 J-3·J-7)이 `run_plan` 경로에서도 그대로 동작해야 한다.
  * 완료 조건 1의 base 사슬(v0.7, 감사 C3): base = **OS-2의 실제 base master**(XRUN-F1 card C 병합 뒤이고, gain-budget LA-1이 먼저 병합됐으면 그것도 포함)의 수작업 사슬(위 순서, 하네스와 같은 인자·같은 진단 설정)이다. 비교 대상은 OS-2 병합본의 `run_plan`이다. LA-1과의 선후 규칙은 N7.1 'OS-2와 gain-budget LA-1의 선후'.
* **F-1(사용자 승인 S-9)**: OS-2 검증 fixture는 N7.1 '추가 의존'의 F-1 문단이다. OS-2 선행 조건이다.
* **승인됨(S-8)**:
  * PD-1·PD-2·PD-6·PD-7은 위 card 표 본문에 반영했다. TR-3~TR-5(국면 2 게이트 해제) 사이 승인 회로가 사이징되지 않는 기간(OD-3)은 수용됐다(N5 XS-15). (v0.8) 그 기간은 TR-5·TR-B 통합 병합까지다(XS-15 v0.8).
  * PD-8: `run_stage_a`는 `donors`·`counters`를 필수 키워드로 받는다. 40 §2.4.5 '전달' 행 개정이 필요하다(N3.9). card B가 아직 코드에 들어가지 않았으면 card B design 쪽을 먼저 고쳐 서명을 두 번 바꾸지 않는다. 이미 들어갔으면 OS-2가 바꾸고 card B·C의 `run_stage_a` 호출 test를 같은 변경에서 고친다.

완료 조건이 걸리는 card: 1·5·7·8·10은 OS-2부터(10의 오라클 다리는 OS-V 뒤에 닫힘), 2·3·4는 OS-5부터(변형이 둘 이상인 계획이 생길 때), 6은 OS-3, 9는 OS-L((v0.8) offset-trim TR-B와 함께 -- 종류 (ii)(iii); 종류 (i) 몫은 TR-TL에서 다시 확인).

**완료 조건**(기능 전체). **변경 종류 표시**(v0.7, 감사 E1, O-34 (1) -- 판정 기준 정본은 gain-budget N6.3 '변경 종류별 판정 기준', 인용만): 조건 1 = **순수 리팩터링**(필드별), 조건 2·9 = **결정성**(비트 동일 유지 -- 같은 코드·같은 입력에서 계획 안 실행과 단독 실행을 비교), 조건 10 = **동작 변경**. 결정성 비트 동일(같은 코드·환경·입력 두 번 실행)은 모든 card에서 항상 검사한다. 조건 3~8은 계수·거부·배선·정합 확인이라 변경 종류 판정 대상이 아니다.
1. **요구가 없는 실행**에서 library 13회로 결과가 base와 같다. 변경 종류 = **순수 리팩터링**: 필드별로 판정한다 -- 이산 판단은 정확히 같고, 연속값은 기존 선언에서 유도한 분해능 이내(NFR-4, O-34 (1))(옛 문언 '비트 동일'은 history). 비교 제외 범위(PD-5, S-8):
   * spec 지문(`spec_fp`·`section_fps`)은 **제외하지 않는다**. 요구 섹션은 있을 때만 spec 지문 묶음에 넣으므로(OT §3.3 선례) 요구 없는 spec의 지문이 바뀌지 않는다.
   * 블록 코드 해시 입력 버전(F2)·코드 지문(F3)은 코드가 바뀌는 card에서 필연적으로 바뀐다. 이 제외는 **판정 기준 변경으로 보고**하고, 목록은 검증자가 소유한다.
   * 그 밖에 빼는 칸: 계수·시간 칸(40 §2.4.13 T 부류)과, 실행 경계 문구 변경으로 바뀌는 칸이 있으면 그 목록(design이 정하고 검증자가 소유).
   * base는 OS-2의 실제 base master(XRUN-F1 card C 병합 뒤) 기준선이고, base 쪽 실행은 그 master의 수작업 사슬이다(W-1, N7.2 'v0.5 반영', N7.1 'OS-2와 gain-budget LA-1의 선후').
2. **계획 안 결과 = 단독 결과**(변경 종류 = 결정성): 변형이 둘 이상인 계획에서 각 변형의 결과가 그 변형만 담은 계획으로 돈 결과와 비트 동일하다(T 부류 제외). 층 0 조립·수리·외층 자동 켬 판정·비지배 재판정이 변형 단위라는 것(N3.6 v0.7 행)이 이 조건의 전제다. 변형 순서를 바꿔도 같다. **범위는 E_B를 선언한 실행이다.** 시간 예산에서 E_B를 유도하는 실행(X-17 후반)은 유도값이 평가 시간 중앙값에 의존하고(`kernel.py:153-158`, card C 뒤 `search_ceiling`), 앞 변형의 블록 결과 적중으로 뒤 변형의 평가 시간이 짧아지면 유도 E_B가 달라진다. 벽시계 정지(F-6)도 같다. 이런 실행에서 비트 동일을 요구하려면 계획 순서·구성과 무관한 유도 규칙이 따로 있어야 한다. 그 규칙은 DS-U9(열림)로 두고, 정해지기 전에는 유도 실행을 조건 2에서 빼고 결과에 '유도 예산 -- 단독과 다를 수 있음'을 적는다. 이 제외는 기준 약화가 아니라 범위 표기이고, 검증자가 확인한다.
3. **재계산 0**: 실행 계획 전체에서 같은 입력의 블록 재계산 0, 같은 평가 키 재계산 0(40 §2.4.9 판정 1을 실행 전체에).
4. **공유 증거**: 같은 topology 변형 둘을 담은 계획에서 S1 블록 계산 수가 변형 하나일 때와 같다. 블록 결과 색인 적중 수와 S1v 재계산 수(DS-2)를 결과에 낸다.
5. **fail-closed 증거**: N3.2 로더 규칙과 N3.3 정지 조건마다 거부 test가 실제로 거부한다(통과가 아니라 거부를 먼저 확인).
6. **비교 도구**: 엔진 import 0, 권고 문장 0, `code_fp`·공통 판정 불일치 표시.
7. 모든 새 함수가 진입점에서 호출된다(배선 증거). 옛 진입 흐름이 남지 않는다.
8. 상위 N6.3의 graph 단일 정본·재계산 계수·파일 분할 확인과 design 대 구현 gap 분석을 통과한다.
9. **(v0.6, OS-L) 실행 중 추가된 변형**(변경 종류 = 결정성, 아래 셋째 항목의 비트 동일):
   * θ에 무관한 블록(단계 A·S0 수준)은 추가된 변형에서 계산 0(전부 색인 적중)이다. 계산되는 S0 수준 블록은 offset-trim G-12의 '문턱에 의존하는 블록' 목록 안에만 있다. 목록 밖 S0 수준 블록이 계산되면 FAIL이다. **층 0 조립 블록**(gain-budget LA-1 경로 -- 블록 국소 후보·국소 봉인·블록 국소 front·조합 DP·조립·수리)도 같은 규칙이다: 변형 단위로 다시 돌지만(N3.6 v0.7 행), 그 안에서 계산되는 블록은 문턱을 입력 버전으로 읽는 것뿐이고 그 블록은 G-12 목록 안에 있어야 한다(감사 C2). 커널 안 블록은 문턱이 바뀌어 새 θ에서 계산되는 것이 정당하므로 이 항목의 대상이 아니다.
   * 실행 계획 전체에서 같은 입력 재계산 0(블록·평가 키, 완료 조건 3).
   * 추가된 변형의 결과는 새 세션을 열어 처음 변형은 실행하지 않고 같은 문턱 입력으로 그 변형만 추가해 실행한 결과와 비트 동일하다(N3.12 '허용 동작'. E_B 선언 실행, T 부류 제외).
   * 허용 범위 밖의 추가(다른 topology, 사용자 판정 제약 변경, 문턱 밖 형태 변경, 같은 정체 중복)는 거부된다. 거부를 먼저 확인한다.
   * Δ_T가 문턱에 들어가는 길은 변형 추가 인터페이스 하나뿐이다(호출 grep과 실행 경로 test).
10. **(v0.7, OS-2) matching 요구 실행**(변경 종류 = **동작 변경**, O-34 (1) 네 다리 -- 정본 gain-budget N6.3):
   * **정의 손계산 오라클 toy**(피검 함수로 만들지 않음): (a) 커널 판정 k·σ_in ≤ 문턱이 손계산 σ_in에서 맞게 통과·거부한다 (b) front 판정 k·σ_in + \|V_id*\| ≤ 문턱 -- ΔW ≠ 0인 toy에서 손계산 V_id*(gain-budget DEC-23 정의 문장)로 위반 점이 front에서 빠지고 비지배 재필터가 다시 돈다(거부를 먼저 확인), \|A_dc\| > 판정 분해능인 toy에서 ΔW = 0이면 V_id* = 0으로 통과함을 정직하게 적는다(ΔW = 0 → 0은 엔진 1차 계산 규칙이고 \|A_dc\| > 판정 분해능일 때만 쓴다 -- O-63 (1)); **정의 불능 toy**(v0.7.3, O-62 (3)·O-63 (1) 갈래 먼저): \|A_dc\| ≤ 판정 분해능인 toy에 ΔW = 0을 준 점(ΔW ≠ 0인 점도 같음)은 ΔW와 무관하게 σ_in·V_id* 정의 불능이고, 어느 판정 자리(커널 행 ①·front 판정 ②, N3.3)에서 빠지든 원인 = 갈래 사유 기록의 참조, offset 위반 기록 0이다(front에서 빠지면 비지배 재필터가 다시 돈다; 0·통과로 나오거나 offset 위반으로 기록되면 red -- 정본 gain-budget v6.23 병합 `294bde4d`의 DEC-23 'A_dc 정의 불능 갈래'·'front 판정', DEC-74, 'DE-1 후속 정정 표' offset-strategy 행, 인용만); **미수렴 toy**(O-64 (2)): 커널 출발 창 미수렴 toy는 gain-budget N6.6 완료 조건 (6)·(12)(a)를 인용하고, matching 합성 제약이 걸린 점이면 front에서 빠지고 원인 = 미수렴 사유 기록의 참조다(offset 위반으로 기록되면 red) (c) 두 판정이 같은 문턱 항목 하나를 읽는다(문턱 사본 0, grep).
   * **봉인 불변식**: front 점 전부 평가 커널 봉인 통과(KVL·KCL·영역, gain-budget N3.6).
   * **SPICE oracle 대조**: σ_in = 오라클 MC(A = `.tf`, OP-5), V_id* = 오라클 `.dc`(OP-5), 엔진 점 입력 = gain-budget EO-1 생산자. 선행 EO-1·OP-5·OS-V 전에는 '보류'이고 이 조건은 닫지 않는다(gain-budget N6.3 (i)).
   * **검증자 값 변화표**: F-1 fixture 결과의 변화와 원인(원인 미설명 0). 결정성 비트 동일은 항상 검사한다.
   * 단위 9 뒤 실현 W 재판정은 단위 9 card의 완료 조건에서 같은 기준으로 확인한다(이 card 범위 밖, gain-budget DEC-74·N6.1 단위 9).

---

## N8. 원문 근거표

* 보관 위치: `skills/analog-gmid-design/assets/technique/sources/<폴더>/`(`source.pdf`·`paper.md`, 목록은 그 폴더 `README.md`). 쪽 렌더는 skill 폴더에서 `python tools/pdf_to_md.py ensure`로 만든다.
* 쪽 번호는 PDF 쪽이다. 수치는 인용하지 않는다. trim 규칙 자체의 원문은 offset-trim 계획 N8이 정본이다.

| R | 원문 | 웹 | 로컬 PDF | 쪽·위치 | 이 계획에서 쓰는 곳 |
|---|---|---|---|---|---|
| R1 | Y. Zhou, A. Kay, 'Offset Correction Methods: Laser Trim, e-Trim, and Chopper', TI SBOT037A, 2017 | [ti.com/lit/SBOT037](https://www.ti.com/lit/SBOT037) | `offset_trim__zhou_2017/source.pdf` | p.1 e-Trim, p.2 Fig.3·Table 1(chopper가 1/f와 시간·온도 drift를 없앤다) | trim은 1/f를 보정하지 않으므로 1/f를 두 방식 공통 판정으로 둔다(N3.4) |
| R2 | A. Kay, 'Op Amp Offset Voltage and Bias Current Limitations', TI SBOA590, 2024 | [ti.com/lit/pdf/sboa590](https://www.ti.com/lit/pdf/sboa590) | `offset_trim__kay_2024/source.pdf` | §1.2 PDF p.7 Figure 1-8 문단 | CMOS offset trim은 drift를 보정하지 않는다. compare 보고에 이 한계를 그대로 싣는다(N3.8) |
| R3 | H. M. von Staudt, 'Trim DAC Design with Minimum DNL for Self-Trim with Self-Test Schemes', IEEE IMS3TW 2011 | [doi:10.1109/IMS3TW.2011.34](https://doi.org/10.1109/IMS3TW.2011.34) | `offset_trim__staudt_2011/source.pdf` | p.1-2 §II.A | trim 보정 구간이 미보정 분포를 덮어야 한다는 조건. 요구의 k를 trim 보정 구간 배수로 쓰는 근거(N3.2, N3.3) |

matching 유도식 k·σ_in + |V_id*| ≤ `offset_in_max_v`는 사용자 결정 S-1의 식이고(판정 위치 분리는 O-53 A2), σ_in·V_id*의 정의는 gain-budget DEC-23(σ_in = 봉인점 DC 방정식 1차 감도 입력 환산, V_id* = 부호 있는 계통 offset 한 칸 -- O-46 (1)·O-47·O-50 G1)이다. 원문 수치나 관례 배수는 쓰지 않는다.

---

## N9. 위험과 대응

| 위험 | 대응 |
|---|---|
| 같은 topology 변형이 평가 캐시를 공유해 다른 변형의 제약 행이 적중한다(F-1·F-2) | 지금 키 그대로의 공유는 금지(N3.6). 나누는 방식은 DS-1. 완료 조건 2(계획 안 = 단독)가 잡는다 |
| DS-1 (가)를 고르면 완료 조건 3(같은 평가 키 재계산 0)과 모순된다 | 조건을 약화하지 않는다. 약화는 DS-U7로 사용자 승인을 받을 때만 |
| matching 합성 판정·출발값이 핵심 층을 건드린다(N3.10) | XS-10 승인 뒤에만 OS-2 착수. 범위(**PD-4 승인, S-8**): 계산 규칙은 `ss_constraint_rows` 한 곳과 `iv_matching_l` 한 곳이고, 입력 전달 때문에 search 파일 다섯(`kernel.py`, `search_context.py`, `start_intervals.py`, `iv_context.py`, `find_front.py`)과 값 형식 `search_values.py`가 더 바뀐다. design이 이 범위를 넘으면 다시 승인받는다. (v0.7) O-53 A2의 front 합성 판정 소비자는 gain-budget DEC-74 front 판정 자리에 붙는다(XS-20 승인 범위). 그 자리의 파일이 위 목록 밖이면 design이 바뀌는 파일을 적어 보고한다 |
| S1v·metric 블록이 제약 extras 때문에 변형마다 다시 계산돼 공유 효과가 줄어든다(F-2·F-3) | 완료 조건 4로 수를 드러낸다(DS-1은 O-176 Ⅵ (나)로 결정 -- 같은 θ 재평가 0, 새 요청은 fail-closed, DS-2는 PD-3로 대상 없음 -- 옛 'M2와 함께 DS-1·DS-2로 사용자에게 올린다', v0.7.5 백로그 재감사 OS-B4). 숨기지 않는다 |
| (v0.6) 보정 루프 동안 엔진 세션(모든 반복의 블록 결과 색인)과 오라클 별도 프로세스가 **메모리를 동시에 점유**한다. 반복마다 색인이 커진다 | 구동기는 엔진 계산과 오라클을 차례로 돌린다(offset-trim NFR-T9, 오라클 안 병렬 수 = 실행 설정 선언값). 반복 상한(D-19)과 색인 상한 식(N3.7)으로 크기를 닫는다. OS-L 병합 전에 반복당 색인 크기(바이트)를 재고, OS-L은 반복마다 색인 항목 수와 프로세스 최대 메모리를 결과에 낸다.<br>**안전한 놓기는 design 선택지로 남긴다**: 끝난 변형의 판정 행은 다시 쓰이지 않는다(같은 정체 재추가는 거부된다). DS-1 = (나)이면 평가 키 부분은 변형 사이 공유라 끝난 변형의 판정 행만 놓을 후보다. 그래서 그런 항목을 놓아도 같은 입력 재계산(완료 조건 3)이 생기지 않을 수 있다. 무엇을 언제 놓을 수 있는지는 DS-1 결정 뒤 design이 정하고 검증한다. 그 밖의 항목(θ 무관 블록 등)은 놓지 않는다.<br>메모리 한도를 넘을 위험이 실측되면 사용자에게 올린다(조용히 비우지 않음). 운영 조건은 XS-19 |
| 실행 계획 전체로 색인 수명이 길어져 메모리가 는다 | 상한 식(N3.7)으로 등록 때 fail-closed. OS-L 병합 전 반복당 색인 크기 측정(XS-19)으로 잰다(옛 'M2의 θ 겹침 수와 블록 수로 미리 잰다' -- OS-B4). 변형 수는 방식 표(N3.5)로 닫혀 있다 |
| 실행 전체 시간이 변형 시간의 합이 된다 | 변형별 예산(N3.7)을 결과에 낸다. 시간 예산 유도는 변형마다 |
| 선언 없는 단일 출력 회로에서 offset 기준이 정의되지 않아 matching front 판정(V_id*)을 잴 수 없다 | 탐색 전 정지(N4-3, gain-budget DEC-23 `reference_undeclared`, O-53 B3 -- 추론 금지). spec이 기준을 선언하면 열린다(N7.1) |
| V_id*의 ΔW 성분 (3)은 단위 9 전 sizing W에서 ΔW가 없으면 0이다 -- 성분 (1)(2)(봉인점 KCL·A_dc)는 커널에서 이미 판정된다(상위 DEC-23 (나′)·U-108; \|A_dc\| ≤ 판정 분해능이면 정의 불능 -- O-63 (1); v0.7.4) | 정직하게 '1차, ΔW = 0' 표기(gain-budget DEC-23). 실현 W 재판정은 단위 9 뒤(O-45 U3), 정확값은 오라클 `.dc`(OS-V·VB-1) |
| 요구와 수단 제약이 섞인 spec이 조용히 한쪽만 판정된다 | 로더 거부(N3.2) |
| compare 표가 권고로 읽힌다 | 도구에 판정·권고 문장 금지(N3.8). 보고에 '권고 아님'과 R1·R2 한계를 싣는다 |
| 국면 2만 돈 compare에서 matching 결과가 다른 코드·다른 선언으로 만든 것이다 | 비교 도구가 `code_fp`·공통 판정 선언 불일치를 표에 적는다(N3.8) |
| 승인된 offset-trim design(§4·§5.1·§5.2·§9.4·§10.1)을 고쳐 TR-1 착수가 늦어진다 | OS-0이 개정안을 같이 내고 한 번에 재승인받는다(S-4). TR-M·TR-L처럼 영향 없는 card는 그대로 진행 |
| library spec이 요구 형식이 아니어서 기능이 library에서 쓰이지 않는다 | 검증은 fixture spec으로 한다(N4). 옮기는 것은 사용자 몫(DS-U5)이고 보고에 적는다 |
| TR-3~TR-5(국면 2 게이트 해제) 사이 승인된 회로를 사이징하지 못한다(OD-3) | 사용자가 수용했다(S-8). 그 기간의 정지 사유(`trim_phase2_search_not_open` 계열, 이름은 design)를 결과에 내고, TR-5(국면 2 게이트 해제)가 정지를 지운다((v0.8) → TR-5·TR-B 통합 병합이 지운다) |
| card C `S3Index` 인터페이스가 OS-5에서 다시 바뀐다(PD-7) | 필수 인자로 바꾸고 card C test를 같은 변경에서 고친다. 기본값 인자로 피하지 않는다 |
| 계획 안 변형 순서가 결과를 바꾼다(숨은 상태) | 블록 순수성(40 §2.4.5 결정성)과, DS-1 = (나)의 평가 키 부분 공유(같은 θ 1회 평가). 완료 조건 2의 순서 뒤집기 test |

---

## N10. 열린 결정

### N10.1 사용자 결정 필요

기본안은 원칙으로 정한 것이고 사용자가 바꿀 수 있다. N5의 XS-1~XS-14 승인·확인도 사용자 몫이다.

| ID | 질문 | 기본안 |
|---|---|---|
| DS-1 | M1 결과(제약이 평가 키 밖, 결과는 제약 의존)에 대한 처리. (가) `S3Index`의 평가 키 부분은 변형별, 블록 결과 부분만 공유(card B 뒤에는 search 변경, 완료 조건 3과 모순, XS-5·XS-8). (나) 평가를 크기·metric(계획 안 요청 합집합)과 변형별 판정으로 나눈다(kernel·graph 변경, XS-5). (다) 평가 키에 변형 제약 지문을 넣어 키를 나눈다(search 변경, XS-5·XS-8). 선택지별 완료 조건 3 관계는 N3.1 표 | **결정됨(O-176 Ⅵ: (나) -- S-14 (다) 번복, 원래 취지와 다름(승인))** -- 같은 θ는 실행 안에서 1회 평가하고 판정만 변형별로 한다. 조건 (1) 판정 행을 graph 필드 `constraint_rows`로 옮기고 `EvalResult` 판정 칸을 같은 변경에서 지운다(값 칸·사본 금지 -- graph 규칙 2·4; writer = search 제약 블록 하나(N3.6·OS-2 행의 같은 블록 -- 변형별 판정 행을 씀), 층 = design) (2) metric 블록은 요청별로 나눈 S3 graft로 공유하고, 추가 변형(N3.12)이 새 metric 요청을 가져오면 fail-closed(정지·사유 기록 -- 조용한 재계산 금지). 반영 시점 = OS-5 착수 전. 옛 S-14 (다) 근거('S-2 핵심 유지')는 as-built 보존 근거라 유지 근거가 아니다(상위 원칙 O-153·O-165). (가)·(다)는 기각. 구현은 OS-5·OS-L(design §10). 옛 결정 원문(S-14 (다))은 history 0.7.6 행 |
| DS-2 | S1v 블록이 제약 tuple 전체를 extras로 받아(F-3) 같은 topology 변형마다 다시 계산되는 몫. (가) 받아들인다(입력 지문이 달라 판정 1 형식 위반은 아니지만 같은 값의 재계산, XS-8). (나) S1v 투영을 뷰 선언·루프 끊는 넷으로 좁힌다(graph 층 변경, XS-5) | **기본안 없음**. M2(card B 뒤 2차)의 S1v 계산 수와 함께 결정받는다. → **닫힘(PD-3, S-8): 대상 없음.** 유도 제약은 S1v 씨앗·extras 밖이라(design OB-4) 같은 topology 변형끼리 S1v 입력이 같다. 유도 제약이 뷰 씨앗을 요구하게 되면 다시 연다 |
| DS-U1 | matching에서 `offset_excess`(구조 가드)를 요구와 함께 둘 수 있게 할지 | 두지 않는다(N3.2 거부). 요구가 offset 판정의 유일한 출처 |
| DS-U2 | 요구와 수단 제약 공존 거부의 범위: `offset_in_sigma_mv`·`offset_sys_mv`·`offset_excess` 셋 다인가 | 셋 다(XS-1). 결정됨(S-6). '판정 제약'의 범위 = 상위 S0 `constraint_classes` 판정 대상 칸의 항목(v0.7.5 -- 옛 `judged` 참인 항목)(`user_spec`, 판정 대상을 가리키는 `reference`)뿐이고, `pending_spice` offset 항목과 `pending_constraints`는 허용(PD-9 승인, S-10) |
| DS-U3 | k의 출처를 요구 하나로 옮기는 것(`offset_trim.coverage_multiple` 삭제) | 옮긴다(XS-6, 단일 정본) |
| DS-U4 | compare에서 공통 판정이 없을 때. '있음'의 정의: 1/f는 `noise_fc_in_hz`나 `noise_out_int_vrms` 가운데 하나 이상이 값이 있는(결정 대기 아님) 판정 제약으로 선언됨, 면적은 `area_search_m2 <=`가 값이 있는 판정 제약으로 선언됨. 둘 다 있어야 한다 | 하나라도 없으면 탐색 전 거부(같은 기준 없이는 나란히 놓을 수 없음). `matching`·`trim` 단독은 요구하지 않는다 |
| DS-U6 | N+1 구성의 m 규칙(XS-2). OT §3.4 집계는 추천 N 하나에 대해 m = min_p m_max,p(N)이다 | N+1에도 같은 집계 규칙을 그대로 쓴다: m = min_p m_max,p(N+1). 어떤 집계 점에서 m_max,p(N+1)이 정의되지 않으면 N+1 구성은 내지 않고 사유를 후보표에 적는다(새 상수 없음) |
| DS-U7 | (DS-1 (가)를 고를 때만) 완료 조건 3을 '변형 안 같은 평가 키 재계산 0 + 변형 사이 수는 보고'로 바꾸는 것 | 바꾸지 않는다. **기준 약화**라 사용자 승인 없이는 하지 않는다 |
| DS-U9 | 시간 예산에서 E_B를 유도하는 실행의 다변형 규칙(완료 조건 2, NFR-S5) | **기본안(상위 v6.38.4 열다섯째 커밋 계획 검증 4 m-11, NFR-S5·상위 NFR-4에서 -- 원칙으로 정한 기본안): 유도 실행 = 결정성 요구(완료 조건 2·NFR-S5) 밖 표기 유지**(옛 '기본안 없음(열림)'); 유도 금지(E_B 선언만)로 바꿀지만 사용자에게 묻는다(상위 U-47 하위 항목). '첫 변형의 유도값을 모든 변형에 쓴다'는 안은 조건 2를 지키지 못한다: 변형 2를 단독으로 돌리면 자기 유도값을 쓰고, 순서가 바뀌면 결과가 바뀐다. 후보는 계획 순서·계획 구성과 무관한 규칙뿐이다(예: 변형마다 자기 단독 실행과 같은 조건에서 유도값을 정하는 규칙이 있는지 design이 조사). 정해지기 전에는 유도 실행을 조건 2·NFR-S5에서 빼고 결과에 표기. **선행 조건**(v0.7.5 백로그 재감사 OS-B1, 사용자 몫): 상위 U-47 'front 시간 예산' 결정 -- 이 질문은 그 하위 질문으로 올린다(후보: 유도 실행을 결정성 요구 밖으로 표기 유지 / 유도 금지(E_B 선언만)). 그때까지 지금 문언(표기·제외)은 fail-closed 표기라 유지 |
| DS-U8 | trim 시험 회로 spec을 요구 형식으로 다시 쓸 때 `offset_in_max_v` 값과 `offset_excess` 처리(XS-9) | 사용자 몫. `offset_excess`는 DS-U2 기본안대로 빼고, `offset_in_max_v` ≥ 승인된 V_res(T-25) 조건만 로더가 본다. **선행 조건**(v0.7.5 백로그 재감사 OS-B3): TR card(시험 회로 T-27·T-28) 착수 때 묻는다 |
| DS-U5 | 기존 library spec(특히 `offset_in_sigma_mv`를 가진 spec, F-9)을 요구 형식으로 옮길지와 그 값 | 사용자 몫. 이 기능은 옮기지 않는다. **선행 조건**(v0.7.5 백로그 재감사 OS-B2): OS-2 착수 때 묻는다 |
| DS-T1 | matching만 쓰는 회로의 SPICE 온도 보정 루프를 T-30 순서(TR-7 뒤)보다 앞당길지(N3.11) | **닫힘(S-9, 권고대로)**: 앞당기지 않는다(T-30 원문 순서). matching 루프에는 DAC 분해 정지가 없어 기술적으로 앞당길 수는 있지만, 보정 루프의 정본(Δ_T·문턱 합성·멈춤 규칙)이 offset-trim 계획 card에 있어 한 번만 구현하려면 그 card 순서를 따르는 것이 낫다 |
| PD-9 | 공존 거부의 '판정 제약' 범위(N11). PD-1~PD-8은 S-8, W-1·F-1·T-30 연결은 S-9로 닫힘 | **닫힘(S-10, 권고대로)**: 판정 제약만 거부, `pending_spice`·`pending_constraints` 허용(N3.2) |
| V-1 | matching 유도 제약의 오라클 측정 card 배정(N3.11) | **승인됨(S-11)**: OS-V card, OS-2 뒤, offset-trim TR-TL 앞(N7.2). (v0.7) 오라클 쪽 선행 = oracle-portability OP-3·gain-budget EO-1·oracle-portability OP-5, `offset_sys_mv` `verified_by`는 gain-budget VB-1 인용(감사 D3·D4) |
| D-24 연결 | offset-trim D-24(반복 구조) | **결정됨(T-35, 안 B)**: v0.6 N3.12·OS-L로 반영 |
| D-25 연결 | offset-trim D-25(Δ_T 출처 지문 대조, 권고 주체 = 엔진 밖 구동기) | **결정됨(T-36: (c) 출처 무결성 + (c-2) 엔진 밖 구동기)**. OS-L 인터페이스는 대조를 통과한 문턱 입력만 받는다(N3.12) |
| D-20 연결 | offset-trim D-20(오라클 판정 대상 점) | **결정됨(T-36 (가))**. 엔진 쪽은 front 점 노출(W-1) 말고 영향 없음 |
| XS-16~XS-19 | 실행 중 목록 증가, 공개 진입 둘, S-3 경계(X-23), 메모리 동시 점유(N5) | **승인(S-12, 사용자 "모두 권고대로 해")** |

### N10.2 오케스트레이터 기본안(원칙으로 확정, 사용자가 바꿀 수 있음)

| ID | 항목 | 기본안과 근거 |
|---|---|---|
| DO-2 | 국면 결정 방식 | 승인 기록 유무(정해진 위치). 진입 인자 분기 없음(S-2) |
| DO-3 | 변형 순서 | N3.5 표 순서 고정. 결과 무관은 완료 조건 2가 확인 |
| DO-4 | 블록 결과 색인·`RunCounters` 수명 | 실행 계획 하나(XS-7 확인 요청) |
| DO-6 | TR card 전 trim·compare 요청 | 계획 함수가 fail-closed 거부 |
| DO-7 | 비교 도구 위치 | 엔진 밖 `tools/`, 엔진 import 금지. 정확한 경로는 design |
| DO-9 | 승인 파일이 있을 때 국면 1 재실행 방법 | 사용자가 승인 기록 파일을 정해진 위치에서 치운다. 엔진은 승인 파일을 고치지 않고, 국면 강제 인자는 두지 않는다. 낡은 승인은 국면 1로 돌아가지 않고 정지(N3.5) |

변형별 예산(옛 DO-1)과 S3 줄 변형 칸(옛 DO-5)은 승인된 정의·형식을 바꾸므로 확인 요청 항목 XS-12·XS-13으로 옮겼다(N5).

### N10.3 OS-0 design에서 닫을 기술 항목

| ID | 항목 |
|---|---|
| G-S1 | matching 판정의 형식(v0.7, O-53 A2 두 자리): ① 커널 행 k·σ_in ≤ 문턱 -- k를 입력으로 받는 새 metric인가, `offset_in_sigma_mv`를 k배로 읽는 제약 행인가 ② front 합성 판정 -- gain-budget DEC-74 front 판정 자리에서 같은 V_id* 값을 읽는 소비자의 형식(새 V_id* 계산 없음). 분해능 규칙(기존 ss 제약 행 규칙과 정합). 그리고 다음 둘:<br>• **단위**: σ_in·V_id* metric(`offset_in_sigma_mv`·`offset_sys_mv`)은 mV 단위(`registry.py:56-58`의 단위 칸 `mv`), `offset_in_max_v`는 V다. 환산은 숫자 1000을 쓰지 않고 단위 어휘(레지스트리 단위 칸과 키 접미 `_v`, core 단위 접두 정의, 예: `iv_matching_l.py`가 쓰는 core `MILLI`)에서 읽는 규칙으로 정한다<br>• **view 출처**: offset metric은 transfer 뷰 metric인데(F-3a) 요구 섹션에는 view 선언이 없다. 유도 제약의 view를 어디서 가져오는지(입력 셀 전달 뷰 = `metric_structure`, 기본 뷰, 사용자 선언 중 하나)를 정한다. 이 선택이 변형별 S1v 값이 같은지(N3.1-3)를 정한다 |
| G-S2 | matching 출발값(as-built `iv_matching_l` L 하한 -- gain-budget v6.38.2 LR6 개정 뒤 입력 gm/ID 하한, 그 계획 DEC-105 (6))의 입력을 유도 제약으로 바꾸는 규칙. (v0.7) 규칙 정본은 gain-budget LR6이고, design이 정하는 것은 LR6 구현이 σ 목표(= 문턱 / k, 커널 판정 ①)를 읽는 자리와 형식뿐이다(N3.3). LA-1 역산 조립 L 단계도 같은 LR6 구현을 쓴다 |
| G-S3 | 변형 정체 지문(topology `connectivity_fp` + 제약 집합 지문)의 정의와 S3·결과 JSON 칸 |
| G-S4 | 변형 제약 집합의 기록 형식: 유도 제약을 spec 판정 제약과 같은 형식으로 만들 때 출처 칸(`value_from_spec` 계열) |
| G-S5 | S1v 계산 수를 결과 JSON에 내는 칸과 계수 정의(완료 조건 4). DS-2가 '대상 없음'으로 닫혔으므로(PD-3) 결정 근거가 아니라 '같은 topology 변형끼리 S1v 입력이 같다'는 사실 확인용이다 |
| G-S6 | 완료 조건 1의 비교 제외 칸 목록(검증자 소유) |

### N10.4 다른 문서 소유자 몫 백로그(결정 아님, v0.7.2)

이 계획이 정하지 않는다. 각 소유자가 자기 개정에서 닫는다(출처: offset-strategy design v0.3.1 `99eb77f6` §18.4).

| ID | 항목 | 소유·시점 |
|---|---|---|
| PS-6 | `open_run(s0_sets=B_S0)` 순환: B_S0는 실행 계획(변형 수, PD-7)에서, 계획은 단계 A의 spec에서 나오는데, 단계 A는 `open_run`의 쌍을 받아야 돈다. 순서를 푸는 문언이 PD-7·40 §2.4.5 '수명' (1)에 없다. OS-2는 `s0_sets`를 더하지 않으므로 막지 않는다 | OS-5 `s0_sets` 구현 전, design·40 §2.4.5 소유자(계획 PD-7 문언이 필요하면 S-7로 계획부터) |
| PS-1 잔여(v0.7.3) | DEC-74 front 판정 기록(위반·정의 불능 점과 원인)의 자리 종류는 정해졌다 -- 출력 기록(gain-budget v6.24 병합 `59ecc88e` DEC-74·N3.3 (b), 사용자 결정 O-68 (3)); 이름은 아직 없다(design v0.3.2는 'DE-1 design 뒤 확정') | 종류 = 출력 기록(gb v6.24 DEC-74, O-68 (3) -- 정해짐), 이름 = card DE-1 design·착수 실측. gb 알림 대상. OS-2 착수 조건(N7.1) |
| PS-7 | 하네스가 평가 결과 전수(`seq` 순)를 읽는 S3 색인 평가 키 부분의 열거 API가 40 §2.4.5 조회 API에 없다(`get(key)`뿐, '색인을 순회하지 않는다'). O-63 (3) 읽기 길(N3.12)이 쓰는 API다 | OS-2 범위(소비자와 같은 변경; 열거 API·대상 부분·계수·분할의 제작 = OS-2·상위 LA-1 가운데 먼저(상위 v6.38.4 열여섯째 커밋 계획 검증 5 MJ-1) -- 상위 v6.38.4 열다섯째 커밋 계획 검증 4 M-1; v0.7.5 백로그 재감사 OS-B8, 옛 'U17 ② design(40 §2.4.5). v0.7.3부터 OS-2 착수 조건'); 40 §2.4.5 조회 API 개정안 = OS-0 design 개정 |

---

## N11. design v0.1과 계획의 차이(사용자 결정 S-7)

S-7에 따라 design이 계획과 다르게 간 점은 design에서 승인받지 않는다. 이 절에서 결정 항목으로 정리하고, 계획 v0.5 독립 검증 → 사용자 승인 → design v0.2 순서로 처리한다. 승인 전에는 계획 규칙을 바꾸지 않는다.

**결정 상태**:

| ID | 상태 |
|---|---|
| PD-1~PD-8 | **사용자 승인됨**(S-8, 권고대로). 계획 규칙에 반영함(N11.2 '반영 위치') |
| W-1·F-1 | **사용자 승인됨**(S-9, 권고대로). N7.1·N7.2·완료 조건 1에 반영함 |
| T-30 연결(DS-T1 포함) | **사용자 승인됨**(S-9). N3.11에 반영함 |
| PD-9 | **사용자 승인됨**(S-10, 권고대로). N3.2 로더 규칙과 DS-U2 문언에 반영했다. design OB-6 수정은 design v0.2 몫이다 |
| V-1(v0.5.1, 검증 B-3) | **사용자 승인됨(S-11)**. matching 유도 제약의 `verified_by`(오라클 측정)를 붙이는 card = OS-V(N7.2). 선행은 OS-2와 오라클 쪽 OP-3·EO-1·OP-5(v0.7, 감사 D4)·gain-budget VB-1(감사 D3)이고, offset-trim TR-TL의 선행이다 |
| F-1 위치 정정 | **사용자 확인됨(S-11)**: 저장소 안·library 밖 fixture(`assets/fixture/` 계열) |
| D-24 연결 | **결정됨(T-35, 안 B)**. v0.6에서 '실행 중 변형 추가'(N3.12, OS-L, XS-16·XS-17)로 반영했다 |
| D-18 연결(v0.5.1, 검증 B-3) | **결정됨(T-34)**: 판정 온도 범위 = T-14 범위, spec 요구 안 칸 한 곳 선언, 소비자 모두 참조. N3.2에 칸을 더했다(v0.5.3) |

* 입력: design v0.1 `docs/02-design/features/offset-strategy.design.md`(브랜치 `ostrat-design`, `aef46c7`)와 그 history, design 독립 검증(82점) 지적.
* 코드 인용 기준: master `d783efe`.
* 표의 열: '원래 취지' = 사용자 취지 문장(N1.1)·S-1~S-6과 다른지. '승인' = 사용자 승인이 필요한지.

### N11.1 항목

| ID | 계획 현 문언 | design이 택한 것과 근거 | 대안 | 권고 | 원래 취지 | 승인 |
|---|---|---|---|---|---|---|
| PD-1 변형 제약 주입 | N3.10 첫 행: 변형마다 spec 사본을 `SizingSpecDoc.from_sections`로 만들어 넘긴다(pipeline + authoring, 핵심 층 무변경) | `build_search_context(..., derived=...)` 별도 입력(design §5.3). 사용자 판정 제약은 요구가 있으면 모든 변형에서 같고(수단 제약 공존 거부), 바뀌는 것은 유도 제약뿐이다. 검증 확인: spec을 extras로 받는 `achievability`(`stage_b.py:168`)는 사본 방식이면 `spec_fp`가 달라져 변형마다 다시 계산되고, `derived` 방식이면 다시 계산되지 않는다. S1v·`constraint_classes`·`search_domain`은 두 방식이 같다 | 계획 문언(사본). 서명 변경은 없지만 `achievability`가 변형마다 다시 계산된다 | **design안(`derived`)**. 원래 취지(계산한 값을 재사용)에 더 가깝다. 대신 `build_search_context` 서명(search 층)이 바뀌므로 N3.10의 '핵심 층 무변경' 분류를 '핵심 층 확장(XS-10 범위)'으로 고친다(PD-4와 같이) | 다르지 않음(더 가까움). 단 S-2 '핵심 유지'와는 다름(XS-10 범위 안) | 필요 |
| PD-2 승인 기록 로더와 국면 2 일의 TR card 배정 | N3.5 '구현 시점'·N7.2 OS-5: 국면 규칙·승인 기록 로더·낡은 승인 정지는 trim 국면을 처음 여는 TR card(OS-5, TR-2)에 묶음. OT §14.1(T-18 승인)은 승인 기록 로더를 TR-1에 둠 | design OB-18(§11.2): TR-2 = 국면 1 행과 '승인 파일이 있으면 국면 2 미구현으로 fail-closed'(파일 존재만 확인), **TR-3** = 승인 기록 로더·결속(`bind_trim`)·낡은 승인 정지·국면 2 분기(파생 topology 단계 A), TR-4 = 구조 동일 검사, **TR-5 안의 국면 2 게이트 해제**(design 표기 'TR-5b'는 offset-trim card 표에 없는 이름). TR-1에는 로더를 부르는 곳이 없어 '만들면 배선'을 못 지킨다 | (ii) 승인 로더·결속·국면 2 분기를 TR-5(국면 2 게이트 해제)에 한꺼번에 두어 국면 2가 열리는 시점을 하나로 만든다(card가 커진다) | **design안(OB-18)**. 결속·낡은 승인 정지가 TR-3부터 실제 경로에서 쓰이고(국면 2 단계 A, TR-4 구조 검사의 입력), 각 card가 자기 일을 배선한다. 다만 OD-3을 같이 승인받는다 | **OD-3(다름)**: TR-3~TR-5(국면 2 게이트 해제) 사이에는 승인된 회로가 단계 A까지만 돌고 `trim_phase2_search_not_open`으로 멈춰 사이징되지 않는다. OT 원래 흐름에 없던 정지다 | 필요(OT §14.1 배정 변경 + OD-3) |
| PD-3 DS-2 대상 소멸 | N10.1 DS-2: S1v가 제약 tuple 전체를 extras로 받아 같은 topology 변형마다 다시 계산되는 몫을 (가)/(나)로 결정(M2 뒤) | design OB-4: 유도 제약은 S1v 씨앗·extras 밖이다. `build_s1v`는 `spec.judged_constraints`만 extras로 받고(`s1v_build.py:39`), 요구가 있으면 사용자 판정 제약은 변형 사이에 같다. 그래서 같은 topology 변형끼리 S1v 입력이 같다(design §10.4) | DS-2를 열어 두고 M2 뒤 결정 | **'대상 없음'으로 닫는다.** 조건: 유도 제약이 S1v 씨앗에 들어가지 않는 동안(OB-4). 나중에 유도 제약이 뷰 씨앗을 요구하게 되면 다시 연다. design §3.5의 S1v 칸(`s1v_computes`·`s1v_inputs`)은 사실 확인용으로 남긴다 | 다르지 않음 | 확인 |
| PD-4 XS-10 범위 서술 | N9: matching 확장 범위를 'metrics 레지스트리 또는 `ss_constraint_rows` 한 곳과 `iv_matching_l` 한 곳'으로 design이 닫는다 | design §12.2: 계산 규칙은 두 곳이다. 입력 전달 때문에 search 파일 다섯(`kernel.py` 요청·호출, `search_context.py` 키워드·속성, `start_intervals.py`·`iv_context.py` 전달, `find_front.py` 기록)과 `search_values.py` 형식이 더 바뀐다 | PD-1을 사본 방식으로 바꾸면 `search_context.py` 키워드는 줄지만 커널 요청·행·출발값 전달은 남는다 | **서술을 '계산 규칙 두 곳 + 입력 전달 search 파일 다섯과 값 형식 하나'로 고친다.** 계산 규칙이 늘지 않으므로 XS-10 승인 취지 안이라고 보지만, 승인 때 들은 범위보다 넓어서 확인받는다 | 다르지 않음 | 확인 |
| PD-5 완료 조건 1 비교 제외 범위 | 완료 조건 1: 계수·시간 칸(T 부류)과 실행 경계 문구 변경으로 바뀌는 칸만 뺀다 | design §3.6(G-S6 초안): F2 블록 코드 해시 입력 버전(`input_version`·`block_versions`·`snapshot_fp`·`context_fp`), F3 코드 지문(`code_fp`·`run_id`), spec 지문(`spec_fp`·`section_fps`)도 뺀다. 특히 요구 섹션 지문 묶음을 `SECTION_GROUPS`(`spec_model.py:306-321`)에 늘 더하면, 요구가 없는 spec도 `spec_fp` = `fp_of(fps)`(`spec_model.py:302`)가 바뀐다 | 요구 섹션이 있을 때만 지문 묶음에 넣는다(OT §3.3 선례). 그러면 요구 없는 spec의 `spec_fp`·`section_fps`는 그대로이고 spec 지문을 제외 목록에 넣지 않아도 된다 | **대안(요구 섹션이 있을 때만 지문에 넣기)**. 비교 기준을 넓히지 않는다. F2·F3 제외는 코드가 바뀌는 card에서 필연적으로 바뀌는 칸이라 OT X-T5와 같은 '판정 기준 변경'으로 보고하고, 목록은 검증자가 소유한다 | F2·F3 제외는 판정 기준 변경(보고). spec 지문 제외는 대안으로 피한다 | 필요(판정 기준 변경) |
| PD-6 공통 판정 검사의 card | N7.2 OS-2 행: 공통 판정 검사(N3.4)를 OS-2에 넣음 | design L11: `run_plan` gate, 구현 card OS-5. 공통 판정은 compare에서만 요구하고(DS-U4), OS-2는 compare를 거부한다 | 계획 문언(OS-2) | **OS-5로 옮긴다**(OS-2에서는 쓰는 곳이 없어 만들면 배선을 못 지킨다) | 다르지 않음 | 확인 |
| PD-7 B_S0 정의와 card C 인터페이스 | N3.7: 색인 상한의 S0 계산 벌 수 = '계획 안 서로 다른 S0 입력의 수' | design OB-12(§7.3): B_S0 = 변형 수 + (국면 2 계획에 원본 topology 변형이 없으면 구조 비교용 원본 S0 한 벌). 실행 전에 계획만으로 계산된다. OS-5에서는 `start_intervals`가 변형마다 `derived`를 읽어 변형마다 S0 입력이 달라지므로 '서로 다른 S0 입력 수'와 거의 같고, 아니어도 크거나 같다(안전 쪽). 또 B_S0와 변형별 E_total,v를 `S3Index`에 등록하므로 card C의 `S3Index` 생성자와 등록 시 상한 검사(40 §2.4.5 fail-closed (5)) 인터페이스가 바뀐다 | 계획 문언(서로 다른 S0 입력 수 -- 실행 전에는 정확히 셀 수 없다) | **design안**. 다만 card C 인터페이스 변경을 숨기지 않는다: OS-5가 `S3Index` 생성자에 필수 인자 B_S0를 더하고 card C의 test를 같은 변경에서 고친다(기본값 인자로 피하지 않는다 -- X-7 '기본값 None 폐지'와 같은 원칙). 40 §2.4.5·§2.4.9 개정(design §15.2)과 함께 | 다르지 않음(상한이 느슨해지는 쪽이라 fail-closed 검사가 약해지는 정도는 결과에 보고) | 확인(40 개정·card C test 영향) |
| PD-8 `run_stage_a`의 `donors`·`counters` | 계획에는 문언 없음(N3.6 '색인을 만드는 자리를 실행 계획 진입으로') | design OB-9: `run_stage_a`가 `donors`·`counters`를 필수 키워드로 받고 `StageAResult.topology` 칸을 더한다. 승인된 40 §2.4.5 '전달' 행은 '`run_stage_a`가 두 객체를 만든다'(card B design)라서 다르다 | (ii) card B가 아직 코드에 들어가지 않았으면 card B design(40 §2.4.5) 자체를 지금 고쳐 `run_stage_a`가 처음부터 두 객체를 받게 한다(같은 서명을 두 번 바꾸지 않음) | **(ii)를 먼저 확인하고, card B 구현이 이미 시작됐으면 design안**(OS-2가 서명을 바꾸고 card B·C의 `run_stage_a` 호출 test를 같은 변경에서 고친다). 어느 쪽이든 40 §2.4.5 '전달' 행 개정이 필요하다 | 다르지 않음 | 필요(승인된 40 design 개정, card B·C test 영향) |
| PD-9 공존 거부의 '판정 제약' 범위 | DS-U2(S-6 결정): 요구와 offset 판정 제약 셋의 공존 거부 | design OB-6(§4.2 L2): `human.constraints` 항목 전부를 출처 kind와 무관하게 거부한다. `judged` = 거짓인 `pending_spice` 항목까지 거부하고, `pending_constraints`(값 없는 이름 목록)는 허용 | design안(넓힘) | **결정 문언에 맞춘다**: `judged` = 참인 offset 제약만 거부한다. `pending_spice` 항목은 판정 제약이 아니므로 거부하지 않는다. 그 항목이 나중에 판정 제약이 되는 순간에는 같은 로더 검사가 거부하므로 fail-closed는 유지된다. `pending_constraints`는 허용 그대로 | 넓히면 결정(S-6) 문언과 다름 | **승인됨(S-10)** |
| W-1 사슬 진입점 | N7.2 OS-2: 실행기를 만들고 '옛 진입 흐름은 같은 변경에서 지운다'. 엔진에 제품 사슬 진입점이 없다는 사실은 적지 않았다 | design E-S13: 단계 A → B → 커널 컨텍스트 → 탐색 컨텍스트 → `find_front`를 잇는 제품 진입점이 없다(`run_gmid_design_pipeline`은 자리만, U16 미병합). 사슬은 test 하네스가 만든다(`tests/integration/nfr4_run_dump.py:376-401`). design 기본안 (i) | (i) OS-2 `run_plan`을 사슬 진입점으로 병합하고 하네스·test의 수작업 사슬을 같은 변경에서 대체한다. U16 `run_gmid_design_pipeline`은 `run_plan`을 부른다고 계약에 적는다.(→ 상위 v6.38.4 열여섯째 커밋 계획 검증 5 m-1: 진입점 이름은 하나 = OS-2 `run_plan`, 표면 이름은 OS-0 design; 'U16'은 상위 card 표에 없는 이름이라 정리) 병합 즉시 제품 CLI에서는 쓰이지 않는다. (ii) OS-2를 U16과 함께 병합한다 | **(i)**. 하네스 사슬이 지금 실제로 쓰이는 유일한 사슬이고, 대체하면 옛 수작업 사슬이 사라진다. **계획 요구로 더한다**(검증 B-1): 하네스는 `run_stage_b(..., diagnostic=True)`를 부르고(`nfr4_run_dump.py:387`), 단계 B 보고서 `diagnostic` 칸(`stage_b.py:129`)을 쓰며, `sctx.cache`·`sctx.domain.w_min_m`·`sctx.dc.base`를 읽는다(`nfr4_run_dump.py:401-421`). 그래서 `run_plan`은 (1) 진단 모드를 단계 B에 같은 뜻(측정만, 단계 A 상태·exit code 유지)으로 넘기고 결과에 그 표지를 싣고, (2) 변형마다 탐색 컨텍스트에서 하네스가 읽는 값(평가 결과 목록 -- card B 뒤 S3 메모리 색인의 평가 키 부분, 정의역, S0 수준 스냅샷)에 읽기 전용 자리를 두어야 한다. **(v0.7.2 정정, 검증 OS-M1, O-63 (3))** 색인·donors·계수에 닿는 값(평가 결과 목록 = 평가 키 부분)은 세션이 열린 동안 공개 세션 API로만 읽고(열기 → 변형 실행 → 읽기 → 닫기), 결과 객체(`run_plan` 결과·변형 결과)에는 그 참조를 두지 않는다(N3.12 ④ '닫기 = 버린다', N7.2 'v0.5 반영' W-1). 그 밖의 값의 자리와 세부 형식은 design. 옛 문언('결과 객체로 읽기 전용 참조로 내야 한다')은 history v0.7.2에 있다 | (i)은 '만들면 배선'의 제품 경로가 test 하네스라는 점에서 예외 | **필요**('만들면 배선' 승인) |
| F-1 OS-2 matching 검증 fixture | N7.1: 'OS-2의 검증 fixture는 기준이 이미 정의되는 회로로 고른다' | design §16.4 F-1: 차동 출력 회로여야 L4(단일 출력 기준 DC 검사) 없이 돈다. library 차동 출력 회로는 하나다(OT E-13). 값 `offset_in_max_v`·k는 사용자 값 | 단일 출력 회로를 고르고 '출력 기준 DC' 기능 뒤로 미룬다 | 오케스트레이터가 회로·spec 초안을 만들고 사용자가 회로와 값을 승인한다(T-9와 같은 절차, `origin: fixture`, library 밖·저장소 안) | 다르지 않음 | **승인됨(S-9)**: current_reuse_telescopic_ota 사본, {matching, k = 3, `offset_in_max_v` = 3 × 3.3 mV}, 위치 = library 밖 fixture(저장소 안, `assets/fixture/` 계열). 결정 기록의 '저장소 밖'은 오기였고 정정됐다(history) |

### N11.2 반영 위치

아래 항목은 모두 승인됐고(S-8·S-9·S-10·S-11) 표의 자리에 반영했다. 표에 없는 세부는 design v0.2가 옮긴다.

| ID | 바뀌는 곳 |
|---|---|
| PD-1 | N3.10 첫 행(주입 방식·분류), N3.6 공유 표의 S0 행(`achievability` 적중) |
| PD-2 | N3.5 '구현 시점', N7.2 OS-5·(TR 연결) 행, N9에 OD-3 위험 행 |
| PD-3 | N10.1 DS-2 → 닫힘, N10.3 G-S5 |
| PD-4 | N3.10 G-S1·G-S2 행, N9 XS-10 행 |
| PD-5 | 완료 조건 1, N3.2(요구 지문 규칙) |
| PD-6 | N3.4, N7.2 OS-2·OS-5 행 |
| PD-7 | N3.7 색인 상한, N7.2 OS-5 행(card C test 영향) |
| PD-8 | N3.6 블록 결과 색인 행, N3.9 개정 표(40 §2.4.5 '전달') |
| PD-9 | N3.2 로더 규칙 첫 행, N10.1 DS-U2 |
| V-1 | N3.11 소유 경계 표, N7.1, N7.2 OS-V 행 |
| W-1 | N7.2 OS-2 행(진입점·하네스 대체·진단 모드·결과 참조), 완료 조건 7 |
| F-1 | N7.1 추가 의존, N7.2 OS-2 선행 |
