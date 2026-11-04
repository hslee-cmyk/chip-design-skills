"""재측정 행만 fixture 에 반영, g8 기준선 stale 행(_Circuit.members) 제거. 인자: 대상 저장소 루트, rm_head 폴더."""
import json
import sys
from pathlib import Path

ROOT, RM = Path(sys.argv[1]), Path(sys.argv[2])
fx = ROOT / "skills/analog-gmid-design/gmid_engine/tests/integration/fixtures/u17_1b_s0_baseline.json"
raw = fx.read_bytes()
doc = json.loads(raw.decode("utf-8"))
note = ("[IT-1 2026-11-04, 원인 칸 DEC-106(O-168·O-170), 위임 A-39·A-42] 판정자(audit)가 병합본 f2278b9a(격리 복제본, OPENBLAS_NUM_THREADS=1, 사슬 두 번 비트 동일 확인, 회로마다 프로세스 하나)에서 "
        "잰 값으로 다음 행만 바꿨다: 7회로 achievability_sha.dof(입력 점이 V:<n 포트> 변수 하나를 없앰), 5회로 kernel.schema_fp·search_domain_fp(옛 IT-1 의 ln_idu 하나가 사라지고 y 키 = p 포트 넷), "
        "4회로 start.ladder_fp(옛 IT-1 갱신분에서 master 8d77b801 값으로 복귀, value_fp 같음 실측). 값 변화표는 O-225 보류 표지, 판정 기록 .ai/verification/20261104-it1-input-point.json.")
doc2 = {}
for k, v in doc.items():
    doc2[k] = v
    if k == "_source_o227":
        doc2["_source_it1"] = note
rows = []
for p in sorted(RM.glob("*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    if not d["diff"]:
        continue
    assert d["bit_same_a"] and d["bit_same_b"] and d["s0_fp_same"] in (True, None), p
    assert d["status"] == doc[d["circuit"]]["status"]
    doc2[d["circuit"]] = d["new"]
    rows.append((d["circuit"], d["diff"]))
fx.write_bytes((json.dumps(doc2, ensure_ascii=False, indent=1) + ("\n" if raw.endswith(b"\n") else "")).encode("utf-8"))
print(rows)

gb = ROOT / "skills/analog-gmid-design/gmid_engine/tests/structure/g8_baseline.json"
rawg = gb.read_bytes()
g = json.loads(rawg.decode("utf-8"))
before = len(g["rows"])
g["rows"] = [r for r in g["rows"] if not (r["path"] == "sizing/block_columns.py" and r["detail"] == "_Circuit.members" and r["kind"] == "g8_attr_container")]
assert len(g["rows"]) == before - 1
gb.write_bytes((json.dumps(g, ensure_ascii=False, indent=2, sort_keys=True) + ("\n" if rawg.endswith(b"\n") else "")).encode("utf-8"))
print("g8 rows", before, "->", len(g["rows"]))
