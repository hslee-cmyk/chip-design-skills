"""spec card 머리 블록·절 확인(role_paths.parse_spec_card, 사본 tools/gates에서 읽기 전용 import).
사용: python -B check_header.py <사본 루트> <card 경로> <id>"""
import os, sys

root, card, cid = sys.argv[1:4]
sys.path.insert(0, os.path.join(root, "tools/gates"))
import role_paths as r  # noqa: E402
assert os.path.abspath(r.__file__).replace("\\", "/").startswith(os.path.abspath(root).replace("\\", "/"))
c = r.parse_spec_card(open(card, encoding="utf-8").read(), cid)
print({k: c[k] for k in ("id", "phase", "evidence_type", "gate_change", "approval")})
print(list(c["sections"]))
