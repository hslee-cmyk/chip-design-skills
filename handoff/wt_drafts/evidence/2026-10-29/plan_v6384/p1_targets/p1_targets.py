"""plan v6.38.4 P1 실측 -- library 9회로 spec 제약의 판정 대상 술어 두 축(출처 kind·metric 결정 대기) 분포. 엔진 미사용(spec JSON 파싱).
P1은 술어의 자리(graph 필드 하나)만 옮기므로 대상 집합은 불변이어야 한다 -- 그 기준선 수치. 출력: out.jsonl"""
import json, glob, os, collections
LIB = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6384/skills/analog-gmid-design/assets/library"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out.jsonl")
with open(OUT, "w", encoding="utf-8") as fh:
    for f in sorted(glob.glob(os.path.join(LIB, "*.sizing_spec.json"))):
        cs = json.load(open(f, encoding="utf-8"))["human"].get("constraints", [])
        kinds = collections.Counter((c.get("source") or {}).get("kind") for c in cs)
        rec = {"circuit": os.path.basename(f)[:-len(".sizing_spec.json")], "n_constraints": len(cs), "source_kinds": dict(kinds),
               "pending_spice": kinds.get("pending_spice", 0), "metric_decision_pending": sum(1 for c in cs if "metric_decision" in c),
               "value_none_reference": [c.get("metric") for c in cs if c.get("value") is None]}
        fh.write(json.dumps(rec, ensure_ascii=False) + chr(10)); print(rec)
