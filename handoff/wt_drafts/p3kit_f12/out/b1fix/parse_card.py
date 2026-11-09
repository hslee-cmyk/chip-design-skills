import hashlib
import json
import sys
sys.path.insert(0, r"C:\g347\gt\tools\gates")
import role_paths as rp  # gate 6c724de copy (git archive)

p = r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts\draft_p3_f1.spec.md"
b = open(p, "rb").read()
card = rp.parse_spec_card(b.decode("utf-8"), expect_id="20261002-p3-callers-update")
print(json.dumps({k: (v if not isinstance(v, (set, frozenset)) else sorted(v)) for k, v in card.items()
                  if k in ("id", "phase", "evidence_type", "gate_change", "approval", "approvals", "signatures")},
                 ensure_ascii=False, default=str)[:800])
print("keys", sorted(card.keys()))
print("sha256", hashlib.sha256(b).hexdigest(), "bytes", len(b), "lines", b.count(b"\n"))
