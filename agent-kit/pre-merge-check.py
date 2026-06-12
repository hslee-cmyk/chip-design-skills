#!/usr/bin/env python
"""Pre-merge architectural GATE (the architect-advisor's CI wiring).

Classify a change with boundary-classifier.py and gate the merge:
  ARCH  -> BLOCK (exit 1): ADR + architect-advisor escalation required. Partitioning ("new FSM
           vs new state", new module/instance, clock re-wire) is a HUMAN decision, not an ad-hoc
           edit. Major (score>=20) vs minor-structural (<=3) noted.
  IFACE -> WARN: whole-design fan-out audit (T2) before merge.
  LOCAL -> PASS here: route each finding to its verifier by taxonomy class (bug-class-router.py)
           -- correctness is NOT gated structurally; it is owned by reviewer (STATIC) / prover
           (FORMAL) / directed sim (CDC).

Usage (run inside db/design):
  python ../../.ai/agent-proposals/pre-merge-check.py <commit-or-range>   # e.g. HEAD, or A..B
Intended as a pre-merge / CI step on db/design. Exit code 1 blocks the merge when an
un-escalated architectural change is present.
"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CLS = os.path.join(HERE, 'boundary-classifier.py')


def classify(rev):
    out = subprocess.run([sys.executable, CLS, rev], capture_output=True, text=True,
                         errors='replace').stdout
    rows = []
    for ln in out.splitlines():
        m = re.match(r'^(ARCH|IFACE|LOCAL)\s+(\d+)\s+(\w+)\s+(.*)', ln)
        if m:
            rows.append(m.groups())   # (label, score, hash, subject)
    return rows


def main(argv):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    rev = argv[0] if argv else 'HEAD'
    rows = classify(rev)
    if not rows:
        print(f"pre-merge gate: no classifiable .v change in {rev}"); return 0
    arch = [r for r in rows if r[0] == 'ARCH']
    iface = [r for r in rows if r[0] == 'IFACE']
    local = [r for r in rows if r[0] == 'LOCAL']
    print(f"pre-merge gate for {rev}: {len(arch)} ARCH / {len(iface)} IFACE / {len(local)} LOCAL\n")
    for _, sc, h, subj in arch:
        tier = 'MAJOR' if int(sc) >= 20 else 'minor-structural'
        print(f"  [BLOCK] ARCH score={sc} ({tier})  {h[:8]}  {subj[:48]}")
        print(f"          -> ADR required + escalate to verilog-rtl-architect-advisor")
        print(f"             (partitioning is a human decision; see adr-template.md)")
    for _, sc, h, subj in iface:
        print(f"  [WARN]  IFACE  {h[:8]}  {subj[:48]}  -> whole-design fan-out audit (T2)")
    if local:
        print(f"  [PASS]  {len(local)} LOCAL  -> route each finding by taxonomy class (bug-class-router.py);")
        print(f"          correctness owned by reviewer(STATIC) / prover(FORMAL) / sim(CDC), not gated here.")
    blocked = bool(arch)
    print(f"\nGATE: {'BLOCK -- un-escalated architectural change (ADR required)' if blocked else 'PASS -- no architectural boundary crossed'}")
    return 1 if blocked else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
