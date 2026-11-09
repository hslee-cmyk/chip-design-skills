# Phase 4 사전 조사: U-27(LUT 재생성)·U-30(PDK 상수 한 곳 선언)

R = `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`, A = `R/skills/analog-gmid-design/assets`, 기준 HEAD = master `cd64170`.
읽기 전용으로 진행했다. 저장소·worktree에는 아무것도 쓰지 않았고 git 상태도 바꾸지 않았다. 실측 스크립트(`probe_u27.py`, `probe_full_combo.py`, `scan_inst.py`, `scan2.py`)와 출력은 C:/g31에 두었다가 삭제했다. 설치한 것은 없다.
선행 문서: `_drafts/prep_phase4_scope.md`(§1.1 PDK 상수 표, §3.7 LUT, §5.2 기본안).

---

## 0. 요약

* **U-27 선행 조건 (2)는 충족됐다.** 도구·ngspice·모델 경로가 전부 있다. 저장소 스크립트 `sky130_lut_sweep.py`의 넷리스트 생성기를 그대로 써서 한 조합 전체(pfet_01v8, L 0.425 µm, VS 0.8, 49×49 = 2401점, 6열)를 다시 돌렸더니 체크포인트와 **비트 단위로 같았다**(최대 절대차 0). 그러니 옛 격자점 대조(선행 (3))는 "비트 동일"을 기대값으로 삼을 수 있다.
* **U-27 스크립트에 재생성 전에 고쳐야 할 결함이 셋 있다.** (a) 체크포인트 이름이 VS **인덱스** 기반이다(`_VS{iVS}`). B15에서 L 쪽에서 고친 것과 같은 종류의 결함이다. (b) 체크포인트 재사용 조건이 `"SID_1F" in d` 하나뿐이다. 그래서 CGS·CGB 열이 없는 옛 체크포인트 120개가 조용히 재사용된다. (c) npz 메타에 `W_ref`(5 µm), PDK 경로·커밋, ngspice 버전이 없다. 그 결과 `W_ref=5e-6`이 43개 파일에 따로 복사돼 있다.
* **U-30 사본은 하네스 4벌로 끝나지 않는다.** 엔진 폴백 기본값이 `W_bounds`에 11곳, `min_finger_w`/`max_finger_w`에 4곳(단위도 m와 µm가 섞여 있다) 더 있다. 또 **엔진은 spec의 `L_min`·`L_min_by_kind`를 읽지 않는다**(죽은 키). 실제 L 하한은 LUT 축 `L_grid[0]`이다.
* **동작 영향이 큰 쪽은 `W_bounds` 하한 유도(1 µm → 0.42 µm)다.** `min_finger_w` 통일은 레이아웃 단계에만 영향을 준다. 반면 `W_bounds` 하한은 4개 회로의 사이징 단계 전체(11곳)와 `spec_fingerprint`(캐시 지문)를 바꾼다. 실측 instance에서 W가 1 µm 하한 근처인 소자는 folded M3·M4(1.017 µm)와 nmcnr M202(1.02 µm)다.

---

## 1. 계획서 원문 인용 (`docs/01-plan/features/gain-budget-gmid-sizing.plan.md`)

**U-27 (1102행)**
> | U-27 | LUT 재생성: VS 축 0~1.8 V, CGS·CGB 열 추가, **`.noise` 해석 포함해 `SID_1F` 열 추가**(2026-09-17 확정 -- 잡음 축을 지금 늘리지는 않되 데이터는 이 재스윕에서 함께 얻는다. 재스윕을 두 번 하지 않기 위한 묶음이고, 소비는 7b 이후 제약 metric이다. N1.2) | **확정**: 진행. 현 표본 `sky130_nfet_pfet_lut_sample.npz`는 VS 축 0~0.8 V 5점이고 CGS·CGB 열이 없다(실측). 담당 Phase 4(`40-defect-fixes`, DF-27과 같은 design). 선행 조건: (1) DF-27 축 커버리지 게이트 red test가 옛 표본 LUT에서 VS 축 밖 입력을 거부함을 먼저 확인 (2) LUT 생성 도구(`sky130_lut_sweep.py`)·ngspice·모델 경로(LUT 생성 메타) 확인 (3) 재생성 LUT의 옛 격자점 값을 옛 표본과 대조(다르면 원인 보고, 바뀌는 기준선은 DEC-40 승인) (4) 새 LUT 해시로 S0·실패 캐시 지문이 바뀜을 기록. CGS·CGB 열의 소비(스탬프)는 7a(DF-28). VS 축 상한 = library 회로 `supplies_v` 최대 전위차에서 유도한 1.8 V(LR3 유도와 일치) | Phase 4 |

**U-30 (1105행)**
> | U-30 | `two_stage_ota`만 `min_finger_w = 0.1e-6`(나머지 세 회로 1e-6)인 것이 의도인지 | **닫힘**: 의도가 아닌 오류다(판정 경위는 history H2). sky130 공식 periphery rules: difftap.2 최소 채널 폭 0.420 µm(표준셀 밖), difftap.2b 0.360 µm(표준셀 안), poly.1a 0.150 µm, poly.1b lvtn pfet L ≥ 0.350 µm. 로컬 bins.csv(nfet W ≥ 0.36, pfet W ≥ 0.42)는 모델 유효 범위이지 DRC가 아니다. 나머지 회로 1 µm·`W_bounds` 하한 1 µm는 근거가 없다. Phase 4 항목: PDK 상수를 한 곳에 출처 규칙 번호와 함께 선언, `min_finger_w` = difftap.2, `W_bounds` 하한은 `min_finger_w`에서 유도, 교체 전후 self-test·사이징 비교. 출처 기록 `skills/analog-gmid-design/references/lut-generation-checklist.md`(288행 참고) | Phase 4 |

