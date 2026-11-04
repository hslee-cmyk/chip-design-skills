"""IT-1 판정 기록 둘째 판(41faebe0: I4 수정·옛 문언·3b 기준선 반영 뒤). 기존 기록을 읽어 바뀐 칸만 고친다."""
import json
import sys

path = sys.argv[1]
rec = json.load(open(path, encoding="utf-8"))
c = rec["checks"]
c["V1"] = {"verdict": "FAIL", "basis": (
    "미완(코드 결함 판정 아님) -- 41faebe0 짧은 경로 격리 복제본(Temp/claude/it1f)에서 최상위 test 디렉터리별 순차 실행(-k·--deselect·-x 없음) 중 "
    "시스템 메모리 부족으로 하네스가 lut 디렉터리 실행 중(240 통과 시점) 중단시킴(두 번째 중단). 끝난 단위 8개 전부 green: "
    "test_conftest_slow_marker 2/2, authoring 1547/1547, convergence 96/96, core 1085/1085, generality 802/802, graph 1934/1934, "
    "integration 471/471(u17_1b S0 기준선 test 포함, 설정의 19 deselected는 conftest 자체 규칙), layout 527 passed + 2 xfailed/529 "
    "= 6466/10290 완료, failed 0. 미완 3824: lut 1049(중단), metrics 1213, pipeline 84, search 579, sizing 832, structure 67. "
    "IT-1 관련 sizing test는 앞선 짧은 경로 실행(bd468eaf)에서 IT-1 14개 green -- 이 HEAD의 전체 판정은 재실행 필요.")}
c["V6"] = {"verdict": "PASS", "basis": (
    "잔재(완료 조건 3, 계획 1438행 패턴 P) 41faebe0: 엔진(tests 제외) 6줄 = 확정 제외 3(_spec_fields:33·composite_diode:1·metrics CONTRACT:312) "
    "+ 부정문 새 규칙 3(sizing/CONTRACT.md:310·writer_plan.py:10 \"'같은 DC' 엣지는 없다\", sizing/CONTRACT.md:887 'IT-1 규칙대로 ... 같은 DC 엣지·input_tie 없음' "
    "-- ee3d8187이 옛 문언을 고치며 새로 생긴 부정문, 제외 사유 같음). 옛 문언 4줄(CONTRACT:427·887·s2_values:186·seal_node_conflict:6) 수정 확인, 남은 잔재 0. "
    "tests 줄은 IT-1 부재 단언·주석(제거 확인용).")}
c["V5"]["basis"] += (" [둘째 판] 3b(aa3d1075): u17_1b_s0_baseline.json blob 28줄 +/- 28줄, 크기 50552 바이트 동일, CR 0 -- 바뀐 JSON 경로 정확히 28개 = "
                     "achievability_sha/dof 6(current_reuse·folded·ngcc·nmcnr·two_stage·two_stage_sf, R2) + kernel/schema_fp·search_domain_fp 12 + "
                     "start/uncovered_fp 6(R3 y 키·R1) + start/ladder_fp 4(folded·nmcnr·two_stage·two_stage_sf, R1 새 writer ln_idu) -- 변화표·앞선 실패 목록과 일치, "
                     "다른 키 변화 0. test_current_basis: _BASELINE_8E46548_ORIGINAL 원값 그대로 두고 _IT1_DELTA(감사 Δ 6개와 같음)를 더하는 꼴, 단언 == 정확 일치 유지 -- 약화 아님.")
c["V10"]["basis"] = (c["V10"]["basis"].replace("graph 정본 I4 결함 1건은 change_table_summary.json graph_check 참조.",
                     "graph 정본 I4는 ee3d8187에서 key = (THETA_Y, c.writers[roots[0]].y_key)로 수정 확인(정본 우회 의심 0).")
                     + " folded_cascode start.uncovered: base [..., (y,Y), (y,input_common_mode), (y,out)] -> HEAD [..., (y,Y), (y,out), (y,vin_p)] -- "
                       "이름 치환 뒤 집합 같음, 두 목록 모두 (종류, 이름) 정렬이라 vin_p가 out 뒤로 감; probe_diff의 false는 순서 민감 비교 탓. 원인 R3, 미설명 아님.")
for r in rec["reproduced_numbers"]:
    if r["name"] == "residue/pattern_P/stale_lines_after_exclusions":
        r["value"] = 0
        r["command"] = "git grep -nE <P> -- gmid_engine ':!gmid_engine/tests' @41faebe0 - 확정 제외 3 - 부정문 3"
    if r["name"] == "residue/pattern_P/engine_non_test_lines":
        r["value"] = 6
    if r["name"] == "graph/canonical_bypass_suspect":
        r["value"] = 0
        r["command"] = "block_columns.py _solve_input_window @41faebe0: key = (THETA_Y, c.writers[roots[0]].y_key)"
rec["reproduced_numbers"] = [r for r in rec["reproduced_numbers"] if not r["name"].startswith("v1/partial/")]
fcmd = "cd <it1f @41faebe0>/skills/analog-gmid-design && C:/Python314/python.exe -m pytest -p no:cacheprovider -q -rfE --junitxml=<out>/junit_<d>.xml <d>"
rec["reproduced_numbers"] += [
    {"name": "v1/41faebe0/collected", "value": 10290, "command": "C:/Python314/python.exe -m pytest -p no:cacheprovider -q --collect-only"},
    {"name": "v1/41faebe0/completed_green", "value": 6466, "command": fcmd},
    {"name": "v1/41faebe0/failed", "value": 0, "command": fcmd},
    {"name": "v1/41faebe0/not_completed", "value": 3824, "command": fcmd},
    {"name": "3b/baseline_json_changed_paths", "value": 28, "command": "json 경로 비교 git show bd468eaf:<fixture> 대 41faebe0"},
]
rec["auditor_run"]["time"] = "2026-10-22T12:00:00+09:00"
rec["auditor_run"]["worktree"] += "; 둘째 판: Temp/claude/it1f(@41faebe0, remote 제거)"
rec["auditor_run"]["commands"][0] = ("V1: cd <it1f @41faebe0>/skills/analog-gmid-design && for d in <최상위 test 디렉터리 14 단위>; "
                                     "C:/Python314/python.exe -m pytest -p no:cacheprovider -q -rfE --junitxml=junit_<d>.xml <d> "
                                     "(순차; 메모리 부족으로 lut 실행 중 중단)")
with open(path, "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)
print("ok")
