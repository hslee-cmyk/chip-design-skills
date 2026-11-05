# -*- coding: utf-8 -*-
"""재판정 기록 갱신(A-81 처리 뒤). 고친 것만 재고 앞 측정은 재사용."""
import copy, datetime, json, shutil, subprocess
T = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op23_audit"
W = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-op23-audit"
ID = "20261104-op23"
R = f"{W}/.ai/verification/{ID}"
for n in ("re_a3_cm.json", "re_a3_cm2.json", "re_a3_5b.json", "re_card.txt", "re_structure.txt"):
    shutil.copyfile(f"{T}/out/{n}", f"{R}/measure/{n}")
shutil.copyfile(f"{T}/out/re_head/run_log.jsonl", f"{R}/measure/re_head_r1_run_log.jsonl")
shutil.copyfile(f"{T}/tools/finalize2.py", f"{R}/tools/finalize2.py")
git = lambda *a: subprocess.run(["git", "-C", W, *a], capture_output=True, text=True, check=True).stdout.strip()
HEAD = git("rev-parse", "302b4bc6")
TEST, CODE = git("rev-parse", "4ef7c20b"), git("rev-parse", "93e84ab2")
dsha_head = json.loads(open(f"{T}/out/re_head/run_log.jsonl", encoding="utf-8").readline())["descriptor_sha256"]
dsha_run1 = json.loads(open(f"{T}/out/run1/run_log.jsonl", encoding="utf-8").readline())["descriptor_sha256"]

s = json.load(open(f"{R}/sections.json", encoding="utf-8"))
first = {k: copy.deepcopy(s[k]) for k in ("verdict", "major")}
s["round_1"] = first
s["verdict"] = "PASS (Major 0, 재판정 후. minor 는 LA-1 재점검 입력)"
s["major"] = []
s["rejudge"] = {
 "head": HEAD, "reused": "R2~R5, A3-6, A3-7, 2회로 연기, test_independent 는 1차 결과 재사용(다시 돌리지 않음). CM 수정은 CM 벤치 밖 IR 을 바꾸지 않아 R1~R5 대상 밖",
 "M-2": "닫힘. tcm_cmfb 머리 그대로 gain_dc 62.67435095845278, ugf_hz 133510.7841970794, pm_deg_raw 32.84699194740443 = 기준선 비트 동일, Vac AC 0. 파이프라인 cm_loop.measures 차이 없음. test_cm_loop_bench_input_ac_is_zero 통과, 뮤턴트(수정 되돌림 `0.0 if loop`)에서 그 test 만 AssertionError(일반 AC·β 루프 대조 2개는 통과). OP-1 넷리스트 대조 같음 472 -> 480, 잔차 78 -> 70, CM Vac 잔차 0",
 "M-1": f"닫힘. 복제본 머리(사본·변형 없음) R1 rc 0, verdict INCOMPLETE, reject 없음, devices·gain_dc·pm_deg_raw 기준선과 같음. 옆 선언 LF 5e5c02a5..., fbf38fd9... = 판정자 측정본과 바이트 같음(LF), 기술자 칸 같음. PDF 체크아웃·blob sha b5bc7c4f... 2660636 바이트. 기술자 LF 머리 {dsha_head[:12]} = 1차 측정 복제본 {dsha_run1[:12]}: {dsha_head == dsha_run1}",
 "M-3": "닫힘(A-81 채택 안). spec '## forced 고정원 배치', interface A3-5 기대 차이, design §4.2 행 = 코드 build_circuit.py:423-424 와 같다. A3-5 잔차(R3.forced 4줄, R4.forced 2줄)는 전부 그 항목으로 설명된다, 다른 잔차 0. 물리 측정은 1차 physics.1",
 "tests": "플러그인 없이 그대로: card test 182 passed(1차 179 + 3), World.run 입력 폴더 문제 닫힘(op23_support.py:208 mkdir, 저장소에 mkdirfix 0). X-13·test_verified_by 48 passed, tests/structure 171 passed 1 deselected",
 "new_minor": ["m12 M-3 예외가 spec '원래 취지와 다름' 목록에 없고, design §10.6 3단계 '남은 차이 0, 아니면 멈춤' 문언이 그대로이며 design 판·history 도 그대로다. card A3-5 기준과 design §10.6 이 다르다. LA-1 재점검 입력"]}
