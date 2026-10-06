"""1차 auditor 스크립트(방법 참고)를 2차 경로·커밋으로 바꿔 C:/g372/scripts/에 복사한다."""
import os
SRC = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26pre_attempt1/.ai/verification/20260930-b26-pre-test-strengthen/scripts"
DST = "C:/g372/scripts"
REPL = [("C:/g342", "C:/g372"), ("C:/g341", "C:/g371"),
        ("6c724debd884dd1d31034f5279ae450f35e67fc4", "ae1b5886e6fd4b5b18d6096d8ac6076259719ff3"),
        ("d2b2ed71ce506b010e5d87c03add007069a5a322", "e4d5833f89a9a96db7410ce4bfc53703f4f9ef3f")]
for f in ("v1.sh", "cmp_v1.py", "strict_check.py", "vtools.sh", "v2_alt_engines.sh", "ids_main20.py",
          "kill_summary.py", "kill_b26pre.py", "v4_oracle.py", "c8_static.py", "tie_probe.py"):
    s = open(os.path.join(SRC, f), "rb").read().decode("utf-8")
    for a, b in REPL:
        s = s.replace(a, b)
    open(os.path.join(DST, f), "wb").write(s.encode("utf-8"))
    for bad in ("6c724de", "d2b2ed7", "g342", "g341"):
        if bad in s:
            print("STALE", f, bad)
print("done")
