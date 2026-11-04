"""IT-2b 판정 기록 둘째 판(감사 마무리 -- 병합본 c4eaa137 = role/code/it2b c40ad4ea: code 431d2e7b·test 여덟째 db216ef7).
red 계수 규칙은 첫 판(write_record_it2b.py)과 같다: 행동 red(AssertionError·엔진 출력 항목 부재 KeyError·권한표 WriterPermissionError) + 새 이름 부재 AttributeError,
새 서명 직접 호출(TypeError 1, saturation_window 새 positional 꼴 KeyError 11)은 세지 않음.
usage: python -I write_record_it2b_v2.py <red_classified_rg4.json> <out record json>
"""
import hashlib
import json
import sys

SIG_KEYERROR = {"test_hand_linear_system", "test_it2b_sw_kind_is_not_used_for_window_end", "test_it2b_sw_several_roots_move_together",
                "test_it2b_sw_root_pair_replaces_row_equation_by_fixed_net", "test_singular_system_is_none"} | {
                "test_random_linear_systems_against_numpy[%d]" % i for i in range(6)}


def red(rows):
    ids, hashes = [], []
    for r in rows:
        name = r["test_id"].split("::")[-1]
        if r["type"] == "TypeError" or (r["type"] == "KeyError" and name in SIG_KEYERROR):
            continue
        typ = r["type"] if "." in r["type"] else "builtins." + r["type"]
        ids.append(r["test_id"])
        hashes.append(hashlib.sha256((r["test_id"] + "\n" + typ).encode("utf-8")).hexdigest())
    return ids, hashes


