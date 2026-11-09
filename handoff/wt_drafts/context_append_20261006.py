"""Append context_append_20261006.md to a given .ai/context.md by binary append.

Usage: python context_append_20261006.py <path/to/.ai/context.md>

- Never rewrites the target: opens with 'ab' and writes the block bytes only.
- Refuses if the target does not end with b"\n", if the block contains b"\r",
  or if the block's first line is already present (double-append guard).
- After writing, asserts new bytes == original bytes + block (original is an exact
  prefix -> deletion 0), and prints sizes/line counts.
"""
import hashlib
import sys
from pathlib import Path

BLOCK = Path(__file__).with_name("context_append_20261006.md")
MARKER = "- 백로그 추가(2026-10-06, ".encode("utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    target = Path(sys.argv[1])
    block = BLOCK.read_bytes()
    block.decode("utf-8")  # must be valid UTF-8
    if b"\r" in block:
        print("ERROR: block contains CR")
        return 1
    if not block.startswith(b"\n") or not block.endswith(b"\n"):
        print("ERROR: block must start and end with LF")
        return 1

    orig = target.read_bytes()
    if not orig.endswith(b"\n"):
        print("ERROR: target does not end with LF")
        return 1
    if MARKER in orig:
        print("ERROR: block marker already present in target (already appended?)")
        return 1

    with open(target, "ab") as f:
        f.write(block)

    new = target.read_bytes()
    assert new[: len(orig)] == orig, "original bytes are not an exact prefix"
    assert new == orig + block, "new file != original + block"
    print(f"orig  {len(orig)} bytes, {orig.count(b'\n')} lines, sha256 {hashlib.sha256(orig).hexdigest()[:16]}")
    print(f"block {len(block)} bytes, {block.count(b'\n')} lines")
    print(f"new   {len(new)} bytes, {new.count(b'\n')} lines, sha256 {hashlib.sha256(new).hexdigest()[:16]}")
    print("OK: original is exact prefix (deletion 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
