"""base 판 게이트(C:/g244/gate, PYTHONPATH 맨 앞, -P)로 승인 target 재계산·approved_hashes·red_failure_hash."""
import json, sys
import weakening_diff as wd
import merge_gate as mg

ROOT = "C:/g244/iso"
paths = [
    "docs/01-plan/features/gain-budget-gmid-sizing.plan.md",
    "docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md",
    "docs/02-design/specs/20260930-v3-changed-stmt-scope.interface.md",
    "docs/02-design/specs/20260930-v3-changed-stmt-scope.spec.md",
]
h = wd.diff_hash(ROOT, "36e170eec5b9e893c03927e5bb45635071de7e69", "a6a7e342627d72b8fc2c79844f69da7930333520", paths)
appr = wd.approved_hashes(ROOT, "4a286f0fad4f9beafd26647e1f95a89086e07919")
rec = "25f2ba19de7952abd3779fc5984e448d04b5f0f2ac8787b877ec0d215dc2bda6"
out = {"target_recomputed": h, "target_in_record": rec, "match": h == rec,
       "in_approved_hashes_at_base": (h in appr) if not isinstance(appr, dict) else (h in appr or h in appr.values()),
       "approved_type": type(appr).__name__,
       "weakening_diff_file": wd.__file__, "merge_gate_file": mg.__file__}
print(json.dumps(out, ensure_ascii=False, indent=1))
