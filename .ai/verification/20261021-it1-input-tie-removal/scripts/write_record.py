import hashlib
import json
import sys

out = sys.argv[1]
P = "skills/analog-gmid-design/gmid_engine/tests/sizing/test_writer_plan.py::"
red = [("test_it1_undeclared_diffpair_no_input_tie", "AssertionError"),
       ("test_it1_ring_cycle_vgs_after_port_delta_elimination", "AssertionError"),
       ("test_it1_dependent_count_equals_cycle_rank[diff_undeclared]", "AssertionError"),
       ("test_it1_dependent_count_equals_cycle_rank[ring_undeclared]", "AssertionError"),
       ("test_it1_multiple_input_roots_stop[two_components]", "Failed(DID NOT RAISE StructureUnresolvedError)"),
       ("test_it1_multiple_input_roots_stop[isolated_plus_component]", "Failed(DID NOT RAISE StructureUnresolvedError)"),
       ("test_it1_vocabulary_removed", "AssertionError"),
       ("test_it1_renamed_diffpair_same_structure", "AssertionError"),
       ("test_it1_theta_schema_y_components_follow_writers", "AssertionError"),
       ("test_it1_writer_block_owns_plan_fields", "AssertionError")]
ids = [P + t for t, _ in red]
hashes = [hashlib.sha256((P + t + "|" + e).encode()).hexdigest() for t, e in red]
cmd_base = ("cd <it1-base @0366ddb4>/skills/analog-gmid-design && C:/Python314/python.exe -m pytest -p no:cacheprovider -q -rA "
            "--tb=line gmid_engine/tests/sizing/test_writer_plan.py -k test_it1_")
cmd_tgt = ("cd <it1s @bd468eaf>/skills/analog-gmid-design && C:/Python314/python.exe -m pytest -p no:cacheprovider -q -rA --tb=short "
           "gmid_engine/tests/sizing/test_writer_plan.py gmid_engine/tests/sizing/test_current_basis.py "
           "gmid_engine/tests/integration/test_s0_layer_9circuits.py gmid_engine/tests/search/test_orbit_ties.py "
           "gmid_engine/tests/sizing/test_s2_values.py")
