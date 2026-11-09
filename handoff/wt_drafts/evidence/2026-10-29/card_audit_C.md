# card 감사 C -- 20261021 card 12개 + `_TEMPLATE.spec.md` + 작성 필요 card 목록

- 감사자: card 감사자(묶음 C), 2026-10-29. 감사만 했다(문서·git 쓰기 0, 이 결과 파일만 씀).
- 판단 기준(승인된 것만): master 계획 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` **v6.38.4**(머리 `version: 6.38.4`, 승인 O-173), 결정 O-173~O-181, `chip-design-skills/CLAUDE.md` 원칙 1~33(원칙 2 = O-178·O-179 개정판, master 병합 0901dd0e·4a0b6323), 상위 `fpga/CLAUDE.md` '★graph 단일 정본'.
- **사실 정정(브리핑 전제와 다름)**: master design은 **v1.14.2**(`docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md:3` `version: 1.14.2`, 40도 같음, `plan_version: 6.37`)다. v1.15.x(v1.15.3, `plan_version: 6.38.4`)는 미병합 브랜치 `design/v115`(master 대비 30커밋)에만 있고 승인 기록이 없다(`user_decisions.md` O-167은 '착수'만). 그래서 대체된 card의 **재동결은 design v1.15.x 승인 뒤**로 분류했다.
- 승인 전 `plan/v6385`(v6.38.5, 25커밋 '검증 대기')에 기대는 개정 = '개정 대기'. 해당 커밋: `df197966`(ME-1 → CL-1, PW-1b 삭제, e_m 문언 정리), `252d471c`(held-out 0·library 13 문언, IT-1·CPG-1·DR-1 문언).
- 엔진 코드는 읽지 않았다. card 본문 안 엔진 줄 인용은 원칙 8에 따라 판정 근거로 쓰지 않았다(재작성 범위 기록으로만 취급).

## 1. 상태 실측(git 읽기만)

| card | 판정 기록 | 결과 | master 병합 |
|---|---|---|---|
| it0-baseline | `integ/it12:.ai/verification/20261021-it0-baseline.json` (base `c237d96e`, code null) | V2·V4 PASS, 나머지 N/A | 미병합 |
| it1-input-tie-removal | `integ/it12:.ai/verification/20261021-it1-input-tie-removal.json` (code `14e0ca2a`) | V1·V2·V4~V7·V9·V10 PASS | 미병합 |
| it2a-snapshot-derive | `integ/it12:...it2a-snapshot-derive.json` (code `bddef887`) | PASS(V3·V8 N/A) | 미병합 |
| it2b-kernel-window | `integ/it12:...it2b-kernel-window.json` (code `431d2e7b`, merge `6afe4758`) | V1~V10 PASS(V3 N/A) | 미병합 |
| it2c-icm-config | 없음 | 미구현. 재동결 진행본 `card/it2c` `d95c8ff8`(계획 v6.37·design v1.14.1 기준) | -- |
| it2d-refine-front | 없음 | 미구현 | -- |

- master의 it2a·it2b·it2-common 사본은 **판정 전 동결본**이다: `git diff --stat master integ/it12 -- docs/02-design/specs/`는 common 54줄, it2a spec 12·interface 9, it2b spec 49·interface 30줄 차이를 보인다(판정본 = `integ/it12`; 예: it2a approval 줄 `20261022-it2a-seal-signature-ext, 20261022-it2a-o94-ext` 추가, it2b `Window` 칸 다섯·helper 이동 없음·(S4-나) 확정). it0 card는 두 쪽이 같다.
- `cards/simplify`(merge `07964dfe`, 커밋 `1451b1da`)는 이 묶음에서 7파일(it1 둘·it2c 둘·it2d 둘·common)에 표지를 달았다. it0·it2a·it2b(5파일)에는 상태 표지가 없다.

## 2. `cards/simplify` 표지 -- 무엇으로 대체됐나(현행 v6.38.4 기준 재확인)

| 표지 대상 | 대체한 것(현행 계획) | 표지 문언의 정확성 |
|---|---|---|
| IT-1 spec·interface | N6.5 'IT-1 범위 재작성(v6.38.3, O-168·DEC-106)'(plan:1537~): 범위 1 유지, 범위 2~4 → DEC-106 입력 공통모드 변수 하나, 범위 5 = g = s 한 규칙(N6.35 E-19), **범위 6 = B4 S1v 파생 술어(승인 O-173 P9-M1a, plan:1552·1562 완료 7)**, + card 0 IT-0b(plan:1557) | 낡음: '현행 계획 v6.38.3', 'v6.38.4(승인 전)…범위 6 승인 대기 P9-M1a…재동결 범위는 그 승인 뒤' -- v6.38.4는 O-173으로 승인됐고 범위 6은 확정됐다. '검증 대기'도 낡음(검증 10 병합 가능 판정 뒤 병합 `07964dfe`) |
| IT-2c spec·interface | N6.6 범위 1·6(plan:1589·1594): servo 측정 구성(O-115), 전도 행 R0·F 성분 함께 구동(O-118), `graph.ss_circuit` writer 하나(v6.34.1), O-109 D1·D2·D4, **E-09·E-22**(plan:1594 '6. 예외 정리(v6.38.3 -- N6.35 E-09·E-22)'), 착수 실측 (a) servo 피벗 a_e·δA_num (b) A = 0 사례(옛 (c) vntol·reltol은 v6.38.4 `67e7b182`가 뺌, plan:1598) | **틀림 1곳**: 'θ 프레임 창 = KVL 순서 창(E-13)'을 IT-2c 변경으로 적었으나 E-13 소유 card = **WB-1 범위 3a-0·3a**(plan N6.35 E-13 행 소유 칸). 낡음: '검증 대기', v6.38.4 착수 실측 (c) 삭제 미반영 |
| IT-2d spec·interface | N6.6 'IT-2d -- B77'(plan:1598 '**IT-2d 범위 = front·보고가 `node.dc_window_cfg` 값을 쓰는 배선과 옛 입력 창 계산(`ls_swing`) 삭제·`metrics_aux` 배선, 그리고 B77 … 뿐**', '다듬은 창·front 전용 블록은 만들지 않는다(C1 -- 정확도 대조는 oracle `.dc` 몫)') | 맞음. 낡음은 '검증 대기'뿐. 원칙 2(O-178: 엔진 가드 없음·front 최종 oracle)와 현행 범위가 일치 |
| IT-2 공통 (2) | IT-2c·IT-2d 위와 같음 | 같은 E-13 오귀속, '현행 계획 v6.38.3', '검증 대기' |
| IT-2 공통 (3) | card IT-2e(N6.6 범위 5, O-96, plan:1593) -- card 문서 없음 | 맞음 |

## 3. card별 판정

판정 어휘: 그대로 / 상태 표지 / 내용 개정 / 대체됨 표지 / 개정 대기. 본문(동결 기록)은 O-169에 따라 덧대지 않는다 -- 아래 제안은 모두 **표지 블록과 변경 이력 한 줄**만 고친다(원칙 8·29: Edit/Write로, heredoc 금지).

### 3.1 `20261021-it0-baseline.spec.md` -- 상태 표지

- 상태: **완료 이력**(IT-0 측정 PASS, `integ/it12`, master 미병합). master 사본 = 판정한 판과 같음.
- 문제: 표지 없음 → 미착수 card처럼 읽힌다. 본문의 heldout 4회로(29·76·130·134행)는 O-181로 library 이관됨(기록이라 본문 불변). 93행 'IT-2c 착수 실측 (c)'는 v6.38.4 `67e7b182`로 착수 조건에서 빠짐.
- 제안(6행 `---` 다음 줄에 삽입):
  > **[상태 표지 2026-10-29] 완료 이력** -- card 0 IT-0 측정 완료(판정 기록 `integ/it12:.ai/verification/20261021-it0-baseline.json`, base `c237d96e`, V2·V4 PASS·나머지 N/A), master 미병합(IT-1 + IT-2 통합 병합 때 함께 들어감). 현행 계획의 후속 측정은 card 0 **IT-0b**(계획 v6.38.4 N6.5 'IT-1 범위 재작성' 완료 조건 2 -- spec card 미작성). 본문의 heldout 4회로는 O-181로 library로 옮겨졌고, 'IT-2c 착수 실측 (c)'는 계획 v6.38.4가 착수 조건에서 뺐다 -- 본문은 동결 기록이며 덧대지 않는다(O-169).
  + 끝에 `## 변경 이력` 절과 한 줄(표지만 더함, 본문 불변).
