# -*- coding: utf-8 -*-
"""N9.1 '읽을 plan 절' 열 기계 대조.

각 design 행의 '반드시 담을 것' 칸에 나오는 모든 ID/절 번호를 뽑아,
같은 행의 '읽을 plan 절' 열이 그 ID를 직접 포함하거나 그 ID가 정의된 절(N번호)을 포함하는지 검사한다.
결과는 같은 폴더 check_n91_coverage.txt에 append.
"""
import io
import os
import re
import datetime

PLAN = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\docs\01-plan\features\gain-budget-gmid-sizing.plan.md"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_n91_coverage.txt")

# ID 접두어 -> 정의 절
DEF_SEC = {
    "DEC": "N2.1", "WP": "N2.2", "DF": "N5.2", "U": "N7.2", "J": "N7.1",
    "IC": "N4.1", "V": "N4.2", "GB": "N3.1", "K": "N3.7", "MT": "N3.8",
    "SC": "N3.5", "LR": "N3.9", "EL": "N3.12.4", "TS": "N3.11", "MG": "N3.16",
    "MOD": "N3.10", "W": "N3.4", "S": "N3.3", "I": "N5.3", "FR": "N1.3", "NFR": "N1.4",
}

ID_RE = re.compile(
    r"\b(DEC-\d+|DF-\d+|I-[A-Z]\d+|U-\d+|J\d+(?:-[a-h])?|IC\d+|V\d+|GB\d+|K\d+|MT\d+"
    r"|SC-[a-e]|LR\d+|EL\d+|TS\d+|MG\d+|MOD\d+|WP-\d+)\b")
N_RE = re.compile(r"\bN\d+(?:\.\d+)*\b")


def norm(tok):
    m = re.match(r"^([A-Z]+)-?(.*)$", tok)
    pref, rest = m.group(1), m.group(2)
    if pref in ("DEC", "DF", "U", "WP", "IC", "V", "GB", "K", "MT", "LR", "EL", "TS", "MG", "MOD", "J"):
        return "%s-%02d" % (pref, int(re.sub(r"\D", "", rest))) if rest and rest[0].isdigit() else tok
    return tok


def expand_read_ids(text):
    """읽을 절 열에서 ID 집합을 만든다(범위 `~`와 나열 `·` 확장)."""
    out = set()
    for pref, body in re.findall(
            r"(DEC|DF|U|IC|V|GB|K|MT|LR|EL|TS|MG|MOD|WP|J)-?"
            r"(\d+[a-h]?(?:[·~]\d+[a-h]?)*)", text):
        for part in re.split(r"·", body):
            if "~" in part:
                a, b = part.split("~")
                for v in range(int(re.sub(r"\D", "", a)), int(re.sub(r"\D", "", b)) + 1):
                    out.add("%s-%02d" % (pref, v))
            else:
                out.add("%s-%02d" % (pref, int(re.sub(r"\D", "", part))))
    for tok in re.findall(r"\bI-[A-Z]\d+\b", text):
        out.add(tok)
    for tok in re.findall(r"\bSC-[a-e]\b", text):
        out.add(tok)
    for tok in re.findall(r"\bJ\d+-[a-h]\b", text):
        out.add("J-%02d" % int(re.sub(r"\D", "", tok.split("-")[0])))
    return out


def expand_read_secs(text):
    out = set()
    for m in re.finditer(r"N(\d+)\.(\d+)~N(\d+)\.(\d+)", text):
        a1, a2, b1, b2 = map(int, m.groups())
        if a1 == b1:
            for v in range(a2, b2 + 1):
                out.add("N%d.%d" % (a1, v))
    for tok in N_RE.findall(text):
        out.add(tok)
    return out


def covered_sec(sec, read_secs):
    """읽을 절 열이 sec를 덮는가: 같은 절이거나 그 조상 절이 있으면 덮는다."""
    for r in read_secs:
        if sec == r or sec.startswith(r + "."):
            return True
    return False


def main():
    t = io.open(PLAN, "r", encoding="utf-8", newline="").read()
    lines = t.split("\n")
    i0 = next(i for i, ln in enumerate(lines) if ln.startswith("### N9.1 "))
    i1 = next(i for i, ln in enumerate(lines) if ln.startswith("### N9.2 "))
    rows = [ln for ln in lines[i0:i1] if re.match(r"^\| `[0-9a-z-]+` \| ", ln)]
    assert len(rows) == 13, "N9.1 행 %d개" % len(rows)

    report = []
    total_missing = 0
    for ln in rows:
        cells = ln.split("|")
        doc = cells[1].strip().strip("`")
        must = cells[2]
        read = cells[3]
        read_ids = expand_read_ids(read)
        read_secs = expand_read_secs(read)

        miss_ids, miss_secs = [], []
        for tok in sorted(set(ID_RE.findall(must))):
            key = norm(tok)
            if key in read_ids or tok in read_ids:
                continue
            pref = re.match(r"^([A-Z]+)", tok).group(1)
            if covered_sec(DEF_SEC.get(pref, "ZZ"), read_secs):
                continue
            miss_ids.append(tok)
        for sec in sorted(set(N_RE.findall(must))):
            if not covered_sec(sec, read_secs):
                miss_secs.append(sec)
        total_missing += len(miss_ids) + len(miss_secs)
        report.append((doc, miss_ids, miss_secs))

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    buf = ["", "=" * 78, "N9.1 '읽을 plan 절' 커버리지 대조  %s" % ts, "=" * 78]
    for doc, mi, ms in report:
        if mi or ms:
            buf.append("[MISS] %-28s ID %s | 절 %s" % (doc, ",".join(mi) or "-", ",".join(ms) or "-"))
        else:
            buf.append("[ OK ] %-28s" % doc)
    buf.append("누락 합계 %d건 / 13행" % total_missing)
    out = "\n".join(buf) + "\n"
    with io.open(OUT, "a", encoding="utf-8", newline="") as f:
        f.write(out)
    print(out)


if __name__ == "__main__":
    main()