**관련 행**
* 158행 (잡음 축): "... U-27 LUT 재스윕에 `.noise` 해석을 포함해 `SID_1F` 열을 함께 얻는다(**현재 LUT에 없어 `noise_1f_density()`가 호출 즉시 거부한다** ...)". 이 문장은 **낡았다**(§2.5 참고).
* 507행 LR3: "... 축 밖 입력은 클램프하지 않고 구조화 실패 `lut_axis_out_of_range{소자, 축, 값, 범위}`(SEAL_VIOLATION)로 처리한다(DF-27). 필요한 VS 축 상한은 상수로 두지 않고 library 회로 `supplies_v`의 최대 전위 차(현재 1.8 V, U-27)에서 유도해 LUT 생성 체크리스트 입력으로 둔다(U-27)".
* 499행 (SPICE 독립 검증): "`run_ngspice_op_ac(path)`(`C:\ngspice\Spice64\bin\ngspice_con.exe -b`, **모델 경로는 LUT 생성 메타에서 읽는다**)".
* 794행 N3.16 명명 표 (열: 개념 | 정본 이름 | 저장 위치 | 옛 이름 | 시기): "| PDK 상수 | 한 곳 선언(출처 규칙 번호 명시, `min_finger_w` = difftap.2, `W_bounds` 하한은 `min_finger_w`에서 유도, U-30). 키 이름 접미사는 U-32 | **공정 기록 한 곳(LUT 생성 메타와 연결)** | spec_fn 4개 복사본(`L_min`, `W_bounds`, `min_finger_w` 등) | Phase 4(선언), 이름은 U-32 |".
* 937행 DF-27, 938행 DF-28("열 추가 전에는 CGG−CGD 근사 표시, 열 생성은 U-27"), 944행 DF-34("4(PDK 상수 한 곳 선언 U-30으로 복사 제거), 7b(...함수 삭제)").
* 955행 I-A5: "`lut_conditions_from_npz`가 운영 경로에서 불리지 않는다 | 6a(S0에 배선)". 959행 I-A12: `finger_pitch_overhead_m` 0.0 → 7b(MOD8).
* 1001행 N6.1 Phase 4 범위: "... U-27 LUT 재생성, PDK 상수 한 곳 선언(U-30) ...". 1019행 Phase 4 DoD: "... U-27 재생성 LUT의 옛 격자점 값 대조 기록(다르면 원인 보고, 기준선 변경은 DEC-40 승인), U-30 PDK 상수 교체 전후 self-test·사이징 대상 회로 비교표(`min_finger_w` = difftap.2 출처 기록, 바뀌는 기준선·기대값은 DEC-40 승인)".
* 1107행 U-32 (기본안: 단위 접미사를 PDK 키에 적용하지 않음, 7b 착수 전 확정). 1111행 U-36 (수동소자 단위 면적을 U-30과 같은 곳에 선언, 7b 착수 전). 1137행 위험표 (SPICE 환경 확인은 7a design 첫 단계). 1141행 ("LUT 재생성(U-27)이 기존 기준선을 바꿈 | 옛 격자점 대조, 바뀐 기준선은 DEC-40 승인, 지문 변경 기록").

**참조 DEC**
* 234행 DEC-40 (D14): "기준 약화는 매 건 사용자 승인. 승인 기록 없이 병합 불가".
* 255행 DEC-61: vsb = abs(V(source) − V(bulk)), 벌크 기본 규칙(DF-24, U-27 VS 축 상한의 근거).
* 256행 DEC-62: "새 토폴로지 추가는 데이터(... `SPECS` 데이터 항목)만으로 끝나야 한다 ... 회로별 실행 spec 함수는 DF-34".
* 257행 DEC-63: follower 입력 어드미턴스 `cgd + cgb + cgs·(1 − A_buf)`, "cgs는 source 노드, cgb는 bulk 넷에 스탬프"(DF-28, U-27 CGS·CGB 열의 소비처).
* 262행 DEC-68: "개념 하나에 이름 하나·저장 위치 하나, 다른 곳은 참조(`value_from_spec` ...)로만 잇는다 ... 하네스 탐색 설정·PDK 키에 적용할지는 U-32".
* 274행 DEC-80 (i): "레이아웃 격자 분해능 = PDK 선언값(최소 finger 폭, finger pitch·overhead, 허용 L 격자 -- Phase 4의 'PDK 상수 한 곳 선언', U-30)에서 ... 계산한 값 ... 상수로 박지 않는다". 상태는 "미구현(Phase 4 PDK 선언 -> 7a ... -> 7b 소비)".
* DEC-77·DEC-79는 158행·1111행 문맥에서 참조될 뿐이고 U-27·U-30 card 범위에 직접 들어오지 않는다.

---

## 2. U-27 실측

### 2.1 도구·경로

