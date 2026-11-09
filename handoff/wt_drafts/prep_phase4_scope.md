# Phase 4 사전 조사: `40-defect-fixes` design 작성 준비

R = `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`, A = `R/skills/analog-gmid-design/assets`, 기준 HEAD = master `cd64170`.
읽기 전용이다(저장소·worktree 쓰기 없음, git 상태 변경 없음). 실측 스크립트(`measure.py`, AST 스캔)와 출력은 C:/g27에 두었다가 삭제했다. 스크립트가 한 일은 §3 각 항목에 적었다.
design 문서 경로(계획 N9.1 규칙): `docs/02-design/features/gain-budget-gmid-sizing.40-defect-fixes.design.md`. 지금 있는 design은 `00-common`·`05-role-separation`·`10-test-separation`·`20-dead-code-dup` 4개이고, Phase 3은 초안(`_drafts/draft_phase3_design_v2.md`, `30-module-split`)만 있다.

---

## 0. 먼저 알아야 할 정정 세 가지

1. **DF-29~DF-33은 Phase 4 항목이 아니다.** 계획 N5.2의 수정 Phase 열 기준으로 Phase 4 몫이 있는 것은 **DF-34의 Phase 4 몫(PDK 상수 복사 제거)** 하나뿐이다. DF-29 = 2(목록)·7a, DF-30 = 7a, DF-31 = 7b, DF-32 = 6b·6c, DF-33 = 7b. 다만 DF-23(Phase 4 = "일반 규칙으로 교체")이 이름 리터럴 전반을 덮으므로, Phase 4가 실제로 고칠 리터럴 범위는 **P10(`df23-inventory`) 전수 목록에서 담당 Phase = 4로 적힌 행**이 정한다(P10은 아직 미완, Phase 2 남은 card).
2. **DF-35·DF-36은 이미 끝났다**(gate `34bc75e`, `148bd6d`, Phase 2 진행 중에 당겨서 처리). 그래서 N6.1이 정한 Phase 4 앞머리 순서 "TS4 → DF-35 → DF-36 → CC-4 앞부분 → CC-7·CC-8 → 나머지"는 실제로는 **TS4 → CC-4 앞부분 → CC-7·CC-8 → 나머지**다. design은 두 DF를 완료로 인용만 한다.
3. **DF-29는 사실상 삭제로 해소됐다.** 대상 함수 5개(`_load_telescopic_topology_cached`·`_telescopic_class_ab_open_loop_response`·`_cmrr_telescopic_class_ab_cmfb`·`_psrr_telescopic_class_ab`·`_psrr_telescopic_class_ab_cmfb`)가 HEAD에 없다(P5b `d7bce7a`가 삭제). 엔진 운영부의 파일럿 넷 이름 리터럴(`Vbias1~4`, `Vip`, `Vim`, `Vcmfb`, `Vop1`, `Vom1`)은 0건이다(§3.4). 계획 DF-29 행은 낡았고, 닫힘 기록은 history로 옮기는 정정 대상이다(오케스트레이터 몫).

---

## 1. 계획서 원문 인용 (`docs/01-plan/features/gain-budget-gmid-sizing.plan.md`)

### 1.1 N6.1 Phase 4 행 (1001행)

> | 4 | TS4 → DF-35 → DF-36 → `00-common` CC-4의 앞부분(실패 클래스·`FailureRecord`·`exit_code_for`와 DF-37의 하네스 `run()` 몫) → CC-7·CC-8(측정·무동작 도구가 이후 card에 쓰이도록 Phase 4 앞쪽에 둔다) → 나머지. Phase 4 전체 범위: TS4, DF-01~15·18~20·22~24·26·27·35~37, **DF-34의 Phase 4 몫**(회로별 `_spec_*()`이 따로 복사한 PDK 상수 제거 -- 함수 자체를 데이터 항목으로 바꾸고 삭제하는 것은 7b다), MG1 레일 이름 변경(DEC-69), U-27 LUT 재생성, PDK 상수 한 곳 선언(U-30), Phase 2에서 배선을 고른 함수 배선, `fallback_events` 계측(V8), 기존 4개 회로 실행 가능성(I-C11), IC11 활성 | red-green | U-04, U-05, U-09, U-26, U-27 | `40-defect-fixes` |

공통 착수 조건(991행): 해당 design 문서의 사용자 승인(DEC-51), 이전 Phase DoD PASS.

### 1.2 N6.2 Phase 4 완료 조건 (1019행)

> | 4 | DF마다 red-green, V8 도입(정본 실행 `fallback_events` 0), 사이징 대상 회로 실행과 전후 비교표, IC11 2레일 케이스 PASS, MG1 옛 키(계획 `supplies`, spec 스칼라 `vdd` 선언, metric 인자 `supply_nets`) 거부 test PASS, DF-27 VS 축 밖 픽스처 거부, U-27 재생성 LUT의 옛 격자점 값 대조 기록(다르면 원인 보고, 기준선 변경은 DEC-40 승인), U-30 PDK 상수 교체 전후 self-test·사이징 대상 회로 비교표(`min_finger_w` = difftap.2 출처 기록, 바뀌는 기준선·기대값은 DEC-40 승인) |

N6.3(공통): "성능: Phase 4부터 매 Phase 보고", "동작 변경 Phase(4 이후)는 DEC-47 대상 구분대로 측정하고 필요 없는 회로의 무동작을 증명한다."

### 1.3 N9.1 `40-defect-fixes` 행 (반드시 담을 것 / 읽을 plan 절)

> DF별 red 형태(행동 test / lint)와 수정 범위, N3.14 실패 클래스 도입, tol_V 함수 선도입, U-04·U-05 반영, `fallback_events` 스키마와 계측 지점 전수, exit code, I-C11 해소 설계, `supply_nets`·`supplies_v` 기반 레일 판정(DF-19·DF-26)·vsb(DF-24)·IC11, MG1(`vdd` 유도 함수, metric 인자 `supply_nets` 정리, 옛 키 거부), DF-27 축 커버리지 게이트, U-27 LUT 재생성 절차·대조, U-30 PDK 상수 한 곳 선언(규칙 번호 출처·`W_bounds` 하한 유도)과 교체 전후 비교, `00-common` CC-4(실패 규약 코드 형식, DF-37)·CC-5(옛 키 게이트, 직접 `json.load` 전수 대체)·CC-7(θ 탐색부 함수 추출·계측 인터페이스·성능 측정 도구)·CC-8(무동작 판정 도구, 진입점 `activations_out`), DF-35·DF-36
> 읽을 plan 절: N5.2 전체 / N3.6 / N3.10(MOD10 계측 인자) / N3.14 / N3.16(MG1) / N4.1 IC11 / N6.1·N6.2 Phase 4 / N6.3(성능) / `00-common` §6·§7·§10·§11 / DEC-60·61·69 / I-C11 / U-04·05·09·26·27·30

