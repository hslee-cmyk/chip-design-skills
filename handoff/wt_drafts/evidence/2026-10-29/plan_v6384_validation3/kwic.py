"""kwic: python kwic.py <file> <pattern> [before] [after] [lineno-only-filter] -> 줄번호와 앞뒤 문맥(UTF-8 stdout)."""
import sys, re, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
f, pat = sys.argv[1], sys.argv[2]; b = int(sys.argv[3]) if len(sys.argv) > 3 else 200; a = int(sys.argv[4]) if len(sys.argv) > 4 else 200
only = int(sys.argv[5]) if len(sys.argv) > 5 else None
for n, line in enumerate(open(f, encoding='utf-8').read().split('\n'), 1):
    if only and n != only: continue
    for m in re.finditer(pat, line):
        print(f"[{n}:{m.start()}] ...{line[max(0,m.start()-b):m.end()+a]}...\n")