s["minor"] = [m for m in s["minor"] if not m.startswith("m4 ")] + s["rejudge"]["new_minor"]
for z, k, v in (("OP-2", "A2-5", ["PASS", "재판정: 저장소 PDF sha b5bc7c4f..., 값·쪽은 1차 대조 그대로"]),
                ("OP-3", "A3-3", ["PASS", "재판정: 머리 옆 선언 = 판정자 측정본, 머리 R1 통과. 변형 거부·슬라이스는 1차(같은 내용 복제본)"]),
                ("OP-3", "A3-5", ["PASS", "재판정: 잔차 6줄 = 기대 차이(A-81), 다른 잔차 0"]),
                ("OP-3", "extra_CM", ["PASS", "재판정: 비트 동일, 뮤턴트 잡힘"])):
    s[z][k] = v
json.dump(s, open(f"{R}/sections.json", "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)

p = f"{W}/.ai/verification/{ID}.json"
r = json.load(open(p, encoding="utf-8"))
r["test_commit"], r["code_commit"] = TEST, CODE
c = r["checks"]
c["V1"]["basis"] = "임시 규칙 O-229: 전체 test 안 돌림, 통과로 세지 않음. 재판정 범위 = card test 182 passed, X-13·test_verified_by 48 passed, tests/structure 171 passed 1 deselected(머리 302b4bc6). 재사용(1차) = test_independent 3 passed, 2회로 연기 23 passed 158 deselected. 옛 test 26파일 344 함수 미실행(A-80 D-6)."
c["V2"] = {"verdict": "PASS", "basis": "재판정 머리 302b4bc6. OP-2 구역 A2-1~A2-5 PASS(PDF sha b5bc7c4f). OP-3 구역 A3-1~A3-12 PASS: 머리 R1 reject 없음, A3-5 잔차 6줄 = 기대 차이(A-81), A3-4·A3-6·A3-7 은 1차 재사용. red = 1차 새 모듈 ImportError 10건 + M-2 뮤턴트에서 test_cm_loop_bench_input_ac_is_zero AssertionError, green = 182 passed. 구역별 표 = .ai/verification/20261104-op23/sections.json."}
c["V5"]["basis"] += " 재판정: M-3 forced 배치 차이를 A3-5 기대 차이로 올림(A-81, 물리 측정 근거, 제외 칸 추가 아님)."
c["V9"] = {"verdict": "PASS", "basis": "재판정: CM 루프 입력 AC 0(build_circuit.py:390), tcm_cmfb gain_dc·ugf·pm_deg_raw 기준선 비트 동일. 나머지는 1차: forced 재배치 DC·AC·i(V) 부호 같음, VDSAT 경로 fail-open 아님, D-1 거부·PM 동작 맞음, 944 bin 소속·SI 보고값 같음."}
c["V4"]["basis"] += " 재판정: test_cm_loop_bench_input_ac_is_zero 기대값 = CONTRACT 7.11 입력 AC 접지, 뮤턴트로 거부 확인."
for it in r["reproduced_numbers"]:
    if it["name"] == "toy 통과":
        it["value"] = 182
    if it["name"] == "CM gain_dc 새":
        it["value"] = 62.67435095845278
        it["command"] = "tools/a3_cm2.py (재판정 머리)"
r["auditor_run"]["time"] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).replace(microsecond=0).isoformat()
r["auditor_run"]["commands"].append(f"재판정: git clone --no-hardlinks --no-local {W} {T}/iso2; 머리 R1 a3_run.py, a3_cm.py, a3_cm2.py, a3_5b.py, 뮤턴트 사본 {T}/mut, pytest card·X-13·structure")
json.dump(r, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
import jsonschema
print("schema", [e.message[:100] for e in jsonschema.Draft202012Validator(json.load(open(f"{W}/.ai/verification/_schema.json", encoding="utf-8"))).iter_errors(r)], "dsha same", dsha_head == dsha_run1)