| 항목 | 실측 | 근거 |
|---|---|---|
| ngspice | `ngspice_con.exe -v` → `ngspice-46`, KLU. 경로 `C:\ngspice\Spice64\bin\{ngspice.exe, ngspice_con.exe}` | 실행 |
| sky130 PDK 모델 | `C:\pdk\sky130_fd_pr` 있음. git `f62031a1be9aefe902d6d54cddd6f59b57627436`(2020-11-10), origin `google/skywater-pdk-libs-sky130_fd_pr`, partial clone(`blob:none`). `cells/{nfet,pfet}_01v8/*__tt.pm3.spice`·`*__mismatch.corner.spice`·`models/parameters/lod.spice` 모두 있음 | ls·git -C (읽기) |
| gf180 PDK | 없음(`C:\pdk`에 sky130_fd_pr만 있음). U-27 범위 밖이다 | ls |
| LUT 생성 스크립트 | `A/sky130_lut_sweep.py` 337행. `NGSPICE_EXE`(:71)·`PDK_ROOT`(:72)·`LOD_SPICE`(:74)가 박혀 있다. 격자는 `L_GRID_UM` 12점(:104), VGS·VDS 0~1.8 V 49점(:105~107), **`VS_GRID = [0.0, 0.2, 0.4, 0.6, 0.8]`(:108)**, `F_TEST` 100 MHz(:109), 기준폭 `w=5u`(:150) | 읽기 |
| 체크포인트 | `A/ac_sweep_checkpoints/` 120개(= 2소자 × L 12 × VS 5), 추적 중. 키 = ID·GM·GDS·CGG·CGD·SID_1F | ls·np.load |
| 표본 LUT | `sky130_nfet_pfet_lut_sample.npz` sha256 `753d802a…f177f`. 키 = L·VGS·VDS·VS·`corner`("tt")·`temp_c`(27.0)·{ID,GM,GDS,CGG,CGD,SID_1F}_{n,p}. **CGS·CGB 없음**, **SID_1F 있음**, `W_ref`·PDK 경로·ngspice 버전 없음 | np.load |
| `A/_sweep.cir` | LUT와 무관한 VCCS 장난감 넷리스트(gm·ro 소자, `ac lin 1 1k`)다. 추적 중인 잔재다 | 읽기 |

**경로가 박힌 곳(전수, `.bkit` 제외)**
* `A/sky130_lut_sweep.py:71-72` (`NGSPICE_EXE`, `PDK_ROOT`)
* `workspaces/current-reuse-telescopic-ota-report/spice/`: `stage3_full_circuit_ngspice_crosscheck.py:20`, `cmfb_cmrr_ngspice_crosscheck.py:12`, `stage2_battery_psrr_ngspice_crosscheck.py:21`, `stage1_psrr_ngspice_crosscheck.py:26`, `stage1_cmrr_ngspice_crosscheck.py:32` (`NG = r"C:\ngspice\Spice64\bin\ngspice_con.exe"`), `gen_single_device.py:67-68` (PATH 앞에 붙임)
* 계획서 499·1137행, 문서 `docs/04-report/analog-topology-json-library.do.md:1428,1447`, `.ai/context.md` 여러 곳(기록일 뿐 실행 코드 아님), `A/stick_diagram.py:6274`(주석)
* 계획이 말하는 "LUT 생성 메타"는 **아직 없다.** npz가 들고 있는 메타는 `corner`·`temp_c` 두 개뿐이다.

### 2.2 최소 재현 점검 (실행 결과)

방법: C:/g31에서 `sky130_lut_sweep.py`를 모듈로 불러왔다(수정 없이). 그 `_gen_netlist`·`_parse_output`·`_ltag`를 그대로 써서 넷리스트를 C:/g31에 쓰고, `ngspice_con.exe -b`로 돌린 뒤 체크포인트·npz와 비교했다.

| 대상 | 점 수 | 시간 | 결과 |
|---|---|---|---|
| nfet_01v8 L 0.15 VS 0.0, VGS 1.125 / VDS 0.9 (2×2 격자) | 4 | 0.7 s | 6열 모두 npz·체크포인트와 **완전 일치**(상대차 0) |
| pfet_01v8 L 0.5 VS 0.4, 같은 점 | 4 | 0.2 s | 6열 완전 일치 |
| **pfet_01v8 L 0.425 VS 0.8 전체 조합** | 2401 | **329 s** | 6열 `np.array_equal` True, 최대 절대차 0, `Error` 줄 0 |

* 결론: 도구·모델·스크립트가 현재 LUT를 **비트 단위로 재현**한다. U-27 선행 (2)는 충족이다. 선행 (3)(옛 격자점 대조)의 기대값은 "옛 5개 VS 점 × 기존 5열은 비트 동일"로 둘 수 있다. 단, 넷리스트를 바꾸면(CGS·CGB 추출용 포트 추가) 그 기대가 깨질 수 있으므로, 같은 card에서 비트 동일을 다시 측정해야 한다(lchoke 도입 때 스크립트 docstring :133~136이 같은 방식으로 확인했다).
* 최소 재현 점검의 형태(card용): "옛 격자 조합 k개(nfet·pfet 각 1개 이상, VS 끝점 포함)를 새 스크립트로 재생성해 기존 열이 비트 동일인지 확인, 새 열(CGS·CGB)은 CGS+CGD+CGB ≈ CGG 일관성 확인". 이것은 auditor가 격리 경로에서 돌린다.
* 부수 관찰: 1점 격자(`vector(1)`)로 돌리면 ngspice가 `Error: indexing a scalar`를 내고 VGS·VDS가 0으로 남는다. 그래도 `_parse_output`은 점 수만 맞으면 **그대로 통과시킨다**(ngspice `Error:` 줄을 검사하지 않는다). 실제 49×49 실행에는 해당하지 않지만, 출력 파서가 오류를 거부하지 않는다는 뜻이다(인프라 결함이라 백로그 후보. 엔진을 막지 않는다).

### 2.3 재생성 전에 고칠 결함 (U-27 card 범위)

