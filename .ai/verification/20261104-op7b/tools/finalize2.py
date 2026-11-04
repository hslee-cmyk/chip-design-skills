# -*- coding: utf-8 -*-
import copy, datetime, json, shutil, subprocess
T = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7b_audit"
W = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-op7b-audit"
ID = "20261104-op7b"
R = f"{W}/.ai/verification/{ID}"
shutil.copyfile(f"{T}/out/re_a7_3.txt", f"{R}/measure/re_a7_3.txt")
shutil.copyfile(f"{T}/tools/finalize2.py", f"{R}/tools/finalize2.py")
TEST = subprocess.run(["git", "-C", W, "rev-parse", "707cade3"], capture_output=True, text=True, check=True).stdout.strip()
s = json.load(open(f"{R}/sections.json", encoding="utf-8"))
s["round_1"] = {"verdict": s["verdict"], "major": copy.deepcopy(s["major"])}
s["verdict"] = "PASS (Major 0, M-1 확인 뒤. minor 는 LA-1 재점검 입력)"
s["major"] = []
s["measures"]["A7-3"] = ["PASS", "707cade3 뒤 test_spiceinit_isolation 3 passed(복제본). 판정자 변형은 1차 그대로"]
s["rejudge"] = {"test_commit": TEST, "scope": "test_spiceinit_isolation.py 와 그 커밋 diff 만. 다른 측정은 1차 재사용",
                "diff_check": "단언 약화 없음: status.error is None, .spiceinit 바이트, 로그 모드 단언 유지. V(a)=1 은 V(vdd)=FB vdd 로 같은 KVL 단언, 'M1' in devices 추가. log_of 만 실행 폴더 기준으로 고침. T7-9c 단언 변경 0. 코드 변경 0"}
s["minor"].append("m7 T7-9 bench 가 MOS·PDK 를 쓰게 되어 interface '어댑터 격리' 문언 'PDK 없는 저항 넷리스트'와 다르다. 어댑터 present 가 MOS id 만 보는 것은 그대로다(A-86)")
json.dump(s, open(f"{R}/sections.json", "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
p = f"{W}/.ai/verification/{ID}.json"
r = json.load(open(p, encoding="utf-8"))
r["test_commit"] = TEST
c = r["checks"]
c["V1"]["basis"] = c["V1"]["basis"].replace("test_spiceinit_isolation 2 failed 1 passed", "test_spiceinit_isolation 3 passed(707cade3 뒤, 1차 2 failed 1 passed)")
c["V2"] = {"verdict": "PASS", "basis": f"A7-1 219 passed, red 10건. A7-2 10/10. A7-3 test_spiceinit_isolation 3 passed(707cade3, 단언 약화 없음을 diff 로 확인). A7-4 PASS. 표 = .ai/verification/{ID}/sections.json."}
for it in r["reproduced_numbers"]:
    if it["name"] == "격리 test 실패":
        it["name"] = "격리 test 통과"
        it["value"] = 3
r["auditor_run"]["time"] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).replace(microsecond=0).isoformat()
r["auditor_run"]["commands"].append(f"M-1 확인: git clone --no-hardlinks --no-local {W} {T}/iso3; pytest tests/adapters/ngspice/test_spiceinit_isolation.py")
json.dump(r, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
import jsonschema
print("schema", [e.message[:100] for e in jsonschema.Draft202012Validator(json.load(open(f"{W}/.ai/verification/_schema.json", encoding="utf-8"))).iter_errors(r)])