CHECKS = {
    "V1": ("PASS", "전체 suite --run-slow, 병합본 c4eaa137 격리 복제본 h, test 파일 하나당 pytest 프로세스 하나 순차(scripts/run_final.sh 단계 3, 재개 가능, -k·--deselect·-x 없음; 구조 규칙 fixtures 제외): test 파일 441개(junit 442), 10356 passed·0 failed·0 error, xfail 2(기존 layout test_patterns_common_centroid), 설정 deselect 1(structure/test_structure_test_mapping 규칙 H 골격 -- 기본 실행 제외 마커, IT-2a 와 같은 조건). 규칙 A~G·I·K·M(structure/test_structure_rules 14 passed, test_rule_a_one_entry_point_per_file 포함)·test_removed_names 16·reject_fixtures 37 통과. 파일별 최대 작업 집합 최대 2430 MB(run_one.py 계측, 메모리 중단 0). 별도 -m structure_test_mapping(규칙 H): head 위반 6건·base 5건(대상 405) -- 늘어난 1건 = tests/sizing/test_output_structure.py [orphan_test] '원본 없음: sizing/output_structure.py'. 이 파일 이름은 card 'test 작성 주체 몫'이 정한 새 test 이름(41:727 'test_writer_plan.py 옆 새 파일')이라 card 기인; 규칙 H 는 기본 실행에서 빠지는 골격이고 나머지 5건은 기존(logs/ruleH_h.txt·ruleH_b.txt). 처리(이름 변경·mapping 예외)는 오케스트레이터 결정 사항."),
    "V2": ("PASS", "red-green(최종 test = db216ef7 포함). base = 엔진 56080584 + c4eaa137 test 파일 여섯(복제본 r): 45 failed / 140 passed(logs/rg4_r). 분류(raw/red_classified_rg4.json): 행동 red 28 = AssertionError 23 + 엔진 출력 dict 항목 부재 KeyError 4(K2 'z'·P(a) 'p'·D(a) 'in'·test_declared_input_dc_same_theta_seals 'in') + WriterPermissionError 1(권한표 node.dc_output_structure 행 없음); 새 이름 부재 AttributeError 5(Window.input_status·tol_v 4, s2_values.OUTPUT_HIGH_IMPEDANCE 1); 세지 않음 12 = TypeError 1(slope= 키워드) + 새 서명 positional 꼴 KeyError 11. red 계수 33, 하네스·import 가짜 red 0. L12 (f): 엔진 c4506f47(615ef68b 전) + 최종 test(복제본 f) -> 그 test 만 실패(AssertionError: tol_v 1.12305e-5 = 첫 해 tol, 기대 마지막 해 tol 1.45996e-5, 차 3.37e-6 > 허용 0.02·tol_last = 2.92e-7), 나머지 184 pass(logs/rg4_f) -- 행동 red; k_max test 는 c4506f47 에서도 pass(이 test 는 615ef68b 를 가르는 test 가 아님). head c4eaa137 185 passed(logs/rg4_h). 앞 판(dc334fef) red 33·L12 (f) red 와 같은 결과."),
    "V3": ("N/A", "도입 해당 없음(DEC-86): merge_gate·mutate_changed 미사용(N6.3 절차, card V3 칸). D (b)(c)(d) AST test 거부는 변형 17종으로 직접 쟀다(V4)."),
    "V4": ("PASS", "oracle 독립성. (a) L12 (a) k_max test(db216ef7 판): 전제 tol 을 공개 표 API(tol_v_table.at(L, VDS) 를 엔진 해의 dc_op 로 읽은 소자 최솟값)로 읽고, 소진 도달을 '같은 toy·같은 θ·실행마다 새 ctx 에서 상한 2 -> measured, 상한 1 -> unsettled' 비교로 보이며, w.tol_v is not None 으로 A6 b(tol 미정) 갈래를 배제한다 -- 첫 판 감사 제안 둘 반영. 공허하지 않음 실측(logs/neg_lut_probe2.jsonl, 복제본 p = c4eaa137): NEG_QV 0.005(현행) y = 0.3 에서 주입 없음 measured·상한 3 measured·상한 2 measured·상한 1 unsettled(tol_v 1.235e-5, 창 lo 0.68803694 대 0.68803769), test pass; NEG_QV 0.5 에서는 상한 1 도 measured 라 test 가 실패(전제 tol < 1e-3 에서 먼저 실패) -- 소진이 없으면 통과하지 않는다. 상한 1·2 의 상태 차이는 피검 상태 출력의 비교지만 기대값 자체('unsettled'·V = lo + y(hi − lo))는 design 정의이고 상한 값은 test 가 주입한 입력이다(UNJUDGED 0). NEG_QV 0.05 -> 0.005 는 tol 규모(1.46e-4 -> 1.46e-5)만 바꾸는 픽스처 조정: QV 0.05 에서도 k_max·L12 (f)·P(a) 셋 모두 pass. (b) L12 (f) 허용오차 절대 2e-6 -> 상대 0.02·tol_last: 현행 LUT(QV 0.005)에서 tol_last 1.45996e-5 -> 허용 2.92e-7(옛 절대 2e-6 의 1/6.8 -- 더 엄격), 첫 해·마지막 해 tol 차 3.37e-6 = 허용의 11.5배라 판별력 유지, 실측 |tol_v − tol_last| = 0(비트 같음); 옛 LUT(QV 0.05) 규모로 보면 옛 2e-6 = tol_last 의 1.37%, 새 2% -- 같은 규모. 전제 (1) '차 > 1e-5' -> '차 > 0.1·tol_last'(1.46e-6, 실제 차 3.37e-6) 도 규모 맞춤. 약화 아님. (c) D (c)(iii) 'conduct' 부분문자열 대리 측정 한계 1(이름에 conduct 없는 import 통과 -- EO-1 모듈 이름 미정). (d) D (b)(c)(d) 변형 17종(logs/mutate_d2.jsonl): D (b) red 4/5(import 별칭만 통과 -- 한계), D (c) red 6/6, D (d) red 3/3, 기준·주석만 green. 그 밖 oracle: OS (a)~(k) (손) toy 연결, K1·K2·P(a)·P(b)·L12(b)·D(a) (손)+이분법 독립 풀이(전제: 독립 풀이가 엔진 해 재현), L12 (f) (식) 공개 표 API, L12 (e) 끝점 허용 = node.dc_window.tol_v(O-103 design 정의). 피검 함수로 기대값을 만든 assert 없음."),
    "V5": ("PASS", "기준 약화 판정: test diff 56080584..c4eaa137(logs/test_diff_final2.patch, sha256 4d6bb3dd6092e7f2374af31388aa72781465aa3768cb67a06fd996b3057299bd). 지운·완화한 단언 모두 근거 범위 안: (1) conftest write_r4_lut cap_vdsat=() -- 기본 () 이면 루프가 아무것도 더하지 않아 기존 호출 그대로(diff 확인) (2) assert_voltages 키 단언 둘로(card test 메모) (3) saturation_window 새 서명(이동량 = 옛 절대 창 − x0, slope 단언 추가) (4) 끝점 y = 0·1 단언 O-103·L12 (e)(내부 y 단언 그대로, tol_v None 이면 실패) (5) test_declared_input_dc_same_theta_seals '\"in\" not in dc_window' -> 항목 있음·measured(design 4.7-3 3, 브리프 목록 밖) (6) 표 33 -> 34, Window 칸 3 -> 5. IT-2b test 커밋 사이 넣었다 뺀 것: op_mismatch·status_detail(O-98·O-101 범위 이동), test__helpers_dc_solve.py·공개 이름 test(IT-2d 경계), 자작 'v_on' 검사 -> 계획 (9)(c) 세 항목. test 여덟째 db216ef7: k_max 전제 '창 차 > tol' 삭제 -> 상한 2/1 상태 비교 + tol_v not None(더 강함, V4 (a)), L12 (f) 허용오차 절대 -> 상대(현행 규모에서 더 엄격, V4 (b)), NEG_QV 0.005(픽스처). skip·xfail·importorskip 추가 0, approx 추가 1(새 test rel=1e-12). code 커밋 85847b49·5bd20156·615ef68b·431d2e7b 의 test 변경 0, test 커밋 여덟의 비test 변경 0."),
    "V6": ("PASS", "graph 단일 정본(병합본 c4eaa137): G1 -- node.dc_output_structure writer = dc_writer_plan 하나(writer_plan.py:269), 권한표 행 하나(s2_values.py:150); G_vgs _edges 정의·호출 writer_plan.py:101·181 만; 창 끝 식 = input_window.py saturation_window 하나. G2 -- 새 cache·memo·모듈 dict·sctx 슬롯·값 사본 0; 431d2e7b 의 solved_with 는 _solve_input_window 안 지역 변수, out[head] 는 _windows 안 지역 dict 읽기(graph 규칙 2 '블록 안 local' 범위). G3 -- S0 필드 하나, w3_target 없음. G6 -- node.dc_output_structure 엔진 소비자 0 = 출력 전용(sizing/CONTRACT.md:204), Window.input_status·tol_v 엔진 소비자 0 = 출력 전용 -- IT-2c(icm_config)·IT-2d(metrics_aux) 병합본에서 소비자 ≥ 1 확인 필요. G7 -- dc_writer_plan 블록 행 (calls 2, reuses 1, computes 1) 9회로·모든 판 같음. 회로·소자·넷 이름 code 0. I-perf 재계산(base 56080584 대 head c4eaa137, scripts/perf_it2b.py, raw/perf/): dc_columns 한 호출 안 -- common_gate _solve 7 -> 4·input_windows 5 -> 3·같은 인자 재호출 0, nmcnr _solve 7 -> 4·input_windows 6 -> 3·재호출 0; IT-2b 새 함수(_measure·_tolerance·region_rows) 재호출 0. 남은 같은 인자 재호출은 모두 IT-2b 전부터 있던 자리: Circuit.tolerance(SCC 풀이 안 tolerance 닫힘, block_columns.py:614 등; tol_cells 지역 memo 로 LUT 재조회 0 -- tol_v_cell 재호출 0) cg 6 -> 2·nmcnr 19 -> 9, lut.op_point(_helpers_lut.py:44 forward_point 와 gmb.py:53 이 같은 점) cg 15 -> 9·nmcnr 72 -> 36, lut.vdsat(region_rows block_columns.py:257 -- 해가 바뀌어도 x 에 무관한 소자의 같은 점) nmcnr 48 -> 16 -- 모두 base 보다 적음. dc_columns 누적 시간 cg 0.475 -> 0.445 s, nmcnr 0.872 -> 0.797 s; 평가 1회 중앙값(새 컨텍스트·새 LUT memo, 7회) cg 1.293 -> 1.362 s(잡음 범위), nmcnr 1.884 -> 1.673 s. 431d2e7b 효과: 9회로 탐색에서 _solve 감소 nmcnr 157 -> 156·two_stage_ota_sf 121 -> 120(마지막 두 측정 창이 비트 같은 커널 호출 각 1). 첫 판 기록의 'nmcnr 5회' 는 과대 계수(4회는 측정이 모두 None 인 unmeasured 호출 -- 반복 아님)였다 -- 정정. 수치: 필드 수 1(+ Window 칸 2) / 소비자 0 결함 0(출력 전용 선언) / 정본 우회 의심 0 / KVL·KCL 관계 미적용 0 / graph 밖 저장 자리 0."),
    "V7": ("PASS", "배선: saturation_window <- _Circuit.input_windows <- _measure·_windows; region_rows <- input_windows; k_max 모듈 수준 import(block_columns.py:57); fd_jacobian._steps REL_WINDOW 거름. 실행 관측(raw/run): folded·nmcnr·two_stage·two_stage_ota_sf 뿌리 아닌 입력 포트 창, pushpull 선언 포트 창이 평가마다 쓰임; pushpull 은 항목이 늘어도 fd y 스텝 5/5 BASE 와 같음. _refine_ends·_root_windows 엔진 code 0, _helpers_dc_solve.py·test__helpers_dc_solve.py 없음."),
    "V8": ("PASS", "새 폴백 없음. design 상태 갈래 발동(기록되는 상태): unmeasured(A6 a) nmcnr 2/36 커널 호출(PREFIX·HEAD 같음), unsettled 0(9회로), tol 미정 갈래 0. 뿌리 아닌 포트 slope[net]·out[head] 는 없으면 KeyError(fail-closed)."),
    "V9": ("PASS", "끝점 탐침(봉인된 θ 앞 6개 y = 0·1): HEAD 거부는 봉인 7 뿐 -- common_gate 11/12(|slack_v| ≤ 7.95e-12 V), two_stage_ota 6/12(y = 1, ≤ 4.32e-6 V), two_stage_ota_sf 6/12(y = 0, ≤ 6.55e-6 V -- design 4.7-8 (8) 기록 수치 재현), folded·nmcnr 12/12 봉인; 같은 θ 뿌리 tol_v 6.3e-3~8.4e-3 V 보다 세 자릿수 이상 작음(O-103). 탐색 중 실패 수 HEAD = BASE(9회로); 봉인 7 실패 수는 8회로 같고 two_stage_ota_sf 만 0 -> 1 -- 같은 탐색 단계(평가 열 21번째 봉인 호출)의 실패가 lut_query_failed(y 0.076939) -> 봉인 7 no_root_in_window(y 0.076899)로 바뀐 것(PREFIX 대 HEAD 도 같은 차이 -> 4.7-8 (9) 창 값 변화로 θ y 가 달라진 결과, 끝점 아님). y 끝점 방문 HEAD 0·BASE 1(common_gate y = 1, 봉인) -- O-103 근거와 일치. G-10 recomputes_same_input 0(9회로 × 모든 판)."),
    "V10": ("PASS", "9회로 변화표(raw/compare_final.json, raw/tables.json): 설명 안 된 변화 0. BASE 대 HEAD 차이 = (8) 커널 뿌리 y 끝(뿌리 lo·hi·딸린 W4 비입력 뿌리 창·θ y→V 사상·입력 dc_v·fd y 스텝·탐색 궤적 분기: common_gate 1, folded 6, nmcnr 32, two_stage 1, two_stage_ota_sf 83번째 평가) + 입력 포트 창 항목(4.7-2·4.7-3 2·3: folded 107, nmcnr 56, two_stage 35, two_stage_ota_sf 83, pushpull 84 평가) + (9) tol 매 해. front 지문 common_gate 만 다름(궤적 차), 나머지 8 같음. current_reuse·sf_pushpull 모든 평가가 dc_columns 안 실패 -- BASE = HEAD; ngcc 단계 A review_needed -- 출력 구조 칸만(IT-2a 와 같은 조건). (9) 표(PREFIX c4506f47 대 HEAD): common_gate 커널 39 짝 tol 38·회차 1·창 1, 평가 행 tol_v 77/83; folded 57 짝 tol 1; nmcnr 36 짝 tol 8·회차 1·창 1, tol_v 24/105; two_stage 12 짝 tol 12·회차 6·창 6, tol_v 70; two_stage_ota_sf 18 짝 tol 18·회차 2·창 2, tol_v 166(짝 83); measured/unsettled 판정 변화 0. 431d2e7b 순수 리팩터링: HEAD(엔진 615ef68b) 대 HEAD2(431d2e7b) 9회로 모든 칸 비트 동일(커널 n_solve 제외 -- 줄어드는 것이 목적), 결정성 HEAD2 대 HEAD2_rep2 9회로 비트 동일. 분류표 대조 41:724: 12출력 값 일치·정지 3출력 사유 일치·새 정지 0·선언 변화 0, 출력 ∈ F′(writer_plan.py:134) 발동 0/15."),
}


