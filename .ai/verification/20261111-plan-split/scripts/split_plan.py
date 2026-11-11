"""계획서 기계적 분할기 -- 내용을 바꾸지 않고 파일만 나눈다.

split:   plan.md -> 줄이 짧아진 plan.md + <stem>.parts/ 아래 조각 파일
rebuild: 줄이 짧아진 plan.md + parts -> 원래 plan.md (바이트 단위로 같아야 한다)
check:   rebuild 결과가 원본과 같은지, 조각 표지·파일이 짝이 맞는지

분할 대상(사용자 승인 O-275 범위):
  1. N6 card 절(### N6.n card <ID> ...)        -> parts/cards/<ID>.md     (본문), plan에는 제목 + 표지 + 링크
  2. 제목이 '-- **철회**'·'-- **삭제**'인 card와 N3.12 폐기 절 -> parts/archive/
  3. N2.1 결정 레지스터의 긴 표 행(DEC-n, O-n)   -> parts/decisions/<ID>.md (원래 한 줄 그대로), plan에는 요약 한 줄
  4. Status 줄                                  -> parts/status/<stem>-status.md
절 번호·card ID·DEC 번호는 plan에 그대로 남는다.
"""
import re
import sys
from pathlib import Path

HEAD = re.compile(r"^(#{2,3}) (.*)$")
CARD = re.compile(r"^N6\.(\d+) card ([A-Z][A-Za-z0-9]*-[0-9A-Za-z]+)")
DEAD = re.compile(r"^N6\.\d+ card \S+ -- \*\*(철회|삭제)\*\*")
ROW = re.compile(r"^\| ([A-Z]+-\d+[a-z]?) \| ")
SEC_MARK = re.compile(r"^<!-- split:section=(\S+) -->$")
ROW_MARK = re.compile(r"<!-- split:row=(\S+) -->")
ROW_BYTES = 3000          # 이 크기를 넘는 표 행만 따로 둔다


def read(path):
    return Path(path).read_bytes().decode("utf-8")


def sections(lines):
    """## / ### 제목의 (시작, 끝, 수준, 제목). 코드 펜스 안은 제목이 아니다."""
    heads, fence = [], False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            fence = not fence
        m = None if fence else HEAD.match(line)
        if m:
            heads.append([i, None, len(m.group(1)), m.group(2)])
    for k, h in enumerate(heads):
        h[1] = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
    return heads


def clip(s, n):
    s = s.strip().replace("|", "/").replace("<!--", "").replace("-->", "").replace("**", "")
    if len(s) <= n:
        return s
    cut = s[:n]
    return cut[:cut.rfind(" ")] + " ..." if " " in cut[n // 2:] else cut + "..."


def summary(text):
    """결정 칸의 제목 요약: 굵은 첫 구절이 제목 꼴(15자 이상, 날짜로 시작하지 않음)이면 그것을, 아니면 앞 90자."""
    m = re.search(r"\*\*(.+?)\*\*", text)
    if m and len(m.group(1)) >= 15 and not re.match(r"\d{4}-\d\d", m.group(1)):
        return clip(m.group(1), 110)
    return clip(text, 90)


def split(plan_text, stem):
    lines = plan_text.split("\n")
    parts = {}                      # 상대 경로 -> 텍스트
    out = []
    base = "%s.parts" % stem
    heads = sections(lines)
    by_start = {h[0]: h for h in heads}
    i = 0
    in_n21 = False
    status_done = False
    ids = {}
    while i < len(lines):
        line = lines[i]
        h = by_start.get(i)
        if h:
            title = h[3]
            in_n21 = title.startswith("N2.1 ")
            kind = None
            if h[2] == 3 and DEAD.match(title):
                kind, name = "archive", CARD.match(title).group(2)
            elif h[2] == 3 and title.startswith("N3.12 ") and "폐기" in title:
                kind, name = "archive", "N3.12"
            elif h[2] == 3 and CARD.match(title):
                kind, name = "cards", CARD.match(title).group(2)
            if kind:
                rel = "%s/%s.md" % (kind, name)
                assert rel not in parts, "파일 이름 중복: " + rel
                parts[rel] = "".join(l + "\n" for l in lines[h[0]:h[1]])
                path = "%s/%s" % (base, rel)
                out += [line, "<!-- split:section=%s -->" % path, "→ 본문: [%s](%s)" % (rel, path), ""]
                i = h[1]
                continue
        if in_n21:
            m = ROW.match(line)
            if m and len(line.encode("utf-8")) > ROW_BYTES and m.group(1) not in ids:
                rid = m.group(1)
                ids[rid] = 1
                body = line.rstrip()
                head2, apply_, state = body[:-2].rsplit(" | ", 2) if body.endswith(" |") else (None, None, None)
                if head2 is not None:
                    decision = head2[len(m.group(0)):]
                    rel = "decisions/%s.md" % rid
                    parts[rel] = line + "\n"
                    path = "%s/%s" % (base, rel)
                    out.append("| %s | **%s** → [%s](%s) <!-- split:row=%s --> | %s | %s |" % (rid, summary(decision), rid, path, path, clip(apply_, 60), clip(state, 80)))
                    i += 1
                    continue
        if not status_done and line.startswith("> **Status**:"):
            status_done = True
            ver = re.search(r"^version: (\S+)", "\n".join(lines[:5]), re.M)
            rel = "status/%s-status.md" % stem
            parts[rel] = line + "\n"
            path = "%s/%s" % (base, rel)
            out.append("> **Status**: Plan v%s -- 상세 [%s](%s) <!-- split:row=%s -->" % (ver.group(1) if ver else "?", rel, path, path))
            i += 1
            continue
        out.append(line)
        i += 1
    return "\n".join(out), parts


def rebuild(stub_text, read_part):
    lines = stub_text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = SEC_MARK.match(line)
        if m:
            out.pop()                                   # 제목 줄(조각 파일 첫 줄이 같은 제목이다)
            out += read_part(m.group(1)).split("\n")[:-1]
            i += 3                                      # 표지, 링크, 빈 줄
            continue
        m = ROW_MARK.search(line)
        if m:
            out += read_part(m.group(1)).split("\n")[:-1]
            i += 1
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def main(argv):
    mode, plan = argv[0], Path(argv[1])
    stem = plan.name[:-len(".plan.md")]
    base = plan.parent / ("%s.parts" % stem)
    if mode == "split":
        text = read(plan)
        stub, parts = split(text, stem)
        # 사전 확인: 되돌려서 같은지
        back = rebuild(stub, lambda p: parts[p[len(base.name) + 1:]])
        assert back == text, "분할 -> 복원이 원본과 다르다"
        for rel, body in parts.items():
            f = base / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(body.encode("utf-8"))
        plan.write_bytes(stub.encode("utf-8"))
        print("분할 완료: 조각 %d개, plan %d -> %d 바이트" % (len(parts), len(text.encode("utf-8")), len(stub.encode("utf-8"))))
    elif mode == "rebuild":
        out = rebuild(read(plan), lambda p: read(plan.parent / p))
        Path(argv[2]).write_bytes(out.encode("utf-8"))
        print("복원 완료 ->", argv[2])
    else:
        raise SystemExit("usage: split|rebuild <plan.md> [out]")


if __name__ == "__main__":
    main(sys.argv[1:])