### 1.4 담당 Phase에 4가 들어 있는 DF 행 (N5.2, 원문 요지 -- 결함 / 위치 / 수정 Phase / 비고)

| ID | 결함(원문) | 위치 | 수정 Phase | 비고 |
|---|---|---|---|---|
| DF-01 | vsb를 노드전압으로 다시 고치면서 W·gm·gds는 옛 vsb 값으로 남는다(버전 혼재). 원인 코드 `setdefault("vsb", ref_vds)`가 남아 있다 | `reconcile_vsb_from_nodes`, `_hr_resolve_vertical_group` | 4(재계산), 6b(구조 제거) | I-B9 |
| DF-02 | 노드전압 경로 충돌(conflicts)을 엔진이 읽지 않는다 | `propagate_node_voltages` 호출부 | 4(충돌 시 SEAL_VIOLATION, tol_V 함수 선도입), 6b | I-B7 |
| DF-03 | vsb·L 동치류 게이트가 `ValueError`를 던져 탐색 전체가 멈춘다 | `_evaluate` 게이트 | 4(N3.14 실패로 교체) | 보고 시 명시 |
| DF-04 | 복구 함수가 소자명을 부분문자열로 찾는다("M1"이 "M11a"에 걸림) | `repair_infeasible_baseline` | 4 | |
| DF-05 | 미러비 오차 쌍을 그룹의 첫 두 소자만 본다 | `_mirror_ratio_error_pairs` | 4 | I-A4 |
| DF-06 | 광범위 except가 필드 원천을 조용히 버린다 | `node_pole_estimate`, `_mna_stamp_capacitance`, `synthesize_l_class_thetas` 호출부, `knee_L_for_kind` 호출부 | 4 | |
| DF-07 | 캐시 상한 도달 시 LRU가 아니라 캐싱을 멈춘다 | LUT `_query` 캐시, `_FEASIBLE_L_WINDOW_CACHE` | 4 | NFR-2 |
| DF-08 | spec 지문 불일치를 노트만 남기고 유도 임계값을 계속 쓴다 | `resolve_constraint_references` | 4 | U-04 |
| DF-09 | `estimate_area_budget` 블렌딩 식이 α를 상쇄한다(`(2−α)A`) | `estimate_area_budget` | 4(TS4 red) | |
| DF-10 | 이분 역산이 단조성을 검사하지 않는다 | `solve_id_for_target_gm`, `_invert_gm_id_for_current` | 4 | U-05, DEC-11 선례 |
| DF-11 | 적층 diode 해석이 LUT 실패 시 `idu_up = 1.0`을 대입한다 | `solve_stacked_diode_pair` | 4 | |
| DF-12 | 입력환산 오프셋이 gm 없는 소자를 조용히 뺀다 | `_metric_input_referred_offset` | 4 | |
| DF-13 | `id(lut)` 키 캐시와 상한 없는 캐시 | `diode_vds_cached`, `diode_vds_window`, `_KNEE_L_CACHE`, `_gm_id_curve_cache`, `_solve_vgs_cache`, `_idu_scan_cache` | 4 | SC-d |
| DF-14 | `except Exception`이 호출 실패를 폴백으로 바꾼다 | `lut_vdsat_headroom`, `stack_kvl_vgs_limit._known_vds`, `_hr_resolve_vertical_group`(2곳), `repair_infeasible_baseline._probe` | 4 | V8 계측 대상 |
| DF-15 | Rz 캐시 키가 소자명뿐이고 `_dc_replace`가 캐시 dict를 새 ctx와 공유할 수 있다(실행 재현 전) | `_resolve_nulling_resistor_ohm`, `revalidate_finger_override` | 4(재현 test 먼저) | |
| DF-18 | `run_harness.run`이 실패해도 exit 0이고 θ*를 출력만 한다 | `workspaces/run_harness.py` | 4(N3.14 exit code, θ* 기록) | 보고 시 명시 |
| DF-19 | 레일 넷 집합이 모듈마다 다르다(대소문자) | stick_diagram `_RAIL_NETS`, sizing_recipe `_DEFAULT_RAIL_HI`/`_DEFAULT_RAIL_LO` 레일 판정 | 4(DEC-60 `supply_nets`·`supplies_v` 선언으로 교체, MG1, DF-26과 같은 변경 단위, U-26) | "위치 열은 전수여야 한다 ... Phase 4에 **'운영부 레일 이름 리터럴 0' lint**를 두고 목록을 그 lint 산출로 대체한다" |
| DF-20 | 운영 경로의 근거 없는 폴백 상수(vds 0.6/0.2, margin 0.05, W_bounds·gm_id 격자 리터럴, 실행 spec의 역할 라벨 상수 `min_vds_by_role {"cascode": 0.2, "tail": 0.2}`) | `resolve_feed_vds` 계열, `workspaces/run_harness.py`의 `min_vds_by_role` | 4 | WP-03, DEC-27·DF-25(VDsat 유도로 대체), DF-32 |
| DF-22 | 지문 불일치 노트 리스트 `_RESOLVE_STALE_NOTES`를 읽는 코드가 없다 | `resolve_constraint_references` | 4 | DF-08과 함께 |
| DF-23 | 파일럿 적용 사실이 엔진 코드에 이름 리터럴로 박혀 동작을 정하는지 확인 필요 ... 점검 대상은 소자·넷·회로 이름과 topology 파일 경로 전부 | 엔진 소스 전수 | 2(전수 목록·레지스트리 기록), 4(일반 규칙으로 교체) | WP-05, DEC-62, DF-29~DF-34 |
| DF-24 | vsb 유도가 bulk를 nmos = 0 V, pmos = `vdd` 인자로 가정한다 ... `supplies_v`에 음전위 레일을 선언하면 nmos 분기가 틀어진다 | `derive_vsb_from_nodes`와 호출부 `reconcile_vsb_from_nodes` 등 | 4(red: 음전위 레일을 `supplies_v`에 둔 픽스처) | DEC-61, DF-01, U-26 |
| DF-26 | 레일 판정이 넷 이름 집합 하드코딩이다 ... 중간 전위 레일 `agnd`를 레일로 읽지 못한다 | sizing_recipe.py 3882~3883, stick_diagram.py 3147 참고 | 4(DEC-60 구현, DF-19와 같은 변경 단위) | DEC-60, DF-19, IC11, U-26 |
| DF-27 | LUT 표본 VS 축이 0~0.8 V(5점)라 push-pull follower vsb를 덮지 못할 수 있고, L 밖 축의 축 밖 입력 처리 규칙이 없다 | `sky130_nfet_pfet_lut_sample.npz`, `GmIdLUT` 보간부 | 4(red: VS 축 밖 픽스처를 `lut_axis_out_of_range`로 거부, LR3) | DEC-61, U-27 |
| DF-34 | 회로마다 실행 spec 파이썬 함수가 따로 있고 각 함수가 PDK 상수를 따로 복사한다 | `run_harness.py` `SPECS`와 회로별 `_spec_*()` | **4(PDK 상수 한 곳 선언 U-30으로 복사 제거)**, 7b(데이터 항목 교체·함수 삭제) | DEC-62, U-30, DF-23 |
| DF-35 | 하네스 저장소 경로 절대 경로 | `run_harness.py` 머리 | 4(CC-7·CC-8보다 먼저) | **완료 `34bc75e`** |
| DF-36 | instance.json `topology_ref` 절대 경로 | `save_instance_json` | 4(CC-8보다 먼저) | **완료 `148bd6d`** |
| DF-37 | 광범위 except가 N3.14 클래스를 삼킨다(2026-09-18 AST 실측 수) ... `except InfeasibleSizingError` 18곳 ... 하네스 `run()`은 모든 예외를 잡고 exit 0 | assets 전부와 하네스(줄 번호는 CC-4 spec card가 TS1 뒤 AST로 다시 센다) | 4(`00-common` CC-4) | N3.14 클래스와 `SchemaRejectedError`는 다시 raise |