def main():
    rows = json.load(open(sys.argv[1], encoding="utf-8"))
    ids, hashes = red(rows)
    rec = {
        "id": "20261021-it2b-kernel-window",
        "spec_card": "docs/02-design/specs/20261021-it2b-kernel-window.spec.md",
        "evidence_type": "red-green",
        "base_commit": "56080584a94ecbc69f7c4cfe4292a1cf0f121413",
        "test_commit": "db216ef762b98996d7a852f79ea3920d691bfabb",
        "code_commit": "431d2e7b0d7be8e8eea02d0eb79835da98934a6c",
        "checks": {k: {"verdict": v, "basis": b} for k, (v, b) in CHECKS.items()},
        "reproduced_numbers": [
            {"name": "IT2b/red_count_base", "value": len(ids), "command": "scripts/run_final.sh 단계 1(복제본 r) -> scripts/classify_red.py logs/rg4_r -> write_record_it2b_v2.py"},
            {"name": "IT2b/base_failed_total", "value": 45, "command": "scripts/run_final.sh 단계 1, 복제본 r"},
            {"name": "IT2b/head_changed_files_passed", "value": 185, "command": "scripts/run_final.sh 단계 1, 복제본 h(c4eaa137)"},
            {"name": "IT2b/L12f_prefix_failed", "value": 1, "command": "scripts/run_final.sh 단계 1, 복제본 f(엔진 c4506f47 + c4eaa137 test)"},
            {"name": "IT2b/L12f_prefix_tol_v", "value": 1.1230468750011985e-05, "command": "logs/rg4_f/test_block_columns.txt AssertionError 값"},
            {"name": "IT2b/L12f_expected_last_solution_tol", "value": 1.4599609374998927e-05, "command": "logs/rg4_f/test_block_columns.txt AssertionError 값"},
            {"name": "IT2b/L12f_relative_tolerance_abs_v", "value": 2.919921874999785e-07, "command": "0.02 × tol_last (logs/neg_lut_probe2.jsonl NEG_QV 0.005)"},
            {"name": "IT2b/kmax_cap1_unsettled_cap2_measured", "value": 1, "command": "python -I scripts/neg_lut_probe2.py <p> <최종 test> logs/neg_lut_probe2.jsonl (NEG_QV 0.005: k1 unsettled, k2 measured)"},
            {"name": "IT2b/D_ast_mutants_rejected", "value": 13, "command": "python -I scripts/mutate_d.py <m> logs/mutate_d2.jsonl (변형 17)"},
            {"name": "IT2b/os_outputs_value_match", "value": 12, "command": "scripts/compare_it2b.py os (raw/compare_final.json)"},
            {"name": "IT2b/os_stop_reason_match", "value": 3, "command": "scripts/compare_it2b.py os"},
            {"name": "IT2b/os_output_in_fprime", "value": 0, "command": "measure_it2b.py os.out_in_fprime 13회로 합"},
            {"name": "IT2b/unexplained_changes_9circuits", "value": 0, "command": "python -I scripts/compare_it2b.py out/run <표> <o103 jsonl> raw/compare_final.json"},
            {"name": "IT2b/refactor_431d2e7b_diff_columns_9circuits", "value": 0, "command": "python -I scripts/compare_refactor.py out/run raw/compare_refactor.json"},
            {"name": "IT2b/determinism_equal_circuits", "value": 9, "command": "compare_refactor.py determinism (HEAD2 대 HEAD2_rep2)"},
            {"name": "IT2b/G10_recomputes_same_input_9circuits_head", "value": 0, "command": "compare_it2b.py g10"},
            {"name": "IT2b/nine_tol_v_rows_changed_two_stage_ota_sf", "value": 166, "command": "compare_it2b.py prefix_vs_head evals_matched.tol_v_diff"},
            {"name": "IT2b/endpoint_probe_max_abs_slack_two_stage_ota_sf_head", "value": 6.553045858982698e-06, "command": "measure_it2b.py probes"},
            {"name": "IT2b/full_suite_passed_head", "value": 10356, "command": "bash scripts/run_final.sh 단계 3 (junit 합)"},
            {"name": "IT2b/solve_calls_nmcnr_search_head_vs_refactor", "value": 1, "command": "compare_refactor.py n_solve 157 -> 156"},
            {"name": "IT2b/perf_solve_per_dc_columns_nmcnr_base", "value": 7, "command": "python -I scripts/perf_it2b.py b BASE nmcnr_amplifier raw/perf/theta_nmcnr_amplifier.json"},
            {"name": "IT2b/perf_solve_per_dc_columns_nmcnr_head", "value": 4, "command": "python -I scripts/perf_it2b.py h HEAD nmcnr_amplifier raw/perf/theta_nmcnr_amplifier.json"},
            {"name": "IT2b/perf_same_arg_repeat_it2b_new_functions", "value": 0, "command": "perf_it2b.py calls (_measure·_tolerance·region_rows·input_windows·_solve, 회로 둘)"},
        ],
        "approvals": ["20261021-it2-o67-scope"],
        "auditor_run": {
            "time": "2026-10-22T19:30:00+09:00",
            "worktree": "격리 복제본 wt/_scratch_it2b_audit/h(병합본 c4eaa137 = role/code/it2b c40ad4ea 병합), b(엔진 base 56080584), r(56080584 + c4eaa137 test 파일 여섯), f(엔진 c4506f47 + c4eaa137 test -- L12 (f) red·PREFIX 측정), m(dc334fef = 엔진 615ef68b -- HEAD 측정·D 변형), p(c4eaa137 -- test 상수 탐침), 모두 --no-local 복제 뒤 remote 제거, 변형·탐침 뒤 원문 복원(git status 깨끗)",
            "commands": [
                "V1: bash scripts/run_final.sh 단계 3 = test 파일마다(find gmid_engine/tests -name 'test_*.py' -not -path '*/fixtures/*') C:/Python314/python.exe scripts/run_one.py junit/<n>.xml <file> (pytest.main -p no:cacheprovider -q -rfE --tb=short --run-slow), skills/analog-gmid-design, 순차, @c4eaa137",
                "git -C wt/it2b-audit merge --no-ff -F <msg> 27f58cc4 / c4506f47 / 615ef68b / 1a0e10bb / c40ad4ea (Co-Authored-By·Claude-Session 트레일러)",
                "git -c core.longpaths=true clone -q --no-hardlinks --no-local wt/it2b-audit wt/_scratch_it2b_audit/{h,b,r,m,f,p} && git -C <clone> remote remove origin",
                "bash scripts/run_final.sh 단계 1(바뀐 test 파일 다섯 r·f·h) -> python -I scripts/classify_red.py logs/rg4_r raw/red_classified_rg4.json",
                "python -I scripts/mutate_d.py <m> logs/mutate_d2.jsonl; python -I scripts/neg_lut_probe.py <m> logs/neg_lut_probe.jsonl; python -I scripts/neg_lut_probe2.py <p> <최종 test> logs/neg_lut_probe2.jsonl",
                "bash scripts/run_all.sh + run_final.sh 단계 2 = python -I scripts/measure_it2b.py <clone> <BASE|PREFIX|HEAD|HEAD2> <회로> library out/run [--tag _rep2] (eval_budget 40, 탐침 6); heldout 4 + two_stage_ota_sf --os-only",
                "python -I scripts/compare_it2b.py out/run <de1_output_structure_13.md> <o103 yends_9circuits_analyst.jsonl> raw/compare_final.json; python -I scripts/compare_refactor.py out/run raw/compare_refactor.json",
                "bash scripts/run_perf.sh = python -I scripts/perf_it2b.py <b|h> <BASE|HEAD> <common_gate_amplifier|nmcnr_amplifier> raw/perf/theta_<회로>.json raw/perf/perf_<판>_<회로>.json --reps 7",
                "C:/Python314/python.exe -m pytest -p no:cacheprovider -q --tb=line -m structure_test_mapping gmid_engine/tests/structure/test_structure_test_mapping.py (h·b)",
                "git -C h grep -n dc_output_structure|_edges|saturation_window(|_refine_ends|input_status -- gmid_engine ':!gmid_engine/tests'",
            ],
        },
        "red": {"test_ids": ids, "failure_hashes": hashes},
    }
    with open(sys.argv[2], "wb") as f:
        f.write(json.dumps(rec, ensure_ascii=False, indent=1).encode("utf-8"))
    print(len(ids), "red")


if __name__ == "__main__":
    main()
