import collections, json
rows = [json.loads(l) for l in open("C:/Users/HSLEE/AppData/Local/Temp/la1s_op23_audit/out/a3_7.jsonl", encoding="utf-8")]
c = collections.Counter((r.get("code"), r.get("stage"), r.get("lut")) for r in rows)
for k, v in c.most_common():
    print(k, v)
for r in rows:
    if r.get("lut") in ("committed_other_folder",) or str(r.get("code")).startswith(("STOP", "EXC", "NOT")):
        print(r["input"][:60], r.get("code"), r.get("stage"), str(r.get("detail") or r.get("msg"))[:140])
