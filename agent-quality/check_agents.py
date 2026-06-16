#!/usr/bin/env python
"""check_agents.py - verify agent definitions follow the best-practice rubric.

Static gate distilled from:
  [A] Anthropic, "Building Effective Agents" (Simplicity / Transparency / ACI; tool design)
  [O] OpenAI,    "A Practical Guide to Building Agents" (Model/Tools/Instructions;
                  single->multi-agent; layered guardrails; human-in-the-loop)

Rubric + which rules are AUTO vs JUDGE: agent-quality/AGENT_BEST_PRACTICES.md

Usage (from repo root):
    python agent-quality/check_agents.py                  # all agents
    python agent-quality/check_agents.py agents/foo.md     # one agent
Exit code 1 if any agent has a FAIL (so it can gate a commit / CI step).
No third-party deps (frontmatter is parsed as text, not via PyYAML).
"""
import sys, os, re, glob

# files in agents/ that are NOT agent definitions
NON_AGENTS = {"readme.md", "agent_best_practices.md", "agent-validation-prompt.md"}
KNOWN_MODELS = ("opus", "sonnet", "haiku", "claude-")

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"


def load(path):
    """Return (frontmatter_text, body_text). Frontmatter = between the first two '---'."""
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        return None, text          # no frontmatter
    return m.group(1), m.group(2)


def has(text, *needles):
    t = text.lower()
    return any(n.lower() in t for n in needles)


def fm_value(fm, key):
    """Single-line scalar value of a top-level frontmatter key, or '' if absent/block."""
    m = re.search(r"(?m)^%s:\s*(.*)$" % re.escape(key), fm or "")
    return (m.group(1).strip() if m else "")


