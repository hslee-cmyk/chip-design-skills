# fix/o181-tests 독립 검증 (위임 A-31, 재개판)

- 대상: fix/o181-tests d9509421(커밋 4개, 77 파일, 분기점 325ee241).
- 병합본: `iso` = master e33100cc + no-ff 병합(복제본 안 커밋 18df6589). 비교 기준: `iso_master` = e33100cc. 위치 `C:/Users/HSLEE/AppData/Local/Temp/la1s_o181_audit/`. 저장소에는 쓰지 않았다.
- 러너: `o181_validation/run_by_file.py`(인자 `--cwd`, `--out`). 원자료: `o181_validation/`(`results_merged.jsonl`, `results_base.jsonl`, `compare_out.txt`, `base_light_out.txt`, `static2_out.txt`).

## 결론

**확인된 결함은 0건이다. 다만 stage_b 실패 9건을 base에서 재지 못해 '새 실패'가 아직 닫히지 않았다. 그래서 끝 줄은 Major 1이다(미판정, 확정 결함 아님).** base 러너가 메모리 부족으로 강제 종료됐고, 종료 알림의 지시에 따라 다시 시작하지 않았다.

| 판정 항목 | 결과 | 근거 |
|---|---|---|
| 충돌 | 없음 | e33100cc 위 no-ff 병합 깨끗함. 77 파일 전부 수정(M) |
| 엔진 변경 누출 | 없음 | 76 파일이 `gmid_engine/tests/` 안, 1 파일이 `erfc_ota.sizing_spec.json` |
| connectivity 변경 | 없음 | `assets/library/*.topology.json` 변경 0. erfc는 지문 한 줄(아래) |
| 기준 약화 | 없음 | 2절 |
| 새 실패 | **미판정(9건)** | 3절. 16건은 새 실패 아님(측정), 9건은 base 미측정 |

## 1. erfc `topology_fp`

| 확인 | 결과 |
|---|---|
| spec diff | `meta.topology_fp` 한 줄만 |
| topology blob | master와 병합본이 같음 |
| 81dddba5판(O-174 전) 로더 지문 | cc69e381… = spec 옛 값 |
| 6705b911판(O-174) 로더 지문 | a5710202… = spec 새 값 = 현재 값 |
| 두 판 사이 차이 | M19·M20 bulk vdd→vcn, M21 bulk vdd→vcp. 다른 연결 항목은 같음 |
| spec의 의존 | bulk·vsb·M19~M21 grep 0건 |
| 13회로 spec 지문 = topology 지문 | 13/13 |

connectivity를 바꾼 커밋이 아니라 앞선 O-174 정정에 지문을 맞춘 것이다. 승인 근거는 O-199 끝 문장 "spec meta.topology_fp 갱신 진행(spec에 bulk·vsb·M19~M21 의존 항목 0건)"이다. A-31 행의 '승인 행 못 찾음'은 이것으로 닫는다.

## 2. 기준 약화 대조

제거·추가된 단언 줄을 전수로 뽑아 읽었다. 77 파일 중 60 파일은 순수 개명이다(`static_checks_out.txt`).

| 변경 | 판정 | 근거 |
|---|---|---|
| 기대표 9→13 | 상향 | 집합 일치 단언 유지. JSON 재집계가 표와 일치. 출처 인용 확인(A-7, D-1, D-2·D-7, erfc ⚠13, cnr figure 문구, O-196) |
| 규칙 E 어휘 제외 | 승인됨(O-198) | 전체 이름 위반 35건 → 제외 뒤 0건. 빠진 이름은 Q4·Q8·Q9·VS·Z 5개. `structure` 폴더 pytest 통과(거부 self-test 4건 포함) |
| 규칙 E 회로 수 `>= 9` → `>= 13` | 상향 | |
| fixture Q1~Q5→Mfx1~Mfx5 | 불변 | 개명 외 차이는 fx_spec 두 파일의 지문 줄뿐. Mfx는 library 이름과 겹치지 않음 |
| 기준선 KeyError → 회로별 실패 | 상향 | 수집이 죽던 세 파일에서 9회로가 실행되고 4회로는 설명 있는 red. skip 없음 |
| `_searched`·`SEARCHED`의 `.get` | 보완됨 | 새 회로가 조용히 빠지지 않게 `*baseline_present*`가 회로마다 red로 잡음 |
| g10 `len(CIRCUITS)==9` 삭제 | 약화 아님 | 회로별 `_baseline` 전제로 대체. 회로 집합은 thirteen test 3건이 지킴 |
| `_supplies` 기본값 삭제 | 상향 | 옛 선언이 있던 9회로와 값이 같음. 발명 기본값 제거 |
| `_CURRENT_FED` r2r 칸 | 정당(O-196) | 연결 재확인: M21·M22 직렬 diode + Ib5, M23·M24 + Ib2 |

