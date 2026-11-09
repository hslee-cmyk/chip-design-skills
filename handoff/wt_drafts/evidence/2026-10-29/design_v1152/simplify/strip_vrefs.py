"""2차 단순화 -- 경위 괄호 정리 2단계: 검증 회차 지적 번호(검증 M-1, 재검증 R-1, 검증 2 MJ-1 등)만 지운다.
그 번호는 '어느 검증 회차가 이 문장을 낳았나'의 기록이라 규칙 뜻에 들지 않는다. 괄호 경계·구분자(, ; · --)에 붙은 꼴만 지우고 문장 속 서술은 두지 않는다.
backtick 안·끝 변경 이력 절 제외. 바뀐 줄 목록 = strip_vrefs.out.jsonl."""
import json, os, re

W = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/"
DOCS = {"40": "gain-budget-gmid-sizing.40-engine.design.md", "41": "gain-budget-gmid-sizing.41-gain-budget.design.md",
        "42": "gain-budget-gmid-sizing.42-gap-checklist.design.md"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strip_vrefs.out.jsonl")
ID = r"[A-Z]{1,3}-?\d+[a-z]?(?: \([a-z0-9]+\))?"
R = r"(?:design )?(?:재)?검증(?: \d+)? " + ID + r"(?:[·,] ?" + ID + r")*"
P1 = re.compile(r"\(" + R + r"\)")            # 괄호째
P2 = re.compile(r"\(" + R + r"(?: --|,|;) ")  # 괄호 머리
P3 = re.compile(r"(?:,|;| --) " + R + r"(?=[),;])")  # 괄호 안 구분자 뒤 꼬리


def fix(s):
    return P3.sub("", P2.sub("(", P1.sub("", s)))


def run():
    rec = []
    for k, f in DOCS.items():
        raw = open(W + f, "rb").read().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.split(nl)
        for i in range(6 if k != "42" else 0, len(lines)):
            l = lines[i]
            if l.startswith("## 변경 이력"):
                break
            parts = l.split("`")
            for p in range(0, len(parts), 2):
                parts[p] = fix(parts[p])
            new = "`".join(parts)
            if new != l:
                rec.append({"doc": k, "line": i + 1, "bytes_removed": len(l.encode()) - len(new.encode())})
                lines[i] = new
        open(W + f, "wb").write(nl.join(lines).encode("utf-8"))
    with open(OUT, "a", encoding="utf-8") as o:
        for r in rec:
            o.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("lines", len(rec), "bytes", sum(r["bytes_removed"] for r in rec))


run()
