"""p3v7_m10_mutants.py `all` 결과를 test 모양별 생존으로 요약한다(4차 검토 S3). 읽기 전용, 재실행 없음.

test 모양(새 M10 test가 진입점 실행 뒤 무엇을 대조하는가):
  T1 instance.json 키 정렬 해시만(E-INST 정의 그대로) + 진입점 밖으로 나온 예외
  T2 T1 + stdout에 '[FAIL]' 유무(기준과 같아야 함)
  T3 T2 + stdout 전체 해시
  T4 T3 + report.html 해시
분류: 변이 줄이 기준 실행에서 지나간 줄인가(회로별 trace), 문장이 print 호출인가.
사용: python p3v7_m10_summarize.py <m10 all 결과 json> <trace json…> <out.json>
"""
import ast
import json
import sys

RES, TRACES, OUT = sys.argv[1], sys.argv[2:-1], sys.argv[-1]
d = json.load(open(RES, encoding="utf-8"))
base = d["base"][0]
res = d["results"]
reached = {"folded_cascode": set(base.get("lines", []))}
for t in TRACES:
    x = json.load(open(t, encoding="utf-8"))
    reached[x["circuit"]] = set(x.get("lines", []))


def killed(r, shape):
    if r.get("exc"):
        return True
    if r.get("inst_sha") != base.get("inst_sha"):
        return True
    if shape >= 2 and r.get("fail_in_stdout") != base.get("fail_in_stdout"):
        return True
    if shape >= 3 and r.get("stdout_sha") != base.get("stdout_sha"):
        return True
    if shape >= 4 and r.get("report_sha") != base.get("report_sha"):
        return True
    return False


def is_print(seg):
    return seg.strip().startswith("print(")


rows = []
for r in res:
    line = r["line"]
    rows.append({"k": r["tag"], "op": r["op"], "line": line, "seg": r["seg"], "print": is_print(r["seg"]),
                 "reached_by": sorted(c for c, ls in reached.items() if line in ls),
                 "T1": killed(r, 1), "T2": killed(r, 2), "T3": killed(r, 3), "T4": killed(r, 4),
                 "wall_s": r.get("wall_s")})
summ = {"mutants": len(rows), "base_inst_sha": base.get("inst_sha"), "base_report": base.get("report_sha") is not None,
        "deterministic": d["summary"]["deterministic"]}
for t in ("T1", "T2", "T3", "T4"):
    sv = [x for x in rows if not x[t]]
    summ["survive_" + t] = len(sv)
    summ["survive_%s_print" % t] = sum(1 for x in sv if x["print"])
    summ["survive_%s_unreached_fc" % t] = sum(1 for x in sv if "folded_cascode" not in x["reached_by"])
    summ["survive_%s_unreached_any" % t] = sum(1 for x in sv if not x["reached_by"])
summ["survivors_T3"] = ["%s L%d %s" % (x["op"], x["line"], x["seg"][:70]) for x in rows if not x["T3"]]
summ["survivors_T1_list"] = ["%s L%d %s" % (x["op"], x["line"], x["seg"][:70]) for x in rows if not x["T1"]]
summ["wall_s_total"] = round(sum(x["wall_s"] or 0 for x in rows), 1)
summ["wall_s_killed_T1_mean"] = round(sum(x["wall_s"] or 0 for x in rows if x["T1"]) / max(1, sum(1 for x in rows if x["T1"])), 1)
summ["wall_s_survived_T1_mean"] = round(sum(x["wall_s"] or 0 for x in rows if not x["T1"]) / max(1, sum(1 for x in rows if not x["T1"])), 1)
json.dump({"summary": summ, "rows": rows}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in summ.items() if not k.startswith("survivors")}, ensure_ascii=False))
for k in ("survivors_T1_list", "survivors_T3"):
    print(k)
    for x in summ[k]:
        print("  ", x)
