# 검증 46: 점검 파일 두 개의 경로 실재·금지어·근거 칸 범주 점검. 출력 = v46_gate_check.txt (append)
import re, pathlib, hashlib
FPGA = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga")
G = FPGA / "wt/_drafts/ask_gates"
out = open(pathlib.Path(__file__).with_suffix(".txt"), "a", encoding="utf-8")
BAN = ["안 함", "미측정", "상정 전", "확인 필요", "TODO"]
for name in ("2026-10-31_QO200A.md", "2026-10-31_QO200B.md"):
    p = G / name
    b = p.read_bytes(); t = b.decode("utf-8")
    out.write(f"== {name} sha256 {hashlib.sha256(b).hexdigest()}\n")
    out.write(f"  금지어: { {w: t.count(w) for w in BAN} }\n")
    paths = set(re.findall(r"(?:C:/Users/HSLEE/Documents/Todoc/fpga/|wt/)[^\s,)`|]+", t))
    for s in sorted(paths):
        s2 = s.rstrip(".")
        m = re.match(r"(.*?)(?::(\d+))?$", s2)
        fp, ln = m.group(1), m.group(2)
        full = pathlib.Path(fp) if fp.startswith("C:") else FPGA / fp
        ok = full.exists()
        extra = ""
        if ok and ln and full.is_file():
            lines = full.read_text(encoding="utf-8", errors="replace").splitlines()
            extra = " | " + (lines[int(ln) - 1].strip()[:90] if int(ln) <= len(lines) else "LINE_OUT_OF_RANGE")
        out.write(f"  {'OK ' if ok else 'MISSING'} {s2}{extra}\n")
    # 근거 칸 범주: 표 행의 마지막 칸
    for line in t.splitlines():
        if line.startswith("| ") and re.match(r"\| [①②③④⑤⑥⑦⑧⑨] ", line):
            last = line.rstrip(" |").split(" | ")[-1]
            cats = [c for c in ("실측", "agent 인용", "해당 없음") if c in last]
            if not cats or not re.match(r"^(실측|agent 인용|해당 없음)", last.strip()):
                out.write(f"  범주 확인 필요 행: {line[:80]} -> {last[:80]}\n")
out.close()
