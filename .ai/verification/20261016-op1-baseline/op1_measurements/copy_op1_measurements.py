# -*- coding: utf-8 -*-
"""OP-1 측정 산출물(design S-12~S-22가 인용하는 `wt/_scratch_op1/{results,scripts,runs}`와 검증자 초안 둘)을 바이트 그대로 복사하고
sha256 목록을 쓴다(검증자 작성). baseline/(원자료)와 __pycache__는 제외한다.
사용: python -I copy_op1_measurements.py <wt/_scratch_op1> <이 폴더>"""
import hashlib
import os
import shutil
import sys

SRC, DST = sys.argv[1:3]
rows = []
for root, dirs, files in os.walk(SRC):
    rel_root = os.path.relpath(root, SRC).replace("\\", "/")
    if rel_root == "baseline" or rel_root.startswith("baseline/"):
        dirs[:] = []
        continue
    dirs[:] = sorted(d for d in dirs if d != "__pycache__" and not (rel_root == "." and d == "baseline"))
    for f in sorted(files):
        p = os.path.join(root, f)
        rel = os.path.relpath(p, SRC).replace("\\", "/")
        q = os.path.join(DST, "files", rel)
        os.makedirs(os.path.dirname(q), exist_ok=True)
        shutil.copyfile(p, q)
        with open(p, "rb") as fh:
            data = fh.read()
        rows.append((rel, len(data), hashlib.sha256(data).hexdigest()))
with open(os.path.join(DST, "_sha256.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("rel\tsize\tsha256\n")
    for r in rows:
        f.write("%s\t%d\t%s\n" % r)
print(len(rows), sum(r[1] for r in rows))
