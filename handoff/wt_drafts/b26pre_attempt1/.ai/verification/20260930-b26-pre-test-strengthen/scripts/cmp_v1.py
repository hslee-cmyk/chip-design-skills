"""V1 대조. argv: full_base.txt full_T.txt out.json collect_base.txt collect_T.txt
-rA 요약 줄(PASSED/FAILED/ERROR/XFAIL/XPASS/SKIPPED <나머지 전체>)을 id별로 base·T 비교(parametrize id에 공백이 있어 줄 나머지 전체를 키로).
수집 목록(--collect-only -q)도 대조한다."""
import json
import re
import sys

ANCHOR = "skills/analog-gmid-design/assets/tests/"


def norm(s):
    s = s.replace("\\", "/")
    return s[s.index(ANCHOR):] if ANCHOR in s else s


def load(p):
    d = {}
    for line in open(p, encoding="utf-8", errors="replace"):
        m = re.match(r"^(PASSED|FAILED|ERROR|XFAIL|XPASS|SKIPPED) (.+?)\s*$", line)
        if m:
            d.setdefault(norm(m.group(2)), []).append(m.group(1))
    return d


def col(p):
    out = []
    for line in open(p, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        if "::" in line and ANCHOR in line.replace("\\", "/"):
            out.append(norm(line))
    return out


b, t = load(sys.argv[1]), load(sys.argv[2])
cb, ct = col(sys.argv[4]), col(sys.argv[5])
new = sorted(set(t) - set(b))
kinds = ("PASSED", "XFAIL", "FAILED", "ERROR", "XPASS", "SKIPPED")
res = {
    "base_result_lines": sum(len(v) for v in b.values()), "T_result_lines": sum(len(v) for v in t.values()),
    "base_ids": len(b), "T_ids": len(t),
    "base_only": sorted(set(b) - set(t)),
    "changed_existing": sorted(i for i in b if i in t and b[i] != t[i]),
    "new_ids": new, "new_all_passed": all(t[i] == ["PASSED"] for i in new),
    "new_files": sorted({i.split("::")[0] for i in new}),
    "base_counts": {k: sum(v.count(k) for v in b.values()) for k in kinds},
    "T_counts": {k: sum(v.count(k) for v in t.values()) for k in kinds},
    "dup_keys": sorted(i for i, v in list(b.items()) + list(t.items()) if len(v) > 1),
    "collect_base": len(cb), "collect_T": len(ct),
    "collect_base_unique": len(set(cb)), "collect_T_unique": len(set(ct)),
    "collect_base_only": sorted(set(cb) - set(ct)), "collect_new": sorted(set(ct) - set(cb)),
}
json.dump(res, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: (v if not isinstance(v, list) or len(v) < 4 else len(v)) for k, v in res.items()}, ensure_ascii=False))
