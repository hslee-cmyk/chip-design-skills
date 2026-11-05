"""IT-1 M-4 확인: 판정 기록 갱신. 인자: 임시 루트, audit worktree."""
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

import jsonschema

T, W = Path(sys.argv[1]), Path(sys.argv[2])
ID = "20261104-it1-input-point"
p = W / ".ai/verification" / (ID + ".json")
d = json.loads(p.read_text(encoding="utf-8"))
old = json.loads(subprocess.check_output(["git", "-C", str(W), "show", "03e4eab9:.ai/verification/%s.json" % ID]))
n = "test_it1_net_model_has_single_call_site_in_s1v_fields"
i = [k for k, x in enumerate(old["red"]["test_ids"]) if x.endswith("::" + n)]
assert len(i) == 1
d["red"]["test_ids"].append(old["red"]["test_ids"][i[0]])
d["red"]["failure_hashes"].append(old["red"]["failure_hashes"][i[0]])
c = d["checks"]
c["V1"]["basis"] += " M-4 확인 머리 b36782bf: graph/test_coupling_vars.py 만 다시 재어 80 통과(이전 79 + 복원 1), 그 밖 범위는 재지 않았고 앞 수치(card 24 파일 839 + 복원 1 = 840, structure 171, 연기 23)를 재사용한다. 복원 커밋 변경은 그 test 파일 21줄뿐, 엔진·assets diff 0."
c["V2"]["basis"] += " 복원 test 1개를 red 목록에 되돌려 46개(red 측정 재사용), 병합본 통과."
before = c["V3"]["basis"]
c["V3"]["basis"] = before.replace("생존 X4 = Major-4(V5), X5", "X4 = 복원 뒤 killed(test_it1_net_model_has_single_call_site_in_s1v_fields 1 실패, 복원 전 생존), 생존 X5")
assert c["V3"]["basis"] != before
c["V5"] = {"verdict": "PASS", "basis": "M-4 해소: df564bc7 이 test_it1_net_model_has_single_call_site_in_s1v_fields 를 복원, 03e4eab9 대비 diff 에 그 test 본문·import 변경 0(원문 그대로). 뮤턴트 X4 killed, 원복 뒤 80 통과. 그 밖 약화 0: 래칫 new 0을 기준선 수정 없이 달성, T-6a 네 값 test·READS test 삭제는 필드 삭제의 귀결(A-76, 계획·design 40 개정과 일치, 부재 단언으로 대체), os_k 폐기 = A-42, T-1h 는 O-227 (3) 유지."}
d["test_commit"] = subprocess.check_output(["git", "-C", str(W), "rev-parse", "df564bc7"], text=True).strip()
for r in d["reproduced_numbers"]:
    if r["name"] == "card test 수":
        r["value"] = 840
        r["command"] += " + graph/test_coupling_vars.py 재실행(80)"
    if r["name"] == "재판정 뮤턴트 생존 수":
        r["value"] = 1
        r["command"] += " + X4 재측정 m4.json"
    if r["name"] == "red 수":
        r["value"] = 46
d["auditor_run"]["time"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
d["auditor_run"]["commands"].append("M-4 확인: git clone --no-hardlinks --no-local <worktree> iso3; pytest gmid_engine/tests/graph/test_coupling_vars.py; X4 임시 수정 후 같은 test, 원복 후 같은 test(m4.json)")
p.write_bytes(json.dumps(d, ensure_ascii=False, indent=1).encode("utf-8"))
ev = W / ".ai/verification" / ID
shutil.copy(T / "res/m4.json", ev / "m4.json")
shutil.copy(T / "build_record3.py", ev / "scripts/build_record3.py")
jsonschema.validate(d, json.load(open(W / ".ai/verification/_schema.json", encoding="utf-8")))
print("schema ok", len(d["red"]["test_ids"]))
