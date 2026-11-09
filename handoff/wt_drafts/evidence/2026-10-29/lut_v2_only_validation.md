# LUT v2 단일화(O-180) 독립 검증 -- data/lut-v2-only

- 검증자: 독립 검증 agent(작성자 아님), 2026-10-29~30
- 대상: 브랜치 `data/lut-v2-only` 6c2d9a0e (b1c79487·3ca357a6·de265d22·dc63431c·2201f87d·6c2d9a0e), base 4a0b6323
- 실행 장소: 격리 복제본 `C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/lutV/repo`(core.longpaths), 그 안 worktree `base`(4a0b6323)·`mut`(6c2d9a0e 변이용). 대상 worktree 쓰기 0.
- 출력 파일 폴더(아래 `<S>`): `C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/lutV/`

## 판정: 조건부 병합 가능 (Major 1건은 병합 전 수정 권고, 나머지 Minor)

## Major

**M-1 재발 방지 test가 옛 오용 꼴 3개 중 1개만 막는다.** `test_lut_single_source.py`의 이름 정규식은 `sky130*lut*.npz` 파일 이름만 잡는다. 이번에 지운 오용 세 곳 가운데 둘은 그 꼴이 아니었다: conftest `_OLD_MANIFEST`·test_run `REAL_MANIFEST` = `wt/_drafts/engine/lut_slices/manifest.json`, `_NOCOL_MANIFEST` = `wt/_drafts/engine/lut_v2/manifest.json`(경로 리터럴).
- 변이 실측(`<S>mut_single_source.txt`): `mut` worktree에 추적 .py 4개를 넣었다(`git add -N`). (m2) r1 이름 `sky130_nfet_pfet_lut_v2.npz` → 거부함. (m3) `os.environ.get("GMID_LUT_CAP_NPZ")` → 거부함. **(m1) `_drafts\engine\lut_slices\manifest.json`·`_drafts\engine\lut_v2\manifest.json` 경로 리터럴 → 통과(거부 안 함).** **(m4) `np.load(".../_drafts/engine/lut_v2/sky130_fd_pr__nfet_01v8__tt__W5p0000um_dc.npz")` → 통과(거부 안 함).**
- 그 경로의 데이터는 디스크에 그대로 남아 있다. `wt/_drafts/engine/lut_slices`(39 파일, 283 MB)와 `wt/_drafts/engine/lut_v2`(46 파일, 547 MB)이다. 후자에는 **r1 원본 `sky130_nfet_pfet_lut_v2.npz`(sha256 337bd058…, 옛 test가 고정했던 그 파일)**과 `..._verify_midpoints.npz`(d243f380…)도 들어 있다. 그래서 O-180 기록의 "r1 두 파일 git 밖 복구 불가" 문장은 사실과 다르다(사본이 있음).
- 권고: (a) guard 확장 -- 추적 .py 문자열 리터럴 가운데 `manifest.json` 또는 `*.npz`로 끝나는 절대 경로나 `_drafts`·`lut_slices`·`lut_v2/` 조각을 가진 경로가 위치 선언 밖이면 실패. 변이 m1·m4를 거부 확인 test로 넣는다. (b) `_drafts/engine/lut_slices`·`_drafts/engine/lut_v2` 삭제 여부는 사용자 결정이다. O-180 "다른 lut는 지워"의 문언에는 해당하지만 결정 행의 '지움' 목록에는 없다. 지우면 경로가 남아도 fail-closed가 된다.

## Minor

