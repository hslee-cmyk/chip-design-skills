# -*- coding: utf-8 -*-
"""OP-1a (5) 입력 묶음: base 판 입력 원천 파일을 git blob 그대로 복사하고 sha256·blob id를 기록한다(검증자 작성).
사용: python bundle_sources.py <격리 복제본> <base sha> <input_bundle 폴더> <u6 작업 폴더> <u6 확인 json>"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

ISO, BASE, DST, U6W, U6J = sys.argv[1:6]
O = "skills/analog-gmid-design/tools/spice_oracle"
ls = subprocess.run(["git", "-C", ISO, "ls-tree", "-r", "--name-only", BASE, "--", O], capture_output=True, text=True, check=True).stdout.split()
pick = [p for p in ls if p.startswith(O + "/tests/fixtures/")]
pick += [p for p in ls if p.startswith(O + "/smoke/") and (p.endswith(".oracle_input.json") or p.endswith("/smoke_judge.json"))]
pick += [O + "/smoke/u6_selfchecks.py", O + "/tests/conftest.py", O + "/tests/u6_toy5t.py",
         O + "/tests/test_oracle_c10_stability.py", O + "/tests/test_oracle_u6_stability.py",
         O + "/oracle_input.schema.json", O + "/oracle_config.json"]
recs = []
for p in sorted(set(pick)):
    blob = subprocess.run(["git", "-C", ISO, "rev-parse", f"{BASE}:{p}"], capture_output=True, text=True, check=True).stdout.strip()
    data = subprocess.run(["git", "-C", ISO, "cat-file", "blob", blob], capture_output=True, check=True).stdout
    q = os.path.join(DST, "src_at_base", p)
    os.makedirs(os.path.dirname(q), exist_ok=True)
    with open(q, "wb") as f:
        f.write(data)
    recs.append({"path": p, "blob": blob, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
u6 = json.load(open(U6J, encoding="utf-8"))
os.makedirs(os.path.join(DST, "u6"), exist_ok=True)
for key, c in u6["cases"].items():
    src = os.path.join(U6W, key, c["input_json"])
    shutil.copyfile(src, os.path.join(DST, "u6", c["input_json"]))
    assert hashlib.sha256(open(src, "rb").read()).hexdigest() == c["input_sha256"]
u6["cases_note"] = ("입력 JSON의 process.lut_npz는 materialize 실행 작업 폴더 경로다. 같은 내용의 LUT는 기준선 files/u6/lut_rc.npz·lut_5t.npz"
                    "(lut_bit_identical 참). 넷리스트·meta가 기준선 u6/과 바이트 동일(cir_bit_identical·meta_bit_identical)")
json.dump({"base_commit": BASE, "sources": recs, "u6_materialize": u6,
           "n4_1_bundle_note": ("N4-1 입력 묶음: O/tests/fixtures, O/smoke oracle_input(원본, 기준선에서 쓴 lut_npz 수정본은 baseline/files/inputs/), "
                                "test 손 회로(conftest independent_*·u6_toy5t.py), C10 fixture(test_oracle_c10_stability.py·test_oracle_u6_stability.py 안 "
                                "입력 생성 함수), u6 자체 점검(u6_selfchecks.py + u6/ 입력 JSON). test가 실제로 쓴 입력 JSON은 "
                                "baseline/files/pytest/tmp/<폴더>/**/*.input.json(대응은 baseline/_test_tmp_map.json)")},
          open(os.path.join(DST, "input_bundle.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print(len(recs), sum(r["bytes"] for r in recs))
