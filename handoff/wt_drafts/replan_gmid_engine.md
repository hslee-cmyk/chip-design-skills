# gm/ID 엔진 중심 재계획 -- 기존 test 폐기 허용 규칙의 일정 효과 (조사, 2026-10-07)

읽기 전용 조사다. 저장소·게이트·다른 초안은 바꾸지 않았다(이 파일만 새로 씀).
사용자 목표(원문, 2026-10-07): "난 gmid로 아날로그 설계하는데 필요한 엔진을 원해. 모든 테스트는 다시 작성해도 돼. 기존에 있는 테스트를 활용할 수 없으면 버려. 이 계획으로 줄어든 시간이 얼마일지 계산해서 알려줘."
기준: gate `master` = `6df4bd7`. 기준 일정(baseline)은 `_drafts/whole_plan_schedule.md`(같은 날 다른 agent, 15:53)의 §3.3 표를 그대로 쓴다 -- 이 문서는 baseline을 다시 계산하지 않았다.
**(추정)** 표시가 없는 수치는 실측이나 기록 인용이다. 추정에는 식을 함께 적는다.

입력: 계획 N1·N3.10·N3.11·N4.2·N6.1·N6.2(gate), design 05·10·30(gate), `_drafts/phase3_runbook.md`, `v3_options_schedule.md`, `whole_plan_schedule.md`, `draft_phase4_design.md` §5·§7.4·§8.4, `draft_p3_t0.spec.md` 의도 절, `approval_20261007-b26-v4-*.md`, `user_decisions.md`, `tools/gates/weakening_diff.py`(gate), gate test 트리, 현재 세션 jsonl의 Agent 호출 445건 설명(scratchpad `agent_desc.txt`).

---

## 0. 결론 먼저

