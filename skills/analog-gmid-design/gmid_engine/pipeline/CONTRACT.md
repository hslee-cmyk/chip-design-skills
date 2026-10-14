# gmid_engine.pipeline 동작 계약 -- 단계 A 진입점 (U1 배선) + 단계 B GB4 달성가능성 (U9, 5절)

ng-bridge 브랜치(`oracle_input` 등 오라클 생산자)가 같은 파일을 쓴다. 병합 때 이 절을 그 파일의 새 절로 합친다. 이 문서는 단계 A 만 다룬다.

## 1. `run_stage_a(topology_path, spec_path, lut, *, output_dir, pdk_decl, lut_rule_decl, pdk_decl_path, lut_rule_decl_path, supplies_v=None, structure_path=None) -> StageAResult`

[U17 ①-b] (설계 40 §2.4.1~§2.4.3·§2.4.7·§2.4.8 v1.9.1 D1·D6·D8) `lut_rule_decl`(core `read_pdk_decl(LUT 생성 규칙 선언)` 결과)도 **필수**다(PdkDecl 아니면 `TypeError`) -- S0 키 입력에
`lut_rule_decl_fp`(`decl_sha256`), sources 에 `lut_rule_decl`(`lut_rule_decl_path`, `decl_sha256`)가 더해진다(S0 필드 `graph/kernel: junction_source` 가 그 선언을 읽는다). `PdkDecl` 값에는 파일 경로가 없으므로(사용자 결정 7, core CONTRACT 9.2) 두 선언의 위치는 호출자가 `pdk_decl_path`·`lut_rule_decl_path`(**필수** 키워드 인자, 기본값 없음)로 넘긴다. sources 는 S0 키 메타(U-68 정리가 '그 선언 파일의 현재 바이트로 키를 만들 수 있나' 를 판정하는 위치 기록 -- 저장소 안이면 `repo:` 상대 위치)일 뿐 S0 값·스냅샷 `fp`·`context_fp` 에 들어가지 않는다: PDK 선언을 바꾸면 옛 선언으로 만든 스냅샷이 다음 첫 쓰기에서 정리된다. 두 경로의 파일 원본 바이트 sha256 이 각각 `pdk_decl.decl_sha256`·`lut_rule_decl.decl_sha256` 과 다르거나 파일이 없으면 진입에서(보고서 폴더 쓰기·S0 정리 전) `SchemaRejectedError` 로 거부한다(없으면 reason `pdk_decl_missing`, sha 다르면 `pdk_source_sha256_mismatch`, core CONTRACT 9.3 과 같다; fail-closed; 선언을 읽은 그 파일의 경로만 받는다 -- U-68 정리가 경로의 현재 파일로 키 재현을 판정하므로). 키는 core `S0Slot`
(`StageAResult.s0`)로 묶어 넘긴다. **단계 A 는 S0 스냅샷을 읽기만 한다**: 적중이면 그 스냅샷, 아니면 빈 S0 수준 스냅샷(권한표 search `S0_WRITERS`) 위에서 `build_s1` ->
`build_s1v`(필드 `graph/s1v`) -> 계산 블록 `coupling_vars`(필드 `graph/coupling`)를 부르고(적중이면 계산 0), 쓰기는 `search.build_search_context(s0=)` 끝에서 한 번이다(v1.9.1 D6).
보고서의 `views`·`applied_facts`·`ff_ratio_candidates`·`tables`·`coupling` 은 필드를 읽어 만든다. `tables` 에서 옛 `key`(S1v 묶음 키) 칸은 없어지고 `facts_applied` 는
`applied_facts` 로 이름이 바뀐다(묶음 객체 없음, 사본·별칭 없음).

[U17 ①-a] `pdk_decl`(core `read_pdk_decl` 결과)은 **필수**다 -- 빠지면 파이썬 `TypeError`, PdkDecl 아니면(None 포함) `TypeError`(S0 키의 PDK 선언 해시, 40 §2.4.12 Q1 fail-closed). S0 수준 스냅샷 영속화(설계 40 §2.4.3, core CONTRACT §11): `structure.json` 로드 뒤 키 입력 {`topology_fp`(정규화 연결 지문), `supplies_v_fp`, `spec_fp`(spec 없으면 None), `structure_facts_fp`(`fp_of(StructureFacts)`), `derivation_rule_fp`(`structure_rule_fp()`), `lut_fp`(`lut.fp`), `pdk_decl_fp`(`pdk_decl.decl_sha256`)} + 입력 파일 sources {`topology`(경로, `file_sha256`), `spec`(경로, `file_sha256` | spec 없으면 (None, None)), `structure`(경로, 원본 sha256 | 파일 없으면 None), `pdk_decl`(`pdk_decl_path`, `decl_sha256`), `lut_manifest`·`lut_cap`·`lut_midpoints`·`lut_noise`·`lut_mismatch`(LUT 출처의 경로·sha256, 없으면 (None, None))} + 엔진 코드 지문으로 `S0SnapshotStore.default` 를 읽는다. hit 이면 `build_s1(previous=읽은 스냅샷)` -- S1 블록 12개가 모두 재사용(계산 0), 결과 `s1.snapshot.fp` 는 계산했을 때와 같다. miss·corrupt 면 계산한 S1 스냅샷을 쓴다(`save`). 보고서 `s0_snapshot` = "hit" | "miss" | "corrupt"(S1 단계 전 정지면 None). 엔진 코드 지문은 호출마다 한 번 재 `StageAResult.code_fp`(정지 결과 포함)로 돌려준다 -- `search.build_search_context(..., code_fp=)` 가 받는다.

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

