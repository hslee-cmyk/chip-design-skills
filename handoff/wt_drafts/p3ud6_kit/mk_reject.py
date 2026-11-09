"""measure only: apply one D0b reject input (draft_p3_d0b.spec.md '거부해야 할 입력' table) to the working tree of the regen copy.
    python -B mk_reject.py <clone root> <id>
Exact anchors, count must be 1, else exit 1 without writing."""
import os
import sys

ROOT, ID = sys.argv[1:3]
A = ROOT + "/skills/analog-gmid-design/assets/"
PLAN = ROOT + "/docs/01-plan/features/gain-budget-gmid-sizing.plan.md"
REG = ROOT + "/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md"


def sub(path, old, new):
    raw = open(path, encoding="utf-8", newline="").read()
    if raw.count(old) != 1:
        sys.exit("%s anchor count %d in %s" % (ID, raw.count(old), path))
    open(path, "w", encoding="utf-8", newline="").write(raw.replace(old, new))


MOD1_END = "`lut_conditions_from_npz`, gmb 유도(`∂ID/∂VSB`) |"
if ID == "R-A1":
    sub(PLAN, MOD1_END, "`lut_conditions_from_npz`, gmb 유도(`∂ID/∂VSB`), `save_html_report` |")
elif ID == "R-A2":
    raw = open(PLAN, encoding="utf-8", newline="").read()
    line = [l for l in raw.splitlines() if l.startswith("| MOD2 |")]
    assert len(line) == 1
    sub(PLAN, line[0], line[0][:-2] + ", `compute_metric` |")
elif ID == "R-A3":
    with open(A + "sizing_recipe.py", "a", encoding="utf-8", newline="") as fh:
        fh.write("\n\ndef _p3rd_orphan():\n    return 0\n")
elif ID == "R-A4":
    sub(A + "stick_diagram.py", "                        pipeline_result: dict) -> None:",
        "                        pipeline_result: dict, _p3rd_probe=build_stick_diagram) -> None:")
elif ID == "R-A5":
    sub(A + "design_report.py", "from __future__ import annotations\n", "")
elif ID == "R-A6":
    sub(PLAN, "| 레지스트리 등급 R0 레이아웃 함수 |", "| 레지스트리 등급 R0 레이아웃 함수, `_as_set` |")
elif ID == "R-A7":
    pass  # tool deletion -- simulated as no plan output
elif ID == "R-B1":
    sub(REG, "| `size_transistor` | ID=gm/gm_id, W=L·ID/IDu | gmid_sizing_engine |", "| `size_transistor` | ID=gm/gm_id, W=L·ID/IDu | circuit_metrics |")
elif ID == "R-B2":
    sub(REG, "| `quantize_L` | L을 grid_step 배수로 스냅(nearest/floor/ceil) | theta_search |", "| `quantize_L` | L을 grid_step 배수로 스냅(nearest/floor/ceil) | theta_search(S3) |")
elif ID in ("R-B3", "R-E1"):
    new = "〃" if ID == "R-B3" else "theta_search"
    sub(REG, "| `_theta_evidence_for_pair` | 쌍이 theta feed A/A_signed root 또는 C target/reference로 강제되는지 | instance_report_builder |",
        "| `_theta_evidence_for_pair` | 쌍이 theta feed A/A_signed root 또는 C target/reference로 강제되는지 | %s |" % new)
elif ID == "R-C1":
    raw = open(REG, encoding="utf-8", newline="").read()
    i = raw.index("| 이관 목적지 | 근거 규칙 |")
    raw = raw[:i] + "| 이관 목적지 | 근거규칙 |" + raw[i + len("| 이관 목적지 | 근거 규칙 |"):]
    open(REG, "w", encoding="utf-8", newline="").write(raw)
elif ID == "R-C2":
    sub(REG, "| `size_transistor` | ID=gm/gm_id, W=L·ID/IDu | gmid_sizing_engine | A-1 |", "| `size_transistor` | ID=gm/gm_id, W=L·ID/IDu | gmid_sizing_engine | A-9 |")
elif ID == "R-D1":
    sub(REG, "| `validate_theta_declaration_order` | theta 선언순서=실행순서 계약 검사 | circuit_state_graph | A-1 | 보류(Phase 4) |",
        "| `validate_theta_declaration_order` | theta 선언순서=실행순서 계약 검사 | circuit_state_graph | A-1 | 보류(Phase 3) |")
else:
    sys.exit("unknown id")
print("applied", ID)
