# 계획서 v5.0 패치 재검증 (verify_v50.md 59건 반영 확인)

- 대상: `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` v5.0(964줄) 전체를 읽었다.
- 대조: `rewrite2/verify_v50.md` 표 1(59건)과 표 2(design 13개).
- 원자료 확인:
  - `probe_stage_partition.result.md` 3줄(R1/R2/R3 정의), 593~648줄(요약)
  - history.md 4961~4962줄("R1/R2 full은 대부분 0% -- 입력쌍의 gate→source→drain이 경유 비용 0인 우회로"), 2976~2980줄(다중 diff pair Case A/B/C), 3953줄(f_c 36.6MHz vs 실측 30.50MHz)
  - `sizing_recipe.py`: `validate_metric_units`:5813(이름 접미사-단위 규약 `unit_hint_from_metric_name` 존재), `node_pole_estimate`:4080(`undetermined` 반환), knee 중앙값 docstring:2557~2572
  - `tests/`에 TS6 승격 후보 7개와 `derive_achievable_bounds.py`가 모두 있다(Glob).
- 인용 표기: 절 번호+ID. 심각도는 **막음** / **혼동** / **경미**.
- stale 참조 grep: `N4.4`·`N4.5` 0건, `DEC-33` 0건. `I-A3/I-A4/I-B7/I-B9`는 DF 비고·N5.3 머리·A.2에만 남았다(의도대로).

---

## 1. 59건 판정

