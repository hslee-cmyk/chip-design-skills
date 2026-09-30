"""레지스트리 §1 집계 표(R0·R1·R2·D·DUP) vs §3~§7 소절 제목 괄호 수·실제 표 행 수. 사용: sec_counts.py <레지스트리> <out.json>
§ 번호 -> 등급: 3 R0, 4 R1, 5 R2, 6 DUP, 7 D. 행 = '|'로 시작하고 구분선이 아닌 줄에서 머리 줄 제외."""
import json, re, sys
lines = open(sys.argv[1], encoding="utf-8").read().split("\n")
grade = {"3": "R0", "4": "R1", "5": "R2", "6": "DUP", "7": "D"}
res, cur_g, cur = {}, None, None
sec1 = {}
in1 = False
for i, l in enumerate(lines):
    m = re.match(r"^## (\d+)\.", l)
    if m:
        in1 = m.group(1) == "1"
        cur_g = grade.get(m.group(1)); cur = None
        continue
    if in1 and l.startswith("|") and not re.match(r"^\|\s*-", l):
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if c[0] == "파일":
            hdr = c
        else:
            sec1[c[0]] = {h: c[k] for k, h in enumerate(hdr) if h in ("R0", "R1", "R2", "D", "DUP")}
    m = re.match(r"^### (.+?) \((\d+)\)\s*$", l)
    if m and cur_g:
        cur = {"grade": cur_g, "file": m.group(1), "heading": int(m.group(2)), "rows": 0, "hdr_seen": False, "line": i + 1}
        res[f"{cur_g}/{m.group(1)}"] = cur
        continue
    if cur and l.startswith("|"):
        if re.match(r"^\|\s*-", l):
            continue
        if not cur["hdr_seen"]:
            cur["hdr_seen"] = True
            continue
        cur["rows"] += 1
out = {"sec1": sec1, "subsections": {k: {kk: v[kk] for kk in ("heading", "rows", "line")} for k, v in res.items()}}
mism = []
for k, v in res.items():
    g, f = k.split("/", 1)
    s1 = sec1.get(f, {}).get(g)
    if not (str(v["heading"]) == str(v["rows"]) == str(s1)):
        mism.append({"key": k, "sec1": s1, "heading": v["heading"], "rows": v["rows"]})
out["mismatch"] = mism
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False))
