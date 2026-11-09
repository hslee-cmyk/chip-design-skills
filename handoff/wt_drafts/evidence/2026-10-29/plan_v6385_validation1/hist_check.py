"""history 원문 보존 확인: 바뀐 계획 줄마다 옛 줄의 지워진 조각이 history 새 행의 «원문»에 그대로 있는지."""
import difflib, re, pathlib
d = pathlib.Path(__file__).parent
old = (d/"old_plan.md").read_text(encoding="utf-8").split("\n")
new = (d/"new_plan.md").read_text(encoding="utf-8").split("\n")
oh = (d/"old_hist.md").read_text(encoding="utf-8"); nh = (d/"new_hist.md").read_text(encoding="utf-8")
added_hist = "\n".join(l for l in nh.split("\n") if l not in set(oh.split("\n")))
quotes = re.findall(r"원문: «(.*?)»", added_hist, re.S)
out = [f"history 추가 행의 원문 인용 {len(quotes)}개; 옛 history 줄 보존 = {all(l in nh.split(chr(10)) for l in oh.split(chr(10)))}"]
sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal": continue
    for k in range(i1, i2):
        o = old[k]; n = new[j1 + (k - i1)] if j1 + (k - i1) < j2 else ""
        cm = difflib.SequenceMatcher(None, o, n, autojunk=False)
        for t, a1, a2, b1, b2 in cm.get_opcodes():
            if t in ("replace", "delete"):
                frag = o[a1:a2]
                if len(frag.strip()) < 4: continue
                ok = any(frag in q for q in quotes)
                out.append(f"old L{k+1} 지운 조각 {len(frag)}자 history 원문에 있음={ok}: {frag[:120]!r}")
(d/"hist_check.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
