"""run_attack33.sh 결과(jsonl)를 단계 × 도구 표로(단계 판정 = 기대 exit·조각과 같은가, exit).
    python -B a33_table.py <a33.jsonl> [<표 출력 .md>]"""
import json
import sys

rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
tab, order, summ = {}, [], {}
for o in rows:
    if "summary" in o:
        summ[o["variant"]] = o["summary"]
        continue
    if o["step"] not in order:
        order.append(o["step"])
    tab.setdefault(o["step"], {})[o["variant"]] = (o["verdict"], o["exit"], o["why"])
vs = sorted({v for s in tab.values() for v in s})
lines = ["| 단계 | " + " | ".join("%s (판정, exit)" % ("base 도구" if v == "-" else "시제품 " + v) for v in vs) + " |",
         "|---|" + "---|" * len(vs)]
cnt = {v: {} for v in vs}
for s in order:
    cells = []
    for v in vs:
        verdict, ex, why = tab[s].get(v, ("-", "-", ""))
        cnt[v][verdict] = cnt[v].get(verdict, 0) + 1
        cells.append("%s, %s" % (verdict, ex))
    lines.append("| `%s` | %s |" % (s, " | ".join(cells)))
lines.append("")
lines.append("합계: " + "; ".join("%s %s" % ("base" if v == "-" else v, cnt[v]) for v in vs))
out = "\n".join(lines)
print(out)
if len(sys.argv) > 2:
    open(sys.argv[2], "w", encoding="utf-8").write(out + "\n")
