# gmid_engine.pipeline 동작 계약 -- 단계 A 진입점 (U1 배선) + 단계 B GB4 달성가능성 (U9, 5절)

ng-bridge 브랜치(`oracle_input` 등 오라클 생산자)가 같은 파일을 쓴다. 병합 때 이 절을 그 파일의 새 절로 합친다. 이 문서는 단계 A 만 다룬다.

## 1. `run_stage_a(topology_path, spec_path, lut, *, output_dir, supplies_v=None, structure_path=None) -> StageAResult`

설계 40 §2.1 GB0~GB2, 41 §0 단계 A1~A3. 파일: `stage_a.py`(진입), `stage_a_budget.py`(`structure_count_budget`), `stage_a_report.py`(`write_stage_a_report`).

* 입력: topology 경로, spec 경로(None 이면 spec 없이 구조만 -- 기본 전달 뷰), `lut`(로드된 `LutSet`), `output_dir`, 선택 `supplies_v`({레일: 전위}; 없으면 spec
  의 `supplies_v`), 선택 `structure_path`(기본 = topology 파일 옆 `<회로>.structure.json`).
* 순서 [U1b, 40 §3.2-3]: A1 `load_topology`·`load_sizing_spec` -> `load_structure_facts`(topology_hash = `doc.connectivity_fp`, rule_hash = `structure_rule_fp()`, `net_names` = topology 의 모든 넷;
  `build_s1` 전에 이미 있는 값이다) -> A2 `build_s1(structure=)`(`dc_role`·`matching_pair` 사실 소비) -> A3 `build_s1v(structure=, declared_loop_cuts=)`(`stop_on_unsupported=False`: 기록을 받아 여기서 판정)
  -> 보고서. `declared_loop_cuts` = spec 제약 중 안정도 metric(`pm_` 접두)의 **내부** 루프 뷰 선언(`ViewDecl` mode loop, `beta != declared`)의 끊는 넷. spec `feedback` 소자에서 유도된 β 루프(`beta == declared`, 입력 포트에서 되먹임 수동소자를 거쳐 끊는 테스트벤치 루프)는 metric 의 되먹임 뷰가 평가하는 것이라 엔진 루프 뷰 대조(`loop_cut_unmatched`)와 `build_s1v` 전달 양쪽에서 제외한다 -- 단계 A 가 spec 에서 직접 모은다(authoring 파일을 고치지 않는다).
  끊는 넷은 **엔진 루프 뷰의 끊는 gate 넷**(보고서 `views[].cuts[*][1]`)이어야 하고, 맞지 않는 선언은 단계 A 가 `loop_cut_unmatched`(review_needed)로 보고서에 올린다(graph CONTRACT).
* **N_S**(41 §0): `structure_count_budget(lut, kinds, declared=None)` = `search.count_budget` 한 곳(U9): 회로가 쓰는 kind 의 모든 폭 슬라이스에 대한 |L|·|VGS|·|VDS|·|VS| 합. 시간 무관·LUT 에서만 정해진다.
  spec `structure_count_budget{value, source}` 선언(`CountBudgetDecl`)이 있으면 단계 A 가 `declared=spec.structure_count_budget` 로 넘겨 그 값이 대체한다(S0 지문은 spec 지문).
* ratified 사실(structure.json): 개념 7개와 소비 방식은 graph CONTRACT 10.6(`drive_kind`·`ac_ground_exception`·`dc_role` override, `loop_role`·`feedforward_cell` confirm, `matching_pair` override).
  `stage_members`(대상 stage 이름, 값 = 공백으로 이은 소자 이름)는 declared stage 로 유도와 대조(`declared_stage_mismatch` review_needed). topology 태그는 읽지 않는다. 파일이 없거나 `stage_members` 사실이 없으면 `declared_comparison` =
  `not_performed: <파일> absent|has no stage_members facts`. 해시 불일치 사실은 적용하지 않고 `structure_fact_stale`(review_needed).
* 정지와 exit code: A1 `SchemaRejectedError` -> exit 7(`stop_reasons` = `A1_load: ...`), A2 거부 -> 7 또는 2, `structure.json` 형식 위반(JSON 이 아닌 파일 포함) -> `SchemaRejectedError` gate `structure_json` -> exit 7(`A2_structure_json`; U1b 가 사실 로드를 `build_s1` 앞으로 옮겼다), N_S 정의역 밖(MOS 없음·LUT 슬라이스 없음, `structure_count_budget` 의 `ValueError`) -> `count_budget_undefined` -> exit 2(`A2_count_budget`). 모든 정지에서 보고서를 쓴다. `기록만` 기록 있음 -> status `stopped`, exit 2.
  review_needed 만 -> status `review_needed`, exit 2(GB4 앞 정지). 그 밖 -> `ok`, exit 0.

## 2. 보고서 (`<output_dir>/<회로>.stage_a.json`, `.stage_a.md`)

JSON 키(키 정렬): `circuit`, `status`, `exit_code`, `count_budget`(정지 전 단계면 0), `declared_comparison`, `stop_reasons`(`severity|code|view|대상,...|근거` 문자열 목록,
로드 거부는 `A1_load: <FailureRecord>`), `review_needed`(같은 형식), `views`(id·kind·blocks[kind,key,stage]·loop_count·cuts + [U1b] feedforward[id,cells,bias_cells,load_cells,bypassed_blocks,sign]·loop_roles[loop_id,role,reason]·polarity), `applied_facts`([U1b] 적용·확인한 (concept, subject) 목록), `ff_ratio_candidates`([U1b] [{view, ff, bypassed_block, relation, source}] -- 영점 상쇄 비율 제약 후보, 값은 spec 이 선언할 때만 제약), `tables`(= `graph.structure_tables(s1v)`:
뷰별 셀·구동 종류·stage·블록·극점 노드·출력 방향·루프·끊는 점·`unreduced_diff`·기록, L 동치류, declared 요약, 적용한 ratified 사실; 로드 정지면 None), `coupling`([U10] GB3 결합 변수: `kind_counts`·`bias_columns`·`column_block_map`·`column_mate_devices`·`vars`[kind,members,nets,blocks,domain,init_rule] -- `graph.coupling_vars`, 단계 A4; 구조 정지·로드 정지면 None; 바이어스 기둥 의사 블록은 `blocks` 에 `bias:<기둥 id>` 키로 나온다, graph CONTRACT §11). `.md` 는 같은 정보의
사람용 요약. 기존 파일은 덮어쓴다.

