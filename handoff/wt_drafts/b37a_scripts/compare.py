"""measure.py 두 출력(base/head)을 비교해 E-LIB·E3·offset·audit·SPECS 차이표를 쓴다.
사용: python -B compare.py <base.json> <head.json> <out.txt>"""
import json, sys

b = json.load(open(sys.argv[1], encoding="utf-8"))
h = json.load(open(sys.argv[2], encoding="utf-8"))
fh = open(sys.argv[3], "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    fh.write(s + "\n")


for c in sorted(b["circuits"]):
    B, H = b["circuits"][c], h["circuits"][c]
    log("==", c)
    log("  transistors same:", B["transistors"] == H["transistors"])
    mk = sorted(k for k in set(B["meta"]) | set(H["meta"]) if B["meta"].get(k) != H["meta"].get(k))
    log("  meta diff keys:", mk)
    for k in mk:
        bv, hv = B["meta"].get(k), H["meta"].get(k)
        if isinstance(bv, dict) or isinstance(hv, dict):
            bv, hv = bv or {}, hv or {}
            for dev in sorted(set(bv) | set(hv)):
                if bv.get(dev) != hv.get(dev):
                    bd, hd = bv.get(dev) or {}, hv.get(dev) or {}
                    if isinstance(bd, dict) and isinstance(hd, dict):
                        f = {x: (bd.get(x), hd.get(x)) for x in sorted(set(bd) | set(hd)) if bd.get(x) != hd.get(x)}
                    else:
                        f = (bd, hd)
                    log("    %s.%s: %s" % (k, dev, f))
        elif isinstance(bv, list) or isinstance(hv, list):
            bl, hl = bv or [], hv or []
            log("    %s: len %d -> %d" % (k, len(bl), len(hl)))
            for x in bl:
                if x not in hl:
                    log("      - removed:", json.dumps(x, ensure_ascii=False)[:300])
            for x in hl:
                if x not in bl:
                    log("      + added:", json.dumps(x, ensure_ascii=False)[:300])
        else:
            log("    %s: %r -> %r" % (k, bv, hv))
    log("  ports(head):", H.get("ports"))
    e3b, e3h = B["e3"], H["e3"]
    log("  E3 declared_vsid=%s same=%s" % (e3b.get("declared_vsid"), e3b == e3h))
    if e3b != e3h:
        gb = [g for g in e3b.get("groups", []) if len(g) > 1]
        gh = [g for g in e3h.get("groups", []) if len(g) > 1]
        log("    base multi-groups:", gb)
        log("    head multi-groups:", gh)
    log("  offset same:", B["offset_pairs"] == H["offset_pairs"], H["offset_pairs"])
    log("  audit same:", B["audit"] == H["audit"], (H["audit"][:80] if isinstance(H["audit"], str) else "result"))
if "specs" in b:
    log("== SPECS")
    for k in b["specs"]:
        sb, sh = b["specs"][k], h["specs"][k]
        same = {x: sb.get(x) == sh.get(x) for x in ("metrics", "sized_hash", "error")}
        log("  %s same=%s sec %s/%s n_metrics=%s err=%s" % (k, same, sb["sec"], sh["sec"], len(sb.get("metrics") or {}), (sb.get("error") or "")[:80]))
fh.close()
