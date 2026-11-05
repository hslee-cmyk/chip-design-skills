"""A-107 수정 뮤턴트: 복사본에서 새 조건·새 판정을 되돌려 새 test 가 잡는지. 결과 파일."""
import json
import os
import pathlib
import subprocess
import sys

root = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONUTF8="1", APPDATA="C:/Users/HSLEE/AppData/Roaming", USERPROFILE="C:/Users/HSLEE", PYTHONPYCACHEPREFIX=str(root.parent / "pyc_mut"))
T = "gmid_engine/tests/metrics/"
muts = [
    ("대조", None, None, None, [T + "test_block_model.py", T + "test_sensitivity_gate.py"]),
    ("막다른 규칙 용량 독자 뺌", "metrics/block_model.py", " and n not in read and count[n] == 1", " and count[n] == 1", [T + "test_block_model.py"]),
    ("용량 독자를 모든 C 넷으로(과잉 제외)", "metrics/block_model.py", "if o in charge}", "}", [T + "test_block_model.py", T + "test_block_residual.py"]),
    ("gate _finite 가 None 만", "metrics/sensitivity_gate.py", "return value is not None and math.isfinite(value)", "return value is not None", [T + "test_sensitivity_gate.py"]),
]
rows = []
for name, rel, old, new, tests in muts:
    text = None
    if rel:
        path = root / "gmid_engine" / rel
        text = path.read_bytes().decode("utf-8")
        assert old in text, name
        path.write_bytes(text.replace(old, new, 1).encode("utf-8"))
    p = subprocess.run([sys.executable, "-m", "pytest", *tests, "-q", "--tb=line", "-p", "no:cacheprovider", "-W", "ignore"], cwd=root, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if rel:
        path.write_bytes(text.encode("utf-8"))
    rows.append({"name": name, "rc": p.returncode, "last": p.stdout.strip().splitlines()[-1][:160], "failed": [l[:110] for l in p.stdout.splitlines() if l.startswith("FAILED")][:4]})
    print(rows[-1], flush=True)
out.write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding="utf-8")
