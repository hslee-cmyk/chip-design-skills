"""base 판 merge_gate.receive 사전 판정(auditor). 스크래치 복제본(<pre>)에서 판정 기록을 audit 커밋으로 만든 뒤
receive(git_dir, old=gate master, new=그 커밋)의 실패 목록을 출력한다. 로더 규칙 1~10 결과와 V5 basis 64자리 16진도 따로 본다.
사용: PYTHONPATH=<캐시> python -P precheck_receive.py <pre 복제본> <old> <new> <id>"""
import json, re, sys
import merge_gate as mg
pre, old, new, cid = sys.argv[1:5]
fails = mg.receive(pre + "/.git", old, new)
print("receive fails", len(fails))
for f in fails:
    print(" -", f)
nv = mg.TreeView(["-C", pre], new)
rec = json.loads(nv.read(".ai/verification/%s.json" % cid).decode("utf-8"))
print("V5 hex64", re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", rec["checks"]["V5"]["basis"]))
print("FAIL checks", [k for k, c in rec["checks"].items() if c["verdict"] == "FAIL"])
