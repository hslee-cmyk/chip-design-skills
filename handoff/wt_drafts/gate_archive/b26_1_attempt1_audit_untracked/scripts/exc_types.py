# pytest 긴 traceback 출력에서 실패·오류 test마다 마지막 위치 줄 `<파일>:<줄>: <예외 타입>`과 마지막 `E ` 줄을 뽑는다.
import re, sys, json
src, outp = sys.argv[1:3]
text = open(src, encoding="utf-8", errors="replace").read().splitlines()
HDR = re.compile(r"^_{3,} (?:ERROR at (setup|teardown) of )?(.+?) _{3,}$")
LOC = re.compile(r"^(\S.*?):(\d+): (\S+)$")
res = {}
cur = None
for line in text:
    m = HDR.match(line)
    if m:
        cur = (m.group(2), m.group(1) or "call")
        res[cur] = {"loc": None, "E": []}
        continue
    if line.startswith("=") or line.startswith("FAILED ") or line.startswith("PASSED "):
        cur = None if line.startswith("=") else cur
    if cur is None:
        continue
    lm = LOC.match(line)
    if lm:
        res[cur]["loc"] = {"file": lm.group(1), "line": int(lm.group(2)), "type": lm.group(3)}
    if line.startswith("E "):
        res[cur]["E"].append(line[1:].strip())
out = []
for (name, phase), v in res.items():
    last_e = [e for e in v["E"] if re.match(r"^[A-Za-z_][\w\.]*(Error|Exception|Failed|Exit|Interrupt)?\b", e)]
    out.append({"test": name, "phase": phase, "type": v["loc"]["type"] if v["loc"] else None,
                "loc": "%s:%s" % (v["loc"]["file"], v["loc"]["line"]) if v["loc"] else None,
                "first_E": v["E"][0][:240] if v["E"] else None, "last_E": v["E"][-1][:240] if v["E"] else None})
json.dump(out, open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out))