참고(Phase 4 아님): DF-16 7a, DF-17 1(완료), DF-21 2, DF-25 6b, DF-28 7a, DF-29 2·7a(§0-3 삭제 해소), DF-30 7a, DF-31 7b, DF-32 6b·6c, DF-33 7b.

TS4(N3.11, 561행): "자기참조 기대값 제거(피검 식으로 기대값을 만든 test를 oracle 4종으로 교체) | 해당 결함 test가 base에서 FAIL(DF-09 등) | 4(첫 작업)".

### 1.5 IC11 (N4.1, 829행)

> | IC11 | 레일 기준 전위 가정(레일 0 V, 레일 이름 집합) | 전압 차는 노드전압과 레일 선언(DEC-60)에서만 유도 | `test_rail_origin_shift_invariance`: 같은 회로를 원점만 옮긴 두 레일 선언으로 돌려 소자 VGS·VDS·VSB·gm_id·W·metric(dc·ss·ls 전부)이 허용오차 안에서 같음(DF-24·DF-26 검출). Phase 4 대상은 레일 둘인 기존 회로(예: `two_stage_ota` (vdd 1.8, gnd 0 V) 대 (vdd 0.9, gnd −0.9 V)). agnd 3레일 신규 회로는 `supply_nets`가 생긴 뒤(6a, U-26 (b)) 대상에 추가. **거부 케이스(선행)**: 레일 셋 이상·음전위 레일 회로를 `supply_nets` 없이 로드하면 GB0 로드 게이트가 거부함을 같은 test 파일에서 먼저 증명한다(DEC-60, N4.3 공격 13) | 4(DEC-60 구현, 2레일), 6a(3레일 추가) |

현 상태: `A/tests/contracts/test_ic11.py:11` `gmid_ic("IC11", phase="4", case="rail2")` xfail 뼈대가 있다(rail3·reject는 phase 6a).

### 1.6 MG1 (N3.16)

정본 표 3행(769~771행):
> | 레일 넷 | `supply_nets`(list) | topology | sizing_recipe `_DEFAULT_RAIL_HI/LO`, `rail_nets`, stick_diagram `_RAIL_NETS` | MG1 |
> | 레일 전압 | `supplies_v`({넷: V}, DC) | sizing_spec human(7b 전 `SPECS` spec) | spec 스칼라 `vdd`(유도 함수 하나로 대체), 계획 `supplies`, metric `rail`의 `else 0.0`, nmcnr `sky130_supplies_v`·문헌 `supply_v`(→ 각 문서 기록의 `supplies_v`) | MG1(코드), MG0(문서) |
> | 공급 전류 셀 레일(다른 뜻) | metric 인자 `supply_nets` 이름 삭제, 레일별 기록 | metric 선언 | sizing_recipe `supply_current`의 `spec.get("supply_nets")` | MG1 |

단계 행(802행):
> | MG1 | 레일: topology `supply_nets`, spec `supplies_v`, `vdd` 유도 함수, 이름 집합 제거, metric 인자 `supply_nets`/`rail_nets` 정리. 옛 키 거부 게이트 + IC11 | code-author / test-author | Phase 4(DF-19·24·26과 같은 변경 단위) |

PDK 상수 행: "한 곳 선언(출처 규칙 번호 명시, `min_finger_w` = difftap.2, `W_bounds` 하한은 `min_finger_w`에서 유도, U-30). 키 이름 접미사는 U-32 | 공정 기록 한 곳(LUT 생성 메타와 연결) | spec_fn 4개 복사본(`L_min`, `W_bounds`, `min_finger_w` 등) | Phase 4(선언), 이름은 U-32".

### 1.7 DEC-60·DEC-62·DEC-69 (요지 원문)

* **DEC-60**(254행, 길어서 핵심 문장만): "레일은 두 선언으로 정한다(넷 이름 집합으로 판정하지 않는다). 레일 **넷** = topology 선택 필드 `supply_nets` ... 레일 **전압**(DC) = 사이징 스펙의 사람 선언 `supplies_v{넷: 전압}`(7b 전에는 `SPECS[circuit]` 항목) ... MG1(Phase 4) 전까지만 전환기 이름집합 해석을 쓴다 ... MG1부터 모든 사이징 대상 회로는 `supplies_v`가 필수이고 스칼라 `vdd` 폴백은 MG1과 함께 삭제한다(가장 높은 레일 전압은 `supplies_v`에서 유도하는 함수 하나). spec 넷 키 집합은 topology `supply_nets`와 같아야 하고 로드 게이트가 강제한다 ... 레일이 셋 이상인 회로의 공급전류는 레일별로 기록 ... 코드의 metric 인자 `supply_nets`는 Phase 4에서 이름을 비운다(MG1)". (i)(ii)(iii) 거부 규칙과 공격 13·14는 6a GB0 로드 게이트 소관이 섞여 있다(IC11 거부 케이스는 phase 6a 표식).
* **DEC-62**(256행): "새 토폴로지 추가는 데이터(topology.json connectivity·`ports`·`passive_elements`·`supply_nets`, `sizing_spec.json`(`supplies_v` 포함), `SPECS` 데이터 항목)만으로 끝나야 한다. 회로 이름으로 갈리는 코드가 필요해지면 그 사실을 일반 규칙의 결함(DF)으로 등록하고 규칙을 고친다. 현재 위반 8곳은 DF-30 ... DF-31 ... 회로별 실행 spec 함수는 DF-34, 파일럿 넷 이름·topology 경로가 박힌 운영 metric은 DF-29다" | 원칙.
* **DEC-69**(263행): "MG1 Phase 4(레일 코드) ... 각 단계는 옛 키 거부 로드 게이트를 같은 변경 단위에 넣고(선례 `validate_no_legacy_vs_key`, '실제로 거부한다'를 먼저 확인), 이름 변경 코드는 code-author, 옛 키 거부 red test·equivalence 비교는 test-author가 쓴다 ... 이름만 바꾼 변경은 사이징 대상 회로의 θ*·metric·instance.json 수치가 키 매핑 후 같아야 한다(다르면 동작 변경)".
* **DEC-61**(255행, DF-24의 근거): "없으면 nmos = `supplies_v` 중 가장 낮은 전위 넷, pmos = 가장 높은 전위 넷이다. vsb = abs(V(source) − V(bulk))이며 노드전압(W0 레일 전압 포함)에서 유도한다(레일 0 V 가정 금지)".
* **DEC-32 / N3.6**(tol 식, B21 (a)의 답): "`tol_V` = (kind, L 앵커, VDS)별 LUT leave-one-out 보간 오차(VGS 기준)의 최댓값 ... `tol_I` = `tol_V` × 해당 순환 블록 소자 gm의 최댓값". KCL 잔차 봉인 항목 3 "`exclude_nets`는 사유가 선언된 넷만".

