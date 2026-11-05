import collections, hashlib, json, re, sys
import xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
rows = []
for tc in root.iter("testcase"):
    f = tc.find("failure")
    if f is None:
        f = tc.find("error")
    if f is None:
        continue
    msg = f.get("message") or ""
    m = re.match(r"([\w.]+(?:Error|Exception|Failed)|AssertionError|assert\b)", msg)
    typ = m.group(1) if m else ("AssertionError" if msg.startswith("assert") else msg.split(":")[0][:40])
    tid = tc.get("classname", "").replace(".", "/") + "::" + tc.get("name", "")
    rows.append((tid, typ, msg[:160]))
print(len(rows))
print(collections.Counter(r[1] for r in rows).most_common())
sel = [r for r in rows if re.search(r"sat_threshold|dc_sat_v|vds_cost|vds_floor|headroom_lower|headroom_without|off_gate_(reads|correction|field)|tol_vdsat_max", r[0])]
print("card named", len(sel), collections.Counter(r[1] for r in sel).most_common())
json.dump({"test_ids": [r[0] for r in sel], "failure_hashes": [hashlib.sha256(("%s|%s" % (r[0], r[1])).encode("utf-8")).hexdigest() for r in sel],
           "types": {r[0]: r[1] for r in sel}, "all": rows}, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
for r in sel[:60]:
    print(r[0].split("tests/")[-1][:95], r[1], r[2][:70].replace("\n", " "))
