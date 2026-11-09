"""history 넷째 커밋 «원문» 행: 옛 plan(7252a725)에 있고 새 plan(426c98b7)에 없는지. 결과 = hist_check.txt"""
import re
M = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6385_validation5/"
old = open(M + "old_plan.md", encoding="utf-8").read()
new = open(M + "new_plan.md", encoding="utf-8").read()
oh = open(M + "old_history.md", encoding="utf-8").read().split("\n")
nh = open(M + "new_history.md", encoding="utf-8").read().split("\n")
with open(M + "hist_check.txt", "w", encoding="utf-8") as o:
    o.write("old history lines %d, new %d; old lines preserved as prefix/suffix check:\n" % (len(oh), len(nh)))
    import difflib
    ops = [x for x in difflib.SequenceMatcher(None, oh, nh, autojunk=False).get_opcodes() if x[0] != "equal"]
    o.write("opcodes %r\n" % ops)
    for i in range(1855, 1869):
        s = nh[i]
        m = re.search("원문: «(.*)»", s)
        if not m:
            o.write("L%d no 원문: %s\n" % (i + 1, s[:120])); continue
        t = m.group(1)
        # 원문 안 '…' 생략 조각 지원
        parts = [p.replace("\|","|") for p in re.split(r" … |…", t) if p.strip()]
        ino = all(p in old for p in parts)
        inn = all(p in new for p in parts)
        o.write("L%d parts=%d in_old=%s in_new=%s | %s\n" % (i + 1, len(parts), ino, inn, s[:90]))