### 1.8 Phase 4 착수 조건 U (N7.2 원문 요지)

| U | 결정 | 기본안 | 필요 시점 | 승인 기록(HEAD) |
|---|---|---|---|---|
| U-04 | 픽스처와 정본 spec의 구분 | spec에 `origin: canonical \| fixture` 필수, 픽스처는 유도 임계값을 읽지 않음 | Phase 4 | 없음 |
| U-05 | 비단조 곡선에서 이분 역산의 처리 | 단조 구간별 근을 모두 돌려주고 호출자가 선택 규칙을 명시(DEC-11 확장) | Phase 4 | 없음 |
| U-09 | two_stage stage1_out 분리·nmcnr stage2_diode_ref 이월을 언제 풀지 | Phase 4에서 DF와 함께 | Phase 4 | 없음 |
| U-26 | (a) 기존 4개 회로의 `supply_nets`·`supplies_v{넷: 전압}`(nmcnr은 확정 `{vdd: 0.9, vss: −0.9}`) (b) library 회로 `supply_nets`(9/9 선언 완료) (c) `wall_clock_budget_s` | (a) connectivity 레일 넷과 `SPECS[circuit]["vdd"]`로 제안표를 만들어 사용자 확인 ... "남은 것은 (a)의 레일 **전압** `supplies_v`다" | (a) Phase 4, (b) 6a(충족), (c) 6b | 없음((a)) |
| U-27 | LUT 재생성: VS 축 0~1.8 V, CGS·CGB 열 추가, `.noise` 포함 `SID_1F` | 확정: 진행. 선행 (1) DF-27 red가 옛 LUT에서 VS 축 밖 거부 (2) `sky130_lut_sweep.py`·ngspice·모델 경로 확인 (3) 옛 격자점 대조(다르면 DEC-40) (4) 새 LUT 해시로 S0·실패 캐시 지문 변경 기록 | Phase 4 | 계획 본문 확정(별도 기록 없음) |
| U-30 | `two_stage_ota`만 `min_finger_w = 0.1e-6` | 닫힘: 오류. PDK 상수 한 곳 선언, `min_finger_w` = difftap.2(0.420 µm), `W_bounds` 하한은 `min_finger_w`에서 유도, 교체 전후 비교 | Phase 4 | 계획 본문 닫힘 |
| (U-36) | 수동소자 단위 면적 PDK 출처 | U-30과 같은 곳에 선언 | 7b 착수 전 | -- |

---

## 2. Phase 4로 넘어온 백로그 (`.ai/context.md` 끝부분)

* **B21**(14939행, P3c 보류 사유, "Phase 4 공동분석"): "(a) B8 KCL 허용 범위 선언 부재 (b) supplies_v 레일별 전압 선언 부재(DEC-60, 스칼라 vdd만) (c) 엔진 결함 후보 -- folded_cascode 노드전압 전파가 순회 순서에 의존(X 1.6 vs 0.0 V, out 1.4 vs -0.2 V), 파일럿 다중 도달 불일치 4건(Vom1/Vop1 0.677 vs 0.900 V), KCL 잔차 파일럿 Vx 4.185 uA·folded tail 50.5 uA."
  * 매핑: (a) → N3.6 `tol_I` 식(원칙 유도, DF-02의 "tol_V 함수 선도입"과 같은 card), (b) → U-26 (a)·MG1, (c) → DF-02(conflicts 미소비)·IC2(순서 의존, 6b)의 재현 입력. P3c 재착수 조건.
* **B24**(14954행, "Phase 4"): "(a) LUT에 VGS 기준 gm·gds 공개 조회 API 없음(면제 해제 조건) (b) 정해진 VGS의 W와 size_transistor W가 PMOS에서 다름 -- 결함 후보(P3b의 PMOS gm/ID 비단조, _solve_vgs 최고 근 선택과 같은 뿌리 추정)."
  * (a) 면제 = 승인 기록 `20260929-p4-scan-exempt`(gain_ranking의 `lut._query` 직접 조회). (b)는 DF-10·U-05(비단조 역산)와 같은 뿌리 후보.
* **B26**(14963·14972행): "P4에서 probe 레일 집합을 _DEFAULT_RAIL_HI/LO(넷 이름 리터럴)로 배선했고 _metric_supply_current는 'vdd'만 본다 -- supply_nets 선언에서 읽도록 고칠 대상" / "B26 해소 = supply_nets 선언 배선으로 엔진 전반 레일 이름 의존 제거(Phase 4 후보, P3c 재착수 조건 (2)와 같은 일)". 상세 조사는 `_drafts/prep_b26_supply_nets.md`(§3.4 card 초안 B26-1~4, §4 D0~D2). `_drafts/draft_b26_1.spec.md`는 **없다**(아직 작성 안 됨).
* 관련(Phase 4 밖이지만 영향): B19(diode `headroom_role` 라벨 의존 = IC4/DF-32, 6b·6c 회로 해석), B22·B30(문서 이름 안내), B25(스캐너 면제 단위), B33(V7 호출 그래프 간선 누락 -- Phase 4 card V7 판정 잡음이 된다).
* Phase 2 DoD 결정 D2(user_decisions.md): "P3c 보류(B21, Phase 4), 스캐너 범위 밖 rail-set 재구현 1건"을 DoD 기록에 남김 -- Phase 4 B26 card가 `tests/probe_physical_consistency.py`의 rail-set 재구현까지 정리 대상으로 잡아야 한다.

---

## 3. HEAD 재측정 (`cd64170`, AST 스캔, docstring 제외)

### 3.1 `_METRICS_REGISTRY` 회로 이름 키 (DF-30, 담당 7a)

