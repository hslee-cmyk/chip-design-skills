"""IT-1 판정 기록 최종 판(41faebe0): V1 = 전체 합집합 green."""
import json
import sys

path = sys.argv[1]
rec = json.load(open(path, encoding="utf-8"))
rec["checks"]["V1"] = {"verdict": "PASS", "basis": (
    "41faebe0 짧은 경로 격리 복제본(Temp/claude/it1f, remote 제거)에서 전체 실행(-k·--deselect·-x 없음, 설정 자체 deselect 20 = integration 19 + structure 1). "
    "메모리 중단을 피하려 단위별로 나눠 순차 실행(동시 pytest 프로세스 1개). 1차(디렉터리 단위): test_conftest_slow_marker 2, authoring 1547, convergence 96, "
    "core 1085, generality 802, graph 1934, integration 471, layout 527 + xfail 2 = 6466. 2차: lut 1049(파일 46개 각각 따로), metrics 1213, pipeline 84, "
    "search 579, sizing 832, structure 67 = 3824. 합 10290 = 수집 10290(junit 테스트 id 대 --collect-only id 대조: 누락 0, 초과 0). "
    "결과: passed 10288, xfailed 2(layout test_patterns_common_centroid 두 개, 기존), failed 0, error 0. "
    "u17_1b S0 기준선(3b)·test_current_basis 8e46548+Δ·IT-1 test 14개 포함 전부 green.")}
rec["checks"]["V6"]["basis"] = rec["checks"]["V6"]["basis"].replace(
    "제외 사유 같음)", "제외 사유 같음 -- 오케스트레이터 승인: 부정문으로 새 규칙(부재)을 적은 줄이라 옛 규칙 잔재 아님)")
rec["reproduced_numbers"] = [r for r in rec["reproduced_numbers"] if not r["name"].startswith("v1/41faebe0/")]
c1 = "cd <it1f @41faebe0>/skills/analog-gmid-design && C:/Python314/python.exe -m pytest -p no:cacheprovider -q -rfE --junitxml=<out>/junit_<u>.xml <u>"
rec["reproduced_numbers"] += [
    {"name": "v1/41faebe0/collected", "value": 10290, "command": "C:/Python314/python.exe -m pytest -p no:cacheprovider -q --collect-only"},
    {"name": "v1/41faebe0/run_union", "value": 10290, "command": c1 + " (1차 디렉터리 8단위 + 2차 lut 파일 46 + 디렉터리 5)"},
    {"name": "v1/41faebe0/passed", "value": 10288, "command": c1},
    {"name": "v1/41faebe0/xfailed", "value": 2, "command": c1},
    {"name": "v1/41faebe0/failed", "value": 0, "command": c1},
    {"name": "v1/41faebe0/coverage_missing", "value": 0, "command": "junit testcase id 합집합 대 collect_all id 대조"},
]
rec["auditor_run"]["time"] = "2026-10-22T18:00:00+09:00"
rec["auditor_run"]["commands"][0] = ("V1: cd <it1f @41faebe0>/skills/analog-gmid-design && C:/Python314/python.exe -m pytest -p no:cacheprovider -q -rfE "
                                     "--junitxml=junit_<u>.xml <u> -- 단위 u = 최상위 test 디렉터리(lut만 파일별), 순차, 합집합 10290 = 수집 전부")
with open(path, "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)
print("ok", {k: v["verdict"] for k, v in rec["checks"].items()})
