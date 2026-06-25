#!/usr/bin/env python
"""PreToolUse(Bash) guard: block `> nul` redirects in MSYS bash.

On this Windows machine the Bash tool is MSYS2 (POSIX sh), which has NO `nul`
device. A cmd/PowerShell habit like `> nul` / `2> nul` therefore does NOT discard
output — it creates a real junk file named `nul` in the working directory. Use
`/dev/null` instead. This hook blocks (exit 2) such commands and tells the caller
to fix them, so the junk file is never created.

Matches redirects to a bare `nul` target (any case, optional quotes or `./`),
e.g. `> nul`, `>nul`, `2>nul`, `>> nul`, `&> nul`, `1> "nul"`. Does NOT match
`/dev/null`, `nul.log`, `nullable`, or `nul` used as a non-redirect argument.
Known limitation: a literal `> nul` inside a quoted string is also flagged
(conservative). Fail-open (exit 0) on any parse error.
"""
import sys, json, re

# redirect op (optional fd digits or &) then a bare nul target at a token boundary
PAT = re.compile(
    r'(?:^|\s)(?:[0-9]+|&)?>>?\s*(?:"nul"|\'nul\'|(?:\./)?nul)(?=$|[\s;&|)])',
    re.IGNORECASE,
)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not cmd:
        return 0
    if not PAT.search(cmd):
        return 0
    sys.stderr.write(
        "BLOCKED by guard-bash-nul: redirect to `nul` detected.\n"
        "This is MSYS2 bash — there is NO `nul` device, so `> nul` / `2> nul` does\n"
        "NOT discard output; it creates a real junk file named 'nul'.\n"
        "Use '/dev/null' instead, e.g.  > /dev/null 2>&1\n"
    )
    return 2


sys.exit(main())