- [U17-1d] A2 `build_s1(marks=)`: spec 이 있으면 `sizing.symmetry_marks(dc_inputs_from_spec(spec))`, 없으면 `NO_MARKS`(대칭 블록의 선언 표시 -- 커널 컨텍스트와 같은 그래프 하나, 40 §6-8 D-2).
  보고서 키 `orbit_matching_crosstab` = `{"orbits": [{"members", "records": [[kind, members]]}], "records": [{"kind", "members", "orbits"}]}`(MOS 궤도만, 40 §6-5; 정지 전 단계면 None).

JSON 키(키 정렬): `circuit`, `status`, `exit_code`, `count_budget`(정지 전 단계면 0), `declared_comparison`, `stop_reasons`(`severity|code|view|대상,...|근거` 문자열 목록,
로드 거부는 `A1_load: <FailureRecord>`), `review_needed`(같은 형식), `views`(id·kind·blocks[kind,key,stage]·loop_count·cuts + [U1b] feedforward[id,cells,bias_cells,load_cells,bypassed_blocks,sign]·loop_roles[loop_id,role,reason]·polarity), `applied_facts`([U1b] 적용·확인한 (concept, subject) 목록), `ff_ratio_candidates`([U1b] [{view, ff, bypassed_block, relation, source}] -- 영점 상쇄 비율 제약 후보, 값은 spec 이 선언할 때만 제약), `tables`(= `graph.structure_tables(s1v)`:
뷰별 셀·구동 종류·stage·블록·극점 노드·출력 방향·루프·끊는 점·`unreduced_diff`·기록, L 동치류, declared 요약, 적용한 ratified 사실; 로드 정지면 None), `coupling`([U10] GB3 결합 변수: `kind_counts`·`bias_columns`·`column_block_map`·`column_mate_devices`·`vars`[kind,members,nets,blocks,domain,init_rule] -- `graph.coupling_vars`, 단계 A4; 구조 정지·로드 정지면 None; 바이어스 기둥 의사 블록은 `blocks` 에 `bias:<기둥 id>` 키로 나온다, graph CONTRACT §11). `.md` 는 같은 정보의
사람용 요약. 기존 파일은 덮어쓴다.

## 3. 결과 `StageAResult(exit_code, status, report, report_paths, s1=None, spec=None, code_fp=None, s0=None)`

[U17 ①-b] 묶음 `S1v` 칸은 없다(설계 40 §2.4.7). `s1` = S0 수준 스냅샷 위 `S1Graph`(S1 + `graph/s1v` + `graph/coupling` 필드, `column_unassigned` 정지면 결합 필드 없음; S1 전 정지면 None),
`spec`(로드 정지면 None), `code_fp`(엔진 코드 지문), `s0`(core `S0Slot` -- 키를 만들기 전 정지면 None). 후속 단계: 커널 컨텍스트는 L 동치류를 필드 `graph/s1v: l_classes` 에서 읽는다
(`sizing.build_kernel_context(stage_a.s1, ...)`), 탐색 컨텍스트는 `build_search_context(..., code_fp=stage_a.code_fp, s0=stage_a.s0)`.

## 4. 불변량

같은 입력 -> 같은 `report["tables"]`. `exit_code == 0` 이면 `stop_reasons`·`review_needed` 가 비어 있다. `exit_code` 는 `ok` 이면 0, 로드 거부면 7, 그 밖 정지면 2. 보고서 파일은 항상 쓰인다.

## 5. 단계 B -- `run_stage_b(stage_a, memo, pdk_decl, *, output_dir, settings, diagnostic=False) -> StageBResult` (U9, 설계 41 §0 A5~A7, 41 §4, 40 §3.4)

[U17 ①-b] (설계 40 §2.4.7·§2.4.8 v1.9.1 D2·D6) 커널 컨텍스트(`build_kernel_context(stage_a.s1, inputs, lut)` -- L 동치류는 필드에서) 뒤 스냅샷을 S0 수준 권한표(`S0_WRITERS`)로 넓히고
계산 블록 `search_domain` -> `passive_area_decl` -> `achievability`(필드 `graph/ach`)를 부른다(같은 S0 면 재사용). 정지 판정은 필드 `graph/ach: reasons` 를 읽어 한다(비면 ok, 있으면 exit 3).
`settings`(`SearchSettings`) = 탐색 실행 설정, **필수**(기본값 없음 -- 빠지면 파이썬 `TypeError`, `SearchSettings` 아니면 진입 맨 앞에서 `TypeError`). `build_search_context` 와 같은 값을 넘기면 정의역 블록이 한 번만 계산된다(수동소자 상자가 정의역 입력이라 다른 값이면 그 블록이 다시 계산된다).
보고서 `achievability` 칸은 필드에서 같은 키(`gain`·`area`·`headroom`·`buffer_window_report`·`warnings`·`dof`·`curves`
요약·`count_budget`·`verdict`·`reasons`)로 만든다. 결과 `StageBResult(exit_code, status, diagnostic, report, report_paths, s1=None)` -- `s1` = S0 수준 스냅샷 위 S1Graph(GB4 필드 포함, 건너뛰거나
정지했으면 단계 A 의 것). 묶음 `Achievability` 칸은 없다.

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
* 결과 `StageBResult(exit_code, status, diagnostic, report, report_paths, s1=None)`([U17 ①-b] -- 위 머리 단락).
* 소비처(배선): `achievability.area.a_lb_m2` 는 U11 `search.front_diagnosis` 의 `front_missing` 노트 `A_lb` 자리(지금 `not_computed:achievability_u9_missing`)에 들어간다 -- U11(`budget_report.py`)이 이 브랜치에 병합되면
  `front_diagnosis` 가 `StageBResult.achievability.area` 를 받아 `A_lb` 와 `A_lb/예산` 을 채운다(설계 40 §7.1-4 (i)).
