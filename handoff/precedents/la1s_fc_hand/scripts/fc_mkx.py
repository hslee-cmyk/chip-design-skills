"""설계 변수 파일 만들기: 바탕 x 파일 + 고친 칸 + 행 w_s(분할·행 이름으로) -> 새 x 파일.
usage: fc_mkx.py <base.json> <new.json> <tag> <changes.json 문자열> [part ws_row.json 문자열]"""
import json, sys
import fc_plan2_parts as PP
x = json.load(open(sys.argv[1], encoding="utf-8"))
x["tag"] = sys.argv[3]
ch = json.loads(sys.argv[4])
for k, v in ch.items():
    if isinstance(v, dict) and isinstance(x.get(k), dict):
        x[k].update(v)
    else:
        x[k] = v
if len(sys.argv) > 6:
    part = PP.PART[sys.argv[5]]
    wr = json.loads(sys.argv[6])
    x["ws"] = {n: wr[rn] for rn, _, names in part for n in names}
    x["ws_part"] = [sys.argv[5], wr]
json.dump(x, open(sys.argv[2], "w", encoding="utf-8"))