* `sizing_recipe.py:5083-5110`, 키 23개 중 회로 이름 키 **4개**: `:5087 folded_cascode_gain_db`, `:5088 folded_cascode_pm_deg`, `:5089 nmcnr_gain_db`, `:5090 nmcnr_pm_deg`.
* 회로별 함수 **7개**: `_folded_cascode_rout` 2872, `_metric_folded_cascode_gain_db` 2893, `_metric_folded_cascode_pm_deg` 2909, `_nmcnr_stage1_rout` 2940, `_nmcnr_predict` 2965, `_metric_nmcnr_gain_db` 3019, `_metric_nmcnr_pm_deg` 3026(계획 위치 열은 5개만 적고 줄 번호 5656~5663은 낡음).
* `_CMRR_ESTIMATOR_REGISTRY`(4760)·`_PSRR_ESTIMATOR_REGISTRY`(4777)는 `diff_pair_tail` 하나씩만 남았다(P5b 삭제 뒤).

### 3.2 `_COMPENSATION_REGISTRY` 회로별 함수 (DF-31, 담당 7b)

* `sizing_recipe.py:1416-1423`, 키 4개: `:1417 miller_ota_topology`, `:1418 nmcnr_3stage_topology`, `:1419 ngcc_3stage_topology`, `:1422 current_reuse_telescopic_topology`(계획 줄 번호 1464~1471은 낡음).
* 정의: `topology_library.py:33`, `:62`, `:339`, `:373`. 회로 이름 보조 함수 3개 더: `nmcnr_compensation_elements` 121, `nmcnr_predict_ac_response` 137, `nmcnr_check_dominant_pole_approximation` 257.

### 3.3 회로별 spec 함수와 PDK 상수 복사 (DF-34, Phase 4 몫 = PDK 상수)

* `workspaces/run_harness.py`: `_spec_two_stage_ota` 72-129, `_spec_current_reuse_telescopic_ota` 132-209, `_spec_folded_cascode` 212-246, `_spec_nmcnr_amplifier` 249-304, `SPECS` 309-356(키 310·316·333·344).
* PDK 상수 사본(4벌):

| 키 | two_stage | current_reuse | folded | nmcnr |
|---|---|---|---|---|
| `L_min` | :115 1.5e-07 | :170 1.5e-07 | :239 1.5e-07 | :295 1.5e-07 |
| `W_bounds` | :117 (1e-06, 2e-04) | :172 같음 | :241 같음 | :297 같음 |
| `min_finger_w` | **:121 1e-07** | :186 1e-06 | :243 1e-06 | :301 1e-06 |
| `vdd`(MG1) | :105 1.8 | :142 1.8 | :234 1.8 | :288 1.8 |
| `min_vds_by_role`(DF-20) | :118 {cascode 0.2, tail 0.2} | :173 {cascode 0.2, tail 0.3, mirror 0.3} | :242 {cascode 0.2, mirror 0.2} | :300 {cascode 0.2, mirror 0.2} |

* **새 발견 -- 엔진 쪽 PDK 기본값 사본**(계획 U-30·DF-34 위치 열에 없음): `sizing_recipe.py:9273` `min_finger_w=spec.get("min_finger_w", 1e-6), max_finger_w=spec.get("max_finger_w", 40e-6)`, `stick_diagram.py:5954`·`:6043` 기본 인자 `min_finger_w=1.0, max_finger_w=40.0`(µm 단위), `:6204 search_shared_finger_w(min_finger_w=0.4, max_finger_w=45.0)`, `PROCESS_GEOMETRY` `:6272`(`finger_pitch_overhead_m` 0.0 `:6279`, I-A12 7b). U-30 "한 곳 선언"을 하네스만 고치면 엔진 기본값이 두 번째 정본으로 남는다 → U-30 card 범위에 이 기본값들을 넣어야 한다(원칙 유도, §5.2).
* 회로 이름·topology 경로 리터럴은 `SPECS` 데이터(311·317·334·345)와 `run_harness.py:367·393`(`current_reuse_telescopic_ota` 기본 회로 이름)뿐이다. DEC-62는 `SPECS` 데이터 항목을 허용한다.
* DF-33(7b) 사이트 확인: `stack_groups_override` :124, `row_split` :128(two_stage만).

### 3.4 파일럿 넷 이름·레일 이름 리터럴

* 파일럿 넷 이름(`Vbias1~4`, `Vip`, `Vim`, `Vcmfb`, `Vop1`, `Vom1`, `Vop`, `Vom`, `Vx`, `N_cc_rz*`): 엔진 운영부 **0건**. 걸린 것은 `stick_diagram.py` 예제 데이터 함수 `folded_cascode_example`(6743~6756, `X`·`Y`)·`two_stage_ota_example`(6783·6791, `OUT`)뿐이다(판정 아님, 레지스트리에 행 없음 = B32).
* 레일 이름 문자열 리터럴(대소문자 `vdd|vss|gnd|agnd|...`): `sizing_recipe.py` **42개 / 14함수**, `stick_diagram.py` **35개 / 10함수**(예제 2함수 포함), `run_harness.py` 4개(`vdd: 1.8` 선언). 상수 참조(`_RAIL_NETS` 등)까지 넣은 넷 판정 사이트 전수는 `prep_b26_supply_nets.md` §1.1·§1.2 표(sizing 14·stick 14 함수)가 정본이다.
* 이름 집합 정의: `sizing_recipe.py:3714-3715` `_DEFAULT_RAIL_HI/LO`, `:8003` `_rail_nets = frozenset({"vdd","gnd","vss"})`, `:4293` `_metric_kcl_residual` 인라인 튜플, `:4361` `_metric_supply_current` `spec.get("supply_nets") or ("vdd","VDD")`, MNA 고정 노드 `:4086` `build_ac_network`·`:4991` `_full_circuit_response` `fixed = {"gnd": 0.0}`, `stick_diagram.py:2983` `_RAIL_NETS`.
* 엔진이 topology 최상위 `supply_nets`를 읽는 곳: **0**. `supplies_v`를 읽는 곳: **0**(`run_harness.py:287` 주석뿐).
* 스칼라 `spec["vdd"]`·`.get("vdd")` 읽기(MG1 V 종류): `sizing_recipe.py` **21줄** -- 1729, 3254, 4626, 4653, 7068, 7222, 7228, 7290, 7295, 7296, 7445, 7449, 7450, 8233, 8242, 8277, 8652, 8656, 10157, 10159, 10160.

### 3.5 Phase 4 DF 대상 함수의 HEAD 위치 (모두 존재, DF-29만 부재)

