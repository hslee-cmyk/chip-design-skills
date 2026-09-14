# 계획서 v5.0 재구성 독립 검증

- 대상: `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` v5.0(968줄)을 전부 읽었다. 대조 원문은 v4.49 전문(history.md 안의 `~~~~markdown` 블록, 3480~5043줄)이다.
- 대조 감사: `rewrite2/contradictions.md`(47건), `ambiguities.md`(118건), `duplication_history_map.md`.
- 원자료·코드 확인에 쓴 것:
  - `probe_stage_partition.result.md`의 1~20줄과 593~648줄
  - 레지스트리 34~43줄
  - `sizing_recipe.py`(`lut_conditions_from_npz`:5355, `_RESOLVE_STALE_NOTES`:8367, `achievable_metric_bound`:8271, `InfeasibleSizingError`:6984)
  - `tests/` 아래 파일 존재 여부(`probe_interp_scheme_loo.py`, `probe_mirror_gain_ranking.py`, `derive_achievable_bounds.py`)
  - `install.py`의 `--only hooks --project`(12줄)
  - `slew_rate_*` grep(저장소 전체)
- 인용 표기: 새 문서는 절 번호+ID(예: `N3.2-4`)로, 옛 문서는 v4.49 절 번호로 쓴다. `hist:N`은 history.md의 줄 번호다.
- 심각도: **막음**(해당 design 문서를 쓸 수 없거나 틀리게 쓰게 됨) / **혼동** / **경미**.
- ambiguities.md에는 "top 15" 목록이 없다(rewrite2 폴더 grep 결과 0건). 그래서 top 15만 고르지 않고 118건 전부를 개별 판정했다(부록 2).

---

## 1. 지적 사항

