"""measure only: FU stand-in -- `from __future__ import annotations` right after the module docstring of DR and ACF
(draft_p3_fu.spec.md: H = B[:1] + [I] + B[1:]). Asserts docstring first and no existing future line."""
import ast
import sys

ROOT = sys.argv[1]
for rel in ("design_report.py", "audit_current_forced.py"):
    p = "%s/skills/analog-gmid-design/assets/%s" % (ROOT, rel)
    raw = open(p, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    tree = ast.parse(raw)
    b0 = tree.body[0]
    assert isinstance(b0, ast.Expr) and isinstance(b0.value, ast.Constant) and isinstance(b0.value.value, str), rel
    assert "from __future__" not in raw, rel
    lines = raw.split(nl)
    lines.insert(b0.end_lineno, "from __future__ import annotations")
    open(p, "w", encoding="utf-8", newline="").write(nl.join(lines))
    print("FU", rel, "after line", b0.end_lineno)
