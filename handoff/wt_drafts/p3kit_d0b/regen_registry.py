"""D0b 작성 전 실측(측정 전용, 역할 산출물 아님): `plan` 출력으로 레지스트리 '이관 목적지' 열을 다시 쓰는 모의.

    python -B regen_registry.py <레지스트리 md(복제본 안)> <plan.json> <요약 out.json> [--write]

행 분류(D0a 계약 2 A-4의 짝짓기 규칙 그대로 -- 함수 칸 첫 백틱 토큰의 '.' 앞 = 단위 키, 파일은 보지 않는다):
  one      -- 그 키의 배정 단위가 있고 배정 MOD가 하나
  multi    -- 같은 키의 배정 단위가 둘 이상이고 MOD가 갈림(파일이 다른 같은 이름)
  nested   -- 함수 칸이 `  └ ` 중첩 표기(단위가 아니다)
  nounit   -- 키에 맞는 배정 단위가 없음(분할 대상·N3.10 파일 밖 함수, 미배정 단위, 지워진 함수)
--write면 one 행의 목적지 셀을 배정 MOD 줄기로, 표마다 '근거 규칙' 열을 목적지 열 바로 뒤에 더해 그 행의 rule을 쓴다(다른 분류 행은 셀 그대로, 근거 칸 '-').
"""
import json
import re
import sys

REG, PLAN, OUT = sys.argv[1:4]
WRITE = "--write" in sys.argv[4:]
plan = json.load(open(PLAN, encoding="utf-8"))
by_key = {}
for uid, v in plan["assignment"].items():
    by_key.setdefault(uid.split("::", 1)[1], []).append((uid, v["mod"], v["rule"]))

raw = open(REG, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in raw else "\n"
lines = raw.split(nl)


def split_cells(line):
    s = line.strip()[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    out, cur, i = [], "", 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur += "\\|"
            i += 2
            continue
        if s[i] == "|":
            out.append(cur.strip())
            cur = ""
        else:
            cur += s[i]
        i += 1
    out.append(cur.strip())
    return out


def join(cells):
    return "| " + " | ".join(cells) + " |"


cls = {"one": [], "multi": [], "nested": [], "nounit": []}
tables = 0
i = 0
while i < len(lines):
    if lines[i].startswith("|") and i + 1 < len(lines) and re.match(r"^\|\s*:?-{3,}", lines[i + 1]):
        hdr = split_cells(lines[i])
        if "함수" in hdr and "이관 목적지" in hdr:
            tables += 1
            cf, cd = hdr.index("함수"), hdr.index("이관 목적지")
            if WRITE:
                lines[i] = join(hdr[:cd + 1] + ["근거 규칙"] + hdr[cd + 1:])
                sep = split_cells(lines[i + 1])
                lines[i + 1] = join(sep[:cd + 1] + ["---"] + sep[cd + 1:])
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                c = split_cells(lines[j])
                fcell = c[cf] if cf < len(c) else ""
                toks = re.findall(r"`([^`]*)`", fcell)
                tok = toks[0] if toks else ""
                rule = "-"
                if tok.lstrip().startswith("└") or tok.startswith(" "):
                    k = "nested"
                else:
                    key = tok.strip().split(".")[0]
                    us = by_key.get(key, [])
                    mods = sorted({m for _, m, _ in us})
                    if not us:
                        k = "nounit"
                    elif len(mods) == 1:
                        k = "one"
                        if WRITE and cd < len(c):
                            c[cd] = mods[0][:-3]
                        rule = ",".join(sorted({r for _, _, r in us}))
                    else:
                        k = "multi"
                cls[k].append({"line": j + 1, "func": tok, "units": [u for u, _, _ in by_key.get(tok.strip().split(".")[0], [])]})
                if WRITE:
                    while len(c) <= cd:
                        c.append("")
                    lines[j] = join(c[:cd + 1] + [rule] + c[cd + 1:])
                j += 1
            i = j
            continue
    i += 1
if WRITE:
    open(REG, "w", encoding="utf-8", newline="").write(nl.join(lines))
summary = {"tables": tables, "counts": {k: len(v) for k, v in cls.items()}, "rows": cls}
json.dump(summary, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({"tables": tables, "counts": summary["counts"], "write": WRITE}, ensure_ascii=False))