표지(Major 아님):
- 규칙 E 어휘 면제는 엔진 전체에 걸린다. plan_ids에 이름을 올리면 규칙을 피할 수 있다. O-198이 승인한 정의다.
- `test_spec_library_load.py`의 9회로 결정 표 test는 `TABLE`(9회로) 그대로다. 새 4회로에는 그 항목이 없다.
- 파일 이름 `*_9circuits`는 낡았다.
- `test_structure_test_mapping.py`(규칙 H)는 마커로 기본 제외라 이번에 돌지 않았다(rc 5, test 0건). 설계된 동작이다.

## 3. 전체 test

파일 하나당 프로세스 하나, slow 포함(`--run-slow`).

| 쪽 | 범위 | 결과 |
|---|---|---|
| 병합본 | 442/442 파일 완료, 메모리 중단 0(최저 여유 2684 MB) | 10406건, 실패 25, 오류 0, skip 2 |
| base | 비교 범위(authoring, integration, structure) 64개 중 45개 완료 | 1637건, 실패 4, 오류 0 |

- base 미측정 19개: `integration/`의 `test_blas_thread_determinism`, `test_drive_kind_mixed_9circuits`, `test_floorplan_literal_sensitivity`, `test_g10_no_recompute_9circuits`, `test_j_rules_library`, `test_layer0_boundary_rows`, `test_nfr4_compare`, `test_no_s0_files_written`, `test_rerun_s3_independence`, `test_run_isolation`, `test_s0_layer_9circuits`, `test_sp1_library_summary`, `test_spec_library_load`, `test_stage_a_library`, `test_stage_b_library`와 `structure/`의 `test_removed_names`, `test_structure_rules`, `test_structure_rules_reject_fixtures`, `test_structure_test_mapping`.
- base를 애초에 범위에서 뺀 곳: 변경 test가 없는 폴더(lut, metrics 등). 병합본에서 실패가 0이라 새 실패가 될 수 없다. 이 폴더들의 base 실패 수는 재지 않았다.
- 주의: `compare_out.txt`의 'merged only' 25건은 위 미측정 파일 때문이다. 그 자체로 새 실패라는 뜻이 아니다.

### base 실패 4건(측정, 전부 이 브랜치가 고침)

| test | 원인 | 병합본 |
|---|---|---|
| `test_spec_load::test_spec_fixture_names_disjoint_from_library` | fixture 이름 Q1~Q5가 rfc_ota와 겹침 | 통과 |
| `test_topology_load::test_fixture_names_disjoint_from_library` | 같음 | 통과 |
| `test_authoring_library_load::test_library_has_exactly_nine_circuits` | 기대표 9회로 | 13회로 test로 통과 |
| `test_bias_source_manifest_library::test_library_set_is_nine` | 같음 | 13회로 test로 통과 |

수집 오류(측정, `--collect-only`): base의 `test_g10_no_recompute_9circuits`, `test_layer0_boundary_rows`, `test_s0_layer_9circuits`는 `KeyError: 'cnr_ota'`로 test를 하나도 수집하지 못한다. 병합본에서는 이 세 파일의 9회로 test가 돈다.

### 병합본 실패 25건과 원인