집계: **반영됨 53 / 부분 4(#8, #10, #40, #52) / 반영이 틀림(새 문제) 2(#9, #36) / 미반영 0**. "막음" 6건(#1~#6)은 모두 반영됐다.

| verify # | 판정 | 근거(새 문서 인용) |
|---|---|---|
| 1 (막음) | 반영됨 | N3.2-4 "gate->drain 비용 1, source->drain(캐스코드)·gate->source 비용 0, diode 노드 게이트의 gate->drain 비용 0(미러) ... DM 뷰에서는 입력쌍 공통 소스가 자기대응 넷(가상접지)이라 gate->source 우회로가 끊긴다 ... R3(DM/R2)". 요약표에서 R3(DM/R2)는 8/8·6/6·5/5·3/3·4/4·10/10이다. "전체 회로에 같은 비용을 쓰면 ... 0으로 떨어진다"는 history 4962줄과 요약 R2 0/n이 뒷받침한다 |
| 2 (막음) | 반영됨 | N6.1 6a "U-08, U-17. 6a-2는 U-06(J1~J6, J9 ports, 구조 정본)", 6b "U-06(J8), U-20", 7b "U-06(J3 정지전류, J7, J9 passive)". U-06 필요 시점 열도 같다. 남은 문제: J6의 7a 소비(새 문제 N7) |
| 3 (막음) | 반영됨 | N3.12.2 code-author "`docs/02-design/disputes/<id>.md`(자기 변경 id만)", 오케스트레이터 "`docs/02-design/**`(disputes 제외)". 남은 문제: 양식 `_TEMPLATE.md`의 소유자(N9) |
| 4 (막음) | 반영됨 | N3.5 실패 캐시 "S0가 없는 Phase 5~6a 전에는 지문 자리에 임시 지문(topology 파일 내용 해시 + spec 전체 해시 + 엔진 소스 파일 해시)을 쓰고, 6a에서 S0로 바꾼다. 임시 지문 레코드는 그 뒤 읽지 않는다(SC-d)". 남은 문제: N3.3 S3 저장 경로가 `<S0 지문>`만 적는다(N12) |
| 5 (막음) | 반영됨 | N3.5 "7c 전에는 그 Phase에 존재하는 단계만으로 `T_fixed`를 실측해 같은 식으로 N을 계산하고, 판정 기록에 어느 단계를 넣었는지 적는다(6b LRU 상한, 6c DOF 표본 수가 이 N을 쓴다)" |
| 6 (막음) | 반영됨 | 오케스트레이터 행 "`library/*.structure.json`(status 전이 기록만)". EL2 "무시 목록 = `.gitignore` 대상(`library/*.search_archive/`, 실행 산출물 `runs/`를 `.gitignore`에 등록)". N3.3 S1 "메모리(엔진 유도, 매 실행 재생성) + structure.json(ratified 기록만, 오케스트레이터가 씀)". 남은 문제: `.gitignore` 소유자(N5) |
| 7 | 반영됨 | N4.2 머리 "'도입'은 병합 판정에 적용되는 Phase다. 도구는 모두 Phase 0.5에서 완성되고, 0.5의 공격 시나리오·사례 재생에서 거부 동작을 증명한다" |
| 8 | 부분 | N6.1 Phase 1은 "IC3(필드 완전성·이름 충돌 검사 신설)·IC5(...) 활성", "TS0·IC3·IC5 red-green"으로 고쳤다. 그러나 N6.2 Phase 1 DoD는 여전히 "IC 전부 xfail 선언"이고 IC3·IC5 PASS가 없다(N1) |
| 9 | 반영이 틀림 | N3.12.3에 "test 전용 변경(TS2·TS3·TS5·TS6): 순서 4·5를 생략"을 더했다. 그런데 바로 위 bullet은 여전히 "동작을 보존하는 변경(TS1·TS2, ...)은 `equivalence`(test 커밋이 그대로이고 ...)"다. TS2가 두 규칙에 동시에 걸린다(N2) |
| 10 | 부분 | TS1 "추출 스크립트는 code-author가 작성하고 test-author가 Bash로 실행해 출력을 커밋한다". 스크립트를 담는 커밋이 test 커밋(순서 2)보다 앞서야 하는데, 흐름에서는 code-author가 순서 5에 온다(N3) |
| 11 | 반영됨 | V3 "변이는 worktree 밖 임시 복사본에서 수행하고 worktree는 바꾸지 않는다" |
| 12 | 반영됨 | EL3 "code 커밋이 `tests/**`(`tests/tools/**` 제외)·기준선·conftest를 바꾸면 차단". 남은 문제: TS6 이동이 두 소유 경로에 걸친다(N4) |
| 13 | 반영됨 | 순서 6 "오케스트레이터가 `git worktree add ../wt/<id>-audit <test 커밋>` 후 code 브랜치를 `--no-ff`로 병합한 상태를 만든다". N3.12.2 "경로 판정은 대상 경로를 해당 worktree 루트 기준 상대 경로로 바꾼 뒤 한다" |
| 14 | 반영됨 | N3.12.2 끝 "'사용자만' 경로는 Claude 세션의 도구 호출로 쓸 수 없다(EL1 거부) -- 사용자가 세션 밖에서 편집하거나, 부트스트랩 ④ 단계(hook 설치 전)에 오케스트레이터가 승인 기록과 함께 한 번 쓴다" |
| 15 | 반영됨 | N6.1 7a "`verified_by`(U-11 결과에 따라 SPICE AC gain 대조 포함)". N8 "SPICE를 처음 쓰는 Phase(U-11에 따라 7a 또는 7c)". 남은 문제: 7a DoD의 "N5.4 명시"가 N5.4에 없다(N10) |
| 16 | 반영됨 | N7.2 U-20 "`stack_headroom_slack_v`를 봉인 항목으로 흡수할지 ... 봉인 항목 1·5가 같은 사실을 보므로 metric 삭제 \| 6b". N5.3 I-C10 "6b, U-20". N6.1 6b 착수 조건에 U-20이 있다 |
| 17 | 반영됨 | N5.3 I-A10 "... folded는 `omega_c`를 노출하지 않아 측정 불가 \| 7a(...), DEC-49". DEC-25 상태 "4개 회로 선측정 미완 I-A10" |
| 18 | 반영됨 | V9 "... `matching_offset`/`matching_ratio` 관계 엣지 멤버의 (W/L, gm_id) 일치(허용오차 = 해당 LUT 격자 분해능)". 허용오차 근거는 N13 |
| 19 | 반영됨 | N6.1 6a "레지스트리 §2 ★ DUP(diode·미러 그룹·diffpair/tail)를 U-06 결론의 정본으로 통합하고 옛 함수 삭제", 7a "metric DUP 3쌍(gain/PM/CMRR) 통합" |
| 20 | 반영됨 | J6 "파일럿 M18a/M19/M18b를 stage1 부하(G_out)로, nmcnr M104/M106을 해당 stage 부하로 넣을지 \| 6a, 7a". probe 645·648줄과 맞는다 |
| 21 | 반영됨 | N6.3 "동작 변경 spec card마다 거부해야 할 입력의 test 존재" |
| 22 | 반영됨 | N6.2 7a "평가 기록에 MNA-블록 잔차 필드(4개 회로)", 7b "derived 필드마다 status·evidence·rule_hash", 3 "레지스트리 이관 목적지 열 = 실제 위치" |
| 23 | 반영됨 | N5.3 I-B22 "입력환산 오프셋의 다중 diff pair(cascade 입력환산, CMFB 오차증폭기) 처리 \| 7a(DEC-23)". history 2979~2980줄 Case B/C와 맞는다 |
| 24 | 반영됨 | U-21 "선언 L theta(`L_cascode`, `L_stage2out_*`)를 L 동치류 theta로 대체하고 삭제할지 \| DEC-18에 따라 삭제 \| 7b". N6.1 7b 착수 조건에도 있다 |
| 25 | 반영됨 | TS6 "승격(후보 `probe_gm_id_monotonicity`, ... `probe_prevention_wiring`)". 7개 파일 모두 존재한다 |
| 26 | 반영됨 | LR8 끝 "branch(`vertical_stack_id`, 전기)와 row(물리 행)는 다르다: PMOS/NMOS는 kind별 행으로 먼저 나뉘므로 같은 branch 안에서 L이 달라도 된다" |
| 27 | 반영됨 | LR5 "mirror = kind별 knee(`measure_L_knee`, 격자 전체 중앙값), bias_replica = `feasible_L_window` 하한, cascode·signal = knee 목표를 거부". "격자 전체 중앙값"은 sizing_recipe 2571줄에 근거가 있다 |
| 28 | 반영됨 | J8 "... `bias_replica` 의도(단서: vsb 오류 소자 M38/M60/M61/M68이 모두 `budget_reference_device` 보유)" |
| 29 | 반영됨 | DEC-25 "노드별 근사 `node_pole_estimate`는 못 세는 고임피던스 노드를 `undetermined`로 실패시킨다"(코드 4107줄과 맞음). I-A11 "크로스오버 주파수 해석 차이(선언식 36.6MHz 대 전체 응답 실측 30.50MHz)"(history 3953줄) |
| 30 | 반영됨 | DEC-08 "파일럿 Iref `value_amp = 1.2µA`는 사용자가 원문에서 확인한 고정 대상(사이징 경로 미배선, I-B14)" |
| 31 | 반영됨 | DEC-12 "멤버 vds가 미정이면 역할별 `min_vds`를 바닥으로 쓰고", 상태 "S1 관계 엣지 기반으로 전환, 6b" |
| 32 | 반영됨 | SC-b "재사용 시 `setdefault`로 기존 값을 건너뛰지 않는다(V6 lint 대상)" |
| 33 | 반영됨 | N0.3에 `gm-id-methodology.md` §13, `analog-topology-json-library.plan.md`, `.ai/context.md` 세션44~48 세 행이 있다 |
| 34 | 반영됨 | N3.12.6 agent 정의 "frontmatter `isolation`은 쓰지 않는다 -- worktree는 N3.12.3에서 오케스트레이터가 만든다" |
| 35 | 반영됨 | N3.15 "슬루율 필드 이름은 metric 단위 레지스트리(DEC-53)의 이름-단위 규약을 따라 하나로 정한다 ... `7b-compensation-allocation` design이 레지스트리 단위표를 인용해 적는다". 규약은 `validate_metric_units`의 `unit_hint_from_metric_name`으로 실재한다. N9.1 7b 목록에는 빠져 있다(N11) |
| 36 | 반영이 틀림 | 열 제목은 "exit code(서로 다른 비0 규약값, 분류 순서대로 배정)"인데 값은 NONCONVERGENT 4, SEAL_VIOLATION **4**다. "서로 다른"과 "분류 순서대로" 둘 다 어긋난다(N6) |
| 37 | 반영됨 | V3 "상수 변경(정수는 ±1, 실수는 표기된 마지막 자릿수 한 단위 ±)" |
| 38 | 반영됨 | N3.6 "수축 사상의 오차 한계 `|x_k − x*| ≤ q^k·|Δ0| / (1 − q)` ... q = 최근 두 연속 변화비의 최댓값이며 매 반복 갱신한다. q ≥ 1이 두 번 연속 관측되면 NONCONVERGENT". 한 번만 q ≥ 1일 때 식이 정의되지 않는다(N14, 경미) |
| 39 | 반영됨 | N3.5 "S2 LRU 상한 = (DEC-34 식의 샘플 수 + 선언 `n_starts` × 평가 계수기로 실측한 SLSQP 1회 평가 수) × 계산 블록 수" |
| 40 | 부분 | U-03 "근거: WP-01의 배선 대상은 저장소에 추적되는 파일", U-09 "근거: 4개 회로 측정(N6.3)이 Phase 4부터 ..."는 반영됐다. U-16 "근거: WP-07(role 메타데이터는 분석해 갱신할 수 있고 connectivity는 사용자 영역)"은 인용 대상이 틀렸다. N2.2 WP-07 원문("topology.json이 유일한 토폴로지 소스다. connectivity는 사용자 영역이다. test 픽스처는 ...")에는 role 메타데이터 갱신 허용 문장이 없다(N15) |
| 41 | 반영됨 | I-A6 "7b(슬롯은 `human.constraints`의 metric). 헤드룸 하한으로도 쓰는지는 6b design이 W4 창과 함께 판정". N9.1 6b 목록에는 빠져 있다(N11) |
| 42 | 반영됨 | DF-16 비고 "목적함수 전력 정의가 GB8 전력 정의와 같은 결정이라 7a로 옮긴다" |
| 43 | 반영됨 | N6.1 Phase 4 "IC7 활성" |
| 44 | 반영됨 | IC2 "노드전압 ≤ tol_V, 전류 ≤ tol_I, 그 밖의 연속 필드 ≤ tol_V 섭동의 감도 전파값" |
| 45 | 반영됨 | DEC-32 "순환 블록 수렴 허용오차는 LUT 보간 오차(leave-one-out)에서 ... LUT 격자 간격은 FD 스텝과 bisection 구간에 쓴다(식: N3.6, N3.7)" |
| 46 | 반영됨 | N5.3 머리 "v5.0에서 I-G3, I-G7, I-G8, ..." / A.2 "I-G8(N9.3)" |
| 47 | 반영됨 | A.2 "신설: I-A10(...), I-A11(...), I-B22(...), I-C10(옛 §10.5a-8, U-20), I-C11(옛 A66, U-09)". N0.4 문구와의 충돌은 N9(경미) |
| 48 | 반영됨 | N0.4 "IC·SC·V·GB·RC·TS·W·MT·EL·DF·I-*는 옛 번호와 같다. DEC·WP·U는 새 번호이며 부록 A.2로 찾는다" |
| 49 | 반영됨 | N0.4 "SP1 \| stage 분할 규칙(DM 뷰 + N3.2-4 엣지 비용)", DEC-43 "SP1(DM 뷰 + N3.2-4 엣지 비용)" |
| 50 | 반영됨 | N3.11 "`unit/test_mod1_gmid_lut.py ... unit/test_mod9_instance_report_builder.py`" |
| 51 | 반영됨 | A.2 "A70→DEC-18·DEC-19(knee 출발은 LR5)" |
| 52 | 부분 | 부록 B는 "(첫 번째 출현)", "(첫 번째 출현, v5.0 전문 블록 이전)", "(본문이 있는 첫 번째 출현)"으로 고쳤다. A.1 "§10.1, §10.6~§10.14 \| 이력 같은 번호", "§0, §0.1~§0.5 ... \| 이력 §0"은 앵커가 아직 모호하다 |
| 53 | 반영됨 | N2.1 범례에 "**원칙**(구현 대상이 아닌 규칙)"이 추가됐고 DEC-44·47·49·51 상태가 "원칙"이다. DEC-44·47의 날짜 열도 "원칙"이다(N16, 경미) |
| 54 | 반영됨 | N3.5 "DEC-34 식의 샘플 수", N3.7 "표본 수 = DEC-34 식의 샘플 수 안", N9.1 7c "DEC-34 샘플 수 구현" |
| 55 | 반영됨 | 옛 N4.2·N4.4를 지우고 번호를 당겼다. N0.2 auditor 순서 "N4.2 검사표 -> N3.12.3 흐름·판정 규칙 -> N3.5 계약 test 열". N0.4 V1~V10 "N4.2", N3.12.3 순서 6 "(N4.2)", N3.12.6 ③ "(N4.3)", N6.2 0.5 "N4.3 공격 11건", N6.3 "N4.2 도입 표", N9.1 00 "V 도입 표(N4.2)", A.1 "§14.5 / §14.6 → N4.2 / N4.3" 모두 새 번호와 맞는다 |
| 56 | 반영됨 | N5.3 머리 "DF와 같은 결함인 I-A3(DF-16), I-A4(DF-05), I-B7(DF-02), I-B9(DF-01)은 N5.2에만 둔다". 표에서 네 행이 빠졌고 DF 비고에 옛 ID가 남았다 |
| 57 | 반영됨 | DEC-33 행 삭제(grep 0건), A.2 "D3→N6.1" |
| 58 | 반영됨 | N0.1 "탐색·test 결과 수치를 보고할 때는 auditor 판정 기록(N3.12.5)에서만 인용한다(설계 입력인 사실 수치는 예외)" |
| 59 | 반영됨 | N3.13-6 "호출 도구는 기존 `derive_achievable_bounds.py`(TS6에서 `tests/tools/`로 이동)를 재사용한다". TS6 "운영 도구 `derive_achievable_bounds.py`는 `tests/tools/`로 이동". 이동의 소유권 문제는 N4 |

---

## 2. 패치로 새로 생긴(또는 드러난) 문제

| # | 심각도 | 위치·인용 | 문제 | 수정안(구체 문장) |
|---|---|---|---|---|
| N8 | **막음** | N3.2-6 "부호가 섞이면 `review_needed`(Cc–Rz 직렬 루프는 J7)". N3.3 "유도 값을 평가가 소비하기 시작하는 6c부터 `review_needed`가 남아 있으면 GB4 전에 정지한다". N6.1·U-06·N7.1은 J7을 **7b**에 둔다. N6.2 6c DoD "블록·y 목록(4개 회로)" | Cc–Rz가 있는 회로(two_stage·nmcnr)는 6a에서 J7 판정이 `review_needed`로 남는다. 그러면 6c에서 STRUCTURE_UNRESOLVED로 멈춘다. 결국 6c DoD(4개 회로)를 채울 수 없다. U-06 시점을 J별로 나누는 패치(#2)에서 J7을 7b로 둔 결과다 | U-06 필요 시점과 N6.1 6a-2 착수 조건의 J 목록에 J7을 넣는다: "6a-2(J1~J7, J9 ports, 구조 정본)". N7.1 J7 소비 Phase를 "6a(극성 ratify), 7b(보상 규칙 소비)"로 고친다. 7b에 J7을 남기려면 N3.3에 "6c 정지 판정은 소비 Phase가 6c 이하인 J 항목의 `review_needed`만 본다"를 적는다. 다만 이 방식은 WP-02의 skip 검토 대상이다 |
| N1 | 혼동 | N6.1 Phase 1 "IC3 ... IC5 ... 활성". N6.2 Phase 1 DoD "IC 전부 xfail 선언(담당 Phase 명시)" | 패치(#8)가 범위와 판정 유형만 고쳤다. DoD는 IC3·IC5까지 xfail로 선언하라고 읽힌다. 담당 Phase(N4.1)가 1인데 PASS 조건이 없다 | N6.2 Phase 1을 "IC3·IC5 PASS, 나머지 IC xfail 선언(담당 Phase 명시)"로 고친다 |
| N2 | 혼동 | N3.12.3 판정 유형 bullet "동작을 보존하는 변경(TS1·**TS2**, Phase 2 통합, Phase 3 이동)은 `equivalence`(**test 커밋이 그대로이고** base와 병합본 모두 통과...)". 다음 bullet "test 전용 변경(**TS2**·TS3·TS5·TS6): 순서 4·5를 생략" | TS2는 test를 새로 쓰는 변경이라 "test 커밋 불변"을 만족할 수 없다. 두 규칙 중 어느 증거를 V2·EL4가 요구하는지 정해지지 않는다 | 첫 bullet의 괄호를 "(TS1, Phase 2 통합, Phase 3 이동)"으로 줄인다. V2 판정 규칙에 "test 전용 변경: 섹션->test 매핑표의 모든 섹션이 변경 후 test에서 PASS(N3.12.3)"를 셋째 유형으로 더한다. N3.12.5 `evidence_type`에 `test-only`를 추가한다 |
| N3 | 혼동 | TS1 "추출 스크립트는 code-author가 작성하고 test-author가 Bash로 실행해 출력을 커밋한다". N3.12.3 순서 1~2는 test-author가 `<base>`에서 분기한 worktree에서 먼저 커밋한다. code-author는 순서 5다 | 스크립트(`tools/migrate/**`)가 base에 없으면 test-author가 순서 2에서 실행할 수 없다. 스크립트를 담는 변경의 spec card와 판정 유형도 없다 | TS1에 이 문장을 더한다: "추출 스크립트는 선행 변경 `<id>-extract-tool`(code-author 단독, 판정 유형 red-green: test-author가 합성 입력 파일에서 추출 결과를 단정하는 test)로 먼저 병합하고, TS1 변경의 `<base>`는 그 병합 커밋이다" |
| N4 | 혼동 | TS6 "운영 도구 `derive_achievable_bounds.py`는 `tests/tools/`로 이동". 현재 위치 `tests/derive_achievable_bounds.py`는 test-author 경로(`tests/**`), 목적지 `tests/tools/**`는 code-author 경로다. N3.12.3 "test 전용 변경(... TS6): 순서 4·5를 생략" | 한 역할이 이동(삭제+추가)을 한 커밋으로 할 수 없다. test-author는 목적지에 쓸 수 없고(EL1), code-author는 원본을 지울 수 없다. TS6를 test 전용으로 두면 code-author 단계가 없어 목적지를 쓸 주체가 없다 | TS6에 이 문장을 더한다: "운영 도구 이동은 code 커밋(`tests/tools/`에 추가, `Role: code`) 뒤 test 커밋(원본 삭제, `Role: test`)의 두 커밋으로 하고, 이 부분만 순서 4·5를 생략하지 않는다" |
| N5 | 혼동 | EL2 "무시 목록 = `.gitignore` 대상(... `.gitignore`에 등록) + ...(무시 목록 변경은 사용자만)". N3.12.2 '사용자만' 행 "`.githooks/**`, `.claude/**`, `install.py`, ..."에 `.gitignore`가 없다. hook 판정 범위 "`agent_type`이 없고 대상 경로가 위 표의 경로와 겹치는 호출만 판정" | `.gitignore`가 경로표에 없어서 메인 세션의 `.gitignore` 편집은 hook이 판정하지 않고 통과한다. 그러면 오케스트레이터가 무시 목록을 넓혀 EL2를 무력화할 수 있다. "사용자만"이라는 규칙과 강제 장치가 어긋난다. `search_archive`·`runs/` 등록을 누가 언제 하는지도 없다 | '사용자만' 행에 "`.gitignore`"를 더한다. N3.12.6 ①에 "`.gitignore`에 `library/*.search_archive/`, `runs/` 등록(부트스트랩 예외, 승인 기록)"을 더한다 |
| N6 | 경미 | N3.14 열 제목 "서로 다른 비0 규약값, 분류 순서대로 배정", NONCONVERGENT 4 / SEAL_VIOLATION 4 | 제목과 값이 모순이다(#36 반영 오류) | SEAL_VIOLATION을 5, SEARCH_FAILED를 6으로 바꾼다. 둘을 같은 코드로 두려는 의도라면 제목을 "탐색 시작 전 정지와 탐색 중 실패를 구분하는 비0 규약값"으로 바꾸고 4의 공유 이유를 적는다 |
| N7 | 경미 | N7.1 J6 소비 Phase "6a, 7a". N6.1 7a 착수 조건 "U-07, U-10, U-11, U-19", U-06 필요 시점 "6a-2(J1~J6 ...) / 6b(J8) / 7b(...)" | J6은 7a에서 소비되는데 7a 착수 조건과 U-06 시점에 없다(6a-2에서 이미 ratify되므로 실질 차단은 아니지만 표끼리 어긋난다) | J6 소비 Phase를 "6a(ratify), 7a(gain metric이 소비)"로 적는다. N6.1 7a 착수 조건에 "J6 승인 기록(6a-2에서 확정)"을 더한다 |
| N9 | 경미 | N0.4 "IC·SC·V·GB·RC·TS·W·MT·EL·DF·I-*는 옛 번호와 같다" | A.2와 N5.3에 신설 ID(SC-e, DF-22, I-A10, I-A11, I-B22, I-C10, I-C11)가 있다 | "... 옛 번호와 같다(신설 번호는 A.2 '신설' 표기)"로 고친다 |
| N10 | 경미 | N6.2 7a "U-11이 SPICE를 7c로 두면 '검증 대기' 표시 + N5.4 명시". N5.4 목록은 I-B21, DF-16, DF-03, DF-18뿐이다 | 참조한 목록에 해당 항목이 없다 | N5.4 끝에 "U-11이 SPICE를 7c로 둔 경우 7a~7c 사이 gain metric의 `verified_by` 검증 대기"를 더한다 |
| N11 | 경미 | N9.1 6b "... J8 결론 반영"(U-20, I-A6 판정 없음). N9.1 7b(U-21, 슬루율 명칭 없음). N3.15 "실제 이름은 `7b-compensation-allocation` design이 ... 적는다", I-A6 "6b design이 W4 창과 함께 판정" | 본문이 design에 넘긴 작업이 해당 design 문서 필수 목록에 없다. N9.2-8(열린 질문 금지)과 겹치면 빠뜨리기 쉽다 | N9.1 6b에 "U-20 반영, I-A6 헤드룸 하한 여부 판정"을, 7b에 "U-21 반영, 슬루율 필드 명칭(DEC-53 규약 인용)"을 더한다 |
| N12 | 경미 | N3.3 S3 "키 = S0 전체 지문", 저장 "`search_archive/<S0 지문>/...`". N6.1 Phase 5 "S3 레코드 v1" | Phase 5~6a 동안의 저장 디렉터리 이름이 N3.3에 없다(N3.5 임시 지문과 연결되지 않음) | N3.3 S3 저장 열에 "(Phase 5~6a 전은 N3.5 임시 지문을 디렉터리 이름으로 쓴다)"를 더한다 |
| N13 | 경미 | V9 "(W/L, gm_id) 일치(허용오차 = 해당 LUT 격자 분해능)" | W는 LUT 격자 변수가 아니다. W/L 허용오차의 근거 식이 없다(WP-03) | "gm_id는 LUT gm_id 격자 간격, W/L은 같은 ID에서 그 gm_id 허용오차가 만드는 IDu 차의 상대값"으로 계산식을 적는다 |
| N14 | 경미 | N3.6 "q ≥ 1이 두 번 연속 관측되면 NONCONVERGENT" | q ≥ 1이 한 번만 나온 반복에서는 `1/(1−q)` 상한식이 정의되지 않는다. 이때 상한을 어떻게 다룰지 없다 | "q ≥ 1인 반복에서는 상한을 갱신하지 않고 직전 상한을 유지한다"를 더한다 |
| N15 | 경미 | U-16 "근거: WP-07(role 메타데이터는 분석해 갱신할 수 있고 connectivity는 사용자 영역), WP-08" | WP-07 본문에는 괄호 속 전반부가 없다. 인용이 원문과 다르다 | WP-07을 "topology.json이 유일한 토폴로지 소스다. connectivity는 사용자만 수정하고, role·matching 메타데이터는 분석해 갱신할 수 있다. ..."로 고친다(메모리 topology_json_single_source와 같은 문장) |
| N16 | 경미 | N2.1 DEC-44·DEC-47 날짜 열 "원칙" | 날짜 열에 상태 값이 들어갔다 | 결정 날짜(원자료 `rewrite_X_decisions.md`)를 적는다. 날짜가 없으면 "--"로 둔다 |
| N17 | 경미 | N3.12.2 오케스트레이터 "`docs/02-design/**`(disputes 제외)". N3.12.6 양식 "`docs/02-design/disputes/_TEMPLATE.md`" | 부트스트랩 뒤에는 dispute 양식을 고칠 주체가 없다(code-author는 "자기 변경 id만") | 오케스트레이터 행을 "`docs/02-design/**`(disputes는 `_TEMPLATE.md`만)"으로 고친다 |
| N18 | 경미 | N3.12.3 순서 6 "code 브랜치를 `--no-ff`로 병합한 상태", 순서 7 "merge gate(EL4) 통과 시에만 병합" | 순서 7이 병합하는 대상(code 브랜치인지 audit worktree의 병합 커밋인지)과 그 병합 커밋의 트레일러를 정하지 않았다. EL4는 "모든 커밋의 트레일러"를 검사한다 | 순서 7을 "오케스트레이터가 audit worktree의 병합 커밋(트레일러 `Role: doc`, EL4는 merge 커밋의 트레일러 검사를 면제하고 부모 커밋만 검사)을 base 브랜치로 fast-forward한다"로 고친다 |

---

## 3. design 문서 13개 판정

| design 문서 | 이전 판정 | 판정 | 남은 걸림(#) |
|---|---|---|---|
| `00-common` | 착수 가능 | 착수 가능 | exit code 중복(N6), `test-only` 증거 유형(N2) |
| `05-role-separation` | 막힘 | **혼동** | `.gitignore` 소유(N5), 병합 커밋과 EL4(N18), dispute 양식 소유(N17). 막던 #3·#6·#11~#14는 해소. 착수 조건 U-15·U-16 |
| `10-test-separation` | 혼동 | **혼동** | TS2 판정 유형 이중(N2), TS1 추출 스크립트 선행 병합(N3), Phase 1 DoD IC3·IC5(N1). 착수 조건 U-01 |
| `20-dead-code-dup` | 착수 가능 | **혼동** | TS6 운영 도구 이동의 역할 경계(N4). U-02 |
| `30-module-split` | 착수 가능 | 착수 가능 | 없음(U-03) |
| `40-defect-fixes` | 착수 가능 | 착수 가능 | 없음(U-04·U-05·U-09) |
| `50-failure-cache` | 막힘 | **착수 가능** | 저장 디렉터리 이름(N12, 경미) |
| `6a-structure-stage` | 막힘 | **착수 가능** | J7을 6a-2에서 ratify할지(N8, 6a가 결정할 몫은 아니지만 대조표 범위에 영향). U-06·U-08·U-17 |
| `6b-node-voltage-seal` | 막힘 | **착수 가능** | N9.1 목록 누락 U-20·I-A6(N11), 반복 상한 q≥1 1회(N14), V9 허용오차(N13) |
| `6c-coupling-achievability` | 혼동 | **막힘** | J7 `review_needed` 잔존 -> 6c 정지 -> 4개 회로 DoD 불가(N8) |
| `7a-gain-metric` | 혼동 | 착수 가능 | J6 착수 조건 표기(N7), N5.4 검증 대기(N10). U-07·U-10·U-11·U-19 |
| `7b-compensation-allocation` | 혼동 | 착수 가능 | N9.1 목록 누락 U-21·슬루율 명칭(N11). U-12·U-13·U-14·U-21·U-06(J3·J7·J9) |
| `7c-archive-spice` | 착수 가능 | 착수 가능 | 없음 |

집계: 착수 가능 9 / 혼동 3 / 막힘 1(`6c`).

---

## 4. 남은 "근거 없는 신규 내용"

| 내용 | 판정 |
|---|---|
| N3.2-4 "DM 뷰가 아닌 전체 회로에 같은 비용을 쓰면 우회로 때문에 입력단 stage 번호가 0으로 떨어진다" | 근거 있음(history 4962줄, probe 요약 R1/R2 full 0/n) |
| N3.15 슬루율 "이름-단위 규약" | 근거 있음(`unit_hint_from_metric_name`, `validate_metric_units` docstring (3)) |
| LR5 "격자 전체 중앙값" | 근거 있음(sizing_recipe 2557~2572줄) |
| I-A11 "선언식 36.6MHz 대 전체 응답 실측 30.50MHz" | 근거 있음(history 3953·4169·2180줄) |
| I-B22 "cascade 입력환산, CMFB 오차증폭기" | 근거 있음(history 2979~2980줄) |
| DEC-25 `node_pole_estimate` `undetermined` | 근거 있음(코드 4107·4111줄) |
| N3.6 q 규칙("최근 두 연속 변화비의 최댓값", "두 번 연속") | 식의 근거(수축 사상 오차 한계)는 적혀 있다. "두 번 연속"이라는 횟수는 여전히 규약 선택이다(경미, 설명 한 줄 권장) |
| V9 W/L 허용오차 "LUT 격자 분해능" | **근거 없음**(N13) |
| N3.14 exit code 2/3/4/4/5/1 | **근거 없음 + 자기모순**(N6) |
| U-16 근거 문장 | **인용 불일치**(N15) |
| N6.2 7b "Pareto 제시·정지와 사용자가 고른 점의 재실행" | ambiguities P7b-07이 요구한 DoD 분기를 채운 설계 선택이다. 근거는 DEC-07·U-13으로 충분하다 |
| N3.12.3 순서 6 `--no-ff` 병합 주체 | verify #13 수정안 그대로다. 병합 커밋 처리만 빠졌다(N18) |
