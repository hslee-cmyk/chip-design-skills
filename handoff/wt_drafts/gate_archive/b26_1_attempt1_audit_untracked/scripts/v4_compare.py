# V4 미리보기 대조: T1 출력의 (1) FAIL·exempt 각각에 대해 (a) T1 줄 글 (b) 그 줄이 B1->T1 diff의 추가/바뀐 줄인지
# (c) B1 트리의 같은 파일을 같은 도구(--head B1, 파일 인자)로 돌린 결과에 같은 test·같은 줄 글의 같은 발견이 있었는지.
import json, subprocess, sys, re
cache, iso, b1, t1, card, t1json, outp, b1out = sys.argv[1:9]
PY = sys.executable

def git(*a):
    return subprocess.run(["git", "-C", iso] + list(a), capture_output=True, check=True).stdout

d = json.load(open(t1json, encoding="utf-8"))
files = d["files"]
b1_files = [f for f in files if subprocess.run(["git", "-C", iso, "cat-file", "-e", "%s:%s" % (b1, f)]).returncode == 0]
r = subprocess.run([PY, cache + "/test_lint.py", "--root", iso, "--interface-card", card, "--head", b1] + b1_files,
                   capture_output=True)
open(b1out, "wb").write(r.stdout)
db = json.loads(r.stdout.decode("utf-8"))

def lines(rev, f):
    return git("show", "%s:%s" % (rev, f)).decode("utf-8").splitlines()

def added_lines(f):
    out = git("diff", "-U0", "--no-renames", b1, t1, "--", f).decode("utf-8")
    s = set()
    for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", out, re.M):
        st = int(m.group(1)); n = int(m.group(2)) if m.group(2) is not None else 1
        s |= set(range(st, st + n))
    return s

cache_l = {}
def L(rev, f):
    k = (rev, f)
    if k not in cache_l:
        cache_l[k] = lines(rev, f)
    return cache_l[k]

b1_set = {}
for x in db.get("findings", []):
    if x["rule"] == "(1)":
        txt = L(b1, x["file"])[x["line"] - 1].strip()
        b1_set.setdefault((x["file"], x["test"], txt, x["output"]), []).append(x["line"])
rows = []
added_cache = {}
for x in d["findings"]:
    if x["rule"] != "(1)":
        continue
    f = x["file"]
    if f not in added_cache:
        added_cache[f] = added_lines(f) if f in b1_files else None
    txt = L(t1, f)[x["line"] - 1].strip()
    new_file = f not in b1_files
    changed = (not new_file) and x["line"] in added_cache[f]
    pre = [k for k in b1_set if k[0] == f and k[1] == x["test"] and k[2] == txt]
    rows.append({"file": f, "test": x["test"], "t1_line": x["line"], "text": txt, "output": x["output"],
                 "new_file": new_file, "changed_line": changed,
                 "b1_same_finding": [{"b1_line": l, "b1_output": k[3]} for k in pre for l in b1_set[k]],
                 "class": "기존" if (pre and not new_file and not changed) else "새"})
summ = {"b1_tool_verdict": db.get("verdict"), "b1_files": b1_files,
        "b1_rule1": [{"file": k[0], "test": k[1], "text": k[2], "output": k[3], "lines": v} for k, v in b1_set.items()],
        "t1_rule1": rows,
        "t1_rule2_counts": {o: sum(1 for x in d["findings"] if x["rule"] == "(2)" and x["output"] == o)
                            for o in ("PASS", "UNJUDGED", "NO-SUBJECT", "FAIL")}}
open(outp, "w", encoding="utf-8").write(json.dumps(summ, ensure_ascii=False, indent=1))
for r_ in rows:
    print(r_["class"], r_["output"], r_["file"].rsplit("/", 1)[1], r_["test"], r_["t1_line"], r_["changed_line"],
          r_["b1_same_finding"], r_["text"][:110])
print(summ["t1_rule2_counts"], "b1 verdict", db.get("verdict"), "b1 rule1 n", sum(len(v) for v in b1_set.values()))