| 분류 | test | 건수 | base 쪽 | 새 실패? |
|---|---|---|---|---|
| 기준선 없음(새 4회로) | g10 `test_no_same_input_recompute_in_one_run` | 4 | 수집 오류(측정) | 아님 |
| 기준선 없음 | layer0 `test_layer0_baseline_present_for_every_library_circuit` | 4 | 수집 오류, 새 test | 아님 |
| 기준선 없음 | s0 `test_baseline_present_for_every_library_circuit` | 4 | 수집 오류, 새 test | 아님 |
| 기준선 없음 | s0 `test_stage_reports_unchanged_from_base` | 4 | 수집 오류 | 아님 |
| 엔진 쪽 정지 | stage_b cnr: `block_grid`, `gain`, `area`, `diagnostic` | 4 | **미측정** | 추론상 아님 |
| 엔진 쪽 정지 | stage_b r2r: `block_grid` | 1 | **미측정** | 추론상 아님 |
| 엔진 쪽 정지 | stage_b erfc: `block_grid`, `gain`, `area`, `diagnostic` | 4 | **미측정** | 추론상 아님 |

stage_b 9건의 근거(측정이 아닌 추론과 인용):
- test 파일 차이는 `_CURRENT_FED`의 r2r 칸 추가뿐이고, 엔진과 cnr·r2r spec은 base와 같다(실측). 그래서 cnr 4건과 r2r `block_grid`의 결과는 base에서도 같아야 한다.
- erfc는 base에서 spec 지문이 topology와 다르다(cc69… 대 a571…, 실측). 그래서 단계 A가 spec을 거부해 ach가 없을 것이다. 다만 거부 자체를 base에서 재지는 않았다. `base_light_out.txt`의 `erfc spec rejected TypeError`는 내 스크립트 호출 오류(인자 누락)이고 거부 증거가 아니다.
- 원인(agent 인용, `2026-10-31/o181_test_impact.md`): cnr = 단계 B `dc_resistor_cycle` 자기 정지로 ach None, r2r = `block_input_pattern_unsupported`로 pi=0. 같은 문서가 분기점 시점 master의 stage_b 실패를 erfc 5, cnr 4, r2r 2건으로 적었다.
- erfc의 정지 사유는 미측정이다. 지문 갱신 뒤 드러난 실패다.

## 메모리

base 러너는 Claude Code가 메모리 부족으로 강제 종료했다(러너의 1.5 GB 규칙이 아님). 종료 알림이 재시작 금지라 다시 돌리지 않았다. 남은 프로세스는 없고, 확인 시점 여유는 5148 MB다.

## 닫는 방법(지시가 있을 때)

러너는 끝난 파일을 건너뛰므로 같은 명령으로 이어진다. 판정에 필요한 최소 범위는 `test_stage_b_library.py` 하나로, 병합본에서 약 3분 걸렸다.

```
C:/Python314/python.exe -P <evidence>/o181_validation/run_by_file.py --cwd <TEMP>/iso_master --out <TEMP>/byfile_base --only-file <TEMP>/base_files.txt
```

stage_b 9건이 base에서도 실패하면 Major 0으로 닫는다.

## 판정

- 확인된 기준 약화·엔진 변경 누출·connectivity 변경·새 실패: 0건.
- Major 1 = **M-1 새 실패 미판정**(stage_b 9건을 base에서 같은 방식으로 재지 못함). 지시한 비교 방식이 끝나지 않아 fail-closed로 넣었다.

verdict: Major 1

## 닫기 측정 (2026-11-04, 사용자 지시 "1번 다시 돌려")

- 실행: 오케스트레이터가 `test_stage_b_library.py` 하나를 `iso_master`(e33100cc)에서 같은 러너로 돌림. 원자료 `o181_validation/results_base_stage_b.jsonl`. `--abort-mb 2048`, 최저 여유 2381 MB, 184초.
- base: 68 test, 실패 11. 병합본: 68 test, 실패 9.
- 병합본 실패 9건은 전부 base에서도 실패(새 실패 0). base에만 있는 실패 2건: `test_area_lower_bound_from_declared_values[r2r_opamp]`, `test_count_budget_is_lut_grid_sum_of_used_kinds[erfc_ota]`.
- 위 '닫는 방법'에 판정자가 미리 적은 규칙(9건이 base에서도 실패하면 Major 0)을 그대로 적용했다. 오케스트레이터는 fix/o181-tests 작성자가 아니다. 9건의 실패 원인 판정은 아니며, 그 처리는 O-227 (2)가 맡는다.

verdict: Major 0