- m-1 범위 밖 삭제 2건: `legacy/workspaces/current-reuse-telescopic-ota-report/build_html.py`·`build_report.py`는 sample LUT를 **읽지 않는다**(보고서 문자열에 파일 이름만 있음, base 165행·230행). O-180은 "legacy 코드 본문은 남기되 sample 경로 언급 삭제"이므로 문언상 수정 대상이지 삭제 대상이 아니다. 원칙 33(legacy 폐기 허용)으로 실제 피해는 없다. "원래 취지와 다름"으로 보고할 것.
- m-2 workspace 스크립트 13개(resize·diagnose_*·check_box_shape*·smoke_*·sample_metrics·theta_sensitivity·run_harness_smoke)는 sample을 `np.load`로 직접 읽었다. 이것은 "test·probe"가 아니라 workspace 분석 스크립트다. 삭제는 타당하지만 승인 문구("legacy test·probe")보다 넓으니 보고에 명시할 것.
- m-3 `legacy/tests/contracts/test_ts6_dead_probes.py::test_dead_probe_files_are_absent` 통삭제: probe 수(42−3−승격)는 probe 삭제로 틀어진다. 그래도 DF-21 세 경로 부재 단언(`assert_paths_absent`)은 여전히 유효했는데 함께 사라졌다. 기준 약화이고 legacy라 영향은 없다. 사용자에게 알릴 것.
- m-4 `gmid_engine/lut/CONTRACT.md` 1.8 마지막 항목(276~277행)은 아직 "test 기본 경로 전환(아직 안 함) … `GMID_LUT_MANIFEST`·`GMID_LUT_CAP_NPZ` 환경 덮어쓰기는 유지 가능"이라고 적혀 있다. O-180과 충돌하는 낡은 문언이다(guard는 .py만 본다). 252행 r1 중점 파일 이름은 실측 기록이라 둘 수 있다.
- m-5 `tests/lut/conftest.py` 1284행에 `# --- 결정 B 이전 v2 슬라이스 …` 머리줄이 남았다(아래 fixture 0개). `assets/sky130_lut_sweep.py` 571행 `existing =sorted(` 띄어쓰기도 있다. 둘 다 표면 문제.
- m-6 `tools/spice_oracle/legacy_adapter.py`는 두 모드가 모두 사용 불가가 됐다. 새 실행은 run_harness import RuntimeError이다. `--from-dump`는 dump의 `lut_path`(sample) 파일이 없어 SystemExit이다. 소비자는 지운 C12 test뿐이었고 engine 소비자는 0(grep)이라 fail-closed로 타당하다. 다만 adapter 삭제·유지 여부를 보고에 적을 것.
- m-7 저장소 밖: gmid-light faa3b43이 sample npz만 지웠다. 추적 .py 48개가 아직 sample 경로를 참조한다(`git -C gmid-light grep -l lut_sample -- '*.py'`). gmid-light가 살아 있는 저장소면 같은 오용의 원천이다. 이 브랜치 범위 밖이다.

## 검사별 결과

(1) O-180 범위. 삭제 57 / 수정 26 / 추가 1. 삭제 전수 분류(base 내용 grep, `lut_sample|real_lut|run_harness|LUTFILE|sky130_regression_reference|_library_sized_contexts`):
- 데이터 1: sample npz
- 골든 JSON 1: `sky130_regression_reference.json`(`lut_file` = sample)
- legacy contract test 3: df35·restore_plan·ts6_probe_relocate(534행 sample is_file 단언)
- probe 31: 전부 sample 직접 또는 run_harness 경유
- tools 1: derive_achievable_bounds(run_harness)
- unit 7: `_library_sized_contexts`(run_harness) 및 그 소비자 6
- workspace 스크립트 15: 13개는 sample을 읽음, 2개는 읽지 않음(m-1)

엔진 코드(`gmid_engine/` 비 test) 삭제·수정 0. legacy 코드 본문 수정은 `sizing_recipe.py` docstring 2곳과 `run_harness.py`(LUTFILE=None + raise)뿐이다. 이력 문서는 CONTRACT·worked-example·checklist·SMOKE_REPORT의 sample 언급을 '삭제됨 -- 기록'으로 바꿨고 지운 것은 없다. 남긴 LUT는 `lut_v2_location.json` 선언 5파일(manifest·r2 cap·r2 중점·noise r1·mismatch r1)이다. `lut_data/sky130_lut_v2`에 r1 두 파일은 없다. 단 _drafts 사본이 있다(M-1).

(2) 재배선. `test_run.py`·`tests/lut/conftest.py`·`test_legacy_adapter.py`·`sky130_lut_sweep.py candidates`는 모두 `resolve_lut_location(assets/lut_v2_location.json, os.environ)` 하나만 쓴다. 남은 `GMID_LUT_*` 이름은 선언 env(V2_ROOT·TABLE_CACHE_DIR)와 GENERATOR_DIR(생성기 폴더, LUT 아님)뿐이다. 남은 test의 assert·기대값·skip은 바뀐 것 0이다(diff 전수: 바뀐 줄은 경로 해석뿐, `_need(None, …)`도 없으면 FAIL 유지). 삭제된 test는 옛 12-L·nocol·r1 대조 9개, C12 legacy_slow 5개, legacy s004·s014·s157이다. 모두 지운 LUT/하네스에 묶여 있었다. 지운 real-data 경로(cap_table 출처·cgg_minus_cgd_at_gs·slice_id_match)는 toy test가 계속 덮는다(test__helpers_columns 10건 등). 생성기 기본 해석을 실측했다(`<S>sweep_default_check.txt`): r2 npz, L 18개.

