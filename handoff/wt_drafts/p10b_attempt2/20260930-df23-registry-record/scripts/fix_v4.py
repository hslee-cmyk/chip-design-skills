"""V4 basis를 `oracle 대조: `로 시작하게 재배치(로더 규칙 3: 개행 금지, 규칙 10: 그 접두를 가진 줄 = 문자열 머리)."""
import json
import sys

p = sys.argv[1]
s = open(p, "rb").read().decode("utf-8")
d = json.loads(s)
b = d["checks"]["V4"]["basis"]
sep = "UNJUDGED 판정 문장을 포함해 기대값마다 대조했다.\noracle 대조: "
assert b.count(sep) == 1
tool, oracle = b.split(sep)
new = "oracle 대조: (UNJUDGED 판정 문장 포함, 기대값마다) " + oracle + " -- 도구 실행: " + tool.rstrip()
old_json = json.dumps(b, ensure_ascii=False)
new_json = json.dumps(new, ensure_ascii=False)
assert s.count(old_json) == 1, "basis 원문을 파일에서 정확히 찾지 못함"
s = s.replace(old_json, new_json)
json.loads(s)
open(p, "wb").write(s.encode("utf-8"))
print(new[:80])
