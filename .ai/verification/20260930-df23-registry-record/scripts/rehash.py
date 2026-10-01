import hashlib, json, sys
ok = 0; n = 0
for ln in open(sys.argv[1], encoding="utf-8"):
    r = json.loads(ln); n += 1
    h = hashlib.sha256((r["test_id"] + "\n" + r["exc_type"]).encode("utf-8")).hexdigest()
    ok += h == r["failure_hash"]
print(n, ok)