DF-01 `reconcile_vsb_from_nodes` 3808·`_hr_resolve_vertical_group` 7089 / DF-02 `propagate_node_voltages` 3727(`conflicts` 3758~3786) / DF-03 `_build_theta_evaluator` 7930·`_evaluate` 8124 / DF-04 `repair_infeasible_baseline` 10410 / DF-05 `_mirror_ratio_error_pairs` 4388 / DF-06 `node_pole_estimate` 3917·`_mna_stamp_capacitance` 4029·`synthesize_l_class_thetas` 2451·`knee_L_for_kind` 2394 / DF-07 `_query` 378(`_QUERY_CACHE_MAX` 257, 상한 도달 시 저장 중단 390)·`_FEASIBLE_L_WINDOW_CACHE` 2530 / DF-08·22 `resolve_constraint_references` 7821·`_RESOLVE_STALE_NOTES` 7818·7840·7880 / DF-09 `estimate_area_budget` 2765(식 2793~2794) / DF-10 `solve_id_for_target_gm` 1433·`_invert_gm_id_for_current` 1471 / DF-11 `solve_stacked_diode_pair` 3491(`idu_up = 1.0` 3539) / DF-12 `_metric_input_referred_offset` 4561 / DF-13 `diode_vds_cached` 3206·`diode_vds_window` 3402·`_KNEE_L_CACHE` 2391·LUT 인스턴스 캐시 345·352·366, `id(lut)` 키 2432·2575·3215·3449 / DF-14 `lut_vdsat_headroom` 1591·`stack_kvl_vgs_limit` 1668(`_known_vds` 1747)·`_probe` 10471 / DF-15 `_resolve_nulling_resistor_ohm` 4908·`revalidate_finger_override` 11299(`_dc_replace`는 `dataclasses.replace` 별칭 42, 사용 8064) / DF-18 `run` `run_harness.py:422` / DF-20 `resolve_feed_vds` 1971, `min_vds_by_role` 엔진 소비 15곳 이상(1102, 1571, 1704, 1734, 1942~1984, 5498, 6583~6610 …) / DF-24 `derive_vsb_from_nodes` 3789 / DF-27 `GmIdLUT` 52, `SemiEmpiricalGmIdLUT` 259.

### 3.6 DF-37 광범위 except (핸들러 수, 현재 대 계획 2026-09-18)

| 파일 | `…ValueError…` | `Exception` | `InfeasibleSizingError` |
|---|---|---|---|
| sizing_recipe.py | 26 (계획 52) | 6 (7) | 18 (18) |
| stick_diagram.py | 4 (23) | 0 (1) | 0 |
| audit_current_forced.py / topology_to_markdown.py | 0 | 1 / 1 | 0 |
| run_harness.py | 1 (1) | 2 (2) | 0 |

감소분은 TS1 인라인 self-test 추출과 Phase 2 삭제로 보인다(원인 분리는 안 함). 계획이 적은 대로 CC-4 spec card가 그 시점 AST로 다시 센다.

### 3.7 LUT (DF-27·U-27·B24)

* `sky130_nfet_pfet_lut_sample.npz`: 축 L 12점(0.15~4 µm), VGS 49, VDS 49, **VS 5점 [0, 0.2, 0.4, 0.6, 0.8]**. 열 = ID·GM·GDS·CGG·CGD·**SID_1F**(n·p). **CGS·CGB 없음.** SID_1F는 이미 있다 -- U-27 문구 "SID_1F 열 추가"는 "새 VS 축으로 함께 재스윕"으로 읽어야 한다(design에서 한 줄 정정).
* 체크포인트 `assets/ac_sweep_checkpoints/*_VS0~4.npz`(nfet·pfet × L 12 × VS 5)가 있다 -- 재생성 도구의 재개 형식 확인 대상.
* B24 (a) 확인: `SemiEmpiricalGmIdLUT` 공개 메서드는 `id_density_at_vgs`, `gm_id_to_id_density`, `cgg_absolute`, `gm_gds_ratio`, `vgs_for_gm_id`, `gm_id_for_vgs`, `noise_1f_density`. **VGS를 주고 gm·gds 절대값을 받는 공개 메서드가 없다**(비공개 `_query`/`_query_multi`만).

### 3.8 레지스트리·승인 상태

* 레지스트리 §2 '정본 후보(B26 해소 뒤 확정)' 7행: 40(전류미러 그룹)·42(노드 DC 전압)·43(KCL 엣지)·53(gain)·54(PM)·55(CMRR)·56(MNA 스탬프).
* 레지스트리 §7 `보류(Phase 4)` **14행**(489~517): `_invq_newton`, `build_toy_lut`, `solve_diode_stack_current`, `estimate_area_budget`, `signal_path_nodes`, `node_pole_estimate`, `load_derived_bounds`, `MirrorSymmetryVerdict`, `check_mirror_symmetry`, `find_differential_and_mirror_forks`, `MultiLeafHubParityVerdict`, `check_multi_leaf_hub_parity`, `audit_vertical_stack_id_euler_feasibility`, `find_euler_repair_options`. Phase 3 초안 D-10이 `보류(Phase 3)` 9행을 더 `보류(Phase 4)`로 넘긴다 → Phase 4 시점 **23행**.
* **겹침(중요)**: `estimate_area_budget`(DF-09, TS4 첫 red 대상)·`node_pole_estimate`(DF-06, B26 사이트)·`find_differential_and_mirror_forks`(B26 사이트, 운영 도달 불가)·`solve_diode_stack_current`가 모두 "배선/삭제 판단" 보류 행이다. 삭제로 결정되면 그 DF 몫과 B26 사이트가 같이 사라지므로, **배선/삭제 결정이 TS4·DF-06·B26 card보다 먼저**여야 한다(지울 코드를 고치지 않기).
* `.ai/approvals/`에 U-04·U-05·U-09·U-26(a)·U-27·U-30 승인 기록은 **없다**.

---

## 4. card 후보와 의존

### 4.1 Phase 3 모듈 파일과의 관계

* 계획상 Phase 4는 Phase 3 DoD PASS 뒤다(N6.1 공통 착수 조건). `00-common` §17이 새 코드의 위치를 Phase 3 모듈로 정해 두었다: `SchemaRejectedError`·`FailureRecord`·`LEGACY_NAMES`·`load_json_checked` → **MOD2**, N3.14 예외 계층·`FAILURE_CLASSES`·`exit_code_for` → **MOD4**, θ 탐색부 추출·`ContextVar` → **MOD6**, `instrument`·`activations_out` 인자 → **MOD10**(Phase 3 M10이 만든다), tol_V 함수 → **MOD1**(N3.6 "MOD1 함수로 승격"). 따라서 CC-4·CC-5·CC-7·CC-8·tol_V는 **모듈 파일이 있어야** 계약대로 둘 수 있다.
* Phase 3 앞으로 당길 수 있는 후보(엔진을 건드리지만 모듈 위치 계약이 없는 것): **B26-1(접근자 + 집합 사이트), B26-4(레일 리터럴 lint)** -- `prep_b26_supply_nets.md` §3.5 근거(역방향 import 10건이 `_RAIL_NETS` 하나 때문, 편집 파일 2개 대 6개, 곧 지울 상수를 옮기지 않음). **충돌**: Phase 3 초안 v2 §1은 "레지스트리 §2 '정본 후보'의 정본 확정(B26, Phase 4)"을 범위 밖으로 적고 B26을 Phase 4에 둔다. 당기려면 N6.1 순서표·DF-19/26 문구("MG1과 같은 변경 단위")를 "넷 판정(B26) / 전압(MG1)"로 나누는 계획 개정 승인이 필요하다 → Phase 3 design 승인(UD-0) **전에** 정해야 D0b 배정(`_RAIL_NETS` 목적지)이 흔들리지 않는다.
* 엔진을 건드리지 않아 지금 준비 가능한 것: 결정 수집(§5.1), U-27 선행 조건 (2)(도구·ngspice·모델 경로 확인 -- 읽기 전용 실측), P10 전수 목록 완료(DF-23 Phase 4 범위 확정), 각 card 작성 전 실측.

