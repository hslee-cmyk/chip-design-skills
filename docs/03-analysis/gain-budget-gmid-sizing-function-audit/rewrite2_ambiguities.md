# gain-budget-gmid-sizing 계획서 v4.49 -- design 작성자 시점 모호성 감사

> 대상: `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(1,562줄, 2026-09-14 작업트리). `plan:N`은 **현재 파일 줄 번호**다.
> 대조: 이력 `history:`(=gain-budget-gmid-sizing.history.md), 레지스트리 `reg:`, 감사 원자료 `audit/<파일>:줄`(=docs/03-analysis/gain-budget-gmid-sizing-function-audit/), 코드 `SR:`(sizing_recipe.py), 저장소 실측(ls/grep).
> 범주: 1 입출력·인터페이스 / 2 판정기준·수치 도출 / 3 책임·권한 / 4 DoD 측정 가능성 / 5 의존·선행 / 6 예외·실패 경로 / 7 용어.
> "사용자 결정?" 열: **예** = 사용자만 답할 수 있음(spec·회로 해석·승인 사안). **아니오** = 기존 원칙·기록으로 답이 나옴(그 답을 적음).

## 집계

| Phase | 모호점 수 |
|---|---|
| 공통(전 Phase) | 14 |
| 0.5 역할 분리 인프라 | 20 |
| 1 test 분리 | 8 |
| 2 사장코드·DUP | 3 |
| 3 10모듈 분리 | 6 |
| 4 결함 #1~21 | 9 |
| 5 실패 캐시·θ* | 4 |
| 6a S0/S1/S1v | 12 |
| 6b 노드전압 정본·봉인 | 9 |
| 6c 결합 블록·달성가능성·DOF | 8 |
| 7a gain metric·감도 게이트 | 7 |
| 7b 보상·3층 할당·sizing_spec | 10 |
| 7c S3·SPICE | 8 |
| **합계** | **118** |

---

## 1. 모호성 표

### 공통(전 Phase)

| # | Phase | 범주 | 모호한 곳(plan:줄 인용) | design 작성자가 막히는 이유 | 답이 이미 있나(위치) | 해소안: 계획서에 명시할 것 | 사용자 결정? |
|---|---|---|---|---|---|---|---|
| X01 | 공통 | 5,7 | §3.4 표 A/B의 `plan:` 인용이 전부 **v4.48 줄 번호**(plan:243 "줄 번호는 v4.48 작업트리 기준"). 예: A01 "writer 티어 plan:1417" -> 현재 plan:1498, A40 "D1 plan:1012" -> 현재 plan:1098, A54 "D5 plan:1021" -> 현재 plan:1102 | 결정의 원문 위치를 따라가면 엉뚱한 줄에 도착한다. 결정 정본 표가 추적 불가 | 없음 | §3.4의 `plan:N`을 전부 `§절번호`(예 `§15.4 §7.3행`)로 치환하고, 줄 번호는 이력·코드 인용에만 쓴다는 규칙 한 줄 추가 | 아니오 |
| X02 | 공통 | 1 | "Phase별 design 문서를 거친다"(plan:17), "design 문서를 거쳐 착수"(plan:1248) -- 파일명·단위·절 구성 없음. 한편 spec card는 `docs/02-design/specs/<id>.md`(plan:1334) | design 문서가 Phase당 1개인지, spec card(변경 1건)와 무엇이 다른지, 어디에 두는지 모른다 | 부분: 저장소 관례 `docs/02-design/features/<name>.design.md`(ls 실측) | 부록 "design 문서 목록" 표(이 문서 §3 초안) + "design 문서 = Phase 설계(인터페이스·판정식), spec card = 그 설계를 구현하는 변경 1건의 계약" 정의 한 줄 | 아니오 |
| X03 | 공통 | 7 | 기호 `T`가 다섯 가지로 쓰인다: writer 티어 T0~T4(plan:1498), test 분리 단계 T0~T7(plan:1236-1243), metric 티어 T1/T2/T3(plan:1500, plan:816), 은폐 유형 T1~T11(plan:1292-1304), 이력 원인 유형 T1~T7(plan:983, 1003, 1055) | "T3 전역 게이트"(plan:1514)가 metric 티어인지 writer 티어인지 문맥으로만 구분 -- design 문서 간 교차 참조가 깨진다 | 없음 | 접두 분리: writer 티어 `W0~W4`, test 단계 `TS0~TS7`, metric 티어 `MT1~MT3`, 은폐 유형 `CT1~CT11`, 이력 원인 `HT1~HT7`. 용어집에 등록 | 아니오 |
| X04 | 공통 | 4,5 | 모든 Phase DoD "4개 회로 측정(필요 없는 회로에서 무동작 증명)"(plan:378, plan:1558) -- 그런데 `two_stage_ota`는 "stage1_out KVL이 풀리기 전에는 어떤 유도도 못 돌린다"(plan:945-946), A66 "별도 세션 이월"(plan:321). §0.2 착수 조건(plan:57-71)에 없음 | 4회로 DoD가 Phase 1부터 원리적으로 달성 불가. "무동작"의 판정(출력 바이트 동일? 코드 경로 미발동 계수?)도 없다 | 부분: history:3004(§12.7-0 "선행: ports·two_stage stage1_out·nmcnr stage2_diode_ref 이월 해소 -- 없으면 4회로 측정 자체 불가")가 있었으나 v4.48 재작성에서 빠짐 | (1) §0.2에 "4회로 실행 가능성(two_stage stage1_out 분리, nmcnr stage2_diode_ref)" 행을 추가하고 담당 Phase 지정 (2) "무동작 = 해당 기능의 발동 계수 0 **그리고** 그 회로의 결과 산출물이 Phase 전후 동일" 정의 | **예** -- A66은 사용자가 "별도 세션"으로 멈춘 항목. 몇 번째 Phase 앞에 둘지 사용자 확인 |
| X05 | 공통 | 4 | "평가 오버헤드 실측"(plan:378, 399), "wall-clock ≤ 5분(B4)"(plan:392은 7b만, plan:1558은 **각 Phase**) | 측정 조건이 없다: 어떤 spec(정본?)·`slsqp_kwargs`(run_harness.py:326 n_starts=3/maxiter=25)·cold/warm·반복 횟수·기계. B4 원 측정(history:563-609)은 폐기된 "knee 창 전수" 정책 기준 | 부분: history:608 "파일럿 1회 전체 실행 ≤5분(기본 정책 기준)" | 벤치 명령 1개를 고정(`python -m ... --spec canonical --circuit <4회로>`), 측정 = warm 평가 k회 중앙값 + 전체 실행 1회 wall-clock, 기계 정보 기록. 5분 **게이트**는 7b 이후만, 그 전 Phase는 보고만 -- plan:392/1558 불일치 정리 | 아니오(B4 기존 결정) |
| X06 | 공통 | 3,4 | 공통 DoD "auditor 판정 PASS(§14.5 A1~A10)"(plan:378) -- 그러나 A8 `fallback_events`는 Phase 4에서 구현(plan:1386), A9 계약 test는 T7로 6a~7c에 나눠 생김(plan:1243) | Phase 0.5~3에서 A8/A9는 실행 대상이 없어 PASS가 불가능하거나 "볼 수 없어 통과"(C5)가 된다 | 없음 | Phase × A1~A10 활성표. 미존재 검사는 PASS가 아니라 `N/A(사유, 도입 Phase)`로 판정 기록에 적는다 | 아니오(C5 원칙) |
| X07 | 공통 | 5 | Phase 5 "θ* 기록·시드, 아카이브 시드"(plan:1257) vs Phase 7c "S3 아카이브"(plan:1556). S3 키는 "S0 전체 지문"(plan:1046)인데 S0는 6a에서 생김 | Phase 5가 쓰는 기록의 스키마·키가 무엇인지, 7c에서 다시 만드는지 모른다 | 없음 | Phase 5 = S3 레코드 스키마 v1 확정(키는 당장 계산 가능한 지문: topology 내용 해시 + spec 전체 해시 + 엔진 소스 해시), 6a에서 S0로 키 교체(불일치=없음, C-d), 7c = 전역 샘플·분지만 추가 | 아니오 |
| X08 | 공통 | 5 | §12.5.3 평가 커널(블록 입출력 선언, S2 LRU 적재, 조인트 스캔 키)(plan:1062-1064)이 §15.8 어느 Phase에도 배정되지 않음. §13.6 Phase 6 행(plan:1258)은 "대체됨"이라 적었지만 본문 순서(S2 -> DAG -> S1v)가 15.8(S1v가 6a)과 다름 | 성능 이득이 가장 큰 작업(plan:1064 "warm 평가의 66%")의 담당 Phase가 없다 | 없음 | 15.8 표 6b에 "유도 DAG + S2 블록 memo(§12.5.3)" 명시, §13.6 Phase 6·7 행은 "15.8 참조"만 남기고 본문 삭제 | 아니오 |
| X09 | 공통 | 5 | 임계값 bisection(§10.15, plan:890-946, A34 "구현은 design 단계 후", plan:289 "§15에 Phase 배치 없음") | G0 "제약값 출처 필수"(plan:1508)를 적용하면 `mismatch_sigma_mV=5.0`(A33)·`gain_db=54`(A64)의 출처가 필요한데 그걸 만드는 도구가 어느 Phase에도 없다 | 없음 | bisect 모드를 7a 착수 조건(또는 G0 구현 Phase=6a)에 배정. 결합 제약(`value_from_constraint`, plan:933-937) 확인을 DoD에 | 아니오(선택지 3은 사용자 확정, 배치만 필요) |
| X10 | 공통 | 7 | "블록"이 넷: 결합 블록(G3, plan:1511), 평가 커널 계산 블록(plan:1062), 순환 블록/SCC 블록(plan:1057, 1515), 블록 DP(plan:1514) | 같은 단어로 서로 다른 그래프의 단위를 가리켜 인터페이스 이름이 충돌 | 없음 | 용어: `coupling block`(결합 블록), `compute block`(계산 블록), `cycle block`(SCC 순환 블록). DP는 "결합 블록 단위 DP" | 아니오 |
| X11 | 공통 | 7 | "stage"가 넷: 선언 stage(`compensation.stage_devices`, plan:1016), S1v `stage_index`(plan:1043), history §8의 "Stage 1/2/3"(harness 단계), bkit Phase | G2 산출물 필드명, harness 이름, Phase 이름이 섞인다 | 없음 | 용어집 등록: `signal stage`(S1v 유도), `declared stage`, `pipeline step`(harness), `Phase`(작업 단위) | 아니오 |
| X12 | 공통 | 6 | 실패 규약이 절마다 따로: `review_needed`로 "정지"(plan:1510), "탐색 전에 정지"(plan:1512), `InfeasibleSizingError`(잔차 포함, plan:1057), "명시적 실패"(plan:389), exit 0 결함(#18, plan:1168) | 무엇을 raise/return하고 exit code가 몇이며 보고 파일이 어디인지 design마다 다르게 정하게 된다 | 부분: `class InfeasibleSizingError(ValueError)` SR:6984 존재 | 공통 실패 표: 종류(구조 미확정 / 달성 불가 / 비수렴 / 봉인 위반 / 탐색 실패) × 예외 클래스 × 반환 구조(분류·소자·margin) × exit code × 기록 위치 | 아니오 |
| X13 | 공통 | 1 | 판정 기록 `.ai/verification/<id>.json`(plan:1339, 1367, 1388, 1420) -- 필드 목록 없음. `<id>` 부여 규칙 없음(spec card id? 브랜치 `role/test/<id>`?) | L4 merge gate(plan:1367)와 auditor가 같은 스키마를 써야 하는데 필드가 "test 커밋 해시·실패 test id·red 기록·PASS·보고 수치"로만 흩어져 있다 | 없음 | 스키마 필드 표: id, spec_card, base_commit, test_commit, red{test_ids, 실패 메시지 해시}, green_commit, checks{A1..A10: PASS/FAIL/N/A+근거}, reproduced_numbers{name,value,명령}, approvals[], auditor_run{시각, worktree, 명령}. `<id>` = `YYYYMMDD-<slug>` | 아니오 |
| X14 | 공통 | 3 | "사용자 승인 기록"(plan:1353, A5 plan:1383, D14 plan:1440) -- 형식·위치·누가 쓰는가 없음 | `weakening_diff.py`가 무엇을 읽어 "승인 있음"을 판정하는지 구현 불가. 작성 agent가 승인 기록을 스스로 쓰면 T4 은폐가 재발 | 없음 | 승인 기록 = `.ai/approvals/<id>.md`(오케스트레이터만 쓰기, L1이 gmid-* 쓰기 거부), 사용자 원문 인용 + 대상 diff 해시. A5는 diff 해시 일치로 판정 | 아니오(D14 확정의 구현) |

### Phase 0.5 -- 역할 분리 인프라

| # | Phase | 범주 | 모호한 곳(plan:줄 인용) | design 작성자가 막히는 이유 | 답이 이미 있나(위치) | 해소안 | 사용자 결정? |
|---|---|---|---|---|---|---|---|
| P05-01 | 0.5 | 1,3 | "역할별 쓰기 허용 glob 밖이면 deny"(plan:1364) -- glob 목록이 없다. 권한은 문장으로만(plan:1320-1322) | `role_guard.py`의 핵심 데이터가 없다. 특히 `library/*.topology.json`, `tests/tools/`(정본 데이터를 쓰는 도구, plan:1228), `tests/oracles/`(plan:1349), 레지스트리 문서(plan:1151 "같은 커밋에서 갱신")가 누구 것인지 불명 | 부분: 메모리 "topology.json connectivity는 사용자만, role 메타데이터는 Claude" | 역할 × 경로 allow/deny 표(code-author: `assets/*.py`, `workspaces/run_harness.py`, 레지스트리 문서 / test-author: `assets/tests/**`, `tests/oracles/**` / auditor: `.ai/verification/**` / 오케스트레이터: `docs/01-plan`, `docs/02-design`, `.ai/context.md`, `.ai/approvals` / 전원 금지: `.githooks/**`, `.claude/**`, `tools/gates/**`, `library/*.topology.json` connectivity) | **예**(topology.json 쓰기 주체 -- connectivity는 사용자, role 메타는 누가: 오케스트레이터인가 code-author인가) |
| P05-02 | 0.5 | 1 | "메인 세션의 analog-gmid-design 경로에만 판정"(plan:1417), "메인 세션(agent_type 없음)은 엔진 소스·tests 쓰기 거부"(plan:1364) | "analog-gmid-design 경로"의 술어가 없다(`skills/analog-gmid-design/**` 전체? `assets/` 만? `workspaces/*gmid*`?). RTL agent와 settings를 공유하므로 오탐 범위가 여기서 결정된다 | 없음 | 경로 술어를 glob로 확정 + 판정 대상 도구 목록(Edit/Write/NotebookEdit/Bash의 쓰기 패턴) | 아니오 |
| P05-03 | 0.5 | 1,6 | "hook 입력 필드명(`agent_type` 등)은 문서 요약 기준이라 L1~L2 구현 첫 단계에서 실측"(plan:1373, DoD plan:382) | 필드가 PreToolUse/SubagentStop 중 일부 이벤트에만 있거나 없으면 L1의 역할 판정이 성립하지 않는다. 대안 설계가 계획에 없다 | 없음 | 실측 절차(더미 hook이 stdin을 파일에 기록, 세 역할 각각 호출) + 분기: 필드 없음 -> worktree 경로(cwd) 기반 역할 추론으로 대체 | **예**(필드가 없어 대체 판정을 쓸 경우 -- ★절대원칙상 대체 불가 시 승인) |
| P05-04 | 0.5 | 1,3 | hook 위치 `.claude/hooks/role_guard.py` + "프로젝트 `.claude/settings.json`에 등록"(plan:1417, D15 plan:1441) | 저장소 관례는 `hooks/*.py` 원본 + `install.py --only hooks --project`가 `.claude/hooks/`+settings.json으로 복사(install.py:10-12, 기본은 USER scope). 저장소에는 `.claude/settings.json`이 없고 `settings.local.json`만 있다. 또 "모든 역할에 `.claude/**` 쓰기 금지"(plan:1364)라 누가 hook을 설치하는지 불명 | 부분: install.py:10-19, 190-230 | 원본 = `hooks/role_guard.py`, 설치 = `install.py --only hooks --project .`(사용자 또는 부트스트랩 단계에서 오케스트레이터가 L1 등록 **전**에 실행). 등록 후 `.claude/**`는 전원 금지 | 아니오(D15 확정의 구현 경로) |
| P05-05 | 0.5 | 1,5 | L3 "`.githooks/pre-commit`에 `role_commit_gate.py` 추가, python 없으면 BLOCK"(plan:1366, 1418) | 현 `.githooks/pre-commit`은 agents/*.md 검사만 하고 python 부재 시 **skip**(실파일). `core.hooksPath=.githooks` 설정됨(git config 실측). 별도로 `project-hooks/pre-commit`(다른 프로젝트 설치용)도 있다. 기존 agent 검사의 skip도 BLOCK으로 바꾸는지, 어느 파일을 고치는지 불명 | 부분: 실파일 두 개 | `.githooks/pre-commit`만 수정, 기존 agent 검사와 role 게이트를 순서대로, python 부재는 두 검사 모두 BLOCK. `project-hooks/`는 범위 밖 명시 | 아니오 |
| P05-06 | 0.5 | 1,3 | "커밋은 `Role: code\|test\|audit` 트레일러 필수"(plan:1366) | 오케스트레이터 커밋(계획·spec card·레지스트리), 사용자 수동 커밋, RTL skill 등 **무관 커밋**에도 트레일러를 요구하면 저장소 전체가 막힌다. audit 판정 기록은 커밋되는가? | 없음 | 트레일러 요구 조건 = staged 경로가 gmid 역할 glob과 교차할 때만. 값에 `doc`(오케스트레이터) 추가. 판정 기록은 `Role: audit` 커밋 | 아니오 |
| P05-07 | 0.5 | 1 | "한 커밋이 소스와 tests를 동시에 바꾸면 BLOCK"(plan:1366) -- 소스/tests 경로 분류 규칙 없음 | `tests/tools/derive_achievable_bounds.py`(선언에 `value`+`_derived`를 씀, plan:924), `tests/canonical_theta_star.json`(데이터), `tests/baseline/*` 등 경계 파일의 분류가 L3·A5 결과를 좌우 | 없음 | 경로 분류표(src / test / fixture-data / tool / doc)와 조합 규칙 표 | 아니오 |
| P05-08 | 0.5 | 2 | A3 뮤테이션 "살아남은 변이가 있으면 FAIL"(plan:1381) | (1) 등가 변이(의미 불변) 처리 규칙 없음 -> 영원한 FAIL 가능 (2) "이번에 바뀐 함수" 식별법 없음(Phase 3 이동 커밋은 전 함수가 "바뀜") (3) 변이당 test 선택·시간 상한 없음(SD self-test 30초, plan:1205) | 없음 | 연산자 표(plan:1381의 6종 고정) / 대상 = diff 줄을 포함하는 def 중 AST 해시가 바뀐 것(이동만 한 함수 제외) / 변이당 실행 test = 그 함수 호출을 포함하는 test만(AST 인벤토리) / 등가 변이 면제는 사용자 승인 기록(X14)으로만 | 아니오(D13·D14 원칙) |
| P05-09 | 0.5 | 2 | A4 "피검 함수 본문의 식과 AST 동형"(plan:1382) | 정규화 수준(변수명 치환? 상수 포함?)과 "피검 함수" 식별(test가 import한 심볼? spec card의 interface card?)이 없다 | 없음 | 정규화 = 이름을 위치 인덱스로 치환한 `ast.dump`의 BinOp/Call 부분트리 해시, 피검 함수 = interface card에 적힌 심볼 | 아니오 |
| P05-10 | 0.5 | 2 | A5 약화 분류기 "허용오차 확대·격자 확대·픽스처 입력 이동"(plan:1353, 1383) | 판정 규칙이 없다: `pytest.approx(rel/abs)` 값 증가, `grid_points_per_theta` 증가(2e1944a), fixture 인자 변경의 "이동"과 "정정" 구분 | 부분: audit/agent7_self_concealment.md:17-30 사례별 diff | 약화 패턴 표(AST diff 규칙 7개: assert 삭제 / 비교 완화 / approx 인자 증가 / skip·xfail 추가 / 리터럴 기대값 변경 / fixture 입력 리터럴 변경 / assert를 if·try 아래로) -- 일치하면 무조건 승인 필요, "정정"도 예외 없음 | 아니오(D14 매 건 승인) |
| P05-11 | 0.5 | 2 | A6 "근거 필드 없는 새 숫자 리터럴"(plan:1384) | "근거 필드"가 무엇인지(주석? `value_from_spec`? 상수 표?), 허용 리터럴(0, 1, 2, -1, 인덱스)이 없다 | 부분: plan:1170(#20 폴백 상수 예시), 메모리 "근거 선언값 하나만 남기고 참조" | 허용: {0, 1, -1, 2 in 산술식 계수, 인덱스}, 그 외 리터럴은 `spec`/`topology`/LUT 참조 또는 `# derive: <함수명>` 태그 + 그 함수 존재 검사 | 아니오 |
| P05-12 | 0.5 | 1,5 | A7 배선 검사 "운영 경로(`run_harness` -> ... 도달, 문자열 레지스트리 포함)", "§13.1 AST 인벤토리 재사용"(plan:1385, 1115-1119) | 인벤토리 **스크립트가 저장소에 없다**(감사는 agent 6개가 수행, plan:1115-1116; `tools/` 디렉터리 없음 -- ls 실측). Phase 3 뒤 진입점이 `run_gmid_design_pipeline`(plan:1192)으로 바뀌면 루트도 바뀐다 | 없음 | `tools/gates/reachability.py` 신설을 산출물 표(plan:1414-1421)에 추가, 루트 목록은 설정 파일(Phase 3 전후 둘) | 아니오 |
| P05-13 | 0.5 | 1,3 | interface card "기계적으로 뽑은 시그니처 + spec card"(plan:1371, D12 plan:1438) | 누가 생성하는가, 생성 도구, 아직 없는 신규 함수의 시그니처는 어디서 오는가 | 없음 | 생성 = 오케스트레이터가 `tools/gates/interface_card.py`로(기존 함수: AST 시그니처+docstring 첫 단락, 신규 함수: spec card의 시그니처 절) | 아니오 |
| P05-14 | 0.5 | 1 | spec card 필드(plan:1334-1335), `disputes/<id>.md`(plan:1342), `disputes/_TEMPLATE.md`(plan:1420) | spec card 양식이 한 줄 나열뿐. `disputes/`의 루트가 저장소 루트인지 docs 아래인지 불명 | 없음 | spec card 필드 표(의도 / 관찰 가능한 계약 / interface card / oracle 종류(a~d)와 출처 / 거부해야 할 입력 / 4회로 적용 여부 / 결정 필요 항목 / 승인 기록 링크). 경로 `docs/02-design/specs/`, `docs/02-design/disputes/` | 아니오 |
| P05-15 | 0.5 | 3,5 | 부트스트랩 "첫 구축분은 사용자가 공격 시나리오 결과를 직접 확인"(plan:1423-1424) | "첫 구축분"의 범위(L1만? L1~L4 전부? agents 3개?), 자체 호스팅 전환 시점, 사용자 확인 기록 형식, agents/*.md를 누가 쓰는가(plan:1423은 게이트·시나리오·판정만 배정) | 없음 | 부트스트랩 순서표: ① 오케스트레이터가 agents 3개 + hook·gate 스크립트 초안(예외적으로 메인 세션) ② 공격 시나리오 실행 로그를 사용자에게 제시·확인 기록 ③ D15 등록 ④ 이후 모든 변경은 §14.3 흐름 | 아니오(부트스트랩 방식은 확정됨, 순서만) |
| P05-16 | 0.5 | 4 | 과거 사례 7건 "다음 커밋을 되돌린 상태에서 새 절차가 잡아야 한다"(plan:1408-1410) | 해시가 없는 사례(area α 상쇄, Test 16, 76.48)는 "되돌릴" 커밋이 없다. 재생 입력(합성 diff? 옛 커밋 checkout?)과 기대 게이트 메시지가 없음 | 부분: audit/agent7_self_concealment.md -- α 상쇄 e329283(:20), Test 16 e329283/e5fbf92(:17), 76.48 5dc4679(:63), 3250baa(:26), 2e1944a(:28), 1b9b4ea(:40), caa970b(:22) | 재생표: 사례 / 커밋 / 재생 방식(해당 diff만 담은 합성 커밋을 현재 base에 적용) / 기대 거부 겹(A2~A9) / 기대 메시지 키워드 | 아니오 |
| P05-17 | 0.5 | 1,3 | worktree `role/test/<id>`, "base = 고정된 test 커밋"(plan:1336, 1340), auditor "깨끗한 worktree"(plan:1343), agent frontmatter `isolation: worktree`(plan:1416) | 브랜치 생성·test 커밋을 code worktree base로 넘기는 주체와 명령, 병합본 생성 방법, Windows 경로 제약이 없다 | 없음 | 오케스트레이션 시퀀스(명령 수준): 오케스트레이터가 브랜치 생성 -> test-author 커밋 -> auditor freeze -> 오케스트레이터가 code 브랜치를 test 커밋에서 생성 -> ... -> auditor가 `git worktree add`로 병합본 검증 | 아니오 |
| P05-18 | 0.5 | 6 | L2 "위반 파일이 있으면 exit 2로 완료를 거부(되돌리기 전에는 끝낼 수 없음)"(plan:1365) | `__pycache__`, `.pytest_cache`, probe 결과 파일(메모리 "결과를 파일에 써라") 같은 부산물이 역할 glob 밖이면 agent가 영원히 못 끝난다 | 없음 | 무시 목록(.gitignore 대상 + 명시 목록)과 "무시 목록 변경 = `.claude/**` 변경이라 사용자만" 규칙 | 아니오 |
| P05-19 | 0.5 | 4 | "RTL agent 무동작 케이스"(plan:382, 1417) | 무동작의 판정(hook이 allow를 즉시 반환? 출력 없음? 지연 상한?)이 없다 | 없음 | 판정 = 10개 RTL agent_type과 agent_type 없음+비gmid 경로 각각에서 hook stdout 비어 있음 + exit 0 | 아니오 |
| P05-20 | 0.5 | 3 | A10 "작성자가 보고한 수치를 auditor가 실행해 판정 기록에"(plan:1388) | 작성자의 "보고"가 어디에 있는지(커밋 메시지? agent 최종 응답? spec card?) 없다. auditor는 "작성자의 보고를 증거로 받지 않는다"(plan:1322) | 없음 | 보고 수치는 spec card의 "재현할 수치" 절에 오케스트레이터가 옮기고, auditor는 그 목록을 명령과 함께 재실행 | 아니오 |

### Phase 1 -- test 분리 T0~T3

| # | Phase | 범주 | 모호한 곳 | 막히는 이유 | 답이 이미 있나 | 해소안 | 사용자 결정? |
|---|---|---|---|---|---|---|---|
| P1-01 | 1 | 5 | Phase 1 = T0~T3(plan:61, 1253). T4(plan:1240), T5(plan:1241), T6(plan:1242, D7 승인 필요), T7(plan:1243 "§12 구현 단계와 함께")은 Phase 미배정 | T4의 "결함 #9가 test에서 FAIL로 드러남"은 Phase 4의 FAIL-first와 같은 일인데 담당이 불명. T6은 Phase 2 착수 조건 D7에 의존 | 없음 | 배정: T4 -> Phase 4 착수 첫 작업, T5 -> Phase 1 끝(T3 완료 시), T6 -> Phase 2(D7과 같은 승인표), T7 -> 각 Phase(계약별 Phase 매핑표) | 아니오 |
| P1-02 | 1 | 3,5 | T0 "원인 기록 + 수정(엔진이면 승인) + baseline 재생성"(plan:1236), "T0(Test 16)은 의도 판정이라 spec card -> 사용자"(plan:1426) -- 한편 "Phase 0.5 ~ Phase 3은 추가 결정 없이 착수"(plan:1444) | Phase 1 안에 사용자 결정이 끼어 있는데 결정 목록에 없다. baseline 재생성은 A5 약화(기준선 변경)에 해당하는지도 불명 | 부분: audit/agent7:17(원문 "dispositions 키를 재확인할 것") | §14.9 끝 문장을 "D7·D6·D8 + T0 의도 판정(Phase 1) + D14 발생 시"로 정정. baseline 재생성은 D14 승인 대상 | **예**(Test 16 의도 판정 -- 이미 사용자 몫으로 적혀 있음, 목록 누락만) |
| P1-03 | 1 | 1,4 | T1 "`tests/legacy/selftest_*.py`로 본문 그대로", DoD "stdout이 baseline과 바이트 동일, `PYTHONHASHSEED` 1~5"(plan:1237) | (1) `tests/legacy/`가 목표 트리(plan:1210-1230)에 없음, T2 뒤 존폐 불명 (2) `for ... in set(...)` 잔존(SR:10302, SD 5곳, plan:826)으로 seed마다 stdout이 달라질 수 있어 비회귀인데도 FAIL 가능. baseline이 어느 seed로 캡처됐는지 없음 | 없음 | 트리에 `legacy/`(T2 완료 시 삭제) 추가. DoD = seed k마다 "이관 전 스크립트 stdout(seed k)" 대 "이관 후(seed k)" 바이트 동일 -- baseline 파일 대조가 아니라 전후 대조 | 아니오 |
| P1-04 | 1 | 2,5 | T2 "`pytest -p no:randomly`와 무작위 순서 둘 다 통과"(plan:1238) | 무작위 순서에는 pytest-randomly류 플러그인이 필요한데 설치 여부·정책(최소 릴리스 나이, `ignore-scripts`)이 적혀 있지 않다. mutmut은 같은 이유로 자체 구현(D13, plan:1439) | 부분: D13 선례 | conftest의 `pytest_collection_modifyitems`에서 seed 고정 셔플 구현(자체, 의존성 0), `-p no:randomly` 문구 삭제 | 아니오(D13 선례) |
| P1-05 | 1 | 1 | conftest `real_lut(세션, npz)`, `library_dir`, 임시 topology 팩토리(plan:1212-1213) | 어느 npz(LUT 파일 경로·지문)인지, 임시 topology가 손타이핑 lookalike 데이터 금지 원칙(plan:343 B07 "부분 반영")을 어떻게 지키는지 없음 | 부분: plan:343 | fixture 규칙: 회로 데이터는 `library/*.topology.json`에서만 로드·변형(connectivity 손타이핑 금지), LUT는 저장소 npz 경로 고정 + 지문 기록 | 아니오(B07) |
| P1-06 | 1 | 3 | "T1 기계적 이관은 test-author 커밋 + code-author 커밋 두 개, auditor가 동등성 판정"(plan:1425) | 두 커밋의 순서·중간 상태(블록이 소스와 legacy에 동시 존재) 허용 여부, 동등성 판정 명령이 없다 | 없음 | 순서: test 커밋(legacy 추가) -> auditor가 전후 stdout 동일 확인 -> code 커밋(소스 블록 삭제) -> auditor 재확인 | 아니오 |
| P1-07 | 1 | 4 | T3 DoD `grep -n "PASS\|FAIL" tests/unit` 판정 문자열 0(plan:1239) | `tests/integration`·`contracts`·`regression`이 빠짐. test 이름·docstring의 PASS 단어도 걸림 | 없음 | 대상 `tests/**`(probes 제외), 판정 = `print(`/`logging` 인자 문자열 안의 PASS/FAIL 토큰만 AST로 검사 | 아니오 |
| P1-08 | 1 | 2 | `@pytest.mark.slow`(L5c, Test 53 등 "7+곳", plan:1245) | slow 판정 기준(초)이 없어 test-author마다 다르게 붙인다 | 없음 | 기준 = 실측 시간이 기본 실행 예산(전체 비slow 합계 목표)을 넘기는 test -- 숫자를 박지 말고 `--durations` 실측표를 판정 기록에 첨부 | 아니오 |

### Phase 2 -- 사장코드·동작보존 DUP

| # | Phase | 범주 | 모호한 곳 | 막히는 이유 | 답이 이미 있나 | 해소안 | 사용자 결정? |
|---|---|---|---|---|---|---|---|
| P2-01 | 2 | 1,3 | D7 "레지스트리 §7 D 목록 + probe 삭제 11개를 항목별 삭제/배선 제안표로"(plan:1278) | 제안표 열(항목/근거/호출부 0 증거/배선 시 소비자/삭제 시 영향)이 없다 | 있음(목록): reg:475-540(§7 D), audit/agent5_small_tests_selftest.md(probe 목록) | 제안표 열 정의 + "배선 제안은 ★절대원칙상 소비자·대체 대상 명시 필수" | **예**(D7 -- 이미 착수 조건) |
| P2-02 | 2 | 4 | "동작 보존 DUP 통합 -- 보존 증명: test 전부 통과"(plan:1254) | Phase 1 이관 test가 DUP 함수를 커버하는지 모른다(커버리지 없음). 통과가 곧 보존 증명이 아니다 | 없음 | DUP마다 "옛 함수 vs 정본" 차등 test(4회로 입력 전수에서 출력 동일) 1개를 test-author가 먼저 작성 -> 통합 후 옛 함수 삭제 | 아니오 |
| P2-03 | 2 | 5 | 통합 대상 목록: plan:1254의 7개(W 식, KCL 엣지, theta footprint, euler fixup, 보간, union-find, 위반량 합) vs reg:439-470(§6 DUP 11+7+1) vs reg:36-59(§2 정본표, ★는 Phase 4 공동분석) | Phase 2에서 무엇을 하고 무엇을 Phase 4로 미루는지 목록이 셋이다 | 부분: reg §2 "행동 보존 통합 가능" 표기 | Phase 2 목록 = reg §2에서 상태가 "행동 보존 통합 가능"인 행만, ★ 행은 Phase 4, metric 3쌍(gain/PM/CMRR)은 Phase 7a로 명시 | 아니오 |

### Phase 3 -- 10모듈 분리

| # | Phase | 범주 | 모호한 곳 | 막히는 이유 | 답이 이미 있나 | 해소안 | 사용자 결정? |
|---|---|---|---|---|---|---|---|
| P3-01 | 3 | 1,5 | 의존 열: `stick_diagram.py` 의존 "1, 3"(plan:1189) -- 그런데 SD의 `load_topology`는 #2로 이관(plan:1184), SD `run_topology_pipeline`이 `load_topology`를 부름(reg:46). 레이아웃 test는 "역방향 import"(plan:1223) | 명시된 의존 방향대로 옮기면 SD가 #2를 import해야 해 표가 틀리거나 순환이 생긴다 | 부분: reg 각 표의 "이관 목적지" 열(reg:65, 154, 240...) | 함수 단위 이관표를 레지스트리 목적지 열에서 자동 생성해 의존 그래프를 계산하고, 표의 의존 열은 그 결과로 교체. `topology_library.py`/`design_report.py`/`sky130_lut_sweep.py` 목적지 명시 | 아니오 |
| P3-02 | 3 | 4 | DoD "import 순환 0(검사 스크립트)"(plan:385), "import는 한 방향"(plan:1179) | 스크립트 이름·소유자·"한 방향" 판정 규칙(모듈 번호 순서)이 없다 | 없음 | `tools/gates/import_layering.py`(code-author 작성, test-author 거부 케이스, 판정 = 모듈 번호가 큰 쪽 -> 작은 쪽만 허용) | 아니오 |
| P3-03 | 3 | 2,4 | "이동 전용 커밋(본문 무변경)"(plan:1199) | auditor가 "본문 무변경"을 증명하는 방법이 없다. A3 뮤테이션을 이동 함수 전부에 걸면 비용 폭발 | 없음 | 증명 = 이동 전후 함수별 `ast.dump`(docstring 제외) 해시 동일 + import 줄만 차이. 해시 동일 함수는 A3 대상 제외 | 아니오 |
| P3-04 | 3 | 5 | shim `from gmid_sizing_engine import *`(plan:1194) | `import *`는 `_` 접두 심볼을 안 가져온다(plan:1237이 같은 문제를 이미 지적). 호출부가 `_hr_*`, `_metric_*` 등을 쓰면 shim이 깨진다 | 부분: plan:1237 | shim = 모듈별 명시 재수출 목록(AST 인벤토리에서 생성), `__all__` 사용 금지(비공개 심볼 포함 필요) | 아니오 |
| P3-05 | 3 | 5 | "호출부(`run_harness.py`, probe, workspaces)가 새 모듈을 import하도록 바뀌면 삭제"(plan:1194-1195) | `workspaces/` 아래 보고서 스크립트(git status의 `smoke_run_harness_session18_save.py` 등) 중 어디까지 갱신 대상인지 없음 -- 범위가 없으면 삭제 조건이 영원히 안 선다 | 없음 | 갱신 대상 = grep으로 `sizing_recipe` import하는 파일 전수 목록을 design에 고정, 그 외 workspaces 스크래치는 "갱신 안 함(깨짐 허용)" 여부를 명시 | **예**(workspaces 일회성 스크립트를 깨지게 둘지) |
| P3-06 | 3 | 1 | `run_harness.py`는 "`canonical_spec()`/`SPECS`만 남는 얇은 호출자"(plan:1192) -- 위치는 skill 밖 `workspaces/` | 정본 spec(`canonical_spec`, SR 8151 계열)이 skill 패키지 밖에 남으면 `gmid_design_pipeline`이 workspaces를 import하는 역방향 의존 | 없음 | 정본 spec 정의를 `topology_authoring.py`(또는 `library/` 데이터)로 옮길지 명시 | 아니오 |

### Phase 4 -- 결함 #1~21

| # | Phase | 범주 | 모호한 곳 | 막히는 이유 | 답이 이미 있나 | 해소안 | 사용자 결정? |
|---|---|---|---|---|---|---|---|
| P4-01 | 4 | 6,5 | #3 "게이트 `ValueError`가 탐색 전체 크래시"(plan:1080) -- 무엇으로 바꾸는지 없음. "실패도 결과(margin)"는 Phase 5(plan:1068) | Phase 4에서 고칠 때 반환 규약(구조화 실패? 페널티?)이 없고, Phase 5에서 다시 바뀐다 | 없음 | Phase 4에서 X12의 구조화 실패 타입을 도입(분류·소자·margin 필드), SLSQP 쪽은 그 실패를 infeasible로 받음. Phase 5는 그것을 캐시만 | 아니오 |
| P4-02 | 4 | 5 | #1 vsb/W 버전 혼재, #2 conflicts 미검사를 Phase 4에서 수정(plan:1256) -- 같은 것을 6b 봉인 게이트·D1이 구조로 제거(plan:389, 1515) | 이중 구현. Phase 4 수정이 6b에서 버려지면 "만들고 대체"가 반복되고, #2의 허용오차(history:1185 "~1mV" vs D2 계산)도 두 번 정한다 | 없음 | Phase 4 범위 = "틀린 값을 쓰지 않게 거부"(conflicts가 있으면 명시 실패, W를 vsb 확정 후 재계산)만, 허용오차는 D2 계산 함수 하나를 Phase 4에서 만들고 6b가 재사용 | 아니오(D2: 계산) |
| P4-03 | 4 | 2,3 | #8 "C-d(불일치=없음) 도입 시 픽스처와 정본을 구분하는 방법을 함께 정해야 한다"(plan:1085), 부록 "미결"(plan:370) | 결정 주체·방법이 없는데 Phase 4 착수 조건에도 없다 | 없음 | 후보: spec에 `origin: canonical\|fixture` 필드 필수, fixture는 유도 임계값을 읽지 않고 fixture 자신의 선언만 사용 | **예**(공유 엔진 동작 변경 -- 승인 원칙) |
| P4-04 | 4 | 4 | DoD "결함 #1~21마다 FAIL-first test"(plan:386) | #6 광범위 except, #13 캐시 키, #19 레일 넷 대소문자, #20 폴백 상수, #21 probe 실행 불가는 행동 test로 red를 만들기 어렵다(lint류) | 없음 | 결함별 test 형태표(행동 test / A6 lint 규칙 / fixture 기반 KeyError 재현), lint로 잡는 것은 "base에서 lint FAIL"을 red로 인정 | 아니오 |
| P4-05 | 4 | 5 | 착수 조건 D8 "diode·미러 키·diffpair/tail 공동분석"(plan:1279) -> "D8은 J1~J9로 확장"(plan:1543) -> J1~J9는 6a 착수 조건(plan:66) | Phase 4가 J1~J9 전부를 기다리는지, D8 원래 3개만인지 불명 | 없음 | Phase 4 = D8 핵심 3개(reg:39-41 ★행), J1~J9 = 6a. §15.7 끝 문장을 "D8 결론을 J 목록의 입력으로"로 정정 | **예**(D8 -- 이미 착수 조건) |
| P4-06 | 4 | 1 | A8 "엔진이 결과에 `fallback_events`를 노출(Phase 4에서 code-author가 구현)"(plan:1386) | 필드 위치(ctx? 반환 dict?), 이벤트 스키마, 무엇이 폴백인지(#14 5곳, #20 상수, except 흡수) 목록이 없다 | 부분: plan:1164, 1170 목록 | 이벤트 스키마 {site(함수:라벨), kind(except/default/skip), device, detail} + 계측 대상 전수 목록 | 아니오 |
| P4-07 | 4 | 3 | D6 "4회로 비교 수치를 제시하고 결정"(plan:1277) | objective가 바뀌면 착지가 바뀌어 기존 test 기대값(착지 수치)이 대량 변경 -> A5 약화 분류기에 전부 걸린다. 일괄 승인인지 매 건인지 불명 | 부분: D14 "매 건" | D6 승인 기록에 "objective 변경으로 인한 기대값 변경 목록"을 첨부해 한 승인으로 묶음(각 건은 목록에 열거) | **예**(D6 + 묶음 승인 허용 여부) |
| P4-08 | 4 | 2 | #10 "이분 역산이 단조성을 검사하지 않음"(plan:1160) -- 비단조 발견 시 동작 없음 | 명시 실패인지, B20처럼 rightmost root인지 결정 없음 | 부분: A19 B20 `_solve_vgs` rightmost root 사용자 승인(plan:274) | 기본안 = 단조 구간 분할 후 전체 근 반환 + 호출자가 선택 규칙 명시(B20 선례 확장) | **예**(공유 엔진 변경 승인) |
| P4-09 | 4 | 6 | #18 "실패해도 exit 0"(plan:1168) -- 비0 코드 체계 없음 | CI/auditor가 실패 종류를 구분 못 함 | 없음 | X12 표의 exit code 열로 해소 | 아니오 |

### Phase 5 -- 실패 캐시·θ*

| # | Phase | 범주 | 모호한 곳 | 막히는 이유 | 답이 이미 있나 | 해소안 | 사용자 결정? |
|---|---|---|---|---|---|---|---|
| P5-01 | 5 | 1,2 | "예외를 구조화된 실패(분류·소자·margin)로 캐시", "제약 함수는 가능하면 margin"(plan:1068) | 캐시 키(θ 부동소수 정확 일치? 양자화?), 실패 분류 체계, 예외에서 margin 추출법, "가능하면"의 대상 제약 목록이 없다. 페널티를 margin으로 바꾸면 탐색 경로·착지가 바뀐다(동작 변경 기록 필요) | 부분: plan:1013(811회 중 784 중복 실측) | 키 = θ 벡터 `float.hex` 튜플 + 평가 문맥 지문, 분류 = X12 표, margin = 위반 제약의 정규화 위반량. 착지 변화는 4회로 전후표 | 아니오 |
| P5-02 | 5 | 2 | "start 사전선별"(plan:1257) | 선별 기준(아카이브 실현가능 여부? 저비용 평가 순위?)과 선별 수가 없다 | 부분: plan:1069(S3 상위 k개 + 전역 샘플) | Phase 5 기준 = 아카이브에서 지문 일치 feasible 점 우선, 없으면 기존 x0. k = 기존 `n_starts`(SPECS 선언값)로 -- 새 상수 없음 | 아니오 |
| P5-03 | 5 | 1 | "θ* 기록 + 아카이브 시드"(plan:1257) | 파일 위치·형식이 없다. `tests/canonical_theta_star.json`이 이미 있고 엔진이 안 읽는다(plan:1012) | 부분: 기존 파일 존재(ls) | 기록 위치 `library/<name>.search_archive/`(데이터, test 경로 아님) + 레코드 스키마(X07) | 아니오 |
| P5-04 | 5 | 4 | DoD "SLSQP 동일 점 재평가 0, θ* 기록이 다음 실행 시작점으로 쓰임을 실측, 탐색 시간 전/후"(plan:387) | "0"의 측정법(계수기 위치), 시간 개선 판정 기준 없음 | 없음 | 계수기 = 평가 함수 입구의 θ 키 적중/미적중 카운터를 판정 기록에. 시간은 보고만(게이트 아님) 명시 | 아니오 |

### Phase 6a -- S0/S1 구조 유도 + S1v stage 분할

| # | Phase | 범주 | 모호한 곳 | 막히는 이유 | 답이 이미 있나 | 해소안 | 사용자 결정? |
|---|---|---|---|---|---|---|---|
| P6a-01 | 6a | 1 | S1 "넷/소자·수동소자·이상소스, 타입 있는 관계 엣지 `equal_vgs`·`vds_eq_vgs`·`same_as`·`budget_ref`·`stacked_vsb`·`matching{offset,ratio}`, 모든 유도 사실에 status + 증거 net"(plan:1042) | 필드 수준 스키마(노드 속성, 엣지 속성, 증거 표현, 방향성)가 없다 | 부분: history:2911-2931(§11.2 노드/엣지 필드 -- 폐기된 §11용이나 소비자 역산 표는 유효), audit/review_B:109-115(결합변수 추출용 필드) | 스키마 표(노드: name, terminals[(dev,term)], is_rail, ac_ground_class, port_role / 소자 엣지: kind, d/g/s/b, is_diode / 관계 엣지: type, members, status, evidence{rule, nets}) | 아니오 |
| P6a-02 | 6a | 2 | S0 "유도 규칙 코드 해시(유도 함수 소스에서 계산)", "LUT 내용+생성메타 해시"(plan:1041), G0 "metric 정의 해시"(plan:1508) | 어느 함수들(전이 폐포?)의 소스인지, 정규화(주석·docstring 제외?)가 없다 -- Phase 3 이동만으로 해시가 바뀌면 전 캐시가 무효. `lut_conditions_from_npz()`는 운영 호출 0(plan:827) | 없음 | 해시 = S1 유도 함수 집합(AST 인벤토리에서 호출 폐포)의 `ast.dump`(docstring 제외, 모듈 경로 제외). LUT 메타는 `lut_conditions_from_npz` 배선으로(★절대원칙) | 아니오 |
| P6a-03 | 6a | 2 | 규칙 "DM 뷰 + R2 -- gate→drain +1, source→drain 같은 stage, diode 노드 게이트 gate→drain 같은 stage, 부하·tail 분류", "R2ng도 거의 같다"(plan:1479-1481) | 채택 규칙이 R3(DM/R2)인지 R2ng인지 확정 문장이 없다. DM 뷰 구성(대칭 대응의 `unresolved`/`low_conf` 처리, 자기대응 넷=가상접지, 단일출력 대응 제거 규칙)이 계획에 없다 | **있음**: audit/probe_stage_partition.result.md:3(R1/R2/R3 정의), :16-19(자기대응·low_conf), :206("단일출력이라 대응 제거 [신규 규칙]"), :593-644(요약: R3(DM/R2)만 4회로 전 선언 100%, R2ng는 folded 4/5) + probe_stage_partition.py | "채택 = R3(DM/R2), 0-1 BFS 최소 index. DM 뷰 = `find_structural_symmetry_candidates` mirror 대응, 자기대응 넷은 가상접지, unresolved 소자는 DM 뷰에서 제외하고 목록 보고, 단일출력 회로는 출력-대응 쌍 제거" 를 본문에 인용. probe는 **같은 방법이라 oracle이 아님** -- oracle은 4회로 ratified 선언(§14.3 (d)) | 아니오(실측 결과로 확정) |
| P6a-04 | 6a | 4,2 | G2 산출물 "stage별 {input, cascode, load, tail, **출력노드, G_out 기여 소자 전부**}"(plan:1510) -- DoD는 "소자 단위 100%"만(plan:388) | 실측 100%는 소자 stage index 일치뿐이다. two_stage R3(DM/R2) stage1 **출력노드=[]**(O1을 잃음, probe:371) -- J5(plan:1537)의 현상. 출력노드·G_out 기여자는 검증되지 않았는데 7a/6c가 그것을 입력으로 쓴다 | 부분: probe:173-183, 410-422(출력노드 gds 기여자 수작업 대조) | 6a DoD에 "stage 출력노드 집합과 G_out 기여 소자 집합이 ratified 대조표와 일치" 추가, J5 해소 전에는 two_stage·nmcnr 출력노드를 `review_needed`로 명시 | **예**(J5 -- 회로 해석) |
| P6a-05 | 6a | 2 | 교류접지 "레일, gate-only 넷"(plan:1485) | 이상 전압원 단자, 입력·수동소자 단자 제외 조건이 빠짐 -> 구현자가 gate-only 입력 넷(vin)을 접지로 잘라낼 수 있다 | **있음**: probe:10-12(G1 레일 / G2 gate-only 비구동, 입력·수동·이상원 단자 아님 / G3 이상 전압원 단자), 대조 probe:313 | 3분류 정의를 본문에 인용 + J1(replica bias) 결론을 G2 예외로 반영하는 자리 | 아니오(규칙) / J1은 **예** |
| P6a-06 | 6a | 1,3,7 | 상태값 두 벌: `status{declared/derived/proposed/review_needed}`(plan:1042) vs `status{derived/ratified/review_needed}`(plan:1495). DoD "ratified 선언과 100%"(plan:388) | 상태 전이(누가 derived->ratified로 바꾸나), 저장 위치가 없다. `sizing_spec.json`은 7b(plan:1555)인데 6a가 ratified를 저장해야 한다. topology.json은 connectivity 전용(plan:114) | 없음 | 단일 상태 집합 {declared, derived, proposed, review_needed, ratified} + 전이표(derived/proposed -> review_needed: 엔진, review_needed -> ratified: 공동분석 후 오케스트레이터가 사용자 원문과 함께, ratified -> review_needed: S0 지문 변경 시 자동). 저장 = `library/<name>.structure.json`(6a 신설, 7b에서 sizing_spec.json 유도 필드로 흡수) | 아니오(topology.json 전용 원칙에서 별도 파일이 도출) |
| P6a-07 | 6a | 6 | "shadow 모드로 기존 선언과 매 실행 대조(동작 무변경)"(plan:1551) vs "불일치는 `review_needed`로 정지"(plan:1510) | shadow에서 파이프라인을 멈추면 동작 변경이다. 무엇이 멈추는지(엔진? test?) 불명 | 없음 | 6a: 불일치 = 대조 보고 파일 + contracts test FAIL(파이프라인은 기존 선언으로 계속). 정지는 유도값을 **소비**하기 시작하는 Phase(6c/7a)부터 | 아니오 |
| P6a-08 | 6a | 5 | D5 ports "착수 조건: Phase 0 선행"(plan:1102), "D5 ports 확인은 Phase 0 선행"(plan:1444) -- Phase 0은 ✅ 완료(plan:59), folded·nmcnr은 ports 없음(plan:1489), two_stage 출력 미선언(probe:308 "제안: gain metric sense") | 착수 조건 표기가 자기모순이라 6a 착수 판정을 못 한다 | 부분: §0.2 6a 행에 D5(plan:66) | plan:1102·1444의 "Phase 0 선행"을 "6a 착수 조건"으로 정정, 대상 3회로(two_stage 출력 포함) 명시 | **예**(D5 절차상 사용자 확인) |
| P6a-09 | 6a | 5 | 6a 착수 조건 "J1~J9 공동분석"(plan:66, 1551) | J7(Cc–Rz 극성), J8(`fold_group`/`budget_reference_device`), J9 중 passive 누락은 stage 분할과 무관하고 G5/K5에서 쓰인다 -- 전부를 선행하면 6a가 불필요하게 막힌다 | 부분: plan:1531-1541 근거 열(C/A/D) | J 항목별 소비 Phase 열 추가(J1~J6·J9 ports -> 6a, J7 -> 7b, J8 -> 6b(vsb 오류 4소자), J9 passive -> 7b) | 아니오(배치) / 각 J 내용은 **예** |
| P6a-10 | 6a | 1 | S1v "`(excite, sense)` 모드별"(plan:1043), "어느 여기 모드가 스펙인가는 graph로 안 됨"(plan:1488) -- G0 사람 선언 목록(plan:1508)에 모드 선언 없음 | 어떤 모드들을 계산하는지(DM/CM/supply), 모드 목록의 출처가 없다 | 부분: 기존 metric 선언이 `excite`/`sense_p`/`sense_n`을 가짐(plan:755) | G0에 "S1v 모드 = metrics 선언의 (excite, sense) 집합에서 수집" 규칙 추가, 모드 없는 회로는 DM만 | 아니오 |
| P6a-11 | 6a | 2 | "피드백 엣지 + 극성"(plan:1043, 1510), "DM의 Cf 궤환 극성"(plan:1486) | 수동소자가 닫는 루프는 부호 집합이 [-1, 1] 혼재로 나온다(probe:41-54, 87-98) -- 혼재 시 판정 규칙 없음 | 부분: probe:40 "저주파 부호, -1=부궤환 후보" | 규칙: MOS만 복귀 경로의 부호가 단일이면 그 부호, 혼재면 `review_needed`. Cc–Rz는 J7 | J7은 **예**, 규칙은 아니오 |
| P6a-12 | 6a | 5 | G1 "레지스트리 정본 함수만 사용"(plan:1509) -- diffpair/tail 정본은 "(미정)"(reg:41) | 정본이 없는 개념을 6a에서 무엇으로 유도하나 | 부분: reg:41, probe:186-187 교차확인 | Phase 4 D8 결론이 정본을 확정 -> 6a 입력으로 명시(P4-05와 연결) | D8에 포함 |

### Phase 6b -- 노드전압 정본 + writer 티어 + 봉인 게이트

| # | Phase | 범주 | 모호한 곳 | 막히는 이유 | 답이 이미 있나 | 해소안 | 사용자 결정? |
|---|---|---|---|---|---|---|---|
| P6b-01 | 6b | 2 | 봉인 게이트 "KVL 합, KCL 잔차, 노드전압 충돌, 버전 일치"(plan:1515) -- 항목별 임계값 없음 | D1에서는 스택 KVL 합이 노드전압 차이로 **항등식**이라 KVL 검사는 정의상 참(자기참조)이 된다. 정작 A14 요구사항 "KVL/KCL/**VGS**"(plan:269)와 history §7.5의 "재구성 Vgs vs LUT 예측 Vgs" 검사(history:1187-1190)가 봉인 목록에서 빠졌다 | 부분: history:1179-1190, `kcl_residual_uA` metric(plan:810, `exclude_nets` 포함) | 봉인 항목 재정의: ① 노드 충돌(경로별 값 차 ≤ tol_V) ② **VGS 정합**(노드 차 VGS vs `vgs_for_gm_id` ≤ tol_V, diode 포함) ③ KCL 잔차(≤ tol_I, `exclude_nets` 사용 금지 또는 사유 기록) ④ 버전 일치(정확 일치). tol_V·tol_I는 D2 함수 출력 | 아니오(A14·D2) |
| P6b-02 | 6b | 2 | D2 "LUT VDS 격자 간격과 보간 오차에서 계산. 계산 방법은 Phase 6 design 문서에서 명세"(plan:1099) | 입력은 있으나 식이 없다. 보간 오차를 어떻게 추정하나, 반복 상한은 무엇에서 유도하나(상수 금지) | 부분: `tests/probe_interp_scheme_loo.py`/`.result.txt`(LOO 보간 오차 실측 도구 존재, ls), diode 고정점은 bisection(plan:808) | 제안 식: tol_V = max over (kind, L 앵커) LOO 보간 오차(vgs) ; tol_I = tol_V × max gm(해당 블록) ; 반복 상한 = bisection이면 ceil(log2(구간폭/tol_V)), 고정점 반복이면 수축률 추정 기반 -- 둘 다 계산값. 비수렴 = 상한 도달 시 잔차 포함 `InfeasibleSizingError` | 아니오 |
| P6b-03 | 6b | 1 | writer 티어 T0 레일/T1 구조 항등/T2 물리 종속 블록/T3 **선언된 노드전압 목표**/T4 자유 노드(plan:1498), C-a "필드×writer 티어 권한표"(plan:1055) | 권한표 본체가 없다. T3의 선언 필드가 무엇인지(G0 목록 plan:1508에 없음; `Voc_des`? `vdd_kvl`? `C` diode_stack target_net?) 불명 | 부분: history:348-350(`diode_stack.target_net`) | 권한표(S2 필드 × W0~W4 × 허용 연산) + W3 소스 필드 목록을 G0에 추가 | 아니오 |
| P6b-04 | 6b | 1 | "유도 DAG의 SCC로 순환 블록을 구조적으로 찾아"(plan:1057), 순환 10종(plan:1019) | DAG 노드가 필드인지 계산 블록인지, 엣지를 무엇에서 얻는지(선언된 블록 입출력? S1 관계 엣지?) 없다 | 부분: plan:1019 순환 목록, audit/review_B:28 | DAG 노드 = S2 필드 그룹(노드전압/소자 op/스택 배분), 엣지 = 계산 블록 입출력 선언(§12.5.3)에서 생성. 10종 순환이 SCC로 나오는지를 6b DoD에 | 아니오 |
| P6b-05 | 6b | 4 | DoD "순서 섞기 불변(C2)"(plan:389), C2 "instance.json이 바이트 동일"(plan:215) -- B12 `set` 순회 결정론은 7c(plan:826) | 무엇을 섞는지(`by_name` dict 순서, 그룹 순서, set)와 동일 판정(바이트? 고정점 반복이 있으면 부동소수 차)이 없다. 결정론 수정이 7c라 6b DoD가 먼저 깨진다 | 없음 | 섞는 대상 3종 명시, 판정 = 이산 필드 완전 일치 + 연속 필드 ≤ tol(D2). B12 수정은 6b로 당김 | 아니오 |
| P6b-06 | 6b | 6 | "노드 충돌은 명시적 실패"(plan:389) | 탐색 중(SLSQP 안) 충돌이 나면 크래시인지 구조화 실패인지(P4-01 규약과 연결) 불명 | 없음 | X12 "봉인 위반" 행으로 통일, 탐색 중에는 margin=충돌 크기로 반환 | 아니오 |
| P6b-07 | 6b | 5,4 | "6b 전 shadow 동등 단언"(plan:409) -- D1은 값을 바꾸는 것이 목적 | 무엇과 "동등"해야 하는지 없다 | 없음 | 동등 대상 = 봉인 위반이 없던 옛 경로 소자만. 값이 달라진 소자는 "달라진 이유(W0~W4 중 어느 writer)" 기록과 함께 허용 | 아니오 |
| P6b-08 | 6b | 2 | S2 "상한 있는 LRU"(plan:1044), A6 "상한 없는 캐시 금지"(plan:1384) | LRU 상한 값의 근거가 없다(상수 금지) | 없음 | 상한 = 탐색 1회 예상 평가 수(D4 계산값) × 계산 블록 수, 실측 메모리로 검증 | 아니오 |
| P6b-09 | 6b | 2 | C-b "파생 필드는 입력 버전을 기록"(plan:1056) | 버전 표현(내용 해시? 단조 카운터?)과 비용이 없다 -- 평가 72.9ms 예산(메모리 실측)에 필드마다 해시를 붙이면 역행 | 없음 | 버전 = 쓰기마다 증가하는 writer 카운터(필드 단위), S2 memo 키만 내용 해시 | 아니오 |

