"""T-10a 판별력: members 전달을 끊는 뮤턴트 둘을 test_ub1_block_residual_passes_block_members 하나로만 판정. 결과 파일."""
import json
import os
import pathlib
import subprocess
import sys

root = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONUTF8="1", APPDATA="C:/Users/HSLEE/AppData/Roaming", USERPROFILE="C:/Users/HSLEE", PYTHONPYCACHEPREFIX=str(root.parent / "pyc_mut"))
TEST = "gmid_engine/tests/metrics/test_block_residual.py::test_ub1_block_residual_passes_block_members"
muts = [
    ("대조(변경 없음)", None, None, None),
    ("_structure 가 block.members 를 안 읽음", "metrics/block_model.py", "owners = (set(block.members) | set(extra)) - barred", "owners = set(extra) - barred"),
    ("block_residual 이 members 를 비워 넘김", "metrics/block_residual.py", "found = block_local_gain(ss, block, drive,", "found = block_local_gain(ss, __import__('dataclasses').replace(block, members=()), drive,"),
]
rows = []
for name, rel, old, new in muts:
    text = None
    if rel:
        path = root / "gmid_engine" / rel
        text = path.read_bytes().decode("utf-8")
        assert old in text, name
        path.write_bytes(text.replace(old, new, 1).encode("utf-8"))
    p = subprocess.run([sys.executable, "-m", "pytest", TEST, "-q", "--tb=line", "-p", "no:cacheprovider", "-W", "ignore"], cwd=root, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if rel:
        path.write_bytes(text.encode("utf-8"))
    rows.append({"name": name, "rc": p.returncode, "last": p.stdout.strip().splitlines()[-1][:200]})
    print(rows[-1], flush=True)
out.write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding="utf-8")
