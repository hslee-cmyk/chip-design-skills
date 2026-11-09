# 시제품 결과 요약: Temp 결과를 evidence 로 복사 + 대안별 표. 실행마다 전체 재생성.
import json, pathlib, shutil
T = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/la1a_pg_a/proto/out")
H = pathlib.Path(__file__).parent
if (T / "r5r6v2.jsonl").exists():
    shutil.copyfile(T / "r5r6v2.jsonl", H / "m4_proto_r5r6v2.jsonl")
if (T / "pg_hook.jsonl").exists():
    shutil.copyfile(T / "pg_hook.jsonl", H / "m4_proto_hook.jsonl")
if (T / "status.txt").exists():
    shutil.copyfile(T / "status.txt", H / "m4_proto_status.txt")
rows = [json.loads(l) for l in open(H / "m4_proto_r5r6v2.jsonl", encoding="utf-8")]
hook = [json.loads(l) for l in open(H / "m4_proto_hook.jsonl", encoding="utf-8")] if (H / "m4_proto_hook.jsonl").exists() else []
out = []
seen = {}
for r in rows:
    k = (r.get("circuit"), r.get("run"))
    seen.setdefault(k, {})
    seen[k].setdefault(r.get("stage"), []).append(r)
for k in sorted(seen, key=str):
    s = seen[k]
    line = "%s %s: " % k
    b = (s.get("base") or [{}])[0]
    d = (s.get("derive") or [{}])[0]
    su = (s.get("summary") or [{}])[0]
    ker = [x for x in s.get("kernel", [])]
    line += "accepted=%s base_status=%s fail=%s min0=%s viol0=%s | derive min=%s viol=%s changed=%s conflicts=%s" % (su.get("accepted_rung"), b.get("base_status"), str(b.get("base_fail"))[:90], b.get("min0"), str(b.get("viol0"))[:110], d.get("min_exact"), str(d.get("viol_exact"))[:140], str(d.get("changed_ln"))[:90], str(d.get("conflicts"))[:60])
    if s.get("error"):
        line += " ERROR " + str(s["error"][0].get("error"))[-200:]
    out.append(line)
    ks = [st for st in s if st not in ("base", "derive", "summary", "done", "gbw")]
    out.append("   stages=" + ",".join(map(str, ks)))
out.append("--- LP x")
for h in hook:
    if h.get("alt") != "A0":
        out.append("%s %s lp=%s x=%s eq=%s" % (h["circuit"], h["alt"], h["lp"], {k: float("%.3g" % v) for k, v in h["x"].items()} if isinstance(h["x"], dict) else h["x"], {k: float("%.3g" % v) for k, v in h["eq"].items()}))
txt = "\n".join(out) + "\n"
(H / "m4_proto_summary.txt").write_text(txt, encoding="utf-8")
print(txt)