### Phase 6c -- 결합 블록 + 달성가능성·DOF 진단

| # | Phase | 범주 | 모호한 곳 | 막히는 이유 | 답이 이미 있나 | 해소안 | 사용자 결정? |
|---|---|---|---|---|---|---|---|
| P6c-01 | 6c | 7,1 | G3 "관계 엣지의 **연결성분**으로 블록을 묶는다: 출력노드 부하가 다른 미러·L 동치류에 속하면 같은 블록"(plan:1511) vs G6 "블록 간 결합변수 y(공유 VGS, 공통 L, 스택 배분)"(plan:1514) | 연결성분으로 묶으면 파일럿은 미러 18소자가 tail·bias·부하를 잇기 때문에(plan:735 계열) 사실상 **한 블록**이 되고 y가 비어 3층 할당이 성립하지 않는다. 두 문장이 서로 반대 정의 | **있음**: audit/review_B:107-119(블록 = S1v stage 블록, y = K1 경계 부하·K2 블록을 넘는 equal_vgs·K3/K4 공유 스택을 S1 엣지에서 추출) | G3 문장을 review_B 정의로 교체: "결합 블록 = S1v signal stage, 결합변수 y = 두 블록 이상에 걸친 관계 엣지 멤버의 상태". 연결성분 문구 삭제 | 아니오(원자료 채택) -- 경계 부하 귀속은 J6 **예** |
| P6c-02 | 6c | 2,5 | G4 "블록별 A_i,max 표(출력노드 부하 gds 포함, LUT 격자 전수)"(plan:1512); P8 "보상이 고정한 gm에서 A_i,max 합"(audit/review_D:40) -- G4는 6c, G5(보상)는 7b | A_i,max가 (gm_id, L, VDS)에 대해 무엇을 최대화하는지, 경계 부하 소자(y)의 상태를 어디에 두는지, VDS 범위를 어디서 얻는지(D1 자유 노드) 없다. 보상 선행이 필요한지 순서도 모순 | 부분: audit/review_B:142("A_i,max = max over (gm_id,L,VDS) of gm/gds", H:1364) | 6c 정의 = 보상 무관 상한: max over (x_i, y ∈ 가능역) 20log(gm_i·R_out,i), VDS 범위 = W4 자유 노드 창. 7b에서 보상 고정 gm으로 재계산하는 "정밀 판정" 추가 | 아니오 |
| P6c-03 | 6c | 2 | "구조 DOF(등식만) + θ 표본 Jacobian 수치 rank"(plan:1501, 1512) | 표본 θ 개수, FD 스텝, rank 허용오차가 없다 -- 상수를 지어내게 된다 | 없음 | rank 허용오차 = `numpy.linalg.matrix_rank` 기본(σ_max·max(m,n)·eps, 표준 정의), FD 스텝 = LUT 격자 간격 기반, 표본 수 = D4 예산 안의 계산값 | 아니오 |
| P6c-04 | 6c | 1 | DOF "스택별 자유도 = (k−1) − (diode·offset·budget_ref 등식 수)"(plan:1501) | 변수·방정식 목록의 전체 표가 계획에 없다 | **있음**: audit/review_B:168 이후(Q3 변수·방정식 표), history:1308-1348(옛 알고리즘·상태값·overconstrained 대응) | review_B Q3 표를 본문에 인용, 반환 `DofReport{status: ok\|underdetermined\|overconstrained, 경쟁 목표 쌍}` 유지(history:1328) | 아니오 |
| P6c-05 | 6c | 2 | "LUT 곡선 단조·볼록·단위는 로드 시 검사해 해법 선택에 반영"(plan:1512) | 검사 판정 기준과 "해법 선택" 매핑(비단조면 무엇을 쓰나)이 없다 | 부분: plan:1160(PMOS 75.3% 비단조 실측), history:1575(A10 gm/gds 비단조) | 매핑표: 단조 -> 이분 역산 허용 / 비단조 -> 격자 전수(DP)만 / 단위 불일치 -> 로드 거부 | 아니오 |
| P6c-06 | 6c | 2,5 | "제약별 달성 상한"(plan:1512)을 **탐색 전에** | 기존 `achievable_metric_bound`는 전체 탐색 반복(한 스텝=탐색 1회, plan:941 "수십 분")이라 "탐색 전 저비용 진단"과 충돌 | 부분: SR:8271 | 6c 범위 = LUT·구조만으로 계산 가능한 상한(gain, 전류)만, 나머지 제약은 "상한 미상"으로 보고. 탐색 기반 상한은 G0 출처 도구(X09)로 분리 | 아니오 |
| P6c-07 | 6c | 4 | DoD "달성 불가 픽스처에서 탐색 전 정지"(plan:390) | 픽스처 oracle 출처(§14.3 4종 중 무엇)가 없다 -- test-author가 기대값을 못 만든다 | 없음 | oracle (a) 손계산: 목표 gain > Σ 블록 이론 상한(LUT 격자 전수를 test가 **다른 방법**으로 계산)인 선언 | 아니오 |
| P6c-08 | 6c | 5 | "결합 잔차(블록 gain 합 대 전체회로 gain)는 기존 6480조합 데이터로 먼저 잰다 -- 아직 측정하지 않았다"(plan:1526) | 이 측정이 어느 Phase의 작업인지, 결과가 6c 블록 정의·7a 설계의 전제인지 없다 | 부분: `tests/probe_mirror_gain_ranking.py`/`.result.txt`, audit/review_B:119 | 6c 첫 작업으로 배정, 잔차가 0이 아니면 해당 블록 쌍을 MT3로 표시 | 아니오 |