def check(path):
    """Return list of (rule_id, status, message)."""
    name_stem = os.path.splitext(os.path.basename(path))[0]
    fm, body = load(path)
    r = []
    if fm is None:
        r.append(("FM", FAIL, "no YAML frontmatter (--- ... ---) found"))
        return r
    fmb = fm + "\n" + body  # searchable whole for content signals

    # --- frontmatter structural (FAIL if missing core fields) ---
    name = fm_value(fm, "name")
    r.append(("name", PASS if name else FAIL,
              ("name='%s'" % name) + ("" if name == name_stem else " != filename '%s'" % name_stem)
              if name else "missing 'name:'"))
    if name and name != name_stem:
        r[-1] = ("name", WARN, "name='%s' should equal filename stem '%s'" % (name, name_stem))

    has_desc = bool(re.search(r"(?m)^description:", fm))
    r.append(("desc", PASS if has_desc else FAIL, "description present" if has_desc else "missing 'description:'"))

    # R1 Model fit
    model = fm_value(fm, "model")
    if not model:
        r.append(("R1-model", FAIL, "missing 'model:' (pick a tier per task) [O]"))
    elif any(k in model.lower() for k in KNOWN_MODELS):
        r.append(("R1-model", PASS, "model=%s (tier appropriateness = JUDGE)" % model))
    else:
        r.append(("R1-model", WARN, "model='%s' not a known tier" % model))

    # R2 Tool minimality & clarity (ACI)
    tools = fm_value(fm, "tools")
    if not tools:
        r.append(("R2-tools", FAIL, "missing 'tools:' (explicit minimal list) [A,O]"))
    elif "*" in tools or "all tools" in tools.lower():
        r.append(("R2-tools", WARN, "tools is a wildcard/all-tools; prefer explicit minimal set [A-ACI]"))
    else:
        n = len([t for t in tools.split(",") if t.strip()])
        st = WARN if n > 15 else PASS
        r.append(("R2-tools", st, "%d explicit tools%s (overlap/clarity = JUDGE)"
                  % (n, " — review for overlap [O tool-overload]" if n > 15 else "")))

    # R4 Single responsibility + boundaries (when-to-use AND when-NOT)
    pos = has(fm, "use ", "use it when", "use proactively", "사용", "when ")
    neg = has(fm, "do not", "does not", "don't", "not for", "not use", "not own",
              "not decide", "not implement", "not classify", "not edit", "hands off",
              "instead of", "instead.", "금지", "되돌", "❌", "않는")
    if pos and neg:
        r.append(("R4-scope", PASS, "has when-to-use AND boundary (do-NOT) [O,A]"))
    elif pos and not neg:
        r.append(("R4-scope", FAIL, "no explicit boundary — add when-NOT-to-use / HANDS OFF / 금지 [O,A]"))
    else:
        r.append(("R4-scope", WARN, "scope signals weak (when-to-use unclear)"))

    # R6 Routing triggers
    r.append(("R6-triggers", PASS if has(fm, "trigger", "트리거") else WARN,
              "Triggers present" if has(fm, "trigger", "트리거") else "no Triggers: list (routing) [O]"))

    # R7 Transparency (explicit report/output)
    r.append(("R7-transparency", PASS if has(body, "보고", "report", "output format", "산출물", "보고 형식", "must report") else WARN,
              "report/output format present" if has(body, "보고", "report", "산출물", "output format") else "no explicit report/output format [A]"))

    # R8 Stop conditions / scope-exit
    r.append(("R8-stop", PASS if has(fmb, "stop", "iteration", "blocker", "되돌린다", "되돌린", "halt", "exit condition", "종료", "scope 밖", "escalat") else WARN,
              "stop/scope-exit present" if has(fmb, "stop", "iteration", "blocker", "되돌린", "halt", "종료", "escalat") else "no stop/iteration/scope-exit condition [A,O]"))

    # R9 Guardrails / hard constraints
    r.append(("R9-guardrails", PASS if has(body, "하드 제약", "금지", "must not", "must NOT", "절대", "수정 금지", "forbidden", "⚠️") else WARN,
              "hard constraints present" if has(body, "하드 제약", "금지", "must not", "절대", "forbidden") else "no hard-constraint / guardrail section [O,A]"))

    # R10 Human escalation / handoff
    r.append(("R10-escalate", PASS if has(fmb, "escalat", "handoff", "hand off", "hands off", "되돌린다", "human", "사람", "넘긴다", "넘긴", "router", "라우팅") else WARN,
              "escalation/handoff present" if has(fmb, "escalat", "handoff", "hands off", "human", "사람", "넘긴", "router") else "no escalation/handoff path [O,A]"))

    # R11 Honest limits
    r.append(("R11-limits", PASS if has(body, "한계", "limits", "limitation", "증명 못", "못 하는", "honest", "정직") else WARN,
              "limits section present" if has(body, "한계", "limits", "증명 못", "honest") else "no honest-limits section [A]"))

    # R12 Evals / regression
    r.append(("R12-evals", PASS if has(fmb, "regression", "answer key", "answer-key", "eval", "회귀", "검증됨", "pass/fail", "test") else WARN,
              "eval/regression referenced" if has(fmb, "regression", "answer key", "eval", "회귀", "검증됨") else "no eval/regression/answer-key reference [O,A]"))

    # R3 Instructions structured (presence only; quality = JUDGE)
    structured = bool(re.search(r"(?m)^#{1,4}\s", body)) or bool(re.search(r"(?m)^\s*\d+[.)]\s", body))
    r.append(("R3-steps", PASS if structured else WARN,
              "structured procedure present (steps/actions/edge-cases = JUDGE)" if structured else "no structured steps/headings [O]"))

    return r


def main():
    try:  # Windows consoles default to a non-UTF-8 codepage (cp949/cp1252)
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    here = os.path.dirname(os.path.abspath(__file__))
    agents_dir = os.path.join(os.path.dirname(here), "agents")  # ../agents
    args = sys.argv[1:]
    files = args if args else sorted(
        p for p in glob.glob(os.path.join(agents_dir, "*.md"))
        if os.path.basename(p).lower() not in NON_AGENTS)

    print("Agent best-practices check  (rubric: agent-quality/AGENT_BEST_PRACTICES.md)")
    print("=" * 70)
    any_fail = False
    for path in files:
        rows = check(path)
        nF = sum(1 for _, s, _ in rows if s == FAIL)
        nW = sum(1 for _, s, _ in rows if s == WARN)
        any_fail |= nF > 0
        verdict = "FAIL" if nF else ("WARN" if nW else "PASS")
        print("\n%-34s  [%s]  (%d FAIL, %d WARN)" % (os.path.basename(path), verdict, nF, nW))
        for rid, st, msg in rows:
            if st != PASS:
                print("   %-4s %-16s %s" % (st, rid, msg))
        if nF == 0 and nW == 0:
            print("   all checks pass")
    print("\n" + "=" * 70)
    print("Reminder: R3/R5/R7/R9/R10/R13 also need a JUDGE pass — see agent-validation-prompt.md")
    print("RESULT:", "FAIL (fix blocking items)" if any_fail else "no blocking FAILs")
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