- 원칙 점검: 원칙 16·O-181 -- 기록에 대한 표지라 held-out 사용 문제 없음. IT-0b 작성 때 '9회로'는 library 13(O-181)로 -- 계획 문언은 v6.38.5 `252d471c` 대기 → **개정 대기**(IT-0b 쪽).
- 근거: plan:1557, 결정 O-181 행(user_decisions.md:1162), `67e7b182`.

### 3.2 `20261021-it1-input-tie-removal.spec.md`·`.interface.md` -- 상태 표지(문언 갱신) + 개정 대기

- 상태: 판정 PASS(`integ/it12`), 대체됨(재작성 범위), 재동결 필요.
- 고칠 줄: spec 9행·interface 3행 표지.
  - '[대체 표지 2026-10-29 -- 검증 대기]' → '[대체 표지 2026-10-29 -- 검증 10 병합 가능 판정, master `07964dfe`]'
  - '현행 계획 v6.38.3 N6.5' → '현행 계획 v6.38.4 N6.5'
  - 마지막 문장 '계획 v6.38.4(승인 전)는 … 범위 6(B4 S1v 파생 술어, 승인 대기 P9-M1a)을 더하는 안을 걸고 있어 재동결 범위는 그 승인 뒤 정한다.' →
    > 계획 v6.38.4(승인 O-173 P9-M1a)가 범위 6(B4 S1v 파생 술어, 완료 조건 7)을 더했다. 재동결 범위 = 범위 1 + 재작성 범위 2~5(DEC-106·E-19) + 범위 6, card 0 IT-0b 먼저. 재동결 착수 = design 41 §6.7-1a·40 §3.7 정정(design v1.15.x -- 미승인, master design = v1.14.2) 승인 뒤.
