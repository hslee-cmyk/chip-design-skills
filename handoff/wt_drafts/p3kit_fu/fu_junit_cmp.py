"""FU spec card '작성 전 실측' -- PT3 junit 두 개의 test id별 결과(passed/failed/error/skipped/xfailed) 대조.
사용: python -B fu_junit_cmp.py <base.junit.xml> <head.junit.xml>  -> stdout 한 줄 JSON(수·차이 목록)"""
import json
import sys
import xml.etree.ElementTree as ET


def outcomes(p):
    res = {}
    for tc in ET.parse(p).getroot().iter("testcase"):
        tid = "%s::%s" % (tc.get("classname"), tc.get("name"))
        kind = "passed"
        for ch in tc:
            if ch.tag in ("failure", "error"):
                kind = ch.tag
            elif ch.tag == "skipped":
                kind = "xfailed" if (ch.get("type") == "pytest.xfail") else "skipped"
        res[tid] = kind
    return res


b, h = outcomes(sys.argv[1]), outcomes(sys.argv[2])
cnt = lambda d: {k: sum(1 for v in d.values() if v == k) for k in sorted(set(d.values()))}
diff = sorted(t for t in set(b) | set(h) if b.get(t) != h.get(t))
print(json.dumps({"ids_base": len(b), "ids_head": len(h), "base": cnt(b), "head": cnt(h), "diff": diff[:50], "n_diff": len(diff)},
                 ensure_ascii=False))
