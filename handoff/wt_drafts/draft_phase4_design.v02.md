# gain-budget-gmid-sizing -- Phase 4 `40-defect-fixes` design

> **[초안 v0.2 -- 저장소 미반영]** 정식 경로(계획 N9.1): `docs/02-design/features/gain-budget-gmid-sizing.40-defect-fixes.design.md`(현재 없음).
> 측정 시점 = gate `master` `cd64170`(2026-09-30). 저장소·worktree 쓰기 0, git 상태 변경 0. 재측정 스크래치 `C:/g36`(`remeasure.py` → `remeasure.json`, 끝나면 삭제).

버전 v0.2(초안). v0.2 변경: 입력 두 개(`prep_b34_b35_grammar.md`, `review_b26_1.md`)를 반영했다. 그 결과 §9의 열린 항목 1·2를 닫았고, card 3건(B34·B36·B37)을 더했으며, B35를 B26-2 SD 호출부 어댑터로 흡수했다. 결정 3건(UD-13 B26-1 V3 처리, UD-14 B26-1 앞당김 승인, UD-15 analog-grammar 소속·게이트 편입)을 추가했고, §8.4에 V3 전신 변이 비용을 적었다. 정본 인용 규칙은 계획 N9.4 -- 이 문서는 계획서·`00-common`·`05`·`10`·`20`·Phase 3 초안(`30-module-split` v2)의 정의를 재서술하지 않고 절 번호로 인용한다.
읽은 계획 절(N9.1 `40-defect-fixes` 행): N5.2 전체, N3.6, N3.10, N3.14, N3.16, N4.1 IC11, N6.1·N6.2 Phase 4, N6.3, `00-common` §6·§7·§10·§11·§14·§18, DEC-40·47·51·60·61·62·69, I-C11, U-04·05·09·26·27·30. N9.2 필수 절 대응은 부록 B.

**표기 규칙(이 문서 전체)**
* **[재측정]** = 이 초안 작성 때 `C:/g36/remeasure.py`로 cd64170에서 다시 잰 사실(§2, 부록 A).
* **[prep]** = 입력 준비 문서의 실측을 인용했고 이 초안에서 다시 재지 않았다. card 작성 전 실측(card 처리 속도 규칙)에서 다시 잰다.
* **[미확인]** = 실측 근거가 없는 문장(추정·설계 제안). 이 표시가 붙은 것은 착수 전 확인 대상이다.

**입력 문서**(`C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/`): `prep_phase4_scope.md`, `prep_b26_supply_nets.md`, `draft_b26_1.spec.md`, `draft_b26_plan_patch.md`, `b26_decision_table.md`, `prep_u27_u30.md`, `prep_deferred_rows.md`, `backlog_additions.md`, `user_decisions.md`, `draft_phase3_design_v2.md`, (v0.2) `prep_b34_b35_grammar.md`, `review_b26_1.md`.
**아직 없는 입력**: `v3_scope_systemic.md`(V3 전신 변이 비용 측정). 작성 시점에 `_drafts/`에 없었다(ls 확인). 그래서 §8.4의 Phase 4 전반 수치는 [미확인]이고, B26-1 한 card의 수치만 `review_b26_1.md` B1에서 인용했다.

---

## 1. 목표와 범위

### 1.1 목표

Phase 4는 **동작을 바꾸는 첫 Phase**다. 계획 N5.2가 Phase 4에 배정한 결함(DF)을 red-green으로 고치고, 이후 Phase가 쓰는 공통 기반(N3.14 실패 규약, 옛 키 게이트, 성능·무동작 계측 도구)을 먼저 깐다. 끝나면 (1) 엔진이 실패를 삼키지 않고 N3.14 클래스와 exit code로 드러내며 (2) 레일·PDK 상수가 선언 한 곳에서만 오고(이름 집합·사본 0) (3) 조용한 폴백이 `fallback_events`로 계측되어 정본 실행에서 0이고 (4) 사이징 대상 회로의 전후 비교표가 판정 기록으로 남는다.

### 1.2 계획 원문

N6.1 Phase 4 행(계획 1001행):
> | 4 | TS4 → DF-35 → DF-36 → `00-common` CC-4의 앞부분(실패 클래스·`FailureRecord`·`exit_code_for`와 DF-37의 하네스 `run()` 몫) → CC-7·CC-8(측정·무동작 도구가 이후 card에 쓰이도록 Phase 4 앞쪽에 둔다) → 나머지. Phase 4 전체 범위: TS4, DF-01~15·18~20·22~24·26·27·35~37, **DF-34의 Phase 4 몫**(회로별 `_spec_*()`이 따로 복사한 PDK 상수 제거 -- 함수 자체를 데이터 항목으로 바꾸고 삭제하는 것은 7b다), MG1 레일 이름 변경(DEC-69), U-27 LUT 재생성, PDK 상수 한 곳 선언(U-30), Phase 2에서 배선을 고른 함수 배선, `fallback_events` 계측(V8), 기존 4개 회로 실행 가능성(I-C11), IC11 활성 | red-green | U-04, U-05, U-09, U-26, U-27 | `40-defect-fixes` |

N6.2 Phase 4 완료 조건(1019행):
> DF마다 red-green, V8 도입(정본 실행 `fallback_events` 0), 사이징 대상 회로 실행과 전후 비교표, IC11 2레일 케이스 PASS, MG1 옛 키(계획 `supplies`, spec 스칼라 `vdd` 선언, metric 인자 `supply_nets`) 거부 test PASS, DF-27 VS 축 밖 픽스처 거부, U-27 재생성 LUT의 옛 격자점 값 대조 기록(다르면 원인 보고, 기준선 변경은 DEC-40 승인), U-30 PDK 상수 교체 전후 self-test·사이징 대상 회로 비교표(`min_finger_w` = difftap.2 출처 기록, 바뀌는 기준선·기대값은 DEC-40 승인)

N9.1 `40-defect-fixes` 행(1158행, 반드시 담을 것 요지): DF별 red 형태와 수정 범위, N3.14 실패 클래스 도입, tol_V 함수 선도입, U-04·U-05, `fallback_events` 스키마와 계측 지점 전수, exit code, I-C11 해소 설계, `supply_nets`·`supplies_v` 레일 판정(DF-19·26)·vsb(DF-24)·IC11, MG1, DF-27 축 커버리지 게이트, U-27 절차·대조, U-30 선언과 전후 비교, `00-common` CC-4·CC-5·CC-7·CC-8, DF-35·36.

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
| U-27 LUT 재생성·옛 격자점 대조 | U-27(확정) | LUT·PDK |
| V8 `fallback_events` | N4.2 844행 V8 | 실패 규약(DF-14와 한 card) |
| I-C11(U-09) | 979행 | 회로 |
| IC11 rail2 활성 | N4.1 829행 | 레일 |
| 보류 행 배선(Phase 2에서 '배선'을 고른 함수) | N6.1 "Phase 2에서 배선을 고른 함수 배선" | 배선·삭제 |
| 백로그 B21(a)(c)·B24·B26 | `.ai/context.md` 14939·14954·14963행 [prep] | 노드전압 / LUT / 레일 |

### 1.4 범위 밖(명시)

