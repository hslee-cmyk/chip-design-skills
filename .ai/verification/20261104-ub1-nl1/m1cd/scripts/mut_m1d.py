"""M-1c·M-1d 뮤턴트. usage: mut_m1d.py <mut skill root> <out json>"""
import json
import os
import pathlib
import subprocess
import sys

root = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONUTF8="1", APPDATA="C:/Users/HSLEE/AppData/Roaming", USERPROFILE="C:/Users/HSLEE", PYTHONPYCACHEPREFIX=str(root.parent / "pyc_mut"))
T = "gmid_engine/tests/metrics/"
SET = [T + "test_block_model.py", T + "test__helpers_nodal.py", T + "test_block_residual.py", T + "test_icm_config.py", T + "test_offset_analysis.py"]
muts = [
    ("대조", None, None, None),
    ("확장을 소자 capacitors 만으로", "metrics/block_model.py", "new = {int(t) for t in numpy.flatnonzero(c_pairs[o])} & cap_only - charge", "new = {t for k in ss.circuit.capacitors for t, u in ((k.a, k.b), (k.b, k.a)) if u == o} & cap_only - charge"),
    ("_structure C 조건 없이 조립", "metrics/block_model.py", "    c_full = None  ", "    c_full = capacitance_matrix(ss.circuit, len(ss.nodes))  "),
    ("block_local_gain C 다시 조립", "metrics/block_model.py", "c = c_full if charge else", "c = capacitance_matrix(ss.circuit, size) if charge else"),
    ("charge_seeded 늘 참(nodal_of·view_factor C 조립)", "metrics/_helpers_nodal.py", "return any(not g[i].any() for i in range(g.shape[0]) if i not in fixed_set)", "return True"),
    ("charge_seeded 늘 거짓(물리)", "metrics/_helpers_nodal.py", "return any(not g[i].any() for i in range(g.shape[0]) if i not in fixed_set)", "return False"),
    ("charge_seeded 가 고정 행도 봄", "metrics/_helpers_nodal.py", "for i in range(g.shape[0]) if i not in fixed_set)", "for i in range(g.shape[0]))"),
]
rows = []
for name, rel, old, new in muts:
    text = None
    if rel:
        path = root / "gmid_engine" / rel
        text = path.read_bytes().decode("utf-8")
        assert old in text, name
        path.write_bytes(text.replace(old, new, 1).encode("utf-8"))
    p = subprocess.run([sys.executable, "-m", "pytest", *SET, "-q", "--tb=line", "-p", "no:cacheprovider", "-W", "ignore"], cwd=root, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if rel:
        path.write_bytes(text.encode("utf-8"))
    rows.append({"name": name, "rc": p.returncode, "last": ((p.stdout.strip().splitlines() or [p.stderr[-160:]])[-1])[:160], "failed": [l[:120] for l in p.stdout.splitlines() if l.startswith("FAILED")][:4]})
    print(rows[-1], flush=True)
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding="utf-8")