(3) 재발 방지 test 거부 능력.
- base(4a0b6323 + 새 test 파일): 3 failed / 2 passed(`<S>base_single_source.txt`). 실패 = 추적 sample npz 1, 이름 참조(sweep·test_run·conftest 등), env 덮어쓰기(MANIFEST·CAP_NPZ…). 통과 2는 sha256 거부·정규식 자기확인이다(base에서도 통과하는 게 맞음).
- head: 5 passed(전체 run 안).
- GMID_LUT_V2_ROOT 실측(`<S>root_env_check.txt`): 실제 r1 cap(337bd058…)을 r2 이름으로 바꾸고 나머지는 진짜 파일로 채운 루트를 env로 주면 `lut_location_sha256_mismatch`(item cap_npz)로 거부한다.
- 변이 결과는 M-1 참조.

(4) test 실행(독립):
- `gmid_engine/tests/lut/` + `test_legacy_adapter.py`(head, 복제본): 1045 passed, 25 failed(`<S>head_lut_adapter.txt`). 25건 전부 `test_legacy_adapter.py`의 FileNotFoundError이고 원인은 scratchpad 경로 길이(MAX_PATH)다.
- 짧은 경로 worktree에서 다시 돌렸다(`<S>head_adapter_short.txt`): head 25 passed. base는 `-m "not legacy_slow"`로 25 passed, 5 deselected(`<S>base_adapter_short.txt`). 결과는 같고 지운 5건 = C12 slow이다.
- 따라서 tests/lut 1045 passed + adapter 25 passed = **1070 passed, 실패 0**.
- `layout/test_run.py -k m3a_regression_real_lut`: 1 passed, 78.7 s(`<S>head_layout_m3a.txt`).
- 작성자 보고 1088과 18 차이가 난다. 작성자 측정 묶음이 무엇인지 커밋에 적혀 있지 않아 대조하지 못했다. 이 차이는 판정 근거가 아니며 내 측정이 정본이다.

(5) run_harness RuntimeError. 남은 실행 소비자는 `tools/spice_oracle/legacy_adapter.py:81` 하나뿐이다(새 실행 모드, m-6). legacy contract test·tools/gates는 run_harness.py를 AST·경로로만 읽어 import하지 않는다. 지운 모듈 이름의 남은 참조는 주석·docstring뿐이다(`check_box_shape`는 같은 이름의 함수). `gmid_engine/`와 oracle test가 깨지는 곳은 0이다(위 실행). import 시 즉시 실패시키는 것은 원칙 10(fail-closed)에 맞는다. LUT 없이 조용히 돌지 않는다. 원칙 9 관점에서는 대체 경로(새 엔진)가 이미 있다. legacy 하네스를 v2로 재배선하지 않은 것은 원칙 33(legacy 폐기 허용)에 맞는다. legacy test 묶음은 base·head 모두 수집 단계에서 conftest 계획서 표 파싱 오류로 실패한다(exit 4, `<S>legacy_collect_{base,repo}.txt`). 이미 있던 결함이라 이번 변경의 영향을 pytest로는 잴 수 없다. 정적 grep으로 대신했다.

(6) 남은 이름 참조(이력 .ai/docs/wt 제외):
- `lut/CONTRACT.md:252`(r1 중점 이름, 실측 기록)·`:276-277`(m-4)
- `legacy/workspaces/current-reuse-telescopic-ota-report/{REPORT_DATA.json, final_report.html}`·`workspaces/analog-gmid-design-workspace/.../report.html`(산출물 기록)
- `tools/spice_oracle/smoke/*.oracle_input.json`(smoke 당시 기록 -- test가 lut_npz를 덮어씀)
- `test_lut_single_source.py:106`(거부 확인용)
- .py 코드 참조는 0이다.

## 안전 확인
- 실제 저장소 `status --short | head`: 검증 전후 같음.
- reflog 마지막 3줄: 검증 중 `1b1f2eac merge cards/revise-1029b`가 하나 늘었다. 내 명령이 아니다(이 검증은 실제 저장소에 읽기 명령만 썼다) -- 오케스트레이터 병합으로 보임.
- 대상 worktree: 6c2d9a0e, 깨끗함.
- 격리 복제본 안 임시 worktree `Temp/lvh`·`Temp/lvb`(짧은 경로용)는 제거했다.

