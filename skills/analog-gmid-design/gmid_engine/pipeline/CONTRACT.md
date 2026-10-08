# gmid_engine.pipeline 동작 계약 -- 단계 A 진입점 (U1 배선)

ng-bridge 브랜치(`oracle_input` 등 오라클 생산자)가 같은 파일을 쓴다. 병합 때 이 절을 그 파일의 새 절로 합친다. 이 문서는 단계 A 만 다룬다.

## 1. `run_stage_a(topology_path, spec_path, lut, *, output_dir, supplies_v=None, structure_path=None) -> StageAResult`

설계 40 §2.1 GB0~GB2, 41 §0 단계 A1~A3. 파일: `stage_a.py`(진입), `stage_a_budget.py`(`structure_count_budget`), `stage_a_report.py`(`write_stage_a_report`).

* 입력: topology 경로, spec 경로(None 이면 spec 없이 구조만 -- 기본 전달 뷰), `lut`(로드된 `LutSet`), `output_dir`, 선택 `supplies_v`({레일: 전위}; 없으면 spec
  의 `supplies_v`), 선택 `structure_path`(기본 = topology 파일 옆 `<회로>.structure.json`).
* 순서 [U1b, 40 §3.2-3]: A1 `load_topology`·`load_sizing_spec` -> `load_structure_facts`(topology_hash = `doc.connectivity_fp`, rule_hash = `structure_rule_fp()`, `net_names` = topology 의 모든 넷;
  `build_s1` 전에 이미 있는 값이다) -> A2 `build_s1(structure=)`(`dc_role`·`matching_pair` 사실 소비) -> A3 `build_s1v(structure=, declared_loop_cuts=)`(`stop_on_unsupported=False`: 기록을 받아 여기서 판정)
  -> 보고서. `declared_loop_cuts` = spec 제약 중 안정도 metric(`pm_` 접두)의 루프 뷰 선언(`ViewDecl` mode loop)의 끊는 넷 -- 단계 A 가 spec 에서 직접 모은다(authoring 파일을 고치지 않는다).
* **N_S**(41 §0): `structure_count_budget(lut, kinds)` = 회로가 쓰는 kind 의 모든 폭 슬라이스에 대한 |L|·|VGS|·|VDS|·|VS| 합. 시간 무관·LUT 에서만 정해진다.
  spec `structure_count_budget` 선언은 U5 로더가 들어오면 대체한다.
* ratified 사실(structure.json): 개념 7개와 소비 방식은 graph CONTRACT 10.6(`drive_kind`·`ac_ground_exception`·`dc_role` override, `loop_role`·`feedforward_cell` confirm, `matching_pair` override).
  `stage_members`(대상 stage 이름, 값 = 공백으로 이은 소자 이름)는 declared stage 로 유도와 대조(`declared_stage_mismatch` review_needed). topology 태그는 읽지 않는다. 파일이 없거나 `stage_members` 사실이 없으면 `declared_comparison` =
  `not_performed: <파일> absent|has no stage_members facts`. 해시 불일치 사실은 적용하지 않고 `structure_fact_stale`(review_needed).
* 정지와 exit code: A1 `SchemaRejectedError` -> exit 7(`stop_reasons` = `A1_load: ...`), A2 거부 -> 7 또는 2, `structure.json` 형식 위반(JSON 이 아닌 파일 포함) -> `SchemaRejectedError` gate `structure_json` -> exit 7(`A2_structure_json`; U1b 가 사실 로드를 `build_s1` 앞으로 옮겼다), N_S 정의역 밖(MOS 없음·LUT 슬라이스 없음, `structure_count_budget` 의 `ValueError`) -> `count_budget_undefined` -> exit 2(`A2_count_budget`). 모든 정지에서 보고서를 쓴다. `기록만` 기록 있음 -> status `stopped`, exit 2.
  review_needed 만 -> status `review_needed`, exit 2(GB4 앞 정지). 그 밖 -> `ok`, exit 0.

## 2. 보고서 (`<output_dir>/<회로>.stage_a.json`, `.stage_a.md`)

JSON 키(키 정렬): `circuit`, `status`, `exit_code`, `count_budget`(정지 전 단계면 0), `declared_comparison`, `stop_reasons`(`severity|code|view|대상,...|근거` 문자열 목록,
로드 거부는 `A1_load: <FailureRecord>`), `review_needed`(같은 형식), `views`(id·kind·blocks[kind,key,stage]·loop_count·cuts + [U1b] feedforward[id,cells,bias_cells,load_cells,bypassed_blocks,sign]·loop_roles[loop_id,role,reason]·polarity), `applied_facts`([U1b] 적용·확인한 (concept, subject) 목록), `ff_ratio_candidates`([U1b] [{view, ff, bypassed_block, relation, source}] -- 영점 상쇄 비율 제약 후보, 값은 spec 이 선언할 때만 제약), `tables`(= `graph.structure_tables(s1v)`:
뷰별 셀·구동 종류·stage·블록·극점 노드·출력 방향·루프·끊는 점·`unreduced_diff`·기록, L 동치류, declared 요약, 적용한 ratified 사실; 로드 정지면 None). `.md` 는 같은 정보의
사람용 요약. 기존 파일은 덮어쓴다.

## 3. 결과 `StageAResult(exit_code, status, s1v, report, report_paths)`

`s1v` 는 정지 전 단계(A1·A2·structure)에서는 None. 후속 단계: `s1v.l_classes` -> `sizing.build_kernel_context(..., l_classes=)`.

## 4. 불변량

같은 입력 -> 같은 `report["tables"]`. `exit_code == 0` 이면 `stop_reasons`·`review_needed` 가 비어 있다. `exit_code` 는 `ok` 이면 0, 로드 거부면 7, 그 밖 정지면 2. 보고서 파일은 항상 쓰인다.