| # | 결함 | 위치 | 영향 | 기본안 |
|---|---|---|---|---|
| G1 | 체크포인트 이름이 VS **인덱스** 기반(`f"{devcell}_{tag}_VS{iVS}.npz"`) | `sky130_lut_sweep.py:267, 275-276` | 새 VS 격자가 0.2 V 간격 연장이면 인덱스 0~4가 우연히 같은 값이라 무해하다. 하지만 0.1 V 간격이면 `VS1` = 0.1인데 체크포인트 `VS1` = 0.2라서 **다른 VS 결과를 조용히 재사용한다**. B15(L 인덱스, :84~88)와 같은 종류다 | `_ltag`처럼 값 기반 태그(`VS0p2000`), 옛 120개는 이름만 옮김(내용 동일, 해시로 확인) |
| G2 | 재사용 조건이 `"SID_1F" in d` 하나 | `:268-272` | CGS·CGB 없는 옛 체크포인트를 그대로 재사용한다. 그 뒤 조립(`run_device`)에서 새 열이 비거나 튜플 길이가 틀려 실패한다 | 필요한 열 집합 전체(`ID,GM,GDS,CGG,CGD,CGS,CGB,SID_1F`)가 있을 때만 재사용 |
| G3 | CGS·CGB 추출 경로 없음. 넷리스트에서 소스가 접지 노드 `0`(`xdut d g 0 b`, :150)이라 소스 포트 여기가 불가능하다 | `:146-150, 172-179` | 열 추가(U-27 문언)를 할 수 없다 | CGB = 벌크 여기(`vb ... ac`)에서 게이트 전류로 구한다(Y11·Y12와 같은 방식). CGS = 소스를 별도 전압원 노드로 분리해 여기. 일관성 게이트 CGS+CGD+CGB ≈ CGG. 기존 열 비트 동일을 재측정 |
| G4 | npz 메타 부족: `W_ref`(스크립트 `w=5u`), PDK 루트·커밋, 모델 파일, ngspice 버전, 스크립트 해시, `F_TEST`·`LCHOKE_*`가 없다 | `:329-333` | 엔진이 `W_ref=5e-6`을 따로 박아야 한다(`workspaces/run_harness.py:65` 외 **43개 파일**: 하네스, `tests/unit/test_selftest_sizing_recipe.py`, `tests/tools/regression_runner.py`, probe 28개, workspaces 스크립트, `.ai/verification` 1개). 계획 499행의 "모델 경로는 LUT 생성 메타에서 읽는다"도 현재는 불가능하다 | npz에 `w_ref_m`, `pdk_root`, `pdk_commit`, `model_files`, `ngspice_version`, `sweep_script_sha256`, `f_test_hz`, `vs_semantics="VSB, source=0"`을 기록한다. 하네스 `_W_REF`는 npz에서 읽는다(DEC-68 저장 위치 하나) |
| G5 | `VS_GRID` 상수가 박혀 있다 | `:108` | LR3(507행)은 상한을 `supplies_v` 최대 전위차에서 유도해 "LUT 생성 체크리스트 입력"으로 두라고 한다 | 상한 = library 회로 `supplies_v` 최대 차(현재 1.8 V)를 계산해 스크립트 인자로 받는다. 간격은 기존 선언 0.2 V 유지(§4 참고) |
| G6 | 출력 경로가 저장소 assets 안(`OUTPUT_DIR` = 스크립트 폴더, 체크포인트·npz 덮어쓰기) | `:73, 75, 323` | card 실행 중 저장소 직접 쓰기 | code worktree 안에서 실행하거나 `--out` 인자로 받는다 |

**실행 비용**: 조합 1개 = 329 s(실측, noise 포함). 옛 docstring의 "40조합 55분"(≈82 s/조합)은 noise 추가 전 수치라 낡았다. CGS·CGB 열이 새로 생기면 **옛 체크포인트 120개도 전부 다시 돌려야 한다**.
* VS 0~1.8 V, 0.2 간격(10점): 2 × 12 × 10 = 240조합 × ≈330 s ≈ **22시간**(직렬, 추가 AC 해석 2회 몫 제외).
* 0.1 간격(19점): 456조합 ≈ **42시간**.
* 조합끼리는 서로 독립인 프로세스라 병렬화할 수 있다. 다만 현재 스크립트는 직렬이고, 병렬화는 도구 변경이다. 실행은 `run_in_background`로 하고 조합마다 체크포인트를 남긴다(memory: 결과는 파일에).

### 2.4 문서·코드의 낡은 문장 (U-27 card에서 한 줄씩 정정)

* 계획 158행 "현재 LUT에 없어 `noise_1f_density()`가 호출 즉시 거부한다": 틀렸다. 하네스가 `SID_1F=_d["SID_1F_n"]`를 넘기고(`run_harness.py:67,69`), npz에 열이 있다.
* `sizing_recipe.py:660-662` `noise_1f_density` docstring("`sky130_nfet_pfet_lut_sample.npz` 전부 해당 -- 아직 `.noise` 해석을 포함한 재스윕이 안 됨"): 낡았다.
* `sizing_recipe.py:4789-4791` `lut_conditions_from_npz` docstring("저장소의 `sky130_nfet_pfet_lut_sample.npz`에는 기록이 없다"): 낡았다. 현재 npz에는 `corner`·`temp_c`가 있다.
* `references/lut-generation-checklist.md` §8.1 표 `SID_1F` 행 "⏳ 배치 7-3g 구현 대기": 낡았다. CGS·CGB 행 자체가 없다(§2 골격 `.probe`에는 CGS·CGB가 있다).
* U-27 문언 "SID_1F 열 추가"는 "새 VS 축으로 함께 재스윕"으로 읽는다(prep_phase4_scope §5.2와 같다).

### 2.5 U-27 선행 조건별 상태

| 선행 | 상태 |
|---|---|
| (1) DF-27 red(옛 LUT에서 VS 축 밖 거부) | 미착수. test-author 몫이다. 옛 LUT VS 상한 0.8 V를 넘는 픽스처(예: vsb 0.9 V)를 쓴다 |
| (2) 도구·ngspice·모델 경로 | **충족**(§2.1·§2.2). 이 문서가 읽기 전용 실측 기록이다. card에서는 auditor가 판정 기록으로 다시 잰다 |
| (3) 옛 격자점 대조 | 방법 확정(비트 동일 기대, §2.2). G3 넷리스트 변경 뒤 재측정 필요 |
| (4) 새 LUT 해시 → S0·실패 캐시 지문 | 옛 해시 `753d802a…f177f` 기록. **현재 `spec_fingerprint`(`sizing_recipe.py:7590-7596`)는 LUT를 지문에 넣지 않는다**(:7600 "LUT 객체는 `id()`가 매번 달라 지문에 넣지 않는다"). 새 LUT 해시를 지문에 넣는 경로는 I-A5(6a, S0 배선)·DF-13(LUT 내용 지문)과 겹친다. U-27 card에서는 "지문이 바뀜을 기록"만 하고, 배선은 DF-13 card로 넘긴다 |

