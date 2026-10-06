"""auditor 캐시와 오케스트레이터 캐시(<git-common-dir>/gmid-gate-cache/<base>)를 파일 단위로 비교(읽기 전용)."""
import filecmp, os, subprocess, sys
wt, base, mine = sys.argv[1:4]
common = subprocess.run(["git", "-C", wt, "rev-parse", "--git-common-dir"], capture_output=True, check=True, text=True).stdout.strip()
orch = os.path.join(common, "gmid-gate-cache", base)
def files(d):
    out = set()
    for r, ds, fs in os.walk(d):
        ds[:] = [x for x in ds if x not in ("__pycache__", "rejudged")]
        for f in fs:
            if f.endswith(".pyc") or f.startswith("status-"):
                continue
            out.add(os.path.relpath(os.path.join(r, f), d).replace("\\", "/"))
    return out
a, b = files(mine), files(orch)
diff = [p for p in sorted(a & b) if not filecmp.cmp(os.path.join(mine, p), os.path.join(orch, p), shallow=False)]
print("mine", len(a), "orch", len(b), "only_mine", sorted(a - b), "only_orch", sorted(b - a), "content_diff", diff)
