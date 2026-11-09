# swing 공칭 점: 읽기 자릿수. print 기본 자릿수와 numdgt, 파서 입력 표기를 잰다(저항 분압 하나, PDK 안 씀). 결과 m6.jsonl
import json, os, subprocess, tempfile
EXE = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "m6.jsonl")
open(OUT, "w").close()
NET = "* t\nR1 a b 1k\nR2 b 0 2.3456789k\nV1 a 0 0.9\n.control\nop\nprint v(b)\nset numdgt=%s\nprint v(b)\nquit\n.endc\n.end\n"
for nd in ("9", "15"):
    d = tempfile.mkdtemp(prefix="op75_m6_")
    open(os.path.join(d, ".spiceinit"), "w").close()
    open(os.path.join(d, "b.cir"), "w", newline="\n").write(NET % nd)
    p = subprocess.run([EXE, "-b", "b.cir"], cwd=d, capture_output=True, text=True, timeout=60)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps({"numdgt": nd, "rc": p.returncode, "lines": [l.strip() for l in p.stdout.splitlines() if l.strip().startswith("v(b)")]}) + "\n")
