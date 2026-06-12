#!/usr/bin/env python
"""Bug-class ROUTER — codifies the §6 routing table deterministically.

Companion to `boundary-classifier.py`. The classifier answers the STRUCTURAL question
("new FSM vs new state" = ARCH/IFACE/LOCAL, COMPUTED not judged); this router answers the
VERIFICATION question — given a failure-class, the cheapest reliable verifier and its owner
agent. It is the deterministic backbone of the verilog-rtl-architect-advisor §3 "Route" table
and the verilog-rtl-reviewer hand-off (STATIC findings it keeps vs SIM/FORMAL it forwards to
the Prover). Grounded in ../knowledge/ai-verilog-coding-methodology.md §5–§6,
../analysis/claude-diff/failure-taxonomy.md, ../experiments/formal-demo/:
  FORMAL   -> verilog-rtl-prover (sby)            self-contained logic/timing, proven on real RTL
  STATIC   -> verilog-rtl-reviewer (S1–S13)       reachability / fan-out / lint / RAM / width
  SIM      -> directed sim (cloud0/xcelium-mcp)   CDC-timing tier formal gives up (clock collapse)
  ESCALATE -> verilog-rtl-architect-advisor       architectural partitioning -> ADR + guarding SVA

NUANCE (why a router, not a 1:1 table): structural label and taxonomy class are ORTHOGONAL —
2ebd51f (count==0 deadlock) is structurally LOCAL yet routes to FORMAL by its T5 class. So
`--commit` resolves only ARCH/IFACE/LOCAL; a LOCAL finding is then routed by its T1..T9 class
(detected by the reviewer/architect-advisor signatures, not here).

Usage:
  python bug-class-router.py T5                # route for one class (T1..T9 / ARCH/IFACE/LOCAL / full name)
  python bug-class-router.py --commit 2ebd51f  # structural label via boundary-classifier, then route
  python bug-class-router.py --table           # full routing table
"""
import os, sys, subprocess

HERE       = os.path.dirname(os.path.abspath(__file__))
CLASSIFIER = os.path.join(HERE, 'boundary-classifier.py')
DB_DESIGN  = os.getcwd()  # invoke from within db/design (agent docs cd there first)

NAMES = {
    'T1': 'PROTOCOL_SPEC',  'T2': 'PORT_INTEGRATION', 'T3': 'CLOCK_RESET_CDC',
    'T4': 'TIMING_CYCLE',   'T5': 'FSM_CORNER_DEADLOCK', 'T6': 'POINTER_HANDSHAKE',
    'T7': 'STRUCTURE_STYLE', 'T8': 'FPGA_RAM', 'T9': 'WIDTH_TRUNCATION',
    'CDC': 'CDC-timing (cross-domain)',
    'ARCH': 'ARCH (structural-delta)', 'IFACE': 'IFACE (ports-only)', 'LOCAL': 'LOCAL (in-place edit)',
}
ORDER = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'CDC', 'ARCH', 'IFACE', 'LOCAL']

