"""A-34: 두 structure.json 의 rule_hash 줄만 바이트 치환. 인자: 저장소 루트, 옛 값, 새 값."""
import sys
from pathlib import Path

root, old, new = sys.argv[1:4]
for n in ("current_reuse_telescopic_ota", "nmcnr_amplifier"):
    p = Path(root) / "skills/analog-gmid-design/assets/library" / (n + ".structure.json")
    b = p.read_bytes()
    key = ('"rule_hash": "%s"' % old).encode()
    assert b.count(key) == 1, n
    p.write_bytes(b.replace(key, ('"rule_hash": "%s"' % new).encode()))
print("ok")
