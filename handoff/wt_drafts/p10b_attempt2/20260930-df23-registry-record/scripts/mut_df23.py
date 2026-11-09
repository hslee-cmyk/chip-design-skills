"""V3 보충 뮤테이션(spec card 20260930-df23-registry-record 계약 5 (d)) -- base 판 mutate_changed.py의 대상 규칙·연산자를 그대로 쓴다.

base 판 `mutate_changed.py`는 대상 파일을 `reachability._is_source`(A/ 바로 아래 *.py, workspaces/run_harness.py)로 고르므로
이 card의 변경 `A/tests/tools/reg_check.py`는 대상 0이다. 그래서 같은 모듈의 함수를 불러 같은 규칙으로 변이만 만든다:
  대상 def = mutate_changed.changed_defs(base 소스, head 소스) -- diff가 닿은 def 중 AST 해시(docstring 제외)가 바뀐 것과 새 def
  연산자   = mutate_changed.mutants -- 비교 뒤집기, 산술 교체, 상수 ±, 문장 삭제, 조기 return, except 본문 삭제
  치환     = mutate_changed._replace_def
변이마다 reg_check를 import하는 test 두 파일(test_reg_check_df23.py, test_reg_check.py)을 V1 형태 옵션으로 돌린다. 원본은 매번 복원.

사용: python -P mut_df23.py <병합본 격리 복제본> <게이트 캐시> <base 커밋> <out.jsonl> [--list-only] [--timeout 초] [--tests 상대경로,…] [--limit N]
  PYTHONPATH 맨 앞에 게이트 캐시를 둔다(이 스크립트가 sys.path에 넣는다). 결과는 변이마다 append.
  out.jsonl 첫 줄 = 대상·변이 수, 둘째 줄 = 무변이 기준 실행(실패면 중단, exit 2). 생존 있으면 exit 1.
"""
import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile

root, cache, base_rev, out = sys.argv[1:5]
list_only = "--list-only" in sys.argv
timeout = int(sys.argv[sys.argv.index("--timeout") + 1]) if "--timeout" in sys.argv else 300
sys.path.insert(0, cache)
import mutate_changed as mc  # noqa: E402  (base 판 게이트 코드)

REL = "skills/analog-gmid-design/assets/tests/tools/reg_check.py"
TESTS = ["skills/analog-gmid-design/assets/tests/contracts/test_reg_check_df23.py",
         "skills/analog-gmid-design/assets/tests/contracts/test_reg_check.py"]
if "--tests" in sys.argv:   # 자기 점검용(기본은 위 두 파일)
    TESTS = sys.argv[sys.argv.index("--tests") + 1].split(",")
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None   # 자기 점검용
PY = "C:/Python314/python.exe"
target = os.path.join(root, *REL.split("/"))
orig = open(target, "rb").read()
head_src = orig.decode("utf-8")
bs = subprocess.run(["git", "-C", root, "show", "%s:%s" % (base_rev, REL)], capture_output=True)
base_src = bs.stdout.decode("utf-8") if bs.returncode == 0 else None
# 줄 끝: 원본이 CRLF면 _replace_def(split('\n')) 뒤에도 남은 줄의 \r은 그대로 두고 새 줄에는 \r을 붙인다.
crlf = "\r\n" in head_src
src_lf = head_src.replace("\r\n", "\n")
defs = mc.changed_defs(base_src.replace("\r\n", "\n") if base_src is not None else None, src_lf)


def node_line(fn, path):
    p = path
    while True:
        try:
            n = mc._get(fn, p)
            if hasattr(n, "lineno"):
                return n.lineno, getattr(n, "end_lineno", n.lineno)
        except Exception:
            pass
        if "." not in p:
            return fn.lineno, fn.end_lineno
        p = p.rsplit(".", 1)[0]


plan = []
for q, fn in defs:
    for op, path, mfn in mc.mutants(fn, src_lf):
        l0, l1 = node_line(fn, path) if op != "early_return" else (fn.lineno, fn.lineno)
        plan.append({"id": "reg_check:%s:%s:%s" % (q, op, path), "def": q, "op": op, "path": path, "lines": [l0, l1],
                     "_fn": fn, "_mfn": mfn})


def run_tests():
    pyc = tempfile.mkdtemp(prefix="pyc_mut_", dir="C:/g88")
    env = dict(os.environ, PYTHONPATH=cache, PYTHONPYCACHEPREFIX=pyc, PYTHONDONTWRITEBYTECODE="1",
               APPDATA="C:/Users/HSLEE/AppData/Roaming")
    cmd = [PY, "-P", "-m", "pytest", "-c", cache + "/pytest_gate.ini", "--rootdir=" + root, "--confcutdir=" + root,
           "--gmid-phase=2", "--gmid-strict="] + [root + "/" + t for t in TESTS] + ["-q", "-p", "no:cacheprovider", "-x"]
    try:
        p = subprocess.run(cmd, capture_output=True, env=env, timeout=timeout)
        last = p.stdout.decode("utf-8", "replace").strip().splitlines()[-1:]
        return p.returncode, last
    except subprocess.TimeoutExpired:
        return "timeout", []
    finally:
        shutil.rmtree(pyc, ignore_errors=True)


with open(out, "w", encoding="utf-8") as fo:
    fo.write(json.dumps({"base": base_rev, "file": REL, "base_exists": base_src is not None,
                         "target_defs": [[q, fn.lineno, fn.end_lineno] for q, fn in defs], "mutants": len(plan),
                         "ops": sorted({p["op"] for p in plan})}, ensure_ascii=False) + "\n")
    fo.flush()
    if list_only:
        for p in plan:
            fo.write(json.dumps({k: v for k, v in p.items() if not k.startswith("_")}, ensure_ascii=False) + "\n")
        sys.exit(0)
    rc, last = run_tests()
    fo.write(json.dumps({"control": True, "exit": rc, "summary": last}, ensure_ascii=False) + "\n")
    fo.flush()
    if rc != 0:
        sys.exit(2)
    survived = 0
    try:
        for p in plan[:LIMIT]:
            new = mc._replace_def(src_lf, p["_fn"], p["_mfn"])
            if crlf:
                new = new.replace("\n", "\r\n")
            open(target, "wb").write(new.encode("utf-8"))
            rc, last = run_tests()
            killed = rc != 0
            survived += 0 if killed else 1
            fo.write(json.dumps({"id": p["id"], "op": p["op"], "lines": p["lines"], "exit": rc, "killed": killed,
                                 "summary": last}, ensure_ascii=False) + "\n")
            fo.flush()
    finally:
        open(target, "wb").write(orig)
    fo.write(json.dumps({"done": True, "mutants": len(plan), "survived": survived}, ensure_ascii=False) + "\n")
sys.exit(1 if survived else 0)
