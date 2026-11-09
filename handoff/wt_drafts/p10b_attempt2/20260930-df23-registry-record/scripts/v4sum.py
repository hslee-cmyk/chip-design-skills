"""test_lint JSON 출력 요약: (rule, output) 개수, PASS/UNJUDGED/NO-SUBJECT 밖 발견 전부."""
import collections
import json
import sys

txt = open(sys.argv[1], encoding="utf-8").read()
lines = [ln for ln in txt.splitlines() if ln.strip().startswith("{")]
if not lines:
    print(sys.argv[1], "NO JSON")
    print(txt[-3000:])
    sys.exit(0)
d = json.loads(lines[-1])
print(sys.argv[1], d.get("verdict"), d.get("files"))
print(sorted(collections.Counter((x.get("rule"), x.get("output")) for x in d.get("findings", [])).items()))
for x in d.get("findings", []):
    if x.get("output") not in ("PASS", "UNJUDGED", "NO-SUBJECT"):
        print(x)
print({k: v for k, v in d.items() if k != "findings"})
