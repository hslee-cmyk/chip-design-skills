"""사본 하나에서 판정 설정 pytest를 돌려 junit + 실패 목록을 C:/g68/out/<label>.* 에 쓴다.
사용: python -B run_pt.py <사본> <label>"""
import os, subprocess, sys
import xml.etree.ElementTree as ET

root, label = sys.argv[1], sys.argv[2]
out = "C:/g68/out"
junit = "%s/%s.junit.xml" % (out, label)
env = dict(os.environ, PYTHONHASHSEED="0")
cmd = ["C:/Python314/python.exe", "-B", "-m", "pytest", "-c", root + "/tools/gates/pytest_gate.ini",
       "--rootdir=" + root, "--confcutdir=" + root, "--gmid-phase=2", "-p", "no:cacheprovider",
       "-q", "-rfE", "--junitxml=" + junit, root + "/skills/analog-gmid-design/assets/tests"]
with open("%s/%s.log" % (out, label), "w", encoding="utf-8") as fh:
    r = subprocess.run(cmd, cwd=root, env=env, stdout=fh, stderr=subprocess.STDOUT)
bad = []
for tc in ET.parse(junit).getroot().iter("testcase"):
    for k in ("failure", "error"):
        e = tc.find(k)
        if e is not None:
            bad.append("%s::%s [%s] %s" % (tc.get("classname"), tc.get("name"), k, (e.get("message") or "")[:200].replace("\n", " ")))
with open("%s/%s.fail.txt" % (out, label), "w", encoding="utf-8") as fh:
    fh.write("rc=%d\n" % r.returncode)
    fh.write("\n".join(sorted(bad)) + "\n")
print(label, "rc", r.returncode, "bad", len(bad))