checks = {
    "V1": ("FAIL", "미완(코드 결함 판정 아님) -- 병합본 bd468eaf 전체 실행(-k·--deselect·-x 없음)이 시스템 메모리 부족으로 하네스에 의해 "
           "88.6%(9122/10290 수집) 지점에서 중단됨. 실행분: 통과 9072, F 48, xfail 2. F 48 = (가) authoring 36(test_topology_load 등) -- "
           "긴 복제본 경로(MAX_PATH) FileNotFoundError 환경 산물, 짧은 경로 복제본에서 106 passed 확인(base 복제본도 같은 원인 38 F) "
           "(나) integration/test_s0_layer_9circuits 12 -- S0 기준선 u17_1b_s0_baseline.json, 커밋 3b 대기(승인 o13-scope). "
           "미실행 1168개 중 IT-1 관련 230개를 짧은 경로 복제본에서 따로 실행: 18 failed = test_current_basis 8e46548 6 + s0_layer 12(모두 3b 대기), "
           "212 passed(IT-1 test 14 포함). 전체 재실행 필요(logs/v1_partial_failures.txt·logs/targeted_head.txt)."),
    "V2": ("PASS", "red-green: base 0366ddb4(코드 = e98d0b0f, 비 test diff 0)에서 IT-1 test 14개 중 10개가 assertion으로 FAIL(AssertionError 8, "
           "pytest.raises DID NOT RAISE 2), 4개 green(무동작 성질 (c) declared 2·declared_input_plan_unchanged·isolated_single_root_builds -- card와 일치). "
           "HEAD bd468eaf에서 14개 모두 PASS. 사유 대조: diff 2==1·ring 6==5(종속 수 = 순환 수), 정지 미발생, REL_TIE 존재, y 키 input_common_mode, "
           "dc_columns READS port_direction 부재(logs/red_base.txt)."),
    "V3": ("N/A", "도입 해당 없음(DEC-86): merge_gate·mutate_changed 미사용, N6.3 절차라 이 판정에서 재지 않음."),
    "V4": ("PASS", "oracle 대조: IT-1 test 기대값은 손계산(toy 순환 수·뿌리 넷 이름·정지 detail 꼴)이고 피검 함수 출력 복사가 아님(test_writer_plan.py 338-525 읽기). "
           "결정성: HEAD 측정 두 번(raw/IT1 대 raw/IT1_rep2) 차이 = wall_s·tag·m_i3.perf.eval_time_median_s 시간 칸뿐(8회로)."),
    "V5": ("PASS", "기준 약화 0: diff e98d0b0f..bd468eaf test 12파일 모두 승인 범위(o13-scope 10파일 + k3-ext test_orbit_ties·test_s2_values:148). "
           "skip/xfail/importorskip 추가 0, 리터럴 완화 0. 지운 assert 줄 11개 모두 대체: test_writer_plan 4줄 -> 3줄(M1·M2 둘 다 writer 단언), "
           "test_s2_values 어휘 -> 부재 단언 + BRANCH 상수 단언, scc_newton·input_window·size_and_seal_local·block_columns는 y 키 이름만, "
           "orbit_ties 대칭 단언 6개 유지 + 정지 단언 1 추가(k3-ext #3). test_current_basis·S0 기준선은 미변경(3b)."),
    "V6": ("FAIL", "잔재(완료 조건 3, 계획 1438행 패턴 P, gmid_engine 전체): HEAD 27줄 = 엔진 9 + tests 18. 식별자 잔재 엔진 코드 0, 같은 DC 엣지 코드 0. "
           "확정 제외 3줄 확인. 추가 제외 제안 2줄(부정문 새 규칙: sizing/CONTRACT.md:310, writer_plan.py:10). 남는 옛 문언 4줄 = 결함: "
           "sizing/CONTRACT.md:427('입력 묶음 전원'), sizing/CONTRACT.md:887('U2 기본안 (a)대로 W4(입력 공통모드 y)'), sizing/s2_values.py:186 "
           "docstring('U2 기본안 (a) W4'), sizing/seal_node_conflict.py:6 docstring('같은 DC'). tests 18줄은 IT-1 부재 단언·주석(제외 사유 = 제거 확인)."),
    "V7": ("PASS", "배선: BRANCH_INPUT_MULTIPLE_ROOTS는 dc_writer_plan 정지 자리(writer_plan.py:223-227) 운영 경로에서 쓰임(library 발동 0, toy·d/s 뒤집은 toy 발동). "
           "dc_columns READS node.port_direction은 _Circuit.inputs(block_columns.py:178)가 읽어 input_roots()·_solve_input_window가 소비."),
    "V8": ("N/A", "도입 해당 없음: IT-1 diff에 폴백 경로 없음."),
    "V9": ("PASS", "library 8회로(ngcc는 단계 A review_needed라 IT-0 하네스 밖, 탐침으로 따로 잼) 종속 수 = 같은 DC 엣지 없는 G_vgs(F 한 점) 순환 수(M-I6 equal true, tie_edges 0). "
           "achievability n_equations 감소 = 옛 tie: 등식 수 1과 정확 일치, n_variables·status free_dof 불변."),
    "V10": ("PASS", "9회로 변화표(change_table.json + probe_diff.json): 설명 안 된 변화 0. 변화 7회로(2입력 6 + common_gate y 키 이름만), 무변화 2(입력 DC 선언). "
            "HEAD 쓰기 계획 = IT-0 SIM 필드별 같음. BASELINE_8E46548 Δ 6개 재현(reproduced_numbers). graph 정본 I4 결함 1건은 change_table_summary.json graph_check 참조."),
}
cmdp = "C:/Python314/python.exe -I scripts/probe_s0.py <repo> out/probe_head.json (test_current_basis._measured_domain 과 같은 경로)"
rn = []
for n, v in [("current_reuse_telescopic_ota", (30, 38)), ("folded_cascode", (0, 17)), ("ngcc_3stage_ff", (0, 22)),
             ("nmcnr_amplifier", (0, 24)), ("two_stage_ota", (0, 11)), ("two_stage_ota_sf", (0, 13)),
             ("common_gate_amplifier", (0, 6)), ("pushpull_follower_buffer", (0, 8)), ("sf_pushpull_output_opamp", (0, 26))]:
    rn.append({"name": "8E46548/%s/ties" % n, "value": v[0], "command": cmdp})
    rn.append({"name": "8E46548/%s/variables" % n, "value": v[1], "command": cmdp})
