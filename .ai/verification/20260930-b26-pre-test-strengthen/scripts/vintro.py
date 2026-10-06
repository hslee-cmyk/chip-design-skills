"""base 판 계획서를 base 판 merge_gate.read_plan_tables_text로 읽어 v_intro를 출력한다. argv: <iso> <base>"""
import subprocess
import sys
import merge_gate as mg
root, base = sys.argv[1:3]
txt = subprocess.run(["git", "-C", root, "show", base + ":docs/01-plan/features/gain-budget-gmid-sizing.plan.md"],
                     capture_output=True, check=True).stdout.decode("utf-8")
pt = mg.read_plan_tables_text(txt)
print({k: pt.v_intro[k] for k in sorted(pt.v_intro)})