# class -> {route, owner_agent, rationale, example_commit}.  Faithful to §6 / taxonomy.
ROUTES = {
    'T1': dict(route='STATIC', owner_agent='verilog-rtl-reviewer', example_commit='5b61531',
               rationale='Protocol-relational dead-code -> STATIC reachability (reviewer S12); '
                         'formal needs costly env-contract (E1: free-input deep BMC FAIL).'),
    'T2': dict(route='STATIC', owner_agent='verilog-rtl-reviewer', example_commit='dcfa6d2',
               rationale='Integration -> STATIC fan-out/filelist/read-back audit; zero fan-out = dead feature.'),
    'T3': dict(route='STATIC', owner_agent='verilog-rtl-reviewer', example_commit='86a1796',
               rationale='Clock/reset CONNECTION provenance -> STATIC (reviewer); but CDC-TIMING (2-FF) -> SIM/multiclock-formal.'),
    'T4': dict(route='FORMAL', owner_agent='verilog-rtl-prover', example_commit='05a53c5',
               rationale='Sync-read cycle-latency -> FORMAL when single-clock, else directed SIM; never sample read-data same cycle as rd_en.'),
    'T5': dict(route='FORMAL', owner_agent='verilog-rtl-prover', example_commit='2ebd51f',
               rationale='Self-contained FSM deadlock / degenerate (count==0) load -> FORMAL (sby); proven on real ext_backTelInterface.'),
    'T6': dict(route='FORMAL', owner_agent='verilog-rtl-prover', example_commit='737070b',
               rationale='Circular-pointer wrap/off-by-one -> FORMAL on boundary corners + STATIC smell (no zero-extend / missing ~full).'),
    'T7': dict(route='STATIC', owner_agent='verilog-rtl-reviewer', example_commit='72b2219',
               rationale='Non-compiling/implicit-net style -> STATIC lint with `default_nettype none (warnings = build errors).'),
    'T8': dict(route='STATIC', owner_agent='verilog-rtl-reviewer', example_commit='c69a048',
               rationale='RAM inference (one write port / ramstyle / init) -> STATIC + synthesis RAM-inference report.'),
    'T9': dict(route='STATIC', owner_agent='verilog-rtl-reviewer', example_commit='f451926',
               rationale='Index-vs-value width mismatch -> STATIC index-out-of-range lint; keep header/decl widths in sync.'),
    'CDC': dict(route='SIM', owner_agent='directed sim (cloud0/xcelium-mcp); or prover via multiclock harness', example_commit='86a1796',
                rationale='Cross-domain (2-FF/CDC) TIMING tier single-clock formal abstracts away -> directed sim, '
                          'OR multiclock formal (property-library TPL-7, fairness harness, proven in cdc_demo) when justified. '
                          'SIM sub-tier of T3 (gated-clock) and T4 (variable/CDC read-latency).'),
    'ARCH': dict(route='ESCALATE', owner_agent='verilog-rtl-architect-advisor', example_commit='3f979ac',
                 rationale='New/removed FSM-module-instance-case-arm or clock re-wire -> ESCALATE ADR (>=20 major) with partitioning options + guarding SVA.'),
    'IFACE': dict(route='STATIC', owner_agent='verilog-rtl-reviewer', example_commit='768ff83',
                  rationale='Ports-only change -> whole-design fan-out audit (same as T2) before proceeding.'),
    'LOCAL': dict(route='RECLASSIFY', owner_agent='verilog-rtl-architect-advisor -> taxonomy router', example_commit='2ebd51f',
                  rationale='No architectural boundary; NOT statically verified by itself -- route the finding by its T1..T9 class (e.g. T5 deadlock -> FORMAL).'),
}

ALIAS = {c: c for c in ORDER}
ALIAS.update({v.split()[0]: k for k, v in NAMES.items()})  # full name (e.g. PROTOCOL_SPEC) -> code


def lookup(key):
    code = ALIAS.get(key.strip().upper())
    return code, (ROUTES[code] if code else None)


def print_route(code):
    e = ROUTES[code]
    print(f"{code}  {NAMES[code]}")
    print(f"  route          : {e['route']}")
    print(f"  owner_agent    : {e['owner_agent']}")
    print(f"  rationale      : {e['rationale']}")
    print(f"  example_commit : {e['example_commit']}  (db/design)")


def print_table():
    print("| Class | Route | Owner agent | Example | Rationale |")
    print("|---|---|---|---|---|")
    for c in ORDER:
        e = ROUTES[c]
        print(f"| {c} {NAMES[c]} | {e['route']} | {e['owner_agent']} | {e['example_commit']} | {e['rationale']} |")


def route_commit(commit):
    """Run the validated structural-delta tool in db/design, then route by its label."""
    if not os.path.isdir(DB_DESIGN):
        print(f"db/design submodule not found at {DB_DESIGN}"); return 2
    try:
        r = subprocess.run([sys.executable, CLASSIFIER, commit], cwd=DB_DESIGN,
                           capture_output=True, text=True)
    except OSError as ex:
        print(f"failed to run boundary-classifier.py: {ex}"); return 2
    label = next((t[0] for t in (ln.split() for ln in r.stdout.splitlines())
                  if t and t[0] in ('ARCH', 'IFACE', 'LOCAL')), None)
    if not label:
        sys.stderr.write(r.stdout + r.stderr)
        print(f"could not classify {commit} (boundary-classifier emitted no ARCH/IFACE/LOCAL row)"); return 2
    print(f"structural-delta label for {commit[:8]} : {label}\n")
    if label == 'LOCAL':
        print("-> route the finding by its taxonomy class (T1..T9).")
        print("   structural-delta is LOCAL (no architectural boundary); the *correctness* route")
        print("   depends on the bug class, which is detected by the verilog-rtl-reviewer /")
        print("   architect-advisor signatures, NOT by this structural classifier.")
        print("   e.g. 2ebd51f is LOCAL but is a T5 deadlock -> FORMAL (verilog-rtl-prover).")
        return 0
    print_route(label)  # ARCH -> ESCALATE, IFACE -> STATIC fan-out
    return 0


def main(argv):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__); return 0
    if argv[0] == '--table':
        print_table(); return 0
    if argv[0] == '--commit':
        if len(argv) < 2:
            print("usage: bug-class-router.py --commit <hash>"); return 2
        return route_commit(argv[1])
    code, e = lookup(argv[0])
    if not e:
        print(f"unknown class '{argv[0]}'. known: {', '.join(ORDER)} (or full names)."); return 2
    print_route(code); return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
