"""격리 복제본에서 인라인 self-test를 (1) 스크립트로 직접 (2) 모듈 한 벌로 블록만 실행 두 방식으로 돌려
stdout 바이트·종료 코드·시간을 파일에 append 한다(10-test-separation design 부록 A 실측).

(2) 방식: 모듈을 import한 뒤 그 모듈 전역 사본에서 main 블록 본문만 exec -- TS1 이관본(모듈 한 벌)을 흉내 낸다.
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ISO = Path(sys.argv[1])
OUT = Path(sys.argv[2])
MODS = sys.argv[3].split(",")
SEEDS = sys.argv[4].split(",")
ASSETS = ISO / "skills/analog-gmid-design/assets"
PY = sys.executable

SIM = r'''
import ast, sys
sys.path.insert(0, r"{assets}")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import {mod} as _m
_src = open(_m.__file__, encoding="utf-8").read()
_t = ast.parse(_src)
_blk = [n for n in _t.body if isinstance(n, ast.If) and ast.unparse(n.test).replace("'", '"') == '__name__ == "__main__"'][0]
_g = dict(vars(_m)); _g["__name__"] = "__legacy__"
exec(compile(ast.Module(body=_blk.body, type_ignores=[]), _m.__file__, "exec"), _g)
'''

for mod in MODS:
    for seed in SEEDS:
        for way in ("direct", "onecopy"):
            env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONIOENCODING="utf-8")
            if way == "direct":
                cmd = [PY, str(ASSETS / f"{mod}.py")]
            else:
                cmd = [PY, "-c", SIM.format(assets=str(ASSETS), mod=mod)]
            t0 = time.perf_counter()
            r = subprocess.run(cmd, cwd=str(ASSETS), env=env, capture_output=True)
            dt = time.perf_counter() - t0
            name = f"{mod}.{way}.seed{seed}"
            (OUT / f"{name}.stdout").write_bytes(r.stdout)
            (OUT / f"{name}.stderr").write_bytes(r.stderr)
            rec = {"mod": mod, "way": way, "seed": seed, "exit": r.returncode, "seconds": round(dt, 1),
                   "stdout_sha256": hashlib.sha256(r.stdout).hexdigest(), "stdout_lines": r.stdout.count(b"\n")}
            with open(OUT / "results.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
