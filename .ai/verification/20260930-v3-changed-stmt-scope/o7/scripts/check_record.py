import json, sys
import merge_gate as mg
A = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-v3-changed-stmt-scope-audit"
cid = "20260930-v3-changed-stmt-scope"
raw = open(A + "/.ai/verification/%s.json" % cid, "rb").read()
schema = json.load(open(A + "/.ai/verification/_schema.json", encoding="utf-8"))
def ra(a):
    try:
        return open(A + "/.ai/approvals/%s.md" % a, "rb").read()
    except OSError:
        return None
plan = mg.read_plan_tables(A + "/docs/01-plan/features/gain-budget-gmid-sizing.plan.md")
obj = mg.load_verification_record(raw, file_id=cid, schema=schema, read_approval=ra, spec_phase="0.5", plan=plan)
print("OK", sorted(obj["checks"]), {k: v["verdict"] for k, v in obj["checks"].items()})
