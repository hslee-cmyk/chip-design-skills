"""검증 8: 8cbf8306 -> 6b0d70f6 에서 지워진 문장 조각이 history «원문»(새 행)에 보존됐는지 확인."""
import re, difflib, pathlib
M = pathlib.Path(__file__).parent
old = (M / "plan_8cbf8306.md").read_text(encoding="utf-8").splitlines()
new = (M / "plan_6b0d70f6.md").read_text(encoding="utf-8").splitlines()
ho = (M / "hist_8cbf8306.md").read_text(encoding="utf-8")
hn = (M / "hist_6b0d70f6.md").read_text(encoding="utf-8")
# history 새 부분만
sm = difflib.SequenceMatcher(None, ho.splitlines(), hn.splitlines(), autojunk=False)
added = []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag in ("insert", "replace"):
        added += hn.splitlines()[j1:j2]
added_txt = "\n".join(added).replace("\\|", "|")
out = []
out.append(f"history 추가 줄 수 = {len(added)}")
yuanmun = [l for l in added if "원문: «" in l]
out.append(f"«원문» 행 수 = {len(yuanmun)}")
for l in yuanmun:
    out.append("  - " + l.split("|")[1].strip())

def frags(s):
    # 문장/구 단위 조각
    parts = re.split(r"(?<=[.;])\s+| -- | / |\(|\)|·", s)
    return [p.strip() for p in parts if len(p.strip()) >= 12]

sm2 = difflib.SequenceMatcher(None, old, new, autojunk=False)
for tag, i1, i2, j1, j2 in sm2.get_opcodes():
    if tag == "equal":
        continue
    for k in range(i1, i2):
        o = old[k]
        nl = "\n".join(new[j1:j2])
        out.append(f"\n=== old line {k+1} (tag {tag})")
        # 원문 행 전체 보존?
        whole = o.strip() in added_txt
        out.append(f"line whole in history-added: {whole}")
        miss = []
        for f in frags(o):
            if f in nl:
                continue
            if f in added_txt:
                continue
            miss.append(f)
        out.append(f"fragments missing from both new line and history-added: {len(miss)}")
        for f in miss:
            out.append("  MISS: " + f)
(M / "hist_check.txt").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