- 개정 대기(v6.38.5 승인 뒤): 재동결본의 코퍼스 문언(library 13, held-out 0 → A' 판정 정지 -- O-181 확정, 계획 문언 `252d471c` 대기), N6.3 판정 기준 문언(e_m 제거 -- O-178 확정, 계획 문언 `df197966` 대기).
- 원칙 점검: 원칙 8(본문의 as-built 줄 인용은 재작성 범위로만 남김 -- 표지 문언에 새 엔진 근거 없음), 원칙 9(범위 6 소비자 = 완료 7 (i) `net_model(` 호출 하나 -- plan:1562).
- 근거: plan:1537·1552·1557·1562, O-173 행(user_decisions.md:1154), `07964dfe`, design 41:3.

### 3.3 `20261021-it2-common.md` -- 내용 개정(표지 문언) + 개정 대기

- 상태: 혼합(IT-2a·2b = 완료 이력, IT-2c·2d = 대체됨, IT-2e = 문서 없음).
- 고칠 줄: 3행 표지.
  - '검증 대기' → 병합(`07964dfe`) 표기.
  - '(계획 v6.38.3 N6.6)' → '(계획 v6.38.4 N6.6)'.
  - 원인 목록의 '`E-13`' 삭제 → 별도 문장: 'θ 프레임 창 = KVL 순서 창(N6.35 E-13)은 IT-2c가 아니라 card WB-1 범위 3a-0·3a 몫이다(이 문서 IT-2b 몫 창 경로의 재작성 범위).'
  - 추가 문장(승인 결정 반영 지시, 본문 불변):
    > 재동결 때 지킬 것: (i) 'IT-2c 착수 실측 (c)' 삭제·(a) = servo 피벗 a_e(계획 v6.38.4 N6.6 순서) (ii) O-178 e_m 폐지 -- G6 출력 전용 선언의 `IcmWindow.model_error_ref`, '덮지 않는 것'의 ME-1 인용을 재동결본에 옮기지 않음 (iii) O-181 -- 'library 9 + heldout 4'는 library 13, held-out 0 동안 A' 일반성 판정 정지 (iv) 재동결 착수 = design v1.15.x 승인 뒤(master design 41 = v1.14.2).
- 개정 대기: (ii)·(iii)의 계획 문언(ME-1 → CL-1, 코퍼스 13)은 v6.38.5 승인 뒤 인용 번호만 바꿈.
- 원칙 점검: 원칙 2(O-178 -- 엔진 판정 가드·e_m 칸을 card에 다시 들이지 않음), 원칙 7(G1~G7 계약은 재동결본에서도 유지 -- 현행 N3.3 G0~G7로 이름 맞춤), 원칙 16·O-181.
- 근거: plan:1594(E-09·E-22), N6.35 E-13 행 소유 칸 'WB-1 범위 3a-0·3a', plan:1598, 이 파일 65·155행.

### 3.4 `20261021-it2a-snapshot-derive.spec.md`·`.interface.md` -- 상태 표지

- 상태: 완료 이력(PASS `integ/it12`). master 사본 = 판정 전 동결본.
- 제안(spec 7행 `---` 다음, interface 1행 제목 다음):
  > **[상태 표지 2026-10-29] 완료 이력** -- IT-2a 판정 PASS(`integ/it12:.ai/verification/20261021-it2a-snapshot-derive.json`, code `bddef887`), master 미병합. 이 master 사본은 판정 전 동결본이다 -- 판정한 판(approval `20261022-it2a-seal-signature-ext`·`20261022-it2a-o94-ext`, keep = base writer ∪ 봉인 4 호출 목록, L11 (d))은 `integ/it12`에 있고 통합 병합 때 그 판으로 바뀐다. 후속 = card IT-2e(계획 v6.38.4 N6.6 범위 5 -- 같은 집합식을 함수 하나로, spec card 미작성). 본문은 기록이며 덧대지 않는다(O-169).
- 원칙 점검: 원칙 7 규칙 5(스냅샷 파생)와 판정본 일치 -- 문제 없음.
- 근거: `git diff master integ/it12 -- …it2a…spec.md`(approval 줄·keep 정의), plan:1593.

### 3.5 `20261021-it2b-kernel-window.spec.md`·`.interface.md` -- 상태 표지

- 상태: 완료 이력(PASS `integ/it12`, merge `6afe4758`). master 사본 = 판정 전 동결본(`Window` 칸 여섯·`_helpers_dc_solve` 이동·op_mismatch 단언 -- 판정본에서 모두 바뀜).
- 제안(spec 7행 `---` 다음, interface 1행 제목 다음):
  > **[상태 표지 2026-10-29] 완료 이력** -- IT-2b 판정 PASS(`integ/it12:.ai/verification/20261021-it2b-kernel-window.json`, code `431d2e7b`), master 미병합. 이 master 사본은 판정 전 동결본이다(판정본 = `integ/it12`, design 41 v1.12.10 재동결: `Window` 칸 다섯, helper 이동 없음, (S4-나) 확정, 동작점 불일치 단언은 EO-1). 이 card 산출 가운데 `node.dc_output_structure`와 뿌리 아닌 입력 포트·선언 포트 `node.dc_window` 항목은 현행 IT-2c가 지우고(계획 v6.38.4 N6.35 E-09, O-109 D1), 입력 창 측정 되풀이 경로(`k_max`·`unmeasured`/`unsettled`)는 card WB-1 범위 3a가 KVL 순서 창으로 다시 쓴다(N6.35 E-13) -- 재작성 범위 기록. 본문은 덧대지 않는다(O-169).
- 원칙 점검: 원칙 8·O-169(완료 card 산출도 재작성 대상 -- 보존 근거로 쓰지 않음을 표지가 밝힘).
- 근거: `git diff master integ/it12 -- …it2b…`, plan:1594, N6.35 E-09·E-13 행.

### 3.6 `20261021-it2c-icm-config.spec.md`·`.interface.md` -- 내용 개정(표지 문언) + 개정 대기

- 상태: 미구현, 대체됨, 재동결 필요(진행본 `card/it2c` `d95c8ff8` = 계획 v6.37·design v1.14.1).
- 고칠 줄: spec 9행·interface 3행 표지.
  - '검증 대기' → 병합 표기.
  - '·θ 프레임 창 = KVL 순서 창(E-13)' 삭제(소유 = WB-1 범위 3a), '재동결본 … v6.38.3 E-09·E-22·E-13 반영 전' → 'E-09·E-22 반영 전'.
  - 추가: '계획 v6.38.4: 착수 실측 = (a) servo 피벗 a_e·δA_num (b) A = 0 대칭 사례; 옛 (c) 오라클 vntol·reltol은 엔진 착수 조건에서 뺌(`67e7b182`). 재동결 착수 = design v1.15.x 승인 뒤(master design 41 = v1.14.2).'
- 개정 대기(v6.38.5 승인 뒤 재동결 내용): e_m·model_error 인용 제거 문언(O-178 확정, 계획 `df197966`), library 13·A' 정지(O-181, `252d471c`). 열린 결정 가운데 Q-W1(실현 servo IT-2c 피벗 의존 -- v6.38.5 `426c98b7`)이 닫히기 전에는 IT-2c 피벗 칸 범위를 재동결본에서 확정하지 않는다.
- 원칙 점검: 원칙 2(측정 구성 창의 정확도 대조는 oracle 몫 -- 엔진 가드 칸 없음), 원칙 3·4(ICMR = DC 양, servo KCL), 원칙 7(`graph.ss_circuit` writer 하나), 원칙 9(E-09 삭제는 소비자 grep 0 완료 조건).
- 근거: plan:1589·1594·1598, N6.35 E-13 행.

### 3.7 `20261021-it2d-refine-front.spec.md`·`.interface.md` -- 상태 표지(작은 갱신) + 개정 대기

- 상태: 미구현, 대체됨(옛 범위 소멸, O-109 C1·O-115), 재동결 필요.
- 고칠 줄: spec 9행·interface 3행 -- '검증 대기' → 병합 표기, '현행 IT-2d 범위' 문장에 출처 'plan v6.38.4 N6.6 순서(1598행)' 표기, 끝에 '재동결 착수 = IT-2c 재동결·design v1.15.x 승인 뒤'.
- 대체 내용 정확성: 맞음(현행 범위 = front·보고 `node.dc_window_cfg` 배선, `ls_swing` 입력 창 삭제, `metrics_aux` 배선, B77). 원칙 2(O-178)와 일치 -- 다듬은 창·front 전용 블록 없음, 정확도 대조 = oracle `.dc`.
- 개정 대기: 코퍼스·e_m 문언(v6.38.5).
- 근거: plan:1598.

### 3.8 `_TEMPLATE.spec.md` -- 내용 개정

| 줄 | 지금 | 문제(원칙·계획) | 제안 문안 |
|---|---|---|---|
| 3 | `phase: <계획서 N6.1에서 읽은 Phase 순서의 원소>` | DEC-86으로 Phase 순서표는 history, N6.1에 Phase 열 없음(plan:1172 '옛 Phase 순서표(0~7c)… history로'); 20261021 card 전부 '해당 없음 (DEC-86 …)'을 씀 | `phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)` |
| 6~8 | `activated_ic_case`·`_rename`·`noop_activation_id` | 옛 엔진 IC gate 전용(N6.1 '0.5 역할 분리 인프라 폐기', 옛 test LT-1 삭제) | 본문에서 지우고 주석에 '옛 gate 전용 -- 새 엔진 card는 쓰지 않음'(파서 허용 키 목록은 그대로) |
| 40 | `grep -rn "glob(" A/tests/` | 옛 엔진 경로(`assets`) | `skills/analog-gmid-design/gmid_engine/tests/`(`E/tests/`) 기준, 구조 규칙 H 이름 충돌 |
| 42 | 'N3.12.2 쓰기 경로표' | N3.12는 기록(DEC-86); 현행 = N6.3 WP-13 + `.claude/agents/gmid-*.md` | '쓰기 경로: 코드 주체 ≠ test 주체(WP-13, N6.3), test 주체는 interface card만' |
| 44 | 'V7 면제 승인' | 원칙 9: 배선 안 되면 만들지 않음, 못 하면 사용자 승인(면제 gate 아님) | '미배선: 새·되살린 def·필드마다 운영 경로 호출자 ≥ 1. 배선할 수 없으면 만들지 않고 사용자 승인(원칙 9)' |
| 45 | `A/tests/contracts/` | 옛 경로 | `E/tests/structure`(규칙 A~I)·바뀌는 이름 grep |
| 46 | V3 `mutate_changed` | gate 꺼짐(DEC-86) | '해당 없음(DEC-86)' 또는 줄 삭제 |
| 47 | '다른 Phase의 일' | Phase 없음 | '다른 card 범위의 일' |
| (추가) 14 | -- | 원칙 7·fpga/CLAUDE.md 1~7, plan N3.3 G0~G7, N6.3 '같은 입력 재계산 0'(래칫) | 'graph 정본: 새·바뀐 필드마다 writer 하나·권한표 행 하나, 같은 입력 → 필드 하나(G0~G7), 새 cache·memo·sctx 슬롯·사본 0, 단계 사이 참조 전달; 같은 입력 재계산 래칫(새 B 0·자기 배정 B 해소)' |
| (추가) 15 | -- | 원칙 9·memory '그래프 계산값 소비' | '소비자: 새·바뀐 graph 필드마다 엔진 소비자 ≥ 1 또는 출력 전용 선언(표)' |
| (추가) 16 | -- | 원칙 8(O-153·O-165·O-169) | '엔진 인용 용도: card 안 엔진 줄 인용은 (1) 엔진 밖 사실 (2) 재작성 범위(지울·바꿀 코드·소비자)뿐 -- 자리·writer·판정 근거로 쓰지 않는다' |
| (추가) 17 | -- | 원칙 2(O-178·O-179), N6.3 변경 종류 표 | '판정 기준: 변경 종류(N6.3 표)와 E-0 물리 관문·정의 동일성; front 점 최종 합격 = oracle(닫기), SPICE 수치 동일성은 기준 아님, e_m·model_error 칸을 만들거나 읽지 않음; 주파수 손계산은 LUT C 열(O-179)' |
| (추가) 18 | -- | 원칙 11·12·16, O-181 | '값·일반성: 상수 출처(선언·PDK·LUT·spec) 표기, 회로 이름 코드 0, library 13 n/N 측정, held-out 0개 기간은 A′ 판정 정지 표기' |
| (추가) 절 | -- | 원칙 24·O-171 | `## 원래 취지와 다름` 절, '결정 필요 항목'마다 물리 결정자·식/원문·실측·판정 칸 |
| 54~55 주석 | '필드 목록의 정본은 계획서 N3.12.3' | N3.12는 기록 | '머리 키 형식 = `tools/gates/role_paths.py parse_spec_card`(형식 호환용), 절차 정본 = 계획 N6.3' |

- 개정 대기 부분: (추가) 17의 계획 인용 번호(N6.3 E-1·NFR-5 문언은 master v6.38.4에 아직 e_m가 남아 있음 -- plan:1308 'E-1 … e_m은 ME-1…') → v6.38.5 `df197966` 승인 뒤 인용 갱신. 문안 자체는 승인된 O-178·원칙 2만 인용하므로 지금 써도 된다.

## 4. 분류 집계(13파일)

| 판정 | 파일 수 | 파일 |
|---|---|---|
| 그대로 | 0 | -- |
| 상태 표지(새로 달기) | 5 | it0 spec, it2a spec·interface, it2b spec·interface |
| 상태 표지(기존 표지 문언 갱신) | 4 | it1 spec·interface, it2d spec·interface |
| 내용 개정(표지 문언 정정 -- E-13 오귀속 포함) | 4 | it2-common, it2c spec·interface, `_TEMPLATE.spec.md`(본문 개정) |
| 대체됨 표지(새로) | 0 | -- (필요한 곳엔 이미 있음) |
| 개정 대기(위와 겹침 -- v6.38.5·design v1.15.x 승인 뒤) | 9 | it1 ×2, it2c ×2, it2d ×2, common, it0(IT-0b 쪽), template(인용 번호) |

## 5. 작성 필요 card 목록(master 계획 v6.38.4 N6.x에 있고 spec card 파일 없음 -- 작성하지 않음)

`docs/02-design/specs/`에는 2026-09 옛 엔진 card와 20261021 IT card만 있다(`ls` 실측, `git ls-files '*spec.md'` 다른 자리 0).

**A. 새로 써야 할 card(30)**

| # | card | 절 | 비고(착수 조건 요지) |
|---|---|---|---|
| 1 | IT-0b (card 0) | N6.5 재작성 완료 2 | IT-1 재동결 앞, 코퍼스 문언 v6.38.5 대기 |
| 2 | IT-2e | N6.6 범위 5 | IT-2d 뒤, design 40 §2.4.7·41 4.7-3c |
| 3 | LT-1 | N6.4 | `legacy/` 아직 있음(미구현) |
| 4 | SH-1 | N6.7 | |
| 5 | DE-1 | N6.8 | WB-1·SF-1 뒤 |
| 6 | FX-1 | N6.9 | |
| 7 | NL-1 | N6.10 | UB-1과 같은 통합 병합 |
| 8 | DT-1 | N6.11 | B12 포함 |
| 9 | LI-1 | N6.12 | |
| 10 | LA-0 (card 0) | N6.14 | |
| 11 | LA-1 | N6.14 | |
| 12 | UB-0 (card 0) | N6.15 | |
| 13 | UB-1 | N6.15 | |
| 14 | LA2-0 (card 0) | N6.16 | 착수 조건이 ME-1·PW-1b에 걸림 → 개정 대기 |
| 15 | LA-2 | N6.16 | 같음 → 개정 대기 |
| 16 | PW-1a | N6.17 | |
| 17 | VB-1 | N6.18 | |
| 18 | EO-1 | N6.20 | |
| 19 | SD-1 | N6.21 | |
| 20 | NU-1 | N6.23 | |
| 21 | TN-1 | N6.26 | |
| 22 | GV-1 | N6.27 | |
| 23 | SF-1 | N6.28 | |
| 24 | TB-1 | N6.29 | |
| 25 | CMP-1 | N6.30 | 평가(게이트 아님) |
| 26 | SB-1 | N6.31 | |
| 27 | WB-1 | N6.32 | E-13 범위 3a 포함 |
| 28 | RS-1 | N6.33 | |
| 29 | CPG-1 | N6.34 | 게이트, 코퍼스 문언 v6.38.5 대기 |
| 30 | DR-1 | N6.36 | 규칙 근거 재수립(O-175) v6.38.5 대기 |

**B. 재동결(파일은 있음, 3)**: IT-1(+범위 6), IT-2c(진행본 `card/it2c` `d95c8ff8`), IT-2d -- 모두 design v1.15.x 승인 뒤.

**C. 작성 보류 -- 개정 대기(3)**: ME-1(N6.19 -- O-178이 폐지 결정, v6.38.5 `df197966`이 CL-1로 대체), PW-1b(N6.17 -- v6.38.5 삭제), AP-1(N6.22 -- 미래 card, 계획 개정 먼저).

**D. 작성 불요(3)**: PR-1(N6.13 철회), NB-1(N6.24 삭제), RB-1(N6.25 대상 소멸).

다른 계획 card(oracle OP-*, headroom-chain HC-*, graph-consumption GC-*, offset OS-*·TR-*)와 XRUN-F1 card C는 이 계획 N6.x 절이 아니라 범위 밖.

## 6. 자기 점검(원칙)

- 원칙 8: 엔진 소스 열람 0, 판정 근거는 계획·결정·git 기록만. 원칙 20: 사용자 결정 번호는 '무엇이 확정됐나' 사실로만 인용(근거 칸은 계획 줄).
- 원칙 7: 제안 문안에 새 칸·사본 없음(표지 = 판정 기록 경로 참조).
- 원칙 24 '원래 취지와 다름': 브리핑의 'master design v1.15.x' 전제가 사실과 다름(master = v1.14.2) -- 재동결 시점 판단이 이 사실에 달림.
- 원칙 29: 이 파일은 Write 도구로만 씀.
