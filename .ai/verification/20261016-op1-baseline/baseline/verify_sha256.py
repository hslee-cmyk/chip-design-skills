# -*- coding: utf-8 -*-
"""OP-1a 완료 조건 '목록의 sha256으로 원자료 재대조'(검증자 작성).
  raw 모드:       python -I verify_sha256.py raw <원자료 루트(wt/_scratch_op1/baseline)>
                  -> 원자료 전 파일 집합이 _sha256_all.tsv와 같고 파일마다 크기·sha256이 같은지
  committed 모드: python -I verify_sha256.py committed <이 baseline 폴더의 files/ 경로>
                  -> committed=1 행의 파일이 files/ 아래에 있고 크기·sha256이 같으며 files/에 목록 밖 파일이 없는지
출력: JSON 한 줄(n_rows, n_checked, missing, extra, mismatched)."""
import hashlib
import json
import os
import sys

MODE, ROOT = sys.argv[1:3]
here = os.path.dirname(os.path.abspath(__file__))
rows = []
with open(os.path.join(here, "_sha256_all.tsv"), encoding="utf-8") as f:
    next(f)
    for ln in f:
        rel, size, s, cls, committed = ln.rstrip("\n").split("\t")
        rows.append((rel, int(size), s, cls, committed == "1"))
want = {r[0]: r for r in rows if MODE == "raw" or r[4]}
have = set()
for root, _, files in os.walk(ROOT):
    for fn in files:
        have.add(os.path.relpath(os.path.join(root, fn), ROOT).replace("\\", "/"))
missing = sorted(set(want) - have)
extra = sorted(have - set(want))
bad = []
for rel in sorted(set(want) & have):
    p = os.path.join(ROOT, rel)
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    if h.hexdigest() != want[rel][2] or os.path.getsize(p) != want[rel][1]:
        bad.append(rel)
print(json.dumps({"mode": MODE, "n_rows": len(rows), "n_checked": len(set(want) & have), "missing": missing[:20], "n_missing": len(missing),
                  "extra": extra[:20], "n_extra": len(extra), "mismatched": bad[:20], "n_mismatched": len(bad),
                  "ok": not missing and not extra and not bad}, ensure_ascii=False))
