#!/usr/bin/env python
"""TEMPLATE.md 를 원칙 26(CLAUDE.md)에서 파싱한 규칙으로 생성한다. 원칙 26 이 바뀌면 다시 실행한다.
사용: python ask_gate_template.py [출력경로]   (기본: ask_gate_rules 의 게이트 폴더/TEMPLATE.md)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ask_gate_rules as AR  # noqa: E402

DEF_OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "wt", "_drafts", "ask_gates", "TEMPLATE.md").replace("\\", "/")


def render(R):
    pre = " / ".join("'%s'" % p for p in R["prefixes"])
    out = ["---", "kind: recommend", "headers: 질문헤더1, 질문헤더2",
           "candidate_doc: C:/절대/경로/후보문서.md", "candidate_sha256: <후보 문서 bytes 의 sha256>",
           "validation: C:/절대/경로/검증기록.md", "reason:", "---",
           "# 점검 파일 (AskUserQuestion 게이트) -- 이 파일은 ask_gate_template.py 가 원칙 26 에서 생성함. 손으로 고치지 말 것",
           "",
           "kind: recommend|approval = 권고/승인 질문, clarify = 권고 없는 명확화 질문(reason 필수, option label 에 '(Recommended)' 금지).",
           "headers 는 질문 header 집합과 정확히 같아야 한다(쉼표 목록). 이 파일을 복사해 새 이름으로 점검 파일을 만든다.",
           "표 각 행의 마지막 칸(근거 칸)은 %s 중 하나로 시작한다. 금지 표현: %s." % (
               pre, ", ".join("'%s'" % w for w in R["forbidden"])),
           ""]
    for s in R["sections"]:
        out += ["## " + s, "(작성)", ""]
    out += ["## %s: 질문헤더1" % R["table_label"], "| # | 항목 | 내용 | 근거 칸 |", "|---|------|------|---------|"]
    for n, name in R["rows"]:
        out.append("| %s | %s | ... | %s...) |" % (n, name.replace("|", "/"), R["prefixes"][0]))
    out += ["",
            "(header 마다 `## %s: <header>` 절을 하나씩 둔다. 근거 칸의 경로 토큰은 존재해야 한다.)" % R["table_label"],
            "",
            "## validation 파일 형식 (검증자가 쓴다, 작성자가 쓰지 않는다)",
            "검증자는 이 점검 파일 bytes 전체의 sha256 을 구해 validation 파일에 아래 두 줄을 쓴다.",
            "점검 파일이 검증 뒤 한 글자라도 바뀌면 거부된다.", "",
            "    verdict: Major 0", "    gate_sha256: <점검 파일 bytes 전체의 sha256 hex>", ""]
    return "\n".join(out)


def main():
    R = AR.load_rules()
    path = sys.argv[1] if len(sys.argv) > 1 else DEF_OUT
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(render(R).encode("utf-8"))
    print("생성: %s (절 %d, 행 %s)" % (path, len(R["sections"]) + 1, "".join(n for n, _ in R["rows"])))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
