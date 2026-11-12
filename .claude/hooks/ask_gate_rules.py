"""원칙 26에서 게이트 검사 항목을 읽는 공용 파서. hook과 템플릿 생성기가 같이 쓴다.
원칙 26 정본 = skill `.claude/skills/report-bundle/SKILL.md`(2026-11-12 CLAUDE.md 개정으로 이전 — 경로는 이 파일 기준 상대 경로라
Windows·cloud0 어디서든 같은 저장소의 정본을 읽는다). env ASK_GATE_PRINCIPLES로 덮어쓸 수 있다."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DEF_PRINCIPLES = os.path.normpath(os.path.join(HERE, "..", "skills", "report-bundle", "SKILL.md"))
DEF_EXTRA = os.path.join(HERE, "ask_gate_extra.json")
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"


class RuleError(Exception):
    pass


def load_rules(principles=None, extra=None):
    """반환: dict(sections=[제목], table_label, rows=[(원문자, 항목이름)], prefixes=[...], forbidden=[...])."""
    principles = principles or os.environ.get("ASK_GATE_PRINCIPLES", DEF_PRINCIPLES)
    extra = extra or os.environ.get("ASK_GATE_EXTRA", DEF_EXTRA)
    fmt = "원칙 26 형식 오류: "
    try:
        with open(principles, "rb") as f:
            lines = f.read().decode("utf-8-sig").replace("\r\n", "\n").split("\n")
    except OSError as e:
        raise RuleError(fmt + "원칙 26 정본(skill report-bundle)을 읽을 수 없음 (%s: %s)" % (principles, e))
    start = next((i for i, l in enumerate(lines) if re.match(r"^26\.\s", l)), None)
    if start is None:
        raise RuleError(fmt + "'26. ' 로 시작하는 줄이 없음 (%s)" % principles)
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"^\d+\.\s", lines[i])), len(lines))
    head = lines[start]
    block = lines[start:end]
    # 접두/금지어: 머리 문장의 작은따옴표 인용. 첫 문장('...다.'까지)은 허용, 그 뒤에서 허용이 아닌 인용은 금지.
    m = re.search(r"하나다\.", head)
    first = head[:m.end()] if m else head
    rest = head[m.end():] if m else ""
    prefixes = []
    for t in re.findall(r"'([^']+)'", first):
        p = t.split("(")[0] + "(" if "(" in t else t
        if p not in prefixes:
            prefixes.append(p)
    allowed_raw = set(re.findall(r"'([^']+)'", first))
    forbidden = []
    for t in re.findall(r"'([^']+)'", rest):
        if t in allowed_raw or t in forbidden:
            continue
        forbidden.append(t)
    if not prefixes:
        raise RuleError(fmt + "머리 문장에서 허용 근거 접두(작은따옴표 인용)를 찾지 못함")
    # 하위 목록
    items = []
    for l in block[1:]:
        mm = re.match(r"^\s+\d+\.\s+\*\*(.+?)\*\*(.*)$", l)
        if mm:
            items.append([mm.group(1).strip(), mm.group(2)])
        elif items and l.strip():
            items[-1][1] += " " + l.strip()
    if not items:
        raise RuleError(fmt + "하위 목록 '1. **제목**' 이 0개")
    sections, table_label, rows = [], None, []
    for title, body in items:
        marks = [c for c in re.findall("[" + CIRCLED + "]", title + body)]
        if marks:
            if table_label is not None:
                raise RuleError(fmt + "원 문자 목록이 있는 하위 항목이 둘 이상")
            table_label = re.sub(r"\s*\d+항목\s*$", "", title).strip()
            parts = re.split("([" + CIRCLED + "])", body)
            for i in range(1, len(parts) - 1, 2):
                rows.append((parts[i], parts[i + 1].strip()))
        else:
            sections.append(title)
    if table_label is None or not rows:
        raise RuleError(fmt + "원 문자(①②…) 목록이 0개")
    try:
        with open(extra, "rb") as f:
            ex = json.loads(f.read().decode("utf-8-sig"))
        extra_forbidden = [str(x) for x in ex.get("forbidden", [])]
        measured_only = {str(k): str(v) for k, v in (ex.get("measured_only") or {}).items()}
    except (OSError, ValueError, AttributeError) as e:
        raise RuleError("보조 금지어 파일 오류 (%s: %s)" % (extra, e))
    for w in extra_forbidden:
        if w not in forbidden:
            forbidden.append(w)
    # measured_only: 이 행은 '해당 없음'·'agent 인용'만으로 둘 수 없다 -- 첫 허용 접두(실측) + 실재 경로 필수.
    row_marks = [n for n, _ in rows]
    for k in measured_only:
        if k not in row_marks:
            raise RuleError("보조 파일 measured_only 항목 %s 가 원칙 26 목록(%s)에 없음 (%s)" % (k, "".join(row_marks), extra))
    return {"sections": sections, "table_label": table_label, "rows": rows,
            "prefixes": prefixes, "forbidden": forbidden, "measured_only": measured_only}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    r = load_rules()
    print(json.dumps(r, ensure_ascii=False, indent=1))
