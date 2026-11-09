"""보고서에 텍스트 파일 내용을 바이너리 append 한다(heredoc append 금지 원칙).
사용: python rep_append.py <report.md> <section file>"""
import sys

data = open(sys.argv[2], "rb").read()
if not data.endswith(b"\n"):
    data += b"\n"
with open(sys.argv[1], "ab") as fh:
    fh.write(data)
print("appended", len(data), "bytes")
