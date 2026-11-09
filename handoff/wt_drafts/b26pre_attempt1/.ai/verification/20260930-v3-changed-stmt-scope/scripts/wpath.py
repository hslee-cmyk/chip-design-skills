import subprocess, role_paths as rp
plan = subprocess.run(["git","-C","C:/g244/iso","show","4a286f0:docs/01-plan/features/gain-budget-gmid-sizing.plan.md"],capture_output=True,check=True).stdout.decode("utf-8")
rules = rp.read_write_paths(plan)
rules = rules[0] if isinstance(rules, tuple) and rules and isinstance(rules[0], list) else rules
paths = ["tools/gates/redteam/attacks/35-v3-changed-scope/expect.json","tools/gates/redteam/attacks/35-v3-changed-scope/run.sh","tools/gates/redteam/attacks/35-v3-changed-scope/v.json"]
for p in paths:
    hits = [(r.actor, r.glob, getattr(r,"condition",None)) for r in rules if rp.match_glob(r.glob, p, "20260930-v3-changed-stmt-scope")]
    print(p, hits)
