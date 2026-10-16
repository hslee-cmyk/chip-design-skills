# -*- coding: utf-8 -*-
"""OP-1a base_check -- 기준선 원자료가 base 판 오라클로 만든 것임의 대조(검증자 작성).
(1) base 판 오라클 파일(tools/spice_oracle/**)의 blob과 마지막 변경 커밋, (2) 기준선 smoke 실행 기록(OP-1 n4_baseline.jsonl)의
    input_orig_sha256 대 base blob을 core.autocrlf=true 체크아웃 형태(LF -> CRLF)로 바꾼 sha256(blob 그대로의 sha256도 기록), (3) 기준선 junit test id 집합 대 base 판 pytest --collect-only id 집합.
사용: python -I base_check.py <격리 복제본> <base sha> <record 폴더> <collect-only 출력 파일> <결과 json>"""
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

ISO, BASE, REC, COLLECT, OUT = sys.argv[1:6]
O = "skills/analog-gmid-design/tools/spice_oracle"


def git(*a, binary=False):
    r = subprocess.run(["git", "-C", ISO, *a], capture_output=True, check=True)
    return r.stdout if binary else r.stdout.decode("utf-8").strip()


files = git("ls-tree", "-r", "--name-only", BASE, "--", O).splitlines()
py = [p for p in files if p.endswith(".py") and "/" not in p[len(O) + 1:]]
ident = []
for p in py:
    ident.append({"path": p, "blob": git("rev-parse", f"{BASE}:{p}"),
                  "last_commit": git("log", "-1", "--format=%H %cI", BASE, "--", p)})
last_any_py = git("log", "-1", "--format=%H %cI", BASE, "--", *[p for p in files if p.endswith(".py")])
smoke = []
with open(os.path.join(REC, "op1_measurements/files/results/n4_baseline.jsonl"), encoding="utf-8") as f:
    for ln in f:
        r = json.loads(ln)
        rel = O + "/smoke/" + os.path.basename(r["input_orig"].replace("\\", "/"))
        data = git("cat-file", "blob", f"{BASE}:{rel}", binary=True)
        crlf = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")   # core.autocrlf=true 체크아웃 형태(이 기계 git 설정)
        smoke.append({"case": r["case"], "base_path": rel, "base_blob_sha256": hashlib.sha256(data).hexdigest(),
                      "base_checkout_crlf_sha256": hashlib.sha256(crlf).hexdigest(),
                      "baseline_record_sha256": r["input_orig_sha256"],
                      "equal_blob": hashlib.sha256(data).hexdigest() == r["input_orig_sha256"],
                      "equal": hashlib.sha256(crlf).hexdigest() == r["input_orig_sha256"]})
junit = ET.parse(os.path.join(REC, "baseline/files/pytest/junit.xml")).getroot()
jids = set()
for tc in junit.iter("testcase"):
    cn = tc.get("classname").split(".")
    jids.add("/".join(cn) + ".py::" + tc.get("name"))
cids = set()
with open(COLLECT, encoding="utf-8", errors="replace") as f:
    for ln in f:
        ln = ln.strip()
        if "::" in ln and ln.startswith("tools/"):
            cids.add(ln)
res = {"base_commit": BASE, "oracle_top_py": ident, "last_commit_touching_any_oracle_py": last_any_py,
       "smoke_input_identity": smoke,
       "junit_vs_collect": {"n_junit": len(jids), "n_collect": len(cids), "only_junit": sorted(jids - cids)[:20],
                            "only_collect": sorted(cids - jids)[:20], "equal": jids == cids}}
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print(json.dumps({"last_py": last_any_py, "smoke_equal": [s["equal"] for s in smoke], "junit_vs_collect": res["junit_vs_collect"]["equal"],
                  "n": (len(jids), len(cids))}, ensure_ascii=False))