---

## 3. U-30 실측

### 3.1 하네스 사본 (`workspaces/run_harness.py`, HEAD)

| 키 | 단위 | two_stage `_spec_two_stage_ota`(:72) | current_reuse (:132) | folded (:212) | nmcnr (:249) | PDK 출처 | 엔진 소비 |
|---|---|---|---|---|---|---|---|
| `min_finger_w` | m | **:121 `0.1e-6`** | :186 `1e-6` | :243 `1e-6` | :301 `1e-6` | difftap.2 = 0.420 µm (U-30 닫힘) | `sizing_recipe.py:9273` 한 곳 → `assign_finger_geometry` |
| `max_finger_w` | m | :122 `40e-6` | :187 | :244 | :302 (모두 `40e-6`) | **DRC 근거 없음**(탐색·레이아웃 선택. 모델 bin W 상한 7.0 µm보다 크다) | 같은 곳 |
| `W_bounds` | m | :117 `(1e-6, 200e-6)` | :172 | :241 | :297 (모두 같음) | 하한 = `min_finger_w`에서 유도(U-30). 상한 200 µm은 근거 없음(탐색 설정) | 11곳(§3.2) + `spec_fingerprint` 키(:7590-7592) |
| `L_min` | m | :115 `0.15e-6` | :170 | :239 | :295 | poly.1a 0.150 µm | **엔진 읽기 0**(`sizing_recipe.py:9115` docstring뿐) |
| `L_min_by_kind` | m | :116 `{nmos,pmos: 0.15e-6}` | :171 | :240 | :296 | poly.1a (pfet_01v8은 lvtn이 아니므로 poly.1b 0.35는 해당 없음) | **엔진 읽기 0**(:8509 오류 문구뿐) |
| `L_GRID_STEP` → spec `L_grid_step` | m | 모듈 상수 :51 `0.005e-6`(sky130hs.tlef MANUFACTURINGGRID, 주석 :47-50). spec :107·:157·:236·:292 참조 | | | | 제조 그리드 | `sizing_recipe.py:9196, 10188, 10921-10930` 외, `spec_fingerprint` 키 |
| `vth0_slope` | V·µm | :123 `{nfet 3.356e-3, pfet 5.856e-3}` | :188 | :245 | :303 (모두 같음) | `C:\pdk\...\nfet_01v8__mismatch.corner.spice:20` `3.356e-03`, `pfet ...:26` `5.856e-03`(실측 일치) | `sizing_recipe.py:3087, 6806` |
| `_W_REF` | m | 모듈 상수 :65 `5e-6` | | | | LUT 생성 기준폭(`sky130_lut_sweep.py:150` `w=5u`). LUT 메타(U-27 G4) | `SemiEmpiricalGmIdLUT(W_ref=)` :67·:69 |
| (참고) `vdd` | V | :105 `1.8` | :142 | :234 | :288 | MG1 몫, U-30 아님 | -- |

`L_candidates`는 4회로 모두 `layout_grid_L_candidates(_NMOS, L_GRID_STEP, n=41)`이고 `L_min` 인자를 넘기지 않는다. 그래서 L 하한은 `sizing_recipe.py:812` `lo = float(lut.L_grid[0])`, 곧 LUT 축 0.15e-6이다. **spec `L_min`을 바꿔도 동작은 바뀌지 않는다.**

### 3.2 엔진 쪽 두 번째 정본 (폴백 기본값)

**`sizing_recipe.py` `W_bounds` 폴백 `(1e-6, 200e-6)` 11곳**
| 줄 | 함수 |
|---|---|
| 1626 | `lut_vdsat_headroom` |
| 1988 | `search_gm_id_for_role` 기본 인자 |
| 2697 | `derive_role_L` |
| 2748 | `derive_class_L` |
| 3623 | `apply_diode_self_consistent_gm_id` |
| 5763 | `_make_shared_current_scorer` |
| 6055 | `_feed_metric_stage_budget` |
| 6731 | `make_replica_feasibility_check` |
| 7266 | `_hr_resolve_vertical_group` 안 `_stack_min_vds` |
| 7462 | `_hr_resolve_vertical_group` 안 `_stack_min_vds`(두 번째) |
| 8716 | `_build_theta_evaluator` 안 `_evaluate` |

`W_bounds`를 인자로 받아 쓰는 곳은 `_idu_scan` 필터(1579-1589), `feasible_L_window`(2534·2574), `diode_vds_window`(3403·3449 캐시 키·3467·3480), `solve_stacked_diode_pair`(3493·3547·3568)다.

