"""measure only (W-1 (가) -- T0 stand-in part): the 3 unit selftests import the non-engine names that a future complete shim
(TL/SR/DR) would no longer bind from their origin instead (p3_followup_questions.md §2.4 (가) text). Engine names on the same
line untouched. Exact-anchor edits, exactly one occurrence each, else exit 1."""
import sys

ROOT = sys.argv[1]
U = ROOT + "/skills/analog-gmid-design/assets/tests/unit/"
EDITS = {
    "test_selftest_topology_library.py": [
        ("from topology_library import (current_reuse_telescopic_topology, math, miller_ota_topology,",
         "import math  # noqa: E402\nfrom topology_library import (current_reuse_telescopic_topology, miller_ota_topology,")],
    "test_selftest_sizing_recipe.py": [
        (" _build_theta_evaluator, _dc_replace, _full_circuit_response,", " _build_theta_evaluator, _full_circuit_response,"),
        (" find_optimal_sizing, json, knee_L_for_kind, load_topology, math, nmcnr_predict_ac_response, np, optimize_full_circuit_budget,",
         " find_optimal_sizing, knee_L_for_kind, load_topology, optimize_full_circuit_budget,"),
        ("from regression_runner import run_regression_case  # noqa: E402\n",
         "from regression_runner import run_regression_case  # noqa: E402\n"
         "from dataclasses import replace as _dc_replace  # noqa: E402\nimport json  # noqa: E402\nimport math  # noqa: E402\n"
         "import numpy as np  # noqa: E402\nfrom topology_library import nmcnr_predict_ac_response  # noqa: E402\n")],
    "test_selftest_design_report.py": [
        ("from design_report import (assemble_report_data, build_topology_device_table, os, render_html_report)  # noqa: E402",
         "from design_report import (assemble_report_data, build_topology_device_table, render_html_report)  # noqa: E402")],
}
for f, eds in EDITS.items():
    raw = open(U + f, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    t = raw.replace("\r\n", "\n")
    for old, new in eds:
        if t.count(old) != 1:
            sys.exit("anchor %s count %d: %s" % (f, t.count(old), old[:60]))
        t = t.replace(old, new)
    open(U + f, "w", encoding="utf-8", newline="").write(t.replace("\n", nl))
    print("T0-W1 stand-in", f, len(eds))