* 이 규칙(기존 test를 지키지 않고 버리고, 엔진 test는 계약 기준으로 새로 쓴다)만으로 줄어드는 시간은 **중앙 약 75 h(활동일 약 7, 달력 약 12일), 낙관 축 약 36 h(달력 6일), 비관 축 약 152 h(달력 26일) -- 전체의 약 7~8%**다(3절).
* 줄어드는 몫은 (1) Phase 3의 legacy 보존 card 3장(T0·T1·V4 강화)과 F1 두 번 시도, (2) Phase 4의 test 인프라 card 4장(B41·#3·#4·#5 TS4), (3) 이후 Phase에서 legacy test 때문에 끼어드는 card와 card 안 마찰이다. 대신 새로 쓰는 card(폐기 1장 + 엔진 핵심 회귀 test 재작성 3장)와 문서·승인 비용이 든다.
* 일정의 큰 몫은 이 규칙과 무관하다: card마다 붙는 검증·조율(바뀐 줄의 68%가 판정 기록, 22%가 문서, code 1.7% -- `whole_plan_schedule.md` §2.4), 아직 설계 안 된 5~7c(card의 63~71%), 활동일 비율 0.53~0.57. 더 크게 줄이려면 4절의 선택 항목(사전 승인 게이트 변경, 모듈 분할 보류)이 사용자 결정으로 필요하다.
* **게이트 도구는 고치지 않아도 된다.** 폐기 card를 '파일 통째 삭제'로만 하면 V5 diff 해시가 base blob만으로 정해져(`weakening_diff.py` 208~212행: head blob이 없으면 `-`) 승인 기록을 순서 0에 미리 커밋할 수 있다 → 두 번 시도 없이 한 번에 끝난다. 계획 표·design 문서 정정은 승인 기록 2건(plan_tables, design diff)이 필요하다.

---

## 1. 엔진 필수 범위 정의

### 1.1 엔진이 해야 하는 일 (계획 N1.1·N1.3, SKILL.md '이 skill의 목적')

"임의의 topology + spec이 주어지면 모든 소자(트랜지스터 + 수동소자)의 값을 확정한다"(SKILL.md 26행~). 계획이 정한 사슬:

| 단계 | 엔진 기능 | 계획 근거 | 담당 Phase | 모듈 |
|---|---|---|---|---|
| 1 | LUT 조회·보간·역산(gm/ID ↔ ID/W, VGS), LUT 메타·축 게이트 | FR-5, DF-27, U-27 | 4·6a(S0) | MOD1 |
| 2 | topology·spec 로드, 옛 키 거부, 레일 선언 접근 | FR-9, DEC-62·68·69 | 3(B26-1)·4·6a(MG2) | MOD2 |
| 3 | 구조 유도: signal stage·소자 구성·결합 블록·기둥(S1) | FR-1, DEC-43·71 | 6a | MOD3 |
| 4 | 소자 사이징과 노드전압 DC 정본(W 티어, 봉인) | FR-5·6, DEC-67 | 4(DF)·6b | MOD4 |
| 5 | 결합 잔차·달성가능성·DOF(탐색 전 불가 보고) | FR-8 | 6c | MOD4 |
| 6 | metric: 전체회로 MNA gain, 출력 임피던스, 전력·면적 축, SPICE 대조·모델 오차 | FR-2·6, DEC-72·78~80 | 7a | MOD5 |
| 7 | 보상 → gain 할당(층 0 + 외층 SLSQP), (전력, 면적) front | FR-3·4, DEC-70·71·73·77 | 7b | MOD6 |
| 8 | 결과 재사용·실패 캐시·시작점, 아카이브, SPICE `.op` 전 소자 | FR-7 | 5·7c | MOD6 |
| 9 | 단일 진입점 `run_gmid_design_pipeline(spec)`, instance.json·HTML 보고 | N3.10 MOD9·MOD10 | 3(M9·M10) | MOD9·MOD10 |
| 비기능 | 버그 free·조용한 실패 불가(NFR-1), 캐시·재계산 0(NFR-2), IC1~IC11 강제 test(NFR-3), 결정론(NFR-4), 스펙 맞춤(NFR-5) | N1.4 | 전 Phase | -- |

### 1.2 남은 일의 분류

분류: **E** = 엔진 기능·결함 수정(1.1 사슬에 직접), **I** = 엔진을 위한 게이트·구조 인프라, **L** = 기존(legacy) test를 보존·이전·강화하기 위한 일, **D** = 문서·DoD.

**Phase 3 남은 20장**(`phase3_runbook.md` §6~§16, `whole_plan_schedule.md` §1):

| card | 분류 | 이유 | 새 규칙에서 |
|---|---|---|---|
| B26-1 `20260930-b26-rail-accessor-set` | E | 레일을 이름 집합이 아니라 선언으로(DF-19·26, DEC-62 topology 무관) | **유지**(진행 중). V4 FAIL은 (가′) 면제로 처리(3.1 결정 D1) |
| V4 강화 `20261007-b26-v4-legacy-strengthen` | L | 이관 selftest 4개(s133·s134·s135·s159)의 판정 강화 -- 곧 버릴 test | **제외** |
| B33 `20260930-v7-registry-edges` | I(gate) | V7 거짓 FAIL 115 → 39, 거짓 PASS 64 → 0 -- 엔진 card의 배선 판정에 직접 영향 | 유지 |
| T0 `20260930-p3-tests-location-free` | L | 계약 test가 정의 위치를 가정하는 것을 고침(의도 절: `test_ic5` `_DOMAIN_TABLE`, `test_dup_w_calc:442`, `test_ts6_dead_probes`, `test_b26_rail_accessor`, selftest 3파일 import 7이름) | **제외** -- L1이 해당 test를 지우고 위치 무관 판을 새 파일로 씀 |
| FU `20261002-p3-future-annotations` | I | 이동 equivalence 전제 | 유지(모듈 분할 유지 시) |
| G1 `20260930-p3-gate-move-aware` | I(gate) | 이동한 def를 V3에서 빼지 않으면 M1 590·M2 302 변이 | 유지(모듈 분할 유지 시) |
| D0a·D0b | I | 이동 계획 도구·레지스트리 목적지 | 유지(모듈 분할 유지 시) |
| M1~M6·M8·M9(8장) | I | N3.10 모듈 구조(파일당 한 책임, import 계층) | 유지 권고(4.2 결정 D5) |
| M10 `p3-mod10-entry` | **E** | 엔진의 유일 진입점(MOD10) | 유지 |
| T1 `p3-test-relocate` | L | `unit/test_selftest_*.py`를 `unit/test_mod*.py`로 옮김 + V5 | **제외**(selftest를 L1이 지움) |
| F1 `20261002-p3-callers-update` | I + L | 추적 파일·workspaces 16파일 호출부(I) + TS6 (마) 핀 전환·B군 11 test import(L, V5 두 번 시도) | **축소 유지**: 호출부만, 한 번 시도 |
| F2 `20261002-p3-shim-delete` | I | shim 삭제, `sizing_recipe.py` 삭제(DoD 조건) | 유지(모듈 분할 유지 시) |
| Phase 3 DoD | D | -- | 유지(C1 card 수·E 단계 정정) |

**Phase 4 초안 49장**(`draft_phase4_design.md` §5):

| 묶음 | card | 분류 | 새 규칙에서 |
|---|---|---|---|
| test 인프라 | B41 `scope-note-test`(test-only, `save_instance_json` docstring 고정) | L | **제외**(필요하면 L2a가 보고 계약으로 흡수) |
| test 인프라 | #3 `pole-oracle-to-tests`, #4 `toy-lut-to-tests` | L(test 픽스처·oracle 이전) | **L2에 흡수**(새 test가 쓰는 픽스처로 같이 만든다) |
| test 인프라 | #5 `ts4-selfref-oracle`(TS4: 자기참조 기대값을 oracle로 교체) | L | **L2로 대체**(대상 test 자체를 버리고 oracle 기반으로 새로 씀) |
| 정리 | #2 `d4-delete-unwired` | D/E(죽은 함수 삭제) | 유지. `test_ic5` 표 V5 몫은 L1 뒤 사라짐 → 한 번 시도 |
| 실패 규약·측정 | #6~#16 | E(#7 CC-7a는 7b 구조 준비, #8·#9는 NFR-2·무동작 측정 도구) | 유지 |
| 레일 | #17~#22, #51, #19 lint, #20 CC-5 | E | 유지 |
| 노드전압·LUT·PDK·캐시·개별·배선·회로 | #23~#44, #47(B37a), #53~#55, 조건부 C1·C2·#49·#52 | E | 유지 |
| gate | #46 `b36-grammar-gate-scope` | I(gate) | 이 규칙과 무관 -- 백로그 후보(4.3, 선택) |

**Phase 5~7c**(미설계, `whole_plan_schedule.md` §1.1의 90/135/180장): 범위 항목은 전부 E다(1.1 표 3~8단계). 줄어드는 것은 범위가 아니라 **준비 중 끼어드는 legacy 대응 card**(b26pre·V4 강화·T0 같은 것)와 card 안 legacy 마찰이다(3.2).

### 1.3 실측: 지금까지 legacy test에 쓴 몫

* 병합 card(09-21~10-07, 판정 기록 39건, gate `git log --first-parent`): legacy test 이관·보존 card 약 15장(TS0~TS7, sections-merge, probe 4장, d-move-tests, p10, md-sync, b26pre), gate 9장, 엔진 쪽 정리·결함 약 13장. 새 gm/ID 기능 card는 0(`whole_plan_schedule.md` §2.4와 같은 결론).
* 현재 세션 Agent 호출 445건(09-30 18:08 ~ 10-07)의 설명 키워드 분류(scratchpad `agent_desc.txt`, 겹침 있음): T0·T1·t0_carry·T0-V4 32, b26pre 22, F1 23, TS6 6, B41 6, V4 legacy 2 → **legacy 보존 몫 약 80~95건 = 18~21%**. 그중 legacy card 전체(T0·T1·b26pre)가 약 54건(12%), 살아남는 card 안의 legacy 마찰(F1의 TS6·V5, B26-1 V4·dispute)이 약 25건(**약 6%**).
* gate test 트리(6df4bd7): `unit/test_selftest_*.py` 4파일 212 test·7,758줄(TS1 이관본, 원 `if __name__` 블록), 이관·과정 고정 meta test(`test_ts6_*`·`test_ts3_no_print_verdicts`·`test_d_move_tests`·`test_phase2_stale_refs`·`test_restore_plan_functions`·`test_d_delete_*`·`tooling/test_extract_selftest` 등) 약 140 test.

---

## 2. 새 규칙 아래의 재계획

### 2.1 원칙 (바꾸지 않는 것)

* 역할 분리(작성자 ≠ 검증자, test-author는 소스 열람 금지), EL1~EL4, V1~V10, 한 번에 변경 하나 -- **그대로**. 사용자 규칙은 "기존 test를 보존할 의무"를 없앨 뿐 "기준 약화는 승인"(DEC-40)이나 "자기참조 금지"(V4)를 없애지 않는다.
* 폐기는 **사용자 승인 1건**으로 한 번에 한다(DEC-40 '매 건 승인'의 한 건). 새 test는 '추가'라 V5 발견이 없다(`weakening_diff.py` 머리 표 -- 삭제·감소·완화만 발견).
* **버리는 기준**: (가) 이관 selftest(자기참조 기대값·위치 결합·파일 전체 V4 FAIL의 원천), (나) 끝난 이관·삭제 단계를 고정하는 과정 meta test(엔진 동작을 판정하지 않음), (다) 정의 위치를 가정하는 계약 test(위치 무관 판을 같은 card에서 새 파일로). **남기는 것**: IC1~IC11 xfail 계약(NFR-3), `unit/test_probe_*`(물리 불변식, Phase 2 승격 -- 그대로 쓸 수 있음), 최근 card의 엔진 동작 계약(`test_b34_*`, `test_b26_backfill_*`, `test_df35/36_*`, `test_dup_*`, `test_ic3`), 운영 도구 test(`test_reg_check*` -- DF-23 스캐너는 Phase 4 #39·7b가 씀), auditor E-INST·E-LIB 대조 키트.

### 2.2 새 card와 순서

| 순서 | 항목 | 판정 유형 | 내용 | 승인 |
|---|---|---|---|---|
| 1 | B26-1 1차 → 운반 → 2차(진행 중 그대로) | red-green | V4 FAIL 4 test는 **(가′) 면제**(초안 `approval_20261007-b26-v4-exempt.dropped.md` 되살림)로 처리, V4 강화 card는 만들지 않는다 | 결정 D1(오늘 답 "(다)"를 되돌림) |
| 2 | **R0** 문서 슬롯(역할 브랜치 0) | -- | 계획 DEC-82 신설(legacy test 보존 의무 없음, 엔진 회귀는 계약 test가 지킴), N3.11 TS4 행 → L1·L2 행, N6.1 Phase 4 범위 첫 줄 'TS4 →' 삭제, N4.2 V2 test-only 판정에 '폐기 대응표'(지운 test마다 '승인된 폐기' 또는 '대체 test id') 문구, design 30 §7.1·§8.1 ORDER에서 T0·T1 삭제와 F1 범위 축소, design 10 TS4 주석, `tests/README.md` | plan_tables 승인 1 + design 30 diff 승인 1(UD-0 승인이 '추가 표 개정은 다시 묻는다'고 했음) -- 질문 한 번에 묶음(D2) |
| 3 | **L1** `legacy-test-disposal` | test-only, **한 번 시도** | 파일 통째 삭제만: selftest 4파일, 과정 meta test 파일들, 위치 가정 계약 test 파일(T0 A군·F1 B군 중 엔진 동작을 판정하는 것은 같은 test 커밋에서 **위치 무관 새 파일**로 다시 씀 -- 규칙 R-DEF, design 30 §7.1). V5 diff 해시 = 삭제 경로의 base blob만으로 정해짐 → 순서 0에 승인 기록 커밋. auditor V2 = 폐기 대응표 전수 대조 | V5 diff 승인 1(D3, 목록 제시) |
| 4 | B33 → FU → G1 → D0a → D0b → M1~M6·M8·M9 → M10 → F1(축소) → F2 → Phase 3 DoD | 기존 | T0·T1 없음. F1 = 호출부만(test 쪽 V5 없음 → 한 번 시도). DoD C1 '20장' → 18장, E 단계의 T0·T1 참조 삭제 | 기존 승인 그대로 |
| 5 | **L2a** 엔진 핵심 회귀 test | test-only(추가만), 한 번 시도 | MOD1·MOD4: `solve_id_for_target_gm`(s006)·`solve_diode_stack_current`(s007)·`search_gm_id_for_role`(s021)·`ro`(s022)·VGS(s040)·`noise_1f_density`(s056)·`estimate_mismatch_sigma`(s059)·`_nmcnr_stage1_rout`(s063)·보상(s052, topology_library s004·Cgg)을 **독립 oracle**(폐형식·문헌·손계산 리터럴)로. #3 pole oracle·#4 toy LUT 픽스처를 여기서 만든다 | 없음(추가) |
| 6 | **L2b** 구조 유도 회귀 test | 같음 | MOD3: `find_diode_stacks`(s099·s100)·`trace_*_branches`(s126·s128)·`find_differential_pair_candidates`(s130)·`find_verified_*`·`refine_differential_and_mirror_relations`(s129~s139)·`suggest_vertical_stack_composites`·`_propose_vertical_stack_ids` -- library 회로의 손 판독 대조표(oracle (d))로. 6a S1의 출발점 | 없음 |
| 7 | **L2c** 파일럿 전체회로 통합 test | 같음 | `optimize_full_circuit_budget`(s012·s036·s037·s051)·`run_topology_pipeline*`(s011, SD s089·s090)를 `integration/`(N3.11)으로. DEC-56 픽스처 규칙(`r_cmfb_vocdes` 하한 0.02, `stop_after_sizing=True`)을 그대로 옮김 | 없음 |
| 8 | (조건부) **L2d** 레이아웃 회귀 test | 같음 | MOD7·MOD8: common-centroid·interdigitate·floorplan·`repair_matching_safety`·finger geometry(SD s021~s116). #41 `euler-repair-wire`나 7b MOD8 수렴 루프(LR9) 착수 전 | 없음 |
| 9 | Phase 4 이후 | 기존 | 각 엔진 card의 red-green test가 그 함수의 계약을 새로 고정. b26pre 같은 '변경 전 고정' test-only card는 따로 만들지 않고 그 card의 test 커밋에 넣는다 | 기존(DEC-40 건별) |

L1을 B26-1 **뒤**에 두는 이유: B26-1의 1차 V3 기대값(변이 299, 생존 1 = U3)과 2차 '기대 생존 0'은 지금 test 집합(legacy selftest 포함)으로 잰 것이다. 2차 전에 test를 지우면 죽던 변이가 살아 V3 FAIL → 3차 시도가 될 수 있다(무거운 V3 1회 2.1/4.3/5.5 h, `v3_options_schedule.md` §1.1).

### 2.3 바꿔야 하는 계획·게이트 규칙 (전수)

| 규칙 | 바꿈? | 내용 | 필요한 것 |
|---|---|---|---|
| DEC-40 / V5(`weakening_diff.py`) | **아니오** | 폐기 = 승인 1건. 삭제 전용 card는 해시를 미리 계산 | L1 V5 diff 승인 기록 1 |
| V1 전체 실행 | 아니오 | 지운 id는 base에만 있음 -- V1은 병합본 전체 PASS만 본다 | -- |
| V2 test-only 판정 | **예(문구)** | '섹션→test 매핑표' 규칙을 폐기 card에 쓰도록 '승인된 폐기' 항목 허용 | 계획 N4.2 문구 → plan_tables 승인(R0) |
| V3 | 아니오 | 단, test가 줄어 변이가 덜 죽음 → 각 card가 자기 test로 죽여야 함(3.2 g) | -- |
| V4 자기참조 lint | 아니오 | 새 test는 V4를 통과해야 함. legacy 파일 전체 lint FAIL 원천이 사라짐 | -- |
| N3.11 test 구조·TS 단계표 | 예 | TS4 행 → L1·L2. `legacy/` 행 삭제(이미 빈 디렉터리면 문구만) | doc(R0) |
| N6.1 Phase 4 범위 'TS4 → …' | 예 | 첫 작업을 L2a~c로 | plan_tables 승인(R0 -- N6.1은 게이트가 읽는 표) |
| N2.1 결정 레지스터 | 예 | DEC-82 추가(사용자 원문 인용) | doc + 사용자 결정 기록(D2) |
| design 30 §7.1·§8.1·§9.2 | 예 | T0·T1 삭제, F1 범위, '뒤에 올 승인: T1·F1' 삭제 | design diff 승인(R0) |
| design 10 TS4 | 예(주석) | 대체됨 표시 | doc |
| Phase 3 DoD 초안·키트 | 예 | C1 20 → 18장, T0·T1 참조 단계, E6 `--allow-changed` 확인 | 초안 개정(검토 1회) |
| Phase 4 design 초안 | 예 | #3·#4·#5·B41 삭제, L2a~c 추가, #2 V5 몫·§7.4 `test_ic5` 줄 삭제 | 초안 개정(아직 미승인 -- 승인 질문에 포함) |
| N1.4 NFR-3 IC 강제 test, EL1~EL4, 역할 표 N3.12.2 | 아니오 | -- | -- |
| (선택) V5 사전 승인 | 게이트 변경 | 4.1 | gate_change card + 사용자 승인 |

---

## 3. 줄어드는 시간

### 3.1 Phase 3 (card 목록이 설계돼 있음)

단가는 `v3_options_schedule.md` §3.1의 card 종류별 범위(일반 1.5~3.5 h, 두 번 시도 3~6 h)와 `whole_plan_schedule.md` §3.2(V4 강화 2.5/4/7 h). O/M/P = 낙관/중앙/비관(중앙 = 범위 중간값, 추정).

| 항목 | O | M | P | 근거 |
|---|---|---|---|---|
| V4 강화 card 제외 | −2.5 | −4.0 | −7.0 | whole_plan §3.2 |
| T0 제외(두 번 시도 test-only) | −3.0 | −4.5 | −6.0 | v3_options §3.1 'T0 3~6' |
| T1 제외(두 번 시도 test-only) | −3.0 | −4.5 | −6.0 | 같음 'T1 3~6' |
| F1 두 번 시도 → 한 번(일반 card) | −1.5 | −2.5 | −2.5 | 'F1 3~6' → 일반 '1.5~3.5' |
| R0 문서·계획·DoD 키트 정정 + 승인 질문 | +2.0 | +4.0 | +8.0 | (추정) 문서 커밋 2~3개 + DoD 키트 개정(그 초안은 검토 6회째 -- 비관 폭 큼) |
| L1 폐기 card(목록 작성 포함) | +2.5 | +4.5 | +7.5 | (추정) 일반 card 1.5/2.5/3.5 + 목록·대응표 1/2/4 |
| B26-1 (가′) 면제 기록 되살림 | +0.3 | +0.5 | +1.0 | (추정) 초안 있음(`*.dropped.md`) |
| **Phase 3 합** | **−5.2** | **−6.5** | **−5.0** | |

card 수: 20/20/21 → **18/18/19**(−T0·T1·V4 강화, +L1).
반영 안 한 상방: L1 뒤 test 수가 약 1,129 → 약 780(추정 −350: selftest 212 + meta 약 140)으로 줄어 V1·M10 V3가 빨라진다. 재지 않았으므로 셈에 넣지 않았다.

### 3.2 Phase 4~7c (식)

* **c** = card 수 감소 비율(legacy 대응 card의 몫). 실측 근거: Phase 4 초안 4/49 = 8%(B41·#3·#4·#5), Phase 3 3/23 = 13%(T0·T1·V4 강화), Phase 3 창 B26 계열 2/5 = 40%(b26pre·V4 강화 -- 표본 작음, 상한 참고). 중앙 **8%**, 범위 4~13%.
* **f** = 살아남는 card 안의 legacy 마찰 비율. 실측 근거: 세션 Agent 호출 중 살아남는 card의 legacy 마찰 약 25/445 = 5.6%(1.3). 중앙 **6%**, 범위 3~12%.
* **g** = 새로 생기는 비용 비율: legacy test가 공짜로 죽이던 변이를 각 card의 새 test가 죽여야 하고(V3), 회귀 test가 L2 전까지 얇다. (추정) 중앙 **3%**, 범위 2~5%. 순 마찰 감소 **f − g = 3%**(범위 −2% ~ +10%).
* Phase 4: card 49/52/54 − 4(B41·#3·#4·#5) + 3(L2a~c) [+1 L2d 비관] = **48/51/54**. 시간 = (card 변화 × h) + (f − g) × 남은 card × h. h = 2.5/4.0/7.0 h/card(whole_plan §3.1).
* 5~7c: baseline card 90/136/180 × (1 − c) = **83/125/166**. 시간 = 줄어든 card × h + (f − g) × 남은 card × h.

| Phase | O | M | P | 식 |
|---|---|---|---|---|
| 4 card | −2.5 | −4.0 | 0 | (−4 + 3) × h; P는 L2d 포함 −4 + 4 |
| 4 마찰 | −3.6 | −6.1 | −11.3 | 0.03 × (48·2.5 / 51·4 / 54·7) |
| 5~7c card | −18.0 | −43.5 | −100.8 | 0.08 × (90/136/180) × h |
| 5~7c 마찰 | −6.2 | −15.0 | −34.8 | 0.03 × (82.8·2.5 / 125.1·4 / 165.6·7) |
| **4~7c 합** | **−30.3** | **−68.6** | **−146.9** | |

### 3.3 전체 비교

| | baseline O / M / P | 재계획 O / M / P | 줄어든 몫 O / M / P |
|---|---|---|---|
| card 수 | 159 / 208 / 255 | **149 / 194 / 239** | 10 / 14 / 16 |
| 작업 시간 h | 425 / 953 / 2,110 | **390 / 878 / 1,958** | **35.5 / 75.1 / 151.9**(8.4% / 7.9% / 7.2%) |
| 활동일(÷10.5 h) | 40.5 / 90.8 / 201.0 | **37.1 / 83.6 / 186.5** | 3.4 / 7.2 / 14.5 |
| 달력일 | 73 / 167 / 399 | **67 / 155 / 373** | **6 / 12 / 26** |
| 사용자 질문 | -- | +1회(D1~D3 묶음) | -- |

달력 식(whole_plan §3.1과 같음): 활동일 / 활동일 비율(0.57 / 0.57 / 0.53) + baseline의 달력 추가분(2.0 / 7.7 / 19.8일, baseline 달력 − 활동일/비율로 역산) + 새 질문 대기 0 / 0.5 / 1일(추정).
달력 환산(오늘 10-07 기준, 추정): 낙관 약 12월 중순 → **12월 초~중순**, 중앙 약 2027-03 하순 → **2027-03 초**, 비관 약 2027-11 → **2027-10 중순**.

**민감도**(중앙 baseline에 c·f−g 범위를 넣음, 추정): (c 4%, f−g −2%) → 약 **18 h(달력 3일)** / 중앙(8%, 3%) → 75 h(12일) / (13%, 10%) → 약 **149 h(25일)**. 가장 큰 변수는 '5~7c에서 legacy 대응 card가 몇 장 끼어들었을까'(c)다.

---

## 4. 이 규칙 밖의 더 큰 선택지 (사용자 결정, 셈은 3절과 따로)

### 4.1 V5 사전 승인 게이트 변경 (선택 D4)
* 무엇: `weakening_diff.py`가 `target_kind: units` 승인(경로·test 단위·패턴, 그리고 새 기대값)을 test 커밋 **전**에 받아 대조. 지금은 diff 해시가 test 커밋 뒤에만 정해져 V5가 걸리는 card는 두 번 시도한다(B26-1·T0·F1·#2·b26pre 선례).
* 횟수: Phase 4 초안 §7.4의 DEC-40 예정 건 약 12 + 이후 Phase(동작 변경마다 E-INST 해시·θ*·기대값) → 4~7c 15 / 22 / 30회(추정).
* 1회당 추가 시도 비용: b26pre 실측 4.4 h − 일반 card 중앙 1.0 h = **3.4 h**(gate 이력), 범위 2~6 h.
* 효과: 15·2 / 22·3.4 / 30·6 = 30 / 75 / 180 h − gate card 비용 2 / 4 / 8 h(v3_options §1.4 gate card 선례) = **순 28 / 71 / 172 h**(추정).
* 약화 쪽 위험: 승인이 정확한 diff 바이트가 아니라 (단위, 패턴, 새 값)에 묶인다. 새 값을 승인에 적게 하면 은폐 여지는 작지만, redteam 공격(승인 밖 단위·다른 값)을 새로 증명해야 한다. 게이트 변경 = 사용자 승인 필수(N3.12.2).

### 4.2 모듈 분할(M1~M9·FU·G1·D0a·D0b·F2) 보류 (선택 D5 -- 권고: 유지)
* 남은 비용(v3_options W 범위 합, T0·T1 제외): 약 24 / 41 / 59 h. 보류하면 Phase 4 초안의 'P3? = Y' card와 CC-7a(MOD8 → MOD6 추출)를 다시 맞춰야 함(4 / 8 / 16 h, 추정) → 순 약 20 / 33 / 43 h.
* 유지 권고 이유: 초안·키트가 이미 다 있고(검토 끝), G1 뒤 M card V3는 분 단위, 6a S1(MOD3)·7b(MOD6)이 새 코드를 넣을 자리, 12,013줄 `sizing_recipe.py`에 새 기능을 더하면 나중 분할이 더 비싸짐. M10(진입점)은 엔진 필수라 어느 쪽이든 유지.

### 4.3 gate·인프라 card 백로그 (규칙 밖, 참고)
* #46 B36(게이트 범위), `--jobs/--resume` V3 card -- memory '인프라 작업은 gmid 엔진을 막을 때만'에 따라 막힐 때만. 셈에 넣지 않음.

---

## 5. 버릴 때의 위험 -- 다시 써야 하는 것

| legacy test | 지키던 엔진 동작 | 버리면 | 처리 |
|---|---|---|---|
| `test_selftest_sizing_recipe.py` s012·s036·s037·s051(`optimize_full_circuit_budget`), s011(`run_topology_pipeline_with_finger_fixup`) | **파일럿 전체회로 사이징 -- 유일한 전체회로 통합 test**(DEC-56 픽스처) | 동작 변경 Phase(4~)에서 전체회로 회귀를 못 봄 | **L2c 필수**(Phase 4 첫 동작 변경 전) |
| 같은 파일 s006·s007·s021·s022·s040·s056·s059·s063, `test_selftest_topology_library.py` s004·Cgg | gm/ID 역산·diode 스택·역할별 gm/ID 탐색·ro·VGS·잡음·mismatch·보상식 | 핵심 수식 회귀 | **L2a 필수**(독립 oracle로) |
| `test_selftest_stick_diagram.py` s099~s140(`find_diode_stacks`, `trace_*_branches`, `find_*differential*`, `refine_*`, `_propose_vertical_stack_ids`) | 구조 유도(미러·차동쌍·diode·기둥) -- B26-1·6a가 바꾸는 곳 | 6a 전에 구조 회귀 공백 | **L2b 필수** |
| 같은 파일 s021~s116(common-centroid, interdigitate, floorplan, `repair_matching_safety`, finger geometry, euler) | 레이아웃·사이징↔레이아웃 수렴 | #41·backfill류·7b LR9에서 회귀 공백 | **L2d 조건부**(그 card 착수 전) |
| s009 `revalidate_finger_override`, s015·s016 matching finger growth | finger 재검증 | 같은 공백 | L2d에 포함 |
| `test_selftest_design_report.py` 4개 | 보고서 표 조립 | 보고 회귀(엔진 수치 아님) | 버림 -- M9·MOD9 card가 계약 test로 |
| 과정 meta test(`test_ts6_*`, `test_ts3_*`, `test_d_move_tests`, `test_phase2_stale_refs`, `test_restore_plan_functions`, `test_d_delete_*`, `tooling/test_extract_selftest`) | 끝난 이관 단계·삭제 상태 고정 | 지운 죽은 코드가 되살아나도 못 봄 | 버림 -- V7 배선 게이트·레지스트리가 대신. 엔진 동작 판정 없음 |

공통 위험:
* **L1 ~ L2c 사이 공백**(Phase 3 이동 card 구간): 이동은 AST 해시 동일 + auditor E-INST·E-LIB 대조로 판정되므로 공백의 영향은 작다. 다만 그 사이 **동작을 바꾸는 card는 두지 않는다**(L2a~c를 Phase 4 첫 동작 변경 card 앞에 둔다).
* **V3 변이 생존 증가**: legacy test가 넓게 죽이던 변이를 card마다 새 test로 죽여야 한다(3.2 g). L1을 B26-1 뒤에 두는 이유이기도 하다.
* **IC 계약·물리 불변식은 남긴다**: IC1~IC11(NFR-3), `unit/test_probe_*`(gm/ID 단조성, LUT L 보간, 기생 PM, 재검증 범위) -- 버리지 않는다.
* **다시 쓴 test의 독립성**: 기대값을 지금 엔진 출력에서 베끼면 그것이 자기참조다(V4가 놓치는 손 리터럴 포함 -- N4.2 V4 끝 문단). L2는 oracle 종류·출처를 spec card에 적고 auditor가 대조한다(기존 규칙 그대로).

---

## 6. 사용자 결정 필요 항목

| id | 질문 | 기본안 | 영향 |
|---|---|---|---|
| D1 | B26-1 V4: 오늘 고른 "(다) 4 test 강화 card"를 "(가′) 면제"로 되돌리는가 (4 test는 L1에서 버림) | 되돌림 | V4 강화 card 제외(−2.5/−4/−7 h) |
| D2 | DEC-82(legacy test 보존 의무 없음, 엔진 회귀는 계약 test) + 계획 N3.11·N4.2 V2·N6.1 Phase 4 문구 + design 30 T0·T1 삭제·F1 축소를 승인하는가 | 승인 | plan_tables 승인 1 + design diff 승인 1 |
| D3 | L1 폐기 목록(파일 단위, 2.1 기준 (가)(나)(다))을 승인하는가 -- 목록은 L1 spec card 작성 때 제시 | 승인 | V5 diff 승인 1(해시 미리 계산, 한 번 시도) |
| D4 | (선택) V5 사전 승인 게이트 변경을 하는가 | 묻기만(권고 없음 -- 약화 쪽 위험 있음) | 순 28 / 71 / 172 h(추정) |
| D5 | (선택) 모듈 분할을 유지하는가 | 유지 | 보류 시 순 20 / 33 / 43 h(추정), 나중 비용 증가 |

D1~D3은 질문 한 번(AskUserQuestion 3문항)에 묶을 수 있다. 그 밖(L2 test 범위, 순서)은 원칙 기본안이라 묻지 않는다.

## 7. 불확실성
* baseline 자체(5~7c card 수 r, card당 h)가 외삽이다(`whole_plan_schedule.md` §5). 이 문서의 절감은 그 위의 비율이라 같은 불확실성을 물려받는다.
* c·f·g는 표본이 작다(세션 Agent 호출 키워드 분류 -- 설명 문자열만 봄, 겹침 있음; Phase 4 초안 card 표). g는 실측 근거 없는 추정이다.
* L1 뒤 test 수·V1/V3 시간 감소는 재지 않았다(상방, 셈 밖).
* L2a~c의 실제 크기(다시 써야 할 판정 수)는 L1 목록을 만들 때 정해진다. 크면 card가 늘어 절감이 준다.