rn += [{"name": "change_table/library9/unexplained", "value": 0, "command": "C:/Python314/python.exe -I scripts/compare_it1.py; scripts/diff_probe.py"},
       {"name": "red/base/assertion_failures", "value": 10, "command": cmd_base},
       {"name": "head/it1_tests_passed", "value": 14, "command": cmd_tgt},
       {"name": "residue/pattern_P/engine_non_test_lines", "value": 9, "command": "git grep -nE <P> -- skills/analog-gmid-design/gmid_engine ':!skills/analog-gmid-design/gmid_engine/tests'"},
       {"name": "residue/pattern_P/stale_lines_after_exclusions", "value": 4, "command": "위 결과 - 확정 제외 3 - 부정문 2"},
       {"name": "graph/field_count_changed", "value": 3, "command": "node.dc_writer·device.dc_coord·graph.dc_tie_breaks (새 필드 0)"},
       {"name": "graph/consumer_zero", "value": 0, "command": "grep READS -- dc_tie_breaks는 IT-1 전부터 엔진 소비자 0(결과 기록 전용, 변화 아님)"},
       {"name": "graph/canonical_bypass_suspect", "value": 1, "command": "block_columns.py _solve_input_window: key = (THETA_Y, roots[0]) -- y_key 필드 대신 넷 이름(I4)"},
       {"name": "graph/kvl_kcl_relation_not_applied", "value": 0, "command": "writer_plan·block_columns diff 읽기"},
       {"name": "graph/storage_outside_graph", "value": 0, "command": "git diff e98d0b0f bd468eaf 엔진 + 줄 grep cache|memo|dict|sctx"},
       {"name": "v1/partial/executed", "value": 9122, "command": "V1 명령(중단)"},
       {"name": "v1/partial/failed", "value": 48, "command": "V1 명령(중단)"}]
rec = {
    "id": "20261021-it1-input-tie-removal",
    "spec_card": "docs/02-design/specs/20261021-it1-input-tie-removal.spec.md",
    "evidence_type": "red-green",
    "base_commit": "e98d0b0f10cc97d6256c1f4928b2f1f61f63ae44",
    "test_commit": "46cb7bc4d22adceb2a7a73336547ae3ada19dfb7",
    "code_commit": "14e0ca2af4a6de90878682a1d971076431fd3178",
    "red": {"test_ids": ids, "failure_hashes": hashes},
    "checks": {k: {"verdict": v, "basis": b} for k, (v, b) in checks.items()},
    "reproduced_numbers": rn,
    "approvals": ["20261021-it1-o13-scope", "20261021-it1-k3-ext"],
    "auditor_run": {"time": "2026-10-22T00:00:00+09:00",
                    "worktree": "격리 복제본 scratchpad/it1-audit/it1-iso(@bd468eaf, remote 제거), base 복제본 it1-base(@0366ddb4), 짧은 경로 복제본 Temp/claude/it1s(@bd468eaf)",
                    "commands": ["V1: cd <it1-iso>/skills/analog-gmid-design && C:/Python314/python.exe -m pytest -p no:cacheprovider -q -rfE (메모리 부족으로 88.6%에서 중단)",
                                 "git -c core.longpaths=true clone --no-hardlinks --no-local wt/it1-audit <TEMP>/it1-iso && git -C <TEMP>/it1-iso remote remove origin",
                                 cmd_base, cmd_tgt,
                                 "C:/Python314/python.exe -I scripts/measure_it1.py <it1-iso> IT1 <circuit> library|heldout out [--tag _rep2]",
                                 "C:/Python314/python.exe -I scripts/compare_it1.py <IT-0 raw> out out/change_table.json",
                                 "C:/Python314/python.exe -I scripts/probe_s0.py <repo> out/probe_{base,head}.json; scripts/diff_probe.py",
                                 "git grep -nE <계획 1438행 패턴 P> -- skills/analog-gmid-design/gmid_engine"]},
}
with open(out, "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)
print("ok")
