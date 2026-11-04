"""IT-1 재판정 뮤턴트: 복제본 임시 수정 -> test -> 원 바이트 복원. 커밋 없음."""
import json
import os
import re
import subprocess
import sys

ISO, OUT = sys.argv[1], sys.argv[2]
ROOT = ISO + "/skills/analog-gmid-design"
E = "gmid_engine/"
env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
LF, CRLF = chr(10), chr(13) + chr(10)
RAISE = ('    if len(declared) == 1:' + LF
         + '        raise StructureUnresolvedError(devices=(), detail={"reason": UNSUPPORTED_RULE_BRANCH,' + LF
         + '                                                           "rule_branch": BRANCH_INPUT_TARGET_ONE_PORT,' + LF
         + '                                                           "ports": tuple(sorted(diff.values())), "declared": declared})')
MUT = [
    ("X1 input_target_one_port 정지 코드 제거", "sizing/writer_plan.py", RAISE, "    return", ["sizing/test_writer_plan.py"], "one_port"),
    ("X2 입력 DC 선언 가드 제거", "sizing/writer_plan.py", "    if not input_dc_declared:" + LF + "        _stop_if_one_port_targeted", "    if True:" + LF + "        _stop_if_one_port_targeted", ["sizing/test_writer_plan.py", "sizing/test_kernel_context.py"], ""),
    ("X3 두 포트 다 선언도 정지", "sizing/writer_plan.py", "    if len(declared) == 1:", "    if len(declared) >= 1:", ["sizing/test_writer_plan.py"], "both"),
    ("X4 coupling_vars 둘째 net_model 호출 복귀", "graph/coupling_vars.py", "    model = net_index(s1)", "    from .net_model import net_model; model = net_model(s1)", ["graph/test_coupling_vars.py", "graph/test_net_model.py", "structure"], ""),
    ("X5 terms 짝 포트 제약 제거", "sizing/block_columns.py", "if w.relation == REL_INPUT_POINT and w.known == net:", "if False:", ["sizing/test_block_columns.py"], ""),
    ("X6 rule_hash 재기록 되돌림", "../assets/library/nmcnr_amplifier.structure.json", '"rule_hash": "ca0fde40c5599facc08b18d3fd94036b7fd8b242580edf5db1fd0eb54ad04347"', '"rule_hash": "5c0b84c53d2f350e2d27a2aba8acb2739379a16a6227e042c7761b183fb6906b"', ["graph/test_s1v_build.py"], "rh"),
]


def run(test):
    p = subprocess.run([sys.executable, "-m", "pytest", E + "tests/" + test, "-q", "-p", "no:cacheprovider", "--tb=line"], cwd=ROOT, env=env, capture_output=True, encoding="utf-8", errors="replace")
    fails = re.findall(r"^(?:FAILED|ERROR) \S*::(\S+)", p.stdout, re.M)
    return p.returncode, fails, p.stdout.strip().splitlines()[-1:]


for name, path, old, new, tests, kw in MUT:
    full = ROOT + "/" + E + path
    orig = open(full, "rb").read()
    if old.encode("utf-8") not in orig and CRLF.encode() in orig:
        old, new = old.replace(LF, CRLF), new.replace(LF, CRLF)
    if old.encode("utf-8") not in orig:
        open(OUT, "ab").write((json.dumps({"mut": name, "error": "old 없음"}, ensure_ascii=False) + LF).encode("utf-8"))
        continue
    open(full, "wb").write(orig.replace(old.encode("utf-8"), new.encode("utf-8")))
    try:
        res = []
        for t in tests:
            rc, fails, tail = run(t)
            res.append({"test": t, "rc": rc, "n_fail": len(fails), "fails": fails[:12], "tail": tail})
    finally:
        open(full, "wb").write(orig)
    open(OUT, "ab").write((json.dumps({"mut": name, "killed": any(r["rc"] != 0 for r in res), "kw_hit": any(kw in f for r in res for f in r["fails"]) if kw else None, "res": res}, ensure_ascii=False) + LF).encode("utf-8"))