## 재검증 -- e1f615b5 (2026-10-30)

**판정: 병합 가능.** M-1은 해소됐다. 새 guard에 구멍 2개가 남았지만 둘 다 일부러 우회해야 생기는 경우라 Minor로 본다. 아래 r-1은 병합 전에 한 줄로 고치기를 권고한다.

(1) M-1 guard 변이 재현. `mut` worktree를 e1f615b5로 옮기고 추적 .py 변이 5개를 넣었다(`git add -N`). 결과 파일은 `<S>mut2_single_source.txt`.

| 변이 | 내용 | 결과 |
|---|---|---|
| m1 | `_drafts\engine\lut_slices\manifest.json`·`lut_v2\manifest.json` 경로 리터럴 | 거부 |
| m4 | 슬라이스 npz 직접 `np.load` | 거부 |
| m5 | 폴더가 붙은 lut manifest(`D:/data/old_lut_set/manifest.json`) | 거부 |
| m6 | `os.path.join(<허용 리터럴 _drafts/engine/lut_slices>, "manifest.json")` | **통과(구멍)** |
| m7 | 위반 리터럴이 있는 파일에 SyntaxError를 넣음 | **통과(구멍)** |

- **r-1 (Minor, 병합 전 권고): 허용 예외가 파일과 무관하게 걸린다.** `_GEN_SEARCH` 예외 자체는 타당하다. 그 폴더에서 찾는 것은 LUT 데이터가 아니라 슬라이스 생성기 소스이고, `test_tolerance.py:696-714`가 manifest의 `generator_sha256`과 같은 파일만 쓴다. 그런데 `ALLOWED_LITERALS`는 모든 파일에 적용된다. 그리고 그 폴더에는 옛 12-L LUT의 `manifest.json`과 슬라이스가 그대로 있다. 그래서 다른 파일이 이 리터럴에 `"manifest.json"`만 이어 붙이면 옛 LUT를 조용히 읽을 수 있다(m6). 권고는 예외를 (파일 `gmid_engine/tests/lut/test_tolerance.py`, 리터럴) 쌍으로 좁히는 것이다. 근본적으로는 `_drafts` 옛 LUT 삭제(사용자 결정)나 생성기를 데이터 루트로 옮기는 방법이 있다.
- **r-2 (Minor): SyntaxError 파일을 건너뛴다.** `except SyntaxError: continue`는 fail-open이다. 정규식으로 대체 검사하거나 실패로 바꾸기를 권고한다. 실제 피해 가능성은 낮다(문법 오류 파일은 import도 되지 않음).
- 오탐 점검: 전체 tests/lut 실행에서 새 guard test 2개가 통과했다. 즉 지금 저장소에서 오탐은 0이다.

(2) m-1 복원. base(4a0b6323)와 diff한 결과 `build_html.py`·`build_report.py`는 각 1줄만 다르다. sample 파일 이름을 "old sample LUT … removed O-180"으로 바꾼 줄뿐이다. 나머지는 base와 바이트 동일하다.

(3) m-3 복원. 되살린 `test_dead_probe_files_are_absent`의 단언 `assert_paths_absent(_REPO_ROOT, _DELETED_PROBES)`는 base 줄과 같다. base에서 빠진 것은 probe 수 인벤토리와 `assert_promotion_is_exclusive`이다. 둘 다 probe 삭제로 성립하지 않는다. legacy 묶음은 base부터 수집이 실패해서 이 단언을 실행으로 확인하지는 못했다.

(4) test 재실행. 짧은 경로 worktree `Temp/lvh`(e1f615b5)에서 `gmid_engine/tests/lut/` + `tools/spice_oracle/tests/test_legacy_adapter.py`를 돌렸다. 결과는 **1072 passed, 실패 0**, 739.5 s다(`<S>head2_lut_adapter.txt`). `test_lut_single_source.py` 7개가 포함돼 있다. 작성자 보고 1072와 일치하고, 1차의 1070에 새 guard test 2개를 더한 수와 같다.

그 밖에 m-4(CONTRACT 1.8 문언)와 m-5(conftest 머리줄, `existing = sorted`) 반영을 diff로 확인했다.

안전: 실제 저장소의 `status --short | head`와 reflog 마지막 3줄이 재검증 전후 같다. 대상 worktree는 깨끗하다. `Temp/lvh`는 제거했다.
