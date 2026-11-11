#!/usr/bin/env python
"""append_guard.py self-test -- 실제로 거부하는지(exit 2)와 허용 경로를 막지 않는지(exit 0)를 subprocess로 잰다."""
import json
import os
import subprocess
import sys

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "append_guard.py")
CWD = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
TMP = os.environ.get("TEMP", "C:/Users/HSLEE/AppData/Local/Temp").replace("\\", "/")

CASES = [
    # (이름, 도구, 명령, 기대 exit)
    ("cat>> 프로젝트", "Bash", "cat >> wt/_drafts/x.md <<'EOF'\nhi\nEOF", 2),
    ("echo>> 상대경로", "Bash", "echo hi >> notes.md", 2),
    ("echo>> 절대 msys", "Bash", "echo hi >> /c/Users/HSLEE/Documents/Todoc/fpga/wt/a.md", 2),
    ("2>> 로그 프로젝트", "Bash", "python x.py 2>> err.log", 2),
    ("heredoc > 덮어쓰기", "Bash", "cat > ../wt/_drafts/evidence/a.md <<EOF\nx\nEOF", 2),
    ("tee -a 프로젝트", "Bash", "echo hi | tee -a a.md", 2),
    ("heredoc | tee", "Bash", "cat <<EOF | tee b.md\nx\nEOF", 2),
    ("변수 대상", "Bash", 'echo hi >> "$OUT"', 2),
    ("명령 치환 대상", "Bash", "echo hi >> $(pwd)/a.md", 2),
    ("홈 경로", "Bash", "echo hi >> ~/.claude/x.md", 2),
    ("PS Add-Content", "PowerShell", "Add-Content -Path wt\\a.md -Value hi", 2),
    ("PS Out-File -Append", "PowerShell", "'x' | Out-File -FilePath C:\\Users\\HSLEE\\Documents\\Todoc\\fpga\\a.md -Append", 2),
    ("PS >>", "PowerShell", "'x' >> a.md", 2),
    ("PS ac 위치 인자", "PowerShell", "ac a.md 'x'", 2),
    ("허용: >> 임시", "Bash", "echo hi >> %s/x.log" % TMP, 0),
    ("허용: >> $TEMP", "Bash", 'echo hi >> "$TEMP/x.log"', 0),
    ("허용: >> /tmp", "Bash", "echo hi >> /tmp/x.log", 0),
    ("허용: 2>>/dev/null", "Bash", "ls 2>>/dev/null", 0),
    ("허용: 2>&1", "Bash", "ls 2>&1 | head", 0),
    ("허용: > 덮어쓰기(heredoc 없음)", "Bash", "git log > %s/l.txt" % TMP, 0),
    ("허용: python heredoc", "Bash", "C:/Python314/python.exe - <<'EOF'\nprint(1)\nEOF", 0),
    ("허용: heredoc > 임시", "Bash", "cat > %s/s.py <<'EOF'\nx\nEOF" % TMP, 0),
    ("허용: git commit heredoc", "Bash", "git -C . commit -m \"$(cat <<'EOF'\nmsg\nEOF\n)\"", 0),
    ("허용: tee 임시 -a", "Bash", "echo x | tee -a %s/t.log" % TMP, 0),
    ("허용: 비교 연산", "Bash", "[ 1 -gt 0 ] && echo ok", 0),
    ("허용: 다른 도구", "Read", "", 0),
    ("허용: 커밋 본문 'ID > 0'", "Bash", "git -C . commit -m \"$(cat <<'EOF'\nP5: ID > 0 only, a >> b\nEOF\n)\"", 0),
    ("허용: 따옴표 안 >>", "Bash", 'echo "a >> b" | grep a', 0),
    ("허용: python heredoc 본문 >>", "Bash", "C:/Python314/python.exe - <<'EOF'\nx = 1 >> 2\nEOF", 0),
    ("거부: 따옴표 대상 프로젝트", "Bash", 'echo hi >> "wt/_drafts/a b.md"', 2),
    ("거부: heredoc 본문 뒤 >>", "Bash", "cat <<EOF >> a.md\nx > y\nEOF", 2),
    ("허용: PS Out-File 덮어쓰기","PowerShell", "'x' | Out-File %s/o.txt" % TMP, 0),
]


def run(tool, cmd):
    payload = {"tool_name": tool, "tool_input": {"command": cmd}, "cwd": CWD}
    p = subprocess.run([sys.executable, HOOK], input=json.dumps(payload).encode("utf-8"), capture_output=True)
    return p.returncode, p.stderr.decode("utf-8", "replace")


def main():
    fails = 0
    for name, tool, cmd, want in CASES:
        rc, err = run(tool, cmd)
        ok = rc == want
        fails += not ok
        print("%s %-28s want=%d got=%d%s" % ("PASS" if ok else "FAIL", name, want, rc, "" if ok else " | " + err.strip()[:200]))
    rc = subprocess.run([sys.executable, HOOK], input=b"not json", capture_output=True).returncode
    fails += rc != 2
    print("%s %-28s want=2 got=%d" % ("PASS" if rc == 2 else "FAIL", "깨진 입력 fail-closed", rc))
    print("ALL PASS" if not fails else "%d FAIL" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
