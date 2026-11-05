# -*- coding: utf-8 -*-
"""A-6: git 객체 바이트의 sha256을 _sha256_all.tsv와 직접 대조. 사용: blobcheck.py <worktree> <rev 접두, ':' = 색인 또는 'HEAD:'>"""
import hashlib, json, subprocess, sys
W, REV = sys.argv[1:3]
P = ".ai/verification/20261104-op1b/baseline/"
n = bad = 0
badl = []
with open(f"{W}/{P}_sha256_all.tsv", encoding="utf-8") as f:
    next(f)
    for ln in f:
        rel, size, s, cls, c = ln.rstrip("\n").split("\t")
        if c != "1":
            continue
        b = subprocess.run(["git", "-C", W, "cat-file", "blob", f"{REV}{P}files/{rel}"], capture_output=True, check=True).stdout
        n += 1
        if hashlib.sha256(b).hexdigest() != s or len(b) != int(size):
            bad += 1
            badl.append(rel)
print(json.dumps({"rev": REV, "n_checked": n, "n_mismatched": bad, "mismatched": badl[:10]}))