### 4.2 묶음과 순서

```
[선두, 순서 고정]  TS4 ─> CC4a ─> CC7a(탐색부 추출, equivalence) ─> CC7b(계측·성능 도구) ─> CC8(activations_out·무동작 도구)
                     ▲ (DF-09가 estimate_area_budget 배선/삭제 결정에 기댐)
[결정 선행]        W1~W3(§7 보류 23행 배선/삭제) ──> TS4, DF-06, B26
[레일]             B26-1 ─> B26-2(D1) ─> B26-3(D2) ; B26-4(lint, B26-1 뒤)
                   MG1a(supplies_v 선언·vdd 유도 함수, U-26a) ─> DF-24(vsb, DEC-61) ─> IC11 rail2 활성
                   MG1b(옛 키 거부 + CC-5 load_json_checked, CC4a 뒤: SchemaRejectedError 필요)
[LUT·PDK]          DF-27(축 게이트 red, 옛 LUT) ─> U-27(재생성·옛 격자점 대조, DEC-40)
                   U-30(PDK 상수 한 곳 + DF-34 Phase 4 몫 + 엔진 기본값) ; B24a(VGS 기준 gm·gds 공개 API, 면제 해제)
                   DF-10·B24b(U-05 비단조 역산)
[실패 규약, CC4a 뒤] DF-03, DF-37 나머지(CC4b), DF-06, DF-14 + V8 fallback_events, DF-18 나머지(θ* 기록), DF-11, DF-12
[노드전압]         tolV(MOD1 tol_V·tol_I 함수, B21a) ─> DF-02(conflicts → SEAL_VIOLATION, B21c 재현) ; DF-01(vsb 재계산)
[캐시 NFR-2]       DF-07(LRU), DF-13(id(lut) 키 → 내용 지문, 상한), DF-15(재현 test 먼저)
[개별]             DF-04, DF-05, DF-08+DF-22(U-04), DF-20(근거 없는 폴백 상수), DF-23 Phase 4 몫(P10 목록)
[회로]             I-C11(U-09): two_stage stage1_out 분리, nmcnr stage2_diode_ref
[마감]             Phase 4 DoD: 사이징 대상 회로 전후 비교표, V8 0, perf 보고(마지막 동작 변경 card의 perf.json)
```

* **파일 충돌 집합**(병합은 순차, 준비는 병렬): `_evaluate`/`_build_theta_evaluator`(MOD6)을 고치는 DF-03·DF-01·DF-02·DF-14·CC7a·B26-1(8003행) / MNA(MOD5) B26-3 / 로드 경로(MOD2) CC-5·MG1b·B26-1 / LUT(MOD1) DF-07·DF-13·DF-27·B24a·tolV.
* **같은 card로 묶어야 하는 것**(원칙): DF-08+DF-22(같은 함수, 계획 비고 "DF-08과 함께"), DF-19+DF-26(계획 "같은 변경 단위" -- B26 분리 시 넷 판정 쪽), MG1의 이름 변경+옛 키 거부 게이트(DEC-69 "같은 변경 단위"), DF-14+V8 계측 지점(계획 비고 "V8 계측 대상").

### 4.3 개수 추정

| 묶음 | card 수 |
|---|---|
| 선두(TS4, CC4a, CC7a, CC7b, CC8) | 5 |
| 보류 행 배선/삭제(W1~W3, 결정 묶음별) | 2~3 |
| 레일(B26-1~4, MG1a, MG1b, DF-24, IC11) | 7~9(B26-1을 로드 경로/평가 경로로 나누면 +1, IC11은 DF-24에 흡수 가능) |
| LUT·PDK(DF-27, U-27, U-30, B24a, DF-10) | 5 |
| 실패 규약(DF-03, CC4b, DF-06, DF-14, DF-18, DF-11, DF-12) | 6~7 |
| 노드전압(tolV, DF-02, DF-01) | 3 |
| 캐시(DF-07, DF-13, DF-15) | 2~3 |
| 개별(DF-04, DF-05, DF-08+22, DF-20, DF-23) | 4~5 |
| I-C11 | 1~2 |
| **합계** | **약 35~43** (Phase 3 초안 15건의 2.5배 안팎) |

design 한 문서로 담기에는 크다. N9.1은 `40-defect-fixes` 한 문서로 정했으므로 문서는 하나로 두고, §8 spec card 표를 위 묶음 단위 소절로 나누는 것을 권한다(분할 문서는 계획 개정이라 필요 없으면 하지 않는다).

### 4.4 병렬 준비 가능한 것(spec card 초안·작성 전 실측)

* 지금: 결정 수집 전부(§5.1), W 결정 제안표(보류 23행마다 호출부·소비자·삭제 영향 -- 20-dead-code-dup U-02 제안표 양식 재사용), U-27 선행 (2) 실측, U-30 전후 비교 대상 목록(하네스 4 + 엔진 기본값 4곳), B26-1·B26-4 spec card 초안(당길지 결정 전이라도 내용은 같다), DF-15 재현 시도(읽기 전용 스크립트).
* Phase 3 진행 중: CC4a·CC7a·CC8 spec card 초안(목적 모듈은 Phase 3 D0b 이관표 확정 뒤 파일:줄만 채운다), TS4 대상 test 목록(자기참조 기대값 -- `test_s028_estimate_area_budget` 등, `test_selftest_sizing_recipe.py`·`test_selftest_stick_diagram.py`·`probe_diode_gmid_readiness.py`에 '자기참조' 표기 있음).
* Phase 4 착수 뒤: 선두 5건이 순서 고정이므로 그 사이에 나머지 묶음의 작성 전 실측을 한 벌로 뽑는다(card 처리 속도 규칙 -- 사실 문장은 card 작성 자리에서 다시 잰다).

---

## 5. 결정: 사용자 몫 대 원칙 기본안

### 5.1 진짜 사용자 몫

