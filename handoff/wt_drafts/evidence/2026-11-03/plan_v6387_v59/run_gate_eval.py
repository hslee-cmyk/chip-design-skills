"""v57: run ask_gate.evaluate directly for headers {PLAN-AP, C4-Q2}; read-only (prints errors). Output to gate_eval_out.txt."""
import sys, hashlib
HOOKS = r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/.claude/hooks"
sys.path.insert(0, HOOKS)
import ask_gate, ask_gate_rules
R = ask_gate_rules.load_rules()
errs, gate, kind = ask_gate.evaluate({"PLAN-AP7"}, ask_gate.DEF_DIR, ask_gate.DEF_BASE, R)
raw = open(gate, "rb").read() if gate else b""
out = [f"gate={gate}", f"kind={kind}", f"gate_sha256={hashlib.sha256(raw).hexdigest()}", f"rules forbidden={R['forbidden']}", f"prefixes={R['prefixes']}",
       f"measured_only={R.get('measured_only')}", f"errors={len(errs)}"] + [" - " + e for e in errs]
open(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/plan_v6387_v59/gate_eval_out.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