| # | 과제 | 심각도 | 새 문서 위치·인용 | 옛 문서·감사 근거 | 문제 | 수정안(구체 문장) |
|---|---|---|---|---|---|---|
| 1 | 4, 3 | **막음** | N3.2-4 "gate->drain 비용 1, source->drain 비용 0, **gate->source 엣지는 쓰지 않는다**" + N3.2-7 "4개 회로 실측 100% 일치" | probe 결과 3줄: "R1=gd엣지 1회당 +1(**sd/gs 0**), R2=R1+diode 게이트 gd 0, R3=DM/CM 뷰에서 R2". 요약 593~644줄: 4회로 전부 100%인 규칙은 **R3(DM/R2)**(gs 엣지를 비용 0으로 포함)뿐이다. gs 엣지를 뺀 R2ng는 folded에서 4/5다. **DM/R2ng 조합은 측정한 적이 없다.** ambiguities P6a-03은 "채택 = R3(DM/R2)"라고 적었다. | SP1은 측정하지 않은 조합(DM 뷰 + gs 제외)을 정의해 놓고 "100% 실측"을 근거로 댄다. 6a 설계자가 이 규칙을 그대로 구현하면 회귀 기준의 근거가 사라진다. | N3.2-4를 이렇게 바꾼다: "gate->drain 비용 1, source->drain·gate->source 비용 0, diode 노드 게이트의 gate->drain 비용 0. DM 뷰에서는 입력쌍 공통 소스가 자기대응 넷(가상접지)이므로 gate->source 우회로가 끊긴다(측정 규칙 R3(DM/R2), probe_stage_partition 요약)." gs 엣지를 빼는 쪽으로 가려면 DM/R2ng를 4회로에서 다시 측정한 결과를 먼저 첨부한다. |
| 2 | 3 | **막음** | N6.1 6a "추가 착수 조건: U-06(J1~J9), U-08, U-17". 같은 행 범위에 "6a-1 유도·대조표, 6a-2 공동분석·ratify". N7.1의 소비 Phase는 J7=7b, J8=6b | contradictions #10(J1~J9는 6a-1 대조표 없이 판정할 수 없다. 해소안은 착수 조건에서 J 제거). ambiguities P6a-09 | 공동분석의 입력인 대조표를 6a-1이 만드는데, J1~J9 전부가 6a **착수** 조건이다. 옛 모순 #10이 그대로 남았다. 또 J7(7b)·J8(6b)이 6a를 막고, 6b 행에는 J8이 없다. | N6.1 6a 추가 착수 조건을 "U-08, U-17"로 줄인다. 6a-2 착수 조건에 "U-06(J1~J6, J9 ports)"를 두고, 6b에 "J8", 7b에 "J3, J7, J9 passive"를 둔다. N7.2 U-06의 필요 시점도 "6a-2 / 6b / 7b(J 항목별, N7.1 소비 Phase)"로 고친다. |
| 3 | 3 | **막음** | N3.12.3 순서 5 "code-author ... `docs/02-design/disputes/<id>.md`에 근거를 쓰고 멈춘다". N3.12.2 경로표에서 code-author 쓰기 경로에 `docs/02-design/**`가 없다(오케스트레이터 전용) | 옛 §14.3 [4] `disputes/<id>.md`는 작성자가 쓰는 것이었다. ambiguities P05-14(경로 확정) | EL1이 code-author의 dispute 작성을 거부한다. 흐름 자체가 실행되지 않는다. | N3.12.2 gmid-code-author 행에 "`docs/02-design/disputes/<id>.md`(자기 변경 id만)"를 더한다. 오케스트레이터 행은 "`docs/02-design/**`(disputes 제외)"로 고친다. |
| 4 | 3, 5 | **막음** | N3.5 실패 캐시 "키 = (θ 성분 `float.hex`, **S0 지문**)". N3.3 S3 "키 = S0 전체 지문". N6.1 Phase 5 "S3 레코드 v1". S0는 N6.1 6a에서 생긴다 | ambiguities X07(Phase 5가 쓸 키는 당장 계산 가능한 지문이어야 하고, 6a에서 S0로 교체). P5-01 | Phase 5(`50-failure-cache`)가 아직 존재하지 않는 S0 지문을 키로 써야 한다. design을 쓸 수 없다. | N3.5 실패 캐시 뒤에 이 문장을 더한다: "Phase 5~6a 전: 키의 지문 = topology 파일 내용 해시 + spec 전체 해시 + 엔진 소스 파일 해시(임시 지문). 6a에서 S0로 교체하며, 임시 지문 레코드는 읽지 않는다(SC-d)." |
| 5 | 3, 5 | **막음** | N3.5 "S2 LRU 상한 = (D4 식의 샘플 수 + `n_starts` × `maxiter`) × 계산 블록 수"(6b). N3.7 DOF "표본 수 = D4 식의 샘플 수 안"(6c). N3.5 D4: `T_fixed` = presolve, GB0~GB5, **DP, 좌표강하, SLSQP** 실측 합(7b 이후에야 존재) | ambiguities P6b-08, P6c-03(상한은 D4 계산값에서) | 6b·6c design이 7c에서야 계산되는 N에 의존한다. 6b의 LRU 상한을 정할 수 없다. | N3.5에 이 문장을 더한다: "7c 전의 N은 그 Phase에 존재하는 단계만으로 `T_fixed`를 실측해 같은 식으로 계산하고, 판정 기록에 어느 단계를 넣었는지 적는다." |
| 6 | 3 | **막음** | N3.3 S1 저장 "`library/<name>.structure.json`(ratified 기록, 6a)", 전이 "`review_needed`->`ratified` / 오케스트레이터". S3 "`library/<name>.search_archive/...`". N3.12.2 오케스트레이터 경로는 `library/*.topology.json`뿐이다. EL2 무시 목록은 `.gitignore`와 `__pycache__`, `.pytest_cache`뿐이다 | ambiguities P6a-06(structure.json 신설), P7c-03(archive), P05-18(부산물 무시 목록) | ① 오케스트레이터가 ratified를 기록할 파일에 쓰기 권한이 없다. ② test-author·auditor가 파이프라인을 돌리면 생기는 search_archive·structure.json이 EL2 위반이 되어 완료가 거부된다. | 오케스트레이터 행에 "`library/*.structure.json`(status 전이 기록만)"을 더한다. EL2 무시 목록에 "`library/*.search_archive/**`(`.gitignore`에 등록)"을 더한다. structure.json 가운데 엔진이 쓰는 derived 부분과 사람이 쓰는 ratified 부분을 한 파일에 둘지 두 파일로 나눌지 N3.3에 적는다. |
| 7 | 3 | 혼동 | N4.3 V4·V5·V6 "도입 1". N6.2 0.5 "공격 11건 거부 로그 + 사례 5건 적발". N4.5 공격 6~9와 사례 e329283·e5fbf92·3250baa·1b9b4ea·2e1944a의 기대 거부는 V4/V5/V6 | contradictions #4(검사별 활성 Phase 표) | 0.5 DoD가 "도입 1"인 검사로 적발해야 한다. 도구는 0.5 산출물(N3.12.6)에 있으므로 뜻은 "도구 0.5 완성, 병합 판정 적용 1"로 보인다. 그런데 문서에 그 구분이 없다. | N4.3 머리에 이 문장을 더한다: "'도입'은 병합 판정에 적용되는 Phase다. 도구는 모두 0.5에서 완성되고, 0.5의 redteam 재생에서 거부 동작을 증명한다." |
| 8 | 3, 5 | 혼동 | N6.1 Phase 1 "IC3·IC5 활성", 판정 유형 "TS0 red-green, 나머지 equivalence". N4.1 IC3 test는 "필드·이름 충돌 0", IC5는 "게이트 docstring 전수" | 옛 §3.3 C3 "필드 완전성·이름 충돌 검사가 없음", C5 "19개 중 4개만 명시"(지금 돌리면 FAIL) | IC3·IC5를 Phase 1에서 PASS시키려면 검사 신설과 게이트 docstring 수정(code 변경, red-green)이 필요하다. Phase 1은 equivalence만 허용하고 범위에도 없다. | N6.1 Phase 1 범위에 "IC3(필드 완전성·이름 충돌 검사 신설)·IC5(게이트 docstring '검사하지 않는 것' 절 추가)"를 적고 판정 유형을 "TS0·IC3·IC5 red-green, 나머지 equivalence"로 고친다. 아니면 IC3·IC5 담당을 Phase 4로 옮긴다. |
| 9 | 3, 5 | 혼동 | N3.12.3 흐름은 test 커밋(2) -> code 커밋(5)를 전제한다. N6.1 Phase 1의 TS2·TS3·TS5는 tests만 바꾸는 변경이다. equivalence 정의는 "test 커밋 불변 + base·병합본 모두 통과" | ambiguities P1-06(TS1 순서만 다룸) | code 커밋이 없는 test 전용 변경(TS2 pytest화, TS3 print->assert, TS5 기준선 삭제)의 흐름과 V2 증거가 정의돼 있지 않다. | N3.12.3 판정 유형 뒤에 이 문장을 더한다: "test 전용 변경(TS2·TS3·TS5·TS6): 순서 4·5를 생략한다. 증거 = 변경 전 test 집합이 base에서 통과시킨 섹션을 변경 후 test가 모두 PASS함(섹션->test 매핑표, `10-test-separation`)." |
| 10 | 3, 5 | 혼동 | N3.11 TS1 "추출 스크립트(`tools/migrate/extract_selftest.py`)로 `tests/legacy/`에 본문 그대로 이관. test 커밋(legacy 추가)". DEC-38 "test-author는 소스 경로 Read 거부" | contradictions #5(기본안: 추출 스크립트는 auditor가 실행하고 결과만 test-author에게 전달) | 스크립트를 누가 실행하는지 없다. 결과는 test-author 경로(`tests/legacy/`)에 쓰여야 하는데 스크립트는 소스를 읽는다. | TS1에 이 문장을 더한다: "추출 스크립트는 code-author가 작성하고, test-author가 Bash로 실행해 출력을 커밋한다(스크립트 실행은 Read 도구 거부 대상이 아니다. 산출물이 본문 그대로임은 auditor의 stdout 동등성으로 판정)." |
| 11 | 3 | 혼동 | N3.12.2 auditor 경로 `.ai/verification/**`. N4.3 V3 "변이마다 그 함수를 호출하는 test만 실행". EL2는 worktree `git status`를 경로표와 대조한다 | ambiguities P05-08 | 뮤테이션은 소스를 바꿔야 한다. auditor worktree에서 하면 EL2 위반이 되어 완료가 거부된다. | V3 판정 규칙에 이 문장을 더한다: "변이는 worktree 밖 임시 복사본(또는 메모리 import 훅)에서 수행하고 worktree는 바꾸지 않는다." |
| 12 | 3 | 혼동 | N3.12.4 EL3 "code 커밋이 tests·기준선·conftest를 바꾸면 차단". N3.12.2 code-author 경로에 `skills/analog-gmid-design/assets/tests/tools/**` | ambiguities P05-07(경로 분류표) | code-author 소유인 `tests/tools/**`를 바꾸는 code 커밋을 EL3가 차단한다. | EL3를 "code 커밋이 `tests/**`(`tests/tools/**` 제외)·기준선·conftest를 바꾸면 차단"으로 고친다. |
| 13 | 3, 5 | 혼동 | N3.12.3 "`git worktree add ../wt/<id>-test`", 순서 6 "auditor ... `../wt/<id>-audit`에서 병합본 검증". 경로표 glob는 저장소 상대(`skills/...`) | ambiguities P05-17(병합본 생성 방법·주체) | ① audit worktree와 병합본 커밋을 누가 만드는지 없다. ② hook이 받는 절대 경로(`../wt/...`)를 경로표 glob에 어떻게 대응시킬지(worktree 루트 기준 상대화) 없다. | 순서 6 앞에 "오케스트레이터가 `git worktree add ../wt/<id>-audit <test 커밋>` 후 code 브랜치를 `--no-ff` 병합한 상태를 만든다"를 넣는다. N3.12.2 끝에 "경로 판정은 대상 경로를 해당 worktree 루트 기준 상대 경로로 바꾼 뒤 한다"를 넣는다. |
| 14 | 3 | 혼동 | N3.12.2 "사용자만: `.githooks/**`, `.claude/**`, `install.py`, `agents/gmid-*.md`". hook 판정 범위 "`agent_type`이 없고 대상 경로가 표와 겹치는 호출" | contradictions #1 | Claude 메인 세션에서는 사용자 지시와 오케스트레이터를 hook이 구별하지 못한다. "사용자만" 경로는 사실상 세션 밖에서만 편집할 수 있는데 그 점이 적혀 있지 않다. N3.12.6 ④의 `.githooks/pre-commit` 갱신 주체도 없다. | N3.12.2 끝에 이 문장을 더한다: "'사용자만' 경로는 Claude 세션의 도구 호출로 쓸 수 없다(EL1 거부). 사용자가 세션 밖에서 편집하거나, 부트스트랩 ④ 단계(hook 설치 전)에 오케스트레이터가 사용자 승인 기록과 함께 한 번 쓴다." |
| 15 | 3 | 혼동 | N6.1 7a 범위 "`verified_by`와 SPICE AC gain 대조". N3.8 `verified_by` 적용 순서는 U-11. N7.2 머리 "기본안은 ... **확정 전에는 구현하지 않는다**". N8 "SPICE 모델·ngspice 환경 부재 -> **7c** design 첫 단계에서 확인" | ambiguities P7a-06(선택지 ①·② 중 사용자 결정) | 미확정인 U-11 기본안(SPICE AC를 7a로 당김)이 7a 범위에 확정된 것처럼 들어가 있다. 환경 확인 시점(7c)과도 어긋난다. | N6.1 7a 범위를 "`verified_by`(U-11 결과에 따라 SPICE AC gain 대조 포함)"로 고친다. N8 대응을 "SPICE를 처음 쓰는 Phase(U-11에 따라 7a 또는 7c) design 첫 단계에서 확인"으로 고친다. |
| 16 | 3, 5 | 혼동 | N5.3 I-C10 "6b(봉인 항목으로 흡수 여부를 **design에서 결정**)". N9.2-8 "열린 질문: 없어야 한다. 남으면 N7에 추가를 요청하고 그 항목을 구현하지 않는다" | 옛 §10.5a-8(A8 폐기 뒤 담당 없음) | 계획서가 스스로 결정을 design에 넘기면서, 동시에 design의 열린 질문을 금지한다. | I-C10을 N7.2에 U-20("`stack_headroom_slack_v`를 봉인 항목으로 흡수할지 metric 제약으로 남길지", 기본안: 봉인 항목 1·5가 같은 사실을 보므로 metric 삭제, 필요 시점 6b)으로 올린다. |
| 17 | 1 | 혼동 | N3.8, N5.3 모두 folded의 `parasitic_pm_deg` 측정 가능성을 언급하지 않는다. DEC-25 "구현됨", DEC-49 "4개 회로에서 먼저 잰 뒤 정한다" | 옛 §7.0 §7.11:669-671 판정 "대체됨 -- **현행 제약 상태 + 4회로 측정 미완을 함께 기록**", 근거 "folded_cascode는 `omega_c` 미노출로 측정 불가(context:14324) -- A73 미충족" | DEC-49 원칙을 어긴 채 걸려 있는 제약(파일럿만 선측정)이 열린 항목에서 빠졌다. | N5.3에 행을 더한다: "I-A10(신설) \| `parasitic_pm_deg >= PM_target_deg` 제약이 4회로 선측정 없이 걸려 있다(folded `omega_c` 미노출) \| 7a(`smallsignal_gain_db` 이관 시 omega_c 노출), DEC-49". |
| 18 | 1 | 혼동 | N4.3 V9 "4개 회로 결과가 봉인 항목(N3.6)과 IC1을 통과". N3.6 봉인 항목에 매칭 대칭이 없다 | 옛 §14.5 A9 "KVL·Vgs=Vds·KCL·**매칭 대칭** 단정". §12.3-3 "매칭쌍 M2a/M2b 중 M2b만 정상" | 노드전압 정본만으로는 매칭쌍의 W·gm 대칭이 보장되지 않는다(버전 혼재 사례). 물리 불변식 하나가 빠졌다. | V9를 "봉인 항목(N3.6), IC1, 그리고 `matching_offset`/`matching_ratio` 관계 엣지 멤버의 (W/L, gm_id) 일치(tol = 해당 LUT 격자 분해능)"로 고친다. |
| 19 | 1 | 혼동 | N6.1 Phase 2 "레지스트리 §2에서 '행동 보존 통합 가능'인 DUP 통합". Phase 4·6a 행에는 동작이 바뀌는 DUP 통합이 없다 | 옛 §13.6 Phase 4 "동작이 바뀌는 DUP 통합(★ diode·미러·diffpair 정본은 공동분석, metric 3쌍은 4회로 재측정)". ambiguities P2-03(★ 행 -> Phase 4, metric 3쌍 -> 7a). 레지스트리 39~41 ★ 3행 | ★ DUP 3개념과 metric 3쌍(gain/PM/CMRR)의 통합 Phase가 사라졌다. 옛 함수 삭제(WP-14) 시점도 없다. | N6.1 6a 범위에 "레지스트리 §2 ★ DUP(diode·미러 그룹·diffpair/tail)를 U-06 결론의 정본으로 통합하고 옛 함수 삭제"를 넣는다. 7a 범위에 "metric DUP 3쌍 통합"을 넣는다. |
| 20 | 1, 5 | 혼동 | N3.2-7 "declared stage에 없는 부하(파일럿 Vom1의 M19·M18a·M18b)". N7.1 J6은 파일럿만 다룬다 | probe 결과 648줄 "nmcnr_amplifier: gain 선언 누락 출력노드 접속 소자 2개 ['M104', 'M106']". 옛 §15.3은 "folded·nmcnr은 실제 누락 0"이라 적었는데 원자료와 맞지 않는다 | nmcnr의 출력노드 부하 귀속이 공동분석 목록에 없다. 6a DoD의 "ratified 대조표"에 이 항목이 빠진다. | N7.1 J6을 "M18a/M19/M18b(파일럿), M104/M106(nmcnr)을 해당 stage 부하(G_out)로 넣을지"로 넓힌다. |
| 21 | 1 | 경미 | N6.3 공통 완료 조건에 "test-author의 거부 케이스"가 없다 | 옛 §4.1 공통 "**test-author의 거부 케이스**", §15.8 "각 Phase DoD: ... test-author의 거부 케이스" | 공통 DoD 한 항목이 사라졌다(NFR-3은 IC만 다룬다). | N6.3 첫 bullet에 "동작 변경 spec card마다 거부해야 할 입력의 test가 있음"을 더한다. |
| 22 | 1 | 경미 | N6.2 7a에 "잔차 매 평가 기록"이 없고, 7b에 "유도 필드 status·증거"가 없다. 3에 "레지스트리 목적지 갱신"이 없다 | 옛 §4.1 7a "분해-전체 괴리 매 평가 기록", 7b "`sizing_spec.json` 유도 필드 `status`/증거", 3 "레지스트리 목적지 갱신" | FR-2·N3.15·WP-14에는 요구로 있으나 측정할 DoD에서 빠졌다. | N6.2 7a에 "평가 기록에 MNA-블록 잔차 필드 존재(4회로)", 7b에 "derived 필드마다 status·evidence·rule_hash", 3에 "레지스트리 이관 목적지 열 = 실제 위치"를 더한다. |
| 23 | 1 | 경미 | N5.3에 다중 diff pair 오프셋이 없다 | 옛 §3.4 A35 "다중 diff pair Case B/C 미해결(history:2976-2980)" | 열린 항목이 사라졌다. | N5.3에 "I-B22(신설) \| 입력환산 오프셋의 다중 diff pair Case B/C \| 7a(DEC-23)"을 더한다. |
| 24 | 1 | 경미 | DEC-06 "theta는 자유 탐색 변수만". 옛 선언 L theta 처리 방침이 없다 | 옛 A28 "기존 선언 L theta(`L_cascode`/`L_stage2out_*`) 존폐 결정은 미확인" | 결정되지 않은 항목이 사라졌다(7b 이관에서 부딪친다). | N7.2에 U-21 "선언 L theta(`L_cascode`, `L_stage2out_*`)를 L 동치류 theta로 대체하고 삭제할지"(기본안: DEC-18에 따라 삭제, 7b)를 더한다. |
| 25 | 1 | 경미 | N3.11 표에 TS6 승격 대상이 없다. N9.1 `20-dead-code-dup`은 "TS6 승격·삭제·이동 목록"을 요구한다 | 옛 §13.5 T6 승격 7개(`probe_gm_id_monotonicity`, `probe_physical_consistency`, `probe_parasitic_pm_all_circuits`, `probe_role_L_derivation`, `probe_lut_L_interpolation`, `probe_revalidation_scope`, `probe_prevention_wiring`), 복제 7건 | 이미 조사된 후보 목록이 사라져 design이 조사를 되풀이하게 된다. | N3.11 TS6 행에 "승격 후보: (옛 §13.5 T6의 7개 파일명)"을 옮긴다. |
| 26 | 1 | 경미 | N3.9 LR8 "같은 물리 행 안에서 L은 달라도 되지만 finger 폭은 같아야" | 옛 §7.7 branch/row 주의(§7.0 "원칙은 유효"): 한 `vertical_stack_id`에 PMOS/NMOS가 섞이고 L이 달라도 정상인 이유는 2축 분리(kind별 행 분리) | branch와 row를 구분하는 규칙이 빠졌다. | LR8 끝에 "branch(`vertical_stack_id`, 전기)와 row(물리 행)는 다르다. PMOS/NMOS는 kind별 행으로 먼저 나뉘므로 같은 branch 안에서 L이 달라도 된다"를 더한다. |
| 27 | 1 | 경미 | N3.9 LR5 "cascode·signal 역할의 knee 거부 가드는 유지" | 옛 §7.0 §7.10:518-523 판정 "`_L_ROLE_TARGETS` = mirror->knee, **bias_replica->창 하한**, cascode/signal->거부" | bias_replica의 초기 L 규칙이 빠졌다. | LR5에 "초기 L 목표: mirror = knee, bias_replica = `feasible_L_window` 하한, cascode·signal = knee 거부(`derive_role_L`)"를 적는다. |
| 28 | 1 | 경미 | N7.1 J8에 `bias_replica` 의도가 없다 | 옛 §15.7 J8 "`voltage_divider`/`floating_current_source`/**`bias_replica`** 의도 ... B24 vsb 오류 4소자 M38/M60/M61/M68 추적 단서" | 공동분석 항목 일부와 추적 단서가 빠졌다. | J8에 "`bias_replica` 의도(단서: vsb 오류 소자 M38/M60/M61/M68이 모두 `budget_reference_device` 보유)"를 더한다. |
| 29 | 1 | 경미 | N3.8·DEC-25에 L1 한정 규칙과 f_c 차이 원인이 없다 | 옛 §7.0 §7.11:656-660 "여전히 유효(L1 한정): 못 세는 고임피던스 노드는 `undetermined` 명시 실패", §7.11:575-582 "f_c 36.6MHz vs 실측 30.50MHz 차이 원인 미확인" | 여전히 유효하다고 판정된 규칙 하나와 열린 확인 하나가 빠졌다. | DEC-25 비고에 "L1 근사(`node_pole_estimate`)는 못 세는 고임피던스 노드를 `undetermined`로 실패. 정본은 L2 전체 응답"을 적는다. N5.3에 "f_c 해석 차이(36.6 vs 30.50MHz)"를 7a 확인 항목으로 둔다. |
| 30 | 1 | 경미 | DEC-08(value_amp), WP-04(논문 값) | 옛 A16 "파일럿 Iref 1.2µA는 사용자가 논문 원문에서 직접 확인한 값 -- A15 규약상 고정 대상이나 미배선" | 일반 원칙으로 합치면서 구체 사실(이 값은 고정 입력 대상)이 빠졌다. | DEC-08 비고에 "파일럿 Iref `value_amp=1.2µA`는 사용자 확인 값(고정 대상, 사이징 경로 미배선 I-B14)"을 적는다. |
| 31 | 1 | 경미 | DEC-12 | 옛 A20 "미정 vds는 역할별 min_vds 바닥" | 구현된 결정의 세부 규칙이 빠졌다. | DEC-12 결정문에 "미정 vds는 역할별 `min_vds` 바닥"을 더한다(6b에서 W 티어로 대체될 때까지). |
| 32 | 1 | 경미 | N3.5 SC-b | 옛 §12.5.2 C-b "재사용 모드에서 `setdefault` 건너뛰기 금지" | 계약 문장 하나가 빠졌다(DF-01의 원인 패턴). | SC-b 규칙에 "재사용 시 `setdefault`로 기존 값을 건너뛰지 않는다(V6 lint 대상)"를 더한다. |
| 33 | 1 | 경미 | N0.3 관련 문서 | 옛 §1.3 `analog-topology-json-library.plan.md`(topology.json connectivity 전용 의도), `gm-id-methodology.md` §13, `.ai/context.md` 세션44~48 | 참조 문서 3개가 빠졌다(WP-07·WP-15의 근거). | N0.3에 세 행을 더한다. |
| 34 | 1 | 경미 | N3.12.6 agent 정의 | 옛 §14.7 "각자 frontmatter `isolation: worktree`, auditor는 판정 기록 외 쓰기 없음" | worktree를 오케스트레이터가 직접 만드는 방식으로 바뀌었는지, frontmatter 규정을 뺀 것인지 알 수 없다. | agent 정의 행에 "frontmatter `isolation`은 쓰지 않는다(worktree는 N3.12.3에서 오케스트레이터가 생성)" 또는 그 반대를 명시한다. |
| 35 | 4 | 혼동 | N3.15 "슬루율은 `slew_rate_v_per_s` 하나로 통일한다(단위 SI, I-C7 해소)" | 옛 I-C7은 `slew_rate_v_per_us` vs `slew_rate_target` 명칭 불일치. ambiguities P7b-01은 "slew 명칭 확정"만 요구. 저장소 grep 결과 `slew_rate_v_per_s`는 plan에만 있다 | 두 후보 어느 쪽도 아닌 세 번째 이름을 근거 없이 정했다(단위 규약 결정 포함). | "명칭은 metric 단위 레지스트리(DEC-53) 규약을 따른다"로 바꾸고, 실제 이름은 `7b-compensation-allocation` design이 레지스트리 단위표를 인용해 정하게 한다. 아니면 U 항목으로 올린다. |
| 36 | 4 | 경미 | N3.14 exit code "2 / 3 / 4 / 5 / 1" | ambiguities X12는 "exit code 열"만 제안했다. 옛 문서에는 비0 규정만 있었다(DF-18) | 번호 배정의 근거가 없다(파이썬 기본 1만 근거 있음). | 열 제목을 "exit code(서로 다른 비0, 번호는 `00-common`에서 고정)"로 바꾸거나, 번호를 둔다면 "분류 순서대로 배정한 규약값"이라고 명시한다. |
| 37 | 4 | 경미 | N4.3 V3 "상수 **±1 단위**" | 옛 §14.5 A3 "상수 ±". ambiguities P05-08은 연산자 6종 고정 | "1 단위"(정수 1? 최하위 유효 자리?)가 정의돼 있지 않다. | "상수 변이 = 정수는 ±1, 실수는 ×(1±ε)(ε = 그 리터럴의 표기 자릿수 최하위 1)"처럼 정의하거나 "±"로 되돌린다. |
| 38 | 4 | 경미 | N3.6 "고정점 반복이면 처음 두 반복의 변화비 q로 `ceil(log(tol_V/\|Δ0\|)/log q)`, q ≥ 1이면 즉시 NONCONVERGENT" | ambiguities P6b-02 "수축률 추정 기반"(식 없음). bisection 식은 P6b-02에 있다 | 구체식과 "처음 두 반복", "q≥1 즉시 실패"는 새로 정한 것이다. 초기 과도에서 오판할 수 있다. | "q = 최근 두 연속 변화비의 최댓값, q ≥ 1이 두 번 연속이면 NONCONVERGENT"처럼 규칙의 근거(수축 사상 오차 한계)를 한 줄 적는다. |
| 39 | 4 | 경미 | N3.5 LRU 상한 "`n_starts` × `maxiter`" | ambiguities P6b-08 "탐색 1회 예상 평가 수(D4 계산값) × 계산 블록 수" | SLSQP의 한 반복은 FD 평가 차원+1회라 `maxiter`는 평가 수가 아니다. 과소 추정이다. | "`n_starts` × (평가 계수기로 실측한 SLSQP 1회 평가 수)"로 고친다(Phase 5 계수기 재사용). |
| 40 | 4 | 경미 | N7.2 U-03 기본안 "허용", U-09 기본안 "Phase 4에서 DF와 함께", U-16 기본안 "오케스트레이터가 사용자 확인 후 반영(`Role: doc`)" | ambiguities P3-05·X04·P05-01은 "사용자 결정 예"로만 적었고 기본안이 없다. U-16은 메모리("role 메타는 Claude")가 부분 근거 | 원칙에서 나온 근거를 적지 않고 기본안을 정했다(WP-16 요건). | 각 기본안 옆에 근거를 적는다. U-03: "WP-01 대상은 추적 파일", U-09: "N6.3 4회로 측정이 Phase 4부터 동작 변경 판정에 필요", U-16: "메모리 topology_json_single_source: role 메타는 Claude 분석 가능". |
| 41 | 4 | 경미 | N5.3 I-A6 "7b(`sizing_spec.json` human.constraints의 metric으로 추가)" | 옛 §10 A6 담당 "Phase 6a(D5 ports) -> 6b, **공식 미배정**" | 담당 Phase를 근거 없이 배정했다. 헤드룸 하한이면 6b(W 티어)와 관련된다. | "7b(슬롯은 `human.constraints`), 헤드룸 하한으로 쓰는지는 6b design이 W 티어 창과 함께 판정"으로 근거를 적는다. |
| 42 | 4 | 경미 | N5.2 DF-16 "수정 Phase 7a". N6.1 Phase 4 "DF-01~15·18~20·22" | 옛 §13.6 Phase 4 "결함 #1~21", D10 "순서 예외 없음". contradictions #7 해소안 "D6은 Phase 4가 최초 시점" | DF-16을 7a로 옮긴 근거가 적혀 있지 않다(감사 해소안과 반대 방향). | DF-16 비고에 "목적함수 정의(U-10)가 GB8 전력 정의와 같은 결정이라 7a로 옮긴다. 그 전 보고는 N5.4"를 적는다. |
| 43 | 3 | 경미 | N4.1 IC7 "4 이후 매 Phase". N6.1 Phase 4 행에는 IC7 활성 표기가 없다(1: IC3·IC5, 6b: IC1·2·9·10, 6c: IC4·6·8은 적혀 있다) | P7c-07 | IC 활성 표기가 한 곳 빠졌다. | N6.1 Phase 4 범위에 "IC7 활성"을 더한다. |
| 44 | 3 | 경미 | N4.1 IC2 "연속 필드 ≤ tol_V" | ambiguities P6b-05 "연속 필드 ≤ tol(D2)" | 전류·W·gm 같은 연속 필드에 볼트 허용오차를 적용해 단위가 맞지 않는다. | "노드전압 필드 ≤ tol_V, 전류 필드 ≤ tol_I, 그 밖의 연속 필드는 해당 입력 전압 섭동 tol_V의 감도 전파값"으로 고친다. |
| 45 | 3 | 경미 | DEC-32 "허용오차와 반복 상한은 **LUT 격자 간격**·보간 오차에서 계산한다(식: N3.6)". N3.6 tol_V 식은 LOO 보간 오차만 쓴다 | 옛 D2 "LUT VDS 격자 간격과 보간 오차" | 결정문과 식이 다르다. | DEC-32를 "LUT 보간 오차(LOO)에서 계산, 격자 간격은 FD 스텝·bisection 구간폭에 쓴다(식: N3.6, N3.7)"로 고친다. |
| 46 | 3, 7 | 경미 | N5.3 머리 "v5.0에서 I-G3, I-G7, I-C3, I-C5, I-C7, I-C9, I-A9는 본문 명세로 닫았다". A.2도 같은 목록. N9.3 "새 토폴로지 추가 절차(I-G8)" | 옛 §10 열린 32건에 G8 포함 | I-G8이 열림 목록에도 닫힘 목록에도 없다(24 + 7 = 31건). | N5.3 머리와 A.2 닫힘 목록에 "I-G8(N9.3)"을 더한다. |
| 47 | 7 | 경미 | N0.4 "I-A* ... (옛 §10 A/B/G/C 번호 유지)". N5.3 I-C10, I-C11 | 옛 §10 C 계열은 C3~C9뿐이다. I-C10 = §10.5a-8, I-C11 = A66 | 새로 만든 ID가 "번호 유지" 규칙과 어긋나고 A.2에 신설 표기도 없다. | A.2 이슈 행에 "신설: I-C10(옛 §10.5a-8), I-C11(옛 A66)"을 더한다. |
| 48 | 7 | 경미 | N0.4 "ID 접두어(번호는 옛 문서와 같다 -- 부록 A가 1:1 대응)" | A.2: A02->DEC-04, A70->LR4·LR5, B21->WP-20, D6->U-10 | DEC·WP 번호는 옛 번호와 다르고 1:1도 아니다. | "번호는 IC·SC·V·GB·RC·TS·W·MT·EL·DF·I-*만 옛 번호와 같다. DEC·WP·U는 새 번호이며 부록 A.2로 찾는다"로 고친다. |
| 49 | 7 | 경미 | N0.4 "SP1 \| stage 분할 규칙(DM 뷰 + **R2**)", N2.1 DEC-43 "SP1(DM 뷰 + R2)" | N0.4 자신이 R 기호를 LR·RC·등급으로 나눴다. probe의 R2 정의는 문서 안에 없다 | "R2"가 문서 안에서 정의되지 않았고 레지스트리 등급 R2와 겹친다. | "DM 뷰 + R2"를 "DM 뷰 + N3.2-4 엣지 비용 규칙"으로 바꾼다. |
| 50 | 7 | 경미 | N3.11 `unit/test_m1_gmid_lut.py ... test_m9_...` | N0.4 "MOD1~MOD10(트랜지스터 이름 M1a 등과 구분)" | 파일명 `m1`이 트랜지스터 M1과 모양이 같다. | `unit/test_mod1_gmid_lut.py` 형식으로 바꾼다. |
| 51 | 7 | 경미 | A.2 "A70->LR4·LR5" | 옛 A70 "L 탐색 = knee 창 + 경계 검사 -> **변경**: 실제 L은 l_class theta 연속 탐색 + warm start 격자(A28/A31)" | 현행 형태는 DEC-18·DEC-19인데 매핑이 LR4·LR5다. | "A70->DEC-18·DEC-19(knee 출발은 LR5)"로 고친다. |
| 52 | 7 | 경미 | A.1 "§10.1, §10.6~§10.14 \| 이력 같은 번호". 부록 B "`## 0. 이어받을 지점`", "`### 7.1` ~ `### 7.9`" | duplication_history_map §2.3: history에 같은 제목이 두 번 있다(§0: hist:16·3069, §10.6~14: hist:1932~ 본문과 3410~ stub, §7.1: hist:280·3968) | 앵커가 모호하다. | 부록 B 각 행에 "첫 번째 출현(v5.0 전문 블록 이전)"을 명시하거나 고유 제목 문자열을 적는다. |
| 53 | 3 | 경미 | N2.1 머리 "상태: 구현됨 / 부분 / 미구현 / 착수 조건". 표 안에는 "원칙"(DEC-44·49·51), "--"(DEC-33·47)도 있다 | 옛 §3.4 상태 표기 7종 | 범례와 표 값이 다르다. | 범례에 "원칙(구현 대상 아닌 규칙)"을 더하고 "--"를 "원칙"으로 바꾼다. |
| 54 | 7 | 경미 | N3.5 "S2 LRU 상한 = (**N3.5 D4 식**의 샘플 수 ...)". 같은 절의 식 이름은 "전역 샘플 수(DEC-34)" | -- | 같은 절 안에서 별칭(D4)과 ID(DEC-34)를 섞어 쓴다. | "DEC-34 식"으로 통일한다(N3.7, N9.1 7c도). |
| 55 | 6 | 경미 | N4.2 한 줄("SC 강제 test는 N3.5 표가 정본"), N4.4 한 줄("N3.12.3이 정본이다") | duplication_history_map #6 | 내용 없는 포인터 절이다. | N4.2·N4.4를 지우고 N0.2 auditor 읽는 순서에 "N3.5 강제 test 열, N3.12.3"을 더한다. |
| 56 | 6 | 경미 | N5.3 I-A3(=DF-16·U-10), I-A4(=DF-05), I-B7(=DF-02), I-B9(=DF-01) | duplication_history_map #5 | DF와 I가 같은 결함을 두 번 적는다. | 이 네 I 행을 N5.3에서 지우고 해당 DF 비고 열에 옛 ID만 남긴다(A.2 대응은 유지). |
| 57 | 6 | 경미 | N2.1 DEC-33 "착수 순서는 N6.1 표 하나를 따른다" | -- | 문서 구조를 서술한 메타 문장이지 설계 결정이 아니다. | DEC-33을 지우고 A.2 "D3->N6.1"로 둔다. |
| 58 | 6 | 경미 | N0.1 "수치는 auditor 판정 기록(N3.12.5)에서만 인용한다". 본문에는 15,270줄, 6480조합, 앵커 12개, 5분 등 수치가 있다 | 옛 §4.1 "판정 수치는 auditor 판정 기록에서만 인용" | 규칙의 적용 대상(보고서)이 계획서 자체로 읽힌다. | "탐색·test 결과 수치를 **보고할 때**는 판정 기록에서만 인용한다(설계 입력인 사실 수치는 예외)"로 고친다. |
| 59 | 1 | 경미 | N3.13-6 "`achievable_metric_bound(mode="bisect")`" | 옛 §10.15 "`tests/derive_achievable_bounds.py`는 선언에서 대상을 찾아 돌리는 구조라 그대로 쓴다"(파일 존재 확인) | 재사용할 운영 도구가 빠져 새로 만들 위험이 있다(WP-14). | N3.13-6에 "호출 도구: `tests/tools/derive_achievable_bounds.py`(현 `tests/` 위치에서 TS6로 이동)"를 더한다. |

