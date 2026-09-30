"""판정 기록을 base 판 로더 규칙 1~10 + V1 명령 형태로 미리 판정(커밋 전). 사용: precheck_record.py <기록 파일> <base 복제본> <base> <approvals 디렉터리>"""
import json, os, re, sys
import merge_gate as mg
rec_path, root, base, appdir = sys.argv[1:5]
old = mg.TreeView(["-C", root], base)
tables = mg.read_plan_tables_text(old.read(mg.PLAN_PATH).decode("utf-8"))
card = mg.rp.parse_spec_card(old.read(mg.rp.spec_card_path("20260930-d-move-tests")).decode("utf-8"), "20260930-d-move-tests")
raw = open(rec_path, "rb").read()
def ra(a):
    p = os.path.join(appdir, a + ".md")
    return open(p, "rb").read() if os.path.exists(p) else None
rec = mg.load_verification_record(raw, file_id="20260930-d-move-tests", schema=json.loads(old.read(mg.SCHEMA_PATH).decode("utf-8")),
                                  read_approval=ra, spec_phase=card["phase"], plan=tables)
v1 = [c for c in rec["auditor_run"]["commands"] if c.startswith("V1: ")]
print("V1 elements", len(v1))
print("v1_command_check", mg.v1_command_check(v1[0][4:], python_path="C:/Python314/python.exe", old=base,
                                                strict_needed=sorted(mg.strict_set(old, card)), phase=card["phase"]))
print("V5 hex64", re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", rec["checks"]["V5"]["basis"]))
print("FAIL", [k for k, c in rec["checks"].items() if c["verdict"] == "FAIL"])
print("ok")
