"""IT-2a 판정 기록 작성(감사). red = 허용 예외 타입(AssertionError·Failed·신규 심볼 AttributeError)인 base 실패만(00-common §8.1).
usage: python -I write_record.py <red_base.xml> <record 본문 json(red 없음)> <out_json>
"""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

PFX = "skills/analog-gmid-design/"
EXCLUDE = {"gmid_engine/tests/sizing/test_seal.py::test_it2a_seal_dc_base_keyword_required"}   # T-L11e: card 가 red 계수에서 뺀다


def red_from(xml):
    ids, hashes, skipped = [], [], []
    for tc in ET.parse(xml).iter("testcase"):
        f = tc.find("failure")
        if f is None:
            continue
        nid = tc.get("classname").replace(".", "/") + ".py::" + tc.get("name")
        msg = f.get("message") or ""
        if nid in EXCLUDE:
            skipped.append((nid, "T-L11e"))
            continue
        if msg.startswith("AttributeError: derive_child"):
            typ = "builtins.AttributeError"
        elif msg.startswith("Failed: DID NOT RAISE"):
            typ = "builtins.Failed"
        elif msg.startswith("AssertionError") or msg.startswith("assert "):
            typ = "builtins.AssertionError"
        else:
            skipped.append((nid, msg.split(":")[0]))
            continue
        tid = PFX + nid
        ids.append(tid)
        hashes.append(hashlib.sha256((tid + "\n" + typ).encode("utf-8")).hexdigest())
    return ids, hashes, skipped


def main():
    ids, hashes, skipped = red_from(sys.argv[1])
    rec = json.loads(open(sys.argv[2], encoding="utf-8").read())
    rec["red"] = {"test_ids": ids, "failure_hashes": hashes}
    with open(sys.argv[3], "wb") as f:
        f.write(json.dumps(rec, ensure_ascii=False, indent=1).encode("utf-8"))
    print(len(ids), "red;", len(skipped), "excluded:", sorted({s[1] for s in skipped}))


if __name__ == "__main__":
    main()
