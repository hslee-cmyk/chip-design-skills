"""V2 ⑤ 사본 준비: <rev>의 skills/analog-gmid-design/assets·skills/analog-grammar·docs/01-plan을 git archive로 풀고 T의 새 test blob을 더한다.
argv: <복제본> <rev> <대상 폴더> <T>"""
import io
import os
import subprocess
import sys
import tarfile

root, rev, dst, T = sys.argv[1:5]
assert not os.path.exists(dst), dst
os.makedirs(dst)
paths = ["skills/analog-gmid-design/assets", "skills/analog-grammar", "docs/01-plan"]
data = subprocess.run(["git", "-C", root, "archive", rev] + paths, capture_output=True, check=True).stdout
tarfile.open(fileobj=io.BytesIO(data)).extractall(dst, filter="data")
F = "skills/analog-gmid-design/assets/tests/contracts/test_b26pre_existing_paths.py"
assert not os.path.exists(os.path.join(dst, F)), "rev에 이미 새 test가 있다"
blob = subprocess.run(["git", "-C", root, "show", "%s:%s" % (T, F)], capture_output=True, check=True).stdout
open(os.path.join(dst, F), "wb").write(blob)
print(rev, dst, "ok", len(blob))
