import re, pathlib
E=pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6385_validation2")
old=(E/"old_plan.md").read_text(encoding='utf-8'); new=(E/"new_plan.md").read_text(encoding='utf-8')
oh=(E/"old_hist.md").read_text(encoding='utf-8'); nh=(E/"new_hist.md").read_text(encoding='utf-8')
out=[]
out.append(f"old history lines all kept: {all(l in nh.split(chr(10)) for l in oh.split(chr(10)))}")
added=[l for l in nh.split('\n') if l not in set(oh.split('\n'))]
for l in added:
    for q in re.findall(r"«(.*?)»", l, re.S):
        q2=q.strip()
        out.append(f"quote in old plan={q2 in old} in new plan={q2 in new} :: {q2[:90]}")
# removed fragments from word diff
wd=(E/"diff_word.txt").read_text(encoding='utf-8')
rem=re.findall(r"\[-(.*?)-\]", wd, re.S)
hist_new="\n".join(added)
miss=[r for r in rem if r not in hist_new]
out.append(f"removed fragments {len(rem)}, not literally in new H rows: {len(miss)}")
for r in miss: out.append("  MISS: "+r[:120])
(E/"hist_check.txt").write_text("\n".join(out)+"\n",encoding='utf-8')
print("\n".join(out))