**`min_finger_w`/`max_finger_w` 폴백 (단위 섞임)**
| 위치 | 값 | 단위 | 운영 도달 |
|---|---|---|---|
| `sizing_recipe.py:9273` `spec.get("min_finger_w", 1e-6)`, `spec.get("max_finger_w", 40e-6)` | 1e-6 / 40e-6 | m | 도달하지만 하네스가 늘 선언하므로 폴백은 쓰이지 않는다 |
| `stick_diagram.py:5954` `search_stack_finger_w(min_finger_w=1.0, max_finger_w=40.0)` | 1.0 / 40.0 | **µm** | 운영 호출은 늘 명시 인자(6100·6104·6107)라 기본값은 안 쓰인다 |
| `stick_diagram.py:6043` `assign_finger_geometry(min_finger_w=1.0, max_finger_w=40.0)` | 1.0 / 40.0 | **µm** | 운영 호출(`sizing_recipe.py:9271`)은 명시 인자(m) |
| `stick_diagram.py:6204` `search_shared_finger_w(min_finger_w=0.4, max_finger_w=45.0)` | 0.4 / 45.0 | **µm** | **엔진 호출 0**. `workspaces/current-reuse-telescopic-ota-report/stick.py:34,53,73,112`(µm 명시값)만 부른다 |
| `stick_diagram.py:6272-6280` `PROCESS_GEOMETRY["finger_pitch_overhead_m"] = 0.0` | 0.0 | m | I-A12(7b). DEC-80 (i)의 입력이라 선언 자리는 U-30과 같은 곳에 둔다(값은 미확보, `null` + 사유) |

docstring은 `devices: {device_name: W_um}`(stick_diagram :5971·:6221)인데 운영은 m를 넘긴다. **단위 계약이 문서와 코드에서 서로 다르다.**

### 3.3 모든 소비자 (분류)

| 분류 | 파일 | 키 |
|---|---|---|
| 운영 정본 | `workspaces/run_harness.py` | 위 §3.1 전부 |
| 엔진 | `A/sizing_recipe.py` | `W_bounds` 11 + 인자 경로, `min/max_finger_w` 9273, `vth0_slope` 3087·6806, `L_grid_step` 9196·10188·10921·10930, 지문 7590 |
| 엔진 | `A/stick_diagram.py` | 5954·6043·6204 기본값, 6011·6244 비교, 6126 오류 문구 |
| test (test-author 소유, 픽스처) | `tests/unit/test_selftest_sizing_recipe.py` | `min_finger_w` **0.1e-6** :414·:1026, 1e-6 :1252. `L_min` 0.18e-6 :402, 0.1e-6 :1034, 0.15e-6 여러 곳, 0.5e-6 :2289. `W_bounds` :2248 외 |
| test | `tests/unit/test_selftest_stick_diagram.py:2594-2595` | `assign_finger_geometry(..., min_finger_w=1e-6, max_finger_w=40e-6)`(m 명시) |
| test | `tests/contracts/test_restore_plan_functions.py:277-329` | 합성 dict의 `L_min`(동작 무관) |
| probe | `tests/probes/probe_l5c_stage2out_L.py:81-84` 외 probe 다수 | 하네스 복사본 |
| 1회성 workspaces | `two-stage-ota-report/*.py`, `current-reuse-telescopic-ota-report/*.py`(smoke·diagnose·stick.py) | 하네스 복사본(`L_min` 0.15e-6 등) |
| topology 주석 | `library/current_reuse_telescopic_ota.topology.json:1071,1079,1155,1163,1309` | "L_min x2.5 = 0.375um" 문구(옛 배수 규칙 설명, 동작 무관) |

### 3.4 선언 위치 제안

* 계획 근거: 794행 저장 위치 = "공정 기록 한 곳(LUT 생성 메타와 연결)", 499행 "모델 경로는 LUT 생성 메타에서 읽는다", DEC-80 (i) "PDK 선언값에서 계산", DEC-68 "저장 위치 하나, 다른 곳은 참조", DEC-62(`SPECS`는 데이터 항목), DF-34(7b에서 `_spec_*()` 삭제).
* `sizing_spec.json`은 회로마다 있는 파일이고 7b에 생긴다. PDK 상수는 회로와 무관하므로 **기각**한다(4벌 복사가 그대로 남는다).
* LUT npz에 직접 넣는 방안도 **기각**한다. DRC 규칙(difftap.2 등)은 스윕 결과가 아니고, npz는 재생성 산출물이라 규칙값이 스윕 스크립트 상수가 된다(checklist §8이 "두 가지 서로 다른 출처를 구분한다"고 명시한 것과 반대).
* **기본안: 공정 기록 JSON 한 개 + LUT 메타에서 해시로 연결**
  * 파일: `A/pdk/sky130_fd_pr.process.json`(이름은 card에서 test glob 충돌 grep).
  * 필드(값은 SI m, 키 접미사는 U-32 기본안대로 적용하지 않음):
    * `min_finger_w` = 0.42e-6 {rule: "difftap.2", source: "google/skywater-pdk docs/rules/periphery/periphery.csv"}
    * `l_min` = 0.15e-6 {rule: "poly.1a"}
    * `l_grid_step` = 0.005e-6 {source: "sky130hs.tlef MANUFACTURINGGRID"}
    * `vth0_slope` = {nmos, pmos}. `mismatch.corner.spice` 파일·param 이름을 출처로 적는다. 값은 파일에서 읽어 캐시하는 것이 원칙(memory: 근거 하나 남기고 계산+캐시)이고, 모델 경로는 LUT 메타 `pdk_root`에서 온다.
    * `finger_pitch_overhead_m` = null {I-A12, 미확보}
    * `passive_unit_area` = null {U-36 자리, 7b 전}
  * 유도값: `W_bounds[0]` = `min_finger_w`(finger 1개 소자의 최소 W). 함수 하나로 계산하고 캐시한다.
  * 로더: MOD1(`gmid_lut.py`, 계획 521행 MOD1이 `lut_conditions_from_npz`를 가짐 = 공정·LUT 메타 계층). MOD4·MOD7 양쪽이 쓰므로 가장 낮은 계층이다.
  * 연결: U-27 npz에 `process_record_sha256`를 기록한다. 로더가 두 해시가 어긋나면 거부한다.
  * 하네스: `SPECS` 4벌의 `min_finger_w`·`W_bounds` 하한·`L_min*`·`vth0_slope`·`L_GRID_STEP`·`_W_REF` 복사를 지우고 로더 값을 참조한다(DF-34 Phase 4 몫).
  * 엔진: §3.2 폴백 15곳을 지우고, 선언이 없으면 구조화 실패로 처리한다(조용한 기본값 금지).
  * stick_diagram: µm 기본 인자를 지우고 m로 단위 계약을 통일한다(docstring `W_um` 정정).