## 3. 결과 `StageAResult(exit_code, status, s1v, report, report_paths, s1=None, spec=None)`

`s1v`·`s1`·`spec` 은 정지 전 단계(A1·A2·structure)에서는 None(`s1`·`spec` 은 단계 B 가 이어 쓴다, U9). 후속 단계: `s1v.l_classes` -> `sizing.build_kernel_context(..., l_classes=)`.

## 4. 불변량

같은 입력 -> 같은 `report["tables"]`. `exit_code == 0` 이면 `stop_reasons`·`review_needed` 가 비어 있다. `exit_code` 는 `ok` 이면 0, 로드 거부면 7, 그 밖 정지면 2. 보고서 파일은 항상 쓰인다.

## 5. 단계 B -- `run_stage_b(stage_a, memo, pdk_decl, *, output_dir, diagnostic=False) -> StageBResult` (U9, 설계 41 §0 A5~A7, 41 §4, 40 §3.4)

파일 `stage_b.py`. GB4 달성가능성(`metrics.achievability`)을 단계 A 결과 위에서 한 번 돌린다(탐색 앞, S0 당 1회).

* 입력: `stage_a`(`run_stage_a` 결과), `memo`(`lut.LutMemo`; 호출자가 상한을 정한다 -- 곡선 영역 상한이 GB4 가 만드는 곡선 수 Σ_kind |L|·|VDS|·|VS| 이상이면 재계산이 없다), `pdk_decl`
  (`core.read_pdk_decl` 결과 -- `search_domain` 의 b_A 와 `passive_area_decl` 의 단위 면적), `output_dir`, 선택 `diagnostic`.
* 순서: `stage_a.status` 가 `ok` 일 때만 계산한다(`review_needed`·정지는 GB4 앞 정지 -- `status = skipped`, exit code 는 단계 A 의 것). `diagnostic=True` 면 `s1v` 가 있는 한 정지 상태에서도 계산해
  측정만 한다(정지 판정은 안 바뀌고 `StageBResult.diagnostic` = True 로 표시). -> `dc_inputs_from_spec` -> `build_kernel_context(l_classes=)`(쓰기 계획·전류 기저·θ 스키마) ->
  `search_domain`(θ 전류 상자·자기동형 묶음 `ties`/`negated`/`zeros`·b_A. `SearchSettings.front_budget_s` = spec `search.front_budget_s`, 없으면 `wall_clock_budget_s`) -> `search.passive_area_decl` ->
  `search.count_budget`(N_S, 선언값 우선) -> `metrics.achievability(stop=True)`.
* 정지와 exit code: 인증된 근거가 있으면(Σ gain 상한 < 목표, A_lb > 예산 + b_A, 대상 창 상한 < 선언 제약, 매칭 안 되는 등식) `InfeasibleTargetError` -> **exit 3**(`status = infeasible`, `stop_reasons` =
  `<사유 코드> <상세 JSON>`). 커널 컨텍스트·search 정의역의 정지(`StructureUnresolvedError`·`SchemaRejectedError`·`InfeasibleTargetError` 선언 KCL 충돌)도 같은 방식으로 `status = stopped` 와 그 분류 exit code.
  미상(인증 못 함)·선언 제약 없는 창·입력 DC 대기는 정지가 아니다(`status = ok`, exit 0, 수치와 사유가 보고서에 있다). 보고서는 항상 쓴다.
* 보고서 `<output_dir>/<회로>.stage_b.json`(키 정렬)·`.stage_b.md`: 키 `circuit`, `status`, `exit_code`, `diagnostic`, `count_budget`(N_S), `stop_reasons`, `achievability`(None 이거나 `metrics.Achievability` 의 JSON:
  `gain`{view, blocks[], ff[], sum_db, b_db, target_db, verdict, n_unknown, found_sum_db}, `area`{a_lb_m2, terms, budget_m2, b_a_m2, verdict, not_certified}, `headroom[]`, `buffer_window_report[]`, `warnings`,
  `dof`, `curves`{요약: 슬라이스·축별 칸 개수, 격자 전용 칸은 (kind, w_key, 축)별 개수}, `count_budget`). 블록 행 `BlockBound`: `status`(certified|unknown), `a_max_db`·`b_db`(인증만), `pi`(격자 곱), `axes`, `row_condition`,
  `reason`(미상 사유), `found_db`(하한 추정 -- 상한이 아니다).
* 결과 `StageBResult(exit_code, status, diagnostic, achievability, report, report_paths)`.
* 소비처(배선): `achievability.area.a_lb_m2` 는 U11 `search.front_diagnosis` 의 `front_missing` 노트 `A_lb` 자리(지금 `not_computed:achievability_u9_missing`)에 들어간다 -- U11(`budget_report.py`)이 이 브랜치에 병합되면
  `front_diagnosis` 가 `StageBResult.achievability.area` 를 받아 `A_lb` 와 `A_lb/예산` 을 채운다(설계 40 §7.1-4 (i)).