### Phase 7a -- gain metric 통일 + 감도 게이트 + B21

| # | Phase | 범주 | 모호한 곳 | 막히는 이유 | 답이 이미 있나 | 해소안 | 사용자 결정? |
|---|---|---|---|---|---|---|---|
| P7a-01 | 7a | 2 | "stage gain은 그 노드전압에서 얻는 분해 부산물"(plan:1516) | 계산식이 없다(연속 stage 출력노드 AC 전압비? 피드백 엣지 Cf를 끊은 개루프?). 비율의 곱이 전체와 같으면 다시 "정의상 참" 비교가 된다 | 부분: audit/review_B:116-118(`gain_total = Σ 20log(gm_i·R_out,i(x,y))`) | 분해 = 블록별 `20log(gm_i·R_out,i)`(review_B 식, 부하 포함). 전체 = MNA. 잔차 = 둘의 차 -- 곱-비율 정의는 금지 명시 | 아니오 |
| P7a-02 | 7a | 2 | 감도 게이트 "분해 값 변화 0인데 전체회로 값이 변하면 오류"(plan:1516, review_D P2 "FD 스텝에서") | "0"의 수치 판정, 섭동 방향(모든 θ? 결합변수만?), 실행 시점(매 평가? 봉인마다?), 괴리 경보 기준이 없다 | 부분: audit/review_D:34 | "0" = MNA 해의 수치 분해능 이하(선형해 잔차에서 계산), 방향 = S1 영향 집합(P7)에서 분해 metric이 읽지 않는 소자를 건드리는 θ, 시점 = 봉인 스냅샷마다 1회 | 아니오 |
| P7a-03 | 7a | 1,5 | "gain metric은 전체회로 MNA(DM 뷰) 하나"(plan:1516) | 교체 대상(`gain_stages_sum`, `folded_cascode_gain_db`, `nmcnr_gain_db`, reg:53)과 회로별 excite/sense 선언 -- folded·nmcnr은 ports 없음(plan:1489), folded는 `omega_c` 미노출(plan:484) | 부분: reg:53 | 회로별 이관표(현 metric type -> `smallsignal_gain_db` 선언, excite/sense 넷, 필요 선행 J9/D5) | 아니오 |
| P7a-04 | 7a | 5 | 7a 착수 조건 "D6·D8"(plan:69, 1554) -- D6·D8은 이미 Phase 4 착수 조건(plan:1277, 1279) | 중복 조건이라 "Phase 4에서 결정된 것을 다시 묻는가"가 불명 | 없음 | 7a 조건에서 D6·D8 삭제(Phase 4 결론 인용), 대신 J6(B21 부하 귀속) 명시 | 아니오 |
| P7a-05 | 7a | 2 | "T1/T2/T3는 reader 기록 support set으로 자동 분류"(plan:1500, 1516) | support set -> 티어 매핑 규칙이 없다. C-a reader 기록은 6b 산출물인지 불명 | **있음(정의)**: history:669-673(T1 stage-local / T2 stage-분해가능 / T3 기약 전역) | 매핑: support ⊆ 한 블록 -> MT1, 블록별 항의 합으로 표현 가능 -> MT2, 그 외 -> MT3. reader 기록은 6b 산출물로 명시 | 아니오 |
| P7a-06 | 7a | 5,2 | G9 "metric 등록 시 `verified_by` 필수"(plan:1517), review_D P5 "미검증 metric은 제약 사용 금지"(audit/review_D:37) -- SPICE는 7c | 7a가 새 MNA gain을 제약으로 쓰는 순간 `verified_by`가 없다. P5를 따르면 7a~7b의 gain 제약은 쓸 수 없다 | 없음 | 선택지: ① SPICE AC gain 대조(7c의 일부)를 7a로 당김 ② 7a~7c 사이 "검증 대기" 표시로 제약 사용 허용 + 보고에 명시 | **예**(순서·원칙 적용 범위) |
| P7a-07 | 7a | 4 | DoD "B21 재현 픽스처에서 감도 게이트 FAIL"(plan:391) | 픽스처 구성(미러 18소자 변화 조합 몇 개, 어느 θ)과 oracle이 없다 | 부분: `tests/probe_mirror_gain_ranking.py`(6480조합) | 픽스처 = 6480조합 중 `gain_stages_sum` Δ=0 & MNA Δ 최대인 두 점(데이터에서 선택), oracle = (c) 기존 실측 데이터 | 아니오 |