| # | 결정 | 기본안(제안) | 왜 사용자 몫인가 |
|---|---|---|---|
| 1 | `40-defect-fixes` design 승인 | -- | DEC-51 |
| 2 | **U-26 (a)** 기존 3회로 `supplies_v` 값과 nmcnr 분할 레일 실행 전환 시점 | two_stage·current_reuse·folded = `{vdd: 1.8, gnd: 0.0}`(현 `SPECS` `vdd`에서), nmcnr = 확정값 `{vdd: 0.9, vss: −0.9}`를 MG1a card에서 실행 spec에 반영 | spec 값(레일 전압) |
| 3 | **D1 레일 극성 규칙**(B26-2) | "PMOS source로만 나오는 선언 레일 = 높은 레일, NMOS source로만 = 낮은 레일, 둘 다 아니면 중간(agnd), 둘 다면 거부" -- 9/9 모순 0. 대안: topology에 극성 선언(connectivity라 사용자 작성) | 회로 해석 규칙(공동분석) |
| 4 | **D2 소신호 MNA에서 선언 레일 전부를 교류접지로**(B26-3) | 예(DEC-60 문언과 맞음). current_reuse `cmrr_estimate_db` 중앙점 73.145 → 73.380 dB(+0.235), θ*에서 auditor 재측정 | 동작 변경 + DEC-40 기준선 승인 |
| 5 | **U-09 / I-C11**: two_stage stage1_out 분리, nmcnr stage2_diode_ref 이월 해소 방식 | design이 connectivity 제안표를 내고 사용자 확인 | 회로 해석·topology connectivity(WP-07) |
| 6 | **U-04** 픽스처/정본 구분 | `origin: canonical \| fixture` 필수(계획 기본안) | 계획이 사용자 결정으로 지정 |
| 7 | **U-05** 비단조 역산 | 단조 구간별 근 전부 반환 + 호출자 선택 규칙 명시. B24 (b)(PMOS W 차이)를 같은 card의 red 후보로 | 계획이 사용자 결정으로 지정, `_solve_vgs` 근 선택(DEC-11)과 같은 뿌리 |
| 8 | **보류(Phase 4) 23행 배선/삭제**(W1~W3) | 항목별 제안표(20 design U-02 양식) 일괄 승인. 특히 `estimate_area_budget`(DF-09·TS4)·`node_pole_estimate`(DF-06·B26)·`find_differential_and_mirror_forks`(B26) 먼저 | 삭제·배선 판단은 사용자 승인(레지스트리 처리 열 문언) |
| 9 | **B26-1·B26-4를 Phase 3 앞으로 당길지**(순서표 개정) | 당긴다(prep_b26 §3.5), 전압 쪽(MG1·DF-24·IC11)은 Phase 4에 남김 | N6.1 판정 표 개정은 승인 대상(0.5 공격 16) |
| 10 | 기준선 변경 승인(DEC-40, 발생 시마다) | U-27 새 LUT 격자점 차, U-30 `min_finger_w` 1e-7 → difftap.2 교체로 바뀌는 two_stage 결과, D2 CMRR 변화, DF 수정으로 바뀌는 θ* | 기준 변경은 매 건 사용자 승인 |

### 5.2 원칙에서 확정되는 기본안(묻지 않는다, design에 근거와 함께 적는다)

* **D0 이름집합 대체 경로 없음**: `supply_nets` 없으면 거부. 9/9 선언 완료(U-26 (b)) + 사용자 원칙 "항상 topology와 무관한 엔진 식". DEC-60의 '전환기 이름집합 해석' 한시 조항 종료를 계획 정정으로 기록(오케스트레이터).
* **B21 (a) KCL 허용 범위**: 새 선언값을 만들지 않는다. N3.6 `tol_I = tol_V × 블록 gm 최댓값` 식을 MOD1 함수로 구현(DF-02의 "tol_V 함수 선도입"과 같은 card). 상수를 박지 않는다(memory: 근거 하나 남기고 계산+캐시).
* **U-30 범위에 엔진 기본값 포함**(§3.3 새 발견): 개념 하나에 저장 위치 하나(DEC-68). `min_finger_w` = difftap.2, `W_bounds` 하한은 `min_finger_w`에서 유도, 단위(µm/m) 섞임도 같은 card에서 한 단위로. U-36 수동소자 단위 면적은 선언 자리만 같은 곳에 두고 값은 7b 착수 전(U-36 기본안 문언).
* **DF-29 닫힘 기록**(삭제 해소, P5b) · **DF-30/31 계획 줄 번호 갱신**: 계획 정정(오케스트레이터, history로 경위).
* **DF-23 Phase 4 범위 = P10 전수 목록의 담당 Phase 4 행**(목록 밖으로 넓히지 않는다).
* **캐시**: DF-07 = 상한 있는 LRU, DF-13 = `id(lut)` 대신 LUT 내용 지문(SC-d) + 상한. 새 캐시를 만들지 않고 기존 엔트리를 고친다(NFR-2, N3.3). B26 접근자는 `_load_full_topology_cached` 엔트리에 얹어 평가 루프 안 재계산 0(prep_b26 §3.1).
* **U-27 SID_1F 문구**: 열은 이미 있다 → "새 VS 축으로 함께 재스윕"으로 읽는다(계획 한 줄 정정).
* **순서**: 선두 순서는 N6.1대로(DF-35·36 완료 반영). 보류 행 결정은 선두 TS4 앞.
* **작성자≠검증자**: 모든 card의 red·기대값은 test-author(interface card만 보고), 전후 비교표·perf 수치는 auditor 판정 기록에서만 인용. 레일 lint(B26-4)·tol_V 도구의 test도 test-author 합성 입력(oracle (a)).
* **만들면 배선**: 새 함수(`rail_declaration`, tol_V/tol_I, `vdd` 유도 함수, VGS 기준 gm·gds API, `load_json_checked`)는 만든 card에서 운영 호출부가 바로 부른다. B24a API는 면제 `20260929-p4-scan-exempt`를 같은 card에서 해제(gain_ranking이 공개 API로 교체)해야 배선이 완결된다.

---

## 6. design 문서 작성 시 주의 (측정에서 나온 것)

* 계획 DF 위치 열의 줄 번호는 대부분 낡았다(DF-26 "3882~3883·3147" → 현재 3714·2983, DF-30 "5656~5663" → 5087~5090, DF-31 "1464~1471" → 1416~1423). design은 함수 이름으로 인용하고 줄은 card 작성 전 실측에서 채운다.
* Phase 3이 끝나면 위 줄 번호는 전부 MOD 파일로 바뀐다. design의 위치는 **Phase 3 D0b 이관표**(레지스트리 목적지 열)를 인용한다.
* "사이징 대상 회로 실행과 전후 비교표"의 기준: `prep_b26` §2.4에서 two_stage·nmcnr가 bounds 중앙점 θ에서 `InfeasibleSizingError`였다(레일 무관). 전후 비교는 하네스 정본 실행(θ*)으로 하고, I-C11 해소 전 두 회로의 비교 범위를 design이 미리 적는다(N6.3 "I-C11 해소 전 two_stage·nmcnr" 문구).
* B33(V7 호출 그래프가 클래스 `__init__`·레지스트리 dict 값 간선을 놓침)은 CC-4(예외 클래스)·DF-30 레지스트리 관련 card의 V7 판정에 잡음을 낸다 -- Phase 4 착수 전 G1(Phase 3)에서 처리되는지 확인.
