"""계약 2 대조: base·병합본 출력에서 interdig_ok를 뺀 모든 필드가 같은지, 다른 것이 interdig_ok뿐인지.
usage: python c2cmp.py <base_s0> <M_s0> <base_s1> <M_s1>"""
import json, sys

b0, m0, b1, m1 = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:5])


def strip(c):
    c = json.loads(json.dumps(c))
    for e in c["relaxed_pairs"]:
        e.pop("interdig_ok")
        e.pop("consistent")
    return c


for tag, B, M in (("seed0", b0, m0), ("seed1", b1, m1)):
    same_other = 0
    diffs = []
    for cb, cm in zip(B["cases"], M["cases"]):
        assert cb["label"] == cm["label"]
        if strip(cb) == strip(cm):
            same_other += 1
        else:
            diffs.append(("OTHER-FIELD-DIFF", cb["label"]))
        for eb, em in zip(cb["relaxed_pairs"], cm["relaxed_pairs"]):
            if eb["interdig_ok"] is not em["interdig_ok"]:
                diffs.append(("interdig_ok", cb["label"], eb["pair"], eb["interdig_ok"], em["interdig_ok"],
                              "base consistent", eb["consistent"], "M consistent", em["consistent"]))
    n_rp = sum(len(c["relaxed_pairs"]) for c in M["cases"])
    incons_b = sum(1 for c in B["cases"] for e in c["relaxed_pairs"] if not e["consistent"])
    incons_m = sum(1 for c in M["cases"] for e in c["relaxed_pairs"] if not e["consistent"])
    print(tag, "cases", len(B["cases"]), "same_except_interdig_ok", same_other,
          "relaxed_entries", n_rp, "inconsistent base", incons_b, "inconsistent M", incons_m)
    for d in diffs:
        print("  ", d)
print("seed0==seed1 base", b0["cases"] == b1["cases"], "M", m0["cases"] == m1["cases"])
