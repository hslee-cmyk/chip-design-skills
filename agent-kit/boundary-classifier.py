#!/usr/bin/env python
"""Architectural-change classifier for db/design Verilog commits.

Computes a STRUCTURAL-DELTA signature from a commit's Verilog diff and classifies it:
  ARCH  -> architectural change (new/removed FSM, module, instance, case-arm, or a
           clock/reset re-wire). The agent must ESCALATE: present partitioning options
           + rationale to the human, do NOT decide ad-hoc.
  IFACE -> interface change only (ports added/removed). Whole-design fan-out review.
  LOCAL -> in-place logic/expression edit. Safe for the constrained Implementer;
           correctness is checked by the Prover (formal) / directed sim, NOT here.

This is the Architect-advisor's classifier. The point (per the AI-failure forensics):
the "new FSM vs new state" decision must be COMPUTED from the structural delta, never
judged from a grepped fragment.

Usage (run inside db/design):
  python boundary-classifier.py claude-implemented-version..HEAD
  python boundary-classifier.py <commit>
"""
import subprocess, re, sys

# patterns evaluated on a diff line with its leading +/- stripped
PAT = {
    'MOD'  : re.compile(r'^\s*module\s+\w'),
    'ALW'  : re.compile(r'^\s*always\b'),
    'CASE' : re.compile(r'^\s*(unique\s+|priority\s+)?case\s*\('),
    'ARM'  : re.compile(r'^\s*`\w+\s*:'),                 # FSM state case-arm: `STREAM_WRITE:
    'STATE': re.compile(r"^\s*`define\s+\w+\s+\(?\s*\d+'b|^\s*localparam\b.*\b\w*(STATE|IDLE|_ST)\w*\s*="),
    'INST' : re.compile(r'^\s*[A-Za-z_]\w*(\s*#\(.*\))?\s+u_\w+\s*\('),
    'PORT' : re.compile(r'^\s*(input|output|inout)\b(?!\s+integer)'),
}
# a clock/reset PORT CONNECTION line (.i_refClk(...), .i_rst_n(...))
CLKCONN = re.compile(r'^\s*\.\s*\w*([Cc]lk|CLK|rst_n|[Rr]st)\w*\s*\(')
BACKUP  = re.compile(r'backup|\.bak\b|/bak/', re.I)

STRUCT_KEYS = ['MOD', 'ALW', 'CASE', 'ARM', 'STATE', 'INST']


def commits(rev):
    out = subprocess.check_output(['git', 'rev-list', '--reverse', rev], text=True) \
        if '..' in rev else rev + '\n'
    return [h for h in out.split() if h]


def subject(h):
    return subprocess.check_output(['git', 'show', '-s', '--format=%s', h], text=True,
                                   errors='replace').strip()


def analyze(h):
    patch = subprocess.check_output(['git', 'show', h, '--', '*.v'], text=True, errors='replace')
    sig = {f'+{k}': 0 for k in STRUCT_KEYS}
    sig.update({f'-{k}': 0 for k in STRUCT_KEYS})
    sig['clk_rewire'] = 0          # clock/reset connection on a REMOVED line = re-wire
    sig['+PORT'] = sig['-PORT'] = 0
    skip = False
    for ln in patch.splitlines():
        if ln.startswith('diff --git'):
            skip = bool(BACKUP.search(ln))                      # ignore backup files
            continue
        if skip or not ln or ln[0] not in '+-' or ln[:3] in ('+++', '---'):
            continue
        sign, body = ln[0], ln[1:]
        for k, rx in PAT.items():
            if rx.search(body):
                if k == 'PORT':
                    sig[f'{sign}PORT'] += 1
                else:
                    sig[f'{sign}{k}'] += 1
        if sign == '-' and CLKCONN.search(body):
            sig['clk_rewire'] += 1
    added  = sum(sig[f'+{k}'] for k in STRUCT_KEYS)
    removed = sum(sig[f'-{k}'] for k in STRUCT_KEYS)
    ports = sig['+PORT'] + sig['-PORT']
    if added or removed or sig['clk_rewire']:
        lab, score = 'ARCH', added + removed + 5 * sig['clk_rewire']
    elif ports:
        lab, score = 'IFACE', ports
    else:
        lab, score = 'LOCAL', 0
    return lab, score, sig


def reason(sig):
    bits = []
    for k in STRUCT_KEYS:
        if sig[f'+{k}']: bits.append(f'+{k}={sig["+"+k]}')
        if sig[f'-{k}']: bits.append(f'-{k}={sig["-"+k]}')
    if sig['clk_rewire']: bits.append(f'CLK_REWIRE={sig["clk_rewire"]}')
    if sig['+PORT'] or sig['-PORT']: bits.append(f'PORT=+{sig["+PORT"]}/-{sig["-PORT"]}')
    return ' '.join(bits) or '(none)'


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    rev = sys.argv[1] if len(sys.argv) > 1 else 'claude-implemented-version..HEAD'
    rows = []
    for h in commits(rev):
        lab, score, sig = analyze(h)
        rows.append((lab, score, h, subject(h), reason(sig)))
    order = {'ARCH': 0, 'IFACE': 1, 'LOCAL': 2}
    rows.sort(key=lambda r: (order[r[0]], -r[1]))
    print(f"{'LABEL':5} {'sc':>3}  {'hash':8}  subject / signal")
    print('-' * 110)
    for lab, score, h, subj, why in rows:
        print(f"{lab:5} {score:>3}  {h[:8]}  {subj[:52]}")
        if lab != 'LOCAL':
            print(f"{'':19}  -> {why}")
    from collections import Counter
    c = Counter(r[0] for r in rows)
    print('-' * 110)
    print('totals:', dict(c), 'of', len(rows))
