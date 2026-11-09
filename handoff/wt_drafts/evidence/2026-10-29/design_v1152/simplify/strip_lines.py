"""2차 단순화 -- as-built 줄 번호 인용 정리(O-153·O-165: 엔진 인용은 외부 사실·재작성 범위만).
`<경로>.py:<줄>` 꼴(backtick 안)에서 ':<줄>'만 지운다(파일 경로는 남김). 재작성 범위 문맥(줄에 아래 낱말이 있으면)은 건드리지 않는다.
바뀐 줄마다 (문서, 줄 번호, 지운 인용 원문)을 strip_lines.out.jsonl에 남긴다(원문 보존 -- git 이전 판과 함께)."""
import json, os, re, sys

W = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/"
DOCS = {"40": "gain-budget-gmid-sizing.40-engine.design.md", "41": "gain-budget-gmid-sizing.41-gain-budget.design.md"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strip_lines.out.jsonl")
KEEP = ("재작성", "삭제", "지운다", "지우고", "바꾼다", "바꿀", "고친다", "고칠", "옮긴다", "옮기", "변경 목록", "수정", "범위(", "재측정", "대조", "정정")
PAT = re.compile(r"`((?:E/|O/|tools/|skills/|docs/)?[A-Za-z0-9_./\-]+\.(?:py|md|json|toml)):([0-9][0-9,·\-–]*)`")


def run():
    rec = []
    for k, f in DOCS.items():
        raw = open(W + f, "rb").read().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.split(nl)
        for i, l in enumerate(lines):
            if any(w in l for w in KEEP):
                continue
            hits = PAT.findall(l)
            if not hits:
                continue
            new = PAT.sub(lambda m: "`" + m.group(1) + "`", l)
            rec.append({"doc": k, "line": i + 1, "removed": ["%s:%s" % h for h in hits]})
            lines[i] = new
        open(W + f, "wb").write(nl.join(lines).encode("utf-8"))
    with open(OUT, "a", encoding="utf-8") as o:
        for r in rec:
            o.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("lines changed", len(rec), "citations", sum(len(r["removed"]) for r in rec))


run()
