"""IT-2b red 분류(감사). base(r) junit xml 들에서 실패마다 (test id, 예외 타입, 메시지 첫 줄, 마지막 traceback 줄)을 뽑고 분류한다.
분류: absent = 새 이름 부재(ImportError·AttributeError·KeyError on 새 필드 등 -- 메시지로 판단), typeerror = 새 서명 직접 호출 TypeError(red 로 세지 않음),
behavior = AssertionError·Failed(행동 red), other = 그 밖(하네스 오류 의심).
usage: python -I classify_red.py <xml dir> <out json>
"""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PFX = "skills/analog-gmid-design/"


def main():
    rows = []
    for xml in sorted(Path(sys.argv[1]).glob("*.xml")):
        for tc in ET.parse(xml).iter("testcase"):
            f = tc.find("failure")
            if f is None:
                f = tc.find("error")
                if f is None:
                    continue
            nid = tc.get("classname").replace(".", "/") + ".py::" + tc.get("name")
            msg = (f.get("message") or "").strip()
            text = f.text or ""
            last = [ln for ln in text.splitlines() if ln.startswith("E ")]
            first = msg.splitlines()[0] if msg else ""
            typ = first.split(":")[0] if ":" in first else first[:40]
            if first.startswith("assert") or typ == "AssertionError":
                typ = "AssertionError"
            if typ == "TypeError":
                cls = "typeerror_excluded"
            elif typ in ("AttributeError", "ImportError", "ModuleNotFoundError", "KeyError"):
                cls = "absent_name"
            elif typ in ("AssertionError", "Failed"):
                cls = "behavior"
            else:
                cls = "other"
            tid = PFX + nid
            rows.append({"test_id": tid, "type": typ, "class": cls, "message": first[:300],
                         "E_lines": [ln[:300] for ln in last[:6]],
                         "hash": hashlib.sha256((tid + "\n" + "builtins." + typ).encode("utf-8")).hexdigest()})
    Path(sys.argv[2]).write_bytes(json.dumps(rows, ensure_ascii=False, indent=1).encode("utf-8"))
    from collections import Counter
    print(Counter(r["class"] for r in rows), Counter(r["type"] for r in rows))
    for r in rows:
        print(r["class"], r["type"], r["test_id"].split("::")[-1], "|", r["message"][:160])


if __name__ == "__main__":
    main()
