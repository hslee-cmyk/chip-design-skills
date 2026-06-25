#!/usr/bin/env python
"""PreToolUse guard (bkit-agnostic, USER-scope safe).

Policy: formal/lint scratch artifacts must NOT be written inside a shared-RTL
git submodule (chip RTL is read-only from a consuming project). They belong in a
dedicated verification workspace OUTSIDE the submodule.

Designed to be registered at USER scope (~/.claude/settings.json) so it applies
to every project, yet harmless in projects with no such submodule: it fail-opens
(exit 0) whenever the written path is not inside a policed submodule directory.
This is why it composes cleanly with bkit's own plugin hooks (Claude Code fires
ALL hooks across plugin + user + project scopes as a union; none shadow another).

Per-project override (optional), via env var:
  GUARD_SUBMODULE_DIRS   comma-separated path fragments, default "db/design"
  GUARD_DEDICATED_DIR    human hint for where work should go, default "formal/"
Fail-open on ANY error so it never blocks legitimate work by accident.
"""
import sys, json, os

DIRS = [d.strip().strip("/").lower()
        for d in os.environ.get("GUARD_SUBMODULE_DIRS", "db/design").split(",")
        if d.strip()]
DEDICATED = os.environ.get("GUARD_DEDICATED_DIR", "formal/")

FORMAL_EXTS = {".sby", ".smt2", ".il", ".ys", ".gtkw", ".vcd", ".fst",
               ".yw", ".smtc", ".witness", ".eqy", ".vlt"}


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") not in ("Write", "Edit"):
        return 0
    fp = (data.get("tool_input") or {}).get("file_path") or ""
    if not fp:
        return 0
    norm = fp.replace("\\", "/").lower()
    if not any(("/" + d + "/") in norm for d in DIRS):
        return 0
    base = os.path.basename(norm)
    ext = os.path.splitext(base)[1]
    blocked = (
        base == "def.vh"
        or ext in FORMAL_EXTS
        or base.endswith("_stub.v")
        or base.endswith("_formal.v")
        or "/engine_" in norm
        or "/obj_dir/" in norm
    )
    if not blocked:
        return 0
    msg = (
        "BLOCKED by guard-submodule-formal: '" + fp + "'\n"
        "POLICY: formal/lint artifacts/runs MUST live OUTSIDE the shared-RTL\n"
        "submodule (" + ", ".join(DIRS) + "). Use the dedicated workspace:\n"
        "    <project>/" + DEDICATED + "   <- copy RTL there, run sby/verilator HERE.\n"
        "Reading the submodule RTL is fine; writing formal/lint files INSIDE it is forbidden."
    )
    sys.stderr.write(msg + "\n")
    return 2


sys.exit(main())
