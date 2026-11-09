# gain-budget-gmid-sizing -- Phase 4 `40-defect-fixes` design

> **[초안 v0.3 -- 저장소 미반영]** 정식 경로(계획 N9.1): `docs/02-design/features/gain-budget-gmid-sizing.40-defect-fixes.design.md`(현재 없음).
> 측정 시점 = gate `master` **`7535799`**(2026-09-30). v0.2는 `cd64170`에서 쟀다. `git diff --stat cd64170 7535799 -- skills workspaces`는 **빈 출력**이고 바뀐 것은 `tools/gates`(B28 V3 이력 복제본: `mutate_changed.py`, redteam 공격 31)뿐이다. 그래서 v0.2의 엔진·하네스 사실(줄 번호 포함)은 HEAD에서 그대로 성립한다.
> 저장소·worktree 쓰기 0, git 상태 변경 0. v0.3 재측정 스크래치 `C:/g48`(HEAD `git archive` 사본 + `m.py`·`reach.py`·`appc*.py`·`runall.sh`, 끝나면 삭제). 발견별 변경 대응은 `phase4_revision_log.md`. v0.2 원본은 `draft_phase4_design.v02.md`.

버전 v0.3(초안). v0.3 변경(독립 검토 `review_phase4_design.md` 반영):
* blocking 4건: MG1의 nmcnr 전압을 원점 이동 동등값으로(B1), IC11 rail2 판정식·선행·대상 회로 교체와 감도 전파 허용오차 card(B2), N9.1 필수 내용(`fallback_events` 스키마·계측 지점 전수, I-C11 해소 설계, 인터페이스 5건)을 §10·§11·부록 C로(B3), B35 방식을 UD-15에 묶은 사용자 결정으로(B4).
* should-fix·minor: Phase 3 초안 **v3** 기준 모듈 배치, 의존 간선, UD-2·UD-3 질문 삭제, UD-13을 게이트 변경 card로, 나머지는 revision log.

정본 인용 규칙은 계획 N9.4 -- 이 문서는 계획서·`00-common`·`05`·`10`·`20`·Phase 3 초안(`30-module-split` **v3**)의 정의를 재서술하지 않고 절 번호로 인용한다.
읽은 계획 절(N9.1 `40-defect-fixes` 행): N5.2 전체, N3.6, N3.10, N3.14, N3.16, N4.1 IC11, N4.2 V3·V4·V8, N6.1·N6.2 Phase 4, N6.3, N0.4(106·124행), `00-common` §6·§7·§10·§11·§14·§18, DEC-40·47·51·60·61·62·69·70·71·76, I-C11, U-04·05·09·25·26·27·30. N9.2 필수 절 대응은 부록 B.

**표기 규칙(이 문서 전체)**
* **[재측정]** = v0.2 때 `cd64170`에서 다시 잰 사실(엔진·하네스 변경 0이라 HEAD에서도 같다).
* **[재측정 v0.3]** = 이번에 `7535799` 사본(`C:/g48/repo`)에서 잰 사실(부록 A).
* **[prep]** = 입력 준비 문서의 실측 인용. card 작성 전 실측(card 처리 속도 규칙)에서 다시 잰다.
* **[미확인]** = 실측 근거가 없는 문장. 착수 전 확인 대상이다.

**입력 문서**(`C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/`): `prep_phase4_scope.md`, `prep_b26_supply_nets.md`, `draft_b26_1.spec.md`, `draft_b26_plan_patch.md`, `b26_decision_table.md`, `prep_u27_u30.md`, `prep_deferred_rows.md`, `backlog_additions.md`, `user_decisions.md`, **`draft_phase3_design_v3.md`**(v0.2의 v2를 교체), `prep_b34_b35_grammar.md`, `review_b26_1.md`, (v0.3) `review_phase4_design.md`.
**아직 없는 입력**: `v3_scope_systemic.md`(V3 전신 변이 비용 측정) -- v0.3 작성 시점에도 `_drafts/`에 없다(ls 확인). §8.4의 Phase 4 전반 수치만 [미확인]으로 남는다. v0.3에서는 V3 범위 문제를 decision이 아니라 게이트 변경 card #48로 다루므로(§5.12) 이 입력은 더 이상 결정을 막지 않고, #48의 비용 근거 자료로만 쓰인다.

---

## 1. 목표와 범위

### 1.1 목표

Phase 4는 **동작을 바꾸는 첫 Phase**다. 계획 N5.2가 Phase 4에 배정한 결함(DF)을 red-green으로 고치고, 이후 Phase가 쓰는 공통 기반(N3.14 실패 규약, 옛 키 게이트, 성능·무동작 계측 도구)을 먼저 깐다. 끝나면 (1) 엔진이 실패를 삼키지 않고 N3.14 클래스와 exit code로 드러내며 (2) 레일·PDK 상수가 선언 한 곳에서만 오고(이름 집합·사본 0) (3) 조용한 폴백이 `fallback_events`로 계측되어 정본 실행에서 0이고 (4) 사이징 대상 회로의 전후 비교표가 판정 기록으로 남는다.

### 1.2 계획 원문

N6.1 Phase 4 행(계획 1001행):
> | 4 | TS4 → DF-35 → DF-36 → `00-common` CC-4의 앞부분(실패 클래스·`FailureRecord`·`exit_code_for`와 DF-37의 하네스 `run()` 몫) → CC-7·CC-8(측정·무동작 도구가 이후 card에 쓰이도록 Phase 4 앞쪽에 둔다) → 나머지. Phase 4 전체 범위: TS4, DF-01~15·18~20·22~24·26·27·35~37, **DF-34의 Phase 4 몫**(회로별 `_spec_*()`이 따로 복사한 PDK 상수 제거 -- 함수 자체를 데이터 항목으로 바꾸고 삭제하는 것은 7b다), MG1 레일 이름 변경(DEC-69), U-27 LUT 재생성, PDK 상수 한 곳 선언(U-30), Phase 2에서 배선을 고른 함수 배선, `fallback_events` 계측(V8), 기존 4개 회로 실행 가능성(I-C11), IC11 활성 | red-green | U-04, U-05, U-09, U-26, U-27 | `40-defect-fixes` |

N6.2 Phase 4 완료 조건(1019행):
> DF마다 red-green, V8 도입(정본 실행 `fallback_events` 0), 사이징 대상 회로 실행과 전후 비교표, IC11 2레일 케이스 PASS, MG1 옛 키(계획 `supplies`, spec 스칼라 `vdd` 선언, metric 인자 `supply_nets`) 거부 test PASS, DF-27 VS 축 밖 픽스처 거부, U-27 재생성 LUT의 옛 격자점 값 대조 기록(다르면 원인 보고, 기준선 변경은 DEC-40 승인), U-30 PDK 상수 교체 전후 self-test·사이징 대상 회로 비교표(`min_finger_w` = difftap.2 출처 기록, 바뀌는 기준선·기대값은 DEC-40 승인)

N9.1 `40-defect-fixes` 행(1158행, 반드시 담을 것 요지): DF별 red 형태와 수정 범위, N3.14 실패 클래스 도입, tol_V 함수 선도입, U-04·U-05, **`fallback_events` 스키마와 계측 지점 전수**(→ §10.1, 부록 C), exit code, **I-C11 해소 설계**(→ §11), `supply_nets`·`supplies_v` 레일 판정(DF-19·26)·vsb(DF-24)·IC11, MG1, DF-27 축 커버리지 게이트, U-27 절차·대조, U-30 선언과 전후 비교, `00-common` CC-4·CC-5·CC-7·CC-8, DF-35·36.

N6.3(공통): "성능: Phase 4부터 매 Phase 보고", "동작 변경 Phase(4 이후)는 DEC-47 대상 구분대로 측정하고 필요 없는 회로의 무동작을 증명한다."

### 1.3 범위 안