* `max_finger_w` 40 µm·`W_bounds` 상한 200 µm·`stage_w_max`는 **PDK 규칙이 아니다.** 공정 기록에 넣지 않고 하네스 탐색 설정 공통 한 곳(4벌 → 1곳, `SPECS` 공통 데이터)으로 옮긴다. 값은 바꾸지 않는다.
* `L_min`·`L_min_by_kind`(죽은 키) 처리: 선언(`l_min`)은 두고 **배선**한다. `layout_grid_L_candidates(..., L_min=)`에 `max(l_min, lut.L_grid[0])`를 넘기고, `l_min`이 LUT 축 밖이면 LR3 거부. 현재 두 값이 모두 0.15e-6이라 동작 변화 0이다(만들면 배선). 하네스의 두 죽은 키는 삭제한다.

### 3.5 동작 보존 비교 목록 (무거운 계산 없이 식별만)

| 변경 | 영향 단계 | 영향 회로 | 예상 |
|---|---|---|---|
| C1 two_stage `min_finger_w` 0.1e-6 → 0.42e-6 | 레이아웃(`assign_finger_geometry` → finger 배정·행 기하·floorplan·`audit_ok`·하네스 row_split 루프·instance.json·보고) | two_stage | [0.1, 0.42) µm finger 후보가 사라진다. 옛 PROVISIONAL instance(`two_stage_ota.PROVISIONAL_gain51.instance.json`)의 최소 finger_w는 0.997 µm(M3·M4)라 그 스냅샷 기준으로는 변화가 없다. 다만 현 HEAD에서 two_stage가 레이아웃 단계에 도달하는지는 I-C11 해소 전에는 불확실하다(prep_b26 §2.4: 중앙점 θ에서 InfeasibleSizingError) |
| C2 나머지 세 회로 `min_finger_w` 1e-6 → 0.42e-6 | 레이아웃 | current_reuse, folded, nmcnr | 하한을 완화하면 작은 finger_w 후보가 추가된다. seed stack은 가장 큰 fw를 먼저 고르므로 대개 그대로지만, 비 seed stack의 target 맞춤·완화 경로가 달라질 수 있다. 실측 instance에서 finger_w가 1 µm 하한 근처인 소자: folded M3·M4(1.017 µm, 1 finger, auditor base `df36/einst/base_folded_cascode.instance.json`), nmcnr M202(1.02 µm, 옛 workspaces 스냅샷), folded 옛 스냅샷 12개(1.01~1.08 µm) → **바뀔 가능성이 높다** |
| C3 `W_bounds` 하한 1e-6 → 0.42e-6(유도) | **사이징 전체**(§3.2의 11곳 + 인자 경로), `spec_fingerprint` 변경 → 실패 캐시·민감도 캐시 키(`sizing_recipe.py:7683, 7755-7761`) 변경 | **4회로 전부** | W 하한이 걸려 있던 소자(folded M3·M4 1.017 µm, nmcnr M202 1.02 µm)는 gm_id·L 창이 넓어져 θ*·W·전력이 바뀔 수 있다. current_reuse는 최소 W 1.22 µm라 직접 하한에 걸린 소자는 없지만, `feasible_L_window`·diode 창이 하한 W에 의존하므로(2574, 3467) 변화 0을 가정할 수 없다 → 전후 비교 필수, 바뀌면 DEC-40 |
| C4 엔진 폴백 15곳 삭제 | 선언이 없는 호출 | 운영 4회로는 늘 선언 → 변화 0 | test·probe 중 `W_bounds`/`min_finger_w`를 생략한 픽스처가 구조화 실패로 바뀐다. card 전 실측으로 전수를 확인해야 한다(생략 픽스처 목록). 테스트 쪽 대응은 test-author 몫 |
| C5 `L_min` 배선(`max(l_min, L_grid[0])`) | L 후보 | 4회로 | 0.15e-6 = 0.15e-6이라 변화 0(무동작임을 측정으로 보인다) |
| C6 `vth0_slope`를 PDK 파일에서 읽기 | mismatch metric | 4회로 | 값이 같아서(3.356e-3/5.856e-3 실측 일치) 변화 0. 파싱 결과를 비트 동일로 확인 |
| C7 `_W_REF`·`L_GRID_STEP`을 메타·기록에서 읽기 | LUT 스케일링, L 스냅 | 4회로 | 값이 같아서 변화 0 |
| C8 stick_diagram µm 기본값 삭제·단위 m 통일 | 기본값에 기대는 호출만 | 엔진 운영 0 | workspaces `stick.py`(µm 명시)는 1회성 스크립트라 범위 밖(기록만). test `test_s113`은 m 명시라 무영향 |
| 픽스처 `min_finger_w` 0.1e-6(test :414·:1026) | self-test | -- | 픽스처(origin: fixture, U-04)라 **바꾸지 않는 것이 기본**이다. 공정 기록을 참조하게 할지는 test-author 판단 |

* 비교 순서 제안: C5·C6·C7(무동작 증명) → C4 → C1·C2(레이아웃만) → C3(사이징) 순서로 **별도 커밋이나 측정 단계로 나눈다.** 그래야 전후 비교표에서 변화 원인을 가를 수 있다. C3은 DoD의 "사이징 대상 회로 비교표"가 요구하는 핵심 항목이다.
* 비교 기준: 하네스 정본 실행 θ*(prep_phase4_scope §6). two_stage·nmcnr는 I-C11 해소 전 비교 범위를 design에 미리 적는다.

