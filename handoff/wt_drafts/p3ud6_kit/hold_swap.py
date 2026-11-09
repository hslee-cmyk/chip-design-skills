"""measure only: D0b contract 7 stand-in -- every `보류(Phase 3)` in the registry becomes `보류(Phase 4)` (count printed)."""
import sys

p = sys.argv[1]
raw = open(p, encoding="utf-8", newline="").read()
n = raw.count("보류(Phase 3)")
open(p, "w", encoding="utf-8", newline="").write(raw.replace("보류(Phase 3)", "보류(Phase 4)"))
print("hold_swap", n, "-> Phase 4; Phase 4 now", raw.replace("보류(Phase 3)", "보류(Phase 4)").count("보류(Phase 4)"))
