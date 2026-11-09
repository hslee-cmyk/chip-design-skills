"""측정 전용(F1 착수 조건 (2) 모의): T0가 selftest 3파일의 shim 경유 비엔진 이름을 출처 import로 바꾼 F1 base'와,
그 위에서 F1이 '같은 줄의 엔진 이름만' 바꾼 head'를 스크래치 복제본에 커밋한다(git plumbing, 체크아웃 없음).

    python -B t0sim.py <복제본> <F1 모의 base rev> <F1 모의 rev> <결과 json>
비엔진 이름 = base 트리에서 그 shim으로 풀리지 않는 이름(binding_origin이 def가 아님 -- 모의 M9: np·json·math·_dc_replace·os, TL 이름
nmcnr_predict_ac_response). 출처: 표준·외부 모듈은 아래 SRC 표, 엔진 이름은 base에서 그 이름을 재수출하는 shim(topology_library)."""
import ast
import json
import os
import subprocess
import sys

R, BASE, HEAD, OUT = sys.argv[1:5]
A = "skills/analog-gmid-design/assets/"
U = A + "tests/unit/"
FILES = ["test_selftest_sizing_recipe.py", "test_selftest_topology_library.py", "test_selftest_design_report.py"]
SRC = {"np": "import numpy as np", "json": "import json", "math": "import math", "os": "import os",
       "_dc_replace": "from dataclasses import replace as _dc_replace"}
TL_NAMES = {"nmcnr_predict_ac_response": "topology_library"}
ENG = {"sizing_recipe", "topology_library", "design_report", "stick_diagram", "gmid_lut", "topology_authoring", "circuit_state_graph",
       "gmid_sizing_engine", "circuit_metrics", "theta_search", "sizing_layout_convergence", "instance_report_builder"}


def git(*a, env=None):
    r = subprocess.run(["git", "-C", R] + list(a), capture_output=True, env=env)
    if r.returncode:
        raise SystemExit(r.stderr.decode("utf-8", "replace"))
    return r.stdout.decode("utf-8")


def in_run(s):
    """엔진 from-import, 또는 SRC 이름만 묶는 import(모의 F1이 끼워 넣은 비엔진 줄)."""
    if isinstance(s, ast.ImportFrom) and s.module in ENG:
        return True
    if isinstance(s, (ast.Import, ast.ImportFrom)):
        return all((a.asname or a.name) in SRC for a in s.names)
    return False


def eng_group(src):
    """모듈 최상위의 연속한 엔진 from-import 묶음(첫 줄 번호, 끝 줄 번호, 문장들)."""
    t = ast.parse(src)
    body = t.body
    for i, s in enumerate(body):
        if isinstance(s, ast.ImportFrom) and s.module in ENG:
            j = i
            while j + 1 < len(body) and in_run(body[j + 1]):
                j += 1
            return s.lineno, body[j].end_lineno, body[i:j + 1]
    raise SystemExit("엔진 import 없음")


res = {}
blobs_b, blobs_h = {}, {}
for f in FILES:
    sb = git("show", "%s:%s%s" % (BASE, U, f))
    sh = git("show", "%s:%s%s" % (HEAD, U, f))
    lb = sb.split("\n")
    lo, hi, stmts = eng_group(sb)
    nonengine, tl, keep_lines = [], [], []
    for s in stmts:
        names = [(a.name, a.asname) for a in s.names]
        keep = [(n, a) for n, a in names if n not in SRC and n not in TL_NAMES]
        nonengine += [n for n, _a in names if n in SRC]
        tl += [n for n, _a in names if n in TL_NAMES]
        if keep:
            keep_lines.append("from %s import (%s)  # noqa: E402" % (s.module, ", ".join(n + (" as " + a if a else "") for n, a in keep)))
    keep_lines += ["from %s import %s  # noqa: E402" % (TL_NAMES[n], n) for n in tl]
    pre = [SRC[n] + "  # noqa: E402" for n in sorted(nonengine)]
    base2 = "\n".join(lb[:lo - 1] + pre + keep_lines + lb[hi:])
    # head': 같은 비엔진 줄(같은 자리) + F1 모의가 쓴 엔진 import 줄(비엔진 줄 뺌)
    th = ast.parse(sh)
    hl = sh.split("\n")
    i0 = next(i for i, s in enumerate(th.body) if isinstance(s, ast.ImportFrom) and s.module in ENG)
    i1 = i0
    while i1 + 1 < len(th.body) and in_run(th.body[i1 + 1]):
        i1 += 1
    run = th.body[i0:i1 + 1]
    eng_h = [s for s in run if isinstance(s, ast.ImportFrom) and s.module in ENG]
    h_lo, h_hi = run[0].lineno, run[-1].end_lineno
    eng_lines = ["\n".join(hl[s.lineno - 1:s.end_lineno]) for s in eng_h]
    head2 = "\n".join(hl[:h_lo - 1] + pre + eng_lines + hl[h_hi:])
    blobs_b[U + f], blobs_h[U + f] = base2, head2
    res[f] = {"nonengine": sorted(nonengine), "tl_names": tl, "base_lines": pre + keep_lines, "head_lines": pre + eng_lines}


def commit(parent, files, msg):
    idx = os.path.join(os.environ.get("TMP", "."), "idx.t0sim")
    env = dict(os.environ, GIT_INDEX_FILE=idx)
    if os.path.exists(idx):
        os.remove(idx)
    git("read-tree", parent, env=env)
    for p, txt in files.items():
        r = subprocess.run(["git", "-C", R, "hash-object", "-w", "--stdin", "--no-filters"], input=txt.encode("utf-8"), capture_output=True)
        git("update-index", "--add", "--cacheinfo", "100644,%s,%s" % (r.stdout.decode().strip(), p), env=env)
    tree = git("write-tree", env=env).strip()
    os.remove(idx)
    return git("-c", "user.name=sim", "-c", "user.email=sim@x", "commit-tree", tree, "-p", parent, "-m", msg).strip()


res["T0B"] = commit(BASE, blobs_b, "sim: T0 (selftest 3 non-engine names -> source imports)")
res["T0H"] = commit(HEAD, blobs_h, "sim: F1 mock on T0 (engine names only)")
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(res["T0B"], res["T0H"])
