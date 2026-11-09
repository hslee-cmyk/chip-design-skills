"""판정 기록 JSON 문자열 안의 날 개행(제어 문자)을 찾아 `\\n` 이스케이프로 바꾼다(문자열 밖 개행은 그대로)."""
import json
import sys

p = sys.argv[1]
s = open(p, "rb").read().decode("utf-8")
out, in_str, esc, fixed = [], False, False, 0
for ch in s:
    if in_str:
        if esc:
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == '"':
            in_str = False
        elif ch == "\n":
            out.append("\\n")
            fixed += 1
            continue
    elif ch == '"':
        in_str = True
    out.append(ch)
t = "".join(out)
d = json.loads(t)
open(p, "wb").write(t.encode("utf-8"))
b = d["checks"]["V4"]["basis"]
print("fixed", fixed, "oracle lines", sum(1 for l in b.split("\n") if l.startswith("oracle 대조: ")))
