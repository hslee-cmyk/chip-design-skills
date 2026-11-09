"""2차 단순화 -- 경위 괄호 정리 1단계: design 판 표지(v1.x[.y][ N째 커밋])만 지운다(출처 번호 DEC·O·N·U·card는 남김).
꼴: (a) 판 표지만 든 괄호 '(v1.13.0)'·'(v1.12.10 셋째 커밋)' -> 괄호째 삭제
    (b) 괄호 머리 '(v1.13.0 -- '·'(v1.13.0, '·'(v1.13.0; ' -> '('
    (c) 괄호 안 '; v1.14.1 -- '·', v1.14.1 -- ' -> '; '·', '
판 표지는 그 문장이 언제 바뀌었는지의 기록이라 규칙·정의·인터페이스 뜻에 들지 않는다(원문 = git 이전 판, 바뀐 줄 목록 = strip_vtags.out.jsonl)."""
import json, os, re

W = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/"
DOCS = {"40": "gain-budget-gmid-sizing.40-engine.design.md", "41": "gain-budget-gmid-sizing.41-gain-budget.design.md",
        "42": "gain-budget-gmid-sizing.42-gap-checklist.design.md"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strip_vtags.out.jsonl")
V = r"v1\.\d+(?:\.\d+)?(?: (?:첫|둘째|셋째|넷째|다섯째|여섯째|일곱째|여덟째|아홉째|열째)(?: 커밋)?)?"
PA = re.compile(r" ?\(" + V + r"\)")
PB = re.compile(r"\(" + V + r"(?: --|,|;) ")
PC = re.compile(r"([;,]) " + V + r" -- ")


def run():
    rec = []
    for k, f in DOCS.items():
        raw = open(W + f, "rb").read().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.split(nl)
        start = 6 if k != "42" else 0  # 머리(front matter·제목) 이후만
        for i in range(start, len(lines)):
            l = lines[i]
            if l.startswith("## 변경 이력"):
                break
            if "`" in l:
                # backtick 안은 건드리지 않음: backtick 조각을 가리고 처리
                parts = l.split("`")
                for p in range(0, len(parts), 2):
                    parts[p] = PC.sub(r"\1 ", PB.sub("(", PA.sub("", parts[p])))
                new = "`".join(parts)
            else:
                new = PC.sub(r"\1 ", PB.sub("(", PA.sub("", l)))
            if new != l:
                rec.append({"doc": k, "line": i + 1, "bytes_removed": len(l.encode()) - len(new.encode())})
                lines[i] = new
        open(W + f, "wb").write(nl.join(lines).encode("utf-8"))
    with open(OUT, "a", encoding="utf-8") as o:
        for r in rec:
            o.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("lines", len(rec), "bytes", sum(r["bytes_removed"] for r in rec))


run()
