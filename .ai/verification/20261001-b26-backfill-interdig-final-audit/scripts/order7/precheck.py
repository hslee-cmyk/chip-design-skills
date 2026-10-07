import sys, json
sys.path.insert(0, "C:/g394/gmid-gate-cache/863a037cc0d774bb984006ea39966c5e4dd741ab")
import merge_gate as mg, role_paths as rp
B="863a037cc0d774bb984006ea39966c5e4dd741ab"; rid="20261001-b26-backfill-interdig-final-audit"
old=mg.TreeView(mg.Repo("C:/g394/iso/.git").args, B)
card=rp.parse_spec_card(old.read(rp.spec_card_path(rid)).decode("utf-8"), rid)
raw=open(sys.argv[1],"rb").read()
mg.load_verification_record(raw, file_id=rid, schema=json.loads(old.read(mg.SCHEMA_PATH).decode("utf-8")),
    read_approval=lambda x: old.read(mg.APPROVALS_DIR + x + ".md"), spec_phase=card["phase"],
    plan=mg.read_plan_tables_text(old.read(mg.PLAN_PATH).decode("utf-8")))
print("LOADER PASS")
