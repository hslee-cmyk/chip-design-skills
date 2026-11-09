# Phase 3 완료 판정(DoD) -- auditor 브리핑 초안 (v4, 2026-10-06, 정합 기준 gate `master` `6c724de`; v3 `2183f2e`, v2 `fd4ef8c`, v1 `4a286f0`)

> **v4(2026-10-06, 정합 갱신 -- 판정 기준 불변)**: gate `master` `2183f2e` → `6c724de`(문서 커밋 1 -- b26pre spec card). design 30·계획·`tools/gates` 변경 0(`fd4ef8c..6c724de`) → §2 블록 sha256·줄 번호 그대로. 반영: kit `n63_p3.py` nomerge(사용자 승인, `review_nomerges.md` B·S 0) → §5 12행·§10 ③·§6·§7 관찰 3; D0a det4·det5 `--allow-changed` 의미 → §4 E6 행·§6 E6 거부 확인; D0a 계약 4 `import-dup` → §5 3행·§9-4·`judge_p3.py`; M10·T1 초안 id. `6c724de` 모래상자(`C:/g368`): `missing` 25, `N6.3 1 PASS(n=37) | 2 FAIL(2/20, 기록 없음 1) | 3 FAIL | 4 PASS(n=2) | 5 FAIL`, `merges_clean` []. 작성자 재실행 때 gate `master`는 `ae1b588`(b26pre spec card 개정 문서 커밋 1개 더, design 30·계획·`tools/gates` 변경 0) -- 같은 수치(§8.v4). 독립 검토 `_drafts/review_phase3_dod_refresh.md`(B 0·S 1·minor 8)의 S1·m1~m5·m7·m8 반영(m6은 T1 card 몫). kit: `judge_p3.py`(`CHK_KINDS` 11종·E2 ② '모든 목록'·`e6` 판정), `run_dod.sh` e6(거부 확인 실행 + 판정 줄); `n63_p3.py` 무수정. 작성자 재실행 §8.v4(`C:/g380`). 사본 `draft_phase3_dod.md.pre-v4.bak`, kit 사본 `phase3_dod_kit/{judge_p3.py,run_dod.sh}.pre-v4.bak`.

> **v4r(2026-10-07, 독립 검토 `_drafts/review_phase3_dod_v4.md`(B 0·S 1·minor 4) 반영 -- 판정 기준(design 30 §10) 불변)**: S1 E6 거부 확인을 '허용 두 id ⊆ `changed`(중복 없음)·두 id를 뺀 발견 = 허용 있는 실행'으로 좁히고 판정은 허용 있는 실행으로(진짜 E6 실패가 INVALID가 아니라 FAIL) -- §4 E6 행·§5 8행·§6 E6 거부 확인 행·`judge_p3.py e6`(검토 §3 (a)~(c) 문안); m-a 중복 id 거부(같은 조건); m-b `judge_p3.py`가 어떤 입력(인자 모자람·명령 모름·목록 아닌 값·`GC` 없음)에도 판정 줄을 남김(`main()`); m-c §9-4 단위 id 표기 확인 구절; m-d §8.v3 4번 문구(TREESAME). §8.v3 끝에 M10 모의 관찰(`check --card ALL`의 SD 4971행 MOD9 재수출 `order` 1 -- F2 전 상태, E6은 F2 뒤 최종 H에서 확인) 추가. 판정기 자체 시험 `phase3_dod_kit/judge_e6_selftest.py` 55/55(§8.v4r). 사본 `draft_phase3_dod.md.pre-v4r.bak`, `phase3_dod_kit/judge_p3.py.pre-v4r.bak`. `run_dod.sh` 동작 무수정(e6 거부 확인 주석만 v4r 조건으로 정정 -- v4s 검토 v4r n-4 문구 정정).

> **v4s(2026-10-07, 독립 검토 `_drafts/review_phase3_dod_v4r.md`(B 0·S 0·minor 4) 반영 -- 판정 기준(design 30 §10) 불변)**: n-1 E6 -- 허용 있는 실행이 이미 FAIL 모양(exit ≠ 0 또는 비지 않은 발견)이면 거부 확인 불성립이어도 `E6 FAIL`(삭제된 허용 id의 `lost` 등, 검토 V07), PASS 모양일 때만 불성립 → INVALID(공허 PASS 막기) -- §5 8행·§6 E6 거부 확인 행·`judge_p3.py e6`; 그래서 det3 모양(허용 있는 쪽에만 `lost`·`rebind`, 검토 v4 §3)도 INVALID가 아니라 FAIL로 돌아간다(어느 쪽도 PASS 아님). n-2 `e01` H·F2 base `findings`가 목록이 아니면 E1 INVALID(옛: `""`·`{}` → E1 PASS, F2 base `"x"` → 거부 확인 성립). n-3 E6 INVALID 줄이 깨진 거부 확인 조건 이름(`judge_p3.py` `_e6_reject_check` 9개, 코드 순서: `출력 없음/findings 없음`·`findings 값 모양 모름(목록 아님)`(이 둘은 그 하나만 적고 멈춘다)·`exit≠1`·`없는 종류 키`·`changed 원소 모양 모름`·`changed 중복`·`허용 id 빠짐`·`changed 차이`·`나머지 발견 다른 종류` -- 목록 보충은 검토 v4s m-2, §8.v4s)을 적는다. n-4 위 v4r 줄 문구, `run_dod.sh` 머리 이력 v4r·v4s 줄과 e6 주석 한 구절(동작 무수정). `judge_e6_selftest.py` docstring M01~M05b 정정 + 검토 v4r 실패 사례 14가지(D01~D03·N01~N04·G01~G07) 추가 → **69/69**(옛 v4r 판정기 대비: R16a·R30a·A11a~A13a·D01·D02 INVALID → FAIL, G01·G02·G04·G05 PASS → INVALID). 사본 `*.pre-v4s.bak`(초안·`judge_p3.py`·`run_dod.sh`·`judge_e6_selftest.py`).

> **v3(2026-10-06, 리허설만 재실행)**: gate `master` `fd4ef8c` → `2183f2e`. 그 사이 커밋 7개 -- 문서 4개(`b4734cd` 백로그 이관, `8b64a84` 승인 기록 `20261001-b26-phase3-cards`, `298089b` B34 references, `7243f28` B34 spec card) + **B34 `20260930-b34-grammar-explicit` 병합**(`d504784` test·`2eb7e55` code·`c851e54` merge·`2183f2e` 판정 기록 -- Phase 3 card 첫 판정 기록). 판정 기준·kit 변경 없음(kit 결함 없음, kit 파일 안 건드림). 리허설 결과 §8.v3(`C:/g312`). §4·§5·§6 표의 '리허설' 열은 v2 값 그대로 두고, `2183f2e`에서 달라진 값은 §8.v3에만 적는다. 사본 `draft_phase3_dod.md.pre-2183.bak`.

> **v2(2026-10-06, 기준 재설정)**: gate `master` `4a286f0` → `fd4ef8c`. 그 사이 커밋 8개 -- card 35 `20260930-v3-changed-stmt-scope` 병합(`0ef7430` test·`b70a05a` code·`a17b8bd` merge·`dafe5cf` 판정 기록), [D-11] 계획 N3.10 MOD1 `_QUERY_CACHE_MAX` 토큰(`29d2fc2`)·승인 기록 `20261002-p3-d11-query-cache-max`(`300fd65`), **design 30 §10 정정 D1~D4 커밋 `7f67ec3`**(§9 어긋남 1·2 해소), 계획 N3.12.2 쓰기 경로표 F1 두 행·승인 기록 `20261002-p3-f1-workspaces-write-path`(`fd4ef8c`, plan_tables_hash `16b899d1…`). 판정 기준·kit 동작 변경 없음(kit은 머리 주석만). design 블록 5개는 `fd4ef8c`에서 다시 뽑아 sha256·줄 범위가 v1과 같음을 확인(§2). 리허설 재실행 §8.0(`C:/g285`). 사본 `draft_phase3_dod.md.pre-fd4.bak`, kit 사본 `phase3_dod_kit/*.pre-fd4.bak`.

> **v1(r1, 2026-10-02)**: 독립 검토 `_drafts/review_phase3_dod.md`(판정 S, 차단 없음) 반영. 사본 `draft_phase3_dod.md.pre-r1.bak`, kit 사본 `phase3_dod_kit/*.pre-r1.bak`.
> (S1) design `fresh()` 결함은 design 정정으로 -- 패치 도구 `_drafts/design30_dod_corrections.py`·안내 `design30_dod_corrections.md`(D1 필수, D2·D3·D4 채택, 게이트 실측상 문서 커밋만 필요·승인 기록 불필요).
> (S2) 판정기가 빈 입력을 PASS로 세던 경로 7개를 막음 -- E1(E0 PASS + F2 base 거부 확인 없으면 PENDING), E0(N3.10 10행 단정), N6.3-4(0개면 PENDING + 덮음 대조), N6.3-5(test-only `== {test}`, equivalence 근거 문장 없음 = FAIL), E4(`assignment` 없음 = INVALID), E3(rc 0일 때만 판정 줄), e01·e3b·e4·ia·e6 머리 HEAD = H 단정. 경미 §5 1~8 반영. 리허설 재실행 §8(`C:/g245`).

받는 agent(공식 실행 때): `gmid-verification-auditor`. 이 작업은 card가 아니다(spec card·판정 기록 .json·커밋 없음).
**모양은 Phase 2 DoD를 그대로 따른다**(실측으로 확인한 생산 경로):

| 단계 | Phase 2 실례 | Phase 3에서 |
|---|---|---|
| 브리핑(실행 절차만, 판정 기준은 design) | `_drafts/phase2_dod_brief.md` v1~v5(드라이런 `phase2_dod_dryrun.md`, 사전 실행 `phase2_dod_prerun.md` 반영) | 이 문서(v0) + 실행기 `_drafts/phase3_dod_kit/run_dod.sh` |
| 측정 판 H | DoD 착수 때의 gate `master` = `5f643a9`(md 일치 card 판정 기록 커밋, `5f643a9` 제목 'audit: 20261001-topology-md-sync …') | DoD 착수 때의 gate `master`(F2 판정 기록과 그 뒤 정리 커밋까지) |
| auditor 결과 파일 | `_drafts/phase2_dod_result.md`(격리 복제본 `C:/g90/iso`) | `_drafts/phase3_dod_result.md`(격리 복제본 `C:/g<N>/iso`) |
| 저장소 기록 | 오케스트레이터가 다시 계산하지 않고 옮김 → `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/phase2-dod.md`, 커밋 `2eefda1`(`Role: doc`, 137줄, 제목 'docs: Phase 2 완료 판정 기록(DoD, H = 5f643a9 -- …)') | `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/phase3-dod.md`(디렉터리는 `6c8287f`가 `scripts/e_inst_p3.py`·`e_lib_p3.py`를 넣으며 이미 있음) |
| 결과 머리 | `## 판정` 다음 줄 `판정: PASS` | 같음 |

이 초안은 **판정 기준을 만들지 않는다**. 기준은 design 30 §10(정본 bash 블록과 표)과 계획 N6.2 Phase 3 행(1020행, `fd4ef8c` 판 -- `4a286f0` 판 1018행에서 N3.12.2 두 행만큼 밀림)·N6.3(1030행~)이고, 여기는 (1) 그 명령을 어떤 입력으로 어떤 순서로 돌리는지,
(2) 입력값을 어느 card의 판정 기록에서 읽는지, (3) 기대값, (4) `fd4ef8c`(v2; v1·v0은 `4a286f0`)에서 모래상자로 미리 돌린 결과만 적는다. 이 문서와 기준 문서가 어긋나면 기준 문서를 따른다.

---

## 0. 착수 조건 (보내기 전에 오케스트레이터가 확인 -- `run_dod.sh guard inputs`가 기계로 단정)

