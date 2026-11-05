"""기준선 칸별 diff (639eef25 대 머리) 를 판정 제안과 대조."""
import json, subprocess, sys
W = sys.argv[1]
F = "skills/analog-gmid-design/gmid_engine/tests/integration/fixtures/u17_1b_s0_baseline.json"
def show(rev, path):
    return json.loads(subprocess.run(["git", "-C", W, "show", rev + ":" + path], capture_output=True, check=True).stdout.decode("utf-8"))
old, new = show("639eef25", F), show("HEAD", F)
prop = show("639eef25", ".ai/verification/20261104-hcs/s0_baseline_proposal.json")
diffs = []
def walk(a, b, path):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                diffs.append((path + (k,), a.get(k, "<없음>"), b.get(k, "<없음>")))
            else:
                walk(a[k], b[k], path + (k,))
    elif a != b:
        diffs.append((path, a, b))
walk(old, new, ())
want = {("folded_cascode", "start", "row_fp", d): fp for d, fp in prop["start.row_fp"].items()}
want[("folded_cascode", "start", "ladder_fp")] = prop["start.ladder_fp"]
got = {p: b for p, _a, b in diffs}
print("변경 칸", len(diffs), "제안 칸", len(want))
print("row_fp 칸", sum(1 for p in got if p[:3] == ("folded_cascode", "start", "row_fp")), "ladder", sum(1 for p in got if p == ("folded_cascode", "start", "ladder_fp")))
print("제안과 같음", got == want)
print("제안 밖 칸", [p for p in got if p not in want])
print("제안인데 안 바뀜·값 다름", [p for p in want if got.get(p) != want[p]])
print("다른 회로·최상위 변경", sorted({p[0] for p in got if p[0] != "folded_cascode"}))
raw = subprocess.run(["git", "-C", W, "diff", "--numstat", "639eef25", "HEAD", "--", F], capture_output=True).stdout.decode()
print(raw.strip())