* **이미 끝남**: DF-35(`34bc75e`), DF-36(`148bd6d`) -- Phase 2 진행 중 앞당겨 처리. 인용만 한다 [prep: `prep_phase4_scope.md` §0-2].
* **삭제로 해소**: DF-29 대상 5함수가 HEAD에 없다(P5b `d7bce7a`) [prep: 같은 문서 §0-3]. 계획 DF-29 행 닫힘 기록은 계획 정정(§9).
* **다른 Phase**: DF-16·28·30(7a), DF-21(2), DF-25(6b), DF-31·33·DF-34의 함수 삭제 몫(7b), DF-32(6b·6c), IC11 rail3·reject(6a, `test_ic11.py` 표식 [재측정]), GB0 로드 게이트 일반형(6a), tol_V·tol_I를 쓰는 봉인 구현(6b design 1161행), CGS·CGB 열의 **소비**(DF-28, 7a), U-36 수동소자 단위 면적 **값**(7b 전), SID_1F 잡음 metric 소비(7b 이후).
* **인프라 백로그**(엔진을 막을 때만 처리, 메모리 규칙): B29·B30·B31·B32·B33, `sky130_lut_sweep._parse_output`의 `Error:` 미검사 [prep: `prep_u27_u30.md` §2.2].
* **analog-grammar 관련(v0.2)**: 다음 항목은 범위 **안**에 넣는다.
  * B34(조용한 폴백)는 #45.
  * B35(`netclass.RAILS_*`)는 B26-2(#17)의 SD 호출부 어댑터로 흡수한다.
  * B36(게이트 공백)은 #46. 형태는 UD-15에 따른다.
  * B37(`ports` 미전달)은 #47.
  * analog-grammar 파일 자체를 레일 선언 기반으로 고치는 확장안은 **범위 밖**이다. UD-15에서 (a)를 고르고 뒤에 따로 판단한다.
  * B29~B33·`_TEMPLATE`의 `supply_nets` 필드 부재(`review_b26_1.md` M2)는 인프라·문서 백로그로 둔다.

### 1.5 계획과 HEAD가 어긋나는 곳(이 design이 전제하는 정정)

1. N6.1 앞머리 순서의 DF-35·DF-36은 완료 -- 실제 순서는 **TS4 → CC-4 앞부분 → CC-7·CC-8 → 나머지** [prep].
2. DF 위치 열 줄 번호가 낡았다(DF-26 "3882~3883·3147" → 3714·3715·2983 [재측정]). 이 design은 **함수 이름**으로 인용하고, Phase 3 뒤에는 D0b 이관표의 MOD 파일을 따른다.
3. U-27 "SID_1F 열 추가"는 열이 이미 있다 [재측정: npz 키에 `SID_1F_n`·`SID_1F_p`] → "새 VS 축으로 함께 재스윕"으로 읽는다. 계획 158행 "`noise_1f_density()`가 호출 즉시 거부" 문장도 낡았다 [prep: `prep_u27_u30.md` §2.4].
4. DF-19 비고의 "29개(`sizing_recipe` 15 · `stick_diagram` 10 · `run_harness` 4)"는 옛 스캔이다. 넷 판정 운영 함수는 AST 전수 SR 14 · SD 14(상수 3 별도)이고 `run_harness` 4는 전압 선언(MG1)이다 [prep: `prep_b26_supply_nets.md` §1.4].
5. 레일 넷과 레일 전압을 한 변경 단위(MG1)로 묶은 문구 → 넷(B26) / 전압(MG1) 분리. 계획 정정안 `draft_b26_plan_patch.md`(판정 표 무변경, `plan_tables_hash` 전후 동일 확인 조건).

---

## 2. HEAD 사실 (재측정한 것만)

명령: `C:/Python314/python.exe -B C:/g36/remeasure.py`(AST·정규식·`np.load`·`git grep`, 읽기 전용) → `C:/g36/remeasure.json`. 아래 표의 모든 값은 그 출력이다. 원래 출처 prep과 다르면 '비고'에 적었다.

| # | 사실 | 값(cd64170) | 원 출처 | 비고 |
|---|---|---|---|---|
| F1 | 기준 커밋·design 문서 | HEAD `cd64170`. design 4개(`00`·`05`·`10`·`20`), `40` 없음 | `prep_phase4_scope.md` 머리 | 일치 |
| F2 | 레일 이름 집합 정의 위치 | SR `_DEFAULT_RAIL_HI/LO` 3714·3715, SD `_RAIL_NETS` 2983, SR `_rail_nets = frozenset(...)` 8003, MNA `fixed = {"gnd": 0.0}` SR 4086·4991 | `prep_b26_supply_nets.md` §1.1·§1.2 | 일치 |
| F3 | 엔진이 `supply_nets`·`supplies_v`를 읽는 곳 | 문자열 상수 `"supply_nets"`: SR 4361 하나(metric 선언 키, `_metric_supply_current` 정의 4339 안), SD 0. `"supplies_v"`: SR 0 | 같은 문서 머리 "중요 실측" | 일치 -- **엔진은 topology 최상위 `supply_nets`를 읽지 않는다** |
| F4 | 스칼라 `spec["vdd"]`·`.get("vdd")` 읽기(MG1 대상) | SR **20줄**: 1729, 3254, 4626, 4653, 7068, 7222, 7228, 7290, 7295, 7296, 7445, 7449, 7450, 8233, 8242, 8277, 8652, 10157, 10159, 10160 | `prep_phase4_scope.md` §3.4("21줄") | **정정**: prep의 21줄 중 8656은 오류 메시지 문자열 안의 `spec['vdd']`이고 읽기가 아니다 |
| F5 | 광범위 except 핸들러 수(DF-37) | SR `ValueError` 포함 26 · `Exception` 6 · `InfeasibleSizingError` 18, SD 4·0·0, `audit_current_forced` 0·1·0, `topology_to_markdown` 0·1·0, `topology_library`·`design_report` 0, 하네스 1·2·0 | `prep_phase4_scope.md` §3.6 | 일치(계획 2026-09-18 값 SR 52·7, SD 23·1과 다름 -- CC-4b spec card가 그 시점 AST로 다시 센다) |
| F6 | 하네스 PDK·전압 사본 | `min_finger_w` 121 **`0.1e-6`**, 186·243·301 `1e-6` / `W_bounds` 117·172·241·297 / `L_min` 115·170·239·295 / `"vdd": 1.8` 105·142·234·288 / `min_vds_by_role` 118·173·242·300 | `prep_u27_u30.md` §3.1 | 일치 |
| F7 | 엔진 쪽 두 번째 정본(폴백 기본값) | `W_bounds` `(1e-6, 200e-6)` SR 11곳: 1626, 1988, 2697, 2748, 3623, 5763, 6055, 6731, 7266, 7462, 8716. `spec.get("min_finger_w", …)` SR 9273. SD 기본 인자 5954·6043(`1.0`/`40.0`, µm), 6204(`0.4`/`45.0`) | `prep_u27_u30.md` §3.2 | 일치 |
| F8 | DF 대상 함수 정의 줄 | `solve_id_for_target_gm` 1433, `_invert_gm_id_for_current` 1471, `lut_vdsat_headroom` 1591, `stack_kvl_vgs_limit` 1668, `resolve_feed_vds` 1971, `true_current_mirror_groups` 2191, `estimate_area_budget` 2765, `diode_vds_cached` 3206, `diode_vds_window` 3402, `solve_stacked_diode_pair` 3491, `propagate_node_voltages` 3727, `derive_vsb_from_nodes` 3789, `reconcile_vsb_from_nodes` 3808, `node_pole_estimate` 3917, `build_ac_network` 4067, `_metric_kcl_residual` 4267, `_metric_supply_current` 4339, `_mirror_ratio_error_pairs` 4388, `_metric_input_referred_offset` 4561, `_resolve_nulling_resistor_ohm` 4908, `_full_circuit_response` 4970, `validate_no_legacy_vs_key` 5217, `InfeasibleSizingError` 6429, `_hr_resolve_vertical_group` 7089, `spec_fingerprint` 7596, `resolve_constraint_references` 7821, `_build_theta_evaluator` 7930, `optimize_full_circuit_budget` 9075, `repair_infeasible_baseline` 10410, `revalidate_finger_override` 11299, `GmIdLUT` 52, `SemiEmpiricalGmIdLUT` 259, `_query`(메서드) 378, SD `load_topology` 8550 | `prep_phase4_scope.md` §3.5 | 일치 |
| F9 | 캐시·폴백 결함 지점 | `_QUERY_CACHE_MAX` 257, 상한 도달 분기 390(DF-07). `idu_up = 1.0` 3539(DF-11). `setdefault("vsb", …)` 3813·3857·7407·7579(DF-01 원인 코드) | 앞 둘은 prep §3.5 | `setdefault` 4줄은 이 초안에서 새로 센 것 -- 4줄 중 DF-01 원인은 몇 곳인지 [미확인] |
| F10 | 표본 LUT | 키 = L·VGS·VDS·VS·`corner`·`temp_c`·{ID,GM,GDS,CGG,CGD,SID_1F}_{n,p}. **CGS·CGB 없음, SID_1F 있음.** L 12점, **VS = [0, 0.2, 0.4, 0.6, 0.8]**. sha256 `753d802a860320dd54b53b95920c6f9addcea821c55089358bf4b1f1ebaf177f`. `sky130_lut_sweep.py:108` `VS_GRID` | `prep_u27_u30.md` §2.1 | 일치 |
| F11 | 착수 조건 승인 기록 | `.ai/approvals/` 41개 중 U-04·U-05·U-09·U-26·U-27·U-30·`40-defect`·B26에 해당하는 것 **0** | `prep_phase4_scope.md` §3.8 | 일치 |
| F12 | 레지스트리 보류 표기 | 문자열 `보류(Phase 3)` 9회, `보류(Phase 4)` 14회, `보류(Phase 6a)` 2회 | `prep_deferred_rows.md` 머리 | 일치. 등장 횟수 = 행 수라는 것은 [미확인](처리 열 밖 등장 여부 안 봄) |
| F13 | IC11 뼈대 | `tests/contracts/test_ic11.py`: `rail2` phase 4, `rail3`·`reject` phase 6a | `prep_phase4_scope.md` §1.5 | 일치 |
| F14 | '자기참조' 표기 test | 판정 test의 자기참조는 `test_selftest_sizing_recipe.py:1786`(`estimate_area_budget`) 하나. 나머지 3건은 다른 뜻(diode 자기 연결·기대 문장 규칙) | `prep_deferred_rows.md` §1-2 | 일치 -- **TS4의 명시 대상은 사실상 1건** |

**재측정하지 않고 인용하는 핵심 사실**(모두 [prep], card 작성 전 실측 대상):
* U-27 도구·ngspice-46·`C:\pdk\sky130_fd_pr`(`f62031a`)가 현 LUT를 **비트 동일로 재현**(pfet L 0.425 VS 0.8 2401점, 329 s) -- `prep_u27_u30.md` §2.2.
* 구조 규칙 극성(PMOS source만 = hi, NMOS source만 = lo)이 library 9/9에서 CONFLICT 0, hi·lo 각 1 -- `b26_decision_table.md` §1.2.
* 선언 레일 전부 교류접지 시 바뀌는 metric은 current_reuse `cmrr_estimate_db` 73.14488 → 73.38009(θ*) 하나 -- 같은 문서 §2.2(prep §2.4의 "중앙점"은 θ*로 정정됨).
* two_stage·nmcnr는 bounds 중앙점 θ에서 `InfeasibleSizingError`(레일 무관) -- `prep_b26_supply_nets.md` §2.4, `b26_decision_table.md` §2.2.
* B26-1 scratch: 병합 상당 사본에서 E-LIB 9/9·사이징 4회로 결과 동일, 기존 test 판정 불변(근사) -- `draft_b26_1.spec.md` '재현할 수치'.
* 보류 행 25개 조사(배선 3, 삭제·이관 7묶음, 사용자 결정 4, 6a 승인 2) -- `prep_deferred_rows.md` §0·§3.
* (v0.2) **B34 재현**: analog-grammar가 없으면 다음 일이 생긴다(`prep_b34_b35_grammar.md` §1.3).
  * current_reuse θ\* 평가가 성공에서 `ValueError`(vertical_stack_id 순환)로 바뀐다.
  * `load_topology` meta가 9/9 회로에서 달라진다.
  * review 목록이 9회로 모두 0건이 된다. 그래서 `require_device_roles_reviewed`가 아무것도 막지 않는다.
  * `install.py` `SKILLS`에 analog-grammar가 없어서 설치본은 **항상** 이 폴백으로 돈다.
  * 폴백 사이트는 직접 12곳, 전파 9곳이다(같은 문서 §1.2).
* (v0.2) **B35**: SD에서 AG를 쓰는 함수는 12개(운영 8)다. 9회로 전부 `RAILS ∩ 트랜지스터 넷 = supply_nets ∩ 트랜지스터 넷`이다. SD 운영 경로는 극성을 소비하지 않는다(극성 변이에서 `load_topology` 9/9·SPECS 4회로가 같았다) -- 같은 문서 §2·§3.3.
* (v0.2) **B26-1 검토**(`review_b26_1.md`): 사실 문장은 대부분 재현됐다.
  * **blocking B1**: V3 대상 def가 약 32개이고 변이가 약 2,465개다. `_metric_kcl_residual`의 인벤토리는 0이다.
  * **blocking B2**: 계약 7의 역방향이 `load_topology` meta 수준에서는 병합본에서도 성립하지 않는다. netclass 이름 판정 때문이다.
  * **S1**: `rail_declaration` 호출 수는 1 → 2 → 2다. 계약 문장 "1회"가 거짓이다.
  * **S3**: 앞당김은 알림이 아니라 승인 기록으로 받아야 한다.

---

## 3. card 묶음, 순서, 의존

### 3.1 Phase 3 모듈 파일과의 관계

계획상 Phase 4 착수 = Phase 3 DoD PASS 뒤(N6.1 공통). `00-common`이 새 코드의 **목적 모듈**을 정해 두었으므로 아래 card는 Phase 3 모듈 파일이 있어야 계약대로 둘 수 있다.

| card | 필요한 모듈 | 근거 |
|---|---|---|
| CC-4a·CC-4b | MOD2(`SchemaRejectedError`·`FailureRecord`), MOD4(N3.14 예외·`FAILURE_CLASSES`·`exit_code_for`) | `00-common` §7.1 |
| CC-5, MG1 | MOD2(`LEGACY_NAMES`·`load_json_checked`) | `00-common` §6.1 |
| CC-7a·CC-7b | MOD6(탐색부 추출·`ContextVar`), MOD10(`instrument`) | `00-common` §10.1 |
| CC-8 | MOD10(`activations_out`) | `00-common` §11.2 |
| DF-02(tol_V) | MOD1(N3.6 "MOD1 함수로 승격") | 계획 N3.6 [prep] |
| W-1 `theta-order-gate` | MOD2(계획 N3.10 MOD2 '선언 순서 게이트') | `prep_deferred_rows.md` §3.1 |
| 그 밖 DF card | 고치는 함수가 Phase 3 뒤 있는 MOD 파일 | D0b 이관표 |

MOD10 진입점 시그니처는 Phase 3 초안 D-5(`(spec, *, topology_path, search, output_dir)`)를 받고 CC-7·CC-8이 `instrument`·`activations_out`을 더한다(Phase 3 초안 §2.3). Phase 3 초안이 승인 전이므로 이 연결은 **[미확인]**(Phase 3 design 승인 뒤 확정).

### 3.2 Phase 3보다 먼저 할 수 있는 것

원칙 근거: 계획 N3.10 "등급 D 함수는 옮기기 전에 처리한다", 곧 지울 코드를 옮기지 않기, 편집 파일 2개(Phase 3 뒤 6개 모듈) [prep: `prep_b26_supply_nets.md` §3.5].

| card | 앞당길 수 있는 조건 | 막히는 것 |
|---|---|---|
| **B26-1** `b26-rail-accessor-set` | (1) 계획 정정안 `draft_b26_plan_patch.md`를 커밋한다(판정 표 무변경). 검토 S5에 따라 N3.16 문구를 "kcl_residual `rail_nets`는 B26-1에서 거부, 그 밖의 옛 키는 MG1"로 맞춘다. (2) P9 병합 뒤 base (3) **UD-14 decision 승인 기록**(DEC-60 넷 전환기 종료 + DF-19·26 넷 몫 분리 + Phase 3 전 착수 -- 검토 S3) (4) **UD-13 V3 처리 결정**(검토 B1) (5) spec card 보강. 계약 7 역방향의 관찰 대상을 B26-1 사이트만으로 정해지는 값으로 한정한다(B2). 계약 3을 "`rail_declaration` 호출 수 = `load_topology` 호출 수"로 고친다(S1). red 진입점을 항목별로 적는다(S4). `_metric_kcl_residual`을 직접 이름으로 부르는 test를 넣는다(B1-3) | 초안 있음, 검토 blocking 2건(B1·B2) |
| **B34** `b34-grammar-explicit-dependency`(#45) | 독립이다(B26-1과 파일이 겹치므로 순차). **Phase 3 M2(어댑터를 MOD2로 이동) 전**에 하는 것이 싸다. 이동은 해시 동일성 증명이라 최종형을 먼저 만들어 두면 된다 | 없음. 사용자 작업 1건 동반: `install.py` `SKILLS`에 analog-grammar 추가(EL1상 사용자 경로) |
| **B26-4** `b26-rail-literal-lint` | '운영부 레일 이름 리터럴 0'이 병합본에서 성립해야 red-green이 된다 → **B26-2·B26-3이 먼저 병합되고**, 비운영 사이트(`node_pole_estimate`·`find_differential_and_mirror_forks`·`propose_theta_kcl_gap_fill`)가 삭제·이관·면제로 정리돼야 한다 | D1·D2(§7 UD-1·UD-2), UD-7(U-A)·UD-9(U-C), D-6 이관 |
| **d4-delete-unwired**(D-1~D-4) | U-02 승인이 '보류(Phase 4 배선)'로 둔 행을 **삭제**로 바꾸는 것 -- 이 design 승인(UD-0)으로 덮는다. 계획 소비자(DF-09·TS4 행) 정정을 같은 card에 | `test_ic5` `_DOMAIN_TABLE` 행 삭제(D-4) = V5, DEC-40 승인(§7.1 뒤 목록) |
| **pole-oracle-to-tests**(D-6) | 위와 같음. 계획 DEC-25·DF-06 문장 정정 동반 | B26-4 lint·DF-06 card보다 먼저여야 한다 |
| **toy-lut-to-tests**(D-7) | test-only 이관(`d-move-tests` 선례) | Phase 3 F1과 묶어도 된다 |

B26-2·B26-3도 D1·D2가 일찍 결정되면 Phase 3 전에 할 수 있다(편집 파일은 SR·SD 둘).

**B35 처리는 B26-2 안의 SD 호출부 어댑터로 한다**(기본안, `review_b26_1.md` S2).
* analog-grammar 파일은 고치지 않는다.
* SD의 `_import_analog_grammar` 호출부에서 넷 이름을 바꿔 넘기고 결과를 역치환한다.
  * 선언 레일은 극성별 정준 토큰(`VDD`/`GND`)으로 바꾼다.
  * 선언 밖인데 레일 이름을 가진 넷(`vss`·`agnd` 등, 대소문자 무관)은 중립 토큰으로 바꾼다.
* code-author 경로 안의 일이라 N3.12.2 경로표 개정(plan_tables 승인)이 필요 없다.
* 극성이 필요하므로 D1(UD-1)이 선행이다.

**기본안과 충돌하는 준비 문서의 반론을 같이 적는다.** `prep_b34_b35_grammar.md` §3.2는 이 '호출부 번역'을 다섯 가지 이유로 기각하고 analog-grammar 확장을 권고했다.
* (i) 극성마다 이름 집합 원소가 5개라 담을 수 있는 레일 수에 상한이 있다.
* (ii) 극성을 뭉개면 `find_idiom_matches` 원본 출력이 바뀐다.
* (iii) 넷 이름을 키로 쓰는 출력(`cls`·`imp`·`stack_edges`·`Match.ports`)을 전부 역변환해야 한다.
* (iv) 결과적으로 B26-4 lint의 취지를 우회한다.
* (v) analog-grammar 자체는 여전히 이름 기반이다.

B26-2 spec card는 이 다섯 가지를 계약으로 막는다.
* (i) 한 극성의 선언 레일이 정준 토큰 수를 넘으면 명시적으로 거부한다.
* (ii)(iii) 역치환 완전성: 이름 바꾸기 불변을 `load_topology` meta **전체**에 건다. 이것이 B26-1 검토 B2가 남긴 빈칸을 닫는다.
* (iv) 어댑터의 정준 토큰은 lint 면제 규칙으로 명시하고, 이름으로 판정하는 코드는 0으로 둔다.
* (v)는 UD-15에서 (a)를 고른 뒤 analog-grammar 확장 card로 넘긴다.

(i)의 상한은 library 9회로에서 걸리지 않는다. 구조 규칙으로 hi·lo가 각각 정확히 하나이고, mid는 `agnd`(커패시터 단자만) 뿐이다 [prep: `b26_decision_table.md` §1.2]. 걸리는 것은 H3(레벨 시프터)처럼 같은 극성 레일이 여럿인 미래 회로다.

Phase 3 초안 v2 §1은 "레지스트리 §2 '정본 후보'의 정본 확정(B26, Phase 4)"을 범위 밖으로 둔다. B26-1을 당기면 Phase 3 D0b의 `_RAIL_NETS` 목적지가 바뀌므로 **Phase 3 design 승인(UD-0 of Phase 3) 전에** 당김 여부가 정해져야 한다 [prep: `prep_phase4_scope.md` §4.1].

### 3.3 순서

```
[Phase 3 전 후보]  plan-patch + UD-14 + UD-13 ─> B26-1 ;  B34(#45, M2 전, B26-1과 순차) ;
                   d4-delete-unwired, pole-oracle-to-tests, toy-lut-to-tests
[Phase 3]          (30-module-split) ── DoD PASS
[Phase 4 선두, 순서 고정]
   TS4 ─> CC-4a ─> CC-7a(추출, equivalence) ─> CC-7b(계측·perf 도구) ─> CC-8(activations_out·noop 도구)
   (TS4 범위는 D-1 결정에 기댄다: D-1 삭제면 TS4 대상 = V4 lint 산출 목록)
[선두 뒤, 묶음끼리는 병렬 준비·순차 병합]
 실패 규약   CC-4b(DF-37) ; DF-03 ; DF-06 ; DF-14+V8 ; DF-18(θ* 기록) ; DF-11 ; DF-12
 레일        B34 ─> B26-2(D1, +B35 어댑터) ─> B37(ports 전달) ; B26-2 ─> B26-3(D2) ─> B26-4(lint) ;  CC-5 ─> MG1(U-26a) ─> DF-24+IC11 rail2
 게이트      B36(UD-15 결과에 따른 형태, 게이트 변경 card) -- 레일 묶음과 독립, B26-4 lint 범위에 AG를 넣을지는 B36 뒤
 노드전압    DF-02(+tol_V, B21c 재현) ─> DF-01
 LUT·PDK     DF-27(옛 LUT red) ─> U-27a(스크립트) ─> U-27b(재생성·대조) ─> U-30a(선언·무동작) ─> U-30b(W 하한·finger, DEC-40)
             B24a(VGS 기준 조회 API, 면제 해제) ; DF-10+B24b(U-05)
 캐시        DF-07 ; DF-13 ; DF-15(재현 먼저)
 개별        DF-04 ; DF-05 ; DF-08+22(U-04) ; DF-20 ; DF-23(P10 목록의 Phase 4 행)
 배선        W-1 ; W-2+D-5 ; W-3 ; (UD-7 결과에 따라) U-A card
 회로        I-C11 two_stage ; I-C11 nmcnr   (U-09)
[마감]       Phase 4 DoD(§6) -- 마지막 동작 변경 card의 perf.json, 전후 비교표
```

순서 근거:
* 선두 5건은 N6.1·`00-common` §11.1 고정. CC-7 병합 **다음** 동작 변경 card부터 perf 측정, CC-8 병합 다음부터 무동작 판정이 card마다 적용된다(`00-common` §10·§11.1).
* DF-27 → U-27: U-27 선행 (1) "DF-27 red가 옛 LUT에서 VS 축 밖 거부"(계획 U-27).
* U-27 → U-30: U-30b의 사이징 비교(C3)가 새 LUT 위에서 한 번만 일어나 기준선 승인이 한 번으로 끝난다 [prep: `prep_u27_u30.md` §4.2].
* CC-5 → MG1: 옛 키 게이트의 공통 형식(`reject_legacy_names`)이 있어야 MG1이 자기 행을 더한다(DEC-69 "옛 키 거부 로드 게이트를 같은 변경 단위에"). CC-5는 CC-4a 뒤(`SchemaRejectedError` 필요).
* MG1 → DF-24: DEC-61 bulk 기본값이 `supplies_v` 전압 순서로 정의된다.
* D-1 결정 → TS4, D-6 → DF-06·B26-4: 지울 코드를 고치지 않는다 [prep: `prep_phase4_scope.md` §3.8].
* W-2는 `d4-delete-unwired`(test_ic5 표 수정 1회) 병합 뒤 -- V5 승인을 한 번으로 [prep: `prep_deferred_rows.md` §4].

### 3.4 파일 충돌 집합(준비는 병렬, 병합은 순차)

[prep: `prep_phase4_scope.md` §4.2, Phase 3 뒤 모듈 이름은 D0b 확정 전이라 [미확인]]
* 평가 커널 빌더(`_build_theta_evaluator`/`_evaluate`, MOD6): DF-03·DF-01·DF-02·DF-14·CC-7a·B26-2(8003행 `_rail_nets`).
* MNA(MOD5): B26-3.
* 로드 경로(MOD2): CC-5·MG1·B26-1·W-1.
* LUT(MOD1): DF-07·DF-13·DF-27·B24a·DF-10·DF-02(tol_V)·U-30a(공정 기록 로더).
* 하네스(`workspaces/run_harness.py`): CC-4a·CC-7b·CC-8·DF-18·MG1·U-30a·DF-20.

### 3.5 한 card로 묶는 것(원칙)

| 묶음 | 근거 |
|---|---|
| DF-08 + DF-22 | 같은 함수, 계획 비고 "DF-08과 함께" |
| DF-14 + V8 계측 지점 | 계획 비고 "V8 계측 대상" |
| MG1 이름 변경 + 옛 키 거부 행 | DEC-69 "같은 변경 단위" |
| DF-02 + tol_V 함수 | N9.1 "tol_V 함수 선도입" + 만들면 배선(소비자가 DF-02) |
| DF-24 + IC11 rail2 활성 | IC11의 원점 이동 불변 test가 DF-24를 검출하는 red(N4.1 829행) |
| DF-10 + B24 (b) | 같은 뿌리 후보(PMOS gm/ID 비단조, `_solve_vgs` 근 선택) [prep, 뿌리 동일은 [미확인]] |
| W-2 + D-5 | vsid 감사의 유효 1건(`cmfb_tail`)을 W-2 배선이 대체 [prep: `prep_deferred_rows.md` §3.1] |
| U-30 + DF-34 Phase 4 몫 + 엔진 폴백 15곳 | 개념 하나에 저장 위치 하나(DEC-68). 하네스만 고치면 엔진 기본값이 두 번째 정본으로 남는다 [재측정 F7] |

---

## 4. 원칙을 계약으로 (모든 card의 spec card '관찰 가능한 계약'에 전 범위로 넣는다)

### 4.1 topology 무관 (DEC-62, 사용자 원칙 2026-09-30)

* 새 함수와 고치는 사이트에 **소자·넷·회로 이름 리터럴과 topology 경로가 없다**. 판정은 선언(`supply_nets`, `supplies_v`, `ports`, `bulk`, metric 선언)과 구조 술어(소자 kind·단자 연결)에서만 읽는다.
* 판정기: card마다 (a) **합성 topology**(library에 없는 회로·넷·소자 이름 -- 선례 `tests/contracts/test_d_delete_telescopic.py` `_SYN_RAILS = ["rail_hi","rail_lo"]`)에서 기대값이 나오고 (b) **역방향**: 선언에 없는 넷이 `vdd`·`gnd` 같은 이름이어도 레일로 취급하지 않는다(`draft_b26_1.spec.md` 계약 7).
* 변환 불변: 레일 이름 바꾸기·원점 이동(IC11 `test_rail_origin_shift_invariance`) -- setup 결과 또는 metric이 되돌리면 같다.
* 전 범위 강제: B26-4 lint(운영부 레일 이름 리터럴 0), DF-23 Phase 4 행(P10 목록)의 일반 규칙 교체. 정본으로 고르는 엔진 식이 이름 기반이면 정본이 아니다(`_DEFAULT_RAIL_*` 선례).
* 무동작 증명: 기능이 필요 없는 library 회로에서 발동 계수 0·산출물 동일(`00-common` §11, CC-8 뒤) -- 일반성을 **측정**으로 보인다.

### 4.2 조용한 폴백 금지

* 선언이 없으면 거부한다: CC-4a 전에는 `ValueError`(메시지에 선언 이름과 DEC 번호), CC-4a 뒤 로드 거부는 `SchemaRejectedError`(N3.14 SCHEMA_REJECTED, exit 7), 탐색 중 실패는 N3.14 클래스.
* **기본값 없는 인자**: 레일·PDK·전압 인자를 이름 집합·리터럴 기본값이나 `None`→기본값으로 두지 않는다(`draft_b26_1.spec.md` 원칙 2).
* 광범위 except는 N3.14 클래스와 `SchemaRejectedError`를 다시 raise한다(DF-37, `00-common` §7.3). 탐색 루프는 `CANDIDATE_FAILURE_CLASSES`만 이름으로 잡는다.
* 남기는 폴백은 전부 `fallback_events{site, kind, device, detail}`에 기록한다(V8). 정본 실행에서 0이어야 한다.
* 게이트는 **'실제로 거부한다'를 먼저** 보인다: 거부 test는 조용한 통과(기본값 대입) 합성 구현을 넣으면 FAIL해야 한다(`test_d_delete_telescopic` `test_rejection_check_fails_on_silent_or_unlisted_refusal` 형태).
* 클램프 금지: LUT 축 밖 입력은 `lut_axis_out_of_range{소자, 축, 값, 범위}`(SEAL_VIOLATION)로(LR3, DF-27).

### 4.3 만들면 배선

새 함수는 **만든 card에서** 운영 호출부가 부르고, 원래 문제가 있던 경로를 대체한다. 대체할 수 없으면 만들지 않고 사용자 승인을 구한다.

| 새 것 | 만드는 card | 같은 card의 운영 소비자(대체하는 것) |
|---|---|---|
| `rail_declaration`·`RailDeclaration` | B26-1 | `load_topology` → 집합 판정 사이트 전부(이름 집합) |
| 극성 필드(hi/lo/mid) | B26-2 | `trace_*`·`propagate_node_voltages`·`_metric_supply_current` 등(이름 리터럴 `"vdd"`/`"gnd"`) |
| analog-grammar 호출부 어댑터(선언 레일 → 정준 토큰, 역치환) | B26-2(B35 흡수) | SD 운영 8함수의 AG 호출(`netclass.RAILS*` 이름 판정) |
| analog-grammar 명시적 의존 오류 | B34(#45) | `_import_analog_grammar`의 `None` 폴백 12곳과 전파 9곳, 소비처 0인 `unavailable_reason` 2곳(만들고 배선 안 한 것 -- 삭제) |
| `ports` 선언 전달 | B37(#47) | `load_topology` → `propose_device_roles_gap_fill`의 `inputs`/`outputs`(지금은 넘기지 않아 `HINT_*` 이름 정규식이 추정) |
| N3.14 예외·`FAILURE_CLASSES`·`exit_code_for`·`FailureRecord` | CC-4a | 하네스 `run()` 종료 코드(모든 예외를 삼키고 exit 0) |
| `LEGACY_NAMES`·`load_json_checked`·`reject_legacy_names` | CC-5 | 엔진의 파일 읽기 `json.load` 전부, `validate_no_legacy_vs_key`(삭제) |
| `vdd` 유도 함수(가장 높은 레일 전압 = `supplies_v`에서) | MG1 | 스칼라 `spec["vdd"]` 읽기 20줄 [재측정 F4] |
| θ 탐색 함수(추출), `instrument`, `measure_search_perf.py` | CC-7a·7b | `optimize_full_circuit_budget` 인라인 탐색, N6.3 보고 |
| `activations_out`, `noop_proof.py` | CC-8 | N6.3 무동작 증명 |
| `tol_V` 함수(MOD1) | DF-02 | `propagate_node_voltages` conflicts 판정(지금 미소비) |
| 공정 기록 로더(PDK 상수) | U-30a | 하네스 4벌·엔진 폴백 15곳, 죽은 키 `L_min`은 `layout_grid_L_candidates(L_min=)`에 배선 |
| VGS 기준 gm·gds 공개 조회 | B24a | `gain_ranking`의 `lut._query` 직접 조회 → 면제 `20260929-p4-scan-exempt` 같은 card에서 해제 |
| `fallback_events` 기록 | DF-14+V8 | 운영 폴백 지점 전수(스키마·지점 목록은 그 card) |
| 레일 리터럴 lint | B26-4 | DF-19 위치 열(lint 산출로 대체), DoD E10 |

* **`tol_I`는 Phase 4에서 만들지 않는다**(원칙 기본안): Phase 4 안에 엔진 소비자가 없다(KCL 봉인은 6b design 몫). B21 (a)를 `tol_I` 식으로 해소한다는 prep 매핑(`prep_phase4_scope.md` §2)은 소비자가 test(P3c)뿐이라 이 원칙과 충돌한다 → P3c 재착수 조건 (a)는 6b로 넘기거나, test 쪽이 N3.6 식을 oracle로 직접 계산하게 한다. **[미확인]**: P3c test가 엔진 함수 없이 `tol_I`를 계산할 수 있는지(계획 N3.6 입력이 LUT leave-one-out 오차라 test 쪽 재구현이 V4 규칙 (2)에 걸릴 수 있다).

### 4.4 캐싱 (NFR-2, N3.3)

* **새 캐시를 만들지 않는다.** 이미 있는 엔트리에 싣는다(B26-1: `_load_full_topology_cached`의 `meta["rails"]`, 평가 루프 안 접근자 호출 0 -- 계수 래퍼로 관찰).
* 고치는 캐시는 **상한 + LRU**(DF-07, "캐싱 중단 금지"), 키는 **계산이 실제로 읽는 가변 상태의 내용 지문**(DF-13: `id(lut)` → LUT 내용 지문, SC-d). 모듈 수준 캐시는 읽고 쓰는 함수와 같은 모듈(Phase 3 CACHE-ID).
* 새 선언 읽기(공정 기록, `supplies_v`)는 **실행당 한 번** 읽고 캐시한다. 유도값(`W_bounds` 하한 = `min_finger_w`, `vdd` = max(`supplies_v`))은 함수 하나로 계산하고 결과를 보관한다(메모리: 근거 하나 남기고 계산+캐시).
* iteration 안의 계산은 쓰는 순간 캐시한다. 측정은 추측이 아니라 계측으로: CC-7 뒤 card마다 `perf.json`(eval_count·eval_median_s), 캐시 card는 적중·미적중 계수와 같은 입력 해시 재계산 수(NFR-2 합격 기준의 Phase 4 몫 -- 전체 계측은 6b).
* 이미 있는 결함을 키우지 않는다: 경로 문자열 캐시 키(S0 지문 = 6a)는 재사용만 하고 넓히지 않는다.

### 4.5 작성자 ≠ 검증자

모든 card의 red·기대값·픽스처는 test-author(interface card만), 구현은 code-author, 전후 비교표·perf·E-LIB·E-INST 수치는 auditor 판정 기록에서만 인용한다. 기존 test 기대값이 병합본과 다르면 test-author는 고치지 않고 dispute를 쓴다. 기준 약화·기준선 변경은 DEC-40 승인 없이 병합하지 않는다.

---

## 5. card 표

열: 판정 = 판정 유형(N3.12.3), oracle 종류 (a) 구성 (b) 독립 방법·문헌 (c) 동작 보존(base 결과) (d) 계획·원자료. `P3?` = Phase 3 모듈 파일 필요(Y) / Phase 3 전 가능(pre) / 무관(-). DoD = §6 ID.

### 5.1 Phase 3 전 후보

| # | id(초안) | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 1 | `b26-rail-accessor-set` | DF-19·26 넷 몫 1(접근자 + 집합 판정 사이트 11함수) | red-green | (a) 합성 레일 이름 topology. 역방향은 B26-1 사이트만으로 정해지는 값(`_matching_pairs_autofilled`·`_vertical_stack_id_autofilled`·`l_sharing_classes`·kcl_residual)에 한정한다(검토 B2). (b) 이름 바꾸기 setup 불변. (c) E-LIB 9/9·E-INST | 계획 정정, P9, UD-13, UD-14 | pre | E0·E10(부분) |
| 45 | `b34-grammar-explicit-dependency` | B34: `_import_analog_grammar`가 `ImportError`를 삼키지 않고 경로·skill 이름을 담아 다시 던진다. `is None` 폴백 12곳·전파 9곳·`unavailable_reason` 2곳을 삭제한다. 'gate 소자 없음 → `None`'(test_s120)은 범위 밖이고 docstring으로 뜻을 나눈다 | red-green | (a) `monkeypatch.setitem(sys.modules, "netclass", None)`로 부재를 흉내 내면 base는 'DID NOT RAISE'. 조용한 반환 합성 구현에서 test FAIL(자기 점검). (c) analog-grammar가 있을 때 E-LIB 9/9·E-INST 동일 | 없음(#1과 순차) | pre(Phase 3 M2 전) | E0·E1 |
| 2 | `d4-delete-unwired` | 보류 D-1(`estimate_area_budget` → DF-09 닫힘)·D-2·D-3·D-4 | equivalence | (c) E-LIB·E-INST, (a) NEW-TOPO | UD-0, DEC-40 V5 승인(test_ic5 표, §7.1 뒤 목록) | pre | E0 |
| 3 | `pole-oracle-to-tests` | D-6 `node_pole_estimate`·`signal_path_nodes` → test oracle | equivalence(test 이관 → 엔진 삭제) | (c) 승격 test 판정 불변 | UD-0 | pre | E0 |
| 4 | `toy-lut-to-tests` | D-7 `_invq_newton`·`build_toy_lut` → tests 픽스처 | test-only | (c) E-AST | UD-0 | pre | -- |

### 5.2 선두(순서 고정)

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 5 | `ts4-selfref-oracle` | TS4: 자기참조 기대값을 oracle 4종으로 | red-green(해당 결함 test가 base에서 FAIL) | (a)·(b) | #2(D-1 결정) -- D-1 삭제면 대상 = V4 lint(`test_lint.py`) 산출 목록 **[미확인: 그 산출이 0이면 TS4는 계획 정정으로 닫는다]** | Y | E0 |
| 6 | `cc4a-failure-classes` | CC-4 앞부분: §7.1 형식, 하네스 `run()` exit code(DF-18 exit 몫·DF-37 하네스 몫), §9.3 N3.14 대조 test | red-green | (a) 합성 raise → exit code, (d) 계획 N3.14 | #5 | Y | E0·E11 |
| 7 | `cc7a-search-extract` | θ 탐색부 함수 추출 | equivalence | (c) E-INST·E-LIB | #6 | Y | E8 |
| 8 | `cc7b-perf-instrument` | `instrument`·`ContextVar`·`measure_search_perf.py` | red-green | (a) worktree 밖 경로 → exit 8, 실패 입력 → `status=failed` | #7 | Y | E8 |
| 9 | `cc8-noop-activations` | `activations_out`·`noop_proof.py` | red-green | (a) 발동 1건 → exit 9 등(`00-common` §14 CC-8) | #6 | Y | E9 |

### 5.3 실패 규약(CC-4a 뒤)

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 10 | `cc4b-df37-broad-except` | DF-37 광범위 except 재raise(수는 그 시점 AST -- F5) | red-green | (a) N3.14 예외를 던지는 합성 입력이 삼켜지지 않음 | #6 | Y | E0 |
| 11 | `df03-gate-failure-class` | DF-03 vsb·L 동치류 게이트 `ValueError` → N3.14 | red-green | (a) 위반 픽스처 → 탐색 계속·실패 기록 | #6 | Y | E0 |
| 12 | `df06-field-source-except` | DF-06(D-6 뒤 사이트 3: `_mna_stamp_capacitance`, `synthesize_l_class_thetas`·`knee_L_for_kind` 호출부) | red-green | (a) 원천 없는 필드 → 구조화 실패 | #3, #6 | Y | E0 |
| 13 | `df14-v8-fallback-events` | DF-14 `except Exception` 5지점 + V8 스키마·계측 지점 전수 | red-green | (a) 호출 실패 합성 → 실패 클래스, 폴백 발동 → `fallback_events` 1건 | #6 | Y | E0·E1 |
| 14 | `df18-theta-star-record` | DF-18 나머지: θ* 기록 | red-green | (a) 실행 산출물에 θ* 기록 | #6 | Y | E0 |
| 15 | `df11-stacked-diode-lut-fail` | DF-11 `idu_up = 1.0` 대입 제거 | red-green | (a) LUT 실패 주입 → 실패 클래스 | #6 | Y | E0 |
| 16 | `df12-offset-missing-gm` | DF-12 gm 없는 소자 조용히 제외 | red-green | (a) 손계산 오프셋 | #6 | Y | E0 |

### 5.4 레일

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 17 | `b26-rail-polarity` | B26-2: 극성(구조 규칙 + `supply_roles` 자리), `trace_*`·방향 라벨·`propagate_node_voltages`/`derive_vsb_from_nodes` 기본 인자·`_metric_supply_current`·`_metric_rail_referenced_voltage`·`_metric_battery_centering_deviation`, B26-1에서 넘어온 SR 7282·8003·8091, **B35 SD 호출부 어댑터**(운영 8함수, §3.2의 반론 (i)~(iv)를 계약으로) | red-green | (a) vss 회로 `trace_*` 가지 수, 합성 H1·H2·H4 거부, 합성 레일 이름 + 선언 밖 내부 넷 `vdd`. (b) 레일 이름 바꾸기에서 `load_topology` meta **전체** 불변. (c) E-LIB 9/9·E-INST. 9회로 `RAILS∩넷 = supply_nets∩넷`이라 무동작 [prep] | #1, #45, UD-1 | 조건부 pre | E0·E10 |
| 18 | `b26-mna-rail-ground` | B26-3: MNA 고정 노드 = 선언 레일 전부 → `also_fix`·`excite`로 덮어쓰기 | red-green + E-INST 차이표 | (a) 합성 회로 CM 응답, (c) 차이표(auditor θ* 재측정) | #17, UD-2(DEC-40 1건 포함) | 조건부 pre | E0·E2 |
| 19 | `b26-rail-literal-lint` | B26-4: lint 도구 + 이름 상수 삭제 + 레지스트리 §2 정본 확정 + DF-19 위치 열 대체 | red-green(base lint FAIL, 병합본 0) | (a) 도구 합성 입력, (d) AST 전수 | #17, #18, #3, UD-7·UD-9 | 조건부 pre | E10 |
| 20 | `cc5-legacy-gate-loader` | CC-5: `LEGACY_NAMES`·`load_json_checked`·`reject_legacy_names`, `json.load` 전수 대체, `validate_no_legacy_vs_key` → `vs` 행 | red-green | (d) 계획 N3.16에서 test-author가 옮긴 기대 목록 | #6 | Y | E4 |
| 21 | `mg1-rail-voltage` | MG1: `supplies_v`(하네스 `SPECS`), `vdd` 유도 함수, 스칼라 `vdd` 폴백 삭제, metric 인자 `supply_nets`·`rail_nets` 정리, 옛 키 행(`supplies`, spec `vdd`, metric `supply_nets`) | red-green + DEC-69 equivalence(키 매핑 뒤 θ*·metric·instance.json 동일) | (a) 옛 키 픽스처 거부, (c) E-INST | #20, UD-3 | Y | E4·E2 |
| 46 | `b36-grammar-gate-scope` | B36 게이트 공백. **UD-15 (a)**이면: N3.12.2 경로표에 `skills/analog-grammar/**` 행을 추가하고, `role_paths`·`reachability`(동적 import 간선 포함)·`mutate_changed`·`source_lint`·`interface_card`·`weakening_diff`의 범위에 넣는다. **(b)**이면: analog-gmid-design으로 흡수(이동 card, DUP·CLI 처리 포함) | 게이트 변경(B28 형식, 부트스트랩 ①~③) 또는 equivalence | (a) analog-grammar 수정 합성 커밋이 trailer 없이 거부됨, redteam 사례. (c) 흡수 시 E-AST | UD-15, plan_tables·게이트 변경 승인 | - | -- |
| 47 | `b37-ports-to-grammar` | B37: `load_topology`가 topology `ports`(9/9 선언)를 `propose_device_roles_gap_fill`의 `inputs`/`outputs`로 넘긴다. 이름 정규식 `HINT_*` 추정을 선언으로 대체 | red-green(+ 결과가 바뀌면 E-LIB 차이표) | (a) 입력 넷을 힌트 정규식에 걸리지 않는 이름으로 둔 합성 topology. (c) E-LIB 9/9 **[미확인: 9회로에서 결과가 바뀌는지 재지 않음 -- 바뀌면 DEC-40]** | #17 | 조건부 pre | E0 |
| 22 | `df24-ic11-rail-origin` | DF-24 vsb 유도(DEC-61, 레일 0 V 가정 제거) + IC11 rail2 활성 | red-green | (b) 변환 불변: two_stage (1.8, 0) 대 (0.9, −0.9) VGS·VDS·VSB·gm_id·W·metric 동일, (a) 음전위 레일 픽스처 | #21 | Y | E3 |

### 5.5 노드전압

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 23 | `df02-conflicts-seal-tolv` | DF-02 conflicts → SEAL_VIOLATION + `tol_V` 함수(MOD1, N3.6 식) | red-green | (a) 다중 도달 불일치 합성, (d) B21 (c) 재현 입력(folded X 1.6 대 0.0 V, 파일럿 Vom1/Vop1 0.677 대 0.900 V [prep]) | #6 | Y | E0 |
| 24 | `df01-vsb-recompute` | DF-01 vsb를 노드전압으로 고친 뒤 W·gm·gds 재계산(구조 제거는 6b) | red-green | (a) 버전 혼재 검출 픽스처 | #22, #23 | Y | E0 |

### 5.6 LUT·PDK

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 25 | `df27-lut-axis-gate` | DF-27 축 커버리지 게이트(옛 LUT에서 VS 0.8 V 밖 거부) | red-green | (a) vsb 0.9 V 픽스처 → `lut_axis_out_of_range` | #6 | Y | E5 |
| 26 | `u27a-sweep-script` | U-27 도구 결함 G1~G6(VS 값 기반 체크포인트 이름, 재사용 조건 = 필요 열 전체, CGS·CGB 추출, npz 메타 `w_ref_m`·PDK 커밋·ngspice 버전·스크립트 해시, VS 상한을 `supplies_v` 최대 차에서 인자로, 출력 경로 인자) | red-green | (a) 소형 격자, 옛 조합 비트 동일 재측정, CGS+CGD+CGB ≈ CGG | #25 | - | E6 |
| 27 | `u27b-lut-regen` | 재생성(VS 0~1.8 V, 0.2 V 간격 10점, 240조합 ≈ 22시간 [prep]) + 옛 격자점 대조 + 새 해시 기록 | red-green(DF-27 red 입력이 새 LUT에서 축 안) + 대조 기록 | (c) 옛 5 VS 점 × 기존 5열 비트 동일 기대 | #26, 다르면 UD-11 | - | E6 |
| 28 | `u30a-pdk-record-noop` | U-30 선언: 공정 기록 한 곳(출처 규칙 번호) + MOD1 로더 + npz 해시 연결 + DF-34 Phase 4 몫(하네스 사본 삭제) + 엔진 폴백 15곳 삭제 + 단위 m 통일 + `L_min` 배선, 값은 **아직 기존 값**(무동작 단계 C4~C8) | red-green(선언 누락 거부) + equivalence(E-INST 동일) | (d) PDK 규칙표, (c) E-INST | #27 | Y | E7 |
| 29 | `u30b-wbounds-min-finger` | `min_finger_w` = difftap.2 0.42 µm, `W_bounds` 하한 = `min_finger_w` 유도(C1·C2·C3) | red-green + 전후 비교표 | (d) difftap.2 출처, (c) 비교표(auditor) | #28, UD-12 | Y | E7·E2 |
| 30 | `b24a-lut-vgs-query-api` | B24 (a) VGS 기준 gm·gds 공개 조회 + `gain_ranking` 교체 + 면제 해제 | red-green | (a) 격자점 조회값 = 표 값 | #6 | Y | E0 |
| 31 | `df10-nonmonotone-inversion` | DF-10 이분 역산 단조성 + B24 (b) PMOS W 차이 | red-green | (a) 비단조 합성 곡선, 단조 구간별 근 전부 | UD-5 | Y | E0 |

### 5.7 캐시

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 32 | `df07-lru-caches` | DF-07 `_query` 캐시·`_FEASIBLE_L_WINDOW_CACHE` 상한 도달 시 LRU | red-green | (a) 상한 초과 뒤 최근 키 적중 | #6 | Y | E0 |
| 33 | `df13-lut-content-key` | DF-13 `id(lut)` 키 → LUT 내용 지문 + 상한 | red-green | (a) 같은 내용 다른 객체 적중·다른 내용 미적중 | #27 | Y | E0 |
| 34 | `df15-rz-cache-key` | DF-15 Rz 캐시 키·`_dc_replace` 공유(재현 test 먼저) | red-green(재현 안 되면 계획 정정 요청) | (a) | #6 | Y | E0 |

### 5.8 개별

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 35 | `df04-device-name-exact` | DF-04 부분문자열 매칭("M1" ⊂ "M11a") | red-green | (a) | #6 | Y | E0 |
| 36 | `df05-mirror-pairs-all` | DF-05 그룹 첫 두 소자만 비교 | red-green | (a) 3소자 미러 | #6 | Y | E0 |
| 37 | `df08-22-spec-origin` | DF-08·DF-22 지문 불일치 시 유도 임계값 사용·`_RESOLVE_STALE_NOTES` 미소비 + U-04 `origin` | red-green | (a) 픽스처 spec이 유도 임계값을 읽지 않음, 정본 spec 불일치 → 거부 | UD-4 | Y | E0 |
| 38 | `df20-fallback-constants` | DF-20 근거 없는 폴백 상수(vds 0.6/0.2, margin 0.05, 격자 리터럴, 하네스 `min_vds_by_role` 4벌 [재측정 F6]) | red-green | (d) 유도 근거(DEC-27·DF-25 연결은 6b) | #13 | Y | E0·E1 |
| 39 | `df23-general-rules` | DF-23 Phase 4 행(P10 목록에서 담당 = 4인 행만) | red-green | (a) NEW-TOPO | P10 병합 **[미확인: 행 수는 P10이 정한다]** | Y | E0 |

### 5.9 배선

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 40 | `theta-order-gate` | W-1 `validate_theta_declaration_order`를 `_build_theta_evaluator`에 배선(최종 thetas) | red-green | (a) library topology의 theta 순서만 뒤바꾼 픽스처 거부, 무동작 9/9(위반 0 [prep]) | #6 | Y | E0 |
| 41 | `euler-repair-wire` | W-2 `find_euler_repair_options`를 `run_topology_pipeline_with_finger_fixup` 분할 폴백 앞에 + D-5 삭제 | red-green + E-INST 전후 | (a) S146 blocked 그룹, (c) 행 배치 전후(DEC-47) | #2, 달라지면 DEC-40(§7.1 뒤 목록) | Y | E0·E2 |
| 42 | `roles-ratify-cli` | W-3 `apply_device_roles_gap_fill` 도구 진입점 + 게이트 메시지 | red-green | (a) 합성 topology 사본 기록·재로드 | - | Y | E0 |

### 5.10 회로

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 43 | `ic11c-two-stage-stage1` | I-C11 two_stage stage1_out 분리 | red-green **[미확인: 수정이 topology connectivity(사용자 몫)인지 엔진 규칙인지 -- 회로 해석 공동분석]** | (c) E-INST 전후 | UD-6 | Y | E2 |
| 44 | `ic11c-nmcnr-stage2-diode-ref` | I-C11 nmcnr stage2_diode_ref 이월 | 위와 같음 | (c) | UD-6, UD-3(nmcnr ±0.9 실행 전환) | Y | E2 |

### 5.11 조건부

| # | id | 조건 | 내용 |
|---|---|---|---|
| C1 | `theta-authoring-wire` 또는 `d4-delete-theta-authoring` | UD-7(U-A) 결과 | theta 작성 묶음 4함수 배선(검토 필요 게이트 + W-3 도구 기록) 또는 삭제 |
| C2 | `df09-area-blend` | D-1이 승인되지 않으면(UD-0에서 삭제 거부) | DF-09 `(2−α)A` 식 수정(TS4 red) |

**합계: 47건 + 조건부 2건.** (Phase 3 전 후보 5(#45 포함), 선두 5, 실패 규약 7, 레일 8(#46·#47 포함), 노드전압 2, LUT·PDK 7, 캐시 3, 개별 5, 배선 3, 회로 2.) 번호 #45~#47은 v0.2에서 더한 것이고, 표에서는 관련 묶음 안에 넣었다. `prep_phase4_scope.md` §4.3 추정 35~43보다 많은 이유: U-27·U-30을 무동작 단계와 동작 변경 단계로 나눴고(전후 비교에서 변화 원인을 가르기 위함, `prep_u27_u30.md` §3.5), 보류 행 삭제를 3 card로 나눴다. 한 문서로 둔다(N9.1). 분할 문서는 계획 개정이라 하지 않는다.

**card 단위 확인이 필요한 것**: #1은 크다(새 인자를 받는 함수 20개, 호출부 ~45 [prep]) -- 로드 경로/평가 경로 둘로 나눌 수 있다(`prep_b26_supply_nets.md` §3.4). #13 `fallback_events` 지점 전수가 많으면 스키마 card와 지점 card로 나눈다 **[미확인: 지점 수 미측정]**.

---

## 6. DoD 표

auditor가 Phase 4 마지막 card 병합본의 격리 복제본 `<iso>`에서 실행한다. `PT` = `10-test-separation` §10 정의(`--gmid-phase=4`). `$PY` = `C:/Python314/python.exe -B`. 새 도구 경로는 해당 card가 만든다(이름은 초안 -- card 작성 전 test glob 충돌 grep).

| ID | N6.2 `4` 조건 | 명령 | 통과 기준 |
|---|---|---|---|
| E0 | DF마다 red-green | Phase 4 card마다 `.ai/verification/<id>.json`의 판정 유형·red 기록(`00-common` §8.1 스키마) | §5 card 전부 판정 기록 있음, red-green card는 base red(허용 예외 타입 안) + 병합본 green. 계획 N5.2에서 담당 Phase에 4가 있는 DF 전부가 card 또는 닫힘 기록(DF-09 삭제·DF-29 삭제·DF-35·36 완료)에 대응 **[미확인: 판정 기록 필드 이름은 스키마에서 card 작성 때 확인]** |
| E1 | V8 도입(정본 실행 `fallback_events` 0) | 사이징 대상 회로마다 하네스 정본 실행 → 산출물의 `fallback_events`(위치는 #13이 정한다. 기본안: `instance.json` 최상위 키) | 모든 회로에서 빈 목록. 키가 없으면 FAIL(계측 미배선 = WP-01) |
| E2 | 사이징 대상 회로 실행과 전후 비교표 | base = Phase 3 DoD 병합본, head = Phase 4 마지막 병합본. 회로마다 하네스 정본 실행 θ*·metric 전부·`instance.json` 정규화 해시, 변화마다 원인 card id | 표가 판정 기록에 있고, 바뀐 기준선마다 DEC-40 승인 기록 id가 붙어 있다. two_stage·nmcnr는 I-C11(#43·#44) 해소 전후 두 단으로 적는다 **[미확인: 현 HEAD 하네스 정본 실행에서 두 회로가 끝까지 도는지 재측정 안 함 -- 중앙점 θ 거부만 prep 근거]** |
| E3 | IC11 2레일 케이스 PASS | `PT -rA <iso>/skills/analog-gmid-design/assets/tests/contracts/test_ic11.py` | `rail2` PASS, `rail3`·`reject` XFAIL(6a) |
| E4 | MG1 옛 키 거부 test PASS | `PT <iso>/…/tests/contracts -k "legacy"` **[id 초안]** | 계획 `supplies`, spec 스칼라 `vdd`, metric 인자 `supply_nets`(+`rail_nets`) 각각 `SchemaRejectedError`, 조용한 통과 합성 구현에서 test FAIL(자기 점검) |
| E5 | DF-27 VS 축 밖 픽스처 거부 | `PT <iso>/…/tests -k "lut_axis"` **[id 초안]** | 축 밖 입력 → `lut_axis_out_of_range`(SEAL_VIOLATION), 클램프 0 |
| E6 | U-27 옛 격자점 대조 기록 | auditor가 새 LUT와 옛 표본(sha256 `753d802a…f177f`)의 공통 격자(L 12 × VGS 49 × VDS 49 × VS 5)를 열별 비교 → `.ai/verification/<u27b id>/grid_compare.json` | 기존 열 비트 동일, 아니면 원인 보고 + DEC-40 승인(UD-11). 새 해시로 지문이 바뀜을 기록(배선은 #33) |
| E7 | U-30 전후 비교표 | #28: E-INST 동일(무동작), #29: self-test·사이징 대상 회로 비교(C1·C2 레이아웃, C3 사이징 분리) | `min_finger_w` 출처 = difftap.2 기록, 공정 기록 밖 PDK 사본 0(AST: 하네스 `min_finger_w`·`W_bounds`·`L_min` 리터럴 0, 엔진 폴백 0), 바뀐 기준선마다 UD-12 승인 |
| E8 | 성능 보고(N6.3) | `$PY <iso>/skills/analog-gmid-design/assets/tests/tools/measure_search_perf.py --worktree <iso> --circuit <파일럿> --out <iso 밖>`(`00-common` §10) | Phase 4 마지막 동작 변경 card의 `perf.json` 존재, `status=ok` |
| E9 | 무동작 증명(N6.3·DEC-47) | CC-8 뒤 card마다 `noop_proof.py`(`00-common` §11.5), spec card '기능이 필요 없는 회로' 전부 | card마다 `noop-<circuit>.json` PASS |
| E10 | DF-19 '운영부 레일 이름 리터럴 0' | `$PY <iso>/skills/analog-gmid-design/assets/tests/tools/rail_literal_scan.py --root <iso>` **[도구 이름 초안, #19가 만든다]** | exit 0, 발견 0(예제 데이터 면제 규칙은 #19 계약) |
| E11 | 전체 회귀·실패 규약 | `PT` 전체 + E-LIB 재측정 + N3.14 대조 test | 실패 0, E-LIB 9/9(로드 결과 차이는 원인 card 판정 기록에 설명된 것만) |

---

## 7. 사용자 결정 (진짜 사용자 몫만)

**UD-0 이 design 승인(DEC-51)**: 아래 '원칙 기본안'(§7.2)과 계획 정정 요청(§9)을 함께 덮는다.

### 7.1 결정 항목

| ID | 결정 | 권고(준비된 기본안) | 왜 사용자 몫인가 | 막는 card | 결정 자료 |
|---|---|---|---|---|---|
| **UD-1** | **D1 레일 극성** | **(C) 구조 규칙 기본 + 선택 필드 `supply_roles`(예외 회로만)**. 규칙: 선언 레일이 PMOS source로만 = hi, NMOS source로만 = lo, 둘 다 아님 = mid, 둘 다 = 거부. 게이트: CONFLICT·hi 없음·lo 없음 거부, 선언과 구조 증거 모순 거부, `supplies_v`가 있으면 전압 순서 대조(H4 조용한 오답을 여기서 잡는다). library 9/9 규칙으로 판정 → 파일 수정 0 [prep]. `supply_roles` 필드 코드는 첫 예외 회로와 함께(만들면 배선) | 회로 해석 규칙(공동분석). 대안 (B) '항상 사람이 극성 선언'은 9 topology 수정·승인 기록 | #17, #19 | `b26_decision_table.md` §1·§3 |
| **UD-2** | **D2 소신호 MNA에서 선언 레일 전부 교류접지** | **(i) 예**: `{r: 0 for r in supply_nets}` 다음 `also_fix`·`excite`로 덮어쓰기. 이상 전원 소신호 해석의 정의와 맞고, 바뀌는 기준값은 current_reuse `cmrr_estimate_db` +0.235 dB(제약 ≥ 60 dB 대비 여유 13 dB, 완화 방향) 하나 [prep]. **DEC-40 기준선 승인 1건 동반**(θ*에서 auditor가 다시 잰 값으로) | 동작 변경 + 기준선 변경 | #18 | `b26_decision_table.md` §2·§3 |
| **UD-3** | **U-26 (a) `supplies_v` 값과 nmcnr 분할 레일 실행 전환 시점** | two_stage·current_reuse·folded = `{vdd: 1.8, gnd: 0.0}`(현 `SPECS` `vdd` [재측정 F6]), nmcnr = 확정값 `{vdd: 0.9, vss: −0.9}`를 MG1 card(#21)에서 실행 spec에 반영 | spec 값(레일 전압) | #21, #22, #44 | `prep_phase4_scope.md` §5.1-2, `prep_b26_supply_nets.md` §4 |
| **UD-4** | **U-04 픽스처/정본 구분** | 계획 기본안: spec에 `origin: canonical \| fixture` 필수, 픽스처는 유도 임계값을 읽지 않음 | 계획이 사용자 결정으로 지정(N7.2) | #37 | 계획 1079행 |
| **UD-5** | **U-05 비단조 곡선 이분 역산** | 계획 기본안: 단조 구간별 근 전부 반환 + 호출자 선택 규칙 명시(DEC-11 확장). B24 (b) PMOS W 차이를 같은 card의 red 후보로 | 계획이 사용자 결정으로 지정 | #31 | 계획 1080행, `prep_phase4_scope.md` §5.1-7 |
| **UD-6** | **U-09 / I-C11 해소 방식** | Phase 4에서 DF와 함께(계획 기본안). design 보강판에서 two_stage stage1_out·nmcnr stage2_diode_ref의 connectivity 제안표를 내고 사용자가 확인 **[미확인: 제안표 준비 문서 없음 -- §8 준비 항목]** | 회로 해석·topology connectivity(WP-07) | #43, #44, E2 | 계획 979·1084행 |
| **UD-7** | **보류 행 U-A: theta 작성 묶음**(`propose_theta_kcl_gap_fill`·`apply_theta_kcl_gap_fill`·`audit_theta_root_direction`·`find_idiom_matches`) | **배선**: `load_topology`가 theta 미선언·부분 선언 회로에 제안을 계산하고 `_build_theta_evaluator`에 '검토 필요' 게이트(자유 root·placeholder 있으면 거부), 기록은 W-3 도구. 근거: DEC-62 경로가 지금 이것뿐, 5회로 theta 0 [prep]. `audit_theta_root_direction`은 ports feedback 역할 선언 허용 뒤 | 회로 해석 규칙(WP-06) + topology 데이터(feedback 선언) | C1, #19 | `prep_deferred_rows.md` §3.3 U-A |
| **UD-8** | **보류 행 U-B: `find_diode_stacks` 묶음** | **삭제**: S1 `is_diode` = `is_diode_connected`, 이웃 관계는 6a S1 관계 엣지로. current_reuse만 18 대 16(`M58`·`M63`) [prep] | ★ diode 정의(공동분석) | 6a S1 | 같은 문서 U-B |
| **UD-9** | **보류 행 U-C: `find_differential_and_mirror_forks`** | **6a ★ 공동분석까지 유지(비운영 면제)**, B26 작업 없이 B26-4 lint에서 이 함수만 면제. 운영 `find_verified_...`가 4회로에서 못 찾는 관계를 이 함수가 낸다 [prep] | ★ diffpair/mirror 정본(공동분석) | #19 | 같은 문서 U-C |
| **UD-10** | **보류 행 U-D: `check_mirror_symmetry` 묶음** | **7b I-A13 좌우 대칭 검사의 바탕으로 배선**, 7b까지 미배선 면제. 기존 U-02 승인 3항(삭제 명시)을 번복하는 것이라 사용자 결정 | 기존 승인과 충돌 | 7b | 같은 문서 U-D |
| **UD-11** | **DEC-40 기준선 승인 -- U-27 새 LUT** | 기존 열 비트 동일이 목표. 다르면 원인 보고(넷리스트 G3 변경 탓 여부) 뒤 건별 승인 | 기준 변경은 매 건 사용자 승인 | #27 | `prep_u27_u30.md` §4.1 UD-b |
| **UD-12** | **DEC-40 기준선 승인 -- U-30 교체** | C3(`W_bounds` 하한 1 µm → 0.42 µm)로 바뀌는 4회로 θ*·기대값, C1·C2(finger 배정·floorplan). 비교표를 auditor 판정 기록으로 제시한 뒤 건별 승인. 영향 후보: folded M3·M4 1.017 µm, nmcnr M202 1.02 µm [prep] | 같음 | #29 | `prep_u27_u30.md` §3.5·§4.1 UD-a |
| **UD-13** | **B26-1 V3 처리**(검토 U1) | 선택지는 셋이다. (a) 이 card의 V3 대상을 diff가 닿은 문장과 새 def로 좁히고, 나머지 변이는 id 목록으로 면제하는 decision 승인 (b) card 재분할 (c) 전수 실행 + test 보강. **권고는 (a)이고, 한 card가 아니라 Phase 4 공통 규칙으로 한 번 정하는 것이다**(§8.4). 근거: 원칙('기본값 없는 키워드 인자', 만들면 배선)이 큰 def의 본문 전체를 V3 대상으로 만든다. (b)는 `kcl_series_union` 등이 로드·평가 경로에 함께 쓰여 깔끔히 나눌 수 없다 [prep: 검토 B1]. (c)는 수 일 단위다. 면제는 '생존 변이 id 목록 + 사유'로 판정 기록에 남긴다(기준 약화 은폐 금지) | 게이트 판정 범위를 좁히는 일(DEC-40 성격) | #1, 그리고 Phase 4 card 전반 | `review_b26_1.md` B1·U1 |
| **UD-14** | **DEC-60 넷 전환기 종료 + DF-19·26 넷 몫을 MG1에서 분리 + B26-1을 Phase 3 전에 착수**(검토 U2) | 승인한다. 전제(선언 없는 4회로)는 U-26 (b) 9/9로 사라졌고, 사용자 원칙 'topology 무관'과 맞는다. v0.1은 이것을 '알림'으로 적었으나 검토 S3에 따라 **decision 승인 기록 한 건**으로 바꾼다. 선례: U-39는 기본안도 원문 승인, DF-35·36 앞당김은 사용자 지시 | N2 결정표의 확정 결정(DEC-60)의 한시 조항을 바꾼다 | #1 | `draft_b26_plan_patch.md`, `review_b26_1.md` S3 |
| **UD-15** | **B36 analog-grammar의 소속과 게이트 편입** | **(a) 별도 skill로 두고 gmid 게이트 범위에 편입**: N3.12.2 행 추가(code-author = `assets/*.py`, 오케스트레이터 = 문서, 사용자 = 판정 트리), 게이트 도구 6개에 glob 추가, V7 동적 import 간선. 대안 (b)는 analog-gmid-design 흡수이고, 단독 CLI 삭제나 DUP를 감수해야 한다. 어느 쪽이든 plan_tables 승인과 게이트 변경 승인 2건이 필요하다. B35를 어댑터(B26-2)로 처리해도 게이트 공백은 남는다. 엔진 판정을 바꾸는 코드가 trailer·test·audit 없이 바뀔 수 있기 때문이다 | skill 경계·공유 설정, 판정 표 개정 | #46 | `prep_b34_b35_grammar.md` §2.3·§3.2·§5 |

**사용자 작업(결정 아님)**: `install.py` `SKILLS`에 `"analog-grammar"`를 추가한다(쓰기 주체가 사용자인 경로). B34(#45)가 병합되면 설치본은 조용히 틀리는 대신 **명시적으로 실패**한다. 그 전에 이 작업이 있어야 설치본이 동작한다.

**같은 성격으로 뒤에 올 DEC-40 승인**(지금 결정할 것 아님, 발생 시 건별): D2의 CMRR 기준선(UD-2에 포함), W-2 행 분할 감소로 바뀌는 E-INST(#41), `test_ic5` `_DOMAIN_TABLE` 행 삭제와 `len == 21` 수정(#2 D-4, #41 D-5 -- 한 card에 몰아 V5 1회), 각 DF 수정으로 바뀌는 θ*(E2), B26-1 기존 test에 `supply_nets`·`rails=` 추가가 V5로 잡히면 `target_kind: diff`.

**알림 항목**: v0.1의 'B26-1 앞당김 알림'은 v0.2에서 UD-14(승인 기록)로 올렸다. B35를 확장안이 아니라 어댑터로 처리하는 것은 원칙 기본안이다(경로표 개정 불필요, §3.2). 다만 준비 문서의 권고와 다르므로 보고 때 알린다. 정보 보고: `max_finger_w` 40 µm가 모델 bin W 상한 7.0 µm보다 크다(이번에 값을 바꾸지 않음, `prep_u27_u30.md` UD-c).

### 7.2 원칙 기본안(UD-0으로 확정 -- 따로 묻지 않는다)

| ID | 기본안 | 근거 |
|---|---|---|
| P-1 | `supply_nets` 없으면 거부, 이름 집합 대체 경로 없음(D0) | 9/9 선언 완료(U-26 (b)), 사용자 원칙 'topology 무관' |
| P-2 | 보류 행 삭제·이관 D-1~D-7, 배선 W-1~W-3 | `prep_deferred_rows.md` §3.1·§3.2(G-1~G-4, WP-01·WP-14, DEC-79). 계획 소비자 있는 행(DF-09·TS4·DEC-25·DF-06)은 같은 card에서 계획 정정 |
| P-3 | `tol_V`는 DF-02와 한 card(MOD1), `tol_I`는 Phase 4에서 만들지 않음 | 만들면 배선(§4.3) |
| P-4 | U-30 범위에 엔진 폴백 15곳·단위 통일·`L_min` 배선 포함. 선언 위치 = 공정 기록 JSON 하나 + MOD1 로더 + LUT 메타 해시 연결(`sizing_spec.json`·npz 직접 저장 기각). `max_finger_w`·`W_bounds` 상한·`stage_w_max`는 PDK 규칙이 아니라 하네스 탐색 설정 공통 한 곳(값 유지). U-36·`finger_pitch_overhead_m`은 자리만 `null` + 사유 | DEC-68, `prep_u27_u30.md` §3.4·§4.2 |
| P-5 | U-27 VS 격자 = 상한은 `supplies_v` 최대 차에서 유도(1.8 V), 간격은 기존 0.2 V 유지(옛 5점이 부분집합 → 비트 대조 가능). 0.1 V는 보간 오차 실측이 생기면 | 새 상수 금지, `prep_u27_u30.md` §4.2 |
| P-6 | U-27 → U-30 순서(기준선 승인 1회) | 같은 문서 |
| P-7 | 캐시: 새 캐시 없음, DF-07 = 상한 LRU, DF-13 = 내용 지문 + 상한 | NFR-2, N3.3 |
| P-8 | DF-23 Phase 4 범위 = P10 전수 목록의 담당 4 행(목록 밖으로 넓히지 않음) | 계획 DF-23, P10 |
| P-9 | 레일 인자는 기본값 없는 키워드 전용 | §4.2 |
| P-10 | B34: analog-grammar는 필수 의존이고 부재 시 명시적 오류. 선택 의존안 (c)는 기각 -- 이 기능은 보강이 아니라 사이징 입력(device_roles·vsid·review 게이트)의 원천이다 | 조용한 폴백 금지, `prep_b34_b35_grammar.md` §3.1 |
| P-11 | B35: B26-2의 SD 호출부 어댑터. analog-grammar 파일은 불변, 경로표 개정 불필요. monkeypatch(전역 `RAILS` 교체)는 기각 | `review_b26_1.md` S2, 조정자 지시(v0.2) |
| P-12 | B37: `ports` 선언을 넘겨 이름 힌트 추정을 대체한다(topology 무관) | DEC-62 |

---

## 8. 병렬 준비 계획

card 처리 속도 규칙(메모리): 사실 문장은 쓰는 자리에서 재측정, 새 이름은 test glob 충돌 grep, 원칙은 계약에 전 범위로, 삭제 전 계획서 소비자 grep, 병렬 가능한 준비는 항상 미리.

### 8.1 지금(Phase 2 남은 card·Phase 3 design 승인과 병렬)

| 준비 | 산출 | 막히는 것 |
|---|---|---|
| B26-1 spec card 보강(검토 완료: `review_b26_1.md`) | B1 'V3 계획' 절, B2 역방향 한정, S1 호출 수 불변식, S4 red 진입점 표, S5 정정안 문구, M1~M6 | UD-13·UD-14 |
| 계획 정정안 커밋 준비(`draft_b26_plan_patch.md`) | `plan_tables_hash` 전후 측정. DF-19 비고의 "극성 판정"을 "집합 소속 대부분"으로 고치고, 12함수(운영 8)로 정정한다 | P9 병합 순서 |
| B34 spec card 초안(#45) | 계약 초안은 `prep_b34_b35_grammar.md` §3.1에 있음. 착수 시 폴백 사이트 줄 번호와 `unavailable_reason` 문서 grep을 다시 잰다 | 없음 |
| B26-2 어댑터 설계(B35 흡수) | 정준 토큰 규칙, 역치환 대상 전수(`cls`·`imp`·`stack_edges`·`Match.ports`·입력 힌트), §3.2의 반론 (i)~(iv) 계약화 | UD-1 |
| B36 게이트 card 준비(UD-15 (a) 가정) | 도구 6개의 glob 위치, V7 동적 import 간선 규칙, redteam 사례 | UD-15 |
| B37 영향 실측 | 9회로에서 `ports`를 넘길 때 `load_topology` meta 차이 | 없음 |
| V3 비용 측정(`v3_scope_systemic.md`, 진행 중) | card별 V3 대상 def·변이 수 추정(§8.4) | 없음 |
| UD-1~UD-15 결정 수집(자료 준비 완료, UD-6만 제안표 필요) | 승인 기록 초안 | 없음 |
| I-C11 connectivity 제안표(UD-6) | two_stage stage1_out·nmcnr stage2_diode_ref 현 연결·제안 연결·근거 | 회로 해석 -- 사용자와 공동분석 |
| `d4-delete-unwired`·`pole-oracle-to-tests`·`toy-lut-to-tests` spec card 초안 | 계획 소비자 grep(DF-09·TS4·DEC-25·DF-06), `test_ic5` 표 영향 | UD-0 |
| TS4 대상 실측: V4 lint(`test_lint.py`) 산출 목록 | D-1 삭제 시 TS4 대상 | 없음 |
| U-30 C4 대상: `W_bounds`·`min_finger_w` 생략 test·probe 픽스처 전수(AST) | #28 기존 test 영향 목록 | 없음 |
| U-27 병렬화 판단 자료(240조합 ≈ 22시간 직렬) | 조합 독립 실행 가능 여부 | 없음 |
| DF-15 재현 시도(읽기 전용 스크립트) | 재현되면 red 입력, 안 되면 계획 정정 요청 | 없음 |
| `fallback_events` 지점 전수 실측(DF-14 5지점 + DF-20 상수 + 엔진 폴백) | #13 card 크기·분할 여부 | 없음 |
| `setdefault("vsb")` 4줄(F9)의 DF-01 원인 지점 판정 | #24 범위 | 없음 |

### 8.2 Phase 3 진행 중

* 선두 5건(#5~#9) spec card 초안 -- 목적 모듈은 Phase 3 D0b 이관표 확정 뒤 파일:줄만 채운다.
* 파일 충돌 집합(§3.4)의 모듈 이름을 D0b로 확정.
* B33(V7 호출 그래프가 `__init__`·레지스트리 dict 값 간선 누락)이 G1에서 처리되는지 확인 -- CC-4(예외 클래스)·레지스트리 관련 card V7 판정의 잡음이 된다.

### 8.3 Phase 4 착수 뒤

* 선두 5건이 순서 고정이므로 그 사이에 나머지 묶음의 **작성 전 실측을 한 벌로** 뽑는다(모듈 이동 뒤 줄 번호 전부 갱신).
* U-27b 재생성은 `run_in_background` + 조합마다 체크포인트(결과는 파일에) -- 준비 card(#26) 병합 즉시 시작해 다른 묶음과 겹친다.
* auditor 측정 재사용: E-LIB·E-INST base 산출물은 Phase 3 DoD 기록을 base로 재사용하고 card마다 다시 만들지 않는다 **[미확인: Phase 3 DoD 기록 형식이 아직 없다]**.

### 8.4 V3 전신 변이 비용이 Phase 4 일정에 미치는 영향

**측정된 것(B26-1 한 card)** [prep: `review_b26_1.md` B1]
* `tools/gates/mutate_changed.py`는 AST가 바뀐 def의 **본문 전체**에 변이를 건다. 바뀐 줄에만 거는 것이 아니다.
* B26-1은 def 약 32개를 바꾸고, 변이는 약 2,465개다. 큰 것:
  * `_build_theta_evaluator` 497(1,004줄)
  * `propose_device_roles_gap_fill` 331
  * `optimize_full_circuit_budget` 229
  * `load_topology` 58
* 인벤토리(그 def를 지나는 test 수)는 `load_topology` 230, `propose_device_roles_gap_fill` 231, `_build_theta_evaluator` 110이다. 대부분 사이징 평가를 지나는 느린 test다. 변이 × 인벤토리 실행 시간은 **수 일 단위**다.
* `_METRICS_REGISTRY` dict로 불리는 metric 함수(`_metric_kcl_residual` 등)는 정적 인벤토리가 0이다. 그래서 새 test가 이름으로 부르지 않으면 변이가 전부 '생존'이 된다.
* B28(V3 이력 복제본)이 병합되면 도구가 실제로 돈다. 그러면 기준 실행 실패는 ERROR가 되고, P8·DF-36의 '사이트만 대체 측정' 선례를 쓸 수 없다.

**Phase 4 전반으로의 확장**: [미확인 -- `_drafts/v3_scope_systemic.md` 측정 대기, 작성 시점에 파일 없음]. 아래는 구조에서 나온 추론이고 수치가 아니다.
1. **큰 def를 건드리는 card는 매번 그 def의 전체 변이를 낸다.** §3.4 파일 충돌 집합에서 평가 커널 빌더(`_build_theta_evaluator`, 변이 약 497)를 고치는 card는 DF-03·DF-01·DF-02·DF-14·CC-7a·B26-2 6건이다. 여기에 CC-4b(DF-37 광범위 except, 여러 큰 def에 퍼짐)·DF-20·W-1이 더해질 가능성이 있다 **[미확인]**. `propose_device_roles_gap_fill`(약 331)을 고치는 card는 B26-1·B34·B26-2·B37 4건이다. 이 def들은 Phase 3에서 이동만 하고 분할하지 않으므로(N3.10) Phase 4에서도 크기가 그대로다.
2. **card 수 × 수 일**이면 Phase 4 병합 처리량은 V3 시간이 결정한다. 47 card 중 V3 대상 def를 가진 red-green card가 대부분이다. test-only·equivalence 이동 card(#3·#4 등)만 예외일 수 있다. [미확인: card별 변이 수 추정은 v3_scope_systemic.md가 나오면 이 절에 card별 열로 넣는다]
3. **정책 제안(UD-13 일반화)**: V3 범위 규칙을 card마다 결정하지 않고 Phase 4 공통으로 한 번 정한다. 기본안은 **'diff가 닿은 문장 + 새 def'를 대상**으로 하고, 나머지 변이는 도구가 낸 id 목록으로 면제를 기록한다. 이렇게 하면 기준 약화가 판정 기록에 남는다. 계획 N4.2 V3 행("diff가 닿은 def 중 AST 해시가 바뀐 것")의 해석 개정이므로 게이트 변경 승인이 필요할 수 있다 **[미확인: 계획 개정인지 decision 면제로 충분한지]**.
4. **완화책(원칙 안)**:
   * (a) CC-7a가 θ 탐색부를 함수로 추출하면 `optimize_full_circuit_budget`의 변이 대상이 줄어든다. 선두 순서상 이미 앞에 있다.
   * (b) registry 경유 metric test는 함수 이름으로 직접 부른다(인벤토리 0 방지). 모든 metric card의 interface card에 이 조건을 넣는다.
   * (c) 같은 큰 def를 고치는 card의 V3 실행은 auditor가 병합 순서대로 줄 세워 background로 돌리고 결과를 파일에 쓴다(메모리 규칙).
   * (d) 평가 커널 빌더의 분할은 6b의 '평가 커널 계산 블록 분할'이 맡는다. Phase 4에서 앞당기면 동작 보존 추출 card가 하나 더 생긴다. 판단은 v3_scope_systemic 수치를 본 뒤에 한다.
5. **일정 영향**: U-27b 재생성(약 22시간, background)은 V3와 자원을 다투므로 한 기계에서 동시에 돌리지 않는다 **[미확인: 병렬 실행 시 시간 영향 미측정]**.

---

## 9. 열린 항목과 계획 정정 요청

N9.2-8은 "열린 질문이 없어야 한다"이다. 1·2는 v0.2에서 닫았고, 남은 것은 2a다. 3 이하는 계획 정정 요청이다(오케스트레이터, 경위는 history).

1. ~~B34·B35 범위~~ **닫힘(v0.2)**:
   * B34는 #45(Phase 3 M2 전, P-10)로 둔다.
   * B35는 B26-2 SD 호출부 어댑터(P-11)로 흡수한다. 경로표 개정은 필요 없다.
   * B36 게이트 공백은 #46과 UD-15로 둔다.
   * B37은 #47로 둔다.
   * SD의 AG 사용 함수 수는 11(운영 7)이 아니라 12(운영 8)다. `geometry_colocation_union`이 `find_stack_edges`를 거쳐 더해진다 [prep: `prep_b34_b35_grammar.md` 요약]. netclass 판정은 대부분 집합 소속이다(극성은 netclass 102·103, idioms 600·601뿐 -- 검토 S2).
2. ~~B26-1 초안 독립 검토~~ **닫힘(v0.2)**: `review_b26_1.md`. blocking B1(V3)은 UD-13과 §8.4로, B2(역방향)는 #1 oracle 한정과 B26-2 meta 전체 불변으로 처리한다. S1~S5·M1~M6은 spec card 보강 목록(§8.1)에 있다.
2a. **남은 열린 항목**: `v3_scope_systemic.md`(§8.4 수치). 나오면 §8.4의 [미확인]을 교체하고 UD-13 권고를 다시 확인한다.
3. 계획 DF-29 행 닫힘(P5b 삭제), DF-09 행 닫힘(D-1 승인 시), TS4 행 "DF-09 등" → V4 lint 산출 목록, DEC-25의 `node_pole_estimate` 문장, DF-06 위치 열에서 `node_pole_estimate` 제거.
4. DF 위치 열 줄 번호 갱신(DF-26·30·31) -- 함수 이름 인용으로 바꾸는 것을 권한다.
5. U-27 "SID_1F 열 추가" → "새 VS 축으로 함께 재스윕", 계획 158행 문장, `sizing_recipe.py` docstring 660~662·4789~4791, checklist §8.1(코드 docstring은 #26 card에서).
6. DF-19 비고 "29개" → AST 전수와 assets 밖 사이트(1과 연결), DEC-60·GB0·W0·N3.16·DEC-69·MG1·DF-19·DF-26·N6.1 범위·공격 13·N6.2 6a·U-26 문구(`draft_b26_plan_patch.md` §1~§6).
7. N3.16 PDK 상수 행: 엔진 폴백 15곳을 옛 이름(사본) 열에 추가(U-30 범위 명시).
8. B21 (a) 매핑: `tol_I`는 6b(§4.3) -- P3c 재착수 조건 (a)의 담당 Phase를 6b로.

---

## 부록 A. 재측정 명령과 결과

`R` = `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`, `A` = `R/skills/analog-gmid-design/assets`, `$PY` = `C:/Python314/python.exe -B`.

| # | 명령 | 결과(요약, 전체는 `C:/g36/remeasure.json` -- 삭제 전 이 표로 옮김) |
|---|---|---|
| A1 | `git -C R rev-parse --short HEAD`, `os.listdir(R/docs/02-design/features)` | `cd64170`, design 4개 |
| A2 | SR·SD·하네스 줄 정규식(`^_DEFAULT_RAIL_(HI\|LO)\s*=`, `^_RAIL_NETS\s*=`, `fixed\s*=\s*\{"gnd": 0.0\}`, `_rail_nets\s*=\s*frozenset`, `"min_finger_w"`, `"W_bounds"`, `"L_min"`, `"vdd"\s*:`, `"min_vds_by_role"`, `\(1e-6,\s*200e-6\)`, `get\("min_finger_w",`, `_QUERY_CACHE_MAX`, `idu_up\s*=\s*1\.0`, `setdefault\("vsb"`) | F2·F6·F7·F9 |
| A3 | AST: 문자열 상수 `"supply_nets"`·`"supplies_v"`, `Subscript` 키 `"vdd"`와 `.get("vdd")` 호출 줄 | F3, F4(20줄. 8656은 `sed -n 8656p`로 오류 메시지 문자열임을 확인) |
| A4 | AST `ExceptHandler` 타입 이름 계수(파일 7개) | F5 |
| A5 | AST 최상위 def·class 줄, `_query` 메서드 줄 | F8 |
| A6 | `grep -n "min_finger_w" A/stick_diagram.py` | 5954·6043(1.0/40.0), 6204(0.4/45.0) -- 타입 주석 `: float =` 형태라 A2 정규식이 놓쳐 따로 확인 |
| A7 | `np.load(A/sky130_nfet_pfet_lut_sample.npz)` 키·`VS`·`len(L)`, 파일 sha256 | F10 |
| A8 | `os.listdir(R/.ai/approvals)` 정규식 `u-?0?4\|u-?0?5\|u-?0?9\|u-?26\|u-?27\|u-?30\|40-defect\|phase4\|b26` | 41개 중 일치 1(`20260922-u43-gitignore-githooks.md`, 무관 -- 'u43'의 부분 일치) |
| A9 | 레지스트리 문자열 계수 `보류(Phase 3/4/6a)` | 9 / 14 / 2 |
| A10 | `A/tests/contracts/test_ic11.py`의 `gmid_ic` 줄 | rail2 = 4, rail3·reject = 6a |
| A11 | `git -C R grep -n 자기참조 -- A/tests` | 4건(판정 자기참조는 `test_selftest_sizing_recipe.py:1786` 하나) |

측정 한계: A2 정규식은 줄 단위라 여러 줄에 걸친 선언을 놓칠 수 있다. A3은 `spec["vdd"]`·`.get("vdd")` 형태만 센다(`spec.get(key)`처럼 변수 키로 읽는 경우 제외).

## 부록 B. N9.2 필수 절 대응

| N9.2 | 이 문서 |
|---|---|
| 1 범위 | §1 |
| 2 인터페이스 | §4.3 표(새 함수·소비자), §3.1(목적 모듈). 시그니처 상세는 card별 interface card(선례 `draft_b26_1.spec.md` '신규 시그니처'). **보강판 과제**: `fallback_events` 스키마, 공정 기록 JSON 필드, `supply_roles` 스키마 자리, `vdd` 유도 함수 시그니처를 이 문서에 고정 |
| 3 판정식 | E-LIB·E-INST·NEW-TOPO는 `20-dead-code-dup` §3, 무동작은 `00-common` §11.4, 변환 불변(IC11)은 N4.1. **보강판 과제**: 전후 비교표(E2)의 정규화·허용오차 식(허용오차 없음 = 비트 동일이 기본, 동작 변경 card는 차이를 원인 card로 귀속) |
| 4 실패 경로 | N3.14 + `00-common` §7(CC-4a가 도입). Phase 4 이후 모든 card의 거부는 N3.14 클래스 |
| 5 역할별 산출물 | §5 |
| 6 DoD 측정 명령 | §6 |
| 7 착수 조건 | §7(U-04·05·09·26·27 승인 기록 0 -- F11), Phase 3 DoD PASS, 이 문서 승인 |
| 8 열린 질문 | §9 1·2는 v0.2에서 닫혔다. 남은 것은 2a(V3 비용 측정) |