## 2. 과제 5 -- N9 design 문서별 착수 가능성

| design 문서 | 판정 | 막히는 곳(표 1의 #) |
|---|---|---|
| `00-common` | 착수 가능 | exit code 번호 근거(#36), 상태 범례(#53) |
| `05-role-separation` | **막힘** | dispute 쓰기 권한(#3), structure.json·search_archive 쓰기 주체와 EL2(#6), V 도입과 0.5 DoD(#7), mutation 위치(#11), EL3 대 `tests/tools`(#12), audit worktree·병합본 생성과 경로 상대화(#13), "사용자만" 경로 편집 방법(#14). 착수 조건 U-15·U-16 |
| `10-test-separation` | 혼동 | IC3·IC5 활성에 필요한 코드 변경과 판정 유형(#8), test 전용 변경의 흐름·증거(#9), TS1 추출 스크립트 실행 주체(#10). U-01 |
| `20-dead-code-dup` | 착수 가능 | ★ DUP·metric 3쌍의 Phase가 빠짐(#19), TS6 승격 후보 유실(#25). U-02 |
| `30-module-split` | 착수 가능 | 없음(U-03) |
| `40-defect-fixes` | 착수 가능 | DF-16 이동 근거(#42), IC7 활성(#43). U-04·U-05·U-09 |
| `50-failure-cache` | **막힘** | S0가 없는 Phase 5의 캐시·S3 키(#4) |
| `6a-structure-stage` | **막힘** | SP1 엣지 규칙과 실측 근거 불일치(#1), J1~J9 착수 조건 순환(#2), structure.json 권한(#6), nmcnr 부하 J 누락(#20) |
| `6b-node-voltage-seal` | **막힘** | LRU 상한이 7c의 N에 의존(#5), I-C10 결정을 design에 떠넘김(#16), J8이 6b 착수 조건에 없음(#2), IC2 단위(#44), 반복 상한 식(#38) |
| `6c-coupling-achievability` | 혼동 | DOF 표본 수가 D4에 의존(#5), 달성 불가 픽스처의 oracle 종류 미지정(부록 2 P6c-07) |
| `7a-gain-metric` | 혼동 | U-11 기본안을 범위에 선반영(#15), folded `omega_c` 측정 불가 누락(#17), 다중 diff pair(#23), f_c 확인(#29). U-07·U-10·U-11·U-19 |
| `7b-compensation-allocation` | 혼동 | slew 명칭 근거 없음(#35), 선언 L theta 존폐(#24). U-13 기본안(Pareto 정지)과 7b DoD "`gain_budget_db` 출력·파일럿 5분"이 파일럿에서 동시에 성립하는 조건이 없음(ambiguities P7b-07이 남긴 것, U-13 결과에 따라 DoD 분기 필요) |
| `7c-archive-spice` | 착수 가능 | N의 T_fixed 구성(#5와 같은 식) |

---

## 부록 1. contradictions.md 47건 판정

판정: 해소(위치) / 부분 / 미해소 / U로 이관.

| 감사 # | 판정 | 비고 |
|---|---|---|
| 1 (막음) | 해소(N3.12.2 경로표: auditor `.ai/verification/**`, 게이트는 spec card+승인 기록) | 새 모순: dispute 경로(표 1 #3) |
| 2 (막음) | 해소(WP-14 "같은 변경 단위", WP-19, N3.12.3 test 커밋 선행, EL3) | -- |
| 3 (막음) | 해소(N3.12.3 판정 유형 red-green/equivalence, V2, EL4 "판정 유형별 증거") | test 전용 변경은 미정의(표 1 #9) |
| 4 (막음) | 해소(N4.5 재생 Phase 열, N4.3 도입 열, N6.2 0.5 "사례 5건") | V4~V6 도입 1과 0.5 사용(표 1 #7) |
| 5 (막음) | 부분(N3.11 TS1 추출 스크립트) | 실행 주체가 없다(표 1 #10) |
| 6 (막음) | 해소(N3.1 실행 구조 "GB6과 GB7이 한 평가 안에서 같은 순환 블록으로 수렴") | DP 격자 결정과 SCC 고정점의 경계는 7b design 몫 |
| 7 (막음) | 해소(D6->U-10 7a, D8->U-06 6a, N6.1) | 감사 해소안(D6=Phase 4)과 방향이 다르고 근거 서술이 없다(표 1 #42) |
| 9 (막음) | 해소(N3.2-7: input·cascode·tail은 declared 100%, 출력노드·load·G_out은 ratified 대조) | 규칙 정의 오류는 따로 있다(표 1 #1) |
| 11 (막음) | 해소(N3.11 TS0~TS7 Phase 열, N6.1) | -- |
| 8 | 해소(N3.8 전력 = U-10, GB8) | -- |
| 10 | **미해소**(N6.1 6a 추가 착수 조건 U-06(J1~J9)) | 표 1 #2 |
| 12 | 해소(N3.11 TS1 두 커밋, N3.12.3) | -- |
| 13 | 해소(N3.10 끝 "배선을 고른 함수는 Phase 4", N6.1 Phase 2·4) | -- |
| 14 | 해소(N3.10 MOD 표에서 동작 변경 괄호 제거, DF-18 Phase 4) | -- |
| 15 | 해소(N0.4 status 5값, N3.3 전이표) | -- |
| 16 | 해소(N3.4 "`set_device_vds`는 W 티어 setter의 파생") | -- |
| 17 | U로 이관(U-04, SC-d 문구에 기본안 반영) | -- |
| 18 | 해소(N7.2 U-01~U-19 한 표) | -- |
| 19 | 해소(DEC-35 적용 6a, U-08) | -- |
| 20 | 해소(N6.1 공통 착수 조건 "design 문서 사용자 승인") | -- |
| 21 | 해소(N6.1 유일 순서 정본, DEC-33) | -- |
| 22 | 해소(N6.3 "5분 게이트는 7b·7c", 그 전 Phase는 보고) | -- |
| 23 | 해소(N1.1 결정 순서, Summary) | -- |
| 25 | 해소("지금 돌리면" 열 삭제, N4.1) | -- |
| 26 | 해소(N1.2 범위 밖, N5.3 머리 닫힘 목록) | I-G8 누락(표 1 #46) |
| 28 | 해소(N0.1 인용 규칙, DF 위치 열 = 함수명) | -- |
| 29 | 해소(N0.4 TS/W/MT) | -- |
| 30 | 해소(LR/RC/"등급 R") | SP1 정의의 "R2" 잔존(표 1 #49) |
| 31 | 해소(GB0~GB9, I-G*) | -- |
| 32 | 해소(N0.4 접두어 표) | -- |
| 34 | 해소(N3.1 GB0 구현 Phase "6a(의미·게이트), 7b(파일)") | -- |
| 37 | U로 이관(U-16, N3.12.2에 기본안 반영) | 기본안 근거 서술 없음(표 1 #40) |
| 40 | U로 이관(U-12, N3.7 보상 규칙) | -- |
| 42 | 해소(N3.4 셋째 bullet "표현 불가 / 봉인이 거부" 구분, N3.6 항목 4·5) | -- |
| 24 | 해소(§7.x 본문 이력 이동, 판정은 LR·DEC에 반영) | 일부 "여전히 유효" 항목 유실(표 1 #17, #26, #27, #29) |
| 27 | 해소(DEC-47, A74->DEC-47) | -- |
| 33 | 해소(원설계 Phase 서술 삭제, DEC-31 적용 6b) | -- |
| 35 | 부분(N6.1 Phase 5 "S3 레코드 v1", 7c "S3 전체") | Phase 5 키 문제(표 1 #4) |
| 36 | 해소(N3.11 트리에 oracles·legacy) | -- |
| 38 | 해소(N3.11 conftest `--shuffle-seed` 자체 구현) | -- |
| 39 | U로 이관(U-14, DEC-10) | -- |
| 41 | 해소(N3.15 human `gain_budget_db_override`(source 필수), DEC-03) | -- |
| 43 | 해소(SC-e 신설) | -- |
| 44 | 해소(N1.2 레이아웃 "MOD7로 옮기기만", N3.10 MOD7 행, LR9 "현 엔진에는 루프 없음, 7b MOD8") | -- |
| 45 | 해소(불일치 수치 삭제, 집계는 원자료) | -- |
| 46 | 해소(DEC-13 "부분(DF-01)") | -- |
| 47 | 해소(DEC-50 착수 조건 U-19) | -- |

**집계**: 해소 40 / 부분 2(#5, #35) / 미해소 1(#10) / U로 이관 4(#17, #37, #39, #40). 막음 9건: 해소 8, 부분 1(#5).

---

## 부록 2. ambiguities.md 118건 판정

ambiguities.md에는 "top 15" 목록이 없다. 그래서 "사용자 결정? 예" 항목을 포함한 118건 전부를 개별 행으로 판정했다.

| 감사 # | 판정 | 비고 |
|---|---|---|
| X01 | 해소(N0.1 인용 규칙) | -- |
| X02 | 해소(N0.4 spec card 정의, N9.1 경로) | -- |
| X03 | 해소(N0.4) | -- |
| X04 | 해소(N0.4 무동작 증명, N6.1 Phase 4 I-C11, U-09, N6.3) | U-09 기본안 근거 없음(표 1 #40) |
| X05 | 해소(N6.3 성능 조건) | 명령은 `00-common`에서 |
| X06 | 해소(N4.3 도입 열, N/A 규칙) | -- |
| X07 | **미해소** | 표 1 #4(막음) |
| X08 | 해소(N6.1 6b "계산 블록과 S2 memo") | -- |
| X09 | 해소(N6.1 7a, N3.13) | -- |
| X10 | 해소(N0.4 결합/계산/순환 블록) | -- |
| X11 | 해소(N0.4 signal/declared stage) | -- |
| X12 | 해소(N3.14) | exit code 번호 근거 없음(표 1 #36) |
| X13 | 해소(N3.12.5 판정 기록) | -- |
| X14 | 해소(N3.12.5 승인 기록) | -- |
| P05-01 | 해소(N3.12.2) + U-16 | dispute·structure.json 누락(표 1 #3, #6) |
| P05-02 | 해소(N3.12.2 hook 판정 범위) | -- |
| P05-03 | U로 이관(U-15) + N3.12.6 ② 실측 | -- |
| P05-04 | 해소(N3.12.6 ④, 산출물 `hooks/role_*.py`) | -- |
| P05-05 | 해소(EL3 "python이 없으면 둘 다 차단") | `project-hooks/` 범위 밖 명시 없음(경미) |
| P05-06 | 해소(EL3 트레일러 조건, `doc` 값) | -- |
| P05-07 | 부분(N9.1 05 "경로 분류 규칙"에 위임) | EL3와 `tests/tools` 충돌(표 1 #12) |
| P05-08 | 해소(V3) | 변이 위치(표 1 #11), "±1 단위"(표 1 #37) |
| P05-09 | 해소(V4 (2)) | -- |
| P05-10 | 해소(N0.4 기준 약화 8패턴, V5) | -- |
| P05-11 | 해소(V6 허용 집합, `# derive:` 태그) | -- |
| P05-12 | 해소(V7, `reachability.py`) | -- |
| P05-13 | 해소(N3.12.3 ①, N3.12.5 interface card) | -- |
| P05-14 | 해소(N3.12.3 spec card 필드, 경로) | -- |
| P05-15 | 해소(N3.12.6 부트스트랩 ①~⑤) | -- |
| P05-16 | 해소(N4.5 과거 사례 재생 표) | -- |
| P05-17 | 부분(N3.12.3 worktree 명령) | 병합본 생성 주체·경로 상대화(표 1 #13) |
| P05-18 | 해소(EL2 무시 목록) | 런타임 산출물 누락(표 1 #6) |
| P05-19 | 해소(N4.5 공격 11) | -- |
| P05-20 | 해소(N3.12.5 보고 수치) | -- |
| P1-01 | 해소(N3.11 TS Phase 열) | -- |
| P1-02 | U로 이관(U-01, N6.1 Phase 1) | -- |
| P1-03 | 해소(N3.11 TS1 완료 판정, legacy) | -- |
| P1-04 | 해소(conftest `--shuffle-seed`) | -- |
| P1-05 | 해소(N3.11 conftest, WP-07) | -- |
| P1-06 | 해소(TS1 커밋 순서) | 실행 주체(표 1 #10) |
| P1-07 | 해소(TS3 AST 검사) | -- |
| P1-08 | 해소(N3.11 `slow` 표식) | -- |
| P2-01 | U로 이관(U-02), 열은 N9.1 20 | -- |
| P2-02 | 해소(N6.2 Phase 2 차등 test) | -- |
| P2-03 | 부분(N6.1 Phase 2 "행동 보존 통합 가능") | ★ 행·metric 3쌍 Phase 없음(표 1 #19) |
| P3-01 | 해소(N3.10 규칙: 레지스트리 목적지 열에서 Phase 3 design이 생성) | -- |
| P3-02 | 해소(N6.2 3, `import_layering.py`, N3.10 규칙) | -- |
| P3-03 | 해소(N3.10 이동 규칙 AST 해시) | -- |
| P3-04 | 해소(N3.10 shim) | -- |
| P3-05 | U로 이관(U-03) | -- |
| P3-06 | 해소(N3.10 "`canonical_spec()`/`SPECS`는 run_harness에 남고 MOD10에 인자") | -- |
| P4-01 | 해소(N3.14, DF-03) | -- |
| P4-02 | 해소(DF-01·DF-02 Phase 열 "4(거부·재계산), 6b(구조)", tol_V 선도입) | -- |
| P4-03 | U로 이관(U-04) | -- |
| P4-04 | 해소(N5.2 머리 "test 또는 lint(V6)", N9.1 40) | -- |
| P4-05 | 해소(D8->U-06 6a, Phase 4 착수 조건에서 제외) | -- |
| P4-06 | 해소(V8 `fallback_events` 스키마) | 계측 지점 전수는 N9.1 40 |
| P4-07 | U로 이관(U-07, 7a) | -- |
| P4-08 | U로 이관(U-05) | -- |
| P4-09 | 해소(N3.14 exit code) | -- |
| P5-01 | 부분(N3.5 실패 캐시 키·margin) | 키의 S0가 Phase 5에 없음(표 1 #4) |
| P5-02 | 해소(N3.5 시작점) | -- |
| P5-03 | 해소(N3.3 S3 경로) | 기존 `tests/canonical_theta_star.json` 처리 없음(경미) |
| P5-04 | 해소(N6.2 5 평가 입구 계수기) | -- |
| P6a-01 | 해소(N3.3 S1) | -- |
| P6a-02 | 해소(N3.3 S0) | -- |
| P6a-03 | **미해소(오기)** | N3.2-4가 측정 규칙 R3(DM/R2)과 다르다(표 1 #1, 막음) |
| P6a-04 | 해소(N3.2-7, N6.2 6a, J5·J6) | nmcnr M104/M106(표 1 #20) |
| P6a-05 | 해소(N3.2-1 교류접지 3분류) | -- |
| P6a-06 | 해소(N0.4·N3.3 status, `structure.json`) | 쓰기 권한(표 1 #6) |
| P6a-07 | 해소(N3.3 끝 "6a shadow, 6c부터 정지") | -- |
| P6a-08 | 해소(DEC-35, U-08 6a) | -- |
| P6a-09 | **미해소** | N7.1 소비 Phase 열은 생겼으나 N6.1 착수 조건이 J1~J9 전부(표 1 #2) |
| P6a-10 | 해소(N3.2-2) | -- |
| P6a-11 | 해소(N3.2-6, J7) | -- |
| P6a-12 | U로 이관(U-06 구조 개념 정본) | -- |
| P6b-01 | 해소(N3.6 봉인 항목 1~5) | -- |
| P6b-02 | 해소(N3.6 허용오차 식) | 고정점 반복 상한 식은 새로 정한 것(표 1 #38) |
| P6b-03 | 해소(N3.4 W3 출처, 권한표는 N9.1 6b) | -- |
| P6b-04 | 해소(SC-c "계산 블록 입출력 선언으로 만든 유도 DAG") | -- |
| P6b-05 | 해소(IC2, I-B12 6b로 이동) | 단위(표 1 #44) |
| P6b-06 | 해소(N3.14 SEAL_VIOLATION) | -- |
| P6b-07 | 해소(N8 노드전압 정본 전환 행) | -- |
| P6b-08 | **미해소** | 식은 있으나 입력 N이 7c에만 존재(표 1 #5, 막음) |
| P6b-09 | 해소(SC-b 쓰기 카운터) | -- |
| P6c-01 | 해소(N0.4 결합 블록, GB3) | -- |
| P6c-02 | 해소(N3.7 블록 gain 상한) | -- |
| P6c-03 | 부분(N3.7 수치 rank) | 표본 수가 D4에 의존(표 1 #5) |
| P6c-04 | 해소(N3.7 DOF 변수·등식, `DofReport`) | -- |
| P6c-05 | 해소(N3.7 LUT 곡선 검사) | -- |
| P6c-06 | 해소(N3.7 달성가능성 "상한 미상") | -- |
| P6c-07 | 부분(N9.1 6c "달성 불가 픽스처와 oracle") | oracle 종류가 지정되지 않음. 수정안: "oracle (a) 손계산 -- test가 LUT 격자 전수를 다른 구현으로 계산한 Σ 상한 < 목표" |
| P6c-08 | 해소(N3.7 "결합 잔차 측정(6c 첫 작업)") | -- |
| P7a-01 | 해소(N3.8 블록 gain·잔차, 곱 분해 금지) | -- |
| P7a-02 | 해소(N3.8 감도 게이트 ε·방향·시점) | -- |
| P7a-03 | 해소(N3.8 회로별 이관) | folded `omega_c`(표 1 #17) |
| P7a-04 | 해소(N6.1 7a 착수 조건 재정리) | J6 소비 7a인데 착수 조건에 없음(경미) |
| P7a-05 | 해소(N3.8 metric 티어) | -- |
| P7a-06 | U로 이관(U-11) | 7a 범위에 기본안 선반영(표 1 #15) |
| P7a-07 | 해소(N6.2 7a 픽스처) | -- |
| P7b-01 | 해소(N3.15) | slew 명칭(표 1 #35) |
| P7b-02 | 해소(N3.7 중층 종료·상한) | -- |
| P7b-03 | 해소(N3.7 내층 DP) | -- |
| P7b-04 | 해소(N3.7 검증) | -- |
| P7b-05 | U로 이관(U-12) | -- |
| P7b-06 | 해소(N3.7 보상 규칙, `ID_source` 3종) | J3는 U-06 |
| P7b-07 | U로 이관(U-13) | 7b DoD와 Pareto 정지의 양립(표 2 7b) |
| P7b-08 | 해소(N3.15 override) | -- |
| P7b-09 | U로 이관(U-14) | -- |
| P7b-10 | 해소(GB0 로드 게이트, DEC-08) | -- |
| P7c-01 | 해소(N3.8 SPICE 비교량·허용오차) | -- |
| P7c-02 | 해소(N3.8 SPICE 인터페이스) | -- |
| P7c-03 | 해소(N3.3 S3 형식) | 크기 상한은 N8 "보고"로 대체(경미) |
| P7c-04 | 해소(N3.5 D4 식, Sobol) | -- |
| P7c-05 | 해소(N3.5 분지) | -- |
| P7c-06 | 해소(N6.2 7c) | -- |
| P7c-07 | 해소(N4.1 담당 Phase, TS7 만료) | -- |
| P7c-08 | 해소(N3.8 `verified_by`) | -- |

**집계**: 해소 96 / 부분 6(P05-07, P05-17, P2-03, P5-01, P6c-03, P6c-07) / 미해소 4(X07, P6a-03, P6a-09, P6b-08) / U로 이관 12(P05-03, P1-02, P2-01, P3-05, P4-03, P4-07, P4-08, P6a-12, P7a-06, P7b-05, P7b-07, P7b-09).

---

## 부록 3. 신규 내용의 근거 확인(과제 4, 근거 있는 것)

| 새 내용 | 판정 |
|---|---|
| N3.6 봉인 항목 1~5 | 근거 있음(P6b-01 항목 1~4, 항목 5는 옛 §15.4 "충돌은 봉인 게이트가 거부"·contradictions #42) |
| tol_V(LOO)·tol_I·bisection 반복 상한 | 근거 있음(P6b-02, `tests/probe_interp_scheme_loo.py` 존재) |
| V6 허용 리터럴 {0, 1, −1, 산술식의 2, 인덱스} | 근거 있음(P05-11) |
| V4 AST 동형 정규화 | 근거 있음(P05-09) |
| DEC-34 N 식, Sobol | 근거 있음(P7c-04) |
| `.ai/approvals/`, 판정 기록 필드, `<id>`=YYYYMMDD-slug | 근거 있음(X13, X14) |
| `library/<name>.structure.json`, `search_archive/<S0>/{evals,runs}.jsonl` | 근거 있음(P6a-06, P5-03, P7c-03) |
| `hooks/role_*.py` + `install.py --only hooks --project .` | 근거 있음(P05-04, install.py:12) |
| `tools/gates/{reachability, interface_card, import_layering}.py` | 근거 있음(P05-12, P05-13, P3-02) |
| `sizing_spec.json` `schema_version`(5), `origin` | 근거 있음(P7b-01 "스키마 v5", P4-03/U-04) |
| W3 `Voc_des` 계열 | 근거 부분(P6b-03 후보. 파일럿 topology에 `Voc_des`/`vocdes` 16회 존재) |
| `gm_1 = 2π·GBW·CL` 기본안 | 근거 있음(P7b-05, U-12로 보류) |
| U-04·U-05·U-07·U-11·U-12·U-13·U-14·U-15 기본안 | 근거 있음(각 P4-03, P4-08, P4-07, P7a-06①, P7b-05, DEC-07, P7b-09, P05-03) |
| U-03·U-09·U-16 기본안 | 근거 서술 없음(표 1 #40) |
| `slew_rate_v_per_s`, exit code 번호, V3 "±1 단위", 고정점 반복 상한 식, LRU `n_starts×maxiter`, I-A6 7b, DF-16 7a, SP1 gs 제외 | 근거 없음(표 1 #1, #35~#39, #41, #42) |
| worktree 경로 `../wt/<id>-*`, `tools/migrate/extract_selftest.py` | 감사에 없는 새 경로다. 설계 선택이라 경미하지만 경로표와 상호작용한다(표 1 #13) |