---

## 4. 결정 분류

### 4.1 사용자 결정 (진짜 사용자 몫)

| # | 결정 | 이유 | 기본 제안 |
|---|---|---|---|
| UD-a | **DEC-40 기준선 변경 승인 — U-30 C3(`W_bounds` 하한 유도)** 으로 바뀌는 4회로 θ*·기대값, C1·C2로 바뀌는 finger 배정·floorplan | 기준 변경은 매 건 사용자 승인(DEC-40, 1019행) | 비교표를 auditor 판정 기록으로 제시한 뒤 건별 승인 |
| UD-b | **DEC-40 — U-27 새 LUT**: 옛 격자점이 비트 동일이 아니게 되면(넷리스트 G3 변경 탓) 그 차이와 이로 바뀌는 기준선 | 1102·1141행 | 기존 열 비트 동일이 목표. 다르면 원인 보고 후 승인 |
| UD-c | (정보 확인, 선택) `max_finger_w` 40 µm가 로컬 모델 bin W 상한 7.0 µm(`nfet/pfet_01v8.bins.csv`)보다 크다 | 계획 어디에도 없는 사실이다. 모델 유효 범위 밖 finger를 허용하는지는 회로·공정 판단이다 | 이번 U-30에서는 값을 바꾸지 않는다. 사실만 보고하고 결정은 사용자가 원할 때(7a SPICE 대조에서 모델 오차로 드러날 수 있음) |

**`min_finger_w`의 올바른 값은 사용자 결정이 아니다.** 계획 U-30이 이미 닫았다(difftap.2 = 0.420 µm, two_stage 0.1 µm는 오류, 나머지 1 µm는 근거 없음). nfet bin 0.36 µm·difftap.2b 0.36 µm는 표준셀 안 규칙이거나 모델 범위라서 채택하지 않는다(계획 문언). 사용자 몫은 그 교체로 바뀌는 **결과의 승인(UD-a)** 뿐이다.

### 4.2 원칙에서 정해지는 기본안 (묻지 않는다, design에 근거와 함께 적는다)

* PDK 값: difftap.2 0.42e-6, poly.1a 0.15e-6, 제조 그리드 0.005e-6, vth0_slope는 PDK 파일에서 읽기. 모두 계획·checklist §8.2 출처가 있다.
* 선언 위치: 공정 기록 JSON + MOD1 로더 + npz 해시 연결(§3.4). `sizing_spec.json`과 npz 직접 저장은 기각.
* `W_bounds` 하한 = `min_finger_w`(유도 함수 하나, 캐시). 상한·`max_finger_w`·`stage_w_max`는 탐색 설정이라 하네스 공통 한 곳에 두고 값은 유지.
* 엔진 폴백 15곳 삭제 + 구조화 실패(조용한 기본값 금지, 개념 하나에 저장 위치 하나).
* 단위: m 하나로 통일(stick_diagram µm 기본값·docstring 정정).
* `L_min` 선언은 배선하고(`max(l_min, L_grid[0])`, 무동작 증명), 하네스 죽은 키는 삭제.
* 키 이름 접미사: U-32 기본안(적용 안 함)대로 둔다. 7b에서 확정.
* U-36 수동소자 단위 면적·I-A12 `finger_pitch_overhead_m`은 자리만 두고 `null` + 사유(7b 전).
* U-27 VS 격자: 상한은 `supplies_v` 최대 차에서 유도(1.8 V). **간격은 기존 선언 0.2 V 유지**(새 상수를 만들지 않고, 옛 5점이 부분집합이 되어 비트 대조가 가능하다. 240조합 ≈ 22시간). checklist §1은 0.1 V를 권장하지만(456조합 ≈ 42시간) 그 근거는 body effect 해상도 일반론이다. 0.2 V 간격이 보간 오차 문제를 낸다는 실측이 생기면 그때 늘린다(백로그).
* U-27 CGS·CGB: 벌크·소스 여기 Y-파라미터로 직접 추출하고, CGS+CGD+CGB ≈ CGG 일관성 게이트를 둔다. 기존 열 비트 동일을 재측정한다.
* U-27 스크립트 결함 G1~G6은 같은 card에서 고친다(재생성의 정합성 조건이다). `_parse_output`의 `Error:` 미검사는 인프라 백로그로 둔다(엔진을 막지 않는다, memory: 인프라 작업은 gmid 엔진을 막을 때만).
* 실행: code worktree 안, `run_in_background`, 조합마다 체크포인트. 병렬화는 필요할 때 따로 판단.
* 낡은 문장 정정(§2.4): 계획 158행, `sizing_recipe.py:660-662`·`:4789-4791` docstring, checklist §8.1. 계획 정정은 오케스트레이터 몫이고 경위는 history로.
* 순서: DF-27 red(옛 LUT) → U-27(G1~G6 수정·재생성·대조) → U-30. U-30의 C3 비교가 새 LUT 위에서 한 번만 일어나도록 U-27 뒤에 둔다. 반대로 하면 기준선 승인이 두 번 필요하다.

### 4.3 착수 전에 할 실측 (card 작성 직전, 읽기 전용)

* C4 대상: `W_bounds`·`min_finger_w`를 생략한 test·probe 픽스처 전수(AST로 `spec` dict 리터럴 키 검사).
* 공정 기록 파일 이름·경로가 test glob과 충돌하지 않는지 grep.
* `spec_fingerprint`를 쓰는 캐시 목록(7683, 7755-7761 외)과 C3로 무효화되는 저장 캐시 유무.
* 현 HEAD 하네스 θ*에서 4회로 중 레이아웃 단계에 도달하는 회로(C1·C2 비교 가능 범위, I-C11과 연동).