### Phase 7b -- 보상 먼저 + 3층 gain 할당 + sizing_spec.json

| # | Phase | 범주 | 모호한 곳 | 막히는 이유 | 답이 이미 있나 | 해소안 | 사용자 결정? |
|---|---|---|---|---|---|---|---|
| P7b-01 | 7b | 1 | `sizing_spec.json` "필드를 둘로 가른다: graph 유도 vs 사람 선언"(plan:1495) | 필드 수준 스키마·버전·로더 시그니처(`load_sizing_spec` def 0, plan:1133)·4회로 이관 절차·topology.json에서 `sizing_roles`/`device_roles`/`compensation` 제거 시점이 없다. 이력 초안(history:280-463)은 v4.0 개념(자유 theta 폐기·"gm_id 유일 자유축"·수동 `stages[].devices`·`load: []`)이라 그대로 못 쓴다(plan:1496 "폐기") | 부분: history:280-463(초안), plan:1495(분리 목록), plan:823-824(C6 미사용 필드, C7 slew 명칭) | 스키마 v5 표(섹션: meta{schema_version, topology_hash} / human{objective, constraints[+source], ports, value_amp, compensation_targets, driving_spec, cross_kind_matching, same_as} / derived{필드, status, evidence, rule_hash}) + 필드별 history 초안 대비 유지/폐기 열 + slew 명칭 확정 | 아니오 |
| P7b-02 | 7b | 2,6 | 3층 할당 "수렴 판정·반복 상한·명시적 실패"(plan:408) | 좌표강하 종료 조건, y 1-D 격자 해상도, 반복 상한 유도, SLSQP polish 인자가 없다 | 부분: audit/review_B:126("각 단계 정확 최소화면 목적값 비증가") | 종료 = 한 바퀴에서 y 불변 또는 목적값 감소 ≤ DP 격자가 만드는 목적값 분해능, 상한 = y 격자 점 수 합(유한 격자라 순환 없음 증명), polish = SPECS 선언 `slsqp_kwargs` | 아니오 |
| P7b-03 | 7b | 1,2 | 내층 "블록별 DP(gm_id × L)"(plan:1514) | DP 상태·격자(gm_id 격자 출처, L 격자 = LUT 앵커 12 vs 정본 spec `L_candidates` 41점 plan:452), 제약 결합(gain dB bin 해상도, 면적 bin), 목적(전력 D6) 정의가 없다 | 부분: history:1607-1720(v4.2 분리형 DP, 면적 bin·N=4 0.294s) | DP 명세 표: 상태 = (블록, 누적 gain bin), 결정 = (gm_id, L 동치류), 비용 = 레일 전류, bin 해상도 = LUT 격자가 만드는 gain 분해능(계산), L 격자 = LUT 실측 앵커(외삽 금지 R3) | 아니오 |
| P7b-04 | 7b | 4 | DoD "3층 할당 결과를 **다른 모델** 전수탐색과 대조"(plan:392, 1521) | "다른 모델"의 정의, 범위(격자 크기·회로), 일치 허용오차가 없다 | 부분: audit/review_D:47-49 사례18(같은 대리 모델 비교 금지) | 다른 모델 = 전체회로 MNA를 목적/제약으로 쓰는 축소 격자 전수(파일럿 + 1회로), 일치 = 최적 목적값 차 ≤ 격자 분해능 | 아니오 |
| P7b-05 | 7b | 6 | G5 "(CL, GBW, PM) -> (Cc, Rz, gm_i)"(plan:1513) -- `folded_cascode`는 `compensation: null`(plan:820 G1 미해결) | 단일단 회로에서 gm 출처가 없어 G5가 정의되지 않는다 | 없음 | 기본안: 보상 없음 = 지배 pole이 출력노드 → `gm_1 = 2π·GBW·CL`(부하 선언)로 1급 케이스 | **예**(회로 해석 -- 공동분석 원칙) |
| P7b-06 | 7b | 1 | 3단 NMCNR 보상 DOF·`Rz=1/gm2`(plan:821 G2), class-AB 정지전류 `kvl_battery_loop`(plan:822 G4) | 보상 레지스트리 함수는 있으나(SR:1469-1476) DOF 계수기·ID_source 타입이 없다 | 부분: plan:821-822 | 보상 함수별 `solves_for`/`gm_refs`를 stage 수에서 유도하는 규칙 + ID_source 타입 열거(kcl / ideal_source_ref / kvl_battery_loop) | J3는 **예** |
| P7b-07 | 7b | 2,5 | 면적 제약형(A08, plan:263), `Area_i` 정의 미결(A2, plan:818), 면적 예산 미선언 시 Pareto 후 정지(A09, plan:264) -- 파일럿에 area 제약 없음 | 7b 파이프라인이 파일럿에서 Pareto로 정지하므로 DoD "파일럿 wall-clock ≤5분"(plan:392)과 할당 결과 대조가 성립하지 않는다 | 부분: history:1655-1660 | Area 정의(Σ W·L + 수동소자, 레이아웃 면적과의 관계)와 파일럿 면적 예산 값 | **예**(Area 정의·파일럿 면적 예산은 사용자 spec) |
| P7b-08 | 7b | 3 | `gain_budget_db_override` "사람 선언 필드로 존치할지 명시"(plan:448) | §15.4 사람 선언 목록(plan:1495)에 없어 스키마에 넣을지 모른다 | 부분: plan:535(v3.1 "특정 배분 강제는 override로만") | 존치 + G0 출처 필수 적용(출처 없으면 로드 거부) | 아니오(v3.1 확정 + G0 원칙) |
| P7b-09 | 7b | 2 | 중층 "공유 VGS는 gain 기준(B19')"(plan:1514) -- "pmos:Vcmfb 그룹은 gain 폭 0dB라 기준 미정"(plan:273) | gain이 무감한 결합변수의 좌표강하 선택 규칙이 없다 | 없음 | 기본안: gain 폭이 분해능 이하면 목적함수(전력) 기준으로 선택하고 그 사실을 기록 | **예**(B19'는 사용자 확정 규칙의 예외 처리) |
| P7b-10 | 7b | 5 | `value_amp` 선언 시 ID_ref 고정 입력(A15, plan:270; §7.0 plan:442) + theta `r_biasgen` 공존(plan:815) | 7b에서 theta를 제거하는지, 선언 전류와 theta가 둘 다 있을 때 무엇이 이기는지 불명 | 부분: A15 "값이 있으면 그 값을 실제 전류로"(사용자 확정) | 로드 게이트: `value_amp` 선언 + 같은 소스를 움직이는 theta 존재 = 로드 거부(중복 writer, C-a) | 아니오(A15) |

### Phase 7c -- S3 아카이브·전역 샘플 + SPICE 독립 검증

| # | Phase | 범주 | 모호한 곳 | 막히는 이유 | 답이 이미 있나 | 해소안 | 사용자 결정? |
|---|---|---|---|---|---|---|---|
| P7c-01 | 7c | 2 | SPICE "허용오차는 사전 계산 A9"(plan:1517, 393, 825) | 무엇을 비교하는지(.op 노드전압, 소자 ID, AC gain dB)와 계산식이 없다. LUT가 같은 sky130 모델에서 생성됐다면 기대 오차원은 보간 오차 + LUT에 없는 Cdb/Csb(plan:763-767)뿐 | 부분: audit/review_B:15, 61("D2식 계산으로 사전 고정") | 비교량 3종 + 허용오차 = D2 tol_V(노드), tol_V·gm 전파(ID), AC gain은 노드 tol을 소신호 감도로 전파한 값. 접합용량 누락 노드는 비교 제외가 아니라 별도 열로 보고 | 아니오 |
| P7c-02 | 7c | 1 | SPICE 인프라: `build_transient_netlist.py` 없음(audit/review_B:15), `cross_check_with_spice` def 0(plan:1133) | 넷리스트 생성기 입력(S1+S2), sky130 모델 파일 경로, ngspice 실행 방법(`C:\ngspice\Spice64\bin\ngspice_con.exe -b`, 프로젝트 CLAUDE.md), two_stage·nmcnr `passive_elements` 누락(plan:1489)이 계획에 없다 | 부분: fpga/CLAUDE.md ngspice 절 | 인터페이스: `write_spice_netlist(S1, S2, models) -> path`, `run_ngspice_op_ac(path) -> {nodes, ids, ac}`; 모델 경로는 LUT 생성 메타에서 읽음(`sky130_lut_sweep.py` 기록) | 아니오 (모델 파일 존재 여부는 환경 확인) |
| P7c-03 | 7c | 1 | S3 "평가 아카이브(θ 전체, ok/fail, metric, 제약 여유, 실패 분류+막은 소자+margin, 분지 id), 실행 기록, 조각, 유도 임계값", 디스크(plan:1046) | 파일 형식, 위치, 크기 상한, 동시 쓰기, 지문 불일치 시 처리(C-d "없음") 구현 규약이 없다 | 부분: plan:1046, 1058 | 형식 = 지문별 디렉터리의 JSON Lines(append-only, 케이스마다 flush -- 메모리 "결과를 파일에"), 상한 = 지문당 최근 N 실행(N은 D4 예산에서), 불일치 지문 디렉터리는 읽지 않음 | 아니오 |
| P7c-04 | 7c | 2 | D4 "wall-clock ≤5분 안에서 평가 1회 실측 시간으로 샘플 수를 계산"(plan:1101), "Sobol/LHS, 1,000점 × 72ms ≈ 72초"(plan:1069) | 식에서 빼야 할 고정 비용(presolve 16.5s history:573, DP, 좌표강하, SLSQP polish)과 t_eval 측정법, Sobol/LHS 중 선택, `scipy.stats.qmc` 가용성이 없다 | 부분: history:563-609 | N = floor((300 s − T_fixed_measured) / t_eval_median), T_fixed = 같은 실행의 비샘플 단계 실측 합, Sobol(`scipy.stats.qmc.Sobol`, scipy는 SLSQP로 이미 의존) | 아니오 |
| P7c-05 | 7c | 2 | "조각 지도를 그린 뒤 서로 다른 분지에서 SLSQP"(plan:1069) | "분지" 판정(실현가능 점 군집? DP 분지 id?)과 분지 수가 없다 | 없음 | 분지 = feasible 샘플의 θ 공간 연결성분(격자 인접 기준) 또는 DP 결정 벡터가 다른 해, 시작점 수 = 선언 `n_starts` | 아니오 |
| P7c-06 | 7c | 4 | DoD "S3 아카이브 재사용 실측"(plan:393) | 통과 기준이 없다 | 없음 | 기준 = 같은 지문 재실행에서 아카이브 적중 수 > 0 이고 결과 θ*가 첫 실행 이상(목적값) -- 수치 개선은 보고만 | 아니오 |
| P7c-07 | 7c | 4,5 | DoD "§3.3 C1~C10 강제 test 전원 PASS"(plan:393) -- C 테스트는 T7로 각 Phase에 흩어짐(plan:1243), C1 `< tol`(plan:214)의 tol 미정 | 어느 Phase가 어느 C를 PASS시키는지 없다. XFAIL은 "만료일 필수, 만료되면 FAIL"(plan:1355) -- 7c까지의 만료일을 무엇으로 쓰나 | 없음 | C × Phase 표(C1·C2·C9 -> 6b, C3 -> 1, C4·C8 -> 6a/6c, C5 -> 0.5(lint), C6 -> 6c, C7 -> 각 Phase, C10 -> 6b). XFAIL 만료 = 담당 Phase DoD 시점. C1 tol = D2 tol_V | 아니오 |
| P7c-08 | 7c | 1 | `verified_by` "독립 대조 스크립트 경로+오차"(audit/review_D:63) | 필드 형식·보관 위치·재검증 주기(metric 코드 해시 변경 시?)가 없다 | 부분: audit/review_D:63 | `verified_by{script, oracle_kind(a~d), max_error, metric_code_hash, date}`; metric 코드 해시가 바뀌면 자동 무효(C-d) | 아니오 |

---

## 2. 용어집 초안

| 용어 | 정의 | 출처 위치 |
|---|---|---|
| gain-budget-first | "gain이 gm을 정한다"가 아니라 stage별 gain 예산을 엔진이 **유도해 산출**한다. 총 gain은 제약 하나로만 입력 | plan:528-530(§7.4), A04 plan:259 |
| 보상 먼저(인과) | (CL, GBW, PM) -> (Cc, Rz, gm_1..N)를 먼저 한 번에 결정, 이후 gm_id_i·L(동치류)·자유 노드전압이 자유 축 | plan:517-526, §7.0 plan:441, G5 plan:1513 |
| Circuit State Graph(CSG) | 그래프 + 네 계약(C-a~C-d) + 평가 커널 + 탐색 기억 | plan:1033-1035 |
| S0 지문 | topology 정규화 해시, LUT 내용+메타 해시, spec 전체 해시, 유도 규칙 코드 해시 | plan:1041 |
| S1 구조 | 넷(노드)·소자/수동/이상소스(엣지)·타입 있는 관계 엣지, 개념당 정의 하나, 유도 사실에 status+증거 | plan:1042 |
| S1v 여기 뷰 | (excite, sense) 모드별 SCC 응축 신호 DAG + 피드백 엣지·극성 + stage_index + role_in_stage | plan:1043 |
| DM 뷰 | 대칭 net 대응으로 만든 차동모드 반회로 뷰. 자기대응 넷 = 가상접지 | plan:1479, probe:3, :16 |
| R2 규칙(stage 분할) | gate→drain 엣지 통과 시 stage+1, source→drain(캐스코드) 0, diode 노드 게이트의 gate→drain 0(미러), 출력노드 부하·공유 소스 tail 분류. 채택은 R3(DM/R2) | plan:1479-1481, probe:3, :593-644 |
| 교류접지 집합 | G1 레일 / G2 gate-only 비구동 넷(입력·수동·이상원 단자 아님) / G3 이상 전압원 단자 | probe:10-12 (plan:1485는 일부만) |
| 고임피던스 노드 | 드레인만 붙은 노드(소스가 붙은 노드는 1/(gm+gds) 저임피던스). stage 출력 경계 후보. 접합용량이 없어 용량을 못 세면 `undetermined` 명시 실패 | plan:763-767, audit/review_B:161 |
| S2 동작점 | 노드 DC 전압(경로별 값·충돌), 소자 op, KCL 전류, 스택 배분, 노드 cap/G, metric. 필드마다 {writer, input_version}. 키 = 계산 블록 입력 내용 해시, 상한 LRU | plan:1044 |
| S2p 사전정보 | 직전 수렴 스냅샷. 초기값·시드로만, 결과값으로 금지 | plan:1045 |
| S3 탐색 기억 | 평가 아카이브(실패 포함)·실행 기록·실현가능 조각·유도 임계값. 키 = S0 전체, 디스크 | plan:1046 |
| C-a 단일 writer | 필드×writer 티어 권한표, 타입 setter만, 원시 대입 grep 금지, `proposed`는 평가 경로가 못 읽음 | plan:1055 |
| C-b 버전 있는 유도 | 파생 필드가 입력 버전을 기록, 봉인 게이트가 불일치 거부 | plan:1056 |
| C-c 순환 = 명시적 고정점 | 유도 DAG의 SCC를 블록 단위 반복, 수렴 판정·반복 상한·비수렴 시 잔차 포함 예외 | plan:1057 |
| C-d 내용 지문 무효화 | 지문 불일치 = 없음(노트 후 사용 금지) | plan:1058 |
| D1 노드전압 정본 | 노드전압이 DC 1차 사실, vds/vgs/vsb는 차이로 유도 | plan:1098 |
| D2 순환 허용오차 | LUT VDS 격자 간격·보간 오차에서 계산(식은 Phase 6 design) | plan:1099 |
| writer 티어(W0~W4 제안) | T0 레일 / T1 구조 항등(diode, 노드 공유 병합) / T2 물리 종속 블록 / T3 선언된 노드전압 목표 / T4 자유 노드(배분기). "먼저 쓴 값 존중" 폐기 | plan:1498 |
| 봉인 게이트 | metric 계산 전 스냅샷 검사: KVL 합·KCL 잔차·노드전압 충돌·버전 일치(+VGS 정합 추가 제안) | plan:1515, plan:1056 |
| signal stage | S1v DM 뷰 R2로 유도된 stage: {input, cascode, load, tail, 출력노드, G_out 기여 소자 전부} | plan:1510 |
| G_out | stage 출력노드에 붙은 소자 gds 합(캐스코드는 곱 부스트). stage gain = gm_in / G_out | plan:148, plan:1497 |
| 결합 블록(coupling block) | (제안 정의) S1v signal stage 단위 블록. plan:1511의 "연결성분" 정의와 충돌 -- P6c-01 | audit/review_B:109 |
| 결합변수 y | 둘 이상 블록에 걸친 관계의 상태: K1 경계 부하 소자 상태, K2 공유 VGS 동치류, K3/K4 공유 스택 노드전압 | plan:1511, audit/review_B:111-115 |
| K1~K7 | stage 경계를 넘는 결합 종류(K1 출력노드 부하, K2 공유 VGS, K3 적층 vsb, K4 공유 스택, K5 다음단 Cgg->PM, K6 보상 gm, K7 비단조-국소) | audit/review_B:95-103, plan:1502 |
| A_i,max | 블록 i가 낼 수 있는 최대 gain(부하 gds 포함, LUT 격자 전수) | plan:1512, audit/review_B:142 |
| DOF 진단 | 구조 DOF(등식만 rank) + θ 표본 Jacobian 수치 rank. 결과 ok/underdetermined/overconstrained | plan:1501, history:1328 |
| 3층 할당 | 내층 y 고정 블록 DP(gm_id×L) / 중층 y 좌표강하(공유 VGS는 gain 기준) / 외층 SLSQP polish + MT3 전역 게이트 | plan:1514, audit/review_B:121-134 |
| metric 티어(MT1~MT3 제안) | T1 stage-local / T2 stage-분해가능 / T3 기약 전역 | history:669-673, plan:1500 |
| 감도 게이트 | 분해(대리) metric 변화 0인데 전체회로 MNA 값이 변하면 오류, 괴리 매 평가 기록 | plan:1516, audit/review_D:34 |
| 결합 잔차 | 블록 gain 합 대 전체회로 gain 차 | plan:1526, audit/review_B:119 |
| `verified_by` | metric 등록 시 독립 대조 스크립트 경로+오차 | plan:1517, audit/review_D:63 |
| status 상태값 | declared / derived / proposed / review_needed / ratified -- 두 벌로 흩어짐(P6a-06) | plan:1042, plan:1495 |
| review_needed | 증거 없는 유도·선언 불일치 표시, 파이프라인 정지 조건(C8) | plan:221, plan:1510 |
| ratified | 공동분석으로 사용자가 확정한 유도 사실 | plan:1510 |
| shadow 모드 | 새 유도 결과를 기존 경로와 매 실행 대조만 하고 동작은 바꾸지 않는 모드 | plan:1551 |
| 공동분석(J1~J9) | 회로 해석이 걸린 항목을 사용자와 함께 확정 | plan:1531-1543 |
| test 분리 단계(TS0~TS7 제안) | T0 숨은 FAIL / T1 기계적 이관 / T2 pytest화 / T3 print 판정 제거 / T4 자기참조 기대값 제거 / T5 baseline 퇴역 / T6 probe 정리 / T7 계약 test | plan:1236-1243 |
| 역할 4권한 | 의도(사용자+오케스트레이터) / 구현(gmid-code-author) / 판정 기준(gmid-test-author) / 판정 실행+보고 수치(gmid-verification-auditor) | plan:1317-1322 |
| 오케스트레이터 | 메인 세션. 라우팅·spec card·계획/기록 문서만 쓴다 | plan:1324, D11 plan:1437 |
| spec card | 변경 1건의 의도·관찰 가능한 계약·oracle 출처·거부 입력·결정 필요 항목 | plan:1334-1335 |
| interface card | 기계적으로 뽑은 시그니처 + spec card. test-author의 유일한 구현 정보 | plan:1371, D12 plan:1438 |
| red -> freeze -> green -> audit -> merge | 변경 1건의 흐름 | plan:1331-1345 |
| oracle 4종 | (a) 물리 불변식·손계산 (b) 다른 방법 참조구현 (c) known-good(SPICE, 결함 전 커밋) (d) spec card 사용자 값 | plan:1347-1352 |
| 기준 약화 | assert 삭제, 허용오차 확대, skip/xfail, 기대값 리터럴 변경, 픽스처 입력 이동, 격자 확대, 단정을 조건문 아래로 -- 매 건 사용자 승인 | plan:1353-1354, D14 plan:1440 |
| L1~L4 | 도구 호출 전 hook / 호출 후·SubagentStop hook / pre-commit 게이트 / merge gate | plan:1362-1367 |
| A1~A10 | auditor 검사 스크립트 목록 | plan:1377-1388 |
| 은폐 유형(CT1~CT11 제안) | 판정 없는 test ~ 공유 산출물 의존 | plan:1292-1304 |
| R0/R1/R2/D/DUP | 레지스트리 등급: 그대로 재사용 / 국소 수정 / §12로 대체 / 운영 호출 0 / 중복 | plan:1120, reg:13-18 |
| 운영 경로 | `run_harness` -> `optimize_full_circuit_budget` -> `_evaluate`(Phase 3 뒤 `run_gmid_design_pipeline`) | plan:1119, plan:1192 |
| 무동작 증명 | (정의 없음 -- X04 제안: 기능 발동 계수 0 + 산출물 전후 동일) | plan:378 |

---

## 3. design 문서 목록 초안

경로 관례: `docs/02-design/features/gain-budget-gmid-sizing.<phase>-<slug>.design.md`(저장소 기존 `docs/02-design/features/*.design.md` 관례). spec card는 `docs/02-design/specs/<id>.spec.md`.

| Phase | design 문서 | 반드시 담아야 할 절 |
|---|---|---|
| 공통 | `gain-budget-gmid-sizing.00-common.design.md` | 용어집(§2 확정본) / 공통 실패 타입표(X12) / 판정 기록 스키마(X13) / 승인 기록 형식(X14) / Phase × A1~A10 활성표(X06) / Phase × C1~C10 표(P7c-07) / 벤치 조건(X05) / 4회로 무동작 판정(X04) / design 문서·spec card 관계(X02) |
| 0.5 | `...05-role-separation.design.md` | 역할×경로 glob 표(P05-01, 02) / hook 입력 실측 절차와 대체 분기(P05-03) / hook·git 게이트 설치 경로(P05-04, 05) / 트레일러·경로 분류 규칙(P05-06, 07) / A3~A7 판정 규칙(P05-08~12) / interface card·spec card·disputes 양식(P05-13, 14) / 부트스트랩 순서(P05-15) / 공격 시나리오 10 + 과거 사례 7 재생표(P05-16) / worktree 오케스트레이션 시퀀스(P05-17) / L2 무시 목록(P05-18) / RTL 무동작 판정(P05-19) / A10 보고 수치 경로(P05-20) / agents 3개 frontmatter·check_agents 통과 확인 |
| 1 | `...10-test-separation.design.md` | T0 Test 16 spec card / TS 단계별 Phase 배정(P1-01) / legacy 디렉터리 수명·전후 stdout 대조법(P1-03) / 셔플 자체 구현(P1-04) / conftest fixture 규칙(P1-05) / 두 역할 커밋 순서(P1-06) / T3 lint 범위(P1-07) / slow 판정(P1-08) |
| 2 | `...20-dead-code-dup.design.md` | D7 제안표 열(P2-01) / DUP 차등 test 방식(P2-02) / Phase 2·4·7a 통합 대상 분할표(P2-03) |
| 3 | `...30-module-split.design.md` | 함수→모듈 이관표(레지스트리 목적지 열에서 생성)·계산된 의존 그래프(P3-01) / import 계층 게이트(P3-02) / 이동 무변경 AST 증명(P3-03) / shim 명시 재수출(P3-04) / 호출부 갱신 범위(P3-05) / 정본 spec 위치(P3-06) |
| 4 | `...40-defect-fixes.design.md` | 결함 #1~21별 red 형태·수정 범위표(P4-04) / 구조화 실패 도입(P4-01) / #1·#2와 6b 경계·D2 함수 선도입(P4-02) / #8 fixture·정본 구분(P4-03) / D8 핵심 3개 공동분석 대조표(P4-05) / `fallback_events` 스키마(P4-06) / D6 비교표·묶음 승인(P4-07) / #10 비단조 처리(P4-08) / exit code(P4-09) |
| 5 | `...50-failure-cache-theta.design.md` | 실패 캐시 키·분류·margin(P5-01) / start 선별 규칙(P5-02) / S3 레코드 스키마 v1·위치(P5-03, X07) / 계수기와 DoD 측정(P5-04) |
| 6a | `...6a-structure-stage-partition.design.md` | S0 해시 구성·정규화(P6a-02) / S1 노드·엣지·관계 엣지 스키마(P6a-01) / 교류접지 3분류(P6a-05) / DM 뷰 구성·R3(DM/R2) 알고리즘 명세(P6a-03) / 모드 수집(P6a-10) / 피드백 극성 규칙(P6a-11) / status 상태 전이표·저장 파일(P6a-06) / shadow 대조 보고·정지 시점(P6a-07) / 출력노드·G_out 대조 DoD(P6a-04) / ports 제안표(P6a-08) / J 항목별 결론 기록 양식·소비 Phase(P6a-09) / 정본 함수 매핑(P6a-12) |
| 6b | `...6b-node-voltage-seal.design.md` | S2 필드 스키마 / writer 권한표·W3 소스(P6b-03) / 유도 DAG·계산 블록 입출력 선언(P6b-04, X08) / D2 식·반복 상한 유도(P6b-02) / 봉인 항목·임계값(VGS 정합 포함)(P6b-01) / 버전 표현(P6b-09) / S2 LRU 상한 유도(P6b-08) / 순서 섞기 대상·판정(P6b-05) / shadow 동등 범위(P6b-07) / 봉인 위반 실패 규약(P6b-06) |
| 6c | `...6c-coupling-achievability-dof.design.md` | 결합 블록·y 정의(review_B 채택)(P6c-01) / 결합 잔차 측정(P6c-08) / A_i,max 정의·VDS 범위(P6c-02) / 제약별 저비용 상한 범위(P6c-06) / DOF 변수·방정식표·수치 rank 규칙(P6c-03, 04) / LUT 곡선 검사→해법 매핑(P6c-05) / 정지 보고 형식 / 달성 불가 픽스처 oracle(P6c-07) |
| 7a | `...7a-gain-metric-sensitivity.design.md` | 회로별 gain metric 이관표(P7a-03) / 분해식(P7a-01) / 감도 게이트 판정(P7a-02) / MT1~3 자동 분류 규칙(P7a-05) / `verified_by` 적용 순서(P7a-06) / B21 픽스처(P7a-07) / bisect 모드 배치(X09) / 착수 조건 정리(P7a-04) |
| 7b | `...7b-compensation-allocation-spec.design.md` | `sizing_spec.json` v5 스키마·로더·4회로 이관·topology.json 필드 제거(P7b-01, 08, 10) / G5 보상 규약(단일단·3단·class-AB)(P7b-05, 06) / 내층 DP 명세(P7b-03) / 중층 좌표강하 종료·예외 규칙(P7b-02, 09) / 외층 polish / Area 정의·Pareto 정지(P7b-07) / 다른 모델 대조 test(P7b-04) |
| 7c | `...7c-archive-spice.design.md` | S3 저장 형식·상한·지문 처리(P7c-03) / D4 샘플 수 식·Sobol(P7c-04) / 분지 판정(P7c-05) / SPICE 넷리스트 생성·실행 인터페이스(P7c-02) / 비교량·허용오차 계산(P7c-01) / `verified_by` 형식(P7c-08) / DoD 기준(P7c-06, 07) |