| # | 조건 | 근거 | 실측(v4: C1·C4는 `6c724de`; 나머지는 `fd4ef8c` v2 리허설, v1 `4a286f0`와 다른 것만 따로 적음) |
|---|---|---|---|
| C1 | 아래 §4의 phase 3 card **20장**이 spec card로 H 트리에 있고, 20장 모두 판정 기록 `.ai/verification/<id>.json`이 있다 | 계획 N6.3 첫 줄, design §9.1(`^phase: 3$` 목록), 기록 `20261001-b26-phase3-cards` | v4 `6c724de`: `^phase: 3$` **2장**(B34 `20260930-b34-grammar-explicit` 판정 기록 있음 `2183f2e`, b26pre `20260930-b26-pre-test-strengthen` 기록 없음 -- attempt 1 폐기, attempt 2 대기), 나머지 18장 spec card 없음. (v2 `fd4ef8c`: 0장 -- 머리 분포 `phase: 0.5` 6 · `phase: 1` 13 · `phase: 2` 18 · 양식 1) |
| C2 | 게이트 card 넷(34 면제 묶기, 35 범위 정책, B33, G1)의 판정 기록이 H에 있다 | design §5.5.1·§8.1(G1 선행), §10 E2 ① 키(`defs`·`move_rejected`·`moved` = G1, `not_targeted`·`targets_by_def` = 범위 정책) | 34 `20260930-v3-exempt-binding` 있음(V `PNNNNNNNNP`, 판정 기록 커밋 `3e835e0`) · **35 `20260930-v3-changed-stmt-scope` 있음**(v2: V `PNNNNNNNNP`, red-green, base `4a286f0`·test `0ef7430`·code `b70a05a`, 병합 `a17b8bd`, 판정 기록 커밋 `dafe5cf`) · B33·G1 spec card 없음 |
| C3 | 역할 브랜치 `refs/heads/role/` 비어 있음 | Phase 2 브리핑 §2 가드 (4) | v2: **0개**(G2 PASS -- 35 병합 뒤 정리됨). v1 `4a286f0` 때는 35 진행 중 1~3개 |
| C4 | 승인·결정 기록이 H에 있다: `20260930-30-module-split-design`(design 30 승인), `20261001-b26-phase3-cards`(네 card phase 3) | design 머리 v8.5, §9.1 | 앞 것 있음(`36e170e`), 뒤 것 **있음**(`8b64a84` -- v2 `fd4ef8c` 때는 없었고 B34 등 네 card 머리 `approval:`이 가리킨다) |
| C5 | P2D(Phase 2 DoD '대상' 커밋)가 H 트리 `phase2-dod.md` '대상:' 줄의 첫 40자 해시이고, 같은 파일에 `판정: PASS` 줄이 있고, H의 조상 | design §10 E5 `P2D=` | `5f643a905fbc14c1374063b47fea6428ba088563`, `판정: PASS` 있음, 조상 O |
| C6 | `tools/migrate/move_plan.py`와 `tests/contracts/test_p3_registry_dest.py`가 H에 있다 | D0a·D0b 산출물(§10 E2·E4·E6) | 둘 다 없음(`tools/migrate/`에는 `extract_selftest.py` 1개) |
| C7 | E5 스크립트 사본 출처 4개가 있다 | design §10 E5 | H 판 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py`·`e_lib_p3.py` 있음(`6c8287f`), P2D 판 `.ai/verification/20260930-df36-instance-relpath/scripts/e_inst_df36.py`·`e_lib.py` 있음 |
| C8 | **D-27 동결**이 지켜졌다(D0b 병합~F2 병합 사이 Phase 3 밖 card가 엔진·`tools/gates`·`tools/migrate`·레지스트리 목적지 열을 바꾸지 않음) | design §9.1 동결 | 사후 측정은 E2 `INVALID` 검사·E6·E4 `reg_mismatch`가 한다(§5) |
| C9 | 메인 저장소를 cwd로 쓰는 다른 agent가 없고, 임시 경로 `C:/g<N>`가 없다(이 작업 전용 예약) | Phase 2 브리핑 §0 마지막 두 줄, 메모리 '임시 경로 고유 배정' | -- |

공식 실행의 `inputs.json` `missing`은 0이어야 한다. v4 `6c724de` 실측 **25개**(phase 3 spec card 0장 18 + `b26pre 판정 기록` 1 + 게이트 B33·G1 2 + B0·MPC 2 + 파일 2 -- §8.v4). `fd4ef8c` 리허설(v2)은 **27개**(card spec 20, 게이트 기록 2(B33·G1), B0, MPC, 파일 3: `test_p3_registry_dest.py`·`move_plan.py`·`20261001-b26-phase3-cards.md`) -- v1 `4a286f0`의 28개에서 35 판정 기록 1개(`dafe5cf`)만큼 줄었다.

**card 상태(v4 `6c724de`)**: B34 **완료**(판정 기록 `2183f2e`), b26pre spec card `6c724de`, attempt 2 개정 `ae1b588`(계약 1(d)·2·5·8 리터럴 개정, 같은 id·test-only, 판정 기록 대기 -- §8.v4 실행 중 gate `master`가 `ae1b588`로 옮겨짐), M10·T1 초안 작성(2026-10-06, `draft_p3_m10.spec.md` `20261006-p3-mod10-entry`·`draft_p3_t1.spec.md` `20261006-p3-test-relocate`). T1 착수는 사용자 질문 T1-2(V4 면제 다시 받기 `20261006-p3-t1-v4-exempt`) 답 뒤. 나머지 phase 3 card 18장 spec card 없음, B33·G1 spec card 없음.

**card 상태(`fd4ef8c`, v2 -- 이력)**: Phase 3 기간 0.5 게이트 card 넷 중 34·35 **완료**(판정 기록 `3e835e0`·`dafe5cf`), B33·G1 spec card 없음(대기). phase 3 card 20장(§4·`p3_cards.py`) **전부 대기**(spec card 0장). 착수 준비로 들어온 것: [D-11] N3.10 MOD1 대표 대상 `_QUERY_CACHE_MAX`(`29d2fc2`, 승인 `300fd65` -- M1·D0b가 소비), N3.12.2 gmid-code-author 쓰기 경로 `workspaces/current-reuse-telescopic-ota-report/*.py`·`workspaces/two-stage-ota-report/*.py`(`fd4ef8c`, 승인 `20261002-p3-f1-workspaces-write-path` -- F1이 소비). 둘 다 DoD 입력(§4)·MOD 파일 이름(N3.10 표 10행)은 바꾸지 않는다.

## 1. 기준 문서

- 측정 명령·통과 기준: design `docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md` §10(773~1117행, v8.5 `6c8287f` + 실행 절차 정정 D1~D4 `7f67ec3`(판정 블록·표 통과 기준 문구 불변), 승인 기록 `20260930-30-module-split-design` `36e170e`) -- **bash 블록이 정본**(design §10 머리 v6 문장), 표 칸은 ID와 통과 기준. §3 판정식 표(MOVED·MOVE-AST·MOVE-TOTAL·LAYER·SHIM·IMPORT-ANY·GONE-SHIM·SD-NAMES·REG-DEST·LAYOUT-FLAT).
- 조건: 계획 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` N6.2 Phase 3 행(1020행, `fd4ef8c` 판) "MOD1~MOD10 존재, import 계층 위반 0(`import_layering.py`), 이동 커밋마다 AST 해시 동일, `sizing_recipe.py` 삭제, 레지스트리 이관 목적지 열 = 실제 위치"와 N6.3(1030행~: 판정 기록 PASS·EL4·거부 입력 test, 동작 보존 Phase 1~3은 실행 가능한 회로 전부 equivalence).
- 결정: `20261001-b26-phase3-cards`(B34·b26pre·backfill·B26-1 = phase 3 → 이 DoD의 N6.3 목록), 선례 `20260930-phase2-e4-baseline`(직전 Phase DoD 대상 대 마지막 병합본 비교 -- design E5가 따른 모양)·`20260930-phase2-e4-phase`(Phase 번호 바꾼 PT와 `--gmid-dod` 두 실행 -- design E5가 처음부터 쓴 모양).
- 판정 실행 규칙은 Phase 2 브리핑 §2·§3을 그대로 쓴다(격리 복제본, 메인 읽기 전용, 스크립트 파일 실행, `APPDATA`·`HOME` export, 판 바꿀 때 HEAD·status 확인, 메인 쓰기 감시와 출처 판정).

## 2. 경로·가드·실행 방식

- 임시 경로 `G=C:/g<N>` 하나(공식 실행 때 오케스트레이터가 비어 있는 번호를 배정). 복제본 `$G/iso`(`--no-hardlinks --no-local -c core.longpaths=true -c core.autocrlf=false`, origin 제거, `checkout --detach H`), 스크립트 `$G/scripts`, 출력 `$G/out`, `TMP`·`TEMP`·`TMPDIR` = `$G/tmp`, cwd = `$G`. 결과 파일 `_drafts/phase3_dod_result.md`만 `$G` 밖.
- 실행: `bash _drafts/phase3_dod_kit/run_dod.sh "$G" "$H" official [단계…]`. 단계(기본 순서): `guard inputs e01 e2 e3 e3b e4 ia e5pt e5lib e6 n63 watch`. 각 단계는 `$G/out/timeline.txt`에 시작·끝을 적고 판정 줄을 `$G/out/judge.txt`에 덧붙인다(중간에 끊겨도 남는다). 오래 걸리는 `e2`(M card V3 재실행)·`e5pt`·`e5lib`는 `run_in_background`.
- 가드(`guard`·`inputs`, official이면 하나라도 어긋날 때 exit 1): G1 H = `gate/master` = `ls-remote gate refs/heads/master` / G2 역할 브랜치 0 / G3 복제본 HEAD = H·status 0줄 / G4 design 블록 추출 성공 / G5 `inputs.json` `missing` 0(v1: M card V1 `--gmid-phase`가 3이 아닌 것, MPC 판 `move_plan.py` blob ≠ H 판도 `missing`에 든다).
- 작업 트리를 읽는 단계(`e01`·`e3b`·`e4`·`ia`·`e6`)는 머리에서 HEAD = H·status 0줄을 단정하고, 아니면 H로 옮긴 뒤 다시 단정한다(`need_h`, 실패하면 모드와 무관하게 exit 1 -- v1, 검토 §4 끝). 단계만 다시 돌려도(`run_dod.sh … e6`) P2D 판을 재지 않는다. E5 판 전환 실패는 `E5 INVALID: 판 전환 실패 <판>` 줄(design 정정 D1과 같은 문구)과 함께 그 측정을 건너뛴다(`fresh_k`).
- **판정 코드는 손으로 옮기지 않는다**: `phase3_dod_kit/extract_design_blocks.py <iso> <H> <S>`가 **H 판 design 30 §10**(§10~§11 머리 사이에서만 찾음)에서 `E3_AST`·`E3B_AST` heredoc, E5 판정 python heredoc, `import_any()` 함수, `EXCL`·`MP_ARGS` 줄을 바이트 그대로 뽑고 sha256을 `blk_sha256.txt`에 적는다. 표지가 정확히 한 번이 아니면 INVALID. `fd4ef8c` 추출값(v2 재추출 -- `4a286f0` 값과 sha256·줄 범위 모두 같다. `7f67ec3` 정정의 세 hunk(783~796 `GC`·`PT3`, 1034~1044 `fresh()`·호출, 1099 E6 `--head`)는 모두 다섯 블록 밖이라 블록 바이트가 그대로다. 결과 파일 '절차 메모'에 공식 실행 값과 함께 적는다):

  | 블록 | design 줄 | sha256 |
  |---|---|---|
  | `blk_e3_ast.py` | 822-858 | `ec96033a6ff69bae31f3c4bec02300447c4fba767df9deef1b3bc6b4d547ae96` |
  | `blk_e3b_ast.py` | 875-988 | `b3803fca20258a019fb7c4d410ec24ae421b03cf1d88e84ac480c57861f70b7a` |
  | `blk_e5_judge.py` | 1047-1095 | `ae6422d680dae2ab46b53e952ab340e0ac4bab78b816572b17946f3bbe8f5bad` |
  | `blk_import_any.sh` | 999-1018 | `de554c33a8807fa7a7c5ae31fe75fe6b2a30ad3a97450427c153cead37a4b318` |
  | `blk_vars.sh`(`EXCL` 820, `MP_ARGS` 797-801) | -- | `e00a46341f7bbc46e4e2aeb44c2a6eb986eb9a365f8453285697305ca504df3a` |

  design 30의 다섯 블록이 H까지 바뀌지 않으면 같은 값이어야 한다(다르면 '절차 메모'에 어느 커밋이 바꿨는지). `fd4ef8c`까지 design 30을 바꾼 커밋은 `6c8287f`(v8.5)·`7f67ec3`(정정 D1~D4, 블록 밖).
- 메인 쓰기 감시(`watch`): status `--porcelain --ignored` 전후 같음, reflog 전후 같음, `find <R>/{workspaces,skills,tools,.ai/verification} -newer stamp` 0개, 루트 `-maxdepth 1` 0개. 불일치는 Phase 2 브리핑 §2의 (가)(나)(다) 출처 판정.

## 3. 공통 정의 (design §10 '공통'과 같은 값, 실행기 머리)

```bash
PY="C:/Python314/python.exe -B"                                # design 그대로(따옴표 없이 펼친다)
GC="$G/cache_$H/tools/gates"                                    # git archive H tools/gates -- <iso> 밖(design 정정 D4 = `7f67ec3` 786행과 같음, §9 1 해소)
PT3(){ local t="$ISO/skills/analog-gmid-design/assets/tests"; case "${1:-}" in "$ISO"/*) t="$1"; shift;; esac
  PYTHONPATH="$GC" PYTHONPYCACHEPREFIX="$(mktemp -d -p "$G/pyc")" C:/Python314/python.exe -P -m pytest -c "$GC/pytest_gate.ini" \
    --rootdir="$ISO" --confcutdir="$ISO" "$t" --gmid-phase=3 "$@"; }      # 출력 형식용으로 -q --color=no만 더한다
source "$S/blk_vars.sh"                                         # EXCL(D-9 제외 집합), MP_ARGS(--plan --registry --split 5 --keep --aliases)
MPC=<inputs.json MPC>; git -C "$ISO" show "$MPC:tools/migrate/move_plan.py" > "$S/move_plan.py"
B0=<inputs.json B0>; P2D=<inputs.json P2D>; cards.txt = <inputs.json에서 만든 8줄>
to_h(){ checkout -- . ; clean -fdx ; checkout --detach "$1" ; HEAD = "$1" ; status --porcelain --ignored 0줄 }   # 판 바꾸기(design 정정 D1 = `7f67ec3` 1034행 fresh()와 같음, §9 2 해소)
need_h(){ HEAD = H·status 0줄이 아니면 to_h H, 그래도 아니면 exit 1 }                                     # v1
fresh_k(){ to_h "$1" 실패면 `E5 INVALID: 판 전환 실패 $1` + return 1 }; 측정 = `fresh_k X && $PY …`        # v1(design 정정 D1·D2와 같음)
```

## 4. 입력값과 그 값을 주는 판정 기록 (`phase3_dod_kit/inputs_p3.py <iso> <H> <out> <GC>`)

| 입력 | 정의(design §10) | 읽는 곳 | 주는 card(판정 기록) | `fd4ef8c`(v2) |
|---|---|---|---|---|
| `P2D` | Phase 2 DoD '대상' 커밋 | H 트리 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/phase2-dod.md` '대상:' 줄 첫 40자 해시 | (Phase 2 DoD 기록 `2eefda1`) | `5f643a905fbc14c1374063b47fea6428ba088563` |
| `B0` | M1 판정 기록 `base_commit`(D0b 병합 뒤) | `.ai/verification/<M1 id>.json` | **M1** `20261002-p3-move-mod1-gmid-lut`(초안 id -- 커밋 날짜로 바뀔 수 있음, kit은 slug 정규식) | 없음(PENDING) |
| `MPC` | `tools/migrate/move_plan.py`를 마지막으로 바꾼 판정 기록의 `code_commit` | 기록마다 `git diff --name-only base code -- tools/migrate/move_plan.py`가 빈 출력이 아닌 것 중 판정 기록 커밋이 가장 새것. 덤으로 `MPC:move_plan.py` blob = `H:move_plan.py` blob 확인(다르면 판정 기록 밖 변경 -- v1: `missing`에 넣어 G5가 INVALID로 멈춘다, 검토 §5-1) | **D0a** `20260930-p3-move-plan-tool`(지금 초안 id) | 없음 |
| `cards.txt` 8줄 | `<base_commit> <code_commit> <MOD 파일> <V1의 --gmid-strict= 값>` | M 기록의 `base_commit`·`code_commit`, `auditor_run.commands` 중 `V1: `로 시작하는 원소의 `--gmid-strict=` 값(그 원소의 `--gmid-phase=`도 적는다 -- 3이어야 한다, merge_gate `v1_command_check`; v1: 3이 아니면 `missing`, 검토 §5-2), MOD 파일 = H 판 계획 N3.10 표(`import_layering.mod_table`) MODn | **M1·M2·M3·M4·M5·M6·M8·M9** | 0줄. N3.10 표(H 판) = MOD1 `gmid_lut` · MOD2 `topology_authoring` · MOD3 `circuit_state_graph` · MOD4 `gmid_sizing_engine` · MOD5 `circuit_metrics` · MOD6 `theta_search` · MOD7 `stick_diagram` · MOD8 `sizing_layout_convergence` · MOD9 `instance_report_builder` · MOD10 `gmid_design_pipeline` |
| E4 test | `contracts/test_p3_registry_dest.py` | H 트리 | **D0b** `20260930-p3-registry-dest`(test 커밋) | 없음 |
| E5 rails 계약값 | `RailDeclaration(nets = P2D library supply_nets)` | 판정 python이 `git show P2D:…/library/<회로>.topology.json`에서 직접 | **B26-1** `20260930-b26-rail-accessor-set`(계약 1·2·8 -- `MASK_META = ("rails",)`의 근거) | B26-1 미병합 |
| E5 `EXCL_INST = ()` | instance.json에서 뺄 키 없음 | design 판정 python 상수 | B34(계약 7)·B26-1(계약 8)·b26pre(test-only)·backfill(`interdig_ok`는 `pipeline_result`에만) -- design D-28 (e) | -- |
| E6 `--allow-changed` | `workspaces/run_harness.py::run`, `…/gmid_design_pipeline.py::run_gmid_design_pipeline` | design 블록 상수 | **M10** `20261006-p3-mod10-entry`(초안 id -- 커밋 날짜로 바뀔 수 있음, kit은 slug 정규식)(ENTRY -- 계약 3 MOD10 최상위 = import + def 하나) · 의미는 **D0a** 계약 4 `changed` 끝 문단(det4·det5, 단계 `allow-changed-declared`: 허용 id는 `changed` 단위이되 목록에 적지 않음 -- base 짝 `lost` 아님·자기 읽기 `rebind` 아님; 다른 단위의 `rebind`·`lost`와 삭제된 허용 id의 `lost`는 그대로). v4: 거부 확인(허용 없이 exit 1·`changed` ⊇ 두 id(중복 없음)·나머지 발견 두 실행 같음 -- v4r 검토 v4 S1)을 §6에서 같이 잰다 | -- |
| E2 V3 출력 키 | `defs`·`move_rejected`·`moved` / `not_targeted`·`targets_by_def` | H 판 `tools/gates/mutate_changed.py` | **G1** `20260930-p3-gate-move-aware`(초안 id -- 커밋 날짜로 바뀔 수 있음, kit은 slug 정규식) / **35** `20260930-v3-changed-stmt-scope`(v2: 병합 완료) | v2 `fd4ef8c` 판 V3 출력 키 = `exempt_ignored killed mutants not_targeted survivor_bindings survivors targets targets_by_def tool verdict` -- 35 몫 `not_targeted`·`targets_by_def` 생김, G1 몫 `defs`·`move_rejected`·`moved` 셋 없음(v1 `4a286f0`: 다섯 키 모두 없음). v4 관찰: M10 초안 V3-RESULT(G1 시제품 + 범위 정책 판 `mutate_changed`)가 다섯 키 이름을 design 이름 그대로 냄(`m10_t1_open_items.md` 'M10 V3' -- M10 모의, 판정 기준 아님) |
| E1·E3·E3b 판정 시점 | F2 병합 뒤 | H | **F2** `20261002-p3-shim-delete`(F1 `20261002-p3-callers-update`가 대상 상태를 만든다)(초안 id -- 커밋 날짜로 바뀔 수 있음, kit은 slug 정규식) | -- |

## 5. 판정 항목 -- **13개**(design §10 표 E0~E6 8개 + 계획 N6.3 1~5 5개)

명령 열의 단계 이름은 `run_dod.sh` 단계, 괄호는 design §10 줄. '기대'는 공식 H의 PASS 조건(design 표 문구 요약 -- 판정은 design 문구 그대로). 리허설 열은 `fd4ef8c`(v2, Phase 3 card 0장 병합) 실측이고 증거가 아니다. v1 `4a286f0`와 다른 값은 '(v1 …)'로 함께 적는다.

| # | ID | 계획 조건 | 명령 | 기대(PASS) | 입력 기록 | `fd4ef8c` 리허설(v2) |
|---|---|---|---|---|---|---|
| 1 | E0 | MOD1~MOD10 존재 | `e01`: `$PY "$GC/import_layering.py" --root "$ISO" > layer.json`(806행) → `judge_p3.py e01` | `present` = N3.10 10행 전부. v1: 도구가 읽은 표가 10행·번호 1..10이 아니면 **INVALID**(빈 표 = `present 0/0` PASS를 막는다, 검토 §4-b) | F2 등 M card 전부 | **FAIL** -- `present` `{"stick_diagram": 7}` 1/10(판별: 9개 없음) |
| 2 | E1 | import 계층 위반 0 | 같은 실행 + v1 거부 확인: F2 판정 기록 `base_commit` 판을 `git archive`로 `$G/f2base`에 풀어 같은 도구(`layer_f2base.json`) | exit 0, `findings` 0(F2가 SD → MOD9 임시 재수출을 지운 뒤). v1(검토 §4-a): **E0이 PASS가 아니면 PENDING**(MOD 파일이 없으면 위반도 있을 수 없다 -- 공허), F2 base 출력이 없으면 PENDING, F2 base `findings` 0이면 INVALID(D-22 임시 재수출을 못 잡음). PASS 줄에 거부 확인 수를 함께 적는다. r2(검토 r1 m1): H 출력에 `findings` 키가 없으면 **INVALID**(키 없음을 0으로 읽지 않는다) | F2 | **PENDING**(E0 미충족 -- 공허, 판정 아님; exit 0·`findings` 0은 적기만) |
| 3 | E2 | 이동 커밋마다 AST 해시 동일 | `e2`: `git diff --quiet "$B0" H -- tools/gates tools/migrate`(809행) + `cards.txt`마다 `mutate_changed.py --base b --head h --gmid-phase=3 --gmid-strict=<V1 값>`·`move_plan.py check --card <MOD>`(810~814행) → `judge_p3.py e2` | `E2 INVALID` 없음; card마다 ① V3 exit 0, `defs` = `[]`, `mutants` = 0, `move_rejected` = `{}`, `not_targeted` = 0, `targets_by_def` = `{}` ② check exit 0, `findings` 열 종류(`move-set`·`move-rejected`·`changed`·`lost`·`rebind`·`future`·`import-dup`·`stmt-order`·`order`·`shim`·`cache` -- D0a 계약 4 11종, design §10 E2 표 괄호는 10개(§6.3 459행은 11개) -- '모든 목록'으로 판정) 모두 빈 목록 ③ 일관성(`moved` = `moved_defs` 등)은 증거로 세지 않고 적기만. v1: `cards.txt`가 8줄(한 줄 4칸)이 아니면 INVALID(검토 §5-3) | M1~M6·M8·M9, D0a(MPC), G1·35(키) | **PENDING**(cards.txt 0줄). 기계 리허설 `mutate_changed --base fd4ef8c^ --head fd4ef8c`(문서 커밋) → exit 0, 단계 112 s; ①의 키 중 `defs`·`move_rejected`·`moved` 3개 없음(v1 `4a286f0^..4a286f0`: 5개 없음, 94 s -- 35 병합으로 `not_targeted`·`targets_by_def`가 생긴 것이 기대된 차이) -- 판정기가 키 없음을 PASS로 세지 않는다 |
| 4 | E3 | `sizing_recipe.py` 삭제 | `e3`: 세 shim 부재(817~819행) + `blk_e3_ast.py`를 B0(거부 확인)와 H에(866~871행) | 첫 루프 출력 없음, 거부 확인이 B0에서 `stmt` > 0·`call` > 0, `E3 FAIL(도구 오류)` 없음, H에서 제외 집합 밖 importer 0 → `E3 PASS`. v1(검토 §4-g): design 866~871행처럼 파이썬 rc ≠ 0이면 그 판은 `E3 FAIL(도구 오류 rc=… rev=…)` 한 줄만 내고 `E3 PASS`/`E3 FAIL:`·거부 확인 수 줄은 내지 않는다 | B0(M1), F1·F2 | 세 파일 있음 → `E3 FAIL` 3줄; 거부 확인(대용 B0 = H) rc 0 **`stmt` 69줄·63파일, `call` 9줄·5파일**(design 부록 `7535799` 실측과 같은 수), 제외 집합 안 1파일; H 판정 `E3 FAIL: 제외 집합 밖 importer 66파일`(판별) |
| 5 | E3b | (SD-NAMES, D-26) | `e3b`: `blk_e3b_ast.py "$ISO" "$B0" HEAD "$EXCL"`(991행) | `E3b LIVE moved_out=m base_files_reading_moved_out=f pre_existing=p`에서 m > 0·f > 0, `INVALID`·`FAIL`·`ERROR`·도구 오류 없음, `E3b PASS`; p는 적기만 | B0(M1), F1·F2 | 대용 B0 = H: `LIVE moved_out=0 base_files_reading_moved_out=0 pre_existing=1` + **`E3b INVALID`**(거부 확인이 '이동 없음'을 잡는다 -- design 기대와 같음). `pre_existing=1`은 design §11-10 `stick.py` `block_from_row_widths`와 같은 수 |
| 6 | E4 | 레지스트리 목적지 = 실제 위치 | `e4`: `PT3 …/contracts/test_p3_registry_dest.py`(995행) + `move_plan.py plan`(996행) → `judge_p3.py e4` | test exit 0, plan exit 0, `reg_mismatch`·`unassigned`·`upward`·`cycles`·`conflicts` 0, `absent_split` = [`design_report.py`, `sizing_recipe.py`, `topology_library.py`], SD·ACF 밖 단위 `rule` 전부 `A-0`. v1: `assignment`가 없거나 비면 **INVALID**(A-0 검사가 공허하게 참이 되는 것을 막는다, 검토 §4-f). r2(검토 r1 m4): 출력 없음 표지를 둘로 나눔 -- `move_plan.py` 없음(plan 미실행) → `E4 PENDING`, plan을 돌렸는데 출력 JSON이 없음/읽을 수 없음 → `E4 INVALID` | D0b(test), D0a(MPC) | **PENDING**(test·도구 없음) |
| 7 | E5 | 동작 보존(N6.3) | `ia`: `import_any "$ISO"`(1019행); `e5pt`: `PT3`·`PT3 --gmid-dod`(1022·1023행); `e5lib`: E-INST 2회로 × (P2D df36, P2D p3, H p3) + E-LIB 4회(1028~1045행) + `blk_e5_judge.py`(1046~1096행) | IMPORT-ANY `tried=n expected=n failed=0` 한 줄(n > 0) + 함수 종료 0; PT3 두 실행 실패 0·수집 ≥ 1; `E5 INVALID` 없음 + `E5 E-LIB/E-INST PASS` | B26-1(rails), P2D, `6c8287f` 스크립트 | IMPORT-ANY **`tried=5 expected=5 failed=0`**, 종료 0(SR·SD·TL·DR·ACF); PT3·PT3 --gmid-dod 둘 다 1047 passed·15 xfailed; E-INST 2회로·E-LIB 해시 같음, **rails 계약 FAIL 9 → E5 FAIL**(B26-1 미병합 -- 기대) -- v2 `fd4ef8c`도 같음 |
| 8 | E6 | 정의 보존(MOVE-TOTAL) | `e6`: `move_plan.py check --base "$B0" --head "$H" --card ALL --allow-changed <2>`(1099~1101행, v1: `--head "$H"` = design 정정 D3, 단계 머리 HEAD = H 단정) | exit 0, 발견 목록 전부 빈 목록(11종 키 모두 있음). v4(검토 refresh m2, v4 검토 S1): 같은 B0..H를 `--allow-changed` 없이 돌린 거부 확인이 exit 1이고, 그 `findings.changed` 단위 id 집합이 두 허용 id를 **포함**하고(중복 없음), 두 허용 id를 뺀 `changed`와 다른 10종이 허용 있는 실행의 `findings`와 같아야 한다 -- 아니면 **E6 INVALID**(허용이 실제 바뀐 단위를 덮지 않거나 두 실행이 어긋남). 거부 확인이 성립하면 판정은 허용 있는 실행으로 한다(선언 밖 `changed`·`lost` 등은 두 실행 모두에 나오므로 `E6 FAIL`). v4s(검토 v4r n-1): 허용 있는 실행이 이미 FAIL 모양(exit ≠ 0 또는 비지 않은 발견)이면 거부 확인이 불성립이어도 **`E6 FAIL`**(불성립 조건을 덧붙임 -- 예: 삭제된 허용 id는 두 실행 모두 `lost`이고 거부 확인 `changed`에 그 id가 없다, D0a 계약 4); 거부 확인 불성립 → INVALID는 허용 있는 실행이 PASS 모양일 때만(공허 PASS 막기) (§6 'E6 거부 확인'; `judge_p3.py e6`) | B0(M1), D0a(MPC), M10 | **PENDING** |
| 9 | N6.3-1 | 판정 기록 PASS | `n63`: `n63_p3.py`(H 트리 `.ai/verification/*.json` 전수) | 전부 `checks.V1`~`V10` ∈ {PASS, N/A}; 건수 = 35 + 20(phase 3) + 3(35·B33·G1) = **58 예상**(그 사이 다른 card가 있으면 그만큼) | 전부 | v2: **36건** 전부 PASS/N/A(v1 35건 + 35 판정 기록 `dafe5cf`). 58 예상은 그대로(36 + phase 3 20 + B33·G1 2) |
| 10 | N6.3-2 | phase 3 기록 | 같은 도구 | `git grep -l -E '^phase: 3$' H -- docs/02-design/specs` = §4 목록 20장과 같은 집합(표지마다 정확히 1장), 20장 모두 판정 기록 있음, 목록 밖 phase 3 card 0 | 20 card | 0장 → FAIL(표지 20개 모두 0장) |
| 11 | N6.3-3 | merge gate(EL4) 형식 | 같은 도구 | card마다 기록을 마지막으로 바꾼 커밋 = `Role: audit`·`Change-Id: <id>`·H 조상; test-only 아니면 제목 `merge <id>` 병합 정확히 1개(H 조상); test-only면 병합 0·`code_commit` null·audit 커밋 단일 부모 = `test_commit`; base·test·code H 조상 | 20 card | 행 없음 → FAIL |
| 12 | N6.3-4 | 카드 밖 엔진 변경 0 | 같은 도구: `git log P2D..H -- 'skills/analog-gmid-design/assets/*.py' workspaces/run_harness.py 'skills/analog-gmid-design/assets/library/*.json' 'tools/migrate/*'`(nomerge -- `--no-merges` 없음, 2026-10-06 사용자 승인; 기본 history simplification이 남긴 merge는 `merge_class`로 가른다: 자동 병합(`merge-tree --write-tree`)과 그 경로 내용이 같으면 clean → 목록에서 빼고 `merges_clean`에 적기만, 다르면 evil(충돌 해결·부모 3개 이상 포함) → trailer와 무관하게 어긋남) | 전부 `Role: code`/`test` + Change-Id ∈ phase 3 20장. v1(검토 §4-c): **커밋 0개면 PENDING**(Phase 2는 기대 개수 31로 공허를 막았다). 덮음 대조: 20 card 판정 기록의 `test_commit`·`code_commit`(null 아닌 것) 중 **엔진 경로를 바꾼 커밋은 모두 목록에 있어야 한다**(없으면 FAIL). 엔진 경로를 바꾸지 않은 커밋(레지스트리 문서만 등)은 목록에 들 수 없으므로 '경로 밖'으로 적기만 한다 -- 검토 문구 "전부 목록에"를 그대로 걸면 Phase 2 재현에서 `registry-grade-fix` code `cbddcb9`(레지스트리 문서만, D0b도 같은 모양 예상)가 거짓 FAIL이 된다(§6) | 20 card | **PENDING**(`5f643a9..fd4ef8c` 0개 -- 35의 `tools/gates` 커밋은 pathspec 밖; v0의 공허 PASS) |
| 13 | N6.3-5 | 동작 변경 card 증거 | 같은 도구 | red-green(design: B34·backfill·B26-1·D0a·D0b·M10·F2 = 7) `red.test_ids`·`failure_hashes` 비어 있지 않음 + V2 PASS; test-only(b26pre·T0·T1 = 3) 4번 목록에서 그 card 커밋의 Role 집합 **정확히 `{test}`**(v1: 빈 집합 FAIL, Phase 2 문구 "`Role: test` 각 1개", 검토 §4-d); equivalence(FU·M1~M6·M8·M9·F1 = 10) V2 PASS + `checks.V2.basis`가 비어 있지 않음(v1: 비면 `근거 문장 없음` = FAIL, `outputs_hash`만으로 통과 금지 -- 검토 §4-e) -- base = 병합본 문장 인용인지는 도구가 `quote_check` 표시를 달고 **auditor가 인용으로 판정** | 20 card | 행 없음 → FAIL |

판정 종합: 13항목 모두 PASS면 `판정: PASS`. PENDING(입력 없음)은 공식 실행에서 나오면 안 된다(가드 G5가 먼저 멈춘다).
evidence_type은 **기록에 적힌 그대로** 적고, design §8 유형과 다르면 판정을 바꾸지 않고 '절차 메모'에 적는다(Phase 2 B49 선례).

## 6. 판별력 대조 (공식 실행에서도 같은 순서로 -- 검사가 실제로 거부함을 보인다)

| 대상 | 판 | 기대 | 리허설(v2 `fd4ef8c` 재실행 행은 그렇게 적음, 나머지는 v1 `4a286f0`) |
|---|---|---|---|
| E0 | B0(M1 base) | `present` 1/10(`stick_diagram`만) -- M card가 MOD 파일을 만든다 | H = `fd4ef8c`에서 1/10(같은 모양, v1 `4a286f0`도 같음) |
| E1 거부 확인(v1) | F2 판정 기록 `base_commit` | `findings` > 0(SD → MOD9 임시 재수출, D-22) -- 0이면 E1 INVALID | F2 미병합 → 수행 안 함(E1 PENDING). 판정기 합성 입력 확인(`C:/g245/jt`): F2 base findings 0 → `E1 INVALID`, 3 → `E1 PASS … 거부 확인 findings=3`, 출력 없음 → `E1 PENDING`, E0 FAIL → `E1 PENDING` |
| E0 표 단정(v1) | MOD10 행을 뺀 계획서 사본 | `E0 INVALID N3.10 표 9행` | 합성 입력에서 그대로 |
| E2·E4 판정기(v1) | 3줄 cards.txt / `assignment` 없는 plan 출력 | `E2 INVALID cards.txt 3줄` / `E4 INVALID … assignment` | 합성 입력에서 그대로 |
| E3 거부 확인 | B0 | `stmt` > 0·`call` > 0(명령이 살아 있다) | v2 `fd4ef8c` = v1: 69줄·63파일 / 9줄·5파일(`test_d_delete_dead.py:101`, `test_d_delete_telescopic.py:111`, `test_dup_w_calc.py:75`, `test_restore_plan_functions.py` 5곳, `test_ts6_dead_probes.py:229`) |
| E3b | B0 = HEAD | `E3b INVALID`(moved_out 0) | 그대로 재현(v2 `fd4ef8c`도) |
| E2 판정기 | 키 없는 V3 출력 | PASS로 세지 않음 | v2: 키 3개(`defs`·`move_rejected`·`moved`) 없음 보고(v1: 5개) |
| E6 거부 확인(v4, v4r 검토 v4 S1) | B0..H, `--allow-changed` 없이 | exit 1, `findings.changed` ⊇ {`workspaces/run_harness.py::run`, `skills/analog-gmid-design/assets/gmid_design_pipeline.py::run_gmid_design_pipeline`}(중복 없음), 두 id를 뺀 발견 = 허용 있는 실행의 발견(올바른 H에서는 `changed` = 정확히 두 id·다른 10종 빈 목록 -- D0a 단계 `allow-changed-declared` (2)와 같은 모양) -- 아니면 E6 INVALID(허용 있는 실행이 PASS 모양일 때만; 이미 FAIL 모양이면 불성립 조건을 덧붙여 E6 FAIL -- v4s 검토 v4r n-1. INVALID·FAIL 줄은 깨진 조건 이름을 적는다 -- n-3) | 공식에서만(리허설은 D0a 없음). 판정기 합성 입력 확인 §8.v4·§8.v4r·§8.v4s |
| E5 rails 계약 | B26-1 없는 HEAD | `E5 E-LIB rails 계약 FAIL` 회로마다 | 9회로 모두 FAIL 줄 + 종합 FAIL(§8 e5lib 행, v2 `fd4ef8c`도 같음) |
| N6.3 검사기 | Phase 2 H `5f643a9`, 범위 `da03c0e..`, `^phase: 2$`, Phase 2 목록 17 | committed `phase2-dod.md` N6.3 **수치** 재현(판정 일치가 아니다 -- phase=2 모드에는 Phase 2 브리핑이 허용한 예외 목록이 없어 2번은 `FAIL`로 찍힌다) | **수치 재현**(v1 검사기, `C:/g245/n63p2`): `1 PASS(n=34) \| 2 FAIL(18/17, 기록 없음 1) \| 3 PASS \| 4 PASS(n=31, 어긋남 0, 덮음 누락 0, 경로 밖 1) \| 5 PASS`. 기록 34건 전부 PASS/N/A; phase 2 card 18장·기록 17·없는 것 `20260923-probe-promote-consistency` 1(2번 FAIL의 원인 = Phase 2가 허용한 예외 1건); evidence_type red-green 8·equivalence 4·test-only 5; audit 커밋 17개(`1cdebc9` … `5f643a9`)와 병합 커밋 12개가 phase2-dod.md 표와 같음; 엔진 커밋 31개·어긋남 0(`tools/migrate/*`를 더해도 31). v1 덮음 대조: card 커밋 29개 중 목록 안 28·경로 밖 1(`registry-grade-fix` code `cbddcb9` -- `function-registry.md`만 3줄), 누락 0. test-only 5장 `{test}`, equivalence 4장 basis 모두 비어 있지 않음 -- v1 강화 뒤에도 5번 PASS 그대로. nomerge 판 kit(2026-10-06)으로 같은 범위를 다시 재면 JSON이 `merges_clean: []` 한 키만 늘고 수치 그대로(n=31, `review_nomerges` §1 -- `C:/g353`) |

## 7. 남긴 관찰 (판정에 걸지 않는다 -- 실측으로만)

1. **`--gmid-dod`의 엄격 대상**: E5 두 실행의 xfailed 수를 대조하고, `git grep -n -E 'gmid_ic\([^)]*phase="3"' H -- skills/analog-gmid-design/assets/tests` 수를 적는다(`4a286f0`·`fd4ef8c` = 0건, v2 두 실행 모두 15 xfailed -- 같으면 "phase 3 표식 IC 케이스 0, `--gmid-dod`가 엄격 대상을 더하지 않음").
2. **Phase 3 기간 0.5 card**: 34·35·B33·G1의 V 판정 한 줄씩(N6.3-1에 들고 2번 목록에는 넣지 않는다). v1(검토 §5-6): 같은 줄에 N6.3-3 행 검사(audit 트레일러·병합 모양)를 관찰로 돌린다(`n63.json` `obs_gate05`, 판정 기준 아님). `4a286f0`: 34 `PNNNNNNNNP`. v2 `fd4ef8c`: 34 `PNNNNNNNNP`·35 `PNNNNNNNNP`, 둘 다 audit·merge 행 검사 True, B33·G1 없음. B33은 spec card 초안 머리가 `phase: 0.5`·`gate_change: yes`(`_drafts/draft_b33.final.spec.md`)라 '네 card phase 3' 결정(`20261001-b26-phase3-cards` -- B34·b26pre·backfill·B26-1만 덮음) 밖이다.
3. **`P2D..H`의 `tools/gates` 커밋 trailer**(`obs_tools_gates`): 게이트 card 커밋만이어야 한다. `4a286f0`: `dd01d1d`(`Role: code`, 34)·`8b1f929`(`Role: test`, 34) 2개. v2 `fd4ef8c`: 4개 -- 위 둘 + `b70a05a`(`Role: code`, 35)·`0ef7430`(`Role: test`, 35), 모두 게이트 card trailer(기대된 차이). (nomerge 판: `--no-merges` 없이, clean merge는 빼고 evil merge는 `merge`·`merge_only_paths` 키와 함께 적는다.)
4. **E3b `pre_existing`**: 수와 (파일, 이름) -- `4a286f0`·`fd4ef8c` 1(design §11-10 백로그).
5. **E5 동등 확인의 `engine_origin`**: P2D 판 `e_inst_p3` 대 `e_inst_df36` 차이가 `engine_origin` 한 키뿐인지(판정 python의 INVALID 조건) -- 리허설 값은 §8.
6. **추적 산출물 instance.json `topology_ref`**: Phase 2 관찰 4와 같은 방식으로 H 판 두 파일 값만 적는다.

## 8. 리허설 (v3 `2183f2e`, v2 `fd4ef8c`, v1·v0 `4a286f0`)

### 8.v4s 판정기 개정·독립 검토·실제 범위 재실행 (2026-10-07 -- 판정 아님; 이 절은 검토 v4s m-2로 추가, 사본 `draft_phase3_dod.md.pre-v4t.bak`)

**v4s에서 바뀐 것**(검토 `review_phase3_dod_v4r.md` n-1~n-4, 머리 v4s 줄): n-1 E6 -- 허용 있는 실행이 이미 FAIL 모양(exit ≠ 0 또는 비지 않은 발견)이면 거부 확인 불성립이어도 `E6 FAIL`(불성립 조건을 줄에 덧붙임), PASS 모양일 때만 불성립 → `E6 INVALID`(공허 PASS 막기). n-2 `e01` H·F2 base `findings`가 목록이 아니면 `E1 INVALID`. n-3 E6 줄이 깨진 거부 확인 조건 이름을 적는다(`_e6_reject_check` 9개 -- 머리 v4s 줄). n-4 머리 v4r 줄 문구와 `run_dod.sh` 이력·e6 주석(동작 무수정). 자체 시험 `judge_e6_selftest.py`에 검토 v4r 실패 사례 14가지(D01~D03·N01~N04·G01~G07) 추가 → **69/69**.

**독립 검토 `_drafts/review_phase3_dod_v4s.md`(모래상자 `C:/g405`) -- B 0·S 0·minor 2, 거짓 PASS 0**. 검토자 자체 합성 34가지(E6 23 + e01 11) 34/34 기대와 같음, E-id마다 판정 줄 1개·traceback 0. 실제 경로 e01(`863a037`)에서 새/옛 판정기 출력 바이트 같음. `run_dod.sh` 명령 줄 변화 0. 옛 판정기(`judge_p3.py.pre-v4s.bak`)와 판정 종류가 달라진 자체 시험 케이스는 정확히 **11개**:
- R16a·R30a·A11a·A12a·A13a·D01·D02: 옛 INVALID → 새 **FAIL**(허용 있는 실행이 비지 않은 발견을 낸 FAIL 모양 -- n-1). 이 중 기대값을 바꾼 것은 R16a·R30a·A11a·A12a·A13a 5개(§8.v4r 끝 항목의 INVALID가 FAIL로 돌아감)이고 검토는 n-1 원칙에서 바로 나오며 약화가 아니라고 판정했다(어느 쪽도 PASS 아님, PASS 쪽으로 움직인 기대값 0). D03(허용 있는 실행 PASS 모양 + 허용 id 빠짐)은 INVALID로 남는다.
- G01·G02·G04·G05: 옛 **PASS** → 새 INVALID(e01 `findings` 목록 아님 -- n-2). 검토자 입력 G07(H `""` + F2 base `"x"`)에서 옛 판정기는 `E1` 거짓 PASS, 새 판정기는 INVALID.
- 나머지 58개는 옛과 같다.

**오케스트레이터 후속 수정(검토 v4s m-1)**: `judge_p3.py` `_e6_reject_check` 첫 줄을 `if not isinstance(n, dict) or not isinstance(n.get("findings"), dict):`로 -- 거부 쪽 출력이 최상위 사전이 아니면(목록·문자열) 예외(`E6 INVALID 판정기 예외`, 검토 V10·V11) 대신 `출력 없음/findings 없음` 조건으로 들어가 n-1 규칙을 따른다. 자체 시험 다시 **69/69**(`SELFTEST PASS`, rc 0 -- 작성자 재실행 `C:/g424`, `judge_p3.py` sha256 `ddb369b9…d7bd7b3`). 69가지에는 이 모양이 없어 따로 4입력으로 확인: 거부 쪽 `[1, 2]`·`"findings"` × 허용 있는 실행 FAIL 모양(`lost` 1, exit 1) → `E6 FAIL … 거부 확인 불성립(출력 없음/findings 없음(exit 1))`, PASS 모양(11종 빈 목록, exit 0) → `E6 INVALID 거부 확인 불성립: 출력 없음/findings 없음` -- 판정기 예외 0. 검토 m-2(이 절·§8.v4r 끝 항목·§6 E6 거부 확인 행 참조·머리 v4s 줄 조건 이름 목록)는 v4t에서 반영.

**실제 범위 재실행(gate `master` = `6df4bd7`)**: 검토 때 `863a037` 뒤 gate `master`가 `6df4bd7`로 옮겨졌다 -- 커밋 6개: backfill `20261001-b26-backfill-interdig-final-audit` 병합(`3004096` test·`495bb0e` code·`0bb2278` merge·`22fd126` 판정 기록), 승인 기록 `a6eaec3`(`20260930-b26-b40-reason-key`), B26-1 spec card `6df4bd7`(`20260930-b26-rail-accessor-set` + interface card). `863a037..6df4bd7`에서 design 30·계획·`tools/gates` 변경 0(문서 쪽은 B26-1 spec·interface card 2개와 승인·판정 기록뿐) → §2 블록 그대로(G4 PASS). kit `run_dod.sh /c/g424 6df4bd7 rehearse guard inputs e01 e4 n63`(읽기 단계만, TMP/TEMP = `C:/g424/tmp`, 셸 `cd` 없음, 메인은 `git -C` 읽기만, 13:48:43~13:49:40):
- guard: G1 PASS(H = `gate/master` = `ls-remote` = `6df4bd7`), G2 INFO(역할 브랜치 `role/test/20260930-b26-rail-accessor-set` -- B26-1 진행 중, official이면 멈춤), G3 PASS, G4 PASS.
- inputs: `missing` **23**(v4 `6c724de`·`ae1b588` 25 → 23): phase 3 spec card 0장 18 → **16**(backfill·B26-1 spec card 생김 -- 남은 것 T0·FU·D0a·D0b·M1~M6·M8·M9·M10·T1·F1·F2), 판정 기록 빠짐 b26pre → **B26-1**(b26pre `2db7622`·backfill `22fd126` 판정 기록 있음), 게이트 B33·G1 2, B0·MPC 2, 파일 2(`test_p3_registry_dest.py`·`move_plan.py`). P2D `5f643a9`, cards.txt 0줄.
- e01: `E0 FAIL present 1/10`(9개 없음), `E1 PENDING(E0 미충족 …) exit=0 findings=0`(F2 base 없음 -- 거부 확인 판 없음). 검토 §0 `863a037`과 같은 모양.
- e4: `E4 PENDING move_plan.py(D0a) 없음 -- plan 미실행(test exit 4)`.
- n63: `N6.3 1 PASS(n=39) | 2 FAIL(4/20, 기록 없음 1) | 3 FAIL | 4 PASS(n=5, 어긋남 0, 덮음 누락 0, 경로 밖 0) | 5 FAIL`, 관찰 0.5 = 34·35 `PNNNNNNNNP` audit·merge True, B33·G1 없음. 2의 4장 = B34·b26pre·backfill(기록 있음)·B26-1(기록 없음); 3은 20행 중 기록 없는 행 17(B26-1 + spec card 없는 16). `obs_tools_gates` 4(변화 없음).
- 메인: 전후 HEAD `6df4bd7`, status `--ignored` 177줄·reflog 362줄 전후 같음(watch 단계 대신 같은 비교를 손으로). kit 파일 무수정, `__pycache__` 0. `C:/g424`는 기록 뒤 삭제.

### 8.v4r 판정기 자체 시험 (2026-10-07, `phase3_dod_kit/judge_e6_selftest.py`, 임시 파일은 `C:/g384/tmp` 아래 tempfile, 끝에 삭제 -- 판정 아님)

검토 v4(`review_phase3_dod_v4.md`)의 S1·m-a·m-b를 `judge_p3.py`에 반영한 뒤, 검토 §2 합성 30가지(R01~R30, 검토 문구로 재구성 -- 원본 입력은 검토 모래상자와 함께 지워짐)와 §8.v4 작성자 13가지(A01~A13), m-b 보강 6가지(M01~M05b)를 한 파일로 고정했다. 원문이 '허용 없는 쪽에도 같은 발견이 있는지'를 말하지 않는 경우(R16·R30·A11~A13)는 두 변형(a 두 실행 어긋남 / b 두 실행 같음)을 둔다. 결과 **55/55 기대와 같음**(`SELFTEST PASS`), 옛 판정기(`judge_p3.py.pre-v4r.bak`)와 나란히 돌린 차이:
- 올바른 H 모양(R01·R02·R25·A01·A02) `E6 PASS` -- 옛과 같다.
- **R19**(`lost` 1, 두 실행 모두) 옛 INVALID → **`E6 FAIL {'lost': 1}`**, **R20**(선언 밖 `changed` 1, 두 실행 모두) 옛 INVALID → **`E6 FAIL {'changed': 1}`** -- S1 해소.
- R11(`changed` = [id1, id1, id2]) 옛 PASS → INVALID(m-a). R05(허용 없는 쪽에만 셋째 id) INVALID 그대로.
- R09(인자 2개)·R23a/b(`lost` 값 정수) 옛 traceback·판정 줄 없음 → `E6 INVALID 판정기 예외`/`findings 값 모양 모름`(m-b). M01~M05b: 명령 없음·모름 → `E? INVALID`, `e4` 인자 없음 → `E4 INVALID`, `e2` card 하나 값 모양 모름 → `E2 FAIL`(그 card를 `bad`에 넣고 계속), `GC` 없는 `e01` → `E0`·`E1 INVALID` 두 줄.
- 판정 종류가 옛과 달라진 것(검토 §3가 따로 예고하지 않은 것): 허용 있는 실행에만 발견이 있고 허용 없는 실행에는 없는 입력(R16a·R30a·A11a·A12a·A13a -- det3 모양 포함) 옛 FAIL → **INVALID**('두 실행 어긋남' -- 검토 §3 (a) 문언 그대로), 같은 발견이 두 실행에 다 있으면(…b) **FAIL**. 실제 도구(D0a 계약 4 178~181행: `lost`·`rebind` 예외는 두 실행에서 같다)에서는 b 모양만 나온다. 어느 쪽도 PASS가 아니므로 거짓 PASS 0. **v4s에서 바뀜**: 이 다섯(…a)은 검토 v4r n-1(허용 있는 실행이 이미 FAIL 모양이면 거부 확인 불성립이어도 FAIL)로 INVALID가 아니라 **FAIL**이 됐고 자체 시험은 69/69가 됐다 -- §8.v4s.

### 8.v4 작성자 재실행 (모래상자 `C:/g380`, 2026-10-06, 끝에 삭제 -- 판정 아님, 검토 refresh §0과 같은 범위)

환경: 메인에서 `git clone -q --no-hardlinks --no-local -c core.longpaths=true -c core.autocrlf=false`, origin 제거, `checkout --detach`, status `--ignored` 0줄, `TMP`/`TEMP`/`TMPDIR` = `C:/g380/tmp`, `cd` 없음(모든 경로 절대), `git archive <H> tools/gates` 캐시. `inputs_p3.py`·`n63_p3.py`만 직접 실행(guard·watch·측정 단계 미실행 -- 검토와 같음).

| 확인 | 결과 |
|---|---|
| 구문 | `ast.parse` 5개(`judge_p3.py`·`inputs_p3.py`·`n63_p3.py`·`p3_cards.py`·`extract_design_blocks.py`) OK, `bash -n run_dod.sh` OK |
| `6c724de`(검토 범위) | `inputs.json` `missing` **25**(검토 §0과 같은 목록), `N6.3 1 PASS(n=37) \| 2 FAIL(2/20, 기록 없음 1) \| 3 FAIL \| 4 PASS(n=2, 어긋남 0, 덮음 누락 0, 경로 밖 0) \| 5 FAIL`, `merges_clean` [], `obs_tools_gates` 4, 관찰 0.5 = 34·35 `PNNNNNNNNP` audit·merge True, B33·G1 없음 -- n63 줄 변화 없음(n63_p3.py 무수정) |
| `ae1b588`(실행 시점 gate `master` -- `6c724de` 뒤 b26pre spec card 개정 문서 커밋 1개, design 30·계획·`tools/gates` 변경 0) | `missing` 25(목록 `6c724de`와 같음), n63 줄 `6c724de`와 같음, `merges_clean` [] |
| E6 판정기 합성 입력(`judge_p3.py e6`, 13가지) | 허용 있음 11종 빈 목록 exit 0 + 거부 확인 exit 1·`changed` = 두 id(사전 `unit`/문자열 두 모양) → `E6 PASS`; 거부 확인 id 1개·exit 0 빈 목록(공허)·exit 0이지만 id 둘·`changed` 원소 모양 모름·다른 종류(`rebind`) 섞임·출력 없음(양쪽) → `E6 INVALID`; 허용 있음 출력에 `import-dup` 키 없음 → `E6 INVALID`; det3 모양(허용 있음에 `lost` 1·`rebind` 1) → `E6 FAIL {'lost': 1, 'rebind': 1}`; `import-dup` 1·열거 밖 종류 1 → `E6 FAIL` |
| E2 ② '모든 목록'(합성 cards.txt 8줄) | card 하나 `import-dup` 1·다른 card 열거 밖 종류 1(둘 다 exit 0) → v4 `E2 FAIL`(둘 다 이름 적힘), v3 판정기(`judge_p3.py.pre-v4.bak`)는 같은 입력에 `E2 PASS`(m1 결함 재현); 모두 빈 목록 → `E2 PASS` |
| 대역으로 E6 B0→H 모의 | **수행 안 함** -- 고친(det4) 대역이 없다: `p3kit_m2_m9/move_plan_sim.py`(10-02, 다른 agent 편집 중일 수 있어 건드리지 않음)는 허용 id를 `changed`에서만 빼는 det3 모양이라 E6 기대 모양을 재현하지 못한다(검토 refresh m7 -- §8.v3 끝 'v4 추가' 줄) |
| 메인 | 실행 전후 status `--ignored` 176줄·reflog 357줄 같음, HEAD = gate `master` = `ae1b588`. 역할 브랜치: 실행 시작 0 → 끝 1(`role/test/20260930-b26-pre-test-strengthen` = `ae1b588` -- 이 실행 밖 주체, 이 실행은 메인에 `git -C` 읽기만) |

### 8.v3 재실행 (모래상자 `C:/g312`, 2026-10-06 18:06~18:43, 끝에 삭제 -- kit `run_dod.sh /c/g312 2183f2e rehearse` 그대로(kit 동작 = v1 r2, 파일 안 바꿈), 메인 작업 트리에서 `git clone --no-hardlinks --no-local -c core.longpaths=true -c core.autocrlf=false`, origin 제거, TMP/TEMP = `C:/g312/tmp`, kit 안 cwd `C:/g312`)

**기대한 차이(B34 병합)만 나왔고 예상 밖 결과는 없다.** 판정 블록 5개 sha256·줄 범위 = §2 표 값(`2183f2e` 재추출, B34는 design 30을 바꾸지 않음). 메인: 실행 전후 status 176줄·reflog 355줄 같음, gate `master` 끝까지 `2183f2e`(v2 때와 달리 실행 중 동시 커밋 없음).

| 단계 | v3 결과 | v2 대비 |
|---|---|---|
| guard / inputs | G1 PASS(H = `gate/master` = `ls-remote` = `2183f2e`), G2 PASS(역할 브랜치 0), G3 PASS, G4 PASS(sha256 5개 같음), G5 `missing` **25** | missing 27 → 25: `B34 spec card 0장` 해소(spec card + 판정 기록 있음 -- `cards.B34` base `7243f28`·test `d504784`·code `2eb7e55`, evidence_type `red-green`), `파일 .ai/approvals/20261001-b26-phase3-cards.md` 해소(C4 -- v2 '뒤 사정'에서 예고한 것). 남은 25 = phase 3 spec card 0장 19 + 게이트 card B33·G1 2 + B0·MPC 2 + E4 test·`move_plan.py` 파일 2 |
| e01 | `E0 FAIL present 1/10`, `E1 PENDING(E0 미충족 …) exit=0 findings=0` | 같음 |
| e2 | PENDING(cards.txt 0줄), 기계 리허설 V3 `H^..H`(= `c851e54..2183f2e`, 판정 기록 커밋) exit 0, 없는 키 `defs`·`move_rejected`·`moved` | 같음 |
| e3 / e3b | 세 shim `E3 FAIL` 3줄, 거부 확인(대용 B0 = H) rc 0 stmt 69·call 9·파일 67(제외 1), `E3 FAIL: 제외 집합 밖 importer 66파일` / `LIVE 0 0 1` + `E3b INVALID` | 같음 -- B34 새 test `contracts/test_b34_grammar_explicit.py`는 `stick_diagram`만 import해 세 shim importer 수를 바꾸지 않음 |
| e4 / e6 | `E4 PENDING move_plan.py(D0a) 없음 -- plan 미실행(test exit 4)` / `E6 PENDING` | 같음 |
| ia | `tried=5 expected=5 failed=0`, 종료 0 | 같음 |
| e5pt | PT3 exit 0 **1090 passed·15 xfailed**(278.76 s) / `--gmid-dod` exit 0 **1090 passed·15 xfailed**(373.92 s) -- B34 판정 기록의 병합본 수치(1090 passed·15 xfailed)와 같음. 관찰 1: `gmid_ic(… phase="3")` 0건, xfailed 두 실행 같음 | 1047 → 1090 passed(+43 = B34 새 test), xfailed 15 그대로 |
| e5lib | 10회 exit 0, `E5 INVALID` 없음, E-INST 두 회로 같음(`without_topology_ref_sha256` crt `185b675e…`·fc `0ca6746f…`, raw crt `2fc426d9…`·fc `ef3cd996…` -- P2D df36·P2D p3·H p3 세 판 같음), E-LIB(rails 뺀 해시) 9회로 같음 `1d2e3bf6…b7a8f`(4회), rails 계약 FAIL 9 → `E5 E-LIB/E-INST FAIL`. 사본 sha256 앞 12자 `7d26134ad00e`·`c6b82fc7b4cd`·`6cc484956035`·`41b72d7d3449` = v0 값. 22분 6초 | 같음 -- B34가 analog-grammar 있음에서 동작 보존(B34 기록 '계약 7 base 대조·E-LIB 9/9·E-INST 2 같음')과 일치. rails FAIL은 B26-1 미병합(기대) |
| n63 | `1 PASS(n=37) \| 2 FAIL(1/20, 기록 없음 0) \| 3 FAIL \| 4 PASS(n=2, 어긋남 0, 덮음 누락 0, 경로 밖 0) \| 5 FAIL` | 아래 'N6.3 B34 처리' |
| watch | W1·W2·W3 PASS. 복제본 reflog clone → H → (P2D ↔ H) 3왕복 → H(8줄), 끝 HEAD = H, status 0줄 | v2의 W2·W3 FAIL(실행 밖 동시 커밋) 없음 |

**N6.3 B34 처리(검사기 `n63_p3.py`가 B34를 맞게 다루는지 -- 판정 기록 `2183f2e`와 대조)**:
- 1번: n 36 → **37**(B34 기록 추가), 전부 PASS/N/A. B34 V = `PPPPPPPNNP`(V8·V9 N/A = 도입 phase 4·6b, 기록 문구와 같음).
- 2번: `^phase: 3$` spec card = **1장**(`20260930-b34-grammar-explicit`), 표지 B34에 정확히 1장, 판정 기록 있음, 목록 밖 phase 3 card 0. 나머지 19 표지 0장 → FAIL(기대).
- 3번 B34 행: 기록을 마지막으로 바꾼 커밋 `2183f2e`(`Role: audit`·`Change-Id: 20260930-b34-grammar-explicit`, H 조상) → `audit_trailers_ok` True; test-only가 아니므로 병합 경로 -- 제목 `merge 20260930-b34-grammar-explicit` 병합 정확히 1개 `c851e54`(부모 `d504784`·`2eb7e55`, H 조상) → `merge_ok` True; base `7243f28`·test·code H 조상 True. 3번 FAIL은 나머지 19행 없음 때문(기대). 병합 커밋 trailer는 `Role: doc`(34 `5a602d4`·35 `a17b8bd`와 같은 관례) -- 검사기는 병합 trailer를 보지 않는다(판정 기준 밖, 관찰만).
- **4번: PENDING → PASS(n=2)** -- 처음으로 공허가 아니다. `5f643a9..2183f2e` 엔진 pathspec 커밋 = `d504784`(`Role: test`, `assets/tests/contracts/test_b34_grammar_explicit.py` -- pathspec `assets/*.py`의 `*`가 `/`를 넘어 tests 하위도 덮음)·`2eb7e55`(`Role: code`, `sizing_recipe.py`·`stick_diagram.py`) 둘, 둘 다 Change-Id = B34(목록 안) → 어긋남 0. 덮음 대조: B34 기록 `test_commit` `d504784`(엔진 경로 1)·`code_commit` `2eb7e55`(엔진 경로 2) 모두 `in_list`, 누락 0. B34 기록의 사슬(T `d504784` → K `2eb7e55` → M `c851e54`)과 같다. 다른 6개 커밋 중 문서 4·audit은 pathspec 밖, merge `c851e54`는 둘째 부모 `2eb7e55`와 엔진 경로가 같아(TREESAME) 목록에서 빠진다(v3 kit은 `--no-merges`, v4 kit은 기본 simplification -- `merges_clean` []) (v4r: 검토 v4 m-d 문구 정정, 수치 불변). 공식 실행에서 4번은 20장 전부의 커밋을 같은 방식으로 센다(지금 PASS는 1/20 범위의 PASS이고, 2·3·5번이 나머지를 막는다).
- 5번 B34: **test-only 경로가 아니라 red-green 경로**로 들어간다(분기는 기록의 `evidence_type` = `red-green`, design §8 유형 `red-green`과 같음) -- `red.test_ids` 27·`failure_hashes` 27, V2 PASS → B34 ok. 5번 FAIL은 19행 없음 때문(기대). 4번 `per_card_role` B34 = `{code 1, test 1}`이므로 만약 test-only로 잘못 분류됐다면 `{test}` 조건에 걸려 FAIL이 났을 것 -- 분기가 기록 값을 따름을 확인.
- 관찰 0.5: 34·35 `PNNNNNNNNP` audit·merge True, B33·G1 없음. `obs_tools_gates` 4개(v2와 같음 -- B34는 `tools/gates`를 바꾸지 않음).

**v3 뒤 사정(이 리허설 밖)**: watch 끝(18:43:25) 26초 뒤 18:43:51에 메인에 오케스트레이터 문서 커밋 `6c724de`(b26pre spec card `20260930-b26-pre-test-strengthen` + interface card, test-only, phase 3)가 들어와 gate `master`가 `6c724de`로 옮겨졌다(메인 reflog 355 → 356줄). 그 판에서는 N6.3-2가 2장(b26pre 판정 기록 없음 → `기록 없음 1`)이 되고 G5 `missing`도 b26pre 몫 1개가 바뀐다 -- 이 절의 수치는 `2183f2e` 기준이다.

**공식 실행 전 다시 볼 것(판정 기준 밖)**: 없음(예상 밖 결과 0). 위 4번 PASS가 '1/20 범위'라는 점만 결과 파일 N6.3 표에서 다른 항목과 함께 읽을 것.
v4 추가(검토 refresh m7): E6 B0→H 전체 모의가 아직 없다(실측은 card별 `check` -- M1~M9 발견 0 -- 와 M9→M10 `--card gmid_design_pipeline.py`(X-1)뿐). D0a 병합 뒤, M/T1/F 모의 사슬이 있으면 `check --card ALL` B0→끝을 한 번 돌려 볼 것(판정 아님; 허용 있음·없음 둘 다 -- §6 E6 거부 확인 모양).
v4r 추가(M10 모의 관찰 -- M-card/모의 agent 보고, 오케스트레이터 전달, 판정 기준 아님): M10 모의 판에서 `check --card ALL`을 돌리면 `stick_diagram.py` 4971행(SD 파일 끝 MOD9 재수출 줄 -- M9가 D-22 (1)로 남기는 임시 재수출, `draft_p3_m9.spec.md` 21·103행)이 `order` 발견 1을 낸다. 이 줄은 F2가 shim·임시 재수출을 지울 때 사라진다. E6은 **F2 병합 뒤의 최종 H**에서 돌리므로(§4 E1·E3·E3b 판정 시점 행, design §10 E6) 그때 `order`가 빈 목록인지 확인할 것 -- 비어 있지 않으면 E6은 FAIL로 적는다. E6 기준은 바꾸지 않는다(중간 판의 `order` 1은 F2 전 상태라 기대된 모양이고, 최종 H에서 남으면 결함이다).

### 8.0 v2 재실행 (모래상자 `C:/g285`, 2026-10-06 15:16~15:59, 끝에 삭제 -- kit `run_dod.sh /c/g285 fd4ef8c rehearse` 그대로(kit 동작 = v1 r2), 메인 작업 트리에서 `git clone --no-hardlinks --no-local -c core.longpaths=true -c core.autocrlf=false`, origin 제거, TMP/TEMP = `C:/g285/tmp`, cwd `C:/g285`)

**판정 결과는 v1(아래 8.1)과 같다. 다른 것은 기대된 차이 넷뿐이다**: (1) G2 역할 브랜치 0(35 정리) (2) G5 `missing` 28 → 27(35 판정 기록) (3) E2 기계 리허설 V3 출력에 `not_targeted`·`targets_by_def`가 생김(35 병합; G1 몫 3키는 여전히 없음) (4) N6.3-1 n 35 → 36, 관찰 2에 35 `PNNNNNNNNP`, 관찰 3 `tools/gates` 커밋 2 → 4(35 test·code). 시간은 실행마다 다르다.

| 단계 | v2 결과 | v1 대비 |
|---|---|---|
| guard / inputs | G1 PASS(H = `gate/master` = `ls-remote` = `fd4ef8c`), **G2 PASS(역할 브랜치 0)**, G3 PASS, G4 PASS(블록 sha256 5개·줄 범위 v1과 같음 -- §2), G5 `missing` **27** | G2 INFO → PASS, missing 28 → 27 |
| e01 | `E0 FAIL present 1/10`, `E1 PENDING(E0 미충족 …) exit=0 findings=0` | 같음 |
| e2 | PENDING(cards.txt 0줄), 기계 리허설 V3 `H^..H` exit 0, 키 `exempt_ignored killed mutants not_targeted survivor_bindings survivors targets targets_by_def tool verdict` -- design ① 키 중 `defs`·`move_rejected`·`moved` 없음 | 없는 키 5 → 3(35 몫 생김) |
| e3 / e3b | 세 shim `E3 FAIL` 3줄, 거부 확인 rc 0 stmt 69·call 9·파일 67(제외 1), `E3 FAIL: 제외 집합 밖 importer 66파일` / `LIVE 0 0 1` + `E3b INVALID` | 같음 |
| e4 / e6 | `E4 PENDING move_plan.py(D0a) 없음 -- plan 미실행(test exit 4)` / `E6 PENDING` | 같음 |
| ia | `tried=5 expected=5 failed=0`, 종료 0 | 같음 |
| e5pt | PT3 exit 0 1047 passed·15 xfailed(310.42 s) / `--gmid-dod` exit 0 1047 passed·15 xfailed(306.60 s) | 같음(시간만) |
| e5lib | 10회 exit 0, `E5 INVALID` 없음, E-INST 두 회로 같음(`without_topology_ref_sha256` crt `185b675e…`·fc `0ca6746f…` = v0 값), E-LIB 9회로 같음, rails 계약 FAIL 9 → `E5 E-LIB/E-INST FAIL`. 사본 sha256 앞 12자 `7d26134ad00e`·`c6b82fc7b4cd`·`6cc484956035`·`41b72d7d3449` = v0 값. 22분 14초 | 같음 |
| n63 | `1 PASS(n=36) \| 2 FAIL(0/20, 기록 없음 0) \| 3 FAIL \| 4 PENDING(n=0, 어긋남 0, 덮음 누락 0, 경로 밖 0) \| 5 FAIL`; 관찰 0.5: 34·35 `PNNNNNNNNP` audit·merge True, B33·G1 없음; `obs_tools_gates` 4개(`b70a05a` code 35·`0ef7430` test 35·`dd01d1d`·`8b1f929` 34) | n 35 → 36, 35 행·게이트 커밋 2개 추가 |
| watch | **W1 PASS**(메인 status 전후 같음), **W2 FAIL·W3 FAIL -- 출처 = 이 실행 밖(Phase 2 브리핑 §2 (다) 다른 주체)**: 실행 중(stamp 15:16:15 이후) 메인 저장소에 오케스트레이터 문서 커밋(`Role: doc`) 4개가 들어왔다 -- `b4734cd`(15:21, `.ai/context.md` 백로그 이관), `8b64a84`(승인 기록 `20261001-b26-phase3-cards`), `298089b`(B34 `references/analog-grammar-integration.md`), `7243f28`(B34 spec card). W2 = 그 네 커밋의 reflog 줄(350 → 354줄, 넷 다 `commit:`), W3 '지정 1' = `skills/analog-gmid-design/references/analog-grammar-integration.md`(`298089b`가 바꾼 파일). kit은 메인에 `git -C` 읽기만 하고 쓰기는 `C:/g285` 아래뿐이다. 복제본 reflog clone → H → (P2D ↔ H) 3왕복 → H, 끝 status 0줄 | v1은 모두 PASS(그때는 동시 커밋 없음) |

**v2 뒤 사정(이 초안의 기준 밖, 공식 실행 전 다시 잴 것)**: 위 watch 출처의 네 커밋으로 gate `master`가 `7243f28`로 옮겨졌다(이 작업 끝 시점 `rev-parse gate/master`). 그 결과 C4(`20261001-b26-phase3-cards` H 트리에 있음)와 C1(`git grep -l -E '^phase: 3$' 7243f28 -- docs/02-design/specs` = 1장, `20260930-b34-grammar-explicit.spec.md`)이 `7243f28`에서는 달라진다(`missing`도 줄어든다) -- 이 초안의 수치는 `fd4ef8c` 기준이다.

### 8.1 v1 재실행 (모래상자 `C:/g245`, 2026-10-02 16:54~17:35, 끝에 삭제 -- r1 kit `run_dod.sh /c/g245 4a286f0 rehearse` 그대로, 복제 `-c core.autocrlf=false`, TMP/TEMP = `C:/g245/tmp`)

**공허 PASS였던 항목이 이제 PENDING이다. 나머지는 v0(아래 8.2)·독립 검토 재실행(`C:/g236`)과 같다.**

| 단계 | v1 결과 | v0 대비 |
|---|---|---|
| guard / inputs | G1 PASS, G2 INFO(역할 브랜치 수는 진행 중 card에 따라 달라지는 진행 상황이지 고정 수가 아니다 -- 이 실행 2개 `role/audit/20260930-v3-changed-stmt-scope`·`role/test/…`, 독립 검토 r1 재실행 때 3개(`role/audit|code|test/20260930-v3-changed-stmt-scope`, 35 진행 중); 공식이면 0이어야 하고 아니면 멈춤), G3·G4 PASS(블록 sha256 5개 같음), G5 `missing` 28 | 같음(역할 브랜치 수만 진행 상황에 따라 다름: v0 1 → v1 2 → r1 검토 3) |
| e01 | `E0 FAIL present 1/10`, **`E1 PENDING(E0 미충족 -- 공허, 판정 아님) exit=0 findings=0`** | **E1 PASS → PENDING** |
| e2 | PENDING, 기계 리허설 V3 `H^..H` exit 0, 키 5개 없음 | 같음 |
| e3 / e3b | 세 shim `E3 FAIL` 3줄, 거부 확인 rc 0 stmt 69·call 9·파일 67(제외 1), `E3 FAIL: 제외 집합 밖 importer 66파일` / `LIVE 0 0 1` + `E3b INVALID` | 같음 |
| e4 / e6 | PENDING / PENDING | 같음 |
| ia | `tried=5 expected=5 failed=0`, 종료 0 | 같음 |
| e5pt | PT3 exit 0 1047 passed·15 xfailed(359.70 s) / `--gmid-dod` exit 0 1047 passed·15 xfailed(345.85 s) | 같음(시간만) |
| e5lib | 10회 exit 0, `E5 INVALID` 없음, E-INST 두 회로 같음, E-LIB 9회로 같음, **rails 계약 FAIL 9 → `E5 E-LIB/E-INST FAIL`** | 같음 |
| n63 | `1 PASS(n=35) \| 2 FAIL(0/20) \| 3 FAIL \| 4 PENDING(n=0, 어긋남 0, 덮음 누락 0, 경로 밖 0) \| 5 FAIL`; 관찰 0.5: 34 `PNNNNNNNNP` audit·merge 행 검사 True, 35·B33·G1 없음 | **4 PASS → PENDING** |
| watch | W1·W2·W3 PASS. 복제본 reflog clone → H → (P2D ↔ H) **3왕복** → H, 끝 status 0줄 | 같음 |

판별력 대조(v1 추가)는 §6(합성 입력 `C:/g245/jt`, N6.3 Phase 2 재현 `C:/g245/n63p2`). 메인 저장소: HEAD `4a286f0`, `status --porcelain --ignored`(175줄)·reflog(345줄)가 실행 전 스냅숏과 같음(kit W1·W2와 별도 대조), stamp 이후 파일 0.

### 8.2 v0 (모래상자 `C:/g228`, 2026-10-02 14:33~15:17, 끝에 삭제 -- 실행기 `phase3_dod_kit/run_dod.sh … rehearse` 그대로)

환경: `git clone -q --no-hardlinks --no-local -c core.longpaths=true` 21 s, origin 제거, `checkout --detach 4a286f0fad4f9beafd26647e1f95a89086e07919`, status 0줄, `TMP`/`TEMP` = `C:/g228/tmp`, cwd `C:/g228`, Python 3.14.2.
H = `gate/master` = `ls-remote gate` = `4a286f0`(G1 PASS), 역할 브랜치 1개(G2 -- 공식이면 멈춤), G3·G4 PASS, G5 `missing` 28.

| 단계 | 결과 | 소요 |
|---|---|---|
| guard / inputs | 위 | 6 s / 28 s |
| e01 | E0 FAIL 1/10, E1 exit 0 findings 0(v0 실행기는 `E1 PASS`로 찍음 -- v1에서 PENDING) | 2 s |
| e2 | PENDING + 기계 리허설(V3 키 5개 없음) | 94 s |
| e3 / e3b | §5 4·5행 | 105 s / 43 s |
| e4 / e6 | PENDING / PENDING | 1 s / 1 s |
| ia | `tried=5 expected=5 failed=0`, 종료 0 | 9 s |
| n63 | 1 PASS(35건) · 2 FAIL(0/20) · 3 FAIL · 4 PASS(0개 -- 공허, v1에서 PENDING) · 5 FAIL | 13 s |
| n63 판별력(Phase 2 재현) | §6 마지막 행 | 73 s(E5 PT3 실행과 겹침) |
| e5pt | `PT3` exit 0 **1047 passed, 15 xfailed**(pytest 292.84 s) / `PT3 --gmid-dod` exit 0 **1047 passed, 15 xfailed**(343.29 s) -- xfailed 같음(관찰 1: phase 3 IC 표식 0) | 11분 6초 |
| e5lib | 10회 실행 모두 exit 0. 동등 확인 통과(`E5 INVALID` 없음 -- P2D에서 `e_inst_p3` = `e_inst_df36`, `e_lib_p3`(MASK 없음) = `e_lib`). `E5 E-INST current_reuse_telescopic_ota 같음`·`folded_cascode 같음`(`without_topology_ref_sha256` crt `185b675e…50e51ca`·fc `0ca6746f…cda754`, raw crt `2fc426d9…eb863d`·fc `ef3cd996…c9bb3f0` -- 세 실행 같음, Phase 2 DoD 표의 값과 같음). `E5 E-LIB(rails 뺀 해시) 같음 (9 회로)`, 해시 `1d2e3bf6…b7a8f`(4회 같음 = phase2-dod.md E-LIB 값). **`E5 E-LIB rails 계약 FAIL` 9줄**(HEAD·P2D 모두 `<ABSENT>` -- B26-1 미병합이라 기대대로; 기대 nets(P2D library): vdd/gnd 6회로, nmcnr vdd/vss, pushpull·sf_pushpull vdd/vss/agnd) → **`E5 E-LIB/E-INST FAIL rails:…`** -- 계약값 판정이 실제로 거부함(판별). 사본 sha256: e_inst_p3 `7d26134a…25e283`, e_lib_p3 `c6b82fc7…aa140e`, e_inst_df36 `6cc48495…f09510`, e_lib `41b72d7d…68ee9` | 24분 6초(crt 1판 6분~7분 28초, fc 1판 약 1분 10초) |
| watch | W1 메인 status 전후 같음 · W2 메인 reflog 전후 같음 · W3 stamp 이후 파일 0(지정 경로·루트) -- 모두 PASS. 복제본 reflog clone → H → (P2D ↔ H 3왕복 -- 회로마다 1 + E-LIB 1, v0의 '4왕복'은 오기) → H, 끝 HEAD = H | 1 s |

## 9. design 30 §10과의 어긋남·확인 요청 (기준을 바꾸지 않는 절차 사항 -- 공식 실행 전 오케스트레이터 판단)

(v1: 1·2는 design 정정 D4·D1로 넘겼다 -- `_drafts/design30_dod_corrections.md`. v2: 정정 D1~D4가 `7f67ec3`으로 design에 들어가 1·2는 **해소**. kit 동작은 정정 판과 같고 정정 전후 판정 블록 sha256 5개·줄 범위도 같다(`fd4ef8c` 재추출, §2).)

1. **`GC`** -- **해소(정정 커밋 `7f67ec3`, D4: design 786행 `GC="<05 §4.4 캐시: git archive <H> tools/gates를 <iso> 밖…>/tools/gates"`, PT3도 같은 `$GC`)**. 아래는 v1 당시 기록: design 블록은 `GC="$ISO/tools/gates"`이고 같은 블록의 E5 `fresh "$P2D"`가 `<iso>`를 P2D로 옮긴다. `P2D..4a286f0`에 `tools/gates` 커밋이 2개(34 면제 묶기) 있으므로 P2D 판 `tools/gates` ≠ H 판이다 -- E5 뒤에 `$GC`를 쓰는 명령이 오면 다른 판 게이트로 돈다. design 주석이 허용하는 캐시(`05` §4.4) 쪽으로, 실행기는 `git archive H tools/gates`를 `<iso>` 밖(`$G/cache_<H>`)에 둔다(Phase 2 DoD와 같은 방식). 판정 영향 없음.
2. **`fresh()` 순서** -- **해소(정정 커밋 `7f67ec3`, D1·D2·D3: design 1034행 `fresh()`가 먼저 지우고 옮긴 뒤 HEAD·status를 확인하고 실패면 `E5 INVALID: 판 전환 실패 $1`, 호출은 `&&`·`|| exit 1`, E6 `--head "$H"`)**. 아래는 v1 당시 기록: design은 `checkout --detach "$1" && checkout -- . && clean -fdx`이다. 직전 E-INST가 추적 `workspaces/*/…instance.json`을 바꾼 상태에서 두 판의 그 파일이 다르면 `checkout --detach`가 거부되고 `&&` 때문에 뒤가 건너뛰어진 채 스크립트가 **이전 판에서** 돈다(HEAD 확인 없음). 실행기 `to_h`는 먼저 `checkout -- .`·`clean -fdx` 후 `checkout --detach`, 그리고 HEAD = 대상·status `--ignored` 0줄을 단정한다(Phase 2 브리핑 §2 판 바꾸기 규칙). `P2D..4a286f0`에는 그 파일 변경이 없어 리허설에서는 차이가 드러나지 않는다.
3. **card 목록 범위**: 지시문의 목록(T0·FU·G1·D0a·D0b·M1~M9·F1·F2 + B34·b26pre·backfill·B26-1·B33)에 비해 design §8(card 수 17)은 **M10**(`p3-mod10-entry`, red-green)과 **T1**(`p3-test-relocate`, test-only -- 둘 다 초안 `draft_p3_m10.spec.md`·`draft_p3_t1.spec.md`(2026-10-06), id `20261006-p3-mod10-entry`·`20261006-p3-test-relocate`)을 더 가진다 -- 이 초안은 design대로 둘을 넣었다(`^phase: 3$`이면 N6.3-2가 어차피 센다). **B33·G1**은 `phase: 0.5` 게이트 card라 `^phase: 3$` 목록(20장) 밖이고 C2·관찰 2로만 다룬다.
4. **E2 ① 키**: `4a286f0` 판 V3 출력에는 `defs`·`move_rejected`·`moved`·`not_targeted`·`targets_by_def`가 없었다. **v2 `fd4ef8c`(35 병합 뒤)**: `not_targeted`·`targets_by_def`가 생겼고 이름이 design과 같다(35 몫 확인 완료). `defs`·`move_rejected`·`moved` 셋은 아직 없다 -- G1 판정 기록 뒤 다시 잰다(design §10 E2 행 "출력 키가 바뀌면 이 행을 다시 잰다"). v4: 시제품에서 다섯 키 이름 = design 이름(M10 모의 V3-RESULT, `m10_t1_open_items.md` 'M10 V3' -- 판정 기준 아님). `move_plan check` 출력 키(`findings` 종류 11개(`import-dup` 포함 -- D0a 계약 4 v8.4), `moved_defs`·`moved_units`·`assigned`)는 D0a 초안 계약 4 문언에서 읽었다 -- D0a 병합 뒤 확인. v4r(검토 v4 m-c): 같이 확인할 것 -- `check` `findings.changed` 원소의 단위 id 표기가 `--allow-changed` 표기(저장소 상대 `<경로>::<qualname>`, design E6·`judge_p3.py` `E6_ALLOW`)와 같은지. D0a 계약 2 `plan` 단위 id는 `<A 기준 파일>::<키>`이고 계약 4 단계 예는 `A/h.py::run`(A 약어)라, `changed`가 A 기준으로 나오면 판정기는 E6 INVALID(fail-closed, 거짓 PASS 없음 -- 검토 v4 합성 29)로 공식 실행이 멈춘다.
5. **IMPORT-ANY 위치**: design 블록은 `import_any`를 E4 뒤·E5 앞에 둔다. 실행기는 `ia` 단계로 같은 자리에서 H 판으로 돌린다(판정 영향 없음).
6. **N6.3-4 경로**(v1 확정, 검토 §1·§5-5): Phase 2 DoD의 세 pathspec에 D-27 동결 범위 `tools/migrate/*`를 더했다 -- **기준 강화**(Phase 2 재현 수 불변 31, `da03c0e..4a286f0`의 `tools/migrate/*` 커밋 0개, D0a code 커밋이 목록에 들어와 N6.3-4가 D0a를 실제로 본다). 사용자 확인 불필요. `tools/gates`는 넣지 않는다 -- Phase 3 기간 게이트 card(0.5: 34·35·B33·G1)의 정당한 변경이 Change-Id ∉ phase 3 목록이라 거짓 FAIL이 되고, 그 커밋은 관찰 3(`obs_tools_gates`)이 trailer로 따로 본다. 결과 '절차 메모'에 둘 다 적는다(§10).
7. **결정 기록 C4**: `20261001-b26-phase3-cards`가 아직 H 트리에 없다 -- 네 card의 첫 문서 커밋 전에 들어가야 한다(card 머리 `approval:`이 가리킨다).

## 10. 결과 파일 `_drafts/phase3_dod_result.md` 형식 (phase2-dod.md 머리를 따른다)

```
# Phase 3 완료 조건(DoD) 측정 결과 (auditor 원본 -- 오케스트레이터가 phase3-dod.md로 옮김)
대상: 측정 커밋 H = DoD 착수 때의 gate `master` = `<H>`(제목 '<H 제목>'). F2 판정 기록 커밋 = `<…>`, P2D = `<P2D>`, B0 = `<B0>`(M1 기록), MPC = `<MPC>`(D0a 기록). 측정 주체 = gmid-verification-auditor(독립 측정, <날짜>).
기준: design 30 §10(v8.5 6c8287f + 정정 7f67ec3, 승인 20260930-30-module-split-design), 계획 N6.2 Phase 3 행(H 판 줄 번호 -- fd4ef8c 1020행)·N6.3, 결정 20261001-b26-phase3-cards.
환경: 격리 복제본 C:/g<N>/iso, cwd C:/g<N>, Python/pytest 버전, 게이트 캐시 = git archive <H> tools/gates, design 블록 sha256 5개. 메인 저장소 쓰기 0(status·reflog 전후 동일, stamp 이후 파일 0).
## 판정
판정: <PASS|FAIL>
| ID | 조건(N6.2) | 판정 | 측정 결과 |   -- E0, E1, E2, E3, E3b, E4, E5, E6
## 판별력 대조   (§6 표)
## N6.3 공통 조건   (1~5, phase 3 기록 20건 표: card·id·evidence_type(기록)·V1~V10·audit 커밋·merge 커밋·base/test/code 조상; 0.5 card 줄)
## 남긴 관찰(PASS, 차단 아님)   (§7 1~6)
## 절차 메모   (브리핑과 기준의 어긋남, 스크립트 sha256·blob id, 단계별 소요(timeline.txt), 복제본 reflog/status)
              필수 두 줄(v1): ① "N6.3-4 pathspec의 `tools/migrate/*`는 이 브리핑이 더한 경로다(D-27 동결 범위, 기준 강화 -- Phase 2 재현 수 불변 31).
              `tools/gates`는 0.5 게이트 card의 정당한 변경이라 넣지 않고 관찰 3으로 본다." ② "N6.3 검사기 판별력 대조의 Phase 2 재현은 **수치** 재현이다
              (phase=2 모드에 Phase 2 브리핑의 예외 목록이 없어 2번은 FAIL로 찍힌다 -- 판정 일치를 주장하지 않는다)."
              r2 추가 두 줄(검토 r1 m2·m3, ③은 v4에서 nomerge로 바꿈): ③ "N6.3-4 목록은 `--no-merges` 없이 뽑는다(nomerge, 2026-10-06 사용자 승인). 엔진 경로 내용이 자동 병합과 다른 merge(evil -- merge에서만
              바뀐 내용·충돌 해결·부모 3개 이상)는 trailer와 무관하게 어긋남이고, 자동 병합과 같은 merge(clean)는 `merges_clean`에 적기만 한다. 남는 사각(`review_nomerges` m4):
              충돌을 한 부모와 TREESAME으로 해결한 merge는 기본 simplification이 그 부모만 따라가 반대편 커밋이 목록에 나오지 않는다 -- 그 내용은 H 트리에 없다.
              EL4(`merge_gate.py` 'M 트리 = M^2(code 끝) 트리', 1147~1148행)는 그대로 병합 내용을 막는다. merge-tree 객체는 임시 객체 디렉터리에만 쓰지만 복제본에 이미 있는
              loose 객체의 mtime이 갱신될 수 있다(복제본 한정, 메인 무관 -- `review_nomerges` m3)." ④ "덮음 대조의 `diff-tree`는 `-m`·`--root`가 없어 병합 커밋·부모 없는 커밋을 '경로 밖'으로
              잘못 분류한다. 받아들여진 기록에서는 생기지 않는다: EL4가 `code_commit == K`(1198행, K = 병합 아닌 `Role: code` 끝, 1163~1164행)를
              강제하고 부모 없는 커밋은 1094~1095행에서 거부한다. test_commit이 병합(사슬 없는 equivalence의 T = M^1 = old)이면 그 내용은 그 병합의
              EL4 통과로 덮인다."
## 범위 밖 메모
종료: <날짜 시각>, 항목 E0~E6·N6.3 1~5·판별력·관찰 1~6 전부 기록.
복제본: HEAD = <H>, reflog 이동 clone→H→P2D→H(E5 판 바꾸기 횟수), status <…>.
메인: HEAD = <실행 전과 같은 해시>, status 차이 0, reflog 차이 0, stamp 이후 파일 0(지정 경로·루트).
```

FAIL이 나오면 고치지 않고 원출력 경로와 함께 적고 나머지를 끝까지 잰다. 판정 기록·spec card·승인·문서를 만들거나 바꾸지 않는다.

## 11. 오케스트레이터 (auditor 보고 뒤 -- Phase 2 `2eefda1` 절차와 같음)

결과 파일을 다시 계산하지 않고 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/phase3-dod.md`로 옮겨 문서 커밋(`Role: doc`, 제목 'docs: Phase 3 완료 판정 기록(DoD, H = <H> -- …)') → `.ai/context.md` Python 바이너리 append(`git diff --numstat` 삭제 0줄) → push 단독 실행·전체 출력 확인 → 그 뒤 `C:/g<N>` 삭제. 이 커밋이 Phase 4 design 착수 조건("이전 Phase DoD PASS", 계획 N6.1)의 인용 대상이다.

## 12. 시간 예산 (리허설 실측 + design·Phase 2 기록 인용)

| 단계 | 근거 | 예산 |
|---|---|---|
| 가드 + 복제 + 입력 | 리허설 21 s + 6 s + 28 s | 2분 |
| E0·E1 / E3 / E3b / E4 / IMPORT-ANY / E6 / N6.3 | 리허설 2 / 105 / 43 / 1 / 9 / 1 / 13 s(E4·E6은 도구 없음 -- 공식 값 아님) | 각 3분 |
| E2(M card 8건 V3 재실행 + check) | design §2.3·M행: G1 이동 제외로 card마다 V3 대상 def 0이면 변이 0 → 기준선 실행만(리허설 H^..H 94 s) | card당 3분, 합 30분 |
| E5 PT3 / PT3 --gmid-dod | 리허설 292.84 s / 343.29 s(1047 passed·15 xfailed -- 공식 H는 card test가 더해져 늘어난다) | 각 12분 |
| E5 E-INST(crt 3회·fc 3회) + E-LIB 4회 | 리허설 24분 6초 | 40분 |
| **전체(직렬)** | | **약 100분** |
