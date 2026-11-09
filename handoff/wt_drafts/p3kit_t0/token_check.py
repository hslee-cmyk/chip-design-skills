"""T0 계약 9 점검(측정 전용): base..T의 바뀐 test 파일 `+` 줄에 전수 스캔 test 금지 토큰이 식별자·문자열로 나오는지.

    C:/Python314/python.exe -B token_check.py <복제본> <base> <T> <출력 JSON>

토큰 목록은 base 트리의 test_d_delete_dead·test_d_delete_telescopic·test_d_move_tests 상수에서 **다시 뽑는다**(card 계약 9 목록과 대조)
+ test_ts3_no_print_verdicts의 print/logging 인자 안 PASS·FAIL.
"""
import ast
import json
import re
import subprocess
import sys

ROOT, BASE, HEAD, OUT = sys.argv[1:5]
C = "skills/analog-gmid-design/assets/tests/contracts/"
CARD9 = {"converge_with_parasitics", "render_stick_diagram", "slew_rate", "suggest_headroom_stack_groups", "fT", "junction_cap",
         "_cmfb_amp_gain_diode_load", "_cmrr_telescopic_class_ab", "_cmrr_telescopic_class_ab_cmfb", "_load_telescopic_topology_cached",
         "_psrr_telescopic_class_ab", "_psrr_telescopic_class_ab_cmfb", "_telescopic_class_ab_open_loop_gains",
         "_telescopic_class_ab_open_loop_response", "_telescopic_open_loop_device_names", "_TELESCOPIC_FIXED_BASE",
         "_open_loop_gains_cache", "RegressionVerdict", "_REGRESSION_ENGINES", "_run_optimize_multistage_case",
         "find_interleaved_symmetric_splits", "run_regression_case", "regression_runner", "interleave_splits"}


def git(*a):
    return subprocess.run(["git", "-C", ROOT] + list(a), capture_output=True, check=True).stdout.decode("utf-8")


names = git("diff", "--name-only", BASE, HEAD).split()
plus = [l[1:] for l in git("diff", "-U0", BASE, HEAD, "--", *names).splitlines() if l.startswith("+") and not l.startswith("+++")]
words = set()
for l in plus:
    words |= set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", l))
hits = sorted(CARD9 & words)
pf = [l for l in plus if re.search(r"\b(print|log|logger|logging)\b", l) and re.search(r"PASS|FAIL", l)]
res = {"changed_files": names, "plus_lines": len(plus), "card9_token_hits": hits, "print_pass_fail_lines": pf}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False))