| 항목 | 계획 근거 | card 묶음(§5) |
|---|---|---|
| TS4 자기참조 기대값 제거 | N3.11 561행 "4(첫 작업)" | 선두 |
| N3.14 실패 클래스·`FailureRecord`·`exit_code_for`, 하네스 exit code(DF-18 exit 몫, DF-37 하네스 몫) | `00-common` §7.1, CC-4 앞부분 | 선두 |
| θ 탐색부 추출·계측 인터페이스·성능 도구(CC-7), `activations_out`·무동작 도구(CC-8) | `00-common` §10·§11 | 선두 |
| DF-01~15, 18~20, 22~24, 26, 27, 37 | N5.2 담당 Phase 열 | 실패 규약 / 노드전압 / 캐시 / 레일 / LUT / 개별 |
| DF-34 Phase 4 몫(PDK 상수 사본 제거) + U-30 | N5.2, U-30(닫힘) | LUT·PDK |
| MG1(레일 **전압**: `supplies_v`, `vdd` 유도 함수, 옛 키 거부) + CC-5 | N3.16 802행, DEC-69, `00-common` §6 | 레일 |
| DF-19·DF-26 넷 몫(B26-1~B26-4) | N5.2, 계획 정정안 `draft_b26_plan_patch.md` | 레일(B26-1은 Phase 3 전 후보) |
| U-27 LUT 재생성·옛 격자점 대조(도구의 ngspice `Error:` 미검사 포함, #26 G7) | U-27(확정) | LUT·PDK |
| V8 `fallback_events`(스키마·지점 전수는 §10.1·부록 C) | N4.2 844행 V8 | 실패 규약(DF-14와 한 card) |
| I-C11(U-09) -- 실패 명시화(#43)와 해소(#44, UD-6) | 979·1084행 | 회로 |
| IC11 rail2 활성(대상 회로 = HEAD에서 끝까지 도는 2레일 회로, §5.4) | N4.1 829행 | 레일 |
| 보류 행 배선(Phase 2에서 '배선'을 고른 함수) | N6.1 | 배선·삭제 |
| `tests/probe_physical_consistency.py`의 레일 이름 집합 재구현 교체 | 사용자 결정 기록 2026-09-30 Phase 2 DoD D2("스캐너 범위 밖 rail-set 재구현 1건") | 레일(#17 test 커밋) |
| 백로그 B21(b)(c)·B24·B26·B34~B37 | `.ai/context.md` 14939행 외 [prep] | 노드전압 / LUT / 레일 |

### 1.4 범위 밖(명시)

* **이미 끝남**: DF-35(`34bc75e`), DF-36(`148bd6d`) -- 인용만 한다 [prep: `prep_phase4_scope.md` §0-2].
* **삭제로 해소**: DF-29 대상 5함수가 HEAD에 없다(P5b `d7bce7a`) [prep]. 계획 DF-29 행 닫힘은 계획 정정(§9).
* **다른 Phase**: DF-16·28·30(7a), DF-21(2), DF-25(6b), DF-31·33·DF-34의 함수 삭제 몫(7b), DF-32(6b·6c), IC11 rail3·reject(6a, `test_ic11.py` 표식 [재측정]), GB0 로드 게이트 일반형(6a), tol_V·tol_I를 쓰는 봉인 구현(6b), CGS·CGB 열의 **소비**(DF-28, 7a), U-36 수동소자 단위 면적 **값**(7b 전), SID_1F 잡음 metric 소비(7b 이후), `tol_I`(6b, P-3).
* **B21 (a)와 P3c 재착수**: `tol_I`가 6b이므로 P3c 재착수 위치 = 6b의 `tol_I` card 뒤. 조건 (b) `supplies_v`는 #21, (c) DF-02는 #23에서 Phase 4 안에 충족된다(§9-8).
* **U-25 실행 `SPECS` 이관**(agnd 두 회로 `sf_pushpull_output_opamp`·`pushpull_follower_buffer`, 그리고 `two_stage_ota_sf`): **범위 밖**. 조건 "DEC-60 구현 뒤"는 #1·#17·#21이 병합되면 Phase 4 안에서 성립한다. 그래도 넣지 않는 이유: (1) 이관은 사이징 대상 회로를 늘리는 스펙 데이터 추가이지 결함 수정이 아니고 N6.1 Phase 4 범위 문구에 없다 (2) agnd 3레일 회로의 IC11은 6a(rail3)다 (3) 넣으면 E1·E2 대상이 바뀌어 Phase 4 전후 비교의 기준 집합이 흔들린다. 이관 시점은 6a(IC11 rail3와 함께) 또는 7b(`sizing_spec.json` 이관)이고, 그 Phase design이 정한다.
* **인프라 백로그**(엔진을 막을 때만, 메모리 규칙): B29·B30·B31·B32·B33. v0.2가 여기 넣었던 `sky130_lut_sweep._parse_output`의 `Error:` 미검사는 **범위 안으로 옮겼다**(#26 G7 -- 이 Phase가 약 22시간 걸려 만드는 엔진 입력 LUT의 조용한 실패이므로 '엔진을 막는' 조건에 해당한다).
* **analog-grammar**: B34는 #45, B36은 #46, B37은 #47. **B35의 처리 방식은 UD-15에 묶은 사용자 결정이다**(§7.1). B29~B33·`_TEMPLATE`의 `supply_nets` 필드 부재(`review_b26_1.md` M2)는 인프라·문서 백로그.
* **`HINT_*` 이름 정규식의 바이어스 넷 추정**: `ports`에 바이어스 역할이 없어 B37로 대체되지 않는다. 새 백로그 **B38**(제안, §9-12)로 둔다.

### 1.5 계획과 HEAD가 어긋나는 곳(이 design이 전제하는 정정)

1. N6.1 앞머리 순서의 DF-35·DF-36은 완료 -- 실제 순서는 **TS4 → CC-4 앞부분 → CC-7·CC-8 → 나머지** [prep].
2. DF 위치 열 줄 번호가 낡았다(DF-26 "3882~3883·3147" → 3714·3715·2983 [재측정]). 이 design은 **함수 이름**으로 인용하고, Phase 3 뒤에는 D0b 이관표의 MOD 파일을 따른다.
3. U-27 "SID_1F 열 추가"는 열이 이미 있다 [재측정] → "새 VS 축으로 함께 재스윕"으로 읽는다. 계획 158행 문장도 낡았다 [prep].
4. DF-19 비고의 "29개"는 옛 스캔이다. 넷 판정 운영 함수는 AST 전수 SR 14 · SD 14(상수 3 별도)이고 `run_harness` 4는 전압 선언(MG1)이다 [prep].
5. 레일 넷과 레일 전압을 한 변경 단위(MG1)로 묶은 문구 → 넷(B26) / 전압(MG1) 분리. 계획 정정안 `draft_b26_plan_patch.md`.
6. (v0.3) DF-24 위치 열 "`derive_vsb_from_nodes`(sizing_recipe.py 3957행 참고)"는 3789행 [재측정]. 그리고 vsb의 조용한 `0.0` 기본값이 SR에 **31곳**(`.get("vsb", 0.0)`)과 `setdefault` 2곳(SR 7579 `ref_vds`, SD 4605 `0.0`) 있다 [재측정 v0.3, 부록 C.2] -- DF-01·DF-24 행이 이 사이트를 적지 않는다.

---

## 2. HEAD 사실 (재측정한 것만)

v0.2 명령: `C:/g36/remeasure.py`(cd64170). v0.3 명령: `C:/g48/m.py`·`reach.py`·`runall.sh`(7535799 사본). 표의 값은 그 출력이다.

| # | 사실 | 값 | 원 출처 | 비고 |
|---|---|---|---|---|
| F1 | 기준 커밋·design 문서 | HEAD `7535799`. design 4개(`00`·`05`·`10`·`20`), `40` 없음 | 검토 §4 | cd64170 이후 엔진·하네스 변경 0 [재측정 v0.3] |
| F2 | 레일 이름 집합 정의 위치 | SR `_DEFAULT_RAIL_HI/LO` 3714·3715, SD `_RAIL_NETS` 2983, SR `_rail_nets = frozenset(...)` 8003, MNA `fixed = {"gnd": 0.0}` SR 4086·4991 | `prep_b26_supply_nets.md` §1.1·§1.2 | 일치(검토 재측정도 일치) |
| F3 | 엔진이 `supply_nets`·`supplies_v`를 읽는 곳 | `"supply_nets"`: SR 4361 하나(metric 선언 키), SD 0. `"supplies_v"`: SR 0 | 같은 문서 | **엔진은 topology 최상위 `supply_nets`를 읽지 않는다** |
| F4 | 스칼라 `spec["vdd"]`·`.get("vdd")` 읽기(MG1 대상) | SR **20줄**: 1729, 3254, 4626, 4653, 7068, 7222, 7228, 7290, 7295, 7296, 7445, 7449, 7450, 8233, 8242, 8277, 8652, 10157, 10159, 10160 | `prep_phase4_scope.md` §3.4("21줄") | 8656은 오류 메시지 문자열. 7068은 `_hr_verify_group_kvl_sum`의 "직렬 VDS 합 = vdd" -- **레일 폭(hi − lo)으로 쓰는 읽기**다(§10.4) |
| F5 | 광범위 except 핸들러 수(DF-37) | SR `ValueError` 포함 26 · `Exception` 6 · `InfeasibleSizingError` 18, SD 4·0·0, 하네스 1·2·0 | `prep_phase4_scope.md` §3.6 | 일치 |
| F6 | 하네스 PDK·전압 사본 | `min_finger_w` 121 **`0.1e-6`**, 186·243·301 `1e-6` / `W_bounds` 117·172·241·297 / `L_min` 115·170·239·295 / `"vdd": 1.8` 105·142·234·288 / `min_vds_by_role` 118·173·242·300 | `prep_u27_u30.md` §3.1 | 일치 |
| F7 | 엔진 쪽 두 번째 정본(폴백 기본값) | `W_bounds` `(1e-6, 200e-6)` SR 11곳(1626, 1988, 2697, 2748, 3623, 5763, 6055, 6731, 7266, 7462, 8716), `spec.get("min_finger_w", …)` SR 9273, SD 기본 인자 5954·6043·6204 | `prep_u27_u30.md` §3.2 | 일치(부록 C.2의 `.get` 형태는 10곳, 1988은 다른 형태) |
| F8 | DF 대상 함수 정의 줄 | v0.2 표 그대로(`derive_vsb_from_nodes` 3789 … SD `load_topology` 8550). 추가: SD `_import_analog_grammar` 1045, `propose_device_roles_gap_fill` 3845 | `prep_phase4_scope.md` §3.5 | 일치 |
| F9 | 캐시·폴백 결함 지점 | `_QUERY_CACHE_MAX` 257·390(DF-07), `idu_up = 1.0` 3539(DF-11). `setdefault("vsb", …)` 문자열은 3813·3857·7407·7579에 있으나 **3813·3857은 docstring, 7407은 주석이고 코드는 7579 한 줄**(`other_entry.setdefault("vsb", ref_vds)`, `_hr_resolve_vertical_group`)이다 | 검토 F9 | **정정(v0.3)**: DF-01 원인 코드 = 7579 하나. AST로 세면 `setdefault("vsb", …)` 코드는 SR 7579 + **SD 4605**(`apply_device_roles_gap_fill`, `0.0`) 둘 [재측정 v0.3] |
| F10 | 표본 LUT | 키 = L·VGS·VDS·VS·`corner`·`temp_c`·{ID,GM,GDS,CGG,CGD,SID_1F}_{n,p}. CGS·CGB 없음. L 12점, VS = [0, 0.2, 0.4, 0.6, 0.8]. sha256 `753d802a…f177f` | `prep_u27_u30.md` §2.1 | 일치 |
| F11 | 착수 조건 승인 기록 | `.ai/approvals/` **42개**(HEAD, `b7d2570`이 1개 추가) 중 U-04·U-05·U-09·U-26·U-27·U-30·`40-defect`·B26 해당 **0** | 검토 F11 | 수는 HEAD 이동분 |
| F12 | 레지스트리 보류 표기 | `보류(Phase 3)` 9, `보류(Phase 4)` 14, `보류(Phase 6a)` 2 -- **표 행으로 세도 같다** | 검토 F12 | v0.2의 [미확인] 닫힘 |
| F13 | IC11 뼈대 | `tests/contracts/test_ic11.py`: `rail2` phase 4, `rail3`·`reject` phase 6a, 본문은 `pytest.fail()` 한 줄 [재측정 v0.3] | `prep_phase4_scope.md` §1.5 | 일치 |
| F14 | '자기참조' 표기 test | 판정 자기참조는 `test_selftest_sizing_recipe.py:1786` 하나 | `prep_deferred_rows.md` §1-2 | 일치 |
| **F15** | **하네스 정본 실행 4회로(HEAD 사본, `python run_harness.py <key>`)** | two_stage_ota: **`[FAIL] ValueError: 'stage1_out' 그룹의 VDS 합(2.37965V)이 vdd(1.8V)와 불일치(diff=+0.579654V)`** -- M4=0.9172(`vds_match_vgs_of` M6), M2=0.9(compensation), refs M5=0.5625, 36 s. nmcnr_amplifier: **`[FAIL] ValueError: 모든 theta 격자점이 infeasible`** -- 마지막 사유 `'stage2_diode_ref' 그룹(예산 1.5V, 미해결 ['M203'])… 0.525V를 배정할 곳이 없다… 구간 [M203∈[0.6375,0.975]]`, 36 s. folded_cascode: **끝까지 실행**(θ* `{'Ibg': 5e-07, …}`, `instance.json` 저장, `audit_ok=False`·`floorplan_ok=False` 그대로 저장), 단독 43 s. current_reuse_telescopic_ota: **끝까지 실행**(SLSQP 3 start, `instance.json` 저장, `audit_ok=False`), 4회로 병렬 중 411 s. **네 경우 모두 프로세스 exit code 0**(DF-18) | [재측정 v0.3] `C:/g48/run_*.log` | v0.2 E2의 [미확인] 닫힘. two_stage 실패 문구는 I-C11 known-limitation test(`test_selftest_sizing_recipe.py:2437` 'stage1_out'·'KVL')와 같다 |
| **F16** | IC11 대상 후보의 DF-24 검출력(source가 선언 레일이 아닌 NMOS) | folded_cascode 2(M7·M8), current_reuse 12 [재측정 v0.3] | -- | 원점 이동에서 DF-24 nmos 분기(`v`를 그대로 반환)가 발동한다 |
| **F17** | 조용한 폴백 후보 전수(엔진 `A/*.py` + 하네스) | 예외를 다시 던지지 않는 except 핸들러 **59**(SR 47·SD 5·하네스 3·도구 4), 운영 도달 52. `.get(<문자열 키>, <리터럴>)` **112**(스칼라·튜플 77 + 빈 컨테이너 35). `setdefault` 49(그중 선언 값 기본값은 vsb 2). SD analog-grammar `None` 폴백 직접 12·전파 9(= `prep_b34_b35_grammar.md` §1.2, 줄 번호 HEAD 동일) | [재측정 v0.3] 부록 C | §10.1의 계측 지점 전수 근거 |
| **F18** | `test_ic5`의 표-함수 대조 | `missing = set(_DOMAIN_TABLE) - found_keys` → **표에 있는 함수가 없으면 FAIL**, 표에 없는 함수는 형식만 검사, `len(_DOMAIN_TABLE) == 21` [재측정 v0.3] | 검토 S5 '미측정' | D-5 표 행을 먼저 지우는 것은 안전, 함수를 먼저 지우면 FAIL(§5.9 #41) |
| **F19** | CC-5 깊은 복사 관용구 `json.loads(json.dumps(x))` | 엔진 모듈 AST 계수 **0**(`json.load(s)` 9곳 모두 파일 읽기) [재측정 v0.3] | 검토 S12 | `00-common` §14 CC-5 행 "AST 계수가 0이면 해당 없음" → 해당 없음 |
| **F20** | `sky130_lut_sweep._parse_output`(196~227행) | ngspice 출력의 `Error:` 줄을 검사하지 않는다. 검사는 파싱된 점 수(`len(id_v) != n`)뿐 [재측정 v0.3] | `prep_u27_u30.md` §2.2 | #26 G7 |
| **F21** | topology `ports` 모양 | library 9/9가 `{넷: {role, direction}}`. role 값 = `differential_input_n/p`·`single_ended_input`·`differential_output_n/p`·`single_ended_output`. `_TEMPLATE`에는 `ports` 키가 **없다**(검토의 'null'이 아님) [재측정 v0.3] | 검토 S8 | #47 |
| **F22** | 레일 이름 문자열 상수(AST `Constant`, 대소문자 그대로) | SR `vdd` 26·`VDD` 3·`gnd` 6·`GND` 2·`vss` 3·`VSS` 2, SD `vdd` 17·`gnd` 17·`vss` 1, 하네스 `vdd` 4 [재측정 v0.3] | -- | #19 lint 기준선(base FAIL 입력) |
| **F23** | `install.py` `SKILLS` | 27~29행에 `analog-grammar` 없음 [재측정 v0.3] | 검토 S4 | #45 병합 선행 사용자 작업 |
| **F24** | `derived_spec` 사용처 | `workspaces/run_harness.py`, `tests/contracts/test_restore_plan_functions.py` [재측정 v0.3] | 검토 M6 | #50·#29·#51이 변형 spec을 이것으로 만든다 |

**재측정하지 않고 인용하는 핵심 사실**(모두 [prep], card 작성 전 실측 대상): v0.2 §2 뒤 목록 그대로(U-27 도구 비트 재현, 구조 규칙 극성 9/9, CMRR 73.14488 → 73.38009, B26-1 scratch, 보류 행 25개, B34 재현, B35 사용처 12(운영 8)와 9회로 `RAILS∩넷 = supply_nets∩넷`, B26-1 검토 B1·B2·S1·S3).

---

## 3. card 묶음, 순서, 의존

### 3.1 Phase 3 모듈 파일과의 관계 (Phase 3 초안 **v3** 기준)

계획상 Phase 4 착수 = Phase 3 DoD PASS 뒤(N6.1 공통). 아래 MOD 표기는 `00-common`이 정한 목적 모듈이거나 Phase 3 v3 §6.2 A-3 계산 결과다. **최종 파일은 D0b 이관표**(Phase 3 v3 §8 D0b)가 정한다.

| card | 필요한 모듈 | 근거 |
|---|---|---|
| CC-4a·CC-4b | MOD2(`SchemaRejectedError`·`FailureRecord`), MOD4(N3.14 예외·`FAILURE_CLASSES`·`exit_code_for`) | `00-common` §7.1 |
| CC-5, MG1 | MOD2(`LEGACY_NAMES`·`load_json_checked`) | `00-common` §6.1 |
| CC-7a·CC-7b | **MOD8에서 추출해 MOD6으로**(Phase 3 v3 D-3: `optimize_full_circuit_budget`의 Phase 3 위치는 MOD8, 탐색부 추출 뒤 MOD6), MOD10(`instrument`) | `00-common` §10.1 435행, Phase 3 v3 A-3·D-3 |
| CC-8 | MOD10(`activations_out`) | `00-common` §11.2 |
| DF-02(tol_V) | MOD1 | 계획 N3.6 |
| 로드 경로(`load_topology`) 수정 card(B26-1·B34·B26-2·B37) | **MOD3**(Phase 3 v3 A-3: 표 MOD2였으나 구조 자동채움을 불러 MOD3) | Phase 3 v3 §6.2 |
| W-1 `theta-order-gate` | **D0b 확정 뒤**. Phase 3 v3 A-3에 따라 `validate_theta_declaration_order`는 표의 MOD2가 아니라 `_build_shared_current_joint_plan`·`_shared_current_groups_from_compensation`의 MOD 이상으로 간다 | Phase 3 v3 §6.2 |
| analog-grammar 어댑터(`_import_analog_grammar` 등) | D0b 확정 뒤(`prep_b34_b35_grammar.md` §4의 'MOD2' 가정은 Phase 3 v3 A-3 이전 판이라 쓰지 않는다) | Phase 3 v3 §6 |
| 그 밖 DF card | 고치는 함수가 Phase 3 뒤 있는 MOD 파일 | D0b 이관표 |

MOD10 진입점 시그니처는 Phase 3 v3 §2.3(`run_gmid_design_pipeline(spec, *, topology_path, search, output_dir)`)을 받고 CC-7·CC-8이 `instrument`·`activations_out`을 더한다. Phase 3 초안이 승인 전이므로 이 연결은 **Phase 3 design 승인 뒤 확정**이다.

**Phase 3 design 쪽 교차 항목(같은 승인 묶음에서 정할 것)**: Phase 3 v3는 `cd64170`에서 D0b 원자료를 쟀다. 이 문서의 Phase 3 전 후보(#1·#45·#2·#3·#4)가 Phase 3 착수 전에 병합되면 D0b 이관표 원자료(정의 위치·참조 그래프)가 바뀐다. 그래서 Phase 3 design에 "Phase 3 전 병합 card 목록이 확정되면 D0b 작성 전 실측을 그 병합본에서 다시 한다"는 한 줄이 필요하다. 또 Phase 3 v3 D-10('보류(Phase 3) 9행은 옮기고 D 유지')과 이 문서 #2~#4(D-1~D-7 삭제·이관)는 대상 행이 달라 직접 충돌하지 않는다. 다만 #2~#4가 먼저 병합되면 Phase 3 이동 대상 수가 줄어든다.

### 3.2 Phase 3보다 먼저 할 수 있는 것

원칙 근거: 계획 N3.10 "등급 D 함수는 옮기기 전에 처리한다", 곧 지울 코드를 옮기지 않기 [prep: `prep_b26_supply_nets.md` §3.5].

| card | 앞당길 수 있는 조건 | 막히는 것 |
|---|---|---|
| **B26-1** `b26-rail-accessor-set`(#1) | (1) 계획 정정안 `draft_b26_plan_patch.md` 커밋(판정 표 무변경, N3.16 문구는 검토 S5대로) (2) P9 병합 뒤 base (3) **UD-14 decision 승인 기록** (4) **#48 V3 범위 게이트 변경 병합**(v0.2의 UD-13 decision을 대체, §5.12) (5) spec card 보강(검토 `review_b26_1.md` B2·S1·S4·B1-3) | 초안 있음, 검토 blocking 2건 |
| **B34** `b34-grammar-explicit-dependency`(#45) | 독립(B26-1과 파일이 겹쳐 순차). Phase 3에서 `_import_analog_grammar`를 옮기는 이동 card(D0b가 정하는 M 번호) **전**에 하는 것이 싸다 | **병합 선행 사용자 작업**: `install.py` `SKILLS`에 `"analog-grammar"` 추가(F23). 이것 없이 병합하면 설치본은 조용히 틀리던 것이 명시적으로 실패하는 상태가 된다 |
| **B26-4** `b26-rail-literal-lint`(#19) | 병합본에서 '운영부 레일 이름 리터럴 0'이 성립해야 red-green이 된다 → #17·#18·#21과 비운영 사이트 정리(D-6 #3, UD-7 결과 card, UD-9 면제)가 먼저 | UD-1, UD-7, UD-9, #21(스칼라 `spec["vdd"]` 키도 세므로, §5.4) |
| **d4-delete-unwired**(#2) | U-02 승인이 '보류(Phase 4 배선)'로 둔 행을 삭제로 바꾸는 것 -- UD-0으로 덮는다. **`test_ic5` `_DOMAIN_TABLE`의 D-4·D-5 두 행을 이 card에서 함께 지운다**(V5 1회, F18) | DEC-40 V5 승인 |
| **pole-oracle-to-tests**(#3) | 위와 같음. 계획 DEC-25·DF-06 문장 정정 동반 | #12·#19보다 먼저 |
| **toy-lut-to-tests**(#4) | test-only 이관 | Phase 3 F1과 묶어도 된다 |

B26-2·B26-3도 UD-1이 일찍 결정되면 Phase 3 전에 할 수 있다(편집 파일은 SR·SD 둘).

Phase 3 v3 §1은 "레지스트리 §2 '정본 후보'의 정본 확정(B26, Phase 4)"을 범위 밖으로 둔다. B26-1을 당기면 Phase 3 D0b의 `_RAIL_NETS` 목적지가 바뀌므로 **Phase 3 design 승인 전에** 당김 여부가 정해져야 한다.

### 3.3 순서

```
[Phase 3 전 후보]  plan-patch + UD-14 + #48(V3 범위 게이트 변경) ─> B26-1(#1) ;  B34(#45, 사용자 install.py 작업 뒤 병합) ;
                   d4-delete-unwired(#2), pole-oracle-to-tests(#3), toy-lut-to-tests(#4)
[Phase 3]          (30-module-split) ── DoD PASS
[Phase 4 선두, 순서 고정]
   TS4(#5) ─> CC-4a(#6) ─┬─> CC-7a(#7, equivalence) ─> CC-7b(#8, 계측·perf 도구)
                          └─> CC-8(#9, activations_out·noop 도구)        (00-common CC-8 행: "CC-4 앞부분 뒤")
   (TS4 범위는 D-1 결정에 기댄다. #2가 Phase 3 전에 안 되면 §9-9의 계획 정정)
[선두 뒤, 묶음끼리는 병렬 준비·순차 병합]
 실패 규약   CC-4b(#10) ; DF-03(#11) ; DF-06(#12) ; DF-14+V8(#13, #9 뒤) ; DF-18(#14) ; DF-11(#15) ; DF-12(#16)
 레일        B34(#45) ─> B26-2(#17, UD-1) ─> B37(#47)
             B26-2(#17) ─> B26-3(#18)
             CC-5(#20) ─> MG1(#21, nmcnr = {vdd 1.8, vss 0.0})
             {#17, #18, #21, #3, UD-7 결과 card, UD-9} ─> B26-4 lint(#19)
             {#21, #23} ─> IC11 판정기(#50, test-only) ─> DF-24+IC11 rail2(#22) ─> nmcnr ±0.9 전환(#51)
             (#17 ─> #22 : `derive_vsb_from_nodes` 기본 인자를 둘 다 고친다)
 게이트      B36(#46, UD-15 결과 형태) ;  UD-15 (2)=X이면 {#17, #46, #19} ─> B35 grammar 확장(#49)
 노드전압    DF-02(#23, +tol_V) ─> DF-01(#24, #22·#13 뒤)
 LUT·PDK     DF-27(#25) ─> U-27a(#26) ─> U-27b(#27) ─> U-30a(#28) ─> U-30b(#29)
             B24a(#30) ; DF-10+B24b(#31, #6 뒤)
 캐시        DF-07(#32) ; DF-13(#33, #6 뒤 -- U-27b와 독립) ; DF-15(#34)
 개별        DF-04(#35) ; DF-05(#36) ; DF-08+22(#37) ; DF-20(#38) ; DF-23(#39)
 배선        W-1(#40) ; W-2+D-5 함수 삭제(#41, #2 뒤) ; W-3(#42) ; (UD-7 결과) C1
 회로        I-C11 실패 명시화(#43) ─> I-C11 해소(#44, UD-6 결과)
[마감]       Phase 4 DoD(§6) -- 마지막 동작 변경 card의 perf.json, 전후 비교표
```

순서 근거:
* 선두 5건은 N6.1·`00-common` §11.1 고정. CC-8의 선행은 `00-common` CC-8 행("DF-35·36·CC-4 앞부분 뒤") 그대로 #6이다(v0.2 도식의 CC-7b ─> CC-8은 표와 달라 고쳤다). CC-7 병합 다음 동작 변경 card부터 perf 측정, CC-8 병합 다음부터 무동작 판정이 card마다 적용된다.
* **MG1(#21)은 nmcnr 전압을 원점 이동 동등값 `{vdd: 1.8, vss: 0.0}`으로 둔다**(계획 U-26 (a) "실행 spec은 스칼라 `vdd: 1.8`로 원점 이동 동등"). #21은 DF-24가 아직 고쳐지지 않은 엔진이라 음전위 레일을 넣으면 알려진 결함이 발동해 #21의 DEC-69 equivalence가 깨진다. 확정값 `{vdd: 0.9, vss: −0.9}` 전환은 **#22 병합 뒤 #51**이다(§5.4).
* #22의 선행 = #21(`supplies_v`), #23(`tol_V` -- IC11 허용오차의 입력), #17(`derive_vsb_from_nodes` 기본 인자를 #17도 고친다 -- 같은 함수 병합 충돌 방지), #50(판정기).
* DF-27 → U-27 → U-30: v0.2와 같다(U-27 선행 (1), 기준선 승인 한 번).
* CC-5 → MG1: 옛 키 게이트 공통 형식이 먼저(DEC-69 "같은 변경 단위"). CC-5는 CC-4a 뒤.
* D-1 결정 → TS4, D-6 → DF-06·B26-4: 지울 코드를 고치지 않는다.
* #13은 #9 뒤: §10.1-4 발동 규칙이 CC-8의 발동 계수로 지점별 처리를 가른다.
* #33(DF-13)은 #6 뒤. v0.2의 #27 선행은 뺐다: 내용 지문은 새 LUT가 필요 없고, E6의 '새 해시로 지문이 바뀜' 기록은 #33이 먼저 병합돼 있어도 U-27b가 할 수 있다. 캐시 card를 22시간 재생성 뒤로 직렬화할 이유가 없다.
* W-2(#41)은 #2(표 행 삭제) 뒤. `test_ic5`는 표 행의 함수가 없을 때만 FAIL하므로(F18) 표 행을 먼저 지우고 함수는 대체(W-2)와 같은 card에서 지운다.

### 3.4 파일 충돌 집합(준비는 병렬, 병합은 순차)

[Phase 3 뒤 모듈 이름은 D0b 확정 전. 아래는 Phase 3 v3 A-3 반영]
* 평가 커널 빌더(`_build_theta_evaluator`/`_evaluate`, MOD6): DF-03·DF-01·DF-02·DF-14·CC-7a·B26-2(8003행 `_rail_nets`)·W-1.
* **MOD8(`optimize_full_circuit_budget`의 Phase 3 위치)**: CC-7a(추출 원천), DF-18(θ* 기록), U-30a(9273 `min_finger_w`), DF-20.
* MNA(MOD5): B26-3.
* **로드 경로(`load_topology`, MOD3)**: B26-1·B34·B26-2·B37(`propose_device_roles_gap_fill` 포함).
* 옛 키·spec 로드(MOD2): CC-5·MG1.
* LUT(MOD1): DF-07·DF-13·DF-27·B24a·DF-10·DF-02(tol_V)·U-30a(공정 기록 로더).
* 하네스(`workspaces/run_harness.py`): CC-4a·CC-7b·CC-8·DF-18·MG1·U-30a·DF-20·#51.
* `_hr_resolve_vertical_group`·`_hr_verify_group_kvl_sum`(평가 경로): DF-14·DF-01·MG1(7068·7222~7450 스칼라 `vdd`)·#43.

### 3.5 한 card로 묶는 것(원칙)

| 묶음 | 근거 |
|---|---|
| DF-08 + DF-22 | 같은 함수, 계획 비고 |
| DF-14 + V8 계측 지점 | 계획 비고 "V8 계측 대상" |
| MG1 이름 변경 + 옛 키 거부 행 | DEC-69 "같은 변경 단위" |
| DF-02 + tol_V 함수 | N9.1 "tol_V 함수 선도입" + 만들면 배선(소비자 = DF-02 conflicts 판정) |
| DF-24 + IC11 rail2 활성 | IC11 원점 이동 불변 test가 DF-24를 검출하는 red(N4.1 829행). 판정기(감도 전파 허용오차)는 한 card 앞 #50에서 xfail strict로 먼저 실행된다(§5.4) |
| DF-10 + B24 (b) | 같은 뿌리 후보 [prep, 뿌리 동일은 [미확인]] |
| W-2 + D-5 **함수** 삭제 | vsid 감사의 유효 1건(`cmfb_tail`)을 W-2 배선이 대체 -- 대체와 삭제를 한 card에 [prep]. D-5 **표 행**은 #2(F18) |
| U-30 + DF-34 Phase 4 몫 + 엔진 폴백 15곳 | 개념 하나에 저장 위치 하나(DEC-68) |
| B26-2 + probe rail-set 교체 | `tests/probe_physical_consistency.py` 40행 `RAIL_HI, RAIL_LO = {"vdd","VDD"}, {"gnd","GND","vss","VSS"}`, 49행 `{"vdd": VDD, "gnd": 0.0}`, 126행 극성 판정 [재측정 v0.3] -- 극성이 필요하므로 #17의 test 커밋(test-author 경로)에서 `supply_nets` + #17 극성 읽기로 교체 |

---

## 4. 원칙을 계약으로 (모든 card의 spec card '관찰 가능한 계약'에 전 범위로 넣는다)

### 4.1 topology 무관 (DEC-62, 사용자 원칙 2026-09-30)

* 새 함수와 고치는 사이트에 **소자·넷·회로 이름 리터럴과 topology 경로가 없다**. 판정은 선언(`supply_nets`, `supplies_v`, `ports`의 `role`, `bulk`, metric 선언)과 구조 술어에서만 읽는다.
* 판정기: card마다 (a) **합성 topology**(선례 `test_d_delete_telescopic.py` `_SYN_RAILS = ["rail_hi","rail_lo"]`)에서 기대값이 나오고 (b) **역방향**: 선언에 없는 넷이 `vdd`·`gnd` 같은 이름이어도 레일로 취급하지 않는다.
* 변환 불변: 레일 이름 바꾸기·원점 이동(IC11) -- 되돌리면 같다(허용오차는 §10.6).
* **코드가 정하는 개수 상한 금지**: 레일 수·극성별 레일 수에 코드 상한을 두지 않는다(같은 극성 레일이 여럿인 회로 -- 예: 레벨 시프터 -- 도 데이터만으로 들어와야 한다, DEC-62). 상한이 생기는 방식은 사용자 결정(UD-15)으로만 채택하고, 채택하면 DEC-62 예외와 그 해소 card를 계약에 적는다.
* 전 범위 강제: B26-4 lint(§5.4 #19, PT 계약 test로 상시 실행), DF-23 Phase 4 행.
* 무동작 증명: 기능이 필요 없는 library 회로에서 발동 계수 0·산출물 동일(`00-common` §11, CC-8 뒤).

### 4.2 조용한 폴백 금지

* 선언이 없으면 거부한다: CC-4a 전에는 `ValueError`(메시지에 선언 이름과 DEC 번호), CC-4a 뒤 로드 거부는 `SchemaRejectedError`(exit 7), 탐색 중 실패는 N3.14 클래스.
* **기본값 없는 인자**: 레일·PDK·전압 인자를 이름 집합·리터럴 기본값이나 `None`→기본값으로 두지 않는다.
* 광범위 except는 N3.14 클래스와 `SchemaRejectedError`를 다시 raise한다(DF-37). 탐색 루프는 `CANDIDATE_FAILURE_CLASSES`만 이름으로 잡는다.
* 남기는 폴백은 전부 `fallback_events`에 기록한다(V8, 스키마·지점·처리 규칙은 §10.1). 정본 실행에서 0이어야 한다.
* 게이트는 **'실제로 거부한다'를 먼저** 보인다(조용한 통과 합성 구현에서 test FAIL).
* 클램프 금지: LUT 축 밖 입력은 `lut_axis_out_of_range`(SEAL_VIOLATION)로(DF-27).

### 4.3 만들면 배선

새 함수는 **만든 card에서** 운영 호출부가 부르고, 원래 문제가 있던 경로를 대체한다. 대체할 수 없으면 만들지 않고 사용자 승인을 구한다.

| 새 것 | 만드는 card | 같은 card의 소비자(대체하는 것) |
|---|---|---|
| `rail_declaration`·`RailDeclaration` | #1 | `load_topology` → 집합 판정 사이트 전부 |
| 극성 필드(hi/lo/mid, §10.3) | #17 | `trace_*`·`propagate_node_voltages`·`_metric_supply_current` 등, `probe_physical_consistency.py` 레일 집합(test 커밋) |
| (UD-15 (2)=X) analog-grammar `rails` 인자 | #49 | SD 운영 8함수의 AG 호출(`netclass.RAILS*` 이름 판정). (UD-15 (2)=Y이면 #17 안의 SD 호출부 어댑터가 같은 자리를 대체) |
| analog-grammar 명시적 의존 오류 | #45 | `_import_analog_grammar`의 `None` 폴백 12곳·전파 9곳, 소비처 0인 `unavailable_reason` 2곳(삭제) |
| `ports`의 `role` → 입출력 유도 전달 | #47 | `load_topology` → `propose_device_roles_gap_fill`의 `inputs`/`outputs`(지금은 넘기지 않아 `HINT_*` 이름 정규식이 추정) |
| N3.14 예외·`FAILURE_CLASSES`·`exit_code_for`·`FailureRecord` | #6 | 하네스 `run()` 종료 코드(모든 예외를 삼키고 exit 0, F15) |
| `LEGACY_NAMES`·`load_json_checked`·`reject_legacy_names` | #20 | 엔진의 파일 읽기 `json.load` 9곳(F19), `validate_no_legacy_vs_key`(삭제) |
| `rail_voltages(spec, rails)`(§10.4) | #21 | 스칼라 `spec["vdd"]` 읽기 20줄(F4) |
| θ 탐색 함수(추출), `instrument`, `measure_search_perf.py` | #7·#8 | `optimize_full_circuit_budget` 인라인 탐색, N6.3 보고 |
| `activations_out`, `noop_proof.py` | #9 | N6.3 무동작 증명, §10.1-4 발동 규칙 |
| `tol_V` 함수(MOD1) | #23 | `propagate_node_voltages` conflicts 판정(지금 미소비). #50의 IC11 허용오차가 두 번째 소비자 |
| IC11 감도 전파 허용오차(test 쪽 판정기, §10.6) | #50 | 같은 card의 IC11 `rail2` test 본문(xfail strict로 즉시 실행) → #22가 xfail 해제 |
| 공정 기록 로더(PDK 상수, §10.2) | #28 | 하네스 4벌·엔진 폴백 15곳, 죽은 키 `L_min`은 `layout_grid_L_candidates(L_min=)`에 배선 |
| VGS 기준 gm·gds 공개 조회 | #30 | `gain_ranking`의 `lut._query` 직접 조회 → 면제 `20260929-p4-scan-exempt` 해제 |
| `record_fallback`·`FallbackEvent`(§10.1) | #13 | 부록 C의 `I` 지점 + #13 발동 규칙으로 계측으로 남는 지점. 하네스 산출물 `fallback_events` 키(E1) |
| 레일 리터럴 lint 도구 + PT 계약 test | #19 | DF-19 위치 열(lint 산출로 대체), **모든 병합본 V1에서 PT로 상시 실행**(§5.4 #19), DoD E10 |
| V3 'diff가 닿은 문장' 선택 | #48 | `mutate_changed.py` 대상 선택(게이트 변경), Phase 4 card 전부의 V3 |

* **`tol_I`는 Phase 4에서 만들지 않는다**(P-3): Phase 4 안에 엔진 소비자가 없다. P3c 재착수는 6b(§1.4, §9-8).
* **`derived_spec` 재사용**(검토 M6): 변형 spec이 필요한 card(#50·#22의 원점 이동, #29의 U-30 전후, #51)는 새 변형 도구를 만들지 않고 하네스 `derived_spec(circuit, why, **overrides)`(F24)를 쓴다. 이것으로 6a 면제 기록의 'Phase 4 후보' 한 건이 Phase 4 안에서 소비된다.

### 4.4 캐싱 (NFR-2, N3.3)

* **새 캐시를 만들지 않는다.** 이미 있는 엔트리에 싣는다(B26-1: `_load_full_topology_cached`의 `meta["rails"]`).
* 고치는 캐시는 **상한 + LRU**(DF-07), 키는 **계산이 실제로 읽는 가변 상태의 내용 지문**(DF-13). **DF-13 지문은 LUT 로드 때 한 번 계산해 LUT 객체에 보관**한다(호출마다 계산 금지). 근거 하나 원칙에 따라 지문 = LUT 파일의 sha256(U-27b가 npz 메타·판정 기록에 남기는 값과 같은 값)이다. 메모리에서 만든 합성 LUT(test)는 배열 바이트의 sha256을 생성 시점에 한 번 계산한다.
* 새 선언 읽기(공정 기록, `supplies_v`)는 **실행당 한 번** 읽고 캐시한다. 유도값(`W_bounds` 하한 = `min_finger_w`, `rail_voltages`)은 함수 하나로 계산하고 결과를 보관한다.
* `fallback_events`는 평가 루프 안에서 발생할 수 있으므로 **(site, kind, device) 키로 집계**하고 첫 발생 detail과 계수만 남긴다(§10.1-1). 크기 상한 = 서로 다른 (site, kind, device) 수이고 θ 평가 수와 무관하다.
* 측정은 계측으로: CC-7 뒤 card마다 `perf.json`, 캐시 card는 적중·미적중 계수와 같은 입력 해시 재계산 수.
* 이미 있는 결함을 키우지 않는다: 경로 문자열 캐시 키(S0 지문 = 6a)는 재사용만 한다.

### 4.5 작성자 ≠ 검증자

모든 card의 red·기대값·픽스처는 test-author(interface card만), 구현은 code-author, 전후 비교표·perf·E-LIB·E-INST 수치는 auditor 판정 기록에서만 인용한다. 기존 test 기대값이 병합본과 다르면 test-author는 고치지 않고 dispute를 쓴다. 기준 약화·기준선 변경은 DEC-40 승인 없이 병합하지 않는다. **게이트 판정 범위를 바꾸는 일(V3 범위)은 오케스트레이터 선택이 아니라 게이트 변경 card(#48)와 그 승인으로만 한다.**

---

## 5. card 표

열: 판정 = 판정 유형(N3.12.3), oracle 종류 (a) 구성 (b) 독립 방법·문헌 (c) 동작 보존(base 결과) (d) 계획·원자료. `P3?` = Phase 3 모듈 파일 필요(Y) / Phase 3 전 가능(pre) / 무관(-). DoD = §6 ID.

### 5.1 Phase 3 전 후보

| # | id(초안) | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 1 | `b26-rail-accessor-set` | DF-19·26 넷 몫 1(접근자 + 집합 판정 사이트 11함수) | red-green | (a) 합성 레일 이름 topology. 역방향은 B26-1 사이트만으로 정해지는 값에 한정(검토 B2). (b) 이름 바꾸기 setup 불변. (c) E-LIB 9/9·E-INST | 계획 정정, P9, UD-14, **#48** | pre | E0·E10(부분) |
| 45 | `b34-grammar-explicit-dependency` | B34: `_import_analog_grammar`가 `ImportError`를 삼키지 않고 경로·skill 이름을 담아 다시 던진다. 폴백 12곳·전파 9곳·`unavailable_reason` 2곳 삭제(부록 C.3). 'gate 소자 없음 → `None`'(test_s120)은 범위 밖, docstring으로 뜻을 나눈다 | red-green | (a) `monkeypatch.setitem(sys.modules, "netclass", None)`로 base 'DID NOT RAISE', 조용한 반환 합성 구현에서 test FAIL. (c) E-LIB 9/9·E-INST | 없음(#1과 순차). **병합 선행: 사용자 `install.py` 작업**(F23) | pre(`_import_analog_grammar` 이동 card 전) | E0·E1 |
| 2 | `d4-delete-unwired` | 보류 D-1(`estimate_area_budget` → DF-09 닫힘)·D-2·D-3·D-4 함수 삭제 + **`test_ic5` `_DOMAIN_TABLE` D-4·D-5 두 행 삭제와 `len == 21` → 19**(V5 1회) | equivalence | (c) E-LIB·E-INST, (a) NEW-TOPO | UD-0, DEC-40 V5 승인 | pre | E0 |
| 3 | `pole-oracle-to-tests` | D-6 → test oracle | equivalence | (c) 승격 test 판정 불변 | UD-0 | pre | E0 |
| 4 | `toy-lut-to-tests` | D-7 → tests 픽스처 | test-only | (c) E-AST | UD-0 | pre | -- |

### 5.2 선두(순서 고정)

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 5 | `ts4-selfref-oracle` | TS4 | red-green | (a)·(b) | #2(D-1 결정) -- D-1 삭제면 대상 = V4 lint 산출 목록 **[미확인: 그 산출이 0이면 TS4는 계획 정정으로 닫는다]** | Y | E0 |
| 6 | `cc4a-failure-classes` | CC-4 앞부분, 하네스 `run()` exit code(DF-18 exit 몫·DF-37 하네스 몫 -- 하네스 except 3곳 476·512·528, F15에서 4회로 모두 exit 0) | red-green | (a) 합성 raise → exit code, (d) 계획 N3.14 | #5 | Y | E0·E11 |
| 7 | `cc7a-search-extract` | θ 탐색부를 MOD8의 `optimize_full_circuit_budget`에서 추출해 MOD6으로 | equivalence | (c) E-INST·E-LIB | #6 | Y | E8 |
| 8 | `cc7b-perf-instrument` | `instrument`·`ContextVar`·`measure_search_perf.py` | red-green | (a) worktree 밖 경로 → exit 8, 실패 입력 → `status=failed` | #7 | Y | E8 |
| 9 | `cc8-noop-activations` | `activations_out`·`noop_proof.py` | red-green | (a) 발동 1건 → exit 9 등 | **#6**(`00-common` CC-8 행) | Y | E9 |

### 5.3 실패 규약(CC-4a 뒤)

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 10 | `cc4b-df37-broad-except` | DF-37 광범위 except 재raise + 부록 C.1의 `F`(탐색 후보 실패 14곳)를 `CANDIDATE_FAILURE_CLASSES` 이름으로, `X`(후보점 배제 15곳)의 잡는 타입을 LUT 정의역 오류로 좁힘 | red-green | (a) N3.14 예외를 던지는 합성 입력이 삼켜지지 않음 | #6 | Y | E0 |
| 11 | `df03-gate-failure-class` | DF-03 | red-green | (a) 위반 픽스처 → 탐색 계속·실패 기록 | #6 | Y | E0 |
| 12 | `df06-field-source-except` | DF-06(D-6 뒤 사이트 3, 부록 C.1 SR 4054 포함) | red-green | (a) 원천 없는 필드 → 구조화 실패 | #3, #6 | Y | E0 |
| 13 | `df14-v8-fallback-events` | DF-14 `except Exception` 5지점(부록 C.1 `R #13 (DF-14)`) 제거 + **V8 `fallback_events`(§10.1 스키마·기록 함수·하네스 산출 키) + 부록 C의 `I` 5지점 계측 + §10.1-4 발동 규칙 적용**(발동 0 → 거부, 발동 > 0 → 계측·원인 card 지정) + SR 5809 방어 폴백(DEC-76) | red-green | (a) 호출 실패 합성 → 실패 클래스, 폴백 발동 → `fallback_events` 1건(같은 site 반복 → 계수만 증가), 조용한 기본값 합성 구현에서 test FAIL | #6, **#9** | Y | E0·E1 |
| 14 | `df18-theta-star-record` | DF-18 나머지: θ* 기록 | red-green | (a) 실행 산출물에 θ* 기록 | #6 | Y | E0 |
| 15 | `df11-stacked-diode-lut-fail` | DF-11 `idu_up = 1.0` 제거(SR 3538~3539) | red-green | (a) LUT 실패 주입 → 실패 클래스 | #6 | Y | E0 |
| 16 | `df12-offset-missing-gm` | DF-12 | red-green | (a) 손계산 오프셋 | #6 | Y | E0 |

#13 크기: 부록 C 기준 계측 후보는 `I` 5지점 + 발동 규칙 대상(부록 C.2 스칼라 기본값 중 담당 card가 없는 약 62곳(vsb `.get` 31 포함) + vsb `setdefault` 2, C.4)이다. 발동 계수를 잰 뒤(card 작성 전 실측, CC-8 도구) 거부로 바뀌는 지점과 계측으로 남는 지점이 갈린다. 둘을 합쳐 한 card가 크면 **스키마·기록 함수·DF-14 card**와 **지점 적용 card**로 나눈다(나눠도 스키마 card가 최소 1지점을 배선해야 한다 -- 만들면 배선).

### 5.4 레일

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 17 | `b26-rail-polarity` | B26-2: 극성(구조 규칙 + `supply_roles` 자리, §10.3), `trace_*`·방향 라벨·`propagate_node_voltages`/`derive_vsb_from_nodes` 기본 인자·`_metric_supply_current`·`_metric_rail_referenced_voltage`·`_metric_battery_centering_deviation`, B26-1에서 넘어온 SR 7282·8003·8091, **test 커밋: `probe_physical_consistency.py` 레일 집합 교체**. (UD-15 (2)=Y일 때만) SD 호출부 어댑터 | red-green | (a) vss 회로 `trace_*` 가지 수, 합성 H1·H2·H4 거부, 합성 레일 이름 + 선언 밖 내부 넷 `vdd`. (b) 레일 이름 바꾸기에서 `load_topology` meta 불변(meta **전체** 불변은 B35 처리 뒤 -- X면 #49, Y면 이 card). (c) E-LIB 9/9·E-INST [prep 무동작] | #1, #45, UD-1, (UD-15 결과) | 조건부 pre | E0·E10 |
| 18 | `b26-mna-rail-ground` | B26-3: MNA 고정 노드 = 선언 레일 전부 → `also_fix`·`excite`로 덮어쓰기(P-13) | red-green + E-INST 차이표 | (a) 합성 회로 CM 응답, (c) 차이표(auditor θ* 재측정) | #17, DEC-40 1건(current_reuse `cmrr_estimate_db`, §7.4) | 조건부 pre | E0·E2 |
| 19 | `b26-rail-literal-lint` | B26-4: lint 도구 `A/tests/tools/rail_literal_scan.py` + **PT 계약 test `A/tests/contracts/test_rail_literal_lint.py`**(모든 병합본 V1에서 실행 -- 상시 배선) + 이름 상수 삭제 + 레지스트리 §2 정본 확정 + DF-19 위치 열 대체. 판정 규칙·면제 목록은 표 아래 | red-green(base lint FAIL -- F22, 병합본 0) | (a) 도구 합성 입력(면제 밖 리터럴 1개 → FAIL, 면제 목록 항목 → PASS, 조용한 통과 합성 구현 → test FAIL), (d) AST 전수 | #17, #18, **#21**, #3, **UD-7 결과 card(C1)**, UD-9 | 조건부 pre | E10 |
| 20 | `cc5-legacy-gate-loader` | CC-5: `LEGACY_NAMES`·`load_json_checked`·`reject_legacy_names`, `json.load` 9곳 대체, `validate_no_legacy_vs_key` → `vs` 행. **깊은 복사 관용구는 해당 없음**(AST 계수 0, F19 -- 병합본에서 0 유지를 같은 test가 단언) | red-green | (d) 계획 N3.16에서 test-author가 옮긴 기대 목록 | #6 | Y | E4 |
| 21 | `mg1-rail-voltage` | MG1: `supplies_v`(하네스 `SPECS`: two_stage·current_reuse·folded = `{vdd: 1.8, gnd: 0.0}`, **nmcnr = `{vdd: 1.8, vss: 0.0}`(원점 이동 동등값)**), `rail_voltages` 유도 함수(§10.4), 스칼라 `vdd` 20줄을 폭(hi − lo)/절대값(hi)으로 분류해 교체, metric 인자 `supply_nets`·`rail_nets` 정리, 옛 키 행(`supplies`, spec `vdd`, metric `supply_nets`) | red-green + DEC-69 equivalence(키 매핑 뒤 θ*·metric·instance.json 동일 -- 4회로 모두 최저 레일 = 0 V라 성립) | (a) 옛 키 픽스처 거부, (c) E-INST | #20, U-26 (a) 확인 기록(§7.3) | Y | E4·E2 |
| 50 | `ic11-rail2-oracle` | **IC11 판정기(test-only)**: `test_ic11.py` `rail2` 본문 + 감도 전파 허용오차 helper(§10.6, test 쪽). 대상 회로 = **folded_cascode**(HEAD 하네스 정본 실행이 끝까지 돈다 -- F15, DF-24 검출 NMOS 2 -- F16. 두 번째 후보 current_reuse). 원점 이동 spec은 `derived_spec(..., supplies_v=…)`. #22 전까지 `pytest.mark.xfail(strict=True, raises=AssertionError, reason="DF-24, #22에서 해제")` | test-only + V5 승인(xfail 추가, 선례 `20260922-c9-ic11-split`) + V4 규칙 (1) 면제 승인(§10.6) | (b) 변환 불변 + 감도 전파 허용오차(§10.6). 판정기 자기 점검: helper를 도함수를 아는 합성 함수에 적용한 값 = 손계산, 원점 이동 오류를 심은 합성 평가기에서 test FAIL | #21, #23 | Y | E3 |
| 22 | `df24-ic11-rail-origin` | DF-24 vsb 유도(DEC-61, 레일 0 V 가정 제거: nmos = V(source) − V(bulk), bulk 기본 = 가장 낮은 레일 전압, pmos = V(bulk) − V(source)) + #50의 xfail 해제 | red-green(base = #50의 xfail strict가 실제 실패로 기록됨) | (b) #50의 판정식. (a) 음전위 레일을 `supplies_v`에 둔 합성 픽스처 | #21, **#23**, **#17**, #50 | Y | E3 |
| 51 | `nmcnr-split-rail-spec` | nmcnr `SPECS` `supplies_v`를 확정값 `{vdd: 0.9, vss: −0.9}`로(U-26 (a)) | equivalence(IC11 불변 -- 무동작 card) | (c) #22 뒤 엔진에서 전후 비교: I-C11이 해소되지 않았으면 같은 실패 클래스·같은 margin(허용오차 §10.6) + 실패 전까지의 setup 양(노드전압은 −0.9 V 이동, VGS·VDS·VSB·gm_id·W 불변), 해소됐으면 E-INST 전부 | #22 (#44가 nmcnr를 해소하면 그 뒤) | Y | E2 |
| 46 | `b36-grammar-gate-scope` | B36 게이트 공백. UD-15 (1)=(a)이면 N3.12.2 행 추가 + 게이트 도구 6개 범위, (b)이면 흡수 이동 card | 게이트 변경(B28 형식) 또는 equivalence | (a) analog-grammar 수정 합성 커밋이 trailer 없이 거부됨, redteam 사례 | UD-15, plan_tables·게이트 변경 승인 | - | -- |
| 47 | `b37-ports-to-grammar` | B37: `load_topology`가 topology `ports`의 **`role`에서 입출력을 유도**해 `propose_device_roles_gap_fill`의 `inputs`/`outputs`로 넘긴다(`direction`은 읽지 않는다 -- 계획 N3.15·DEC-69 MG2가 삭제). role → 입출력 대응은 role 어휘의 선언 표 하나(F21의 6개 값)로 정하고 이름 정규식은 쓰지 않는다. **`ports`가 없으면 `SchemaRejectedError`**(폴백 없음). 바이어스 넷 추정은 범위 밖(B38) | red-green(+ 결과가 바뀌면 E-LIB 차이표·DEC-40) | (a) 입력 넷을 힌트 정규식에 걸리지 않는 이름으로 둔 합성 topology, `ports` 없는 합성 topology 거부. (c) E-LIB 9/9 **[미확인: 9회로 결과 변화 -- card 전 실측]** | #17, #6 | 조건부 pre | E0 |

**#19 lint 판정 규칙(계약)**:
* 대상 = 엔진 모듈 `A/*.py`(Phase 3 뒤 MOD1~MOD10). 하네스 `SPECS`의 `supplies_v` 키는 **선언 데이터**(DEC-62 'SPECS 데이터 항목')라 대상이 아니다.
* 발견 = 문자열 상수(`ast.Constant`, docstring 식 문장 제외) 중 casefold 값이 **스캔 어휘**에 드는 것. 스캔 어휘는 lint가 실행 시점에 읽는다: library 모든 topology의 `supply_nets` 합집합 ∪ analog-grammar `netclass`의 레일 이름 집합. 어휘를 lint 코드에 박지 않는다(topology 무관).
* spec 키 `"vdd"`도 센다 -- 그래서 #21이 선행이다(F4 20줄을 MG1이 없앤다).
* **면제 목록(전부, 이 밖은 0)**: (E-a) 예제 데이터 함수 `folded_cascode_example`·`two_stage_ota_example`(SD, `prep_b26_supply_nets.md` §1.4 '판정 아님') (E-b) UD-9가 유지로 결정되면 `find_differential_and_mirror_forks`(6a 공동분석까지) (E-c) UD-15 (2)=Y이면 어댑터의 정준 토큰 상수 (E-d) UD-15 (2)=X이면 analog-grammar CLI 경계 모듈(`analyze.py`)의 이름 집합 가정. 면제는 lint 입력 파일의 목록(함수·모듈 이름 단위)으로 두고 면제마다 근거 id를 적는다. E10 통과 기준에 이 목록이 그대로 들어간다.
* AG 파일(`skills/analog-grammar/assets/*.py`)은 UD-15 (2)=X일 때 #49가 lint 범위에 더한다.

### 5.5 노드전압

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 23 | `df02-conflicts-seal-tolv` | DF-02 conflicts → SEAL_VIOLATION + `tol_V` 함수(MOD1, N3.6 식: (kind, L 앵커, VDS)별 LUT leave-one-out 보간 오차 최댓값, `tests/probe_interp_scheme_loo.py` 방법 승격) | red-green | (a) 다중 도달 불일치 합성, (d) B21 (c) 재현 입력 [prep] | #6 | Y | E0 |
| 24 | `df01-vsb-recompute` | DF-01: vsb를 노드전압으로 고친 뒤 W·gm·gds 재계산(원인 코드 SR 7579 한 줄, F9). §10.1-4 발동 규칙에서 원인이 DF-01로 지정된 `vsb` 기본값 사이트 | red-green | (a) 버전 혼재 검출 픽스처 | #22, #23, #13 | Y | E0 |

### 5.6 LUT·PDK

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 25 | `df27-lut-axis-gate` | DF-27 | red-green | (a) vsb 0.9 V 픽스처 → `lut_axis_out_of_range` | #6 | Y | E5 |
| 26 | `u27a-sweep-script` | U-27 도구 결함 G1~G6(v0.2와 같다) + **G7: `_parse_output`이 ngspice 출력의 `Error:` 줄을 발견하면 조합 이름·줄을 담아 거부**(F20) | red-green | (a) 소형 격자, 옛 조합 비트 동일 재측정, CGS+CGD+CGB ≈ CGG, **`Error:` 줄이 있는 합성 ngspice 출력에서 base는 조용히 파싱(red) → 병합본 거부** | #25 | - | E6 |
| 27 | `u27b-lut-regen` | 재생성 + 옛 격자점 대조 + 새 해시 기록 + **VS 축 leave-one-out 보간 오차 기록**(정보, P-5) | red-green + 대조 기록 | (c) 옛 5 VS 점 × 기존 5열 비트 동일 기대 | #26, 다르면 DEC-40(§7.4) | - | E6 |
| 28 | `u30a-pdk-record-noop` | U-30 선언(§10.2) + MOD1 로더 + npz 해시 연결 + DF-34 Phase 4 몫 + 엔진 폴백 15곳 삭제 + 단위 m 통일 + `L_min` 배선, 값은 **기존 값**(무동작 단계) | red-green + equivalence | (d) PDK 규칙표, (c) E-INST | #27 | Y | E7 |
| 29 | `u30b-wbounds-min-finger` | `min_finger_w` = difftap.2, `W_bounds` 하한 유도 | red-green + 전후 비교표 | (d), (c) 비교표(auditor, 변형 spec은 `derived_spec`) | #28, DEC-40(§7.4) | Y | E7·E2 |
| 30 | `b24a-lut-vgs-query-api` | B24 (a) | red-green | (a) 격자점 조회값 = 표 값 | #6 | Y | E0 |
| 31 | `df10-nonmonotone-inversion` | DF-10 + B24 (b) | red-green | (a) 비단조 합성 곡선 | UD-5, **#6** | Y | E0 |

### 5.7 캐시

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 32 | `df07-lru-caches` | DF-07 | red-green | (a) 상한 초과 뒤 최근 키 적중 | #6 | Y | E0 |
| 33 | `df13-lut-content-key` | DF-13 `id(lut)` 키 → **LUT 로드 때 한 번 계산한 내용 지문**(§4.4) + 상한 | red-green | (a) 같은 내용 다른 객체 적중·다른 내용 미적중, 호출당 지문 재계산 0(계수 래퍼) | **#6** | Y | E0 |
| 34 | `df15-rz-cache-key` | DF-15(재현 먼저) | red-green(재현 안 되면 계획 정정 요청) | (a) | #6 | Y | E0 |

### 5.8 개별

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 35 | `df04-device-name-exact` | DF-04 | red-green | (a) | #6 | Y | E0 |
| 36 | `df05-mirror-pairs-all` | DF-05 | red-green | (a) 3소자 미러 | #6 | Y | E0 |
| 37 | `df08-22-spec-origin` | DF-08·DF-22 + U-04 `origin` | red-green | (a) | UD-4 | Y | E0 |
| 38 | `df20-fallback-constants` | DF-20(vds 0.6/0.2, margin 0.05 -- SR 1564, `gm_id_bounds` `(2.0, 30.0)` 3곳, `_DEFAULT_METRIC_STAGE_BUDGET_GM_ID` 15.0 -- SR 1941·6042·10221, `min_vds_by_role` 읽기 3곳과 하네스 4벌) | red-green | (d) 유도 근거(DEC-27·DF-25 연결은 6b) | #13 | Y | E0·E1 |
| 39 | `df23-general-rules` | DF-23 Phase 4 행(P10 목록) | red-green | (a) NEW-TOPO | P10 병합 **[미확인: 행 수는 P10이 정한다]** | Y | E0 |

### 5.9 배선

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 40 | `theta-order-gate` | W-1 | red-green | (a) theta 순서만 뒤바꾼 픽스처 거부, 무동작 9/9 | #6 | Y | E0 |
| 41 | `euler-repair-wire` | W-2 배선 + **D-5 함수 `audit_vertical_stack_id_euler_feasibility` 삭제**(표 행은 #2가 이미 지웠다 -- F18로 중간 병합본 안전) | red-green + E-INST 전후 | (a) S146 blocked 그룹, (c) 행 배치 전후 | #2, 달라지면 DEC-40 | Y | E0·E2 |
| 42 | `roles-ratify-cli` | W-3 | red-green | (a) 합성 topology 사본 기록·재로드 | - | Y | E0 |

### 5.10 회로 (I-C11, 설계는 §11)

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 43 | `ic11c-explicit-failure` | I-C11 실패 명시화(UD-6과 무관하게 한다): two_stage `_hr_verify_group_kvl_sum`의 KVL 불일치 `ValueError`와 nmcnr 스택 예산 배정 불가를 N3.14 `SealViolationError`(항목 = 기둥 KVL, 소자, 위반 크기 → margin = 위반/`tol_V`)로 바꾸고 탐색이 후보 실패로 기록한 뒤 계속하게 한다. 모든 시작점 실패면 `SearchFailedError`(exit 6) | red-green | (a) 하네스 정본 실행 two_stage·nmcnr: base = `ValueError`·exit 0(F15), 병합본 = 실패 레코드 + exit 6(또는 해가 나오면 θ*). 메시지의 'stage1_out'·'KVL'은 유지(known-limitation test 3쌍이 계속 성립 -- `InfeasibleSizingError`가 `ValueError` 하위(SR 6429)이므로 xfail `raises=ValueError`도 성립) | #6, #10, #23 | Y | E2·E11 |
| 44 | `ic11c-resolve` | I-C11 해소 -- UD-6 선택지에 따라 내용이 정해진다(§11.3): (A) 계획 정정만(이 card 없음) / (B) DEC-70 부분 선행 구현 / (C) topology 선언 정정(공동분석 결과 반영). 어느 경우든 해소된 회로의 xfail 3건·known_limitation 3건 정리, V4 면제 `20260923-c9-v4-exempt` 재검토(백로그 B9·B12) | red-green(해소 시 xfail strict가 XPASS → 해제) | (c) E-INST 전후, (a) 합성 회로(B안), (d) 공동분석 확인표(C안) | UD-6, #43 | Y | E2 |

### 5.11 조건부

| # | id | 조건 | 내용 |
|---|---|---|---|
| C1 | `theta-authoring-wire` 또는 `d4-delete-theta-authoring` | UD-7(U-A) 결과 | theta 작성 묶음 4함수 배선 또는 삭제. `propose_theta_kcl_gap_fill` 사이트(SD 3559·3561·3719)를 정리하므로 **#19의 선행** |
| C2 | `df09-area-blend` | D-1이 승인되지 않으면 | DF-09 `(2−α)A` 식 수정 |
| C3 = 49 | `b35-grammar-rails-arg` | UD-15 (2)=X | analog-grammar에 기본값 없는 `rails` 인자(`classify_nets(…, *, rails)`·`stack_edges(devs, *, rails)`, 나머지는 `imp.get(n) == RAIL_Z`), SD는 `meta["rails"]`(+#17 극성)를 넘긴다, CLI 경계로 이름 집합 가정 이동, lint 범위에 AG 추가, mid 레일은 UD-15 (3) 결과대로. oracle: (a) `prep_b34_b35_grammar.md` §3.4 합성 topology, (b) 레일 이름 바꾸기에서 `load_topology` meta **전체** 불변, (c) E-LIB 9/9·E-INST 2. 선행 #17, #46, #19 |
| -- | UD-8(U-B `find_diode_stacks` 묶음) 삭제 승인 시 | -- | 삭제 card는 **6a S1 card**(대체물인 S1 관계 엣지가 생기는 card)다. Phase 4에서 지우지 않는다(대체 전 삭제 금지) |

### 5.12 게이트 변경

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 48 | `v3-diff-touched-scope` | V3 대상 선택을 'diff가 닿은 def의 본문 전체'에서 **'diff가 닿은 문장 + 새 def 전체'**로. 판정은 `tools/gates/mutate_changed.py`가 한다(대상 문장 선택·제외 변이 id 목록을 도구 출력 JSON으로). 제외 변이는 판정 기록에 도구 출력 그대로 남고, 오케스트레이터·auditor가 손으로 면제 id를 만들지 않는다. 계획 N4.2 V3 행 문구, `05` §10 V3 행, §18 부트스트랩 절차 | **게이트 변경(B28 형식)**, `gate_change: yes`, plan_tables 승인 + 게이트 변경 승인 | (a) redteam 새 공격: 닿은 문장 안의 변이를 살려 두는 합성 커밋이 FAIL, 닿지 않은 문장 변이만 사는 커밋이 PASS하면서 제외 id가 출력에 있음, 새 def의 변이가 제외되지 않음. 기존 redteam 전부 PASS | B28(병합됨 `2b41e79`) | - | -- |

**합계**: 50건(v0.2 47 + #48·#50·#51) + 조건부 3건(C1, C2, C3 = #49). 한 문서로 둔다(N9.1).

**card 단위 확인이 필요한 것**: #1은 크다(로드 경로/평가 경로 둘로 나눌 수 있다). #13은 §5.3 뒤 문단의 분할 규칙을 따른다.

---

## 6. DoD 표

auditor가 Phase 4 마지막 card 병합본의 격리 복제본 `<iso>`에서 실행한다. `PT` = `10-test-separation` §10 정의(`--gmid-phase=4`). `$PY` = `C:/Python314/python.exe -B`. 새 도구 경로는 해당 card가 만든다(이름은 초안 -- card 작성 전 test glob 충돌 grep).

| ID | N6.2 `4` 조건 | 명령 | 통과 기준 |
|---|---|---|---|
| E0 | DF마다 red-green | Phase 4 card마다 `.ai/verification/<id>.json`의 판정 유형·red 기록 | §5 card 전부 판정 기록 있음, red-green card는 base red + 병합본 green. N5.2에서 담당 Phase에 4가 있는 DF 전부가 card 또는 닫힘 기록에 대응 **[미확인: 판정 기록 필드 이름은 `00-common` §8.1 스키마에서 card 작성 때 확인]** |
| E1 | V8 도입(정본 실행 `fallback_events` 0) | 사이징 대상 4회로마다 하네스 정본 실행 → 산출물의 `fallback_events`(§10.1-2: 성공이면 `instance.json` 최상위, 실패면 실행 기록 JSON) | **4회로 모두** 키가 있고 빈 목록. 키가 없으면 FAIL(계측 미배선). two_stage·nmcnr가 #43 뒤 실패 레코드로 끝나도 실행 기록의 `fallback_events`가 비어 있어야 한다 |
| E2 | 사이징 대상 회로 실행과 전후 비교표 | base = Phase 3 DoD 병합본, head = Phase 4 마지막 병합본. 회로마다 하네스 정본 실행 결과를 §10.5 식으로 정규화해 비교 | 표가 판정 기록에 있고, 바뀐 항목마다 원인 card id와 DEC-40 승인 기록 id가 붙어 있다. two_stage·nmcnr는 base에서 `ValueError`(F15)이므로 비교 단위가 '결과 종류(θ* / 실패 클래스)·margin·실패 전 setup 양'이다. UD-6 결과가 Phase 4 해소면 해소 전후 두 단 |
| E3 | IC11 2레일 케이스 PASS | `PT -rA <iso>/skills/analog-gmid-design/assets/tests/contracts/test_ic11.py` | `rail2` PASS(xfail 표식 없음 -- #22가 해제), `rail3`·`reject` XFAIL(6a) |
| E4 | MG1 옛 키 거부 test PASS | `PT <iso>/…/tests/contracts -k "legacy"` **[id 초안]** | 계획 `supplies`, spec 스칼라 `vdd`, metric 인자 `supply_nets`(+`rail_nets`) 각각 `SchemaRejectedError`, 조용한 통과 합성 구현에서 test FAIL |
| E5 | DF-27 VS 축 밖 픽스처 거부 | `PT <iso>/…/tests -k "lut_axis"` **[id 초안]** | 축 밖 입력 → `lut_axis_out_of_range`, 클램프 0 |
| E6 | U-27 옛 격자점 대조 기록 | auditor가 새 LUT와 옛 표본의 공통 격자를 열별 비교 → `grid_compare.json` | 기존 열 비트 동일, 아니면 원인 보고 + DEC-40 승인. 새 해시·VS 축 LOO 오차 기록 |
| E7 | U-30 전후 비교표 | #28: E-INST 동일, #29: self-test·사이징 대상 회로 비교 | `min_finger_w` 출처 = difftap.2 기록, 공정 기록 밖 PDK 사본 0, 바뀐 기준선마다 DEC-40 승인 |
| E8 | 성능 보고(N6.3) | `$PY <iso>/…/tests/tools/measure_search_perf.py --worktree <iso> --circuit <파일럿> --out <iso 밖>` | 마지막 동작 변경 card의 `perf.json` 존재, `status=ok` |
| E9 | 무동작 증명(N6.3·DEC-47) | CC-8 뒤 card마다 `noop_proof.py` | card마다 `noop-<circuit>.json` PASS |
| E10 | DF-19 '운영부 레일 이름 리터럴 0' | `PT <iso>/…/tests/contracts/test_rail_literal_lint.py` + `$PY <iso>/…/tests/tools/rail_literal_scan.py --root <iso>` **[이름 초안, #19]** | test PASS, 도구 exit 0, 발견 0. 면제 = §5.4 #19 면제 목록 그대로(UD-9·UD-15 결과로 정해진 항목만), 목록 밖 면제 0 |
| E11 | 전체 회귀·실패 규약 | `PT` 전체 + E-LIB 재측정 + N3.14 대조 test | 실패 0, E-LIB 9/9 |

---

## 7. 사용자 결정 (진짜 사용자 몫만)

**UD-0 이 design 승인(DEC-51)**: 아래 '원칙 기본안'(§7.2)과 계획 정정 요청(§9)을 함께 덮는다.

v0.2 대비: UD-2(교류접지)·UD-3(`supplies_v` 값·시점)은 계획이 이미 정한 것이라 질문에서 뺐다(→ P-13·P-14, 남는 것은 §7.4의 DEC-40 기준선 승인과 §7.3의 U-26 (a) 확인 기록). UD-11·UD-12는 '발생 시 건별 DEC-40'이라 §7.4로 옮겼다. UD-13은 decision이 아니라 게이트 변경 card #48이다. B35 방식(v0.2 P-11)은 UD-15에 묶었다.

### 7.1 결정 항목

| ID | 결정 | 권고(준비된 기본안) | 왜 사용자 몫인가 | 막는 card | 결정 자료 |
|---|---|---|---|---|---|
| **UD-1** | **D1 레일 극성** | **(C) 구조 규칙 기본 + 선택 필드 `supply_roles`(예외 회로만, §10.3)**. 규칙·게이트는 v0.2와 같다. library 9/9 규칙으로 판정 → 파일 수정 0 [prep] | 회로 해석 규칙(공동분석) | #17, #19 | `b26_decision_table.md` §1·§3 |
| **UD-4** | **U-04 픽스처/정본 구분** | 계획 기본안: spec에 `origin: canonical \| fixture` 필수 | 계획이 사용자 결정으로 지정(N7.2) | #37 | 계획 1079행 |
| **UD-5** | **U-05 비단조 곡선 이분 역산** | 계획 기본안: 단조 구간별 근 전부 반환 + 호출자 선택 규칙 명시 | 계획이 사용자 결정으로 지정 | #31 | 계획 1080행 |
| **UD-6** | **U-09 / I-C11 해소 방식**(§11) | 선택지 (A) 계획 정정: Phase 4는 #43 실패 명시화까지, 해소는 DEC-70(AC → DC 되먹임)·DEC-71(기둥 조립)을 구현하는 Phase로 옮긴다(U-09 재결정 + xfail 3건 만료 Phase 변경) / (B) DEC-70의 부분을 Phase 4에 선행 구현(엔진 규칙, 계획 개정) / (C) 회로별 topology 선언 정정(공동분석, WP-07). 회로마다 다를 수 있다. **권고: #43은 원칙상 무조건. nmcnr는 (C)부터**(엔진 메시지가 "선언되지 않은 소자/수동소자가 있거나 vertical_stack_id 선언이 실제 직렬 경로와 다르다"고 선언 쪽을 가리킨다 -- F15), **two_stage는 (A)**(원인이 compensation의 AC 결정 VDS와 DC KVL 불일치 -- 세션41에 사용자가 "DC/AC 조율 없이는 못 푸는 문제"로 기록, 그 일반 규칙이 DEC-70이고 계획 상태 '미구현'). 이 권고는 회로 해석(C)과 계획 범위(A·B) 판단을 포함하므로 결정은 사용자 몫이다 | 회로 해석·topology connectivity(WP-07), 계획 N7 U-09 재결정 | #44, E2 | §11, F15 |
| **UD-7** | **보류 행 U-A: theta 작성 묶음** | **배선**(v0.2와 같다) | 회로 해석 규칙 + topology 데이터 | C1, #19 | `prep_deferred_rows.md` §3.3 |
| **UD-8** | **보류 행 U-B: `find_diode_stacks` 묶음** | **삭제**. 삭제 card는 6a S1 card(§5.11) | ★ diode 정의(공동분석) | 6a S1 | 같은 문서 U-B |
| **UD-9** | **보류 행 U-C: `find_differential_and_mirror_forks`** | **6a ★ 공동분석까지 유지(비운영 면제)**, #19 면제 목록 E-b | ★ diffpair/mirror 정본(공동분석) | #19 | 같은 문서 U-C |
| **UD-10** | **보류 행 U-D: `check_mirror_symmetry` 묶음** | **7b I-A13의 바탕으로 배선**, 7b까지 미배선 면제. 기존 U-02 승인 3항 번복 | 기존 승인과 충돌 | 7b | 같은 문서 U-D |
| **UD-14** | **DEC-60 넷 전환기 종료 + DF-19·26 넷 몫을 MG1에서 분리 + B26-1을 Phase 3 전에 착수** | 승인한다(v0.2와 같다) | N2 확정 결정의 한시 조항 변경 | #1 | `draft_b26_plan_patch.md`, `review_b26_1.md` S3 |
| **UD-15** | **analog-grammar 묶음 결정 -- (1) 소속·게이트 편입, (2) B35 처리 방식, (3) 선언된 mid 레일의 grammar 매핑** | (1) **(a) 별도 skill + gmid 게이트 편입**. (2) **X(analog-grammar 확장)**: (1)이 (a)면 게이트·경로표 승인이 어차피 필요해 Y의 비용 이점(경로표 개정 불필요)이 사라지고, 아래 비교표에서 X만 DEC-62와 충돌하지 않는다. (3) **공동분석 항목**: 기본 제안은 "선언 레일은 극성과 무관하게 grammar에서 레일(`RAIL_Z`)로 보고, `SUPPLY`/`GROUND` 라벨은 hi/lo만 받는다(mid는 라벨 없음)" -- 사용자 확인 필요 | skill 경계·공유 설정, 판정 표 개정, **레일 수 상한 여부(DEC-62)와 교류접지 넷의 grammar 역할(회로 해석)** | #46, #17, #49, #19 | `prep_b34_b35_grammar.md` §2.3·§3.2·§5, 아래 비교표 |

**UD-15 (2) 비교표(중립)** -- 두 안 모두 9회로 무동작(`RAILS ∩ 트랜지스터 넷 = supply_nets ∩ 트랜지스터 넷` 9/9, SD 운영 경로는 극성 미소비 [prep: §3.3])이다.

| 기준 | X: analog-grammar 확장(`rails` 인자) | Y: SD 호출부 어댑터(넷 이름 번역) |
|---|---|---|
| 고치는 파일 | analog-grammar `netclass`·`idioms`(+CLI), SD | SD만 |
| 필요한 승인 | UD-15 (1)의 plan_tables + 게이트 변경(#46) -- (1)=(a)면 **추가 0** | 경로표 개정 불필요. 단 B36 게이트 공백(#46)은 Y를 골라도 남아 (1)의 승인은 어차피 필요하다 |
| **레일 수 상한(DEC-62)** | 없음(선언 집합을 그대로 받는다) | **있음**: 극성마다 정준 토큰 수(analog-grammar 이름 집합 원소 5개)를 넘는 선언 레일은 명시적으로 거부해야 한다 = topology에 따라 거부하는 코드 상한. 같은 극성 레일이 여럿인 회로(레벨 시프터 H3 등)가 걸린다. 채택하면 DEC-62 예외 기록과 해소 card가 필요하다 |
| **mid 레일(선언된 `agnd`) 처리** | `rails` 집합에 넣고 라벨은 (3)의 결정대로 | 정준 토큰이 `VDD`/`GND` 극성 둘뿐이라 **mid를 어느 토큰으로 번역할지**가 정의되지 않는다. 어느 쪽을 골라도 grammar의 role 유도가 달라질 수 있다 → (3)과 같은 회로 해석 결정이 번역 규칙 안에 숨는다 |
| 이름 기반 판정 잔존 | analog-grammar 라이브러리 함수에서 0(이름 집합은 CLI 경계의 명시 가정으로만) | analog-grammar 내부는 그대로 이름 기반(일반화 미충족). SD는 이름 집합을 인코딩 통로로 참조 |
| B26-4 lint | AG 라이브러리까지 범위에 넣을 수 있다(면제 E-d는 CLI 모듈 하나) | 정준 토큰 리터럴을 lint 면제(E-c)로 둬야 한다 |
| 역변환 부담 | 없음 | `cls`·`imp`·`stack_edges`·`Match.ports`·입력 힌트를 전부 역치환해야 하고, 누락이 조용히 난다 -- 계약 "`load_topology` meta 전체 불변"으로 막아야 한다 |
| 극성 의존 | 극성(B26-2) 뒤 한 번에(API 1회 변경) | 극성으로 토큰을 고르므로 B26-2(UD-1) 선행 |
| 작업량 | card 1건 추가(#49) + AG test를 gmid `tests/contracts/`에 | #17 안에 흡수(card 수 불변) |
| 되돌림 비용 | analog-grammar API 변경(단독 CLI 사용자 영향) | 어댑터 삭제만 |

**사용자 작업(결정 아님)**: `install.py` `SKILLS`에 `"analog-grammar"` 추가(쓰기 주체가 사용자인 경로, F23). **#45 병합의 선행 조건**이다.

### 7.2 원칙 기본안(UD-0으로 확정 -- 따로 묻지 않는다)

| ID | 기본안 | 근거 |
|---|---|---|
| P-1 | `supply_nets` 없으면 거부, 이름 집합 대체 경로 없음 | 9/9 선언 완료(U-26 (b)), DEC-60 |
| P-2 | 보류 행 삭제·이관 D-1~D-7, 배선 W-1~W-3 | `prep_deferred_rows.md` §3.1·§3.2 |
| P-3 | `tol_V`는 DF-02와 한 card(MOD1), `tol_I`는 Phase 4에서 만들지 않음 | 만들면 배선 |
| P-4 | U-30 범위·선언 위치(§10.2), `max_finger_w`·`W_bounds` 상한·`stage_w_max`는 하네스 탐색 설정 공통 한 곳(값 유지). **정보 보고**: `max_finger_w` 40 µm > 모델 bin W 상한 7.0 µm(이번에 값을 바꾸지 않음) | DEC-68, `prep_u27_u30.md` |
| P-5 | U-27 VS 격자 = 상한은 `supplies_v` 최대 차에서 유도, 간격은 기존 0.2 V 유지. 0.2 V의 보간 오차는 #27에서 auditor가 VS 축 leave-one-out 오차로 **기록**(E6)하고, 간격을 바꿀지의 판단은 백로그 **B39**(제안: "VS 축 보간 오차 대 tol_V 비교 -- 6b 봉인 설계 때 판단")로 둔다 | 새 상수 금지, checklist §1 0.1 V 권장과의 차이 기록(검토 M7) |
| P-6 | U-27 → U-30 순서 | 기준선 승인 1회 |
| P-7 | 캐시(§4.4) | NFR-2 |
| P-8 | DF-23 Phase 4 범위 = P10 목록의 담당 4 행 | 계획 DF-23 |
| P-9 | 레일 인자는 기본값 없는 키워드 전용 | §4.2 |
| P-10 | B34: analog-grammar는 필수 의존이고 부재 시 명시적 오류 | 조용한 폴백 금지 |
| P-12 | B37: `ports`의 `role`에서 입출력 유도, `direction` 미사용, `ports` 부재 거부, 바이어스 추정은 B38 | DEC-62, 계획 N3.15(`direction` 없음) |
| **P-13** | **(v0.2 UD-2) 소신호 MNA에서 선언 레일 전부 교류접지**: `{r: 0 for r in supply_nets}` 다음 `also_fix`·`excite`로 덮어쓰기 | 계획 N0.4 106행 '교류접지 집합' 정의("레일 넷은 … AC구조에서는 모든 뷰의 교류접지다. 그 넷을 `ac_excite`로 선언한 전달 뷰만 예외"), DF-26 문구. 사용자에게는 결과 기준선(current_reuse `cmrr_estimate_db`)의 DEC-40 승인만 받는다(§7.4) |
| **P-14** | **(v0.2 UD-3) `supplies_v` 값**: nmcnr = 계획 확정값 `{vdd: 0.9, vss: −0.9}`(U-26 (a)), 적용 시점 = #22 뒤 #51(B1). #21에서는 원점 이동 동등값 `{vdd: 1.8, vss: 0.0}`. two_stage·current_reuse·folded = `{vdd: 1.8, gnd: 0.0}`(현 `SPECS` `vdd` 1.8, 세 회로 `supply_nets` = `['vdd','gnd']` [재측정 v0.3]) | 계획 U-26 (a). 세 회로 값은 계획이 정한 절차('제안표 → 사용자 확인')의 확인 기록이 착수 조건이다(§7.3) -- 결정 질문이 아니다 |
| **P-15** | U-25 실행 `SPECS` 이관은 범위 밖(§1.4) | N6.1 Phase 4 범위, IC11 rail3 = 6a |
| **P-16** | CC-5 깊은 복사 관용구 = 해당 없음(F19) | `00-common` §14 CC-5 행 |
| **P-17** | B26-4 lint는 PT 계약 test로 상시 실행, 면제 목록은 §5.4 #19에 전부 | 만들면 배선(검토 S10). 게이트 도구 변경이 아니라 test 추가라 게이트 변경 승인이 필요 없다 |
| **P-18** | D-5: 표 행은 #2, 함수는 #41 | F18(표에 없는 함수는 형식만 검사, 표 행의 함수가 없으면 FAIL) |
| **P-19** | 폴백 사이트 처리 규칙(§10.1-3·4) | DEC-76, V8, 조용한 폴백 금지 |
| **P-20** | U-27 도구 `Error:` 검사는 #26 범위(G7) | 이 Phase가 만드는 엔진 입력의 조용한 실패(검토 S6) |

v0.2의 P-11(B35 = 어댑터)은 **지웠다**. 근거 열의 '조정자 지시'는 사용자 승인이 아니고, 비용 근거는 UD-15 (1)=(a)에서 사라지며, 어댑터의 레일 수 상한은 DEC-62와 충돌한다(검토 B4). B35는 UD-15 (2)로 옮겼다.

### 7.3 착수 조건 승인 기록(결정 질문이 아니라 계획·게이트가 요구하는 확인)

| 기록 | 내용 | 막는 card |
|---|---|---|
| U-26 (a) 확인 | two_stage·current_reuse·folded의 `supplies_v` 제안표(P-14) 확인 | #21 |
| U-04·U-05·U-09·U-27·U-30 | 계획 N7.2가 Phase 4 착수 조건으로 지정(F11: 해당 승인 0) | 각 card |
| #48 게이트 변경 승인 | plan_tables + 게이트 변경(B28 형식) | #1과 Phase 4 card 전부의 V3 |
| #46 게이트 변경 승인 | UD-15 (1) 결과 | #46·#49 |
| #50 V4 규칙 (1) 면제 | 불변식 test의 기대값이 피검 함수 호출(선례 `20260923-c9-v4-exempt`) | #50 |

### 7.4 뒤에 올 DEC-40 승인(지금 결정할 것 아님, 발생 시 건별)

* current_reuse `cmrr_estimate_db` 기준선(P-13, #18) -- auditor가 θ*에서 다시 잰 값으로 [prep: 73.14488 → 73.38009].
* U-27 새 LUT 기존 열 차이(v0.2 UD-11, #27).
* U-30 교체로 바뀌는 θ*·기대값·finger 배정(v0.2 UD-12, #29) [prep 영향 후보: folded M3·M4 1.017 µm, nmcnr M202 1.02 µm].
* W-2 행 분할 감소로 바뀌는 E-INST(#41).
* `test_ic5` `_DOMAIN_TABLE` D-4·D-5 두 행 삭제와 `len` 21 → 19(#2, V5 1회).
* #50 xfail strict 추가(V5).
* I-C11 xfail·known_limitation 정리(#44, UD-6 결과).
* 각 DF 수정으로 바뀌는 θ*(E2), #47로 바뀌는 E-LIB.
* B26-1 기존 test에 `supply_nets`·`rails=` 추가가 V5로 잡히면 `target_kind: diff`.

---

## 8. 병렬 준비 계획

card 처리 속도 규칙(메모리): 사실 문장은 쓰는 자리에서 재측정, 새 이름은 test glob 충돌 grep, 원칙은 계약에 전 범위로, 삭제 전 계획서 소비자 grep, 병렬 가능한 준비는 항상 미리.

### 8.1 지금(Phase 2 남은 card·Phase 3 design 승인과 병렬)

| 준비 | 산출 | 막히는 것 |
|---|---|---|
| B26-1 spec card 보강 | 검토 `review_b26_1.md` B2·S1·S4·S5·M1~M6 반영. V3 계획은 #48 뒤 도구 출력 기준 | UD-14, #48 |
| **#48 V3 범위 게이트 변경 spec card** | `mutate_changed.py` 대상 선택 지점, redteam 새 공격 3종, 계획 N4.2·`05` §10 문구 | 게이트 변경 승인 |
| 계획 정정안 커밋 준비(`draft_b26_plan_patch.md`) | `plan_tables_hash` 전후 측정 | P9 병합 순서 |
| B34 spec card 초안(#45) | 폴백 사이트는 부록 C.3(HEAD 줄 번호 = prep과 같음) | 사용자 `install.py` 작업(병합 전) |
| UD-15 결정 자료 | §7.1 비교표 + (3) mid 레일 공동분석 표(pushpull 두 회로의 `agnd` 연결: 커패시터 단자만 [prep]) | 없음 |
| B36 게이트 card 준비 | 도구 6개 glob 위치, V7 동적 import 간선 규칙, redteam 사례 | UD-15 |
| B37 영향 실측 | 9회로에서 `role` 유도 입출력을 넘길 때 `load_topology` meta 차이 | 없음 |
| `v3_scope_systemic.md`(아직 없음) | #48의 비용 근거(card별 V3 대상 def·변이 수) | 없음 |
| I-C11 공동분석 자료(UD-6) | nmcnr `stage2_diode_ref` 그룹 멤버·직렬 경로 표(`topology_to_markdown.py` 넷 기준 표, 메모리 '회로도 판독은 넷 표로 재검증'), two_stage `stage1_out` VDS 출처 표(F15의 M4·M2·M5) | 사용자와 공동분석 |
| #2·#3·#4 spec card 초안 | 계획 소비자 grep, `test_ic5` 두 행(F18) | UD-0 |
| TS4 대상 실측(V4 lint 산출) | D-1 삭제 시 TS4 대상 | 없음 |
| U-30 C4 대상 픽스처 전수(AST) | #28 기존 test 영향 | 없음 |
| U-27 병렬화 판단 자료 | 조합 독립 실행 가능 여부 | 없음 |
| DF-15 재현 시도 | red 입력 또는 계획 정정 요청 | 없음 |
| **#13 발동 계수 실측 준비**(CC-8 도구 병합 뒤 실행) | 부록 C.1 `I` 5지점 + C.2 스칼라 기본값 지점의 정본 실행·E-LIB 발동 계수 → 거부/계측 분류. 같은 AST 규칙에 `x.get(k) or <리터럴>` 형태를 더해 다시 센다(부록 A 측정 한계) | #9 |
| **#50 평가점 선정** | folded_cascode에서 두 레일 선언 모두 끝까지 도는 θ(하네스 θ* 또는 `_evaluate_once` 규칙 점), 감도 전파 섭동 평가가 끝나는지 | #21 |

### 8.2 Phase 3 진행 중

* 선두 5건(#5~#9) spec card 초안 -- 목적 모듈은 D0b 확정 뒤 파일:줄만 채운다.
* 파일 충돌 집합(§3.4)의 모듈 이름을 D0b로 확정.
* B33(V7 호출 그래프 간선 누락)이 G1에서 처리되는지 확인.

### 8.3 Phase 4 착수 뒤

* 선두 5건 사이에 나머지 묶음의 **작성 전 실측을 한 벌로** 뽑는다.
* U-27b 재생성은 `run_in_background` + 조합마다 체크포인트 -- #26 병합 즉시 시작.
* auditor 측정 재사용: E-LIB·E-INST base 산출물은 Phase 3 DoD 기록을 base로 재사용 **[미확인: Phase 3 DoD 기록 형식이 아직 없다]**.

### 8.4 V3 전신 변이 비용이 Phase 4 일정에 미치는 영향

**측정된 것(B26-1 한 card)** [prep: `review_b26_1.md` B1]: v0.2와 같다(def 약 32개, 변이 약 2,465개, 인벤토리 `load_topology` 230 등, registry 경유 metric 인벤토리 0).

**현재 사실(v0.3, 검토 M3)**: B28(V3 이력 복제본)은 **이미 병합됐다**(`2b41e79` merge, `8790b24` 판정 기록). `mutate_changed.py`는 지금 `--head` 격리 복제본에서 변이를 실제로 돌리고, **기준 실행 실패는 ERROR(exit 2)**다(`dee338d`). 따라서 P8·DF-36의 '사이트만 대체 측정' 선례는 Phase 4에서 쓸 수 없다.

**대응(v0.3)**: v0.2의 UD-13(decision으로 V3 범위를 좁힘)은 **게이트 변경 card #48로 바꿨다**(검토 S9). 판정 범위를 좁히는 일을 조정자가 decision으로 적용하면 기준 약화를 은폐하는 경로가 되기 때문이다. #48은 'diff가 닿은 문장 + 새 def'만 변이 대상으로 삼고, 제외한 변이 id를 도구가 출력한다(판정 기록에 그대로 남는다). redteam이 '닿은 문장의 변이는 여전히 죽어야 함'을 보인다.

**Phase 4 전반으로의 확장**: [미확인 -- `v3_scope_systemic.md` 없음]. 구조 추론(수치 아님):
1. 큰 def(`_build_theta_evaluator` 약 497, `propose_device_roles_gap_fill` 약 331)를 건드리는 card는 #48 없이는 매번 그 def 전체 변이를 낸다. 평가 커널 빌더를 고치는 card는 §3.4 기준 7건, `propose_device_roles_gap_fill`은 4건(#1·#45·#17·#47).
2. #48이 병합되면 변이 수는 닿은 문장 수에 비례한다. 수치는 `v3_scope_systemic.md`가 나오면 card별 열로 넣는다.
3. 완화책(원칙 안): (a) CC-7a 추출 (b) registry 경유 metric test는 함수 이름으로 직접 부른다(모든 metric card의 interface card 조건) (c) 같은 큰 def를 고치는 card의 V3는 병합 순서대로 background 실행, 결과는 파일에 (d) 평가 커널 빌더 분할은 6b.
4. 일정: U-27b 재생성(약 22시간)과 V3를 한 기계에서 동시에 돌리지 않는다 **[미확인: 병렬 시간 영향]**.

---

## 9. 열린 항목과 계획 정정 요청

N9.2-8은 "열린 질문이 없어야 한다"이다. v0.3의 남은 열린 질문은 **없다**:
* `v3_scope_systemic.md` 부재는 #48로 결정 경로가 바뀌어 비용 근거 자료로만 남는다(§8.4, 결정을 막지 않는다).
* I-C11은 UD-6(사용자 결정)으로 올렸다.
* 본문의 [미확인]은 전부 'card 작성 전 실측' 대상이고 설계 판단을 바꾸지 않는 수치다(E0 필드 이름, TS4 대상 수, B37 영향, DF-10 뿌리 동일, DF-23 행 수, Phase 3 DoD 기록 형식, 병렬 시간, #43 뒤 two_stage 해 존재 여부). 그중 설계를 바꿀 수 있는 것은 조건과 처리가 적혀 있다(TS4 대상 0 → 계획 정정, §10.1-4 발동 > 0이면서 원인 card가 Phase 4 밖 → N7 추가 요청).

아래는 계획 정정 요청이다(오케스트레이터, 경위는 history).

1. 계획 DF-29 행 닫힘(P5b 삭제), DF-09 행 닫힘(D-1 승인 시), TS4 행 "DF-09 등" → V4 lint 산출 목록, DEC-25의 `node_pole_estimate` 문장, DF-06 위치 열에서 `node_pole_estimate` 제거.
2. DF 위치 열 줄 번호 갱신 → 함수 이름 인용(DF-24 "3957행" → `derive_vsb_from_nodes`, §1.5-6 포함).
3. U-27 "SID_1F 열 추가" → "새 VS 축으로 함께 재스윕", 계획 158행, docstring·checklist.
4. DF-19 비고 "29개" 등 `draft_b26_plan_patch.md` §1~§6.
5. N3.16 PDK 상수 행: 엔진 폴백 15곳을 옛 이름(사본) 열에 추가.
6. **DF-01·DF-24 행에 vsb 조용한 기본값 사이트 추가**(SR `.get("vsb", 0.0)` 31곳, `setdefault` SD 4605 -- 부록 C.2).
7. **N4.2 V3 행과 `05` §10**: #48 게이트 변경 card가 문구를 바꾼다(plan_tables 승인).
8. **B21 (a) 매핑·P3c 재착수**: `tol_I`는 6b → P3c 재착수 위치 = 6b `tol_I` card 뒤. 조건 (b)는 #21, (c)는 #23에서 충족(Phase 2 DoD 기록의 'P3c 보류(B21, Phase 4)'를 '(6b)'로).
9. **N6.1 'TS4 첫 작업'**: #2가 Phase 3 전에 병합되지 않으면 Phase 4에서 #2가 TS4보다 앞선다 -- 그때 N6.1 순서 문구 정정(검토 M9).
10. **U-09(UD-6 결과가 (A)이면)**: I-C11 해소 Phase를 DEC-70·71 구현 Phase로, N6.1 Phase 4 범위 문구 'I-C11' → '실패 명시화', xfail 3건 reason의 만료 Phase 갱신(백로그 B12).
11. **Phase 3 design 교차 항목**(§3.1): D0b 원자료 재측정 조건 한 줄.
12. 백로그 추가(`backlog_additions.md`): **B38**(`classify_nets` `HINT_*` 이름 정규식의 바이어스 넷 추정 -- `ports`에 바이어스 역할 없음), **B39**(VS 0.2 V 간격 보간 오차 판단, P-5).

---

## 10. 인터페이스 (N9.2-2 -- v0.2 부록 B가 '보강판 과제'로 미뤘던 5건)

모듈 표기는 §3.1(D0b 확정 전 계획 MOD). 이름은 card 작성 전 test glob 충돌 grep 대상이다.

### 10.1 `fallback_events` (V8, #13)

**10.1-1 기록 단위와 함수**(MOD4, N3.14 예외·`FailureRecord`와 같은 계층):
```python
@dataclass(frozen=True)
class FallbackEvent:
    site: str        # "<모듈 이름>::<정규 이름>#<태그>" -- 줄 번호가 아닌 안정 id(태그는 한 함수 안 여러 지점 구분)
    kind: str        # 10.1-3의 어휘: "derivation_skipped" | "alternate_path" | "declared_default"
    device: str | None
    detail: str      # 첫 발생의 상세(선언 이름·대체된 값·원래 예외 타입)
    count: int       # 같은 (site, kind, device)의 발생 수

def record_fallback(site: str, kind: str, *, device: str | None, detail: str) -> None
def collect_fallbacks() -> ContextManager[list[FallbackEvent]]   # 실행 진입점이 연다
```
* 수집기는 `ContextVar` 하나(CC-7b의 계측 `ContextVar`와 같은 방식, 새 전역 가변 상태 없음). 실행 진입점(MOD10 `run_gmid_design_pipeline`, 그 전에는 `optimize_full_circuit_budget`)이 연다.
* 수집기가 열려 있지 않으면 `record_fallback`은 아무것도 하지 않는다. V8의 정의 범위가 '정본 spec 실행 결과'이고 계측은 출력만 바꾸므로 동작 경로에는 영향이 없다. 단위 test가 계측을 보려면 `collect_fallbacks()`를 직접 연다.
* 집계: (site, kind, device) 키 dict, 값 = 첫 detail + count(§4.4, NFR-2). 출력은 site 순 정렬 목록(결정론).

**10.1-2 산출 위치**: 성공 실행 = `optimize_full_circuit_budget` 결과 dict 키 `fallback_events` + `instance.json` 최상위 키 `fallback_events`. 실패 실행(#6 뒤 하네스가 쓰는 실행 기록 JSON) = 같은 키. 키가 없으면 E1 FAIL(계측 미배선).

**10.1-3 분류(부록 C의 처리 열 코드)**

| 코드 | 뜻 | `fallback_events` |
|---|---|---|
| R | 제거(거부로 교체) -- 담당 card 지정 | 아니오(사라진다) |
| I | 선언·유도 실패를 '없음'이나 다른 경로로 바꿈 → **계측** | 예, kind = `derivation_skipped`·`alternate_path` |
| X | 격자·후보점 배제(그 점을 쓰지 않을 뿐 값을 지어내지 않음) | 아니오 -- CC-4b(#10)가 잡는 타입을 LUT 정의역 오류로 좁힌다 |
| F | 탐색 후보 실패 기록(N3.14 '탐색 중 처리 = 실패 기록') | 아니오 -- `FailureRecord`(V8 밖) |
| N | 비운영·도구·구조화 반환(조용하지 않음) | 아니오 |
| D | 선언값 리터럴 기본값(`.get(k, <스칼라>)`·`setdefault`) | 10.1-4 규칙으로 R 또는 I(kind = `declared_default`) |
| C0 | 빈 컨테이너 기본값(`{}`·`[]`·`()`·`set()`) = '선택 선언 없음 = 빈 집합' 규약 | 아니오. 단 **필수 선언 키**의 빈 기본값이면 R(해당 card에서) |

**10.1-4 발동 규칙(D·I 지점)**: #13 작성 전 실측으로 지점마다 발동 계수를 잰다(CC-8 `activations_out` 방식, 대상 = 하네스 정본 실행 4회로 + E-LIB 9회로).
* 발동 0 → **R**(DEC-76 "발동 0인 폴백은 구현하지 않는다": 거부로 교체, 거부 메시지에 선언 이름).
* 발동 > 0 → **I**(계측)로 두고 원인 card를 지정한다(선언 추가·유도 규칙). V8 = 정본 실행 0이므로 Phase 4 DoD 전까지 원인 card가 병합돼야 한다. 원인 card가 Phase 4 범위 밖이면(예: vsb 기본값의 구조 제거 = 6b DF-01) 그 지점이 E1을 FAIL시키므로 **N7 추가 요청 대상**이다(N9.2-8). card 작성 전 실측에서 그런 지점이 나오면 이 design 개정으로 다룬다.
* 이미 담당이 있는 D 지점: `W_bounds`·`min_finger_w`(#28), `gm_id_bounds`·margin 0.05·`min_vds_by_role`·`_DEFAULT_METRIC_STAGE_BUDGET_GM_ID`(#38), `vsb` 기본값(10.1-4 적용 뒤 #24 또는 #22).

**10.1-5 계측 지점 전수**: 부록 C(핸들러 59, 스칼라·튜플 기본값 77, 빈 컨테이너 35, B34 21). 실측 도구·명령은 부록 A. Phase 3 뒤에는 같은 AST 규칙으로 MOD 파일에서 다시 센다(D0b 뒤 줄 번호 갱신).

### 10.2 공정 기록 JSON (U-30, #28)

* 파일: `A/pdk/sky130_fd_pr.process.json`(이름은 card에서 glob 충돌 grep) [prep: `prep_u27_u30.md` §3.4].
* 스키마(값은 SI m, 모든 값 항목에 출처):
```json
{
  "schema": "process_record/1",
  "pdk": {"name": "sky130_fd_pr", "commit": "<C:\\pdk\\sky130_fd_pr HEAD>"},
  "min_finger_w": {"value": 0.42e-6, "rule": "difftap.2", "source": "google/skywater-pdk docs/rules/periphery/periphery.csv"},
  "l_min":        {"value": 0.15e-6, "rule": "poly.1a",   "source": "(같은 파일)"},
  "l_grid_step":  {"value": 0.005e-6, "source": "sky130hs.tlef MANUFACTURINGGRID"},
  "vth0_slope":   {"source": {"file": "<mismatch.corner.spice 경로>", "params": {"nmos": "<param>", "pmos": "<param>"}}},
  "finger_pitch_overhead_m": {"value": null, "reason": "I-A12 미확보"},
  "passive_unit_area":       {"value": null, "reason": "U-36, 7b 전"}
}
```
* `vth0_slope` 값은 파일에 적지 않고 로더가 모델 파일에서 읽어 캐시한다(근거 하나).
* 로더(MOD1): `load_process_record(path) -> ProcessRecord`(실행당 1회, 미지 키·출처 없는 값 거부 = `SchemaRejectedError`). 유도: `w_bounds_lower(rec) = rec.min_finger_w`.
* 연결: U-27 npz 메타에 `process_record_sha256`. LUT 로드 때 해시가 다르면 거부.

### 10.3 `supply_roles` (UD-1 (C), #17)

* 자리만 계획에 둔다(첫 예외 회로와 함께 코드, 만들면 배선). 모양 [prep: `b26_decision_table.md` §1.4]:
```json
"supply_roles": {"<레일 넷>": {"role": "rail_high" | "rail_low" | "rail_mid"}}
```
* 게이트: 키 집합 = `supply_nets`(`_` 접두 제외), `rail_high`·`rail_low` 각 1 이상(**개수 상한 없음**), 구조 증거와 모순 거부, `supplies_v`가 있으면 min(high) > max(mid) > max(low).
* 선언이 없으면 구조 규칙(PMOS source만 = hi, NMOS source만 = lo, 둘 다 아님 = mid, 둘 다 = 거부).
* #17 코드가 만드는 것: `RailDeclaration`에 `polarity: Mapping[str, Literal["hi", "lo", "mid"]]` 필드(구조 규칙 결과).

### 10.4 `vdd` 유도 함수 (MG1, #21)

```python
@dataclass(frozen=True)
class RailVoltages:
    by_net: Mapping[str, float]   # supplies_v 그대로
    hi: float                     # max(by_net.values())
    lo: float                     # min(by_net.values())
    @property
    def span(self) -> float: ...  # hi - lo

def rail_voltages(spec: Mapping, rails: RailDeclaration) -> RailVoltages
```
* 모듈: MOD2(spec 로드 계층) [D0b 확정 뒤].
* 거부: `set(supplies_v) != set(rails.nets)` → `SchemaRejectedError`, spec에 스칼라 `vdd` → 옛 키 거부(CC-5 행).
* 계산은 spec 로드당 1회, spec 객체에 보관(평가 루프 안 호출 0 -- 계수 래퍼로 관찰).
* F4 20줄의 교체는 **읽기의 뜻으로 분류**한다: 레일 폭으로 쓰는 읽기(예: 7068 KVL 합 = vdd) → `span`, 가장 높은 레일 전위로 쓰는 읽기 → `hi`. 분류표는 #21 interface card에 줄마다 적는다. 원점 이동 전 4회로(최저 레일 0 V)에서는 두 뜻이 같은 값이라 #21은 equivalence가 성립한다. 뜻을 잘못 고른 줄은 #50·#22·#51의 IC11 불변으로 검출된다.
* 극성(#17)이 있으면 게이트가 `hi`의 넷이 `rail_high`인지 대조한다(UD-1 게이트 4번과 같은 규칙).

### 10.5 전후 비교표(E2) 정규화와 허용오차

* 비교 단위(회로마다): 결과 종류(θ* / N3.14 실패 클래스), θ*, metric 전부, `instance.json` 정규화 해시, 실패면 margin과 실패 전 setup 양(소자별 VGS·VDS·VSB·gm_id·W).
* 정규화: `json.dumps(obj, sort_keys=True)`에 float는 `float.hex`로, 경로 값 키는 `20-dead-code-dup` §3 E-INST 정의의 제외 규칙을 그대로 쓴다(재서술하지 않는다). 해시 = sha256.
* 허용오차: **기본은 비트 동일**(equivalence·무동작 card). 동작 변경 card는 차이를 허용오차로 흡수하지 않고 항목마다 원인 card id와 DEC-40 승인 id를 붙인다(차이 = 기록 대상). 예외는 원점 이동 불변(IC11, #50·#22·#51)뿐이며 식은 10.6이다.

### 10.6 IC11 감도 전파 허용오차 (#50 판정기)

계획 N4.1 IC11: "VGS·VDS·VSB·gm_id·W·metric(dc·ss·ls 전부)이 허용오차(전압 tol_V, 그 밖은 tol_V 섭동의 감도 전파값) 안에서 같음". 이를 다음 식으로 적는다.
* 두 레일 선언 S_A(현 `supplies_v`)와 S_B(모든 레일을 같은 Δ만큼 이동: folded는 (1.8, 0) → (0.9, −0.9))로 같은 θ 평가점을 평가한다.
* 전압 양 q ∈ {VGS, VDS, VSB}(소자별): |q_A − q_B| ≤ tol_V(kind, L, VDS_A)(#23의 MOD1 함수).
* 그 밖의 양 q(소자별 gm_id·W, metric 전부): |q_A − q_B| ≤ tol_q,
  tol_q = max_{r ∈ supply_nets} |q(S_A에서 레일 r만 +τ) − q(S_A)|, τ = 평가점의 모든 소자에 대한 tol_V(kind, L, VDS)의 최댓값.
  (일차 유한 차분 = 'tol_V 섭동의 감도 전파'. 레일 하나만 움직이면 레일 폭이 바뀌므로 전압 의존 양은 0이 아닌 감도를 얻는다.)
* tol_q = 0인 양(전압과 무관한 양)은 비트 동일을 요구한다. 전압과 무관하면 같은 입력에서 같은 연산이므로 성립해야 한다.
* 섭동 평가가 실패하면(infeasible) 판정은 ERROR다(PASS로 세지 않는다).
* DF-24 검출력: base(#22 전)에서 nmos vsb는 S_B에서 |Δ| = 0.9 V만큼 틀린다(F16의 M7·M8). tol_V(LUT 보간 오차)가 이보다 작아야 red가 된다 -- #50이 xfail strict로 **실제 실패가 나는 것**을 판정 기록에 남긴다.
* 소유: test 쪽 helper(`A/tests/contracts/`, test-author). 엔진 함수로 만들지 않는 이유 = Phase 4에 엔진 소비자가 없다(봉인은 6b). 소비자는 같은 card의 `rail2` test다(만들면 배선).
* V4: 기대값(S_A 결과)이 피검 함수 호출로 만들어지므로 규칙 (1) 발견이 난다. 불변식·재현성 test의 선례 `20260923-c9-v4-exempt`와 같은 모양의 **V4 규칙 (1) 면제 승인 1건**이 #50의 착수 조건이다(§7.3). 규칙 (2)(식 복사)는 해당 없음(허용오차는 섭동 실행 결과이지 피검 식의 재서술이 아니다).

---

## 11. I-C11 해소 설계 (N9.1 필수, U-09)

### 11.1 현 상태(HEAD 실측, F15)

| 회로 | 실패 | 원인 기록 |
|---|---|---|
| two_stage_ota | `_hr_verify_group_kvl_sum`의 `ValueError`: `stage1_out` 그룹 VDS 합 2.37965 V ≠ vdd 1.8 V(diff +0.579654 V). M4 = 0.9172(`vds_match_vgs_of` M6 -- DC), M2 = 0.9(compensation -- AC 목표에서 정함), refs M5 = 0.5625(헤드룸) | 세션41(`.ai/context.md` 12380~12440행): 사용자가 `stage1` → `stage1_ref`/`stage1_out` 분리를 "올바른 방향이니 유지"로 확정, M4+M2+M5 불일치는 "DC/AC 조율 없이는 못 푸는 문제" |
| nmcnr_amplifier | 모든 θ 격자점 infeasible. 마지막 사유: `stage2_diode_ref` 그룹 예산 1.5 V 중 0.525 V를 배정할 곳이 없음(구간 제약 diode M203 ∈ [0.6375, 0.975]) | 엔진 메시지 자체가 "이 컬럼에 선언되지 않은 소자/수동소자가 있거나 vertical_stack_id 선언이 실제 직렬 경로와 다르다"고 가리킨다 |

둘 다 N3.14 클래스가 아닌 `ValueError`이고 하네스는 exit 0이다. 관련 test: xfail strict 3건 + known_limitation 3건(`20260922-c9-ic11-split`), V4 면제 2건(`20260923-c9-v4-exempt`, 'Phase 4 I-C11 해소 시 재검토' 명시, 백로그 B9·B12).

### 11.2 무조건 하는 것 -- #43 실패 명시화

원칙(조용한 실패 금지, N3.14)만으로 정해진다. KVL 불일치·예산 배정 불가를 `SealViolationError`(항목 = 기둥 KVL, 소자 목록, 위반 크기, margin = 위반/`tol_V`)로 바꾸고, 탐색은 후보 실패로 기록한 뒤 계속한다. 모든 시작점이 실패하면 `SearchFailedError`(exit 6). 결과: 두 회로의 E1·E2 행이 '실행 끝 = 실패 클래스'로 판정 가능해진다. 메시지 문구('stage1_out', 'KVL')는 유지해 known_limitation test 3건이 계속 성립한다. θ 격자 다른 점에서 해가 나올 수 있는지는 [미확인]이다(#43 병합본에서 E2가 기록한다).

### 11.3 해소 선택지(UD-6)

| 안 | 내용 | 일반성(DEC-62) | 계획 영향 | 동작 영향 |
|---|---|---|---|---|
| (A) 계획 정정 | Phase 4는 11.2까지. 해소는 DEC-70(AC·대신호 → DC 되먹임: AC 결과는 θ의 제약으로만 되돌아간다)·DEC-71(기둥 조립)을 구현하는 Phase로 | 엔진 무변경 | U-09 재결정(N7), xfail 3건 만료 Phase 갱신, N6.1 Phase 4 범위 문구 'I-C11' → '실패 명시화' | 없음(11.2만) |
| (B) DEC-70 부분 선행 | 직렬 그룹의 KVL을 정본으로 두고, compensation이 정한 VDS는 고정값이 아니라 θ 제약(위반 = 후보 실패)으로 되돌린다. 이름 없는 규칙이라 두 회로 외에도 적용된다 | 규칙은 topology 무관 | DEC-70 상태 '미구현' → 부분 구현, Phase 배정 변경(계획 개정) | current_reuse·folded에도 적용된다 -- 무동작 증명 또는 DEC-40 |
| (C) topology 선언 정정 | 회로별 공동분석으로 선언을 바로잡는다: nmcnr `stage2_diode_ref` 멤버·직렬 경로(엔진 메시지가 가리키는 쪽), two_stage `vds_match_vgs_of`·compensation `stage_devices` | 데이터만 바뀐다(DEC-62 경로) | topology 수정은 사용자 확인 + 승인 기록(WP-07, U-16) | 그 회로만. S0 지문 변경 → `review_needed` |

* **권고**(§7.1 UD-6): nmcnr = (C)부터(원인이 선언이면 엔진을 바꿀 이유가 없다 -- 공동분석으로 확인), two_stage = (A)(DC/AC 조율은 DEC-70의 설계 몫이고, 세션41에 사용자가 별도 설계로 넘겼다). 이 권고는 회로 해석과 계획 범위 판단이라 결정은 사용자 몫이다.
* 어느 안이든 #44(또는 계획 정정)가 할 일: 해소된 회로의 xfail strict 해제(XPASS → 해제), known_limitation test 정리, V4 면제 2건 재검토(승인 기록의 '재검토' 절), 백로그 B12(xfail reason 만료 절) 처리.

---

## 부록 A. 재측정 명령과 결과

`R` = 저장소, `A` = `R/skills/analog-gmid-design/assets`, `$PY` = `C:/Python314/python.exe -B`. v0.2 표(A1~A11, `C:/g36`, cd64170)는 `draft_phase4_design.v02.md` 부록 A 그대로이고, 엔진·하네스가 HEAD까지 변경 0이라 값이 유지된다.

v0.3(스크래치 `C:/g48`, 끝나면 삭제):

| # | 명령 | 결과 |
|---|---|---|
| B1 | `git -C R rev-parse --short HEAD`, `git -C R diff --stat cd64170 HEAD -- skills workspaces tools`, `ls R/.ai/approvals \| wc -l` | `7535799`, skills·workspaces 0, tools 5파일(B28), 승인 42 |
| B2 | `git -C R archive HEAD skills/analog-gmid-design skills/analog-grammar workspaces/run_harness.py tools docs install.py \| tar -x -C C:/g48/repo` | 격리 사본 |
| B3 | `runall.sh`: 사본의 `workspaces/`에서 `$PY run_harness.py <key>` 4회로 병렬, 로그 `C:/g48/run_<key>.log`, 요약 `run_summary.txt`. folded는 보고 디렉터리를 만든 뒤 단독 재실행(`run_folded_cascode_2.log` -- 첫 실행은 사본에 보고 디렉터리가 없어 저장 단계에서만 `FileNotFoundError`, θ*까지는 같음) | F15 (rc 전부 0; two_stage 36 s, nmcnr 36 s, folded 43 s 단독, current_reuse 411 s 병렬) |
| B4 | `m.py`: AST로 (i) `raise` 없는 except 핸들러 (ii) `.get(<str>, <리터럴>)` (iii) `setdefault` (iv) `json.load(s)`·깊은 복사 관용구 (v) SD `_import_analog_grammar` 호출·`is None` 줄 (vi) library `ports` 모양 (vii) 레일 이름 문자열 상수 (viii) `_parse_output` 본문 (ix) `test_ic5` 표 대조 줄 (x) `test_ic11.py` (xi) `derived_spec` 사용처 (xii) `install.py` `SKILLS` → `m.json` | F17~F24, 부록 C |
| B5 | `reach.py`: `tools/gates/reachability.build_graph`로 사본 엔진+하네스 그래프, `gate_config.json` `reachability_roots.before_phase3`에서 도달(384 노드) → 지점별 운영 도달 → `reach.json` | 부록 C '운영 도달' 열. 중첩 함수는 이름 끝 부분으로만 맞춰 근사(`_known_vds` 등 '아니오(근사)') |
| B6 | `appc.py`·`appc2.py`: B4·B5 결과를 부록 C 표로 | 부록 C |
| B7 | folded·current_reuse topology에서 `kind == nmos`이고 source ∉ `supply_nets`인 소자 계수 | F16 |

측정 한계: AST 규칙은 문자열 키의 `.get`·`setdefault`와 `raise` 없는 핸들러만 센다(변수 키, `or` 기본값(`x.get(k) or 0.0`), 조건식 대입은 세지 않는다 -- #13 작성 전 실측에서 같은 규칙에 `BoolOp(or)` 기본값을 더해 다시 센다). 운영 도달은 V7 그래프의 이름 과대 근사를 물려받는다(Phase 3 v3 §2.3).

## 부록 B. N9.2 필수 절 대응

| N9.2 | 이 문서 |
|---|---|
| 1 범위 | §1 |
| 2 인터페이스 | §4.3 표(새 것·소비자), §3.1(목적 모듈), **§10(`fallback_events`·공정 기록·`supply_roles`·`rail_voltages`·E2 정규화·IC11 허용오차)** |
| 3 판정식 | E-LIB·E-INST·NEW-TOPO는 `20-dead-code-dup` §3, 무동작은 `00-common` §11.4, **E2는 §10.5, IC11은 §10.6**, #19 lint 규칙은 §5.4 |
| 4 실패 경로 | N3.14 + `00-common` §7(#6), #43(I-C11 → `SealViolationError`/`SearchFailedError`), §10.1(`fallback_events`와 실패 레코드의 경계) |
| 5 역할별 산출물 | §5 |
| 6 DoD 측정 명령 | §6 |
| 7 착수 조건 | §7.3(U-04·05·09·26·27·30 승인 기록 0 -- F11, #48·#46 게이트 변경 승인, #50 V4 면제), Phase 3 DoD PASS, 이 문서 승인 |
| 8 열린 질문 | §9 -- 없음(사용자 결정 UD-1·4~10·14·15와 계획 정정 요청만) |

## 부록 C. 조용한 폴백 후보 전수 (HEAD `7535799`, `A/*.py` + 하네스)

처리 코드는 §10.1-3. `#n` = 담당 card. 운영 도달 = 부록 A B5(근사).

### C.1 예외를 다시 던지지 않는 except 핸들러 (59)

| 파일 | 줄 | 함수 | except 타입 | 운영 도달 | 처리 |
|---|---|---|---|---|---|
| audit_current_forced.py | 164 | `<module>` | `Exception` | 아니오(근사) | N (도구·정리: 운영 판정 밖) |
| run_harness.py | 476 | `run` | `ValueError` | 예 | R #6 (CC-4a exit code) |
| run_harness.py | 512 | `run` | `Exception` | 예 | R #6 |
| run_harness.py | 528 | `run` | `Exception` | 예 | R #6 |
| sizing_recipe.py | 447 | `_idu_scan` | `ValueError` | 예 | X #10 |
| sizing_recipe.py | 893 | `find_optimal_sizing` | `ValueError,ZeroDivisionError` | 예 | X #10 |
| sizing_recipe.py | 1630 | `lut_vdsat_headroom` | `Exception` | 예 | R #13 (DF-14) |
| sizing_recipe.py | 1766 | `_known_vds` | `Exception` | 아니오(근사) | R #13 (DF-14) |
| sizing_recipe.py | 2081 | `search_gm_id_for_role` | `ValueError` | 예 | X #10 |
| sizing_recipe.py | 2172 | `measure_L_knee` | `ValueError,KeyError` | 예 | X #10 |
| sizing_recipe.py | 2586 | `feasible_L_window` | `ValueError` | 예 | X #10 |
| sizing_recipe.py | 2679 | `derive_role_L` | `KeyError,ValueError` | 예 | I #13 |
| sizing_recipe.py | 2737 | `derive_class_L` | `KeyError,ValueError` | 예 | I #13 |
| sizing_recipe.py | 3170 | `solve_diode_connected_vds` | `ValueError` | 예 | X #10 |
| sizing_recipe.py | 3219 | `diode_vds_cached` | `DiodeSelfConsistencyError` | 아니오(근사) | X #10 |
| sizing_recipe.py | 3462 | `diode_vds_window` | `ValueError,KeyError` | 예 | X #10 |
| sizing_recipe.py | 3474 | `diode_vds_window` | `ValueError,KeyError` | 예 | X #10 |
| sizing_recipe.py | 3538 | `solve_stacked_diode_pair` | `ValueError,KeyError` | 예 | R #15 (DF-11 `idu_up = 1.0`) |
| sizing_recipe.py | 3563 | `solve_stacked_diode_pair` | `ValueError,KeyError` | 예 | X #10 |
| sizing_recipe.py | 3975 | `node_pole_estimate` | `KeyError,ValueError` | 아니오(근사) | R #3 (D-6 `node_pole_estimate` test 이관) |
| sizing_recipe.py | 4054 | `_mna_stamp_capacitance` | `KeyError,ValueError` | 아니오(근사) | R #12 (DF-06 `_mna_stamp_capacitance`) |
| sizing_recipe.py | 5790 | `_score_and_apply` | `ValueError` | 예 | X #10 |
| sizing_recipe.py | 5809 | `_score_and_apply` | `KeyError` | 예 | R #13 (DEC-76: 코드 주석이 '이론상 도달하지 않음'이라 적은 방어 폴백 -- 발동 0 확인 뒤 거부) |
| sizing_recipe.py | 6739 | `check` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 6802 | `check` | `ValueError` | 예 | X #10 |
| sizing_recipe.py | 7297 | `_hr_resolve_vertical_group` | `Exception` | 예 | R #13 (DF-14) |
| sizing_recipe.py | 7376 | `_hr_resolve_vertical_group` | `ValueError,KeyError` | 예 | X #10 |
| sizing_recipe.py | 7451 | `_hr_resolve_vertical_group` | `Exception` | 예 | R #13 (DF-14) |
| sizing_recipe.py | 7801 | `achievable_metric_bound` | `Exception` | 아니오(근사) | N (seed 실패를 notes에 기록, DF-14 밖) |
| sizing_recipe.py | 7962 | `_build_theta_evaluator` | `KeyError,ValueError` | 예 | I #13 |
| sizing_recipe.py | 8457 | `_evaluate` | `KeyError,ValueError` | 예 | I #13 |
| sizing_recipe.py | 8639 | `_evaluate` | `_HeadroomDependencyNotReady` | 예 | N (내부 제어 신호 `_HeadroomDependencyNotReady` -- 다음 패스에서 재시도, 값 대입 없음) |
| sizing_recipe.py | 9034 | `diagnose_sizing_roles_gap` | `ValueError` | 예 | N (하네스 진단 경로 `diagnose_sizing_roles_gap`) |
| sizing_recipe.py | 9219 | `optimize_full_circuit_budget` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 9807 | `derive_theta_dependency_graph` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 9819 | `derive_theta_dependency_graph` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 9824 | `derive_theta_dependency_graph` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 9997 | `extract_linear_feasibility_constraints` | `ValueError` | 예 | N (거부를 구조화 레코드로 반환 -- 조용하지 않음) |
| sizing_recipe.py | 10355 | `search_stage_budget_L_warm_start` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 10476 | `_probe` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 10479 | `_probe` | `Exception` | 예 | R #13 (DF-14) |
| sizing_recipe.py | 10756 | `presolve_warm_start` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 10770 | `presolve_warm_start` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 10959 | `_objective_fn` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 10969 | `_fn` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 11025 | `_optimize_theta_slsqp` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 11047 | `_callback` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 11061 | `_optimize_theta_slsqp` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 11197 | `_optimize_theta_slsqp_block_coordinate` | `ValueError` | 예 | I #13 |
| sizing_recipe.py | 11452 | `apply_and_revalidate_pair_adjustment` | `ValueError` | 예 | N (거부를 구조화 레코드로 반환 -- 조용하지 않음) |
| sizing_recipe.py | 11565 | `apply_and_revalidate_matching_finger_growth` | `ValueError` | 예 | N (거부를 구조화 레코드로 반환 -- 조용하지 않음) |
| sky130_lut_sweep.py | 253 | `_cleanup_temp` | `FileNotFoundError` | 예 | N (도구·정리: 운영 판정 밖) |
| sky130_lut_sweep.py | 255 | `_cleanup_temp` | `OSError` | 예 | N (도구·정리: 운영 판정 밖) |
| stick_diagram.py | 374 | `_try_pattern_table_match` | `ValueError` | 예 | X (패턴표 후보 배제 → 다음 후보) |
| stick_diagram.py | 1057 | `_import_analog_grammar` | `ImportError` | 예 | R #45 (B34) |
| stick_diagram.py | 4818 | `_verified_euler_fix` | `ValueError` | 예 | X (Euler 검사 불가 → '검증 안 됨' 반환, 수리 후보 배제) |
| stick_diagram.py | 4911 | `audit_vertical_stack_id_euler_feasibility` | `ValueError` | 아니오(근사) | R #2 표 행 / #41 함수 (D-5) |
| stick_diagram.py | 8977 | `_topology_ref_relpath` | `ValueError` | 예 | N (다른 드라이브 → 바로 아래에서 거부) |
| topology_to_markdown.py | 191 | `<module>` | `Exception` | 예 | N (도구·정리: 운영 판정 밖) |

계수: F 14, I 5, N 11, R 14, X 15 (합 59)

`X #10` = 격자·후보점 배제(값을 지어내지 않음), CC-4b가 잡는 타입을 LUT 정의역 오류로 좁힌다(DF-27 뒤 `lut_axis_out_of_range`). `F #10` = 탐색 후보 실패 기록(`CANDIDATE_FAILURE_CLASSES` 이름으로), V8 밖. `I #13` = 선언·유도 실패를 '없음'·다른 경로로 바꿈 → `fallback_events` 계측 + §10.1-4 발동 규칙.

### C.2 선언값 리터럴 기본값 `.get(<문자열 키>, <스칼라·튜플>)` (77) + `setdefault` 선언 기본값 (2)

| 파일 | 키 | 기본값 | 줄(곳 수; 함수) | 운영 도달 | 처리 |
|---|---|---|---|---|---|
| run_harness.py | `search_method` | `'grid'` | 447 (1; `run`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `ID` | `0` | 7261, 7274, 7404 (3; `_hr_resolve_vertical_group`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `W_bounds` | `(1e-06, 0.0002)` | 1626, 2697, 2748, 3623, 5763, 6055, 6731, 7266, 7462, 8716 (10; `_evaluate`, `_feed_metric_stage_budget`, `_hr_resolve_vertical_group`, `_make_shared_current_scorer`, `apply_diode_self_consistent_gm_id`, `derive_class_L` 외) | 예 | R #28 (U-30 엔진 폴백) |
| sizing_recipe.py | `aggregate` | `'max'` | 4379 (1; `_mirror_ratio_aggregate`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `complement_key` | `'t_lln'` | 5558, 9635 (2; `_feed_settling_split`, `_theta_feed_footprint`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `freq` | `1.0` | 3054 (1; `_metric_flicker_plus_thermal_sum`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `gds` | `0.0` | 3960 (1; `node_pole_estimate`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `gm` | `0.0` | 3960 (1; `node_pole_estimate`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `gm_id_bounds` | `(2.0, 30.0)` | 5521, 9298, 9372 (3; `_evaluate_row_split`, `_feed_gm_target_convention`, `optimize_full_circuit_budget`) | 예 | R #38 (DF-20 격자 리터럴) |
| sizing_recipe.py | `margin` | `0.05` | 1564 (1; `_default_cascode_headroom`) | 예 | R #38 (DF-20 margin 0.05) |
| sizing_recipe.py | `max_finger_w` | `4e-05` | 9273 (1; `optimize_full_circuit_budget`) | 예 | #28 (탐색 설정 공통 한 곳으로, P-4) |
| sizing_recipe.py | `max_layout_retry_rounds` | `6` | 9485 (1; `optimize_full_circuit_budget`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `max_split_per_stack` | `6` | 9484 (1; `optimize_full_circuit_budget`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `maxiter` | `80` | 11172 (1; `_optimize_theta_slsqp_block_coordinate`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `metric` | `'gain_db'` | 5691, 6012 (2; `_build_shared_current_joint_plan`, `_feed_metric_stage_budget`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `min_finger_w` | `1e-06` | 9273 (1; `optimize_full_circuit_budget`) | 예 | R #28 |
| sizing_recipe.py | `min_vds` | `0.0` | 7308, 7321 (2; `_hr_resolve_vertical_group`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `n_samples` | `0` | 2789 (1; `estimate_area_budget`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `output_key` | `'t_slew'` | 5556, 9634 (2; `_feed_settling_split`, `_theta_feed_footprint`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `sense_den` | `'common'` | 5038 (1; `_metric_smallsignal_ratio_db`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `sense_mode` | `'diff'` | 5054 (1; `_metric_smallsignal_gain_db`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `sense_num` | `'diff'` | 5036 (1; `_metric_smallsignal_ratio_db`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `sign` | `1` | 5411, 9994 (2; `_feed_root_signed_sum`, `extract_linear_feasibility_constraints`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `stage_objective` | `'power'` | 8164 (1; `_evaluate`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `temperature_K` | `300.0` | 3055 (1; `_metric_flicker_plus_thermal_sum`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `total_key` | `'t_settle_total'` | 5557 (1; `_feed_settling_split`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `type` | `''` | 2300 (1; `gain_stage_tails`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `vsb` | `0.0` | 1527, 1629, 1765, 2695, 2746, 2935, 3067, 3314, 3389, 3665, 3974, 4053, 4625, 5504, 5789, 5802, 6026, 6053, 6116, 7138, 7175, 7302, 7454, 8714, 8776, 8788, 8838, 8838, 8864, 10223, 11332 (31; `_evaluate`, `_feed_gm_target_convention`, `_feed_metric_stage_budget`, `_hr_resolve_vertical_group`, `_known_vds`, `_metric_flicker_plus_thermal_sum` 외) | 예 | #13 발동 규칙 + #24(DF-01) -- §10.1-4 |
| stick_diagram.py | `sign` | `1` | 3772 (1; `propose_theta_kcl_gap_fill`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |

표 = 스칼라·튜플 기본값 77곳. 빈 컨테이너 기본값(`{}`·`[]`·`()`·`set()`) 35곳(25종)은 표에서 뺐다(§10.1-3 분류 C0).

`setdefault`의 선언 값 기본값: SR 7579 `_hr_resolve_vertical_group` `other_entry.setdefault("vsb", ref_vds)`(DF-01 원인 코드, #24), SD 4605 `apply_device_roles_gap_fill` `entry.setdefault("vsb", 0.0)`(topology `device_roles`에 vsb 0 V 가정을 **기록**하는 W-3 도구 경로 -- #42와 §10.1-4). 나머지 `setdefault` 47곳은 캐시·집계용 내부 dict(`'_cache'`, union-find `find`, 목록 누적)라 선언 기본값이 아니다(C0).

### C.3 analog-grammar 부재 폴백 (B34, #45에서 전부 R)

`prep_b34_b35_grammar.md` §1.2 표 그대로(엔진 변경 0이라 줄 번호 HEAD 동일, `_import_analog_grammar` 호출 줄 1045·1072·1088·1312·1444·1713·1893·2258·2399·2494·3380·3528·4070 [재측정 v0.3]).
* 직접 12: `find_idiom_matches` 1072~1074, `find_stack_edges` 1088~1090, `find_differential_and_mirror_forks` 1312~1314, `suggest_vertical_stack_composites` 1444~1446, `find_verified_differential_and_mirror_relations` 1713~1715, `_propose_vertical_stack_ids` 1893~1895, `_propose_headroom_roles` 2258~2260, `refine_differential_and_mirror_relations` 2399~2401·2410 및 2494~2495, `audit_theta_root_direction` 3380~3382, `propose_theta_kcl_gap_fill` 3528~3531, `propose_device_roles_gap_fill` 4070~4073·4087.
* 전파 9: `find_differential_pair_candidates` 1543, `_propose_gm_id_roles` 2092, `_propose_L_roles` 2165·2169, `refine_…` 2420·2440, `propose_device_roles_gap_fill` 3966~3970, `propose_vertical_stack_id_gap_fill` 3296, `geometry_colocation_union` 3115~3116, `load_topology` 8668~8737, SR `_build_theta_evaluator` 7952(게이트가 막을 재료를 잃음).
* `unavailable_reason` 반환 2곳(SD 3531·3535·3540 `propose_theta_kcl_gap_fill`, 3968 `propose_device_roles_gap_fill`) -- 소비처 0, 삭제.

### C.4 계수 요약

| 분류 | 수 | 처리 |
|---|---|---|
| R(제거) | 핸들러 14 + 기본값(`W_bounds` 10·`min_finger_w` 1·`gm_id_bounds` 3·margin 1) + B34 21 | 담당 card |
| F(실패 기록) | 핸들러 14 | #10 |
| X(후보 배제) | 핸들러 15 | #10 |
| I(계측) | 핸들러 5 | #13 |
| D(발동 규칙) | 기본값 약 62(vsb 31 포함) + `setdefault` 2 | #13 §10.1-4 → R 또는 I |
| N(비운영·구조화) | 핸들러 11 | 없음 |
| C0(빈 컨테이너) | 35 | 없음(필수 선언 키면 해당 card에서 R) |
